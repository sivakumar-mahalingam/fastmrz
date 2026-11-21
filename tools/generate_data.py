"""Synthetic MRZ line generator (training data for the recognizer)."""
import random, string, sys, os
import numpy as np, cv2
from fonts import resolve  # noqa: run from the tools directory
from PIL import Image, ImageDraw, ImageFont

CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<"
H, W = 32, 768
FONTS = [("OCRB.otf", 70),
         ("OCRBS.otf", 12),
         ("DejaVuSansMono.ttf", 5),
         ("LiberationMono-Regular.ttf", 5),
         ("LiberationMono-Bold.ttf", 4),
         ("FreeMonoBold.ttf", 4)]
WIDE = [("OCRB.otf", 34),
        ("OCRBS.otf", 6),
        ("OCRBL.otf", 6),
        ("JetBrainsMono-Regular.ttf", 4),
        ("JetBrainsMono-Bold.ttf", 3),
        ("DejaVuSansMono.ttf", 3),
        ("DejaVuSans.ttf", 5),
        ("DejaVuSans-Bold.ttf", 4),
        ("LiberationSans-Regular.ttf", 5),
        ("LiberationSans-Bold.ttf", 4),
        ("LiberationMono-Regular.ttf", 3),
        ("FreeSans.ttf", 4),
        ("FreeSansBold.ttf", 3),
        ("Inter-Medium.otf", 4),
        ("Inter-SemiBold.otf", 3),
        ("Carlito-Regular.ttf", 3),
        ("ipag.ttf", 3),
        ("FreeMonoBold.ttf", 2)]
if os.environ.get("FONTSET") == "wide":
    FONTS = WIDE
FS = 40
EDGE_P = 0.3
_fonts = {}
def font(p):
    if p not in _fonts: _fonts[p] = ImageFont.truetype(resolve(p), FS)
    return _fonts[p]

L, D = string.ascii_uppercase, string.digits
def rs(n, a): return "".join(random.choice(a) for _ in range(n))
def name(maxlen):
    parts = [rs(random.randint(2, 10), L) for _ in range(random.randint(1, 3))]
    giv = [rs(random.randint(1, 9), L) for _ in range(random.randint(0, 3))]
    s = "<".join(parts) + "<<" + "<".join(giv)
    return s[:maxlen].ljust(maxlen, "<")
def opt(n):
    r = random.random()
    if r < .4: return "<" * n
    k = random.randint(1, n)
    return rs(k, D if random.random() < .6 else D + L).ljust(n, "<")
def docno(n=9):
    r = random.random()
    s = rs(n, D) if r < .4 else rs(random.randint(1, 3), L) + rs(n - 3, D) if r < .7 else rs(n, D + L)
    if random.random() < .15:
        k = random.randint(5, n - 1); s = s[:k].ljust(n, "<")
    return s[:n].ljust(n, "<")
def text():
    r = random.random()
    c3 = lambda: rs(3, L) if random.random() < .9 else rs(1, L) + "<<"
    sex = lambda: random.choice("MFMF<X")
    if r < .14:   # TD3 l1
        return random.choice(["P<", "P<", "PA", "PP", "PD", "PM", "PO", "PS", "V<", "VN"]) + c3() + name(39)
    if r < .30:   # TD3/MRVA l2
        return docno() + rs(1, D) + c3() + rs(7, D) + sex() + rs(7, D) + opt(14) + random.choice([rs(2, D), "<" + rs(1, D), "<<"])
    if r < .36:   # TD2 l1
        return random.choice(["I<", "ID", "A<", "C<", "IP", "V<", "AC"]) + c3() + name(31)
    if r < .43:   # TD2 l2
        return docno() + rs(1, D) + c3() + rs(7, D) + sex() + rs(7, D) + opt(7) + random.choice([rs(1, D), "<"])
    if r < .51:   # TD1 l1
        return random.choice(["I<", "ID", "A<", "C<", "IR", "AR", "CR", "IO", "I" + rs(1, L)]) + c3() + docno() + random.choice([rs(1, D), "<"]) + opt(15)
    if r < .59:   # TD1 l2
        return rs(7, D) + sex() + rs(7, D) + c3() + opt(11) + rs(1, D)
    if r < .66:   # TD1 l3
        return name(30)
    if r < .70:   # French old ID
        return ("IDFRA" + name(25) + rs(6, D + "<")) if random.random() < .5 else (rs(12, D) + rs(1, D) + name(14) + rs(7, D) + sex() + rs(1, D))
    # random strings, random runs
    n = random.choice([30, 36, 44, 30, 36, 44, random.randint(18, 48)])
    out = ""
    while len(out) < n:
        q = random.random()
        k = random.randint(1, 12)
        out += "<" * k if q < .25 else rs(k, D) if q < .55 else rs(k, L) if q < .85 else rs(k, D + L)
    return out[:n]

def render_line(draw, txt, fnt, x0, y0, pitch, fill, jit=0):
    for i, ch in enumerate(txt):
        bb = fnt.getbbox(ch)
        cw = bb[2] - bb[0]
        x = x0 + i * pitch + (pitch - cw) / 2 - bb[0] + (random.uniform(-jit, jit) if jit else 0)
        y = y0 + (random.uniform(-jit, jit) if jit else 0)
        draw.text((x, y), ch, font=fnt, fill=fill)

def smooth_noise(h, w, k, amp):
    g = np.random.randn(max(2, h // k), max(2, w // k)).astype(np.float32)
    return cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC) * amp

def background(h, w):
    base = random.uniform(120, 250)
    bg = np.full((h, w), base, np.float32)
    bg += smooth_noise(h, w, random.choice([16, 40, 100]), random.uniform(0, 22))
    if random.random() < .5:  # gradient
        gx = np.linspace(0, 1, w, dtype=np.float32)[None, :] * random.uniform(-50, 50)
        gy = np.linspace(0, 1, h, dtype=np.float32)[:, None] * random.uniform(-30, 30)
        bg += gx + gy
    if random.random() < .45:  # guilloche / security pattern
        xs = np.arange(w, dtype=np.float32)
        for _ in range(random.randint(2, 14)):
            a = random.uniform(5, 60); f = random.uniform(.002, .03); ph = random.uniform(0, 6.3)
            ys = random.uniform(0, h) + a * np.sin(xs * f + ph)
            pts = np.stack([xs, ys], 1).astype(np.int32)
            cv2.polylines(bg, [pts], False, base + random.uniform(-45, 30), random.randint(1, 3), cv2.LINE_AA)
    if random.random() < .15:  # fine periodic raster
        p = random.randint(3, 9)
        bg[:, ::p] += random.uniform(-25, 15)
    if random.random() < .12:
        p = random.randint(3, 9)
        bg[::p, :] += random.uniform(-25, 15)
    return bg

def sample():
    fp = random.choices([f for f, _ in FONTS], [w for _, w in FONTS])[0]
    fnt = font(fp)
    txt = text()
    n = len(txt)
    adv = fnt.getlength("0")
    pitch = adv * random.uniform(0.92, 1.30) if fp.startswith("OCRB") else max(adv, fnt.getlength("W") * random.uniform(0.85, 1.0)) * random.uniform(0.95, 1.25)
    asc = fnt.getbbox("H"); ch = asc[3] - asc[1]; ytop = asc[1]
    lsp = pitch * random.uniform(1.9, 2.8)
    mx = int(pitch * 6); my = int(lsp * 1.6)
    cw_, chh = int(n * pitch + 2 * mx), int(ch + 2 * my)
    ink = Image.new("L", (cw_, chh), 0)
    dr = ImageDraw.Draw(ink)
    jit = random.uniform(0, 1.5) if random.random() < .3 else 0
    render_line(dr, txt, fnt, mx, my - ytop, pitch, 255, jit)
    # neighbours (other MRZ lines / text) above and below
    for sgn in (-1, 1):
        if random.random() < .8:
            t2 = text()[:n + 4]
            off = random.uniform(-.5, .5) * pitch if random.random() < .3 else 0
            render_line(dr, t2, fnt, mx + off, my - ytop + sgn * lsp, pitch, 255)
    # clutter text left / right
    if random.random() < .15:
        render_line(dr, rs(3, L + D), fnt, mx - pitch * random.uniform(4.5, 6), my - ytop, pitch, 255)
    if random.random() < .15:
        render_line(dr, rs(3, L + D), fnt, mx + (n + random.uniform(1.5, 3)) * pitch, my - ytop, pitch, 255)
    ink = np.asarray(ink, np.uint8)
    # stroke weight
    r = random.random()
    if r < .25: ink = cv2.dilate(ink, np.ones((3, 3), np.uint8), iterations=1)
    elif r < .40: ink = cv2.erode(ink, np.ones((2, 2), np.uint8))
    if random.random() < .12:  # broken / dotty print
        m = (np.random.rand(*ink.shape) > random.uniform(.05, .25)).astype(np.uint8)
        m = cv2.erode(m, np.ones((2, 2), np.uint8))
        ink = ink * m
    a = ink.astype(np.float32) / 255
    bg = background(chh, cw_)
    dark = random.uniform(0, 95)
    alpha = random.uniform(.55, 1.0)
    if random.random() < .08: dark = random.uniform(95, 130)
    img = bg * (1 - a * alpha) + dark * a * alpha
    if random.random() < .25:  # overlay clutter: faint stamp / hologram streaks
        ov = smooth_noise(chh, cw_, random.choice([8, 20]), 1.0)
        img += (ov > random.uniform(.8, 1.6)) * random.uniform(-40, 60)
    if random.random() < .2:  # glare blob
        cx, cy = random.uniform(0, cw_), random.uniform(0, chh)
        yy, xx = np.mgrid[0:chh, 0:cw_].astype(np.float32)
        s = random.uniform(.5, 3) * ch
        img += random.uniform(40, 150) * np.exp(-(((xx - cx) / (s * 3)) ** 2 + ((yy - cy) / s) ** 2))
    # document / page edges next to the MRZ (the bottom line sits close to the page border)
    if random.random() < EDGE_P:
        yy, xx = np.mgrid[0:chh, 0:cw_].astype(np.float32)
        for side in random.sample(["l", "r", "b", "t"], random.choice([1, 1, 2, 3])):
            sl_ = random.uniform(-.03, .03)
            if side == "l": dist = (mx - pitch * random.uniform(.25, 2.2)) - xx + sl_ * yy
            elif side == "r": dist = xx - (mx + n * pitch + pitch * random.uniform(.25, 2.2)) + sl_ * yy
            elif side == "b": dist = yy - (my + ch + ch * random.uniform(.25, 1.0)) + sl_ * xx
            else: dist = (my - ch * random.uniform(.25, 1.0)) - yy + sl_ * xx
            outside = np.clip(dist / random.uniform(.5, 3) + .5, 0, 1)
            lvl = random.choice([random.uniform(0, 70), random.uniform(60, 200), random.uniform(200, 255)])
            tex = lvl + smooth_noise(chh, cw_, random.choice([4, 12, 40]), random.uniform(0, 25))
            img = img * (1 - outside) + tex * outside
            if random.random() < .5:   # dark or bright rim line
                rim = np.exp(-(dist / random.uniform(1, 4)) ** 2)
                img += rim * random.uniform(-120, 80)
    if random.random() < .2:       # page curvature
        A = random.uniform(.03, .16) * ch
        xs_ = np.arange(cw_, dtype=np.float32)
        dy = A * np.sin(np.pi * (xs_ - mx) / max(1.0, n * pitch) * random.uniform(.5, 1.5) + random.uniform(0, 6.3))
        mapx = np.repeat(xs_[None, :], chh, 0)
        mapy = np.arange(chh, dtype=np.float32)[:, None] + dy[None, :]
        img = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    img = np.clip(img, 0, 255)
    # crop quad
    hh = ch * random.uniform(1.15, 2.1)
    cy = my + ch / 2 + random.uniform(-.14, .14) * ch
    xl = mx - pitch * random.uniform(-.08, 1.6) if random.random() < .85 else mx - pitch * random.uniform(1.6, 3.5)
    xr = mx + n * pitch + pitch * random.uniform(-.08, 1.6) if random.random() < .85 else mx + n * pitch + pitch * random.uniform(1.6, 3.5)
    ang = np.deg2rad(random.gauss(0, .5)); ang = float(np.clip(ang, -.03, .03))
    sl = np.tan(ang)
    kst = random.uniform(-.06, .06) * hh  # keystone
    shear = random.uniform(-.12, .12) * hh
    src = np.float32([[xl + shear / 2, cy - hh / 2 - sl * (xr - xl) / 2 - kst / 2],
                      [xr + shear / 2, cy - hh / 2 + sl * (xr - xl) / 2 + kst / 2],
                      [xr - shear / 2, cy + hh / 2 + sl * (xr - xl) / 2 - kst / 2],
                      [xl - shear / 2, cy + hh / 2 - sl * (xr - xl) / 2 + kst / 2]])
    # native resolution (char height in px of the "photo")
    nat = random.choice([random.uniform(5.5, 10), random.uniform(8, 16), random.uniform(12, 40)])
    sc = nat / ch
    nw, nh = max(8, int((xr - xl) * sc)), max(6, int(hh * sc))
    M = cv2.getPerspectiveTransform(src, np.float32([[0, 0], [nw, 0], [nw, nh], [0, nh]]))
    # antialiased downscale: blur first
    sig = max(0.01, 0.45 / sc)
    pre = cv2.GaussianBlur(img, (0, 0), sig) if sc < 0.7 else img
    im = cv2.warpPerspective(pre, M, (nw, nh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    r = random.random()
    if r < .45: im = cv2.GaussianBlur(im, (0, 0), random.uniform(.3, max(.5, nat / 11)))
    elif r < .55:  # motion blur
        k = random.randint(2, max(2, int(nat / 3)))
        ker = np.zeros((k, k), np.float32)
        if random.random() < .5: ker[k // 2, :] = 1
        else: ker[:, k // 2] = 1
        im = cv2.filter2D(im, -1, ker / ker.sum())
    if random.random() < .6: im += np.random.randn(*im.shape).astype(np.float32) * random.uniform(1, 5 + 9 * min(1, nat / 16))
    if random.random() < .4:  # contrast / gamma
        im = (np.clip(im, 0, 255) / 255) ** random.uniform(.6, 1.7) * 255
        c = random.uniform(.35, 1.0); im = (im - im.mean()) * c + im.mean()
    im = np.clip(im, 0, 255).astype(np.uint8)
    if random.random() < .6:
        _, enc = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, random.randint(15, 92)])
        im = cv2.imdecode(enc, cv2.IMREAD_GRAYSCALE)
    if random.random() < .15:  # unsharp (phone sharpening)
        b = cv2.GaussianBlur(im, (0, 0), 1.0)
        im = cv2.addWeighted(im, 1 + random.uniform(.5, 1.5), b, -random.uniform(.5, 1.5), 0)
    interp = random.choice([cv2.INTER_LINEAR, cv2.INTER_CUBIC, cv2.INTER_AREA, cv2.INTER_LINEAR])
    im = cv2.resize(im, (W, H), interpolation=interp)
    return norm(im), txt

def norm(im):
    """Contrast stretch used identically at train and inference time."""
    im = im.astype(np.float32)
    lo, hi = np.percentile(im, (2, 98))
    if hi - lo < 1: hi = lo + 1
    return np.clip((im - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    out, n, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    if len(sys.argv) > 4: EDGE_P = float(sys.argv[4])
    random.seed(seed); np.random.seed(seed)
    cv2.setNumThreads(1)
    X = np.lib.format.open_memmap(out + "_x.npy", mode="w+", dtype=np.uint8, shape=(n, H, W))
    T = []
    for i in range(n):
        X[i], t = sample(); T.append(t)
    X.flush()
    open(out + "_y.txt", "w").write("\n".join(T))
