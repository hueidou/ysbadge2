# ESP32 定时投天气（每天 6:00）

用一块 ESP32-C3 当 BLE 中央端：每天 6:00 自己取天气、画 800×480 七色图、LZ77 压缩、
BLE 投给胸牌，然后深睡到次日。PC 不用开机。协议层与 `epd_send.py` 完全一致，见 `PROTOCOL.md`；
本文只记 ESP32 端特有的东西。

## 0. 现状（2026-10-29 实机跑通）

| 项 | 值 |
| --- | --- |
| 板子 | 合宙 **AirM2M CORE-ESP32C3**（板上印 `luatos.com/t/esp32c3`），4MB flash，无 PSRAM |
| 板型 | `esp32:esp32:AirM2M_CORE_ESP32C3`（**不是** `esp32c3`，见 §1） |
| 核心 | arduino-esp32 3.3.12 |
| 分区 | `PartitionScheme=huge_app`（固件 1.46MB，默认 1.2MB 装不下） |
| 串口 | COM7（CH343），上传 921600 |
| 实测 | 上海/北京各投一次成功；压缩 88550~91971 bit（11.0~11.5KB，5.8~6.0%）；压缩耗时 0.9~1.3s；MTU 247 下 46~48 块发完；深睡间隔 ~7.2h 对上 6:00 |

## 1. 板型坑（先看这条，能省半天）

这块板上印着 `luatos.com/t/esp32c3`，是合宙的 AirM2M CORE-ESP32C3。**必须用它的专用板型编译**：

```bash
--fqbn esp32:esp32:AirM2M_CORE_ESP32C3
```

用通用 `esp32:esp32:esp32c3` 编译出来的固件，烧进去就是这个死循环（本机实测）：

```
E (25) flash_parts: partition 0 invalid magic number 0xffdf   # 换镜像会变成 0xffff / 0xcecd 等
E (25) boot: Failed to verify partition table
E (26) boot: load partition table error!
```

注意它**不是**分区表真的坏了。当时为了定位，做过这些，全部无效（记下来免得别人重走）：

| 排查 | 结果 |
| --- | --- |
| `esptool erase_flash` 全片擦除后重烧 | 无效 |
| 换分区方案（default / huge_app / no_ota …） | 无效 |
| flash 模式与频率（DIO / QIO / 20M / 40M / 80M） | 无效；QIO 直接不输出 |
| 分别用 bootloader+partitions+app 与 merged.bin 烧 | 无效 |
| stub 写入 vs `--no-stub` ROM 写入 | 无效（两种都验证通过） |
| arduino-esp32 3.3.12 与 2.0.17 两版 bootloader | 无效 |
| 把 0x8000 整页写成 0xAA 后再启动 | 仍报 `0xffdf` → bootloader 读到的不是 flash 内容 |
| `esptool --no-stub read_flash 0x8000` | 读出正确内容 → ROM 能读、二级 bootloader 读不了 |

结论：这是板级 flash 配置与通用 C3 定义不匹配，换板型即可，和分区表/烧写流程无关。

## 2. 为什么是"逐行生成 + 流式压缩"

ESP32-C3 只有 400KB SRAM、没有 PSRAM，整屏 4bit 帧缓冲 192000 B 不能常驻：

| 缓冲 | 大小 | 说明 |
| --- | --- | --- |
| 单行像素 | 800 B | 只在画某一行时存在 |
| 行缓存 | 8 行 × 800 B | 覆盖 LZ77 需要的 1024B 前视/回看 |
| 压缩输出 | 36 KB | 静态分配；超 32KB 拒绝发送 |
| LZ77 候选表 | 16 KB | 2048 桶 × 2 槽 |

`ui_byte(pos)` 按需渲染第 `pos/400` 行（400 B = 800 像素 × 4bit）并缓存 8 行，
`lz77_compress()` 只需要 1024B 窗口与 1024B 前视，两者一拼就得到完整的 192000 B 输入。
实测空闲堆剩 165KB，BLE + 压缩同时跑没有压力。


## 3. 压缩器与 Python 侧的关系

`lz77.cpp` 是 `epd_send.py:compress()` 的移植：窗口 1024、偏移 10bit 相对**窗口起点**、
匹配长度 Golomb(m=3)、字面量 9bit、位流字节内高位优先（数据位 LSB 先发）。唯一差异：
候选匹配位置用 2 槽哈希表代替 Python 的 64K 桶 + 二分，所以**输出是合法流但不保证逐字节相同**
（解压结果相同，体积略大：同一张图 C++ 11476 B vs Python 7503 B）。

交叉验证方式（必须保持）：

```bash
# 1) 主机版程序把 C++ 压出的流和"直接渲染"的原始帧都落盘
cd _verify/host && g++ -std=c++17 -O2 -I../../firmware/weather_badge host.cpp \
    ../../firmware/weather_badge/{ui,canvas,icons,font,wmo,lz77,font_data}.cpp -o host.exe
./host.exe frame f.lz f.raw

# 2) 用 Python 的 decompress()（与设备侧位级一致）还原并比对
python _verify/check_lz77_port.py
```

通过判据：`decompress(f.lz, bits) == f.raw` 且 `bits <= 262144`。

## 4. 每天 6:00 / 省电 / 手动触发

- 时间：NTP（aliyun / tencent / pool.ntp.org），本地时间 = UTC + `TZ_OFFSET_SEC`（东八区 28800）
- `POWER_SAVE 1`（默认）：投完 `esp_sleep_enable_timer_wakeup()` + `esp_deep_sleep_start()`，
  睡到次日 6:00（本机实测 25957s ≈ 7.2h，醒来正好 6:00），深睡电流 ~10µA 量级
- `POWER_SAVE 0`：一直醒着用 `millis()` 轮询（调试用，串口日志不断）
- 顺序固定为 取数 → **关 WiFi** → 压缩 → BLE：单射频分时用，避免 WiFi/BLE 共存掉线，也把 RAM 让出来
- 失败重试 `MAX_RETRY` 次；仍失败就 `RETRY_MINUTES` 后再来（胸牌两次刷新之间需 ≥30s）
- **调试触发**：上电后 `SERIAL_FORCE_MS`（3s）内往串口发任意字符就立刻投一张。
  不能用 BOOT(GPIO9) 做按键——它是 strapping 脚，按住上电会进下载模式。

## 5. 编译与烧录

```bash
CLI=./.toolchain/arduino-cli.exe        # 本机装在这里；也可用 PATH 里的 arduino-cli
FQBN=esp32:esp32:AirM2M_CORE_ESP32C3
OPTS=PartitionScheme=huge_app

# 编译
$CLI compile --fqbn $FQBN --board-options $OPTS \
    --output-dir firmware/weather_badge/build firmware/weather_badge

# 烧录（合宙板认 COM7 / CH343；分 4 段写，bootloader 在 0x0）
cd firmware/weather_badge/build
python -m esptool --port COM7 write_flash \
  0x0     weather_badge.ino.bootloader.bin \
  0x8000  weather_badge.ino.partitions.bin \
  0xe000  esp32.esp32.esp32c3/boot_app0.bin \
  0x10000 weather_badge.ino.bin

# 看日志（会先按 EN 复位再抓，等价上电）
python _verify/c3_bootlog.py 40 115200
```

> 3.3.12 的 `--output-dir` 里还有 `*.merged.bin`，理论上 `write_flash 0x0 merged.bin` 一把梭也行；
> 但本机排查时更常用分段写，出问题容易定位是哪一段。


## 6. 配置（只改 `firmware/weather_badge/config.h`）

| 宏 | 默认 | 说明 |
| --- | --- | --- |
| `WIFI_SSID` / `WIFI_PASS` | 占位 | 真实凭据放 `secrets.h`（已 gitignore，`config.h` 用 `__has_include` 包含） |
| `LATITUDE` / `LONGITUDE` | 39.9042 / 116.4074 | 北京。上海 31.23 / 121.47，南纬/西经为负 |
| `TIMEZONE` | Asia/Shanghai | 只用于 open-meteo 的时区换算 |
| `TZ_OFFSET_SEC` | 28800 | 本地时间 = UTC + 该值，NTP 与"下一次 6:00"都靠它 |
| `CITY_NAME` | "北京" | **每个字都要在 `tools/charset.txt` 里**，否则显示空白（不会崩） |
| `EPD_MAC` | EE:96:BB:1E:05:28 | 胸牌 MAC（`EPD_NAME` 非空时改按广播名匹配） |
| `EPD_INDEX` | 1 | 1=A 面 / 2=B 面 / 3=双面同显 / 7=双面异显（异显要改代码拼两面） |
| `PUSH_HOUR` / `PUSH_MIN` | 6 / 0 | 本地时间 |
| `POWER_SAVE` | 1 | 1=投完深睡到次日；0=常醒轮询 |
| `RETRY_MINUTES` / `MAX_RETRY` | 10 / 3 | 失败后的重试节奏 |
| `CHUNK_DELAY_MS` | 40 | ff02 分包间隔，与 `epd_send.py` 一致 |
| `SERIAL_FORCE_MS` | 3000 | 上电后多少毫秒内收串口字符 = 立即投图 |

## 7. 换城市要补字

字模是从系统字体离线烘的，只含 `tools/charset.txt` 里列过的字。换了新字（比如城市名）会显示空白：

```bash
# 1) 把新字加进 tools/charset.txt（一行纯文字，# 后是注释）
# 2) 重新生成字模（120px 数字 + 44/32/22px 三档含汉字，合计约 74KB）
python tools/gen_font.py
# 3) 重新编译烧录
```

## 8. 版式调整

排版在 `ui.cpp` 的 `draw_header / draw_main / draw_bottom`，坐标写死。当前设计（2026-10-29 改版）：

| 区域 | 内容 |
| --- | --- |
| 顶栏 | 6px 橙色色条 + 日期/周几（32px）+ 更新时间（22px，右对齐） |
| 主体左 | 天气图标，中心 (152,218)、半径 102 |
| 主体右 | 橙色竖条 + 城市名（44px）→ 温度数字（120px，按冷暖上色）→ 小号度号（32px）→ 天气词（44px） |
| 统计行 | 体感 / 风 / 湿度：22px 小标签 + 32px 数值，三栏对齐 |
| 底栏 | 2px 分割线 + 竖线分隔「今日」「明天」两栏，22px 彩色标签 + 44px 数值 |

图标是**实心剪影**风格（`icons.cpp`）：云=三圆+底座的黑填充，太阳=黑底压黄心的圆+橙色射线；
雨/雪用蓝色粗线，雷用「黑粗线打底 + 黄线压面」保证白底上也有对比。温度配色：≤10° 蓝、≤26° 橙、更高红。

不想烧片就本机预览：

```bash
cd _verify/host
g++ -std=c++17 -O2 -I../../firmware/weather_badge host.cpp \
    ../../firmware/weather_badge/{ui,canvas,icons,font,wmo,lz77,font_data}.cpp -o host.exe
./host.exe preview out.ppm 61 21   # 61=小雨、21 度；ppm 用 PIL 转 png 看
```

## 9. 已知风险 / 待验

- **无完成回执**：`epd_push()` 返回 true 只代表数据发完，是否真的刷新只能看屏（协议本身没有 ACK）
- **MTU**：本机 C3 申请 247 成功（`setMTU(247)` → 48 块）；若某块板协商失败会自动退回 23/20B，
  时间从 ~2s 变成 ~24s，功能不受影响
- **两次刷新间隔**：设备刷一次约 30s，期间收到的数据会被吞。本实现每天只投一次，不会撞上；
  如果将来加"手动触发"，请自己保证 30s 间隔
- **深睡后无法远程调试**：串口触发只在复位后的 3s 窗口内有效，投完就睡；要长期调试把 `POWER_SAVE` 设 0
- **字体/版式未在真机核对**：本机只在 PC 上渲染预览 + 实机投图，屏幕观感（对比度、字号）按需再调
- **32KB 上限**：文字+图标版实测 11KB（5.8%），离上限很远；若将来加照片/抖动，必须先在
  `--offline` 或 `check_lz77_port.py` 里确认比特数

