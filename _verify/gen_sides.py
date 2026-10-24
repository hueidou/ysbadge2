# -*- coding: utf-8 -*-
"""生成双面异显测试图：A 面红底条 + 大字 A，B 面蓝底条 + 大字 B。"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
from PIL import Image, ImageDraw, ImageFont

OUT = _VD
F = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 200)

def make(path, color, ch):
    im = Image.new("RGB", (800, 480), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 799, 90), fill=color)                 # 顶部色条
    d.text((300, 150), ch, font=F, fill=(0, 0, 0))           # 大字
    im.save(path)
    print(path, im.size)

make(OUT + "/sideA.png", (255, 0, 0), "A")
make(OUT + "/sideB.png", (0, 0, 255), "B")
