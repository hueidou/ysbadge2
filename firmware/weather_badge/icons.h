#pragma once
#include "model.h"
#include <stdint.h>

// 在行 row 上画 7 色面板图标，中心 (cx,cy)、半径 r（约 108 像素最合适）。
void icon_draw(IconKind k, uint8_t *row, int y, int cx, int cy, int r);

