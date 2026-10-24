package com.app.ysbadge;

import android.graphics.Bitmap;
import android.nfc.tech.IsoDep;
import android.util.Log;
import androidx.core.view.ViewCompat;
import com.app.myapplication.tool.NfcCastOutSate;
import java.io.IOException;
import org.apache.xmlbeans.XmlValidationError;

/* JADX INFO: loaded from: classes2.dex */
public class NfcDataHandler {
    private static final char[] HEX_CHAR = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'};
    private static final String TAG = "NFC Data Handler...";
    byte compress_type;
    boolean dither_enable;
    byte epd_index;
    byte epd_type;
    private IsoDep isoDep;
    int nfcType;
    byte[] pic_data;
    byte[] pic_data_A;
    byte[] pic_data_B;
    byte[] pic_data_compressed;
    byte[] pic_data_one;
    byte[] pic_data_two;

    public NfcDataHandler(byte t_epd_index, IsoDep isoDep_i, Bitmap bitmap_img_one, Bitmap bitmap_img_two) {
        this.isoDep = null;
        this.nfcType = 0;
        this.epd_type = (byte) 6;
        this.compress_type = (byte) 1;
        this.dither_enable = false;
        this.isoDep = isoDep_i;
        this.epd_index = t_epd_index;
        if (this.epd_index == 7) {
            this.pic_data_one = EPD_Config.getPicData(this.epd_type, this.dither_enable, bitmap_img_one);
            this.pic_data_two = EPD_Config.getPicData(this.epd_type, this.dither_enable, bitmap_img_two);
            this.pic_data = combineBytes(this.pic_data_one, this.pic_data_two);
        } else {
            this.pic_data = EPD_Config.getPicData(this.epd_type, this.dither_enable, bitmap_img_one);
        }
        this.nfcType = 2;
    }

    public NfcDataHandler(IsoDep isoDep_i) {
        this.isoDep = null;
        this.nfcType = 0;
        this.isoDep = isoDep_i;
        this.nfcType = 1;
    }

    public static String bytesToHexString(byte[] bytes) {
        int a;
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            if (b < 0) {
                a = b + 256;
            } else {
                a = b;
            }
            sb.append(HEX_CHAR[a / 16]);
            sb.append(HEX_CHAR[a % 16]);
        }
        return sb.toString().toUpperCase();
    }

    public void start() {
        Log.e(TAG, "开始刷新");
        new MyThread().start();
    }

    class MyThread extends Thread {
        private static final int MAX_PACKET_CNT = 39;
        private static final int PACKAGE_SIZE = 9600;
        private static final int PACKET_SIZE = 240;
        private int packet_counter = 0;

        public MyThread() {
        }

        private void checkResponse(byte[] capdu, byte[] response) {
            int i = this.packet_counter;
            if (i == 0 || i == 1) {
                String result = NfcDataHandler.bytesToHexString(response);
                if (result.length() >= 4) {
                    String resultStatus = result.substring(result.length() - 4, result.length());
                    if (resultStatus.equals("9000")) {
                        String resultData = result.substring(0, result.length() - 4);
                        int i2 = this.packet_counter;
                        if (i2 == 0) {
                            NfcCastOutSate.setMac(resultData);
                        } else if (i2 == 1) {
                            NfcCastOutSate.setElectricQuantity(resultData);
                        }
                    }
                }
            }
            StringBuilder sb = new StringBuilder();
            sb.append(NfcDataHandler.bytesToHexString(capdu));
            sb.append("  NO.");
            int i3 = this.packet_counter;
            this.packet_counter = i3 + 1;
            sb.append(i3);
            Log.e(NfcDataHandler.TAG, sb.toString());
            Log.e(NfcDataHandler.TAG, "Response: " + NfcDataHandler.bytesToHexString(response));
        }

        private void handleResponse(byte[] capdu, byte[] response) {
            if (response[0] == -112 && response[1] == 0) {
                Log.e(NfcDataHandler.TAG, "CAPDU Send OK.");
                return;
            }
            if (response[0] == 101) {
                byte b = response[1];
                if (b == 0) {
                    Log.e(NfcDataHandler.TAG, "CAPDU Send Fail!");
                    return;
                }
                if (b != 1) {
                    if (b == 3) {
                        Log.e(NfcDataHandler.TAG, "Dev Auth Failed.");
                    }
                } else {
                    Log.e(NfcDataHandler.TAG, "Invalid Length. Send again!");
                    try {
                        byte[] r = NfcDataHandler.this.isoDep.transceive(capdu);
                        handleResponse(capdu, r);
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
            }
        }

        @Override // java.lang.Thread, java.lang.Runnable
        public void run() {
            NfcCastOutSate.setSate(102, "数据传输");
            try {
                try {
                    if (!NfcDataHandler.this.isoDep.isConnected()) {
                        NfcDataHandler.this.isoDep.connect();
                    }
                    NfcDataHandler.this.isoDep.setTimeout(XmlValidationError.LIST_INVALID);
                    byte[] apdu_get_mac = {-48, -47, 4, 0, 0, 8};
                    byte[] response = NfcDataHandler.this.isoDep.transceive(apdu_get_mac);
                    checkResponse(apdu_get_mac, response);
                    byte[] get_batt_lvl = {-48, -47, 5, 0, 0, 3};
                    byte[] response2 = NfcDataHandler.this.isoDep.transceive(get_batt_lvl);
                    checkResponse(get_batt_lvl, response2);
                    try {
                        if (NfcDataHandler.this.nfcType != 1) {
                            if (NfcDataHandler.this.nfcType == 2) {
                                Log.e(NfcDataHandler.TAG, "EPD_Type: " + ((int) NfcDataHandler.this.epd_type));
                                Log.e(NfcDataHandler.TAG, "EPD_Index: " + ((int) NfcDataHandler.this.epd_index));
                                byte[] apdu_epd_init = {-48, -47, 0, 0, 2, NfcDataHandler.this.epd_type, NfcDataHandler.this.epd_index, 2};
                                byte[] response3 = NfcDataHandler.this.isoDep.transceive(apdu_epd_init);
                                checkResponse(apdu_epd_init, response3);
                                Thread.sleep(100L);
                                byte[] apdu_epd_info = new byte[11];
                                apdu_epd_info[0] = -48;
                                apdu_epd_info[1] = -47;
                                apdu_epd_info[2] = 1;
                                apdu_epd_info[3] = 0;
                                apdu_epd_info[4] = 5;
                                apdu_epd_info[5] = NfcDataHandler.this.compress_type;
                                if (NfcDataHandler.this.compress_type == 0) {
                                    int length = NfcDataHandler.this.pic_data.length;
                                    apdu_epd_info[6] = (byte) (length & 255);
                                    apdu_epd_info[7] = (byte) ((65280 & length) >> 8);
                                    apdu_epd_info[8] = (byte) ((16711680 & length) >> 16);
                                    apdu_epd_info[9] = (byte) ((length & ViewCompat.MEASURED_STATE_MASK) >> 24);
                                } else if (NfcDataHandler.this.compress_type == 1) {
                                    LZ77Compress lz77Compress = new LZ77Compress();
                                    NfcDataHandler.this.pic_data_compressed = lz77Compress.Compress(NfcDataHandler.this.pic_data);
                                    System.out.print("UlNumberOfBits=");
                                    System.out.println(lz77Compress.getUlNumberOfBits());
                                    System.out.println("Compressed Data Bytes:" + NfcDataHandler.this.pic_data_compressed.length);
                                    int length2 = lz77Compress.getUlNumberOfBits();
                                    apdu_epd_info[6] = (byte) (length2 & 255);
                                    apdu_epd_info[7] = (byte) ((65280 & length2) >> 8);
                                    apdu_epd_info[8] = (byte) ((16711680 & length2) >> 16);
                                    apdu_epd_info[9] = (byte) (((-16777216) & length2) >> 24);
                                }
                                apdu_epd_info[10] = 2;
                                byte[] response4 = NfcDataHandler.this.isoDep.transceive(apdu_epd_info);
                                checkResponse(apdu_epd_info, response4);
                                Thread.sleep(100L);
                                if (NfcDataHandler.this.compress_type == 0) {
                                    SendPic(NfcDataHandler.this.pic_data);
                                } else if (NfcDataHandler.this.compress_type == 1) {
                                    SendPic(NfcDataHandler.this.pic_data_compressed);
                                }
                                byte[] apdu_epd_update = {-48, -47, 3, 0, 0, 2};
                                Thread.sleep(100L);
                                NfcDataHandler.this.isoDep.transceive(apdu_epd_update);
                                NfcCastOutSate.setSate(400, "发送完成");
                                Log.e(NfcDataHandler.TAG, "发送完成!");
                            }
                            NfcDataHandler.this.isoDep.close();
                            Log.e(NfcDataHandler.TAG, "刷新任务结束。");
                        }
                        NfcCastOutSate.setSate(400, "完成");
                        NfcDataHandler.this.isoDep.close();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                    Log.e(NfcDataHandler.TAG, "刷新任务结束。");
                } catch (IOException e2) {
                    NfcCastOutSate.setSate(401, "NFC读写错误！！！");
                    Log.e(NfcDataHandler.TAG, "NFC读写错误！！！");
                    e2.printStackTrace();
                    try {
                        NfcDataHandler.this.isoDep.close();
                    } catch (IOException e3) {
                        e = e3;
                        e.printStackTrace();
                        Log.e(NfcDataHandler.TAG, "刷新任务结束。");
                    }
                    Log.e(NfcDataHandler.TAG, "刷新任务结束。");
                } catch (InterruptedException e4) {
                    NfcCastOutSate.setSate(402, "等待Busy超时！！！");
                    e4.printStackTrace();
                    try {
                        NfcDataHandler.this.isoDep.close();
                    } catch (IOException e5) {
                        e = e5;
                        e.printStackTrace();
                        Log.e(NfcDataHandler.TAG, "刷新任务结束。");
                    }
                    Log.e(NfcDataHandler.TAG, "刷新任务结束。");
                }
            } catch (Throwable th) {
                try {
                    NfcDataHandler.this.isoDep.close();
                } catch (IOException e6) {
                    e6.printStackTrace();
                }
                Log.e(NfcDataHandler.TAG, "刷新任务结束。");
                throw th;
            }
        }

        public void SendPic(byte[] pic_data) throws InterruptedException, IOException {
            int packet_count = 0;
            int pos = 0;
            do {
                int payload_size = Math.min(pic_data.length - pos, PACKET_SIZE);
                byte[] packet = new byte[payload_size + 6];
                packet[0] = -48;
                packet[1] = -47;
                packet[2] = 2;
                packet[3] = 0;
                packet[4] = (byte) payload_size;
                packet[packet.length - 1] = 2;
                System.arraycopy(pic_data, pos, packet, 5, payload_size);
                byte[] response = NfcDataHandler.this.isoDep.transceive(packet);
                handleResponse(packet, response);
                pos += payload_size;
                packet_count++;
                if (packet_count >= 39 || pos >= pic_data.length) {
                    Log.e(NfcDataHandler.TAG, "Start Decompress & Sending...");
                    byte[] start_decompress_sending = {-48, -47, EPD_Config.EPD_CMD_START_SENDING, 0, 0, 2};
                    byte[] response2 = NfcDataHandler.this.isoDep.transceive(start_decompress_sending);
                    checkResponse(start_decompress_sending, response2);
                    while (is_decompress_sending() == -1) {
                    }
                    packet_count = 0;
                }
            } while (pos < pic_data.length);
        }

        public int is_decompress_sending() throws InterruptedException, IOException {
            byte[] get_buffer_state = {-48, -47, EPD_Config.EPD_CMD_BUFFER_EMPTY, 0, 0, 8};
            Thread.sleep(100L);
            byte[] response = NfcDataHandler.this.isoDep.transceive(get_buffer_state);
            if (response[0] == -112 && response[1] == 0) {
                Log.e(NfcDataHandler.TAG, "Decompress & Send OK.");
                return 0;
            }
            if (response[0] != -128 || response[1] != -112) {
                return -1;
            }
            Log.e(NfcDataHandler.TAG, "Decompress & Send ongoing...");
            return -1;
        }
    }

    public static byte[] combineBytes(byte[] data1, byte[] data2) {
        byte[] data3 = new byte[data1.length + data2.length];
        System.arraycopy(data1, 0, data3, 0, data1.length);
        System.arraycopy(data2, 0, data3, data1.length, data2.length);
        return data3;
    }
}
