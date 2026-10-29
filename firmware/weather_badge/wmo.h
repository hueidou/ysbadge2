#pragma once
// WMO weather code（Open-Meteo 用的那套）-> 图标 + 中文词。
#include "model.h"

IconKind wmo_icon(int code);
const char *wmo_text(int code);   // UTF-8；未收录返回 "未知"

