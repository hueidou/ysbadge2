#include "wmo.h"

IconKind wmo_icon(int code) {
  if (code == 0) return ICON_SUN;
  if (code == 1) return ICON_SUN_CLOUD;
  if (code == 2) return ICON_CLOUD;
  if (code == 3) return ICON_OVERCAST;
  if (code == 45 || code == 48) return ICON_FOG;
  if (code >= 51 && code <= 57) return ICON_DRIZZLE;
  if (code == 66 || code == 67) return ICON_SLEET;
  if (code >= 61 && code <= 65) return (code >= 65) ? ICON_HEAVY_RAIN : ICON_RAIN;
  if (code == 80 || code == 81) return ICON_RAIN;
  if (code == 82) return ICON_HEAVY_RAIN;
  if (code >= 71 && code <= 77) return ICON_SNOW;
  if (code == 85 || code == 86) return ICON_SNOW;
  if (code >= 95) return ICON_THUNDER;
  if (code >= 96) return ICON_THUNDER;
  return ICON_UNKNOWN;
}

const char *wmo_text(int code) {
  switch (code) {
    case 0:  return "晴";
    case 1:  return "少云";
    case 2:  return "多云";
    case 3:  return "阴";
    case 45: case 48: return "雾";
    case 51: return "毛毛雨";
    case 53: case 55: return "毛毛雨";
    case 56: case 57: return "冻雨";
    case 61: return "小雨";
    case 63: return "中雨";
    case 65: return "大雨";
    case 66: case 67: return "冻雨";
    case 71: return "小雪";
    case 73: return "中雪";
    case 75: return "大雪";
    case 77: return "雪粒";
    case 80: return "阵雨";
    case 81: return "阵雨";
    case 82: return "暴雨";
    case 85: return "阵雪";
    case 86: return "阵雪";
    case 95: return "雷阵雨";
    case 96: case 99: return "雷暴";
    default: return "未知";
  }
}

