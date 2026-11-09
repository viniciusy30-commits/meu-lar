package com.vinicius.meular

import kotlin.math.max
import kotlin.math.min

/**
 * Etapa 139: quarteirão urbano denso (estilo Nova York / Los Angeles).
 * Prédios colados em volta do quarteirão, com a fachada alinhada na calçada; cada frente é dividida em lotes de largura sorteada
 * e cada lote ganha um prédio próprio (tipo, altura, material, cor, térreo, cobertura). Esquinas com prédios mais altos.
 * No miolo: pátio (jardim, estacionamento, piscina, quadra ou playground).
 */
object TownBlock {
    private const val CURB = Town.CURB

    private val FACADES = arrayOf("#E8E1D3", "#D9D4CA", "#C9B8A3", "#B7C3C9", "#E3D5C1", "#A9A39A", "#EDE8DF", "#D6C7B2", "#BFC7CE", "#E9DCCB", "#C7BBA8", "#DDE3E6", "#CDBFAE", "#E4E0D6")
    private val BRICKS = arrayOf("#9C5A3C", "#A86B4F", "#8A4B36", "#B07A5E", "#7E4A3A", "#C08A6A", "#8F5A47", "#6E3B2E")
    private val GLASS = arrayOf("#4F6E86", "#3F5F6E", "#5E7F8F", "#2F4A5E", "#6F8C99", "#3E5A4E", "#55707F", "#2B3F52")
    private val SIGNS = intArrayOf(1, 2, 4, 5, 7, 8, 13, 14, 15, 16, 17, 18, 19, 22, 23, 34, 35, 36, 37, 38, 39, 40)

    fun build(g: CityGeo.Gen, u: Town.Urban, ui: Int): Float {
        val r = City.Rng(ui * 92821 + 17)
        val d = TownPlan.districtAt((u.x0 + u.x1) / 2, (u.z0 + u.z1) / 2)
        val W = u.x1 - u.x0; val Dp = u.z1 - u.z0
        val b = g.b
        CityGeo.groundBox(b, u.x0, u.z0, u.x1, u.z1, Mt.PAVER, 0.8f, C("#E3E0DA"))
        CityGeo.groundBox(g.f, u.x0, u.z0, u.x1, u.z1, Mt.PAVER, 0.8f, C("#E3E0DA"))
        val dd = (min(W, Dp) * 0.3f).coerceIn(12f, if (d == TownPlan.DOWN) 26f else 20f)
        // faixas das 4 frentes (as de cima e de baixo ocupam as quinas)
        val strips = arrayOf(
            floatArrayOf(u.x0, u.z0, u.x1, u.z0 + dd, 0f),
            floatArrayOf(u.x1 - dd, u.z0 + dd, u.x1, u.z1 - dd, 1f),
            floatArrayOf(u.x0, u.z1 - dd, u.x1, u.z1, 2f),
            floatArrayOf(u.x0, u.z0 + dd, u.x0 + dd, u.z1 - dd, 3f))
        var top = 0f
        for (st in strips) {
            val side = st[4].toInt()
            // Etapa 146: lado que não dá para rua (vizinho de outro lote) fica sem fachada
            val mx = when (side) { 1 -> u.x1 + 2.5f; 3 -> u.x0 - 2.5f; else -> (u.x0 + u.x1) / 2 }; val mz = when (side) { 0 -> u.z0 - 2.5f; 2 -> u.z1 + 2.5f; else -> (u.z0 + u.z1) / 2 }
            if (Town.clearance(mx, mz) > 1f) continue
            val sf = TownSmall.F(st[0], st[1], st[2], st[3], side)
            val L = sf.W
            if (L < 6f) continue
            // divide a frente em lotes
            val minW = when (d) { TownPlan.DOWN -> 16f; TownPlan.COM -> 12f; else -> 7f }
            val maxW = when (d) { TownPlan.DOWN -> 34f; TownPlan.COM -> 26f; else -> 20f }
            val cuts = ArrayList<Float>(); cuts.add(0f)
            var a = 0f
            while (L - a > maxW) { val w = r.r(minW, maxW); if (L - a - w < minW) break; a += w; cuts.add(a) }
            cuts.add(L)
            for (k in 0 until cuts.size - 1) {
                val ua = cuts[k]; val ub = cuts[k + 1]
                val corner = (side == 0 || side == 2) && (k == 0 || k == cuts.size - 2)
                // retângulo do lote no mundo
                val ax = sf.x(ua, 0f); val az = sf.z(ua, 0f); val bx = sf.x(ub, sf.D); val bz = sf.z(ub, sf.D)
                val pf = TownSmall.F(min(ax, bx), min(az, bz), max(ax, bx), max(az, bz), side)
                val h = building(g, pf, d, corner, City.Rng(ui * 7177 + side * 131 + k * 17 + 3), if (!corner) -1 else if (k == 0) 0 else 1)
                top = max(top, h)
            }
        }
        // miolo
        val ix0 = u.x0 + dd + 1f; val ix1 = u.x1 - dd - 1f; val iz0 = u.z0 + dd + 1f; val iz1 = u.z1 - dd - 1f
        if (ix1 - ix0 > 8f && iz1 - iz0 > 8f) court(g, ix0, iz0, ix1, iz1, r)
        return top + 3f
    }

    /** Prédio de um lote: frente em v = 0 (alinhada na calçada). Devolve a altura. */
    private fun building(g: CityGeo.Gen, f: TownSmall.F, d: Int, corner: Boolean, r: City.Rng, cEnd: Int = -1): Float {
        val b = g.b; val W = f.W; val Dp = f.D
        val fh = r.r(3.0f, 3.5f)
        val floors = when (d) {
            TownPlan.DOWN -> (if (corner) r.i(30) + 18 else r.i(26) + 8)
            TownPlan.COM -> (if (corner) 4 + r.i(5) else 2 + r.i(4))
            else -> (if (corner) 6 + r.i(5) else 3 + r.i(6))
        }
        val kind = when (d) {
            TownPlan.DOWN -> intArrayOf(3, 2, 3, 0, 5, 2, 3)[r.i(7)]
            TownPlan.COM -> intArrayOf(0, 1, 2, 0, 4, 1)[r.i(6)]
            else -> if (W < 11f) 4 else intArrayOf(0, 1, 1, 0, 4, 5, 2, 1)[r.i(8)]
        }
        val gh = 4.2f                                   // térreo
        val H = gh + floors * fh
        val dep = Dp
        val shopGround = kind != 4 && (d != TownPlan.URB || r.chance(0.6f) || corner)
        val tw = d == TownPlan.DOWN && (kind == 2 || kind == 3)   // Etapa 149: arranha-céu com desenho próprio
        // ---- longe
        val col = when (kind) { 1 -> C(BRICKS[r.i(BRICKS.size)]); 2, 3 -> C(GLASS[r.i(GLASS.size)]); else -> C(FACADES[r.i(FACADES.size)]) }
        if (!tw) {
            g.f.m(if (kind == 2 || kind == 3) Mt.METAL else Mt.FACADE, if (kind == 2 || kind == 3) 1f else 1f / 3f)
            f.box(g.f, W / 2, CURB, dep / 2, W - 0.1f, H, dep, col)
        } else { g.f.m(Mt.STONE, 0.6f); f.box(g.f, W / 2, CURB, dep / 2, W - 0.1f, gh, dep, C("#8C8F94")) }
        if (g.reg) f.solid(g, 0.05f, 0f, W - 0.05f, dep)
        // ---- térreo
        if (shopGround) {
            val gcol = C(arrayOf("#5F6368", "#8C8F94", "#3E4247", "#B0A99F", "#2E3135", "#E2DCCF", "#6B4A32")[r.i(7)])
            b.m(Mt.PLASTER, 0.5f); f.box(b, W / 2, CURB, dep / 2, W - 0.1f, gh, dep, gcol)
            b.m(Mt.PLAIN)
            val nv = max(1, (W / 4.5f).toInt())
            for (k in 0 until nv) {
                val wu = W * (k + 0.5f) / nv; val ww = W / nv - 0.7f
                f.box(b, wu, CURB + 0.25f, -0.03f, ww + 0.16f, 3.3f, 0.07f, C("#2B2E31"))           // caixilho
                f.box(b, wu, CURB + 0.35f, -0.07f, ww - 0.1f, 3.1f, 0.02f, C(arrayOf("#4C6B7D", "#3E5A6B", "#56788A")[r.i(3)]))   // vidro escuro
                f.box(b, wu, CURB + 2.6f, -0.09f, ww - 0.1f, 0.05f, 0.03f, C("#2B2E31"))
                if (k == nv / 2) f.box(b, wu, CURB + 0.35f, -0.1f, 0.05f, 2.25f, 0.03f, C("#2B2E31"))
            }
            if (r.chance(0.6f)) {   // toldo e letreiro
                val aw = C(arrayOf("#C62828", "#1565C0", "#2E7D32", "#F9A825", "#6A1B9A", "#EF6C00", "#00838F", "#37474F", "#5D4037")[r.i(9)])
                b.m(Mt.FABRIC, 1f); f.box(b, W / 2, CURB + 3.5f, -0.75f, W - 0.8f, 0.1f, 1.5f, aw)
                CityGeo.sign(b, f.x(W / 2, -0.12f), CURB + 3.75f, f.z(W / 2, -0.12f), f.fx, f.fz, min(W - 1.2f, 8f), 0.7f, SIGNS[r.i(SIGNS.size)])
            } else { b.m(Mt.METAL, 1f); f.box(b, W / 2, CURB + 3.6f, -0.6f, W - 0.6f, 0.14f, 1.2f, C("#3B3F44")) }
        } else {
            b.m(Mt.STONE, 0.6f); f.box(b, W / 2, CURB, dep / 2, W - 0.1f, gh, dep, shade(col, -20))
            b.m(Mt.PLAIN); f.box(b, W / 2, CURB + 0.2f, -0.04f, 1.6f, 2.6f, 0.06f, C("#3B2A1E"))
            b.m(Mt.STONE, 0.8f); f.box(b, W / 2, CURB, -0.7f, 2.4f, 0.4f, 1.3f, C("#B8B3AA"))
        }
        // ---- quina: a lateral que dá para a rua transversal também tem vitrine/janelas
        if (cEnd >= 0) {
            val su = if (cEnd == 0) -0.04f else W + 0.04f
            b.m(Mt.PLAIN)
            val nv2 = max(1, (dep / 4.5f).toInt())
            for (k in 0 until nv2) {
                val vc = dep * (k + 0.5f) / nv2
                f.box(b, su, CURB + 0.25f, vc, 0.07f, 3.3f, dep / nv2 - 0.6f, C("#2B2E31"))
                f.box(b, su + (if (cEnd == 0) -0.04f else 0.04f), CURB + 0.35f, vc, 0.02f, 3.1f, dep / nv2 - 0.8f, C("#4C6B7D"))
                if (kind == 1) for (fl in 0 until floors) f.box(b, su, CURB + gh + fl * fh + 0.8f, vc, 0.08f, 1.6f, 1.05f, C("#3E4C57"))
            }
        }
        // ---- corpo
        val y1 = CURB + gh
        if (tw) return tower(g, f, r, W, dep, floors + (if (corner) 6 else 0), y1)
        when (kind) {
            1 -> { // tijolo com janelas em grade, cornija e escada de incêndio
                b.m(Mt.STONE, 0.45f); f.box(b, W / 2, y1, dep / 2, W - 0.1f, floors * fh, dep, col)
                b.m(Mt.PLAIN)
                val nw = max(2, (W / 2.6f).toInt())
                for (fl in 0 until floors) for (k in 0 until nw) {
                    val wu = W * (k + 0.5f) / nw; val wy = y1 + fl * fh + 0.8f
                    f.box(b, wu, wy - 0.12f, -0.05f, 1.25f, 0.12f, 0.12f, C("#D9D2C2"))
                    f.box(b, wu, wy, -0.03f, 1.05f, 1.6f, 0.06f, C("#3E4C57"))
                }
                b.m(Mt.STONE, 0.6f); f.box(b, W / 2, y1 + floors * fh, dep / 2, W + 0.2f, 0.7f, dep + 0.3f, C("#CFC6B4"))
                if (r.chance(0.6f) && floors >= 3) {
                    b.m(Mt.METAL, 1f); val fu = W * 0.5f
                    for (fl in 1 until floors) { f.box(b, fu, y1 + fl * fh - 0.05f, -0.8f, 3.4f, 0.08f, 1.4f, C("#1E1E1E")); f.box(b, fu, y1 + fl * fh, -1.48f, 3.4f, 0.9f, 0.04f, C("#1E1E1E")) }
                    f.box(b, fu + 1.6f, y1, -1.48f, 0.06f, floors * fh, 0.06f, C("#1E1E1E"))
                }
            }
            2 -> { // vidro com montantes
                b.m(Mt.METAL, 1f); f.box(b, W / 2, y1, dep / 2, W - 0.1f, floors * fh, dep, col)
                b.m(Mt.PLAIN)
                var uu = 0.8f; while (uu < W - 0.5f) { f.box(b, uu, y1, -0.03f, 0.1f, floors * fh, 0.06f, C("#C9CED3")); uu += 1.6f }
                for (k in 1..floors) f.box(b, W / 2, y1 + k * fh - 0.05f, dep / 2, W + 0.02f, 0.1f, dep + 0.06f, C("#9AA3AB"))
            }
            3 -> { // torre sobre embasamento (centro): pódio + torre recuada, às vezes com coroa
                val pod = 3 + r.i(3)
                b.m(Mt.FACADE, 1f / 3f); f.box(b, W / 2, y1, dep / 2, W - 0.1f, pod * fh, dep, C(FACADES[r.i(FACADES.size)]))
                val ins = min(W, dep) * 0.18f
                val ty = y1 + pod * fh; val tf = max(4, floors - pod)
                b.m(Mt.METAL, 1f); f.box(b, W / 2, ty, dep / 2, W - 2 * ins, tf * fh, dep - 2 * ins, col)
                b.m(Mt.PLAIN)
                var uu = ins + 0.8f; while (uu < W - ins - 0.5f) { f.box(b, uu, ty, ins - 0.03f, 0.1f, tf * fh, 0.06f, C("#C9CED3")); uu += 1.6f }
                for (k in 1..tf step 2) f.box(b, W / 2, ty + k * fh, dep / 2, W - 2 * ins + 0.04f, 0.12f, dep - 2 * ins + 0.04f, C("#9AA3AB"))
                if (r.chance(0.5f)) { b.m(Mt.METAL, 1f); f.box(b, W / 2, ty + tf * fh, dep / 2, (W - 2 * ins) * 0.6f, 6f, (dep - 2 * ins) * 0.6f, shade(col, 15)); f.box(b, W / 2, ty + tf * fh + 6f, dep / 2, 0.3f, 10f, 0.3f, C("#B0B6BC")) }
                return ty + tf * fh + 6f
            }
            4 -> { // sobrados geminados estreitos (3–4 andares) com escadinha
                val n = max(1, (W / 6f).toInt()); val uw = W / n
                for (k in 0 until n) {
                    val c2 = C(if (r.chance(0.5f)) BRICKS[r.i(BRICKS.size)] else FACADES[r.i(FACADES.size)])
                    val hh = gh + (2 + r.i(2)) * fh
                    b.m(Mt.STONE, 0.45f); f.box(b, uw * (k + 0.5f), CURB, dep / 2, uw - 0.05f, hh, dep, c2)
                    b.m(Mt.PLAIN)
                    f.box(b, uw * (k + 0.5f) - uw * 0.25f, CURB + 1.0f, -0.04f, 1.0f, 2.2f, 0.06f, C(arrayOf("#2B2B2B", "#5A3A22", "#1F3A5F", "#7A2E2E")[r.i(4)]))
                    b.m(Mt.STONE, 0.8f); for (q in 0..3) f.box(b, uw * (k + 0.5f) - uw * 0.25f, CURB + q * 0.25f, -0.4f - (3 - q) * 0.3f, 1.4f, 0.25f, 0.3f, C("#B8B3AA"))
                    b.m(Mt.PLAIN)
                    for (fl in 0 until ((hh - 1f) / fh).toInt()) for (q in 0..1) f.box(b, uw * (k + 0.5f) + (q - 0.3f) * uw * 0.4f, CURB + 1.4f + fl * fh, -0.03f, 1.0f, 1.6f, 0.06f, C("#3E4C57"))
                    b.m(Mt.STONE, 0.6f); f.box(b, uw * (k + 0.5f), CURB + hh, dep / 2, uw + 0.05f, 0.5f, dep + 0.2f, C("#CFC6B4"))
                }
                return gh + 4 * fh
            }
            5 -> { // art déco escalonado
                b.m(Mt.FACADE, 1f / 3f)
                val s1 = (floors * 0.55f).toInt().coerceAtLeast(2); val s2 = (floors * 0.3f).toInt().coerceAtLeast(1); val s3 = max(1, floors - s1 - s2)
                f.box(b, W / 2, y1, dep / 2, W - 0.1f, s1 * fh, dep, col)
                f.box(b, W / 2, y1 + s1 * fh, dep / 2, W * 0.78f, s2 * fh, dep * 0.78f, shade(col, 6))
                f.box(b, W / 2, y1 + (s1 + s2) * fh, dep / 2, W * 0.55f, s3 * fh, dep * 0.55f, shade(col, 12))
                b.m(Mt.PLASTER, 0.5f)
                f.box(b, W / 2, y1 + s1 * fh, dep / 2, W + 0.2f, 0.4f, dep + 0.2f, shade(col, -25))
                f.box(b, W / 2, y1 + (s1 + s2) * fh, dep / 2, W * 0.8f, 0.4f, dep * 0.8f, shade(col, -25))
                b.m(Mt.METAL, 1f); f.box(b, W / 2, y1 + floors * fh, dep / 2, 0.4f, 8f, 0.4f, C("#C9A227"))
                return y1 + floors * fh + 8f
            }
            else -> { // reboco com janelas (textura de fachada), varandas às vezes
                b.m(Mt.FACADE, 1f / 3f, 0f, -y1 / 3f); f.box(b, W / 2, y1, dep / 2, W - 0.1f, floors * fh, dep, col)
                b.m(Mt.PLASTER, 0.5f); f.box(b, W / 2, y1 + floors * fh, dep / 2, W + 0.2f, 0.6f, dep + 0.2f, shade(col, -25))
                if (r.chance(0.45f)) for (fl in 1 until floors) for (q in 0 until max(1, (W / 5.5f).toInt())) {
                    val bu = 2.75f + q * 5.5f; if (bu > W - 1.5f) continue
                    b.m(Mt.STONE, 0.5f); f.box(b, bu, y1 + fl * fh, -0.6f, 3.4f, 0.14f, 1.2f, C("#EDEDED"))
                    b.m(Mt.METAL, 1f); f.box(b, bu, y1 + fl * fh + 0.14f, -1.15f, 3.4f, 0.95f, 0.04f, C("#9E9E9E"))
                }
            }
        }
        // ------------------------------------------------ Etapa 153: fachada viva
        val dark = C("#2B2E31")
        if (kind != 2) {   // ar-condicionado de janela, cada prédio com os seus
            b.m(Mt.METAL, 1f)
            val nw = max(2, (W / 2.6f).toInt())
            for (fl in 0 until floors) for (k in 0 until nw) if (r.chance(0.15f)) { val wu = W * (k + 0.5f) / nw
                f.box(b, wu, y1 + fl * fh + 0.42f, -0.22f, 0.75f, 0.42f, 0.4f, C("#D9D9D6")); f.box(b, wu, y1 + fl * fh + 0.48f, -0.43f, 0.6f, 0.3f, 0.02f, C("#8A8F94")) }
        }
        if (shopGround && floors >= 3 && r.chance(0.5f)) {   // letreiro vertical em bandeira
            val sc = C(arrayOf("#C62828", "#1565C0", "#2E7D32", "#F9A825", "#6A1B9A", "#EF6C00", "#00838F", "#AD1457")[r.i(8)])
            val su = if (r.chance(0.5f)) 0.7f else W - 0.7f; val sh = min(floors * fh * 0.6f, 7f)
            b.m(Mt.PLAIN); f.box(b, su, y1 + 0.8f, -0.6f, 0.2f, sh, 0.95f, sc)
            var q = 0; while (q * 1.1f + 0.9f < sh) { f.box(b, su, y1 + 1.0f + q * 1.1f, -0.6f, 0.22f, 0.7f, 0.62f, C("#FFFFFF")); f.box(b, su, y1 + 1.15f + q * 1.1f, -0.6f, 0.23f, 0.4f, 0.4f, sc); q++ }
            b.m(Mt.METAL, 1f); for (k in floatArrayOf(0.15f, 0.85f)) f.box(b, su, y1 + 0.8f + sh * k, -0.07f, 0.07f, 0.07f, 0.14f, dark)
        }
        if (shopGround) {   // arandelas no térreo
            b.m(Mt.PLAIN); var lu = 2.2f; while (lu < W - 1f) { f.box(b, lu, CURB + 3.05f, -0.1f, 0.2f, 0.28f, 0.16f, C("#FFF2C8")); lu += 6.5f }
        }
        if (shopGround && W > 9f && r.chance(0.4f)) {   // mesinhas de café na calçada com guarda-sol
            val umb = C(arrayOf("#C62828", "#1565C0", "#2E7D32", "#F9A825", "#FAFAFA", "#EF6C00")[r.i(6)]); val chairC = C(arrayOf("#37474F", "#6D4C41", "#ECEFF1")[r.i(3)])
            var tu = 2.2f; var nt = 0
            while (tu < W - 1.6f && nt < 3) {
                b.m(Mt.METAL, 1f); f.box(b, tu, CURB, -1.75f, 0.06f, 2.1f, 0.06f, C("#9E9E9E")); f.box(b, tu, CURB + 0.72f, -1.75f, 0.8f, 0.04f, 0.8f, C("#F2F2F2"))
                for (sg in floatArrayOf(-1f, 1f)) { f.box(b, tu + sg * 0.68f, CURB, -1.75f, 0.4f, 0.45f, 0.4f, chairC); f.box(b, tu + sg * 0.86f, CURB + 0.45f, -1.75f, 0.04f, 0.42f, 0.4f, chairC) }
                b.m(Mt.FABRIC, 1f); f.box(b, tu, CURB + 2.1f, -1.75f, 1.9f, 0.08f, 1.9f, umb); f.box(b, tu, CURB + 2.18f, -1.75f, 1.0f, 0.1f, 1.0f, shade(umb, -20))
                if (g.reg) f.solid(g, tu - 0.9f, -2.25f, tu + 0.9f, -1.25f)
                tu += 3.4f; nt++
            }
        } else if (r.chance(0.6f)) {   // vasos grandes ladeando a entrada
            for (sg in floatArrayOf(-1f, 1f)) { val pu = (W / 2 + sg * 1.5f).coerceIn(0.5f, W - 0.5f)
                b.m(Mt.STONE, 0.8f); f.box(b, pu, CURB, -0.5f, 0.55f, 0.55f, 0.55f, C(arrayOf("#B5603A", "#8C8F94", "#E2DCCF")[r.i(3)]))
                CityGeo.bush(g, f.x(pu, -0.5f), f.z(pu, -0.5f), 0.42f, CURB + 0.5f)
                if (g.reg) f.solid(g, pu - 0.3f, -0.8f, pu + 0.3f, -0.2f) }
        }
        // cobertura: casa de máquinas, caixas, antenas, jardim às vezes
        val ry = y1 + floors * fh + 0.6f
        // platibanda em volta do telhado
        b.m(Mt.PLASTER, 0.5f); val pc = shade(col, -18)
        f.box(b, W / 2, ry, 0.12f, W - 0.1f, 0.5f, 0.24f, pc); f.box(b, W / 2, ry, dep - 0.12f, W - 0.1f, 0.5f, 0.24f, pc)
        f.box(b, 0.17f, ry, dep / 2, 0.24f, 0.5f, dep - 0.4f, pc); f.box(b, W - 0.17f, ry, dep / 2, 0.24f, 0.5f, dep - 0.4f, pc)
        if (W > 9f && dep > 9f && r.chance(0.4f)) {   // placas solares
            b.m(Mt.METAL, 1f); val sx0 = W * 0.2f; val sz0 = dep * 0.55f
            for (i in 0 until min(4, ((W * 0.6f) / 1.9f).toInt())) for (j in 0..1) { f.box(b, sx0 + i * 1.9f, ry + 0.25f, sz0 + j * 1.3f, 1.7f, 0.06f, 1.1f, C("#1F3A5F")); f.box(b, sx0 + i * 1.9f, ry, sz0 + j * 1.3f, 0.08f, 0.25f, 0.08f, C("#9E9E9E")) }
        }
        if (r.chance(0.5f)) { b.m(Mt.METAL, 1f); val du = W * r.r(0.15f, 0.85f); val dv = dep * r.r(0.2f, 0.5f)   // parabólica
            f.box(b, du, ry, dv, 0.06f, 1.1f, 0.06f, C("#9E9E9E")); b.cyl(f.x(du, dv), ry + 1.0f, f.z(du, dv), 0.1f, 0.6f, 0.25f, C("#E6E6E6"), true, 10) }
        if (floors >= 5 && W > 10f && r.chance(0.35f)) {   // outdoor no topo
            b.m(Mt.METAL, 1f); val bw = min(W - 2f, 9f); val bh = bw / 3.2f
            for (sg in floatArrayOf(-0.4f, 0.4f)) f.box(b, W / 2 + sg * bw, ry, 0.7f, 0.14f, 1.4f + bh, 0.14f, dark)
            f.box(b, W / 2, ry + 1.3f, 0.62f, bw + 0.3f, bh + 0.3f, 0.12f, dark)
            b.m(Mt.PLAIN); val ad = C(arrayOf("#E53935", "#1E88E5", "#FDD835", "#43A047", "#8E24AA", "#FB8C00", "#00ACC1", "#F06292")[r.i(8)])
            f.box(b, W / 2, ry + 1.45f, 0.54f, bw, bh, 0.03f, ad); f.box(b, W / 2 - bw * 0.22f, ry + 1.45f + bh * 0.25f, 0.51f, bw * 0.4f, bh * 0.5f, 0.02f, C("#FFFFFF")); f.box(b, W / 2 + bw * 0.25f, ry + 1.45f + bh * 0.15f, 0.51f, bw * 0.3f, bh * 0.18f, 0.02f, shade(ad, -60))
            CityGeo.sign(b, f.x(W / 2, 0.48f), ry + 1.45f + bh * 0.82f, f.z(W / 2, 0.48f), f.fx, f.fz, bw * 0.8f, bw * 0.1f, SIGNS[r.i(SIGNS.size)], false)
        }
        b.m(Mt.METAL, 1f)
        if (r.chance(0.7f)) f.box(b, W * r.r(0.25f, 0.75f), ry, dep * r.r(0.3f, 0.7f), min(4f, W * 0.3f), 2.4f, min(4f, dep * 0.3f), C("#B0B6BC"))
        if (r.chance(0.5f)) f.box(b, W * 0.2f, ry, dep * 0.75f, 1.6f, 1f, 1.2f, C("#C8CCD0"))
        if (r.chance(0.3f) && W > 10f) { b.m(Mt.GRASS, 0.5f); f.box(b, W * 0.6f, ry - 0.5f, dep * 0.4f, W * 0.4f, 0.15f, dep * 0.3f, C("#5E8C4A")) }
        if (d == TownPlan.URB && r.chance(0.3f)) { b.m(Mt.WOOD, 0.6f); f.box(b, W * 0.7f, ry, dep * 0.6f, 2.2f, 2.6f, 2.2f, C("#7A5A3C")); b.m(Mt.ROOF, 0.6f); f.box(b, W * 0.7f, ry + 2.6f, dep * 0.6f, 2.6f, 0.6f, 2.6f, C("#4A3A2E")) }   // caixa d'água de madeira (NY)
        return ry + 3f
    }

    private val TINT = arrayOf("#8FB4CC", "#7FA9A6", "#9DB8A0", "#B59A7E", "#A9B4BE", "#6F8FB5", "#C2CCD3", "#8C9CB0", "#94A8B8", "#A3B6A9")

    /** Etapa 149: arranha-céu — cada um com um desenho (escalonado, grade de concreto, faixas, cilindro, coroa em pirâmide, brises de bronze, torres gêmeas),
     *  com o volume também no modelo de longe, para o horizonte ter silhuetas diferentes. */
    private fun tower(g: CityGeo.Gen, f: TownSmall.F, r: City.Rng, W: Float, dep: Float, floors: Int, y1: Float): Float {
        val b = g.b; val fh = 3f
        val tint = C(TINT[r.i(TINT.size)])
        fun mass(u: Float, y: Float, v: Float, su: Float, sy: Float, sv: Float, c: Int, mat: Int = Mt.CURTAIN, sc: Float = 1f / 3f) {
            b.m(mat, sc, 0f, -y / 3f); f.box(b, u, y, v, su, sy, sv, c)
            g.f.m(mat, sc, 0f, -y / 3f); f.box(g.f, u, y, v, su, sy, sv, c)
        }
        fun beacon(u: Float, y: Float, v: Float) { b.m(Mt.PLAIN); f.box(b, u, y, v, 0.35f, 0.35f, 0.35f, C("#E53935")) }
        var H = floors * fh
        var a = r.i(7)
        if (a == 3 && min(W, dep) < 15f) a = 0
        if (a == 6 && W < 22f) a = 4
        when (a) {
            0 -> { // escalonado (wedding cake): três volumes que vão recuando, com marquises de pedra e lanterna de vidro no topo
                val h1 = (H * 0.55f / fh).toInt() * fh; val h2 = (H * 0.28f / fh).toInt() * fh; val h3 = max(2 * fh, H - h1 - h2)
                val i2 = min(W, dep) * 0.12f; val i3 = min(W, dep) * 0.24f
                mass(W / 2, y1, dep / 2, W - 0.1f, h1, dep, tint)
                mass(W / 2, y1 + h1, dep / 2, W - 2 * i2, h2, dep - 2 * i2, shade(tint, 6))
                mass(W / 2, y1 + h1 + h2, dep / 2, W - 2 * i3, h3, dep - 2 * i3, shade(tint, 12))
                b.m(Mt.STONE, 0.6f)
                f.box(b, W / 2, y1 + h1, dep / 2, W + 0.3f, 0.5f, dep + 0.3f, C("#D8D2C4"))
                f.box(b, W / 2, y1 + h1 + h2, dep / 2, W - 2 * i2 + 0.3f, 0.5f, dep - 2 * i2 + 0.3f, C("#D8D2C4"))
                val top = y1 + h1 + h2 + h3
                mass(W / 2, top, dep / 2, (W - 2 * i3) * 0.55f, 6f, (dep - 2 * i3) * 0.55f, C("#F3E7C2"), Mt.GLASS, 1f)
                mass(W / 2, top + 6f, dep / 2, 0.5f, 14f, 0.5f, C("#C9CED3"), Mt.METAL, 1f)
                beacon(W / 2, top + 20f, dep / 2)
                return top + 20f
            }
            1 -> { // grade de concreto claro com pilastras salientes e heliponto
                val wall = C(arrayOf("#ECE7DD", "#E2DED6", "#D8CDBB", "#F1EEE8")[r.i(4)])
                mass(W / 2, y1, dep / 2, W - 0.1f, H, dep, wall, Mt.FACADE)
                b.m(Mt.PLASTER, 0.5f)
                var uu = 0f; val step = W / max(2, (W / 4.5f).toInt())
                while (uu <= W + 0.01f) { f.box(b, uu.coerceIn(0.2f, W - 0.2f), y1, -0.18f, 0.45f, H, 0.4f, shade(wall, -8)); f.box(b, uu.coerceIn(0.2f, W - 0.2f), y1, dep + 0.18f, 0.45f, H, 0.4f, shade(wall, -8)); uu += step }
                for (k in 1..(H / fh / 6f).toInt()) f.box(b, W / 2, y1 + k * 6 * fh - 0.2f, dep / 2, W + 0.5f, 0.4f, dep + 0.5f, shade(wall, -14))
                val top = y1 + H
                mass(W / 2, top, dep / 2, W + 0.3f, 1.4f, dep + 0.3f, shade(wall, -18), Mt.PLASTER, 0.5f)
                val hr = min(W, dep) * 0.36f
                b.m(Mt.PLAIN)
                b.cyl(f.x(W / 2, dep / 2), top + 1.4f, f.z(W / 2, dep / 2), hr, hr, 0.06f, C("#4A4D52"), true, 28)
                b.cyl(f.x(W / 2, dep / 2), top + 1.42f, f.z(W / 2, dep / 2), hr * 0.92f, hr * 0.92f, 0.06f, C("#F2C230"), true, 28)
                b.cyl(f.x(W / 2, dep / 2), top + 1.44f, f.z(W / 2, dep / 2), hr * 0.86f, hr * 0.86f, 0.06f, C("#4A4D52"), true, 28)
                f.box(b, W / 2 - hr * 0.3f, top + 1.47f, dep / 2, 0.5f, 0.05f, hr * 0.9f, C("#F4F4F4"))
                f.box(b, W / 2 + hr * 0.3f, top + 1.47f, dep / 2, 0.5f, 0.05f, hr * 0.9f, C("#F4F4F4"))
                f.box(b, W / 2, top + 1.47f, dep / 2, hr * 0.6f, 0.05f, 0.5f, C("#F4F4F4"))
                beacon(0.6f, top + 1.4f, 0.6f); beacon(W - 0.6f, top + 1.4f, dep - 0.6f)
                return top + 3f
            }
            2 -> { // janelas em fita: vidro escuro corrido e faixa branca em cada andar, laje de cobertura em balanço
                val wall = C(arrayOf("#F2F0EB", "#E6E1D7", "#DADFE3")[r.i(3)])
                mass(W / 2, y1, dep / 2, W - 0.1f, H, dep, wall, Mt.PLASTER, 0.5f)
                b.m(Mt.GLASS, 1f); g.f.m(Mt.GLASS, 1f)
                val gl = C(arrayOf("#3B5568", "#2F4F4F", "#44505C", "#4D6B7E")[r.i(4)])
                for (k in 0 until (H / fh).toInt()) {
                    f.box(b, W / 2, y1 + k * fh + 1.0f, dep / 2, W + 0.06f, 1.75f, dep + 0.06f, gl)
                    if (k % 2 == 0) f.box(g.f, W / 2, y1 + k * fh + 1.0f, dep / 2, W + 0.06f, 3.5f, dep + 0.06f, gl)
                }
                val top = y1 + H
                mass(W / 2, top, dep / 2, W + 2.4f, 0.6f, dep + 2.4f, wall, Mt.PLASTER, 0.5f)
                b.m(Mt.METAL, 1f); for (s2 in floatArrayOf(0.3f, 0.7f)) f.box(b, W * s2, top + 0.6f, dep / 2, 0.25f, 9f + s2 * 6f, 0.25f, C("#B0B6BC"))
                beacon(W * 0.7f, top + 0.6f + 13.2f, dep / 2)
                return top + 15f
            }
            3 -> { // cilindro de vidro com anéis e coroa
                val rr = min(W, dep) / 2 - 0.4f; val cx = f.x(W / 2, dep / 2); val cz = f.z(W / 2, dep / 2)
                for (mb in arrayOf(b, g.f)) { mb.m(Mt.CURTAIN, 1f / 3f, 0f, -y1 / 3f); mb.cyl(cx, y1, cz, rr, rr, H, tint, true, 28) }
                b.m(Mt.METAL, 1f)
                var k = 4; while (k * fh < H) { b.cyl(cx, y1 + k * fh - 0.15f, cz, rr + 0.2f, rr + 0.2f, 0.3f, C("#DDE1E4"), true, 28); k += 4 }
                val top = y1 + H
                for (mb in arrayOf(b, g.f)) { mb.m(Mt.METAL, 1f); mb.cyl(cx, top, cz, rr + 0.3f, rr * 0.7f, 2.5f, C("#DDE1E4"), true, 28); mb.cyl(cx, top + 2.5f, cz, rr * 0.55f, rr * 0.45f, 7f, shade(tint, 20), true, 24); mb.cyl(cx, top + 9.5f, cz, 0.35f, 0.08f, 16f, C("#C9CED3"), true, 8) }
                beacon(W / 2, top + 25.5f, dep / 2)
                return top + 26f
            }
            4 -> { // torre com colunas de pedra nas quinas e coroa em pirâmide dourada
                val ins = min(W, dep) * 0.08f; val tw2 = W - 2 * ins; val td = dep - 2 * ins
                val pod = 3 * fh
                mass(W / 2, y1, dep / 2, W - 0.1f, pod, dep, C(FACADES[r.i(FACADES.size)]), Mt.FACADE)
                mass(W / 2, y1 + pod, dep / 2, tw2, H - pod, td, tint)
                b.m(Mt.STONE, 0.5f); g.f.m(Mt.STONE, 0.5f)
                val stc = C(arrayOf("#D9D2C2", "#C8BBA6", "#E5E0D6")[r.i(3)])
                for (cu in floatArrayOf(ins, W - ins)) for (cv in floatArrayOf(ins, dep - ins)) for (mb in arrayOf(b, g.f)) f.box(mb, cu, y1 + pod, cv, 1.4f, H - pod + 1f, 1.4f, stc)
                val top = y1 + H + 1f
                var y = top; var sw = tw2; var sd = td
                b.m(Mt.METAL, 1f); g.f.m(Mt.METAL, 1f)
                val gold = C(arrayOf("#C9A227", "#B9B9B9", "#5E7F6E")[r.i(3)])
                for (q in 0 until 6) { for (mb in arrayOf(b, g.f)) f.box(mb, W / 2, y, dep / 2, sw, 1.6f, sd, gold); y += 1.6f; sw *= 0.78f; sd *= 0.78f }
                for (mb in arrayOf(b, g.f)) f.box(mb, W / 2, y, dep / 2, 0.3f, 8f, 0.3f, gold)
                beacon(W / 2, y + 8f, dep / 2)
                return y + 8f
            }
            5 -> { // vidro bronze com brises verticais e coroa vazada
                val bz = C(arrayOf("#B08D6A", "#9C8B78", "#8E9A86")[r.i(3)])
                mass(W / 2, y1, dep / 2, W - 0.1f, H, dep, bz)
                b.m(Mt.METAL, 1f)
                val fin = shade(bz, -45)
                var uu = 0.75f; while (uu < W - 0.5f) { f.box(b, uu, y1, -0.3f, 0.14f, H + 2f, 0.6f, fin); f.box(b, uu, y1, dep + 0.3f, 0.14f, H + 2f, 0.6f, fin); uu += 1.5f }
                val top = y1 + H
                for (mb in arrayOf(b, g.f)) {
                    mb.m(Mt.METAL, 1f)
                    for (cu in floatArrayOf(0.4f, W - 0.4f)) for (cv in floatArrayOf(0.4f, dep - 0.4f)) f.box(mb, cu, top, cv, 0.8f, 9f, 0.8f, fin)
                    f.box(mb, W / 2, top + 8f, 0.4f, W, 1f, 0.8f, fin); f.box(mb, W / 2, top + 8f, dep - 0.4f, W, 1f, 0.8f, fin)
                    f.box(mb, 0.4f, top + 8f, dep / 2, 0.8f, 1f, dep, fin); f.box(mb, W - 0.4f, top + 8f, dep / 2, 0.8f, 1f, dep, fin)
                }
                b.m(Mt.METAL, 1f); f.box(b, W / 2, top, dep / 2, W * 0.4f, 3f, dep * 0.4f, C("#9EA4AA"))
                beacon(0.4f, top + 9f, 0.4f)
                return top + 9f
            }
            else -> { // torres gêmeas ligadas por uma passarela de vidro
                val sw = W * 0.4f; val h2 = (H * 0.78f / fh).toInt() * fh
                mass(W * 0.21f, y1, dep / 2, sw, H, dep * 0.9f, tint)
                mass(W * 0.79f, y1, dep / 2, sw, h2, dep * 0.9f, shade(tint, 8))
                val by = y1 + (h2 * 0.6f / fh).toInt() * fh
                mass(W / 2, by, dep / 2, W * 0.2f + 0.4f, 2 * fh, dep * 0.4f, C("#DDE6EC"), Mt.GLASS, 1f)
                b.m(Mt.METAL, 1f)
                f.box(b, W * 0.21f, y1 + H, dep / 2, sw + 0.4f, 1.2f, dep * 0.9f + 0.4f, C("#DDE1E4"))
                f.box(b, W * 0.79f, y1 + h2, dep / 2, sw + 0.4f, 1.2f, dep * 0.9f + 0.4f, C("#DDE1E4"))
                beacon(W * 0.21f, y1 + H + 1.2f, dep / 2)
                return y1 + H + 2f
            }
        }
    }

    /** Miolo do quarteirão. */
    private fun court(g: CityGeo.Gen, x0: Float, z0: Float, x1: Float, z1: Float, r: City.Rng) {
        val b = g.b; val cx = (x0 + x1) / 2; val cz = (z0 + z1) / 2
        when (r.i(5)) {
            0 -> { // jardim
                b.m(Mt.GRASS, 0.3f); b.plane(x0, z0, x1, z1, CURB + 0.015f, C("#C9E6B4"))
                b.m(Mt.PAVER, 0.6f); b.plane(cx - 1.2f, z0, cx + 1.2f, z1, CURB + 0.025f, C("#D9CFBC")); b.plane(x0, cz - 1.2f, x1, cz + 1.2f, CURB + 0.025f, C("#D9CFBC"))
                for (q in 0..3) { val tx = if (q % 2 == 0) (x0 + cx) / 2 else (cx + x1) / 2; val tz = if (q < 2) (z0 + cz) / 2 else (cz + z1) / 2; CityGeo.tree(g, tx, tz, 0.9f); g.solid(tx - 0.3f, tz - 0.3f, tx + 0.3f, tz + 0.3f) }
            }
            1 -> { // estacionamento
                b.m(Mt.ASPHALT, 0.3f); b.plane(x0, z0, x1, z1, CURB + 0.015f, C("#D0D0D0"))
                b.m(Mt.PLAIN); var x = x0 + 1f; while (x < x1 - 1f) { b.plane(x - 0.05f, z0 + 1f, x + 0.05f, z0 + 6f, CURB + 0.03f, C("#F4F4F4")); b.plane(x - 0.05f, z1 - 6f, x + 0.05f, z1 - 1f, CURB + 0.03f, C("#F4F4F4")); x += 2.6f }
            }
            2 -> { // piscina do condomínio
                b.m(Mt.TILE, 0.5f); b.plane(x0, z0, x1, z1, CURB + 0.015f, C("#E8E2D6"))
                b.m(Mt.PLAIN); b.plane(x0 + 2.5f, z0 + 2.5f, x1 - 2.5f, z1 - 2.5f, CURB + 0.04f, C("#3AA7C9"))
            }
            3 -> { // quadra
                b.m(Mt.PLAIN); b.plane(x0, z0, x1, z1, CURB + 0.015f, C("#C25B3C")); b.plane(x0 + 1.5f, z0 + 1.5f, x1 - 1.5f, z1 - 1.5f, CURB + 0.03f, C("#3E6FA8"))
                b.plane(x0 + 1.5f, cz - 0.05f, x1 - 1.5f, cz + 0.05f, CURB + 0.045f, C("#F4F4F4"))
            }
            else -> { // playground e bancos
                b.m(Mt.PLAIN); b.plane(x0, z0, x1, z1, CURB + 0.015f, C("#D9CFBC"))
                b.cyl(cx, CURB, cz, min(x1 - x0, z1 - z0) * 0.3f, min(x1 - x0, z1 - z0) * 0.3f, 0.04f, C("#C9603E"), true, 24)
                b.m(Mt.METAL, 1f); b.box(cx, CURB + 1.2f, cz, 3f, 0.1f, 0.1f, C("#E0452E")); for (s in floatArrayOf(-1.5f, 1.5f)) b.box(cx + s, CURB + 0.6f, cz, 0.1f, 1.2f, 0.1f, C("#E0452E"))
                g.solid(cx - 1.6f, cz - 0.2f, cx + 1.6f, cz + 0.2f)
            }
        }
    }
}
