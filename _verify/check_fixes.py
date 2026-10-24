# -*- coding: utf-8 -*-
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import sys, subprocess
sys.path.insert(0, _ROOT)
from PIL import Image, ImageDraw, ImageFont
import epd_send as E

OUT = _VD
f = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 90)

# 1) EXIF：造一张"相机竖拍"文件（存储时旋转 90°CCW + orientation=6）
upright = Image.new("RGB", (800, 480), (255,255,255))
d = ImageDraw.Draw(upright)
d.rectangle((0,0,799,120), fill=(255,0,0))
d.text((60,10), "TOP", font=f, fill=(0,0,0))
upright.save(OUT + "/upright.png")
stored = upright.transpose(Image.ROTATE_90)          # 90° CCW
ex = Image.Exif(); ex[274] = 6                        # Orientation: rotate 90 CW to display
stored.save(OUT + "/exif6.jpg", exif=ex, quality=98)
print("exif file size", Image.open(OUT + "/exif6.jpg").size)

a, _ = E.encode_image(OUT + "/upright.png", False, False)
b, _ = E.encode_image(OUT + "/exif6.jpg", False, False)
print("EXIF 方向修正 ->", "PASS" if a == b else "FAIL (bytes differ)")

# 2) 透明底：左半透明、右半红
rgba = Image.new("RGBA", (800, 480), (0,0,0,0))
dr = ImageDraw.Draw(rgba)
dr.rectangle((400,0,799,479), fill=(255,0,0,255))
rgba.save(OUT + "/alpha.png")
c, _ = E.encode_image(OUT + "/alpha.png", False, False)
px = lambda i: (c[(i[1]*800 + i[0])//2] >> 4) if i[0] % 2 == 0 else (c[(i[1]*800 + i[0])//2] & 15)
left, right = px((10,10)), px((700,200))
print("透明底铺白 ->", "PASS" if left == 1 and right == 4 else f"FAIL left={left}(期望1白) right={right}(期望4红)")

# 3) 体积守门：噪声图必然超限
import random
rnd = random.Random(1)
noise = Image.new("RGB", (800, 480))
noise.putdata([(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)) for _ in range(800*480)])
noise.save(OUT + "/noise.png")
r = subprocess.run([sys.executable, _ROOT + r"/epd_send.py",
                    "--image", OUT + "/noise.png", "--addr", "11:22:33:44:55:66"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print("守门 exit =", r.returncode, "(期望 2)")
print(r.stdout.strip().splitlines()[-2])
print(r.stderr.strip())
print("守门 ->", "PASS" if r.returncode == 2 and "拒绝发送" in r.stderr else "FAIL")
