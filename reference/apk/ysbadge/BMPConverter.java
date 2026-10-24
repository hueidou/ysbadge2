package com.app.ysbadge;

import java.lang.reflect.Array;

/* JADX INFO: loaded from: classes2.dex */
public class BMPConverter {
    public static final int DEV_TYPE_BW = 0;
    public static final int DEV_TYPE_BWR = 1;
    public static final int DEV_TYPE_BWY = 2;
    public static final int DEV_TYPE_BWYR = 3;
    public static final int DEV_TYPE_NCOLOR = 4;

    public static RGBTriple[] getPalette(int deviceType) {
        if (deviceType == 0) {
            RGBTriple[] palette = {new RGBTriple(0, 0, 0), new RGBTriple(255, 255, 255)};
            return palette;
        }
        if (deviceType != 1) {
            if (deviceType == 2) {
                RGBTriple[] palette2 = {new RGBTriple(0, 0, 0), new RGBTriple(255, 255, 255), new RGBTriple(255, 255, 0)};
                return palette2;
            }
            if (deviceType == 3) {
                RGBTriple[] palette3 = {new RGBTriple(0, 0, 0), new RGBTriple(255, 255, 255), new RGBTriple(255, 255, 0), new RGBTriple(255, 0, 0)};
                return palette3;
            }
            if (deviceType == 4) {
                RGBTriple[] palette4 = {new RGBTriple(0, 0, 0), new RGBTriple(255, 255, 255), new RGBTriple(0, 255, 0), new RGBTriple(0, 0, 255), new RGBTriple(255, 0, 0), new RGBTriple(255, 255, 0), new RGBTriple(255, 128, 0)};
                return palette4;
            }
            return null;
        }
        RGBTriple[] palette5 = {new RGBTriple(0, 0, 0), new RGBTriple(255, 255, 255), new RGBTriple(255, 0, 0)};
        return palette5;
    }

    public static byte[][] thresholding(RGBTriple[][] image, RGBTriple[] palette) {
        byte[][] result = (byte[][]) Array.newInstance((Class<?>) byte.class, image.length, image[0].length);
        for (int y = 0; y < image.length; y++) {
            for (int x = 0; x < image[y].length; x++) {
                RGBTriple currentPixel = image[y][x];
                byte index = findNearestColor(currentPixel, palette);
                result[y][x] = index;
            }
        }
        return result;
    }

    public static byte[][] floydSteinbergDither(RGBTriple[][] image, RGBTriple[] palette) {
        byte[][] result = (byte[][]) Array.newInstance((Class<?>) byte.class, image.length, image[0].length);
        for (int y = 0; y < image.length; y++) {
            for (int x = 0; x < image[y].length; x++) {
                RGBTriple currentPixel = image[y][x];
                byte index = findNearestColor(currentPixel, palette);
                result[y][x] = index;
                for (int i = 0; i < 3; i++) {
                    int error = (currentPixel.channels[i] & 255) - (palette[index].channels[i] & 255);
                    if (x + 1 < image[0].length) {
                        image[y + 0][x + 1].channels[i] = plus_truncate_uchar(image[y + 0][x + 1].channels[i], (error * 7) >> 4);
                    }
                    if (y + 1 < image.length) {
                        if (x - 1 > 0) {
                            image[y + 1][x - 1].channels[i] = plus_truncate_uchar(image[y + 1][x - 1].channels[i], (error * 3) >> 4);
                        }
                        image[y + 1][x + 0].channels[i] = plus_truncate_uchar(image[y + 1][x + 0].channels[i], (error * 5) >> 4);
                        if (x + 1 < image[0].length) {
                            image[y + 1][x + 1].channels[i] = plus_truncate_uchar(image[y + 1][x + 1].channels[i], (error * 1) >> 4);
                        }
                    }
                }
            }
        }
        return result;
    }

    private static byte plus_truncate_uchar(byte a, int b) {
        if ((a & 255) + b < 0) {
            return (byte) 0;
        }
        if ((a & 255) + b > 255) {
            return (byte) -1;
        }
        return (byte) (a + b);
    }

    private static byte findNearestColor(RGBTriple color, RGBTriple[] palette) {
        int minDistanceSquared = 195076;
        int bestIndex = 0;
        for (int i = 0; i < palette.length; i++) {
            int Rdiff = (color.channels[0] & 255) - (palette[i].channels[0] & 255);
            int Gdiff = (color.channels[1] & 255) - (palette[i].channels[1] & 255);
            int Bdiff = (color.channels[2] & 255) - (palette[i].channels[2] & 255);
            int distanceSquared = (Rdiff * Rdiff) + (Gdiff * Gdiff) + (Bdiff * Bdiff);
            if (distanceSquared < minDistanceSquared) {
                minDistanceSquared = distanceSquared;
                bestIndex = i;
            }
        }
        return (byte) bestIndex;
    }
}
