# -*- coding: utf-8 -*-
"""新实现 vs 基线：速度、像素差异、压缩体积。"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import sys, time
sys.path.insert(0, _ROOT)
import epd_send as E
from PIL import Image

def unpack(raw):
    im = Image.new("RGB", (800, 480)); px = im.load()
    for y in range(480):
        for x in range(0, 800, 2):
            b = raw[(y*800 + x)//2]
            px[x, y] = E.PALETTE[b >> 4]; px[x+1, y] = E.PALETTE[b & 15]
    return im

for name in ("P20261021-191121.jpg", "_verify/test_pattern.png"):
    tag = name.split("/")[-1].split(".")[0]
    t = time.time()
    raw, _ = E.encode_image(_ROOT + r"/" + name, True, False)
    dt = time.time() - t
    comp, bits = E.compress(raw)
    im = unpack(raw)
    im.save(rf"{_VD}/new_{tag}.png")
    base = Image.open(rf"{_VD}/base_{tag}.png").load()
    px = im.load()
    diff = sum(1 for y in range(480) for x in range(800) if px[x, y] != base[x, y])
    print(f"{tag:24} {dt:5.2f}s  bits={bits:7d}  bytes={len(comp):6d}  colors={len(im.getcolors(400000))}  与基线不同像素={diff} ({100*diff/(800*480):.2f}%)")
