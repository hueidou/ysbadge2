#pragma once
// BLE 中央端：把一条完整压缩流投到 YSBadge2。
// 时序见 docs/PROTOCOL.md §3：INIT(ff03) -> PIC_INFO(ff03) -> 分块写 ff02。
#include <stdint.h>

// 返回 true 只代表数据已全部写出；设备没有完成回执，是否刷新只能看屏。
bool epd_push(const uint8_t *payload, uint32_t bits, uint8_t index);

// 只扫描+连接，确认能摸到设备（调试用）
bool epd_probe();

