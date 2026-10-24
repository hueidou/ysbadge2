import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import sys, time
sys.path.insert(0, _ROOT)
import epd_send as E
t=time.time(); raw,_=E.encode_image(_ROOT + r"/P20261021-191121.jpg", True, False); t1=time.time()-t
t=time.time(); comp,bits=E.compress(raw); t2=time.time()-t
t=time.time(); E.decompress(comp,bits); t3=time.time()-t
print(f"encode(dither) {t1:.2f}s | compress {t2:.2f}s | decompress {t3:.2f}s | total {t1+t2:.2f}s")
