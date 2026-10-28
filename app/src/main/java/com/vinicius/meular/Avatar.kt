package com.vinicius.meular

import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin
import kotlin.random.Random

/** Paletas e nomes usados pelo criador de personagem. */
object AvaPal {
    val SKIN = intArrayOf(C("#FFE0C4"), C("#F5C9A0"), C("#E0A878"), C("#C58B5C"), C("#8E5A3A"), C("#5B3A26"))
    val HAIR = intArrayOf(
        C("#1C1A1A"), C("#3B2A1E"), C("#6B4A2F"), C("#D8B25E"), C("#B5482A"),
        C("#9A9A9F"), C("#EDEDED"), C("#3F6FD8"), C("#E86FA8"), C("#3FB57A")
    )
    val EYE = intArrayOf(C("#5B3A1E"), C("#3B7FD0"), C("#3E9B5B"), C("#7F8C99"), C("#B5772B"), C("#1B1B1B"))
    val TOP = intArrayOf(
        C("#FFFFFF"), C("#2B2F3A"), C("#E5484D"), C("#F2A33A"), C("#F4D35E"),
        C("#3CCB7F"), C("#3E8EDE"), C("#7B5CD6"), C("#EE6FA6"), C("#8B6B4A")
    )
    val BOT = intArrayOf(
        C("#2E4A7D"), C("#1E2230"), C("#6B6F7A"), C("#C9B79C"), C("#7A4E32"),
        C("#FFFFFF"), C("#3F7D5A"), C("#B03A48"), C("#E8A6C0"), C("#4F5BD5")
    )
    val SHOE = intArrayOf(C("#FFFFFF"), C("#1E2230"), C("#E5484D"), C("#3E8EDE"), C("#7A4E32"), C("#F2A33A"))

    val HAIR_N = listOf("Careca", "Curto", "Médio", "Longo", "Rabo de cavalo", "Coque", "Moicano", "Black power", "Topete")
    val BODY_N = listOf("Magro", "Médio", "Forte")
    val TOP_N = listOf("Camiseta", "Manga longa", "Regata", "Moletom", "Vestido")
    val BOT_N = listOf("Calça", "Bermuda", "Saia", "Short")
    val GLASS_N = listOf("Sem óculos", "Redondo", "Quadrado", "Escuro")
    val BEARD_N = listOf("Sem barba", "Bigode", "Cavanhaque", "Barba cheia")

}

/** Dados do personagem (salvos como texto simples). */
class Avatar(
    var female: Boolean = false,
    var skin: Int = 1,
    var body: Int = 1,
    var hair: Int = 1,
    var hairC: Int = 1,
    var eye: Int = 0,
    var top: Int = 0,
    var topC: Int = 6,
    var bottom: Int = 0,
    var botC: Int = 0,
    var shoeC: Int = 0,
    var glasses: Int = 0,
    var beard: Int = 0
) {
    fun encode(): String = listOf(
        if (female) 1 else 0, skin, body, hair, hairC, eye, top, topC, bottom, botC, shoeC, glasses, beard
    ).joinToString(",")

    /** Troca de gênero com um visual-base bonito, mantendo pele, olhos e cor do cabelo. */
    fun applyGender(f: Boolean) {
        female = f
        if (f) {
            hair = 3; beard = 0; top = 0; topC = 8; bottom = 0; botC = 0; shoeC = 0
        } else {
            hair = 1; top = 0; topC = 6; bottom = 0; botC = 1; shoeC = 0
        }
    }


    companion object {
        fun decode(s: String?): Avatar? {
            if (s.isNullOrBlank()) return null
            return try {
                val p = s.split(",").map { it.trim().toInt() }
                if (p.size < 13) null
                else Avatar(
                    p[0] == 1,
                    p[1].coerceIn(0, AvaPal.SKIN.size - 1),
                    p[2].coerceIn(0, 2),
                    p[3].coerceIn(0, AvaPal.HAIR_N.size - 1),
                    p[4].coerceIn(0, AvaPal.HAIR.size - 1),
                    p[5].coerceIn(0, AvaPal.EYE.size - 1),
                    p[6].coerceIn(0, AvaPal.TOP_N.size - 1),
                    p[7].coerceIn(0, AvaPal.TOP.size - 1),
                    p[8].coerceIn(0, AvaPal.BOT_N.size - 1),
                    p[9].coerceIn(0, AvaPal.BOT.size - 1),
                    p[10].coerceIn(0, AvaPal.SHOE.size - 1),
                    p[11].coerceIn(0, AvaPal.GLASS_N.size - 1),
                    p[12].coerceIn(0, AvaPal.BEARD_N.size - 1)
                )
            } catch (e: Exception) {
                null
            }
        }

        fun random(female: Boolean): Avatar {
            val r = Random
            val hairs = if (female) listOf(2, 3, 3, 4, 5, 7, 8) else listOf(0, 1, 1, 6, 7, 8, 2)
            val beards = if (female) listOf(0) else listOf(0, 0, 0, 1, 2, 3)
            return Avatar(
                female,

                r.nextInt(AvaPal.SKIN.size),
                r.nextInt(3),
                hairs.random(),
                if (r.nextInt(5) == 0) r.nextInt(AvaPal.HAIR.size) else r.nextInt(7),
                r.nextInt(AvaPal.EYE.size),
                if (female) listOf(0, 1, 2, 4, 4).random() else listOf(0, 0, 1, 2, 3).random(),
                r.nextInt(AvaPal.TOP.size),
                if (female) listOf(0, 1, 2, 3).random() else listOf(0, 0, 1, 3).random(),
                r.nextInt(AvaPal.BOT.size),
                r.nextInt(AvaPal.SHOE.size),
                listOf(0, 0, 0, 1, 2, 3).random(),
                beards.random()
            )
        }
    }
}

/** Modelo 3D do personagem (origem nos pés, rosto virado para +z) e o palco do criador. */
object AvatarModel {
    private fun pick(arr: IntArray, i: Int): Int = arr[i.coerceIn(0, arr.size - 1)]

    fun stage(): Mesh {
        val b = MB()
        b.m(Mt.PLAIN)
        b.cyl(0.0, 0.0, 0.0, 1.36, 1.36, 0.05, C("#FF7A59"), true, 56)
        b.cyl(0.0, 0.0, 0.0, 1.3, 1.3, 0.082, C("#2C3450"), true, 56)
        b.cyl(0.0, 0.0, 0.0, 1.0, 1.0, 0.0835, C("#343D5C"), true, 56)
        b.blob(0.0, 0.0855, 0.0, 0.62, 0.5, 0.45f)
        return b.toMesh()
    }

    fun build(a: Avatar): Mesh {
        val b = MB()
        b.m(Mt.PLAIN)
        val f = a.female
        val skin = pick(AvaPal.SKIN, a.skin)
        val hc = pick(AvaPal.HAIR, a.hairC)
        val bc = if (a.hairC >= 7) C("#3A2A20") else hc
        val eyeC = pick(AvaPal.EYE, a.eye)
        val tc = pick(AvaPal.TOP, a.topC)
        val bot = pick(AvaPal.BOT, a.botC)
        val shoe = pick(AvaPal.SHOE, a.shoeC)
        val bi = a.body.coerceIn(0, 2)
        val sides = doubleArrayOf(-1.0, 1.0)

        // proporções estilizadas: cabeça grande, pernas curtas
        val k = doubleArrayOf(0.88, 1.0, 1.15)[bi]
        val hipY = 0.62
        val shY = 1.0
        val headY = 1.36
        val lx = 0.095 * (0.92 + 0.08 * k) + (if (f) 0.004 else 0.0)
        val chest = (if (f) 0.165 else 0.185) * k
        val armX = chest + 0.05
        val dress = a.top == 4
        val skinD = shade(skin, -22)
        val white = C("#FAFAFA")
        val dark = C("#15171D")

        // ---------- pernas e sapatos
        for (sx in sides) {
            val x = sx * lx
            b.cyl(x, 0.09, 0.0, 0.066, 0.097, hipY - 0.09, skin, true, 16)
            b.rbox(x, 0.055, 0.04, 0.165, 0.105, 0.31, 0.05, shoe)
            b.box(x, 0.012, 0.045, 0.168, 0.024, 0.318, C("#F2F2F2"))
        }

        // ---------- roupa de baixo
        val botC = if (dress) tc else bot
        b.sphere(0.0, hipY + 0.01, 0.0, 0.175 * k + (if (f) 0.012 else 0.0), botC, 0.115, 18)
        if (!dress) {
            when (a.bottom) {
                0 -> for (sx in sides) b.cyl(sx * lx, 0.09, 0.0, 0.074, 0.106, hipY - 0.07, bot, true, 16)
                1 -> for (sx in sides) b.cyl(sx * lx, 0.30, 0.0, 0.098, 0.106, hipY - 0.28, bot, true, 16)
                2 -> b.lathe(0.0, 0.30, 0.0, floatArrayOf(0.31f, 0f, 0.28f, 0.12f, 0.23f, 0.24f, 0.19f, 0.33f, 0.18f, 0.37f), bot, true, 28)
                else -> for (sx in sides) b.cyl(sx * lx, 0.44, 0.0, 0.102, 0.108, hipY - 0.42, bot, true, 16)
            }
        } else {
            val prof = floatArrayOf(0.33f, 0f, 0.30f, 0.12f, 0.24f, 0.26f, 0.19f, 0.38f, 0.17f, 0.46f)
            b.lathe(0.0, 0.24, 0.0, prof, tc, true, 28)
        }

        // ---------- tronco
        val hood = a.top == 3
        val ks = if (hood) 1.08 else 1.0
        val tp = if (f) floatArrayOf(0.155f, 0f, 0.14f, 0.12f, 0.145f, 0.22f, 0.165f, 0.32f, 0.15f, 0.40f, 0.10f, 0.44f, 0.05f, 0.46f)
        else floatArrayOf(0.150f, 0f, 0.165f, 0.08f, 0.175f, 0.2f, 0.19f, 0.32f, 0.175f, 0.40f, 0.10f, 0.44f, 0.05f, 0.46f)
        val prof = FloatArray(tp.size) { i -> (tp[i] * (if (i % 2 == 0) (k * ks) else 1.0)).toFloat() }
        b.lathe(0.0, 0.58, 0.0, prof, tc, true, 28)
        if (f) for (sx in sides) b.sphere(sx * 0.07, 0.84, 0.115, 0.06, tc, 0.055, 12)
        // gola
        b.cyl(0.0, 1.0, 0.0, 0.075, 0.068, 0.04, shade(tc, -28), true, 18)
        if (hood) {
            b.sphere(0.0, 1.03, -0.09, 0.11, tc, 0.07, 12)
            b.rbox(0.0, 0.72, 0.165 * k, 0.2, 0.09, 0.05, 0.03, shade(tc, -18))
        }

        // ---------- braços
        val sleeveLong = a.top == 1 || a.top == 3
        val sleeveShort = a.top == 0 || a.top == 4
        for (sx in sides) {
            val x = sx * armX
            b.cyl(x, 0.58, 0.0, 0.040, 0.050, 0.42, skin, true, 14)
            b.sphere(x, 0.565, 0.0, 0.056, skin, 0.058, 12)
            if (sleeveLong) b.cyl(x, 0.60, 0.0, 0.052, 0.066, 0.40, tc, true, 14)
            else if (sleeveShort) b.cyl(x, 0.84, 0.0, 0.062, 0.068, 0.16, tc, true, 14)
            b.sphere(x, 0.985, 0.0, 0.07, if (a.top == 2) skin else tc, 0.066, 12)
        }

        // ---------- pescoço e cabeça
        b.cyl(0.0, 1.0, 0.0, 0.058, 0.052, 0.12, skin, true, 14)
        b.sphere(0.0, headY, 0.0, 0.30, skin, 0.29, 24)
        for (sx in sides) {
            b.sphere(sx * 0.295, headY - 0.01, -0.01, 0.045, skin, 0.06, 10)
            b.sphere(sx * 0.304, headY - 0.01, -0.005, 0.025, skinD, 0.036, 8)
        }
        // bochechas e nariz
        val blush = mix(skin, C("#FF6B7E"), 0.30f)
        for (sx in sides) b.sphere(sx * 0.17, headY - 0.075, 0.225, 0.036, blush, 0.02, 10)
        b.sphere(0.0, headY - 0.05, 0.292, 0.028, shade(skin, -8), 0.026, 10)

        // olhos grandes
        val browC = shade(bc, -35)
        for (sx in sides) {
            val x = sx * 0.11
            b.sphere(x, headY + 0.005, 0.245, 0.062, white, 0.078, 14)
            b.sphere(x, headY + 0.005, 0.268, 0.044, eyeC, 0.058, 14)
            b.sphere(x, headY + 0.005, 0.287, 0.026, dark, 0.034, 10)
            b.sphere(x + 0.016, headY + 0.03, 0.31, 0.012, white, 0.012, 6, false)
            b.sphere(x - 0.012, headY - 0.02, 0.305, 0.006, white, 0.006, 6, false)
            b.box(x, headY + 0.098, 0.262, 0.085, 0.017, 0.02, browC)
            if (f) {
                b.box(x, headY + 0.082, 0.272, 0.115, 0.012, 0.02, dark)
                b.box(sx * 0.172, headY + 0.07, 0.25, 0.014, 0.016, 0.018, dark)
            }
        }
        // boca (sorriso)
        val lip = if (f) C("#D4566A") else C("#B24A55")
        for (i in -3..3) {
            b.sphere(i * 0.016, headY - 0.125 + 0.0034 * i * i, 0.262, 0.0085, lip, 0.0085, 6)
        }

        // ---------- barba
        if (a.beard > 0) {
            b.rbox(0.0, headY - 0.092, 0.283, 0.13, 0.026, 0.026, 0.012, bc)
            if (a.beard == 2) {
                b.rbox(0.0, headY - 0.235, 0.172, 0.075, 0.085, 0.075, 0.03, bc)
            } else if (a.beard == 3) {
                b.sphere(0.0, headY - 0.20, 0.03, 0.268, bc, 0.12, 20)
                b.rbox(0.0, headY - 0.245, 0.17, 0.12, 0.07, 0.07, 0.03, bc)
            }
        }

        // ---------- óculos
        if (a.glasses > 0) {
            val fr = C("#1D222B")
            val hy = headY + 0.005
            for (sx in sides) {
                val x = sx * 0.11
                when (a.glasses) {
                    1 -> for (i in 0 until 16) {
                        val an = 2.0 * PI * i / 16
                        b.box(x + 0.082 * cos(an), hy + 0.082 * sin(an), 0.318, 0.016, 0.016, 0.014, fr)
                    }
                    2 -> {
                        b.box(x, hy + 0.075, 0.318, 0.17, 0.014, 0.014, fr)
                        b.box(x, hy - 0.075, 0.318, 0.17, 0.014, 0.014, fr)
                        b.box(x - 0.085, hy, 0.318, 0.014, 0.16, 0.014, fr)
                        b.box(x + 0.085, hy, 0.318, 0.014, 0.16, 0.014, fr)
                    }
                    else -> b.rbox(x, hy, 0.318, 0.18, 0.13, 0.016, 0.04, C("#0E1117"))
                }
                b.box(sx * 0.285, hy + 0.01, 0.15, 0.012, 0.012, 0.3, fr)
            }
            b.box(0.0, hy + 0.02, 0.318, 0.05, 0.012, 0.014, fr)
        }

        // ---------- cabelo
        fun dome() {
            val n = 8
            val pr = FloatArray(n * 2)
            for (i in 0 until n) {
                val an = PI / 2.0 * i / (n - 1)
                pr[i * 2] = (0.322 * cos(an)).toFloat()
                pr[i * 2 + 1] = (0.25 * sin(an)).toFloat()
            }
            b.lathe(0.0, headY + 0.10, -0.01, pr, hc, true, 24)
        }
        fun fringe() {
            for (j in -2..2) {
                val x = j * 0.075
                b.sphere(x, headY + 0.15 - 0.012 * (if (j % 2 == 0) 0 else 1), 0.19, 0.062, hc, 0.07, 10)
            }
        }
        fun back(ry: Double, dy: Double) {
            b.sphere(0.0, headY + dy, -0.05, 0.312, hc, ry, 20)
        }
        when (a.hair) {
            1 -> { dome(); back(0.25, 0.05); fringe() }
            2 -> {
                dome(); back(0.30, -0.02); fringe()
                for (sx in sides) b.sphere(sx * 0.27, headY - 0.04, 0.02, 0.07, hc, 0.16, 10)
            }
            3 -> {
                dome(); back(0.30, -0.02); fringe()
                b.rbox(0.0, headY - 0.32, -0.16, 0.5, 0.6, 0.13, 0.06, hc)
                for (sx in sides) b.rbox(sx * 0.29, headY - 0.22, 0.0, 0.07, 0.36, 0.2, 0.03, hc)
            }
            4 -> {
                dome(); back(0.25, 0.05); fringe()
                b.sphere(0.0, headY + 0.03, -0.31, 0.04, C("#E5484D"), 0.04, 8)
                b.cyl(0.0, headY - 0.34, -0.36, 0.035, 0.07, 0.4, hc, true, 12)
                b.sphere(0.0, headY - 0.36, -0.36, 0.06, hc, 0.06, 10)
            }
            5 -> {
                dome(); back(0.25, 0.05); fringe()
                b.sphere(0.0, headY + 0.40, -0.04, 0.12, hc, 0.11, 14)
                b.cyl(0.0, headY + 0.30, -0.04, 0.07, 0.07, 0.03, C("#E5484D"), true, 12)
            }
            6 -> {
                b.sphere(0.0, headY + 0.03, -0.02, 0.305, mix(skin, hc, 0.30f), 0.29, 20)
                b.rbox(0.0, headY + 0.33, -0.02, 0.075, 0.16, 0.46, 0.035, hc)
            }
            7 -> {
                b.sphere(0.0, headY + 0.10, -0.10, 0.38, hc, 0.32, 18)
                for (sx in sides) b.sphere(sx * 0.2, headY + 0.28, 0.0, 0.14, hc, 0.12, 10)
            }
            8 -> {
                dome(); back(0.25, 0.05); fringe()
                b.rbox(0.0, headY + 0.33, 0.07, 0.34, 0.13, 0.3, 0.06, hc)
            }
            else -> {}
        }
        return b.toMesh()
    }
}
