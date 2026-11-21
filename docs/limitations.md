# Limitations

This document outlines the current limitations and known issues of FastMRZ 3.

---

## Recognition Limitations

### Known misses

Known weak spots:

- **Non-standard line length:** some documents print a 43-character line. The output is padded to the standard 44.
- **Look-alike characters without a check digit:** `0`/`O`, `0`/`D` and `O`/`Q` in names, optional data or alphanumeric document numbers depend purely on the glyph shape. Fonts far from OCR-B are less reliable there. Fields with a check digit are repaired automatically.
- **Very small print:** MRZ characters smaller than about 8 px high are not readable.

**Recommendation:** capture the document so the MRZ is reasonably sharp and its characters are at least ~10 px tall. Rotation, perspective, moderate blur, JPEG compression, dim lighting and noise are handled.

### No confidence scores

The recogniser's confidence is used internally to choose between readings, but it is not exposed. Readings that are too uncertain are rejected and reported as `"No MRZ detected"` instead of returned.

### One MRZ per image

If an image contains several MRZs (e.g. a scanned page with multiple documents), only the best-scoring one is returned. For PDFs, only the first page (of up to 10) with an MRZ is used.

---

## Feature Limitations

### No Face Extraction

FastMRZ does not extract the photograph from the document. It only reads the MRZ.

### No MRZ Generation

FastMRZ cannot generate MRZ text from structured data. It only parses existing MRZ text.

### Text input is not auto-corrected

`input_type="text"` parses the MRZ exactly as given. The check-digit guided repair only applies to images, where the recogniser's per-character alternatives are known.

### PDF input needs an extra

`input_type="pdf"` requires PyMuPDF (`pip install "fastmrz[pdf]"`). Pages are rendered at 200 dpi.

---

## Validation Limitations

### Checksum and format validation only

FastMRZ validates the format, dates and check digits, but does not validate:

- Country code authenticity (unknown codes lower a reading's score, but are not reported as errors)
- Document number format validity
- Document expiry status (expired documents are still parsed and reported as `SUCCESS`)

### No Cross-Field Validation

There is no validation that checks relationships between fields:

- Issuer code vs. nationality code consistency
- Document code vs. document type consistency
- Optional data format validation

### First problem only

When validation fails, `status_message` names the first problem found, not every failing check digit.

---

## Platform Limitations

### Operating System Support

FastMRZ is tested on:

- macOS
- Linux (POSIX)
- Windows 10/11

Other platforms (e.g., mobile, embedded systems) are not officially supported.

### Python Version

Requires Python 3.8 or higher.

### Architecture

The ONNX recogniser is run via OpenCV's DNN module, which may have different performance characteristics on different CPU architectures (x86, ARM, etc.).

---

## Security Considerations

### No Encryption

FastMRZ does not encrypt data in memory or during processing. MRZ data contains sensitive personal information.

### No Redaction

The package does not sanitize or redact MRZ data in its return values. Take care when logging results.

### AGPL License

FastMRZ is licensed under AGPL-3.0. If you modify and distribute the software (or use it in a network service), you must make your modifications available under the same license.

---

## Resolved in v3

These limitations of 2.x no longer apply:

- **Tesseract dependency:** removed in v3. There is no system dependency and no `mrz.traineddata` to install.
- **Rotated or skewed images:** detection works at any rotation, skew and perspective.
- **Fixed 256x256 segmentation crop:** replaced by multi-scale line detection.
- **No PDF support:** `input_type="pdf"`.
- **No bulk processing:** `get_details_batch()`.
- **No `get_mrz_image`:** implemented.
- **Valid MRZs reported as invalid:** check rules now follow ICAO 9303 (e.g. `<` as an empty optional-data check digit).

---

## Planned Improvements

- [ ] Image enhancement model parameter
- [ ] Text image enhancement model
- [ ] `generate_mrz` function
- [ ] Face image extraction
- [ ] Complete check digit status reporting

---

## Reporting Issues

If you encounter issues not documented here, please:

1. Check the [Issue Tracker](https://github.com/sivakumar-mahalingam/fastmrz/issues) for existing reports
2. Open a new issue with:
   - A description of the problem
   - Sample image (if possible)
   - Expected vs. actual output
   - System information (OS, Python version, FastMRZ version)

---

## Next Steps

- Learn about [checksum validation](checksum-validation.md)
- Review the [contributing guide](contributing.md)
- Check the [changelog](changelog.md) for version history
