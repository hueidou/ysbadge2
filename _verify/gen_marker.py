
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
from PIL import Image, ImageDraw, ImageFont
im=Image.new("RGB",(800,480),(0,255,0)); d=ImageDraw.Draw(im)
f=None
for p in ("C:/Windows/Fonts/msyh.ttc","C:/Windows/Fonts/simhei.ttf"):
    try: f=ImageFont.truetype(p,150); break
    except Exception: pass
d.rectangle((0,0,799,479),outline=(0,0,0),width=12)
d.text((60,140),"标记图",font=f,fill=(0,0,255))
im.save("marker.png"); print("ok")
