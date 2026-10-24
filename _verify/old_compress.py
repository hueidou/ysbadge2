MAX_WND = 1024

MAX_WND = 1024

def _oldcp(data, p1, p2, cap):
    if cap <= 0 or data[p1] != data[p2]:
        return 0
    lo, hi = 1, cap
    while lo < hi:
        mid = (lo + hi + 1) >> 1
        if data[p1:p1+mid] == data[p2:p2+mid]:
            lo = mid
        else:
            hi = mid - 1
    return lo

def old_compress(data):
    n = len(data)
    out = bytearray(n*2)
    bitpos = 0
    i = 0
    def w0(bp):
        out[bp >> 3] &= (0xFF ^ (1 << (7 & bp)))
    while i < n:
        rel = i - MAX_WND
        if rel >= 0:
            winStart, maxlen = rel, MAX_WND
        elif rel >= -MAX_WND:
            winStart, maxlen = 0, MAX_WND + rel
        else:
            winStart, maxlen = -1, 0
        if maxlen > n - i:
            maxlen = n - i
        length = 0
        offset = 0
        best = 0
        if winStart >= 0:
            for k in range(maxlen):
                cap = maxlen - k
                if cap <= best:
                    break
                ml = _oldcp(data, winStart+k, i, cap)
                if ml > best:
                    best = ml
                    offset = k
                    length = ml
        if length > 1:
            out[bitpos >> 3] |= (1 << (7 & bitpos)); bitpos += 1
            for b in range(10):
                if (offset >> b) & 1:
                    out[bitpos >> 3] |= (1 << (7 & bitpos))
                else:
                    w0(bitpos)
                bitpos += 1
            x = length
            q = (x - 1) >> 3
            r = (x - (q << 3)) - 1
            for _ in range(q):
                out[bitpos >> 3] |= (1 << (7 & bitpos)); bitpos += 1
            w0(bitpos); bitpos += 1
            for b in range(3):
                if (r >> b) & 1:
                    out[bitpos >> 3] |= (1 << (7 & bitpos))
                else:
                    w0(bitpos)
                bitpos += 1
            i += length
        else:
            w0(bitpos); bitpos += 1
            c = data[i]
            for b in range(8):
                if (c >> b) & 1:
                    out[bitpos >> 3] |= (1 << (7 & bitpos))
                else:
                    w0(bitpos)
                bitpos += 1
            i += 1
    total_bits = bitpos
    nbytes = (total_bits + 7) >> 3
    return bytes(out[:nbytes]), total_bits


import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_VD = _os.path.join(_ROOT, "_verify")