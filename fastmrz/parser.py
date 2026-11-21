"""MRZ parsing, validation and check-digit driven OCR repair (ICAO Doc 9303)."""
from datetime import date
from itertools import combinations

__all__ = ["CHARSET", "check_digit", "clean_text", "parse", "repair", "FORMATS"]

CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<"
_IDX = {c: i for i, c in enumerate(CHARSET)}
_DIGITS = set("0123456789")
_ALPHA = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# character classes used for the positional constraints
_CLASSES = {
    "A": _ALPHA,                     # letter
    "a": _ALPHA | {"<"},             # letter or filler
    "N": _DIGITS,                    # digit
    "n": _DIGITS | {"<"},            # digit or filler
    "X": _ALPHA | _DIGITS | {"<"},   # anything
    "S": set("MFX<"),                # sex
}

# line length -> (number of lines)
FORMATS = {"TD1": (3, 30), "TD2": (2, 36), "TD3": (2, 44), "MRVA": (2, 44), "MRVB": (2, 36)}


def _mask(spec):
    return "".join(cls * n for cls, n in spec)


_MASKS = {
    "TD3": [_mask([("A", 1), ("a", 4), ("a", 39)]),
            _mask([("X", 9), ("n", 1), ("a", 3), ("n", 6), ("n", 1), ("S", 1), ("n", 6), ("n", 1), ("X", 14), ("n", 1), ("N", 1)])],
    "MRVA": [_mask([("A", 1), ("a", 4), ("a", 39)]),
             _mask([("X", 9), ("n", 1), ("a", 3), ("n", 6), ("n", 1), ("S", 1), ("n", 6), ("n", 1), ("X", 16)])],
    "TD2": [_mask([("A", 1), ("a", 4), ("a", 31)]),
            _mask([("X", 9), ("n", 1), ("a", 3), ("n", 6), ("n", 1), ("S", 1), ("n", 6), ("n", 1), ("X", 7), ("N", 1)])],
    "MRVB": [_mask([("A", 1), ("a", 4), ("a", 31)]),
             _mask([("X", 9), ("n", 1), ("a", 3), ("n", 6), ("n", 1), ("S", 1), ("n", 6), ("n", 1), ("X", 8)])],
    "TD1": [_mask([("A", 1), ("a", 4), ("X", 9), ("n", 1), ("X", 15)]),
            _mask([("n", 6), ("n", 1), ("S", 1), ("n", 6), ("n", 1), ("a", 3), ("X", 11), ("N", 1)]),
            _mask([("a", 30)])],
}

# (name, line, start, end, check line, check pos)
_CHECKS = {
    "TD3": [("document_number", 1, 0, 9, 1, 9), ("birth_date", 1, 13, 19, 1, 19),
            ("expiry_date", 1, 21, 27, 1, 27), ("optional_data", 1, 28, 42, 1, 42)],
    "MRVA": [("document_number", 1, 0, 9, 1, 9), ("birth_date", 1, 13, 19, 1, 19), ("expiry_date", 1, 21, 27, 1, 27)],
    "TD2": [("document_number", 1, 0, 9, 1, 9), ("birth_date", 1, 13, 19, 1, 19), ("expiry_date", 1, 21, 27, 1, 27)],
    "MRVB": [("document_number", 1, 0, 9, 1, 9), ("birth_date", 1, 13, 19, 1, 19), ("expiry_date", 1, 21, 27, 1, 27)],
    "TD1": [("document_number", 0, 5, 14, 0, 14), ("birth_date", 1, 0, 6, 1, 6), ("expiry_date", 1, 8, 14, 1, 14)],
}

# composite check digit: list of (line, start, end) and the (line, pos) of the digit
_COMPOSITE = {
    "TD3": ([(1, 0, 10), (1, 13, 20), (1, 21, 43)], (1, 43)),
    "TD2": ([(1, 0, 10), (1, 13, 20), (1, 21, 35)], (1, 35)),
    "TD1": ([(0, 5, 30), (1, 0, 7), (1, 8, 15), (1, 18, 29)], (1, 29)),
}

_MESSAGES = {
    "document_number": "Document number checksum is not matching",
    "birth_date": "Date of birth checksum is not matching",
    "expiry_date": "Date of expiry checksum is not matching",
    "optional_data": "Optional data checksum is not matching",
    "final": "Final checksum is not matching",
}


def check_digit(text):
    """ICAO 9303 check digit (weights 7, 3, 1) of ``text`` as a one character string."""
    total = 0
    for i, ch in enumerate(text):
        if ch.isdigit():
            v = ord(ch) - 48
        elif "A" <= ch <= "Z":
            v = ord(ch) - 55
        else:
            v = 0
        total += v * (7, 3, 1)[i % 3]
    return str(total % 10)


def clean_text(text):
    """Normalise raw MRZ text: upper case, no blanks, only non-empty lines."""
    lines = []
    for raw in str(text).upper().replace("\r", "\n").split("\n"):
        ln = "".join(ch for ch in raw if not ch.isspace())
        ln = ln.replace("«", "<<").replace("‹", "<")
        if ln:
            lines.append(ln)
    return lines


def detect_type(lines):
    """MRZ type of a list of lines or ``None``."""
    n = len(lines)
    if n == 3 and all(len(ln) == 30 for ln in lines):
        return "TD1"
    if n == 2 and len(lines[0]) == len(lines[1]):
        visa = lines[0][:1] == "V"
        if len(lines[0]) == 44:
            return "MRVA" if visa else "TD3"
        if len(lines[0]) == 36:
            return "MRVB" if visa else "TD2"
    return None


def _composite_text(mrz_type, lines):
    parts, _ = _COMPOSITE[mrz_type]
    return "".join(lines[ln][a:b] for ln, a, b in parts)


def _long_td1_number(lines):
    """TD1 document numbers longer than 9 characters continue in the optional data."""
    if lines[0][14] != "<":
        return None
    rest = lines[0][15:].rstrip("<")
    if len(rest) < 2 or not rest[-1].isdigit():
        return None
    return lines[0][5:14] + rest[:-1], rest[-1]


def check_status(mrz_type, lines):
    """Return ``{check name: bool}`` for all check digits of the MRZ."""
    res = {}
    for name, ln, a, b, cl, cp in _CHECKS[mrz_type]:
        field, given = lines[ln][a:b], lines[cl][cp]
        if name == "document_number" and mrz_type == "TD1":
            long_no = _long_td1_number(lines)
            if long_no:
                res[name] = check_digit(long_no[0]) == long_no[1]
                continue
        if name == "optional_data" and given == "<":
            # the check digit may be a filler when the optional data is empty
            res[name] = field.strip("<") == ""
            continue
        res[name] = given == check_digit(field)
    if mrz_type in _COMPOSITE:
        _, (cl, cp) = _COMPOSITE[mrz_type]
        res["final"] = lines[cl][cp] == check_digit(_composite_text(mrz_type, lines))
    return res


def _format_date(raw, kind, today=None):
    """YYMMDD -> YYYY-MM-DD; ``None`` when it is not a calendar date."""
    if len(raw) != 6 or not raw.isdigit():
        return None
    today = today or date.today()
    yy, mm, dd = int(raw[:2]), int(raw[2:4]), int(raw[4:])
    if kind == "birth":
        year = 2000 + yy
        if year > today.year or (year == today.year and (mm, dd) > (today.month, today.day)):
            year -= 100
    else:
        # expiry dates lie between the recent past and a few decades ahead
        year = 2000 + yy
        if year > today.year + 50:
            year -= 100
    if mm == 0 or dd == 0:
        # partially unknown dates are allowed by the standard
        return "%04d-%02d-%02d" % (year, mm, dd) if mm <= 12 and dd <= 31 else None
    try:
        return date(year, mm, dd).isoformat()
    except ValueError:
        return None


# ISO 3166-1 alpha-3 plus the extra codes of ICAO Doc 9303 part 3 (and the UTO specimen state)
_COUNTRY_CODES = frozenset((
    "ABW AFG AGO AIA ALA ALB AND ARE ARG ARM ASM ATA ATF ATG AUS AUT "
    "AZE BDI BEL BEN BES BFA BGD BGR BHR BHS BIH BLM BLR BLZ BMU BOL "
    "BRA BRB BRN BTN BVT BWA CAF CAN CCK CHE CHL CHN CIV CMR COD COG "
    "COK COL COM CPV CRI CUB CUW CXR CYM CYP CZE DEU DJI DMA DNK DOM "
    "DZA ECU EGY ERI ESH ESP EST ETH FIN FJI FLK FRA FRO FSM GAB GBR "
    "GEO GGY GHA GIB GIN GLP GMB GNB GNQ GRC GRD GRL GTM GUF GUM GUY "
    "HKG HMD HND HRV HTI HUN IDN IMN IND IOT IRL IRN IRQ ISL ISR ITA "
    "JAM JEY JOR JPN KAZ KEN KGZ KHM KIR KNA KOR KWT LAO LBN LBR LBY "
    "LCA LIE LKA LSO LTU LUX LVA MAC MAF MAR MCO MDA MDG MDV MEX MHL "
    "MKD MLI MLT MMR MNE MNG MNP MOZ MRT MSR MTQ MUS MWI MYS MYT NAM "
    "NCL NER NFK NGA NIC NIU NLD NOR NPL NRU NZL OMN PAK PAN PCN PER "
    "PHL PLW PNG POL PRI PRK PRT PRY PSE PYF QAT REU ROU RUS RWA SAU "
    "SDN SEN SGP SGS SHN SJM SLB SLE SLV SMR SOM SPM SRB SSD STP SUR "
    "SVK SVN SWE SWZ SXM SYC SYR TCA TCD TGO THA TJK TKL TKM TLS TON "
    "TTO TUN TUR TUV TWN TZA UGA UKR UMI URY USA UZB VAT VCT VEN VGB "
    "VIR VNM VUT WLF WSM YEM ZAF ZMB ZWE "
    "D GBD GBN GBO GBP GBS UNO UNA UNK XXA XXB XXC XXX EUE XBA XIM XCC XCE XCO XEC XPO XES XMP XOM XDC"
    " RKS ANT NTZ YUG SCG CSK DDR ZAR TMP BUR UTO"
).split())

# where the issuing state and nationality codes sit: (line, start)
_CODE_POS = {
    "TD3": ((0, 2), (1, 10)), "MRVA": ((0, 2), (1, 10)),
    "TD2": ((0, 2), (1, 10)), "MRVB": ((0, 2), (1, 10)),
    "TD1": ((0, 2), (1, 15)),
}


def bad_codes(mrz_type, lines):
    """Number of issuing state / nationality codes that are not known ICAO codes."""
    n = 0
    for ln, a in _CODE_POS[mrz_type]:
        code = lines[ln][a:a + 3].strip("<")
        n += bool(code) and code not in _COUNTRY_CODES
    return n


def bad_dates(mrz_type, lines):
    """Number of birth/expiry fields that are not calendar dates."""
    n = 0
    for name, ln, a, b, _, _ in _CHECKS[mrz_type]:
        if name in ("birth_date", "expiry_date"):
            n += _format_date(lines[ln][a:b], name[:-5]) is None
    return n


def _names(field):
    field = field.strip("<")
    if "<<" in field:
        surname, given = field.split("<<", 1)
    else:
        surname, given = field, ""
    clean = lambda s: " ".join(p for p in s.replace("<", " ").split())
    return clean(surname), clean(given)


def parse(lines, include_checkdigit=True):
    """Parse cleaned MRZ lines into the result dictionary."""
    if not lines:
        return {"status": "FAILURE", "status_message": "No MRZ detected"}
    mrz_type = detect_type(lines)
    if mrz_type is None or any(ch not in _IDX for ln in lines for ch in ln):
        return {"status": "FAILURE", "status_message": "Invalid MRZ format"}

    errors = []
    d = {"mrz_type": mrz_type}
    l0, l1 = lines[0], lines[1]
    d["document_code"] = l0[:2].strip("<")
    d["issuer_code"] = l0[2:5].strip("<")
    if not l0[:1].isalpha() or not d["issuer_code"].isalpha():
        errors.append("Invalid MRZ format")
    status = check_status(mrz_type, lines)

    if mrz_type == "TD1":
        long_no = _long_td1_number(lines)
        if long_no:
            d["document_number"], doc_cd = long_no[0], long_no[1]
            optional_1 = ""
        else:
            d["document_number"], doc_cd = l0[5:14].strip("<"), l0[14]
            optional_1 = l0[15:30].strip("<")
        birth, birth_cd, sex = l1[0:6], l1[6], l1[7]
        expiry, expiry_cd, nationality = l1[8:14], l1[14], l1[15:18]
        surname, given = _names(lines[2])
    else:
        surname, given = _names(l0[5:])
        d["document_number"], doc_cd = l1[0:9].strip("<"), l1[9]
        nationality, birth, birth_cd, sex = l1[10:13], l1[13:19], l1[19], l1[20]
        expiry, expiry_cd = l1[21:27], l1[27]

    d["surname"], d["given_name"] = surname, given
    if include_checkdigit:
        d["document_number_checkdigit"] = doc_cd
    d["nationality_code"] = nationality.strip("<")
    if d["nationality_code"] and not d["nationality_code"].isalpha():
        errors.append("Invalid MRZ format")

    d["birth_date"] = _format_date(birth, "birth")
    if include_checkdigit:
        d["birth_date_checkdigit"] = birth_cd
    d["sex"] = sex
    d["expiry_date"] = _format_date(expiry, "expiry")
    if include_checkdigit:
        d["expiry_date_checkdigit"] = expiry_cd
    if d["birth_date"] is None:
        d["birth_date"] = birth
        if birth.strip("<"):
            errors.append("Invalid date of birth")
    if d["expiry_date"] is None:
        d["expiry_date"] = expiry
        if expiry.strip("<"):
            errors.append("Invalid date of expiry")

    if mrz_type == "TD1":
        d["optional_data_1"] = optional_1
        d["optional_data_2"] = l1[18:29].strip("<")
    elif mrz_type == "TD3":
        d["optional_data"] = l1[28:42].strip("<")
        if include_checkdigit:
            d["optional_data_checkdigit"] = l1[42]
    elif mrz_type == "TD2":
        d["optional_data"] = l1[28:35].strip("<")
    else:
        d["optional_data"] = l1[28:].strip("<")
    if include_checkdigit and mrz_type in _COMPOSITE:
        _, (cl, cp) = _COMPOSITE[mrz_type]
        d["final_checkdigit"] = lines[cl][cp]

    for name in ("document_number", "birth_date", "expiry_date", "optional_data", "final"):
        if status.get(name) is False:
            errors.append(_MESSAGES[name])

    d["mrz_text"] = "\n".join(lines)
    if errors:
        d["status"] = "FAILURE"
        d["status_message"] = errors[0]
    else:
        d["status"] = "SUCCESS"
    return d


# --------------------------------------------------------------------------
# OCR repair
# --------------------------------------------------------------------------

def _fit_length(text, probs, target, is_name):
    """Pad / trim a recognised line to ``target`` characters.

    Filler runs are where OCR miscounts, so characters are inserted into or
    removed from the longest run of ``<``.
    """
    n = len(text)
    if n == target:
        return text, probs
    filler = _filler_prob()
    if n < target:
        k = target - n
        if is_name or "<" not in text:
            pos = n
        else:
            pos = _longest_run(text)[1]
        return text[:pos] + "<" * k + text[pos:], probs[:pos] + [filler] * k + probs[pos:]
    # too long: drop doubtful characters at the ends (page border, clutter) first,
    # then surplus fillers
    text, probs = list(text), list(probs)
    while len(text) > target:
        ends = [(probs[i][_IDX[text[i]]], i) for i in (0, len(text) - 1)]
        conf, i = min(ends)
        start, end = _longest_run("".join(text))
        if conf < 0.6 or end - start < 2:
            del text[i], probs[i]
        else:
            del text[end - 1], probs[end - 1]
    return "".join(text), probs


def _filler_prob():
    p = [0.0] * len(CHARSET)
    p[_IDX["<"]] = 0.5
    return p


def _longest_run(text):
    best, cur, start = (0, 0), 0, 0
    for i, ch in enumerate(text + "#"):
        if ch == "<":
            if cur == 0:
                start = i
            cur += 1
        else:
            if cur > best[1] - best[0] or (cur and cur == best[1] - best[0]):
                best = (start, i)
            cur = 0
    return best


def _apply_masks(mrz_type, lines, probs):
    """Force every position into its allowed character class using the OCR probabilities."""
    out = []
    for ln, (text, pr, mask) in enumerate(zip(lines, probs, _MASKS[mrz_type])):
        chars = list(text)
        for i, ch in enumerate(chars):
            allowed = _CLASSES[mask[i]]
            if ch in allowed:
                continue
            best = max(allowed, key=lambda c: pr[i][_IDX[c]])
            # a confident read with no credible alternative is kept: the document
            # itself is malformed and the parser will report it
            if pr[i][_IDX[ch]] >= 0.9 and pr[i][_IDX[best]] < 0.02:
                continue
            if pr[i][_IDX[best]] <= 1e-4:
                best = _CONFUSION.get((ch, mask[i]))
                if best is None or best not in allowed:
                    continue
            chars[i] = best
        out.append("".join(chars))
    return out


# fallback look-alikes when the recogniser gives no usable alternative
_CONFUSION = {}
for _a, _d in (("O", "0"), ("Q", "0"), ("D", "0"), ("I", "1"), ("L", "1"), ("Z", "2"), ("S", "5"),
               ("G", "6"), ("B", "8"), ("T", "7"), ("A", "4")):
    _CONFUSION[(_a, "N")] = _CONFUSION[(_a, "n")] = _d
for _d, _a in (("0", "O"), ("1", "I"), ("2", "Z"), ("5", "S"), ("6", "G"), ("8", "B"), ("4", "A"), ("7", "T")):
    _CONFUSION[(_d, "A")] = _CONFUSION[(_d, "a")] = _a


def _alternatives(mrz_type, lines, probs, positions, min_p, max_p=0.9):
    """Plausible substitutions ``(cost, line, pos, char)`` for the given positions."""
    alts = []
    for ln, i in positions:
        pr, cur = probs[ln][i], lines[ln][i]
        allowed = _CLASSES[_MASKS[mrz_type][ln][i]]
        p_cur = max(pr[_IDX[cur]], 1e-6)
        if p_cur >= max_p:
            continue    # a confident read is never overruled by a check digit
        for c in allowed:
            p = pr[_IDX[c]]
            if c != cur and p >= min_p:
                alts.append((p_cur / p, ln, i, c))
    alts.sort()
    return alts[:10]


def _fix_checks(mrz_type, lines, probs, min_p=0.05):
    """Try the recogniser's second guesses on fields whose check digit fails."""
    lines = list(lines)

    def failing():
        return [k for k, ok in check_status(mrz_type, lines).items() if not ok]

    bad = failing()
    if not bad:
        return lines
    spans = {}
    for name, ln, a, b, cl, cp in _CHECKS[mrz_type]:
        spans[name] = [(ln, i) for i in range(a, b)] + [(cl, cp)]
    if mrz_type == "TD1":
        spans["document_number"] += [(0, i) for i in range(15, 30)]
    if mrz_type in _COMPOSITE:
        parts, (cl, cp) = _COMPOSITE[mrz_type]
        spans["final"] = [(ln, i) for ln, a, b in parts for i in range(a, b)] + [(cl, cp)]

    for name in [n for n in bad if n != "final"] + (["final"] if "final" in bad else []):
        before = failing()
        if name not in before:
            continue
        alts = _alternatives(mrz_type, lines, probs, spans[name], min_p)
        best = None
        for k in (1, 2):
            for combo in combinations(alts, k):
                if len({(c[1], c[2]) for c in combo}) < k:
                    continue
                trial = [list(x) for x in lines]
                for _, ln, i, c in combo:
                    trial[ln][i] = c
                trial = ["".join(x) for x in trial]
                now = [k2 for k2, ok in check_status(mrz_type, trial).items() if not ok]
                # must repair this check without breaking another one
                if name in now or len(now) >= len(before) or set(now) - set(before):
                    continue
                cost = 1.0
                for c in combo:
                    cost *= c[0]
                if best is None or (len(now), cost) < best[0]:
                    best = ((len(now), cost), trial)
            if best:
                break
        if best:
            lines = best[1]
    return lines


def _fix_check_digits(mrz_type, lines, probs, min_p=0.01):
    """Last resort: re-read only the check digits themselves.

    Used when substitutions inside the fields could not satisfy the checks. A
    check digit may be replaced by a low-probability alternative (or, for an
    empty optional data field, by ``0``/``<`` as ICAO 9303 requires) but only
    when the result passes every check.
    """
    status = check_status(mrz_type, lines)
    if all(status.values()):
        return lines
    positions = {}
    for name, ln, a, b, cl, cp in _CHECKS[mrz_type]:
        if not status[name]:
            positions[(cl, cp)] = name
    if mrz_type in _COMPOSITE:
        positions[_COMPOSITE[mrz_type][1]] = "final"
    alts = []
    for (ln, i), name in positions.items():
        pr, cur = probs[ln][i], lines[ln][i]
        p_cur = max(pr[_IDX[cur]], 1e-6)
        forced = ""
        if name == "optional_data":
            ck = [c for c in _CHECKS[mrz_type] if c[0] == name][0]
            if lines[ck[1]][ck[2]:ck[3]].strip("<") == "":
                forced = "0<"
        for c in _CLASSES[_MASKS[mrz_type][ln][i]]:
            if c == cur:
                continue
            p = pr[_IDX[c]]
            if c in forced:
                # a printed digit is far more likely a misread 0 than a misread <
                p = max(p, 0.05 if (c == "0") == cur.isdigit() else 0.02)
            if p >= min_p:
                alts.append((p_cur / p, ln, i, c))
    best = None
    for k in (1, 2):
        for combo in combinations(alts, k):
            if len({(c[1], c[2]) for c in combo}) < k:
                continue
            trial = [list(x) for x in lines]
            for _, ln, i, c in combo:
                trial[ln][i] = c
            trial = ["".join(x) for x in trial]
            if not all(check_status(mrz_type, trial).values()):
                continue
            cost = 1.0
            for c in combo:
                cost *= c[0]
            if best is None or cost < best[0]:
                best = (cost, trial)
        if best:
            return best[1]
    return lines


def _match_issuer(mrz_type, lines, probs, min_p=0.03):
    """Issuing state code that differs from the nationality in one or two letters is most
    likely a misread of it, when the recogniser itself saw those letters as possible."""
    (il, ia), (nl, na) = _CODE_POS[mrz_type]
    issuer, nat = lines[il][ia:ia + 3], lines[nl][na:na + 3]
    if issuer == nat or "<" in nat or not nat.isalpha():
        return lines
    diff = [i for i in range(3) if issuer[i] != nat[i]]
    if len(diff) > 2 or any(probs[il][ia + i][_IDX[nat[i]]] < min_p for i in diff):
        return lines
    out = list(lines)
    out[il] = out[il][:ia] + nat + out[il][ia + 3:]
    return out


def repair(lines, probs):
    """Turn raw recogniser output into a well formed MRZ.

    ``lines`` are the recognised strings, ``probs`` the per character
    probability vectors (indexed like :data:`CHARSET`). Returns
    ``(mrz_type, lines, edits)`` where ``edits`` counts the structural corrections
    that were needed; ``mrz_type`` is ``None`` when the text is not MRZ shaped.
    """
    n = len(lines)
    if n not in (2, 3) or any(len(ln) < 10 for ln in lines):
        return None, lines, 0
    if n == 3:
        target = 30
    else:
        avg = sum(len(ln) for ln in lines) / 2.0
        target = 44 if avg > 40 else 36
    if any(abs(len(ln) - target) > 4 for ln in lines):
        return None, lines, 0
    name_line = 2 if n == 3 else 0
    fitted, fprobs = [], []
    edits = 0
    for i, (ln, pr) in enumerate(zip(lines, probs)):
        t, p = _fit_length(ln, list(pr), target, i == name_line)
        # trailing fillers of the name line are cheap to get wrong and harmless to fix
        edits += abs(len(ln) - target) * (1 if i != name_line else 0.5)
        fitted.append(t)
        fprobs.append(p)
    mrz_type = detect_type(fitted)
    if mrz_type is None:
        return None, lines, 0
    masked = _apply_masks(mrz_type, fitted, fprobs)
    masked = _match_issuer(detect_type(masked) or mrz_type, masked, fprobs)
    edits += sum(a != b for x, y in zip(fitted, masked) for a, b in zip(x, y))
    mrz_type = detect_type(masked)
    fixed = _fix_check_digits(mrz_type, _fix_checks(mrz_type, masked, fprobs), fprobs)
    # substitutions made only to satisfy a check digit weigh double
    edits += 2 * sum(a != b for x, y in zip(masked, fixed) for a, b in zip(x, y))
    return mrz_type, fixed, edits
