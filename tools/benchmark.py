"""Measure MRZ reading accuracy: benchmark.py <image dir> <ground truth json>."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from fastmrz import FastMRZ  # noqa: E402


def main(image_dir, gt_path):
    truth = json.load(open(gt_path))
    reader = FastMRZ()
    ok, elapsed = 0, 0.0
    for name, expected in sorted(truth.items()):
        start = time.time()
        got = reader.get_details(os.path.join(image_dir, name), ignore_parse=True)
        elapsed += time.time() - start
        if got == expected.strip():
            ok += 1
        else:
            print("FAIL %s\n  got: %s\n  exp: %s" % (name, got.replace("\n", " | "), expected.replace("\n", " | ")))
    print("exact match %d/%d, %.0f ms per image" % (ok, len(truth), 1000 * elapsed / max(1, len(truth))))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
