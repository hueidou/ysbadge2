import asyncio
from bleak import BleakClient
ADDR="EE:96:BB:1E:05:28"
async def main():
    async with BleakClient(ADDR, timeout=20) as c:
        print("connected", c.is_connected, "mtu", c.mtu_size)
        for s in c.services:
            print("SERVICE", s.uuid, s.description)
            for ch in s.characteristics:
                print("   CHAR", ch.uuid, ch.properties)
        await asyncio.sleep(0.5)
asyncio.run(main())
