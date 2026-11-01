package com.vinicius.meular.sculpt;

import static com.vinicius.meular.sculpt.Prims.sstep;

/** Bolas dos olhos: esfera com iris, pupila, brilho e sombra de palpebra pintados nos vertices. */
final class Eyes {
    private Eyes() {}

    /** side: +1 / -1. c: centro. re: raio. */
    static Layer eye(float cx, float cy, float cz, float re, float side, float irisR, float pupilR) {
        Layer.Builder b = new Layer.Builder();
        // eixo do olhar: leve divergencia
        float gx = side * 0.06f, gy = 0.0f, gz = 1f;
        float gl = (float) Math.sqrt(gx * gx + gy * gy + gz * gz); gx /= gl; gy /= gl; gz /= gl;
        // base: e1 = lateral, e2 = cima
        float e1x = gz, e1y = 0, e1z = -gx; float l1 = (float) Math.sqrt(e1x * e1x + e1z * e1z); e1x /= l1; e1z /= l1;
        float e2x = gy * e1z - gz * e1y, e2y = gz * e1x - gx * e1z, e2z = gx * e1y - gy * e1x;
        int lon = 40;
        float[] th = new float[48]; int nr = 0;
        // aneis: densos na frente (iris), mais espacados atras
        for (float t = 0f; t < 0.95f; t += 0.035f) th[nr++] = t;
        for (float t = 0.95f; t <= 1.80f; t += 0.11f) th[nr++] = t;
        int[][] ring = new int[nr][lon];
        int apex = -1;
        for (int i = 0; i < nr; i++) {
            float t = th[i];
            int cnt = i == 0 ? 1 : lon;
            for (int j = 0; j < cnt; j++) {
                float ph = (float) (2 * Math.PI * j / lon);
                float st = (float) Math.sin(t), ct = (float) Math.cos(t);
                float cph = (float) Math.cos(ph), sph = (float) Math.sin(ph);
                float dx = ct * gx + st * (cph * e1x + sph * e2x);
                float dy = ct * gy + st * (cph * e1y + sph * e2y);
                float dz = ct * gz + st * (cph * e1z + sph * e2z);
                int tg; float aa = 0f, bb = 0f;
                float ir = (float) Math.asin(irisR / re), pr = (float) Math.asin(pupilR / re);
                // sombra da palpebra superior e do canto: escurece o branco no alto
                float topShade = Math.max(0f, dy * 1.2f) * 0.85f;
                if (t < pr) { tg = Layer.PUPIL; }
                else if (t < ir) {
                    tg = Layer.IRIS;
                    aa = (t - pr) / (ir - pr);               // 0 perto da pupila, 1 na borda
                    bb = topShade;
                } else {
                    tg = Layer.SCLERA; aa = sstep(ir, ir + 0.35f, t) * 0.25f + topShade * 0.6f; // sombreado leve
                }
                // brilho principal (alto, para o lado de dentro) e secundario (baixo, para fora)
                float gA = glint(t, ph, 0.31f, 2.36f, 0.14f);
                float gB = glint(t, ph, 0.36f, -0.80f, 0.065f);
                float gl2 = Math.max(gA, gB);
                if (gl2 > 0.02f && t < ir + 0.02f) { tg = Layer.GLINT; aa = gl2; bb = 0f; }
                ring[i][j] = b.v(cx + re * dx, cy + re * dy, cz + re * dz, dx, dy, dz, tg, aa, bb);
            }
        }
        for (int i = 0; i + 1 < nr; i++) {
            if (i == 0) { for (int j = 0; j < lon; j++) b.tri(ring[0][0], ring[1][j], ring[1][(j + 1) % lon]); continue; }
            for (int j = 0; j < lon; j++) {
                int j2 = (j + 1) % lon;
                b.tri(ring[i][j], ring[i + 1][j], ring[i + 1][j2]);
                b.tri(ring[i][j], ring[i + 1][j2], ring[i][j2]);
            }
        }
        return b.done();
    }

    /** Peso do brilho em (theta, phi) para um brilho centrado em (t0, p0) com raio angular rr. */
    private static float glint(float t, float ph, float t0, float p0, float rr) {
        float x1 = (float) (Math.sin(t) * Math.cos(ph)), y1 = (float) (Math.sin(t) * Math.sin(ph));
        float x0 = (float) (Math.sin(t0) * Math.cos(p0)), y0 = (float) (Math.sin(t0) * Math.sin(p0));
        float d = (float) Math.sqrt((x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0));
        return 1f - sstep(rr * 0.55f, rr, d);
    }
}
