package com.vinicius.meular

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * Etapa 145: elevados (vias expressas suspensas) com alças de subida e descida.
 * Cada elevado corre sobre o canteiro central de uma avenida larga (24 m): pista de 9 m, 1 faixa por sentido,
 * a 7,5 m de altura, pilares em T fora dos cruzamentos, rampas sobre aterro com muro de contenção nas pontas.
 * O carro e o personagem podem subir pelas alças, andar lá em cima e descer; por baixo a avenida continua livre.
 */
object Elevado {
    const val HW = 4.5f          // meia largura do tabuleiro
    const val TOP = 7.5f         // altura da pista
    const val RAMP = 100f        // comprimento de cada alça

    /** axis 0: corre em x com z = c; axis 1: corre em z com x = c. a0..a1 = extensão; nome na placa. */
    class E(val axis: Int, val c: Float, val a0: Float, val a1: Float, val name: String) {
        val pillars = ArrayList<Float>()
        fun prof(s: Float): Float {
            if (s < a0 || s > a1) return Float.NaN
            val t = min(1f, min((s - a0) / RAMP, (a1 - s) / RAMP))
            return TOP * t * t * (3 - 2 * t)
        }
        fun sOf(x: Float, z: Float) = if (axis == 0) x else z
        fun lat(x: Float, z: Float) = if (axis == 0) z - c else x - c
        fun px(s: Float, l: Float) = if (axis == 0) s else c + l
        fun pz(s: Float, l: Float) = if (axis == 0) c + l else s
    }
    val list = ArrayList<E>()

    /** Monta os elevados a partir das avenidas do plano (chamar depois de Town.build). */
    fun plan() {
        list.clear(); edgeSet.clear()
        if (!City.TOWN) return
        // Etapa 146: tenta as quatro avenidas largas e fica com as que cabem sem cruzar outro elevado no mesmo nível
        fit(0, TownPlan.ZS[1], TownPlan.XS[0] + 30f, TownPlan.XS[TownPlan.N] - 30f, "Elevado Paulista")
        fit(0, TownPlan.ZS[3], TownPlan.XS[0] + 30f, TownPlan.XS[TownPlan.N] - 30f, "Elevado Atlântica")
        fit(1, TownPlan.XS[2], TownPlan.ZS[0] + 30f, TownPlan.ZS[TownPlan.N] - 40f, "Elevado Brasil")
        fit(1, TownPlan.XS[1], TownPlan.ZS[0] + 30f, TownPlan.ZS[TownPlan.N] - 40f, "Elevado Santos Dumont")
    }

    /** Ajusta as pontas para as alças não caírem em cruzamento e põe pilares longe das ruas transversais. */
    private fun fit(axis: Int, c: Float, s0: Float, s1: Float, name: String) {
        val cross = ArrayList<Float>()
        for (n in Town.nodes) { val s = if (axis == 0) n.x else n.z; val l = if (axis == 0) n.z - c else n.x - c; if (abs(l) < 18f + n.r) cross.add(s) }
        // só o trecho baixo da alça (até ~5 m de altura) precisa ficar longe de cruzamento; por cima dá para passar
        fun clearRamp(a: Float, b: Float) = cross.none { it > a && it < b }
        var a0 = s0; var k = 0; while (k < 120 && !clearRamp(a0 - 12f, a0 + 70f)) { a0 += 4f; k++ }
        var a1 = s1; k = 0; while (k < 120 && !clearRamp(a1 - 70f, a1 + 12f)) { a1 -= 4f; k++ }
        if (a1 - a0 < RAMP * 2.5f) return
        // não pode cruzar um elevado já aceito (os dois estariam na mesma altura)
        for (o in list) if (o.axis != axis) { val so = c; val sm = o.c; if (sm > a0 - 10f && sm < a1 + 10f && so > o.a0 - 10f && so < o.a1 + 10f) return }
        val e = E(axis, c, a0, a1, name)
        var s = a0 + RAMP * 0.75f
        while (s < a1 - RAMP * 0.75f) {
            val near = cross.any { abs(it - s) < 17f }
            if (!near) { e.pillars.add(s); s += 30f } else s += 3f
        }
        list.add(e)
        for ((ei, ed) in Town.edges.withIndex()) { val m = ed.pts.size / 4 * 2; val x = ed.pts[m]; val z = ed.pts[m + 1]
            if (abs(e.lat(x, z)) < 3f && e.sOf(x, z) > e.a0 - 15f && e.sOf(x, z) < e.a1 + 15f) edgeSet.add(ei) }
    }
    /** Ruas que passam por baixo de um elevado: os carros usam só a faixa da direita (a de dentro tem pilar e aterro). */
    val edgeSet = HashSet<Int>()
    /** O ponto está debaixo de algum elevado (para não plantar árvore no canteiro)? */
    fun covers(x: Float, z: Float) = list.any { abs(it.lat(x, z)) < HW + 1f && it.sOf(x, z) > it.a0 - 3f && it.sOf(x, z) < it.a1 + 3f }

    // ---------------------------------------------------------------- superfície e colisão
    /** Altura da pista sob (x, z) para quem está em refY (só vale se estiver na mesma camada); NaN se não está no elevado. */
    fun surface(x: Float, z: Float, refY: Float): Float {
        var best = Float.NaN
        for (e in list) {
            if (abs(e.lat(x, z)) > HW) continue
            val y = e.prof(e.sOf(x, z)); if (y.isNaN()) continue
            if (refY > y - 1.3f && refY < y + 1.3f && (best.isNaN() || y > best)) best = y
        }
        return best
    }

    private fun blocked(x: Float, z: Float, ref: Float, upMin: Float, onTol: Float, clear: Float, rail: Float, pr: Float): Boolean {
        for (e in list) {
            val s = e.sOf(x, z); val l = abs(e.lat(x, z))
            if (s < e.a0 - 1f || s > e.a1 + 1f || l > 12f) continue
            val y = e.prof(s.coerceIn(e.a0, e.a1))
            val onDeck = ref > upMin && abs(ref - y) < onTol
            if (onDeck) { if (l > rail) return true; continue }
            if (l < HW + 0.2f && y > upMin && y < clear) return true                 // por baixo da alça baixa: aterro
            for (p in e.pillars) if (abs(s - p) < pr && l < pr) return true          // pilar
        }
        return false
    }
    fun blockedCar(x: Float, z: Float, ref: Float) = list.isNotEmpty() && blocked(x, z, ref, 0.9f, 1.6f, 4.6f, HW - 0.45f, 0.95f)
    fun blockedWalk(x: Float, z: Float, ref: Float) = list.isNotEmpty() && blocked(x, z, ref, 0.45f, 1.0f, 2.3f, HW - 0.35f, 1.0f)

    // ---------------------------------------------------------------- geometria
    /** Um pedaço de cada elevado por chunk (~120 m), sempre carregado. */
    fun chunks(out: ArrayList<City.Chunk>) {
        for (e in list) {
            var s = e.a0
            while (s < e.a1 - 0.5f) {
                val t = min(e.a1, s + 120f)
                val b = MB(); piece(b, e, s, t)
                val m = b.toMesh(true)
                val x0 = min(e.px(s, -12f), e.px(t, 12f)); val x1 = max(e.px(s, -12f), e.px(t, 12f))
                val z0 = min(e.pz(s, -12f), e.pz(t, 12f)); val z1 = max(e.pz(s, -12f), e.pz(t, 12f))
                out.add(City.Chunk(m, null, x0, z0, x1, z1, TOP + 6f))
                s = t
            }
        }
    }

    private val CON = C("#B9B4AA"); private val CON_D = C("#8F8A80"); private val ASPH = C("#4A4C50"); private val RAILC = C("#D6D2C8")

    /** Quadrilátero com normal calculada (a, b, c, d em sentido anti-horário visto de fora). */
    private fun q(b: MB, p: FloatArray, col: Int) {
        val ux = p[3] - p[0]; val uy = p[4] - p[1]; val uz = p[5] - p[2]; val vx = p[9] - p[0]; val vy = p[10] - p[1]; val vz = p[11] - p[2]
        var nx = uy * vz - uz * vy; var ny = uz * vx - ux * vz; var nz = ux * vy - uy * vx; val nl = max(1e-5f, kotlin.math.sqrt(nx * nx + ny * ny + nz * nz)); nx /= nl; ny /= nl; nz /= nl
        val ax = if (abs(ny) > 0.6f) 1 else if (abs(nx) > abs(nz)) 0 else 2
        fun v(i: Int) { val x = p[i * 3]; val y = p[i * 3 + 1]; val z = p[i * 3 + 2]; when (ax) { 0 -> b.v(x, y, z, nx, ny, nz, col, z, y); 1 -> b.v(x, y, z, nx, ny, nz, col, x, z); else -> b.v(x, y, z, nx, ny, nz, col, x, y) } }
        for (i in intArrayOf(0, 1, 2, 0, 2, 3)) v(i)
        for (i in intArrayOf(0, 2, 1, 0, 3, 2)) { val x = p[i * 3]; val y = p[i * 3 + 1]; val z = p[i * 3 + 2]; b.v(x, y, z, -nx, -ny, -nz, col, if (ax == 0) z else x, if (ax == 1) z else y) }
    }
    /** Faixa ao longo do elevado entre as laterais l0..l1, de s0 a s1, com altura y(s) + dy (topo) — passos de 5 m. */
    private fun strip(b: MB, e: E, s0: Float, s1: Float, l0: Float, l1: Float, dy: Float, col: Int) {
        var s = s0
        while (s < s1 - 0.01f) { val t = min(s1, s + 5f); val ya = e.prof(s) + dy; val yb = e.prof(t) + dy
            q(b, floatArrayOf(e.px(s, l0), ya, e.pz(s, l0), e.px(t, l0), yb, e.pz(t, l0), e.px(t, l1), yb, e.pz(t, l1), e.px(s, l1), ya, e.pz(s, l1)), col); s = t }
    }
    /** Parede vertical ao longo do elevado na lateral l, entre y(s)+top e y(s)+bot (bot pode ser chão: use -1e9 para 0). */
    private fun side(b: MB, e: E, s0: Float, s1: Float, l: Float, bot: Float, top: Float, col: Int, ground: Boolean = false) {
        var s = s0
        while (s < s1 - 0.01f) { val t = min(s1, s + 5f); val ya = e.prof(s); val yb = e.prof(t)
            val a0 = if (ground) 0f else ya + bot; val b0 = if (ground) 0f else yb + bot
            q(b, floatArrayOf(e.px(s, l), a0, e.pz(s, l), e.px(t, l), b0, e.pz(t, l), e.px(t, l), yb + top, e.pz(t, l), e.px(s, l), ya + top, e.pz(s, l)), col); s = t }
    }

    private fun piece(b: MB, e: E, s0: Float, s1: Float) {
        // pista: asfalto, laje (espessura 0,9 m) e vigas por baixo
        b.m(Mt.ASPHALT, 0.25f); strip(b, e, s0, s1, -HW, HW, 0.02f, ASPH)
        b.m(Mt.STONE, 0.5f)
        strip(b, e, s0, s1, -HW - 0.35f, HW + 0.35f, -0.9f, CON_D)
        side(b, e, s0, s1, -HW - 0.35f, -0.9f, 0.02f, CON); side(b, e, s0, s1, HW + 0.35f, -0.9f, 0.02f, CON)
        for (l in floatArrayOf(-2.6f, 0f, 2.6f)) { side(b, e, s0, s1, l - 0.35f, -1.6f, -0.9f, CON_D); side(b, e, s0, s1, l + 0.35f, -1.6f, -0.9f, CON_D); strip(b, e, s0, s1, l - 0.35f, l + 0.35f, -1.6f, CON_D) }
        // sinalização: faixa dupla amarela no meio, brancas nas bordas, tachões
        b.m(Mt.PLAIN)
        strip(b, e, s0, s1, -0.22f, -0.1f, 0.035f, C("#F2C230")); strip(b, e, s0, s1, 0.1f, 0.22f, 0.035f, C("#F2C230"))
        strip(b, e, s0, s1, -HW + 0.35f, -HW + 0.5f, 0.035f, C("#F4F4F0")); strip(b, e, s0, s1, HW - 0.5f, HW - 0.35f, 0.035f, C("#F4F4F0"))
        // barreiras tipo New Jersey (base larga, topo estreito) dos dois lados
        b.m(Mt.STONE, 0.5f)
        for (sg in floatArrayOf(-1f, 1f)) {
            val lo = sg * HW; val li = sg * (HW - 0.4f); val lt = sg * (HW - 0.15f)
            side(b, e, s0, s1, li, 0.02f, 0.35f, RAILC); side(b, e, s0, s1, lt, 0.35f, 1.0f, RAILC)
            side(b, e, s0, s1, lo + sg * 0.35f, 0.02f, 1.0f, CON)
            strip(b, e, s0, s1, min(lt, lo + sg * 0.35f), max(lt, lo + sg * 0.35f), 1.0f, RAILC)
            strip(b, e, s0, s1, min(li, lt), max(li, lt), 0.35f, RAILC)
        }
        // aterro com muro de contenção onde a alça ainda é baixa (passar por baixo não dá)
        var s = s0
        while (s < s1 - 0.01f) {
            val t = min(s1, s + 5f)
            if (e.prof(t) < 5.2f || e.prof(s) < 5.2f) { b.m(Mt.STONE, 0.6f); side(b, e, s, t, -HW - 0.36f, 0f, -0.9f, C("#A39B8E"), true); side(b, e, s, t, HW + 0.36f, 0f, -0.9f, C("#A39B8E"), true) }
            s = t
        }
        // pilares em T
        for (p in e.pillars) if (p >= s0 && p < s1) {
            val y = e.prof(p) - 1.6f
            b.m(Mt.STONE, 0.5f)
            b.box(e.px(p, 0f), y / 2, e.pz(p, 0f), 1.5f, y, 1.5f, CON)
            val cw = if (e.axis == 0) 1.6f else HW * 2 + 0.4f; val cd = if (e.axis == 0) HW * 2 + 0.4f else 1.6f
            b.box(e.px(p, 0f), y - 0.45f, e.pz(p, 0f), cw, 0.9f, cd, CON_D)
            b.m(Mt.PLAIN); b.box(e.px(p, 0f), 0.6, e.pz(p, 0f), 1.56f, 0.5f, 1.56f, C("#F2C230")); b.box(e.px(p, 0f), 0.85, e.pz(p, 0f), 1.57f, 0.12f, 1.57f, C("#222222"))
        }
        // postes de luz no tabuleiro, alternando de lado a cada 40 m
        var lp = Math.ceil((s0 - e.a0) / 40.0).toFloat() * 40f + e.a0
        var k = ((lp - e.a0) / 40f).toInt()
        while (lp < s1) {
            if (lp > e.a0 + 10f && lp < e.a1 - 10f) {
                val sg = if (k % 2 == 0) -1f else 1f; val y = e.prof(lp) + 1.0f; val l = sg * (HW - 0.2f)
                b.m(Mt.METAL); b.cyl(e.px(lp, l), y, e.pz(lp, l), 0.1f, 0.07f, 7.5f, C("#6E747A"), true, 6)
                val al = sg * (HW - 1.8f)
                b.box((e.px(lp, l) + e.px(lp, al)) / 2, y + 7.4f, (e.pz(lp, l) + e.pz(lp, al)) / 2, if (e.axis == 0) 0.12f else 1.7f, 0.1f, if (e.axis == 0) 1.7f else 0.12f, C("#6E747A"))
                b.box(e.px(lp, al), y + 7.28f, e.pz(lp, al), 0.6f, 0.14f, 0.6f, C("#5A5F64")); b.m(Mt.PLAIN); b.box(e.px(lp, al), y + 7.2f, e.pz(lp, al), 0.5f, 0.02f, 0.5f, C("#FFF2C0"), false)
            }
            lp += 40f; k++
        }
        // pórticos com placa verde perto de cada alça
        for (gs in floatArrayOf(e.a0 + RAMP + 25f, e.a1 - RAMP - 25f)) if (gs >= s0 && gs < s1) {
            val y = e.prof(gs)
            b.m(Mt.METAL)
            for (sg in floatArrayOf(-1f, 1f)) b.box(e.px(gs, sg * (HW + 0.1f)), y + 3.0f, e.pz(gs, sg * (HW + 0.1f)), 0.25f, 6.0f, 0.25f, C("#7A8086"))
            b.box(e.px(gs, 0f), y + 5.9f, e.pz(gs, 0f), if (e.axis == 0) 0.3f else HW * 2 + 0.6f, 0.25f, if (e.axis == 0) HW * 2 + 0.6f else 0.3f, C("#7A8086"))
            b.m(Mt.PLAIN)
            for (sg in floatArrayOf(-1f, 1f)) {
                val l = sg * 2.2f; val face = if (e.axis == 0) 0.12f else 3.6f; val faceZ = if (e.axis == 0) 3.6f else 0.12f
                b.box(e.px(gs, l), y + 4.6f, e.pz(gs, l), face, 1.4f, faceZ, C("#0F6B3A"))
                for (r in 0..1) b.box(e.px(gs, l), y + 4.85f + r * 0.5f, e.pz(gs, l), if (e.axis == 0) 0.14f else 2.6f - r * 0.8f, 0.14f, if (e.axis == 0) 2.6f - r * 0.8f else 0.14f, C("#FFFFFF"), false)
            }
        }
    }
}
