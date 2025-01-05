from fastmrz import FastMRZ
import json
import base64

fast_mrz = FastMRZ()
# Pass file path of installed Tesseract OCR, incase if not added to PATH variable
# fast_mrz = FastMRZ(tesseract_path=r'/path/to/tesseract/source')
passport_mrz = fast_mrz.get_details("../data/passport_uk.jpg")
print("JSON:")
print(json.dumps(passport_mrz, indent=4))

print("\n")

passport_mrz = fast_mrz.get_details("../data/passport_uk.jpg", ignore_parse=True)
print("TEXT:")
print(passport_mrz)

print("\n")

passport_mrz = fast_mrz.get_details("P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n7077979792GBR9505209M1704224<<<<<<<<<<<<<<00", input_type="text")
print("JSON:")
print(json.dumps(passport_mrz, indent=4))

print("\n")

is_valid = fast_mrz.validate_mrz("P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n7077979792GBR1505209M1704224<<<<<<<<<<<<<<00")
print("MRZ VALIDITY CHECK:")
print(json.dumps(is_valid, indent=4))

print("\n")
image_file = open("../data/passport_uk.jpg", "rb")
image_data = image_file.read()
image_file.close()
base64_string = base64.b64encode(image_data).decode("utf-8")
passport_mrz = fast_mrz.get_details(base64_string, input_type="base64", ignore_parse=True)
print("TEXT:")
print(passport_mrz)