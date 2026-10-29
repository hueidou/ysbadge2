#include "epd_ble.h"
#include "config.h"
#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEClient.h>
#include <BLERemoteCharacteristic.h>
#include <BLERemoteService.h>

static const char *SVC_UUID = "0000ff01-0000-1000-8000-00805f9b34fb";
static const char *PIC_UUID = "0000ff02-0000-1000-8000-00805f9b34fb";
static const char *CMD_UUID = "0000ff03-0000-1000-8000-00805f9b34fb";
static const char *NTF_UUID = "0000ff04-0000-1000-8000-00805f9b34fb";

static volatile bool s_got_info = false;

static void on_notify(BLERemoteCharacteristic *ch, uint8_t *data, size_t len, bool isNotify) {
  (void)ch; (void)isNotify;
  Serial.printf("[ble] notify %u B:", (unsigned)len);
  for (size_t i = 0; i < len; i++) Serial.printf(" %02x", data[i]);
  Serial.println();
  if (len >= 1 && data[0] == 0x02) s_got_info = true;   // 02 00 00 = 已收到 PIC_INFO
}

static bool addr_match(const BLEAddress &a, const char *mac) {
  return strcasecmp(a.toString().c_str(), mac) == 0;
}

// 扫 10s 找目标；结果集在 stop() 后就失效，所以拷一份出来
static BLEAdvertisedDevice *scan_for(const char *mac, const char *name, uint32_t seconds) {
  BLEScan *scan = BLEDevice::getScan();
  scan->setActiveScan(true);
  scan->setInterval(60);
  scan->setWindow(50);
  scan->clearResults();
  BLEScanResults *res = scan->start(seconds, false);
  BLEAdvertisedDevice *hit = nullptr;
  for (int i = 0; res && i < res->getCount(); i++) {
    BLEAdvertisedDevice d = res->getDevice(i);
    bool want_mac = mac && *mac;
    bool ok = want_mac ? addr_match(d.getAddress(), mac)
                       : (name && *name && d.haveName() && d.getName() == name);
    if (ok) {
      Serial.printf("[ble] 找到 %s rssi=%d\n", d.getAddress().toString().c_str(), d.getRSSI());
      hit = new BLEAdvertisedDevice(d);
      break;
    }
  }
  scan->stop();
  scan->clearResults();
  return hit;
}


bool epd_probe() {
  BLEAdvertisedDevice *dev = scan_for(EPD_MAC, EPD_NAME, 8);
  if (!dev) { Serial.println("[ble] 没扫到设备"); return false; }
  delete dev;
  return true;
}

bool epd_push(const uint8_t *payload, uint32_t bits, uint8_t index) {
  static bool inited = false;
  if (!inited) { BLEDevice::init("ysbadge-feeder"); inited = true; }

  BLEAdvertisedDevice *dev = scan_for(EPD_MAC, EPD_NAME, 10);
  if (!dev) return false;

  BLEClient *cl = BLEDevice::createClient();
  if (!cl->connect(dev)) {
    Serial.println("[ble] 连接失败");
    delete cl;
    delete dev;
    return false;
  }
  delete dev;

  uint16_t mtu = 23;
  if (cl->setMTU(247)) mtu = cl->getMTU();       // 失败就退回默认 23（每包 20B）
  Serial.printf("[ble] 已连接, mtu=%u\n", (unsigned)mtu);

  BLERemoteService *svc = cl->getService(BLEUUID(SVC_UUID));
  if (!svc) {
    Serial.println("[ble] 找不到 ff01 服务");
    cl->disconnect(); delete cl; return false;
  }
  BLERemoteCharacteristic *chCmd = svc->getCharacteristic(BLEUUID(CMD_UUID));
  BLERemoteCharacteristic *chPic = svc->getCharacteristic(BLEUUID(PIC_UUID));
  BLERemoteCharacteristic *chNtf = svc->getCharacteristic(BLEUUID(NTF_UUID));
  if (!chCmd || !chPic) {
    Serial.println("[ble] 缺 ff02/ff03 特征");
    cl->disconnect(); delete cl; return false;
  }
  if (chNtf && chNtf->canNotify()) chNtf->subscribe(true, on_notify);


  // INIT
  uint8_t init[3] = {0x00, 0x06, index};
  chCmd->writeValue(init, sizeof init, false);
  delay(300);

  // PIC_INFO：compress_type=1 时 len 必须是压缩后比特数（docs/PROTOCOL.md §2）
  uint8_t info[6] = {0x01, 0x01,
                     (uint8_t)(bits & 0xFF), (uint8_t)((bits >> 8) & 0xFF),
                     (uint8_t)((bits >> 16) & 0xFF), (uint8_t)((bits >> 24) & 0xFF)};
  s_got_info = false;
  chCmd->writeValue(info, sizeof info, false);
  Serial.printf("[ble] INIT %02x %02x %02x, PIC_INFO len=%u bit\n",
                init[0], init[1], init[2], (unsigned)bits);

  for (int i = 0; i < 12 && !s_got_info; i++) delay(100);   // 等 02 00 00，最多 1.2s
  if (!s_got_info) Serial.println("[ble] 未收到 INFO 回执，继续发");

  uint32_t bytes = (bits + 7) / 8;
  uint32_t chunk = mtu > 23 ? (uint32_t)(mtu - 3) : 20;
  uint32_t total = (bytes + chunk - 1) / chunk;
  Serial.printf("[ble] 发送 %u B / %u 块 x %u B\n", (unsigned)bytes, (unsigned)total, (unsigned)chunk);
  for (uint32_t off = 0, k = 0; off < bytes; off += chunk, k++) {
    uint32_t n = (bytes - off) < chunk ? (bytes - off) : chunk;
    chPic->writeValue((uint8_t *)(payload + off), n, false);
    delay(CHUNK_DELAY_MS);
    if (k % 20 == 0) Serial.printf("  %u/%u\n", (unsigned)k, (unsigned)total);
  }

  delay(1500);           // 留出解压+刷新的时间；两次刷新之间设备需要约 30s
  cl->disconnect();
  delete cl;
  Serial.println("[ble] 发送完成（无完成回执，看屏幕）");
  return true;
}

