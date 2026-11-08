package com.vinicius.meular

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.BlurMaskFilter
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RadialGradient
import android.graphics.RectF
import android.graphics.Shader
import android.graphics.Typeface
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

/**
 * Etapa 123: menu inicial e tela de carregamento no estilo The Sims 4.
 * Fundo em degradê com luzes desfocadas subindo, plumbob verde girando com brilho, título e botões grandes.
 */

/** Fundo animado: céu em degradê, luzes (bokeh) subindo devagar, brilho no centro. */
class MenuBackdrop(ctx: Context, private val top: Int, private val bottom: Int) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val t0 = System.nanoTime()
    private class Dot(var x: Float, var y: Float, val r: Float, val v: Float, val a: Int, val c: Int, val ph: Float)
    private val dots = ArrayList<Dot>()
    private val rnd = java.util.Random(7)

    init { setLayerType(LAYER_TYPE_HARDWARE, null) }

    override fun onDraw(c: Canvas) {
        val w = width.toFloat(); val h = height.toFloat()
        if (w <= 0f) return
        val t = (System.nanoTime() - t0) / 1e9f
        p.shader = LinearGradient(0f, 0f, 0f, h, top, bottom, Shader.TileMode.CLAMP)
        c.drawRect(0f, 0f, w, h, p)
        p.shader = RadialGradient(w * 0.5f, h * 0.38f, max(w, h) * 0.55f, 0x5568E0FF, 0x0068E0FF, Shader.TileMode.CLAMP)
        c.drawRect(0f, 0f, w, h, p)
        p.shader = null
        if (dots.isEmpty()) {
            val d = resources.displayMetrics.density
            val cols = intArrayOf(0xFFFFFFFF.toInt(), 0xFF9FF0C8.toInt(), 0xFF8FD3FF.toInt(), 0xFFFFE7A0.toInt())
            for (i in 0 until 34) dots.add(Dot(rnd.nextFloat() * w, rnd.nextFloat() * h, (6 + rnd.nextFloat() * 34) * d, (8 + rnd.nextFloat() * 22) * d, 18 + rnd.nextInt(40), cols[i % cols.size], rnd.nextFloat() * 6f))
        }
        for (dt in dots) {
            val y = ((dt.y - t * dt.v) % (h + dt.r * 2) + h + dt.r * 2) % (h + dt.r * 2) - dt.r
            val x = dt.x + sin(t * 0.4f + dt.ph) * 18f
            p.color = (dt.c and 0x00FFFFFF) or (dt.a shl 24)
            c.drawCircle(x, y, dt.r, p)
            p.color = (dt.c and 0x00FFFFFF) or ((dt.a / 2) shl 24)
            c.drawCircle(x, y, dt.r * 1.6f, p)
        }
        postInvalidateOnAnimation()
    }
}

/** Plumbob: diamante verde facetado que gira, com brilho embaixo. */
class Plumbob(ctx: Context) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val glow = Paint(Paint.ANTI_ALIAS_FLAG)
    private val path = Path()
    private val t0 = System.nanoTime()
    var speed = 1f

    init { setLayerType(LAYER_TYPE_SOFTWARE, null) }

    override fun onDraw(c: Canvas) {
        val w = width.toFloat(); val h = height.toFloat()
        val t = (System.nanoTime() - t0) / 1e9f * speed
        val cx = w / 2; val bob = sin(t * 1.6f) * h * 0.03f
        val cy = h * 0.48f + bob
        val rw = w * 0.26f; val top = h * 0.40f; val bot = h * 0.44f
        // brilho
        glow.maskFilter = BlurMaskFilter(w * 0.18f, BlurMaskFilter.Blur.NORMAL)
        glow.color = 0x7039FF8A
        c.drawCircle(cx, cy, w * 0.22f, glow)
        // 6 faces em volta: cada uma é um losango (metade de cima e de baixo), largura pela rotação
        val n = 6
        val ang = t * 1.4f
        val faces = ArrayList<FloatArray>()
        for (k in 0 until n) {
            val a0 = ang + k * 2f * Math.PI.toFloat() / n; val a1 = a0 + 2f * Math.PI.toFloat() / n
            val z = cos((a0 + a1) / 2)            // profundidade (só desenha as da frente)
            if (z < -0.05f) continue
            faces.add(floatArrayOf(sin(a0), sin(a1), z, k.toFloat()))
        }
        faces.sortBy { it[2] }
        for (f in faces) {
            val x0 = cx + f[0] * rw; val x1 = cx + f[1] * rw
            val light = (0.55f + 0.45f * f[2]) * (if (f[3].toInt() % 2 == 0) 1f else 0.86f)
            fun col(l: Float, base: Int): Int {
                val r = ((base shr 16 and 255) * l).toInt().coerceIn(0, 255); val g = ((base shr 8 and 255) * l).toInt().coerceIn(0, 255); val b = ((base and 255) * l).toInt().coerceIn(0, 255)
                return Color.rgb(r, g, b)
            }
            // metade de cima
            path.reset(); path.moveTo(cx, cy - top); path.lineTo(x0, cy); path.lineTo(x1, cy); path.close()
            p.shader = LinearGradient(0f, cy - top, 0f, cy, col(light * 1.15f, 0x7DFFB0), col(light, 0x22C55E), Shader.TileMode.CLAMP)
            c.drawPath(path, p)
            // metade de baixo
            path.reset(); path.moveTo(cx, cy + bot); path.lineTo(x0, cy); path.lineTo(x1, cy); path.close()
            p.shader = LinearGradient(0f, cy, 0f, cy + bot, col(light * 0.9f, 0x1FB255), col(light * 0.6f, 0x0E7A38), Shader.TileMode.CLAMP)
            c.drawPath(path, p)
        }
        p.shader = null
        // reflexo
        p.color = 0x66FFFFFF
        path.reset(); path.moveTo(cx - rw * 0.15f, cy - top * 0.8f); path.lineTo(cx - rw * 0.55f, cy - top * 0.12f); path.lineTo(cx - rw * 0.35f, cy - top * 0.1f); path.close()
        c.drawPath(path, p)
        // sombra no chão
        glow.maskFilter = BlurMaskFilter(w * 0.05f, BlurMaskFilter.Blur.NORMAL)
        glow.color = 0x55000000
        val sh = 1f - abs(bob) / (h * 0.03f) * 0.2f
        c.drawOval(RectF(cx - rw * 0.7f * sh, h * 0.95f - h * 0.025f, cx + rw * 0.7f * sh, h * 0.95f + h * 0.025f), glow)
        postInvalidateOnAnimation()
    }
}

@SuppressLint("ViewConstructor")
class MainMenu(ctx: Context, version: String, private val onPlay: () -> Unit, private val onCreator: () -> Unit, private val onNews: () -> Unit, private val onSettings: () -> Unit) : FrameLayout(ctx) {
    private val d = resources.displayMetrics.density
    private fun dp(v: Float) = (v * d).toInt()

    init {
        isClickable = true
        addView(MenuBackdrop(ctx, 0xFF0B2A4A.toInt(), 0xFF0A5A72.toInt()), LayoutParams(-1, -1))
        val land = resources.displayMetrics.widthPixels > resources.displayMetrics.heightPixels
        val root = LinearLayout(ctx)
        root.orientation = if (land) LinearLayout.HORIZONTAL else LinearLayout.VERTICAL
        root.gravity = Gravity.CENTER
        // lado da marca: plumbob + título
        val brand = LinearLayout(ctx); brand.orientation = LinearLayout.VERTICAL; brand.gravity = Gravity.CENTER_HORIZONTAL
        brand.addView(Plumbob(ctx), LinearLayout.LayoutParams(dp(120f), dp(150f)))
        val title = TextView(ctx); title.text = "Meu Lar"; title.textSize = 54f; title.setTextColor(Color.WHITE)
        title.typeface = Typeface.create("sans-serif-black", Typeface.BOLD); title.setShadowLayer(18f, 0f, 6f, 0x99000000.toInt())
        title.paint.shader = LinearGradient(0f, 0f, 0f, 54f * d, intArrayOf(0xFFFFFFFF.toInt(), 0xFFD7F7FF.toInt()), null, Shader.TileMode.CLAMP)
        brand.addView(title)
        val sub = TextView(ctx); sub.text = "Viva a sua história"; sub.textSize = 16f; sub.setTextColor(0xFFBDE9FF.toInt()); sub.letterSpacing = 0.12f
        brand.addView(sub, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(2f) })
        root.addView(brand, LinearLayout.LayoutParams(-2, -2).also { if (land) it.rightMargin = dp(56f) else it.bottomMargin = dp(26f) })
        // botões
        val col = LinearLayout(ctx); col.orientation = LinearLayout.VERTICAL; col.gravity = Gravity.CENTER_HORIZONTAL
        col.addView(bigBtn("Jogar", "Entrar na cidade", 0xFF4BD37B.toInt(), 0xFF1E9E4F.toInt(), "▶") { onPlay() }, LinearLayout.LayoutParams(dp(290f), dp(70f)))
        col.addView(bigBtn("Criar personagem", "Rosto, corpo e roupas", 0xFF4FC3F7.toInt(), 0xFF1E7FC0.toInt(), "☺") { onCreator() }, LinearLayout.LayoutParams(dp(290f), dp(60f)).also { it.topMargin = dp(12f) })
        val row = LinearLayout(ctx); row.orientation = LinearLayout.HORIZONTAL
        row.addView(bigBtn("Novidades", null, 0xFFB085F5.toInt(), 0xFF6A3FC0.toInt(), "★") { onNews() }, LinearLayout.LayoutParams(0, dp(52f), 1f).also { it.rightMargin = dp(6f) })
        row.addView(bigBtn("Opções", null, 0xFF90A4AE.toInt(), 0xFF546E7A.toInt(), "⚙") { onSettings() }, LinearLayout.LayoutParams(0, dp(52f), 1f).also { it.leftMargin = dp(6f) })
        col.addView(row, LinearLayout.LayoutParams(dp(290f), -2).also { it.topMargin = dp(12f) })
        root.addView(col)
        addView(root, LayoutParams(-1, -1))
        val ver = TextView(ctx); ver.text = version; ver.textSize = 11f; ver.setTextColor(0x99FFFFFF.toInt())
        addView(ver, LayoutParams(-2, -2, Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(16f), dp(10f)) })
        // entrada: sobe e aparece
        root.alpha = 0f; root.translationY = dp(24f).toFloat()
        root.animate().alpha(1f).translationY(0f).setDuration(650).setStartDelay(120).start()
    }

    private fun bigBtn(t: String, s: String?, c0: Int, c1: Int, icon: String, act: () -> Unit): View {
        val f = FrameLayout(context)
        val g = android.graphics.drawable.GradientDrawable(android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(c0, c1))
        g.cornerRadius = dp(35f).toFloat(); g.setStroke(dp(2f), 0xCCFFFFFF.toInt())
        f.background = g
        f.elevation = dp(8f).toFloat()
        val l = LinearLayout(context); l.orientation = LinearLayout.HORIZONTAL; l.gravity = Gravity.CENTER_VERTICAL
        l.setPadding(dp(14f), 0, dp(18f), 0)
        val ic = TextView(context); ic.text = icon; ic.textSize = 20f; ic.setTextColor(c1); ic.gravity = Gravity.CENTER; ic.typeface = Typeface.DEFAULT_BOLD
        val ib = android.graphics.drawable.GradientDrawable(); ib.shape = android.graphics.drawable.GradientDrawable.OVAL; ib.setColor(Color.WHITE)
        ic.background = ib
        l.addView(ic, LinearLayout.LayoutParams(dp(38f), dp(38f)).also { it.rightMargin = dp(12f) })
        val tc = LinearLayout(context); tc.orientation = LinearLayout.VERTICAL
        val tt = TextView(context); tt.text = t; tt.textSize = if (s != null) 20f else 16f; tt.setTextColor(Color.WHITE); tt.typeface = Typeface.DEFAULT_BOLD; tt.setShadowLayer(6f, 0f, 2f, 0x66000000)
        tc.addView(tt)
        if (s != null) { val ss = TextView(context); ss.text = s; ss.textSize = 12f; ss.setTextColor(0xDDFFFFFF.toInt()); tc.addView(ss) }
        l.addView(tc)
        f.addView(l, LayoutParams(-1, -1))
        // brilho de vidro na metade de cima
        val shine = View(context)
        val sg = android.graphics.drawable.GradientDrawable(android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(0x55FFFFFF, 0x00FFFFFF)); sg.cornerRadius = dp(35f).toFloat()
        shine.background = sg
        f.addView(shine, LayoutParams(-1, -1).also { it.setMargins(dp(4f), dp(3f), dp(4f), dp(22f)) })
        f.setOnTouchListener { v, e ->
            when (e.actionMasked) {
                MotionEvent.ACTION_DOWN -> v.animate().scaleX(0.95f).scaleY(0.95f).setDuration(80).start()
                MotionEvent.ACTION_UP -> { v.animate().scaleX(1f).scaleY(1f).setDuration(120).start(); act() }
                MotionEvent.ACTION_CANCEL -> v.animate().scaleX(1f).scaleY(1f).setDuration(120).start()
            }
            true
        }
        return f
    }
}

/** Tela de carregamento: plumbob, etapa atual, barra de progresso e dicas. */
@SuppressLint("ViewConstructor")
class LoadingScreen(ctx: Context, private val progress: () -> Float, private val onDone: () -> Unit) : FrameLayout(ctx) {
    private val d = resources.displayMetrics.density
    private fun dp(v: Float) = (v * d).toInt()
    private val tips = arrayOf(
        "Toque no botão do mapa para ver a cidade inteira e ligar o GPS.",
        "Na loja, aba Veículos: escolha seu carro ou moto. Ele fica na rua em frente de casa.",
        "Chegue perto do seu veículo e toque em Dirigir.",
        "Dá para entrar nas casas, lojas e prédios: as paredes somem como no Sims.",
        "A praia tem píer, quiosques e um mar com ondas. Vale o passeio!",
        "O parque de diversões fica perto da praia: roda-gigante, montanha-russa e carrossel.",
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

    init {
        isClickable = true
        addView(MenuBackdrop(ctx, 0xFF071B33.toInt(), 0xFF0B4A5E.toInt()), LayoutParams(-1, -1))
        val col = LinearLayout(ctx); col.orientation = LinearLayout.VERTICAL; col.gravity = Gravity.CENTER_HORIZONTAL
        val pb = Plumbob(ctx); pb.speed = 1.8f
        col.addView(pb, LinearLayout.LayoutParams(dp(96f), dp(120f)))
        stage = TextView(ctx); stage.textSize = 18f; stage.setTextColor(Color.WHITE); stage.typeface = Typeface.DEFAULT_BOLD; stage.gravity = Gravity.CENTER
        col.addView(stage, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(10f) })
        val track = FrameLayout(ctx)
        val tg = android.graphics.drawable.GradientDrawable(); tg.cornerRadius = dp(8f).toFloat(); tg.setColor(0x33FFFFFF); tg.setStroke(dp(1f), 0x55FFFFFF)
        track.background = tg
        bar = View(ctx)
        val bg = android.graphics.drawable.GradientDrawable(android.graphics.drawable.GradientDrawable.Orientation.LEFT_RIGHT, intArrayOf(0xFF34D27A.toInt(), 0xFF8CF0B4.toInt())); bg.cornerRadius = dp(8f).toFloat()
        bar.background = bg
        track.addView(bar, LayoutParams(0, -1))
        col.addView(track, LinearLayout.LayoutParams(dp(280f), dp(14f)).also { it.topMargin = dp(14f) })
        pct = TextView(ctx); pct.textSize = 12f; pct.setTextColor(0xCCFFFFFF.toInt())
        col.addView(pct, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(6f) })
        tip = TextView(ctx); tip.textSize = 14f; tip.setTextColor(0xFFBDE9FF.toInt()); tip.gravity = Gravity.CENTER
        tip.setPadding(dp(28f), 0, dp(28f), 0)
        addView(col, LayoutParams(-2, -2, Gravity.CENTER))
        addView(tip, LayoutParams(-1, -2, Gravity.BOTTOM).also { it.bottomMargin = dp(34f) })
        tip.text = "Dica: " + tips[tipIdx]
        lastTip = System.currentTimeMillis()
        post(object : Runnable {
            override fun run() {
                if (finished) return
                val target = progress().coerceIn(0f, 1f)
                shown += (target - shown) * 0.18f
                if (target >= 1f && shown > 0.985f) shown = 1f
                val w = (dp(280f) * shown).toInt()
                bar.layoutParams = bar.layoutParams.also { it.width = max(dp(14f), w) }
                bar.requestLayout()
                pct.text = "${(shown * 100).toInt()}%"
                stage.text = when {
                    shown < 0.12f -> "Abrindo o mapa da cidade..."
                    shown < 0.35f -> "Asfaltando as ruas..."
                    shown < 0.55f -> "Erguendo casas e prédios..."
                    shown < 0.72f -> "Mobiliando os interiores..."
                    shown < 0.86f -> "Enchendo a praia e o parque..."
                    shown < 0.99f -> "Ligando o trânsito..."
                    else -> "Pronto!"
                }
                val now = System.currentTimeMillis()
                if (now - lastTip > 4200L) {
                    lastTip = now; tipIdx = (tipIdx + 1) % tips.size
                    tip.animate().alpha(0f).setDuration(220).withEndAction { tip.text = "Dica: " + tips[tipIdx]; tip.animate().alpha(1f).setDuration(260).start() }.start()
                }
                if (shown >= 1f) { finished = true; postDelayed({ onDone() }, 350); return }
                postDelayed(this, 33)
            }
        })
    }
}
