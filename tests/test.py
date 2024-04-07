import numpy as np
import os
from fastmrz import FastMRZ

fast_mrz = FastMRZ()


# Test cases for _process_image function
def test_process_image():
    image_path = os.path.abspath('../data/td3.jpg')
    processed_image = fast_mrz._process_image(image_path)
    assert isinstance(processed_image, np.ndarray)
    assert processed_image.shape == (1, 256, 256, 3)


# Test cases for _get_roi function
def test_get_roi():
    output_data = np.random.rand(1, 256, 256, 1)
    image_path = os.path.abspath('../data/td3.jpg')
    roi = fast_mrz._get_roi(output_data, image_path)
    assert isinstance(roi, str)


# Test cases for _cleanse_roi function
def test_cleanse_roi():
    raw_text = "P<UTOERIKSSON<<ANNA<MARIA<<< <<<<<<<<<  <<<<<<<\n\nL898902C36UTO7408122F1204159ZE184226B<<<<<10\n"
    cleansed_text = fast_mrz._cleanse_roi(raw_text)
    assert isinstance(cleansed_text, str)


# Test cases for _get_final_check_digit function
def test_get_final_check_digit():
    input_string = "'I<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<\nD231458907UTO7408122F1204159<<<<<<<6"
    input_type = "TD2"
    final_check_digit = fast_mrz._get_final_check_digit(input_string, input_type)
    assert isinstance(final_check_digit, str)


# Test cases for _get_check_digit function
def test_get_check_digit():
    input_string = "'I<UTOERIKSSON<<ANNA< MARIA<<<<< <<<<<<\nD231458907UTO7408122F1204159<<<<<<<6\n\n"
    check_digit = fast_mrz._get_check_digit(input_string)
    assert isinstance(check_digit, str)


# Test cases for _format_date function
def test_format_date():
    input_date = "220101"
    formatted_date = fast_mrz._format_date(input_date)
    assert isinstance(formatted_date, str)


# Test cases for read_raw_mrz function
def test_read_raw_mrz():
    image_path = os.path.abspath('../data/td2.jpg')
    raw_mrz = fast_mrz.read_raw_mrz(image_path)
    assert isinstance(raw_mrz, str)


# Test cases for read_mrz function
def test_read_mrz():
    image_path = os.path.abspath('../data/td3.jpg')
    mrz_data = fast_mrz.read_mrz(image_path)
    assert isinstance(mrz_data, dict)
    assert 'status' in mrz_data.keys()
