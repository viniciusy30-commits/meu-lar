package com.vinicius.meular
// versao etapa39-tamanhos (sem comentarios de bloco; se esta linha aparece no GitHub, este zip foi aplicado)

import android.content.res.AssetManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.opengl.GLES20
import android.opengl.GLUtils
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.ConcurrentHashMap

// Móveis do pack "home-set-2020s" (Unity), convertidos por ferramentas/moveis/buildmob.py para assets/mob.
//  - mob/<id>.bin (MOB1): tamanho em casas (largura, profundidade), texturas usadas e as peças (uma por material):
//    material do app, índice da textura, recorte por alfa (folhas), cor do material, vértices (pos, normal, uv) e índices;
//  - a pasta mob/tex: texturas do pack (potência de 2, ladrilhadas);
//  - mob/icons/<id>.png: miniatura da loja.
// A malha vem do pack sem alteração de tamanho nem de forma: x em [0,largura], z em [0,profundidade], y para cima, frente em +z.
// Deve ser chamado na thread do GL (sobe as texturas).
object MobLoader {
    @Volatile var assets: AssetManager? = null
    private val texIds = HashMap<String, Int>()
    private val thumbs = HashMap<String, Bitmap?>()
    private val boundsCache = ConcurrentHashMap<String, FloatArray>()

    // O contexto do GL foi recriado: as texturas antigas não valem mais.
    fun reset() { texIds.clear() }

    private fun texture(am: AssetManager, name: String): Int {
        texIds[name]?.let { return it }
        var id = 0
        try {
            val bmp = am.open("mob/tex/$name").use { BitmapFactory.decodeStream(it) }
            if (bmp != null) {
                val ids = IntArray(1)
                GLES20.glGenTextures(1, ids, 0)
                id = ids[0]
                GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, id)
                GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bmp, 0)
                GLES20.glGenerateMipmap(GLES20.GL_TEXTURE_2D)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR_MIPMAP_LINEAR)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_REPEAT)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_REPEAT)
                bmp.recycle()
            }
        } catch (e: Throwable) {
            id = 0
        }
        texIds[name] = id
        return id
    }

    // Miniatura da loja (ou null se não existir).
    fun thumb(id: String): Bitmap? {
        if (thumbs.containsKey(id)) return thumbs[id]
        val am = assets
        val b = try { am?.open("mob/icons/$id.png")?.use { BitmapFactory.decodeStream(it) } } catch (e: Throwable) { null }
        thumbs[id] = b
        return b
    }

    // Limites da malha do móvel, sem mexer no GL: [x0, z0, x1, z1, altura] (ou null se não achar o arquivo).
    fun bounds(id: String): FloatArray? {
        boundsCache[id]?.let { return it }
        val am = assets ?: return null
        try {
            val raw = am.open("mob/$id.bin").use { it.readBytes() }
            val b = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN)
            b.position(4)
            val nt = b.int
            val np = b.int
            b.int; b.int
            for (i in 0 until nt) {
                val n = b.get().toInt() and 255
                b.position(b.position() + n)
            }
            var x0 = Float.MAX_VALUE; var z0 = Float.MAX_VALUE
            var x1 = -Float.MAX_VALUE; var z1 = -Float.MAX_VALUE
            var y1 = 0f
            for (pi in 0 until np) {
                b.get(); b.short; b.get()
                b.float; b.float; b.float; b.float
                val nv = b.int
                val ni = b.int
                for (v in 0 until nv) {
                    val x = b.float
                    val y = b.float
                    val z = b.float
                    b.position(b.position() + 20)
                    if (x < x0) x0 = x
                    if (x > x1) x1 = x
                    if (z < z0) z0 = z
                    if (z > z1) z1 = z
                    if (y > y1) y1 = y
                }
                b.position(b.position() + ni * 2)
            }
            if (x1 < x0) return null
            val r = floatArrayOf(x0, z0, x1, z1, y1)
            boundsCache[id] = r
            return r
        } catch (e: Throwable) {
            return null
        }
    }

    fun load(id: String): Mesh {
        val am = assets ?: return Mesh(emptyList())
        try {
            val raw = am.open("mob/$id.bin").use { it.readBytes() }
            val b = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN)
            require(b.get().toInt() == 'M'.code && b.get().toInt() == 'O'.code && b.get().toInt() == 'B'.code && b.get().toInt() == '1'.code)
            val nt = b.int
            val np = b.int
            b.int; b.int   // largura e profundidade em casas (o tipo já guarda)
            val names = ArrayList<String>()
            for (i in 0 until nt) {
                val n = b.get().toInt() and 255
                val bytes = ByteArray(n)
                b.get(bytes)
                names.add(String(bytes, Charsets.UTF_8))
            }
            val parts = ArrayList<Part>()
            for (pi in 0 until np) {
                val mat = b.get().toInt().coerceIn(0, Mt.COUNT - 1)
                val ti = b.short.toInt()
                val cut = b.get().toInt()
                val cr = b.float; val cg = b.float; val cb = b.float; val ca = b.float
                val nv = b.int
                val ni = b.int
                val fb = ByteBuffer.allocateDirect(nv * STRIDE * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
                val row = FloatArray(STRIDE)
                for (v in 0 until nv) {
                    for (k in 0 until 3) row[k] = b.float
                    for (k in 0 until 3) row[3 + k] = b.float
                    row[6] = cr; row[7] = cg; row[8] = cb; row[9] = ca
                    row[10] = b.float; row[11] = b.float
                    fb.put(row)
                }
                fb.position(0)
                val ib = ByteBuffer.allocateDirect(ni * 2).order(ByteOrder.nativeOrder()).asShortBuffer()
                for (i in 0 until ni) ib.put(b.short)
                ib.position(0)
                val tex = if (ti >= 0 && ti < names.size) texture(am, names[ti]) else 0
                val p = Part(mat, fb, nv, ib, ni, tex)
                p.gpu = true
                if (cut != 0) p.cut = 0.5f
                parts.add(p)
            }
            return Mesh(parts)
        } catch (e: Throwable) {
            return Mesh(emptyList())
        }
    }
}
