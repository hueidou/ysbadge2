# -*- coding: utf-8 -*-
"""生成 README 用的天气卡示例图（直接调用固件同一套 C++ 渲染器，保证和屏上一致）。

用法：
    cd _verify/host && python make_weather_example.py
产物：../../docs/images/weather-example.png（800x480）

前置：host.exe 已编译（见 docs/ESP32_WEATHER.md §8）。
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "docs", "images", "weather-example.png")
CODE, TEMP = 0, 9          # 晴、9 度（与 2026-10-29 实机那版一致）


def main():
    exe = os.path.join(HERE, "host.exe")
    if not os.path.exists(exe):
        sys.exit("先编译 host.exe：见 docs/ESP32_WEATHER.md §8")
    ppm = os.path.join(HERE, "_example.ppm")
    subprocess.run([exe, "preview", ppm, str(CODE), str(TEMP)], check=True)
    try:
        from PIL import Image
        Image.open(ppm).convert("RGB").save(OUT)
    finally:
        os.remove(ppm)
    print("已更新", os.path.normpath(OUT))


if __name__ == "__main__":
    main()

