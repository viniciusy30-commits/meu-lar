package com.vinicius.meular.mods;

import java.util.HashMap;

/**
 * Camadas de roupa: calcula quanto cada vértice de uma peça de FORA precisa sair para ficar por cima de uma peça
 * de DENTRO sem atravessá-la (calça < camiseta < jaqueta). A direção do empurrão é a normal da superfície de dentro
 * (sempre consistente), não a normal da peça de fora (que em dobras/forros pode apontar para dentro).
 * Só empurra para fora; nunca puxa. O resultado é espalhado e suavizado na malha para não criar degraus.
 */
public final class Layers {
    private Layers() {}

    /**
     * @return deslocamento (x,y,z por vértice) a somar à posição de repouso da peça de fora; zeros se nada a fazer
     */
    public static float[] separate(float[] opos, int[] oidx,
                                   float[] ipos, float[] inor, int[] iidx,
                                   float gap, float maxPush, float radius) {
        final int onv = opos.length / 3;
        float[] vec = new float[onv * 3];
        if (ipos.length == 0 || iidx.length < 3 || onv == 0) return vec;
        final int inv = ipos.length / 3, itn = iidx.length / 3, ns = inv + itn;
        float[] sp = new float[ns * 3], sn = new float[ns * 3];
        System.arraycopy(ipos, 0, sp, 0, inv * 3);
        System.arraycopy(inor, 0, sn, 0, inv * 3);
        boolean[] used = new boolean[inv];
        for (int i = 0; i < iidx.length; i++) used[iidx[i]] = true;
        // vértices que nenhum triângulo usa (parte cortada) ficam longe, para nunca servirem de amostra
        for (int i = 0; i < inv; i++) if (!used[i]) { sp[i * 3] = sp[i * 3 + 1] = sp[i * 3 + 2] = 1e7f; }
        for (int t = 0; t < itn; t++) {
            int a = iidx[t * 3] * 3, b = iidx[t * 3 + 1] * 3, c = iidx[t * 3 + 2] * 3, o = (inv + t) * 3;
            for (int k = 0; k < 3; k++) sp[o + k] = (ipos[a + k] + ipos[b + k] + ipos[c + k]) / 3f;
            float nx = inor[a] + inor[b] + inor[c], ny = inor[a + 1] + inor[b + 1] + inor[c + 1], nz = inor[a + 2] + inor[b + 2] + inor[c + 2];
            float l = (float) Math.sqrt(nx * nx + ny * ny + nz * nz);
            if (l < 1e-6f) l = 1f;
            sn[o] = nx / l; sn[o + 1] = ny / l; sn[o + 2] = nz / l;
        }
        final float cell = radius;
        HashMap<Long, Integer> counts = new HashMap<>();
        for (int i = 0; i < ns; i++) if (sp[i * 3] < 1e6f) counts.merge(key(sp[i * 3], sp[i * 3 + 1], sp[i * 3 + 2], cell), 1, Integer::sum);
        HashMap<Long, int[]> grid = new HashMap<>();
        for (java.util.Map.Entry<Long, Integer> e : counts.entrySet()) grid.put(e.getKey(), new int[e.getValue() + 1]);
        for (int i = 0; i < ns; i++) {
            if (sp[i * 3] >= 1e6f) continue;
            int[] arr = grid.get(key(sp[i * 3], sp[i * 3 + 1], sp[i * 3 + 2], cell));
            arr[++arr[0]] = i;
        }
        // centro (x,z) da peça de dentro a cada 2 cm de altura: direção "para fora do corpo", estável mesmo onde a normal da malha é ruidosa
        float ymin = Float.MAX_VALUE, ymax = -Float.MAX_VALUE;
        for (int i = 0; i < inv; i++) if (used[i]) { ymin = Math.min(ymin, ipos[i * 3 + 1]); ymax = Math.max(ymax, ipos[i * 3 + 1]); }
        final float bin0 = ymin;
        final int nb = Math.max(1, (int) Math.ceil((ymax - ymin) / 2f) + 1);
        final float[] bcx = new float[nb], bcz = new float[nb]; int[] bn = new int[nb];
        for (int i = 0; i < inv; i++) {
            if (!used[i]) continue;
            int b = Math.min(nb - 1, (int) ((ipos[i * 3 + 1] - bin0) / 2f));
            bcx[b] += ipos[i * 3]; bcz[b] += ipos[i * 3 + 2]; bn[b]++;
        }
        for (int b = 0; b < nb; b++) if (bn[b] > 0) { bcx[b] /= bn[b]; bcz[b] /= bn[b]; } else { bcx[b] = Float.NaN; }
        final float r2 = radius * radius;
        float[] q = new float[4];   // nx, ny, nz, need
        float[] need = new float[onv * 3];
        for (int v = 0; v < onv; v++) {
            if (!needAt(grid, sp, sn, cell, r2, opos[v * 3], opos[v * 3 + 1], opos[v * 3 + 2], gap, q)) continue;
            blend(q, opos[v * 3], opos[v * 3 + 1], opos[v * 3 + 2], bin0, bcx, bcz);
            float m = Math.min(q[3], maxPush);
            need[v * 3] = q[0] * m; need[v * 3 + 1] = q[1] * m; need[v * 3 + 2] = q[2] * m;
        }
        // pontos dentro dos triângulos (centro e meio das arestas): triângulos grandes atravessam a peça de dentro com os vértices fora
        float[] pt = new float[3];
        for (int t = 0; t < oidx.length / 3; t++) {
            int a = oidx[t * 3] * 3, b = oidx[t * 3 + 1] * 3, c = oidx[t * 3 + 2] * 3;
            float bm = 0, bx = 0, by = 0, bz = 0;
            for (int s = 0; s < 4; s++) {
                for (int k = 0; k < 3; k++) {
                    pt[k] = s == 0 ? (opos[a + k] + opos[b + k] + opos[c + k]) / 3f
                          : s == 1 ? (opos[a + k] + opos[b + k]) / 2f
                          : s == 2 ? (opos[b + k] + opos[c + k]) / 2f
                          : (opos[a + k] + opos[c + k]) / 2f;
                }
                if (!needAt(grid, sp, sn, cell, r2, pt[0], pt[1], pt[2], gap, q)) continue;
                blend(q, pt[0], pt[1], pt[2], bin0, bcx, bcz);
                float m = Math.min(q[3], maxPush);
                if (m > bm) { bm = m; bx = q[0]; by = q[1]; bz = q[2]; }
            }
            if (bm <= 0) continue;
            int[] vs = {oidx[t * 3], oidx[t * 3 + 1], oidx[t * 3 + 2]};
            for (int v : vs) {
                float cur = len(need, v);
                if (bm > cur) { need[v * 3] = bx * bm; need[v * 3 + 1] = by * bm; need[v * 3 + 2] = bz * bm; }
            }
        }
        // espalha o empurrão pelo ESPAÇO (não só pela malha): peças soltas da mesma jaqueta (barra, forro, camisa) andam juntas, sem frestas entre elas
        float[] cur = need.clone(), nxt = new float[onv * 3];
        int onT = oidx.length / 3;
        float nyMin = Float.MAX_VALUE, nyMax = -Float.MAX_VALUE;
        for (int v = 0; v < onv; v++) if (sq(need, v) > 1e-6f) { nyMin = Math.min(nyMin, opos[v * 3 + 1]); nyMax = Math.max(nyMax, opos[v * 3 + 1]); }
        if (nyMin <= nyMax) {
            final float sr = 3.5f;
            HashMap<Long, Integer> oc = new HashMap<>();
            int[] act = new int[onv]; int na = 0;
            for (int v = 0; v < onv; v++) if (opos[v * 3 + 1] >= nyMin - 8f && opos[v * 3 + 1] <= nyMax + 8f) { act[na++] = v; oc.merge(key(opos[v * 3], opos[v * 3 + 1], opos[v * 3 + 2], sr), 1, Integer::sum); }
            HashMap<Long, int[]> og = new HashMap<>();
            for (java.util.Map.Entry<Long, Integer> e : oc.entrySet()) og.put(e.getKey(), new int[e.getValue() + 1]);
            for (int i = 0; i < na; i++) { int v = act[i]; int[] arr = og.get(key(opos[v * 3], opos[v * 3 + 1], opos[v * 3 + 2], sr)); arr[++arr[0]] = v; }
            final float sr2 = sr * sr;
            for (int it = 0; it < 14; it++) {
                System.arraycopy(cur, 0, nxt, 0, cur.length);
                for (int i = 0; i < na; i++) {
                    int v = act[i];
                    float x = opos[v * 3], y = opos[v * 3 + 1], z = opos[v * 3 + 2];
                    int cx = (int) Math.floor(x / sr), cy = (int) Math.floor(y / sr), cz = (int) Math.floor(z / sr);
                    float bx = nxt[v * 3], by = nxt[v * 3 + 1], bz = nxt[v * 3 + 2], bl = bx * bx + by * by + bz * bz;
                    for (int dx = -1; dx <= 1; dx++) for (int dy = -1; dy <= 1; dy++) for (int dz = -1; dz <= 1; dz++) {
                        int[] arr = og.get(pack(cx + dx, cy + dy, cz + dz));
                        if (arr == null) continue;
                        for (int k = 1; k <= arr[0]; k++) {
                            int u = arr[k];
                            float ex = opos[u * 3] - x, ey = opos[u * 3 + 1] - y, ez = opos[u * 3 + 2] - z;
                            if (ex * ex + ey * ey + ez * ez > sr2) continue;
                            final float dk = 0.94f; float fx = cur[u * 3] * dk, fy = cur[u * 3 + 1] * dk, fz = cur[u * 3 + 2] * dk;
                            float fl = fx * fx + fy * fy + fz * fz;
                            if (fl > bl) { bl = fl; bx = fx; by = fy; bz = fz; }
                        }
                    }
                    nxt[v * 3] = bx; nxt[v * 3 + 1] = by; nxt[v * 3 + 2] = bz;
                }
                float[] tmp = cur; cur = nxt; nxt = tmp;
            }
        }
        float[] sum = new float[onv * 3]; int[] deg = new int[onv];
        for (int pass = 0; pass < 2; pass++) {
            java.util.Arrays.fill(sum, 0f); java.util.Arrays.fill(deg, 0);
            for (int t = 0; t < onT; t++) {
                int[] vs = {oidx[t * 3], oidx[t * 3 + 1], oidx[t * 3 + 2]};
                for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++) if (i != j) {
                    for (int k = 0; k < 3; k++) sum[vs[i] * 3 + k] += cur[vs[j] * 3 + k];
                    deg[vs[i]]++;
                }
            }
            for (int v = 0; v < onv; v++) {
                if (deg[v] == 0) continue;
                float sx = 0.5f * cur[v * 3] + 0.5f * sum[v * 3] / deg[v];
                float sy = 0.5f * cur[v * 3 + 1] + 0.5f * sum[v * 3 + 1] / deg[v];
                float sz = 0.5f * cur[v * 3 + 2] + 0.5f * sum[v * 3 + 2] / deg[v];
                if (sx * sx + sy * sy + sz * sz >= sq(need, v)) { cur[v * 3] = sx; cur[v * 3 + 1] = sy; cur[v * 3 + 2] = sz; }
                else { cur[v * 3] = need[v * 3]; cur[v * 3 + 1] = need[v * 3 + 1]; cur[v * 3 + 2] = need[v * 3 + 2]; }
            }
        }
        // vértices na mesma posição (costuras de UV) andam juntos: sem frestas nas emendas
        HashMap<Long, float[]> weld = new HashMap<>();
        for (int v = 0; v < onv; v++) {
            long k = wkey(opos[v * 3], opos[v * 3 + 1], opos[v * 3 + 2]);
            float[] w = weld.get(k);
            if (w == null) { w = new float[4]; weld.put(k, w); }
            w[0] += cur[v * 3]; w[1] += cur[v * 3 + 1]; w[2] += cur[v * 3 + 2]; w[3] += 1f;
        }
        for (int v = 0; v < onv; v++) {
            float[] w = weld.get(wkey(opos[v * 3], opos[v * 3 + 1], opos[v * 3 + 2]));
            if (w[3] > 1f) { cur[v * 3] = w[0] / w[3]; cur[v * 3 + 1] = w[1] / w[3]; cur[v * 3 + 2] = w[2] / w[3]; }
        }
        for (int v = 0; v < onv; v++) {
            float l = len(cur, v);
            if (l > maxPush) { float k = maxPush / l; cur[v * 3] *= k; cur[v * 3 + 1] *= k; cur[v * 3 + 2] *= k; }
        }
        return cur;
    }

    /** Mistura a normal da peça de dentro com a direção radial (para fora do eixo do corpo) e ajusta o tamanho para ainda chegar na folga. */
    private static void blend(float[] q, float x, float y, float z, float bin0, float[] bcx, float[] bcz) {
        int b = (int) ((y - bin0) / 2f);
        if (b < 0) b = 0; if (b >= bcx.length) b = bcx.length - 1;
        float cx = bcx[b], cz = bcz[b];
        if (Float.isNaN(cx)) return;
        float rx = x - cx, rz = z - cz, rl = (float) Math.sqrt(rx * rx + rz * rz);
        if (rl < 1e-3f) return;
        rx /= rl; rz /= rl;
        float dx = q[0] + rx, dy = q[1], dz = q[2] + rz;
        float dl = (float) Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dl < 1e-3f) return;
        dx /= dl; dy /= dl; dz /= dl;
        float along = dx * q[0] + dy * q[1] + dz * q[2];   // quanto da nova direção anda na direção da normal de dentro
        if (along < 0.35f) return;                         // muito diferente: fica com a normal
        q[3] = q[3] / along;
        q[0] = dx; q[1] = dy; q[2] = dz;
    }

    private static void spread(float[] cur, float[] nxt, int from, int to) {
        float fx = cur[from * 3] * 0.82f, fy = cur[from * 3 + 1] * 0.82f, fz = cur[from * 3 + 2] * 0.82f;
        float f2 = fx * fx + fy * fy + fz * fz;
        if (f2 > sq(nxt, to)) { nxt[to * 3] = fx; nxt[to * 3 + 1] = fy; nxt[to * 3 + 2] = fz; }
    }

    private static float sq(float[] a, int v) { return a[v * 3] * a[v * 3] + a[v * 3 + 1] * a[v * 3 + 1] + a[v * 3 + 2] * a[v * 3 + 2]; }
    private static float len(float[] a, int v) { return (float) Math.sqrt(sq(a, v)); }

    /** q = {nx, ny, nz, quanto falta}; false se não há peça de dentro por perto ou se já há folga. */
    private static boolean needAt(HashMap<Long, int[]> grid, float[] sp, float[] sn, float cell, float r2,
                                  float x, float y, float z, float gap, float[] q) {
        int cx = (int) Math.floor(x / cell), cy = (int) Math.floor(y / cell), cz = (int) Math.floor(z / cell);
        float best = Float.MAX_VALUE; int bi = -1;
        for (int dx = -1; dx <= 1; dx++) for (int dy = -1; dy <= 1; dy++) for (int dz = -1; dz <= 1; dz++) {
            int[] arr = grid.get(pack(cx + dx, cy + dy, cz + dz));
            if (arr == null) continue;
            for (int k = 1; k <= arr[0]; k++) {
                int i = arr[k];
                float ex = x - sp[i * 3], ey = y - sp[i * 3 + 1], ez = z - sp[i * 3 + 2];
                float d2 = ex * ex + ey * ey + ez * ez;
                if (d2 < best) { best = d2; bi = i; }
            }
        }
        if (bi < 0 || best > r2) return false;
        float side = (x - sp[bi * 3]) * sn[bi * 3] + (y - sp[bi * 3 + 1]) * sn[bi * 3 + 1] + (z - sp[bi * 3 + 2]) * sn[bi * 3 + 2];
        float n = gap - side;
        if (n <= 0f) return false;
        q[0] = sn[bi * 3]; q[1] = sn[bi * 3 + 1]; q[2] = sn[bi * 3 + 2]; q[3] = n;
        return true;
    }

    /** Triângulos cujo centro fica em y <= cutY (a parte da peça de dentro que sobra à mostra por baixo da jaqueta). */
    public static int[] keepBelow(float[] pos, int[] idx, float cutY) {
        int n = idx.length / 3, k = 0;
        int[] out = new int[idx.length];
        for (int t = 0; t < n; t++) {
            float cy = (pos[idx[t * 3] * 3 + 1] + pos[idx[t * 3 + 1] * 3 + 1] + pos[idx[t * 3 + 2] * 3 + 1]) / 3f;
            if (cy > cutY) continue;
            out[k++] = idx[t * 3]; out[k++] = idx[t * 3 + 1]; out[k++] = idx[t * 3 + 2];
        }
        return java.util.Arrays.copyOf(out, k);
    }

    /** Triângulos cujo centro fica em y >= cutY (o que sobra da peça de fora depois de tirar a aba/barra que penduraria sobre a calça). */
    public static int[] keepAbove(float[] pos, int[] idx, float cutY) {
        int n = idx.length / 3, k = 0;
        int[] out = new int[idx.length];
        for (int t = 0; t < n; t++) {
            float cy = (pos[idx[t * 3] * 3 + 1] + pos[idx[t * 3 + 1] * 3 + 1] + pos[idx[t * 3 + 2] * 3 + 1]) / 3f;
            if (cy < cutY) continue;
            out[k++] = idx[t * 3]; out[k++] = idx[t * 3 + 1]; out[k++] = idx[t * 3 + 2];
        }
        return java.util.Arrays.copyOf(out, k);
    }

    private static long wkey(float x, float y, float z) {
        return pack(Math.round(x * 40f), Math.round(y * 40f), Math.round(z * 40f));
    }

    private static long key(float x, float y, float z, float cell) {
        return pack((int) Math.floor(x / cell), (int) Math.floor(y / cell), (int) Math.floor(z / cell));
    }

    private static long pack(int x, int y, int z) {
        return ((long) (x & 0x1FFFFF) << 42) | ((long) (y & 0x1FFFFF) << 21) | (long) (z & 0x1FFFFF);
    }
}
