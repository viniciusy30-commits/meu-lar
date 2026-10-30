package com.vinicius.meular.sculpt;

import com.vinicius.meular.sculpt.Prims.Cone;
import com.vinicius.meular.sculpt.Prims.Ell;
import com.vinicius.meular.sculpt.Prims.Field;

import static com.vinicius.meular.sculpt.Prims.mixf;
import static com.vinicius.meular.sculpt.Prims.smax;
import static com.vinicius.meular.sculpt.Prims.smin;
import static com.vinicius.meular.sculpt.Prims.sstep;

/** Cabelo, barba, roupas, sapatos e oculos esculpidos (mesma tecnica da pele: campo de distancia + malha lisa). */
final class Gear {
    private Gear() {}

    private static final float HY = Body.HEAD_Y;
    /** Resolucao da malha das roupas (metros por celula). */
    static final float CH = 0.0095f;

    // ------------------------------------------------------------------ utilidades
    /** Plano de corte no meio de uma celula da grade (borda limpa, sem serrilhado). */
    static float snapY(float y, float h) { return ((float) Math.floor(y / h) + 0.5f) * h; }

    static float gridY0(float ymin, float h) { return (float) Math.floor(ymin / h) * h; }

    /** Plano: ponto, normal (para fora da peca) e tolerancia. */
    private static float[] plane(float px, float py, float pz, float nx, float ny, float nz, float tol) {
        return new float[]{px, py, pz, nx, ny, nz, tol};
    }

    /** Remove as tampas planas deixadas pelos cortes (a roupa fica aberta na barra e nas mangas). */
    static Layer dropCaps(Layer l, float[][] planes) {
        Layer r = new Layer();
        r.p = l.p; r.n = l.n; r.tag = l.tag; r.a = l.a; r.b = l.b; r.nv = l.nv;
        int[] t2 = new int[l.nt * 3];
        int k = 0;
        for (int i = 0; i < l.nt; i++) {
            int A = l.t[i * 3], B = l.t[i * 3 + 1], C = l.t[i * 3 + 2];
            boolean cap = false;
            for (float[] q : planes) {
                if (!near(l, A, q) || !near(l, B, q) || !near(l, C, q)) continue;
                float ux = l.p[B * 3] - l.p[A * 3], uy = l.p[B * 3 + 1] - l.p[A * 3 + 1], uz = l.p[B * 3 + 2] - l.p[A * 3 + 2];
                float vx = l.p[C * 3] - l.p[A * 3], vy = l.p[C * 3 + 1] - l.p[A * 3 + 1], vz = l.p[C * 3 + 2] - l.p[A * 3 + 2];
                float nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
                float nl = (float) Math.sqrt(nx * nx + ny * ny + nz * nz);
                if (nl < 1e-12f) { cap = true; break; }
                if ((nx * q[3] + ny * q[4] + nz * q[5]) / nl > 0.85f) { cap = true; break; }
            }
            if (!cap) { t2[k++] = A; t2[k++] = B; t2[k++] = C; }
        }
        r.t = java.util.Arrays.copyOf(t2, k);
        r.nt = k / 3;
        return r;
    }

    private static boolean near(Layer l, int v, float[] q) {
        float d = (l.p[v * 3] - q[0]) * q[3] + (l.p[v * 3 + 1] - q[1]) * q[4] + (l.p[v * 3 + 2] - q[2]) * q[5];
        return Math.abs(d) <= q[6];
    }

    /** Oclusao ambiente barata (como na pele): compara a distancia um pouco para fora com a esperada. */
    static float ao(Field f, float x, float y, float z, float nx, float ny, float nz) {
        float s = 0.012f;
        float dd = f.d(x + nx * s, y + ny * s, z + nz * s);
        return 1f - sstep(0.35f, 1.0f, dd / s);
    }

    /** Cilindro reto de raio r entre a e b, limitado por fracoes t0..t1 do comprimento (regiao das mangas). */
    static final class Tube {
        private final float ax, ay, az, ux, uy, uz, len, r;
        Tube(float ax, float ay, float az, float bx, float by, float bz, float r) {
            this.ax = ax; this.ay = ay; this.az = az;
            float dx = bx - ax, dy = by - ay, dz = bz - az;
            len = (float) Math.sqrt(dx * dx + dy * dy + dz * dz);
            ux = dx / len; uy = dy / len; uz = dz / len;
            this.r = r;
        }
        float d(float x, float y, float z, float t0, float t1) {
            float px = x - ax, py = y - ay, pz = z - az;
            float s = px * ux + py * uy + pz * uz;
            float qx = px - s * ux, qy = py - s * uy, qz = pz - s * uz;
            float rad = (float) Math.sqrt(qx * qx + qy * qy + qz * qz) - r;
            return Math.max(rad, Math.max(t0 * len - s, s - t1 * len));
        }
    }

    // ------------------------------------------------------------------ roupa de cima
    static Layer top(final int kind, final Body b) {
        final float H = CH;
        final boolean sleeves = kind == 0 || kind == 1 || kind == 3;
        final boolean longS = kind == 1 || kind == 3;
        final float hem = snapY(kind == 3 ? 0.79f : (kind == 4 ? 0.93f : (kind == 2 ? 0.86f : 0.84f)), H);
        final float cutY = snapY(longS ? b.wristL[1] + 0.030f : 1.07f, H);
        final float base = kind == 3 ? 0.0125f : (kind == 2 || kind == 4 ? 0.0085f : 0.0075f);
        final float loose = kind == 3 ? 0.020f : (kind == 4 ? 0.0f : (kind == 2 ? 0.011f : 0.013f));
        final float sh = b.shW;
        final float[] sL = b.shoulderL, eL = b.elbowL, wL = b.wristL;
        final Tube upT = new Tube(sL[0], sL[1], sL[2], eL[0], eL[1], eL[2], 0.066f);
        final Tube foT = new Tube(eL[0], eL[1], eL[2], wL[0], wL[1], wL[2], 0.060f);
        final boolean wide = kind == 2 || kind == 4;
        final Ell neck = wide ? new Ell(0, 1.318f, 0.030f, 0.074f, 0.060f, 0.084f)
                : (kind == 3 ? new Ell(0, 1.346f, 0.014f, 0.060f, 0.052f, 0.066f) : new Ell(0, 1.322f, 0.022f, 0.064f, 0.050f, 0.080f));
        final Ell hood = new Ell(0, 1.300f, -0.048f, 0.084f, 0.046f, 0.062f);
        final Field f = (x, y, z) -> {
            float d = b.d(x, y, z);
            if (d > 0.08f) return d;
            float ax = Math.abs(x);
            float sd = d - (base + loose * sstep(1.10f, 0.92f, y));
            float xl = wide ? mixf((b.female ? 0.130f : 0.152f) * b.wScale + 0.012f, sh - 0.045f, sstep(1.13f, 1.20f, y)) : sh + 0.025f;
            float reg = Math.max(ax - xl, Math.max(hem - y, y - 1.345f));
            if (sleeves) {
                float rs = Math.max(upT.d(ax, y, z, -0.42f, 9f), y - 1.345f);
                if (longS) rs = Math.min(rs, foT.d(ax, y, z, -0.035f, 9f));
                rs = Math.max(rs, cutY - y);
                reg = Math.min(reg, rs);
            }
            float r = Math.max(sd, reg);
            if (kind == 3) r = smin(r, hood.d(x, y, z), 0.02f);
            return smax(r, -neck.d(x, y, z), 0.005f);
        };
        Mesher.Out o = Mesher.run(f, -0.34f, gridY0(hem - 0.03f, H), -0.16f, 0.34f, 1.40f, 0.18f, H);
        Layer l = Layer.from(o, (x, y, z, nx, ny, nz, out) -> {
            float band = 1f - sstep(0f, 0.016f, y - hem);
            if (sleeves && Math.abs(x) > sh - 0.005f) band = Math.max(band, 1f - sstep(0f, 0.016f, y - cutY));
            out[0] = Layer.TOP;
            out[1] = band;
            out[2] = ao(f, x, y, z, nx, ny, nz);
        });
        java.util.ArrayList<float[]> pl = new java.util.ArrayList<>();
        pl.add(plane(0, hem, 0, 0, -1, 0, 0.9f * H));
        if (sleeves) pl.add(plane(0, cutY, 0, 0, -1, 0, 0.9f * H));
        return dropCaps(l, pl.toArray(new float[0][]));
    }


    // ------------------------------------------------------------------ roupa de baixo
    /** kind: 0 calca, 1 bermuda, 2 saia, 3 short. */
    static Layer bottom(final int kind, final Body b) {
        if (kind == 2) return skirt(b, 0.975f, 0.640f, 0.128f, 0.215f, 0.585f, Layer.BOT);
        final float H = CH;
        final float hem = snapY(kind == 0 ? 0.080f : (kind == 1 ? 0.405f : 0.600f), H);
        final float top = snapY(0.960f, H);
        final float xlim = Math.max(b.shW + 0.006f, b.legX + 0.095f);
        final float base = kind == 0 ? 0.0085f : 0.011f;
        final float flare = kind == 0 ? 0.004f : 0.009f;
        final Field f = (x, y, z) -> {
            float d = b.d(x, y, z);
            if (d > 0.08f) return d;
            float ax = Math.abs(x);
            float sd = d - (base + flare * sstep(hem + 0.14f, hem, y));
            float reg = Math.max(ax - xlim, Math.max(hem - y, y - top));
            return Math.max(sd, reg);
        };
        Mesher.Out o = Mesher.run(f, -0.26f, gridY0(hem - 0.03f, H), -0.19f, 0.26f, top + 0.03f, 0.19f, H);
        Layer l = Layer.from(o, (x, y, z, nx, ny, nz, out) -> {
            float band = 1f - sstep(0f, 0.016f, y - hem);
            float wb = 1f - sstep(0f, 0.022f, top - y);                       // cos
            out[0] = Layer.BOT;
            out[1] = Math.max(band, wb * 0.8f);
            out[2] = ao(f, x, y, z, nx, ny, nz);
        });
        return dropCaps(l, new float[][]{plane(0, hem, 0, 0, -1, 0, 0.9f * H), plane(0, top, 0, 0, 1, 0, 0.9f * H)});
    }

    /** Saia/vestido rodado (cone arredondado, cortado plano em cima e embaixo, com pregas suaves). */
    static Layer skirt(final Body b, final float yTop, final float yMid, final float rTop, final float rBot, final float yHemN, final int tag) {
        final float H = CH;
        final Cone sk = new Cone(0, yTop, 0, 0, yMid, 0, rTop, rBot);
        final float yHem = snapY(yHemN, H);
        final float yCut = snapY(yTop + 0.012f, H);
        final Field f = (x, y, z) -> {
            float d = sk.d(x, y, z);
            if (d > 0.06f) return d;
            float th = (float) Math.atan2(z, x);
            d += 0.0055f * sstep(yTop - 0.12f, yHem, y) * (float) Math.sin(11f * th);   // pregas que crescem para a barra
            return Math.max(d, Math.max(yHem - y, y - yCut));
        };
        Mesher.Out o = Mesher.run(f, -0.27f, gridY0(yHem - 0.03f, H), -0.27f, 0.27f, yCut + 0.03f, 0.27f, H);
        Layer l = Layer.from(o, (x, y, z, nx, ny, nz, out) -> {
            out[0] = tag;
            out[1] = Math.max(1f - sstep(0f, 0.016f, y - yHem), 0.8f * (1f - sstep(0f, 0.02f, yTop - y)));
            out[2] = ao(f, x, y, z, nx, ny, nz);
        });
        return dropCaps(l, new float[][]{plane(0, yHem, 0, 0, -1, 0, 0.9f * H), plane(0, yCut, 0, 0, 1, 0, 0.9f * H)});
    }

    // ------------------------------------------------------------------ sapatos

    static Layer shoes(final Body b) {
        final float H = 0.0052f;
        final float x0 = b.legX + 0.003f;
        final float yb = snapY(-0.0004f, H);
        final Ell upper = new Ell(x0, 0.050f, 0.034f, 0.0455f, 0.046f, 0.108f);
        final Cone collar = new Cone(x0, 0.140f, -0.010f, x0, 0.070f, -0.004f, 0.040f, 0.046f);
        final Ell sole = new Ell(x0, 0.014f, 0.034f, 0.0488f, 0.0150f, 0.112f);
        final Field f = (x, y, z) -> {
            float xx = Math.abs(x);
            float d = smin(upper.d(xx, y, z), collar.d(xx, y, z), 0.02f);
            d = smin(d, sole.d(xx, y, z), 0.006f);
            return Math.max(d, yb - y);
        };
        Mesher.Out o = Mesher.run(f, -0.19f, gridY0(-0.03f, H), -0.10f, 0.19f, 0.16f, 0.17f, H);
        Layer l = Layer.from(o, (x, y, z, nx, ny, nz, out) -> {
            out[0] = y < 0.026f ? Layer.SOLE : Layer.SHOE;
            out[1] = 0f;
            out[2] = ao(f, x, y, z, nx, ny, nz);
        });
        return dropCaps(l, new float[][]{plane(0, yb, 0, 0, -1, 0, 0.9f * H)});
    }


    // ------------------------------------------------------------------ cabelo
    /** Mechas: -1..1, em fatias radiais a partir do alto da cabeca (da o ar de fios sem custar triangulos). */
    private static float strand(float x, float y, float z) {
        float ang = (float) Math.atan2(x, z + 0.014f);
        float n = Prims.noise(x * 28f, y * 28f, z * 28f);
        return (float) Math.sin(ang * 15f + 2.6f * n + y * 9f);
    }

    /** style: 1 curto, 2 medio, 3 longo, 4 rabo de cavalo, 5 coque, 6 moicano, 7 black power, 8 topete. */
    static Layer hair(final int style, final Body b) {
        final float hy = HY, hw = b.hw;
        final Ell cap = new Ell(0, hy + 0.030f, -0.014f, hw + 0.0145f, 0.102f, 0.110f);
        final float hl, yl, slope, yMin;
        switch (style) {
            case 1: hl = 0.044f; yl = 0.036f; slope = 0.55f; yMin = hy - 0.10f; break;
            case 2: hl = 0.040f; yl = -0.088f; slope = 0.0f; yMin = hy - 0.13f; break;
            case 3: hl = 0.040f; yl = -0.40f; slope = 0.0f; yMin = 1.06f; break;
            case 4: hl = 0.088f; yl = 0.030f; slope = 0.55f; yMin = hy - 0.22f; break;
            case 5: hl = 0.088f; yl = 0.030f; slope = 0.55f; yMin = hy - 0.10f; break;
            case 6: hl = 0.094f; yl = 0.040f; slope = 0.50f; yMin = hy - 0.10f; break;
            case 7: hl = 0.074f; yl = -0.040f; slope = 0.30f; yMin = hy - 0.12f; break;
            default: hl = 0.074f; yl = 0.036f; slope = 0.55f; yMin = hy - 0.10f; break;
        }
        // volumes extras por estilo
        final Ell bobBack = new Ell(0, hy - 0.020f, -0.052f, hw + 0.030f, 0.100f, 0.090f);
        final Ell bobL = new Ell(hw + 0.012f, hy - 0.030f, -0.012f, 0.028f, 0.078f, 0.082f);
        final Ell sheet = new Ell(0, 1.285f, -0.078f, 0.100f, 0.215f, 0.048f);
        final Ell lockL = new Ell(hw + 0.012f, 1.300f, -0.006f, 0.027f, 0.150f, 0.052f);
        final Cone tail = new Cone(0, hy + 0.036f, -0.108f, 0, hy - 0.105f, -0.168f, 0.030f, 0.013f);
        final Ell knot = new Ell(0, hy + 0.040f, -0.110f, 0.034f, 0.034f, 0.030f);
        final Ell bun = new Ell(0, hy + 0.118f, -0.052f, 0.052f, 0.046f, 0.052f);
        final Ell crest = new Ell(0, hy + 0.092f, -0.018f, 0.021f, 0.060f, 0.120f);
        final Ell thin = new Ell(0, hy + 0.030f, -0.014f, hw + 0.0035f, 0.0955f, 0.1035f);
        final Ell afro = new Ell(0, hy + 0.045f, -0.012f, 0.132f, 0.128f, 0.134f);
        final Ell quiff = new Ell(0, hy + 0.112f, 0.050f, 0.062f, 0.040f, 0.082f, -0.32f, 0f, 0f);
        final Ell fringe = new Ell(0.014f, hy + 0.080f, 0.072f, 0.078f, 0.028f, 0.036f, 0f, 0f, -0.16f);
        final Ell fringeBig = new Ell(0.010f, hy + 0.076f, 0.074f, 0.090f, 0.034f, 0.038f, 0f, 0f, -0.20f);
        final Ell fringeS = new Ell(0.008f, hy + 0.082f, 0.070f, 0.070f, 0.030f, 0.034f, 0f, 0f, -0.14f);

        final Field f = (x, y, z) -> {
            float ax = Math.abs(x);
            float d;
            if (style == 6) d = thin.d(x, y, z);
            else if (style == 7) d = afro.d(x, y, z);
            else d = cap.d(x, y, z);
            if (d > 0.20f) return d;
            if (style == 2) {
                d = smin(d, bobBack.d(ax, y, z), 0.03f);
                d = smin(d, bobL.d(ax, y, z), 0.03f);
            } else if (style == 3) {
                d = smin(d, bobBack.d(ax, y, z), 0.03f);
                d = smin(d, sheet.d(ax, y, z), 0.05f);
                d = smin(d, lockL.d(ax, y, z), 0.03f);
            } else if (style == 7) {
                d += 0.0055f * Prims.noise(x * 52f, y * 52f, z * 52f);
            }
            // linha do cabelo na testa (curva: mais alta nas temporas)
            float fr = Math.max(0.034f - z, y - (hy + hl + 0.034f * sstep(0.012f, 0.078f, ax)));
            d = smax(d, -fr, 0.007f);
            // limite inferior inclinado: libera as orelhas e a nuca
            d = smax(d, (hy + yl + slope * Math.min(z, 0f)) - y, 0.007f);
            // volumes que entram depois dos cortes
            switch (style) {
                case 4: d = smin(smin(d, knot.d(x, y, z), 0.02f), tail.d(x, y, z), 0.02f); break;
                case 5: d = smin(d, bun.d(x, y, z), 0.026f); break;
                case 6: d = smin(d, crest.d(x, y, z), 0.016f); break;
                case 8: d = smin(smin(d, quiff.d(x, y, z), 0.030f), fringe.d(x, y, z), 0.014f); break;
                default: break;
            }
            // mechas (relevo suave, largura de varias celulas)
            d += 0.0022f * strand(x, y, z);
            return d;
        };
        final float hres = style == 7 ? 0.0058f : 0.0054f;
        Mesher.Out o = Mesher.run(f, -0.19f, yMin, -0.22f, 0.19f, hy + 0.20f, 0.15f, hres);
        return Layer.from(o, (x, y, z, nx, ny, nz, out) -> {
            out[0] = Layer.HAIR;
            float s = strand(x, y, z);
            float a = 0.5f + 0.5f * s;
            if (style == 6 && Math.abs(x) > 0.024f) a = 0.06f;           // laterais raspadas: so uma sombra
            out[1] = a;
            out[2] = ao(f, x, y, z, nx, ny, nz);
        });
    }

    // ------------------------------------------------------------------ barba
    /** kind: 1 bigode, 2 cavanhaque, 3 barba cheia. Casca fina sobre o rosto liso. */
    static Layer beard(final int kind, final Body b) {
        final float hy = HY, hw = b.hw;
        final float t = kind == 1 ? 0.0050f : 0.0085f;
        final Ell must = new Ell(0, hy + Body.LIP_DY + 0.0225f, 0.078f, 0.036f, 0.0105f, 0.030f);
        final Ell tuft = new Ell(0, hy - 0.100f, 0.048f, 0.026f, 0.034f, 0.040f);
        final Ell jawZone = new Ell(0, hy - 0.060f, 0.006f, hw + 0.022f, 0.066f, 0.114f);
        final Ell mouth = new Ell(0, hy + Body.LIP_DY, 0.082f, 0.024f, 0.0115f, 0.022f);
        final Field f = (x, y, z) -> {
            float hd = b.headBase(x, y, z);
            if (hd > 0.045f) return hd;
            float ax = Math.abs(x);
            float d = hd - t;
            float zone;
            if (kind == 1) zone = must.d(x, y, z);
            else if (kind == 2) zone = smin(must.d(x, y, z), tuft.d(x, y, z), 0.012f);
            else {
                float up = y - (hy - 0.052f + 0.040f * sstep(0.020f, 0.080f, ax));
                zone = Math.max(jawZone.d(x, y, z), up);
                zone = smin(zone, must.d(x, y, z), 0.010f);
                d -= 0.006f * sstep(hy - 0.075f, hy - 0.115f, y) * sstep(0.0f, 0.03f, z);   // mais volume no queixo
            }
            d = Math.max(d, zone);
            if (kind >= 2) d = smax(d, -mouth.d(x, y, z), 0.004f);
            d += 0.0012f * strand(x * 1.4f, y * 1.4f, z * 1.4f);
            return d;
        };
        float yLo = kind == 1 ? hy - 0.075f : hy - 0.145f;
        Mesher.Out o = Mesher.run(f, -0.115f, yLo, -0.03f, 0.115f, hy - 0.02f, 0.135f, 0.0042f);
        return Layer.from(o, (x, y, z, nx, ny, nz, out) -> {
            out[0] = Layer.BEARD;
            out[1] = 0.5f + 0.5f * Prims.noise(x * 120f, y * 120f, z * 120f);
            out[2] = ao(f, x, y, z, nx, ny, nz);
        });
    }

    // ------------------------------------------------------------------ oculos
    private static final float[] EYEC = {Body.EYE_X, HY + Body.EYE_DY};

    /** Distancia assinada 2D (no plano xy) da forma da lente, centrada em (cx,cy). kind: 1 redondo, 2 quadrado, 3 escuro. */
    private static float lens2(int kind, float x, float y, float cx, float cy) {
        float dx = x - cx, dy = y - cy;
        if (kind == 1) return (float) Math.sqrt(dx * dx + dy * dy) - 0.0235f;
        float hx = kind == 2 ? 0.0245f : 0.0268f, hyy = kind == 2 ? 0.0195f : 0.0225f, r = kind == 2 ? 0.0060f : 0.0085f;
        if (kind == 3) dy += 0.0012f * (dx > 0 ? 1 : -1) * (Math.abs(dx) / hx);  // leve inclinacao das pontas
        float qx = Math.abs(dx) - (hx - r), qy = Math.abs(dy) - (hyy - r);
        return (float) Math.sqrt(Math.max(qx, 0f) * Math.max(qx, 0f) + Math.max(qy, 0f) * Math.max(qy, 0f)) + Math.min(Math.max(qx, qy), 0f) - r;
    }

    private static float lensZ(Body b) { return b.surfaceZ(Body.EYE_X, HY + Body.EYE_DY) + 0.0105f; }

    static Layer frame(final int kind, final Body b) {
        final float zr = lensZ(b);
        final float cx = EYEC[0], cy = EYEC[1];
        final float rt = kind == 3 ? 0.0034f : 0.0017f;                // espessura do aro
        final Cone bridge = new Cone(cx - 0.0225f, cy + 0.0060f, zr, 0.0f, cy + 0.0075f, zr + 0.0030f, rt * 0.95f, rt * 0.95f);
        final float tx = cx + (kind == 1 ? 0.0235f : 0.0268f);
        final Cone t1 = new Cone(tx, cy + 0.010f, zr - 0.001f, b.hw + 0.007f, cy + 0.011f, 0.030f, rt * 0.9f, rt * 0.9f);
        final Cone t2 = new Cone(b.hw + 0.007f, cy + 0.011f, 0.030f, b.hw + 0.012f, cy + 0.006f, -0.028f, rt * 0.9f, rt * 0.9f);
        final Cone t3 = new Cone(b.hw + 0.012f, cy + 0.006f, -0.028f, b.hw + 0.012f, cy - 0.012f, -0.034f, rt * 0.9f, rt * 0.9f);
        final Field f = (x, y, z) -> {
            float ax = Math.abs(x);
            if (ax > 0.115f) return 1f;
            float s2 = lens2(kind, ax, y, cx, cy);
            float dz = z - zr;
            float rim;
            if (kind == 3) {
                float w = Math.abs(s2 + 0.0030f) - 0.0034f;                 // aro largo e achatado
                float h = Math.abs(dz) - 0.0024f;
                rim = (float) Math.sqrt(Math.max(w, 0f) * Math.max(w, 0f) + Math.max(h, 0f) * Math.max(h, 0f)) + Math.min(Math.max(w, h), 0f) - 0.0006f;
            } else {
                rim = (float) Math.sqrt(s2 * s2 + dz * dz) - rt;
            }
            float d = rim;
            d = Math.min(d, bridge.d(ax, y, z));
            d = Math.min(d, Math.min(t1.d(ax, y, z), Math.min(t2.d(ax, y, z), t3.d(ax, y, z))));
            return d;
        };
        Mesher.Out o = Mesher.run(f, -0.112f, cy - 0.050f, -0.050f, 0.112f, cy + 0.045f, zr + 0.014f, 0.0016f);
        return Layer.from(o, (x, y, z, nx, ny, nz, out) -> { out[0] = Layer.FRAME; out[1] = 0f; out[2] = 0f; });
    }

    /** Lentes: duas folhas finas dentro dos aros (translucidas no app). */
    static Layer lens(final int kind, final Body b) {
        final float zr = lensZ(b);
        final float cx = EYEC[0], cy = EYEC[1];
        Layer.Builder bd = new Layer.Builder();
        final int seg = 44;
        for (int side = -1; side <= 1; side += 2) {
            float ox = side * cx;
            int c = bd.v(ox, cy, zr, 0, 0, 1, Layer.LENS, 0f, 0f);
            int[] ring = new int[seg];
            for (int i = 0; i < seg; i++) {
                float ang = (float) (2 * Math.PI * i / seg);
                float ux = (float) Math.cos(ang), uy = (float) Math.sin(ang);
                // acha a borda da forma na direcao (ux,uy) por bisseccao
                float lo = 0f, hi = 0.05f;
                for (int k = 0; k < 24; k++) {
                    float m = 0.5f * (lo + hi);
                    if (lens2(kind, cx + ux * m, cy + uy * m, cx, cy) < -0.0006f) lo = m; else hi = m;
                }
                ring[i] = bd.v(ox + side * ux * lo, cy + uy * lo, zr, 0, 0, 1, Layer.LENS, 0f, 0f);
            }
            for (int i = 0; i < seg; i++) {
                int j = (i + 1) % seg;
                if (side > 0) bd.tri(c, ring[i], ring[j]); else bd.tri(c, ring[j], ring[i]);
            }
        }
        return bd.done();
    }
}
