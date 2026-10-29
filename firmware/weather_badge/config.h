#pragma once
// ================= 用户配置：只需要改这个文件 =================
// WiFi（仅支持 2.4GHz；ESP32-C3 不支持 5G）
// 真实凭据放 secrets.h（已被 .gitignore 忽略），这里给的是占位值
#if __has_include("secrets.h")
#include "secrets.h"
#endif
#ifndef WIFI_SSID
#define WIFI_SSID   "your-ssid"
#endif
#ifndef WIFI_PASS
#define WIFI_PASS   "your-password"
#endif

// 位置：纬度、经度（十进制度，南纬/西经为负）。北京 39.9042 / 116.4074
#define LATITUDE    39.9042f
#define LONGITUDE   116.4074f
#define TIMEZONE    "Asia/Shanghai"
#define TZ_OFFSET_SEC (8 * 3600)      // 东八区；NTP 用 UTC+偏移换算本地时间
#define CITY_NAME   "北京"             // 每个字都要在 tools/charset.txt 里，否则会显示为空白

// 投图
#define EPD_MAC     "EE:96:BB:1E:05:28"   // 胸牌 MAC（A 面 index 1 / B 面 2 / 双面 3 / 双面异显 7）
#define EPD_INDEX   1                     // 1=A 面，2=B 面，3=双面同显
#define EPD_NAME    ""                    // 可选：按广播名匹配（留空则按 MAC）

// 每天几点投图（本地时间，24 小时制）
#define PUSH_HOUR   6
#define PUSH_MIN    0

// 1 = 投完进深睡，第二天到点再醒（推荐，功耗 ~10uA）
// 0 = 一直醒着用 millis 等下一次（调试用，串口能一直看到日志）
#define POWER_SAVE  1

// 连不上时：浅睡 10 分钟重试几次，再放弃等明天
#define RETRY_MINUTES 10
#define MAX_RETRY     3

// BLE 分块间隔：实测 40ms 最稳；如果经常丢数据可以调大
#define CHUNK_DELAY_MS 40

// 串口波特率
#define SERIAL_BAUD 115200

// 上电后 3 秒内在串口敲任意字符 = 立刻投一张（调试用）。
// 注意：不要用 GPIO9(BOOT) 做按键——它是 strapping 脚，按住上电会进下载模式。
#define SERIAL_FORCE_MS 3000

