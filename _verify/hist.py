# -*- coding: utf-8 -*-
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import sys
sys.path.insert(0, _ROOT)
import epd_send as E
from PIL import Image, ImageDraw, ImageFont
PAL = E.PALETTE
def hist(path):
    im = Image.open(path).convert("RGB")
    px = im.load(); c = [0]*7
    for y in range(480):
        for x in range(800):
            c[PAL.index(px[x,y])] += 1
    return c
names = ["黑","白","绿","蓝","红","黄","橙"]
for tag in ("P20261021-191121", "test_pattern"):
    b = hist(rf"{_VD}/base_{tag}.png")
    n = hist(rf"{_VD}/new_{tag}.png")
    print(tag)
    for i,(nb,nn) in enumerate(zip(b,n)):
        print(f"   {names[i]}: 基线 {nb:6d}  新 {nn:6d}  差 {nn-nb:+6d}")

# 并排裁切对比：上=基线，下=新实现，取中央 400x220 放大 2 倍
for tag in ("P20261021-191121",):
    B = Image.open(rf"{_VD}/base_{tag}.png").crop((200,130,600,350)).resize((800,440), Image.NEAREST)
    N = Image.open(rf"{_VD}/new_{tag}.png").crop((200,130,600,350)).resize((800,440), Image.NEAREST)
    out = Image.new("RGB",(800,920),(255,255,255))
    out.paste(B,(0,20)); out.paste(N,(0,480))
    d = ImageDraw.Draw(out)
    d.text((6,2), "BEFORE: pure python FS", fill=(0,0,0))
    d.text((6,462), "AFTER: PIL quantize FS", fill=(0,0,0))
    out.save(rf"{_VD}/compare_{tag}.png")
    print("saved compare")
