"""MRZ localisation.

Finds candidate MRZ blocks as groups of 2-3 parallel, equally long text lines
and returns one quadrilateral per text line (in source image coordinates).
Pure OpenCV, no neural network: the candidates are verified later by the
recogniser and the MRZ check digits, so recall matters more than precision.
"""
import math

import cv2
import numpy as np

__all__ = ["find_candidates", "refine_candidate", "warp_line"]


def _resize(gray, long_side):
    h, w = gray.shape[:2]
    scale = long_side / float(max(h, w))
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
    small = cv2.resize(gray, (max(1, int(round(w * scale))), max(1, int(round(h * scale)))), interpolation=interp)
    return small, scale


def _text_lines(gray, smear, iso=False):
    """Return rotated boxes (cx, cy, length, height, angle_rad) of text-line shaped blobs.

    ``iso=False`` smears ink horizontally, which is robust for roughly upright
    text. ``iso=True`` uses an isotropic closing instead: the gap between MRZ
    characters is much smaller than the gap between MRZ lines, so characters
    merge into lines whatever the rotation of the document.
    """
    g = cv2.GaussianBlur(gray, (3, 3), 0)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (19, 19))
    bh = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, k)
    # local contrast normalisation so faint MRZ print survives next to strong edges
    loc = cv2.blur(bh, (61, 61)).astype(np.float32)
    bh = np.clip(bh.astype(np.float32) * 48.0 / (loc + 12.0), 0, 255).astype(np.uint8)
    if iso:
        sm = cv2.morphologyEx(bh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (smear, smear)))
        sm = cv2.blur(sm, (3, 3))
    else:
        sm = cv2.morphologyEx(bh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (smear, 1)))
        sm = cv2.blur(sm, (max(3, smear // 2) | 1, 1))
    if iso:
        # flat surroundings (table, scanner lid) must not drag the threshold down
        vals = sm[sm > 8]
        if vals.size < 100:
            return []
        thr, _ = cv2.threshold(vals.reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        bw = (sm > thr * 1.15).astype(np.uint8)
    else:
        thr, _ = cv2.threshold(sm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        bw = (sm > thr * 0.8).astype(np.uint8)
    if iso:
        bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    else:
        bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (smear, 3)))
    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        if len(c) < 5:
            continue
        (cx, cy), (bw_, bh_), ang = cv2.minAreaRect(c)
        if bw_ < bh_:
            bw_, bh_, ang = bh_, bw_, ang + 90.0
        ang = (ang + 90.0) % 180.0 - 90.0
        if bh_ < 4 or bh_ > 70 or bw_ < 30 or bw_ < 2.5 * bh_:
            continue
        if not iso and abs(ang) > 30:
            continue
        boxes.append((cx, cy, bw_, bh_, math.radians(ang)))
    boxes = _merge_collinear(boxes)
    return [b for b in boxes if b[2] >= 110 and b[2] >= 7.0 * b[3]]


def _merge_collinear(boxes):
    """Join fragments of one text line (same direction, same baseline, small gap)."""
    n = len(boxes)
    if n < 2 or n > 400:
        return boxes
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        cx, cy, L, H, a = boxes[i]
        ux, uy = math.cos(a), math.sin(a)
        for j in range(i + 1, n):
            cx2, cy2, L2, H2, a2 = boxes[j]
            hm = max(H, H2)
            if min(H, H2) < 0.5 * hm:
                continue
            # short fragments have unreliable angles: compare positions instead
            dx, dy = cx2 - cx, cy2 - cy
            if L >= L2:
                along, perp = dx * ux + dy * uy, -dx * uy + dy * ux
            else:
                u2x, u2y = math.cos(a2), math.sin(a2)
                along, perp = dx * u2x + dy * u2y, -dx * u2y + dy * u2x
            if abs(perp) > 0.45 * hm + 0.03 * abs(along):
                continue
            if abs(along) - 0.5 * (L + L2) > 2.5 * hm:
                continue
            if min(L, L2) > 6 * hm and _angle_diff(a, a2) > math.radians(6):
                continue
            parent[find(i)] = find(j)
    clusters = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(i)
    out = []
    for idx in clusters.values():
        if len(idx) == 1:
            out.append(boxes[idx[0]])
            continue
        pts = np.concatenate([cv2.boxPoints(((boxes[i][0], boxes[i][1]), (boxes[i][2], boxes[i][3]),
                                             math.degrees(boxes[i][4]))) for i in idx]).astype(np.float32)
        (cx, cy), (w_, h_), ang = cv2.minAreaRect(pts)
        if w_ < h_:
            w_, h_, ang = h_, w_, ang + 90.0
        ang = (ang + 90.0) % 180.0 - 90.0
        out.append((cx, cy, w_, h_, math.radians(ang)))
    return out


def _angle_diff(a, b):
    """Smallest difference between two line directions (mod 180 degrees)."""
    return abs((a - b + math.pi / 2) % math.pi - math.pi / 2)


def _group(boxes):
    """Group line boxes into stacks of 2..3 parallel lines with equal length."""
    n = len(boxes)
    links = {}
    for i in range(n):
        cx, cy, L, H, a = boxes[i]
        ux, uy = math.cos(a), math.sin(a)
        best = None
        for j in range(n):
            if j == i:
                continue
            cx2, cy2, L2, H2, a2 = boxes[j]
            if _angle_diff(a, a2) > math.radians(5):
                continue
            if min(L, L2) / max(L, L2) < 0.72 or min(H, H2) / max(H, H2) < 0.5:
                continue
            dx, dy = cx2 - cx, cy2 - cy
            along = dx * ux + dy * uy
            perp = -dx * uy + dy * ux
            hm = 0.5 * (H + H2)
            if perp < 1.1 * hm or perp > 5.0 * hm:
                continue
            if abs(along) > 0.16 * max(L, L2):
                continue
            if best is None or perp < best[0]:
                best = (perp, j)
        if best:
            links[i] = best[1]
    groups, used = [], set()
    targets = set(links.values())
    for i in range(n):
        if i in used or i not in links or i in targets:
            continue
        chain = [i]
        while chain[-1] in links and links[chain[-1]] not in chain:
            chain.append(links[chain[-1]])
        used.update(chain)
        # an MRZ has 2 or 3 lines; longer stacks are split into sliding windows
        if len(chain) <= 3:
            groups.append(chain)
            if len(chain) == 3:
                groups.append(chain[1:])
                groups.append(chain[:2])
        else:
            for k in range(len(chain) - 1, 0, -1):
                if k >= 2:
                    groups.append(chain[k - 2:k + 1])
                groups.append(chain[k - 1:k + 1])
    out = []
    for g in groups:
        ref = boxes[g[0]][4]
        grp = []
        for i in g:
            cx, cy, L, H, a = boxes[i]
            # express all directions of a group on the same branch
            while a - ref > math.pi / 2:
                a -= math.pi
            while a - ref < -math.pi / 2:
                a += math.pi
            grp.append((cx, cy, L, H, a))
        out.append(grp)
    return out


def _quads(group, scale, to_src):
    """One quad (TL, TR, BR, BL) per line, sharing the horizontal extent of the group."""
    ang = float(np.mean([b[4] for b in group]))
    ux, uy = math.cos(ang), math.sin(ang)
    hm = float(np.mean([b[3] for b in group]))
    # all MRZ lines are equally long: use the union of the extents plus a margin
    lo = min((b[0] * ux + b[1] * uy) - b[2] / 2 for b in group) - 0.9 * hm
    hi = max((b[0] * ux + b[1] * uy) + b[2] / 2 for b in group) + 0.9 * hm
    quads = []
    for (cx, cy, L, H, a) in group:
        # each line keeps its own slope (perspective makes the lines non-parallel)
        lx, ly = math.cos(a), math.sin(a)
        nx, ny = -ly, lx
        u0 = cx * ux + cy * uy
        proj = max(1e-6, lx * ux + ly * uy)
        half = 0.5 * 1.55 * max(H + 3.0, hm) + 1.0
        pts = []
        for t, side in ((lo, -1), (hi, -1), (hi, 1), (lo, 1)):
            d = (t - u0) / proj
            pts.append((cx + d * lx + side * half * nx, cy + d * ly + side * half * ny))
        quads.append(to_src(np.array(pts, np.float32) / scale))
    return quads


def _detect(gray, long_side, smear, iso):
    small, scale = _resize(gray, long_side)
    out = []
    for g in _group(_text_lines(small, smear, iso)):
        length = float(np.mean([b[2] for b in g]))
        out.append({"score": length * (1.0 + 0.15 * len(g)) / long_side, "n": len(g), "group": g, "scale": scale})
    return out


def find_candidates(gray, long_sides=(1024,), rotations=(0, 90), smear=25, iso=False, max_candidates=8):
    """Return candidate MRZ blocks, best first.

    Each candidate is ``{"quads": [4x2 float32, ...], "score": float}`` with one
    quad per text line, top line first, in coordinates of ``gray``. With
    ``iso=True`` lines of any orientation are found in a single pass.
    """
    if iso:
        rotations = (0,)
    h, w = gray.shape[:2]
    cands = []
    for rot in rotations:
        if rot == 0:
            img, to_src = gray, (lambda p: p)
        elif rot == 90:   # rotate image 90deg clockwise; map points back
            img = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
            to_src = (lambda p, h=h: np.stack([p[:, 1], h - 1 - p[:, 0]], 1).astype(np.float32))
        else:
            M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), rot, 1.0)
            cos, sin = abs(M[0, 0]), abs(M[0, 1])
            nw, nh = int(h * sin + w * cos), int(h * cos + w * sin)
            M[0, 2] += nw / 2.0 - w / 2.0
            M[1, 2] += nh / 2.0 - h / 2.0
            img = cv2.warpAffine(gray, M, (nw, nh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            Mi = cv2.invertAffineTransform(M)
            to_src = (lambda p, Mi=Mi: (np.hstack([p, np.ones((len(p), 1), np.float32)]) @ Mi.T).astype(np.float32))
        for ls in long_sides:
            for c in _detect(img, ls, smear, iso):
                c["quads"] = _quads(c["group"], c["scale"], to_src)
                c["rot"] = rot
                cands.append(c)
    cands.sort(key=lambda c: -c["score"])
    return cands[:max_candidates]


def refine_candidate(gray, cand, char_height=16.0, max_width=1800):
    """Re-detect the lines of a candidate at a resolution suited to its text size.

    The first pass runs on a downscaled image, so its line boxes can be off by
    a noticeable fraction of the character height. Here the block is rectified
    and scaled to a nominal character height and the lines are located again.
    Returns a candidate with refined quads (or ``cand`` when nothing better is found).
    """
    quads = cand["quads"]
    top, bot = np.float32(quads[0]), np.float32(quads[-1])
    line_h = float(np.linalg.norm(top[3] - top[0]))
    width = float(np.linalg.norm(top[1] - top[0]))
    if line_h < 2 or width < 20:
        return cand
    # block corners with a margin of one line above/below and a little at the sides
    ex = (top[1] - top[0]) / width
    ey = (top[3] - top[0]) / line_h
    mx, my = 0.6 * line_h, 0.8 * line_h
    src = np.float32([top[0] - ex * mx - ey * my, top[1] + ex * mx - ey * my,
                      bot[2] + ex * mx + ey * my, bot[3] - ex * mx + ey * my])
    bw = float(np.linalg.norm(src[1] - src[0]))
    bh = float(np.linalg.norm(src[3] - src[0]))
    scale = char_height / (line_h / 1.55)
    scale = min(scale, max_width / bw)
    W, H = int(round(bw * scale)), int(round(bh * scale))
    if W < 120 or H < 24:
        return cand
    M = cv2.getPerspectiveTransform(src, np.float32([[0, 0], [W, 0], [W, H], [0, H]]))
    flags = cv2.INTER_AREA if scale < 0.7 else cv2.INTER_CUBIC
    if scale < 0.7:
        # warpPerspective does not antialias: shrink in two steps
        k = int(min(4, math.ceil(1.0 / scale)))
        S = np.diag([k, k, 1.0])
        block = cv2.warpPerspective(gray, S @ M, (W * k, H * k), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        block = cv2.resize(block, (W, H), interpolation=cv2.INTER_AREA)
    else:
        block = cv2.warpPerspective(gray, M, (W, H), flags=flags, borderMode=cv2.BORDER_REPLICATE)
    boxes = [b for b in _text_lines(block, 25) if b[2] > 0.6 * W and abs(b[4]) < math.radians(8)]
    n = len(quads)
    if len(boxes) < n:
        return cand
    boxes.sort(key=lambda b: b[1])
    if len(boxes) > n:
        # keep the n lines closest to where the first pass saw them
        exp = [(float(np.mean(cv2.perspectiveTransform(np.float32(q)[None], M)[0][:, 1]))) for q in quads]
        picked = []
        for y in exp:
            cands = [b for b in boxes if b not in picked]
            picked.append(min(cands, key=lambda b: abs(b[1] - y)))
        boxes = sorted(picked, key=lambda b: b[1])
    Mi = np.linalg.inv(M)
    to_src = lambda p: cv2.perspectiveTransform(np.float32(p)[None], Mi)[0]
    out = dict(cand)
    out["quads"] = _quads(boxes, 1.0, to_src)
    return out


def warp_line(gray, quad, out_w=768, out_h=32, flip=False):
    """Rectify one text line to a fixed size strip."""
    dst = np.float32([[0, 0], [out_w, 0], [out_w, out_h], [0, out_h]])
    src = np.float32(quad)
    if flip:
        src = src[[2, 3, 0, 1]]
    # supersample when the source line is much larger than the output strip
    M = cv2.getPerspectiveTransform(src, dst)
    src_h = float(np.linalg.norm(src[3] - src[0]))
    src_w = float(np.linalg.norm(src[1] - src[0]))
    f = min(src_h / out_h, src_w / out_w)
    if f > 1.5:
        k = int(min(4, math.ceil(f)))
        S = np.diag([k, k, 1.0]).astype(np.float64)
        big = cv2.warpPerspective(gray, S @ M, (out_w * k, out_h * k), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        return cv2.resize(big, (out_w, out_h), interpolation=cv2.INTER_AREA)
    return cv2.warpPerspective(gray, M, (out_w, out_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
