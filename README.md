# Fast MRZ

![License](https://img.shields.io/badge/license-AGPL%203.0-green)
![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue?logo=python)
[![CodeQL](https://github.com/sivakumar-mahalingam/fastmrz/actions/workflows/codeql.yml/badge.svg)](https://github.com/sivakumar-mahalingam/fastmrz/actions/workflows/codeql.yml)

<a href="https://github.com/sivakumar-mahalingam/fastmrz/" target="_blank">
    <img src="https://raw.githubusercontent.com/sivakumar-mahalingam/fastmrz/main/docs/FastMRZ.png" target="_blank" />
</a>

This repository extracts the Machine Readable Zone (MRZ) from document images. The MRZ typically contains important information such as the document holder's name, nationality, document number, date of birth, etc.

**️Features:**

- Detects and extracts the MRZ region from document images
- Contour detection to accurately identify the MRZ area
- Custom trained models for Tensor and Tesseract 
- Contains checksum logics for data validation
- Outputs the extracted MRZ region as text/json for further processing or analysis


## Built With

![Tensorflow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-27338e?style=for-the-badge&logo=OpenCV&logoColor=white)
![Tesseract OCR](https://img.shields.io/badge/Tesseract%20OCR-0F9D58?style=for-the-badge&logo=google&logoColor=white)
![NumPy](https://img.shields.io/badge/numpy-316192?style=for-the-badge&logo=numpy&logoColor=white)

## Installation

1. Install `fastmrz` from pip
    ```Console
    $ pip install fastmrz
    
    ---> 100%
    ```

2. You also need to install [Tesseract OCR](https://tesseract-ocr.github.io/tessdoc/Installation.html) engine. And set `PATH` variable with the executable. 

3. Replace `eng.traineddata` in `tessdata` folder with the downloaded `tessdata/mrz_v2.traineddata` file from the repo

## Example

```Python
from fastmrz import FastMRZ
import os
import json

fast_mrz = FastMRZ()
# Pass file path of installed Tesseract OCR, incase if not added to PATH variable
# fast_mrz = FastMRZ(tesseract_path=r'/opt/homebrew/Cellar/tesseract/5.3.4_1/bin/tesseract') # Default path in Mac
# fast_mrz = FastMRZ(tesseract_path=r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe') # Default path in Windows
passport_mrz = fast_mrz.get_mrz(os.path.abspath('../data/passport_uk.jpg'))
print("JSON:")
print(json.dumps(passport_mrz, indent=4))

print("\n")

passport_mrz = fast_mrz.get_raw_mrz(os.path.abspath('../data/passport_uk.jpg'))
print("TEXT:")
print(passport_mrz)
```

**OUTPUT:**
```Console
JSON:
{
    "mrz_type": "TD3",
    "document_type": "P",
    "country_code": "GBR",
    "surname": "PUDARSAN",
    "given_name": "HENERT",
    "document_number": "707797979",
    "nationality": "GBR",
    "date_of_birth": "1995-05-20",
    "sex": "M",
    "date_of_expiry": "2017-04-22",
    "status": "SUCCESS"
}


TEXT:
P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<
7077979792GBR9505209M1704224<<<<<<<<<<<<<<00
```

## MRZ Wiki

<details>
    <summary><b>MRZ Types & Format</b></summary>

The standard for MRZ code is strictly regulated and has to comply with [Doc 9303](https://www.icao.int/publications/pages/publication.aspx?docnum=9303). Machine Readable Travel Documents published by the International Civil Aviation Organization.

There are currently several types of ICAO standard machine-readable zones, which vary in the number of lines and characters in each line:

- TD-1 (e.g. citizen’s identification card, EU ID card, US Green Card): consists of 3 lines, 30 characters each.
- TD-2 (e.g. Romania ID, old type of German ID), and MRV-B (machine-readable visas type B — e.g. Schengen visa): consists of 2 lines, 36 characters each.
- TD-3 (all international passports, also known as MRP), and MRV-A (machine-readable visas type A — issued by the USA, Japan, China, and others): consist of 2 lines, 44 characters each.

Now, based on the example of a national passport, let us take a closer look at the MRZ composition.

![MRZ fields distribution](https://raw.githubusercontent.com/sivakumar-mahalingam/fastmrz/main/docs/mrz_fields_distribution.png)

</details>

![MRZ GIF](https://raw.githubusercontent.com/sivakumar-mahalingam/fastmrz/main/docs/mrz.gif)

## ToDo

- [ ] Test for **mrva** and **mrvb** documents
- [ ] Add `wiki` page

## License

Distributed under the AGPL-3.0 License. See `LICENSE` for more information.

## Show your support

Give a ⭐️ if <a href="https://github.com/sivakumar-mahalingam/fastmrz/">this</a> project helped you!

