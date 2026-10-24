# reference/apk/ — 官方 APK 原件

`base.apk` 是厂商 App（`com.app.myapplication`，4 个 dex）的原件，**不可再生**，
本仓库协议结论的原始证据都出自对它的逆向分析。

**反编译产物（jadx 源码）不随公开仓库分发**：它是厂商代码的派生作品，整树再分发有版权风险。
结论与关键行短引用（作为证据引用）见 `docs/APK_FEATURES.md` 与 `docs/PROTOCOL.md`；
需要核对时按下面的方法自行再反编译。

| 文件 | 体积 | 说明 |
| --- | ---: | --- |
| `base.apk` | 53M | 官方 App 原件（4 个 dex），不可再生 |

## 再反编译（如需核对结论）

    jadx -d apk_src base.apk

协议层源码在产物里的位置：`apk_src/sources/com/app/ysbadge/`——`EPD_Config.java`（命令帧构造、
`getPicData_NColor_4bit`）、`NfcDataHandler.java`（NFC 链路）、`LZ77Compress.java`（自研 LZ77）、
`BMPConverter.java`（量化）等 7 个文件，约 1375 行，带方法体。资源树（res/、assets/fonts）
直接解压 base.apk 即有，与协议无关。
