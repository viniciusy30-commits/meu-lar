package com.vinicius.meular

import kotlin.math.max
import kotlin.math.min

/**
 * Etapa 142: espaço interno dos locais de trabalho e a mobília detalhada usada neles.
 * u = x do mundo, v = profundidade a partir da fachada (para dentro).
 * Cada móvel recebe uma direção (dir): 0 = olha para a porta (-v), 1 = olha para o fundo (+v), 2 = -u, 3 = +u.
 * No referencial do móvel, lx é o lado e lz é "para frente" (para onde a pessoa que usa o móvel olha).
 */
class JobSpace(val g: CityGeo.Gen, val x0: Float, val x1: Float, val zf: Float, val fz: Float, val depth: Float, val h: Float, seed0: Int) {
    private val FL = City.FLOOR
    val b get() = g.A
    fun z(v: Float) = zf - fz * v
    val cx get() = (x0 + x1) / 2
    val w get() = x1 - x0
    val wallsV = ArrayList<Float>()
    val wallsU = ArrayList<Float>()
    private var sd = seed0 * 7919 + 13
    fun rn(): Float { sd = sd * 1103515245 + 12345; return ((sd ushr 9) and 0xFFFF) / 65536f }
    fun rr(a: Float, e: Float) = a + (e - a) * rn()
    fun pc(a: Array<String>): Int = C(a[(rn() * a.size).toInt().coerceIn(0, a.size - 1)])

    fun box(u: Float, y: Float, v: Float, su: Float, sy: Float, sv: Float, c: Int, mat: Int = Mt.PLAIN, sc: Float = 1f, lit: Boolean = true) { b.m(mat, sc); b.box(u, y + sy / 2, z(v), su, sy, sv, c, lit) }
    fun solid(u0: Float, v0: Float, u1: Float, v1: Float) { val a = z(v0); val c = z(v1); g.solid(min(u0, u1), min(a, c), max(u0, u1), max(a, c)) }

    // ---------------------------------------------------------------- referencial do móvel
    fun au(u: Float, v: Float, dir: Int, lx: Float, lz: Float) = when (dir) { 0 -> u + lx; 1 -> u - lx; 2 -> u - lz; else -> u + lz }
    fun av(u: Float, v: Float, dir: Int, lx: Float, lz: Float) = when (dir) { 0 -> v - lz; 1 -> v + lz; 2 -> v - lx; else -> v + lx }
    fun ob(u: Float, v: Float, dir: Int, lx: Float, y: Float, lz: Float, sx: Float, sy: Float, sz: Float, c: Int, mat: Int = Mt.PLAIN, sc: Float = 1f, lit: Boolean = true) {
        val a = dir < 2
        box(au(u, v, dir, lx, lz), y, av(u, v, dir, lx, lz), if (a) sx else sz, sy, if (a) sz else sx, c, mat, sc, lit)
    }
    fun oc(u: Float, v: Float, dir: Int, lx: Float, y: Float, lz: Float, r: Float, hh: Float, c: Int, mat: Int = Mt.METAL, seg: Int = 10, r2: Float = r, lit: Boolean = true) {
        b.m(mat, 1f); b.cyl(au(u, v, dir, lx, lz), y, z(av(u, v, dir, lx, lz)), r, r2, hh, c, lit, seg)
    }
    fun os(u: Float, v: Float, dir: Int, lx0: Float, lz0: Float, lx1: Float, lz1: Float) = solid(au(u, v, dir, lx0, lz0), av(u, v, dir, lx0, lz0), au(u, v, dir, lx1, lz1), av(u, v, dir, lx1, lz1))
    fun ball(u: Float, y: Float, v: Float, r: Float, c: Int, ry: Float = r) = CityGeo.ball(b, u, y, z(v), r, c, ry, 7)
    fun op(dir: Int) = dir xor 1

    // ---------------------------------------------------------------- paredes internas
    fun wallTo(v: Float, u0: Float, u1: Float, doorU: Float = Float.NaN, c: Int = C("#F2EEE6"), glass: Boolean = false) {
        wallsV.add(v)
        if (glass) {
            box((u0 + u1) / 2, FL, v, u1 - u0, 0.1f, 0.12f, C("#3B3F44"), Mt.METAL); box((u0 + u1) / 2, FL + 2.5f, v, u1 - u0, 0.1f, 0.12f, C("#3B3F44"), Mt.METAL)
            box((u0 + u1) / 2, FL + 2.6f, v, u1 - u0, h - 2.6f, 0.12f, c, Mt.PLASTER, 0.4f)
            var u = u0; while (u <= u1 + 0.01f) { if (doorU.isNaN() || u < doorU - 0.55f || u > doorU + 0.55f) box(u, FL, v, 0.06f, 2.6f, 0.08f, C("#3B3F44"), Mt.METAL); u += 1.2f }
            if (doorU.isNaN()) box((u0 + u1) / 2, FL + 0.1f, v, u1 - u0, 2.4f, 0.03f, C("#BFD8E2"), Mt.GLASS)
            else { box((u0 + doorU - 0.55f) / 2, FL + 0.1f, v, doorU - 0.55f - u0, 2.4f, 0.03f, C("#BFD8E2"), Mt.GLASS); box((doorU + 0.55f + u1) / 2, FL + 0.1f, v, u1 - doorU - 0.55f, 2.4f, 0.03f, C("#BFD8E2"), Mt.GLASS) }
        } else {
            val ops = if (doorU.isNaN()) emptyList() else listOf(CityGeo.Op(doorU, 1.0f, FL, FL + 2.2f, true))
            CityGeo.wall(g, 0, z(v), u0, u1, FL, FL + h, if (fz > 0) -1 else 1, ops, c, c, Mt.PLASTER, 0.12f, true)
            if (!doorU.isNaN()) { box(doorU - 0.53f, FL, v, 0.06f, 2.25f, 0.16f, C("#8D6E63"), Mt.WOOD, 0.5f); box(doorU + 0.53f, FL, v, 0.06f, 2.25f, 0.16f, C("#8D6E63"), Mt.WOOD, 0.5f); box(doorU, FL + 2.2f, v, 1.12f, 0.06f, 0.16f, C("#8D6E63"), Mt.WOOD, 0.5f) }
            for (sg in floatArrayOf(-1f, 1f)) { if (doorU.isNaN()) box((u0 + u1) / 2, FL, v + sg * 0.065f, u1 - u0, 0.1f, 0.012f, C("#9E9E9E")) else { box((u0 + doorU - 0.56f) / 2, FL, v + sg * 0.065f, doorU - 0.56f - u0, 0.1f, 0.012f, C("#9E9E9E")); box((doorU + 0.56f + u1) / 2, FL, v + sg * 0.065f, u1 - doorU - 0.56f, 0.1f, 0.012f, C("#9E9E9E")) } }
        }
        if (doorU.isNaN()) solid(u0, v - 0.08f, u1, v + 0.08f) else { solid(u0, v - 0.08f, doorU - 0.55f, v + 0.08f); solid(doorU + 0.55f, v - 0.08f, u1, v + 0.08f) }
    }
    fun wallAlong(u: Float, v0: Float, v1: Float, doorV: Float = Float.NaN, c: Int = C("#F2EEE6"), glass: Boolean = false) {
        wallsU.add(u)
        val a = min(z(v0), z(v1)); val e = max(z(v0), z(v1))
        if (glass) {
            box(u, FL, (v0 + v1) / 2, 0.12f, 0.1f, v1 - v0, C("#3B3F44"), Mt.METAL); box(u, FL + 2.5f, (v0 + v1) / 2, 0.12f, 0.1f, v1 - v0, C("#3B3F44"), Mt.METAL)
            box(u, FL + 2.6f, (v0 + v1) / 2, 0.12f, h - 2.6f, v1 - v0, c, Mt.PLASTER, 0.4f)
            var v = v0; while (v <= v1 + 0.01f) { if (doorV.isNaN() || v < doorV - 0.55f || v > doorV + 0.55f) box(u, FL, v, 0.08f, 2.6f, 0.06f, C("#3B3F44"), Mt.METAL); v += 1.2f }
            if (doorV.isNaN()) box(u, FL + 0.1f, (v0 + v1) / 2, 0.03f, 2.4f, v1 - v0, C("#BFD8E2"), Mt.GLASS)
            else { box(u, FL + 0.1f, (v0 + doorV - 0.55f) / 2, 0.03f, 2.4f, doorV - 0.55f - v0, C("#BFD8E2"), Mt.GLASS); box(u, FL + 0.1f, (doorV + 0.55f + v1) / 2, 0.03f, 2.4f, v1 - doorV - 0.55f, C("#BFD8E2"), Mt.GLASS) }
        } else {
            val ops = if (doorV.isNaN()) emptyList() else listOf(CityGeo.Op(z(doorV), 1.0f, FL, FL + 2.2f, true))
            CityGeo.wall(g, 1, u, a, e, FL, FL + h, 1, ops, c, c, Mt.PLASTER, 0.12f, true)
            if (!doorV.isNaN()) { box(u, FL, doorV - 0.53f, 0.16f, 2.25f, 0.06f, C("#8D6E63"), Mt.WOOD, 0.5f); box(u, FL, doorV + 0.53f, 0.16f, 2.25f, 0.06f, C("#8D6E63"), Mt.WOOD, 0.5f); box(u, FL + 2.2f, doorV, 0.16f, 0.06f, 1.12f, C("#8D6E63"), Mt.WOOD, 0.5f) }
        }
        if (doorV.isNaN()) solid(u - 0.08f, v0, u + 0.08f, v1) else { solid(u - 0.08f, v0, u + 0.08f, doorV - 0.55f); solid(u - 0.08f, doorV + 0.55f, u + 0.08f, v1) }
    }

    // ---------------------------------------------------------------- assentos
    /** Cadeira de escritório giratória: base estrela, pistão, braços. Quem senta olha para dir. */
    fun chairO(u: Float, v: Float, dir: Int, c: Int = C("#2E3135")) {
        val k = C("#202225")
        for (a in 0 until 5) { val an = a * 1.2566f; ob(u, v, dir, kotlin.math.cos(an) * 0.14f, FL + 0.03f, kotlin.math.sin(an) * 0.14f, 0.26f, 0.03f, 0.05f, k) }
        oc(u, v, dir, 0f, FL, 0f, 0.07f, 0.06f, k, Mt.METAL, 6)
        oc(u, v, dir, 0f, FL + 0.06f, 0f, 0.025f, 0.36f, C("#9E9E9E"), Mt.METAL, 6)
        ob(u, v, dir, 0f, FL + 0.4f, 0.02f, 0.5f, 0.09f, 0.48f, c, Mt.FABRIC)
        ob(u, v, dir, 0f, FL + 0.56f, -0.24f, 0.46f, 0.6f, 0.07f, c, Mt.FABRIC)
        ob(u, v, dir, 0f, FL + 0.44f, -0.26f, 0.08f, 0.14f, 0.04f, k)
        for (s in floatArrayOf(-1f, 1f)) { ob(u, v, dir, s * 0.27f, FL + 0.49f, -0.02f, 0.04f, 0.17f, 0.04f, k); ob(u, v, dir, s * 0.27f, FL + 0.66f, 0.0f, 0.07f, 0.035f, 0.3f, k) }
        os(u, v, dir, -0.3f, -0.3f, 0.3f, 0.3f)
    }
    /** Cadeira de madeira/metal de 4 pés com encosto vazado. */
    fun chairW(u: Float, v: Float, dir: Int, c: Int = C("#8D6E63"), seat: Int = c, metal: Boolean = false) {
        val m = if (metal) Mt.METAL else Mt.WOOD
        for (a in floatArrayOf(-0.18f, 0.18f)) for (e in floatArrayOf(-0.17f, 0.17f)) ob(u, v, dir, a, FL, e, 0.04f, if (e < 0) 0.92f else 0.44f, 0.04f, c, m, 0.5f)
        ob(u, v, dir, 0f, FL + 0.44f, 0f, 0.44f, 0.05f, 0.42f, seat, if (seat == c) m else Mt.FABRIC, 0.5f)
        ob(u, v, dir, 0f, FL + 0.66f, -0.17f, 0.4f, 0.2f, 0.03f, c, m, 0.5f)
        ob(u, v, dir, 0f, FL + 0.18f, 0f, 0.36f, 0.025f, 0.025f, c, m, 0.5f)
        os(u, v, dir, -0.22f, -0.22f, 0.22f, 0.22f)
    }
    fun stool(u: Float, v: Float, c: Int = C("#C0392B"), hh: Float = 0.75f) {
        oc(u, v, 0, 0f, FL, 0f, 0.2f, 0.03f, C("#9E9E9E"), Mt.METAL, 10); oc(u, v, 0, 0f, FL + 0.03f, 0f, 0.035f, hh - 0.09f, C("#BDBDBD"), Mt.METAL, 6)
        oc(u, v, 0, 0f, FL + 0.28f, 0f, 0.16f, 0.02f, C("#BDBDBD"), Mt.METAL, 10); oc(u, v, 0, 0f, FL + hh - 0.06f, 0f, 0.2f, 0.08f, c, Mt.FABRIC, 12)
        solid(u - 0.2f, v - 0.2f, u + 0.2f, v + 0.2f)
    }
    /** Sofá: base, almofadas do assento separadas, encosto, braços, pés e almofadas soltas. */
    fun sofa(u: Float, v: Float, dir: Int, w: Float = 2.2f, c: Int = C("#4A5A6A"), pillow: Int = C("#E0D3B8")) {
        val k = C("#3A2A1E")
        for (a in floatArrayOf(-w / 2 + 0.1f, w / 2 - 0.1f)) for (e in floatArrayOf(-0.36f, 0.36f)) ob(u, v, dir, a, FL, e, 0.06f, 0.08f, 0.06f, k, Mt.WOOD)
        ob(u, v, dir, 0f, FL + 0.08f, 0f, w, 0.3f, 0.9f, shade(c, -12), Mt.FABRIC)
        val n = max(1, ((w - 0.4f) / 0.7f).toInt()); val cw = (w - 0.4f) / n
        for (i in 0 until n) ob(u, v, dir, -w / 2 + 0.2f + cw * (i + 0.5f), FL + 0.38f, 0.08f, cw - 0.03f, 0.13f, 0.66f, c, Mt.FABRIC)
        ob(u, v, dir, 0f, FL + 0.38f, -0.34f, w - 0.02f, 0.5f, 0.22f, shade(c, -6), Mt.FABRIC)
        for (i in 0 until n) ob(u, v, dir, -w / 2 + 0.2f + cw * (i + 0.5f), FL + 0.5f, -0.2f, cw - 0.04f, 0.36f, 0.1f, c, Mt.FABRIC)
        for (s in floatArrayOf(-1f, 1f)) ob(u, v, dir, s * (w / 2 - 0.1f), FL + 0.08f, 0f, 0.2f, 0.56f, 0.9f, shade(c, -6), Mt.FABRIC)
        if (w > 1.4f) for (s in floatArrayOf(-1f, 1f)) ob(u, v, dir, s * (w / 2 - 0.42f), FL + 0.52f, -0.12f, 0.38f, 0.34f, 0.12f, pillow, Mt.FABRIC)
        os(u, v, dir, -w / 2, -0.45f, w / 2, 0.45f)
    }
    fun bench(u: Float, v: Float, dir: Int, w: Float, c: Int = C("#A1887F"), metal: Int = C("#424242")) {
        for (s in floatArrayOf(-1f, 1f)) ob(u, v, dir, s * (w / 2 - 0.15f), FL, 0f, 0.05f, 0.42f, 0.36f, metal, Mt.METAL)
        for (k in 0..2) ob(u, v, dir, 0f, FL + 0.42f, -0.13f + k * 0.13f, w, 0.04f, 0.11f, c, Mt.WOOD, 0.5f)
        os(u, v, dir, -w / 2, -0.2f, w / 2, 0.2f)
    }
    /** Fileira de cadeiras de espera presas numa barra. */
    fun waitRow(u: Float, v: Float, dir: Int, n: Int, c: Int) {
        val wd = n * 0.58f
        ob(u, v, dir, 0f, FL + 0.3f, 0f, wd, 0.06f, 0.08f, C("#9E9E9E"), Mt.METAL)
        for (s in floatArrayOf(-1f, 1f)) ob(u, v, dir, s * (wd / 2 - 0.1f), FL, 0f, 0.06f, 0.3f, 0.5f, C("#757575"), Mt.METAL)
        for (i in 0 until n) { val lx = -wd / 2 + 0.29f + i * 0.58f; ob(u, v, dir, lx, FL + 0.38f, 0.02f, 0.5f, 0.06f, 0.46f, c, Mt.FABRIC); ob(u, v, dir, lx, FL + 0.44f, -0.22f, 0.5f, 0.48f, 0.05f, c, Mt.FABRIC)
            if (i > 0) ob(u, v, dir, lx - 0.29f, FL + 0.6f, 0f, 0.05f, 0.03f, 0.36f, C("#616161"), Mt.METAL) }
        os(u, v, dir, -wd / 2, -0.3f, wd / 2, 0.28f)
    }

    // ---------------------------------------------------------------- mesas e trabalho
    /** Mesa de escritório: tampo, painel lateral, gaveteiro com puxadores, painel frontal. Quem usa fica em -lz. */
    fun desk(u: Float, v: Float, dir: Int, w: Float = 1.5f, dp: Float = 0.75f, c: Int = C("#C8B49A"), leg: Int = C("#3B3F44")) {
        ob(u, v, dir, 0f, FL + 0.72f, 0f, w, 0.04f, dp, c, Mt.WOOD, 0.5f)
        ob(u, v, dir, -w / 2 + 0.04f, FL, 0f, 0.05f, 0.72f, dp - 0.06f, leg, Mt.METAL)
        ob(u, v, dir, w / 2 - 0.25f, FL, 0.02f, 0.44f, 0.7f, dp - 0.1f, shade(c, -18), Mt.WOOD, 0.5f)
        for (k in 0..2) { ob(u, v, dir, w / 2 - 0.25f, FL + 0.05f + k * 0.22f, -dp / 2 + 0.06f, 0.4f, 0.2f, 0.015f, shade(c, -8), Mt.WOOD, 0.5f); ob(u, v, dir, w / 2 - 0.25f, FL + 0.19f + k * 0.22f, -dp / 2 + 0.05f, 0.12f, 0.02f, 0.02f, C("#9E9E9E"), Mt.METAL) }
        ob(u, v, dir, -0.1f, FL + 0.28f, dp / 2 - 0.05f, w - 0.6f, 0.42f, 0.02f, leg, Mt.METAL)
        os(u, v, dir, -w / 2, -dp / 2, w / 2, dp / 2)
    }
    fun monitor(u: Float, v: Float, dir: Int, y0: Float = FL + 0.76f, wide: Float = 0.56f, glow: Int = C("#4A8CC8")) {
        val k = C("#141414")
        ob(u, v, dir, 0f, y0, 0.03f, 0.22f, 0.015f, 0.16f, k); ob(u, v, dir, 0f, y0 + 0.015f, 0.07f, 0.045f, 0.2f, 0.03f, k)
        ob(u, v, dir, 0f, y0 + 0.15f, 0.04f, wide, wide * 0.6f, 0.03f, k)
        ob(u, v, dir, 0f, y0 + 0.165f, 0.022f, wide - 0.04f, wide * 0.6f - 0.03f, 0.006f, glow, Mt.PLAIN, 1f, false)
        for (i in 0..2) ob(u, v, dir, -wide * 0.12f + i * 0.02f, y0 + 0.21f + i * wide * 0.12f, 0.017f, wide * (0.6f - i * 0.12f), 0.018f, 0.004f, shade(glow, 60 - i * 20), Mt.PLAIN, 1f, false)
    }
    fun keyboard(u: Float, v: Float, dir: Int, y0: Float = FL + 0.76f) { ob(u, v, dir, 0f, y0, 0f, 0.44f, 0.022f, 0.14f, C("#2A2A2A")); ob(u, v, dir, 0f, y0 + 0.022f, 0f, 0.4f, 0.006f, 0.1f, C("#4A4A4A")); ob(u, v, dir, 0.32f, y0, 0f, 0.06f, 0.025f, 0.1f, C("#2A2A2A")) }
    fun mug(u: Float, v: Float, y0: Float = FL + 0.76f) { oc(u, v, 0, 0f, y0, 0f, 0.04f, 0.1f, pc(arrayOf("#FFFFFF", "#E53935", "#1E88E5", "#FDD835", "#212121")), Mt.PLAIN, 8) }
    fun papers(u: Float, v: Float, dir: Int, y0: Float = FL + 0.76f) { val n = 1 + (rn() * 4).toInt(); for (i in 0 until n) ob(u, v, dir, rr(-0.02f, 0.02f), y0 + i * 0.012f, rr(-0.02f, 0.02f), 0.21f, 0.01f, 0.3f, if (i == n - 1 && rn() < 0.4f) C("#FFF59D") else C("#FAFAFA")) }
    fun deskLamp(u: Float, v: Float, y0: Float = FL + 0.76f, c: Int = C("#263238")) { oc(u, v, 0, 0f, y0, 0f, 0.08f, 0.02f, c, Mt.METAL, 8); oc(u, v, 0, 0f, y0 + 0.02f, 0f, 0.012f, 0.38f, c, Mt.METAL, 5); oc(u, v, 0, 0f, y0 + 0.34f, 0f, 0.1f, 0.12f, c, Mt.METAL, 8, 0.05f); oc(u, v, 0, 0f, y0 + 0.335f, 0f, 0.08f, 0.01f, C("#FFF8D0"), Mt.PLAIN, 8, 0.08f, false) }
    fun smallPlant(u: Float, v: Float, y0: Float = FL + 0.76f) { oc(u, v, 0, 0f, y0, 0f, 0.07f, 0.12f, C("#ECEFF1"), Mt.PLAIN, 8, 0.09f); ball(u, y0 + 0.2f, v, 0.12f, C("#558B2F")) }
    fun phone(u: Float, v: Float, dir: Int, y0: Float = FL + 0.76f) { ob(u, v, dir, 0f, y0, 0f, 0.2f, 0.06f, 0.18f, C("#263238")); ob(u, v, dir, 0f, y0 + 0.06f, 0.03f, 0.2f, 0.04f, 0.06f, C("#37474F")) }
    /** Posto de trabalho completo: mesa, 1-2 monitores, teclado, mouse, cadeira e objetos pessoais variados. */
    fun station(u: Float, v: Float, dir: Int, w: Float = 1.5f, nm: Int = 1, dc: Int = C("#C8B49A"), cc: Int = C("#2E3135"), glow: Int = C("#4A8CC8")) {
        desk(u, v, dir, w, 0.75f, dc)
        if (nm == 1) monitor(au(u, v, dir, -0.1f, 0.15f), av(u, v, dir, -0.1f, 0.15f), dir, glow = glow)
        else for (s in floatArrayOf(-0.31f, 0.31f)) monitor(au(u, v, dir, s - 0.05f, 0.15f), av(u, v, dir, s - 0.05f, 0.15f), dir, glow = glow)
        keyboard(au(u, v, dir, -0.12f, -0.16f), av(u, v, dir, -0.12f, -0.16f), dir)
        chairO(au(u, v, dir, -0.1f, -0.72f), av(u, v, dir, -0.1f, -0.72f), dir, cc)
        val q = rn()
        if (q < 0.5f) mug(au(u, v, dir, w / 2 - 0.2f, -0.15f), av(u, v, dir, w / 2 - 0.2f, -0.15f))
        if (q > 0.3f) papers(au(u, v, dir, -w / 2 + 0.25f, 0f), av(u, v, dir, -w / 2 + 0.25f, 0f), dir)
        if (q > 0.65f) smallPlant(au(u, v, dir, w / 2 - 0.18f, 0.22f), av(u, v, dir, w / 2 - 0.18f, 0.22f))
        else if (q < 0.25f) deskLamp(au(u, v, dir, w / 2 - 0.15f, 0.22f), av(u, v, dir, w / 2 - 0.15f, 0.22f))
    }
    /** Mesa de 4 pés. */
    fun table(u: Float, v: Float, su: Float, sv: Float, c: Int = C("#9A7350"), leg: Int = C("#3B3F44"), hh: Float = 0.75f, mat: Int = Mt.WOOD) {
        box(u, FL + hh - 0.04f, v, su, 0.04f, sv, c, mat, 0.5f)
        box(u, FL + hh - 0.12f, v, su - 0.1f, 0.08f, sv - 0.1f, shade(c, -15), mat, 0.5f)
        for (a in floatArrayOf(-1f, 1f)) for (e in floatArrayOf(-1f, 1f)) box(u + a * (su / 2 - 0.08f), FL, v + e * (sv / 2 - 0.08f), 0.06f, hh - 0.04f, 0.06f, leg, Mt.METAL)
        solid(u - su / 2, v - sv / 2, u + su / 2, v + sv / 2)
    }
    fun tableRound(u: Float, v: Float, r: Float, c: Int = C("#F5F5F5"), hh: Float = 0.75f) {
        oc(u, v, 0, 0f, FL + hh - 0.04f, 0f, r, 0.04f, c, Mt.WOOD, 14); oc(u, v, 0, 0f, FL + 0.02f, 0f, 0.04f, hh - 0.06f, C("#424242"), Mt.METAL, 6); oc(u, v, 0, 0f, FL, 0f, 0.25f, 0.03f, C("#424242"), Mt.METAL, 10)
        solid(u - r, v - r, u + r, v + r)
    }
    /** Balcão de atendimento: frente alta com faixa de cor, tampo de apoio, superfície de trabalho atrás. Cliente em -lz. */
    fun reception(u: Float, v: Float, dir: Int, len: Float, c: Int, top: Int, accent: Int, staff: Int = 1) {
        ob(u, v, dir, 0f, FL + 0.08f, -0.3f, len, 1.02f, 0.08f, c, Mt.WOOD, 0.5f)
        ob(u, v, dir, 0f, FL, -0.27f, len - 0.04f, 0.08f, 0.04f, shade(c, -40))
        ob(u, v, dir, 0f, FL + 0.7f, -0.345f, len - 0.2f, 0.07f, 0.01f, accent, Mt.PLAIN, 1f, false)
        ob(u, v, dir, 0f, FL + 1.1f, -0.22f, len + 0.06f, 0.05f, 0.36f, top, Mt.STONE, 1f)
        for (s in floatArrayOf(-1f, 1f)) ob(u, v, dir, s * (len / 2 - 0.03f), FL, 0.08f, 0.06f, 1.1f, 0.76f, c, Mt.WOOD, 0.5f)
        ob(u, v, dir, 0f, FL + 0.72f, 0.12f, len - 0.1f, 0.04f, 0.6f, top, Mt.WOOD, 0.5f)
        os(u, v, dir, -len / 2, -0.4f, len / 2, 0.45f)
        val wd = op(dir)
        for (i in 0 until staff) {
            val lx = -len / 2 + len * (i + 0.5f) / staff
            monitor(au(u, v, dir, lx, 0.3f), av(u, v, dir, lx, 0.3f), wd)
            keyboard(au(u, v, dir, lx, 0.05f), av(u, v, dir, lx, 0.05f), wd)
            chairO(au(u, v, dir, lx, 0.85f), av(u, v, dir, lx, 0.85f), wd, shade(c, -10))
        }
        phone(au(u, v, dir, len / 2 - 0.3f, 0.2f), av(u, v, dir, len / 2 - 0.3f, 0.2f), wd)
        if (len > 2.4f) smallPlant(au(u, v, dir, -len / 2 + 0.25f, -0.22f), av(u, v, dir, -len / 2 + 0.25f, -0.22f), FL + 1.15f)
    }
    /** Balcão comum (loja/cozinha): corpo, rodapé recuado, tampo com beiral. */
    fun counter(u: Float, v: Float, dir: Int, len: Float, dp: Float = 0.7f, c: Int = C("#5A3A22"), top: Int = C("#E8E2D6"), hh: Float = 0.92f, doors: Boolean = true) {
        ob(u, v, dir, 0f, FL, 0.04f, len - 0.04f, 0.1f, dp - 0.1f, shade(c, -40))
        ob(u, v, dir, 0f, FL + 0.1f, 0f, len, hh - 0.1f, dp, c, Mt.WOOD, 0.5f)
        ob(u, v, dir, 0f, FL + hh, -0.02f, len + 0.04f, 0.04f, dp + 0.04f, top, Mt.STONE, 1f)
        if (doors) { val n = max(1, (len / 0.6f).toInt()); val dw = len / n
            for (i in 0 until n) { ob(u, v, dir, -len / 2 + dw * (i + 0.5f), FL + 0.14f, -dp / 2 - 0.005f, dw - 0.04f, hh - 0.2f, 0.01f, shade(c, 10), Mt.WOOD, 0.5f); ob(u, v, dir, -len / 2 + dw * (i + 0.5f) + dw * 0.3f, FL + hh - 0.25f, -dp / 2 - 0.015f, 0.02f, 0.12f, 0.02f, C("#B0B0B0"), Mt.METAL) } }
        os(u, v, dir, -len / 2, -dp / 2, len / 2, dp / 2)
    }

    // ---------------------------------------------------------------- armazenamento
    private val bookC = arrayOf("#8E2424", "#1E3A6E", "#2E5E3A", "#B07A1E", "#5B3A6E", "#3C3C3C", "#C9B79C", "#6E2E1E", "#1E5E6E", "#E0D6C2")
    /** Estante de livros encostada na parede (aberta para -lz). */
    fun bookcase(u: Float, v: Float, dir: Int, len: Float, c: Int = C("#5D4037"), hh: Float = 2.2f, fill: Float = 0.85f) {
        ob(u, v, dir, 0f, FL, 0.16f, len, hh, 0.03f, shade(c, -20), Mt.WOOD, 0.5f)
        for (s in floatArrayOf(-1f, 1f)) ob(u, v, dir, s * (len / 2 - 0.02f), FL, 0f, 0.04f, hh, 0.36f, c, Mt.WOOD, 0.5f)
        val n = max(3, ((hh - 0.15f) / 0.4f).toInt()); val sh = (hh - 0.12f) / n
        for (i in 0..n) ob(u, v, dir, 0f, FL + 0.08f + i * sh - (if (i == n) 0f else 0f), 0f, len - 0.04f, 0.03f, 0.35f, c, Mt.WOOD, 0.5f)
        ob(u, v, dir, 0f, FL, -0.16f, len - 0.04f, 0.08f, 0.02f, shade(c, -25))
        val cols = max(1, ((len - 0.08f) / 0.9f).toInt())
        for (i in 0 until n) {
            var x = -len / 2 + 0.06f
            while (x < len / 2 - 0.12f) {
                val seg = min(rr(0.18f, 0.55f), len / 2 - 0.06f - x)
                if (rn() < fill) { val bh = rr(0.2f, min(0.32f, sh - 0.06f)); ob(u, v, dir, x + seg / 2, FL + 0.11f + i * sh, 0.02f, seg - 0.01f, bh, 0.24f, C(bookC[(rn() * bookC.size).toInt().coerceIn(0, 9)]), Mt.BOOKS, 0.6f) }
                else if (rn() < 0.4f) { oc(au(u, v, dir, x + seg / 2, 0f), av(u, v, dir, x + seg / 2, 0f), 0, 0f, FL + 0.11f + i * sh, 0f, 0.06f, 0.14f, pc(arrayOf("#ECEFF1", "#B0855A", "#26A69A")), Mt.PLAIN, 8) }
                x += seg
            }
        }
        if (cols < 0) Unit
        os(u, v, dir, -len / 2, -0.2f, len / 2, 0.2f)
    }
    fun fileCab(u: Float, v: Float, dir: Int, n: Int, c: Int = C("#90A4AE"), dr: Int = 4) {
        for (k in 0 until n) { val lx = -(n - 1) * 0.25f + k * 0.5f
            ob(u, v, dir, lx, FL, 0f, 0.47f, dr * 0.33f + 0.04f, 0.6f, c, Mt.METAL)
            for (j in 0 until dr) { ob(u, v, dir, lx, FL + 0.04f + j * 0.33f, -0.305f, 0.42f, 0.29f, 0.01f, shade(c, 12), Mt.METAL); ob(u, v, dir, lx, FL + 0.24f + j * 0.33f, -0.315f, 0.14f, 0.025f, 0.02f, C("#5F6B72"), Mt.METAL); ob(u, v, dir, lx, FL + 0.28f + j * 0.33f, -0.312f, 0.08f, 0.04f, 0.01f, C("#FAFAFA")) } }
        if (rn() < 0.6f) papers(au(u, v, dir, 0f, 0f), av(u, v, dir, 0f, 0f), dir, FL + dr * 0.33f + 0.04f)
        os(u, v, dir, -n * 0.25f, -0.32f, n * 0.25f, 0.3f)
    }
    /** Armários de vestiário com respiro, puxador, número e banco na frente. */
    fun lockers(u: Float, v: Float, dir: Int, n: Int, c: Int = C("#5C7A8E"), withBench: Boolean = true) {
        for (k in 0 until n) { val lx = -(n - 1) * 0.24f + k * 0.48f
            ob(u, v, dir, lx, FL + 0.1f, 0f, 0.46f, 1.8f, 0.48f, c, Mt.METAL); ob(u, v, dir, lx, FL, 0.02f, 0.46f, 0.1f, 0.44f, C("#37474F"))
            for (j in 0..3) ob(u, v, dir, lx, FL + 1.55f + j * 0.06f, -0.245f, 0.26f, 0.02f, 0.01f, shade(c, -35))
            for (j in 0..3) ob(u, v, dir, lx, FL + 0.25f + j * 0.06f, -0.245f, 0.26f, 0.02f, 0.01f, shade(c, -35))
            ob(u, v, dir, lx + 0.15f, FL + 1.0f, -0.25f, 0.03f, 0.16f, 0.03f, C("#E0E0E0"), Mt.METAL); ob(u, v, dir, lx, FL + 1.32f, -0.245f, 0.1f, 0.06f, 0.01f, C("#FAFAFA"))
            ob(u, v, dir, lx + 0.23f, FL + 0.1f, -0.245f, 0.006f, 1.8f, 0.01f, shade(c, -45)) }
        os(u, v, dir, -n * 0.24f, -0.25f, n * 0.24f, 0.25f)
        if (withBench) bench(au(u, v, dir, 0f, -0.85f), av(u, v, dir, 0f, -0.85f), dir, min(n * 0.48f - 0.2f, 2.4f))
    }
    /** Porta-paletes / estante metálica com caixas de papelão. */
    fun rack(u: Float, v: Float, dir: Int, len: Float, hh: Float = 2.6f, beam: Int = C("#EF6C00"), up: Int = C("#1565C0"), dp: Float = 1.0f) {
        val bays = max(1, (len / 2.4f).toInt()); val bw = len / bays; val lv = max(2, (hh / 0.9f).toInt())
        for (i in 0..bays) for (e in floatArrayOf(-dp / 2 + 0.04f, dp / 2 - 0.04f)) ob(u, v, dir, -len / 2 + i * bw, FL, e, 0.08f, hh, 0.08f, up, Mt.METAL)
        for (j in 0 until lv) { val y = FL + 0.12f + j * hh / lv
            for (e in floatArrayOf(-dp / 2 + 0.04f, dp / 2 - 0.04f)) ob(u, v, dir, 0f, y, e, len, 0.1f, 0.05f, beam, Mt.METAL)
            ob(u, v, dir, 0f, y + 0.1f, 0f, len - 0.04f, 0.02f, dp - 0.06f, C("#A1887F"), Mt.WOOD, 0.5f)
            for (i in 0 until bays) { var x = -len / 2 + i * bw + 0.1f
                while (x < -len / 2 + (i + 1) * bw - 0.4f) { val bx = rr(0.35f, 0.7f); if (x + bx > -len / 2 + (i + 1) * bw - 0.08f) break
                    val by = rr(0.25f, min(0.65f, hh / lv - 0.2f)); if (rn() < 0.85f) { ob(u, v, dir, x + bx / 2, y + 0.12f, rr(-0.05f, 0.05f), bx - 0.03f, by, rr(0.45f, dp - 0.15f), pc(arrayOf("#C49A6C", "#B8895A", "#D2AE82", "#A67C52")), Mt.PLAIN); ob(u, v, dir, x + bx / 2, y + 0.12f + by * 0.5f, -dp / 2 + 0.1f, bx * 0.5f, 0.07f, 0.01f, C("#FAFAFA")) }
                    x += bx + 0.04f } } }
        os(u, v, dir, -len / 2, -dp / 2, len / 2, dp / 2)
    }
    private val goodsC = arrayOf("#D32F2F", "#1976D2", "#FBC02D", "#388E3C", "#F57C00", "#7B1FA2", "#00897B", "#FFFFFF", "#5D4037", "#E91E63")
    /** Gôndola de supermercado dupla face com produtos variados, faixa de preço e pontas de gôndola. */
    fun gondola(u: Float, v: Float, dir: Int, len: Float, ends: Boolean = true) {
        ob(u, v, dir, 0f, FL, 0f, len, 0.12f, 1.0f, C("#ECEFF1"), Mt.METAL)
        ob(u, v, dir, 0f, FL, 0f, len, 1.75f, 0.06f, C("#CFD8DC"), Mt.METAL)
        ob(u, v, dir, 0f, FL + 1.75f, 0f, len, 0.18f, 0.08f, C("#E53935"))
        for (s in floatArrayOf(-1f, 1f)) for (j in 0..3) { val y = FL + 0.12f + j * 0.42f
            ob(u, v, dir, 0f, y, s * 0.26f, len, 0.025f, 0.46f, C("#E0E0E0"), Mt.METAL)
            ob(u, v, dir, 0f, y - 0.04f, s * 0.49f, len, 0.06f, 0.012f, C(if (j % 2 == 0) "#FFF59D" else "#FAFAFA"), Mt.PLAIN, 1f, false)
            var x = -len / 2 + 0.04f
            while (x < len / 2 - 0.12f) { val seg = min(rr(0.2f, 0.6f), len / 2 - 0.04f - x); val ph = rr(0.16f, 0.32f)
                ob(u, v, dir, x + seg / 2, y + 0.025f, s * 0.27f, seg - 0.02f, ph, 0.4f, C(goodsC[(rn() * goodsC.size).toInt().coerceIn(0, 9)]), Mt.GOODS, 0.7f)
                x += seg } }
        if (ends) for (s in floatArrayOf(-1f, 1f)) { ob(u, v, dir, s * (len / 2 + 0.3f), FL, 0f, 0.6f, 0.9f, 0.9f, C("#E53935"), Mt.PLAIN); for (k in 0..2) for (q in 0..1) ob(u, v, dir, s * (len / 2 + 0.3f), FL + 0.9f + k * 0.2f, -0.2f + q * 0.4f, 0.5f, 0.19f, 0.36f, C(goodsC[(k + q * 3 + (len * 3).toInt()) % 10]), Mt.GOODS, 0.7f) }
        os(u, v, dir, -len / 2 - (if (ends) 0.6f else 0f), -0.5f, len / 2 + (if (ends) 0.6f else 0f), 0.5f)
    }
    /** Geladeira vertical com portas de vidro, interior iluminado e produtos. Aberta para -lz. */
    fun fridge(u: Float, v: Float, dir: Int, len: Float, c: Int = C("#ECEFF1")) {
        ob(u, v, dir, 0f, FL, 0f, len, 2.1f, 0.8f, c, Mt.METAL)
        ob(u, v, dir, 0f, FL + 2.1f, -0.05f, len, 0.25f, 0.7f, C("#1565C0"))
        ob(u, v, dir, 0f, FL + 0.15f, -0.38f, len - 0.1f, 1.8f, 0.02f, C("#F1FAFF"), Mt.PLAIN, 1f, false)
        for (j in 0..4) { ob(u, v, dir, 0f, FL + 0.2f + j * 0.36f, -0.34f, len - 0.12f, 0.02f, 0.05f, C("#B0BEC5"), Mt.METAL)
            var x = -len / 2 + 0.08f; while (x < len / 2 - 0.12f) { val seg = min(rr(0.12f, 0.3f), len / 2 - 0.06f - x); ob(u, v, dir, x + seg / 2, FL + 0.22f + j * 0.36f, -0.33f, seg - 0.03f, rr(0.18f, 0.3f), 0.06f, C(goodsC[(rn() * 10).toInt().coerceIn(0, 9)]), Mt.GOODS, 0.7f); x += seg } }
        val n = max(1, (len / 0.75f).toInt()); for (i in 0..n) ob(u, v, dir, -len / 2 + i * len / n, FL + 0.1f, -0.41f, 0.05f, 1.9f, 0.04f, C("#90A4AE"), Mt.METAL)
        ob(u, v, dir, 0f, FL + 0.12f, -0.415f, len, 1.86f, 0.01f, C("#CFE8F2"), Mt.GLASS)
        for (i in 0 until n) ob(u, v, dir, -len / 2 + (i + 0.85f) * len / n, FL + 0.8f, -0.44f, 0.03f, 0.5f, 0.03f, C("#ECEFF1"), Mt.METAL)
        os(u, v, dir, -len / 2, -0.42f, len / 2, 0.4f)
    }
    /** Caixa de supermercado: esteira ao longo de lz, operador no lado +lx. */
    fun checkout(u: Float, v: Float, dir: Int, accent: Int = C("#E53935")) {
        ob(u, v, dir, 0f, FL, 0f, 0.8f, 0.9f, 2.6f, C("#455A64"), Mt.METAL); ob(u, v, dir, 0f, FL + 0.5f, 0f, 0.82f, 0.1f, 2.62f, accent)
        ob(u, v, dir, -0.05f, FL + 0.9f, -0.35f, 0.55f, 0.03f, 1.7f, C("#1A1A1A"))
        ob(u, v, dir, 0f, FL + 0.9f, 0.85f, 0.75f, 0.03f, 0.8f, C("#B0BEC5"), Mt.METAL); ob(u, v, dir, -0.3f, FL + 0.93f, 0.85f, 0.04f, 0.12f, 0.8f, C("#B0BEC5"), Mt.METAL)
        ob(u, v, dir, 0.32f, FL + 0.93f, 0.35f, 0.3f, 0.15f, 0.35f, C("#263238")); ob(u, v, dir, 0.32f, FL + 1.08f, 0.35f, 0.04f, 0.25f, 0.04f, C("#263238"))
        ob(u, v, dir, 0.32f, FL + 1.28f, 0.35f, 0.3f, 0.2f, 0.03f, C("#212121")); ob(u, v, dir, 0.32f, FL + 1.3f, 0.335f, 0.26f, 0.16f, 0.005f, C("#7FD1FF"), Mt.PLAIN, 1f, false)
        ob(u, v, dir, 0f, FL + 0.93f, 0.15f, 0.3f, 0.03f, 0.25f, C("#90CAF9"), Mt.GLASS)
        oc(au(u, v, dir, 0f, 0.1f), av(u, v, dir, 0f, 0.1f), 0, 0f, FL + 0.9f, 0f, 0.03f, 1.4f, C("#9E9E9E")); ob(u, v, dir, 0f, FL + 2.3f, 0.1f, 0.25f, 0.25f, 0.06f, accent, Mt.PLAIN, 1f, false)
        os(u, v, dir, -0.4f, -1.3f, 0.4f, 1.3f)
        stool(au(u, v, dir, 0.85f, 0.35f), av(u, v, dir, 0.85f, 0.35f), C("#37474F"), 0.7f)
    }

    // ---------------------------------------------------------------- camas e saúde
    fun bedH(u: Float, v: Float, dir: Int, blanket: Int = C("#90CAF9")) {
        val m = C("#B0BEC5")
        for (a in floatArrayOf(-0.42f, 0.42f)) for (e in floatArrayOf(-0.9f, 0.9f)) { ob(u, v, dir, a, FL, e, 0.06f, 0.1f, 0.06f, C("#212121")); ob(u, v, dir, a, FL + 0.1f, e, 0.04f, 0.38f, 0.04f, m, Mt.METAL) }
        ob(u, v, dir, 0f, FL + 0.45f, 0f, 0.92f, 0.08f, 2.0f, m, Mt.METAL); ob(u, v, dir, 0f, FL + 0.53f, 0f, 0.88f, 0.14f, 1.95f, C("#FAFAFA"), Mt.FABRIC)
        ob(u, v, dir, 0f, FL + 0.6f, -0.25f, 0.92f, 0.1f, 1.3f, blanket, Mt.FABRIC); ob(u, v, dir, 0f, FL + 0.67f, 0.75f, 0.6f, 0.12f, 0.35f, C("#FFFFFF"), Mt.FABRIC)
        ob(u, v, dir, 0f, FL + 0.45f, 0.98f, 0.92f, 0.6f, 0.05f, m, Mt.METAL); ob(u, v, dir, 0f, FL + 0.45f, -0.98f, 0.92f, 0.35f, 0.05f, m, Mt.METAL)
        for (s in floatArrayOf(-1f, 1f)) { ob(u, v, dir, s * 0.47f, FL + 0.75f, 0.35f, 0.03f, 0.04f, 0.9f, m, Mt.METAL); ob(u, v, dir, s * 0.47f, FL + 0.55f, 0.35f, 0.03f, 0.2f, 0.03f, m, Mt.METAL) }
        // suporte de soro e monitor ao lado da cabeceira
        val iu = au(u, v, dir, 0.75f, 0.7f); val iv = av(u, v, dir, 0.75f, 0.7f)
        oc(iu, iv, 0, 0f, FL, 0f, 0.22f, 0.03f, C("#616161"), Mt.METAL, 5); oc(iu, iv, 0, 0f, FL, 0f, 0.015f, 1.95f, C("#BDBDBD"), Mt.METAL, 5)
        box(iu, FL + 1.65f, iv, 0.12f, 0.2f, 0.05f, C("#E3F2FD"), Mt.GLASS)
        val mu = au(u, v, dir, -0.8f, 0.8f); val mv = av(u, v, dir, -0.8f, 0.8f)
        box(mu, FL, mv, 0.45f, 0.7f, 0.4f, C("#ECEFF1"), Mt.METAL); box(mu, FL + 0.7f, mv, 0.32f, 0.26f, 0.08f, C("#263238")); monitorFlat(mu, mv, dir)
        os(u, v, dir, -0.5f, -1.05f, 0.5f, 1.05f); solid(iu - 0.15f, iv - 0.15f, iu + 0.15f, iv + 0.15f)
    }
    private fun monitorFlat(u: Float, v: Float, dir: Int) { ob(u, v, dir, 0f, FL + 0.73f, -0.045f, 0.28f, 0.2f, 0.005f, C("#0B3D2E"), Mt.PLAIN, 1f, false); ob(u, v, dir, 0f, FL + 0.8f, -0.05f, 0.24f, 0.015f, 0.004f, C("#69F0AE"), Mt.PLAIN, 1f, false) }
    fun bed(u: Float, v: Float, dir: Int, c: Int = C("#E8EEF2"), frame: Int = C("#6D4C41")) {
        ob(u, v, dir, 0f, FL, 0f, 1.0f, 0.35f, 2.0f, frame, Mt.WOOD, 0.5f); ob(u, v, dir, 0f, FL + 0.35f, 0f, 0.96f, 0.18f, 1.95f, C("#FAFAFA"), Mt.FABRIC)
        ob(u, v, dir, 0f, FL + 0.48f, -0.3f, 1.0f, 0.08f, 1.4f, c, Mt.FABRIC); ob(u, v, dir, 0f, FL + 0.53f, 0.72f, 0.7f, 0.12f, 0.35f, C("#FFFFFF"), Mt.FABRIC)
        ob(u, v, dir, 0f, FL, 1.0f, 1.04f, 0.95f, 0.06f, frame, Mt.WOOD, 0.5f)
        os(u, v, dir, -0.52f, -1.0f, 0.52f, 1.03f)
    }
    fun bunk(u: Float, v: Float, dir: Int, c: Int) {
        for (a in floatArrayOf(-0.48f, 0.48f)) for (e in floatArrayOf(-0.97f, 0.97f)) ob(u, v, dir, a, FL, e, 0.05f, 1.9f, 0.05f, C("#607D8B"), Mt.METAL)
        for (y in floatArrayOf(0.3f, 1.35f)) { ob(u, v, dir, 0f, FL + y, 0f, 0.98f, 0.06f, 1.98f, C("#607D8B"), Mt.METAL); ob(u, v, dir, 0f, FL + y + 0.06f, 0f, 0.92f, 0.14f, 1.9f, C("#FAFAFA"), Mt.FABRIC); ob(u, v, dir, 0f, FL + y + 0.17f, -0.3f, 0.94f, 0.06f, 1.3f, c, Mt.FABRIC); ob(u, v, dir, 0f, FL + y + 0.2f, 0.7f, 0.6f, 0.1f, 0.3f, C("#FFFFFF"), Mt.FABRIC) }
        for (k in 0..3) ob(u, v, dir, 0.5f, FL + 0.5f + k * 0.28f, -0.6f, 0.04f, 0.03f, 0.3f, C("#90A4AE"), Mt.METAL)
        os(u, v, dir, -0.5f, -1.0f, 0.5f, 1.0f)
    }
    fun sinkCab(u: Float, v: Float, dir: Int, len: Float = 1.2f) {
        counter(u, v, dir, len, 0.6f, C("#ECEFF1"), C("#FAFAFA"))
        ob(u, v, dir, 0f, FL + 0.9f, 0f, 0.45f, 0.03f, 0.35f, C("#B0BEC5"), Mt.METAL); oc(au(u, v, dir, 0f, 0.22f), av(u, v, dir, 0f, 0.22f), 0, 0f, FL + 0.96f, 0f, 0.02f, 0.3f, C("#CFD8DC")); ob(u, v, dir, 0f, FL + 1.24f, 0.15f, 0.03f, 0.03f, 0.16f, C("#CFD8DC"), Mt.METAL)
        ob(u, v, dir, 0f, FL + 1.3f, 0.27f, 0.6f, 0.75f, 0.03f, C("#DDE7EC"), Mt.GLASS)
    }

    // ---------------------------------------------------------------- parede e decoração
    /** Quadro de parede (aberto para -lz, encostado em +lz). kind 0 branco, 1 lousa verde, 2 cortiça. */
    fun board(u: Float, v: Float, dir: Int, w: Float, kind: Int = 0, y0: Float = FL + 0.9f, hh: Float = 1.2f) {
        val face = when (kind) { 1 -> C("#2E5D3A"); 2 -> C("#C69C6D"); else -> C("#FAFAFA") }
        ob(u, v, dir, 0f, y0 - 0.04f, 0f, w + 0.08f, hh + 0.08f, 0.03f, C(if (kind == 2) "#6D4C41" else "#B0BEC5"), Mt.METAL)
        ob(u, v, dir, 0f, y0, -0.02f, w, hh, 0.012f, face, if (kind == 2) Mt.FABRIC else Mt.PLAIN)
        ob(u, v, dir, 0f, y0 - 0.06f, -0.06f, w * 0.9f, 0.03f, 0.08f, C("#B0BEC5"), Mt.METAL)
        val ink = arrayOf("#1565C0", "#C62828", "#2E7D32", "#212121")
        for (i in 0 until 6) { val lw = rr(0.2f, w * 0.45f); val lx = rr(-w / 2 + 0.1f + lw / 2, w / 2 - 0.1f - lw / 2); val ly = y0 + 0.15f + i * (hh - 0.3f) / 6
            when (kind) { 1 -> ob(u, v, dir, lx, ly, -0.03f, lw, 0.025f, 0.004f, C("#E8F5E9"), Mt.PLAIN, 1f, false)
                2 -> ob(u, v, dir, lx, ly - 0.05f, -0.03f, 0.2f, 0.24f, 0.004f, pc(arrayOf("#FFF59D", "#FFFFFF", "#80DEEA", "#F48FB1", "#C5E1A5")))
                else -> ob(u, v, dir, lx, ly, -0.03f, lw, 0.025f, 0.004f, C(ink[(i + (w * 7).toInt()) % 4])) } }
    }
    /** Quadro decorativo abstrato. */
    fun art(u: Float, v: Float, dir: Int, w: Float, hh: Float, y0: Float = FL + 1.2f, frame: Int = C("#2B2B2B")) {
        ob(u, v, dir, 0f, y0, 0f, w, hh, 0.04f, frame); ob(u, v, dir, 0f, y0 + 0.05f, -0.022f, w - 0.1f, hh - 0.1f, 0.005f, C("#F5F1E8"))
        val pal = arrayOf("#E07A5F", "#3D405B", "#81B29A", "#F2CC8F", "#5E81AC", "#BF616A", "#A3BE8C", "#D08770")
        for (i in 0 until 3) { val bw = rr(w * 0.2f, w * 0.5f); val bh = rr(hh * 0.2f, hh * 0.55f); ob(u, v, dir, rr(-w / 2 + 0.1f + bw / 2, w / 2 - 0.1f - bw / 2), y0 + rr(0.08f, hh - 0.08f - bh), -0.026f - i * 0.002f, bw, bh, 0.003f, pc(pal)) }
    }
    fun tv(u: Float, v: Float, dir: Int, w: Float, y0: Float = FL + 1.3f, glow: Int = C("#3A6EA5")) {
        ob(u, v, dir, 0f, y0, 0f, w, w * 0.57f, 0.06f, C("#111111")); ob(u, v, dir, 0f, y0 + 0.03f, -0.032f, w - 0.06f, w * 0.57f - 0.06f, 0.005f, glow, Mt.PLAIN, 1f, false)
        ob(u, v, dir, -w * 0.15f, y0 + w * 0.12f, -0.036f, w * 0.5f, w * 0.25f, 0.004f, shade(glow, 50), Mt.PLAIN, 1f, false)
    }
    fun clock(u: Float, v: Float, dir: Int, y0: Float) { ob(u, v, dir, 0f, y0, 0f, 0.36f, 0.36f, 0.04f, C("#263238")); ob(u, v, dir, 0f, y0 + 0.03f, -0.022f, 0.3f, 0.3f, 0.005f, C("#FAFAFA")); ob(u, v, dir, 0f, y0 + 0.17f, -0.027f, 0.02f, 0.12f, 0.004f, C("#212121")); ob(u, v, dir, 0.04f, y0 + 0.17f, -0.027f, 0.1f, 0.02f, 0.004f, C("#212121")) }
    fun rug(u: Float, v: Float, su: Float, sv: Float, c: Int, border: Int = shade(c, -30)) { box(u, FL, v, su, 0.01f, sv, border, Mt.RUG, 1f); box(u, FL + 0.01f, v, su - 0.2f, 0.006f, sv - 0.2f, c, Mt.RUG, 1f) }
    fun floorLamp(u: Float, v: Float) { oc(u, v, 0, 0f, FL, 0f, 0.16f, 0.03f, C("#212121"), Mt.METAL, 10); oc(u, v, 0, 0f, FL + 0.03f, 0f, 0.015f, 1.45f, C("#212121"), Mt.METAL, 5); oc(u, v, 0, 0f, FL + 1.35f, 0f, 0.22f, 0.3f, C("#F3E5C8"), Mt.FABRIC, 12, 0.16f); oc(u, v, 0, 0f, FL + 1.34f, 0f, 0.2f, 0.01f, C("#FFF3C4"), Mt.PLAIN, 12, 0.2f, false); solid(u - 0.18f, v - 0.18f, u + 0.18f, v + 0.18f) }
    fun pendant(u: Float, v: Float, drop: Float = 1.0f, c: Int = C("#263238")) { oc(u, v, 0, 0f, FL + h - drop, 0f, 0.008f, drop, C("#212121"), Mt.PLAIN, 4); oc(u, v, 0, 0f, FL + h - drop - 0.25f, 0f, 0.28f, 0.25f, c, Mt.METAL, 12, 0.08f); oc(u, v, 0, 0f, FL + h - drop - 0.26f, 0f, 0.25f, 0.01f, C("#FFF6D0"), Mt.PLAIN, 12, 0.25f, false) }
    /** Planta em vaso: 0 arbusto, 1 árvore (ficus), 2 espada-de-são-jorge, 3 palmeira. */
    fun plant(u: Float, v: Float, kind: Int = 0, pot: Int = C("#B5643C")) {
        when (kind) {
            1 -> { oc(u, v, 0, 0f, FL, 0f, 0.24f, 0.45f, pot, Mt.PLAIN, 10, 0.3f); oc(u, v, 0, 0f, FL + 0.44f, 0f, 0.27f, 0.02f, C("#4E342E"), Mt.PLAIN, 10); oc(u, v, 0, 0f, FL + 0.45f, 0f, 0.04f, 1.1f, C("#6D4C41"), Mt.BARK, 5)
                ball(u, FL + 1.6f, v, 0.45f, C("#2E7D32"), 0.4f); ball(u + 0.22f, FL + 1.35f, v + 0.1f, 0.3f, C("#388E3C")); ball(u - 0.2f, FL + 1.4f, v - 0.12f, 0.32f, C("#43A047")) }
            2 -> { box(u, FL, v, 0.38f, 0.42f, 0.38f, pot); for (i in 0 until 7) { val a = i * 0.9f; box(u + kotlin.math.cos(a) * 0.08f, FL + 0.42f, v + kotlin.math.sin(a) * 0.08f, 0.06f, rr(0.5f, 0.85f), 0.02f, C(if (i % 2 == 0) "#33691E" else "#558B2F"), Mt.LEAF, 1f) } }
            3 -> { oc(u, v, 0, 0f, FL, 0f, 0.26f, 0.5f, pot, Mt.PLAIN, 10, 0.22f); for (i in 0 until 3) oc(u + (i - 1) * 0.06f, v, 0, 0f, FL + 0.5f, 0f, 0.03f, 0.9f + i * 0.2f, C("#8D6E63"), Mt.BARK, 5)
                for (i in 0 until 6) { val a = i * 1.05f; ball(u + kotlin.math.cos(a) * 0.35f, FL + 1.5f + (i % 2) * 0.2f, v + kotlin.math.sin(a) * 0.35f, 0.32f, C("#558B2F"), 0.12f) } }
            else -> { oc(u, v, 0, 0f, FL, 0f, 0.2f, 0.4f, pot, Mt.PLAIN, 10, 0.24f); ball(u, FL + 0.72f, v, 0.36f, C("#3E8E41"), 0.34f); ball(u + 0.15f, FL + 0.95f, v - 0.08f, 0.22f, C("#4CAF50")) }
        }
        solid(u - 0.25f, v - 0.25f, u + 0.25f, v + 0.25f)
    }
    fun cooler(u: Float, v: Float) { box(u, FL, v, 0.32f, 1.0f, 0.32f, C("#ECEFF1"), Mt.METAL); box(u - 0.06f, FL + 0.8f, v - 0.165f, 0.04f, 0.04f, 0.03f, C("#E53935")); box(u + 0.06f, FL + 0.8f, v - 0.165f, 0.04f, 0.04f, 0.03f, C("#1E88E5")); oc(u, v, 0, 0f, FL + 1.0f, 0f, 0.14f, 0.42f, C("#90CAF9"), Mt.GLASS, 10); solid(u - 0.2f, v - 0.2f, u + 0.2f, v + 0.2f) }
    fun bin(u: Float, v: Float, c: Int = C("#546E7A")) { oc(u, v, 0, 0f, FL, 0f, 0.16f, 0.42f, c, Mt.METAL, 10, 0.18f); solid(u - 0.18f, v - 0.18f, u + 0.18f, v + 0.18f) }
    fun vending(u: Float, v: Float, dir: Int, c: Int = C("#C62828")) {
        ob(u, v, dir, 0f, FL, 0f, 0.95f, 1.85f, 0.8f, c, Mt.METAL); ob(u, v, dir, -0.12f, FL + 0.55f, -0.405f, 0.6f, 1.15f, 0.01f, C("#E3F2FD"), Mt.PLAIN, 1f, false)
        for (j in 0..4) for (i in 0..3) ob(u, v, dir, -0.36f + i * 0.16f, FL + 0.62f + j * 0.22f, -0.41f, 0.11f, 0.15f, 0.005f, C(goodsC[(i + j * 3) % 10]), Mt.PLAIN, 1f, false)
        ob(u, v, dir, 0.33f, FL + 1.0f, -0.41f, 0.16f, 0.35f, 0.01f, C("#263238")); ob(u, v, dir, -0.12f, FL + 0.15f, -0.41f, 0.6f, 0.25f, 0.01f, C("#212121"))
        os(u, v, dir, -0.48f, -0.4f, 0.48f, 0.4f)
    }
    fun coffeeMachine(u: Float, v: Float, dir: Int, y0: Float = FL + 0.92f) { ob(u, v, dir, 0f, y0, 0f, 0.32f, 0.42f, 0.36f, C("#212121"), Mt.METAL); ob(u, v, dir, 0f, y0 + 0.12f, -0.12f, 0.16f, 0.04f, 0.12f, C("#9E9E9E"), Mt.METAL); ob(u, v, dir, 0f, y0 + 0.3f, -0.185f, 0.18f, 0.06f, 0.005f, C("#4FC3F7"), Mt.PLAIN, 1f, false); mug(au(u, v, dir, 0f, -0.08f), av(u, v, dir, 0f, -0.08f), y0) }
    fun microwave(u: Float, v: Float, dir: Int, y0: Float = FL + 0.92f) { ob(u, v, dir, 0f, y0, 0f, 0.5f, 0.3f, 0.38f, C("#ECEFF1"), Mt.METAL); ob(u, v, dir, -0.06f, y0 + 0.05f, -0.195f, 0.3f, 0.2f, 0.005f, C("#212121")); ob(u, v, dir, 0.18f, y0 + 0.08f, -0.195f, 0.08f, 0.15f, 0.005f, C("#455A64")) }
    fun homeFridge(u: Float, v: Float, dir: Int, c: Int = C("#ECEFF1")) { ob(u, v, dir, 0f, FL, 0f, 0.75f, 1.8f, 0.7f, c, Mt.METAL); ob(u, v, dir, 0f, FL + 1.2f, -0.355f, 0.73f, 0.012f, 0.01f, shade(c, -30)); for (y in floatArrayOf(0.7f, 1.35f)) ob(u, v, dir, 0.3f, FL + y, -0.37f, 0.03f, 0.3f, 0.03f, C("#9E9E9E"), Mt.METAL); os(u, v, dir, -0.38f, -0.36f, 0.38f, 0.36f) }
    fun copier(u: Float, v: Float, dir: Int) { ob(u, v, dir, 0f, FL, 0f, 0.7f, 0.95f, 0.65f, C("#ECEFF1"), Mt.METAL); ob(u, v, dir, 0f, FL + 0.95f, 0.05f, 0.66f, 0.12f, 0.55f, C("#CFD8DC"), Mt.METAL); ob(u, v, dir, 0.2f, FL + 0.95f, -0.25f, 0.22f, 0.04f, 0.14f, C("#263238")); ob(u, v, dir, 0.2f, FL + 0.99f, -0.25f, 0.16f, 0.005f, 0.08f, C("#80DEEA"), Mt.PLAIN, 1f, false); for (k in 0..2) ob(u, v, dir, 0f, FL + 0.15f + k * 0.25f, -0.33f, 0.62f, 0.2f, 0.01f, C("#DADFE2")); os(u, v, dir, -0.35f, -0.33f, 0.35f, 0.33f) }
    fun ac(u: Float, v: Float, dir: Int) { ob(u, v, dir, 0f, FL + h - 0.75f, 0f, 1.0f, 0.3f, 0.22f, C("#FAFAFA")); ob(u, v, dir, 0f, FL + h - 0.72f, -0.115f, 0.9f, 0.04f, 0.01f, C("#B0BEC5")) }
    fun exitSign(u: Float, v: Float, dir: Int, y0: Float) { ob(u, v, dir, 0f, y0, 0f, 0.4f, 0.16f, 0.05f, C("#1B5E20")); ob(u, v, dir, 0f, y0 + 0.03f, -0.026f, 0.34f, 0.1f, 0.004f, C("#69F0AE"), Mt.PLAIN, 1f, false) }
    fun extinguisher(u: Float, v: Float, dir: Int) { ob(u, v, dir, 0f, FL + 1.55f, 0f, 0.3f, 0.3f, 0.01f, C("#D32F2F")); oc(au(u, v, dir, 0f, -0.1f), av(u, v, dir, 0f, -0.1f), 0, 0f, FL + 0.95f, 0f, 0.08f, 0.5f, C("#D32F2F"), Mt.METAL, 8); oc(au(u, v, dir, 0f, -0.1f), av(u, v, dir, 0f, -0.1f), 0, 0f, FL + 1.45f, 0f, 0.03f, 0.08f, C("#212121"), Mt.METAL, 6) }
    /** Carro simples (caixa com cabine, rodas, faróis e lanternas). Frente em +lz. */
    fun car(u: Float, v: Float, dir: Int, c: Int, y0: Float = FL) {
        for (a in floatArrayOf(-0.82f, 0.82f)) for (e in floatArrayOf(-1.35f, 1.35f)) { ob(u, v, dir, a, y0, e, 0.22f, 0.62f, 0.62f, C("#1A1A1A")); ob(u, v, dir, a * 1.02f, y0 + 0.16f, e, 0.2f, 0.3f, 0.3f, C("#B0BEC5"), Mt.METAL) }
        ob(u, v, dir, 0f, y0 + 0.3f, 0f, 1.76f, 0.55f, 4.2f, c, Mt.METAL); ob(u, v, dir, 0f, y0 + 0.85f, -0.25f, 1.56f, 0.5f, 2.1f, c, Mt.METAL)
        ob(u, v, dir, 0f, y0 + 0.88f, -0.25f, 1.58f, 0.4f, 1.9f, C("#2A3A48"), Mt.GLASS)
        ob(u, v, dir, 0f, y0 + 0.9f, 0.82f, 1.4f, 0.38f, 0.04f, C("#2A3A48"), Mt.GLASS)
        for (s in floatArrayOf(-0.6f, 0.6f)) { ob(u, v, dir, s, y0 + 0.6f, 2.1f, 0.35f, 0.12f, 0.02f, C("#FFF9C4"), Mt.PLAIN, 1f, false); ob(u, v, dir, s, y0 + 0.62f, -2.1f, 0.35f, 0.1f, 0.02f, C("#D50000"), Mt.PLAIN, 1f, false) }
        ob(u, v, dir, 0f, y0 + 0.3f, 2.12f, 1.7f, 0.18f, 0.06f, C("#212121")); ob(u, v, dir, 0f, y0 + 0.3f, -2.12f, 1.7f, 0.18f, 0.06f, C("#212121"))
    }
}
