#pragma once
// 行缓冲绘图原语：所有函数只在"当前行 y"落笔，供逐行生成整屏使用。
// 画布是 800x480 的调色板索引缓冲（0 黑 1 白 2 绿 3 蓝 4 红 5 黄 6 橙）。
#include <stdint.h>
#include "font.h"

#define UI_W 800
#define UI_H 480

void cv_clear_row(uint8_t *row, int color);
void cv_hline(uint8_t *row, int y, int x0, int x1, int color);
void cv_rect(uint8_t *row, int y, int x0, int y0, int x1, int y1, int color);
void cv_circle(uint8_t *row, int y, int cx, int cy, int r, int color);
void cv_ring(uint8_t *row, int y, int cx, int cy, int r, int thick, int color);
void cv_seg(uint8_t *row, int y, int x0, int y0, int x1, int y1, int thick, int color);
void cv_text(uint8_t *row, int y, int x, int ytop, const Font &f, const char *utf8, int color);
void cv_text_right(uint8_t *row, int y, int x_right, int ytop, const Font &f, const char *utf8, int color);

