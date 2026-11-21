"""Turn a folder of document photos into recogniser training data, without manual labelling.

usage: python import_images.py <image dir> <out prefix> [variants]

For every image the current FastMRZ reads the MRZ. A reading is used as a label only
when every check digit passes and every date is valid. Lines no check digit protects
(the name line, line 1 of TD2/TD3) are used only when every character was read with
high confidence; the others are written to a review sheet instead of being guessed.

A ``labels.json`` in the image folder (file name -> MRZ text, lines separated by
newlines) overrides the reading for those files, e.g. after reviewing the sheets.

Writes, next to ``<out prefix>``:
  <out>0_x.npy / <out>0_y.txt    training strips (``variants`` jittered copies per line)
  <out>test_x.npy / _y.txt       lines of the held-out documents (20%, by MRZ text)
  <out>holdout.json              held-out images -> MRZ text, for benchmark.py
  <out>review/*.png, review.json lines that need a human to confirm them
  <out>report.json               what happened to every image

Images and strips stay on this machine; nothing is uploaded.
"""
import glob
import json
import os
import random
import sys
import zlib

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from fastmrz import FastMRZ  # noqa: E402
from fastmrz.detector import warp_line  # noqa: E402

H, W = 32, 768
EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")
NAME_MIN_P = 0.98      # every character of an unprotected line must be at least this sure


def unprotected_lines(mrz_type):
    """Indexes of lines that no check digit covers.

    These lines (the name line of TD1, line 1 of the two-line formats) can be misread
    without any check digit failing, so they are only trusted as labels when the
    recogniser was confident about every character.

    Args:
        mrz_type: ``"TD1"``, ``"TD2"``, ``"TD3"``, ``"MRVA"`` or ``"MRVB"``.

    Returns:
        List of 0-based line indexes.
    """
    return [2] if mrz_type == "TD1" else [0]


def jitter(quad, rnd, scale):
    """Randomly move the four corners of a line quadrilateral.

    Simulates small detection errors (slightly too tight, loose, shifted or tilted
    crops) so the recogniser learns to tolerate them.

    Args:
        quad: 4 x 2 ``float32`` array of corner points in image coordinates.
        rnd: ``random.Random`` instance, so the augmentation is reproducible.
        scale: Maximum shift per coordinate, in pixels.

    Returns:
        A new 4 x 2 array; ``quad`` is not modified.
    """
    q = quad.copy()
    q += np.array([[rnd.uniform(-1, 1), rnd.uniform(-1, 1)] for _ in range(4)], np.float32) * scale
    return q


def photometric(strip, rnd):
    """Apply random image-quality degradations to a grey line strip.

    Each call applies, at random: Gaussian blur (50% of the time), a brightness and
    contrast change, Gaussian noise, and JPEG re-compression at quality 30-90 (30% of
    the time).

    Args:
        strip: Grey ``uint8`` strip of shape ``(H, W)``.
        rnd: ``random.Random`` instance, so the augmentation is reproducible.

    Returns:
        The degraded strip as ``uint8``, same shape as ``strip``.
    """
    img = strip.astype(np.float32)
    if rnd.random() < 0.5:
        img = cv2.GaussianBlur(img, (0, 0), rnd.uniform(0.3, 1.1))
    img = img * rnd.uniform(0.7, 1.2) + rnd.uniform(-25, 25)
    img += np.random.RandomState(rnd.randint(0, 1 << 30)).randn(*img.shape).astype(np.float32) * rnd.uniform(0, 8)
    img = np.clip(img, 0, 255).astype(np.uint8)
    if rnd.random() < 0.3:
        img = cv2.imdecode(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, rnd.randint(30, 90)])[1], 0)
    return img


def main(image_dir, out, variants=8):
    """Read every image under ``image_dir`` and write training, test and review data.

    For each image the MRZ is read with FastMRZ. Lines are used as labels when the
    reading passes every check (or comes from ``labels.json``); unprotected lines read
    with low confidence go to the review sheet instead. About 20% of documents,
    chosen by a hash of the MRZ text, are held out as test data. See the module
    docstring for the files written.

    Args:
        image_dir: Folder searched recursively for images (see ``EXTS``).
        out: Output path prefix, e.g. ``"data/preal"``; file names are appended to it
            directly, so include a trailing ``/`` to write into a folder instead.
        variants: Number of jittered and degraded training copies per usable line.
    """
    fm = FastMRZ()
    overrides = {}
    if os.path.isfile(os.path.join(image_dir, "labels.json")):
        overrides = json.load(open(os.path.join(image_dir, "labels.json")))
    files = sorted(f for f in glob.glob(os.path.join(image_dir, "**", "*"), recursive=True)
                   if f.lower().endswith(EXTS))
    os.makedirs(out + "review", exist_ok=True)
    rnd = random.Random(11)
    train_x, train_y, test_x, test_y = [], [], [], []
    holdout, review, report = {}, [], {}
    for path in files:
        name = os.path.relpath(path, image_dir).replace(os.sep, "/")
        try:
            image = fm._load(path, "imagepath")
            gray = fm._to_gray(image)
            reading = fm._read(image)
        except ValueError as exc:
            report[name] = "unreadable: %s" % exc
            continue
        if reading is None:
            report[name] = "no MRZ found"
            continue
        strips = [warp_line(gray, q, 640, 32, flip=reading.flip) for q in reading.quads]
        rec = fm.recognizer(strips)
        lines = list(reading.lines)
        if name in overrides:
            lines = overrides[name].strip().split("\n")
            ok = len(lines) == len(reading.quads)
            usable = list(range(len(lines))) if ok else []
            report[name] = "labelled from labels.json" if ok else "labels.json line count mismatch"
        elif not reading.valid or reading.bad_dates:
            report[name] = "skipped: check digits or dates invalid (%s)" % "|".join(lines)
            continue
        else:
            usable = []
            for i in range(len(lines)):
                sure = rec[i][1] and min(max(p) for p in rec[i][1]) >= NAME_MIN_P and rec[i][0] == lines[i]
                if i not in unprotected_lines(reading.mrz_type) or sure:
                    usable.append(i)
                else:
                    sheet = "review/%04d.png" % len(review)
                    cv2.imwrite(out + sheet, cv2.resize(strips[i], (1280, 64), interpolation=cv2.INTER_CUBIC))
                    review.append({"file": name, "line": i, "read": lines[i], "sheet": sheet})
            report[name] = "used lines %s" % usable
        # split by document (MRZ text), so photos of the same document never end up on both sides
        held_out = zlib.crc32("\n".join(lines).encode()) % 100 < 20
        if held_out and len(usable) == len(lines):
            holdout[name] = "\n".join(lines)
        for i in usable:
            quad = reading.quads[i]
            height = float(np.linalg.norm(quad[3] - quad[0]))
            if held_out:
                test_x.append(cv2.resize(warp_line(gray, quad, W, H, flip=reading.flip), (W, H)))
                test_y.append(lines[i])
                continue
            for _ in range(variants):
                q = jitter(quad, rnd, 0.12 * height)
                train_x.append(photometric(warp_line(gray, q, W, H, flip=reading.flip), rnd))
                train_y.append(lines[i])
    if train_x:
        np.save(out + "0_x.npy", np.stack(train_x))
        open(out + "0_y.txt", "w").write("\n".join(train_y))
    if test_x:
        np.save(out + "test_x.npy", np.stack(test_x))
        open(out + "test_y.txt", "w").write("\n".join(test_y))
    json.dump(holdout, open(out + "holdout.json", "w"), indent=1)
    json.dump(review, open(out + "review.json", "w"), indent=1)
    json.dump(report, open(out + "report.json", "w"), indent=1)
    print("images %d | training strips %d | held-out lines %d (%d images) | lines to review %d"
          % (len(files), len(train_x), len(test_x), len(holdout), len(review)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 8)
