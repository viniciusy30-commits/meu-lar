package com.vinicius.meular.mods;
import java.nio.file.*;
import java.util.*;
public class T10 {
    public static void main(String[] a) throws Exception {
        Pkg pkg = new Pkg(Files.readAllBytes(Paths.get(a[0])));
        int k = 0;
        for (Pkg.Ent e : pkg.ofType(Geom.T_GEOM)) {
            RawMesh m = Geom.parse(pkg.read(e), pkg.game());
            int nv = m.nv();
            float[] pos = new float[nv * 3], nor = new float[nv * 3], uv = new float[nv * 2]; int[] bi = new int[nv * 4]; float[] bw = new float[nv * 4];
            for (int i = 0; i < nv; i++) { for (int c = 0; c < 3; c++) { pos[i*3+c] = m.pos[i*3+c] * 100f; nor[i*3+c] = m.nor != null ? m.nor[i*3+c] : 0; } uv[i*2] = m.uv[i*2]; uv[i*2+1] = m.uv[i*2+1]; bw[i*4] = 1; }
            Files.write(Paths.get(a[1] + "/raw" + k + ".cup"), Fit.cup1(pos, nor, uv, m.idx, bi, bw));
            System.out.println("raw" + k + " nv=" + nv);
            k++;
        }
    }
}
