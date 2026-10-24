
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
from PIL import Image, ImageDraw, ImageFont
PAL=[(0,0,0),(255,255,255),(0,255,0),(0,0,255),(255,0,0),(255,255,0),(255,128,0)]
im=Image.new("RGB",(800,480),(255,255,255)); d=ImageDraw.Draw(im)
# 顶部 7 色竖条，每色索引编号
for i,c in enumerate(PAL):
    x0=i*800//7; x1=(i+1)*800//7
    d.rectangle((x0,0,x1,150),fill=c)
    d.text((x0+18,60),str(i),fill=(0,0,0) if i!=0 else (255,255,255))
# 下半部：黑白棋盘 + 细线 + 文字
for y in range(160,480,20):
    for x in range(0,400,20):
        if ((x//20)+(y//20))%2==0: d.rectangle((x,y,x+19,y+19),fill=(0,0,0))
d.rectangle((400,160,799,479),outline=(0,0,0),width=4)
for i in range(10):
    d.line((410,180+i*9,790,180+i*9),fill=(0,0,0),width=1)
f=None
for p in ("C:/Windows/Fonts/msyh.ttc","C:/Windows/Fonts/simhei.ttf"):
    try:
        f=ImageFont.truetype(p,44); break
    except Exception: pass
d.text((415,380),"COMPRESS_TYPE=0",font=f,fill=(0,0,0))
d.text((415,430),"未压缩 192000B",font=f,fill=(0,0,0))
im.save("test_pattern.png")
print("ok")
