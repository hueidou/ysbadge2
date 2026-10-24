import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")
import asyncio, time
from bleak import BleakClient
ADDR="EE:96:BB:1E:05:28"
async def main():
    for i in range(6):
        t0=time.time()
        try:
            async with BleakClient(ADDR, timeout=12.0) as cl:
                print(f"[{i+1}] OK mtu={cl.mtu_size} {time.time()-t0:.1f}s", flush=True)
                return
        except Exception as e:
            print(f"[{i+1}] {type(e).__name__}: {e} ({time.time()-t0:.1f}s)", flush=True)
        await asyncio.sleep(5)
asyncio.run(main())
