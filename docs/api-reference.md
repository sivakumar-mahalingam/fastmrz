# API Reference

Complete documentation for the FastMRZ Python API.

---

## FastMRZ Class

The main class for MRZ extraction and validation.

### `__init__`

```python
FastMRZ(tesseract_path: str = "", tessdata_path: str = "")
```

Initialize the FastMRZ engine.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tesseract_path` | `str` | `""` | Path to the Tesseract OCR executable. Leave empty if Tesseract is in your system PATH. |
| `tessdata_path` | `str` | `""` | Path to the directory containing Tesseract trained data files (including `mrz.traineddata`). |

**Example:**

```python
from fastmrz import FastMRZ

# Default initialization (Tesseract in PATH)
fast_mrz = FastMRZ()

# With explicit paths
fast_mrz = FastMRZ(
    tesseract_path=r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    tessdata_path=r'C:\Program Files\Tesseract-OCR\tessdata'
)
```

**Raises:**

No exceptions are raised during initialization. The ONNX model is loaded at this stage.

---

### `get_details`

```python
get_details(
    input_data: Union[str, np.ndarray, bytes],
    input_type: str = "imagepath",
    ignore_parse: bool = False,
    include_checkdigit: bool = True
) -> Union[dict, str]
```

Extract MRZ data from the provided input.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_data` | `str`, `np.ndarray`, or `bytes` | Required | The input data. Format depends on `input_type`. |
| `input_type` | `str` | `"imagepath"` | Type of input data. One of: `"imagepath"`, `"numpy"`, `"base64"`, `"text"`. |
| `ignore_parse` | `bool` | `False` | If `True`, returns raw MRZ text instead of parsed dictionary. |
| `include_checkdigit` | `bool` | `True` | If `True`, includes check digit fields in the output dictionary. |

**Returns:**

- If `ignore_parse=False`: A dictionary with parsed MRZ fields (see [Output Format](#output-format))
- If `ignore_parse=True`: A string containing the raw MRZ text

**Raises:**

- `ValueError`: If `input_data` is not valid for the specified `input_type`, or if `input_type` is unsupported.

**Examples:**

```python
# From image path
result = fast_mrz.get_details("passport.jpg")

# From NumPy array
import cv2
image = cv2.imread("passport.jpg")
result = fast_mrz.get_details(image, input_type="numpy")

# From Base64 string
import base64
with open("passport.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
result = fast_mrz.get_details(b64, input_type="base64")

# From raw MRZ text
mrz_text = "P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n7077979792GBR9505209M1704224<<<<<<<<<<<<<<00"
result = fast_mrz.get_details(mrz_text, input_type="text")

# Get raw MRZ text only
raw_mrz = fast_mrz.get_details("passport.jpg", ignore_parse=True)
print(raw_mrz)

# Exclude check digits from output
result = fast_mrz.get_details("passport.jpg", include_checkdigit=False)
```

---

### `validate_mrz`

```python
validate_mrz(mrz_text: str) -> dict
```

Validate a raw MRZ text string against ICAO 9303 checksum rules.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mrz_text` | `str` | Required | Raw MRZ text string to validate. |

**Returns:**

A dictionary with validation result:

```python
# Valid MRZ
{
    "is_valid": True,
    "status_message": "The given mrz is valid"
}

# Invalid MRZ
{
    "is_valid": False,
    "status_message": "Document number checksum is not matching"
}
```

**Example:**

```python
result = fast_mrz.validate_mrz(
    "P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n"
    "7077979792GBR9505209M1704224<<<<<<<<<<<<<<00"
)
print(result["is_valid"])  # True
```

---

## Output Format

### Parsed MRZ Dictionary (TD3 - Passport)

```python
{
    "mrz_type": "TD3",
    "document_code": "P",
    "issuer_code": "GBR",
    "surname": "PUDARSAN",
    "given_name": "HENERT",
    "document_number": "707797979",
    "document_number_checkdigit": "2",
    "nationality_code": "GBR",
    "birth_date": "1995-05-20",
    "birth_date_checkdigit": "9",
    "sex": "M",
    "expiry_date": "2017-04-22",
    "expiry_date_checkdigit": "4",
    "optional_data": "",
    "optional_data_checkdigit": "0",
    "final_checkdigit": "0",
    "mrz_text": "P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n7077979792GBR9505209M1704224<<<<<<<<<<<<<<00",
    "status": "SUCCESS"
}
```

### Parsed MRZ Dictionary (TD1 - ID Card)

```python
{
    "mrz_type": "TD1",
    "document_code": "I",
    "issuer_code": "UTO",
    "document_number": "L898902C3",
    "document_number_checkdigit": "6",
    "optional_data_1": "",
    "birth_date": "1974-08-12",
    "birth_date_checkdigit": "2",
    "sex": "F",
    "expiry_date": "2012-04-15",
    "expiry_date_checkdigit": "9",
    "nationality_code": "UTO",
    "optional_data_2": "ZE184226B",
    "final_checkdigit": "0",
    "surname": "ERIKSSON",
    "given_name": "ANNA MARIA",
    "mrz_text": "...",
    "status": "SUCCESS"
}
```

### Parsed MRZ Dictionary (TD2)

```python
{
    "mrz_type": "TD2",
    "document_code": "I",
    "issuer_code": "UTO",
    "surname": "ERIKSSON",
    "given_name": "ANNA MARIA",
    "document_number": "D23145890",
    "document_number_checkdigit": "7",
    "nationality_code": "UTO",
    "birth_date": "1974-08-12",
    "birth_date_checkdigit": "2",
    "sex": "F",
    "expiry_date": "2012-04-15",
    "expiry_date_checkdigit": "9",
    "optional_data": "",
    "final_checkdigit": "6",
    "mrz_text": "...",
    "status": "SUCCESS"
}
```

### Parsed MRZ Dictionary (MRVA/MRVB - Visa)

```python
{
    "mrz_type": "MRVA",  # or "MRVB"
    "document_code": "V",
    "issuer_code": "USA",
    "surname": "...",
    "given_name": "...",
    "document_number": "...",
    "document_number_checkdigit": "...",
    "nationality_code": "...",
    "birth_date": "...",
    "birth_date_checkdigit": "...",
    "sex": "...",
    "expiry_date": "...",
    "expiry_date_checkdigit": "...",
    "optional_data": "...",
    "mrz_text": "...",
    "status": "SUCCESS"
}
```

Note: MRVA and MRVB do not include `final_checkdigit` or `optional_data_checkdigit` fields.

---

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `mrz_type` | `str` | Document type: `TD1`, `TD2`, `TD3`, `MRVA`, or `MRVB` |
| `document_code` | `str` | Document type code (e.g., `P` for passport, `I` for ID, `V` for visa) |
| `issuer_code` | `str` | 3-letter ISO country code of the issuing authority |
| `surname` | `str` | Holder's surname(s) |
| `given_name` | `str` | Holder's given name(s) |
| `document_number` | `str` | Unique document identifier |
| `document_number_checkdigit` | `str` | Check digit for document number |
| `nationality_code` | `str` | 3-letter ISO country code of holder's nationality |
| `birth_date` | `str` | Date of birth in ISO 8601 format (YYYY-MM-DD) |
| `birth_date_checkdigit` | `str` | Check digit for date of birth |
| `sex` | `str` | Holder's sex: `M`, `F`, or `<` (unspecified) |
| `expiry_date` | `str` | Document expiry date in ISO 8601 format (YYYY-MM-DD) |
| `expiry_date_checkdigit` | `str` | Check digit for expiry date |
| `optional_data` | `str` | Optional data field (varies by document type) |
| `optional_data_checkdigit` | `str` | Check digit for optional data (TD3 only) |
| `optional_data_1` | `str` | First optional data field (TD1 only) |
| `optional_data_2` | `str` | Second optional data field (TD1 only) |
| `final_checkdigit` | `str` | Composite check digit |
| `mrz_text` | `str` | Raw MRZ text as extracted |
| `status` | `str` | Processing status: `SUCCESS` or `FAILURE` |
| `status_message` | `str` | Error message (present only when `status` is `FAILURE`) |

---

## Error Responses

When extraction or validation fails, the response includes a `status` of `"FAILURE"` and a `status_message`:

| Status Message | Cause |
|----------------|-------|
| `"No MRZ detected"` | The segmentation model did not find an MRZ region in the image |
| `"Invalid MRZ format"` | The extracted text does not match any known MRZ format |
| `"Document number checksum is not matching"` | Document number check digit validation failed |
| `"Date of birth checksum is not matching"` | Birth date check digit validation failed |
| `"Date of expiry checksum is not matching"` | Expiry date check digit validation failed |
| `"Optional data checksum is not matching"` | Optional data check digit validation failed (TD3) |
| `"Final checksum is not matching"` | Composite check digit validation failed |

---

## Input Validation

The `get_details` method validates input before processing:

- **`imagepath`**: Checks if the file exists using `os.path.isfile()`
- **`numpy`**: Checks if the array has 3 channels (RGB/BGR)
- **`base64`**: Decodes and validates the Base64 string
- **`text`**: Passes directly to the parser

Invalid inputs raise a `ValueError` with a descriptive message.

---

## Internal Methods

These methods are used internally and are not part of the public API. They are documented here for reference and debugging purposes.

### `_process_image`

```python
_process_image(image_path: Union[str, np.ndarray]) -> np.ndarray
```

Preprocesses an image for ONNX model inference.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `image_path` | `str` or `np.ndarray` | File path or NumPy array of the image |

**Returns:**

Preprocessed image array of shape `(1, 256, 256, 3)`.

---

### `_get_roi`

```python
_get_roi(output_data: np.ndarray, image_path: Union[str, np.ndarray]) -> str
```

Extracts the MRZ region from the segmentation output and performs OCR.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `output_data` | `np.ndarray` | Segmentation mask from ONNX model |
| `image_path` | `str` or `np.ndarray` | Original image for ROI extraction |

**Returns:**

Raw OCR text from the MRZ region.

---

### `_cleanse_roi`

```python
_cleanse_roi(mrz_text: str) -> str
```

Cleanses raw OCR output to extract valid MRZ lines.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `mrz_text` | `str` | Raw OCR output text |

**Returns:**

Cleaned MRZ text with valid lines only.

---

### `_parse_mrz`

```python
_parse_mrz(mrz_text: str, include_checkdigit: bool = True) -> dict
```

Parses MRZ text into structured fields.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `mrz_text` | `str` | Cleaned MRZ text |
| `include_checkdigit` | `bool` | Whether to include check digit fields |

**Returns:**

Dictionary with parsed MRZ fields.

---

### `_get_checkdigit`

```python
_get_checkdigit(input_string: str) -> str
```

Calculates the ICAO 9303 check digit for a given string.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `input_string` | `str` | String to calculate check digit for |

**Returns:**

Single-digit check digit as a string.

---

### `_get_final_checkdigit`

```python
_get_final_checkdigit(input_string: list, input_type: str) -> str
```

Calculates the composite final check digit.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `input_string` | `list` | List of MRZ lines |
| `input_type` | `str` | Document type (`TD1`, `TD2`, `TD3`) |

**Returns:**

Final composite check digit as a string.

---

### `_format_date`

```python
_format_date(input_date: str) -> str
```

Converts YYMMDD date string to ISO 8601 format (YYYY-MM-DD).

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `input_date` | `str` | Date in YYMMDD format |

**Returns:**

Formatted date string in YYYY-MM-DD format.

---

### `_get_birth_date`

```python
_get_birth_date(birth_date_str: str, expiry_date_str: str) -> str
```

Resolves century ambiguity in birth dates.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `birth_date_str` | `str` | Birth date in YYYY-MM-DD format |
| `expiry_date_str` | `str` | Expiry date in YYYY-MM-DD format |

**Returns:**

Adjusted birth date string.

---

### `_is_valid`

```python
_is_valid(image: Union[str, np.ndarray]) -> bool
```

Validates input image.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `image` | `str` or `np.ndarray` | File path or NumPy array |

**Returns:**

`True` if the input is valid, `False` otherwise.

---

### `_get_mrz`

```python
_get_mrz(image: Union[str, np.ndarray]) -> str
```

End-to-end MRZ extraction from an image.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `image` | `str` or `np.ndarray` | Input image |

**Returns:**

Cleaned MRZ text string.

---

### `_image_to_base64`

```python
_image_to_base64(imagepath: str) -> str
```

Converts an image file to Base64 string.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `imagepath` | `str` | Path to image file |

**Returns:**

Base64-encoded string.

---

### `_base64_to_array`

```python
_base64_to_array(base64_string: str) -> np.ndarray
```

Decodes a Base64 string to a NumPy array.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `base64_string` | `str` | Base64-encoded image data |

**Returns:**

NumPy array of the decoded image.

---

## Next Steps

- Learn about [supported document types](supported-documents.md)
- Understand [checksum validation](checksum-validation.md) in detail
- Review known [limitations](limitations.md)
