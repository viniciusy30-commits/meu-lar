package com.vinicius.meular.mods;

/** Descompressor RefPack/QFS (usado nos packages do The Sims 2, 3 e 4). */
final class RefPack {
    private RefPack() {}

    /** [src] começa em [start] no cabeçalho 0x10FB / 0x50FB. */
    static byte[] decode(byte[] src, int start) throws Exception {
        int p = start;
        int flags = src[p] & 255;
        if ((src[p + 1] & 255) != 0xFB) throw new Exception("RefPack inválido");
        p += 2;
        int len;
        if ((flags & 0x80) != 0) {
            len = ((src[p] & 255) << 24) | ((src[p + 1] & 255) << 16) | ((src[p + 2] & 255) << 8) | (src[p + 3] & 255);
            p += 4;
        } else {
            len = ((src[p] & 255) << 16) | ((src[p + 1] & 255) << 8) | (src[p + 2] & 255);
            p += 3;
        }
        if (len < 0 || len > 256 * 1024 * 1024) throw new Exception("RefPack: tamanho absurdo");
        byte[] out = new byte[len];
        int o = 0;
        int n = src.length;
        while (p < n && o < len) {
            int c0 = src[p++] & 255;
            int nl;
            int ref = 0;
            int cnt = 0;
            if (c0 < 0x80) {
                int c1 = src[p++] & 255;
                nl = c0 & 3;
                o = lit(src, p, out, o, nl); p += nl;
                ref = o - 1 - (((c0 & 0x60) << 3) + c1);
                cnt = ((c0 & 0x1C) >> 2) + 3;
            } else if (c0 < 0xC0) {
                int c1 = src[p] & 255;
                int c2 = src[p + 1] & 255;
                p += 2;
                nl = (c1 >> 6) & 3;
                o = lit(src, p, out, o, nl); p += nl;
                ref = o - 1 - (((c1 & 0x3F) << 8) + c2);
                cnt = (c0 & 0x3F) + 4;
            } else if (c0 < 0xE0) {
                int c1 = src[p] & 255;
                int c2 = src[p + 1] & 255;
                int c3 = src[p + 2] & 255;
                p += 3;
                nl = c0 & 3;
                o = lit(src, p, out, o, nl); p += nl;
                ref = o - 1 - (((c0 & 0x10) << 12) + (c1 << 8) + c2);
                cnt = ((c0 & 0x0C) << 6) + c3 + 5;
            } else if (c0 < 0xFC) {
                nl = ((c0 & 0x1F) << 2) + 4;
                o = lit(src, p, out, o, nl); p += nl;
                continue;
            } else {
                nl = c0 & 3;
                o = lit(src, p, out, o, nl); p += nl;
                break;
            }
            if (ref < 0) throw new Exception("RefPack: referência inválida");
            for (int i = 0; i < cnt && o < len; i++) out[o++] = out[ref++];
        }
        return out;
    }

    private static int lit(byte[] src, int p, byte[] out, int o, int nl) {
        int k = Math.min(nl, out.length - o);
        if (k > 0) System.arraycopy(src, p, out, o, k);
        return o + Math.max(k, 0);
    }
}
