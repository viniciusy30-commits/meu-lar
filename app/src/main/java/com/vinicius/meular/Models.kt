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

    // Etapa 68: móveis básicos modelados (assets/flora/f_*.bin, ferramentas/ambiente/furn_items.py). Se o arquivo faltar, cai no modelo antigo de caixas.
    private val FURN = mapOf(
        Type.CHAIR to "f_chair", Type.TABLE to "f_table", Type.BED to "f_bed", Type.SOFA to "f_sofa", Type.SHELF to "f_shelf",
        Type.PLANT to "f_plant", Type.RUG to "f_rug", Type.TV to "f_tv", Type.FRIDGE to "f_fridge", Type.STOVE to "f_stove",
        Type.LAMP to "f_lamp", Type.NIGHT to "f_night", Type.COFFEE to "f_coffee", Type.WARDROBE to "f_wardrobe"
    )

    fun furniture(t: Type): Mesh {
        t.mob?.let { return MobLoader.load(it) }
        FURN[t]?.let { id ->
            val fb = Flora.Batch()
            fb.place(id, 0.0, 0.0, 0.0)
            val parts = fb.build()
            if (parts.isNotEmpty()) return Mesh(parts)
        }
        val b = MB()
        when (t) {
            Type.CHAIR -> {
                val wd = C("#B8824F"); val cu = C("#D9645A")
                b.m(Mt.WOOD)
                for (lx in listOf(0.29, 0.71)) for (lz in listOf(0.29, 0.71)) leg(b, lx, lz, 0.45, 0.018, 0.028, wd)
                b.rbox(0.5, 0.465, 0.5, 0.46, 0.05, 0.46, 0.02, wd)
                b.rbox(0.29, 0.74, 0.29, 0.04, 0.5, 0.04, 0.015, wd, true, 1)
                b.rbox(0.71, 0.74, 0.29, 0.04, 0.5, 0.04, 0.015, wd, true, 1)
                b.rbox(0.5, 0.94, 0.29, 0.46, 0.08, 0.045, 0.02, wd)
                b.rbox(0.5, 0.72, 0.29, 0.38, 0.05, 0.02, 0.01, wd, true, 1)
                b.rbox(0.5, 0.82, 0.29, 0.38, 0.05, 0.02, 0.01, wd, true, 1)
                b.m(Mt.FABRIC, 1.5f)
                b.rbox(0.5, 0.505, 0.51, 0.41, 0.05, 0.40, 0.022, cu)
            }
            Type.TABLE -> {
                val wood = C("#D9A56C"); val dk = C("#8A5A3A")
                b.m(Mt.WOOD)
                b.rbox(1.0, 0.77, 0.5, 1.88, 0.06, 0.9, 0.025, wood, true, 3)
                b.rbox(1.0, 0.715, 0.5, 1.6, 0.05, 0.68, 0.012, dk)
                for (lx in listOf(0.2, 1.8)) for (lz in listOf(0.2, 0.8)) leg(b, lx, lz, 0.74, 0.025, 0.04, dk)
                b.m(Mt.FABRIC, 1.5f)
                b.rbox(1.0, 0.803, 0.5, 1.5, 0.006, 0.3, 0.003, C("#E9E2D3"))
                b.m(Mt.PLAIN)
                val vase = floatArrayOf(0f, 0f, 0.06f, 0f, 0.085f, 0.05f, 0.1f, 0.12f, 0.07f, 0.21f, 0.04f, 0.26f, 0.055f, 0.29f, 0.045f, 0.29f)
                b.lathe(1.0, 0.806, 0.5, vase, C("#5DB1D6"), true, 20)
                b.m(Mt.GRASS, 2f)
                val fl = listOf(C("#F26B8A"), C("#FFD24D"), C("#FFFFFF"), C("#E9825A"), C("#B48CF2"))
                val px = listOf(0.0, -0.08, 0.09, -0.04, 0.06)
                val pz = listOf(0.0, 0.03, -0.04, -0.07, 0.07)
                val py = listOf(0.52, 0.46, 0.48, 0.42, 0.44)
                b.sphere(1.0, 1.1, 0.5, 0.17, C("#4C9A3C"), 0.12, 8)
                b.m(Mt.PLAIN)
                for (i in 0 until 5) b.sphere(1.0 + px[i], 0.806 + py[i] + 0.12, 0.5 + pz[i], 0.06, fl[i], 0.06, 7)
                for (cx in listOf(0.45, 1.55)) {
                    b.lathe(cx, 0.806, 0.5, floatArrayOf(0f, 0f, 0.15f, 0f, 0.16f, 0.015f, 0.0f, 0.015f), C("#F4F1EA"), true, 24)
                    b.lathe(cx, 0.82, 0.5, floatArrayOf(0f, 0f, 0.1f, 0f, 0.11f, 0.01f, 0.0f, 0.01f), C("#E8E4DA"), true, 24)
                    b.lathe(cx + 0.28, 0.806, 0.56, floatArrayOf(0f, 0f, 0.04f, 0f, 0.05f, 0.09f, 0.045f, 0.09f, 0f, 0.075f), C("#FFFFFF"), true, 14)
                }
            }
            Type.BED -> {
                val wd = C("#7A5236")
                b.m(Mt.WOOD)
                b.rbox(0.5, 0.2, 1.0, 0.96, 0.2, 1.94, 0.03, wd)
                for (lx in listOf(0.08, 0.92)) for (lz in listOf(0.1, 1.9)) leg(b, lx, lz, 0.12, 0.03, 0.035, C("#4E342E"))
                b.rbox(0.5, 0.68, 0.05, 0.98, 0.86, 0.09, 0.035, wd, true, 3)
                b.rbox(0.5, 0.40, 1.97, 0.96, 0.36, 0.06, 0.03, wd)
                b.m(Mt.FABRIC, 1.5f)
                b.rbox(0.5, 0.4, 1.04, 0.88, 0.17, 1.8, 0.07, C("#F2F0EA"), true, 3)
                b.rbox(0.5, 0.49, 1.5, 0.93, 0.07, 1.1, 0.04, C("#5C7DBA"), true, 3)
                b.rbox(0.5, 0.52, 0.93, 0.94, 0.11, 0.2, 0.05, C("#8AA5D6"), true, 3)
                b.rbox(0.5, 0.67, 0.14, 0.82, 0.55, 0.06, 0.04, C("#8B8F9C"), true, 3)
                b.rbox(0.27, 0.56, 0.35, 0.38, 0.12, 0.3, 0.06, C("#FFFFFF"), true, 3)
                b.rbox(0.73, 0.56, 0.35, 0.38, 0.12, 0.3, 0.06, C("#F6F3EC"), true, 3)
            }
            Type.SOFA -> {
                val d = C("#3A8A88"); val mm = C("#46A09C"); val l = C("#58B5B0")
                b.m(Mt.WOOD)
                for (lx in listOf(0.12, 1.88)) for (lz in listOf(0.14, 0.86)) leg(b, lx, lz, 0.1, 0.025, 0.035, C("#6B4630"))
                b.m(Mt.FABRIC, 1.4f)
                b.rbox(1.0, 0.25, 0.5, 1.92, 0.28, 0.88, 0.07, d, true, 3)
                b.rbox(1.0, 0.7, 0.14, 1.92, 0.62, 0.26, 0.09, d, true, 3)
                b.rbox(0.1, 0.5, 0.5, 0.22, 0.46, 0.88, 0.09, d, true, 3)
                b.rbox(1.9, 0.5, 0.5, 0.22, 0.46, 0.88, 0.09, d, true, 3)
                b.rbox(0.62, 0.46, 0.6, 0.76, 0.15, 0.66, 0.07, mm, true, 3)
                b.rbox(1.38, 0.46, 0.6, 0.76, 0.15, 0.66, 0.07, mm, true, 3)
                b.rbox(0.62, 0.74, 0.3, 0.74, 0.42, 0.2, 0.09, l, true, 3)
                b.rbox(1.38, 0.74, 0.3, 0.74, 0.42, 0.2, 0.09, l, true, 3)
                b.rbox(0.42, 0.7, 0.55, 0.3, 0.28, 0.1, 0.05, C("#F0A04B"))
                b.rbox(1.62, 0.7, 0.55, 0.3, 0.28, 0.1, 0.05, C("#F4EBD8"))
            }
            Type.SHELF -> {
                val wd = C("#9B6B45")
                b.m(Mt.WOOD)
                b.rbox(0.04, 0.95, 0.2, 0.07, 1.9, 0.4, 0.012, wd, true, 1)
                b.rbox(1.96, 0.95, 0.2, 0.07, 1.9, 0.4, 0.012, wd, true, 1)
                b.rbox(1.0, 1.88, 0.2, 2.0, 0.06, 0.42, 0.015, wd, true, 1)
                b.rbox(1.0, 0.05, 0.2, 1.9, 0.1, 0.4, 0.012, wd, true, 1)
                b.box(1.0, 0.95, 0.02, 1.9, 1.8, 0.03, C("#6E4630"))
                for (y in listOf(0.46, 0.9, 1.36)) b.rbox(1.0, y, 0.2, 1.9, 0.04, 0.38, 0.01, wd, true, 1)
                b.m(Mt.PLAIN)
                val cols = listOf("#C8553D", "#E3A72F", "#4F8F5A", "#2F6FA8", "#7B4F9B", "#E8873A", "#2F9AA6", "#F0E6D2")
                val bases = listOf(0.1, 0.48, 0.92, 1.38)
                for (j in 0 until 4) {
                    var x = 0.12
                    var k = j * 3
                    val lim = if (j == 2) 1.1 else if (j == 3) 1.0 else 1.82
                    while (x < lim) {
                        val hh = 0.28 + ((k * 7) % 4) * 0.045
                        val ww = 0.06 + ((k * 3) % 3) * 0.018
                        b.box(x + ww / 2, bases[j] + 0.02 + hh / 2, 0.21, ww, hh, 0.27, C(cols[k % cols.size]))
                        x += ww + 0.008
                        k++
                    }
                }
                b.lathe(1.55, 0.92, 0.2, floatArrayOf(0f, 0f, 0.08f, 0f, 0.1f, 0.14f, 0.0f, 0.14f), C("#C1663A"), true, 16)
                b.m(Mt.GRASS, 2f)
                b.sphere(1.55, 1.2, 0.2, 0.15, C("#4C9A3C"), 0.13, 8)
                b.sphere(1.46, 1.12, 0.22, 0.1, C("#5CB04A"), 0.09, 7)
                b.m(Mt.WOOD)
                b.rbox(1.5, 1.52, 0.22, 0.26, 0.3, 0.025, 0.01, C("#3B2A20"), true, 1)
                b.m(Mt.PLAIN)
                b.box(1.5, 1.52, 0.236, 0.2, 0.24, 0.005, C("#BFD9EA"), false)
                b.box(1.5, 1.46, 0.24, 0.2, 0.1, 0.005, C("#6FA66A"), false)
            }
            Type.PLANT -> {
                b.m(Mt.PLAIN)
                b.lathe(0.5, 0.0, 0.5, floatArrayOf(0f, 0f, 0.13f, 0f, 0.20f, 0.32f, 0.23f, 0.34f, 0.23f, 0.41f, 0.2f, 0.41f, 0.19f, 0.37f, 0f, 0.37f), C("#C9703F"), true, 24)
                b.tube(0.5, 0.366, 0.5, 0.19, 0.01, C("#3A2A20"))
                b.m(Mt.WOOD)
                b.cyl(0.5, 0.37, 0.5, 0.03, 0.018, 0.55, C("#6B4A32"), true, 8)
                b.m(Mt.GRASS, 1.5f)
                val g1 = C("#2F7F3A"); val g2 = C("#4FA04A"); val g3 = C("#6CBE5C")
                b.sphere(0.5, 1.0, 0.5, 0.26, g1, 0.2, 9)
                b.sphere(0.34, 0.86, 0.52, 0.18, g2, 0.14, 8)
                b.sphere(0.68, 0.92, 0.45, 0.2, g1, 0.15, 8)
                b.sphere(0.52, 1.24, 0.46, 0.2, g3, 0.15, 8)
                b.sphere(0.4, 1.12, 0.66, 0.16, g2, 0.12, 8)
                b.sphere(0.62, 1.1, 0.64, 0.15, g3, 0.12, 8)
                b.sphere(0.36, 1.2, 0.38, 0.14, g3, 0.11, 8)
                b.sphere(0.7, 1.22, 0.36, 0.13, g2, 0.1, 8)
                b.sphere(0.5, 0.78, 0.7, 0.13, g1, 0.1, 8)
                b.sphere(0.3, 0.98, 0.3, 0.12, g2, 0.1, 8)
            }
            Type.RUG -> {
                b.m(Mt.RUG, 1f / 1.9f, -0.05f / 1.9f, -0.05f / 1.9f)
                b.rbox(1.0, 0.017, 1.0, 1.9, 0.034, 1.9, 0.016, C("#FFFFFF"), true, 1)
            }
            Type.TV -> {
                b.m(Mt.WOOD)
                val dk = C("#5A4030")
                b.rbox(1.0, 0.31, 0.5, 1.9, 0.34, 0.6, 0.025, C("#7B5638"), true, 2)
                for (lx in listOf(0.14, 1.86)) for (lz in listOf(0.15, 0.85)) leg(b, lx, lz, 0.14, 0.02, 0.03, dk)
                b.rbox(0.5, 0.3, 0.805, 0.86, 0.26, 0.02, 0.01, dk, true, 1)
                b.rbox(1.5, 0.3, 0.805, 0.86, 0.26, 0.02, 0.01, dk, true, 1)
                b.m(Mt.METAL)
                b.rbox(0.5, 0.38, 0.825, 0.2, 0.02, 0.015, 0.007, C("#C9CED4"), true, 1)
                b.rbox(1.5, 0.38, 0.825, 0.2, 0.02, 0.015, 0.007, C("#C9CED4"), true, 1)
                b.rbox(1.0, 0.495, 0.5, 0.5, 0.03, 0.2, 0.012, C("#22262B"), true, 1)
                b.rbox(1.0, 0.92, 0.5, 1.5, 0.8, 0.04, 0.018, C("#15181C"), true, 2)
                b.m(Mt.PLAIN)
                b.gradQuadZ(0.3, 1.7, 0.56, 1.28, 0.522, C("#14284F"), C("#3C86E0"))
                b.gradQuadZ(0.3, 1.7, 0.56, 0.75, 0.523, C("#1F5E3A"), C("#3F8F52"))
                b.gradQuadZ(0.62, 0.86, 0.75, 0.9, 0.523, C("#2B6E44"), C("#2B6E44"))
                b.gradQuadZ(1.15, 1.45, 1.05, 1.1, 0.523, C("#DCEBFF"), C("#DCEBFF"))
            }
            Type.FRIDGE -> {
                b.m(Mt.METAL)
                val body = C("#E8ECF0")
                b.rbox(0.5, 0.95, 0.46, 0.88, 1.9, 0.76, 0.03, body, true, 2)
                b.rbox(0.5, 1.27, 0.865, 0.85, 1.22, 0.03, 0.02, C("#F1F4F7"), true, 2)
                b.rbox(0.5, 0.34, 0.865, 0.85, 0.56, 0.03, 0.02, C("#F1F4F7"), true, 2)
                b.cyl(0.78, 1.0, 0.92, 0.016, 0.016, 0.55, C("#9AA5AE"), true, 10)
                b.cyl(0.78, 0.3, 0.92, 0.016, 0.016, 0.22, C("#9AA5AE"), true, 10)
                b.m(Mt.PLAIN)
                b.rbox(0.28, 1.62, 0.885, 0.1, 0.1, 0.012, 0.01, C("#F2635A"), true, 1)
                b.rbox(0.4, 1.5, 0.885, 0.09, 0.12, 0.012, 0.01, C("#F4C84B"), true, 1)
                b.box(0.3, 1.46, 0.884, 0.14, 0.2, 0.004, C("#FFFFFF"))
            }
            Type.STOVE -> {
                b.m(Mt.METAL)
                b.rbox(0.5, 0.43, 0.47, 0.9, 0.86, 0.8, 0.03, C("#E4E7EA"), true, 2)
                b.rbox(0.5, 0.88, 0.47, 0.92, 0.03, 0.82, 0.015, C("#1F2429"), true, 1)
                b.rbox(0.5, 0.4, 0.875, 0.78, 0.52, 0.03, 0.02, C("#D5D9DD"), true, 2)
                b.rbox(0.5, 0.42, 0.895, 0.58, 0.3, 0.01, 0.012, C("#121519"), true, 1)
                b.rbox(0.5, 0.7, 0.915, 0.64, 0.03, 0.03, 0.015, C("#B6BEC6"), true, 1)
                b.rbox(0.5, 0.82, 0.875, 0.8, 0.1, 0.03, 0.015, C("#B9C0C7"), true, 1)
                b.rbox(0.5, 1.08, 0.07, 0.9, 0.36, 0.06, 0.02, C("#CDD2D8"), true, 1)
                b.m(Mt.PLAIN)
                for (bx in listOf(0.28, 0.72)) for (bz in listOf(0.32, 0.64)) {
                    b.tube(bx, 0.895, bz, 0.12, 0.012, C("#3B4249"))
                    b.tube(bx, 0.905, bz, 0.05, 0.01, C("#E0583F"))
                }
                for (kx in listOf(0.2, 0.37, 0.63, 0.8)) b.rbox(kx, 0.82, 0.905, 0.05, 0.05, 0.03, 0.02, C("#2B3036"), true, 1)
                b.box(0.5, 1.12, 0.103, 0.18, 0.06, 0.004, C("#58E08E"), false)
            }
            Type.LAMP -> {
                b.m(Mt.METAL)
                b.lathe(0.5, 0.0, 0.5, floatArrayOf(0f, 0f, 0.2f, 0f, 0.2f, 0.02f, 0.15f, 0.045f, 0f, 0.05f), C("#3A424A"), true, 24)
                b.cyl(0.5, 0.05, 0.5, 0.018, 0.018, 1.2, C("#9AA5AE"), true, 10)
                b.m(Mt.PLAIN)
                b.lathe(0.5, 1.18, 0.5, floatArrayOf(0.26f, 0f, 0.18f, 0.4f), C("#FFE7A6"), false, 28)
                b.sphere(0.5, 1.3, 0.5, 0.07, C("#FFF8DD"), 0.07, 7, false)
            }
            Type.NIGHT -> {
                val wd = C("#B98A5C")
                b.m(Mt.WOOD)
                for (lx in listOf(0.27, 0.73)) for (lz in listOf(0.3, 0.7)) leg(b, lx, lz, 0.14, 0.02, 0.028, wd)
                b.rbox(0.5, 0.36, 0.5, 0.54, 0.44, 0.44, 0.025, wd, true, 2)
                b.rbox(0.5, 0.6, 0.5, 0.6, 0.04, 0.5, 0.02, wd, true, 2)
                b.rbox(0.5, 0.43, 0.725, 0.46, 0.17, 0.02, 0.01, C("#A57647"), true, 1)
                b.rbox(0.5, 0.24, 0.725, 0.46, 0.17, 0.02, 0.01, C("#A57647"), true, 1)
                b.m(Mt.METAL)
                b.sphere(0.5, 0.43, 0.745, 0.022, C("#B8C0C8"), 0.022, 6)
                b.sphere(0.5, 0.24, 0.745, 0.022, C("#B8C0C8"), 0.022, 6)
                b.m(Mt.PLAIN)
                b.lathe(0.36, 0.62, 0.48, floatArrayOf(0f, 0f, 0.07f, 0f, 0.05f, 0.02f, 0.015f, 0.05f, 0.015f, 0.22f, 0f, 0.22f), C("#F4F1EA"), true, 16)
                b.lathe(0.36, 0.78, 0.48, floatArrayOf(0.12f, 0f, 0.075f, 0.17f), C("#FFE7A6"), false, 18)
                b.box(0.68, 0.635, 0.5, 0.22, 0.03, 0.15, C("#2F6FA8"))
                b.box(0.68, 0.665, 0.5, 0.2, 0.03, 0.14, C("#E3A72F"))
            }
            Type.COFFEE -> {
                val wd = C("#C99259"); val dk = C("#6E4630")
                b.m(Mt.WOOD)
                b.rbox(1.0, 0.41, 0.5, 1.4, 0.05, 0.7, 0.03, wd, true, 3)
                b.rbox(1.0, 0.17, 0.5, 1.2, 0.025, 0.5, 0.012, dk, true, 1)
                for (lx in listOf(0.42, 1.58)) for (lz in listOf(0.22, 0.78)) leg(b, lx, lz, 0.39, 0.02, 0.03, dk)
                b.m(Mt.PLAIN)
                b.rbox(0.72, 0.447, 0.5, 0.32, 0.03, 0.23, 0.005, C("#2F5D8A"), true, 1)
                b.rbox(0.72, 0.478, 0.5, 0.27, 0.03, 0.2, 0.005, C("#C9A227"), true, 1)
                b.lathe(1.25, 0.435, 0.45, floatArrayOf(0f, 0f, 0.055f, 0f, 0.065f, 0.09f, 0.058f, 0.09f, 0f, 0.075f), C("#FFFFFF"), true, 16)
                b.lathe(1.25, 0.435, 0.45, floatArrayOf(0.2f, 0f, 0.2f, 0.01f, 0f, 0.012f), C("#F4F1EA"), true, 18)
                b.lathe(1.0, 0.435, 0.58, floatArrayOf(0f, 0f, 0.06f, 0f, 0.075f, 0.12f, 0.05f, 0.18f, 0.0f, 0.18f), C("#E8A04B"), true, 16)
            }
            Type.WARDROBE -> {
                val wd = C("#D5B48A")
                b.m(Mt.WOOD)
                b.rbox(1.0, 0.045, 0.38, 1.88, 0.09, 0.68, 0.012, C("#6E4630"), true, 1)
                b.rbox(1.0, 1.06, 0.37, 1.92, 1.95, 0.72, 0.02, wd, true, 2)
                b.rbox(1.0, 2.07, 0.38, 2.0, 0.06, 0.78, 0.02, C("#C2A074"), true, 1)
                b.rbox(0.5, 1.06, 0.74, 0.92, 1.85, 0.03, 0.015, C("#DEC196"), true, 1)
                b.rbox(1.5, 1.06, 0.74, 0.92, 1.85, 0.03, 0.015, C("#DEC196"), true, 1)
                for (cx in listOf(0.5, 1.5)) {
                    b.rbox(cx, 1.55, 0.76, 0.7, 0.75, 0.012, 0.01, C("#E6CDA6"), true, 1)
                    b.rbox(cx, 0.55, 0.76, 0.7, 0.55, 0.012, 0.01, C("#E6CDA6"), true, 1)
                }
                b.m(Mt.METAL)
                b.rbox(0.9, 1.05, 0.78, 0.03, 0.42, 0.03, 0.015, C("#B8C0C8"), true, 1)
                b.rbox(1.1, 1.05, 0.78, 0.03, 0.42, 0.03, 0.015, C("#B8C0C8"), true, 1)
            }
            else -> {}
        }
        return b.toMesh(true)
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
                fl.place("door_110", o.c, 0.0, 0.0)
                b.m(Mt.METAL)
                b.rbox(o.c + ww / 2 + 0.45, 1.75, -0.2, 0.08, 0.14, 0.06, 0.02, C("#2B3036"), true, 1)
                b.m(Mt.PLAIN)
                b.sphere(o.c + ww / 2 + 0.45, 1.75, -0.24, 0.06, C("#FFE9A8"), 0.07, 7, false)
            } else {
                val wn = Math.round(ww * 100).toInt()
                val id = if (wn >= 175) "190" else if (wn >= 140) "160" else "125"
                fl.place("win_$id", o.c, 0.0, 0.0)
                val cc = if (o.c < len / 2) C("#D9786B") else C("#E4B25F")
                fl.place("curt_$id", o.c, 0.0, 0.0, 1.0, 0.0,
                    Math.min(1.25f, android.graphics.Color.red(cc) / 255f * 1.15f), Math.min(1.25f, android.graphics.Color.green(cc) / 255f * 1.15f), Math.min(1.25f, android.graphics.Color.blue(cc) / 255f * 1.15f))
            }
        }

        // lambri (Etapa 68): módulos de 1 m, menos na porta
        for (i in 0 until Math.floor(len).toInt()) {
            val x0m = i.toDouble(); val x1m = i + 1.0
            var skip = false
            for (o in sorted) if (o.door && x1m > o.c - o.w / 2 - 0.02 && x0m < o.c + o.w / 2 + 0.02) skip = true
            if (!skip) fl.place("wain_1", x0m, 0.0, 0.0)
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
        // laje do telhado: fascia clara + telhas por cima (Etapa 69)
        b.m(Mt.PLASTER, 0.5f)
        b.rbox(W / 2, HH + 0.11, H / 2, W + 0.7, 0.2, H + 0.7, 0.04, C("#F3EEE4"), true, 2)
        b.m(Mt.ROOF, 0.55f)
        b.rbox(W / 2, HH + 0.245, H / 2, W + 0.5, 0.07, H + 0.5, 0.025, C("#FFFFFF"), true, 2)
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

    fun yard(gw: Int, gh: Int): Mesh {
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

        // vasos na varanda
        for (sx in intArrayOf(-1, 1)) {
            val px = W / 2 + sx * 1.15
            b.m(Mt.PLAIN)
            b.lathe(px, 0.09, H + 1.2, floatArrayOf(0f, 0f, 0.13f, 0f, 0.2f, 0.32f, 0.23f, 0.34f, 0.23f, 0.41f, 0.2f, 0.41f, 0.19f, 0.37f, 0f, 0.37f), C("#C9703F"), true, 20)
            fl.place("bush_b", px, 0.44, H + 1.2, 0.5, px * 7.0)
        }

        // postes de luz do jardim (modelados, Etapa 69)
        for (sx in intArrayOf(-1, 1)) for (zz in listOf(H + 3.5, H + 6.5)) fl.place("lamp_post", W / 2 + sx * 1.1, 0.0, zz, 0.8, 0.0)

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

        // tufos de grama espalhados pelo quintal (fora da casa e do caminho)
        run {
            val rnd = java.util.Random(7)
            var k = 0
            var tries = 0
            while (k < 360 && tries < 4000) {
                tries++
                val gx = x0 + 1.0 + rnd.nextDouble() * (x1 - x0 - 2.0)
                val gz = z0 + 1.0 + rnd.nextDouble() * (z1 - z0 - 2.0)
                if (gx > -0.9 && gx < W + 0.9 && gz > -1.4 && gz < H + 0.9) continue
                if (Math.abs(gx - W / 2) < 1.5 && gz > H) continue
                fl.place(if (k % 3 == 0) "grass_b" else "grass_a", gx, 0.0, gz, 0.38 + rnd.nextDouble() * 0.3, rnd.nextDouble() * 6.28)
                k++
            }
        }

        // banco e caixa de correio modelados (Etapa 69)
        fl.place("bench", W + 2.6, 0.0, H + 2.4, 1.0, -Math.PI / 2)
        fl.place("mailbox", W / 2 + 1.5, 0.0, H + 8.5, 1.0, Math.PI / 2)

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
                fl.place("gate_lantern", px, 1.47, z1)
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
