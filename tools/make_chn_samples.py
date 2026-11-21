"""Render synthetic Chinese-style passport pages for tests (issue 19 of the old repo).

Chinese passports fill the 14-character personal number field completely, so the
second MRZ line contains no ``<`` filler at all. Old fastmrz dropped such lines.

usage: python make_chn_samples.py <output dir>
Needs Pillow and the OCR-B and DejaVu fonts (see fonts.py).
"""
import os
import random
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from fastmrz.parser import check_digit  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fonts import resolve  # noqa: E402

OCRB = resolve("OCRB.otf")
SANS = resolve("DejaVuSans.ttf")

PEOPLE = [
    # surname, given names, document number, birth, sex, expiry, personal number
    ("ZHANG", "WEI", "E12345678", "900101", "M", "300101", "LCOCKMNMNEPDA9"),
    ("LI", "XIAO<MING", "EA9876543", "851231", "F", "280615", "MHLPHNPOLNNHA9"),
    ("WANG", "FANG", "E00012345", "020228", "F", "320907", "KDJNEHFMPMLAB4"),
    ("CHEN", "JIAN<GUO", "EB2468013", "770704", "M", "270311", "NBGLKHKMONPDA2"),
]


def mrz_lines(surname, given, number, birth, sex, expiry, personal):
    line1 = ("POCHN" + surname + "<<" + given).ljust(44, "<")
    number_cd = check_digit(number)
    personal_cd = check_digit(personal)
    line2 = (number + number_cd + "CHN" + birth + check_digit(birth) + sex + expiry + check_digit(expiry)
             + personal + personal_cd)
    composite = number + number_cd + birth + check_digit(birth) + expiry + check_digit(expiry) + personal + personal_cd
    line2 += check_digit(composite)
    assert len(line1) == 44 and len(line2) == 44 and "<" not in line2
    return line1, line2


def page(lines, seed):
    rnd = random.Random(seed)
    w, h = 1250, 880
    bg = np.full((h, w), 236, np.float32)
    xs = np.arange(w, dtype=np.float32)
    for _ in range(18):    # guilloche-like security print
        a, f, ph = rnd.uniform(10, 60), rnd.uniform(0.004, 0.02), rnd.uniform(0, 6.3)
        ys = rnd.uniform(0, h) + a * np.sin(xs * f + ph)
        cv2.polylines(bg, [np.stack([xs, ys], 1).astype(np.int32)], False, rnd.uniform(205, 225), 2, cv2.LINE_AA)
    img = Image.fromarray(bg.astype(np.uint8))
    d = ImageDraw.Draw(img)
    sans, small = ImageFont.truetype(SANS, 30), ImageFont.truetype(SANS, 22)
    d.text((60, 40), "PEOPLE'S REPUBLIC OF CHINA   PASSPORT", font=sans, fill=60)
    d.rectangle((70, 120, 360, 500), fill=150)                       # photo
    d.ellipse((140, 170, 290, 340), fill=110)
    for i, (k, v) in enumerate([("Type", "P"), ("Country code", "CHN"), ("Passport No.", lines[1][:9]),
                                ("Surname", lines[0][5:].split("<<")[0]), ("Date of birth", lines[1][13:19]),
                                ("Date of expiry", lines[1][21:27])]):
        d.text((420, 130 + 60 * i), k, font=small, fill=110)
        d.text((420, 155 + 60 * i), v, font=small, fill=30)
    ocrb = ImageFont.truetype(OCRB, 34)
    pitch = ocrb.getlength("0") * 1.02
    for row, text in enumerate(lines):
        for i, ch in enumerate(text):
            d.text((60 + i * pitch, 715 + 58 * row), ch, font=ocrb, fill=25)
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_GRAY2BGR)


def photo(im, angle, seed):
    """Place the page on a table, rotated and in perspective, with uneven light and blur."""
    rnd = np.random.RandomState(seed)
    h, w = im.shape[:2]
    canvas_w, canvas_h = int(w * 1.5), int(h * 1.6)
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    c = np.float32([canvas_w / 2, canvas_h / 2])
    rot = cv2.getRotationMatrix2D((0, 0), angle, 1.0)[:, :2]
    dst = (src - [w / 2, h / 2]) @ rot.T + c + rnd.uniform(-35, 35, (4, 2))
    M = cv2.getPerspectiveTransform(src, dst.astype(np.float32))
    out = cv2.warpPerspective(im, M, (canvas_w, canvas_h), flags=cv2.INTER_CUBIC, borderValue=(95, 80, 70))
    shade = np.linspace(0.75, 1.1, canvas_w, dtype=np.float32)[None, :, None]
    out = np.clip(cv2.GaussianBlur(out.astype(np.float32) * shade, (0, 0), 1.2) + rnd.randn(*out.shape) * 5, 0, 255)
    return out.astype(np.uint8)


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    truth = {}
    variants = [("scan", None), ("photo", 8), ("rotated", -97), ("lowres", None)]
    for k, (person, (kind, angle)) in enumerate(zip(PEOPLE, variants)):
        lines = mrz_lines(*person)
        im = page(lines, k)
        if angle is not None:
            im = photo(im, angle, k)
        if kind == "lowres":
            im = cv2.resize(im, None, fx=0.55, fy=0.55, interpolation=cv2.INTER_AREA)
        name = "chn_passport_%s.jpg" % kind
        cv2.imwrite(os.path.join(out_dir, name), im, [cv2.IMWRITE_JPEG_QUALITY, 80])
        truth[name] = "\n".join(lines)
    for name, text in truth.items():
        print(name)
        print(text)


if __name__ == "__main__":
    main(sys.argv[1])
