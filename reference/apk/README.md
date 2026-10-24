# reference/apk/ — 官方 APK 原件 + 协议层反编译源码

`base.apk` 是厂商 App（`com.app.myapplication`，4 个 dex）的原件，**不可再生**，
本仓库协议结论的原始证据都出自对它的逆向分析。

## 收录范围

| 路径 | 内容 |
| --- | --- |
| `base.apk` | 官方 App 原件（53M，4 个 dex），不可再生 |
| `ysbadge/` | **协议层反编译源码 8 个文件**（jadx 产出，带方法体）——docs 各处引用的原始证据 |

8 个文件：

| 文件 | jadx 原始路径 | 内容 |
| --- | --- | --- |
| `ysbadge/EPD_Config.java` | com/app/ysbadge/ | 命令帧构造、`getPicData_NColor_4bit` |
| `ysbadge/NfcDataHandler.java` | com/app/ysbadge/ | NFC(ISO-DEP) 完整链路、批量握手 |
| `ysbadge/LZ77Compress.java` | com/app/ysbadge/ | 自研 LZ77（窗口 1024 / Golomb m=3），`epd_send.compress()` 的复刻对象 |
| `ysbadge/BMPConverter.java` | com/app/ysbadge/ | 量化/抖动（FS/Bayer） |
| `ysbadge/RGBTriple.java` | com/app/ysbadge/ | 颜色三元组 |
| `ysbadge/BluetoothTool.java` | com/app/**myapplication/tool**/ | BLE 路径：INIT→PIC_INFO→流式写 ff02；compress_type 分支（:41/:55）即 PIC_INFO len 语义的源码级证据 |
| `ysbadge/utils/CrcCheckUtil.java` | com/app/ysbadge/utils/ | CRC 工具 |
| `ysbadge/utils/HttpDownloader.java` | com/app/ysbadge/utils/ | 模板下载 |

为集中引用，文件从各自 jadx 路径平铺到 `ysbadge/`（`BluetoothTool.java` 原属 myapplication.tool 包，
是 2026-10-21 只留 ysbadge 包时唯一被漏掉的源码级证据；2026-10-23 用 jadx 1.5.6 重新反编译找回，
docs 引用的 :41/:55 行号与新版输出一致）。

## 完整反编译树不随仓库分发

jadx 全量输出约 9700 个类，其中 99% 是与协议无关的第三方库（xmlbeans / reactivestreams / w3c 等），
整树再分发只有噪音和版权风险。需要时自行生成（已实测可用）：

    jadx --no-res -d apk_src base.apk        # jadx 1.5.6 实测

生成后协议层文件在 `apk_src/sources/com/app/ysbadge/` 与
`apk_src/sources/com/app/myapplication/tool/`；资源树（res/、assets/fonts）直接解压 base.apk 即有。

## 注意

这些文件是厂商专有代码的反编译产物，收录仅为**协议互操作的技术证据与引用来源**；
如厂商认为不合适，会随时删除。
