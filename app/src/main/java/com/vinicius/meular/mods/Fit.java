package com.vinicius.meular.mods;

/** Encaixa uma malha importada no corpo do app: eixos, escala, posição, braços (T -> A), pesos de osso e tipo de peça. */
final class Fit {
    private Fit() {}

    static final class Placed {
        float[] pos;
        float[] nor;
        double loss;
        float s, ty, tz;
        int mode;
        float ymin, ymax;
        String slot;
    }

    private static final float CAP2 = 100f;   // distância máxima considerada no erro (10 cm)

    // ------------------------------------------------------------------ eixos
    /** 0 = já é (x lateral, y para cima, z para a frente); 1 = Z para cima, frente +Y; 2 = Z para cima, frente -Y. */
    private static void axis(int mode, float[] src, float[] dst) {
        for (int i = 0; i < src.length; i += 3) {
            float x = src[i], y = src[i + 1], z = src[i + 2];
            switch (mode) {
                case 1: dst[i] = -x; dst[i + 1] = z; dst[i + 2] = y; break;
                case 2: dst[i] = x; dst[i + 1] = z; dst[i + 2] = -y; break;
                default: dst[i] = x; dst[i + 1] = y; dst[i + 2] = z;
            }
        }
    }

    static float[] computeNormals(float[] pos, int[] idx) {
        float[] n = new float[pos.length];
        for (int t = 0; t < idx.length; t += 3) {
            int a = idx[t] * 3, b = idx[t + 1] * 3, c = idx[t + 2] * 3;
            float ux = pos[b] - pos[a], uy = pos[b + 1] - pos[a + 1], uz = pos[b + 2] - pos[a + 2];
            float vx = pos[c] - pos[a], vy = pos[c + 1] - pos[a + 1], vz = pos[c + 2] - pos[a + 2];
            float nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
            for (int k : new int[]{a, b, c}) { n[k] += nx; n[k + 1] += ny; n[k + 2] += nz; }
        }
        norm(n);
        return n;
    }

    private static void norm(float[] n) {
        for (int i = 0; i < n.length; i += 3) {
            float l = (float) Math.sqrt(n[i] * n[i] + n[i + 1] * n[i + 1] + n[i + 2] * n[i + 2]);
            if (l > 1e-9f) { n[i] /= l; n[i + 1] /= l; n[i + 2] /= l; } else { n[i] = 0; n[i + 1] = 1; n[i + 2] = 0; }
        }
    }

    // ------------------------------------------------------------------ encaixe
    private static double loss(Grid g, float[] sx, float[] sy, float[] sz, int n, float s, float ty, float tz, float[] d2) {
        double acc = 0;
        for (int i = 0; i < n; i++) {
            int k = g.nearest(sx[i] * s, sy[i] * s + ty, sz[i] * s + tz, 1, d2);
            acc += (k < 0 || d2[0] > CAP2) ? CAP2 : d2[0];
        }
        return acc / n;
    }

    /** Erro rápido sem mexer na malha (já na escala/posição do app). */
    static double quickLoss(RawMesh m, BodyRef b, Grid g) {
        int nv = m.nv();
        int ns = Math.min(300, nv);
        float[] d2 = new float[1];
        double acc = 0;
        for (int i = 0; i < ns; i++) {
            int v = (int) ((long) i * nv / ns);
            int k = g.nearest(m.pos[v * 3] * b.s0, m.pos[v * 3 + 1] * b.s0, m.pos[v * 3 + 2] * b.s0, 1, d2);
            acc += (k < 0 || d2[0] > CAP2) ? CAP2 : d2[0];
        }
        return acc / ns;
    }

    static Grid bodyGrid(BodyRef b) { return new Grid(b.pos, 5f); }

    static Placed place(RawMesh m, BodyRef b, Grid g) throws Exception {
        int nv = m.nv();
        if (nv < 4 || m.nt() < 2) throw new Exception("Malha vazia");
        int game = m.game;
        int[] modes = game == 2 ? new int[]{1, 2} : new int[]{0};
        float s0 = game == 2 ? 100f : b.s0;
        double win = game == 3 ? 0.04 : game == 2 ? 0.15 : 0.35;
        double sStep = game == 3 ? 0.01 : game == 2 ? 0.025 : 0.05;
        float tyR = game == 3 ? 3f : game == 2 ? 16f : 20f, tyS = game == 3 ? 1.5f : game == 2 ? 4f : 5f;
        float tzR = game == 3 ? 3f : game == 2 ? 10.5f : 12f, tzS = game == 3 ? 1.5f : game == 2 ? 3.5f : 4f;

        float[] mp = new float[nv * 3];
        Placed best = null;
        float[] d2 = new float[1];
        for (int mode : modes) {
            axis(mode, m.pos, mp);
            // amostras (sem os braços esticados do Sims 2)
            int cap = 500;
            float[] sx = new float[cap], sy = new float[cap], sz = new float[cap];
            int ns = 0;
            int step = Math.max(1, nv / cap);
            for (int v = 0; v < nv && ns < cap; v += step) {
                if (game == 2 && Math.abs(mp[v * 3]) * 100f > 24f) continue;
                sx[ns] = mp[v * 3]; sy[ns] = mp[v * 3 + 1]; sz[ns] = mp[v * 3 + 2]; ns++;
            }
            if (ns < 30) {
                ns = 0;
                for (int v = 0; v < nv && ns < cap; v += step) { sx[ns] = mp[v * 3]; sy[ns] = mp[v * 3 + 1]; sz[ns] = mp[v * 3 + 2]; ns++; }
            }
            double bl = Double.MAX_VALUE;
            float bs = s0, bty = 0, btz = 0;
            for (double f = -win; f <= win + 1e-9; f += sStep) {
                float s = (float) (s0 * (1 + f));
                for (float ty = -tyR; ty <= tyR + 1e-3f; ty += tyS) {
                    for (float tz = -tzR; tz <= tzR + 1e-3f; tz += tzS) {
                        double l = loss(g, sx, sy, sz, ns, s, ty, tz, d2);
                        if (l < bl) { bl = l; bs = s; bty = ty; btz = tz; }
                    }
                }
            }
            // refina em volta do melhor
            float ds = (float) (s0 * sStep), dty = tyS, dtz = tzS;
            for (int it = 0; it < 2; it++) {
                float cs = bs, cty = bty, ctz = btz;
                for (int a = -2; a <= 2; a++) for (int c = -2; c <= 2; c++) for (int e = -2; e <= 2; e++) {
                    float s = cs + a * ds / 3f, ty = cty + c * dty / 3f, tz = ctz + e * dtz / 3f;
                    double l = loss(g, sx, sy, sz, ns, s, ty, tz, d2);
                    if (l < bl) { bl = l; bs = s; bty = ty; btz = tz; }
                }
                ds /= 3f; dty /= 3f; dtz /= 3f;
            }
            double lossAdj = (game == 2 && mode == 2) ? bl * 1.06 : bl;
            if (best == null || lossAdj < best.loss) {
                best = new Placed();
                best.loss = lossAdj;
                best.s = bs; best.ty = bty; best.tz = btz; best.mode = mode;
            }
        }
        // aplica a melhor transformação
        float[] pos = new float[nv * 3];
        float[] nor = m.nor != null ? m.nor.clone() : computeNormals(m.pos, m.idx);
        float[] tn = new float[nv * 3];
        axis(best.mode, m.pos, pos);
        axis(best.mode, nor, tn);
        for (int i = 0; i < nv; i++) {
            pos[i * 3] *= best.s;
            pos[i * 3 + 1] = pos[i * 3 + 1] * best.s + best.ty;
            pos[i * 3 + 2] = pos[i * 3 + 2] * best.s + best.tz;
        }
        if (game == 2) reposeArms(pos, tn, b, best.s);
        norm(tn);
        float ymin = Float.MAX_VALUE, ymax = -Float.MAX_VALUE;
        for (int i = 0; i < nv; i++) { ymin = Math.min(ymin, pos[i * 3 + 1]); ymax = Math.max(ymax, pos[i * 3 + 1]); }
        best.pos = pos;
        best.nor = tn;
        best.ymin = ymin;
        best.ymax = ymax;
        best.slot = classify(ymin, ymax);
        return best;
    }

    /** Sims 2: os braços vêm esticados em T; gira em volta do ombro até a pose A do corpo do app. */
    private static void reposeArms(float[] pos, float[] nor, BodyRef b, float s) {
        int nv = pos.length / 3;
        float maxX = 0;
        for (int i = 0; i < nv; i++) maxX = Math.max(maxX, Math.abs(pos[i * 3]));
        if (maxX < 0.5f * s) return;                       // sem braços esticados
        float phi;
        if (b.rig != null && b.rig.length >= 9) {
            phi = (float) Math.atan2(b.rig[1] - b.rig[7], b.rig[6] - b.rig[0]);   // ombro -> mão
            if (!(phi > 0.3f && phi < 1.3f)) phi = (float) (Math.PI / 4);
        } else phi = (float) (Math.PI / 4);
        double sy = 0;
        int cnt = 0;
        for (int i = 0; i < nv; i++) if (Math.abs(pos[i * 3]) > 0.5f * s) { sy += pos[i * 3 + 1]; cnt++; }
        float py = cnt > 0 ? (float) (sy / cnt) : 0.5f * 0f;
        float px = 0.19f * s, xa = 0.17f * s, xb = 0.26f * s;
        float cs = (float) Math.cos(phi), sn = (float) Math.sin(phi);
        for (int i = 0; i < nv; i++) {
            float x = pos[i * 3];
            float ax = Math.abs(x);
            if (ax <= xa) continue;
            float t = Math.min(1f, (ax - xa) / (xb - xa));
            float w = t * t * (3 - 2 * t);
            float dx = ax - px, dy = pos[i * 3 + 1] - py;
            float rx = dx * cs + dy * sn, ry = -dx * sn + dy * cs;
            float nx = px + rx, ny = py + ry;
            pos[i * 3] = Math.signum(x) * (ax + (nx - ax) * w);
            pos[i * 3 + 1] = pos[i * 3 + 1] + (ny - pos[i * 3 + 1]) * w;
            // normal
            float nax = nor[i * 3] * Math.signum(x), nay = nor[i * 3 + 1];
            float rnx = nax * cs + nay * sn, rny = -nax * sn + nay * cs;
            nor[i * 3] = Math.signum(x) * (nax + (rnx - nax) * w);
            nor[i * 3 + 1] = nay + (rny - nay) * w;
        }
    }

    // ------------------------------------------------------------------ tipo da peça
    static String classify(float ymin, float ymax) {
        if (ymax > 168f) return ymin < 135f ? "hairBack" : "hat";
        boolean legs = ymin < 60f, torso = ymax > 125f;
        if (legs && torso) return "overall";
        if (legs) return ymax < 45f ? "feet" : "bottom";
        return "top";
    }

    // ------------------------------------------------------------------ pesos de osso
    /** Copia os pesos dos vértices do corpo mais próximos (mesmo lado). Cabelo/chapéu seguem a cabeça. */
    static void weights(BodyRef b, float[] pos, String slot, int[] bi, float[] bw) {
        int nv = pos.length / 3;
        if (slot.equals("hat")) {
            for (int i = 0; i < nv; i++) { bi[i * 4] = 8; bw[i * 4] = 1f; }
            return;
        }
        if (slot.equals("hairBack")) {
            for (int i = 0; i < nv; i++) {
                float t = Math.max(0f, Math.min(1f, (150f - pos[i * 3 + 1]) / 10f));
                bi[i * 4] = 8; bi[i * 4 + 1] = 4; bw[i * 4] = 1f - t; bw[i * 4 + 1] = t;
            }
            return;
        }
        Grid g = new Grid(b.pos, 4f);
        int[] oi = new int[3];
        float[] od = new float[3];
        int[] tb = new int[16];
        float[] tw = new float[16];
        for (int v = 0; v < nv; v++) {
            float x = pos[v * 3], y = pos[v * 3 + 1], z = pos[v * 3 + 2];
            int c = 0;
            for (int range = 1; range <= 6 && c == 0; range += (range < 2 ? 1 : 2)) c = g.knn(x, y, z, range, 3, true, oi, od);
            if (c == 0) c = g.knn(x, y, z, 6, 3, false, oi, od);
            if (c == 0) { bi[v * 4] = 0; bw[v * 4] = 1f; continue; }
            int nb = 0;
            for (int k = 0; k < c; k++) {
                float wk = 1f / ((float) Math.sqrt(od[k]) + 0.8f);
                for (int j = 0; j < 4; j++) {
                    float w = b.bw[oi[k] * 4 + j];
                    if (w <= 0f) continue;
                    int bone = b.bi[oi[k] * 4 + j];
                    int q = 0;
                    while (q < nb && tb[q] != bone) q++;
                    if (q == nb) { if (nb >= 16) continue; tb[nb] = bone; tw[nb] = 0; nb++; }
                    tw[q] += w * wk;
                }
            }
            // 4 maiores
            for (int j = 0; j < 4; j++) {
                int bq = -1;
                for (int q = 0; q < nb; q++) if (tw[q] > 0 && (bq < 0 || tw[q] > tw[bq])) bq = q;
                if (bq < 0) { bi[v * 4 + j] = 0; bw[v * 4 + j] = 0; continue; }
                bi[v * 4 + j] = tb[bq]; bw[v * 4 + j] = tw[bq];
                tw[bq] = -tw[bq];
            }
            float sum = 0;
            for (int j = 0; j < 4; j++) sum += bw[v * 4 + j];
            if (sum <= 0) { bi[v * 4] = 0; bw[v * 4] = 1f; for (int j = 1; j < 4; j++) bw[v * 4 + j] = 0; }
            else for (int j = 0; j < 4; j++) bw[v * 4 + j] /= sum;
        }
    }

    // ------------------------------------------------------------------ arquivo CUP1
    /**
     * Limpa os pesos de osso copiados do corpo: vértice cujos pesos destoam dos vizinhos na malha da roupa
     * (ex.: barra da calça presa à coluna, ponta de manga presa ao tronco) recebe a média dos vizinhos; depois suaviza.
     * Sem isso, na animação esses vértices ficam para trás e esticam "pontas" de tecido.
     */
    static void cleanWeights(float[] pos, int[] idx, int[] bi, float[] bw, boolean legSplit) { cleanWeights(pos, idx, bi, bw, legSplit, null); }

    /** [legT]: por vértice 1 = perna direita, 0 = esquerda, -1 = sem perna (usa a posição x). Null = tudo pela posição x. */
    static void cleanWeights(float[] pos, int[] idx, int[] bi, float[] bw, boolean legSplit, float[] legT) {
        int nv = pos.length / 3;
        int[] w = new int[nv];
        java.util.HashMap<String, Integer> ids = new java.util.HashMap<>();
        for (int v = 0; v < nv; v++) {
            String k = Math.round(pos[v*3]*200) + "," + Math.round(pos[v*3+1]*200) + "," + Math.round(pos[v*3+2]*200);
            Integer id = ids.get(k); if (id == null) { id = ids.size(); ids.put(k, id); } w[v] = id;
        }
        int nw = ids.size(), NB = 64;
        float[][] W = new float[nw][NB];
        for (int v = 0; v < nv; v++) for (int k = 0; k < 4; k++) if (bw[v*4+k] > 0f) W[w[v]][bi[v*4+k] & 63] += bw[v*4+k];
        for (int i = 0; i < nw; i++) { float s = 0; for (float x : W[i]) s += x; if (s > 1e-9f) for (int b = 0; b < NB; b++) W[i][b] /= s; }
        java.util.ArrayList<java.util.TreeSet<Integer>> adj = new java.util.ArrayList<>();
        for (int i = 0; i < nw; i++) adj.add(new java.util.TreeSet<>());
        for (int t = 0; t < idx.length / 3; t++) {
            int a = w[idx[t*3]], b = w[idx[t*3+1]], c = w[idx[t*3+2]];
            adj.get(a).add(b); adj.get(a).add(c); adj.get(b).add(a); adj.get(b).add(c); adj.get(c).add(a); adj.get(c).add(b);
        }
        for (int i = 0; i < nw; i++) adj.get(i).remove(i);
        for (int round = 0; round < 4; round++) {
            float[][] N = new float[nw][]; int ch = 0;
            for (int i = 0; i < nw; i++) {
                N[i] = W[i];
                if (adj.get(i).isEmpty()) continue;
                float[] m = new float[NB];
                for (int j : adj.get(i)) for (int b = 0; b < NB; b++) m[b] += W[j][b];
                float d = 0; for (int b = 0; b < NB; b++) { m[b] /= adj.get(i).size(); d += Math.abs(W[i][b] - m[b]); }
                if (d > 0.6f) { N[i] = m; ch++; }
            }
            W = N;
            if (ch == 0) break;
        }
        for (int it = 0; it < 2; it++) {
            float[][] N = new float[nw][];
            for (int i = 0; i < nw; i++) {
                N[i] = W[i];
                if (adj.get(i).isEmpty()) continue;
                float[] m = new float[NB];
                for (int j : adj.get(i)) for (int b = 0; b < NB; b++) m[b] += W[j][b];
                float[] r = new float[NB];
                for (int b = 0; b < NB; b++) r[b] = 0.5f * W[i][b] + 0.5f * (m[b] / adj.get(i).size());
                N[i] = r;
            }
            W = N;
        }
        if (legSplit) {
            // cada perna só segue o próprio osso (direita x>0): sem isso a coxa que sobe atravessa o tecido da frente
            int[][] pairs = {{17, 21}, {18, 22}, {19, 23}, {20, 24}};
            float[] wx = new float[nw]; for (int v = 0; v < nv; v++) wx[w[v]] = pos[v*3];
            float[] wl = new float[nw]; java.util.Arrays.fill(wl, -1f);
            if (legT != null) for (int v = 0; v < nv; v++) if (legT[v] >= 0f) wl[w[v]] = legT[v];
            for (int i = 0; i < nw; i++) {
                // barra sobre o pé: dedos e pé seguem a canela (a barra não rasga em "pontas" quando o pé dobra na corrida)
                for (int[] fp : new int[][]{{20, 19}, {19, 18}, {24, 23}, {23, 22}}) { W[i][fp[1]] += W[i][fp[0]]; W[i][fp[0]] = 0f; }
                float t = wl[i] >= 0f ? wl[i] : Math.max(0f, Math.min(1f, (wx[i] + 1.5f) / 3f));
                for (int[] pr : pairs) { float tot = W[i][pr[0]] + W[i][pr[1]]; W[i][pr[0]] = tot * t; W[i][pr[1]] = tot * (1f - t); }
            }
        }
        for (int v = 0; v < nv; v++) {
            float[] row = W[w[v]].clone();
            float sum = 0;
            for (int j = 0; j < 4; j++) {
                int best = 0; for (int b = 1; b < NB; b++) if (row[b] > row[best]) best = b;
                bi[v*4+j] = best; bw[v*4+j] = row[best]; sum += row[best]; row[best] = -1f;
            }
            if (sum <= 1e-9f) { bi[v*4] = 0; bw[v*4] = 1f; for (int j = 1; j < 4; j++) bw[v*4+j] = 0f; }
            else for (int j = 0; j < 4; j++) bw[v*4+j] /= sum;
        }
    }

    static byte[] cup1(float[] pos, float[] nor, float[] uv, int[] idx, int[] bi, float[] bw) throws Exception {
        int nv = pos.length / 3, ni = idx.length;
        if (nv > 65535) throw new Exception("Malha pesada demais (" + nv + " vértices)");
        java.nio.ByteBuffer bb = java.nio.ByteBuffer.allocate(16 + nv * 44 + ni * 2).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        bb.put((byte) 'C').put((byte) 'U').put((byte) 'P').put((byte) '1');
        bb.putInt(nv).putInt(ni).putInt(0);
        for (int v = 0; v < nv; v++) {
            for (int k = 0; k < 3; k++) bb.putFloat(pos[v * 3 + k]);
            for (int k = 0; k < 3; k++) bb.putFloat(nor[v * 3 + k]);
            bb.putFloat(uv[v * 2]).putFloat(uv[v * 2 + 1]);
            bb.put((byte) 255).put((byte) 255).put((byte) 255).put((byte) 255);
            for (int k = 0; k < 4; k++) bb.put((byte) bi[v * 4 + k]);
            int[] q = new int[4];
            int sum = 0, big = 0;
            for (int k = 0; k < 4; k++) { q[k] = Math.round(bw[v * 4 + k] * 255f); sum += q[k]; if (bw[v * 4 + k] > bw[v * 4 + big]) big = k; }
            q[big] += 255 - sum;
            for (int k = 0; k < 4; k++) bb.put((byte) Math.max(0, Math.min(255, q[k])));
        }
        for (int i = 0; i < ni; i++) bb.putShort((short) idx[i]);
        return bb.array();
    }
}
