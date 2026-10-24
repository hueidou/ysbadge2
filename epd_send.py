# -*- coding: utf-8 -*-
"""Faithful e-ink transmitter for com.app.myapplication / YSBadge2.
Sources: EPD_Config.getPicData_NColor_4bit, BMPConverter.thresholding/floydSteinbergDither,
         LZ77Compress.Compress, BluetoothTool BLE flow.
"""
import sys, time, argparse
from bisect import bisect_left

W, H = 800, 480
MAX_PAYLOAD_BITS = 262144   # 实测上限：超过则设备静默丢弃整张（约 32KB）
PALETTE = [(0,0,0),(255,255,255),(0,255,0),(0,0,255),(255,0,0),(255,255,0),(255,128,0)]

CH_WRITE_CMD = "0000ff03-0000-1000-8000-00805f9b34fb"
CH_WRITE_PIC = "0000ff02-0000-1000-8000-00805f9b34fb"
CH_NOTIFY    = "0000ff04-0000-1000-8000-00805f9b34fb"

def palette_image():
    """PIL 量化用的 7 色调色板；索引顺序即线上格式，不能改。"""
    from PIL import Image
    p = Image.new("P", (1, 1))
    flat = [c for rgb in PALETTE for c in rgb]
    flat += [0] * (768 - len(flat))
    p.putpalette(flat)
    return p

def pack_indexed(idx):
    """P 模式索引字节(每像素 1 字节) -> 4bit/像素线上格式。"""
    assert len(idx) == W * H, len(idx)
    return bytes(map(lambda hi, lo: (hi << 4) | (lo & 0x0F), idx[0::2], idx[1::2]))

def nearest(px):
    r, g, b = px[0], px[1], px[2]
    best = 1 << 30
    bi = 0
    for i in range(len(PALETTE)):
        pr, pg, pb = PALETTE[i]
        d = (r-pr)*(r-pr) + (g-pg)*(g-pg) + (b-pb)*(b-pb)
        if d < best:
            best = d
            bi = i
    return bi

def build_canvas(path, fill, stretch=False):
    from PIL import Image, ImageOps
    with Image.open(path) as src:
        im = ImageOps.exif_transpose(src)      # 手机竖拍靠 EXIF 标记方向，不转就会躺倒
        if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
            rgba = im.convert("RGBA")          # 透明区必须铺白，convert("RGB") 会变黑
            bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            im = Image.alpha_composite(bg, rgba)
        im = im.convert("RGB")
    sw, sh = im.size
    if stretch:
        canvas = im.resize((W, H), Image.LANCZOS)
        return canvas, (sw, sh)
    if fill:
        scale = max(W / sw, H / sh)
        nw, nh = int(sw*scale + 0.5), int(sh*scale + 0.5)
        im2 = im.resize((nw, nh), Image.LANCZOS)
        left = (nw - W) // 2
        top = (nh - H) // 2
        canvas = im2.crop((left, top, left+W, top+H))
    else:
        scale = min(W / sw, H / sh)
        nw, nh = max(1, int(sw*scale)), max(1, int(sh*scale))
        im2 = im.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGB", (W, H), (255, 255, 255))
        canvas.paste(im2, ((W-nw)//2, (H-nh)//2))
    return canvas, (sw, sh)

BAYER8 = [
 [ 0,32, 8,40, 2,34,10,42],
 [48,16,56,24,50,18,58,26],
 [12,44, 4,36,14,46, 6,38],
 [60,28,52,20,62,30,54,22],
 [ 3,35,11,43, 1,33, 9,41],
 [51,19,59,27,49,17,57,25],
 [15,47, 7,39,13,45, 5,37],
 [63,31,55,23,61,29,53,21],
]

def encode_image(path, dither, fill, flip=False, invert=False, ordered=False, spread=128, sat=1.0, contrast=1.0, bright=1.0, noise=0, seed=1, sharp=1.0, stretch=False):
    canvas, info = build_canvas(path, fill, stretch)
    from PIL import ImageEnhance
    if sat != 1.0:
        canvas = ImageEnhance.Color(canvas).enhance(sat)
    if contrast != 1.0:
        canvas = ImageEnhance.Contrast(canvas).enhance(contrast)
    if bright != 1.0:
        canvas = ImageEnhance.Brightness(canvas).enhance(bright)
    if sharp != 1.0:
        canvas = ImageEnhance.Sharpness(canvas).enhance(sharp)
    if invert:
        from PIL import ImageOps
        canvas = ImageOps.invert(canvas)
    if flip:
        canvas = canvas.rotate(180)
    px = canvas.load()
    if ordered:
        out = bytearray((W*H)//2)
        k = 0
        for y in range(H):
            for x in range(0, W, 2):
                def q(xx):
                    t = ((BAYER8[y & 7][xx & 7] + 0.5) / 64.0 - 0.5) * spread
                    r = px[xx, y][0] + t; g = px[xx, y][1] + t; b = px[xx, y][2] + t
                    r = 0 if r < 0 else (255 if r > 255 else r)
                    g = 0 if g < 0 else (255 if g > 255 else g)
                    b = 0 if b < 0 else (255 if b > 255 else b)
                    return nearest((r, g, b))
                out[k] = (q(x) << 4) | (q(x+1) & 0x0F)
                k += 1
    elif dither:
        # 交给她 PIL 的 C 实现做 Floyd–Steinberg：误差在 7 色调色板上扩散，
        # 语义与 APK 的 BMPConverter.floydSteinbergDither 一致，但无 Python 逐像素循环。
        from PIL import Image as _Image
        q = canvas.quantize(palette=palette_image(), dither=_Image.Dither.FLOYDSTEINBERG)
        out = pack_indexed(q.tobytes())
    else:
        import random
        rng = random.Random(seed)
        A = int(noise)
        def q(xx, yy):
            c = px[xx, yy]
            r = c[0]; g = c[1]; b = c[2]
            if A:
                r += rng.randint(-A, A); g += rng.randint(-A, A); b += rng.randint(-A, A)
                r = 0 if r < 0 else (255 if r > 255 else r)
                g = 0 if g < 0 else (255 if g > 255 else g)
                b = 0 if b < 0 else (255 if b > 255 else b)
            return nearest((r, g, b))
        out = bytearray((W*H)//2)
        k = 0
        for y in range(H):
            for x in range(0, W, 2):
                out[k] = (q(x, y) << 4) | (q(x+1, y) & 0x0F)
                k += 1
    return bytes(out), info

MAX_WND = 1024

def compress(data):
    """LZ77（窗口 1024，偏移 10bit，长度 Golomb m=3）。

    与旧实现逐字节一致的输出，但用 2 字节前缀索引只考察首两字节相同的位置
    （长度为 1 的匹配不会被编码），并按距离递增顺序保持原有的平局规则。
    """
    n = len(data)
    out = bytearray(n * 2)
    bitpos = 0
    i = 0
    buckets = {}

    def w0(bp):
        out[bp >> 3] &= (0xFF ^ (1 << (7 & bp)))

    def remember(pos):
        if pos + 1 >= n:
            return
        key = (data[pos] << 8) | data[pos + 1]
        bucket = buckets.get(key)
        if bucket is None:
            buckets[key] = [pos]
        else:
            bucket.append(pos)
            if len(bucket) > 128:
                del bucket[:bisect_left(bucket, pos - MAX_WND)]

    while i < n:
        rel = i - MAX_WND
        if rel >= 0:
            win_start, maxlen = rel, MAX_WND
        elif rel >= -MAX_WND:
            win_start, maxlen = 0, MAX_WND + rel
        else:
            win_start, maxlen = -1, 0
        if maxlen > n - i:
            maxlen = n - i

        length = 0
        offset = 0
        best = 0
        if win_start >= 0 and i + 1 < n:
            bucket = buckets.get((data[i] << 8) | data[i + 1])
            if bucket:
                limit = win_start + maxlen          # 第 k 个候选的上限 cap = limit - p
                for p in bucket[bisect_left(bucket, win_start):]:
                    if p >= limit:
                        break
                    cap = limit - p
                    if cap <= best:
                        break
                    probe = best + 1                # 想赢必须超过 best
                    if data[p:p + probe] != data[i:i + probe]:
                        continue
                    lo, hi = probe, cap
                    while lo < hi:
                        mid = (lo + hi + 1) >> 1
                        if data[p:p + mid] == data[i:i + mid]:
                            lo = mid
                        else:
                            hi = mid - 1
                    best = lo
                    offset = p - win_start
                    if best == cap:
                        break

        if best > 1:
            out[bitpos >> 3] |= (1 << (7 & bitpos)); bitpos += 1
            for b in range(10):
                if (offset >> b) & 1:
                    out[bitpos >> 3] |= (1 << (7 & bitpos))
                else:
                    w0(bitpos)
                bitpos += 1
            x = best
            q = (x - 1) >> 3
            r = (x - (q << 3)) - 1
            for _ in range(q):
                out[bitpos >> 3] |= (1 << (7 & bitpos)); bitpos += 1
            w0(bitpos); bitpos += 1
            for b in range(3):
                if (r >> b) & 1:
                    out[bitpos >> 3] |= (1 << (7 & bitpos))
                else:
                    w0(bitpos)
                bitpos += 1
            for pos in range(i, i + best):
                remember(pos)
            i += best
        else:
            w0(bitpos); bitpos += 1
            c = data[i]
            for b in range(8):
                if (c >> b) & 1:
                    out[bitpos >> 3] |= (1 << (7 & bitpos))
                else:
                    w0(bitpos)
                bitpos += 1
            remember(i)
            i += 1

    total_bits = bitpos
    nbytes = (total_bits + 7) >> 3
    return bytes(out[:nbytes]), total_bits

def decompress(buf, total_bits):
    def bit(bp):
        return (buf[bp >> 3] >> (7 & bp)) & 1
    out = bytearray()
    bp = 0
    while bp < total_bits:
        if bit(bp):
            bp += 1
            off = 0
            for b in range(10):
                if bit(bp):
                    off |= (1 << b)
                bp += 1
            q = 0
            while bit(bp) == 1:
                q += 1
                bp += 1
            bp += 1
            r = 0
            for b in range(3):
                if bit(bp):
                    r |= (1 << b)
                bp += 1
            length = (q << 3) + r + 1
            cur = len(out)
            ws = max(0, cur - MAX_WND)
            src = ws + off
            for t in range(length):
                out.append(out[src+t])
        else:
            bp += 1
            c = 0
            for b in range(8):
                if bit(bp):
                    c |= (1 << b)
                bp += 1
            out.append(c)
    return bytes(out)

def selftest():
    import random
    cases = [b"", b"A", b"AAAA", b"ABABABABAB", bytes(range(64)),
             bytes([random.randrange(16) for _ in range(300)]),
             bytes([random.randrange(4) for _ in range(1000)])]
    for d in cases:
        c, bits = compress(d)
        r = decompress(c, bits)
        if r != d:
            raise SystemExit("LZ77 MISMATCH len=%d comp=%d restored=%d" % (len(d), len(c), len(r)))
    print("[selftest] LZ77 round-trip OK on %d cases" % len(cases))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--addr", default="EE:96:BB:1E:05:28")
    ap.add_argument("--index", type=int, default=1, help="epd_index: 1=A, 2=B, 3=A&B same, 7=A&B diff")
    ap.add_argument("--dither", action="store_true")
    ap.add_argument("--ordered", action="store_true")
    ap.add_argument("--spread", type=int, default=128)
    ap.add_argument("--sat", type=float, default=1.0)
    ap.add_argument("--contrast", type=float, default=1.0)
    ap.add_argument("--bright", type=float, default=1.0)
    ap.add_argument("--noise", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--sharp", type=float, default=1.0)
    ap.add_argument("--fill", action="store_true")
    ap.add_argument("--stretch", action="store_true")
    ap.add_argument("--flip", action="store_true")
    ap.add_argument("--invert", action="store_true")
    ap.add_argument("--image2", default=None, help="side-B image; enables index=7 combine")
    ap.add_argument("--dither2", action="store_true")
    ap.add_argument("--fill2", action="store_true")
    ap.add_argument("--flip2", action="store_true")
    ap.add_argument("--invert2", action="store_true")
    ap.add_argument("--update", action="store_true", help="send UPDATE(0x03) after data")
    ap.add_argument("--no-compress", action="store_true",
                    help="EXPERIMENTAL compress_type=0 raw 192000B; this unit's firmware does not "
                         "refresh and may wedge GATT (see docs/LESSONS.md section 1)")
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    selftest()
    t0 = time.time()
    if a.image2:
        rawA, infoA = encode_image(a.image, a.dither, a.fill)
        rawB, infoB = encode_image(a.image2, a.dither2, a.fill2, a.flip2, a.invert2)
        raw = rawA + rawB
        idx = 7
        print("index 7 (A&B diff): A=%dx%d(dither=%s,fill=%s)  B=%dx%d(dither=%s,fill=%s)" % (
              infoA[0], infoA[1], a.dither, a.fill, infoB[0], infoB[1], a.dither2, a.fill2))
    else:
        raw, info = encode_image(a.image, a.dither, a.fill, a.flip, a.invert, a.ordered, a.spread, a.sat, a.contrast, a.bright, a.noise, a.seed, a.sharp, a.stretch)
        idx = a.index
        print("index %d dither=%s fill=%s ; image %dx%d -> 800x480" % (idx, a.dither, a.fill, info[0], info[1]))
    print("pic_data %d bytes" % len(raw))
    over = False
    if a.no_compress:
        payload = raw
        ctype = 0
        decl = len(payload)      # 未压缩：PIC_INFO len = 原始字节数（PROTOCOL.md §2）
        print("compress_type=0 (raw 192000B) - 本机固件实测不刷新，仅作实验")
    else:
        payload, bits = compress(raw)
        ctype = 1
        decl = bits              # 压缩：PIC_INFO len = 压缩后比特数（PROTOCOL.md §2，2026-10-21 实机确认）
        over = bits > MAX_PAYLOAD_BITS
        print("compressed %d bytes, %d bits (%.1f%% of raw, 上限 %d)%s" % (
              len(payload), bits, 100.0*bits/8/len(raw), MAX_PAYLOAD_BITS,
              "  <== 超限，设备会静默丢弃" if over else ""))
        rt = decompress(payload, bits)
        print("round-trip restore == raw:", rt == raw)
    print("encode+verify %.1fs" % (time.time()-t0))
    if a.offline:
        sys.exit(0)
    if over:
        print("拒绝发送：压缩后 %d bit 超过设备上限 %d bit（约 32KB）。" % (bits, MAX_PAYLOAD_BITS), file=sys.stderr)
        print("可选做法：去掉 --dither；减小画面细节（避免细密纹理/噪点）；换更简洁的图。", file=sys.stderr)
        sys.exit(2)
    import asyncio
    from bleak import BleakClient
    init = bytes([0x00, 0x06, idx])
    info_cmd = bytes([0x01, ctype]) + decl.to_bytes(4, "little")
    print("PIC_INFO len = %d（%s）" % (decl, "压缩后比特数" if ctype == 1 else "原始字节数"))
    print("screen index", idx, " INIT", init.hex(" "), " PIC_INFO", info_cmd.hex(" "))
    notes = []
    def on_notify(_, data):
        notes.append(bytes(data)); print("[notify]", bytes(data).hex(" "))
    async def run():
        async with BleakClient(a.addr, timeout=20) as cl:
            print("connected:", cl.is_connected, "mtu:", cl.mtu_size)
            await cl.start_notify(CH_NOTIFY, on_notify)
            await asyncio.sleep(0.3)
            await cl.write_gatt_char(CH_WRITE_CMD, init, response=False)
            await asyncio.sleep(0.3)
            await cl.write_gatt_char(CH_WRITE_CMD, info_cmd, response=False)
            await asyncio.sleep(0.6)
            chunk = max(20, cl.mtu_size - 3)
            total = (len(payload) + chunk - 1) // chunk
            print("sending %d chunks x %d bytes (%.1fs est) ..." % (total, chunk, total*0.04))
            for idx in range(total):
                await cl.write_gatt_char(CH_WRITE_PIC, payload[idx*chunk:(idx+1)*chunk], response=False)
                await asyncio.sleep(0.04)
                if (idx+1) % 50 == 0:
                    print("  %d/%d" % (idx+1, total))
            if a.update:
                await asyncio.sleep(0.4)
                print("--> UPDATE (03 00)")
                await cl.write_gatt_char(CH_WRITE_CMD, bytes([0x03, 0x00]), response=False)
                await asyncio.sleep(0.5)
            print("data sent; waiting 1.5s ...")
            await asyncio.sleep(1.5)
            try:
                await cl.stop_notify(CH_NOTIFY)
            except Exception:
                pass
        print("done. notifications:", len(notes))
    asyncio.run(run())
