# -*- coding: utf-8 -*-
"""交叉验证：web/ysbadge-core.js（Node 模块）vs epd_send.py，必须逐字节一致。

    python _verify/check_web_core.py

验证项：
  1. LZ77 compress：空/单字节/重复/随机/真实 192000B 图，输出字节与比特数完全一致
  2. LZ77 decompress：JS 自往返
  3. 量化+打包：同一份 RGBA（Python build_canvas 产物）下，none/ordered/noise 三种路径一致
  4. MT19937：JS 与 Python random.Random(seed).randint() 序列一致（noise 路径的 RNG 基础）
  5. JS 侧 selftest() 全通过（含纯白整屏打包 == 0x11）

FS 抖动不在断言内：PIL 与手写误差扩散的噪声图案不同（语义一致），见 docs/IMAGE_PROCESSING.md §3。
"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import sys, os, json, base64, random, subprocess, tempfile

ROOT = _ROOT
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + r"/_verify")
import epd_send as E

CORE_JS = ROOT + r"/web/ysbadge-core.js"
IMG = ROOT + r"/_verify/test_pattern.png"

RUNNER = r"""
const YSB = require(process.argv[2]);
const vec = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));
const out = { selftest: YSB.selftest(), items: {} };
for (const v of vec.items) {
  const r = {};
  try {
    if (v.kind === 'bytes') {
      const data = Uint8Array.from(Buffer.from(v.b64, 'base64'));
      const c = YSB.compress(data);
      r.comp = Buffer.from(c.bytes).toString('hex');
      r.bits = c.bits;
      const d = YSB.decompress(c.bytes, c.bits);
      r.rt = d.length === data.length && d.every((x, i) => x === data[i]);
    } else if (v.kind === 'rgba') {
      const rgba = Uint8Array.from(Buffer.from(v.b64, 'base64'));
      const idx = YSB.quantizeRGBA(rgba, { mode: v.mode, spread: v.spread, noise: v.noise, seed: v.seed });
      r.packed = Buffer.from(YSB.packIndexed(idx)).toString('hex');
    } else if (v.kind === 'mt') {
      const mt = YSB.mt19937(v.seed);
      r.mt = []; for (let i = 0; i < 12; i++) r.mt.push(mt.randint(-v.amp, v.amp));
    }
  } catch (e) { r.error = String((e && e.message) || e); }
  out.items[v.name] = r;
}
require('fs').writeFileSync(process.argv[4], JSON.stringify(out));
"""

def b64(b):
    return base64.b64encode(bytes(b)).decode()

def lz_cases():
    rnd = random.Random(20261021)
    return [b"", b"A", b"AAAA", b"ABABABABAB", bytes(range(64)),
            bytes(rnd.randrange(16) for _ in range(300)),
            bytes(rnd.randrange(4) for _ in range(1000)),
            bytes(rnd.randrange(256) for _ in range(192000)),
            bytes(rnd.randrange(16) for _ in range(192000)),
            bytes(rnd.randrange(2) for _ in range(192000)),
            bytes((i * 7 + (i >> 5)) & 0xFF for i in range(192000))]

IMG_SPECS = [("img-nearest", (False, False, False, False, False, 128, 1, 1, 1, 0, 1, 1.0, False)),
             ("img-ordered128", (False, False, False, False, True, 128, 1, 1, 1, 0, 1, 1.0, False)),
             ("img-ordered64", (False, False, False, False, True, 64, 1, 1, 1, 0, 1, 1.0, False)),
             ("img-noise16s1", (False, False, False, False, False, 128, 1, 1, 1, 16, 1, 1.0, False)),
             ("img-noise32s7", (False, False, False, False, False, 128, 1, 1, 1, 32, 7, 1.0, False))]

def build_vectors():
    items = []
    for i, c in enumerate(lz_cases()):
        items.append({"name": "lz%d" % i, "kind": "bytes", "b64": b64(c)})
    for nm, args in IMG_SPECS:
        rw, _ = E.encode_image(IMG, *args)
        items.append({"name": nm, "kind": "bytes", "b64": b64(rw)})
    # 量化+打包：喂同一份 RGBA（build_canvas 产物，转成 4 字节/像素），隔离出量化层做逐字节比对
    canvas, info = E.build_canvas(IMG, False, False)
    rgba = canvas.convert("RGBA").tobytes()
    assert len(rgba) == 800 * 480 * 4, len(rgba)
    for nm, mode, spread, noise, seed in [("q-none", "none", 128, 0, 1),
                                          ("q-ordered128", "ordered", 128, 0, 1),
                                          ("q-ordered64", "ordered", 64, 0, 1),
                                          ("q-noise16s1", "none", 128, 16, 1),
                                          ("q-noise32s7", "none", 128, 32, 7)]:
        items.append({"name": nm, "kind": "rgba", "mode": mode, "spread": spread,
                      "noise": noise, "seed": seed, "b64": b64(rgba)})
    for sd, amp in [(1, 16), (7, 32), (12345, 200), (0, 16)]:
        items.append({"name": "mt-%d-%d" % (sd, amp), "kind": "mt", "seed": sd, "amp": amp})
    return items

def expected():
    exp = {}
    for i, c in enumerate(lz_cases()):
        comp, bits = E.compress(c)
        exp["lz%d" % i] = {"comp": comp.hex(), "bits": bits}
    for nm, args in IMG_SPECS:
        rw, _ = E.encode_image(IMG, *args)
        comp, bits = E.compress(rw)
        exp[nm] = {"comp": comp.hex(), "bits": bits}
    for nm, args in [("q-none", IMG_SPECS[0][1]), ("q-ordered128", IMG_SPECS[1][1]),
                     ("q-ordered64", IMG_SPECS[2][1]), ("q-noise16s1", IMG_SPECS[3][1]),
                     ("q-noise32s7", IMG_SPECS[4][1])]:
        rw, _ = E.encode_image(IMG, *args)
        exp[nm] = {"packed": bytes(rw).hex()}
    for sd, amp in [(1, 16), (7, 32), (12345, 200), (0, 16)]:
        r = random.Random(sd)
        exp["mt-%d-%d" % (sd, amp)] = {"mt": [r.randint(-amp, amp) for _ in range(12)]}
    return exp

def main():
    items = build_vectors()
    exp = expected()
    tmp = tempfile.mkdtemp(prefix="ysbx_", dir=ROOT + r"/_verify")
    vec_p = os.path.join(tmp, "vec.json")
    out_p = os.path.join(tmp, "out.json")
    run_p = os.path.join(tmp, "run.js")
    open(vec_p, "w", encoding="utf-8").write(json.dumps({"items": items}))
    open(run_p, "w", encoding="utf-8").write(RUNNER)
    print("模块 %s，%d 个向量" % (os.path.relpath(CORE_JS, ROOT), len(items)))
    p = subprocess.run(["node", run_p, CORE_JS, vec_p, out_p], capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        print("node 运行失败 rc=%d" % p.returncode)
        print(p.stdout)
        print(p.stderr)
        return 2
    if p.stderr.strip():
        print("node stderr: " + p.stderr.strip()[:500])
    got = json.load(open(out_p, encoding="utf-8"))
    fails = []
    st = got.get("selftest") or {}
    if st.get("ok"):
        print("JS selftest ............ PASS（%d 项，含纯白 0x11 不变量）" % len(st.get("results", [])))
    else:
        fails.append("JS selftest 未全部通过: " + json.dumps(st.get("results", []), ensure_ascii=False))
    for it in items:
        nm = it["name"]
        g = (got.get("items") or {}).get(nm) or {}
        e = exp.get(nm) or {}
        if "error" in g:
            fails.append("%s: JS 异常 %s" % (nm, g["error"]))
            continue
        if it["kind"] == "bytes":
            if g.get("comp") != e["comp"]:
                fails.append("%s: 压缩字节不一致（js %d B / py %d B）" % (nm, len(g.get("comp", "")) // 2, len(e["comp"]) // 2))
            elif g.get("bits") != e["bits"]:
                fails.append("%s: 比特数不一致 js=%s py=%s" % (nm, g.get("bits"), e["bits"]))
            elif not g.get("rt"):
                fails.append("%s: JS 自往返失败" % nm)
            else:
                print("%-16s PASS  %8d bit  %7d B" % (nm, e["bits"], len(e["comp"]) // 2))
        elif it["kind"] == "rgba":
            if g.get("packed") != e["packed"]:
                d = sum(1 for x, y in zip(g.get("packed", ""), e["packed"]) if x != y)
                fails.append("%s: 量化+打包不一致（差异 %d 字符）" % (nm, d))
            else:
                print("%-16s PASS  192000 B 逐字节一致" % nm)
        elif it["kind"] == "mt":
            if g.get("mt") != e["mt"]:
                fails.append("%s: MT19937 序列不一致 js=%s py=%s" % (nm, g.get("mt"), e["mt"]))
            else:
                print("%-16s PASS  %s" % (nm, g.get("mt")))
    print("")
    if fails:
        print("==== 失败 %d 项 ====" % len(fails))
        for f in fails:
            print("  FAIL " + f)
        print("临时目录保留供排查：%s" % tmp)
        return 1
    print("==== 全部通过：%d 个向量，web/ysbadge-core.js 与 epd_send.py 逐字节一致 ====" % len(items))
    try:
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)
    except OSError:
        print("临时目录清理失败（可手动删）：%s" % tmp)
    return 0

raise SystemExit(main())
