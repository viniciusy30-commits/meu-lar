package com.vinicius.meular

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.SystemClock
import android.view.View
import kotlin.math.min

object Pal {
    val BG = Color.parseColor("#1B2030")
    val CARD = Color.parseColor("#2A3144")
    val CARD_HI = Color.parseColor("#343C54")
    val TEXT = Color.parseColor("#F2F4FA")
    val SUB = Color.parseColor("#9AA5C0")
    val GOLD = Color.parseColor("#FFC94A")
    val CORAL = Color.parseColor("#FF7A59")
    val CORAL2 = Color.parseColor("#F2563A")
    val GREEN = Color.parseColor("#3CCB7F")
    val GREEN2 = Color.parseColor("#1FA463")
    val GLASS = Color.parseColor("#D91B2030")
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
        val s = min(width, height) / 100f
        if (s <= 0f) return
        c.save()
        c.translate((width - 100f * s) / 2f, (height - 100f * s) / 2f)
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

/** Barra de progresso fina e arredondada. */
class PillBar(ctx: Context) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val rf = RectF()
    private var shown = 0f
    var value = 0f
        set(v) { field = v; invalidate() }

    override fun onDraw(c: Canvas) {
        val h = height.toFloat()
        shown += (value - shown) * 0.25f
        p.color = Color.parseColor("#66000000")
        rf.set(0f, 0f, width.toFloat(), h); c.drawRoundRect(rf, h / 2, h / 2, p)
        if (shown > 0.01f) {
            p.color = Pal.GREEN
            rf.set(0f, 0f, maxOf(h, width * shown), h); c.drawRoundRect(rf, h / 2, h / 2, p)
        }
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
        val padX = 12f * d
        val h = size * d + 14f * d
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
                label(c, txt, cx, cy + 34f * d, 14f, Color.parseColor("#C41B2030"), Color.WHITE)
            }

            val r = game.joyR
            if (game.joyActive) {
                p.style = Paint.Style.FILL; p.color = Color.argb(40, 255, 255, 255)
                c.drawCircle(game.joyBx, game.joyBy, r, p)
                p.style = Paint.Style.STROKE; p.strokeWidth = 2f * d; p.color = Color.argb(150, 255, 255, 255)
                c.drawCircle(game.joyBx, game.joyBy, r, p)
                p.style = Paint.Style.FILL; p.color = Color.argb(190, 255, 255, 255)
                c.drawCircle(game.joyKx, game.joyKy, r * 0.42f, p)
            } else {
                p.style = Paint.Style.STROKE; p.strokeWidth = 2f * d; p.color = Color.argb(70, 255, 255, 255)
                c.drawCircle(w * 0.2f, h * 0.74f, r, p)
                p.style = Paint.Style.FILL; p.color = Color.argb(50, 255, 255, 255)
                c.drawCircle(w * 0.2f, h * 0.74f, r * 0.42f, p)
            }

            val age = SystemClock.uptimeMillis() - t0
            if (age < 9000L) {
                val al = if (age < 7000L) 1f else (9000L - age) / 2000f
                label(c, "Esquerda: andar   •   Direita: olhar", cx, h * 0.28f, 13f, Color.argb((190 * al).toInt(), 27, 32, 48), Color.argb((255 * al).toInt(), 255, 255, 255))
            }
        }
        postInvalidateOnAnimation()
    }
}
