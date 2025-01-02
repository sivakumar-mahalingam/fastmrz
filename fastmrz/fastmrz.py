import numpy as np
import cv2
import pytesseract
from datetime import datetime
import os


class FastMRZ:

    def __init__(self, tesseract_path=""):
        self.tesseract_path = tesseract_path
        self.net = cv2.dnn.readNetFromONNX(
            os.path.join(os.path.dirname(__file__), "model/mrz_seg.onnx")
        )

    def _process_image(self, image_path):
        image = (
            cv2.imread(image_path, cv2.IMREAD_COLOR)
            if isinstance(image_path, str)
            else image_path
        )

        image = cv2.resize(image, (256, 256), interpolation=cv2.INTER_NEAREST)
        image = np.asarray(np.float32(image / 255))

        if len(image.shape) > 3:
            image = image[:, :, :3]
        image = np.reshape(image, (1, 256, 256, 3))

        return image

    def _get_roi(self, output_data, image_path):
        if self.tesseract_path != "":
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        image = (
            cv2.imread(image_path, cv2.IMREAD_COLOR)
            if isinstance(image_path, str)
            else image_path
        )

        output_data = (output_data[0, :, :, 0] > 0.35) * 1
        output_data = np.uint8(output_data * 255)
        altered_image = cv2.resize(output_data, (image.shape[1], image.shape[0]))

        kernel = np.ones((5, 5), dtype=np.float32)
        altered_image = cv2.erode(altered_image, kernel, iterations=3)
        contours, hierarchy = cv2.findContours(
            altered_image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )
        if len(contours) == 0:
            return ""

        c_area = np.zeros([len(contours)])
        for j in range(len(contours)):
            c_area[j] = cv2.contourArea(contours[j])

        x, y, w, h = cv2.boundingRect(contours[np.argmax(c_area)])
        roi_arr = image[y : y + h, x : x + w].copy()
        return pytesseract.image_to_string(roi_arr, lang="mrz")

    def _cleanse_roi(self, mrz_text):
        input_list = mrz_text.replace(" ", "").split("\n")

        selection_length = next(
            (
                len(item)
                for item in input_list
                if "<" in item and len(item) in {30, 36, 44}
            ),
            None,
        )
        if selection_length is None:
            return ""
        new_list = [item for item in input_list if len(item) >= selection_length]
        return "\n".join(new_list)

    def _get_final_check_digit(self, input_string, input_type):
        if input_type == "TD3":
            return self._get_check_digit(
                input_string[:10] + input_string[13:20] + input_string[21:43]
            )
        elif input_type == "TD2":
            return self._get_check_digit(
                input_string[:10] + input_string[13:20] + input_string[21:35]
            )
        else:
            return self._get_check_digit(
                input_string[0][5:]
                + input_string[1][:7]
                + input_string[1][8:15]
                + input_string[1][18:29]
            )

    def _get_check_digit(self, input_string):
        weights_pattern = [7, 3, 1]

        total = 0
        for i, char in enumerate(input_string):
            if char.isdigit():
                value = int(char)
            elif char.isalpha():
                value = ord(char.upper()) - ord("A") + 10
            else:
                value = 0
            total += value * weights_pattern[i % len(weights_pattern)]

        check_digit = total % 10

        return str(check_digit)

    def _format_date(self, input_date):
        formatted_date = str(datetime.strptime(input_date, "%y%m%d").date())
        return formatted_date

    def _is_valid(self, image):
        if isinstance(image, str):
            return bool(os.path.isfile(image))
        elif isinstance(image, np.ndarray):
            return image.shape[-1] == 3

    def _get_mrz(self, image):
        image_array = self._process_image(image)
        self.net.setInput(image_array)
        output_data = self.net.forward()
        mrz_roi = self._get_roi(output_data, image)
        return self._cleanse_roi(mrz_roi)

    def get_details(self, image, ignore_parse=False):
        if not self._is_valid(image):
            return {"status": "FAILURE", "message": "Invalid input image"}
        mrz_text = self._get_mrz(image)
        return mrz_text if ignore_parse else self._parse_mrz(mrz_text)

    def _get_birth_date(self, birth_date_str, expiry_date_str):
        birth_year = int(birth_date_str[:4])
        expiry_year = int(expiry_date_str[:4])

        if expiry_year > birth_year:
            return birth_date_str
        adjusted_year = birth_year - 100
        return f"{adjusted_year}-{birth_date_str[5:]}"

    def _parse_mrz(self, mrz_text):
        if not mrz_text:
            return {"status": "FAILURE", "message": "No MRZ detected"}
        mrz_lines = mrz_text.strip().split("\n")
        if len(mrz_lines) not in [2, 3]:
            return {"status": "FAILURE", "message": "Invalid MRZ format"}

        mrz_code_dict = {}
        if len(mrz_lines) == 2:
            if mrz_lines[1][-1] == '<':
                mrz_code_dict["mrz_type"] = "MRVB" if len(mrz_lines[0]) == 36 else "MRVA"
            else:
                mrz_code_dict["mrz_type"] = "TD2" if len(mrz_lines[0]) == 36 else "TD3"

            # Line 1
            mrz_code_dict["document_code"] = mrz_lines[0][:2].strip("<")
            mrz_code_dict["issuer_code"] = mrz_lines[0][2:5]
            if not mrz_code_dict["issuer_code"].isalpha():
                return {"status": "FAILURE", "message": "Invalid MRZ format"}
            names = mrz_lines[0][5:].split("<<")
            mrz_code_dict["surname"] = names[0].replace("<", " ")
            mrz_code_dict["given_name"] = names[1].replace("<", " ")

            # Line 2
            mrz_code_dict["document_number"] = mrz_lines[1][:9].replace("<", "")
            mrz_code_dict["document_number_checkdigit"] = self._get_check_digit(mrz_code_dict["document_number"])
            if (
                mrz_code_dict["document_number_checkdigit"]
                != mrz_lines[1][9]
            ):
                return {
                    "status": "FAILURE",
                    "message": "document number checksum is not matching",
                }
            mrz_code_dict["nationality_code"] = mrz_lines[1][10:13]
            if not mrz_code_dict["nationality_code"].isalpha():
                return {"status": "FAILURE", "message": "Invalid MRZ format"}
            mrz_code_dict["birth_date"] = mrz_lines[1][13:19]
            if (
                self._get_check_digit(mrz_code_dict["birth_date"])
                != mrz_lines[1][19]
            ):
                return {
                    "status": "FAILURE",
                    "message": "date of birth checksum is not matching",
                }
            mrz_code_dict["birth_date"] = self._format_date(
                mrz_code_dict["birth_date"]
            )
            mrz_code_dict["sex"] = mrz_lines[1][20]
            mrz_code_dict["expiry_date"] = mrz_lines[1][21:27]
            if (
                self._get_check_digit(mrz_code_dict["expiry_date"])
                != mrz_lines[1][27]
            ):
                return {
                    "status": "FAILURE",
                    "message": "date of expiry checksum is not matching",
                }
            mrz_code_dict["expiry_date"] = self._format_date(
                mrz_code_dict["expiry_date"]
            )
            mrz_code_dict["birth_date"] = self._get_birth_date(
                mrz_code_dict["birth_date"], mrz_code_dict["expiry_date"]
            )
            if mrz_code_dict["mrz_type"] == "TD2":
                mrz_code_dict["optional_data"] = mrz_lines[1][28:35].strip("<")
            elif mrz_code_dict["mrz_type"] == "TD3":
                mrz_code_dict["optional_data"] = mrz_lines[1][28:42].strip("<")
            elif mrz_code_dict["mrz_type"] == "MRVA":
                mrz_code_dict["optional_data"] = mrz_lines[1][28:44].strip("<")
            else:
                mrz_code_dict["optional_data"] = mrz_lines[1][28:36].strip("<")

            if (mrz_lines[1][-1] != self._get_final_check_digit(mrz_lines[1], mrz_code_dict["mrz_type"])
                    and mrz_code_dict["mrz_type"] not in ("MRVA", "MRVB")):
                return {
                    "status": "FAILURE",
                    "message": "final checksum is not matching",
                }

        else:
            mrz_code_dict["mrz_type"] = "TD1"

            # Line 1
            mrz_code_dict["document_code"] = mrz_lines[0][:2].strip("<")
            mrz_code_dict["issuer_code"] = mrz_lines[0][2:5]
            if not mrz_code_dict["issuer_code"].isalpha():
                return {"status": "FAILURE", "message": "Invalid MRZ format"}
            mrz_code_dict["document_number"] = mrz_lines[0][5:14]
            mrz_code_dict["document_number_checkdigit"] = self._get_check_digit(mrz_code_dict["document_number"])
            if (
                mrz_code_dict["document_number_checkdigit"]
                != mrz_lines[0][14]
            ):
                return {
                    "status": "FAILURE",
                    "message": "document number checksum is not matching",
                }
            mrz_code_dict["optional_data_1"] = mrz_lines[0][15:].strip("<")

            # Line 2
            mrz_code_dict["birth_date"] = mrz_lines[1][:6]
            if self._get_check_digit(mrz_code_dict["birth_date"]) != mrz_lines[1][6]:
                return {
                    "status": "FAILURE",
                    "message": "date of birth checksum is not matching",
                }
            mrz_code_dict["birth_date"] = self._format_date(
                mrz_code_dict["birth_date"]
            )
            mrz_code_dict["sex"] = mrz_lines[1][7]
            mrz_code_dict["expiry_date"] = mrz_lines[1][8:14]
            if (
                self._get_check_digit(mrz_code_dict["expiry_date"])
                != mrz_lines[1][14]
            ):
                return {
                    "status": "FAILURE",
                    "message": "date of expiry checksum is not matching",
                }
            mrz_code_dict["expiry_date"] = self._format_date(
                mrz_code_dict["expiry_date"]
            )
            mrz_code_dict["birth_date"] = self._get_birth_date(
                mrz_code_dict["birth_date"], mrz_code_dict["expiry_date"]
            )
            mrz_code_dict["nationality_code"] = mrz_lines[1][15:18]
            if not mrz_code_dict["nationality_code"].isalpha():
                return {"status": "FAILURE", "message": "Invalid MRZ format"}
            mrz_code_dict["optional_data_2"] = mrz_lines[0][18:29].strip("<")
            if mrz_lines[1][-1] != self._get_final_check_digit(
                mrz_lines, mrz_code_dict["mrz_type"]
            ):
                return {
                    "status": "FAILURE",
                    "message": "final checksum is not matching",
                }

            # Line 3
            names = mrz_lines[2].split("<<")
            mrz_code_dict["surname"] = names[0].replace("<", " ")
            mrz_code_dict["given_name"] = names[1].replace("<", " ")

        mrz_code_dict["mrz_text"] = mrz_text

        # Final status
        mrz_code_dict["status"] = "SUCCESS"
        return mrz_code_dict

    def get_details_mrz(self, mrz_text):
        mrz_text = self._cleanse_roi(mrz_text)
        return self._parse_mrz(mrz_text)
