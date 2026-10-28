package com.vinicius.meular

object Models {

    fun shadow(w: Int, h: Int): Mesh {
        val b = MB()
        b.blob(w / 2.0, 0.07, h / 2.0, w / 2.0 + 0.3, h / 2.0 + 0.3, 0.38f)
        return b.toMesh()
    }

    fun ring(w: Int, h: Int): Mesh {
        val b = MB()
        val c = C("#FFEB3B")
        val t = 0.07
        b.box(w / 2.0, 0.09, -0.02, w + 0.1, 0.02, t, c, false)
        b.box(w / 2.0, 0.09, h + 0.02, w + 0.1, 0.02, t, c, false)
        b.box(-0.02, 0.09, h / 2.0, t, 0.02, h + 0.1, c, false)
        b.box(w + 0.02, 0.09, h / 2.0, t, 0.02, h + 0.1, c, false)
        return b.toMesh()
    }

    fun furniture(t: Type): Mesh {
        val b = MB()
        when (t) {
            Type.CHAIR -> {
                val wood = C("#8D5A3B"); val cu = C("#E57373")
                for (lx in listOf(0.15, 0.85)) for (lz in listOf(0.15, 0.85)) b.box(lx, 0.22, lz, 0.08, 0.44, 0.08, wood)
                b.box(0.5, 0.47, 0.5, 0.78, 0.07, 0.78, wood)
                b.box(0.5, 0.54, 0.53, 0.66, 0.07, 0.62, cu)
                b.box(0.16, 0.78, 0.13, 0.07, 0.64, 0.07, wood)
                b.box(0.84, 0.78, 0.13, 0.07, 0.64, 0.07, wood)
                b.box(0.5, 0.92, 0.13, 0.78, 0.2, 0.06, wood)
                b.box(0.5, 0.7, 0.13, 0.6, 0.06, 0.04, wood)
            }
            Type.TABLE -> {
                val wood = C("#C68B59"); val dk = C("#8D5A3B")
                b.box(1.0, 0.74, 0.5, 1.9, 0.08, 0.9, wood)
                b.box(1.0, 0.67, 0.5, 1.7, 0.06, 0.7, dk)
                for (lx in listOf(0.14, 1.86)) for (lz in listOf(0.14, 0.86)) b.box(lx, 0.35, lz, 0.09, 0.7, 0.09, dk)
                b.tube(1.0, 0.78, 0.5, 0.08, 0.22, C("#4FC3F7"))
                b.sphere(1.0, 1.08, 0.5, 0.11, C("#F06292"))
                b.sphere(0.92, 1.02, 0.54, 0.08, C("#FFD54F"))
                b.sphere(1.08, 1.03, 0.45, 0.08, C("#81C784"))
                b.tube(1.55, 0.78, 0.5, 0.18, 0.02, C("#ECEFF1"))
                b.tube(0.5, 0.78, 0.45, 0.12, 0.02, C("#ECEFF1"))
            }
            Type.BED -> {
                val wood = C("#6D4C41")
                b.box(0.5, 0.17, 1.0, 0.98, 0.24, 1.96, wood)
                b.box(0.5, 0.62, 0.05, 1.0, 0.95, 0.09, C("#4E342E"))
                b.box(0.5, 0.38, 1.05, 0.88, 0.2, 1.8, C("#ECEFF1"))
                b.box(0.5, 0.51, 1.42, 0.92, 0.07, 1.2, C("#5C6BC0"))
                b.box(0.5, 0.52, 0.84, 0.93, 0.07, 0.12, C("#7986CB"))
                b.box(0.28, 0.55, 0.34, 0.38, 0.13, 0.3, C("#FAFAFA"))
                b.box(0.72, 0.55, 0.34, 0.38, 0.13, 0.3, C("#FAFAFA"))
                b.box(0.06, 0.4, 1.94, 0.1, 0.5, 0.1, wood)
                b.box(0.94, 0.4, 1.94, 0.1, 0.5, 0.1, wood)
            }
            Type.SOFA -> {
                val d = C("#00897B"); val m = C("#26A69A"); val l = C("#4DB6AC")
                b.box(1.0, 0.22, 0.5, 1.9, 0.3, 0.92, d)
                b.box(0.57, 0.47, 0.6, 0.8, 0.16, 0.7, m)
                b.box(1.43, 0.47, 0.6, 0.8, 0.16, 0.7, m)
                b.box(1.0, 0.68, 0.13, 1.9, 0.6, 0.26, C("#00796B"))
                b.box(0.57, 0.72, 0.3, 0.78, 0.42, 0.18, l)
                b.box(1.43, 0.72, 0.3, 0.78, 0.42, 0.18, l)
                b.box(0.11, 0.52, 0.5, 0.22, 0.5, 0.92, d)
                b.box(1.89, 0.52, 0.5, 0.22, 0.5, 0.92, d)
                b.box(0.4, 0.66, 0.6, 0.3, 0.28, 0.1, C("#FFB74D"))
                for (lx in listOf(0.1, 1.9)) for (lz in listOf(0.1, 0.9)) b.box(lx, 0.04, lz, 0.08, 0.08, 0.08, C("#3E2723"))
            }
            Type.SHELF -> {
                val w = C("#5D4037")
                b.box(0.04, 0.95, 0.2, 0.07, 1.9, 0.38, w)
                b.box(1.96, 0.95, 0.2, 0.07, 1.9, 0.38, w)
                b.box(1.0, 1.9, 0.2, 2.0, 0.06, 0.4, w)
                b.box(1.0, 0.05, 0.2, 1.9, 0.1, 0.38, w)
                b.box(1.0, 0.95, 0.02, 1.9, 1.8, 0.04, C("#4E342E"))
                for (y in listOf(0.45, 0.9, 1.35)) b.box(1.0, y, 0.2, 1.9, 0.04, 0.36, C("#6D4C41"))
                val cols = listOf("#E53935", "#FDD835", "#43A047", "#1E88E5", "#8E24AA", "#FB8C00", "#00ACC1")
                val bases = listOf(0.1, 0.47, 0.92, 1.37)
                for (j in 0 until 4) {
                    var x = 0.12
                    var k = j * 3
                    while (x < 1.82) {
                        val hh = 0.28 + ((k * 7) % 4) * 0.04
                        val ww = 0.07 + ((k * 3) % 3) * 0.015
                        b.box(x + ww / 2, bases[j] + 0.02 + hh / 2, 0.2, ww, hh, 0.26, C(cols[k % cols.size]))
                        x += ww + 0.01
                        k++
                    }
                }
            }
            Type.PLANT -> {
                b.cyl(0.5, 0.0, 0.5, 0.17, 0.22, 0.38, C("#C1663A"))
                b.tube(0.5, 0.38, 0.5, 0.19, 0.02, C("#3E2723"))
                b.tube(0.5, 0.38, 0.5, 0.03, 0.55, C("#6D4C41"))
                b.sphere(0.5, 0.95, 0.5, 0.3, C("#2E7D32"), 0.26)
                b.sphere(0.34, 0.8, 0.52, 0.2, C("#43A047"))
                b.sphere(0.66, 0.85, 0.45, 0.22, C("#388E3C"))
                b.sphere(0.5, 1.2, 0.5, 0.2, C("#66BB6A"))
                b.sphere(0.45, 0.8, 0.68, 0.17, C("#4CAF50"))
            }
            Type.RUG -> {
                b.box(1.0, 0.015, 1.0, 1.9, 0.03, 1.9, C("#B71C1C"))
                b.box(1.0, 0.032, 1.0, 1.6, 0.03, 1.6, C("#FFE0B2"))
                b.box(1.0, 0.048, 1.0, 1.3, 0.03, 1.3, C("#E57373"))
                b.tube(1.0, 0.05, 1.0, 0.35, 0.015, C("#B71C1C"), true)
            }
            Type.TV -> {
                b.box(1.0, 0.22, 0.5, 1.9, 0.44, 0.7, C("#5D4037"))
                b.box(0.5, 0.22, 0.86, 0.85, 0.3, 0.02, C("#4E342E"))
                b.box(1.5, 0.22, 0.86, 0.85, 0.3, 0.02, C("#4E342E"))
                b.box(1.0, 0.47, 0.5, 0.5, 0.04, 0.25, C("#212121"))
                b.box(1.0, 0.95, 0.5, 1.5, 0.85, 0.07, C("#111111"))
                b.box(1.0, 0.95, 0.545, 1.4, 0.75, 0.02, C("#4FC3F7"), false)
                b.box(0.78, 1.08, 0.556, 0.5, 0.25, 0.01, C("#B3E5FC"), false)
            }
            Type.FRIDGE -> {
                b.box(0.5, 0.92, 0.5, 0.88, 1.84, 0.84, C("#ECEFF1"))
                b.box(0.5, 1.86, 0.5, 0.9, 0.04, 0.86, C("#CFD8DC"))
                b.box(0.5, 1.28, 0.925, 0.88, 0.03, 0.02, C("#90A4AE"))
                b.box(0.8, 1.5, 0.95, 0.05, 0.35, 0.05, C("#607D8B"))
                b.box(0.8, 0.95, 0.95, 0.05, 0.5, 0.05, C("#607D8B"))
                b.box(0.3, 1.5, 0.93, 0.1, 0.1, 0.01, C("#FF7043"))
            }
            Type.STOVE -> {
                b.box(0.5, 0.45, 0.5, 0.9, 0.9, 0.84, C("#CFD8DC"))
                b.box(0.5, 0.92, 0.5, 0.92, 0.04, 0.86, C("#263238"))
                b.box(0.5, 1.15, 0.06, 0.9, 0.5, 0.06, C("#B0BEC5"))
                for (bx in listOf(0.3, 0.7)) for (bz in listOf(0.35, 0.68)) {
                    b.tube(bx, 0.94, bz, 0.13, 0.015, C("#455A64"))
                    b.tube(bx, 0.955, bz, 0.05, 0.01, C("#FF5252"))
                }
                b.box(0.5, 0.4, 0.93, 0.76, 0.5, 0.03, C("#37474F"))
                b.box(0.5, 0.42, 0.95, 0.55, 0.3, 0.01, C("#111111"))
                b.box(0.5, 0.68, 0.97, 0.6, 0.04, 0.04, C("#B0BEC5"))
            }
            Type.LAMP -> {
                b.cyl(0.5, 0.0, 0.5, 0.22, 0.2, 0.05, C("#37474F"))
                b.tube(0.5, 0.05, 0.5, 0.025, 1.3, C("#78909C"))
                b.cyl(0.5, 1.22, 0.5, 0.27, 0.16, 0.36, C("#FFF3C4"), false, 20)
            }
        }
        return b.toMesh()
    }

    private fun tree(b: MB, x: Double, z: Double, s: Double) {
        b.tube(x, -0.4, z, 0.14 * s, 1.1 * s, C("#6D4C41"))
        b.sphere(x, 1.1 * s, z, 0.9 * s, C("#43A047"))
        b.sphere(x + 0.3 * s, 1.6 * s, z - 0.2 * s, 0.6 * s, C("#66BB6A"))
    }

    fun floor(gw: Int, gh: Int): Mesh {
        val b = MB()
        b.box(gw / 2.0, -0.2, gh / 2.0, gw + 0.5, 0.4, gh + 0.5, C("#5B4A63"))
        b.box(gw / 2.0, -0.45, gh / 2.0, gw + 40.0, 0.1, gh + 40.0, C("#6FA36B"))
        val base = intArrayOf(C("#C9965F"), C("#BB8553"))
        for (z in 0 until gh) for (x in 0 until gw) for (k in 0 until 4) {
            val hv = (x * 31 + z * 17 + k * 13) % 7
            val col = shade(base[(x + z) % 2], (hv - 3) * 3)
            if ((x + z) % 2 == 0) b.box(x + 0.5, -0.01, z + k * 0.25 + 0.125, 0.99, 0.02, 0.235, col)
            else b.box(x + k * 0.25 + 0.125, -0.01, z + 0.5, 0.235, 0.02, 0.99, col)
        }
        tree(b, -2.4, -2.2, 1.0)
        tree(b, gw + 2.6, gh * 0.25, 1.2)
        tree(b, -2.0, gh + 2.2, 0.9)
        tree(b, gw + 1.8, gh + 2.6, 1.1)
        return b.toMesh()
    }

    fun wall(len: Double, window: Boolean, ext: Boolean): Mesh {
        val b = MB()
        val t = 0.16
        val hh = 2.5
        val wc = C("#F1DCCB")
        val white = C("#FAF6EF")
        val xs = if (ext) -t else 0.0
        val xe = if (ext) len + t else len
        fun seg(x0: Double, x1: Double, y0: Double, y1: Double) =
            b.box((x0 + x1) / 2, (y0 + y1) / 2, -t / 2, x1 - x0, y1 - y0, t, wc)
        if (window) {
            val c = len / 2
            val w0 = c - 0.95
            val w1 = c + 0.95
            seg(xs, w0, 0.0, hh); seg(w1, xe, 0.0, hh); seg(w0, w1, 0.0, 0.95); seg(w0, w1, 1.95, hh)
            b.box(c, 1.45, -t / 2, 1.9, 1.0, 0.02, C("#BFE9FF"), false)
            b.box(c - 0.95, 1.45, -t / 2, 0.08, 1.1, 0.12, white)
            b.box(c + 0.95, 1.45, -t / 2, 0.08, 1.1, 0.12, white)
            b.box(c, 1.95, -t / 2, 2.0, 0.08, 0.12, white)
            b.box(c, 0.95, 0.04, 2.1, 0.06, 0.26, white)
            b.box(c, 1.45, -t / 2, 0.05, 1.0, 0.06, white)
            b.box(c, 1.45, -t / 2, 1.9, 0.05, 0.06, white)
            b.box(c - 1.05, 1.5, 0.1, 0.3, 1.35, 0.08, C("#E57373"))
            b.box(c + 1.05, 1.5, 0.1, 0.3, 1.35, 0.08, C("#E57373"))
            b.box(c, 2.2, 0.1, 2.6, 0.04, 0.04, C("#5D4037"))
            b.box(0.85, 1.5, 0.03, 0.6, 0.45, 0.04, C("#5D4037"))
            b.box(0.85, 1.5, 0.055, 0.5, 0.35, 0.01, C("#81C784"))
            b.box(0.85, 1.43, 0.065, 0.3, 0.12, 0.01, C("#A5D6A7"))
        } else {
            seg(xs, xe, 0.0, hh)
        }
        b.box((xs + xe) / 2, 0.09, 0.03, xe - xs, 0.18, 0.06, white)
        b.box((xs + xe) / 2, hh + 0.03, -t / 2, xe - xs, 0.06, t + 0.04, C("#8D6E63"))
        return b.toMesh()
    }
}
