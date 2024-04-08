# Fast MRZ

![License](https://img.shields.io/badge/license-AGPL%203.0-green)
![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue?logo=python)
[![CodeQL](https://github.com/sivakumar-mahalingam/fastmrz/actions/workflows/codeql.yml/badge.svg)](https://github.com/sivakumar-mahalingam/fastmrz/actions/workflows/codeql.yml)

<a href="https://github.com/sivakumar-mahalingam/fastmrz/" target="_blank">
    <img src="https://raw.githubusercontent.com/sivakumar-mahalingam/fastmrz/main/docs/FastMRZ.png" target="_blank" />
</a>

This repository extracts the Machine Readable Zone (MRZ) from document images. The MRZ typically contains important information such as the document holder's name, nationality, document number, date of birth, etc.

**️Features:**

- Automatically detects and extracts the MRZ region from passport images.
- Utilizes contour detection to accurately identify the MRZ area.
- Outputs the extracted MRZ region as text for further processing or analysis.

**How to Use:**

- Clone the repository to your local machine.
- Install `Tesseract OCR` engine. And set `PATH` variable with the executable.
- Install required dependencies(mentioned in requirements.txt).
- Replace the default Tesseract model with 'data/mrz_v2.traineddata'


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

## License

Distributed under the AGPL-3.0 License. See `LICENSE` for more information.

## Show your support

Give a ⭐️ if <a href="https://github.com/sivakumar-mahalingam/fastmrz/">this</a> project helped you!

