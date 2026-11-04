package com.vinicius.meular.mods;
import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
public class T9 {
    public static void main(String[] a) throws Exception {
        String g = a[0]; float ratio = Float.parseFloat(a[1]); String file = a[2]; String outp = a[3]; String grayPng = a[4];
        String root = "/home/claude/work/merged/app/src/main/assets/cute/";
        float[] rig = null;
        for (String ln : Files.readAllLines(Paths.get(root + "bodyrig.txt"))) { String[] f = ln.trim().split("\\|"); if (f.length >= 2 && f[0].equals(g + "1")) { String[] v = f[1].split(","); rig = new float[v.length]; for (int i = 0; i < v.length; i++) rig[i] = Float.parseFloat(v[i]); } }
        ByteBuffer b = ByteBuffer.wrap(Files.readAllBytes(Paths.get(root + "p_body_" + g + "1.bin"))).order(ByteOrder.LITTLE_ENDIAN);
        b.position(4); int nv = b.getInt(), ni = b.getInt(), fl = b.getInt();
        float[] pos = new float[nv * 3], nor = new float[nv * 3], bw = new float[nv * 4]; int[] bi = new int[nv * 4];
        for (int v = 0; v < nv; v++) { for (int k = 0; k < 3; k++) pos[v*3+k] = b.getFloat(); for (int k = 0; k < 3; k++) nor[v*3+k] = b.getFloat(); b.getFloat(); b.getFloat(); b.position(b.position()+4); for (int k = 0; k < 4; k++) bi[v*4+k] = b.get() & 255; for (int k = 0; k < 4; k++) bw[v*4+k] = (b.get() & 255) / 255f; }
        int[] idx = new int[ni]; for (int i = 0; i < ni; i++) idx[i] = b.getShort() & 0xFFFF;
        BodyRef body = new BodyRef(pos, nor, bi, bw, idx, rig, 96.8f / ratio);
        Importer.Out o = Importer.convert(Files.readAllBytes(Paths.get(file)), new File(file).getName(), body);
        Importer.PieceOut p = o.pieces.get(0);
        BufferedImage im = ImageIO.read(new File(grayPng)); int w = im.getWidth(), h = im.getHeight();
        int[] px = new int[w * h]; im.getRGB(0, 0, w, h, px, 0, w);
        byte[] cup = Importer.cullBlack(p.cup, px, w, h);
        Files.write(Paths.get(outp + ".cup"), cup); Files.write(Paths.get(outp + "_raw.cup"), p.cup);
        System.out.println(g + " verts=" + p.verts + " fit=" + p.fit + " slot=" + p.slot + " cup " + p.cup.length + " -> " + cup.length);
    }
}
