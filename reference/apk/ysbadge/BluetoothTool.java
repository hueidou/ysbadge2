package com.app.myapplication.tool;

import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattService;
import android.graphics.Bitmap;
import android.util.Log;
import com.app.fastble.BleManager;
import com.app.fastble.callback.BleGattCallback;
import com.app.fastble.callback.BleMtuChangedCallback;
import com.app.fastble.callback.BleNotifyCallback;
import com.app.fastble.callback.BleWriteCallback;
import com.app.fastble.data.BleDevice;
import com.app.fastble.exception.BleException;
import com.app.ysbadge.EPD_Config;
import com.app.ysbadge.LZ77Compress;
import java.util.List;
import java.util.UUID;

/* JADX INFO: loaded from: classes2.dex */
public class BluetoothTool {
    byte compress_type;
    BleDevice currentConnectedDevice;
    boolean dither_enable;
    byte epd_index;
    byte epd_type;
    byte[] pic_data;
    byte[] pic_data_compressed;
    private final String TAG = "BluetoothTool";
    private final String uuid_string_service_epd = "0000ff01-0000-1000-8000-00805f9b34fb";
    private final String uuid_string_epd_write_pic = "0000ff02-0000-1000-8000-00805f9b34fb";
    private final String uuid_string_epd_write_cmd = "0000ff03-0000-1000-8000-00805f9b34fb";
    private final String uuid_string_epd_notify = "0000ff04-0000-1000-8000-00805f9b34fb";
    private BleWriteCallback CmdCallback = new BleWriteCallback() { // from class: com.app.myapplication.tool.BluetoothTool.3
        @Override // com.app.fastble.callback.BleWriteCallback
        public void onWriteSuccess(int current, int total, byte[] justWrite) {
            byte[] cmd;
            byte b = justWrite[0];
            if (b == 0) {
                Log.e("BluetoothTool", "Send EPD_CMD_INIT OK.");
                if (BluetoothTool.this.compress_type == 0) {
                    cmd = EPD_Config.get_EPD_CMD_SEND_PIC_INFO(BluetoothTool.this.compress_type, BluetoothTool.this.pic_data.length, false);
                } else {
                    LZ77Compress lz77Compress = new LZ77Compress();
                    BluetoothTool bluetoothTool = BluetoothTool.this;
                    bluetoothTool.pic_data_compressed = lz77Compress.Compress(bluetoothTool.pic_data);
                    cmd = EPD_Config.get_EPD_CMD_SEND_PIC_INFO(BluetoothTool.this.compress_type, lz77Compress.getUlNumberOfBits(), false);
                }
                BluetoothTool bluetoothTool2 = BluetoothTool.this;
                bluetoothTool2.SendCmd(bluetoothTool2.currentConnectedDevice, cmd, BluetoothTool.this.CmdCallback);
                return;
            }
            if (b == 1) {
                Log.e("BluetoothTool", "Send EPD_CMD_PIC_INFO OK.");
                if (BluetoothTool.this.compress_type == 0) {
                    BluetoothTool bluetoothTool3 = BluetoothTool.this;
                    bluetoothTool3.SendPicture(bluetoothTool3.currentConnectedDevice, BluetoothTool.this.pic_data);
                } else if (BluetoothTool.this.compress_type == 1) {
                    System.out.println(" pic_data_compressed.length;:" + BluetoothTool.this.pic_data_compressed.length);
                }
                BluetoothTool bluetoothTool4 = BluetoothTool.this;
                bluetoothTool4.SendPicture(bluetoothTool4.currentConnectedDevice, BluetoothTool.this.pic_data_compressed);
            }
        }

        @Override // com.app.fastble.callback.BleWriteCallback
        public void onWriteFailure(BleException exception) {
            Log.e("BluetoothTool", "发送命令失败！");
        }
    };

    public BluetoothTool() {
        initType();
    }

    public void initType() {
        this.epd_type = (byte) 6;
        this.compress_type = (byte) 1;
        this.dither_enable = false;
    }

    public void sendImg(byte t_epd_index, final BleDevice bleDevice, Bitmap bitmap_img_one, Bitmap bitmap_img_two) {
        this.epd_index = t_epd_index;
        if (this.epd_index == 7) {
            byte[] pic_data_one = EPD_Config.getPicData(this.epd_type, this.dither_enable, bitmap_img_one);
            byte[] pic_data_two = EPD_Config.getPicData(this.epd_type, this.dither_enable, bitmap_img_two);
            this.pic_data = combineBytes(pic_data_one, pic_data_two);
        } else {
            this.pic_data = EPD_Config.getPicData(this.epd_type, this.dither_enable, bitmap_img_one);
        }
        this.currentConnectedDevice = bleDevice;
        BleManager.getInstance().connect(bleDevice, new BleGattCallback() { // from class: com.app.myapplication.tool.BluetoothTool.1
            @Override // com.app.fastble.callback.BleGattCallback
            public void onStartConnect() {
                Log.e("BluetoothTool", "开始连接：" + bleDevice.getName() + "[" + bleDevice.getMac() + "]");
            }

            @Override // com.app.fastble.callback.BleGattCallback
            public void onConnectFail(BleDevice bleDevice2, BleException exception) {
                Log.e("BluetoothTool", "连接失败！");
                BluetoothCastOutInformationList.setIState(3);
            }

            @Override // com.app.fastble.callback.BleGattCallback
            public void onConnectSuccess(BleDevice bleDevice2, BluetoothGatt gatt, int status) {
                BluetoothTool.this.setMtu(bleDevice2, 256);
            }

            @Override // com.app.fastble.callback.BleGattCallback
            public void onDisConnected(boolean isActiveDisConnected, BleDevice bleDevice2, BluetoothGatt gatt, int status) {
                if (isActiveDisConnected) {
                    Log.e("BluetoothTool", "主动断开连接！");
                } else {
                    Log.e("BluetoothTool", "断开连接！");
                }
            }
        });
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void setMtu(final BleDevice bleDevice, int mtu) {
        BleManager.getInstance().setMtu(bleDevice, mtu, new BleMtuChangedCallback() { // from class: com.app.myapplication.tool.BluetoothTool.2
            @Override // com.app.fastble.callback.BleMtuChangedCallback
            public void onSetMTUFailure(BleException exception) {
                Log.e("BluetoothTool", "MTU设置失败：" + exception.toString());
            }

            @Override // com.app.fastble.callback.BleMtuChangedCallback
            public void onMtuChanged(int mtu2) {
                Log.e("BluetoothTool", "MTU设置成功: " + mtu2);
                BleManager.getInstance().setSplitWriteNum(mtu2 + (-3));
                BluetoothGatt bluetoothGatt = BleManager.getInstance().getBluetoothGatt(bleDevice);
                List<BluetoothGattService> serviceList = bluetoothGatt.getServices();
                for (BluetoothGattService service : serviceList) {
                    UUID uuid_service = service.getUuid();
                    Log.e("BluetoothTool", "发现一个主服务：[" + uuid_service.toString() + "]");
                    List<BluetoothGattCharacteristic> characteristicList = service.getCharacteristics();
                    for (BluetoothGattCharacteristic characteristic : characteristicList) {
                        UUID uuid_chara = characteristic.getUuid();
                        Log.e("BluetoothTool", "    发现一个特征：[" + uuid_chara.toString() + "]");
                    }
                }
                BleManager.getInstance().notify(bleDevice, "0000ff01-0000-1000-8000-00805f9b34fb", "0000ff04-0000-1000-8000-00805f9b34fb", new BleNotifyCallback() { // from class: com.app.myapplication.tool.BluetoothTool.2.1
                    @Override // com.app.fastble.callback.BleNotifyCallback
                    public void onNotifySuccess() {
                        Log.e("BluetoothTool", "打开Notify成功！");
                        byte[] cmd = EPD_Config.get_EPD_CMD_INIT(BluetoothTool.this.epd_type, BluetoothTool.this.epd_index, false);
                        BluetoothTool.this.SendCmd(bleDevice, cmd, BluetoothTool.this.CmdCallback);
                    }

                    @Override // com.app.fastble.callback.BleNotifyCallback
                    public void onNotifyFailure(BleException exception) {
                        BluetoothCastOutInformationList.setIState(3);
                        Log.e("BluetoothTool", "打开Notify失败！");
                    }

                    @Override // com.app.fastble.callback.BleNotifyCallback
                    public void onCharacteristicChanged(byte[] data) {
                        Log.e("BluetoothTool", "收到Notify：" + ((int) data[0]));
                    }
                });
            }
        });
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void SendCmd(BleDevice bleDevice, byte[] cmd, BleWriteCallback callback) {
        BleManager.getInstance().write(bleDevice, "0000ff01-0000-1000-8000-00805f9b34fb", "0000ff03-0000-1000-8000-00805f9b34fb", cmd, callback);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void SendPicture(final BleDevice bleDevice, byte[] pic_data) {
        try {
            Thread.sleep(500L);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        BleManager.getInstance().write(bleDevice, "0000ff01-0000-1000-8000-00805f9b34fb", "0000ff02-0000-1000-8000-00805f9b34fb", pic_data, true, true, 40L, new BleWriteCallback() { // from class: com.app.myapplication.tool.BluetoothTool.4
            @Override // com.app.fastble.callback.BleWriteCallback
            public void onWriteSuccess(int current, int total, byte[] justWrite) {
                Log.e("BluetoothTool", "发送数据成功：分包" + current + "/" + total + "。当前包长度：" + justWrite.length);
                if (current == total) {
                    Log.e("BluetoothTool", "图片发送完成！");
                    try {
                        Thread.sleep(1000L);
                    } catch (InterruptedException e2) {
                        e2.printStackTrace();
                    }
                    BleManager.getInstance().disconnect(bleDevice);
                    BluetoothCastOutInformationList.setIState(2);
                }
            }

            @Override // com.app.fastble.callback.BleWriteCallback
            public void onWriteFailure(BleException exception) {
                BluetoothCastOutInformationList.setIState(3);
                Log.e("BluetoothTool", "发送数据失败！");
            }
        });
    }

    public static byte[] combineBytes(byte[] data1, byte[] data2) {
        byte[] data3 = new byte[data1.length + data2.length];
        System.arraycopy(data1, 0, data3, 0, data1.length);
        System.arraycopy(data2, 0, data3, data1.length, data2.length);
        return data3;
    }
}
