# -*- coding: utf-8 -*-
"""从系统 TTF 生成 1bpp 点阵字模，供 ESP32 端（无 AA 渲染）使用。

用法：python tools/gen_font.py
产出：firmware/weather_badge/font_data.h / font_data.cpp
字符集 = ASCII + '°' + tools/charset.txt 里的字（换城市就往里补字再重跑）。
字模按墨迹 bbox 裁剪，并记录步进宽度 adv，避免窄字（1、°）挤在一起。
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "firmware", "weather_badge")

FONT_CANDIDATES = [
    "C:/Windows/Fonts/HarmonyOS_Sans_SC_Bold.ttf",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
]
SIZES = [
    (120, set("0123456789-.°")),
    (44, None),
    (32, None),
    (22, None),
]
SS = 4
THRESH = 90


def find_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    sys.exit("找不到可用的中文字体，请改 FONT_CANDIDATES")


def load_chars():
    chars = [chr(c) for c in range(0x20, 0x7F)]
    chars.append("°")
    p = os.path.join(HERE, "charset.txt")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.split("#")[0].strip()
                chars.extend(list(line))
    return sorted(set(chars))


def render_glyph(font_path, size, ch):
    """返回 (w, h, x0, y0, adv, bytes)；x0/y0 是墨迹相对单元格左上角的偏移。"""
    big = ImageFont.truetype(font_path, size * SS)
    ascent, descent = big.getmetrics()
    cell_h = ascent + descent
    adv = max(1, int(round(big.getlength(ch) / SS)))
    pad = 4
    canvas = Image.new("L", (adv * SS + pad * 2, cell_h * SS + pad * 2), 0)
    ImageDraw.Draw(canvas).text((pad, pad), ch, font=big, fill=255, anchor="la")
    bbox = canvas.getbbox()
    if bbox is None:
        return 0, 0, 0, 0, adv, b""
    crop = canvas.crop(bbox)
    w = max(1, int(round(crop.width / SS)))
    h = max(1, int(round(crop.height / SS)))
    img = crop.resize((w, h), Image.LANCZOS)
    px = img.load()
    stride = (w + 7) // 8
    buf = bytearray(stride * h)
    for y in range(h):
        for x in range(w):
            if px[x, y] >= THRESH:
                buf[y * stride + (x >> 3)] |= 0x80 >> (x & 7)
    return w, h, (bbox[0] - pad) // SS, (bbox[1] - pad) // SS, adv, bytes(buf)



def main():
    font_path = find_font()
    chars = load_chars()
    print("字体", font_path, "字符数", len(chars))
    pools, tables, line_h = [], [], []

    for size, only in SIZES:
        pool = bytearray()
        items = []
        ascent, descent = ImageFont.truetype(font_path, size).getmetrics()
        for ch in chars:
            if only is not None and ch not in only:
                continue
            w, h, x0, y0, adv, bmp = render_glyph(font_path, size, ch)
            off = pool.find(bmp) if bmp else -1
            if off < 0:
                off = len(pool)
                pool.extend(bmp)
            items.append((ord(ch), off, w, h, x0, y0, adv))
        pools.append(pool)
        tables.append(items)
        line_h.append(ascent + descent)
        print("  %2dpx: %3d 字, 池 %6d B, 行高 %d" % (size, len(items), len(pool), ascent + descent))

    with open(os.path.join(OUT, "font_data.h"), "w", encoding="utf-8", newline="\n") as f:
        f.write("// 自动生成，勿手改：tools/gen_font.py\n#pragma once\n#include <stdint.h>\n#include \"font.h\"\n\n")
        for size, _ in SIZES:
            f.write("extern const Glyph glyphs_%d[];\nextern const uint16_t glyph_count_%d;\n" % (size, size))
        f.write("extern const uint8_t font_pool[];\n")

    allpool = bytearray()
    bases = []
    for p in pools:
        bases.append(len(allpool))
        allpool.extend(p)

    with open(os.path.join(OUT, "font_data.cpp"), "w", encoding="utf-8", newline="\n") as f:
        f.write("// 自动生成，勿手改：tools/gen_font.py\n#include \"font_data.h\"\n\n")
        f.write("const uint8_t font_pool[] = {")
        f.write(",".join(str(b) for b in allpool))
        f.write("};\n\n")
        for i, (size, _) in enumerate(SIZES):
            f.write("const Glyph glyphs_%d[] = {\n" % size)
            for cp, off, w, h, x0, y0, adv in tables[i]:
                f.write("{%d,%d,%d,%d,%d,%d,%d},\n" % (cp, off + bases[i], w, h, x0, y0, adv))
            f.write("};\nconst uint16_t glyph_count_%d = %d;\n\n" % (size, len(tables[i])))
        for idx, (size, _only) in enumerate(SIZES):
            f.write("const Font font_%d = {glyphs_%d, glyph_count_%d, %d};\n"
                    % (size, size, size, line_h[idx]))

    print("合计 %d B -> %s" % (len(allpool), os.path.join(OUT, "font_data.cpp")))


if __name__ == "__main__":
    main()

