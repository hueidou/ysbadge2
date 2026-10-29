#include "icons.h"
#include "canvas.h"

// 统一风格：实心剪影 + 粗笔触。1bpp 下描边会碎，实心块最清楚。
static const int BLACK = 0, WHITE = 1, BLUE = 3, YELLOW = 5, ORANGE = 6;

// 云的实心剪影：底座矩形 + 三个圆，圆决定外轮廓
static void cloud_fill(uint8_t *row, int y, int cx, int cy, int r, int color) {
  cv_rect(row, y, cx - r * 62 / 100, cy + r * 6 / 100, cx + r * 62 / 100, cy + r * 44 / 100, color);
  cv_circle(row, y, cx - r * 42 / 100, cy + r * 4 / 100, r * 40 / 100, color);
  cv_circle(row, y, cx - r * 2 / 100, cy - r * 20 / 100, r * 50 / 100, color);
  cv_circle(row, y, cx + r * 40 / 100, cy - r * 2 / 100, r * 36 / 100, color);
}

static void cloud(uint8_t *row, int y, int cx, int cy, int r) {
  cloud_fill(row, y, cx, cy, r, BLACK);
}

// 云外留一圈白，用于"压在太阳前面"时把两者分开
static void cloud_over(uint8_t *row, int y, int cx, int cy, int r) {
  cloud_fill(row, y, cx, cy, r + 7, WHITE);
  cloud_fill(row, y, cx, cy, r, BLACK);
}

static void sun(uint8_t *row, int y, int cx, int cy, int r, bool rays) {
  if (rays) {
    static const int ang[8][2] = {{100, 0}, {71, 71}, {0, 100}, {-71, 71},
                                  {-100, 0}, {-71, -71}, {0, -100}, {71, -71}};
    for (int i = 0; i < 8; i++) {
      int ax = cx + ang[i][0] * r * 96 / 10000;
      int ay = cy + ang[i][1] * r * 96 / 10000;
      int bx = cx + ang[i][0] * r * 64 / 10000;
      int by = cy + ang[i][1] * r * 64 / 10000;
      cv_seg(row, y, bx, by, ax, ay, r / 14 + 2, ORANGE);
    }
  }
  cv_circle(row, y, cx, cy, r * 48 / 100, BLACK);            // 黑底 + 黄心 = 连续的黑描边
  cv_circle(row, y, cx, cy, r * 48 / 100 - 3, YELLOW);
}

static void drops(uint8_t *row, int y, int cx, int cy, int r, int n, int len, int color) {
  for (int i = 0; i < n; i++) {
    int x = cx - r * 62 / 100 + (n > 1 ? i * (r * 124 / 100) / (n - 1) : 0);
    cv_seg(row, y, x, cy, x - len / 3, cy + len, 6, color);
  }
}

static void flake(uint8_t *row, int y, int cx, int cy, int r, int color) {
  cv_seg(row, y, cx - r, cy, cx + r, cy, 4, color);
  cv_seg(row, y, cx - r * 7 / 10, cy - r * 7 / 10, cx + r * 7 / 10, cy + r * 7 / 10, 4, color);
  cv_seg(row, y, cx - r * 7 / 10, cy + r * 7 / 10, cx + r * 7 / 10, cy - r * 7 / 10, 4, color);
}


void icon_draw(IconKind k, uint8_t *row, int y, int cx, int cy, int r) {
  switch (k) {
    case ICON_SUN:
      sun(row, y, cx, cy, r, true);
      break;
    case ICON_SUN_CLOUD:            // 少云：大太阳 + 小云
      sun(row, y, cx - r * 22 / 100, cy - r * 24 / 100, r * 64 / 100, true);
      cloud_over(row, y, cx + r * 16 / 100, cy + r * 20 / 100, r * 58 / 100);
      break;
    case ICON_CLOUD:                // 多云：太阳被大云挡一半
      sun(row, y, cx - r * 30 / 100, cy - r * 32 / 100, r * 52 / 100, true);
      cloud_over(row, y, cx + r * 10 / 100, cy + r * 18 / 100, r * 74 / 100);
      break;
    case ICON_OVERCAST:             // 阴：只有厚厚的云
      cloud(row, y, cx, cy, r * 94 / 100);
      break;
    case ICON_DRIZZLE:
      cloud(row, y, cx, cy - r * 16 / 100, r * 80 / 100);
      drops(row, y, cx, cy + r * 34 / 100, r * 58 / 100, 3, r / 5, BLUE);
      break;
    case ICON_RAIN:
      cloud(row, y, cx, cy - r * 20 / 100, r * 84 / 100);
      drops(row, y, cx, cy + r * 30 / 100, r * 62 / 100, 4, r * 30 / 100, BLUE);
      break;
    case ICON_HEAVY_RAIN:
      cloud(row, y, cx, cy - r * 26 / 100, r * 84 / 100);
      drops(row, y, cx, cy + r * 22 / 100, r * 68 / 100, 5, r * 42 / 100, BLUE);
      break;
    case ICON_SLEET:
      cloud(row, y, cx, cy - r * 22 / 100, r * 82 / 100);
      drops(row, y, cx - r * 24 / 100, cy + r * 26 / 100, r * 44 / 100, 2, r * 26 / 100, BLUE);
      flake(row, y, cx + r * 36 / 100, cy + r * 44 / 100, r * 17 / 100, BLUE);
      break;
    case ICON_SNOW:
      cloud(row, y, cx, cy - r * 24 / 100, r * 82 / 100);
      flake(row, y, cx - r * 32 / 100, cy + r * 40 / 100, r * 16 / 100, BLUE);
      flake(row, y, cx + r * 2 / 100, cy + r * 46 / 100, r * 16 / 100, BLUE);
      flake(row, y, cx + r * 36 / 100, cy + r * 40 / 100, r * 16 / 100, BLUE);
      break;
    case ICON_THUNDER:
      cloud(row, y, cx, cy - r * 26 / 100, r * 82 / 100);
      // 闪电：黑粗线打底再压黄线，白底上也看得清
      cv_seg(row, y, cx + r * 12 / 100, cy + r * 2 / 100, cx - r * 12 / 100, cy + r * 34 / 100, 18, BLACK);
      cv_seg(row, y, cx - r * 12 / 100, cy + r * 34 / 100, cx + r * 10 / 100, cy + r * 35 / 100, 14, BLACK);
      cv_seg(row, y, cx + r * 10 / 100, cy + r * 34 / 100, cx - r * 16 / 100, cy + r * 74 / 100, 14, BLACK);
      cv_seg(row, y, cx + r * 10 / 100, cy + r * 4 / 100, cx - r * 11 / 100, cy + r * 32 / 100, 10, YELLOW);
      cv_seg(row, y, cx - r * 10 / 100, cy + r * 32 / 100, cx + r * 8 / 100, cy + r * 33 / 100, 7, YELLOW);
      cv_seg(row, y, cx + r * 9 / 100, cy + r * 33 / 100, cx - r * 14 / 100, cy + r * 70 / 100, 7, YELLOW);
      break;
    case ICON_FOG:
      sun(row, y, cx - r * 10 / 100, cy - r * 34 / 100, r * 40 / 100, false);
      for (int i = 0; i < 3; i++) {
        int w = r * ((i == 1) ? 78 : 92) / 100;
        cv_rect(row, y, cx - w, cy + r * 6 / 100 + i * r * 26 / 100,
                cx + w, cy + r * 6 / 100 + i * r * 26 / 100 + r / 10, BLACK);
      }
      break;
    case ICON_HAZE:
      for (int i = 0; i < 4; i++) {
        int w = r * ((i % 2) ? 76 : 90) / 100;
        cv_rect(row, y, cx - w, cy - r * 40 / 100 + i * r * 26 / 100,
                cx + w, cy - r * 40 / 100 + i * r * 26 / 100 + r / 12 + 2, BLACK);
      }
      break;
    default:
      cv_circle(row, y, cx, cy, r * 44 / 100, BLACK);
      cv_circle(row, y, cx, cy, r * 44 / 100 - 8, WHITE);
      cv_rect(row, y, cx - r * 5 / 100, cy - r * 26 / 100, cx + r * 5 / 100, cy + r * 6 / 100, BLACK);
      cv_circle(row, y, cx, cy + r * 22 / 100, r * 7 / 100, BLACK);
      break;
  }
}

