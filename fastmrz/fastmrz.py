"""FastMRZ: locate, read and validate the Machine Readable Zone of travel documents."""
from __future__ import annotations

import base64
import os
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Iterable, List, Literal, Optional, Union, overload

import cv2
import numpy as np

from . import parser
from .detector import find_candidates, refine_candidate, warp_line
from .recognizer import LINE_H, LINE_W, Recognizer

__all__ = ["FastMRZ", "InputData", "InputType", "MRZDetails"]

#: Accepted ``input_type`` values.
InputType = Literal["imagepath", "numpy", "base64", "bytes", "pdf", "text"]
#: Anything ``get_details`` can read: a path, an image array, base64 text, encoded bytes or MRZ text.
InputData = Union[str, "os.PathLike[str]", bytes, bytearray, np.ndarray]
#: Parsed result: every value is a string (dates are ``YYYY-MM-DD``).
MRZDetails = Dict[str, str]

_NO_MRZ = {"status": "FAILURE", "status_message": "No MRZ detected"}
_MAX_EDITS = 6


class _Reading:
    """One decoded MRZ candidate."""

    __slots__ = ("mrz_type", "lines", "confidence", "passed", "total", "quads", "flip", "edits", "bad_dates", "bad_codes")

    def __init__(self, mrz_type, lines, confidence, quads, flip, edits):
        self.mrz_type, self.lines, self.confidence, self.quads, self.flip = mrz_type, lines, confidence, quads, flip
        self.edits = edits
        status = parser.check_status(mrz_type, lines)
        self.passed, self.total = sum(status.values()), len(status)
        self.bad_dates = parser.bad_dates(mrz_type, lines)
        self.bad_codes = parser.bad_codes(mrz_type, lines)

    @property
    def valid(self):
        return self.passed == self.total

    @property
    def score(self):
        return 1.5 * self.passed / float(self.total) + self.confidence - 0.25 * self.edits - 1.0 * self.bad_dates - 0.5 * self.bad_codes

    @property
    def clean(self):
        """Confident read that needed (almost) no structural repair."""
        return self.confidence >= 0.9 and self.edits <= 2 and not self.bad_dates

    @property
    def plausible(self):
        """Looks like an MRZ even though not every check digit matches."""
        return self.valid or (self.confidence >= 0.8 and self.edits <= 3)


class FastMRZ:
    """Extract MRZ data from images of passports, ID cards and visas.

    Args:
        tesseract_path: Deprecated and ignored (Tesseract is no longer used);
            passing it raises a ``FutureWarning``.
        tessdata_path: Deprecated and ignored, like ``tesseract_path``.
        model_path: Optional path to a replacement recogniser ONNX model.
            Defaults to the model shipped in ``fastmrz/model``.

    One instance can be shared by several threads.
    """

    def __init__(self, tesseract_path: str = "", tessdata_path: str = "",
                 model_path: Optional[Union[str, "os.PathLike[str]"]] = None) -> None:
        for name, value in (("tesseract_path", tesseract_path), ("tessdata_path", tessdata_path)):
            if value:
                warnings.warn(
                    "FastMRZ(%s=...) is deprecated and ignored: Tesseract is no longer used. "
                    "Remove the argument; it will be dropped in a future release." % name,
                    FutureWarning, stacklevel=2)
        self.recognizer = Recognizer(model_path)

    # ------------------------------------------------------------------ input
    @staticmethod
    def _to_gray(image):
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("Input is not a valid image.")
        if image.dtype != np.uint8:
            image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        if image.ndim == 2:
            return image
        if image.ndim == 3 and image.shape[2] == 1:
            return image[:, :, 0]
        if image.ndim == 3 and image.shape[2] >= 3:
            return cv2.cvtColor(np.ascontiguousarray(image[:, :, :3]), cv2.COLOR_BGR2GRAY)
        raise ValueError("Input is not a valid image.")

    @staticmethod
    def _decode_bytes(data):
        image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Input is not a valid image.")
        return image

    def _load(self, input_data, input_type):
        if input_type == "imagepath":
            path = os.fspath(input_data)
            if not os.path.isfile(path):
                raise ValueError("Input is not a valid image file.")
            with open(path, "rb") as fh:
                return self._decode_bytes(fh.read())
        if input_type == "numpy":
            if not isinstance(input_data, np.ndarray):
                raise ValueError("Input is not a valid NumPy array.")
            return input_data
        if input_type == "base64":
            if isinstance(input_data, str) and input_data.startswith("data:") and "," in input_data:
                input_data = input_data.split(",", 1)[1]
            try:
                raw = base64.b64decode(input_data)
            except Exception:
                raise ValueError("Input is not a valid base64 string.")
            return self._decode_bytes(raw)
        if input_type == "bytes":
            return self._decode_bytes(bytes(input_data))
        raise ValueError("Unsupported input_type: %s" % input_type)

    @staticmethod
    def _pdf_pages(input_data, dpi=200, max_pages=10):
        """Render PDF pages (path or bytes) to grey images. Needs ``pip install pymupdf``."""
        try:
            import pymupdf
        except ImportError:
            try:
                import fitz as pymupdf    # PyMuPDF < 1.24 only provides the "fitz" name
            except ImportError:
                raise ValueError("PDF input needs PyMuPDF: pip install fastmrz[pdf]")
        try:
            if isinstance(input_data, (bytes, bytearray)):
                doc = pymupdf.open(stream=bytes(input_data), filetype="pdf")
            else:
                doc = pymupdf.open(os.fspath(input_data))
        except Exception:
            raise ValueError("Input is not a valid PDF.")
        with doc:
            for i, page in enumerate(doc):
                if i >= max_pages:
                    break
                pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
                yield np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, 0].copy()

    # ---------------------------------------------------------------- reading
    def _evaluate(self, gray, candidates):
        """Recognise candidate blocks (both reading directions) and return the readings."""
        candidates = [refine_candidate(gray, c) for c in candidates]
        strips, index = [], []
        for ci, cand in enumerate(candidates):
            for flip in (False, True):
                quads = cand["quads"][::-1] if flip else cand["quads"]
                for q in quads:
                    strips.append(warp_line(gray, q, LINE_W, LINE_H, flip=flip))
                index.append((ci, flip, len(quads)))
        results = self.recognizer(strips)
        readings, pos = [], 0
        for ci, flip, n in index:
            chunk = results[pos:pos + n]
            pos += n
            texts = [c[0] for c in chunk]
            mrz_type, lines, edits = parser.repair(texts, [c[1] for c in chunk])
            if mrz_type is None or edits > _MAX_EDITS:
                continue    # not MRZ shaped: a real zone never needs that much repair
            conf = float(np.mean([c[2] for c in chunk]))
            quads = candidates[ci]["quads"]
            readings.append(_Reading(mrz_type, lines, conf, quads[::-1] if flip else quads, flip, edits))
        return readings

    def _stages(self, gray):
        """Detector settings from cheap/common to exhaustive."""
        long_side = max(gray.shape[:2])
        yield dict(long_sides=(1024,), rotations=(0, 90))
        yield dict(long_sides=(1024,), iso=True, smear=9)
        yield dict(long_sides=(1024,), iso=True, smear=17)
        extra = [640]
        if long_side > 1400:
            extra.append(1600)
        if long_side > 2400:
            extra.append(2400)
        yield dict(long_sides=tuple(extra), rotations=(0, 90))
        yield dict(long_sides=tuple(extra), iso=True, smear=11)
        yield dict(long_sides=(1024,), rotations=(0, 90), smear=41)
        yield dict(long_sides=(1024,), rotations=(0, 90), smear=15)
        yield dict(long_sides=(1024,), iso=True, smear=13)
        # diagonal documents: straighten by +-45 degrees and use the directional detector
        yield dict(long_sides=(1024,), rotations=(45, -45))
        yield dict(long_sides=(1024,), rotations=(30, -30, 60, -60))

    def _read(self, image):
        gray = self._to_gray(image)
        best = None
        agree = {}    # text read without any repair -> number of detector stages that produced it
        for stage in self._stages(gray):
            candidates = find_candidates(gray, **stage)
            stage_best = None
            # the top candidate alone usually settles it; the rest are read in groups of three
            for start, stop in [(0, 1)] + [(i, i + 3) for i in range(1, len(candidates), 3)]:
                for r in self._evaluate(gray, candidates[start:stop]):
                    if stage_best is None or r.score > stage_best.score:
                        stage_best = r
                    if best is None or r.score > best.score:
                        best = r
                if best is not None and best.valid and best.edits <= 1 and not best.bad_dates:
                    return best
            if best is not None and best.clean:
                break    # readable MRZ whose check digits are simply wrong
            if stage_best is not None and stage_best.lines == best.lines and (
                    (best.valid and not best.bad_dates and not best.bad_codes)
                    or (stage_best.edits == 0 and best.edits == 0 and best.confidence >= 0.95)):
                # two independent detector settings agree on the best reading: either a valid
                # MRZ that needed repairs, or an unrepaired read of an unusual document
                # (wrong check digit, specimen date). More searching would not change it.
                key = tuple(best.lines)
                agree[key] = agree.get(key, 0) + 1
                if agree[key] >= 2:
                    break
        return best if best is not None and best.plausible else None

    # -------------------------------------------------------------------- API
    @overload
    def get_details(self, input_data: InputData, input_type: InputType = ...,
                    ignore_parse: Literal[False] = ..., include_checkdigit: bool = ...) -> MRZDetails: ...

    @overload
    def get_details(self, input_data: InputData, input_type: InputType,
                    ignore_parse: Literal[True], include_checkdigit: bool = ...) -> str: ...

    @overload
    def get_details(self, input_data: InputData, input_type: InputType = ..., *,
                    ignore_parse: Literal[True], include_checkdigit: bool = ...) -> str: ...

    @overload
    def get_details(self, input_data: InputData, input_type: InputType = ...,
                    ignore_parse: bool = ..., include_checkdigit: bool = ...) -> Union[MRZDetails, str]: ...

    def get_details(self, input_data: InputData, input_type: InputType = "imagepath",
                    ignore_parse: bool = False, include_checkdigit: bool = True) -> Union[MRZDetails, str]:
        """Read and parse the MRZ of one document.

        Args:
            input_data: The document, in the form given by ``input_type``.
            input_type: One of

                - ``"imagepath"``: path to an image file (str or ``pathlib.Path``)
                - ``"numpy"``: image array, BGR colour or greyscale
                - ``"base64"``: base64 encoded image file, ``data:`` URIs allowed
                - ``"bytes"``: encoded image file (JPEG, PNG, ...)
                - ``"pdf"``: path or bytes of a PDF; the first page (of up to 10)
                  with an MRZ is used. Needs ``pip install fastmrz[pdf]``.
                - ``"text"``: MRZ text with lines separated by newlines; only parsed,
                  never auto-corrected
            ignore_parse: Return the raw MRZ text instead of the parsed fields.
            include_checkdigit: Include the ``*_checkdigit`` keys in the result.

        Returns:
            With ``ignore_parse=True`` the MRZ lines joined by ``"\\n"``, or ``""`` when
            no MRZ is found. Otherwise a dict of strings: ``mrz_type``,
            ``document_code``, ``issuer_code``, ``document_number``, ``surname``,
            ``given_name``, ``nationality_code``, ``birth_date``, ``sex``,
            ``expiry_date``, the optional data fields, the check digits,
            ``mrz_text``, ``status`` (``"SUCCESS"`` / ``"FAILURE"``) and, on
            failure, ``status_message``. See the README for the full table.

        Raises:
            ValueError: The input cannot be read (missing file, undecodable image,
                bad base64, unsupported ``input_type``, PDF without PyMuPDF).
        """
        if input_type == "text":
            lines = parser.clean_text(input_data)
            if ignore_parse:
                return "\n".join(lines)
            return parser.parse(lines, include_checkdigit=include_checkdigit)
        if input_type == "pdf":
            reading = None
            for page in self._pdf_pages(input_data):
                reading = self._read(page)
                if reading is not None:
                    break
        else:
            reading = self._read(self._load(input_data, input_type))
        if reading is None:
            return "" if ignore_parse else dict(_NO_MRZ)
        if ignore_parse:
            return "\n".join(reading.lines)
        return parser.parse(reading.lines, include_checkdigit=include_checkdigit)

    def get_details_batch(self, inputs: Iterable[InputData], input_type: InputType = "imagepath",
                          ignore_parse: bool = False, include_checkdigit: bool = True,
                          workers: Optional[int] = None) -> List[Union[MRZDetails, str]]:
        """Read many documents in parallel.

        Args:
            inputs: The documents, all of the same ``input_type``.
            input_type, ignore_parse, include_checkdigit: As for :meth:`get_details`.
            workers: Number of threads. Defaults to the number of CPUs, at most 8;
                ``1`` reads sequentially.

        Returns:
            One result per input, in input order, as :meth:`get_details` would
            return it. An input that cannot be read does not stop the batch: its
            result is ``{"status": "FAILURE", "status_message": <reason>}``, or
            ``""`` with ``ignore_parse=True``.
        """
        inputs = list(inputs)
        if workers is None:
            workers = min(8, os.cpu_count() or 1)

        def one(item):
            try:
                return self.get_details(item, input_type=input_type, ignore_parse=ignore_parse,
                                        include_checkdigit=include_checkdigit)
            except ValueError as exc:
                return "" if ignore_parse else {"status": "FAILURE", "status_message": str(exc)}

        if workers <= 1 or len(inputs) <= 1:
            return [one(x) for x in inputs]
        with ThreadPoolExecutor(max_workers=min(workers, len(inputs))) as pool:
            return list(pool.map(one, inputs))

    def get_mrz_image(self, input_data: InputData, input_type: InputType = "imagepath") -> Optional[np.ndarray]:
        """Return the MRZ as the recogniser saw it.

        Args:
            input_data, input_type: As for :meth:`get_details` (``"text"`` is not
                supported).

        Returns:
            A greyscale ``uint8`` array: the rectified MRZ lines stacked top to
            bottom, each 32 x 640 pixels (so 64 x 640 for two lines, 96 x 640 for
            TD1). ``None`` when no MRZ is found.

        Raises:
            ValueError: The input cannot be read.
        """
        if input_type == "pdf":
            for image in self._pdf_pages(input_data):
                reading = self._read(image)
                if reading is not None:
                    break
            else:
                return None
        else:
            image = self._load(input_data, input_type)
            reading = self._read(image)
        if reading is None:
            return None
        gray = self._to_gray(image)
        return np.vstack([warp_line(gray, q, LINE_W, LINE_H, flip=reading.flip) for q in reading.quads])

    def validate_mrz(self, mrz_text: str) -> Dict[str, Union[bool, str]]:
        """Check the format and every check digit of an MRZ string.

        Args:
            mrz_text: MRZ lines separated by newlines.

        Returns:
            ``{"is_valid": True, "status_message": "The given mrz is valid"}`` or
            ``{"is_valid": False, "status_message": <first problem found>}``.
        """
        result = parser.parse(parser.clean_text(mrz_text))
        if result.get("status") == "SUCCESS":
            return {"is_valid": True, "status_message": "The given mrz is valid"}
        return {"is_valid": False, "status_message": result.get("status_message")}
