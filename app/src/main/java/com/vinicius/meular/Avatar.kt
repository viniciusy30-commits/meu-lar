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
        val f = a.female
        val skin = pick(AvaPal.SKIN, a.skin)
        val hc = pick(AvaPal.HAIR, a.hairC)
        val bc = if (a.hairC >= 7) C("#3A2A20") else hc
        val eyeC = pick(AvaPal.EYE, a.eye)
        val tc = pick(AvaPal.TOP, a.topC)
        val bot = pick(AvaPal.BOT, a.botC)
        val shoe = pick(AvaPal.SHOE, a.shoeC)
        val bi = a.body.coerceIn(0, 2)

        // proporções
        val hipY = if (f) 0.86 else 0.90
        val torsoH = if (f) 0.52 else 0.56
        val shY = hipY + torsoH
        val headY = shY + 0.185
        val sw = if (f) doubleArrayOf(0.34, 0.37, 0.42)[bi] else doubleArrayOf(0.40, 0.44, 0.50)[bi]
        val dep = if (f) doubleArrayOf(0.18, 0.20, 0.24)[bi] else doubleArrayOf(0.20, 0.22, 0.26)[bi]
        val ws = if (f) sw * 0.80 else sw * 0.92
        val hipW = if (f) sw * 1.12 else sw * 0.95
        val lx = hipW / 4.0
        val rTop = lx * 0.88
        val rAnk = rTop * 0.55
        val armX = sw / 2.0 + 0.045
        val dress = a.top == 4
        val sides = doubleArrayOf(-1.0, 1.0)

        fun rl(y: Double): Double = rAnk + (rTop - rAnk) * ((y - 0.07) / (hipY - 0.07))

        // ---------- pernas e sapatos (pele)
        b.m(Mt.PLAIN)
        for (sx in sides) {

            val x = sx * lx
            b.cyl(x, 0.07, 0.0, rAnk, rTop, hipY - 0.07, skin, true, 14)
            b.rbox(x, 0.04, 0.045, 0.1, 0.07, 0.26, 0.03, shoe)
            b.box(x, 0.013, 0.045, 0.104, 0.026, 0.264, C("#EDEDED"))
        }

        // ---------- roupa de baixo
        b.m(Mt.FABRIC, 1.4f)
        if (!dress) {
            when (a.bottom) {
                0 -> for (sx in sides) {
                    b.cyl(sx * lx, 0.07, 0.0, rAnk + 0.008, rTop + 0.012, hipY - 0.07, bot, true, 14)
                }
                1 -> for (sx in sides) {
                    val by = hipY - 0.36
                    b.cyl(sx * lx, by, 0.0, rl(by) + 0.014, rTop + 0.014, 0.36, bot, true, 14)
                }
                2 -> {
                    val prof = floatArrayOf(0.26f, 0f, 0.23f, 0.10f, 0.20f, 0.20f, 0.18f, 0.28f, 0.19f, 0.32f)
                    b.lathe(0.0, hipY - 0.26, 0.0, prof, bot, true, 24)
                }
                else -> for (sx in sides) {
                    val by = hipY - 0.17
                    b.cyl(sx * lx, by, 0.0, rl(by) + 0.014, rTop + 0.014, 0.17, bot, true, 14)
                }
            }
        } else {
            val prof = floatArrayOf(0.30f, 0f, 0.26f, 0.12f, 0.20f, 0.28f, 0.16f, 0.42f, 0.17f, 0.50f)
            b.lathe(0.0, hipY - 0.40, 0.0, prof, tc, true, 24)
        }
        b.rbox(0.0, hipY, 0.0, hipW, 0.2, dep, 0.07, if (dress) tc else bot)


        // ---------- tronco
        val hood = a.top == 3
        val tw = if (hood) sw + 0.03 else sw
        val td = if (hood) dep + 0.03 else dep
        val twaist = ws + (tw - sw)
        b.rbox(0.0, shY - 0.17, 0.0, tw, 0.34, td, 0.075, tc)
        b.rbox(0.0, hipY + (torsoH - 0.34) / 2.0 + 0.04, 0.0, twaist, torsoH - 0.34 + 0.1, td * 0.92, 0.06, tc)
        if (f) {
            for (sx in sides) b.sphere(sx * 0.075, shY - 0.2, td / 2.0 - 0.012, 0.055, tc, 0.05, 8)
        }
        if (hood) {
            b.sphere(0.0, shY + 0.0, -0.1, 0.075, tc, 0.06, 8)
        }

        // ---------- mangas
        for (sx in sides) {
            val x = sx * armX
            when (a.top) {
                0 -> b.cyl(x, shY - 0.26, 0.0, 0.05, 0.058, 0.25, tc, true, 12)
                1 -> b.cyl(x, shY - 0.58, 0.0, 0.043, 0.058, 0.56, tc, true, 12)
                3 -> b.cyl(x, shY - 0.58, 0.0, 0.049, 0.064, 0.56, tc, true, 12)
                else -> {}
            }
        }

        // ---------- braços, pescoço e cabeça (pele)
        b.m(Mt.PLAIN)
        val sleeve = a.top == 0 || a.top == 1 || a.top == 3
        for (sx in sides) {
            val x = sx * armX
            b.cyl(x, shY - 0.60, 0.0, 0.034, 0.042, 0.56, skin, true, 12)
            b.sphere(x, shY - 0.64, 0.0, 0.04, skin, 0.052, 8)

        }
        for (sx in sides) {
            b.sphere(sx * armX, shY - 0.05, 0.0, 0.058, if (sleeve) tc else skin, 0.056, 8)
        }
        b.cyl(0.0, shY - 0.01, 0.0, 0.046, 0.042, 0.1, skin, true, 12)
        b.sphere(0.0, headY, 0.0, 0.105, skin, 0.125, 14)
        for (sx in sides) b.sphere(sx * 0.104, headY - 0.005, 0.0, 0.02, skin, 0.028, 6)
        b.sphere(0.0, headY - 0.018, 0.106, 0.017, shade(skin, -10), 0.019, 6)

        // olhos
        val white = C("#F6F6F6")
        val dark = C("#14161C")
        val browC = shade(bc, -30)
        for (sx in sides) {
            val x = sx * 0.04
            b.sphere(x, headY + 0.008, 0.088, 0.02, white, 0.02, 8)
            b.sphere(x, headY + 0.008, 0.098, 0.012, eyeC, 0.013, 8)
            b.sphere(x, headY + 0.008, 0.106, 0.0065, dark, 0.007, 6)
            b.box(sx * 0.042, headY + 0.045, 0.091, 0.044, 0.008, 0.014, browC)
            if (f) b.box(x, headY + 0.03, 0.098, 0.038, 0.006, 0.01, dark)
        }
        // boca
        b.box(0.0, headY - 0.056, 0.094, 0.034, 0.008, 0.012, if (f) C("#C9505C") else C("#A8524A"))

        // ---------- barba
        if (a.beard > 0) {
            b.box(0.0, headY - 0.04, 0.1, 0.07, 0.014, 0.02, bc)
            if (a.beard == 2) {
                b.box(0.0, headY - 0.1, 0.068, 0.04, 0.05, 0.03, bc)
            } else if (a.beard == 3) {
                b.box(0.0, headY - 0.1, 0.06, 0.11, 0.05, 0.06, bc)
                for (sx in sides) b.box(sx * 0.085, headY - 0.07, 0.03, 0.03, 0.08, 0.1, bc)

            }
        }

        // ---------- óculos
        if (a.glasses > 0) {
            val fr = C("#222831")
            val hy = headY + 0.008
            for (sx in sides) {
                val x = sx * 0.042
                when (a.glasses) {
                    1 -> for (i in 0 until 12) {
                        val an = 2.0 * PI * i / 12
                        b.box(x + 0.032 * cos(an), hy + 0.032 * sin(an), 0.113, 0.012, 0.012, 0.007, fr)
                    }
                    2 -> {
                        b.box(x, hy + 0.026, 0.113, 0.07, 0.008, 0.008, fr)
                        b.box(x, hy - 0.026, 0.113, 0.07, 0.008, 0.008, fr)
                        b.box(x - 0.035, hy, 0.113, 0.008, 0.052, 0.008, fr)
                        b.box(x + 0.035, hy, 0.113, 0.008, 0.052, 0.008, fr)
                    }
                    else -> b.rbox(x, hy, 0.112, 0.068, 0.045, 0.012, 0.012, C("#15181F"))
                }
                b.box(sx * 0.108, hy + 0.004, 0.05, 0.007, 0.007, 0.12, fr)
            }
            b.box(0.0, hy + 0.004, 0.113, 0.03, 0.007, 0.007, fr)
        }

        // ---------- cabelo
        fun dome(c: Int) {
            val n = 7
            val prof = FloatArray(n * 2)
            for (i in 0 until n) {

                val an = PI / 2.0 * i / (n - 1)
                prof[i * 2] = (0.113 * cos(an)).toFloat()
                prof[i * 2 + 1] = (0.09 * sin(an)).toFloat()
            }
            b.lathe(0.0, headY + 0.05, -0.005, prof, c, true, 18)
        }
        when (a.hair) {
            1 -> {
                dome(hc)
                b.sphere(0.0, headY, -0.03, 0.111, hc, 0.115, 10)
            }
            2 -> {
                dome(hc)
                b.sphere(0.0, headY - 0.06, -0.045, 0.118, hc, 0.15, 10)
            }
            3 -> {
                dome(hc)
                b.sphere(0.0, headY - 0.06, -0.045, 0.118, hc, 0.15, 10)
                b.rbox(0.0, headY - 0.22, -0.085, 0.23, 0.42, 0.07, 0.03, hc)
                for (sx in sides) b.rbox(sx * 0.115, headY - 0.1, -0.02, 0.03, 0.26, 0.12, 0.012, hc)
            }
            4 -> {
                dome(hc)
                b.sphere(0.0, headY, -0.03, 0.111, hc, 0.115, 10)
                b.sphere(0.0, headY - 0.01, -0.125, 0.028, C("#E5484D"), 0.028, 6)
                b.cyl(0.0, headY - 0.2, -0.15, 0.02, 0.05, 0.2, hc, true, 10)
            }
            5 -> {
                dome(hc)
                b.sphere(0.0, headY, -0.03, 0.111, hc, 0.115, 10)
                b.sphere(0.0, headY + 0.145, -0.055, 0.058, hc, 0.052, 10)
            }

            6 -> {
                dome(mix(skin, hc, 0.35f))
                b.rbox(0.0, headY + 0.12, -0.015, 0.035, 0.075, 0.2, 0.014, hc)
            }
            7 -> {
                b.sphere(0.0, headY + 0.045, -0.07, 0.17, hc, 0.16, 12)
            }
            8 -> {
                dome(hc)
                b.sphere(0.0, headY, -0.03, 0.111, hc, 0.115, 10)
                b.rbox(0.0, headY + 0.145, 0.045, 0.15, 0.05, 0.14, 0.022, hc)
            }
            else -> {}
        }
        return b.toMesh()
    }
}
