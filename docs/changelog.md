# Changelog

All notable changes to FastMRZ will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned

- PDF input support
- Bulk/batch processing
- Image enhancement model parameter
- Text image enhancement model
- `get_mrz_image` function to return cropped MRZ region
- `generate_mrz` function to create MRZ from structured data
- Face image extraction from documents
- Complete check digit status reporting
- Improved Tesseract model training

---

## [2.1] - 2024

### Added

- `status_message` field in output for detailed error reporting
- `validate_mrz()` method for standalone MRZ validation
- `include_checkdigit` parameter to control check digit inclusion in output
- Support for MRVA (Machine-Readable Visa Type A) documents
- Support for MRVB (Machine-Readable Visa Type B) documents
- NumPy array input support (`input_type="numpy"`)
- Base64 string input support (`input_type="base64"`)
- Raw MRZ text input support (`input_type="text"`)

### Changed

- Renamed `message` to `status_message` in output dictionary
- Updated ONNX segmentation model
- Improved MRZ text cleansing logic

### Fixed

- MRZ detection for skewed document images
- Check digit validation for TD1 documents

---

## [2.0] - 2024

### Added

- Custom ONNX segmentation model for MRZ detection
- Contour-based ROI extraction
- Support for TD1, TD2, and TD3 document types
- ICAO 9303 checksum validation
- Date formatting (YYMMDD to ISO 8601)
- Century resolution for birth dates
- JSON output format
- Custom Tesseract trained data (`mrz.traineddata`)

### Changed

- Complete rewrite of the extraction pipeline
- Replaced traditional image processing with ML-based segmentation
- Improved accuracy for challenging document images

---

## [1.0] - Initial Release

### Added

- Basic MRZ extraction from passport images
- Tesseract OCR integration
- Contour detection for MRZ region identification
- Support for TD3 (passport) documents
- JSON output format

---

## Version Summary

| Version | Release Date | Key Features |
|---------|--------------|--------------|
| 2.1 | 2024 | MRVA/MRVB support, validation, multiple input formats |
| 2.0 | 2024 | ONNX model, complete pipeline rewrite |
| 1.0 | - | Initial MRZ extraction |

---

## Migration Guide

### From 1.x to 2.x

Version 2.0 introduced significant changes:

1. **ONNX Model**: The extraction pipeline now uses a custom-trained ONNX model. Ensure you have the `mrz.traineddata` file installed.

2. **Output Format**: The output dictionary structure may have changed. Check the [API Reference](api-reference.md) for the current format.

3. **Tesseract Path**: If Tesseract is not in your PATH, you must now provide the path explicitly:
   ```python
   fast_mrz = FastMRZ(tesseract_path="/path/to/tesseract")
   ```

### From 2.0 to 2.1

Version 2.1 is backward compatible with 2.0. New features are additive:

- `validate_mrz()` method is new
- `include_checkdigit` parameter is new (defaults to `True` for compatibility)
- `status_message` replaces `message` in output

---

## Release Process

Releases are published to PyPI. To install a specific version:

```bash
pip install fastmrz==2.1
```

---

## Links

- [PyPI Releases](https://pypi.org/project/fastmrz/#history)
- [GitHub Releases](https://github.com/sivakumar-mahalingam/fastmrz/releases)
- [Issue Tracker](https://github.com/sivakumar-mahalingam/fastmrz/issues)
