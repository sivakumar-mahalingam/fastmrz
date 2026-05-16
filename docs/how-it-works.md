# How It Works

This document explains the internal architecture and processing pipeline of FastMRZ.

---

## Architecture Overview

FastMRZ combines three core technologies to extract MRZ data from document images:

1. **ONNX-based Semantic Segmentation** - Locates the MRZ region in the document
2. **Contour Detection** - Extracts the precise bounding box of the MRZ area
3. **Tesseract OCR** - Reads the text from the extracted region

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FastMRZ Processing Pipeline                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────┐ │
│  │  Input   │───▶│   ONNX Model │───▶│   Contour    │───▶│  Tesseract │ │
│  │  Image   │    │ Segmentation │    │  Detection   │    │    OCR  │ │
│  └──────────┘    └──────────────┘    └──────────────┘    └────────┘ │
│                                                                        │
│       ┌──────────────────────────────────────────────────────┐        │
│       │                   MRZ Parser                         │        │
│       │  (Field extraction, date formatting, validation)     │        │
│       └──────────────────────────────────────────────────────┘        │
│                                                                        │
│       ┌──────────────────────────────────────────────────────┐        │
│       │              Checksum Validation                      │        │
│       │  (ICAO 9303 check digits for all fields)             │        │
│       └──────────────────────────────────────────────────────┘        │
│                                                                        │
│                              │                                         │
│                              ▼                                         │
│                    ┌──────────────────┐                                │
│                    │  Structured JSON │                                │
│                    │    Output        │                                │
│                    └──────────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Processing Pipeline

### Step 1: Image Preprocessing

When an image is passed to FastMRZ, it undergoes preprocessing before being fed to the segmentation model:

```python
# Image is resized to 256x256 for the ONNX model
image = cv2.resize(image, (256, 256), interpolation=cv2.INTER_NEAREST)

# Normalized to [0, 1] range
image = np.asarray(np.float32(image / 255))

# Reshaped to model input shape (1, 256, 256, 3)
image = np.reshape(image, (1, 256, 256, 3))
```

The fixed 256x256 input size ensures consistent model inference regardless of the original image resolution.

### Step 2: ONNX Segmentation Model

FastMRZ includes a pre-trained ONNX model (`mrz_seg.onnx`) that performs semantic segmentation to identify the MRZ region in the document image.

```python
# Load the model (done once during initialization)
self.net = cv2.dnn.readNetFromONNX(
    os.path.join(os.path.dirname(__file__), "model/mrz_seg.onnx")
)

# Run inference
self.net.setInput(image_array)
output_data = self.net.forward()
```

The model outputs a segmentation mask where pixels belonging to the MRZ region have high confidence values.

**Model Details:**
- Format: ONNX (Open Neural Network Exchange)
- Input: 256x256 RGB image
- Output: Segmentation mask (256x256x1)
- Framework: Run via OpenCV's DNN module (no additional ML dependencies)

### Step 3: Contour Detection & ROI Extraction

The segmentation mask is processed to extract the precise MRZ bounding box:

```python
# Threshold the output mask
output_data = (output_data[0, :, :, 0] > 0.25) * 1
output_data = np.uint8(output_data * 255)

# Resize mask to original image dimensions
altered_image = cv2.resize(output_data, (image.shape[1], image.shape[0]))

# Morphological erosion to clean up noise
kernel = np.ones((5, 5), dtype=np.float32)
altered_image = cv2.erode(altered_image, kernel, iterations=1)

# Find contours
contours, hierarchy = cv2.findContours(
    altered_image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
)

# Select the largest contour by area
c_area = np.zeros([len(contours)])
for j in range(len(contours)):
    c_area[j] = cv2.contourArea(contours[j])

x, y, w, h = cv2.boundingRect(contours[np.argmax(c_area)])
```

**Padding**: A 10-pixel padding is added around the bounding box to ensure the entire MRZ region is captured:

```python
padding = 10
x_start = max(0, x - padding)
y_start = max(0, y - padding)
x_end = min(image.shape[1], x + w + padding)
y_end = min(image.shape[0], y + h + padding)
```

### Step 4: Image Preprocessing for OCR

The extracted ROI undergoes additional preprocessing to optimize it for Tesseract OCR:

```python
# Convert to grayscale
roi_gray = cv2.cvtColor(roi_arr, cv2.COLOR_BGR2GRAY)

# Apply Otsu's thresholding for binary image
roi_threshold = cv2.threshold(
    roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
)[1]
```

Otsu's thresholding automatically determines the optimal threshold value to separate text from background, which significantly improves OCR accuracy for MRZ text.

### Step 5: Tesseract OCR

The preprocessed ROI is passed to Tesseract with the custom MRZ-trained model:

```python
custom_config = r"--oem 3 --psm 6" + (
    f" --tessdata-dir {self.tessdata_path}" if self.tessdata_path else ""
)
mrz_text = pytesseract.image_to_string(
    roi_threshold, lang="mrz", config=custom_config
)
```

**Configuration parameters:**
- `--oem 3`: Uses both LSTM and legacy OCR engines
- `--psm 6`: Assumes a single uniform block of text
- `lang="mrz"`: Uses the custom MRZ-trained data

### Step 6: MRZ Text Cleansing

The raw OCR output is cleaned to extract valid MRZ lines:

```python
def _cleanse_roi(self, mrz_text):
    input_list = mrz_text.replace(" ", "").split("\n")
    
    # Detect MRZ line length (30, 36, or 44 characters)
    selection_length = next(
        (len(item) for item in input_list
         if "<" in item and len(item) in {30, 36, 44}),
        None,
    )
    
    # Filter lines matching the detected format
    new_list = [item for item in input_list
                if len(item) >= selection_length and "<" in item]
    
    return "\n".join(new_list)
```

This step handles common OCR artifacts like extra whitespace, broken lines, and noise.

### Step 7: MRZ Parsing

The cleansed MRZ text is parsed according to ICAO Doc 9303 specifications. The parser handles all supported document types:

| Document Type | Detection Logic |
|---------------|-----------------|
| **TD3** | 2 lines, 44 chars each, last char is not `<` |
| **TD2** | 2 lines, 36 chars each, last char is not `<` |
| **MRVA** | 2 lines, 44 chars each, last char is `<` |
| **MRVB** | 2 lines, 36 chars each, last char is `<` |
| **TD1** | 3 lines, 30 chars each |

**Parsed Fields:**

For TD2/TD3/MRVA/MRVB (2-line formats):
- Document code
- Issuer code (3-letter country code)
- Surname
- Given name(s)
- Document number
- Nationality code
- Date of birth
- Sex
- Expiry date
- Optional data
- All check digits

For TD1 (3-line format):
- Document code
- Issuer code
- Document number
- Optional data (parts 1 and 2)
- Date of birth
- Sex
- Expiry date
- Nationality code
- Surname
- Given name(s)
- All check digits

### Step 8: Date Formatting

MRZ dates are stored as YYMMDD format. FastMRZ converts them to ISO 8601 format (YYYY-MM-DD):

```python
def _format_date(self, input_date):
    formatted_date = str(datetime.strptime(input_date, "%y%m%d").date())
    return formatted_date
```

**Century Handling**: MRZ dates use 2-digit years. FastMRZ determines the century by comparing birth date with expiry date:

```python
def _get_birth_date(self, birth_date_str, expiry_date_str):
    birth_year = int(birth_date_str[:4])
    expiry_year = int(expiry_date_str[:4])
    
    if expiry_year > birth_year:
        return birth_date_str
    adjusted_year = birth_year - 100
    return f"{adjusted_year}-{birth_date_str[5:]}"
```

If the birth year appears to be in the future relative to the expiry date, it is adjusted back by 100 years.

### Step 9: Checksum Validation

FastMRZ validates all ICAO 9303 check digits:

```python
def _get_checkdigit(self, input_string):
    weights_pattern = [7, 3, 1]
    
    total = 0
    for i, char in enumerate(input_string):
        if char.isdigit():
            value = int(char)
        elif char.isalpha():
            value = ord(char.upper()) - ord("A") + 10
        else:
            value = 0
        total += value * weights_pattern[i % len(weights_pattern)]
    
    check_digit = total % 10
    return str(check_digit)
```

**Validated Fields:**
- Document number check digit
- Date of birth check digit
- Expiry date check digit
- Optional data check digit (TD3 only)
- Final composite check digit

If any check digit fails validation, the result status is set to `"FAILURE"` with a descriptive error message.

---

## Input Type Handling

FastMRZ supports multiple input formats through the `input_type` parameter:

| Input Type | Processing |
|------------|------------|
| `imagepath` | Reads file, converts to Base64, then to NumPy array |
| `numpy` | Uses array directly |
| `base64` | Decodes to NumPy array |
| `text` | Skips image processing, parses MRZ text directly |

---

## Error Handling

FastMRZ provides structured error responses:

```python
# Successful extraction
{
    "mrz_type": "TD3",
    "document_code": "P",
    ...
    "status": "SUCCESS"
}

# Failed extraction
{
    "status": "FAILURE",
    "status_message": "No MRZ detected"
}

# Checksum mismatch
{
    "mrz_type": "TD3",
    ...
    "status": "FAILURE",
    "status_message": "Document number checksum is not matching"
}
```

---

## Performance Considerations

- **Model Loading**: The ONNX model is loaded once during `FastMRZ` initialization, not per-call
- **Image Resizing**: All images are resized to 256x256 for consistent model inference
- **Memory Efficiency**: Uses `opencv-python-headless` to avoid GUI dependencies
- **Minimal Dependencies**: Only OpenCV and pytesseract are required

---

## Next Steps

- Explore the [API Reference](api-reference.md) for detailed method documentation
- Learn about [checksum validation](checksum-validation.md) in depth
- Review known [limitations](limitations.md)
