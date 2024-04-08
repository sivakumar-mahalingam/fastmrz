from fastmrz import FastMRZ
import os
import json

fast_mrz = FastMRZ()
# Pass file path of installed Tesseract OCR, incase if not added to PATH variable
# fast_mrz = FastMRZ(tesseract_path=r'/opt/homebrew/Cellar/tesseract/5.3.4_1/bin/tesseract') # Default path in Mac
# fast_mrz = FastMRZ(tesseract_path=r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe') # Default path in Windows
passport_mrz = fast_mrz.get_mrz(os.path.abspath('../data/passport_uk.jpg'))
print(json.dumps(passport_mrz, indent=4))
