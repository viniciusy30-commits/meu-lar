package com.vinicius.meular.sculpt;

import com.vinicius.meular.sculpt.Prims.Field;

/** Extrai uma superfície lisa e contínua de um campo de distância (surface nets, avaliação esparsa por blocos). */
public final class Mesher {
    private Mesher() {}

    /** Resultado: vértices (posição + normal suave) e triângulos indexados. */
    public static final class Out {
        public float[] p = new float[3 * 1024];
        public float[] n;
        public int nv;
        public int[] t = new int[3 * 1024];
        public int nt;

        int addV(float x, float y, float z) {
            if (nv * 3 + 3 > p.length) p = java.util.Arrays.copyOf(p, p.length * 2);
            p[nv * 3] = x; p[nv * 3 + 1] = y; p[nv * 3 + 2] = z;
            return nv++;
        }

        void addT(int a, int b, int c) {
            if (nt * 3 + 3 > t.length) t = java.util.Arrays.copyOf(t, t.length * 2);
            t[nt * 3] = a; t[nt * 3 + 1] = b; t[nt * 3 + 2] = c;
            nt++;
        }
    }

    private static final int B = 6;
    private static final int[][] EDGES = {
        {0, 1}, {2, 3}, {4, 5}, {6, 7},
        {0, 2}, {1, 3}, {4, 6}, {5, 7},
        {0, 4}, {1, 5}, {2, 6}, {3, 7}
    };

    public static Out run(Field f, float x0, float y0, float z0, float x1, float y1, float z1, float h) {
        final int nx = (int) Math.ceil((x1 - x0) / h) + 1;
        final int ny = (int) Math.ceil((y1 - y0) / h) + 1;
        final int nz = (int) Math.ceil((z1 - z0) / h) + 1;
        final float[] val = new float[nx * ny * nz];
        final boolean[] known = new boolean[nx * ny * nz];
        final int cx = nx - 1, cy = ny - 1, cz = nz - 1;
        final int[] cv = new int[cx * cy * cz];
        java.util.Arrays.fill(cv, -1);
        final Out o = new Out();

        final int bnx = (cx + B - 1) / B, bny = (cy + B - 1) / B, bnz = (cz + B - 1) / B;
        final boolean[] active = new boolean[bnx * bny * bnz];
        final float thr = 0.866f * B * h * 1.7f + h;
        for (int bk = 0; bk < bnz; bk++) for (int bj = 0; bj < bny; bj++) for (int bi = 0; bi < bnx; bi++) {
            float mx = x0 + (bi * B + B * 0.5f) * h, my = y0 + (bj * B + B * 0.5f) * h, mz = z0 + (bk * B + B * 0.5f) * h;
            active[(bk * bny + bj) * bnx + bi] = Math.abs(f.d(mx, my, mz)) <= thr;
        }

        final float[] cvv = new float[8];
        // vértices por célula
        for (int bk = 0; bk < bnz; bk++) for (int bj = 0; bj < bny; bj++) for (int bi = 0; bi < bnx; bi++) {
            if (!active[(bk * bny + bj) * bnx + bi]) continue;
            int i1 = Math.min((bi + 1) * B, cx), j1 = Math.min((bj + 1) * B, cy), k1 = Math.min((bk + 1) * B, cz);
            for (int k = bk * B; k < k1; k++) for (int j = bj * B; j < j1; j++) for (int i = bi * B; i < i1; i++) {
                int mask = 0;
                for (int c = 0; c < 8; c++) {
                    int ii = i + (c & 1), jj = j + ((c >> 1) & 1), kk = k + ((c >> 2) & 1);
                    int id = (kk * ny + jj) * nx + ii;
                    if (!known[id]) { val[id] = f.d(x0 + ii * h, y0 + jj * h, z0 + kk * h); known[id] = true; }
                    cvv[c] = val[id];
                    if (cvv[c] < 0f) mask |= 1 << c;
                }
                if (mask == 0 || mask == 255) continue;
                float sx = 0, sy = 0, sz = 0; int cnt = 0;
                for (int[] e : EDGES) {
                    float a = cvv[e[0]], b = cvv[e[1]];
                    if ((a < 0f) == (b < 0f)) continue;
                    float t = a / (a - b);
                    int ax = e[0] & 1, ay = (e[0] >> 1) & 1, az = (e[0] >> 2) & 1;
                    int bx = e[1] & 1, by = (e[1] >> 1) & 1, bz = (e[1] >> 2) & 1;
                    sx += ax + (bx - ax) * t; sy += ay + (by - ay) * t; sz += az + (bz - az) * t;
                    cnt++;
                }
                float inv = 1f / cnt;
                float px = x0 + (i + sx * inv) * h, py = y0 + (j + sy * inv) * h, pz = z0 + (k + sz * inv) * h;
                cv[(k * cy + j) * cx + i] = o.addV(px, py, pz);
            }
        }
        // faces: uma por aresta com troca de sinal
        for (int bk = 0; bk < bnz; bk++) for (int bj = 0; bj < bny; bj++) for (int bi = 0; bi < bnx; bi++) {
            if (!active[(bk * bny + bj) * bnx + bi]) continue;
            int i1 = Math.min((bi + 1) * B, nx), j1 = Math.min((bj + 1) * B, ny), k1 = Math.min((bk + 1) * B, nz);
            for (int k = bk * B; k < k1; k++) for (int j = bj * B; j < j1; j++) for (int i = bi * B; i < i1; i++) {
                int id = (k * ny + j) * nx + i;
                if (!known[id]) continue;
                boolean in0 = val[id] < 0f;
                if (i < cx && j >= 1 && k >= 1 && j < cy && k < cz) {
                    int id2 = id + 1;
                    if (known[id2] && (val[id2] < 0f) != in0)
                        quad(o, h, cv[((k - 1) * cy + (j - 1)) * cx + i], cv[((k - 1) * cy + j) * cx + i], cv[(k * cy + j) * cx + i], cv[(k * cy + (j - 1)) * cx + i], in0);
                }
                if (j < cy && i >= 1 && k >= 1 && i < cx && k < cz) {
                    int id2 = id + nx;
                    if (known[id2] && (val[id2] < 0f) != in0)
                        quad(o, h, cv[((k - 1) * cy + j) * cx + (i - 1)], cv[(k * cy + j) * cx + (i - 1)], cv[(k * cy + j) * cx + i], cv[((k - 1) * cy + j) * cx + i], in0);
                }
                if (k < cz && i >= 1 && j >= 1 && i < cx && j < cy) {
                    int id2 = id + nx * ny;
                    if (known[id2] && (val[id2] < 0f) != in0)
                        quad(o, h, cv[(k * cy + (j - 1)) * cx + (i - 1)], cv[(k * cy + (j - 1)) * cx + i], cv[(k * cy + j) * cx + i], cv[(k * cy + j) * cx + (i - 1)], in0);
                }
            }
        }
        normals(o);
        return o;
    }

    private static void quad(Out o, float h, int a, int b, int c, int d, boolean lowerInside) {
        if (a < 0 || b < 0 || c < 0 || d < 0) return;
        if (!lowerInside) { int t = a; a = d; d = t; t = b; b = c; c = t; } // inverte o sentido
        float acx = o.p[a * 3] - o.p[c * 3], acy = o.p[a * 3 + 1] - o.p[c * 3 + 1], acz = o.p[a * 3 + 2] - o.p[c * 3 + 2];
        float bdx = o.p[b * 3] - o.p[d * 3], bdy = o.p[b * 3 + 1] - o.p[d * 3 + 1], bdz = o.p[b * 3 + 2] - o.p[d * 3 + 2];
        if (acx * acx + acy * acy + acz * acz <= bdx * bdx + bdy * bdy + bdz * bdz) { o.addT(a, b, c); o.addT(a, c, d); }
        else { o.addT(a, b, d); o.addT(b, c, d); }
    }

    /** Normais suaves: média das normais das faces (ponderada pela área). */
    public static void normals(Out o) {
        o.n = new float[o.nv * 3];
        for (int i = 0; i < o.nt; i++) {
            int a = o.t[i * 3], b = o.t[i * 3 + 1], c = o.t[i * 3 + 2];
            float ux = o.p[b * 3] - o.p[a * 3], uy = o.p[b * 3 + 1] - o.p[a * 3 + 1], uz = o.p[b * 3 + 2] - o.p[a * 3 + 2];
            float vx = o.p[c * 3] - o.p[a * 3], vy = o.p[c * 3 + 1] - o.p[a * 3 + 1], vz = o.p[c * 3 + 2] - o.p[a * 3 + 2];
            float nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
            for (int q = 0; q < 3; q++) {
                int v = o.t[i * 3 + q];
                o.n[v * 3] += nx; o.n[v * 3 + 1] += ny; o.n[v * 3 + 2] += nz;
            }
        }
        for (int v = 0; v < o.nv; v++) {
            float x = o.n[v * 3], y = o.n[v * 3 + 1], z = o.n[v * 3 + 2];
            float l = (float) Math.sqrt(x * x + y * y + z * z);
            if (l < 1e-12f) { o.n[v * 3 + 1] = 1f; continue; }
            o.n[v * 3] = x / l; o.n[v * 3 + 1] = y / l; o.n[v * 3 + 2] = z / l;
        }
    }
}
