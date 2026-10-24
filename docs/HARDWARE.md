# YSBadge2 硬件识别（PCB V2.3）

2026-10-21 依据实物照片识别，照片见 `analysis/hardware/`。

> 说明：两张照片是**同一面（元件面）的左右两段**，在电源区（D10 / 150 / 3R3 / Q3）重叠，不是正反面。

## 1. 结论摘要

| 项目 | 结论 | 依据 |
|---|---|---|
| 主控 | **PHY6220**（奉加微 Phyplus，Cortex-M0，BLE SoC，QFN32，内置 flash） | U1 丝印 `PHY+` / `PHY6220` |
| 批次 | 2104EFE323（约 2021 年第 4 周） | 同上 |
| 板号 | V2.3 | 板面丝印 |
| 屏 | A面 FPC 座与主控**同面**，屏体压在元件上方；双面屏的另一路接口位置待确认 | 区域二可见 FPC 座，旁标 A面 |
| 晶振 | 金属封装无源晶振 X2，频率丝印不可辨（PHY6220 常用 24MHz，待确认） | 区域一特写 |
| 供电 | 外接锂电池，`PWR` 座，红黑线 | 区域二 |
| 近场 | NFC 天线：镀金座 + 细黑线引出 | 区域一 |
| 调试口 | **6 个测试焊盘：3V3 / RX / TX / C / D / G** | 区域一上缘丝印 |

板上没有独立 SPI flash，固件在 PHY6220 片内 flash 里。

## 2. 元件与布局（同一面的两个区域）

### 区域一：主控与调试口（board_area1_mcu.jpg）

- **U1**：PHY6220，QFN32；右侧紧邻金属封装晶振 **X2** 与匹配电容
- 6 个调试测试焊盘，板子上缘偏中，丝印 `3V3 RX TX C D G`
- **BOOT** 按键（右上）、**RESET** 按键（右下）
- **NFC** 镀金座（下缘），细黑线为 NFC 天线
- 电源器件：`L5 150`、`L9 3R3`、`D10`、`Q3`、`U5` 等
- 板右侧边缘有一处矩形避让/开窗区（标 `U12`），内部无元件；是否为第二面屏接口或天线净空待确认

### 区域二：屏座与电池（board_area2_epd.jpg）

- **墨水屏 FPC 座**：约 32 pin，金属卡扣式，旁印 **A面**；与主控同面，屏体折叠覆盖在元件上方
- **PWR** 电池座（红黑线），下方是橙色锂电池
- 同一批电源器件 `D10`、`150`、`3R3`、`Q3` 在此区域重复出现 —— 两张照片的重叠证据
- 板边丝印 **V2.3**

## 3. 调试口（最关键）

| 焊盘 | 推断功能 | 说明 |
|---|---|---|
| 3V3 | 3.3V 供电 | 与电池二选一 |
| RX | UART 接收（相对 MCU） | 接 USB-TTL 的 TX |
| TX | UART 发送 | 接 USB-TTL 的 RX |
| C | **SWCLK**（推断） | Cortex-M0 SWD 时钟 |
| D | **SWDIO**（推断） | Cortex-M0 SWD 数据 |
| G | GND | 与板地连通 |

依据：PHY62xx 系列常见做法是把 SWD 与 UART 一起引出，`C/D` 对应 CLK/DIO 缩写；精确功能需万用表或接 DAPLink 验证（见 §6）。

接线注意：

- **电池与 3V3 不要同时接**，避免两路电源顶牛
- 先接好 `G`，再接信号线
- 严禁把 3.3V 误接到 `C` 或 `D`

## 4. 取固件流程（SWD，只读）

1. 准备 DAPLink / J-Link 与探针（焊盘间距小，建议飞线）
2. 接 `3V3 C D G`（供电可改由电池提供）
3. 用 pyOCD 或 OpenOCD 连接，Cortex-M0 的 **IDCODE 应为 `0x0BB11477`**
4. 识别成功后读取片内 flash 全片（容量以实测为准，PHY6220 常见 256KB）
5. 校验：在镜像里搜索字符串 `Jack Wang`（原 ff04 读口返回值），命中即证明 dump 到的是同一份固件
6. 保存为 `firmware/ysbadge2_v2.3.bin` 并记录 CRC32

该流程只读，不写 flash，不改变设备状态；前提是出厂未启用读保护。

## 5. 串口调试（CH340C，可行但仅限 UART）

CH340C 是 USB↔UART 桥，**没有 SWD 时序能力，不能用来读 flash**；它能做的是抓日志、确认固件行为。

### 5.1 接线

| CH340C | 板上焊盘 | 说明 |
|---|---|---|
| TX | RX | 交叉连接 |
| RX | TX | 交叉连接 |
| GND | G | 必接，先接地 |
| 3V3 | 3V3 | **不接**（电池供电时）；若板子无电池才由此供电 |

- 电平必须 **3.3V**（模块上的 5V/3.3V 跳线选 3.3V），5V 逻辑会损伤 PHY6220
- 电池与 3V3 **二选一**，不要同时供

### 5.2 参数与抓取方法

- 串口参数：`8N1`，先试 `115200`，不通再试 `921600`、`1500000`
- 顺序：**先开串口监听，再按 RESET**，否则会漏掉启动阶段
- 预期能看到：启动打印、固件版本、复位原因、外设初始化、可能的 CLI 或错误码
- 拿不到：flash 内容（必须走 SWD，见 §4）

### 5.3 CH340C 与 DAPLink 对比

| | CH340C | DAPLink（CMSIS-DAP） |
|---|---|---|
| 接口 | UART | SWD（SWCLK/SWDIO） |
| 能抓日志 | ✅ | ❌ |
| 能读 flash | ❌（除非厂商 UART ISP 开放读回） | ✅（未启用读保护时） |
| 典型价格 | 几元 | 十几元 |
| 风险 | 低（只收日志时） | 中（探针短接、误写） |

建议顺序：先用 CH340C 抓启动日志摸清固件；信息不足再上 DAPLink 读片。

## 6. 风险与待确认

- **读保护**：IDCODE 读不到或 flash 全为 0xFF，说明 SWD 被关闭或启用读保护，只能走 UART BootROM 的 ISP 或放弃
- **物理风险**：探针打滑短接 3V3 与相邻焊盘会烧芯片；焊接温度过高会掉焊盘；翻板前先松 FPC 卡扣
- **不要写 flash**：本设备无 DFU 恢复通道（PROTOCOL.md §9），取固件阶段严禁写操作
- 待确认：`C/D` 是否为 SWCLK/SWDIO（接 DAPLink 读 IDCODE 即可验证）；UART 波特率（115200 / 921600 试）；X2 晶振频率；无线天线形式（未见明显板载走线天线）；B面屏的 FPC 接口位置；NFC 通道用途（配网/唤醒/触发刷新，未测）；串口是否输出有效启动日志（待接 CH340C 实测）

## 7. 照片索引

| 文件 | 内容 |
|---|---|
| `analysis/hardware/board_area1_mcu.jpg` | 区域一：U1(MCU)、调试焊盘、BOOT/RESET、NFC 座 |
| `analysis/hardware/board_area2_epd.jpg` | 区域二：A面 FPC 座、PWR 电池座、电源区、V2.3 |
| `analysis/hardware/u1_chip.png` | U1 丝印特写（PHY6220） |
| `analysis/hardware/debug_pads.png` | 6 个调试焊盘丝印特写 |
| `analysis/hardware/nfc_area.png` | NFC 天线座与走线 |

## 7. 屏体识别：GDEY073D46（2026-10-23 调研，推断，待实物确认）

尺寸 / 色彩 / 接口三项与公开资料唯一匹配：**800×480 七色 SPI 50-pin FPC**
→ **Good Display GDEY073D46**（7.3 寸 ACeP，黑/白/红/黄/蓝/绿/橙；微雪同规格产品为
7.3inch e-Paper (F)，SKU 23433/23434）。证据级别：**推断**（规格匹配度极高；
确认方法即 §6 待确认项：读 FPC 补丁丝印或拆屏看 COG 绑定处）。

| 项目 | 参数 | 对项目的意义 |
| --- | --- | --- |
| 满刷时间 | **32s**（微雪标 35s；同面板整机页写约 30s） | 解释本机实测「两次刷新间隔约 30s、刷新期间吞数据」：ACeP 满刷固定 32s，**不支持局刷**（Good Display 只列 Full refresh，cale-idf 明确 "Partial update: Not supported as in most of the color epapers"） |
| 帧缓冲 | 屏内集成 frame buffer + LUT（数据手册原文） | §6.0「192KB 在屏自己的 GRAM、MCU 只持一批 + 解压窗口」获得数据手册级佐证 |
| 工作温度 | **15~35°C** | 北京秋冬室外低于下限，低温刷新可能变慢或出残影；发送前留意环境温度 |
| 刷新功耗 | 52.8 mW，待机 0.118 mW | 双面 = 双屏双倍刷新功耗与时间 |
| 接口 | SPI（DIN/SCLK/CS/DC/RST/BUSY） | 照片中板上 FPC 座约 32 pin，数据手册为 50 pin FPC——连接器形式/针数不一致，待确认（可能只接了部分信号或转了接板） |
| 控制器 | **SPD1656 家族（待验）** | cale-idf 实测该屏行为与 SPD1656 驱动一致（作者自注不确定）；Adafruit CircuitPython 有 `adafruit-circuitpython-spd1656`（4"/5.65" ACeP）。读 IC 丝印确认 |
| 生命周期 | **EOL**，继任型号 GDEP073E01 | 未来买样板/换屏的型号参考 |

同面板生态（他机，可作对照实现）：微雪 7.3inch e-Paper HAT (F)、martinberlin/cale-idf
（ESP-IDF 驱动 + CALE.es 在线渲染）、GxEPD2（`GxEPD2_730c_ACeP_730` 类）、
Adafruit CircuitPython spd1656、Pimoroni Inky Impression（5.7 寸同族 ACeP）。
近乎同品类的整机：**DMIF073CBW1**（双面 7.3 寸 ACeP + NFC/BLE 投图的电子公告牌，
选配 5.65/7.3 寸，BLE 5.0，2 节 5 号电池）——与本胸牌的产品形态几乎同构。

**注意：4bit 色序是发送方约定的，不是屏固有的。** GxEPD2 的 ACeP canonical 色序为
0黑 1红 2绿 3橙 4黄 5蓝 6白（Arduino 论坛帖，2023），与本机实测的
0黑 1白 2绿 3蓝 4红 5黄 6橙 **不同**。本机口径以实测为准（PROTOCOL.md §4），不要照抄 GxEPD2。
