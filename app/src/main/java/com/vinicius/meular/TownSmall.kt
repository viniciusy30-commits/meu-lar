package com.vinicius.meular

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * Etapa 138: construções pequenas para os espaços de 12 a 36 m que sobram nos quarteirões.
 * Viram para a rua mais perto; cada uma sorteia tipo, medidas, cores e detalhes pela semente:
 * sobrados geminados, prédio residencial pequeno, comércio de bairro com letreiro, prédio de escritórios de vidro,
 * estacionamento arborizado e pátio com pérgola.
 */
object TownSmall {
    private const val CURB = Town.CURB

    /** Quadro local: u ao longo da frente, v da frente (0) para o fundo. */
    class F(val x0: Float, val z0: Float, val x1: Float, val z1: Float, val side: Int) {
        // side: 0 frente em z0 (olhando −z), 1 frente em x1 (+x), 2 frente em z1 (+z), 3 frente em x0 (−x)
        val W get() = if (side % 2 == 0) x1 - x0 else z1 - z0
        val D get() = if (side % 2 == 0) z1 - z0 else x1 - x0
        fun x(u: Float, v: Float) = when (side) { 0 -> x0 + u; 1 -> x1 - v; 2 -> x1 - u; else -> x0 + v }
        fun z(u: Float, v: Float) = when (side) { 0 -> z0 + v; 1 -> z0 + u; 2 -> z1 - v; else -> z1 - u }
        val fx get() = when (side) { 1 -> 1f; 3 -> -1f; else -> 0f }
        val fz get() = when (side) { 0 -> -1f; 2 -> 1f; else -> 0f }
        /** caixa no quadro local (centro u, v; largura su, fundo sv) */
        fun box(b: MB, u: Float, y: Float, v: Float, su: Float, sy: Float, sv: Float, c: Int) {
            val cx = x(u, v); val cz = z(u, v)
            if (side % 2 == 0) b.box(cx, y + sy / 2, cz, su, sy, sv, c) else b.box(cx, y + sy / 2, cz, sv, sy, su, c)
        }
        fun solid(g: CityGeo.Gen, u0: Float, v0: Float, u1: Float, v1: Float) {
            val ax = x(u0, v0); val az = z(u0, v0); val bx = x(u1, v1); val bz = z(u1, v1)
            g.solid(min(ax, bx), min(az, bz), max(ax, bx), max(az, bz))
        }
    }

    fun build(g: CityGeo.Gen, u: Town.Urban, ui: Int): Float {
        val r = City.Rng(ui * 6151 + 29)
        // frente para a rua mais perto (o lado com menos folga)
        val mids = arrayOf(floatArrayOf((u.x0 + u.x1) / 2, u.z0 - 3f), floatArrayOf(u.x1 + 3f, (u.z0 + u.z1) / 2), floatArrayOf((u.x0 + u.x1) / 2, u.z1 + 3f), floatArrayOf(u.x0 - 3f, (u.z0 + u.z1) / 2))
        var side = 0; var bc = Float.MAX_VALUE
        for (k in 0..3) { val c = Town.clearance(mids[k][0], mids[k][1]); if (c < bc) { bc = c; side = k } }
        val f = F(u.x0, u.z0, u.x1, u.z1, side)
        val W = f.W; val D = f.D
        val d = TownPlan.districtAt((u.x0 + u.x1) / 2, (u.z0 + u.z1) / 2)
        val b = g.b
        // chão do espaço (calçado no comércio/centro, grama nos bairros)
        val urbanD = d == TownPlan.DOWN || d == TownPlan.COM
        CityGeo.groundBox(b, u.x0, u.z0, u.x1, u.z1, if (urbanD) Mt.PAVER else Mt.GRASS, if (urbanD) 0.9f else 0.3f, if (urbanD) C("#E3E0DA") else C("#D6EEC4"))
        CityGeo.groundBox(g.f, u.x0, u.z0, u.x1, u.z1, if (urbanD) Mt.PAVER else Mt.GRASS, if (urbanD) 0.9f else 0.3f, if (urbanD) C("#E3E0DA") else C("#D6EEC4"))
        val kind = if (d == TownPlan.MAN) 5 else if (d == TownPlan.SUB || d == TownPlan.HOME) (if (W >= 14f && D >= 14f) 0 else 5) else when {
            W < 14f || D < 12f -> if (r.chance(0.5f)) 4 else 5
            urbanD -> intArrayOf(2, 3, 1, 2, 3, 4, 1)[r.i(7)]
            else -> intArrayOf(0, 0, 1, 2, 0, 1, 5, 4)[r.i(8)]
        }
        return when (kind) {
            0 -> townhouses(g, f, r)
            1 -> apartments(g, f, r)
            2 -> shop(g, f, r)
            3 -> office(g, f, r)
            4 -> parking(g, f, r)
            else -> courtyard(g, f, r)
        }
    }

    private val WALLS = arrayOf("#E9E2D0", "#C9D6DF", "#EFE3C2", "#D7DDD0", "#F2E8DA", "#B9C4C9", "#E7D9CF", "#A86B4F", "#9C5A3C", "#DCCBB5", "#CBD8C3", "#F4F1EA")
    private val ROOFS = arrayOf("#4A4F55", "#5B4A42", "#3E4348", "#6B5D53", "#7A4E3A", "#B5523B")

    /** Sobrados geminados: 2 a 5 casas coladas, cada uma com cor, porta e escadinha próprias. */
    private fun townhouses(g: CityGeo.Gen, f: F, r: City.Rng): Float {
        val b = g.b; val W = f.W; val D = f.D
        val n = max(2, (W / 6.5f).toInt()).coerceAtMost(5); val uw = (W - 2f) / n
        val dep = min(D - 5f, 11f); val v0 = 3f
        val roof = C(ROOFS[r.i(ROOFS.size)]); val h = if (r.chance(0.6f)) 6.2f else 3.3f
        for (k in 0 until n) {
            val uc = 1f + uw * (k + 0.5f)
            val col = C(WALLS[r.i(WALLS.size)])
            b.m(if (r.chance(0.3f)) Mt.STONE else Mt.SIDING, 0.6f); f.box(b, uc, CURB, v0 + dep / 2, uw - 0.05f, h, dep, col)
            b.m(Mt.ROOF, 0.6f); f.box(b, uc, CURB + h, v0 + dep / 2, uw + 0.1f, 0.35f, dep + 0.6f, roof)
            b.m(Mt.PLAIN)
            f.box(b, uc - uw * 0.22f, CURB + 0.35f, v0 - 0.05f, 1.0f, 2.1f, 0.1f, C(arrayOf("#8E1B1B", "#1F3A5F", "#222222", "#5A3A22", "#2E5E3A")[r.i(5)]))
            for (fl in 0 until (h / 3f).toInt()) f.box(b, uc + uw * 0.18f, CURB + 1.1f + fl * 3f, v0 - 0.06f, 1.3f, 1.3f, 0.08f, C("#4E6A7E"))
            if (h > 4f) f.box(b, uc - uw * 0.22f, CURB + 4.1f, v0 - 0.06f, 1.2f, 1.2f, 0.08f, C("#4E6A7E"))
            b.m(Mt.STONE, 0.8f); f.box(b, uc - uw * 0.22f, CURB, v0 - 0.8f, 1.6f, 0.35f, 1.5f, C("#B8B3AA"))
            if (r.chance(0.5f)) CityGeo.bush(g, f.x(uc + uw * 0.25f, 1.2f), f.z(uc + uw * 0.25f, 1.2f), 0.55f)
        }
        f.solid(g, 1f, v0, W - 1f, v0 + dep)
        // muretinha na frente
        b.m(Mt.STONE, 0.7f); f.box(b, W / 2, CURB, 0.5f, W - 1f, 0.5f, 0.25f, C("#CFC8BA"))
        return h + 1f
    }

    /** Prédio residencial pequeno (3 a 7 andares) com varandas e portaria. */
    private fun apartments(g: CityGeo.Gen, f: F, r: City.Rng): Float {
        val b = g.b; val W = f.W; val D = f.D
        val fl = 3 + r.i(5); val fh = 3f; val H = 4f + fl * fh
        val w = W - 3f; val dep = min(D - 4f, 16f); val v0 = 2.5f
        val col = C(arrayOf("#E8E1D3", "#D9D4CA", "#C9B8A3", "#B7C3C9", "#E3D5C1", "#A9A39A", "#EDE8DF")[r.i(7)])
        b.m(Mt.STONE, 0.6f); f.box(b, W / 2, CURB, v0 + dep / 2, w, 4f, dep, C("#8C8F94"))
        b.m(Mt.FACADE, 1f / 3f); f.box(b, W / 2, CURB + 4f, v0 + dep / 2, w, fl * fh, dep, col)
        b.m(Mt.PLASTER, 0.5f); f.box(b, W / 2, CURB + H, v0 + dep / 2, w + 0.3f, 0.6f, dep + 0.3f, shade(col, -25))
        // varandas
        if (r.chance(0.6f)) for (k in 1 until fl) for (q in 0 until max(1, (w / 5f).toInt())) {
            val uc = 1.5f + 2.5f + q * 5f; if (uc > W - 2f) continue
            b.m(Mt.STONE, 0.5f); f.box(b, uc, CURB + 4f + k * fh, v0 - 0.6f, 3.4f, 0.14f, 1.2f, C("#EDEDED"))
            b.m(Mt.METAL, 1f); f.box(b, uc, CURB + 4f + k * fh + 0.14f, v0 - 1.15f, 3.4f, 0.95f, 0.04f, C("#9E9E9E"))
        }
        // portaria com vidro e marquise
        b.m(Mt.PLAIN); f.box(b, W / 2, CURB + 0.1f, v0 - 0.04f, 3.4f, 2.8f, 0.08f, C("#5C7A8E"))
        b.m(Mt.METAL, 1f); f.box(b, W / 2, CURB + 3.1f, v0 - 1.2f, 4.4f, 0.16f, 2.4f, C("#4A4F55"))
        // caixa d'água e casa de máquinas
        b.m(Mt.METAL, 1f); f.box(b, W / 2 + w / 4, CURB + H + 0.6f, v0 + dep / 2, 3f, 2.4f, 3f, C("#B0B6BC"))
        f.solid(g, 1.5f, v0, W - 1.5f, v0 + dep)
        g.f.m(Mt.FACADE, 1f / 3f); f.box(g.f, W / 2, CURB, v0 + dep / 2, w, H, dep, col)
        return H + 3f
    }

    /** Comércio de bairro: térreo com vitrine, toldo e letreiro; às vezes um andar em cima. */
    private fun shop(g: CityGeo.Gen, f: F, r: City.Rng): Float {
        val b = g.b; val W = f.W; val D = f.D
        val w = W - 2f; val dep = min(D - 3f, 14f); val v0 = 1.5f
        val two = r.chance(0.5f); val H = if (two) 7.6f else 4.4f
        val col = C(WALLS[r.i(WALLS.size)])
        b.m(Mt.PLASTER, 0.6f); f.box(b, W / 2, CURB, v0 + dep / 2, w, H, dep, col)
        b.m(Mt.PLAIN)
        // vitrines e porta
        val nv = max(1, (w / 4f).toInt())
        for (k in 0 until nv) f.box(b, 1f + w * (k + 0.5f) / nv, CURB + 0.4f, v0 - 0.04f, w / nv - 0.6f, 2.8f, 0.06f, C("#7FA3B8"))
        // toldo listrado
        val aw = C(arrayOf("#C62828", "#1565C0", "#2E7D32", "#F9A825", "#6A1B9A", "#EF6C00", "#00838F")[r.i(7)])
        b.m(Mt.FABRIC, 1f); f.box(b, W / 2, CURB + 3.3f, v0 - 0.8f, w - 0.4f, 0.12f, 1.6f, aw); f.box(b, W / 2, CURB + 3.05f, v0 - 1.55f, w - 0.4f, 0.4f, 0.06f, aw)
        // letreiro (atlas de letreiros da cidade)
        val idx = intArrayOf(2, 4, 5, 13, 14, 15, 16, 17, 34, 35, 36, 37, 38, 39, 1, 7, 8)[r.i(17)]
        val sx = f.x(W / 2, v0 - 0.1f); val sz = f.z(W / 2, v0 - 0.1f)
        CityGeo.sign(b, sx, CURB + 3.6f, sz, f.fx, f.fz, min(w - 1f, 7f), 0.75f, idx)
        if (two) { b.m(Mt.PLAIN); for (k in 0 until nv) f.box(b, 1f + w * (k + 0.5f) / nv, CURB + 5.1f, v0 - 0.05f, 1.4f, 1.5f, 0.08f, C("#4E6A7E")) }
        b.m(Mt.PLASTER, 0.5f); f.box(b, W / 2, CURB + H, v0 + dep / 2, w + 0.2f, 0.5f, dep + 0.2f, shade(col, -25))
        // mesinhas na calçada ou bicicletário
        if (r.chance(0.5f)) for (k in 0..1) { b.m(Mt.METAL, 1f); f.box(b, W * (0.3f + k * 0.4f), CURB, v0 - 2.6f, 0.7f, 0.75f, 0.7f, C("#3B3F44")) }
        f.solid(g, 1f, v0, W - 1f, v0 + dep)
        g.f.m(Mt.PLASTER, 0.6f); f.box(g.f, W / 2, CURB, v0 + dep / 2, w, H, dep, col)
        return H + 1f
    }

    /** Escritórios: caixa de vidro com montantes, 4 a 10 andares. */
    private fun office(g: CityGeo.Gen, f: F, r: City.Rng): Float {
        val b = g.b; val W = f.W; val D = f.D
        val fl = 4 + r.i(7); val H = 4.5f + fl * 3.4f
        val w = W - 3f; val dep = min(D - 4f, 20f); val v0 = 2.5f
        val gl = C(arrayOf("#4F6E86", "#3F5F6E", "#5E7F8F", "#2F4A5E", "#6F8C99", "#3E5A4E")[r.i(6)])
        b.m(Mt.STONE, 0.6f); f.box(b, W / 2, CURB, v0 + dep / 2, w, 4.5f, dep, C("#5F6368"))
        b.m(Mt.METAL, 1f); f.box(b, W / 2, CURB + 4.5f, v0 + dep / 2, w, fl * 3.4f, dep, gl)
        b.m(Mt.PLAIN)
        var uu = 1.5f; while (uu <= W - 1.5f + 0.01f) { f.box(b, uu, CURB + 4.5f, v0 - 0.03f, 0.1f, fl * 3.4f, 0.06f, C("#C9CED3")); uu += 1.6f }
        for (k in 1..fl) f.box(b, W / 2, CURB + 4.5f + k * 3.4f - 0.05f, v0 + dep / 2, w + 0.06f, 0.1f, dep + 0.06f, C("#9AA3AB"))
        f.box(b, W / 2, CURB + 0.2f, v0 - 0.04f, w * 0.6f, 3.6f, 0.06f, C("#7FA3B8"))
        b.m(Mt.METAL, 1f); f.box(b, W / 2, CURB + 4.2f, v0 - 1.5f, w * 0.7f, 0.2f, 3f, C("#3B3F44"))
        f.solid(g, 1.5f, v0, W - 1.5f, v0 + dep)
        g.f.m(Mt.METAL, 1f); f.box(g.f, W / 2, CURB, v0 + dep / 2, w, H, dep, gl)
        return H + 1f
    }

    /** Estacionamento com vagas pintadas, árvores e alguns carros. */
    private fun parking(g: CityGeo.Gen, f: F, r: City.Rng): Float {
        val b = g.b; val W = f.W; val D = f.D
        b.m(Mt.ASPHALT, 0.3f); f.box(b, W / 2, CURB, D / 2, W - 1f, 0.03f, D - 1f, C("#D0D0D0"))
        b.m(Mt.PLAIN)
        val n = ((W - 2f) / 2.6f).toInt()
        for (k in 0..n) f.box(b, 1f + k * 2.6f, CURB + 0.03f, D - 3.2f, 0.1f, 0.01f, 5f, C("#F4F4F4"))
        for (k in 0 until n) if (r.chance(0.55f)) {
            val m = Vehicles.pick(r); if (Vehicles.halfL(m) > 2.6f) continue
            val tmp = MB(); Vehicles.geom(Vehicles.XF(tmp, 0f, 0f, 0f, 1), m, r.i(12))
            val cx = f.x(2.3f + k * 2.6f, D - 3.2f); val cz = f.z(2.3f + k * 2.6f, D - 3.2f)
            b.appendRot(tmp, -f.fz, -f.fx, cx, CURB + 0.03f, cz)
            g.solid(cx - 1.2f, cz - 1.2f, cx + 1.2f, cz + 1.2f)
        }
        if (W > 10f) for (k in 0..1) { val tx = f.x(if (k == 0) 1.5f else W - 1.5f, 2f); val tz = f.z(if (k == 0) 1.5f else W - 1.5f, 2f); CityGeo.tree(g, tx, tz, 0.8f); g.solid(tx - 0.3f, tz - 0.3f, tx + 0.3f, tz + 0.3f) }
        return 6f
    }

    /** Pátio com pérgola, canteiros e bancos (respiro entre os prédios). */
    private fun courtyard(g: CityGeo.Gen, f: F, r: City.Rng): Float {
        val b = g.b; val W = f.W; val D = f.D
        b.m(Mt.PAVER, 0.6f); f.box(b, W / 2, CURB, D / 2, W - 1.5f, 0.02f, D - 1.5f, C("#D9CFBC"))
        b.m(Mt.WOOD, 0.6f)
        val pw = min(W - 4f, 8f); val pd = min(D - 4f, 5f)
        for (q in 0..1) for (k in 0..1) f.box(b, W / 2 + (k - 0.5f) * pw, CURB, D / 2 + (q - 0.5f) * pd, 0.25f, 2.8f, 0.25f, C("#7A5A3C"))
        for (k in 0..5) f.box(b, W / 2, CURB + 2.8f, D / 2 - pd / 2 + k * pd / 5, pw + 0.6f, 0.15f, 0.12f, C("#7A5A3C"))
        b.m(Mt.GRASS, 0.5f); f.box(b, W / 2, CURB + 2.95f, D / 2, pw, 0.2f, pd * 0.6f, C("#4E7A3A"))
        for (k in 0..1) { val bx = f.x(W * (0.25f + k * 0.5f), D * 0.25f); val bz = f.z(W * (0.25f + k * 0.5f), D * 0.25f); CityGeo.bush(g, bx, bz, 0.8f) }
        CityGeo.publicBench(b, f.x(W / 2, D * 0.8f), f.z(W / 2, D * 0.8f), f.fx, f.fz)
        if (r.chance(0.5f)) CityGeo.tree(g, f.x(W * 0.8f, D * 0.75f), f.z(W * 0.8f, D * 0.75f), 0.9f)
        return 4f
    }

    @Suppress("unused") private fun unused() = abs(0f)
}
