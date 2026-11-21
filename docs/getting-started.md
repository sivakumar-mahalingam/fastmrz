# Installation & Setup

This guide covers installing FastMRZ and checking that it works.

---

## Requirements

| | Supported | Tested |
|---|---|---|
| Python | 3.8 or newer | 3.8, 3.9, 3.10, 3.11, 3.12, 3.13 |
| numpy | any version that matches your OpenCV | 1.24.4 to 2.5.5 |
| opencv-python-headless | 4.8 or newer | 4.8.1, 5.0.0, 5.1.0 |
| PyMuPDF (PDF input) | 1.23 or newer, except 1.26.5 and 1.26.6 (security advisory) | 1.23.26, 1.24.11, 1.26.4, 2.1 |

FastMRZ is pure Python. It needs no system packages, no PyTorch and no GPU: the MRZ recogniser is a 2.5 MB ONNX model that ships inside the package and runs through OpenCV.

!!! note "Upgrading from 2.x"
    Tesseract OCR and the `mrz.traineddata` file were **removed in v3**. You no longer need to install them or copy trained data anywhere, and you can uninstall Tesseract if nothing else on your system uses it.

---

## Install FastMRZ

=== "pip"

    ```bash
    pip install fastmrz
    ```

=== "uv"

    ```bash
    uv pip install fastmrz
    ```

=== "From source"

    ```bash
    git clone https://github.com/sivakumar-mahalingam/fastmrz.git
    cd fastmrz
    pip install .
    ```

### PDF input

PDF input (`input_type="pdf"`) works out of the box: [PyMuPDF](https://pymupdf.readthedocs.io/) is installed with FastMRZ. The former `fastmrz[pdf]` extra is still accepted but no longer needed.

---

## Usage

```python
from fastmrz import FastMRZ
import json

fast_mrz = FastMRZ()

result = fast_mrz.get_details("data/passport_uk.jpg", include_checkdigit=False)
print(json.dumps(result, indent=4))

text = fast_mrz.get_details("data/passport_uk.jpg", ignore_parse=True)
print(text)
```

**Output:**

```console
{
    "mrz_type": "TD3",
    "document_code": "P",
    "issuer_code": "GBR",
    "document_number": "707797979",
    "surname": "PUDARSAN",
    "given_name": "HENERT",
    "nationality_code": "GBR",
    "birth_date": "1995-05-20",
    "sex": "M",
    "expiry_date": "2017-04-22",
    "optional_data": "",
    "mrz_text": "P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n7077979792GBR9505209M1704224<<<<<<<<<<<<<<00",
    "status": "SUCCESS"
}
P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<
7077979792GBR9505209M1704224<<<<<<<<<<<<<<00
```

One `FastMRZ` instance loads the model once and can be shared across threads, so create it once and reuse it.

### Custom recogniser model

To use a custom recogniser model, pass its path:

```python
fast_mrz = FastMRZ(model_path="path/to/mrz_rec.onnx")
```

### Migrating 2.x code

`FastMRZ(tesseract_path=..., tessdata_path=...)` is still accepted, so existing code keeps running. Since Tesseract was removed in v3, both arguments are ignored and raise a `FutureWarning`. Remove them:

```python
# 2.x
fast_mrz = FastMRZ(tesseract_path=r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# 3.x
fast_mrz = FastMRZ()
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `numpy` | any matching OpenCV | Image arrays |
| `opencv-python-headless` | >= 4.8 | Image processing, MRZ detection, ONNX inference (`cv2.dnn`) |
| `pymupdf` | >= 1.23, != 1.26.5, != 1.26.6 | PDF rendering for `input_type="pdf"` |

The required packages are installed automatically by pip.

---

## System Requirements

- **Python**: 3.8 or higher
- **Operating Systems**:
  - macOS
  - Linux (POSIX)
  - Windows 10/11
- **CPU only**: about 0.1 s per image on a typical CPU

---

## Verify Installation

From a clone of the repository, run the test suite:

```bash
python -m unittest tests.test_fastmrz
```

---

## Next Steps

- Learn about [supported document types](supported-documents.md)
- Explore the [processing pipeline](how-it-works.md)
- Check the [API reference](api-reference.md) for detailed method documentation
