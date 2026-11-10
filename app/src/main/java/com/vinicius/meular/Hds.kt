package com.vinicius.meular

import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Paint
import android.opengl.GLES20
import android.opengl.GLUtils
import org.json.JSONObject
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.sqrt

/**
 * Cidade 2: ruas, quarteirões e 17 casas (com interior) do Hds, prontas em assets/hds/city2.glb + city2.json.
 * A montagem (thread da cidade) junta as peças em pedaços de 64 m; o GL (City.service -> [gl]) sobe texturas e malhas aos poucos.
 * Telhado/forro de cada casa fica numa malha separada: some quando o jogador está dentro dela na vista de cima.
 * As casas não têm compra por enquanto: aparecem só marcadas nos mapas.
 */
object Hds {
    class Roof(val x0: Float, val z0: Float, val x1: Float, val z1: Float) { @Volatile var mesh: Mesh? = null }

    private class Acc { var v = FloatArray(STRIDE * 2048); var nv = 0; var idx = ShortArray(3072); var ni = 0 }
    private class Pend(val img: Int, val cut: Boolean, val mat: Int, val a: Acc)
    private class Group { val cur = HashMap<Int, Acc>(); val all = ArrayList<Pend>() }
    private class CG { val g = Group(); var x0 = 1e9f; var z0 = 1e9f; var x1 = -1e9f; var z1 = -1e9f; var h = 0f }
    private class Job(val chunk: City.Chunk?, val roof: Roof?, val pends: List<Pend>)

    @Volatile var roofs: List<Roof> = emptyList()
    @Volatile var minX = 0f; @Volatile var maxX = 0f; @Volatile var minZ = 0f; @Volatile var maxZ = 0f
    @Volatile private var model: GModel? = null
    private val jobs = java.util.concurrent.ConcurrentLinkedQueue<Job>()
    private var texIds = IntArray(0)
    private var clampImg = BooleanArray(0)
    private var texGen = -1

    // dados do mapa (já deslocados para a posição do lote do jogador)
    @Volatile private var mxr = FloatArray(0)
    @Volatile private var mzr = FloatArray(0)
    @Volatile private var mplots: List<FloatArray> = emptyList()

    private const val CELL = 64f
    private const val PAD = 0.15f

    /** jogador dentro da caixa de alguma casa? (câmera usa plano próximo menor) */
    fun inside(x: Float, z: Float): Boolean { for (r in roofs) if (x > r.x0 && x < r.x1 && z > r.z0 && z < r.z1) return true; return false }

    fun clear() {
        jobs.clear()
        for (r in roofs) r.mesh?.release()
        roofs = emptyList()
        model = null
        if (texIds.any { it != 0 }) { try { GLES20.glDeleteTextures(texIds.size, texIds, 0) } catch (e: Throwable) { } }
        texIds = IntArray(0)
        mxr = FloatArray(0); mzr = FloatArray(0); mplots = emptyList()
    }

    private fun addPrim(g: Group, p: GPrim, m: FloatArray, ox: Float, oz: Float, cg: CG?) {
        val key = ((p.img + 1) shl 12) or (p.mat shl 1) or (if (p.cut) 1 else 0)
        var a = g.cur[key]
        if (a == null || a.nv + p.nv > 65000) {
            a = Acc(); g.cur[key] = a; g.all.add(Pend(p.img, p.cut, p.mat, a))
        }
        val need = (a.nv + p.nv) * STRIDE
        if (need > a.v.size) a.v = a.v.copyOf(maxOf(need, a.v.size * 2))
        if (a.ni + p.idx.size > a.idx.size) a.idx = a.idx.copyOf(maxOf(a.ni + p.idx.size, a.idx.size * 2))
        val base = a.nv
        for (i in 0 until p.nv) {
            val s = i * STRIDE; val d = (base + i) * STRIDE
            System.arraycopy(p.v, s, a.v, d, STRIDE)
            val x = p.v[s]; val y = p.v[s + 1]; val z = p.v[s + 2]
            val wx = m[0] * x + m[1] * y + m[2] * z + m[3] + ox
            val wy = m[4] * x + m[5] * y + m[6] * z + m[7]
            val wz = m[8] * x + m[9] * y + m[10] * z + m[11] + oz
            a.v[d] = wx; a.v[d + 1] = wy; a.v[d + 2] = wz
            val nx = p.v[s + 3]; val ny = p.v[s + 4]; val nz = p.v[s + 5]
            var tx = m[0] * nx + m[1] * ny + m[2] * nz
            var ty = m[4] * nx + m[5] * ny + m[6] * nz
            var tz = m[8] * nx + m[9] * ny + m[10] * nz
            val l = sqrt(tx * tx + ty * ty + tz * tz)
            if (l > 1e-6f) { tx /= l; ty /= l; tz /= l }
            a.v[d + 3] = tx; a.v[d + 4] = ty; a.v[d + 5] = tz
            if (cg != null) {
                if (wx < cg.x0) cg.x0 = wx; if (wx > cg.x1) cg.x1 = wx
                if (wz < cg.z0) cg.z0 = wz; if (wz > cg.z1) cg.z1 = wz
                if (wy > cg.h) cg.h = wy
            }
        }
        a.nv += p.nv
        // Etapa 164: descarta triângulos repetidos no mesmo lugar do mundo (causavam o piscar por disputa de profundidade)
        var k = 0
        while (k + 2 < p.idx.size) {
            val i0 = p.idx[k].toInt() and 0xFFFF; val i1 = p.idx[k + 1].toInt() and 0xFFFF; val i2 = p.idx[k + 2].toInt() and 0xFFFF
            val h = vh(a.v, (base + i0) * STRIDE) + vh(a.v, (base + i1) * STRIDE) + vh(a.v, (base + i2) * STRIDE)
            if (seen.add(h)) {
                a.idx[a.ni] = (i0 + base).toShort(); a.idx[a.ni + 1] = (i1 + base).toShort(); a.idx[a.ni + 2] = (i2 + base).toShort()
                a.ni += 3
            } else dropped++
            k += 3
        }
    }

    private val seen = HashSet<Long>()
    private var dropped = 0
    /** hash de um vértice (posição em passos de 2 cm); a soma dos 3 não depende da ordem */
    private fun vh(v: FloatArray, o: Int): Long {
        var h = Math.round(v[o] * 50f).toLong() * 73856093L xor Math.round(v[o + 1] * 50f).toLong() * 19349663L xor Math.round(v[o + 2] * 50f).toLong() * 83492791L
        h = (h xor (h ushr 31)) * -0x61c8864680b583ebL
        return h xor (h ushr 29)
    }

    /** Thread da cidade. Preenche [out] com os pedaços (malhas chegam depois, pelo GL) e registra colisões e marcadores. */
    fun build(out: ArrayList<City.Chunk>, W: Float, H: Float, tk: Int) {
        clear()
        seen.clear(); dropped = 0
        val am = Glb.assets ?: throw IllegalStateException("assets ainda não prontos")
        City.step(0.05f)
        val gm = Glb.parse(am.open("hds/city2.glb").use { it.readBytes() }, "city2")
        City.step(0.4f)
        val js = JSONObject(am.open("hds/city2.json").bufferedReader().use { it.readText() })
        City.step(0.5f)
        val res = js.getJSONArray("res")
        val ox = (City.lotX0 + City.lotX1) / 2f - res.getDouble(0).toFloat()
        val oz = (City.lotZ0 + City.lotZ1) / 2f - res.getDouble(1).toFloat()
        val plots = js.getJSONArray("plots"); val np = plots.length()

        val clamp = BooleanArray(gm.images.size)
        for (n in gm.nodes) for (p in n.prims) if (p.cut && p.img in clamp.indices) clamp[p.img] = true

        val roofG = Array(np) { Group() }
        val cells = HashMap<Long, CG>()
        val inst = js.getJSONArray("inst")
        val m = FloatArray(12)
        for (j in 0 until inst.length()) {
            val a = inst.getJSONArray(j)
            val pi = a.getInt(0)
            for (k in 0 until 12) m[k] = a.getDouble(1 + k).toFloat()
            val kind = a.getInt(13); val plot = a.getInt(14)
            val node = gm.nodes.getOrNull(pi) ?: continue
            if (node.prims.isEmpty()) continue
            if (kind == 2 && plot in 0 until np) {
                for (p in node.prims) addPrim(roofG[plot], p, m, ox, oz, null)
            } else {
                val cx = Math.floor(((m[3] + ox) / CELL).toDouble()).toInt(); val cz = Math.floor(((m[11] + oz) / CELL).toDouble()).toInt()
                val key = (cx + 4096).toLong() * 65536L + (cz + 4096).toLong()
                val cg = cells.getOrPut(key) { CG() }
                for (p in node.prims) addPrim(cg.g, p, m, ox, oz, cg)
            }
            if (j % 256 == 0) City.step(0.5f + 0.4f * j / inst.length())
        }

        for (cg in cells.values) {
            if (cg.g.all.isEmpty()) continue
            val c = City.Chunk(null, null, cg.x0 - 0.5f, cg.z0 - 0.5f, cg.x1 + 0.5f, cg.z1 + 0.5f, cg.h + 0.5f)
            out.add(c)
            jobs.add(Job(c, null, cg.g.all))
        }
        val rl = ArrayList<Roof>()
        val pl = ArrayList<FloatArray>()
        for (k in 0 until np) {
            val b = plots.getJSONObject(k)
            val x0 = b.getDouble("x0").toFloat() + ox; val z0 = b.getDouble("z0").toFloat() + oz
            val x1 = b.getDouble("x1").toFloat() + ox; val z1 = b.getDouble("z1").toFloat() + oz
            pl.add(floatArrayOf(x0, z0, x1, z1))
            val r = Roof(x0 - 0.3f, z0 - 0.3f, x1 + 0.3f, z1 + 0.3f)
            rl.add(r)
            if (roofG[k].all.isNotEmpty()) jobs.add(Job(null, r, roofG[k].all))
            City.addPlace(City.Place("Casa ${k + 1}", (x0 + x1) / 2f, (z0 + z1) / 2f, 0xFFFF7043.toInt(), 'C'))
        }

        // colisões (paredes e cercas, já com os vãos de porta)
        val so = js.getJSONArray("solids")
        var i = 0
        while (i + 3 < so.length()) {
            City.addSolid(floatArrayOf(so.getDouble(i).toFloat() + ox - PAD, so.getDouble(i + 1).toFloat() + oz - PAD, so.getDouble(i + 2).toFloat() + ox + PAD, so.getDouble(i + 3).toFloat() + oz + PAD))   // Etapa 164: folga = raio do corpo
            i += 4
        }

        val bd = js.getJSONArray("bounds")
        minX = bd.getDouble(0).toFloat() + ox - 250f; minZ = bd.getDouble(1).toFloat() + oz - 250f
        maxX = bd.getDouble(2).toFloat() + ox + 250f; maxZ = bd.getDouble(3).toFloat() + oz + 250f
        val xa = js.getJSONArray("xr"); val za = js.getJSONArray("zr")
        mxr = FloatArray(xa.length()) { xa.getDouble(it).toFloat() + ox }
        mzr = FloatArray(za.length()) { za.getDouble(it).toFloat() + oz }
        android.util.Log.i("Hds", "triângulos repetidos descartados: $dropped")
        seen.clear()
        mplots = pl
        clampImg = clamp
        roofs = rl
        model = gm
        City.alive()
    }

    private fun tex(gm: GModel, i: Int): Int {
        if (i < 0 || i >= texIds.size) return 0
        if (texIds[i] != 0) return texIds[i]
        val b = gm.images[i]
        try {
            val opt = BitmapFactory.Options().apply { inPremultiplied = false }
            val bmp = BitmapFactory.decodeByteArray(b, 0, b.size, opt) ?: return 0
            val ids = IntArray(1); GLES20.glGenTextures(1, ids, 0)
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, ids[0])
            GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bmp, 0)
            GLES20.glGenerateMipmap(GLES20.GL_TEXTURE_2D)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR_MIPMAP_LINEAR)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
            val w = if (i < clampImg.size && clampImg[i]) GLES20.GL_CLAMP_TO_EDGE else GLES20.GL_REPEAT
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, w)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, w)
            bmp.recycle()
            texIds[i] = ids[0]
        } catch (e: Throwable) {
            android.util.Log.e("Hds", "textura $i falhou", e)
        }
        return texIds[i]
    }

    /** Thread do GL: sobe as malhas prontas aos poucos (uns 10 ms por quadro), para a cidade aparecer sem travar. */
    fun gl() {
        if (jobs.isEmpty()) return
        val gm = model ?: return
        if (texGen != GlGen.gen || texIds.size != gm.images.size) { texGen = GlGen.gen; texIds = IntArray(gm.images.size) }
        val t0 = System.nanoTime()
        while (true) {
            val job = jobs.poll() ?: break
            val parts = ArrayList<Part>()
            for (pe in job.pends) {
                val a = pe.a
                if (a.nv == 0 || a.ni == 0) continue
                val fb = ByteBuffer.allocateDirect(a.nv * STRIDE * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
                fb.put(a.v, 0, a.nv * STRIDE); fb.position(0)
                val ib = ByteBuffer.allocateDirect(a.ni * 2).order(ByteOrder.nativeOrder()).asShortBuffer()
                ib.put(a.idx, 0, a.ni); ib.position(0)
                val part = Part(pe.mat, fb, a.nv, ib, a.ni, tex(gm, pe.img))
                part.gpu = true
                if (pe.cut) part.cut = 0.5f
                parts.add(part)
                a.v = FloatArray(0); a.idx = ShortArray(0)   // devolve a memória da cópia em arrays
            }
            if (parts.isNotEmpty()) {
                val mesh = Mesh(parts).gpuOnly()
                job.chunk?.let { it.near = mesh }
                job.roof?.mesh = mesh
            }
            if (System.nanoTime() - t0 > 10_000_000L) break
        }
        if (jobs.isEmpty()) model = null   // texturas já estão na placa: solta o GLB da memória
    }

    /** Ruas, calçadas, quarteirões e casas no mapa (mundo já em metros do jogo). */
    fun drawMap(c: Canvas, fill: Paint, road: Paint) {
        val xs = mxr; val zs = mzr
        if (xs.isEmpty() || zs.isEmpty()) return
        fill.color = 0xFFC5E1A5.toInt()
        c.drawRect(minX, minZ, maxX, maxZ, fill)
        fill.color = 0xFFDCD8D0.toInt()
        for (z in zs) c.drawRect(xs[0] - 8f, z - 8f, xs[xs.size - 1] + 8f, z + 8f, fill)
        for (x in xs) c.drawRect(x - 8f, zs[0] - 8f, x + 8f, zs[zs.size - 1] + 8f, fill)
        val oldStyle = road.style
        road.style = Paint.Style.FILL
        for (z in zs) c.drawRect(xs[0] - 5.2f, z - 5.2f, xs[xs.size - 1] + 5.2f, z + 5.2f, road)
        for (x in xs) c.drawRect(x - 5.2f, zs[0] - 5.2f, x + 5.2f, zs[zs.size - 1] + 5.2f, road)
        road.style = oldStyle
        fill.color = 0xFFBCAAA4.toInt()
        for (p in mplots) c.drawRect(p[0], p[1], p[2], p[3], fill)
    }
}
