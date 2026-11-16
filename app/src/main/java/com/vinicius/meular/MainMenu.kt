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
class CityScene(ctx: Context, private val dusk: Float = 0f) : View(ctx) {
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
        val top = lerp(0xFF3E6FC6.toInt(), 0xFF2A2E6E.toInt(), dusk); val mid = lerp(0xFF8EC5F0.toInt(), 0xFFE58A7C.toInt(), dusk); val low = lerp(0xFFFFE2B0.toInt(), 0xFFFFC27A.toInt(), dusk)
        p.shader = LinearGradient(0f, 0f, 0f, hz, intArrayOf(top, mid, low), floatArrayOf(0f, 0.62f, 1f), Shader.TileMode.CLAMP)
        c.drawRect(0f, 0f, w, hz + 2f, p); p.shader = null
        // sol com halo
        val sx = w * 0.62f; val sy = hz - h * 0.06f
        p.maskFilter = BlurMaskFilter(h * 0.12f, BlurMaskFilter.Blur.NORMAL); p.color = 0x88FFD27A.toInt(); c.drawCircle(sx, sy, h * 0.12f, p); p.maskFilter = null
        fill(0xFFFFE9A8.toInt()); c.drawCircle(sx, sy, h * 0.07f, p)
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
        // mar com reflexo do sol
        p.shader = LinearGradient(0f, hz, 0f, h, intArrayOf(lerp(0xFF4DA3D6.toInt(), 0xFF5D6FB0.toInt(), dusk), lerp(0xFF2C7FB8.toInt(), 0xFF35468A.toInt(), dusk), 0xFF1F6FA0.toInt()), null, Shader.TileMode.CLAMP)
        c.drawRect(0f, hz, w, h, p); p.shader = null
        for (k in 0 until 14) { fill(Color.argb(140 - k * 8, 255, 236, 180)); val yy = hz + k * h * 0.012f; val ww = w * (0.05f - k * 0.002f); c.drawRect(sx - ww, yy, sx + ww, yy + h * 0.004f, p) }
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

@SuppressLint("ViewConstructor")
class MainMenu(ctx: Context, version: String, household: String, money: String,
               private val onPlay: () -> Unit, private val onCreator: () -> Unit, private val onNews: () -> Unit, private val onSettings: () -> Unit) : FrameLayout(ctx) {
    private val d = resources.displayMetrics.density
    private fun dp(v: Float) = (v * d).toInt()
    val sim: ImageView = ImageView(ctx)
    val face: ImageView = ImageView(ctx)
    private val simBox = FrameLayout(ctx)
    private val news = arrayOf(
        Triple(0, "A cidade à beira-mar", "Ruas, prédios, lojas e casas para morar."),
        Triple(1, "Praia e faróis", "Calçadão, barracas, quadras e dois faróis para visitar."),
        Triple(2, "Garagem", "Escolha seu carro ou moto na loja e saia dirigindo."))
    private var newsIdx = 0

    init {
        isClickable = true
        setBackgroundColor(0xFF2C6CA8.toInt())
        addView(CityScene(ctx), LayoutParams(-1, -1))
        val dm = resources.displayMetrics
        val H = dm.heightPixels.toFloat()

        // centro: pedestal + personagem com os pés apoiados nele
        val stageW = (H * 0.62f).toInt(); val stageH = (H * 0.9f).toInt()
        addView(simBox, LayoutParams(stageW, stageH, Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL).also { it.leftMargin = dp(60f) })
        val ped = object : View(ctx) {
            val p = Paint(Paint.ANTI_ALIAS_FLAG)
            override fun onDraw(c: Canvas) {
                val w = width.toFloat(); val h = height.toFloat()
                p.color = 0x40000000; c.drawOval(RectF(w * 0.05f, h * 0.45f, w * 0.95f, h * 1.0f), p)
                p.shader = LinearGradient(0f, 0f, 0f, h, 0xFFFFFFFF.toInt(), 0xFFCFE3F2.toInt(), Shader.TileMode.CLAMP)
                c.drawOval(RectF(w * 0.08f, h * 0.2f, w * 0.92f, h * 0.85f), p); p.shader = null
                p.color = 0xFFF2B33D.toInt(); p.style = Paint.Style.STROKE; p.strokeWidth = h * 0.06f
                c.drawOval(RectF(w * 0.08f, h * 0.2f, w * 0.92f, h * 0.85f), p); p.style = Paint.Style.FILL
                p.color = 0x66FFFFFF; c.drawOval(RectF(w * 0.2f, h * 0.3f, w * 0.8f, h * 0.55f), p)
            }
        }
        val pedH = dp(46f)
        simBox.addView(ped, LayoutParams(-1, pedH, Gravity.BOTTOM).also { it.bottomMargin = dp(10f) })
        sim.scaleType = ImageView.ScaleType.FIT_END
        simBox.addView(sim, LayoutParams(-1, -1, Gravity.BOTTOM).also { it.bottomMargin = dp(10f) + (pedH * 0.5f).toInt() })
        sim.alpha = 0f

        // topo esquerdo: logo
        val logo = LinearLayout(ctx); logo.orientation = LinearLayout.HORIZONTAL; logo.gravity = Gravity.CENTER_VERTICAL
        logo.addView(HouseLogo(ctx), LinearLayout.LayoutParams(dp(52f), dp(52f)))
        val lt = LinearLayout(ctx); lt.orientation = LinearLayout.VERTICAL
        lt.addView(txt("MEU", 13f, 0xFFFFE6A8.toInt(), MenuPal.BLACK).also { it.includeFontPadding = false; it.letterSpacing = 0.3f })
        lt.addView(txt("LAR", 34f, Color.WHITE, MenuPal.BLACK).also { it.includeFontPadding = false; it.setShadowLayer(10f, 0f, 3f, 0x88002244.toInt()); it.letterSpacing = 0.06f })
        logo.addView(lt, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(8f) })
        addView(logo, LayoutParams(-2, -2, Gravity.TOP or Gravity.START).also { it.setMargins(dp(24f), dp(14f), 0, 0) })

        // topo direito: perfil (rosto, nome da casa e dinheiro)
        val hi = LinearLayout(ctx); hi.orientation = LinearLayout.HORIZONTAL; hi.gravity = Gravity.CENTER_VERTICAL
        hi.setPadding(dp(6f), dp(5f), dp(16f), dp(5f))
        val hb = GradientDrawable(); hb.cornerRadius = dp(26f).toFloat(); hb.setColor(0x66102A4A); hb.setStroke(dp(1.5f), 0x66FFFFFF); hi.background = hb
        face.scaleType = ImageView.ScaleType.CENTER_CROP
        val fb = GradientDrawable(); fb.shape = GradientDrawable.OVAL; fb.setColor(MenuPal.PALE); fb.setStroke(dp(2f), Color.WHITE); face.background = fb
        face.outlineProvider = object : android.view.ViewOutlineProvider() { override fun getOutline(v: View, o: android.graphics.Outline) { o.setOval(0, 0, v.width, v.height) } }
        face.clipToOutline = true
        hi.addView(face, LinearLayout.LayoutParams(dp(40f), dp(40f)))
        val info = LinearLayout(ctx); info.orientation = LinearLayout.VERTICAL
        info.addView(txt(household, 13f, Color.WHITE, MenuPal.TITLE))
        info.addView(txt("R$ $money", 14f, 0xFFFFE08A.toInt(), MenuPal.BLACK))
        hi.addView(info, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(10f) })
        addView(hi, LayoutParams(-2, -2, Gravity.TOP or Gravity.END).also { it.setMargins(0, dp(14f), dp(18f), 0) })

        // esquerda: menu único (cada opção uma vez)
        val left = LinearLayout(ctx); left.orientation = LinearLayout.VERTICAL
        val play = txt("▶  JOGAR", 24f, Color.WHITE, MenuPal.BLACK); play.gravity = Gravity.CENTER
        play.setShadowLayer(6f, 0f, 2f, 0x66003300)
        val pg = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(0xFF6FD66B.toInt(), 0xFF2FA24C.toInt())); pg.cornerRadius = dp(16f).toFloat(); pg.setStroke(dp(2f), 0xCCFFFFFF.toInt())
        play.background = pg; play.elevation = dp(6f).toFloat()
        pressable(play) { onPlay() }
        left.addView(play, LinearLayout.LayoutParams(dp(230f), dp(58f)))
        left.addView(menuBtn("PERSONAGEM", "Criar e mudar o visual") { onCreator() }, LinearLayout.LayoutParams(dp(230f), dp(50f)).also { it.topMargin = dp(10f) })
        left.addView(menuBtn("NOVIDADES", "O que tem de novo") { onNews() }, LinearLayout.LayoutParams(dp(230f), dp(50f)).also { it.topMargin = dp(8f) })
        left.addView(menuBtn("CONFIGURAÇÕES", "Gráficos, som e controles") { onSettings() }, LinearLayout.LayoutParams(dp(230f), dp(50f)).also { it.topMargin = dp(8f) })
        left.addView(menuBtn("SAIR", "Fechar o jogo") { (context as? android.app.Activity)?.finish() }, LinearLayout.LayoutParams(dp(230f), dp(50f)).also { it.topMargin = dp(8f) })
        addView(left, LayoutParams(-2, -2, Gravity.CENTER_VERTICAL or Gravity.START).also { it.leftMargin = dp(26f); it.topMargin = dp(40f) })

        // direita embaixo: um cartão de novidade que troca sozinho (só informação, sem botões repetidos)
        val card = LinearLayout(ctx); card.orientation = LinearLayout.VERTICAL
        val cg = GradientDrawable(); cg.cornerRadius = dp(14f).toFloat(); cg.setColor(0xF2FFFFFF.toInt()); card.background = cg
        card.elevation = dp(6f).toFloat(); card.clipToOutline = true
        val art = FrameLayout(ctx)
        card.addView(art, LinearLayout.LayoutParams(-1, dp(84f)))
        val ct = txt("", 14f, MenuPal.INK, MenuPal.BLACK); val cb = txt("", 11.5f, 0xFF3F5F95.toInt(), MenuPal.TITLE)
        val inner = LinearLayout(ctx); inner.orientation = LinearLayout.VERTICAL; inner.setPadding(dp(12f), dp(6f), dp(12f), dp(8f))
        inner.addView(ct); inner.addView(cb)
        val dots = LinearLayout(ctx); dots.orientation = LinearLayout.HORIZONTAL
        val dv = ArrayList<View>()
        for (k in news.indices) { val v = View(ctx); dv.add(v); dots.addView(v, LinearLayout.LayoutParams(dp(7f), dp(7f)).also { it.setMargins(0, dp(6f), dp(5f), 0) }) }
        inner.addView(dots)
        card.addView(inner)
        fun show() {
            val n = news[newsIdx]
            art.removeAllViews(); art.addView(CardArt(ctx, n.first), LayoutParams(-1, -1))
            ct.text = n.second.uppercase(); cb.text = n.third
            for ((i, v) in dv.withIndex()) { val g = GradientDrawable(); g.shape = GradientDrawable.OVAL; g.setColor(if (i == newsIdx) MenuPal.INK else 0xFFB8C4DC.toInt()); v.background = g }
        }
        show()
        card.setOnClickListener { newsIdx = (newsIdx + 1) % news.size; show() }
        postDelayed(object : Runnable { override fun run() { if (!isAttachedToWindow) return; newsIdx = (newsIdx + 1) % news.size; card.animate().alpha(0f).setDuration(200).withEndAction { show(); card.animate().alpha(1f).setDuration(260).start() }.start(); postDelayed(this, 6000) } }, 6000)
        addView(card, LayoutParams(dp(220f), -2, Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(18f), dp(16f)) })

        // versão
        val ver = txt(version, 10f, 0xCCFFFFFF.toInt(), Typeface.DEFAULT)
        ver.setPadding(dp(8f), dp(3f), dp(8f), dp(3f))
        val vb = GradientDrawable(); vb.cornerRadius = dp(8f).toFloat(); vb.setColor(0x66102A4A); ver.background = vb
        addView(ver, LayoutParams(-2, -2, Gravity.BOTTOM or Gravity.START).also { it.setMargins(dp(14f), 0, 0, dp(12f)) })

        left.alpha = 0f; left.translationX = -dp(30f).toFloat()
        left.animate().alpha(1f).translationX(0f).setDuration(500).setStartDelay(150).start()
        card.alpha = 0f; card.translationY = dp(20f).toFloat()
        card.animate().alpha(1f).translationY(0f).setDuration(500).setStartDelay(300).start()
    }

    /** Foto do personagem chegou: corta a borda transparente de baixo (senão ele "flutua") e aparece subindo de leve. */
    fun setSim(b: Bitmap) {
        sim.setImageBitmap(trimBottom(b))
        sim.translationY = dp(14f).toFloat()
        sim.animate().alpha(1f).translationY(0f).setDuration(500).start()
    }

    private fun trimBottom(b: Bitmap): Bitmap {
        val w = b.width; val h = b.height
        if (w <= 0 || h <= 0) return b
        val row = IntArray(w)
        var bottom = h - 1
        while (bottom > h / 2) {
            b.getPixels(row, 0, w, 0, bottom, w, 1)
            if (row.any { (it ushr 24) > 40 }) break
            bottom--
        }
        var topR = 0
        while (topR < bottom - 10) {
            b.getPixels(row, 0, w, 0, topR, w, 1)
            if (row.any { (it ushr 24) > 40 }) break
            topR++
        }
        if (bottom >= h - 1 && topR == 0) return b
        return Bitmap.createBitmap(b, 0, topR, w, bottom - topR + 1)
    }

    private fun txt(s: String, size: Float, col: Int, tf: Typeface): TextView {
        val t = TextView(context); t.text = s; t.textSize = size; t.setTextColor(col); t.typeface = tf
        return t
    }

    private fun menuBtn(title: String, sub: String, act: () -> Unit): View {
        val v = LinearLayout(context); v.orientation = LinearLayout.VERTICAL; v.gravity = Gravity.CENTER_VERTICAL
        v.setPadding(dp(16f), 0, dp(12f), 0)
        val g = GradientDrawable(); g.cornerRadius = dp(14f).toFloat(); g.setColor(0x8C10284A.toInt()); g.setStroke(dp(1.5f), 0x55FFFFFF); v.background = g
        v.addView(txt(title, 16f, Color.WHITE, MenuPal.BLACK).also { it.includeFontPadding = false })
        v.addView(txt(sub, 10.5f, 0xCCDDEBFF.toInt(), MenuPal.TITLE).also { it.includeFontPadding = false })
        pressable(v, act)
        return v
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
        addView(CityScene(ctx, 0.85f), LayoutParams(-1, -1))
        // véu escuro embaixo para o texto
        addView(View(ctx).also { it.background = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(0x00000000, 0x00000000, 0xAA0A1530.toInt())) }, LayoutParams(-1, -1))
        val logo = LinearLayout(ctx); logo.orientation = LinearLayout.HORIZONTAL; logo.gravity = Gravity.CENTER_VERTICAL
        logo.addView(HouseLogo(ctx), LinearLayout.LayoutParams(dp(64f), dp(64f)))
        val lt = LinearLayout(ctx); lt.orientation = LinearLayout.VERTICAL
        lt.addView(TextView(ctx).also { it.text = "MEU"; it.textSize = 15f; it.setTextColor(0xFFFFE6A8.toInt()); it.typeface = MenuPal.BLACK; it.letterSpacing = 0.3f; it.includeFontPadding = false })
        lt.addView(TextView(ctx).also { it.text = "LAR"; it.textSize = 42f; it.setTextColor(Color.WHITE); it.typeface = MenuPal.BLACK; it.includeFontPadding = false; it.setShadowLayer(12f, 0f, 4f, 0x99001133.toInt()) })
        logo.addView(lt, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(10f) })
        addView(logo, LayoutParams(-2, -2, Gravity.TOP or Gravity.START).also { it.setMargins(dp(28f), dp(20f), 0, 0) })

        val col = LinearLayout(ctx); col.orientation = LinearLayout.VERTICAL; col.gravity = Gravity.START
        stage = TextView(ctx); stage.textSize = 18f; stage.setTextColor(Color.WHITE); stage.typeface = MenuPal.BLACK
        stage.setShadowLayer(6f, 0f, 2f, 0x88001A33.toInt())
        val row = LinearLayout(ctx); row.orientation = LinearLayout.HORIZONTAL; row.gravity = Gravity.BOTTOM
        row.addView(stage, LinearLayout.LayoutParams(0, -2, 1f))
        pct = TextView(ctx); pct.textSize = 15f; pct.setTextColor(0xFFFFE08A.toInt()); pct.typeface = MenuPal.BLACK
        row.addView(pct)
        barW = (resources.displayMetrics.widthPixels * 0.62f).toInt()
        col.addView(row, LinearLayout.LayoutParams(barW, -2))
        val track = FrameLayout(ctx)
        val tg = GradientDrawable(); tg.cornerRadius = dp(8f).toFloat(); tg.setColor(0x55FFFFFF); tg.setStroke(dp(1.5f), 0xAAFFFFFF.toInt())
        track.background = tg
        track.setPadding(dp(3f), dp(3f), dp(3f), dp(3f))
        bar = View(ctx)
        val bg = GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, intArrayOf(0xFFF2B33D.toInt(), 0xFFFFE08A.toInt())); bg.cornerRadius = dp(5f).toFloat()
        bar.background = bg
        track.addView(bar, LayoutParams(0, -1))
        col.addView(track, LinearLayout.LayoutParams(barW, dp(16f)).also { it.topMargin = dp(8f) })
        tip = TextView(ctx); tip.textSize = 13f; tip.setTextColor(0xFFE6EEFF.toInt()); tip.typeface = MenuPal.TITLE
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
