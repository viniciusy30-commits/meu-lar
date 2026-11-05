package com.vinicius.meular

import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

object Finish {
    class Floor(val nome: String, val mat: Int, val tint: Int, val amostra: Int, val preco: Int)
    class Wall(val nome: String, val cor: Int, val preco: Int)

    val floors = listOf(
        Floor("Carvalho claro", Mt.FLOOR_L, C("#FFFFFF"), C("#D9AE7C"), 0),
        Floor("Madeira cinza", Mt.FLOOR_L, C("#B6B7C3"), C("#A9AAB4"), 120),
        Floor("Nogueira", Mt.FLOOR_D, C("#FFFFFF"), C("#7A4E32"), 150),
        Floor("Porcelanato", Mt.TILE, C("#FFFFFF"), C("#E6E3DC"), 200)
    )
    val walls = listOf(
        Wall("Creme", C("#F2E8DA"), 0),
        Wall("Branco gelo", C("#F6F6F4"), 40),
        Wall("Azul névoa", C("#C3D8EA"), 60),
        Wall("Verde sálvia", C("#BFD1B6"), 60),
        Wall("Rosa chá", C("#EFCFCA"), 60),
        Wall("Manteiga", C("#F4E3A6"), 60),
        Wall("Grafite", C("#9AA0AE"), 80)
    )
}

class Opening(val c: Double, val w: Double, val door: Boolean)

object Models {
    const val HH = 2.5

    // ------------------------------------------------------------ pequenos utilitários

    fun shadow(w: Int, h: Int): Mesh {
        val b = MB()
        b.blob(w / 2.0, 0.07, h / 2.0, w / 2.0 + 0.28, h / 2.0 + 0.28, 0.42f)
        return b.toMesh(true)
    }

    fun ring(w: Int, h: Int, c: Int): Mesh {
        val b = MB()
        val t = 0.07
        b.box(w / 2.0, 0.09, -0.03, w + 0.14, 0.02, t, c, false)
        b.box(w / 2.0, 0.09, h + 0.03, w + 0.14, 0.02, t, c, false)
        b.box(-0.03, 0.09, h / 2.0, t, 0.02, h + 0.14, c, false)
        b.box(w + 0.03, 0.09, h / 2.0, t, 0.02, h + 0.14, c, false)
        return b.toMesh(true)
    }

    // Sombra e anel de seleção do tamanho real do móvel (metros). A sombra fica centrada na origem.
    fun shadowF(w: Double, h: Double): Mesh {
        val b = MB()
        b.blob(0.0, 0.07, 0.0, w / 2.0 + 0.18, h / 2.0 + 0.18, 0.42f)
        return b.toMesh(true)
    }

    fun ringF(w: Double, h: Double, c: Int): Mesh {
        val b = MB()
        val t = 0.07
        b.box(w / 2.0, 0.09, -0.03, w + 0.14, 0.02, t, c, false)
        b.box(w / 2.0, 0.09, h + 0.03, w + 0.14, 0.02, t, c, false)
        b.box(-0.03, 0.09, h / 2.0, t, 0.02, h + 0.14, c, false)
        b.box(w + 0.03, 0.09, h / 2.0, t, 0.02, h + 0.14, c, false)
        return b.toMesh(true)
    }

    private fun leg(b: MB, x: Double, z: Double, h: Double, rb: Double, rt: Double, c: Int) =
        b.cyl(x, 0.0, z, rb, rt, h, c, true, 12)

    // ------------------------------------------------------------ móveis

    // Etapa 87: os móveis antigos (pacote f_*.bin e caixas) saíram do jogo; só sobram os GLB do Plano Mestre e as plantas.
    fun furniture(t: Type): Mesh {
        t.glb?.let { id -> Glb.get(id)?.let { return it.staticMesh(t.w / 2f, t.h / 2f) } }
        t.fl?.let { id ->
            val fb = Flora.Batch()
            // a cerca nasce no canto (0..2 m em x); o resto é centrado na área do item
            if (id == "fence_panel") fb.place(id, 0.0, 0.0, t.h / 2.0) else fb.place(id, t.w / 2.0, 0.0, t.h / 2.0)
            val parts = fb.build()
            if (parts.isNotEmpty()) return Mesh(parts)
        }
        return Mesh(emptyList())
    }

    // ------------------------------------------------------------ casa

    fun interior(gw: Int, gh: Int, fl: Finish.Floor): Mesh {
        val b = MB()
        b.m(fl.mat, 1f)
        b.plane(0, 0, gw, gh, 0.0, fl.tint)
        b.m(Mt.STONE, 0.5f)
        b.box(gw / 2.0, -0.205, gh / 2.0, gw + 0.5, 0.4, gh + 0.5, C("#C9C3B9"))
        return b.toMesh(true)
    }

    private fun curtains(b: MB, c: Double, w: Double, y0: Double, y1: Double, col: Int) {
        val rodY = y1 + 0.25
        val dk = C("#4A3426")
        b.m(Mt.WOOD)
        b.rbox(c, rodY, 0.1, w + 0.9, 0.035, 0.035, 0.015, dk, true, 1)
        b.sphere(c - w / 2 - 0.47, rodY, 0.1, 0.045, dk, 0.045, 6)
        b.sphere(c + w / 2 + 0.47, rodY, 0.1, 0.045, dk, 0.045, 6)
        val top = rodY - 0.05
        val bot = y0 - 0.5
        val hgt = top - bot
        b.m(Mt.FABRIC, 1.5f)
        val pwid = w * 0.30 + 0.4
        val n = 6
        for (side in intArrayOf(-1, 1)) {
            val inner = c + side * (w / 2 - w * 0.30)
            for (i in 0 until n) {
                val xi = inner + side * (pwid * (i + 0.5) / n)
                val zi = 0.075 + 0.028 * sin(i * 1.9)
                val tone = if (i % 2 == 0) col else shade(col, -14)
                b.rbox(xi, bot + hgt / 2, zi, pwid / n * 1.2, hgt, 0.045, 0.02, tone, true, 1)
            }
        }
    }

    fun wall(len: Double, ops: List<Opening>, tint: Int, ext: Boolean, art: Boolean): Mesh {
        val b = MB()
        val fl = Flora.Batch()
        val ti = 0.07
        val to = 0.10
        val tt = ti + to
        val xs = if (ext) -tt else 0.0
        val xe = if (ext) len + tt else len
        val outer = C("#F4E9D2")
        val wh = C("#F7F5F0")
        val sorted = ops.sortedBy { it.c }

        fun slab(x0: Double, x1: Double, y0: Double, y1: Double) {
            if (x1 - x0 < 0.001 || y1 - y0 < 0.001) return
            b.m(Mt.PLASTER, 0.5f)
            b.box((x0 + x1) / 2, (y0 + y1) / 2, -ti / 2, x1 - x0, y1 - y0, ti, tint)
            b.m(Mt.SIDING, 0.9f)
            b.box((x0 + x1) / 2, (y0 + y1) / 2, -ti - to / 2, x1 - x0, y1 - y0, to, outer)
        }

        var cur = xs
        for (o in sorted) {
            val x0 = o.c - o.w / 2
            val x1 = o.c + o.w / 2
            val ya = if (o.door) 0.0 else 0.92
            val yb = if (o.door) 2.1 else 1.95
            slab(cur, x0, 0.0, HH)
            slab(x0, x1, 0.0, ya)
            slab(x0, x1, yb, HH)
            cur = x1
        }
        slab(cur, xe, 0.0, HH)

        for (o in sorted) {
            val ww = o.w
            if (o.door) {
                // porta modelada: batente, soleira e folha aberta para fora (Etapa 68)
                fl.place("door_frame_110", o.c, 0.0, 0.0)
                b.m(Mt.METAL)
                b.rbox(o.c + ww / 2 + 0.45, 1.75, -0.2, 0.08, 0.14, 0.06, 0.02, C("#2B3036"), true, 1)
                b.m(Mt.PLAIN)
                b.sphere(o.c + ww / 2 + 0.45, 1.75, -0.24, 0.06, C("#FFE9A8"), 0.07, 7, false)
            } else {
                // Etapa 75: a cortina agora é tecido simulado (Cloth.kt); aqui ficam só a janela, a barra e os suportes
                val wn = Math.round(ww * 100).toInt()
                val id = if (wn >= 175) "190" else if (wn >= 140) "160" else "125"
                fl.place("win_$id", o.c, 0.0, 0.0)
                val half = ww / 2 + 0.10 + 0.5 + 0.06
                b.m(Mt.WOOD)
                b.rbox(o.c, 2.075, 0.215, half * 2, 0.028, 0.028, 0.012, C("#4A3426"), true, 1)
                b.m(Mt.PLAIN)
                for (sd in intArrayOf(-1, 1)) {
                    b.sphere(o.c + sd * (half + 0.025), 2.075, 0.215, 0.034, C("#C9A24E"), 0.04, 8, false)
                    b.box(o.c + sd * (half - 0.04), 2.075, 0.11, 0.016, 0.016, 0.21, C("#8A6A2E"), false)
                    b.box(o.c + sd * (ww / 2 + 0.10 + 0.03), 2.075, 0.11, 0.016, 0.016, 0.21, C("#8A6A2E"), false)
                    // gancho de amarração
                    b.sphere(o.c + sd * (ww / 2 + 0.10 + 0.0), 1.22, 0.17, 0.02, C("#C9A24E"), 0.02, 6, false)
                }
            }
        }

        // rodapé, moldura de teto e platibanda externa
        b.m(Mt.PLAIN)
        b.rbox(len / 2, HH - 0.04, 0.028, len, 0.08, 0.056, 0.01, wh, true, 1)
        b.m(Mt.STONE, 0.7f)
        b.rbox((xs + xe) / 2, 0.11, -tt - 0.012, xe - xs + 0.02, 0.22, 0.035, 0.012, C("#D8D0C2"), true, 1)

        if (art) {
            val cx = len / 2
            b.m(Mt.WOOD)
            b.rbox(cx, 1.55, 0.04, 1.3, 0.9, 0.05, 0.012, C("#4A3426"), true, 1)
            b.m(Mt.PLAIN)
            b.box(cx, 1.55, 0.068, 1.18, 0.78, 0.01, C("#F3ECE0"), false)
            b.box(cx - 0.35, 1.45, 0.075, 0.22, 0.5, 0.005, C("#C8553D"), false)
            b.box(cx - 0.05, 1.6, 0.075, 0.28, 0.45, 0.005, C("#E3A72F"), false)
            b.box(cx + 0.3, 1.5, 0.075, 0.2, 0.6, 0.005, C("#2F7F86"), false)
        }
        val wm = b.toMesh(true)
        return Mesh(wm.parts + fl.build())
    }

    /** Folha da porta (origem na dobradiça), animada pelo Renderer3D. */
    fun doorLeaf(): Mesh {
        val fb = Flora.Batch()
        fb.place("door_leaf_110", 0.0, 0.0, 0.0)
        return Mesh(fb.build())
    }

    // telhado de quatro águas (Etapa 70)
    private fun roofTri(b: MB, ax: Double, ay: Double, az: Double, bx: Double, by: Double, bz: Double, cx: Double, cy: Double, cz: Double, col: Int) {
        var ux = bx - ax; var uy = by - ay; var uz = bz - az
        var vx = cx - ax; var vy = cy - ay; var vz = cz - az
        var nx = uy * vz - uz * vy; var ny = uz * vx - ux * vz; var nz = ux * vy - uy * vx
        val l = Math.sqrt(nx * nx + ny * ny + nz * nz)
        nx /= l; ny /= l; nz /= l
        if (ny < 0) { nx = -nx; ny = -ny; nz = -nz }
        fun p(x: Double, y: Double, z: Double) = b.v(x.toFloat(), y.toFloat(), z.toFloat(), nx.toFloat(), ny.toFloat(), nz.toFloat(), col, x.toFloat(), (z + y * 1.6).toFloat())
        p(ax, ay, az); p(bx, by, bz); p(cx, cy, cz)
    }

    private fun roofQuad(b: MB, p: Array<DoubleArray>, col: Int) {
        roofTri(b, p[0][0], p[0][1], p[0][2], p[1][0], p[1][1], p[1][2], p[2][0], p[2][1], p[2][2], col)
        roofTri(b, p[0][0], p[0][1], p[0][2], p[2][0], p[2][1], p[2][2], p[3][0], p[3][1], p[3][2], col)
    }

    private fun roof(b: MB, W: Double, H: Double) {
        val o = 0.6
        val ye = HH + 0.2
        val hw = (Math.min(W, H) + 2 * o) / 2
        val rise = hw * 0.52
        val yr = ye + rise
        val x0 = -o; val x1 = W + o; val z0 = -o; val z1 = H + o
        val white = C("#FFFFFF")
        b.m(Mt.ROOF, 0.5f)
        val e0 = doubleArrayOf(x0, ye, z0); val e1 = doubleArrayOf(x1, ye, z0); val e2 = doubleArrayOf(x1, ye, z1); val e3 = doubleArrayOf(x0, ye, z1)
        val r0: DoubleArray; val r1: DoubleArray
        if (W >= H) {
            r0 = doubleArrayOf(x0 + hw, yr, H / 2); r1 = doubleArrayOf(x1 - hw, yr, H / 2)
            roofQuad(b, arrayOf(e0, e1, r1, r0), white)
            roofQuad(b, arrayOf(e2, e3, r0, r1), white)
            roofTri(b, e0[0], e0[1], e0[2], e3[0], e3[1], e3[2], r0[0], r0[1], r0[2], white)
            roofTri(b, e1[0], e1[1], e1[2], e2[0], e2[1], e2[2], r1[0], r1[1], r1[2], white)
        } else {
            r0 = doubleArrayOf(W / 2, yr, z0 + hw); r1 = doubleArrayOf(W / 2, yr, z1 - hw)
            roofQuad(b, arrayOf(e0, e3, r1, r0), white)
            roofQuad(b, arrayOf(e1, e2, r1, r0), white)
            roofTri(b, e0[0], e0[1], e0[2], e1[0], e1[1], e1[2], r0[0], r0[1], r0[2], white)
            roofTri(b, e3[0], e3[1], e3[2], e2[0], e2[1], e2[2], r1[0], r1[1], r1[2], white)
        }
        // beirais: fáscia clara em volta e forro do beiral por baixo
        b.m(Mt.PLASTER, 0.5f)
        val fc = C("#F6F1E7")
        b.rbox((x0 + x1) / 2, ye - 0.09, z0, x1 - x0 + 0.06, 0.2, 0.07, 0.02, fc, true, 1)
        b.rbox((x0 + x1) / 2, ye - 0.09, z1, x1 - x0 + 0.06, 0.2, 0.07, 0.02, fc, true, 1)
        b.rbox(x0, ye - 0.09, (z0 + z1) / 2, 0.07, 0.2, z1 - z0, 0.02, fc, true, 1)
        b.rbox(x1, ye - 0.09, (z0 + z1) / 2, 0.07, 0.2, z1 - z0, 0.02, fc, true, 1)
        b.plane(x0, z0, x1, z1, HH + 0.02, C("#EFE8DB"), false)
        // cumeeira e cantos
        b.m(Mt.ROOF, 0.5f)
        val rc = C("#D9DCE6")
        fun cap(ax: DoubleArray, bx: DoubleArray) {
            val n = 6
            for (i in 0 until n) {
                val t0 = i.toDouble() / n; val t1 = (i + 1.0) / n
                val sx = ax[0] + (bx[0] - ax[0]) * t0; val sy = ax[1] + (bx[1] - ax[1]) * t0 + 0.03; val sz = ax[2] + (bx[2] - ax[2]) * t0
                val ex = ax[0] + (bx[0] - ax[0]) * t1; val ey = ax[1] + (bx[1] - ax[1]) * t1 + 0.03; val ez = ax[2] + (bx[2] - ax[2]) * t1
                b.rbox((sx + ex) / 2, (sy + ey) / 2, (sz + ez) / 2, Math.abs(ex - sx) + 0.09, 0.09, Math.abs(ez - sz) + 0.09, 0.03, rc, true, 1)
            }
        }
        if (W >= H) { if (r1[0] > r0[0] + 0.05) cap(r0, r1) } else { if (r1[2] > r0[2] + 0.05) cap(r0, r1) }
    }

    fun ceiling(gw: Int, gh: Int): Mesh {
        val b = MB()
        val W = gw.toDouble(); val H = gh.toDouble()
        b.m(Mt.PLASTER, 0.5f)
        b.plane(0, 0, gw, gh, HH - 0.01, C("#F6F2EA"), false)
        // lustre
        val cx = W / 2; val cz = H / 2
        b.m(Mt.METAL)
        b.cyl(cx, HH - 0.03, cz, 0.12, 0.12, 0.03, C("#2B3036"), true, 16)
        b.cyl(cx, HH - 0.3, cz, 0.012, 0.012, 0.28, C("#2B3036"), true, 8)
        b.m(Mt.PLAIN)
        b.lathe(cx, HH - 0.55, cz, floatArrayOf(0.34f, 0f, 0.1f, 0.27f), C("#F4F1EA"), true, 28)
        b.sphere(cx, HH - 0.5, cz, 0.09, C("#FFF3C8"), 0.09, 8, false)
        roof(b, W, H)
        return b.toMesh(true)
    }

    // ------------------------------------------------------------ quintal

    private fun tree(b: MB, x: Double, z: Double, s: Double, l1: Int, l2: Int) {
        b.m(Mt.WOOD, 1f)
        b.cyl(x, -0.03, z, 0.17 * s, 0.09 * s, 1.9 * s, C("#6B4A32"), true, 10)
        b.m(Mt.GRASS, 0.9f)
        val cy = 2.3 * s
        b.sphere(x, cy + 0.5 * s, z, 0.95 * s, l1, 0.85 * s, 12)
        b.sphere(x + 0.55 * s, cy, z + 0.2 * s, 0.7 * s, l2, 0.62 * s, 10)
        b.sphere(x - 0.5 * s, cy - 0.05 * s, z - 0.25 * s, 0.72 * s, l1, 0.63 * s, 10)
        b.sphere(x + 0.1 * s, cy + 1.15 * s, z - 0.1 * s, 0.62 * s, l2, 0.55 * s, 10)
        b.sphere(x - 0.3 * s, cy + 0.2 * s, z + 0.55 * s, 0.6 * s, l2, 0.52 * s, 10)
        b.sphere(x + 0.35 * s, cy + 0.3 * s, z - 0.55 * s, 0.58 * s, l1, 0.5 * s, 10)
    }

    private fun bush(b: MB, x: Double, z: Double, s: Double, c: Int, flower: Int?) {
        b.m(Mt.GRASS, 1.2f)
        b.sphere(x, 0.3 * s, z, 0.5 * s, c, 0.38 * s, 10)
        b.sphere(x + 0.35 * s, 0.25 * s, z + 0.1 * s, 0.38 * s, shade(c, 12), 0.3 * s, 9)
        b.sphere(x - 0.3 * s, 0.25 * s, z - 0.12 * s, 0.36 * s, shade(c, -10), 0.28 * s, 9)
        if (flower != null) {
            b.m(Mt.PLAIN)
            for (i in 0 until 9) {
                val a = i * 2.4
                b.sphere(x + cos(a) * 0.45 * s, 0.3 * s + sin(i * 1.3) * 0.18 * s + 0.15 * s, z + sin(a) * 0.42 * s, 0.055, flower, 0.055, 5)
            }
        }
    }

    private fun picketX(b: MB, z: Double, xa: Double, xb: Double) {
        var x = xa
        while (x <= xb) {
            b.box(x, 0.45, z, 0.09, 0.9, 0.03, C("#F4F1EA"))
            b.cyl(x, 0.9, z, 0.052, 0.0, 0.08, C("#F4F1EA"), true, 4)
            x += 0.2
        }
        b.box((xa + xb) / 2, 0.28, z, xb - xa, 0.07, 0.05, C("#E9E4D8"))
        b.box((xa + xb) / 2, 0.68, z, xb - xa, 0.07, 0.05, C("#E9E4D8"))
        var p = xa
        while (p <= xb + 0.01) {
            b.box(p, 0.5, z, 0.12, 1.0, 0.12, C("#EEE9DD"))
            p += 2.0
        }
    }

    private fun picketZ(b: MB, x: Double, za: Double, zb: Double) {
        var z = za
        while (z <= zb) {
            b.box(x, 0.45, z, 0.03, 0.9, 0.09, C("#F4F1EA"))
            b.cyl(x, 0.9, z, 0.052, 0.0, 0.08, C("#F4F1EA"), true, 4)
            z += 0.2
        }
        b.box(x, 0.28, (za + zb) / 2, 0.05, 0.07, zb - za, C("#E9E4D8"))
        b.box(x, 0.68, (za + zb) / 2, 0.05, 0.07, zb - za, C("#E9E4D8"))
        var p = za
        while (p <= zb + 0.01) {
            b.box(x, 0.5, p, 0.12, 1.0, 0.12, C("#EEE9DD"))
            p += 2.0
        }
    }

    fun yard(gw: Int, gh: Int, vitrine: Boolean = false): Mesh {
        val b = MB()
        val fl = Flora.Batch()
        val W = gw.toDouble(); val H = gh.toDouble()
        val x0 = -7.0; val x1 = W + 7.0; val z0 = -7.0; val z1 = H + 9.0
        val white = C("#FFFFFF")

        // chão: malha de células de 6 m com variação suave de cor por vértice (sem o xadrez repetido)
        b.m(Mt.GRASS, 0.3f)
        run {
            fun gn(i: Int, j: Int): Float {
                var h = i * 374761393 + j * 668265263
                h = (h xor (h ushr 13)) * 1274126177
                return ((h xor (h ushr 16)) and 0xFFFF) / 65535f
            }
            fun gcol(i: Int, j: Int): Int {
                val n = 0.55f * gn(i, j) + 0.45f * gn(i / 2 + 500, j / 2 + 500)
                return mix(C("#D6EEC4"), C("#FFFFFF"), n)
            }
            val cs = 6.0
            val ia = Math.floor((-110.0) / cs).toInt(); val ib = Math.ceil((W + 110.0) / cs).toInt()
            val ja = Math.floor((-110.0) / cs).toInt(); val jb = Math.ceil((H + 110.0) / cs).toInt()
            for (i in ia until ib) for (j in ja until jb) {
                val xa = (i * cs).toFloat(); val xb = ((i + 1) * cs).toFloat(); val za = (j * cs).toFloat(); val zb = ((j + 1) * cs).toFloat()
                val yy = -0.03f
                fun vv(x: Float, z: Float, ci: Int, cj: Int) = b.v(x, yy, z, 0f, 1f, 0f, gcol(ci, cj), x, z)
                vv(xa, za, i, j); vv(xa, zb, i, j + 1); vv(xb, zb, i + 1, j + 1)
                vv(xa, za, i, j); vv(xb, zb, i + 1, j + 1); vv(xb, za, i + 1, j)
            }
        }

        // colinhas ao longe: cúpulas sem luz com degradê (verde no topo, névoa na base)
        for (k in 0 until 22) {
            val a = k * 2.0 * PI / 22 + 0.1 * (k % 3)
            val far = k % 2 == 0
            val dist = if (far) 118.0 else 100.0
            val rx = 20.0 + (k * 7 % 5) * 5
            val hh = (if (far) 9.0 else 6.5) + (k * 5 % 4)
            val topC = if (far) C("#9CC4A0") else C("#86B77A")
            val botC = C("#CFE2D2")
            val cx = W / 2 + dist * cos(a); val cz = H / 2 + dist * sin(a)
            val nR = 10; val nL = 4
            val ca = cos(a + PI / 2).toFloat(); val sa = sin(a + PI / 2).toFloat()
            fun pt(t: Int, s: Int): FloatArray {
                val ph = PI * 2 * s / nR
                val rr = rx * cos(PI / 2 * t / nL)
                val yy = hh * sin(PI / 2 * t / nL) - 1.0
                val lx = rr * cos(ph); val lz = rr * sin(ph) * 0.55
                return floatArrayOf((cx + lx * ca - lz * sa).toFloat(), yy.toFloat(), (cz + lx * sa + lz * ca).toFloat(), t.toFloat() / nL)
            }
            for (t in 0 until nL) for (s in 0 until nR) {
                val p00 = pt(t, s); val p01 = pt(t, s + 1); val p10 = pt(t + 1, s); val p11 = pt(t + 1, s + 1)
                fun e(p: FloatArray) = b.v(p[0], p[1], p[2], 0f, 0f, 0f, mix(botC, topC, Math.min(1f, p[3] * 1.3f)), 0f, 0f)
                e(p00); e(p10); e(p11); e(p00); e(p11); e(p01)
            }
        }

        // caminho de pedras + varanda
        b.m(Mt.PAVER, 0.9f)
        b.rbox(W / 2, -0.005, (H + 1.7 + z1) / 2, 1.5, 0.05, z1 - H - 1.7, 0.015, white, true, 1)
        b.m(Mt.PAVER, 0.7f)
        b.rbox(W / 2, 0.045, H + 0.95, 2.8, 0.09, 1.6, 0.025, C("#EDE5D8"), true, 2)
        b.rbox(W / 2, 0.0, H + 1.95, 2.0, 0.07, 0.45, 0.02, C("#EDE5D8"), true, 2)

        // Etapa 87: vasos da varanda e postes de luz (anteriores ao Plano Mestre) foram retirados

        // canteiros com flores na frente da casa (flores e folhas de verdade, Etapa 67)
        val fnames = listOf("fl_tulip", "fl_daisy", "fl_lav", "fl_yellow", "fl_poppy")
        for (side in 0..1) {
            val xa = if (side == 0) 0.45 else W / 2 + 1.75
            val xb = if (side == 0) W / 2 - 1.75 else W - 0.45
            b.m(Mt.PLAIN)
            b.rbox((xa + xb) / 2, 0.08, H + 0.65, xb - xa, 0.16, 0.7, 0.05, C("#4B3427"), true, 2)
            var x = xa + 0.25
            var i = 0
            while (x < xb - 0.1) {
                val zz = H + 0.5 + (i % 3) * 0.14
                fl.place(fnames[(i + side * 2) % fnames.size], x, 0.14, zz, 0.9 + 0.2 * ((i * 7) % 5) / 4.0, i * 1.9)
                if (i % 3 == 1) fl.place("bush_a", x + 0.2, 0.13, H + 0.82, 0.32, i * 2.3, 1f, 1f, 1f)
                x += 0.42
                i++
            }
        }

        // cerca-viva atrás da casa
        run {
            val n = Math.ceil((W + 1.4) / 2.0).toInt()
            val step = (W + 1.4) / n
            for (i in 0 until n) fl.place("hedge", -0.7 + step * (i + 0.5), 0.0, -0.85, step / 2.0, 0.0, 1f, 1f, 1f)
        }

        // árvores e arbustos
        if (vitrine) {
            // Etapa 87: sala de testes — todas as plantas e árvores do jogo do lado de fora da casa, em fila, com o nome no catálogo
            val tall = Type.values().filter { it.cat == 4 && (it.fl?.let { f -> f.startsWith("oak") || f.startsWith("cherry") || f.startsWith("pine") } ?: false) }
            val low = Type.values().filter { it.cat == 4 && it !in tall }
            // árvores à esquerda da casa (x = -3,8), espaçadas pelo tamanho
            var zz = 2.5
            for (t in tall) { fl.place(t.fl!!, -3.8, 0.0, zz, 1.0, 0.6); zz += t.h.toDouble() * 0.9 }
            // arbustos, cerca-viva e flores à direita da casa (x = W + 2,5 / W + 4,5), em duas colunas
            var zl = 1.5; var col = 0
            for (t in low) {
                val xx = W + (if (col == 0) 2.4 else 4.6)
                fl.place(t.fl!!, xx, 0.0, zl, 1.0, 0.3)
                col = 1 - col
                if (col == 0) zl += Math.max(1.2, t.h * 0.9)
            }
        } else {
            fl.place("oak_a", -3.6, 0.0, -3.2, 1.0, 0.4)
            fl.place("oak_b", W + 3.8, 0.0, H * 0.25, 1.1, 2.0, 0.97f, 1.0f, 0.97f)
            fl.place("cherry_a", -3.4, 0.0, H + 3.6, 0.95, 1.1)
            fl.place("pine_a", W + 3.2, 0.0, H + 4.8, 1.05, 0.7)
            fl.place("oak_a", W / 2 + 4.5, 0.0, -4.8, 1.2, 3.6, 0.95f, 1.0f, 0.95f)
            fl.place("pine_a", -5.2, 0.0, H * 0.5, 1.2, 2.6, 0.95f, 1.0f, 0.97f)
            fl.place("bush_pink", -1.1, 0.0, H * 0.4, 1.0, 0.5)
            fl.place("bush_a", W + 1.2, 0.0, H * 0.7, 1.15, 1.7)
            fl.place("bush_white", -1.0, 0.0, H + 1.5, 0.95, 2.9)
            fl.place("bush_pink", W + 1.1, 0.0, H + 1.2, 1.0, 4.1)
            fl.place("bush_b", W / 2 - 3.2, 0.0, H + 5.0, 1.25, 0.9)
            fl.place("bush_white", W / 2 + 3.4, 0.0, H + 6.2, 1.1, 3.3)
        }

        // tufos de grama espalhados pelo quintal (fora da casa e do caminho)
        run {
            val rnd = java.util.Random(7)
            var k = 0
            var tries = 0
            while (k < 0 && tries < 4000) {
                tries++
                val gx = x0 + 1.0 + rnd.nextDouble() * (x1 - x0 - 2.0)
                val gz = z0 + 1.0 + rnd.nextDouble() * (z1 - z0 - 2.0)
                if (gx > -0.9 && gx < W + 0.9 && gz > -1.4 && gz < H + 0.9) continue
                if (Math.abs(gx - W / 2) < 1.5 && gz > H) continue
                fl.place(if (k % 3 == 0) "grass_b" else "grass_a", gx, 0.0, gz, 0.38 + rnd.nextDouble() * 0.3, rnd.nextDouble() * 6.28)
                k++
            }
        }

        // cerca com portão (painéis e postes modelados)
        run {
            fun line(len: Double, cb: (Double, Double, Double) -> Unit) {
                val n = Math.max(1, (len / 2.0).toInt())
                val step = len / n
                for (i in 0 until n) cb(i * step, step, step / 2.0)
            }
            line(x1 - x0) { o, st, sc ->
                val cx = x0 + o + st / 2
                fl.place("fence_post", x0 + o, 0.0, z0, 1.0, 0.0)
                fl.place("fence_panel", x0 + o + st, 0.0, z0, sc, Math.PI)
                fl.place("fence_post", x0 + o, 0.0, z1, 1.0, 0.0)
                if (Math.abs(cx - W / 2) > 1.4) fl.place("fence_panel", x0 + o, 0.0, z1, sc, 0.0)
            }
            fl.place("fence_post", x1, 0.0, z0, 1.0, 0.0); fl.place("fence_post", x1, 0.0, z1, 1.0, 0.0)
            line(z1 - z0) { o, st, sc ->
                fl.place("fence_post", x0, 0.0, z0 + o, 1.0, 0.0)
                fl.place("fence_panel", x0, 0.0, z0 + o, sc, -Math.PI / 2)
                fl.place("fence_post", x1, 0.0, z0 + o, 1.0, 0.0)
                fl.place("fence_panel", x1, 0.0, z0 + o + st, sc, Math.PI / 2)
            }
            fl.place("fence_post", x0, 0.0, z1, 1.0, 0.0)
            for (sx in intArrayOf(-1, 1)) {
                val px = W / 2 + sx * 1.0
                fl.place("fence_post", px, 0.0, z1, 1.25, 0.0)
            }
        }
        val yardMesh = b.toMesh(true)
        return Mesh(yardMesh.parts + fl.build())
    }

    // ------------------------------------------------------------ céu

    fun sky(): Mesh {
        val b = MB()
        val top = C("#3F7FDB"); val mid = C("#9CC8F2"); val hor = C("#EAF3FA"); val gnd = C("#A9C79A")
        val R = 120f
        val lat = 14
        val lon = 28
        fun col(y: Float): Int = if (y >= 0f) {
            if (y < 0.25f) mix(hor, mid, y / 0.25f) else mix(mid, top, ((y - 0.25f) / 0.75f).coerceIn(0f, 1f))
        } else mix(hor, gnd, (-y * 4f).coerceIn(0f, 1f))
        val pi = PI.toFloat()
        for (i in 0 until lat) {
            val t0 = pi * i / lat
            val t1 = pi * (i + 1) / lat
            for (j in 0 until lon) {
                val p0 = 2f * pi * j / lon
                val p1 = 2f * pi * (j + 1) / lon
                fun pt(t: Float, p: Float) = b.raw(R * sin(t) * cos(p), R * cos(t), R * sin(t) * sin(p), col(cos(t)))
                pt(t0, p0); pt(t1, p0); pt(t1, p1)
                pt(t0, p0); pt(t1, p1); pt(t0, p1)
            }
        }
        val fl = Flora.Batch()
        for (k in 0 until 16) {
            val a = k * 0.62 + 0.3 * (k % 3)
            val rr = 85.0 + (k % 3) * 8
            val cx = cos(a) * rr; val cz = sin(a) * rr; val cy = 32.0 + (k % 4) * 8.0
            fl.place("cloud_a", cx, cy, cz, 46.0 + (k % 5) * 7.0, Math.atan2(-cx, -cz))
        }
        // sol
        val sl = sqrt(0.45 * 0.45 + 1.0 + 0.65 * 0.65)
        val sx = 0.45 / sl * 100; val sy = 1.0 / sl * 100; val sz = 0.65 / sl * 100
        b.al = 0.10f
        b.sphere(sx, sy, sz, 24.0, C("#FFF0B8"), 24.0, 12, false)
        b.al = 0.2f
        b.sphere(sx, sy, sz, 15.0, C("#FFEAA0"), 15.0, 12, false)
        b.al = 0.35f
        b.sphere(sx, sy, sz, 9.0, C("#FFE9A0"), 9.0, 10, false)
        b.al = 1f
        b.sphere(sx, sy, sz, 5.0, C("#FFFBE8"), 5.0, 12, false)
        val sm = b.toMesh(true)
        return Mesh(sm.parts + fl.build())
    }
}
