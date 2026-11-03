package com.vinicius.meular.mods;

/** Texturas dos packages: TXTR (Sims 2), DDS/DST (Sims 3 e 4), RLE2 (Sims 4). */
public final class Tex {
    private Tex() {}

    public static final int T_TXTR = 0x1C4A276C;     // Sims 2
    public static final int T_IMG = 0x00B2D882;      // Sims 3/4 (DDS ou DST)
    public static final int T_RLE2 = 0x3453CF95;     // Sims 4

    // ------------------------------------------------------------------ blocos DXT
    private static int rgb565(int c) {
        int r = (c >> 11) & 31, g = (c >> 5) & 63, b = c & 31;
        r = (r << 3) | (r >> 2); g = (g << 2) | (g >> 4); b = (b << 3) | (b >> 2);
        return (r << 16) | (g << 8) | b;
    }

    /** Bloco de cor (8 bytes) -> 16 pixels RGB (sem alfa). [dxt1]: c0 <= c1 usa 3 cores + transparente. */
    private static void colorBlock(byte[] d, int p, int[] out, boolean dxt1) {
        int c0 = (d[p] & 255) | ((d[p + 1] & 255) << 8);
        int c1 = (d[p + 2] & 255) | ((d[p + 3] & 255) << 8);
        int[] c = new int[4];
        c[0] = rgb565(c0);
        c[1] = rgb565(c1);
        if (c0 > c1 || !dxt1) {
            c[2] = mix(c[0], c[1], 2, 1);
            c[3] = mix(c[0], c[1], 1, 2);
        } else {
            c[2] = mix(c[0], c[1], 1, 1);
            c[3] = 0;   // transparente (alfa tratado fora)
        }
        long bits = (d[p + 4] & 255L) | ((d[p + 5] & 255L) << 8) | ((d[p + 6] & 255L) << 16) | ((d[p + 7] & 255L) << 24);
        for (int i = 0; i < 16; i++) {
            int k = (int) ((bits >> (2 * i)) & 3);
            out[i] = c[k] | (dxt1 && c0 <= c1 && k == 3 ? 0 : 0xFF000000);
        }
    }

    private static int mix(int a, int b, int wa, int wb) {
        int s = wa + wb;
        int r = (((a >> 16) & 255) * wa + ((b >> 16) & 255) * wb) / s;
        int g = (((a >> 8) & 255) * wa + ((b >> 8) & 255) * wb) / s;
        int bl = ((a & 255) * wa + (b & 255) * wb) / s;
        return (r << 16) | (g << 8) | bl;
    }

    private static void alphaDxt5(byte[] d, int p, int[] a) {
        int a0 = d[p] & 255, a1 = d[p + 1] & 255;
        int[] t = new int[8];
        t[0] = a0; t[1] = a1;
        if (a0 > a1) { for (int i = 1; i < 7; i++) t[i + 1] = ((7 - i) * a0 + i * a1) / 7; }
        else { for (int i = 1; i < 5; i++) t[i + 1] = ((5 - i) * a0 + i * a1) / 5; t[6] = 0; t[7] = 255; }
        long bits = 0;
        for (int i = 0; i < 6; i++) bits |= (d[p + 2 + i] & 255L) << (8 * i);
        for (int i = 0; i < 16; i++) a[i] = t[(int) ((bits >> (3 * i)) & 7)];
    }

    private static void alphaDxt3(byte[] d, int p, int[] a) {
        for (int i = 0; i < 8; i++) {
            int v = d[p + i] & 255;
            a[i * 2] = (v & 15) * 17;
            a[i * 2 + 1] = (v >> 4) * 17;
        }
    }

    /** kind: 1 = DXT1, 3 = DXT3, 5 = DXT5. [colorFirst] = bloco de cor antes do de alfa (Sims 2). */
    static Img dxt(byte[] d, int off, int w, int h, int kind, boolean colorFirst) throws Exception {
        int bs = kind == 1 ? 8 : 16;
        int bw = Math.max(1, (w + 3) / 4), bh = Math.max(1, (h + 3) / 4);
        if (off < 0 || (long) off + (long) bw * bh * bs > d.length) throw new Exception("Textura truncada");
        Img im = new Img(w, h);
        int[] col = new int[16];
        int[] al = new int[16];
        int p = off;
        for (int by = 0; by < bh; by++) {
            for (int bx = 0; bx < bw; bx++) {
                if (kind == 1) {
                    colorBlock(d, p, col, true);
                    java.util.Arrays.fill(al, 255);
                    for (int i = 0; i < 16; i++) if ((col[i] >>> 24) == 0) al[i] = 0;
                } else {
                    int ap = colorFirst ? p + 8 : p;
                    int cp = colorFirst ? p : p + 8;
                    if (kind == 3) alphaDxt3(d, ap, al); else alphaDxt5(d, ap, al);
                    colorBlock(d, cp, col, false);
                }
                for (int i = 0; i < 16; i++) {
                    int x = bx * 4 + (i & 3), y = by * 4 + (i >> 2);
                    if (x < w && y < h) im.argb[y * w + x] = (al[i] << 24) | (col[i] & 0xFFFFFF);
                }
                p += bs;
            }
        }
        return im;
    }

    // ------------------------------------------------------------------ Sims 2: TXTR
    /** Nome interno do recurso (ex.: "##0x7f1075ca!body~stdMatBaseTextureName_txtr"). */
    public static String sims2Name(byte[] b) {
        try {
            Rd r = new Rd(b, 0);
            if (r.u32() != 0xFFFF0001L) return "";
            int nl = r.count(1000);
            r.skip(16L * nl);
            int nb = r.count(1000);
            r.skip(4L * nb);
            r.str7(); r.i32(); r.i32();
            r.str7(); r.i32(); r.i32();
            return r.str7();
        } catch (Exception e) {
            return "";
        }
    }

    public static Img sims2(byte[] b) throws Exception {
        Rd r = new Rd(b, 0);
        if (r.u32() != 0xFFFF0001L) throw new Exception("TXTR: cabeçalho inesperado");
        int nl = r.count(1000);
        r.skip(16L * nl);
        int nb = r.count(1000);
        r.skip(4L * nb);
        r.str7(); r.i32(); r.i32();
        r.str7(); r.i32(); r.i32();
        r.str7();
        int w = r.i32(), h = r.i32(), fmt = r.i32(), lv = r.i32();
        if (w <= 0 || h <= 0 || w > 4096 || h > 4096) throw new Exception("TXTR: tamanho inválido");
        int kind;
        switch (fmt) {
            case 4: kind = 1; break;
            case 5: kind = 3; break;
            case 6: kind = 5; break;
            default: throw new Exception("Formato de textura do Sims 2 ainda não suportado (" + fmt + ")");
        }
        int bw = Math.max(1, w / 4), bh = Math.max(1, h / 4);
        int size0 = bw * bh * (kind == 1 ? 8 : 16);
        // o bloco do maior nível vem depois de um inteiro com o seu tamanho
        int start = -1;
        for (int q = r.p + 4; q < Math.min(b.length - 4, r.p + 96); q++) {
            int v = (b[q] & 255) | ((b[q + 1] & 255) << 8) | ((b[q + 2] & 255) << 16) | ((b[q + 3] & 255) << 24);
            if (v == size0) { start = q + 4; break; }
        }
        if (start < 0 || start + size0 > b.length) start = b.length - size0;
        return dxt(b, start, w, h, kind, false);
    }

    // ------------------------------------------------------------------ Sims 3/4: DDS / DST
    public static Img dds(byte[] b) throws Exception {
        if (b.length < 128 || b[0] != 'D' || b[1] != 'D' || b[2] != 'S') throw new Exception("DDS: cabeçalho inválido");
        Rd r = new Rd(b, 12);
        int h = r.i32(), w = r.i32();
        String fc = new String(b, 84, 4, java.nio.charset.StandardCharsets.ISO_8859_1);
        if (w <= 0 || h <= 0 || w > 8192 || h > 8192) throw new Exception("DDS: tamanho inválido");
        switch (fc) {
            case "DXT1": return dxt(b, 128, w, h, 1, false);
            case "DXT3": return dxt(b, 128, w, h, 3, false);
            case "DXT5": return dxt(b, 128, w, h, 5, false);
            case "DST1": return dxt(unshuffle(b, w, h, false), 0, w, h, 1, false);
            case "DST5": return dxt(unshuffle(b, w, h, true), 0, w, h, 5, false);
            default: break;
        }
        // sem compressão (BGRA/BGR)
        int bits = new Rd(b, 88).i32();
        int rm = new Rd(b, 92).i32(), gm = new Rd(b, 96).i32(), bm = new Rd(b, 100).i32(), am = new Rd(b, 104).i32();
        if (bits != 32 && bits != 24) throw new Exception("Formato DDS não suportado (" + fc.trim() + ")");
        int bpp = bits / 8;
        if ((long) 128 + (long) w * h * bpp > b.length) throw new Exception("DDS truncado");
        Img im = new Img(w, h);
        for (int i = 0; i < w * h; i++) {
            int v = 0;
            for (int k = 0; k < bpp; k++) v |= (b[128 + i * bpp + k] & 255) << (8 * k);
            int a = am != 0 ? comp(v, am) : 255;
            im.argb[i] = (a << 24) | (comp(v, rm) << 16) | (comp(v, gm) << 8) | comp(v, bm);
        }
        return im;
    }

    private static int comp(int v, int mask) {
        if (mask == 0) return 0;
        int sh = Integer.numberOfTrailingZeros(mask);
        int mx = mask >>> sh;
        return (int) (((v & mask) >>> sh) * 255L / Math.max(mx, 1));
    }

    /** DST1/DST5: os campos de cada bloco DXT ficam separados em sequências (cores/índices etc.). */
    private static byte[] unshuffle(byte[] b, int w, int h, boolean dxt5) throws Exception {
        int nb = Math.max(1, (w + 3) / 4) * Math.max(1, (h + 3) / 4);
        int bs = dxt5 ? 16 : 8;
        if (128 + (long) nb * bs > b.length) throw new Exception("DST truncado");
        byte[] o = new byte[nb * bs];
        int p = 128;
        if (!dxt5) {
            int ep = p, ip = p + nb * 4;
            for (int i = 0; i < nb; i++) {
                System.arraycopy(b, ep + i * 4, o, i * 8, 4);
                System.arraycopy(b, ip + i * 4, o, i * 8 + 4, 4);
            }
        } else {
            int ae = p, ce = p + nb * 2, ai = p + nb * 6, ci = p + nb * 10;
            for (int i = 0; i < nb; i++) {
                System.arraycopy(b, ae + i * 2, o, i * 16, 2);
                System.arraycopy(b, ai + i * 6, o, i * 16 + 2, 6);
                System.arraycopy(b, ce + i * 4, o, i * 16 + 8, 4);
                System.arraycopy(b, ci + i * 4, o, i * 16 + 12, 4);
            }
        }
        return o;
    }

    // ------------------------------------------------------------------ Sims 4: RLE2
    public static Img rle2(byte[] b) throws Exception {
        Rd r = new Rd(b, 8);
        int w = r.u16(), h = r.u16(), mc = r.u16();
        if (w <= 0 || h <= 0 || mc <= 0 || mc > 16) throw new Exception("RLE2: cabeçalho inválido");
        r.p = 16;
        int[][] offs = new int[mc][5];
        for (int m = 0; m < mc; m++) for (int k = 0; k < 5; k++) offs[m][k] = r.i32();
        int nb = (w / 4) * (h / 4);
        int[] st = new int[5], en = new int[5];
        for (int k = 0; k < 5; k++) { st[k] = offs[0][k]; en[k] = mc > 1 ? offs[1][k] : b.length; }
        byte[] out = new byte[nb * 16];
        int pos = 0, ic = 0, ia = 0;
        for (int q = st[0]; q + 1 < en[0]; q += 2) {
            int c = (b[q] & 255) | ((b[q + 1] & 255) << 8);
            int op = c & 3, n = c >> 2;
            if (pos + n > nb) throw new Exception("RLE2: dados inválidos");
            if (op == 0) { pos += n; }
            else if (op == 1) {
                for (int i = 0; i < n; i++) {
                    int d = (pos + i) * 16;
                    System.arraycopy(b, st[3] + 2 * (ia + i), out, d, 2);
                    System.arraycopy(b, st[4] + 6 * (ia + i), out, d + 2, 6);
                    System.arraycopy(b, st[1] + 4 * (ic + i), out, d + 8, 4);
                    System.arraycopy(b, st[2] + 4 * (ic + i), out, d + 12, 4);
                }
                ia += n; ic += n; pos += n;
            } else if (op == 2) {
                for (int i = 0; i < n; i++) {
                    int d = (pos + i) * 16;
                    out[d] = (byte) 255; out[d + 1] = (byte) 255;
                    System.arraycopy(b, st[1] + 4 * (ic + i), out, d + 8, 4);
                    System.arraycopy(b, st[2] + 4 * (ic + i), out, d + 12, 4);
                }
                ic += n; pos += n;
            } else throw new Exception("RLE2: operação desconhecida");
        }
        return dxt(out, 0, w, h, 5, false);
    }
}
