# _verify/INDEX.md — 硬件实验脚本索引

本目录是**按单次实验使用**的脚本集合，不是测试套件。唯一可以随时跑的是
`check_fixes.py`（纯函数断言，不连设备）；其余 BLE 实验需要真机，且会真的往设备写数据。

脚本路径从自身位置推导（`_ROOT` = 仓库根，`_VD` = `_verify/`），clone 到任何目录都能跑。
fixture：`test_pattern.png` 与 `marker.png` 是**固定 fixture，已入库**（check_web_core.py 的期望向量按它们的字节计算，
可用 gen_pattern.py / gen_marker.py 再生核对）；`noise.png` 由 check_fixes.py / check_stress.py 首次运行自生成。

## 0. 实验计划（未执行，需批准）

| 文档 | 内容 |
| --- | --- |
| `PLAN_32KB_BLE.md` | **BLE 路径突破 32KB 上限的安全预案**：目标判据、已知/未知清单、6 步单变量阶梯、观测手段、中止条件、断电恢复 SOP、记录模板。风险等级高（最坏后果为设备失联需断电重启），执行前须满足其 §3 全部前置条件，并由人工全程确认屏幕状态 |
| `LOG_32KB_BLE.md` | 32KB 突破实验日志：Step 0-3 已执行（基线 / 空探 0xA0 / 空探 0xA1 / 投图后补 A0），含 ff04 帧型记录与消歧实验；A0 触发刷新的结论已降级为待验（依赖目视观测） | PLAN_32KB_BLE.md 的执行记录 |

## 1. 无硬件自检（可随时跑）

| 脚本 | 作用 | 对应结论 |
| --- | --- | --- |
| `check_fixes.py` | 三项断言：EXIF 方向、透明底铺白、体积守门（噪声图期望 exit 2 + "拒绝发送"）。会自建 `upright.png`/`exif6.jpg`/`alpha.png`/`noise.png` | README「图片载入已处理两个常见坑」 |
| `check_compress.py` | 新 `compress()` 与 `old_compress.py` 旧暴力实现在多组随机数据上逐字节比对 | epd_send.py `compress()` docstring 的「输出逐字节一致」 |
| `check_stress.py` | 压缩器压力：2 符号 192KB 等极端数据的耗时与体积 | 压缩性能余量 |
| `timing.py` | 编码/压缩/解压分阶段耗时 | IMAGE_PROCESSING.md §3 的「整条链路约 1.1s」 |
| `old_compress.py` | 重构前的暴力 LZ77 参考实现，上面两个检查的对照基线 | — |
| `check_web_core.py` | **网页版协议层交叉验证**：用 Node 直接 `require` `web/ysbadge-core.js`，与 `epd_send.py` 逐字节比对 25 个向量（LZ77 压缩/解压、量化 none/ordered/noise + 4bit 打包、MT19937 序列、JS selftest）。改 web 协议层后必跑 | README「网页版工具」章节的逐字节一致声明 |
| `check_web_page.py` | 网页版校验（无需浏览器）：内联 script 逐个 `node --check`、`ysbadge-core.js` 可加载且 selftest 全过、`$('id')` 与 HTML 交叉核对，外加两级冒烟——**编码管线**（DOM shim 下 loadFile→encode→直方图→视图→按钮）与 **BLE 发送**（形状逼真的 fake Web Bluetooth：properties 为布尔字典，点扫描→连接→发送，校验 ff03 两帧字节与 ff02 分块分布） | 防页面级语法/引用/运行时/BLE 路径错误；2026-10-21 靠它抓住了 `properties` 按数组用的 bug |
| `browser_check.js` | 真实浏览器验证：CDP 驱动本机 Edge/Chrome 打开 `web/index.html`，收集 console 错误与未捕获异常，并用 DataTransfer+drop 事件触发真实图片加载，读回界面字段；另断言实时联动、预设、超限自救按钮（关抖动后体积回到限内）、帮助 overlay（? 开 / Esc 关）、自检 pill、footer 版本号、title 恢复、快捷填帧、文字模式重算、index 7 自动切换、A/B 预览与交换、发送队列、参数方案、预览 PNG 导出、A/B 设置联动、人工裁剪（合成拖拽→应用→清除→体积复原）。用法：先起 `msedge --headless=new --remote-debugging-port=9333 --user-data-dir=<临时目录> file:///<仓库路径>/web/index.html`，再 `node _verify/browser_check.js 9333` | 2026-10-21 实测通过：零异常，压缩 7913 B / 63298 bit，PIC_INFO `01 01 e9 1e 00 00`；2026-10-23 三轮网页优化（交互/性能/功能）后复跑仍全过，断言覆盖文字模式、index 7 自动切换、A/B 预览与交换、队列、参数方案、预览 PNG 导出 |

## 2. 出图工艺对照（数字已写进 IMAGE_PROCESSING.md §3）

| 脚本 | 作用 |
| --- | --- |
| `baseline.py` | 旧手写误差扩散量化的速度/保真基线 |
| `bench_quant.py` | PIL `quantize()` 快路径 vs 基线：速度、像素差、压缩体积 |
| `fidelity.py` | 两实现与原图的 MAE 对比（77.55 vs 77.53 的来源） |
| `hist.py` | 量化后 7 色分布直方图对比（逐色差 < 3% 的来源） |
| `gen_pattern.py` | 生成测试输入图 `test_pattern.png`（产物已在库） |
| `gen_marker.py` | 生成 A/B 标记图 `marker.png`（产物已在库） |

## 3. BLE 实验（需真机，会真的发图）

| 脚本 | 作用 | 结论落在 |
| --- | --- | --- |
| `ab_marker.py` | 同一张标记图先压缩后未压缩的 A/B；**PIC_INFO 声明用比特数** | docs/LESSONS.md §1 表 1/2 行 |
| `probe_raw.py` | compress_type=0 不刷新的三组场景定位 | docs/LESSONS.md §1 |
| `probe_raw2.py` | UPDATE-only / 按比特声明长度 / raw+UPDATE 三探针 | docs/LESSONS.md §1 |
| `verify_nocompress.py` | 未压缩通道完整验证（787 包全流程 + 通知时间戳） | docs/LESSONS.md §1 表 3-7 行 |
| `watch_and_send.py` | 盯广播，设备一出现就连并发（应对短广播窗口） | — |
| `burst.py` | 连续 6 次连接发送，验证第二张被吞 | README 约束 4（间隔约 30s） |
| `send_probe.py` | 实机发送探针：复刻 ab_marker 已验证路径（PIC_INFO 声明**比特数**、244B/40ms），全程记录 ff04 通知时间戳，发完保持 20s 不断连。传第三参图B 时走 index 7 双面异显。2026-10-21 实测：单面正常刷新（确认 len 比特数口径）、index 7 两面分别正确显示（确认异显可用） | docs/PROTOCOL.md §2 / index 7 实机确认段 |
| `probe_cmd.py` | 单帧探针：向 ff03 写一条命令、记录 ff04 响应后干净断开——安全试探未知命令（0xA0/0xA1 就是这么探的） | PLAN_32KB_BLE.md Step 1-3 |
| `diag_gatt.py` | 重复只读枚举 GATT，诊断 ff01 服务消失/设备假死；2026-10-21 靠它确认 RESET 键（非拔电池）可恢复 | docs/HARDWARE.md §6 |
| `gen_sides.py` | 生成双面异显测试图 sideA.png（红条大字 A）/ sideB.png（蓝条大字 B） | index 7 实机验证的输入 |
| `gen_demo.py` | 生成两张**体现屏幕特点**的演示图：A 面 7 色能力图（7 色块 + 文字对比度 + 限制演示区：渐变/细灰线/小字）、B 面姓名标签实例（IMAGE_PROCESSING.md §9 版式，名字取 ff04 读口返回的 Jack Wang）。只用 7 个精确调色板色、纯色块、高对比大字 | 2026-10-21 以 index 7 双面异显实机发送，两面均正常显示 |
| `gen_weather.py` | 生成「北京今日天气」800×480 上屏卡片（屏幕 B 面）：扁平色块 + 大字 + 几何图标，只用 7 色palette、无抖动，脚本内置 2026-10-23 三源天气数据与自检（量化→打包→压缩，须 ≤262144 bit）。产物 `_verify/weather_bj_20261023.png`（gitignore，可再生）。已实机发送 index 2：10,573 B / 84,577 bit | 按天改数据重跑即可更新 B 面 |（README 示例图已改用 `_verify/host/make_weather_example.py`，与固件同一套渲染器）
| `host/make_weather_example.py` | 调 host.exe 的 preview 出 README 的 800x480 天气卡示例，渲染器就是固件那份 C++（ui/canvas/icons/font），图和屏上完全一致 | 需先编译 host.exe；样例固定北京 9 度/晴 |

## 4. 已知失效点 / 注意事项

- **缺源图**：`baseline.py`、`bench_quant.py`、`fidelity.py`、`timing.py` 引用
  `P20261021-191121.jpg`（实验时的手机照片，不随仓库分发），缺图直接 FileNotFound；
  `fidelity.py` 可用库内 `test_pattern.png` 替代。
- **图片文件分工**：`marker.png`、`test_pattern.png` 是实验输入；`upright.png`、`exif6.jpg`、
  `alpha.png`、`noise.png` 是 `check_fixes.py` 的自产 fixture（删了再跑一次就有）。
  2026-10-21 已清理 `base_*`/`new_*`/`compare_*` 前缀的量化实验输出图（可再生，409KB）。
- `cmp_small.png`（870KB）没有任何脚本引用，是人工留档的对比截图，暂留。
- 这里的实验都**真的会连设备**。跑之前确认设备已从上次的掉线状态断电重启过
  （危险输入见 CODEBUDDY.md「危险输入」一节）。
- 2026-10-21 清理：删掉 5 个早期 `diag_*.py` 连接诊断、`scan.py`（被 `tools/scan_ble.py` 取代）、
  `check_exif.py`（被 `check_fixes.py` 覆盖）、`ff04_calib.py`（结论已进 docs/PROTOCOL.md §8）——结论都已进 docs/。
