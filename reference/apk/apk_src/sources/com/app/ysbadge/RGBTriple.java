package com.app.ysbadge;

import androidx.core.view.MotionEventCompat;
import androidx.core.view.ViewCompat;

/* JADX INFO: loaded from: classes2.dex */
public class RGBTriple {
    public byte[] channels;

    public int getColor() {
        byte[] bArr = this.channels;
        return (bArr[2] & 255) | ((bArr[0] << 16) & 16711680) | ((bArr[1] << 8) & MotionEventCompat.ACTION_POINTER_INDEX_MASK) | ViewCompat.MEASURED_STATE_MASK;
    }

    public RGBTriple() {
        this.channels = new byte[3];
    }

    public RGBTriple(int R, int G, int B) {
        this.channels = new byte[]{(byte) R, (byte) G, (byte) B};
    }
}
