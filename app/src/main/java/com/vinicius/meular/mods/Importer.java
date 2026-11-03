package com.vinicius.meular.mods;

import java.util.ArrayList;
import java.util.List;

/** Converte um .package do The Sims 2, 3 ou 4 em peças do jogo (malha CUP1 + textura PNG). */
public final class Importer {
    private Importer() {}

    public static final class PieceOut {
        public String name;
        public String slot;        // top, bottom, overall, feet, hairBack, hat
        public byte[] cup;         // arquivo CUP1
        public byte[] png;         // textura (PNG)
        public boolean hasTex;
        public boolean alpha;      // textura com recorte (cabelo)
        public int game;
        public int verts;
        public double fit;         // erro médio² do encaixe (cm²), só informativo
    }

    public static final class Out {
        public final List<PieceOut> pieces = new ArrayList<>();
        public Img texOnly;        // package só com textura
        public String texName = "";
        public final List<String> notes = new ArrayList<>();
    }

    public static Out convert(byte[] data, String fileName, BodyRef body) throws Exception {
        Pkg pkg = new Pkg(data);
        int game = pkg.game();
        Out out = new Out();
        String base = cleanName(fileName);
        List<RawMesh> meshes = new ArrayList<>();
        Img tex = null;
        try {
            tex = pickTexture(pkg, game);
        } catch (Exception e) {
            out.notes.add("Textura não lida: " + e.getMessage());
        }
        if (game == 2) {
            for (Pkg.Ent e : pkg.ofType(Gmdc.T_GMDC)) {
                List<RawMesh> gs = Gmdc.parse(pkg.read(e));
                RawMesh all = merge(gs);
                if (all != null) { all.name = base; meshes.add(all); }
            }
        } else {
            List<Pkg.Ent> ge = pkg.ofType(Geom.T_GEOM);
            List<RawMesh> cand = new ArrayList<>();
            int bad = 0, small = 0;
            String firstErr = "";
            for (Pkg.Ent e : ge) {
                try {
                    RawMesh m = Geom.parse(pkg.read(e), game);
                    if (m.nv() >= 100 && m.nv() <= 60000 && m.nt() > 20) cand.add(m);
                    else small++;
                } catch (Exception ex) {
                    bad++;
                    if (firstErr.isEmpty()) firstErr = String.valueOf(ex.getMessage());
                }
            }
            if (cand.isEmpty()) {
                java.util.TreeMap<String, Integer> hist = new java.util.TreeMap<>();
                for (Pkg.Ent e : pkg.ents) hist.merge(Integer.toHexString(e.type), 1, Integer::sum);
                out.notes.add("Sims " + game + " (DBPF " + pkg.major + "." + pkg.minor + "): " + ge.size() + " malha(s) GEOM, " + bad + " com erro"
                        + (firstErr.isEmpty() ? "" : " (" + firstErr + ")") + ", " + small + " fora do tamanho. Tipos no arquivo: " + hist);
            }
            if (cand.size() > 14) {
                cand.sort((a, c) -> c.nv() - a.nv());
                cand = new ArrayList<>(cand.subList(0, 14));
            }
            if (!cand.isEmpty()) {
                Grid g = Fit.bodyGrid(body);
                RawMesh bestM = null;
                double bl = Double.MAX_VALUE;
                List<double[]> ls = new ArrayList<>();
                List<RawMesh> ok = new ArrayList<>();
                for (RawMesh m : cand) {
                    try {
                        Fit.Placed p = Fit.place(m, body, g);
                        ls.add(new double[]{p.loss});
                        ok.add(m);
                        if (p.loss < bl) bl = p.loss;
                    } catch (Exception ex) { /* ignora */ }
                }
                // entre as de erro parecido, a mais detalhada (LOD 0)
                for (int i = 0; i < ok.size(); i++) {
                    if (ls.get(i)[0] <= bl * 1.25 + 0.5 && (bestM == null || ok.get(i).nv() > bestM.nv())) bestM = ok.get(i);
                }
                if (bestM != null) { bestM.name = base; meshes.add(bestM); }
            }
        }
        if (meshes.isEmpty()) {
            String dae = baseMeshName(pkg);
            if (!dae.isEmpty()) out.notes.add(0, "Esse package é uma COR (recolor) do modelo \"" + dae + "\" do próprio jogo da EA; a malha não vem no arquivo, então não dá para montar a roupa só com ele. Use packages que tragam a malha junto.");
            if (tex != null) {
                out.texOnly = tex.limit(1024).pot();
                out.texName = base;
                out.notes.add("Package só com textura.");
                return out;
            }
            throw new Exception("Esse package não tem malha (roupa/cabelo) nem textura que eu consiga ler"
                    + (game == 2 ? "." : " (procurei GEOM)."));
        }
        Grid g = Fit.bodyGrid(body);
        int n = 0;
        for (RawMesh m : meshes) {
            Fit.Placed p = Fit.place(m, body, g);
            int nv = m.nv();
            float[] uv = new float[nv * 2];
            for (int i = 0; i < nv; i++) {
                float u = m.uv != null ? m.uv[i * 2] : 0f, v = m.uv != null ? m.uv[i * 2 + 1] : 0f;
                uv[i * 2] = u;
                uv[i * 2 + 1] = v;   // Sims 2, 3 e 4: v já cresce de cima para baixo (conferido pela altura x v)
            }
            int[] bi = new int[nv * 4];
            float[] bw = new float[nv * 4];
            Fit.weights(body, p.pos, p.slot, bi, bw);
            PieceOut po = new PieceOut();
            po.name = meshes.size() > 1 ? base + " " + (++n) : base;
            po.slot = p.slot;
            po.game = game;
            po.verts = nv;
            po.fit = p.loss;
            po.cup = Fit.cup1(p.pos, p.nor, uv, m.idx, bi, bw);
            Img t = tex;
            if (t != null && t.meanLuma() < 12) {
                out.notes.add("A textura veio quase toda preta; ignorei (provável leitura errada).");
                t = null;
            }
            if (t != null) {
                t = t.limit(1024).pot();
                po.alpha = (p.slot.equals("hairBack") || p.slot.equals("hat")) && t.hasAlpha();
                if (!po.alpha) t = t.opaque();
                po.png = t.png();
                po.hasTex = true;
            } else {
                po.png = Img.solid(8, 8, 0xFFB9BDC4).png();
                po.hasTex = false;
                out.notes.add("Sem textura: a peça entrou cinza. Importe também o package de cor (recolor).");
            }
            out.pieces.add(po);
        }
        return out;
    }

    // ------------------------------------------------------------------ Sims 2: áreas de pele
    /**
     * As malhas do Sims 2 trazem antebraços, mãos, pescoço e canelas; na textura essas áreas são pretas (o jogo original pinta a pele por cima).
     * Tira os triângulos cujos 3 vértices caem em pixels pretos para a pele do corpo do app aparecer. Devolve o CUP1 novo.
     */
    public static byte[] cullBlack(byte[] cup, int[] argb, int w, int h) {
        try {
            java.nio.ByteBuffer b = java.nio.ByteBuffer.wrap(cup).order(java.nio.ByteOrder.LITTLE_ENDIAN);
            b.position(4);
            int nv = b.getInt(), ni = b.getInt();
            b.getInt();
            int vo = 16, io = 16 + nv * 44;
            boolean[] dark = new boolean[nv];
            for (int v = 0; v < nv; v++) {
                float u = b.getFloat(vo + v * 44 + 24), t = b.getFloat(vo + v * 44 + 28);
                int x = Math.max(0, Math.min(w - 1, (int) (u * w))), y = Math.max(0, Math.min(h - 1, (int) (t * h)));
                int c = argb[y * w + x];
                int sum = ((c >> 16) & 255) + ((c >> 8) & 255) + (c & 255);
                if (sum < 20) { dark[v] = true; continue; }
                if (sum >= 150) continue;
                // escuro e achatado (bloco sem detalhe): é a área de pele, não tecido
                int mn = 255, mx = 0;
                for (int dy = -3; dy <= 3; dy++) {
                    for (int dx = -3; dx <= 3; dx++) {
                        int xx = Math.max(0, Math.min(w - 1, x + dx)), yy = Math.max(0, Math.min(h - 1, y + dy));
                        int q = argb[yy * w + xx];
                        int l = (((q >> 16) & 255) + ((q >> 8) & 255) + (q & 255)) / 3;
                        mn = Math.min(mn, l); mx = Math.max(mx, l);
                    }
                }
                dark[v] = mx - mn <= 12;
            }
            int nt = ni / 3;
            boolean[] keepT = new boolean[nt];
            int kept = 0;
            for (int t = 0; t < nt; t++) {
                int a = b.getShort(io + t * 6) & 0xFFFF, c1 = b.getShort(io + t * 6 + 2) & 0xFFFF, c2 = b.getShort(io + t * 6 + 4) & 0xFFFF;
                keepT[t] = !(dark[a] && dark[c1] && dark[c2]);
                if (keepT[t]) kept++;
            }
            if (kept == nt || kept < nt * 0.15) return cup;
            int[] map = new int[nv];
            java.util.Arrays.fill(map, -1);
            int nn = 0;
            for (int t = 0; t < nt; t++) {
                if (!keepT[t]) continue;
                for (int k = 0; k < 3; k++) {
                    int v = b.getShort(io + t * 6 + k * 2) & 0xFFFF;
                    if (map[v] < 0) map[v] = nn++;
                }
            }
            java.nio.ByteBuffer o = java.nio.ByteBuffer.allocate(16 + nn * 44 + kept * 6).order(java.nio.ByteOrder.LITTLE_ENDIAN);
            o.put(cup, 0, 4);
            o.putInt(nn).putInt(kept * 3).putInt(0);
            byte[] vv = new byte[nn * 44];
            for (int v = 0; v < nv; v++) if (map[v] >= 0) System.arraycopy(cup, vo + v * 44, vv, map[v] * 44, 44);
            o.put(vv);
            for (int t = 0; t < nt; t++) {
                if (!keepT[t]) continue;
                for (int k = 0; k < 3; k++) o.putShort((short) map[b.getShort(io + t * 6 + k * 2) & 0xFFFF]);
            }
            return o.array();
        } catch (RuntimeException e) {
            return cup;
        }
    }

    /** Sims 3: nome do modelo (daeFileName) que o CASP do recolor usa; vazio se não achar. */
    private static String baseMeshName(Pkg pkg) {
        try {
            for (Pkg.Ent e : pkg.ofType(0x034AEECB)) {
                byte[] b = pkg.read(e);
                String t = new String(b, java.nio.charset.StandardCharsets.UTF_16LE);
                java.util.regex.Matcher m = java.util.regex.Pattern.compile("daeFileName\"\\s+value=\"([^\"]+)\"").matcher(t);
                if (m.find()) return m.group(1);
                t = new String(b, java.nio.charset.StandardCharsets.ISO_8859_1);
                m = java.util.regex.Pattern.compile("daeFileName\"\\s+value=\"([^\"]+)\"").matcher(t);
                if (m.find()) return m.group(1);
            }
        } catch (Exception e) { /* ignora */ }
        return "";
    }

    // ------------------------------------------------------------------ auxiliares
    private static RawMesh merge(List<RawMesh> gs) {
        if (gs.isEmpty()) return null;
        if (gs.size() == 1) return gs.get(0);
        int nv = 0, ni = 0;
        for (RawMesh m : gs) { nv += m.nv(); ni += m.idx.length; }
        RawMesh r = new RawMesh();
        r.game = gs.get(0).game;
        r.pos = new float[nv * 3];
        r.nor = new float[nv * 3];
        r.uv = new float[nv * 2];
        r.idx = new int[ni];
        int vo = 0, io = 0;
        for (RawMesh m : gs) {
            System.arraycopy(m.pos, 0, r.pos, vo * 3, m.pos.length);
            float[] nn = m.nor != null ? m.nor : Fit.computeNormals(m.pos, m.idx);
            System.arraycopy(nn, 0, r.nor, vo * 3, nn.length);
            if (m.uv != null) System.arraycopy(m.uv, 0, r.uv, vo * 2, m.uv.length);
            for (int i = 0; i < m.idx.length; i++) r.idx[io + i] = m.idx[i] + vo;
            vo += m.nv();
            io += m.idx.length;
        }
        return r;
    }

    private static Img pickTexture(Pkg pkg, int game) throws Exception {
        if (game == 2) {
            Img best = null;
            int bestScore = -1;
            for (Pkg.Ent e : pkg.ofType(Tex.T_TXTR)) {
                byte[] b = pkg.read(e);
                String nm = Tex.sims2Name(b).toLowerCase();
                int sc = nm.contains("basetexture") ? 3 : (nm.contains("normal") || nm.contains("bump") || nm.contains("spec") || nm.contains("shadow")) ? 0 : 1;
                if (sc > bestScore) {
                    try { best = Tex.sims2(b); bestScore = sc; } catch (Exception ex) { if (best == null) throw ex; }
                }
            }
            return best;
        }
        Img best = null;
        long bestArea = -1;
        Exception last = null;
        List<Pkg.Ent> ents = new ArrayList<>();
        ents.addAll(pkg.ofType(Tex.T_IMG));
        ents.addAll(pkg.ofType(Tex.T_RLE2));
        for (Pkg.Ent e : ents) {
            try {
                byte[] b = pkg.read(e);
                Img im = e.type == Tex.T_RLE2 ? Tex.rle2(b) : Tex.dds(b);
                long area = (long) im.w * im.h;
                if (area >= 128 * 128 && area > bestArea) { best = im; bestArea = area; }
            } catch (Exception ex) { last = ex; }
        }
        if (best == null && last != null) throw last;
        return best;
    }

    private static String cleanName(String f) {
        String s = f == null ? "mod" : f;
        int sl = Math.max(s.lastIndexOf('/'), s.lastIndexOf('\\'));
        if (sl >= 0) s = s.substring(sl + 1);
        if (s.toLowerCase().endsWith(".package")) s = s.substring(0, s.length() - 8);
        s = s.replace('|', ' ').replace('_', ' ').trim();
        if (s.length() > 40) s = s.substring(0, 40);
        return s.isEmpty() ? "mod" : s;
    }
}
