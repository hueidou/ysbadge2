package com.app.ysbadge;

import android.graphics.Bitmap;
import androidx.core.view.ViewCompat;
import androidx.recyclerview.widget.ItemTouchHelper;
import com.app.ysbadge.utils.CrcCheckUtil;
import java.lang.reflect.Array;

/* JADX INFO: loaded from: classes2.dex */
public class EPD_Config {
    public static final byte EPD_CMD_BUFFER_EMPTY = -95;
    public static final byte EPD_CMD_DEVICE_VERIFICATION = -120;
    public static final byte EPD_CMD_GET_BATTERY_LEVEL = 5;
    public static final byte EPD_CMD_GET_DEVICE_MAC = 4;
    public static final byte EPD_CMD_INIT = 0;
    public static final byte EPD_CMD_SEND_PIC = 2;
    public static final byte EPD_CMD_SEND_PIC_INFO = 1;
    public static final byte EPD_CMD_START_SENDING = -96;
    public static final byte EPD_CMD_UPDATE = 3;
    public static final byte EPD_INDEX_A = 1;
    public static final byte EPD_INDEX_AB_DIFF = 7;
    public static final byte EPD_INDEX_AB_SAME = 3;
    public static final byte EPD_INDEX_B = 2;
    public static final byte EPD_TYPE_BW_0213 = 13;
    public static final byte EPD_TYPE_BW_0213_HINK = 12;
    public static final byte EPD_TYPE_BW_0290 = 14;
    public static final byte EPD_TYPE_BW_0290_HINK = 17;
    public static final byte EPD_TYPE_BW_0370 = 0;
    public static final byte EPD_TYPE_BW_0750_800 = 2;
    public static final byte EPD_TYPE_E4_0213 = 15;
    public static final byte EPD_TYPE_E4_0213_HINK = 10;
    public static final byte EPD_TYPE_E4_0290 = 16;
    public static final byte EPD_TYPE_E4_0370 = 1;
    public static final byte EPD_TYPE_E4_0420 = 7;
    public static final byte EPD_TYPE_E4_0420_WF = 9;
    public static final byte EPD_TYPE_E4_0583 = 11;
    public static final byte EPD_TYPE_E4_0750_800 = 3;
    public static final byte EPD_TYPE_E4_0750_880 = 8;
    public static final byte EPD_TYPE_E5_0730 = 4;
    public static final byte EPD_TYPE_NCOLOR_0565 = 5;
    public static final byte EPD_TYPE_NCOLOR_0730 = 6;
    public static final byte LZ7_COMPRESS = 1;
    public static final byte NO_COMPRESS = 0;
    public static final String[] m_sides = {"Side A", "Side B", "Side A&B 同显", "Side A&B 异显"};
    public static final byte[] m_sides_b = {1, 2, 3, 7};
    public static final String[] m_types = {"EPD_TYPE_BW_0370", "EPD_TYPE_E4_0370", "EPD_TYPE_BW_0750_800", "EPD_TYPE_E4_0750_800", "EPD_TYPE_E5_0730", "EPD_TYPE_NCOLOR_0565", "EPD_TYPE_NCOLOR_0730", "EPD_TYPE_E4_0420", "EPD_TYPE_E4_0750_880", "EPD_TYPE_E4_0420_WF", "EPD_TYPE_E4_0213_HINK", "EPD_TYPE_E4_0583", "EPD_TYPE_BW_0213_HINK", "EPD_TYPE_BW_0213", "EPD_TYPE_BW_0290", "EPD_TYPE_E4_0213", "EPD_TYPE_E4_0290", "EPD_TYPE_BW_0290_HINK"};
    public static final byte[] m_types_b = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17};
    public static final int[][] epd_size = {new int[]{240, 416}, new int[]{240, 416}, new int[]{800, 480}, new int[]{800, 480}, new int[]{800, 480}, new int[]{600, 448}, new int[]{800, 480}, new int[]{400, 300}, new int[]{880, 528}, new int[]{400, 300}, new int[]{128, ItemTouchHelper.Callback.DEFAULT_SWIPE_ANIMATION_DURATION}, new int[]{648, 480}, new int[]{128, ItemTouchHelper.Callback.DEFAULT_SWIPE_ANIMATION_DURATION}, new int[]{128, ItemTouchHelper.Callback.DEFAULT_SWIPE_ANIMATION_DURATION}, new int[]{128, 296}, new int[]{128, ItemTouchHelper.Callback.DEFAULT_SWIPE_ANIMATION_DURATION}, new int[]{128, 296}, new int[]{128, 296}};
    public static final String[] m_compress = {"No Compress", "LZ7 Compress"};
    public static final byte[] m_compress_b = {0, 1};
    public static final String[] m_dither = {"No Dither", "Dither"};

    public static byte[] get_EPD_CMD_UPDATE(boolean crc_enable) {
        if (crc_enable) {
            byte[] cmd = {0, 0, (byte) ((packet_crc >> 8) & 255), (byte) (packet_crc & 255), 3, 0};
            int packet_crc = CrcCheckUtil.calcCrc16(cmd, 4, 2);
            return cmd;
        }
        return new byte[]{3, 0};
    }

    public static byte[] get_EPD_CMD_INIT(byte epd_type, byte epd_index, boolean crc_enable) {
        if (crc_enable) {
            byte[] cmd = {0, 0, (byte) ((packet_crc >> 8) & 255), (byte) (packet_crc & 255), 0, epd_type, epd_index};
            int packet_crc = CrcCheckUtil.calcCrc16(cmd, 4, 3);
            return cmd;
        }
        return new byte[]{0, epd_type, epd_index};
    }

    public static byte[] get_EPD_CMD_SEND_PIC_INFO(byte compress_type, int sizeof_data_to_send, boolean crc_enable) {
        if (crc_enable) {
            byte[] cmd = {0, 0, (byte) ((packet_crc >> 8) & 255), (byte) (packet_crc & 255), 1, compress_type, (byte) (sizeof_data_to_send & 255), (byte) ((65280 & sizeof_data_to_send) >> 8), (byte) ((sizeof_data_to_send & 16711680) >> 16), (byte) (((-16777216) & sizeof_data_to_send) >> 24)};
            int packet_crc = CrcCheckUtil.calcCrc16(cmd, 4, 6);
            return cmd;
        }
        return new byte[]{1, compress_type, (byte) (sizeof_data_to_send & 255), (byte) ((65280 & sizeof_data_to_send) >> 8), (byte) ((16711680 & sizeof_data_to_send) >> 16), (byte) (((-16777216) & sizeof_data_to_send) >> 24)};
    }

    public static byte[] get_EPD_CMD_DEV_AUTH(byte[] mac, boolean crc_enable) {
        byte[] key = new byte[6];
        for (int i = 0; i < 6; i++) {
            key[i] = (byte) (((-(mac[i] + 1)) + 37) & 255);
        }
        if (crc_enable) {
            byte[] cmd = {0, 0, (byte) ((packet_crc >> 8) & 255), (byte) (packet_crc & 255), EPD_CMD_DEVICE_VERIFICATION, key[0], key[1], key[2], key[3], key[4], key[5]};
            int packet_crc = CrcCheckUtil.calcCrc16(cmd, 4, 7);
            return cmd;
        }
        return new byte[]{EPD_CMD_DEVICE_VERIFICATION, key[0], key[1], key[2], key[3], key[4], key[5]};
    }

    public static byte[] getPicData(int epd_type, boolean dither_enable, Bitmap bitmap) {
        Bitmap bitmap2;
        Bitmap bitmap3;
        Bitmap bitmap4;
        Bitmap bitmap5;
        Bitmap bitmap6;
        Bitmap bitmap7;
        switch (epd_type) {
            case 0:
            case 2:
            case 12:
            case 13:
            case 14:
            case 17:
                if (dither_enable) {
                    bitmap2 = getDitheredBitmap(bitmap, 0);
                } else {
                    bitmap2 = getThresholdedBitmap(bitmap, 0);
                }
                byte[] pic_data = getPicData_BW_1bit(bitmap2);
                return pic_data;
            case 1:
            case 7:
            case 8:
            case 10:
            case 11:
            case 15:
            case 16:
                if (dither_enable) {
                    bitmap3 = getDitheredBitmap(bitmap, 1);
                } else {
                    bitmap3 = getThresholdedBitmap(bitmap, 1);
                }
                byte[] pic_data2 = getPicData_E4_1bit(bitmap3);
                return pic_data2;
            case 3:
                if (dither_enable) {
                    bitmap4 = getDitheredBitmap(bitmap, 1);
                } else {
                    bitmap4 = getThresholdedBitmap(bitmap, 1);
                }
                byte[] pic_data3 = getPicData_E4_1bit_Reverse(bitmap4);
                return pic_data3;
            case 4:
                if (dither_enable) {
                    bitmap5 = getDitheredBitmap(bitmap, 3);
                } else {
                    bitmap5 = getThresholdedBitmap(bitmap, 3);
                }
                byte[] pic_data4 = getPicData_E5_2bit(bitmap5);
                return pic_data4;
            case 5:
            case 6:
                if (dither_enable) {
                    bitmap6 = getDitheredBitmap(bitmap, 4);
                } else {
                    bitmap6 = getThresholdedBitmap(bitmap, 4);
                }
                byte[] pic_data5 = getPicData_NColor_4bit(bitmap6);
                return pic_data5;
            case 9:
                if (dither_enable) {
                    bitmap7 = getDitheredBitmap(bitmap, 1);
                } else {
                    bitmap7 = getThresholdedBitmap(bitmap, 1);
                }
                byte[] pic_data6 = getPicData_E4_1bit_Reverse_Reverse(bitmap7);
                return pic_data6;
            default:
                return null;
        }
    }

    public static Bitmap getDitheredBitmap(Bitmap bitmap, int device_type) {
        RGBTriple[][] image = (RGBTriple[][]) Array.newInstance((Class<?>) RGBTriple.class, bitmap.getWidth(), bitmap.getHeight());
        for (int i = 0; i < bitmap.getWidth(); i++) {
            for (int j = 0; j < bitmap.getHeight(); j++) {
                int argb = bitmap.getPixel(i, j);
                image[i][j] = new RGBTriple();
                image[i][j].channels[0] = (byte) ((16711680 & argb) >> 16);
                image[i][j].channels[1] = (byte) ((65280 & argb) >> 8);
                image[i][j].channels[2] = (byte) (argb & 255);
            }
        }
        byte[][] dithered_index = BMPConverter.floydSteinbergDither(image, BMPConverter.getPalette(device_type));
        for (int i2 = 0; i2 < bitmap.getWidth(); i2++) {
            for (int j2 = 0; j2 < bitmap.getHeight(); j2++) {
                bitmap.setPixel(i2, j2, BMPConverter.getPalette(device_type)[dithered_index[i2][j2]].getColor());
            }
        }
        return bitmap;
    }

    private static Bitmap getThresholdedBitmap(Bitmap bitmap, int device_type) {
        RGBTriple[][] image = (RGBTriple[][]) Array.newInstance((Class<?>) RGBTriple.class, bitmap.getWidth(), bitmap.getHeight());
        for (int i = 0; i < bitmap.getWidth(); i++) {
            for (int j = 0; j < bitmap.getHeight(); j++) {
                int argb = bitmap.getPixel(i, j);
                image[i][j] = new RGBTriple();
                image[i][j].channels[0] = (byte) ((16711680 & argb) >> 16);
                image[i][j].channels[1] = (byte) ((65280 & argb) >> 8);
                image[i][j].channels[2] = (byte) (argb & 255);
            }
        }
        byte[][] dithered_index = BMPConverter.thresholding(image, BMPConverter.getPalette(device_type));
        for (int i2 = 0; i2 < bitmap.getWidth(); i2++) {
            for (int j2 = 0; j2 < bitmap.getHeight(); j2++) {
                bitmap.setPixel(i2, j2, BMPConverter.getPalette(device_type)[dithered_index[i2][j2]].getColor());
            }
        }
        return bitmap;
    }

    private static byte[] getPicData_BW_1bit(Bitmap bitmap) {
        int width = bitmap.getWidth();
        int height = bitmap.getHeight();
        int rwidth = ((width + 7) / 8) * 8;
        byte[] pic_data = new byte[(rwidth * height) / 8];
        byte temp_mono = 0;
        int bit_count = 0;
        int byte_count = 0;
        for (int j = 0; j < height; j++) {
            for (int i = width - 1; i >= 0; i--) {
                int rgb = bitmap.getPixel(i, j) & ViewCompat.MEASURED_SIZE_MASK;
                temp_mono = (byte) (temp_mono << 1);
                if (rgb == 16777215) {
                    temp_mono = (byte) (temp_mono | 1);
                }
                bit_count++;
                if (bit_count == 8) {
                    pic_data[byte_count] = temp_mono;
                    byte_count++;
                    temp_mono = 0;
                    bit_count = 0;
                }
            }
        }
        return pic_data;
    }

    private static byte[] getPicData_E4_1bit(Bitmap bitmap) {
        int width = bitmap.getWidth();
        int height = bitmap.getHeight();
        byte[] pic_data = new byte[(width * height) / 4];
        int r_offset = (width * height) / 8;
        byte temp_mono = 0;
        byte temp_r = 0;
        int bit_count = 0;
        int byte_count = 0;
        for (int j = height - 1; j >= 0; j--) {
            for (int i = 0; i < width; i++) {
                int rgb = bitmap.getPixel(i, j) & ViewCompat.MEASURED_SIZE_MASK;
                temp_mono = (byte) (temp_mono << 1);
                temp_r = (byte) (temp_r << 1);
                if (rgb == 16777215) {
                    temp_mono = (byte) (temp_mono | 1);
                } else if (rgb == 16711680) {
                    temp_r = (byte) (temp_r | 1);
                    temp_mono = (byte) (temp_mono | 1);
                }
                bit_count++;
                if (bit_count == 8) {
                    pic_data[byte_count] = temp_mono;
                    pic_data[byte_count + r_offset] = temp_r;
                    byte_count++;
                    temp_mono = 0;
                    temp_r = 0;
                    bit_count = 0;
                }
            }
        }
        return pic_data;
    }

    private static byte[] getPicData_E4_1bit_Reverse(Bitmap bitmap) {
        int width = bitmap.getWidth();
        int height = bitmap.getHeight();
        byte[] pic_data = new byte[(width * height) / 4];
        int r_offset = (width * height) / 8;
        byte temp_mono = 0;
        byte temp_r = 0;
        int bit_count = 0;
        int byte_count = 0;
        for (int j = 0; j < height; j++) {
            for (int i = 0; i < width; i++) {
                int rgb = 16777215 & bitmap.getPixel(i, j);
                temp_mono = (byte) (temp_mono << 1);
                temp_r = (byte) (temp_r << 1);
                if (rgb == 0) {
                    temp_mono = (byte) (temp_mono | 1);
                } else if (rgb == 16711680) {
                    temp_r = (byte) (temp_r | 1);
                    temp_mono = (byte) (temp_mono | 1);
                }
                bit_count++;
                if (bit_count == 8) {
                    pic_data[byte_count] = temp_mono;
                    pic_data[byte_count + r_offset] = temp_r;
                    byte_count++;
                    temp_mono = 0;
                    temp_r = 0;
                    bit_count = 0;
                }
            }
        }
        return pic_data;
    }

    private static byte[] getPicData_E4_1bit_Reverse_Reverse(Bitmap bitmap) {
        int width = bitmap.getWidth();
        int height = bitmap.getHeight();
        byte[] pic_data = new byte[(width * height) / 4];
        int r_offset = (width * height) / 8;
        byte temp_mono = 0;
        byte temp_r = 0;
        int bit_count = 0;
        int byte_count = 0;
        for (int j = 0; j < height; j++) {
            for (int i = 0; i < width; i++) {
                int rgb = 16777215 & bitmap.getPixel(i, j);
                temp_mono = (byte) (temp_mono << 1);
                temp_r = (byte) (temp_r << 1);
                if (rgb == 0) {
                    temp_mono = (byte) (temp_mono | 1);
                } else if (rgb == 16711680) {
                    temp_r = (byte) (temp_r | 1);
                    temp_mono = (byte) (temp_mono | 1);
                }
                bit_count++;
                if (bit_count == 8) {
                    pic_data[byte_count] = (byte) (temp_mono ^ (-1));
                    pic_data[byte_count + r_offset] = (byte) (temp_r ^ (-1));
                    byte_count++;
                    temp_mono = 0;
                    temp_r = 0;
                    bit_count = 0;
                }
            }
        }
        return pic_data;
    }

    private static byte[] getPicData_E5_2bit(Bitmap bitmap) {
        int width = bitmap.getWidth();
        int height = bitmap.getHeight();
        byte[] pic_data = new byte[(width * height) / 4];
        byte temp = 0;
        int bit_count = 0;
        int byte_count = 0;
        for (int j = 0; j < height; j++) {
            for (int i = 0; i < width; i++) {
                int rgb = bitmap.getPixel(i, j) & ViewCompat.MEASURED_SIZE_MASK;
                temp = (byte) (temp << 2);
                if (rgb == 16777215) {
                    temp = (byte) (temp | 1);
                } else if (rgb == 16776960) {
                    temp = (byte) (temp | 2);
                } else if (rgb == 16711680) {
                    temp = (byte) (temp | 3);
                }
                bit_count += 2;
                if (bit_count == 8) {
                    pic_data[byte_count] = temp;
                    byte_count++;
                    temp = 0;
                    bit_count = 0;
                }
            }
        }
        return pic_data;
    }

    private static byte[] getPicData_NColor_4bit(Bitmap bitmap) {
        int width = bitmap.getWidth();
        int height = bitmap.getHeight();
        byte[] pic_data = new byte[(width * height) / 2];
        byte temp = 0;
        int bit_count = 0;
        int byte_count = 0;
        for (int j = 0; j < height; j++) {
            for (int i = 0; i < width; i++) {
                int rgb = bitmap.getPixel(i, j) & ViewCompat.MEASURED_SIZE_MASK;
                temp = (byte) (temp << 4);
                if (rgb == 16777215) {
                    temp = (byte) (temp | 1);
                } else if (rgb == 65280) {
                    temp = (byte) (temp | 2);
                } else if (rgb == 255) {
                    temp = (byte) (temp | 3);
                } else if (rgb == 16711680) {
                    temp = (byte) (temp | 4);
                } else if (rgb == 16776960) {
                    temp = (byte) (temp | 5);
                } else if (rgb == 16744448) {
                    temp = (byte) (temp | 6);
                }
                bit_count += 4;
                if (bit_count == 8) {
                    pic_data[byte_count] = temp;
                    byte_count++;
                    temp = 0;
                    bit_count = 0;
                }
            }
        }
        return pic_data;
    }
}
