# -*- coding: utf-8 -*-
import asyncio, sys, time
from bleak import BleakScanner
DUR = int(sys.argv[1]) if len(sys.argv) > 1 else 60
seen = {}
def cb(dev, adv):
    n = (adv.local_name or dev.name or "")
    su = [str(u).lower() for u in (adv.service_uuids or [])]
    if "ys" in n.lower() or "0000ff01-0000-1000-8000-00805f9b34fb" in su:
        if dev.address not in seen:
            print("[%s] FOUND %s %r rssi=%d" % (time.strftime("%H:%M:%S"), dev.address, n, adv.rssi), flush=True)
        seen[dev.address] = adv.rssi
async def main():
    async with BleakScanner(cb) as s:
        await asyncio.sleep(DUR)
asyncio.run(main())
print("[%s] window over; seen: %s" % (time.strftime("%H:%M:%S"), seen or "NONE"), flush=True)
