# FastMRZ

![FastMRZ](https://raw.githubusercontent.com/sivakumar-mahalingam/fastmrz/main/docs/FastMRZ.png)

**FastMRZ** is an open-source Python package that automates the extraction and validation of Machine Readable Zone (MRZ) data from travel documents and identification cards. Built with computer vision, machine learning-based segmentation, and optical character recognition, FastMRZ delivers accurate MRZ extraction from document images with minimal setup.

---

## Overview

In today's world, where speed is critical, sensitive document processing must be automated. Whether it's passports, visas, or ID cards, extracting MRZ data with accuracy and speed is essential for building reliable identity verification applications.

FastMRZ provides a lightweight, efficient, and easy-to-use implementation that simplifies MRZ extraction for developers building systems in FinTech, security, and identity verification.

---

## Key Features

- **MRZ Detection**: Detects and extracts the MRZ region from document images using contour detection
- **Custom ONNX Models**: Integrated custom-trained ONNX segmentation models for improved recognition accuracy
- **Built-in Validation**: Comprehensive checksum logic verifies extracted data to catch OCR errors and detect potential document tampering
- **Multiple Input Formats**: Accepts image paths, NumPy arrays, Base64 strings, or raw MRZ text
- **Structured Output**: Returns extracted MRZ data as structured JSON with parsed fields
- **ICAO Compliant**: Follows ICAO Doc 9303 standards for MRZ format and validation

---

## Supported Document Types

| Type | Description | Lines | Characters per Line |
|------|-------------|-------|---------------------|
| **TD1** | ID cards, US Green Card | 3 | 30 |
| **TD2** | Some national IDs, MRV-B visas | 2 | 36 |
| **TD3** | International passports, MRV-A visas | 2 | 44 |
| **MRVA** | Machine-readable visas Type A | 2 | 44 |
| **MRVB** | Machine-readable visas Type B | 2 | 36 |

---

## Quick Start

### Installation

```bash
pip install fastmrz
```

### Basic Usage

```python
from fastmrz import FastMRZ
import json

fast_mrz = FastMRZ()
result = fast_mrz.get_details("path/to/passport.jpg")
print(json.dumps(result, indent=4))
```

### Example Output

```json
{
    "mrz_type": "TD3",
    "document_code": "P",
    "issuer_code": "GBR",
    "surname": "PUDARSAN",
    "given_name": "HENERT",
    "document_number": "707797979",
    "nationality_code": "GBR",
    "birth_date": "1995-05-20",
    "sex": "M",
    "expiry_date": "2017-04-22",
    "mrz_text": "P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n7077979792GBR9505209M1704224<<<<<<<<<<<<<<00",
    "status": "SUCCESS"
}
```

---

## Prerequisites

FastMRZ requires the **Tesseract OCR** engine to be installed on your system. See the [Installation Guide](getting-started.md) for detailed setup instructions.

---

## Documentation

| Section | Description |
|---------|-------------|
| [Getting Started](getting-started.md) | Installation, prerequisites, and setup |
| [How It Works](how-it-works.md) | Architecture, processing pipeline, and internals |
| [Supported Documents](supported-documents.md) | Document types and MRZ formats |
| [Input Formats](input-formats.md) | Supported input types and usage |
| [API Reference](api-reference.md) | Complete API documentation |
| [Checksum Validation](checksum-validation.md) | How ICAO check digits work |
| [Limitations](limitations.md) | Current limitations and known issues |
| [Contributing](contributing.md) | How to contribute to the project |
| [Changelog](changelog.md) | Version history and release notes |

---

## Links

- **GitHub Repository**: [https://github.com/sivakumar-mahalingam/fastmrz](https://github.com/sivakumar-mahalingam/fastmrz)
- **PyPI Package**: [https://pypi.org/project/fastmrz/](https://pypi.org/project/fastmrz/)
- **Issue Tracker**: [https://github.com/sivakumar-mahalingam/fastmrz/issues](https://github.com/sivakumar-mahalingam/fastmrz/issues)

---

## License

Distributed under the AGPL-3.0 License. See [LICENSE](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/LICENSE) for more information.
