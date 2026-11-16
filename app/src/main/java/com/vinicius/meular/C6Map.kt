package com.vinicius.meular

import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Typeface
import org.json.JSONObject
import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.max

/**
 * Cidade 6: dados do mapa (c6.json "mapa") — nomes das ruas com a posição e o ângulo para escrever no mapa, lugares
 * com ícone e a rede de ruas (trechos entre cruzamentos, com a curva de cada um) para o GPS achar o caminho mais curto.
 */
object C6Map {
    class Label(val x: Float, val z: Float, val ang: Float, val name: String, val kind: Int)
    @Volatile var labels: List<Label> = emptyList(); private set
    @Volatile var ready = false; private set
    private var nx = FloatArray(0); private var nz = FloatArray(0)
    private var ea = IntArray(0); private var eb = IntArray(0); private var elen = FloatArray(0); private var ename = IntArray(0)
    private var epts: Array<FloatArray> = emptyArray()
    private var names: Array<String> = emptyArray()
    private var adj: Array<IntArray> = emptyArray()

    fun load(m: JSONObject, cx: Float, cz: Float) {
        try {
            val ls = ArrayList<Label>()
            m.optJSONArray("rotulos")?.let { a -> for (i in 0 until a.length()) { val o = a.getJSONArray(i); ls.add(Label(o.getDouble(0).toFloat() + cx, o.getDouble(1).toFloat() + cz, o.getDouble(2).toFloat(), o.getString(3), o.getInt(4))) } }
            labels = ls
            val g = m.getJSONObject("grafo")
            val no = g.getJSONArray("nos"); val n = no.length() / 2
            nx = FloatArray(n) { no.getDouble(it * 2).toFloat() + cx }; nz = FloatArray(n) { no.getDouble(it * 2 + 1).toFloat() + cz }
            val ar = g.getJSONArray("arestas"); val e = ar.length()
            ea = IntArray(e); eb = IntArray(e); elen = FloatArray(e); ename = IntArray(e)
            epts = Array(e) { i ->
                val o = ar.getJSONArray(i); ea[i] = o.getInt(0); eb[i] = o.getInt(1); elen[i] = o.getDouble(2).toFloat(); ename[i] = o.getInt(3)
                val p = o.getJSONArray(4); FloatArray(p.length()) { k -> p.getDouble(k).toFloat() + (if (k % 2 == 0) cx else cz) }
            }
            val nm = g.getJSONArray("nomes"); names = Array(nm.length()) { nm.getString(it) }
            val lists = Array(n) { ArrayList<Int>() }
            for (i in 0 until e) { lists[ea[i]].add(i); lists[eb[i]].add(i) }
            adj = Array(n) { lists[it].toIntArray() }
            ready = n > 0
        } catch (t: Throwable) { ready = false }
    }

    /** ponto da rua mais perto: (aresta, segmento, t, x, z, distância ao início da aresta) */
    private fun snap(x: Float, z: Float): FloatArray {
        var best = Float.MAX_VALUE; val r = FloatArray(6)
        for (e in epts.indices) {
            val p = epts[e]; var acc = 0f
            var k = 0
            while (k + 3 < p.size) {
                val ax = p[k]; val az = p[k + 1]; val bx = p[k + 2]; val bz = p[k + 3]
                val dx = bx - ax; val dz = bz - az; val l2 = dx * dx + dz * dz; val l = kotlin.math.sqrt(l2)
                val t = if (l2 < 1e-6f) 0f else (((x - ax) * dx + (z - az) * dz) / l2).coerceIn(0f, 1f)
                val qx = ax + dx * t; val qz = az + dz * t
                val d = hypot(x - qx, z - qz)
                if (d < best) { best = d; r[0] = e.toFloat(); r[1] = (k / 2).toFloat(); r[2] = t; r[3] = qx; r[4] = qz; r[5] = acc + l * t }
                acc += l; k += 2
            }
        }
        return r
    }

    /** caminho mais curto pelas ruas: pontos (x, z) e o nome da rua de cada trecho */
    fun route(px: Float, pz: Float, dx: Float, dz: Float): Pair<FloatArray, Array<String>>? {
        if (!ready) return null
        val s = snap(px, pz); val t = snap(dx, dz)
        val es = s[0].toInt(); val et = t[0].toInt()
        val n = nx.size
        val dist = FloatArray(n) { Float.MAX_VALUE }; val prevE = IntArray(n) { -1 }; val done = BooleanArray(n)
        dist[ea[es]] = s[5]; dist[eb[es]] = elen[es] - s[5]
        val pq = java.util.PriorityQueue<Long>(64, compareBy { java.lang.Float.intBitsToFloat((it ushr 32).toInt()) })
        fun push(i: Int) { pq.add((java.lang.Float.floatToIntBits(dist[i]).toLong() shl 32) or i.toLong()) }
        push(ea[es]); push(eb[es])
        while (pq.isNotEmpty()) {
            val q = pq.poll()!!; val u = (q and 0xFFFFFFFFL).toInt()
            if (done[u]) continue; done[u] = true
            for (e in adj[u]) {
                val v = if (ea[e] == u) eb[e] else ea[e]
                val nd = dist[u] + elen[e]
                if (nd < dist[v]) { dist[v] = nd; prevE[v] = e; push(v) }
            }
        }
        val pts = ArrayList<Float>(); val nm = ArrayList<String>()
        fun add(x: Float, z: Float, name: String) {
            if (pts.size >= 2 && abs(pts[pts.size - 2] - x) < 0.05f && abs(pts[pts.size - 1] - z) < 0.05f) return
            if (pts.size >= 2) nm.add(name)
            pts.add(x); pts.add(z)
        }
        val sName = names.getOrElse(ename[es]) { "" }; val tName = names.getOrElse(ename[et]) { "" }
        add(px, pz, sName); add(s[3], s[4], sName)
        val da = dist[ea[et]] + t[5]; val db = dist[eb[et]] + (elen[et] - t[5])
        val direct = if (es == et) abs(t[5] - s[5]) else Float.MAX_VALUE
        if (direct <= minOf(da, db)) {
            // mesma rua: segue a curva da aresta entre os dois pontos
            walk(es, s, t, ::add, sName)
        } else {
            val endNode = if (da <= db) ea[et] else eb[et]
            // sequência de arestas do início até endNode
            val seq = ArrayList<Int>(); var v = endNode
            while (prevE[v] >= 0) { val e = prevE[v]; seq.add(e); v = if (ea[e] == v) eb[e] else ea[e] }
            seq.reverse()
            val startNode = v
            // trecho da aresta de partida até o nó de partida
            val p = epts[es]; val k = s[1].toInt()
            if (startNode == ea[es]) { var i = k; while (i >= 0) { add(p[i * 2], p[i * 2 + 1], sName); i-- } }
            else { var i = k + 1; while (i * 2 + 1 < p.size) { add(p[i * 2], p[i * 2 + 1], sName); i++ } }
            var cur = startNode
            for (e in seq) {
                val q = epts[e]; val nmE = names.getOrElse(ename[e]) { "" }
                if (ea[e] == cur) { var i = 0; while (i * 2 + 1 < q.size) { add(q[i * 2], q[i * 2 + 1], nmE); i++ }; cur = eb[e] }
                else { var i = q.size / 2 - 1; while (i >= 0) { add(q[i * 2], q[i * 2 + 1], nmE); i-- }; cur = ea[e] }
            }
            val r = epts[et]; val kt = t[1].toInt()
            if (endNode == ea[et]) { var i = 1; while (i <= kt) { add(r[i * 2], r[i * 2 + 1], tName); i++ } }
            else { var i = r.size / 2 - 2; while (i > kt) { add(r[i * 2], r[i * 2 + 1], tName); i-- } }
        }
        add(t[3], t[4], tName); add(dx, dz, tName)
        return Pair(pts.toFloatArray(), nm.toTypedArray())
    }

    private fun walk(e: Int, s: FloatArray, t: FloatArray, add: (Float, Float, String) -> Unit, name: String) {
        val p = epts[e]; val ks = s[1].toInt(); val kt = t[1].toInt()
        if (s[5] <= t[5]) { var i = ks + 1; while (i <= kt) { add(p[i * 2], p[i * 2 + 1], name); i++ } }
        else { var i = ks; while (i > kt) { add(p[i * 2], p[i * 2 + 1], name); i-- } }
    }

    /** nome da rua mais perto de um ponto (para o mapa e o HUD) */
    fun streetAt(x: Float, z: Float): String { if (!ready) return ""; val s = snap(x, z); return names.getOrElse(ename[s[0].toInt()]) { "" } }

    // ---------------------------------------------------------------- desenho dos nomes das ruas
    private val lp = Paint(Paint.ANTI_ALIAS_FLAG).apply { typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD); textAlign = Paint.Align.CENTER; color = 0xFF37474F.toInt() }
    private val lh = Paint(Paint.ANTI_ALIAS_FLAG).apply { typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD); textAlign = Paint.Align.CENTER; color = 0xF2FFFFFF.toInt(); style = Paint.Style.STROKE }

    /** chamado com o canvas já em coordenadas do mundo (s = pixels por metro), [rot] = giro do mapa em graus */
    fun drawLabels(c: Canvas, s: Float, dens: Float, rot: Float) {
        if (!ready || s < 0.45f) return
        for (l in labels) {
            if (l.kind == 0 && s < 0.9f) continue
            val size = (if (l.kind >= 2) 12.5f else 11f) * dens / s
            lp.textSize = size; lh.textSize = size; lh.strokeWidth = size * 0.3f
            lp.color = if (l.kind >= 2) 0xFF5D4037.toInt() else 0xFF37474F.toInt()
            c.save(); c.translate(l.x, l.z)
            var a = l.ang
            val eff = ((a + rot) % 360f + 360f) % 360f
            if (eff > 90f && eff < 270f) a += 180f        // texto nunca de cabeça para baixo
            c.rotate(a)
            c.drawText(l.name, 0f, size * 0.35f, lh); c.drawText(l.name, 0f, size * 0.35f, lp)
            c.restore()
        }
    }

    fun clear() { ready = false; labels = emptyList() }
    @Suppress("unused") private fun maxOf2(a: Float, b: Float) = max(a, b)
}
