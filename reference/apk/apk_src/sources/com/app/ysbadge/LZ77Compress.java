package com.app.ysbadge;

/* JADX INFO: loaded from: classes2.dex */
public class LZ77Compress {
    static final /* synthetic */ boolean $assertionsDisabled = false;
    private long length;
    private long offset;
    private byte[] pDataBuffer;
    private byte[] pOutputBuffer;
    private long pSlideWindowPtr;
    private long pUnprocessedDataPtr;
    private long pulNumberOfBits;
    private int ulNumberOfBits;
    private int OFFSET_CODING_LENGTH = 10;
    private int MAX_WND_SIZE = 1024;

    /* JADX INFO: renamed from: m */
    private int f81m = 3;
    private int count = 1;

    private long CompareStrings(long string1, long string2, long length) {
        long p1 = string1;
        long p2 = string2;
        for (long i = 0; i < length; i++) {
            byte[] bArr = this.pDataBuffer;
            if (bArr[(int) p1] != bArr[(int) p2]) {
                break;
            }
            p1++;
            p2++;
        }
        return p1 - string1;
    }

    private void FindLongestSubstring(long pSourceString, long pString, long ulSourceStringLength) {
        this.offset = 0L;
        this.length = 0L;
        if (-1 == pSourceString || -1 == pString) {
            return;
        }
        long pSrc = pSourceString;
        long ioffset = 0;
        long pulSubstringLength = 0;
        for (long ulMaxLength = ulSourceStringLength; ulMaxLength > 0; ulMaxLength--) {
            long ilength = CompareStrings(pSrc, pString, ulMaxLength);
            if (ilength > pulSubstringLength) {
                long pulSubstringOffset = ioffset;
                this.offset = pulSubstringOffset;
                this.length = ilength;
                pulSubstringLength = ilength;
            }
            pSrc++;
            ioffset++;
        }
    }

    private void Write1ToBitStream(long ulBitOffset) {
        long ulByteBoundary = ulBitOffset >> 3;
        long ulOffsetInByte = 7 & ulBitOffset;
        byte[] bArr = this.pOutputBuffer;
        byte c = bArr[(int) ulByteBoundary];
        bArr[(int) ulByteBoundary] = (byte) ((c & 255) | (1 << ((int) ulOffsetInByte)));
    }

    private void Write0ToBitStream(long ulBitOffset) {
        long ulByteBoundary = ulBitOffset >> 3;
        long ulOffsetInByte = 7 & ulBitOffset;
        byte[] bArr = this.pOutputBuffer;
        byte c = bArr[(int) ulByteBoundary];
        bArr[(int) ulByteBoundary] = (byte) (c & 255 & ((1 << ((int) ulOffsetInByte)) ^ (-1)));
    }

    private long WriteGolombCode(long ulBitOffset) {
        long x = this.length;
        int i = this.f81m;
        long q = (x - 1) >> i;
        long r = (x - (q << i)) - 1;
        int i2 = 0;
        long ulBitOffset2 = ulBitOffset;
        while (i2 < q) {
            Write1ToBitStream(ulBitOffset2);
            i2++;
            ulBitOffset2++;
        }
        Write0ToBitStream(ulBitOffset2);
        long ulBitOffset3 = ulBitOffset2 + 1;
        int i3 = 0;
        while (true) {
            int i4 = this.f81m;
            if (i3 >= i4) {
                return ((long) i4) + q + 1;
            }
            if (((r >> i3) & 1) > 0) {
                Write1ToBitStream(ulBitOffset3);
            } else {
                Write0ToBitStream(ulBitOffset3);
            }
            i3++;
            ulBitOffset3++;
        }
    }

    public byte[] Compress(byte[] bytes) {
        long ulDataLength;
        long ulMaxlength;
        long ulBitOffset;
        this.count = 1;
        this.pDataBuffer = bytes;
        long ulDataLength2 = bytes.length;
        this.pOutputBuffer = new byte[((int) ulDataLength2) * 2];
        long iSlideWindowPtr = -this.MAX_WND_SIZE;
        long j = -1;
        this.pSlideWindowPtr = -1L;
        long ulBytesCoded = 0;
        long iSlideWindowPtr2 = 0;
        long ulBitOffset2 = iSlideWindowPtr;
        while (ulBytesCoded < ulDataLength2) {
            if (ulBitOffset2 >= 0) {
                this.pSlideWindowPtr = ulBitOffset2;
                ulDataLength = ulDataLength2;
                byte b = this.pDataBuffer[(int) this.pSlideWindowPtr];
                ulMaxlength = this.MAX_WND_SIZE;
            } else {
                ulDataLength = ulDataLength2;
                int i = this.MAX_WND_SIZE;
                if (ulBitOffset2 >= (-i)) {
                    this.pSlideWindowPtr = 0L;
                    ulMaxlength = ((long) i) + ulBitOffset2;
                } else {
                    this.pSlideWindowPtr = j;
                    ulMaxlength = 0;
                }
            }
            this.pUnprocessedDataPtr = ulBytesCoded;
            byte b2 = this.pDataBuffer[(int) this.pUnprocessedDataPtr];
            if (ulMaxlength > ulDataLength - ulBytesCoded) {
                ulMaxlength = ulDataLength - ulBytesCoded;
            }
            long j2 = this.pSlideWindowPtr;
            long iSlideWindowPtr3 = this.pUnprocessedDataPtr;
            long ulBytesCoded2 = ulBytesCoded;
            long ulBytesCoded3 = iSlideWindowPtr2;
            long iSlideWindowPtr4 = ulBitOffset2;
            long iSlideWindowPtr5 = ulMaxlength;
            FindLongestSubstring(j2, iSlideWindowPtr3, iSlideWindowPtr5);
            if (this.length <= this.MAX_WND_SIZE) {
                long j3 = this.offset;
            }
            if (this.length > 1) {
                Write1ToBitStream(ulBytesCoded3);
                long ulBitOffset3 = ulBytesCoded3 + 1;
                int i2 = 0;
                while (i2 < this.OFFSET_CODING_LENGTH) {
                    if (((this.offset >> i2) & 1) > 0) {
                        Write1ToBitStream(ulBitOffset3);
                    } else {
                        Write0ToBitStream(ulBitOffset3);
                    }
                    i2++;
                    ulBitOffset3++;
                }
                long ulCodingLength = WriteGolombCode(ulBitOffset3);
                ulBitOffset = ulBitOffset3 + ulCodingLength;
                long j4 = this.length;
                ulBytesCoded = ulBytesCoded2 + j4;
                ulBitOffset2 = iSlideWindowPtr4 + j4;
            } else {
                Write0ToBitStream(ulBytesCoded3);
                ulBitOffset = ulBytesCoded3 + 1;
                byte cc = this.pDataBuffer[(int) this.pUnprocessedDataPtr];
                int i3 = 0;
                while (i3 < 8) {
                    if ((((cc & 255) >> i3) & 1) > 0) {
                        Write1ToBitStream(ulBitOffset);
                    } else {
                        Write0ToBitStream(ulBitOffset);
                    }
                    i3++;
                    ulBitOffset++;
                }
                ulBytesCoded = ulBytesCoded2 + 1;
                ulBitOffset2 = iSlideWindowPtr4 + 1;
            }
            iSlideWindowPtr2 = ulBitOffset;
            ulDataLength2 = ulDataLength;
            j = -1;
        }
        long ulBytesCoded4 = ulBytesCoded;
        long ulBytesCoded5 = iSlideWindowPtr2;
        if (ulBytesCoded4 != ulDataLength2) {
        }
        this.pulNumberOfBits = ulBytesCoded5;
        int k = (int) ((this.pulNumberOfBits + 7) >> 3);
        byte[] b3 = new byte[k];
        System.arraycopy(this.pOutputBuffer, 0, b3, 0, k);
        setUlNumberOfBits((int) this.pulNumberOfBits);
        return b3;
    }

    public int getUlNumberOfBits() {
        return this.ulNumberOfBits;
    }

    public void setUlNumberOfBits(int ulNumberOfBits) {
        this.ulNumberOfBits = ulNumberOfBits;
    }

    public String bytesToHexString(byte[] src) {
        StringBuilder stringBuilder = new StringBuilder("");
        if (src == null || src.length <= 0) {
            return null;
        }
        for (byte b : src) {
            int v = b & 255;
            String hv = Integer.toHexString(v);
            stringBuilder.append("0x");
            if (hv.length() < 2) {
                stringBuilder.append(0);
            }
            stringBuilder.append(hv);
            stringBuilder.append(",");
        }
        return stringBuilder.toString();
    }
}
