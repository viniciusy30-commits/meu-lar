package com.vinicius.meular

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

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
        if (m <= 7f || d > 14) { b.v(ax, y, az, 0f, 1f, 0f, c, ax, az); b.v(bx, y, bz, 0f, 1f, 0f, c, bx, bz); b.v(cx, y, cz, 0f, 1f, 0f, c, cx, cz); return }
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

    const val TILE = 360f
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
        for ((ti, t) in tiles.withIndex()) {
            val g = CityGeo.Gen(out.size, City.Rng(ti * 13 + 1), t.x0, t.z0, t.x1, t.z1, true)
            tile(g, ti, true)
            val far = if (g.f.isEmpty()) null else g.f.toMesh(true)
            val c = City.Chunk(null, far, t.x0, t.z0, t.x1, t.z1, 30f)
            c.lazyI = ti; c.lazyJ = -1
            out.add(c)
        }
        // quadras do centro e do comércio: prédios e lojas (com interior) do gerador de quarteirões
        for ((ui, u) in Town.urban.withIndex()) {
            val g = CityGeo.Gen(out.size, City.Rng(u.i * 131 + u.j * 17 + 7 + ui * 3), u.x0, u.z0, u.x1, u.z1, true)
            val h = buildUrban(g, u, ui)
            val far = if (g.f.isEmpty()) null else g.f.toMesh(true)
            val c = City.Chunk(null, far, u.x0, u.z0, u.x1, u.z1, h)
            c.lazyI = ui; c.lazyJ = -2
            out.add(c)
        }
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
            val ring = floatArrayOf(u.x0, u.z0, u.x1, u.z0, u.x1, u.z1, u.x0, u.z1)
            skirt(g.b, ring); skirt(g.f, ring)
            g.b.endFixed(); g.f.endFixed(); g.fl.fixedY = Float.NaN
        }
        return h
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
                val c = TownHouses.corners(l)
                skirt(g.b, c); if (far) skirt(g.f, c)
                g.b.endFixed(); if (far) g.f.endFixed(); g.fl.fixedY = Float.NaN
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
            val mid = p.copyOfRange(a0 * 2, a1 * 2 + 2)
            val r = Town.offset(mid, -1.5f); val l = Town.offset(mid, 1.5f)
            b.m(Mt.GRASS, 0.3f); ribbon(b, r, l, CURB + 0.04f, GRASS)
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
                b.m(Mt.GRASS, 0.3f); fan(b, cx, cz, cp, CURB + 0.04f, GRASS)
                b.m(Mt.STONE, 1f); curbWall(b, cp, 0f, CURB + 0.04f, false, CURBC)
            }
            // árvores no canteiro
            var s = 10f
            while (s < ed.len - 10f) { val i = (s / ed.len * (n - 1)).toInt().coerceIn(a0 + 1, a1 - 1); if (!Elevado.covers(p[i * 2], p[i * 2 + 1])) CityGeo.tree(g, p[i * 2], p[i * 2 + 1], 0.8f, CURB + 0.04f, 4); s += 18f }
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
        var s = 9f; var k = 0
        while (s < ed.len - 9f) {
            val i = (s / ed.len * (n - 1)).toInt().coerceIn(0, n - 1)
            val t = Town.tangent(p, i)
            val sd = if (k % 2 == 0) 1f else -1f
            val nx = -t[1] * sd; val nz = t[0] * sd
            val lx = p[i * 2] + nx * (hw + 0.55f); val lz = p[i * 2 + 1] + nz * (hw + 0.55f)
            lamp(b, lx, lz, -nx, -nz)
            g.solid(lx - 0.15f, lz - 0.15f, lx + 0.15f, lz + 0.15f)
            // árvore no meio do vão entre dois postes, no lado oposto
            val s2 = s + 13f
            if (s2 < ed.len - 9f && ed.w < 22f) {
                val j = (s2 / ed.len * (n - 1)).toInt().coerceIn(0, n - 1)
                val t2 = Town.tangent(p, j)
                val tx = p[j * 2] - t2[1] * (-sd) * (hw + SW - 1.0f); val tz = p[j * 2 + 1] + t2[0] * (-sd) * (hw + SW - 1.0f)
                CityGeo.tree(g, tx, tz, rng.r(0.7f, 0.85f))
                g.solid(tx - 0.25f, tz - 0.25f, tx + 0.25f, tz + 0.25f)
            }
            s += 26f; k++
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
        // mata: copas cônicas espalhadas nos morros
        val tr = City.Rng(77)
        repeat(1400) {
            val x = tr.r(g.x0, g.x1); val z = tr.r(g.z0, zb); val h = Town.hill(x, z)
            if (h < 4f) return@repeat
            val s = tr.r(0.8f, 1.5f)
            b.m(Mt.BARK, 1f); b.cyl(x, h - 0.5f, z, 0.35f * s, 0.25f * s, 3.5f * s, C("#5D4037"), true, 5)
            b.m(Mt.PLAIN); b.cyl(x, h + 2.2f * s, z, 2.6f * s, 0.2f, 6.5f * s, C(if (tr.chance(0.5f)) "#2E5E32" else "#3B6E3A"), true, 7)
        }
        val ol = Town.outline
        if (ol.isNotEmpty()) {
            val ring = FloatArray(ol.size + 2); System.arraycopy(ol, 0, ring, 0, ol.size); ring[ol.size] = ol[0]; ring[ol.size + 1] = ol[1]
            b.m(Mt.STONE, 1f); curbWall(b, ring, -0.06f, CURB, Town.polyArea(ol) < 0, CURBC)
        }
        return g.finish(100f)
    }
}
