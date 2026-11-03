package com.vinicius.meular.mods;

import java.util.ArrayList;
import java.util.List;
import java.util.zip.Inflater;

/** Leitor de arquivos .package (DBPF): 1.x = The Sims 2, 2.0 = The Sims 3, 2.1 = The Sims 4. */
public final class Pkg {
    public static final class Ent {
        public int type;
        public int group;
        public int i1;      // instância (parte baixa no Sims 2/3/4: ver [inst])
        public int i2;
        public long inst;
        int off;
        int size;
        int mem;
        int comp;
        boolean qfs;        // Sims 2: listado no DIR (comprimido com QFS)
    }

    public final byte[] d;
    public final int major;
    public final int minor;
    public final List<Ent> ents = new ArrayList<>();

    public Pkg(byte[] d) throws Exception {
        this.d = d;
        if (d.length < 96 || d[0] != 'D' || d[1] != 'B' || d[2] != 'P' || d[3] != 'F') throw new Exception("Isso não é um arquivo .package do The Sims");
        major = i32(4);
        minor = i32(8);
        if (major == 1) parse1();
        else if (major == 2) parse2();
        else throw new Exception("Versão de package não suportada (" + major + "." + minor + ")");
    }

    /** 2 = Sims 2, 3 = Sims 3, 4 = Sims 4. */
    public int game() {
        if (major == 1) return 2;
        return minor >= 1 ? 4 : 3;
    }

    private int i32(int p) {
        return (d[p] & 255) | ((d[p + 1] & 255) << 8) | ((d[p + 2] & 255) << 16) | ((d[p + 3] & 255) << 24);
    }

    private void parse1() throws Exception {
        int n = i32(36);
        int off = i32(40);
        int imin = i32(60);
        int es = imin >= 2 ? 24 : 20;
        if (n < 0 || off < 0 || (long) off + (long) n * es > d.length) throw new Exception("Índice do package corrompido");
        for (int i = 0; i < n; i++) {
            int q = off + i * es;
            Ent e = new Ent();
            e.type = i32(q);
            e.group = i32(q + 4);
            e.i1 = i32(q + 8);
            int k = 12;
            if (es == 24) { e.i2 = i32(q + 12); k = 16; }
            e.off = i32(q + k);
            e.size = i32(q + k + 4);
            e.mem = e.size;
            e.inst = ((long) e.i2 << 32) | (e.i1 & 0xFFFFFFFFL);
            ents.add(e);
        }
        // DIR (0xE86B1EEF): lista os recursos comprimidos (QFS) e o tamanho depois de descomprimir
        for (Ent e : new ArrayList<>(ents)) {
            if (e.type != 0xE86B1EEF) continue;
            int ds = es == 24 ? 20 : 16;
            int cnt = e.size / ds;
            for (int i = 0; i < cnt; i++) {
                int q = e.off + i * ds;
                int t = i32(q);
                int g = i32(q + 4);
                int a = i32(q + 8);
                int b = es == 24 ? i32(q + 12) : 0;
                int sz = i32(q + ds - 4);
                for (Ent x : ents) {
                    if (x.type == t && x.group == g && x.i1 == a && x.i2 == b) { x.qfs = true; x.mem = sz; }
                }
            }
        }
    }

    private void parse2() throws Exception {
        int n = i32(36);
        int idx = i32(64);
        if (idx == 0) idx = i32(40);
        if (n < 0 || idx <= 0 || idx >= d.length) throw new Exception("Índice do package corrompido");
        int flags = i32(idx);
        int p = idx + 4;
        int[] c = new int[3];
        for (int i = 0; i < 3; i++) if ((flags & (1 << i)) != 0) { c[i] = i32(p); p += 4; }
        for (int k = 0; k < n; k++) {
            Ent e = new Ent();
            int t = c[0];
            int g = c[1];
            int ih = c[2];
            if ((flags & 1) == 0) { t = i32(p); p += 4; }
            if ((flags & 2) == 0) { g = i32(p); p += 4; }
            if ((flags & 4) == 0) { ih = i32(p); p += 4; }
            int il = i32(p); p += 4;
            e.off = i32(p); p += 4;
            e.size = i32(p) & 0x7FFFFFFF; p += 4;
            e.mem = i32(p); p += 4;
            e.comp = i32(p) & 0xFFFF; p += 4;
            e.type = t;
            e.group = g;
            e.i1 = il;
            e.i2 = ih;
            e.inst = ((long) ih << 32) | (il & 0xFFFFFFFFL);
            ents.add(e);
        }
    }

    public List<Ent> ofType(int type) {
        List<Ent> r = new ArrayList<>();
        for (Ent e : ents) if (e.type == type) r.add(e);
        return r;
    }

    public byte[] read(Ent e) throws Exception {
        if (e.off < 0 || e.size < 0 || (long) e.off + e.size > d.length) throw new Exception("Recurso fora do arquivo");
        byte[] raw = new byte[e.size];
        System.arraycopy(d, e.off, raw, 0, e.size);
        if (major == 1) {
            if (!e.qfs) return raw;
            return RefPack.decode(raw, 4);
        }
        switch (e.comp) {
            case 0: return raw;
            case 0x5A42: {
                Inflater inf = new Inflater();
                inf.setInput(raw);
                byte[] out = new byte[Math.max(e.mem, 16)];
                int o = 0;
                try {
                    while (!inf.finished() && o < out.length) {
                        int k = inf.inflate(out, o, out.length - o);
                        if (k == 0 && (inf.needsInput() || inf.needsDictionary())) break;
                        o += k;
                    }
                } finally {
                    inf.end();
                }
                if (o != out.length) { byte[] t = new byte[o]; System.arraycopy(out, 0, t, 0, o); out = t; }
                return out;
            }
            case 0xFFFE:
            case 0xFFFF:
                return RefPack.decode(raw, 0);
            default:
                throw new Exception("Compressão de package não suportada (0x" + Integer.toHexString(e.comp) + ")");
        }
    }
}
