package com.vinicius.meular

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

/** Etapa 151: hipotenusa rápida (Math.hypot é muito lenta e aqui é chamada milhões de vezes na montagem). */
private fun hypot(a: Float, b: Float): Float = kotlin.math.sqrt(a * a + b * b)

/** Etapa 131: desenho das ruas curvas, cruzamentos, rotatória, calçadas e chão dos quarteirões. */
object TownGeo {
    private const val CURB = Town.CURB
    private const val SW = Town.SW
    private val ASPH = C("#FFFFFF")
    private val WALK = C("#E3E0DA")
    private val CURBC = C("#C9C6C0")
    private val YEL = C("#F2C230")
    private val WHT = C("#F4F4F4")
    private val GRASS = C("#D6EEC4")

    // ------------------------------------------------------------ primitivas

    /** Faixa no chão entre a linha da direita [r] e a da esquerda [l] (mesmo número de pontos), virada para cima. */
    fun ribbon(b: MB, r: FloatArray, l: FloatArray, y: Float, c: Int) {
        val n = min(r.size, l.size) / 2
        for (i in 0 until n - 1) {
            val ax = r[i * 2]; val az = r[i * 2 + 1]; val bx = r[i * 2 + 2]; val bz = r[i * 2 + 3]
            val cx = l[i * 2 + 2]; val cz = l[i * 2 + 3]; val dx = l[i * 2]; val dz = l[i * 2 + 1]
            b.v(ax, y, az, 0f, 1f, 0f, c, ax, az); b.v(bx, y, bz, 0f, 1f, 0f, c, bx, bz); b.v(cx, y, cz, 0f, 1f, 0f, c, cx, cz)
            b.v(ax, y, az, 0f, 1f, 0f, c, ax, az); b.v(cx, y, cz, 0f, 1f, 0f, c, cx, cz); b.v(dx, y, dz, 0f, 1f, 0f, c, dx, dz)
        }
    }

    /** Parede vertical ao longo da linha [p], de y0 a y1, virada para a esquerda (left = true) ou direita de quem anda pela linha. */
    fun curbWall(b: MB, p: FloatArray, y0: Float, y1: Float, left: Boolean, c: Int) {
        val n = p.size / 2
        for (i in 0 until n - 1) {
            var ax = p[i * 2]; var az = p[i * 2 + 1]; var bx = p[i * 2 + 2]; var bz = p[i * 2 + 3]
            val dx = bx - ax; val dz = bz - az; val l = max(1e-5f, hypot(dx, dz))
            var nx = -dz / l; var nz = dx / l
            if (!left) { nx = -nx; nz = -nz; val tx = ax; val tz = az; ax = bx; az = bz; bx = tx; bz = tz }
            val u0 = 0f; val u1 = l
            b.v(ax, y0, az, nx, 0f, nz, c, u0, y0); b.v(bx, y0, bz, nx, 0f, nz, c, u1, y0); b.v(bx, y1, bz, nx, 0f, nz, c, u1, y1)
            b.v(ax, y0, az, nx, 0f, nz, c, u0, y0); b.v(bx, y1, bz, nx, 0f, nz, c, u1, y1); b.v(ax, y1, az, nx, 0f, nz, c, u0, y1)
        }
    }

    /** Triângulos (x, z) planos, virados para cima. */
    fun tris(b: MB, t: FloatArray, y: Float, c: Int) {
        if (b.countOnly) return   // Etapa 151: malha de perto na montagem não é usada
        var i = 0
        while (i + 5 < t.size) {
            if (b.warp) split(b, t[i], t[i + 1], t[i + 2], t[i + 3], t[i + 4], t[i + 5], y, c, 0)
            else { b.v(t[i], y, t[i + 1], 0f, 1f, 0f, c, t[i], t[i + 1]); b.v(t[i + 2], y, t[i + 3], 0f, 1f, 0f, c, t[i + 2], t[i + 3]); b.v(t[i + 4], y, t[i + 5], 0f, 1f, 0f, c, t[i + 4], t[i + 5]) }
            i += 6
        }
    }

    /** Etapa 147: triângulo grande vira pedaços de até ~7 m (o relevo dobra o chão sem buraco). */
    private fun split(b: MB, ax: Float, az: Float, bx: Float, bz: Float, cx: Float, cz: Float, y: Float, c: Int, d: Int) {
        val ab = hypot(bx - ax, bz - az); val bc = hypot(cx - bx, cz - bz); val ca = hypot(ax - cx, az - cz)
        val m = max(ab, max(bc, ca))
        // Etapa 150: no relevo, pedaços de ~2 m (a malha acompanha os platôs sem rampa de grama por cima do gramado)
        // Etapa 150: triângulo inteiro dentro de um lote do relevo some (o lote tem o próprio gramado); na borda de lote, pedaços de ~1 m
        var lim = 7f
        // Etapa 155: chão plano (sem relevo em nenhum ponto do triângulo) não precisa ser picado — o gramado do parque sozinho tinha 600 mil vértices
        if (m > 7f && m < 400f && Town.terrain(ax, az) == 0f && Town.terrain(bx, bz) == 0f && Town.terrain(cx, cz) == 0f && Town.terrain((ax + bx) / 2, (az + bz) / 2) == 0f && Town.terrain((bx + cx) / 2, (bz + cz) / 2) == 0f && Town.terrain((cx + ax) / 2, (cz + az) / 2) == 0f && Town.terrain((ax + bx + cx) / 3, (az + bz + cz) / 3) == 0f) lim = 1e9f
        if (b.warp && m <= 7f && Town.terrain((ax + bx + cx) / 3, (az + bz + cz) / 3) != 0f) {
            val la = TownHouses.reliefLot(ax, az); val lb = TownHouses.reliefLot(bx, bz); val lc = TownHouses.reliefLot(cx, cz)
            val l1 = TownHouses.reliefLot((ax + bx) / 2, (az + bz) / 2); val l2 = TownHouses.reliefLot((bx + cx) / 2, (bz + cz) / 2); val l3 = TownHouses.reliefLot((cx + ax) / 2, (cz + az) / 2)
            val l4 = TownHouses.reliefLot((ax + bx + cx) / 3, (az + bz + cz) / 3)
            // inteiro dentro de lotes (cada lote tem o próprio gramado nivelado): some
            if (la != null && lb != null && lc != null && l1 != null && l2 != null && l3 != null && l4 != null) return
            // Etapa 151: na borda de um lote só refina onde o chão de fora fica acima do gramado do lote (senão ele já fica escondido embaixo)
            var pmin = Float.MAX_VALUE
            for (q in arrayOf(la, lb, lc, l1, l2, l3, l4)) if (q != null && q.pad < pmin) pmin = q.pad
            if (pmin != Float.MAX_VALUE && max(Town.meshElev(ax, az), max(Town.meshElev(bx, bz), Town.meshElev(cx, cz))) > pmin - 0.04f) lim = 2.0f
        }
        if (m <= lim || d > 20) { b.v(ax, y, az, 0f, 1f, 0f, c, ax, az); b.v(bx, y, bz, 0f, 1f, 0f, c, bx, bz); b.v(cx, y, cz, 0f, 1f, 0f, c, cx, cz); return }
        when (m) {
            ab -> { val mx = (ax + bx) / 2; val mz = (az + bz) / 2; split(b, ax, az, mx, mz, cx, cz, y, c, d + 1); split(b, mx, mz, bx, bz, cx, cz, y, c, d + 1) }
            bc -> { val mx = (bx + cx) / 2; val mz = (bz + cz) / 2; split(b, ax, az, bx, bz, mx, mz, y, c, d + 1); split(b, ax, az, mx, mz, cx, cz, y, c, d + 1) }
            else -> { val mx = (cx + ax) / 2; val mz = (cz + az) / 2; split(b, ax, az, bx, bz, mx, mz, y, c, d + 1); split(b, mx, mz, bx, bz, cx, cz, y, c, d + 1) }
        }
    }

    /** Leque a partir do centro (polígono estrelado em volta de cx, cz), virado para cima. */
    fun fan(b: MB, cx: Float, cz: Float, p: FloatArray, y: Float, c: Int) {
        val n = p.size / 2
        for (i in 0 until n) {
            val j = (i + 1) % n
            b.v(cx, y, cz, 0f, 1f, 0f, c, cx, cz); b.v(p[i * 2], y, p[i * 2 + 1], 0f, 1f, 0f, c, p[i * 2], p[i * 2 + 1]); b.v(p[j * 2], y, p[j * 2 + 1], 0f, 1f, 0f, c, p[j * 2], p[j * 2 + 1])
        }
    }

    /** Retângulo plano girado (marca no chão): centro, direção (fx, fz), comprimento ao longo e largura. */
    fun mark(b: MB, cx: Float, cz: Float, fx: Float, fz: Float, len: Float, wid: Float, y: Float, c: Int) {
        val ax = fx * len / 2; val az = fz * len / 2; val sx = -fz * wid / 2; val sz = fx * wid / 2
        val r = floatArrayOf(cx - ax - sx, cz - az - sz, cx + ax - sx, cz + az - sz)
        val l = floatArrayOf(cx - ax + sx, cz - az + sz, cx + ax + sx, cz + az + sz)
        ribbon(b, r, l, y, c)
    }

    /** Caixa girada em volta de y (rumo fx, fz). */
    fun obox(b: MB, cx: Float, cy: Float, cz: Float, len: Float, h: Float, wid: Float, fx: Float, fz: Float, c: Int) {
        val ax = fx * len / 2; val az = fz * len / 2; val sx = -fz * wid / 2; val sz = fx * wid / 2
        val px = floatArrayOf(cx - ax - sx, cx + ax - sx, cx + ax + sx, cx - ax + sx)
        val pz = floatArrayOf(cz - az - sz, cz + az - sz, cz + az + sz, cz - az + sz)
        val y0 = cy - h / 2; val y1 = cy + h / 2
        val top = FloatArray(8) { if (it % 2 == 0) px[it / 2] else pz[it / 2] }
        tris(b, floatArrayOf(px[0], pz[0], px[1], pz[1], px[2], pz[2], px[0], pz[0], px[2], pz[2], px[3], pz[3]), y1, c)
        val ring = floatArrayOf(px[0], pz[0], px[1], pz[1], px[2], pz[2], px[3], pz[3], px[0], pz[0])
        curbWall(b, ring, y0, y1, false, c)
        if (top.isEmpty()) return
    }

    // ------------------------------------------------------------ ruas

    // ------------------------------------------------------------ pedaços (carregados perto do jogador)

    // Etapa 151: pedaços menores (180 m): o detalhe em volta do jogador fica pronto bem mais rápido e gasta menos memória
    const val TILE = 180f
    class Tile(val i: Int, val j: Int) {
        val edges = ArrayList<Int>(); val nodes = ArrayList<Int>(); val blocks = ArrayList<Int>(); val lots = ArrayList<Int>()
        var x0 = Float.MAX_VALUE; var z0 = Float.MAX_VALUE; var x1 = -Float.MAX_VALUE; var z1 = -Float.MAX_VALUE
        fun grow(p: FloatArray, m: Float) { var k = 0; while (k < p.size) { x0 = min(x0, p[k] - m); x1 = max(x1, p[k] + m); z0 = min(z0, p[k + 1] - m); z1 = max(z1, p[k + 1] + m); k += 2 } }
    }
    val tiles = ArrayList<Tile>()

    private fun tileOf(x: Float, z: Float, map: HashMap<Long, Tile>): Tile {
        val i = Math.floor(x / TILE.toDouble()).toInt(); val j = Math.floor(z / TILE.toDouble()).toInt()
        return map.getOrPut(i.toLong() * 100000L + j) { Tile(i, j) }
    }

    /** Monta os pedaços: cada um com a versão de longe pronta e a de perto gerada de novo quando o jogador chegar. */
    fun build(out: ArrayList<City.Chunk>) {
        tiles.clear()
        Elevado.plan()
        val map = HashMap<Long, Tile>()
        for ((ei, ed) in Town.edges.withIndex()) { val m = ed.pts.size / 4 * 2; val t = tileOf(ed.pts[m], ed.pts[m + 1], map); t.edges.add(ei); t.grow(ed.pts, ed.w / 2 + SW + 3f) }
        for ((ni, nd) in Town.nodes.withIndex()) { val t = tileOf(nd.x, nd.z, map); t.nodes.add(ni); t.grow(nd.poly, SW + 3f) }
        for ((bi, bl) in Town.blocks.withIndex()) {
            var cx = 0f; var cz = 0f; val n = bl.size / 2; for (k in 0 until n) { cx += bl[k * 2]; cz += bl[k * 2 + 1] }
            val t = tileOf(cx / n, cz / n, map); t.blocks.add(bi); t.grow(bl, 1f)
        }
        for ((li, l) in TownHouses.lots.withIndex()) {
            val t = tileOf(l.cx, l.cz, map); t.lots.add(li)
            t.grow(floatArrayOf(l.wx(-l.w / 2, -SW - 1f), l.wz(-l.w / 2, -SW - 1f), l.wx(l.w / 2, l.d), l.wz(l.w / 2, l.d), l.wx(-l.w / 2, l.d), l.wz(-l.w / 2, l.d), l.wx(l.w / 2, -SW - 1f), l.wz(l.w / 2, -SW - 1f)), 4f)
        }
        tiles.addAll(map.values)
        // Etapa 151: o que é preguiçoso e compartilhado é calculado antes (as threads só leem)
        for (u in Town.urban) u.padY()
        TownPark.isPark(0)
        // Etapa 151: cada pedaço (e cada quadra do centro) é gerado numa thread auxiliar; o índice do pedaço é fixo
        val base = out.size; val nT = tiles.size; val nU = Town.urban.size
        val jobs = ArrayList<java.util.concurrent.Future<City.Chunk>>(nT + nU)
        for ((ti, t) in tiles.withIndex()) jobs.add(City.workers.submit(java.util.concurrent.Callable {
            City.alive()
            val g = CityGeo.Gen(base + ti, City.Rng(ti * 13 + 1), t.x0, t.z0, t.x1, t.z1, true)
            g.b.countOnly = true   // aqui só interessa a versão de longe (a de perto é gerada quando o jogador chega)
            tile(g, ti, true)
            val far = if (g.f.isEmpty()) null else g.f.toMesh(true)
            City.Chunk(null, far, t.x0, t.z0, t.x1, t.z1, 30f).also { it.lazyI = ti; it.lazyJ = -1 }
        }))
        // quadras do centro e do comércio: prédios e lojas (com interior) do gerador de quarteirões
        for ((ui, u) in Town.urban.withIndex()) jobs.add(City.workers.submit(java.util.concurrent.Callable {
            City.alive()
            val g = CityGeo.Gen(base + nT + ui, City.Rng(u.i * 131 + u.j * 17 + 7 + ui * 3), u.x0, u.z0, u.x1, u.z1, true)
            g.b.countOnly = true   // conta os vértices (faixas dos prédios), sem gravar a malha de perto
            val h = buildUrban(g, u, ui)
            val far = if (g.f.isEmpty()) null else g.f.toMesh(true)
            City.Chunk(null, far, u.x0, u.z0, u.x1, u.z1, h).also { it.lazyI = ui; it.lazyJ = -2 }
        }))
        try {
            for ((k, f) in jobs.withIndex()) {
                City.step(0.34f + 0.52f * k / jobs.size)
                try { out.add(f.get()) } catch (e: java.util.concurrent.ExecutionException) { throw e.cause ?: e }
            }
        } catch (e: Throwable) { for (f in jobs) f.cancel(false); throw e }
        Elevado.chunks(out)   // Etapa 145: elevados e alças
        out.add(outside(out.size))
    }

    /** Detalhe de uma quadra do centro/comércio (gerada de novo igual, sem registrar colisões). */
    fun urbanNear(ci: Int, ui: Int): Pair<Mesh, Flora.Batch> {
        val u = Town.urban[ui]
        val g = CityGeo.Gen(ci, City.Rng(u.i * 131 + u.j * 17 + 7 + ui * 3), u.x0, u.z0, u.x1, u.z1, false)
        buildUrban(g, u, ui)
        return Pair(g.b.toMesh(true), g.fl)
    }

    private fun buildUrban(g: CityGeo.Gen, u: Town.Urban, ui: Int): Float {
        val pad = if (u.type == "small") u.padY() else Float.NaN
        if (!pad.isNaN()) { g.b.beginFixed(pad); g.f.beginFixed(pad); g.fl.fixedY = pad }
        val h = if (u.type == "small") TownSmall.build(g, u, ui) else if (u.type == "perim") TownBlock.build(g, u, ui) else if (u.type.startsWith("job:")) TownJobs.build(g, u, ui) else CityGeo.block(g, u.type, u.i, u.j)
        if (!pad.isNaN()) {
            g.b.endFixed(); g.f.endFixed(); g.fl.fixedY = Float.NaN
            // Etapa 150: muro de arrimo em volta (do chão de fora até o platô)
            for (mb in arrayOf(g.b, g.f)) {
                mb.beginFixed(0f); mb.m(Mt.STONE, 0.5f)
                retain(mb, u.x0, u.z0, u.x1, u.z0, 0f, -1f, pad + CURB); retain(mb, u.x1, u.z0, u.x1, u.z1, 1f, 0f, pad + CURB)
                retain(mb, u.x1, u.z1, u.x0, u.z1, 0f, 1f, pad + CURB); retain(mb, u.x0, u.z1, u.x0, u.z0, -1f, 0f, pad + CURB)
                mb.endFixed()
            }
        }
        return h
    }

    /**
     * Etapa 150: muro de arrimo ao longo da borda a→b de um platô de altura [top] (já com a guia), com o lado de fora em (ox, oz):
     * de 35 cm abaixo do chão mais baixo até o chão mais alto (o de dentro ou o de fora), amostrado a cada ~1 m. [skip](t) pula trechos.
     */
    fun retain(b: MB, ax: Float, az: Float, bx: Float, bz: Float, ox: Float, oz: Float, top: Float, skip: (Float) -> Boolean = { false }) {
        val L = hypot(bx - ax, bz - az); if (L < 0.05f) return
        val n = max(1, Math.ceil(L.toDouble()).toInt())
        val col = C("#D2CBBD"); val cap = C("#E6E0D4")   // Etapa 152: arrimo claro (antes parecia uma faixa preta)
        var px = 0f; var pz = 0f; var pt = 0f; var pb = 0f; var pok = false
        for (i in 0..n) {
            val t = i / n.toFloat(); val x = ax + (bx - ax) * t; val z = az + (bz - az) * t
            val o = Town.groundH(x + ox * 0.35f, z + oz * 0.35f)
            val hi = max(top, o); val lo = min(top, o) - 0.35f
            val ok = abs(top - o) > 0.04f && !skip(t)
            if (i > 0 && (ok || pok) && !skip(t - 0.5f / n)) {
                for (sg in floatArrayOf(1f, -1f)) {
                    val nx = ox * sg; val nz = oz * sg; val dx = if (sg < 0f) -ox * 0.015f else 0f; val dz = if (sg < 0f) -oz * 0.015f else 0f
                    val ax2 = px + dx; val az2 = pz + dz; val bx2 = x + dx; val bz2 = z + dz
                    b.v(ax2, pb, az2, nx, 0f, nz, col, px + pz, pb); b.v(bx2, lo, bz2, nx, 0f, nz, col, x + z, lo); b.v(bx2, hi, bz2, nx, 0f, nz, col, x + z, hi)
                    b.v(ax2, pb, az2, nx, 0f, nz, col, px + pz, pb); b.v(bx2, hi, bz2, nx, 0f, nz, col, x + z, hi); b.v(ax2, pt, az2, nx, 0f, nz, col, px + pz, pt)
                }
                // coroamento por cima, onde o desnível passa de 30 cm
                if (max(pt, hi) - max(pb, lo) > 0.65f) {
                    val y = max(pt, hi) + 0.025f; val w = 0.13f
                    b.v(px - ox * w, y, pz - oz * w, 0f, 1f, 0f, cap, px, pz); b.v(x + ox * w, y, z + oz * w, 0f, 1f, 0f, cap, x, z); b.v(x - ox * w, y, z - oz * w, 0f, 1f, 0f, cap, x, z)
                    b.v(px - ox * w, y, pz - oz * w, 0f, 1f, 0f, cap, px, pz); b.v(px + ox * w, y, pz + oz * w, 0f, 1f, 0f, cap, px, pz); b.v(x + ox * w, y, z + oz * w, 0f, 1f, 0f, cap, x, z)
                    for (q in 0..1) { val sx = if (q == 0) -1f else 1f   // laterais do coroamento (5 cm)
                        b.v(px + sx * ox * w, y, pz + sx * oz * w, sx * ox, 0f, sx * oz, cap, px, y); b.v(x + sx * ox * w, y - 0.05f, z + sx * oz * w, sx * ox, 0f, sx * oz, cap, x, y - 0.05f); b.v(x + sx * ox * w, y, z + sx * oz * w, sx * ox, 0f, sx * oz, cap, x, y)
                        b.v(px + sx * ox * w, y, pz + sx * oz * w, sx * ox, 0f, sx * oz, cap, px, y); b.v(px + sx * ox * w, y - 0.05f, pz + sx * oz * w, sx * ox, 0f, sx * oz, cap, px, y - 0.05f); b.v(x + sx * ox * w, y - 0.05f, z + sx * oz * w, sx * ox, 0f, sx * oz, cap, x, y - 0.05f) }
                }
            }
            px = x; pz = z; pt = hi; pb = lo; pok = ok
        }
    }

    /** Etapa 148: muro de arrimo em volta de um platô (de 3 m abaixo até a borda do gramado) — some no lado alto, aparece no baixo. */
    fun skirt(b: MB, c: FloatArray) {
        b.m(Mt.STONE, 0.5f)
        val col = C("#A8A196")
        for (i in 0 until 4) {
            val j = (i + 1) % 4
            val ax = c[i * 2]; val az = c[i * 2 + 1]; val bx = c[j * 2]; val bz = c[j * 2 + 1]
            val dx = bx - ax; val dz = bz - az; val l = max(1e-4f, hypot(dx, dz)); val nx = dz / l; val nz = -dx / l
            for (sg in floatArrayOf(1f, -1f)) {
                b.v(ax, -3f, az, nx * sg, 0f, nz * sg, col, ax + az, -3f); b.v(bx, -3f, bz, nx * sg, 0f, nz * sg, col, bx + bz, -3f); b.v(bx, 0.01f, bz, nx * sg, 0f, nz * sg, col, bx + bz, 0.01f)
                b.v(ax, -3f, az, nx * sg, 0f, nz * sg, col, ax + az, -3f); b.v(bx, 0.01f, bz, nx * sg, 0f, nz * sg, col, bx + bz, 0.01f); b.v(ax, 0.01f, az, nx * sg, 0f, nz * sg, col, ax + az, 0.01f)
            }
        }
    }

    /** Gera o pedaço [ti] (perto em g.b, longe em g.f se [far]). */
    fun tile(g: CityGeo.Gen, ti: Int, far: Boolean) {
        val t = tiles[ti]
        for (ei in t.edges) edge(g, ei, Town.edges[ei])
        for (ni in t.nodes) node(g, ni, Town.nodes[ni])
        val lot = floatArrayOf(City.lotX0, City.lotZ0, City.lotX1, City.lotZ0, City.lotX1, City.lotZ1, City.lotX0, City.lotZ1)
        for (bi in t.blocks) {
            val bl = Town.blocks[bi]
            val us = Town.urban.filter { it.block == bi }
            val u = us.firstOrNull { !it.infill }
            val holes = ArrayList<FloatArray>()
            if (bi == Town.homeBlock) holes.add(lot)
            for (q in us) holes.add(floatArrayOf(q.x0, q.z0, q.x1, q.z0, q.x1, q.z1, q.x0, q.z1))
            val tr = Town.triangulate(bl, holes)
            val mat = if (u != null) Mt.PAVER else Mt.GRASS; val col = if (u != null) WALK else GRASS; val sc = if (u != null) 0.9f else 0.3f
            g.b.m(mat, sc); tris(g.b, tr, CURB, col)
            if (far) { g.f.m(mat, sc); tris(g.f, tr, CURB, col) }
            if (bi == Town.homeBlock) {
                val ring = floatArrayOf(City.lotX0, City.lotZ0, City.lotX1, City.lotZ0, City.lotX1, City.lotZ1, City.lotX0, City.lotZ1, City.lotX0, City.lotZ0)
                g.b.m(Mt.STONE, 1f); curbWall(g.b, ring, 0f, CURB, true, CURBC)
            }
        }
        for (bi in t.blocks) if (TownPark.isPark(bi)) TownPark.draw(g, bi, !far, far)
        for (li in t.lots) {
            val l = TownHouses.lots[li]
            if (!l.pad.isNaN()) { g.b.beginFixed(l.pad); if (far) g.f.beginFixed(l.pad); g.fl.fixedY = l.pad }
            TownHouses.draw(g, l, !far, far)
            if (!l.pad.isNaN()) {
                g.b.endFixed(); if (far) g.f.endFixed(); g.fl.fixedY = Float.NaN
                TownHouses.walls(g, l, far)
            }
        }
        if (!far) return
        val f = g.f
        for (ei in t.edges) {
            val ed = Town.edges[ei]
            val hw = ed.w / 2
            f.m(Mt.ASPHALT, 0.25f); ribbon(f, Town.offset(ed.pts, -hw), Town.offset(ed.pts, hw), 0f, ASPH)
            f.m(Mt.PAVER, 0.9f)
            ribbon(f, Town.offset(ed.pts, -hw - SW), Town.offset(ed.pts, -hw), CURB, WALK)
            ribbon(f, Town.offset(ed.pts, hw), Town.offset(ed.pts, hw + SW), CURB, WALK)
        }
        for (ni in t.nodes) { val nd = Town.nodes[ni]; f.m(Mt.ASPHALT, 0.25f); fan(f, nd.x, nd.z, nd.poly, 0f, ASPH); f.m(Mt.PAVER, 0.9f); for ((_, c) in nd.corners) ribbon(f, Town.outward(c, SW), c, CURB, WALK) }
    }

    private fun edge(g: CityGeo.Gen, ei: Int, ed: Town.Edge) {
        val b = g.b; val p = ed.pts; val n = p.size / 2; val hw = ed.w / 2
        // asfalto
        b.m(Mt.ASPHALT, 0.25f); ribbon(b, Town.offset(p, -hw), Town.offset(p, hw), 0f, ASPH)
        // calçadas (dos dois lados) e guias
        for (sd in intArrayOf(-1, 1)) {
            val inner = Town.offset(p, sd * hw); val outer = Town.offset(p, sd * (hw + SW))
            b.m(Mt.PAVER, 0.9f)
            if (sd > 0) ribbon(b, inner, outer, CURB, WALK) else ribbon(b, outer, inner, CURB, WALK)
            b.m(Mt.STONE, 1f)
            // guia: faixa de pedra de 20 cm junto do asfalto, um pouco mais alta
            val g2 = Town.offset(p, sd * (hw + 0.2f))
            if (sd > 0) ribbon(b, inner, g2, CURB + 0.012f, CURBC) else ribbon(b, g2, inner, CURB + 0.012f, CURBC)
            curbWall(b, inner, 0f, CURB + 0.012f, sd < 0, CURBC)
        }
        // canteiro central das avenidas
        val a0 = 1; val a1 = n - 2
        if (ed.avenue && a1 - a0 >= 2) {
          // Etapa 152: canteiro em trechos — some na entrada das alças do elevado (pista livre) e vira piso de concreto debaixo do tabuleiro
          val zt = IntArray(n) { Elevado.zone(p[it * 2], p[it * 2 + 1]) }
          var rs = a0
          while (rs <= a1) {
            val ty = zt[rs]; var re = rs
            while (re < a1 && zt[re + 1] == ty) re++
            val nextStart = re + 1
            if (ty != 1 && re > rs) {
            val mid = p.copyOfRange(rs * 2, re * 2 + 2)
            val r = Town.offset(mid, -1.5f); val l = Town.offset(mid, 1.5f)
            val gm = if (ty == 2) Mt.PAVER else Mt.GRASS; val gc = if (ty == 2) C("#CFCAC0") else GRASS; val gs = if (ty == 2) 0.6f else 0.3f
            b.m(gm, gs); ribbon(b, r, l, CURB + 0.04f, gc)
            b.m(Mt.STONE, 1f)
            curbWall(b, r, 0f, CURB + 0.04f, false, CURBC); curbWall(b, l, 0f, CURB + 0.04f, true, CURBC)
            // pontas arredondadas (meio círculo) do canteiro
            for (end in 0..1) {
                val i = if (end == 0) 0 else mid.size / 2 - 1
                val t = Town.tangent(mid, i); val dir = if (end == 0) -1f else 1f
                val cx = mid[i * 2]; val cz = mid[i * 2 + 1]
                val cap = ArrayList<Float>()
                val base = atan2(t[1] * dir, t[0] * dir)
                for (k in 0..8) { val a = base - PI.toFloat() / 2 + PI.toFloat() * k / 8; cap.add(cx + cos(a) * 1.5f); cap.add(cz + sin(a) * 1.5f) }
                val cp = cap.toFloatArray()
                b.m(gm, gs); fan(b, cx, cz, cp, CURB + 0.04f, gc)
                b.m(Mt.STONE, 1f); curbWall(b, cp, 0f, CURB + 0.04f, false, CURBC)
            }
            }
            rs = nextStart
          }
            // árvores no canteiro
            var s = 10f
            while (s < ed.len - 10f) { val i = (s / ed.len * (n - 1)).toInt().coerceIn(a0 + 1, a1 - 1); if (Elevado.zone(p[i * 2], p[i * 2 + 1]) == 0 && !Elevado.covers(p[i * 2], p[i * 2 + 1])) CityGeo.tree(g, p[i * 2], p[i * 2 + 1], 0.8f, CURB + 0.04f, 4); s += 18f }
        }
        // sinalização horizontal
        b.m(Mt.PLAIN)
        val y = 0.02f
        // as linhas param antes da faixa de pedestre
        fun trimAt(nd: Town.Node) = if (nd.edges.size >= 3 && nd.round <= 0f) 3 else 1
        val i0 = trimAt(Town.nodes[ed.a]); val i1 = n - 1 - trimAt(Town.nodes[ed.b])
        if (i1 > i0) {
            val seg = p.copyOfRange(i0 * 2, i1 * 2 + 2)
            if (ed.avenue) {
                for (sd in floatArrayOf(-5f, 5f)) dashes(b, Town.offset(seg, sd), 3f, 3f, 0.12f, y, WHT)
            } else if (ed.w >= 13f) {
                for (sd in floatArrayOf(-0.13f, 0.13f)) line(b, Town.offset(seg, sd), 0.1f, y, YEL)
            }
            for (sd in floatArrayOf(-1f, 1f)) line(b, Town.offset(seg, sd * (hw - 0.45f)), 0.12f, y, WHT)
        }
        // faixas de pedestre nas pontas que dão em cruzamento
        for (end in 0..1) {
            val nd = Town.nodes[if (end == 0) ed.a else ed.b]
            if (nd.edges.size < 3 || nd.round > 0f) continue
            val i = if (end == 0) 0 else n - 1
            val t = Town.tangent(p, i); val dir = if (end == 0) 1f else -1f
            val fx = t[0] * dir; val fz = t[1] * dir
            val cx = p[i * 2] + fx * 2.6f; val cz = p[i * 2 + 1] + fz * 2.6f
            var o = -hw + 0.9f
            while (o <= hw - 0.9f) { mark(b, cx - fz * o, cz + fx * o, fx, fz, 3.2f, 0.5f, y, WHT); o += 1.0f }
            // linha de parada na faixa que chega ao cruzamento (lado direito de quem chega)
            val sx = cx + fx * 2.2f; val sz = cz + fz * 2.2f
            val half = if (ed.avenue) (hw - 1.5f) / 2 else hw / 2
            val c0 = if (ed.avenue) 1.5f + half else half
            mark(b, sx + fz * c0, sz - fx * c0, -fz, fx, half * 2 - 0.4f, 0.35f, y, WHT)
        }
        // postes e árvores nas calçadas
        val rng = City.Rng(ei * 97 + 5)
        fun at(sv: Float, side: Float, off: Float): FloatArray {
            val i = (sv / ed.len * (n - 1)).toInt().coerceIn(0, n - 1); val t = Town.tangent(p, i)
            val nx = -t[1] * side; val nz = t[0] * side
            return floatArrayOf(p[i * 2] + nx * off, p[i * 2 + 1] + nz * off, nx, nz, t[0], t[1])
        }
        var s = 9f; var k = 0
        while (s < ed.len - 9f) {
            val sd = if (k % 2 == 0) 1f else -1f
            val q = at(s, sd, hw + 0.55f)
            lamp(b, q[0], q[1], -q[2], -q[3])
            g.solid(q[0] - 0.15f, q[1] - 0.15f, q[0] + 0.15f, q[1] + 0.15f)
            s += 26f; k++
        }
        // Etapa 149: cada rua com a sua espécie de árvore (Etapa 150: só árvores verdes — copa redonda, copa clara ou copa alta), dos dois lados
        val res = ed.kind == TownPlan.SUB || ed.kind == TownPlan.HOME || ed.kind == TownPlan.MAN || ed.kind == TownPlan.PARK
        val species = intArrayOf(0, 1, 4, 0, 1, 4, 0, 1)[Math.floorMod(ed.name.hashCode(), 8)]
        if (ed.len > 16f) {
            var st = 6f; var q = 0
            val step = if (ed.avenue) 15f else if (res) 13f else 13f
            while (st < ed.len - 6f) {
                val near = ((st - 9f) % 26f + 26f) % 26f
                val stop = ed.avenue && ed.len > 50f && (abs(st - ed.len * 0.35f) < 4f || abs(st - ed.len * 0.65f) < 4f)
                if (near > 2.2f && near < 23.8f && !stop) {
                    val sd = if (q % 2 == 0) -1f else 1f
                    val pt = at(st, sd, hw + 1.05f)
                    if (!res) { b.m(Mt.METAL, 1f); b.box(pt[0], CURB + 0.005f, pt[1], 1.3f, 0.02f, 1.3f, C("#3A3A3A")); b.m(Mt.PLAIN); b.box(pt[0], CURB + 0.012f, pt[1], 1.1f, 0.02f, 1.1f, C("#5A4632")) }
                    CityGeo.tree(g, pt[0], pt[1], if (ed.avenue) rng.r(0.85f, 1.05f) else if (res) rng.r(0.72f, 0.92f) else rng.r(0.62f, 0.75f), CURB, if (res || ed.avenue) species else (if (rng.chance(0.5f)) 0 else 4))
                    g.solid(pt[0] - 0.25f, pt[1] - 0.25f, pt[0] + 0.25f, pt[1] + 0.25f)
                }
                st += step; q++
            }
        }
        // mobiliário urbano: hidrantes nos bairros; bancos, lixeiras e ponto de ônibus no centro/comércio
        if (res) {
            var st = 20f
            while (st < ed.len - 8f) { val pt = at(st, 1f, hw + 0.45f); b.m(Mt.METAL, 1f); b.cyl(pt[0], CURB, pt[1], 0.13f, 0.11f, 0.55f, C("#C62828"), true, 8); b.cyl(pt[0], CURB + 0.55f, pt[1], 0.09f, 0.04f, 0.12f, C("#C62828"), true, 8); g.solid(pt[0] - 0.15f, pt[1] - 0.15f, pt[0] + 0.15f, pt[1] + 0.15f); st += 52f }
        } else if (ed.len > 30f) {
            var st = 15f; var q = 0
            while (st < ed.len - 12f) {
                val sd = if (q % 2 == 0) 1f else -1f
                val pt = at(st, sd, hw + 2.6f)
                val fx = -pt[2]; val fz = -pt[3]   // de frente para a rua
                val ax = pt[4]; val az = pt[5]
                b.m(Mt.WOOD, 0.6f)
                for (o in floatArrayOf(-0.15f, 0f, 0.15f)) b.box(pt[0] - fx * o, CURB + 0.45f, pt[1] - fz * o, abs(ax) * 1.7f + abs(fx) * 0.12f, 0.05f, abs(az) * 1.7f + abs(fz) * 0.12f, C("#8D6E63"))
                b.box(pt[0] - fx * 0.28f, CURB + 0.75f, pt[1] - fz * 0.28f, abs(ax) * 1.7f + abs(fx) * 0.05f, 0.4f, abs(az) * 1.7f + abs(fz) * 0.05f, C("#8D6E63"))
                b.m(Mt.METAL, 1f); for (o in floatArrayOf(-0.75f, 0.75f)) b.box(pt[0] + ax * o, CURB + 0.225f, pt[1] + az * o, 0.06f, 0.45f, 0.06f, C("#37474F"))
                g.solid(pt[0] - 0.9f, pt[1] - 0.9f, pt[0] + 0.9f, pt[1] + 0.9f)
                val bn = at(st + 4f, sd, hw + 0.5f); b.cyl(bn[0], CURB, bn[1], 0.25f, 0.27f, 0.85f, C("#2E7D32"), true, 10); g.solid(bn[0] - 0.3f, bn[1] - 0.3f, bn[0] + 0.3f, bn[1] + 0.3f)
                st += 38f; q++
            }
        }
        if (ed.avenue && ed.len > 50f) for (sd in floatArrayOf(-1f, 1f)) {
            // ponto de ônibus com abrigo de vidro, banco, placa e mapa
            val pt = at(ed.len * (if (sd > 0) 0.35f else 0.65f), sd, hw + 2.1f)
            val fx = -pt[2]; val fz = -pt[3]; val ax = pt[4]; val az = pt[5]
            val cx = pt[0]; val cz = pt[1]
            b.m(Mt.METAL, 1f)
            for (o in floatArrayOf(-1.6f, 1.6f)) b.box(cx + ax * o - fx * 0.6f, CURB + 1.25f, cz + az * o - fz * 0.6f, 0.08f, 2.5f, 0.08f, C("#455A64"))
            b.box(cx - fx * 0.3f, CURB + 2.5f, cz - fz * 0.3f, abs(ax) * 3.6f + abs(fx) * 1.6f, 0.1f, abs(az) * 3.6f + abs(fz) * 1.6f, C("#455A64"))
            b.m(Mt.GLASS); b.box(cx - fx * 0.65f, CURB + 1.35f, cz - fz * 0.65f, abs(ax) * 3.2f + abs(fx) * 0.03f, 2.1f, abs(az) * 3.2f + abs(fz) * 0.03f, C("#CFE8F2"))
            b.m(Mt.WOOD, 0.6f); b.box(cx - fx * 0.35f, CURB + 0.45f, cz - fz * 0.35f, abs(ax) * 2.6f + abs(fx) * 0.4f, 0.06f, abs(az) * 2.6f + abs(fz) * 0.4f, C("#8D6E63"))
            b.m(Mt.PLAIN); b.box(cx + ax * 1.55f - fx * 0.62f, CURB + 1.25f, cz + az * 1.55f - fz * 0.62f, abs(ax) * 0.05f + abs(fx) * 0.9f, 1.3f, abs(az) * 0.05f + abs(fz) * 0.9f, C("#1565C0"), false)
            b.m(Mt.METAL, 1f); b.box(cx + ax * 2.3f + fx * 0.4f, CURB + 1.3f, cz + az * 2.3f + fz * 0.4f, 0.07f, 2.6f, 0.07f, C("#9E9E9E")); b.m(Mt.PLAIN); b.box(cx + ax * 2.3f + fx * 0.4f, CURB + 2.3f, cz + az * 2.3f + fz * 0.4f, 0.5f, 0.5f, 0.05f, C("#1565C0"))
            g.solid(min(cx + ax * 1.7f, cx - ax * 1.7f) - 0.8f, min(cz + az * 1.7f, cz - az * 1.7f) - 0.8f, max(cx + ax * 1.7f, cx - ax * 1.7f) + 0.8f, max(cz + az * 1.7f, cz - az * 1.7f) + 0.8f)
        }
        // ------------------------------------------------------------ Etapa 152: rua viva
        val pr = City.Rng(ei * 311 + 9)
        // carros estacionados junto do meio-fio (ruas, não avenidas), virados no sentido da mão
        if (!ed.avenue && ed.len > 44f) {
            var st = 16f; var q = 0
            while (st < ed.len - 16f) {
                val sd = if (q % 2 == 0) 1f else -1f
                if (pr.chance(0.7f)) {
                    val pt = at(st, sd, -(hw - 1.2f)).let { floatArrayOf(it[0] + it[2] * 2f * (hw - 1.2f), it[1] + it[3] * 2f * (hw - 1.2f), it[4], it[5]) }
                    var m = Vehicles.pick(pr); var k = 0
                    while (Vehicles.halfL(m) > 2.6f && k++ < 10) m = Vehicles.pick(pr)
                    val tmp = MB(); Vehicles.geom(Vehicles.XF(tmp, 0f, 0f, 0f, 1), m, pr.i(12))
                    val dx = pt[2] * sd; val dz = pt[3] * sd
                    b.appendRot(tmp, dz, dx, pt[0], 0f, pt[1])
                    g.solid(pt[0] - 1.6f, pt[1] - 1.6f, pt[0] + 1.6f, pt[1] + 1.6f)
                }
                st += 26f; q++
            }
        }
        // tampas de bueiro no asfalto e bocas de lobo junto da guia
        run {
            var st = 21f; var q = 0
            while (st < ed.len - 12f) {
                val c = at(st, if (q % 2 == 0) 1f else -1f, -hw + min(2.6f, hw * 0.45f) + hw).let { floatArrayOf(it[0], it[1]) }
                val mc = at(st, if (q % 2 == 0) 1f else -1f, 0f)
                val mx = mc[0] + mc[2] * 2.2f; val mz = mc[1] + mc[3] * 2.2f
                b.m(Mt.METAL, 1f); b.cyl(mx, 0.004f, mz, 0.4f, 0.4f, 0.012f, C("#4A4A4C"), true, 12); b.cyl(mx, 0.006f, mz, 0.3f, 0.3f, 0.013f, C("#5C5C5F"), true, 12)
                val dr = at(st + 9f, if (q % 2 == 0) -1f else 1f, hw - 0.3f)
                b.m(Mt.PLAIN); obox(b, dr[0], 0.012f, dr[1], 1.0f, 0.02f, 0.4f, dr[4], dr[5], C("#2A2A2C"))
                c[0] += 0f
                st += 43f; q++
            }
        }
        if (ed.avenue) { /* avenida: só o que já tem (pontos de ônibus, árvores, postes de luz) */ }
        else if (res) {
            // postes de madeira com fiação (bairros): cruzeta, isoladores, transformador de vez em quando, três fios com barriga
            if (ed.len > 30f) {
                var st = 5f; var prev: FloatArray? = null; var q = 0
                while (st < ed.len - 3f) {
                    val pt = at(st, 1f, hw + 3.0f)
                    b.m(Mt.WOOD, 0.6f); b.cyl(pt[0], CURB, pt[1], 0.13f, 0.1f, 8.2f, C("#6B5442"), true, 7)
                    obox(b, pt[0], CURB + 7.6f, pt[1], 0.12f, 0.12f, 2.0f, pt[4], pt[5], C("#5E4A3A"))
                    b.m(Mt.PLAIN); for (o in floatArrayOf(-0.85f, 0f, 0.85f)) b.cyl(pt[0] + pt[2] * o, CURB + 7.66f, pt[1] + pt[3] * o, 0.05f, 0.04f, 0.16f, C("#E8E6E0"), true, 6)
                    if (q % 3 == 1) { b.m(Mt.METAL, 1f); b.cyl(pt[0] - pt[2] * 0.35f, CURB + 6.2f, pt[1] - pt[3] * 0.35f, 0.24f, 0.24f, 0.8f, C("#8A9096"), true, 10) }
                    g.solid(pt[0] - 0.15f, pt[1] - 0.15f, pt[0] + 0.15f, pt[1] + 0.15f)
                    val pv = prev
                    if (pv != null) {
                        b.m(Mt.PLAIN)
                        for (o in floatArrayOf(-0.85f, 0f, 0.85f)) {
                            val ax = pv[0] + pv[2] * o; val az = pv[1] + pv[3] * o; val bx = pt[0] + pt[2] * o; val bz = pt[1] + pt[3] * o
                            val mx = (ax + bx) / 2; val mz = (az + bz) / 2
                            for (h in 0..1) { val x0 = if (h == 0) ax else mx; val z0 = if (h == 0) az else mz; val x1 = if (h == 0) mx else bx; val z1 = if (h == 0) mz else bz
                                val l = max(0.01f, hypot(x1 - x0, z1 - z0)); val ya = CURB + 7.8f - (if (h == 0) 0f else 0.4f); val yb = CURB + 7.8f - (if (h == 0) 0.4f else 0f)
                                val wx = -(z1 - z0) / l * 0.012f; val wz = (x1 - x0) / l * 0.012f; val wc = C("#1E1E1E")
                                for (sg in floatArrayOf(1f, -1f)) {   // fita fina (dois lados) entre os postes, com a barriga no meio
                                    b.v(x0, ya, z0, wx * 80f * sg, 0.2f, wz * 80f * sg, wc, 0f, 0f); b.v(x1, yb, z1, wx * 80f * sg, 0.2f, wz * 80f * sg, wc, 1f, 0f); b.v(x1, yb + 0.03f, z1, wx * 80f * sg, 0.2f, wz * 80f * sg, wc, 1f, 1f)
                                    b.v(x0, ya, z0, wx * 80f * sg, 0.2f, wz * 80f * sg, wc, 0f, 0f); b.v(x1, yb + 0.03f, z1, wx * 80f * sg, 0.2f, wz * 80f * sg, wc, 1f, 1f); b.v(x0, ya + 0.03f, z0, wx * 80f * sg, 0.2f, wz * 80f * sg, wc, 0f, 1f)
                                } }
                        }
                    }
                    prev = pt; st += 36f; q++
                }
            }
            // lixeiras de rodinha na beira da calçada
            var st = 12f
            while (st < ed.len - 8f) {
                if (pr.chance(0.55f)) { val sd = if (pr.chance(0.5f)) 1f else -1f; val pt = at(st, sd, hw + 0.75f)
                    b.m(Mt.PLAIN)
                    for ((k, col) in arrayOf("#2E7D32", "#1565C0").withIndex()) { if (k == 1 && !pr.chance(0.6f)) continue
                        val bx = pt[0] + pt[4] * k * 0.7f; val bz = pt[1] + pt[5] * k * 0.7f
                        b.box(bx, CURB + 0.5f, bz, 0.55f, 1.0f, 0.55f, C(col)); b.box(bx, CURB + 1.03f, bz, 0.6f, 0.06f, 0.6f, shade(C(col), -30)) }
                    g.solid(pt[0] - 0.4f, pt[1] - 0.4f, pt[0] + 0.9f, pt[1] + 0.9f) }
                st += 27f
            }
        } else if (ed.len > 30f) {
            // centro/comércio: floreiras de pedra com arbusto, totens de anúncio, paraciclos e parquímetros
            var st = 24f; var q = 0
            while (st < ed.len - 14f) {
                val sd = if (q % 2 == 0) -1f else 1f
                val pt = at(st, sd, hw + 2.7f)
                when (q % 4) {
                    0, 2 -> { b.m(Mt.STONE, 0.6f); obox(b, pt[0], CURB + 0.3f, pt[1], 1.8f, 0.6f, 0.8f, pt[4], pt[5], C("#B8B2A6")); b.m(Mt.PLAIN); obox(b, pt[0], CURB + 0.6f, pt[1], 1.6f, 0.04f, 0.6f, pt[4], pt[5], C("#4A3A2A"))
                        CityGeo.bush(g, pt[0] - pt[4] * 0.4f, pt[1] - pt[5] * 0.4f, 0.5f, CURB + 0.55f); CityGeo.bush(g, pt[0] + pt[4] * 0.4f, pt[1] + pt[5] * 0.4f, 0.45f, CURB + 0.55f)
                        g.solid(pt[0] - 0.9f, pt[1] - 0.9f, pt[0] + 0.9f, pt[1] + 0.9f) }
                    1 -> { val t = at(st, sd, hw + 0.9f); b.m(Mt.METAL, 1f); obox(b, t[0], CURB + 0.2f, t[1], 0.9f, 0.4f, 0.14f, t[4], t[5], C("#3B3F44")); obox(b, t[0], CURB + 1.45f, t[1], 1.25f, 2.1f, 0.16f, t[4], t[5], C("#2B2E31"))
                        b.m(Mt.PLAIN); val ad = C(arrayOf("#E53935", "#1E88E5", "#FDD835", "#43A047", "#8E24AA", "#FB8C00", "#00ACC1")[pr.i(7)])
                        for (f2 in floatArrayOf(-0.09f, 0.09f)) { obox(b, t[0] + t[2] * f2, CURB + 1.5f, t[1] + t[3] * f2, 1.1f, 1.8f, 0.01f, t[4], t[5], ad); obox(b, t[0] + t[2] * f2 * 1.1f, CURB + 1.95f, t[1] + t[3] * f2 * 1.1f, 0.8f, 0.5f, 0.01f, t[4], t[5], C("#FFFFFF")); obox(b, t[0] + t[2] * f2 * 1.1f, CURB + 1.1f, t[1] + t[3] * f2 * 1.1f, 0.9f, 0.12f, 0.01f, t[4], t[5], shade(ad, -50)) }
                        g.solid(t[0] - 0.6f, t[1] - 0.6f, t[0] + 0.6f, t[1] + 0.6f) }
                    else -> { val t = at(st, sd, hw + 0.8f); b.m(Mt.METAL, 1f)   // paraciclo com bicicletas
                        for (k in 0..3) { val bx = t[0] + t[4] * (k - 1.5f) * 0.75f; val bz = t[1] + t[5] * (k - 1.5f) * 0.75f
                            for (o in floatArrayOf(-0.3f, 0.3f)) b.cyl(bx + t[2] * o, CURB, bz + t[3] * o, 0.025f, 0.025f, 0.8f, C("#B0B6BC"), true, 5)
                            obox(b, bx, CURB + 0.8f, bz, 0.05f, 0.05f, 0.65f, t[4], t[5], C("#B0B6BC"))
                            if (k % 2 == 0) { val bc = C(arrayOf("#C62828", "#1565C0", "#2E7D32", "#212121", "#F9A825")[pr.i(5)]); val ox = bx + t[4] * 0.2f; val oz = bz + t[5] * 0.2f
                                for (o in floatArrayOf(-0.5f, 0.5f)) { b.m(Mt.PLAIN); obox(b, ox + t[2] * o, CURB + 0.33f, oz + t[3] * o, 0.04f, 0.66f, 0.66f, t[4], t[5], C("#1C1C1C")); b.m(Mt.METAL, 1f) }
                                obox(b, ox, CURB + 0.62f, oz, 0.04f, 0.05f, 1.0f, t[4], t[5], bc); obox(b, ox - t[2] * 0.3f, CURB + 0.85f, oz - t[3] * 0.3f, 0.12f, 0.05f, 0.24f, t[4], t[5], C("#222222")); obox(b, ox + t[2] * 0.45f, CURB + 0.95f, oz + t[3] * 0.45f, 0.45f, 0.04f, 0.04f, t[4], t[5], C("#333333")) } }
                        g.solid(t[0] - 1.5f, t[1] - 1.5f, t[0] + 1.5f, t[1] + 1.5f) }
                }
                // parquímetro perto de cada conjunto
                val pm = at(st + 6f, sd, hw + 0.45f); b.m(Mt.METAL, 1f); b.cyl(pm[0], CURB, pm[1], 0.035f, 0.035f, 1.1f, C("#6E747A"), true, 5); b.box(pm[0], CURB + 1.22f, pm[1], 0.16f, 0.26f, 0.12f, C("#37474F"))
                st += 22f; q++
            }
        }
    }

    private fun line(b: MB, p: FloatArray, w: Float, y: Float, c: Int) = ribbon(b, Town.offset(p, -w / 2), Town.offset(p, w / 2), y, c)

    private fun dashes(b: MB, p: FloatArray, on: Float, off: Float, w: Float, y: Float, c: Int) {
        val n = p.size / 2; var acc = 0f; var draw = true; var start = 0
        for (i in 1 until n) {
            acc += hypot(p[i * 2] - p[i * 2 - 2], p[i * 2 + 1] - p[i * 2 - 1])
            if (acc >= (if (draw) on else off)) {
                if (draw && i > start) line(b, p.copyOfRange(start * 2, i * 2 + 2), w, y, c)
                draw = !draw; acc = 0f; start = i
            }
        }
    }

    /** Poste com braço virado para a rua (fx, fz). */
    private fun lamp(b: MB, x: Float, z: Float, fx: Float, fz: Float) {
        Shade.pole(x, z, 6.4f, 0.09f)
        b.m(Mt.METAL, 1f)
        b.cyl(x, CURB, z, 0.2f, 0.12f, 0.7f, C("#3B4046"), true, 8)
        b.cyl(x, CURB + 0.7f, z, 0.1f, 0.06f, 5.7f, C("#4A4F55"), true, 7)
        obox(b, x + fx * 0.75f, CURB + 6.3f, z + fz * 0.75f, 1.5f, 0.09f, 0.1f, fx, fz, C("#4A4F55"))
        obox(b, x + fx * 1.45f, CURB + 6.22f, z + fz * 1.45f, 0.7f, 0.16f, 0.32f, fx, fz, C("#3B4046"))
        b.m(Mt.PLAIN)
        obox(b, x + fx * 1.45f, CURB + 6.12f, z + fz * 1.45f, 0.6f, 0.03f, 0.26f, fx, fz, C("#FFF6D8"))
    }

    // ------------------------------------------------------------ cruzamentos

    private fun node(g: CityGeo.Gen, ni: Int, nd: Town.Node) {
        val b = g.b
        b.m(Mt.ASPHALT, 0.25f); fan(b, nd.x, nd.z, nd.poly, 0f, ASPH)
        // calçada e guia em curva nas esquinas
        for ((_, c) in nd.corners) {
            val o = Town.outward(c, SW); val gi = Town.outward(c, 0.2f)
            b.m(Mt.PAVER, 0.9f); ribbon(b, o, c, CURB, WALK)
            b.m(Mt.STONE, 1f); ribbon(b, gi, c, CURB + 0.012f, CURBC)
            curbWall(b, c, 0f, CURB + 0.012f, true, CURBC)
        }
        // Etapa 153: semáforos e placas de rua nas esquinas dos cruzamentos maiores
        if (nd.round == 0f && nd.edges.size >= 3 && nd.edges.any { Town.edges[it].w >= 16f }) {
            for ((_, c) in nd.corners) {
                val o = Town.outward(c, 0.75f); val m = (o.size / 4) * 2
                val x = o[m]; val z = o[m + 1]
                b.m(Mt.METAL, 1f)
                b.cyl(x, CURB, z, 0.14f, 0.09f, 0.5f, C("#2B2E31"), true, 8); b.cyl(x, CURB + 0.5f, z, 0.07f, 0.06f, 4.3f, C("#3B4046"), true, 7)
                b.box(x, CURB + 5.3f, z, 0.34f, 1.0f, 0.34f, C("#1E1E1E")); b.box(x, CURB + 5.85f, z, 0.44f, 0.06f, 0.44f, C("#1E1E1E"))
                b.m(Mt.PLAIN)
                for ((k, lc) in arrayOf("#E53935", "#5A4A12", "#1F4A22").withIndex()) { b.box(x, CURB + 5.62f - k * 0.31f, z, 0.37f, 0.2f, 0.2f, C(lc), false); b.box(x, CURB + 5.62f - k * 0.31f, z, 0.2f, 0.2f, 0.37f, C(lc), false) }
                // sinal de pedestre e placas verdes com o nome das ruas
                b.box(x, CURB + 3.0f, z, 0.26f, 0.42f, 0.26f, C("#1E1E1E")); b.box(x, CURB + 3.08f, z, 0.29f, 0.16f, 0.16f, C("#E53935"), false); b.box(x, CURB + 3.08f, z, 0.16f, 0.16f, 0.29f, C("#E53935"), false)
                b.box(x, CURB + 3.75f, z, 1.1f, 0.24f, 0.03f, C("#1B5E20")); b.box(x, CURB + 3.75f, z, 0.9f, 0.05f, 0.035f, C("#FFFFFF"))
                b.box(x, CURB + 4.05f, z, 0.03f, 0.24f, 1.1f, C("#1B5E20")); b.box(x, CURB + 4.05f, z, 0.035f, 0.05f, 0.9f, C("#FFFFFF"))
                Shade.pole(x, z, 5.8f, 0.09f)
                g.solid(x - 0.15f, z - 0.15f, x + 0.15f, z + 0.15f)
            }
        }
        if (nd.round > 0f) {
            // ilha da rotatória: grama, guia, faixa de paralelepípedo e uma árvore grande no meio
            val ir = nd.round - 8f
            val ring = FloatArray(41 * 2); for (k in 0..40) { val a = 2 * PI.toFloat() * k / 40; ring[k * 2] = nd.x + cos(a) * ir; ring[k * 2 + 1] = nd.z + sin(a) * ir }
            val ring2 = FloatArray(41 * 2); for (k in 0..40) { val a = 2 * PI.toFloat() * k / 40; ring2[k * 2] = nd.x + cos(a) * (ir + 1.2f); ring2[k * 2 + 1] = nd.z + sin(a) * (ir + 1.2f) }
            b.m(Mt.PAVER, 0.6f); ribbon(b, ring2, ring, 0.06f, C("#B9B1A3"))
            b.m(Mt.GRASS, 0.3f); fan(b, nd.x, nd.z, ring.copyOf(80), CURB + 0.05f, GRASS)
            b.m(Mt.STONE, 1f); curbWall(b, ring, 0f, CURB + 0.05f, false, CURBC)
            CityGeo.tree(g, nd.x, nd.z, 1.25f, CURB + 0.05f, 0)
            for (k in 0 until 6) { val a = k * PI.toFloat() / 3 + 0.3f; CityGeo.bush(g, nd.x + cos(a) * (ir - 2f), nd.z + sin(a) * (ir - 2f), 0.9f, CURB + 0.05f) }
            g.solid(nd.x - ir * 0.7f, nd.z - ir * 0.7f, nd.x + ir * 0.7f, nd.z + ir * 0.7f)
            // setas da rotatória
            b.m(Mt.PLAIN)
            for (k in 0 until 4) {
                val a = k * PI.toFloat() / 2 + PI.toFloat() / 4; val rr = ir + 5f
                mark(b, nd.x + cos(a) * rr, nd.z + sin(a) * rr, sin(a), -cos(a), 2.2f, 0.25f, 0.02f, WHT)
            }
        }
    }

    // ------------------------------------------------------------ chão dos quarteirões e de fora da cidade

    /** Campo em volta da cidade (um pouco abaixo do asfalto) e a guia na borda do contorno. */
    private fun outside(idx: Int): City.Chunk {
        val g = CityGeo.Gen(idx, City.Rng(32), Town.minX - 600f, Town.minZ - 600f, Town.maxX + 600f, Town.maxZ + 600f)
        val b = g.b
        // ao sul da Av. Beira-Mar fica a praia (areia e mar): o campo só vai até a orla
        val zb = TownPlan.ZS[TownPlan.N] + 10f + SW
        // Etapa 146: morros em volta (malha de 24 m), com mata mais escura nas encostas altas e árvores espalhadas
        val cs = 24f
        val nx = ((g.x1 - g.x0) / cs).toInt(); val nz = ((zb - g.z0) / cs).toInt()
        fun hy(x: Float, z: Float): Float { val h = Town.hill(x, z); return if (h <= 0f) -0.6f else h }
        fun col(h: Float, x: Float, z: Float): Int { val k = (h / 70f).coerceIn(0f, 1f); val v = kotlin.math.sin(x * 0.05f) * kotlin.math.cos(z * 0.043f) * 0.08f
            val r = (0xCF * (1 - k) + 0x5E * k) * (1 + v); val gg = (0xE6 * (1 - k) + 0x8A * k) * (1 + v); val bb = (0xB8 * (1 - k) + 0x4E * k) * (1 + v)
            return android.graphics.Color.rgb(r.toInt().coerceIn(0, 255), gg.toInt().coerceIn(0, 255), bb.toInt().coerceIn(0, 255)) }
        b.m(Mt.GRASS, 0.3f)
        for (i in 0 until nx) for (j in 0 until nz) {
            val xa = g.x0 + i * cs; val xb = xa + cs; val za = g.z0 + j * cs; val zc = min(zb, za + cs)
            val ya = hy(xa, za); val yb = hy(xb, za); val yc = hy(xb, zc); val yd = hy(xa, zc)
            val ux = xb - xa; val nxv = -(yb - ya) / ux; val nzv = -(yd - ya) / (zc - za); val nl = kotlin.math.sqrt(nxv * nxv + 1f + nzv * nzv)
            val c1 = col(ya, xa, za); val c2 = col(yb, xb, za); val c3 = col(yc, xb, zc); val c4 = col(yd, xa, zc)
            b.v(xa, ya, za, nxv / nl, 1f / nl, nzv / nl, c1, xa, za); b.v(xb, yb, za, nxv / nl, 1f / nl, nzv / nl, c2, xb, za); b.v(xb, yc, zc, nxv / nl, 1f / nl, nzv / nl, c3, xb, zc)
            b.v(xa, ya, za, nxv / nl, 1f / nl, nzv / nl, c1, xa, za); b.v(xb, yc, zc, nxv / nl, 1f / nl, nzv / nl, c3, xb, zc); b.v(xa, yd, zc, nxv / nl, 1f / nl, nzv / nl, c4, xa, zc)
        }
        // Etapa 154: mata leve (o pedaço dos morros fica sempre carregado: poucos triângulos por árvore, senão estoura a memória do celular)
        fun pine(x: Float, y: Float, z: Float, s: Float, gc: Int) {
            b.m(Mt.BARK, 1f); b.cyl(x, y - 0.5f, z, 0.3f * s, 0.2f * s, 3.0f * s, C("#5D4037"), true, 4)
            b.m(Mt.PLAIN); b.cyl(x, y + 2.0f * s, z, 2.7f * s, 1.0f * s, 3.0f * s, gc, true, 5); b.cyl(x, y + 4.6f * s, z, 1.8f * s, 0.1f, 3.6f * s, shade(gc, 14), true, 5)
        }
        fun round(x: Float, y: Float, z: Float, s: Float, gc: Int) {
            b.m(Mt.BARK, 1f); b.cyl(x, y - 0.5f, z, 0.35f * s, 0.25f * s, 4.2f * s, C("#6B5442"), true, 4)
            b.m(Mt.PLAIN); CityGeo.ball(b, x, y + 5.4f * s, z, 3.0f * s, gc, 2.3f * s, 5)
        }
        val PINE = arrayOf("#2E5E32", "#3B6E3A", "#27522C", "#44783F"); val LEAF = arrayOf("#3F7A35", "#4E8B3A", "#5B8A44", "#356B2E")
        val tr = City.Rng(77)
        repeat(1700) {
            val x = tr.r(g.x0, g.x1); val z = tr.r(g.z0, zb); val h = Town.hill(x, z)
            if (h < 4f) return@repeat
            val s = tr.r(0.8f, 1.5f)
            if (tr.chance(0.55f)) pine(x, h, z, s, C(PINE[tr.i(4)])) else round(x, h, z, s, C(LEAF[tr.i(4)]))
        }
        repeat(220) {
            val x = tr.r(g.x0, g.x1); val z = tr.r(g.z0, zb); val h = Town.hill(x, z)
            if (h < 1.5f) return@repeat
            val s = tr.r(0.6f, 2.2f); val rc = C(arrayOf("#8E8A84", "#9C978E", "#7C7872", "#A6A096")[tr.i(4)])
            b.m(Mt.STONE, 0.4f); CityGeo.ball(b, x, h + 0.2f * s, z, 1.1f * s, rc, 0.7f * s, 5)
            b.m(Mt.PLAIN); CityGeo.ball(b, x - 1.3f * s, h + 0.3f, z + 0.9f * s, 0.9f * s, C(if (tr.chance(0.5f)) "#4E8B3A" else "#6BA84F"), 0.6f * s, 5)
        }
        val ol = Town.outline
        // mata fechada logo depois da rua de contorno: árvores de verdade só bem na beira, o resto leve
        if (ol.isNotEmpty()) {
            fun distOut(x: Float, z: Float): Float {
                if (Town.inside(ol, x, z)) return -1f
                var d = Float.MAX_VALUE; val n = ol.size / 2
                for (i in 0 until n) { val j = (i + 1) % n; val ax = ol[i * 2]; val az = ol[i * 2 + 1]; val bx = ol[j * 2]; val bz = ol[j * 2 + 1]
                    val ux = bx - ax; val uz = bz - az; val l2 = max(1e-4f, ux * ux + uz * uz); val t = (((x - ax) * ux + (z - az) * uz) / l2).coerceIn(0f, 1f)
                    d = min(d, hypot(x - ax - ux * t, z - az - uz * t)) }
                return d
            }
            val fr = City.Rng(919)
            var placed = 0; var tries = 0; var real = 0
            while (placed < 1300 && tries < 20000) {
                tries++
                val x = fr.r(Town.minX - 160f, Town.maxX + 160f); val z = fr.r(Town.minZ - 160f, zb - 25f)
                val d = distOut(x, z); if (d < 9f || d > 150f) continue
                if (fr.r(0f, 1f) < d / 220f) continue   // mais fechada junto da cidade
                val y = hy(x, z) + 0.6f
                if (d < 30f && real < 260 && fr.chance(0.6f)) { CityGeo.tree(g, x, z, fr.r(1.0f, 1.6f), y, if (fr.chance(0.6f)) 0 else 4); real++ }
                else if (fr.chance(0.5f)) pine(x, y, z, fr.r(0.9f, 1.5f), C(PINE[fr.i(4)])) else round(x, y, z, fr.r(0.9f, 1.4f), C(LEAF[fr.i(4)]))
                placed++
            }
        }
        if (ol.isNotEmpty()) {
            val ring = FloatArray(ol.size + 2); System.arraycopy(ol, 0, ring, 0, ol.size); ring[ol.size] = ol[0]; ring[ol.size + 1] = ol[1]
            b.m(Mt.STONE, 1f); curbWall(b, ring, -0.06f, CURB, Town.polyArea(ol) < 0, CURBC)
        }
        return g.finish(100f)
    }
}
