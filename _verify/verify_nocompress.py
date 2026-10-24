# -*- coding: utf-8 -*-
"""未压缩通道验证：扫描到即连，重试，全程打时间戳。"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import argparse, asyncio, sys, time
sys.path.insert(0, _ROOT)
import epd_send as E
from bleak import BleakClient, BleakScanner

ap = argparse.ArgumentParser()
ap.add_argument("--image", required=True)
ap.add_argument("--index", type=int, default=1)
ap.add_argument("--chunk", type=int, default=244)
ap.add_argument("--interval", type=float, default=0.04)
ap.add_argument("--retries", type=int, default=4)
a = ap.parse_args()

raw, info = E.encode_image(a.image, False, False)
assert len(raw) == 192000, len(raw)
ADDR = "EE:96:BB:1E:05:28"
notif = []

async def attempt(n):
    t0 = time.time()
    dev = await BleakScanner.find_device_by_address(ADDR, timeout=8.0)
    if dev is None:
        print(f"[{n}] 扫描 8s 未发现 {ADDR}", flush=True)
        return False
    print(f"[{n}] 发现设备 {dev.address} rssi? ({time.time()-t0:.1f}s)", flush=True)
    def cb(ch, data):
        notif.append((round(time.time()-t0, 2), bytes(data)))
        print(f"  [notify {time.time()-t0:5.2f}s] {bytes(data).hex(' ')}", flush=True)
    try:
        async with BleakClient(dev, timeout=20.0) as cl:
            print(f"  已连接 mtu={cl.mtu_size} ({time.time()-t0:.1f}s)", flush=True)
            await cl.start_notify(E.CH_NOTIFY, cb)
            await asyncio.sleep(0.3)
            await cl.write_gatt_char(E.CH_WRITE_CMD, bytes([0x00, 0x06, a.index]), response=True)
            await asyncio.sleep(0.3)
            await cl.write_gatt_char(E.CH_WRITE_CMD, bytes([0x01, 0x00]) + len(raw).to_bytes(4, "little"), response=True)
            await asyncio.sleep(0.5)
            t1 = time.time()
            total = (len(raw) + a.chunk - 1) // a.chunk
            print(f"  开始发 {total} 包 x {a.chunk}B", flush=True)
            for i in range(total):
                await cl.write_gatt_char(E.CH_WRITE_PIC, raw[i*a.chunk:(i+1)*a.chunk], response=False)
                if a.interval:
                    await asyncio.sleep(a.interval)
                if (i+1) % 100 == 0:
                    print(f"    {i+1}/{total}  {time.time()-t1:.1f}s", flush=True)
            dt = time.time() - t1
            print(f"  数据发完 {dt:.1f}s，等待刷新", flush=True)
            await asyncio.sleep(3.0)
            try:
                await cl.stop_notify(E.CH_NOTIFY)
            except Exception as e:
                print("  stop_notify:", e, flush=True)
            print(f"  总耗时 {time.time()-t0:.1f}s，通知 {len(notif)} 条", flush=True)
            return True
    except Exception as e:
        print(f"  失败: {type(e).__name__}: {e}", flush=True)
        return False

async def main():
    for n in range(1, a.retries + 1):
        if await attempt(n):
            print("RESULT: sent", flush=True)
            return 0
        await asyncio.sleep(1.0)
    print("RESULT: all attempts failed", flush=True)
    return 1

raise SystemExit(asyncio.run(main()))
