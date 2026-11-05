package com.vinicius.meular

import java.util.concurrent.ConcurrentHashMap

// Tamanho real de cada móvel: o que ele ocupa de verdade no chão e a altura, lidos da própria malha 3D.
// O modelo é desenhado no tamanho do personagem (escala [scale]) e a colisão, a seleção e a sombra usam
// esse tamanho, e não a casa inteira da grade.
object Foot {
    private val cache = ConcurrentHashMap<Type, FloatArray>()

    fun scale(t: Type): Float = 1f

    // Limites da malha sem escala: [x0, z0, x1, z1, altura] ou null se não deu para ler.
    private fun raw(t: Type): FloatArray? {
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
        t.glb?.let { id ->
            // Etapa 83: objetos da biblioteca 3D usam os colisores do próprio GLB (a folhagem do vaso não bloqueia ninguém)
            val g = Glb.get(id) ?: return floatArrayOf(0f, 0f, t.w.toFloat(), t.h.toFloat(), t.alt)
            val f = g.foot(t.dyn)
            val cx = t.w / 2f; val cz = t.h / 2f
            val bb = floatArrayOf(cx + f[0], cz + f[1], cx + f[2], cz + f[3], f[4])
            cache[t] = bb
            return bb
        }
        if (t.cat == 4) {
            // árvores e itens do quintal: só o pé (tronco/base) conta como corpo, a copa não bloqueia
            val ex = when (t.fl) { "fence_panel" -> 1.0f; "hedge" -> 1.2f; "bench" -> 0.7f; "fl_lav", "bush_a", "bush_b", "bush_pink", "bush_white" -> 0.7f; else -> 0.35f }
            val ez = when (t.fl) { "fence_panel" -> 0.1f; "hedge" -> 0.7f; "bench" -> 0.3f; "fl_lav", "bush_a", "bush_b", "bush_pink", "bush_white" -> 0.7f; else -> 0.35f }
            val bb = floatArrayOf(t.w / 2f - ex, t.h / 2f - ez, t.w / 2f + ex, t.h / 2f + ez, t.alt)
            cache[t] = bb
            return bb
        }
        val r = raw(t) ?: return floatArrayOf(0f, 0f, t.w.toFloat(), t.h.toFloat(), t.alt)
        val s = scale(t)
        val cx = t.w / 2f
        val cz = t.h / 2f
        val b = floatArrayOf(cx + (r[0] - cx) * s, cz + (r[1] - cz) * s, cx + (r[2] - cx) * s, cz + (r[3] - cz) * s, r[4] * s)
        cache[t] = b
        return b
    }

    fun height(t: Type): Float = box(t)[4]

    /** Etapa 86: retângulos [x0, z0, x1, z1] de cada colisor que bloqueia (pernas da mesa, assento da cadeira...), já girados,
     *  para encaixar uma cadeira embaixo da mesa sem bater no tampo. null = usar o retângulo inteiro. */
    fun blockRects(t: Type, rot: Int, x: Int, y: Int, ox: Float, oz: Float): List<FloatArray>? {
        val g = t.glb?.let { Glb.get(it) } ?: return null
        val bl = g.cols.filter { it.blocks }
        if (bl.size < 2) return null
        val odd = rot % 2 != 0
        val w = if (odd) t.h else t.w
        val h = if (odd) t.w else t.h
        val cx = x + ox + w / 2f; val cz = y + oz + h / 2f
        val q = ((rot % 4) + 4) % 4
        return bl.map { c ->
            val (wx, wz) = when (q) { 1 -> Pair(c.cz, -c.cx); 2 -> Pair(-c.cx, -c.cz); 3 -> Pair(-c.cz, c.cx); else -> Pair(c.cx, c.cz) }
            val sx = if (odd) c.sz else c.sx; val sz = if (odd) c.sx else c.sz
            floatArrayOf(cx + wx - sx / 2f, cz + wz - sz / 2f, cx + wx + sx / 2f, cz + wz + sz / 2f)
        }
    }

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
