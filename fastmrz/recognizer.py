"""MRZ text line recogniser: a small fully convolutional CTC network run with OpenCV DNN."""
import os
import threading

import cv2
import numpy as np

from .parser import CHARSET

__all__ = ["Recognizer", "LINE_W", "LINE_H"]

LINE_H, LINE_W = 32, 640
_BLANK = len(CHARSET)
_DEFAULT_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "mrz_rec.onnx")


def normalize(strip):
    """Contrast stretch a grey strip to float32 [0, 1]."""
    strip = strip.astype(np.float32)
    lo, hi = np.percentile(strip, (2, 98))
    if hi - lo < 1:
        hi = lo + 1
    return np.clip((strip - lo) / (hi - lo), 0, 1)


class Recognizer:
    """Thread safe: OpenCV networks keep per-call state, so each thread gets its own copy."""

    def __init__(self, model_path=None):
        with open(str(model_path or _DEFAULT_MODEL), "rb") as fh:
            self._model = np.frombuffer(fh.read(), np.uint8)
        self._local = threading.local()
        self.net    # load once now so a bad model fails early

    @property
    def net(self):
        net = getattr(self._local, "net", None)
        if net is None:
            net = self._local.net = cv2.dnn.readNetFromONNX(self._model)
        return net

    def __call__(self, strips):
        """Recognise grey strips of size LINE_H x LINE_W.

        Returns one ``(text, probs, confidence)`` per strip, where ``probs`` holds a
        probability vector over :data:`CHARSET` for every recognised character.
        """
        if not len(strips):
            return []
        blob = np.stack([normalize(s) for s in strips])[:, None, :, :]
        net = self.net
        net.setInput(np.ascontiguousarray(blob, dtype=np.float32))
        logits = net.forward()[:, :, 0, :]              # N, C, T
        logits = logits - logits.max(axis=1, keepdims=True)
        p = np.exp(logits)
        p /= p.sum(axis=1, keepdims=True)
        return [self._decode(pi) for pi in p]

    @staticmethod
    def _decode(p):
        best = p.argmax(axis=0)
        text, probs, conf = [], [], []
        t, T = 0, len(best)
        while t < T:
            c = best[t]
            e = t
            while e + 1 < T and best[e + 1] == c:
                e += 1
            if c != _BLANK:
                seg = p[:_BLANK, t:e + 1]
                peak = seg[:, seg[c].argmax()]
                v = peak / max(peak.sum(), 1e-6)
                text.append(CHARSET[c])
                probs.append(v.tolist())
                conf.append(float(p[c, t:e + 1].max()))
            t = e + 1
        return "".join(text), probs, (float(np.mean(conf)) if conf else 0.0)
