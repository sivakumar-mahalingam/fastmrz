"""Convert the Doubango tesseractMRZ dataset into recogniser training strips.

The dataset (BSD 3-Clause, https://github.com/DoubangoTelecom/tesseractMRZ, folder
``dataset``) holds about 7,200 binarised MRZ line crops (``*.tif``) with ground truth
(``*.gt.txt``). Each crop is turned into several greyscale, blurred, noisy strips so
it looks like what the detector feeds the recogniser.

usage: python import_doubango.py <dataset dir> <out prefix> [exclude.json] [variants]

Writes ``<out prefix>0_x.npy/_y.txt`` and ``<out prefix>1_x.npy/_y.txt`` (training,
``variants`` copies per line, default 8) and ``<out prefix>test_x.npy/_y.txt`` (15% of
source images, held out, unmodified). ``exclude.json`` maps names to MRZ texts (like the
benchmark ground truth); every source image containing one of those lines is dropped so
a benchmark is not trained on.
"""
import glob
import json
import os
import random
import re
import sys
import zlib

import cv2
import numpy as np

H, W = 32, 768
CHARS = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<")


def strip(crop, padx, pady):
    h = crop.shape[0]
    py, px = int(round(h * pady)), int(round(h * padx))
    big = cv2.copyMakeBorder(crop, py, py, px, px, cv2.BORDER_REPLICATE)
    return cv2.resize(big, (W, H), interpolation=cv2.INTER_AREA)


def degrade(crop, rnd):
    """Make a binarised crop look like a grey camera or scanner line."""
    if rnd.random() < 0.25:
        return crop
    h, w = crop.shape
    m = crop.astype(np.float32) / 255.0                      # 1 = paper, 0 = ink
    if rnd.random() < 0.5:                                   # thicker or thinner strokes
        k = np.ones((2, 2), np.uint8)
        m = (cv2.erode if rnd.random() < 0.5 else cv2.dilate)((m * 255).astype(np.uint8), k).astype(np.float32) / 255
    m = cv2.GaussianBlur(m, (0, 0), rnd.uniform(0.4, 1.6) * h / 40.0)
    ink, paper = rnd.uniform(0, 100), rnd.uniform(140, 250)
    img = ink + (paper - ink) * m
    shade = np.random.RandomState(rnd.randint(0, 1 << 30)).randn(4, 16).astype(np.float32)
    img += cv2.resize(shade, (w, h), interpolation=cv2.INTER_CUBIC) * rnd.uniform(0, 18)
    img += np.random.RandomState(rnd.randint(0, 1 << 30)).randn(h, w).astype(np.float32) * rnd.uniform(0, 10)
    img = np.clip(img, 0, 255).astype(np.uint8)
    if rnd.random() < 0.4:
        img = cv2.imdecode(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, rnd.randint(25, 90)])[1], 0)
    return img


def main(dataset, out, exclude=None, variants=8):
    seen = set()
    if exclude:
        seen = {ln for v in json.load(open(exclude)).values() for ln in v.split("\n") if ln}
    items = []
    for f in sorted(glob.glob(os.path.join(dataset, "*.tif"))):
        y = open(f[:-4] + ".gt.txt").read().strip()
        items.append((re.sub(r"-\d+\.tif$", "", os.path.basename(f)), f, y))
    bad_src = {s for s, _, y in items if y in seen}
    kept = [(s, f, y) for s, f, y in items if s not in bad_src and y and set(y) <= CHARS]
    test = [it for it in kept if zlib.crc32(it[0].encode()) % 100 < 15]
    train = [it for it in kept if zlib.crc32(it[0].encode()) % 100 >= 15]
    print("lines %d, dropped %d, train %d, test %d" % (len(items), len(items) - len(kept), len(train), len(test)))
    np.save(out + "test_x.npy", np.stack([strip(cv2.imread(f, 0), 0.9, 0.0) for _, f, _ in test]))
    open(out + "test_y.txt", "w").write("\n".join(y for _, _, y in test))
    rnd = random.Random(7)
    for part in range(2):
        xs, ys = [], []
        for _ in range(variants // 2):
            for _, f, y in train:
                xs.append(strip(degrade(cv2.imread(f, 0), rnd), rnd.uniform(0.5, 1.4), rnd.uniform(0.0, 0.12)))
                ys.append(y)
        np.save(out + "%d_x.npy" % part, np.stack(xs))
        open(out + "%d_y.txt" % part, "w").write("\n".join(ys))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None,
         int(sys.argv[4]) if len(sys.argv) > 4 else 8)
