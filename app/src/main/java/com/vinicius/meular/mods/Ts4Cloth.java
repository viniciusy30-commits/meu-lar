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
        /** janela (fração da textura original) usada no recorte; as outras cores usam a mesma. */
        public float cu0, cv0, cu1, cv1;
        /** quantas cores (CASPs) o pacote tem. */
        public int swatches;
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
        // Etapa 112: sapatos são baixos (até 45 cm no espaço do app). A sola é horizontal,
        // mas não é uma "tampa de barra" de calça; preservar esses triângulos.
        float rawYmax = -Float.MAX_VALUE;
        for (int i = 1; i < m.pos.length; i += 3) rawYmax = Math.max(rawYmax, m.pos[i] * body.s0);
        final boolean shoeLike = rawYmax < 45f;
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
        // Tampas horizontais da barra de calça/short. Não remover a sola de sapatos.
        if (!shoeLike) {
            float yl = Float.MAX_VALUE, yh = -Float.MAX_VALUE;
            for (int t = 0; t < nt0; t++) if (keepT[t]) for (int k = 0; k < 3; k++) { float y = m.pos[m.idx[t*3+k]*3+1] * body.s0; yl = Math.min(yl, y); yh = Math.max(yh, y); }
            if (yh < 125f && yl < 70f) {
                int capped = 0;
                for (int t = 0; t < nt0; t++) {
                    if (!keepT[t]) continue;
                    int a = m.idx[t*3], b = m.idx[t*3+1], c = m.idx[t*3+2];
                    float ya = m.pos[a*3+1] * body.s0, yb = m.pos[b*3+1] * body.s0, yc = m.pos[c*3+1] * body.s0;
                    float ux = m.pos[b*3]-m.pos[a*3], uy = m.pos[b*3+1]-m.pos[a*3+1], uz = m.pos[b*3+2]-m.pos[a*3+2];
                    float vx = m.pos[c*3]-m.pos[a*3], vy = m.pos[c*3+1]-m.pos[a*3+1], vz = m.pos[c*3+2]-m.pos[a*3+2];
                    float nx = uy*vz-uz*vy, ny = uz*vx-ux*vz, nz = ux*vy-uy*vx, nl = (float) Math.sqrt(nx*nx+ny*ny+nz*nz);
                    if (nl < 1e-9f) continue;
                    float ymx = Math.max(ya, Math.max(yb, yc)), ymn = Math.min(ya, Math.min(yb, yc));
                    if (Math.abs(ny / nl) > 0.9f && ymx - ymn < 1.2f && ymn < yl + 3f) { keepT[t] = false; kept--; capped++; }
                }
                out.notes.add("tampas da barra removidas: " + capped);
            }
        } else {
            out.notes.add("sola preservada: peça classificada como sapato");
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
        float ymin = Float.MAX_VALUE, ymax = -Float.MAX_VALUE;
        for (int i = 0; i < nv; i++) { ymin = Math.min(ymin, pos[i*3+1]); ymax = Math.max(ymax, pos[i*3+1]); }
        // antes do encaixe: calça/short = peça que não chega ao tronco; camiseta = peça que não chega às pernas
        final boolean preBottom = !shoeLike && ymax < 125f && ymin < 70f, preTop = ymax > 125f && ymin > 60f;
        // ---- pernas: cada perna é um tubo separado (componente conexo abaixo da virilha)
        float[] legT = null;
        if (preBottom) {
            float[] cutOut = new float[1];
            legT = legLabels(pos, idx, cutOut);
            if (legT != null && ymin > 40f) {
                shrinkLegs(pos, legT, ymin, cutOut[0], SHORT_HEM_SCALE);
                out.notes.add("short: pernas estreitadas (barra x" + SHORT_HEM_SCALE + ")");
            }
            if (legT == null) out.notes.add("AVISO: não achei as duas pernas separadas; pesos por posição x");
        }
        pushOut(body, pos, idx, clear, out, shoeLike);
        if (preTop) { int pulled = collarPull(body, pos, idx, ymax, clear); out.notes.add("gola: " + pulled + " vértices puxados ao pescoço"); }
        ymin = Float.MAX_VALUE; ymax = -Float.MAX_VALUE;
        for (int i = 0; i < nv; i++) { ymin = Math.min(ymin, pos[i*3+1]); ymax = Math.max(ymax, pos[i*3+1]); }
        out.ymin = ymin; out.ymax = ymax; out.slot = Fit.classify(ymin, ymax);
        // ---- pesos de osso
        int[] bi = new int[nv*4]; float[] bw = new float[nv*4];
        Fit.weights(body, pos, out.slot, bi, bw);
        if (!out.slot.equals("hat") && !out.slot.equals("hairBack")) Fit.cleanWeights(pos, idx, bi, bw, out.slot.equals("bottom"), legT);
        // ---- textura recortada na região usada
        float u0 = 1, v0 = 1, u1 = 0, v1 = 0;
        for (int i = 0; i < nv; i++) { u0 = Math.min(u0, uv[i*2]); u1 = Math.max(u1, uv[i*2]); v0 = Math.min(v0, uv[i*2+1]); v1 = Math.max(v1, uv[i*2+1]); }
        float mu = 6f / raw.w, mv = 6f / raw.h;       // margem de 6 px
        u0 = Math.max(0, u0 - mu); u1 = Math.min(1, u1 + mu); v0 = Math.max(0, v0 - mv); v1 = Math.min(1, v1 + mv);
        int px0 = (int) Math.floor(u0 * raw.w), px1 = (int) Math.ceil(u1 * raw.w), py0 = (int) Math.floor(v0 * raw.h), py1 = (int) Math.ceil(v1 * raw.h);
        u0 = px0 / (float) raw.w; u1 = px1 / (float) raw.w; v0 = py0 / (float) raw.h; v1 = py1 / (float) raw.h;
        Img tex = crop(raw, px0, py0, px1, py1);
        tex = bleed(tex, 24);
        int tw = potFit(Math.min(maxTex, tex.w)), th = potFit(Math.min(maxTex, tex.h));
        tex = resize(tex, tw, th);
        for (int i = 0; i < nv; i++) { uv[i*2] = (uv[i*2] - u0) / (u1 - u0); uv[i*2+1] = (uv[i*2+1] - v0) / (v1 - v0); }
        out.texW = tw; out.texH = th; out.cu0 = u0; out.cv0 = v0; out.cu1 = u1; out.cv1 = v1; out.swatches = casps.size();
        out.png = tex.opaque().png();
        out.cup = Fit.cup1(pos, nor, uv, idx, bi, bw);
        out.verts = nv; out.tris = kept;
        return out;
    }


    // ------------------------------------------------------------------ pernas, gola e cores (Etapa 110)
    static final float SHORT_HEM_SCALE = 0.78f;

    /** Rótulo por vértice: 1 = perna direita (x maior), 0 = esquerda, -1 = acima da virilha. Null se não achar duas pernas. */
    static float[] legLabels(float[] pos, int[] idx, float[] cutOut) {
        int nv = pos.length / 3;
        HashMap<String, Integer> wid = new HashMap<>(); int[] w = new int[nv];
        for (int v = 0; v < nv; v++) {
            String k = Math.round(pos[v*3]*200) + "," + Math.round(pos[v*3+1]*200) + "," + Math.round(pos[v*3+2]*200);
            Integer id = wid.get(k); if (id == null) { id = wid.size(); wid.put(k, id); } w[v] = id;
        }
        int nw = wid.size();
        for (float cut = 92f; cut >= 56f; cut -= 2f) {
            int[] par = new int[nw]; for (int i = 0; i < nw; i++) par[i] = i;
            boolean[] used = new boolean[nw];
            for (int t = 0; t < idx.length / 3; t++) {
                int a = idx[t*3], b = idx[t*3+1], c = idx[t*3+2];
                if (Math.max(pos[a*3+1], Math.max(pos[b*3+1], pos[c*3+1])) >= cut) continue;
                int wa = w[a], wb = w[b], wc = w[c]; used[wa] = used[wb] = used[wc] = true;
                par[find(par, wa)] = find(par, wb); par[find(par, wb)] = find(par, wc);
            }
            HashMap<Integer, float[]> comp = new HashMap<>();   // raiz -> {n, soma x}
            for (int v = 0; v < nv; v++) if (used[w[v]]) { float[] c = comp.computeIfAbsent(find(par, w[v]), k -> new float[2]); c[0]++; c[1] += pos[v*3]; }
            ArrayList<Integer> big = new ArrayList<>();
            for (Map.Entry<Integer, float[]> e : comp.entrySet()) if (e.getValue()[0] >= 20) big.add(e.getKey());
            if (big.size() != 2) continue;
            float m0 = comp.get(big.get(0))[1] / comp.get(big.get(0))[0], m1 = comp.get(big.get(1))[1] / comp.get(big.get(1))[0];
            if (Math.abs(m0 - m1) < 6f) continue;
            int right = m0 > m1 ? big.get(0) : big.get(1);
            float[] t = new float[nv];
            for (int v = 0; v < nv; v++) t[v] = !used[w[v]] ? -1f : (find(par, w[v]) == right ? 1f : 0f);
            if (cutOut != null) cutOut[0] = cut;
            return t;
        }
        return null;
    }
    private static int find(int[] p, int a) { while (p[a] != a) { p[a] = p[p[a]]; a = p[a]; } return a; }

    /** Encolhe cada perna do short em torno do próprio eixo (a barra era ~2x a coxa: parecia saia e as pernas se tocavam). */
    static void shrinkLegs(float[] pos, float[] legT, float ymin, float cut, float hemScale) {
        int nv = pos.length / 3;
        for (int side = 0; side <= 1; side++) {
            float cs = 0, es = 0; int n = 0;
            for (int v = 0; v < nv; v++) if (legT[v] == side) { cs += pos[v*3]; es += pos[v*3+2]; n++; }
            if (n == 0) continue;
            // eixo por faixa de altura (a perna não é reta): média dos vértices da faixa de 3 cm
            for (int v = 0; v < nv; v++) {
                if (legT[v] != side) continue;
                float y = pos[v*3+1], sx = 0, sz = 0; int k = 0;
                for (int u = 0; u < nv; u++) if (legT[u] == side && Math.abs(pos[u*3+1] - y) < 3f) { sx += pos[u*3]; sz += pos[u*3+2]; k++; }
                float cx = sx / k, cz = sz / k;
                float t = Math.max(0f, Math.min(1f, (y - ymin) / Math.max(1f, cut - ymin)));
                t = t * t * (3f - 2f * t);
                float f = hemScale + (1f - hemScale) * t;
                pos[v*3] = cx + (pos[v*3] - cx) * f; pos[v*3+2] = cz + (pos[v*3+2] - cz) * f;
            }
        }
    }

    /** Gola: puxa para a pele do pescoço o tecido que ficou flutuando (só aproxima, nunca entra na pele). O deslocamento é suavizado na malha. */
    static int collarPull(BodyRef b, float[] pos, int[] idx, float ymax, float clear) {
        int nv = pos.length / 3, moved = 0; float[] q = new float[6];
        float[] bp = b.pos, bn = b.nor; int[] bi = b.idx;
        final float band = 6.5f;
        float[] d = new float[nv * 3];
        for (int v = 0; v < nv; v++) {
            float x = pos[v*3], y = pos[v*3+1], z = pos[v*3+2];
            if (y < ymax - band || Math.abs(x) > 12f) continue;
            float best = Float.MAX_VALUE, nx = 0, ny = 0, nz = 0, sd = 0;
            for (int t = 0; t < bi.length / 3; t++) {
                int ia = bi[t*3]*3, ib = bi[t*3+1]*3, ic = bi[t*3+2]*3;
                if (Math.min(bp[ia+1], Math.min(bp[ib+1], bp[ic+1])) > y + 6f || Math.max(bp[ia+1], Math.max(bp[ib+1], bp[ic+1])) < y - 6f) continue;
                T3Geo.closest(x, y, z, bp[ia], bp[ia+1], bp[ia+2], bp[ib], bp[ib+1], bp[ib+2], bp[ic], bp[ic+1], bp[ic+2], q);
                float dx = x - q[0], dy = y - q[1], dz = z - q[2], d2 = dx*dx + dy*dy + dz*dz;
                if (d2 >= best) continue;
                float tx = bn[ia]*q[3] + bn[ib]*q[4] + bn[ic]*q[5], ty = bn[ia+1]*q[3] + bn[ib+1]*q[4] + bn[ic+1]*q[5], tz = bn[ia+2]*q[3] + bn[ib+2]*q[4] + bn[ic+2]*q[5];
                float nl = (float) Math.sqrt(tx*tx + ty*ty + tz*tz); if (nl < 1e-7f) continue;
                best = d2; nx = tx / nl; ny = ty / nl; nz = tz / nl;
                sd = (float) Math.sqrt(d2) * (dx*nx + dy*ny + dz*nz < 0 ? -1f : 1f);
            }
            if (best == Float.MAX_VALUE || sd <= clear + 0.2f) continue;
            float k = Math.min(sd - clear, 3.5f);
            float wy = Math.max(0f, Math.min(1f, (y - (ymax - band)) / 3.5f)); wy = wy * wy * (3f - 2f * wy);
            d[v*3] = -nx * k * wy; d[v*3+1] = -ny * k * wy; d[v*3+2] = -nz * k * wy;
        }
        // soldagem por posição + suavização do deslocamento entre vizinhos
        HashMap<String, Integer> wid = new HashMap<>(); int[] w = new int[nv];
        for (int v = 0; v < nv; v++) {
            String key = Math.round(pos[v*3]*200) + "," + Math.round(pos[v*3+1]*200) + "," + Math.round(pos[v*3+2]*200);
            Integer id = wid.get(key); if (id == null) { id = wid.size(); wid.put(key, id); } w[v] = id;
        }
        int nw = wid.size(); float[] wd = new float[nw * 3]; boolean[] inBand = new boolean[nw];
        for (int v = 0; v < nv; v++) { for (int k = 0; k < 3; k++) wd[w[v]*3+k] = d[v*3+k]; if (pos[v*3+1] >= ymax - band) inBand[w[v]] = true; }
        ArrayList<HashSet<Integer>> adj = new ArrayList<>(); for (int i = 0; i < nw; i++) adj.add(new HashSet<>());
        for (int t = 0; t < idx.length / 3; t++) for (int k = 0; k < 3; k++) { int a2 = w[idx[t*3+k]], c2 = w[idx[t*3+(k+1)%3]]; if (a2 != c2) { adj.get(a2).add(c2); adj.get(c2).add(a2); } }
        for (int it = 0; it < 8; it++) {
            float[] nd = wd.clone();
            for (int i = 0; i < nw; i++) {
                if (!inBand[i] || adj.get(i).isEmpty()) continue;
                for (int k = 0; k < 3; k++) { float sum = 0; for (int j : adj.get(i)) sum += wd[j*3+k]; nd[i*3+k] = 0.4f * wd[i*3+k] + 0.6f * sum / adj.get(i).size(); }
            }
            wd = nd;
        }
        for (int v = 0; v < nv; v++) {
            float dx = wd[w[v]*3], dy = wd[w[v]*3+1], dz = wd[w[v]*3+2];
            if (dx*dx + dy*dy + dz*dz < 1e-6f) continue;
            pos[v*3] += dx; pos[v*3+1] += dy; pos[v*3+2] += dz; moved++;
        }
        return moved;
    }

    /** Textura de outra cor do mesmo pacote, com o mesmo recorte e tamanho da malha convertida. [avg] recebe a cor média (RGB). */
    public static Img colorTexture(byte[] pkgBytes, int swatch, Out ref, int[] avg) throws Exception {
        Pkg pkg = new Pkg(pkgBytes);
        List<Pkg.Ent> casps = pkg.ofType(0x034AEECB);
        byte[] casp = pkg.read(casps.get(Math.min(swatch, casps.size() - 1)));
        Img raw = null;
        for (Pkg.Ent e : pkg.ofType(Tex.T_RLE2)) if (refs(casp, e)) { raw = Tex.rle2(pkg.read(e)); break; }
        if (raw == null) for (Pkg.Ent e : pkg.ofType(Tex.T_IMG)) if (refs(casp, e)) { raw = Tex.dds(pkg.read(e)); break; }
        if (raw == null) throw new Exception("textura da cor " + swatch + " não encontrada");
        int px0 = Math.round(ref.cu0 * raw.w), px1 = Math.round(ref.cu1 * raw.w), py0 = Math.round(ref.cv0 * raw.h), py1 = Math.round(ref.cv1 * raw.h);
        Img tex = crop(raw, px0, py0, px1, py1);
        long sr = 0, sg = 0, sb = 0, n = 0;
        for (int p : tex.argb) if ((p >>> 24) >= 128) { sr += (p >> 16) & 255; sg += (p >> 8) & 255; sb += p & 255; n++; }
        if (avg != null) avg[0] = n == 0 ? 0x808080 : (int) (sr / n) << 16 | (int) (sg / n) << 8 | (int) (sb / n);
        tex = bleed(tex, 24);
        return resize(tex, ref.texW, ref.texH).opaque();
    }

    // ------------------------------------------------------------------ encaixe
    private static void pushOut(BodyRef b, float[] pos, int[] idx, float clear, Out out, boolean shoeLike) {
        // várias passadas: a direção suavizada não garante a folga na primeira; repete até não haver penetração
        int total = 0; float mxAll = 0;
        extra = new float[pos.length / 3];
        for (int pass = 0; pass < 8; pass++) {
            Out o = new Out();
            pushOnce(b, pos, idx, clear, o, pass, shoeLike);
            total += o.pushed; mxAll = Math.max(mxAll, o.maxPush);
            if (o.pushed == 0 || o.maxPush < 0.03f) break;
        }
        out.pushed = total; out.maxPush = mxAll;
    }
    private static void pushOnce(BodyRef b, float[] pos, int[] idx, float clear, Out out, int pass, boolean shoeLike) {
        // nas passadas de refinamento a barra da calça/short fica de fora: só a 1ª passada mexe nela (evita boca de sino)
        float yminAll = Float.MAX_VALUE, ymaxAll = -Float.MAX_VALUE;
        for (int i = 1; i < pos.length; i += 3) { yminAll = Math.min(yminAll, pos[i]); ymaxAll = Math.max(ymaxAll, pos[i]); }
        final float hemY = (pass > 0 && ymaxAll < 125f && !shoeLike) ? yminAll + HEM_BAND : -Float.MAX_VALUE;
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
    /** Potência de 2 mais próxima por cima quando o recorte já passa de 1,3x a de baixo (não joga fora resolução à toa). */
    static int potFit(int n) { int p = potFloor(n); return n > p * 1.3f ? p * 2 : p; }
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
