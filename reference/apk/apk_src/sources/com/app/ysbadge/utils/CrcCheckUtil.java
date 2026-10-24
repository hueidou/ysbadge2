package com.app.ysbadge.utils;

import com.app.ysbadge.EPD_Config;
import org.apache.poi.hssf.record.PaletteRecord;
import org.apache.poi.p011ss.formula.ptg.Area3DPtg;
import org.apache.poi.p011ss.formula.ptg.AreaErrPtg;
import org.apache.poi.p011ss.formula.ptg.AttrPtg;
import org.apache.poi.p011ss.formula.ptg.BoolPtg;
import org.apache.poi.p011ss.formula.ptg.DeletedArea3DPtg;
import org.apache.poi.p011ss.formula.ptg.DeletedRef3DPtg;
import org.apache.poi.p011ss.formula.ptg.IntPtg;
import org.apache.poi.p011ss.formula.ptg.MemFuncPtg;
import org.apache.poi.p011ss.formula.ptg.MissingArgPtg;
import org.apache.poi.p011ss.formula.ptg.NumberPtg;
import org.apache.poi.p011ss.formula.ptg.ParenthesisPtg;
import org.apache.poi.p011ss.formula.ptg.PercentPtg;
import org.apache.poi.p011ss.formula.ptg.Ptg;
import org.apache.poi.p011ss.formula.ptg.Ref3DPtg;
import org.apache.poi.p011ss.formula.ptg.RefErrorPtg;
import org.apache.poi.p011ss.formula.ptg.RefNPtg;
import org.apache.poi.p011ss.formula.ptg.RefPtg;
import org.apache.poi.p011ss.formula.ptg.StringPtg;
import org.apache.poi.p011ss.formula.ptg.UnaryMinusPtg;
import org.apache.poi.p011ss.formula.ptg.UnaryPlusPtg;

/* JADX INFO: loaded from: classes2.dex */
public class CrcCheckUtil {
    private static final int POLYNOMIAL = 40961;
    private static final int PRESET_VALUE = 65535;
    private static final char[] HEX_CHAR = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'};
    static byte[] crc16_tab_h = {0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY, 1, -64, -128, 65, 1, -64, -128, 65, 0, -63, -127, Ptg.CLASS_ARRAY};
    static byte[] crc16_tab_l = {0, -64, -63, 1, -61, 3, 2, -62, -58, 6, 7, -57, 5, -59, -60, 4, -52, 12, 13, -51, 15, -49, -50, 14, 10, -54, -53, 11, -55, 9, 8, -56, -40, 24, AttrPtg.sid, -39, 27, -37, -38, 26, IntPtg.sid, -34, -33, NumberPtg.sid, -35, BoolPtg.sid, 28, -36, PercentPtg.sid, -44, -43, ParenthesisPtg.sid, -41, StringPtg.sid, MissingArgPtg.sid, -42, -46, UnaryPlusPtg.sid, UnaryMinusPtg.sid, -45, 17, -47, -48, 16, -16, 48, 49, -15, 51, -13, -14, 50, 54, -10, -9, 55, -11, 53, 52, -12, DeletedRef3DPtg.sid, -4, -3, DeletedArea3DPtg.sid, -1, 63, 62, -2, -6, Ref3DPtg.sid, Area3DPtg.sid, -5, 57, -7, -8, PaletteRecord.STANDARD_PALETTE_SIZE, 40, -24, -23, MemFuncPtg.sid, -21, AreaErrPtg.sid, RefErrorPtg.sid, -22, -18, 46, 47, -17, 45, -19, -20, RefNPtg.sid, -28, RefPtg.sid, 37, -27, 39, -25, -26, 38, 34, -30, -29, 35, -31, 33, 32, -32, EPD_Config.EPD_CMD_START_SENDING, 96, 97, EPD_Config.EPD_CMD_BUFFER_EMPTY, 99, -93, -94, 98, 102, -90, -89, 103, -91, 101, 100, -92, 108, -84, -83, 109, -81, 111, 110, -82, -86, 106, 107, -85, 105, -87, -88, 104, 120, -72, -71, 121, -69, 123, 122, -70, -66, 126, 127, -65, 125, -67, -68, 124, -76, 116, 117, -75, 119, -73, -74, 118, 114, -78, -77, 115, -79, 113, 112, -80, 80, -112, -111, 81, -109, 83, 82, -110, -106, 86, 87, -105, 85, -107, -108, 84, -100, 92, 93, -99, 95, -97, -98, 94, 90, -102, -101, 91, -103, 89, 88, -104, EPD_Config.EPD_CMD_DEVICE_VERIFICATION, 72, 73, -119, 75, -117, -118, 74, 78, -114, -113, 79, -115, 77, 76, -116, 68, -124, -123, 69, -121, 71, 70, -122, -126, 66, 67, -125, 65, -127, -128, Ptg.CLASS_ARRAY};

    public static String getHexString(int i) {
        String hexString = String.format("%04x", Integer.valueOf(i));
        return hexString;
    }

    public static String getCrc16String(byte[] data) {
        StringBuilder builder = new StringBuilder();
        String hex = getHexString(getCrc16(data));
        builder.append(hex.substring(2));
        builder.append(hex.substring(0, 2));
        return builder.toString();
    }

    public static String getCrc16String(String data) {
        StringBuilder builder = new StringBuilder();
        String hex = getHexString(getCrc16(data));
        builder.append(hex.substring(2));
        builder.append(hex.substring(0, 2));
        return builder.toString();
    }

    public static int getCrc16(byte[] data) {
        System.out.println("\nCRC 16 calculation progress:\n");
        int current_crc_value = 65535;
        for (byte b : data) {
            current_crc_value ^= b & 255;
            for (int j = 0; j < 8; j++) {
                if ((current_crc_value & 1) != 0) {
                    current_crc_value = (current_crc_value >>> 1) ^ POLYNOMIAL;
                } else {
                    current_crc_value >>>= 1;
                }
            }
        }
        return 65535 & current_crc_value;
    }

    public static int getCrc16(String str) {
        byte[] data = hexStringToBytes(str);
        System.out.println("\nCRC 16 calculation progress:\n");
        int current_crc_value = 65535;
        for (byte b : data) {
            current_crc_value ^= b & 255;
            for (int j = 0; j < 8; j++) {
                if ((current_crc_value & 1) != 0) {
                    current_crc_value = (current_crc_value >>> 1) ^ POLYNOMIAL;
                } else {
                    current_crc_value >>>= 1;
                }
            }
        }
        return 65535 & current_crc_value;
    }

    public static String printHexString(byte[] b) {
        StringBuffer returnValue = new StringBuffer();
        for (int i = 0; i < b.length; i++) {
            String hex = Integer.toHexString(b[i] & 255);
            if (hex.length() == 1) {
                hex = '0' + hex;
            }
            if (i % 2 == 0) {
                returnValue.append(hex.toUpperCase() + "");
            } else {
                returnValue.append(hex.toUpperCase() + " ");
            }
        }
        return returnValue.toString();
    }

    public static String bytesToHexFun1(byte[] bytes) {
        int a;
        char[] buf = new char[bytes.length * 2];
        int index = 0;
        for (byte b : bytes) {
            if (b < 0) {
                a = b + 256;
            } else {
                a = b;
            }
            int index2 = index + 1;
            char[] cArr = HEX_CHAR;
            buf[index] = cArr[a / 16];
            index = index2 + 1;
            buf[index2] = cArr[a % 16];
        }
        return new String(buf);
    }

    public static String bytesToHexFun2(byte[] bytes) {
        char[] buf = new char[bytes.length * 2];
        int index = 0;
        for (byte b : bytes) {
            int index2 = index + 1;
            char[] cArr = HEX_CHAR;
            buf[index] = cArr[(b >>> 4) & 15];
            index = index2 + 1;
            buf[index2] = cArr[b & 15];
        }
        return new String(buf);
    }

    public static String bytesToHexString(byte[] src) {
        StringBuilder stringBuilder = new StringBuilder("");
        if (src == null || src.length <= 0) {
            return null;
        }
        for (byte b : src) {
            int v = b & 255;
            String hv = Integer.toHexString(v);
            if (hv.length() < 2) {
                stringBuilder.append(0);
            }
            stringBuilder.append(hv);
        }
        return stringBuilder.toString();
    }

    public static String bytes2HexString(byte[] b) {
        StringBuffer result = new StringBuffer();
        for (byte b2 : b) {
            String hex = Integer.toHexString(b2 & 255);
            if (hex.length() == 1) {
                hex = '0' + hex;
            }
            result.append(hex.toUpperCase());
        }
        return result.toString();
    }

    public static byte[] hexStringToBytes(String hexString) {
        if (hexString == null || hexString.equals("")) {
            return null;
        }
        String hexString2 = hexString.toUpperCase();
        int length = hexString2.length() / 2;
        char[] hexChars = hexString2.toCharArray();
        byte[] d = new byte[length];
        for (int i = 0; i < length; i++) {
            int pos = i * 2;
            d[i] = (byte) ((charToByte(hexChars[pos]) << 4) | charToByte(hexChars[pos + 1]));
        }
        return d;
    }

    private static byte charToByte(char c) {
        return (byte) "0123456789ABCDEF".indexOf(c);
    }

    public static int calcCrc16(byte[] data) {
        return calcCrc16(data, 0, data.length);
    }

    public static int calcCrc16(byte[] data, int offset, int len) {
        return calcCrc16(data, offset, len, 0);
    }

    public static int calcCrc16(byte[] data, int offset, int len, int preval) {
        int i = (65280 & preval) >> 8;
        int ucCRCLo = preval & 255;
        for (int i2 = 0; i2 < len; i2++) {
            int iIndex = (data[offset + i2] ^ ucCRCLo) & 255;
            ucCRCLo = i ^ crc16_tab_h[iIndex];
            i = crc16_tab_l[iIndex];
        }
        int i3 = i & 255;
        return (i3 << 8) | (ucCRCLo & 255 & 65535);
    }
}
