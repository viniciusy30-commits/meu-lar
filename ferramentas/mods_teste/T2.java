import com.vinicius.meular.mods.*;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.*;
import java.nio.file.*;
public class T2 {
    public static void main(String[] a) throws Exception {
        // a: cup png out
        byte[] cup = Files.readAllBytes(Paths.get(a[0]));
        BufferedImage im = ImageIO.read(new File(a[1]));
        int w = im.getWidth(), h = im.getHeight();
        int[] px = im.getRGB(0, 0, w, h, null, 0, w);
        byte[] o = Importer.cullBlack(cup, px, w, h);
        Files.write(Paths.get(a[2]), o);
        System.out.println(cup.length + " -> " + o.length);
    }
}
