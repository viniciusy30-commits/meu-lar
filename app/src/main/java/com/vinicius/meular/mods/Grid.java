package com.vinicius.meular.mods;

/** Grade espacial para achar o vértice mais próximo rapidamente. */
final class Grid {
    private final float[] p;
    private final float cell;
    private final int[] head;
    private final int[] next;
    private final int mask;

    Grid(float[] p, float cell) {
        this.p = p;
        this.cell = cell;
        int n = p.length / 3;
        int sz = 16;
        while (sz < n * 2) sz <<= 1;
        mask = sz - 1;
        head = new int[sz];
        java.util.Arrays.fill(head, -1);
        next = new int[n];
        for (int i = 0; i < n; i++) {
            int h = hash(fl(p[i * 3]), fl(p[i * 3 + 1]), fl(p[i * 3 + 2])) & mask;
            next[i] = head[h];
            head[h] = i;
        }
    }

    private int fl(float v) { return (int) Math.floor(v / cell); }

    private static int hash(int x, int y, int z) {
        int h = x * 73856093 ^ y * 19349663 ^ z * 83492791;
        return h ^ (h >>> 15);
    }

    /** Índice do ponto mais próximo dentro de [range] células (ou -1); a distância² sai em [d2]. */
    int nearest(float x, float y, float z, int range, float[] d2) {
        int cx = fl(x), cy = fl(y), cz = fl(z);
        int best = -1;
        float bd = Float.MAX_VALUE;
        for (int dx = -range; dx <= range; dx++) {
            for (int dy = -range; dy <= range; dy++) {
                for (int dz = -range; dz <= range; dz++) {
                    int i = head[hash(cx + dx, cy + dy, cz + dz) & mask];
                    while (i >= 0) {
                        float ex = p[i * 3] - x, ey = p[i * 3 + 1] - y, ez = p[i * 3 + 2] - z;
                        float d = ex * ex + ey * ey + ez * ez;
                        if (d < bd) { bd = d; best = i; }
                        i = next[i];
                    }
                }
            }
        }
        if (d2 != null) d2[0] = bd;
        return best;
    }

    /** Até [k] pontos mais próximos (do mais perto ao mais longe) dentro de [range] células, com filtro de lado (x) opcional. Retorna quantos achou. */
    int knn(float x, float y, float z, int range, int k, boolean sameSide, int[] oi, float[] od) {
        int cx = fl(x), cy = fl(y), cz = fl(z);
        int cnt = 0;
        for (int dx = -range; dx <= range; dx++) {
            for (int dy = -range; dy <= range; dy++) {
                for (int dz = -range; dz <= range; dz++) {
                    int i = head[hash(cx + dx, cy + dy, cz + dz) & mask];
                    while (i >= 0) {
                        float px = p[i * 3];
                        if (!sameSide || !(Math.abs(x) > 2.5f && Math.abs(px) > 1.0f && (x > 0) != (px > 0))) {
                            float ex = px - x, ey = p[i * 3 + 1] - y, ez = p[i * 3 + 2] - z;
                            float d = ex * ex + ey * ey + ez * ez;
                            if (cnt < k || d < od[cnt - 1]) {
                                int q = cnt < k ? cnt++ : k - 1;
                                while (q > 0 && od[q - 1] > d) { od[q] = od[q - 1]; oi[q] = oi[q - 1]; q--; }
                                od[q] = d;
                                oi[q] = i;
                            }
                        }
                        i = next[i];
                    }
                }
            }
        }
        return cnt;
    }
}
