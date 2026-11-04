import com.vinicius.meular.mods.*;
import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;
public class T6 {
    public static void main(String[] a) throws Exception {
        String g = a[0]; float ratio = Float.parseFloat(a[1]); String file = a[2]; String outp = a[3];
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
        System.out.println(g + " pecas=" + o.pieces.size() + " texOnly=" + (o.texOnly != null) + " notes=" + o.notes);
        int i = 0;
        for (Importer.PieceOut p : o.pieces) {
            System.out.println("  [" + i + "] " + p.name + " slot=" + p.slot + " verts=" + p.verts + " fit=" + p.fit + " tex=" + p.hasTex + " alpha=" + p.alpha + " game=" + p.game);
            Files.write(Paths.get(outp + "_" + i + ".cup"), p.cup); Files.write(Paths.get(outp + "_" + i + ".png"), p.png); i++;
        }
    }
}
