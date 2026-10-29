// YSBadge2 天气喂图器（ESP32-C3 / 合宙 AirM2M CORE-ESP32C3 + Arduino）
// 每天 PUSH_HOUR:PUSH_MIN（默认 6:00）：取 Open-Meteo 天气 -> 画 800x480 七色图
// -> LZ77 压缩 -> BLE 投给胸牌 -> 深睡到次日。
// 协议与体积上限见 docs/PROTOCOL.md；ESP32 端的取舍见 docs/ESP32_WEATHER.md。
#include <Arduino.h>
#include <WiFi.h>
#include <time.h>
#include <esp_sleep.h>
#include "config.h"
#include "model.h"
#include "ui.h"
#include "lz77.h"
#include "weather.h"
#include "epd_ble.h"

#define MAX_OUT_BYTES (36 * 1024)          // 设备上限 262144 bit（32KB），留余量便于判超限

static uint8_t s_out[MAX_OUT_BYTES] __attribute__((aligned(4)));
static Weather s_w;

#if !POWER_SAVE
static uint32_t s_next_at_ms = 0;
#endif

static bool wifi_connect() {
  if (WiFi.status() == WL_CONNECTED) return true;
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.printf("[wifi] 连接 %s", WIFI_SSID);
  for (int i = 0; i < 40; i++) {          // 最多 20s
    if (WiFi.status() == WL_CONNECTED) {
      Serial.printf("\n[wifi] 已连 %s rssi=%d\n",
                    WiFi.localIP().toString().c_str(), (int)WiFi.RSSI());
      return true;
    }
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[wifi] 失败");
  return false;
}

static void wifi_off() {
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  delay(200);
}


// 一次完整投图：取数 -> 排版 -> 压缩 -> BLE。返回 false 表示这一轮失败（可重试）
static bool push_once() {
  if (!wifi_connect()) return false;
  if (!weather_sync_time()) { wifi_off(); return false; }
  if (!weather_fetch(s_w)) { wifi_off(); return false; }
  wifi_off();                    // 先关 WiFi：BLE 单独占射频，也把 RAM 让出来

  ui_begin(s_w);
  ui_reset_cache();
  memset(s_out, 0, sizeof s_out);
  uint32_t t0 = millis();
  Lz77Result r = lz77_compress(800u * 480u / 2u, ui_byte, nullptr, s_out, sizeof s_out);
  Serial.printf("[lz] %u bit = %d B (%.1f%% / 192000 B), 耗时 %u ms\n",
                (unsigned)r.bits, (int)r.bytes,
                100.0f * (float)r.bytes / 192000.0f, (unsigned)(millis() - t0));
  if (r.overflow) {
    Serial.println("[lz] 输出缓冲不够，拒绝发送");
    return false;
  }
  if (r.bits > 262144) {
    Serial.printf("[lz] %u bit 超设备上限 262144 bit，拒绝发送\n", (unsigned)r.bits);
    return false;
  }
  return epd_push(s_out, r.bits, EPD_INDEX);
}

// 距离下一个 PUSH_HOUR:PUSH_MIN（本地时间）还有多少秒；时间没同步就按重试间隔
static uint32_t secs_to_next() {
  time_t now = time(nullptr);
  if (now < 1700000000) return RETRY_MINUTES * 60;
  struct tm t;
  time_t local = now + TZ_OFFSET_SEC;
  gmtime_r(&local, &t);
  int32_t s = (PUSH_HOUR * 3600 + PUSH_MIN * 60) -
              (t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec);
  if (s <= 30) s += 24 * 3600;      // 今天这个点已过，排到明天
  return (uint32_t)s;
}

static bool run_with_retry(int tries) {
  for (int i = 0; i < tries; i++) {
    if (push_once()) return true;
    Serial.printf("[retry] 第 %d/%d 次失败\n", i + 1, tries);
    delay(5000);
  }
  return false;
}


void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(300);
  Serial.println();
  Serial.println("=== YSBadge2 天气喂图器 ===");
  Serial.printf("[boot] %s rev%d, flash %u MB, 空闲堆 %u B\n",
                ESP.getChipModel(), (int)ESP.getChipRevision(),
                (unsigned)(ESP.getFlashChipSize() / (1024 * 1024)),
                (unsigned)ESP.getFreeHeap());

  // 串口在 SERIAL_FORCE_MS 内收到任意字符 = 立刻投一张（调试用，不用等到 6:00）
  bool forced = false;
  uint32_t t_wait = millis();
  while (millis() - t_wait < SERIAL_FORCE_MS) {
    if (Serial.available()) { Serial.read(); forced = true; break; }
    delay(20);
  }
  if (forced) Serial.println("[boot] 串口触发：立即投图");

  bool ok = run_with_retry(forced ? 1 : MAX_RETRY);
  Serial.println(ok ? "[done] 已发出" : "[done] 本轮失败");

  uint32_t wait_s = ok ? secs_to_next() : (uint32_t)(RETRY_MINUTES * 60);
#if POWER_SAVE
  Serial.printf("[sleep] 深睡 %u s（约 %.1f 小时）后醒来\n", (unsigned)wait_s, wait_s / 3600.0f);
  Serial.flush();
  esp_sleep_enable_timer_wakeup((uint64_t)wait_s * 1000000ULL);
  esp_deep_sleep_start();
#else
  s_next_at_ms = millis() + wait_s * 1000UL;
  Serial.printf("[sched] 下一次在 %u s 后\n", (unsigned)wait_s);
#endif
}

void loop() {
#if POWER_SAVE
  delay(1000);            // 深睡模式下走不到这里
#else
  if ((int32_t)(millis() - s_next_at_ms) >= 0) {
    bool ok = run_with_retry(MAX_RETRY);
    uint32_t wait_s = ok ? secs_to_next() : (uint32_t)(RETRY_MINUTES * 60);
    s_next_at_ms = millis() + wait_s * 1000UL;
    Serial.printf("[sched] 下一次在 %u s 后\n", (unsigned)wait_s);
  }
  delay(1000);
#endif
}

