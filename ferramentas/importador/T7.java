package com.vinicius.meular.mods;
import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;
public class T7 {
    public static void main(String[] a) throws Exception {
        String g = a[0]; float ratio = Float.parseFloat(a[1]); String file = a[2];
        String root = "/home/claude/work/merged/app/src/main/assets/cute/";
        float[] rig = null;
        for (String ln : Files.readAllLines(Paths.get(root + "bodyrig.txt"))) { String[] f = ln.trim().split("\\|"); if (f.length >= 2 && f[0].equals(g + "1")) { String[] v = f[1].split(","); rig = new float[v.length]; for (int i = 0; i < v.length; i++) rig[i] = Float.parseFloat(v[i]); } }
        ByteBuffer b = ByteBuffer.wrap(Files.readAllBytes(Paths.get(root + "p_body_" + g + "1.bin"))).order(ByteOrder.LITTLE_ENDIAN);
        b.position(4); int nv = b.getInt(), ni = b.getInt(), fl = b.getInt();
        float[] pos = new float[nv * 3], nor = new float[nv * 3], bw = new float[nv * 4]; int[] bi = new int[nv * 4];
        for (int v = 0; v < nv; v++) { for (int k = 0; k < 3; k++) pos[v*3+k] = b.getFloat(); for (int k = 0; k < 3; k++) nor[v*3+k] = b.getFloat(); b.getFloat(); b.getFloat(); b.position(b.position()+4); for (int k = 0; k < 4; k++) bi[v*4+k] = b.get() & 255; for (int k = 0; k < 4; k++) bw[v*4+k] = (b.get() & 255) / 255f; }
        int[] idx = new int[ni]; for (int i = 0; i < ni; i++) idx[i] = b.getShort() & 0xFFFF;
        BodyRef body = new BodyRef(pos, nor, bi, bw, idx, rig, 96.8f / ratio);
        Pkg pkg = new Pkg(Files.readAllBytes(Paths.get(file)));
        System.out.println("game=" + pkg.game() + " ents=" + pkg.ents.size());
        TreeMap<String,Integer> hist = new TreeMap<>(); for (Pkg.Ent e : pkg.ents) hist.merge(Integer.toHexString(e.type), 1, Integer::sum); System.out.println(hist);
        Grid gr = Fit.bodyGrid(body);
        int k = 0;
        for (Pkg.Ent e : pkg.ofType(Geom.T_GEOM)) {
            RawMesh m = Geom.parse(pkg.read(e), pkg.game());
            double[] mn = {1e9,1e9,1e9}, mx = {-1e9,-1e9,-1e9};
            for (int i = 0; i < m.nv(); i++) for (int c = 0; c < 3; c++) { double v = m.pos[i*3+c]; mn[c] = Math.min(mn[c], v); mx[c] = Math.max(mx[c], v); }
            String loss = "?";
            try { Fit.Placed p = Fit.place(m, body, gr); loss = String.format("%.2f slot=%s", p.loss, p.slot); } catch (Exception ex) { loss = "ERR " + ex; }
            System.out.printf("GEOM %d inst=%x nv=%d nt=%d bbox y[%.2f..%.2f] x[%.2f..%.2f] z[%.2f..%.2f] loss=%s%n", k++, e.inst, m.nv(), m.nt(), mn[1], mx[1], mn[0], mx[0], mn[2], mx[2], loss);
        }
    }
}
