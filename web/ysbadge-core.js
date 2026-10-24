/*!
 * ysbadge-core.js — YSBadge2 协议层纯函数（无 DOM 依赖）
 *
 * 与 epd_send.py 逐字节一致，由 _verify/check_web_core.py 交叉验证：
 *   量化(nearest/ordered/noise) · 4bit 打包 · LZ77 压缩/解压 · MT19937(噪声 RNG)
 *
 * 浏览器：<script src="ysbadge-core.js"></script> 后可用全局 YSB
 * Node  ：const YSB = require('./ysbadge-core.js')
 */
(function (global, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else global.YSB = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var W = 800, H = 480, MAX_WND = 1024, MAX_BITS = 262144;
  var PALETTE = [[0,0,0],[255,255,255],[0,255,0],[0,0,255],[255,0,0],[255,255,0],[255,128,0]];
  var BAYER8 = [
    [ 0,32, 8,40, 2,34,10,42],[48,16,56,24,50,18,58,26],
    [12,44, 4,36,14,46, 6,38],[60,28,52,20,62,30,54,22],
    [ 3,35,11,43, 1,33, 9,41],[51,19,59,27,49,17,57,25],
    [15,47, 7,39,13,45, 5,37],[63,31,55,23,61,29,53,21]];

  function clamp255(v) { return v < 0 ? 0 : (v > 255 ? 255 : v); }

  // 最近色：欧氏距离，严格小于才替换（同距取索引小者）
  function nearest(r, g, b) {
    var best = 1073741824, bi = 0;
    for (var i = 0; i < 7; i++) {
      var p = PALETTE[i];
      var d = (r - p[0]) * (r - p[0]) + (g - p[1]) * (g - p[1]) + (b - p[2]) * (b - p[2]);
      if (d < best) { best = d; bi = i; }
    }
    return bi;
  }

  // ---- MT19937：与 Python random.Random(int) 的播种/取数语义一致 ----
  function mt19937(seed) {
    var N = 624, M = 397, MATRIX_A = 0x9908b0df, UPPER = 0x80000000, LOWER = 0x7fffffff;
    var mt = new Array(N), mti = N;
    function initGenrand(s) {
      mt[0] = s >>> 0;
      for (var i = 1; i < N; i++)
        mt[i] = (Math.imul(1812433253, (mt[i - 1] ^ (mt[i - 1] >>> 30))) + i) >>> 0;
      mti = N;
    }
    // 与 CPython _randommodule.c 的 init_by_array 一致：比 mt19937ar.c 参考实现
    // 多第二个混合循环（1566083941 / 减法），末尾强制 mt[0]=0x80000000。
    function initByArray(key) {
      var i = 1, j = 0, k = Math.max(N, key.length);
      initGenrand(19650218);
      for (; k; k--) {
        mt[i] = (((mt[i] ^ Math.imul((mt[i - 1] ^ (mt[i - 1] >>> 30)), 1664525)) + key[j] + j) >>> 0);
        i++; j++;
        if (i >= N) { mt[0] = mt[N - 1]; i = 1; }
        if (j >= key.length) j = 0;
      }
      for (k = N - 1; k; k--) {
        mt[i] = ((mt[i] ^ Math.imul((mt[i - 1] ^ (mt[i - 1] >>> 30)), 1566083941)) - i) >>> 0;
        i++;
        if (i >= N) { mt[0] = mt[N - 1]; i = 1; }
      }
      mt[0] = 0x80000000;   /* MSB is 1; assuring non-zero initial array */
    }
    // Python random.seed(int)：绝对值按 32bit 小端切词后 init_by_array
    var key = [], big = BigInt(Math.abs(seed));
    if (big === 0n) key = [0];
    else while (big > 0n) { key.push(Number(big & 0xffffffffn)); big >>= 32n; }
    initByArray(key);
    function genrand() {
      var y;
      if (mti >= N) {
        var kk;
        for (kk = 0; kk < N - M; kk++) {
          y = (mt[kk] & UPPER) | (mt[kk + 1] & LOWER);
          mt[kk] = (mt[kk + M] ^ (y >>> 1) ^ ((y & 1) ? MATRIX_A : 0)) >>> 0;
        }
        for (; kk < N - 1; kk++) {
          y = (mt[kk] & UPPER) | (mt[kk + 1] & LOWER);
          mt[kk] = (mt[kk + (M - N)] ^ (y >>> 1) ^ ((y & 1) ? MATRIX_A : 0)) >>> 0;
        }
        y = (mt[N - 1] & UPPER) | (mt[0] & LOWER);
        mt[N - 1] = (mt[M - 1] ^ (y >>> 1) ^ ((y & 1) ? MATRIX_A : 0)) >>> 0;
        mti = 0;
      }
      y = mt[mti++];
      y ^= (y >>> 11);
      y ^= (Math.imul(y, 0x80) & 0x9d2c5680) >>> 0;      // y ^= (y << 7)  & 0x9d2c5680
      y ^= (Math.imul(y, 0x8000) & 0xefc60000) >>> 0;    // y ^= (y << 15) & 0xefc60000
      y ^= y >>> 18;
      return y >>> 0;
    }
    function getrandbits(k) { return k === 0 ? 0 : (genrand() >>> (32 - k)); }
    function randbelow(v) {                        // random._randbelow
      var b = 0, t = v;
      while (t > 0) { t = Math.floor(t / 2); b++; }
      var r = getrandbits(b);
      while (r >= v) r = getrandbits(b);
      return r;
    }
    return {
      genrand: genrand,
      randint: function (a, b) { return a + randbelow(b - a + 1); }
    };
  }

  // ---- 量化：rgba 长度 W*H*4，行优先。RNG 消耗顺序同行优先逐像素 (r,g,b) ----
  function quantizeRGBA(rgba, opts) {
    opts = opts || {};
    var mode = opts.mode || 'none';
    var spread = (opts.spread === undefined ? 128 : opts.spread);
    var noise = opts.noise || 0, seed = (opts.seed === undefined ? 1 : opts.seed);
    var idx = new Uint8Array(W * H), rng = noise > 0 ? mt19937(seed) : null, A = Math.floor(noise);
    if (mode === 'fs') {
      // 标准 Floyd–Steinberg（7/16,3/16,5/16,1/16）。注意：PIL 的 FS 噪声图案与此不同
      // （语义一致），见 docs/IMAGE_PROCESSING.md §3，故本路径不与 Python 做逐字节断言。
      var er = new Float64Array(W * H), eg = new Float64Array(W * H), eb = new Float64Array(W * H);
      for (var y = 0; y < H; y++) for (var x = 0; x < W; x++) {
        var o = y * W + x, p = o * 4;
        var r = clamp255(rgba[p] + er[o]), g = clamp255(rgba[p + 1] + eg[o]), b = clamp255(rgba[p + 2] + eb[o]);
        var q = nearest(r, g, b);
        idx[o] = q;
        var pr = PALETTE[q], dr = r - pr[0], dg = g - pr[1], db = b - pr[2];
        if (x + 1 < W)       { er[o + 1] += dr * 7 / 16; eg[o + 1] += dg * 7 / 16; eb[o + 1] += db * 7 / 16; }
        if (y + 1 < H) {
          er[(y + 1) * W + x] += dr * 5 / 16; eg[(y + 1) * W + x] += dg * 5 / 16; eb[(y + 1) * W + x] += db * 5 / 16;
          if (x > 0)     { er[(y + 1) * W + x - 1] += dr * 3 / 16; eg[(y + 1) * W + x - 1] += dg * 3 / 16; eb[(y + 1) * W + x - 1] += db * 3 / 16; }
          if (x + 1 < W) { er[(y + 1) * W + x + 1] += dr / 16;     eg[(y + 1) * W + x + 1] += dg / 16;     eb[(y + 1) * W + x + 1] += db / 16; }
        }
      }
      return idx;
    }
    for (var y2 = 0; y2 < H; y2++) for (var x2 = 0; x2 < W; x2++) {
      var pp = (y2 * W + x2) * 4;
      var rr = rgba[pp], gg = rgba[pp + 1], bb = rgba[pp + 2];
      if (A) {
        rr += rng.randint(-A, A); gg += rng.randint(-A, A); bb += rng.randint(-A, A);
        rr = clamp255(rr); gg = clamp255(gg); bb = clamp255(bb);
      }
      if (mode === 'ordered') {
        var t = ((BAYER8[y2 & 7][x2 & 7] + 0.5) / 64.0 - 0.5) * spread;
        rr = clamp255(rr + t); gg = clamp255(gg + t); bb = clamp255(bb + t);
      }
      idx[y2 * W + x2] = nearest(rr, gg, bb);
    }
    return idx;
  }

  // ---- 4bit 打包：高半字节=偶数列，低=奇数列；纯白整屏应为全 0x11 ----
  function packIndexed(idx) {
    var out = new Uint8Array((W * H) >> 1);
    for (var k = 0, n = W * H; k < n; k += 2)
      out[k >> 1] = ((idx[k] << 4) | (idx[k + 1] & 0x0F)) & 0xFF;
    return out;
  }

  function sliceEq(a, ao, b, bo, len) {
    for (var t = 0; t < len; t++) if (a[ao + t] !== b[bo + t]) return false;
    return true;
  }

  // ---- LZ77：窗口 1024，偏移 10bit，长度 Golomb m=3，字面量 9bit ----
  // 位序与 epd_send.py 一致：字节内 LSB 优先（bit p -> byte[p>>3] 的第 (p&7) 位）。
  function compress(data) {
    var n = data.length, out = new Uint8Array(n * 2 + 8), bitpos = 0, i = 0;
    var buckets = new Map();
    function setBit(p) { out[p >> 3] |= (1 << (p & 7)); }
    function remember(pos) {
      if (pos + 1 >= n) return;
      var key = (data[pos] << 8) | data[pos + 1], b = buckets.get(key);
      if (b === undefined) { buckets.set(key, [pos]); return; }
      b.push(pos);
      if (b.length > 128) {
        var cut = pos - MAX_WND, k = 0;
        while (k < b.length && b[k] < cut) k++;
        if (k > 0) b.splice(0, k);
      }
    }
    while (i < n) {
      var rel = i - MAX_WND, winStart, maxLen;
      if (rel >= 0) { winStart = rel; maxLen = MAX_WND; }
      else if (rel >= -MAX_WND) { winStart = 0; maxLen = MAX_WND + rel; }
      else { winStart = -1; maxLen = 0; }
      if (maxLen > n - i) maxLen = n - i;
      var best = 0, offset = 0;
      if (winStart >= 0 && i + 1 < n) {
        var bucket = buckets.get((data[i] << 8) | data[i + 1]);
        if (bucket) {
          var limit = winStart + maxLen, s = 0;
          while (s < bucket.length && bucket[s] < winStart) s++;
          for (; s < bucket.length; s++) {
            var p = bucket[s];
            if (p >= limit) break;
            var cap = limit - p;
            if (cap <= best) break;
            var probe = best + 1;
            if (!sliceEq(data, p, data, i, probe)) continue;
            var lo = probe, hi = cap;
            while (lo < hi) {
              var mid = (lo + hi + 1) >> 1;
              if (sliceEq(data, p, data, i, mid)) lo = mid; else hi = mid - 1;
            }
            best = lo; offset = p - winStart;
            if (best === cap) break;
          }
        }
      }
      if (best > 1) {
        setBit(bitpos); bitpos++;                                   // flag 1
        for (var b1 = 0; b1 < 10; b1++) { if ((offset >> b1) & 1) setBit(bitpos); bitpos++; }
        var x = best, qq = (x - 1) >> 3, rr2 = (x - (qq << 3)) - 1;
        for (var t1 = 0; t1 < qq; t1++) { setBit(bitpos); bitpos++; }   // Golomb q 个 1
        bitpos++;                                                      // 1 个 0
        for (var b2 = 0; b2 < 3; b2++) { if ((rr2 >> b2) & 1) setBit(bitpos); bitpos++; }
        for (var pos = i; pos < i + best; pos++) remember(pos);
        i += best;
      } else {
        bitpos++;                                                     // flag 0
        var c = data[i];
        for (var b3 = 0; b3 < 8; b3++) { if ((c >> b3) & 1) setBit(bitpos); bitpos++; }
        remember(i);
        i += 1;
      }
    }
    return { bytes: out.slice(0, (bitpos + 7) >> 3), bits: bitpos };
  }

  function decompress(buf, totalBits) {
    function bit(bp) { return (buf[bp >> 3] >> (bp & 7)) & 1; }
    var out = [], bp = 0;
    while (bp < totalBits) {
      if (bit(bp)) {
        bp += 1;
        var off = 0;
        for (var b = 0; b < 10; b++) { if (bit(bp)) off |= (1 << b); bp++; }
        var q = 0;
        while (bit(bp) === 1) { q += 1; bp++; }
        bp += 1;
        var r = 0;
        for (var b2 = 0; b2 < 3; b2++) { if (bit(bp)) r |= (1 << b2); bp++; }
        var length = (q << 3) + r + 1;
        var cur = out.length, ws = cur - MAX_WND > 0 ? cur - MAX_WND : 0, src = ws + off;
        for (var t = 0; t < length; t++) out.push(out[src + t]);
      } else {
        bp += 1;
        var c = 0;
        for (var b3 = 0; b3 < 8; b3++) { if (bit(bp)) c |= (1 << b3); bp++; }
        out.push(c);
      }
    }
    return new Uint8Array(out);
  }

  // ---- 自检：LZ77 往返 + 半字节序不变量（纯白整屏打包后应全为 0x11）----
  function selftest() {
    var cases = [], i;
    cases.push(new Uint8Array(0));
    cases.push(new Uint8Array([65]));
    var a4 = new Uint8Array(4); for (i = 0; i < 4; i++) a4[i] = 65; cases.push(a4);
    var ab = new Uint8Array(10); for (i = 0; i < 10; i++) ab[i] = (i & 1) ? 66 : 65; cases.push(ab);
    var r64 = new Uint8Array(64); for (i = 0; i < 64; i++) r64[i] = i; cases.push(r64);
    var r300 = new Uint8Array(300); for (i = 0; i < 300; i++) r300[i] = Math.floor(Math.random() * 16); cases.push(r300);
    var r1000 = new Uint8Array(1000); for (i = 0; i < 1000; i++) r1000[i] = Math.floor(Math.random() * 4); cases.push(r1000);
    var white = new Uint8Array(W * H); for (i = 0; i < white.length; i++) white[i] = 1;
    var wp = packIndexed(white), all11 = true;
    for (i = 0; i < wp.length; i++) if (wp[i] !== 0x11) { all11 = false; break; }
    var results = [], ok = true;
    for (i = 0; i < cases.length; i++) {
      var c = compress(cases[i]);
      var r = decompress(c.bytes, c.bits);
      var pass = r.length === cases[i].length && sliceEq(r, 0, cases[i], 0, r.length);
      if (!pass) ok = false;
      results.push({ name: 'case' + i + ' len=' + cases[i].length + ' bits=' + c.bits, pass: pass });
    }
    if (!all11) ok = false;
    results.push({ name: 'pure-white pack == 0x11 x192000', pass: all11 });
    return { ok: ok, results: results };
  }

  return {
    VERSION: '1.2.0',
    W: W, H: H, MAX_WND: MAX_WND, MAX_BITS: MAX_BITS, PALETTE: PALETTE, BAYER8: BAYER8,
    nearest: nearest, mt19937: mt19937, quantizeRGBA: quantizeRGBA, packIndexed: packIndexed,
    compress: compress, decompress: decompress, selftest: selftest
  };
});
