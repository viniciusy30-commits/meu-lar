package com.vinicius.meular.mods;

import java.util.*;

/**
 * Conversor de roupas do The Sims 4 (CC de camiseta/short/jeans) para peças CUP1 do corpo am5/af5 do app.
 * Corrige: LOD errado, recorte por alfa que rasgava bordas, encaixe deslocado, textura de baixa resolução com borda preta.
 */
public final class Ts4Cloth {
    private Ts4Cloth() {}
    static final float HEM_BAND = 9f;
    /** Deslocamento acumulado das passadas de refinamento por vértice (a camiseta tem teto, para as mangas não abrirem). */
    private static float[] extra;
    static final float TOP_EXTRA_CAP = 1.1f;

    public static final class Out {
        public byte[] cup, png;
        public String slot;
        public int verts, tris, srcTris, pushed;
        public float maxPush, ymin, ymax;
        public int texW, texH;
        public final List<String> notes = new ArrayList<>();
    }

    /** [swatch]: índice do CASP/cor dentro do package (0 = primeira cor). [clear]: folga mínima (cm) entre tecido e pele. */
    public static Out convert(byte[] pkgBytes, BodyRef body, int swatch, float clear, int maxTex) throws Exception {
        Pkg pkg = new Pkg(pkgBytes);
        Out out = new Out();
        // ---- textura da cor escolhida
        List<Pkg.Ent> casps = pkg.ofType(0x034AEECB);
        if (casps.isEmpty()) throw new Exception("CASP ausente");
        byte[] casp = pkg.read(casps.get(Math.min(swatch, casps.size() - 1)));
        Img raw = null;
        for (Pkg.Ent e : pkg.ofType(Tex.T_RLE2)) if (refs(casp, e)) { raw = Tex.rle2(pkg.read(e)); break; }
        if (raw == null) for (Pkg.Ent e : pkg.ofType(Tex.T_IMG)) if (refs(casp, e)) { raw = Tex.dds(pkg.read(e)); break; }
        if (raw == null) throw new Exception("textura da cor " + swatch + " não encontrada");
        // ---- malha: o LOD mais detalhado (todos os LODs usam a mesma transformação)
        RawMesh m = null;
        for (Pkg.Ent e : pkg.ofType(Geom.T_GEOM)) {
            RawMesh c = Geom.parse(pkg.read(e), 4);
            if (m == null || c.nv() > m.nv()) m = c;
        }
        if (m == null || m.uv == null) throw new Exception("GEOM/UV ausente");
        final int nv0 = m.nv();
        // ---- só tecido: remove apenas triângulos CUJO CENTRO e VÉRTICES estão 100% em área transparente (casca de pele do TS4)
        int nt0 = m.nt();
        boolean[] keepT = new boolean[nt0];
        int kept = 0;
        for (int t = 0; t < nt0; t++) {
            int a = m.idx[t * 3], b = m.idx[t * 3 + 1], c = m.idx[t * 3 + 2];
            int op = 0, tot = 0;
            float[][] bs = {{1/3f,1/3f,1/3f},{.8f,.1f,.1f},{.1f,.8f,.1f},{.1f,.1f,.8f},{.5f,.5f,0f},{0f,.5f,.5f},{.5f,0f,.5f}};
            for (float[] w : bs) {
                float u = w[0]*m.uv[a*2] + w[1]*m.uv[b*2] + w[2]*m.uv[c*2];
                float v = w[0]*m.uv[a*2+1] + w[1]*m.uv[b*2+1] + w[2]*m.uv[c*2+1];
                int x = Math.max(0, Math.min(raw.w - 1, (int) (u * raw.w))), y = Math.max(0, Math.min(raw.h - 1, (int) (v * raw.h)));
                tot++; if ((raw.argb[y * raw.w + x] >>> 24) >= 128) op++;
            }
            keepT[t] = op * 2 >= tot;     // maioria opaca (no LOD0 é sempre 0% ou 100%)
            // triângulo degenerado
            float ax = m.pos[a*3], ay = m.pos[a*3+1], az = m.pos[a*3+2];
            float ux = m.pos[b*3]-ax, uy = m.pos[b*3+1]-ay, uz = m.pos[b*3+2]-az, vx = m.pos[c*3]-ax, vy = m.pos[c*3+1]-ay, vz = m.pos[c*3+2]-az;
            float cx = uy*vz-uz*vy, cy = uz*vx-ux*vz, cz = ux*vy-uy*vx;
            if (cx*cx+cy*cy+cz*cz < 1e-14f) keepT[t] = false;
            if (keepT[t]) kept++;
        }
        out.srcTris = nt0;
        if (kept < 20) throw new Exception("quase nenhum triângulo de tecido (" + kept + ")");
        // ---- compacta vértices
        int[] map = new int[nv0]; Arrays.fill(map, -1); int nv = 0;
        for (int t = 0; t < nt0; t++) if (keepT[t]) for (int k = 0; k < 3; k++) { int v = m.idx[t*3+k]; if (map[v] < 0) map[v] = nv++; }
        float[] pos = new float[nv*3], nor = new float[nv*3], uv = new float[nv*2];
        int[] idx = new int[kept*3];
        for (int v = 0; v < nv0; v++) if (map[v] >= 0) {
            int o = map[v];
            for (int k = 0; k < 3; k++) { pos[o*3+k] = m.pos[v*3+k] * body.s0; nor[o*3+k] = m.nor != null ? m.nor[v*3+k] : 0; }
            uv[o*2] = m.uv[v*2]; uv[o*2+1] = m.uv[v*2+1];
        }
        int q = 0; for (int t = 0; t < nt0; t++) if (keepT[t]) for (int k = 0; k < 3; k++) idx[q++] = map[m.idx[t*3+k]];
        if (m.nor == null) nor = Fit.computeNormals(pos, idx);
        // ---- encaixe: empurra para fora SÓ onde o tecido está dentro da pele, de forma suave (campo de deslocamento)
        pushOut(body, pos, idx, clear, out);
        float ymin = Float.MAX_VALUE, ymax = -Float.MAX_VALUE;
        for (int i = 0; i < nv; i++) { ymin = Math.min(ymin, pos[i*3+1]); ymax = Math.max(ymax, pos[i*3+1]); }
        out.ymin = ymin; out.ymax = ymax; out.slot = Fit.classify(ymin, ymax);
        // ---- pesos de osso
        int[] bi = new int[nv*4]; float[] bw = new float[nv*4];
        Fit.weights(body, pos, out.slot, bi, bw);
        if (!out.slot.equals("hat") && !out.slot.equals("hairBack")) Fit.cleanWeights(pos, idx, bi, bw, out.slot.equals("bottom"));
        // ---- textura recortada na região usada
        float u0 = 1, v0 = 1, u1 = 0, v1 = 0;
        for (int i = 0; i < nv; i++) { u0 = Math.min(u0, uv[i*2]); u1 = Math.max(u1, uv[i*2]); v0 = Math.min(v0, uv[i*2+1]); v1 = Math.max(v1, uv[i*2+1]); }
        float mu = 6f / raw.w, mv = 6f / raw.h;       // margem de 6 px
        u0 = Math.max(0, u0 - mu); u1 = Math.min(1, u1 + mu); v0 = Math.max(0, v0 - mv); v1 = Math.min(1, v1 + mv);
        int px0 = (int) Math.floor(u0 * raw.w), px1 = (int) Math.ceil(u1 * raw.w), py0 = (int) Math.floor(v0 * raw.h), py1 = (int) Math.ceil(v1 * raw.h);
        u0 = px0 / (float) raw.w; u1 = px1 / (float) raw.w; v0 = py0 / (float) raw.h; v1 = py1 / (float) raw.h;
        Img tex = crop(raw, px0, py0, px1, py1);
        tex = bleed(tex, 24);
        int tw = potFloor(Math.min(maxTex, tex.w)), th = potFloor(Math.min(maxTex, tex.h));
        tex = resize(tex, tw, th);
        for (int i = 0; i < nv; i++) { uv[i*2] = (uv[i*2] - u0) / (u1 - u0); uv[i*2+1] = (uv[i*2+1] - v0) / (v1 - v0); }
        out.texW = tw; out.texH = th;
        out.png = tex.opaque().png();
        out.cup = Fit.cup1(pos, nor, uv, idx, bi, bw);
        out.verts = nv; out.tris = kept;
        return out;
    }

    // ------------------------------------------------------------------ encaixe
    private static void pushOut(BodyRef b, float[] pos, int[] idx, float clear, Out out) {
        // várias passadas: a direção suavizada não garante a folga na primeira; repete até não haver penetração
        int total = 0; float mxAll = 0;
        extra = new float[pos.length / 3];
        for (int pass = 0; pass < 8; pass++) {
            Out o = new Out();
            pushOnce(b, pos, idx, clear, o, pass);
            total += o.pushed; mxAll = Math.max(mxAll, o.maxPush);
            if (o.pushed == 0 || o.maxPush < 0.03f) break;
        }
        out.pushed = total; out.maxPush = mxAll;
    }
    private static void pushOnce(BodyRef b, float[] pos, int[] idx, float clear, Out out, int pass) {
        // nas passadas de refinamento a barra da calça/short fica de fora: só a 1ª passada mexe nela (evita boca de sino)
        float yminAll = Float.MAX_VALUE, ymaxAll = -Float.MAX_VALUE;
        for (int i = 1; i < pos.length; i += 3) { yminAll = Math.min(yminAll, pos[i]); ymaxAll = Math.max(ymaxAll, pos[i]); }
        final float hemY = (pass > 0 && ymaxAll < 125f) ? yminAll + HEM_BAND : -Float.MAX_VALUE;
        int nv = pos.length / 3;
        float[] bp = b.pos, bn = b.nor; int[] bi = b.idx; int bt = bi.length / 3;
        // grade simples sobre os centros dos triângulos do corpo para limitar candidatos
        float cell = 6f;
        HashMap<Long, int[]> grid = new HashMap<>();
        HashMap<Long, ArrayList<Integer>> tmp = new HashMap<>();
        for (int t = 0; t < bt; t++) {
            int a = bi[t*3]*3, c = bi[t*3+1]*3, d = bi[t*3+2]*3;
            float x0 = Math.min(bp[a], Math.min(bp[c], bp[d])), x1 = Math.max(bp[a], Math.max(bp[c], bp[d]));
            float y0 = Math.min(bp[a+1], Math.min(bp[c+1], bp[d+1])), y1 = Math.max(bp[a+1], Math.max(bp[c+1], bp[d+1]));
            float z0 = Math.min(bp[a+2], Math.min(bp[c+2], bp[d+2])), z1 = Math.max(bp[a+2], Math.max(bp[c+2], bp[d+2]));
            for (int gx = (int) Math.floor(x0 / cell); gx <= (int) Math.floor(x1 / cell); gx++)
                for (int gy = (int) Math.floor(y0 / cell); gy <= (int) Math.floor(y1 / cell); gy++)
                    for (int gz = (int) Math.floor(z0 / cell); gz <= (int) Math.floor(z1 / cell); gz++)
                        tmp.computeIfAbsent(key(gx, gy, gz), k -> new ArrayList<>()).add(t);
        }
        for (Map.Entry<Long, ArrayList<Integer>> e : tmp.entrySet()) { int[] a = new int[e.getValue().size()]; for (int i = 0; i < a.length; i++) a[i] = e.getValue().get(i); grid.put(e.getKey(), a); }
        float[] req = new float[nv], dir = new float[nv*3], q = new float[6];
        int ntr = idx.length / 3, np = nv + ntr * 4;
        float[] sx = new float[np], sy = new float[np], sz = new float[np];
        for (int v = 0; v < nv; v++) { sx[v] = pos[v*3]; sy[v] = pos[v*3+1]; sz[v] = pos[v*3+2]; }
        for (int t = 0; t < ntr; t++) {
            int a = idx[t*3], c = idx[t*3+1], e = idx[t*3+2];
            int[][] pr = {{a,c,e},{a,c,c},{c,e,e},{e,a,a}};
            for (int k = 0; k < 4; k++) { int o = nv + t*4 + k; int[] z3 = pr[k];
                sx[o] = (pos[z3[0]*3] + pos[z3[1]*3] + pos[z3[2]*3]) / 3f; sy[o] = (pos[z3[0]*3+1] + pos[z3[1]*3+1] + pos[z3[2]*3+1]) / 3f; sz[o] = (pos[z3[0]*3+2] + pos[z3[1]*3+2] + pos[z3[2]*3+2]) / 3f; }
        }
        for (int v = 0; v < np; v++) {
            float x = sx[v], y = sy[v], z = sz[v];
            float best = Float.MAX_VALUE, sd = 0, nx = 0, ny = 1, nz = 0;
            // procura em anéis de células até achar candidato
            for (int r = 1; r <= 3 && best == Float.MAX_VALUE; r++) {
                int cx = (int) Math.floor(x / cell), cy = (int) Math.floor(y / cell), cz = (int) Math.floor(z / cell);
                for (int gx = cx - r; gx <= cx + r; gx++) for (int gy = cy - r; gy <= cy + r; gy++) for (int gz = cz - r; gz <= cz + r; gz++) {
                    int[] ts = grid.get(key(gx, gy, gz)); if (ts == null) continue;
                    for (int t : ts) {
                        int ia = bi[t*3]*3, ib = bi[t*3+1]*3, ic = bi[t*3+2]*3;
                        T3Geo.closest(x, y, z, bp[ia], bp[ia+1], bp[ia+2], bp[ib], bp[ib+1], bp[ib+2], bp[ic], bp[ic+1], bp[ic+2], q);
                        float dx = x - q[0], dy = y - q[1], dz = z - q[2], d2 = dx*dx + dy*dy + dz*dz;
                        if (d2 >= best) continue;
                        float tx = bn[ia]*q[3] + bn[ib]*q[4] + bn[ic]*q[5], ty = bn[ia+1]*q[3] + bn[ib+1]*q[4] + bn[ic+1]*q[5], tz = bn[ia+2]*q[3] + bn[ib+2]*q[4] + bn[ic+2]*q[5];
                        float nl = (float) Math.sqrt(tx*tx + ty*ty + tz*tz); if (nl < 1e-7f) continue;
                        tx /= nl; ty /= nl; tz /= nl;
                        best = d2; nx = tx; ny = ty; nz = tz;
                        sd = (float) Math.sqrt(d2) * (dx*tx + dy*ty + dz*tz < 0 ? -1f : 1f);
                    }
                }
            }
            float rq = best == Float.MAX_VALUE ? 0f : Math.max(0f, clear - sd);
            if (y < hemY) rq = 0f;
            if (v < nv) { dir[v*3] = nx; dir[v*3+1] = ny; dir[v*3+2] = nz; req[v] = rq; }
            else if (rq > 0f) {
                int t = (v - nv) / 4, k = (v - nv) % 4; int a = idx[t*3], c = idx[t*3+1], e = idx[t*3+2];
                int[] own = k == 0 ? new int[]{a,c,e} : k == 1 ? new int[]{a,c} : k == 2 ? new int[]{c,e} : new int[]{e,a};
                for (int u : own) if (rq * 1.15f > req[u]) { req[u] = rq * 1.15f; dir[u*3] = nx; dir[u*3+1] = ny; dir[u*3+2] = nz; }
            }
        }
        // vértices soldados por posição (costuras de UV não podem abrir)
        HashMap<String, Integer> wid = new HashMap<>(); int[] w = new int[nv]; int nw = 0;
        for (int v = 0; v < nv; v++) {
            String k = Math.round(pos[v*3]*200) + "," + Math.round(pos[v*3+1]*200) + "," + Math.round(pos[v*3+2]*200);
            Integer id = wid.get(k); if (id == null) { id = nw++; wid.put(k, id); } w[v] = id;
        }
        float[] wreq = new float[nw]; float[] wdir = new float[nw*3];
        for (int v = 0; v < nv; v++) if (req[v] >= wreq[w[v]]) { wreq[w[v]] = req[v]; for (int k = 0; k < 3; k++) wdir[w[v]*3+k] = dir[v*3+k]; }
        // adjacência soldada
        ArrayList<HashSet<Integer>> adj = new ArrayList<>(); for (int i = 0; i < nw; i++) adj.add(new HashSet<>());
        for (int t = 0; t < idx.length / 3; t++) for (int k = 0; k < 3; k++) { int a = w[idx[t*3+k]], c = w[idx[t*3+(k+1)%3]]; if (a != c) { adj.get(a).add(c); adj.get(c).add(a); } }
        float[] d = wreq.clone();
        for (int it = 0; it < 24; it++) {
            float[] nd = new float[nw];
            for (int i = 0; i < nw; i++) {
                float s = 0; for (int j : adj.get(i)) s += d[j];
                float avg = adj.get(i).isEmpty() ? d[i] : s / adj.get(i).size();
                nd[i] = Math.max(wreq[i], 0.5f * d[i] + 0.5f * avg * 0.97f);
            }
            d = nd;
        }
        // direção do vértice soldado: média das direções dos vértices que o compõem, ponderada pelo pedido
        float[] fin = new float[nv];
        int cnt = 0; float mx = 0;
        // direção suavizada: média da direção dos vizinhos com pedido
        float[] sdx = new float[nw*3];
        for (int i = 0; i < nw; i++) {
            float ax = wdir[i*3], ay = wdir[i*3+1], az = wdir[i*3+2]; float ws = wreq[i] > 0 ? 3f : 0f;
            ax *= ws; ay *= ws; az *= ws;
            for (int j : adj.get(i)) { float wj = wreq[j] > 0 ? 1f : 0.05f; ax += wdir[j*3]*wj; ay += wdir[j*3+1]*wj; az += wdir[j*3+2]*wj; }
            float l = (float) Math.sqrt(ax*ax + ay*ay + az*az);
            if (l < 1e-6f) { ax = wdir[i*3]; ay = wdir[i*3+1]; az = wdir[i*3+2]; l = 1f; }
            sdx[i*3] = ax / l; sdx[i*3+1] = ay / l; sdx[i*3+2] = az / l;
        }
        for (int v = 0; v < nv; v++) {
            float dd = d[w[v]];
            if (pass > 0 && ymaxAll >= 125f) dd = Math.min(dd, Math.max(0f, TOP_EXTRA_CAP - extra[v]));
            if (dd <= 0.02f) continue;
            if (pass > 0) extra[v] += dd;
            for (int k = 0; k < 3; k++) pos[v*3+k] += sdx[w[v]*3+k] * dd;
            cnt++; if (dd > mx) mx = dd;
        }
        out.pushed = cnt; out.maxPush = mx;
    }
    private static long key(int x, int y, int z) { return ((long) (x + 512) << 40) | ((long) (y + 512) << 20) | (long) (z + 512); }

    // ------------------------------------------------------------------ textura
    private static boolean refs(byte[] casp, Pkg.Ent e) {
        int[] v = {e.i1, e.i2, e.group, e.type};
        for (int p = 0; p <= casp.length - 16; p++) {
            boolean ok = true;
            for (int k = 0; k < 4 && ok; k++) { int q = p + k*4, x = v[k];
                if ((casp[q]&255)!=(x&255)||(casp[q+1]&255)!=((x>>>8)&255)||(casp[q+2]&255)!=((x>>>16)&255)||(casp[q+3]&255)!=((x>>>24)&255)) ok = false; }
            if (ok) return true;
        }
        return false;
    }
    static int potFloor(int n) { int p = 1; while (p * 2 <= n) p *= 2; return Math.max(8, p); }

    static Img crop(Img s, int x0, int y0, int x1, int y1) {
        Img o = new Img(x1 - x0, y1 - y0);
        for (int y = 0; y < o.h; y++) System.arraycopy(s.argb, (y + y0) * s.w + x0, o.argb, y * o.w, o.w);
        return o;
    }
    /** Preenche a área transparente com a cor vizinha mais próxima (a borda não "vaza" preto na filtragem/mipmap). */
    static Img bleed(Img s, int iters) {
        int w = s.w, h = s.h; int[] a = s.argb.clone(); boolean[] has = new boolean[w*h];
        for (int i = 0; i < a.length; i++) has[i] = (a[i] >>> 24) >= 128;
        long sr = 0, sg = 0, sb = 0, n = 0;
        for (int i = 0; i < a.length; i++) if (has[i]) { sr += (a[i]>>16)&255; sg += (a[i]>>8)&255; sb += a[i]&255; n++; }
        int mean = n == 0 ? 0x808080 : (int) (sr/n) << 16 | (int) (sg/n) << 8 | (int) (sb/n);
        for (int it = 0; it < iters; it++) {
            boolean[] nh = has.clone(); int[] na = a.clone();
            for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
                if (has[y*w+x]) continue;
                int r = 0, g = 0, b = 0, c = 0;
                for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) {
                    int xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= w || yy >= h || !has[yy*w+xx]) continue;
                    int p = a[yy*w+xx]; r += (p>>16)&255; g += (p>>8)&255; b += p&255; c++;
                }
                if (c > 0) { na[y*w+x] = 0xFF000000 | (r/c) << 16 | (g/c) << 8 | (b/c); nh[y*w+x] = true; }
            }
            a = na; has = nh;
        }
        for (int i = 0; i < a.length; i++) a[i] = has[i] ? (a[i] | 0xFF000000) : (0xFF000000 | mean);
        return new Img(w, h, a);
    }
    /** Redução por média de área (sem fundo preto: a imagem já foi preenchida). */
    static Img resize(Img s, int tw, int th) {
        if (tw == s.w && th == s.h) return s;
        Img o = new Img(tw, th);
        for (int y = 0; y < th; y++) {
            float sy0 = y * (float) s.h / th, sy1 = (y + 1) * (float) s.h / th;
            for (int x = 0; x < tw; x++) {
                float sx0 = x * (float) s.w / tw, sx1 = (x + 1) * (float) s.w / tw;
                double r = 0, g = 0, b = 0, ws = 0;
                for (int yy = (int) sy0; yy < Math.min(s.h, (int) Math.ceil(sy1)); yy++) {
                    double wy = Math.min(yy + 1, sy1) - Math.max(yy, sy0);
                    for (int xx = (int) sx0; xx < Math.min(s.w, (int) Math.ceil(sx1)); xx++) {
                        double wx = Math.min(xx + 1, sx1) - Math.max(xx, sx0), ww = wx * wy; int p = s.argb[yy*s.w+xx];
                        r += ww * ((p>>16)&255); g += ww * ((p>>8)&255); b += ww * (p&255); ws += ww;
                    }
                }
                o.argb[y*tw+x] = 0xFF000000 | ((int) Math.round(r/ws)) << 16 | ((int) Math.round(g/ws)) << 8 | (int) Math.round(b/ws);
            }
        }
        return o;
    }
}
