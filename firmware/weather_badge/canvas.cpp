#include "canvas.h"
#include <math.h>
#include <string.h>

static inline void dot(uint8_t *row, int x, int color) {
  if (x >= 0 && x < UI_W) row[x] = (uint8_t)color;
}

void cv_clear_row(uint8_t *row, int color) { memset(row, color, UI_W); }

void cv_hline(uint8_t *row, int y, int x0, int x1, int color) {
  if (y < 0 || y >= UI_H) return;
  if (x0 > x1) { int t = x0; x0 = x1; x1 = t; }
  if (x0 < 0) x0 = 0;
  if (x1 > UI_W - 1) x1 = UI_W - 1;
  for (int x = x0; x <= x1; x++) row[x] = (uint8_t)color;
}

void cv_rect(uint8_t *row, int y, int x0, int y0, int x1, int y1, int color) {
  if (y < y0 || y > y1) return;
  cv_hline(row, y, x0, x1, color);
}

void cv_circle(uint8_t *row, int y, int cx, int cy, int r, int color) {
  int dy = y - cy;
  if (dy < -r || dy > r) return;
  int dx = (int)sqrtf((float)(r * r - dy * dy));
  for (int x = cx - dx; x <= cx + dx; x++) dot(row, x, color);
}

void cv_ring(uint8_t *row, int y, int cx, int cy, int r, int thick, int color) {
  for (int i = 0; i < thick; i++) {
    int rr = r - i;
    int dy = y - cy;
    if (rr <= 0 || dy < -rr || dy > rr) continue;
    int dx = (int)sqrtf((float)(rr * rr - dy * dy));
    dot(row, cx - dx, color);
    dot(row, cx + dx, color);
  }
}


void cv_seg(uint8_t *row, int y, int x0, int y0, int x1, int y1, int thick, int color) {
  int dx = x1 - x0, dy = y1 - y0;
  int steps = (abs(dx) > abs(dy)) ? abs(dx) : abs(dy);
  if (steps <= 0) { dot(row, x0, color); return; }
  for (int t = 0; t < thick; t++) {
    for (int s = 0; s <= steps; s++) {
      int px = x0 + dx * s / steps;
      int py = y0 + dy * s / steps + t;
      if (py == y) dot(row, px, color);
    }
  }
}

void cv_text(uint8_t *row, int y, int x, int ytop, const Font &f, const char *utf8, int color) {
  int pen = x;
  const char *p = utf8;
  while (*p) {
    uint32_t cp = utf8_next(p);
    if (cp == ' ') { pen += f.line_h / 3; continue; }
    const Glyph *g = font_find(f, cp);
    if (!g) { pen += f.line_h / 2; continue; }
    int gy = y - (ytop + g->y0);
    if (gy >= 0 && gy < g->h) {
      int stride = (g->w + 7) >> 3;
      const uint8_t *bits = font_pool + g->off + gy * stride;
      for (int bx = 0; bx < g->w; bx++) {
        if (bits[bx >> 3] & (0x80 >> (bx & 7))) dot(row, pen + g->x0 + bx, color);
      }
    }
    pen += g->adv;
  }
}

void cv_text_right(uint8_t *row, int y, int x_right, int ytop, const Font &f, const char *utf8, int color) {
  cv_text(row, y, x_right - font_width(f, utf8), ytop, f, utf8, color);
}

