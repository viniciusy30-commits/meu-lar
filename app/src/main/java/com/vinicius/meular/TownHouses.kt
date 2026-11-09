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
    private val LW = floatArrayOf(0f, 17f, 22f, 30f, 62f)
    private val LD = floatArrayOf(0f, 30f, 36f, 46f, 80f)

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
            if (ed.w > 14f) continue   // casas não ficam de frente para avenida / rua principal
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
                        val l = Lot(fx + tx * w / 2 * 1f, fz + tz * w / 2 * 1f, ltx, ltz, nx, nz, w - 0.6f, d, tier, seed)
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

    /** Desenha o lote [l]: casa, garagem, entrada de carro, caixa de correio, cerca, árvores. [far] = versão simples. */
    fun draw(g: CityGeo.Gen, l: Lot, near: Boolean, far: Boolean) {
        if (l.tier == 4) { mansion(g, l, near, far); return }
        val r = City.Rng(l.seed * 7919 + 13)
        val side = C(SIDING[r.i(SIDING.size)]); val roof = C(ROOFC[r.i(ROOFC.size)]); val door = C(DOORC[r.i(DOORC.size)])
        val t = l.tier
        val W = l.w; val D = l.d
        // dimensões da casa
        val (hw, hd, floors) = when (t) { 1 -> Triple(min(9f, W - 7f), min(8.5f, D * 0.32f), 1); 2 -> Triple(min(11f, W - 8.5f), min(9.5f, D * 0.3f), if (r.chance(0.6f)) 2 else 1); 3 -> Triple(min(15f, W - 10f), min(11f, D * 0.28f), 2); else -> Triple(min(26f, W - 18f), min(15f, D * 0.22f), 2) }
        val set = when (t) { 1 -> 7f; 2 -> 8.5f; 3 -> 10f; else -> 18f }
        val gw = when (t) { 1 -> 3.6f; 2 -> 6.2f; 3 -> 8.8f; else -> 9.5f }   // largura da garagem
        val gSide = if (r.chance(0.5f)) 1f else -1f
        // casa + garagem ocupam (hw + gw) na frente, centralizadas no lote
        val total = hw + gw
        val hx0 = -total / 2 + (if (gSide < 0) gw else 0f)            // casa de hx0 a hx0 + hw
        val gx0 = if (gSide < 0) -total / 2 else hx0 + hw             // garagem de gx0 a gx0 + gw
        val wallH = 2.9f; val H = wallH * floors
        val y0 = CURB
        if (far) {
            val f = Pen(g.f, l)
            g.f.m(Mt.PLAIN)
            f.box(hx0 + hw / 2, y0, set + hd / 2, hw, H, hd, side)
            f.box(gx0 + gw / 2, y0, set + 0.6f + 3.5f, gw, 2.7f, 7f, side)
            gable(f, hx0, hx0 + hw, set, set + hd, y0 + H, hd * 0.32f, roof, 0.4f)
        }
        if (g.reg) {
            solid(l, hx0, set, hx0 + hw, set + hd)
            solid(l, gx0, set + 0.6f, gx0 + gw, set + 7.6f)
        }
        if (!near) return
        val b = g.b; val p = Pen(b, l)
        // fundação e paredes
        b.m(Mt.STONE, 1f); p.box(hx0 + hw / 2, y0, set + hd / 2, hw + 0.2f, 0.45f, hd + 0.2f, C("#9C9890"))
        b.m(if (t >= 3 && r.chance(0.5f)) Mt.PLASTER else Mt.SIDING, 0.8f)
        p.box(hx0 + hw / 2, y0 + 0.45f, set + hd / 2, hw, H - 0.45f, hd, side)
        // faixa entre andares
        if (floors > 1) { b.m(Mt.PLAIN); p.box(hx0 + hw / 2, y0 + wallH - 0.1f, set + hd / 2, hw + 0.08f, 0.18f, hd + 0.08f, TRIM) }
        // telhado
        b.m(Mt.ROOF, 0.6f); gable(p, hx0, hx0 + hw, set, set + hd, y0 + H, hd * 0.34f, roof, 0.5f, side)
        // garagem: corpo, telhado próprio mais baixo, portão
        b.m(Mt.SIDING, 0.8f); p.box(gx0 + gw / 2, y0, set + 0.6f + 3.5f, gw, 2.75f, 7f, side)
        b.m(Mt.ROOF, 0.6f); gable(p, gx0, gx0 + gw, set + 0.6f, set + 7.6f, y0 + 2.75f, 1.6f, roof, 0.35f, side)
        b.m(Mt.PLAIN)
        val nDoors = if (t == 1) 1 else if (t == 4) 3 else (gw / 3.1f).toInt().coerceAtLeast(1)
        val dw = (gw - 0.6f) / nDoors
        for (k in 0 until nDoors) {
            val cx = gx0 + 0.3f + dw * (k + 0.5f)
            p.box(cx, y0 + 0.02f, set + 0.6f - 0.04f, dw - 0.4f, 2.25f, 0.06f, C("#F3F3F0"))
            for (q in 1..3) p.box(cx, y0 + 0.02f + q * 0.56f, set + 0.6f - 0.08f, dw - 0.5f, 0.04f, 0.04f, C("#D6D6D2"))
        }
        // entrada de carro (concreto) da garagem até o meio-fio, passando pela calçada
        val dx0 = gx0 + 0.2f; val dx1 = gx0 + gw - 0.2f
        b.m(Mt.PAVER, 0.5f); p.flat(dx0, -Town.SW - 0.6f, dx1, set + 0.6f, y0 + 0.018f, CONC)
        // calçadinha da porta até a calçada
        val doorX = if (gSide > 0) hx0 + hw * 0.38f else hx0 + hw * 0.62f
        p.flat(doorX - 0.65f, -0.6f, doorX + 0.65f, set, y0 + 0.016f, C("#CFCAC0"))
        // porta e varanda
        b.m(Mt.PLAIN)
        p.box(doorX, y0 + 0.45f, set - 0.05f, 1.15f, 2.2f, 0.1f, door)
        p.box(doorX, y0 + 0.45f, set - 0.08f, 1.45f, 2.38f, 0.06f, TRIM)
        p.box(doorX + 0.38f, y0 + 1.5f, set - 0.12f, 0.06f, 0.06f, 0.05f, C("#C9A227"))
        if (t >= 2) {
            // varanda coberta com colunas
            val pw = if (t >= 3) hw * 0.7f else 3.6f; val pd = 2.2f
            val pc = if (t >= 3) hx0 + hw / 2 else doorX
            b.m(Mt.WOOD, 0.6f); p.box(pc, y0, set - pd / 2, pw, 0.45f, pd, C("#B9B2A6"))
            b.m(Mt.PLAIN)
            for (k in 0..1) p.box(pc + (if (k == 0) -1 else 1) * (pw / 2 - 0.2f), y0 + 0.45f, set - pd + 0.2f, 0.22f, 2.5f, 0.22f, TRIM)
            if (t >= 3) for (k in 1..2) p.box(pc - pw / 2 + 0.2f + (pw - 0.4f) * k / 3, y0 + 0.45f, set - pd + 0.2f, 0.22f, 2.5f, 0.22f, TRIM)
            b.m(Mt.ROOF, 0.6f); p.box(pc, y0 + 2.95f, set - pd / 2, pw + 0.3f, 0.16f, pd + 0.2f, roof)
        } else {
            b.m(Mt.STONE, 1f); p.box(doorX, y0, set - 0.7f, 1.8f, 0.3f, 1.4f, C("#B8B3AA"))
        }
        // janelas (frente, laterais) com moldura e venezianas
        b.m(Mt.PLAIN)
        val shut = C(arrayOf("#2F3E4E", "#4A3A2E", "#2E4A3A", "#1E1E1E", "#7A2E2E")[r.i(5)])
        for (fl in 0 until floors) {
            val wy = y0 + 0.45f + 0.95f + fl * wallH
            val n = max(2, (hw / 3.2f).toInt())
            for (k in 0 until n) {
                val wx = hx0 + hw * (k + 0.5f) / n
                if (fl == 0 && abs(wx - doorX) < 1.4f) continue
                window(p, wx, wy, set, -1f, shut, t >= 2)
            }
            for (k in 0 until max(2, (hw / 4f).toInt())) window(p, hx0 + hw * (k + 0.5f) / max(2, (hw / 4f).toInt()), wy, set + hd, 1f, shut, false)
            for (sx in floatArrayOf(hx0, hx0 + hw)) {
                if ((sx == hx0 + hw && gSide > 0) || (sx == hx0 && gSide < 0)) continue   // lado colado na garagem
                for (k in 0..1) windowSide(p, sx, wy, set + hd * (0.3f + k * 0.4f), if (sx == hx0) -1f else 1f)
            }
        }
        // chaminé
        if (r.chance(0.5f)) { b.m(Mt.STONE, 1f); p.box(hx0 + hw * (if (gSide > 0) 0.15f else 0.85f), y0 + H, set + hd * 0.6f, 0.9f, hd * 0.34f + 1.2f, 0.9f, C("#8D6E63")) }
        // caixa de correio junto do meio-fio
        val mx = if (gSide > 0) dx0 - 0.8f else dx1 + 0.8f
        b.m(Mt.WOOD, 0.6f); p.box(mx, y0, -Town.SW - 0.25f, 0.1f, 1.05f, 0.1f, C("#5A4636"))
        b.m(Mt.METAL, 1f); p.box(mx, y0 + 1.05f, -Town.SW - 0.25f, 0.24f, 0.24f, 0.48f, C(arrayOf("#222222", "#F2F2F2", "#1F3A5F", "#8E1B1B")[r.i(4)]))
        if (g.reg) solid(l, mx - 0.15f, -Town.SW - 0.5f, mx + 0.15f, -Town.SW)
        // cerca do quintal (madeira) dos lados e no fundo
        val fc = C(if (r.chance(0.5f)) "#E9E4DA" else "#A88A6A")
        b.m(Mt.WOOD, 0.6f)
        val fz0 = set + hd * 0.6f
        fence(p, -W / 2 + 0.15f, fz0, -W / 2 + 0.15f, D - 0.2f, fc, g)
        fence(p, W / 2 - 0.15f, fz0, W / 2 - 0.15f, D - 0.2f, fc, g)
        fence(p, -W / 2 + 0.15f, D - 0.2f, W / 2 - 0.15f, D - 0.2f, fc, g)
        // cerca branca na frente (algumas)
        if (t <= 2 && r.chance(0.35f)) {
            b.m(Mt.WOOD, 0.6f)
            val a0 = -W / 2 + 0.3f; val a1 = min(dx0, doorX - 0.8f) - 0.3f; val b0 = max(dx1, doorX + 0.8f) + 0.3f; val b1 = W / 2 - 0.3f
            if (a1 > a0 + 1f) picket(p, a0, a1, 0.6f, g)
            if (b1 > b0 + 1f) picket(p, b0, b1, 0.6f, g)
        }
        // árvores e arbustos
        CityGeo.tree(g, l.wx(if (gSide > 0) -W / 2 + 3f else W / 2 - 3f, set * 0.45f), l.wz(if (gSide > 0) -W / 2 + 3f else W / 2 - 3f, set * 0.45f), r.r(0.7f, 0.95f))
        if (g.reg) solid(l, (if (gSide > 0) -W / 2 + 3f else W / 2 - 3f) - 0.25f, set * 0.45f - 0.25f, (if (gSide > 0) -W / 2 + 3f else W / 2 - 3f) + 0.25f, set * 0.45f + 0.25f)
        for (k in 0 until (2 + t)) { val bx = hx0 + 0.6f + (hw - 1.2f) * k / (1 + t); if (abs(bx - doorX) > 1.2f) CityGeo.bush(g, l.wx(bx, set - 0.8f), l.wz(bx, set - 0.8f), 0.55f) }
        if (D > 34f) CityGeo.tree(g, l.wx(r.r(-W / 3, W / 3), D - 6f), l.wz(r.r(-W / 3, W / 3), D - 6f), r.r(0.8f, 1.05f))
        // piscina no quintal (casas grandes)
        if (t >= 3 && D - (set + hd) > 14f) {
            val pz0 = set + hd + 4f; val pz1 = min(D - 4f, pz0 + 9f); val pxw = min(W - 8f, 10f)
            b.m(Mt.TILE, 0.5f); p.flat(-pxw / 2 - 1.2f, pz0 - 1.2f, pxw / 2 + 1.2f, pz1 + 1.2f, y0 + 0.02f, C("#E8E2D6"))
            b.m(Mt.PLAIN); p.flat(-pxw / 2, pz0, pxw / 2, pz1, y0 + 0.035f, C("#3FA9D6"))
        }
        // placa "à venda"
        if (l.forSale) {
            val sx = if (gSide > 0) -W / 2 + 1.5f else W / 2 - 1.5f
            b.m(Mt.WOOD, 0.6f); p.box(sx, y0, 1.2f, 0.08f, 1.3f, 0.08f, C("#F2F2F2"))
            b.m(Mt.PLAIN); p.box(sx, y0 + 0.75f, 1.2f, 0.9f, 0.55f, 0.04f, C("#C62828"))
        }
    }

    // ------------------------------------------------------------ mansão

    /**
     * Mansão: bloco central de 3 andares com pórtico de colunas e frontão, duas alas laterais recuadas,
     * garagem para 3 carros separada, muro com portão, entrada circular com chafariz, piscina e casa de piscina no fundo.
     */
    private fun mansion(g: CityGeo.Gen, l: Lot, near: Boolean, far: Boolean) {
        val r = City.Rng(l.seed * 104729 + 7)
        val wall = C(arrayOf("#F3EEE4", "#EDE6D8", "#E9E4DA", "#F5F0E6", "#DCD3C3")[r.i(5)])
        val roof = C(arrayOf("#3E4348", "#4A4F55", "#5B4A42", "#2F3337")[r.i(4)])
        val W = l.w; val D = l.d; val y0 = CURB
        val set = 24f
        val cw = 15f; val cd = 13f; val ch = 3.4f * 3        // bloco central
        val ww = min(11f, (W - cw - 14f) / 2); val wd = 10f; val wh = 3.4f * 2   // alas
        val wzs = set + 2.5f
        if (far) {
            val f = Pen(g.f, l); g.f.m(Mt.PLAIN)
            f.box(0f, y0, set + cd / 2, cw, ch, cd, wall)
            for (sg in floatArrayOf(-1f, 1f)) f.box(sg * (cw / 2 + ww / 2), y0, wzs + wd / 2, ww, wh, wd, wall)
            hip(f, -cw / 2, cw / 2, set, set + cd, y0 + ch, 3.2f, roof, 0.5f)
        }
        if (g.reg) {
            solid(l, -cw / 2, set, cw / 2, set + cd)
            for (sg in floatArrayOf(-1f, 1f)) solid(l, min(sg * cw / 2, sg * (cw / 2 + ww)), wzs, max(sg * cw / 2, sg * (cw / 2 + ww)), wzs + wd)
        }
        if (!near) return
        val b = g.b; val p = Pen(b, l)
        // corpo
        b.m(Mt.STONE, 1f); p.box(0f, y0, set + cd / 2, cw + 0.4f, 0.7f, cd + 0.4f, C("#A8A196"))
        b.m(Mt.PLASTER, 0.8f); p.box(0f, y0 + 0.7f, set + cd / 2, cw, ch - 0.7f, cd, wall)
        for (sg in floatArrayOf(-1f, 1f)) {
            val cx = sg * (cw / 2 + ww / 2)
            b.m(Mt.STONE, 1f); p.box(cx, y0, wzs + wd / 2, ww + 0.3f, 0.6f, wd + 0.3f, C("#A8A196"))
            b.m(Mt.PLASTER, 0.8f); p.box(cx, y0 + 0.6f, wzs + wd / 2, ww, wh - 0.6f, wd, wall)
            b.m(Mt.ROOF, 0.6f); hip(p, cx - ww / 2, cx + ww / 2, wzs, wzs + wd, y0 + wh, 2.6f, roof, 0.45f)
        }
        b.m(Mt.ROOF, 0.6f); hip(p, -cw / 2, cw / 2, set, set + cd, y0 + ch, 3.4f, roof, 0.55f)
        // cornija branca no alto das paredes e faixas entre andares
        b.m(Mt.PLAIN)
        p.box(0f, y0 + ch - 0.25f, set + cd / 2, cw + 0.3f, 0.25f, cd + 0.3f, TRIM)
        for (k in 1..2) p.box(0f, y0 + 3.4f * k, set + cd / 2, cw + 0.12f, 0.16f, cd + 0.12f, TRIM)
        // janelas altas (frente do bloco central e das alas)
        val shut = C("#2F3E4E")
        for (fl in 0..2) for (k in 0 until 5) {
            val wx = -cw / 2 + cw * (k + 0.5f) / 5
            if (fl == 0 && k == 2) continue
            tallWindow(p, wx, y0 + 1.25f + fl * 3.4f, set, shut)
        }
        for (sg in floatArrayOf(-1f, 1f)) for (fl in 0..1) for (k in 0 until 3) {
            val wx = sg * (cw / 2 + ww * (k + 0.5f) / 3)
            tallWindow(p, wx, y0 + 1.25f + fl * 3.4f, wzs, shut)
        }
        // porta dupla e pórtico com 4 colunas e frontão
        p.box(0f, y0 + 0.7f, set - 0.05f, 2.2f, 2.9f, 0.1f, C("#3B2A1E"))
        p.box(0f, y0 + 0.7f, set - 0.08f, 2.7f, 3.2f, 0.06f, TRIM)
        val pd = 4.2f; val pw = 8.4f
        b.m(Mt.STONE, 1f)
        for (k in 0..2) p.box(0f, y0 + k * 0.23f, set - pd - 0.9f + k * 0.3f + 0.45f, pw + 1.2f - k * 0.3f, 0.23f, pd + 0.9f - k * 0.3f, C("#D9D3C7"))
        b.m(Mt.PLAIN)
        for (k in 0..3) p.cyl(-pw / 2 + 0.4f + (pw - 0.8f) * k / 3, y0 + 0.7f, set - pd + 0.4f, 0.32f, 6.3f, TRIM, 14)
        p.box(0f, y0 + 7.0f, set - pd / 2, pw + 0.6f, 0.6f, pd + 0.2f, TRIM)
        b.m(Mt.ROOF, 0.6f)
        val ry = y0 + 7.6f; val zf = set - pd - 0.1f
        p.tri(floatArrayOf(-pw / 2 - 0.3f, ry, zf, pw / 2 + 0.3f, ry, zf, 0f, ry + 2.0f, zf), 0f, 0f, -1f, TRIM)
        p.quad(floatArrayOf(-pw / 2 - 0.3f, ry, zf, -pw / 2 - 0.3f, ry, set, 0f, ry + 2.0f, set, 0f, ry + 2.0f, zf), -1f, 1f, 0f, roof)
        p.quad(floatArrayOf(pw / 2 + 0.3f, ry, zf, pw / 2 + 0.3f, ry, set, 0f, ry + 2.0f, set, 0f, ry + 2.0f, zf), 1f, 1f, 0f, roof)
        if (g.reg) for (k in 0..3) { val cx = -pw / 2 + 0.4f + (pw - 0.8f) * k / 3; solid(l, cx - 0.3f, set - pd + 0.1f, cx + 0.3f, set - pd + 0.7f) }
        // entrada circular com chafariz
        val rc = 7.5f; val ccz = set - pd - 1.5f - rc - 2.8f
        val ring = 40
        b.m(Mt.PAVER, 0.5f)
        for (k in 0 until ring) {
            val a0 = 6.2832f * k / ring; val a1 = 6.2832f * (k + 1) / ring
            val ri = rc - 2.8f; val ro = rc + 2.8f
            p.quad(floatArrayOf(cos(a0) * ri, y0 + 0.02f, ccz + sin(a0) * ri, cos(a1) * ri, y0 + 0.02f, ccz + sin(a1) * ri, cos(a1) * ro, y0 + 0.02f, ccz + sin(a1) * ro, cos(a0) * ro, y0 + 0.02f, ccz + sin(a0) * ro), 0f, 1f, 0f, C("#D9D2C2"))
        }
        // ligação do círculo com o portão e com a garagem
        p.flat(-2.6f, -Town.SW - 0.6f, 2.6f, ccz - rc + 2.6f, y0 + 0.019f, C("#D9D2C2"))
        // chafariz
        b.m(Mt.STONE, 1f); p.cyl(0f, y0, ccz, 2.4f, 0.55f, C("#CFC8BA"), 24); p.cyl(0f, y0 + 0.55f, ccz, 0.35f, 1.3f, C("#CFC8BA"), 12); p.cyl(0f, y0 + 1.8f, ccz, 1.0f, 0.18f, C("#CFC8BA"), 16)
        b.m(Mt.PLAIN); p.cyl(0f, y0 + 0.5f, ccz, 2.15f, 0.06f, C("#5DB3D9"), 24)
        if (g.reg) solid(l, -2.4f, ccz - 2.4f, 2.4f, ccz + 2.4f)
        // garagem para 3 carros (separada, de um lado) com caminho até o círculo
        val gs = if (r.chance(0.5f)) 1f else -1f
        val gx = gs * (W / 2 - 9f); val gz = set + 1f
        b.m(Mt.PLASTER, 0.8f); p.box(gx, y0, gz + 4f, 11f, 3.2f, 8f, wall)
        b.m(Mt.ROOF, 0.6f); hip(p, gx - 5.5f, gx + 5.5f, gz, gz + 8f, y0 + 3.2f, 1.8f, roof, 0.35f)
        b.m(Mt.PLAIN); for (k in 0..2) p.box(gx - 3.5f + k * 3.5f, y0 + 0.02f, gz - 0.04f, 2.8f, 2.4f, 0.06f, C("#5A3A22"))
        b.m(Mt.PAVER, 0.5f); p.flat(gx - 5.3f, ccz, gx + 5.3f, gz, y0 + 0.019f, C("#D9D2C2"))
        p.flat(min(gx, 0f), ccz - 2.6f, max(gx, 0f), ccz + 2.6f, y0 + 0.017f, C("#D9D2C2"))
        if (g.reg) solid(l, gx - 5.5f, gz, gx + 5.5f, gz + 8f)
        // muro com grade e portão na frente
        val mz = 0.5f
        for (sg in floatArrayOf(-1f, 1f)) {
            val a = sg * 3.4f; val e = sg * (W / 2 - 0.3f)
            b.m(Mt.STONE, 1f); p.box((a + e) / 2, y0, mz, abs(e - a), 0.9f, 0.4f, C("#CFC6B4"))
            b.m(Mt.METAL, 1f); p.box((a + e) / 2, y0 + 0.9f, mz, abs(e - a), 0.06f, 0.06f, C("#222222")); p.box((a + e) / 2, y0 + 1.95f, mz, abs(e - a), 0.06f, 0.06f, C("#222222"))
            var x = min(a, e) + 0.15f; while (x < max(a, e)) { p.box(x, y0 + 0.9f, mz, 0.04f, 1.2f, 0.04f, C("#222222")); x += 0.18f }
            b.m(Mt.STONE, 1f); var px = min(a, e); while (px <= max(a, e) + 0.01f) { p.box(px, y0, mz, 0.6f, 2.3f, 0.6f, C("#CFC6B4")); px += (abs(e - a) / max(1f, (abs(e - a) / 6f).toInt().toFloat())) }
            if (g.reg) solid(l, min(a, e), mz - 0.3f, max(a, e), mz + 0.3f)
            // muro dos lados até o fundo
            b.m(Mt.STONE, 1f); p.box(e, y0, D / 2, 0.4f, 2.2f, D - 1f, C("#CFC6B4"))
            if (g.reg) solid(l, e - 0.25f, mz, e + 0.25f, D - 0.5f)
        }
        b.m(Mt.STONE, 1f); p.box(0f, y0, D - 0.5f, W - 0.6f, 2.2f, 0.4f, C("#CFC6B4"))
        if (g.reg) solid(l, -W / 2, D - 0.8f, W / 2, D - 0.2f)
        // portão de ferro (aberto, folhas encostadas no muro)
        b.m(Mt.METAL, 1f)
        for (sg in floatArrayOf(-1f, 1f)) { p.box(sg * 3.4f, y0, mz, 0.7f, 2.6f, 0.7f, C("#CFC6B4")); p.box(sg * 3.3f, y0 + 0.1f, mz + 1.6f, 0.06f, 2.1f, 3.0f, C("#222222")) }
        // cerca viva e árvores no jardim da frente
        for (sg in floatArrayOf(-1f, 1f)) {
            for (k in 0 until 6) { val hx = sg * (W / 2 - 3f); val hz = 4f + k * (set - 6f) / 5; CityGeo.tree(g, l.wx(hx, hz), l.wz(hx, hz), r.r(0.85f, 1.1f), CURB, 4); if (g.reg) solid(l, hx - 0.3f, hz - 0.3f, hx + 0.3f, hz + 0.3f) }
            for (k in 0 until 8) { val bx = sg * (cw / 2 + 0.8f + k * 1.2f); CityGeo.bush(g, l.wx(bx, wzs - 0.9f), l.wz(bx, wzs - 0.9f), 0.7f) }
        }
        // piscina grande, deck e casa de piscina
        val pz0 = set + cd + 8f; val pz1 = min(D - 10f, pz0 + 14f); val pxw = min(W - 24f, 22f)
        if (pz1 > pz0 + 6f) {
            b.m(Mt.TILE, 0.5f); p.flat(-pxw / 2 - 3f, pz0 - 3f, pxw / 2 + 3f, pz1 + 3f, y0 + 0.02f, C("#EDE7DB"))
            b.m(Mt.PLAIN); p.flat(-pxw / 2, pz0, pxw / 2, pz1, y0 + 0.035f, C("#36A3D3"))
            b.m(Mt.STONE, 1f); p.box(0f, y0 + 0.02f, pz0 - 0.15f, pxw + 0.3f, 0.06f, 0.3f, C("#F2EEE6")); p.box(0f, y0 + 0.02f, pz1 + 0.15f, pxw + 0.3f, 0.06f, 0.3f, C("#F2EEE6"))
            // espreguiçadeiras
            b.m(Mt.FABRIC, 1f); for (k in 0 until 4) { val sx = -pxw / 2 + 2f + k * (pxw - 4f) / 3; p.box(sx, y0 + 0.25f, pz0 - 1.9f, 0.7f, 0.12f, 1.9f, C("#FFFFFF")) }
            if (D - pz1 > 9f) {
                b.m(Mt.PLASTER, 0.8f); p.box(0f, y0, pz1 + 6f, 9f, 3f, 5f, wall)
                b.m(Mt.ROOF, 0.6f); hip(p, -4.5f, 4.5f, pz1 + 3.5f, pz1 + 8.5f, y0 + 3f, 1.4f, roof, 0.4f)
                if (g.reg) solid(l, -4.5f, pz1 + 3.5f, 4.5f, pz1 + 8.5f)
            }
            CityGeo.palm(g, l.wx(-pxw / 2 - 2f, pz1 + 2f), l.wz(-pxw / 2 - 2f, pz1 + 2f), 1f)
            CityGeo.palm(g, l.wx(pxw / 2 + 2f, pz0 - 2f), l.wz(pxw / 2 + 2f, pz0 - 2f), 1f)
        }
        if (l.forSale) { b.m(Mt.PLAIN); p.box(5.5f, y0, mz - 0.6f, 1.4f, 0.8f, 0.05f, C("#C62828")); p.box(5.5f, y0 + 0.8f, mz - 0.6f, 0.08f, 0.6f, 0.08f, C("#F2F2F2")) }
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

    private fun window(p: Pen, x: Float, y: Float, z: Float, out: Float, shut: Int, shutters: Boolean) {
        p.box(x, y - 0.06f, z + out * 0.03f, 1.3f, 1.42f, 0.08f, TRIM)
        p.box(x, y, z + out * 0.07f, 1.1f, 1.3f, 0.02f, GLASSC)
        p.box(x, y + 0.62f, z + out * 0.08f, 1.1f, 0.06f, 0.03f, TRIM)
        p.box(x, y, z + out * 0.085f, 0.05f, 1.3f, 0.03f, TRIM)
        if (shutters) for (s in floatArrayOf(-1f, 1f)) p.box(x + s * 0.88f, y - 0.02f, z + out * 0.06f, 0.42f, 1.4f, 0.05f, shut)
    }

    private fun windowSide(p: Pen, x: Float, y: Float, z: Float, out: Float) {
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
