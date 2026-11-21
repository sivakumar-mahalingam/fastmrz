"""Locate the fonts used to render synthetic training data.

Fonts are looked up by file name, so they can live anywhere: directories in the
``MRZ_FONT_DIRS`` environment variable (separated by ``os.pathsep``) are searched
first, then the usual system font folders of Linux, macOS and Windows.

Run ``python fonts.py`` to check that every font is present.
"""
import os
import sys

# file name -> Debian/Ubuntu package that ships it
PACKAGES = {
    "OCRB.otf": "fonts-ocr-b",
    "OCRBS.otf": "fonts-ocr-b",
    "OCRBL.otf": "fonts-ocr-b",
    "DejaVuSans.ttf": "fonts-dejavu-core",
    "DejaVuSans-Bold.ttf": "fonts-dejavu-core",
    "DejaVuSansMono.ttf": "fonts-dejavu-mono",
    "LiberationSans-Regular.ttf": "fonts-liberation",
    "LiberationSans-Bold.ttf": "fonts-liberation",
    "LiberationMono-Regular.ttf": "fonts-liberation",
    "LiberationMono-Bold.ttf": "fonts-liberation",
    "FreeSans.ttf": "fonts-freefont-ttf",
    "FreeSansBold.ttf": "fonts-freefont-ttf",
    "FreeMonoBold.ttf": "fonts-freefont-ttf",
    "JetBrainsMono-Regular.ttf": "fonts-jetbrains-mono",
    "JetBrainsMono-Bold.ttf": "fonts-jetbrains-mono",
    "Inter-Medium.otf": "fonts-inter",
    "Inter-SemiBold.otf": "fonts-inter",
    "Carlito-Regular.ttf": "fonts-crosextra-carlito",
    "ipag.ttf": "fonts-ipafont-gothic",
}

_SYSTEM_DIRS = [
    "/usr/share/fonts", "/usr/local/share/fonts", "~/.fonts", "~/.local/share/fonts",
    "/Library/Fonts", "/System/Library/Fonts", "~/Library/Fonts",
    os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
]
_index = None


def _build_index():
    dirs = [d for d in os.environ.get("MRZ_FONT_DIRS", "").split(os.pathsep) if d] + _SYSTEM_DIRS
    index = {}
    for d in dirs:
        d = os.path.expanduser(d)
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                index.setdefault(f, os.path.join(root, f))
    return index


def find(name):
    """Full path of a font file name, or ``None``."""
    global _index
    if _index is None:
        _index = _build_index()
    return _index.get(name)


def resolve(name):
    """Full path of a font file name; exits with install instructions when it is missing."""
    path = find(name)
    if path is None:
        sys.exit("Font %s not found. Run 'python fonts.py' for install instructions." % name)
    return path


def main():
    missing = []
    for name in sorted(PACKAGES):
        path = find(name)
        print("%-28s %s" % (name, path or "MISSING (package %s)" % PACKAGES[name]))
        if path is None:
            missing.append(name)
    if missing:
        print("\n%d font(s) missing. On Debian/Ubuntu:\n  sudo apt install %s"
              % (len(missing), " ".join(sorted({PACKAGES[m] for m in missing}))))
        print("Elsewhere, copy the font files into a folder and set MRZ_FONT_DIRS to it.")
        sys.exit(1)
    print("\nAll %d fonts found." % len(PACKAGES))


if __name__ == "__main__":
    main()
