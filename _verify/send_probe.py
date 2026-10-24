# -*- coding: utf-8 -*-
"""实机发送探针：复刻 ab_marker.py 已验证成功的压缩路径。

    python _verify/send_probe.py [图A] [index] [图B]

- PIC_INFO 声明**压缩后比特数**（LESSONS.md §1 第 2 行的硬件验证口径）
- ff02 分块 244 B、40ms；ff03 用带响应写；全程记录 ff04 通知时间戳
- 发完保持 20s 观察通知，不断连（设备可能需要连接保持）
- 传第三参图B 时走 index 7（A&B 异显，pic_data = A || B），与 CLI --image2 一致
"""
import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import sys, time, asyncio

sys.path.insert(0, _ROOT)
import epd_send as E
from bleak import BleakClient, BleakScanner

ADDR = "EE:96:BB:1E:05:28"
CHUNK = 244
IMG_A = sys.argv[1] if len(sys.argv) > 1 else _VD + r"/test_pattern.png"
INDEX = int(sys.argv[2]) if len(sys.argv) > 2 else 1
IMG_B = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "-" else None
# 可选第四参：数据发完后补一帧原始 hex 到 ff03（如 A0）；第五参：补帧后的观察秒数
POST_CMD = bytes.fromhex(sys.argv[4].replace(" ", "")) if len(sys.argv) > 4 and sys.argv[4] != "-" else None
POST_HOLD = float(sys.argv[5]) if len(sys.argv) > 5 else 30.0

def log(*a):
    print(*a, flush=True)

async def main():
    log("== 等设备广播 ==")
    dev = await BleakScanner.find_device_by_address(ADDR, timeout=60)
    if not dev:
        log("60s 未发现设备，放弃（不要盲目重试）")
        return 1
    log("发现设备", dev.address)
    if IMG_B:
        rawA, infoA = E.encode_image(IMG_A, False, False)
        rawB, infoB = E.encode_image(IMG_B, False, False, False, False)   # 同 CLI：B 面只吃这四个参数
        raw = rawA + rawB
        log("A 面 %s -> %d B；B 面 %s -> %d B；合并 %d B" % (infoA, len(rawA), infoB, len(rawB), len(raw)))
    else:
        raw, info = E.encode_image(IMG_A, False, False)
        log("pic_data %d B" % len(raw))
    comp, bits = E.compress(raw)
    rt = E.decompress(comp, bits)
    assert rt == raw, "round-trip FAIL"
    log("压缩 %d B / %d bit（上限 262144，占 %.1f%%）" % (len(comp), bits, 100.0 * bits / 262144))
    if bits > E.MAX_PAYLOAD_BITS:
        log("超限，放弃发送")
        return 2
    init = bytes([0x00, 0x06, INDEX])
    info_cmd = bytes([0x01, 0x01]) + bits.to_bytes(4, "little")
    log("INIT    ", init.hex(" "))
    log("PIC_INFO", info_cmd.hex(" "), "（len=%d 比特）" % bits)
    frames = []
    t0 = time.time()
    try:
        async with BleakClient(dev, timeout=25) as c:
            def cb(_, d):
                frames.append((round(time.time() - t0, 2), bytes(d).hex(" ")))
                log("   [ff04 %6.2fs] %s" % (time.time() - t0, bytes(d).hex(" ")))
            await c.start_notify(E.CH_NOTIFY, cb)
            await asyncio.sleep(0.3)
            await c.write_gatt_char(E.CH_WRITE_CMD, init, response=True)
            await asyncio.sleep(0.3)
            await c.write_gatt_char(E.CH_WRITE_CMD, info_cmd, response=True)
            await asyncio.sleep(0.6)
            n = (len(comp) + CHUNK - 1) // CHUNK
            log("PIC_DATA %d B -> ff02，%d 块 x %d B，40ms/块" % (len(comp), n, CHUNK))
            for i in range(n):
                await c.write_gatt_char(E.CH_WRITE_PIC, comp[i * CHUNK:(i + 1) * CHUNK], response=False)
                await asyncio.sleep(0.04)
            log("发送完成 %.2fs" % (time.time() - t0))
            if POST_CMD:
                log("补发命令 %s -> ff03（带响应写）" % POST_CMD.hex(" "))
                await c.write_gatt_char(E.CH_WRITE_CMD, POST_CMD, response=True)
                log("补发完成，观察 %.0fs" % POST_HOLD)
                await asyncio.sleep(POST_HOLD)
            else:
                var_hold = POST_HOLD if len(sys.argv) > 5 else 20.0
                log("保持连接观察 %.0fs" % var_hold)
                await asyncio.sleep(var_hold)
            try:
                await c.stop_notify(E.CH_NOTIFY)
            except Exception:
                pass
        log("断开正常")
    except Exception as e:
        log("异常 %s: %s" % (type(e).__name__, e))
    log("ff04 通知汇总:", frames if frames else "无")
    log("DONE —— 请看两块屏幕（A 面 / B 面）是否分别显示两张图")
    return 0

raise SystemExit(asyncio.run(main()))
