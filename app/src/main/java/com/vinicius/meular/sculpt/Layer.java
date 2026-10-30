package com.vinicius.meular.sculpt;

/** Malha de uma camada (pele, olhos, roupa, cabelo...) com etiqueta de material por vertice. */
public final class Layer {
    public static final int SKIN = 0, LIP = 1, BROW = 2, LASH = 3, SCLERA = 4, IRIS = 5, PUPIL = 6, GLINT = 7,
        HAIR = 8, BEARD = 9, TOP = 10, TOPD = 11, BOT = 12, BOTD = 13, SHOE = 14, SOLE = 15, FRAME = 16, LENS = 17,
        WHITE = 18, TEETH = 19, HAIRD = 20;

    public float[] p, n;
    public int[] tag;
    public float[] a, b;
    public int[] t;
    public int nv, nt;

    public interface Tagger { void tag(float x, float y, float z, float nx, float ny, float nz, float[] out); }

    public static Layer from(Mesher.Out o, Tagger tg) {
        Layer l = new Layer();
        l.p = java.util.Arrays.copyOf(o.p, o.nv * 3);
        l.n = o.n;
        l.nv = o.nv;
        l.t = java.util.Arrays.copyOf(o.t, o.nt * 3);
        l.nt = o.nt;
        l.tag = new int[o.nv]; l.a = new float[o.nv]; l.b = new float[o.nv];
        float[] r = new float[3];
        for (int i = 0; i < o.nv; i++) {
            r[0] = 0; r[1] = 0; r[2] = 0;
            tg.tag(o.p[i * 3], o.p[i * 3 + 1], o.p[i * 3 + 2], o.n[i * 3], o.n[i * 3 + 1], o.n[i * 3 + 2], r);
            l.tag[i] = (int) r[0]; l.a[i] = r[1]; l.b[i] = r[2];
        }
        return l;
    }

    /** Remove triangulos para os quais drop devolve true (pelo centro do triangulo). */
    public interface Drop { boolean drop(float cx, float cy, float cz); }

    public Layer without(Drop dr) {
        Layer l = new Layer();
        l.p = p; l.n = n; l.tag = tag; l.a = a; l.b = b; l.nv = nv;
        int[] nt2 = new int[nt * 3]; int k = 0;
        for (int i = 0; i < nt; i++) {
            int x = t[i * 3], y = t[i * 3 + 1], z = t[i * 3 + 2];
            float cx = (p[x * 3] + p[y * 3] + p[z * 3]) / 3f, cy = (p[x * 3 + 1] + p[y * 3 + 1] + p[z * 3 + 1]) / 3f, cz = (p[x * 3 + 2] + p[y * 3 + 2] + p[z * 3 + 2]) / 3f;
            if (dr.drop(cx, cy, cz)) continue;
            nt2[k++] = x; nt2[k++] = y; nt2[k++] = z;
        }
        l.t = java.util.Arrays.copyOf(nt2, k); l.nt = k / 3;
        return l;
    }

    // ---------------------------------------------------------------- construcao manual (olhos, aros...)
    public static final class Builder {
        float[] p = new float[3 * 512], n = new float[3 * 512], a = new float[512], b = new float[512];
        int[] tag = new int[512], t = new int[3 * 1024];
        int nv, nt;
        public int v(float x, float y, float z, float nx, float ny, float nz, int tg, float aa, float bb) {
            if (nv == a.length) {
                p = java.util.Arrays.copyOf(p, nv * 6); n = java.util.Arrays.copyOf(n, nv * 6);
                a = java.util.Arrays.copyOf(a, nv * 2); b = java.util.Arrays.copyOf(b, nv * 2); tag = java.util.Arrays.copyOf(tag, nv * 2);
            }
            p[nv * 3] = x; p[nv * 3 + 1] = y; p[nv * 3 + 2] = z; n[nv * 3] = nx; n[nv * 3 + 1] = ny; n[nv * 3 + 2] = nz;
            tag[nv] = tg; a[nv] = aa; b[nv] = bb;
            return nv++;
        }
        public void tri(int x, int y, int z) {
            if (nt * 3 + 3 > t.length) t = java.util.Arrays.copyOf(t, t.length * 2);
            t[nt * 3] = x; t[nt * 3 + 1] = y; t[nt * 3 + 2] = z; nt++;
        }
        public Layer done() {
            Layer l = new Layer();
            l.p = java.util.Arrays.copyOf(p, nv * 3); l.n = java.util.Arrays.copyOf(n, nv * 3);
            l.a = java.util.Arrays.copyOf(a, nv); l.b = java.util.Arrays.copyOf(b, nv); l.tag = java.util.Arrays.copyOf(tag, nv);
            l.t = java.util.Arrays.copyOf(t, nt * 3); l.nv = nv; l.nt = nt;
            return l;
        }
    }
}
