package com.vinicius.meular.mods;

/** The Sims 3 / The Sims 4: GEOM (0x015A1849) -> malha. Os pesos de osso do arquivo são ignorados (o app copia os do corpo). */
final class Geom {
    private Geom() {}

    static final int T_GEOM = 0x015A1849;

    static RawMesh parse(byte[] b, int game) throws Exception {
        int o = -1;
        for (int i = 0; i + 4 <= Math.min(b.length, 64); i++) {
            if (b[i] == 'G' && b[i + 1] == 'E' && b[i + 2] == 'O' && b[i + 3] == 'M') { o = i; break; }
        }
        if (o < 0) throw new Exception("GEOM: marca não encontrada");
        Rd r = new Rd(b, o + 4);
        r.i32();                    // versão
        r.i32();                    // deslocamento TGI
        r.i32();                    // tamanho TGI
        long shader = r.u32();
        if (shader != 0) {
            long sz = r.u32();
            if (sz > b.length) throw new Exception("GEOM: bloco de shader inválido");
            r.skip(sz);
        }
        r.i32();                    // grupo de mistura
        r.i32();                    // ordem
        int nv = r.count(500000);
        int nf = r.count(64);
        int[] dt = new int[nf];
        int[] bpe = new int[nf];
        int stride = 0;
        for (int i = 0; i < nf; i++) {
            dt[i] = r.i32();
            r.i32();
            bpe[i] = r.u8();
            stride += bpe[i];
        }
        if (nv <= 0 || !r.left((long) nv * stride)) throw new Exception("GEOM: vértices truncados");
        int offPos = -1, offNor = -1, offUv = -1;
        int acc = 0;
        for (int i = 0; i < nf; i++) {
            if (dt[i] == 1 && bpe[i] == 12 && offPos < 0) offPos = acc;
            else if (dt[i] == 2 && bpe[i] == 12 && offNor < 0) offNor = acc;
            else if (dt[i] == 3 && bpe[i] == 8 && offUv < 0) offUv = acc;
            acc += bpe[i];
        }
        if (offPos < 0) throw new Exception("GEOM: sem posições");
        float[] pos = new float[nv * 3];
        float[] nor = offNor >= 0 ? new float[nv * 3] : null;
        float[] uv = offUv >= 0 ? new float[nv * 2] : null;
        int base = r.p;
        for (int v = 0; v < nv; v++) {
            int q = base + v * stride;
            for (int k = 0; k < 3; k++) pos[v * 3 + k] = fl(b, q + offPos + k * 4);
            if (nor != null) for (int k = 0; k < 3; k++) nor[v * 3 + k] = fl(b, q + offNor + k * 4);
            if (uv != null) for (int k = 0; k < 2; k++) uv[v * 2 + k] = fl(b, q + offUv + k * 4);
        }
        r.p = base + nv * stride;
        r.i32();                    // submalhas
        int bpf = r.u8();
        int nfp = r.count(3_000_000);
        if (bpf != 2 && bpf != 4) throw new Exception("GEOM: tamanho de índice inesperado");
        if (!r.left((long) nfp * bpf)) throw new Exception("GEOM: faces truncadas");
        int nt = nfp / 3;
        int[] idx = new int[nt * 3];
        int ok = 0;
        for (int t = 0; t < nt; t++) {
            int a = bpf == 2 ? r.u16() : r.i32();
            int bb = bpf == 2 ? r.u16() : r.i32();
            int c = bpf == 2 ? r.u16() : r.i32();
            if (a < 0 || bb < 0 || c < 0 || a >= nv || bb >= nv || c >= nv) continue;
            idx[ok * 3] = a; idx[ok * 3 + 1] = bb; idx[ok * 3 + 2] = c;
            ok++;
        }
        RawMesh m = new RawMesh();
        m.game = game;
        m.pos = pos;
        m.nor = nor;
        m.uv = uv;
        m.idx = java.util.Arrays.copyOf(idx, ok * 3);
        return m;
    }

    private static float fl(byte[] b, int p) {
        return Float.intBitsToFloat((b[p] & 255) | ((b[p + 1] & 255) << 8) | ((b[p + 2] & 255) << 16) | ((b[p + 3] & 255) << 24));
    }
}
