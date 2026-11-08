package com.vinicius.meular

import android.graphics.Bitmap
import android.opengl.GLES20
import android.opengl.GLUtils
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.exp
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Etapa 127: céu de verdade.
 * - Cúpula com degradê por vértice em alta resolução (azul fundo no alto, claro e enevoado no horizonte, brilho quente em volta do sol).
 * - Sol: disco com halo em camadas.
 * - Nuvens: camada de cúmulos procedurais (ruído fractal projetado num plano alto), com base acinzentada, topo iluminado,
 *   borda prateada do lado do sol e esmaecendo no horizonte. Textura gerada uma vez (fora do quadro) e desenhada numa cúpula que gira bem devagar.
 */
object Sky {
    val SUN = floatArrayOf(0.45f, 1f, 0.65f).let { val l = sqrt(it[0] * it[0] + it[1] * it[1] + it[2] * it[2]); floatArrayOf(it[0] / l, it[1] / l, it[2] / l) }
    const val W = 1024
    const val H = 256

    @Volatile private var pix: IntArray? = null

    /** Cor do céu numa direção (também usada pela água e pela névoa). */
    fun skyColor(dx: Float, dy: Float, dz: Float, out: FloatArray) {
        val y = max(dy, 0f)
        val t = 1f - exp(-y * 3.2f)
        // horizonte claro e levemente quente; zênite azul profundo
        var r = 0.80f + (0.24f - 0.80f) * t
        var g = 0.88f + (0.48f - 0.88f) * t
        var b = 0.96f + (0.86f - 0.96f) * t
        val cs = max(0f, dx * SUN[0] + dy * SUN[1] + dz * SUN[2])
        val glow = cs.pow(10f) * 0.22f + cs.pow(64f) * 0.35f
        r += glow * 1.0f; g += glow * 0.92f; b += glow * 0.72f
        if (dy < 0f) { val k = min(1f, -dy * 5f); r += (0.78f - r) * k; g += (0.84f - g) * k; b += (0.86f - b) * k }
        out[0] = min(1f, r); out[1] = min(1f, g); out[2] = min(1f, b)
    }

    // ---------------------------------------------------------------- ruído
    private val perm = IntArray(512).also { val p = IntArray(256) { it }; var s = 1234567L; for (i in 255 downTo 1) { s = s * 6364136223846793005L + 1442695040888963407L; val j = ((s ushr 33) % (i + 1)).toInt(); val t = p[i]; p[i] = p[j]; p[j] = t }; for (i in 0 until 512) it[i] = p[i and 255] }
    private fun hash(x: Int, y: Int) = perm[(perm[x and 255] + y) and 511] / 255f
    private fun vnoise(x: Float, y: Float): Float {
        val xi = floor(x).toInt(); val yi = floor(y).toInt()
        val fx = x - xi; val fy = y - yi
        val u = fx * fx * (3 - 2 * fx); val v = fy * fy * (3 - 2 * fy)
        val a = hash(xi, yi); val b = hash(xi + 1, yi); val c = hash(xi, yi + 1); val d = hash(xi + 1, yi + 1)
        return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v
    }
    private fun fbm(x: Float, y: Float): Float {
        var s = 0f; var a = 0.5f; var fx = x; var fy = y
        for (i in 0 until 5) { s += a * vnoise(fx, fy); val nx = fx * 1.6f + fy * 1.2f; fy = -fx * 1.2f + fy * 1.6f; fx = nx + 3.1f; a *= 0.5f }
        return s
    }
    private fun density(px: Float, pz: Float): Float {
        // cúmulos: massas grandes com bordas recortadas
        val big = fbm(px * 0.55f, pz * 0.55f)
        val n = big * 0.75f + fbm(px * 1.9f + 7.3f, pz * 1.9f - 2.1f) * 0.25f
        return ((n - 0.47f) * 4.2f).coerceIn(0f, 1f)
    }

    /** Pixels RGBA da camada de nuvens (u = azimute, v = 0 no zênite → 1 no horizonte). Calculado uma vez. */
    fun cloudPixels(): IntArray {
        pix?.let { return it }
        synchronized(this) {
            pix?.let { return it }
            val a = IntArray(W * H)
            val sc = FloatArray(3)
            for (j in 0 until H) {
                val el = (1f - (j + 0.5f) / H) * (PI.toFloat() / 2)      // elevação
                val dy = sin(el); val ch = cos(el)
                for (i in 0 until W) {
                    val az = (i + 0.5f) / W * 2f * PI.toFloat()
                    val dx = ch * cos(az); val dz = ch * sin(az)
                    // projeção num plano de nuvens (perto do horizonte as nuvens se achatam e somem na névoa)
                    val k = 1f / (dy + 0.06f)
                    val px = dx * k * 1.3f; val pz = dz * k * 1.3f
                    val d = density(px, pz)
                    if (d <= 0.001f) { a[j * W + i] = 0; continue }
                    // iluminação: menos densidade na direção do sol = lado iluminado
                    val dl = density(px + SUN[0] * 0.35f, pz + SUN[2] * 0.35f)
                    val lit = (1f - dl * 0.85f).coerceIn(0f, 1f)
                    val cs = max(0f, dx * SUN[0] + dy * SUN[1] + dz * SUN[2])
                    val silver = cs.pow(12f) * (1f - d) * 0.6f
                    var r = 0.66f + 0.36f * lit + silver; var g = 0.70f + 0.32f * lit + silver; var b = 0.80f + 0.22f * lit + silver * 0.8f
                    // horizonte: as nuvens tomam a cor da névoa
                    val hz = (1f - dy * 4f).coerceIn(0f, 1f)
                    skyColor(dx, dy, dz, sc)
                    r += (sc[0] - r) * hz * 0.6f; g += (sc[1] - g) * hz * 0.6f; b += (sc[2] - b) * hz * 0.6f
                    val al = (d * (0.55f + 0.45f * min(1f, d * 2f))) * (1f - hz * 0.7f) * min(1f, dy * 18f)
                    fun c8(v: Float) = (min(1f, v) * 255f).toInt().coerceIn(0, 255)
                    a[j * W + i] = (c8(al) shl 24) or (c8(r) shl 16) or (c8(g) shl 8) or c8(b)
                }
            }
            pix = a
            return a
        }
    }

    /** Começa a calcular as nuvens fora da thread do GL (no carregamento). */
    fun prepare() { if (pix == null) Thread({ cloudPixels() }, "ceu").start() }

    private var texId = 0
    private var texGen = -1
    fun texture(): Int {
        if (texId != 0 && texGen == GlGen.gen) return texId
        val ids = IntArray(1); GLES20.glGenTextures(1, ids, 0); texId = ids[0]; texGen = GlGen.gen
        val bmp = Bitmap.createBitmap(cloudPixels(), W, H, Bitmap.Config.ARGB_8888)
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, texId)
        GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bmp, 0)
        GLES20.glGenerateMipmap(GLES20.GL_TEXTURE_2D)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR_MIPMAP_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_REPEAT)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)
        bmp.recycle()
        return texId
    }

    /** Cúpula do céu (degradê por vértice + sol). Sem normal (o shader pinta a cor pura). */
    fun dome(): Mesh {
        val b = MB()
        val R = 120f
        val lat = 28; val lon = 56
        val sc = FloatArray(3)
        fun col(dx: Float, dy: Float, dz: Float): Int { skyColor(dx, dy, dz, sc); return android.graphics.Color.rgb((sc[0] * 255).toInt(), (sc[1] * 255).toInt(), (sc[2] * 255).toInt()) }
        val pi = PI.toFloat()
        for (i in 0 until lat) {
            // mais faixas perto do horizonte (onde o degradê muda rápido)
            fun th(k: Int): Float { val t = k.toFloat() / lat; return pi * (if (t < 0.5f) 0.5f * (1f - (1f - 2f * t).pow(1.6f)) else 0.5f + 0.5f * (2f * t - 1f).pow(1.6f)) }
            val t0 = th(i); val t1 = th(i + 1)
            for (j in 0 until lon) {
                val p0 = 2f * pi * j / lon; val p1 = 2f * pi * (j + 1) / lon
                fun pt(t: Float, p: Float) { val dx = sin(t) * cos(p); val dy = cos(t); val dz = sin(t) * sin(p); b.raw(R * dx, R * dy, R * dz, col(dx, dy, dz)) }
                pt(t0, p0); pt(t1, p0); pt(t1, p1)
                pt(t0, p0); pt(t1, p1); pt(t0, p1)
            }
        }
        // sol: disco nítido + halos
        val sx = SUN[0] * 100; val sy = SUN[1] * 100; val sz = SUN[2] * 100
        b.al = 0.07f; b.sphere(sx.toDouble(), sy.toDouble(), sz.toDouble(), 30.0, C("#FFF2C8"), 30.0, 14, false)
        b.al = 0.14f; b.sphere(sx.toDouble(), sy.toDouble(), sz.toDouble(), 14.0, C("#FFEFC0"), 14.0, 14, false)
        b.al = 0.32f; b.sphere(sx.toDouble(), sy.toDouble(), sz.toDouble(), 6.5, C("#FFF4D6"), 6.5, 12, false)
        b.al = 1f; b.sphere(sx.toDouble(), sy.toDouble(), sz.toDouble(), 3.2, C("#FFFDF4"), 3.2, 14, false)
        return b.toMesh(true)
    }

    /** Cúpula das nuvens (textura com alfa), um pouco menor que a do céu. */
    fun clouds(): Mesh {
        val R = 112f
        val lat = 12; val lon = 48
        val n = lat * lon * 6
        val fb = ByteBuffer.allocateDirect(n * STRIDE * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
        val pi = PI.toFloat()
        fun pt(el: Float, az: Float, u: Float, v: Float) {
            val ch = cos(el)
            fb.put(R * ch * cos(az)); fb.put(R * sin(el)); fb.put(R * ch * sin(az))
            fb.put(0f); fb.put(0f); fb.put(0f)
            fb.put(1f); fb.put(1f); fb.put(1f); fb.put(1f)
            fb.put(u); fb.put(v)
        }
        for (i in 0 until lat) {
            val v0 = i.toFloat() / lat; val v1 = (i + 1).toFloat() / lat
            val e0 = (1f - v0) * pi / 2; val e1 = (1f - v1) * pi / 2
            for (j in 0 until lon) {
                val u0 = j.toFloat() / lon; val u1 = (j + 1).toFloat() / lon
                val a0 = u0 * 2 * pi; val a1 = u1 * 2 * pi
                pt(e0, a0, u0, v0); pt(e1, a0, u0, v1); pt(e1, a1, u1, v1)
                pt(e0, a0, u0, v0); pt(e1, a1, u1, v1); pt(e0, a1, u1, v0)
            }
        }
        fb.position(0)
        return Mesh(listOf(Part(Mt.PLAIN, fb, n, tex = texture())))
    }
}
