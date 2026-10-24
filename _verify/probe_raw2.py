# -*- coding: utf-8 -*-
"""three probes: UPDATE-only / raw with bits-declared len / raw + UPDATE"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import asyncio, sys, time
sys.path.insert(0, _ROOT)
import epd_send as E
from bleak import BleakClient, BleakScanner
ADDR="EE:96:BB:1E:05:28"; CHUNK=244
raw,_=E.encode_image(_VD + r"/marker.png", False, False)
log=lambda *a: print(*a, flush=True)

async def conn():
    for _ in range(3):
        d = await BleakScanner.find_device_by_address(ADDR, timeout=10)
        if d: return d
    return None

async def probe(tag, decl, send_data, update, hold=22):
    dev = await conn()
    if not dev: log(f"{tag}: 设备未广播"); return
    t0=time.time(); frames=[]
    try:
        async with BleakClient(dev, timeout=25) as c:
            def cb(_,d):
                frames.append((round(time.time()-t0,1), bytes(d).hex(' ')))
                log(f"   [{tag}] ff04 {time.time()-t0:5.1f}s {bytes(d).hex(' ')}")
            await c.start_notify(E.CH_NOTIFY, cb); await asyncio.sleep(0.3)
            if decl is not None:
                await c.write_gatt_char(E.CH_WRITE_CMD, bytes([0x00,0x06,0x01]), response=True)
                await asyncio.sleep(0.3)
                await c.write_gatt_char(E.CH_WRITE_CMD, bytes([0x01,0x00])+decl.to_bytes(4,"little"), response=True)
                await asyncio.sleep(0.5)
            if send_data:
                n=(len(raw)+CHUNK-1)//CHUNK; t1=time.time()
                for i in range(n):
                    await c.write_gatt_char(E.CH_WRITE_PIC, raw[i*CHUNK:(i+1)*CHUNK], response=False)
                    await asyncio.sleep(0.04)
                log(f"   [{tag}] {n} 包发完 {time.time()-t1:.1f}s")
            if update:
                await asyncio.sleep(0.8)
                try:
                    await c.write_gatt_char(E.CH_WRITE_CMD, bytes([0x03,0x00]), response=True)
                    log(f"   [{tag}] UPDATE 已写")
                except Exception as e:
                    log(f"   [{tag}] UPDATE 失败 {type(e).__name__}")
            await asyncio.sleep(hold)
            try: await c.stop_notify(E.CH_NOTIFY)
            except Exception: pass
        log(f"{tag}: 正常断开 frames={frames}")
    except Exception as e:
        log(f"{tag}: 异常 {type(e).__name__}: {e}")

async def main():
    log("--- P1 UPDATE-only (验证上次 raw 数据是否残留在缓冲)")
    await probe("P1", None, False, True, 15)
    log("等 30s"); await asyncio.sleep(30)
    log("--- P2 raw 但长度声明为比特 1536000")
    await probe("P2", len(raw)*8, True, False, 22)
    log("等 35s"); await asyncio.sleep(35)
    log("--- P3 raw 字节长度 + UPDATE")
    await probe("P3", len(raw), True, True, 22)
    log("DONE")

asyncio.run(main())
