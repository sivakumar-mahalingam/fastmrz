# API Reference

Complete documentation for the FastMRZ Python API.

Type hints are included (`py.typed`), so editors and type checkers see the types below. The package exports:

```python
from fastmrz import FastMRZ, InputData, InputType, MRZDetails
```

| Name | Definition |
|---|---|
| `FastMRZ` | The main class |
| `InputType` | `Literal["imagepath", "numpy", "base64", "bytes", "pdf", "text"]` |
| `InputData` | `Union[str, os.PathLike[str], bytes, bytearray, numpy.ndarray]` |
| `MRZDetails` | `Dict[str, str]`, the parsed result |

---

## FastMRZ Class

The main class for MRZ extraction and validation. One instance can be shared by several threads.

### `__init__`

```python
FastMRZ(
    tesseract_path: str = "",
    tessdata_path: str = "",
    model_path: Optional[Union[str, os.PathLike[str]]] = None,
)
```

Initialize the FastMRZ engine and load the recogniser model.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tesseract_path` | `str` | `""` | Deprecated and ignored: Tesseract was removed in v3. Passing a value raises a `FutureWarning`. |
| `tessdata_path` | `str` | `""` | Deprecated and ignored, like `tesseract_path`. |
| `model_path` | `str \| PathLike \| None` | `None` | Replacement recogniser ONNX model. Defaults to the bundled `fastmrz/model/mrz_rec.onnx`. |

**Example:**

```python
from fastmrz import FastMRZ

fast_mrz = FastMRZ()

# With a custom recogniser model
fast_mrz = FastMRZ(model_path="models/mrz_rec.onnx")
```

**Raises:**

The model is loaded here, so a missing or invalid `model_path` fails immediately (`OSError` / `cv2.error`).

---

### `get_details`

```python
get_details(
    input_data: InputData,
    input_type: InputType = "imagepath",
    ignore_parse: bool = False,
    include_checkdigit: bool = True,
) -> Union[MRZDetails, str]
```

Read and parse the MRZ of one document.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_data` | `InputData` | Required | The document, in the form given by `input_type`. |
| `input_type` | `InputType` | `"imagepath"` | One of `"imagepath"`, `"numpy"`, `"base64"`, `"bytes"`, `"pdf"`, `"text"`. See [Input Formats](input-formats.md). |
| `ignore_parse` | `bool` | `False` | If `True`, returns the raw MRZ text instead of the parsed dictionary. |
| `include_checkdigit` | `bool` | `True` | If `True`, includes the `*_checkdigit` fields in the output dictionary. |

**Returns:**

- If `ignore_parse=False`: a dictionary of strings (see [Output Format](#output-format)). When no MRZ is found: `{"status": "FAILURE", "status_message": "No MRZ detected"}`.
- If `ignore_parse=True`: the MRZ lines joined by `"\n"`, or `""` when no MRZ is found.

**Raises:**

- `ValueError`: the input cannot be read (missing file, undecodable image, bad base64, unsupported `input_type`, PDF input without PyMuPDF installed).

**Examples:**

```python
# From image path (str or pathlib.Path)
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

# From encoded image bytes
with open("passport.jpg", "rb") as f:
    result = fast_mrz.get_details(f.read(), input_type="bytes")

# From a PDF (needs: pip install "fastmrz[pdf]")
result = fast_mrz.get_details("scan.pdf", input_type="pdf")

# From raw MRZ text
mrz_text = "P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n7077979792GBR9505209M1704224<<<<<<<<<<<<<<00"
result = fast_mrz.get_details(mrz_text, input_type="text")

# Get raw MRZ text only
raw_mrz = fast_mrz.get_details("passport.jpg", ignore_parse=True)

# Exclude check digits from output
result = fast_mrz.get_details("passport.jpg", include_checkdigit=False)
```

---

### `get_details_batch`

```python
get_details_batch(
    inputs: Iterable[InputData],
    input_type: InputType = "imagepath",
    ignore_parse: bool = False,
    include_checkdigit: bool = True,
    workers: Optional[int] = None,
) -> List[Union[MRZDetails, str]]
```

Read many documents in parallel on a thread pool.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `inputs` | `Iterable[InputData]` | Required | The documents, all of the same `input_type`. |
| `input_type`, `ignore_parse`, `include_checkdigit` | | | As for `get_details`. |
| `workers` | `int \| None` | `None` | Number of threads. Defaults to the number of CPUs, at most 8. `1` reads sequentially. |

**Returns:**

One result per input, **in input order**, as `get_details` would return it. An input that cannot be read does not stop the batch: its result is `{"status": "FAILURE", "status_message": <reason>}`, or `""` with `ignore_parse=True`.

**Example:**

```python
results = fast_mrz.get_details_batch(["a.jpg", "b.jpg", "missing.jpg"])
# [{... "status": "SUCCESS"}, {...}, {"status": "FAILURE", "status_message": "Input is not a valid image file."}]
```

Expect about 1.5x the throughput of a plain loop on a 4-core CPU; OpenCV already uses several cores per image.

---

### `get_mrz_image`

```python
get_mrz_image(
    input_data: InputData,
    input_type: InputType = "imagepath",
) -> Optional[numpy.ndarray]
```

Return the MRZ as the recogniser saw it.

**Parameters:**

As for `get_details`; `"text"` is not supported.

**Returns:**

A greyscale `uint8` array: the rectified MRZ lines stacked top to bottom, each 32 x 640 pixels (so 64 x 640 for two-line formats, 96 x 640 for TD1). `None` when no MRZ is found.

**Raises:**

- `ValueError`: the input cannot be read.

**Example:**

```python
import cv2

strip = fast_mrz.get_mrz_image("passport.jpg")
if strip is not None:
    cv2.imwrite("mrz.png", strip)   # 64 x 640 for a passport
```

---

### `validate_mrz`

```python
validate_mrz(mrz_text: str) -> Dict[str, Union[bool, str]]
```

Check the format and every check digit of an MRZ string.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mrz_text` | `str` | Required | MRZ lines separated by newlines. |

**Returns:**

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

All values are strings. Check-digit keys are left out with `include_checkdigit=False`.

### TD3 (Passport)

```python
{
    "mrz_type": "TD3",
    "document_code": "P",
    "issuer_code": "GBR",
    "document_number": "707797979",
    "surname": "PUDARSAN",
    "given_name": "HENERT",
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

### TD1 (ID Card)

```python
{
    "mrz_type": "TD1",
    "document_code": "I",
    "issuer_code": "UTO",
    "document_number": "D23145890",
    "surname": "ERIKSSON",
    "given_name": "ANNA MARIA",
    "document_number_checkdigit": "7",
    "nationality_code": "UTO",
    "birth_date": "1974-08-12",
    "birth_date_checkdigit": "2",
    "sex": "F",
    "expiry_date": "2012-04-15",
    "expiry_date_checkdigit": "9",
    "optional_data_1": "",
    "optional_data_2": "",
    "final_checkdigit": "6",
    "mrz_text": "I<UTOD231458907<<<<<<<<<<<<<<<\n7408122F1204159UTO<<<<<<<<<<<6\nERIKSSON<<ANNA<MARIA<<<<<<<<<<",
    "status": "SUCCESS"
}
```

### TD2

```python
{
    "mrz_type": "TD2",
    "document_code": "I",
    "issuer_code": "UTO",
    "document_number": "D23145890",
    "surname": "ERIKSSON",
    "given_name": "ANNA MARIA",
    "document_number_checkdigit": "7",
    "nationality_code": "UTO",
    "birth_date": "1974-08-12",
    "birth_date_checkdigit": "2",
    "sex": "F",
    "expiry_date": "2012-04-15",
    "expiry_date_checkdigit": "9",
    "optional_data": "",
    "final_checkdigit": "6",
    "mrz_text": "I<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<\nD231458907UTO7408122F1204159<<<<<<<6",
    "status": "SUCCESS"
}
```

### MRVA / MRVB (Visa)

```python
{
    "mrz_type": "MRVA",  # or "MRVB"
    "document_code": "V",
    "issuer_code": "UTO",
    "document_number": "L8988901C",
    "surname": "ERIKSSON",
    "given_name": "ANNA MARIA",
    "document_number_checkdigit": "4",
    "nationality_code": "XXX",
    "birth_date": "1940-09-07",
    "birth_date_checkdigit": "8",
    "sex": "F",
    "expiry_date": "1996-12-10",
    "expiry_date_checkdigit": "9",
    "optional_data": "6ZE184226B",
    "mrz_text": "V<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL8988901C4XXX4009078F96121096ZE184226B<<<<<<",
    "status": "SUCCESS"
}
```

Note: MRVA and MRVB do not include `final_checkdigit` or `optional_data_checkdigit` fields.

---

## Field Descriptions

| Key | Formats | Example | Meaning |
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

---

## Error Responses

When extraction or validation fails, the response includes a `status` of `"FAILURE"` and a `status_message`:

| Status Message | Cause |
|----------------|-------|
| `"No MRZ detected"` | No MRZ was found in the image (the result contains only `status` and `status_message`) |
| `"Invalid MRZ format"` | The text does not match any known MRZ format |
| `"Invalid date of birth"` | The birth date is not a calendar date |
| `"Invalid date of expiry"` | The expiry date is not a calendar date |
| `"Document number checksum is not matching"` | Document number check digit validation failed |
| `"Date of birth checksum is not matching"` | Birth date check digit validation failed |
| `"Date of expiry checksum is not matching"` | Expiry date check digit validation failed |
| `"Optional data checksum is not matching"` | Optional data check digit validation failed (TD3) |
| `"Final checksum is not matching"` | Composite check digit validation failed |

---

## Input Validation

Inputs that cannot be read raise `ValueError` with a descriptive message:

| `input_type` | Error |
|---|---|
| `imagepath` | `Input is not a valid image file.` (missing file) / `Input is not a valid image.` (undecodable) |
| `numpy` | `Input is not a valid NumPy array.` / `Input is not a valid image.` (empty or wrong shape) |
| `base64` | `Input is not a valid base64 string.` / `Input is not a valid image.` |
| `bytes` | `Input is not a valid image.` |
| `pdf` | `Input is not a valid PDF.` / `PDF input needs PyMuPDF: pip install fastmrz[pdf]` |
| anything else | `Unsupported input_type: <value>` |

---

## Next Steps

- Learn about [supported document types](supported-documents.md)
- Understand [checksum validation](checksum-validation.md) in detail
- Review known [limitations](limitations.md)
