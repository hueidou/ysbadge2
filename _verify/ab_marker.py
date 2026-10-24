# -*- coding: utf-8 -*-
"""A/B：同一张标记图，先压缩发、再未压缩发，观察是否刷新/设备是否掉线。"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import asyncio, sys, time
sys.path.insert(0, _ROOT)
import epd_send as E
from bleak import BleakClient, BleakScanner

ADDR="EE:96:BB:1E:05:28"; CHUNK=244
raw,_=E.encode_image(_VD + r"/marker.png", False, False)
comp,bits=E.compress(raw)
log=lambda *a: print(*a, flush=True)

async def wait_dev(sec):
    log(f"等广播 {sec:.0f}s ...")
    d = await BleakScanner.find_device_by_address(ADDR, timeout=sec)
    if d: log(f"发现设备")
    return d

async def transfer(dev, name, ctype, decl, buf, hold):
    t0=time.time(); frames=[]
    try:
        async with BleakClient(dev, timeout=25) as c:
            def cb(_,d):
                frames.append((round(time.time()-t0,1), bytes(d).hex(' ')))
                log(f"   [ff04 {time.time()-t0:5.1f}s] {bytes(d).hex(' ')}")
            await c.start_notify(E.CH_NOTIFY, cb); await asyncio.sleep(0.3)
            await c.write_gatt_char(E.CH_WRITE_CMD, bytes([0x00,0x06,0x01]), response=True)
            await asyncio.sleep(0.3)
            await c.write_gatt_char(E.CH_WRITE_CMD, bytes([0x01,ctype])+decl.to_bytes(4,"little"), response=True)
            await asyncio.sleep(0.5)
            n=(len(buf)+CHUNK-1)//CHUNK; t1=time.time()
            for i in range(n):
                await c.write_gatt_char(E.CH_WRITE_PIC, buf[i*CHUNK:(i+1)*CHUNK], response=False)
                await asyncio.sleep(0.04)
            log(f"   {name}: {n} 包 {len(buf)}B 发完 {time.time()-t1:.1f}s")
            await asyncio.sleep(hold)
            try: await c.stop_notify(E.CH_NOTIFY)
            except Exception: pass
        log(f"   {name} 断开正常, frames={frames}")
        return True
    except Exception as e:
        log(f"   {name} 异常 {type(e).__name__}: {e} frames={frames}")
        return False

async def main():
    dev = await wait_dev(200)
    if not dev: log("超时未发现设备"); return 1
    await transfer(dev, "A 压缩", 1, bits, comp, 20)
    log("等 35s"); await asyncio.sleep(35)
    dev = await wait_dev(20)
    if not dev: log("A 之后设备不再广播（异常）"); return 1
    await transfer(dev, "B 未压缩", 0, len(raw), raw, 25)
    log("等 15s 后扫描看设备是否还在广播")
    await asyncio.sleep(15)
    d2 = await BleakScanner.find_device_by_address(ADDR, timeout=8)
    log("扫描结果:", "仍在广播" if d2 else "已消失/无响应")
    log("DONE")

raise SystemExit(asyncio.run(main()))
