package com.vinicius.meular.mods;

/** Quais triângulos do corpo ficam por baixo de uma peça (para a pele não furar o tecido). */
public final class Cover {
    private Cover() {}

    /** [mark] (um boolean por triângulo do corpo) recebe true nos triângulos cobertos. */
    public static void mark(float[] bpos, int[] bidx, float[] ppos, float[] pnor, float radius, boolean[] mark) {
        mark(bpos, bidx, ppos, pnor, radius, mark, Float.MAX_VALUE);
    }

    /** [ymax]: triângulos do corpo acima dessa altura (pescoço/cabeça) nunca são escondidos. */
    public static void mark(float[] bpos, int[] bidx, float[] ppos, float[] pnor, float radius, boolean[] mark, float ymax) {
        if (ppos.length == 0) return;
        Grid g = new Grid(ppos, radius);
        int nt = bidx.length / 3;
        float[] d2 = new float[1];
        float r2 = radius * radius;
        for (int t = 0; t < nt && t < mark.length; t++) {
            int a = bidx[t * 3] * 3, b = bidx[t * 3 + 1] * 3, c = bidx[t * 3 + 2] * 3;
            float x = (bpos[a] + bpos[b] + bpos[c]) / 3f, y = (bpos[a + 1] + bpos[b + 1] + bpos[c + 1]) / 3f, z = (bpos[a + 2] + bpos[b + 2] + bpos[c + 2]) / 3f;
            if (y > ymax) continue;
            int i = g.nearest(x, y, z, 1, d2);
            if (i < 0 || d2[0] > r2) continue;
            // o ponto do corpo precisa estar atrás da superfície do tecido
            float side = (x - ppos[i * 3]) * pnor[i * 3] + (y - ppos[i * 3 + 1]) * pnor[i * 3 + 1] + (z - ppos[i * 3 + 2]) * pnor[i * 3 + 2];
            if (side < 0.6f) mark[t] = true;
        }
    }
}
