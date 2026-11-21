# Limitations

This document outlines the current limitations and known issues of FastMRZ.

---

## Image Processing Limitations

### Resolution Sensitivity

The ONNX segmentation model resizes all input images to **256x256 pixels** before inference. This fixed resolution may cause issues:

- **Very low-resolution images**: MRZ text may become unreadable after downscaling
- **Very high-resolution images**: Fine details may be lost during resizing

**Recommendation:** Use images with a resolution where the MRZ region is clearly visible but not excessively large (recommended: 1000-2000 pixels wide).

### Image Quality Dependence

OCR accuracy depends heavily on image quality:

- **Blurry images**: May result in failed MRZ detection or incorrect character recognition
- **Poor lighting**: Shadows, glare, or uneven lighting can obscure the MRZ region
- **Low contrast**: MRZ text must have sufficient contrast against the background
- **Skewed documents**: While the contour detection handles some skew, extreme angles may cause detection failure

**Recommendation:** Capture documents in well-lit conditions with the camera parallel to the document surface.

### No Image Enhancement

FastMRZ does not currently include automatic image enhancement:

- No automatic brightness/contrast adjustment
- No automatic deskew correction
- No noise reduction beyond basic morphological operations
- No super-resolution for low-quality images

**Workaround:** Pre-process images using OpenCV or other libraries before passing them to FastMRZ:

```python
import cv2
import numpy as np
from fastmrz import FastMRZ

fast_mrz = FastMRZ()

# Load and enhance image
image = cv2.imread("passport.jpg")

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply sharpening
kernel = np.array([[-1, -1, -1],
                   [-1,  9, -1],
                   [-1, -1, -1]])
sharpened = cv2.filter2D(gray, -1, kernel)

# Apply adaptive thresholding
binary = cv2.adaptiveThreshold(
    sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY, 11, 2
)

# Convert back to 3-channel for FastMRZ
enhanced = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

result = fast_mrz.get_details(enhanced, input_type="numpy")
```

---

## Feature Limitations

### No PDF Support

PDF input is not yet implemented. The `input_type="pdf"` parameter exists in the code but is non-functional.

**Workaround:** Convert PDFs to images before processing:

```python
# Using PyMuPDF (fitz)
import fitz

doc = fitz.open("document.pdf")
for page_num in range(len(doc)):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=300)
    pix.save(f"page_{page_num}.png")
    result = fast_mrz.get_details(f"page_{page_num}.png")
```

### No Bulk Processing

FastMRZ processes one document at a time. There is no built-in batch processing functionality.

**Workaround:** Implement your own loop:

```python
import os
from fastmrz import FastMRZ

fast_mrz = FastMRZ()
results = {}

for filename in os.listdir("documents/"):
    if filename.endswith((".jpg", ".png")):
        filepath = os.path.join("documents/", filename)
        results[filename] = fast_mrz.get_details(filepath)
```

### No Face Extraction

FastMRZ does not extract the photograph from the document. It only extracts the MRZ text region.

### No MRZ Generation

FastMRZ cannot generate MRZ text from structured data. It only parses existing MRZ text.

### No `get_mrz_image` Function

The ability to extract and return the cropped MRZ image region is not implemented.

---

## Model Limitations

### Single ONNX Model

FastMRZ uses a single segmentation model (`mrz_seg.onnx`) trained on a specific dataset:

- The model may not generalize well to all document types or layouts
- Documents with unusual MRZ placements may not be detected
- The model was trained on 256x256 images, which limits its resolution handling

### No Confidence Scores

The model output is thresholded at 0.25, but confidence scores are not exposed to the user. There is no way to know how confident the model is about its detection.

### No Multi-Region Detection

If a document contains multiple MRZ regions (e.g., a scanned page with multiple passports), only the largest detected region is processed.

---

## OCR Limitations

### Tesseract Dependency

FastMRZ relies on Tesseract OCR, which has its own limitations:

- Requires external installation (not bundled with the package)
- Requires manual installation of the custom `mrz.traineddata` file
- Tesseract accuracy varies with font, size, and image quality
- Some characters may be confused (e.g., `0` vs `O`, `1` vs `I`)

### Custom Trained Data Required

The custom `mrz.traineddata` file must be manually copied to the Tesseract tessdata folder. Without it, OCR accuracy will be significantly lower.

### Limited Language Support

The MRZ trained data is optimized for the restricted MRZ character set (A-Z, 0-9, `<`). It is not suitable for general text recognition.

---

## Validation Limitations

### Checksum Validation Only

FastMRZ validates check digits but does not validate:

- Country code authenticity (any 3-letter code is accepted)
- Document number format validity
- Date reasonableness (e.g., future birth dates are not flagged)
- Document expiry status (expired documents are still parsed)

### No Cross-Field Validation

There is no validation that checks relationships between fields:

- Issuer code vs. nationality code consistency
- Document code vs. document type consistency
- Optional data format validation

### Incomplete Check Digit Status

Not all check digit statuses are fully implemented. The TODO list indicates this is a planned improvement.

---

## Platform Limitations

### Operating System Support

FastMRZ is tested on:
- macOS
- Linux (POSIX)
- Windows 10/11

Other platforms (e.g., mobile, embedded systems) are not officially supported.

### Python Version

Requires Python 3.8 or higher. Older versions are not supported.

### Architecture

The ONNX model is run via OpenCV's DNN module, which may have different performance characteristics on different CPU architectures (x86, ARM, etc.).

---

## Security Considerations

### No Encryption

FastMRZ does not encrypt data in memory or during processing. MRZ data contains sensitive personal information.

### No Input Sanitization

The package does not sanitize or redact MRZ data in logs or error messages.

### AGPL License

FastMRZ is licensed under AGPL-3.0. If you modify and distribute the software (or use it in a network service), you must make your modifications available under the same license.

---

## Planned Improvements

The following improvements are tracked in the project's TODO list:

- [ ] PDF input support
- [ ] Bulk/batch processing
- [ ] Image enhancement model parameter
- [ ] Text image enhancement model
- [ ] Improved Tesseract model training
- [ ] `get_mrz_image` function
- [ ] `generate_mrz` function
- [ ] Face image extraction
- [ ] Complete check digit status reporting
- [ ] Documentation website

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
