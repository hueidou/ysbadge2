# APK 功能与实现深入分析

包名 com.app.myapplication（白标 YSBadge 电子徽章/双面墨水屏控制器）
产物：base.apk，4 个 dex（multidex），反编译约 9700 个类。协议层 7 个文件的反编译源码随仓库分发（reference/apk/apk_src/sources/com/app/ysbadge/，docs 引用的原始证据）；完整反编译树（约 9700 类，多数为无关第三方库）按 reference/apk/README.md 的方法自行生成。

## 0. 定位
绑定/编辑模板 → 生成 800x480 图片 → 通过 BLE（或 NFC）投到双面七色墨水屏设备；
同时提供设备分组、名册分组、模板、背景、字体、Excel 导入、扫码、经典蓝牙文件互传等管理功能。

## 1. 技术栈与第三方库
- AndroidX：appcompat、navigation、recyclerview、constraintlayout、lifecycle、viewpager 等
- FastBle（com.app.fastble）：内嵌 BLE 封装（扫描/连接/MTU/notify/分块写）
- Apache POI + org.openxmlformats + org.codehaus.stax2 + com.fasterxml.aalto + xmlbeans：Excel(xls/xlsx) 读写
- journeyapps barcodescanner（ZXing）：扫码
- io.reactivex（RxJava）：异步/事件
- com.graphbuilder（curve/geom/math）：曲线/几何工具
- com.google.android.material：Material 组件
- 4 dex、multidex

## 2. 权限（能力面）
- 存储：READ/WRITE_EXTERNAL_STORAGE
- 安装：REQUEST_INSTALL_PACKAGES、REPLACE_EXISTING_PACKAGE（具备安装/替换 APK 能力）
- 网络：INTERNET
- NFC：NFC
- 蓝牙：BLUETOOTH/BLUETOOTH_ADMIN/SCAN/ADVERTISE/CONNECT
- 定位：ACCESS_COARSE/FINE_LOCATION（BLE 扫描必需）
- 其他：VIBRATE、CAMERA

## 3. 组件与页面
- MainActivity：BottomNavigation + Navigation 组件；NFC 前台调度（onNewIntent → NfcCastOut）；
  首次启动 firstBoot() 初始化目录与数据库，并生成"默认模板"。
- 三个主 Tab：Equipment（设备）、CastOut（投图）、Toolkit（工具）。
- 子页面：
  - panelGroup：PanelGroupFragment/PanelDetailsFragment/PanelAddFragment/PanelEditFragment/PanelImportExcel（名册）
  - template：TemplateListFragment（模板列表）/TemplateSetting（模板编辑）
  - background：BackgroundDetailsFragment/AddBackgroundFragment/EditBackgroundFragment
  - font：FontList/FontImport
  - deviceGroup：DeviceGroupFragment/DeviceGroupDetailsFragment（设备分组/明细）
  - rapidShare：RapidShare（作为服务端）/RapidShareLink（文件互传）
  - toolkit：ToolkitFragment（入口聚合）
  - equipment：EquipmentFragment
  - CustomCaptureActivity：扫码 Activity

## 4. 数据模型（SQLite，MyDbOpenHelper，8 张表）
- panel_group(id,name,total,column_number,create_time)
- panel(id,information_1..5,panel_group_id,column_number)        名册一行
- template(id,name,column_number,background_id,effect_img)        模板
- template_information(id,template_id,sequence,width,height,co_x,co_y,font_family,font_type,font_size,font_alignment,font_weight,font_color)
- background_management(id,title,image_path,create_time)
- device_group(id,name,device_nums,create_time)
- device(id,device_group_id,mac,sequence_number)
- font(id,name,location)

实体（entity/）：PanelGroup、Panel、Template、TemplateInformation、BackgroundImage、DeviceGroup、Device、
CatFont、MyFont、Bluetooth、BluetoothCastOutInformation、KeyValue、IconText。
全局状态（MyApplication）：template_id_a、template_id_b、panel_group_id、background_id。

## 5. 核心流程：投图（CastOut）
1. 选择 A/B 两面模板（template_id_a/b），可选"名册分组"或"手动输入"：
   - tab_index=0 手动录入信息一~五
   - tab_index=1 从 PanelGroup/Panel（或 Excel 导入的名册）取每台设备对应一行
2. 生成图片：CreateTemplateImg.CreateTemplateBitmap(context, informationNum, img_path, alti, als, fs)
   - 固定 800x480 ARGB 画布
   - 背景图 drawBitmap(bm,0,0,null) 原样贴（不缩放）
   - 按 TemplateInformation 逐条绘制文字：字体/字号/颜色/对齐/坐标/宽高
   - 结果存 jpg（effect_img），供预览与投图复用
3. 扫描设备：FastBle，规则 setDeviceName(true,"YSBadge")，超时 10s
4. 连接并投图（BluetoothTool）：
   connect → setMtu(256) → 使能 ff04 通知 → INIT → PIC_INFO → 分块写 ff02(40ms) → 断开
5. 投图类型（cast_type → epd_index）：
   - 只 A = 1，只 B = 2，A&B 同显 = 3，A&B 异显 = 7
6. 多设备队列 BluetoothCastOutInformationList：依次投图、失败重试、状态机（1 待发/2 成功/3 失败）

## 6. 图片与协议层（com.app.ysbadge）
- EPD_Config：命令构造与像素编码
  - 命令：INIT(0)、SEND_PIC_INFO(1)、SEND_PIC(2)、UPDATE(3)、GET_MAC(4)、GET_BATTERY(5)、DEVICE_VERIFICATION(0x88)、START_SENDING(0xA0)、BUFFER_EMPTY(0xA1)
  - 面板类型枚举 18 种（BW/E4/E5/NColor…），epd_size 表；默认 epd_type=6（NColor 0730，800x480）
  - getPicData 按类型分发；4bit 路径为 getPicData_NColor_4bit（7 色最近邻 + 4bit/px 打包）
- BMPConverter：调色板(deviceType 0/1/2/3/4)；thresholding（最近色，欧氏距离）；floydSteinbergDither（误差扩散）
- LZ77Compress：自研 LZ77（窗口1024，偏移10bit，Golomb m=3），输出比特数用于 PIC_INFO
- CrcCheckUtil：CRC-16/MODBUS 查表；get_EPD_CMD_* 带 crc_enable 分支（BLE 传输实际用 false，不带 CRC）
- NfcDataHandler：NFC(ISO-DEP/APDU) 投图完整链路
  GET_MAC → GET_BATTERY → INIT → PIC_INFO → SendPic（240字节/包，每批≤39包）→ UPDATE
  并解析响应码（0x9000 成功、101/x 长度/鉴权错误）
- HttpDownloader：HttpURLConnection GET 下载到本地（快速分享拉取用）

## 7. 分享功能（经典蓝牙，非 BLE 投图）
- RapidShare：本机作为 RFCOMM Server（listenUsingRfcommWithServiceRecord），
  请求可被发现 120s，扫描附近手机，BlueToothAccept 线程接收连接。
- RapidShareLink：作为客户端 createRfcommSocketToServiceRecord 连接，经 OutputStream 传文件。
- 用途：手机间互传图片/模板等，与墨水屏 BLE 投图是两套通道。

## 8. 名册 / 模板 / 背景 / 字体
- 名册：PanelGroup + Panel(information_1..5)；PanelImportExcel + ExcelUtils 用 POI 解析
  （跳过表头；第 1 列判断非空，第 2..5 列取信息）。
- 模板：Template + 最多 5 条 TemplateInformation；TemplateSetting 用 SeekBar 调字号/宽高/坐标、
  Spinner 选字体与列数、按钮选对齐、选颜色；实时生成预览图。
- 背景：BackgroundImage 管理图片路径，支持新增/编辑/删除/设为主背景。
- 字体：FontImport 导入字体文件到应用目录；TypefaceHelper/MyFontList 加载；CatFont 内置分类。

## 9. 工具类（tool/，29 个）
BluetoothTool、BluetoothToolShare、BluetoothCastOutInformationList（BLE 投图与队列）、
CreateTemplateImg（出图）、NfcManager、NfcCastOutSate（NFC 状态）、QRCodeTool、CustomCaptureActivity（扫码）、
ExcelUtils、FileChooseUtil/Uri2PathUtil/FileUtil/CopyFileUtils/FileDirTool/LocalFileTool（文件）、
DeviceInfo、MyApplication、MyToast/MyDialog/DialogGeneral/DialogGeneralList/DialogFastCheck（UI）、
MyAdapter/MyPagerAdapter/IconText、MyDbOpenHelper/MyDbOpenHelperSingle、MyColorList、MyFontList、TypefaceHelper。

## 10. 实现特点与风险点
- 权限偏大：具备安装/替换 APK 能力（REQUEST_INSTALL_PACKAGES + REPLACE_EXISTING_PACKAGE），配合 INTERNET 可做自升级/下发安装。
- 协议明文、无鉴权：BLE 路径无 CRC、无 DEV_AUTH；NFC 路径才有响应码/鉴权分支。
- 大量硬编码：epd_type=6、compress_type=1、800x480、扫描名前缀 "YSBadge"、字体/颜色默认值。
- 投图强依赖压缩体积：设备侧约 32KB(262144bit) 上限，App 通过"从不抖动(dither_enable 恒 false)+800x480"隐式满足；无发送前体积校验。
- NFC 链路比 BLE 完整（含 UPDATE 与响应校验），BLE 链路被简化。
- 双面通过 epd_index 选择；实测该固件 index 1/3 稳定，index 2 单发有效，index 7（异显）
  2026-10-21 在压缩模式下验证通过（两图合并 63063 bit，两面分别正确显示）；连续快发易被"刷新中"吞掉。

## 11. 关键类索引（便于二次开发）
- 投图入口：p003ui/castOut/CastOutFragment（UI/流程）、tool/BluetoothTool（BLE 发送）
- 出图：tool/CreateTemplateImg、ysbadge/EPD_Config、ysbadge/BMPConverter
- 压缩：ysbadge/LZ77Compress
- NFC：ysbadge/NfcDataHandler、tool/NfcManager
- 数据：mydb/*Sql、tool/MyDbOpenHelper
- 分享：p003ui/rapidShare/*、tool/BluetoothToolShare、tool/BlueToothAccept
