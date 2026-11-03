import com.vinicius.meular.mods.*;
import java.io.*;
import java.nio.*;
import java.nio.file.*;

public class T1 {
    static BodyRef loadBody(String bin, float[] rig, float s0) throws Exception {
        ByteBuffer b = ByteBuffer.wrap(Files.readAllBytes(Paths.get(bin))).order(ByteOrder.LITTLE_ENDIAN);
        b.position(4);
        int nv = b.getInt(), ni = b.getInt(), fl = b.getInt();
        float[] pos = new float[nv * 3], nor = new float[nv * 3], bw = new float[nv * 4];
        int[] bi = new int[nv * 4];
        for (int v = 0; v < nv; v++) {
            for (int k = 0; k < 3; k++) pos[v * 3 + k] = b.getFloat();
            for (int k = 0; k < 3; k++) nor[v * 3 + k] = b.getFloat();
            b.getFloat(); b.getFloat();
            b.position(b.position() + 4);
            for (int k = 0; k < 4; k++) bi[v * 4 + k] = b.get() & 255;
            for (int k = 0; k < 4; k++) bw[v * 4 + k] = (b.get() & 255) / 255f;
        }
        int[] idx = new int[ni];
        for (int i = 0; i < ni; i++) idx[i] = b.getShort() & 0xFFFF;
        return new BodyRef(pos, nor, bi, bw, idx, rig, s0);
    }
    public static void main(String[] a) throws Exception {
        String root = "/home/claude/work/merged/";
        float[] rig = {15.71f,149.50f,-2.02f,37.99f,127.28f,-3.60f,57.91f,107.42f,-2.00f,6.48f,99.36f,0.00f,8.22f,51.90f,1.24f,9.73f,10.85f,-0.95f,142.41f,157.71f,164.33f,1.33f,184.16f};
        BodyRef body = loadBody(root + "app/src/main/assets/cute/p_body_am1.bin", rig, 96.8f / 0.9861f);
        for (String f : a) {
            byte[] d = Files.readAllBytes(Paths.get(f));
            long t0 = System.currentTimeMillis();
            try {
                Importer.Out o = Importer.convert(d, new File(f).getName(), body);
                System.out.println(f + " -> " + o.pieces.size() + " pecas, texOnly=" + (o.texOnly != null) + " " + o.notes + " (" + (System.currentTimeMillis() - t0) + " ms)");
                int i = 0;
                for (Importer.PieceOut p : o.pieces) {
                    System.out.println("   " + p.name + " slot=" + p.slot + " verts=" + p.verts + " fit=" + p.fit + " tex=" + p.hasTex + " cup=" + p.cup.length);
                    Files.write(Paths.get("/tmp/out_" + new File(f).getName() + "_" + i + ".cup"), p.cup);
                    Files.write(Paths.get("/tmp/out_" + new File(f).getName() + "_" + i + ".png"), p.png);
                    i++;
                }
                if (o.texOnly != null) Files.write(Paths.get("/tmp/out_" + new File(f).getName() + "_tex.png"), o.texOnly.png());
            } catch (Exception e) {
                System.out.println(f + " ERRO: " + e);
            }
        }
    }
}
