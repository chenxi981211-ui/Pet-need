#!/usr/bin/env python3
"""
Zet een foto op de juiste plek in de site (schaalt en comprimeert automatisch).

Gebruik:
    python3 scripts/add-photo.py <bestand> <bestemming>

Bestemmingen:
    winkel        de winkelpui        -> assets/img/site/winkel.jpg        (4:3)
    winkelkat     de winkelkat        -> assets/img/site/winkelkat.jpg     (3:4)
    winkelkat-2   tweede kattenfoto   -> assets/img/site/winkelkat-2.jpg   (1:1)
    hero          hoofdfoto homepage  -> assets/img/site/hero-hond.jpg     (1:1)

Voorbeeld:
    python3 scripts/add-photo.py ~/Downloads/IMG_1234.jpg winkelkat
    python3 scripts/build.py
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow ontbreekt. Installeer met:  python3 -m pip install --user Pillow")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGETS = {
    # naam:        (pad,                                  breedte, hoogte, verticale bijsnijfocus)
    "winkel":      ("assets/img/site/winkel.jpg",          1400, 1050, 0.5),
    "winkelkat":   ("assets/img/site/winkelkat.jpg",        900, 1200, 0.35),
    "winkelkat-2": ("assets/img/site/winkelkat-2.jpg",      800,  800, 0.4),
    "hero":        ("assets/img/site/hero-hond.jpg",       1200, 1200, 0.4),
}


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in TARGETS:
        print(__doc__)
        sys.exit(1)

    src = os.path.expanduser(sys.argv[1])
    if not os.path.exists(src):
        sys.exit("Bestand niet gevonden: %s" % src)

    rel, tw, th, focus = TARGETS[sys.argv[2]]
    im = Image.open(src)
    im = im.convert("RGB")

    # cover-crop naar de doelverhouding, met de focus iets boven het midden
    target, cur = tw / th, im.width / im.height
    if cur > target:
        nw = int(im.height * target)
        left = int((im.width - nw) * 0.5)
        im = im.crop((left, 0, left + nw, im.height))
    else:
        nh = int(im.width / target)
        top = int((im.height - nh) * focus)
        im = im.crop((0, top, im.width, top + nh))
    im = im.resize((tw, th), Image.LANCZOS)

    dst = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im.save(dst, quality=84, optimize=True)
    print("Opgeslagen: %s  (%d×%d, %d KB)" % (rel, tw, th, os.path.getsize(dst) / 1024))
    print("Draai nu:   python3 scripts/build.py")


if __name__ == "__main__":
    main()
