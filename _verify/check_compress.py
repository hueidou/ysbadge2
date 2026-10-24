# -*- coding: utf-8 -*-
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import sys, random, time
sys.path.insert(0, _ROOT)
sys.path.insert(0, _VD)
import epd_send as E
from old_compress import old_compress

def rnd(n, k, seed=1):
    r = random.Random(seed)
    return bytes(r.randrange(k) for _ in range(n))

cases = {
    "empty": b"",
    "one": b"A",
    "run": b"AAAA",
    "abab": b"ABABABABAB",
    "range64": bytes(range(64)),
    "rnd16_100": rnd(100, 16),
    "rnd16_1000": rnd(1000, 16),
    "rnd16_5000": rnd(5000, 16),
    "rnd4_20000": rnd(20000, 4),
    "zeros_3000": bytes(3000),
    "period3_5000": (b"ABC" * 1667)[:5000],
    "zeros_192k": bytes(192000),
}
# 真实数据
for name, args in (("test_pattern", ("_verify/test_pattern.png", False, False)),
                   ("marker", ("_verify/marker.png", False, False)),
                   ("photo", ("P20261021-191121.jpg", True, False))):
    raw, _ = E.encode_image(_ROOT + r"/" + args[0], args[1], args[2])
    cases["raw_" + name] = raw

ok = True
for name, data in cases.items():
    tc, tb = old_compress(data)
    nc, nb = E.compress(data)
    same = (tc == nc and tb == nb)
    ok &= same
    rt = E.decompress(nc, nb)
    print(f"{name:16} n={len(data):7d} 旧={len(tc):6d}B/{tb:8d}bit 新={len(nc):6d}B/{nb:8d}bit 一致={same} 自解压={rt == data}")
print("ALL IDENTICAL" if ok else "!!! MISMATCH")

# 计时
data = cases["raw_photo"]
t = time.time(); old_compress(data); t_old = time.time() - t
t = time.time(); E.compress(data); t_new = time.time() - t
print(f"计时(照片 raw): 旧 {t_old:.2f}s -> 新 {t_new:.2f}s  (x{t_old/t_new:.1f})")
