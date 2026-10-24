# -*- coding: utf-8 -*-
"""单帧命令探针：往 ff03 写一帧原始 hex，全程记录 ff04 通知。

    python _verify/probe_cmd.py <hex> [观察秒数]

安全约束（PLAN_32KB_BLE.md）：
- 一次只发一帧，不在脚本内连续发多个未知命令
- 不发 ff02 数据
- 发完干净断开，断开前留足观察时间
"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import sys, time, asyncio

sys.path.insert(0, _ROOT)
import epd_send as E
from bleak import BleakClient, BleakScanner

ADDR = "EE:96:BB:1E:05:28"

def log(*a):
    print(*a, flush=True)

def parse_hex(s):
    c = s.replace(" ", "").replace(":", "")
    return bytes.fromhex(c)

async def main():
    if len(sys.argv) < 2:
        log("用法: probe_cmd.py <hex> [观察秒数]"); return 2
    frame = parse_hex(sys.argv[1])
    hold = float(sys.argv[2]) if len(sys.argv) > 2 else 25.0
    log("== 等设备广播 ==")
    dev = await BleakScanner.find_device_by_address(ADDR, timeout=60)
    if not dev:
        log("未发现设备"); return 1
    log("帧内容: " + frame.hex(" ") + "（%d 字节）-> ff03（带响应写）" % len(frame))
    frames = []
    t0 = time.time()
    try:
        async with BleakClient(dev, timeout=25) as c:
            def cb(_, d):
                frames.append((round(time.time() - t0, 2), bytes(d).hex(" ")))
                log("   [ff04 %6.2fs] %s" % (time.time() - t0, bytes(d).hex(" ")))
            await c.start_notify(E.CH_NOTIFY, cb)
            await asyncio.sleep(0.3)
            log("写入 %s ..." % frame.hex(" "))
            await c.write_gatt_char(E.CH_WRITE_CMD, frame, response=True)
            log("写入完成（%.2fs），观察 %.0fs" % (time.time() - t0, hold))
            await asyncio.sleep(hold)
            try:
                await c.stop_notify(E.CH_NOTIFY)
            except Exception:
                pass
        log("断开正常")
    except Exception as e:
        log("异常 %s: %s" % (type(e).__name__, e))
    log("ff04 通知汇总:", frames if frames else "无")
    log("DONE —— 请看屏幕并确认设备是否仍在广播")
    return 0

raise SystemExit(asyncio.run(main()))
