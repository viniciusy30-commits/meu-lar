package com.vinicius.meular

import java.util.concurrent.ConcurrentHashMap

// Tamanho real de cada móvel: o que ele ocupa de verdade no chão e a altura, lidos da própria malha 3D.
// O modelo é desenhado no tamanho do personagem (escala [scale]) e a colisão, a seleção e a sombra usam
// esse tamanho, e não a casa inteira da grade.
object Foot {
    private val cache = ConcurrentHashMap<Type, FloatArray>()

    // Escala dos móveis do pack, para ficarem do tamanho certo ao lado do personagem (cerca de 1,75 m).
    // O pack original é grande demais (sofá com 5 m, cadeira de escritório com 1,5 m, planta com 2,3 m).
    private val ESC: Map<String, Float> = mapOf(
        "sofa01" to 0.72f, "sofa02" to 0.75f, "casual-chair01" to 0.85f,
        "coffee-table01" to 0.72f, "coffee-table02" to 0.70f, "cabinet01" to 0.85f,
        "shelf01" to 0.88f, "stool01" to 0.80f,
        "small-cushion01" to 0.60f, "small-cushion02" to 0.65f, "speaker01" to 1.25f,
        "office-desk01" to 0.80f, "office-chair01" to 0.70f, "computer-case" to 1.45f,
        "monitor01" to 0.70f, "keyboard01" to 1.25f, "desk-lamp01" to 0.60f,
        "carpet01" to 0.60f, "carpet02" to 0.60f, "indoor-plant01" to 0.70f,
        "vase03" to 0.85f, "book01" to 0.70f, "book02" to 0.75f
    )

    fun scale(t: Type): Float {
        val m = t.mob ?: return 1f
        return ESC[m] ?: 1f
    }

    // Limites da malha sem escala: [x0, z0, x1, z1, altura] ou null se não deu para ler.
    private fun raw(t: Type): FloatArray? {
        val m = t.mob
        if (m != null) return MobLoader.bounds(m)
        return try {
            val mesh = Models.furniture(t)
            var x0 = Float.MAX_VALUE; var z0 = Float.MAX_VALUE
            var x1 = -Float.MAX_VALUE; var z1 = -Float.MAX_VALUE
            var y1 = 0f
            for (p in mesh.parts) {
                for (v in 0 until p.count) {
                    val x = p.buf.get(v * STRIDE)
                    val y = p.buf.get(v * STRIDE + 1)
                    val z = p.buf.get(v * STRIDE + 2)
                    if (x < x0) x0 = x
                    if (x > x1) x1 = x
                    if (z < z0) z0 = z
                    if (z > z1) z1 = z
                    if (y > y1) y1 = y
                }
            }
            if (x1 < x0) null else floatArrayOf(x0, z0, x1, z1, y1)
        } catch (e: Throwable) {
            null
        }
    }

    // [x0, z0, x1, z1, altura] do móvel (sem girar), já com a escala, em metros na área de [Type.w] x [Type.h].
    fun box(t: Type): FloatArray {
        cache[t]?.let { return it }
        val r = raw(t) ?: return floatArrayOf(0f, 0f, t.w.toFloat(), t.h.toFloat(), t.alt)
        val s = scale(t)
        val cx = t.w / 2f
        val cz = t.h / 2f
        val b = floatArrayOf(cx + (r[0] - cx) * s, cz + (r[1] - cz) * s, cx + (r[2] - cx) * s, cz + (r[3] - cz) * s, r[4] * s)
        cache[t] = b
        return b
    }

    fun height(t: Type): Float = box(t)[4]

    // Retângulo que o móvel ocupa no mundo, já girado: [x0, z0, x1, z1].
    fun rect(t: Type, rot: Int, x: Int, y: Int, ox: Float, oz: Float): FloatArray {
        val b = box(t)
        val tw = t.w / 2f
        val th = t.h / 2f
        val odd = rot % 2 != 0
        val w = if (odd) t.h else t.w
        val h = if (odd) t.w else t.h
        val cx = x + ox + w / 2f
        val cz = y + oz + h / 2f
        val q = ((rot % 4) + 4) % 4
        var minX = Float.MAX_VALUE; var minZ = Float.MAX_VALUE
        var maxX = -Float.MAX_VALUE; var maxZ = -Float.MAX_VALUE
        for (k in 0 until 4) {
            val lx = (if ((k and 1) == 0) b[0] else b[2]) - tw
            val lz = (if ((k and 2) == 0) b[1] else b[3]) - th
            var rx = lx
            var rz = lz
            when (q) {
                1 -> { rx = lz; rz = -lx }
                2 -> { rx = -lx; rz = -lz }
                3 -> { rx = -lz; rz = lx }
            }
            val wx = cx + rx
            val wz = cz + rz
            if (wx < minX) minX = wx
            if (wx > maxX) maxX = wx
            if (wz < minZ) minZ = wz
            if (wz > maxZ) maxZ = wz
        }
        return floatArrayOf(minX, minZ, maxX, maxZ)
    }
}
