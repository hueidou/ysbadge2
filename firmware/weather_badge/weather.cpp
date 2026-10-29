#include "weather.h"
#include "wmo.h"
#include "config.h"
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <time.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

// ---- 极简 JSON 取值（不引第三方库，只认 open-meteo 这套固定结构）----
static const char *find_key(const char *js, const char *key) {
  char pat[48];
  snprintf(pat, sizeof pat, "\"%s\":", key);
  return strstr(js, pat);
}

// 从 from 开始找 "key": 后的第 idx 个数字；from 要指到 "current":{ 或 "daily":{ 之后，
// 否则会先命中 current_units 里的 "temperature_2m":"°C" 这种字符串。
static bool json_num(const char *from, const char *key, int idx, float *out) {
  const char *p = find_key(from, key);
  if (!p) return false;
  p += strlen(key) + 3;
  if (*p == '[') {
    p++;
    for (int i = 0; i < idx; i++) {
      const char *comma = strchr(p, ',');
      if (!comma) return false;
      p = comma + 1;
    }
  } else if (idx != 0) {
    return false;
  }
  if (*p == 'n') return false;
  char *end = nullptr;
  double v = strtod(p, &end);
  if (end == p) return false;
  *out = (float)v;
  return true;
}

static int roundi(float v) { return (int)lroundf(v); }

bool weather_sync_time() {
  configTime(0, 0, "ntp.aliyun.com", "ntp.tencent.com", "pool.ntp.org");
  for (int i = 0; i < 40; i++) {          // 最多 20s
    time_t now = time(nullptr);
    if (now > 1700000000) {
      struct tm tmv;
      time_t local = now + TZ_OFFSET_SEC;
      gmtime_r(&local, &tmv);
      Serial.printf("[time] %04d-%02d-%02d %02d:%02d:%02d (UTC%+d)\n",
                    tmv.tm_year + 1900, tmv.tm_mon + 1, tmv.tm_mday,
                    tmv.tm_hour, tmv.tm_min, tmv.tm_sec, TZ_OFFSET_SEC / 3600);
      return true;
    }
    delay(500);
  }
  Serial.println("[time] NTP 同步失败");
  return false;
}


static bool http_get_body(const char *host, const char *path, char *body, size_t cap) {
  WiFiClientSecure cl;
  cl.setInsecure();                      // 只读公开天气数据，不做证书校验
  cl.setTimeout(15000);
  if (!cl.connect(host, 443)) {
    Serial.printf("[http] 连接 %s 失败\n", host);
    return false;
  }
  cl.printf("GET %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: YSBadge2-ESP32\r\n"
            "Accept: application/json\r\nConnection: close\r\n\r\n", path, host);

  static char raw[4096];
  size_t n = 0;
  uint32_t t0 = millis();
  while (millis() - t0 < 20000) {
    while (cl.available() && n < sizeof(raw) - 1) raw[n++] = (char)cl.read();
    if (!cl.connected() && !cl.available()) break;
    if (n >= sizeof(raw) - 1) break;
    delay(10);
  }
  cl.stop();
  raw[n] = 0;
  if (n == 0) { Serial.println("[http] 空响应"); return false; }

  char *b = strstr(raw, "\r\n\r\n");
  if (!b || strncmp(raw, "HTTP/1.1 200", 12) != 0) {
    Serial.printf("[http] 响应异常: %.40s\n", raw);
    return false;
  }
  b += 4;
  size_t blen = n - (size_t)(b - raw);
  if (blen >= cap) blen = cap - 1;
  memcpy(body, b, blen);
  body[blen] = 0;
  Serial.printf("[http] body %u B\n", (unsigned)blen);
  return true;
}


bool weather_fetch(Weather &w) {
  static char path[384];
  snprintf(path, sizeof path,
           "/v1/forecast?latitude=%.4f&longitude=%.4f"
           "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
           "weather_code,wind_speed_10m"
           "&daily=weather_code,temperature_2m_max,temperature_2m_min,"
           "precipitation_probability_max"
           "&timezone=%s&forecast_days=2",
           (double)LATITUDE, (double)LONGITUDE, TIMEZONE);

  static char body[3072];
  if (!http_get_body("api.open-meteo.com", path, body, sizeof body)) return false;

  const char *pcur = strstr(body, "\"current\":{");
  const char *pday = strstr(body, "\"daily\":{");
  if (!pcur || !pday) {
    Serial.println("[json] 缺 current/daily 对象");
    return false;
  }

  float temp, feels, hum, wind, code, pop0, tmax0, tmin0, dcode1, tmax1, tmin1;
  if (!json_num(pcur, "temperature_2m", 0, &temp) ||
      !json_num(pcur, "weather_code", 0, &code)) {
    Serial.println("[json] current 字段缺失");
    return false;
  }
  if (!json_num(pday, "temperature_2m_max", 0, &tmax0) ||
      !json_num(pday, "temperature_2m_min", 0, &tmin0)) {
    Serial.println("[json] daily 字段缺失");
    return false;
  }
  if (!json_num(pcur, "apparent_temperature", 0, &feels)) feels = temp;
  if (!json_num(pcur, "relative_humidity_2m", 0, &hum)) hum = 0;
  if (!json_num(pcur, "wind_speed_10m", 0, &wind)) wind = 0;
  if (!json_num(pday, "precipitation_probability_max", 0, &pop0)) pop0 = -1;
  if (!json_num(pday, "weather_code", 1, &dcode1)) dcode1 = code;
  if (!json_num(pday, "temperature_2m_max", 1, &tmax1)) tmax1 = tmax0;
  if (!json_num(pday, "temperature_2m_min", 1, &tmin1)) tmin1 = tmin0;

  memset(&w, 0, sizeof w);
  w.valid = true;
  w.temp  = roundi(temp);
  w.feels = roundi(feels);
  w.code  = roundi(code);
  w.hum   = roundi(hum);
  w.wind  = roundi(wind);
  w.pop   = pop0 < 0 ? 0 : roundi(pop0);
  w.tmax  = roundi(tmax0);
  w.tmin  = roundi(tmin0);
  w.code2 = roundi(dcode1);
  w.tmax2 = roundi(tmax1);
  w.tmin2 = roundi(tmin1);
  strncpy(w.city, CITY_NAME, sizeof(w.city) - 1);

  time_t now = time(nullptr) + TZ_OFFSET_SEC;
  struct tm tmv;
  gmtime_r(&now, &tmv);
  w.y = tmv.tm_year + 1900;
  w.mo = tmv.tm_mon + 1;
  w.d = tmv.tm_mday;
  w.dow = tmv.tm_wday;
  w.hh = tmv.tm_hour;
  w.mi = tmv.tm_min;

  Serial.printf("[weather] %s %d度 %s 今日 %d~%d 降水 %d%% 风 %d 湿度 %d\n",
                w.city, w.temp, wmo_text(w.code), w.tmin, w.tmax, w.pop, w.wind, w.hum);
  return true;
}

