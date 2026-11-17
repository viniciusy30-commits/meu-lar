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
 * Menu inicial e tela de carregamento com identidade própria do Meu Lar: a cidade à beira-mar ilustrada no
 * fim da tarde (céu em degradê, sol, nuvens andando, prédios com janelas acesas, morros, farol girando a luz,
 * coqueiros e ondas na praia), logo com a casinha, menu único à esquerda e o personagem no centro sobre um pedestal.
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


/** Cena da cidade à beira-mar (parte fixa guardada em bitmap; nuvens, ondas, luz do farol e gaivotas animadas). */
class CityScene(ctx: Context, private val dusk: Float = 0f, private val night: Float = 0f, private val sunU: Float = 0.62f, private val sunV: Float = 0.06f) : View(ctx) {
    private var cache: Bitmap? = null
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val path = Path()
    private val t0 = System.nanoTime()

    override fun onSizeChanged(w: Int, h: Int, ow: Int, oh: Int) { cache?.recycle(); cache = null }

    private fun fill(c: Int) { p.shader = null; p.style = Paint.Style.FILL; p.color = c; p.maskFilter = null }
    private fun lerp(a: Int, b: Int, t: Float): Int {
        val k = t.coerceIn(0f, 1f)
        return Color.argb(255, ((a shr 16 and 255) + ((b shr 16 and 255) - (a shr 16 and 255)) * k).toInt(), ((a shr 8 and 255) + ((b shr 8 and 255) - (a shr 8 and 255)) * k).toInt(), ((a and 255) + ((b and 255) - (a and 255)) * k).toInt())
    }

    override fun onDraw(c: Canvas) {
        val w = width.toFloat(); val h = height.toFloat()
        if (w <= 0f || h <= 0f) return
        var bmp = cache
        if (bmp == null) { bmp = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888); paintStatic(Canvas(bmp), w, h); cache = bmp }
        val t = (System.nanoTime() - t0) / 1e9f
        // céu e sol já no bitmap; nuvens por cima do céu e atrás da cidade não dá (bitmap único): ficam altas, sobre o céu
        c.drawBitmap(bmp, 0f, 0f, null)
        val hz = h * 0.66f
        if (night > 0f) { fill(Color.argb((115 * night).toInt(), 8, 12, 38)); c.drawRect(0f, hz - h * 0.36f, w, h, p) }   // cidade e mar no escuro (janelas continuam acesas por baixo do véu)
        for (k in 0 until 5) {
            val sp = 6f + k * 3f
            val cx = ((k * 0.27f * w + t * sp) % (w * 1.4f)) - w * 0.2f
            val cy = h * (0.08f + 0.06f * (k % 3))
            val s = h * (0.05f + 0.015f * (k % 2))
            fill(if (k % 2 == 0) 0x55FFFFFF else 0x40FFF3E6)
            c.drawOval(RectF(cx - s * 2.2f, cy - s * 0.5f, cx + s * 2.2f, cy + s * 0.5f), p)
            c.drawOval(RectF(cx - s * 1.1f, cy - s * 0.95f, cx + s * 0.9f, cy + s * 0.3f), p)
            c.drawOval(RectF(cx - s * 0.1f, cy - s * 0.75f, cx + s * 1.6f, cy + s * 0.35f), p)
        }
        // luz do farol girando (cone translúcido)
        val lx = w * 0.86f; val ly = hz - h * 0.235f
        val a = (t * 0.9f) % (2f * Math.PI.toFloat())
        val reach = w * 0.55f * abs(cos(a)) + w * 0.04f
        val dir = if (cos(a) >= 0f) 1f else -1f
        val spread = h * 0.05f
        p.shader = LinearGradient(lx, ly, lx - dir * reach, ly, 0x88FFF6C8.toInt(), 0x00FFF6C8, Shader.TileMode.CLAMP)
        path.reset(); path.moveTo(lx, ly); path.lineTo(lx - dir * reach, ly - spread); path.lineTo(lx - dir * reach, ly + spread); path.close()
        c.drawPath(path, p); p.shader = null
        fill(0xFFFFF4C2.toInt()); c.drawCircle(lx, ly, h * 0.011f, p)
        // ondas chegando na areia
        for (k in 0 until 3) {
            val ph = ((t * 0.25f + k / 3f) % 1f)
            val yy = hz + (h * 0.88f - hz) * (0.35f + 0.55f * ph)
            fill(Color.argb((150 * (1f - ph)).toInt(), 255, 255, 255))
            path.reset(); path.moveTo(-10f, yy)
            var x = 0f
            while (x <= w + 40f) { path.quadTo(x + w * 0.04f, yy - h * 0.012f, x + w * 0.08f, yy); x += w * 0.08f }
            path.lineTo(w + 40f, yy + h * 0.006f); path.lineTo(-10f, yy + h * 0.006f); path.close()
            c.drawPath(path, p)
        }
        // veleiros passando ao longe e brilhos na água
        for (k in 0 until 3) {
            val bx = ((t * (4f + k * 2f) + k * w * 0.37f) % (w * 1.3f)) - w * 0.15f
            val by = hz + h * (0.03f + 0.03f * k); val s = h * (0.035f - k * 0.006f)
            val bob = sin(t * 1.5f + k) * s * 0.06f
            fill(0xFF2C3A55.toInt()); path.reset(); path.moveTo(bx - s * 0.7f, by + bob); path.lineTo(bx + s * 0.7f, by + bob); path.lineTo(bx + s * 0.5f, by + s * 0.22f + bob); path.lineTo(bx - s * 0.5f, by + s * 0.22f + bob); path.close(); c.drawPath(path, p)
            fill(0xFFFDFBF4.toInt()); path.reset(); path.moveTo(bx, by - s * 1.3f + bob); path.lineTo(bx, by - s * 0.05f + bob); path.lineTo(bx + s * 0.6f, by - s * 0.05f + bob); path.close(); c.drawPath(path, p)
            fill(0xFFF2D8A0.toInt()); path.reset(); path.moveTo(bx - s * 0.05f, by - s * 1.1f + bob); path.lineTo(bx - s * 0.05f, by - s * 0.05f + bob); path.lineTo(bx - s * 0.5f, by - s * 0.05f + bob); path.close(); c.drawPath(path, p)
        }
        for (k in 0 until 26) {
            val ph = (t * 0.7f + k * 0.37f) % 1f
            val sx2 = w * (0.5f + 0.24f * sin(k * 12.9898f)); val sy2 = hz + (h * 0.84f - hz) * (0.1f + 0.8f * ((k * 0.618f) % 1f))
            fill(Color.argb((200 * sin(ph * Math.PI.toFloat())).toInt().coerceIn(0, 255), 255, 246, 214))
            c.drawRect(sx2 - h * 0.008f, sy2, sx2 + h * 0.008f, sy2 + h * 0.0025f, p)
        }
        // gaivotas
        p.style = Paint.Style.STROKE; p.strokeWidth = h * 0.004f; p.color = 0xAA2A2F45.toInt(); p.strokeCap = Paint.Cap.ROUND
        for (k in 0 until 3) {
            val bx = ((t * (18f + k * 7f) + k * w * 0.3f) % (w * 1.2f)) - w * 0.1f
            val by = h * (0.2f + 0.05f * k) + sin(t * 1.3f + k) * h * 0.01f
            val f = sin(t * 6f + k) * h * 0.008f
            val s = h * 0.016f
            path.reset(); path.moveTo(bx - s, by - f); path.quadTo(bx - s * 0.5f, by - s * 0.6f, bx, by); path.quadTo(bx + s * 0.5f, by - s * 0.6f, bx + s, by - f)
            c.drawPath(path, p)
        }
        p.style = Paint.Style.FILL
        postInvalidateOnAnimation()
    }

    private fun paintStatic(c: Canvas, w: Float, h: Float) {
        val hz = h * 0.66f
        // céu do fim da tarde
        var top = lerp(0xFF3E6FC6.toInt(), 0xFF2A2E6E.toInt(), dusk); var mid = lerp(0xFF8EC5F0.toInt(), 0xFFE58A7C.toInt(), dusk); var low = lerp(0xFFFFE2B0.toInt(), 0xFFFFC27A.toInt(), dusk)
        top = lerp(top, 0xFF070B24.toInt(), night); mid = lerp(mid, 0xFF1B2452.toInt(), night); low = lerp(low, 0xFF3A3F72.toInt(), night)
        p.shader = LinearGradient(0f, 0f, 0f, hz, intArrayOf(top, mid, low), floatArrayOf(0f, 0.62f, 1f), Shader.TileMode.CLAMP)
        c.drawRect(0f, 0f, w, hz + 2f, p); p.shader = null
        // sol com halo
        val sx = w * sunU; val sy = hz - h * sunV
        if (night > 0.5f) {
            // estrelas e lua
            val rs = java.util.Random(3)
            for (k in 0 until 140) { fill(Color.argb((60 + rs.nextInt(150) * night).toInt().coerceIn(0, 255), 255, 255, 240)); c.drawCircle(w * rs.nextFloat(), hz * 0.85f * rs.nextFloat(), h * (0.0015f + rs.nextFloat() * 0.0025f), p) }
            val mx = w * 0.72f; val my = h * 0.17f
            p.maskFilter = BlurMaskFilter(h * 0.08f, BlurMaskFilter.Blur.NORMAL); p.color = 0x55CFE0FF; c.drawCircle(mx, my, h * 0.08f, p); p.maskFilter = null
            fill(0xFFF4F1E4.toInt()); c.drawCircle(mx, my, h * 0.045f, p)
            fill(0x22000033); c.drawCircle(mx - h * 0.012f, my - h * 0.01f, h * 0.009f, p); c.drawCircle(mx + h * 0.014f, my + h * 0.012f, h * 0.006f, p)
        } else {
            p.maskFilter = BlurMaskFilter(h * 0.12f, BlurMaskFilter.Blur.NORMAL); p.color = lerp(0x88FFF0C0.toInt(), 0x88FFB060.toInt(), dusk); c.drawCircle(sx, sy, h * 0.12f, p); p.maskFilter = null
            fill(lerp(0xFFFFF6D8.toInt(), 0xFFFFC86E.toInt(), dusk)); c.drawCircle(sx, sy, h * 0.07f, p)
        }
        // morros ao fundo
        fill(lerp(0xFF7FA8C9.toInt(), 0xFF8A6E9E.toInt(), dusk))
        path.reset(); path.moveTo(0f, hz); path.cubicTo(w * 0.1f, hz - h * 0.2f, w * 0.25f, hz - h * 0.12f, w * 0.34f, hz - h * 0.18f); path.cubicTo(w * 0.45f, hz - h * 0.26f, w * 0.55f, hz - h * 0.1f, w * 0.7f, hz - h * 0.14f); path.cubicTo(w * 0.82f, hz - h * 0.17f, w * 0.92f, hz - h * 0.08f, w, hz - h * 0.1f); path.lineTo(w, hz); path.close()
        c.drawPath(path, p)
        // prédios em 2 camadas, com janelas acesas
        val rnd = java.util.Random(11)
        for (layer in 0..1) {
            var x = -w * 0.02f
            val base = hz + h * 0.005f
            val colA = if (layer == 0) lerp(0xFF6D8FB8.toInt(), 0xFF6A5A8E.toInt(), dusk) else lerp(0xFF3F5E8C.toInt(), 0xFF3C3566.toInt(), dusk)
            while (x < w * 0.78f) {
                val bw = w * (0.03f + rnd.nextFloat() * 0.045f)
                val bh = h * (if (layer == 0) 0.12f + rnd.nextFloat() * 0.22f else 0.06f + rnd.nextFloat() * 0.16f)
                fill(colA); c.drawRect(x, base - bh, x + bw, base, p)
                fill(shade(colA, 1.18f)); c.drawRect(x, base - bh, x + bw * 0.18f, base, p)
                if (rnd.nextFloat() < 0.3f) { fill(shade(colA, 0.8f)); c.drawRect(x + bw * 0.3f, base - bh - h * 0.015f, x + bw * 0.7f, base - bh, p) }
                fill(if (layer == 0) 0x55FFF1C1 else 0xAAFFE7A0.toInt())
                var yy = base - bh + h * 0.012f
                while (yy < base - h * 0.012f) { var xx = x + bw * 0.25f; while (xx < x + bw - bw * 0.15f) { if (rnd.nextFloat() < 0.45f) c.drawRect(xx, yy, xx + bw * 0.12f, yy + h * 0.01f, p); xx += bw * 0.22f }; yy += h * 0.022f }
                x += bw + w * (if (layer == 0) 0.004f else 0.012f)
            }
        }
        // antenas e caixas d'água nos telhados mais altos
        val rnd2 = java.util.Random(5)
        for (k in 0 until 14) {
            val x = w * rnd2.nextFloat() * 0.78f; val y = hz - h * (0.18f + rnd2.nextFloat() * 0.12f)
            fill(lerp(0xFF3F5E8C.toInt(), 0xFF3C3566.toInt(), dusk)); c.drawRect(x, y, x + h * 0.004f, y + h * 0.05f, p)
            if (k % 3 == 0) { fill(0xFFFF6B5B.toInt()); c.drawCircle(x + h * 0.002f, y, h * 0.004f, p) }
        }
        // mar com reflexo do sol
        p.shader = LinearGradient(0f, hz, 0f, h, intArrayOf(lerp(0xFF4DA3D6.toInt(), 0xFF5D6FB0.toInt(), dusk), lerp(0xFF2C7FB8.toInt(), 0xFF35468A.toInt(), dusk), 0xFF1F6FA0.toInt()), null, Shader.TileMode.CLAMP)
        c.drawRect(0f, hz, w, h, p); p.shader = null
        for (k in 0 until 14) { fill(Color.argb(140 - k * 8, 255, 236, 180)); val yy = hz + k * h * 0.012f; val ww = w * (0.05f - k * 0.002f); c.drawRect(sx - ww, yy, sx + ww, yy + h * 0.004f, p) }
        // reflexo da cidade na água (faixas que se desfazem)
        for (k in 0 until 18) {
            fill(Color.argb(40 - k * 2, 255, 230, 170)); val yy = hz + h * 0.008f * k
            var x = (k * 37 % 11) * w * 0.004f
            while (x < w * 0.78f) { c.drawRect(x, yy, x + w * 0.02f, yy + h * 0.0025f, p); x += w * (0.035f + (k % 3) * 0.01f) }
        }
        // molhe e farol à direita
        fill(0xFF5B5A63.toInt()); c.drawRect(w * 0.72f, hz - h * 0.01f, w * 0.95f, hz + h * 0.012f, p)
        val lx = w * 0.86f; val base = hz - h * 0.01f
        for (k in 0 until 6) {
            val y0 = base - h * 0.035f * k; val y1 = y0 - h * 0.035f
            val r0 = h * (0.03f - 0.0025f * k); val r1 = h * (0.03f - 0.0025f * (k + 1))
            fill(if (k % 2 == 0) 0xFFF5F2EC.toInt() else 0xFFD63B35.toInt())
            path.reset(); path.moveTo(lx - r0, y0); path.lineTo(lx - r1, y1); path.lineTo(lx + r1, y1); path.lineTo(lx + r0, y0); path.close(); c.drawPath(path, p)
        }
        val ly = base - h * 0.21f
        fill(0xFF2A2F3A.toInt()); c.drawRect(lx - h * 0.02f, ly + h * 0.004f, lx + h * 0.02f, ly + h * 0.01f, p)
        fill(0xFFFFF4C2.toInt()); c.drawRect(lx - h * 0.012f, ly - h * 0.02f, lx + h * 0.012f, ly + h * 0.004f, p)
        fill(0xFFD63B35.toInt()); path.reset(); path.moveTo(lx - h * 0.016f, ly - h * 0.02f); path.lineTo(lx, ly - h * 0.04f); path.lineTo(lx + h * 0.016f, ly - h * 0.02f); path.close(); c.drawPath(path, p)
        // areia
        p.shader = LinearGradient(0f, h * 0.84f, 0f, h, 0xFFF3DDAA.toInt(), 0xFFE5C68A.toInt(), Shader.TileMode.CLAMP)
        path.reset(); path.moveTo(0f, h * 0.86f); path.cubicTo(w * 0.3f, h * 0.82f, w * 0.6f, h * 0.9f, w, h * 0.85f); path.lineTo(w, h); path.lineTo(0f, h); path.close()
        c.drawPath(path, p); p.shader = null
        // calçadão em ondas (pedra portuguesa) na beira, com postes
        val cz0 = h * 0.94f
        fill(0xFFF4F1EA.toInt()); c.drawRect(0f, cz0, w, h, p)
        fill(0xFF2E2E34.toInt())
        var wy = cz0 + h * 0.012f
        while (wy < h + 4f) {
            path.reset(); path.moveTo(0f, wy)
            var x = 0f
            while (x <= w + h * 0.1f) { path.quadTo(x + h * 0.025f, wy - h * 0.012f, x + h * 0.05f, wy); path.quadTo(x + h * 0.075f, wy + h * 0.012f, x + h * 0.1f, wy); x += h * 0.1f }
            path.lineTo(w + h * 0.1f, wy + h * 0.01f)
            x = w + h * 0.1f
            while (x >= 0f) { path.quadTo(x - h * 0.025f, wy + h * 0.022f, x - h * 0.05f, wy + h * 0.01f); path.quadTo(x - h * 0.075f, wy - h * 0.002f, x - h * 0.1f, wy + h * 0.01f); x -= h * 0.1f }
            path.close(); c.drawPath(path, p)
            wy += h * 0.035f
        }
        fill(0xFFD9D4C8.toInt()); c.drawRect(0f, cz0 - h * 0.006f, w, cz0, p)
        for (k in 0 until 6) {
            val lx2 = w * (0.12f + 0.17f * k)
            fill(0xFF2A2F3A.toInt()); c.drawRect(lx2 - h * 0.003f, cz0 - h * 0.13f, lx2 + h * 0.003f, cz0, p)
            c.drawRect(lx2 - h * 0.02f, cz0 - h * 0.13f, lx2 + h * 0.02f, cz0 - h * 0.125f, p)
            fill(0xFFFFF0C0.toInt()); c.drawCircle(lx2 - h * 0.02f, cz0 - h * 0.12f, h * 0.007f, p); c.drawCircle(lx2 + h * 0.02f, cz0 - h * 0.12f, h * 0.007f, p)
        }
        // coqueiros nas pontas
        palm(c, w * 0.06f, h * 0.98f, h * 0.42f, -8f); palm(c, w * 0.13f, h, h * 0.32f, 6f); palm(c, w * 0.95f, h, h * 0.36f, 10f)
        // guarda-sóis
        umb(c, w * 0.30f, h * 0.93f, h * 0.06f, 0xFFE8473D.toInt()); umb(c, w * 0.72f, h * 0.95f, h * 0.055f, 0xFFF2B33D.toInt())
        // vinheta para o texto ler bem
        p.shader = LinearGradient(0f, 0f, w * 0.45f, 0f, 0x88102040.toInt(), 0x00102040, Shader.TileMode.CLAMP); c.drawRect(0f, 0f, w * 0.45f, h, p); p.shader = null
    }

    private fun shade(cc: Int, k: Float): Int = Color.rgb(((cc shr 16 and 255) * k).toInt().coerceIn(0, 255), ((cc shr 8 and 255) * k).toInt().coerceIn(0, 255), ((cc and 255) * k).toInt().coerceIn(0, 255))

    private fun palm(c: Canvas, x: Float, y: Float, hh: Float, lean: Float) {
        p.style = Paint.Style.STROKE; p.strokeCap = Paint.Cap.ROUND; p.color = 0xFF6B4A2E.toInt(); p.strokeWidth = hh * 0.05f; p.shader = null
        val tx = x + lean / 100f * hh * 3f; val ty = y - hh
        path.reset(); path.moveTo(x, y); path.quadTo(x + (tx - x) * 0.2f, y - hh * 0.5f, tx, ty); c.drawPath(path, p)
        p.style = Paint.Style.FILL
        for (k in 0 until 8) {
            val a = -170f + k * 22f + lean
            c.save(); c.translate(tx, ty); c.rotate(a)
            p.color = if (k % 2 == 0) 0xFF2E7D4F.toInt() else 0xFF3E9A5E.toInt()
            path.reset(); path.moveTo(0f, 0f); path.quadTo(hh * 0.22f, -hh * 0.12f, hh * 0.42f, hh * 0.06f); path.quadTo(hh * 0.2f, -hh * 0.02f, 0f, 0f); path.close()
            c.drawPath(path, p); c.restore()
        }
        p.color = 0xFF7A5A2E.toInt(); c.drawCircle(tx - hh * 0.02f, ty + hh * 0.02f, hh * 0.025f, p); c.drawCircle(tx + hh * 0.02f, ty + hh * 0.025f, hh * 0.025f, p)
    }

    private fun umb(c: Canvas, x: Float, y: Float, r: Float, col: Int) {
        p.style = Paint.Style.STROKE; p.strokeWidth = r * 0.06f; p.color = 0xFFEDEDED.toInt(); c.drawLine(x, y, x + r * 0.1f, y - r * 1.4f, p)
        p.style = Paint.Style.FILL
        for (k in 0 until 4) {
            p.color = if (k % 2 == 0) col else 0xFFFFFFFF.toInt()
            c.drawArc(RectF(x - r + r * 0.1f, y - r * 1.9f, x + r + r * 0.1f, y - r * 0.9f), 180f + k * 45f, 45f, true, p)
        }
    }
}

/** Logo do Meu Lar: casinha com telhado, porta e janela acesa (desenhada, sem imagem). */
class HouseLogo(ctx: Context) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val path = Path()
    private val t0 = System.nanoTime()
    var animate = true
    override fun onDraw(c: Canvas) {
        val w = width.toFloat(); val h = height.toFloat()
        val t = (System.nanoTime() - t0) / 1e9f
        val s = min(w, h)
        val ox = (w - s) / 2; val oy = (h - s) / 2 + (if (animate) sin(t * 2f) * s * 0.02f else 0f)
        p.color = 0x33000000; c.drawOval(RectF(ox + s * 0.18f, oy + s * 0.9f, ox + s * 0.82f, oy + s * 0.98f), p)
        p.color = 0xFFFFF8EE.toInt(); c.drawRoundRect(RectF(ox + s * 0.2f, oy + s * 0.45f, ox + s * 0.8f, oy + s * 0.92f), s * 0.04f, s * 0.04f, p)
        p.color = 0xFFE8553E.toInt(); path.reset(); path.moveTo(ox + s * 0.08f, oy + s * 0.5f); path.lineTo(ox + s * 0.5f, oy + s * 0.12f); path.lineTo(ox + s * 0.92f, oy + s * 0.5f); path.lineTo(ox + s * 0.82f, oy + s * 0.56f); path.lineTo(ox + s * 0.5f, oy + s * 0.27f); path.lineTo(ox + s * 0.18f, oy + s * 0.56f); path.close(); c.drawPath(path, p)
        p.color = 0xFFB83A2A.toInt(); c.drawRect(ox + s * 0.64f, oy + s * 0.2f, ox + s * 0.73f, oy + s * 0.38f, p)
        p.color = 0xFF2F6FB0.toInt(); c.drawRoundRect(RectF(ox + s * 0.42f, oy + s * 0.64f, ox + s * 0.58f, oy + s * 0.92f), s * 0.03f, s * 0.03f, p)
        val glow = if (animate) 0.75f + 0.25f * sin(t * 3f) else 1f
        p.color = Color.argb((255 * glow).toInt(), 255, 214, 102); c.drawRect(ox + s * 0.26f, oy + s * 0.6f, ox + s * 0.37f, oy + s * 0.71f, p); c.drawRect(ox + s * 0.63f, oy + s * 0.6f, ox + s * 0.74f, oy + s * 0.71f, p)
        p.color = 0xFF8E5A2E.toInt(); c.drawCircle(ox + s * 0.545f, oy + s * 0.79f, s * 0.015f, p)
        if (animate) postInvalidateOnAnimation()
    }
}

/** Fundo do menu: céu pastel em degradê, bolhas de luz (bokeh) subindo devagar, morros e a orla em silhueta clara. */
class SoftScene(ctx: Context) : View(ctx) {
    private var cache: Bitmap? = null
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val path = Path()
    private val t0 = System.nanoTime()
    override fun onSizeChanged(w: Int, h: Int, ow: Int, oh: Int) { cache?.recycle(); cache = null }
    override fun onDraw(c: Canvas) {
        val w = width.toFloat(); val h = height.toFloat()
        if (w <= 0f || h <= 0f) return
        var bmp = cache
        if (bmp == null) { bmp = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888); paintStatic(Canvas(bmp), w, h); cache = bmp }
        c.drawBitmap(bmp, 0f, 0f, null)
        val t = (System.nanoTime() - t0) / 1e9f
        // bokeh: círculos claros subindo e pulsando bem devagar
        for (k in 0 until 14) {
            val sx = w * ((k * 0.137f + 0.05f) % 1f)
            val sp = 6f + (k % 5) * 3f
            val y = h - ((t * sp + k * h * 0.27f) % (h * 1.2f))
            val r = h * (0.02f + 0.035f * ((k * 7) % 5) / 4f)
            val a = (0.10f + 0.10f * sin(t * 0.6f + k)) * (y / h).coerceIn(0f, 1f)
            p.shader = null; p.color = Color.argb((255 * a).toInt().coerceIn(0, 255), 255, 255, 255)
            c.drawCircle(sx + sin(t * 0.3f + k) * h * 0.02f, y, r, p)
        }
        postInvalidateOnAnimation()
    }
    private fun paintStatic(c: Canvas, w: Float, h: Float) {
        p.shader = LinearGradient(0f, 0f, 0f, h, intArrayOf(0xFF8FD3F0.toInt(), 0xFFC4EAF8.toInt(), 0xFFEAF7FC.toInt()), floatArrayOf(0f, 0.55f, 1f), Shader.TileMode.CLAMP)
        c.drawRect(0f, 0f, w, h, p); p.shader = null
        // brilho do sol suave no alto à direita
        p.shader = android.graphics.RadialGradient(w * 0.78f, h * 0.18f, h * 0.6f, intArrayOf(0x88FFFFFF.toInt(), 0x00FFFFFF), null, Shader.TileMode.CLAMP)
        c.drawRect(0f, 0f, w, h, p); p.shader = null
        // faixas curvas claras (como um teto/arcos), bem leves
        p.style = Paint.Style.STROKE; p.strokeWidth = h * 0.012f
        for (k in 0 until 3) { p.color = Color.argb(40 - k * 10, 255, 255, 255); c.drawArc(RectF(-w * 0.4f, h * (0.08f + k * 0.07f), w * 1.4f, h * (1.6f + k * 0.07f)), 180f, 180f, false, p) }
        p.style = Paint.Style.FILL
        // morros e orla em silhueta pastel
        val hz = h * 0.72f
        p.color = 0xFFB3DDEE.toInt()
        path.reset(); path.moveTo(0f, hz); path.cubicTo(w * 0.15f, hz - h * 0.16f, w * 0.3f, hz - h * 0.06f, w * 0.42f, hz - h * 0.12f); path.cubicTo(w * 0.55f, hz - h * 0.2f, w * 0.7f, hz - h * 0.04f, w, hz - h * 0.09f); path.lineTo(w, hz); path.close(); c.drawPath(path, p)
        val rnd = java.util.Random(4)
        var x = w * 0.02f
        p.color = 0xFFA4D3E8.toInt()
        while (x < w * 0.7f) {
            val bw = w * (0.025f + rnd.nextFloat() * 0.03f); val bh = h * (0.05f + rnd.nextFloat() * 0.14f)
            c.drawRoundRect(RectF(x, hz - bh, x + bw, hz + 2f), h * 0.004f, h * 0.004f, p)
            x += bw + w * 0.006f
        }
        // farol pequeno à direita
        val lx = w * 0.88f
        p.color = 0xFFFFFFFF.toInt(); c.drawRect(lx - h * 0.012f, hz - h * 0.15f, lx + h * 0.012f, hz, p)
        p.color = 0xFFF4A3A0.toInt(); for (k in 0 until 3) c.drawRect(lx - h * 0.012f, hz - h * (0.03f + 0.05f * k), lx + h * 0.012f, hz - h * (0.055f + 0.05f * k), p)
        p.color = 0xFFFFF4C8.toInt(); c.drawCircle(lx, hz - h * 0.16f, h * 0.012f, p)
        // mar e areia em faixas suaves
        p.shader = LinearGradient(0f, hz, 0f, h, intArrayOf(0xFF9ED6EC.toInt(), 0xFFCFEAF4.toInt()), null, Shader.TileMode.CLAMP); c.drawRect(0f, hz, w, h, p); p.shader = null
        p.color = 0x66FFFFFF; for (k in 0 until 4) { val yy = hz + h * (0.03f + k * 0.05f); c.drawRoundRect(RectF(w * (0.1f + k * 0.13f), yy, w * (0.3f + k * 0.13f), yy + h * 0.006f), h, h, p) }
        p.shader = LinearGradient(0f, h * 0.86f, 0f, h, 0xFFF7EBD3.toInt(), 0xFFF1DFBE.toInt(), Shader.TileMode.CLAMP)
        path.reset(); path.moveTo(0f, h * 0.9f); path.cubicTo(w * 0.3f, h * 0.86f, w * 0.65f, h * 0.93f, w, h * 0.88f); path.lineTo(w, h); path.lineTo(0f, h); path.close(); c.drawPath(path, p); p.shader = null
    }
}

@SuppressLint("ViewConstructor")
class MainMenu(ctx: Context, version: String, household: String, money: String,
               private val onPlay: () -> Unit, private val onCreator: () -> Unit, private val onNews: () -> Unit, private val onSettings: () -> Unit) : FrameLayout(ctx) {
    companion object {
        /** última foto do personagem (aparece na hora quando o menu abre de novo) */
        @Volatile var lastSim: Bitmap? = null
    }
    private val d = resources.displayMetrics.density
    private fun dp(v: Float) = (v * d).toInt()
    val sim: ImageView = ImageView(ctx)
    val face: ImageView = ImageView(ctx)      // (mantido para quem atualiza o retrato; não aparece no menu)
    private val stage = FrameLayout(ctx)

    init {
        isClickable = true
        setBackgroundColor(0xFF8FD3F0.toInt())
        // fundo: a cidade à beira-mar ilustrada, com a luz da hora real (tarde vira pôr do sol)
        val hr = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY) + java.util.Calendar.getInstance().get(java.util.Calendar.MINUTE) / 60f
        // manhã (sol baixo à esquerda), meio-dia (sol alto), fim de tarde (pôr do sol à direita), noite (lua e estrelas)
        val night = when { hr >= 19.5f || hr < 5.5f -> 1f; hr >= 18.5f -> hr - 18.5f; hr < 6.5f -> 6.5f - hr; else -> 0f }.coerceIn(0f, 1f)
        val dusk = when { hr in 16.5f..19.5f -> 1f - kotlin.math.abs(hr - 18.3f) / 1.8f; hr in 5.5f..7.5f -> 1f - kotlin.math.abs(hr - 6.3f) / 1.2f; else -> 0f }.coerceIn(0f, 1f)
        val dayK = ((hr - 6f) / 12.5f).coerceIn(0f, 1f)
        val sunU = 0.12f + 0.76f * dayK; val sunV = 0.04f + 0.42f * kotlin.math.sin(dayK * Math.PI.toFloat())
        addView(CityScene(ctx, dusk, night, sunU, sunV), LayoutParams(-1, -1))
        // véu claro no meio (o texto e os botões ficam legíveis sem caixas nem contornos)
        addView(object : View(ctx) {
            val p = Paint(Paint.ANTI_ALIAS_FLAG)
            override fun onDraw(c: Canvas) {
                val w = width.toFloat(); val h = height.toFloat()
                p.shader = android.graphics.RadialGradient(w / 2f, h * 0.52f, w * 0.42f, intArrayOf(0xC8F4FBFF.toInt(), 0x80EAF6FC.toInt(), 0x00EAF6FC), floatArrayOf(0f, 0.6f, 1f), Shader.TileMode.CLAMP)
                c.drawRect(0f, 0f, w, h, p)
            }
        }, LayoutParams(-1, -1))
        val col = LinearLayout(ctx); col.orientation = LinearLayout.VERTICAL; col.gravity = Gravity.CENTER_HORIZONTAL
        val logo = LinearLayout(ctx); logo.orientation = LinearLayout.HORIZONTAL; logo.gravity = Gravity.CENTER_VERTICAL
        logo.addView(HouseLogo(ctx), LinearLayout.LayoutParams(dp(60f), dp(60f)))
        val lt = LinearLayout(ctx); lt.orientation = LinearLayout.VERTICAL
        lt.addView(txt("MEU", 14f, 0xFF2D7FA8.toInt(), MenuPal.BLACK).also { it.includeFontPadding = false; it.letterSpacing = 0.4f })
        lt.addView(txt("LAR", 44f, 0xFF16466E.toInt(), MenuPal.BLACK).also { it.includeFontPadding = false; it.setShadowLayer(10f, 0f, 3f, 0x55FFFFFF); it.letterSpacing = 0.06f })
        logo.addView(lt, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(12f) })
        col.addView(logo, LinearLayout.LayoutParams(-2, -2))
        col.addView(txt("A vida na cidade à beira-mar", 13f, 0xFF2F6E92.toInt(), MenuPal.TITLE).also { it.gravity = Gravity.CENTER }, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(2f); it.bottomMargin = dp(18f) })
        val play = PillButton(ctx, "JOGAR", 0, 0xFF5FD3A0.toInt(), 0xFF22A67A.toInt(), Color.WHITE); pressable(play) { onPlay() }
        col.addView(play, LinearLayout.LayoutParams(dp(270f), dp(58f)))
        val b1 = PillButton(ctx, "Personagem", 1, 0xF7FFFFFF.toInt(), 0xEEF1F8FC.toInt(), 0xFF1D4D72.toInt()); pressable(b1) { onCreator() }
        col.addView(b1, LinearLayout.LayoutParams(dp(270f), dp(48f)).also { it.topMargin = dp(12f) })
        val b2 = PillButton(ctx, "Configurações", 2, 0xF7FFFFFF.toInt(), 0xEEF1F8FC.toInt(), 0xFF1D4D72.toInt()); pressable(b2) { onSettings() }
        col.addView(b2, LinearLayout.LayoutParams(dp(270f), dp(48f)).also { it.topMargin = dp(9f) })
        val b3 = PillButton(ctx, "Sair", 3, 0xF7FFFFFF.toInt(), 0xEEF1F8FC.toInt(), 0xFF1D4D72.toInt()); pressable(b3) { (context as? android.app.Activity)?.finish() }
        col.addView(b3, LinearLayout.LayoutParams(dp(270f), dp(48f)).also { it.topMargin = dp(9f) })
        addView(col, LayoutParams(-2, -2, Gravity.CENTER))
        addView(txt(version, 11f, 0xAA16466E.toInt(), MenuPal.TITLE), LayoutParams(-2, -2, Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(16f), dp(10f)) })
        col.alpha = 0f; col.translationY = dp(18f).toFloat()
        col.animate().alpha(1f).translationY(0f).setDuration(600).setStartDelay(120).start()
    }

    /** Foto do personagem chegou: recorta as bordas transparentes (fica centrado e com os pés na plataforma) e guarda. */
    fun setSim(b: Bitmap) {
        val t = trim(b)
        val first = sim.drawable == null
        lastSim = t
        showSim(t, first)
        Thread { try { context.openFileOutput("menu_sim.png", Context.MODE_PRIVATE).use { t.compress(Bitmap.CompressFormat.PNG, 100, it) } } catch (e: Throwable) { } }.start()
    }

    private fun showSim(b: Bitmap, anim: Boolean) {
        sim.setImageBitmap(b)
        if (anim || sim.alpha < 1f) { sim.translationY = dp(12f).toFloat(); sim.animate().alpha(1f).translationY(0f).setDuration(420).start() }
    }

    private fun loadCached(): Bitmap? = try { context.openFileInput("menu_sim.png").use { android.graphics.BitmapFactory.decodeStream(it) }?.also { lastSim = it } } catch (e: Throwable) { null }

    private fun trim(b: Bitmap): Bitmap {
        val w = b.width; val h = b.height
        if (w <= 0 || h <= 0) return b
        val px = IntArray(w * h); b.getPixels(px, 0, w, 0, 0, w, h)
        var x0 = w; var x1 = -1; var y0 = h; var y1 = -1
        for (y in 0 until h) { val o = y * w; for (x in 0 until w) if ((px[o + x] ushr 24) > 40) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y } }
        if (x1 < 0) return b
        return Bitmap.createBitmap(b, x0, y0, x1 - x0 + 1, y1 - y0 + 1)
    }

    private fun txt(s: String, size: Float, col: Int, tf: Typeface): TextView {
        val t = TextView(context); t.text = s; t.textSize = size; t.setTextColor(col); t.typeface = tf
        return t
    }

    private fun pressable(v: View, act: () -> Unit) {
        v.setOnTouchListener { vv, e ->
            when (e.actionMasked) {
                MotionEvent.ACTION_DOWN -> vv.animate().scaleX(0.97f).scaleY(0.97f).alpha(0.9f).setDuration(70).start()
                MotionEvent.ACTION_UP -> { vv.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(110).start(); if (e.x in 0f..vv.width.toFloat() && e.y in 0f..vv.height.toFloat()) act() }
                MotionEvent.ACTION_CANCEL -> vv.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(110).start()
            }
            true
        }
    }
}

/** Botão em pílula sem contorno: degradê suave, sombra difusa embaixo, brilho no alto, ícone simples e texto centrado. */
class PillButton(ctx: Context, private val title: String, private val icon: Int, private val c0: Int, private val c1: Int, private val ink: Int) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val path = Path()
    init { setLayerType(LAYER_TYPE_SOFTWARE, null) }
    override fun onDraw(c: Canvas) {
        val w = width.toFloat(); val h = height.toFloat(); val m = h * 0.1f
        val box = RectF(m, m * 0.6f, w - m, h - m * 1.4f); val r = box.height() / 2f
        p.maskFilter = BlurMaskFilter(h * 0.14f, BlurMaskFilter.Blur.NORMAL); p.color = 0x2A12415F
        c.drawRoundRect(RectF(box.left + h * 0.08f, box.top + h * 0.16f, box.right - h * 0.08f, box.bottom + h * 0.1f), r, r, p); p.maskFilter = null
        p.shader = LinearGradient(0f, box.top, 0f, box.bottom, c0, c1, Shader.TileMode.CLAMP); c.drawRoundRect(box, r, r, p); p.shader = null
        p.shader = LinearGradient(0f, box.top, 0f, box.centerY(), 0x55FFFFFF, 0x00FFFFFF, Shader.TileMode.CLAMP)
        c.drawRoundRect(RectF(box.left + r * 0.4f, box.top + h * 0.04f, box.right - r * 0.4f, box.centerY()), r, r, p); p.shader = null
        p.typeface = MenuPal.BLACK; p.textSize = box.height() * (if (icon == 0) 0.42f else 0.36f); p.color = ink; p.textAlign = Paint.Align.CENTER
        val tw = p.measureText(title); val iconS = box.height() * 0.22f; val gap = box.height() * 0.28f
        val tx = box.centerX() + (iconS + gap) / 2f; val ty = box.centerY() - (p.descent() + p.ascent()) / 2f
        c.drawText(title, tx, ty, p)
        val ix = tx - tw / 2f - gap - iconS * 0.5f; val iy = box.centerY(); val s = iconS
        p.color = ink; p.alpha = if (icon == 0) 255 else 200
        when (icon) {
            0 -> { path.reset(); path.moveTo(ix - s * 0.55f, iy - s); path.lineTo(ix + s * 0.95f, iy); path.lineTo(ix - s * 0.55f, iy + s); path.close(); c.drawPath(path, p) }
            1 -> { c.drawCircle(ix, iy - s * 0.42f, s * 0.48f, p); c.drawRoundRect(RectF(ix - s * 0.9f, iy + s * 0.15f, ix + s * 0.9f, iy + s * 1.05f), s * 0.45f, s * 0.45f, p) }
            2 -> { for (k in 0 until 8) { c.save(); c.rotate(k * 45f, ix, iy); c.drawRect(ix - s * 0.2f, iy - s * 1.05f, ix + s * 0.2f, iy - s * 0.6f, p); c.restore() }; c.drawCircle(ix, iy, s * 0.72f, p); p.color = c1; c.drawCircle(ix, iy, s * 0.3f, p) }
            else -> { p.style = Paint.Style.STROKE; p.strokeWidth = s * 0.26f; p.strokeCap = Paint.Cap.ROUND; c.drawArc(RectF(ix - s * 0.8f, iy - s * 0.7f, ix + s * 0.8f, iy + s * 0.9f), -50f, 280f, false, p); c.drawLine(ix, iy - s, ix, iy, p); p.style = Paint.Style.FILL }
        }
        p.alpha = 255; p.textAlign = Paint.Align.LEFT
    }
}

/** Botão do menu desenhado: cartão branco arredondado com sombra leve, ícone num círculo colorido, título e subtítulo. */
class MenuButton(ctx: Context, private val title: String, private val sub: String, private val icon: Int, private val main: Boolean) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val path = Path()
    init { setLayerType(LAYER_TYPE_SOFTWARE, null) }
    override fun onDraw(c: Canvas) {
        val w = width.toFloat(); val h = height.toFloat(); val r = h * 0.5f
        val m = h * 0.08f
        p.maskFilter = BlurMaskFilter(h * 0.12f, BlurMaskFilter.Blur.NORMAL); p.color = 0x3326506E
        c.drawRoundRect(RectF(m, m * 1.8f, w - m, h - m * 0.2f), r, r, p); p.maskFilter = null
        if (main) p.shader = LinearGradient(0f, 0f, 0f, h, 0xFF8EE08A.toInt(), 0xFF3DB45E.toInt(), Shader.TileMode.CLAMP)
        else p.shader = LinearGradient(0f, 0f, 0f, h, 0xFFFFFFFF.toInt(), 0xFFEFF7FB.toInt(), Shader.TileMode.CLAMP)
        val box = RectF(m, m, w - m, h - m * 1.6f)
        c.drawRoundRect(box, r, r, p); p.shader = null
        p.color = if (main) 0x44FFFFFF else 0xFFFFFFFF.toInt(); c.drawRoundRect(RectF(box.left + h * 0.08f, box.top + h * 0.05f, box.right - h * 0.08f, box.top + box.height() * 0.45f), r, r, p)
        val cx = box.left + box.height() * 0.55f; val cy = box.centerY(); val cr = box.height() * 0.36f
        val iconBg = when (icon) { 0 -> 0x33FFFFFF; 1 -> 0xFFFFB86B.toInt(); 2 -> 0xFF6FC3E8.toInt(); else -> 0xFFF08A8A.toInt() }
        p.color = iconBg; c.drawCircle(cx, cy, cr, p)
        p.color = Color.WHITE
        val s = cr * 0.55f
        when (icon) {
            0 -> { path.reset(); path.moveTo(cx - s * 0.5f, cy - s); path.lineTo(cx + s, cy); path.lineTo(cx - s * 0.5f, cy + s); path.close(); c.drawPath(path, p) }
            1 -> { c.drawCircle(cx, cy - s * 0.45f, s * 0.45f, p); c.drawRoundRect(RectF(cx - s * 0.85f, cy + s * 0.1f, cx + s * 0.85f, cy + s * 1.0f), s * 0.4f, s * 0.4f, p) }
            2 -> { for (k in 0 until 8) { c.save(); c.rotate(k * 45f, cx, cy); c.drawRect(cx - s * 0.18f, cy - s * 1.05f, cx + s * 0.18f, cy - s * 0.6f, p); c.restore() }; c.drawCircle(cx, cy, s * 0.72f, p); p.color = iconBg; c.drawCircle(cx, cy, s * 0.3f, p) }
            else -> { p.style = Paint.Style.STROKE; p.strokeWidth = s * 0.24f; p.strokeCap = Paint.Cap.ROUND; c.drawArc(RectF(cx - s * 0.8f, cy - s * 0.7f, cx + s * 0.8f, cy + s * 0.9f), -50f, 280f, false, p); c.drawLine(cx, cy - s * 1.0f, cx, cy, p); p.style = Paint.Style.FILL }
        }
        val tx = cx + cr + h * 0.22f
        p.typeface = MenuPal.BLACK; p.textSize = box.height() * (if (main) 0.36f else 0.32f); p.color = if (main) Color.WHITE else 0xFF16466E.toInt()
        if (main) p.setShadowLayer(3f, 0f, 1.5f, 0x40000000)
        c.drawText(title, tx, box.top + box.height() * 0.52f, p); p.clearShadowLayer()
        p.typeface = MenuPal.TITLE; p.textSize = box.height() * 0.22f; p.color = if (main) 0xF0FFFFFF.toInt() else 0xFF5A8AA6.toInt()
        c.drawText(sub, tx, box.top + box.height() * 0.8f, p)
        p.typeface = MenuPal.BLACK; p.textSize = box.height() * 0.42f; p.color = if (main) Color.WHITE else 0xFF8DB9CF.toInt()
        c.drawText("›", box.right - box.height() * 0.48f, box.top + box.height() * 0.66f, p)
    }
}

/** Ilustração dos cartões de novidade. kind: 0 cidade, 1 praia e farol, 2 garagem. */
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
                val lx = w * 0.78f
                p.color = 0xFF5B5A63.toInt(); c.drawRect(w * 0.6f, h * 0.6f, w * 0.95f, h * 0.66f, p)
                for (k in 0 until 5) { p.color = if (k % 2 == 0) 0xFFFFFFFF.toInt() else 0xFFD63B35.toInt(); c.drawRect(lx - h * 0.06f + k * h * 0.005f, h * 0.6f - (k + 1) * h * 0.09f, lx + h * 0.06f - k * h * 0.005f, h * 0.6f - k * h * 0.09f, p) }
                p.color = 0xFFFFF4C2.toInt(); c.drawRect(lx - h * 0.035f, h * 0.06f, lx + h * 0.035f, h * 0.15f, p)
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
            }
        }
    }
}

/** Tela de carregamento: a cidade à beira-mar ao entardecer (animada), logo da casinha, etapa, barra e dicas. */
@SuppressLint("ViewConstructor")
class LoadingScreen(ctx: Context, private val progress: () -> Float, private val onDone: () -> Unit) : FrameLayout(ctx) {
    private val d = resources.displayMetrics.density
    private fun dp(v: Float) = (v * d).toInt()
    private val tips = arrayOf(
        "Toque no botão do mapa para ver a cidade inteira e ligar o GPS.",
        "Na loja, aba Veículos: escolha seu carro ou moto. Ele fica na rua em frente de casa.",
        "Chegue perto do seu veículo e toque em Dirigir.",
        "Dá para entrar nas casas, lojas e prédios.",
        "Os molhes da praia levam até os dois faróis. Suba a escada da areia!",
        "As barracas da praia têm cadeiras e guarda-sóis para todo mundo.",
        "Casas e terrenos com placa vermelha estão à venda.",
        "Os carros param no sinal vermelho. Atravesse na faixa!")
    private val stage: TextView
    private val tip: TextView
    private val pct: TextView
    private val bar: View
    private val barW: Int
    private var shown = 0f
    private var finished = false
    private var tipIdx = (Math.random() * tips.size).toInt()
    private var lastTip = 0L
    private var lastTarget = -1f
    private var lastMove = System.currentTimeMillis()

    init {
        isClickable = true
        setBackgroundColor(0xFF2A2E6E.toInt())
        addView(SoftScene(ctx), LayoutParams(-1, -1))
        // véu escuro embaixo para o texto
        addView(View(ctx).also { it.background = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(0x00000000, 0x00000000, 0x55FFFFFF)) }, LayoutParams(-1, -1))
        val logo = LinearLayout(ctx); logo.orientation = LinearLayout.HORIZONTAL; logo.gravity = Gravity.CENTER_VERTICAL
        logo.addView(HouseLogo(ctx), LinearLayout.LayoutParams(dp(64f), dp(64f)))
        val lt = LinearLayout(ctx); lt.orientation = LinearLayout.VERTICAL
        lt.addView(TextView(ctx).also { it.text = "MEU"; it.textSize = 15f; it.setTextColor(0xFF2D7FA8.toInt()); it.typeface = MenuPal.BLACK; it.letterSpacing = 0.3f; it.includeFontPadding = false })
        lt.addView(TextView(ctx).also { it.text = "LAR"; it.textSize = 42f; it.setTextColor(0xFF16466E.toInt()); it.typeface = MenuPal.BLACK; it.includeFontPadding = false; it.setShadowLayer(12f, 0f, 4f, 0x99001133.toInt()) })
        logo.addView(lt, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(10f) })
        addView(logo, LayoutParams(-2, -2, Gravity.TOP or Gravity.START).also { it.setMargins(dp(28f), dp(20f), 0, 0) })

        val col = LinearLayout(ctx); col.orientation = LinearLayout.VERTICAL; col.gravity = Gravity.START
        stage = TextView(ctx); stage.textSize = 18f; stage.setTextColor(0xFF16466E.toInt()); stage.typeface = MenuPal.BLACK
        stage.setShadowLayer(6f, 0f, 2f, 0x66FFFFFF)
        val row = LinearLayout(ctx); row.orientation = LinearLayout.HORIZONTAL; row.gravity = Gravity.BOTTOM
        row.addView(stage, LinearLayout.LayoutParams(0, -2, 1f))
        pct = TextView(ctx); pct.textSize = 15f; pct.setTextColor(0xFF2D9E5A.toInt()); pct.typeface = MenuPal.BLACK
        row.addView(pct)
        barW = (resources.displayMetrics.widthPixels * 0.62f).toInt()
        col.addView(row, LinearLayout.LayoutParams(barW, -2))
        val track = FrameLayout(ctx)
        val tg = GradientDrawable(); tg.cornerRadius = dp(8f).toFloat(); tg.setColor(0xCCFFFFFF.toInt()); tg.setStroke(dp(1.5f), 0x557FB6D0)
        track.background = tg
        track.setPadding(dp(3f), dp(3f), dp(3f), dp(3f))
        bar = View(ctx)
        val bg = GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, intArrayOf(0xFF3DB45E.toInt(), 0xFF8EE08A.toInt())); bg.cornerRadius = dp(5f).toFloat()
        bar.background = bg
        track.addView(bar, LayoutParams(0, -1))
        col.addView(track, LinearLayout.LayoutParams(barW, dp(16f)).also { it.topMargin = dp(8f) })
        tip = TextView(ctx); tip.textSize = 13f; tip.setTextColor(0xFF3C6F8C.toInt()); tip.typeface = MenuPal.TITLE
        col.addView(tip, LinearLayout.LayoutParams(barW, -2).also { it.topMargin = dp(10f) })
        addView(col, LayoutParams(-2, -2, Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL).also { it.bottomMargin = dp(26f) })
        tip.text = "Dica: " + tips[tipIdx]
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
                val w = ((barW - dp(6f)) * shown).toInt()
                bar.layoutParams = bar.layoutParams.also { it.width = maxOf(dp(10f), w) }
                bar.requestLayout()
                pct.text = "${(shown * 100).toInt()}%"
                stage.text = when {
                    shown < 0.12f -> "Abrindo o mapa da cidade"
                    shown < 0.35f -> "Asfaltando as ruas"
                    shown < 0.55f -> "Erguendo casas e prédios"
                    shown < 0.72f -> "Mobiliando os interiores"
                    shown < 0.86f -> "Arrumando a praia"
                    shown < 0.99f -> "Ligando o trânsito"
                    else -> "Pronto!"
                }
                val now = System.currentTimeMillis()
                if (now - lastTip > 4500L) {
                    lastTip = now; tipIdx = (tipIdx + 1) % tips.size
                    tip.animate().alpha(0f).setDuration(220).withEndAction { tip.text = "Dica: " + tips[tipIdx]; tip.animate().alpha(1f).setDuration(260).start() }.start()
                }
                if (shown >= 1f) { finished = true; postDelayed({ onDone() }, 400); return }
                postDelayed(this, 33)
            }
        })
    }
}
