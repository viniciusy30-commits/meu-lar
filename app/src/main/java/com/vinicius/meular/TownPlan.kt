package com.vinicius.meular

import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min

/**
 * Etapa 131b: planta da cidade grande.
 *
 * Esqueleto de avenidas e ruas principais (malha 5 × 5 de superquadras de ~350 m, levemente torta e curva);
 * dentro de cada superquadra, o bairro desenha as próprias ruas:
 *  - CENTRO: malha de ruas retas (quadras de ~110 m), prédios altos;
 *  - COMÉRCIO: malha mais larga (quadras de ~170 m), lojas e estacionamentos;
 *  - SUBÚRBIO: rua em laço ou serpenteando, com ruas sem saída (cul-de-sac) — casas no padrão americano;
 *  - PARQUE: sem ruas internas;
 *  - CASA: o bairro da casa do jogador (rua reta na frente do terreno).
 */
object TownPlan {
    const val SUB = 0; const val DOWN = 1; const val COM = 2; const val PARK = 3; const val HOME = 4; const val MAN = 5

    val XS = floatArrayOf(-880f, -530f, -180f, 170f, 520f, 870f)
    val ZS = floatArrayOf(-850f, -500f, -150f, 200f, 550f, 900f)

    /** Bairro de cada superquadra [linha z][coluna x]. */
    val D = arrayOf(
        intArrayOf(MAN, SUB, MAN, PARK, MAN),
        intArrayOf(SUB, COM, DOWN, DOWN, SUB),
        intArrayOf(PARK, SUB, HOME, DOWN, COM),
        intArrayOf(SUB, COM, SUB, COM, SUB),
        intArrayOf(SUB, SUB, SUB, SUB, PARK))

    /** Distrito de cada quarteirão (pelo centro) — usado depois para escolher o que construir. */
    fun districtAt(x: Float, z: Float): Int {
        var c = 0; while (c < 4 && x > XS[c + 1]) c++
        var r = 0; while (r < 4 && z > ZS[r + 1]) r++
        return D[r][c]
    }

    /** Nível das casas de cada superquadra de subúrbio (1 pequena, 2 média, 3 grande). */
    val TIER = arrayOf(
        intArrayOf(4, 3, 4, 0, 4),
        intArrayOf(1, 0, 0, 0, 3),
        intArrayOf(0, 2, 2, 0, 0),
        intArrayOf(1, 0, 1, 0, 3),
        intArrayOf(1, 2, 1, 2, 0))
    fun tierAt(x: Float, z: Float): Int {
        var c = 0; while (c < 4 && x > XS[c + 1]) c++
        var r = 0; while (r < 4 && z > ZS[r + 1]) r++
        return TIER[r][c].coerceIn(1, 3)
    }

    private val STREETS = arrayOf("R. dos Ipês", "R. das Flores", "R. Aurora", "R. da Paz", "R. do Sol", "R. Primavera", "R. das Acácias", "R. Bela Vista",
        "R. do Mirante", "R. dos Andradas", "R. Leste", "R. das Gaivotas", "R. Esperança", "R. Jardim", "R. dos Coqueiros", "R. das Palmeiras",
        "R. Harmonia", "R. Girassol", "R. das Orquídeas", "R. Lua Nova", "R. do Bosque", "R. Serena", "R. dos Pinheiros", "R. Monte Claro",
        "R. Vale Verde", "R. Boa Vista", "R. das Hortênsias", "R. Sete de Setembro", "R. XV de Novembro", "R. Tiradentes", "R. do Comércio", "R. Direita")
    private val AVES = arrayOf("Av. Atlântica", "Av. Brasil", "Av. Paulista", "Av. Central", "Av. das Nações", "Av. Beira-Mar", "Av. Santos Dumont", "Av. Independência", "Av. Liberdade", "Av. Presidente Vargas", "Av. Rio Branco", "Av. Ipiranga")
    private val CULS = arrayOf("Vila das Rosas", "Vila Lírio", "Vila Jasmim", "Vila Magnólia", "Vila Violeta", "Vila Camélia", "Vila Azaleia", "Vila Tulipa", "Vila Begônia", "Vila Dália", "Vila Margarida", "Vila Gardênia")
    private var si = 0; private var ci = 0
    private fun street() = STREETS[(si++) % STREETS.size]
    private fun cul() = CULS[(ci++) % CULS.size]

    /** Curva original de um lado da superquadra (cópia, para achar pontos mesmo depois de a rua ser dividida). */
    private class Curve(val ax: Float, val az: Float, val c1x: Float, val c1z: Float, val c2x: Float, val c2z: Float, val bx: Float, val bz: Float) {
        fun at(t: Float): FloatArray { val u = 1 - t; return floatArrayOf(u * u * u * ax + 3 * u * u * t * c1x + 3 * u * t * t * c2x + t * t * t * bx, u * u * u * az + 3 * u * u * t * c1z + 3 * u * t * t * c2z + t * t * t * bz) }
        /** parâmetro em que a curva passa por z (ou x) — busca simples */
        fun tAtZ(z: Float): Float { var bt = 0.5f; var bd = Float.MAX_VALUE; for (k in 0..400) { val t = k / 400f; val d = abs(at(t)[1] - z); if (d < bd) { bd = d; bt = t } }; return bt }
    }
    private fun curveOf(ei: Int): Curve { val e = Town.edges[ei]; val a = Town.nodes[e.a]; val b = Town.nodes[e.b]; return Curve(a.x, a.z, e.c1x, e.c1z, e.c2x, e.c2z, b.x, b.z) }

    /** Centro e comércio ficam em malha reta (alinhada aos eixos): prédios e lojas com interior são montados em quadras retangulares. */
    private fun urbanSide(r: Int, c: Int) = r in 0..4 && c in 0..4 && (D[r][c] == DOWN || D[r][c] == COM)
    private fun urbanCorner(r: Int, c: Int) = urbanSide(r - 1, c - 1) || urbanSide(r - 1, c) || urbanSide(r, c - 1) || urbanSide(r, c)

    fun generate() {
        si = 0; ci = 0
        val rng = City.Rng(2026)
        val G = Array(6) { IntArray(6) }
        for (r in 0..5) for (c in 0..5) {
            val homeCorner = (r == 2 || r == 3) && (c == 2 || c == 3)
            val j = if (urbanCorner(r, c)) 0f else if (homeCorner) 8f else 45f
            val edge = r == 0 || r == 5 || c == 0 || c == 5
            G[r][c] = Town.n(XS[c] + rng.r(-j, j), ZS[r] + rng.r(-j, j), if (r == 3 && c == 3) 27f else if (r == 1 && c == 3) 24f else if (r == 3 && c == 1) 22f else 0f)
            if (edge) { /* borda: sem rotatória */ }
        }
        // avenidas: linha z 3 e coluna x 3 (as do lado de baixo e da direita do bairro da casa) e a linha 1
        val hName = Array(6) { if (it == 3) AVES[0] else if (it == 1) AVES[2] else if (it == 0 || it == 5) AVES[3 + it % 2] else street() }
        val vName = Array(6) { if (it == 3) AVES[1] else if (it == 1) AVES[6] else if (it == 0 || it == 5) AVES[7 + it % 2] else street() }
        val H = Array(6) { IntArray(5) }; val V = Array(5) { IntArray(6) }
        for (r in 0..5) for (c in 0..4) {
            val home = (r == 2 || r == 3) && c == 2
            val w = if (r == 3 || r == 1) 24f else 16f
            val bend = if (home) rng.r(-6f, 6f) else rng.r(-24f, 24f)
            H[r][c] = Town.e(G[r][c], G[r][c + 1], w, if (urbanSide(r - 1, c) || urbanSide(r, c)) 0f else bend, hName[r])
        }
        for (r in 0..4) for (c in 0..5) {
            val home = r == 2 && (c == 2 || c == 3)
            val w = if (c == 3 || c == 1) 24f else 16f
            val bend = if (home) rng.r(-6f, 6f) else rng.r(-24f, 24f)
            V[r][c] = Town.e(G[r][c], G[r + 1][c], w, if (urbanSide(r, c - 1) || urbanSide(r, c)) 0f else bend, vName[c])
        }
        // bairros (as curvas de cada lado guardadas antes de qualquer divisão)
        val HC = Array(6) { r -> Array(5) { c -> curveOf(H[r][c]) } }; val VC = Array(5) { r -> Array(6) { c -> curveOf(V[r][c]) } }
        for (r in 0..4) for (c in 0..4) {
            val N = HC[r][c]; val S = HC[r + 1][c]; val W = VC[r][c]; val E = VC[r][c + 1]
            val q = arrayOf(Town.nodes[G[r][c]], Town.nodes[G[r][c + 1]], Town.nodes[G[r + 1][c + 1]], Town.nodes[G[r + 1][c]])
            fun bil(u: Float, v: Float): FloatArray {
                val tx = q[0].x + (q[1].x - q[0].x) * u; val tz = q[0].z + (q[1].z - q[0].z) * u
                val bx = q[3].x + (q[2].x - q[3].x) * u; val bz = q[3].z + (q[2].z - q[3].z) * u
                return floatArrayOf(tx + (bx - tx) * v, tz + (bz - tz) * v)
            }
            val cr = City.Rng(r * 31 + c * 7 + 3)
            when (D[r][c]) {
                DOWN -> grid(N, S, W, E, 4, 16f, DOWN)
                COM -> grid(N, S, W, E, 3, 16f, COM)
                MAN -> {
                    // bairro nobre: poucas ruas, longas e curvas
                    val rot = cr.i(4)
                    val P: (Float, Float) -> FloatArray = { u0, v0 -> val (u, v) = when (rot) { 1 -> Pair(1 - v0, u0); 2 -> Pair(1 - u0, 1 - v0); 3 -> Pair(v0, 1 - u0); else -> Pair(u0, v0) }; bil(u, v) }
                    estateSub(P, cr)
                }
                SUB -> {
                    // padrão girado (0..3 × 90°) e espelhado ao acaso: cada bairro fica diferente
                    val rot = cr.i(4); val mir = cr.chance(0.5f)
                    val P: (Float, Float) -> FloatArray = { u0, v0 ->
                        val u1 = if (mir) 1 - u0 else u0
                        val (u, v) = when (rot) { 1 -> Pair(1 - v0, u1); 2 -> Pair(1 - u1, 1 - v0); 3 -> Pair(v0, 1 - u1); else -> Pair(u1, v0) }
                        bil(u, v)
                    }
                    when (cr.i(4)) { 0 -> loopSub(P, cr); 1 -> meanderSub(P, cr); 2 -> crescentSub(P, cr); else -> courtSub(P, cr) }
                }
                HOME -> homeSub(N, S, W, E)
                else -> {}
            }
        }
        // distrito de cada rua (pelo meio)
        for (ed in Town.edges) { val m = Town.at(ed, 0.5f); ed.kind = districtAt(m[0], m[1]) }
    }

    /** Liga dois pontos com uma rua, criando os nós nos lados da superquadra quando for o caso. */
    private fun nodeAt(p: FloatArray, onSide: Boolean): Int = if (onSide) Town.splitNear(p[0], p[1]) else Town.n(p[0], p[1])

    /** Malha reta: [k] quadras em cada direção. */
    private fun grid(N: Curve, S: Curve, W: Curve, E: Curve, k: Int, w: Float, kind: Int) {
        class Ln(val p: FloatArray, val q: FloatArray, val name: String) { val nodes = ArrayList<Pair<Float, Int>>() }
        val lines = ArrayList<Ln>()
        for (i in 1 until k) { val t = i / k.toFloat(); lines.add(Ln(N.at(t), S.at(t), street())) }
        val nV = lines.size
        for (i in 1 until k) { val t = i / k.toFloat(); lines.add(Ln(W.at(t), E.at(t), street())) }
        for (ln in lines) { ln.nodes.add(Pair(0f, nodeAt(ln.p, true))); ln.nodes.add(Pair(1f, nodeAt(ln.q, true))) }
        for (a in 0 until nV) for (b in nV until lines.size) {
            val A = lines[a]; val B = lines[b]
            val x = segX(A.p, A.q, B.p, B.q) ?: continue
            val ni = Town.n(x[0], x[1])
            A.nodes.add(Pair(x[2], ni)); B.nodes.add(Pair(x[3], ni))
        }
        for (ln in lines) {
            ln.nodes.sortBy { it.first }
            for (i in 0 until ln.nodes.size - 1) { val ei = Town.e(ln.nodes[i].second, ln.nodes[i + 1].second, w, 0f, ln.name); Town.edges[ei].kind = kind }
        }
    }

    private fun segX(a: FloatArray, b: FloatArray, c: FloatArray, d: FloatArray): FloatArray? {
        val rx = b[0] - a[0]; val rz = b[1] - a[1]; val sx = d[0] - c[0]; val sz = d[1] - c[1]
        val den = rx * sz - rz * sx
        if (abs(den) < 1e-6f) return null
        val t = ((c[0] - a[0]) * sz - (c[1] - a[1]) * sx) / den; val u = ((c[0] - a[0]) * rz - (c[1] - a[1]) * rx) / den
        if (t <= 0f || t >= 1f || u <= 0f || u >= 1f) return null
        return floatArrayOf(a[0] + rx * t, a[1] + rz * t, t, u)
    }

    // Padrões de subúrbio no "espaço do bairro": u da esquerda para a direita, v de cima (0) para baixo (1).
    // Pontos com v = 1 (ou 0, ou u = 0/1) caem nas ruas da borda e são ligados nelas. Tudo com folga de 20% das bordas.

    private fun side(P: (Float, Float) -> FloatArray, u: Float, v: Float): Int { val p = P(u, v); return Town.splitNear(p[0], p[1]) }
    private fun inner(P: (Float, Float) -> FloatArray, u: Float, v: Float): Int { val p = P(u, v); return Town.n(p[0], p[1]) }
    private fun j(r: City.Rng) = r.r(-0.035f, 0.035f)

    /** Laço: entra por baixo, dá a volta e sai por baixo; ruas sem saída para fora e para dentro. */
    private fun loopSub(P: (Float, Float) -> FloatArray, r: City.Rng) {
        val name = street()
        val s1 = side(P, 0.32f + j(r), 1f); val s2 = side(P, 0.68f + j(r), 1f)
        val i1 = inner(P, 0.28f + j(r), 0.45f + j(r)); val i2 = inner(P, 0.72f + j(r), 0.45f + j(r))
        Town.e(s1, i1, 12f, r.r(-10f, 10f), name)
        val top = Town.e(i1, i2, 12f, -r.r(14f, 26f), name)
        Town.e(i2, s2, 12f, r.r(-10f, 10f), name)
        val mid = Town.split(top, 0.5f)
        Town.e(mid, inner(P, 0.5f + j(r), 0.2f), 12f, r.r(-8f, 8f), cul())
        Town.e(i1, inner(P, 0.2f, 0.22f + j(r)), 12f, r.r(-8f, 8f), cul())
        Town.e(i2, inner(P, 0.8f, 0.22f + j(r)), 12f, r.r(-8f, 8f), cul())
        Town.e(mid, inner(P, 0.5f + j(r), 0.78f), 12f, r.r(-6f, 6f), cul())
        Town.e(side(P, 0f, 0.6f + j(r)), i1, 12f, r.r(-8f, 8f), street())
    }

    /** Rua que serpenteia de um lado ao outro, com ruas sem saída alternadas. */
    private fun meanderSub(P: (Float, Float) -> FloatArray, r: City.Rng) {
        val name = street()
        val a = side(P, 0f, 0.5f + j(r)); val b = side(P, 1f, 0.5f + j(r))
        val m1 = inner(P, 0.36f + j(r), 0.38f + j(r)); val m2 = inner(P, 0.64f + j(r), 0.62f + j(r))
        Town.e(a, m1, 12f, r.r(-14f, 14f), name); val mm = Town.e(m1, m2, 12f, r.r(-16f, 16f), name); Town.e(m2, b, 12f, r.r(-14f, 14f), name)
        Town.e(m1, inner(P, 0.36f + j(r), 0.2f), 12f, r.r(-8f, 8f), cul())
        Town.e(m2, inner(P, 0.64f + j(r), 0.8f), 12f, r.r(-8f, 8f), cul())
        Town.e(m1, inner(P, 0.22f, 0.8f), 12f, r.r(-8f, 8f), cul())
        Town.e(m2, inner(P, 0.78f, 0.2f), 12f, r.r(-8f, 8f), cul())
        val c = Town.split(mm, 0.5f)
        Town.e(c, side(P, 0.5f + j(r), 1f), 12f, r.r(-8f, 8f), street())
    }

    /** Duas ruas em arco atravessando o bairro, ligadas no meio. */
    private fun crescentSub(P: (Float, Float) -> FloatArray, r: City.Rng) {
        val n1 = street(); val n2 = street()
        val a1 = side(P, 0f, 0.33f + j(r)); val b1 = side(P, 1f, 0.33f + j(r))
        val a2 = side(P, 0f, 0.7f + j(r)); val b2 = side(P, 1f, 0.7f + j(r))
        val e1 = Town.e(a1, b1, 12f, r.r(14f, 24f), n1)
        val e2 = Town.e(a2, b2, 12f, -r.r(14f, 24f), n2)
        val m1 = Town.split(e1, 0.5f); val m2 = Town.split(e2, 0.5f)
        Town.e(m1, m2, 12f, r.r(-6f, 6f), street())
        val q1 = Town.split(Town.nodes[m1].edges[0], 0.5f); Town.e(q1, inner(P, 0.27f + j(r), 0.12f), 12f, 0f, cul())
        val q2 = Town.split(Town.nodes[m2].edges[1], 0.5f); Town.e(q2, inner(P, 0.73f + j(r), 0.9f), 12f, 0f, cul())
    }

    /** Rua de acesso com várias ruas sem saída em leque (condomínio aberto). */
    private fun courtSub(P: (Float, Float) -> FloatArray, r: City.Rng) {
        val name = street()
        val s1 = side(P, 0.5f + j(r), 1f)
        val hub = inner(P, 0.5f + j(r), 0.5f + j(r))
        Town.e(s1, hub, 12f, r.r(-10f, 10f), name)
        val hub2 = inner(P, 0.5f + j(r), 0.3f)
        Town.e(hub, hub2, 12f, r.r(-8f, 8f), name)
        Town.e(hub, inner(P, 0.2f, 0.62f + j(r)), 12f, r.r(-10f, 10f), cul())
        Town.e(hub, inner(P, 0.8f, 0.62f + j(r)), 12f, r.r(-10f, 10f), cul())
        Town.e(hub2, inner(P, 0.22f, 0.2f), 12f, r.r(-10f, 10f), cul())
        Town.e(hub2, inner(P, 0.78f, 0.2f), 12f, r.r(-10f, 10f), cul())
        Town.e(hub2, side(P, 0.5f + j(r), 0f), 12f, r.r(-8f, 8f), street())
    }

    /** Bairro nobre: uma alameda curva atravessando e duas ruas sem saída longas (terrenos enormes dos dois lados). */
    private fun estateSub(P: (Float, Float) -> FloatArray, r: City.Rng) {
        val name = "Al. " + arrayOf("dos Jacarandás", "das Sibipirunas", "Imperial", "dos Ipês Roxos", "do Lago Azul", "das Palmeiras Reais")[r.i(6)]
        val a = side(P, 0f, 0.5f + j(r)); val b = side(P, 1f, 0.5f + j(r))
        val e = Town.e(a, b, 12f, r.r(30f, 45f) * (if (r.chance(0.5f)) 1 else -1), name)
        val m = Town.split(e, 0.5f)
        Town.e(m, inner(P, 0.5f + j(r), 0.14f), 12f, r.r(-18f, 18f), cul())
        Town.e(m, inner(P, 0.5f + j(r), 0.86f), 12f, r.r(-18f, 18f), cul())
    }

    /** Bairro da casa: rua reta passando na frente do terreno (z ≈ 52), ruas sem saída para cima e um laço embaixo. */
    private fun homeSub(N: Curve, S: Curve, W: Curve, E: Curve) {
        val z = 52f; val name = "R. das Magnólias"
        val w = nodeAt(W.at(W.tAtZ(z)), true); val e = nodeAt(E.at(E.tAtZ(z)), true)
        val xs = floatArrayOf(-118f, -64f, 84f, 120f)
        val ids = IntArray(xs.size) { Town.n(xs[it], z) }
        var prev = w
        for (id in ids) { Town.e(prev, id, 14f, 0f, name); prev = id }
        Town.e(prev, e, 14f, 0f, name)
        Town.e(ids[0], Town.n(-122f, -78f), 12f, 6f, "Vila das Rosas")
        Town.e(ids[3], Town.n(122f, -82f), 12f, -6f, "Vila Lírio")
        val l1 = Town.n(-46f, 140f); val l2 = Town.n(66f, 140f)
        Town.e(ids[1], l1, 12f, 8f, "R. do Lago"); Town.e(l1, l2, 12f, 14f, "R. do Lago"); Town.e(l2, ids[2], 12f, 8f, "R. do Lago")
    }

    @Suppress("unused") private fun dist(a: FloatArray, b: FloatArray) = hypot(a[0] - b[0], a[1] - b[1])
    @Suppress("unused") private fun clamp(v: Float) = max(0f, min(1f, v))
}
