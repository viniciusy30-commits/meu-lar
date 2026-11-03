package com.vinicius.meular.mods;

import java.io.ByteArrayOutputStream;
import java.util.zip.CRC32;
import java.util.zip.Deflater;

/** Imagem ARGB simples + gravação em PNG (sem depender do Android, para poder testar no PC). */
public final class Img {
    public final int w;
    public final int h;
    public final int[] argb;

    public Img(int w, int h) { this.w = w; this.h = h; this.argb = new int[w * h]; }
    public Img(int w, int h, int[] a) { this.w = w; this.h = h; this.argb = a; }

    public static Img solid(int w, int h, int c) {
        Img m = new Img(w, h);
        java.util.Arrays.fill(m.argb, c);
        return m;
    }

    /** Reduz pela metade (média 2x2) até caber em [max]. */
    public Img limit(int max) {
        Img m = this;
        while (m.w > max || m.h > max) {
            int nw = Math.max(1, m.w / 2), nh = Math.max(1, m.h / 2);
            Img n = new Img(nw, nh);
            for (int y = 0; y < nh; y++) {
                for (int x = 0; x < nw; x++) {
                    int a = 0, r = 0, g = 0, b = 0;
                    for (int k = 0; k < 4; k++) {
                        int sx = Math.min(m.w - 1, x * 2 + (k & 1)), sy = Math.min(m.h - 1, y * 2 + (k >> 1));
                        int c = m.argb[sy * m.w + sx];
                        a += c >>> 24; r += (c >> 16) & 255; g += (c >> 8) & 255; b += c & 255;
                    }
                    n.argb[y * nw + x] = ((a / 4) << 24) | ((r / 4) << 16) | ((g / 4) << 8) | (b / 4);
                }
            }
            m = n;
        }
        return m;
    }

    /** Lado em potência de 2 (GLES2 não carrega textura NPOT com repetição/mipmap: ficaria preta). */
    public Img pot() {
        int nw = 1, nh = 1;
        while (nw < w) nw <<= 1;
        while (nh < h) nh <<= 1;
        if (nw == w && nh == h) return this;
        Img n = new Img(nw, nh);
        for (int y = 0; y < nh; y++) {
            int sy = Math.min(h - 1, (int) ((long) y * h / nh));
            for (int x = 0; x < nw; x++) n.argb[y * nw + x] = argb[sy * w + Math.min(w - 1, (int) ((long) x * w / nw))];
        }
        return n;
    }

    /** Brilho médio (0..255) dos pixels visíveis; textura quase preta quase sempre é leitura errada. */
    public double meanLuma() {
        double acc = 0;
        long n = 0;
        for (int c : argb) {
            if ((c >>> 24) < 8) continue;
            acc += (((c >> 16) & 255) + ((c >> 8) & 255) + (c & 255)) / 3.0;
            n++;
        }
        return n == 0 ? 0 : acc / n;
    }

    /** true se existe algum pixel com alfa < 250. */
    public boolean hasAlpha() {
        for (int c : argb) if ((c >>> 24) < 250) return true;
        return false;
    }

    public Img opaque() {
        int[] a = new int[argb.length];
        for (int i = 0; i < a.length; i++) a[i] = argb[i] | 0xFF000000;
        return new Img(w, h, a);
    }

    public byte[] png() {
        ByteArrayOutputStream raw = new ByteArrayOutputStream(w * h * 4 + h);
        byte[] row = new byte[w * 4];
        for (int y = 0; y < h; y++) {
            raw.write(0);
            for (int x = 0; x < w; x++) {
                int c = argb[y * w + x];
                row[x * 4] = (byte) (c >> 16);
                row[x * 4 + 1] = (byte) (c >> 8);
                row[x * 4 + 2] = (byte) c;
                row[x * 4 + 3] = (byte) (c >>> 24);
            }
            raw.write(row, 0, row.length);
        }
        Deflater df = new Deflater(6);
        df.setInput(raw.toByteArray());
        df.finish();
        ByteArrayOutputStream z = new ByteArrayOutputStream();
        byte[] buf = new byte[65536];
        while (!df.finished()) { int k = df.deflate(buf); z.write(buf, 0, k); }
        df.end();
        ByteArrayOutputStream o = new ByteArrayOutputStream();
        o.write(new byte[]{(byte) 0x89, 'P', 'N', 'G', 13, 10, 26, 10}, 0, 8);
        byte[] ih = new byte[13];
        put32(ih, 0, w); put32(ih, 4, h);
        ih[8] = 8; ih[9] = 6;
        chunk(o, "IHDR", ih);
        chunk(o, "IDAT", z.toByteArray());
        chunk(o, "IEND", new byte[0]);
        return o.toByteArray();
    }

    private static void put32(byte[] b, int p, int v) {
        b[p] = (byte) (v >>> 24); b[p + 1] = (byte) (v >>> 16); b[p + 2] = (byte) (v >>> 8); b[p + 3] = (byte) v;
    }

    private static void chunk(ByteArrayOutputStream o, String type, byte[] data) {
        byte[] l = new byte[4];
        put32(l, 0, data.length);
        o.write(l, 0, 4);
        byte[] t = type.getBytes(java.nio.charset.StandardCharsets.US_ASCII);
        o.write(t, 0, 4);
        o.write(data, 0, data.length);
        CRC32 crc = new CRC32();
        crc.update(t);
        crc.update(data);
        put32(l, 0, (int) crc.getValue());
        o.write(l, 0, 4);
    }
}
