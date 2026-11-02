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
import android.graphics.LinearGradient
import android.graphics.Shader
import android.os.SystemClock
import android.view.View
import kotlin.math.min

object Pal {
    val BG = Color.parseColor("#231A38")
    val BG2 = Color.parseColor("#33275A")
    val CARD = Color.parseColor("#372B58")
    val CARD_HI = Color.parseColor("#43376A")
    val TEXT = Color.parseColor("#FFF4E6")
    val SUB = Color.parseColor("#BBAEDB")
    val GOLD = Color.parseColor("#FFCB4D")
    val LINE = Color.parseColor("#6A5A9C")
    val INK = Color.parseColor("#1A1229")
    val CORAL = Color.parseColor("#FF7A59")
    val CORAL2 = Color.parseColor("#F0583F")
    val GREEN = Color.parseColor("#3CCB7F")
    val GREEN2 = Color.parseColor("#1FA463")
    val GLASS = Color.parseColor("#E6231A38")
    val SIMS = Color.parseColor("#EB2A2046")
    val SIMS_HI = Color.parseColor("#EB3A2D5E")
    val SIMS_LINE = Color.parseColor("#996A5A9C")
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
    val LAV = Tone(c("#C3A8FF"), c("#7F60EA"), c("#4C36AE"))
    val ROSE = Tone(c("#FF9DBF"), c("#EC5C8D"), c("#A93560"))
    val GHOST = Tone(c("#3E3262"), c("#352A57"), c("#1C1431"))
    val CARD = Tone(c("#43376A"), c("#372B58"), c("#190F2E"))
    val PANEL = Tone(c("#3A2D5E"), c("#2A2046"), c("#120B22"))
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
}

/** Ícones desenhados em vetor (grade 100x100). Móveis usam o ordinal do Type (0..13). */
class IconView(ctx: Context, var kind: Int, var color: Int = Color.WHITE, var accent: Int = Pal.BG) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val rf = RectF()
    private val path = Path()

    fun set(k: Int) { kind = k; invalidate() }

    private fun fill(c: Int) { p.style = Paint.Style.FILL; p.color = c }
    private fun stroke(c: Int, w: Float) {
        p.style = Paint.Style.STROKE; p.color = c; p.strokeWidth = w
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
        val s = min(aw, ah) / 100f
        if (s <= 0f) return
        c.save()
        c.translate(paddingLeft + (aw - 100f * s) / 2f, paddingTop + (ah - 100f * s) / 2f)
        c.scale(s, s)
        p.strokeCap = Paint.Cap.BUTT
        paintIcon(c)
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
            Ic.BASE -> {
                fill(w); c.drawCircle(50f, 26f, 17f, p)
                path.reset(); path.moveTo(16f, 92f); path.cubicTo(16f, 46f, 84f, 46f, 84f, 92f); path.close(); c.drawPath(path, p)
            }
            Ic.BODY -> {
                fill(w); c.drawCircle(50f, 16f, 12f, p)
                rr(c, 30f, 33f, 70f, 72f, 13f); rr(c, 12f, 35f, 26f, 68f, 7f); rr(c, 74f, 35f, 88f, 68f, 7f)
                rr(c, 32f, 64f, 48f, 94f, 7f); rr(c, 52f, 64f, 68f, 94f, 7f)
            }
            Ic.HAIR -> {
                fill(w)
                path.reset(); path.fillType = Path.FillType.EVEN_ODD
                rf.set(14f, 8f, 86f, 92f); path.addOval(rf, Path.Direction.CW)
                rf.set(31f, 34f, 69f, 82f); path.addOval(rf, Path.Direction.CW)
                c.drawPath(path, p)
                path.fillType = Path.FillType.WINDING
            }
            Ic.FACE -> {
                fill(w)
                path.reset(); path.fillType = Path.FillType.EVEN_ODD
                path.addCircle(50f, 50f, 44f, Path.Direction.CW)
                path.addCircle(34f, 34f, 6.5f, Path.Direction.CW)
                path.addCircle(66f, 34f, 6.5f, Path.Direction.CW)
                path.moveTo(26f, 58f); path.quadTo(50f, 90f, 74f, 58f); path.quadTo(50f, 71f, 26f, 58f); path.close()
                c.drawPath(path, p)
                path.fillType = Path.FillType.WINDING
            }
            Ic.SHIRT -> {
                fill(w)
                path.reset(); path.moveTo(32f, 12f); path.lineTo(8f, 30f); path.lineTo(20f, 49f); path.lineTo(30f, 42f)
                path.lineTo(30f, 88f); path.lineTo(70f, 88f); path.lineTo(70f, 42f); path.lineTo(80f, 49f); path.lineTo(92f, 30f)
                path.lineTo(68f, 12f); path.quadTo(50f, 32f, 32f, 12f); path.close(); c.drawPath(path, p)
            }
            Ic.SHOE -> {
                fill(w)
                path.reset(); path.moveTo(10f, 22f); path.lineTo(40f, 22f); path.lineTo(42f, 46f); path.quadTo(48f, 58f, 66f, 60f)
                path.quadTo(92f, 62f, 92f, 76f); path.lineTo(10f, 76f); path.close(); c.drawPath(path, p)
                rr(c, 8f, 72f, 94f, 90f, 8f)
                fill(a); rr(c, 18f, 34f, 34f, 39f, 2f); rr(c, 18f, 46f, 34f, 51f, 2f)
            }
            Ic.HAT -> {
                fill(w); rf.set(16f, 22f, 84f, 94f); c.drawArc(rf, 180f, 180f, true, p)
                rr(c, 8f, 57f, 94f, 71f, 7f)
            }
            Ic.CHEV -> {
                stroke(w, 12f); path.reset(); path.moveTo(34f, 16f); path.lineTo(68f, 50f); path.lineTo(34f, 84f); c.drawPath(path, p)
            }
            Ic.SPARK -> {
                fill(w); path.reset(); path.moveTo(50f, 2f); path.quadTo(54f, 46f, 98f, 50f); path.quadTo(54f, 54f, 50f, 98f)
                path.quadTo(46f, 54f, 2f, 50f); path.quadTo(46f, 46f, 50f, 2f); path.close(); c.drawPath(path, p)
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
        fillShader = LinearGradient(0f, 0f, 0f, h.toFloat(), intArrayOf(0xFF8CF2C6.toInt(), 0xFF2FBF86.toInt()), null, Shader.TileMode.CLAMP)
    }

    override fun onDraw(c: Canvas) {
        val h = height.toFloat()
        val w = width.toFloat()
        shown += (value - shown) * 0.25f
        p.shader = null
        p.style = Paint.Style.FILL
        p.color = 0xFF120B22.toInt()
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
        p.color = Pal.LINE
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
