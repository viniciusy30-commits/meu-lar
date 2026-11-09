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
    // Etapa 147: casa maior — 18 x 12 m (antes 12 x 9), cômodos folgados e portas de 1 m
    const val W = 18
    const val H = 12
    const val T = 0.12f
    const val DOOR = 1.0f
    const val ZA = 5.2f            // parede entre os quartos (fundo) e a área social (frente)

    /** Parede: eixo 0 = ao longo de x (em z = c, de a a b); eixo 1 = ao longo de z (em x = c). Portas = centros das aberturas. */
    class Wall(val axis: Int, val c: Float, val a: Float, val b: Float, val doors: FloatArray, val doorW: Float = DOOR)

    /*
     * fundo (z 0..5.2): suíte (x 0..6.4) com banheiro próprio (x 4.4..6.4, z 0..2.8), banheiro social (x 6.4..9),
     *                   quarto 2 (x 9..14), lavanderia (x 14..18)
     * frente (z 5.2..12): sala de estar (x 0..10.5) e cozinha com copa (x 10.5..18), passagem larga de 2,4 m entre elas
     */
    val walls = listOf(
        Wall(0, ZA, 0f, 18f, floatArrayOf(3.0f, 7.7f, 9.85f, 17.25f)),
        Wall(1, 6.4f, 0f, ZA, floatArrayOf()),
        Wall(1, 9.0f, 0f, ZA, floatArrayOf()),
        Wall(1, 14.0f, 0f, ZA, floatArrayOf()),
        Wall(0, 2.8f, 4.4f, 6.4f, floatArrayOf()),
        Wall(1, 4.4f, 0f, 2.8f, floatArrayOf(2.15f), 0.85f),
        Wall(1, 10.5f, ZA, 12f, floatArrayOf(8.7f), 2.4f))

    /** Banheiros, lavanderia e cozinha têm piso frio. [x0, z0, x1, z1] */
    val tiles = listOf(floatArrayOf(6.46f, 0f, 8.94f, ZA - 0.06f), floatArrayOf(4.46f, 0f, 6.34f, 2.74f), floatArrayOf(14.06f, 0f, 18f, ZA - 0.06f), floatArrayOf(10.56f, ZA + 0.06f, 18f, 12f))

    /** Peças fixas (louças, lavanderia) que bloqueiam o caminho: [x0, z0, x1, z1]. */
    val fixtures = listOf(
        floatArrayOf(6.46f, 0.05f, 7.6f, 1.15f),     // box do banheiro social
        floatArrayOf(8.32f, 0.12f, 8.9f, 0.75f),     // vaso
        floatArrayOf(8.5f, 2.15f, 8.96f, 3.05f),     // pia
        floatArrayOf(5.3f, 0.05f, 6.36f, 1.05f),     // box da suíte
        floatArrayOf(4.62f, 0.12f, 5.18f, 0.75f),    // vaso da suíte
        floatArrayOf(5.92f, 1.55f, 6.38f, 2.45f),    // pia da suíte
        floatArrayOf(14.1f, 0.05f, 16.9f, 0.75f),    // máquinas e tanque da lavanderia
        floatArrayOf(17.3f, 0.05f, 17.95f, 1.6f))    // aquecedor e armário

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
    fun blocks(gw: Int, gh: Int, x: Float, z: Float, m: Float = 0.16f): Boolean {
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
    const val GX0 = W + 0.15f; const val GX1 = W + 4.6f; const val GZ0 = H - 6.8f; const val GZ1 = H.toFloat()
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
        // ---- banheiro social: box com vidro (encostado na parede da suíte), vaso no fundo, pia com espelho na parede do quarto 2
        bath(b, 6.46f, 0.05f, 7.6f, 1.15f, false, 8.61f, 0.43f, 8.72f, 2.6f, 1f, C("#80CBC4"))
        // ---- banheiro da suíte: box no canto direito, vaso no fundo, pia na parede da direita
        bath(b, 5.3f, 0.05f, 6.36f, 1.05f, true, 4.9f, 0.43f, 6.12f, 2.0f, 1f, C("#F8BBD0"))
        // ---- lavanderia: lavadora, secadora, tanque, prateleira, aquecedor, varal
        laundry(b)
        // ---- luminárias: uma plafon por cômodo
        b.m(Mt.PLAIN)
        for (p in arrayOf(floatArrayOf(2.4f, 2.8f), floatArrayOf(7.7f, 2.9f), floatArrayOf(11.5f, 2.6f), floatArrayOf(5.4f, 1.9f), floatArrayOf(16f, 2.8f), floatArrayOf(5.2f, 8.6f), floatArrayOf(14.2f, 8.6f))) {
            b.cyl(p[0], hh - 0.06, p[1], 0.24, 0.24, 0.05, C("#ECEFF1"), true, 14); b.cyl(p[0], hh - 0.065, p[1], 0.21, 0.21, 0.006, C("#FFF6D6"), false, 14)
        }
    }

    /**
     * Banheiro: box (sx0..sx1, sz0..sz1, encostado no fundo z=0; vidro na frente e no lado aberto: direita se glassRight),
     * vaso em (tx, tz) com a caixa para o fundo, pia em (px, pz) encostada numa parede em x (wall = +1 parede em x maior).
     */
    private fun bath(b: MB, sx0: Float, sz0: Float, sx1: Float, sz1: Float, glassLeft: Boolean, tx: Float, tz: Float, px: Float, pz: Float, wall: Float, towel: Int) {
        val white = C("#FAFAFA"); val chrome = C("#CFD8DC")
        val gx = if (glassLeft) sx0 else sx1; val wx = if (glassLeft) sx1 else sx0
        b.m(Mt.TILE, 0.4f); b.box((sx0 + sx1) / 2, 0.03, (sz0 + sz1) / 2, sx1 - sx0, 0.06, sz1 - sz0, C("#B0BEC5"))
        b.m(Mt.GLASS); b.box((sx0 + sx1) / 2, 1.0, sz1, sx1 - sx0, 1.9, 0.02, C("#D6EEF5")); b.box(gx, 1.0, (sz0 + sz1) / 2, 0.02, 1.9, sz1 - sz0, C("#D6EEF5"))
        b.m(Mt.METAL); b.box(gx, 1.0, sz1, 0.03, 1.95, 0.03, chrome); b.cyl((sx0 + sx1) / 2, 1.9, sz0 + 0.14, 0.1, 0.1, 0.02, chrome, true, 10); b.box((sx0 + sx1) / 2, 1.6, sz0 + 0.04, 0.03, 0.6, 0.03, chrome)
        b.m(Mt.TILE, 0.35f); b.box((sx0 + sx1) / 2, 1.1, sz0 + 0.02, sx1 - sx0, 2.0, 0.02, C("#E0F2F1")); b.box(wx + (if (glassLeft) -0.01f else 0.01f), 1.1, (sz0 + sz1) / 2, 0.02, 2.0, sz1 - sz0, C("#E0F2F1"))
        // vaso: base, assento, caixa acoplada no fundo
        b.m(Mt.PLAIN); b.box(tx, 0.2, tz + 0.04f, 0.38, 0.4, 0.5, white); b.box(tx, 0.42, tz + 0.04f, 0.4, 0.04, 0.48, white); b.box(tx, 0.62, tz - 0.2f, 0.42, 0.4, 0.16, white)
        b.m(Mt.METAL); b.box(tx + 0.12f, 0.84, tz - 0.2f, 0.06, 0.02, 0.04, chrome)
        // pia: gabinete de madeira, tampo de pedra, torneira junto da parede, espelho na parede
        b.m(Mt.WOOD, 0.5f); b.box(px, 0.42, pz, 0.46, 0.8, 0.9, C("#8D6E63"))
        b.m(Mt.STONE, 0.6f); b.box(px, 0.85, pz, 0.5, 0.05, 0.95, C("#ECEFF1"))
        b.m(Mt.PLAIN); b.box(px - wall * 0.02f, 0.885, pz, 0.32, 0.01, 0.5, C("#FFFFFF"))
        b.m(Mt.METAL); b.cyl(px + wall * 0.17f, 0.88, pz, 0.025, 0.025, 0.2, chrome, true, 8); b.box(px + wall * 0.1f, 1.06, pz, 0.14, 0.025, 0.025, chrome)
        b.m(Mt.GLASS); b.box(px + wall * 0.22f, 1.55, pz, 0.02, 0.8, 0.7, C("#E3F2FD"))
        b.m(Mt.FABRIC); b.box(px + wall * 0.2f, 1.2, pz + 0.65f, 0.04, 0.5, 0.35, towel)
    }

    private fun laundry(b: MB) {
        val white = C("#F5F5F5")
        for ((i, x) in floatArrayOf(14.5f, 15.25f).withIndex()) {
            b.m(Mt.METAL); b.box(x.toDouble(), 0.43, 0.38, 0.66, 0.86, 0.62, white)
            b.m(Mt.PLAIN); b.cyl(x.toDouble(), 0.4, 0.69, 0.2, 0.2, 0.01, C(if (i == 0) "#90A4AE" else "#B0BEC5"), true, 14)
            b.box(x.toDouble(), 0.78, 0.7, 0.5, 0.06, 0.01, C("#263238")); b.box(x + 0.2, 0.79, 0.71, 0.06, 0.03, 0.01, C("#4FC3F7"), false)
        }
        // tanque com torneira
        b.m(Mt.STONE, 0.6f); b.box(16.3, 0.45, 0.38, 0.9, 0.9, 0.62, C("#E0E0E0")); b.box(16.3, 0.9, 0.38, 0.95, 0.05, 0.66, C("#EEEEEE"))
        b.m(Mt.METAL); b.cyl(16.3, 0.93, 0.12, 0.025, 0.025, 0.25, C("#CFD8DC"), true, 8)
        // prateleira com produtos de limpeza
        b.m(Mt.WOOD, 0.5f); b.box(15.4, 1.6, 0.16, 2.6, 0.04, 0.3, C("#A1887F"))
        b.m(Mt.PLAIN); for (k in 0 until 7) b.box(14.3 + k * 0.33, 1.72, 0.16, 0.12, 0.2 + (k % 3) * 0.05, 0.1, C(arrayOf("#1E88E5", "#E53935", "#FDD835", "#43A047", "#8E24AA", "#FB8C00", "#00ACC1")[k]))
        // aquecedor e armário alto
        b.m(Mt.WOOD, 0.5f); b.box(17.62, 1.0, 0.82, 0.6, 2.0, 1.5, C("#ECE6DA")); b.m(Mt.METAL); b.box(17.31, 1.1, 0.82, 0.02, 0.1, 0.5, C("#9E9E9E"))
        b.m(Mt.METAL); b.cyl(17.62, 2.05, 0.82, 0.22, 0.22, 0.4, C("#ECEFF1"), true, 12)
        // varal de teto com roupas
        b.m(Mt.METAL); b.box(15.6, 2.4, 2.6, 2.6, 0.03, 0.03, C("#9E9E9E")); b.box(15.6, 2.4, 3.2, 2.6, 0.03, 0.03, C("#9E9E9E"))
        b.m(Mt.FABRIC); for (k in 0 until 5) b.box(14.6 + k * 0.5, 2.15, 2.6 + (k % 2) * 0.6, 0.35, 0.5, 0.02, C(arrayOf("#EF5350", "#42A5F5", "#FFFFFF", "#66BB6A", "#FFCA28")[k]))
        // cesto de roupa
        b.m(Mt.PLAIN); b.cyl(16.9, 0.0, 1.5, 0.25, 0.28, 0.5, C("#D7CCC8"), true, 10)
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
