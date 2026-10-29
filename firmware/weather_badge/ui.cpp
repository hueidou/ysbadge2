#include "ui.h"
#include "canvas.h"
#include "icons.h"
#include "wmo.h"
#include "font.h"
#include <stdio.h>
#include <string.h>

static const int BLACK = 0, WHITE = 1, BLUE = 3, RED = 4, ORANGE = 6;

static Weather s_w;

void ui_begin(const Weather &w) { s_w = w; }

// 温度配色：偏冷蓝、常温橙、高温红——比统一用黑色更有"读一眼就知道"的感觉
static int temp_color(int t) {
  if (t <= 10) return BLUE;
  if (t <= 26) return ORANGE;
  return RED;
}

// 顶部：6px 橙色色条 + 日期 + 更新时间
static void draw_header(uint8_t *row, int y) {
  static const char *kDow[7] = {"周日", "周一", "周二", "周三", "周四", "周五", "周六"};
  cv_rect(row, y, 0, 0, UI_W - 1, 5, ORANGE);

  char buf[64];
  snprintf(buf, sizeof buf, "%d月%d日", s_w.mo, s_w.d);
  cv_text(row, y, 36, 24, font_32, buf, BLACK);
  int w = font_width(font_32, buf);
  cv_text(row, y, 36 + w + 14, 24, font_32, kDow[s_w.dow % 7], BLACK);

  snprintf(buf, sizeof buf, "%02d:%02d 更新", s_w.hh, s_w.mi);
  cv_text_right(row, y, 764, 32, font_22, buf, BLACK);
}


// 主体：左侧大图标，右侧城市 + 超大温度 + 天气词 + 一行体感/风/湿度
static void draw_main(uint8_t *row, int y) {
  icon_draw(wmo_icon(s_w.code), row, y, 152, 218, 102);

  // 城市左边的橙色竖条（视觉锚点）
  cv_rect(row, y, 318, 94, 323, 136, ORANGE);
  cv_text(row, y, 334, 92, font_44, s_w.city, BLACK);

  const int tc = temp_color(s_w.temp);
  char num[8];
  snprintf(num, sizeof num, "%d", s_w.temp);
  cv_text(row, y, 328, 148, font_120, num, tc);
  int nw = font_width(font_120, num);
  cv_text(row, y, 328 + nw - 2, 186, font_32, "°", tc);

  cv_text(row, y, 328 + nw + 46, 198, font_44, wmo_text(s_w.code), BLACK);

  // 三项小统计：小标签 + 大数值，比连成一长句更好扫读
  char v[24];
  cv_text(row, y, 334, 282, font_22, "体感", BLACK);
  snprintf(v, sizeof v, "%d°", s_w.feels);
  cv_text(row, y, 334, 306, font_32, v, BLACK);

  cv_text(row, y, 470, 282, font_22, "风", BLACK);
  snprintf(v, sizeof v, "%dkm/h", s_w.wind);
  cv_text(row, y, 470, 306, font_32, v, BLACK);

  cv_text(row, y, 634, 282, font_22, "湿度", BLACK);
  snprintf(v, sizeof v, "%d%%", s_w.hum);
  cv_text(row, y, 634, 306, font_32, v, BLACK);
}


// 底部：今日 / 明天 两栏，标签用彩色小字、数值用大字
static void draw_bottom(uint8_t *row, int y) {
  cv_rect(row, y, 36, 356, 764, 357, BLACK);       // 分割线
  cv_rect(row, y, 399, 370, 400, 452, BLACK);      // 竖分隔

  char a[64], b[64];
  cv_text(row, y, 36, 370, font_22, "今日", BLUE);
  snprintf(a, sizeof a, "%d°~%d°", s_w.tmin, s_w.tmax);
  cv_text(row, y, 36, 398, font_44, a, temp_color(s_w.tmax));

  cv_text(row, y, 420, 370, font_22, "明天", ORANGE);
  const char *w2 = wmo_text(s_w.code2);
  cv_text(row, y, 420, 398, font_44, w2, BLACK);
  snprintf(b, sizeof b, "%d°~%d°", s_w.tmin2, s_w.tmax2);
  cv_text(row, y, 420 + font_width(font_44, w2) + 14, 398, font_44, b, temp_color(s_w.tmax2));

  if (s_w.days > 0) {
    char c[40];
    snprintf(c, sizeof c, "数据已 %d 天未更新", s_w.days);
    cv_text_right(row, y, 764, 440, font_22, c, RED);
  }
}

void ui_row(int y, uint8_t *pix) {
  cv_clear_row(pix, WHITE);
  if (y < 0 || y >= UI_H) return;
  draw_header(pix, y);
  draw_main(pix, y);
  draw_bottom(pix, y);
}

// ---- LZ77 取字节回调：按行缓存 8 行，覆盖 1024B 前视/回看 ----

#define ROW_BYTES (UI_W / 2)
#define CACHE_ROWS 8

static uint8_t s_cache[CACHE_ROWS][UI_W];
static int16_t s_cache_row[CACHE_ROWS];

void ui_reset_cache() {
  for (int i = 0; i < CACHE_ROWS; i++) s_cache_row[i] = -1;
}

uint8_t ui_byte(uint32_t pos, void *ctx) {
  (void)ctx;
  uint32_t r = pos / ROW_BYTES;
  uint32_t c = pos % ROW_BYTES;
  uint8_t *p = s_cache[r % CACHE_ROWS];
  if (s_cache_row[r % CACHE_ROWS] != (int16_t)r) {
    ui_row((int)r, p);
    s_cache_row[r % CACHE_ROWS] = (int16_t)r;
  }
  return (uint8_t)((p[c * 2] << 4) | (p[c * 2 + 1] & 0x0F));
}

