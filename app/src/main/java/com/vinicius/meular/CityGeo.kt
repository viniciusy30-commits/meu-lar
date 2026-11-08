package com.vinicius.meular

import kotlin.math.PI
import kotlin.math.acos
import android.graphics.Color
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
            if (reg) {
                City.addBld(bd)
                val top = max(A.maxY(), H.maxY())   // Etapa 127: sombra projetada do prédio
                if (top > 1f) Shade.box(bd.x0, bd.z0, bd.x1, bd.z1, top * 0.94f)
            }
            A = b; H = b; cur = null
        }

        /** Etapa 128: porta no vão (centro x, parede z, lado de fora fz): batente fixo na malha, folhas animadas à parte. */
        fun door(name: String, x: Float, zf: Float, fz: Float, w: Float, h: Float, th: Float) {
            val pk = Doors.pick(name, rng)
            val d = City.Door(x, FL, zf, if (fz > 0) 1f else -1f, w, h, pk[0], pk[1], pk[2], name.uppercase())
            Doors.statics(H, d, th)
            if (reg) City.doors.add(d)
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
        val uvs = Signs.uv(idx)   // Etapa 127: atlas novo 2048 × 2048
        val u0 = uvs[0]; val u1 = uvs[2]; val v0 = uvs[1]; val v1 = uvs[3]
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
    /** Galho/tronco: tubo octogonal afinando de (x0,y0,z0) a (x1,y1,z1), com casca. */
    fun limb(b: MB, x0: Float, y0: Float, z0: Float, x1: Float, y1: Float, z1: Float, r0: Float, r1: Float, c: Int, sides: Int = 7) {
        var tx = x1 - x0; var ty = y1 - y0; var tz = z1 - z0
        val tl = sqrt(tx * tx + ty * ty + tz * tz).coerceAtLeast(1e-4f); tx /= tl; ty /= tl; tz /= tl
        // base perpendicular
        var ax = if (abs(ty) < 0.9f) 0f else 1f; var ay = if (abs(ty) < 0.9f) 1f else 0f; var az = 0f
        var ux = ty * az - tz * ay; var uy = tz * ax - tx * az; var uz = tx * ay - ty * ax
        val ul = sqrt(ux * ux + uy * uy + uz * uz); ux /= ul; uy /= ul; uz /= ul
        val vx = ty * uz - tz * uy; val vy = tz * ux - tx * uz; val vz = tx * uy - ty * ux
        b.m(Mt.BARK, 1f)
        for (i in 0 until sides) {
            val a0 = 2f * PI.toFloat() * i / sides; val a1 = 2f * PI.toFloat() * (i + 1) / sides
            val c0 = cos(a0); val s0 = sin(a0); val c1 = cos(a1); val s1 = sin(a1)
            val n0x = ux * c0 + vx * s0; val n0y = uy * c0 + vy * s0; val n0z = uz * c0 + vz * s0
            val n1x = ux * c1 + vx * s1; val n1y = uy * c1 + vy * s1; val n1z = uz * c1 + vz * s1
            val u0 = i.toFloat() / sides; val u1 = (i + 1f) / sides; val vv = tl / (r0 * 6f + 0.3f)
            fun v(nx: Float, ny: Float, nz: Float, r: Float, px: Float, py: Float, pz: Float, u: Float, w: Float) = b.v(px + nx * r, py + ny * r, pz + nz * r, nx, ny, nz, c, u, w)
            v(n0x, n0y, n0z, r0, x0, y0, z0, u0, 0f); v(n1x, n1y, n1z, r0, x0, y0, z0, u1, 0f); v(n1x, n1y, n1z, r1, x1, y1, z1, u1, vv)
            v(n0x, n0y, n0z, r0, x0, y0, z0, u0, 0f); v(n1x, n1y, n1z, r1, x1, y1, z1, u1, vv); v(n0x, n0y, n0z, r1, x1, y1, z1, u0, vv)
        }
    }

    /**
     * Etapa 125: árvore de verdade — tronco com casca, galhos e copa feita de cartões de folhas (textura com recorte),
     * normais "esféricas" (a copa fica com volume e luz macia) e sombra embaixo da copa.
     * kind: 0 carvalho, 1 bordo claro, 2 ipê roxo, 3 ipê amarelo, 4 copa alta (rua).
     */
    fun tree(g: Gen, x: Float, z: Float, s: Float, y: Float = CURB, kind0: Int = -1) {
        val b = g.b; val rng = g.rng
        val kind = if (kind0 >= 0) kind0 else rng.pick(arrayOf(0, 0, 1, 4, 4, 2, 3, 0, 1))
        val H = (if (kind == 4) 3.4f else 2.6f) * s
        val R = (if (kind == 4) 1.9f else 2.3f) * s
        val trunk = C(rng.pick(arrayOf("#6B5442", "#7A604A", "#5E4A3A")))
        // tronco levemente torto e galhos
        val lx = rng.r(-0.25f, 0.25f) * s; val lz = rng.r(-0.25f, 0.25f) * s
        limb(b, x, y - 0.05f, z, x + lx, y + H, z + lz, 0.2f * s, 0.12f * s, trunk)
        val cy = y + H + R * 0.55f
        val nb = 3 + rng.i(2)
        for (k in 0 until nb) {
            val a = k * 6.283f / nb + rng.r(-0.4f, 0.4f)
            limb(b, x + lx * 0.8f, y + H * 0.82f, z + lz * 0.8f, x + lx + cos(a) * R * 0.6f, cy + rng.r(-0.3f, 0.6f) * s, z + lz + sin(a) * R * 0.6f, 0.09f * s, 0.04f * s, trunk, 5)
        }
        // canteiro: terra e grade em volta (só na calçada)
        val base = when (kind) { 1 -> C("#8FCB5A"); 2 -> C("#B07ACB"); 3 -> C("#F2C94C"); else -> C(rng.pick(arrayOf("#5E9E48", "#6AA84F", "#4F8F3F"))) }
        val mat = if (kind == 1 || kind == 2 || kind == 3) Mt.LEAF2 else Mt.LEAF
        b.m(mat, 1f)
        val nc = (if (kind == 4) 13 else 16)
        val ccx = x + lx; val ccz = z + lz
        for (k in 0 until nc) {
            // pontos espalhados num elipsoide (mais em cima)
            val u = (k + 0.5f) / nc
            val phi = acos(1f - 1.6f * u)
            val th = k * 2.39996f + rng.r(-0.3f, 0.3f)
            val dx = sin(phi) * cos(th); val dy = cos(phi); val dz = sin(phi) * sin(th)
            val px = ccx + dx * R * 0.78f; val py = cy + dy * R * 0.62f; val pz = ccz + dz * R * 0.78f
            val sz = R * rng.r(0.85f, 1.15f)
            // cor: mais escuro embaixo/dentro, variação por cartão
            val lum = 0.72f + 0.38f * (dy * 0.5f + 0.5f) + rng.r(-0.08f, 0.08f)
            val cc = Color.rgb(((base shr 16 and 255) * lum).toInt().coerceIn(0, 255), ((base shr 8 and 255) * lum).toInt().coerceIn(0, 255), ((base and 255) * lum).toInt().coerceIn(0, 255))
            for (j in 0 until 2) {
                val ang = th + j * 1.5708f + rng.r(-0.2f, 0.2f)
                val rx = cos(ang) * sz * 0.5f; val rz = sin(ang) * sz * 0.5f
                val tilt = 0.25f * sz
                val y0 = py - sz * 0.45f; val y1 = py + sz * 0.55f
                // normal suave: do centro da copa para fora
                val nl = sqrt(dx * dx + dy * dy + dz * dz).coerceAtLeast(0.01f)
                val nx = dx / nl; val ny = dy / nl * 0.8f + 0.2f; val nz = dz / nl
                b.v(px - rx, y0, pz - rz, nx, ny, nz, cc, 0.02f, 0.98f); b.v(px + rx, y0, pz + rz, nx, ny, nz, cc, 0.98f, 0.98f); b.v(px + rx + dx * tilt, y1, pz + rz + dz * tilt, nx, ny, nz, cc, 0.98f, 0.02f)
                b.v(px - rx, y0, pz - rz, nx, ny, nz, cc, 0.02f, 0.98f); b.v(px + rx + dx * tilt, y1, pz + rz + dz * tilt, nx, ny, nz, cc, 0.98f, 0.02f); b.v(px - rx + dx * tilt, y1, pz - rz + dz * tilt, nx, ny, nz, cc, 0.02f, 0.02f)
            }
        }
        // Etapa 127: sombra projetada pelo sol (antes um disco translúcido embaixo que piscava)
        if (g.reg) Shade.tree(x, z, ccx, ccz, cy, R * 0.82f, R * 0.62f, y)
        // longe: tronco e bola
        g.f.m(Mt.PLAIN)
        g.f.cyl(x, y, z, 0.15f * s, 0.1f * s, H, trunk, true, 4)
        ball(g.f, ccx, cy, ccz, R * 0.95f, shade(base, -10), R * 0.75f, 6)
    }

    /** Palmeira: tronco curvo em gomos e folhas compridas caídas. */
    fun palm(g: Gen, x: Float, z: Float, s: Float, y: Float = CURB) {
        val b = g.b; val rng = g.rng
        val lean = rng.r(-0.35f, 0.35f); val leanZ = rng.r(-0.35f, 0.35f)
        val segs = 9; val hh = 6.5f * s
        var px = x; var pz = z; var py = y - 0.05f
        for (k in 1..segs) {
            val t = k.toFloat() / segs
            val nx = x + lean * hh * t * t; val nz = z + leanZ * hh * t * t; val ny = y + hh * t
            limb(b, px, py, pz, nx, ny, nz, 0.21f * s * (1f - 0.3f * (t - 1f / segs)), 0.21f * s * (1f - 0.3f * t), if (k % 2 == 0) C("#B59A7A") else C("#A88C6C"), 8)
            px = nx; pz = nz; py = ny
        }
        val tx = x + lean * hh; val tz = z + leanZ * hh; val ty = y + hh
        b.m(Mt.PLAIN)
        CityGeo.ball(b, tx, ty, tz, 0.35f * s, C("#6B5A2E"), 0.3f * s, 6)
        // Etapa 127: folhas de verdade — raque curva com dezenas de folíolos finos caindo dos dois lados
        val nf = 11
        for (k in 0 until nf) {
            val a = k * 2f * PI.toFloat() / nf + rng.r(-0.2f, 0.2f)
            val dx = cos(a); val dz = sin(a)
            val len = rng.r(3.0f, 3.9f) * s
            val up = rng.r(0.6f, 1.2f)
            val gc = C(rng.pick(arrayOf("#3E8E41", "#4C9A47", "#357F3A", "#58A34E")))
            val steps = 14
            var lx = tx; var ly = ty; var lz = tz
            for (st in 1..steps) {
                val t = st.toFloat() / steps
                val nx = tx + dx * len * t; val nz = tz + dz * len * t
                val ny = ty + up * s * t - 2.4f * s * t * t
                // raque
                val rw = 0.05f * s * (1f - t * 0.7f)
                q(b, P(lx - dz * rw, ly, lz + dx * rw) + P(lx + dz * rw, ly, lz - dx * rw) + P(nx + dz * rw, ny, nz - dx * rw) + P(nx - dz * rw, ny, nz + dx * rw), shade(gc, -25))
                // folíolos dos dois lados (compridos no meio da folha, curtos na ponta)
                val ll = (0.75f * sin(PI.toFloat() * min(1f, t * 1.1f)) + 0.12f) * s
                for (sd in floatArrayOf(-1f, 1f)) {
                    val px = -dz * sd; val pz = dx * sd
                    val ex = nx + px * ll * 0.85f + dx * ll * 0.35f; val ez = nz + pz * ll * 0.85f + dz * ll * 0.35f
                    val ey = ny - ll * 0.55f
                    val w = 0.045f * s
                    tri(b, P(nx - dx * w, ny, nz - dz * w) + P(nx + dx * w, ny, nz + dz * w) + P(ex, ey, ez), if (st % 2 == 0) gc else shade(gc, 12))
                    tri(b, P((nx + ex) / 2, (ny + ey) / 2 + 0.06f * s, (nz + ez) / 2) + P(nx + dx * w * 0.5f, ny, nz + dz * w * 0.5f) + P(ex, ey, ez), shade(gc, -12))
                }
                lx = nx; ly = ny; lz = nz
            }
        }
        // cachos de coco embaixo da copa
        for (k in 0 until 4) { val a = k * 1.7f; ball(b, tx + cos(a) * 0.22f * s, ty - 0.25f * s, tz + sin(a) * 0.22f * s, 0.12f * s, C("#7A5A2E"), 0.13f * s, 6) }
        if (g.reg) Shade.tree(x, z, tx, tz, ty - 0.6f * s, 2.6f * s, 0.5f * s, y, 0.22f)
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
        Shade.pole(x, z, 6.4f, 0.09f)
        b.m(Mt.METAL, 1f)
        b.cyl(x, y, z, 0.2f, 0.12f, 0.7f, C("#3B4046"), true, 8)
        b.cyl(x, y + 0.7f, z, 0.1f, 0.06f, 5.7f, C("#4A4F55"), true, 7)
        b.cyl(x, y + 0.68f, z, 0.14f, 0.14f, 0.06f, C("#2E3236"), true, 8)
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
            val d = fix - out * (th / 2 + 0.012f)   // Etapa 126: 1,2 cm da face (3 mm piscava de longe)
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

    /** Etapa 127: caixa "macia" (cantos chanfrados) — almofadas e estofados sem cara de tijolo. */
    fun soft(b: MB, l: L, lx: Float, y: Float, lz: Float, sx: Float, sy: Float, sz: Float, c: Int, r: Float = 0.035f) {
        val rr = min(r, min(sy, sz) * 0.45f)
        lb(b, l, lx, y, lz, sx, sy - 2 * rr, sz, c)
        lb(b, l, lx, y, lz, sx - 2 * min(rr, sx * 0.3f), sy, sz - 2 * rr, shade(c, 4))
    }

    /** Sofá: base com pés de madeira torneados, assentos com almofadas arredondadas, encosto inclinado em duas camadas, braços com rolo. */
    fun sofa(b: MB, l: L, w: Float, col: Int) {
        val y = FL
        b.m(Mt.FABRIC, 1f)
        val dark = shade(col, -16)
        soft(b, l, 0f, y + 0.25f, 0.02f, w - 0.1f, 0.22f, 0.86f, dark, 0.05f)
        val n = max(2, (w / 0.8f).toInt()); val cw = (w - 0.42f) / n
        for (k in 0 until n) {
            val cx = -w / 2 + 0.21f + cw * (k + 0.5f)
            soft(b, l, cx, y + 0.44f, -0.06f, cw - 0.025f, 0.17f, 0.68f, col, 0.06f)
            CityGeo.limb(b, l.wx(cx - cw / 2 + 0.03f, -0.39f), y + 0.44f, l.wz(cx - cw / 2 + 0.03f, -0.39f), l.wx(cx + cw / 2 - 0.03f, -0.39f), y + 0.44f, l.wz(cx + cw / 2 - 0.03f, -0.39f), 0.07f, 0.07f, col, 8)
            // encosto: almofada solta inclinada (duas peças escalonadas)
            soft(b, l, cx, y + 0.66f, 0.2f, cw - 0.04f, 0.3f, 0.18f, shade(col, 3), 0.07f)
            soft(b, l, cx, y + 0.86f, 0.27f, cw - 0.05f, 0.22f, 0.16f, shade(col, 6), 0.07f)
        }
        soft(b, l, 0f, y + 0.66f, 0.38f, w - 0.1f, 0.62f, 0.12f, dark, 0.04f)
        for (s in floatArrayOf(-1f, 1f)) {
            soft(b, l, s * (w / 2 - 0.11f), y + 0.42f, 0.02f, 0.2f, 0.4f, 0.86f, shade(col, -6), 0.05f)
            CityGeo.limb(b, l.wx(s * (w / 2 - 0.11f), -0.4f), y + 0.64f, l.wz(s * (w / 2 - 0.11f), -0.4f), l.wx(s * (w / 2 - 0.11f), 0.42f), y + 0.64f, l.wz(s * (w / 2 - 0.11f), 0.42f), 0.1f, 0.1f, shade(col, -3), 8)
        }
        // almofadas decorativas (uma de cada lado, cores que combinam)
        val pc = arrayOf(C("#F2E8CF"), mix(col, C("#FFFFFF"), 0.45f), C("#C9A227"))
        for ((i, s) in floatArrayOf(-1f, 1f).withIndex()) soft(b, l, s * (w / 2 - 0.42f), y + 0.68f, 0.12f, 0.4f, 0.38f, 0.12f, pc[(i + w.toInt()) % 3], 0.05f)
        b.m(Mt.WOOD, 1f)
        for (s in floatArrayOf(-1f, 1f)) for (t in floatArrayOf(-0.34f, 0.36f)) lcyl(b, l, s * (w / 2 - 0.12f), y, t, 0.025f, 0.04f, 0.14f, C("#3E2C23"), 7)
    }

    /** Poltrona: estofado com braços em rolo, almofada solta, encosto alto e pés palito. */
    fun armchair(b: MB, l: L, col: Int) {
        val y = FL
        b.m(Mt.FABRIC, 1f)
        soft(b, l, 0f, y + 0.26f, 0.02f, 0.8f, 0.2f, 0.8f, shade(col, -14), 0.05f)
        soft(b, l, 0f, y + 0.44f, -0.06f, 0.52f, 0.16f, 0.62f, col, 0.06f)
        CityGeo.limb(b, l.wx(-0.24f, -0.36f), y + 0.44f, l.wz(-0.24f, -0.36f), l.wx(0.24f, -0.36f), y + 0.44f, l.wz(0.24f, -0.36f), 0.07f, 0.07f, col, 8)
        soft(b, l, 0f, y + 0.72f, 0.32f, 0.78f, 0.66f, 0.16f, shade(col, -6), 0.06f)
        soft(b, l, 0f, y + 0.74f, 0.21f, 0.5f, 0.46f, 0.1f, shade(col, 4), 0.05f)
        for (s in floatArrayOf(-1f, 1f)) {
            soft(b, l, s * 0.33f, y + 0.44f, 0.02f, 0.14f, 0.34f, 0.8f, shade(col, -6), 0.04f)
            CityGeo.limb(b, l.wx(s * 0.33f, -0.38f), y + 0.62f, l.wz(s * 0.33f, -0.38f), l.wx(s * 0.33f, 0.38f), y + 0.62f, l.wz(s * 0.33f, 0.38f), 0.08f, 0.08f, shade(col, -2), 8)
        }
        b.m(Mt.WOOD, 1f)
        for (s in floatArrayOf(-0.32f, 0.32f)) for (t in floatArrayOf(-0.32f, 0.32f)) lcyl(b, l, s, y, t, 0.02f, 0.035f, 0.16f, C("#4A3428"), 7)
    }

    fun rug(b: MB, x0: Float, z0: Float, x1: Float, z1: Float, col: Int) {
        b.m(Mt.RUG, 0.5f)
        b.box((x0 + x1) / 2, FL + 0.006f, (z0 + z1) / 2, x1 - x0, 0.012f, z1 - z0, col)
    }

    /** Mesa de centro: tampo com borda, prateleira de baixo com revistas, bandeja, vaso com flores e livros. */
    fun coffeeTable(b: MB, l: L, wood: Int) {
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, FL + 0.41f, 0f, 1.1f, 0.035f, 0.6f, wood)
        lb(b, l, 0f, FL + 0.385f, 0f, 1.06f, 0.02f, 0.56f, shade(wood, -12))
        lb(b, l, 0f, FL + 0.12f, 0f, 0.98f, 0.025f, 0.5f, shade(wood, -6))
        for (s in floatArrayOf(-0.5f, 0.5f)) for (t in floatArrayOf(-0.25f, 0.25f)) lcyl(b, l, s, FL, t, 0.022f, 0.03f, 0.39f, shade(wood, -22), 7)
        b.m(Mt.PLAIN)
        lb(b, l, -0.2f, FL + 0.14f, 0.05f, 0.3f, 0.02f, 0.22f, C("#C0392B")); lb(b, l, -0.18f, FL + 0.155f, 0.04f, 0.28f, 0.012f, 0.2f, C("#ECEFF1"))
        lb(b, l, 0.18f, FL + 0.433f, 0.04f, 0.26f, 0.01f, 0.2f, C("#263238")); lb(b, l, 0.2f, FL + 0.443f, 0.03f, 0.22f, 0.01f, 0.17f, C("#E3C567"))
        b.m(Mt.METAL, 1f); lb(b, l, -0.25f, FL + 0.435f, -0.02f, 0.38f, 0.015f, 0.26f, C("#B08D57"))
        b.m(Mt.PLAIN)
        lcyl(b, l, -0.25f, FL + 0.44f, -0.02f, 0.045f, 0.035f, 0.14f, C("#FFFFFF"), 10)
        for (k in 0 until 4) lsph(b, l, -0.25f + cos(k * 1.6f) * 0.04f, FL + 0.6f + (k % 2) * 0.03f, -0.02f + sin(k * 1.6f) * 0.04f, 0.035f, C(arrayOf("#E57373", "#FFF176", "#F48FB1", "#FFFFFF")[k]), 0.03f, 5)
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
        for (k in 0..3) CityInt.goods(b, l.wx(0f, 0.03f), FL + 0.045f + k * 0.48f, l.wz(0f, 0.03f), if (l.alongX) 0.92f else 0.24f, 0.4f, if (l.alongX) 0.24f else 0.92f, C("#FFFFFF"), Mt.BOOKS)
    }

    /**
     * Etapa 127: planta de vaso com folhas de verdade (cartões com a textura de folha, com recorte) em vez de bolas verdes.
     * Vaso com borda, terra e pedrinhas; tipos: costela-de-adão, palmeira-areca, ficus, espada-de-são-jorge.
     */
    fun plant(b: MB, x: Float, z: Float, s: Float, rng: City.Rng, y: Float = FL) {
        val pot = rng.pick(arrayOf(C("#D9D2C5"), C("#3A3A3A"), C("#B5643C"), C("#FFFFFF"), C("#5B6F5A"), C("#C9B79C")))
        b.m(Mt.STONE, 1.5f)
        b.cyl(x, y, z, 0.15f * s, 0.2f * s, 0.4f * s, pot, true, 14)
        b.cyl(x, y + 0.38f * s, z, 0.215f * s, 0.215f * s, 0.05f * s, shade(pot, -10), true, 14)
        b.m(Mt.PLAIN); b.cyl(x, y + 0.42f * s, z, 0.19f * s, 0.19f * s, 0.012f, C("#4E3B2A"), true, 12)
        for (k in 0 until 5) CityGeo.ball(b, x + cos(k * 1.3f) * 0.1f * s, y + 0.435f * s, z + sin(k * 1.3f) * 0.1f * s, 0.025f * s, C("#BDB5A6"), 0.015f * s, 4)
        val kind = rng.i(4)
        val base = y + 0.43f * s
        if (kind == 3) {
            // espada-de-são-jorge: folhas retas listradas
            b.m(Mt.PLAIN)
            for (k in 0 until 9) {
                val a = k * 0.7f + rng.r(-0.2f, 0.2f); val h = rng.r(0.5f, 0.85f) * s
                val ox = cos(a) * 0.06f * s; val oz = sin(a) * 0.06f * s
                val tx = ox * 2.2f; val tz = oz * 2.2f
                val w = 0.035f * s
                val c = if (k % 2 == 0) C("#3F6B3A") else C("#56804A")
                q(b, P(x + ox - oz / 0.06f * w * 0.016f - w, base, z + oz) + P(x + ox + w, base, z + oz) + P(x + tx + w * 0.3f, base + h, z + tz) + P(x + tx - w * 0.3f, base + h, z + tz), c)
                q(b, P(x + ox, base, z + oz - w) + P(x + ox, base, z + oz + w) + P(x + tx, base + h, z + tz + w * 0.3f) + P(x + tx, base + h, z + tz - w * 0.3f), shade(c, -12))
            }
            return
        }
        // caules
        b.m(Mt.PLAIN)
        val n = when (kind) { 0 -> 7; 1 -> 9; else -> 11 }
        val tips = ArrayList<FloatArray>()
        for (k in 0 until n) {
            val a = k * 2.39996f + rng.r(-0.3f, 0.3f)
            val rr = when (kind) { 0 -> rng.r(0.22f, 0.4f); 1 -> rng.r(0.18f, 0.36f); else -> rng.r(0.08f, 0.24f) } * s
            val hh = when (kind) { 0 -> rng.r(0.35f, 0.75f); 1 -> rng.r(0.7f, 1.25f); else -> rng.r(0.6f, 1.15f) } * s
            val tx = x + cos(a) * rr; val tz = z + sin(a) * rr; val ty = base + hh
            CityGeo.limb(b, x + cos(a) * 0.03f * s, base, z + sin(a) * 0.03f * s, tx, ty, tz, 0.012f * s, 0.006f * s, C(if (kind == 2) "#5D4632" else "#4E7A3A"), 4)
            tips.add(floatArrayOf(tx, ty, tz, a))
        }
        // folhas: cartões cruzados com a textura (folhagem densa no ficus, folhas grandes na costela e na areca)
        b.m(if (kind == 2) Mt.LEAF else Mt.LEAFB, 1f)
        val gc = C(when (kind) { 0 -> "#3E7D3A"; 1 -> "#5E9A45"; else -> "#4A8A3E" })
        for (t in tips) {
            val sz = when (kind) { 0 -> 0.42f; 1 -> 0.55f; else -> 0.34f } * s
            for (j in 0 until 2) {
                val ang = t[3] + j * 1.5708f
                val rx = cos(ang) * sz * 0.5f; val rz = sin(ang) * sz * 0.5f
                val y0 = t[1] - sz * 0.45f; val y1 = t[1] + sz * 0.45f
                val dx = cos(t[3]) * sz * 0.25f; val dz = sin(t[3]) * sz * 0.25f
                val nx = cos(t[3]); val nz = sin(t[3])
                val cc = shade(gc, rng.r(-10f, 14f).toInt())
                b.v(t[0] - rx, y0, t[2] - rz, nx, 0.6f, nz, cc, 0.02f, 0.98f); b.v(t[0] + rx, y0, t[2] + rz, nx, 0.6f, nz, cc, 0.98f, 0.98f); b.v(t[0] + rx + dx, y1, t[2] + rz + dz, nx, 0.6f, nz, cc, 0.98f, 0.02f)
                b.v(t[0] - rx, y0, t[2] - rz, nx, 0.6f, nz, cc, 0.02f, 0.98f); b.v(t[0] + rx + dx, y1, t[2] + rz + dz, nx, 0.6f, nz, cc, 0.98f, 0.02f); b.v(t[0] - rx + dx, y1, t[2] - rz + dz, nx, 0.6f, nz, cc, 0.02f, 0.02f)
            }
        }
        if (kind == 2) for (k in 0 until 4) {
            // copa do ficus: mais cartões no alto
            val a = k * 1.57f; val px = x + cos(a) * 0.12f * s; val pz = z + sin(a) * 0.12f * s; val py = base + 1.0f * s
            val sz = 0.42f * s
            for (j in 0 until 2) {
                val ang = a + j * 1.5708f; val rx = cos(ang) * sz * 0.5f; val rz = sin(ang) * sz * 0.5f
                b.v(px - rx, py - sz * 0.4f, pz - rz, cos(a), 0.6f, sin(a), gc, 0.02f, 0.98f); b.v(px + rx, py - sz * 0.4f, pz + rz, cos(a), 0.6f, sin(a), gc, 0.98f, 0.98f); b.v(px + rx, py + sz * 0.5f, pz + rz, cos(a), 0.6f, sin(a), gc, 0.98f, 0.02f)
                b.v(px - rx, py - sz * 0.4f, pz - rz, cos(a), 0.6f, sin(a), gc, 0.02f, 0.98f); b.v(px + rx, py + sz * 0.5f, pz + rz, cos(a), 0.6f, sin(a), gc, 0.98f, 0.02f); b.v(px - rx, py + sz * 0.5f, pz - rz, cos(a), 0.6f, sin(a), gc, 0.02f, 0.02f)
            }
        }
        b.m(Mt.PLAIN)
    }

    /** Luminária de piso em arco: base de mármore, haste curva, cúpula. */
    fun floorLamp(b: MB, x: Float, z: Float) {
        b.m(Mt.STONE, 0.8f)
        b.cyl(x, FL, z, 0.17f, 0.18f, 0.06f, C("#E8E4DC"), true, 14)
        b.m(Mt.METAL, 1f)
        var px = x; var py = FL + 0.06f
        for (k in 1..6) { val t = k / 6f; val nx = x + 0.45f * t * t; val ny = FL + 0.06f + 1.55f * kotlin.math.sin(t * 1.4f) / kotlin.math.sin(1.4f); CityGeo.limb(b, px, py, z, nx, ny, z, 0.014f, 0.014f, C("#B8A06A"), 5); px = nx; py = ny }
        b.m(Mt.FABRIC, 1f)
        b.cyl(px, py - 0.25f, z, 0.24f, 0.13f, 0.24f, C("#F3E9D2"), true, 16)
        b.m(Mt.PLAIN); b.cyl(px, py - 0.25f, z, 0.2f, 0.2f, 0.01f, C("#FFF6DC"), false, 14)
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
        val dk = shade(wood, -15)
        b.m(Mt.WOOD, 1f)
        // assento com borda e pés levemente cônicos, travessas
        lb(b, l, 0f, y + 0.445f, 0f, 0.44f, 0.035f, 0.43f, wood)
        for (s in floatArrayOf(-0.185f, 0.185f)) for (t in floatArrayOf(-0.18f, 0.18f)) lb(b, l, s, y + 0.215f, t, 0.035f, 0.43f, 0.035f, dk)
        for (s in floatArrayOf(-0.185f, 0.185f)) lb(b, l, s, y + 0.16f, 0f, 0.02f, 0.025f, 0.36f, dk)
        lb(b, l, 0f, y + 0.16f, 0.18f, 0.36f, 0.025f, 0.02f, dk)
        // encosto: dois montantes curvos + travessa alta + três réguas
        for (s in floatArrayOf(-0.185f, 0.185f)) CityGeo.limb(b, l.wx(s, 0.19f), y + 0.46f, l.wz(s, 0.19f), l.wx(s, 0.23f), y + 0.9f, l.wz(s, 0.23f), 0.02f, 0.018f, dk, 5)
        lb(b, l, 0f, y + 0.86f, 0.22f, 0.4f, 0.09f, 0.025f, wood)
        for (k in -1..1) lb(b, l, k * 0.1f, y + 0.66f, 0.205f, 0.035f, 0.3f, 0.018f, wood)
        b.m(Mt.FABRIC, 1f)
        soft(b, l, 0f, y + 0.485f, -0.01f, 0.4f, 0.045f, 0.38f, fab, 0.015f)
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

    /** Mesa de trabalho: gaveteiro, monitor com suporte, teclado, mouse, luminária, papéis, caneca, porta-lápis. */
    fun desk(b: MB, l: L, wood: Int, fab: Int) {
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, FL + 0.74f, 0f, 1.3f, 0.035f, 0.66f, wood)
        lb(b, l, -0.62f, FL + 0.37f, 0f, 0.04f, 0.72f, 0.62f, shade(wood, -15))
        lb(b, l, 0.38f, FL + 0.36f, 0f, 0.48f, 0.7f, 0.6f, shade(wood, -8))   // gaveteiro
        b.m(Mt.PLAIN)
        for (k in 0 until 3) { lb(b, l, 0.38f, FL + 0.15f + k * 0.21f, -0.302f, 0.44f, 0.19f, 0.006f, shade(wood, -2)); lb(b, l, 0.38f, FL + 0.22f + k * 0.21f, -0.31f, 0.12f, 0.015f, 0.012f, C("#9E9E9E")) }
        lb(b, l, 0f, FL + 0.55f, 0.3f, 1.2f, 0.36f, 0.015f, shade(wood, -18))   // painel de fundo
        b.m(Mt.METAL, 1f)
        lb(b, l, 0.05f, FL + 0.765f, 0.15f, 0.22f, 0.015f, 0.18f, C("#2A2A2A"))
        lb(b, l, 0.05f, FL + 0.86f, 0.17f, 0.04f, 0.2f, 0.03f, C("#2A2A2A"))
        lb(b, l, 0.05f, FL + 1.08f, 0.16f, 0.62f, 0.36f, 0.03f, C("#151515"))
        b.m(Mt.PLAIN)
        lb(b, l, 0.05f, FL + 1.085f, 0.143f, 0.58f, 0.32f, 0.004f, C("#2F5D8C"), false)
        lb(b, l, -0.08f, FL + 1.13f, 0.14f, 0.24f, 0.14f, 0.003f, C("#E8F1FA"), false); lb(b, l, 0.2f, FL + 1.04f, 0.14f, 0.2f, 0.18f, 0.003f, C("#9FC3E6"), false)
        b.m(Mt.METAL, 1f)
        lb(b, l, 0.02f, FL + 0.765f, -0.1f, 0.44f, 0.018f, 0.15f, C("#303030"))
        b.m(Mt.PLAIN); lb(b, l, 0.02f, FL + 0.776f, -0.1f, 0.4f, 0.004f, 0.11f, C("#555555"))
        lsph(b, l, 0.33f, FL + 0.77f, -0.1f, 0.03f, C("#303030"), 0.018f, 6)
        lb(b, l, -0.38f, FL + 0.762f, -0.02f, 0.22f, 0.006f, 0.3f, C("#FAFAFA")); lb(b, l, -0.36f, FL + 0.768f, -0.04f, 0.21f, 0.006f, 0.29f, C("#FFFDE7"))
        lcyl(b, l, -0.5f, FL + 0.758f, 0.12f, 0.04f, 0.04f, 0.1f, C("#C62828"), 8)
        lcyl(b, l, -0.55f, FL + 0.758f, -0.15f, 0.035f, 0.035f, 0.1f, C("#37474F"), 8)
        for (k in 0 until 3) CityGeo.limb(b, l.wx(-0.55f + (k - 1) * 0.012f, -0.15f), FL + 0.8f, l.wz(-0.55f + (k - 1) * 0.012f, -0.15f), l.wx(-0.55f + (k - 1) * 0.02f, -0.15f), FL + 0.92f, l.wz(-0.55f + (k - 1) * 0.02f, -0.15f), 0.005f, 0.005f, C(arrayOf("#1565C0", "#F9A825", "#C62828")[k]), 3)
        // luminária de mesa articulada
        b.m(Mt.METAL, 1f)
        lcyl(b, l, -0.52f, FL + 0.758f, 0.2f, 0.07f, 0.07f, 0.02f, C("#212121"), 10)
        CityGeo.limb(b, l.wx(-0.52f, 0.2f), FL + 0.77f, l.wz(-0.52f, 0.2f), l.wx(-0.45f, 0.1f), FL + 1.12f, l.wz(-0.45f, 0.1f), 0.01f, 0.01f, C("#212121"), 4)
        CityGeo.limb(b, l.wx(-0.45f, 0.1f), FL + 1.12f, l.wz(-0.45f, 0.1f), l.wx(-0.32f, -0.05f), FL + 1.08f, l.wz(-0.32f, -0.05f), 0.01f, 0.01f, C("#212121"), 4)
        lcyl(b, l, -0.32f, FL + 1.0f, -0.05f, 0.07f, 0.03f, 0.08f, C("#212121"), 10)
        officeChair(b, L(l.wx(0f, -0.65f), l.wz(0f, -0.65f), -l.fx, -l.fz), fab)
    }

    /** Cadeira de escritório: base estrela de 5 pontas com rodízios, pistão, assento e encosto estofados, braços. */
    fun officeChair(b: MB, l: L, fab: Int) {
        b.m(Mt.METAL, 1f)
        val cx = l.wx(0f, 0f); val cz = l.wz(0f, 0f)
        for (k in 0 until 5) {
            val a = k * 1.2566f + 0.3f
            val ex = cx + cos(a) * 0.3f; val ez = cz + sin(a) * 0.3f
            CityGeo.limb(b, cx, FL + 0.1f, cz, ex, FL + 0.07f, ez, 0.022f, 0.016f, C("#1E1E1E"), 4)
            CityGeo.ball(b, ex, FL + 0.035f, ez, 0.03f, C("#111111"), 0.035f, 5)
        }
        lcyl(b, l, 0f, FL + 0.09f, 0f, 0.04f, 0.04f, 0.08f, C("#1E1E1E"), 8)
        lcyl(b, l, 0f, FL + 0.17f, 0f, 0.025f, 0.025f, 0.26f, C("#9E9E9E"), 8)
        lb(b, l, 0f, FL + 0.43f, 0f, 0.3f, 0.03f, 0.3f, C("#1E1E1E"))
        b.m(Mt.FABRIC, 1f)
        soft(b, l, 0f, FL + 0.48f, -0.01f, 0.5f, 0.08f, 0.48f, fab, 0.03f)
        CityGeo.limb(b, l.wx(0f, 0.18f), FL + 0.45f, l.wz(0f, 0.18f), l.wx(0f, 0.25f), FL + 0.62f, l.wz(0f, 0.25f), 0.03f, 0.03f, C("#1E1E1E"), 5)
        soft(b, l, 0f, FL + 0.86f, 0.26f, 0.46f, 0.5f, 0.07f, fab, 0.03f)
        soft(b, l, 0f, FL + 0.75f, 0.23f, 0.36f, 0.14f, 0.04f, shade(fab, -10), 0.02f)   // apoio lombar
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-0.26f, 0.26f)) { lb(b, l, s, FL + 0.56f, 0.04f, 0.03f, 0.16f, 0.03f, C("#1E1E1E")); lb(b, l, s, FL + 0.65f, 0f, 0.06f, 0.025f, 0.26f, C("#2A2A2A")) }
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
    fun house(g: Gen, x0: Float, x1: Float, fz0: Float, fz: Float, depth: Float, style: Int, forSale: Boolean, mansion: Boolean = false, gar: Int = -1) {
        val rng = g.rng
        val lotW = x1 - x0
        val wall = C(rng.pick(WALLS)); val roof = C(rng.pick(ROOFS)); val trim = C("#FFFFFF")
        val wood = rng.pick(WOODS)
        // Etapa 129: todas as casas de uma rua com a mesma frente (recuo) e os mesmos fundos; larguras iguais quando o lote deixa
        val hw = if (mansion) min(lotW - 9.6f, 21f.also { rng.r(18f, 24f) }) else min(lotW - 4.3f, 9.8f.also { rng.r(8.5f, 11f) })
        var hd = if (mansion) 14f.also { rng.r(13f, 15f) } else 9f.also { rng.r(8.2f, 10f) }
        var set = if (mansion) 10f.also { rng.r(9f, 11f) } else 6f.also { rng.r(5.5f, 7f) }
        // Etapa 127: a casa (e o quintal dos fundos) cabem no lote — antes a piscina/árvores do fundo invadiam a casa do lote de trás
        val pool = mansion && set + hd + 10.5f <= depth   // piscina só se o lote for fundo o bastante
        val back = if (pool) 10.5f else 4.6f
        if (set + hd + back > depth) { val k = (depth - back) / (set + hd); set *= max(0.75f, k); hd = min(hd, depth - back - set) }
        val sideGarRnd = rng.chance(0.5f)
        val sideGar = if (gar >= 0) gar == 0 else sideGarRnd
        // casa + entrada de carros formam um conjunto centralizado no lote (a casa fica 1,8 m para o lado oposto à garagem)
        val hcx = (x0 + x1) / 2 + (if (mansion) 0f else (if (sideGar) -1.8f else 1.8f))
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
        val gx = if (mansion) hx1 + (x1 - hx1) / 2f else if (sideGar) hx1 + 2.0f else hx0 - 2.0f
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
        val sOps = arrayListOf(Op((hz0 + hz1) / 2 + hd * 0.23f, 1.1f, FL + 1.1f, winT, false), Op((hz0 + hz1) / 2 - hd * 0.23f, 1.1f, FL + 1.1f, winT, false))
        wall(g, 1, hx0, hz0 + 0.1f, hz1 - 0.1f, FL, topY, -1, sOps, wall, inC, matOut)
        wall(g, 1, hx1, hz0 + 0.1f, hz1 - 0.1f, FL, topY, 1, sOps, wall, inC, matOut)
        // paredes como sólidos (a porta fica aberta)
        g.solid(hx0 - 0.2f, hz0 - 0.2f, hx0 + 0.2f, hz1 + 0.2f); g.solid(hx1 - 0.2f, hz0 - 0.2f, hx1 + 0.2f, hz1 + 0.2f)
        g.solid(hx0, zb - 0.2f, hx1, zb + 0.2f)
        g.solid(hx0, zf - 0.2f, hcx - 0.62f, zf + 0.2f); g.solid(hcx + 0.62f, zf - 0.2f, hx1, zf + 0.2f)
        // Etapa 128: porta de verdade (abre quando chega perto) e luminária da entrada
        g.door(name, hcx, zf, fz, 1.1f, 2.2f, 0.2f)
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
        val fenceType = if (mansion) 2 else (style % 3).also { rng.i(3) }
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
        // uma árvore no fundo e outra na frente, sempre no canto oposto à garagem
        rng.chance(0.7f); rng.r(0.9f, 1.3f); rng.chance(0.6f); rng.r(0.7f, 1.0f)
        tree(g, if (sideGar) x0 + 2.2f else x1 - 2.2f, Z(depth - 3.5f), 1.1f)
        tree(g, if (sideGar) x0 + 1.8f else x1 - 1.8f, Z(2.0f), 0.85f)
        if (forSale) {
            b.m(Mt.WOOD, 1f); b.box(hcx - 2.2f, CURB + 0.6f, Z(1.4f), 0.08f, 1.2f, 0.08f, C("#5D4037"))
            sign(b, hcx - 2.2f, CURB + 1.0f, Z(1.4f) + fz * 0.06f, 0f, fz, 1.4f, 0.32f, City.signIdx("À VENDA"))
        }
        // quintal dos fundos: churrasqueira / piscina (mansão)
        if (pool) {
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
        val fm0 = if (kind == 3) Mt.TILE else rng.pick(arrayOf(Mt.TILE, Mt.STONE, Mt.FLOOR_L))
        val fl0 = shop?.let { CityInt.floor(it) }
        A.m(fl0?.first ?: fm0, fl0?.third ?: 0.6f); A.box(cx, FL - 0.005f, cz, w - 0.3f, 0.012f, d - 0.3f, fl0?.second ?: C("#F2F2F2"))
        // térreo: vitrine de vidro na frente com porta, paredes nos outros lados
        val fOps = ArrayList<Op>()
        val nv = max(1, (w / 4f).toInt()).let { if (it % 2 == 0) it + 1 else it }
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
        g.door(shop ?: "PRÉDIO", door.c, zf, fz, 1.8f, 2.6f, 0.3f)
        g.solid(x0 - 0.2f, z0 - 0.2f, x0 + 0.25f, z1 + 0.2f); g.solid(x1 - 0.25f, z0 - 0.2f, x1 + 0.2f, z1 + 0.2f); g.solid(x0, zb - 0.25f, x1, zb + 0.25f)
        g.solid(x0, zf - 0.25f, door.c - 0.95f, zf + 0.25f); g.solid(door.c + 0.95f, zf - 0.25f, x1, zf + 0.25f)
        // interior do térreo
        if (shop == null || !shopInterior(g, shop, x0 + 0.3f, z0 + 0.3f, x1 - 0.3f, z1 - 0.3f, zf, fz, door.c)) interior(g, kind, x0 + 0.3f, z0 + 0.3f, x1 - 0.3f, z1 - 0.3f, zf, fz, door.c)
        // marquise, letreiro
        H.m(Mt.METAL, 1f)
        H.box(cx, FL + gh - 0.9f, Z(set - 1.0f), w - 0.4f, 0.14f, 2.0f, C("#4A4F55"))
        H.m(Mt.PLAIN)
        H.box(cx, FL + gh - 0.98f, Z(set - 1.0f), w - 0.6f, 0.02f, 1.8f, C("#FFF6D8"), false)
        if (shop != null) {
            val si = Signs.pick(shop, rng)
            val sp = Signs.spec(si)
            // letreiro em pé na borda da marquise (como nas fachadas de verdade); a faixa da marquise ganha frente mais alta
            H.m(Mt.METAL, 1f); H.box(cx, FL + gh - 0.95f, Z(set - 2.0f), w - 0.4f, 0.38f, 0.06f, C("#3A3F45"))
            Signs.mount(H, si, cx, FL + gh - 0.8f, Z(set - 2.0f), fz, min(w - 2f, 9f), if (sp.style == Signs.LETTERS) 0.9f else 0.75f, 0.04f)
            if (sp.blade >= 0) Signs.blade(H, sp.blade, x0 + 0.6f, FL + gh + 0.4f, Z(set), fz, 0.9f)
        }
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
        H.m(Mt.STONE, 0.5f); H.box(cx, topY + 0.09f, cz, w - 0.2f, 0.18f, d - 0.2f, C("#9A9A9A"))   // Etapa 126: laje mais alta (não briga com o topo da fachada)
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

    /** Cor das paredes de dentro, por tipo de loja. */
    fun innerColor(n: String): Int = C(when (n) {
        "PADARIA" -> "#F6E6CC"; "FARMÁCIA" -> "#F4FBF6"; "CAFÉ" -> "#E9DCCB"; "PET SHOP" -> "#DDF1FB"; "SALÃO DE BELEZA" -> "#FBE4EE"
        "PIZZARIA" -> "#F3DDC9"; "FLORICULTURA" -> "#EAF5DF"; "SORVETERIA" -> "#FDE7F0"; "ACADEMIA" -> "#3B4148"; "LANCHONETE" -> "#FFF1C9"
        "ÓTICA" -> "#F7F7F7"; "MODA" -> "#F2EFEA"; "HAMBÚRGUER" -> "#3D2A22"; "BARBEARIA" -> "#2F3A40"; "PAPELARIA" -> "#FFF8D6"
        "AÇAÍ" -> "#EADCF5"; "MERCADINHO" -> "#F5F5F0"; "SUSHI" -> "#EFE3CF"; "ELETRÔNICOS" -> "#E8EEF6"; "LIVRARIA" -> "#EDE2D0"
        else -> "#F7F3EC" })

    /**
     * Etapa 125: interior próprio de cada tipo de loja (balcão, vitrines, mesas, prateleiras e objetos diferentes).
     * Devolve false para tipos sem interior especial (usa o genérico).
     */
    fun shopInterior(g: Gen, name: String, x0: Float, z0: Float, x1: Float, z1: Float, zf: Float, fz: Float, doorX: Float): Boolean {
        if (CityInt.build(g, name, x0, z0, x1, z1, zf, fz, doorX)) return true   // Etapa 126: interiores próprios e realistas
        val A = g.A; val rng = g.rng
        val w = x1 - x0; val cx = (x0 + x1) / 2; val cz = (z0 + z1) / 2
        val inF = -fz
        val back = if (fz > 0) z0 else z1
        fun Zi(d: Float) = zf + inF * d                      // d metros para dentro a partir da porta
        val depth = abs(back - zf)
        // luminárias e forro (somem ao entrar)
        g.H.m(Mt.PLAIN)
        var lx = x0 + 1.5f
        while (lx < x1 - 1f) { g.H.box(lx, FL + 4.2f, cz, 0.9f, 0.04f, 0.9f, C("#FFFDF2"), false); lx += 2.6f }
        g.H.m(Mt.PLASTER, 0.5f); g.H.box(cx, FL + 4.35f, cz, w, 0.1f, depth, C("#F4F4F4"))
        val wood = rng.pick(WOODS)
        fun backCounter(col: Int, wd: Float = min(w - 2f, 5f)) {
            counter(A, L(cx, Zi(depth - 1.3f), 0f, fz), wd, col, rng, false)
            g.solid(cx - wd / 2, min(Zi(depth - 1.7f), Zi(depth - 0.9f)), cx + wd / 2, max(Zi(depth - 1.7f), Zi(depth - 0.9f)))
        }
        fun wallShelves(col: Int, items: Boolean) {
            // prateleiras nas duas paredes laterais
            for (sx in floatArrayOf(x0 + 0.3f, x1 - 0.3f)) {
                var d = 1.5f
                while (d < depth - 2.4f) {
                    val l = L(sx, Zi(d), if (sx < cx) 1f else -1f, 0f)
                    A.m(Mt.WOOD, 1f); lb(A, l, 0f, FL + 1.1f, 0.12f, 1.6f, 2.2f, 0.04f, col)
                    for (k in 0..3) lb(A, l, 0f, FL + 0.3f + k * 0.55f, 0f, 1.6f, 0.04f, 0.38f, col)
                    if (items) for (k in 0..3) CityInt.goods(A, l.wx(0f, 0.02f), FL + 0.32f + k * 0.55f, l.wz(0f, 0.02f), if (l.alongX) 1.56f else 0.3f, 0.3f, if (l.alongX) 0.3f else 1.56f)
                    d += 1.7f
                }
                g.solid(sx - 0.45f, min(Zi(1.4f), Zi(depth - 2.3f)), sx + 0.45f, max(Zi(1.4f), Zi(depth - 2.3f)))
            }
        }
        fun tables(n: Int, round: Boolean) {
            // Etapa 129: colunas simétricas em torno do centro e corredor da porta sempre livre
            var i = 0
            val nc = max(1, ((w - 2.4f) / 2.6f).toInt())
            for (j in 0 until nc) {
                val x = cx + (j - (nc - 1) / 2f) * 2.6f
                var d = 1.8f
                while (d < depth - 3.2f && i < n) {
                    if (abs(x - doorX) < 1.5f && d < 3.4f) { d += 2.4f; continue }
                    if (round) cafeTable(A, x, Zi(d), rng) else { diningSet(A, L(x, Zi(d), 0f, fz), wood, 4, rng.pick(FABRICS)) }
                    g.solid(x - 0.5f, Zi(d) - 0.5f, x + 0.5f, Zi(d) + 0.5f)
                    d += 2.4f; i++
                }
            }
        }
        when (name) {
            "PADARIA" -> {
                // vitrine refrigerada de pães e doces, prateleira de pães atrás, mesinhas
                counter(A, L(cx, Zi(depth - 1.6f), 0f, fz), min(w - 2f, 5.5f), C("#8D6E63"), rng, true)
                g.solid(cx - 2.8f, min(Zi(depth - 2f), Zi(depth - 1.2f)), cx + 2.8f, max(Zi(depth - 2f), Zi(depth - 1.2f)))
                val l = L(cx, back - inF * 0.25f, 0f, fz)
                A.m(Mt.WOOD, 1f); lb(A, l, 0f, FL + 1.2f, 0.05f, min(w - 2f, 5f), 2.0f, 0.1f, C("#6D4C41"))
                for (k in 0..2) { lb(A, l, 0f, FL + 0.6f + k * 0.55f, -0.12f, min(w - 2f, 5f), 0.04f, 0.35f, C("#8D6E63"))
                    A.m(Mt.PLAIN); for (i in 0 until 9) ball(A, l.wx(-2.1f + i * 0.52f, -0.12f), FL + 0.7f + k * 0.55f, l.wz(-2.1f + i * 0.52f, -0.12f), 0.13f, rng.pick(arrayOf(C("#C68A4A"), C("#E0B070"), C("#A86A30"))), 0.08f, 6); A.m(Mt.WOOD, 1f) }
                tables(4, true)
            }
            "FARMÁCIA", "MERCADINHO", "PAPELARIA" -> {
                wallShelves(if (name == "FARMÁCIA") C("#FFFFFF") else C("#E0E0E0"), true)
                // gôndola no meio
                val gw = min(3.4f, w - 4.6f)   // Etapa 129: sobra ≥ 1,15 m de cada lado da gôndola
                if (gw >= 1.2f) { shelf(A, cx, Zi(depth * 0.45f), gw, rng); g.solid(cx - gw / 2, Zi(depth * 0.45f) - 0.4f, cx + gw / 2, Zi(depth * 0.45f) + 0.4f) }
                backCounter(C("#FFFFFF"), 3f)
                if (name == "FARMÁCIA") { A.m(Mt.PLAIN); val l = L(cx, back - inF * 0.12f, 0f, fz); lb(A, l, 0f, FL + 2.8f, 0f, 0.9f, 0.3f, 0.04f, C("#1E9E5A"), false); lb(A, l, 0f, FL + 2.8f, 0f, 0.3f, 0.9f, 0.04f, C("#1E9E5A"), false) }
            }
            "CAFÉ", "SORVETERIA", "AÇAÍ", "LANCHONETE" -> {
                counter(A, L(cx, Zi(depth - 1.6f), 0f, fz), min(w - 2f, 5f), C(if (name == "CAFÉ") "#4E342E" else if (name == "AÇAÍ") "#6A1B9A" else "#FFFFFF"), rng, name == "CAFÉ" || name == "LANCHONETE")
                g.solid(cx - 2.6f, min(Zi(depth - 2f), Zi(depth - 1.2f)), cx + 2.6f, max(Zi(depth - 2f), Zi(depth - 1.2f)))
                if (name == "SORVETERIA" || name == "AÇAÍ") {
                    // freezer com cubas coloridas
                    val l = L(cx, Zi(depth - 1.6f), 0f, fz)
                    A.m(Mt.PLAIN); for (i in 0 until 8) lb(A, l, -1.6f + i * 0.45f, FL + 1.04f, -0.05f, 0.38f, 0.04f, 0.42f, rng.pick(arrayOf(C("#F8BBD0"), C("#FFF59D"), C("#A5D6A7"), C("#8D6E63"), C("#CE93D8"), C("#FFFFFF"))), false)
                }
                // quadro de cardápio na parede do fundo
                A.m(Mt.PLAIN); val lm = L(cx, back - inF * 0.1f, 0f, fz)
                lb(A, lm, 0f, FL + 2.6f, 0f, min(w - 3f, 4f), 1.0f, 0.04f, C("#263238"))
                for (i in 0 until 4) lb(A, lm, -1.3f + i * 0.85f, FL + 2.6f, -0.03f, 0.7f, 0.7f, 0.01f, C(rng.pick(arrayOf("#FFCC80", "#EF9A9A", "#A5D6A7", "#FFF59D"))), false)
                tables(5, true)
            }
            "HAMBÚRGUER", "PIZZARIA", "SUSHI", "RESTAURANTE" -> {
                if (name == "PIZZARIA") {
                    // forno a lenha de tijolo no fundo
                    val ox = x1 - 1.6f; val oz = back - inF * 1.2f
                    A.m(Mt.STONE, 1f); A.box(ox, FL + 0.5f, oz, 2.0f, 1.0f, 1.8f, C("#B5654A"))
                    A.m(Mt.STONE, 1f); ball(A, ox, FL + 1.0f, oz, 0.95f, C("#C0705A"), 0.8f, 9)
                    A.m(Mt.PLAIN); A.box(ox, FL + 1.25f, oz - inF * -0.9f, 0.6f, 0.4f, 0.05f, C("#1A1A1A")); A.box(ox, FL + 1.18f, oz - inF * -0.92f, 0.4f, 0.2f, 0.02f, C("#FF8F00"), false)
                    g.solid(ox - 1.1f, oz - 1f, ox + 1.1f, oz + 1f)
                }
                if (name == "SUSHI") {
                    // balcão em L com banquinhos
                    val l = L(cx, Zi(depth - 1.5f), 0f, fz)
                    A.m(Mt.WOOD, 1f); lb(A, l, 0f, FL + 0.55f, 0f, min(w - 2f, 5.5f), 1.1f, 0.6f, C("#D7B98E")); lb(A, l, 0f, FL + 1.12f, -0.1f, min(w - 2f, 5.5f) + 0.1f, 0.05f, 0.85f, C("#3E2723"))
                    A.m(Mt.METAL, 1f); for (i in 0 until 6) { val sx = -2.2f + i * 0.88f; lcyl(A, l, sx, FL, -0.75f, 0.04f, 0.04f, 0.75f, C("#555555"), 6); lcyl(A, l, sx, FL + 0.75f, -0.75f, 0.2f, 0.2f, 0.06f, C("#B71C1C"), 10) }
                    g.solid(cx - 2.8f, min(Zi(depth - 2.1f), Zi(depth - 1.2f)), cx + 2.8f, max(Zi(depth - 2.1f), Zi(depth - 1.2f)))
                } else backCounter(C(if (name == "HAMBÚRGUER") "#C62828" else "#5D4037"), 3.5f)
                if (name == "HAMBÚRGUER") {
                    // sofás de lanchonete (boxes) na parede lateral
                    var d = 1.8f
                    while (d < depth - 3f) {
                        sofa(A, L(x0 + 0.7f, Zi(d), 1f, 0f), 1.4f, C("#C62828"))
                        A.m(Mt.WOOD, 1f); A.box(x0 + 1.6f, FL + 0.74f, Zi(d), 0.8f, 0.05f, 1.1f, C("#ECEFF1"))
                        g.solid(x0, Zi(d) - 0.8f, x0 + 2f, Zi(d) + 0.8f)
                        d += 2.2f
                    }
                    tables(3, true)
                } else tables(5, false)
            }
            "PET SHOP" -> {
                // aquários iluminados, gaiolas, ração nas prateleiras
                for (i in 0 until 3) {
                    val ax = x0 + 1.2f + i * 1.4f; val az = back - inF * 0.5f
                    A.m(Mt.WOOD, 1f); A.box(ax, FL + 0.45f, az, 1.2f, 0.9f, 0.5f, C("#37474F"))
                    A.m(Mt.PLAIN); A.box(ax, FL + 1.25f, az, 1.15f, 0.7f, 0.45f, C("#4FC3F7"), false)
                    for (k in 0 until 3) ball(A, ax - 0.3f + k * 0.3f, FL + 1.15f + k * 0.12f, az, 0.06f, rng.pick(arrayOf(C("#FF7043"), C("#FFEE58"), C("#AB47BC"))), 0.04f, 5, false)
                }
                for (i in 0 until 2) {
                    val gx = x1 - 1.2f; val gz = Zi(2f + i * 1.8f)
                    A.m(Mt.METAL, 1f); A.box(gx, FL + 0.4f, gz, 1.0f, 0.8f, 0.8f, C("#B0BEC5"))
                    A.m(Mt.PLAIN); A.box(gx, FL + 0.41f, gz, 0.94f, 0.74f, 0.74f, C("#ECEFF1"), false)
                    ball(A, gx, FL + 0.25f, gz, 0.2f, C(rng.pick(arrayOf("#D7A86E", "#FFFFFF", "#5D4037"))), 0.15f, 6)
                    g.solid(gx - 0.55f, gz - 0.45f, gx + 0.55f, gz + 0.45f)
                }
                g.solid(x0, back - inF * 0.8f - 0.4f, x0 + 4.6f, back + 0.4f)
                backCounter(C("#25A8E0"), 2.4f)
            }
            "SALÃO DE BELEZA", "BARBEARIA" -> {
                // cadeiras viradas para espelhos na parede lateral, lavatório no fundo
                var d = 1.6f
                while (d < depth - 2.4f) {
                    mirrorWall(A, x0 + 0.04f, Zi(d))
                    A.m(Mt.WOOD, 1f); A.box(x0 + 0.3f, FL + 0.85f, Zi(d), 0.5f, 0.06f, 1.0f, C("#FFFFFF"))
                    officeChair(A, L(x0 + 1.2f, Zi(d), 1f, 0f), C(if (name == "BARBEARIA") "#4E342E" else "#EC407A"))
                    g.solid(x0, Zi(d) - 0.5f, x0 + 1.6f, Zi(d) + 0.5f)
                    d += 1.6f
                }
                val l = L(x1 - 1.0f, back - inF * 0.5f, 0f, fz)
                A.m(Mt.PLAIN); lb(A, l, 0f, FL + 0.8f, 0f, 0.7f, 0.3f, 0.6f, C("#212121")); lcyl(A, l, 0f, FL + 0.95f, 0f, 0.25f, 0.2f, 0.12f, C("#FAFAFA"), 10)
                sofa(A, L(x1 - 1f, Zi(1.8f), -1f, 0f), 1.8f, C("#455A64"))
                plant(A, x1 - 0.5f, Zi(0.7f), 1f, rng)
            }
            "FLORICULTURA" -> {
                // baldes de flores em degraus e vasos grandes
                for (row in 0 until 3) {
                    val zz = Zi(1.6f + row * 1.6f)
                    // dois bancos iguais, com corredor livre de 2 m no centro (porta)
                    val seg = (w - 2.5f) / 2f - 1.0f
                    for (sd in floatArrayOf(-1f, 1f)) { val sc = cx + sd * (1.0f + seg / 2f)
                        A.m(Mt.WOOD, 1f); A.box(sc, FL + 0.25f, zz, seg, 0.5f, 0.8f, C("#A1887F"))
                        g.solid(sc - seg / 2, zz - 0.45f, sc + seg / 2, zz + 0.45f) }
                    var x = x0 + 1.6f
                    while (x < x1 - 1.4f) {
                        if (abs(x - cx) < 1.0f) { x += 0.65f; continue }
                        A.m(Mt.METAL, 1f); A.cyl(x, FL + 0.5f, zz, 0.2f, 0.17f, 0.35f, C("#90A4AE"), true, 8)
                        g.fl.place(arrayOf("fl_tulip", "fl_daisy", "fl_poppy", "fl_lav", "fl_yellow")[rng.i(5)], x.toDouble(), (FL + 0.8f).toDouble(), zz.toDouble(), 2.4, rng.r(0f, 6f).toDouble())
                        x += 0.65f
                    }
                }
                for (i in 0 until 3) plant(A, x1 - 0.6f, back - inF * (0.6f + i * 1.2f), 1.5f, rng)
                backCounter(C("#7CB342"), 2.2f)
            }
            "MODA", "ÓTICA", "ELETRÔNICOS", "LIVRARIA" -> {
                when (name) {
                    "LIVRARIA" -> { var d = 1.4f; while (d < depth - 2f) { for (sx in floatArrayOf(x0 + 0.3f, x1 - 0.3f)) bookshelf(A, L(sx, Zi(d), if (sx < cx) 1f else -1f, 0f), wood, rng); d += 1.05f }
                        g.solid(x0, min(Zi(1f), Zi(depth - 1.8f)), x0 + 0.7f, max(Zi(1f), Zi(depth - 1.8f))); g.solid(x1 - 0.7f, min(Zi(1f), Zi(depth - 1.8f)), x1, max(Zi(1f), Zi(depth - 1.8f)))
                        displayTable(A, cx, Zi(depth * 0.45f), rng); armchair(A, L(cx + 1.6f, Zi(depth * 0.45f), -1f, 0f), rng.pick(FABRICS)) }
                    "ELETRÔNICOS" -> { // parede de TVs e mesas com celulares
                        val l = L(cx, back - inF * 0.12f, 0f, fz)
                        A.m(Mt.METAL, 1f)
                        for (r in 0..1) for (i in -2..2) { lb(A, l, i * 1.05f, FL + 1.3f + r * 0.75f, 0f, 0.95f, 0.6f, 0.05f, C("#111111")); A.m(Mt.PLAIN); lb(A, l, i * 1.05f, FL + 1.3f + r * 0.75f, -0.03f, 0.88f, 0.52f, 0.01f, C(rng.pick(arrayOf("#29B6F6", "#66BB6A", "#FFA726", "#AB47BC"))), false); A.m(Mt.METAL, 1f) }
                        for (i in 0 until 2) { val tz = Zi(2.0f + i * 2.4f); for (sd in floatArrayOf(-1f, 1f)) { val tx = cx + sd * min(2.0f, w / 2 - 1.7f); displayTable(A, tx, tz, rng); g.solid(tx - 0.75f, tz - 0.45f, tx + 0.75f, tz + 0.45f) } } }
                    "ÓTICA" -> { // vitrines de óculos
                        for (sx in floatArrayOf(x0 + 0.35f, x1 - 0.35f)) { val l = L(sx, cz, if (sx < cx) 1f else -1f, 0f)
                            A.m(Mt.WOOD, 1f); lb(A, l, 0f, FL + 1.1f, 0.1f, depth - 3f, 2.2f, 0.05f, C("#FFFFFF"))
                            A.m(Mt.PLAIN); for (r in 0 until 5) for (i in 0 until ((depth - 3.4f) / 0.35f).toInt()) lb(A, l, -(depth - 3.4f) / 2 + i * 0.35f, FL + 0.6f + r * 0.35f, 0.05f, 0.22f, 0.07f, 0.03f, C(rng.pick(arrayOf("#212121", "#6D4C41", "#C62828", "#1565C0"))), false) }
                        for (i in 0 until 2) { val tz = Zi(2.0f + i * 2.2f); for (sd in floatArrayOf(-1f, 1f)) { val tx = cx + sd * min(2.0f, w / 2 - 1.7f); displayTable(A, tx, tz, rng); g.solid(tx - 0.75f, tz - 0.45f, tx + 0.75f, tz + 0.45f) } }
                        mirrorWall(A, cx, back - inF * 0.04f) }
                    else -> { // moda: araras e manequins
                        for (i in 0 until max(1, (w / 2.6f).toInt())) { val rx = x0 + 1.4f + i * 2.6f; rack(A, L(rx, cz, 0f, fz), rng); g.solid(rx - 0.7f, cz - 0.4f, rx + 0.7f, cz + 0.4f) }
                        for (i in 0 until 2) { val mx = x0 + 1.2f + i * (w - 2.4f); val mz = Zi(1.0f)
                            A.m(Mt.PLAIN); A.cyl(mx, FL, mz, 0.2f, 0.2f, 0.04f, C("#424242"), true, 10); A.box(mx, FL + 0.6f, mz, 0.04f, 1.2f, 0.04f, C("#9E9E9E"))
                            A.m(Mt.FABRIC, 1f); A.box(mx, FL + 1.35f, mz, 0.42f, 0.6f, 0.24f, rng.pick(FABRICS)); A.box(mx, FL + 0.85f, mz, 0.36f, 0.45f, 0.22f, rng.pick(FABRICS))
                            A.m(Mt.PLAIN); ball(A, mx, FL + 1.8f, mz, 0.12f, C("#ECEFF1"), 0.15f, 7) }
                        mirrorWall(A, x1 - 0.04f, cz) }
                }
                backCounter(C("#FFFFFF"), 2.4f)
            }
            else -> return false
        }
        // tapete de entrada e vaso perto da porta
        rug(A, doorX - 0.7f, min(Zi(0.2f), Zi(1.2f)), doorX + 0.7f, max(Zi(0.2f), Zi(1.2f)), C("#455A64"))
        return true
    }

    private val PROD = arrayOf(C("#E53935"), C("#FDD835"), C("#43A047"), C("#1E88E5"), C("#FB8C00"), C("#8E24AA"), C("#FFFFFF"), C("#6D4C41"), C("#00ACC1"))

    fun shelf(b: MB, x: Float, z: Float, w: Float, rng: City.Rng) {
        b.m(Mt.METAL, 1f)
        b.box(x, FL + 0.9f, z, w, 1.8f, 0.06f, C("#DADDE0"))
        b.box(x, FL + 0.08f, z, w, 0.16f, 0.62f, C("#8A8F94"))
        for (k in 0..3) b.box(x, FL + 0.25f + k * 0.42f, z, w, 0.025f, 0.62f, C("#ECEEF0"))
        for (k in 0..3) for (side in floatArrayOf(-1f, 1f)) {
            CityInt.goods(b, x, FL + 0.265f + k * 0.42f, z + side * 0.17f, w - 0.04f, 0.34f, 0.26f)
            b.m(Mt.PLAIN); b.box(x, FL + 0.24f + k * 0.42f, z + side * 0.312f, w, 0.045f, 0.006f, C("#FFF59D"), false)
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
            val x0 = xa + sw * k + 0.15f; val x1 = x0 + sw - 0.3f; val cx = (x0 + x1) / 2   // Etapa 127: paredes vizinhas não se cruzam (piscavam)
            val col = C(rng.pick(WALLS)); val two = rng.chance(0.55f)
            val zf = Z(1.5f); val zb = Z(1.5f + depth); val z0 = min(zf, zb); val z1 = max(zf, zb)
            val (signName, kind) = signs[k]
            val bd = g.begin(x0, z0, x1, z1, signName.lowercase().replaceFirstChar { it.uppercase() })
            val A = g.A; val H = g.H
            A.m(Mt.STONE, 0.6f); A.box(cx, FL / 2, (z0 + z1) / 2, x1 - x0, FL, depth, C("#A8A39B"))
            val fm0 = rng.pick(arrayOf(Mt.TILE, Mt.FLOOR_L, Mt.FLOOR_D))
            val fl0 = CityInt.floor(signName)
            A.m(fl0?.first ?: fm0, fl0?.third ?: 0.6f); A.box(cx, FL - 0.005f, (z0 + z1) / 2, x1 - x0 - 0.3f, 0.012f, depth - 0.3f, fl0?.second ?: C("#FFFFFF"))
            val hh = 4.4f
            // Etapa 129: porta no centro da loja e uma vitrine de cada lado, iguais (antes a porta ficava deslocada)
            val ww0 = x1 - x0
            val reg = ww0 / 2f - 0.7f - 0.8f            // espaço de cada lado entre o pilar da porta e o pilar da ponta
            val vw = min(reg, 4.6f); val vc = 0.7f + reg / 2f + 0.8f * 0f
            val ops = if (vw > 1.2f) listOf(Op(cx - (0.7f + reg / 2f), vw, FL + 0.4f, FL + 3.0f, false), Op(cx, 1.3f, FL, FL + 2.5f, true), Op(cx + (0.7f + reg / 2f), vw, FL + 0.4f, FL + 3.0f, false))
                      else listOf(Op(cx, 1.3f, FL, FL + 2.5f, true))
            val inW = innerColor(signName)
            wall(g, 0, zf, x0, x1, FL, FL + hh, if (fz > 0) 1 else -1, ops, col, inW, Mt.PLASTER, 0.24f)
            wall(g, 0, zb, x0, x1, FL, FL + hh, if (fz > 0) -1 else 1, emptyList(), col, inW, Mt.PLASTER, 0.24f)
            wall(g, 1, x0, z0 + 0.12f, z1 - 0.12f, FL, FL + hh, -1, emptyList(), col, inW, Mt.PLASTER, 0.24f)
            wall(g, 1, x1, z0 + 0.12f, z1 - 0.12f, FL, FL + hh, 1, emptyList(), col, inW, Mt.PLASTER, 0.24f)
            g.solid(x0 - 0.15f, z0 - 0.15f, x0 + 0.2f, z1 + 0.15f); g.solid(x1 - 0.2f, z0 - 0.15f, x1 + 0.15f, z1 + 0.15f); g.solid(x0, zb - 0.2f, x1, zb + 0.2f)
            g.solid(x0, zf - 0.2f, cx - 0.7f, zf + 0.2f); g.solid(cx + 0.7f, zf - 0.2f, x1, zf + 0.2f)
            g.door(signName, cx, zf, fz, 1.3f, 2.5f, 0.24f)
            if (!shopInterior(g, signName, x0 + 0.25f, z0 + 0.25f, x1 - 0.25f, z1 - 0.25f, zf, fz, cx)) interior(g, kind, x0 + 0.25f, z0 + 0.25f, x1 - 0.25f, z1 - 0.25f, zf, fz, cx)
            // platibanda, toldo, letreiro, andar de cima
            H.m(Mt.STONE, 0.5f)
            H.box(cx, FL + hh + 0.3f, (z0 + z1) / 2, x1 - x0 + 0.1f, 0.6f, depth + 0.1f, shade(col, -28))
            // Etapa 127: cada loja com marca, letreiro e toldo próprios (caixa luminosa, letra-caixa, neon, madeira, toldo com nome)
            val si = Signs.pick(signName, rng)
            val sp = Signs.spec(si)
            val doorX = cx
            val awnT = if (sp.style == Signs.AWNING) 1 else sp.awn
            val awnC = if (sp.style == Signs.AWNING) C(sp.bg) else C(rng.pick(arrayOf("#B3261E", "#1F5E8C", "#2A7D6F", "#C46A1C", "#5B3F86", "#2E6B30", "#6B4A3A", "#22313F")))
            if (awnT > 0) Signs.awning(H, awnT, x0 + 0.45f, x1 - 0.45f, FL + 3.22f, zf, fz, 1.15f, awnC, if (sp.style == Signs.AWNING) si else -1)
            if (sp.style != Signs.AWNING) {
                val sh = if (sp.style == Signs.LETTERS) 0.82f else 0.7f
                Signs.mount(H, si, cx, FL + 3.4f, zf, fz, min(x1 - x0 - 1.4f, 6.2f), sh)
            }
            if (sp.blade >= 0) Signs.blade(H, sp.blade, x1 - 0.3f, FL + 3.35f, zf, fz, 0.62f)
            Signs.doorDetails(H, doorX, FL, zf, fz, cx - (0.7f + reg / 2f), vw, C(sp.fg.let { if (sp.style == Signs.LETTERS || sp.style == Signs.NEON) it else sp.bg }), k + 1)
            if (sp.awn == 1 || sp.awn == 3 || kind == 2) { Signs.aframe(H, doorX - 1.9f, CURB, zf + fz * 0.85f, fz); Signs.aframe(H, doorX + 1.9f, CURB, zf + fz * 0.85f, fz) }
            if (rng.chance(0.55f) && vw > 1.2f) for (sd in floatArrayOf(-1f, 1f)) Signs.planter(H, cx + sd * (0.7f + reg / 2f), CURB, zf + fz * 0.3f, min(vw * 0.7f, 2.4f), rng)
            // pilastra entre uma loja e a outra (cobre a junta)
            if (k < n - 1) { H.m(Mt.STONE, 0.6f); H.box(x1 + 0.15f, (FL + hh + 0.6f) / 2, (z0 + z1) / 2, 0.36f, FL + hh + 0.6f, depth + 0.3f, shade(col, -22)) }
            // Etapa 127: fundos da loja não ficam lisos — janelas altas com grade, porta de serviço, ar-condicionado e calha
            run {
                val bz = zb - fz * 0.13f
                H.m(Mt.PLAIN)
                for (wx in floatArrayOf(cx - sw * 0.28f, cx + sw * 0.28f)) {
                    H.box(wx, FL + 2.6f, bz, 1.1f, 0.7f, 0.05f, C("#F2F2F2"))
                    H.m(Mt.METAL, 1f); H.box(wx, FL + 2.6f, bz - fz * 0.02f, 0.98f, 0.58f, 0.02f, C("#56708A"))
                    for (m in 0 until 5) H.box(wx - 0.4f + m * 0.2f, FL + 2.6f, bz - fz * 0.05f, 0.025f, 0.62f, 0.025f, C("#3A3A3A"))
                    H.m(Mt.PLAIN)
                }
                H.m(Mt.METAL, 1f)
                H.box(cx, FL + 1.1f, bz, 0.95f, 2.2f, 0.06f, C("#6B7076"))
                H.box(cx + 0.32f, FL + 1.1f, bz - fz * 0.04f, 0.05f, 0.05f, 0.04f, C("#C9C9C9"))
                H.box(cx, FL + 2.9f, bz - fz * 0.22f, 0.8f, 0.55f, 0.32f, C("#E6E6E6"))
                H.m(Mt.PLAIN); for (m in 0 until 6) H.box(cx - 0.3f + m * 0.12f, FL + 1.6f, bz - fz * 0.385f, 0.05f, 0.45f, 0.01f, C("#8A8A8A"))
                H.m(Mt.METAL, 1f); H.box(x0 + 0.3f, (FL + hh + 0.5f) / 2, bz - fz * 0.05f, 0.09f, FL + hh + 0.5f, 0.09f, C("#9E9E9E"))
            }
            if (two) {
                val y2 = FL + hh + 0.6f
                H.m(Mt.PLASTER, 0.5f); H.box(cx, y2 + 1.5f, (z0 + z1) / 2, x1 - x0, 3.0f, depth, col)
                for (s in floatArrayOf(-1f, 1f)) {
                    // Etapa 126: moldura descolada da parede e vidro à frente dela (antes as faces coincidiam e piscavam)
                    H.m(Mt.PLAIN); H.box(cx + s * sw * 0.22f, y2 + 1.5f, zf + fz * 0.036f, 1.4f, 1.5f, 0.05f, C("#FFFFFF"))
                    H.m(Mt.METAL, 1f); H.box(cx + s * sw * 0.22f, y2 + 1.5f, zf + fz * 0.072f, 1.25f, 1.35f, 0.012f, C("#5D7A93"))
                    H.m(Mt.WOOD, 1f); H.box(cx + s * sw * 0.22f - 0.85f, y2 + 1.5f, zf + fz * 0.06f, 0.3f, 1.5f, 0.04f, C("#2E7D32")); H.box(cx + s * sw * 0.22f + 0.85f, y2 + 1.5f, zf + fz * 0.06f, 0.3f, 1.5f, 0.04f, C("#2E7D32"))
                }
                for (s2 in floatArrayOf(-1f, 1f)) {
                    H.m(Mt.PLAIN); H.box(cx + s2 * sw * 0.22f, y2 + 1.5f, zb - fz * 0.036f, 1.2f, 1.3f, 0.05f, C("#FFFFFF"))
                    H.m(Mt.METAL, 1f); H.box(cx + s2 * sw * 0.22f, y2 + 1.5f, zb - fz * 0.072f, 1.05f, 1.15f, 0.012f, C("#5D7A93"))
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
                    cafeTableOut(g.b, tx, Z(0.6f), awnC)
                }
            }
            // longe
            g.f.m(Mt.PLASTER, 0.5f); g.f.box(cx, (FL + hh + (if (two) 3.6f else 0.6f)) / 2, (z0 + z1) / 2, x1 - x0, FL + hh + (if (two) 3.6f else 0.6f), depth, col)
            if (awnT > 0) { g.f.m(Mt.FABRIC, 1f); g.f.box(cx, FL + 3.0f, Z(0.8f), x1 - x0 - 0.9f, 0.4f, 1.15f, awnC) }
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
            "park" -> { lawnHole(g, (g.x0 + g.x1) / 2 + 4f, (g.z0 + g.z1) / 2 - 3f, 12.5f + 2f); park(g) }
            "fun" -> { CityFun.park(g); 30f }
            else -> { lawn(g); 1f }
        }
    }

    /** Gramado com um buraco quadrado (onde entra o terreno do lago). */
    private fun lawnHole(g: Gen, hx: Float, hz: Float, hr: Float) {
        val c = C("#D6EEC4")
        groundBox(g.b, g.x0, g.z0, g.x1, hz - hr, Mt.GRASS, 0.3f, c); groundBox(g.b, g.x0, hz + hr, g.x1, g.z1, Mt.GRASS, 0.3f, c)
        groundBox(g.b, g.x0, hz - hr, hx - hr, hz + hr, Mt.GRASS, 0.3f, c); groundBox(g.b, hx + hr, hz - hr, g.x1, hz + hr, Mt.GRASS, 0.3f, c)
        groundBox(g.f, g.x0, g.z0, g.x1, g.z1, Mt.GRASS, 0.3f, c)
    }

    /**
     * Etapa 127: lago natural. Terreno em grade com margem irregular: grama → barranco de terra → fundo escuro;
     * a água (shader próprio) fica um palmo abaixo do gramado. Pedras na margem, taboas, vitórias-régias, ponte em arco
     * de madeira com corrimão, deque com bancos e patos.
     */
    fun lake(g: Gen, lx: Float, lz: Float, r: Float) {
        val b = g.b; val rng = g.rng
        val wy = CURB - 0.28f
        val er = r * City.LAKE_EDGE
        fun edge(a: Float) = er * (1f + 0.10f * sin(a * 3f + 0.7f) + 0.06f * sin(a * 5f + 2.1f) + 0.04f * cos(a * 2f))
        fun h(x: Float, z: Float): Float {
            val dx = x - lx; val dz = z - lz
            val d = sqrt(dx * dx + dz * dz); val e = edge(kotlin.math.atan2(dz, dx))
            val t = d / e
            return when {
                t > 1.16f -> CURB
                t > 1.0f -> wy + 0.06f + (CURB - wy - 0.06f) * ((t - 1f) / 0.16f).let { it * it * (3 - 2 * it) }
                else -> wy + 0.06f - 1.3f * (1f - t * t).let { kotlin.math.sqrt(it) }
            }
        }
        val hr = r + 2f
        val n = 46
        val step = 2 * hr / n
        val grass = C("#CFE6B8"); val mud = C("#7A6448"); val bed = C("#3E4A3A")
        for (j in 0 until n) for (i in 0 until n) {
            val x0 = lx - hr + i * step; val z0 = lz - hr + j * step; val x1 = x0 + step; val z1 = z0 + step
            val h00 = h(x0, z0); val h10 = h(x1, z0); val h01 = h(x0, z1); val h11 = h(x1, z1)
            val hm = (h00 + h10 + h01 + h11) / 4
            val (mat, col) = when {
                hm > CURB - 0.02f -> Pair(Mt.GRASS, grass)
                hm > wy - 0.08f -> Pair(Mt.STONE, mud)
                else -> Pair(Mt.PLAIN, bed)
            }
            b.m(mat, if (mat == Mt.GRASS) 0.3f else 0.8f)
            q(b, P(x0, h00, z0) + P(x0, h01, z1) + P(x1, h11, z1) + P(x1, h10, z0), col)
        }
        g.f.m(Mt.PLAIN); g.f.cyl(lx, CURB - 0.1f, lz, er * 1.05f, er * 1.05f, 0.11f, C("#3F6E7A"), true, 20)
        if (g.reg) City.lakes.add(floatArrayOf(lx, lz, r, wy))
        // água: bloqueia andando (menos o corredor da ponte)
        g.solid(lx - er * 0.95f, lz - er * 0.95f, lx - 1.25f, lz + er * 0.95f); g.solid(lx + 1.25f, lz - er * 0.95f, lx + er * 0.95f, lz + er * 0.95f)
        // pedras na margem
        b.m(Mt.STONE, 1.2f)
        for (k in 0 until 46) {
            val a = k * 6.2832f / 46 + rng.r(-0.05f, 0.05f)
            val e = edge(a) * rng.r(0.98f, 1.06f)
            val sz = rng.r(0.18f, 0.45f)
            ball(b, lx + cos(a) * e, wy + 0.05f, lz + sin(a) * e, sz, C(rng.pick(arrayOf("#8E8A80", "#A29D92", "#7D786E", "#9A948A"))), sz * rng.r(0.45f, 0.7f), 7)
        }
        // taboas e capim alto em moitas na margem
        b.m(Mt.PLAIN)
        for (k in 0 until 16) {
            val a = rng.r(0f, 6.2832f)
            if (abs(sin(a)) < 0.25f) continue   // deixa a frente da ponte livre
            val e = edge(a) * rng.r(0.9f, 1.0f)
            val bx = lx + cos(a) * e; val bz = lz + sin(a) * e
            for (m in 0 until 9) {
                val ox = rng.r(-0.45f, 0.45f); val oz = rng.r(-0.45f, 0.45f)
                val hh = rng.r(0.9f, 1.6f); val lean = rng.r(-0.18f, 0.18f)
                val c = C(rng.pick(arrayOf("#5C7F3A", "#6E8F45", "#4E6E33", "#7A9A50")))
                val x = bx + ox; val z = bz + oz
                q(b, P(x - 0.04f, wy, z) + P(x + 0.04f, wy, z) + P(x + lean + 0.012f, wy + hh, z + lean * 0.5f) + P(x + lean - 0.012f, wy + hh, z + lean * 0.5f), c)
                q(b, P(x, wy, z - 0.04f) + P(x, wy, z + 0.04f) + P(x + lean, wy + hh, z + lean * 0.5f + 0.012f) + P(x + lean, wy + hh, z + lean * 0.5f - 0.012f), shade(c, -15))
                if (m % 3 == 0) { b.cyl(x + lean * 0.78f, wy + hh * 0.72f, z + lean * 0.39f, 0.03f, 0.03f, 0.18f, C("#5D3A1F"), true, 5) }
            }
        }
        // vitórias-régias (com uma flor rosa de vez em quando)
        for (k in 0 until 22) {
            val a = rng.r(0f, 6.2832f); val d = edge(a) * rng.r(0.35f, 0.85f)
            val px = lx + cos(a) * d; val pz = lz + sin(a) * d
            if (abs(px - lx) < 1.6f) continue   // embaixo da ponte não
            val rr = rng.r(0.25f, 0.5f)
            b.m(Mt.PLAIN)
            val nseg = 10; val gap = rng.r(0f, 6.28f)
            for (sgi in 0 until nseg) {
                val a0 = gap + 0.35f + sgi * (6.2832f - 0.5f) / nseg; val a1 = gap + 0.35f + (sgi + 1) * (6.2832f - 0.5f) / nseg
                tri(b, P(px, wy + 0.035f, pz) + P(px + cos(a1) * rr, wy + 0.03f, pz + sin(a1) * rr) + P(px + cos(a0) * rr, wy + 0.03f, pz + sin(a0) * rr), C(if (k % 2 == 0) "#4F8A3A" else "#5E9944"))
            }
            if (k % 5 == 0) { ball(b, px + 0.05f, wy + 0.08f, pz, 0.07f, C("#F48FB1"), 0.05f, 6); ball(b, px + 0.05f, wy + 0.11f, pz, 0.03f, C("#FFF176"), 0.02f, 5) }
        }
        // ponte em arco de madeira atravessando o lago (norte-sul)
        val bl = er * 2.5f
        val bw = 2.0f
        b.m(Mt.WOOD, 1f)
        val np = (bl / 0.3f).toInt()
        fun deck(t: Float) = CURB + 0.12f + 0.75f * sin(PI.toFloat() * t)
        for (k in 0 until np) {
            val t = (k + 0.5f) / np
            val z = lz - bl / 2 + t * bl
            b.box(lx, deck(t), z, bw, 0.06f, 0.27f, C(if (k % 2 == 0) "#9B7350" else "#8E6A49"))
        }
        // vigas, pilares e corrimão
        for (sd in floatArrayOf(-1f, 1f)) {
            for (k in 0 until 12) {
                val t0 = k / 12f; val t1 = (k + 1) / 12f
                limb(b, lx + sd * bw * 0.48f, deck(t0) - 0.08f, lz - bl / 2 + t0 * bl, lx + sd * bw * 0.48f, deck(t1) - 0.08f, lz - bl / 2 + t1 * bl, 0.07f, 0.07f, C("#6E4E33"), 4)
                limb(b, lx + sd * bw * 0.5f, deck(t0) + 0.92f, lz - bl / 2 + t0 * bl, lx + sd * bw * 0.5f, deck(t1) + 0.92f, lz - bl / 2 + t1 * bl, 0.05f, 0.05f, C("#7A5638"), 5)
                limb(b, lx + sd * bw * 0.5f, deck(t0) + 0.5f, lz - bl / 2 + t0 * bl, lx + sd * bw * 0.5f, deck(t1) + 0.5f, lz - bl / 2 + t1 * bl, 0.025f, 0.025f, C("#7A5638"), 4)
            }
            for (k in 0..12) {
                val t = k / 12f
                b.box(lx + sd * bw * 0.5f, deck(t) + 0.47f, lz - bl / 2 + t * bl, 0.09f, 0.94f, 0.09f, C("#6E4E33"))
                if (k % 3 == 0 && k in 1..11) b.box(lx + sd * bw * 0.48f, (wy - 0.4f + deck(t)) / 2, lz - bl / 2 + t * bl, 0.14f, deck(t) - wy + 0.4f, 0.14f, C("#5B4029"))
            }
            // lanterninhas nas pontas
            for (e in floatArrayOf(0f, 1f)) { b.box(lx + sd * bw * 0.5f, deck(e) + 1.05f, lz - bl / 2 + e * bl, 0.16f, 0.22f, 0.16f, C("#2E2E2E")); b.m(Mt.PLAIN); b.box(lx + sd * bw * 0.5f, deck(e) + 1.05f, lz - bl / 2 + e * bl, 0.12f, 0.16f, 0.17f, C("#FFF3C4"), false); b.m(Mt.WOOD, 1f) }
        }
        // deque de madeira na margem leste com bancos
        val dx0 = lx + er * 0.82f
        b.m(Mt.WOOD, 1f)
        for (k in 0 until 14) b.box(dx0 + 1.4f, CURB + 0.1f, lz - 2.6f + k * 0.37f, 3.2f, 0.06f, 0.33f, C(if (k % 2 == 0) "#A57B55" else "#987150"))
        for (s2 in floatArrayOf(-2.5f, 2.5f)) for (t in floatArrayOf(0.1f, 2.7f)) b.box(dx0 + t, (wy - 0.3f + CURB) / 2, lz + s2, 0.14f, CURB - wy + 0.3f, 0.14f, C("#5B4029"))
        b.box(dx0 + 0.05f, CURB + 0.6f, lz, 0.06f, 0.06f, 5.2f, C("#7A5638")); for (k in 0..4) b.box(dx0 + 0.05f, CURB + 0.35f, lz - 2.5f + k * 1.25f, 0.08f, 0.5f, 0.08f, C("#6E4E33"))
        publicBench(b, dx0 + 2.4f, lz - 1.3f, -1f, 0f); publicBench(b, dx0 + 2.4f, lz + 1.3f, -1f, 0f)
        // patos (corpo, cabeça, bico, cauda)
        for (k in 0 until 5) {
            val a = 1.0f + k * 0.5f; val d = er * 0.55f
            val px = lx + cos(a) * d + (k % 2) * 0.6f; val pz = lz + sin(a) * d
            val fx = -sin(a); val fz = cos(a)
            val wh = k != 2
            b.m(Mt.PLAIN)
            ball(b, px, wy + 0.1f, pz, 0.2f, C(if (wh) "#F5F5F0" else "#7A6A55"), 0.12f, 8)
            ball(b, px + fx * 0.17f, wy + 0.27f, pz + fz * 0.17f, 0.085f, C(if (wh) "#FAFAF5" else "#2E6B3A"), 0.085f, 7)
            b.box(px + fx * 0.27f, wy + 0.26f, pz + fz * 0.27f, 0.08f, 0.03f, 0.08f, C("#F39C12"))
            ball(b, px - fx * 0.2f, wy + 0.17f, pz - fz * 0.2f, 0.07f, C(if (wh) "#ECECE6" else "#5E4E3C"), 0.05f, 5)
        }
        g.solid(lx - bw / 2 - 0.2f, lz - bl / 2, lx - bw / 2, lz + bl / 2); g.solid(lx + bw / 2, lz - bl / 2, lx + bw / 2 + 0.2f, lz + bl / 2)
        if (g.reg) City.bridges.add(floatArrayOf(lx - bw / 2, lz - bl / 2, lx + bw / 2, lz + bl / 2, CURB + 0.15f, 0.75f))
    }

    private fun lawn(g: Gen) { groundBox(g.b, g.x0, g.z0, g.x1, g.z1, Mt.GRASS, 0.3f, C("#D6EEC4")); groundBox(g.f, g.x0, g.z0, g.x1, g.z1, Mt.GRASS, 0.3f, C("#D6EEC4")) }
    private fun plaza(g: Gen) { groundBox(g.b, g.x0, g.z0, g.x1, g.z1, Mt.PAVER, 0.7f, C("#E2DDD3")); groundBox(g.f, g.x0, g.z0, g.x1, g.z1, Mt.PAVER, 0.7f, C("#E2DDD3")) }

    private fun residential(g: Gen, lots: Boolean) {
        val rng = g.rng
        val depth = (g.z1 - g.z0) / 2
        // estilo predominante do bairro + variações (nenhuma casa igual: cores, tamanhos, móveis e detalhes sorteados)
        val main = rng.i(5)
        for (side in intArrayOf(0, 1)) {
            var x = g.x0; var li = 0
            while (x < g.x1 - 9f) {
                val lw = min(g.x1 - x, rng.r(12.5f, 15.5f)).let { if (g.x1 - x - it < 11f) g.x1 - x else it }
                val fz0 = if (side == 0) g.z1 else g.z0
                val fz = if (side == 0) 1f else -1f
                val empty = if (lots) rng.chance(0.6f) else rng.chance(0.08f)
                if (empty) emptyLot(g, x, x + lw, fz0, fz, depth)
                else house(g, x, x + lw, fz0, fz, depth, if (rng.chance(0.6f)) main else rng.i(5), rng.chance(0.18f), false, li % 2)
                // divisa entre lotes (não no fim do quarteirão: ali é a rua)
                if (x + lw < g.x1 - 1f) {
                    g.b.m(Mt.STONE, 0.8f)
                    g.b.box(x + lw, CURB + 0.9f, (g.z0 + g.z1) / 2 - fz * depth / 2 - fz * 2f, 0.15f, 1.8f, depth - 5f, C("#D9D2C5"))
                    g.solid(x + lw - 0.15f, min(fz0, fz0 - fz * depth) + 3f, x + lw + 0.15f, max(fz0, fz0 - fz * depth) - 2f)
                }
                x += lw; li++
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
        // Etapa 127: as duas torres (frente e fundos) não podem se encostar: sobra um pátio de 5 m no meio para árvores e bancos
        val td = min(18f, (g.z1 - g.z0) / 2f - 2f - 2.5f)
        for (k in 0 until 2) {
            val xa = g.x0 + 1.5f + k * (w + 2f)
            val s1 = if (hotel && k == 0) "HOTEL" to 0 else rng.pick(shopsA)
            val s2 = rng.pick(shopsA)
            val f1 = if (hotel && k == 0) 24 else rng.i(14) + 9
            hMax = max(hMax, tower(g, xa, xa + w, g.z1, 1f, 2f, td, f1, if (rng.chance(0.45f)) rng.pick(GLASS_C) else rng.pick(TOWER_C), s1.first, s1.second, rng.chance(0.3f), rng.chance(0.45f)))
            hMax = max(hMax, tower(g, xa, xa + w, g.z0, -1f, 2f, td, rng.i(16) + 7, if (rng.chance(0.45f)) rng.pick(GLASS_C) else rng.pick(TOWER_C), s2.first, s2.second, rng.chance(0.3f), rng.chance(0.45f)))
        }
        val cz = (g.z0 + g.z1) / 2
        for (k in 0 until 5) tree(g, g.x0 + 5f + k * (g.x1 - g.x0 - 10f) / 4f, cz, 1.0f)
        for (k in 0 until 4) { val bx = g.x0 + 9f + k * (g.x1 - g.x0 - 18f) / 3f; publicBench(g.b, bx, cz + 1.6f, 0f, 1f); publicBench(g.b, bx, cz - 1.6f, 0f, -1f) }
        return hMax
    }

    /** Banco de praça: laterais de ferro fundido curvas, assento e encosto de ripas de madeira, apoio de braço. */
    fun publicBench(b: MB, x: Float, z: Float, fx: Float, fz: Float) {
        val l = L(x, z, fx, fz)
        val y = CURB
        b.m(Mt.WOOD, 1f)
        for (k in 0 until 4) lb(b, l, 0f, y + 0.44f, -0.2f + k * 0.12f, 1.75f, 0.035f, 0.1f, C(if (k % 2 == 0) "#9C6B3F" else "#93633A"))
        for (k in 0 until 3) lb(b, l, 0f, y + 0.6f + k * 0.13f, 0.27f + k * 0.035f, 1.75f, 0.09f, 0.03f, C(if (k % 2 == 0) "#9C6B3F" else "#93633A"))
        b.m(Mt.METAL, 1f)
        val iron = C("#24292E")
        for (s0 in floatArrayOf(-0.72f, 0.72f)) {
            // pé dianteiro curvo, pé traseiro que sobe até o encosto, braço
            CityGeo.limb(b, l.wx(s0, -0.28f), y, l.wz(s0, -0.28f), l.wx(s0, -0.18f), y + 0.42f, l.wz(s0, -0.18f), 0.03f, 0.025f, iron, 5)
            CityGeo.limb(b, l.wx(s0, 0.24f), y, l.wz(s0, 0.24f), l.wx(s0, 0.2f), y + 0.42f, l.wz(s0, 0.2f), 0.03f, 0.025f, iron, 5)
            CityGeo.limb(b, l.wx(s0, 0.2f), y + 0.42f, l.wz(s0, 0.2f), l.wx(s0, 0.36f), y + 0.9f, l.wz(s0, 0.36f), 0.025f, 0.02f, iron, 5)
            lb(b, l, s0, y + 0.41f, 0f, 0.05f, 0.04f, 0.5f, iron)
            CityGeo.limb(b, l.wx(s0, -0.24f), y + 0.62f, l.wz(s0, -0.24f), l.wx(s0, 0.24f), y + 0.64f, l.wz(s0, 0.24f), 0.025f, 0.025f, iron, 5)
            CityGeo.limb(b, l.wx(s0, -0.22f), y + 0.42f, l.wz(s0, -0.22f), l.wx(s0, -0.24f), y + 0.62f, l.wz(s0, -0.24f), 0.02f, 0.02f, iron, 4)
        }
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
        for (sd in floatArrayOf(-1f, 1f)) Vehicles.parkedKind(g, g.x0 + 2f + w / 2 + sd * 3.6f, g.z1 - 2.6f, 0, CURB, Vehicles.POLICE)   // Etapa 129: um de cada lado da porta
        val h2 = tower(g, g.x1 - 2f - w, g.x1 - 2f, g.z1, 1f, 5f, 16f, 2, C("#F3D9D2"), "BOMBEIROS", 0)
        Vehicles.parkedKind(g, g.x1 - 2f - w / 2 + 4.5f, g.z1 - 2.8f, 0, CURB, Vehicles.FIRE)   // Etapa 128: fora da frente da porta
        residentialStrip(g, g.z0, -1f, 20f)
        return max(h1, h2)
    }

    private fun residentialStrip(g: Gen, fz0: Float, fz: Float, depth: Float) {
        val rng = g.rng
        var x = g.x0; var li = 0
        while (x < g.x1 - 9f) {
            val lw = min(g.x1 - x, rng.r(12.5f, 15.5f)).let { if (g.x1 - x - it < 11f) g.x1 - x else it }
            house(g, x, x + lw, fz0, fz, depth, rng.i(5), rng.chance(0.2f), false, li % 2)
            x += lw; li++
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
        g.door("IGREJA MATRIZ", cx, zf, 1f, 2.2f, 4f, 0.4f)
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
        // Etapa 128: torre com pórtico vazado embaixo (antes a torre maciça tampava a porta da igreja)
        val pY = FL + 5.3f
        H.box(cx, (pY + ty + 15f) / 2, zf + 1.6f, 4f, ty + 15f - pY, 3.2f, wc)
        for (s in floatArrayOf(-1f, 1f)) { H.box(cx + s * 1.82f, (FL + pY) / 2, zf + 1.6f, 0.36f, pY - FL, 3.2f, wc); g.solid(cx + s * 1.82f - 0.2f, zf, cx + s * 1.82f + 0.2f, zf + 3.2f) }
        H.m(Mt.STONE, 0.5f); H.box(cx, pY - 0.12f, zf + 3.1f, 4.1f, 0.24f, 0.24f, C("#D9CDB8"))
        H.m(Mt.PLAIN); H.box(cx, pY - 0.005f, zf + 1.6f, 3.2f, 0.01f, 3.0f, C("#FFF3D6"), false)
        H.m(Mt.PLASTER, 0.5f)
        H.m(Mt.PLAIN); H.box(cx, ty + 9f, zf + 3.22f, 1.6f, 2.6f, 0.05f, C("#3E2723")); H.box(cx, ty + 9f, zf - 0.02f, 1.6f, 2.6f, 0.05f, C("#3E2723"))
        H.m(Mt.ROOF, 0.6f)
        q(H, P(cx - 2.2f, ty + 15f, zf - 0.2f) + P(cx + 2.2f, ty + 15f, zf - 0.2f) + P(cx, ty + 19f, zf + 1.6f) + P(cx, ty + 19f, zf + 1.6f), C("#6D3A2A"))
        q(H, P(cx + 2.2f, ty + 15f, zf + 3.4f) + P(cx - 2.2f, ty + 15f, zf + 3.4f) + P(cx, ty + 19f, zf + 1.6f) + P(cx, ty + 19f, zf + 1.6f), C("#6D3A2A"))
        q(H, P(cx - 2.2f, ty + 15f, zf + 3.4f) + P(cx - 2.2f, ty + 15f, zf - 0.2f) + P(cx, ty + 19f, zf + 1.6f) + P(cx, ty + 19f, zf + 1.6f), C("#6D3A2A"))
        q(H, P(cx + 2.2f, ty + 15f, zf - 0.2f) + P(cx + 2.2f, ty + 15f, zf + 3.4f) + P(cx, ty + 19f, zf + 1.6f) + P(cx, ty + 19f, zf + 1.6f), C("#6D3A2A"))
        H.m(Mt.METAL, 1f); H.box(cx, ty + 20.2f, zf + 1.6f, 0.15f, 2.4f, 0.15f, C("#C9A227")); H.box(cx, ty + 20.6f, zf + 1.6f, 1.2f, 0.15f, 0.15f, C("#C9A227"))
        sign(H, cx, FL + 5.45f, zf + 3.22f, 0f, 1f, 3.6f, 0.5f, City.signIdx("IGREJA MATRIZ"))
        g.end()
        g.place(City.Place("Igreja Matriz", cx, zf + 3f, 0xFF6D4C41.toInt(), 'I'))
        g.f.m(Mt.PLASTER, 0.5f); g.f.box(cx, FL + 4.5f, (zf + zb) / 2, w, 9f, zf - zb, wc); g.f.box(cx, ty + 3f, zf + 1.6f, 4f, 24f, 3.2f, wc)
        for (k in 0 until 8) tree(g, g.x0 + 3f + (k % 2) * (g.x1 - g.x0 - 6f), g.z0 + 5f + (k / 2) * 10f, 1.1f)
        for (k in 0 until 3) publicBench(b, cx - 6f + k * 6f, g.z1 - 3f, 0f, -1f)
        return 40f
    }

    /** Anel (coroa circular) de raio r0..r1 entre as alturas y0..y1, com face de cima, laterais de dentro e de fora. */
    fun ringWall(b: MB, x: Float, z: Float, r0: Float, r1: Float, y0: Float, y1: Float, c: Int, n: Int = 40) {
        for (k in 0 until n) {
            val a0 = k * 6.2832f / n; val a1 = (k + 1) * 6.2832f / n
            val c0 = cos(a0); val s0 = sin(a0); val c1 = cos(a1); val s1 = sin(a1)
            q(b, P(x + c0 * r1, y1, z + s0 * r1) + P(x + c1 * r1, y1, z + s1 * r1) + P(x + c1 * r0, y1, z + s1 * r0) + P(x + c0 * r0, y1, z + s0 * r0), c)
            q(b, P(x + c0 * r1, y0, z + s0 * r1) + P(x + c1 * r1, y0, z + s1 * r1) + P(x + c1 * r1, y1, z + s1 * r1) + P(x + c0 * r1, y1, z + s0 * r1), shade(c, -6))
            q(b, P(x + c1 * r0, y0, z + s1 * r0) + P(x + c0 * r0, y0, z + s0 * r0) + P(x + c0 * r0, y1, z + s0 * r0) + P(x + c1 * r0, y1, z + s1 * r0), shade(c, -14))
        }
    }

    /**
     * Etapa 127: chafariz de três andares com água de verdade (o mesmo shader dos lagos) no tanque e nas taças,
     * jatos em arco caindo de uma taça para a outra, bordas com moldura e fundo de azulejo.
     */
    private fun fountain(g: Gen, x: Float, z: Float) {
        val b = g.b
        val stone = C("#E3DCCD"); val st2 = C("#D2C9B7")
        b.m(Mt.STONE, 0.8f)
        // tanque: mureta com moldura dupla
        ringWall(b, x, z, 4.05f, 4.45f, CURB, CURB + 0.55f, stone, 48)
        ringWall(b, x, z, 4.4f, 4.6f, CURB, CURB + 0.12f, st2, 48)
        ringWall(b, x, z, 4.0f, 4.5f, CURB + 0.55f, CURB + 0.62f, shade(stone, 8), 48)
        b.m(Mt.TILE, 1.4f); b.cyl(x, CURB - 0.3f, z, 4.06f, 4.06f, 0.24f, C("#5FA9C4"), true, 40)   // fundo de azulejo (abaixo do piso da praça)
        // pedestal, taça de baixo (bojo), coluna, taça do meio, coluna, taça de cima, pinha
        b.m(Mt.STONE, 0.8f)
        b.cyl(x, CURB, z, 0.75f, 0.6f, 0.25f, st2, true, 16)
        b.cyl(x, CURB + 0.25f, z, 0.42f, 0.36f, 1.25f, stone, true, 16)
        for (k in 0 until 3) b.cyl(x, CURB + 0.4f + k * 0.4f, z, 0.45f, 0.45f, 0.06f, st2, true, 16)
        b.cyl(x, CURB + 1.5f, z, 0.35f, 1.0f, 0.5f, stone, true, 24)
        ringWall(b, x, z, 1.62f, 1.78f, CURB + 2.0f, CURB + 2.22f, stone, 32)
        b.cyl(x, CURB + 2.0f, z, 1.0f, 1.7f, 0.02f, stone, true, 32)
        b.cyl(x, CURB + 2.22f, z, 0.24f, 0.18f, 0.85f, stone, true, 12)
        b.cyl(x, CURB + 3.0f, z, 0.18f, 0.55f, 0.28f, stone, true, 18)
        ringWall(b, x, z, 0.62f, 0.72f, CURB + 3.28f, CURB + 3.4f, stone, 24)
        b.cyl(x, CURB + 3.28f, z, 0.55f, 0.66f, 0.02f, stone, true, 24)
        b.cyl(x, CURB + 3.4f, z, 0.08f, 0.05f, 0.3f, stone, true, 8)
        ball(b, x, CURB + 3.74f, z, 0.11f, stone, 0.15f, 8)
        // água nos três níveis
        if (g.reg) { City.lakes.add(floatArrayOf(x, z, -4.04f, CURB + 0.42f)); City.lakes.add(floatArrayOf(x, z, -1.6f, CURB + 2.18f)); City.lakes.add(floatArrayOf(x, z, -0.6f, CURB + 3.36f)) }
        // jatos: arcos de água (vidro) caindo da taça de cima para a do meio e da do meio para o tanque
        b.m(Mt.GLASS)
        for ((r0, y0, r1, y1, n) in listOf(arrayOf(0.66f, CURB + 3.38f, 1.25f, CURB + 2.2f, 12f), arrayOf(1.75f, CURB + 2.2f, 2.9f, CURB + 0.45f, 18f))) {
            for (k in 0 until n.toInt()) {
                val a = k * 6.2832f / n
                var px = x + cos(a) * r0; var py = y0; var pz = z + sin(a) * r0
                for (st in 1..5) {
                    val t = st / 5f
                    val rr = r0 + (r1 - r0) * t; val yy = y0 + 0.12f * t - (y0 - y1 + 0.12f) * t * t
                    val nx = x + cos(a) * rr; val nz = z + sin(a) * rr
                    b.al = 0.5f - 0.15f * t
                    CityGeo.limb(b, px, py, pz, nx, yy, nz, 0.03f + 0.01f * t, 0.03f + 0.015f * t, C("#E3F7FF"), 4)
                    px = nx; py = yy; pz = nz
                }
            }
        }
        b.al = 0.55f; CityGeo.limb(b, x, CURB + 3.8f, z, x, CURB + 4.35f, z, 0.05f, 0.02f, C("#E8FAFF"), 6)
        b.al = 1f
        g.solid(x - 4.5f, z - 4.5f, x + 4.5f, z + 4.5f)
        g.f.m(Mt.STONE, 0.8f); g.f.cyl(x, CURB, z, 4.5f, 4.5f, 0.6f, stone, true, 16)
    }

    /** Poste colonial de praça: base octogonal, fuste canelado verde-escuro, braços com quatro lanternas. */
    private fun colonialLamp(b: MB, x: Float, z: Float) {
        Shade.pole(x, z, 4.2f, 0.1f)
        val gc = C("#1E3328")
        b.m(Mt.METAL, 1f)
        b.cyl(x, CURB, z, 0.28f, 0.24f, 0.45f, gc, true, 8)
        b.cyl(x, CURB + 0.45f, z, 0.16f, 0.16f, 0.08f, shade(gc, 10), true, 8)
        b.cyl(x, CURB + 0.53f, z, 0.1f, 0.07f, 3.0f, gc, true, 8)
        b.cyl(x, CURB + 3.5f, z, 0.12f, 0.12f, 0.08f, shade(gc, 10), true, 8)
        for (k in 0 until 4) {
            val a = k * 1.5708f + 0.785f
            val ex = x + cos(a) * 0.55f; val ez = z + sin(a) * 0.55f
            CityGeo.limb(b, x, CURB + 3.45f, z, ex, CURB + 3.75f, ez, 0.025f, 0.02f, gc, 4)
            b.m(Mt.METAL, 1f); b.cyl(ex, CURB + 3.72f, ez, 0.09f, 0.14f, 0.05f, gc, true, 6)
            b.m(Mt.PLAIN); b.cyl(ex, CURB + 3.77f, ez, 0.11f, 0.13f, 0.32f, C("#FFF4D2"), false, 6)
            b.m(Mt.METAL, 1f); b.cyl(ex, CURB + 4.09f, ez, 0.15f, 0.03f, 0.14f, gc, true, 6)
        }
        b.cyl(x, CURB + 3.58f, z, 0.08f, 0.02f, 0.5f, gc, true, 6)
    }

    /** Coreto octogonal: base com degraus, colunas de ferro, guarda-corpo com balaústres, telhado com beiral e lambrequim. */
    /** Prisma octogonal com vértices em 22,5° + 45°·k (mesmo alinhamento das colunas do coreto). */
    private fun oct(b: MB, kx: Float, y0: Float, kz: Float, r: Float, h: Float, col: Int) {
        for (k in 0 until 8) {
            val a0 = k * 0.7854f + 0.3927f; val a1 = (k + 1) * 0.7854f + 0.3927f
            val x0 = kx + cos(a0) * r; val z0 = kz + sin(a0) * r; val x1 = kx + cos(a1) * r; val z1 = kz + sin(a1) * r
            q(b, P(x0, y0 + h, z0) + P(x1, y0 + h, z1) + P(x1, y0, z1) + P(x0, y0, z0), col)
            CityGeo.tri(b, P(x0, y0 + h, z0) + P(kx, y0 + h, kz) + P(x1, y0 + h, z1), col)
            CityGeo.tri(b, P(x1, y0, z1) + P(kx, y0, kz) + P(x0, y0, z0), col)
        }
    }

    private fun coreto(g: Gen, kx: Float, kz: Float) {
        val b = g.b
        val R = 4.2f; val yb = CURB + 0.8f
        b.m(Mt.STONE, 0.8f)
        // Etapa 129: octógonos alinhados com as colunas (vértices em 22,5° + 45°·k); o lado do norte (270°) é a entrada, de frente para a alameda
        oct(b, kx, CURB, kz, R + 0.6f, 0.27f, C("#D8CFBE"))
        oct(b, kx, CURB + 0.27f, kz, R + 0.3f, 0.27f, C("#DED5C4"))
        oct(b, kx, CURB + 0.54f, kz, R, 0.26f, C("#E6DDCC"))
        b.m(Mt.STONE, 0.8f); b.box(kx, CURB + 0.07f, kz - (R + 0.6f) * 0.924f - 0.4f, 2.6f, 0.14f, 0.8f, C("#CFC6B4"))   // degrau da entrada, no eixo
        b.m(Mt.WOOD, 1f); oct(b, kx, yb - 0.01f, kz, R - 0.1f, 0.02f, C("#A0764F"))
        val iron = C("#F4F1EA")
        for (k in 0 until 8) {
            val a = k * 0.7854f + 0.3927f
            val px = kx + cos(a) * (R - 0.2f); val pz = kz + sin(a) * (R - 0.2f)
            b.m(Mt.METAL, 1f)
            b.cyl(px, yb, pz, 0.1f, 0.1f, 0.18f, iron, true, 8)
            b.cyl(px, yb + 0.18f, pz, 0.065f, 0.065f, 2.8f, iron, true, 8)
            b.cyl(px, yb + 2.95f, pz, 0.12f, 0.08f, 0.15f, iron, true, 8)
            // arco decorativo entre colunas
            val a2 = (k + 1) * 0.7854f + 0.3927f
            val qx = kx + cos(a2) * (R - 0.2f); val qz = kz + sin(a2) * (R - 0.2f)
            for (st in 0 until 6) {
                val t0 = st / 6f; val t1 = (st + 1) / 6f
                val h0 = 2.65f + 0.3f * (1 - (2 * t0 - 1) * (2 * t0 - 1)); val h1 = 2.65f + 0.3f * (1 - (2 * t1 - 1) * (2 * t1 - 1))
                CityGeo.limb(b, px + (qx - px) * t0, yb + h0, pz + (qz - pz) * t0, px + (qx - px) * t1, yb + h1, pz + (qz - pz) * t1, 0.03f, 0.03f, iron, 4)
            }
            // guarda-corpo (menos na entrada)
            if (k != 5) {   // lado norte (entre as colunas 5 e 6) fica sem guarda-corpo: é a entrada
                CityGeo.limb(b, px, yb + 0.9f, pz, qx, yb + 0.9f, qz, 0.035f, 0.035f, iron, 4)
                CityGeo.limb(b, px, yb + 0.12f, pz, qx, yb + 0.12f, qz, 0.03f, 0.03f, iron, 4)
                for (m in 1 until 8) { val t = m / 8f; val bx = px + (qx - px) * t; val bz = pz + (qz - pz) * t; b.cyl(bx, yb + 0.12f, bz, 0.025f, 0.025f, 0.78f, iron, true, 5) }
            }
        }
        // telhado octogonal com beiral e lambrequim
        val yr = yb + 3.1f
        b.m(Mt.ROOF, 0.6f)
        for (k in 0 until 8) {
            val a0 = k * 0.7854f + 0.3927f; val a1 = (k + 1) * 0.7854f + 0.3927f
            CityGeo.tri(b, P(kx + cos(a0) * (R + 0.5f), yr, kz + sin(a0) * (R + 0.5f)) + P(kx, yr + 2.0f, kz) + P(kx + cos(a1) * (R + 0.5f), yr, kz + sin(a1) * (R + 0.5f)), C("#2F5D3A"))
        }
        b.m(Mt.WOOD, 1f)
        for (k in 0 until 8) {
            val a0 = k * 0.7854f + 0.3927f; val a1 = (k + 1) * 0.7854f + 0.3927f
            q(b, P(kx + cos(a0) * (R + 0.5f), yr, kz + sin(a0) * (R + 0.5f)) + P(kx + cos(a1) * (R + 0.5f), yr, kz + sin(a1) * (R + 0.5f)) + P(kx + cos(a1) * (R + 0.5f), yr - 0.25f, kz + sin(a1) * (R + 0.5f)) + P(kx + cos(a0) * (R + 0.5f), yr - 0.25f, kz + sin(a0) * (R + 0.5f)), C("#F4F1EA"))
            for (m in 0 until 6) {   // lambrequim (recortes)
                val t0 = m / 6f; val t1 = (m + 1) / 6f; val tm = (t0 + t1) / 2
                fun pt(t: Float, dy: Float) = P(kx + (cos(a0) + (cos(a1) - cos(a0)) * t) * (R + 0.5f), yr - 0.25f - dy, kz + (sin(a0) + (sin(a1) - sin(a0)) * t) * (R + 0.5f))
                CityGeo.tri(b, pt(t0, 0f) + pt(t1, 0f) + pt(tm, 0.14f), C("#F4F1EA"))
            }
        }
        oct(b, kx, yr - 0.02f, kz, R + 0.45f, 0.02f, C("#E8E0D2"))
        b.m(Mt.METAL, 1f); b.cyl(kx, yr + 1.95f, kz, 0.06f, 0.02f, 0.6f, C("#C9A227"), true, 6); ball(b, kx, yr + 2.1f, kz, 0.1f, C("#C9A227"), 0.1f, 6)
        g.solid(kx - R - 0.3f, kz - R - 0.3f, kx + R + 0.3f, kz + R + 0.3f)
    }

    /** Banca de jornal: caixa verde com toldo, revistas penduradas na frente, jornais no balcão. */
    private fun newsstand(g: Gen, x: Float, z: Float, fx: Float, fz: Float) {
        val b = g.b
        val l = L(x, z, fx, fz)
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, CURB + 1.25f, 0.2f, 2.6f, 2.5f, 1.6f, C("#1F6B45"))
        lb(b, l, 0f, CURB + 2.56f, 0f, 2.9f, 0.12f, 2.2f, C("#17543A"))
        b.m(Mt.FABRIC, 1f); lb(b, l, 0f, CURB + 2.45f, -1.0f, 2.8f, 0.06f, 0.6f, C("#C62828"))
        // vitrine de revistas (textura de mercadoria) e balcão
        CityInt.goods(b, l.wx(0f, -0.62f), CURB + 0.95f, l.wz(0f, -0.62f), if (l.alongX) 2.4f else 0.04f, 1.25f, if (l.alongX) 0.04f else 2.4f, C("#FFFFFF"), Mt.BOOKS)
        b.m(Mt.WOOD, 1f); lb(b, l, 0f, CURB + 0.45f, -0.7f, 2.4f, 0.9f, 0.3f, C("#17543A"))
        b.m(Mt.PLAIN); for (k in 0 until 6) lb(b, l, -1.0f + k * 0.4f, CURB + 0.92f, -0.72f, 0.32f, 0.03f, 0.24f, C(arrayOf("#F5F5F5", "#FFF59D", "#E3F2FD", "#FCE4EC")[k % 4]))
        g.solid(x - 1.5f, z - 1.3f, x + 1.5f, z + 1.3f)
        Shade.box(min(l.wx(-1.3f, -0.6f), l.wx(1.3f, 1.0f)), min(l.wz(-1.3f, -0.6f), l.wz(1.3f, 1.0f)), max(l.wx(-1.3f, -0.6f), l.wx(1.3f, 1.0f)), max(l.wz(-1.3f, -0.6f), l.wz(1.3f, 1.0f)), 2.6f)
    }

    /** Etapa 129: canteiro retangular com mureta de pedra, cerca viva só nos lados de fora, grama, flores e uma árvore no centro. */
    private fun bed(g: Gen, x0: Float, z0: Float, x1: Float, z1: Float, kind: Int) {
        val b = g.b
        val mx = (x0 + x1) / 2; val mz = (z0 + z1) / 2; val w = x1 - x0; val d = z1 - z0
        b.m(Mt.STONE, 0.8f)
        val cc = C("#CFC6B4")
        b.box(mx, CURB + 0.15f, z0 + 0.12f, w, 0.3f, 0.24f, cc); b.box(mx, CURB + 0.15f, z1 - 0.12f, w, 0.3f, 0.24f, cc)
        b.box(x0 + 0.12f, CURB + 0.15f, mz, 0.24f, 0.3f, d - 0.48f, cc); b.box(x1 - 0.12f, CURB + 0.15f, mz, 0.24f, 0.3f, d - 0.48f, cc)
        b.m(Mt.GRASS, 0.3f); b.box(mx, CURB + 0.12f, mz, w - 0.4f, 0.24f, d - 0.4f, C("#9CC77A"))
        // cerca viva baixa em todo o perímetro, espaçada igual
        b.m(Mt.LEAFB, 1f)
        val nx = max(2, (w / 0.7f).toInt()); val nz = max(2, (d / 0.7f).toInt())
        for (k in 0 until nx) { val x = x0 + 0.55f + (w - 1.1f) * (k + 0.5f) / nx
            for (zz in floatArrayOf(z0 + 0.55f, z1 - 0.55f)) b.box(x, CURB + 0.5f, zz, (w - 1.1f) / nx * 0.92f, 0.46f, 0.6f, C(if (k % 2 == 0) "#3F7A35" else "#467F3A")) }
        for (k in 0 until nz) { val z = z0 + 1.15f + (d - 2.3f) * (k + 0.5f) / nz
            for (xx in floatArrayOf(x0 + 0.55f, x1 - 0.55f)) b.box(xx, CURB + 0.5f, z, 0.6f, 0.46f, (d - 2.3f) / nz * 0.92f, C(if (k % 2 == 0) "#3F7A35" else "#467F3A")) }
        flowers(g, x0 + 1.4f, z0 + 1.4f, x1 - 1.4f, z1 - 1.4f, 30, CURB + 0.24f)
        tree(g, mx, mz, 1.15f, CURB + 0.24f, kind)
        g.solid(x0, z0, x1, z1)
    }

    /**
     * Etapa 127/129: praça. O quarteirão é estreito (26 × 48 m), então tudo é simétrico nos dois eixos do centro:
     * alamedas em cruz até o largo redondo com chafariz; quatro canteiros retangulares iguais; no fim norte o obelisco
     * (com banca e pipoca dos lados) e no fim sul o coreto, ambos no eixo; bancos e postes em posições espelhadas.
     */
    private fun praca(g: Gen): Float {
        val b = g.b; val rng = g.rng
        val cx = (g.x0 + g.x1) / 2; val cz = (g.z0 + g.z1) / 2
        val hw = (g.x1 - g.x0) / 2; val hd = (g.z1 - g.z0) / 2
        val light = C("#ECE6D8"); val dark = C("#3B3936"); val gran = C("#9C978E")
        val RL = 8.0f   // raio do largo
        // alamedas em cruz (de fora até o largo), com guias de granito dos dois lados
        b.m(Mt.PAVER, 0.7f)
        val ln = hd - RL; val le = hw - RL
        for (sg in floatArrayOf(-1f, 1f)) {
            b.box(cx, CURB + 0.01f, cz + sg * (RL + ln / 2), 4.4f, 0.02f, ln, C("#E2D9C8"))
            b.box(cx + sg * (RL + le / 2), CURB + 0.01f, cz, le, 0.02f, 4.4f, C("#E2D9C8"))
        }
        b.m(Mt.STONE, 1f)
        for (sg in floatArrayOf(-1f, 1f)) for (sd in floatArrayOf(-2.3f, 2.3f)) {
            b.box(cx + sd, CURB + 0.03f, cz + sg * (RL + ln / 2), 0.2f, 0.06f, ln, gran)
            b.box(cx + sg * (RL + le / 2), CURB + 0.03f, cz + sd, le, 0.06f, 0.2f, gran)
        }
        // largo circular: pedra portuguesa em ondas (3 faixas, claras e escuras)
        val nseg = 96
        b.m(Mt.STONE, 2.2f)
        fun rr(a: Float, bd: Int) = if (bd <= 0) 4.6f else if (bd >= 3) RL else 4.6f + bd * (RL - 4.6f) / 3f + 0.25f * sin(a * 8f + bd * 1.3f)
        for (k in 0 until nseg) {
            val a0 = k * 6.2832f / nseg; val a1 = (k + 1) * 6.2832f / nseg
            for (band in 0 until 3) {
                val ra0 = rr(a0, band); val ra1 = rr(a1, band); val rb0 = rr(a0, band + 1); val rb1 = rr(a1, band + 1)
                q(b, P(cx + cos(a0) * ra0, CURB + 0.022f, cz + sin(a0) * ra0) + P(cx + cos(a0) * rb0, CURB + 0.022f, cz + sin(a0) * rb0) + P(cx + cos(a1) * rb1, CURB + 0.022f, cz + sin(a1) * rb1) + P(cx + cos(a1) * ra1, CURB + 0.022f, cz + sin(a1) * ra1), if (band % 2 == 0) light else dark)
            }
        }
        ringWall(b, cx, cz, RL, RL + 0.22f, CURB, CURB + 0.075f, gran, 64)
        fountain(g, cx, cz)
        // pombos ciscando entre o chafariz e os bancos
        b.m(Mt.PLAIN)
        for (k in 0 until 9) {
            val a = rng.r(0f, 6.28f); val r = rng.r(5.0f, 5.8f)
            val px = cx + cos(a) * r; val pz = cz + sin(a) * r; val h = rng.r(0f, 6.28f)
            ball(b, px, CURB + 0.1f, pz, 0.09f, C(if (k % 3 == 0) "#8A8C93" else "#6E7078"), 0.07f, 6)
            ball(b, px + cos(h) * 0.09f, CURB + 0.16f, pz + sin(h) * 0.09f, 0.04f, C("#5A5C63"), 0.04f, 5)
        }
        // quatro canteiros iguais, um em cada quadrante (fora do largo, longe das alamedas)
        val bx0 = 4.2f; val bx1 = hw - 0.6f; val bz0 = 8.0f; val bz1 = 14.0f
        for (sx in floatArrayOf(-1f, 1f)) for (sz in floatArrayOf(-1f, 1f))
            bed(g, if (sx > 0) cx + bx0 else cx - bx1, if (sz > 0) cz + bz0 else cz - bz1, if (sx > 0) cx + bx1 else cx - bx0, if (sz > 0) cz + bz1 else cz - bz0, if (sz > 0) 3 else 2)
        // oito bancos de ferro fundido encostados na mureta do largo, virados para o chafariz, espelhados nos eixos
        for (sx in floatArrayOf(-1f, 1f)) for (sz in floatArrayOf(-1f, 1f)) {
            publicBench(b, cx + sx * 6.9f, cz + sz * 3.6f, -sx, 0f); g.solid(cx + sx * 6.9f - 0.5f, cz + sz * 3.6f - 0.95f, cx + sx * 6.9f + 0.5f, cz + sz * 3.6f + 0.95f)
            publicBench(b, cx + sx * 3.6f, cz + sz * 6.9f, 0f, -sz); g.solid(cx + sx * 3.6f - 0.95f, cz + sz * 6.9f - 0.5f, cx + sx * 3.6f + 0.95f, cz + sz * 6.9f + 0.5f)
        }
        // postes coloniais: anel atrás dos bancos (22,5° + 45°·k) e dois de cada lado das alamedas, tudo espelhado
        for (k in 0 until 8) { val a = (22.5f + 45f * k) * PI.toFloat() / 180f; colonialLamp(b, cx + 8.75f * cos(a), cz + 8.75f * sin(a)) }
        for (sx in floatArrayOf(-1f, 1f)) for (sz in floatArrayOf(-1f, 1f)) {
            colonialLamp(b, cx + sx * 2.9f, cz + sz * 11f)       // na alameda norte-sul, ao lado de cada canteiro
            colonialLamp(b, cx + sx * 10.8f, cz + sz * 2.9f)     // na alameda leste-oeste
            colonialLamp(b, cx + sx * 2.9f, cz + sz * 20.2f)     // junto ao obelisco / coreto
        }
        // fim norte: obelisco no eixo, num pátio redondo; banca e pipoca espelhados dos lados
        val mz = cz - 19.2f
        b.m(Mt.STONE, 0.8f)
        b.cyl(cx, CURB, mz, 3.6f, 3.6f, 0.03f, C("#E6DDCC"), true, 32)
        ringWall(b, cx, mz, 3.45f, 3.65f, CURB, CURB + 0.08f, gran, 32)
        b.box(cx, CURB + 0.15f + 0.03f, mz, 2.2f, 0.3f, 2.2f, C("#CFC6B4")); b.box(cx, CURB + 0.48f, mz, 1.6f, 0.3f, 1.6f, C("#D6CDBB"))
        b.box(cx, CURB + 1.23f, mz, 1.0f, 1.2f, 1.0f, C("#DED5C4"))
        b.cyl(cx, CURB + 1.83f, mz, 0.42f, 0.12f, 3.6f, C("#E6DDCC"), true, 4)
        b.m(Mt.METAL, 1f); b.box(cx, CURB + 1.28f, mz + 0.505f, 0.8f, 0.5f, 0.02f, C("#7A5C2E"))
        sign(b, cx, CURB + 1.13f, mz + 0.52f, 0f, 1f, 0.7f, 0.3f, City.signIdx("PRAÇA CENTRAL"), false)   // placa virada para o largo
        Shade.box(cx - 0.5f, mz - 0.5f, cx + 0.5f, mz + 0.5f, 4.5f)
        g.solid(cx - 1.1f, mz - 1.1f, cx + 1.1f, mz + 1.1f)
        newsstand(g, cx - 9.6f, mz, 1f, 0f)
        run {
            val px = cx + 9.2f; val pz = mz
            b.m(Mt.METAL, 1f); b.box(px, CURB + 0.75f, pz, 1.0f, 0.7f, 0.6f, C("#C62828")); b.box(px, CURB + 1.15f, pz, 1.0f, 0.1f, 0.6f, C("#FAFAFA"))
            b.m(Mt.GLASS); b.al = 0.45f; b.box(px, CURB + 1.45f, pz, 0.8f, 0.5f, 0.5f, C("#FFF8E1")); b.al = 1f
            b.m(Mt.PLAIN); for (k in 0 until 14) ball(b, px - 0.3f + (k % 5) * 0.15f, CURB + 1.25f + (k / 5) * 0.06f, pz - 0.1f + (k % 3) * 0.1f, 0.05f, C("#FFF3C4"), 0.04f, 4)
            b.m(Mt.METAL, 1f); for (sd in floatArrayOf(-0.4f, 0.4f)) b.cyl(px + sd, CURB, pz + 0.32f, 0.2f, 0.2f, 0.04f, C("#222222"), true, 10)
            b.cyl(px, CURB + 1.7f, pz, 0.02f, 0.02f, 0.8f, C("#888888"), true, 5)
            b.m(Mt.FABRIC, 1f); b.cyl(px, CURB + 2.5f, pz, 0.9f, 0.05f, 0.35f, C("#FBC02D"), true, 10)
            g.solid(px - 0.6f, pz - 0.4f, px + 0.6f, pz + 0.4f)
        }
        // fim sul: coreto no eixo
        coreto(g, cx, cz + 19.2f)
        g.place(City.Place("Praça Central", cx, cz, 0xFF43A047.toInt(), 'P'))
        return 10f
    }

    private fun park(g: Gen): Float {
        val b = g.b; val rng = g.rng
        val cx = (g.x0 + g.x1) / 2; val cz = (g.z0 + g.z1) / 2
        lake(g, cx, cz, 12.5f)
        // caminho circular contínuo em volta do lago (piso intertravado com meio-fio de pedra)
        run {
            val r0 = 18.0f; val r1 = 20.4f; val n = 72
            b.m(Mt.PAVER, 0.7f)
            for (k in 0 until n) {
                val a0 = k * 6.2832f / n; val a1 = (k + 1) * 6.2832f / n
                q(b, P(cx + r0 * cos(a0), CURB + 0.03f, cz + r0 * sin(a0)) + P(cx + r1 * cos(a0), CURB + 0.03f, cz + r1 * sin(a0)) + P(cx + r1 * cos(a1), CURB + 0.03f, cz + r1 * sin(a1)) + P(cx + r0 * cos(a1), CURB + 0.03f, cz + r0 * sin(a1)), C("#E4D6BC"))
            }
            b.m(Mt.STONE, 1f)
            for (k in 0 until n) {
                val a0 = k * 6.2832f / n; val a1 = (k + 1) * 6.2832f / n
                for (rr in floatArrayOf(r0 - 0.08f, r1 + 0.08f)) {
                    val x0 = cx + rr * cos(a0); val z0 = cz + rr * sin(a0); val x1 = cx + rr * cos(a1); val z1 = cz + rr * sin(a1)
                    val nx = cos((a0 + a1) / 2) * 0.08f; val nz = sin((a0 + a1) / 2) * 0.08f
                    q(b, P(x0 - nx, CURB + 0.07f, z0 - nz) + P(x0 + nx, CURB + 0.07f, z0 + nz) + P(x1 + nx, CURB + 0.07f, z1 + nz) + P(x1 - nx, CURB + 0.07f, z1 - nz), C("#B8B2A6"))
                }
            }
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
            if (dx * dx + dz * dz < 13f * 13f) continue
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

    private const val CW = 0.24f   // largura da guia

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
            for (iv in freeIntervals(X0, X1, bandX, -SIDE)) {   // Etapa 125: calçada cobre também os cantos dos cruzamentos
                // Etapa 126: calçada até a guia (sem sobrepor) e guia um pouco mais alta e saliente: nada de faces no mesmo plano piscando
                groundBox(b, iv[0], za, iv[1], za + SIDE - CW, Mt.PAVER, 0.9f, walk); groundBox(g.f, iv[0], za, iv[1], za + SIDE, Mt.PAVER, 0.9f, walk)
                groundBox(b, iv[0], zb - SIDE + CW, iv[1], zb, Mt.PAVER, 0.9f, walk); groundBox(g.f, iv[0], zb - SIDE, iv[1], zb, Mt.PAVER, 0.9f, walk)
                b.m(Mt.STONE, 1f)
                b.box((iv[0] + iv[1]) / 2, (CURB + 0.03f) / 2, za + SIDE - CW / 2 + 0.01f, iv[1] - iv[0], CURB + 0.03f, CW + 0.02f, curbC)
                b.box((iv[0] + iv[1]) / 2, (CURB + 0.03f) / 2, zb - SIDE + CW / 2 - 0.01f, iv[1] - iv[0], CURB + 0.03f, CW + 0.02f, curbC)
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
                // Etapa 129: mobiliário da calçada simétrico — postes e árvores alternados, espelhados nos dois lados e centrados no trecho
                val pos = furniturePos(iv[0] + 6f, iv[1] - 6f)
                for ((n, x) in pos.withIndex()) {
                    val sp = if (pos.size > 1) pos[1] - pos[0] else 9f
                    val pk = nearPraca(x, za + 1f) || nearPraca(x, zb - 1f)   // Etapa 129: nada na frente da entrada da praça
                    if (pk) { }
                    else if (n % 2 == 0) { streetLamp(b, x, za + 0.6f, 0f, 1f); streetLamp(b, x, zb - 0.6f, 0f, -1f) }
                    else { if (k == 7) { palm(g, x, za + 1.3f, 0.9f); palm(g, x, zb - 1.3f, 0.9f) } else { streetTree(g, x, za + 1.4f); streetTree(g, x, zb - 1.4f) } }
                    if (n < pos.size - 1) {
                        val mx = x + sp / 2
                        manhole(b, mx, zc + (if (n % 2 == 0) 2.2f else -2.2f)); drain(b, mx, za + SIDE + 0.25f, true); drain(b, mx, zb - SIDE - 0.25f, true)
                    }
                    if (n % 4 == 1 && !pk) { trashBin(b, x + 1.7f, za + 0.5f); hydrant(b, x + 1.7f, zb - 0.45f) }
                }
                if (pos.size >= 5 && ii % 2 == 0) { val sp = pos[1] - pos[0]; busStop(g, pos[pos.size / 2] + sp / 2, za + 1.3f, 1f) }
            }
        }
        for (k in 0 until 8) {
            val xa = bandX[k * 2]; val xb = bandX[k * 2 + 1]; val xc = (xa + xb) / 2
            val segs = freeIntervals(Z0, Z1, bandZ, -SIDE)
            for (bb in arrayOf(b, g.f)) { bb.m(Mt.ASPHALT, 0.25f); for (iv in segs) bb.plane(xa + SIDE, iv[0], xb - SIDE, iv[1], 0f, asph) }
            for (iv in freeIntervals(Z0, Z1, bandZ)) {
                groundBox(b, xa, iv[0], xa + SIDE - CW, iv[1], Mt.PAVER, 0.9f, walk); groundBox(g.f, xa, iv[0], xa + SIDE, iv[1], Mt.PAVER, 0.9f, walk)
                groundBox(b, xb - SIDE + CW, iv[0], xb, iv[1], Mt.PAVER, 0.9f, walk); groundBox(g.f, xb - SIDE, iv[0], xb, iv[1], Mt.PAVER, 0.9f, walk)
                b.m(Mt.STONE, 1f)
                b.box(xa + SIDE - CW / 2 + 0.01f, (CURB + 0.03f) / 2, (iv[0] + iv[1]) / 2, CW + 0.02f, CURB + 0.03f, iv[1] - iv[0], curbC)
                b.box(xb - SIDE + CW / 2 - 0.01f, (CURB + 0.03f) / 2, (iv[0] + iv[1]) / 2, CW + 0.02f, CURB + 0.03f, iv[1] - iv[0], curbC)
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
                val pos = furniturePos(iv[0] + 6f, iv[1] - 6f)
                for ((n, z) in pos.withIndex()) {
                    val sp = if (pos.size > 1) pos[1] - pos[0] else 9f
                    val pk = nearPraca(xa + 1f, z) || nearPraca(xb - 1f, z)
                    if (pk) { }
                    else if (n % 2 == 0) { streetLamp(b, xa + 0.6f, z, 1f, 0f); streetLamp(b, xb - 0.6f, z, -1f, 0f) }
                    else { streetTree(g, xa + 1.4f, z); streetTree(g, xb - 1.4f, z) }
                    if (n < pos.size - 1) {
                        val mz = z + sp / 2
                        manhole(b, xc + (if (n % 2 == 0) 2.2f else -2.2f), mz); drain(b, xa + SIDE + 0.25f, mz, false); drain(b, xb - SIDE - 0.25f, mz, false)
                    }
                    if (n % 4 == 1 && !pk) { trashBin(b, xa + 0.5f, z + 1.7f); hydrant(b, xb - 0.45f, z + 1.7f) }
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
                    b.cyl(x, CURB, z, 0.16f, 0.12f, 0.5f, C("#2E3236"), true, 8)
                    b.cyl(x, CURB + 0.5f, z, 0.1f, 0.08f, 3.9f, C("#3A3F44"), true, 8)
                    for ((hi, h) in headPos(x, z, cx, cz).withIndex()) {
                        // caixa com placa de fundo amarela e pretas, e "bonés" sobre cada luz (virados para o trânsito do eixo)
                        val alongX = hi == 0
                        b.box(h[0], h[1], h[2], 0.36f, 1.0f, 0.36f, C("#1E1F22"))
                        b.m(Mt.PLAIN)
                        if (alongX) b.box(h[0], h[1], h[2], 0.06f, 1.2f, 0.56f, C("#F2C230")) else b.box(h[0], h[1], h[2], 0.56f, 1.2f, 0.06f, C("#F2C230"))
                        b.m(Mt.METAL, 1f)
                        for (k in -1..1) for (sd in floatArrayOf(-1f, 1f)) {
                            if (alongX) b.box(h[0] + sd * 0.23f, h[1] + k * 0.3f + 0.13f, h[2], 0.12f, 0.03f, 0.3f, C("#141516"))
                            else b.box(h[0], h[1] + k * 0.3f + 0.13f, h[2] + sd * 0.23f, 0.3f, 0.03f, 0.12f, C("#141516"))
                        }
                    }
                    b.m(Mt.PLAIN)
                    b.box(x, CURB + 1.1f, z, 0.16f, 0.22f, 0.16f, C("#F2C230"))   // botoeira de pedestre
                    b.box(x, CURB + 1.13f, z + (if (cz == 0) 0.081f else -0.081f), 0.08f, 0.08f, 0.01f, C("#212121"))
                    // piso tátil amarelo nas duas rampas da esquina e frades
                    b.m(Mt.STONE, 4f)
                    val dxs = if (cx == 0) 1f else -1f; val dzs = if (cz == 0) 1f else -1f
                    b.plane(x + dxs * 1.2f - 0.6f, z - 0.55f + dzs * 0.2f, x + dxs * 1.2f + 0.6f, z + 0.55f + dzs * 0.2f, CURB + 0.006f, C("#F7C948"))
                    b.plane(x - 0.55f + dxs * 0.2f, z + dzs * 1.2f - 0.6f, x + 0.55f + dxs * 0.2f, z + dzs * 1.2f + 0.6f, CURB + 0.006f, C("#F7C948"))
                    b.m(Mt.METAL, 1f)
                    b.cyl(x - dxs * 0.6f, CURB, z - dzs * 0.6f, 0.08f, 0.07f, 0.85f, C("#455A64"), true, 6)
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

    /** Árvore de calçada: canteiro de terra com grade de ferro e a árvore no meio. */
    /** Etapa 129: posições igualmente espaçadas (~9 m), em número ímpar e simétricas no trecho [a, e] (poste-árvore-poste...). */
    /** Etapa 129: entradas da praça (eixos N-S em x=3 e L-O em z=54): poste, árvore e lixeira não ficam na frente delas. */
    private fun nearPraca(x: Float, z: Float): Boolean {
        val nsAxis = abs(x - 3f) < 3.0f && (abs(z - 30f) < 4.5f || abs(z - 78f) < 4.5f)
        val ewAxis = abs(z - 54f) < 3.0f && (abs(x + 10f) < 4.5f || abs(x - 16f) < 4.5f)
        return nsAxis || ewAxis
    }

    private fun furniturePos(a: Float, e: Float): List<Float> {
        val len = e - a
        if (len < 3f) return emptyList()
        var n = Math.round(len / 9f) + 1
        if (n % 2 == 0) n++
        while (n > 1 && len / (n - 1) < 6.5f) n -= 2
        if (n <= 1) return listOf((a + e) / 2)
        return List(n) { a + len * it / (n - 1) }
    }

    private fun streetTree(g: Gen, x: Float, z: Float) {
        val b = g.b
        b.m(Mt.PLAIN)
        b.plane(x - 0.6f, z - 0.6f, x + 0.6f, z + 0.6f, CURB + 0.004f, C("#4A3A2A"))
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-0.6f, 0.6f)) { b.box(x + s, CURB + 0.02f, z, 0.06f, 0.04f, 1.26f, C("#2F3336")); b.box(x, CURB + 0.02f, z + s, 1.26f, 0.04f, 0.06f, C("#2F3336")) }
        for (k in -2..2) b.box(x + k * 0.22f, CURB + 0.015f, z, 0.03f, 0.03f, 1.2f, C("#3A3F44"))
        tree(g, x, z, g.rng.r(0.85f, 1.05f), CURB, if (g.rng.chance(0.25f)) 2 + g.rng.i(2) else 4)
    }

    private fun manhole(b: MB, x: Float, z: Float) {
        b.m(Mt.METAL, 1f)
        b.cyl(x, 0.006f, z, 0.42f, 0.42f, 0.012f, C("#3C3F42"), true, 14)
        b.m(Mt.PLAIN)
        for (k in -2..2) b.plane(x - 0.3f, z + k * 0.12f - 0.015f, x + 0.3f, z + k * 0.12f + 0.015f, 0.02f, C("#2A2C2E"))
    }

    private fun drain(b: MB, x: Float, z: Float, alongX: Boolean) {
        b.m(Mt.METAL, 1f)
        if (alongX) b.box(x, 0.008f, z, 0.9f, 0.016f, 0.35f, C("#2B2D30")) else b.box(x, 0.008f, z, 0.35f, 0.016f, 0.9f, C("#2B2D30"))
        b.m(Mt.PLAIN)
        for (k in -3..3) if (alongX) b.plane(x + k * 0.11f - 0.02f, z - 0.15f, x + k * 0.11f + 0.02f, z + 0.15f, 0.018f, C("#111214")) else b.plane(x - 0.15f, z + k * 0.11f - 0.02f, x + 0.15f, z + k * 0.11f + 0.02f, 0.018f, C("#111214"))
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
            var d = 230.0 + (k % 3) * 20
            val rr = 55f + (k % 4) * 12f
            var cx: Float; var cz: Float
            // Etapa 128: o morro não pode entrar na cidade (cobria os fundos da igreja e de casas da beirada)
            while (true) {
                cx = ((X0 + X1) / 2 + d * cos(ang)).toFloat(); cz = ((Z0 + Z1) / 2 + d * sin(ang) * 0.9).toFloat()
                val ox = max(0f, max(X0 - 14f - cx, cx - X1 - 14f)); val oz = max(0f, max(Z0 - 14f - cz, cz - Z1 - 14f))
                if (sqrt(ox * ox + oz * oz) > rr || d > 900.0) break
                d += 6.0
            }
            CityGeo.ball(b, cx, -8f, cz, rr, mix(C("#7FAE7C"), C("#B9D3BC"), (k % 3) / 3f), 34f + (k % 3) * 8f, 12)
        }
        val c = City.Chunk(b.toMesh(true), null, X0 - 420f, Z0 - 420f, X1 + 420f, Z1 + 420f, 70f)
        c.pend = g.fl
        return c
    }
}
