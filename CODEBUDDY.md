# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## 项目是什么

对 YSBadge2（双面 800×480 七色电子墨水胸牌）的 BLE 投图工具做逆向复刻。核心产物是单文件
`epd_send.py`：PC 端直接把图片编码成设备要的 4bit 位图 + LZ77 压缩流，经 BLE 写入屏幕。

代码量很小，知识量很大：**大部分工作是实测标定协议与出图工艺，结论都写在 `docs/` 的 md 里**。
判断"该怎么改"之前先读文档，不要从代码反推协议。

- 设备 MAC `EE:96:BB:1E:05:28`，服务 ff01 / 写图 ff02 / 写命令 ff03 / 通知 ff04
- 主控 PHY6220（Cortex-M0），无 DFU 恢复通道，无独立 flash

## 常用命令

环境：Windows 11 + Python 3.14，依赖只有 `bleak`（3.0.2）与 `Pillow`（12.2.0），
没有 requirements/venv/CI。大文件策略：`reference/apk/base.apk`（53M 官方原件，不可再生）**入库**；
`_verify` 的实验图片（fixture 与输出）由 `gen_*.py` / `check_*.py` 再生，按 `.gitignore` 不入库；
浏览器验证用的 headless profile 目录同样不入库。

```bash
# 只编码 + 打印压缩体积，不连设备（无硬件也能跑，首选自检方式）
python epd_send.py --image x.jpg --offline

# 实机投图（index 1=A 面，2=B 面，3=双面同显）
python epd_send.py --image x.jpg --index 2

# 双面异显（index 7 由 --image2 自动启用）
python epd_send.py --image a.jpg --image2 b.jpg

# 体积守门自检：噪声图必然超限，期望 exit 2 + "拒绝发送"
python _verify/check_fixes.py      # 另含 EXIF 方向、透明底铺白两项断言

# BLE 辅助
python tools/scan_ble.py           # 扫 12s，标出带 ff01 的设备
python tools/watch_ble.py 60       # 观察广播 60s（判断设备是否还活着）
python tools/gatt_dump.py          # 连接后枚举 service/characteristic

# 网页版（web/）配套校验：JS 协议层 vs Python 逐字节交叉验证 + 页面静态检查
python _verify/check_web_core.py   # 25 个向量：量化/打包/LZ77/MT19937
python _verify/check_web_page.py   # 页面语法、模块加载、id 核对 + DOM shim 冒烟（无需浏览器）

# 真实浏览器验证（需本机 Edge/Chrome；先起带调试端口的 headless 实例再跑）
node _verify/browser_check.js 9333

# ESP32 定时投图（firmware/weather_badge，合宙 AirM2M CORE-ESP32C3）
# 板型必须是 AirM2M_CORE_ESP32C3；用通用 esp32c3 会无限重启并报 partition table error
./.toolchain/arduino-cli.exe compile --fqbn esp32:esp32:AirM2M_CORE_ESP32C3     --board-options PartitionScheme=huge_app --output-dir firmware/weather_badge/build firmware/weather_badge
python _verify/check_lz77_port.py        # C++ 压缩流 vs Python 解压器，逐字节往返
python _verify/c3_bootlog.py 40 115200   # 复位并抓 40s 串口日志
```

**没有独立测试框架**：`epd_send.py` 启动时无条件调用 `selftest()`，对 `compress()`/`decompress()`
做 7 组往返逐字节比对，任何调用都在跑。改压缩器后跑一次 `--offline` 即可回归。
`_verify/` 下是硬件实验脚本，按单次实验使用，不是测试套件；
各脚本用途见 `_verify/INDEX.md`。

## 架构与数据流

```
图片文件
  └─ build_canvas()      EXIF 转正 → 透明底铺白 → contain/fill/stretch 到 800×480
  └─ 增强/翻转           ImageEnhance ×4 → invert → rotate180
  └─ 量化                三种互斥路径：--ordered(Bayer8) / --dither(PIL Floyd–Steinberg) / 最近色
  └─ pack_indexed()      每像素 1 字节索引 → 4bit/px，高半字节=偶数列
  └─ compress()          LZ77，返回 (bytes, bit_length)
  └─ BLE                 INIT → PIC_INFO → ff02 分块（mtu-3，40ms/块）→ 可选 UPDATE
```

关键不变量（改任何一环都会破坏协议）：

| 量 | 值 | 说明 |
| --- | --- | --- |
| 画布 | 800×480 | 固定，不随源图变 |
| 裸数据 | 192000 B | 800×480 / 2 |
| 调色板顺序 | 黑 白 绿 蓝 红 黄 橙 | 索引即线上 4bit 码，**顺序不能动** |
| 半字节序 | 高=偶数列，低=奇数列 | 纯白整屏打包后应为 192000 个 `0x11` |
| 压缩上限 | 262144 bit (~32KB) | 超限设备静默丢弃；远超限会掉线需断电。**这是固件 BLE 接收缓冲的限制（根源主控 RAM），不是屏幕的限制**——屏自己能存 192000 B，见 docs/PROTOCOL.md §6.0 |
| 两次刷新间隔 | 约 30s | 刷新期间收到的数据被吞，连续快发会丢第二张 |

## 协议要点（细节见 docs/PROTOCOL.md）

命令帧走 ff03，无 CRC，无鉴权，无 ACK：

```
INIT      [00, 06, index]
PIC_INFO  [01, ctype, len0..len3]   小端
PIC_DATA  写 ff02 的原始字节流
UPDATE    [03, 00]                  可选项，BLE 官方 App 不发
```

- `index`：1=A，2=B，3=A&B 同显，7=A&B 异显（pic_data = A || B）
- `ctype=1`（压缩）是唯一可用通道；`ctype=0` 未压缩在本机固件上**不刷新且会卡死 GATT**，
  `--no-compress` 只是保留的实验开关，不要用它做"大图绕过 32KB"的方案
- ff04 的 read 恒返回 ASCII `Jack Wang`；notify 只有 `02 00 00`（已收 INFO）与 `00 02`（等数据超时），
  **没有完成回执**，成功只能看屏幕

### 危险输入（实测会让设备失联，需断电重启）

- `INIT` 的 `epd_index=9`（非法索引）：发帧瞬间挂
- 声明长度远超实发数据 / payload 远超 262144 bit：传输中掉线且不再广播

改发送逻辑时，务必保留 `--offline` 的体积打印与超限拒绝（exit 2），别为了"先发出去看看"绕过它。

## 文档地图（结论的权威顺序）

| 文件 | 内容 |
| --- | --- |
| `docs/PROTOCOL.md` | 协议实测确认版。§5.1 LZ77 位级格式与走查实例、§5.2 设备侧解压证据、§6.0 32KB 归属定性、§6.2 压缩比门槛阶梯、§9.1 扫描不到≠失联；§7 是勘误，推翻了早期"带 CRC / 有 DEV_AUTH"的推测；以本文为准 |
| `docs/IMAGE_PROCESSING.md` | 7 色出图工艺：尺寸策略、按内容选抖动、PIL 快路径、体积实测、HTML 截图参数 |
| `docs/LESSONS.md` | 参考项目的对照实验。证据分级（源码/他机/本机/待验），未压缩通道关闭的依据在 §1 |
| `docs/REFERENCE_EPDIY.md` | 另两个参考项目（vroland/epdiy、tsl0922 蓝牙墨水屏日历）的对照。全为他机/源码级，无本机实测；产出 2 个待验方向（时间同步命令、驱动 IC 识别） |
| `docs/ESP32_WEATHER.md` | ESP32-C3 定时投图：合宙 AirM2M 板型坑（用错 fqbn 必报 partition table error）、逐行生成 + 流式压缩的内存账、6:00 深睡调度、编译烧录命令、实测压缩比 |
| `docs/APK_FEATURES.md` | 官方 APK 逆向：页面、SQLite 8 张表、投图流程、`com.app.ysbadge` 关键类索引 |
| `docs/HARDWARE.md` | PCB V2.3 识别、6 个调试焊盘、SWD 取固件流程（只读） |
| `README.md` | 面向使用者的总结与 CLI 参数表 |
| `reference/apk/README.md` | 官方 APK 原件的说明与再反编译方法（反编译源码不进公开仓库，原因见该文件） |
| `_verify/INDEX.md` | 每个实验脚本的用途、证据归属、已知失效点 |
| `reference/apk/ysbadge/` | 协议层反编译源码 8 个文件（含 myapplication.tool 包的 BluetoothTool.java），docs 各处引用的原始证据；完整反编译树见 reference/apk/README.md |
| `web/index.html`、`web/ysbadge-core.js` | 网页版投图台（纯前端 Web Bluetooth）。协议层在 ysbadge-core.js，与 epd_send.py 逐字节一致，**改它必须跑 `_verify/check_web_core.py`** |

## 工作约定

- **先文档后代码**：协议/工艺类结论先落进对应的 md（标注证据级别：源码/他机/本机/待验），
  确认后再改 `epd_send.py`。不要把"推理出来的协议"直接写进代码当事实。
- **推断必须标待验**：例如 32KB 上限只二分到"成功 32024 B、失败 39186 B"，不要说成精确边界。
- 文档与注释用中文；代码保持当前风格——单文件、无第三方抽象、`selftest()` 常驻。
- **协议层只有一份实现**：`web/ysbadge-core.js` 是 `epd_send.py` 的 JS 移植，两者由
  `_verify/check_web_core.py` 逐字节锁死。改任何一边（量化/打包/LZ77/MT19937）都要跑该脚本，
  不允许出现只改一边的状态；缩放/增强/FS 抖动是已知的、文档化的例外（见 README 网页版章节）。
- `_verify/` 里的脚本可以被新实验脚本复制改造，但不要把它们包装成库或包；
脚本路径从自身位置推导（`_ROOT` / `_VD`），不要写绝对路径；新增内容才分类归档。
- **PIC_INFO 的 len 语义（2026-10-21 实机确认）**：compress_type=1 时填**压缩后比特数**，
  compress_type=0 时填原始字节数。证据：网页版曾按字节数声明，屏幕无变化且设备失联需断电重启；
  按比特数声明（`_verify/send_probe.py`、`_verify/ab_marker.py`）均正常刷新。`epd_send.py` 与网页版
  现均已按比特数；这段曾是仓库里的待核对项，现在是结论，不要再改回字节数。
