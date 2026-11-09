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
        // ---- longe
        val col = when (kind) { 1 -> C(BRICKS[r.i(BRICKS.size)]); 2, 3 -> C(GLASS[r.i(GLASS.size)]); else -> C(FACADES[r.i(FACADES.size)]) }
        g.f.m(if (kind == 2 || kind == 3) Mt.METAL else Mt.FACADE, if (kind == 2 || kind == 3) 1f else 1f / 3f)
        f.box(g.f, W / 2, CURB, dep / 2, W - 0.1f, H, dep, col)
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
        // cobertura: casa de máquinas, caixas, antenas, jardim às vezes
        val ry = y1 + floors * fh + 0.6f
        b.m(Mt.METAL, 1f)
        if (r.chance(0.7f)) f.box(b, W * r.r(0.25f, 0.75f), ry, dep * r.r(0.3f, 0.7f), min(4f, W * 0.3f), 2.4f, min(4f, dep * 0.3f), C("#B0B6BC"))
        if (r.chance(0.5f)) f.box(b, W * 0.2f, ry, dep * 0.75f, 1.6f, 1f, 1.2f, C("#C8CCD0"))
        if (r.chance(0.3f) && W > 10f) { b.m(Mt.GRASS, 0.5f); f.box(b, W * 0.6f, ry - 0.5f, dep * 0.4f, W * 0.4f, 0.15f, dep * 0.3f, C("#5E8C4A")) }
        if (d == TownPlan.URB && r.chance(0.3f)) { b.m(Mt.WOOD, 0.6f); f.box(b, W * 0.7f, ry, dep * 0.6f, 2.2f, 2.6f, 2.2f, C("#7A5A3C")); b.m(Mt.ROOF, 0.6f); f.box(b, W * 0.7f, ry + 2.6f, dep * 0.6f, 2.6f, 0.6f, 2.6f, C("#4A3A2E")) }   // caixa d'água de madeira (NY)
        return ry + 3f
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
