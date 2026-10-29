#pragma once
// 整屏排版：一次 ui_begin() 喂数据，之后可按任意顺序逐行取像素。
#include "model.h"
#include <stdint.h>

void ui_begin(const Weather &w);
void ui_row(int y, uint8_t *pix);            // pix 长度 800，内容是调色板索引 0..6
uint8_t ui_byte(uint32_t pos, void *ctx);    // LZ77 的取字节回调：pos -> 打包后的 4bit 字节
void ui_reset_cache();

