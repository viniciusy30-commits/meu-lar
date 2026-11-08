package com.vinicius.meular

import android.content.res.AssetManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.opengl.GLES20
import android.opengl.GLUtils
import kotlin.math.exp

/**
 * Etapa 116: cores de pele, sobrancelhas, olhos e lábios do corpo do Sims 4 (atlas sk_s4m.png / sk_s4f.png).
 *
 * As máscaras ficam em `cute/sk_s4m_mask.png` / `sk_s4f_mask.png` (R = pele, G = sobrancelhas, B = lábios) e
 * `sk_s4m_iris.png` / `sk_s4f_iris.png` (cinza = íris), geradas por `ferramentas/etapa116_mascaras_s4.py`.
 * Para cada região: saída = cor escolhida x (sombreado do pixel / sombreado médio da região), então o detalhe da textura
 * é mantido e só a cor muda (pele ainda mantém metade da variação de cor original). Cor "original" (-1) não mexe em nada.
 * Roda numa thread de fundo; a thread GL só sobe a textura pronta (glTexSubImage2D) em [upload].
 */
object S4Skin {
    private const val S_PELE = 0
    private const val S_OLHOS = 1
    private const val S_LABIOS = 12
    private const val S_SOBRANCELHA = 13

    private class Atlas(val tex: String, val sx: String) {
        var w = 0
        var h = 0
        var base = IntArray(0)
        var mk = IntArray(0)          // R pele, G sobrancelha, B lábios
        var ir = IntArray(0)          // íris (canal R)
        val ref = Array(4) { FloatArray(3) { 128f } }   // referência por região: 0 pele, 1 sobrancelha, 2 lábios, 3 íris
        var out = IntArray(0)
        var bmp: Bitmap? = null
        var loaded = false
        @Volatile var need = false     // a textura GL deste atlas existe
        @Volatile var pending = false
        var modified = false
    }

    private val atlases = arrayOf(Atlas("sk_s4m.png", "sk_s4m"), Atlas("sk_s4f.png", "sk_s4f"))
    private val lock = Any()
    @Volatile private var assets: AssetManager? = null
    @Volatile private var want = IntArray(CuteColor.SLOTS) { -1 }
    @Volatile private var failed = false
    private var working = false
    private var dirty = false

    fun setColors(cc: IntArray) {
        val c = IntArray(CuteColor.SLOTS) { -1 }
        for (i in c.indices) if (i < cc.size) c[i] = cc[i]
        synchronized(lock) { want = c; dirty = true }
        kick()
    }

    /** Contexto GL (re)criado: as texturas voltaram ao original, então as cores escolhidas sobem de novo. */
    fun start(am: AssetManager) {
        assets = am
        synchronized(lock) {
            for (a in atlases) { a.need = false; if (a.modified) a.pending = true }
            dirty = true
        }
        kick()
    }

    private fun kick() {
        val am = assets ?: return
        if (failed) return
        synchronized(lock) {
            if (working) return
            working = true
        }
        val t = Thread { work(am) }
        t.isDaemon = true
        t.name = "s4-skin"
        t.start()
    }

    /** Thread GL, todo quadro: ids das texturas de pele do Sims 4 (0 = ainda não existe) e sobe as cores prontas. */
    fun upload(texM: Int, texF: Int) {
        val ids = intArrayOf(texM, texF)
        var kickNow = false
        for (i in atlases.indices) {
            val a = atlases[i]
            if (ids[i] != 0 && !a.need) { a.need = true; kickNow = true }
            if (!a.pending || ids[i] == 0) continue
            synchronized(lock) {
                val b = a.bmp ?: return@synchronized
                if (!a.pending) return@synchronized
                a.pending = false
                GLES20.glActiveTexture(GLES20.GL_TEXTURE0)
                GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, ids[i])
                GLUtils.texSubImage2D(GLES20.GL_TEXTURE_2D, 0, 0, 0, b)
            }
        }
        if (kickNow) { synchronized(lock) { dirty = true }; kick() }
    }

    private fun work(am: AssetManager) {
        try {
            while (true) {
                val snap: IntArray
                synchronized(lock) {
                    if (!dirty) { working = false; return }
                    dirty = false
                    snap = want
                }
                val tg = arrayOfNulls<FloatArray>(4)
                val slots = intArrayOf(S_PELE, S_SOBRANCELHA, S_LABIOS, S_OLHOS)
                for (k in 0 until 4) {
                    val i = snap[slots[k]]
                    val p = CuteColor.palette(slots[k])
                    if (i >= 0 && i < p.size) tg[k] = floatArrayOf(Color.red(p[i]).toFloat(), Color.green(p[i]).toFloat(), Color.blue(p[i]).toFloat())
                }
                val ident = tg.all { it == null }
                for (a in atlases) {
                    if (!a.need) continue
                    if (ident && !a.modified) continue
                    if (!a.loaded) { load(am, a); a.loaded = true }
                    compute(a, tg)
                    val b = a.bmp ?: continue
                    synchronized(lock) {
                        b.setPixels(a.out, 0, a.w, 0, 0, a.w, a.h)
                        a.modified = !ident
                        a.pending = true
                    }
                }
            }
        } catch (e: Throwable) {
            failed = true
            synchronized(lock) { working = false }
        }
    }

    private fun decode(am: AssetManager, name: String): Bitmap {
        val o = BitmapFactory.Options()
        o.inPreferredConfig = Bitmap.Config.ARGB_8888
        return am.open("cute/$name").use { BitmapFactory.decodeStream(it, null, o) }!!
    }

    private fun load(am: AssetManager, a: Atlas) {
        val b = decode(am, a.tex)
        a.w = b.width; a.h = b.height
        val n = a.w * a.h
        a.base = IntArray(n); b.getPixels(a.base, 0, a.w, 0, 0, a.w, a.h)
        a.bmp = b.copy(Bitmap.Config.ARGB_8888, true)
        b.recycle()
        val m = decode(am, a.sx + "_mask.png"); a.mk = IntArray(n); m.getPixels(a.mk, 0, a.w, 0, 0, a.w, a.h); m.recycle()
        val r = decode(am, a.sx + "_iris.png"); a.ir = IntArray(n); r.getPixels(a.ir, 0, a.w, 0, 0, a.w, a.h); r.recycle()
        a.out = IntArray(n)
        // cor média de referência de cada região (pele: peso^4, como nas ferramentas)
        val sum = Array(4) { DoubleArray(4) }
        for (i in 0 until n) {
            val p = a.base[i]
            val pr = ((p shr 16) and 255).toDouble(); val pg = ((p shr 8) and 255).toDouble(); val pb = (p and 255).toDouble()
            val ws = w4(a.mk[i] shr 16 and 255)
            val wb = (a.mk[i] shr 8 and 255) / 255.0
            val wl = (a.mk[i] and 255) / 255.0
            val wi = (a.ir[i] shr 16 and 255) / 255.0
            val ww = doubleArrayOf(ws, wb, wl, wi)
            for (k in 0 until 4) { val w = ww[k]; if (w > 0) { sum[k][0] += pr * w; sum[k][1] += pg * w; sum[k][2] += pb * w; sum[k][3] += w } }
        }
        for (k in 0 until 4) if (sum[k][3] > 0) for (c in 0 until 3) a.ref[k][c] = (sum[k][c] / sum[k][3]).toFloat().coerceAtLeast(1f)
    }

    private fun w4(v: Int): Double { val w = v / 255.0; return w * w * w * w }

    private fun lum(r: Float, g: Float, b: Float) = 0.299f * r + 0.587f * g + 0.114f * b

    private fun knee(o: Float): Float = if (o <= 200f) o else 200f + 55f * (1f - exp(-(o - 200f) / 55f))

    private fun compute(a: Atlas, tg: Array<FloatArray?>) {
        val n = a.w * a.h
        val refL = FloatArray(4) { lum(a.ref[it][0], a.ref[it][1], a.ref[it][2]) }
        val col = FloatArray(3)
        for (i in 0 until n) {
            val p = a.base[i]
            val sk = a.mk[i] shr 16 and 255
            val br = a.mk[i] shr 8 and 255
            val lp = a.mk[i] and 255
            val ir = a.ir[i] shr 16 and 255
            if ((sk or br or lp or ir) == 0) { a.out[i] = p; continue }
            val pr = ((p shr 16) and 255).toFloat(); val pg = ((p shr 8) and 255).toFloat(); val pb = (p and 255).toFloat()
            var r = pr; var g = pg; var b = pb
            val l = lum(pr, pg, pb)
            for (k in 0 until 4) {
                val t = tg[k] ?: continue
                val w = (when (k) { 0 -> sk; 1 -> br; 2 -> lp; else -> ir }) / 255f
                if (w <= 0f) continue
                val rf = a.ref[k]
                val kk = l / refL[k]
                for (c in 0 until 3) {
                    val pc = if (c == 0) pr else if (c == 1) pg else pb
                    val kc = if (k == 0) 0.5f * pc / rf[c] + 0.5f * kk else kk
                    col[c] = knee(t[c] * kc).coerceIn(0f, 255f)
                }
                r = r * (1f - w) + col[0] * w
                g = g * (1f - w) + col[1] * w
                b = b * (1f - w) + col[2] * w
            }
            a.out[i] = (0xFF shl 24) or (r.toInt().coerceIn(0, 255) shl 16) or (g.toInt().coerceIn(0, 255) shl 8) or b.toInt().coerceIn(0, 255)
        }
    }
}
