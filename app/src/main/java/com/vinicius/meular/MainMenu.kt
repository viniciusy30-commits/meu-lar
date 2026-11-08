package com.vinicius.meular

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BlurMaskFilter
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.graphics.Shader
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.sin

/**
 * Etapa 124: menu inicial no estilo da tela "Home" do The Sims 4:
 * sala ilustrada em tons de azul, o personagem de corpo inteiro sobre o tapete redondo, logo com plumbob,
 * abas no topo, menu à esquerda com faixa de destaque, cartões de novidades à direita e versão no canto.
 */
object MenuPal {
    const val BG = 0xFF5CB6DA.toInt()
    const val BG2 = 0xFF6EC1E3.toInt()
    const val MID = 0xFF4BA2C9.toInt()
    const val DARK = 0xFF3A88B2.toInt()
    const val DEEP = 0xFF2C6C94.toInt()
    const val LIGHT = 0xFFA6DCF1.toInt()
    const val PALE = 0xFFD4EFFA.toInt()
    const val WHITE = 0xFFF2FBFF.toInt()
    const val INK = 0xFF233F8F.toInt()
    const val BTN = 0xFF4B55B0.toInt()
    val TITLE: Typeface = Typeface.create("sans-serif-condensed", Typeface.BOLD)
    val BLACK: Typeface = Typeface.create("sans-serif-black", Typeface.BOLD)
}

/** A sala desenhada (fica guardada num bitmap; só redesenha se mudar o tamanho). */
class RoomArt(ctx: Context) : View(ctx) {
    private var cache: Bitmap? = null
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val path = Path()

    override fun onSizeChanged(w: Int, h: Int, ow: Int, oh: Int) { cache?.recycle(); cache = null }

    override fun onDraw(c: Canvas) {
        val w = width; val h = height
        if (w <= 0 || h <= 0) return
        var bmp = cache
        if (bmp == null) { bmp = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888); paint(Canvas(bmp), w.toFloat(), h.toFloat()); cache = bmp }
        c.drawBitmap(bmp, 0f, 0f, null)
    }

    private fun fill(c: Int) { p.shader = null; p.style = Paint.Style.FILL; p.color = c }
    private fun stroke(c: Int, wd: Float) { p.shader = null; p.style = Paint.Style.STROKE; p.color = c; p.strokeWidth = wd; p.strokeCap = Paint.Cap.ROUND }

    private fun leaf(c: Canvas, x: Float, y: Float, len: Float, ang: Float, col: Int) {
        c.save(); c.translate(x, y); c.rotate(ang)
        fill(col)
        path.reset(); path.moveTo(0f, 0f); path.quadTo(len * 0.5f, -len * 0.32f, len, 0f); path.quadTo(len * 0.5f, len * 0.32f, 0f, 0f); path.close()
        c.drawPath(path, p)
        c.restore()
    }

    private fun plantTuft(c: Canvas, x: Float, y: Float, s: Float, col: Int) {
        for (k in 0 until 9) {
            val a = -150f + k * 15f
            leaf(c, x, y, s * (0.7f + 0.3f * ((k * 37) % 5) / 4f), a, col)
        }
    }

    private fun paint(c: Canvas, w: Float, h: Float) {
        val u = min(w, h * 1.9f) / 100f   // unidade proporcional
        val cx = w * 0.47f
        // parede em degradê com faixa curva clara (como o "teto" do TS4)
        p.shader = LinearGradient(0f, 0f, 0f, h, intArrayOf(MenuPal.BG2, MenuPal.BG, MenuPal.MID), floatArrayOf(0f, 0.55f, 1f), Shader.TileMode.CLAMP)
        c.drawRect(0f, 0f, w, h, p)
        stroke(0x33FFFFFF, u * 0.5f)
        c.drawArc(RectF(-w * 0.3f, h * 0.12f, w * 1.3f, h * 1.2f), 180f, 180f, false, p)
        stroke(0x22FFFFFF, u * 0.35f)
        c.drawArc(RectF(-w * 0.25f, h * 0.19f, w * 1.25f, h * 1.3f), 180f, 180f, false, p)
        // piso: mancha irregular mais escura
        fill(MenuPal.MID)
        path.reset()
        path.moveTo(w * 0.18f, h * 0.70f)
        path.cubicTo(w * 0.22f, h * 0.60f, w * 0.70f, h * 0.58f, w * 0.78f, h * 0.68f)
        path.cubicTo(w * 0.86f, h * 0.78f, w * 0.80f, h * 0.98f, w * 0.62f, h * 1.02f)
        path.lineTo(w * 0.24f, h * 1.02f)
        path.cubicTo(w * 0.10f, h * 0.96f, w * 0.12f, h * 0.78f, w * 0.18f, h * 0.70f)
        c.drawPath(path, p)
        // janelas em arco (3) + janela oval à direita, com plantas e sol dentro
        val wy0 = h * 0.24f; val wy1 = h * 0.58f
        val arches = floatArrayOf(cx - u * 13f, cx, cx + u * 13f)
        for ((i, ax) in arches.withIndex()) {
            val aw = u * (if (i == 1) 11f else 9.5f); val top = if (i == 1) wy0 - u * 3f else wy0
            val r = RectF(ax - aw / 2, top, ax + aw / 2, wy1)
            fill(MenuPal.DARK); c.drawRoundRect(RectF(r.left - u * 0.6f, r.top - u * 0.6f, r.right + u * 0.6f, r.bottom + u * 0.4f), aw / 2 + u * 0.6f, aw / 2 + u * 0.6f, p)
            fill(MenuPal.WHITE); c.drawRoundRect(r, aw / 2, aw / 2, p)
            c.save(); c.clipRect(r)
            fill(MenuPal.PALE); c.drawRect(r.left, r.bottom - (r.height() * 0.32f), r.right, r.bottom, p)
            when (i) {
                0 -> { plantTuft(c, ax - u * 1.5f, r.bottom - u * 2f, u * 5f, MenuPal.DARK); plantTuft(c, ax + u * 2f, r.bottom - u * 1f, u * 3.5f, MenuPal.MID) }
                1 -> { stroke(MenuPal.DARK, u * 0.45f); c.drawLine(ax, r.bottom, ax, r.top + u * 6f, p); for (k in 0 until 7) { leaf(c, ax, r.bottom - u * (3f + k * 2.4f), u * 3.2f, -35f, MenuPal.MID); leaf(c, ax, r.bottom - u * (4f + k * 2.4f), u * 3.2f, -145f, MenuPal.DARK) } }
                else -> { fill(MenuPal.LIGHT); c.drawCircle(ax + u * 1.5f, r.top + u * 7f, u * 2.4f, p); stroke(MenuPal.LIGHT, u * 0.35f); for (k in 0 until 8) { val a = k * 0.785f; c.drawLine(ax + u * 1.5f + cos(a) * u * 3.2f, r.top + u * 7f + sin(a) * u * 3.2f, ax + u * 1.5f + cos(a) * u * 4.4f, r.top + u * 7f + sin(a) * u * 4.4f, p) }; fill(MenuPal.DARK); path.reset(); path.moveTo(r.left, r.bottom); path.quadTo(ax, r.bottom - u * 6f, r.right, r.bottom - u * 2f); path.lineTo(r.right, r.bottom); path.close(); c.drawPath(path, p) }
            }
            c.restore()
            // trepadeiras nas bordas
            for (k in 0 until 6) leaf(c, r.left - u * 0.4f, r.top + u * (4f + k * 3f), u * 2f, if (k % 2 == 0) 200f else 160f, MenuPal.DEEP)
        }
        val ox = cx + u * 26f; val oy = h * 0.41f
        val oval = RectF(ox - u * 6f, oy - u * 9f, ox + u * 6f, oy + u * 8f)
        fill(MenuPal.DARK); c.drawOval(RectF(oval.left - u * 0.7f, oval.top - u * 0.7f, oval.right + u * 0.7f, oval.bottom + u * 0.7f), p)
        fill(MenuPal.WHITE); c.drawOval(oval, p)
        stroke(MenuPal.DARK, u * 0.5f); c.drawLine(ox, oval.top, ox, oval.bottom, p); c.drawLine(oval.left, oy, oval.right, oy, p)
        fill(MenuPal.WHITE); c.drawRoundRect(RectF(ox - u * 2.4f, oy + u * 3f, ox + u * 2.4f, oy + u * 6.5f), u, u, p)
        plantTuft(c, ox, oy + u * 3.2f, u * 3f, MenuPal.MID)
        // lâmpadas pendentes
        for ((i, lx) in floatArrayOf(cx - u * 6f, cx, cx + u * 6f).withIndex()) {
            val ly = h * (0.10f + (if (i == 1) 0.06f else 0.02f))
            stroke(MenuPal.DEEP, u * 0.25f); c.drawLine(lx, 0f, lx, ly, p)
            fill(MenuPal.DARK)
            path.reset(); path.moveTo(lx - u * 3f, ly + u * 3.2f); path.cubicTo(lx - u * 3f, ly - u * 0.5f, lx + u * 3f, ly - u * 0.5f, lx + u * 3f, ly + u * 3.2f); path.close()
            c.drawPath(path, p)
            fill(MenuPal.LIGHT); c.drawRect(lx - u * 2.6f, ly + u * 3f, lx + u * 2.6f, ly + u * 3.6f, p)
        }
        // sofá atrás do personagem
        val sy = h * 0.60f
        fill(MenuPal.LIGHT); c.drawRoundRect(RectF(cx - u * 12f, sy - u * 6f, cx + u * 12f, sy + u * 2.5f), u * 2f, u * 2f, p)
        fill(MenuPal.PALE); c.drawRoundRect(RectF(cx - u * 13.5f, sy - u * 3f, cx - u * 10f, sy + u * 3f), u * 1.2f, u * 1.2f, p); c.drawRoundRect(RectF(cx + u * 10f, sy - u * 3f, cx + u * 13.5f, sy + u * 3f), u * 1.2f, u * 1.2f, p)
        fill(MenuPal.WHITE); c.drawRoundRect(RectF(cx - u * 9f, sy - u * 4.5f, cx - u * 4f, sy - u * 0.5f), u, u, p)
        fill(MenuPal.DEEP); c.drawRoundRect(RectF(cx - u * 4f, sy - u * 4.2f, cx + u * 1f, sy - u * 0.5f), u, u, p)
        fill(MenuPal.PALE); c.drawRoundRect(RectF(cx + u * 4f, sy - u * 4.5f, cx + u * 9f, sy - u * 0.5f), u, u, p)
        // tapete redondo com franjas
        val ry = h * 0.80f
        fill(MenuPal.LIGHT); c.drawOval(RectF(cx - u * 32f, ry - u * 8f, cx + u * 32f, ry + u * 8f), p)
        fill(MenuPal.WHITE); for (k in 0 until 64) { val a = k * 6.283f / 64; c.drawCircle(cx + cos(a) * u * 33f, ry + sin(a) * u * 8.6f, u * 0.55f, p) }
        fill(0xFFB9E4F5.toInt()); c.drawOval(RectF(cx - u * 24f, ry - u * 5.6f, cx + u * 24f, ry + u * 5.6f), p)
        fill(MenuPal.PALE); c.drawOval(RectF(cx - u * 13f, ry - u * 3f, cx + u * 13f, ry + u * 3f), p)
        stroke(MenuPal.LIGHT, u * 0.3f); c.drawOval(RectF(cx - u * 9f, ry - u * 2f, cx + u * 9f, ry + u * 2f), p)
        // canto esquerdo: prateleira hexagonal com plantas, vaso grande e luminária de chão
        val hx = cx - u * 30f; val hy = h * 0.30f
        for ((i, o) in arrayOf(floatArrayOf(0f, 0f), floatArrayOf(4.2f, 0f), floatArrayOf(2.1f, -3.6f)).withIndex()) {
            val px = hx + o[0] * u; val py = hy + o[1] * u
            stroke(MenuPal.DEEP, u * 0.45f)
            path.reset(); for (k in 0..6) { val a = k * 1.047f + 0.5236f; val x = px + cos(a) * u * 2.2f; val y = py + sin(a) * u * 2.2f; if (k == 0) path.moveTo(x, y) else path.lineTo(x, y) }
            c.drawPath(path, p)
            plantTuft(c, px, py + u * 1.2f, u * 1.6f, if (i % 2 == 0) MenuPal.DEEP else MenuPal.DARK)
        }
        fill(MenuPal.DEEP); c.drawRect(hx - u * 4f, hy + u * 4.5f, hx + u * 8f, hy + u * 5.2f, p)
        val vx = cx - u * 30f; val vy = h * 0.70f
        fill(MenuPal.LIGHT); c.drawOval(RectF(vx - u * 5f, vy + u * 2f, vx + u * 5f, vy + u * 4f), p)
        fill(MenuPal.WHITE); path.reset(); path.moveTo(vx - u * 2.6f, vy - u * 3f); path.lineTo(vx + u * 2.6f, vy - u * 3f); path.lineTo(vx + u * 2f, vy + u * 3f); path.lineTo(vx - u * 2f, vy + u * 3f); path.close(); c.drawPath(path, p)
        for (k in 0 until 11) leaf(c, vx, vy - u * 3f, u * (6f + (k % 3)), -170f + k * 16f, if (k % 2 == 0) MenuPal.DEEP else MenuPal.DARK)
        stroke(MenuPal.DEEP, u * 0.4f); c.drawLine(vx + u * 6f, vy + u * 3f, vx + u * 6f, h * 0.38f, p)
        fill(MenuPal.DARK); path.reset(); path.moveTo(vx + u * 3.6f, h * 0.43f); path.lineTo(vx + u * 4.6f, h * 0.36f); path.lineTo(vx + u * 7.4f, h * 0.36f); path.lineTo(vx + u * 8.4f, h * 0.43f); path.close(); c.drawPath(path, p)
        fill(MenuPal.DEEP); c.drawOval(RectF(vx + u * 4.5f, vy + u * 2.6f, vx + u * 7.5f, vy + u * 3.6f), p)
        p.shader = null
    }
}

/** Plumbob facetado que gira (usado no logo, na faixa do menu e no carregamento). */
class Plumbob(ctx: Context) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val glow = Paint(Paint.ANTI_ALIAS_FLAG)
    private val path = Path()
    private val t0 = System.nanoTime()
    var speed = 1f
    var spin = true
    var glowOn = true

    init { setLayerType(LAYER_TYPE_SOFTWARE, null) }

    override fun onDraw(c: Canvas) {
        val w = width.toFloat(); val h = height.toFloat()
        val t = (System.nanoTime() - t0) / 1e9f * speed
        val cx = w / 2; val bob = if (spin) sin(t * 1.6f) * h * 0.025f else 0f
        val cy = h * 0.48f + bob
        val rw = w * 0.30f; val top = h * 0.44f; val bot = h * 0.46f
        if (glowOn) {
            glow.maskFilter = BlurMaskFilter(w * 0.16f, BlurMaskFilter.Blur.NORMAL)
            glow.color = 0x6639FF8A
            c.drawCircle(cx, cy, w * 0.2f, glow)
        }
        val n = 6
        val ang = if (spin) t * 1.4f else 0.3f
        val faces = ArrayList<FloatArray>()
        for (k in 0 until n) {
            val a0 = ang + k * 2f * Math.PI.toFloat() / n; val a1 = a0 + 2f * Math.PI.toFloat() / n
            val z = cos((a0 + a1) / 2)
            if (z < -0.05f) continue
            faces.add(floatArrayOf(sin(a0), sin(a1), z, k.toFloat()))
        }
        faces.sortBy { it[2] }
        fun col(l: Float, base: Int): Int {
            val r = ((base shr 16 and 255) * l).toInt().coerceIn(0, 255); val g = ((base shr 8 and 255) * l).toInt().coerceIn(0, 255); val b = ((base and 255) * l).toInt().coerceIn(0, 255)
            return Color.rgb(r, g, b)
        }
        for (f in faces) {
            val x0 = cx + f[0] * rw; val x1 = cx + f[1] * rw
            val light = (0.55f + 0.45f * f[2]) * (if (f[3].toInt() % 2 == 0) 1f else 0.86f)
            path.reset(); path.moveTo(cx, cy - top); path.lineTo(x0, cy); path.lineTo(x1, cy); path.close()
            p.shader = LinearGradient(0f, cy - top, 0f, cy, col(light * 1.15f, 0x7DFFB0), col(light, 0x22C55E), Shader.TileMode.CLAMP)
            c.drawPath(path, p)
            path.reset(); path.moveTo(cx, cy + bot); path.lineTo(x0, cy); path.lineTo(x1, cy); path.close()
            p.shader = LinearGradient(0f, cy, 0f, cy + bot, col(light * 0.9f, 0x1FB255), col(light * 0.6f, 0x0E7A38), Shader.TileMode.CLAMP)
            c.drawPath(path, p)
        }
        p.shader = null
        p.color = 0x70FFFFFF
        path.reset(); path.moveTo(cx - rw * 0.12f, cy - top * 0.82f); path.lineTo(cx - rw * 0.55f, cy - top * 0.12f); path.lineTo(cx - rw * 0.33f, cy - top * 0.1f); path.close()
        c.drawPath(path, p)
        if (spin) postInvalidateOnAnimation()
    }
}

/** Ilustração do topo dos cartões de novidades. kind: 0 cidade, 1 praia e parque, 2 garagem. */
class CardArt(ctx: Context, private val kind: Int) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val path = Path()
    override fun onDraw(c: Canvas) {
        val w = width.toFloat(); val h = height.toFloat()
        when (kind) {
            0 -> {
                p.shader = LinearGradient(0f, 0f, 0f, h, intArrayOf(0xFFFFB37A.toInt(), 0xFFF2789A.toInt(), 0xFF6B5BC4.toInt()), null, Shader.TileMode.CLAMP); c.drawRect(0f, 0f, w, h, p); p.shader = null
                p.color = 0xFFFFE6A8.toInt(); c.drawCircle(w * 0.72f, h * 0.45f, h * 0.22f, p)
                val rnd = java.util.Random(3)
                var x = 0f
                while (x < w) {
                    val bw = w * (0.06f + rnd.nextFloat() * 0.07f); val bh = h * (0.3f + rnd.nextFloat() * 0.55f)
                    p.color = if (rnd.nextBoolean()) 0xFF2B2D6E.toInt() else 0xFF3A3A86.toInt()
                    c.drawRect(x, h - bh, x + bw, h, p)
                    p.color = 0xFFFFE08A.toInt()
                    var yy = h - bh + h * 0.05f
                    while (yy < h - h * 0.06f) { var xx = x + bw * 0.18f; while (xx < x + bw - bw * 0.2f) { if (rnd.nextFloat() < 0.5f) c.drawRect(xx, yy, xx + bw * 0.14f, yy + h * 0.035f, p); xx += bw * 0.28f }; yy += h * 0.08f }
                    x += bw + w * 0.008f
                }
            }
            1 -> {
                p.shader = LinearGradient(0f, 0f, 0f, h, 0xFF7FD6FF.toInt(), 0xFFC9F0FF.toInt(), Shader.TileMode.CLAMP); c.drawRect(0f, 0f, w, h, p); p.shader = null
                p.color = 0xFF2E9BD6.toInt(); c.drawRect(0f, h * 0.62f, w, h, p)
                p.color = 0xFFF3DDA6.toInt(); path.reset(); path.moveTo(0f, h); path.lineTo(0f, h * 0.78f); path.quadTo(w * 0.4f, h * 0.66f, w * 0.65f, h); path.close(); c.drawPath(path, p)
                p.style = Paint.Style.STROKE; p.strokeWidth = h * 0.025f; p.color = 0xFFFFFFFF.toInt()
                val fx = w * 0.72f; val fy = h * 0.42f; val fr = h * 0.3f
                c.drawCircle(fx, fy, fr, p); for (k in 0 until 8) { val a = k * 0.785f; c.drawLine(fx, fy, fx + cos(a) * fr, fy + sin(a) * fr, p) }
                c.drawLine(fx, fy, fx - fr * 0.6f, h * 0.9f, p); c.drawLine(fx, fy, fx + fr * 0.6f, h * 0.9f, p)
                p.style = Paint.Style.FILL
                val cols = intArrayOf(0xFFE53935.toInt(), 0xFFFDD835.toInt(), 0xFF43A047.toInt(), 0xFF8E24AA.toInt())
                for (k in 0 until 8) { val a = k * 0.785f; p.color = cols[k % 4]; c.drawRect(fx + cos(a) * fr - h * 0.035f, fy + sin(a) * fr, fx + cos(a) * fr + h * 0.035f, fy + sin(a) * fr + h * 0.07f, p) }
                p.color = 0xFF6D4C41.toInt(); c.drawRect(w * 0.16f, h * 0.35f, w * 0.18f, h * 0.82f, p)
                p.color = 0xFF2E7D32.toInt(); for (k in 0 until 6) { c.save(); c.translate(w * 0.17f, h * 0.35f); c.rotate(-150f + k * 25f); c.drawOval(RectF(0f, -h * 0.04f, h * 0.28f, h * 0.04f), p); c.restore() }
            }
            else -> {
                p.shader = LinearGradient(0f, 0f, 0f, h, 0xFF90CAF9.toInt(), 0xFFE3F2FD.toInt(), Shader.TileMode.CLAMP); c.drawRect(0f, 0f, w, h, p); p.shader = null
                p.color = 0xFF546E7A.toInt(); c.drawRect(0f, h * 0.72f, w, h, p)
                p.color = 0xFFFFFFFF.toInt(); var x = 0f; while (x < w) { c.drawRect(x, h * 0.85f, x + w * 0.08f, h * 0.87f, p); x += w * 0.14f }
                val bx = w * 0.22f; val by = h * 0.72f; val s = h * 0.5f
                p.color = 0xFFD32F2F.toInt()
                path.reset(); path.moveTo(bx, by); path.lineTo(bx, by - s * 0.32f); path.lineTo(bx + s * 0.35f, by - s * 0.42f); path.lineTo(bx + s * 0.62f, by - s * 0.78f); path.lineTo(bx + s * 1.25f, by - s * 0.78f); path.lineTo(bx + s * 1.55f, by - s * 0.45f); path.lineTo(bx + s * 1.95f, by - s * 0.38f); path.lineTo(bx + s * 1.95f, by); path.close(); c.drawPath(path, p)
                p.color = 0xFF263238.toInt(); path.reset(); path.moveTo(bx + s * 0.7f, by - s * 0.72f); path.lineTo(bx + s * 1.2f, by - s * 0.72f); path.lineTo(bx + s * 1.43f, by - s * 0.46f); path.lineTo(bx + s * 0.5f, by - s * 0.46f); path.close(); c.drawPath(path, p)
                p.color = 0xFF111111.toInt(); c.drawCircle(bx + s * 0.45f, by, s * 0.2f, p); c.drawCircle(bx + s * 1.5f, by, s * 0.2f, p)
                p.color = 0xFFCFD8DC.toInt(); c.drawCircle(bx + s * 0.45f, by, s * 0.1f, p); c.drawCircle(bx + s * 1.5f, by, s * 0.1f, p)
                p.color = 0xFFFFF59D.toInt(); c.drawRect(bx + s * 1.85f, by - s * 0.32f, bx + s * 1.95f, by - s * 0.24f, p)
            }
        }
    }
}

@SuppressLint("ViewConstructor")
class MainMenu(ctx: Context, version: String, household: String, money: String,
               private val onPlay: () -> Unit, private val onCreator: () -> Unit, private val onNews: () -> Unit, private val onSettings: () -> Unit) : FrameLayout(ctx) {
    private val d = resources.displayMetrics.density
    private fun dp(v: Float) = (v * d).toInt()
    val sim: ImageView = ImageView(ctx)
    val face: ImageView = ImageView(ctx)
    private val cards = ArrayList<View>()
    private var page = 0

    init {
        isClickable = true
        setBackgroundColor(MenuPal.BG)
        addView(RoomArt(ctx), LayoutParams(-1, -1))
        val dm = resources.displayMetrics
        val H = dm.heightPixels.toFloat(); val W = dm.widthPixels.toFloat()
        // personagem de corpo inteiro em pé no tapete (a foto chega pelo renderizador)
        sim.scaleType = ImageView.ScaleType.FIT_END
        val simH = (H * 0.74f).toInt()
        addView(sim, LayoutParams((simH * 0.5714f).toInt(), simH, Gravity.TOP or Gravity.START).also { it.leftMargin = (W * 0.47f - simH * 0.2857f).toInt(); it.topMargin = (H * 0.82f - simH).toInt() })
        sim.alpha = 0f
        // sombra do personagem no tapete
        val shadow = View(ctx); val sg = GradientDrawable(); sg.shape = GradientDrawable.OVAL; sg.setColor(0x33244E78); shadow.background = sg
        addView(shadow, LayoutParams(dp(110f), dp(18f), Gravity.TOP or Gravity.START).also { it.leftMargin = (W * 0.47f - dp(55f)).toInt(); it.topMargin = (H * 0.815f - dp(9f)).toInt() })
        sim.bringToFront()

        // topo esquerdo: logo
        val logo = LinearLayout(ctx); logo.orientation = LinearLayout.HORIZONTAL; logo.gravity = Gravity.CENTER_VERTICAL
        val pb = Plumbob(ctx); pb.speed = 0.6f
        logo.addView(pb, LinearLayout.LayoutParams(dp(30f), dp(46f)))
        val lt = LinearLayout(ctx); lt.orientation = LinearLayout.VERTICAL
        lt.addView(txt("meu", 12f, Color.WHITE, MenuPal.TITLE).also { it.setPadding(dp(2f), 0, 0, 0); it.includeFontPadding = false })
        lt.addView(txt("LAR", 30f, Color.WHITE, MenuPal.BLACK).also { it.includeFontPadding = false; it.setShadowLayer(8f, 0f, 3f, 0x55003355); it.letterSpacing = 0.04f })
        logo.addView(lt, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(4f) })
        addView(logo, LayoutParams(-2, -2, Gravity.TOP or Gravity.START).also { it.setMargins(dp(22f), dp(12f), 0, 0) })

        // topo centro: abas
        val tabs = LinearLayout(ctx); tabs.orientation = LinearLayout.HORIZONTAL
        tabs.addView(tab("INÍCIO", 0xFF63E08C.toInt(), 0xFF1F6B3A.toInt()) { }, LinearLayout.LayoutParams(dp(120f), dp(36f)))
        tabs.addView(tab("NOVIDADES", 0xFF8C8FE0.toInt(), Color.WHITE) { onNews() }, LinearLayout.LayoutParams(dp(130f), dp(36f)).also { it.leftMargin = dp(4f) })
        addView(tabs, LayoutParams(-2, -2, Gravity.TOP or Gravity.CENTER_HORIZONTAL).also { it.topMargin = dp(14f) })

        // topo direito: rosto, saudação e "..."
        val hi = LinearLayout(ctx); hi.orientation = LinearLayout.HORIZONTAL; hi.gravity = Gravity.CENTER_VERTICAL
        face.scaleType = ImageView.ScaleType.CENTER_CROP
        val fb = GradientDrawable(); fb.shape = GradientDrawable.OVAL; fb.setColor(MenuPal.PALE); fb.setStroke(dp(2f), Color.WHITE); face.background = fb
        face.outlineProvider = object : android.view.ViewOutlineProvider() { override fun getOutline(v: View, o: android.graphics.Outline) { o.setOval(0, 0, v.width, v.height) } }
        face.clipToOutline = true
        hi.addView(face, LinearLayout.LayoutParams(dp(34f), dp(34f)))
        hi.addView(txt("Que bom te ver!", 14f, Color.WHITE, MenuPal.TITLE).also { it.setShadowLayer(4f, 0f, 1f, 0x44000000) }, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(8f) })
        val dots = txt("•••", 15f, MenuPal.BTN, MenuPal.BLACK); dots.gravity = Gravity.CENTER
        val dbg = GradientDrawable(); dbg.cornerRadius = dp(14f).toFloat(); dbg.setColor(Color.WHITE); dots.background = dbg
        dots.setOnClickListener { onSettings() }
        hi.addView(dots, LinearLayout.LayoutParams(dp(44f), dp(26f)).also { it.leftMargin = dp(10f) })
        addView(hi, LayoutParams(-2, -2, Gravity.TOP or Gravity.END).also { it.setMargins(0, dp(14f), dp(18f), 0) })

        // esquerda: casa, dinheiro e o menu
        val left = LinearLayout(ctx); left.orientation = LinearLayout.VERTICAL
        left.addView(txt(household.uppercase(), 15f, Color.WHITE, MenuPal.TITLE).also { it.letterSpacing = 0.03f }, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(22f) })
        left.addView(txt("§ $money", 13f, Color.WHITE, MenuPal.TITLE), LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(22f); it.bottomMargin = dp(12f) })
        // faixa de destaque com plumbob: Continuar
        val band = FrameLayout(ctx)
        band.background = GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, intArrayOf(0xFF2F70A8.toInt(), 0xCC3B86BD.toInt(), 0x003B86BD))
        val br = LinearLayout(ctx); br.orientation = LinearLayout.HORIZONTAL; br.gravity = Gravity.CENTER_VERTICAL
        val bp = Plumbob(ctx); bp.glowOn = false; bp.speed = 0.8f
        br.addView(bp, LinearLayout.LayoutParams(dp(26f), dp(42f)).also { it.leftMargin = dp(18f) })
        br.addView(txt("CONTINUAR JOGO", 24f, Color.WHITE, MenuPal.BLACK).also { it.setShadowLayer(6f, 0f, 2f, 0x55001A33) }, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(10f) })
        band.addView(br, LayoutParams(-1, -1))
        pressable(band) { onPlay() }
        left.addView(band, LinearLayout.LayoutParams(dp(300f), dp(56f)))
        left.addView(item("NOVO PERSONAGEM", 19f) { onCreator() }, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(22f); it.topMargin = dp(14f) })
        left.addView(item("CONFIGURAÇÕES", 19f) { onSettings() }, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(22f); it.topMargin = dp(6f) })
        left.addView(item("NOVIDADES", 13f) { onNews() }, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(22f); it.topMargin = dp(14f) })
        left.addView(item("SAIR", 13f) { (context as? android.app.Activity)?.finish() }, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(22f); it.topMargin = dp(4f) })
        addView(left, LayoutParams(-2, -2, Gravity.CENTER_VERTICAL or Gravity.START).also { it.topMargin = dp(36f) })

        // direita: cartões de novidades (2 por vez) com setas
        val right = LinearLayout(ctx); right.orientation = LinearLayout.VERTICAL; right.gravity = Gravity.CENTER_HORIZONTAL
        val cardH = ((H / d - 150f) / 2f).coerceIn(96f, 150f)
        cards.add(card(0, "A CIDADE CHEGOU", "48 quarteirões, casas para entrar, prédios, lojas e muito mais.", "JOGAR", cardH) { onPlay() })
        cards.add(card(1, "PRAIA E DIVERSÃO", "Calçadão, píer, roda-gigante e montanha-russa te esperando.", "JOGAR", cardH) { onPlay() })
        cards.add(card(2, "GARAGEM ABERTA", "Escolha seu carro ou moto na loja e saia dirigindo.", "VER MAIS", cardH) { onNews() })
        val stack = LinearLayout(ctx); stack.orientation = LinearLayout.VERTICAL
        for (cd in cards) stack.addView(cd, LinearLayout.LayoutParams(dp(210f), dp(cardH)).also { it.bottomMargin = dp(8f) })
        right.addView(stack)
        val nav = LinearLayout(ctx); nav.orientation = LinearLayout.HORIZONTAL; nav.gravity = Gravity.CENTER_VERTICAL
        val pager = LinearLayout(ctx); pager.orientation = LinearLayout.HORIZONTAL; pager.gravity = Gravity.CENTER
        val pbg = GradientDrawable(); pbg.cornerRadius = dp(12f).toFloat(); pbg.setColor(Color.WHITE); pager.background = pbg
        val dotViews = ArrayList<View>()
        for (k in 0 until 2) { val v = View(ctx); dotViews.add(v); pager.addView(v, LinearLayout.LayoutParams(dp(9f), dp(9f)).also { it.setMargins(dp(4f), 0, dp(4f), 0) }) }
        fun showPage() {
            for ((i, cd) in cards.withIndex()) cd.visibility = if (i / 2 == page || (page == 1 && i == 1)) View.VISIBLE else View.GONE
            for ((i, v) in dotViews.withIndex()) { val g = GradientDrawable(); g.shape = GradientDrawable.OVAL; g.setColor(if (i == page) MenuPal.INK else 0xFFB0B8D8.toInt()); v.background = g }
        }
        nav.addView(arrow("‹") { page = 0; showPage() }, LinearLayout.LayoutParams(dp(28f), dp(28f)))
        nav.addView(pager, LinearLayout.LayoutParams(dp(130f), dp(24f)).also { it.setMargins(dp(8f), 0, dp(8f), 0) })
        nav.addView(arrow("›") { page = 1; showPage() }, LinearLayout.LayoutParams(dp(28f), dp(28f)))
        right.addView(nav)
        showPage()
        addView(right, LayoutParams(-2, -2, Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(16f), dp(12f)) })

        // canto: versão
        val ver = txt(version, 10f, 0xCCFFFFFF.toInt(), Typeface.DEFAULT)
        ver.setPadding(dp(8f), dp(4f), dp(8f), dp(4f))
        val vb = GradientDrawable(); vb.cornerRadius = dp(4f).toFloat(); vb.setColor(0xFF1E3A78.toInt()); ver.background = vb
        addView(ver, LayoutParams(-2, -2, Gravity.BOTTOM or Gravity.START).also { it.setMargins(dp(14f), 0, 0, dp(12f)) })

        left.alpha = 0f; left.translationX = -dp(30f).toFloat()
        left.animate().alpha(1f).translationX(0f).setDuration(500).setStartDelay(150).start()
        right.alpha = 0f; right.translationX = dp(30f).toFloat()
        right.animate().alpha(1f).translationX(0f).setDuration(500).setStartDelay(250).start()
    }

    /** Foto do personagem chegou: aparece subindo de leve. */
    fun setSim(b: Bitmap) {
        sim.setImageBitmap(b)
        sim.translationY = dp(14f).toFloat()
        sim.animate().alpha(1f).translationY(0f).setDuration(500).start()
    }

    private fun txt(s: String, size: Float, col: Int, tf: Typeface): TextView {
        val t = TextView(context); t.text = s; t.textSize = size; t.setTextColor(col); t.typeface = tf
        return t
    }

    private fun item(s: String, size: Float, act: () -> Unit): TextView {
        val t = txt(s, size, Color.WHITE, MenuPal.BLACK)
        t.setShadowLayer(5f, 0f, 2f, 0x44001A33)
        pressable(t, act)
        return t
    }

    private fun pressable(v: View, act: () -> Unit) {
        v.setOnTouchListener { vv, e ->
            when (e.actionMasked) {
                MotionEvent.ACTION_DOWN -> vv.animate().scaleX(0.96f).scaleY(0.96f).alpha(0.85f).setDuration(70).start()
                MotionEvent.ACTION_UP -> { vv.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(110).start(); if (e.x in 0f..vv.width.toFloat() && e.y in 0f..vv.height.toFloat()) act() }
                MotionEvent.ACTION_CANCEL -> vv.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(110).start()
            }
            true
        }
        v.pivotX = 0f
    }

    /** Aba em paralelogramo (como HOME/STORE). */
    private fun tab(s: String, col: Int, tc: Int, act: () -> Unit): View {
        val v = object : View(context) {
            val p = Paint(Paint.ANTI_ALIAS_FLAG)
            val path = Path()
            override fun onDraw(c: Canvas) {
                val w = width.toFloat(); val h = height.toFloat(); val k = h * 0.35f
                path.reset(); path.moveTo(k, 0f); path.lineTo(w, 0f); path.lineTo(w - k, h); path.lineTo(0f, h); path.close()
                p.color = 0x33000000; c.save(); c.translate(0f, 3f); c.drawPath(path, p); c.restore()
                p.color = col; c.drawPath(path, p)
                p.color = tc; p.textSize = h * 0.46f; p.typeface = MenuPal.BLACK; p.textAlign = Paint.Align.CENTER
                c.drawText(s, w / 2, h * 0.66f, p)
            }
        }
        pressable(v, act)
        return v
    }

    private fun arrow(s: String, act: () -> Unit): TextView {
        val t = txt(s, 20f, Color.WHITE, MenuPal.BLACK); t.gravity = Gravity.CENTER; t.includeFontPadding = false
        val g = GradientDrawable(); g.shape = GradientDrawable.OVAL; g.setColor(MenuPal.INK); t.background = g
        t.setOnClickListener { act() }
        return t
    }

    private fun card(kind: Int, title: String, body: String, btn: String, hDp: Float, act: () -> Unit): View {
        val f = LinearLayout(context); f.orientation = LinearLayout.VERTICAL
        val g = GradientDrawable(); g.cornerRadius = dp(8f).toFloat(); g.setColor(Color.WHITE); f.background = g
        f.elevation = dp(4f).toFloat(); f.clipToOutline = true
        f.addView(CardArt(context, kind), LinearLayout.LayoutParams(-1, dp(hDp * 0.42f)))
        val inner = LinearLayout(context); inner.orientation = LinearLayout.VERTICAL; inner.setPadding(dp(10f), dp(5f), dp(10f), dp(6f))
        inner.addView(txt(title, 13f, MenuPal.INK, MenuPal.BLACK))
        val b = txt(body, 10.5f, 0xFF3F5FB5.toInt(), MenuPal.TITLE); b.maxLines = 2
        inner.addView(b)
        val bt = txt(btn, 10.5f, Color.WHITE, MenuPal.BLACK); bt.gravity = Gravity.CENTER
        val bg = GradientDrawable(); bg.cornerRadius = dp(3f).toFloat(); bg.setColor(MenuPal.BTN); bt.background = bg
        bt.setPadding(dp(14f), dp(3f), dp(14f), dp(3f))
        pressable(bt, act)
        inner.addView(bt, LinearLayout.LayoutParams(-2, -2).also { it.gravity = Gravity.CENTER_HORIZONTAL; it.topMargin = dp(3f) })
        f.addView(inner, LinearLayout.LayoutParams(-1, -1))
        return f
    }
}

/** Tela de carregamento: fundo azul liso (nada do jogo aparece atrás), plumbob grande, etapa, barra e dicas. */
@SuppressLint("ViewConstructor")
class LoadingScreen(ctx: Context, private val progress: () -> Float, private val onDone: () -> Unit) : FrameLayout(ctx) {
    private val d = resources.displayMetrics.density
    private fun dp(v: Float) = (v * d).toInt()
    private val tips = arrayOf(
        "Toque no botão do mapa para ver a cidade inteira e ligar o GPS.",
        "Na loja, aba Veículos: escolha seu carro ou moto. Ele fica na rua em frente de casa.",
        "Chegue perto do seu veículo e toque em Dirigir.",
        "Dá para entrar nas casas, lojas e prédios: as paredes somem como no Sims.",
        "A praia tem píer, quiosques e um mar com ondas.",
        "O parque de diversões fica na beira-mar: roda-gigante, montanha-russa e carrossel.",
        "Casas e terrenos com placa vermelha estão à venda.",
        "Os carros param no sinal vermelho. Atravesse na faixa!")
    private val stage: TextView
    private val tip: TextView
    private val pct: TextView
    private val bar: View
    private var shown = 0f
    private var finished = false
    private var tipIdx = (Math.random() * tips.size).toInt()
    private var lastTip = 0L
    private var lastTarget = -1f
    private var lastMove = System.currentTimeMillis()

    init {
        isClickable = true
        setBackgroundColor(MenuPal.BG)
        addView(object : View(ctx) {
            val p = Paint(Paint.ANTI_ALIAS_FLAG)
            val t0 = System.nanoTime()
            override fun onDraw(c: Canvas) {
                val w = width.toFloat(); val h = height.toFloat()
                p.shader = LinearGradient(0f, 0f, 0f, h, intArrayOf(MenuPal.BG2, MenuPal.BG, MenuPal.DARK), floatArrayOf(0f, 0.6f, 1f), Shader.TileMode.CLAMP)
                c.drawRect(0f, 0f, w, h, p); p.shader = null
                // losangos claros girando devagar ao fundo (padrão do carregamento)
                val t = (System.nanoTime() - t0) / 1e9f
                p.color = 0x14FFFFFF
                val s = min(w, h) * 0.09f
                var y = -s; var row = 0
                while (y < h + s) {
                    var x = if (row % 2 == 0) -s else 0f
                    while (x < w + s) {
                        c.save(); c.translate(x + sin(t * 0.3f + y * 0.01f) * 6f, y); c.rotate(45f)
                        c.drawRect(-s * 0.32f, -s * 0.32f, s * 0.32f, s * 0.32f, p); c.restore()
                        x += s * 2f
                    }
                    y += s; row++
                }
                postInvalidateOnAnimation()
            }
        }, LayoutParams(-1, -1))
        val col = LinearLayout(ctx); col.orientation = LinearLayout.VERTICAL; col.gravity = Gravity.CENTER_HORIZONTAL
        val pb = Plumbob(ctx); pb.speed = 1.6f
        col.addView(pb, LinearLayout.LayoutParams(dp(90f), dp(126f)))
        stage = TextView(ctx); stage.textSize = 20f; stage.setTextColor(Color.WHITE); stage.typeface = MenuPal.BLACK; stage.gravity = Gravity.CENTER
        stage.setShadowLayer(6f, 0f, 2f, 0x55001A33)
        col.addView(stage, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(6f) })
        val track = FrameLayout(ctx)
        val tg = GradientDrawable(); tg.cornerRadius = dp(9f).toFloat(); tg.setColor(0x40FFFFFF); tg.setStroke(dp(2f), Color.WHITE)
        track.background = tg
        track.setPadding(dp(3f), dp(3f), dp(3f), dp(3f))
        bar = View(ctx)
        val bg = GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, intArrayOf(0xFF2ECC71.toInt(), 0xFF9BF2C0.toInt())); bg.cornerRadius = dp(6f).toFloat()
        bar.background = bg
        track.addView(bar, LayoutParams(0, -1))
        col.addView(track, LinearLayout.LayoutParams(dp(320f), dp(18f)).also { it.topMargin = dp(14f) })
        pct = TextView(ctx); pct.textSize = 13f; pct.setTextColor(Color.WHITE); pct.typeface = MenuPal.TITLE
        col.addView(pct, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(6f) })
        addView(col, LayoutParams(-2, -2, Gravity.CENTER).also { it.bottomMargin = dp(20f) })
        // dica num cartão branco embaixo
        val tipBox = LinearLayout(ctx); tipBox.orientation = LinearLayout.HORIZONTAL; tipBox.gravity = Gravity.CENTER_VERTICAL
        val tb = GradientDrawable(); tb.cornerRadius = dp(10f).toFloat(); tb.setColor(0xF2FFFFFF.toInt()); tipBox.background = tb
        tipBox.setPadding(dp(14f), dp(8f), dp(16f), dp(8f))
        val lamp = TextView(ctx); lamp.text = "DICA"; lamp.textSize = 11f; lamp.setTextColor(Color.WHITE); lamp.typeface = MenuPal.BLACK; lamp.gravity = Gravity.CENTER
        val lb = GradientDrawable(); lb.cornerRadius = dp(4f).toFloat(); lb.setColor(MenuPal.BTN); lamp.background = lb; lamp.setPadding(dp(8f), dp(2f), dp(8f), dp(2f))
        tipBox.addView(lamp)
        tip = TextView(ctx); tip.textSize = 13f; tip.setTextColor(MenuPal.INK); tip.typeface = MenuPal.TITLE
        tipBox.addView(tip, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(10f) })
        addView(tipBox, LayoutParams(-2, -2, Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL).also { it.bottomMargin = dp(22f) })
        tip.text = tips[tipIdx]
        lastTip = System.currentTimeMillis()
        post(object : Runnable {
            override fun run() {
                if (finished) return
                var target = progress().coerceIn(0f, 1f)
                val nowT = System.currentTimeMillis()
                if (abs(target - lastTarget) > 0.001f) { lastTarget = target; lastMove = nowT }
                // nunca fica preso: parado no fim por muito tempo, entra assim mesmo (o resto termina de carregar jogando)
                if (target >= 0.85f && nowT - lastMove > 9000L) target = 1f
                if (nowT - lastMove > 30000L) target = 1f
                shown += (target - shown) * 0.16f
                if (target >= 1f && shown > 0.985f) shown = 1f
                val w = ((dp(320f) - dp(6f)) * shown).toInt()
                bar.layoutParams = bar.layoutParams.also { it.width = maxOf(dp(12f), w) }
                bar.requestLayout()
                pct.text = "${(shown * 100).toInt()}%"
                stage.text = when {
                    shown < 0.12f -> "Abrindo o mapa da cidade"
                    shown < 0.35f -> "Asfaltando as ruas"
                    shown < 0.55f -> "Erguendo casas e prédios"
                    shown < 0.72f -> "Mobiliando os interiores"
                    shown < 0.86f -> "Enchendo a praia e o parque"
                    shown < 0.99f -> "Ligando o trânsito"
                    else -> "Pronto!"
                }
                val now = System.currentTimeMillis()
                if (now - lastTip > 4500L) {
                    lastTip = now; tipIdx = (tipIdx + 1) % tips.size
                    tip.animate().alpha(0f).setDuration(220).withEndAction { tip.text = tips[tipIdx]; tip.animate().alpha(1f).setDuration(260).start() }.start()
                }
                if (shown >= 1f) { finished = true; postDelayed({ onDone() }, 400); return }
                postDelayed(this, 33)
            }
        })
    }
}
