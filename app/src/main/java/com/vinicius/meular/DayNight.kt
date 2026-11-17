package com.vinicius.meular

import kotlin.math.max
import kotlin.math.min

/**
 * Ciclo de dia e noite: 60 minutos de jogo = 30 min de dia + 30 min de noite, com entardecer e amanhecer de ~2 min.
 * [night] 0 (dia) .. 1 (noite) e [dusk] 0..1 (pico laranja no pôr e no nascer do sol) são lidos pelos shaders.
 * O botão do jogo chama [toggle]: pula para o começo do dia ou da noite, com a troca de luz animada em ~4 s.
 */
object DayNight {
    const val CYCLE = 3600f                 // segundos por ciclo completo
    private const val EDGE = 0.035f         // meia largura da transição (fração do ciclo ≈ 2 min)
    private var base = System.nanoTime()
    private var phase0 = 0.08f              // começa de manhã
    @Volatile var night = 0f; private set
    @Volatile var dusk = 0f; private set
    private var shown = -1f
    private var lastT = 0L

    /** fase do ciclo 0..1: 0..0.5 dia, 0.5..1 noite */
    fun phase(): Float {
        val s = (System.nanoTime() - base) / 1e9f
        val p = phase0 + s / CYCLE
        return p - kotlin.math.floor(p)
    }

    private fun smooth(a: Float, b: Float, x: Float): Float { val t = ((x - a) / (b - a)).coerceIn(0f, 1f); return t * t * (3f - 2f * t) }

    /** noite "verdadeira" pela fase (0..1) */
    private fun nightAt(p: Float): Float = when {
        p < EDGE -> 1f - smooth(1f - EDGE, 1f + EDGE, p + 1f)            // amanhecer (fim da transição)
        p < 0.5f - EDGE -> 0f                                              // dia
        p < 0.5f + EDGE -> smooth(0.5f - EDGE, 0.5f + EDGE, p)            // entardecer
        p < 1f - EDGE -> 1f                                                // noite
        else -> 1f - smooth(1f - EDGE, 1f + EDGE, p)                      // amanhecer (começo)
    }

    /** chamado uma vez por quadro */
    fun update() {
        val now = System.nanoTime()
        val dt = if (lastT == 0L) 0f else ((now - lastT) / 1e9f).coerceIn(0f, 0.2f)
        lastT = now
        val p = phase()
        val target = nightAt(p)
        shown = if (shown < 0f) target else shown + (target - shown) * min(1f, dt * 0.9f)
        night = shown
        // pôr/nascer do sol: pico quando a noite está pela metade da transição
        dusk = (1f - kotlin.math.abs(shown - 0.5f) * 2f).coerceIn(0f, 1f) * if (shown in 0.02f..0.98f) 1f else 0f
    }

    val isNight: Boolean get() = phase() >= 0.5f

    /** botão: troca entre dia e noite (pula a fase; a luz acompanha em poucos segundos) */
    fun toggle() {
        val goNight = !isNight
        val p = if (goNight) 0.5f + EDGE + 0.01f else EDGE + 0.01f
        phase0 = p; base = System.nanoTime()
    }

    /** minutos que faltam para a próxima troca (para mostrar no botão) */
    fun minutesLeft(): Int {
        val p = phase()
        val next = if (p < 0.5f) 0.5f else 1f
        return ((next - p) * CYCLE / 60f).toInt() + 1
    }
}
