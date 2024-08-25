from fastmrz import FastMRZ
import json

fast_mrz = FastMRZ()
# Pass file path of installed Tesseract OCR, incase if not added to PATH variable
# fast_mrz = FastMRZ(tesseract_path=r'/path/to/tesseract/source')
passport_mrz = fast_mrz.get_mrz("data/passport_uk.jpg")
print("JSON:")
print(json.dumps(passport_mrz, indent=4))

print("\n")

passport_mrz = fast_mrz.get_mrz("data/passport_uk.jpg", raw=True)
print("TEXT:")
print(passport_mrz)
