package com.vinicius.meular

import android.opengl.GLES20
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.exp
import kotlin.math.max
import kotlin.math.min

/**
 * Cidade 6: as poças de luz de todos os postes num mapa só (textura 2048², ~1,6 m por pixel, filtro linear).
 * O shader faz uma leitura por pixel à noite: luz quente no chão em volta de cada poste, sem custo por poste.
 */
object LightMap {
    @Volatile var tex = 0; private set
    var x0 = 0f; var z0 = 0f; var inv = 0f
    private var gen = -1
    private var src: FloatArray? = null
    private const val N = 2048

    /** chamado no início do quadro (thread do GL) */
    fun ensure() {
        if (!(City.C6 && Relevo.on)) return
        val p = Relevo.postesA
        if (p.isEmpty()) return
        if (tex != 0 && gen == GlGen.gen && src === p) return
        val wa = Relevo.worldA
        val size = if (wa.size >= 2) max(wa[0], wa[1]) + 40f else 3400f
        x0 = Relevo.CX - 20f; z0 = Relevo.CZ - 20f; inv = 1f / size
        val px = size / N
        val img = FloatArray(N * N)
        var k = 0
        while (k + 2 < p.size) {
            val lx = (p[k] + 20f) / px; val lz = (p[k + 1] + 20f) / px; val r = max(p[k + 2], 3f) / px
            val rr = (r * 1.6f).toInt() + 1
            val ci = lx.toInt(); val cj = lz.toInt()
            for (j in max(0, cj - rr)..min(N - 1, cj + rr)) for (i in max(0, ci - rr)..min(N - 1, ci + rr)) {
                val dx = (i + 0.5f - lx) / r; val dz = (j + 0.5f - lz) / r
                val d2 = dx * dx + dz * dz
                if (d2 > 2.6f) continue
                img[j * N + i] += exp(-d2 * 1.8f)
            }
            k += 3
        }
        val bb = ByteBuffer.allocateDirect(N * N).order(ByteOrder.nativeOrder())
        for (q in 0 until N * N) bb.put((min(1f, img[q]) * 255f).toInt().toByte())
        bb.position(0)
        val ids = IntArray(1)
        if (tex != 0 && gen == GlGen.gen) GLES20.glDeleteTextures(1, intArrayOf(tex), 0)
        GLES20.glGenTextures(1, ids, 0); tex = ids[0]
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, tex)
        GLES20.glPixelStorei(GLES20.GL_UNPACK_ALIGNMENT, 1)
        GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D, 0, GLES20.GL_LUMINANCE, N, N, 0, GLES20.GL_LUMINANCE, GLES20.GL_UNSIGNED_BYTE, bb)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, 0)
        gen = GlGen.gen; src = p
    }
}
