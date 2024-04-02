import numpy as np
import cv2
import tensorflow
import pytesseract
import os
import re


# Set the Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/Cellar/tesseract/5.3.4_1/bin/tesseract'


class Laghima:
    def __init__(self, model_path):
        self.interpreter = tensorflow.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def _process_image(self, image_path):
        image = cv2.imread(image_path, cv2.IMREAD_COLOR) if isinstance(image_path, str) else image_path

        image = cv2.resize(image, (256, 256), interpolation=cv2.INTER_NEAREST)
        image = np.asarray(np.float32(image / 255))

        if len(image.shape) > 3:
            image = image[:, :, :3]
        image = np.reshape(image, (1, 256, 256, 3))

        return image

    def _get_roi(self, output_data, image_path):
        image = cv2.imread(image_path, cv2.IMREAD_COLOR) if isinstance(image_path, str) else image_path

        output_data = (output_data[0, :, :, 0] > 0.35) * 1
        output_data = np.uint8(output_data * 255)
        altered_image = cv2.resize(output_data, (image.shape[1], image.shape[0]))

        kernel = np.ones((5, 5), dtype=np.float32)
        altered_image = cv2.erode(altered_image, kernel, iterations=3)
        contours, hierarchy = cv2.findContours(altered_image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if len(contours) == 0:
            return None

        c_area = np.zeros([len(contours)])
        for j in range(len(contours)):
            c_area[j] = cv2.contourArea(contours[j])

        x, y, w, h = cv2.boundingRect(contours[np.argmax(c_area)])
        roi_arr = image[y:y + h, x:x + w].copy()
        roi = pytesseract.image_to_string(roi_arr)

        return roi

    def _cleanse_roi(self, input_text):
        return re.sub(r'\s+\n*$', '', input_text)

    def _parse_mrz(self, mrz_text):
        mrz_lines = mrz_text.strip().split('\n')
        if len(mrz_lines) not in [2, 3]:
            raise ValueError("Invalid MRZ Format")

        mrz_code_dict = {}
        if len(mrz_lines) == 2:
            mrz_code_dict['type'] = 'TD2' if len(mrz_lines[0]) == 36 else 'TD3'

            mrz_code_dict['document_type'] = mrz_lines[0][:1]
            mrz_code_dict['country_code'] = mrz_lines[0][2:5]
            names = (mrz_lines[0][5:]).split('<<')
            mrz_code_dict['surname'] = names[0].replace('<', ' ')
            mrz_code_dict['given_name'] = names[1].replace('<', ' ')
            mrz_code_dict['passport_number'] = mrz_lines[1][0:9].replace('<', '')
            mrz_code_dict['nationality'] = mrz_lines[1][10:13]
            mrz_code_dict['date_of_birth'] = mrz_lines[1][13:19]
            mrz_code_dict['sex'] = mrz_lines[1][20]
            mrz_code_dict['date_of_expiry'] = mrz_lines[1][21:27]
        else:
            # need to update
            mrz_code_dict['type'] = 'TD1'

            mrz_code_dict['document_type'] = mrz_lines[0][:2]
            mrz_code_dict['country_code'] = mrz_lines[0][2:5]
            names = (mrz_lines[0][5:]).split('<<')
            mrz_code_dict['surname'] = names[0].replace('<', ' ')
            mrz_code_dict['given_name'] = names[1].replace('<', ' ')
            mrz_code_dict['passport_number'] = mrz_lines[1][0:9].replace('<', '')
            mrz_code_dict['nationality'] = mrz_lines[1][10:13]
            mrz_code_dict['date_of_birth'] = mrz_lines[1][13:19]
            mrz_code_dict['sex'] = mrz_lines[1][20]
            mrz_code_dict['date_of_expiry'] = mrz_lines[1][21:27]

        return mrz_code_dict

    def _get_check_digit(self, input_string):
        weights_pattern = [7, 3, 1]

        total = 0
        for i, char in enumerate(input_string):
            if char.isdigit():
                value = int(char)
            elif char.isalpha():
                value = ord(char.upper()) - ord('A') + 10
            else:
                value = 0
            total += value * weights_pattern[i % len(weights_pattern)]

        check_digit = total % 10

        return check_digit

    def read_raw_mrz(self, image_path):
        image_array = self._process_image(image_path)
        self.interpreter.set_tensor(self.input_details[0]['index'], image_array)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        raw_roi = self._get_roi(output_data, image_path)
        cleansed_roi = self._cleanse_roi(raw_roi)

        return cleansed_roi

    def read_mrz(self, image_path):
        mrz_text = self.read_raw_mrz(image_path)
        return self._parse_mrz(mrz_text)


laghima = Laghima(os.path.abspath('../models/mrz_seg.tflite'))

passport_mrz = laghima.read_mrz(os.path.abspath('../data/passport_uk.jpg')

print(passport_mrz)
