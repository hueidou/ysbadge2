# -*- coding: utf-8 -*-
"""抓 ESP32-C3 上电/复位日志：先压 EN 再放开，从第一毫秒开始读。

用法：python _verify/c3_bootlog.py [秒数] [波特率]
"""
import sys, time, serial

port = "COM7"
secs = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200

s = serial.Serial(port, baud, timeout=0.01)
s.setDTR(False)     # IO0 = 高（正常启动，不进下载模式）
s.setRTS(True)      # EN 拉低 = 复位
time.sleep(0.15)
s.reset_input_buffer()
t0 = time.time()
s.setRTS(False)     # 放开 EN，芯片开始跑

buf = bytearray()
while time.time() - t0 < secs:
    chunk = s.read(4096)
    if chunk:
        buf.extend(chunk)
s.close()

raw = bytes(buf)
print("=== %d B @ %d baud, %.1fs ===" % (len(raw), baud, secs))
print(raw.decode("utf-8", "replace"))
open("_verify/_c3_bootlog.bin", "wb").write(raw)
print("=== raw hex (first 128B) ===")
print(raw[:128].hex(" "))

