package com.vinicius.meular

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.graphics.Typeface
import android.graphics.drawable.Drawable
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.LayerDrawable
import android.graphics.BlurMaskFilter
import android.graphics.LinearGradient
import android.graphics.Shader
import android.os.SystemClock
import android.view.View
import kotlin.math.min

object Pal {
    val BG = Color.parseColor("#0E1A2B")
    val BG2 = Color.parseColor("#1B3350")
    val CARD = Color.parseColor("#1F3A57")
    val CARD_HI = Color.parseColor("#2A4A6D")
    val TEXT = Color.parseColor("#F4FAFF")
    val SUB = Color.parseColor("#9FC2DE")
    val GOLD = Color.parseColor("#FFCB4D")
    val LINE = Color.parseColor("#5CB4E4")
    val INK = Color.parseColor("#0A1220")
    val CORAL = Color.parseColor("#FF7A59")
    val CORAL2 = Color.parseColor("#F0583F")
    val GREEN = Color.parseColor("#3CCB7F")
    val GREEN2 = Color.parseColor("#1FA463")
    val GLASS = Color.parseColor("#E60E1A2B")
    val SIMS = Color.parseColor("#EB12233A")
    val SIMS_HI = Color.parseColor("#EB1F3A5C")
    val SIMS_LINE = Color.parseColor("#9958B8E8")
    val SIMS_BLUE = Color.parseColor("#58B8E8")
    val PLUMB = Color.parseColor("#6BE04A")
    val PLUMB2 = Color.parseColor("#2FA83A")
}

/** Cor de botão "gostosinho": topo claro, base mais escura e a borda de baixo (o "degrau"). */
class Tone(val top: Int, val bot: Int, val edge: Int)

object Tn {
    private fun c(s: String) = Color.parseColor(s)
    val SKY = Tone(c("#7FD0FF"), c("#3F9BE8"), c("#245FA8"))
    val MINT = Tone(c("#6DE8B4"), c("#2FBF86"), c("#17805B"))
    val SUN = Tone(c("#FFDB75"), c("#FFB52E"), c("#BC7708"))
    val CORAL = Tone(c("#FF9A7A"), c("#F0583F"), c("#A83423"))
    val LAV = Tone(c("#8ADAFA"), c("#2F95D6"), c("#1A5C94"))
    val ROSE = Tone(c("#FF9DBF"), c("#EC5C8D"), c("#A93560"))
    val GHOST = Tone(c("#2C4866"), c("#223A55"), c("#0D1A2A"))
    val CARD = Tone(c("#2A4A6D"), c("#1F3A57"), c("#0B1726"))
    val PANEL = Tone(c("#223D5C"), c("#162B45"), c("#08121F"))
    val SIMS_BLUE = Tone(c("#4FC3F0"), c("#1B7FB8"), c("#0E5A87"))
    val SIMS_PURPLE = Tone(c("#A45CE0"), c("#6A2FA8"), c("#46207A"))
    val SIMS_GREEN = Tone(c("#9BE23A"), c("#5BA81C"), c("#3C7A10"))
    val GLASS = Tone(c("#7A8794"), c("#4E5A66"), c("#2E363E"))
}

object Ui {
    fun bg(color: Int, radius: Float, stroke: Int = 0, strokeW: Float = 0f): GradientDrawable {
        val g = GradientDrawable()
        g.setColor(color)
        g.cornerRadius = radius
        if (stroke != 0) g.setStroke(strokeW.toInt().coerceAtLeast(1), stroke)
        return g
    }

    fun grad(c1: Int, c2: Int, radius: Float): GradientDrawable {
        val g = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(c1, c2))
        g.cornerRadius = radius
        return g
    }

    fun oval(color: Int, stroke: Int = 0, strokeW: Float = 0f): GradientDrawable {
        val g = GradientDrawable()
        g.shape = GradientDrawable.OVAL
        g.setColor(color)
        if (stroke != 0) g.setStroke(strokeW.toInt().coerceAtLeast(1), stroke)
        return g
    }

    fun topSheet(color: Int, radius: Float): GradientDrawable {
        val g = GradientDrawable()
        g.setColor(color)
        g.cornerRadii = floatArrayOf(radius, radius, radius, radius, 0f, 0f, 0f, 0f)
        return g
    }

    /** Botão/painel "chunky": degrau escuro embaixo + degradê + brilho no topo. Tudo em px. */
    fun chunky(t: Tone, radius: Float, ledge: Float, gloss: Boolean = true, stroke: Int = 0, strokeW: Float = 0f): Drawable {
        val edge = GradientDrawable()
        edge.setColor(t.edge)
        edge.cornerRadius = radius
        val body = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(t.top, t.bot))
        body.cornerRadius = radius
        if (stroke != 0) body.setStroke(strokeW.toInt().coerceAtLeast(1), stroke)
        val layers: Array<Drawable> = if (gloss) {
            val shine = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(0x4DFFFFFF, 0x00FFFFFF, 0x00FFFFFF))
            shine.cornerRadius = radius
            arrayOf(edge, body, shine)
        } else arrayOf(edge, body)
        val ld = LayerDrawable(layers)
        val l = ledge.toInt()
        for (i in 1 until layers.size) ld.setLayerInset(i, 0, 0, 0, l)
        return ld
    }

    /** Painel escuro com contorno lilás e degrau embaixo (barras, cartões, dock). */
    fun panel(radius: Float, ledge: Float, line: Float): Drawable = chunky(Tn.PANEL, radius, ledge, false, Pal.LINE, line)

    /** Folha que sobe de baixo (menus): degradê roxo com contorno. */
    fun sheetBg(radius: Float, line: Float): GradientDrawable {
        val g = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(Pal.BG2, Pal.BG))
        g.cornerRadii = floatArrayOf(radius, radius, radius, radius, 0f, 0f, 0f, 0f)
        g.setStroke(line.toInt().coerceAtLeast(1), Pal.LINE)
        return g
    }

    /** Segmento da barra estilo Sims: degradê vertical + brilho no topo, cantos arredondados só nas pontas. */
    fun segment(t: Tone, rad: Float, left: Boolean, right: Boolean): Drawable {
        val r = floatArrayOf(
            if (left) rad else 0f, if (left) rad else 0f,
            if (right) rad else 0f, if (right) rad else 0f,
            if (right) rad else 0f, if (right) rad else 0f,
            if (left) rad else 0f, if (left) rad else 0f)
        val body = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(t.top, t.bot))
        body.cornerRadii = r
        val shine = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(0x66FFFFFF, 0x00FFFFFF, 0x00FFFFFF))
        shine.cornerRadii = r
        return LayerDrawable(arrayOf(body, shine))
    }

    /** Moldura branca da barra (com sombra embaixo). */
    fun barFrame(rad: Float, ledge: Float): Drawable {
        val sh = GradientDrawable(); sh.setColor(0x55000000); sh.cornerRadius = rad
        val fr = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(0xFFFFFFFF.toInt(), 0xFFCFE3EE.toInt()))
        fr.cornerRadius = rad
        val ld = LayerDrawable(arrayOf(sh, fr))
        ld.setLayerInset(1, 0, 0, 0, ledge.toInt())
        return ld
    }

    /** Botão redondo de vidro (como zoom/câmera do Sims): fundo translúcido + aro branco. */
    fun glass(strokeW: Float): GradientDrawable {
        val g = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(0xAA8E9AA6.toInt(), 0xAA505C68.toInt()))
        g.shape = GradientDrawable.OVAL
        g.setStroke(strokeW.toInt().coerceAtLeast(1), 0xFFFFFFFF.toInt())
        return g
    }

    private fun mix(a: Int, b: Int, t: Float): Int {
        fun ch(x: Int, y: Int) = (x + (y - x) * t).toInt().coerceIn(0, 255)
        return Color.rgb(ch(Color.red(a), Color.red(b)), ch(Color.green(a), Color.green(b)), ch(Color.blue(a), Color.blue(b)))
    }

    /**
     * Vidro translúcido (glassmorphism): corpo com degradê transparente, reflexo no topo e
     * borda fina de luz. tint = cor do vidro; aTop/aBot = opacidade (0..255) em cima/embaixo.
     */
    fun frost(rad: Float, tint: Int, aTop: Int, aBot: Int, line: Float, oval: Boolean = false, edge: Int = 0xAAFFFFFF.toInt()): Drawable {
        val t = tint and 0xFFFFFF
        val hi = mix(t, Color.WHITE, 0.28f)
        val body = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf((aTop shl 24) or hi, (aBot shl 24) or t))
        val shine = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(0x55FFFFFF, 0x10FFFFFF, 0x00FFFFFF))
        val ring = GradientDrawable()
        ring.setColor(0)
        ring.setStroke(line.toInt().coerceAtLeast(1), edge)
        for (g in arrayOf(body, shine, ring)) {
            if (oval) g.shape = GradientDrawable.OVAL else g.cornerRadius = rad
        }
        val ld = LayerDrawable(arrayOf(body, shine, ring))
        val i = line.toInt().coerceAtLeast(1)
        ld.setLayerInset(1, i, i, i, i)
        return ld
    }

    val BOLD: Typeface = Typeface.create("sans-serif-medium", Typeface.BOLD)
    val MED: Typeface = Typeface.create("sans-serif-medium", Typeface.NORMAL)
}

object Ic {
    const val GEAR = 100
    const val EYE = 101
    const val HOME = 102
    const val WORK = 103
    const val SHOP = 104
    const val CLOSE = 105
    const val ROTATE = 106
    const val MOVE = 107
    const val TRASH = 108
    const val CHECK = 109
    const val COIN = 110
    const val INFO = 111
    const val REFRESH = 112
    const val PERSON = 113
    const val DICE = 114
    const val JUMP = 115
    const val PLUMB = 116
    const val BASE = 117
    const val BODY = 118
    const val HAIR = 119
    const val FACE = 120
    const val SHIRT = 121
    const val SHOE = 122
    const val HAT = 123
    const val CHEV = 124
    const val SPARK = 125
    const val CART = 126
    const val DOTS = 127
    const val PLUS = 128
    const val CASE = 129
    const val BACK = 130
    const val CAM3P = 131
    const val CAM1P = 132
    const val CAMAIR = 133
    const val AVATAR = 134
}

/** Ícones desenhados em vetor (grade 100x100). Móveis usam o ordinal do Type (0..13). */
class IconView(ctx: Context, var kind: Int, var color: Int = Color.WHITE, var accent: Int = Pal.BG) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val rf = RectF()
    private val path = Path()
    var soft = false
    var glow = false
    var glowColor = 0xAA9AD8FF.toInt()
    private var glowPass = false
    private val softShader: Shader = LinearGradient(0f, 8f, 0f, 96f, intArrayOf(0xFFFFFFFF.toInt(), 0xFFDCEEFF.toInt(), 0xFFA9CCF5.toInt()), floatArrayOf(0f, 0.55f, 1f), Shader.TileMode.CLAMP)
    private var blur: BlurMaskFilter? = null

    fun set(k: Int) { kind = k; invalidate() }

    /** Ícone "moderno": degradê claro + brilho suave por trás. */
    fun fancy(glowTint: Int = 0xAA9AD8FF.toInt()): IconView {
        soft = true; glow = true; glowColor = glowTint
        setLayerType(LAYER_TYPE_SOFTWARE, null)
        return this
    }

    private fun paintColor(c: Int) {
        if (glowPass) { p.shader = null; p.color = glowColor }
        else if (soft && c == Color.WHITE) { p.shader = softShader; p.color = Color.WHITE }
        else { p.shader = null; p.color = c }
    }
    /** Preenchimento com degradê vertical (ícones coloridos). */
    private fun gf(top: Int, bot: Int, y0: Float, y1: Float) {
        p.style = Paint.Style.FILL; p.color = Color.WHITE
        p.shader = LinearGradient(0f, y0, 0f, y1, top, bot, Shader.TileMode.CLAMP)
    }
    private fun fill(c: Int) { p.style = Paint.Style.FILL; paintColor(c) }
    private fun stroke(c: Int, w: Float) {
        p.style = Paint.Style.STROKE; paintColor(c); p.strokeWidth = w
        p.strokeCap = Paint.Cap.ROUND; p.strokeJoin = Paint.Join.ROUND
    }
    private fun rr(c: Canvas, l: Float, t: Float, r: Float, b: Float, rad: Float) {
        rf.set(l, t, r, b); c.drawRoundRect(rf, rad, rad, p)
    }
    private fun poly(c: Canvas, vararg v: Float) {
        path.reset(); path.moveTo(v[0], v[1])
        var i = 2
        while (i < v.size) { path.lineTo(v[i], v[i + 1]); i += 2 }
        path.close(); c.drawPath(path, p)
    }

    override fun onDraw(c: Canvas) {
        val aw = width - paddingLeft - paddingRight
        val ah = height - paddingTop - paddingBottom
        var s = min(aw, ah) / 100f
        if (s <= 0f) return
        if (glow) s *= 0.84f
        c.save()
        c.translate(paddingLeft + (aw - 100f * s) / 2f, paddingTop + (ah - 100f * s) / 2f)
        c.scale(s, s)
        p.strokeCap = Paint.Cap.BUTT
        if (glow) {
            if (blur == null) blur = BlurMaskFilter(3.2f * resources.displayMetrics.density, BlurMaskFilter.Blur.NORMAL)
            glowPass = true; p.maskFilter = blur
            paintIcon(c)
            glowPass = false; p.maskFilter = null
        }
        paintIcon(c)
        p.shader = null
        c.restore()
    }

    private fun paintIcon(c: Canvas) {
        val w = color
        val a = accent
        when (kind) {
            Ic.GEAR -> {
                fill(w)
                for (i in 0 until 8) { c.save(); c.rotate(i * 45f, 50f, 50f); rr(c, 43f, 6f, 57f, 26f, 4f); c.restore() }
                path.reset(); path.fillType = Path.FillType.EVEN_ODD
                path.addCircle(50f, 50f, 32f, Path.Direction.CW); path.addCircle(50f, 50f, 14f, Path.Direction.CW)
                c.drawPath(path, p)
                path.fillType = Path.FillType.WINDING
            }
            Ic.EYE -> {
                stroke(w, 8f); rf.set(8f, 28f, 92f, 72f); c.drawOval(rf, p)
                fill(w); c.drawCircle(50f, 50f, 14f, p)
            }
            Ic.HOME -> {
                fill(w); poly(c, 50f, 12f, 94f, 50f, 82f, 50f, 82f, 88f, 18f, 88f, 18f, 50f, 6f, 50f)
                fill(a); rr(c, 42f, 60f, 58f, 88f, 3f)
            }
            Ic.WORK -> {
                stroke(w, 7f); rr(c, 36f, 18f, 64f, 38f, 8f)
                fill(w); rr(c, 10f, 32f, 90f, 86f, 12f)
                fill(a); rr(c, 44f, 54f, 56f, 68f, 3f)
            }
            Ic.SHOP -> {
                stroke(w, 7f); rf.set(33f, 12f, 67f, 52f); c.drawArc(rf, 180f, 180f, false, p)
                fill(w); rr(c, 18f, 34f, 82f, 90f, 10f)
                fill(a); c.drawCircle(38f, 48f, 4f, p); c.drawCircle(62f, 48f, 4f, p)
            }
            Ic.CLOSE -> {
                stroke(w, 11f); c.drawLine(26f, 26f, 74f, 74f, p); c.drawLine(74f, 26f, 26f, 74f, p)
            }
            Ic.ROTATE -> {
                stroke(w, 10f); rf.set(20f, 20f, 80f, 80f); c.drawArc(rf, -40f, 260f, false, p)
                fill(w); poly(c, 8f, 40f, 40f, 40f, 24f, 14f)
            }
            Ic.MOVE -> {
                stroke(w, 8f); c.drawLine(24f, 50f, 76f, 50f, p); c.drawLine(50f, 24f, 50f, 76f, p)
                fill(w)
                poly(c, 50f, 4f, 36f, 24f, 64f, 24f); poly(c, 50f, 96f, 36f, 76f, 64f, 76f)
                poly(c, 4f, 50f, 24f, 36f, 24f, 64f); poly(c, 96f, 50f, 76f, 36f, 76f, 64f)
            }
            Ic.TRASH -> {
                fill(w); rr(c, 18f, 24f, 82f, 34f, 4f); rr(c, 38f, 12f, 62f, 26f, 4f); rr(c, 26f, 38f, 74f, 90f, 8f)
                stroke(a, 6f); c.drawLine(41f, 50f, 41f, 78f, p); c.drawLine(59f, 50f, 59f, 78f, p)
            }
            Ic.CHECK -> {
                stroke(w, 12f); path.reset(); path.moveTo(20f, 52f); path.lineTo(42f, 74f); path.lineTo(82f, 28f); c.drawPath(path, p)
            }
            Ic.COIN -> {
                fill(Color.parseColor("#E39B1C")); c.drawCircle(50f, 50f, 46f, p)
                fill(Pal.GOLD); c.drawCircle(50f, 50f, 40f, p)
                stroke(Color.parseColor("#E39B1C"), 6f); c.drawCircle(50f, 50f, 27f, p)
                fill(Color.parseColor("#E39B1C")); rr(c, 46f, 34f, 54f, 66f, 3f)
            }
            Ic.INFO -> {
                fill(w); c.drawCircle(50f, 50f, 44f, p)
                fill(a); c.drawCircle(50f, 30f, 6f, p); rr(c, 44f, 42f, 56f, 74f, 4f)
            }
            Ic.PERSON -> {
                fill(w); c.drawCircle(50f, 28f, 18f, p)
                path.reset(); path.moveTo(14f, 92f); path.cubicTo(14f, 52f, 86f, 52f, 86f, 92f); path.close(); c.drawPath(path, p)
            }
            Ic.DICE -> {
                fill(w); rr(c, 10f, 10f, 90f, 90f, 18f)
                fill(a)
                c.drawCircle(30f, 30f, 8f, p); c.drawCircle(70f, 30f, 8f, p); c.drawCircle(50f, 50f, 8f, p)
                c.drawCircle(30f, 70f, 8f, p); c.drawCircle(70f, 70f, 8f, p)
            }
            Ic.JUMP -> {
                stroke(w, 13f)
                path.reset(); path.moveTo(20f, 56f); path.lineTo(50f, 26f); path.lineTo(80f, 56f); c.drawPath(path, p)
                path.reset(); path.moveTo(20f, 86f); path.lineTo(50f, 56f); path.lineTo(80f, 86f); c.drawPath(path, p)
            }
            Ic.PLUMB -> {
                fill(Pal.PLUMB2); poly(c, 50f, 4f, 82f, 50f, 50f, 96f, 18f, 50f)
                fill(Pal.PLUMB); poly(c, 50f, 4f, 82f, 50f, 50f, 50f)
                fill(Color.parseColor("#B8F59A")); poly(c, 50f, 4f, 50f, 50f, 18f, 50f)
                fill(Pal.PLUMB2); poly(c, 18f, 50f, 50f, 50f, 50f, 96f)
            }
            Ic.CHEV -> {
                stroke(w, 12f); path.reset(); path.moveTo(34f, 16f); path.lineTo(68f, 50f); path.lineTo(34f, 84f); c.drawPath(path, p)
            }
            Ic.SPARK -> {
                fill(w); path.reset(); path.moveTo(50f, 2f); path.quadTo(54f, 46f, 98f, 50f); path.quadTo(54f, 54f, 50f, 98f)
                path.quadTo(46f, 54f, 2f, 50f); path.quadTo(46f, 46f, 50f, 2f); path.close(); c.drawPath(path, p)
            }
            Ic.CAM3P -> {
                // 3ª pessoa: visor de câmera com o personagem visto de trás
                stroke(w, 6f)
                for (sx in 0..1) for (sy in 0..1) {
                    val x0 = if (sx == 0) 10f else 90f; val y0 = if (sy == 0) 10f else 90f
                    val dx = if (sx == 0) 16f else -16f; val dy = if (sy == 0) 16f else -16f
                    path.reset(); path.moveTo(x0, y0 + dy); path.lineTo(x0, y0); path.lineTo(x0 + dx, y0); c.drawPath(path, p)
                }
                fill(w); c.drawCircle(50f, 34f, 11f, p)
                path.reset(); path.moveTo(26f, 84f); path.cubicTo(26f, 56f, 36f, 49f, 50f, 49f); path.cubicTo(64f, 49f, 74f, 56f, 74f, 84f); path.close(); c.drawPath(path, p)
                fill(a); rr(c, 46f, 56f, 54f, 84f, 3f)
                fill(0xFFFF5A5A.toInt()); c.drawCircle(80f, 22f, 4.2f, p)
            }
            Ic.CAM1P -> {
                // 1ª pessoa: olho dentro do visor
                stroke(w, 6f)
                for (sx in 0..1) for (sy in 0..1) {
                    val x0 = if (sx == 0) 10f else 90f; val y0 = if (sy == 0) 10f else 90f
                    val dx = if (sx == 0) 16f else -16f; val dy = if (sy == 0) 16f else -16f
                    path.reset(); path.moveTo(x0, y0 + dy); path.lineTo(x0, y0); path.lineTo(x0 + dx, y0); c.drawPath(path, p)
                }
                fill(w)
                path.reset(); path.moveTo(16f, 50f); path.quadTo(50f, 18f, 84f, 50f); path.quadTo(50f, 82f, 16f, 50f); path.close(); c.drawPath(path, p)
                fill(a); c.drawCircle(50f, 50f, 15f, p)
                fill(w); c.drawCircle(50f, 50f, 8f, p)
                fill(a); c.drawCircle(50f, 50f, 4.6f, p)
                fill(w); c.drawCircle(45f, 45f, 2.6f, p)
                stroke(w, 4f); c.drawLine(30f, 28f, 25f, 20f, p); c.drawLine(50f, 24f, 50f, 15f, p); c.drawLine(70f, 28f, 75f, 20f, p)
            }
            Ic.CAMAIR -> {
                // vista aérea: casa vista de cima com o cone da câmera
                fill(w)
                path.reset(); path.moveTo(50f, 8f); path.lineTo(70f, 36f); path.lineTo(30f, 36f); path.close()
                p.alpha = 150; c.drawPath(path, p); p.alpha = 255
                fill(w); c.drawCircle(50f, 11f, 5f, p)
                stroke(w, 4f); p.pathEffect = android.graphics.DashPathEffect(floatArrayOf(5f, 5f), 0f)
                rf.set(8f, 58f, 92f, 92f); c.drawOval(rf, p); p.pathEffect = null
                fill(w); poly(c, 50f, 42f, 74f, 62f, 68f, 62f, 68f, 82f, 32f, 82f, 32f, 62f, 26f, 62f)
                fill(a); rr(c, 44f, 68f, 56f, 82f, 3f)
            }
            Ic.BASE -> {
                // duas pessoas (adulto e criança)
                gf(0xFFFFC9A5.toInt(), 0xFFE9A47E.toInt(), 8f, 30f); c.drawCircle(36f, 20f, 11f, p)
                gf(0xFF6C4A33.toInt(), 0xFF4A2F1F.toInt(), 6f, 22f); path.reset(); path.addArc(RectF(25f, 7f, 47f, 29f), 180f, 180f); path.close(); c.drawPath(path, p)
                gf(0xFF5BC4EE.toInt(), 0xFF2F8FD0.toInt(), 34f, 80f); path.reset(); path.moveTo(22f, 82f); path.cubicTo(20f, 50f, 26f, 35f, 36f, 35f); path.cubicTo(46f, 35f, 52f, 50f, 50f, 82f); path.close(); c.drawPath(path, p)
                gf(0xFFFFC9A5.toInt(), 0xFFE9A47E.toInt(), 44f, 62f); c.drawCircle(72f, 52f, 8.5f, p)
                gf(0xFFF28B3C.toInt(), 0xFFE0662A.toInt(), 54f, 62f); path.reset(); path.addArc(RectF(63f, 43f, 81f, 61f), 180f, 180f); path.close(); c.drawPath(path, p)
                gf(0xFFFF8FB8.toInt(), 0xFFE2578F.toInt(), 60f, 84f); path.reset(); path.moveTo(58f, 84f); path.cubicTo(58f, 66f, 64f, 60f, 72f, 60f); path.cubicTo(80f, 60f, 86f, 66f, 86f, 84f); path.close(); c.drawPath(path, p)
            }
            Ic.BODY -> {
                // corpo inteiro: cabeça, tronco, braços e pernas
                gf(0xFF6C4A33.toInt(), 0xFF4A2F1F.toInt(), 4f, 24f); path.reset(); path.addArc(RectF(38f, 4f, 62f, 28f), 180f, 180f); path.close(); c.drawPath(path, p)
                gf(0xFFFFC9A5.toInt(), 0xFFE9A47E.toInt(), 8f, 30f); c.drawCircle(50f, 19f, 11f, p)
                gf(0xFFFFC9A5.toInt(), 0xFFE9A47E.toInt(), 28f, 36f); rr(c, 45f, 28f, 55f, 38f, 3f)
                gf(0xFFFFC9A5.toInt(), 0xFFE9A47E.toInt(), 36f, 70f); rr(c, 14f, 38f, 26f, 70f, 6f); rr(c, 74f, 38f, 86f, 70f, 6f)
                gf(0xFF5BC4EE.toInt(), 0xFF2F8FD0.toInt(), 34f, 66f); rr(c, 25f, 34f, 75f, 66f, 10f)
                fill(0x55FFFFFF); rr(c, 30f, 38f, 38f, 60f, 4f)
                gf(0xFF3E4F8F.toInt(), 0xFF2B386B.toInt(), 62f, 78f); rr(c, 27f, 62f, 73f, 78f, 5f)
                gf(0xFFFFC9A5.toInt(), 0xFFE9A47E.toInt(), 76f, 94f); rr(c, 30f, 76f, 47f, 94f, 5f); rr(c, 53f, 76f, 70f, 94f, 5f)
                fill(0xFF2B386B.toInt()); rr(c, 48.5f, 62f, 51.5f, 78f, 1.5f)
            }
            Ic.HAIR -> {
                // cabelo comprido castanho com brilho
                gf(0xFFFFC9A5.toInt(), 0xFFE9A47E.toInt(), 30f, 80f); path.reset(); path.addOval(RectF(32f, 28f, 68f, 78f), Path.Direction.CW); c.drawPath(path, p)
                gf(0xFF9A6238.toInt(), 0xFF5E3A20.toInt(), 6f, 94f)
                path.reset(); path.moveTo(50f, 6f); path.cubicTo(18f, 6f, 14f, 44f, 20f, 68f); path.cubicTo(22f, 82f, 14f, 90f, 12f, 94f); path.cubicTo(30f, 96f, 36f, 84f, 33f, 70f)
                path.cubicTo(30f, 56f, 34f, 42f, 40f, 36f); path.cubicTo(52f, 36f, 64f, 30f, 70f, 22f); path.cubicTo(74f, 36f, 70f, 56f, 67f, 70f)
                path.cubicTo(64f, 84f, 70f, 96f, 88f, 94f); path.cubicTo(86f, 90f, 78f, 82f, 80f, 68f); path.cubicTo(86f, 44f, 82f, 6f, 50f, 6f); path.close(); c.drawPath(path, p)
                stroke(0x66FFE2B5, 3.4f); path.reset(); path.moveTo(34f, 14f); path.cubicTo(22f, 24f, 22f, 44f, 26f, 60f); c.drawPath(path, p)
                path.reset(); path.moveTo(50f, 10f); path.cubicTo(40f, 12f, 32f, 18f, 30f, 26f); c.drawPath(path, p)
                fill(0xFF3A2A22.toInt()); c.drawCircle(43f, 54f, 2.4f, p); c.drawCircle(57f, 54f, 2.4f, p)
            }
            Ic.FACE -> {
                gf(0xFFFFD2B0.toInt(), 0xFFEBA982.toInt(), 6f, 94f); c.drawCircle(50f, 50f, 40f, p)
                fill(0x33FF6F6F); c.drawCircle(27f, 60f, 7f, p); c.drawCircle(73f, 60f, 7f, p)
                fill(Color.WHITE); rf.set(24f, 38f, 44f, 54f); c.drawOval(rf, p); rf.set(56f, 38f, 76f, 54f); c.drawOval(rf, p)
                gf(0xFF6BC6F0.toInt(), 0xFF2F7FC0.toInt(), 38f, 54f); c.drawCircle(34f, 46f, 7f, p); c.drawCircle(66f, 46f, 7f, p)
                fill(0xFF1B2733.toInt()); c.drawCircle(34f, 46f, 3.6f, p); c.drawCircle(66f, 46f, 3.6f, p)
                fill(Color.WHITE); c.drawCircle(32f, 43.5f, 1.8f, p); c.drawCircle(64f, 43.5f, 1.8f, p)
                stroke(0xFF6A4630.toInt(), 3.6f); path.reset(); path.moveTo(23f, 33f); path.quadTo(34f, 26f, 44f, 31f); c.drawPath(path, p)
                path.reset(); path.moveTo(56f, 31f); path.quadTo(66f, 26f, 77f, 33f); c.drawPath(path, p)
                stroke(0x88C98866.toInt(), 2.6f); path.reset(); path.moveTo(50f, 48f); path.quadTo(46f, 58f, 51f, 61f); c.drawPath(path, p)
                gf(0xFFFF6F85.toInt(), 0xFFD9405F.toInt(), 66f, 80f); path.reset(); path.moveTo(36f, 69f); path.quadTo(50f, 82f, 64f, 69f); path.quadTo(50f, 72f, 36f, 69f); path.close(); c.drawPath(path, p)
            }
            Ic.SHIRT -> {
                gf(0xFF5BD0C8.toInt(), 0xFF2A9EA0.toInt(), 14f, 90f)
                path.reset(); path.moveTo(34f, 14f); path.lineTo(8f, 28f); path.lineTo(18f, 52f); path.lineTo(30f, 46f); path.lineTo(30f, 90f); path.lineTo(70f, 90f); path.lineTo(70f, 46f)
                path.lineTo(82f, 52f); path.lineTo(92f, 28f); path.lineTo(66f, 14f); path.quadTo(50f, 30f, 34f, 14f); path.close(); c.drawPath(path, p)
                fill(0xFFE9FBFA.toInt()); path.reset(); path.moveTo(34f, 14f); path.quadTo(50f, 30f, 66f, 14f); path.quadTo(50f, 22f, 34f, 14f); path.close(); c.drawPath(path, p)
                stroke(0xFF1E7C80.toInt(), 3f); path.reset(); path.moveTo(34f, 14f); path.quadTo(50f, 30f, 66f, 14f); c.drawPath(path, p)
                stroke(0x55000000, 2.4f); c.drawLine(30f, 46f, 30f, 88f, p); c.drawLine(70f, 46f, 70f, 88f, p)
                path.reset(); path.moveTo(40f, 60f); path.quadTo(44f, 72f, 40f, 86f); c.drawPath(path, p)
                gf(0xFFFFD84D.toInt(), 0xFFF2A91E.toInt(), 50f, 72f); poly(c, 50f, 50f, 54f, 58f, 63f, 59f, 56f, 65f, 58f, 74f, 50f, 69f, 42f, 74f, 44f, 65f, 37f, 59f, 46f, 58f)
            }
            Ic.SHOE -> {
                // tênis de cano baixo com cadarço
                gf(0xFFFFFFFF.toInt(), 0xFFD2DCE6.toInt(), 72f, 90f); rr(c, 6f, 72f, 94f, 90f, 9f)
                gf(0xFFFF6B5E.toInt(), 0xFFD6382F.toInt(), 22f, 76f)
                path.reset(); path.moveTo(10f, 74f); path.lineTo(10f, 50f); path.quadTo(12f, 40f, 24f, 38f); path.lineTo(40f, 24f); path.quadTo(46f, 20f, 52f, 26f); path.lineTo(58f, 40f)
                path.quadTo(72f, 46f, 86f, 56f); path.quadTo(94f, 62f, 92f, 74f); path.close(); c.drawPath(path, p)
                gf(0xFFFFFFFF.toInt(), 0xFFE3EAF1.toInt(), 52f, 76f); path.reset(); path.moveTo(68f, 54f); path.quadTo(84f, 58f, 92f, 66f); path.lineTo(92f, 74f); path.lineTo(66f, 74f); path.close(); c.drawPath(path, p)
                stroke(Color.WHITE, 3.4f); c.drawLine(40f, 34f, 50f, 40f, p); c.drawLine(36f, 42f, 48f, 48f, p); c.drawLine(32f, 50f, 46f, 56f, p)
                stroke(0x55B02A22, 3f); path.reset(); path.moveTo(14f, 64f); path.quadTo(34f, 56f, 56f, 66f); c.drawPath(path, p)
                fill(0x33000000); rr(c, 6f, 86f, 94f, 90f, 2f)
            }
            Ic.HAT -> {
                // boné com aba, botão e costuras
                gf(0xFFFFC94D.toInt(), 0xFFF29A1E.toInt(), 18f, 74f)
                path.reset(); path.moveTo(14f, 70f); path.cubicTo(12f, 34f, 34f, 16f, 54f, 18f); path.cubicTo(74f, 20f, 88f, 40f, 88f, 70f); path.close(); c.drawPath(path, p)
                gf(0xFFE07D14.toInt(), 0xFFB85A0A.toInt(), 62f, 84f); path.reset(); path.moveTo(8f, 72f); path.cubicTo(30f, 62f, 70f, 62f, 92f, 72f); path.cubicTo(98f, 80f, 90f, 86f, 80f, 82f); path.cubicTo(60f, 76f, 36f, 76f, 16f, 84f); path.cubicTo(6f, 86f, 2f, 78f, 8f, 72f); path.close(); c.drawPath(path, p)
                stroke(0x66B85A0A, 2.4f); path.reset(); path.moveTo(54f, 18f); path.cubicTo(44f, 34f, 42f, 52f, 46f, 68f); c.drawPath(path, p)
                path.reset(); path.moveTo(54f, 18f); path.cubicTo(64f, 34f, 70f, 52f, 74f, 68f); c.drawPath(path, p)
                fill(0xFFB85A0A.toInt()); c.drawCircle(54f, 18f, 4.4f, p)
                fill(0x55FFFFFF); path.reset(); path.moveTo(26f, 56f); path.cubicTo(28f, 40f, 38f, 28f, 48f, 24f); path.cubicTo(38f, 34f, 32f, 44f, 32f, 58f); path.close(); c.drawPath(path, p)
            }
            Ic.AVATAR -> {
                // retrato: cabelo, rosto e camiseta
                gf(0xFF5BD0C8.toInt(), 0xFF2A9EA0.toInt(), 62f, 100f); path.reset(); path.moveTo(10f, 100f); path.cubicTo(10f, 74f, 26f, 66f, 50f, 66f); path.cubicTo(74f, 66f, 90f, 74f, 90f, 100f); path.close(); c.drawPath(path, p)
                gf(0xFFFFC9A5.toInt(), 0xFFE9A47E.toInt(), 56f, 70f); rr(c, 42f, 54f, 58f, 72f, 5f)
                gf(0xFFFFD2B0.toInt(), 0xFFEBA982.toInt(), 14f, 62f); rf.set(29f, 14f, 71f, 64f); c.drawOval(rf, p)
                gf(0xFF6C4A33.toInt(), 0xFF3F281A.toInt(), 6f, 40f); path.reset(); path.moveTo(26f, 44f); path.cubicTo(22f, 14f, 40f, 6f, 54f, 8f); path.cubicTo(72f, 8f, 82f, 24f, 74f, 46f); path.cubicTo(72f, 34f, 66f, 28f, 56f, 28f); path.cubicTo(42f, 30f, 32f, 34f, 26f, 44f); path.close(); c.drawPath(path, p)
                fill(0xFF1B2733.toInt()); c.drawCircle(42f, 44f, 3.2f, p); c.drawCircle(58f, 44f, 3.2f, p)
                stroke(0xFFD9405F.toInt(), 2.8f); path.reset(); path.moveTo(42f, 55f); path.quadTo(50f, 61f, 58f, 55f); c.drawPath(path, p)
            }
            Ic.BACK -> {
                stroke(w, 12f)
                c.drawLine(80f, 50f, 24f, 50f, p)
                path.reset(); path.moveTo(48f, 24f); path.lineTo(22f, 50f); path.lineTo(48f, 76f); c.drawPath(path, p)
            }
            Ic.CART -> {
                // carrinho detalhado: alça, cesto com grade, rodinhas
                stroke(w, 8f); path.reset(); path.moveTo(4f, 14f); path.lineTo(20f, 14f); path.lineTo(32f, 64f); path.lineTo(80f, 64f); c.drawPath(path, p)
                fill(w); poly(c, 24f, 28f, 94f, 28f, 84f, 56f, 32f, 56f)
                stroke(a, 4f); c.drawLine(44f, 30f, 46f, 54f, p); c.drawLine(60f, 30f, 60f, 54f, p); c.drawLine(76f, 30f, 74f, 54f, p)
                c.drawLine(28f, 42f, 88f, 42f, p)
                fill(w); c.drawCircle(40f, 82f, 8f, p); c.drawCircle(72f, 82f, 8f, p)
                fill(a); c.drawCircle(40f, 82f, 3f, p); c.drawCircle(72f, 82f, 3f, p)
            }
            Ic.DOTS -> {
                fill(w); c.drawCircle(18f, 50f, 10f, p); c.drawCircle(50f, 50f, 10f, p); c.drawCircle(82f, 50f, 10f, p)
            }
            Ic.PLUS -> {
                stroke(w, 16f); c.drawLine(50f, 18f, 50f, 82f, p); c.drawLine(18f, 50f, 82f, 50f, p)
            }
            Ic.CASE -> {
                // maleta detalhada: alça, corpo, faixa e fecho dourado
                stroke(w, 8f); rr(c, 33f, 12f, 67f, 34f, 9f)
                fill(w); rr(c, 8f, 28f, 92f, 86f, 13f)
                fill(a); rr(c, 8f, 52f, 92f, 57f, 0f)
                fill(Pal.GOLD); rr(c, 40f, 46f, 60f, 68f, 5f)
                fill(Color.parseColor("#B8770A")); rr(c, 47f, 54f, 53f, 62f, 2f)
            }
            Ic.REFRESH -> {
                stroke(w, 10f); rf.set(18f, 18f, 82f, 82f); c.drawArc(rf, -20f, 290f, false, p)
                fill(w); poly(c, 66f, 6f, 90f, 30f, 60f, 34f)
            }
            0 -> { // cadeira
                fill(w); rr(c, 24f, 14f, 36f, 56f, 4f); rr(c, 24f, 50f, 78f, 62f, 4f)
                rr(c, 24f, 62f, 34f, 90f, 3f); rr(c, 68f, 62f, 78f, 90f, 3f)
                fill(a); rr(c, 38f, 22f, 44f, 44f, 2f)
            }
            1 -> { // mesa
                fill(w); rr(c, 8f, 32f, 92f, 46f, 5f); rr(c, 16f, 46f, 27f, 86f, 3f); rr(c, 73f, 46f, 84f, 86f, 3f)
                fill(a); c.drawCircle(50f, 24f, 8f, p)
                fill(w); rr(c, 47f, 12f, 53f, 24f, 2f)
            }
            2 -> { // cama
                fill(w); rr(c, 8f, 22f, 20f, 84f, 4f); rr(c, 8f, 58f, 92f, 74f, 4f); rr(c, 80f, 74f, 92f, 86f, 3f)
                rr(c, 20f, 44f, 92f, 60f, 6f)
                fill(a); rr(c, 24f, 34f, 46f, 48f, 7f); rr(c, 52f, 50f, 90f, 60f, 4f)
            }
            3 -> { // sofá
                fill(w); rr(c, 16f, 26f, 84f, 56f, 12f); rr(c, 10f, 48f, 90f, 72f, 9f)
                rr(c, 6f, 38f, 24f, 74f, 8f); rr(c, 76f, 38f, 94f, 74f, 8f); rr(c, 18f, 72f, 28f, 84f, 3f); rr(c, 72f, 72f, 82f, 84f, 3f)
                fill(a); rr(c, 30f, 50f, 70f, 62f, 5f)
            }
            4 -> { // estante
                fill(w); rr(c, 16f, 8f, 84f, 92f, 5f)
                fill(a); rr(c, 23f, 15f, 77f, 36f, 2f); rr(c, 23f, 41f, 77f, 62f, 2f); rr(c, 23f, 67f, 77f, 85f, 2f)
                fill(w); rr(c, 28f, 20f, 35f, 36f, 1f); rr(c, 38f, 24f, 46f, 36f, 1f); rr(c, 56f, 46f, 64f, 62f, 1f); rr(c, 30f, 72f, 40f, 85f, 1f)
            }
            5 -> { // planta
                fill(Color.parseColor("#7EE0A8"))
                rf.set(26f, 18f, 52f, 62f); c.drawOval(rf, p); rf.set(48f, 8f, 76f, 56f); c.drawOval(rf, p)
                fill(Color.parseColor("#4CC27E")); rf.set(36f, 28f, 64f, 66f); c.drawOval(rf, p)
                fill(Color.parseColor("#E9905C")); poly(c, 32f, 62f, 68f, 62f, 62f, 92f, 38f, 92f)
            }
            6 -> { // tapete
                fill(w); rr(c, 8f, 28f, 92f, 72f, 7f)
                fill(a); rr(c, 16f, 36f, 84f, 64f, 4f)
                fill(w); rr(c, 24f, 44f, 76f, 56f, 3f)
            }
            7 -> { // TV
                fill(w); rr(c, 8f, 18f, 92f, 68f, 6f)
                fill(Color.parseColor("#4F86E0")); rr(c, 14f, 24f, 86f, 62f, 3f)
                fill(w); rr(c, 44f, 68f, 56f, 78f, 2f); rr(c, 28f, 78f, 72f, 88f, 4f)
            }
            8 -> { // geladeira
                fill(w); rr(c, 26f, 6f, 74f, 94f, 8f)
                fill(a); rr(c, 26f, 38f, 74f, 43f, 0f)
                rr(c, 62f, 16f, 67f, 32f, 2f); rr(c, 62f, 50f, 67f, 74f, 2f)
            }
            9 -> { // fogão
                fill(w); rr(c, 16f, 10f, 84f, 92f, 7f)
                fill(a); rr(c, 22f, 16f, 78f, 42f, 3f); rr(c, 26f, 54f, 74f, 82f, 4f)
                fill(w); c.drawCircle(38f, 29f, 7f, p); c.drawCircle(62f, 29f, 7f, p); rr(c, 32f, 46f, 68f, 51f, 2f)
            }
            10 -> { // abajur
                fill(Color.parseColor("#FFD866")); poly(c, 32f, 10f, 68f, 10f, 80f, 44f, 20f, 44f)
                fill(w); rr(c, 47f, 44f, 53f, 82f, 2f); rr(c, 32f, 82f, 68f, 92f, 5f)
            }
            11 -> { // criado-mudo
                fill(Color.parseColor("#FFD866")); poly(c, 38f, 8f, 62f, 8f, 70f, 30f, 30f, 30f)
                fill(w); rr(c, 47f, 30f, 53f, 38f, 2f); rr(c, 20f, 38f, 80f, 90f, 6f)
                fill(a); rr(c, 27f, 46f, 73f, 62f, 3f); rr(c, 27f, 68f, 73f, 84f, 3f)
                fill(w); c.drawCircle(50f, 54f, 3f, p); c.drawCircle(50f, 76f, 3f, p)
            }
            12 -> { // mesa de centro
                fill(w); rr(c, 8f, 40f, 92f, 54f, 7f); rr(c, 18f, 54f, 28f, 82f, 3f); rr(c, 72f, 54f, 82f, 82f, 3f)
                fill(a); rr(c, 34f, 28f, 58f, 40f, 2f)
                fill(w); rr(c, 36f, 30f, 56f, 34f, 1f)
            }
            13 -> { // guarda-roupa
                fill(w); rr(c, 16f, 6f, 84f, 94f, 6f)
                fill(a); rr(c, 21f, 11f, 48f, 89f, 3f); rr(c, 52f, 11f, 79f, 89f, 3f)
                fill(w); rr(c, 42f, 44f, 46f, 60f, 2f); rr(c, 54f, 44f, 58f, 60f, 2f)
            }
        }
    }
}

/** Barra de progresso gordinha: trilho escuro com contorno lilás e enchimento verde com brilho. */
class PillBar(ctx: Context) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val rf = RectF()
    private val d = ctx.resources.displayMetrics.density
    private var shown = 0f
    private var fillShader: Shader? = null
    var value = 0f
        set(v) { field = v; invalidate() }

    override fun onSizeChanged(w: Int, h: Int, ow: Int, oh: Int) {
        super.onSizeChanged(w, h, ow, oh)
        fillShader = LinearGradient(0f, 0f, 0f, h.toFloat(), intArrayOf(0xFF9BFBE0.toInt(), 0xFF3FC8F0.toInt()), null, Shader.TileMode.CLAMP)
    }

    override fun onDraw(c: Canvas) {
        val h = height.toFloat()
        val w = width.toFloat()
        shown += (value - shown) * 0.25f
        p.shader = null
        p.style = Paint.Style.FILL
        p.color = 0x66101828
        rf.set(0f, 0f, w, h); c.drawRoundRect(rf, h / 2, h / 2, p)
        val ins = 1.5f * d
        if (shown > 0.01f) {
            val fh = h - ins * 2
            p.shader = fillShader
            rf.set(ins, ins, ins + maxOf(fh, (w - ins * 2) * shown), h - ins)
            c.drawRoundRect(rf, fh / 2, fh / 2, p)
            p.shader = null
        }
        p.style = Paint.Style.STROKE
        p.strokeWidth = ins
        p.color = 0x88FFFFFF.toInt()
        rf.set(ins / 2, ins / 2, w - ins / 2, h - ins / 2); c.drawRoundRect(rf, h / 2, h / 2, p)
        if (kotlin.math.abs(value - shown) > 0.004f) postInvalidateOnAnimation()
    }
}

/** Mira, joystick e dicas por cima do 3D (não captura toques). */
class Overlay(ctx: Context, private val game: GameView) : View(ctx) {
    private val d = ctx.resources.displayMetrics.density
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val rf = RectF()
    private val t0 = SystemClock.uptimeMillis()

    init {
        isClickable = false
        isFocusable = false
        p.typeface = Ui.BOLD
    }

    private fun label(c: Canvas, txt: String, cx: Float, cy: Float, size: Float, bg: Int, fg: Int) {
        p.style = Paint.Style.FILL
        p.textSize = size * d
        val tw = p.measureText(txt)
        val padX = 10f * d
        val h = size * d + 10f * d
        rf.set(cx - tw / 2 - padX, cy - h / 2, cx + tw / 2 + padX, cy + h / 2)
        p.color = bg
        c.drawRoundRect(rf, h / 2, h / 2, p)
        p.color = fg
        p.textAlign = Paint.Align.CENTER
        c.drawText(txt, cx, cy + size * d * 0.35f, p)
    }

    override fun onDraw(c: Canvas) {
        if (game.r.mode == 0) {
            val w = width.toFloat()
            val h = height.toFloat()
            val f = game.r.focus
            val g = game.r.grabbed != null
            val cx = w / 2
            val cy = h / 2
            p.style = Paint.Style.STROKE
            p.strokeWidth = 2.4f * d
            val rad = (if (f != null) 10f else 5f) * d
            p.color = Color.argb(110, 0, 0, 0)
            c.drawCircle(cx, cy, rad + d, p)
            p.strokeWidth = 1.8f * d
            p.color = if (g) Color.parseColor("#5CE08A") else if (f != null) Color.parseColor("#FFE066") else Color.argb(230, 255, 255, 255)
            c.drawCircle(cx, cy, rad, p)
            if (f == null) { p.style = Paint.Style.FILL; c.drawCircle(cx, cy, 1.4f * d, p) }
            if (f != null) {
                val txt = if (g) "Carregando: ${f.type.nome}" else f.type.nome
                label(c, txt, cx, cy + 28f * d, 12f, Color.parseColor("#E62A2046"), Pal.TEXT)
            }

            val r = game.joyR
            if (game.joyActive) {
                p.style = Paint.Style.FILL; p.color = Color.argb(70, 58, 45, 94)
                c.drawCircle(game.joyBx, game.joyBy, r, p)
                p.style = Paint.Style.STROKE; p.strokeWidth = 2.5f * d; p.color = Color.argb(190, 187, 174, 219)
                c.drawCircle(game.joyBx, game.joyBy, r, p)
                p.style = Paint.Style.FILL; p.color = if (game.r.pRun) Color.argb(240, 109, 232, 180) else Color.argb(215, 255, 244, 230)
                c.drawCircle(game.joyKx, game.joyKy, r * 0.42f, p)
            } else {
                p.style = Paint.Style.STROKE; p.strokeWidth = 2.5f * d; p.color = Color.argb(110, 187, 174, 219)
                c.drawCircle(w * 0.15f, h * 0.72f, r, p)
                p.style = Paint.Style.FILL; p.color = Color.argb(90, 255, 244, 230)
                c.drawCircle(w * 0.15f, h * 0.72f, r * 0.42f, p)
            }

            val age = SystemClock.uptimeMillis() - t0
            if (age < 9000L) {
                val al = if (age < 7000L) 1f else (9000L - age) / 2000f
                label(c, "Esquerda: andar   •   Direita: olhar", cx, h * 0.26f, 11f, Color.argb((225 * al).toInt(), 42, 32, 70), Color.argb((255 * al).toInt(), 255, 244, 230))
            }
        }
        postInvalidateOnAnimation()
    }
}
