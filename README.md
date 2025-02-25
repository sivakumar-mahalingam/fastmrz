# Fast MRZ

<div align="center">

[![License](https://img.shields.io/badge/license-AGPL%203.0-34D058?color=blue)](https://github.com/sivakumar-mahalingam/fastmrz/blob/main/LICENSE)
[![Downloads](https://static.pepy.tech/badge/fastmrz)](https://pypistats.org/packages/fastmrz)
![Python](https://img.shields.io/badge/python-3.8+-blue?logo=python&logoColor=959DA5)
[![CodeQL](https://github.com/sivakumar-mahalingam/fastmrz/actions/workflows/codeql.yml/badge.svg)](https://github.com/sivakumar-mahalingam/fastmrz/actions/workflows/codeql.yml)
[![PyPI](https://img.shields.io/pypi/v/fastmrz.svg?logo=pypi&logoColor=959DA5&color=blue)](https://pypi.org/project/fastmrz/)

<a href="https://github.com/sivakumar-mahalingam/fastmrz/" target="_blank">
    <img src="https://raw.githubusercontent.com/sivakumar-mahalingam/fastmrz/main/docs/FastMRZ.png" target="_blank" />
</a>

FastMRZ is an open-source Python package that extracts the Machine Readable Zone (MRZ) from passports and other documents. FastMRZ accepts various input formats such as Image, Base64 string, MRZ string, or NumPy array. 

[Features](#features) •
[Built With](#built-with) •
[Prerequisites](#prerequisites) •
[Installation](#installation) •
[Example](#example) •
[Wiki](#wiki) •
[ToDo](#todo) •
[Contributing](#contributing)

</div>

## ️✨Features

- 👁️Detects and extracts the MRZ region from document images
- ️🔍Contour detection to accurately identify the MRZ area
- 🎨Custom trained models using ONNX 
- 🆗Contains checksum logics for data validation
- 📤Outputs the extracted MRZ region as text/json


## 🛠️Built With

![OpenCV](https://img.shields.io/badge/OpenCV-27338e?style=for-the-badge&logo=OpenCV&logoColor=white)
![Tesseract OCR](https://img.shields.io/badge/Tesseract%20OCR-0F9D58?style=for-the-badge&logo=google&logoColor=white)
![NumPy](https://img.shields.io/badge/numpy-316192?style=for-the-badge&logo=numpy&logoColor=white)
![ONNX](https://img.shields.io/badge/ONNX-7B7B7B?style=for-the-badge&logo=onnx&logoColor=white)

## 🚨Prerequisites
- Install [Tesseract OCR](https://tesseract-ocr.github.io/tessdoc/Installation.html) engine. And set `PATH` variable with the executable and ensure that tesseract can be reached from the command line. 

## ⚙️Installation

1. Install `fastmrz`
    ```bash
    pip install fastmrz
    ```
   This can be done through conda too if you prefer.

     ```bash
     conda create -n fastmrz tesseract -c conda-forge
     conda activate fastmrz
     ```

2. Copy  the `mrz.traineddata` file from the `tessdata` folder of the [repository](https://github.com/sivakumar-mahalingam/fastmrz/raw/main/tessdata/mrz.traineddata) into the `tessdata` folder of the Tesseract installation on **YOUR MACHINE**

## 💡Example

```Python
from fastmrz import FastMRZ
import json

fast_mrz = FastMRZ()
# Pass file path of installed Tesseract OCR, incase if not added to PATH variable
# fast_mrz = FastMRZ(tesseract_path=r'/opt/homebrew/Cellar/tesseract/5.3.4_1/bin/tesseract') # Default path in Mac
# fast_mrz = FastMRZ(tesseract_path=r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe') # Default path in Windows
passport_mrz = fast_mrz.get_details("../data/passport_uk.jpg", include_checkdigit=False)
print("JSON:")
print(json.dumps(passport_mrz, indent=4))

print("\n")

passport_mrz = fast_mrz.get_details("../data/passport_uk.jpg", ignore_parse=True)
print("TEXT:")
print(passport_mrz)
```

**OUTPUT:**
```Console
JSON:
{
    "mrz_type": "TD3",
    "document_code": "P",
    "issuer_code": "GBR",
    "surname": "PUDARSAN",
    "given_name": "HENERT",
    "document_number": "707797979",
    "document_number_checkdigit": "2",
    "nationality_code": "GBR",
    "birth_date": "1995-05-20",
    "sex": "M",
    "expiry_date": "2017-04-22",
    "optional_data": "",
    "mrz_text": "P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n7077979792GBR9505209M1704224<<<<<<<<<<<<<<00",
    "status": "SUCCESS"
}


TEXT:
P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<
7077979792GBR9505209M1704224<<<<<<<<<<<<<<00
```

## 📃Wiki

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

## ✅ToDo

- [x] Include mrva and mrvb documents
- [x] Add wiki page
- [x] Support numpy array as input
- [x] Support mrz text as input
- [x] Support base64 as input
- [ ] Support pdf as input
- [x] Function to return mrz text as output
- [ ] Bulk process
- [ ] Add function parameter - Image Enhancement Model
- [ ] Add function parameter - Text Image Enhancement Model
- [ ] Train Tesseract model with additional data
- [x] Add function parameter - include_checkdigit
- [ ] Add function - get_mrz_image
- [x] Add function - validate_mrz
- [ ] Add function - generate_mrz
- [ ] Extract face image
- [ ] Add documentation page
- [ ] Add all checkdigit status

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'feat: add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## ⚖️License

Distributed under the AGPL-3.0 License. See `LICENSE` for more information.

## 🙏Show your support

Give a ⭐️ if <a href="https://github.com/sivakumar-mahalingam/fastmrz/">this</a> project helped you!

## 🚀Who's Using It?

We’d love to know who’s using **fastmrz**! If your company or project uses this package, feel free to share your story. You can:

- Open an issue with the title "We are using fastmrz!" and include your project or company name.

Thank you for supporting **fastmrz**! 🤟


