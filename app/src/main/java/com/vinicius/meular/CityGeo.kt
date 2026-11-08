package com.vinicius.meular

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Etapa 122: geometria da cidade — ruas, quarteirões, construções com interior mobiliado.
 * Toda construção em que se entra é gravada em dois construtores:
 *  A = sempre visível (piso, móveis, base das paredes até 0,9 m),
 *  H = escondido quando o jogador está dentro (resto das paredes, janelas, andares de cima, telhado, placas).
 */
object CityGeo {
    private val CURB = City.CURB
    private val FL = City.FLOOR
    private val SIDE = City.SIDE
    private const val STUB = 0.9f

    // ============================================================ geração de um pedaço

    class Gen(val idx: Int, val rng: City.Rng, val x0: Float, val z0: Float, val x1: Float, val z1: Float, val reg: Boolean = true) {
        val b = MB()
        val f = MB()
        val fl = Flora.Batch()
        var A: MB = b
        var H: MB = b
        private var cur: City.Bld? = null

        fun begin(ax: Float, az: Float, bx: Float, bz: Float, name: String): City.Bld {
            A = MB(); H = MB()
            val bd = City.Bld(min(ax, bx), min(az, bz), max(ax, bx), max(az, bz), idx, name)
            cur = bd
            return bd
        }

        fun end() {
            val bd = cur ?: return
            b.append(A)
            val c0 = b.counts()
            b.append(H)
            val c1 = b.counts()
            for ((m, n1) in c1) { val n0 = c0[m] ?: 0; if (n1 > n0) bd.ranges[m] = intArrayOf(n0, n1) }
            if (reg) City.addBld(bd)
            A = b; H = b; cur = null
        }

        fun solid(ax: Float, az: Float, bx: Float, bz: Float) { if (reg) City.addSolid(floatArrayOf(min(ax, bx), min(az, bz), max(ax, bx), max(az, bz))) }
        fun place(p: City.Place) { if (reg) City.addPlace(p) }

        /** Pedaço com malha detalhada já pronta (a flora é montada depois, na thread do GL). */
        fun finish(h: Float): City.Chunk {
            val nm = b.toMesh(true)
            val far = if (f.isEmpty()) null else f.toMesh(true)
            val c = City.Chunk(nm, far, x0, z0, x1, z1, h)
            c.pend = fl
            for ((i, p) in nm.parts.withIndex()) { c.nearIdx[p.mat] = i; if (p.mat == Mt.GLASS) c.glass = true }
            return c
        }

        /** Só a versão de longe; a detalhada é gerada de novo quando o jogador chega perto. */
        fun finishFar(h: Float): City.Chunk = City.Chunk(null, null, x0, z0, x1, z1, h)
    }

    // ============================================================ primitivas

    /** Quadrilátero (4 pontos x,y,z) com UV projetado. */
    fun q(b: MB, p: FloatArray, c: Int, lit: Boolean = true) {
        val ux = p[3] - p[0]; val uy = p[4] - p[1]; val uz = p[5] - p[2]
        val vx = p[9] - p[0]; val vy = p[10] - p[1]; val vz = p[11] - p[2]
        var nx = uy * vz - uz * vy; var ny = uz * vx - ux * vz; var nz = ux * vy - uy * vx
        val l = sqrt(nx * nx + ny * ny + nz * nz).coerceAtLeast(1e-6f); nx /= l; ny /= l; nz /= l
        if (!lit) { nx = 0f; ny = 0f; nz = 0f }
        val ax = abs(nx); val ay = abs(ny); val az = abs(nz)
        for (i in intArrayOf(0, 1, 2, 0, 2, 3)) {
            val x = p[i * 3]; val y = p[i * 3 + 1]; val z = p[i * 3 + 2]
            if (ay >= ax && ay >= az) b.v(x, y, z, nx, ny, nz, c, x, z)
            else if (ax >= az) b.v(x, y, z, nx, ny, nz, c, z, y)
            else b.v(x, y, z, nx, ny, nz, c, x, y)
        }
    }

    fun tri(b: MB, p: FloatArray, c: Int) {
        val ux = p[3] - p[0]; val uy = p[4] - p[1]; val uz = p[5] - p[2]
        val vx = p[6] - p[0]; val vy = p[7] - p[1]; val vz = p[8] - p[2]
        var nx = uy * vz - uz * vy; var ny = uz * vx - ux * vz; var nz = ux * vy - uy * vx
        val l = sqrt(nx * nx + ny * ny + nz * nz).coerceAtLeast(1e-6f); nx /= l; ny /= l; nz /= l
        for (i in 0..2) { val x = p[i * 3]; val y = p[i * 3 + 1]; val z = p[i * 3 + 2]; b.v(x, y, z, nx, ny, nz, c, if (abs(nx) > abs(nz)) z else x, y) }
    }

    fun P(x: Float, y: Float, z: Float) = floatArrayOf(x, y, z)

    /** Etapa 122: esfera leve (a do MB tem seg × 2seg faixas — quase 1000 vértices; esta, ~150). */
    fun ball(b: MB, cx: Number, cy: Number, cz: Number, r: Number, c: Int, ry: Number = r, seg: Int = 8, lit: Boolean = true) {
        val x = cx.toFloat(); val y = cy.toFloat(); val z = cz.toFloat(); val rr = r.toFloat(); val rv = ry.toFloat()
        val lon = max(5, min(seg, 10)); val lat = max(3, lon / 2)
        val l = if (lit) 1f else 0f
        val pi = PI.toFloat()
        for (i in 0 until lat) {
            val t0 = pi * i / lat; val t1 = pi * (i + 1) / lat
            for (j in 0 until lon) {
                val p0 = 2f * pi * j / lon; val p1 = 2f * pi * (j + 1) / lon
                fun pt(t: Float, p: Float) {
                    val nx = sin(t) * cos(p); val ny = cos(t); val nz = sin(t) * sin(p)
                    b.v(x + rr * nx, y + rv * ny, z + rr * nz, nx * l, ny * l, nz * l, c, p * rr, t * rv)
                }
                if (i > 0) { pt(t0, p0); pt(t1, p0); pt(t0, p1) }
                if (i < lat - 1) { pt(t0, p1); pt(t1, p0); pt(t1, p1) } else { pt(t0, p1); pt(t1, p0); pt(t1, p1) }
            }
        }
    }

    /** Referencial de uma peça: origem (ox, oz), F = frente. lx para a direita (de quem olha a frente), lz para trás. */
    class L(val ox: Float, val oz: Float, val fx: Float, val fz: Float) {
        val rx = fz; val rz = -fx
        fun wx(lx: Float, lz: Float) = ox + rx * lx - fx * lz
        fun wz(lx: Float, lz: Float) = oz + rz * lx - fz * lz
        val alongX = abs(rx) > 0.5f
    }

    fun lb(b: MB, l: L, lx: Float, y: Float, lz: Float, sx: Float, sy: Float, sz: Float, c: Int, lit: Boolean = true) {
        val cx = l.wx(lx, lz); val cz = l.wz(lx, lz)
        if (l.alongX) b.box(cx, y, cz, sx, sy, sz, c, lit) else b.box(cx, y, cz, sz, sy, sx, c, lit)
    }

    fun lcyl(b: MB, l: L, lx: Float, y: Float, lz: Float, r1: Float, r2: Float, h: Float, c: Int, seg: Int = 10) = b.cyl(l.wx(lx, lz), y, l.wz(lx, lz), r1, r2, h, c, true, seg)
    fun lsph(b: MB, l: L, lx: Float, y: Float, lz: Float, r: Float, c: Int, ry: Float = r, seg: Int = 8) = CityGeo.ball(b, l.wx(lx, lz), y, l.wz(lx, lz), r, c, ry, seg)

    /** Placa com texto [idx] virada para (fx, fz), centro (cx, cz), base y. */
    fun sign(b: MB, cx: Float, y: Float, cz: Float, fx: Float, fz: Float, w: Float, h: Float, idx: Int, frame: Boolean = true) {
        val col = idx % 4; val row = idx / 4
        val u0 = col * 0.25f + 0.0015f; val u1 = u0 + 0.247f
        val v0 = row / 16f + 0.003f; val v1 = (row + 1) / 16f - 0.003f
        val rx = fz; val rz = -fx
        if (frame) {
            b.m(Mt.METAL, 1f)
            val bx = cx - fx * 0.07f; val bz = cz - fz * 0.07f
            if (abs(rx) > 0.5f) b.box(bx, y + h / 2, bz, w + 0.14f, h + 0.14f, 0.12f, C("#2F3133")) else b.box(bx, y + h / 2, bz, 0.12f, h + 0.14f, w + 0.14f, C("#2F3133"))
        }
        b.m(Mt.SIGN, 1f)
        val ax = cx - rx * w / 2 + fx * 0.002f; val az = cz - rz * w / 2 + fz * 0.002f
        val ex = cx + rx * w / 2 + fx * 0.002f; val ez = cz + rz * w / 2 + fz * 0.002f
        val c = C("#FFFFFF")
        b.v(ax, y, az, fx, 0.15f, fz, c, u0, v1); b.v(ex, y, ez, fx, 0.15f, fz, c, u1, v1); b.v(ex, y + h, ez, fx, 0.15f, fz, c, u1, v0)
        b.v(ax, y, az, fx, 0.15f, fz, c, u0, v1); b.v(ex, y + h, ez, fx, 0.15f, fz, c, u1, v0); b.v(ax, y + h, az, fx, 0.15f, fz, c, u0, v0)
        b.m(Mt.PLAIN)
    }

    /** Marca pintada no chão (um retângulo plano, 6 vértices em vez de 36). */
    fun flat(b: MB, cx: Float, cz: Float, sx: Float, sz: Float, c: Int) = b.plane(cx - sx / 2, cz - sz / 2, cx + sx / 2, cz + sz / 2, 0.022f, c)

    fun groundBox(b: MB, x0: Float, z0: Float, x1: Float, z1: Float, mat: Int, s: Float, c: Int, top: Float = CURB) {
        b.m(mat, s)
        b.box((x0 + x1) / 2, top / 2, (z0 + z1) / 2, x1 - x0, top, z1 - z0, c)
    }

    private val LEAF = arrayOf(C("#5E9E48"), C("#4F8F3F"), C("#6DAA4F"), C("#7FB25A"), C("#3F7F3A"), C("#8DBF5E"))

    /** Árvore de copa redonda feita de várias bolas (perto) e uma bola só (longe). */
    fun tree(g: Gen, x: Float, z: Float, s: Float, y: Float = CURB) {
        val b = g.b; val rng = g.rng
        b.m(Mt.WOOD, 1f)
        b.cyl(x, y, z, 0.15f * s, 0.1f * s, 2.3f * s, C("#6E5038"), true, 6)
        b.m(Mt.PLAIN)
        val gc = rng.pick(LEAF)
        ball(b, x, y + 3.0f * s, z, 1.45f * s, gc, 1.2f * s, 8)
        ball(b, x + 0.6f * s, y + 3.5f * s, z + 0.3f * s, 1.0f * s, shade(gc, 16), 0.8f * s, 7)
        g.f.m(Mt.PLAIN)
        g.f.cyl(x, y, z, 0.15f * s, 0.1f * s, 2.0f * s, C("#6E5038"), true, 4)
        ball(g.f, x, y + 3.0f * s, z, 1.6f * s, gc, 1.3f * s, 5)
    }

    /** Palmeira: tronco curvo em gomos e folhas compridas caídas. */
    fun palm(g: Gen, x: Float, z: Float, s: Float, y: Float = CURB) {
        val b = g.b; val rng = g.rng
        val lean = rng.r(-0.35f, 0.35f); val leanZ = rng.r(-0.35f, 0.35f)
        b.m(Mt.WOOD, 1f)
        val segs = 9; val hh = 6.5f * s
        var px = x; var pz = z
        for (k in 0 until segs) {
            val t = k.toFloat() / segs
            val nx = x + lean * hh * t * t; val nz = z + leanZ * hh * t * t
            b.cyl(nx, y + hh * t, nz, 0.2f * s * (1f - 0.35f * t), 0.18f * s * (1f - 0.35f * t), hh / segs + 0.02f, if (k % 2 == 0) C("#8A6D4E") else C("#7A5E42"), true, 7)
            px = nx; pz = nz
        }
        val tx = x + lean * hh; val tz = z + leanZ * hh; val ty = y + hh
        b.m(Mt.PLAIN)
        CityGeo.ball(b, tx, ty, tz, 0.35f * s, C("#6B5A2E"), 0.3f * s, 6)
        val nf = 9
        for (k in 0 until nf) {
            val a = k * 2f * PI.toFloat() / nf + rng.r(-0.2f, 0.2f)
            val dx = cos(a); val dz = sin(a)
            val len = rng.r(3.0f, 3.8f) * s
            val gc = if (k % 2 == 0) C("#3E8E41") else C("#4FA34A")
            var lx = tx; var ly = ty; var lz = tz
            val steps = 5
            for (st in 1..steps) {
                val t = st.toFloat() / steps
                val nx = tx + dx * len * t; val nz = tz + dz * len * t
                val ny = ty + 0.9f * s * t - 2.6f * s * t * t
                val w = 0.55f * s * sin(PI.toFloat() * min(1f, t * 1.15f)) + 0.05f
                val pxw = -dz * w; val pzw = dx * w
                val w0 = 0.55f * s * sin(PI.toFloat() * min(1f, (t - 1f / steps) * 1.15f)) + 0.05f
                val p0x = -dz * w0; val p0z = dx * w0
                q(b, P(lx - p0x, ly, lz - p0z) + P(lx + p0x, ly, lz + p0z) + P(nx + pxw, ny - 0.12f * s, nz + pzw) + P(nx - pxw, ny - 0.12f * s, nz - pzw), gc)
                lx = nx; ly = ny; lz = nz
            }
        }
        g.f.m(Mt.PLAIN)
        g.f.cyl(x, y, z, 0.2f * s, 0.14f * s, hh, C("#8A6D4E"), true, 5)
        CityGeo.ball(g.f, tx, ty - 0.4f * s, tz, 2.6f * s, C("#4A9A45"), 0.9f * s, 6)
    }

    fun bush(g: Gen, x: Float, z: Float, s: Float, y: Float = CURB) {
        g.fl.place(g.rng.pick(arrayOf("bush_a", "bush_b", "bush_pink", "bush_white")), x.toDouble(), y.toDouble(), z.toDouble(), s.toDouble(), g.rng.r(0f, 6f).toDouble())
    }

    fun flowers(g: Gen, x0: Float, z0: Float, x1: Float, z1: Float, n: Int, y: Float) {
        val fn = arrayOf("fl_daisy", "fl_lav", "fl_poppy", "fl_tulip", "fl_yellow")
        val sp = g.rng.i(5)
        for (k in 0 until n) g.fl.place(fn[(sp + k % 2) % 5], g.rng.r(x0, x1).toDouble(), y.toDouble(), g.rng.r(z0, z1).toDouble(), g.rng.r(1.1f, 1.5f).toDouble(), g.rng.r(0f, 6f).toDouble())
    }

    fun streetLamp(b: MB, x: Float, z: Float, ax: Float, az: Float, y: Float = CURB) {
        b.m(Mt.METAL, 1f)
        b.box(x, y + 0.25f, z, 0.3f, 0.5f, 0.3f, C("#3B4046"))
        b.cyl(x, y, z, 0.09f, 0.06f, 6.4f, C("#4A4F55"), true, 6)
        if (ax != 0f || az != 0f) {
            b.box(x + ax * 0.75f, y + 6.3f, z + az * 0.75f, if (ax != 0f) 1.5f else 0.1f, 0.09f, if (az != 0f) 1.5f else 0.1f, C("#4A4F55"))
            b.box(x + ax * 1.45f, y + 6.22f, z + az * 1.45f, if (ax != 0f) 0.7f else 0.32f, 0.16f, if (az != 0f) 0.7f else 0.32f, C("#3B4046"))
            b.m(Mt.PLAIN); b.box(x + ax * 1.45f, y + 6.13f, z + az * 1.45f, if (ax != 0f) 0.6f else 0.26f, 0.03f, if (az != 0f) 0.6f else 0.26f, C("#FFF6D8"), false)
        } else {
            b.m(Mt.PLAIN); CityGeo.ball(b, x, y + 6.55f, z, 0.28f, C("#FFF6D8"), 0.28f, 8, false)
        }
    }

    // ============================================================ paredes com aberturas

    class Op(val c: Float, val w: Float, val b: Float, val t: Float, val door: Boolean)

    /**
     * Parede reta de [a] a [e] ao longo do eixo [axis] (0 = x, 1 = z), na posição [fix] do outro eixo,
     * do piso [y0] até [top]. [out] = lado de fora (+1/-1 no outro eixo). Aberturas em [ops]. Base vai para A, o resto para H.
     */
    fun wall(g: Gen, axis: Int, fix: Float, a: Float, e: Float, y0: Float, top: Float, out: Int, ops: List<Op>, cOut: Int, cIn: Int, matOut: Int, th: Float = 0.2f, interior: Boolean = false) {
        val sorted = ops.sortedBy { it.c }
        // Etapa 122: um bloco só na espessura toda (cor de fora) + uma face fina por dentro (reboco) — metade dos vértices de antes
        fun seg(b: MB, u0: Float, u1: Float, v0: Float, v1: Float) {
            if (u1 - u0 < 0.005f || v1 - v0 < 0.005f) return
            if (interior) {
                b.m(Mt.PLASTER, 0.5f)
                if (axis == 0) b.box((u0 + u1) / 2, (v0 + v1) / 2, fix, u1 - u0, v1 - v0, th, cIn) else b.box(fix, (v0 + v1) / 2, (u0 + u1) / 2, th, v1 - v0, u1 - u0, cIn)
                return
            }
            b.m(matOut, if (matOut == Mt.FACADE) 1f / 3f else 0.5f)
            if (axis == 0) b.box((u0 + u1) / 2, (v0 + v1) / 2, fix, u1 - u0, v1 - v0, th, cOut) else b.box(fix, (v0 + v1) / 2, (u0 + u1) / 2, th, v1 - v0, u1 - u0, cOut)
            b.m(Mt.PLASTER, 0.5f)
            val d = fix - out * (th / 2 + 0.003f)
            if (axis == 0) {
                if (out > 0) q(b, P(u0, v0, d) + P(u0, v1, d) + P(u1, v1, d) + P(u1, v0, d), cIn) else q(b, P(u1, v0, d) + P(u1, v1, d) + P(u0, v1, d) + P(u0, v0, d), cIn)
            } else {
                if (out > 0) q(b, P(d, v0, u1) + P(d, v1, u1) + P(d, v1, u0) + P(d, v0, u0), cIn) else q(b, P(d, v0, u0) + P(d, v1, u0) + P(d, v1, u1) + P(d, v0, u1), cIn)
            }
        }
        fun piece(u0: Float, u1: Float, v0: Float, v1: Float) {
            val ys = y0 + STUB
            if (v1 <= ys) seg(g.A, u0, u1, v0, v1)
            else if (v0 >= ys) seg(g.H, u0, u1, v0, v1)
            else { seg(g.A, u0, u1, v0, ys); seg(g.H, u0, u1, ys, v1) }
        }
        var u = a
        for (o in sorted) {
            val oa = o.c - o.w / 2; val ob = o.c + o.w / 2
            piece(u, oa, y0, top)
            if (o.b > y0) piece(oa, ob, y0, o.b)
            if (o.t < top) piece(oa, ob, o.t, top)
            // moldura e vidro
            val hb = g.H
            hb.m(Mt.PLAIN)
            val fc = C("#FAFAFA")
            val fo = fix + out * (th / 2 + 0.02f)
            fun bx(u0: Float, u1: Float, v0: Float, v1: Float, dd: Float, dth: Float, c: Int, b: MB = hb) {
                if (axis == 0) b.box((u0 + u1) / 2, (v0 + v1) / 2, dd, u1 - u0, v1 - v0, dth, c) else b.box(dd, (v0 + v1) / 2, (u0 + u1) / 2, dth, v1 - v0, u1 - u0, c)
            }
            if (!interior) {
                bx(oa - 0.07f, oa, o.b, o.t + 0.07f, fo, 0.06f, fc); bx(ob, ob + 0.07f, o.b, o.t + 0.07f, fo, 0.06f, fc)
                bx(oa - 0.07f, ob + 0.07f, o.t, o.t + 0.07f, fo, 0.06f, fc)
            }
            if (!o.door) {
                bx(oa - 0.1f, ob + 0.1f, o.b - 0.06f, o.b, fix + out * (th / 2 + 0.06f), 0.16f, C("#E6E2DC"))   // peitoril
                bx(o.c - 0.025f, o.c + 0.025f, o.b, o.t, fix, 0.06f, fc)                              // caixilho do meio
                hb.m(Mt.GLASS); hb.al = 0.32f
                bx(oa, ob, o.b, o.t, fix, 0.02f, C("#BFE3F2"))
                hb.al = 1f; hb.m(Mt.PLAIN)
            }
            u = ob
        }
        piece(u, e, y0, top)
    }

    // ============================================================ móveis (sempre visíveis: g.A)

    private val WOODS = arrayOf(C("#8B5E3C"), C("#A47551"), C("#5C3D2E"), C("#C8A27A"), C("#3E2C23"), C("#D9C2A3"))
    private val FABRICS = arrayOf(C("#4A6FA5"), C("#8E9AAF"), C("#C9ADA7"), C("#5B8E7D"), C("#E9C46A"), C("#B5838D"), C("#6D597A"), C("#D8D8D8"), C("#2F3E46"), C("#A3B18A"))

    fun sofa(b: MB, l: L, w: Float, col: Int) {
        val y = FL
        b.m(Mt.FABRIC, 1f)
        lb(b, l, 0f, y + 0.22f, 0f, w, 0.3f, 0.9f, shade(col, -15))
        val n = max(2, (w / 0.8f).toInt()); val cw = (w - 0.3f) / n
        for (k in 0 until n) lb(b, l, -w / 2 + 0.15f + cw * (k + 0.5f), y + 0.44f, -0.05f, cw - 0.03f, 0.16f, 0.7f, col)
        lb(b, l, 0f, y + 0.65f, 0.36f, w, 0.6f, 0.2f, shade(col, -8))
        for (k in 0 until n) lb(b, l, -w / 2 + 0.15f + cw * (k + 0.5f), y + 0.7f, 0.22f, cw - 0.06f, 0.42f, 0.14f, col)
        for (s in floatArrayOf(-1f, 1f)) lb(b, l, s * (w / 2 - 0.08f), y + 0.42f, 0f, 0.16f, 0.36f, 0.9f, shade(col, -8))
        b.m(Mt.FABRIC, 1f)
        lb(b, l, -w / 2 + 0.45f, y + 0.62f, 0.12f, 0.36f, 0.32f, 0.1f, C("#F2E8CF"))   // almofada
        b.m(Mt.WOOD, 1f)
        for (s in floatArrayOf(-1f, 1f)) for (t in floatArrayOf(-0.35f, 0.35f)) lb(b, l, s * (w / 2 - 0.1f), y + 0.04f, t, 0.05f, 0.08f, 0.05f, C("#3E2C23"))
    }

    fun armchair(b: MB, l: L, col: Int) {
        val y = FL
        b.m(Mt.FABRIC, 1f)
        lb(b, l, 0f, y + 0.24f, 0f, 0.85f, 0.32f, 0.85f, shade(col, -12))
        lb(b, l, 0f, y + 0.45f, -0.04f, 0.58f, 0.14f, 0.66f, col)
        lb(b, l, 0f, y + 0.68f, 0.34f, 0.85f, 0.6f, 0.18f, shade(col, -6))
        for (s in floatArrayOf(-1f, 1f)) lb(b, l, s * 0.36f, y + 0.47f, 0f, 0.14f, 0.3f, 0.85f, shade(col, -6))
    }

    fun rug(b: MB, x0: Float, z0: Float, x1: Float, z1: Float, col: Int) {
        b.m(Mt.RUG, 0.5f)
        b.box((x0 + x1) / 2, FL + 0.006f, (z0 + z1) / 2, x1 - x0, 0.012f, z1 - z0, col)
    }

    fun coffeeTable(b: MB, l: L, wood: Int) {
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, FL + 0.4f, 0f, 1.1f, 0.05f, 0.6f, wood)
        lb(b, l, 0f, FL + 0.12f, 0f, 1.0f, 0.03f, 0.5f, wood)
        for (s in floatArrayOf(-0.5f, 0.5f)) for (t in floatArrayOf(-0.25f, 0.25f)) lb(b, l, s, FL + 0.2f, t, 0.05f, 0.4f, 0.05f, shade(wood, -20))
        b.m(Mt.PLAIN)
        lcyl(b, l, 0.25f, FL + 0.425f, 0f, 0.09f, 0.07f, 0.12f, C("#EDE7E3"), 10)
        lb(b, l, -0.2f, FL + 0.44f, 0.05f, 0.3f, 0.03f, 0.22f, C("#C0392B"))
    }

    fun tvUnit(b: MB, l: L, wood: Int, w: Float = 1.8f) {
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, FL + 0.25f, 0f, w, 0.5f, 0.42f, wood)
        b.m(Mt.PLAIN)
        for (k in 0 until 3) lb(b, l, -w / 3 + k * w / 3, FL + 0.25f, -0.212f, w / 3 - 0.06f, 0.4f, 0.01f, shade(wood, -14))
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.53f, 0f, 0.35f, 0.04f, 0.2f, C("#1A1A1A"))
        lb(b, l, 0f, FL + 0.58f, 0.02f, 0.06f, 0.1f, 0.05f, C("#1A1A1A"))
        lb(b, l, 0f, FL + 1.02f, 0.02f, 1.5f, 0.86f, 0.05f, C("#111111"))
        lb(b, l, 0f, FL + 1.02f, -0.006f, 1.44f, 0.8f, 0.01f, C("#1D2A3A"))
        b.m(Mt.PLAIN)
        lb(b, l, 0.45f, FL + 1.22f, -0.012f, 0.35f, 0.18f, 0.005f, C("#3B6F9E"), false)
        lb(b, l, -0.2f, FL + 0.9f, -0.012f, 0.7f, 0.25f, 0.005f, C("#2B4E6B"), false)
    }

    fun bookshelf(b: MB, l: L, wood: Int, rng: City.Rng) {
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, FL + 1.0f, 0.15f, 1.0f, 2.0f, 0.04f, shade(wood, -15))
        for (s in floatArrayOf(-0.48f, 0.48f)) lb(b, l, s, FL + 1.0f, 0f, 0.04f, 2.0f, 0.34f, wood)
        for (k in 0..4) lb(b, l, 0f, FL + 0.03f + k * 0.48f, 0f, 0.96f, 0.03f, 0.34f, wood)
        b.m(Mt.PLAIN)
        for (k in 0..3) {
            var x = -0.44f
            while (x < 0.4f) {
                val bw = rng.r(0.09f, 0.17f); val bh = rng.r(0.26f, 0.38f)
                lb(b, l, x + bw / 2, FL + 0.045f + k * 0.48f + bh / 2, 0.02f, bw, bh, 0.24f, rng.pick(arrayOf(C("#8E2C2C"), C("#2C4A8E"), C("#2E7D32"), C("#E0A030"), C("#EEEEEE"), C("#5D4037"), C("#455A64"))))
                x += bw + 0.005f
                if (rng.chance(0.08f)) x += 0.12f
            }
        }
    }

    fun plant(b: MB, x: Float, z: Float, s: Float, rng: City.Rng, y: Float = FL) {
        b.m(Mt.PLAIN)
        b.cyl(x, y, z, 0.18f * s, 0.22f * s, 0.42f * s, rng.pick(arrayOf(C("#D9D2C5"), C("#3A3A3A"), C("#B5643C"), C("#FFFFFF"))), true, 12)
        b.cyl(x, y + 0.4f * s, z, 0.2f * s, 0.2f * s, 0.02f, C("#4E3B2A"), true, 12)
        val gc = rng.pick(arrayOf(C("#3E8E41"), C("#2E7D32"), C("#558B2F")))
        for (k in 0 until 3) {
            val a = k * 2.09f
            CityGeo.ball(b, x + cos(a) * 0.14f * s, y + (0.7f + (k % 2) * 0.25f) * s, z + sin(a) * 0.14f * s, 0.2f * s, shade(gc, k * 6), 0.28f * s, 7)
        }
    }

    fun floorLamp(b: MB, x: Float, z: Float) {
        b.m(Mt.METAL, 1f)
        b.cyl(x, FL, z, 0.17f, 0.17f, 0.03f, C("#2B2B2B"), true, 12)
        b.cyl(x, FL, z, 0.02f, 0.02f, 1.5f, C("#2B2B2B"), true, 6)
        b.m(Mt.FABRIC, 1f)
        b.cyl(x, FL + 1.4f, z, 0.24f, 0.16f, 0.3f, C("#F3E9D2"), true, 14)
    }

    fun diningSet(b: MB, l: L, wood: Int, n: Int, fab: Int) {
        val y = FL
        val tw = if (n > 4) 2.2f else 1.4f
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, y + 0.75f, 0f, tw, 0.05f, 0.9f, wood)
        for (s in floatArrayOf(-1f, 1f)) for (t in floatArrayOf(-1f, 1f)) lb(b, l, s * (tw / 2 - 0.08f), y + 0.37f, t * 0.36f, 0.06f, 0.74f, 0.06f, shade(wood, -15))
        val per = n / 2
        for (k in 0 until per) for (s in floatArrayOf(-1f, 1f)) {
            val cx = -tw / 2 + tw * (k + 0.5f) / per
            chair(b, L(l.wx(cx, s * 0.75f), l.wz(cx, s * 0.75f), l.fx * s, l.fz * s), wood, fab)
        }
        b.m(Mt.PLAIN)
        lcyl(b, l, 0f, y + 0.775f, 0f, 0.12f, 0.08f, 0.2f, C("#FFFFFF"), 10)
        lsph(b, l, 0f, y + 1.0f, 0f, 0.12f, C("#E57373"), 0.08f, 7)
    }

    /** Cadeira com a frente (onde se senta) para F. */
    fun chair(b: MB, l: L, wood: Int, fab: Int) {
        val y = FL
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, y + 0.46f, 0f, 0.44f, 0.04f, 0.44f, wood)
        for (s in floatArrayOf(-0.19f, 0.19f)) for (t in floatArrayOf(-0.19f, 0.19f)) lb(b, l, s, y + 0.23f, t, 0.04f, 0.46f, 0.04f, shade(wood, -15))
        for (s in floatArrayOf(-0.19f, 0.19f)) lb(b, l, s, y + 0.72f, 0.2f, 0.04f, 0.52f, 0.04f, shade(wood, -15))
        lb(b, l, 0f, y + 0.86f, 0.2f, 0.42f, 0.16f, 0.03f, wood)
        b.m(Mt.FABRIC, 1f)
        lb(b, l, 0f, y + 0.5f, 0f, 0.4f, 0.04f, 0.4f, fab)
    }

    /** Bancada de cozinha encostada na parede atrás de [l] (largura [w]): armários, pia, fogão, armários de cima. */
    fun kitchen(b: MB, l: L, w: Float, cab: Int, top: Int, rng: City.Rng) {
        val y = FL
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, y + 0.43f, 0f, w, 0.86f, 0.6f, cab)
        b.m(Mt.PLAIN)
        val nd = max(2, (w / 0.6f).toInt())
        for (k in 0 until nd) {
            val dx = -w / 2 + w * (k + 0.5f) / nd
            lb(b, l, dx, y + 0.43f, -0.305f, w / nd - 0.03f, 0.78f, 0.01f, shade(cab, 10))
            lb(b, l, dx + w / nd * 0.32f, y + 0.66f, -0.315f, 0.02f, 0.14f, 0.02f, C("#B0B0B0"))
        }
        b.m(Mt.STONE, 1.5f)
        lb(b, l, 0f, y + 0.885f, -0.01f, w + 0.02f, 0.04f, 0.63f, top)
        // pia
        b.m(Mt.METAL, 1f)
        lb(b, l, -w * 0.22f, y + 0.9f, 0f, 0.6f, 0.012f, 0.42f, C("#C9CED3"))
        lb(b, l, -w * 0.22f, y + 0.85f, 0f, 0.52f, 0.1f, 0.36f, C("#9EA4AA"))
        lcyl(b, l, -w * 0.22f, y + 0.9f, 0.22f, 0.02f, 0.02f, 0.3f, C("#D0D4D8"), 6)
        lb(b, l, -w * 0.22f, y + 1.19f, 0.12f, 0.03f, 0.03f, 0.22f, C("#D0D4D8"))
        // fogão
        lb(b, l, w * 0.22f, y + 0.9f, 0f, 0.6f, 0.02f, 0.55f, C("#1C1C1C"))
        for (s in floatArrayOf(-0.14f, 0.14f)) for (t in floatArrayOf(-0.12f, 0.12f)) lcyl(b, l, w * 0.22f + s, y + 0.91f, t, 0.08f, 0.08f, 0.012f, C("#3A3A3A"), 10)
        lb(b, l, w * 0.22f, y + 0.45f, -0.305f, 0.56f, 0.5f, 0.012f, C("#2B2B2B"))
        // coifa e armários de cima
        lb(b, l, w * 0.22f, y + 1.75f, 0.12f, 0.7f, 0.25f, 0.4f, C("#C9CED3"))
        b.m(Mt.WOOD, 1f)
        for (s in floatArrayOf(-1f, 1f)) {
            val cx = s * (w * 0.22f + 0.5f + (w / 2 - w * 0.22f - 0.5f) / 2)
            val cw = (w / 2 - w * 0.22f - 0.4f)
            if (cw > 0.3f) lb(b, l, cx * 0.9f, y + 1.85f, 0.13f, cw, 0.7f, 0.34f, cab)
        }
        b.m(Mt.PLAIN)
        lcyl(b, l, w * 0.4f, y + 0.905f, -0.05f, 0.08f, 0.07f, 0.18f, C("#D84315"), 10)   // chaleira
        lb(b, l, -w * 0.42f, y + 0.95f, 0.12f, 0.35f, 0.12f, 0.22f, C("#E0E0E0"))          // micro-ondas pequeno
    }

    fun fridge(b: MB, l: L) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.92f, 0f, 0.75f, 1.84f, 0.7f, C("#DDE1E4"))
        b.m(Mt.PLAIN)
        lb(b, l, 0f, FL + 1.3f, -0.352f, 0.73f, 0.01f, 0.01f, C("#9AA0A6"))
        for (y in floatArrayOf(1.6f, 0.75f)) lb(b, l, 0.3f, FL + y, -0.37f, 0.03f, 0.35f, 0.03f, C("#B0B6BC"))
    }

    fun bed(b: MB, l: L, wood: Int, blanket: Int, dbl: Boolean) {
        val y = FL; val w = if (dbl) 1.6f else 0.95f
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, y + 0.2f, 0f, w + 0.1f, 0.25f, 2.1f, wood)
        lb(b, l, 0f, y + 0.6f, 1.05f, w + 0.14f, 1.0f, 0.08f, shade(wood, -10))
        b.m(Mt.FABRIC, 1f)
        lb(b, l, 0f, y + 0.42f, 0f, w, 0.2f, 2.0f, C("#F5F5F5"))
        lb(b, l, 0f, y + 0.535f, -0.18f, w + 0.04f, 0.05f, 1.55f, blanket)
        lb(b, l, 0f, y + 0.45f, -0.95f, w + 0.06f, 0.2f, 0.06f, blanket)
        val np = if (dbl) 2 else 1
        for (k in 0 until np) lb(b, l, if (dbl) (k - 0.5f) * 0.72f else 0f, y + 0.6f, 0.82f, 0.6f, 0.14f, 0.32f, C("#FFFFFF"))
        lb(b, l, 0f, y + 0.565f, -0.3f, w * 0.9f, 0.025f, 0.4f, shade(blanket, 25))
    }

    fun nightstand(b: MB, l: L, wood: Int) {
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, FL + 0.28f, 0f, 0.45f, 0.56f, 0.4f, wood)
        b.m(Mt.PLAIN)
        lb(b, l, 0f, FL + 0.36f, -0.205f, 0.38f, 0.16f, 0.01f, shade(wood, -15))
        lcyl(b, l, 0f, FL + 0.56f, 0f, 0.06f, 0.04f, 0.22f, C("#9E9E9E"), 8)
        b.m(Mt.FABRIC, 1f)
        lcyl(b, l, 0f, FL + 0.74f, 0f, 0.15f, 0.1f, 0.18f, C("#F6EDDC"), 12)
    }

    fun wardrobe(b: MB, l: L, wood: Int, w: Float) {
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, FL + 1.05f, 0f, w, 2.1f, 0.6f, wood)
        b.m(Mt.PLAIN)
        val n = max(2, (w / 0.5f).toInt())
        for (k in 1 until n) lb(b, l, -w / 2 + w * k / n, FL + 1.05f, -0.302f, 0.012f, 2.0f, 0.01f, shade(wood, -25))
        for (k in 0 until n) lb(b, l, -w / 2 + w * (k + 0.5f) / n + (if (k % 2 == 0) 0.17f else -0.17f) * w / n * 2f, FL + 1.05f, -0.315f, 0.025f, 0.3f, 0.02f, C("#B0B0B0"))
    }

    fun desk(b: MB, l: L, wood: Int, fab: Int) {
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, FL + 0.74f, 0f, 1.3f, 0.04f, 0.65f, wood)
        for (s in floatArrayOf(-0.6f, 0.6f)) lb(b, l, s, FL + 0.37f, 0f, 0.05f, 0.74f, 0.6f, shade(wood, -15))
        b.m(Mt.METAL, 1f)
        lb(b, l, 0.1f, FL + 1.05f, 0.18f, 0.6f, 0.36f, 0.03f, C("#1A1A1A"))
        lb(b, l, 0.1f, FL + 1.05f, 0.163f, 0.56f, 0.32f, 0.005f, C("#26476B"))
        lb(b, l, 0.1f, FL + 0.82f, 0.2f, 0.05f, 0.14f, 0.05f, C("#1A1A1A"))
        lb(b, l, 0.05f, FL + 0.77f, -0.08f, 0.45f, 0.02f, 0.15f, C("#2A2A2A"))
        officeChair(b, L(l.wx(0f, -0.65f), l.wz(0f, -0.65f), -l.fx, -l.fz), fab)
    }

    fun officeChair(b: MB, l: L, fab: Int) {
        b.m(Mt.METAL, 1f)
        lcyl(b, l, 0f, FL + 0.05f, 0f, 0.28f, 0.28f, 0.04f, C("#222222"), 5)
        lcyl(b, l, 0f, FL + 0.05f, 0f, 0.03f, 0.03f, 0.4f, C("#555555"), 6)
        b.m(Mt.FABRIC, 1f)
        lb(b, l, 0f, FL + 0.47f, 0f, 0.48f, 0.08f, 0.46f, fab)
        lb(b, l, 0f, FL + 0.82f, 0.22f, 0.44f, 0.56f, 0.07f, fab)
    }

    fun bathroom(b: MB, x0: Float, z0: Float, x1: Float, z1: Float, backZ: Float, fz: Float) {
        // privada e pia encostadas na parede de trás; box de vidro no canto
        val l = L((x0 + x1) / 2, backZ, fz, 0f).let { L(x0 + 0.5f, backZ + fz * 0.4f, 0f, fz) }
        b.m(Mt.PLAIN)
        val wc = C("#FAFAFA")
        lb(b, l, 0f, FL + 0.2f, 0f, 0.38f, 0.4f, 0.55f, wc)
        lb(b, l, 0f, FL + 0.42f, -0.02f, 0.4f, 0.04f, 0.5f, C("#EEEEEE"))
        lb(b, l, 0f, FL + 0.65f, 0.25f, 0.4f, 0.42f, 0.18f, wc)
        val l2 = L(x1 - 0.45f, backZ + fz * 1.58f, 0f, -fz)   // pia na parede da frente, ao lado da porta
        lb(b, l2, 0f, FL + 0.42f, 0f, 0.12f, 0.84f, 0.12f, wc)
        lb(b, l2, 0f, FL + 0.86f, 0f, 0.6f, 0.12f, 0.45f, wc)
        b.m(Mt.METAL, 1f)
        lb(b, l2, 0f, FL + 1.55f, 0.2f, 0.55f, 0.75f, 0.02f, C("#CFE3EA"))
        lb(b, l2, 0f, FL + 0.95f, 0.15f, 0.03f, 0.12f, 0.03f, C("#C0C0C0"))
        // box
        val sx = x1 - 0.55f; val sz = backZ + fz * 0.55f
        b.m(Mt.TILE, 2f)
        b.box(sx, FL + 0.03f, sz, 0.95f, 0.06f, 0.95f, C("#E0E6EA"))
        b.m(Mt.GLASS); b.al = 0.25f
        b.box(sx - 0.47f, FL + 1.0f, sz, 0.02f, 1.9f, 0.95f, C("#DFF3FA"))
        b.box(sx, FL + 1.0f, sz + fz * 0.47f, 0.95f, 1.9f, 0.02f, C("#DFF3FA"))
        b.al = 1f
        b.m(Mt.METAL, 1f)
        b.cyl(sx + 0.3f, FL + 1.9f, sz + fz * 0.3f, 0.12f, 0.12f, 0.03f, C("#C0C0C0"), true, 10)
    }

    // ============================================================ casas

    private val WALLS = arrayOf("#F3E9DA", "#E8D5C0", "#DCE7EE", "#F2DCD3", "#E9EFD9", "#FFF4D6", "#D9D4E8", "#F6F1EA", "#E7C9A9", "#CFE0D8", "#F7E1A0", "#B9D7EA", "#EFC3B3", "#FFFFFF", "#D7E3C2")
    private val ROOFS = arrayOf("#8E4B3A", "#5B5F66", "#A0522D", "#6B3E2E", "#465A6B", "#7A6A5A", "#9C4A2F", "#3E4A52")
    private val DOORS = arrayOf("#6B3E26", "#2F5D50", "#1F3A5F", "#8C2F39", "#3E3E3E", "#B5835A", "#FFFFFF")

    /**
     * Casa de um lote. Frente em z = [fz0] (fachada virada para [fz] = ±1), lote de x0..x1 e profundidade [depth].
     * [style]: 0 tradicional (duas águas), 1 moderna (laje plana), 2 sobrado (2 andares, quatro águas), 3 chalé (telhado alto, madeira), 4 casa de praia (varanda grande).
     */
    fun house(g: Gen, x0: Float, x1: Float, fz0: Float, fz: Float, depth: Float, style: Int, forSale: Boolean, mansion: Boolean = false) {
        val rng = g.rng
        val lotW = x1 - x0
        val wall = C(rng.pick(WALLS)); val roof = C(rng.pick(ROOFS)); val trim = C("#FFFFFF")
        val wood = rng.pick(WOODS)
        val hw = if (mansion) min(lotW - 8f, rng.r(18f, 24f)) else min(lotW - 4.3f, rng.r(8.5f, 11f))
        val hd = if (mansion) rng.r(13f, 15f) else rng.r(8.2f, 10f)
        val set = if (mansion) rng.r(9f, 11f) else rng.r(5.5f, 7f)
        val sideGar = rng.chance(0.5f)
        val hcx = (x0 + x1) / 2 + (if (mansion) 0f else (if (sideGar) -1.6f else 1.6f))
        val hx0 = hcx - hw / 2; val hx1 = hcx + hw / 2
        fun Z(d: Float) = fz0 - fz * d                       // profundidade -> z do mundo
        val zf = Z(set); val zb = Z(set + hd)
        val hz0 = min(zf, zb); val hz1 = max(zf, zb)
        val floors = if (mansion || style == 2) 2 else 1
        val wh = if (style == 1 || mansion) 3.2f else 2.9f
        val topY = FL + wh
        val name = if (mansion) "Mansão" else when (style) { 1 -> "Casa moderna"; 2 -> "Sobrado"; 3 -> "Chalé"; 4 -> "Casa de praia"; else -> "Casa" }

        // jardim: caminho, garagem, gramado com flores
        g.b.m(Mt.PAVER, 0.8f)
        g.b.box(hcx, CURB + 0.01f, (fz0 + zf) / 2, 1.3f, 0.02f, abs(zf - fz0), C("#D8CFC2"))
        val gx = if (mansion) hx1 + 3.5f else if (sideGar) hx1 + 2.0f else hx0 - 2.0f
        val drive = !mansion || true
        if (drive) { g.b.m(Mt.ASPHALT, 0.3f); g.b.box(gx, CURB + 0.012f, (fz0 + Z(set + 6f)) / 2, 3.2f, 0.02f, set + 6f, C("#BDBDBD")) }
        flowers(g, hx0 + 0.3f, min(zf, Z(set - 1.2f)), hx1 - 0.3f, max(zf, Z(set - 1.2f)), if (mansion) 30 else 12, CURB + 0.01f)
        for (k in 0 until (if (mansion) 6 else 3)) bush(g, g.rng.r(hx0, hx1), Z(set - 0.6f), rng.r(0.8f, 1.1f))

        val bd = g.begin(hx0, hz0, hx1, hz1, name)
        bd.forSale = forSale
        bd.price = ((if (mansion) 900000 else 150000 + style * 40000) + rng.i(80) * 1000)
        val A = g.A; val H = g.H

        // fundação e piso
        A.m(Mt.STONE, 0.6f)
        A.box(hcx, FL / 2, (hz0 + hz1) / 2, hw + 0.1f, FL, hd + 0.1f, C("#B9B3AA"))
        val fmat = rng.pick(arrayOf(Mt.FLOOR_L, Mt.FLOOR_D, Mt.TILE))
        A.m(fmat, 0.7f)
        A.box(hcx, FL - 0.005f, (hz0 + hz1) / 2, hw - 0.3f, 0.012f, hd - 0.3f, C("#FFFFFF"))
        // degrau na porta
        A.m(Mt.STONE, 0.6f)
        A.box(hcx, FL / 2, Z(set - 0.45f), 1.8f, FL, 0.9f, C("#CFC8BD"))

        // paredes externas
        val matOut = when (style) { 3 -> Mt.SIDING; 1 -> Mt.PLASTER; else -> if (rng.chance(0.4f)) Mt.SIDING else Mt.PLASTER }
        val inC = C(rng.pick(arrayOf("#F6F1EA", "#EFE8DC", "#E8EEF1", "#F4EAE0", "#FFFFFF")))
        val winW = if (style == 1) 2.2f else 1.3f
        val sill = if (style == 1) FL + 0.5f else FL + 1.0f
        val winT = FL + 2.2f
        // frente: porta no meio + janelas
        val fOps = ArrayList<Op>()
        fOps.add(Op(hcx, 1.1f, FL, FL + 2.2f, true))
        val nwf = if (mansion) 3 else 1
        for (k in 1..nwf) for (s in floatArrayOf(-1f, 1f)) fOps.add(Op(hcx + s * (hw / 2) * (k / (nwf + 0.8f)) * 1.6f * (if (nwf == 1) 0.6f else 0.55f), winW, sill, winT, false))
        wall(g, 0, zf, hx0, hx1, FL, topY, if (fz > 0) 1 else -1, fOps, wall, inC, matOut)
        // fundos
        val bOps = arrayListOf(Op(hx0 + hw * 0.25f, 1.2f, FL + 1.0f, winT, false), Op(hx0 + hw * 0.75f, 1.2f, FL + 1.0f, winT, false))
        wall(g, 0, zb, hx0, hx1, FL, topY, if (fz > 0) -1 else 1, bOps, wall, inC, matOut)
        // laterais
        val sOps = arrayListOf(Op((hz0 + hz1) / 2 + hd * 0.22f, 1.2f, FL + 1.0f, winT, false), Op((hz0 + hz1) / 2 - hd * 0.25f, 1.0f, FL + 1.3f, winT, false))
        wall(g, 1, hx0, hz0 + 0.1f, hz1 - 0.1f, FL, topY, -1, sOps, wall, inC, matOut)
        wall(g, 1, hx1, hz0 + 0.1f, hz1 - 0.1f, FL, topY, 1, sOps, wall, inC, matOut)
        // paredes como sólidos (a porta fica aberta)
        g.solid(hx0 - 0.2f, hz0 - 0.2f, hx0 + 0.2f, hz1 + 0.2f); g.solid(hx1 - 0.2f, hz0 - 0.2f, hx1 + 0.2f, hz1 + 0.2f)
        g.solid(hx0, zb - 0.2f, hx1, zb + 0.2f)
        g.solid(hx0, zf - 0.2f, hcx - 0.62f, zf + 0.2f); g.solid(hcx + 0.62f, zf - 0.2f, hx1, zf + 0.2f)
        // porta aberta (folha encostada por dentro) e luminária da entrada
        H.m(Mt.WOOD, 1f)
        val dc = C(rng.pick(DOORS))
        H.box(hcx - 0.55f + 0.03f, FL + 1.1f, zf - fz * 0.55f, 0.05f, 2.15f, 1.0f, dc)
        H.m(Mt.PLAIN); H.box(hcx + 0.85f, FL + 2.0f, zf + fz * 0.13f, 0.14f, 0.24f, 0.08f, C("#FFF3C4"), false)

        // divisórias de dentro: frente (sala/jantar) e fundo (cozinha à esquerda, quarto à direita, banheiro no canto do quarto)
        val split = Z(set + hd * 0.55f)
        val midX = hcx + (if (rng.chance(0.5f)) -0.4f else 0.4f)
        val bdX = midX + 0.75f   // porta do quarto, junto da parede do meio
        wall(g, 0, split, hx0 + 0.1f, hx1 - 0.1f, FL, topY, 1, listOf(Op(hx0 + hw * 0.25f, 2.2f, FL, FL + 2.3f, true), Op(bdX, 0.95f, FL, FL + 2.15f, true)), inC, inC, Mt.PLASTER, 0.12f, true)
        wall(g, 1, midX, min(split, zb) + 0.06f, max(split, zb) - 0.06f, FL, topY, 1, emptyList(), inC, inC, Mt.PLASTER, 0.12f, true)
        g.solid(hx0, split - 0.08f, hx0 + hw * 0.25f - 1.1f, split + 0.08f); g.solid(hx0 + hw * 0.25f + 1.1f, split - 0.08f, bdX - 0.48f, split + 0.08f)
        g.solid(bdX + 0.48f, split - 0.08f, hx1, split + 0.08f)
        g.solid(midX - 0.08f, min(split, zb), midX + 0.08f, max(split, zb))
        // banheiro: canto de trás do quarto (porta na parede da frente dele, abrindo para o quarto)
        val bathW = 2.2f
        val bx0 = hx1 - bathW
        val bzF = Z(set + hd - 2.0f)
        wall(g, 1, bx0, min(bzF, zb) + 0.06f, max(bzF, zb) - 0.06f, FL, topY, 1, emptyList(), inC, inC, Mt.PLASTER, 0.1f, true)
        wall(g, 0, bzF, bx0, hx1 - 0.1f, FL, topY, 1, listOf(Op(bx0 + 0.6f, 0.8f, FL, FL + 2.1f, true)), inC, inC, Mt.PLASTER, 0.1f, true)
        g.solid(bx0 - 0.06f, min(bzF, zb), bx0 + 0.06f, max(bzF, zb))
        g.solid(bx0 + 1.0f, bzF - 0.06f, hx1, bzF + 0.06f)
        A.m(Mt.TILE, 2.5f); A.box((bx0 + hx1) / 2, FL + 0.004f, (bzF + zb) / 2, bathW - 0.2f, 0.01f, 1.8f, C("#E3EAF0"))
        bathroom(A, bx0 + 0.15f, min(bzF, zb), hx1 - 0.15f, max(bzF, zb), zb + fz * 0.12f, fz)

        // --- móveis
        val fab = rng.pick(FABRICS)
        val front = L(hcx, Z(set + 0.2f), fz, 0f)
        // sala: sofa olhando para a TV
        val sofaZ = Z(set + hd * 0.42f); val tvZ = Z(set + 0.45f)
        val sx = hcx + (if (sideGar) -hw * 0.18f else hw * 0.18f)
        sofa(A, L(sx, sofaZ, 0f, fz), if (mansion) 3.0f else 2.2f, fab)
        g.solid(sx - 1.2f, sofaZ - 0.5f, sx + 1.2f, sofaZ + 0.5f)
        tvUnit(A, L(sx, tvZ + fz * 0.0f, 0f, -fz), wood)
        coffeeTable(A, L(sx, (sofaZ + tvZ) / 2, 0f, fz), wood)
        rug(A, sx - 1.5f, min(sofaZ, tvZ) + 0.6f, sx + 1.5f, max(sofaZ, tvZ) - 0.6f, rng.pick(FABRICS))
        armchair(A, L(sx + (if (sideGar) 1.8f else -1.8f), (sofaZ + tvZ) / 2, if (sideGar) -1f else 1f, 0f), shade(fab, 18))
        plant(A, hx0 + 0.45f, Z(set + 0.5f), 1.0f, rng)
        plant(A, hx1 - 0.45f, Z(set + 0.5f), 0.9f, rng)
        floorLamp(A, sx - 1.5f, sofaZ)
        // jantar do outro lado
        val dx = hcx + (if (sideGar) hw * 0.27f else -hw * 0.27f)
        diningSet(A, L(dx, Z(set + hd * 0.3f), 0f, fz), wood, if (mansion) 8 else 4, fab)
        g.solid(dx - 0.8f, Z(set + hd * 0.3f) - 0.5f, dx + 0.8f, Z(set + hd * 0.3f) + 0.5f)
        bookshelf(A, L(if (sideGar) hx1 - 0.3f else hx0 + 0.3f, Z(set + hd * 0.2f), if (sideGar) -1f else 1f, 0f), wood, rng)
        // cozinha (fundo, esquerda de midX): bancada no fundo e geladeira na ponta
        val kw = max(1.2f, min(3.4f, midX - hx0 - 1.45f))
        kitchen(A, L(hx0 + 0.2f + kw / 2, zb + fz * 0.45f, 0f, fz), kw, rng.pick(arrayOf(C("#FFFFFF"), C("#5B7065"), C("#2F3E46"), C("#C8A27A"), C("#E9E4D9"))), C(rng.pick(arrayOf("#2B2B2B", "#E8E4DC", "#7E7E7E"))), rng)
        g.solid(hx0, min(zb, zb + fz * 0.8f), hx0 + 0.2f + kw, max(zb, zb + fz * 0.8f))
        val frX = hx0 + 0.2f + kw + 0.45f
        if (frX + 0.4f < midX) { fridge(A, L(frX, zb + fz * 0.45f, 0f, fz)); g.solid(frX - 0.4f, min(zb, zb + fz * 0.85f), frX + 0.4f, max(zb, zb + fz * 0.85f)) }
        // quarto (fundo, direita): cama com a cabeceira no fundo, criado-mudo, guarda-roupa junto da parede da frente
        val room = bx0 - midX
        val dbl = room > 2.1f
        val bwid = if (dbl) 1.6f else 0.95f
        val bedX = bx0 - 0.1f - bwid / 2 - 0.05f
        val bedZ = zb + fz * 1.2f
        bed(A, L(bedX, bedZ, 0f, fz), wood, rng.pick(FABRICS), dbl)
        g.solid(bedX - bwid / 2 - 0.05f, min(zb, zb + fz * 2.3f), bedX + bwid / 2 + 0.05f, max(zb, zb + fz * 2.3f))
        if (bedX - bwid / 2 - 0.55f > midX + 0.1f) nightstand(A, L(bedX - bwid / 2 - 0.3f, zb + fz * 0.3f, 0f, fz), wood)
        val wwid = min(1.8f, hx1 - 0.25f - (bdX + 0.6f))
        if (wwid > 0.8f) {
            val wx = bdX + 0.6f + wwid / 2
            wardrobe(A, L(wx, split - fz * 0.36f, 0f, -fz), wood, wwid)
            g.solid(wx - wwid / 2, min(split, split - fz * 0.7f), wx + wwid / 2, max(split, split - fz * 0.7f))
        }
        rug(A, bedX - bwid / 2 - 0.3f, min(bedZ + fz * 1.4f, bedZ + fz * 0.6f), bedX + bwid / 2 + 0.3f, max(bedZ + fz * 1.4f, bedZ + fz * 0.6f), rng.pick(FABRICS))

        // --- telhado / andar de cima (H)
        val ov = 0.5f
        when {
            style == 1 && !mansion -> {   // laje plana com platibanda e brise de madeira
                H.m(Mt.PLASTER, 0.5f)
                H.box(hcx, topY + 0.15f, (hz0 + hz1) / 2, hw + 0.9f, 0.3f, hd + 0.9f, C("#ECEFF1"))
                H.box(hcx, topY + 0.55f, hz0 - 0.4f, hw + 0.9f, 0.5f, 0.1f, C("#ECEFF1")); H.box(hcx, topY + 0.55f, hz1 + 0.4f, hw + 0.9f, 0.5f, 0.1f, C("#ECEFF1"))
                H.box(hx0 - 0.4f, topY + 0.55f, (hz0 + hz1) / 2, 0.1f, 0.5f, hd + 0.9f, C("#ECEFF1")); H.box(hx1 + 0.4f, topY + 0.55f, (hz0 + hz1) / 2, 0.1f, 0.5f, hd + 0.9f, C("#ECEFF1"))
                H.m(Mt.WOOD, 1f)
                for (k in 0 until 9) H.box(hx0 + 0.6f + k * 0.12f, FL + 1.5f, zf + fz * 0.2f, 0.06f, 2.8f, 0.12f, C("#A0703F"))
                // painéis solares
                H.m(Mt.METAL, 1f)
                for (k in 0 until 4) H.box(hcx - 2.4f + k * 1.6f, topY + 0.45f, (hz0 + hz1) / 2, 1.5f, 0.06f, 2.2f, C("#1E2A44"))
            }
            else -> {
                var baseY = topY
                if (floors == 2) {   // andar de cima fechado, com janelas e (no sobrado) varanda
                    val y2 = topY + 0.25f; val t2 = y2 + 2.9f
                    H.m(Mt.STONE, 0.5f)
                    H.box(hcx, topY + 0.12f, (hz0 + hz1) / 2, hw + 0.2f, 0.25f, hd + 0.2f, C("#E0DCD5"))
                    val u2 = ArrayList<Op>()
                    val nw = if (mansion) 5 else 3
                    for (k in 0 until nw) u2.add(Op(hx0 + hw * (k + 0.5f) / nw, if (mansion) 1.6f else 1.3f, y2 + 0.9f, y2 + 2.3f, false))
                    val gH = Gen(g.idx, rng, 0f, 0f, 0f, 0f).also { it.A = H; it.H = H }
                    wall(gH, 0, zf, hx0, hx1, y2, t2, if (fz > 0) 1 else -1, u2, wall, inC, matOut)
                    wall(gH, 0, zb, hx0, hx1, y2, t2, if (fz > 0) -1 else 1, u2, wall, inC, matOut)
                    wall(gH, 1, hx0, hz0 + 0.1f, hz1 - 0.1f, y2, t2, -1, listOf(Op((hz0 + hz1) / 2, 1.2f, y2 + 0.9f, y2 + 2.3f, false)), wall, inC, matOut)
                    wall(gH, 1, hx1, hz0 + 0.1f, hz1 - 0.1f, y2, t2, 1, listOf(Op((hz0 + hz1) / 2, 1.2f, y2 + 0.9f, y2 + 2.3f, false)), wall, inC, matOut)
                    H.m(Mt.PLASTER, 0.5f); H.box(hcx, t2 - 0.05f, (hz0 + hz1) / 2, hw - 0.2f, 0.1f, hd - 0.2f, inC)
                    if (!mansion) {   // varanda sobre a porta
                        H.m(Mt.STONE, 0.5f); H.box(hcx, topY + 0.1f, Z(set - 0.8f), 3.2f, 0.2f, 1.6f, C("#E0DCD5"))
                        H.m(Mt.METAL, 1f)
                        H.box(hcx, topY + 0.65f, Z(set - 1.55f), 3.2f, 0.05f, 0.05f, C("#2B2B2B"))
                        var k = -1.55f
                        while (k <= 1.56f) { H.box(hcx + k, topY + 0.42f, Z(set - 1.55f), 0.03f, 0.45f, 0.03f, C("#2B2B2B")); k += 0.155f }
                    }
                    baseY = t2
                }
                // telhado: duas águas (0, 3, 4) ou quatro águas (2, mansão)
                H.m(Mt.ROOF, 0.6f)
                val rh = when { style == 3 -> 3.6f; mansion -> 3.2f; style == 2 -> 2.4f; else -> rng.r(2.0f, 2.6f) }
                val ye = baseY - rh * ov / (hd / 2)
                val xa = hx0 - ov; val xb = hx1 + ov; val za = hz0 - ov; val zbb = hz1 + ov; val zm = (hz0 + hz1) / 2
                if (style == 2 || mansion) {
                    val inset = hd / 2
                    q(H, P(xa, ye, za) + P(xb, ye, za) + P(xb - inset, baseY + rh, zm) + P(xa + inset, baseY + rh, zm), roof)
                    q(H, P(xb, ye, zbb) + P(xa, ye, zbb) + P(xa + inset, baseY + rh, zm) + P(xb - inset, baseY + rh, zm), roof)
                    tri(H, P(xa, ye, zbb) + P(xa, ye, za) + P(xa + inset, baseY + rh, zm), roof)
                    tri(H, P(xb, ye, za) + P(xb, ye, zbb) + P(xb - inset, baseY + rh, zm), roof)
                } else {
                    q(H, P(xa, ye, za) + P(xb, ye, za) + P(xb, baseY + rh, zm) + P(xa, baseY + rh, zm), roof)
                    q(H, P(xb, ye, zbb) + P(xa, ye, zbb) + P(xa, baseY + rh, zm) + P(xb, baseY + rh, zm), roof)
                    H.m(matOut, 0.5f)
                    tri(H, P(hx0, baseY, hz0) + P(hx0, baseY, hz1) + P(hx0, baseY + rh, zm), wall)
                    tri(H, P(hx1, baseY, hz1) + P(hx1, baseY, hz0) + P(hx1, baseY + rh, zm), wall)
                    // cumeeira e testeira
                    H.m(Mt.PLAIN)
                    H.box(hcx, baseY + rh + 0.03f, zm, hw + 2 * ov + 0.1f, 0.1f, 0.22f, shade(roof, -25))
                }
                // forro e calha
                H.m(Mt.PLAIN)
                H.box(hcx, ye - 0.04f, za + 0.05f, hw + 2 * ov, 0.12f, 0.1f, shade(roof, -35))
                H.box(hcx, ye - 0.04f, zbb - 0.05f, hw + 2 * ov, 0.12f, 0.1f, shade(roof, -35))
                if (!mansion && rng.chance(0.5f)) { H.m(Mt.STONE, 0.8f); H.box(hcx + hw * 0.28f, baseY + rh * 0.75f, zm + hd * 0.15f, 0.75f, rh * 1.3f, 0.75f, C("#9C5B45")) }
                if (rng.chance(0.35f)) { H.m(Mt.METAL, 1f); H.box(hcx - hw * 0.25f, baseY + rh * 0.35f, za + hd * 0.3f, 2.4f, 0.08f, 1.4f, C("#1E2A44")) }   // aquecedor solar
            }
        }
        // varanda com colunas (tradicional, praia, mansão) — fica em H (some quando entra)
        if (style == 0 || style == 4 || mansion) {
            val pw = if (mansion) 8f else if (style == 4) hw else 3.6f
            val pd = if (style == 4) 2.4f else 1.8f
            H.m(Mt.PLASTER, 0.5f)
            H.box(hcx, topY + 0.12f, Z(set - pd / 2), pw + 0.4f, 0.22f, pd + 0.2f, shade(wall, -8))
            for (k in 0..(if (mansion) 4 else if (style == 4) 4 else 1)) {
                val n = if (mansion || style == 4) 4 else 1
                val cx = hcx - pw / 2 + 0.2f + (pw - 0.4f) * k / n
                H.m(Mt.PLAIN); H.cyl(cx, FL, Z(set - pd + 0.15f), if (mansion) 0.22f else 0.12f, if (mansion) 0.2f else 0.11f, wh, trim, true, 12)
            }
            g.A.m(Mt.WOOD, 1f); g.A.box(hcx, FL - 0.02f, Z(set - pd / 2), pw, 0.04f, pd, C("#B48A60"))
        }
        g.end()

        // garagem (fora do prédio, para não sumir junto)
        if (!mansion && rng.chance(0.55f)) {
            val b = g.b
            b.m(Mt.PLASTER, 0.5f)
            b.box(gx, CURB + 1.35f, Z(set + 3f), 3.6f, 2.7f, 6f, wall)
            g.solid(gx - 1.9f, Z(set) , gx + 1.9f, Z(set + 6f))
            b.m(Mt.METAL, 1f)
            b.box(gx, CURB + 1.15f, Z(set - 0.02f), 2.9f, 2.2f, 0.06f, C("#E4E4E4"))
            b.m(Mt.PLAIN)
            for (k in 0 until 6) b.box(gx, CURB + 0.25f + k * 0.37f, Z(set - 0.06f), 2.9f, 0.025f, 0.03f, C("#BDBDBD"))
            b.m(Mt.ROOF, 0.6f); b.box(gx, CURB + 2.78f, Z(set + 3f), 4.0f, 0.16f, 6.4f, roof)
        }
        if (rng.chance(if (mansion) 1f else 0.7f)) Vehicles.parked(g, gx, Z(set - 2.6f), 1, CURB + 0.012f, rng)
        if (mansion) Vehicles.parked(g, gx, Z(set - 8f), 1, CURB + 0.012f, rng)

        // cerca/muro na frente, caixa de correio, árvore, placa à venda
        val b = g.b
        val fenceType = if (mansion) 2 else rng.i(3)
        val fy = Z(0.35f)
        val gapA = min(hcx - 0.8f, gx - 1.8f); val gapB = max(hcx + 0.8f, gx + 1.8f)
        for (seg in arrayOf(floatArrayOf(x0 + 0.2f, if (sideGar || mansion) hcx - 0.8f else gapA), floatArrayOf(if (sideGar || mansion) hcx + 0.8f else hcx + 0.8f, if (sideGar || mansion) gx - 1.8f else x1 - 0.2f), floatArrayOf(if (sideGar || mansion) gx + 1.8f else x1, x1 - 0.2f))) {
            val a = seg[0]; val e = seg[1]
            if (e - a < 0.4f) continue
            when (fenceType) {
                0 -> {   // cerquinha branca de madeira
                    b.m(Mt.WOOD, 1f)
                    b.box((a + e) / 2, CURB + 0.55f, fy, e - a, 0.07f, 0.05f, C("#FFFFFF")); b.box((a + e) / 2, CURB + 0.28f, fy, e - a, 0.07f, 0.05f, C("#FFFFFF"))
                    var p = a; while (p <= e) { b.box(p, CURB + 0.43f, fy, 0.08f, 0.86f, 0.06f, C("#FFFFFF")); p += 0.22f }
                }
                1 -> {   // mureta com grade
                    b.m(Mt.STONE, 0.8f); b.box((a + e) / 2, CURB + 0.35f, fy, e - a, 0.7f, 0.25f, C("#D7CFC4"))
                    b.m(Mt.METAL, 1f); b.box((a + e) / 2, CURB + 1.45f, fy, e - a, 0.04f, 0.04f, C("#2B2B2B"))
                    var p = a; while (p <= e) { b.box(p, CURB + 1.08f, fy, 0.025f, 0.76f, 0.025f, C("#2B2B2B")); p += 0.14f }
                }
                else -> {   // muro alto (mansão) ou cerca viva
                    if (mansion) { b.m(Mt.STONE, 0.8f); b.box((a + e) / 2, CURB + 1.0f, fy, e - a, 2.0f, 0.3f, C("#E8E0D2")); b.m(Mt.PLAIN); b.box((a + e) / 2, CURB + 2.04f, fy, e - a + 0.05f, 0.08f, 0.36f, C("#CFC6B6")) }
                    else { var p = a + 0.4f; while (p < e) { g.fl.place("hedge", p.toDouble(), CURB.toDouble(), fy.toDouble(), 0.8, 0.0); p += 1.2f } }
                }
            }
            g.solid(a, fy - 0.2f, e, fy + 0.2f)
        }
        if (mansion) {   // portão de entrada da garagem
            b.m(Mt.METAL, 1f)
            var p = gx - 1.6f
            while (p <= gx + 1.6f) { b.box(p, CURB + 1.0f, fy, 0.04f, 2.0f, 0.04f, C("#1B1B1B")); p += 0.16f }
            b.box(gx, CURB + 1.95f, fy, 3.3f, 0.08f, 0.06f, C("#B8860B"))
        }
        b.m(Mt.METAL, 1f)
        b.box(hcx + 1.3f, CURB + 0.5f, Z(0.7f), 0.06f, 1.0f, 0.06f, C("#444444"))
        b.box(hcx + 1.3f, CURB + 1.05f, Z(0.7f), 0.25f, 0.22f, 0.42f, C(rng.pick(arrayOf("#C0392B", "#2C3E50", "#27AE60", "#F2F2F2"))))
        if (rng.chance(0.7f)) tree(g, if (sideGar) x0 + 2.2f else x1 - 2.2f, Z(depth - 3.5f), rng.r(0.9f, 1.3f))
        if (rng.chance(0.6f)) tree(g, if (sideGar) x0 + 1.8f else x1 - 1.8f, Z(2.0f), rng.r(0.7f, 1.0f))
        if (forSale) {
            b.m(Mt.WOOD, 1f); b.box(hcx - 2.2f, CURB + 0.6f, Z(1.4f), 0.08f, 1.2f, 0.08f, C("#5D4037"))
            sign(b, hcx - 2.2f, CURB + 1.0f, Z(1.4f) + fz * 0.06f, 0f, fz, 1.4f, 0.32f, City.signIdx("À VENDA"))
        }
        // quintal dos fundos: churrasqueira / piscina (mansão)
        if (mansion) {
            val pz0 = Z(set + hd + 2f); val pz1 = Z(set + hd + 9f)
            b.m(Mt.PAVER, 0.7f); b.box(hcx, CURB + 0.02f, (pz0 + pz1) / 2, 12f, 0.04f, abs(pz1 - pz0) + 2f, C("#EFE6D6"))
            b.m(Mt.TILE, 2f); b.box(hcx, CURB + 0.03f, (pz0 + pz1) / 2, 9f, 0.04f, abs(pz1 - pz0) - 1f, C("#5EC7E8"))
            b.m(Mt.PLAIN); b.al = 0.6f; b.box(hcx, CURB + 0.06f, (pz0 + pz1) / 2, 8.8f, 0.01f, abs(pz1 - pz0) - 1.2f, C("#8FE3F7")); b.al = 1f
            g.solid(hcx - 4.5f, min(pz0, pz1) + 0.5f, hcx + 4.5f, max(pz0, pz1) - 0.5f)
            for (k in 0 until 3) { b.m(Mt.FABRIC, 1f); b.box(hcx - 3f + k * 2.5f, CURB + 0.3f, Z(set + hd + 1.3f), 0.7f, 0.12f, 1.9f, C("#FFFFFF")) }
            palm(g, hcx - 6.5f, pz1, 0.9f); palm(g, hcx + 6.5f, pz1, 1.0f)
        } else if (rng.chance(0.5f)) {
            b.m(Mt.STONE, 0.8f); b.box(hx0 + 1.2f, CURB + 0.9f, Z(set + hd + 2.2f), 1.4f, 1.8f, 0.9f, C("#A1887F"))
            b.m(Mt.PLAIN); b.box(hx0 + 1.2f, CURB + 2.2f, Z(set + hd + 2.2f), 0.5f, 1.0f, 0.5f, C("#8D6E63"))
            g.solid(hx0 + 0.5f, Z(set + hd + 1.7f), hx0 + 1.9f, Z(set + hd + 2.7f))
        }

        // longe: caixa com telhado simples
        val f = g.f
        f.m(if (style == 1) Mt.PLASTER else matOut, 0.5f)
        f.box(hcx, FL + wh * floors / 2 + (if (floors == 2) 0.15f else 0f), (hz0 + hz1) / 2, hw, wh * floors + (if (floors == 2) 0.3f else 0f), hd, wall)
        val by = FL + wh * floors + (if (floors == 2) 0.3f else 0f)
        if (style == 1 && !mansion) { f.m(Mt.PLAIN); f.box(hcx, by + 0.2f, (hz0 + hz1) / 2, hw + 0.6f, 0.4f, hd + 0.6f, C("#ECEFF1")) }
        else {
            f.m(Mt.ROOF, 0.6f)
            val rh = if (style == 3) 3.6f else 2.4f
            q(f, P(hx0 - 0.4f, by, hz0 - 0.4f) + P(hx1 + 0.4f, by, hz0 - 0.4f) + P(hx1 + 0.4f, by + rh, (hz0 + hz1) / 2) + P(hx0 - 0.4f, by + rh, (hz0 + hz1) / 2), roof)
            q(f, P(hx1 + 0.4f, by, hz1 + 0.4f) + P(hx0 - 0.4f, by, hz1 + 0.4f) + P(hx0 - 0.4f, by + rh, (hz0 + hz1) / 2) + P(hx1 + 0.4f, by + rh, (hz0 + hz1) / 2), roof)
            f.m(Mt.PLASTER, 0.5f)
            tri(f, P(hx0, by, hz0) + P(hx0, by, hz1) + P(hx0, by + rh, (hz0 + hz1) / 2), wall)
            tri(f, P(hx1, by, hz1) + P(hx1, by, hz0) + P(hx1, by + rh, (hz0 + hz1) / 2), wall)
        }
    }

    /** Terreno vazio à venda: grama alta, estacas e placa. */
    fun emptyLot(g: Gen, x0: Float, x1: Float, fz0: Float, fz: Float, depth: Float) {
        val b = g.b
        fun Z(d: Float) = fz0 - fz * d
        b.m(Mt.GRASS, 0.25f)
        b.box((x0 + x1) / 2, CURB + 0.005f, (fz0 + Z(depth)) / 2, x1 - x0 - 0.4f, 0.01f, depth - 0.4f, C("#C9DDA6"))
        for (k in 0 until 14) g.fl.place(if (k % 2 == 0) "grass_a" else "grass_b", g.rng.r(x0 + 0.5f, x1 - 0.5f).toDouble(), CURB.toDouble(), g.rng.r(min(fz0, Z(depth)), max(fz0, Z(depth))).toDouble(), g.rng.r(1.2f, 2f).toDouble(), g.rng.r(0f, 6f).toDouble())
        b.m(Mt.WOOD, 1f)
        for (c in arrayOf(floatArrayOf(x0 + 0.4f, Z(0.4f)), floatArrayOf(x1 - 0.4f, Z(0.4f)), floatArrayOf(x0 + 0.4f, Z(depth - 0.4f)), floatArrayOf(x1 - 0.4f, Z(depth - 0.4f)))) {
            b.box(c[0], CURB + 0.4f, c[1], 0.07f, 0.8f, 0.07f, C("#C8A27A"))
            b.m(Mt.PLAIN); b.box(c[0], CURB + 0.78f, c[1], 0.08f, 0.06f, 0.08f, C("#E53935")); b.m(Mt.WOOD, 1f)
        }
        b.m(Mt.PLAIN)
        b.al = 1f
        for (s in intArrayOf(0, 1)) {   // fita zebrada na frente
            val y = CURB + 0.6f
            b.box((x0 + x1) / 2, y, Z(0.4f), x1 - x0 - 0.8f, 0.04f, 0.01f, C("#F2C230"))
        }
        b.m(Mt.WOOD, 1f)
        val cx = (x0 + x1) / 2
        b.box(cx - 0.8f, CURB + 0.9f, Z(1.2f), 0.1f, 1.8f, 0.1f, C("#5D4037")); b.box(cx + 0.8f, CURB + 0.9f, Z(1.2f), 0.1f, 1.8f, 0.1f, C("#5D4037"))
        sign(b, cx, CURB + 1.15f, Z(1.2f) + fz * 0.07f, 0f, fz, 2.2f, 0.55f, City.signIdx("TERRENO À VENDA"))
        g.place(City.Place("Terreno à venda", cx, Z(depth / 2), 0xFFF2C230.toInt(), 'T'))
    }

    // ============================================================ prédios

    /**
     * Prédio: térreo com interior (loja/portaria) onde se entra, andares com fachada de janelas, platibanda, teto com equipamentos.
     * Frente em z = [fz0] virada para [fz]; ocupa x0..x1, profundidade [d] a partir de [set].
     */
    fun tower(g: Gen, x0: Float, x1: Float, fz0: Float, fz: Float, set: Float, d: Float, floors: Int, col: Int, shop: String?, kind: Int, balcony: Boolean = false, glassy: Boolean = false): Float {
        val rng = g.rng
        fun Z(dd: Float) = fz0 - fz * dd
        val w = x1 - x0; val cx = (x0 + x1) / 2
        val zf = Z(set); val zb = Z(set + d); val z0 = min(zf, zb); val z1 = max(zf, zb); val cz = (z0 + z1) / 2
        val gh = 4.4f; val topY = FL + gh + floors * 3f
        val bd = g.begin(x0, z0, x1, z1, shop?.let { it.lowercase().replaceFirstChar { c -> c.uppercase() } } ?: "Prédio")
        val A = g.A; val H = g.H
        A.m(Mt.STONE, 0.6f); A.box(cx, FL / 2, cz, w, FL, d, C("#9E9E9E"))
        A.m(if (kind == 3) Mt.TILE else rng.pick(arrayOf(Mt.TILE, Mt.STONE, Mt.FLOOR_L)), 0.6f); A.box(cx, FL - 0.005f, cz, w - 0.3f, 0.012f, d - 0.3f, C("#F2F2F2"))
        // térreo: vitrine de vidro na frente com porta, paredes nos outros lados
        val fOps = ArrayList<Op>()
        val nv = max(1, (w / 4f).toInt())
        for (k in 0 until nv) {
            val c = x0 + w * (k + 0.5f) / nv
            fOps.add(if (k == nv / 2) Op(c, 1.8f, FL, FL + 2.6f, true) else Op(c, w / nv - 0.5f, FL + 0.3f, FL + 3.3f, false))
        }
        val stoneC = C(rng.pick(arrayOf("#8C8F94", "#5F6368", "#B0A99F", "#3E4247", "#C9C2B6")))
        wall(g, 0, zf, x0, x1, FL, FL + gh, if (fz > 0) 1 else -1, fOps, stoneC, C("#F4F4F4"), Mt.STONE, 0.3f)
        wall(g, 0, zb, x0, x1, FL, FL + gh, if (fz > 0) -1 else 1, emptyList(), stoneC, C("#F4F4F4"), Mt.STONE, 0.3f)
        wall(g, 1, x0, z0 + 0.15f, z1 - 0.15f, FL, FL + gh, -1, emptyList(), stoneC, C("#F4F4F4"), Mt.STONE, 0.3f)
        wall(g, 1, x1, z0 + 0.15f, z1 - 0.15f, FL, FL + gh, 1, emptyList(), stoneC, C("#F4F4F4"), Mt.STONE, 0.3f)
        val door = fOps.first { it.door }
        g.solid(x0 - 0.2f, z0 - 0.2f, x0 + 0.25f, z1 + 0.2f); g.solid(x1 - 0.25f, z0 - 0.2f, x1 + 0.2f, z1 + 0.2f); g.solid(x0, zb - 0.25f, x1, zb + 0.25f)
        g.solid(x0, zf - 0.25f, door.c - 0.95f, zf + 0.25f); g.solid(door.c + 0.95f, zf - 0.25f, x1, zf + 0.25f)
        // interior do térreo
        interior(g, kind, x0 + 0.3f, z0 + 0.3f, x1 - 0.3f, z1 - 0.3f, zf, fz, door.c)
        // marquise, letreiro
        H.m(Mt.METAL, 1f)
        H.box(cx, FL + gh - 0.9f, Z(set - 1.0f), w - 0.4f, 0.14f, 2.0f, C("#4A4F55"))
        H.m(Mt.PLAIN)
        H.box(cx, FL + gh - 0.98f, Z(set - 1.0f), w - 0.6f, 0.02f, 1.8f, C("#FFF6D8"), false)
        if (shop != null) sign(H, cx, FL + gh - 0.7f, Z(set - 0.17f), 0f, fz, min(w - 2f, 9f), 0.85f, City.signIdx(shop))
        // andares
        H.m(Mt.STONE, 0.5f)
        H.box(cx, FL + gh + 0.1f, cz, w + 0.3f, 0.2f, d + 0.3f, shade(stoneC, 10))
        if (glassy) {   // pele de vidro com montantes
            H.m(Mt.METAL, 1f)
            H.box(cx, FL + gh + floors * 1.5f, cz, w, floors * 3f, d, col)
            H.m(Mt.PLAIN)
            var u = x0
            while (u <= x1 + 0.01f) { H.box(u, FL + gh + floors * 1.5f, zf + fz * 0.02f, 0.08f, floors * 3f, 0.06f, C("#C9CED3")); H.box(u, FL + gh + floors * 1.5f, zb - fz * 0.02f, 0.08f, floors * 3f, 0.06f, C("#C9CED3")); u += 1.5f }
            for (k in 1..floors) { H.box(cx, FL + gh + k * 3f, cz, w + 0.06f, 0.1f, d + 0.06f, C("#9AA3AB")) }
        } else {
            H.m(Mt.FACADE, 1f / 3f, 0f, -(FL + gh) / 3f)
            H.box(cx, FL + gh + floors * 1.5f, cz, w, floors * 3f, d, col)
            H.m(Mt.PLASTER, 0.5f)
            var f = 4
            while (f < floors) { H.box(cx, FL + gh + f * 3f, cz, w + 0.25f, 0.28f, d + 0.25f, shade(col, -22)); f += 4 }
        }
        H.m(Mt.PLASTER, 0.5f)
        H.box(cx, topY + 0.5f, z0 + 0.1f, w + 0.3f, 1.0f, 0.2f, shade(col, -28)); H.box(cx, topY + 0.5f, z1 - 0.1f, w + 0.3f, 1.0f, 0.2f, shade(col, -28))
        H.box(x0 + 0.1f, topY + 0.5f, cz, 0.2f, 1.0f, d + 0.3f, shade(col, -28)); H.box(x1 - 0.1f, topY + 0.5f, cz, 0.2f, 1.0f, d + 0.3f, shade(col, -28))
        H.m(Mt.STONE, 0.5f); H.box(cx, topY + 0.03f, cz, w - 0.2f, 0.06f, d - 0.2f, C("#9A9A9A"))
        if (balcony) {
            for (fl in 1 until floors) for (k in 0 until (w / 5.5f).toInt()) {
                val bx = x0 + 2.75f + k * 5.5f
                H.m(Mt.STONE, 0.5f); H.box(bx, FL + gh + fl * 3f + 0.05f, Z(set - 0.6f), 3.6f, 0.14f, 1.2f, C("#EDEDED"))
                H.m(Mt.GLASS); H.al = 0.45f; H.box(bx, FL + gh + fl * 3f + 0.6f, Z(set - 1.18f), 3.6f, 0.95f, 0.03f, C("#A8C7D8")); H.al = 1f
                H.m(Mt.METAL, 1f); H.box(bx, FL + gh + fl * 3f + 1.1f, Z(set - 1.18f), 3.6f, 0.04f, 0.05f, C("#9E9E9E"))
                if (rng.chance(0.3f)) { H.m(Mt.PLAIN); H.cyl(bx - 1.3f, FL + gh + fl * 3f + 0.12f, Z(set - 0.6f), 0.18f, 0.2f, 0.4f, C("#B5643C"), true, 8); CityGeo.ball(H, bx - 1.3f, FL + gh + fl * 3f + 0.75f, Z(set - 0.6f), 0.3f, C("#3E8E41"), 0.35f, 7) }
            }
        }
        // teto
        H.m(Mt.METAL, 1f)
        for (k in 0 until 3) H.box(cx + rng.r(-w / 3, w / 3), topY + 0.5f, cz + rng.r(-d / 3, d / 3), 1.4f, 0.9f, 1.1f, C("#C8CCD0"))
        if (rng.chance(0.7f)) { H.box(x0 + 3f, topY + 1.6f, cz, 3.2f, 3.2f, 3.6f, C("#B0B6BC")); H.box(x0 + 3f, topY + 3.25f, cz, 3.4f, 0.1f, 3.8f, C("#8E959C")) }   // casa de máquinas
        if (rng.chance(0.5f)) H.cyl(x1 - 2.5f, topY, cz, 1.2f, 1.2f, 2.2f, C("#6F7A84"), true, 12)
        if (floors > 14) { H.cyl(cx, topY, cz, 0.06f, 0.03f, 9f, C("#777777"), true, 5); H.m(Mt.PLAIN); CityGeo.ball(H, cx, topY + 9f, cz, 0.18f, C("#FF3B30"), 0.18f, 6, false) }
        g.end()
        // longe
        g.f.m(Mt.STONE, 0.5f); g.f.box(cx, FL + gh / 2, cz, w, gh, d, stoneC)
        if (glassy) { g.f.m(Mt.METAL, 1f); g.f.box(cx, FL + gh + floors * 1.5f, cz, w, floors * 3f, d, col) }
        else { g.f.m(Mt.FACADE, 1f / 3f, 0f, -(FL + gh) / 3f); g.f.box(cx, FL + gh + floors * 1.5f, cz, w, floors * 3f, d, col) }
        g.f.m(Mt.PLASTER, 0.5f); g.f.box(cx, topY + 0.5f, cz, w + 0.3f, 1.0f, d + 0.3f, shade(col, -28))
        if (shop != null) g.place(City.Place(bd.name, cx, Z(set - 2f), placeColor(kind), bd.name.first()))
        return topY + 4f
    }

    private fun placeColor(kind: Int) = when (kind) { 1 -> 0xFF2E7D32.toInt(); 2 -> 0xFFEF6C00.toInt(); 3 -> 0xFFD62828.toInt(); 4 -> 0xFF6A1B9A.toInt(); 5 -> 0xFF1565C0.toInt(); else -> 0xFF546E7A.toInt() }

    /**
     * Interior do térreo. kind: 0 portaria/escritório, 1 mercado/farmácia (prateleiras), 2 café/restaurante (mesas),
     * 3 hospital (recepção e espera), 4 loja de roupa/eletrônicos (vitrines e araras), 5 academia, 6 banco.
     */
    fun interior(g: Gen, kind: Int, x0: Float, z0: Float, x1: Float, z1: Float, zf: Float, fz: Float, doorX: Float) {
        val A = g.A; val rng = g.rng
        val w = x1 - x0; val d = z1 - z0; val cx = (x0 + x1) / 2; val cz = (z0 + z1) / 2
        val back = if (fz > 0) z0 else z1          // parede do fundo
        val inF = -fz                                // de quem está na porta, para dentro
        // luminárias de teto (placas claras) — ficam em H (teto some quando entra)
        g.H.m(Mt.PLAIN)
        var lx = x0 + 2f
        while (lx < x1 - 1f) { g.H.box(lx, FL + 4.2f, cz, 1.2f, 0.04f, 0.3f, C("#FFFDF2"), false); lx += 3f }
        g.H.m(Mt.PLASTER, 0.5f); g.H.box(cx, FL + 4.35f, cz, w, 0.1f, d, C("#F4F4F4"))
        val counterZ = back - inF * 1.3f
        when (kind) {
            1 -> {   // prateleiras de mercado
                val rows = min(3, max(2, ((d - 4f) / 2.2f).toInt()))
                for (r in 0 until rows) {
                    val sz = zf + inF * (3.2f + r * 2.2f)
                    var x = x0 + 1.2f
                    while (x < x1 - 2.2f) {
                        val sw = 2.0f
                        shelf(A, x + sw / 2, sz, sw, rng)
                        g.solid(x, sz - 0.35f, x + sw, sz + 0.35f)
                        x += sw + 0.05f
                    }
                }
                // geladeiras de bebida no fundo
                for (k in 0 until max(1, (w / 1.6f).toInt() - 2)) drinkFridge(A, L(x0 + 1.2f + k * 1.4f, back - inF * 0.45f, 0f, -inF), rng)
                g.solid(x0, back - 0.9f, x1, back + 0.9f)
                checkout(A, L(doorX + 2.6f, zf + inF * 1.6f, -1f, 0f))
                g.solid(doorX + 2.0f, zf + inF * 0.8f - 0.6f, doorX + 3.2f, zf + inF * 2.4f + 0.6f)
            }
            2 -> {   // café / restaurante
                counter(A, L(cx, counterZ, 0f, -inF * -1f).let { L(cx, counterZ, 0f, -inF * -1f) }, min(w - 3f, 5f), C("#5D4037"), rng, true)
                g.solid(cx - min(w - 3f, 5f) / 2, counterZ - 0.5f, cx + min(w - 3f, 5f) / 2, counterZ + 0.5f)
                var x = x0 + 1.4f
                while (x < x1 - 1f) {
                    var zz = zf + inF * 1.8f
                    while ((zz - counterZ) * inF < -2.2f) {
                        cafeTable(A, x, zz, rng)
                        g.solid(x - 0.4f, zz - 0.4f, x + 0.4f, zz + 0.4f)
                        zz += inF * 2.2f
                    }
                    x += 2.4f
                }
            }
            3 -> {   // hospital: recepção, cadeiras de espera, macas
                counter(A, L(cx, counterZ, 0f, fz), min(w - 3f, 6f), C("#ECEFF1"), rng, false)
                g.solid(cx - 3f, counterZ - 0.5f, cx + 3f, counterZ + 0.5f)
                for (r in 0 until 3) for (k in 0 until 6) {
                    val x = x0 + 1.5f + k * 0.62f; val zz = zf + inF * (1.8f + r * 1.4f)
                    chair(A, L(x, zz, 0f, fz), C("#90A4AE"), C("#1E88E5"))
                }
                for (k in 0 until 2) { val x = x1 - 1.6f - k * 1.4f; stretcher(A, L(x, cz, 1f, 0f)) }
                plant(A, x0 + 0.6f, zf + inF * 0.8f, 1.1f, rng)
            }
            4 -> {   // loja: araras e vitrines
                for (k in 0 until max(1, (w / 3f).toInt())) { rack(A, L(x0 + 1.6f + k * 3f, cz, 0f, fz), rng); g.solid(x0 + 0.9f + k * 3f, cz - 0.4f, x0 + 2.3f + k * 3f, cz + 0.4f) }
                for (k in 0 until max(1, (w / 2.2f).toInt() - 1)) displayTable(A, x0 + 1.5f + k * 2.2f, zf + inF * 1.6f, rng)
                checkout(A, L(cx, counterZ, 0f, fz))
                g.solid(cx - 1f, counterZ - 0.5f, cx + 1f, counterZ + 0.5f)
                mirrorWall(A, x0 + 0.05f, cz)
            }
            5 -> {   // academia
                for (k in 0 until max(1, (w / 1.6f).toInt() - 1)) { treadmill(A, L(x0 + 1.2f + k * 1.5f, back - inF * 1.4f, 0f, fz)); g.solid(x0 + 0.8f + k * 1.5f, back - inF * 2.3f - 0.4f, x0 + 1.6f + k * 1.5f, back - inF * 0.5f + 0.4f) }
                for (k in 0 until 3) { weightBench(A, L(x0 + 2f + k * 3f, cz, 1f, 0f)) }
                dumbbells(A, L(x1 - 0.6f, cz, -1f, 0f))
                rug(A, x0 + 0.6f, cz - 2.5f, x1 - 0.6f, cz + 2.5f, C("#37474F"))
            }
            6 -> {   // banco
                counter(A, L(cx, counterZ, 0f, fz), min(w - 3f, 7f), C("#8D6E63"), rng, false)
                g.solid(cx - 3.5f, counterZ - 0.5f, cx + 3.5f, counterZ + 0.5f)
                for (k in 0 until 3) { atm(A, L(x0 + 0.5f, zf + inF * (1.5f + k * 1.2f), 1f, 0f)) }
                sofa(A, L(x1 - 1.5f, zf + inF * 2f, -1f, 0f), 2f, C("#455A64"))
            }
            else -> {   // portaria / escritório
                counter(A, L(cx, cz, 0f, fz), 2.8f, C("#3E2723"), rng, false)
                g.solid(cx - 1.5f, cz - 0.5f, cx + 1.5f, cz + 0.5f)
                sofa(A, L(x0 + 1.6f, zf + inF * 1.6f, 1f, 0f), 2.0f, C("#37474F"))
                plant(A, x0 + 0.6f, zf + inF * 0.6f, 1.2f, rng); plant(A, x1 - 0.6f, zf + inF * 0.6f, 1.2f, rng)
                // elevadores no fundo
                A.m(Mt.METAL, 1f)
                for (k in 0 until 2) {
                    val ex = cx - 1.2f + k * 2.4f
                    A.box(ex, FL + 1.1f, back - inF * 0.17f, 1.1f, 2.2f, 0.04f, C("#B8C0C8"))
                    A.box(ex, FL + 1.1f, back - inF * 0.18f, 0.02f, 2.2f, 0.04f, C("#7D868F"))
                    A.m(Mt.PLAIN); A.box(ex + 0.75f, FL + 1.2f, back - inF * 0.18f, 0.1f, 0.16f, 0.03f, C("#FFCC80"), false); A.m(Mt.METAL, 1f)
                }
                rug(A, cx - 2f, min(zf, cz) + 0.5f, cx + 2f, max(zf, cz) - 0.5f, C("#8D6E63"))
            }
        }
    }

    fun shelf(b: MB, x: Float, z: Float, w: Float, rng: City.Rng) {
        b.m(Mt.METAL, 1f)
        b.box(x, FL + 0.9f, z, w, 1.8f, 0.08f, C("#E0E0E0"))
        b.box(x, FL + 0.05f, z, w, 0.1f, 0.6f, C("#BDBDBD"))
        for (k in 0..3) b.box(x, FL + 0.25f + k * 0.45f, z, w, 0.025f, 0.6f, C("#EEEEEE"))
        b.m(Mt.PLAIN)
        val pal = arrayOf(C("#E53935"), C("#FDD835"), C("#43A047"), C("#1E88E5"), C("#FB8C00"), C("#8E24AA"), C("#FFFFFF"), C("#6D4C41"), C("#00ACC1"))
        for (k in 0..3) for (side in floatArrayOf(-1f, 1f)) {
            var px = x - w / 2 + 0.05f
            val c = rng.pick(pal)
            val ph = rng.r(0.18f, 0.32f); val pw = w - 0.1f
            while (px < x + w / 2 - pw) {
                b.box(px + pw / 2, FL + 0.27f + k * 0.45f + ph / 2, z + side * 0.17f, pw - 0.015f, ph, 0.22f, if (rng.chance(0.25f)) rng.pick(pal) else c)
                px += pw
            }
        }
    }

    fun drinkFridge(b: MB, l: L, rng: City.Rng) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 1.0f, 0f, 1.3f, 2.0f, 0.7f, C("#ECEFF1"))
        b.m(Mt.PLAIN)
        val pal = arrayOf(C("#D32F2F"), C("#388E3C"), C("#FBC02D"), C("#1976D2"), C("#F57C00"))
        for (k in 0 until 4) lb(b, l, 0f, FL + 0.35f + k * 0.42f, -0.2f, 1.15f, 0.28f, 0.1f, pal[k % pal.size], false)
        b.m(Mt.GLASS); b.al = 0.3f
        lb(b, l, 0f, FL + 1.0f, -0.36f, 1.24f, 1.9f, 0.02f, C("#DDF3FF"))
        b.al = 1f
    }

    fun checkout(b: MB, l: L) {
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, FL + 0.45f, 0f, 1.8f, 0.9f, 0.7f, C("#ECEFF1"))
        b.m(Mt.METAL, 1f)
        lb(b, l, -0.2f, FL + 0.91f, 0f, 1.4f, 0.02f, 0.5f, C("#424242"))
        lb(b, l, 0.6f, FL + 1.05f, 0.1f, 0.35f, 0.22f, 0.3f, C("#212121"))
        lb(b, l, 0.6f, FL + 1.25f, 0.15f, 0.3f, 0.22f, 0.03f, C("#263238"))
        b.m(Mt.PLAIN); lb(b, l, 0.6f, FL + 1.25f, 0.13f, 0.26f, 0.17f, 0.005f, C("#4FC3F7"), false)
    }

    fun counter(b: MB, l: L, w: Float, col: Int, rng: City.Rng, food: Boolean) {
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, FL + 0.5f, 0f, w, 1.0f, 0.7f, col)
        b.m(Mt.STONE, 1.5f)
        lb(b, l, 0f, FL + 1.02f, 0f, w + 0.1f, 0.05f, 0.8f, C("#E8E4DC"))
        if (food) {
            b.m(Mt.GLASS); b.al = 0.3f
            lb(b, l, -w * 0.2f, FL + 1.25f, -0.1f, w * 0.5f, 0.4f, 0.5f, C("#E0F7FA"))
            b.al = 1f
            b.m(Mt.PLAIN)
            for (k in 0 until 8) lsph(b, l, -w * 0.2f - w * 0.22f + k * w * 0.06f, FL + 1.12f, -0.1f, 0.07f, rng.pick(arrayOf(C("#D7A86E"), C("#8D5524"), C("#F3D19C"), C("#E57373"))), 0.05f, 6)
            b.m(Mt.METAL, 1f)
            lb(b, l, w * 0.3f, FL + 1.25f, 0.1f, 0.5f, 0.45f, 0.4f, C("#9E9E9E"))   // máquina de café
            lb(b, l, w * 0.3f, FL + 1.32f, -0.08f, 0.12f, 0.08f, 0.1f, C("#212121"))
        } else {
            b.m(Mt.METAL, 1f)
            lb(b, l, -w * 0.2f, FL + 1.25f, 0.1f, 0.5f, 0.4f, 0.04f, C("#212121"))
            lb(b, l, w * 0.2f, FL + 1.25f, 0.1f, 0.5f, 0.4f, 0.04f, C("#212121"))
        }
    }

    fun cafeTable(b: MB, x: Float, z: Float, rng: City.Rng) {
        b.m(Mt.METAL, 1f)
        b.cyl(x, FL, z, 0.25f, 0.25f, 0.03f, C("#2B2B2B"), true, 12)
        b.cyl(x, FL, z, 0.04f, 0.04f, 0.74f, C("#2B2B2B"), true, 6)
        b.m(Mt.WOOD, 1f)
        b.cyl(x, FL + 0.74f, z, 0.42f, 0.42f, 0.04f, rng.pick(WOODS), true, 16)
        val wd = rng.pick(WOODS); val fb = rng.pick(FABRICS)
        chair(b, L(x, z - 0.7f, 0f, 1f), wd, fb); chair(b, L(x, z + 0.7f, 0f, -1f), wd, fb)
        b.m(Mt.PLAIN)
        b.cyl(x + 0.12f, FL + 0.78f, z, 0.05f, 0.04f, 0.09f, C("#FFFFFF"), true, 8)
    }

    fun stretcher(b: MB, l: L) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.7f, 0f, 0.7f, 0.08f, 2.0f, C("#B0BEC5"))
        for (s in floatArrayOf(-0.3f, 0.3f)) for (t in floatArrayOf(-0.9f, 0.9f)) lb(b, l, s, FL + 0.35f, t, 0.04f, 0.7f, 0.04f, C("#90A4AE"))
        b.m(Mt.FABRIC, 1f)
        lb(b, l, 0f, FL + 0.8f, 0f, 0.66f, 0.1f, 1.9f, C("#E3F2FD"))
        lb(b, l, 0f, FL + 0.88f, 0.75f, 0.5f, 0.08f, 0.3f, C("#FFFFFF"))
    }

    fun rack(b: MB, l: L, rng: City.Rng) {
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-0.65f, 0.65f)) lb(b, l, s, FL + 0.8f, 0f, 0.04f, 1.6f, 0.04f, C("#9E9E9E"))
        lb(b, l, 0f, FL + 1.55f, 0f, 1.35f, 0.04f, 0.04f, C("#9E9E9E"))
        b.m(Mt.FABRIC, 1f)
        val c = rng.pick(FABRICS)
        for (k in 0 until 9) lb(b, l, -0.56f + k * 0.14f, FL + 1.15f, 0f, 0.04f, 0.7f, 0.45f, if (k % 3 == 0) shade(c, 30) else c)
    }

    fun displayTable(b: MB, x: Float, z: Float, rng: City.Rng) {
        b.m(Mt.WOOD, 1f)
        b.box(x, FL + 0.4f, z, 1.4f, 0.8f, 0.8f, C("#F5F5F5"))
        b.m(Mt.FABRIC, 1f)
        for (k in 0 until 3) b.box(x - 0.4f + k * 0.4f, FL + 0.84f, z, 0.32f, 0.08f, 0.5f, rng.pick(FABRICS))
    }

    fun mirrorWall(b: MB, x: Float, z: Float) {
        b.m(Mt.METAL, 1f)
        b.box(x, FL + 1.3f, z, 0.03f, 2.0f, 1.2f, C("#DCEFF5"))
    }

    fun treadmill(b: MB, l: L) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.12f, 0f, 0.8f, 0.24f, 1.8f, C("#263238"))
        lb(b, l, 0f, FL + 0.25f, 0f, 0.55f, 0.02f, 1.6f, C("#111111"))
        for (s in floatArrayOf(-0.35f, 0.35f)) lb(b, l, s, FL + 0.75f, 0.8f, 0.05f, 1.1f, 0.05f, C("#546E7A"))
        lb(b, l, 0f, FL + 1.3f, 0.82f, 0.7f, 0.3f, 0.08f, C("#37474F"))
        b.m(Mt.PLAIN); lb(b, l, 0f, FL + 1.32f, 0.775f, 0.4f, 0.18f, 0.01f, C("#4DD0E1"), false)
    }

    fun weightBench(b: MB, l: L) {
        b.m(Mt.FABRIC, 1f); lb(b, l, 0f, FL + 0.45f, 0f, 0.35f, 0.08f, 1.3f, C("#B71C1C"))
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.22f, 0.5f, 0.06f, 0.44f, 0.06f, C("#424242")); lb(b, l, 0f, FL + 0.22f, -0.5f, 0.06f, 0.44f, 0.06f, C("#424242"))
        for (s in floatArrayOf(-0.5f, 0.5f)) lb(b, l, s, FL + 0.6f, 0.55f, 0.05f, 1.0f, 0.05f, C("#616161"))
        lb(b, l, 0f, FL + 1.05f, 0.55f, 1.7f, 0.04f, 0.04f, C("#9E9E9E"))
        for (s in floatArrayOf(-0.75f, 0.75f)) lcyl(b, l, s, FL + 0.85f, 0.55f, 0.22f, 0.22f, 0.4f, C("#212121"), 12)
    }

    fun dumbbells(b: MB, l: L) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.4f, 0f, 2.4f, 0.06f, 0.5f, C("#424242"))
        lb(b, l, 0f, FL + 0.75f, 0f, 2.4f, 0.06f, 0.5f, C("#424242"))
        for (k in 0 until 8) for (y in floatArrayOf(0.48f, 0.83f)) lb(b, l, -1.05f + k * 0.3f, FL + y, 0f, 0.1f, 0.1f, 0.36f, C("#1A1A1A"))
    }

    fun atm(b: MB, l: L) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.8f, 0f, 0.7f, 1.6f, 0.6f, C("#455A64"))
        lb(b, l, 0f, FL + 1.25f, -0.31f, 0.4f, 0.3f, 0.02f, C("#263238"))
        b.m(Mt.PLAIN); lb(b, l, 0f, FL + 1.25f, -0.325f, 0.36f, 0.26f, 0.005f, C("#81D4FA"), false)
        lb(b, l, 0f, FL + 0.95f, -0.33f, 0.3f, 0.1f, 0.06f, C("#9E9E9E"))
    }

    // ============================================================ lojas térreas

    /** Fileira de lojas térreas/sobrados com toldo listrado e letreiro, cada uma com interior. */
    fun shopRow(g: Gen, xa: Float, xb: Float, fz0: Float, fz: Float, signs: List<Pair<String, Int>>, depth: Float) {
        val rng = g.rng
        val n = signs.size; val sw = (xb - xa) / n
        fun Z(d: Float) = fz0 - fz * d
        for (k in 0 until n) {
            val x0 = xa + sw * k + 0.1f; val x1 = x0 + sw - 0.2f; val cx = (x0 + x1) / 2
            val col = C(rng.pick(WALLS)); val two = rng.chance(0.55f)
            val zf = Z(1.5f); val zb = Z(1.5f + depth); val z0 = min(zf, zb); val z1 = max(zf, zb)
            val (signName, kind) = signs[k]
            val bd = g.begin(x0, z0, x1, z1, signName.lowercase().replaceFirstChar { it.uppercase() })
            val A = g.A; val H = g.H
            A.m(Mt.STONE, 0.6f); A.box(cx, FL / 2, (z0 + z1) / 2, x1 - x0, FL, depth, C("#A8A39B"))
            A.m(rng.pick(arrayOf(Mt.TILE, Mt.FLOOR_L, Mt.FLOOR_D)), 0.6f); A.box(cx, FL - 0.005f, (z0 + z1) / 2, x1 - x0 - 0.3f, 0.012f, depth - 0.3f, C("#FFFFFF"))
            val hh = 4.4f
            val ops = listOf(Op(cx + sw * 0.28f, 1.3f, FL, FL + 2.5f, true), Op(cx - sw * 0.12f, sw * 0.5f, FL + 0.4f, FL + 3.0f, false))
            wall(g, 0, zf, x0, x1, FL, FL + hh, if (fz > 0) 1 else -1, ops, col, C("#F7F3EC"), Mt.PLASTER, 0.24f)
            wall(g, 0, zb, x0, x1, FL, FL + hh, if (fz > 0) -1 else 1, emptyList(), col, C("#F7F3EC"), Mt.PLASTER, 0.24f)
            wall(g, 1, x0, z0 + 0.12f, z1 - 0.12f, FL, FL + hh, -1, emptyList(), col, C("#F7F3EC"), Mt.PLASTER, 0.24f)
            wall(g, 1, x1, z0 + 0.12f, z1 - 0.12f, FL, FL + hh, 1, emptyList(), col, C("#F7F3EC"), Mt.PLASTER, 0.24f)
            g.solid(x0 - 0.15f, z0 - 0.15f, x0 + 0.2f, z1 + 0.15f); g.solid(x1 - 0.2f, z0 - 0.15f, x1 + 0.15f, z1 + 0.15f); g.solid(x0, zb - 0.2f, x1, zb + 0.2f)
            g.solid(x0, zf - 0.2f, cx + sw * 0.28f - 0.7f, zf + 0.2f); g.solid(cx + sw * 0.28f + 0.7f, zf - 0.2f, x1, zf + 0.2f)
            interior(g, kind, x0 + 0.25f, z0 + 0.25f, x1 - 0.25f, z1 - 0.25f, zf, fz, cx + sw * 0.28f)
            // platibanda, toldo, letreiro, andar de cima
            H.m(Mt.STONE, 0.5f)
            H.box(cx, FL + hh + 0.3f, (z0 + z1) / 2, x1 - x0 + 0.1f, 0.6f, depth + 0.1f, shade(col, -28))
            val ac = C(rng.pick(arrayOf("#D7263D", "#1B98E0", "#2A9D8F", "#F4A261", "#6A4C93", "#2E7D32", "#795548")))
            val stripes = 10
            for (s in 0 until stripes) {
                val a0 = x0 + 0.3f + (x1 - x0 - 0.6f) * s / stripes; val a1 = a0 + (x1 - x0 - 0.6f) / stripes
                H.m(Mt.FABRIC, 1f)
                q(H, P(a0, FL + 3.25f, Z(1.42f)) + P(a1, FL + 3.25f, Z(1.42f)) + P(a1, FL + 2.7f, Z(0.2f)) + P(a0, FL + 2.7f, Z(0.2f)), if (s % 2 == 0) ac else C("#FFFFFF"))
                q(H, P(a0, FL + 2.7f, Z(0.2f)) + P(a1, FL + 2.7f, Z(0.2f)) + P(a1, FL + 2.5f, Z(0.18f)) + P(a0, FL + 2.5f, Z(0.18f)), if (s % 2 == 0) ac else C("#FFFFFF"))
            }
            sign(H, cx, FL + 3.45f, Z(1.4f) + fz * 0.03f, 0f, fz, min(x1 - x0 - 1.2f, 6.5f), 0.75f, City.signIdx(signName))
            if (two) {
                val y2 = FL + hh + 0.6f
                H.m(Mt.PLASTER, 0.5f); H.box(cx, y2 + 1.5f, (z0 + z1) / 2, x1 - x0, 3.0f, depth, col)
                for (s in floatArrayOf(-1f, 1f)) {
                    H.m(Mt.PLAIN); H.box(cx + s * sw * 0.22f, y2 + 1.5f, zf + fz * 0.03f, 1.4f, 1.5f, 0.06f, C("#FFFFFF"))
                    H.m(Mt.METAL, 1f); H.box(cx + s * sw * 0.22f, y2 + 1.5f, zf + fz * 0.05f, 1.25f, 1.35f, 0.02f, C("#5D7A93"))
                    H.m(Mt.WOOD, 1f); H.box(cx + s * sw * 0.22f - 0.85f, y2 + 1.5f, zf + fz * 0.06f, 0.3f, 1.5f, 0.04f, C("#2E7D32")); H.box(cx + s * sw * 0.22f + 0.85f, y2 + 1.5f, zf + fz * 0.06f, 0.3f, 1.5f, 0.04f, C("#2E7D32"))
                }
                H.m(Mt.ROOF, 0.6f); H.box(cx, y2 + 3.1f, (z0 + z1) / 2, x1 - x0 + 0.3f, 0.2f, depth + 0.3f, C("#8E4B3A"))
                H.m(Mt.METAL, 1f); H.box(cx + sw * 0.3f, y2 + 1.2f, zb + fz * 0.0f - fz * 0.05f, 0.9f, 0.6f, 0.5f, C("#ECEFF1"))   // ar-condicionado
            }
            g.end()
            g.place(City.Place(bd.name, cx, Z(0.8f), placeColor(kind), bd.name.first()))
            // mesinhas na calçada do café/lanchonete/sorveteria
            if (kind == 2) {
                for (t in 0 until 2) {
                    val tx = cx - 1.6f + t * 3.2f
                    cafeTableOut(g.b, tx, Z(0.6f), ac)
                }
            }
            // longe
            g.f.m(Mt.PLASTER, 0.5f); g.f.box(cx, (FL + hh + (if (two) 3.6f else 0.6f)) / 2, (z0 + z1) / 2, x1 - x0, FL + hh + (if (two) 3.6f else 0.6f), depth, col)
            g.f.m(Mt.FABRIC, 1f); g.f.box(cx, FL + 3.0f, Z(0.8f), x1 - x0 - 0.6f, 0.4f, 1.2f, ac)
        }
    }

    fun cafeTableOut(b: MB, x: Float, z: Float, ac: Int) {
        b.m(Mt.METAL, 1f)
        b.cyl(x, CURB, z, 0.04f, 0.04f, 0.74f, C("#333333"), true, 6)
        b.cyl(x, CURB + 0.74f, z, 0.4f, 0.4f, 0.03f, C("#F5F5F5"), true, 14)
        b.m(Mt.FABRIC, 1f)
        b.cyl(x, CURB + 2.0f, z, 1.25f, 0.02f, 0.45f, ac, true, 12)
        b.m(Mt.METAL, 1f)
        b.cyl(x, CURB + 0.75f, z, 0.025f, 0.025f, 1.3f, C("#888888"), true, 5)
        for (s in floatArrayOf(-0.6f, 0.6f)) chairOut(b, x + s, z)
    }

    private fun chairOut(b: MB, x: Float, z: Float) {
        b.m(Mt.METAL, 1f)
        b.box(x, CURB + 0.45f, z, 0.42f, 0.04f, 0.42f, C("#E0E0E0"))
        b.box(x, CURB + 0.22f, z, 0.36f, 0.44f, 0.36f, C("#BDBDBD"))
    }

    // ============================================================ quarteirões

    fun block(g: Gen, t: String, i: Int, j: Int): Float {
        val x0 = g.x0; val z0 = g.z0; val x1 = g.x1; val z1 = g.z1
        val rng = g.rng
        return when (t) {
            "res" -> { lawn(g); residential(g, false); 11f }
            "lots" -> { lawn(g); residential(g, true); 11f }
            "mansion" -> { lawn(g); mansions(g); 13f }
            "apt" -> { lawn(g); apartments(g) }
            "down" -> { plaza(g); downtown(g, false) }
            "hotel" -> { plaza(g); downtown(g, true) }
            "shops" -> { plaza(g); shops(g, j) }
            "mall" -> { plaza(g); mall(g) }
            "super" -> { plaza(g); supermarket(g) }
            "gas" -> { plaza(g); gasStation(g) }
            "hospital" -> { plaza(g); hospital(g) }
            "school" -> { lawn(g); school(g) }
            "police" -> { plaza(g); police(g) }
            "church" -> { lawn(g); church(g) }
            "praca" -> { lawn(g); praca(g) }
            "park" -> { lawn(g); park(g) }
            "fun" -> { CityFun.park(g); 30f }
            else -> { lawn(g); 1f }
        }
    }

    private fun lawn(g: Gen) { groundBox(g.b, g.x0, g.z0, g.x1, g.z1, Mt.GRASS, 0.3f, C("#D6EEC4")); groundBox(g.f, g.x0, g.z0, g.x1, g.z1, Mt.GRASS, 0.3f, C("#D6EEC4")) }
    private fun plaza(g: Gen) { groundBox(g.b, g.x0, g.z0, g.x1, g.z1, Mt.PAVER, 0.7f, C("#E2DDD3")); groundBox(g.f, g.x0, g.z0, g.x1, g.z1, Mt.PAVER, 0.7f, C("#E2DDD3")) }

    private fun residential(g: Gen, lots: Boolean) {
        val rng = g.rng
        val depth = (g.z1 - g.z0) / 2
        // estilo predominante do bairro + variações (nenhuma casa igual: cores, tamanhos, móveis e detalhes sorteados)
        val main = rng.i(5)
        for (side in intArrayOf(0, 1)) {
            var x = g.x0
            while (x < g.x1 - 9f) {
                val lw = min(g.x1 - x, rng.r(12.5f, 15.5f)).let { if (g.x1 - x - it < 11f) g.x1 - x else it }
                val fz0 = if (side == 0) g.z1 else g.z0
                val fz = if (side == 0) 1f else -1f
                val empty = if (lots) rng.chance(0.6f) else rng.chance(0.08f)
                if (empty) emptyLot(g, x, x + lw, fz0, fz, depth)
                else house(g, x, x + lw, fz0, fz, depth, if (rng.chance(0.6f)) main else rng.i(5), rng.chance(0.18f))
                // muro de fundo e divisa
                g.b.m(Mt.STONE, 0.8f)
                g.b.box(x + lw, CURB + 0.9f, (g.z0 + g.z1) / 2 - fz * depth / 2, 0.15f, 1.8f, depth - 1.5f, C("#D9D2C5"))
                g.solid(x + lw - 0.15f, min(fz0, fz0 - fz * depth) + 1f, x + lw + 0.15f, max(fz0, fz0 - fz * depth) - 0.5f)
                x += lw
            }
        }
        g.b.m(Mt.STONE, 0.8f)
        g.b.box((g.x0 + g.x1) / 2, CURB + 0.9f, (g.z0 + g.z1) / 2, g.x1 - g.x0, 1.8f, 0.15f, C("#D9D2C5"))
        g.solid(g.x0, (g.z0 + g.z1) / 2 - 0.15f, g.x1, (g.z0 + g.z1) / 2 + 0.15f)
    }

    private fun mansions(g: Gen) {
        val rng = g.rng
        val depth = (g.z1 - g.z0) / 2
        val n = if (g.x1 - g.x0 > 50f) 2 else 1
        val w = (g.x1 - g.x0) / n
        for (side in intArrayOf(0, 1)) for (k in 0 until n) {
            val fz0 = if (side == 0) g.z1 else g.z0
            val fz = if (side == 0) 1f else -1f
            house(g, g.x0 + w * k, g.x0 + w * (k + 1), fz0, fz, depth, 2, rng.chance(0.3f), true)
        }
        g.b.m(Mt.STONE, 0.8f)
        g.b.box((g.x0 + g.x1) / 2, CURB + 1.1f, (g.z0 + g.z1) / 2, g.x1 - g.x0, 2.2f, 0.25f, C("#E8E0D2"))
        g.solid(g.x0, (g.z0 + g.z1) / 2 - 0.2f, g.x1, (g.z0 + g.z1) / 2 + 0.2f)
        g.place(City.Place("Mansões", (g.x0 + g.x1) / 2, (g.z0 + g.z1) / 2, 0xFFB8860B.toInt(), 'M'))
    }

    private val TOWER_C = arrayOf(C("#F0F0F0"), C("#DDE6EE"), C("#EFE3D3"), C("#C9D6DF"), C("#E6E1EA"), C("#D8D2C4"), C("#F3E5D0"), C("#E0EBE4"))
    private val GLASS_C = arrayOf(C("#4F7C99"), C("#3E6A86"), C("#5E8C7E"), C("#6B7F99"), C("#2F4F6F"))

    private fun apartments(g: Gen): Float {
        val rng = g.rng
        var h = 0f
        val w = g.x1 - g.x0 - 8f
        h = max(h, tower(g, g.x0 + 4f, g.x0 + 4f + w, g.z1, 1f, 4f, 13f, rng.i(5) + 5, rng.pick(TOWER_C), "RESIDENCIAL", 0, true))
        h = max(h, tower(g, g.x0 + 4f, g.x0 + 4f + w, g.z0, -1f, 4f, 13f, rng.i(5) + 5, rng.pick(TOWER_C), "CONDOMÍNIO", 0, true))
        g.b.m(Mt.ASPHALT, 0.3f)
        g.b.box((g.x0 + g.x1) / 2, CURB + 0.01f, (g.z0 + g.z1) / 2, g.x1 - g.x0 - 6f, 0.02f, (g.z1 - g.z0) - 36f, C("#D0D0D0"))
        var x = g.x0 + 6f
        while (x < g.x1 - 6f) { if (rng.chance(0.7f)) Vehicles.parked(g, x, (g.z0 + g.z1) / 2 + (if (rng.chance(0.5f)) -2.8f else 2.8f), 1, CURB + 0.02f, rng); x += 3.2f }
        for (k in 0 until 6) tree(g, g.x0 + 2.2f, g.z0 + 6f + k * 7f, 1f)
        for (k in 0 until 6) tree(g, g.x1 - 2.2f, g.z0 + 6f + k * 7f, 1f)
        return h
    }

    private fun downtown(g: Gen, hotel: Boolean): Float {
        val rng = g.rng
        var hMax = 0f
        val shopsA = arrayOf("BANCO" to 6, "CAFÉ" to 2, "LIVRARIA" to 4, "ELETRÔNICOS" to 4, "MODA" to 4, "ÓTICA" to 4, "RESTAURANTE" to 2, "ACADEMIA" to 5, "SUSHI" to 2, "CASA DE CÂMBIO" to 6, "ESCRITÓRIOS" to 0, "CLÍNICA" to 3)
        val w = (g.x1 - g.x0) / 2f - 2.5f
        for (k in 0 until 2) {
            val xa = g.x0 + 1.5f + k * (w + 2f)
            val s1 = if (hotel && k == 0) "HOTEL" to 0 else rng.pick(shopsA)
            val s2 = rng.pick(shopsA)
            val f1 = if (hotel && k == 0) 24 else rng.i(14) + 9
            hMax = max(hMax, tower(g, xa, xa + w, g.z1, 1f, 2f, 18f, f1, if (rng.chance(0.45f)) rng.pick(GLASS_C) else rng.pick(TOWER_C), s1.first, s1.second, rng.chance(0.3f), rng.chance(0.45f)))
            hMax = max(hMax, tower(g, xa, xa + w, g.z0, -1f, 2f, 18f, rng.i(16) + 7, if (rng.chance(0.45f)) rng.pick(GLASS_C) else rng.pick(TOWER_C), s2.first, s2.second, rng.chance(0.3f), rng.chance(0.45f)))
        }
        val cz = (g.z0 + g.z1) / 2
        for (k in 0 until 5) tree(g, g.x0 + 5f + k * (g.x1 - g.x0 - 10f) / 4f, cz, 1.0f)
        for (k in 0 until 4) { val bx = g.x0 + 9f + k * (g.x1 - g.x0 - 18f) / 3f; publicBench(g.b, bx, cz + 1.6f, 0f, 1f); publicBench(g.b, bx, cz - 1.6f, 0f, -1f) }
        return hMax
    }

    fun publicBench(b: MB, x: Float, z: Float, fx: Float, fz: Float) {
        val l = L(x, z, fx, fz)
        b.m(Mt.WOOD, 1f)
        for (k in 0 until 3) lb(b, l, 0f, CURB + 0.45f, -0.15f + k * 0.15f, 1.7f, 0.04f, 0.12f, C("#9C6B3F"))
        for (k in 0 until 2) lb(b, l, 0f, CURB + 0.65f + k * 0.15f, 0.28f, 1.7f, 0.1f, 0.03f, C("#9C6B3F"))
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-0.75f, 0.75f)) { lb(b, l, s, CURB + 0.22f, 0f, 0.06f, 0.44f, 0.5f, C("#2E2E2E")); lb(b, l, s, CURB + 0.6f, 0.28f, 0.06f, 0.5f, 0.06f, C("#2E2E2E")) }
    }

    private fun shops(g: Gen, j: Int): Float {
        val rng = g.rng
        val all = mutableListOf("PADARIA" to 2, "FARMÁCIA" to 1, "CAFÉ" to 2, "PET SHOP" to 4, "SALÃO DE BELEZA" to 4, "PIZZARIA" to 2, "FLORICULTURA" to 4, "SORVETERIA" to 2, "ACADEMIA" to 5,
            "LANCHONETE" to 2, "ÓTICA" to 4, "MODA" to 4, "HAMBÚRGUER" to 2, "BARBEARIA" to 4, "PAPELARIA" to 4, "AÇAÍ" to 2, "MERCADINHO" to 1, "SUSHI" to 2, "ELETRÔNICOS" to 4, "LIVRARIA" to 4)
        // embaralha (cada quarteirão tem um conjunto diferente)
        for (k in all.indices.reversed()) { val r = rng.i(k + 1); val t = all[k]; all[k] = all[r]; all[r] = t }
        val n = if (g.x1 - g.x0 > 50f) 5 else 4
        shopRow(g, g.x0 + 1f, g.x1 - 1f, g.z0, -1f, all.subList(0, n), 10f)
        shopRow(g, g.x0 + 1f, g.x1 - 1f, g.z1, 1f, all.subList(n, n * 2), 10f)
        // estacionamento no meio
        val cz = (g.z0 + g.z1) / 2
        g.b.m(Mt.ASPHALT, 0.3f)
        g.b.box((g.x0 + g.x1) / 2, CURB + 0.01f, cz, g.x1 - g.x0 - 4f, 0.02f, (g.z1 - g.z0) - 26f, C("#D0D0D0"))
        g.b.m(Mt.PLAIN)
        var x = g.x0 + 4f
        while (x < g.x1 - 4f) { g.b.box(x, CURB + 0.025f, cz, 0.12f, 0.02f, 5f, C("#F4F4F4")); if (rng.chance(0.6f) && x + 3.3f < g.x1 - 4f) Vehicles.parked(g, x + 1.6f, cz, 1, CURB + 0.02f, rng); x += 3.2f }
        return 11f
    }

    private fun mall(g: Gen): Float {
        val rng = g.rng
        val x0 = g.x0 + 3f; val x1 = g.x1 - 3f; val zf = g.z0 + 8f; val zb = g.z1 - 4f
        val h = tower(g, x0, x1, g.z0, -1f, 8f, zb - zf, 3, C("#F5F0E6"), "SHOPPING", 4, false, false)
        // letreiro do cinema e estacionamento na frente
        sign(g.b, (x0 + x1) / 2 + 12f, FL + 11f, zf - 0.2f, 0f, -1f, 6f, 1.2f, City.signIdx("CINEMA"))
        g.b.m(Mt.ASPHALT, 0.3f); g.b.box((g.x0 + g.x1) / 2, CURB + 0.01f, g.z0 + 4f, g.x1 - g.x0 - 4f, 0.02f, 6f, C("#D0D0D0"))
        for (k in 0 until 6) tree(g, g.x0 + 4f + k * (g.x1 - g.x0 - 8f) / 5f, g.z0 + 1.5f, 0.9f)
        return h
    }

    private fun supermarket(g: Gen): Float {
        val rng = g.rng
        shopRow(g, g.x0 + 1f, g.x1 - 1f, g.z0, -1f, listOf("LANCHONETE" to 2, "BANCO" to 6, "ÓTICA" to 4, "MODA" to 4), 9f)
        val h = tower(g, g.x0 + 3f, g.x1 - 3f, g.z1, 1f, 16f, 13f, 1, C("#F6F2EA"), "SUPERMERCADO", 1)
        g.b.m(Mt.ASPHALT, 0.3f)
        g.b.box((g.x0 + g.x1) / 2, CURB + 0.01f, g.z1 - 8.5f, g.x1 - g.x0 - 2f, 0.02f, 15f, C("#D0D0D0"))
        g.b.m(Mt.PLAIN)
        var x = g.x0 + 3f
        while (x < g.x1 - 3f) { g.b.box(x, CURB + 0.025f, g.z1 - 5f, 0.12f, 0.02f, 5f, C("#F4F4F4")); g.b.box(x, CURB + 0.025f, g.z1 - 12f, 0.12f, 0.02f, 5f, C("#F4F4F4")); x += 3.2f }
        x = g.x0 + 4.6f
        while (x < g.x1 - 4f) { if (rng.chance(0.5f)) Vehicles.parked(g, x, if (rng.chance(0.5f)) g.z1 - 5f else g.z1 - 12f, 1, CURB + 0.02f, rng); x += 3.2f }
        return h
    }

    private fun gasStation(g: Gen): Float {
        val b = g.b; val rng = g.rng
        val cx = (g.x0 + g.x1) / 2
        fun Z(d: Float) = g.z0 + d
        b.m(Mt.ASPHALT, 0.3f); b.box(cx, CURB + 0.01f, Z(9f), g.x1 - g.x0 - 4f, 0.02f, 16f, C("#D6D6D6"))
        b.m(Mt.METAL, 1f); b.box(cx, CURB + 5.3f, Z(9f), 20f, 0.7f, 11f, C("#F5F5F5"))
        b.m(Mt.PLAIN)
        b.box(cx, CURB + 5.3f, Z(3.45f), 20.05f, 0.5f, 0.06f, C("#0F7A3D")); b.box(cx, CURB + 5.3f, Z(14.55f), 20.05f, 0.5f, 0.06f, C("#0F7A3D"))
        b.box(cx, CURB + 4.93f, Z(9f), 19f, 0.02f, 10f, C("#FFFDF0"), false)
        for (k in 0 until 3) {
            val px = cx - 6f + k * 6f
            b.m(Mt.METAL, 1f)
            b.box(px, CURB + 2.6f, Z(9f), 0.3f, 5f, 0.3f, C("#DADADA"))
            b.box(px, CURB + 0.1f, Z(9f), 1.4f, 0.2f, 4.4f, C("#BDBDBD"))
            for (s in floatArrayOf(-1.3f, 1.3f)) {
                b.box(px, CURB + 0.85f, Z(9f + s), 0.7f, 1.7f, 0.5f, C("#0F7A3D"))
                b.box(px, CURB + 1.3f, Z(9f + s) - 0.26f * (if (s < 0) 1f else -1f), 0.45f, 0.35f, 0.02f, C("#1A1A1A"))
                b.m(Mt.PLAIN); b.box(px, CURB + 1.33f, Z(9f + s) - 0.275f * (if (s < 0) 1f else -1f), 0.38f, 0.12f, 0.005f, C("#7CFC9A"), false); b.m(Mt.METAL, 1f)
                b.box(px + 0.42f, CURB + 0.95f, Z(9f + s), 0.06f, 0.5f, 0.06f, C("#212121"))
                g.solid(px - 0.5f, Z(9f + s) - 0.35f, px + 0.5f, Z(9f + s) + 0.35f)
            }
        }
        sign(b, cx, CURB + 5.1f, Z(3.4f), 0f, -1f, 5f, 0.45f, City.signIdx("POSTO"))
        b.m(Mt.METAL, 1f)
        b.box(g.x1 - 4f, CURB + 2.5f, Z(1.2f), 0.4f, 5f, 0.4f, C("#777777"))
        b.box(g.x1 - 4f, CURB + 5.6f, Z(1.2f), 2.2f, 2.6f, 0.4f, C("#0F7A3D"))
        sign(b, g.x1 - 4f, CURB + 6.3f, Z(1.2f) - 0.22f, 0f, -1f, 2f, 0.3f, City.signIdx("POSTO"))
        b.m(Mt.PLAIN)
        for (k in 0 until 3) { b.box(g.x1 - 4f, CURB + 5.0f + k * 0.4f, Z(1.2f) - 0.22f, 1.8f, 0.3f, 0.01f, C("#111111")); b.box(g.x1 - 3.5f, CURB + 5.0f + k * 0.4f, Z(1.2f) - 0.23f, 0.7f, 0.22f, 0.005f, C("#FF5252"), false) }
        tower(g, cx - 7f, cx + 7f, g.z0, -1f, 19f, 8f, 0, C("#FFFFFF"), "CONVENIÊNCIA", 1)
        shopRow(g, g.x0 + 1f, g.x1 - 1f, g.z1, 1f, listOf("LANCHONETE" to 2, "ELETRÔNICOS" to 4, "PET SHOP" to 4), 10f)
        for (k in 0 until 2) Vehicles.parked(g, cx - 3f + k * 6f, Z(7.6f), 1, CURB + 0.02f, rng)
        return 9f
    }

    private fun hospital(g: Gen): Float {
        val rng = g.rng
        val w = g.x1 - g.x0 - 8f
        val h = tower(g, g.x0 + 4f, g.x0 + 4f + w, g.z0, -1f, 12f, 22f, 7, C("#F7F9FB"), "HOSPITAL", 3, false, false)
        // pronto-socorro na frente
        val b = g.b
        val pcx = g.x0 + 4f + w * 0.25f
        tower(g, pcx - w * 0.22f, pcx + w * 0.22f, g.z0, -1f, 2.5f, 9f, 0, C("#FFFFFF"), "PRONTO-SOCORRO", 3)
        b.m(Mt.METAL, 1f)
        val acx = g.x0 + 4f + w * 0.72f
        b.box(acx, CURB + 3.6f, g.z0 + 4.5f, 10f, 0.25f, 7f, C("#E8ECEF"))
        for (s in floatArrayOf(-4.6f, 4.6f)) b.box(acx + s, CURB + 1.8f, g.z0 + 1.4f, 0.25f, 3.6f, 0.25f, C("#C8CCD0"))
        b.m(Mt.PLAIN)
        val crossY = FL + 4.4f + 7 * 3f - 3.5f
        b.box(g.x0 + 4f + w * 0.72f, crossY, g.z0 + 11.85f, 3.2f, 1.0f, 0.12f, C("#D62828"), false)
        b.box(g.x0 + 4f + w * 0.72f, crossY, g.z0 + 11.85f, 1.0f, 3.2f, 0.12f, C("#D62828"), false)
        // heliponto
        val hx = g.x0 + 4f + w * 0.6f; val hz = g.z0 + 23f; val ty = FL + 4.4f + 21f + 0.12f
        b.cyl(hx, ty, hz, 4.4f, 4.4f, 0.06f, C("#3C3F44"), true, 28)
        b.cyl(hx, ty + 0.01f, hz, 4.1f, 4.1f, 0.06f, C("#F2C230"), true, 28)
        b.cyl(hx, ty + 0.02f, hz, 3.8f, 3.8f, 0.06f, C("#3C3F44"), true, 28)
        b.box(hx - 0.9f, ty + 0.1f, hz, 0.35f, 0.02f, 2.6f, C("#FFFFFF")); b.box(hx + 0.9f, ty + 0.1f, hz, 0.35f, 0.02f, 2.6f, C("#FFFFFF")); b.box(hx, ty + 0.1f, hz, 1.8f, 0.02f, 0.35f, C("#FFFFFF"))
        for (k in 0 until 2) Vehicles.parkedKind(g, acx - 2.2f + k * 4.4f, g.z0 + 4.2f, 1, CURB, Vehicles.AMBULANCE)
        g.b.m(Mt.ASPHALT, 0.3f)
        g.b.box((g.x0 + g.x1) / 2, CURB + 0.01f, g.z1 - 6.5f, g.x1 - g.x0 - 4f, 0.02f, 11f, C("#D0D0D0"))
        var x = g.x0 + 5f
        while (x < g.x1 - 4f) { if (rng.chance(0.6f)) Vehicles.parked(g, x, g.z1 - 6.5f, 1, CURB + 0.02f, rng); x += 3.3f }
        for (k in 0 until 5) tree(g, g.x0 + 3f + k * (g.x1 - g.x0 - 6f) / 4f, g.z0 + 1.2f, 0.85f)
        return h
    }

    private fun school(g: Gen): Float {
        val b = g.b; val rng = g.rng
        val h = tower(g, g.x0 + 4f, g.x1 - 4f, g.z1, 1f, 4f, 14f, 2, C("#FFF1D6"), "ESCOLA", 0)
        val qx = (g.x0 + g.x1) / 2; val qz = g.z0 + 13f
        b.m(Mt.PLAIN)
        b.box(qx, CURB + 0.015f, qz, 30f, 0.03f, 17f, C("#3C8D5A"))
        b.box(qx, CURB + 0.03f, qz, 28f, 0.03f, 15f, C("#2F6FB0"))
        val wl = C("#FFFFFF")
        b.box(qx, CURB + 0.05f, qz - 7.5f, 28f, 0.02f, 0.1f, wl); b.box(qx, CURB + 0.05f, qz + 7.5f, 28f, 0.02f, 0.1f, wl)
        b.box(qx - 14f, CURB + 0.05f, qz, 0.1f, 0.02f, 15f, wl); b.box(qx + 14f, CURB + 0.05f, qz, 0.1f, 0.02f, 15f, wl)
        b.box(qx, CURB + 0.05f, qz, 0.1f, 0.02f, 15f, wl)
        b.cyl(qx, CURB + 0.045f, qz, 2.5f, 2.5f, 0.01f, C("#2F6FB0"), true, 24)
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-1f, 1f)) {
            b.box(qx + s * 14f, CURB + 1.0f, qz - 1.5f, 0.1f, 2f, 0.1f, wl); b.box(qx + s * 14f, CURB + 1.0f, qz + 1.5f, 0.1f, 2f, 0.1f, wl)
            b.box(qx + s * 14f, CURB + 2.0f, qz, 0.1f, 0.1f, 3.1f, wl)
        }
        b.m(Mt.GLASS); b.al = 0.4f
        b.box(qx, CURB + 1.5f, qz - 8.6f, 30f, 3f, 0.03f, C("#9BA3A8")); b.box(qx, CURB + 1.5f, qz + 8.6f, 30f, 3f, 0.03f, C("#9BA3A8"))
        b.box(qx - 15f, CURB + 1.5f, qz, 0.03f, 3f, 17f, C("#9BA3A8")); b.box(qx + 15f, CURB + 1.5f, qz, 0.03f, 3f, 17f, C("#9BA3A8"))
        b.al = 1f
        g.solid(qx - 15.2f, qz - 8.8f, qx + 15.2f, qz - 8.4f); g.solid(qx - 15.2f, qz + 8.4f, qx + 15.2f, qz + 8.8f)
        Vehicles.parkedKind(g, g.x0 + 3f, g.z1 - 10f, 1, CURB, Vehicles.BUS)
        for (k in 0 until 5) tree(g, g.x1 - 2.5f, g.z0 + 4f + k * 9f, 1.1f)
        return h
    }

    private fun police(g: Gen): Float {
        val rng = g.rng
        val w = (g.x1 - g.x0) / 2 - 3f
        val h1 = tower(g, g.x0 + 2f, g.x0 + 2f + w, g.z1, 1f, 5f, 16f, 3, C("#E3E8EE"), "POLÍCIA", 0)
        for (k in 0 until 2) Vehicles.parkedKind(g, g.x0 + 4f + k * 5f, g.z1 - 2.6f, 0, CURB, Vehicles.POLICE)
        val h2 = tower(g, g.x1 - 2f - w, g.x1 - 2f, g.z1, 1f, 5f, 16f, 2, C("#F3D9D2"), "BOMBEIROS", 0)
        Vehicles.parkedKind(g, g.x1 - 2f - w / 2, g.z1 - 2.8f, 0, CURB, Vehicles.FIRE)
        residentialStrip(g, g.z0, -1f, 20f)
        return max(h1, h2)
    }

    private fun residentialStrip(g: Gen, fz0: Float, fz: Float, depth: Float) {
        val rng = g.rng
        var x = g.x0
        while (x < g.x1 - 9f) {
            val lw = min(g.x1 - x, rng.r(12.5f, 15.5f)).let { if (g.x1 - x - it < 11f) g.x1 - x else it }
            house(g, x, x + lw, fz0, fz, depth, rng.i(5), rng.chance(0.2f))
            x += lw
        }
    }

    private fun church(g: Gen): Float {
        val b = g.b; val rng = g.rng
        val cx = (g.x0 + g.x1) / 2; val zf = g.z1 - 10f; val zb = g.z1 - 34f
        val w = 13f
        // adro
        b.m(Mt.PAVER, 0.7f); b.box(cx, CURB + 0.02f, (g.z1 + zf) / 2, 18f, 0.04f, 10f, C("#E8DCC6"))
        val bd = g.begin(cx - w / 2, zb, cx + w / 2, zf, "Igreja Matriz")
        val A = g.A; val H = g.H
        A.m(Mt.STONE, 0.6f); A.box(cx, FL / 2, (zf + zb) / 2, w, FL, zf - zb, C("#BDB3A3"))
        A.m(Mt.FLOOR_D, 0.6f); A.box(cx, FL - 0.005f, (zf + zb) / 2, w - 0.3f, 0.012f, zf - zb - 0.3f, C("#FFFFFF"))
        val wc = C("#FFF8EC")
        wall(g, 0, zf, cx - w / 2, cx + w / 2, FL, FL + 9f, 1, listOf(Op(cx, 2.2f, FL, FL + 4f, true)), wc, C("#FFFDF7"), Mt.PLASTER, 0.4f)
        wall(g, 0, zb, cx - w / 2, cx + w / 2, FL, FL + 9f, -1, emptyList(), wc, C("#FFFDF7"), Mt.PLASTER, 0.4f)
        val sOps = (0 until 5).map { Op(zb + 3f + it * 4.5f, 1.4f, FL + 2.5f, FL + 6.5f, false) }
        wall(g, 1, cx - w / 2, zb + 0.2f, zf - 0.2f, FL, FL + 9f, -1, sOps, wc, C("#FFFDF7"), Mt.PLASTER, 0.4f)
        wall(g, 1, cx + w / 2, zb + 0.2f, zf - 0.2f, FL, FL + 9f, 1, sOps, wc, C("#FFFDF7"), Mt.PLASTER, 0.4f)
        g.solid(cx - w / 2 - 0.3f, zb, cx - w / 2 + 0.3f, zf); g.solid(cx + w / 2 - 0.3f, zb, cx + w / 2 + 0.3f, zf); g.solid(cx - w / 2, zb - 0.3f, cx + w / 2, zb + 0.3f)
        g.solid(cx - w / 2, zf - 0.3f, cx - 1.2f, zf + 0.3f); g.solid(cx + 1.2f, zf - 0.3f, cx + w / 2, zf + 0.3f)
        // bancos e altar
        for (r in 0 until 7) for (s in floatArrayOf(-1f, 1f)) {
            val bz = zf - 4f - r * 2.0f
            A.m(Mt.WOOD, 1f)
            A.box(cx + s * 3.3f, FL + 0.45f, bz, 4.4f, 0.06f, 0.45f, C("#6D4C41"))
            A.box(cx + s * 3.3f, FL + 0.75f, bz - 0.25f, 4.4f, 0.6f, 0.06f, C("#6D4C41"))
            for (t in floatArrayOf(-2.1f, 2.1f)) A.box(cx + s * 3.3f + t, FL + 0.42f, bz, 0.08f, 0.84f, 0.5f, C("#5D4037"))
            g.solid(cx + s * 3.3f - 2.2f, bz - 0.35f, cx + s * 3.3f + 2.2f, bz + 0.3f)
        }
        A.m(Mt.STONE, 0.8f); A.box(cx, FL + 0.25f, zb + 3f, 8f, 0.5f, 4f, C("#D7CCC8"))
        A.m(Mt.FABRIC, 1f); A.box(cx, FL + 1.0f, zb + 2.5f, 2.4f, 1.0f, 1.0f, C("#FFFFFF")); A.box(cx, FL + 1.52f, zb + 2.5f, 2.5f, 0.04f, 1.1f, C("#C9A227"))
        A.m(Mt.WOOD, 1f); A.box(cx, FL + 4.5f, zb + 0.35f, 0.25f, 3.2f, 0.15f, C("#5D4037")); A.box(cx, FL + 5.4f, zb + 0.35f, 1.6f, 0.25f, 0.15f, C("#5D4037"))
        // telhado e torre
        H.m(Mt.ROOF, 0.6f)
        val ty = FL + 9f
        q(H, P(cx - w / 2 - 0.5f, ty - 0.4f, zb - 0.5f) + P(cx - w / 2 - 0.5f, ty - 0.4f, zf + 0.5f) + P(cx, ty + 4.5f, zf + 0.5f) + P(cx, ty + 4.5f, zb - 0.5f), C("#9C4A2F"))
        q(H, P(cx + w / 2 + 0.5f, ty - 0.4f, zf + 0.5f) + P(cx + w / 2 + 0.5f, ty - 0.4f, zb - 0.5f) + P(cx, ty + 4.5f, zb - 0.5f) + P(cx, ty + 4.5f, zf + 0.5f), C("#9C4A2F"))
        H.m(Mt.PLASTER, 0.5f)
        tri(H, P(cx - w / 2, ty, zf) + P(cx + w / 2, ty, zf) + P(cx, ty + 4.5f, zf), wc)
        tri(H, P(cx + w / 2, ty, zb) + P(cx - w / 2, ty, zb) + P(cx, ty + 4.5f, zb), wc)
        H.box(cx, ty + 3f, zf + 1.6f, 4f, 24f, 3.2f, wc)
        H.m(Mt.PLAIN); H.box(cx, ty + 9f, zf + 3.22f, 1.6f, 2.6f, 0.05f, C("#3E2723")); H.box(cx, ty + 9f, zf - 0.02f, 1.6f, 2.6f, 0.05f, C("#3E2723"))
        H.m(Mt.ROOF, 0.6f)
        q(H, P(cx - 2.2f, ty + 15f, zf - 0.2f) + P(cx + 2.2f, ty + 15f, zf - 0.2f) + P(cx, ty + 19f, zf + 1.6f) + P(cx, ty + 19f, zf + 1.6f), C("#6D3A2A"))
        q(H, P(cx + 2.2f, ty + 15f, zf + 3.4f) + P(cx - 2.2f, ty + 15f, zf + 3.4f) + P(cx, ty + 19f, zf + 1.6f) + P(cx, ty + 19f, zf + 1.6f), C("#6D3A2A"))
        q(H, P(cx - 2.2f, ty + 15f, zf + 3.4f) + P(cx - 2.2f, ty + 15f, zf - 0.2f) + P(cx, ty + 19f, zf + 1.6f) + P(cx, ty + 19f, zf + 1.6f), C("#6D3A2A"))
        q(H, P(cx + 2.2f, ty + 15f, zf - 0.2f) + P(cx + 2.2f, ty + 15f, zf + 3.4f) + P(cx, ty + 19f, zf + 1.6f) + P(cx, ty + 19f, zf + 1.6f), C("#6D3A2A"))
        H.m(Mt.METAL, 1f); H.box(cx, ty + 20.2f, zf + 1.6f, 0.15f, 2.4f, 0.15f, C("#C9A227")); H.box(cx, ty + 20.6f, zf + 1.6f, 1.2f, 0.15f, 0.15f, C("#C9A227"))
        sign(H, cx, FL + 4.6f, zf + 0.22f, 0f, 1f, 4.5f, 0.6f, City.signIdx("IGREJA MATRIZ"))
        g.end()
        g.place(City.Place("Igreja Matriz", cx, zf + 3f, 0xFF6D4C41.toInt(), 'I'))
        g.f.m(Mt.PLASTER, 0.5f); g.f.box(cx, FL + 4.5f, (zf + zb) / 2, w, 9f, zf - zb, wc); g.f.box(cx, ty + 3f, zf + 1.6f, 4f, 24f, 3.2f, wc)
        for (k in 0 until 8) tree(g, g.x0 + 3f + (k % 2) * (g.x1 - g.x0 - 6f), g.z0 + 5f + (k / 2) * 10f, 1.1f)
        for (k in 0 until 3) publicBench(b, cx - 6f + k * 6f, g.z1 - 3f, 0f, -1f)
        return 40f
    }

    private fun fountain(g: Gen, x: Float, z: Float) {
        val b = g.b
        b.m(Mt.STONE, 0.8f)
        b.cyl(x, CURB, z, 4.4f, 4.4f, 0.6f, C("#D9D3C7"), true, 32)
        b.m(Mt.PLAIN)
        b.cyl(x, CURB + 0.45f, z, 4.05f, 4.05f, 0.14f, C("#4FB6D6"), true, 32)
        b.m(Mt.STONE, 0.8f)
        b.cyl(x, CURB + 0.55f, z, 0.55f, 0.38f, 1.7f, C("#D9D3C7"), true, 16)
        b.cyl(x, CURB + 2.2f, z, 1.7f, 1.25f, 0.28f, C("#D9D3C7"), true, 22)
        b.cyl(x, CURB + 2.48f, z, 0.25f, 0.18f, 0.9f, C("#D9D3C7"), true, 12)
        b.cyl(x, CURB + 3.35f, z, 0.75f, 0.55f, 0.18f, C("#D9D3C7"), true, 16)
        b.m(Mt.GLASS); b.al = 0.55f
        b.cyl(x, CURB + 3.5f, z, 0.08f, 0.03f, 0.9f, C("#CFF4FF"), true, 8)
        b.cyl(x, CURB + 2.5f, z, 0.85f, 0.7f, 0.9f, C("#CFF4FF"), true, 16)
        b.cyl(x, CURB + 0.6f, z, 1.75f, 1.4f, 1.6f, C("#CFF4FF"), true, 20)
        b.al = 1f
        g.solid(x - 4.4f, z - 4.4f, x + 4.4f, z + 4.4f)
        g.f.m(Mt.STONE, 0.8f); g.f.cyl(x, CURB, z, 4.4f, 4.4f, 0.6f, C("#D9D3C7"), true, 16)
    }

    private fun praca(g: Gen): Float {
        val b = g.b; val rng = g.rng
        val cx = (g.x0 + g.x1) / 2; val cz = (g.z0 + g.z1) / 2
        b.m(Mt.PAVER, 0.7f)
        b.box(cx, CURB + 0.01f, cz, 4f, 0.02f, g.z1 - g.z0, C("#E5DCCB"))
        b.box(cx, CURB + 0.01f, cz, g.x1 - g.x0, 0.02f, 4f, C("#E5DCCB"))
        b.cyl(cx, CURB, cz, 9.5f, 9.5f, 0.03f, C("#E5DCCB"), true, 36)
        fountain(g, cx, cz)
        for (k in 0 until 4) {
            val a = (k * 90 + 45) * PI.toFloat() / 180f
            val fx = cx + 14f * cos(a); val fzz = cz + 14f * sin(a)
            b.m(Mt.STONE, 0.8f)
            b.cyl(fx, CURB, fzz, 2.6f, 2.6f, 0.38f, C("#BCA88E"), true, 18)
            b.m(Mt.GRASS, 0.3f); b.cyl(fx, CURB + 0.3f, fzz, 2.4f, 2.4f, 0.1f, C("#8DB86B"), true, 18)
            flowers(g, fx - 1.6f, fzz - 1.6f, fx + 1.6f, fzz + 1.6f, 18, CURB + 0.4f)
            g.solid(fx - 2.4f, fzz - 2.4f, fx + 2.4f, fzz + 2.4f)
        }
        for (k in 0 until 8) {
            val a = (k * 45 + 22.5f) * PI.toFloat() / 180f
            val bx = cx + 7.8f * cos(a); val bz = cz + 7.8f * sin(a)
            val ax = if (abs(cos(a)) > abs(sin(a))) (if (cos(a) > 0) 1f else -1f) else 0f
            val az = if (ax == 0f) (if (sin(a) > 0) 1f else -1f) else 0f
            publicBench(b, bx, bz, -ax, -az)
        }
        for (k in 0 until 18) {
            val tx = rng.r(g.x0 + 3f, g.x1 - 3f); val tz = rng.r(g.z0 + 3f, g.z1 - 3f)
            if (abs(tx - cx) < 3.5f || abs(tz - cz) < 3.5f || (abs(tx - cx) < 17f && abs(tz - cz) < 17f)) continue
            if (k % 3 == 0) palm(g, tx, tz, rng.r(0.8f, 1.0f)) else tree(g, tx, tz, rng.r(1.0f, 1.4f))
        }
        for (s in intArrayOf(-1, 1)) { streetLamp(b, cx + s * 2.6f, cz - 15f, 0f, 0f); streetLamp(b, cx + s * 2.6f, cz + 15f, 0f, 0f) }
        sign(b, cx + 3.4f, CURB + 2.0f, g.z0 + 2.5f, 0f, -1f, 4.4f, 0.55f, City.signIdx("PRAÇA CENTRAL"))
        b.m(Mt.WOOD, 1f)
        for (s in floatArrayOf(-2f, 2f)) b.box(cx + 3.4f + s, CURB + 1.1f, g.z0 + 2.6f, 0.15f, 2.2f, 0.15f, C("#6D4C33"))
        // coreto
        val kx = g.x1 - 10f; val kz = g.z1 - 10f
        b.m(Mt.STONE, 0.8f); b.cyl(kx, CURB, kz, 4f, 4f, 0.6f, C("#E0D6C4"), true, 8)
        b.m(Mt.PLAIN)
        for (k in 0 until 8) { val a = k * PI.toFloat() / 4f; b.cyl(kx + 3.6f * cos(a), CURB + 0.6f, kz + 3.6f * sin(a), 0.12f, 0.12f, 3f, C("#FFFFFF"), true, 8) }
        b.m(Mt.ROOF, 0.6f); b.cyl(kx, CURB + 3.6f, kz, 4.6f, 0.2f, 2.2f, C("#2E7D32"), true, 8)
        g.solid(kx - 4f, kz - 4f, kx + 4f, kz + 4f)
        // academia ao ar livre
        val gx = g.x0 + 9f; val gz = g.z1 - 9f
        b.m(Mt.PAVER, 0.7f); b.box(gx, CURB + 0.015f, gz, 10f, 0.03f, 10f, C("#F0C987"))
        b.m(Mt.METAL, 1f)
        for (k in 0 until 4) {
            val ex = gx - 3f + (k % 2) * 6f; val ez = gz - 3f + (k / 2) * 6f
            b.box(ex, CURB + 1.0f, ez, 0.12f, 2.0f, 0.12f, C("#F2C230"))
            b.box(ex, CURB + 1.9f, ez, 1.6f, 0.1f, 0.1f, C("#2E7D32"))
            b.box(ex + 0.7f, CURB + 0.9f, ez, 0.1f, 1.8f, 0.1f, C("#2E7D32"))
        }
        sign(b, gx, CURB + 1.6f, gz + 5.5f, 0f, 1f, 4f, 0.5f, City.signIdx("ACADEMIA AO AR LIVRE"))
        g.place(City.Place("Praça Central", cx, cz, 0xFF43A047.toInt(), 'P'))
        return 10f
    }

    private fun park(g: Gen): Float {
        val b = g.b; val rng = g.rng
        val cx = (g.x0 + g.x1) / 2; val cz = (g.z0 + g.z1) / 2
        b.m(Mt.PLAIN)
        b.cyl(cx + 4f, CURB - 0.05f, cz - 3f, 11f, 11f, 0.08f, C("#C9B79A"), true, 36)
        b.cyl(cx + 4f, CURB - 0.04f, cz - 3f, 10f, 10f, 0.1f, C("#3FA4C8"), true, 36)
        for (k in 0 until 6) { val a = k * 1.05f; CityGeo.ball(b, cx + 4f + 10.4f * cos(a), CURB, cz - 3f + 10.4f * sin(a), 0.5f, C("#9E9E9E"), 0.3f, 6) }
        g.solid(cx - 6f, cz - 13f, cx + 14f, cz + 7f)
        // ponte de madeira no lago e patinhos
        b.m(Mt.WOOD, 1f); b.box(cx + 4f, CURB + 0.25f, cz - 3f, 2f, 0.12f, 21f, C("#A47551"))
        b.m(Mt.PLAIN); for (k in 0 until 3) { CityGeo.ball(b, cx + 8f + k * 0.8f, CURB + 0.1f, cz - 6f + k * 0.5f, 0.15f, C("#FFFFFF"), 0.11f, 6); b.box(cx + 8.12f + k * 0.8f, CURB + 0.14f, cz - 6f + k * 0.5f, 0.05f, 0.03f, 0.05f, C("#FF9800")) }
        b.m(Mt.PAVER, 0.7f)
        for (k in 0 until 48) {
            val a0 = k * 6.283f / 48; val r = 19f
            b.box(cx + r * cos(a0 + 0.065f), CURB + 0.012f, cz + r * sin(a0 + 0.065f), 2.8f, 0.02f, 2.8f, C("#E1D2B6"))
        }
        val px = g.x0 + 7f; val pz = g.z0 + 7f
        b.m(Mt.PLAIN); b.box(px, CURB + 0.02f, pz, 10f, 0.04f, 10f, C("#E8C99A"))
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-1.5f, 1.5f)) b.box(px + s, CURB + 1.2f, pz - 2f, 0.1f, 2.4f, 0.1f, C("#E53935"))
        b.box(px, CURB + 2.4f, pz - 2f, 3.2f, 0.1f, 0.1f, C("#E53935"))
        for (s in floatArrayOf(-0.6f, 0.6f)) { b.box(px + s, CURB + 1.3f, pz - 2f, 0.02f, 2.1f, 0.02f, C("#555555")); b.box(px + s, CURB + 0.3f, pz - 2f, 0.5f, 0.05f, 0.25f, C("#1B98E0")) }
        b.box(px + 1.5f, CURB + 0.9f, pz + 2f, 1.6f, 1.8f, 1.6f, C("#F2C230"))
        b.m(Mt.PLAIN)
        q(b, P(px + 2.3f, CURB + 1.8f, pz + 1.5f) + P(px + 2.3f, CURB + 1.8f, pz + 2.5f) + P(px + 5f, CURB + 0.1f, pz + 2.5f) + P(px + 5f, CURB + 0.1f, pz + 1.5f), C("#2A9D8F"))
        b.box(px - 3f, CURB + 0.5f, pz + 2.5f, 2.6f, 0.08f, 0.35f, C("#8E24AA")); b.box(px - 3f, CURB + 0.25f, pz + 2.5f, 0.15f, 0.5f, 0.15f, C("#555555"))
        g.solid(px - 5f, pz - 5f, px + 5f, pz + 5f)
        for (k in 0 until 32) {
            val tx = rng.r(g.x0 + 2f, g.x1 - 2f); val tz = rng.r(g.z0 + 2f, g.z1 - 2f)
            val dx = tx - cx; val dz = tz - cz
            if (dx * dx + dz * dz < 21f * 21f && dx * dx + dz * dz > 16f * 16f) continue
            if ((tx - cx - 4f) * (tx - cx - 4f) + (tz - cz + 3f) * (tz - cz + 3f) < 13f * 13f) continue
            if (abs(tx - px) < 6f && abs(tz - pz) < 6f) continue
            if (k % 3 == 0) g.fl.place("pine_a", tx.toDouble(), CURB.toDouble(), tz.toDouble(), rng.r(1.1f, 1.5f).toDouble(), rng.r(0f, 6f).toDouble())
            else tree(g, tx, tz, rng.r(1.1f, 1.6f))
        }
        for (k in 0 until 6) {
            val a = k * 1.047f + 0.4f
            val ax = if (abs(cos(a)) > 0.7f) -(if (cos(a) >= 0) 1f else -1f) else 0f
            val az = if (ax == 0f) -(if (sin(a) >= 0) 1f else -1f) else 0f
            publicBench(b, cx + 21.6f * cos(a), cz + 21.6f * sin(a), ax, az)
        }
        g.place(City.Place("Parque", cx, cz, 0xFF2E7D32.toInt(), 'P'))
        return 10f
    }

    // ============================================================ ruas

    fun roads(out: ArrayList<City.Chunk>) {
        val asph = C("#FFFFFF"); val walk = C("#E3E0DA"); val curbC = C("#C9C6C0")
        val yel = C("#F2C230"); val wht = C("#F4F4F4")
        val bandX = City.bandX; val bandZ = City.bandZ
        val X0 = City.X0; val X1 = City.X1; val Z0 = City.Z0; val Z1 = City.Z1
        // Etapa 122: todas as ruas num pedaço só (uma chamada por material)
        val g = Gen(out.size, City.Rng(13), X0, Z0, X1, Z1)
        val b = g.b
        for (k in 0 until 8) {
            val za = bandZ[k * 2]; val zb = bandZ[k * 2 + 1]; val zc = (za + zb) / 2
            b.m(Mt.ASPHALT, 0.25f); b.plane(X0, za + SIDE, X1, zb - SIDE, 0f, asph)
            g.f.m(Mt.ASPHALT, 0.25f); g.f.plane(X0, za + SIDE, X1, zb - SIDE, 0f, asph)
            for (iv in freeIntervals(X0, X1, bandX)) {
                for (bb in arrayOf(b, g.f)) {
                    groundBox(bb, iv[0], za, iv[1], za + SIDE, Mt.PAVER, 0.9f, walk)
                    groundBox(bb, iv[0], zb - SIDE, iv[1], zb, Mt.PAVER, 0.9f, walk)
                }
                b.m(Mt.STONE, 1f)
                b.box((iv[0] + iv[1]) / 2, CURB / 2 + 0.005f, za + SIDE - 0.12f, iv[1] - iv[0], CURB + 0.01f, 0.24f, curbC)
                b.box((iv[0] + iv[1]) / 2, CURB / 2 + 0.005f, zb - SIDE + 0.12f, iv[1] - iv[0], CURB + 0.01f, 0.24f, curbC)
            }
            b.m(Mt.PLAIN)
            for (iv in freeIntervals(X0, X1, bandX, -SIDE)) {
                val a = iv[0] + 3.2f; val e = iv[1] - 3.2f
                if (e <= a) continue
                flat(b, (a + e) / 2, zc - 0.12f, e - a, 0.1f, yel); flat(b, (a + e) / 2, zc + 0.12f, e - a, 0.1f, yel)
                flat(b, (a + e) / 2, za + SIDE + 0.35f, e - a, 0.12f, wht); flat(b, (a + e) / 2, zb - SIDE - 0.35f, e - a, 0.12f, wht)
                for (side in intArrayOf(0, 1)) {
                    if ((side == 0 && iv[0] <= X0 + 0.1f) || (side == 1 && iv[1] >= X1 - 0.1f)) continue
                    val x = if (side == 0) iv[0] else iv[1]; val dx = if (side == 0) 1f else -1f
                    var zz = za + SIDE + 0.5f
                    while (zz < zb - SIDE - 0.4f) { flat(b, x + dx * 1.6f, zz + 0.25f, 2.4f, 0.5f, wht); zz += 1.0f }
                    val s0 = if (side == 0) za + SIDE else zc; val s1 = if (side == 0) zc else zb - SIDE
                    flat(b, x + dx * 3.3f, (s0 + s1) / 2, 0.35f, s1 - s0, wht)
                    // seta no asfalto
                    val ax = x + dx * 7f; val az = (s0 + s1) / 2
                    flat(b, ax + dx * 0.6f, az, 1.6f, 0.18f, wht)
                    tri(b, P(ax - dx * 0.4f, 0.013f, az - 0.4f) + P(ax - dx * 0.4f, 0.013f, az + 0.4f) + P(ax - dx * 1.1f, 0.013f, az), wht)
                }
            }
            for ((ii, iv) in freeIntervals(X0, X1, bandX).withIndex()) {
                var x = iv[0] + 6f; var n = 0
                while (x < iv[1] - 6f) {
                    if (n % 2 == 0) { streetLamp(b, x, za + 0.6f, 0f, 1f); streetLamp(b, x + 9f, zb - 0.6f, 0f, -1f) }
                    else { if (k == 7) { palm(g, x, za + 1.3f, 0.9f); palm(g, x + 9f, zb - 1.3f, 0.9f) } else { tree(g, x, za + 1.3f, g.rng.r(0.8f, 1.0f)); tree(g, x + 9f, zb - 1.3f, g.rng.r(0.8f, 1.0f)) } }
                    if (n % 5 == 3) { trashBin(b, x + 2f, za + 0.5f); hydrant(b, x + 4f, zb - 0.45f) }
                    if (n == 2 && ii % 2 == 0) busStop(g, x + 4.5f, za + 1.3f, 1f)
                    x += 18f; n++
                }
            }
        }
        for (k in 0 until 8) {
            val xa = bandX[k * 2]; val xb = bandX[k * 2 + 1]; val xc = (xa + xb) / 2
            val segs = freeIntervals(Z0, Z1, bandZ, -SIDE)
            for (bb in arrayOf(b, g.f)) { bb.m(Mt.ASPHALT, 0.25f); for (iv in segs) bb.plane(xa + SIDE, iv[0], xb - SIDE, iv[1], 0f, asph) }
            for (iv in freeIntervals(Z0, Z1, bandZ)) {
                for (bb in arrayOf(b, g.f)) {
                    groundBox(bb, xa, iv[0], xa + SIDE, iv[1], Mt.PAVER, 0.9f, walk)
                    groundBox(bb, xb - SIDE, iv[0], xb, iv[1], Mt.PAVER, 0.9f, walk)
                }
                b.m(Mt.STONE, 1f)
                b.box(xa + SIDE - 0.12f, CURB / 2 + 0.005f, (iv[0] + iv[1]) / 2, 0.24f, CURB + 0.01f, iv[1] - iv[0], curbC)
                b.box(xb - SIDE + 0.12f, CURB / 2 + 0.005f, (iv[0] + iv[1]) / 2, 0.24f, CURB + 0.01f, iv[1] - iv[0], curbC)
            }
            b.m(Mt.PLAIN)
            for (iv in segs) {
                val a = iv[0] + 3.2f; val e = iv[1] - 3.2f
                if (e <= a) continue
                flat(b, xc - 0.12f, (a + e) / 2, 0.1f, e - a, yel); flat(b, xc + 0.12f, (a + e) / 2, 0.1f, e - a, yel)
                flat(b, xa + SIDE + 0.35f, (a + e) / 2, 0.12f, e - a, wht); flat(b, xb - SIDE - 0.35f, (a + e) / 2, 0.12f, e - a, wht)
                for (side in intArrayOf(0, 1)) {
                    if ((side == 0 && iv[0] <= Z0 + 0.1f) || (side == 1 && iv[1] >= Z1 - 0.1f)) continue
                    val z = if (side == 0) iv[0] else iv[1]; val dz = if (side == 0) 1f else -1f
                    var xx = xa + SIDE + 0.5f
                    while (xx < xb - SIDE - 0.4f) { flat(b, xx + 0.25f, z + dz * 1.6f, 0.5f, 2.4f, wht); xx += 1.0f }
                    val s0 = if (side == 0) xc else xa + SIDE; val s1 = if (side == 0) xb - SIDE else xc
                    flat(b, (s0 + s1) / 2, z + dz * 3.3f, s1 - s0, 0.35f, wht)
                }
            }
            for ((ii, iv) in freeIntervals(Z0, Z1, bandZ).withIndex()) {
                var z = iv[0] + 6f; var n = 0
                while (z < iv[1] - 6f) {
                    if (n % 2 == 0) { streetLamp(b, xa + 0.6f, z, 1f, 0f); streetLamp(b, xb - 0.6f, z + 9f, -1f, 0f) }
                    else { tree(g, xa + 1.3f, z, g.rng.r(0.8f, 1.0f)); tree(g, xb - 1.3f, z + 9f, g.rng.r(0.8f, 1.0f)) }
                    if (n % 5 == 3) { trashBin(b, xa + 0.5f, z + 2f); hydrant(b, xb - 0.45f, z + 4f) }
                    z += 18f; n++
                }
            }
            // semáforos e placas de rua
            for (j in 1 until 7) {
                if (k == 0 || k == 7) continue
                val za = bandZ[j * 2]; val zb = bandZ[j * 2 + 1]
                for (cx in intArrayOf(0, 1)) for (cz in intArrayOf(0, 1)) {
                    val x = if (cx == 0) xa + 1.0f else xb - 1.0f
                    val z = if (cz == 0) za + 1.0f else zb - 1.0f
                    b.m(Mt.METAL, 1f)
                    b.cyl(x, CURB, z, 0.11f, 0.08f, 4.3f, C("#2E3236"), true, 8)
                    for (h in headPos(x, z, cx, cz)) {
                        b.box(h[0], h[1], h[2], 0.36f, 1.0f, 0.36f, C("#1E1F22"))
                        b.box(h[0], h[1] + 0.56f, h[2], 0.42f, 0.06f, 0.42f, C("#1E1F22"))
                    }
                    b.m(Mt.PLAIN)
                    b.box(x, CURB + 1.1f, z, 0.16f, 0.2f, 0.16f, C("#F2C230"))   // botoeira de pedestre
                    if (cx == 1 && cz == 1) {
                        b.m(Mt.METAL, 1f)
                        b.cyl(x - 0.4f, CURB, z - 0.4f, 0.05f, 0.05f, 3.0f, C("#7D868F"), true, 6)
                        roadSign(b, x - 0.4f, CURB + 2.65f, z - 0.4f, 0f, 1f, City.ROAD_NAMES_Z[k])
                        roadSign(b, x - 0.4f, CURB + 3.0f, z - 0.4f, 1f, 0f, City.ROAD_NAMES_X[j])
                    }
                }
            }
        }
        g.f.clear()
        out.add(g.finish(7f))
    }

    /** Placa de rua verde com o nome (usa o atlas quando o nome existe; senão uma placa lisa). */
    private fun roadSign(b: MB, x: Float, y: Float, z: Float, fx: Float, fz: Float, name: String) {
        val up = name.uppercase()
        val idx = City.SIGNS.indexOfFirst { it.first == up }
        if (idx >= 0) {
            sign(b, x + fx * 0.05f, y, z + fz * 0.05f, fx, fz, 1.9f, 0.26f, idx, false)
            sign(b, x - fx * 0.05f, y, z - fz * 0.05f, -fx, -fz, 1.9f, 0.26f, idx, false)
        } else {
            b.m(Mt.PLAIN)
            if (abs(fz) > 0.5f) b.box(x, y + 0.13f, z, 1.9f, 0.26f, 0.06f, C("#1B7F3B")) else b.box(x, y + 0.13f, z, 0.06f, 0.26f, 1.9f, C("#1B7F3B"))
        }
    }

    private fun trashBin(b: MB, x: Float, z: Float) {
        b.m(Mt.METAL, 1f)
        b.cyl(x, CURB, z, 0.03f, 0.03f, 0.9f, C("#555555"), true, 5)
        b.cyl(x, CURB + 0.45f, z, 0.24f, 0.22f, 0.5f, C("#2E7D32"), true, 10)
    }

    private fun hydrant(b: MB, x: Float, z: Float) {
        b.m(Mt.METAL, 1f)
        b.cyl(x, CURB, z, 0.13f, 0.12f, 0.55f, C("#D32F2F"), true, 10)
        CityGeo.ball(b, x, CURB + 0.6f, z, 0.13f, C("#D32F2F"), 0.1f, 8)
        b.box(x, CURB + 0.38f, z, 0.36f, 0.08f, 0.08f, C("#D32F2F"))
    }

    private fun busStop(g: Gen, x: Float, z: Float, fz: Float) {
        val b = g.b
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-1.6f, 1.6f)) b.box(x + s, CURB + 1.25f, z + fz * 0.6f, 0.08f, 2.5f, 0.08f, C("#455A64"))
        b.box(x, CURB + 2.55f, z, 3.6f, 0.1f, 1.6f, C("#455A64"))
        b.m(Mt.GLASS); b.al = 0.35f; b.box(x, CURB + 1.3f, z + fz * 0.7f, 3.3f, 2.2f, 0.03f, C("#D0EAF5")); b.al = 1f
        b.m(Mt.WOOD, 1f); b.box(x, CURB + 0.45f, z + fz * 0.4f, 2.6f, 0.06f, 0.4f, C("#8D6E63"))
        b.m(Mt.PLAIN); b.box(x + 1.75f, CURB + 2.0f, z + fz * 0.6f, 0.05f, 0.5f, 0.5f, C("#1565C0"))
    }

    fun headPos(x: Float, z: Float, cx: Int, cz: Int): Array<FloatArray> {
        val ox = if (cx == 0) 1f else -1f; val oz = if (cz == 0) 1f else -1f
        return arrayOf(floatArrayOf(x, CURB + 3.8f, z + oz * 0.36f), floatArrayOf(x + ox * 0.36f, CURB + 3.8f, z))
    }

    fun buildLights() {
        val red = C("#FF3B30"); val yel = C("#FFC400"); val grn = C("#33E06A")
        val bandX = City.bandX; val bandZ = City.bandZ
        val arr = arrayOfNulls<Mesh>(4)
        for (ph in 0 until 4) {
            val b = MB(); b.m(Mt.PLAIN)
            for (k in 1 until 7) for (j in 1 until 7) {
                val xa = bandX[k * 2]; val xb = bandX[k * 2 + 1]; val za = bandZ[j * 2]; val zb = bandZ[j * 2 + 1]
                for (cx in intArrayOf(0, 1)) for (cz in intArrayOf(0, 1)) {
                    val x = if (cx == 0) xa + 1.0f else xb - 1.0f
                    val z = if (cz == 0) za + 1.0f else zb - 1.0f
                    val hp = headPos(x, z, cx, cz)
                    for (ax in 0..1) {
                        val st = if (ax == 0) (if (ph == 0) 2 else if (ph == 1) 1 else 0) else (if (ph == 2) 2 else if (ph == 3) 1 else 0)
                        val col = if (st == 2) grn else if (st == 1) yel else red
                        val dy = if (st == 2) -0.3f else if (st == 1) 0f else 0.3f
                        b.box(hp[ax][0], hp[ax][1] + dy, hp[ax][2], 0.38f, 0.22f, 0.38f, col, false)
                    }
                }
            }
            arr[ph] = b.toMesh(true)
        }
        City.setLights(arr)
    }

    fun freeIntervals(a: Float, b: Float, bands: FloatArray, shrink: Float = 0f): List<FloatArray> {
        val out = ArrayList<FloatArray>()
        var cur = a
        var k = 0
        while (k < bands.size) {
            val s = bands[k] - shrink; val e = bands[k + 1] + shrink
            if (e > cur && s < b) { if (s > cur) out.add(floatArrayOf(cur, s)); cur = max(cur, e) }
            k += 2
        }
        if (cur < b) out.add(floatArrayOf(cur, b))
        return out
    }

    /** Anel verde em volta da cidade (menos do lado da praia), morros e mata. */
    fun ring(): City.Chunk {
        val X0 = City.X0; val X1 = City.X1; val Z0 = City.Z0; val Z1 = City.Z1
        val g = Gen(-1, City.Rng(999), X0 - 420f, Z0 - 420f, X1 + 420f, Z1 + 420f)
        val b = g.b
        val R = 420f
        val gc = C("#D6EEC4")
        b.m(Mt.GRASS, 0.3f)
        b.box((X0 - R + X0) / 2f, -0.06f, (Z0 - R + City.BEACH_Z) / 2f, R, 0.02f, City.BEACH_Z - Z0 + R, gc)
        b.box((X1 + X1 + R) / 2f, -0.06f, (Z0 - R + City.BEACH_Z) / 2f, R, 0.02f, City.BEACH_Z - Z0 + R, gc)
        b.box((X0 + X1) / 2f, -0.06f, (Z0 - R + Z0) / 2f, X1 - X0, 0.02f, R, gc)
        val rng = g.rng
        var a = X0 - 6f
        while (a < X1 + 6f) { g.fl.place("pine_a", a.toDouble(), 0.0, (Z0 - 6f - rng.r(0f, 10f)).toDouble(), rng.r(1.3f, 2.1f).toDouble(), rng.r(0f, 6f).toDouble()); a += rng.r(6f, 11f) }
        a = Z0 - 6f
        while (a < City.BEACH_Z) {
            g.fl.place("pine_a", (X0 - 6f - rng.r(0f, 10f)).toDouble(), 0.0, a.toDouble(), rng.r(1.3f, 2.1f).toDouble(), rng.r(0f, 6f).toDouble())
            g.fl.place("pine_a", (X1 + 6f + rng.r(0f, 10f)).toDouble(), 0.0, a.toDouble(), rng.r(1.3f, 2.1f).toDouble(), rng.r(0f, 6f).toDouble())
            a += rng.r(6f, 11f)
        }
        b.m(Mt.PLAIN)
        for (k in 0 until 16) {
            val ang = PI + k * PI / 15
            val d = 230.0 + (k % 3) * 20
            val cx = ((X0 + X1) / 2 + d * cos(ang)).toFloat(); val cz = ((Z0 + Z1) / 2 + d * sin(ang) * 0.9).toFloat()
            CityGeo.ball(b, cx, -8f, cz, 55f + (k % 4) * 12f, mix(C("#7FAE7C"), C("#B9D3BC"), (k % 3) / 3f), 34f + (k % 3) * 8f, 12)
        }
        val c = City.Chunk(b.toMesh(true), null, X0 - 420f, Z0 - 420f, X1 + 420f, Z1 + 420f, 70f)
        c.pend = g.fl
        return c
    }
}
