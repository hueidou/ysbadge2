# -*- coding: utf-8 -*-
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import sys, time
sys.path.insert(0, _ROOT)
import epd_send as E
from PIL import Image

def unpack(raw):
    im = Image.new("RGB", (800, 480))
    px = im.load()
    PAL = E.PALETTE
    for y in range(480):
        for x in range(0, 800, 2):
            b = raw[(y*800 + x)//2]
            px[x, y] = PAL[b >> 4]
            px[x+1, y] = PAL[b & 15]
    return im

for name in ("P20261021-191121.jpg", "_verify/test_pattern.png"):
    t = time.time()
    raw, info = E.encode_image(_ROOT + r"/" + name, True, False)
    dt = time.time() - t
    im = unpack(raw)
    tag = name.split("/")[-1].split(".")[0]
    im.save(rf"{_VD}/base_{tag}.png")
    print(f"BASELINE {tag}: {dt:.1f}s, colors={len(im.getcolors(400000))}")
