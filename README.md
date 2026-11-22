# FastMRZ

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/fastmrz?logo=pypi&logoColor=959DA5&color=blue)](https://pypi.org/project/fastmrz/)
![Python](https://img.shields.io/badge/python-3.8+-blue?logo=python&logoColor=959DA5)
[![Downloads](https://static.pepy.tech/badge/fastmrz)](https://pypistats.org/packages/fastmrz)
[![CodeQL](https://github.com/sivakumar-mahalingam/fastmrz/actions/workflows/codeql.yml/badge.svg)](https://github.com/sivakumar-mahalingam/fastmrz/actions/workflows/codeql.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-34D058?color=blue)](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/LICENSE)
[![DeepWiki](https://img.shields.io/badge/DeepWiki-fastmrz-blue.svg)](https://deepwiki.com/sivakumar-mahalingam/fastmrz)
[![Known Vulnerabilities](https://img.shields.io/badge/Snyk_security-monitored-blue)](https://security.snyk.io/package/pip/fastmrz)
[![CodeFactor](https://www.codefactor.io/repository/github/sivakumar-mahalingam/fastmrz/badge)](https://www.codefactor.io/repository/github/sivakumar-mahalingam/fastmrz)
[![llms.txt](https://img.shields.io/badge/llms.txt-%E2%9C%93-blue)](https://context7.com/sivakumar-mahalingam/fastmrz/llms.txt)

<a href="https://github.com/sivakumar-mahalingam/fastmrz/" target="_blank">
    <img src="https://raw.githubusercontent.com/sivakumar-mahalingam/fastmrz/main/docs/FastMRZ.png" alt="FastMRZ" />
</a>

**A lightweight Python MRZ reader for passports, ID cards and visas.**

FastMRZ uses OpenCV to detect and rectify the MRZ, then reads it with a bundled ONNX model. It does not use or
require Tesseract, PaddleOCR, PyTorch or a GPU. Images, PDFs or raw MRZ text in; validated, parsed fields out.

[Quick start](#quick-start) •
[Features](#features) •
[Installation](#installation) •
[Usage](#usage) •
[API reference](#api-reference) •
[How it works](#how-it-works) •
[FAQ](#faq) •
[Documentation](#documentation) •
[Contributing](#contributing)

</div>

## Quick start

```bash
pip install fastmrz
```

```python
from fastmrz import FastMRZ

fast_mrz = FastMRZ()
details = fast_mrz.get_details("data/td3.jpg")
```

```json
{
    "mrz_type": "TD3",
    "document_code": "P",
    "issuer_code": "UTO",
    "document_number": "L898902C3",
    "surname": "ERIKSSON",
    "given_name": "ANNA MARIA",
    "document_number_checkdigit": "6",
    "nationality_code": "UTO",
    "birth_date": "1974-08-12",
    "birth_date_checkdigit": "2",
    "sex": "F",
    "expiry_date": "2012-04-15",
    "expiry_date_checkdigit": "9",
    "optional_data": "ZE184226B",
    "optional_data_checkdigit": "1",
    "final_checkdigit": "0",
    "mrz_text": "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10",
    "status": "SUCCESS"
}
```

## Features

- **Robust OpenCV detection:** finds and rectifies the MRZ at any rotation, skew or perspective, including small documents in a larger scene.
- **Built-in ONNX recognition:** a 2.5 MB model, trained on synthetic MRZ data, reads the rectified lines through OpenCV DNN. No external OCR engine or service is required.
- **ICAO 9303 validation:** every check digit is verified, and failing check digits trigger automatic repair of misread characters.
- **All standard formats:** TD1, TD2, TD3 (passports), MRV-A and MRV-B (visas).
- **Flexible input:** image path, NumPy array, Base64, encoded bytes, PDF, or MRZ text.
- **Batch processing:** `get_details_batch` reads many documents in parallel; one unreadable file never stops the batch.
- **Typed API:** ships with `py.typed` and exported `MRZDetails`, `InputType` and `InputData` types.

## Installation

```bash
pip install fastmrz
```

From source:

```bash
git clone https://github.com/sivakumar-mahalingam/fastmrz.git
cd fastmrz
pip install .
```

| Dependency | Supported | Tested |
|---|---|---|
| Python | 3.8 or newer | 3.8, 3.9, 3.10, 3.11, 3.12, 3.13 |
| numpy | any version that matches your OpenCV | 1.24.4 to 2.5.5 |
| opencv-python-headless | 4.8 or newer | 4.8.1, 5.0.0, 5.1.0 |
| PyMuPDF | 1.23 or newer, except 1.26.5 and 1.26.6 (security advisory) | 1.23.26, 1.24.11, 1.26.4, 2.1 |

All dependencies are installed automatically by pip. PDF support is included by default.

> **Upgrading from 2.x:** the public API is unchanged. Tesseract and `mrz.traineddata` are no longer used, and
> `tesseract_path` / `tessdata_path` are ignored (they raise a `FutureWarning`). See the
> [migration guide](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/docs/changelog.md#migration-guide).

## Usage

```python
from fastmrz import FastMRZ

fast_mrz = FastMRZ()   # loads the model once; safe to share across threads

# Parsed fields from any supported input
details = fast_mrz.get_details("data/td3.jpg")                    # image path (str or pathlib.Path)
details = fast_mrz.get_details(image_array, input_type="numpy")   # BGR or greyscale ndarray
details = fast_mrz.get_details(b64_string, input_type="base64")   # data: URIs allowed
details = fast_mrz.get_details(image_bytes, input_type="bytes")   # encoded JPEG, PNG, ...
details = fast_mrz.get_details("scan.pdf", input_type="pdf")      # path or bytes
details = fast_mrz.get_details(mrz_string, input_type="text")     # parse only, no OCR

# Raw MRZ text instead of parsed fields
text = fast_mrz.get_details("data/td3.jpg", ignore_parse=True)

# Many documents in parallel, results in input order
results = fast_mrz.get_details_batch(["a.jpg", "b.jpg", "c.jpg"])

# Validate MRZ text
fast_mrz.validate_mrz(text)   # {"is_valid": True, "status_message": "The given mrz is valid"}

# Rectified MRZ crop, e.g. for display or auditing
strip = fast_mrz.get_mrz_image("data/td3.jpg")
```

### Handling results

Check `status` before using the fields. A document is `SUCCESS` only when the format and every check digit are valid.

```python
details = fast_mrz.get_details(path)
if details["status"] == "SUCCESS":
    print(details["document_number"], details["expiry_date"])
else:
    print("Rejected:", details["status_message"])
```

Inputs that cannot be read at all (missing file, undecodable image, invalid Base64 or PDF) raise `ValueError` from
`get_details`. `get_details_batch` reports them as `FAILURE` entries instead.

## API reference

### `FastMRZ(tesseract_path="", tessdata_path="", model_path=None)`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `model_path` | `str \| PathLike \| None` | `None` | Custom recogniser ONNX model; defaults to the bundled one |
| `tesseract_path`, `tessdata_path` | `str` | `""` | Deprecated and ignored; passing a value raises `FutureWarning` |

### Methods

| Method | Returns | Raises |
|---|---|---|
| `get_details(input_data, input_type="imagepath", ignore_parse=False, include_checkdigit=True)` | `dict[str, str]`; with `ignore_parse=True` the MRZ text (`""` if none found) | `ValueError` if the input can't be read |
| `get_details_batch(inputs, input_type="imagepath", ignore_parse=False, include_checkdigit=True, workers=None)` | `list` of `get_details` results, in input order | Never per input: unreadable inputs become `FAILURE` entries |
| `get_mrz_image(input_data, input_type="imagepath")` | `numpy.ndarray` (grey `uint8`, 32 x 640 per MRZ line) or `None` | `ValueError` if the input can't be read |
| `validate_mrz(mrz_text)` | `{"is_valid": bool, "status_message": str}` | - |

`workers` defaults to the number of CPUs, capped at 8. Expect roughly 1.5x the throughput of a plain loop on a
4-core CPU, since OpenCV already parallelises work within each image.

### `input_type`

| Value | `input_data` |
|---|---|
| `"imagepath"` | Path to an image file (`str` or `pathlib.Path`) |
| `"numpy"` | Image array, BGR colour or greyscale |
| `"base64"` | Base64 encoded image file; `data:image/...;base64,` prefix allowed |
| `"bytes"` | Encoded image file (JPEG, PNG, ...) |
| `"pdf"` | Path or bytes of a PDF; the first page (of up to 10) with an MRZ is used |
| `"text"` | MRZ text, lines separated by `\n`; parsed only, never auto-corrected |

### Output fields

All values are strings. Check-digit keys are omitted with `include_checkdigit=False`.

| Key | Formats | Example | Description |
|---|---|---|---|
| `mrz_type` | all | `TD3` | `TD1`, `TD2`, `TD3`, `MRVA` or `MRVB` |
| `document_code` | all | `P` | Document type (`P`, `I`, `ID`, `V`, ...) |
| `issuer_code` | all | `UTO` | Issuing state |
| `document_number` | all | `L898902C3` | Long TD1 numbers continued in the optional data are joined |
| `document_number_checkdigit` | all | `6` | |
| `surname` | all | `ERIKSSON` | |
| `given_name` | all | `ANNA MARIA` | Given names separated by spaces |
| `nationality_code` | all | `UTO` | May be empty |
| `birth_date` | all | `1974-08-12` | `YYYY-MM-DD`; the raw `YYMMDD` if it isn't a calendar date |
| `birth_date_checkdigit` | all | `2` | |
| `sex` | all | `F` | `M`, `F`, `X` or `<` |
| `expiry_date` | all | `2012-04-15` | `YYYY-MM-DD`; the raw `YYMMDD` if it isn't a calendar date |
| `expiry_date_checkdigit` | all | `9` | |
| `optional_data` | TD2, TD3, MRVA, MRVB | `ZE184226B` | Personal number / optional data, fillers removed |
| `optional_data_checkdigit` | TD3 | `1` | |
| `optional_data_1`, `optional_data_2` | TD1 | | Optional data of line 1 and line 2 |
| `final_checkdigit` | TD1, TD2, TD3 | `0` | Composite check digit |
| `mrz_text` | all | | The MRZ lines joined by `\n` |
| `status` | all | `SUCCESS` | `SUCCESS` when the format and every check digit are valid, else `FAILURE` |
| `status_message` | on failure | `Final checksum is not matching` | First problem found |

When no MRZ is found the result is `{"status": "FAILURE", "status_message": "No MRZ detected"}`.

Other `status_message` values: `Invalid MRZ format`, `Invalid date of birth`, `Invalid date of expiry`,
`Document number checksum is not matching`, `Date of birth checksum is not matching`,
`Date of expiry checksum is not matching`, `Optional data checksum is not matching`.

## How it works

| Stage | What happens |
|---|---|
| Detect | Classical computer vision locates 2-3 parallel text lines of equal length, at any rotation, skew or perspective. |
| Rectify | Each line is perspective-warped to a fixed-size strip, in both reading directions. |
| Recognise | A fully convolutional CTC network reads each line and returns per-character probabilities. |
| Repair | Line lengths and positional character sets are enforced; failing check digits trigger substitutions among the recogniser's second choices. |
| Select | Candidates are ranked by check digits, date validity, known ICAO country codes and confidence. |

![MRZ GIF](https://raw.githubusercontent.com/sivakumar-mahalingam/fastmrz/main/docs/mrz.gif)

### Supported documents

| Format | Lines x characters | Typical documents |
|---|---|---|
| TD1 | 3 x 30 | National ID cards, EU ID cards, US Green Card |
| TD2 | 2 x 36 | Older ID cards |
| TD3 | 2 x 44 | Passports (MRP) |
| MRV-A | 2 x 44 | Full-size visas (USA, Japan, China, ...) |
| MRV-B | 2 x 36 | Smaller visas (e.g. Schengen) |

All formats follow [ICAO Doc 9303](https://www.icao.int/publications/doc-series/doc-9303).

## FAQ

### Does FastMRZ use Tesseract?

No. FastMRZ 3.x uses a bundled ONNX recogniser and does not use or require Tesseract or `mrz.traineddata`.
The deprecated `tesseract_path` and `tessdata_path` parameters remain temporarily for backward compatibility but
are ignored.

### Is FastMRZ a drop-in replacement for PassportEye?

FastMRZ is a lightweight alternative for the same core use case, but its API is not compatible with PassportEye.
Use `FastMRZ.get_details` as shown in the [quick start](#quick-start) when migrating.

## Documentation

The documentation is maintained in the [`docs`](https://github.com/sivakumar-mahalingam/fastmrz/tree/main/docs) directory:

- [Getting started](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/docs/getting-started.md): installation and setup
- [How it works](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/docs/how-it-works.md): architecture and processing pipeline
- [API reference](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/docs/api-reference.md): complete API documentation
- [Supported documents](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/docs/supported-documents.md): document types and MRZ formats
- [Input formats](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/docs/input-formats.md): supported input types
- [Checksum validation](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/docs/checksum-validation.md): ICAO check digit details
- [Limitations](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/docs/limitations.md): known limitations
- [Changelog](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/docs/changelog.md): version history and migration guide

## Roadmap

- Face image extraction
- Per-field check digit status
- `generate_mrz` to build an MRZ from structured data

Suggestions are welcome: open a [feature request](https://github.com/sivakumar-mahalingam/fastmrz/issues/new/choose).

## Contributing

Contributions are welcome. Read the [contributing guide](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/docs/contributing.md)
for the development setup and conventions, then:

```bash
git clone https://github.com/<your-username>/fastmrz.git
cd fastmrz
pip install -e .
python -m unittest tests.test_fastmrz
```

Open an [issue](https://github.com/sivakumar-mahalingam/fastmrz/issues/new/choose) to report a bug or propose an
improvement, and use the pull request template when submitting changes.

Please do not attach real identity documents to issues or pull requests; use synthetic or redacted samples.

## Security

Report vulnerabilities privately as described in the [security policy](.github/SECURITY.md). Do not open public issues
for security problems.

## Community

- If FastMRZ is useful to you, consider [starring the repository](https://github.com/sivakumar-mahalingam/fastmrz).
- If your organization or project uses FastMRZ, share your use case by opening an issue titled
  `We are using FastMRZ!`.

Do not include identity documents or other sensitive data.

## License

FastMRZ is licensed under the [Apache License 2.0](LICENSE).
