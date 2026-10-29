#pragma once
// 一张屏幕上要显示的全部数据。ESP32 只需这一份结构就能出整屏。
#include <stdint.h>

enum IconKind : uint8_t {
  ICON_UNKNOWN = 0,
  ICON_SUN,        // 晴
  ICON_SUN_CLOUD,  // 少云 / 晴间多云
  ICON_CLOUD,      // 多云
  ICON_OVERCAST,   // 阴
  ICON_DRIZZLE,    // 毛毛雨
  ICON_RAIN,       // 小/中雨、阵雨
  ICON_HEAVY_RAIN, // 大雨、暴雨
  ICON_SLEET,      // 冻雨、雨夹雪
  ICON_SNOW,       // 雪
  ICON_THUNDER,    // 雷阵雨
  ICON_FOG,        // 雾
  ICON_HAZE,       // 霾 / 沙尘
};

struct Weather {
  bool valid;
  int  y, mo, d, dow, hh, mi;  // 本地时间（dow: 0=周日）
  char city[40];               // UTF-8，需要出现在 tools/charset.txt 里
  int  temp, feels;            // 当前气温 / 体感（整度）
  int  code;                   // 当前 WMO 天气码
  int  hum, wind, pop;         // 湿度 % / 风速 km/h / 今日降水概率 %
  int  tmax, tmin;             // 今日最高/最低
  int  code2, tmax2, tmin2;    // 明天
  int  days;                   // 连续失败天数（>0 时页脚提示数据可能过期）
};

