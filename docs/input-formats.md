# Input Formats

FastMRZ accepts multiple input formats to accommodate different application architectures and data pipelines.

---

## Overview

| Input Type | `input_type` Value | Data Type | Description |
|------------|-------------------|-----------|-------------|
| Image Path | `"imagepath"` | `str` or `pathlib.Path` | File path to an image |
| NumPy Array | `"numpy"` | `np.ndarray` | Image as a NumPy array (BGR colour or greyscale) |
| Base64 String | `"base64"` | `str` | Base64-encoded image data, `data:` URL prefix allowed |
| Image Bytes | `"bytes"` | `bytes` | Encoded image file (JPEG, PNG, ...) |
| PDF | `"pdf"` | `str`, `Path` or `bytes` | PDF file; needs the `pdf` extra |
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

Any format OpenCV can decode:
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
- Must be a valid, non-empty NumPy array
- Colour images are expected in BGR order (OpenCV's default); greyscale (2-D or 1 channel) is accepted too
- Extra channels (e.g. alpha) are ignored; non-`uint8` arrays are rescaled to 0-255

**Example with PIL:**

```python
from PIL import Image
import numpy as np
from fastmrz import FastMRZ

fast_mrz = FastMRZ()

# Load with PIL as greyscale (avoids the RGB vs BGR question)
pil_image = Image.open("passport.jpg").convert("L")
image_array = np.array(pil_image)

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

A data URL prefix (e.g., `data:image/jpeg;base64,...`) is stripped automatically:

```python
import base64
from fastmrz import FastMRZ

fast_mrz = FastMRZ()

# Data URL from browser
data_url = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ..."

result = fast_mrz.get_details(data_url, input_type="base64")
```

---

## Image Bytes

Pass the encoded bytes of an image file, e.g. from an HTTP upload or object storage.

```python
from fastmrz import FastMRZ

fast_mrz = FastMRZ()

with open("passport.jpg", "rb") as f:
    result = fast_mrz.get_details(f.read(), input_type="bytes")
```

**Requirements:**
- Must decode to an image OpenCV can read (JPEG, PNG, BMP, TIFF, WebP, ...)

---

## PDF

Pass a PDF path or the PDF bytes. Up to the first 10 pages are rendered at 200 dpi, and the first page with an MRZ is used.

PDF rendering uses [PyMuPDF](https://pymupdf.readthedocs.io/), which is installed with FastMRZ.

```python
from fastmrz import FastMRZ

fast_mrz = FastMRZ()

result = fast_mrz.get_details("scan.pdf", input_type="pdf")

with open("scan.pdf", "rb") as f:
    result = fast_mrz.get_details(f.read(), input_type="pdf")
```

If PyMuPDF has been uninstalled, `ValueError("PDF input needs PyMuPDF: pip install pymupdf")` is raised.

---

## Raw MRZ Text

Pass pre-extracted MRZ text directly for parsing and validation. This skips the image processing pipeline entirely. The text is parsed exactly as given (upper-cased, whitespace removed) and never auto-corrected.

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

Inputs that cannot be read raise `ValueError` before any processing:

| `input_type` | Check | Error message |
|---|---|---|
| `imagepath` | File exists and decodes | `Input is not a valid image file.` / `Input is not a valid image.` |
| `numpy` | Non-empty `ndarray` with 1, 3 or 4 channels | `Input is not a valid NumPy array.` / `Input is not a valid image.` |
| `base64` | Valid Base64 that decodes to an image | `Input is not a valid base64 string.` / `Input is not a valid image.` |
| `bytes` | Decodes to an image | `Input is not a valid image.` |
| `pdf` | Valid PDF | `Input is not a valid PDF.` / `PDF input needs PyMuPDF: pip install pymupdf` |
| `text` | None at input stage | Format and checksums are reported in `status_message` |

`get_details_batch()` does not raise for unreadable inputs: their entries become `{"status": "FAILURE", "status_message": <message>}`.

---

## Choosing the Right Input Format

| Scenario | Recommended Format |
|----------|-------------------|
| Processing local files | `imagepath` |
| Images already in memory | `numpy` |
| Web API receiving JSON | `base64` |
| Web API receiving file uploads | `bytes` |
| Scanned documents | `pdf` |
| Validating external OCR output | `text` |
| Real-time camera feed | `numpy` |
| Batch processing from disk | `imagepath` with `get_details_batch()` |

---

## Next Steps

- Learn about the [processing pipeline](how-it-works.md)
- Review the [API reference](api-reference.md)
- Check known [limitations](limitations.md)
