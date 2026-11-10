package com.vinicius.meular

import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/** Etapa 151: hipotenusa rápida (Math.hypot é muito lenta e aqui é chamada milhões de vezes na montagem). */
private fun hypot(a: Float, b: Float): Float = kotlin.math.sqrt(a * a + b * b)

/**
 * Etapa 135: parques e praças nos quarteirões de parque e nos que sobram vazios.
 * Lago com margem de pedra, ilha e deck; caminho em volta do lago e caminhos ligando às calçadas;
 * playground, quadras (basquete e futebol), academia ao ar livre, quiosque, bancos e postes ao longo dos caminhos,
 * bosques e canteiros. Tudo posicionado por folga até a borda do quarteirão, aos caminhos e uns aos outros.
 */
object TownPark {
    private const val CURB = Town.CURB
    private val PATH = C("#D9CFBC")
    private val STONE = C("#A39C8E")
    private val WATER = C("#3E93B8")

    /** Parque planejado (calculado uma vez): lago, caminhos, áreas. */
    class Plan(val block: Int) {
        var cx = 0f; var cz = 0f; var lakeR = 0f
        var lakeA = 1f; var lakeB = 1f; var lakeRot = 0f   // elipse: semi-eixos relativos e giro
        var plaza = false                                   // sem lago: praça com chafariz no meio
        val paths = ArrayList<FloatArray>()      // polilinhas (x, z)
        val spots = ArrayList<FloatArray>()      // (x, z, raio, tipo)
        val trees = ArrayList<FloatArray>()
        var pw = 1.4f                              // meia largura dos caminhos
        val gates = ArrayList<FloatArray>()      // Etapa 155: portais de entrada (x, z, direção x, direção z)
    }
    val plans = java.util.concurrent.ConcurrentHashMap<Int, Plan>()   // Etapa 151: lido por várias threads de detalhe

    /** Distância de (x, z) até a borda do polígono (positiva dentro). */
    private fun inset(bl: FloatArray, x: Float, z: Float): Float {
        var m = Float.MAX_VALUE; val n = bl.size / 2
        for (i in 0 until n) {
            val j = (i + 1) % n
            val ax = bl[i * 2]; val az = bl[i * 2 + 1]; val dx = bl[j * 2] - ax; val dz = bl[j * 2 + 1] - az; val l2 = max(1e-6f, dx * dx + dz * dz)
            val t = (((x - ax) * dx + (z - az) * dz) / l2).coerceIn(0f, 1f)
            m = min(m, hypot(x - ax - dx * t, z - az - dz * t))
        }
        return if (Town.inside(bl, x, z)) m else -m
    }

    private fun distSeg(px: Float, pz: Float, p: FloatArray): Float {
        var m = Float.MAX_VALUE
        for (i in 0 until p.size / 2 - 1) {
            val ax = p[i * 2]; val az = p[i * 2 + 1]; val dx = p[i * 2 + 2] - ax; val dz = p[i * 2 + 3] - az; val l2 = max(1e-6f, dx * dx + dz * dz)
            val t = (((px - ax) * dx + (pz - az) * dz) / l2).coerceIn(0f, 1f)
            m = min(m, hypot(px - ax - dx * t, pz - az - dz * t))
        }
        return m
    }

    /** Etapa 146: um parque só — a quadra do bairro PARQUE mais perto do centro da superquadra. */
    private var cacheKey: Any? = null; private var parkIdx = -1
    private fun parkBlock(): Int {
        val key = Town.blocks.firstOrNull()
        if (key !== cacheKey) {
            cacheKey = key; parkIdx = -1; var best = Float.MAX_VALUE
            for ((bi, bl) in Town.blocks.withIndex()) {
                if (bi == Town.homeBlock) continue
                var cx = 0f; var cz = 0f; val n = bl.size / 2; for (k in 0 until n) { cx += bl[k * 2]; cz += bl[k * 2 + 1] }; cx /= n; cz /= n
                if (TownPlan.districtAt(cx, cz) != TownPlan.PARK || abs(Town.polyArea(bl)) < 3000f) continue
                val cc = TownPlan.cellCenter(cx, cz); val d = kotlin.math.hypot(cx - cc[0], cz - cc[1])
                if (d < best) { best = d; parkIdx = bi }
            }
        }
        return parkIdx
    }
    fun isPark(bi: Int): Boolean = bi == parkBlock()
    /** O ponto cai dentro do parque? (as casas não entram nele) */
    fun inPark(x: Float, z: Float): Boolean { val p = parkBlock(); return p >= 0 && Town.inside(Town.blocks[p], x, z) }

    /**
     * Etapa 155: Parque Central com projeto — tudo centralizado e simétrico: lago redondo no meio com anel, dois eixos em cruz
     * até as quatro entradas, alameda em volta, duas alamedas laterais e as áreas alinhadas em duas colunas espelhadas.
     */
    private fun formal(pl: Plan, bl: FloatArray, x0: Float, z0: Float, x1: Float, z1: Float) {
        val cx = (x0 + x1) / 2; val cz = (z0 + z1) / 2
        pl.cx = cx; pl.cz = cz; pl.lakeR = 32f; pl.lakeA = 1f; pl.lakeB = 1f; pl.lakeRot = 0f; pl.plaza = false; pl.pw = 2.3f
        val hx = (x1 - x0) / 2 - 11f; val hz = (z1 - z0) / 2 - 11f; val rr = pl.lakeR + 8f
        fun line(ax: Float, az: Float, bx: Float, bz: Float): FloatArray { val n = max(2, (hypot(bx - ax, bz - az) / 2f).toInt()); val o = FloatArray((n + 1) * 2); for (i in 0..n) { o[i * 2] = ax + (bx - ax) * i / n; o[i * 2 + 1] = az + (bz - az) * i / n }; return o }
        val ring = FloatArray(65 * 2); for (q in 0..64) { val a = 6.2832f * q / 64; ring[q * 2] = cx + cos(a) * rr; ring[q * 2 + 1] = cz + sin(a) * rr }
        pl.paths.add(ring)
        // eixos em cruz, do anel até as entradas
        pl.paths.add(line(cx, cz - rr, cx, cz - hz - 9f)); pl.paths.add(line(cx, cz + rr, cx, cz + hz + 9f))
        pl.paths.add(line(cx - rr, cz, cx - hx - 9f, cz)); pl.paths.add(line(cx + rr, cz, cx + hx + 9f, cz))
        pl.gates.add(floatArrayOf(cx, cz - hz - 7f, 1f, 0f)); pl.gates.add(floatArrayOf(cx, cz + hz + 7f, 1f, 0f)); pl.gates.add(floatArrayOf(cx - hx - 7f, cz, 0f, 1f)); pl.gates.add(floatArrayOf(cx + hx + 7f, cz, 0f, 1f))
        // alameda em volta (retângulo) e as duas alamedas laterais
        pl.paths.add(line(cx - hx, cz - hz, cx + hx, cz - hz)); pl.paths.add(line(cx - hx, cz + hz, cx + hx, cz + hz))
        pl.paths.add(line(cx - hx, cz - hz, cx - hx, cz + hz)); pl.paths.add(line(cx + hx, cz - hz, cx + hx, cz + hz))
        val colP = 46f
        for (sg in floatArrayOf(-1f, 1f)) pl.paths.add(line(cx + sg * colP, cz - hz, cx + sg * colP, cz + hz))
        // áreas: duas colunas espelhadas (oeste e leste), alinhadas pelo mesmo eixo
        val col = min(hx - 34f, 80f)
        fun spot(sx: Float, dz: Float, tp: Int, rad: Float) { if (abs(dz) + rad < hz - 4f) pl.spots.add(floatArrayOf(cx + sx * col, cz + dz, rad, tp.toFloat())) }
        val zs = hz / 139f
        spot(-1f, -104f * zs, 2, 30f); spot(-1f, -52f * zs, 1, 16f)             // noroeste: futebol e quadra
        spot(1f, -110f * zs, 0, 9f); spot(1f, -80f * zs, 12, 8f); spot(1f, -50f * zs, 3, 8f)   // nordeste: parquinho, piquenique, academia
        spot(-1f, 50f * zs, 5, 6f); spot(-1f, 80f * zs, 10, 9f); spot(-1f, 114f * zs, 8, 13f)   // sudoeste: coreto, roseiral, anfiteatro
        spot(1f, 50f * zs, 4, 6f); spot(1f, 80f * zs, 9, 10f); spot(1f, 113f * zs, 6, 12f)      // sudeste: quiosque, vôlei, skate
        // Etapa 156: oito jardins formais (canteiros com cerca viva) entre o eixo central e as alamedas laterais, espelhados
        for (sx in floatArrayOf(-1f, 1f)) for (sz in floatArrayOf(-1f, 1f)) { var k = 0
            for (dz in floatArrayOf(rr + 27f, rr + 69f)) { if (dz + 19f < hz - 3f) pl.spots.add(floatArrayOf(cx + sx * 25.5f, cz + sz * dz, 19f, 13f)); k++ } }
        // árvores: fileiras dos dois lados dos eixos e da alameda de fora, e bosque em grade nos gramados
        fun ok(px: Float, pz: Float, gap: Float): Boolean {
            if (inset(bl, px, pz) < 2.5f) return false
            if (hypot(px - cx, pz - cz) < pl.lakeR + 4f) return false
            if (pl.paths.any { distSeg(px, pz, it) < gap }) return false
            if (pl.spots.any { hypot(px - it[0], pz - it[1]) < it[2] + 3.5f }) return false
            return !pl.trees.any { hypot(px - it[0], pz - it[1]) < 6f }
        }
        val off = pl.pw + 3.2f
        var t = rr + 9f
        while (t < hz - 6f) { for (sg in floatArrayOf(-1f, 1f)) for (sd in floatArrayOf(-1f, 1f)) if (ok(cx + sd * off, cz + sg * t, pl.pw + 1.5f)) pl.trees.add(floatArrayOf(cx + sd * off, cz + sg * t, 1.15f)); t += 13f }
        t = rr + 9f
        while (t < hx - 6f) { for (sg in floatArrayOf(-1f, 1f)) for (sd in floatArrayOf(-1f, 1f)) if (ok(cx + sg * t, cz + sd * off, pl.pw + 1.5f)) pl.trees.add(floatArrayOf(cx + sg * t, cz + sd * off, 1.15f)); t += 13f }
        t = -hx + 8f
        while (t < hx - 6f) { for (sg in floatArrayOf(-1f, 1f)) if (ok(cx + t, cz + sg * (hz + off), pl.pw + 1.5f)) pl.trees.add(floatArrayOf(cx + t, cz + sg * (hz + off), 1.0f)); t += 15f }
        t = -hz + 8f
        while (t < hz - 6f) { for (sg in floatArrayOf(-1f, 1f)) if (ok(cx + sg * (hx + off), cz + t, pl.pw + 1.5f)) pl.trees.add(floatArrayOf(cx + sg * (hx + off), cz + t, 1.0f)); t += 15f }
        val r = City.Rng(4711)
        var gz = -hz + 12f; var row = 0
        while (gz < hz - 8f && pl.trees.size < 125) { var gx = -hx + 12f + (row % 2) * 7f
            while (gx < hx - 8f) { val px = cx + gx + r.r(-2f, 2f); val pz = cz + gz + r.r(-2f, 2f); if (hypot(px - cx, pz - cz) > 58f && ok(px, pz, pl.pw + 4f)) pl.trees.add(floatArrayOf(px, pz, r.r(0.85f, 1.3f))); gx += 14f }
            gz += 13f; row++ }
    }

    /** Etapa 158: bichos do lago que nadam de verdade (carpas em cardume e patos), desenhados a cada quadro. */
    class Swim(val cx: Float, val cz: Float, val rad: Float, val ph: Float, val spd: Float, val mesh: Int, val y: Float)
    @Volatile var swimmers: Array<Swim> = arrayOf()
    @Volatile var swimMesh: Array<Mesh?> = arrayOfNulls(0)
    private val KOI = arrayOf("#FF7A1A", "#FFFFFF", "#E53935", "#FFB300", "#F5F5F5", "#2B2B2B")
    fun buildLife() {
        val ms = ArrayList<Mesh?>()
        for (k in 0 until 6) { val b = MB(); b.m(Mt.PLAIN); val c = C(KOI[k]); val c2 = C(KOI[(k + 1) % 6])
            b.box(0f, 0f, 0f, 0.15f, 0.09f, 0.5f, c); b.box(0f, 0.005f, 0.17f, 0.13f, 0.09f, 0.2f, c2); b.box(0f, 0f, 0.31f, 0.1f, 0.07f, 0.14f, c)
            b.box(0f, 0f, -0.36f, 0.26f, 0.02f, 0.2f, c2); b.box(0.11f, -0.01f, 0.08f, 0.12f, 0.02f, 0.1f, c2); b.box(-0.11f, -0.01f, 0.08f, 0.12f, 0.02f, 0.1f, c2)
            ms.add(b.toMesh(true)) }
        for (k in 0..1) { val b = MB(); b.m(Mt.PLAIN); val body = C(if (k == 0) "#FFFFFF" else "#8D6E63"); val head = if (k == 0) body else C("#1B5E20")
            CityGeo.ball(b, 0f, 0.1f, 0f, 0.22f, body, 0.17f, 7); CityGeo.ball(b, 0f, 0.14f, -0.2f, 0.13f, body, 0.1f, 6); b.box(0f, 0.2f, -0.3f, 0.1f, 0.03f, 0.14f, shade(body, -25))
            b.box(0f, 0.27f, 0.2f, 0.07f, 0.22f, 0.07f, head); CityGeo.ball(b, 0f, 0.42f, 0.22f, 0.1f, head, 0.1f, 6); b.box(0f, 0.4f, 0.35f, 0.07f, 0.03f, 0.12f, C("#FB8C00"))
            ms.add(b.toMesh(true)) }
        swimMesh = ms.toTypedArray()
        val l = ArrayList<Swim>()
        for (bi in Town.blocks.indices) if (isPark(bi)) { val pl = plan(bi); if (pl.gates.isEmpty()) continue
            val R = pl.lakeR; val wy = CURB + 0.33f; val r = City.Rng(8123); val ix = pl.cx + R * 0.3f; val iz = pl.cz - R * 0.2f; val ir = R * 0.18f + 5f
            var n = 0; var t = 0
            while (n < 12 && t++ < 200) { val a = r.r(0f, 6.283f); val d = r.r(9f, R - 7f); val x = pl.cx + cos(a) * d; val z = pl.cz + sin(a) * d; if (hypot(x - ix, z - iz) < ir + 4f) continue
                val dir = if (r.chance(0.5f)) 1f else -1f
                for (k in 0 until 5) l.add(Swim(x + r.r(-0.6f, 0.6f), z + r.r(-0.6f, 0.6f), r.r(1.2f, 3.6f), r.r(0f, 6.283f), dir * r.r(0.5f, 0.9f), r.i(6), wy + 0.035f))
                n++ }
            // patos: voltas largas em torno do chafariz, e alguns em roda menor
            for (k in 0 until 6) l.add(Swim(pl.cx, pl.cz, 5.5f + (k % 2) * 1.4f, k * 1.05f, 0.28f, 6 + k % 2, wy + 0.02f))
            for (k in 0 until 3) l.add(Swim(pl.cx - R * 0.45f, pl.cz + R * 0.35f, 3f + k, k * 2.1f, -0.22f, 6 + k % 2, wy + 0.02f)) }
        swimmers = l.toTypedArray()
    }

    fun plan(bi: Int): Plan {
        plans[bi]?.let { return it }
        val bl = Town.blocks[bi]
        val pl = Plan(bi)
        val r = City.Rng(bi * 977 + 5)
        // centro: o ponto mais "fundo" do polígono (máximo da distância à borda), numa grade
        var x0 = Float.MAX_VALUE; var x1 = -Float.MAX_VALUE; var z0 = Float.MAX_VALUE; var z1 = -Float.MAX_VALUE
        var k = 0; while (k < bl.size) { x0 = min(x0, bl[k]); x1 = max(x1, bl[k]); z0 = min(z0, bl[k + 1]); z1 = max(z1, bl[k + 1]); k += 2 }
        var best = -1f
        val st = max(4f, min(x1 - x0, z1 - z0) / 24f)
        var x = x0; while (x <= x1) { var z = z0; while (z <= z1) { val d = inset(bl, x, z); if (d > best) { best = d; pl.cx = x; pl.cz = z }; z += st }; x += st }
        val big = best > 45f
        if (best > 80f) { formal(pl, bl, x0, z0, x1, z1); plans[bi] = pl; return pl }
        // cada parque com um desenho: índice do parque na cidade decide o tema
        val pidx = Town.blocks.indices.filter { isPark(it) }.indexOf(bi).coerceAtLeast(0)
        val lakeKind = (pidx * 7 + 3) % 4          // 0 redondo, 1 elipse, 2 sem lago (praça), 3 elipse comprida
        pl.lakeR = if (lakeKind == 2) 0f else if (big) min(best * (0.3f + 0.04f * (pidx % 4)), if (best > 80f) 58f else 48f) else if (best > 18f) best * 0.26f else 0f
        if (lakeKind == 1) { pl.lakeA = 1.25f; pl.lakeB = 0.8f } else if (lakeKind == 3) { pl.lakeA = 1.5f; pl.lakeB = 0.62f }
        pl.lakeRot = pidx * 0.7f
        pl.plaza = pl.lakeR == 0f
        // caminho em volta do lago (ou praça central)
        val ringR = if (pl.lakeR > 0f) pl.lakeR * pl.lakeA + 7f else min(best * 0.45f, 14f)
        val ring = FloatArray(49 * 2); for (q in 0..48) { val a = 6.2832f * q / 48; ring[q * 2] = pl.cx + cos(a) * ringR; ring[q * 2 + 1] = pl.cz + sin(a) * ringR }
        pl.paths.add(ring)
        // caminhos do anel até a borda (4 a 6 direções), curvados
        val nRad = if (big) 6 else 4
        val a0 = r.r(0f, 1f)
        for (q in 0 until nRad) {
            val a = a0 + 6.2832f * q / nRad
            val sx = pl.cx + cos(a) * ringR; val sz = pl.cz + sin(a) * ringR
            // anda para fora até chegar a 1 m da borda
            var t = ringR; var ex = sx; var ez = sz
            while (t < 600f) { val px = pl.cx + cos(a) * t; val pz = pl.cz + sin(a) * t; if (inset(bl, px, pz) < 0.6f) break; ex = px; ez = pz; t += 1f }
            if (hypot(ex - sx, ez - sz) < 4f) continue
            val bend = r.r(-0.18f, 0.18f) * hypot(ex - sx, ez - sz)
            val mx = (sx + ex) / 2 - sin(a) * bend; val mz = (sz + ez) / 2 + cos(a) * bend
            val pts = FloatArray(17 * 2)
            for (i in 0..16) { val u = i / 16f; val w = 1 - u; pts[i * 2] = w * w * sx + 2 * w * u * mx + u * u * ex; pts[i * 2 + 1] = w * w * sz + 2 * w * u * mz + u * u * ez }
            // o caminho só vale se ficar todo dentro do quarteirão e fora do lago
            var ok = true; for (i in 0..16) if (inset(bl, pts[i * 2], pts[i * 2 + 1]) < 0.5f || (pl.lakeR > 0f && hypot(pts[i * 2] - pl.cx, pts[i * 2 + 1] - pl.cz) < pl.lakeR + 3f)) { ok = false; break }
            if (ok) pl.paths.add(pts)
        }
        // áreas: 0 playground, 1 basquete, 2 futebol, 3 academia, 4 quiosque, 5 coreto, 6 pista de skate, 7 cachorródromo,
        // 8 anfiteatro, 9 vôlei de areia, 10 roseiral, 11 obelisco/monumento, 12 piquenique
        // cada parque sorteia um conjunto diferente (o índice entra na semente e o conjunto nunca se repete inteiro)
        val pool = mutableListOf(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
        val pr = City.Rng(pidx * 7919 + 11)
        for (i in pool.indices.reversed()) { val j = pr.i(i + 1); val t = pool[i]; pool[i] = pool[j]; pool[j] = t }
        val nWant = if (best > 80f) 13 else if (big) 6 + pidx % 3 else 3 + pidx % 2   // Etapa 155: parque grande tem de tudo
        val want = pool.take(nWant).toIntArray()
        val size = floatArrayOf(9f, 16f, 30f, 8f, 6f, 6f, 12f, 11f, 13f, 10f, 9f, 5f, 8f)
        for (tp in want) {
            val rad = size[tp]
            for (tries in 0 until 80) {
                val px = r.r(x0, x1); val pz = r.r(z0, z1)
                if (inset(bl, px, pz) < rad + 4f) continue
                if (pl.lakeR > 0f && hypot(px - pl.cx, pz - pl.cz) < pl.lakeR * pl.lakeA + rad + 9f) continue
                if (pl.paths.any { distSeg(px, pz, it) < rad + 2f }) continue
                if (pl.spots.any { hypot(px - it[0], pz - it[1]) < rad + it[2] + 4f }) continue
                pl.spots.add(floatArrayOf(px, pz, rad, tp.toFloat())); break
            }
        }
        // árvores: bosques espalhados (folga dos caminhos, do lago e das áreas)
        val area = abs(Town.polyArea(bl))
        val nt = (area / 260f).toInt().coerceIn(8, 160)
        var tries = 0
        while (pl.trees.size < nt && tries++ < nt * 25) {
            val px = r.r(x0, x1); val pz = r.r(z0, z1)
            if (inset(bl, px, pz) < 3f) continue
            if (pl.lakeR > 0f && hypot(px - pl.cx, pz - pl.cz) < pl.lakeR * pl.lakeA + 4f) continue
            if (pl.paths.any { distSeg(px, pz, it) < 3.2f }) continue
            if (pl.spots.any { hypot(px - it[0], pz - it[1]) < it[2] + 3f }) continue
            if (pl.trees.any { hypot(px - it[0], pz - it[1]) < 6f }) continue
            pl.trees.add(floatArrayOf(px, pz, r.r(0.85f, 1.3f)))
        }
        plans[bi] = pl
        return pl
    }

    fun draw(g: CityGeo.Gen, bi: Int, near: Boolean, far: Boolean) {
        val pl = plan(bi)
        val b = g.b
        // lago (fundo um pouco abaixo da grama, margem de pedra)
        if (pl.lakeR > 0f) {
            val R = pl.lakeR
            if (far) { g.f.m(Mt.PLAIN); g.f.cyl(pl.cx, CURB - 0.02f, pl.cz, R, R, 0.3f, WATER, true, 36) }
            if (g.reg) { val s = R * 0.68f; g.solid(pl.cx - s, pl.cz - s, pl.cx + s, pl.cz + s) }
            if (g.reg && pl.gates.isNotEmpty()) City.lakes.add(floatArrayOf(pl.cx, pl.cz, -R, CURB + 0.33f))
            if (near) {
                fun ell(rr: Float): FloatArray { val o = FloatArray(56 * 2); val ca = cos(pl.lakeRot); val sa = sin(pl.lakeRot); for (q in 0 until 56) { val a = 6.2832f * q / 56; val ex = cos(a) * rr * pl.lakeA; val ez = sin(a) * rr * pl.lakeB; o[q * 2] = pl.cx + ex * ca - ez * sa; o[q * 2 + 1] = pl.cz + ex * sa + ez * ca }; return o }
                val rim = ell(R + 1.2f); val wat = ell(R)
                if (pl.gates.isNotEmpty()) {
                    // Etapa 158: lago com água de verdade (ondas e reflexo): borda de pedra em anel, fundo de areia e seixos; a água é desenhada por cima
                    b.m(Mt.STONE, 0.6f); TownGeo.ribbon(b, rim, wat, CURB + 0.42f, C("#B8B2A6")); TownGeo.curbWall(b, rim + floatArrayOf(rim[0], rim[1]), CURB, CURB + 0.42f, false, STONE); TownGeo.curbWall(b, rim + floatArrayOf(rim[0], rim[1]), CURB, CURB + 0.42f, true, STONE)
                    b.m(Mt.PLASTER, 0.7f); TownGeo.fan(b, pl.cx, pl.cz, wat, CURB + 0.05f, C("#7FA9A0"))
                } else {
                b.m(Mt.STONE, 0.6f); TownGeo.fan(b, pl.cx, pl.cz, rim, CURB + 0.25f, STONE)
                b.m(Mt.PLAIN); TownGeo.fan(b, pl.cx, pl.cz, wat, CURB + 0.33f, WATER)
                }
                val ring2 = FloatArray(rim.size + 2); System.arraycopy(rim, 0, ring2, 0, rim.size); ring2[rim.size] = rim[0]; ring2[rim.size + 1] = rim[1]
                b.m(Mt.STONE, 0.6f); TownGeo.curbWall(b, ring2, CURB - 0.02f, CURB + 0.25f, false, STONE)
                // ilha com árvore
                if (R > 20f) { val ix = pl.cx + R * 0.3f; val iz = pl.cz - R * 0.2f; b.m(Mt.GRASS, 0.3f); b.cyl(ix, CURB - 0.02f, iz, R * 0.18f, R * 0.18f, 0.5f, C("#D6EEC4"), true, 24); CityGeo.tree(g, ix, iz, 1.2f, CURB + 0.48f) }
                // deck de madeira entrando no lago
                val a = 2.4f; val dx = cos(a); val dz = sin(a)
                val ox = pl.cx + dx * (R + 3f); val oz = pl.cz + dz * (R + 3f)
                b.m(Mt.WOOD, 0.5f); TownGeo.obox(b, ox - dx * 5f, CURB + 0.45f, oz - dz * 5f, 10f, 0.15f, 3f, dx, dz, C("#9A7350"))
                for (q in 0..3) b.cyl(ox - dx * (q * 3f), CURB - 0.1f, oz - dz * (q * 3f), 0.12f, 0.12f, 0.35f, C("#6B4E36"), true, 6)
                // patos/pedalinhos
                for (q in 0 until 3) { val aa = q * 2.1f + 0.5f; val px = pl.cx + cos(aa) * R * 0.6f; val pz = pl.cz + sin(aa) * R * 0.6f; b.m(Mt.PLAIN); b.box(px, CURB + 0.4f, pz, 1.6f, 0.5f, 2.4f, C(arrayOf("#FFFFFF", "#F2C230", "#E05A47")[q])); CityGeo.ball(b, px, CURB + 1.05f, pz + 0.6f, 0.35f, C(arrayOf("#FFFFFF", "#F2C230", "#E05A47")[q]), 0.35f, 8) }
            }
        }
        if (pl.plaza && near) {
            b.m(Mt.PAVER, 0.5f); b.cyl(pl.cx, CURB, pl.cz, 11f, 11f, 0.03f, C("#E2DCCF"), true, 40)
            b.m(Mt.STONE, 1f); b.cyl(pl.cx, CURB, pl.cz, 4.5f, 4.5f, 0.7f, C("#CFC8BA"), true, 32); b.cyl(pl.cx, CURB + 0.7f, pl.cz, 0.6f, 0.6f, 2.2f, C("#CFC8BA"), true, 12); b.cyl(pl.cx, CURB + 2.9f, pl.cz, 1.8f, 1.8f, 0.25f, C("#CFC8BA"), true, 18)
            b.m(Mt.PLAIN); b.cyl(pl.cx, CURB + 0.62f, pl.cz, 4.2f, 4.2f, 0.06f, C("#5DB3D9"), true, 32)
        }
        if (pl.plaza && g.reg) g.solid(pl.cx - 4.5f, pl.cz - 4.5f, pl.cx + 4.5f, pl.cz + 4.5f)
        // caminhos (pedrisco) com bancos e postes
        for (p in pl.paths) {
            val l = Town.offset(p, -pl.pw); val rr = Town.offset(p, pl.pw)
            if (near) { b.m(Mt.PAVER, 0.6f); TownGeo.ribbon(b, l, rr, CURB + 0.014f, PATH) }
            if (far) { g.f.m(Mt.PAVER, 0.6f); TownGeo.ribbon(g.f, l, rr, CURB + 0.014f, PATH) }
            if (!near) continue
            var acc = 0f; var side = 1f
            for (i in 1 until p.size / 2) {
                acc += hypot(p[i * 2] - p[i * 2 - 2], p[i * 2 + 1] - p[i * 2 - 1])
                if (acc > (if (pl.pw > 2f) 22f else 14f)) {
                    acc = 0f
                    val t = Town.tangent(p, i); val nx = -t[1] * side; val nz = t[0] * side
                    val lx = p[i * 2] + nx * (pl.pw + 0.8f); val lz = p[i * 2 + 1] + nz * (pl.pw + 0.8f)
                    if (side > 0) { CityGeo.streetLamp(b, lx, lz, 0f, 0f); g.solid(lx - 0.15f, lz - 0.15f, lx + 0.15f, lz + 0.15f) }
                    else { bench(b, lx, lz, -nx, -nz); g.solid(lx - 0.4f, lz - 0.4f, lx + 0.4f, lz + 0.4f) }
                    side = -side
                }
            }
        }
        // Etapa 155: portais de entrada (pilares de pedra com viga e lanternas) e canteiros de flores em volta do anel
        if (near) for (gt in pl.gates) {
            val px = gt[2]; val pz = gt[3]
            for (sg in floatArrayOf(-1f, 1f)) { val x = gt[0] + px * sg * 4.2f; val z = gt[1] + pz * sg * 4.2f
                b.m(Mt.STONE, 0.5f); b.box(x, CURB + 1.9f, z, 1.0f, 3.8f, 1.0f, C("#B8B2A6")); b.box(x, CURB + 3.9f, z, 1.3f, 0.25f, 1.3f, C("#A39C8E"))
                b.m(Mt.PLAIN); CityGeo.ball(b, x, CURB + 4.3f, z, 0.3f, C("#FFF2C8"), 0.3f, 7)
                g.solid(x - 0.5f, z - 0.5f, x + 0.5f, z + 0.5f) }
            b.m(Mt.METAL, 1f); b.box(gt[0], CURB + 4.6f, gt[1], 9.6f * abs(px) + 0.25f, 0.3f, 9.6f * abs(pz) + 0.25f, C("#2E4A33"))
            b.box(gt[0], CURB + 5.1f, gt[1], 5.0f * abs(px) + 0.12f, 0.7f, 5.0f * abs(pz) + 0.12f, C("#2E4A33"))
        }
        if (near && pl.gates.isNotEmpty()) { lakeLife(g, pl); axisFlowers(g, pl); lawnLife(g, pl) }
        if (near && pl.gates.isNotEmpty()) {
            val fr = pl.lakeR + 8f + pl.pw + 2.6f; val cols = arrayOf("#E53935", "#FDD835", "#F06292", "#FFFFFF", "#FB8C00", "#8E24AA")
            for (q in 0 until 8) { val a = 0.3927f + q * 0.7854f; val x = pl.cx + cos(a) * fr; val z = pl.cz + sin(a) * fr
                b.m(Mt.STONE, 0.8f); b.cyl(x, CURB, z, 2.3f, 2.3f, 0.3f, STONE, true, 14); b.m(Mt.PLAIN); b.cyl(x, CURB + 0.02f, z, 2.05f, 2.05f, 0.32f, C("#5A4632"), true, 14)
                // Etapa 157: cerejeira florida no meio e dois anéis de flores em volta
                g.fl.place("cherry_a", x.toDouble(), (CURB + 0.3f).toDouble(), z.toDouble(), 0.95, (q * 1.3f).toDouble())
                for (k in 0 until 16) { val fa = k * 0.3927f; flower(g, FL[q % 5], x + cos(fa) * 1.75f, z + sin(fa) * 1.75f, CURB + 0.33f, 2.0f) }
                for (k in 0 until 10) { val fa = k * 0.628f + 0.3f; flower(g, FL[(q + 2) % 5], x + cos(fa) * 1.1f, z + sin(fa) * 1.1f, CURB + 0.33f, 2.0f) }
                g.solid(x - 2.3f, z - 2.3f, x + 2.3f, z + 2.3f) }
        }
        // áreas
        for (s in pl.spots) {
            val x = s[0]; val z = s[1]; val tp = s[3].toInt()
            when (tp) {
                0 -> if (near) playground(g, x, z) else if (g.reg) playground(g, x, z)
                1 -> court(g, x, z, near)
                2 -> soccer(g, x, z, near)
                3 -> if (near) gym(g, x, z) else if (g.reg) gym(g, x, z)
                4 -> kiosk(g, x, z, near)
                5 -> gazebo(g, x, z, near)
                13 -> if (near || g.reg) parterre(g, x, z, ((abs(x - pl.cx) + abs(z - pl.cz) * 3f) / 40f).toInt() + (if (x > pl.cx) 1 else 0) + (if (z > pl.cz) 2 else 0))
                else -> if (near || g.reg) extra(g, tp, x, z, near)
            }
            // caminho curto até o caminho mais perto
            if (near) {
                var bd = Float.MAX_VALUE; var bx = 0f; var bz = 0f
                for (p in pl.paths) for (i in 0 until p.size / 2) { val d = hypot(p[i * 2] - x, p[i * 2 + 1] - z); if (d < bd) { bd = d; bx = p[i * 2]; bz = p[i * 2 + 1] } }
                if (bd < 60f) {
                    val dx = bx - x; val dz = bz - z; val l = max(1e-3f, hypot(dx, dz))
                    val sx = x + dx / l * s[2]; val sz = z + dz / l * s[2]
                    val L = hypot(bx - sx, bz - sz)
                    if (L > 1f) { b.m(Mt.PAVER, 0.6f); TownGeo.obox(b, (sx + bx) / 2, CURB + 0.01f, (sz + bz) / 2, L, 0.012f, 2f, (bx - sx) / L, (bz - sz) / L, PATH) }
                }
            }
        }
        // árvores e canteiros
        if (near) {
            val r = City.Rng(bi * 31 + 1)
            for (t in pl.trees) {
                if (r.chance(0.12f)) CityGeo.palm(g, t[0], t[1], t[2]) else CityGeo.tree(g, t[0], t[1], t[2])
                if (r.chance(0.3f)) CityGeo.bush(g, t[0] + 1.8f, t[1] + 1.2f, 0.7f)
            }
        }
        if (g.reg) for (t in pl.trees) g.solid(t[0] - 0.3f, t[1] - 0.3f, t[0] + 0.3f, t[1] + 0.3f)
    }

    /** Áreas a mais: pista de skate, cachorródromo, anfiteatro, vôlei de areia, roseiral, monumento, piquenique. */
    private fun extra(g: CityGeo.Gen, tp: Int, x: Float, z: Float, near: Boolean) {
        val b = g.b
        when (tp) {
            6 -> { if (g.reg) g.solid(x - 3f, z - 2f, x + 3f, z + 2f); if (!near) return
                b.m(Mt.STONE, 0.4f); b.box(x, CURB + 0.02f, z, 22f, 0.04f, 16f, C("#B7B4AE"))
                b.box(x, CURB + 0.6f, z, 6f, 1.2f, 4f, C("#A9A6A0")); b.m(Mt.METAL, 1f); b.box(x, CURB + 1.25f, z - 2f, 6f, 0.08f, 0.08f, C("#888888"))
                for (s in floatArrayOf(-1f, 1f)) { b.m(Mt.STONE, 0.4f); CityGeo.q(b, CityGeo.P(x + s * 10f, CURB + 0.04f, z - 6f) + CityGeo.P(x + s * 10f, CURB + 0.04f, z + 6f) + CityGeo.P(x + s * 7f, CURB + 1.4f, z + 6f) + CityGeo.P(x + s * 7f, CURB + 1.4f, z - 6f), C("#A9A6A0")) }
                b.m(Mt.METAL, 1f); b.box(x, CURB + 0.35f, z + 5.5f, 8f, 0.06f, 0.06f, C("#C9C9C9")) }
            7 -> { if (g.reg) { g.solid(x - 9f, z - 9.1f, x + 9f, z - 8.9f); g.solid(x - 9f, z + 8.9f, x + 3f, z + 9.1f); g.solid(x - 9.1f, z - 9f, x - 8.9f, z + 9f); g.solid(x + 8.9f, z - 9f, x + 9.1f, z + 9f) }; if (!near) return
                b.m(Mt.PLAIN); b.plane(x - 9f, z - 9f, x + 9f, z + 9f, CURB + 0.012f, C("#B9A57E"))
                b.m(Mt.METAL, 1f); b.box(x, CURB + 0.6f, z - 9f, 18f, 1.2f, 0.03f, C("#4A5A4F")); b.box(x - 3f, CURB + 0.6f, z + 9f, 12f, 1.2f, 0.03f, C("#4A5A4F")); b.box(x - 9f, CURB + 0.6f, z, 0.03f, 1.2f, 18f, C("#4A5A4F")); b.box(x + 9f, CURB + 0.6f, z, 0.03f, 1.2f, 18f, C("#4A5A4F"))
                b.m(Mt.WOOD, 0.5f); b.box(x - 4f, CURB + 0.4f, z, 3f, 0.08f, 0.4f, C("#8A5E3C")); b.box(x + 3f, CURB + 0.5f, z + 3f, 0.3f, 1f, 2.4f, C("#E05A47")) }
            8 -> { if (g.reg) g.solid(x - 4f, z + 6f, x + 4f, z + 9f); if (!near) return
                b.m(Mt.STONE, 0.6f); for (k in 0 until 5) b.cyl(x, CURB + k * 0.35f, z, 12f - k * 1.6f, 12f - k * 1.6f, 0.35f, C("#CFC8BA"), true, 32)
                b.m(Mt.WOOD, 0.5f); b.box(x, CURB + 0.6f, z + 7.5f, 8f, 1.2f, 3f, C("#8A5E3C")); b.m(Mt.FABRIC, 1f); b.box(x, CURB + 4f, z + 9f, 9f, 0.15f, 1f, C("#E9E2D6")) }
            9 -> { if (g.reg) g.solid(x - 4.6f, z - 0.15f, x + 4.6f, z + 0.15f); if (!near) return
                b.m(Mt.PLASTER, 0.7f); b.box(x, CURB + 0.03f, z, 10f, 0.06f, 18f, C("#EED9A8"))
                b.m(Mt.METAL, 1f); for (s in floatArrayOf(-4.6f, 4.6f)) b.box(x + s, CURB + 1.25f, z, 0.1f, 2.5f, 0.1f, C("#DDDDDD")); b.m(Mt.PLAIN); b.box(x, CURB + 2.15f, z, 9.2f, 0.9f, 0.02f, C("#2B2B2B")) }
            10 -> { if (!near) return
                // Etapa 158: roseiral de verdade — três anéis de roseiras em canteiro de terra, passeio de pedrisco entre eles e um arco de treliça
                b.m(Mt.PAVER, 0.6f); b.cyl(x, CURB, z, 8.6f, 8.6f, 0.02f, PATH, true, 28)
                b.m(Mt.STONE, 0.8f); b.cyl(x, CURB, z, 8.0f, 8.0f, 0.14f, STONE, true, 28)
                for ((q, d) in arrayOf(7.85f to 0.16f, 6.2f to 0.18f, 5.4f to 0.20f, 3.6f to 0.22f, 2.8f to 0.24f).withIndex()) { if (q % 2 == 0) b.m(Mt.PLAIN) else b.m(Mt.PAVER, 0.6f); b.cyl(x, CURB, z, d.first, d.first, d.second, if (q % 2 == 0) SOIL else PATH, true, 28) }
                for (k in 0 until 3) { val rr = 2.2f + k * 2.4f; val n = (rr * 4.2f).toInt().coerceAtLeast(6)
                    for (q in 0 until n) { val a = 6.283f * q / n + k * 0.3f; g.fl.place(if ((q + k) % 2 == 0) "bush_pink" else "bush_white", (x + cos(a) * rr).toDouble(), (CURB + 0.16f + (2 - k) * 0.04f).toDouble(), (z + sin(a) * rr).toDouble(), 1.25, a.toDouble()) } }
                b.m(Mt.STONE, 0.8f); b.cyl(x, CURB, z, 1.2f, 1.2f, 0.3f, STONE, true, 16); g.fl.place("cherry_a", x.toDouble(), (CURB + 0.3f).toDouble(), z.toDouble(), 0.8, 0.0)
                b.m(Mt.WOOD, 0.6f); for (sx in floatArrayOf(-1.1f, 1.1f)) b.box(x + sx, CURB + 1.25f, z + 8.2f, 0.14f, 2.5f, 0.14f, C("#F2EEE6")); b.box(x, CURB + 2.55f, z + 8.2f, 2.6f, 0.14f, 0.5f, C("#F2EEE6"))
                g.fl.place("bush_pink", x.toDouble(), (CURB + 2.5f).toDouble(), (z + 8.2f).toDouble(), 0.7, 0.0) }
            11 -> { if (g.reg) g.solid(x - 1.5f, z - 1.5f, x + 1.5f, z + 1.5f); if (!near) return
                b.m(Mt.STONE, 0.6f); b.box(x, CURB + 0.3f, z, 5f, 0.6f, 5f, C("#CFC8BA")); b.box(x, CURB + 0.9f, z, 2.8f, 0.6f, 2.8f, C("#BDB5A6"))
                b.cyl(x, CURB + 1.2f, z, 0.9f, 0.4f, 9f, C("#E6E0D3"), true, 4) }
            else -> { if (!near) return
                for (k in 0 until 4) { val px = x + (k % 2 - 0.5f) * 6f; val pz = z + (k / 2 - 0.5f) * 6f
                    b.m(Mt.WOOD, 0.5f); b.box(px, CURB + 0.75f, pz, 2.2f, 0.08f, 1.0f, C("#8A5E3C")); for (s in floatArrayOf(-0.7f, 0.7f)) b.box(px, CURB + 0.45f, pz + s, 2.2f, 0.06f, 0.3f, C("#7A5A3C"))
                    b.box(px, CURB + 0.37f, pz, 0.12f, 0.75f, 0.12f, C("#6B4A32")) }
                b.m(Mt.STONE, 1f); b.box(x + 4f, CURB + 0.4f, z, 1f, 0.8f, 0.8f, C("#6E6A64")) }
        }
    }

    private val FLOWERS = arrayOf("#E53935", "#FDD835", "#F06292", "#FFFFFF", "#FB8C00", "#8E24AA", "#EC407A", "#FFB300")
    private val HEDGE = C("#2F6B2F")
    private val FL = arrayOf("fl_tulip", "fl_daisy", "fl_poppy", "fl_lav", "fl_yellow")
    private val SOIL = C("#4A3626")
    private fun flower(g: CityGeo.Gen, id: String, x: Float, z: Float, y: Float, s: Float) = g.fl.place(id, x.toDouble(), y.toDouble(), z.toDouble(), s.toDouble(), (x * 7.3f + z * 3.1f).toDouble())

    /** Etapa 156: o lago vivo — chafariz no centro, carpas, vitórias-régias com flor, taboas, pedras, patos e uma borda florida. */
    private fun lakeLife(g: CityGeo.Gen, pl: Plan) {
        val b = g.b; val R = pl.lakeR; val wy = CURB + 0.33f; val r = City.Rng(8123)
        val ix = pl.cx + R * 0.3f; val iz = pl.cz - R * 0.2f; val ir = R * 0.18f + 1.5f
        fun free(x: Float, z: Float, m: Float) = hypot(x - pl.cx, z - pl.cz) < R - m && hypot(x - ix, z - iz) > ir + m && hypot(x - pl.cx, z - pl.cz) > 4.5f
        // chafariz: base de pedra, taça e jatos d'água
        b.m(Mt.STONE, 0.6f); b.cyl(pl.cx, wy - 0.3f, pl.cz, 3.0f, 2.6f, 0.9f, C("#CFC8BA"), true, 20); b.cyl(pl.cx, wy + 0.6f, pl.cz, 0.5f, 0.4f, 1.8f, C("#CFC8BA"), true, 10); b.cyl(pl.cx, wy + 2.4f, pl.cz, 0.5f, 1.9f, 0.4f, C("#CFC8BA"), true, 16)
        b.m(Mt.PLAIN); b.cyl(pl.cx, wy + 0.55f, pl.cz, 2.4f, 2.4f, 0.04f, C("#6FC3E6"), true, 20); b.cyl(pl.cx, wy + 2.76f, pl.cz, 1.7f, 1.7f, 0.04f, C("#6FC3E6"), true, 16)
        b.al = 0.75f
        b.cyl(pl.cx, wy + 2.8f, pl.cz, 0.28f, 0.05f, 4.6f, C("#E6F7FF"), true, 8)
        for (q in 0 until 8) { val a = q * 0.7854f; b.cyl(pl.cx + cos(a) * 1.3f, wy + 2.8f, pl.cz + sin(a) * 1.3f, 0.14f, 0.03f, 1.9f, C("#E6F7FF"), true, 6); b.cyl(pl.cx + cos(a) * 9f, wy, pl.cz + sin(a) * 9f, 0.2f, 0.03f, 2.6f, C("#E6F7FF"), true, 6) }
        b.al = 1f
        if (g.reg) g.solid(pl.cx - 2.6f, pl.cz - 2.6f, pl.cx + 2.6f, pl.cz + 2.6f)
        b.m(Mt.PLAIN)
        // vitórias-régias (algumas com flor) e taboas na margem
        repeat(46) { val a = r.r(0f, 6.283f); val d = r.r(R * 0.45f, R - 1.6f); val x = pl.cx + cos(a) * d; val z = pl.cz + sin(a) * d; if (!free(x, z, 1.0f)) return@repeat
            val rr = r.r(0.45f, 1.0f); b.cyl(x, wy + 0.05f, z, rr, rr, 0.025f, C(if (r.chance(0.5f)) "#3E8E41" else "#57A35A"), true, 9); b.cyl(x, wy + 0.055f, z, rr * 0.86f, rr * 0.86f, 0.026f, C("#6BBF6E"), true, 9)
            if (r.chance(0.4f)) { CityGeo.ball(b, x, wy + 0.17f, z, 0.2f, C(if (r.chance(0.5f)) "#F8BBD0" else "#FFFFFF"), 0.13f, 6); CityGeo.ball(b, x, wy + 0.25f, z, 0.08f, C("#FDD835"), 0.06f, 5) } }
        repeat(16) { val a = it * 0.3927f + r.r(-0.1f, 0.1f); if (abs(((a - 2.4f + 9.42f) % 6.283f) - 3.1416f) < 0.35f) return@repeat
            val x0 = pl.cx + cos(a) * (R - 1.0f); val z0 = pl.cz + sin(a) * (R - 1.0f)
            for (k in 0 until 7) { val x = x0 + r.r(-0.9f, 0.9f); val z = z0 + r.r(-0.9f, 0.9f); val h = r.r(1.1f, 2.0f)
                b.cyl(x, wy - 0.2f, z, 0.022f, 0.014f, h + 0.2f, C("#5C9A45"), true, 4)
                if (k % 2 == 0) { b.cyl(x, wy + h - 0.05f, z, 0.05f, 0.05f, 0.32f, C("#5E4330"), true, 6); b.cyl(x, wy + h + 0.27f, z, 0.012f, 0.004f, 0.18f, C("#5C9A45"), true, 4) }
                else { CityGeo.tri(b, CityGeo.P(x - 0.05f, wy, z) + CityGeo.P(x + 0.05f, wy, z) + CityGeo.P(x + 0.35f, wy + h * 0.9f, z + 0.2f), C("#6BA84F")); CityGeo.tri(b, CityGeo.P(x + 0.05f, wy, z) + CityGeo.P(x - 0.05f, wy, z) + CityGeo.P(x + 0.35f, wy + h * 0.9f, z + 0.2f), C("#6BA84F")) } }
            for (k in 0 until 3) g.fl.place("grass_a", (pl.cx + cos(a) * (R + 0.6f) + k * 0.4f - 0.4f).toDouble(), (CURB + 0.4f).toDouble(), (pl.cz + sin(a) * (R + 0.6f)).toDouble(), 2.6, k.toDouble()) }
        // pedras na borda e patos nadando
        b.m(Mt.STONE, 0.4f)
        repeat(18) { val a = r.r(0f, 6.283f); val s2 = r.r(0.5f, 1.1f); CityGeo.ball(b, pl.cx + cos(a) * (R - 0.4f), wy + 0.05f, pl.cz + sin(a) * (R - 0.4f), s2, C(arrayOf("#8E8A84", "#9C978E", "#7C7872")[r.i(3)]), s2 * 0.6f, 6) }
        // borda florida entre o lago e o anel: flores, arbustos redondos e ciprestes
        for (q in 0 until 40) { val a = q * 0.15708f; if (abs(((a - 2.4f + 9.42f) % 6.283f) - 3.1416f) < 0.2f) continue
            val x = pl.cx + cos(a) * (R + 2.7f); val z = pl.cz + sin(a) * (R + 2.7f)
            if (q % 5 == 0) { b.m(Mt.BARK, 1f); b.cyl(x, CURB, z, 0.12f, 0.1f, 0.5f, C("#5D4037"), true, 5); b.m(Mt.PLAIN); b.cyl(x, CURB + 0.4f, z, 0.75f, 0.05f, 4.2f, C("#2E5E32"), true, 7); if (g.reg) g.solid(x - 0.3f, z - 0.3f, x + 0.3f, z + 0.3f) }
            else if (q % 5 == 2) g.fl.place(if (q % 2 == 0) "bush_pink" else "bush_white", x.toDouble(), CURB.toDouble(), z.toDouble(), 1.0, a.toDouble())
            else for (k in 0 until 9) { val fa = k * 0.698f; val fr2 = if (k == 0) 0f else 0.75f; flower(g, FL[q % 5], x + cos(fa) * fr2, z + sin(fa) * fr2, CURB, 2.0f) } }
    }

    /** Etapa 157: gramado vivo — tufos de capim por todo o parque e manchas de flores do campo entre as árvores. */
    private fun lawnLife(g: CityGeo.Gen, pl: Plan) {
        val r = City.Rng(5521)
        val x0 = pl.gates[2][0] + 9f; val x1 = pl.gates[3][0] - 9f; val z0 = pl.gates[0][1] + 9f; val z1 = pl.gates[1][1] - 9f
        fun free(x: Float, z: Float, m: Float) = hypot(x - pl.cx, z - pl.cz) > pl.lakeR + 7f && pl.paths.none { distSeg(x, z, it) < pl.pw + m } && pl.spots.none { hypot(x - it[0], z - it[1]) < it[2] + m }
        repeat(1500) { val x = r.r(x0, x1); val z = r.r(z0, z1); if (free(x, z, 0.6f)) g.fl.place(if (it % 2 == 0) "grass_a" else "grass_b", x.toDouble(), CURB.toDouble(), z.toDouble(), r.r(2.6f, 4.2f).toDouble(), r.r(0f, 6f).toDouble()) }
        repeat(130) { val x = r.r(x0, x1); val z = r.r(z0, z1); if (!free(x, z, 4f)) return@repeat
            val sp = FL[r.i(5)]; val sp2 = FL[r.i(5)]
            for (k in 0 until 26) { val a = r.r(0f, 6.283f); val d = r.r(0f, 3.2f); flower(g, if (k % 3 == 0) sp2 else sp, x + cos(a) * d, z + sin(a) * d, CURB, r.r(1.5f, 2.1f)) } }
        // Etapa 158: cada área (quadra, parquinho, coreto...) ganha uma moldura de arbustos floridos e flores
        for (sp in pl.spots) { if (sp[3].toInt() == 13) continue; val n = (sp[2] * 1.3f).toInt().coerceIn(8, 30)
            for (k in 0 until n) { val a = 6.283f * k / n; val x = sp[0] + cos(a) * (sp[2] + 2.6f); val z = sp[1] + sin(a) * (sp[2] + 2.6f)
                if (pl.paths.any { distSeg(x, z, it) < pl.pw + 1.2f } || abs(cos(a)) > 0.93f) continue
                if (k % 3 == 0) g.fl.place(arrayOf("bush_pink", "bush_white", "bush_a", "bush_b")[(k / 3) % 4], x.toDouble(), CURB.toDouble(), z.toDouble(), 0.9, a.toDouble())
                else for (q in 0 until 5) flower(g, FL[(sp[3].toInt() + k) % 5], x + r.r(-0.6f, 0.6f), z + r.r(-0.6f, 0.6f), CURB, 1.9f) } }
        // cerejeiras em flor espalhadas, cada uma com um tapete de flores brancas e um banco embaixo de algumas
        var nc = 0; var tries = 0
        while (nc < 26 && tries++ < 700) { val x = r.r(x0, x1); val z = r.r(z0, z1); if (abs(x - pl.cx) < 60f || !free(x, z, 5f) || pl.trees.any { hypot(x - it[0], z - it[1]) < 6f }) continue
            g.fl.place("cherry_a", x.toDouble(), CURB.toDouble(), z.toDouble(), r.r(1.0f, 1.25f).toDouble(), r.r(0f, 6f).toDouble())
            for (k in 0 until 14) { val a = r.r(0f, 6.283f); val d = r.r(0.8f, 2.6f); flower(g, "fl_daisy", x + cos(a) * d, z + sin(a) * d, CURB, 1.6f) }
            if (nc % 2 == 0) bench(g.b, x + 2.2f, z, -1f, 0f)
            if (g.reg) g.solid(x - 0.3f, z - 0.3f, x + 0.3f, z + 0.3f); nc++ }
        // toalhas de piquenique com cesta
        repeat(10) { val x = r.r(x0, x1); val z = r.r(z0, z1); if (!free(x, z, 3f)) return@repeat; val b = g.b
            b.m(Mt.FABRIC, 1f); b.box(x, CURB + 0.012f, z, 2.2f, 0.02f, 1.7f, C(arrayOf("#C62828", "#1565C0", "#F9A825")[it % 3]))
            for (k in -2..2) b.box(x + k * 0.44f, CURB + 0.016f, z, 0.1f, 0.02f, 1.7f, C("#FFFFFF"))
            b.m(Mt.WOOD, 0.6f); b.box(x + 0.5f, CURB + 0.17f, z + 0.3f, 0.5f, 0.3f, 0.35f, C("#B48A60")); b.box(x + 0.5f, CURB + 0.45f, z + 0.3f, 0.04f, 0.26f, 0.3f, C("#8D6E63"))
            b.m(Mt.PLAIN); CityGeo.ball(b, x - 0.4f, CURB + 0.1f, z - 0.3f, 0.09f, C("#E53935"), 0.09f, 5); CityGeo.ball(b, x - 0.2f, CURB + 0.1f, z - 0.4f, 0.09f, C("#FB8C00"), 0.09f, 5) }
    }

    /** Etapa 156: faixas de flores coloridas com cerca viva dos dois lados dos quatro eixos. */
    private fun axisFlowers(g: CityGeo.Gen, pl: Plan) {
        val b = g.b
        for (pi in 1..4) { val p = pl.paths.getOrNull(pi) ?: continue; val n = p.size / 2
            var i = 3; var q = pi
            while (i + 3 < n - 4) {
                val t = Town.tangent(p, i + 1); val mx = (p[i * 2] + p[i * 2 + 6]) / 2; val mz = (p[i * 2 + 1] + p[i * 2 + 7]) / 2
                val L = hypot(p[i * 2 + 6] - p[i * 2], p[i * 2 + 7] - p[i * 2 + 1]) - 0.5f
                for (sd in floatArrayOf(-1f, 1f)) { val ox = -t[1] * sd * (pl.pw + 1.95f); val oz = t[0] * sd * (pl.pw + 1.95f)
                    b.m(Mt.STONE, 0.8f); TownGeo.obox(b, mx + ox, CURB + 0.09f, mz + oz, L + 0.3f, 0.18f, 1.3f, t[0], t[1], STONE)
                    b.m(Mt.PLAIN); TownGeo.obox(b, mx + ox, CURB + 0.11f, mz + oz, L, 0.2f, 1.0f, t[0], t[1], SOIL)
                    var tt = -L / 2 + 0.3f; var kk = 0
                    while (tt < L / 2 - 0.2f) { val w = if (kk % 2 == 0) -0.24f else 0.24f
                        flower(g, FL[q % 5], mx + ox + t[0] * tt - t[1] * w, mz + oz + t[1] * tt + t[0] * w, CURB + 0.2f, 1.9f); tt += 0.5f; kk++ }
                    b.m(Mt.GRASS, 0.5f); TownGeo.obox(b, mx + ox * 1.42f, CURB + 0.35f, mz + oz * 1.42f, L + 0.3f, 0.7f, 0.5f, t[0], t[1], HEDGE) }
                i += 4; q++
            }
        }
    }

    /** Etapa 156: jardim formal — cerca viva em volta com quatro portões, caminhos em cruz, quatro canteiros de flores em degraus e um centro diferente em cada um. */
    private fun parterre(g: CityGeo.Gen, x: Float, z: Float, style: Int) {
        val b = g.b; val hw = 14f; val hd = 16f; val r = City.Rng(style * 131 + 7)
        if (g.reg) { for (sx in floatArrayOf(-1f, 1f)) { g.solid(x + sx * hw - 0.3f, z - hd, x + sx * hw + 0.3f, z - 2f); g.solid(x + sx * hw - 0.3f, z + 2f, x + sx * hw + 0.3f, z + hd) }
            for (sz in floatArrayOf(-1f, 1f)) { g.solid(x - hw, z + sz * hd - 0.3f, x - 2f, z + sz * hd + 0.3f); g.solid(x + 2f, z + sz * hd - 0.3f, x + hw, z + sz * hd + 0.3f) }
            g.solid(x - 1.6f, z - 1.6f, x + 1.6f, z + 1.6f) }
        if (b.countOnly && false) return
        // cerca viva com portões
        b.m(Mt.GRASS, 0.5f)
        for (sx in floatArrayOf(-1f, 1f)) for (sz in floatArrayOf(-1f, 1f)) {
            b.box(x + sx * hw, CURB + 0.45f, z + sz * (hd + 2f) / 2, 0.7f, 0.9f, hd - 2f, HEDGE); b.box(x + sx * (hw + 2f) / 2, CURB + 0.45f, z + sz * hd, hw - 2f, 0.9f, 0.7f, HEDGE)
            // cipreste em cada canto e bola de buxo em cada portão
            b.m(Mt.PLAIN); b.cyl(x + sx * hw, CURB + 0.3f, z + sz * hd, 0.9f, 0.05f, 4.8f, C("#2E5E32"), true, 7)
            CityGeo.ball(b, x + sx * hw, CURB + 1.1f, z + sz * 2.4f, 0.7f, C("#3E8E41"), 0.7f, 6); CityGeo.ball(b, x + sx * 2.4f, CURB + 1.1f, z + sz * hd, 0.7f, C("#3E8E41"), 0.7f, 6)
            b.m(Mt.GRASS, 0.5f)
        }
        // caminhos em cruz e rotatória central
        b.m(Mt.PAVER, 0.6f); b.box(x, CURB + 0.012f, z, 2.6f, 0.02f, hd * 2, PATH); b.box(x, CURB + 0.012f, z, hw * 2, 0.02f, 2.6f, PATH); b.cyl(x, CURB, z, 5.2f, 5.2f, 0.024f, PATH, true, 20)
        // quatro canteiros em degraus de cor
        val c1 = C(FLOWERS[style % 8]); val c2 = C(FLOWERS[(style + 3) % 8]); val c3 = C(FLOWERS[(style + 5) % 8])
        for (sx in floatArrayOf(-1f, 1f)) for (sz in floatArrayOf(-1f, 1f)) { val qx = x + sx * (hw / 2 + 1.0f); val qz = z + sz * (hd / 2 + 1.0f)
            b.m(Mt.STONE, 0.8f); b.box(qx, CURB + 0.1f, qz, hw - 4.2f, 0.2f, hd - 4.2f, STONE)
            // Etapa 157: canteiro de terra plantado com flores de verdade, em faixas (uma espécie por faixa) e um arbusto florido no meio
            b.m(Mt.PLAIN); b.box(qx, CURB + 0.16f, qz, hw - 4.8f, 0.3f, hd - 4.8f, SOIL)
            val bw = (hw - 5.4f) / 2; val bd = (hd - 5.4f) / 2
            var fx = -bw; while (fx <= bw) { var fz = -bd; while (fz <= bd) {
                val band = max(abs(fx) / bw, abs(fz) / bd)
                if (band > 0.18f) flower(g, FL[(style + (if (band > 0.7f) 0 else if (band > 0.42f) 2 else 4)) % 5], qx + fx + r.r(-0.15f, 0.15f), qz + fz + r.r(-0.15f, 0.15f), CURB + 0.3f, r.r(1.7f, 2.3f))
                fz += 0.95f }; fx += 0.95f }
            g.fl.place(if ((style + (if (sx > 0) 1 else 0)) % 2 == 0) "bush_pink" else "bush_white", qx.toDouble(), (CURB + 0.3f).toDouble(), qz.toDouble(), 1.1, 0.0) }
        // centro
        when (style % 4) {
            0 -> { b.m(Mt.STONE, 0.6f); b.cyl(x, CURB, z, 2.6f, 2.6f, 0.6f, C("#CFC8BA"), true, 18); b.cyl(x, CURB + 0.6f, z, 0.35f, 0.3f, 1.5f, C("#CFC8BA"), true, 8); b.cyl(x, CURB + 2.1f, z, 0.3f, 1.2f, 0.3f, C("#CFC8BA"), true, 12)
                b.m(Mt.PLAIN); b.cyl(x, CURB + 0.52f, z, 2.3f, 2.3f, 0.05f, C("#6FC3E6"), true, 18); b.al = 0.75f; b.cyl(x, CURB + 2.4f, z, 0.16f, 0.03f, 2.2f, C("#E6F7FF"), true, 6); b.al = 1f }
            1 -> { b.m(Mt.STONE, 0.6f); b.box(x, CURB + 0.2f, z, 2.4f, 0.4f, 2.4f, C("#B8B2A6")); b.box(x, CURB + 1.0f, z, 1.3f, 1.2f, 1.3f, C("#CFC8BA"))
                b.m(Mt.METAL, 1f); b.cyl(x, CURB + 1.6f, z, 0.32f, 0.22f, 1.5f, C("#7A6A45"), true, 8); CityGeo.ball(b, x, CURB + 3.35f, z, 0.26f, C("#7A6A45"), 0.3f, 7); b.box(x, CURB + 2.75f, z, 1.1f, 0.16f, 0.2f, C("#7A6A45")) }
            2 -> { CityGeo.tree(g, x, z, 1.35f, CURB, 0); b.m(Mt.WOOD, 0.6f)
                for (q in 0 until 8) { val a = q * 0.7854f; TownGeo.obox(b, x + cos(a) * 2.2f, CURB + 0.45f, z + sin(a) * 2.2f, 1.75f, 0.08f, 0.55f, -sin(a), cos(a), C("#8D6E63")); b.box(x + cos(a) * 2.2f, CURB + 0.22f, z + sin(a) * 2.2f, 0.1f, 0.44f, 0.1f, C("#4A4A4A")) } }
            else -> { b.m(Mt.WOOD, 0.6f); for (sx in floatArrayOf(-1.9f, 1.9f)) for (sz in floatArrayOf(-1.9f, 1.9f)) b.box(x + sx, CURB + 1.4f, z + sz, 0.22f, 2.8f, 0.22f, C("#F2EEE6"))
                for (k in -3..3) b.box(x + k * 0.62f, CURB + 2.95f, z, 0.12f, 0.16f, 4.6f, C("#F2EEE6")); for (sz in floatArrayOf(-1.9f, 1.9f)) b.box(x, CURB + 2.84f, z + sz, 4.6f, 0.16f, 0.16f, C("#F2EEE6"))
                for (k in 0 until 5) g.fl.place(if (k % 2 == 0) "bush_pink" else "bush_white", (x + (k - 2) * 0.95f).toDouble(), (CURB + 2.95f).toDouble(), (z + (if (k % 2 == 0) -0.9f else 0.9f)).toDouble(), 0.75, k.toDouble())
                for (sx in floatArrayOf(-1.9f, 1.9f)) for (sz in floatArrayOf(-1.9f, 1.9f)) for (k in 0 until 4) flower(g, "fl_lav", x + sx + (if (k % 2 == 0) 0.3f else -0.3f), z + sz + (if (k < 2) 0.3f else -0.3f), CURB, 2.2f)
                bench(b, x, z + 1.2f, 0f, -1f) }
        }
    }

    private fun bench(b: MB, x: Float, z: Float, fx: Float, fz: Float) {
        b.m(Mt.WOOD, 0.5f)
        TownGeo.obox(b, x, CURB + 0.45f, z, 1.8f, 0.08f, 0.45f, -fz, fx, C("#8A5E3C"))
        TownGeo.obox(b, x - fx * 0.22f, CURB + 0.75f, z - fz * 0.22f, 1.8f, 0.4f, 0.06f, -fz, fx, C("#8A5E3C"))
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-0.75f, 0.75f)) TownGeo.obox(b, x - fz * s, CURB + 0.22f, z + fx * s, 0.08f, 0.45f, 0.5f, -fz, fx, C("#2E3236"))
    }

    private fun playground(g: CityGeo.Gen, x: Float, z: Float) {
        val b = g.b
        if (g.reg) { g.solid(x - 5f, z - 1.2f, x - 1f, z + 1.2f); g.solid(x + 1.5f, z - 2f, x + 5f, z + 2f) }
        // piso emborrachado
        b.m(Mt.PLAIN); b.cyl(x, CURB, z, 8.5f, 8.5f, 0.03f, C("#C9603E"), true, 32)
        b.m(Mt.PLAIN); b.cyl(x, CURB, z, 8.8f, 8.8f, 0.02f, C("#D9D3C7"), true, 32)
        // balanço
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-5f, -1f)) { b.box(x + s, CURB + 1.25f, z - 1.1f, 0.1f, 2.5f, 0.1f, C("#E0452E")); b.box(x + s, CURB + 1.25f, z + 1.1f, 0.1f, 2.5f, 0.1f, C("#E0452E")) }
        b.box(x - 3f, CURB + 2.5f, z, 4.2f, 0.12f, 0.12f, C("#E0452E"))
        for (s in floatArrayOf(-4f, -2f)) { b.box(x + s, CURB + 1.5f, z, 0.03f, 2f, 0.03f, C("#777777")); b.m(Mt.PLAIN); b.box(x + s, CURB + 0.5f, z, 0.5f, 0.06f, 0.2f, C("#222222")); b.m(Mt.METAL, 1f) }
        // escorregador com torre
        b.m(Mt.WOOD, 0.5f); b.box(x + 3.2f, CURB + 0.9f, z, 2f, 0.12f, 2f, C("#9A7350"))
        for (sx in floatArrayOf(2.3f, 4.1f)) for (sz in floatArrayOf(-0.9f, 0.9f)) b.box(x + sx, CURB + 1.3f, z + sz, 0.14f, 2.6f, 0.14f, C("#2E7DC5"))
        b.m(Mt.PLAIN); b.box(x + 3.2f, CURB + 2.65f, z, 2.3f, 0.12f, 2.3f, C("#F2C230"))
        CityGeo.q(b, floatArrayOf(x + 3.6f, CURB + 0.95f, z + 1f, x + 3.6f, CURB + 0.95f, z - 1f, x + 3.6f + 0f, CURB + 0.95f, z - 1f, x + 3.6f, CURB + 0.95f, z + 1f), C("#2E7DC5"))
        b.box(x + 3.2f, CURB + 0.5f, z + 3.2f, 0.8f, 0.06f, 3f, C("#2EA35A"))
        // gangorra e gira-gira
        b.box(x, CURB + 0.45f, z + 5.5f, 3.4f, 0.08f, 0.3f, C("#F2C230")); b.box(x, CURB + 0.22f, z + 5.5f, 0.2f, 0.45f, 0.2f, C("#555555"))
        b.cyl(x - 3f, CURB, z - 5f, 1.4f, 1.4f, 0.25f, C("#E0452E"), true, 16)
        CityGeo.publicBench(b, x + 6.8f, z - 5f, -1f, 0f)
    }

    private fun court(g: CityGeo.Gen, x: Float, z: Float, near: Boolean) {
        val b = g.b; val w = 15f; val d = 28f
        if (g.reg) { g.solid(x - w / 2 - 0.1f, z - d / 2, x - w / 2 + 0.1f, z + d / 2); g.solid(x + w / 2 - 0.1f, z - d / 2, x + w / 2 + 0.1f, z + d / 2); g.solid(x - w / 2, z + d / 2 - 0.1f, x + w / 2, z + d / 2 + 0.1f) }
        if (!near) { g.f.m(Mt.PLAIN); g.f.plane(x - w / 2, z - d / 2, x + w / 2, z + d / 2, CURB + 0.02f, C("#3E6FA8")); return }
        b.m(Mt.PLAIN)
        b.plane(x - w / 2 - 1f, z - d / 2 - 1f, x + w / 2 + 1f, z + d / 2 + 1f, CURB + 0.02f, C("#C25B3C"))
        b.plane(x - w / 2, z - d / 2, x + w / 2, z + d / 2, CURB + 0.045f, C("#3E6FA8"))
        val wt = C("#F4F4F4")
        for (zz in floatArrayOf(z - d / 2, z + d / 2, z)) b.plane(x - w / 2, zz - 0.05f, x + w / 2, zz + 0.05f, CURB + 0.07f, wt)
        for (xx in floatArrayOf(x - w / 2, x + w / 2)) b.plane(xx - 0.05f, z - d / 2, xx + 0.05f, z + d / 2, CURB + 0.07f, wt)
        b.cyl(x, CURB + 0.06f, z, 1.8f, 1.8f, 0.006f, wt, true, 24)
        for (s in floatArrayOf(-1f, 1f)) {
            b.plane(x - 2.4f, if (s < 0) z - d / 2 else z + d / 2 - 5.8f, x + 2.4f, if (s < 0) z - d / 2 + 5.8f else z + d / 2, CURB + 0.055f, C("#C25B3C"))
            b.m(Mt.METAL, 1f)
            b.box(x, CURB + 1.5f, z + s * (d / 2 + 0.6f), 0.15f, 3f, 0.15f, C("#555555"))
            b.box(x, CURB + 3.0f, z + s * (d / 2 - 0.1f), 0.12f, 0.12f, 1.4f, C("#555555"))
            b.box(x, CURB + 3.3f, z + s * (d / 2 - 0.75f), 1.8f, 1.1f, 0.06f, C("#FFFFFF"))
            b.m(Mt.PLAIN); b.cyl(x, CURB + 3.05f, z + s * (d / 2 - 1.2f), 0.23f, 0.23f, 0.03f, C("#E0452E"), true, 12)
        }
        b.m(Mt.METAL, 1f)
        b.box(x - w / 2, CURB + 1.5f, z, 0.03f, 3f, d, C("#5A6B5F")); b.box(x + w / 2, CURB + 1.5f, z, 0.03f, 3f, d, C("#5A6B5F")); b.box(x, CURB + 1.5f, z + d / 2, w, 3f, 0.03f, C("#5A6B5F"))
    }

    private fun soccer(g: CityGeo.Gen, x: Float, z: Float, near: Boolean) {
        val b = g.b; val w = 30f; val d = 50f
        if (!near) { g.f.m(Mt.GRASS, 0.3f); g.f.plane(x - w / 2, z - d / 2, x + w / 2, z + d / 2, CURB + 0.02f, C("#7FBF5A")); return }
        b.m(Mt.GRASS, 0.25f); b.plane(x - w / 2, z - d / 2, x + w / 2, z + d / 2, CURB + 0.012f, C("#8FCF6A"))
        for (k in 0 until 10) if (k % 2 == 0) b.plane(x - w / 2, z - d / 2 + k * d / 10, x + w / 2, z - d / 2 + (k + 1) * d / 10, CURB + 0.016f, C("#7FBF5A"))
        b.m(Mt.PLAIN)
        val wt = C("#F4F4F4"); val y = CURB + 0.02f
        for (zz in floatArrayOf(z - d / 2, z + d / 2, z)) b.plane(x - w / 2, zz - 0.06f, x + w / 2, zz + 0.06f, y, wt)
        for (xx in floatArrayOf(x - w / 2, x + w / 2)) b.plane(xx - 0.06f, z - d / 2, xx + 0.06f, z + d / 2, y, wt)
        for (s in floatArrayOf(-1f, 1f)) {
            val ze = z + s * d / 2
            b.plane(x - 6f, if (s < 0) ze else ze - 8f, x - 5.88f, if (s < 0) ze + 8f else ze, y, wt); b.plane(x + 5.88f, if (s < 0) ze else ze - 8f, x + 6f, if (s < 0) ze + 8f else ze, y, wt)
            b.plane(x - 6f, ze + s * -8f - 0.06f, x + 6f, ze + s * -8f + 0.06f, y, wt)
            b.m(Mt.METAL, 1f)
            for (sx in floatArrayOf(-2.5f, 2.5f)) b.box(x + sx, CURB + 1.1f, ze, 0.12f, 2.2f, 0.12f, wt)
            b.box(x, CURB + 2.2f, ze, 5.1f, 0.12f, 0.12f, wt)
            b.box(x, CURB + 1.1f, ze + s * 1f, 5f, 2.2f, 0.02f, C("#DDDDDD"))
            b.m(Mt.PLAIN)
            if (g.reg) g.solid(x - 2.6f, min(ze, ze + s * 1f) - 0.1f, x + 2.6f, max(ze, ze + s * 1f) + 0.1f)
        }
        b.cyl(x, y, z, 6f, 6f, 0.004f, wt, true, 32); b.cyl(x, y + 0.002f, z, 5.88f, 5.88f, 0.004f, C("#8FCF6A"), true, 32)
        // arquibancada pequena de um lado
        b.m(Mt.STONE, 0.6f); for (k in 0..2) b.box(x + w / 2 + 2f + k * 0.8f, CURB + 0.2f + k * 0.4f, z, 0.8f, 0.4f, 16f, C("#B9B3A8"))
        if (g.reg) g.solid(x + w / 2 + 1.5f, z - 8f, x + w / 2 + 4.5f, z + 8f)
    }

    private fun gym(g: CityGeo.Gen, x: Float, z: Float) {
        val b = g.b
        b.m(Mt.PLAIN); b.cyl(x, CURB, z, 7f, 7f, 0.03f, C("#5E8C4A"), true, 28)
        for (k in 0 until 5) {
            val a = k * 1.2566f; val px = x + cos(a) * 4.5f; val pz = z + sin(a) * 4.5f
            b.m(Mt.METAL, 1f)
            b.box(px, CURB + 0.9f, pz, 0.12f, 1.8f, 0.12f, C("#F2C230")); b.box(px, CURB + 1.8f, pz, 1.4f, 0.1f, 0.1f, C("#2E7DC5"))
            b.box(px + 0.5f, CURB + 0.6f, pz, 0.5f, 0.08f, 0.3f, C("#2E7DC5"))
            if (g.reg) g.solid(px - 0.4f, pz - 0.4f, px + 0.4f, pz + 0.4f)
        }
    }

    private fun kiosk(g: CityGeo.Gen, x: Float, z: Float, near: Boolean) {
        val b = g.b
        if (g.reg) g.solid(x - 2f, z - 2f, x + 2f, z + 2f)
        if (!near) { g.f.m(Mt.PLAIN); g.f.box(x, CURB + 1.5f, z, 4f, 3f, 4f, C("#E8D5B0")); return }
        b.m(Mt.WOOD, 0.5f); b.box(x, CURB + 1.4f, z, 4f, 2.8f, 4f, C("#C9A27A"))
        b.m(Mt.PLAIN); for (s in 0..3) { val a = s * 1.5708f; b.box(x + cos(a) * 2.02f, CURB + 1.5f, z + sin(a) * 2.02f, if (s % 2 == 0) 0.04f else 2.6f, 1.0f, if (s % 2 == 0) 2.6f else 0.04f, C("#3B2A1E")) }
        b.m(Mt.ROOF, 0.6f); b.cyl(x, CURB + 2.8f, z, 3.4f, 0.1f, 1.4f, C("#B5523B"), true, 4)
        // mesas com guarda-sol em volta
        for (k in 0 until 4) {
            val a = k * 1.5708f + 0.785f; val tx = x + cos(a) * 5f; val tz = z + sin(a) * 5f
            b.m(Mt.WOOD, 0.5f); b.cyl(tx, CURB, tz, 0.5f, 0.5f, 0.75f, C("#8A5E3C"), true, 10)
            b.m(Mt.FABRIC, 1f); b.cyl(tx, CURB + 2.2f, tz, 1.4f, 0.05f, 0.45f, C(arrayOf("#E05A47", "#F2C230", "#2E7DC5", "#2EA35A")[k]), true, 10)
            b.m(Mt.METAL, 1f); b.cyl(tx, CURB + 0.75f, tz, 0.03f, 0.03f, 1.5f, C("#DDDDDD"), true, 5)
            if (g.reg) g.solid(tx - 0.5f, tz - 0.5f, tx + 0.5f, tz + 0.5f)
        }
    }

    private fun gazebo(g: CityGeo.Gen, x: Float, z: Float, near: Boolean) {
        val b = g.b
        if (g.reg) for (k in 0 until 8) { val a = k * 0.785f; g.solid(x + cos(a) * 4f - 0.15f, z + sin(a) * 4f - 0.15f, x + cos(a) * 4f + 0.15f, z + sin(a) * 4f + 0.15f) }
        if (!near) return
        b.m(Mt.STONE, 0.6f); b.cyl(x, CURB, z, 4.6f, 4.6f, 0.45f, C("#D9D3C7"), true, 8)
        b.m(Mt.PLAIN); for (k in 0 until 8) { val a = k * 0.785f; b.cyl(x + cos(a) * 4f, CURB + 0.45f, z + sin(a) * 4f, 0.12f, 0.12f, 2.8f, C("#FBFBF8"), true, 8) }
        b.m(Mt.ROOF, 0.6f); b.cyl(x, CURB + 3.25f, z, 5f, 0.1f, 2.2f, C("#3E5A48"), true, 8)
        b.m(Mt.PLAIN); b.cyl(x, CURB + 3.2f, z, 4.4f, 4.4f, 0.12f, C("#FBFBF8"), true, 8)
    }

    @Suppress("unused") private fun unused() = atan2(0f, 1f) + sqrt(1f)
}
