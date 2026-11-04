package com.vinicius.meular.mods;
import java.nio.file.*;
import java.util.*;
public class T8 {
    public static void main(String[] a) throws Exception {
        Pkg pkg = new Pkg(Files.readAllBytes(Paths.get(a[0])));
        int k = 0;
        for (Pkg.Ent e : pkg.ents) {
            if (e.type != Tex.T_IMG && e.type != Tex.T_RLE2) continue;
            try {
                byte[] b = pkg.read(e);
                Img im = e.type == Tex.T_RLE2 ? Tex.rle2(b) : Tex.dds(b);
                System.out.printf("img %d type=%x inst=%x %dx%d luma=%.1f alpha=%b%n", k, e.type, e.inst, im.w, im.h, im.meanLuma(), im.hasAlpha());
                Files.write(Paths.get(a[1] + "/img_" + k + ".png"), im.limit(1024).png());
            } catch (Exception ex) { System.out.printf("img %d inst=%x ERR %s%n", k, e.inst, ex); }
            k++;
        }
    }
}
