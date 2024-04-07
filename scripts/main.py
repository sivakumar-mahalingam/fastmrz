from fastmrz import FastMRZ
import os

fast_mrz = FastMRZ(tesseract_path=r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe')
passport_mrz = fast_mrz.read_mrz(os.path.abspath('../data/passport_uk.jpg'))
print(passport_mrz)
