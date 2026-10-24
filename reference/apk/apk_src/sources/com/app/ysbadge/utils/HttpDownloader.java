package com.app.ysbadge.utils;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/* JADX INFO: loaded from: classes2.dex */
public class HttpDownloader {
    /* JADX WARN: Code duplicated, block: B:35:0x0112 A[Catch: IOException -> 0x010e, TRY_LEAVE, TryCatch #3 {IOException -> 0x010e, blocks: (B:31:0x010a, B:35:0x0112), top: B:60:0x010a }] */
    /* JADX WARN: Code duplicated, block: B:47:0x012d A[DONT_INVERT] */
    /* JADX WARN: Code duplicated, block: B:48:0x012f A[Catch: IOException -> 0x012b, TRY_LEAVE, TryCatch #5 {IOException -> 0x012b, blocks: (B:44:0x0127, B:48:0x012f), top: B:62:0x0127 }] */
    /* JADX WARN: Code duplicated, block: B:62:0x0127 A[EXC_TOP_SPLITTER, SYNTHETIC] */
    public static byte[] downloadFile(String urlPath, String downloadDir, String fileName) throws Throwable {
        BufferedInputStream in = null;
        OutputStream out = null;
        HttpURLConnection connection = null;
        try {
            try {
                URL url = new URL(urlPath);
                connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("GET");
                connection.setRequestProperty("Content-Type", "application/octet-stream;charset=utf-8");
                connection.setRequestProperty("Connection", "close");
                connection.setConnectTimeout(5000);
                connection.setDoOutput(true);
                connection.setDoInput(true);
                connection.connect();
                int fileLength = connection.getContentLength();
                System.out.println("file length-------------" + fileLength + " (byte)");
                in = new BufferedInputStream(connection.getInputStream());
                StringBuilder sb = new StringBuilder();
                sb.append(downloadDir);
                sb.append(File.separatorChar);
                try {
                    sb.append(fileName);
                    String path = sb.toString();
                    File file = new File(path);
                    if (!file.getParentFile().exists()) {
                        file.getParentFile().mkdirs();
                    }
                    out = new FileOutputStream(file);
                    int len = 0;
                    byte[] buf = new byte[1048576];
                    byte[] data = new byte[fileLength];
                    int dataPos = 0;
                    while (true) {
                        int size = in.read(buf);
                        String path2 = path;
                        if (size == -1) {
                            break;
                        }
                        len += size;
                        out.write(buf, 0, size);
                        for (int i = 0; i < size; i++) {
                            data[dataPos] = buf[i];
                            dataPos++;
                        }
                        path = path2;
                    }
                    System.out.println("download finish--" + fileLength + "," + len + "," + dataPos + " (byte)");
                    try {
                        in.close();
                        out.close();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                    connection.disconnect();
                    return data;
                } catch (Exception e2) {
                    e = e2;
                    e.printStackTrace();
                    if (in != null) {
                        try {
                            in.close();
                            if (out != null) {
                                out.close();
                            }
                        } catch (IOException e3) {
                            e3.printStackTrace();
                            connection.disconnect();
                            return new byte[0];
                        }
                    } else if (out != null) {
                        out.close();
                    }
                    connection.disconnect();
                    return new byte[0];
                }
            } catch (Throwable th) {
                th = th;
                Throwable th2 = th;
                if (in != null) {
                    try {
                        in.close();
                        if (0 != 0) {
                            out.close();
                        }
                    } catch (IOException e4) {
                        e4.printStackTrace();
                        connection.disconnect();
                        throw th2;
                    }
                } else if (0 != 0) {
                    out.close();
                }
                connection.disconnect();
                throw th2;
            }
        } catch (Exception e5) {
            e = e5;
        } catch (Throwable th3) {
            th = th3;
            Throwable th4 = th;
            if (in != null) {
                in.close();
                if (0 != 0) {
                    out.close();
                }
            } else if (0 != 0) {
                out.close();
            }
            connection.disconnect();
            throw th4;
        }
    }
}
