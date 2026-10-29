#include "font.h"
#include "font_data.h"

const Glyph *font_find(const Font &f, uint32_t cp) {
  uint16_t lo = 0, hi = f.count;          // 字模表由生成器按 cp 升序排列
  while (lo < hi) {
    uint16_t mid = (uint16_t)((lo + hi) >> 1);
    if (f.glyphs[mid].cp < cp) lo = (uint16_t)(mid + 1);
    else hi = mid;
  }
  if (lo < f.count && f.glyphs[lo].cp == cp) return &f.glyphs[lo];
  return nullptr;
}

int font_width(const Font &f, const char *utf8) {
  int w = 0;
  const char *p = utf8;
  while (*p) {
    uint32_t cp = utf8_next(p);
    if (cp == ' ') { w += f.line_h / 3; continue; }
    const Glyph *g = font_find(f, cp);
    w += g ? g->adv : f.line_h / 2;
  }
  return w;
}
