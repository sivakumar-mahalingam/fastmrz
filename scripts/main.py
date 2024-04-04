import numpy as np
import cv2
import tensorflow
import pytesseract
import os

# Set the Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/Cellar/tesseract/5.3.4_1/bin/tesseract'




laghima = Laghima()

passport_mrz = laghima.read_mrz("/Users/sivakumar.mahalingam/laghima/data/passport_uk.jpg")

print(passport_mrz)
