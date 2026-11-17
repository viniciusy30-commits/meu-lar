package com.vinicius.meular

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.Canvas
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.graphics.Shader
import android.graphics.Typeface
import android.view.View
import kotlin.math.min
import kotlin.math.sin

/**
 * Tela de carregamento temática do trabalho (aparece ao apertar TRABALHAR na porta do local de trabalho).
 * Médico: fundo azul-hospital em degradê, cruz vermelha com brilho, linha de batimento cardíaco animada,
 * nome do hospital, frase do plantão, dica e barra de progresso. Outras profissões: mesma tela com a cor e o ícone delas.
 * Ao terminar chama [done] (o minigame entra aqui no futuro).
 */
class WorkScreen(ctx: Context, private val job: Jobs.Job, private val ms: Long, private val done: () -> Unit) : View(ctx) {
    private val d = resources.displayMetrics.density
    private var t = 0f          // 0..1
    private var clock = 0f      // segundos (animações)
    private val anim = ValueAnimator.ofFloat(0f, 1f).apply {
        duration = ms
        addUpdateListener { t = it.animatedValue as Float; clock = it.currentPlayTime / 1000f; invalidate() }
        addListener(object : android.animation.AnimatorListenerAdapter() { override fun onAnimationEnd(a: android.animation.Animator) { done() } })
    }
    private val theme = when (job.id) {
        "medico", "enfermeiro" -> intArrayOf(0xFF0B3C5D.toInt(), 0xFF1F7A8C.toInt(), 0xFFE53950.toInt())
        "policial" -> intArrayOf(0xFF0D1B3E.toInt(), 0xFF27408B.toInt(), 0xFF64B5F6.toInt())
        "bombeiro" -> intArrayOf(0xFF4A0D0D.toInt(), 0xFFB71C1C.toInt(), 0xFFFFB300.toInt())
        "professor" -> intArrayOf(0xFF1B4332.toInt(), 0xFF2D6A4F.toInt(), 0xFFFFD166.toInt())
        else -> intArrayOf(0xFF22223B.toInt(), 0xFF4A4E69.toInt(), 0xFF9AD1D4.toInt())
    }
    private val tips = mapOf(
        "medico" to listOf("Plantão começando: 6 pacientes na fila da emergência.", "Dica: atenda primeiro os casos vermelhos da triagem.", "Lave as mãos entre um paciente e outro."),
        "enfermeiro" to listOf("Confira a medicação de cada leito.", "Dica: anote tudo no prontuário."))
    private val tip = (tips[job.id] ?: listOf("Bom trabalho!", "Turno começando…")).random()
    private val pTitle = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt(); typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD); textAlign = Paint.Align.CENTER }
    private val pSub = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xDDFFFFFF.toInt(); typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.NORMAL); textAlign = Paint.Align.CENTER }
    private val pLine = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE; strokeCap = Paint.Cap.ROUND; strokeJoin = Paint.Join.ROUND }
    private val pFill = Paint(Paint.ANTI_ALIAS_FLAG)

    init { isClickable = true }   // bloqueia toques no jogo por baixo

    override fun onAttachedToWindow() { super.onAttachedToWindow(); anim.start() }
    override fun onDetachedFromWindow() { anim.cancel(); super.onDetachedFromWindow() }

    override fun onDraw(c: Canvas) {
        val w = width.toFloat(); val h = height.toFloat(); val cx = w / 2f
        pFill.shader = LinearGradient(0f, 0f, w, h, theme[0], theme[1], Shader.TileMode.CLAMP); pFill.alpha = 255
        c.drawRect(0f, 0f, w, h, pFill); pFill.shader = null
        // bolhas suaves ao fundo
        for (k in 0 until 7) {
            val bx = (k * 0.17f + 0.08f) * w + sin(clock * 0.4f + k) * 20f * d; val by = h * (0.2f + 0.6f * ((k * 37) % 10) / 10f) + sin(clock * 0.6f + k * 2) * 14f * d
            pFill.color = 0x14FFFFFF; c.drawCircle(bx, by, (40f + k * 9f) * d, pFill)
        }
        val s = min(w, h)
        // ícone: cruz (saúde) ou emoji da profissão
        val iy = h * 0.30f; val pulse = 1f + 0.06f * sin(clock * 7.5f).coerceAtLeast(0f)
        if (job.id == "medico" || job.id == "enfermeiro") {
            val a = s * 0.07f * pulse; val b = s * 0.022f * pulse
            pFill.color = 0x33FFFFFF; c.drawCircle(cx, iy, a * 1.9f, pFill)
            pFill.color = 0xFFFFFFFF.toInt(); c.drawCircle(cx, iy, a * 1.5f, pFill)
            pFill.color = theme[2]
            c.drawRoundRect(RectF(cx - b, iy - a, cx + b, iy + a), b * 0.4f, b * 0.4f, pFill)
            c.drawRoundRect(RectF(cx - a, iy - b, cx + a, iy + b), b * 0.4f, b * 0.4f, pFill)
        } else {
            pFill.color = 0xFFFFFFFF.toInt(); c.drawCircle(cx, iy, s * 0.1f * pulse, pFill)
            pTitle.textSize = s * 0.11f; c.drawText(EMOJI[job.id] ?: "💼", cx, iy + s * 0.04f, pTitle)
        }
        // batimento cardíaco correndo
        val ly = h * 0.52f; val lw = w * 0.7f; val x0 = cx - lw / 2f
        val path = Path(); val n = 120; val ph = (clock * 0.55f) % 1f
        for (i in 0..n) {
            val u = i / n.toFloat(); val px = x0 + u * lw
            var q = ((u - ph) % 0.25f + 0.25f) % 0.25f / 0.25f
            val yy = when {
                q < 0.40f -> 0f
                q < 0.45f -> -0.15f * sin((q - 0.40f) / 0.05f * Math.PI.toFloat())
                q < 0.50f -> 0f
                q < 0.53f -> (q - 0.50f) / 0.03f * 0.25f
                q < 0.57f -> 0.25f - (q - 0.53f) / 0.04f * 1.25f
                q < 0.61f -> -1f + (q - 0.57f) / 0.04f * 1.15f
                q < 0.64f -> 0.15f - (q - 0.61f) / 0.03f * 0.15f
                q < 0.75f -> -0.22f * sin((q - 0.64f) / 0.11f * Math.PI.toFloat())
                else -> 0f
            }
            val py = ly + yy * s * 0.07f
            if (i == 0) path.moveTo(px, py) else path.lineTo(px, py)
        }
        pLine.shader = LinearGradient(x0, 0f, x0 + lw, 0f, intArrayOf(0x00FFFFFF, 0xFF7CF7C4.toInt(), 0xFFFFFFFF.toInt(), 0x00FFFFFF), null, Shader.TileMode.CLAMP)
        pLine.strokeWidth = 3.2f * d; c.drawPath(path, pLine); pLine.shader = null
        // textos
        pTitle.textSize = 26f * d; c.drawText(job.place, cx, h * 0.66f, pTitle)
        pSub.textSize = 15f * d; c.drawText("${job.name} · ${if (t < 0.5f) "preparando o turno" else "entrando no plantão"}…", cx, h * 0.66f + 26f * d, pSub)
        pSub.textSize = 13f * d; pSub.alpha = 190; c.drawText(tip, cx, h * 0.66f + 50f * d, pSub); pSub.alpha = 255
        // barra de progresso arredondada
        val bw = w * 0.46f; val bh = 10f * d; val by = h * 0.86f
        pFill.color = 0x33FFFFFF; c.drawRoundRect(RectF(cx - bw / 2, by, cx + bw / 2, by + bh), bh / 2, bh / 2, pFill)
        pFill.shader = LinearGradient(cx - bw / 2, 0f, cx + bw / 2, 0f, 0xFFFFFFFF.toInt(), theme[2], Shader.TileMode.CLAMP)
        c.drawRoundRect(RectF(cx - bw / 2, by, cx - bw / 2 + bw * t.coerceAtLeast(0.04f), by + bh), bh / 2, bh / 2, pFill); pFill.shader = null
        pSub.textSize = 12f * d; c.drawText("${(t * 100).toInt()}%", cx, by + bh + 18f * d, pSub)
    }

    companion object {
        val EMOJI = mapOf("medico" to "🩺", "enfermeiro" to "💉", "policial" to "🚓", "bombeiro" to "🚒", "professor" to "📚", "juiz" to "⚖️", "advogado" to "💼",
            "programador" to "💻", "engenheiro" to "👷", "mecanico" to "🔧", "atendente" to "🍔", "repositor" to "🛒", "frentista" to "⛽", "diarista" to "🧹",
            "lixeiro" to "🚛", "entregador" to "📦", "secretario" to "🗂️", "empresario" to "🏢", "prefeito" to "🏛️")
    }
}
