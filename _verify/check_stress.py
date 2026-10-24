import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import sys, random, time
sys.path.insert(0, _ROOT); sys.path.insert(0, _VD)
import epd_send as E
from old_compress import old_compress
import epd_send
r = random.Random(3)
cases = {
  "2符号192k": bytes(r.randrange(2) for _ in range(192000)),
  "AB交替192k": (b"\x11\x22" * 96000),
  "全同192k": bytes([0x11])*192000,
  "渐变量化": None,
}
_NP = _VD + "/noise.png"
if not _os.path.exists(_NP):
    from PIL import Image as _Img
    import random as _rnd
    _n = _Img.new("RGB", (800, 480))
    _n.putdata([(_rnd.randrange(256), _rnd.randrange(256), _rnd.randrange(256)) for _ in range(800 * 480)])
    _n.save(_NP)
noise, _ = E.encode_image(_NP, False, False)
cases["噪点图"] = noise
for k, v in list(cases.items()):
    if v is None: del cases[k]
for k, d in cases.items():
    t=time.time(); c1,b1 = old_compress(d); to=time.time()-t
    t=time.time(); c2,b2 = E.compress(d); tn=time.time()-t
    print(f"{k:12} 一致={c1==c2 and b1==b2} 旧={to:6.2f}s 新={tn:6.3f}s bits={b2}")
