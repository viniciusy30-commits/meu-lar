package com.vinicius.meular.mods;

/** Leitor binário little-endian. */
final class Rd {
    final byte[] b;
    int p;

    Rd(byte[] b, int p) { this.b = b; this.p = p; }

    int u8() { return b[p++] & 255; }
    int u16() { int v = (b[p] & 255) | ((b[p + 1] & 255) << 8); p += 2; return v; }
    int i32() { int v = (b[p] & 255) | ((b[p + 1] & 255) << 8) | ((b[p + 2] & 255) << 16) | ((b[p + 3] & 255) << 24); p += 4; return v; }
    long u32() { return i32() & 0xFFFFFFFFL; }
    float f32() { return Float.intBitsToFloat(i32()); }
    void skip(long n) { p += (int) n; }
    boolean left(long n) { return p >= 0 && n >= 0 && p + n <= b.length; }

    /** Texto com tamanho em 1 byte. */
    String str7() {
        int n = u8();
        String s = new String(b, p, Math.min(n, b.length - p), java.nio.charset.StandardCharsets.ISO_8859_1);
        p += n;
        return s;
    }

    /** Conta de elementos lida com checagem de sanidade. */
    int count(int max) throws Exception {
        long n = u32();
        if (n > max) throw new Exception("Arquivo de malha corrompido");
        return (int) n;
    }
}
