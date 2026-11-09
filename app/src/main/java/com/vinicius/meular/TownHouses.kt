package com.vinicius.meular

import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Etapa 132: lotes e casas no padrão americano.
 *
 * Os lotes são recortados ao longo das ruas locais (dos dois lados), virados para a calçada, seguindo a curva.
 * Cada lote é conferido: nada dele pode cair em rua, calçada, cruzamento, outro lote ou no terreno da casa do jogador.
 * Nível do bairro (tier): 1 casa pequena, 2 média, 3 grande, 4 mansão.
 */
object TownHouses {
    private const val CURB = Town.CURB

    /** Lote: frente no ponto (fx, fz) da calçada, [tx, tz] ao longo da rua, [nx, nz] entrando no lote. */
    class Lot(val fx: Float, val fz: Float, val tx: Float, val tz: Float, val nx: Float, val nz: Float, val w: Float, val d: Float, val tier: Int, val seed: Int) {
        var forSale = false
        var price = 0
        fun wx(lx: Float, lz: Float) = fx + tx * lx + nx * lz
        fun wz(lx: Float, lz: Float) = fz + tz * lx + nz * lz
        val cx get() = wx(0f, d / 2)
        val cz get() = wz(0f, d / 2)
    }
    val lots = ArrayList<Lot>()

    // tamanho do lote por nível: frente, fundo
    private val LW = floatArrayOf(0f, 16f, 20f, 28f, 118f)
    private val LD = floatArrayOf(0f, 28f, 33f, 42f, 150f)

    fun tierOf(x: Float, z: Float): Int {
        val d = TownPlan.districtAt(x, z)
        return when (d) {
            TownPlan.MAN -> 4
            TownPlan.HOME -> 2
            TownPlan.SUB -> TownPlan.tierAt(x, z)
            else -> 0
        }
    }

    // ------------------------------------------------------------ planejamento dos lotes

    private val lotBy = HashMap<Int, ArrayList<Lot>>()
    private fun cell(x: Float, z: Float) = (Math.floor(x / 40.0).toInt() + 3000) * 8192 + (Math.floor(z / 40.0).toInt() + 3000)

    private fun corners(l: Lot): FloatArray = floatArrayOf(l.wx(-l.w / 2, 0f), l.wz(-l.w / 2, 0f), l.wx(l.w / 2, 0f), l.wz(l.w / 2, 0f), l.wx(l.w / 2, l.d), l.wz(l.w / 2, l.d), l.wx(-l.w / 2, l.d), l.wz(-l.w / 2, l.d))

    /** Separação por eixos (dois retângulos girados se sobrepõem?). */
    private fun overlap(a: FloatArray, b: FloatArray): Boolean {
        for (poly in arrayOf(a, b)) for (i in 0 until 4) {
            val j = (i + 1) % 4
            val ex = poly[j * 2] - poly[i * 2]; val ez = poly[j * 2 + 1] - poly[i * 2 + 1]
            val ax = -ez; val az = ex
            var amin = Float.MAX_VALUE; var amax = -Float.MAX_VALUE; var bmin = Float.MAX_VALUE; var bmax = -Float.MAX_VALUE
            for (k in 0 until 4) { val p = a[k * 2] * ax + a[k * 2 + 1] * az; amin = min(amin, p); amax = max(amax, p) }
            for (k in 0 until 4) { val p = b[k * 2] * ax + b[k * 2 + 1] * az; bmin = min(bmin, p); bmax = max(bmax, p) }
            if (amax <= bmin + 0.05f || bmax <= amin + 0.05f) return false
        }
        return true
    }

    private fun fits(l: Lot): Boolean {
        val c = corners(l)
        // pontos ao longo do contorno (a cada ~2,5 m) e no meio: todos fora de rua e calçada, dentro de algum quarteirão
        for (i in 0 until 4) {
            val j = (i + 1) % 4
            val L = hypot(c[j * 2] - c[i * 2], c[j * 2 + 1] - c[i * 2 + 1]); val n = max(1, (L / 2.5f).toInt())
            for (k in 0..n) {
                val x = c[i * 2] + (c[j * 2] - c[i * 2]) * k / n; val z = c[i * 2 + 1] + (c[j * 2 + 1] - c[i * 2 + 1]) * k / n
                if (Town.clearance(x, z) < 0.1f) return false
            }
        }
        if (!Town.inAnyBlock(l.cx, l.cz)) return false
        // terreno da casa do jogador (com folga)
        val home = floatArrayOf(City.lotX0 - 3f, City.lotZ0 - 3f, City.lotX1 + 3f, City.lotZ0 - 3f, City.lotX1 + 3f, City.lotZ1 + 3f, City.lotX0 - 3f, City.lotZ1 + 3f)
        if (overlap(c, home)) return false
        // outros lotes
        val minx = minOf(c[0], c[2], c[4], c[6]); val maxx = maxOf(c[0], c[2], c[4], c[6]); val minz = minOf(c[1], c[3], c[5], c[7]); val maxz = maxOf(c[1], c[3], c[5], c[7])
        for (gx in Math.floor(minx / 40.0).toInt()..Math.floor(maxx / 40.0).toInt()) for (gz in Math.floor(minz / 40.0).toInt()..Math.floor(maxz / 40.0).toInt()) {
            val lst = lotBy[(gx + 3000) * 8192 + (gz + 3000)] ?: continue
            for (o in lst) if (overlap(c, corners(o))) return false
        }
        return true
    }

    private fun add(l: Lot) {
        lots.add(l)
        val c = corners(l)
        val minx = minOf(c[0], c[2], c[4], c[6]); val maxx = maxOf(c[0], c[2], c[4], c[6]); val minz = minOf(c[1], c[3], c[5], c[7]); val maxz = maxOf(c[1], c[3], c[5], c[7])
        for (gx in Math.floor(minx / 40.0).toInt()..Math.floor(maxx / 40.0).toInt()) for (gz in Math.floor(minz / 40.0).toInt()..Math.floor(maxz / 40.0).toInt())
            lotBy.getOrPut((gx + 3000) * 8192 + (gz + 3000)) { ArrayList() }.add(l)
    }

    fun plan() {
        lots.clear(); lotBy.clear(); solids.clear(); solidBy.clear()
        var seed = 1
        for ((ei, ed) in Town.edges.withIndex()) {
            if (ed.w > 16f) continue   // casas não ficam de frente para avenida
            val p = ed.pts; val n = p.size / 2
            if (n < 3) continue
            val cum = FloatArray(n); for (i in 1 until n) cum[i] = cum[i - 1] + hypot(p[i * 2] - p[i * 2 - 2], p[i * 2 + 1] - p[i * 2 - 1])
            for (sd in intArrayOf(-1, 1)) {
                var s = 3f
                while (s < cum[n - 1] - 3f) {
                    var i = 0; while (i < n - 2 && cum[i + 1] < s) i++
                    val f = (s - cum[i]) / max(1e-4f, cum[i + 1] - cum[i])
                    val px = p[i * 2] + (p[i * 2 + 2] - p[i * 2]) * f; val pz = p[i * 2 + 1] + (p[i * 2 + 3] - p[i * 2 + 1]) * f
                    var tx = p[i * 2 + 2] - p[i * 2]; var tz = p[i * 2 + 3] - p[i * 2 + 1]; val tl = max(1e-4f, hypot(tx, tz)); tx /= tl; tz /= tl
                    // para dentro do lote = lado sd da rua (offsetEdge positivo = (-tz, tx))
                    val nx = -tz * sd; val nz = tx * sd
                    val off = ed.w / 2 + Town.SW + 0.6f
                    val fx = px + nx * off; val fz = pz + nz * off
                    val tier = tierOf(fx + nx * 15f, fz + nz * 15f)
                    if (tier == 0) { s += 6f; continue }
                    // a frente do lote corre ao longo da rua: vira-se o tangente para quem olha da rua (x para a direita)
                    val ltx = -sd * tx; val ltz = -sd * tz
                    var placed: Lot? = null
                    for (k in floatArrayOf(1f, 0.85f, 0.7f)) {
                        val w = LW[tier]; val d = LD[tier] * k
                        val l = Lot(fx + tx * w / 2 * 1f, fz + tz * w / 2 * 1f, ltx, ltz, nx, nz, w - 0.25f, d, tier, seed)
                        if (fits(l)) { placed = l; break }
                    }
                    if (placed != null) { add(placed); seed++; s += LW[tier] } else s += 2.5f
                }
            }
        }
        // à venda: alguns de cada nível
        val r = City.Rng(77)
        for (l in lots) if (r.chance(if (l.tier == 4) 0.35f else 0.12f)) { l.forSale = true; l.price = PRICE[l.tier] + r.i(5) * PRICE[l.tier] / 10 }
    }
    val PRICE = intArrayOf(0, 180000, 320000, 650000, 2400000)

    // ------------------------------------------------------------ colisão (retângulos girados)

    class Obb(val cx: Float, val cz: Float, val hx: Float, val hz: Float, val tx: Float, val tz: Float)
    private val solids = ArrayList<Obb>()
    private val solidBy = HashMap<Int, ArrayList<Obb>>()

    fun solid(l: Lot, x0: Float, z0: Float, x1: Float, z1: Float) {
        val cx = l.wx((x0 + x1) / 2, (z0 + z1) / 2); val cz = l.wz((x0 + x1) / 2, (z0 + z1) / 2)
        val o = Obb(cx, cz, abs(x1 - x0) / 2, abs(z1 - z0) / 2, l.tx, l.tz)
        solids.add(o)
        val r = sqrt(o.hx * o.hx + o.hz * o.hz)
        for (gx in Math.floor((cx - r) / 40.0).toInt()..Math.floor((cx + r) / 40.0).toInt()) for (gz in Math.floor((cz - r) / 40.0).toInt()..Math.floor((cz + r) / 40.0).toInt())
            solidBy.getOrPut((gx + 3000) * 8192 + (gz + 3000)) { ArrayList() }.add(o)
    }

    fun blocked(x: Float, z: Float): Boolean {
        val l = solidBy[cell(x, z)] ?: return false
        for (o in l) {
            val dx = x - o.cx; val dz = z - o.cz
            val a = dx * o.tx + dz * o.tz; val b = -dx * o.tz + dz * o.tx
            if (abs(a) < o.hx && abs(b) < o.hz) return true
        }
        return false
    }

    // ------------------------------------------------------------ desenho no espaço do lote

    /** Pincel no espaço do lote: x ao longo da frente (direita de quem olha da rua), z para o fundo, y para cima. */
    class Pen(val b: MB, val l: Lot) {
        fun box(lx: Float, y: Float, lz: Float, sx: Float, sy: Float, sz: Float, c: Int) =
            TownGeo.obox(b, l.wx(lx, lz), y + sy / 2, l.wz(lx, lz), sx, sy, sz, l.tx, l.tz, c)
        /** quadrilátero (pontos no espaço do lote), virado para o lado de [hx, hy, hz] (direção no espaço do lote) */
        fun quad(p: FloatArray, hx: Float, hy: Float, hz: Float, c: Int) {
            val w = FloatArray(12)
            for (k in 0 until 4) { w[k * 3] = l.wx(p[k * 3], p[k * 3 + 2]); w[k * 3 + 1] = p[k * 3 + 1]; w[k * 3 + 2] = l.wz(p[k * 3], p[k * 3 + 2]) }
            val hwx = l.tx * hx + l.nx * hz; val hwz = l.tz * hx + l.nz * hz
            val ux = w[3] - w[0]; val uy = w[4] - w[1]; val uz = w[5] - w[2]; val vx = w[9] - w[0]; val vy = w[10] - w[1]; val vz = w[11] - w[2]
            val nx = uy * vz - uz * vy; val ny = uz * vx - ux * vz; val nz = ux * vy - uy * vx
            if (nx * hwx + ny * hy + nz * hwz < 0) CityGeo.q(b, floatArrayOf(w[9], w[10], w[11], w[6], w[7], w[8], w[3], w[4], w[5], w[0], w[1], w[2]), c)
            else CityGeo.q(b, w, c)
        }
        fun tri(p: FloatArray, hx: Float, hy: Float, hz: Float, c: Int) {
            val w = FloatArray(9)
            for (k in 0 until 3) { w[k * 3] = l.wx(p[k * 3], p[k * 3 + 2]); w[k * 3 + 1] = p[k * 3 + 1]; w[k * 3 + 2] = l.wz(p[k * 3], p[k * 3 + 2]) }
            val hwx = l.tx * hx + l.nx * hz; val hwz = l.tz * hx + l.nz * hz
            val ux = w[3] - w[0]; val uy = w[4] - w[1]; val uz = w[5] - w[2]; val vx = w[6] - w[0]; val vy = w[7] - w[1]; val vz = w[8] - w[2]
            val nx = uy * vz - uz * vy; val ny = uz * vx - ux * vz; val nz = ux * vy - uy * vx
            val o = if (nx * hwx + ny * hy + nz * hwz < 0) floatArrayOf(w[0], w[1], w[2], w[6], w[7], w[8], w[3], w[4], w[5]) else w
            val l2 = max(1e-5f, sqrt(nx * nx + ny * ny + nz * nz)); val sg = if (nx * hwx + ny * hy + nz * hwz < 0) -1f else 1f
            for (k in 0 until 3) b.v(o[k * 3], o[k * 3 + 1], o[k * 3 + 2], nx / l2 * sg, ny / l2 * sg, nz / l2 * sg, c, o[k * 3] + o[k * 3 + 2], o[k * 3 + 1])
        }
        /** piso plano (retângulo no espaço do lote) na altura y */
        fun flat(x0: Float, z0: Float, x1: Float, z1: Float, y: Float, c: Int) = quad(floatArrayOf(x0, y, z0, x1, y, z0, x1, y, z1, x0, y, z1), 0f, 1f, 0f, c)
        fun cyl(lx: Float, y: Float, lz: Float, r: Float, h: Float, c: Int, seg: Int = 10) = b.cyl(l.wx(lx, lz), y, l.wz(lx, lz), r, r, h, c, true, seg)
    }

    // paletas
    private val SIDING = arrayOf("#F4F1EA", "#E9E2D0", "#C9D6DF", "#D7DDD0", "#EFE3C2", "#B9C4C9", "#E7D9CF", "#CBD8C3", "#F2E8DA", "#A7B4BE", "#DCCBB5", "#EDEDED")
    private val ROOFC = arrayOf("#4A4F55", "#5B4A42", "#3E4348", "#6B5D53", "#2F3337", "#59606A", "#7A4E3A")
    private val DOORC = arrayOf("#8E1B1B", "#1F3A5F", "#222222", "#5A3A22", "#2E5E3A", "#F2F2F2", "#6A1B2E")
    private val TRIM = C("#FBFBF8")
    private val CONC = C("#D8D5CE")
    private val GLASSC = C("#4E6A7E")

    // ============================================================ casas (níveis 1 a 3)

    // estilos
    private const val COLONIAL = 0; private const val RANCH = 1; private const val CRAFTSMAN = 2; private const val MODERN = 3; private const val SPANISH = 4; private const val CAPE = 5
    // tipos de fechamento do terreno
    private const val OPEN = 0; private const val PICKET = 1; private const val WALL = 2; private const val IRON = 3; private const val HEDGE = 4; private const val MURETA = 5

    private val BRICK = arrayOf("#9C5A3C", "#A86B4F", "#8A4B36", "#B07A5E", "#7E4A3A", "#C08A6A")
    private val STUCCO = arrayOf("#F1E6D2", "#EADBC2", "#F4EDE1", "#E8D3B9", "#F6F1E7", "#E2CDB0")
    private val MODC = arrayOf("#F4F4F2", "#E6E6E3", "#3B3F44", "#D9D6CF", "#ECECEA", "#55595F")

    /** Desenha o lote [l]: casa, garagem, entrada de carro, caixa de correio, muro/cerca, jardim. [far] = versão simples. */
    fun draw(g: CityGeo.Gen, l: Lot, near: Boolean, far: Boolean) {
        if (l.tier == 4) { mansion(g, l, near, far); return }
        val r = City.Rng(l.seed * 7919 + 13)
        val t = l.tier
        val W = l.w; val D = l.d; val y0 = CURB
        val style = when (t) { 1 -> intArrayOf(RANCH, CRAFTSMAN, CAPE, SPANISH, RANCH, MODERN)[r.i(6)]; 2 -> r.i(6); else -> intArrayOf(COLONIAL, MODERN, SPANISH, CRAFTSMAN, COLONIAL, MODERN)[r.i(6)] }
        // cores e materiais do estilo
        val wallC: Int; val wallM: Int; val roofC: Int; val trim: Int
        when (style) {
            RANCH -> { wallC = C(BRICK[r.i(BRICK.size)]); wallM = Mt.STONE; roofC = C(ROOFC[r.i(ROOFC.size)]); trim = C("#F2EEE6") }
            SPANISH -> { wallC = C(STUCCO[r.i(STUCCO.size)]); wallM = Mt.PLASTER; roofC = C(arrayOf("#B5523B", "#A84A33", "#C0643F", "#9E4530")[r.i(4)]); trim = C("#8A5A3C") }
            MODERN -> { wallC = C(MODC[r.i(MODC.size)]); wallM = Mt.PLASTER; roofC = C("#5A5E63"); trim = C("#2B2E31") }
            CRAFTSMAN -> { wallC = C(arrayOf("#8FA28A", "#A9A08A", "#7F95A3", "#B9A88A", "#9AA49A", "#C2B49A")[r.i(6)]); wallM = Mt.SIDING; roofC = C(ROOFC[r.i(ROOFC.size)]); trim = C("#F4F1E8") }
            else -> { wallC = C(SIDING[r.i(SIDING.size)]); wallM = Mt.SIDING; roofC = C(ROOFC[r.i(ROOFC.size)]); trim = TRIM }
        }
        val door = C(DOORC[r.i(DOORC.size)])
        val floors = when (style) { RANCH, SPANISH -> if (t == 3 && r.chance(0.4f)) 2 else 1; CAPE -> 1; MODERN -> if (t == 1) 1 else 2; else -> if (t == 1) 1 else 2 }
        val wallH = if (style == MODERN) 3.1f else 2.9f
        val H = wallH * floors
        // garagem
        val gw = when (t) { 1 -> if (r.chance(0.3f)) 0f else 3.6f; 2 -> 6.2f; else -> 8.8f }
        val frontGarage = gw > 0f && (style == RANCH || style == MODERN) && r.chance(0.5f)   // garagem avançada na frente
        val gSide = if (r.chance(0.5f)) 1f else -1f
        // largura e fundo da casa (o resto do lote é jardim)
        val sideGap = when (t) { 1 -> 2.2f; 2 -> 2.8f; else -> 3.5f }
        val hw = (W - 2 * sideGap - gw).coerceIn(7f, if (style == RANCH) 20f else 17f)
        val hd = when (style) { RANCH -> 9f; MODERN -> 10.5f; else -> 9f + t * 0.8f }.coerceAtMost(D * 0.38f)
        val set = when (t) { 1 -> 6f; 2 -> 7.5f; else -> 9.5f } + r.r(-0.6f, 0.8f)
        val total = hw + gw
        val hx0 = -total / 2 + (if (gSide < 0) gw else 0f)
        val gx0 = if (gSide < 0) -total / 2 else hx0 + hw
        val gz0 = if (frontGarage) set - 3.5f else set + 0.6f
        val gd = 7f
        // ala em L (avança na frente, do lado oposto à garagem)
        val ell = (style == COLONIAL || style == CRAFTSMAN || style == SPANISH || style == CAPE) && t >= 2 && r.chance(0.55f)
        val ew = hw * 0.42f; val ed = 3.2f
        val ex0 = if (gSide > 0) hx0 else hx0 + hw - ew
        val doorX = if (ell) (if (gSide > 0) hx0 + ew + (hw - ew) * 0.45f else hx0 + (hw - ew) * 0.55f) else hx0 + hw * (if (gSide > 0) 0.4f else 0.6f)
        val dx0 = gx0 + 0.2f; val dx1 = gx0 + gw - 0.2f
        // ---------------- longe
        if (far) {
            val f = Pen(g.f, l); g.f.m(Mt.PLAIN)
            f.box(hx0 + hw / 2, y0, set + hd / 2, hw, H, hd, wallC)
            if (gw > 0f) f.box(gx0 + gw / 2, y0, gz0 + gd / 2, gw, 2.7f, gd, wallC)
            if (style == MODERN) f.box(hx0 + hw / 2, y0 + H, set + hd / 2, hw + 0.4f, 0.3f, hd + 0.4f, roofC)
            else hip(f, hx0, hx0 + hw, set, set + hd, y0 + H, hd * 0.3f, roofC, 0.4f)
        }
        if (g.reg) {
            solid(l, hx0, set, hx0 + hw, set + hd)
            if (gw > 0f) solid(l, gx0, gz0, gx0 + gw, gz0 + gd)
            if (ell) solid(l, ex0, set - ed, ex0 + ew, set)
        }
        // ---------------- muro / cerca (antes do return: colisão sempre)
        val enc = when (style) { SPANISH -> intArrayOf(WALL, WALL, IRON, MURETA)[r.i(4)]; MODERN -> intArrayOf(WALL, IRON, OPEN, HEDGE)[r.i(4)]; else -> intArrayOf(OPEN, OPEN, PICKET, PICKET, HEDGE, MURETA, IRON, WALL)[r.i(8)] }
        val encC = when (enc) { WALL -> if (r.chance(0.5f)) wallC else C(arrayOf("#E9E4DA", "#D8D2C6", "#BDB6A8", "#F2EEE6")[r.i(4)]); PICKET -> C("#FAFAF7"); else -> C(arrayOf("#A88A6A", "#8C7058", "#E9E4DA", "#6E6E6E")[r.i(4)]) }
        val walkX0 = doorX - 0.75f; val walkX1 = doorX + 0.75f
        if (!near) { if (g.reg) enclosure(null, l, enc, encC, W, D, set, hd, hx0, hw, dx0, dx1, walkX0, walkX1, gw > 0f, g); return }
        val b = g.b; val p = Pen(b, l)
        enclosure(p, l, enc, encC, W, D, set, hd, hx0, hw, dx0, dx1, walkX0, walkX1, gw > 0f, g)
        // ---------------- casa
        // fundação
        b.m(Mt.STONE, 1f); p.box(hx0 + hw / 2, y0, set + hd / 2, hw + 0.2f, 0.45f, hd + 0.2f, C(if (style == SPANISH) "#B9A58A" else "#9C9890"))
        b.m(wallM, if (wallM == Mt.STONE) 0.45f else 0.8f)
        p.box(hx0 + hw / 2, y0 + 0.45f, set + hd / 2, hw, H - 0.45f, hd, wallC)
        if (ell) { b.m(Mt.STONE, 1f); p.box(ex0 + ew / 2, y0, set - ed / 2, ew + 0.2f, 0.45f, ed + 0.1f, C("#9C9890")); b.m(wallM, if (wallM == Mt.STONE) 0.45f else 0.8f); p.box(ex0 + ew / 2, y0 + 0.45f, set - ed / 2 - 0.02f, ew, H - 0.45f, ed + 0.04f, wallC) }
        // detalhes de material: tijolo aparente com faixa de reboco no rancho; painel de madeira no moderno; pedra na base do craftsman
        when (style) {
            MODERN -> { b.m(Mt.WOOD, 0.5f); p.box(hx0 + hw * (if (gSide > 0) 0.18f else 0.82f), y0 + 0.45f, set - 0.06f, hw * 0.3f, H - 0.5f, 0.1f, C("#8A5E3C")) }
            CRAFTSMAN -> { b.m(Mt.STONE, 0.5f); p.box(hx0 + hw / 2, y0 + 0.45f, set + hd / 2, hw + 0.12f, 0.9f, hd + 0.12f, C("#8E8578")) }
            else -> {}
        }
        if (floors > 1 && style != MODERN) { b.m(Mt.PLAIN); p.box(hx0 + hw / 2, y0 + wallH - 0.1f, set + hd / 2, hw + 0.08f, 0.18f, hd + 0.08f, trim) }
        // telhado
        b.m(Mt.ROOF, 0.6f)
        when (style) {
            MODERN -> { b.m(Mt.PLAIN); p.box(hx0 + hw / 2, y0 + H, set + hd / 2, hw + 0.5f, 0.35f, hd + 0.5f, C("#4A4E53")); p.box(hx0 + hw / 2, y0 + H + 0.35f, set + hd / 2, hw + 0.5f, 0.06f, hd + 0.5f, C("#2E3135")) }
            RANCH, SPANISH -> hip(p, hx0, hx0 + hw, set, set + hd, y0 + H, hd * (if (style == SPANISH) 0.22f else 0.26f), roofC, 0.6f)
            CAPE -> { gable(p, hx0, hx0 + hw, set, set + hd, y0 + H, hd * 0.55f, roofC, 0.35f, wallC); for (k in 0..1) dormer(p, hx0 + hw * (0.3f + k * 0.4f), y0 + H + 0.3f, set + hd * 0.2f, wallC, roofC) }
            else -> gable(p, hx0, hx0 + hw, set, set + hd, y0 + H, hd * 0.34f, roofC, 0.5f, wallC)
        }
        if (ell) {
            b.m(Mt.ROOF, 0.6f)
            if (style == SPANISH) hip(p, ex0, ex0 + ew, set - ed - 0.3f, set + 1f, y0 + H, 1.4f, roofC, 0.4f)
            else gableZ(p, ex0, ex0 + ew, set - ed, set + 1.5f, y0 + H, ew * 0.4f, roofC, 0.4f, wallC)
        }
        // garagem
        if (gw > 0f) {
            b.m(wallM, if (wallM == Mt.STONE) 0.45f else 0.8f); p.box(gx0 + gw / 2, y0, gz0 + gd / 2, gw, 2.75f, gd, wallC)
            b.m(Mt.ROOF, 0.6f)
            if (style == MODERN) { b.m(Mt.PLAIN); p.box(gx0 + gw / 2, y0 + 2.75f, gz0 + gd / 2, gw + 0.4f, 0.3f, gd + 0.4f, C("#4A4E53")) }
            else if (frontGarage) gableZ(p, gx0, gx0 + gw, gz0, gz0 + gd, y0 + 2.75f, gw * 0.3f, roofC, 0.35f, wallC)
            else gable(p, gx0, gx0 + gw, gz0, gz0 + gd, y0 + 2.75f, 1.6f, roofC, 0.35f, wallC)
            b.m(Mt.PLAIN)
            val nDoors = if (t == 1) 1 else if (r.chance(0.5f)) 1 else (gw / 3.1f).toInt().coerceAtLeast(1)
            val dw = (gw - 0.6f) / nDoors
            val gdc = if (style == MODERN) C("#3B3F44") else if (style == SPANISH || r.chance(0.3f)) C("#6B4A32") else C("#F3F3F0")
            for (k in 0 until nDoors) {
                val cx = gx0 + 0.3f + dw * (k + 0.5f)
                p.box(cx, y0 + 0.02f, gz0 - 0.04f, dw - 0.4f, 2.25f, 0.06f, gdc)
                for (q in 1..3) p.box(cx, y0 + 0.02f + q * 0.56f, gz0 - 0.08f, dw - 0.5f, 0.04f, 0.04f, shade(gdc, -18))
                if (style != MODERN && t >= 2) p.box(cx, y0 + 1.9f, gz0 - 0.09f, dw - 0.9f, 0.22f, 0.03f, GLASSC)
            }
            // carro na entrada (às vezes)
            if (r.chance(0.45f)) parkedCar(g, l, gx0 + gw / 2 + (if (gw > 6f) -1.5f else 0f), gz0 - 3.4f, r)
        } else {
            // sem garagem: carro na grama/entrada lateral
            if (r.chance(0.6f)) parkedCar(g, l, if (gSide > 0) hx0 + hw + sideGap * 0.5f else hx0 - sideGap * 0.5f, set + 1.5f, r)
        }
        // entrada de carro (concreto) da garagem até o meio-fio, passando pela calçada
        if (gw > 0f) { b.m(Mt.PAVER, 0.5f); p.flat(dx0, -Town.SW - 0.6f, dx1, gz0, y0 + 0.018f, CONC) }
        // calçadinha até a porta (em curva nas casas maiores = degraus de pedra)
        b.m(Mt.PAVER, 0.5f)
        if (t >= 2 && r.chance(0.5f)) { var z = 0.8f; while (z < (if (ell) set else set) - 0.8f) { p.flat(doorX - 0.45f, z, doorX + 0.45f, z + 0.6f, y0 + 0.016f, C("#BDB6AA")); z += 0.95f } }
        else p.flat(walkX0 + 0.1f, -0.6f, walkX1 - 0.1f, set - (if (t >= 2) 2.2f else 0.7f), y0 + 0.016f, C("#CFCAC0"))
        // porta e varanda
        b.m(Mt.PLAIN)
        p.box(doorX, y0 + 0.45f, set - 0.05f, if (style == MODERN) 1.3f else 1.05f, if (style == MODERN) 2.5f else 2.2f, 0.1f, door)
        p.box(doorX, y0 + 0.45f, set - 0.08f, 1.45f, 2.4f, 0.06f, trim)
        p.box(doorX + 0.38f, y0 + 1.5f, set - 0.12f, 0.06f, 0.06f, 0.05f, C("#C9A227"))
        when {
            style == CRAFTSMAN || (t >= 2 && style == COLONIAL) -> porch(p, b, if (ell) (if (gSide > 0) hx0 + ew + (hw - ew) / 2 else hx0 + (hw - ew) / 2) else hx0 + hw / 2, set, if (ell) (hw - ew) * 0.9f else hw * 0.75f, 2.4f, y0, roofC, trim, style == CRAFTSMAN, g, l)
            style == SPANISH -> { b.m(Mt.PLASTER, 0.8f); for (sg in floatArrayOf(-1f, 1f)) p.box(doorX + sg * 1.4f, y0 + 0.45f, set - 1.4f, 0.5f, 2.6f, 0.5f, wallC); p.box(doorX, y0 + 2.85f, set - 1.4f, 3.3f, 0.5f, 0.5f, wallC); b.m(Mt.ROOF, 0.6f); p.box(doorX, y0 + 3.35f, set - 0.8f, 3.6f, 0.14f, 1.8f, roofC); if (g.reg) for (sg in floatArrayOf(-1f, 1f)) solid(l, doorX + sg * 1.4f - 0.25f, set - 1.65f, doorX + sg * 1.4f + 0.25f, set - 1.15f) }
            style == MODERN -> { b.m(Mt.PLAIN); p.box(doorX, y0 + 2.9f, set - 1.2f, 3.4f, 0.16f, 2.4f, C("#2E3135")) }
            else -> { b.m(Mt.STONE, 1f); p.box(doorX, y0, set - 0.7f, 1.8f, 0.3f, 1.4f, C("#B8B3AA")) }
        }
        // janelas
        b.m(Mt.PLAIN)
        val shut = C(arrayOf("#2F3E4E", "#4A3A2E", "#2E4A3A", "#1E1E1E", "#7A2E2E", "#F2F2F2")[r.i(6)])
        val shutters = style == COLONIAL || style == CAPE || (style == CRAFTSMAN && r.chance(0.3f))
        for (fl in 0 until floors) {
            val wy = y0 + 0.45f + 0.95f + fl * wallH
            if (style == MODERN) {
                // faixas de vidro do chão ao teto
                val n = max(2, (hw / 3.6f).toInt())
                for (k in 0 until n) { val wx = hx0 + hw * (k + 0.5f) / n; if (fl == 0 && abs(wx - doorX) < 1.6f) continue; p.box(wx, y0 + 0.55f + fl * wallH, set - 0.03f, hw / n - 0.6f, wallH - 0.5f, 0.06f, C("#2E3135")); p.box(wx, y0 + 0.62f + fl * wallH, set - 0.07f, hw / n - 0.8f, wallH - 0.64f, 0.02f, C("#5C7A8E")) }
                p.box(hx0 + hw / 2, y0 + 0.5f + fl * wallH, set + hd + 0.04f, hw * 0.7f, wallH - 0.6f, 0.06f, C("#5C7A8E"))
                continue
            }
            val n = max(2, (hw / 3.2f).toInt())
            for (k in 0 until n) {
                val wx = hx0 + hw * (k + 0.5f) / n
                if (fl == 0 && abs(wx - doorX) < 1.4f) continue
                if (ell && fl == 0 && wx > ex0 - 0.8f && wx < ex0 + ew + 0.8f) continue
                window(p, wx, wy, set, -1f, shut, shutters, trim)
            }
            if (ell) window(p, ex0 + ew / 2, wy, set - ed, -1f, shut, shutters, trim)
            for (k in 0 until max(2, (hw / 4f).toInt())) window(p, hx0 + hw * (k + 0.5f) / max(2, (hw / 4f).toInt()), wy, set + hd, 1f, shut, false, trim)
            for (sx in floatArrayOf(hx0, hx0 + hw)) {
                if (gw > 0f && ((sx == hx0 + hw && gSide > 0) || (sx == hx0 && gSide < 0)) && !frontGarage) continue
                for (k in 0..1) windowSide(p, sx, wy, set + hd * (0.3f + k * 0.4f), if (sx == hx0) -1f else 1f, trim)
            }
        }
        // chaminé
        if (style != MODERN && style != SPANISH && r.chance(0.5f)) { b.m(Mt.STONE, 0.5f); p.box(hx0 + hw * (if (gSide > 0) 0.12f else 0.88f), y0 + H - 0.5f, set + hd * 0.6f, 1.0f, hd * 0.34f + 1.9f, 1.0f, C(arrayOf("#8D6E63", "#9C5A3C", "#7A7A7A")[r.i(3)])) }
        // caixa de correio junto do meio-fio
        val mx = if (gw > 0f) (if (gSide > 0) dx0 - 0.8f else dx1 + 0.8f) else walkX1 + 0.9f
        b.m(Mt.WOOD, 0.6f); p.box(mx, y0, -Town.SW - 0.25f, 0.1f, 1.05f, 0.1f, C("#5A4636"))
        b.m(Mt.METAL, 1f); p.box(mx, y0 + 1.05f, -Town.SW - 0.25f, 0.24f, 0.24f, 0.48f, C(arrayOf("#222222", "#F2F2F2", "#1F3A5F", "#8E1B1B")[r.i(4)]))
        if (g.reg) solid(l, mx - 0.15f, -Town.SW - 0.5f, mx + 0.15f, -Town.SW)
        // jardim: canteiro na frente da casa, árvores, arbustos, flores
        b.m(Mt.GRASS, 0.4f); p.flat(hx0 + 0.3f, set - 1.4f, hx0 + hw - 0.3f, set - 0.2f, y0 + 0.012f, C("#6B4E36"))
        for (k in 0 until (3 + t)) { val bx = hx0 + 0.7f + (hw - 1.4f) * k / (2 + t); if (abs(bx - doorX) > 1.1f && !(ell && bx > ex0 - 0.5f && bx < ex0 + ew + 0.5f)) CityGeo.bush(g, l.wx(bx, set - 0.8f), l.wz(bx, set - 0.8f), r.r(0.45f, 0.65f)) }
        val treeX = if (gSide > 0) -W / 2 + 3f else W / 2 - 3f
        if (r.chance(0.85f)) { if (style == SPANISH && r.chance(0.6f)) CityGeo.palm(g, l.wx(treeX, set * 0.45f), l.wz(treeX, set * 0.45f), 0.9f) else CityGeo.tree(g, l.wx(treeX, set * 0.45f), l.wz(treeX, set * 0.45f), r.r(0.7f, 1.0f)); if (g.reg) solid(l, treeX - 0.25f, set * 0.45f - 0.25f, treeX + 0.25f, set * 0.45f + 0.25f) }
        if (D - set - hd > 10f) for (k in 0 until 1 + r.i(2)) { val tx = r.r(-W / 2 + 2.5f, W / 2 - 2.5f); val tz = r.r(set + hd + 3f, D - 3f); CityGeo.tree(g, l.wx(tx, tz), l.wz(tx, tz), r.r(0.8f, 1.1f)) }
        // quintal: deck/pátio e churrasqueira, piscina nas maiores
        val back = set + hd
        b.m(Mt.WOOD, 0.6f); p.box(hx0 + hw / 2, y0, back + 1.6f, min(hw, 8f), 0.25f, 3.2f, C("#A07E5C"))
        if (t >= 2 && D - back > 15f) {
            val pz0 = back + 5f; val pz1 = min(D - 3.5f, pz0 + (if (t == 3) 9f else 6.5f)); val pxw = min(W - 7f, if (t == 3) 10f else 6.5f)
            if (pz1 > pz0 + 4f && (t == 3 || r.chance(0.35f))) {
                b.m(Mt.TILE, 0.5f); p.flat(-pxw / 2 - 1.2f, pz0 - 1.2f, pxw / 2 + 1.2f, pz1 + 1.2f, y0 + 0.02f, C("#E8E2D6"))
                b.m(Mt.PLAIN); p.flat(-pxw / 2, pz0, pxw / 2, pz1, y0 + 0.035f, C("#3FA9D6"))
            } else { b.m(Mt.PLAIN); p.box(r.r(-W / 4, W / 4), y0, back + 8f, 1.6f, 1.6f, 1.6f, C("#E7D9B8")); p.box(0f, y0, back + 11f, 2.2f, 0.75f, 0.9f, C("#7B5A3E")) }
        }
        // placa "à venda"
        if (l.forSale) {
            val sx = if (gSide > 0) -W / 2 + 1.5f else W / 2 - 1.5f
            b.m(Mt.WOOD, 0.6f); p.box(sx, y0, 1.6f, 0.08f, 1.3f, 0.08f, C("#F2F2F2"))
            b.m(Mt.PLAIN); p.box(sx, y0 + 0.75f, 1.6f, 0.9f, 0.55f, 0.04f, C("#C62828"))
        }
    }

    /** Fechamento do terreno inteiro (frente, lados até o fundo, fundo) com vãos e portões na entrada de carro e na calçadinha. */
    private fun enclosure(p: Pen?, l: Lot, kind: Int, c: Int, W: Float, D: Float, set: Float, hd: Float, hx0: Float, hw: Float, dx0: Float, dx1: Float, w0: Float, w1: Float, drive: Boolean, g: CityGeo.Gen) {
        val fz = 0.35f; val xl = -W / 2 + 0.12f; val xr = W / 2 - 0.12f; val bz = D - 0.15f
        if (kind == OPEN) {
            // frente aberta (gramado americano); quintal fechado com cerca de madeira alta e portão do lado da casa
            val z0 = set + hd * 0.35f
            run(p, l, PICKET + 100, c, xl, z0, xl, bz, g); run(p, l, PICKET + 100, c, xr, z0, xr, bz, g); run(p, l, PICKET + 100, c, xl, bz, xr, bz, g)
            run(p, l, PICKET + 100, c, xl, z0, hx0 - 0.05f, z0, g, gate = true); run(p, l, PICKET + 100, c, hx0 + hw + 0.05f, z0, xr, z0, g, gate = true)
            return
        }
        // frente com vãos
        val gaps = ArrayList<FloatArray>()
        if (drive) gaps.add(floatArrayOf(dx0 - 0.3f, dx1 + 0.3f))
        gaps.add(floatArrayOf(w0 - 0.15f, w1 + 0.15f))
        gaps.sortBy { it[0] }
        // junta vãos que se tocam
        val merged = ArrayList<FloatArray>()
        for (q in gaps) { val last = merged.lastOrNull(); if (last != null && q[0] <= last[1] + 1.2f) last[1] = max(last[1], q[1]) else merged.add(floatArrayOf(q[0], q[1])) }
        var x = xl
        for (q in merged) { if (q[0] - x > 0.4f) run(p, l, kind, c, x, fz, q[0], fz, g, endPost = true); x = q[1] }
        if (xr - x > 0.4f) run(p, l, kind, c, x, fz, xr, fz, g, endPost = true)
        // portões: o da calçadinha (folha aberta para dentro) e o da garagem (de correr, aberto atrás do muro)
        if (p != null && (kind == WALL || kind == IRON || kind == PICKET)) {
            val gc = if (kind == PICKET) C("#FAFAF7") else C("#2A2A2A")
            p.b.m(Mt.METAL, 1f)
            p.box(w0 - 0.1f, CURB, fz + 0.55f, 0.05f, if (kind == PICKET) 1.0f else 1.7f, 1.1f, gc)
            if (drive && kind != PICKET) {
                val len = dx1 - dx0 + 0.6f
                val xs = if (dx0 - len - 0.3f > xl) dx0 - 0.3f - len / 2 else dx1 + 0.3f + len / 2
                p.box(xs, CURB + 0.05f, fz + 0.35f, len, 1.75f, 0.05f, gc)
                var k = xs - len / 2 + 0.12f; while (k < xs + len / 2) { p.box(k, CURB + 0.05f, fz + 0.36f, 0.03f, 1.75f, 0.06f, shade(gc, 20)); k += 0.14f }
            }
        }
        // lados e fundo
        run(p, l, if (kind == PICKET) PICKET + 100 else kind, c, xl, fz, xl, bz, g)
        run(p, l, if (kind == PICKET) PICKET + 100 else kind, c, xr, fz, xr, bz, g)
        run(p, l, if (kind == PICKET) PICKET + 100 else kind, c, xl, bz, xr, bz, g)
    }

    /** Trecho reto de muro/cerca no espaço do lote (sempre ao longo de x ou de z). kind+100 = cerca de madeira alta. */
    private fun run(p: Pen?, l: Lot, kind: Int, c: Int, x0: Float, z0: Float, x1: Float, z1: Float, g: CityGeo.Gen, endPost: Boolean = false, gate: Boolean = false) {
        val L = hypot(x1 - x0, z1 - z0); if (L < 0.3f) return
        val alongX = abs(x1 - x0) >= abs(z1 - z0)
        val cx = (x0 + x1) / 2; val cz = (z0 + z1) / 2
        fun seg(y: Float, h: Float, th: Float, col: Int) { if (alongX) p!!.box(cx, y, cz, L, h, th, col) else p!!.box(cx, y, cz, th, h, L, col) }
        fun posts(step: Float, w: Float, h: Float, col: Int, y: Float = CURB) { val n = max(1, (L / step).toInt()); for (k in 0..n) { val t = k / n.toFloat(); p!!.box(x0 + (x1 - x0) * t, y, z0 + (z1 - z0) * t, w, h, w, col) } }
        if (g.reg) { val th = 0.12f; if (alongX) solid(l, min(x0, x1), cz - th, max(x0, x1), cz + th) else solid(l, cx - th, min(z0, z1), cx + th, max(z0, z1)) }
        if (p == null) return
        val b = p.b
        when (kind) {
            WALL -> { b.m(Mt.PLASTER, 0.8f); seg(CURB, 1.9f, 0.2f, c); b.m(Mt.STONE, 1f); seg(CURB + 1.9f, 0.08f, 0.3f, shade(c, -25)); posts(3.2f, 0.36f, 2.05f, shade(c, -8)) }
            IRON -> { b.m(Mt.STONE, 1f); seg(CURB, 0.55f, 0.28f, C("#BDB6A8")); b.m(Mt.METAL, 1f); seg(CURB + 1.85f, 0.05f, 0.05f, C("#222222")); seg(CURB + 0.7f, 0.05f, 0.05f, C("#222222"))
                val n = (L / 0.15f).toInt(); for (k in 0..n) { val t = k / max(1f, n.toFloat()); p.box(x0 + (x1 - x0) * t, CURB + 0.55f, z0 + (z1 - z0) * t, 0.03f, 1.4f, 0.03f, C("#222222")) }
                b.m(Mt.STONE, 1f); posts(3f, 0.42f, 2.0f, C("#CFC6B4")) }
            PICKET -> { b.m(Mt.WOOD, 0.6f); seg(CURB + 0.3f, 0.07f, 0.05f, c); seg(CURB + 0.72f, 0.07f, 0.05f, c)
                val n = (L / 0.16f).toInt(); for (k in 0..n) { val t = k / max(1f, n.toFloat()); p.box(x0 + (x1 - x0) * t, CURB, z0 + (z1 - z0) * t, 0.08f, 1.0f, 0.03f, c) }
                posts(2.4f, 0.12f, 1.1f, c) }
            HEDGE -> { b.m(Mt.GRASS, 0.5f); seg(CURB, 1.3f, 0.7f, C(arrayOf("#4E7A3A", "#5B8A44", "#3F6E33")[(l.seed) % 3])) }
            MURETA -> { b.m(Mt.STONE, 0.6f); seg(CURB, 0.75f, 0.35f, C("#A39C8E")); b.m(Mt.STONE, 1f); seg(CURB + 0.75f, 0.06f, 0.45f, C("#CFC8BA")) }
            else -> { // cerca de madeira alta (quintal)
                val wc = if (kind == PICKET + 100 && c == C("#FAFAF7")) C("#EFEBE3") else c
                b.m(Mt.WOOD, 0.6f); seg(CURB, 1.8f, 0.06f, wc); posts(2.4f, 0.12f, 1.9f, shade(wc, 15))
                if (gate) { val gx = if (alongX) x1 - 0.6f else cx; val gz = if (alongX) cz else z1 - 0.6f; p.box(gx, CURB + 0.05f, gz, if (alongX) 1.0f else 0.08f, 1.75f, if (alongX) 0.08f else 1.0f, shade(wc, -15)) }
            }
        }
    }

    /** Varanda coberta com colunas (craftsman: colunas grossas em base de pedra). */
    private fun porch(p: Pen, b: MB, cx: Float, set: Float, pw: Float, pd: Float, y0: Float, roofC: Int, trim: Int, craft: Boolean, g: CityGeo.Gen, l: Lot) {
        b.m(Mt.WOOD, 0.6f); p.box(cx, y0, set - pd / 2, pw, 0.45f, pd, C("#B9B2A6"))
        val n = max(2, (pw / 3f).toInt() + 1)
        for (k in 0 until n) {
            val x = cx - pw / 2 + 0.25f + (pw - 0.5f) * k / (n - 1)
            if (craft) { b.m(Mt.STONE, 0.5f); p.box(x, y0 + 0.45f, set - pd + 0.25f, 0.45f, 0.9f, 0.45f, C("#8E8578")); b.m(Mt.PLAIN); p.box(x, y0 + 1.35f, set - pd + 0.25f, 0.28f, 1.6f, 0.28f, trim) }
            else { b.m(Mt.PLAIN); p.cyl(x, y0 + 0.45f, set - pd + 0.25f, 0.13f, 2.5f, trim, 10) }
            if (g.reg) solid(l, x - 0.2f, set - pd + 0.05f, x + 0.2f, set - pd + 0.45f)
        }
        b.m(Mt.PLAIN); p.box(cx, y0 + 2.95f, set - pd + 0.25f, pw, 0.22f, 0.3f, trim)
        b.m(Mt.ROOF, 0.6f); p.quad(floatArrayOf(cx - pw / 2 - 0.25f, y0 + 3.0f, set - pd - 0.3f, cx + pw / 2 + 0.25f, y0 + 3.0f, set - pd - 0.3f, cx + pw / 2 + 0.25f, y0 + 3.6f, set, cx - pw / 2 - 0.25f, y0 + 3.6f, set), 0f, 1f, -1f, roofC)
        p.quad(floatArrayOf(cx - pw / 2 - 0.25f, y0 + 2.98f, set - pd - 0.3f, cx + pw / 2 + 0.25f, y0 + 2.98f, set - pd - 0.3f, cx + pw / 2 + 0.25f, y0 + 2.98f, set, cx - pw / 2 - 0.25f, y0 + 2.98f, set), 0f, -1f, 0f, shade(roofC, 40))
        // cadeiras de balanço / banco
        b.m(Mt.WOOD, 0.6f); p.box(cx + pw * 0.25f, y0 + 0.45f, set - 0.8f, 1.4f, 0.45f, 0.5f, C("#6B4A32"))
    }

    /** Água-furtada (janela no telhado). */
    private fun dormer(p: Pen, x: Float, y: Float, z: Float, wallC: Int, roofC: Int) {
        p.b.m(Mt.SIDING, 0.8f); p.box(x, y, z, 1.6f, 1.5f, 1.8f, wallC)
        p.b.m(Mt.ROOF, 0.6f); gableZ(p, x - 0.8f, x + 0.8f, z - 0.9f, z + 0.9f, y + 1.5f, 0.7f, roofC, 0.15f, wallC)
        p.b.m(Mt.PLAIN); p.box(x, y + 0.3f, z - 0.92f, 0.8f, 0.9f, 0.04f, GLASSC); p.box(x, y + 0.25f, z - 0.9f, 1.0f, 1.0f, 0.03f, TRIM)
    }

    /** Carro estacionado (no espaço do lote, de frente para a rua). */
    private fun parkedCar(g: CityGeo.Gen, l: Lot, x: Float, z: Float, r: City.Rng) {
        val m = Vehicles.pick(r)
        // modelo com o comprimento em z (frente para +z); gira para a frente apontar para a rua (−n)
        val tmp = MB(); Vehicles.geom(Vehicles.XF(tmp, 0f, 0f, 0f, 1), m, r.i(12))
        val fx = -l.nx; val fz = -l.nz   // (0,0,1) -> (fx, fz): x' = z·s, z' = z·c  => s = fx, c = fz
        g.b.appendRot(tmp, fz, fx, l.wx(x, z), CURB, l.wz(x, z))
        if (g.reg) solid(l, x - 1.0f, z - 2.3f, x + 1.0f, z + 2.3f)
    }

    /** Telhado de duas águas com a cumeeira de frente para a rua (ao longo de z). */
    private fun gableZ(p: Pen, x0: Float, x1: Float, z0: Float, z1: Float, y: Float, h: Float, c: Int, e: Float, wall: Int) {
        val xm = (x0 + x1) / 2
        val a0 = x0 - e; val a1 = x1 + e; val b0 = z0 - e; val b1 = z1 + e
        val yE = y - e * h / ((x1 - x0) / 2)
        p.quad(floatArrayOf(a0, yE, b0, a0, yE, b1, xm, y + h, b1, xm, y + h, b0), -1f, 1f, 0f, c)
        p.quad(floatArrayOf(a1, yE, b0, a1, yE, b1, xm, y + h, b1, xm, y + h, b0), 1f, 1f, 0f, c)
        p.tri(floatArrayOf(x0, y, z0, x1, y, z0, xm, y + h, z0), 0f, 0f, -1f, wall)
        p.tri(floatArrayOf(x0, y, z1, x1, y, z1, xm, y + h, z1), 0f, 0f, 1f, wall)
        p.quad(floatArrayOf(a0, yE, b0, a0, yE, b1, x0, y, b1, x0, y, b0), 0f, -1f, 0f, shade(c, 40))
        p.quad(floatArrayOf(a1, yE, b0, a1, yE, b1, x1, y, b1, x1, y, b0), 0f, -1f, 0f, shade(c, 40))
    }

    // ============================================================ mansão

    /**
     * Mansão (terreno de ~120 × 150 m): muro alto com portaria e portão, alameda de palmeiras até o pátio circular com chafariz,
     * palacete de 3 andares com pórtico de colunas duplas, alas, duas torres redondas, varanda; atrás: terraço, piscina de borda infinita,
     * casa de piscina, quadra de tênis, lago com deck, heliponto, jardim formal de cercas vivas, garagem para 6 carros.
     */
    private fun mansion(g: CityGeo.Gen, l: Lot, near: Boolean, far: Boolean) {
        val r = City.Rng(l.seed * 104729 + 7)
        val wall = C(arrayOf("#F3EEE4", "#EDE6D8", "#E9E4DA", "#F5F0E6", "#DCD3C3", "#E8DCC8")[r.i(6)])
        val roof = C(arrayOf("#3E4348", "#4A4F55", "#5B4A42", "#2F3337", "#6B3F2E")[r.i(5)])
        val W = l.w; val D = l.d; val y0 = CURB
        val set = 52f
        val cw = 32f; val cd = 22f; val fh = 3.9f; val ch = fh * 3
        val ww = 20f; val wd = 16f; val wh = fh * 2
        val wzs = set + 3f
        val tr = 4.2f   // raio das torres
        fun towerX(sg: Float) = sg * (cw / 2 + ww + tr - 1f)
        if (far) {
            val f = Pen(g.f, l); g.f.m(Mt.PLAIN)
            f.box(0f, y0, set + cd / 2, cw, ch, cd, wall)
            for (sg in floatArrayOf(-1f, 1f)) f.box(sg * (cw / 2 + ww / 2), y0, wzs + wd / 2, ww, wh, wd, wall)
            hip(f, -cw / 2, cw / 2, set, set + cd, y0 + ch, 5f, roof, 0.6f)
            f.box(0f, y0, 0.6f, W - 1f, 2.6f, 0.5f, C("#CFC6B4"))
        }
        if (g.reg) {
            solid(l, -cw / 2, set, cw / 2, set + cd)
            for (sg in floatArrayOf(-1f, 1f)) { solid(l, min(sg * cw / 2, sg * (cw / 2 + ww)), wzs, max(sg * cw / 2, sg * (cw / 2 + ww)), wzs + wd); solid(l, towerX(sg) - tr, wzs + wd / 2 - tr, towerX(sg) + tr, wzs + wd / 2 + tr) }
        }
        // ---- muro externo com portaria (colisão sempre)
        val gateW = 7f
        for (sg in floatArrayOf(-1f, 1f)) {
            val a = sg * (gateW / 2 + 3f); val e = sg * (W / 2 - 0.3f)
            if (g.reg) { solid(l, min(a, e), 0.3f, max(a, e), 0.9f); solid(l, e - 0.3f, 0.3f, e + 0.3f, D - 0.3f) }
        }
        if (g.reg) solid(l, -W / 2, D - 0.9f, W / 2, D - 0.3f)
        if (!near) return
        val b = g.b; val p = Pen(b, l)
        val stone = C("#CFC6B4"); val dark = C("#222222")
        for (sg in floatArrayOf(-1f, 1f)) {
            val a = sg * (gateW / 2 + 3f); val e = sg * (W / 2 - 0.3f)
            b.m(Mt.STONE, 0.7f); p.box((a + e) / 2, y0, 0.6f, abs(e - a), 1.0f, 0.6f, stone)
            b.m(Mt.METAL, 1f); p.box((a + e) / 2, y0 + 1.0f, 0.6f, abs(e - a), 0.07f, 0.07f, dark); p.box((a + e) / 2, y0 + 2.5f, 0.6f, abs(e - a), 0.07f, 0.07f, dark)
            var x = min(a, e) + 0.15f; while (x < max(a, e)) { p.box(x, y0 + 1.0f, 0.6f, 0.04f, 1.75f, 0.04f, dark); p.cyl(x, y0 + 2.75f, 0.6f, 0.03f, 0.12f, C("#C9A227"), 4); x += 0.2f }
            b.m(Mt.STONE, 0.7f); var px = min(a, e); val step = abs(e - a) / max(1, (abs(e - a) / 7f).toInt()); while (px <= max(a, e) + 0.01f) { p.box(px, y0, 0.6f, 0.8f, 2.9f, 0.8f, stone); p.box(px, y0 + 2.9f, 0.6f, 1.0f, 0.15f, 1.0f, shade(stone, -15)); px += step }
            // muro lateral alto até o fundo
            b.m(Mt.PLASTER, 0.8f); p.box(e, y0, D / 2, 0.45f, 2.6f, D - 1f, wall); b.m(Mt.STONE, 1f); p.box(e, y0 + 2.6f, D / 2, 0.6f, 0.12f, D - 1f, shade(stone, -10))
            // portaria (guarita) de um lado do portão
            if (sg < 0) { b.m(Mt.PLASTER, 0.8f); p.box(-gateW / 2 - 3.2f, y0, 4.5f, 4f, 3f, 4f, wall); b.m(Mt.ROOF, 0.6f); hip(p, -gateW / 2 - 5.2f, -gateW / 2 - 1.2f, 2.5f, 6.5f, y0 + 3f, 1.2f, roof, 0.4f); b.m(Mt.PLAIN); p.box(-gateW / 2 - 1.18f, y0 + 1.1f, 4.5f, 0.05f, 1.2f, 2.4f, GLASSC); if (g.reg) solid(l, -gateW / 2 - 5.2f, 2.5f, -gateW / 2 - 1.2f, 6.5f) }
            // colunas grandes do portão com luminárias
            b.m(Mt.STONE, 0.7f); p.box(sg * (gateW / 2 + 0.6f), y0, 0.6f, 1.3f, 3.6f, 1.3f, stone); p.box(sg * (gateW / 2 + 0.6f), y0 + 3.6f, 0.6f, 1.5f, 0.2f, 1.5f, shade(stone, -15))
            b.m(Mt.PLAIN); p.box(sg * (gateW / 2 + 0.6f), y0 + 3.8f, 0.6f, 0.4f, 0.6f, 0.4f, C("#FFF2C8"))
            // folhas do portão abertas para dentro
            b.m(Mt.METAL, 1f); p.box(sg * (gateW / 2 - 0.1f), y0 + 0.1f, 2.3f, 0.07f, 2.6f, 3.4f, dark)
        }
        b.m(Mt.PLASTER, 0.8f); p.box(0f, y0, D - 0.6f, W - 0.6f, 2.6f, 0.45f, wall)
        // ---- alameda de palmeiras até o pátio
        val rc = 10f; val ccz = set - 9f - rc
        b.m(Mt.PAVER, 0.45f); p.flat(-3.3f, -Town.SW - 0.6f, 3.3f, ccz - rc + 2f, y0 + 0.019f, C("#D9D2C2"))
        var az = 6f; while (az < ccz - rc - 2f) { for (sg in floatArrayOf(-1f, 1f)) { CityGeo.palm(g, l.wx(sg * 5.2f, az), l.wz(sg * 5.2f, az), r.r(1.05f, 1.25f)); if (g.reg) solid(l, sg * 5.2f - 0.3f, az - 0.3f, sg * 5.2f + 0.3f, az + 0.3f) }; az += 7.5f }
        // pátio circular com chafariz grande
        val ring = 48
        b.m(Mt.PAVER, 0.45f)
        for (k in 0 until ring) {
            val a0 = 6.2832f * k / ring; val a1 = 6.2832f * (k + 1) / ring; val ri = rc - 3.4f; val ro = rc + 3.4f
            p.quad(floatArrayOf(cos(a0) * ri, y0 + 0.02f, ccz + sin(a0) * ri, cos(a1) * ri, y0 + 0.02f, ccz + sin(a1) * ri, cos(a1) * ro, y0 + 0.02f, ccz + sin(a1) * ro, cos(a0) * ro, y0 + 0.02f, ccz + sin(a0) * ro), 0f, 1f, 0f, C("#D9D2C2"))
        }
        p.flat(-6f, ccz + rc - 1f, 6f, set - 4.6f, y0 + 0.019f, C("#D9D2C2"))
        b.m(Mt.STONE, 1f); p.cyl(0f, y0, ccz, 4.2f, 0.7f, C("#CFC8BA"), 28); p.cyl(0f, y0 + 0.7f, ccz, 0.5f, 1.8f, C("#CFC8BA"), 12); p.cyl(0f, y0 + 2.5f, ccz, 1.6f, 0.22f, C("#CFC8BA"), 18); p.cyl(0f, y0 + 2.7f, ccz, 0.3f, 1.2f, C("#CFC8BA"), 10); p.cyl(0f, y0 + 3.9f, ccz, 0.8f, 0.15f, C("#CFC8BA"), 14)
        b.m(Mt.PLAIN); p.cyl(0f, y0 + 0.62f, ccz, 3.9f, 0.06f, C("#5DB3D9"), 28)
        if (g.reg) solid(l, -4.2f, ccz - 4.2f, 4.2f, ccz + 4.2f)
        // jardim da frente: gramados com canteiros de flores e topiarias
        for (sg in floatArrayOf(-1f, 1f)) for (k in 0 until 4) {
            val bx = sg * (14f + k * 9f); val bz = ccz
            b.m(Mt.GRASS, 0.5f); p.box(bx, y0, bz, 6f, 0.5f, 6f, C("#4E7A3A"))
            CityGeo.bush(g, l.wx(bx, bz), l.wz(bx, bz), 0.9f)
        }
        // ---- palacete
        b.m(Mt.STONE, 0.7f); p.box(0f, y0, set + cd / 2, cw + 0.6f, 0.9f, cd + 0.6f, C("#A8A196"))
        b.m(Mt.PLASTER, 0.8f); p.box(0f, y0 + 0.9f, set + cd / 2, cw, ch - 0.9f, cd, wall)
        for (sg in floatArrayOf(-1f, 1f)) {
            val cx = sg * (cw / 2 + ww / 2)
            b.m(Mt.STONE, 0.7f); p.box(cx, y0, wzs + wd / 2, ww + 0.4f, 0.8f, wd + 0.4f, C("#A8A196"))
            b.m(Mt.PLASTER, 0.8f); p.box(cx, y0 + 0.8f, wzs + wd / 2, ww, wh - 0.8f, wd, wall)
            b.m(Mt.PLAIN); p.box(cx, y0 + wh - 0.3f, wzs + wd / 2, ww + 0.3f, 0.3f, wd + 0.3f, TRIM)
            b.m(Mt.ROOF, 0.6f); hip(p, cx - ww / 2, cx + ww / 2, wzs, wzs + wd, y0 + wh, 3.4f, roof, 0.55f)
            // torre redonda
            val tx = towerX(sg); val tz = wzs + wd / 2
            b.m(Mt.PLASTER, 0.8f); p.cyl(tx, y0, tz, tr, ch + 2f, wall, 24)
            b.m(Mt.PLAIN); p.cyl(tx, y0 + ch + 1.8f, tz, tr + 0.25f, 0.3f, TRIM, 24)
            b.m(Mt.ROOF, 0.6f); p.b.cyl(l.wx(tx, tz), y0 + ch + 2.1f, l.wz(tx, tz), tr + 0.4f, 0.05f, 6f, roof, true, 24)
            b.m(Mt.PLAIN)
            for (fl in 0..2) for (k in 0 until 6) { val a = 6.2832f * k / 6; val wx = tx + cos(a) * (tr + 0.05f); val wz = tz + sin(a) * (tr + 0.05f); if (sin(a) > 0.6f) continue; p.box(wx, y0 + 1.4f + fl * fh, wz, 0.9f, 1.9f, 0.9f, GLASSC) }
            // janelas das alas (frente e fundo)
            for (fl in 0..1) for (k in 0 until 5) { val wx = cx - ww / 2 + ww * (k + 0.5f) / 5; tallWindow(p, wx, y0 + 1.4f + fl * fh, wzs, C("#2F3E4E")); tallWindowBack(p, wx, y0 + 1.4f + fl * fh, wzs + wd) }
        }
        b.m(Mt.ROOF, 0.6f); hip(p, -cw / 2, cw / 2, set, set + cd, y0 + ch, 5.2f, roof, 0.7f)
        b.m(Mt.PLAIN)
        p.box(0f, y0 + ch - 0.35f, set + cd / 2, cw + 0.4f, 0.35f, cd + 0.4f, TRIM)
        for (k in 1..2) p.box(0f, y0 + fh * k, set + cd / 2, cw + 0.14f, 0.18f, cd + 0.14f, TRIM)
        for (fl in 0..2) for (k in 0 until 9) { val wx = -cw / 2 + cw * (k + 0.5f) / 9; if (fl == 0 && abs(wx) < 4f) continue; tallWindow(p, wx, y0 + 1.4f + fl * fh, set, C("#2F3E4E")); tallWindowBack(p, wx, y0 + 1.4f + fl * fh, set + cd) }
        // porta dupla, pórtico com 6 colunas de dois andares, frontão e varanda no 2º andar
        p.box(0f, y0 + 0.9f, set - 0.05f, 2.8f, 3.6f, 0.1f, C("#3B2A1E")); p.box(0f, y0 + 0.9f, set - 0.08f, 3.4f, 4.0f, 0.06f, TRIM)
        val pd = 6f; val pw = 16f
        b.m(Mt.STONE, 0.7f)
        for (k in 0..3) p.box(0f, y0 + k * 0.23f, set - pd - 1.8f + k * 0.45f + 0.9f, pw + 3f - k * 0.5f, 0.23f, pd + 1.8f - k * 0.45f, C("#D9D3C7"))
        b.m(Mt.PLAIN)
        for (k in 0..5) { val cx = -pw / 2 + 0.6f + (pw - 1.2f) * k / 5; p.cyl(cx, y0 + 0.92f, set - pd + 0.6f, 0.45f, 2 * fh - 0.2f, TRIM, 16); p.box(cx, y0 + 0.92f, set - pd + 0.6f, 1.1f, 0.3f, 1.1f, TRIM); p.box(cx, y0 + 2 * fh + 0.4f, set - pd + 0.6f, 1.1f, 0.35f, 1.1f, TRIM); if (g.reg) solid(l, cx - 0.5f, set - pd + 0.1f, cx + 0.5f, set - pd + 1.1f) }
        p.box(0f, y0 + 2 * fh + 0.75f, set - pd / 2, pw + 1f, 0.8f, pd + 0.4f, TRIM)
        val ry = y0 + 2 * fh + 1.55f; val zf = set - pd - 0.2f
        p.tri(floatArrayOf(-pw / 2 - 0.5f, ry, zf, pw / 2 + 0.5f, ry, zf, 0f, ry + 3.2f, zf), 0f, 0f, -1f, TRIM)
        b.m(Mt.ROOF, 0.6f)
        p.quad(floatArrayOf(-pw / 2 - 0.5f, ry, zf, -pw / 2 - 0.5f, ry, set, 0f, ry + 3.2f, set, 0f, ry + 3.2f, zf), -1f, 1f, 0f, roof)
        p.quad(floatArrayOf(pw / 2 + 0.5f, ry, zf, pw / 2 + 0.5f, ry, set, 0f, ry + 3.2f, set, 0f, ry + 3.2f, zf), 1f, 1f, 0f, roof)
        // balcão do 2º andar sobre a porta
        b.m(Mt.PLAIN); p.box(0f, y0 + fh + 0.6f, set - 1.4f, 7f, 0.25f, 2.8f, TRIM)
        for (k in 0..14) p.box(-3.4f + k * 6.8f / 14, y0 + fh + 0.85f, set - 2.75f, 0.12f, 0.9f, 0.12f, TRIM)
        p.box(0f, y0 + fh + 1.75f, set - 2.75f, 7f, 0.12f, 0.2f, TRIM)
        // ---- garagem para 6 carros (de um lado, com pátio de manobra)
        val gs = if (r.chance(0.5f)) 1f else -1f
        val gx = gs * (W / 2 - 16f); val gz = set - 14f
        b.m(Mt.PLASTER, 0.8f); p.box(gx, y0, gz + 5f, 24f, 3.6f, 10f, wall)
        b.m(Mt.ROOF, 0.6f); hip(p, gx - 12f, gx + 12f, gz, gz + 10f, y0 + 3.6f, 2.2f, roof, 0.45f)
        b.m(Mt.PLAIN); for (k in 0 until 6) p.box(gx - 10f + k * 4f, y0 + 0.02f, gz - 0.04f, 3.2f, 2.7f, 0.06f, C("#5A3A22"))
        b.m(Mt.PAVER, 0.45f); p.flat(gx - 12f, gz - 12f, gx + 12f, gz, y0 + 0.018f, C("#D9D2C2"))
        p.flat(min(gx, 0f) + (if (gx < 0f) 12f else 0f), ccz - 3f, max(gx, 0f) - (if (gx > 0f) 12f else 0f), ccz + 3f, y0 + 0.017f, C("#D9D2C2"))
        if (g.reg) solid(l, gx - 12f, gz, gx + 12f, gz + 10f)
        for (k in 0 until 3) parkedCar(g, l, gx - 8f + k * 8f, gz - 4f, r)
        // ---- fundos: terraço, piscina de borda infinita, casa de piscina
        val back = set + cd
        b.m(Mt.TILE, 0.5f); p.flat(-cw / 2 - 4f, back, cw / 2 + 4f, back + 10f, y0 + 0.02f, C("#EDE7DB"))
        b.m(Mt.STONE, 1f); p.box(0f, y0, back + 10.2f, cw + 8f, 0.6f, 0.4f, stone)
        val pz0 = back + 12f; val pz1 = pz0 + 14f; val pxw = 34f
        b.m(Mt.TILE, 0.5f); p.flat(-pxw / 2 - 4f, pz0 - 4f, pxw / 2 + 4f, pz1 + 4f, y0 + 0.02f, C("#EDE7DB"))
        b.m(Mt.PLAIN); p.flat(-pxw / 2, pz0, pxw / 2, pz1, y0 + 0.035f, C("#2E9BD0"))
        b.m(Mt.STONE, 1f); p.box(0f, y0, pz1 + 0.25f, pxw + 0.5f, 0.12f, 0.5f, C("#9FD3EA"))
        b.m(Mt.FABRIC, 1f); for (k in 0 until 8) { val sx = -pxw / 2 + 2f + k * (pxw - 4f) / 7; p.box(sx, y0 + 0.28f, pz0 - 2.2f, 0.75f, 0.12f, 2.0f, C("#FFFFFF")) }
        for (k in 0 until 3) { val sx = -pxw / 2 + 5f + k * (pxw - 10f) / 2; b.m(Mt.METAL, 1f); p.cyl(sx, y0, pz0 - 3.8f, 0.05f, 2.4f, C("#DDDDDD"), 6); b.m(Mt.FABRIC, 1f); p.b.cyl(l.wx(sx, pz0 - 3.8f), y0 + 2.2f, l.wz(sx, pz0 - 3.8f), 1.6f, 0.05f, 0.5f, C("#F4F1EA"), true, 12) }
        b.m(Mt.PLASTER, 0.8f); p.box(pxw / 2 + 12f, y0, pz0 + 6f, 12f, 3.4f, 8f, wall)
        b.m(Mt.ROOF, 0.6f); hip(p, pxw / 2 + 6f, pxw / 2 + 18f, pz0 + 2f, pz0 + 10f, y0 + 3.4f, 1.8f, roof, 0.45f)
        b.m(Mt.PLAIN); p.box(pxw / 2 + 12f, y0 + 0.4f, pz0 + 1.97f, 8f, 2.6f, 0.05f, GLASSC)
        if (g.reg) solid(l, pxw / 2 + 6f, pz0 + 2f, pxw / 2 + 18f, pz0 + 10f)
        for (sg in floatArrayOf(-1f, 1f)) for (k in 0..1) CityGeo.palm(g, l.wx(sg * (pxw / 2 + 2.5f), pz0 + 2f + k * 11f), l.wz(sg * (pxw / 2 + 2.5f), pz0 + 2f + k * 11f), 1.1f)
        // ---- quadra de tênis
        val tz0 = pz1 + 7f
        if (D - tz0 > 38f) {
            val qx = -W / 2 + 22f
            b.m(Mt.PLAIN); p.flat(qx - 10f, tz0, qx + 10f, tz0 + 36f, y0 + 0.02f, C("#3E7C5A")); p.flat(qx - 5.5f, tz0 + 6f, qx + 5.5f, tz0 + 30f, y0 + 0.03f, C("#2F6B9A"))
            for (zz in floatArrayOf(tz0 + 6f, tz0 + 30f)) p.flat(qx - 5.5f, zz - 0.05f, qx + 5.5f, zz + 0.05f, y0 + 0.04f, TRIM)
            for (xx in floatArrayOf(qx - 5.5f, qx + 5.5f, qx - 4.1f, qx + 4.1f)) p.flat(xx - 0.05f, tz0 + 6f, xx + 0.05f, tz0 + 30f, y0 + 0.04f, TRIM)
            p.flat(qx - 0.04f, tz0 + 12.4f, qx + 0.04f, tz0 + 23.6f, y0 + 0.04f, TRIM); p.flat(qx - 4.1f, tz0 + 12.4f, qx + 4.1f, tz0 + 12.5f, y0 + 0.04f, TRIM); p.flat(qx - 4.1f, tz0 + 23.5f, qx + 4.1f, tz0 + 23.6f, y0 + 0.04f, TRIM)
            b.m(Mt.METAL, 1f); p.box(qx, y0, tz0 + 18f, 12.8f, 1.07f, 0.04f, C("#202020")); p.box(qx, y0 + 1.0f, tz0 + 18f, 12.8f, 0.07f, 0.06f, TRIM)
            // alambrado
            for (zz in floatArrayOf(tz0, tz0 + 36f)) { p.box(qx, y0, zz, 20f, 3.2f, 0.03f, C("#5A6B5F")) }
            for (xx in floatArrayOf(qx - 10f, qx + 10f)) p.box(xx, y0, tz0 + 18f, 0.03f, 3.2f, 36f, C("#5A6B5F"))
            if (g.reg) { solid(l, qx - 10f, tz0 - 0.1f, qx + 10f, tz0 + 0.1f); solid(l, qx - 10f, tz0 + 35.9f, qx + 10f, tz0 + 36.1f); solid(l, qx - 10.1f, tz0, qx - 9.9f, tz0 + 36f); solid(l, qx + 9.9f, tz0, qx + 10.1f, tz0 + 36f) }
            // heliponto
            val hx = W / 2 - 20f; val hz = tz0 + 18f
            b.m(Mt.STONE, 1f); p.cyl(hx, y0, hz, 11f, 0.3f, C("#6E7276"), 32)
            b.m(Mt.PLAIN); p.cyl(hx, y0 + 0.3f, hz, 9.5f, 0.02f, C("#F2C230"), 32); p.cyl(hx, y0 + 0.31f, hz, 9.1f, 0.02f, C("#6E7276"), 32)
            p.flat(hx - 3f, hz - 3.5f, hx - 2f, hz + 3.5f, y0 + 0.34f, TRIM); p.flat(hx + 2f, hz - 3.5f, hx + 3f, hz + 3.5f, y0 + 0.34f, TRIM); p.flat(hx - 2f, hz - 0.5f, hx + 2f, hz + 0.5f, y0 + 0.34f, TRIM)
        }
        // ---- lago com deck e jardim formal ao lado da casa (do lado oposto à garagem)
        val lx = -gs * (W / 2 - 18f); val lz = 26f
        b.m(Mt.STONE, 1f); p.cyl(lx, y0 - 0.02f, lz, 12f, 0.06f, C("#9A9488"), 30)
        b.m(Mt.PLAIN); p.cyl(lx, y0 + 0.02f, lz, 11.2f, 0.06f, C("#3C8FB0"), 30)
        b.m(Mt.WOOD, 0.6f); p.box(lx + (if (lx > 0) -9f else 9f), y0 + 0.05f, lz, 7f, 0.2f, 2.5f, C("#9A7350"))
        if (g.reg) solid(l, lx - 8f, lz - 8f, lx + 8f, lz + 8f)
        // jardim formal: cercas vivas em quadrados
        val fgz = back - 8f
        for (i in 0..2) for (j in 0..1) {
            val bx = lx + (i - 1) * 7f; val bz = fgz + 18f + j * 7f
            if (bz + 3f > D - 3f) continue
            b.m(Mt.GRASS, 0.5f)
            p.box(bx, y0, bz - 2.5f, 5.5f, 0.9f, 0.5f, C("#3F6E33")); p.box(bx, y0, bz + 2.5f, 5.5f, 0.9f, 0.5f, C("#3F6E33"))
            p.box(bx - 2.5f, y0, bz, 0.5f, 0.9f, 5.5f, C("#3F6E33")); p.box(bx + 2.5f, y0, bz, 0.5f, 0.9f, 5.5f, C("#3F6E33"))
            CityGeo.bush(g, l.wx(bx, bz), l.wz(bx, bz), 0.8f)
        }
        // árvores grandes ao longo dos muros
        var tz = 8f; while (tz < D - 6f) { for (sg in floatArrayOf(-1f, 1f)) { val tx = sg * (W / 2 - 4f); if (abs(tx - gx) < 14f && tz > gz - 13f && tz < gz + 11f) continue; CityGeo.tree(g, l.wx(tx, tz), l.wz(tx, tz), r.r(1.0f, 1.3f), CURB, if (r.chance(0.5f)) 4 else 0) }; tz += 11f }
        if (l.forSale) { b.m(Mt.PLAIN); p.box(gateW / 2 + 3f, y0, -0.6f, 1.6f, 0.9f, 0.05f, C("#C62828")); p.box(gateW / 2 + 3f, y0 + 0.9f, -0.6f, 0.08f, 0.7f, 0.08f, C("#F2F2F2")) }
    }

    private fun tallWindowBack(p: Pen, x: Float, y: Float, z: Float) {
        p.box(x, y - 0.08f, z + 0.03f, 1.3f, 2.1f, 0.08f, TRIM)
        p.box(x, y, z + 0.07f, 1.1f, 1.95f, 0.02f, GLASSC)
    }

    private fun tallWindow(p: Pen, x: Float, y: Float, z: Float, shut: Int) {
        p.box(x, y - 0.08f, z - 0.03f, 1.3f, 2.1f, 0.08f, TRIM)
        p.box(x, y, z - 0.07f, 1.1f, 1.95f, 0.02f, GLASSC)
        p.box(x, y + 1.0f, z - 0.085f, 1.1f, 0.05f, 0.03f, TRIM)
        p.box(x, y - 0.15f, z - 0.12f, 1.5f, 0.1f, 0.16f, TRIM)
        for (s in floatArrayOf(-1f, 1f)) p.box(x + s * 0.88f, y - 0.05f, z - 0.06f, 0.42f, 2.05f, 0.05f, shut)
    }

    /** Telhado de quatro águas (cumeeira ao longo de x). */
    private fun hip(p: Pen, x0: Float, x1: Float, z0: Float, z1: Float, y: Float, h: Float, c: Int, e: Float) {
        val a0 = x0 - e; val a1 = x1 + e; val b0 = z0 - e; val b1 = z1 + e
        val zm = (z0 + z1) / 2; val inset = min((x1 - x0) / 2 - 0.2f, (z1 - z0) / 2)
        val r0 = x0 + inset; val r1 = x1 - inset; val yt = y + h
        val yE = y - e * h / ((z1 - z0) / 2)
        p.quad(floatArrayOf(a0, yE, b0, a1, yE, b0, r1, yt, zm, r0, yt, zm), 0f, 1f, -1f, c)
        p.quad(floatArrayOf(a1, yE, b1, a0, yE, b1, r0, yt, zm, r1, yt, zm), 0f, 1f, 1f, c)
        p.tri(floatArrayOf(a0, yE, b1, a0, yE, b0, r0, yt, zm), -1f, 1f, 0f, c)
        p.tri(floatArrayOf(a1, yE, b0, a1, yE, b1, r1, yt, zm), 1f, 1f, 0f, c)
        p.quad(floatArrayOf(a0, yE, b0, a1, yE, b0, a1, yE, b1, a0, yE, b1), 0f, -1f, 0f, shade(c, 40))
    }

    /** Telhado de duas águas: cumeeira ao longo da frente (x0..x1), de z0 a z1, a partir de y, altura h, beiral e. */
    private fun gable(p: Pen, x0: Float, x1: Float, z0: Float, z1: Float, y: Float, h: Float, c: Int, e: Float, wall: Int = shade(c, 25)) {
        val zm = (z0 + z1) / 2
        val a0 = x0 - e; val a1 = x1 + e; val b0 = z0 - e; val b1 = z1 + e
        val yE = y - e * h / ((z1 - z0) / 2)
        p.quad(floatArrayOf(a0, yE, b0, a1, yE, b0, a1, y + h, zm, a0, y + h, zm), 0f, 1f, -1f, c)
        p.quad(floatArrayOf(a0, yE, b1, a1, yE, b1, a1, y + h, zm, a0, y + h, zm), 0f, 1f, 1f, c)
        // oitões (triângulos nas pontas) na cor da parede seria mais bonito; aqui na cor do telhado escurecida
        val gc = wall
        p.tri(floatArrayOf(x0, y, z0, x0, y, z1, x0, y + h, zm), -1f, 0f, 0f, gc)
        p.tri(floatArrayOf(x1, y, z0, x1, y, z1, x1, y + h, zm), 1f, 0f, 0f, gc)
        // forro do beiral (embaixo)
        p.quad(floatArrayOf(a0, yE, b0, a1, yE, b0, a1, y, z0, a0, y, z0), 0f, -1f, 0f, shade(c, 40))
        p.quad(floatArrayOf(a0, yE, b1, a1, yE, b1, a1, y, z1, a0, y, z1), 0f, -1f, 0f, shade(c, 40))
    }

    private fun window(p: Pen, x: Float, y: Float, z: Float, out: Float, shut: Int, shutters: Boolean, trim: Int = TRIM) {
        val TRIM = trim
        p.box(x, y - 0.06f, z + out * 0.03f, 1.3f, 1.42f, 0.08f, TRIM)
        p.box(x, y, z + out * 0.07f, 1.1f, 1.3f, 0.02f, GLASSC)
        p.box(x, y + 0.62f, z + out * 0.08f, 1.1f, 0.06f, 0.03f, TRIM)
        p.box(x, y, z + out * 0.085f, 0.05f, 1.3f, 0.03f, TRIM)
        if (shutters) for (s in floatArrayOf(-1f, 1f)) p.box(x + s * 0.88f, y - 0.02f, z + out * 0.06f, 0.42f, 1.4f, 0.05f, shut)
    }

    private fun windowSide(p: Pen, x: Float, y: Float, z: Float, out: Float, trim: Int = TRIM) {
        val TRIM = trim
        p.box(x + out * 0.03f, y - 0.06f, z, 0.08f, 1.42f, 1.2f, TRIM)
        p.box(x + out * 0.07f, y, z, 0.02f, 1.3f, 1.0f, GLASSC)
    }

    /** Cerca de madeira lisa (1,8 m) de (x0, z0) a (x1, z1), com colisão. */
    private fun fence(p: Pen, x0: Float, z0: Float, x1: Float, z1: Float, c: Int, g: CityGeo.Gen) {
        val L = hypot(x1 - x0, z1 - z0); if (L < 0.5f) return
        val cx = (x0 + x1) / 2; val cz = (z0 + z1) / 2
        if (abs(x1 - x0) > abs(z1 - z0)) p.box(cx, CURB, cz, L, 1.8f, 0.08f, c) else p.box(cx, CURB, cz, 0.08f, 1.8f, L, c)
        val n = (L / 2.4f).toInt()
        for (k in 0..n) { val t = k / max(1f, n.toFloat()); p.box(x0 + (x1 - x0) * t, CURB, z0 + (z1 - z0) * t, 0.12f, 1.9f, 0.12f, shade(c, 15)) }
        if (g.reg) {
            if (abs(x1 - x0) > abs(z1 - z0)) solid(p.l, min(x0, x1), cz - 0.1f, max(x0, x1), cz + 0.1f) else solid(p.l, cx - 0.1f, min(z0, z1), cx + 0.1f, max(z0, z1))
        }
    }

    /** Cerquinha branca de ripas na frente, de x0 a x1 na profundidade z. */
    private fun picket(p: Pen, x0: Float, x1: Float, z: Float, g: CityGeo.Gen) {
        val c = C("#FAFAF7")
        p.box((x0 + x1) / 2, CURB + 0.35f, z, x1 - x0, 0.07f, 0.05f, c)
        p.box((x0 + x1) / 2, CURB + 0.75f, z, x1 - x0, 0.07f, 0.05f, c)
        var x = x0
        while (x <= x1) { p.box(x, CURB, z, 0.08f, 1.0f, 0.03f, c); x += 0.16f }
        if (g.reg) solid(p.l, x0, z - 0.06f, x1, z + 0.06f)
    }

    @Suppress("unused") private fun unused() = cos(0f) + sin(0f)
}
