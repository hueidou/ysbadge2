# -*- coding: utf-8 -*-
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import sys
sys.path.insert(0, _ROOT)
import epd_send as E
from PIL import Image, ImageStat, ImageChops

def err(path, src):
    im = Image.open(path).convert("RGB")
    d = ImageChops.difference(im, src)
    st = ImageStat.Stat(d)
    return sum(st.mean)/3.0, sum(st.rms)/3.0

for tag, srcpath in (("P20261021-191121", "P20261021-191121.jpg"), ("test_pattern", "_verify/test_pattern.png")):
    src, _ = E.build_canvas(_ROOT + r"/" + srcpath, fill=False)
    b = err(rf"{_VD}/base_{tag}.png", src)
    n = err(rf"{_VD}/new_{tag}.png", src)
    print(f"{tag:22} 基线 MAE={b[0]:6.2f} RMSE={b[1]:6.2f} | 新 MAE={n[0]:6.2f} RMSE={n[1]:6.2f}")
