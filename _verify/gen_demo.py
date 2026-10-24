# -*- coding: utf-8 -*-
"""生成两张体现屏幕特点的演示图，用 _verify/send_probe.py 以 index 7 双面异显发送。

设计依据 docs/IMAGE_PROCESSING.md：
  §2  按内容选抖动（纯色块+大字 -> 关抖动）
  §6  设计期约束：只用 7 原色+白底、禁渐变/阴影/半透明/1px 细灰线、对比度拉满、字号宁大勿小
  §9  姓名标签版式：白底圆角块 + 黑字 + 左侧橙色竖条

A 面 = 7 色能力图（含文字对比度与"限制演示"区）
B 面 = 姓名标签实例（Jack Wang，取自 ff04 读口返回的固件字符串）
"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
from PIL import Image, ImageDraw, ImageFont

OUT = _VD
PAL = [(0,0,0),(255,255,255),(0,255,0),(0,0,255),(255,0,0),(255,255,0),(255,128,0)]
NAMES = ["黑","白","绿","蓝","红","黄","橙"]
# 每种底色上的可读文字色（对比度拉满）
ON = [(255,255,255),(0,0,0),(0,0,0),(255,255,255),(255,255,255),(0,0,0),(0,0,0)]
F = lambda sz, b=True: ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", sz)

# ============ A 面：7 色能力图 ============
def make_capability():
    im = Image.new("RGB", (800, 480), (255, 255, 255))
    d = ImageDraw.Draw(im)
    # 标题条
    d.rectangle((0, 0, 799, 54), fill=(0, 0, 0))
    d.text((18, 10), "YSBadge2 · 7 色 4bit 能力图", font=F(30), fill=(255, 255, 255))
    d.text((640, 16), "800×480 · 4bit/px", font=F(16), fill=(0, 255, 0))
    # 7 个色块：索引 + 色名
    w = 800 // 7
    for i in range(7):
        x0, x1 = i * w, (i + 1) * w - 1
        d.rectangle((x0, 66, x1, 176), fill=PAL[i])
        d.rectangle((x0, 66, x1, 176), outline=(0, 0, 0), width=1)
        d.text((x0 + 8, 78), "idx %d" % i, font=F(18), fill=ON[i])
        d.text((x0 + w // 2 - 26, 116), NAMES[i], font=F(40), fill=ON[i])
        d.text((x0 + 8, 150), "%s" % ("#%02X%02X%02X" % PAL[i]), font=F(13), fill=ON[i])
    # 文字对比度区：每种底色上放一个大字
    d.rectangle((0, 190, 799, 282), fill=(255, 255, 255))
    d.text((18, 194), "文字对比度（每色底上的反色大字）", font=F(16), fill=(0, 0, 0))
    for i in range(7):
        x0, x1 = i * w, (i + 1) * w - 1
        d.rectangle((x0, 220, x1, 278), fill=PAL[i])
        d.text((x0 + w // 2 - 24, 226), NAMES[i], font=F(40), fill=ON[i])
    # 限制演示区
    d.rectangle((0, 296, 799, 480), fill=(255, 255, 255))
    d.line((0, 296, 799, 296), fill=(0, 0, 0), width=2)
    d.text((18, 302), "限制演示（这些是屏幕的物理极限，别这么画）", font=F(16), fill=(255, 0, 0))
    # 1) 渐变：会分层
    gx, gy, gw, gh = 18, 330, 300, 46
    for x in range(gw):
        v = int(255 * x / (gw - 1))
        d.line((gx + x, gy, gx + x, gy + gh), fill=(v, v, v))
    d.text((gx, gy + gh + 4), "渐变 → 量化后成色带", font=F(13), fill=(0, 0, 0))
    # 2) 细灰线：会断
    lx, ly = 340, 330
    for k, wd in enumerate((1, 2, 3)):
        for r in range(6):
            d.line((lx + k * 40, ly + r * 8, lx + k * 40 + 30, ly + r * 8),
                   fill=(128, 128, 128), width=wd)
    d.text((lx, ly + 52), "1/2/3px 细灰线 → 断裂", font=F(13), fill=(0, 0, 0))
    # 3) 小字：会糊
    d.text((560, 328), "小字 12px：墨色屏有物理极限", font=F(12), fill=(0, 0, 0))
    d.text((560, 348), "大字 30px：清晰可读", font=F(30), fill=(0, 0, 0))
    d.text((560, 392), "→ 字号宁大勿小", font=F(15), fill=(255, 128, 0))
    # 底部 7 色条
    d.rectangle((0, 462, 799, 480), fill=(0, 0, 0))
    for i in range(7):
        d.rectangle((i * w, 464, (i + 1) * w - 1, 478), fill=PAL[i])
    p = OUT + "/demo_capability.png"
    im.save(p)
    print(p)

# ============ B 面：姓名标签实例 ============
def make_nametag():
    im = Image.new("RGB", (800, 480), (255, 255, 255))
    d = ImageDraw.Draw(im)
    # 顶部细黑线 + 左上角Logo 位
    d.rectangle((0, 0, 799, 6), fill=(0, 0, 0))
    # 姓名块：白底圆角块 + 左侧橙色竖条 + 黑字（IMAGE_PROCESSING.md §9）
    d.rounded_rectangle((30, 44, 470, 190), radius=10, fill=(255, 255, 255), outline=(0, 0, 0), width=2)
    d.rectangle((30, 44, 46, 190), fill=(255, 128, 0))          # 橙色竖条
    d.text((64, 58), "Jack Wang", font=F(52), fill=(0, 0, 0))
    d.text((66, 128), "固件工程师 · YSBadge2", font=F(24), fill=(0, 0, 0))
    # 右侧：一块蓝色信息卡
    d.rounded_rectangle((500, 44, 770, 190), radius=10, fill=(0, 0, 255))
    d.text((520, 58), "BLE 投图台", font=F(26), fill=(255, 255, 255))
    d.text((520, 100), "MAC EE:96:BB", font=F(20), fill=(255, 255, 255))
    d.text((520, 132), "双面 · 7 色 · 800×480", font=F(18), fill=(255, 255, 0))
    # 三枚信息 chip
    chips = [("双面异显", (0, 255, 0), (0, 0, 0)), ("7 色调色板", (255, 255, 0), (0, 0, 0)),
             ("LZ77 压缩", (255, 0, 0), (255, 255, 255))]
    for i, (t, bg, fg) in enumerate(chips):
        x0 = 30 + i * 256
        d.rounded_rectangle((x0, 220, x0 + 236, 292), radius=8, fill=bg, outline=(0, 0, 0), width=2)
        d.text((x0 + 22, 240), t, font=F(30), fill=fg)
    # 中部一句大字（远看可读）
    d.text((30, 330), "桌面 1 米外可读", font=F(44), fill=(0, 0, 0))
    d.text((30, 392), "纯色块 + 高对比 + 大字号", font=F(24), fill=(0, 0, 255))
    # 底部 7 色条 + 色名
    w = 800 // 7
    for i in range(7):
        d.rectangle((i * w, 430, (i + 1) * w - 1, 470), fill=PAL[i])
        d.text((i * w + 10, 436), NAMES[i], font=F(20), fill=ON[i])
    d.rectangle((0, 474, 799, 480), fill=(0, 0, 0))
    p = OUT + "/demo_nametag.png"
    im.save(p)
    print(p)

make_capability()
make_nametag()
