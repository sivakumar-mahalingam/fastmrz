# Input Formats

FastMRZ accepts multiple input formats to accommodate different application architectures and data pipelines.

---

## Overview

| Input Type | `input_type` Value | Data Type | Description |
|------------|-------------------|-----------|-------------|
| Image Path | `"imagepath"` | `str` | File path to an image |
| NumPy Array | `"numpy"` | `np.ndarray` | Image as a NumPy array |
| Base64 String | `"base64"` | `str` | Base64-encoded image data |
| Raw MRZ Text | `"text"` | `str` | Pre-extracted MRZ text string |

---

## Image Path

The default and most common input format. Pass the file path to a document image.

```python
from fastmrz import FastMRZ

fast_mrz = FastMRZ()
result = fast_mrz.get_details("path/to/passport.jpg")
```

**Supported Image Formats:**

Any format supported by OpenCV's `imread`:
- JPEG / JPG
- PNG
- BMP
- TIFF
- WebP

**Requirements:**
- The file must exist and be readable
- The image must contain a visible MRZ region

**Example:**

```python
result = fast_mrz.get_details(
    "/home/user/documents/passport_scan.png",
    input_type="imagepath"  # This is the default
)
```

---

## NumPy Array

Pass an image directly as a NumPy array. This is useful when the image is already loaded in memory or obtained from another library.

```python
import cv2
import numpy as np
from fastmrz import FastMRZ

fast_mrz = FastMRZ()

# Load image with OpenCV
image = cv2.imread("passport.jpg")

# Pass directly to FastMRZ
result = fast_mrz.get_details(image, input_type="numpy")
```

**Requirements:**
- Must be a valid NumPy array
- Must have 3 channels (RGB or BGR format)
- Grayscale images are not supported directly

**Example with PIL:**

```python
from PIL import Image
import numpy as np
from fastmrz import FastMRZ

fast_mrz = FastMRZ()

# Load with PIL and convert
pil_image = Image.open("passport.jpg")
image_array = np.array(pil_image)

# Convert RGBA to RGB if needed
if image_array.shape[2] == 4:
    image_array = image_array[:, :, :3]

result = fast_mrz.get_details(image_array, input_type="numpy")
```

**Example with webcam capture:**

```python
import cv2
from fastmrz import FastMRZ

fast_mrz = FastMRZ()

cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    result = fast_mrz.get_details(frame, input_type="numpy")
    print(result)
cap.release()
```

---

## Base64 String

Pass a Base64-encoded image string. This is useful for web applications where images are transmitted as Base64.

```python
import base64
from fastmrz import FastMRZ

fast_mrz = FastMRZ()

# Encode image to Base64
with open("passport.jpg", "rb") as f:
    b64_string = base64.b64encode(f.read()).decode("utf-8")

# Process Base64 string
result = fast_mrz.get_details(b64_string, input_type="base64")
```

**Requirements:**
- Must be a valid Base64-encoded string
- Must decode to a valid image format

**Example with web upload (Flask):**

```python
from flask import Flask, request, jsonify
from fastmrz import FastMRZ

app = Flask(__name__)
fast_mrz = FastMRZ()

@app.route("/extract-mrz", methods=["POST"])
def extract_mrz():
    # Get Base64 from request
    data = request.json
    b64_image = data["image"]
    
    # Process
    result = fast_mrz.get_details(b64_image, input_type="base64")
    return jsonify(result)
```

**Example with data URL:**

If your Base64 string includes a data URL prefix (e.g., `data:image/jpeg;base64,...`), strip it first:

```python
import base64
from fastmrz import FastMRZ

fast_mrz = FastMRZ()

# Data URL from browser
data_url = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ..."

# Strip the prefix
b64_string = data_url.split(",")[1]

result = fast_mrz.get_details(b64_string, input_type="base64")
```

---

## Raw MRZ Text

Pass pre-extracted MRZ text directly for parsing and validation. This skips the image processing pipeline entirely.

```python
from fastmrz import FastMRZ

fast_mrz = FastMRZ()

mrz_text = (
    "P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n"
    "7077979792GBR9505209M1704224<<<<<<<<<<<<<<00"
)

result = fast_mrz.get_details(mrz_text, input_type="text")
```

**Use Cases:**
- Validating MRZ text obtained from another OCR engine
- Parsing MRZ text from a database
- Testing and debugging
- Processing MRZ text from manual input

**Example - Validate external OCR output:**

```python
# MRZ text from another OCR service
external_mrz = "P<USAJOHN<<DOE<<<<<<<<<<<<<<<<<<<<<<<<<<\n1234567890USA9001015M2501015<<<<<<<<<<<<<<04"

result = fast_mrz.get_details(external_mrz, input_type="text")
print(result["status"])  # SUCCESS or FAILURE
```

**Example - Get raw MRZ text only:**

```python
# Just get the raw MRZ text without parsing
raw_mrz = fast_mrz.get_details("passport.jpg", ignore_parse=True)
print(raw_mrz)
# Output:
# P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<
# 7077979792GBR9505209M1704224<<<<<<<<<<<<<<00
```

---

## Input Validation

FastMRZ validates inputs before processing:

### Image Path Validation

```python
def _is_valid(self, image):
    if isinstance(image, str):
        return bool(os.path.isfile(image))
    elif isinstance(image, np.ndarray):
        return image.shape[-1] == 3
```

- Checks if the file exists
- Raises `ValueError` if the file does not exist

### NumPy Array Validation

- Checks if the array has 3 channels
- Raises `ValueError` if the array shape is invalid

### Base64 Validation

- Decodes the Base64 string
- Raises an exception if the string is not valid Base64

### Text Validation

- No validation at input stage
- Validation occurs during parsing (MRZ format, checksums)

---

## Unsupported Formats

### PDF

PDF input is planned but not yet implemented. The `input_type="pdf"` parameter exists in the code but is not functional:

```python
elif input_type == "pdf":
    # get_details_from_pdf(input_data, ignore_parse=False, include_checkdigit=True)
    pass
```

To process PDFs, convert them to images first:

```python
import fitz  # PyMuPDF

doc = fitz.open("passport.pdf")
page = doc[0]
pix = page.get_pixmap()
pix.save("passport_page.png")

result = fast_mrz.get_details("passport_page.png")
```

---

## Choosing the Right Input Format

| Scenario | Recommended Format |
|----------|-------------------|
| Processing local files | `imagepath` |
| Images already in memory | `numpy` |
| Web API receiving uploads | `base64` |
| Validating external OCR output | `text` |
| Real-time camera feed | `numpy` |
| Batch processing from disk | `imagepath` |

---

## Next Steps

- Learn about the [processing pipeline](how-it-works.md)
- Review the [API reference](api-reference.md)
- Check known [limitations](limitations.md)
