# -*- coding: utf-8 -*-
"""交叉验证：C++ 端（host.exe frame）压出来的比特流，必须被 Python 的 decompress() 还原成同一份 192000 B。

Python 的 decompress() 与设备侧解压器位级一致（见 docs/PROTOCOL.md §5.2），
所以这条链路等于是"设备能不能解出来"的离线证明。
用法：python _verify/check_lz77_port.py
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HOST = os.path.join(HERE, "host")
sys.path.insert(0, ROOT)
from epd_send import compress, decompress

def run_frame():
    exe = os.path.join(HOST, "host.exe")
    if not os.path.exists(exe):
        sys.exit("先编译 host.exe（见 docs/ESP32_WEATHER.md §6）")
    bits, nbytes, ovf = map(int, subprocess.run(
        [exe, "frame", os.path.join(HOST, "f.lz"), os.path.join(HOST, "f.raw")],
        capture_output=True, text=True, check=True).stdout.split())
    lz = open(os.path.join(HOST, "f.lz"), "rb").read()
    raw = open(os.path.join(HOST, "f.raw"), "rb").read()
    return bits, lz, raw

def main():
    bits, lz, raw = run_frame()
    assert len(raw) == 192000, len(raw)
    assert len(lz) == (bits + 7) // 8, (len(lz), bits)
    back = decompress(lz, bits)
    ok = back == raw
    print("C++ 压缩: %d bit = %d B (原始 192000 B, %.1f%%)" % (bits, len(lz), 100.0 * len(lz) / 192000))
    print("Python 解压往返一致:", ok)
    if not ok:
        for i, (a, b) in enumerate(zip(back, raw)):
            if a != b:
                print("首个差异 @%d: got %02x want %02x" % (i, a, b))
                break
        sys.exit(1)
    # 同一份原始帧交给 Python 自己的 compress()，比对体积（不要求逐字节相同）
    py_lz, py_bits = compress(raw)
    print("Python 压缩: %d bit = %d B（体积差 %+d B，允许：候选匹配策略不同）"
          % (py_bits, len(py_lz), len(lz) - len(py_lz)))
    assert bits <= 262144, "超设备上限"

if __name__ == "__main__":
    main()

