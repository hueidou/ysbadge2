#pragma once
// 1bpp 点阵字模接口。字模由 tools/gen_font.py 从系统 TTF 生成（font_data.cpp）。
#include <stdint.h>

struct Glyph {
  uint32_t cp;    // Unicode 码点
  uint32_t off;   // 位图在 font_pool 中的偏移（行优先，MSB 在左）
  uint8_t  w, h;  // 墨迹尺寸
  int8_t   x0, y0;// 墨迹相对"文字单元格左上角"的偏移（已含基线）
  uint8_t  adv;   // 步进宽度（含字间距）
};

struct Font {
  const Glyph  *glyphs;   // 按 cp 升序
  uint16_t      count;
  uint8_t       line_h;   // 行高（像素）
};

extern const Font font_120;  // 大号温度（数字/°/负号）
extern const Font font_44;   // 城市名 / 天气词 / 底部数值
extern const Font font_32;   // 正文
extern const Font font_22;   // 标签 / 页脚
extern const uint8_t font_pool[];

const Glyph *font_find(const Font &f, uint32_t cp);   // 未收录返回 nullptr
int font_width(const Font &f, const char *utf8);      // 只算宽度

// 极简 UTF-8 迭代：p 前进一个码点
static inline uint32_t utf8_next(const char *&p) {
  uint8_t c = (uint8_t)*p++;
  if (c < 0x80) return c;
  int n;
  uint32_t v;
  if ((c & 0xE0) == 0xC0) { n = 1; v = c & 0x1F; }
  else if ((c & 0xF0) == 0xE0) { n = 2; v = c & 0x0F; }
  else if ((c & 0xF8) == 0xF0) { n = 3; v = c & 0x07; }
  else return 0x3F;
  for (int i = 0; i < n; i++) {
    if (((uint8_t)*p & 0xC0) != 0x80) return 0x3F;
    v = (v << 6) | ((uint8_t)*p++ & 0x3F);
  }
  return v;
}

