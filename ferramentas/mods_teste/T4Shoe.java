import com.vinicius.meular.mods.*;
import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

/** Converte o package VHSync Dunk High (Sims 4, masculino) em uma peça feet nativa do Meu Lar. */
public final class T4Shoe {
    private static BodyRef body(Path p) throws Exception {
        ByteBuffer b = ByteBuffer.wrap(Files.readAllBytes(p)).order(ByteOrder.LITTLE_ENDIAN);
        if (b.getInt() != 0x31505543) throw new Exception("Corpo CUP1 inválido: " + p);
        int nv = b.getInt(), ni = b.getInt(); b.getInt();
        float[] pos = new float[nv*3], nor = new float[nv*3], bw = new float[nv*4];
        int[] bi = new int[nv*4];
        for (int v=0; v<nv; v++) {
            for (int k=0;k<3;k++) pos[v*3+k] = b.getFloat();
            for (int k=0;k<3;k++) nor[v*3+k] = b.getFloat();
            b.getFloat(); b.getFloat(); b.position(b.position()+4);
            for (int k=0;k<4;k++) bi[v*4+k] = b.get() & 255;
            for (int k=0;k<4;k++) bw[v*4+k] = (b.get() & 255) / 255f;
        }
        int[] idx = new int[ni];
        for (int i=0;i<ni;i++) idx[i] = b.getShort() & 65535;
        return new BodyRef(pos,nor,bi,bw,idx,null,96.8f/0.9861f);
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new Exception("Uso: T4Shoe <arquivo.package>");
        Path root = Paths.get(".").toAbsolutePath();
        Path src = root.resolve(args[0]).normalize();
        if (!Files.isRegularFile(src)) throw new Exception("Package ausente: " + src);
        BodyRef male = body(root.resolve("app/src/main/assets/cute/p_body_am5.bin"));
        byte[] raw = Files.readAllBytes(src);
        Ts4Cloth.Out o = Ts4Cloth.convert(raw, male, 0, 0.35f, 1024);
        if (!"feet".equals(o.slot)) throw new Exception("O item foi classificado como " + o.slot + ", não como sapato.");
        if (o.swatches < 1) throw new Exception("O package não tem cores CASP.");
        Path out = root.resolve("app/src/main/assets/cute/skate");
        Files.createDirectories(out);
        Files.write(out.resolve("dunk_high_am5.cup"), o.cup);

        StringBuilder colors = new StringBuilder();
        StringBuilder report = new StringBuilder();
        report.append("slot=").append(o.slot).append('\n')
              .append("vertices=").append(o.verts).append('\n')
              .append("triangles=").append(o.tris).append('/').append(o.srcTris).append('\n')
              .append("y_cm=").append(o.ymin).append("..").append(o.ymax).append('\n')
              .append("texture=").append(o.texW).append('x').append(o.texH).append('\n')
              .append("swatches=").append(o.swatches).append('\n')
              .append("pushed_vertices_total=").append(o.pushed).append('\n')
              .append("max_push_cm=").append(o.maxPush).append('\n');
        for (String n : o.notes) report.append("note=").append(n).append('\n');

        for (int i=0; i<o.swatches; i++) {
            int[] avg = {0};
            Img image = Ts4Cloth.colorTexture(raw, i, o, avg);
            String slug = String.format(Locale.ROOT, "c%02d", i+1);
            String file = i == 0 ? "dunk_high_am5.png" : "dunk_high_" + slug + "_am5.png";
            Files.write(out.resolve(file), image.png());
            colors.append(slug).append('|').append(String.format(Locale.ROOT, "%06X", avg[0])).append('\n');
            report.append(slug).append('=').append(String.format(Locale.ROOT, "%06X", avg[0])).append('\n');
        }
        Path tools = root.resolve("ferramentas/mods_teste/cores");
        Files.createDirectories(tools);
        Files.writeString(tools.resolve("dunk_high.txt"), colors.toString());
        Files.writeString(tools.resolve("dunk_high_diagnostico.txt"), report.toString());
        System.out.print(report);
    }
}
