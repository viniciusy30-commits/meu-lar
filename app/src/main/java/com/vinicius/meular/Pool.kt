package com.vinicius.meular

/**
 * Etapa 118: piscina no quintal dos fundos (atrás da casa, z negativo).
 * Medidas em metros do mundo. A água fica um pouco abaixo do deck; o deck está no nível do chão (y = 0).
 * Models.yard desenha (buraco no gramado, bacia, deck, água); Renderer3D bloqueia a água para quem anda e cuida do mergulho/nado.
 */
object Pool {
    const val IW = 5.0f            // largura da água (eixo x)
    const val IL = 6.4f            // comprimento da água (eixo z)
    const val Z1 = -9.0f           // borda da água mais perto da casa
    const val Z0 = Z1 - IL         // borda da água mais longe da casa
    const val DEPTH = 2.0f         // profundidade
    const val WATER_Y = -0.14f     // altura da superfície da água
    const val DECK = 1.4f          // largura do deck de pedra em volta
    const val COPING = 0.35f       // borda branca elevada
    const val BACK_Z = -19.0f      // cerca dos fundos (antes -7)
    const val WALK_Z = -18.6f      // limite do quintal para andar (antes -6.6)

    // gatilhos e distâncias (m, altura 1.0; multiplicados por CuteChar.bodyScale())
    const val DIVE_START = 3.1f    // do quadril até a borda da água quando o mergulho começa (as mãos tocam a água ~0,3 m dentro)
    const val EDGE_START = 1.16f   // do quadril até a borda ao começar "nadar até a borda" (as mãos terminam sobre o deck)
    const val EDGE_END_T = 3.6f    // o clipe tem 5 s; depois de 3,6 s ele só fica parado pendurado na borda
    const val SWIM_SPEED = 1.5f
    const val SIT_SEAT_Y = 0.06f   // altura do assento sentado na borda branca (topo da borda)
    const val SIT_WAIT = 1.3f      // sentado na borda: depois deste tempo (s) ele entra na água sozinho
    const val ENTER_T = 1.0f       // duração de escorregar da borda para a água (s)
    const val ENTER_DIST = 0.9f    // quanto ele entra na água, a partir da borda (m, altura 1,0)
    const val EDGE_HOLD = 0.25f    // tempo (s) empurrando o analógico contra a água, andando, até sentar na borda
    const val INSET = 0.35f        // o quadril não chega mais perto que isto da parede

    fun x0(gw: Int): Float = gw / 2f - IW / 2f
    fun x1(gw: Int): Float = gw / 2f + IW / 2f

    /** (x, z) cai na água (com folga [m] para dentro)? */
    fun inWater(gw: Int, x: Float, z: Float, m: Float = 0f): Boolean =
        x > x0(gw) + m && x < x1(gw) - m && z > Z0 + m && z < Z1 - m

    /** Ponto bloqueado para quem anda: água mais um pouco da borda (o deck e a borda branca ficam livres). */
    fun blocksWalker(gw: Int, x: Float, z: Float): Boolean = inWater(gw, x, z, -0.12f)

    /** Avanço do quadril (m, altura 1,0) no clipe de mergulho, a cada 0,15 s (do 1º quadro até 1,2 s). Os clipes não trazem deslocamento: o jogo move o jogador por esta tabela. */
    private val DIVE_Z = floatArrayOf(0f, 0.427f, 0.918f, 1.32f, 1.745f, 2.216f, 2.724f, 3.182f, 3.591f)
    /** Idem para "nadar até a borda", a cada 0,15 s até 3,6 s (EDGE_END_T); depois fica parado. */
    private val EDGE_Z = floatArrayOf(0.0f, 0.03f, 0.069f, 0.116f, 0.172f, 0.233f, 0.291f, 0.334f, 0.357f, 0.386f, 0.435f, 0.477f, 0.497f, 0.512f, 0.553f, 0.613f, 0.663f, 0.704f, 0.745f, 0.784f, 0.816f, 0.837f, 0.847f, 0.845f, 0.835f)

    private fun tab(t: FloatArray, time: Float): Float {
        val u = (time / 0.15f).coerceAtLeast(0f)
        val i = u.toInt()
        if (i >= t.size - 1) return t[t.size - 1]
        return t[i] + (t[i + 1] - t[i]) * (u - i)
    }
    /** Quanto o quadril já avançou (m, altura 1,0) [time] segundos depois do começo do mergulho / da saída. */
    fun diveZ(time: Float): Float = tab(DIVE_Z, time)
    fun edgeZ(time: Float): Float = tab(EDGE_Z, time)
    val DIVE_END: Float get() = DIVE_Z[DIVE_Z.size - 1]
    val EDGE_END: Float get() = EDGE_Z[EDGE_Z.size - 1]

    /** Em que instante (s) do mergulho o quadril já avançou [d] metros (altura 1,0). Usado para entrar no meio do clipe quando o jogador está perto da água. */
    fun diveTimeAt(d: Float): Float {
        if (d <= 0f) return 0f
        for (i in 1 until DIVE_Z.size) if (d <= DIVE_Z[i]) return (i - 1 + (d - DIVE_Z[i - 1]) / (DIVE_Z[i] - DIVE_Z[i - 1])) * 0.15f
        return 1.2f
    }
}
