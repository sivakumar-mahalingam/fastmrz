from fastmrz import FastMRZ
import os

# fast_mrz = FastMRZ(tesseract_path=r'/opt/homebrew/Cellar/tesseract/5.3.4_1/bin/tesseract')
# fast_mrz = FastMRZ(tesseract_path=r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe')

fast_mrz = FastMRZ()
passport_mrz = fast_mrz.get_mrz(os.path.abspath('../data/passport_uk.jpg'))
print(passport_mrz)

