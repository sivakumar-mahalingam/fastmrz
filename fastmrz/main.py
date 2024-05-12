from fastmrz import FastMRZ
import os
import json

fast_mrz = FastMRZ()
# Pass file path of installed Tesseract OCR, incase if not added to PATH variable
# fast_mrz = FastMRZ(tesseract_path=r'/path/to/tesseract/source')
passport_mrz = fast_mrz.get_mrz(os.path.abspath('../data/passport_uk.jpg'))
print("JSON:")
print(json.dumps(passport_mrz, indent=4))

print("\n")

passport_mrz = fast_mrz.get_raw_mrz(os.path.abspath('../data/passport_uk.jpg'))
print("TEXT:")
print(passport_mrz)
