import numpy as np
import cv2
import tensorflow
import pytesseract
from datetime import datetime
import os

# Set the Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/Cellar/tesseract/5.3.4_1/bin/tesseract'


class Laghima:
    def __init__(self, model_path):
        self.interpreter = tensorflow.lite.Interpreter(model_path=os.path.abspath('./models/mrz_seg.tflite'))
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

    def _cleanse_roi(self, raw_text):
        input_list = raw_text.replace(' ', '').split('\n')

        selection_length = None
        for item in input_list:
            if '<' in item  and len(item) in (30, 36, 44):
                selection_length = len(item)
                break

        new_list = [item for item in input_list if len(item) >= selection_length]

        output_text = '\n'.join(new_list)

        return output_text

    def _get_final_check_digit(self, input_string, input_type):
        if input_type == 'TD3':
            return self._get_check_digit(input_string[0:10] + input_string[13:20] + input_string[21:43])
        elif input_type == 'TD2':
            return self._get_check_digit(input_string[0:10] + input_string[13:20] + input_string[21:35])
        else:
            return self._get_check_digit(input_string[0][5:] + input_string[1][:7] + input_string[1][8:15] + input_string[1][18:29])

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

        return str(check_digit)

    def _format_date(self, input_date):
        formatted_date = str(datetime.strptime(input_date, '%y%m%d').date())
        return formatted_date

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

    def _parse_mrz(self, mrz_text):
        mrz_lines = mrz_text.strip().split('\n')
        if len(mrz_lines) not in [2, 3]:
            return {'status': 'FAILURE', 'message': 'Invalid MRZ format'}

        mrz_code_dict = {}
        if len(mrz_lines) == 2:
            # add optional data field
            mrz_code_dict['mrz_type'] = 'TD2' if len(mrz_lines[0]) == 36 else 'TD3'

            # Line 1
            mrz_code_dict['document_type'] = mrz_lines[0][:1]
            mrz_code_dict['country_code'] = mrz_lines[0][2:5]
            names = mrz_lines[0][5:].split('<<')
            mrz_code_dict['surname'] = names[0].replace('<', ' ')
            mrz_code_dict['given_name'] = names[1].replace('<', ' ')

            # Line 2
            mrz_code_dict['document_number'] = mrz_lines[1][0:9].replace('<', '')
            if self._get_check_digit(mrz_code_dict['document_number']) != mrz_lines[1][9]:
                return {'status': 'FAILURE', 'message': 'document number checksum is not matching'}
            mrz_code_dict['nationality'] = mrz_lines[1][10:13]
            mrz_code_dict['date_of_birth'] = mrz_lines[1][13:19]
            if self._get_check_digit(mrz_code_dict['date_of_birth']) != mrz_lines[1][19]:
                return {'status': 'FAILURE', 'message': 'date of birth checksum is not matching'}
            mrz_code_dict['date_of_birth'] = self._format_date(mrz_code_dict['date_of_birth'])
            mrz_code_dict['sex'] = mrz_lines[1][20]
            mrz_code_dict['date_of_expiry'] = mrz_lines[1][21:27]
            if self._get_check_digit(mrz_code_dict['date_of_expiry']) != mrz_lines[1][27]:
                return {'status': 'FAILURE', 'message': 'date of expiry checksum is not matching'}
            mrz_code_dict['date_of_expiry'] = self._format_date(mrz_code_dict['date_of_expiry'])
            if mrz_lines[1][-1] != self._get_final_check_digit(mrz_lines[1], mrz_code_dict['type']):
                return {'status': 'FAILURE', 'message': 'final checksum is not matching'}

            # Final status
            mrz_code_dict['status'] = 'SUCCESS'
        else:
            mrz_code_dict['mrz_type'] = 'TD1'

            # Line 1
            mrz_code_dict['document_type'] = mrz_lines[0][:2].replace('<', ' ')
            mrz_code_dict['country_code'] = mrz_lines[0][2:5]
            mrz_code_dict['document_number'] = mrz_lines[0][5:14]
            if self._get_check_digit(mrz_code_dict['document_number']) != mrz_lines[0][14]:
                return {'status': 'FAILURE', 'message': 'document number checksum is not matching'}
            mrz_code_dict['optional_data_1'] = mrz_lines[0][15:].strip('<')

            # Line 2
            mrz_code_dict['date_of_birth'] = mrz_lines[1][:6]
            if self._get_check_digit(mrz_code_dict['date_of_birth']) != mrz_lines[1][6]:
                return {'status': 'FAILURE', 'message': 'date of birth checksum is not matching'}
            mrz_code_dict['date_of_birth'] = self._format_date(mrz_code_dict['date_of_birth'])
            mrz_code_dict['sex'] = mrz_lines[1][7]
            mrz_code_dict['date_of_expiry'] = mrz_lines[1][8:14]
            if self._get_check_digit(mrz_code_dict['date_of_expiry']) != mrz_lines[1][14]:
                return {'status': 'FAILURE', 'message': 'date of expiry checksum is not matching'}
            mrz_code_dict['date_of_expiry'] = self._format_date(mrz_code_dict['date_of_expiry'])
            mrz_code_dict['nationality'] = mrz_lines[1][15:18]
            mrz_code_dict['optional_data_2'] = mrz_lines[0][18:29].strip('<')
            if mrz_lines[1][-1] != self._get_final_check_digit(mrz_lines, mrz_code_dict['type']):
                return {'status': 'FAILURE', 'message': 'final checksum is not matching'}

            # Line 3
            names = mrz_lines[2].split('<<')
            mrz_code_dict['surname'] = names[0].replace('<', ' ')
            mrz_code_dict['given_name'] = names[1].replace('<', ' ')

            # Final status
            mrz_code_dict['status'] = 'SUCCESS'

        return mrz_code_dict





