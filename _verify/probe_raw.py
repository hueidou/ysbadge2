# -*- coding: utf-8 -*-
"""定位 compress_type=0 不刷新的原因。三组场景，每组都记录 ff04 通知。"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import asyncio, sys, time
sys.path.insert(0, _ROOT)
import epd_send as E
from bleak import BleakClient, BleakScanner

ADDR = "EE:96:BB:1E:05:28"
CHUNK = 244

raw, _ = E.encode_image(_VD + r"/test_pattern.png", False, False)
comp, bits = E.compress(raw)
log = lambda *a: print(*a, flush=True)

async def scenario(name, ctype, decl, buf, pace_on_notify=False, update=False):
    log(f"== {name}  compress_type={ctype} declare={decl} bytes={len(buf)}")
    dev = await BleakScanner.find_device_by_address(ADDR, timeout=12)
    if dev is None:
        log("   设备未广播"); return False
    t0 = time.time(); frames = []
    try:
        async with BleakClient(dev, timeout=25) as c:
            gate = asyncio.Event()
            def cb(_, d):
                frames.append((round(time.time()-t0,1), bytes(d).hex(' ')))
                log(f"   [ff04 {time.time()-t0:5.1f}s] {bytes(d).hex(' ')}")
                gate.set()
            await c.start_notify(E.CH_NOTIFY, cb)
            await asyncio.sleep(0.3)
            await c.write_gatt_char(E.CH_WRITE_CMD, bytes([0x00,0x06,0x01]), response=True)
            await asyncio.sleep(0.3)
            await c.write_gatt_char(E.CH_WRITE_CMD, bytes([0x01,ctype]) + decl.to_bytes(4,"little"), response=True)
            await asyncio.sleep(0.5)
            total = (len(buf)+CHUNK-1)//CHUNK
            t1 = time.time()
            for i in range(total):
                await c.write_gatt_char(E.CH_WRITE_PIC, buf[i*CHUNK:(i+1)*CHUNK], response=False)
                await asyncio.sleep(0.04)
                if pace_on_notify and gate.is_set():
                    log(f"   收到通知，暂停 2.5s（已发 {i+1}/{total}）")
                    gate.clear()
                    await asyncio.sleep(2.5)
            log(f"   发完 {total} 包 {time.time()-t1:.1f}s")
            if update:
                await asyncio.sleep(0.5)
                await c.write_gatt_char(E.CH_WRITE_CMD, bytes([0x03,0x00]), response=True)
                log("   已发 UPDATE 03 00")
            await asyncio.sleep(20)
            try:
                v = await c.read_gatt_char(E.CH_NOTIFY)
                log(f"   ff04 read = {bytes(v).hex(' ')}")
            except Exception as e:
                log("   ff04 read err", e)
            log(f"   frames={frames}")
            return True
    except Exception as e:
        log(f"   失败 {type(e).__name__}: {e}")
        return False

async def main():
    which = sys.argv[1] if len(sys.argv)>1 else "all"
    if which in ("all","ctl"):
        ok = await scenario("1 对照：压缩模式（已知可用）", 1, bits, comp)
        if not ok: log("对照失败，停止"); return 1
        log("   等 35s 让屏幕刷完"); await asyncio.sleep(35)
    if which in ("all","raw-update"):
        await scenario("2 未压缩 192000B + 收通知暂停 + UPDATE", 0, len(raw), raw, pace_on_notify=True, update=True)
        log("   等 35s"); await asyncio.sleep(35)
    if which in ("all","raw-bits"):
        await scenario("3 未压缩 但长度按比特声明 1536000", 0, len(raw)*8, raw)
    log("DONE")

raise SystemExit(asyncio.run(main()))
