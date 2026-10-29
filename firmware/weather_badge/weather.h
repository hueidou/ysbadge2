#pragma once
// 取 Open-Meteo 数据并填 Weather 结构（免 API key）。
// 依赖：WiFi 已连接、时间已通过 NTP 同步（填日期/时间用）。
#include "model.h"

// 返回是否成功；失败时 w.valid=false，日志里有原因
bool weather_fetch(Weather &w);

// 同步 NTP（返回是否成功）
bool weather_sync_time();

