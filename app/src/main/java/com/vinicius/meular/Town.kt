package com.vinicius.meular

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Etapa 131: motor novo da cidade — ruas como um grafo de curvas (não mais uma grade).
 *
 *  - cada rua é uma curva (Bézier cúbica) entre dois cruzamentos, com largura própria;
 *  - o asfalto, as calçadas, as guias, as faixas e as faixas de pedestre seguem a curva;
 *  - cada cruzamento é um polígono com cantos arredondados (guias em curva), rotatória ou bolsão de rua sem saída;
 *  - os quarteirões saem sozinhos das faces do grafo (polígonos livres, triangulados);
 *  - chão, colisão e trânsito consultam essa geometria (grade espacial de 16 m).
 */
object Town {
    const val SW = 3.5f            // largura da calçada
    const val CURB = 0.15f
    const val FILLET = 6.5f        // raio da curva da guia nas esquinas
    const val STEP = 2f            // espaçamento dos pontos ao longo das ruas

    class Node(val x: Float, val z: Float, val round: Float = 0f) {
        val edges = ArrayList<Int>()
        var r = 0f                                  // raio do cruzamento (onde as ruas começam)
        var poly = FloatArray(0)                    // contorno do asfalto do cruzamento (x, z), anti-horário
        var sorted = IntArray(0)                    // ruas em volta, por ângulo
        val corners = HashMap<Int, FloatArray>()    // rua -> curva da guia até a próxima rua (x, z)
    }

    class Edge(var a: Int, var b: Int, val w: Float, val bend: Float, val name: String) {
        /** pontos de controle da curva (Bézier cúbica a → c1 → c2 → b) */
        var c1x = 0f; var c1z = 0f; var c2x = 0f; var c2z = 0f
        /** distrito (para o que for construído dos lados) */
        var kind = 0
        var pts = FloatArray(0)     // eixo já cortado nos cruzamentos (x, z)
        var len = 0f
        val avenue get() = w >= 22f
    }

    val nodes = ArrayList<Node>()
    val edges = ArrayList<Edge>()
    /** Quarteirões: contorno (x, z) — por dentro da calçada. */
    val blocks = ArrayList<FloatArray>()
    var homeBlock = -1
    @Volatile var on = false
    var minX = 0f; var maxX = 0f; var minZ = 0f; var maxZ = 0f

    // ------------------------------------------------------------ planta

    fun n(x: Float, z: Float, round: Float = 0f): Int { nodes.add(Node(x, z, round)); return nodes.size - 1 }
    fun e(a: Int, b: Int, w: Float, bend: Float, name: String): Int {
        val ed = Edge(a, b, w, bend, name)
        val A = nodes[a]; val B = nodes[b]
        val dx = B.x - A.x; val dz = B.z - A.z; val l = max(1e-3f, hypot(dx, dz))
        val nx = -dz / l * bend; val nz = dx / l * bend
        ed.c1x = A.x + dx / 3 + nx; ed.c1z = A.z + dz / 3 + nz; ed.c2x = A.x + dx * 2 / 3 + nx; ed.c2z = A.z + dz * 2 / 3 + nz
        edges.add(ed); A.edges.add(edges.size - 1); B.edges.add(edges.size - 1)
        return edges.size - 1
    }

    /** Ponto da curva da rua no parâmetro t. */
    fun at(ed: Edge, t: Float): FloatArray {
        val a = nodes[ed.a]; val b = nodes[ed.b]; val u = 1 - t
        return floatArrayOf(u * u * u * a.x + 3 * u * u * t * ed.c1x + 3 * u * t * t * ed.c2x + t * t * t * b.x,
                            u * u * u * a.z + 3 * u * u * t * ed.c1z + 3 * u * t * t * ed.c2z + t * t * t * b.z)
    }

    /** Divide a rua no parâmetro t (de Casteljau): devolve o nó novo. */
    fun split(ei: Int, t: Float): Int {
        val ed = edges[ei]; val A = nodes[ed.a]; val B = nodes[ed.b]
        fun l(a: Float, b: Float) = a + (b - a) * t
        val q0x = l(A.x, ed.c1x); val q0z = l(A.z, ed.c1z); val q1x = l(ed.c1x, ed.c2x); val q1z = l(ed.c1z, ed.c2z); val q2x = l(ed.c2x, B.x); val q2z = l(ed.c2z, B.z)
        val r0x = l(q0x, q1x); val r0z = l(q0z, q1z); val r1x = l(q1x, q2x); val r1z = l(q1z, q2z)
        val sx = l(r0x, r1x); val sz = l(r0z, r1z)
        val ni = n(sx, sz)
        val ob = ed.b
        val e2 = Edge(ni, ob, ed.w, 0f, ed.name); e2.kind = ed.kind
        e2.c1x = r1x; e2.c1z = r1z; e2.c2x = q2x; e2.c2z = q2z
        ed.b = ni; ed.c1x = q0x; ed.c1z = q0z; ed.c2x = r0x; ed.c2z = r0z
        edges.add(e2); val i2 = edges.size - 1
        nodes[ob].edges.remove(ei); nodes[ob].edges.add(i2)
        nodes[ni].edges.add(ei); nodes[ni].edges.add(i2)
        return ni
    }

    /** Divide a rua que passa mais perto de (x, z) no ponto mais próximo (para ligar ruas novas às existentes). */
    fun splitNear(x: Float, z: Float, only: Set<Int>? = null, reuse: Boolean = true, reuseDist: Float = 38f): Int {
        var be = -1; var bt = 0f; var bd = Float.MAX_VALUE
        for ((ei, ed) in edges.withIndex()) {
            if (only != null && ei !in only) continue
            for (k in 0..64) { val t = k / 64f; val p = at(ed, t); val d = hypot(p[0] - x, p[1] - z); if (d < bd) { bd = d; be = ei; bt = t } }
        }
        val ed = edges[be]
        var lo = max(0f, bt - 1 / 64f); var hi = min(1f, bt + 1 / 64f)
        repeat(20) { val m1 = lo + (hi - lo) / 3; val m2 = hi - (hi - lo) / 3; val p1 = at(ed, m1); val p2 = at(ed, m2); if (hypot(p1[0] - x, p1[1] - z) < hypot(p2[0] - x, p2[1] - z)) hi = m2 else lo = m1 }
        val t = (lo + hi) / 2
        // já existe uma ligação (T) bem perto do outro lado da rua: vira um cruzamento só
        val p = at(ed, t)
        if (reuse) for (k in intArrayOf(ed.a, ed.b)) { val nd = nodes[k]; if (nd.edges.size == 3 && hypot(nd.x - p[0], nd.z - p[1]) < reuseDist) return k }
        if (t < 0.02f) return ed.a
        if (t > 0.98f) return ed.b
        return split(be, t)
    }

    /** Traçado da cidade. A casa fica em x [-10, 36], z [-22, 39]; o quarteirão dela é 0-1-2-3. */
    private fun layout() {
        nodes.clear(); edges.clear()
        val hNW = n(-45f, -60f); val hNE = n(75f, -55f); val hSE = n(78f, 54f); val hSW = n(-48f, 54f)
        e(hNW, hNE, 14f, 4f, "R. dos Ipês"); e(hNE, hSE, 14f, -5f, "R. das Flores"); e(hSE, hSW, 14f, 0f, "R. Aurora"); e(hSW, hNW, 14f, 3f, "R. da Paz")
        // avenida leste-oeste com a rotatória
        val aW = n(-300f, 125f); val aM = n(-52f, 142f, 21f); val aE = n(92f, 146f); val rot = n(205f, 130f, 26f); val aE2 = n(335f, 92f)
        e(aW, aM, 24f, 16f, "Av. Atlântica"); e(aM, aE, 24f, -6f, "Av. Atlântica"); e(aE, rot, 24f, 8f, "Av. Atlântica"); e(rot, aE2, 24f, 0f, "Av. Atlântica")
        e(hSW, aM, 14f, 6f, "R. do Sol"); e(hSE, aE, 14f, -5f, "R. Primavera")
        // avenida norte-sul
        val nN = n(190f, -290f); val nC = n(204f, -52f)
        val sS = n(150f, 335f)
        e(nN, nC, 24f, 22f, "Av. Brasil"); e(nC, rot, 24f, -4f, "Av. Brasil"); e(rot, sS, 24f, 26f, "Av. Brasil")
        e(hNE, nC, 16f, 9f, "R. das Palmeiras")
        // oeste
        val w1 = n(-200f, -82f); e(hNW, w1, 16f, -10f, "Av. das Nações"); e(w1, aW, 16f, 30f, "R. do Porto")
        // norte
        val nw = n(-215f, -282f); val nm = n(-32f, -288f)
        e(w1, nw, 14f, 26f, "R. Aurora"); e(nw, nm, 16f, 22f, "Av. Central"); e(nm, nN, 16f, -24f, "Av. Central")
        val m1 = n(-38f, -196f); e(hNW, m1, 14f, 8f, "R. das Acácias"); e(m1, nm, 14f, -4f, "R. das Acácias")
        val m2 = n(82f, -178f); e(hNE, m2, 14f, 6f, "R. Bela Vista"); e(m2, m1, 14f, -6f, "R. do Mirante")
        // leste
        val e1 = n(335f, -62f); val ne = n(335f, -282f)
        e(nC, e1, 16f, -8f, "R. dos Andradas"); e(e1, aE2, 16f, 22f, "R. Leste"); e(nN, ne, 14f, -18f, "Av. Central"); e(ne, e1, 14f, 26f, "R. Leste")
        // sul
        val sw = n(-292f, 322f); val sm = n(-62f, 334f); val s3 = n(82f, 246f); val se = n(334f, 330f)
        e(aW, sw, 14f, 30f, "R. do Porto"); e(sw, sm, 14f, -28f, "R. das Gaivotas"); e(aM, sm, 16f, -15f, "R. Esperança")
        e(sm, sS, 16f, 22f, "R. das Gaivotas"); e(aE, s3, 14f, 12f, "R. Jardim"); e(s3, sm, 14f, 6f, "R. dos Coqueiros")
        e(aE2, se, 14f, 26f, "R. Leste"); e(se, sS, 14f, -30f, "R. das Gaivotas")
        // rua sem saída (vila) saindo da R. dos Coqueiros
        val cul = n(4f, 214f); e(s3, cul, 12f, 4f, "Vila das Rosas")
    }

    // ------------------------------------------------------------ geometria

    private fun bez(a: Node, b: Node, ed: Edge, t: Float, out: FloatArray) {
        val c1x = ed.c1x; val c1z = ed.c1z; val c2x = ed.c2x; val c2z = ed.c2z
        val u = 1 - t
        out[0] = u * u * u * a.x + 3 * u * u * t * c1x + 3 * u * t * t * c2x + t * t * t * b.x
        out[1] = u * u * u * a.z + 3 * u * u * t * c1z + 3 * u * t * t * c2z + t * t * t * b.z
    }

    /** Eixo da rua de r0 (início) até len - r1, reamostrado a cada STEP m. */
    private fun sample(ed: Edge) {
        val a = nodes[ed.a]; val b = nodes[ed.b]
        val N = 400; val xs = FloatArray(N + 1); val zs = FloatArray(N + 1); val ls = FloatArray(N + 1)
        val p = FloatArray(2)
        for (i in 0..N) { bez(a, b, ed, i / N.toFloat(), p); xs[i] = p[0]; zs[i] = p[1]; if (i > 0) ls[i] = ls[i - 1] + hypot(xs[i] - xs[i - 1], zs[i] - zs[i - 1]) }
        // corta onde a curva sai do círculo de cada cruzamento
        var s0 = 0f; for (i in 0..N) if (hypot(xs[i] - a.x, zs[i] - a.z) >= a.r) { s0 = ls[i]; break }
        var s1 = ls[N]; for (i in N downTo 0) if (hypot(xs[i] - b.x, zs[i] - b.z) >= b.r) { s1 = ls[i]; break }
        val L = max(0.5f, s1 - s0)
        val k = max(1, Math.round(L / STEP))
        val out = FloatArray((k + 1) * 2)
        var j = 0
        for (q in 0..k) {
            val s = s0 + L * q / k
            while (j < N - 1 && ls[j + 1] < s) j++
            val f = ((s - ls[j]) / max(1e-5f, ls[j + 1] - ls[j])).coerceIn(0f, 1f)
            out[q * 2] = xs[j] + (xs[j + 1] - xs[j]) * f; out[q * 2 + 1] = zs[j] + (zs[j + 1] - zs[j]) * f
        }
        ed.pts = out; ed.len = L
    }

    /** Direção (unitária) do eixo no ponto i. */
    private fun tan(p: FloatArray, i: Int): FloatArray {
        val n = p.size / 2
        val a = max(0, i - 1); val b = min(n - 1, i + 1)
        val dx = p[b * 2] - p[a * 2]; val dz = p[b * 2 + 1] - p[a * 2 + 1]; val l = max(1e-5f, hypot(dx, dz))
        return floatArrayOf(dx / l, dz / l)
    }

    /** Ponta da rua [ei] no cruzamento [ni]: (x, z, dirX, dirZ) com a direção apontando para fora do cruzamento. */
    private fun endOf(ei: Int, ni: Int): FloatArray {
        val ed = edges[ei]; val p = ed.pts; val n = p.size / 2
        return if (ed.a == ni) { val t = tan(p, 0); floatArrayOf(p[0], p[1], t[0], t[1]) }
        else { val t = tan(p, n - 1); floatArrayOf(p[(n - 1) * 2], p[(n - 1) * 2 + 1], -t[0], -t[1]) }
    }

    /** Lado esquerdo/direito (s = direção girada +90°) da ponta, na distância d do eixo. */
    private fun side(en: FloatArray, d: Float) = floatArrayOf(en[0] - en[3] * d, en[1] + en[2] * d)

    private fun quadBez(p0: FloatArray, c: FloatArray, p1: FloatArray, n: Int): FloatArray {
        val o = FloatArray((n + 1) * 2)
        for (i in 0..n) {
            val t = i / n.toFloat(); val u = 1 - t
            o[i * 2] = u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0]
            o[i * 2 + 1] = u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1]
        }
        return o
    }

    /** Interseção das retas p + t·d e q + u·e; null se quase paralelas. Devolve (x, z, t, u). */
    private fun cross(p: FloatArray, d: FloatArray, q: FloatArray, e: FloatArray): FloatArray? {
        val den = d[0] * e[1] - d[1] * e[0]
        if (abs(den) < 0.08f) return null
        val wx = q[0] - p[0]; val wz = q[1] - p[1]
        val t = (wx * e[1] - wz * e[0]) / den; val u = (wx * d[1] - wz * d[0]) / den
        return floatArrayOf(p[0] + d[0] * t, p[1] + d[1] * t, t, u)
    }

    /** Ângulo (0..2π] de uma ponta de rua até a próxima, no sentido anti-horário. */
    private fun gapE(a: FloatArray, b: FloatArray): Float { var g = atan2(b[3], b[2]) - atan2(a[3], a[2]); while (g <= 0f) g += 2 * PI.toFloat(); return g }

    private fun buildNodes() {
        for (nd in nodes) {
            var hw = 0f; for (ei in nd.edges) hw = max(hw, edges[ei].w / 2)
            nd.r = when {
                nd.round > 0f -> nd.round + 2f
                nd.edges.size == 1 -> hw + 7f            // bolsão de retorno
                nd.edges.size == 2 -> hw + 4f
                else -> hw + FILLET
            }
        }
        for (ed in edges) sample(ed)
        // esquinas agudas: o cruzamento cresce até as bordas das duas ruas se encontrarem dentro dele
        for (pass in 0 until 2) {
            var grew = false
            for ((ni, nd) in nodes.withIndex()) {
                if (nd.edges.size < 2) continue
                val ends = nd.edges.map { endOf(it, ni) }
                val ord = nd.edges.indices.sortedBy { atan2(ends[it][1] - nd.z, ends[it][0] - nd.x) }
                for (k in ord.indices) {
                    val a = ord[k]; val b = ord[(k + 1) % ord.size]
                    val g = gapE(ends[a], ends[b])
                    if (g >= PI.toFloat() * 0.95f) continue
                    val hw = max(edges[nd.edges[a]].w, edges[nd.edges[b]].w) / 2
                    val need = hw / kotlin.math.tan(g / 2) + 4f
                    if (need > nd.r + 0.5f) { nd.r = min(need, 60f); grew = true }
                }
            }
            if (!grew) break
            for (ed in edges) sample(ed)
        }
        for ((ni, nd) in nodes.withIndex()) {
            val ends = nd.edges.map { endOf(it, ni) }
            val ord = nd.edges.indices.sortedBy { atan2(ends[it][1] - nd.z, ends[it][0] - nd.x) }
            nd.sorted = IntArray(ord.size) { nd.edges[ord[it]] }
            val poly = ArrayList<Float>()
            for ((k, oi) in ord.withIndex()) {
                val ei = nd.edges[oi]; val en = ends[oi]; val hw = edges[ei].w / 2
                val nxt = ord[(k + 1) % ord.size]; val en2 = ends[nxt]; val hw2 = edges[nd.edges[nxt]].w / 2
                val pR = side(en, -hw); val pL = side(en, hw)
                poly.add(pR[0]); poly.add(pR[1]); poly.add(pL[0]); poly.add(pL[1])
                val q = side(en2, -hw2)
                val curve: FloatArray
                if (ord.size == 1 || nd.round > 0f) {
                    // bolsão ou rotatória: arco em volta do centro
                    val r0 = hypot(pL[0] - nd.x, pL[1] - nd.z); val r1 = hypot(q[0] - nd.x, q[1] - nd.z)
                    var a0 = atan2(pL[1] - nd.z, pL[0] - nd.x); var a1 = atan2(q[1] - nd.z, q[0] - nd.x)
                    while (a1 <= a0) a1 += 2 * PI.toFloat()
                    if (ord.size > 1 && gapE(en, en2) < PI.toFloat() && a1 - a0 > PI.toFloat()) { a1 = a0 + 0.01f; warn++ }
                    val m = max(6, ((a1 - a0) * 12).toInt()); curve = FloatArray((m + 1) * 2)
                    for (i in 0..m) { val t = i / m.toFloat(); val a = a0 + (a1 - a0) * t; val rr = r0 + (r1 - r0) * t; curve[i * 2] = nd.x + cos(a) * rr; curve[i * 2 + 1] = nd.z + sin(a) * rr }
                } else {
                    run { val a0 = atan2(pL[1] - nd.z, pL[0] - nd.x); var a1 = atan2(q[1] - nd.z, q[0] - nd.x); while (a1 <= a0) a1 += 2 * PI.toFloat(); if (gapE(en, en2) < PI.toFloat() && a1 - a0 > PI.toFloat()) { warn++; System.err.println("esquina apertada no nó $ni") } }
                    val c = cross(pL, floatArrayOf(-en[2], -en[3]), q, floatArrayOf(-en2[2], -en2[3]))
                    val ctl = if (c != null && c[2] > -1f && c[3] > -1f && c[2] < nd.r * 2.2f && c[3] < nd.r * 2.2f) floatArrayOf(c[0], c[1])
                              else floatArrayOf((pL[0] + q[0]) / 2, (pL[1] + q[1]) / 2)
                    curve = quadBez(pL, ctl, q, 10)
                }
                nd.corners[ei] = curve
                for (i in 1 until curve.size / 2 - 1) { poly.add(curve[i * 2]); poly.add(curve[i * 2 + 1]) }
            }
            nd.poly = poly.toFloatArray()
        }
    }

    // ------------------------------------------------------------ quarteirões (faces do grafo)

    /** Desloca a curva para o lado de fora do cruzamento (girando a tangente −90°). */
    private fun offsetOut(c: FloatArray, d: Float): FloatArray {
        val n = c.size / 2; val o = FloatArray(c.size)
        for (i in 0 until n) { val t = tan(c, i); o[i * 2] = c[i * 2] + t[1] * d; o[i * 2 + 1] = c[i * 2 + 1] - t[0] * d }
        return o
    }

    /** Lateral da rua: pontos do eixo deslocados por d (positivo = esquerda de quem anda de a para b). */
    private fun offsetEdge(p: FloatArray, d: Float): FloatArray {
        val n = p.size / 2; val o = FloatArray(p.size)
        for (i in 0 until n) { val t = tan(p, i); o[i * 2] = p[i * 2] - t[1] * d; o[i * 2 + 1] = p[i * 2 + 1] + t[0] * d }
        return o
    }

    private fun area(p: FloatArray): Float { var s = 0f; val n = p.size / 2; for (i in 0 until n) { val j = (i + 1) % n; s += p[i * 2] * p[j * 2 + 1] - p[j * 2] * p[i * 2 + 1] }; return s / 2 }

    private fun buildBlocks() {
        blocks.clear()
        val used = HashSet<Long>()
        fun key(e: Int, fwd: Boolean) = e.toLong() * 2 + (if (fwd) 1 else 0)
        val faces = ArrayList<FloatArray>()
        for (e0 in edges.indices) for (f0 in booleanArrayOf(true, false)) {
            if (key(e0, f0) in used) continue
            val pts = ArrayList<Float>()
            var e = e0; var fwd = f0; var guard = 0
            while (guard++ < 200) {
                if (!used.add(key(e, fwd))) break
                val ed = edges[e]
                val to = if (fwd) ed.b else ed.a
                // lateral direita de quem anda (calçada por fora)
                val off = offsetEdge(ed.pts, -(ed.w / 2 + SW))
                val n = off.size / 2
                if (fwd) for (i in 0 until n) { pts.add(off[i * 2]); pts.add(off[i * 2 + 1]) }
                else { val offL = offsetEdge(ed.pts, ed.w / 2 + SW); for (i in n - 1 downTo 0) { pts.add(offL[i * 2]); pts.add(offL[i * 2 + 1]) } }
                // esquina: próxima rua no sentido anti-horário a partir desta, no nó de chegada
                val nd = nodes[to]
                val k = nd.sorted.indexOf(e)
                val ne = nd.sorted[(k + 1) % nd.sorted.size]
                // esquina do quarteirão em ângulo (como a quina de um prédio): encontro das duas linhas de fora das calçadas;
                // a guia continua arredondada e o canto entre a calçada curva e a quina fica calçado/gramado
                val sharp = run {
                    if (nd.round > 0f || nd.edges.size < 3) return@run null
                    val enA = endOf(e, to); val enB = endOf(ne, to)
                    val gg = gapE(enA, enB); if (gg > PI.toFloat() * 0.65f || gg < PI.toFloat() * 0.35f) return@run null
                    val pa = side(enA, ed.w / 2 + SW); val pb = side(enB, -(edges[ne].w / 2 + SW))
                    val c = cross(pa, floatArrayOf(-enA[2], -enA[3]), pb, floatArrayOf(-enB[2], -enB[3])) ?: return@run null
                    if (c[2] < -1f || c[3] < -1f || c[2] > 25f || c[3] > 25f) return@run null
                    floatArrayOf(c[0], c[1])
                }
                if (sharp != null) { pts.add(sharp[0]); pts.add(sharp[1]) }
                else { val corner = offsetOut(nd.corners[e]!!, SW); for (i in 1 until corner.size / 2 - 1) { pts.add(corner[i * 2]); pts.add(corner[i * 2 + 1]) } }
                e = ne; fwd = edges[ne].a == to
                if (e == e0 && fwd == f0) break
            }
            faces.add(pts.toFloatArray())
        }
        // a face de fora (contorno da cidade) é a de maior área com sinal oposto
        var outer = -1; var big = 0f
        for ((i, f) in faces.withIndex()) { val a = abs(area(f)); if (a > big) { big = a; outer = i } }
        for ((i, f) in faces.withIndex()) if (i != outer && abs(area(f)) > 40f) blocks.add(clean(f))
        outline = if (outer >= 0) clean(faces[outer]) else FloatArray(0)
        homeBlock = blocks.indexOfFirst { inside(it, 13f, 8f) }
    }

    /** Quadra retangular do centro/comércio: retângulo útil (x0, z0, x1, z1) e o tipo do que é construído nela. */
    /**
     * Etapa 137: preenche o que sobra de cada quarteirão (miolo das superquadras, beira das avenidas, em volta da casa):
     * grade de ocupação de 4 m (livre = dentro do quarteirão, longe da calçada, fora dos lotes, parques e do terreno da casa);
     * o maior retângulo livre (até 90 m) recebe um conjunto do gerador de quarteirões (casas em fileira, condomínio, lojas,
     * mercado, escola, igreja, posto, prédios...), conforme o bairro; repete até não caber mais nada útil.
     */
    private fun infill() {
        val C = 4f
        val lotPolys = TownHouses.lots.map { TownHouses.corners(it) }
        var nRes = 0; var nCom = 0; var nDown = 0
        val resT = arrayOf("res", "apt", "res", "lots", "res", "apt", "res", "res", "apt")
        val comT = arrayOf("shops", "apt", "shops", "shops", "apt", "shops")
        val downT = arrayOf("down", "apt", "down", "down", "shops")
        for ((bi, bl) in blocks.withIndex()) {
            if (urban.any { it.block == bi && it.type != "infill" } && urban.first { it.block == bi }.let { u -> (u.x1 - u.x0) * (u.z1 - u.z0) > abs(area(bl)) * 0.7f }) continue
            if (TownPark.isPark(bi)) continue
            var x0 = Float.MAX_VALUE; var x1 = -Float.MAX_VALUE; var z0 = Float.MAX_VALUE; var z1 = -Float.MAX_VALUE
            var k = 0; while (k < bl.size) { x0 = min(x0, bl[k]); x1 = max(x1, bl[k]); z0 = min(z0, bl[k + 1]); z1 = max(z1, bl[k + 1]); k += 2 }
            val nx = ((x1 - x0) / C).toInt(); val nz = ((z1 - z0) / C).toInt()
            if (nx < 8 || nz < 8) continue
            val free = Array(nx) { BooleanArray(nz) }
            val home = floatArrayOf(City.lotX0 - 14f, City.lotZ0 - 14f, City.lotX1 + 14f, City.lotZ1 + 6f)
            for (i in 0 until nx) for (j in 0 until nz) {
                val cx = x0 + (i + 0.5f) * C; val cz = z0 + (j + 0.5f) * C
                if (!inside(bl, cx, cz) || clearance(cx, cz) < C * 0.75f) continue
                if (cx > home[0] && cx < home[2] && cz > home[1] && cz < home[3]) continue
                val cell = floatArrayOf(cx - C / 2, cz - C / 2, cx + C / 2, cz - C / 2, cx + C / 2, cz + C / 2, cx - C / 2, cz + C / 2)
                var hit = false
                for (lp in lotPolys) { if (abs(lp[0] - cx) > 200f) continue; if (TownHouses.overlap(cell, lp)) { hit = true; break } }
                if (!hit) for (u in urban) if (u.block == bi && cx > u.x0 - 2f && cx < u.x1 + 2f && cz > u.z0 - 2f && cz < u.z1 + 2f) { hit = true; break }
                free[i][j] = !hit
            }
            val d = TownPlan.districtAt((x0 + x1) / 2, (z0 + z1) / 2)
            var guard = 0
            // bairros de casas e o nobre: só coisas pequenas e no estilo do bairro (sem prédios grandes no meio das casas)
            var small = d == TownPlan.SUB || d == TownPlan.MAN || d == TownPlan.HOME || d == TownPlan.PARK
            while (guard++ < 80) {
                // maior retângulo livre (histograma): primeiro conjuntos grandes (40 a 92 m), depois construções pequenas (12 a 36 m)
                val hgt = IntArray(nz); var best = 0; var bi0 = 0; var bj0 = 0; var bw = 0; var bh = 0
                val maxC = ((if (small) 36f else 92f) / C).toInt(); val minC = ((if (small) 12f else 40f) / C).toInt()
                for (i in 0 until nx) {
                    for (j in 0 until nz) hgt[j] = if (free[i][j]) hgt[j] + 1 else 0
                    for (j in 0 until nz) {
                        var mh = Int.MAX_VALUE
                        for (j2 in j until min(nz, j + maxC)) {
                            mh = min(mh, min(hgt[j2], maxC)); if (mh < minC) break
                            val w = j2 - j + 1
                            if (w >= minC && mh * w > best) { best = mh * w; bi0 = i - mh + 1; bj0 = j; bw = mh; bh = w }
                        }
                    }
                }
                if (best == 0) { if (!small) { small = true; continue } else break }
                val rx0 = x0 + bi0 * C + 1f; val rz0 = z0 + bj0 * C + 1f; val rx1 = x0 + (bi0 + bw) * C - 1f; val rz1 = z0 + (bj0 + bh) * C - 1f
                // Etapa 146: nada de conjunto repetido (prédio de apartamento igual, igreja...): sobra grande vira quarteirão de prédios variados
                val t = if (small) "small" else "perim"
                if (false) { nDown++; nCom++; nRes++; downT.size; comT.size; resT.size }
                urban.add(Urban(bi, rx0, rz0, rx1, rz1, t, (bi + guard) % 7, 1 + (bi * 3 + guard) % 5, true))
                for (i in max(0, bi0 - 1) until min(nx, bi0 + bw + 1)) for (j in max(0, bj0 - 1) until min(nz, bj0 + bh + 1)) free[i][j] = false
            }
        }
    }

    class Urban(val block: Int, val x0: Float, val z0: Float, val x1: Float, val z1: Float, var type: String, val i: Int, val j: Int, val infill: Boolean = false)
    val urban = ArrayList<Urban>()

    private fun classify() {
        urban.clear()
        val down = arrayOf("down", "hotel", "down", "mall", "down", "apt", "hotel", "down", "hospital", "down", "police", "down", "hotel", "praca", "down", "apt")
        val com = arrayOf("shops", "super", "shops", "gas", "school", "shops", "church", "apt", "shops", "super", "gas", "shops", "apt", "shops", "church", "school")
        var nd = 0; var nc = 0; var nu = 0
        // marcos sem profissão (os lugares de trabalho são únicos e entram depois)
        val landD = arrayOf("mall", "hotel")
        val landC = arrayOf("church")
        val landU = arrayOf<String>()   // Etapa 146: uma igreja só (no comércio)
        for ((bi, bl) in blocks.withIndex()) {
            var x0 = Float.MAX_VALUE; var x1 = -Float.MAX_VALUE; var z0 = Float.MAX_VALUE; var z1 = -Float.MAX_VALUE
            var k = 0; while (k < bl.size) { x0 = min(x0, bl[k]); x1 = max(x1, bl[k]); z0 = min(z0, bl[k + 1]); z1 = max(z1, bl[k + 1]); k += 2 }
            val d = TownPlan.districtAt((x0 + x1) / 2, (z0 + z1) / 2)
            if (d != TownPlan.DOWN && d != TownPlan.COM && d != TownPlan.URB) continue
            val fill = abs(area(bl)) / ((x1 - x0) * (z1 - z0))
            if (fill < 0.94f || x1 - x0 < 30f || z1 - z0 < 30f) continue
            // encolhe cada lado até o retângulo inteiro ficar longe das calçadas
            var m0 = 1.3f; var m1 = 1.3f; var m2 = 1.3f; var m3 = 1.3f
            repeat(30) {
                fun ok(x: Float, z: Float) = clearance(x, z) >= 0.15f
                var moved = false
                val ax = x0 + m0; val bx = x1 - m1; val az = z0 + m2; val bz = z1 - m3
                var q = 0; while (q <= 10) { val x = ax + (bx - ax) * q / 10; if (!ok(x, az)) { m2 += 0.5f; moved = true; break }; q++ }
                q = 0; while (q <= 10) { val x = ax + (bx - ax) * q / 10; if (!ok(x, bz)) { m3 += 0.5f; moved = true; break }; q++ }
                q = 0; while (q <= 10) { val z = az + (bz - az) * q / 10; if (!ok(ax, z)) { m0 += 0.5f; moved = true; break }; q++ }
                q = 0; while (q <= 10) { val z = az + (bz - az) * q / 10; if (!ok(bx, z)) { m1 += 0.5f; moved = true; break }; q++ }
                if (!moved) return@repeat
            }
            // poucos marcos únicos (com interior) e o resto em quarteirões de prédios colados, todos diferentes
            val t = when (d) {
                TownPlan.DOWN -> if (nd < landD.size) landD[nd++] else "perim"
                TownPlan.COM -> if (nc < landC.size) landC[nc++] else "perim"
                else -> if (nu < landU.size && (bi % 5 == 2)) landU[nu++] else "perim"
            }
            if (x1 - m1 - x0 - m0 < 30f || z1 - m3 - z0 - m2 < 30f) continue
            urban.add(Urban(bi, x0 + m0, z0 + m2, x1 - m1, z1 - m3, t, bi % 7, 1 + bi % 5))
        }
        // Etapa 141: um lugar de trabalho único por profissão (níveis 3 e 4 no centro, os outros no comércio e nos bairros urbanos)
        val cxC = TownPlan.XS[2]; val czC = (TownPlan.ZS[1] + TownPlan.ZS[2]) / 2
        for (job in Jobs.ALL) {
            val want = if (job.level >= 3) intArrayOf(TownPlan.DOWN) else intArrayOf(TownPlan.COM, TownPlan.URB)
            val need = when (job.id) { "medico" -> 56f; "prefeito" -> 50f; "professor", "repositor" -> 50f; "juiz" -> 44f; else -> 34f }
            // Etapa 146: só quadras com a frente (lado z) colada numa calçada — a porta tem que dar para a rua
            fun frontOk(u: Urban) = min(clearance((u.x0 + u.x1) / 2, u.z1 + 2.5f), clearance((u.x0 + u.x1) / 2, u.z0 - 2.5f)) < 0.2f
            val cand = urban.filter { it.type == "perim" && TownPlan.districtAt((it.x0 + it.x1) / 2, (it.z0 + it.z1) / 2) in want && it.x1 - it.x0 >= need && it.z1 - it.z0 >= 34f && frontOk(it) && urban.none { o -> o.type.startsWith("job:") && kotlin.math.hypot((o.x0 + o.x1) / 2 - (it.x0 + it.x1) / 2, (o.z0 + o.z1) / 2 - (it.z0 + it.z1) / 2) < 70f } }
                .sortedBy { kotlin.math.hypot((it.x0 + it.x1) / 2 - cxC, (it.z0 + it.z1) / 2 - czC) * (if (job.level >= 3) 1f else -0.3f) + (it.block * 37 % 100) }
            val pick = cand.firstOrNull() ?: urban.firstOrNull { it.type == "perim" && it.x1 - it.x0 >= need && frontOk(it) } ?: urban.firstOrNull { it.type == "perim" && it.x1 - it.x0 >= need } ?: continue
            // Etapa 146: o emprego fica só com o pedaço que precisa; o resto do quarteirão continua com prédios colados
            val jw = max(need, TownJobs.size(job.id).first + 14f)
            if (pick.x1 - pick.x0 - jw >= 36f) {
                val west = (pick.block * 7 + job.level) % 2 == 0
                urban.remove(pick)
                if (west) { urban.add(Urban(pick.block, pick.x0, pick.z0, pick.x0 + jw, pick.z1, "job:" + job.id, pick.i, pick.j)); urban.add(Urban(pick.block, pick.x0 + jw + 1f, pick.z0, pick.x1, pick.z1, "perim", pick.i, pick.j)) }
                else { urban.add(Urban(pick.block, pick.x1 - jw, pick.z0, pick.x1, pick.z1, "job:" + job.id, pick.i, pick.j)); urban.add(Urban(pick.block, pick.x0, pick.z0, pick.x1 - jw - 1f, pick.z1, "perim", pick.i, pick.j)) }
            } else pick.type = "job:" + job.id
            // e no fundo: se o quarteirão for fundo, o emprego fica com a frente e o fundo volta a ter prédios
            val ju = urban.last { it.type == "job:" + job.id }
            val jd = TownJobs.size(job.id).second + 20f
            if (ju.z1 - ju.z0 - jd >= 32f) {
                val frontZ1 = clearance((ju.x0 + ju.x1) / 2, ju.z1 + 2.5f) < clearance((ju.x0 + ju.x1) / 2, ju.z0 - 2.5f)
                urban.remove(ju)
                if (frontZ1) { urban.add(Urban(ju.block, ju.x0, ju.z1 - jd, ju.x1, ju.z1, ju.type, ju.i, ju.j)); urban.add(Urban(ju.block, ju.x0, ju.z0, ju.x1, ju.z1 - jd - 1f, "perim", ju.i, ju.j)) }
                else { urban.add(Urban(ju.block, ju.x0, ju.z0, ju.x1, ju.z0 + jd, ju.type, ju.i, ju.j)); urban.add(Urban(ju.block, ju.x0, ju.z0 + jd + 1f, ju.x1, ju.z1, "perim", ju.i, ju.j)) }
            }
        }
    }
    var outline = FloatArray(0)
    /** quantas esquinas ficaram apertadas demais (ruas chegando quase juntas) — deve ser 0 */
    var warn = 0

    /** Tira pontos repetidos ou quase colineares. */
    private fun clean(p: FloatArray): FloatArray {
        val o = ArrayList<Float>(); val n = p.size / 2
        for (i in 0 until n) {
            val x = p[i * 2]; val z = p[i * 2 + 1]
            if (o.size >= 2 && hypot(o[o.size - 2] - x, o[o.size - 1] - z) < 0.3f) continue
            o.add(x); o.add(z)
        }
        if (o.size >= 4 && hypot(o[0] - o[o.size - 2], o[1] - o[o.size - 1]) < 0.3f) { o.removeAt(o.size - 1); o.removeAt(o.size - 1) }
        return unloop(o.toFloatArray())
    }

    /** Tira laços pequenos (onde a calçada da rua encontra a da esquina e as linhas se cruzam). */
    private fun unloop(p0: FloatArray): FloatArray {
        var p = p0
        var guard = 0
        outer@ while (guard++ < 60) {
            val n = p.size / 2
            for (i in 0 until n) {
                val i2 = (i + 1) % n
                for (j in i + 2 until n) {
                    val j2 = (j + 1) % n
                    if (j2 == i) continue
                    val q = segPt(p[i * 2], p[i * 2 + 1], p[i2 * 2], p[i2 * 2 + 1], p[j * 2], p[j * 2 + 1], p[j2 * 2], p[j2 * 2 + 1]) ?: continue
                    // tira o lado menor do laço (i2..j ou j2..i) e põe o ponto de cruzamento
                    val o = ArrayList<Float>()
                    if (j - i <= n - (j - i)) { var k = j2; while (true) { o.add(p[k * 2]); o.add(p[k * 2 + 1]); if (k == i) break; k = (k + 1) % n } }
                    else { var k = i2; while (true) { o.add(p[k * 2]); o.add(p[k * 2 + 1]); if (k == j) break; k = (k + 1) % n } }
                    o.add(q[0]); o.add(q[1])
                    p = o.toFloatArray()
                    continue@outer
                }
            }
            break
        }
        return p
    }

    private fun segPt(ax: Float, az: Float, bx: Float, bz: Float, cx: Float, cz: Float, dx: Float, dz: Float): FloatArray? {
        val rx = bx - ax; val rz = bz - az; val sx = dx - cx; val sz = dz - cz
        val den = rx * sz - rz * sx
        if (abs(den) < 1e-6f) return null
        val t = ((cx - ax) * sz - (cz - az) * sx) / den; val u = ((cx - ax) * rz - (cz - az) * rx) / den
        if (t <= 0f || t >= 1f || u <= 0f || u >= 1f) return null
        return floatArrayOf(ax + rx * t, az + rz * t)
    }

    fun inside(p: FloatArray, x: Float, z: Float): Boolean {
        var c = false; val n = p.size / 2; var j = n - 1
        for (i in 0 until n) {
            val xi = p[i * 2]; val zi = p[i * 2 + 1]; val xj = p[j * 2]; val zj = p[j * 2 + 1]
            if ((zi > z) != (zj > z) && x < (xj - xi) * (z - zi) / (zj - zi) + xi) c = !c
            j = i
        }
        return c
    }

    // ------------------------------------------------------------ triangulação (orelhas), com buracos por ponte

    fun triangulate(outer0: FloatArray, holes: List<FloatArray> = emptyList()): FloatArray {
        var poly = if (area(outer0) < 0) rev(outer0) else outer0
        for (h0 in holes.sortedByDescending { hh -> (0 until hh.size / 2).maxOf { hh[it * 2] } }) {
            val h = if (area(h0) > 0) rev(h0) else h0
            poly = bridge(poly, h)
        }
        val n = poly.size / 2
        val idx = ArrayList<Int>((0 until n).toList())
        val out = ArrayList<Float>()
        var guard = 0
        while (idx.size > 3 && guard++ < n * n) {
            var cut = false
            for (k in idx.indices) {
                val i0 = idx[(k + idx.size - 1) % idx.size]; val i1 = idx[k]; val i2 = idx[(k + 1) % idx.size]
                val ax = poly[i0 * 2]; val az = poly[i0 * 2 + 1]; val bx = poly[i1 * 2]; val bz = poly[i1 * 2 + 1]; val cx = poly[i2 * 2]; val cz = poly[i2 * 2 + 1]
                val cr = (bx - ax) * (cz - az) - (bz - az) * (cx - ax)
                if (cr <= 1e-6f) continue
                var ok = true
                for (m in idx) {
                    if (m == i0 || m == i1 || m == i2) continue
                    val px = poly[m * 2]; val pz = poly[m * 2 + 1]
                    if ((px == ax && pz == az) || (px == bx && pz == bz) || (px == cx && pz == cz)) continue
                    if (inTri(px, pz, ax, az, bx, bz, cx, cz)) { ok = false; break }
                }
                if (!ok) continue
                out.add(ax); out.add(az); out.add(bx); out.add(bz); out.add(cx); out.add(cz)
                idx.removeAt(k); cut = true; break
            }
            if (!cut) {   // polígono ruim: fecha em leque (melhor um triângulo torto que um buraco)
                val i0 = idx[0]
                for (k in 1 until idx.size - 1) { val a = idx[k]; val b = idx[k + 1]; out.add(poly[i0 * 2]); out.add(poly[i0 * 2 + 1]); out.add(poly[a * 2]); out.add(poly[a * 2 + 1]); out.add(poly[b * 2]); out.add(poly[b * 2 + 1]) }
                idx.clear(); break
            }
        }
        if (idx.size == 3) for (i in idx) { out.add(poly[i * 2]); out.add(poly[i * 2 + 1]) }
        return out.toFloatArray()
    }

    private fun inTri(px: Float, pz: Float, ax: Float, az: Float, bx: Float, bz: Float, cx: Float, cz: Float): Boolean {
        val d1 = (px - bx) * (az - bz) - (ax - bx) * (pz - bz)
        val d2 = (px - cx) * (bz - cz) - (bx - cx) * (pz - cz)
        val d3 = (px - ax) * (cz - az) - (cx - ax) * (pz - az)
        val neg = d1 < 0 || d2 < 0 || d3 < 0; val pos = d1 > 0 || d2 > 0 || d3 > 0
        return !(neg && pos)
    }

    private fun rev(p: FloatArray): FloatArray { val n = p.size / 2; return FloatArray(p.size) { val i = n - 1 - it / 2; p[i * 2 + it % 2] } }

    /** Liga o buraco [h] (horário) ao contorno [p] (anti-horário) pelo ponto mais à direita do buraco. */
    private fun bridge(p: FloatArray, h: FloatArray): FloatArray {
        val hn = h.size / 2; var hi = 0
        for (i in 0 until hn) if (h[i * 2] > h[hi * 2]) hi = i
        val hx = h[hi * 2]; val hz = h[hi * 2 + 1]
        val n = p.size / 2
        // ponto visível do contorno: o mais perto à direita que não cruza nada
        var best = -1; var bd = Float.MAX_VALUE
        for (i in 0 until n) {
            val x = p[i * 2]; val z = p[i * 2 + 1]
            if (x < hx) continue
            val d = hypot(x - hx, z - hz)
            if (d >= bd) continue
            if (crossesAny(p, hx, hz, x, z, i) || crossesAny(h, hx, hz, x, z, hi)) continue
            bd = d; best = i
        }
        if (best < 0) return p
        val o = ArrayList<Float>()
        for (i in 0..best) { o.add(p[i * 2]); o.add(p[i * 2 + 1]) }
        for (k in 0..hn) { val i = (hi + k) % hn; o.add(h[i * 2]); o.add(h[i * 2 + 1]) }
        for (i in best until n) { o.add(p[i * 2]); o.add(p[i * 2 + 1]) }
        return o.toFloatArray()
    }

    private fun crossesAny(p: FloatArray, ax: Float, az: Float, bx: Float, bz: Float, skip: Int): Boolean {
        val n = p.size / 2
        for (i in 0 until n) {
            val j = (i + 1) % n
            if (i == skip || j == skip) continue
            if (segX(ax, az, bx, bz, p[i * 2], p[i * 2 + 1], p[j * 2], p[j * 2 + 1])) return true
        }
        return false
    }

    private fun segX(ax: Float, az: Float, bx: Float, bz: Float, cx: Float, cz: Float, dx: Float, dz: Float): Boolean {
        fun o(px: Float, pz: Float, qx: Float, qz: Float, rx: Float, rz: Float) = (qx - px) * (rz - pz) - (qz - pz) * (rx - px)
        val o1 = o(ax, az, bx, bz, cx, cz); val o2 = o(ax, az, bx, bz, dx, dz); val o3 = o(cx, cz, dx, dz, ax, az); val o4 = o(cx, cz, dx, dz, bx, bz)
        return (o1 > 0) != (o2 > 0) && (o3 > 0) != (o4 > 0)
    }

    // ------------------------------------------------------------ consultas (chão, rua, calçada)

    private val segBy = HashMap<Int, ArrayList<Int>>()   // célula -> (rua << 12 | segmento)
    private val nodeBy = HashMap<Int, ArrayList<Int>>()
    private fun cell(x: Float, z: Float) = (Math.floor(x / 16.0).toInt() + 2000) * 8192 + (Math.floor(z / 16.0).toInt() + 2000)

    private fun index() {
        segBy.clear(); nodeBy.clear()
        for ((ei, ed) in edges.withIndex()) {
            val p = ed.pts; val reach = ed.w / 2 + SW + 1f
            for (i in 0 until p.size / 2 - 1) {
                val x0 = min(p[i * 2], p[i * 2 + 2]) - reach; val x1 = max(p[i * 2], p[i * 2 + 2]) + reach
                val z0 = min(p[i * 2 + 1], p[i * 2 + 3]) - reach; val z1 = max(p[i * 2 + 1], p[i * 2 + 3]) + reach
                for (cx in Math.floor(x0 / 16.0).toInt()..Math.floor(x1 / 16.0).toInt()) for (cz in Math.floor(z0 / 16.0).toInt()..Math.floor(z1 / 16.0).toInt())
                    segBy.getOrPut((cx + 2000) * 8192 + (cz + 2000)) { ArrayList() }.add(ei shl 12 or i)
            }
        }
        for ((ni, nd) in nodes.withIndex()) {
            val r = nd.r + SW + 12f
            for (cx in Math.floor((nd.x - r) / 16.0).toInt()..Math.floor((nd.x + r) / 16.0).toInt()) for (cz in Math.floor((nd.z - r) / 16.0).toInt()..Math.floor((nd.z + r) / 16.0).toInt())
                nodeBy.getOrPut((cx + 2000) * 8192 + (cz + 2000)) { ArrayList() }.add(ni)
        }
    }

    /** 0 = asfalto, 1 = calçada/quarteirão, 2 = canteiro de avenida, 3 = ilha da rotatória. */
    fun surface(x: Float, z: Float): Int {
        val c = cell(x, z)
        nodeBy[c]?.let { l ->
            for (ni in l) {
                val nd = nodes[ni]
                if (nd.round > 0f && hypot(x - nd.x, z - nd.z) < nd.round - 8f) return 3
                if (inside(nd.poly, x, z)) return 0
            }
        }
        segBy[c]?.let { l ->
            for (k in l) {
                val ed = edges[k shr 12]; val i = k and 4095; val p = ed.pts
                val ax = p[i * 2]; val az = p[i * 2 + 1]; val bx = p[i * 2 + 2]; val bz = p[i * 2 + 3]
                val dx = bx - ax; val dz = bz - az; val l2 = dx * dx + dz * dz
                val t = (((x - ax) * dx + (z - az) * dz) / l2)
                if (t < -0.02f || t > 1.02f) continue
                val qx = ax + dx * t; val qz = az + dz * t
                val d = hypot(x - qx, z - qz)
                if (d < ed.w / 2) return if (ed.avenue && d < 1.5f && ed.len > 8f) 2 else 0
            }
        }
        return 1
    }

    /** Folga até a calçada mais perto (negativo = em cima de rua, calçada ou cruzamento). */
    fun clearance(x: Float, z: Float): Float {
        var best = 99f
        val gx = Math.floor(x / 16.0).toInt(); val gz = Math.floor(z / 16.0).toInt()
        for (cx in gx - 1..gx + 1) for (cz in gz - 1..gz + 1) {
            val c = (cx + 2000) * 8192 + (cz + 2000)
            nodeBy[c]?.let { l -> for (ni in l) {
                val nd = nodes[ni]
                if (inside(nd.poly, x, z)) return -1f
                val d = if (hypot(x - nd.x, z - nd.z) > polyRadius(nd) + SW + 2f) 99f else distPoly(nd.poly, x, z) - SW
                if (d < best) best = d
            } }
            segBy[c]?.let { l -> for (k in l) {
                val ed = edges[k shr 12]; val i = k and 4095; val p = ed.pts
                val ax = p[i * 2]; val az = p[i * 2 + 1]; val bx = p[i * 2 + 2]; val bz = p[i * 2 + 3]
                val dx = bx - ax; val dz = bz - az; val l2 = max(1e-6f, dx * dx + dz * dz)
                val t = (((x - ax) * dx + (z - az) * dz) / l2).coerceIn(0f, 1f)
                val d = hypot(x - ax - dx * t, z - az - dz * t) - ed.w / 2 - SW
                if (d < best) best = d
            } }
        }
        return best
    }

    /** raio até o ponto mais longe do contorno do cruzamento (as esquinas com calçada ficam dentro de raio + SW) */
    private fun polyRadius(nd: Node): Float { var m = 0f; var k = 0; while (k < nd.poly.size) { m = max(m, hypot(nd.poly[k] - nd.x, nd.poly[k + 1] - nd.z)); k += 2 }; return m }

    private fun distPoly(p: FloatArray, x: Float, z: Float): Float {
        var m = Float.MAX_VALUE; val n = p.size / 2
        for (i in 0 until n) {
            val j = (i + 1) % n
            val ax = p[i * 2]; val az = p[i * 2 + 1]; val dx = p[j * 2] - ax; val dz = p[j * 2 + 1] - az; val l2 = max(1e-6f, dx * dx + dz * dz)
            val t = (((x - ax) * dx + (z - az) * dz) / l2).coerceIn(0f, 1f)
            m = min(m, hypot(x - ax - dx * t, z - az - dz * t))
        }
        return m
    }

    fun inAnyBlock(x: Float, z: Float): Boolean { for (b in blocks) if (inside(b, x, z)) return true; return false }

    /**
     * Etapa 146: morros em volta da cidade (a cidade fica num vale aberto para o mar). Zero dentro do retângulo da cidade
     * e na praia; sobe aos poucos até 30-90 m a uns 300 m da borda.
     */
    fun hill(x: Float, z: Float): Float {
        if (outline.isEmpty()) return 0f
        val dx = max(0f, max(minX - x, x - maxX)); val dz = max(0f, minZ - z)
        val d = hypot(dx, dz) - 35f
        if (d <= 0f) return 0f
        val t = min(1f, d / 300f); val s = t * t * (3 - 2 * t)
        val n = 0.62f + 0.22f * kotlin.math.sin(x * 0.011f + 1.3f) * kotlin.math.cos(z * 0.009f - 0.4f) + 0.16f * kotlin.math.sin((x + z) * 0.023f) + 0.08f * kotlin.math.sin(x * 0.047f - z * 0.031f)
        val beachZ = TownPlan.ZS[TownPlan.N]
        val fade = ((beachZ - 20f - z) / 160f).coerceIn(0f, 1f)
        return s * 95f * n * fade
    }

    /**
     * Etapa 147: relevo dentro da cidade — cada bairro de casas é um morro (ou um vale), com o topo no meio e plano nas
     * bordas (as avenidas, o centro, o comércio, o parque e o bairro da casa ficam planos). Inclinação máxima ~6%.
     */
    fun terrain(x: Float, z: Float): Float {
        if (outline.isEmpty()) return 0f
        val X = TownPlan.XS; val Z = TownPlan.ZS; val N = TownPlan.N
        if (x <= X[0] || x >= X[N] || z <= Z[0] || z >= Z[N]) return 0f
        var c = 0; while (c < N - 1 && x > X[c + 1]) c++
        var r = 0; while (r < N - 1 && z > Z[r + 1]) r++
        val a = TownPlan.RELIEF[r][c]; if (a == 0f) return 0f
        val u = (x - X[c]) / (X[c + 1] - X[c]); val v = (z - Z[r]) / (Z[r + 1] - Z[r])
        val su = kotlin.math.sin(Math.PI.toFloat() * u); val sv = kotlin.math.sin(Math.PI.toFloat() * v)
        return a * su * su * sv * sv
    }

    fun groundFlat(x: Float, z: Float): Float = groundH(x, z) - terrain(x, z)

    fun groundH(x: Float, z: Float): Float = if (outline.isNotEmpty() && !inside(outline, x, z)) hill(x, z) else terrain(x, z) + when (surface(x, z)) { 0 -> 0f; 2 -> CURB + 0.04f; 3 -> CURB + 0.05f; else -> CURB }

    /** Fora do mapa (além do contorno da cidade + calçada externa). */
    fun outside(x: Float, z: Float) = outline.isNotEmpty() && x > minX - 60f && x < maxX + 60f && z > minZ - 60f && z < maxZ + 60f && false

    // ------------------------------------------------------------ montagem

    fun build(out: ArrayList<City.Chunk>) {
        warn = 0
        TownPlan.generate()
        buildNodes()
        buildBlocks()
        index()
        classify()
        TownHouses.plan()
        infill()
        minX = nodes.minOf { it.x } - 30f; maxX = nodes.maxOf { it.x } + 30f
        minZ = nodes.minOf { it.z } - 30f; maxZ = nodes.maxOf { it.z } + 30f
        TownGeo.build(out)
        on = true
    }

    fun clear() { on = false; nodes.clear(); edges.clear(); blocks.clear(); segBy.clear(); nodeBy.clear(); outline = FloatArray(0) }

    // ------------------------------------------------------------ utilidades para quem desenha

    fun tangent(p: FloatArray, i: Int) = tan(p, i)
    fun offset(p: FloatArray, d: Float) = offsetEdge(p, d)
    fun outward(c: FloatArray, d: Float) = offsetOut(c, d)
    fun endPoint(ei: Int, ni: Int) = endOf(ei, ni)
    fun polyArea(p: FloatArray) = area(p)

    /** Contorno deslocado para fora (d > 0) ou para dentro (d < 0), qualquer sentido. */
    fun polyOffset(p: FloatArray, d: Float): FloatArray {
        val n = p.size / 2; val sg = if (area(p) > 0) 1f else -1f; val o = FloatArray(p.size)
        for (i in 0 until n) {
            val a = (i + n - 1) % n; val c = (i + 1) % n
            var tx = p[c * 2] - p[a * 2]; var tz = p[c * 2 + 1] - p[a * 2 + 1]; val l = max(1e-5f, hypot(tx, tz)); tx /= l; tz /= l
            o[i * 2] = p[i * 2] + tz * d * sg; o[i * 2 + 1] = p[i * 2 + 1] - tx * d * sg
        }
        return o
    }

    // ------------------------------------------------------------ trânsito: faixas e conversões

    /** Mão direita de quem anda no sentido da linha (no mundo do jogo, x para a direita e z para baixo no mapa). */
    fun lanePath(ei: Int, fwd: Boolean, off: Float): FloatArray {
        val ed = edges[ei]
        val p = if (fwd) ed.pts else rev(ed.pts)
        return offsetEdge(p, off)
    }

    /** Trajeto dentro do cruzamento [ni], do fim da faixa [a] ao começo da faixa [b]. */
    fun turnPath(ni: Int, a: FloatArray, b: FloatArray): FloatArray {
        val nd = nodes[ni]
        val n = a.size / 2
        val ax = a[(n - 1) * 2]; val az = a[(n - 1) * 2 + 1]
        val ta = tan(a, n - 1); val tb = tan(b, 0)
        val bx = b[0]; val bz = b[1]
        if (nd.round > 0f || nd.edges.size == 1) {
            val rc = if (nd.round > 0f) nd.round - 8f + 4.6f else max(3f, hypot(ax - nd.x, az - nd.z) * 0.8f)
            var a0 = atan2(az - nd.z, ax - nd.x); var a1 = atan2(bz - nd.z, bx - nd.x)
            // sentido anti-horário visto de cima (ângulo diminuindo)
            while (a1 >= a0 - 0.35f) a1 -= 2 * PI.toFloat()
            val o = ArrayList<Float>(); o.add(ax); o.add(az)
            val m = max(4, ((a0 - a1) * rc / 2.5f).toInt())
            for (i in 0..m) {
                val t = i / m.toFloat(); val ang = a0 - 0.18f + (a1 + 0.18f - (a0 - 0.18f)) * t
                val r = rc + (if (t < 0.2f) (1 - t / 0.2f) * 1.5f else if (t > 0.8f) (t - 0.8f) / 0.2f * 1.5f else 0f)
                o.add(nd.x + cos(ang) * r); o.add(nd.z + sin(ang) * r)
            }
            o.add(bx); o.add(bz)
            return o.toFloatArray()
        }
        val c = cross(floatArrayOf(ax, az), ta, floatArrayOf(bx, bz), floatArrayOf(-tb[0], -tb[1]))
        val ctl = if (c != null && c[2] > 0.5f && c[3] > 0.5f && c[2] < 40f && c[3] < 40f) floatArrayOf(c[0], c[1]) else floatArrayOf((ax + bx) / 2, (az + bz) / 2)
        return quadBez(floatArrayOf(ax, az), ctl, floatArrayOf(bx, bz), 10)
    }
}
