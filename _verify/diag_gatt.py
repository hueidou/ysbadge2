# -*- coding: utf-8 -*-
"""只读诊断：反复连接枚举，观察 ff01 服务是否/何时出现。不写任何特征值。"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import asyncio, time, sys
sys.path.insert(0, _ROOT)
from bleak import BleakClient, BleakScanner

ADDR = "EE:96:BB:1E:05:28"
SVC = "0000ff01-0000-1000-8000-00805f9b34fb"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
GAP = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0

def log(*a): print(*a, flush=True)

async def main():
    dev = await BleakScanner.find_device_by_address(ADDR, timeout=60)
    if not dev:
        log("未发现设备"); return 1
    log("设备就绪，开始 %d 轮只读枚举，间隔 %.0fs" % (N, GAP))
    for i in range(N):
        t0 = time.time()
        try:
            async with BleakClient(dev, timeout=20) as c:
                svcs = [str(s.uuid).lower() for s in c.services]
                has = SVC in svcs
                chs = []
                if has:
                    s = c.services.get_service(SVC)
                    chs = [str(ch.uuid)[4:8] for ch in s.characteristics]
                log("第 %d/%d 轮  ff01=%s  特征=%s  服务数=%d  (%.1fs)" %
                    (i + 1, N, "有" if has else "无", ",".join(chs) if chs else "-", len(svcs), time.time() - t0))
        except Exception as e:
            log("第 %d/%d 轮  连接失败 %s: %s" % (i + 1, N, type(e).__name__, e))
        if i < N - 1:
            await asyncio.sleep(GAP)
    return 0

raise SystemExit(asyncio.run(main()))
