# -*- coding: utf-8 -*-
import asyncio, sys
from bleak import BleakScanner

SERVICE = "0000ff01-0000-1000-8000-00805f9b34fb"

async def main():
    print("scanning 12s ...", flush=True)
    devs = await BleakScanner.discover(timeout=12, return_adv=True)
    print("found %d devices" % len(devs), flush=True)
    for addr, (d, adv) in devs.items():
        name = d.name or adv.local_name or ""
        svcs = [str(u).lower() for u in (adv.service_uuids or [])]
        tag = "  <== EPD ff01" if SERVICE in svcs else ""
        print(f"{addr}  rssi={adv.rssi:<4} name={name!r} services={svcs}{tag}", flush=True)

asyncio.run(main())
