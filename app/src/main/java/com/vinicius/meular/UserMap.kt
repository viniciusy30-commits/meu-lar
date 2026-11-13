package com.vinicius.meular

import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.ceil
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min

/**
 * Etapa 187: mapa criado pelo jogador (Cidade 4). O editor (MapEditorActivity) mexe nesta lista de ruas, rotatórias,
 * casas, árvores e no relevo; compile() converte tudo para o mesmo formato que o Relevo.kt já lê (ruas, rotatórias,
 * pontes, viadutos, relevo em células de 8 m), com cruzamentos, pontes sobre a água, viadutos, becos sem saída e postes automáticos.
 */
object UserMap {
    const val WX = 1000f
    const val WZ = 800f
    const val G = 8f
    const val NX = 126
    const val NZ = 101
    const val BASE = 6.0f
    const val K_STREET = 0
    const val K_AVENUE = 1
    const val K_HIGHWAY = 2
    const val K_VIADUCT = 3
    const val MAX_HOUSES = 17

    class Road(val kind: Int, val pts: ArrayList<FloatArray>)
    class Hub(var x: Float, var z: Float, var r: Float)
    class Hs(val k: Int, var x: Float, var z: Float)
    class Tree(var x: Float, var z: Float, val sp: Int, val sc: Float, val rot: Float, val tone: Float)
    class Compiled(val json: JSONObject, val hs: ShortArray)

    val roads = ArrayList<Road>()
    val hubs = ArrayList<Hub>()
    val houses = ArrayList<Hs>()
    val trees = ArrayList<Tree>()
    var hs = ShortArray(NX * NZ)
    /** sobe a cada gravação; o jogo remonta a Cidade 4 quando muda */
    @Volatile var ver = 0
    private var dir: File? = null
    private var loaded = false

    fun init(d: File) {
        dir = d
        ensure()
    }

    @Synchronized fun ensure() {
        if (loaded) return
        loaded = true
        val f = File(dir ?: return, "usermap.json")
        try {
            if (f.exists()) { fromJson(JSONObject(f.readText())); if (houses.none { it.k == 0 }) defaultMap(); return }
        } catch (e: Throwable) {
            android.util.Log.w("UserMap", "mapa salvo ilegível: $e")
        }
        defaultMap()
    }

    @Synchronized fun defaultMap() {
        roads.clear(); hubs.clear(); houses.clear(); trees.clear()
        for (i in hs.indices) hs[i] = (BASE * 100).toInt().toShort()
        houses.add(Hs(0, 500f, 400f))
        roads.add(Road(K_STREET, arrayListOf(floatArrayOf(160f, 382.4f), floatArrayOf(500f, 382.4f), floatArrayOf(840f, 382.4f))))
    }

    @Synchronized fun toJson(): JSONObject {
        val o = JSONObject()
        val ra = JSONArray()
        for (r in roads) {
            val ro = JSONObject(); ro.put("k", r.kind)
            val p = JSONArray()
            for (q in r.pts) { p.put(q[0].toDouble()); p.put(q[1].toDouble()) }
            ro.put("p", p); ra.put(ro)
        }
        o.put("roads", ra)
        val ha = JSONArray(); for (h in hubs) { ha.put(h.x.toDouble()); ha.put(h.z.toDouble()); ha.put(h.r.toDouble()) }
        o.put("hubs", ha)
        val sa = JSONArray(); for (h in houses) { sa.put(h.k); sa.put(h.x.toDouble()); sa.put(h.z.toDouble()) }
        o.put("houses", sa)
        val ta = JSONArray(); for (t in trees) { ta.put(t.x.toDouble()); ta.put(t.z.toDouble()); ta.put(t.sp); ta.put(t.sc.toDouble()); ta.put(t.rot.toDouble()); ta.put(t.tone.toDouble()) }
        o.put("trees", ta)
        val ga = JSONArray(); for (v in hs) ga.put(v.toInt())
        o.put("hs", ga)
        return o
    }

    @Synchronized fun fromJson(o: JSONObject) {
        roads.clear(); hubs.clear(); houses.clear(); trees.clear()
        val ra = o.getJSONArray("roads")
        for (i in 0 until ra.length()) {
            val ro = ra.getJSONObject(i); val p = ro.getJSONArray("p")
            val l = ArrayList<FloatArray>()
            var k = 0
            while (k + 1 < p.length()) { l.add(floatArrayOf(p.getDouble(k).toFloat(), p.getDouble(k + 1).toFloat())); k += 2 }
            roads.add(Road(ro.getInt("k"), l))
        }
        val ha = o.getJSONArray("hubs"); var i = 0
        while (i + 2 < ha.length()) { hubs.add(Hub(ha.getDouble(i).toFloat(), ha.getDouble(i + 1).toFloat(), ha.getDouble(i + 2).toFloat())); i += 3 }
        val sa = o.getJSONArray("houses"); i = 0
        while (i + 2 < sa.length()) { houses.add(Hs(sa.getInt(i), sa.getDouble(i + 1).toFloat(), sa.getDouble(i + 2).toFloat())); i += 3 }
        val ta = o.getJSONArray("trees"); i = 0
        while (i + 5 < ta.length()) {
            trees.add(Tree(ta.getDouble(i).toFloat(), ta.getDouble(i + 1).toFloat(), ta.getInt(i + 2), ta.getDouble(i + 3).toFloat(), ta.getDouble(i + 4).toFloat(), ta.getDouble(i + 5).toFloat()))
            i += 6
        }
        val ga = o.getJSONArray("hs")
        if (ga.length() == hs.size) for (j in hs.indices) hs[j] = ga.getInt(j).toShort()
    }

    @Synchronized fun save() {
        try { File(dir ?: return, "usermap.json").writeText(toJson().toString()) } catch (e: Throwable) { android.util.Log.w("UserMap", "falha ao salvar: $e") }
        ver++
    }

    // ---------------------------------------------------------------- relevo (pincéis do editor)
    private fun ss(t: Float): Float { val c = t.coerceIn(0f, 1f); return c * c * (3f - 2f * c) }

    /** modo 0 = água (cava), 1 = sobe, 2 = desce, 3 = nivela (volta ao nível base) */
    @Synchronized fun brush(x: Float, z: Float, r: Float, mode: Int) {
        val i0 = max(0, ((x - r * 1.7f) / G).toInt()); val i1 = min(NX - 1, ((x + r * 1.7f) / G).toInt() + 1)
        val j0 = max(0, ((z - r * 1.7f) / G).toInt()); val j1 = min(NZ - 1, ((z + r * 1.7f) / G).toInt() + 1)
        for (j in j0..j1) for (i in i0..i1) {
            val d = hypot(i * G - x, j * G - z)
            val k = j * NX + i
            val old = hs[k] / 100f
            var nv = old
            when (mode) {
                0 -> { val t = ss((d - r * 0.55f) / (r * 1.1f)); val tg = -2.6f * (1f - t) + old * t; if (tg < old) nv = tg }
                1 -> { val w = ss(1f - d / (r * 1.4f)); nv = min(40f, old + 0.9f * w) }
                2 -> { val w = ss(1f - d / (r * 1.4f)); nv = max(-6f, old - 0.9f * w) }
                else -> { val w = ss(1f - d / (r * 1.5f)); nv = old + (BASE - old) * w * 0.7f }
            }
            hs[k] = (nv * 100f).toInt().toShort()
        }
    }

    // ---------------------------------------------------------------- geometria
    /** suaviza os pontos tocados (Catmull-Rom) e reamostra a cada ~5 m */
    fun smooth(p: List<FloatArray>): ArrayList<FloatArray> {
        val out = ArrayList<FloatArray>()
        val n = p.size
        if (n < 2) { for (q in p) out.add(floatArrayOf(q[0], q[1])); return out }
        for (i in 0 until n - 1) {
            val p0 = p[max(i - 1, 0)]; val p1 = p[i]; val p2 = p[i + 1]; val p3 = p[min(i + 2, n - 1)]
            val len = hypot(p2[0] - p1[0], p2[1] - p1[1])
            val steps = max(1, ceil(len / 5f).toInt())
            for (s in 0 until steps) {
                val t = s.toFloat() / steps; val t2 = t * t; val t3 = t2 * t
                val x = 0.5f * ((2f * p1[0]) + (-p0[0] + p2[0]) * t + (2f * p0[0] - 5f * p1[0] + 4f * p2[0] - p3[0]) * t2 + (-p0[0] + 3f * p1[0] - 3f * p2[0] + p3[0]) * t3)
                val z = 0.5f * ((2f * p1[1]) + (-p0[1] + p2[1]) * t + (2f * p0[1] - 5f * p1[1] + 4f * p2[1] - p3[1]) * t2 + (-p0[1] + 3f * p1[1] - 3f * p2[1] + p3[1]) * t3)
                out.add(floatArrayOf(x, z))
            }
        }
        out.add(floatArrayOf(p[n - 1][0], p[n - 1][1]))
        return out
    }

    fun kindWidth(kind: Int): Float = when (kind) { K_STREET -> 7.4f; K_AVENUE -> 9.0f; K_HIGHWAY -> 14.0f; else -> 10.0f }

    private fun hAt(h: ShortArray, x: Float, z: Float): Float {
        val fx = (x / G).coerceIn(0f, NX - 1.001f); val fz = (z / G).coerceIn(0f, NZ - 1.001f)
        val i = fx.toInt(); val j = fz.toInt(); val tx = fx - i; val tz = fz - j
        val a = h[j * NX + i] / 100f; val b = h[j * NX + i + 1] / 100f; val c = h[(j + 1) * NX + i] / 100f; val d = h[(j + 1) * NX + i + 1] / 100f
        return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz
    }

    private fun flat(h: ShortArray, cx: Float, cz: Float, lvl: Float, r0: Float, r1: Float) {
        val i0 = max(0, ((cx - r1) / G).toInt()); val i1 = min(NX - 1, ((cx + r1) / G).toInt() + 1)
        val j0 = max(0, ((cz - r1) / G).toInt()); val j1 = min(NZ - 1, ((cz + r1) / G).toInt() + 1)
        for (j in j0..j1) for (i in i0..i1) {
            val d = hypot(i * G - cx, j * G - cz)
            if (d >= r1) continue
            val t = ss((d - r0) / (r1 - r0))
            val old = h[j * NX + i] / 100f
            h[j * NX + i] = ((lvl * (1f - t) + old * t) * 100f).toInt().toShort()
        }
    }

    private class CR(val src: Road, var x: FloatArray, var z: FloatArray) {
        val c = when (src.kind) { K_STREET -> 4; K_AVENUE -> 5; else -> 1 }
        val w = kindWidth(src.kind)
        val hw = w / 2f
        var cs = FloatArray(0)
        val gaps = ArrayList<FloatArray>()
        var ta = 0f
        var tb = 0f
        var sHub = -1
        var eHub = -1
        var sJ = false
        var eJ = false
        val viaduct = src.kind == K_VIADUCT
        fun len(): Float = if (cs.isEmpty()) 0f else cs[cs.size - 1]
        fun calc() {
            cs = FloatArray(x.size)
            for (q in 1 until x.size) cs[q] = cs[q - 1] + hypot(x[q] - x[q - 1], z[q] - z[q - 1])
        }
    }

    /** distância do ponto à poligonal e o arco (s) do ponto mais próximo */
    private fun nearest(r: CR, px: Float, pz: Float): FloatArray {
        var bd = 1e9f; var bs = 0f; var bx = px; var bz = pz
        for (q in 0 until r.x.size - 1) {
            val vx = r.x[q + 1] - r.x[q]; val vz = r.z[q + 1] - r.z[q]
            val l2 = vx * vx + vz * vz
            if (l2 < 1e-6f) continue
            val t = (((px - r.x[q]) * vx + (pz - r.z[q]) * vz) / l2).coerceIn(0f, 1f)
            val cx = r.x[q] + vx * t; val cz = r.z[q] + vz * t
            val d = hypot(px - cx, pz - cz)
            if (d < bd) { bd = d; bs = r.cs[q] + t * sqrtf(l2); bx = cx; bz = cz }
        }
        return floatArrayOf(bd, bs, bx, bz)
    }

    private fun sqrtf(v: Float): Float = Math.sqrt(v.toDouble()).toFloat()

    private fun addGap(r: CR, a: Float, b: Float) { r.gaps.add(floatArrayOf(a, b)) }

    private fun merged(r: CR): JSONArray {
        val l = r.gaps.sortedBy { it[0] }
        val out = JSONArray()
        var a = 0f; var b = 0f; var have = false
        for (g in l) {
            if (!have) { a = g[0]; b = g[1]; have = true }
            else if (g[0] <= b) b = max(b, g[1])
            else { out.put(round2(a)); out.put(round2(b)); a = g[0]; b = g[1] }
        }
        if (have) { out.put(round2(a)); out.put(round2(b)) }
        return out
    }

    private fun round2(v: Float): Double = Math.round(v * 100f) / 100.0

    private fun atArc(r: CR, s: Float): FloatArray {
        var q = 0
        while (q < r.cs.size - 2 && r.cs[q + 1] < s) q++
        val l = r.cs[q + 1] - r.cs[q]
        val t = if (l > 1e-4f) ((s - r.cs[q]) / l).coerceIn(0f, 1f) else 0f
        var tx = r.x[q + 1] - r.x[q]; var tz = r.z[q + 1] - r.z[q]
        val tl = hypot(tx, tz).coerceAtLeast(1e-4f); tx /= tl; tz /= tl
        return floatArrayOf(r.x[q] + (r.x[q + 1] - r.x[q]) * t, r.z[q] + (r.z[q + 1] - r.z[q]) * t, tx, tz, q.toFloat())
    }

    /** Converte o mapa do jogador para o formato do Relevo (ver sub.json). Sempre tem a Casa 1. */
    @Synchronized fun compile(): Compiled {
        ensure()
        if (houses.none { it.k == 0 }) houses.add(Hs(0, WX / 2f, WZ / 2f))
        val H = hs.copyOf()
        // casas e rotatórias ficam em platôs
        val lvls = HashMap<Int, Float>()
        for (h in houses) {
            val lv = max(hAt(hs, h.x, h.z), 2.5f)
            lvls[h.k] = Math.round(lv * 20f) / 20f
            flat(H, h.x, h.z, lvls[h.k]!!, 22f, 42f)
        }
        val hubLv = FloatArray(hubs.size)
        for ((i, hb) in hubs.withIndex()) {
            hubLv[i] = max(hAt(H, hb.x, hb.z), 2.0f)
            flat(H, hb.x, hb.z, hubLv[i], hb.r + 6f, hb.r + 20f)
        }

        // ---- ruas: suaviza, encaixa nas rotatórias
        val cr = ArrayList<CR>()
        val arms = HashMap<Int, ArrayList<Float>>()
        fun addArm(hi: Int, e: FloatArray, kind: Int) {
            val hb = hubs[hi]
            var ux = e[0] - hb.x; var uz = e[1] - hb.z
            val l = hypot(ux, uz).coerceAtLeast(1e-3f); ux /= l; uz /= l
            val l2 = arms.getOrPut(hi) { ArrayList() }
            l2.add(e[0] - hb.x); l2.add(e[1] - hb.z); l2.add(ux); l2.add(uz); l2.add(kindWidth(kind) / 2f)
        }
        for (r in roads) {
            if (r.pts.size < 2) continue
            val pts = ArrayList<FloatArray>()
            for (q in r.pts) pts.add(floatArrayOf(q[0].coerceIn(2f, WX - 2f), q[1].coerceIn(2f, WZ - 2f)))
            var sh = -1; var eh = -1
            if (r.kind != K_VIADUCT) {
                sh = snapHub(pts, 0, 1); eh = snapHub(pts, pts.size - 1, pts.size - 2)
                if (sh >= 0) addArm(sh, pts[0], r.kind)
                if (eh >= 0) addArm(eh, pts[pts.size - 1], r.kind)
            }
            val sm = smooth(pts)
            val c = CR(r, FloatArray(sm.size) { sm[it][0] }, FloatArray(sm.size) { sm[it][1] })
            c.sHub = sh; c.eHub = eh
            cr.add(c)
        }
        // pontas encaixadas em outra rua (T) ou soltas
        class Jn(val a: CR, val atEnd: Boolean, val b: CR, val px: Float, val pz: Float)
        val jns = ArrayList<Jn>()
        for (c in cr) c.calc()
        for (c in cr) {
            if (c.viaduct) continue
            for (end in 0..1) {
                if ((end == 0 && c.sHub >= 0) || (end == 1 && c.eHub >= 0)) continue
                val ex = if (end == 0) c.x[0] else c.x[c.x.size - 1]; val ez = if (end == 0) c.z[0] else c.z[c.z.size - 1]
                var best: CR? = null; var bd = 3.4f; var bpx = 0f; var bpz = 0f
                for (o in cr) {
                    if (o === c || o.viaduct) continue
                    val nr = nearest(o, ex, ez)
                    if (nr[0] < bd) { bd = nr[0]; best = o; bpx = nr[2]; bpz = nr[3] }
                }
                if (best != null) {
                    if (end == 0) { c.x[0] = bpx; c.z[0] = bpz; c.sJ = true } else { c.x[c.x.size - 1] = bpx; c.z[c.z.size - 1] = bpz; c.eJ = true }
                    jns.add(Jn(c, end == 1, best, bpx, bpz))
                }
            }
        }
        for (c in cr) c.calc()
        for (j in jns) {
            val sb = nearest(j.b, j.px, j.pz)[1]
            addGap(j.b, sb - j.a.hw - 0.7f, sb + j.a.hw + 0.7f)
            if (j.atEnd) { addGap(j.a, j.a.len() - j.b.hw - 0.7f, j.a.len() + 1f); j.a.tb = j.b.hw + 1f }
            else { addGap(j.a, -1f, j.b.hw + 0.7f); j.a.ta = j.b.hw + 1f }
        }
        // cruzamentos (X)
        for (ai in 0 until cr.size) for (bi in ai + 1 until cr.size) {
            val a = cr[ai]; val b = cr[bi]
            if (a.viaduct || b.viaduct) continue
            for (i in 0 until a.x.size - 1) for (j in 0 until b.x.size - 1) {
                val x1 = a.x[i]; val z1 = a.z[i]; val x2 = a.x[i + 1]; val z2 = a.z[i + 1]
                val x3 = b.x[j]; val z3 = b.z[j]; val x4 = b.x[j + 1]; val z4 = b.z[j + 1]
                val den = (x2 - x1) * (z4 - z3) - (z2 - z1) * (x4 - x3)
                if (abs(den) < 1e-5f) continue
                val t = ((x3 - x1) * (z4 - z3) - (z3 - z1) * (x4 - x3)) / den
                val u = ((x3 - x1) * (z2 - z1) - (z3 - z1) * (x2 - x1)) / den
                if (t < 0f || t > 1f || u < 0f || u > 1f) continue
                val sa = a.cs[i] + t * (a.cs[i + 1] - a.cs[i]); val sb = b.cs[j] + u * (b.cs[j + 1] - b.cs[j])
                addGap(a, sa - b.hw - 0.7f, sa + b.hw + 0.7f)
                addGap(b, sb - a.hw - 0.7f, sb + a.hw + 0.7f)
            }
        }

        val roadsJ = JSONArray(); val nodesJ = JSONArray(); val lampJ = JSONArray()
        var nameN = 1
        for (c in cr) {
            val n = c.x.size
            if (n < 2) continue
            val gy = FloatArray(n) { hAt(H, c.x[it], c.z[it]) }
            val br = BooleanArray(n)
            val y = FloatArray(n)
            val S = c.len()
            if (c.viaduct) {
                val ramp = min(45f, S * 0.4f).coerceAtLeast(1f)
                for (q in 0 until n) {
                    val t = (min(c.cs[q], S - c.cs[q]) / ramp).coerceIn(0f, 1f)
                    y[q] = gy[q] + 6.8f * ss(t); br[q] = true
                }
            } else {
                val wet = BooleanArray(n) { gy[it] < -0.25f }
                for (q in 0 until n) { if (wet[q]) for (k in -2..2) { val m = q + k; if (m in 0 until n) br[m] = true } }
                for (q in 0 until n) y[q] = gy[q]
                var q = 0
                while (q < n) {
                    if (!br[q]) { q++; continue }
                    var e = q; while (e + 1 < n && br[e + 1]) e++
                    val ya = if (q > 0) y[q - 1] else if (e + 1 < n) y[e + 1] else max(gy[q], 2f)
                    val yb = if (e + 1 < n) y[e + 1] else ya
                    val lo = max(max(ya, yb), 0.8f)
                    for (m in q..e) y[m] = if (max(ya, yb) < 0.8f) lo else ya + (yb - ya) * (m - q + 1f) / (e - q + 2f)
                    q = e + 1
                }
            }
            val ro = JSONObject()
            ro.put("c", c.c); ro.put("w", c.w.toDouble()); ro.put("a", c.ta.toDouble()); ro.put("b", c.tb.toDouble())
            ro.put("n", "Rua " + nameN++)
            val p = JSONArray()
            for (q in 0 until n) { p.put(round2(c.x[q])); p.put(round2(c.z[q])); p.put(round2(y[q])); p.put(if (br[q]) 1 else 0) }
            ro.put("p", p)
            val gl = merged(c)
            if (gl.length() > 0) { ro.put("cl", gl); ro.put("cr", gl) }
            roadsJ.put(ro)
            // beco sem saída
            if (!c.viaduct && c.src.kind != K_HIGHWAY) {
                if (c.sHub < 0 && !c.sJ) { val nd = JSONArray(); nd.put(round2(c.x[0])); nd.put(round2(c.z[0])); nd.put(round2(gy[0] - 0.14f)); nd.put(12.5); nd.put(1); nodesJ.put(nd) }
                if (c.eHub < 0 && !c.eJ) { val nd = JSONArray(); nd.put(round2(c.x[n - 1])); nd.put(round2(c.z[n - 1])); nd.put(round2(gy[n - 1] - 0.14f)); nd.put(12.5); nd.put(1); nodesJ.put(nd) }
                // postes
                var s = 24f; var side = 1f
                while (s < S - 14f) {
                    val a = atArc(c, s)
                    val qi = a[4].toInt()
                    var ok = !br[qi]
                    for (g in c.gaps) if (s > g[0] - 3f && s < g[1] + 3f) ok = false
                    for (hb in hubs) if (hypot(a[0] - hb.x, a[1] - hb.z) < hb.r + 12f) ok = false
                    if (ok) {
                        val nxv = -a[3]; val nzv = a[2]
                        val off = c.hw + 3.6f
                        lampJ.put(round2(a[0] + nxv * off * side)); lampJ.put(round2(a[1] + nzv * off * side))
                        lampJ.put(round2(atan2((-side * nzv).toDouble(), (-side * nxv).toDouble()).toFloat())); lampJ.put(if (c.src.kind == K_AVENUE) 1 else 0)
                        side = -side
                    }
                    s += 42f
                }
            }
        }
        val roundsJ = JSONArray()
        for ((i, hb) in hubs.withIndex()) {
            val o = JSONObject(); o.put("x", round2(hb.x)); o.put("z", round2(hb.z)); o.put("r", hb.r.toDouble()); o.put("y", round2(hubLv[i] - 0.06f))
            val aa = JSONArray(); arms[i]?.forEach { aa.put(it.toDouble()) }
            o.put("arms", aa); roundsJ.put(o)
        }
        val housesJ = JSONArray()
        for (h in houses) { val o = JSONObject(); o.put("k", h.k); o.put("x", round2(h.x)); o.put("z", round2(h.z)); o.put("lvl", lvls[h.k]!!.toDouble()); housesJ.put(o) }
        // árvores: fora de ruas, rotatórias, casas e água
        val treeJ = JSONArray()
        for (t in trees) {
            if (hAt(H, t.x, t.z) < 1.0f) continue
            var bad = false
            for (h in houses) if (hypot(t.x - h.x, t.z - h.z) < 20f) { bad = true; break }
            if (!bad) for (hb in hubs) if (hypot(t.x - hb.x, t.z - hb.z) < hb.r + 4f) { bad = true; break }
            if (!bad) for (c in cr) {
                if (c.viaduct) continue
                if (nearest(c, t.x, t.z)[0] < c.hw + 4.2f) { bad = true; break }
            }
            if (bad) continue
            treeJ.put(round2(t.x)); treeJ.put(round2(t.z)); treeJ.put(t.sp); treeJ.put(round2(t.sc)); treeJ.put(round2(t.rot)); treeJ.put(round2(t.tone))
        }
        val js = JSONObject()
        js.put("world", JSONArray().put(WX.toDouble()).put(WZ.toDouble()))
        js.put("roads", roadsJ); js.put("rounds", roundsJ); js.put("nodes", nodesJ); js.put("houses", housesJ)
        js.put("bld", JSONArray()); js.put("lamp", lampJ); js.put("hyd", JSONArray()); js.put("tree", treeJ)
        return Compiled(js, H)
    }

    private fun snapHub(pts: ArrayList<FloatArray>, end: Int, nxt: Int): Int {
        val e = pts[end]
        for ((hi, hb) in hubs.withIndex()) {
            if (hypot(e[0] - hb.x, e[1] - hb.z) < hb.r + 10f) {
                var ux = pts[nxt][0] - hb.x; var uz = pts[nxt][1] - hb.z
                var l = hypot(ux, uz)
                if (l < 1e-3f) { ux = 1f; uz = 0f; l = 1f }
                ux /= l; uz /= l
                e[0] = hb.x + ux * (hb.r - 0.6f); e[1] = hb.z + uz * (hb.r - 0.6f)
                return hi
            }
        }
        return -1
    }
}
