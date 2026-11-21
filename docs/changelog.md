# Changelog

All notable changes to FastMRZ will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned

- Image enhancement model parameter
- Text image enhancement model
- `generate_mrz` function to create MRZ from structured data
- Face image extraction from documents
- Complete check digit status reporting

---

## [3.1.0] - 2026-11-21

PDF support by default and an updated recogniser model, plus documentation and repository cleanup (#41). The public API is unchanged.

### Added

- Security policy (`.github/SECURITY.md`) with private vulnerability reporting
- Issue templates for bug reports, feature requests, improvements and blank issues, and a pull request template

### Changed

- PDF support is installed by default: `pymupdf` is now a regular dependency, so `pip install fastmrz` is enough for `input_type="pdf"`. The `pdf` extra is kept as an empty alias, so `pip install "fastmrz[pdf]"` keeps working
- Updated recogniser model (`fastmrz/model/mrz_rec.onnx`, now 2.5 MB), trained on synthetic MRZ data
- Version bumped to 3.1.0 in `pyproject.toml`, `fastmrz/__init__.py` and `uv.lock`

### Removed

- The `tools/` folder and all references to it from the README, docs, tests and `.gitignore`
- The bundled ICAO Doc 9303 PDFs (`docs/9303_p*_cons_en.pdf`); the docs link to the official [ICAO Doc 9303](https://www.icao.int/publications/pages/publication.aspx?docnum=9303) page instead

---

## [3.0.0] - 2026-11-21

Complete rewrite of the reading pipeline. The public API is unchanged.

### Removed

- **Tesseract OCR and `pytesseract` (removed in v3).** No system dependency and no `mrz.traineddata` / tessdata to install.
- The ONNX segmentation model `mrz_seg.onnx` and the `setup.py` / `MANIFEST.in` packaging files.

### Added

- Built-in 2.4 MB ONNX CTC line recogniser (`mrz_rec.onnx`), run through OpenCV
- Classical-CV MRZ detector that works at any rotation, skew and perspective
- Check-digit guided repair of misread characters
- `input_type="bytes"` for encoded image bytes
- `input_type="pdf"` (optional extra: `pip install "fastmrz[pdf]"`)
- `get_details_batch()` for parallel processing of many documents
- `get_mrz_image()` returning the rectified MRZ strip
- `model_path` argument to load a custom recogniser
- Type hints (`py.typed`) and exported `InputType`, `InputData`, `MRZDetails` types
- `"Invalid date of birth"` / `"Invalid date of expiry"` status messages

### Changed

- `tesseract_path` and `tessdata_path` are deprecated and ignored (Tesseract removed in v3); passing them raises a `FutureWarning`
- Dependencies are now `numpy` and `opencv-python-headless>=4.8`

### Fixed

- Lines dropped or MRZ not found (e.g. Chinese passports whose line 2 has no `<`)
- Rotated or skewed images not read
- `<` as an empty optional-data check digit reported as invalid
- TD1 optional data read from the wrong place; long TD1 document numbers not joined
- Crashes on a missing given name or invalid dates

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
- Custom trained data (`mrz.traineddata`) for the OCR engine (Tesseract, removed in v3)

### Changed

- Complete rewrite of the extraction pipeline
- Replaced traditional image processing with ML-based segmentation
- Improved accuracy for challenging document images

---

## [1.0] - Initial Release

### Added

- Basic MRZ extraction from passport images
- Tesseract OCR integration (removed in v3)
- Contour detection for MRZ region identification
- Support for TD3 (passport) documents
- JSON output format

---

## Version Summary

| Version | Release Date | Key Features |
|---------|--------------|--------------|
| 3.1.0 | 2026-11-21 | PDF support by default, updated recogniser model, security policy, issue and PR templates |
| 3.0.0 | 2026-11-21 | Tesseract removed, built-in ONNX recogniser, PDF and batch input |
| 2.1 | 2024 | MRVA/MRVB support, validation, multiple input formats |
| 2.0 | 2024 | ONNX model, complete pipeline rewrite |
| 1.0 | - | Initial MRZ extraction |

---

## Migration Guide

### From 2.x to 3.0

Version 3.0 keeps the 2.x API, so existing code runs unchanged:

1. **Nothing extra to install:** Tesseract and `mrz.traineddata` are no longer used (removed in v3).

2. **Constructor arguments:** `tesseract_path` and `tessdata_path` are ignored (Tesseract removed in v3) and raise a `FutureWarning`. Remove them:
   ```python
   fast_mrz = FastMRZ()
   ```

3. **Output:** the same keys and `status` / `status_message` values. Invalid dates are now reported (`"Invalid date of birth"`, `"Invalid date of expiry"`) and returned as the raw `YYMMDD`.

4. **PDF input:** supported out of the box since 3.1.0 (in 3.0.0 it needed `pip install "fastmrz[pdf]"`).

### From 1.x to 2.x

Version 2.0 introduced significant changes:

1. **ONNX Model**: The extraction pipeline now uses an ONNX segmentation model. In 2.x, the `mrz.traineddata` file also had to be installed (no longer needed: removed in v3).

2. **Output Format**: The output dictionary structure may have changed. Check the [API Reference](api-reference.md) for the current format.

3. **OCR engine path**: In 2.x, if the OCR engine was not in your PATH, you had to pass `tesseract_path` explicitly. This argument is ignored since Tesseract was removed in v3.

### From 2.0 to 2.1

Version 2.1 is backward compatible with 2.0. New features are additive:

- `validate_mrz()` method is new
- `include_checkdigit` parameter is new (defaults to `True` for compatibility)
- `status_message` replaces `message` in output

---

## Release Process

Releases are published to PyPI. To install a specific version:

```bash
pip install fastmrz==3.1.0
```

---

## Links

- [PyPI Releases](https://pypi.org/project/fastmrz/#history)
- [GitHub Releases](https://github.com/sivakumar-mahalingam/fastmrz/releases)
- [Issue Tracker](https://github.com/sivakumar-mahalingam/fastmrz/issues)
