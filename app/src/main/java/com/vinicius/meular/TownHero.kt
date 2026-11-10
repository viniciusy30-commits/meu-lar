package com.vinicius.meular

import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

/**
 * Etapa 159: quarteirão de ouro. O quarteirão do canto superior esquerdo do mapa (índice HERO) recebe o acabamento máximo:
 * fachadas com calha, soleira, cortinas, caixas de flores, número da casa, luminária e vasos na porta, ar-condicionado,
 * jardim com canteiro de flores na frente, enfeites sorteados por lote, cercas baixas e vazadas (nada de muro alto escondendo a casa),
 * telhados coloridos, sobrados geminados com sacada e a pracinha de bolso.
 * Só o que está dentro deste quarteirão é desenhado assim — o resto da cidade segue como antes (o peso fica controlado).
 */
object TownHero {
    private const val CURB = Town.CURB
    const val HERO = 0
    private const val COLONIAL = 0; private const val RANCH = 1; private const val CRAFTSMAN = 2; private const val MODERN = 3; private const val SPANISH = 4; private const val CAPE = 5
    private const val OPEN = 0; private const val PICKET = 1; private const val WALL = 2; private const val IRON = 3; private const val HEDGE = 4; private const val MURETA = 5

    private val heroCache = HashMap<Int, Boolean>()
    @Synchronized fun on(l: TownHouses.Lot): Boolean = heroCache.getOrPut(System.identityHashCode(l)) {
        val bl = Town.blocks.getOrNull(HERO)
        bl != null && Town.inside(bl, l.wx(0f, l.d * 0.5f), l.wz(0f, l.d * 0.5f))
    }
    fun onXZ(x: Float, z: Float): Boolean { val bl = Town.blocks.getOrNull(HERO) ?: return false; return Town.inside(bl, x, z) }
    @Synchronized fun reset() = heroCache.clear()

    // ------------------------------------------------------------ cores e cercas

    private val ROOFS = arrayOf("#B5523B", "#8F4A36", "#5E6A75", "#4F5B66", "#6C7A64", "#7A5A44", "#8A8780", "#A9643C", "#46535F", "#9A6A4A", "#7B4B3A", "#66707A")
    fun roof(l: TownHouses.Lot, style: Int, c0: Int): Int = if (style == SPANISH || style == MODERN) c0 else C(ROOFS[Math.floorMod(l.seed * 7 + 3, ROOFS.size)])

    /** Troca o muro alto por cerca baixa e vazada (grade, mureta, ripado ou sebe). */
    fun fence(l: TownHouses.Lot, enc: Int): Int {
        if (enc != WALL) return enc
        return intArrayOf(IRON, MURETA, PICKET, HEDGE, IRON, MURETA)[Math.floorMod(l.seed * 5 + 1, 6)]
    }

    class Ctx(val style: Int, val hx0: Float, val hw: Float, val hd: Float, val set: Float, val H: Float, val wallH: Float, val floors: Int, val doorX: Float,
              val gSide: Float, val gw: Float, val gx0: Float, val gz0: Float, val dx0: Float, val dx1: Float, val wallC: Int, val roofC: Int, val trim: Int,
              val porch: Boolean, val ell: Boolean, val ex0: Float, val ew: Float, val relief: Boolean)

    private fun fl(g: CityGeo.Gen, l: TownHouses.Lot, id: String, x: Float, z: Float, y: Float, s: Float, ry: Float) =
        g.fl.place(id, l.wx(x, z).toDouble(), y.toDouble(), l.wz(x, z).toDouble(), s.toDouble(), ry.toDouble())

    private val SEG = intArrayOf(0b0111111, 0b0000110, 0b1011011, 0b1001111, 0b1100110, 0b1101101, 0b1111101, 0b0000111, 0b1111111, 0b1101111)   // g f e d c b a

    /** Número da casa em sete segmentos, centrado em (cx, y) na parede da frente. */
    private fun number(p: TownHouses.Pen, cx: Float, y: Float, z: Float, n: Int, c: Int) {
        val s = n.toString(); val sp = 0.13f; val x0 = cx - sp * (s.length - 1) / 2
        for ((k, ch) in s.withIndex()) {
            val m = SEG[ch - '0']; val dx = x0 + k * sp
            fun seg(bit: Int, ox: Float, oy: Float, w: Float, h: Float) { if (m and (1 shl bit) != 0) p.box(dx + ox, y + oy, z, w, h, 0.02f, c) }
            seg(0, 0f, 0.16f, 0.08f, 0.025f); seg(6, 0f, 0.08f, 0.08f, 0.025f); seg(3, 0f, 0f, 0.08f, 0.025f)
            seg(5, -0.045f, 0.085f, 0.025f, 0.08f); seg(4, 0.045f, 0.085f, 0.025f, 0.08f)
            seg(1, -0.045f, 0.005f, 0.025f, 0.08f); seg(2, 0.045f, 0.005f, 0.025f, 0.08f)
        }
    }

    // ------------------------------------------------------------ um lote

    fun lot(g: CityGeo.Gen, l: TownHouses.Lot, p: TownHouses.Pen, c: Ctx) {
        val h = City.Rng(l.seed * 131 + 17)
        val b = p.b; val y0 = CURB; val W = l.w; val D = l.d
        val st = c.style; val hx0 = c.hx0; val hw = c.hw; val hd = c.hd; val set = c.set; val H = c.H
        val modern = st == MODERN
        val e = when (st) { RANCH, SPANISH -> 0.6f; CAPE -> 0.35f; else -> 0.5f }
        // ---- calha e tubo de descida
        if (!modern) {
            val gc = C(arrayOf("#E9E6DF", "#3B3F44", "#8A5A3C", "#F4F1EA")[h.i(4)])
            b.m(Mt.METAL, 1f)
            p.box(hx0 + hw / 2, y0 + H - 0.1f, set - e + 0.04f, hw + 2 * e - 0.08f, 0.1f, 0.1f, gc)
            p.box(hx0 + hw / 2, y0 + H - 0.1f, set + hd + e - 0.04f, hw + 2 * e - 0.08f, 0.1f, 0.1f, gc)
            for (sx in floatArrayOf(hx0 + 0.18f, hx0 + hw - 0.18f)) {
                p.box(sx, y0 + H - 0.12f, set - e / 2, 0.08f, 0.08f, e, gc)
                p.box(sx, y0 + 0.35f, set - 0.06f, 0.08f, H - 0.45f, 0.08f, gc)
                p.box(sx, y0 + 0.28f, set - 0.14f, 0.08f, 0.08f, 0.2f, gc)
            }
        }
        // ---- janelas da frente: soleira, verga, cortinas, caixa de flores
        if (!modern) {
            val n = max(2, (hw / 3.2f).toInt())
            val stone = C("#CFC8BA"); val curt = intArrayOf(C("#F3EBD8"), C("#D9E4EA"), C("#EBD3D0"), C("#E6E1C8"), C("#CBD8C9"), C("#E9DDE9"))
            val fb = arrayOf("fl_poppy", "fl_daisy", "fl_tulip", "fl_yellow", "fl_lav")
            for (fl in 0 until c.floors) {
                val wy = y0 + 0.45f + 0.95f + fl * c.wallH
                for (k in 0 until n) {
                    val wx = hx0 + hw * (k + 0.5f) / n
                    if (fl == 0 && abs(wx - c.doorX) < 1.4f) continue
                    if (c.ell && fl == 0 && wx > c.ex0 - 0.8f && wx < c.ex0 + c.ew + 0.8f) continue
                    b.m(Mt.STONE, 1f); p.box(wx, wy - 0.13f, set - 0.1f, 1.55f, 0.07f, 0.2f, stone)
                    b.m(Mt.PLAIN)
                    val cc = curt[h.i(curt.size)]
                    p.box(wx - 0.37f, wy + 0.02f, set - 0.088f, 0.3f, 1.24f, 0.02f, cc); p.box(wx + 0.37f, wy + 0.02f, set - 0.088f, 0.3f, 1.24f, 0.02f, cc)
                    p.box(wx, wy + 1.2f, set - 0.09f, 1.1f, 0.05f, 0.03f, C("#6B4A32"))
                    if (h.chance(0.55f)) {
                        b.m(Mt.WOOD, 0.6f); p.box(wx, wy - 0.46f, set - 0.22f, 1.25f, 0.3f, 0.28f, C("#7A5638"))
                        b.m(Mt.GRASS, 0.3f); p.box(wx, wy - 0.18f, set - 0.22f, 1.17f, 0.03f, 0.22f, C("#3E5F2C"))
                        val id = fb[h.i(fb.size)]
                        for (q in 0 until 4) fl(g, l, id, wx - 0.45f + q * 0.3f, set - 0.22f, wy - 0.16f, 0.85f, q * 1.7f)
                    }
                }
            }
        }
        // ---- porta: número, luminária, vasos
        val porchY = if (c.porch) 0.45f else if (st == SPANISH || modern) 0f else 0.3f
        b.m(Mt.PLAIN)
        val plX = c.doorX + (if (modern) 1.1f else 1.0f)
        p.box(plX, y0 + 1.5f, set - 0.05f, 0.52f, 0.32f, 0.04f, if (h.chance(0.5f)) C("#2B2B2B") else C("#F2EFE8"))
        number(p, plX, y0 + 1.58f, set - 0.075f, 10 + Math.floorMod(l.seed * 37, 989), C("#C9A227"))
        val lampX = c.doorX - (if (modern) 1.1f else 1.0f)
        b.m(Mt.METAL, 1f); p.box(lampX, y0 + 1.95f, set - 0.1f, 0.14f, 0.26f, 0.12f, C("#26282B"))
        b.m(Mt.PLAIN); p.box(lampX, y0 + 2.02f, set - 0.11f, 0.1f, 0.16f, 0.1f, C("#FFE9A8"), )
        for (sg in floatArrayOf(-1f, 1f)) {
            val px = c.doorX + sg * 1.25f
            if (c.ell && px > c.ex0 - 0.3f && px < c.ex0 + c.ew + 0.3f) continue
            b.m(Mt.STONE, 0.6f); p.cyl(px, y0 + porchY, set - 0.6f, 0.2f, 0.4f, C(arrayOf("#B8613F", "#A5532F", "#C77A52")[h.i(3)]), 10)
            fl(g, l, if (h.chance(0.5f)) "bush_b" else "bush_a", px, set - 0.6f, y0 + porchY + 0.36f, 0.3f, h.r(0f, 6f))
        }
        // ---- ar-condicionado na lateral + condensadora no chão
        val open = if (c.gSide > 0) -1f else 1f
        val sx = if (open < 0) hx0 else hx0 + hw
        if (h.chance(0.8f)) {
            val az = set + hd * 0.5f
            b.m(Mt.PLAIN); p.box(sx + open * 0.1f, y0 + 2.05f, az, 0.2f, 0.3f, 0.9f, C("#EEF0F1")); p.box(sx + open * 0.2f, y0 + 2.12f, az, 0.02f, 0.03f, 0.7f, C("#B9BEC2"))
            b.m(Mt.METAL, 1f); p.box(sx + open * 0.5f, y0, az + 0.3f, 0.35f, 0.62f, 0.8f, C("#D4D7DA"))
            p.box(sx + open * 0.69f, y0 + 0.08f, az + 0.3f, 0.03f, 0.46f, 0.66f, C("#8B9096"))
            b.m(Mt.PLAIN); p.cyl(sx + open * 0.5f, y0 + 0.62f, az + 0.3f, 0.12f, 0.02f, C("#3B3F44"), 8)
            if (g.reg) TownHouses.solid(l, min(sx, sx + open * 0.8f), az - 0.2f, max(sx, sx + open * 0.8f), az + 0.8f)
        }
        // ---- garagem: lâmpada sobre o portão
        if (c.gw > 0f && st != MODERN) {
            b.m(Mt.METAL, 1f); p.box(c.gx0 + c.gw / 2, y0 + 2.9f, c.gz0 - 0.14f, 0.16f, 0.2f, 0.14f, C("#26282B"))
            b.m(Mt.PLAIN); p.box(c.gx0 + c.gw / 2, y0 + 2.95f, c.gz0 - 0.2f, 0.1f, 0.12f, 0.06f, C("#FFE9A8"))
        }
        // ---- jardim da frente
        val zMax = max(1.4f, set - 1.8f); val xl = -W / 2 + 0.7f; val xr = W / 2 - 0.7f
        val treeX = if (c.gSide > 0) -W / 2 + 3f else W / 2 - 3f
        fun ok(x: Float, z: Float, r: Float): Boolean {
            if (abs(x - c.doorX) < 1.5f + r && z > 1.0f) return false
            if (c.gw > 0f && x > c.dx0 - 0.5f - r && x < c.dx1 + 0.5f + r) return false
            if (abs(x - treeX) < 1.3f + r && abs(z - set * 0.45f) < 1.3f + r) return false
            if (x > hx0 - 0.4f - r && x < hx0 + hw + 0.4f + r && z > set - 2.0f - r) return false
            return true
        }
        // faixa de flores junto da cerca
        val sp = arrayOf("fl_daisy", "fl_lav", "fl_poppy", "fl_tulip", "fl_yellow"); val s1 = sp[h.i(5)]; val s2 = sp[h.i(5)]
        var fx = xl; var q = 0
        while (fx < xr) {
            if (ok(fx, 1.0f, 0.3f) && !h.chance(0.15f)) fl(g, l, if (q % 2 == 0) s1 else s2, fx + h.r(-0.1f, 0.1f), h.r(0.8f, 1.35f), CURB, h.r(1.0f, 1.4f), h.r(0f, 6f))
            fx += 0.62f; q++
        }
        // bolinhas de luz ao longo da calçadinha da porta
        b.m(Mt.METAL, 1f)
        var zz = 1.6f; while (zz < set - 1.3f) { for (sg in floatArrayOf(-0.85f, 0.85f)) { p.cyl(c.doorX + sg, y0, zz, 0.03f, 0.42f, C("#2E3236"), 6); b.m(Mt.PLAIN); p.cyl(c.doorX + sg, y0 + 0.42f, zz, 0.06f, 0.07f, C("#FFF0C0"), 8); b.m(Mt.METAL, 1f) }; zz += 1.4f }
        // enfeites sorteados (dois por lote, nunca iguais nos vizinhos)
        val kinds = IntArray(2); kinds[0] = Math.floorMod(l.seed, 9); kinds[1] = (kinds[0] + 3 + h.i(5)) % 9
        for (k in kinds) {
            var x = 0f; var z = 0f; var found = false
            for (t in 0 until 16) { x = h.r(xl, xr); z = h.r(1.5f, zMax); if (ok(x, z, 0.8f)) { found = true; break } }
            if (!found) continue
            ornament(g, l, p, k, x, z, h)
        }
    }

    private fun ornament(g: CityGeo.Gen, l: TownHouses.Lot, p: TownHouses.Pen, kind: Int, x: Float, z: Float, h: City.Rng) {
        val b = p.b; val y0 = CURB
        when (kind) {
            0 -> { // bebedouro de passarinho
                b.m(Mt.STONE, 1f); p.cyl(x, y0, z, 0.16f, 0.12f, C("#BDB6A8"), 10); p.cyl(x, y0 + 0.12f, z, 0.07f, 0.5f, C("#CFC8BA"), 8); p.cyl(x, y0 + 0.62f, z, 0.34f, 0.1f, C("#CFC8BA"), 14)
                b.m(Mt.PLAIN); p.cyl(x, y0 + 0.71f, z, 0.29f, 0.02f, C("#7FB2D6"), 14) }
            1 -> { // gnomo
                val wx = l.wx(x, z); val wz = l.wz(x, z)
                b.m(Mt.PLAIN); b.cyl(wx, y0, wz, 0.07f, 0.07f, 0.06f, C("#3A2A1E"), true, 8); b.cyl(wx, y0 + 0.06f, wz, 0.09f, 0.07f, 0.22f, C("#2F5FA8"), true, 8)
                b.sphere(wx, y0 + 0.34f, wz, 0.07f, C("#E8B896"), 0.07f, 8); b.sphere(wx, y0 + 0.27f, wz, 0.075f, C("#F2F2F2"), 0.06f, 8); b.cyl(wx, y0 + 0.36f, wz, 0.075f, 0.005f, 0.22f, C("#C62828"), true, 8) }
            2 -> { // banco de jardim
                b.m(Mt.WOOD, 0.6f); p.box(x, y0 + 0.42f, z, 1.3f, 0.06f, 0.45f, C("#8D6E4C")); p.box(x, y0 + 0.72f, z + 0.2f, 1.3f, 0.4f, 0.05f, C("#8D6E4C"))
                b.m(Mt.METAL, 1f); for (o in floatArrayOf(-0.55f, 0.55f)) { p.box(x + o, y0, z, 0.06f, 0.42f, 0.4f, C("#2E3236")); p.box(x + o, y0 + 0.42f, z + 0.2f, 0.06f, 0.7f, 0.06f, C("#2E3236")) }
                if (g.reg) TownHouses.solid(l, x - 0.7f, z - 0.3f, x + 0.7f, z + 0.3f) }
            3 -> { // barril de chuva (cisterna)
                b.m(Mt.METAL, 1f); p.cyl(x, y0, z, 0.32f, 0.85f, C("#2F5F8A"), 12); p.cyl(x, y0 + 0.85f, z, 0.34f, 0.05f, C("#24496A"), 12)
                p.cyl(x, y0 + 0.25f, z, 0.335f, 0.04f, C("#1E3F5C"), 12); p.cyl(x, y0 + 0.6f, z, 0.335f, 0.04f, C("#1E3F5C"), 12)
                if (g.reg) TownHouses.solid(l, x - 0.35f, z - 0.35f, x + 0.35f, z + 0.35f) }
            4 -> { // carrinho de mão com flores
                b.m(Mt.METAL, 1f); p.box(x, y0 + 0.3f, z, 0.62f, 0.26f, 0.9f, C("#2F7D4F")); p.cyl(x, y0, z + 0.62f, 0.14f, 0.28f, C("#26282B"), 8)
                p.box(x - 0.3f, y0 + 0.18f, z - 0.55f, 0.04f, 0.04f, 0.5f, C("#8D6E4C")); p.box(x + 0.3f, y0 + 0.18f, z - 0.55f, 0.04f, 0.04f, 0.5f, C("#8D6E4C"))
                b.m(Mt.GRASS, 0.3f); p.box(x, y0 + 0.54f, z, 0.54f, 0.03f, 0.82f, C("#3B2A1C"))
                val id = arrayOf("fl_tulip", "fl_poppy", "fl_yellow")[h.i(3)]; for (q in 0 until 5) fl(g, l, id, x + h.r(-0.2f, 0.2f), z + h.r(-0.3f, 0.3f), y0 + 0.55f, 0.9f, q * 1.1f) }
            5 -> { // enrolador de mangueira
                b.m(Mt.METAL, 1f); p.cyl(x, y0, z, 0.12f, 0.1f, C("#3B3F44"), 8); p.cyl(x, y0 + 0.1f, z, 0.26f, 0.3f, C("#2F9E5A"), 14); p.cyl(x, y0 + 0.1f, z, 0.1f, 0.3f, C("#1E6B3B"), 8); p.cyl(x, y0 + 0.4f, z, 0.28f, 0.03f, C("#26282B"), 14) }
            6 -> { // vasos de terracota empilhados + regador
                b.m(Mt.STONE, 0.6f); for (k in 0 until 3) p.cyl(x - 0.25f + k * 0.28f, y0, z, 0.17f, 0.3f - k * 0.04f, C(arrayOf("#B8613F", "#C77A52", "#A5532F")[k]), 10)
                p.cyl(x - 0.05f, y0 + 0.3f, z, 0.14f, 0.24f, C("#C77A52"), 10)
                b.m(Mt.METAL, 1f); p.cyl(x + 0.6f, y0, z + 0.1f, 0.11f, 0.22f, C("#4AA36B"), 10); p.box(x + 0.72f, y0 + 0.2f, z + 0.1f, 0.2f, 0.03f, 0.03f, C("#4AA36B")) }
            7 -> { // mastro com bandeira
                b.m(Mt.METAL, 1f); p.cyl(x, y0, z, 0.03f, 3.2f, C("#D8D8D8"), 6); b.m(Mt.PLAIN); p.box(x + 0.32f, y0 + 2.7f, z, 0.6f, 0.4f, 0.015f, C("#1B8A3A")); p.box(x + 0.32f, y0 + 2.9f, z - 0.01f, 0.22f, 0.12f, 0.015f, C("#F2D21B"))
                if (g.reg) TownHouses.solid(l, x - 0.1f, z - 0.1f, x + 0.1f, z + 0.1f) }
            else -> { // canteiro de pedra com arbusto e lavanda
                b.m(Mt.STONE, 0.6f); val r = 0.7f
                p.box(x, y0, z - r, 2 * r, 0.22f, 0.12f, C("#B7B0A2")); p.box(x, y0, z + r, 2 * r, 0.22f, 0.12f, C("#B7B0A2")); p.box(x - r, y0, z, 0.12f, 0.22f, 2 * r, C("#B7B0A2")); p.box(x + r, y0, z, 0.12f, 0.22f, 2 * r, C("#B7B0A2"))
                b.m(Mt.GRASS, 0.3f); p.box(x, y0, z, 2 * r - 0.1f, 0.2f, 2 * r - 0.1f, C("#4A3626"))
                fl(g, l, "bush_pink", x, z, y0 + 0.18f, 0.5f, h.r(0f, 6f)); for (q in 0 until 6) fl(g, l, "fl_lav", x + cos(q * 1.05f) * 0.45f, z + sin(q * 1.05f) * 0.45f, y0 + 0.18f, 1f, q.toFloat()) }
        }
    }

    // ------------------------------------------------------------ terrenos pequenos do quarteirão

    fun infill(g: CityGeo.Gen, f: TownSmall.F, r: City.Rng, west: Boolean): Float = if (west) sobrados(g, f, r) else pracinha(g, f, r)

    /** Sobrados geminados brasileiros: térreo com garagem e porta, sacada com guarda-corpo no andar de cima, platibanda, caixa d'água. */
    private fun sobrados(g: CityGeo.Gen, f: TownSmall.F, r: City.Rng): Float {
        val b = g.b; val W = f.W; val D = f.D
        val n = 4; val uw = (W - 1f) / n; val dep = min(D - 5f, 11f); val v0 = 3.5f
        val cols = arrayOf("#E9DFC9", "#C98F6B", "#B9C9D3", "#E8C9C0", "#D6DDB8", "#F1EBDD", "#C7B8D6")
        var last = -1
        for (k in 0 until n) {
            val uc = 0.5f + uw * (k + 0.5f)
            var ci = r.i(cols.size); if (ci == last) ci = (ci + 1) % cols.size; last = ci
            val col = C(cols[ci]); val h = 6.3f
            b.m(Mt.PLASTER, 0.7f); f.box(b, uc, CURB, v0 + dep / 2, uw - 0.06f, h, dep, col)
            b.m(Mt.STONE, 1f); f.box(b, uc, CURB, v0 - 0.02f, uw - 0.06f, 0.5f, 0.06f, C("#8C857A"))
            b.m(Mt.PLASTER, 0.5f); f.box(b, uc, CURB + h, v0 + dep / 2, uw + 0.1f, 0.35f, dep + 0.2f, shade(col, -30)); f.box(b, uc, CURB + h + 0.35f, v0 - 0.05f, uw - 0.06f, 0.7f, 0.2f, shade(col, -12))
            b.m(Mt.PLAIN)
            val gate = k % 2 == 0
            val dc = C(arrayOf("#8E1B1B", "#1F3A5F", "#222222", "#5A3A22", "#2E5E3A")[r.i(5)])
            val du = if (gate) uc + uw * 0.2f else uc - uw * 0.2f
            f.box(b, du, CURB + 0.2f, v0 - 0.06f, 1.0f, 2.2f, 0.1f, dc); f.box(b, du, CURB + 0.2f, v0 - 0.1f, 1.3f, 2.4f, 0.04f, C("#F2EEE6"))
            val gu = if (gate) uc - uw * 0.22f else uc + uw * 0.22f
            f.box(b, gu, CURB + 0.1f, v0 - 0.06f, uw * 0.38f, 2.2f, 0.08f, C("#3B3F44"))
            for (q in 0..6) f.box(b, gu - uw * 0.17f + q * uw * 0.057f, CURB + 0.1f, v0 - 0.1f, 0.03f, 2.2f, 0.03f, C("#26282B"))
            // janelas do térreo e do andar de cima + sacada
            val up = CURB + 3.4f
            f.box(b, uc, up, v0 - 0.06f, uw * 0.6f, 2.3f, 0.08f, C("#4E6A7E")); f.box(b, uc, up, v0 - 0.1f, uw * 0.6f + 0.2f, 0.12f, 0.04f, C("#F2EEE6")); f.box(b, uc, up + 2.3f, v0 - 0.1f, uw * 0.6f + 0.2f, 0.12f, 0.04f, C("#F2EEE6"))
            f.box(b, uc, up, v0 - 0.12f, 0.06f, 2.3f, 0.04f, C("#F2EEE6"))
            f.box(b, uc - uw * 0.2f, up + 0.1f, v0 - 0.14f, 0.3f, 2.0f, 0.02f, C("#F3EBD8")); f.box(b, uc + uw * 0.2f, up + 0.1f, v0 - 0.14f, 0.3f, 2.0f, 0.02f, C("#F3EBD8"))
            b.m(Mt.STONE, 0.5f); f.box(b, uc, CURB + 3.25f, v0 - 0.65f, uw - 0.4f, 0.16f, 1.3f, C("#EDE8DE"))
            b.m(Mt.METAL, 1f); f.box(b, uc, CURB + 3.41f, v0 - 1.25f, uw - 0.45f, 0.06f, 0.05f, C("#26282B")); f.box(b, uc, CURB + 4.3f, v0 - 1.25f, uw - 0.45f, 0.06f, 0.05f, C("#26282B"))
            var q = -uw / 2 + 0.35f; while (q < uw / 2 - 0.3f) { f.box(b, uc + q, CURB + 3.41f, v0 - 1.25f, 0.035f, 0.9f, 0.035f, C("#26282B")); q += 0.17f }
            // vaso na sacada
            b.m(Mt.STONE, 0.6f); f.box(b, uc + uw * 0.3f, CURB + 3.41f, v0 - 0.9f, 0.4f, 0.35f, 0.4f, C("#B8613F"))
            g.fl.place("bush_a", f.x(uc + uw * 0.3f, v0 - 0.9f).toDouble(), (CURB + 3.76f).toDouble(), f.z(uc + uw * 0.3f, v0 - 0.9f).toDouble(), 0.35, k.toDouble())
            // janela do térreo
            // caixa d'água redonda no telhado
            b.m(Mt.METAL, 1f); b.cyl(f.x(uc, v0 + dep * 0.6f), CURB + h + 0.35f, f.z(uc, v0 + dep * 0.6f), 0.6f, 0.58f, 0.95f, C(arrayOf("#2F6FA8", "#D8DCDF", "#1E6B8A")[r.i(3)]), true, 12)
            b.cyl(f.x(uc, v0 + dep * 0.6f), CURB + h + 1.3f, f.z(uc, v0 + dep * 0.6f), 0.62f, 0.62f, 0.07f, C("#9AA0A6"), true, 12)
            // numero, luminária, medidor
            b.m(Mt.PLAIN); f.box(b, du + 0.9f, CURB + 1.5f, v0 - 0.07f, 0.5f, 0.3f, 0.04f, C("#2B2B2B"))
            f.box(b, du - 0.85f, CURB + 2.0f, v0 - 0.1f, 0.12f, 0.2f, 0.1f, C("#FFE9A8"))
            // degrau de pedra + planta
            b.m(Mt.STONE, 1f); f.box(b, du, CURB, v0 - 0.7f, 1.7f, 0.2f, 1.2f, C("#B8B3AA"))
            if (r.chance(0.7f)) g.fl.place("bush_b", f.x(du + 1.3f, 0.9f).toDouble(), CURB.toDouble(), f.z(du + 1.3f, 0.9f).toDouble(), 0.5, k.toDouble())
        }
        f.solid(g, 0.5f, v0, W - 0.5f, v0 + dep)
        // calçada interna e muretinha com pilares na frente, jardineiras
        b.m(Mt.PAVER, 0.6f); f.box(b, W / 2, CURB, v0 / 2, W - 0.4f, 0.02f, v0 - 0.2f, C("#CFC9BD"))
        b.m(Mt.STONE, 0.7f); f.box(b, W / 2, CURB, 0.4f, W - 0.6f, 0.45f, 0.22f, C("#CFC8BA"))
        for (k in 0..n) f.box(b, 0.5f + uw * k, CURB, 0.4f, 0.32f, 0.9f, 0.32f, C("#BDB6A8"))
        return 8f
    }

    /** Pracinha de bolso: piso de pedra, canteiros, banco, bebedouro, balanços, caixa de areia e árvores. */
    private fun pracinha(g: CityGeo.Gen, f: TownSmall.F, r: City.Rng): Float {
        val b = g.b; val W = f.W; val D = f.D
        b.m(Mt.PAVER, 0.6f); f.box(b, W / 2, CURB, D / 2, W - 0.6f, 0.02f, D - 0.6f, C("#DDD3C0"))
        b.m(Mt.GRASS, 0.3f); f.box(b, W * 0.27f, CURB, D * 0.7f, W * 0.46f, 0.04f, D * 0.5f, C("#CFE8BC")); f.box(b, W * 0.8f, CURB, D * 0.6f, W * 0.3f, 0.04f, D * 0.6f, C("#CFE8BC"))
        // meio-fio dos canteiros
        b.m(Mt.STONE, 1f)
        for (sgn in floatArrayOf(0.27f, 0.8f)) { val cw = if (sgn < 0.5f) W * 0.46f else W * 0.3f; val cd = if (sgn < 0.5f) D * 0.5f else D * 0.6f; val cv = if (sgn < 0.5f) D * 0.7f else D * 0.6f
            f.box(b, W * sgn, CURB, cv - cd / 2, cw, 0.1f, 0.1f, C("#BDB6A8")); f.box(b, W * sgn, CURB, cv + cd / 2, cw, 0.1f, 0.1f, C("#BDB6A8")) }
        // balanços
        val sx = W * 0.8f; val sv = D * 0.6f
        b.m(Mt.METAL, 1f)
        for (o in floatArrayOf(-1.6f, 1.6f)) { f.box(b, sx + o, CURB, sv - 0.5f, 0.1f, 2.4f, 0.1f, C("#C62828")); f.box(b, sx + o, CURB, sv + 0.5f, 0.1f, 2.4f, 0.1f, C("#C62828")) }
        f.box(b, sx, CURB + 2.35f, sv, 3.5f, 0.1f, 0.1f, C("#C62828"))
        for (o in floatArrayOf(-0.7f, 0.7f)) { f.box(b, sx + o - 0.25f, CURB + 0.6f, sv, 0.015f, 1.75f, 0.015f, C("#6E7378")); f.box(b, sx + o + 0.25f, CURB + 0.6f, sv, 0.015f, 1.75f, 0.015f, C("#6E7378")); b.m(Mt.WOOD, 0.6f); f.box(b, sx + o, CURB + 0.55f, sv, 0.6f, 0.06f, 0.25f, C("#E0A32E")); b.m(Mt.METAL, 1f) }
        f.solid(g, sx - 2f, sv - 0.7f, sx + 2f, sv + 0.7f)
        // caixa de areia
        b.m(Mt.WOOD, 0.6f); val ax = W * 0.5f; val av = D * 0.35f
        f.box(b, ax, CURB, av - 1.0f, 2.2f, 0.25f, 0.12f, C("#8D6E4C")); f.box(b, ax, CURB, av + 1.0f, 2.2f, 0.25f, 0.12f, C("#8D6E4C")); f.box(b, ax - 1.05f, CURB, av, 0.12f, 0.25f, 2.0f, C("#8D6E4C")); f.box(b, ax + 1.05f, CURB, av, 0.12f, 0.25f, 2.0f, C("#8D6E4C"))
        b.m(Mt.PAVER, 0.4f); f.box(b, ax, CURB, av, 2.0f, 0.18f, 1.9f, C("#E6D3A3"))
        // banco, bebedouro, postes de luz
        CityGeo.publicBench(b, f.x(W * 0.2f, D * 0.3f), f.z(W * 0.2f, D * 0.3f), f.fx, f.fz)
        b.m(Mt.STONE, 1f); f.box(b, W * 0.08f, CURB, D * 0.25f, 0.35f, 0.95f, 0.35f, C("#9AA3AB")); b.m(Mt.METAL, 1f); f.box(b, W * 0.08f, CURB + 0.95f, D * 0.25f, 0.2f, 0.08f, 0.2f, C("#5C6166"))
        for (k in 0..2) { val lx = W * (0.15f + 0.35f * k); val wx = f.x(lx, D * 0.88f); val wz = f.z(lx, D * 0.88f)
            b.m(Mt.METAL, 1f); b.cyl(wx, CURB, wz, 0.05f, 0.04f, 3.2f, C("#2E3236"), true, 6); b.m(Mt.PLAIN); b.sphere(wx, CURB + 3.35f, wz, 0.2f, C("#FFF0C0"), 0.2f, 8) }
        // árvores e flores
        for (k in 0..3) { val tx = f.x(W * (0.12f + 0.25f * k + (k % 2) * 0.05f), D * 0.55f); val tz = f.z(W * (0.12f + 0.25f * k + (k % 2) * 0.05f), D * 0.55f)
            if (k != 3) { CityGeo.tree(g, tx, tz, r.r(0.75f, 0.95f)); g.solid(tx - 0.3f, tz - 0.3f, tx + 0.3f, tz + 0.3f) } }
        val sp = arrayOf("fl_daisy", "fl_lav", "fl_poppy", "fl_tulip", "fl_yellow")
        for (k in 0 until 60) { val u = W * r.r(0.06f, 0.5f); val v = D * r.r(0.46f, 0.94f); g.fl.place(sp[(k / 12) % 5], f.x(u, v).toDouble(), (CURB + 0.04f).toDouble(), f.z(u, v).toDouble(), r.r(1.0f, 1.5f).toDouble(), r.r(0f, 6f).toDouble()) }
        for (k in 0 until 6) { val u = W * (0.08f + 0.08f * k); g.fl.place(if (k % 2 == 0) "bush_pink" else "bush_white", f.x(u, D * 0.93f).toDouble(), CURB.toDouble(), f.z(u, D * 0.93f).toDouble(), 0.7, k.toDouble()) }
        return 4f
    }
}
