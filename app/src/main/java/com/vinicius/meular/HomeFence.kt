package com.vinicius.meular

/** Etapa 160: cerca do terreno da casa do jogador. */
object HomeFence {
    fun build(b: MB, W: Double, x0: Double, x1: Double, z0: Double, z1: Double) {
            val gx0 = W / 2 - 1.25; val gx1 = W / 2 + 1.25
            fenceRun(b, x0, z0, x1, z0)
            fenceRun(b, x0, z0, x0, z1)
            fenceRun(b, x1, z0, x1, z1)
            fenceRun(b, x0, z1, gx0 - 0.25, z1)
            fenceRun(b, gx1 + 0.25, z1, x1, z1)
            // pilares do portão
            for (gx in doubleArrayOf(gx0 - 0.25, gx1 + 0.25)) {
                b.m(Mt.PLASTER, 0.6f); b.box(gx, 1.15, z1, 0.5, 2.3, 0.5, C("#EDE6D8"))
                b.m(Mt.STONE, 0.8f); b.box(gx, 0.25, z1, 0.6, 0.5, 0.6, C("#B9B2A5")); b.box(gx, 2.34, z1, 0.64, 0.08, 0.64, C("#CFC8BA"))
                b.m(Mt.PLAIN); b.box(gx, 2.52, z1, 0.3, 0.28, 0.3, C("#FFF3C8"), false); b.box(gx, 2.7, z1, 0.4, 0.07, 0.4, C("#2B2E31")); b.box(gx, 2.38, z1, 0.34, 0.06, 0.34, C("#2B2E31"))
                    }
            // viga de ferro sobre o portão e placa
            b.m(Mt.METAL, 1f); b.box(W / 2, 2.3, z1, gx1 - gx0 + 0.5, 0.07, 0.07, C("#26292D"))
            b.box(W / 2, 2.12, z1, gx1 - gx0 + 0.3, 0.04, 0.04, C("#26292D"))
    }

    /** Etapa 160: trecho de cerca reto (ao longo de x ou de z): mureta, tampa, pilares a cada ~3 m e grade de ferro. */
    private fun fenceRun(b: MB, xa: Double, za: Double, xb: Double, zb: Double) {
        val alongX = Math.abs(xb - xa) >= Math.abs(zb - za)
        val len = if (alongX) xb - xa else zb - za
        if (len < 0.4) return
        val n = Math.max(1, Math.ceil(len / 3.0).toInt()); val st = len / n
        fun at(t: Double, off: Double = 0.0) = if (alongX) doubleArrayOf(xa + t, za + off) else doubleArrayOf(xa + off, za + t)
        fun bx(t: Double, y: Double, off: Double, along: Double, h: Double, thick: Double, c: Int) {
            val p = at(t, off)
            if (alongX) b.box(p[0], y, p[1], along, h, thick, c) else b.box(p[0], y, p[1], thick, h, along, c)
        }
        val wall = C("#EDE6D8"); val cap = C("#CFC8BA"); val iron = C("#26292D")
        b.m(Mt.PLASTER, 0.6f); bx(len / 2, 0.27, 0.0, len, 0.54, 0.22, wall)
        b.m(Mt.STONE, 0.8f); bx(len / 2, 0.57, 0.0, len, 0.06, 0.32, cap); bx(len / 2, 0.04, 0.0, len, 0.08, 0.3, C("#B9B2A5"))
        // grade de ferro (barras de 2 cm a cada 12 cm, dois trilhos)
        b.m(Mt.METAL, 1f)
        bx(len / 2, 1.5, 0.0, len, 0.05, 0.05, iron); bx(len / 2, 0.75, 0.0, len, 0.05, 0.05, iron)
        val nb = (len / 0.12).toInt()
        for (k in 0..nb) { val t = len * k / nb; bx(t, 1.1, 0.0, 0.022, 1.0, 0.022, iron)
            if (k % 2 == 0) { b.m(Mt.PLAIN); bx(t, 1.6, 0.0, 0.05, 0.1, 0.05, iron); b.m(Mt.METAL, 1f) } }
        // pilares
        for (k in 0..n) {
            val t = k * st
            b.m(Mt.PLASTER, 0.6f); bx(t, 0.9, 0.0, 0.36, 1.8, 0.36, wall)
            b.m(Mt.STONE, 0.8f); bx(t, 0.15, 0.0, 0.44, 0.3, 0.44, C("#B9B2A5")); bx(t, 1.84, 0.0, 0.46, 0.08, 0.46, cap); bx(t, 1.92, 0.0, 0.3, 0.07, 0.3, C("#E3DCCD"))
        }
    }

}
