import com.vinicius.meular.Thumb
import java.io.File
import javax.imageio.ImageIO
import java.awt.image.BufferedImage

val A = "/home/claude/work/merged/app/src/main/assets/cute/"
fun tex(path: String): Triple<IntArray, Int, Int> {
    val im = ImageIO.read(File(path)); val w = im.width; val h = im.height
    val px = IntArray(w * h); im.getRGB(0, 0, w, h, px, 0, w)
    return Triple(px, w, h)
}
fun save(name: String, px: IntArray, s: Int) {
    val bi = BufferedImage(s, s, BufferedImage.TYPE_INT_ARGB); bi.setRGB(0, 0, s, s, px, 0, s)
    File(A + "thumbs").mkdirs(); ImageIO.write(bi, "png", File(A + "thumbs/$name.png"))
}
fun main(args: Array<String>) {
    val groups = if (args.isNotEmpty()) args.toList() else listOf("af", "am", "tf", "tm", "ef", "em")
    for (g in groups) {
        fun piece(cup: String, png: String?, cut: Boolean = false): Thumb.Piece {
            val m = Thumb.parse(File(A + cup).readBytes())
            if (png == null) return Thumb.Piece(m, null, 0, 0, 0xFFD9B79B.toInt())
            val (px, w, h) = tex(A + png)
            return Thumb.Piece(m, px, w, h, 0, cut)
        }
        val head = Thumb.Piece(Thumb.headOf(Thumb.parse(File(A + "p_body_${g}1.bin").readBytes())), null, 0, 0, 0xFFE3BFA2.toInt(), false, true)
        for ((name, slot, p) in listOf(
            Triple("tee_$g", "top", listOf(piece("skate/tee_$g.cup", "skate/tee_$g.png"))),
            Triple("jacket_$g", "jacket", listOf(piece("skate/jacket_$g.cup", "skate/jacket_$g.png"))),
            Triple("cargo_$g", "bottom", listOf(piece("skate/cargo_$g.cup", "skate/cargo_$g.png"))),
            Triple("shoe_$g", "feet", listOf(piece("skate/shoe_$g.cup", "skate/shoe_$g.png"))),
            Triple("hair_$g", "hairBack", listOf(head, piece("skate/hair_$g.cup", "skate/hair_$g.png", true))),
            Triple("hairdef_$g", "hairBack", listOf(head, piece("p_hairback_h$g.bin", "heartbeat.png", true))))) {
            val t0 = System.currentTimeMillis()
            save(name, Thumb.render(p, slot, 256), 256)
            println("$name ${System.currentTimeMillis() - t0} ms")
        }
    }
}
