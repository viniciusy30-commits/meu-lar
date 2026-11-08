import com.vinicius.meular.mods.*;
import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

/**
 * Gera OFFLINE a máscara de pele escondida (a mesma regra de CuteChar.rebuildActive) para o corpo masculino TS4 (am5).
 * Uso: MaskDump <assets/cute> <saida> slot:arquivo.cup ...   (slot: jacket|top|bottom). Escreve <saida>/<nome>.mask (triângulos do corpo escondidos).
 */
public final class MaskDump {
  static final int[] HAND = {12, 16, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54};
  static final int[] FOOT = {18, 19, 20, 22, 23, 24};
  public static void main(String[] a) throws Exception {
    String root = a[0]; Path out = Paths.get(a[1]); Files.createDirectories(out);
    ByteBuffer b = ByteBuffer.wrap(Files.readAllBytes(Paths.get(root, "p_body_am5.bin"))).order(ByteOrder.LITTLE_ENDIAN);
    b.position(4); int nv = b.getInt(), ni = b.getInt(); b.getInt();
    float[] bp = new float[nv * 3]; int[] bi = new int[nv * 4]; float[] bw = new float[nv * 4];
    for (int v = 0; v < nv; v++) {
      for (int k = 0; k < 3; k++) bp[v * 3 + k] = b.getFloat();
      b.position(b.position() + 12 + 8 + 4);
      for (int k = 0; k < 4; k++) bi[v * 4 + k] = b.get() & 255;
      for (int k = 0; k < 4; k++) bw[v * 4 + k] = (b.get() & 255) / 255f;
    }
    int[] bidx = new int[ni]; for (int i = 0; i < ni; i++) bidx[i] = b.getShort() & 0xFFFF;
    float neck = 158.24f;
    for (int ai = 2; ai < a.length; ai++) {
      String sl = a[ai].substring(0, a[ai].indexOf(':')), f = a[ai].substring(a[ai].indexOf(':') + 1);
      byte[] raw = Files.readAllBytes(Paths.get(f));
      ByteBuffer c = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
      c.position(4); int pn = c.getInt(), pni = c.getInt(); c.getInt();
      float[] pp = new float[pn * 3], pnr = new float[pn * 3];
      for (int v = 0; v < pn; v++) {
        for (int k = 0; k < 3; k++) pp[v * 3 + k] = c.getFloat();
        for (int k = 0; k < 3; k++) pnr[v * 3 + k] = c.getFloat();
        c.position(c.position() + 20);
      }
      int[] pidx = new int[pni]; for (int i = 0; i < pni; i++) pidx[i] = c.getShort() & 0xFFFF;
      String nm = Paths.get(f).getFileName().toString();
      Path ca = Paths.get(f + ".cutAbove"), cb = Paths.get(f + ".cutY");
      if (Files.exists(ca)) pidx = Layers.keepAbove(pp, pidx, Float.parseFloat(new String(Files.readAllBytes(ca)).trim()));
      if (Files.exists(cb)) pidx = Layers.keepBelow(pp, pidx, Float.parseFloat(new String(Files.readAllBytes(cb)).trim()));
      boolean[] r = new boolean[ni / 3];
      float lim = sl.equals("bottom") ? 9999f : neck - 7f;
      if (sl.equals("bottom")) { float top = -Float.MAX_VALUE; for (int v = 1; v < pp.length; v += 3) top = Math.max(top, pp[v]); lim = top + 0.5f; }
      float lower = 0f;
      if (sl.equals("jacket")) { float hem = Float.MAX_VALUE; for (int k = 0; k < pidx.length; k++) hem = Math.min(hem, pp[pidx[k] * 3 + 1]); lower = hem - 1.0f; }
      if (nm.contains("minimalist_")) {
        boolean jeans = nm.contains("jeans");
        float md = jeans ? 8.0f : sl.equals("top") ? 5.0f : 4.5f, sd = jeans ? 5.0f : sl.equals("top") ? 3.0f : 2.5f;
        Cover.markSurface(bp, bidx, pp, pnr, pidx, md, r, lower, lim, bi, bw, sl.equals("top") ? HAND : FOOT, sd);
      } else {
        Cover.markSurface(bp, bidx, pp, pnr, pidx, sl.equals("jacket") ? 3.2f : 1.15f, r, lower, lim, bi, bw, sl.equals("jacket") ? HAND : FOOT, 0.6f);
      }
      StringBuilder sb = new StringBuilder(); int n = 0;
      for (int t = 0; t < r.length; t++) if (r[t]) { sb.append(t).append(' '); n++; }
      Files.write(out.resolve(nm + ".mask"), sb.toString().getBytes());
      System.out.println(nm + " (" + sl + "): " + n + " triangulos de pele escondidos");
    }
  }
}
