package com.vinicius.meular

import android.content.res.AssetManager
import android.graphics.BitmapFactory
import android.opengl.GLES20
import android.opengl.GLUtils
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.nio.ShortBuffer

/**
 * Personagem do pack "Cute Characters – Modular Animated Pack" (f_1), convertido do FBX
 * para assets/cute/f_1.bin (malha + pesos de pele + animações já "assadas"
 * em matrizes de osso por quadro) e assets/cute/textures.png.
 * A pele é feita na CPU a cada quadro (≈6,5 mil vértices, barato).
 * Se qualquer coisa falhar, [frame] devolve null e o app usa o personagem antigo.
 */
object CuteChar {
    const val ENABLED = true
    const val IDLE = 0
    const val WALK = 1
    const val JUMP = 2
    /** Velocidade de reprodução do andar: com 1,9 m/s no jogo os pés não deslizam no chão. */
    private const val WALK_RATE = 1.14f

    @Volatile var assets: AssetManager? = null

    /** true quando o personagem novo carregou e pode ser desenhado. */
    val ready: Boolean get() = ENABLED && loaded && mesh != null

    private var nv = 0
    private var ni = 0
    private var nb = 0
    private var pos = FloatArray(0)      // 3 por vértice (pose de referência)
    private var nor = FloatArray(0)      // 3 por vértice
    private var bi = IntArray(0)         // 4 por vértice
    private var bw = FloatArray(0)       // 4 por vértice
    private var clipLen = FloatArray(0)
    private var clipFrames = IntArray(0)
    private var clipData = arrayOfNulls<FloatArray>(0) // frames * nb * 12
    private var out = FloatArray(0)
    private var fb: FloatBuffer? = null
    private var ib: ShortBuffer? = null
    private var mesh: Mesh? = null
    private var texId = 0
    private var loaded = false
    private var failed = false

    /** Chamar na thread GL (onSurfaceCreated): carrega o modelo e cria a textura. */
    fun initGl() {
        if (!ENABLED) return
        val am = assets ?: return
        try {
            if (!loaded && !failed) load(am)
            if (loaded) {
                val ids = IntArray(1)
                GLES20.glGenTextures(1, ids, 0)
                texId = ids[0]
                val bmp = am.open("cute/textures.png").use { BitmapFactory.decodeStream(it) }
                GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, texId)
                GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bmp, 0)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)
                bmp.recycle()
                mesh = Mesh(listOf(Part(Mt.PLAIN, fb!!, nv, ib, ni, texId)))
            }
        } catch (e: Throwable) {
            failed = true
            loaded = false
            mesh = null
        }
    }

    private fun load(am: AssetManager) {
        val raw = am.open("cute/f_1.bin").use { it.readBytes() }
        val b = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN)
        require(b.get().toInt() == 'C'.code && b.get().toInt() == 'U'.code && b.get().toInt() == 'T'.code && b.get().toInt() == '1'.code)
        nv = b.int; ni = b.int; nb = b.int
        val nc = b.int
        pos = FloatArray(nv * 3); nor = FloatArray(nv * 3)
        bi = IntArray(nv * 4); bw = FloatArray(nv * 4)
        out = FloatArray(nv * STRIDE)
        for (v in 0 until nv) {
            for (k in 0 until 3) pos[v * 3 + k] = b.float
            for (k in 0 until 3) nor[v * 3 + k] = b.float
            val u = b.float
            val w = b.float
            val o = v * STRIDE
            out[o + 10] = u
            out[o + 11] = w
            out[o + 6] = (b.get().toInt() and 255) / 255f
            out[o + 7] = (b.get().toInt() and 255) / 255f
            out[o + 8] = (b.get().toInt() and 255) / 255f
            out[o + 9] = (b.get().toInt() and 255) / 255f
            for (k in 0 until 4) bi[v * 4 + k] = b.get().toInt() and 255
            for (k in 0 until 4) bw[v * 4 + k] = (b.get().toInt() and 255) / 255f
        }
        val idx = ShortArray(ni)
        for (i in 0 until ni) idx[i] = b.short
        clipLen = FloatArray(nc); clipFrames = IntArray(nc)
        clipData = arrayOfNulls(nc)
        for (c in 0 until nc) {
            clipLen[c] = b.float
            val nf = b.int
            clipFrames[c] = nf
            val d = FloatArray(nf * nb * 12)
            for (i in d.indices) d[i] = b.float
            clipData[c] = d
        }
        fb = ByteBuffer.allocateDirect(nv * STRIDE * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
        ib = ByteBuffer.allocateDirect(ni * 2).order(ByteOrder.nativeOrder()).asShortBuffer().also {
            it.put(idx); it.position(0)
        }
        loaded = true
    }

    /** Duração (s) do clip. */
    fun clipSeconds(clip: Int): Float =
        if (loaded && clip in clipLen.indices) clipLen[clip] else 1f

    // estado por "slot" (0 = jogador, 1 = avatar da casa, 2 = criador): fase do laço e transição suave
    private val slotClip = IntArray(3) { -1 }
    private val slotT0 = FloatArray(3)
    private val slotBlend = FloatArray(3)
    private val slotNs = LongArray(3)
    private val slotLast = arrayOfNulls<FloatArray>(3)
    private var bone = FloatArray(0)

    private fun smooth01(x: Float): Float {
        val c = if (x < 0f) 0f else if (x > 1f) 1f else x
        return c * c * (3f - 2f * c)
    }

    /**
     * Pose do clip [clip] no tempo [t] (segundos). Devolve a malha pronta para desenhar.
     * Nos clips em laço (parado/andar) a fase recomeça do zero quando o clip muda, e a troca
     * de clip é suavizada (≈0,15 s), sem "pulo" de pose. [slot] separa quem está desenhando.
     */
    fun frame(clip: Int, t: Float, slot: Int = 0): Mesh? {
        val m = mesh ?: return null
        if (!loaded) return null
        val c = clip.coerceIn(0, clipData.size - 1)
        val sl = slot.coerceIn(0, slotClip.size - 1)
        val nf = clipFrames[c]
        val len = clipLen[c].coerceAtLeast(0.001f)
        val d = clipData[c] ?: return null
        val n12 = nb * 12
        if (bone.size != n12) bone = FloatArray(n12)

        val now = System.nanoTime()
        var dt = (now - slotNs[sl]) / 1_000_000_000f
        if (dt < 0f || dt > 0.25f) dt = 0.016f
        slotNs[sl] = now

        if (slotClip[sl] != c) {
            slotBlend[sl] = if (slotClip[sl] < 0) 0f else if (c == JUMP) 0.06f else 0.15f
            slotClip[sl] = c
            slotT0[sl] = t
        }
        var lt = if (c == JUMP) t else (t - slotT0[sl]) * (if (c == WALK) WALK_RATE else 1f)
        if (c != JUMP) {
            lt %= len
            if (lt < 0f) lt += len
        } else if (lt < 0f) lt = 0f

        val ft = (lt / len) * (nf - 1).coerceAtLeast(1)
        val f0 = ft.toInt().coerceIn(0, nf - 1)
        val f1 = (f0 + 1).coerceAtMost(nf - 1)
        val a = ft - f0
        val o0 = f0 * n12
        val o1 = f1 * n12
        for (j in 0 until n12) bone[j] = d[o0 + j] + (d[o1 + j] - d[o0 + j]) * a

        val prev = slotLast[sl]
        if (slotBlend[sl] > 0f && prev != null && prev.size == n12) {
            val dur = if (c == JUMP) 0.06f else 0.15f
            val k = smooth01(1f - slotBlend[sl] / dur)
            for (j in 0 until n12) bone[j] = prev[j] + (bone[j] - prev[j]) * k
            slotBlend[sl] -= dt
        } else {
            slotBlend[sl] = 0f
        }
        val keep: FloatArray = if (prev != null && prev.size == n12) prev else FloatArray(n12).also { slotLast[sl] = it }
        System.arraycopy(bone, 0, keep, 0, n12)

        val mm = bone
        for (v in 0 until nv) {
            val px = pos[v * 3]; val py = pos[v * 3 + 1]; val pz = pos[v * 3 + 2]
            val nx = nor[v * 3]; val ny = nor[v * 3 + 1]; val nz = nor[v * 3 + 2]
            var x = 0f; var y = 0f; var z = 0f
            var X = 0f; var Y = 0f; var Z = 0f
            for (k in 0 until 4) {
                val w = bw[v * 4 + k]
                if (w <= 0f) continue
                val bo = bi[v * 4 + k] * 12
                x += w * (mm[bo] * px + mm[bo + 1] * py + mm[bo + 2] * pz + mm[bo + 3])
                y += w * (mm[bo + 4] * px + mm[bo + 5] * py + mm[bo + 6] * pz + mm[bo + 7])
                z += w * (mm[bo + 8] * px + mm[bo + 9] * py + mm[bo + 10] * pz + mm[bo + 11])
                X += w * (mm[bo] * nx + mm[bo + 1] * ny + mm[bo + 2] * nz)
                Y += w * (mm[bo + 4] * nx + mm[bo + 5] * ny + mm[bo + 6] * nz)
                Z += w * (mm[bo + 8] * nx + mm[bo + 9] * ny + mm[bo + 10] * nz)
            }
            val o = v * STRIDE
            out[o] = x; out[o + 1] = y; out[o + 2] = z
            val nl = Math.sqrt((X * X + Y * Y + Z * Z).toDouble()).toFloat()
            val inv = if (nl > 1e-9f) 1f / nl else 0f
            out[o + 3] = X * inv; out[o + 4] = if (nl > 1e-9f) Y * inv else 1f; out[o + 5] = Z * inv
        }
        val buf = fb ?: return null
        buf.position(0)
        buf.put(out, 0, nv * STRIDE)
        buf.position(0)
        return m
    }
}
