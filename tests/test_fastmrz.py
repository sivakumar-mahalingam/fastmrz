import base64
import unittest
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np

from fastmrz import FastMRZ
from fastmrz import parser

DATA_DIR = Path(__file__).parent.parent / "data"

TD3 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10"
TD2 = "I<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<\nD231458907UTO7408122F1204159<<<<<<<6"
TD1 = "I<UTOD231458907<<<<<<<<<<<<<<<\n7408122F1204159UTO<<<<<<<<<<<6\nERIKSSON<<ANNA<MARIA<<<<<<<<<<"
MRVA = "V<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL8988901C4XXX4009078F96121096ZE184226B<<<<<<"
MRVB = "V<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<\nL8988901C4XXX4009078F9612109<<<<<<<<"
UK = "P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n7077979792GBR9505209M1704224<<<<<<<<<<<<<<00"

# synthetic Chinese passports (tools/make_chn_samples.py): line 2 has no "<" filler
CHN = {
    "chn_passport_scan.jpg": "POCHNZHANG<<WEI<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\nE123456782CHN9001011M3001019LCOCKMNMNEPDA964",
    "chn_passport_photo.jpg": "POCHNLI<<XIAO<MING<<<<<<<<<<<<<<<<<<<<<<<<<<\nEA98765430CHN8512316F2806158MHLPHNPOLNNHA978",
    "chn_passport_rotated.jpg": "POCHNWANG<<FANG<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\nE000123451CHN0202284F3209077KDJNEHFMPMLAB400",
    "chn_passport_lowres.jpg": "POCHNCHEN<<JIAN<GUO<<<<<<<<<<<<<<<<<<<<<<<<<\nEB24680133CHN7707043M2703110NBGLKHKMONPDA292",
}

fast_mrz = FastMRZ()


class TestImages(unittest.TestCase):
    def check(self, name, expected, mrz_type):
        path = DATA_DIR / name
        self.assertEqual(fast_mrz.get_details(path, ignore_parse=True), expected)
        details = fast_mrz.get_details(str(path))
        self.assertEqual(details["status"], "SUCCESS")
        self.assertEqual(details["mrz_type"], mrz_type)
        self.assertEqual(details["mrz_text"], expected)

    def test_td3(self):
        self.check("td3.jpg", TD3, "TD3")

    def test_td2(self):
        self.check("td2.jpg", TD2, "TD2")

    def test_td1(self):
        self.check("td1.jpg", TD1, "TD1")

    def test_mrva(self):
        self.check("mrva.jpg", MRVA, "MRVA")

    def test_mrvb(self):
        self.check("mrvb.jpg", MRVB, "MRVB")

    def test_passport_uk(self):
        self.check("passport_uk.jpg", UK, "TD3")

    def test_chinese_passports(self):
        # issue 19 of the old repo: a second line without "<" was discarded
        for name, expected in CHN.items():
            with self.subTest(name=name):
                self.check(name, expected, "TD3")
        details = fast_mrz.get_details(DATA_DIR / "chn_passport_scan.jpg")
        self.assertEqual(details["nationality_code"], "CHN")
        self.assertEqual(details["optional_data"], "LCOCKMNMNEPDA9")
        self.assertEqual(details["birth_date"], "1990-01-01")

    def test_thread_safety(self):
        names = ["td3.jpg", "td1.jpg", "passport_uk.jpg", "mrvb.jpg"] + list(CHN)
        expected = {n: fast_mrz.get_details(DATA_DIR / n, ignore_parse=True) for n in names}
        with ThreadPoolExecutor(8) as pool:
            results = list(pool.map(lambda n: (n, fast_mrz.get_details(DATA_DIR / n, ignore_parse=True)), names * 3))
        for name, text in results:
            self.assertEqual(text, expected[name], name)

    def test_batch(self):
        names = ["td3.jpg", "nomrz.jpg", "td1.jpg", "passport_uk.jpg"] + list(CHN)
        paths = [DATA_DIR / n for n in names] + ["does/not/exist.jpg"]
        texts = fast_mrz.get_details_batch(paths, ignore_parse=True)
        self.assertEqual(texts[:-1], [fast_mrz.get_details(p, ignore_parse=True) for p in paths[:-1]])
        self.assertEqual(texts[0], TD3)
        self.assertEqual(texts[1], "")
        self.assertEqual(texts[-1], "")
        details = fast_mrz.get_details_batch(paths, workers=2)
        self.assertEqual([d["status"] for d in details[:4]], ["SUCCESS", "FAILURE", "SUCCESS", "SUCCESS"])
        self.assertEqual(details[-1]["status"], "FAILURE")
        self.assertIn("not a valid image", details[-1]["status_message"])
        raw = [(DATA_DIR / "passport_uk.jpg").read_bytes()] * 3
        self.assertEqual(fast_mrz.get_details_batch(raw, input_type="bytes", ignore_parse=True, workers=1), [UK] * 3)
        self.assertEqual(fast_mrz.get_details_batch([]), [])

    def test_no_mrz(self):
        path = DATA_DIR / "nomrz.jpg"
        self.assertEqual(fast_mrz.get_details(path), {"status": "FAILURE", "status_message": "No MRZ detected"})
        self.assertEqual(fast_mrz.get_details(path, ignore_parse=True), "")

    def test_rotated(self):
        image = cv2.imread(str(DATA_DIR / "td3.jpg"))
        for code in (cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE):
            rotated = cv2.rotate(image, code)
            self.assertEqual(fast_mrz.get_details(rotated, input_type="numpy", ignore_parse=True), TD3)

    def test_skewed(self):
        image = cv2.imread(str(DATA_DIR / "passport_uk.jpg"))
        h, w = image.shape[:2]
        for angle in (-25, 8, 40):
            m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 0.7)
            skewed = cv2.warpAffine(image, m, (w, h), borderValue=(90, 90, 90))
            self.assertEqual(fast_mrz.get_details(skewed, input_type="numpy", ignore_parse=True), UK)

    def test_low_resolution(self):
        image = cv2.imread(str(DATA_DIR / "td3.jpg"))
        small = cv2.resize(image, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        self.assertEqual(fast_mrz.get_details(small, input_type="numpy", ignore_parse=True), TD3)

    def test_input_types(self):
        path = DATA_DIR / "passport_uk.jpg"
        raw = path.read_bytes()
        b64 = base64.b64encode(raw).decode()
        self.assertEqual(fast_mrz.get_details(b64, input_type="base64", ignore_parse=True), UK)
        self.assertEqual(fast_mrz.get_details("data:image/jpeg;base64," + b64, input_type="base64", ignore_parse=True), UK)
        self.assertEqual(fast_mrz.get_details(raw, input_type="bytes", ignore_parse=True), UK)
        gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        self.assertEqual(fast_mrz.get_details(gray, input_type="numpy", ignore_parse=True), UK)

    def test_pdf_input(self):
        try:
            import pymupdf
        except ImportError:
            try:
                import fitz as pymupdf
            except ImportError:
                self.skipTest("PyMuPDF not installed")
        path = DATA_DIR / "passport_uk.jpg"
        doc = pymupdf.open()
        blank = doc.new_page()
        blank.insert_text((72, 72), "cover page")
        page = doc.new_page(width=600, height=420)
        page.insert_image(page.rect, filename=str(path))
        pdf = doc.tobytes()
        self.assertEqual(fast_mrz.get_details(pdf, input_type="pdf", ignore_parse=True), UK)
        with self.assertRaises(ValueError):
            fast_mrz.get_details(b"not a pdf", input_type="pdf")

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            fast_mrz.get_details("does/not/exist.jpg")
        with self.assertRaises(ValueError):
            fast_mrz.get_details("not an array", input_type="numpy")
        with self.assertRaises(ValueError):
            fast_mrz.get_details(b"garbage", input_type="bytes")
        with self.assertRaises(ValueError):
            fast_mrz.get_details("x", input_type="unknown")

    def test_blank_image(self):
        blank = np.full((600, 900, 3), 255, np.uint8)
        self.assertEqual(fast_mrz.get_details(blank, input_type="numpy")["status_message"], "No MRZ detected")

    def test_get_mrz_image(self):
        strips = fast_mrz.get_mrz_image(DATA_DIR / "td1.jpg")
        self.assertEqual(strips.shape, (96, 640))
        self.assertIsNone(fast_mrz.get_mrz_image(DATA_DIR / "nomrz.jpg"))


class TestDeprecation(unittest.TestCase):
    def test_tesseract_arguments_warn(self):
        for kwargs in ({"tesseract_path": "/usr/bin/tesseract"}, {"tessdata_path": "tessdata"}):
            with self.subTest(**kwargs), warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                reader = FastMRZ(**kwargs)
                self.assertTrue(any(issubclass(w.category, FutureWarning) and "deprecated" in str(w.message)
                                    for w in caught))
                self.assertEqual(reader.get_details(UK, input_type="text")["status"], "SUCCESS")

    def test_no_warning_by_default(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            FastMRZ()
        self.assertFalse([w for w in caught if issubclass(w.category, FutureWarning)])


class TestParser(unittest.TestCase):
    def test_issuer_matches_nationality(self):
        # "USA" misread as "UGA" (also a real code) is repaired when the recogniser saw "S" as possible
        line1, line2 = "P<UGASALAZAR<<LISBETH<CECILIA<<<<<<<<<<<<<<<", "5342440374USA8405184F2509149115915648<706272"
        probs = [[[0.0] * 37 for _ in line] for line in (line1, line2)]
        for ln, text in enumerate((line1, line2)):
            for i, ch in enumerate(text):
                probs[ln][i][parser.CHARSET.index(ch)] = 0.9
        probs[0][3][parser.CHARSET.index("S")] = 0.08
        _, lines, _ = parser.repair([line1, line2], probs)
        self.assertEqual(lines[0][:5], "P<USA")
        # without any support from the recogniser the read is kept
        probs[0][3][parser.CHARSET.index("S")] = 0.0
        _, lines, _ = parser.repair([line1, line2], probs)
        self.assertEqual(lines[0][:5], "P<UGA")

    def test_chinese_text_without_filler(self):
        for text in CHN.values():
            with self.subTest(text=text):
                self.assertEqual(fast_mrz.get_details(text, input_type="text")["status"], "SUCCESS")

    def test_check_digit(self):
        self.assertEqual(parser.check_digit("L898902C3"), "6")
        self.assertEqual(parser.check_digit("740812"), "2")
        self.assertEqual(parser.check_digit("<<<<<<<<<<<<<<"), "0")

    def test_td3_fields(self):
        d = fast_mrz.get_details(TD3, input_type="text")
        self.assertEqual(d["status"], "SUCCESS")
        self.assertEqual(
            (d["mrz_type"], d["document_code"], d["issuer_code"], d["surname"], d["given_name"]),
            ("TD3", "P", "UTO", "ERIKSSON", "ANNA MARIA"))
        self.assertEqual((d["document_number"], d["nationality_code"], d["sex"]), ("L898902C3", "UTO", "F"))
        self.assertEqual((d["birth_date"], d["expiry_date"]), ("1974-08-12", "2012-04-15"))
        self.assertEqual((d["optional_data"], d["final_checkdigit"]), ("ZE184226B", "0"))

    def test_td1_fields(self):
        d = fast_mrz.get_details(TD1, input_type="text")
        self.assertEqual(d["status"], "SUCCESS")
        self.assertEqual((d["mrz_type"], d["document_number"], d["surname"], d["given_name"]),
                         ("TD1", "D23145890", "ERIKSSON", "ANNA MARIA"))
        self.assertEqual((d["birth_date"], d["expiry_date"], d["nationality_code"]),
                         ("1974-08-12", "2012-04-15", "UTO"))

    def test_other_types(self):
        for text, mrz_type in ((TD2, "TD2"), (MRVA, "MRVA"), (MRVB, "MRVB")):
            d = fast_mrz.get_details(text, input_type="text")
            self.assertEqual((d["status"], d["mrz_type"]), ("SUCCESS", mrz_type))

    def test_include_checkdigit(self):
        d = fast_mrz.get_details(TD3, input_type="text", include_checkdigit=False)
        self.assertFalse([k for k in d if k.endswith("checkdigit")])

    def test_text_is_cleaned(self):
        messy = "P<UTOERIKSSON<<ANNA<MARIA<<< <<<<<<<<<  <<<<<<<\n\nL898902C36UTO7408122F1204159ZE184226B<<<<<10\n"
        self.assertEqual(fast_mrz.get_details(messy, input_type="text", ignore_parse=True), TD3)

    def test_empty_optional_data_checkdigit(self):
        # issue 17: a filler is a valid optional data check digit when the field is empty
        line2 = "7077979792GBR9505209M1704224<<<<<<<<<<<<<<<"
        line2 += parser.check_digit(line2[0:10] + line2[13:20] + line2[21:43])
        d = fast_mrz.get_details("P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n" + line2, input_type="text")
        self.assertEqual(d["status"], "SUCCESS")

    def test_second_line_without_filler(self):
        # issue 19: e.g. Chinese passports have no '<' in the second line
        line2 = "E12345678"
        line2 += parser.check_digit(line2) + "CHN940420" + parser.check_digit("940420") + "M271101"
        line2 += parser.check_digit("271101") + "MHLPHNPOLNNHA9"
        line2 += parser.check_digit("MHLPHNPOLNNHA9")
        line2 += parser.check_digit(line2[0:10] + line2[13:20] + line2[21:43])
        d = fast_mrz.get_details("POCHNZHANG<<SAN<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n" + line2, input_type="text")
        self.assertEqual((d["status"], d["optional_data"]), ("SUCCESS", "MHLPHNPOLNNHA9"))

    def test_long_td1_document_number(self):
        number = "D2314589071234"
        line1 = "I<UTO" + number[:9] + "<" + number[9:] + parser.check_digit(number)
        line1 = line1.ljust(30, "<")
        line2 = "7408122F1204159UTO<<<<<<<<<<<"
        line2 += parser.check_digit(line1[5:30] + line2[0:7] + line2[8:15] + line2[18:29])
        d = fast_mrz.get_details("\n".join([line1, line2, "ERIKSSON<<ANNA<MARIA<<<<<<<<<<"]), input_type="text")
        self.assertEqual((d["status"], d["document_number"]), ("SUCCESS", number))

    def test_single_name(self):
        d = fast_mrz.get_details(
            "P<GBRPUDARSAN".ljust(44, "<") + "\n7077979792GBR9505209M1704224<<<<<<<<<<<<<<00",
            input_type="text")
        self.assertEqual((d["status"], d["surname"], d["given_name"]), ("SUCCESS", "PUDARSAN", ""))

    def test_invalid_date_does_not_raise(self):
        line2 = "7077979792GBR9513209M1704224<<<<<<<<<<<<<<00"
        d = fast_mrz.get_details("P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<\n" + line2, input_type="text")
        self.assertEqual(d["status"], "FAILURE")

    def test_failures(self):
        self.assertEqual(fast_mrz.get_details("", input_type="text")["status_message"], "No MRZ detected")
        self.assertEqual(fast_mrz.get_details("HELLO\nWORLD", input_type="text")["status_message"], "Invalid MRZ format")
        bad = UK[:-1] + "1"
        self.assertEqual(fast_mrz.get_details(bad, input_type="text")["status_message"], "Final checksum is not matching")

    def test_validate_mrz(self):
        self.assertEqual(fast_mrz.validate_mrz(UK), {"is_valid": True, "status_message": "The given mrz is valid"})
        self.assertFalse(fast_mrz.validate_mrz(UK[:-1] + "1")["is_valid"])
        self.assertFalse(fast_mrz.validate_mrz("INVALIDTEXT<<HENERT<<<<\n7077979792GBR9505209M1704224<<<<<<<<<<<<<<00")["is_valid"])

    def test_repair_uses_alternatives(self):
        lines = UK.split("\n")
        probs = []
        for ln in lines:
            row = []
            for ch in ln:
                p = [0.0] * len(parser.CHARSET)
                p[parser.CHARSET.index(ch)] = 1.0
                row.append(p)
            probs.append(row)
        # the recogniser hesitated between 5 and 6 and picked the wrong one
        broken = list(lines[1])
        broken[16] = "6"
        probs[1][16] = [0.0] * len(parser.CHARSET)
        probs[1][16][parser.CHARSET.index("6")] = 0.6
        probs[1][16][parser.CHARSET.index("5")] = 0.4
        mrz_type, fixed, _ = parser.repair([lines[0], "".join(broken)], probs)
        self.assertEqual((mrz_type, fixed), ("TD3", lines))
        # a filler the recogniser dropped is restored
        mrz_type, fixed, _ = parser.repair([lines[0][:-2], lines[1]], [probs[0][:-2], probs[1]])
        self.assertEqual((mrz_type, fixed), ("TD3", lines))


if __name__ == "__main__":
    unittest.main()
