package com.vinicius.meular.mods;

import java.util.ArrayList;
import java.util.List;

/** The Sims 2: GMDC (0xAC4F8687) -> malhas (posição, normal, UV, triângulos). Pesos de osso do jogo original são ignorados. */
final class Gmdc {
    private Gmdc() {}

    static final int T_GMDC = 0xAC4F8687;

    private static final class El {
        int ident;
        int bf;
        byte[] raw;
        int off;
        int len;
    }

    private static final class Link {
        int[] idxs;
        int refmax;
    }

    static List<RawMesh> parse(byte[] b) throws Exception {
        Rd r = new Rd(b, 0);
        if (r.u32() != 0xFFFF0001L) throw new Exception("GMDC: cabeçalho inesperado");
        int nl = r.count(1000);
        r.skip(16L * nl);
        int nb = r.count(1000);
        r.skip(4L * nb);
        r.str7();
        r.i32();
        int ver = r.i32();
        r.str7();
        r.i32();
        r.i32();
        r.str7();
        int ne = r.count(1000);
        El[] els = new El[ne];
        for (int i = 0; i < ne; i++) {
            El e = new El();
            r.i32();                 // tamanho do array de referência
            e.ident = r.i32();
            r.i32();                 // repetição
            e.bf = r.i32();
            r.i32();                 // formato do conjunto
            int bsz = r.count(64 * 1024 * 1024);
            if (!r.left(bsz)) throw new Exception("GMDC: bloco de dados truncado");
            e.raw = b;
            e.off = r.p;
            e.len = bsz;
            r.skip(bsz);
            int nref = r.count(1 << 20);
            r.skip((long) nref * (ver == 4 ? 2 : 4));
            els[i] = e;
        }
        int nlk = r.count(1000);
        Link[] links = new Link[nlk];
        for (int i = 0; i < nlk; i++) {
            Link l = new Link();
            int n = r.count(1000);
            l.idxs = new int[n];
            for (int k = 0; k < n; k++) l.idxs[k] = ver == 4 ? r.u16() : r.i32();
            l.refmax = r.i32();
            r.i32();                 // elementos ativos
            for (int blk = 0; blk < 3; blk++) {
                int c = r.count(1 << 20);
                r.skip((long) c * (ver == 4 ? 2 : 4));
            }
            links[i] = l;
        }
        int ng = r.count(1000);
        List<RawMesh> out = new ArrayList<>();
        for (int g = 0; g < ng; g++) {
            r.i32();                 // tipo primitivo
            int li = r.i32();
            String name = r.str7();
            int fc = r.count(10_000_000);
            int[] f = new int[fc];
            for (int k = 0; k < fc; k++) f[k] = ver == 4 ? r.u16() : r.i32();
            r.i32();                 // opacidade
            if (ver != 1) {
                int nbn = r.count(1000);
                r.skip((long) nbn * (ver == 4 ? 2 : 4));
            }
            if (li < 0 || li >= links.length) continue;
            Link l = links[li];
            El ep = null, en = null, eu = null;
            for (int ei : l.idxs) {
                if (ei < 0 || ei >= els.length) continue;
                El e = els[ei];
                if (e.ident == 0x5B830781 && ep == null && e.len > 0) ep = e;
                else if (e.ident == 0x3B83078B && en == null && e.len > 0) en = e;
                else if (e.ident == 0xBB8307AB && eu == null && e.len > 0) eu = e;
            }
            if (ep == null || fc < 3) continue;
            int n = l.refmax;
            if (n <= 0 || n > ep.len / 12) n = ep.len / 12;
            RawMesh m = new RawMesh();
            m.game = 2;
            m.name = name;
            m.pos = floats(ep, n, 3);
            m.nor = en != null && en.len >= n * 12 ? floats(en, n, 3) : null;
            m.uv = eu != null && eu.len >= n * 8 ? floats(eu, n, 2) : null;
            int nt = fc / 3;
            int[] idx = new int[nt * 3];
            int ok = 0;
            for (int t = 0; t < nt; t++) {
                int a = f[t * 3], bb = f[t * 3 + 1], c = f[t * 3 + 2];
                if (a < 0 || bb < 0 || c < 0 || a >= n || bb >= n || c >= n) continue;
                idx[ok * 3] = a; idx[ok * 3 + 1] = bb; idx[ok * 3 + 2] = c;
                ok++;
            }
            m.idx = java.util.Arrays.copyOf(idx, ok * 3);
            if (ok > 0) out.add(m);
        }
        return out;
    }

    private static float[] floats(El e, int n, int k) {
        float[] a = new float[n * k];
        int p = e.off;
        byte[] b = e.raw;
        for (int i = 0; i < a.length; i++, p += 4) {
            int v = (b[p] & 255) | ((b[p + 1] & 255) << 8) | ((b[p + 2] & 255) << 16) | ((b[p + 3] & 255) << 24);
            a[i] = Float.intBitsToFloat(v);
        }
        return a;
    }
}
