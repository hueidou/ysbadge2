# -*- coding: utf-8 -*-
"""gen_weather.py — 生成「北京今日天气」800x480 上屏卡片（屏幕 B 面用）。

设计约束（docs/IMAGE_PROCESSING.md）：
  - 800x480 固定画布；大字、扁平色块、无渐变、无抖动（nearest 量化无损 -> 压缩体积小）
  - 只用 7 色调色板内的颜色：黑(0,0,0) 白(255,255,255) 绿(0,255,0) 蓝(0,0,255)
    红(255,0,0) 黄(255,255,0) 橙(255,128,0)，量化前后一致
  - 最小字号 30px（小字在 4bit 墨水屏上会糊）

数据（2026-10-23 抓取，三个源互相印证）：
  - 中国天气网 weather.com.cn：今天 多云转晴，白天 17°C / 夜间晴 9°C，西南风 <3 级
  - 墨迹天气：2026-10-23 多云转晴 17/9°C，湿度 63%，南风转北风 2 级，AQI 74
  - 华风爱科：多云转晴 9°/17°，南风 1 级，AQI 74 良
  穿衣提示（中国天气网）：建议着厚外套加毛衣

    python _verify/gen_weather.py            # 生成 _verify/weather_bj_20261023.png
"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, '_verify', 'weather_bj_20261023.png')
FDIR = 'C:/Windows/Fonts'

# 7 色调色板（索引即线上 4bit 码）
BLACK, WHITE, GREEN, BLUE, RED, YELLOW, ORANGE = (
    (0, 0, 0), (255, 255, 255), (0, 255, 0), (0, 0, 255), (255, 0, 0), (255, 255, 0), (255, 128, 0))
PAL = [BLACK, WHITE, GREEN, BLUE, RED, YELLOW, ORANGE]
W, H = 800, 480


def font(name, size):
    return ImageFont.truetype(os.path.join(FDIR, name), size)


def ctext(d, xy, s, f, fill, anchor='mm'):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def sun_cloud(d, cx, cy):
    # 太阳（黄圆 + 橙射线），先画让云压在前面
    sx, sy, sr = cx + 78, cy - 52, 40
    for k in range(8):
        a = math.radians(k * 45)
        d.line([(sx + math.cos(a) * (sr + 8), sy + math.sin(a) * (sr + 8)),
                (sx + math.cos(a) * (sr + 24), sy + math.sin(a) * (sr + 24))], fill=ORANGE, width=10)
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=YELLOW)
    # 云：黑底圆组 + 白底圆组（内缩 7px 形成均匀描边）
    blobs = [(cx - 52, cy + 8, 46), (cx + 2, cy - 12, 55), (cx + 52, cy + 12, 43), (cx - 2, cy + 26, 50)]
    for bx, by, br in blobs:
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=BLACK)
    for bx, by, br in blobs:
        d.ellipse([bx - br + 7, by - br + 7, bx + br - 7, by + br - 7], fill=WHITE)


def chip(d, x, y, w, h, color, label, value):
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=WHITE, outline=BLACK, width=3)
    d.rounded_rectangle([x + 9, y + 11, x + 16, y + h - 11], radius=3, fill=color)
    d.text((x + 28, y + h // 2), label + ' ' + value, font=font('msyhbd.ttc', 36),
           fill=BLACK, anchor='lm')


def main():
    img = Image.new('RGB', (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # 顶部：蓝色标题带 + 橙色饰条
    d.rectangle([0, 0, W, 64], fill=BLUE)
    d.rectangle([0, 64, W, 70], fill=ORANGE)
    ctext(d, (28, 32), '北 京', font('msyhbd.ttc', 44), WHITE, anchor='lm')
    ctext(d, (W - 28, 32), '10月23日 · 周五', font('msyhbd.ttc', 36), WHITE, anchor='rm')

    # 左：天气图标 + 状况
    sun_cloud(d, 168, 204)
    ctext(d, (168, 316), '多云转晴', font('msyhbd.ttc', 62), BLACK)

    # 右：大温度 + 高低温
    ctext(d, (352, 168), '17', font('msyhbd.ttc', 210), BLACK, anchor='lm')
    f210 = font('msyhbd.ttc', 210)
    ctext(d, (352 + d.textlength('17', font=f210) + 14, 96), '°', font('seguisb.ttf', 110),
          ORANGE, anchor='lm')
    f44 = font('msyhbd.ttc', 44)
    ctext(d, (368, 292), '最高 17°', f44, RED, anchor='lm')
    ctext(d, (368 + d.textlength('最高 17°', font=f44) + 40, 292), '最低 9°', f44, BLUE, anchor='lm')

    # 信息 chips：湿度 / 风 / 空气
    cw, gap = 224, 22
    x0 = (W - (cw * 3 + gap * 2)) // 2
    chip(d, x0, 366, cw, 66, BLUE, '湿度', '63%')
    chip(d, x0 + cw + gap, 366, cw, 66, GREEN, '南风', '2级')
    chip(d, x0 + (cw + gap) * 2, 366, cw, 66, ORANGE, '空气', '良')

    # 底部友好提示
    ctext(d, (W // 2, 462), '多云转晴 · 早晚凉，注意添衣', font('msyh.ttc', 34), BLACK)

    img.save(OUT)
    print('saved %s (%dx%d)' % (OUT, W, H))

    # 自检：按 7 色 nearest 量化 -> 打包 -> 压缩，确认体积在上限内
    sys.path.insert(0, ROOT)
    from epd_send import compress, MAX_PAYLOAD_BITS
    px = img.load()
    idx = []
    for y in range(H):
        for x in range(W):
            p = px[x, y]
            best, bd = 0, 1 << 30
            for i, c in enumerate(PAL):
                dd = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2
                if dd < bd:
                    bd, best = dd, i
            idx.append(best)
    raw = bytearray(len(idx) // 2)
    for i in range(0, len(idx), 2):
        raw[i // 2] = (idx[i] << 4) | idx[i + 1]
    payload, bits = compress(bytes(raw))
    print('pic_data %d B -> 压缩后 %d B / %d bit（%.1f%% 上限 %d）%s'
          % (len(raw), len(payload), bits, 100.0 * bits / MAX_PAYLOAD_BITS, MAX_PAYLOAD_BITS,
             'OK' if bits <= MAX_PAYLOAD_BITS else '超限！'))
    hist = {}
    for i in idx:
        hist[i] = hist.get(i, 0) + 1
    names = ['黑', '白', '绿', '蓝', '红', '黄', '橙']
    print('色分布: ' + '  '.join('%s %.1f%%' % (names[i], 100.0 * hist.get(i, 0) / len(idx))
                                for i in range(7) if hist.get(i)))


if __name__ == '__main__':
    main()