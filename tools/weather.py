#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取北京实时天气并渲染成 800x480 七色图，再经 epd_send.py 投到 YSBadge2。

天气源：Open-Meteo（https://open-meteo.com，免 key，返回 WMO 天气编码）。
仅依赖标准库 + Pillow；投图逻辑全部复用 epd_send.py（单一协议源）。

用法：
    python tools/weather.py                 # 联网抓北京天气，投到 B 面（index 2）
    python tools/weather.py --index 1       # 投到 A 面
    python tools/weather.py --sample        # 用内置样例，不联网（无网/自检）
    python tools/weather.py --offline       # 只出图 + 打印压缩体积，不连设备
    python tools/weather.py --font C:/Windows/Fonts/msyh.ttc   # 指定中文字体

说明：本脚本只负责“出图”，投图交给 epd_send.py。实际发送需要本机有蓝牙且胸牌在附近；
沙箱/服务器无 BLE 与设备，请在带蓝牙的 PC 上运行发送。
"""
import sys, os, argparse, json, datetime, tempfile, subprocess, urllib.request, math, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

W, H = 800, 480
# 与 epd_send.PALETTE 一致的七色调色板（索引顺序即线上格式）
PAL = {
    "black": (0, 0, 0), "white": (255, 255, 255), "green": (0, 255, 0),
    "blue": (0, 0, 255), "red": (255, 0, 0), "yellow": (255, 255, 0), "orange": (255, 128, 0),
}
BEIJING = (39.9042, 116.4074)   # 北京市中心近似坐标

# WMO 天气代码 -> (中文短描述, 装饰色键)
WMO = {
    0: ("晴", "orange"), 1: ("晴间多云", "orange"), 2: ("多云", "yellow"), 3: ("阴", "blue"),
    45: ("雾", "blue"), 48: ("雾凇", "blue"),
    51: ("毛毛雨", "blue"), 53: ("毛毛雨", "blue"), 55: ("毛毛雨", "blue"),
    56: ("冻毛毛雨", "blue"), 57: ("冻毛毛雨", "blue"),
    61: ("小雨", "blue"), 63: ("中雨", "blue"), 65: ("大雨", "blue"),
    66: ("冻雨", "blue"), 67: ("冻雨", "blue"),
    71: ("小雪", "blue"), 73: ("中雪", "blue"), 75: ("大雪", "blue"), 77: ("雪粒", "blue"),
    80: ("阵雨", "blue"), 81: ("阵雨", "blue"), 82: ("强阵雨", "blue"),
    85: ("阵雪", "blue"), 86: ("阵雪", "blue"),
    95: ("雷暴", "red"), 96: ("雷暴冰雹", "red"), 99: ("雷暴冰雹", "red"),
}

# 常见中文字体候选路径（Windows / macOS / Linux）
FONTS = [
    r"C:/Windows/Fonts/msyh.ttc", r"C:/Windows/Fonts/msyh.ttf",
    r"C:/Windows/Fonts/simhei.ttf", r"C:/Windows/Fonts/simsun.ttc",
    "/System/Library/Fonts/PingFang.ttc", "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


def find_font(override=None):
    if override:
        return override
    for p in FONTS:
        if os.path.exists(p):
            return p
    return None


WEEK = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def fetch_weather():
    lat, lon = BEIJING
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
           f"&daily=weather_code,temperature_2m_max,temperature_2m_min"
           f"&timezone=Asia%2FShanghai&forecast_days=1")
    with urllib.request.urlopen(url, timeout=15) as r:
        d = json.load(r)
    cur = d["current"]; day = d["daily"]
    code = int(cur["weather_code"])
    label, tint = WMO.get(code, ("未知", "blue"))
    return {
        "temp": cur["temperature_2m"], "feels": cur["apparent_temperature"],
        "humidity": cur["relative_humidity_2m"], "wind": cur["wind_speed_10m"],
        "code": code, "label": label, "tint": tint,
        "tmax": day["temperature_2m_max"][0], "tmin": day["temperature_2m_min"][0],
        "time": cur["time"],
    }


def sample_weather():
    return {"temp": 23.0, "feels": 21.0, "humidity": 45, "wind": 12.0, "code": 2,
            "label": "多云", "tint": "yellow", "tmax": 26.0, "tmin": 15.0,
            "time": datetime.datetime.now().astimezone().isoformat()}


def temp_color(t):
    if t <= 0:   return PAL["blue"]
    if t <= 12:  return PAL["blue"]
    if t <= 22:  return PAL["green"]
    if t <= 30:  return PAL["orange"]
    return PAL["red"]


# helpers + render
BOLD_FONTS = [
    r"C:/Windows/Fonts/msyhbd.ttc", r"C:/Windows/Fonts/simhei.ttf",
    r"C:/Windows/Fonts/msyh.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


def _sun(d, cx, cy, r):
    for k in range(12):
        a = math.radians(k * 30)
        d.line([(cx + math.cos(a) * (r + 6), cy + math.sin(a) * (r + 6)),
                (cx + math.cos(a) * (r + 22), cy + math.sin(a) * (r + 22))],
               fill=PAL["orange"], width=8)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PAL["yellow"], outline=PAL["black"], width=4)


def _cloud(d, cx, cy, s=1.0, fill=PAL["white"], outline=PAL["black"]):
    blobs = [(-54, 8, 46), (2, -14, 56), (54, 12, 44), (-2, 28, 52)]
    blobs = [(cx + bx * s, cy + by * s, br * s) for bx, by, br in blobs]
    for bx, by, br in blobs:
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=outline)
    for bx, by, br in blobs:
        d.ellipse([bx - br + 7 * s, by - br + 7 * s, bx + br - 7 * s, by + br - 7 * s], fill=fill)


def _rain(d, cx, cy, s=1.0):
    for i in range(4):
        x = cx - 40 * s + i * 22 * s
        y = cy + 30 * s
        d.line([(x, y), (x - 8 * s, y + 26 * s)], fill=PAL["blue"], width=6)


def _snow(d, cx, cy, s=1.0):
    rnd = random.Random(7)
    for i in range(5):
        x = cx - 45 * s + i * 22 * s
        y = cy + 34 * s + rnd.randint(-4, 4) * s
        d.ellipse([x - 6 * s, y - 6 * s, x + 6 * s, y + 6 * s], fill=PAL["blue"])


def _bolt(d, cx, cy, s=1.0):
    pts = [(cx + 6 * s, cy + 18 * s), (cx - 14 * s, cy + 50 * s),
           (cx - 2 * s, cy + 50 * s), (cx - 10 * s, cy + 84 * s),
           (cx + 18 * s, cy + 42 * s), (cx + 4 * s, cy + 42 * s)]
    d.polygon(pts, fill=PAL["yellow"], outline=PAL["black"])


def _fog(d, cx, cy, s=1.0):
    for i in range(4):
        y = cy - 10 * s + i * 26 * s
        x0 = cx - 70 * s + (i % 2) * 16 * s
        d.line([(x0, y), (x0 + 140 * s, y)], fill=PAL["blue"], width=8)


def _icon(d, cx, cy, code):
    if code == 0:
        _sun(d, cx, cy, 54)
    elif code == 1:
        _sun(d, cx + 40, cy - 34, 34); _cloud(d, cx, cy + 8, 1.0)
    elif code == 2:
        _sun(d, cx + 44, cy - 30, 30); _cloud(d, cx, cy + 8, 1.0)
    elif code == 3:
        _cloud(d, cx, cy, 1.05)
    elif code in (45, 48):
        _fog(d, cx, cy)
    elif code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        _cloud(d, cx, cy - 18, 1.05); _rain(d, cx, cy + 12, 1.05)
    elif code in (71, 73, 75, 77, 85, 86):
        _cloud(d, cx, cy - 18, 1.05); _snow(d, cx, cy + 8, 1.05)
    elif code in (95, 96, 99):
        _cloud(d, cx, cy - 22, 1.05); _bolt(d, cx, cy + 8, 1.0)
    else:
        _cloud(d, cx, cy, 1.0)


def render(w, font_path):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (W, H), PAL["white"])
    d = ImageDraw.Draw(img)

    def font(sz, bold=False):
        cand = BOLD_FONTS if bold else FONTS
        tried = ([font_path] if font_path else []) + list(cand)
        for p in tried:
            if p and os.path.exists(p):
                try:
                    return ImageFont.truetype(p, sz)
                except Exception:
                    continue
        return ImageFont.load_default()

    black, white = PAL["black"], PAL["white"]
    now = datetime.datetime.now()
    date_s = f"{now.month:02d}/{now.day:02d} {WEEK[now.weekday()]}"

    # 顶栏与固件版式保持一致：白底 + 橙色细条 + 黑字（不用整块蓝底）
    d.rectangle([0, 0, W, 8], fill=PAL["orange"])
    d.text((36, 52), "北京天气", font=font(46, bold=True), fill=black, anchor="lm")
    d.text((W - 36, 52), date_s, font=font(30, bold=True), fill=black, anchor="rm")

    _icon(d, 200, 220, w["code"])
    d.text((200, 340), w["label"], font=font(58, bold=True), fill=black, anchor="mm")

    def fit(text, base, minimum, avail, bold=True):
        sz = base
        while sz > minimum and d.textlength(text, font=font(sz, bold=bold)) > avail:
            sz -= 4
        return font(sz, bold=bold)

    t = w["temp"]
    tcol = temp_color(t)
    num = f"{t:.0f}"
    # 位数多（如 1000）时自动缩字号，给右侧 °C 和边距留位
    fnum = fit(num, 190, 80, W - 36 - 400 - 96)
    nw = d.textlength(num, font=fnum)
    d.text((400, 215), num, font=fnum, fill=black, anchor="lm")
    d.text((400 + nw + 8, 138), "°C", font=font(64, bold=True), fill=tcol, anchor="lm")
    d.text((400, 330), f"体感 {w['feels']:.0f}°", font=font(38, bold=True), fill=black, anchor="lm")

    cy0, ch, gap = 404, 64, 16
    cw = (W - 72 - gap * 2) // 3
    x0 = 30
    chips = [
        (PAL["blue"], "湿度", f"{int(w['humidity'])}%"),
        (PAL["green"], "风速", f"{w['wind']:.0f}km/h"),
        (PAL["orange"], "气温", f"{w['tmin']:.0f}~{w['tmax']:.0f}°"),
    ]
    fchip = fit(max((f"{lab}  {val}" for _, lab, val in chips),
                    key=lambda s: d.textlength(s, font=font(30, bold=True))),
                30, 16, cw - 48)
    for i, (col, lab, val) in enumerate(chips):
        x = x0 + i * (cw + gap)
        d.rounded_rectangle([x, cy0, x + cw, cy0 + ch], radius=14, fill=white, outline=black, width=3)
        d.rounded_rectangle([x + 12, cy0 + 12, x + 22, cy0 + ch - 12], radius=4, fill=col)
        d.text((x + 34, cy0 + ch // 2), f"{lab}  {val}", font=fchip, fill=black, anchor="lm")
    return img



def main():
    ap = argparse.ArgumentParser(description="北京天气 -> YSBadge2")
    ap.add_argument("--index", type=int, default=2, help="epd_index: 1=A 2=B 3=同显 7=异显")
    ap.add_argument("--addr", default="EE:96:BB:1E:05:28")
    ap.add_argument("--font", default=None, help="中文字体路径（否则自动探测）")
    ap.add_argument("--sample", action="store_true", help="用内置样例，不联网")
    ap.add_argument("--offline", action="store_true", help="只出图+打印压缩体积，不连设备")
    a = ap.parse_args()

    w = sample_weather() if a.sample else fetch_weather()
    print(f"天气：{w['label']}  {w['temp']:.0f}°C（体感 {w['feels']:.0f}°）"
          f"  湿度 {int(w['humidity'])}%  风速 {w['wind']:.0f}km/h"
          f"  高 {w['tmax']:.0f}°/低 {w['tmin']:.0f}°")

    img = render(w, a.font)
    fd, png = tempfile.mkstemp(suffix=".png", prefix="ysbadge_weather_")
    os.close(fd)
    img.save(png)
    print("已出图：", png)

    cmd = [sys.executable, os.path.join(ROOT, "epd_send.py"),
           "--image", png, "--index", str(a.index), "--addr", a.addr]
    if a.offline:
        cmd.append("--offline")
    try:
        subprocess.run(cmd, check=True)
    finally:
        if a.offline:
            try:
                os.remove(png)
            except OSError:
                pass


if __name__ == "__main__":
    main()
