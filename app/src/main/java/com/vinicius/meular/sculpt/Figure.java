package com.vinicius.meular.sculpt;

import com.vinicius.meular.sculpt.Prims.Field;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import static com.vinicius.meular.sculpt.Prims.mixf;
import static com.vinicius.meular.sculpt.Prims.sstep;

/** Monta o personagem inteiro: camadas de geometria (em cache) + cores (baratas, refeitas a cada troca de cor). */
public final class Figure {
    private Figure() {}

    /** Parte do visual que muda a forma. */
    public static final class Spec {
        public boolean female; public int build, hair, top, bottom, glasses, beard;
        String body() { return (female ? "f" : "m") + build; }
    }

    /** Cores (0xRRGGBB). */
    public static final class Pal { public int skin, hair, beard, eye, top, bottom, shoe; public boolean lensDark; }

    private static final HashMap<String, Layer> cache = new HashMap<>();
    private static final HashMap<String, Body> bodies = new HashMap<>();

    public static Body body(Spec s) {
        Body b = bodies.get(s.body());
        if (b == null) { b = new Body(s.female, s.build); bodies.put(s.body(), b); }
        return b;
    }

    // ------------------------------------------------------------------ geometria
    static Layer skinLayer(Spec s, String part) {
        String key = "skin:" + s.body() + ":" + part;
        Layer c = cache.get(key);
        if (c != null) return c;
        final Body body = body(s);
        Layer l;
        final Layer.Tagger tg = skinTagger(body);
        if (part.equals("body")) {
            Mesher.Out o = Mesher.run(body, -0.38f, -0.02f, -0.20f, 0.38f, 1.40f, 0.24f, 0.0110f);
            l = Layer.from(o, tg).without(new Layer.Drop() {
                public boolean drop(float x, float y, float z) {
                    if (y > 1.295f) return true;                 // cabeca fica por conta da malha fina
                    return inHand(body.handL, x, y, z) || inHand(body.handR, x, y, z);
                }
            });
        } else if (part.equals("head")) {
            Mesher.Out o = Mesher.run(body, -0.13f, 1.27f, -0.13f, 0.13f, 1.60f, 0.14f, 0.0045f);
            l = Layer.from(o, tg);
        } else {
            Body.Hand h = part.equals("handL") ? body.handL : body.handR;
            float[] w = part.equals("handL") ? body.wristL : body.wristR;
            Mesher.Out o = Mesher.run(body, w[0] - 0.09f, w[1] - 0.17f, w[2] - 0.09f, w[0] + 0.09f, w[1] + 0.03f, w[2] + 0.09f, 0.0038f);
            l = Layer.from(o, tg);
        }
        cache.put(key, l);
        return l;
    }

    private static boolean inHand(Body.Hand h, float x, float y, float z) {
        float dx = x - h.cx, dy = y - h.cy, dz = z - h.cz;
        return dx * dx + dy * dy + dz * dz < 0.115f * 0.115f && y < h.cy + 0.07f;
    }

    /** Pintura do rosto e sombreado de cavidades (AO). */
    static Layer.Tagger skinTagger(final Body body) {
        final float hy = Body.HEAD_Y;
        return new Layer.Tagger() {
            public void tag(float x, float y, float z, float nx, float ny, float nz, float[] o) {
                o[0] = Layer.SKIN; o[1] = 0f;
                // oclusao ambiente barata: compara a distancia um pouco para fora com o esperado
                float s = 0.012f;
                float dd = body.d(x + nx * s, y + ny * s, z + nz * s);
                float ao = 1f - sstep(0.35f, 1.0f, dd / s);
                o[2] = ao;
                float dx = x, dy = y - hy, dz = z;
                if (dx * dx + dy * dy + dz * dz > 0.16f * 0.16f) return;
                if (nz < -0.2f) return;
                float ax = Math.abs(x);
                // bochechas coradas
                float cb = (float) Math.sqrt((ax - 0.052f) * (ax - 0.052f) + (y - (hy - 0.048f)) * (y - (hy - 0.048f)) * 1.3f);
                float blush = 1f - sstep(0.012f, 0.032f, cb);
                if (z > 0.03f) o[1] = blush * (body.female ? 0.34f : 0.20f);
                if (z < 0.05f) return;
                // labios
                float lu = lipDist(body, x, y, z);
                if (lu < 0.0035f) {
                    o[0] = Layer.LIP; o[1] = 1f - sstep(0.0008f, 0.0034f, lu);
                    float sm = ax / 0.0215f; float gv = Math.abs(y - (hy + Body.LIP_DY + 0.0048f * sm * sm));
                    o[2] = Math.max(ao, 0f);
                    if (gv < 0.0036f && ax < 0.0225f) { float wl = (1f - sstep(0.0008f, 0.0036f, gv)) * (1f - sstep(0.016f, 0.0225f, ax)); o[1] = Math.max(o[1], wl); o[2] = Math.max(o[2], 0.85f * wl); }   // linha da boca
                }
                // sobrancelhas (arco pintado)
                float u = (ax - 0.012f) / 0.052f;
                if (u > 0f && u < 1.05f) {
                    float yc = hy + 0.0245f + 0.0085f * (float) Math.sin(Math.PI * Math.min(u, 1f) * 0.85f + 0.25f) - 0.006f * u * u;
                    float th = 0.0042f * (1f - 0.55f * u) + 0.0012f;
                    float dbr = Math.abs(y - yc) / th;
                    if (dbr < 1f && u < 1f) { o[0] = Layer.BROW; o[1] = (1f - sstep(0.45f, 1f, dbr)) * (1f - sstep(0.80f, 1.0f, u) * 0.9f); }
                }
                // contorno do olho (cilios)
                float cut = (x > 0 ? eyeCut(body, x, y, z, 1) : eyeCut(body, x, y, z, -1));
                if (cut > -0.0006f && cut < 0.0036f) {
                    float w = 1f - sstep(0.0004f, body.female ? 0.0036f : 0.0026f, cut);
                    if (y < hy + 0.003f) w *= 0.30f;
                    if (w > 0.02f) { o[0] = Layer.LASH; o[1] = w; }
                }
            }
        };
    }

    private static float lipDist(Body b, float x, float y, float z) { return b.lipDist(x, y, z); }
    private static float eyeCut(Body b, float x, float y, float z, int side) { return b.eyeCut(x, y, z, side); }

    static Layer eyes(Spec s, Body body) {
        String key = "eyes:" + s.body();
        Layer c = cache.get(key);
        if (c != null) return c;
        float ex = body.eyeX(), ey = body.eyeY();
        float zf = body.surfaceZ(ex, ey);
        float re = 0.0150f;
        float cz = zf - 0.0030f - re * 0.985f;
        Layer a = Eyes.eye(ex, ey, cz, re, 1f, 0.0108f, 0.0050f);
        Layer b = Eyes.eye(-ex, ey, cz, re, -1f, 0.0108f, 0.0050f);
        Layer r = merge(a, b);
        cache.put(key, r);
        return r;
    }

    static Layer merge(Layer... ls) {
        Layer r = new Layer();
        int nv = 0, nt = 0;
        for (Layer l : ls) { nv += l.nv; nt += l.nt; }
        r.p = new float[nv * 3]; r.n = new float[nv * 3]; r.tag = new int[nv]; r.a = new float[nv]; r.b = new float[nv]; r.t = new int[nt * 3];
        r.nv = nv; r.nt = nt;
        int vo = 0, to = 0;
        for (Layer l : ls) {
            System.arraycopy(l.p, 0, r.p, vo * 3, l.nv * 3); System.arraycopy(l.n, 0, r.n, vo * 3, l.nv * 3);
            System.arraycopy(l.tag, 0, r.tag, vo, l.nv); System.arraycopy(l.a, 0, r.a, vo, l.nv); System.arraycopy(l.b, 0, r.b, vo, l.nv);
            for (int i = 0; i < l.nt * 3; i++) r.t[to * 3 + i] = l.t[i] + vo;
            vo += l.nv; to += l.nt;
        }
        return r;
    }

    // ------------------------------------------------------------------ cores
    private static float[] rgb(int c) { return new float[]{((c >> 16) & 255) / 255f, ((c >> 8) & 255) / 255f, (c & 255) / 255f}; }

    private static final float ALB = 0.80f;

    private static void color(Layer l, int i, Pal p, float[] out) {
        int tg = l.tag[i]; float a = l.a[i], b = l.b[i];
        float[] sk = rgb(p.skin);
        switch (tg) {
            case Layer.SKIN: {
                float r = sk[0], g = sk[1], bl = sk[2];
                // sombra quente nas cavidades
                float k = b * 0.55f;
                r = mixf(r, sk[0] * 0.80f, k); g = mixf(g, sk[1] * 0.58f, k); bl = mixf(bl, sk[2] * 0.55f, k);
                // rubor
                r = mixf(r, Math.min(1f, sk[0] * 1.00f + 0.02f), a); g = mixf(g, sk[1] * 0.72f, a); bl = mixf(bl, sk[2] * 0.74f, a);
                out[0] = r; out[1] = g; out[2] = bl; return;
            }
            case Layer.LIP: {
                float[] lp = {Math.min(1f, sk[0] * 0.90f + 0.10f), sk[1] * 0.50f + 0.04f, sk[2] * 0.52f + 0.07f};
                float dk = b * 0.45f;
                out[0] = mixf(sk[0], lp[0] * (1f - dk), a); out[1] = mixf(sk[1], lp[1] * (1f - dk), a); out[2] = mixf(sk[2], lp[2] * (1f - dk), a); return;
            }
            case Layer.BROW: {
                float[] h = rgb(p.hair);
                out[0] = mixf(sk[0], h[0] * 0.85f, a * 0.85f); out[1] = mixf(sk[1], h[1] * 0.85f, a * 0.85f); out[2] = mixf(sk[2], h[2] * 0.85f, a * 0.85f); return;
            }
            case Layer.LASH: {
                out[0] = mixf(sk[0], 0.10f, a * 0.92f); out[1] = mixf(sk[1], 0.07f, a * 0.92f); out[2] = mixf(sk[2], 0.08f, a * 0.92f); return;
            }
            case Layer.SCLERA: {
                float sh = 1f - a * 0.9f;
                out[0] = 0.97f * sh; out[1] = 0.95f * sh; out[2] = 0.94f * sh; return;
            }
            case Layer.IRIS: {
                float[] e = rgb(p.eye);
                float inner = 1f - sstep(0f, 0.55f, a);                  // anel claro perto da pupila
                float limb = sstep(0.78f, 1f, a);                       // borda escura
                float r = mixf(e[0], Math.min(1f, e[0] * 1.45f + 0.10f), inner * 0.8f);
                float g = mixf(e[1], Math.min(1f, e[1] * 1.45f + 0.10f), inner * 0.8f);
                float bl = mixf(e[2], Math.min(1f, e[2] * 1.45f + 0.10f), inner * 0.8f);
                float d = 1f - limb * 0.6f - b * 0.5f;
                out[0] = r * d; out[1] = g * d; out[2] = bl * d; return;
            }
            case Layer.PUPIL: out[0] = 0.03f; out[1] = 0.02f; out[2] = 0.04f; return;
            case Layer.GLINT: {
                out[0] = mixf(0.10f, 1f, a); out[1] = mixf(0.09f, 1f, a); out[2] = mixf(0.10f, 1f, a); return;
            }
            case Layer.HAIR: {
                float[] h = rgb(p.hair);
                float k = (0.78f + 0.44f * a) * (1f - 0.50f * b);
                out[0] = Math.min(1f, h[0] * k + 0.015f * a); out[1] = Math.min(1f, h[1] * k + 0.012f * a); out[2] = Math.min(1f, h[2] * k + 0.010f * a); return;
            }
            case Layer.BEARD: {
                float[] h = rgb(p.beard);
                float k = (0.80f + 0.34f * a) * (1f - 0.40f * b);
                out[0] = h[0] * k; out[1] = h[1] * k; out[2] = h[2] * k; return;
            }
            case Layer.TOP: case Layer.BOT: {
                float[] t = rgb(tg == Layer.TOP ? p.top : p.bottom);
                float k = (1f - 0.15f * a) * (1f - 0.42f * b);
                out[0] = t[0] * k; out[1] = t[1] * k; out[2] = t[2] * k; return;
            }
            case Layer.SHOE: {
                float[] t = rgb(p.shoe);
                float k = 1f - 0.40f * b;
                out[0] = t[0] * k; out[1] = t[1] * k; out[2] = t[2] * k; return;
            }
            case Layer.SOLE: {
                float k = 1f - 0.30f * b;
                out[0] = 0.95f * k; out[1] = 0.94f * k; out[2] = 0.91f * k; return;
            }
            case Layer.FRAME: out[0] = 0.09f; out[1] = 0.085f; out[2] = 0.10f; return;
            case Layer.LENS: {
                if (p.lensDark) { out[0] = 0.04f; out[1] = 0.045f; out[2] = 0.06f; }
                else { out[0] = 0.70f; out[1] = 0.84f; out[2] = 0.95f; }
                return;
            }
            default: out[0] = 1f; out[1] = 0f; out[2] = 1f;
        }
    }

    /** Empacota camadas em triangulos soltos (stride 12) com as cores da paleta. */
    public static float[] pack(List<Layer> layers, Pal p) {
        int nt = 0;
        for (Layer l : layers) nt += l.nt;
        float[] o = new float[nt * 3 * 12];
        int k = 0;
        float[] c = new float[3];
        for (Layer l : layers) {
            float[] cols = new float[l.nv * 3];
            float[] alp = new float[l.nv];
            for (int i = 0; i < l.nv; i++) { color(l, i, p, c); cols[i * 3] = c[0] * ALB; cols[i * 3 + 1] = c[1] * ALB; cols[i * 3 + 2] = c[2] * ALB; alp[i] = l.tag[i] == Layer.LENS ? (p.lensDark ? 0.88f : 0.24f) : 1f; }
            for (int i = 0; i < l.nt; i++) for (int q = 0; q < 3; q++) {
                int v = l.t[i * 3 + q];
                o[k] = l.p[v * 3]; o[k + 1] = l.p[v * 3 + 1]; o[k + 2] = l.p[v * 3 + 2];
                o[k + 3] = l.n[v * 3]; o[k + 4] = l.n[v * 3 + 1]; o[k + 5] = l.n[v * 3 + 2];
                o[k + 6] = cols[v * 3]; o[k + 7] = cols[v * 3 + 1]; o[k + 8] = cols[v * 3 + 2]; o[k + 9] = alp[v];
                o[k + 10] = 0f; o[k + 11] = 0f;
                k += 12;
            }
        }
        return o;
    }

    // ------------------------------------------------------------------ pecas (com cache)
    private static Layer part(String key, Gen g) {
        Layer c = cache.get(key);
        if (c == null) {
            if (cache.size() > 44) {
                // descarta primeiro roupas e cabelos; a pele (cara de refazer) so se estiver muito cheio
                java.util.Iterator<String> it = cache.keySet().iterator();
                while (it.hasNext()) { String k = it.next(); if (!k.startsWith("skin:") && !k.startsWith("eyes:")) it.remove(); }
                if (cache.size() > 28) cache.clear();
            }
            c = g.make();
            cache.put(key, c);
        }
        return c;
    }

    private interface Gen { Layer make(); }

    private static Layer lensLayer(final Spec s, final Body body) {
        return part("lens:" + s.glasses + ":" + s.body(), new Gen() { public Layer make() { return Gear.lens(s.glasses, body); } });
    }

    /** Camadas opacas do personagem (define tambem se a lente e escura). */
    private static List<Layer> solidLayers(final Spec s, Pal p) {
        final Body body = body(s);
        List<Layer> ls = new ArrayList<>();
        ls.add(skinLayer(s, "body")); ls.add(skinLayer(s, "head")); ls.add(skinLayer(s, "handL")); ls.add(skinLayer(s, "handR"));
        ls.add(eyes(s, body));
        final String bk = s.body();
        if (s.hair > 0) ls.add(part("hair:" + s.hair + ":" + (s.female ? "f" : "m"), new Gen() { public Layer make() { return Gear.hair(s.hair, body); } }));
        if (s.beard > 0) ls.add(part("beard:" + s.beard + ":" + (s.female ? "f" : "m"), new Gen() { public Layer make() { return Gear.beard(s.beard, body); } }));
        ls.add(part("top:" + s.top + ":" + bk, new Gen() { public Layer make() { return Gear.top(s.top, body); } }));
        if (s.top == 4) {
            ls.add(part("dress:" + bk, new Gen() { public Layer make() { return Gear.skirt(body, 0.945f, 0.600f, 0.122f, 0.205f, 0.500f, Layer.TOP); } }));
        } else {
            ls.add(part("bot:" + s.bottom + ":" + bk, new Gen() { public Layer make() { return Gear.bottom(s.bottom, body); } }));
        }
        ls.add(part("shoes:" + bk, new Gen() { public Layer make() { return Gear.shoes(body); } }));
        if (s.glasses > 0) ls.add(part("frame:" + s.glasses + ":" + bk, new Gen() { public Layer make() { return Gear.frame(s.glasses, body); } }));
        p.lensDark = s.glasses == 3;
        return ls;
    }

    /** Todas as pecas opacas, em triangulos soltos (stride 12). So para testes no PC. */
    public static synchronized float[] build(final Spec s, Pal p) {
        return pack(solidLayers(s, p), p);
    }

    /** So as lentes dos oculos (transparentes); vazio se nao houver oculos. So para testes no PC. */
    public static synchronized float[] buildGlass(Spec s, Pal p) {
        if (s.glasses <= 0) return new float[0];
        List<Layer> ls = new ArrayList<>();
        ls.add(lensLayer(s, body(s)));
        p.lensDark = s.glasses == 3;
        return pack(ls, p);
    }

    // ------------------------------------------------------------------ malha indexada para o app
    /** Pedaco de malha indexada (ate 65000 vertices; vertice = pos3 nor3 cor4 uv2). */
    public static final class Chunk {
        public float[] v = new float[12 * 2048];
        public int nv;
        public short[] idx = new short[3 * 4096];
        public int ni;
        public boolean glass;

        int vert(Layer l, int i, float[] cols, float[] alp) {
            if ((nv + 1) * 12 > v.length) v = java.util.Arrays.copyOf(v, v.length * 2);
            int k = nv * 12;
            v[k] = l.p[i * 3]; v[k + 1] = l.p[i * 3 + 1]; v[k + 2] = l.p[i * 3 + 2];
            v[k + 3] = l.n[i * 3]; v[k + 4] = l.n[i * 3 + 1]; v[k + 5] = l.n[i * 3 + 2];
            v[k + 6] = cols[i * 3]; v[k + 7] = cols[i * 3 + 1]; v[k + 8] = cols[i * 3 + 2]; v[k + 9] = alp[i];
            v[k + 10] = 0f; v[k + 11] = 0f;
            return nv++;
        }

        void index(int id) {
            if (ni == idx.length) idx = java.util.Arrays.copyOf(idx, idx.length * 2);
            idx[ni++] = (short) id;
        }

        void trim() { v = java.util.Arrays.copyOf(v, nv * 12); idx = java.util.Arrays.copyOf(idx, ni); }
    }

    private static final int MAXV = 65000;

    private static void packIndexed(List<Layer> layers, Pal p, boolean glass, List<Chunk> out) {
        Chunk cur = null;
        float[] c = new float[3];
        for (Layer l : layers) {
            float[] cols = new float[l.nv * 3];
            float[] alp = new float[l.nv];
            for (int i = 0; i < l.nv; i++) {
                color(l, i, p, c);
                cols[i * 3] = c[0] * ALB; cols[i * 3 + 1] = c[1] * ALB; cols[i * 3 + 2] = c[2] * ALB;
                alp[i] = l.tag[i] == Layer.LENS ? (p.lensDark ? 0.88f : 0.24f) : 1f;
            }
            int[] map = new int[l.nv];
            java.util.Arrays.fill(map, -1);
            for (int i = 0; i < l.nt; i++) {
                if (cur == null || cur.nv + 3 > MAXV) {
                    if (cur != null) { cur.trim(); out.add(cur); }
                    cur = new Chunk(); cur.glass = glass;
                    java.util.Arrays.fill(map, -1);
                }
                for (int q = 0; q < 3; q++) {
                    int v = l.t[i * 3 + q];
                    if (map[v] < 0) map[v] = cur.vert(l, v, cols, alp);
                    cur.index(map[v]);
                }
            }
        }
        if (cur != null && cur.ni > 0) { cur.trim(); out.add(cur); }
    }

    /** Monta o personagem para o app: pedacos opacos primeiro, lentes (translucidas) por ultimo. */
    public static synchronized Chunk[] buildChunks(Spec s, Pal p) {
        List<Layer> ls = solidLayers(s, p);
        List<Chunk> out = new ArrayList<>();
        packIndexed(ls, p, false, out);
        if (s.glasses > 0) {
            List<Layer> gl = new ArrayList<>();
            gl.add(lensLayer(s, body(s)));
            packIndexed(gl, p, true, out);
        }
        return out.toArray(new Chunk[0]);
    }
}
