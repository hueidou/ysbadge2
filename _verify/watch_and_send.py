# -*- coding: utf-8 -*-
"""盯广播：YSBadge 一出现立刻连接 + 未压缩发送，最多等 N 秒。"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import asyncio, sys, time
sys.path.insert(0, _ROOT)
import epd_send as E
from bleak import BleakClient, BleakScanner

ADDR = "EE:96:BB:1E:05:28"
WINDOW = float(sys.argv[1]) if len(sys.argv) > 1 else 180.0
INDEX = int(sys.argv[2]) if len(sys.argv) > 2 else 1
IMAGE = sys.argv[3] if len(sys.argv) > 3 else "test_pattern.png"
CHUNK, INTERVAL = 244, 0.04

def log(*a): print(*a, flush=True)

async def send(dev, raw):
    notif = []
    def cb(ch, data):
        notif.append(bytes(data)); log(f"  [notify] {bytes(data).hex(' ')}")
    t0 = time.time()
    async with BleakClient(dev, timeout=25.0) as cl:
        log(f"  已连接 mtu={cl.mtu_size} ({time.time()-t0:.1f}s)")
        await cl.start_notify(E.CH_NOTIFY, cb)
        await asyncio.sleep(0.3)
        await cl.write_gatt_char(E.CH_WRITE_CMD, bytes([0x00, 0x06, INDEX]), response=True)
        await asyncio.sleep(0.3)
        info = bytes([0x01, 0x00]) + len(raw).to_bytes(4, "little")
        log("  PIC_INFO", info.hex(" "))
        await cl.write_gatt_char(E.CH_WRITE_CMD, info, response=True)
        await asyncio.sleep(0.5)
        t1 = time.time(); total = (len(raw) + CHUNK - 1) // CHUNK
        log(f"  发送 {total} 包 x {CHUNK}B")
        for i in range(total):
            await cl.write_gatt_char(E.CH_WRITE_PIC, raw[i*CHUNK:(i+1)*CHUNK], response=False)
            await asyncio.sleep(INTERVAL)
            if (i+1) % 100 == 0:
                log(f"    {i+1}/{total} {time.time()-t1:.1f}s")
        log(f"  数据发完 {time.time()-t1:.1f}s，等待刷新")
        await asyncio.sleep(3.0)
        try: await cl.stop_notify(E.CH_NOTIFY)
        except Exception: pass
        log(f"  完成，通知 {len(notif)} 条")

async def main():
    raw, info = E.encode_image(IMAGE, False, False)
    assert len(raw) == 192000
    log(f"payload ready {len(raw)}B; 等待 YSBadge 广播 (最多 {WINDOW:.0f}s) ...")
    seen = asyncio.Event(); holder = {}
    def det(dev, adv):
        if dev.address.upper() == ADDR or "ff01" in " ".join(str(u) for u in (adv.service_uuids or [])):
            if not seen.is_set():
                holder["dev"] = dev
                seen.set()
    scanner = BleakScanner(detection_callback=det)
    await scanner.start()
    try:
        await asyncio.wait_for(seen.wait(), timeout=WINDOW)
    except asyncio.TimeoutError:
        log("等超时：整个窗口内没看到 YSBadge 广播")
        await scanner.stop(); return 1
    dev = holder["dev"]
    log(f"发现 {dev.address}，立刻停止扫描并连接")
    await scanner.stop()
    for attempt in range(3):
        try:
            await send(dev, raw); log("RESULT: SENT"); return 0
        except Exception as e:
            log(f"  连接/发送失败[{attempt+1}]: {type(e).__name__}: {e}")
            await asyncio.sleep(2)
    log("RESULT: FAILED")
    return 1

raise SystemExit(asyncio.run(main()))
