#include "lz77.h"
#include <string.h>

namespace {

// 与 Python 侧一致的常量：窗口 1024、单次匹配上限也是 1024（cap = win_start + maxlen - p）。
constexpr uint32_t WIN       = 1024;
constexpr uint32_t MAX_MATCH = 1024;
constexpr uint32_t MIN_MATCH = 2;
constexpr uint32_t NO_POS    = 0xFFFFFFFFu;

constexpr int HASH_BITS = 11;                 // 2048 桶
constexpr int HASH_SIZE = 1 << HASH_BITS;
constexpr int SLOTS     = 2;                  // 每桶保留最近两个候选

uint32_t s_slot[HASH_SIZE][SLOTS];            // 16 KB
uint32_t s_epos = 0;                          // 测试用：记录已插入位置数（避免未使用告警）

struct Writer {
  uint8_t *out;
  uint32_t cap;
  uint32_t bp;
  bool ovf;

  inline void bit(uint32_t v) {
    if ((bp >> 3) >= cap) { ovf = true; bp++; return; }
    if (v) out[bp >> 3] = (uint8_t)(out[bp >> 3] | (uint8_t)(1u << (7 & bp)));
    bp++;
  }
  inline void bits(uint32_t v, int n) {     // LSB 优先
    for (int i = 0; i < n; i++) bit((v >> i) & 1u);
  }
};

inline uint32_t hash2(uint8_t a, uint8_t b) {
  uint32_t k = ((uint32_t)a << 8) | b;
  k *= 2654435761u;
  return (k >> 21) & (HASH_SIZE - 1);
}

}  // namespace

Lz77Result lz77_compress(uint32_t total, lz77_src_fn src, void *ctx,
                         uint8_t *out, uint32_t out_cap) {
  memset(s_slot, 0xFF, sizeof(s_slot));
  Writer w{out, out_cap, 0, false};

  auto at = [&](uint32_t p) -> uint8_t { return src(p, ctx); };
  auto insert = [&](uint32_t p) {
    if (p + 1 >= total) return;
    uint32_t h = hash2(at(p), at(p + 1));
    s_slot[h][1] = s_slot[h][0];
    s_slot[h][0] = p;
    s_epos++;
  };

  uint32_t i = 0;
  while (i < total) {
    uint32_t win_start = (i > WIN) ? (i - WIN) : 0;
    uint32_t maxlen    = WIN;
    if (maxlen > total - i) maxlen = total - i;

    uint32_t best = 0, offset = 0;

    if (i + 1 < total && maxlen >= MIN_MATCH) {
      uint32_t h = hash2(at(i), at(i + 1));
      for (int s = 0; s < SLOTS; s++) {
        uint32_t p = s_slot[h][s];
        if (p == NO_POS || p >= i) continue;
        if (i - p > WIN) continue;                   // 超出窗口，直接丢弃
        // 先按 best 快速否掉，再逐字节扩展（与 Python 的二分等价，只是这里线性）
        if (best >= maxlen) break;
        uint32_t len = 0;
        uint32_t cap = maxlen;
        if (best + 1 > cap) cap = best + 1;          // 只关心能否超过 best
        while (len < cap && at(p + len) == at(i + len)) len++;
        if (len > best) { best = len; offset = p - win_start; }
      }
    }

    if (w.ovf) break;

    if (best >= MIN_MATCH) {
      w.bit(1);
      w.bits(offset, 10);
      uint32_t x = best - 1;
      uint32_t q = x >> 3;
      uint32_t r = x - (q << 3);
      for (uint32_t k = 0; k < q; k++) w.bit(1);
      w.bit(0);
      w.bits(r, 3);
      for (uint32_t k = 0; k < best; k++) insert(i + k);
      i += best;
    } else {
      w.bit(0);
      w.bits(at(i), 8);
      insert(i);
      i++;
    }
  }

  Lz77Result res;
  res.bits     = w.bp;
  res.bytes    = (int32_t)((w.bp + 7) >> 3);
  res.overflow = w.ovf;
  return res;
}
