import com.vinicius.meular.mods.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

/**
 * Aplica OFFLINE a mesma regra de camadas do app (Layers.separate) e grava cópias dos .cup já empurradas.
 * Uso: LayerDump <saida> gap maxPush radius slot:arquivo.cup ...   (slot: bottom|top|jacket; ordem de camada = bottom < top < jacket)
 */
public final class LayerDump {
  static float[] pos, nor; static int[] idx; static int nv; static byte[] raw;
  static void load(Path p) throws Exception {
    raw = Files.readAllBytes(p);
    ByteBuffer b = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
    b.getInt(); nv = b.getInt(); int ni = b.getInt(); b.getInt();
    pos = new float[nv*3]; nor = new float[nv*3];
    for (int v = 0; v < nv; v++) {
      for (int k = 0; k < 3; k++) pos[v*3+k] = b.getFloat();
      for (int k = 0; k < 3; k++) nor[v*3+k] = b.getFloat();
      b.position(b.position() + 20);
    }
    idx = new int[ni]; for (int i = 0; i < ni; i++) idx[i] = b.getShort() & 0xFFFF;
  }
  static int rank(String s) { return s.equals("bottom") ? 1 : s.equals("jacket") ? 3 : 2; }
  public static void main(String[] a) throws Exception {
    Path out = Paths.get(a[0]); Files.createDirectories(out);
    float gap = Float.parseFloat(a[1]), maxPush = Float.parseFloat(a[2]), radius = Float.parseFloat(a[3]);
    List<String[]> g = new ArrayList<>();
    for (int i = 4; i < a.length; i++) g.add(new String[]{a[i].substring(0, a[i].indexOf(':')), a[i].substring(a[i].indexOf(':') + 1)});
    g.sort((x, y) -> rank(x[0]) - rank(y[0]));
    List<float[]> P = new ArrayList<>(), N = new ArrayList<>(); List<int[]> I = new ArrayList<>(); List<byte[]> R = new ArrayList<>(); List<Integer> NV = new ArrayList<>();
    for (String[] s : g) { load(Paths.get(s[1])); P.add(pos); N.add(nor); I.add(idx); R.add(raw); NV.add(nv); }
    // jaqueta vestida: da peça de baixo (camiseta/vestido) só sobra o que fica abaixo da barra da jaqueta
    // com calça/short/saia vestido, a aba de camisa que pende da barra da jaqueta é retirada (a barra da jaqueta termina na costura)
    boolean hasBottom = false; for (int i = 0; i < g.size(); i++) if (rank(g.get(i)[0]) == 1) hasBottom = true;
    final float flapY = Float.parseFloat(System.getProperty("L_FLAP", "0"));
    float flapCut = Float.MAX_VALUE;
    for (int i = 0; i < g.size(); i++) if (g.get(i)[0].equals("jacket") && hasBottom && flapY > 0f) { I.set(i, Layers.keepAbove(P.get(i), I.get(i), flapY)); flapCut = flapY; }
    float cutY = Float.MAX_VALUE;
    for (int i = 0; i < g.size(); i++) if (g.get(i)[0].equals("jacket")) for (int k = 0; k < I.get(i).length; k++) cutY = Math.min(cutY, P.get(i)[I.get(i)[k] * 3 + 1] + Float.parseFloat(System.getProperty("L_TCUT", "0.5")));
    final float bottomCut = cutY < Float.MAX_VALUE ? cutY - 0.5f + Float.parseFloat(System.getProperty("L_BCUT", "2.0")) : Float.MAX_VALUE;
    for (int i = 0; i < g.size(); i++) if (rank(g.get(i)[0]) == 2 && cutY < Float.MAX_VALUE) I.set(i, Layers.keepBelow(P.get(i), I.get(i), cutY));
    for (int i = 0; i < g.size(); i++) if (rank(g.get(i)[0]) == 1 && bottomCut < Float.MAX_VALUE) I.set(i, Layers.keepBelow(P.get(i), I.get(i), bottomCut));

    for (int i = 0; i < g.size(); i++) {
      float[] push = new float[NV.get(i) * 3];
      for (int j = 0; j < i; j++) {
        if (rank(g.get(j)[0]) >= rank(g.get(i)[0])) continue;
        float[] pj = Layers.separate(P.get(i), I.get(i), P.get(j), N.get(j), I.get(j), gap, maxPush, radius);
        for (int v = 0; v < push.length / 3; v++) { float a1 = pj[v*3]*pj[v*3]+pj[v*3+1]*pj[v*3+1]+pj[v*3+2]*pj[v*3+2], b1 = push[v*3]*push[v*3]+push[v*3+1]*push[v*3+1]+push[v*3+2]*push[v*3+2]; if (a1 > b1) for (int k = 0; k < 3; k++) push[v*3+k] = pj[v*3+k]; }
      }
      float[] p = P.get(i), n = N.get(i); int cnt = 0; float mx = 0;
      for (int v = 0; v < push.length / 3; v++) { float l = (float) Math.sqrt(push[v*3]*push[v*3]+push[v*3+1]*push[v*3+1]+push[v*3+2]*push[v*3+2]); for (int k = 0; k < 3; k++) p[v*3+k] += push[v*3+k]; if (l > 0.05f) cnt++; mx = Math.max(mx, l); }
      ByteBuffer b = ByteBuffer.wrap(R.get(i)).order(ByteOrder.LITTLE_ENDIAN);
      for (int v = 0; v < push.length / 3; v++) for (int k = 0; k < 3; k++) b.putFloat(16 + v * 44 + k * 4, p[v*3+k]);
      String nm = Paths.get(g.get(i)[1]).getFileName().toString();
      Files.write(out.resolve(nm), R.get(i));
      if (rank(g.get(i)[0]) == 1 && bottomCut < Float.MAX_VALUE) Files.write(out.resolve(nm + ".cutY"), String.valueOf(bottomCut).getBytes());
      if (g.get(i)[0].equals("jacket") && flapCut < Float.MAX_VALUE) Files.write(out.resolve(nm + ".cutAbove"), String.valueOf(flapCut).getBytes());
      if (rank(g.get(i)[0]) == 2 && cutY < Float.MAX_VALUE) Files.write(out.resolve(nm + ".cutY"), String.valueOf(cutY).getBytes());

      System.out.println(nm + ": " + cnt + " vertices empurrados, maximo " + mx);
    }
  }
}
