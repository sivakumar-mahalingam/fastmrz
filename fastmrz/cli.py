import argparse
import json
from .fastmrz import FastMRZ

def main():
    parser = argparse.ArgumentParser(
        prog='get_mrz', description='Get mrz data on document'
    )

    parser.add_argument(
        '-f', '--file', help='MRZ Document image file path'
    )

    parser.add_argument(
        '-t', '--tesseract_path', help='Tesseract OCR path'
    )

    args = parser.parse_args()

    fast_mrz = FastMRZ(tesseract_path=args.tesseract_path) if args.tesseract_path else FastMRZ()

    result = fast_mrz.get_mrz()

    print(json.dump(result, indent=4))
