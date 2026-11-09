package com.vinicius.meular

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * Etapa 144: planta da casa do jogador (12 x 9 m, frente em z = 9, porta em x = 6).
 *  fundo (z 0..4): suíte (x 0..4.6) com banheiro próprio (x 2.9..4.6, z 0..2), banheiro social (x 4.6..6.8), quarto 2 (x 6.8..12)
 *  frente (z 4..9): sala (x 0..7) e cozinha/jantar (x 7..12) com passagem larga entre as duas
 * Garagem coberta encostada na lateral direita (x 12..16.4) e quintal cercado (cerca do quintal já existente).
 */
object HouseLayout {
    const val W = 12
    const val H = 9
    const val T = 0.12f
    const val DOOR = 0.9f

    /** Parede: eixo 0 = ao longo de x (em z = c, de a a b); eixo 1 = ao longo de z (em x = c). Portas = centros das aberturas. */
    class Wall(val axis: Int, val c: Float, val a: Float, val b: Float, val doors: FloatArray, val doorW: Float = DOOR)

    val walls = listOf(
        Wall(0, 4.0f, 0f, 12f, floatArrayOf(2.2f, 5.7f, 7.55f)),
        Wall(1, 4.6f, 0f, 4.0f, floatArrayOf()),
        Wall(1, 6.8f, 0f, 4.0f, floatArrayOf()),
        Wall(0, 2.0f, 2.9f, 4.6f, floatArrayOf()),
        Wall(1, 2.9f, 0f, 2.0f, floatArrayOf(1.45f), 0.8f),
        Wall(1, 7.0f, 4.0f, 9f, floatArrayOf(6.6f), 1.8f))

    /** Banheiros e cozinha têm piso frio. [x0, z0, x1, z1] */
    val tiles = listOf(floatArrayOf(4.66f, 0f, 6.74f, 3.94f), floatArrayOf(2.96f, 0f, 4.54f, 1.94f), floatArrayOf(7.06f, 4.06f, 12f, 9f))

    /** Peças fixas do banheiro e da garagem que bloqueiam o caminho: [x0, z0, x1, z1]. */
    val fixtures = listOf(
        floatArrayOf(4.7f, 0.05f, 5.6f, 0.95f),     // box do banheiro social
        floatArrayOf(6.2f, 0.1f, 6.75f, 0.75f),     // vaso
        floatArrayOf(4.7f, 2.4f, 5.2f, 3.4f),       // pia
        floatArrayOf(3.0f, 0.05f, 3.85f, 0.9f),     // box da suíte
        floatArrayOf(4.05f, 1.35f, 4.55f, 1.95f),   // vaso da suíte
        floatArrayOf(4.1f, 0.1f, 4.55f, 0.95f))     // pia da suíte

    /** Retângulos sólidos das paredes internas (já sem as portas). */
    val rects: List<FloatArray> by lazy {
        val out = ArrayList<FloatArray>()
        for (w in walls) {
            var s = w.a
            val cuts = w.doors.sorted()
            for (d in cuts) { val e = d - w.doorW / 2; if (e > s + 0.01f) out.add(seg(w, s, e)); s = d + w.doorW / 2 }
            if (w.b > s + 0.01f) out.add(seg(w, s, w.b))
        }
        out
    }
    private fun seg(w: Wall, a: Float, b: Float) = if (w.axis == 0) floatArrayOf(a, w.c - T / 2, b, w.c + T / 2) else floatArrayOf(w.c - T / 2, a, w.c + T / 2, b)

    fun active(gw: Int, gh: Int) = gw == W && gh == H

    /** O ponto (com folga m) bate em parede interna ou peça fixa? */
    fun blocks(gw: Int, gh: Int, x: Float, z: Float, m: Float = 0.22f): Boolean {
        if (!active(gw, gh)) return false
        for (r in rects) if (x > r[0] - m && x < r[2] + m && z > r[1] - m && z < r[3] + m) return true
        for (r in fixtures) if (x > r[0] - m * 0.6f && x < r[2] + m * 0.6f && z > r[1] - m * 0.6f && z < r[3] + m * 0.6f) return true
        return false
    }

    /** O retângulo de um móvel encosta numa parede interna ou peça fixa? */
    fun overlaps(gw: Int, gh: Int, r: FloatArray): Boolean {
        if (!active(gw, gh)) return false
        for (q in rects + fixtures) if (r[0] < q[2] - 0.01f && r[2] > q[0] + 0.01f && r[1] < q[3] - 0.01f && r[3] > q[1] + 0.01f) return true
        return false
    }

    /** A linha entre dois pontos atravessa alguma parede interna? (para a câmera não ver através) */
    fun crosses(gw: Int, gh: Int, ax: Float, az: Float, bx: Float, bz: Float): Boolean {
        if (!active(gw, gh)) return false
        val n = max(2, (kotlin.math.hypot(bx - ax, bz - az) / 0.08f).toInt())
        for (k in 1..n) { val t = k.toFloat() / n; val x = ax + (bx - ax) * t; val z = az + (bz - az) * t
            for (r in rects) if (x > r[0] - 0.12f && x < r[2] + 0.12f && z > r[1] - 0.12f && z < r[3] + 0.12f) return true }
        return false
    }

    // ---------------------------------------------------------------- garagem (fora da casa, lateral direita)
    const val GX0 = 12.15f; const val GX1 = 16.4f; const val GZ0 = 2.2f; const val GZ1 = 9.0f
    /** Paredes da garagem (fundo e lateral externa) e bancada: bloqueiam quem anda no quintal. */
    val garageSolids = listOf(
        floatArrayOf(GX0, GZ0 - 0.1f, GX1, GZ0 + 0.1f),
        floatArrayOf(GX1 - 0.1f, GZ0, GX1 + 0.1f, GZ1),
        floatArrayOf(GX0 + 0.3f, GZ0 + 0.1f, GX0 + 2.2f, GZ0 + 0.75f),
        floatArrayOf(GX1 - 0.75f, GZ0 + 1.0f, GX1 - 0.1f, GZ0 + 3.2f))
    fun yardBlocks(gw: Int, gh: Int, x: Float, z: Float): Boolean {
        if (!active(gw, gh)) return false
        for (r in garageSolids) if (x > r[0] - 0.25f && x < r[2] + 0.25f && z > r[1] - 0.25f && z < r[3] + 0.25f) return true
        return false
    }

    // ---------------------------------------------------------------- geometria
    /** Paredes internas com batentes e rodapé, pisos frios, louças do banheiro, luminárias por cômodo. */
    fun build(b: MB, wallCol: Int) {
        val hh = 2.5
        val trim = C("#F4F1EA")
        for (w in walls) {
            var s = w.a
            val cuts = w.doors.sorted()
            fun piece(a: Float, e: Float) {
                if (e - a < 0.01f) return
                val cx = (a + e) / 2; val len = e - a
                b.m(Mt.PLASTER, 0.5f)
                if (w.axis == 0) b.box(cx, hh / 2, w.c, len, hh, T, wallCol) else b.box(w.c, hh / 2, cx, T, hh, len, wallCol)
                b.m(Mt.WOOD, 0.5f)
                if (w.axis == 0) b.box(cx, 0.05, w.c, len, 0.1, T + 0.03f, trim) else b.box(w.c, 0.05, cx, T + 0.03f, 0.1, len, trim)
            }
            for (d in cuts) {
                piece(s, d - w.doorW / 2)
                val top = if (w.doorW > 1.2f) 2.3f else 2.1f
                b.m(Mt.PLASTER, 0.5f)
                if (w.axis == 0) b.box(d, (top + hh) / 2, w.c, w.doorW, hh - top, T, wallCol) else b.box(w.c, (top + hh) / 2, d, T, hh - top, w.doorW, wallCol)
                // batentes de madeira
                b.m(Mt.WOOD, 0.5f)
                val fc = C("#8D6E63")
                for (sg in floatArrayOf(-1f, 1f)) {
                    val p = d + sg * (w.doorW / 2 - 0.03f)
                    if (w.axis == 0) b.box(p, top / 2, w.c, 0.06, top, T + 0.04f, fc) else b.box(w.c, top / 2, p, T + 0.04f, top, 0.06, fc)
                }
                if (w.axis == 0) b.box(d, top + 0.03, w.c, w.doorW, 0.06, T + 0.04f, fc) else b.box(w.c, top + 0.03, d, T + 0.04f, 0.06, w.doorW, fc)
                s = d + w.doorW / 2
            }
            piece(s, w.b)
        }
        // pisos frios (cerâmica) nos banheiros e na cozinha
        b.m(Mt.TILE, 0.5f)
        for ((i, r) in tiles.withIndex()) b.plane(r[0], r[1], r[2], r[3], 0.004, C(if (i == 2) "#E8E2D6" else "#DCE6EA"))
        // ---- banheiro social: box com vidro, vaso, pia com espelho, toalheiro
        bath(b, 4.7f, 0.05f, 5.6f, 0.95f, 6.47f, 0.42f, 4.95f, 2.9f, false)
        // ---- banheiro da suíte (espelhado)
        bath(b, 3.0f, 0.05f, 3.85f, 0.9f, 4.3f, 1.65f, 4.32f, 0.52f, true)
        // ---- luminárias: uma plafon por cômodo
        b.m(Mt.PLAIN)
        for (p in arrayOf(floatArrayOf(1.5f, 2.6f), floatArrayOf(5.7f, 2.0f), floatArrayOf(9.4f, 2.0f), floatArrayOf(3.7f, 1.0f), floatArrayOf(10.6f, 6.6f))) {
            b.cyl(p[0], hh - 0.06, p[1], 0.22, 0.22, 0.05, C("#ECEFF1"), true, 14); b.cyl(p[0], hh - 0.065, p[1], 0.19, 0.19, 0.006, C("#FFF6D6"), false, 14)
        }
    }

    private fun bath(b: MB, sx0: Float, sz0: Float, sx1: Float, sz1: Float, tx: Float, tz: Float, px: Float, pz: Float, suite: Boolean) {
        val white = C("#FAFAFA"); val chrome = C("#CFD8DC")
        // box: base, vidro, chuveiro
        b.m(Mt.TILE, 0.4f); b.box((sx0 + sx1) / 2, 0.03, (sz0 + sz1) / 2, sx1 - sx0, 0.06, sz1 - sz0, C("#B0BEC5"))
        b.m(Mt.GLASS); b.box((sx0 + sx1) / 2, 1.0, sz1, sx1 - sx0, 1.9, 0.02, C("#D6EEF5")); b.box(sx1, 1.0, (sz0 + sz1) / 2, 0.02, 1.9, sz1 - sz0, C("#D6EEF5"))
        b.m(Mt.METAL); b.box(sx1, 1.0, sz1, 0.03, 1.95, 0.03, chrome); b.cyl((sx0 + sx1) / 2, 1.9, sz0 + 0.12, 0.1, 0.1, 0.02, chrome, true, 10); b.box((sx0 + sx1) / 2, 1.6, sz0 + 0.04, 0.03, 0.6, 0.03, chrome)
        b.m(Mt.TILE, 0.35f); b.box((sx0 + sx1) / 2, 1.1, sz0 + 0.02, sx1 - sx0, 2.0, 0.02, C("#E0F2F1"))
        // vaso sanitário
        b.m(Mt.PLAIN); b.box(tx, 0.2, tz, 0.38, 0.4, 0.5, white); b.box(tx, 0.42, tz, 0.4, 0.04, 0.48, white); b.box(tx, 0.62, tz - (if (suite) -0.22f else 0.22f), 0.42, 0.4, 0.16, white)
        // pia com gabinete e espelho
        b.m(Mt.WOOD, 0.5f); b.box(px, 0.42, pz, 0.46, 0.8, 0.9, C("#8D6E63"))
        b.m(Mt.STONE, 0.6f); b.box(px, 0.85, pz, 0.5, 0.05, 0.95, C("#ECEFF1"))
        b.m(Mt.METAL); b.cyl(px - (if (suite) -0.12f else 0.12f), 0.88, pz, 0.025, 0.025, 0.2, chrome, true, 8)
        b.m(Mt.GLASS); b.box(px - (if (suite) -0.22f else 0.22f), 1.55, pz, 0.02, 0.8, 0.7, C("#E3F2FD"))
        // toalha
        b.m(Mt.FABRIC); b.box(px, 1.25, pz + (if (suite) -0.62f else 0.62f), 0.04, 0.5, 0.35, C(if (suite) "#F8BBD0" else "#80CBC4"))
    }

    /** Garagem coberta: piso de concreto, colunas, laje, paredes do fundo e lateral, bancada, prateleira e bicicleta. */
    fun garage(b: MB) {
        val hh = 2.6
        b.m(Mt.STONE, 0.6f); b.box((GX0 + GX1) / 2.0, 0.02, (GZ0 + GZ1) / 2.0, (GX1 - GX0).toDouble(), 0.05, (GZ1 - GZ0).toDouble(), C("#B5B2AB"))
        // rampa/entrada até a cerca
        b.box((GX0 + GX1) / 2.0, 0.015, GZ1 + 4.3, (GX1 - GX0 - 0.6).toDouble(), 0.03, 8.6, C("#C7C2B8"))
        b.m(Mt.PLASTER, 0.5f)
        b.box((GX0 + GX1) / 2.0, hh / 2, GZ0.toDouble(), (GX1 - GX0).toDouble(), hh, 0.2, C("#ECE6DA"))
        b.box(GX1.toDouble(), hh / 2, (GZ0 + GZ1) / 2.0, 0.2, hh, (GZ1 - GZ0).toDouble(), C("#ECE6DA"))
        b.m(Mt.STONE, 0.6f); b.box(GX1.toDouble(), hh / 2, GZ1 - 0.1, 0.3, hh, 0.3, C("#D7CCC8"))
        b.m(Mt.ROOF, 0.5f); b.box((GX0 + GX1) / 2.0 + 0.1, hh + 0.08, (GZ0 + GZ1) / 2.0 + 0.2, (GX1 - GX0 + 0.5).toDouble(), 0.16, (GZ1 - GZ0 + 0.6).toDouble(), C("#6D6058"))
        b.m(Mt.PLAIN); b.box((GX0 + GX1) / 2.0, hh - 0.01, (GZ0 + GZ1) / 2.0, (GX1 - GX0).toDouble(), 0.02, (GZ1 - GZ0).toDouble(), C("#F5F1EA"))
        b.cyl((GX0 + GX1) / 2.0, hh - 0.06, (GZ0 + GZ1) / 2.0, 0.3, 0.3, 0.05, C("#FFF6D6"), false, 12)
        // bancada com ferramentas
        b.m(Mt.WOOD, 0.5f); b.box(GX0 + 1.25, 0.45, GZ0 + 0.43, 1.9, 0.9, 0.65, C("#8D6E63"))
        b.m(Mt.METAL); b.box(GX0 + 1.25, 1.35, GZ0 + 0.12, 1.9, 0.9, 0.03, C("#ECEFF1"))
        for (k in 0 until 7) b.box(GX0 + 0.45 + k * 0.27, 1.4 + (k % 2) * 0.2, GZ0 + 0.15, 0.04, 0.25, 0.02, C(arrayOf("#D32F2F", "#212121", "#1565C0", "#9E9E9E")[k % 4]))
        b.box(GX0 + 0.7, 0.94, GZ0 + 0.4, 0.35, 0.18, 0.2, C("#C62828"))
        // prateleira metálica com caixas
        b.m(Mt.METAL); for (k in 0..3) b.box(GX1 - 0.42, 0.1 + k * 0.55, GZ0 + 2.1, 0.6, 0.03, 2.1, C("#90A4AE"))
        for (e in floatArrayOf(GZ0 + 1.08f, GZ0 + 3.12f)) for (a in floatArrayOf(GX1 - 0.7f, GX1 - 0.14f)) b.box(a.toDouble(), 0.85, e.toDouble(), 0.04, 1.7, 0.04, C("#607D8B"))
        b.m(Mt.PLAIN); for (k in 0..2) for (j in 0..1) b.box(GX1 - 0.42, 0.28 + k * 0.55, GZ0 + 1.5 + j * 1.1, 0.5, 0.3, 0.5, C(arrayOf("#C49A6C", "#B8895A", "#D2AE82")[(k + j) % 3]))
        // bicicleta encostada no fundo
        b.m(Mt.METAL)
        b.cyl(GX0 + 3.0, 0.0, GZ0 + 0.3, 0.33, 0.33, 0.04, C("#212121"), true, 14); b.cyl(GX0 + 3.0, 0.0, GZ0 + 1.35, 0.33, 0.33, 0.04, C("#212121"), true, 14)
        b.box(GX0 + 3.0, 0.5, GZ0 + 0.82, 0.04, 0.05, 1.0, C("#1E88E5")); b.box(GX0 + 3.0, 0.75, GZ0 + 0.95, 0.04, 0.5, 0.05, C("#1E88E5")); b.box(GX0 + 3.0, 1.0, GZ0 + 0.35, 0.45, 0.03, 0.03, C("#212121"))
        // marcação da vaga
        b.m(Mt.PLAIN); b.box(GX0 + 0.35, 0.05, (GZ0 + GZ1) / 2.0 + 0.5, 0.08, 0.004, 5.0, C("#FDD835")); b.box(GX1 - 0.95, 0.05, (GZ0 + GZ1) / 2.0 + 1.0, 0.08, 0.004, 4.0, C("#FDD835"))
    }

}
