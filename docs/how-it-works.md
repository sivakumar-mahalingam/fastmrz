# How It Works

This document explains the internal architecture and processing pipeline of FastMRZ 3.

!!! note "Changed in v3"
    Up to 2.x, FastMRZ located the MRZ with an ONNX segmentation model and read it with Tesseract OCR.
    Tesseract was **removed in v3**: detection is now classical computer vision, and the text is read
    by FastMRZ's own small recogniser network. The public API is unchanged.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                   FastMRZ Processing Pipeline                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────┐   ┌──────────┐   ┌──────────┐   ┌────────────┐         │
│  │ Input  │──▶│  Detect  │──▶│ Rectify  │──▶│ Recognise  │         │
│  │ image  │   │ (OpenCV) │   │ 32 x 640 │   │ (ONNX CTC) │         │
│  └────────┘   └──────────┘   └──────────┘   └─────┬──────┘         │
│                                                   │                │
│                    ┌──────────────────┐   ┌───────▼──────┐         │
│                    │      Select      │◀──│    Repair    │         │
│                    │ (score, agree)   │   │ (check digits│         │
│                    └────────┬─────────┘   │  & charsets) │         │
│                             │             └──────────────┘         │
│                    ┌────────▼─────────┐                            │
│                    │ Parse & validate │                            │
│                    │   (ICAO 9303)    │                            │
│                    └────────┬─────────┘                            │
│                             ▼                                      │
│                       dict / text                                  │
└────────────────────────────────────────────────────────────────────┘
```

| Step | What it does |
|---|---|
| Detect | Classical CV (blackhat, local contrast, morphological closing) finds 2-3 parallel text lines of equal length. Works at any rotation (with extra diagonal passes), skew and perspective. |
| Rectify | Each line is perspective-warped to a 32 x 640 strip, in both reading directions. |
| Recognise | A 2.5 MB fully convolutional CTC network (ONNX, run through `cv2.dnn`) reads the whole line at once and returns per-character probabilities. |
| Repair | Line length is fitted to the format, positional character sets are enforced, and failing check digits may trigger a few substitutions among the recogniser's own second choices. |
| Select | Candidates are scored by check digits, date validity, known ICAO country codes, confidence and number of repairs. |

The code lives in four modules:

| Module | Responsibility |
|---|---|
| `fastmrz/detector.py` | Locating MRZ candidates and warping each line to a strip |
| `fastmrz/recognizer.py` | Running the ONNX line recogniser and CTC decoding |
| `fastmrz/parser.py` | Format detection, repair, check digits, field parsing |
| `fastmrz/fastmrz.py` | Public `FastMRZ` class, input loading and the search loop |

---

## Processing Pipeline

### Step 1: Input loading

Every image input (`imagepath`, `numpy`, `base64`, `bytes`, `pdf`) is decoded with OpenCV (PDF pages are rendered at 200 dpi with PyMuPDF) and converted to a greyscale `uint8` image. `text` input skips straight to parsing.

### Step 2: Detection

The detector (`find_candidates`) uses no neural network. On a resized copy of the image it:

1. Applies a **blackhat** transform to highlight dark print on a light background.
2. Normalises **local contrast** so faint MRZ print survives next to strong edges.
3. **Closes** characters into line-shaped blobs: either a horizontal smear (robust for roughly upright documents) or an isotropic closing that works at any rotation, because the gap between MRZ characters is much smaller than the gap between MRZ lines.
4. Fits rotated boxes to the blobs, merges collinear pieces, and groups 2 or 3 **parallel, equally long** lines into MRZ candidates.

Each candidate is a list of quadrilaterals, one per MRZ line, in source-image coordinates. Recall matters more than precision here: false candidates are rejected later by the recogniser and the check digits.

### Step 3: Rectification

Each line quadrilateral is refined and perspective-warped (`warp_line`) to a 32 x 640 greyscale strip. Every candidate is read in both directions (normal and rotated 180°), so upside-down documents are handled without knowing the orientation in advance.

`get_mrz_image()` returns exactly these strips, stacked top to bottom.

### Step 4: Recognition

The strips are contrast-stretched and passed in a single batch to the recogniser (`fastmrz/model/mrz_rec.onnx`):

- **Architecture:** fully convolutional network with a CTC output over the 37 MRZ characters (`0-9`, `A-Z`, `<`)
- **Size:** 2.5 MB, run through OpenCV's DNN module, so no extra ML runtime is needed
- **Data:** trained on synthetically generated MRZ lines

Greedy CTC decoding returns, for each line, the text, a probability vector for every character, and a confidence score. Those per-character alternatives drive the repair step.

### Step 5: Repair

`parser.repair()` turns the raw recognition into a well-formed MRZ:

- **Format fit:** the line count and length decide the format (TD1 3x30, TD2/MRV-B 2x36, TD3/MRV-A 2x44), and lines are fitted to that length.
- **Positional character sets:** positions that must be digits (dates, check digits) or letters (country codes) are forced to the most probable character of the right class.
- **Issuer correction:** an issuing-state code that differs from the nationality by one or two letters the recogniser also considered is corrected.
- **Check-digit guided fixes:** when a check digit fails, at most two substitutions among the recogniser's own second choices are tried. As a last resort only the check digits themselves are re-read, and the result is accepted only if every check then passes.

Readings that would need more than six edits are discarded as "not an MRZ".

### Step 6: Selection

Detection runs in stages, from cheap and common settings to exhaustive ones (extra scales, isotropic closing, ±30/45/60° rotations). Each reading is scored by:

- the fraction of check digits that pass,
- recogniser confidence,
- number of repairs (penalised),
- invalid dates and unknown country codes (penalised).

The search stops as soon as a reading is valid and needed at most one repair, or when two independent detector stages agree on the same reading. Low-quality readings are rejected, and `get_details` then returns `{"status": "FAILURE", "status_message": "No MRZ detected"}`.

### Step 7: Parsing

The selected lines are parsed according to ICAO Doc 9303:

| Document Type | Detection Logic |
|---------------|-----------------|
| **TD1** | 3 lines, 30 chars each |
| **TD2** | 2 lines, 36 chars each, document code does not start with `V` |
| **MRVB** | 2 lines, 36 chars each, document code starts with `V` |
| **TD3** | 2 lines, 44 chars each, document code does not start with `V` |
| **MRVA** | 2 lines, 44 chars each, document code starts with `V` |

TD1 document numbers longer than 9 characters, which continue in the optional data field, are joined back together.

### Step 8: Date formatting

MRZ dates are `YYMMDD`. FastMRZ returns them as `YYYY-MM-DD`:

- **Birth dates** are placed in the most recent century that is not in the future.
- **Expiry dates** are placed between the recent past and 50 years ahead.
- Partially unknown dates (month or day `00`) are kept. A date that is not a calendar date is returned as the raw `YYMMDD`, and the status message reports it.

### Step 9: Checksum validation

All ICAO 9303 check digits are verified with the 7-3-1 weighting (see [Checksum Validation](checksum-validation.md)):

- Document number
- Date of birth
- Date of expiry
- Optional data (TD3; a `<` check digit is accepted when the optional data is empty)
- Final composite check digit (TD1, TD2, TD3)

`status` is `"SUCCESS"` only when the format and every check digit are valid. Otherwise it is `"FAILURE"` and `status_message` names the first problem found.

---

## Input Type Handling

| Input Type | Processing |
|------------|------------|
| `imagepath` | Reads the file bytes and decodes them with OpenCV |
| `numpy` | Uses the array directly (BGR colour or greyscale) |
| `base64` | Strips an optional `data:` prefix, decodes, then decodes the image |
| `bytes` | Decodes the encoded image (JPEG, PNG, ...) |
| `pdf` | Renders up to 10 pages with PyMuPDF; the first page with an MRZ wins |
| `text` | Skips image processing; parses the MRZ text directly (no auto-correction) |

---

## Error Handling

```python
# Successful extraction
{
    "mrz_type": "TD3",
    "document_code": "P",
    ...
    "status": "SUCCESS"
}

# No MRZ found
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

Inputs that cannot be read at all (missing file, undecodable image, bad base64, unsupported `input_type`, PDF without PyMuPDF) raise `ValueError`. `get_details_batch` turns those into `FAILURE` entries instead.

---

## Performance Considerations

- **Model loading:** the ONNX model is read once in `FastMRZ()`. Each thread gets its own OpenCV network, so one instance can be shared across threads.
- **Speed:** about 0.11 s per image on average on a CPU. Most images are settled by the first detector stage.
- **Batching:** `get_details_batch` processes inputs on a thread pool (up to 8 workers by default).
- **Minimal dependencies:** only `numpy`, `opencv-python-headless` and `pymupdf` (for PDFs).

---

## Next Steps

- Explore the [API Reference](api-reference.md) for detailed method documentation
- Learn about [checksum validation](checksum-validation.md) in depth
- Review known [limitations](limitations.md)
