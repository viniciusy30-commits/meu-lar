package com.vinicius.meular

import android.content.res.AssetManager
import android.graphics.BitmapFactory
import android.opengl.GLES20
import android.opengl.GLUtils
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.cos
import kotlin.math.sin

// Etapa 67: vegetação e cerca modeladas (assets/flora/<id>.bin, formato FLR1, feito por ferramentas/ambiente/trees.py).
// Cada arquivo traz peças por (textura, material, recorte) com cor por vértice (sombra de copa já assada) e UV.
// Batch junta várias instâncias (posição, escala, giro) em poucas peças grandes: poucas chamadas de desenho.
// Deve ser chamado na thread do GL (sobe as texturas).
object Flora {
    @Volatile var assets: AssetManager? = null
    private val texIds = HashMap<String, Int>()
    private val cache = HashMap<String, List<Src>>()

    fun reset() { texIds.clear() }

    private class Src(val mat: Int, val tex: String, val cut: Boolean, val nv: Int, val ni: Int,
                      val pos: FloatArray, val nor: FloatArray, val col: FloatArray, val uv: FloatArray, val idx: ShortArray)

    private fun texture(name: String, clamp: Boolean): Int {
        texIds[name]?.let { return it }
        var id = 0
        try {
            val am = assets ?: return 0
            val opt = BitmapFactory.Options().apply { inPremultiplied = false }
            val bmp = am.open("flora/tex/$name").use { BitmapFactory.decodeStream(it, null, opt) }
            if (bmp != null) {
                val ids = IntArray(1)
                GLES20.glGenTextures(1, ids, 0)
                id = ids[0]
                GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, id)
                GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bmp, 0)
                GLES20.glGenerateMipmap(GLES20.GL_TEXTURE_2D)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR_MIPMAP_LINEAR)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
                val w = if (clamp) GLES20.GL_CLAMP_TO_EDGE else GLES20.GL_REPEAT
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, w)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, w)
                bmp.recycle()
            }
        } catch (e: Throwable) {
            id = 0
        }
        texIds[name] = id
        return id
    }

    /** Existe o modelo assets/flora/<id>.bin? */
    fun exists(id: String): Boolean = read(id).isNotEmpty()

    private fun read(id: String): List<Src> {
        cache[id]?.let { return it }
        val out = ArrayList<Src>()
        try {
            val am = assets ?: return out
            val raw = am.open("flora/$id.bin").use { it.readBytes() }
            val b = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN)
            b.position(4)
            val nt = b.int
            val np = b.int
            val names = ArrayList<String>()
            for (i in 0 until nt) {
                val n = b.get().toInt() and 255
                val by = ByteArray(n)
                b.get(by)
                names.add(String(by, Charsets.UTF_8))
            }
            for (pi in 0 until np) {
                val mat = b.get().toInt()
                val ti = b.short.toInt()
                val cut = b.get().toInt() != 0
                val nv = b.int
                val ni = b.int
                val pos = FloatArray(nv * 3); val nor = FloatArray(nv * 3); val col = FloatArray(nv * 4); val uv = FloatArray(nv * 2)
                for (v in 0 until nv) {
                    for (k in 0 until 3) pos[v * 3 + k] = b.float
                    for (k in 0 until 3) nor[v * 3 + k] = b.float
                    for (k in 0 until 4) col[v * 4 + k] = (b.get().toInt() and 255) / 255f
                    uv[v * 2] = b.float; uv[v * 2 + 1] = b.float
                }
                val idx = ShortArray(ni)
                for (i in 0 until ni) idx[i] = b.short
                out.add(Src(mat, names[ti], cut, nv, ni, pos, nor, col, uv, idx))
            }
        } catch (e: Throwable) {
            out.clear()
        }
        cache[id] = out
        return out
    }

    private class Acc(val mat: Int, val tex: String, val cut: Boolean) {
        var v = FloatArray(STRIDE * 4096)
        var nv = 0
        var idx = ShortArray(6144)
        var ni = 0
    }

    class Batch {
        private val accs = LinkedHashMap<String, ArrayList<Acc>>()

        /** Põe uma instância de [id] em (x,y,z), com escala [s], giro [ry] (rad, em Y) e cor multiplicada (variação entre árvores). */
        fun place(id: String, x: Double, y: Double, z: Double, s: Double = 1.0, ry: Double = 0.0, tr0: Float = 1f, tg0: Float = 1f, tb0: Float = 1f) {
            // Etapa 69: pinheiro e cerca saíam escuros/acinzentados no jogo
            val boost = if (id.startsWith("fence_")) 1.14f else 1f
            val pg = if (id.startsWith("pine")) 1.2f else 1f
            val tr = tr0 * boost * (if (pg > 1f) 1.1f else 1f); val tg = tg0 * boost * pg; val tb = tb0 * boost * (if (pg > 1f) 1.05f else 1f)
            val cs = cos(ry).toFloat(); val sn = sin(ry).toFloat(); val sc = s.toFloat()
            for (src in read(id)) {
                val key = "${src.mat}|${src.tex}|${src.cut}"
                val list = accs.getOrPut(key) { ArrayList() }
                var a = list.lastOrNull()
                if (a == null || a.nv + src.nv > 64000) { a = Acc(src.mat, src.tex, src.cut); list.add(a) }
                if ((a.nv + src.nv) * STRIDE > a.v.size) a.v = a.v.copyOf(maxOf(a.v.size * 2, (a.nv + src.nv) * STRIDE))
                if (a.ni + src.ni > a.idx.size) a.idx = a.idx.copyOf(maxOf(a.idx.size * 2, a.ni + src.ni))
                for (i in 0 until src.nv) {
                    val px = src.pos[i * 3] * sc; val py = src.pos[i * 3 + 1] * sc; val pz = src.pos[i * 3 + 2] * sc
                    val nx = src.nor[i * 3]; val ny = src.nor[i * 3 + 1]; val nz = src.nor[i * 3 + 2]
                    val o = (a.nv + i) * STRIDE
                    a.v[o] = (px * cs + pz * sn + x).toFloat()
                    a.v[o + 1] = (py + y).toFloat()
                    a.v[o + 2] = (-px * sn + pz * cs + z).toFloat()
                    a.v[o + 3] = nx * cs + nz * sn
                    a.v[o + 4] = ny
                    a.v[o + 5] = -nx * sn + nz * cs
                    a.v[o + 6] = src.col[i * 4] * tr
                    a.v[o + 7] = src.col[i * 4 + 1] * tg
                    a.v[o + 8] = src.col[i * 4 + 2] * tb
                    a.v[o + 9] = src.col[i * 4 + 3]
                    a.v[o + 10] = src.uv[i * 2]
                    a.v[o + 11] = src.uv[i * 2 + 1]
                }
                val base = a.nv
                for (i in 0 until src.ni) a.idx[a.ni + i] = (src.idx[i] + base).toShort()
                a.nv += src.nv
                a.ni += src.ni
            }
        }

        fun build(): List<Part> {
            val parts = ArrayList<Part>()
            for (list in accs.values) for (a in list) {
                if (a.nv == 0) continue
                val fb = ByteBuffer.allocateDirect(a.nv * STRIDE * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
                fb.put(a.v, 0, a.nv * STRIDE)
                fb.position(0)
                val ib = ByteBuffer.allocateDirect(a.ni * 2).order(ByteOrder.nativeOrder()).asShortBuffer()
                ib.put(a.idx, 0, a.ni)
                ib.position(0)
                val p = Part(a.mat, fb, a.nv, ib, a.ni, texture(a.tex, a.cut))
                p.gpu = true
                if (a.cut) p.cut = 0.4f
                parts.add(p)
            }
            return parts
        }
    }
}
