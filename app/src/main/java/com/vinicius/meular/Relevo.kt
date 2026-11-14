package com.vinicius.meular

import android.content.res.AssetManager
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import org.json.JSONObject
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Etapa 178: cidade nova com RELEVO (sem grade). Lê assets/hds/relevo.bin (alturas a cada 8 m) e assets/hds/city3.json
 * (ruas curvas, rotatórias, pontes e as 17 casas) e monta terreno, água, ruas, rotatórias, pontes e árvores.
 * As casas do Hds (com interior) são as mesmas; só mudam de lugar e sobem/descem para o platô do terreno (ver Hds.build).
 * Sem esses arquivos, o jogo continua com a Cidade 2 antiga.
 */
object Relevo {
    /** canto noroeste do mapa no mundo do jogo (longe do lote da casa antiga, que fica perto de 0,0) */
    const val CX = 300f
    const val CZ = 300f
    private const val ROADY = 0.12f
    private const val CS = 8   // células de terreno por pedaço (8 x 8 m = 64 m)

    class House(val k: Int, val x: Float, val z: Float, val lvl: Float)
    /** Etapa 180b: [cs] = distância acumulada de cada ponto; [ta]/[tb] = quanto da faixa central some junto aos cruzamentos; [gl]/[gr] = "bocas" do meio-fio (pares início/fim) nos lados +n e -n */
    private class Road(val c: Int, val w: Float, val x: FloatArray, val z: FloatArray, val y: FloatArray, val br: BooleanArray, val nx: FloatArray, val nz: FloatArray, val keep: BooleanArray,
                       val cs: FloatArray, val ta: Float, val tb: Float, val gl: FloatArray, val gr: FloatArray)
    /** [arms] = grupos de 5 (dx, dz, ux, uz, meia-largura): começo da pista (relativo ao centro), direção para fora e meia-largura */
    private class Hub(val x: Float, val z: Float, val r: Float, val y: Float, val arms: FloatArray)
    /** Etapa 179: placa de cruzamento (kind 0) ou fim de rua em balão (kind 1) */
    private class Pad(val x: Float, val z: Float, val r: Float, val y: Float, val kind: Int)

    @Volatile var on = false
    /** Etapa 185: Cidade 3 (bairro americano): lê sub.bin + sub.json + sub_mesh.bin (casas, cercas, carros... já montados) */
    @Volatile var sub = false
    private class SubRec(val mat: Int, val nv: Int, val ymax: Float, val f: FloatArray, val c: ByteArray)
    private val subCells = HashMap<Int, ArrayList<SubRec>>()
    private var subSol = FloatArray(0)
    /** Cidade 5: altura do chão pavimentado a cada [wst] m (asfalto, calçada, orla, ponte); -32768 = sem pavimento */
    private var walk = ShortArray(0)
    /** Cidade 5: 1 = vértice de areia de praia (o resto, mesmo baixo, é grama: margens de rio/lagoa sem "degraus" de areia) */
    private var sandMask = ByteArray(0)
    private fun loadSand(am: AssetManager) {
        val bb = ByteBuffer.wrap(am.open("hds/c5_sand.bin").use { it.readBytes() }).order(ByteOrder.LITTLE_ENDIAN)
        val sx = bb.getInt(); val sz = bb.getInt()
        sandMask = if (sx == nx && sz == nz) ByteArray(sx * sz).also { bb.get(it) } else ByteArray(0)
    }
    private fun sandAt(i: Int, j: Int): Boolean = sandMask[j.coerceIn(0, nz - 1) * nx + i.coerceIn(0, nx - 1)].toInt() != 0
    private var wnx = 0
    private var wnz = 0
    private var wst = 2f
    private fun loadWalk(am: AssetManager) {
        val bb = ByteBuffer.wrap(am.open("hds/c5_walk.bin").use { it.readBytes() }).order(ByteOrder.LITTLE_ENDIAN)
        wnx = bb.getInt(); wnz = bb.getInt(); wst = bb.getFloat()
        val w = ShortArray(wnx * wnz)
        for (i in w.indices) w[i] = bb.getShort()
        walk = w
    }
    private fun walkAt(x: Float, z: Float): Float {
        if (walk.isEmpty()) return Float.NaN
        val i = Math.round((x - CX) / wst); val j = Math.round((z - CZ) / wst)
        if (i < 0 || j < 0 || i >= wnx || j >= wnz) return Float.NaN
        val v = walk[j * wnx + i].toInt()
        return if (v == -32768) Float.NaN else v / 100f
    }

    /** colisões do bairro (x0, z0, x1, z1) já em coordenadas do mundo */
    fun subSolids(): List<FloatArray> {
        val l = ArrayList<FloatArray>()
        var i = 0
        while (i + 3 < subSol.size) { l.add(floatArrayOf(subSol[i] + CX, subSol[i + 1] + CZ, subSol[i + 2] + CX, subSol[i + 3] + CZ)); i += 4 }
        return l
    }

    private fun loadSubMesh(am: AssetManager, name: String) {
        subCells.clear()
        val bb = ByteBuffer.wrap(am.open(name).use { it.readBytes() }).order(ByteOrder.LITTLE_ENDIAN)
        bb.getInt()   // "SUB1"
        val n = bb.getInt()
        for (r in 0 until n) {
            val cell = bb.getInt(); val mat = bb.getInt(); val nv = bb.getInt(); val ymax = bb.getFloat()
            val f = FloatArray(nv * 8); val c = ByteArray(nv * 3)
            for (v in 0 until nv) {
                for (k in 0 until 8) f[v * 8 + k] = bb.getFloat()
                c[v * 3] = bb.get(); c[v * 3 + 1] = bb.get(); c[v * 3 + 2] = bb.get()
            }
            subCells.getOrPut(cell) { ArrayList() }.add(SubRec(mat, nv, ymax, f, c))
        }
    }
    @Volatile var worldW = 3200f
    @Volatile var worldH = 2400f
    private var nx = 0
    private var nz = 0
    private var g = 8f
    private var hs = ShortArray(0)
    private val roads = ArrayList<Road>()
    private val hubs = ArrayList<Hub>()
    private val pads = ArrayList<Pad>()
    private val padGrid = HashMap<Int, ArrayList<Pad>>()
    private fun padR(p: Pad): Float = if (p.kind == 1) p.r else p.r + 1.0f   // Etapa 180: cruzamento sem "bolha" (antes r*1.25+1.2)
    private val segGrid = HashMap<Int, ArrayList<IntArray>>()   // células de 32 m -> (rua, trecho) que passam por ali (para o chão)
    private val houses = HashMap<Int, House>()
    @Volatile private var mapBmp: Bitmap? = null

    private val COL_WATER = C("#4F9BD0")
    private val COL_SHAL = C("#8FE0D6")      // água rasa (turquesa)
    private val COL_DEEP = C("#1B5FA6")      // água funda
    private val COL_FOAM = C("#E8FAF7")      // espuma na beira
    private val COL_BED = C("#A8966F")
    private val COL_SAND = C("#E6D6A4")
    private val COL_ROCK = C("#A89C84")
    private val COL_ASPH = C("#D0D0D0")
    private val COL_CURB = C("#CFCAC0")
    private val COL_WALK = C("#DAD5CB")      // calçada de bairro (ladrilho claro)
    private val COL_VERGE = C("#8DBE6E")     // faixa de grama ao lado das avenidas
    private val COL_FENCE = C("#4A525C")     // cerca/guard-rail de avenida
    private val COL_LINE = C("#FFFFFF")
    private val COL_LINE_Y = C("#FFD54F")
    private val COL_BRIDGE = C("#B7B0A8")
    private val COL_UNDER = C("#8A8580")
    private val COL_ISLAND = C("#B9DCA0")
    private val COL_TRUNK = C("#7A5A3A")
    private val GRASS_LO = C("#B4DA9A")
    private val GRASS_HI = C("#E4EBB0")
    private val TREES = intArrayOf(C("#4F9A55"), C("#5FAE5A"), C("#3F8A50"), C("#6BB45C"), C("#7CBF62"))

    fun house(k: Int): House? = houses[k]
    /** Etapa 187: a casa k existe neste mapa? (no mapa do jogador nem todas as 17 casas são colocadas) */
    fun has(k: Int): Boolean = houses.containsKey(k)

    /** Etapa 178: vaga do carro junto à calçada, em frente da Casa 1: (x, z, rumo em rad; frente = (sin h, -cos h)). null se não achar rua perto. */
    fun carSpot(): FloatArray? {
        val h = houses[0] ?: return null
        val hx = CX + h.x; val hz = CZ + h.z
        var bd = 80f; var res: FloatArray? = null
        for (r in roads) {
            if (r.c == 0) continue   // rodovia não
            for (q in 0 until r.x.size) {
                if (r.br[q]) continue
                if (!((q < r.keep.size && r.keep[q]) || (q > 0 && r.keep[q - 1]))) continue
                if ((r.ta > 0f && r.cs[q] < r.ta + 8f) || (r.tb > 0f && r.cs[q] > r.cs[r.cs.size - 1] - r.tb - 8f)) continue   // Etapa 180b: fora do cruzamento
                val d = hypot(r.x[q] - hx, r.z[q] - hz)
                if (d >= bd) continue
                var nearHub = false
                for (u in hubs) if (hypot(r.x[q] - u.x, r.z[q] - u.z) < u.r + 12f) { nearHub = true; break }
                if (!nearHub) for (u in pads) if (hypot(r.x[q] - u.x, r.z[q] - u.z) < padR(u) + 6f) { nearHub = true; break }
                if (nearHub) continue
                val side = if ((hx - r.x[q]) * r.nx[q] + (hz - r.z[q]) * r.nz[q] >= 0f) 1f else -1f
                val off = max(0f, r.w / 2f - 2.2f)
                val tx = r.nz[q]; val tz = -r.nx[q]   // tangente da rua
                bd = d
                res = floatArrayOf(r.x[q] + r.nx[q] * side * off, r.z[q] + r.nz[q] * side * off, Math.atan2(tx.toDouble(), (-tz).toDouble()).toFloat())
            }
        }
        return res
    }

    fun clear() {
        on = false
        hs = ShortArray(0)
        roads.clear(); hubs.clear(); pads.clear(); padGrid.clear(); segGrid.clear(); houses.clear()
        sub = false; subCells.clear(); subSol = FloatArray(0); walk = ShortArray(0); sandMask = ByteArray(0)
        mapBmp = null   // sem recycle: o mapa pode estar sendo desenhado agora
    }

    /** Lê os dados do relevo. false se os arquivos não existem (aí vale a Cidade 2 antiga). */
    fun load(am: AssetManager, wantSub: Boolean = false, user: Boolean = false, c5: Boolean = false): Boolean {
        on = false; sub = false
        try {
            val h: ShortArray
            val js: JSONObject
            if (user) {   // Etapa 187: mapa criado pelo jogador no editor (UserMap)
                val cm = UserMap.compile()
                nx = UserMap.NX; nz = UserMap.NZ; g = UserMap.G
                h = cm.hs; js = cm.json
            } else {
                val bb = ByteBuffer.wrap(am.open(if (c5) "hds/c5.bin" else if (wantSub) "hds/sub.bin" else "hds/relevo.bin").use { it.readBytes() }).order(ByteOrder.LITTLE_ENDIAN)
                nx = bb.getInt(); nz = bb.getInt(); g = bb.getFloat()
                h = ShortArray(nx * nz)
                for (i in h.indices) h[i] = bb.getShort()
                js = JSONObject(am.open(if (c5) "hds/c5.json" else if (wantSub) "hds/sub.json" else "hds/city3.json").bufferedReader().use { it.readText() })
            }
            val wo = js.getJSONArray("world")
            worldW = wo.getDouble(0).toFloat(); worldH = wo.getDouble(1).toFloat()
            roads.clear(); hubs.clear(); pads.clear(); padGrid.clear(); segGrid.clear(); houses.clear()
            val ra = js.getJSONArray("roads")
            for (i in 0 until ra.length()) {
                val o = ra.getJSONObject(i); val p = o.getJSONArray("p"); val n = p.length() / 4
                if (n < 2) continue
                val x = FloatArray(n); val z = FloatArray(n); val y = FloatArray(n); val br = BooleanArray(n)
                for (q in 0 until n) {
                    x[q] = p.getDouble(q * 4).toFloat() + CX; z[q] = p.getDouble(q * 4 + 1).toFloat() + CZ
                    y[q] = p.getDouble(q * 4 + 2).toFloat(); br[q] = p.getInt(q * 4 + 3) != 0
                }
                val ex = FloatArray(n); val ez = FloatArray(n)
                for (q in 0 until n) {
                    val a = max(q - 1, 0); val b = min(q + 1, n - 1)
                    var tx = x[b] - x[a]; var tz = z[b] - z[a]
                    val l = hypot(tx, tz)
                    if (l < 1e-4f) { tx = 1f; tz = 0f } else { tx /= l; tz /= l }
                    ex[q] = -tz; ez[q] = tx
                }
                // Etapa 180b: onde duas pistas se emendam, as duas pontas usam a mesma normal (esquadro): sem cunha de grama na quina
                val n0 = o.optJSONArray("n0"); val n1 = o.optJSONArray("n1")
                if (n0 != null) { ex[0] = n0.getDouble(0).toFloat(); ez[0] = n0.getDouble(1).toFloat() }
                if (n1 != null) { ex[n - 1] = n1.getDouble(0).toFloat(); ez[n - 1] = n1.getDouble(1).toFloat() }
                val w = o.getDouble("w").toFloat()
                // Etapa 180b: a pista vai INTEIRA até o centro do cruzamento (sem discos); só a faixa central some junto ao cruzamento (a, b)
                val ta = o.optDouble("a", 0.0).toFloat(); val tb = o.optDouble("b", 0.0).toFloat()
                val cs = FloatArray(n)
                for (q in 1 until n) cs[q] = cs[q - 1] + hypot(x[q] - x[q - 1], z[q] - z[q - 1])
                val keep = BooleanArray(n - 1) { true }
                val gl = o.optJSONArray("cl"); val gr = o.optJSONArray("cr")
                val gla = FloatArray(gl?.length() ?: 0) { k -> gl!!.getDouble(k).toFloat() }
                val gra = FloatArray(gr?.length() ?: 0) { k -> gr!!.getDouble(k).toFloat() }
                roads.add(Road(o.getInt("c"), w, x, z, y, br, ex, ez, keep, cs, ta, tb, gla, gra))
            }
            val ro = js.getJSONArray("rounds")
            for (i in 0 until ro.length()) {
                val o = ro.getJSONObject(i)
                val aa = o.optJSONArray("arms")
                val arms = FloatArray(aa?.length() ?: 0) { k -> aa!!.getDouble(k).toFloat() }
                hubs.add(Hub(o.getDouble("x").toFloat() + CX, o.getDouble("z").toFloat() + CZ, o.getDouble("r").toFloat(), o.getDouble("y").toFloat(), arms))
            }
            val na = js.optJSONArray("nodes")
            if (na != null) for (i in 0 until na.length()) {
                val o = na.getJSONArray(i)
                pads.add(Pad(o.getDouble(0).toFloat() + CX, o.getDouble(1).toFloat() + CZ, o.getDouble(3).toFloat(), o.getDouble(2).toFloat(), o.getInt(4)))
            }
            val ha = js.getJSONArray("houses")
            for (i in 0 until ha.length()) {
                val o = ha.getJSONObject(i); val k = o.getInt("k")
                houses[k] = House(k, o.getDouble("x").toFloat(), o.getDouble("z").toFloat(), o.getDouble("lvl").toFloat())
            }
            fun fa(k: String): FloatArray { val a = js.optJSONArray(k); return FloatArray(a?.length() ?: 0) { i -> a!!.getDouble(i).toFloat() } }
            bldA = fa("bld"); lampA = fa("lamp"); hydA = fa("hyd"); treeA = fa("tree")   // Etapa 184: população (gen_pop.py)
            if (wantSub) {
                loadSubMesh(am, if (c5) "hds/c5_mesh.bin" else "hds/sub_mesh.bin")
                if (c5) loadWalk(am) else walk = ShortArray(0)
                val sa = js.optJSONArray("solid")
                val so = ArrayList<Float>()
                if (sa != null) for (i in 0 until sa.length()) {
                    val q = sa.get(i)
                    if (q is org.json.JSONArray) for (k in 0 until q.length()) so.add(q.getDouble(k).toFloat()) else so.add((q as Number).toFloat())
                }
                subSol = so.toFloatArray()
            }
            sub = wantSub
            hs = h
            sandMask = ByteArray(0)
            if (c5) try { loadSand(am) } catch (e: Throwable) { sandMask = ByteArray(0) }
            on = true
            liftRoads()
            indexRoads()
            return true
        } catch (e: Throwable) {
            android.util.Log.w("Relevo", "sem relevo: $e")
            clear()
            return false
        }
    }

    private fun hh(i: Int, j: Int): Float = hs[j.coerceIn(0, nz - 1) * nx + i.coerceIn(0, nx - 1)] / 100f

    /** altura do terreno (interpolada) no ponto do mundo */
    fun height(x: Float, z: Float): Float {
        if (!on) return 0f
        val fx = ((x - CX) / g).coerceIn(0f, nx - 1.001f); val fz = ((z - CZ) / g).coerceIn(0f, nz - 1.001f)
        val i = fx.toInt(); val j = fz.toInt(); val tx = fx - i; val tz = fz - j
        val a = hh(i, j); val b = hh(i + 1, j); val c = hh(i, j + 1); val d = hh(i + 1, j + 1)
        return (a * (1f - tx) + b * tx) * (1f - tz) + (c * (1f - tx) + d * tx) * tz
    }

    // Deve corresponder exatamente a CWF no gerador gen_city7.py.
    // As bocas de cruzamento (cl/cr) são calculadas com essas larguras;
    // usar valores maiores no runtime fazia as calçadas invadirem os cruzamentos
    // e criarem sobras/recortes irregulares nas esquinas.
    private fun curbW(r: Road) = when (r.c) { 0, 1 -> 1.4f; 2 -> 2.0f; else -> 2.4f }

    /** Sobe a rua onde o terreno chegaria acima do asfalto (nunca desce): o asfalto fica sempre à vista. Pontes não mudam. */
    private fun liftRoads() {
        for (r in roads) {
            val n = r.x.size
            val hw = r.w / 2f; val cw = curbW(r)
            val need = FloatArray(n) { -1e9f }
            for (q in 0 until n) {
                if (r.br[q]) continue
                var m = -1e9f
                for (k in 0 until 5) {
                    val o = when (k) { 0 -> -(hw + cw); 1 -> -hw; 2 -> 0f; 3 -> hw; else -> hw + cw }
                    val th = height(r.x[q] + r.nx[q] * o, r.z[q] + r.nz[q] * o)
                    val need1 = if (k == 0 || k == 4) th - 0.04f - ROADY else th + 0.03f - ROADY
                    if (need1 > m) m = need1
                }
                need[q] = m
                if (m > r.y[q]) r.y[q] = m
            }
            if (n >= 3) {
                for (pass in 0 until 2) {
                    var prev = r.y[0]
                    for (q in 1 until n - 1) {
                        val cur = r.y[q]
                        if (!r.br[q]) r.y[q] = max(need[q], (prev + 2f * cur + r.y[q + 1]) / 4f)
                        prev = cur
                    }
                }
            }
        }
    }

    private fun indexRoads() {
        segGrid.clear(); padGrid.clear()
        for (p in pads) {
            val e = padR(p) + 2f
            val a0 = Math.floor((p.x - e) / 32.0).toInt(); val a1 = Math.floor((p.x + e) / 32.0).toInt()
            val b0 = Math.floor((p.z - e) / 32.0).toInt(); val b1 = Math.floor((p.z + e) / 32.0).toInt()
            for (a in a0..a1) for (b in b0..b1) padGrid.getOrPut((a + 1000) * 4096 + (b + 1000)) { ArrayList() }.add(p)
        }
        for ((ri, r) in roads.withIndex()) {
            val e = r.w / 2f + curbW(r) + 1f
            for (q in 0 until r.x.size - 1) {
                if (!r.keep[q]) continue
                val x0 = min(r.x[q], r.x[q + 1]) - e; val x1 = max(r.x[q], r.x[q + 1]) + e
                val z0 = min(r.z[q], r.z[q + 1]) - e; val z1 = max(r.z[q], r.z[q + 1]) + e
                val a0 = Math.floor(x0 / 32.0).toInt(); val a1 = Math.floor(x1 / 32.0).toInt()
                val b0 = Math.floor(z0 / 32.0).toInt(); val b1 = Math.floor(z1 / 32.0).toInt()
                for (a in a0..a1) for (b in b0..b1) segGrid.getOrPut((a + 1000) * 4096 + (b + 1000)) { ArrayList() }.add(intArrayOf(ri, q))
            }
        }
    }

    /** altura do asfalto (ou da calçada) sob (x, z), ou NaN se não há rua ali; inclui pontes e rotatórias */
    private fun roadSurface(x: Float, z: Float): Float {
        var best = Float.NaN
        val l = segGrid[(Math.floor(x / 32.0).toInt() + 1000) * 4096 + (Math.floor(z / 32.0).toInt() + 1000)]
        if (l != null) for (s in l) {
            val r = roads[s[0]]; val q = s[1]
            val vx = r.x[q + 1] - r.x[q]; val vz = r.z[q + 1] - r.z[q]
            val l2 = vx * vx + vz * vz
            if (l2 < 1e-4f) continue
            val t = (((x - r.x[q]) * vx + (z - r.z[q]) * vz) / l2).coerceIn(0f, 1f)
            val d = hypot(x - (r.x[q] + vx * t), z - (r.z[q] + vz * t))
            val hw = r.w / 2f
            if (d > hw + curbW(r)) continue
            val y = r.y[q] + (r.y[q + 1] - r.y[q]) * t + ROADY + (if (d > hw) (if (r.c <= 1) 0.07f else 0.1f) else 0f)
            if (best.isNaN() || y > best) best = y
        }
        val pl = padGrid[(Math.floor(x / 32.0).toInt() + 1000) * 4096 + (Math.floor(z / 32.0).toInt() + 1000)]
        if (pl != null) for (p in pl) {
            val d = hypot(x - p.x, z - p.z)
            val rr = padR(p)
            if (d > rr + 1.2f) continue
            val y = p.y + ROADY + 0.06f + (if (d > rr) 0.04f else 0f)
            if (best.isNaN() || y > best) best = y
        }
        for (h in hubs) {
            val d = hypot(x - h.x, z - h.z)
            if (d > h.r + 1.8f) continue
            val y = h.y + ROADY + (if (d < h.r * 0.45f) 0.2f else if (d > h.r) 0.05f else 0f)
            if (best.isNaN() || y > best) best = y
        }
        return best
    }

    /** chão sob (x, z): rua, ponte ou rotatória; senão o terreno */
    fun groundH(x: Float, z: Float): Float {
        val h = height(x, z)
        val wv = walkAt(x, z)
        if (!wv.isNaN() && wv > h - 0.6f) return wv
        val rs = roadSurface(x, z)
        return if (!rs.isNaN() && rs > h - 0.6f) rs else h
    }

    /** água funda demais para andar (mais que a canela), fora de ponte */
    fun wet(x: Float, z: Float): Boolean = on && groundH(x, z) < -0.45f

    private fun grassCol(h: Float): Int = mix(GRASS_LO, GRASS_HI, (h / 60f).coerceIn(0f, 1f))

    private fun tri(b: MB, ax: Float, ay: Float, az: Float, bx: Float, by: Float, bz: Float, cx: Float, cy: Float, cz: Float, nx: Float, ny: Float, nz: Float, c: Int) {
        b.v(ax, ay, az, nx, ny, nz, c, ax, az)
        b.v(bx, by, bz, nx, ny, nz, c, bx, bz)
        b.v(cx, cy, cz, nx, ny, nz, c, cx, cz)
    }

    /** faixa horizontal entre duas linhas (a esquerda e a direita), no alto [y] */
    private fun strip(b: MB, lx0: Float, lz0: Float, rx0: Float, rz0: Float, lx1: Float, lz1: Float, rx1: Float, rz1: Float, y0: Float, y1: Float, c: Int) {
        tri(b, lx0, y0, lz0, rx0, y0, rz0, rx1, y1, rz1, 0f, 1f, 0f, c)
        tri(b, lx0, y0, lz0, rx1, y1, rz1, lx1, y1, lz1, 0f, 1f, 0f, c)
    }

    private fun wall(b: MB, ax: Float, az: Float, bx: Float, bz: Float, yTop: Float, yBot: Float, nx: Float, nz: Float, c: Int) {
        tri(b, ax, yTop, az, bx, yTop, bz, bx, yBot, bz, nx, 0f, nz, c)
        tri(b, ax, yTop, az, bx, yBot, bz, ax, yBot, az, nx, 0f, nz, c)
    }

    /** pedaços de [s0, s1] que sobram depois de tirar os intervalos [gaps] (pares início/fim em ordem crescente) */
    private fun spans(s0: Float, s1: Float, gaps: FloatArray): ArrayList<FloatArray> {
        val out = ArrayList<FloatArray>()
        var cur = s0
        var i = 0
        while (i + 1 < gaps.size) {
            val g0 = gaps[i]; val g1 = gaps[i + 1]
            i += 2
            if (g1 <= cur) continue
            if (g0 >= s1) break
            if (g0 > cur) out.add(floatArrayOf(cur, g0))
            cur = max(cur, g1)
            if (cur >= s1) break
        }
        if (cur < s1 - 1e-3f) out.add(floatArrayOf(cur, s1))
        return out
    }

    /** Etapa 182: true se (x, z) cai sobre a ilha central de uma rotatória (onde a rodovia elevada passa por cima). */
    private fun nearIsland(x: Float, z: Float): Boolean {
        for (h in hubs) if (hypot(x - h.x, z - h.z) < h.r * 0.45f + 3f) return true
        return false
    }

    /** Etapa 182: cerca de avenida de (x0,z0,y0) a (x1,z1,y1): mourões a cada ~3 m e duas travessas (alta e baixa), de dois lados. */
    private fun emitFence(b: MB, x0: Float, z0: Float, y0: Float, x1: Float, z1: Float, y1: Float) {
        val len = hypot(x1 - x0, z1 - z0)
        if (len < 0.3f) return
        val n = max(1, Math.round(len / 3f))
        b.m(Mt.PLAIN, 1f)
        val nx = -(z1 - z0) / len; val nz = (x1 - x0) / len
        for (k in 0..n) {
            val t = k.toFloat() / n
            b.box(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + 0.55f, z0 + (z1 - z0) * t, 0.12f, 1.1f, 0.12f, COL_FENCE)
        }
        for (hgt in floatArrayOf(0.45f, 0.95f)) {
            wall(b, x0, z0, x1, z1, y0 + hgt + 0.07f, y1 + hgt - 0.07f, nx, nz, COL_FENCE)
            wall(b, x1, z1, x0, z0, y1 + hgt + 0.07f, y0 + hgt - 0.07f, -nx, -nz, COL_FENCE)
        }
    }

    private fun emitSeg(b: MB, r: Road, q: Int) {
        val hw = r.w / 2f
        val x0 = r.x[q]; val z0 = r.z[q]; val y0 = r.y[q] + ROADY
        val x1 = r.x[q + 1]; val z1 = r.z[q + 1]; val y1 = r.y[q + 1] + ROADY
        val ax = r.nx[q]; val az = r.nz[q]; val bx = r.nx[q + 1]; val bz = r.nz[q + 1]
        // Interpola a direção da borda sem estreitar a pista nas curvas. Preserva o fator
        // de miter calculado pelo gerador nos encontros entre trechos.
        val ml = hypot(ax, az).coerceAtLeast(1e-4f)
        val mr = hypot(bx, bz).coerceAtLeast(1e-4f)
        fun normalAt(t: Float): FloatArray {
            val vx = ax + (bx - ax) * t
            val vz = az + (bz - az) * t
            val len = hypot(vx, vz).coerceAtLeast(1e-4f)
            val target = ml + (mr - ml) * t
            val scale = target / len
            return floatArrayOf(vx * scale, vz * scale)
        }
        val n0 = normalAt(0f); val n1 = normalAt(1f)
        b.m(Mt.ASPHALT, 0.25f)
        strip(b, x0 + n0[0] * hw, z0 + n0[1] * hw, x0 - n0[0] * hw, z0 - n0[1] * hw, x1 + n1[0] * hw, z1 + n1[1] * hw, x1 - n1[0] * hw, z1 - n1[1] * hw, y0, y1, COL_ASPH)
        val cw = curbW(r)
        val sA = r.cs[q]; val sB = r.cs[q + 1]
        val sl = sB - sA
        // Etapa 182: avenida/rodovia = guia baixa + faixa de grama + cerca (sem calçada); rua de bairro = guia fina + calçada larga de ladrilho
        val avenue = r.c <= 1
        val gw = 0.35f   // largura da guia de pedra junto ao asfalto
        val inHub = nearIsland(x0, z0) || nearIsland(x1, z1)
        for (side in 0 until 2) {
            val sg = if (side == 0) 1f else -1f
            for (sp in spans(sA, sB, if (side == 0) r.gl else r.gr)) {
                val t0 = if (sl > 1e-4f) (sp[0] - sA) / sl else 0f
                val t1 = if (sl > 1e-4f) (sp[1] - sA) / sl else 1f
                val px0 = x0 + (x1 - x0) * t0; val pz0 = z0 + (z1 - z0) * t0; val py0 = y0 + (y1 - y0) * t0
                val px1 = x0 + (x1 - x0) * t1; val pz1 = z0 + (z1 - z0) * t1; val py1 = y0 + (y1 - y0) * t1
                val nn0 = normalAt(t0); val nn1 = normalAt(t1)
                val mx0 = nn0[0] * sg; val mz0 = nn0[1] * sg
                val mx1 = nn1[0] * sg; val mz1 = nn1[1] * sg
                if (inHub && avenue) continue   // a pista que cruza a ilha da rotatória não leva guia nem cerca
                b.m(Mt.PAVER, 0.9f)
                strip(b, px0 + mx0 * hw, pz0 + mz0 * hw, px0 + mx0 * (hw + gw), pz0 + mz0 * (hw + gw), px1 + mx1 * hw, pz1 + mz1 * hw, px1 + mx1 * (hw + gw), pz1 + mz1 * (hw + gw), py0 + 0.07f, py1 + 0.07f, COL_CURB)
                if (avenue) {
                    b.m(Mt.GRASS, 0.3f)
                    strip(b, px0 + mx0 * (hw + gw), pz0 + mz0 * (hw + gw), px0 + mx0 * (hw + cw), pz0 + mz0 * (hw + cw), px1 + mx1 * (hw + gw), pz1 + mz1 * (hw + gw), px1 + mx1 * (hw + cw), pz1 + mz1 * (hw + cw), py0 + 0.03f, py1 + 0.03f, COL_VERGE)
                    if (!(r.br[q] && r.br[q + 1])) emitFence(b, px0 + mx0 * (hw + cw - 0.2f), pz0 + mz0 * (hw + cw - 0.2f), py0, px1 + mx1 * (hw + cw - 0.2f), pz1 + mz1 * (hw + cw - 0.2f), py1)
                } else {
                    b.m(Mt.TILE, 0.5f)
                    strip(b, px0 + mx0 * (hw + gw), pz0 + mz0 * (hw + gw), px0 + mx0 * (hw + cw), pz0 + mz0 * (hw + cw), px1 + mx1 * (hw + gw), pz1 + mz1 * (hw + gw), px1 + mx1 * (hw + cw), pz1 + mz1 * (hw + cw), py0 + 0.1f, py1 + 0.1f, COL_WALK)
                }
            }
        }
        b.m(Mt.PLAIN, 1f)
        if (r.c <= 2) {
            // faixa central: some dentro dos cruzamentos (da ponta até r.ta / r.tb)
            val s0 = max(sA, r.ta); val s1 = min(sB, r.cs[r.cs.size - 1] - r.tb)
            if (s1 > s0 + 1e-3f && sl > 1e-4f) {
                val lc = if (r.c == 0) COL_LINE_Y else COL_LINE
                val t0 = (s0 - sA) / sl; val t1 = (s1 - sA) / sl
                val px0 = x0 + (x1 - x0) * t0; val pz0 = z0 + (z1 - z0) * t0; val py0 = y0 + (y1 - y0) * t0
                val px1 = x0 + (x1 - x0) * t1; val pz1 = z0 + (z1 - z0) * t1; val py1 = y0 + (y1 - y0) * t1
                val nn0 = normalAt(t0); val nn1 = normalAt(t1)
                val mx0 = nn0[0]; val mz0 = nn0[1]
                val mx1 = nn1[0]; val mz1 = nn1[1]
                strip(b, px0 + mx0 * 0.15f, pz0 + mz0 * 0.15f, px0 - mx0 * 0.15f, pz0 - mz0 * 0.15f, px1 + mx1 * 0.15f, pz1 + mz1 * 0.15f, px1 - mx1 * 0.15f, pz1 - mz1 * 0.15f, py0 + 0.02f, py1 + 0.02f, lc)
            }
        }
        if (r.br[q] && r.br[q + 1]) {
            // ponte: parede lateral, parapeito e fundo
            val ow = hw + cw
            wall(b, x0 + n0[0] * ow, z0 + n0[1] * ow, x1 + n1[0] * ow, z1 + n1[1] * ow, y0 + 0.05f, y0 - 1.3f, n0[0], n0[1], COL_BRIDGE)
            wall(b, x0 - n0[0] * ow, z0 - n0[1] * ow, x1 - n1[0] * ow, z1 - n1[1] * ow, y0 + 0.05f, y0 - 1.3f, -n0[0], -n0[1], COL_BRIDGE)
            // Etapa 183: parapeito com as duas faces visíveis + capa de pedra, poste de luz e pilares duplos com travessa
            for (sg in floatArrayOf(1f, -1f)) {
                val ex0 = x0 + n0[0] * ow * sg; val ez0 = z0 + n0[1] * ow * sg; val ex1 = x1 + n1[0] * ow * sg; val ez1 = z1 + n1[1] * ow * sg
                val ix0 = x0 + n0[0] * (ow - 0.3f) * sg; val iz0 = z0 + n0[1] * (ow - 0.3f) * sg; val ix1 = x1 + n1[0] * (ow - 0.3f) * sg; val iz1 = z1 + n1[1] * (ow - 0.3f) * sg
                wall(b, ex0, ez0, ex1, ez1, y0 + 1.0f, y0 + 0.05f, n0[0] * sg, n0[1] * sg, COL_BRIDGE)
                wall(b, ix1, iz1, ix0, iz0, y0 + 1.0f, y0 + 0.05f, -n0[0] * sg, -n0[1] * sg, shade(COL_BRIDGE, 14))
                strip(b, ix0, iz0, ex0, ez0, ix1, iz1, ex1, ez1, y0 + 1.0f, y1 + 1.0f, COL_CURB)
                if (q % 4 == 0) {
                    b.box(ix0, y0 + 2.6f, iz0, 0.16f, 3.2f, 0.16f, COL_FENCE)
                    b.box(ix0, y0 + 4.3f, iz0, 0.55f, 0.22f, 0.55f, C("#FFF0B8"), false)
                }
            }
            // Etapa 184: duas vigas longitudinais sob o tabuleiro e junta de dilatação no início de cada trecho
            val bl = hypot(x1 - x0, z1 - z0)
            if (bl > 0.5f) {
                val bang = Math.atan2((z1 - z0).toDouble(), (x1 - x0).toDouble()).toFloat()
                val ym = (y0 + y1) / 2f
                b.m(Mt.PLAIN, 1f)
                for (sg in floatArrayOf(-1f, 1f)) {
                    obox(b, (x0 + x1) / 2f + n0[0] * hw * 0.5f * sg, (z0 + z1) / 2f + n0[1] * hw * 0.5f * sg, bl, 0.7f, bang, ym - 2.1f, ym - 1.3f, shade(COL_UNDER, -14))
                }
                val jx = (x1 - x0) / bl * 0.18f; val jz = (z1 - z0) / bl * 0.18f
                strip(b, x0 + n0[0] * hw, z0 + n0[1] * hw, x0 - n0[0] * hw, z0 - n0[1] * hw, x0 + n0[0] * hw + jx, z0 + n0[1] * hw + jz, x0 - n0[0] * hw + jx, z0 - n0[1] * hw + jz, y0 + ROADY + 0.03f, y0 + ROADY + 0.03f, C("#2B2E33"))
            }
            if (q % 3 == 0) {   // pilares sob a ponte, do terreno até o fundo da pista
                val top = y0 - 1.3f
                val hgt = top - height(x0, z0)
                if (hgt > 2.2f) {
                    b.m(Mt.PLAIN, 1f)
                    for (sg in floatArrayOf(1f, -1f)) {
                        val cx = x0 + n0[0] * hw * 0.55f * sg; val cz = z0 + n0[1] * hw * 0.55f * sg
                        b.box(cx, (top + height(cx, cz)) / 2f, cz, 1.6f, top - height(cx, cz), 1.6f, COL_UNDER)
                    }
                    b.box(x0, top - 0.35f, z0, hw * 2f + 1.2f, 0.7f, 1.6f, shade(COL_UNDER, -10))
                }
            }
        }
    }

    private fun emitPad(b: MB, p: Pad) {
        val n = 20
        val rr = padR(p)
        val y = p.y + ROADY + 0.06f
        b.m(Mt.ASPHALT, 0.25f)
        for (k in 0 until n) {
            val a0 = (k * 2 * Math.PI / n).toFloat(); val a1 = ((k + 1) * 2 * Math.PI / n).toFloat()
            tri(b, p.x, y, p.z, p.x + cos(a0) * rr, y, p.z + sin(a0) * rr, p.x + cos(a1) * rr, y, p.z + sin(a1) * rr, 0f, 1f, 0f, COL_ASPH)
        }
        b.m(Mt.PAVER, 0.9f)
        val r2 = rr + 1.2f
        for (k in 0 until n) {
            val a0 = (k * 2 * Math.PI / n).toFloat(); val a1 = ((k + 1) * 2 * Math.PI / n).toFloat()
            strip(b, p.x + cos(a0) * rr, p.z + sin(a0) * rr, p.x + cos(a0) * r2, p.z + sin(a0) * r2, p.x + cos(a1) * rr, p.z + sin(a1) * rr, p.x + cos(a1) * r2, p.z + sin(a1) * r2, y + 0.0f, y + 0.0f, COL_CURB)
        }
    }

    /** true se o ponto (qx, qz), relativo ao centro da rotatória, cai dentro da faixa de uma pista que entra nela */
    private fun armAt(qx: Float, qz: Float, h: Hub): Boolean {
        var i = 0
        while (i + 4 < h.arms.size) {
            val dx = qx - h.arms[i]; val dz = qz - h.arms[i + 1]
            val ux = h.arms[i + 2]; val uz = h.arms[i + 3]
            val ax = dx * ux + dz * uz
            val lat = abs(dz * ux - dx * uz)
            if (ax >= -2f && lat <= h.arms[i + 4] + 0.15f) return true
            i += 5
        }
        return false
    }

    private fun emitHub(b: MB, h: Hub) {
        val n = 48
        val y = h.y + ROADY
        b.m(Mt.ASPHALT, 0.25f)
        for (k in 0 until n) {
            val a0 = (k * 2 * Math.PI / n).toFloat(); val a1 = ((k + 1) * 2 * Math.PI / n).toFloat()
            tri(b, h.x, y, h.z, h.x + cos(a0) * h.r, y, h.z + sin(a0) * h.r, h.x + cos(a1) * h.r, y, h.z + sin(a1) * h.r, 0f, 1f, 0f, COL_ASPH)
        }
        b.m(Mt.PAVER, 0.9f)
        val r2 = h.r + 2.4f; val ri = h.r * 0.45f
        val nc = 96   // meio-fio externo mais fino, para abrir a boca de cada pista sem sobrar pedaço
        for (k in 0 until nc) {
            val a0 = (k * 2 * Math.PI / nc).toFloat(); val a1 = ((k + 1) * 2 * Math.PI / nc).toFloat()
            val am = (a0 + a1) / 2f
            if (armAt(cos(am) * (h.r + 1.2f), sin(am) * (h.r + 1.2f), h)) continue
            strip(b, h.x + cos(a0) * h.r, h.z + sin(a0) * h.r, h.x + cos(a0) * r2, h.z + sin(a0) * r2, h.x + cos(a1) * h.r, h.z + sin(a1) * h.r, h.x + cos(a1) * r2, h.z + sin(a1) * r2, y + 0.05f, y + 0.05f, COL_CURB)
        }
        for (k in 0 until n) {
            val a0 = (k * 2 * Math.PI / n).toFloat(); val a1 = ((k + 1) * 2 * Math.PI / n).toFloat()
            strip(b, h.x + cos(a0) * ri, h.z + sin(a0) * ri, h.x + cos(a0) * (ri + 1.0f), h.z + sin(a0) * (ri + 1.0f), h.x + cos(a1) * ri, h.z + sin(a1) * ri, h.x + cos(a1) * (ri + 1.0f), h.z + sin(a1) * (ri + 1.0f), y + 0.06f, y + 0.06f, COL_CURB)
        }
        b.m(Mt.GRASS, 0.3f)
        for (k in 0 until n) {
            val a0 = (k * 2 * Math.PI / n).toFloat(); val a1 = ((k + 1) * 2 * Math.PI / n).toFloat()
            tri(b, h.x, y + 0.2f, h.z, h.x + cos(a0) * ri, y + 0.2f, h.z + sin(a0) * ri, h.x + cos(a1) * ri, y + 0.2f, h.z + sin(a1) * ri, 0f, 1f, 0f, COL_ISLAND)
        }
    }

    private class LazyTrees(val chunk: City.Chunk, val cheap: Mesh, val data: FloatArray) { var rich: Mesh? = null }
    private val lazyTrees = ArrayList<LazyTrees>()
    private var bldA = FloatArray(0)    // 9 por prédio: x, z, w, d, andares, ang, tipo, seed, pódio
    private var lampA = FloatArray(0)   // 4 por poste: x, z, ang, tipo
    private var hydA = FloatArray(0)    // 2 por hidrante
    private var treeA = FloatArray(0)   // 6 por árvore: x, z, espécie, escala, giro, tom

    private val FAC_HOUSE = intArrayOf(C("#F2E3C6"), C("#E8C9A0"), C("#D9E4EA"), C("#EBD3D0"), C("#CFE0C8"), C("#F4EEDC"), C("#E3D0B5"), C("#F0DDB0"))
    private val FAC_APT = intArrayOf(C("#D8D2C8"), C("#C9C3B8"), C("#E0C9B0"), C("#BFC8CE"), C("#D6BFB0"), C("#CBB8A4"), C("#E4DDD0"))
    private val FAC_SHOP = intArrayOf(C("#F0C27A"), C("#E7A98F"), C("#B9D3C2"), C("#E9DDA6"), C("#C7B9D9"), C("#F2B8B0"), C("#BFD6E8"))
    private val FAC_OFFICE = intArrayOf(C("#9FB8CC"), C("#8FA6B8"), C("#A9BFCB"), C("#B7C4CC"), C("#7F9DB5"))
    private val FAC_TOWER = intArrayOf(C("#6F93B3"), C("#5F83A6"), C("#7FA2BC"), C("#8AA9B8"), C("#4F7092"))
    private val ROOFS = intArrayOf(C("#B5523B"), C("#9C4A38"), C("#6E6A66"), C("#8C5B3C"), C("#5E6670"))
    private val AWNINGS = intArrayOf(C("#C62828"), C("#1565C0"), C("#2E7D32"), C("#EF6C00"), C("#6A1B9A"), C("#00838F"))
    private val COL_FOUND = C("#8A8478")
    private val COL_FLAT = C("#8C8F94")
    private val COL_POLE = C("#3A3F47")
    private val COL_LAMP = C("#FFF3C4")
    private val COL_HYD = C("#D32F2F")
    private val COL_BRICK = C("#9C5A44")
    private val TREE_COL = intArrayOf(C("#4F9A55"), C("#6BB45C"), C("#E7A9BE"), C("#2F7A4A"))
    private val TREE_SP = arrayOf("oak_a", "oak_b", "cherry_a", "pine_a")

    /** Etapa 184: quadrilátero (4 pontos, 4 UV) com a ordem dos vértices ajustada à normal (a face aparece por fora). */
    private fun quadN(b: MB, p: FloatArray, uv: FloatArray, nx: Float, ny: Float, nz: Float, c: Int, lit: Boolean = true) {
        val ax = p[3] - p[0]; val ay = p[4] - p[1]; val az = p[5] - p[2]
        val bx = p[6] - p[0]; val by = p[7] - p[1]; val bz = p[8] - p[2]
        val gx = ay * bz - az * by; val gy = az * bx - ax * bz; val gz = ax * by - ay * bx
        val ord = if (gx * nx + gy * ny + gz * nz < 0f) intArrayOf(0, 2, 1, 0, 3, 2) else intArrayOf(0, 1, 2, 0, 2, 3)
        val l = if (lit) 1f else 0f
        for (i in ord) b.v(p[i * 3], p[i * 3 + 1], p[i * 3 + 2], nx * l, ny * l, nz * l, c, uv[i * 2], uv[i * 2 + 1])
    }

    private fun triN(b: MB, p: FloatArray, nx: Float, ny: Float, nz: Float, c: Int) {
        val ax = p[3] - p[0]; val ay = p[4] - p[1]; val az = p[5] - p[2]
        val bx = p[6] - p[0]; val by = p[7] - p[1]; val bz = p[8] - p[2]
        val gx = ay * bz - az * by; val gy = az * bx - ax * bz; val gz = ax * by - ay * bx
        val ord = if (gx * nx + gy * ny + gz * nz < 0f) intArrayOf(0, 2, 1) else intArrayOf(0, 1, 2)
        for (i in ord) b.v(p[i * 3], p[i * 3 + 1], p[i * 3 + 2], nx, ny, nz, c, p[i * 3], p[i * 3 + 2])
    }

    /** caixa girada (ang = direção do eixo "largura" no plano XZ). Paredes com UV de fachada (u = metros ao longo, v = y). */
    private fun obox(b: MB, cx: Float, cz: Float, w: Float, d: Float, ang: Float, y0: Float, y1: Float, col: Int, top: Boolean = true, topCol: Int = col, lit: Boolean = true) {
        val c = cos(ang); val s = sin(ang)
        val lu = floatArrayOf(-w / 2f, w / 2f, w / 2f, -w / 2f); val lv = floatArrayOf(-d / 2f, -d / 2f, d / 2f, d / 2f)
        val xs = FloatArray(4) { cx + c * lu[it] - s * lv[it] }; val zs = FloatArray(4) { cz + s * lu[it] + c * lv[it] }
        for (k in 0..3) {
            val k2 = (k + 1) % 4
            var nx = (xs[k] + xs[k2]) / 2f - cx; var nz = (zs[k] + zs[k2]) / 2f - cz
            val l = hypot(nx, nz).coerceAtLeast(1e-4f); nx /= l; nz /= l
            val len = hypot(xs[k2] - xs[k], zs[k2] - zs[k])
            quadN(b, floatArrayOf(xs[k], y0, zs[k], xs[k2], y0, zs[k2], xs[k2], y1, zs[k2], xs[k], y1, zs[k]),
                floatArrayOf(0f, y0, len, y0, len, y1, 0f, y1), nx, 0f, nz, col, lit)
        }
        if (top) quadN(b, floatArrayOf(xs[0], y1, zs[0], xs[1], y1, zs[1], xs[2], y1, zs[2], xs[3], y1, zs[3]),
            floatArrayOf(xs[0], zs[0], xs[1], zs[1], xs[2], zs[2], xs[3], zs[3]), 0f, 1f, 0f, topCol, lit)
    }

    /** ponto do mundo a partir do centro do prédio e coordenadas locais (u ao longo, v em profundidade) */
    private fun wx(cx: Float, ang: Float, u: Float, v: Float) = cx + cos(ang) * u - sin(ang) * v
    private fun wz(cz: Float, ang: Float, u: Float, v: Float) = cz + sin(ang) * u + cos(ang) * v

    /** Etapa 184: um prédio/casa. Devolve a altura do topo (para o corte de visibilidade do pedaço). */
    private fun emitBuilding(b: MB, i: Int): Float {
        val o = i * 9
        val x = bldA[o] + CX; val z = bldA[o + 1] + CZ; val w = bldA[o + 2]; val d = bldA[o + 3]
        val fl = bldA[o + 4].toInt().coerceAtLeast(1); val ang = bldA[o + 5]; val kind = bldA[o + 6].toInt(); val seed = bldA[o + 7].toInt(); val pod = bldA[o + 8].toInt()
        val rg = java.util.Random(seed.toLong())
        var hmax = -1e9f; var hmin = 1e9f
        for (k in 0..4) {
            val u = if (k == 4) 0f else (if (k % 2 == 0) -w / 2f else w / 2f); val v = if (k == 4) 0f else (if (k < 2) -d / 2f else d / 2f)
            val h = height(wx(x, ang, u, v), wz(z, ang, u, v)); if (h > hmax) hmax = h; if (h < hmin) hmin = h
        }
        val y0 = hmax + 0.15f
        b.m(Mt.PLAIN, 1f)
        obox(b, x, z, w + 0.2f, d + 0.2f, ang, hmin - 0.6f, y0, COL_FOUND, false)
        val pal = when (kind) { 0, 1 -> FAC_HOUSE; 2 -> FAC_SHOP; 3 -> FAC_APT; 4 -> FAC_OFFICE; else -> FAC_TOWER }
        val col = pal[rg.nextInt(pal.size)]
        fun walls(yb: Float, floors: Int, ww: Float, dd: Float, top: Boolean, c: Int): Float {
            b.m(Mt.FACADE, 1f / 3f, 0f, -y0 / 3f)
            obox(b, x, z, ww, dd, ang, yb, yb + floors * 3f, c, false)
            return yb + floors * 3f
        }
        var yt: Float
        when (kind) {
            0, 1 -> {
                yt = walls(y0, fl, w, d, false, col)
                val rc = ROOFS[rg.nextInt(ROOFS.size)]
                val hx = w / 2f + 0.4f; val hz = d / 2f + 0.5f
                val rh = min(d * 0.34f, if (kind == 1) 3.6f else 2.8f)
                fun P(u: Float, v: Float, y: Float) = floatArrayOf(wx(x, ang, u, v), y, wz(z, ang, u, v))
                val a0 = P(-hx, -hz, yt); val a1 = P(hx, -hz, yt); val a2 = P(hx, 0f, yt + rh); val a3 = P(-hx, 0f, yt + rh)
                val b0 = P(-hx, hz, yt); val b1 = P(hx, hz, yt); val b2 = P(hx, 0f, yt + rh); val b3 = P(-hx, 0f, yt + rh)
                val nl = hypot(rh, hz)
                val fvx = -(-sin(ang)); val fvz = -cos(ang)   // direção "frente" (-v)
                b.m(Mt.ROOF, 0.5f)
                quadN(b, a0 + a1 + a2 + a3, floatArrayOf(-hx, 0f, hx, 0f, hx, nl, -hx, nl), fvx * rh / nl, hz / nl, fvz * rh / nl, rc)
                quadN(b, b0 + b1 + b2 + b3, floatArrayOf(-hx, 0f, hx, 0f, hx, nl, -hx, nl), -fvx * rh / nl, hz / nl, -fvz * rh / nl, rc)
                b.m(Mt.PLAIN, 1f)
                val gr = rh * (d / 2f) / hz
                for (sgn in floatArrayOf(-1f, 1f)) {
                    val ux = cos(ang) * sgn; val uz = sin(ang) * sgn
                    triN(b, P(sgn * w / 2f, -d / 2f, yt) + P(sgn * w / 2f, d / 2f, yt) + P(sgn * w / 2f, 0f, yt + gr), ux, 0f, uz, col)
                }
                // porta e chaminé
                val du = (rg.nextFloat() - 0.5f) * (w - 3f)
                obox(b, wx(x, ang, du, -d / 2f - 0.08f), wz(z, ang, du, -d / 2f - 0.08f), 1.1f, 0.2f, ang, y0, y0 + 2.1f, C("#5B4636"))
                if (rg.nextInt(3) == 0) obox(b, wx(x, ang, w * 0.25f, 0f), wz(z, ang, w * 0.25f, 0f), 0.7f, 0.7f, ang, yt + rh * 0.3f, yt + rh + 1.1f, COL_BRICK)
                yt += rh + 1.1f
            }
            2 -> {
                yt = walls(y0, fl, w, d, true, col)
                b.m(Mt.PLAIN, 1f)
                obox(b, x, z, w + 0.4f, d + 0.4f, ang, yt, yt + 0.35f, COL_FLAT)   // laje com beiral
                // toldo da loja (frente = -v)
                val ac = AWNINGS[rg.nextInt(AWNINGS.size)]
                obox(b, wx(x, ang, 0f, -d / 2f - 0.75f), wz(z, ang, 0f, -d / 2f - 0.75f), w - 0.6f, 1.5f, ang, y0 + 3.0f, y0 + 3.25f, ac)
                yt += 0.35f
            }
            3 -> {
                yt = walls(y0, fl, w, d, true, col)
                b.m(Mt.PLAIN, 1f)
                obox(b, x, z, w + 0.5f, d + 0.5f, ang, yt, yt + 0.5f, COL_FLAT)
                yt += 0.5f
                if (rg.nextInt(3) == 0 && fl > 4) { b.m(Mt.FACADE, 1f / 3f, 0f, -y0 / 3f); obox(b, x, z, w * 0.6f, d * 0.6f, ang, yt, yt + 3f, col, false); b.m(Mt.PLAIN, 1f); obox(b, x, z, w * 0.66f, d * 0.66f, ang, yt + 3f, yt + 3.4f, COL_FLAT); yt += 3.4f }
            }
            4 -> {
                val base = if (pod > 0) pod else 0
                var y = y0
                if (base > 0) y = walls(y0, base, w, d, true, col)
                val tw = if (base > 0) w * 0.78f else w; val td = if (base > 0) d * 0.78f else d
                yt = walls(y, fl - base, tw, td, true, col)
                b.m(Mt.PLAIN, 1f)
                obox(b, x, z, tw + 0.5f, td + 0.5f, ang, yt, yt + 0.5f, COL_FLAT)
                yt += 0.5f
            }
            else -> {
                val base = pod.coerceAtLeast(2)
                var y = walls(y0, base, w, d, true, C("#B9B2A6"))
                b.m(Mt.PLAIN, 1f)
                obox(b, x, z, w + 0.5f, d + 0.5f, ang, y, y + 0.4f, COL_FLAT); y += 0.4f
                val tw = w * 0.7f; val td = d * 0.7f
                b.m(Mt.FACADE, 1f / 3f, 0f, -y0 / 3f)
                yt = y + (fl - base) * 3f
                obox(b, x, z, tw, td, ang, y, yt, col, false)
                // coroa do topo
                b.m(Mt.PLAIN, 1f)
                obox(b, x, z, tw + 0.5f, td + 0.5f, ang, yt, yt + 0.6f, C("#5E6670"))
                obox(b, x, z, tw * 0.5f, td * 0.5f, ang, yt + 0.6f, yt + 3.2f, C("#7C838C"))
                obox(b, x, z, 0.35f, 0.35f, ang, yt + 3.2f, yt + 11f, C("#C8CCD2"))
                yt += 11f
            }
        }
        if (kind in 3..4) {   // casa de máquinas e ar-condicionado no telhado
            b.m(Mt.PLAIN, 1f)
            val tw = if (kind == 4 && pod > 0) w * 0.78f else w
            obox(b, wx(x, ang, -tw * 0.22f, 0f), wz(z, ang, -tw * 0.22f, 0f), 3.2f, 3.0f, ang, yt, yt + 2.6f, C("#A5A9B0"))
            obox(b, wx(x, ang, tw * 0.25f, 1.5f), wz(z, ang, tw * 0.25f, 1.5f), 2.0f, 1.6f, ang, yt, yt + 1.2f, C("#8E9298"))
            yt += 2.6f
        }
        return yt
    }

    /** poste de luz: haste, braço para a pista e luminária (sem iluminação, brilha) */
    private fun emitLamp(b: MB, i: Int) {
        val o = i * 4
        val x = lampA[o] + CX; val z = lampA[o + 1] + CZ; val ang = lampA[o + 2]; val av = lampA[o + 3] > 0.5f
        val y = groundH(x, z)
        val hgt = if (av) 8.5f else 5.8f; val arm = if (av) 2.4f else 1.5f
        b.m(Mt.PLAIN, 1f)
        obox(b, x, z, 0.22f, 0.22f, 0f, y, y + 0.5f, C("#4B515A"))
        obox(b, x, z, 0.14f, 0.14f, 0f, y + 0.5f, y + hgt, COL_POLE)
        val dx = cos(ang); val dz = sin(ang)
        obox(b, x + dx * arm / 2f, z + dz * arm / 2f, arm, 0.1f, ang, y + hgt - 0.12f, y + hgt, COL_POLE)
        obox(b, x + dx * arm, z + dz * arm, 0.75f, 0.32f, ang, y + hgt - 0.2f, y + hgt - 0.02f, COL_LAMP, true, COL_LAMP, false)
        if (av) {   // avenida: segundo braço para o outro lado
            obox(b, x - dx * arm / 2f, z - dz * arm / 2f, arm, 0.1f, ang, y + hgt - 0.12f, y + hgt, COL_POLE)
            obox(b, x - dx * arm, z - dz * arm, 0.75f, 0.32f, ang, y + hgt - 0.2f, y + hgt - 0.02f, COL_LAMP, true, COL_LAMP, false)
        }
    }

    private fun emitHydrant(b: MB, i: Int) {
        val x = hydA[i * 2] + CX; val z = hydA[i * 2 + 1] + CZ
        val y = groundH(x, z)
        b.m(Mt.PLAIN, 1f)
        obox(b, x, z, 0.3f, 0.3f, 0f, y, y + 0.65f, COL_HYD)
        obox(b, x, z, 0.38f, 0.38f, 0f, y + 0.55f, y + 0.72f, C("#B71C1C"))
        obox(b, x, z, 0.52f, 0.14f, 0f, y + 0.32f, y + 0.46f, COL_HYD)
    }

    private val TREE_IDS = arrayOf("oak_a", "oak_b", "cherry_a", "pine_a")

    /**
     * Etapa 183b/c: chamado a cada quadro pela thread do GL (City.service). Troca as árvores leves pelas modeladas do HDS
     * nos pedaços a menos de TREE_NEAR do jogador (o mais perto primeiro, um por quadro) e devolve a memória dos que
     * passam de TREE_FAR. Trava de memória: acima de 72% do heap não monta mais nenhum e solta o pedaço detalhado mais longe.
     */
    private const val TREE_NEAR = 260f
    private const val TREE_FAR = 340f

    fun service(ex: Float, ez: Float) {
        if (!on) return
        var best: LazyTrees? = null; var bestD = TREE_NEAR * TREE_NEAR
        var worst: LazyTrees? = null; var worstD = 0f
        for (t in lazyTrees) {
            val c = t.chunk
            val dx = max(0f, max(c.x0 - ex, ex - c.x1)); val dz = max(0f, max(c.z0 - ez, ez - c.z1))
            val d2 = dx * dx + dz * dz
            val rich = t.rich
            if (rich == null) {
                if (d2 < bestD) { bestD = d2; best = t }
            } else if (d2 > TREE_FAR * TREE_FAR) {
                c.near = t.cheap; t.rich = null; rich.release()
            } else if (d2 > worstD) { worstD = d2; worst = t }
        }
        val rt = Runtime.getRuntime()
        val tight = (rt.totalMemory() - rt.freeMemory()) > rt.maxMemory() * 0.72
        if (tight) {   // memória apertada: solta o detalhado mais longe e não monta nada novo neste quadro
            worst?.let { w -> w.rich?.release(); w.chunk.near = w.cheap; w.rich = null }
            return
        }
        val t = best ?: return
        val fl = Flora.Batch(); fl.fixedY = 0f
        var i = 0
        while (i + 6 < t.data.size) {
            val k = t.data[i + 6]
            fl.place(TREE_IDS[t.data[i].toInt().coerceIn(0, 3)], t.data[i + 1].toDouble(), t.data[i + 2].toDouble(), t.data[i + 3].toDouble(), t.data[i + 4].toDouble(), t.data[i + 5].toDouble(), k, k, k)
            i += 7
        }
        val parts = fl.build()
        if (parts.isNotEmpty()) { val m = Mesh(parts).gpuOnly(); t.rich = m; t.chunk.near = m }
    }

    private fun bedCol(h: Float): Int = mix(COL_BED, C("#5D6F73"), ((-0.2f - h) / 7f).coerceIn(0f, 1f))

    /** árvore simples e fofinha: tronco e copa em dois cones (bipirâmide de 6 lados) */
    private fun tree(b: MB, px: Float, py: Float, pz: Float, s: Float, col: Int) {
        b.m(Mt.PLAIN, 1f)
        b.box(px, py + 0.65f * s, pz, 0.34f * s, 1.3f * s, 0.34f * s, COL_TRUNK)
        val yb = py + 1.0f * s; val ym = py + 2.5f * s; val yt = py + 4.4f * s; val r = 1.6f * s
        val n = 6
        for (k in 0 until n) {
            val a0 = (k * 2 * Math.PI / n).toFloat(); val a1 = ((k + 1) * 2 * Math.PI / n).toFloat(); val am = (a0 + a1) / 2f
            val x0 = px + cos(a0) * r; val z0 = pz + sin(a0) * r; val x1 = px + cos(a1) * r; val z1 = pz + sin(a1) * r
            val ct = cos(am); val st = sin(am)
            var hd = yt - ym; var l = sqrt(hd * hd + r * r)
            tri(b, x0, ym, z0, x1, ym, z1, px, yt, pz, ct * hd / l, r / l, st * hd / l, col)
            hd = ym - yb; l = sqrt(hd * hd + r * r)
            tri(b, x0, ym, z0, px, yb, pz, x1, ym, z1, ct * hd / l, -r / l, st * hd / l, shade(col, -18))
        }
    }

    /**
     * Monta o terreno em pedaços de 64 m (um [City.Chunk] por pedaço) com água, ruas, rotatórias, pontes e árvores.
     * [plots]: retângulos (x0, z0, x1, z1) das casas no mundo (sem árvores em volta delas).
     */
    fun build(out: ArrayList<City.Chunk>, plots: List<FloatArray>) {
        if (!on) return
        lazyTrees.clear()
        val ncx = (nx - 1 + CS - 1) / CS; val ncz = (nz - 1 + CS - 1) / CS
        val csize = CS * g
        val segs = HashMap<Int, ArrayList<IntArray>>()
        for ((ri, r) in roads.withIndex()) for (q in 0 until r.x.size - 1) {
            if (!r.keep[q]) continue
            val mx = (r.x[q] + r.x[q + 1]) / 2f; val mz = (r.z[q] + r.z[q + 1]) / 2f
            val ci = ((mx - CX) / csize).toInt().coerceIn(0, ncx - 1); val cj = ((mz - CZ) / csize).toInt().coerceIn(0, ncz - 1)
            segs.getOrPut(cj * 1000 + ci) { ArrayList() }.add(intArrayOf(ri, q))
        }
        val hubB = HashMap<Int, ArrayList<Hub>>()
        for (h in hubs) {
            val ci = ((h.x - CX) / csize).toInt().coerceIn(0, ncx - 1); val cj = ((h.z - CZ) / csize).toInt().coerceIn(0, ncz - 1)
            hubB.getOrPut(cj * 1000 + ci) { ArrayList() }.add(h)
        }
        val padB = HashMap<Int, ArrayList<Pad>>()
        for (p in pads) {
            val ci = ((p.x - CX) / csize).toInt().coerceIn(0, ncx - 1); val cj = ((p.z - CZ) / csize).toInt().coerceIn(0, ncz - 1)
            padB.getOrPut(cj * 1000 + ci) { ArrayList() }.add(p)
        }
        fun binOf(arr: FloatArray, st: Int): HashMap<Int, ArrayList<Int>> {
            val m = HashMap<Int, ArrayList<Int>>()
            for (k in 0 until arr.size / st) {
                val ci = ((arr[k * st] - 0f) / csize).toInt().coerceIn(0, ncx - 1); val cj = ((arr[k * st + 1]) / csize).toInt().coerceIn(0, ncz - 1)
                m.getOrPut(cj * 1000 + ci) { ArrayList() }.add(k)
            }
            return m
        }
        val bldB = binOf(bldA, 9); val lampB = binOf(lampA, 4); val hydB = binOf(hydA, 2); val treeB = binOf(treeA, 6)

        val total = ncx * ncz
        for (cj in 0 until ncz) for (ci in 0 until ncx) {
            City.step(0.55f + 0.4f * (cj * ncx + ci) / total)
            val i0 = ci * CS; val i1 = min(i0 + CS, nx - 1); val j0 = cj * CS; val j1 = min(j0 + CS, nz - 1)
            val tx0 = CX + i0 * g; val tx1 = CX + i1 * g; val tz0 = CZ + j0 * g; val tz1 = CZ + j1 * g
            val b = MB()
            var ymax = -1e9f
            for (j in j0 until j1) for (i in i0 until i1) {
                val h00 = hh(i, j); val h10 = hh(i + 1, j); val h01 = hh(i, j + 1); val h11 = hh(i + 1, j + 1)
                ymax = max(ymax, max(max(h00, h10), max(h01, h11)))
                val x0 = CX + i * g; val x1 = x0 + g; val z0 = CZ + j * g; val z1 = z0 + g
                val avg = (h00 + h10 + h01 + h11) / 4f
                val lo = min(min(h00, h10), min(h01, h11))
                val mode = if (avg < -0.1f) 0 else if (sandMask.isNotEmpty()) {
                    val ns = (if (sandAt(i, j)) 1 else 0) + (if (sandAt(i + 1, j)) 1 else 0) + (if (sandAt(i, j + 1)) 1 else 0) + (if (sandAt(i + 1, j + 1)) 1 else 0)
                    if (ns >= 2 && avg < 1.6f) 1 else 2
                } else if (avg < 1.3f) 1 else 2
                if (mode == 2) b.m(Mt.GRASS, 0.3f) else b.m(Mt.PLAIN, 1f)
                // cor por vértice: na grama, a rocha entra aos poucos com a inclinação do PRÓPRIO vértice (sem quadrados de 8 m)
                // no fundo, o vertice que fica ACIMA da agua na beira da praia e areia (senao aparece uma serra marrom na linha d'agua)
                fun bc(ii: Int, jj: Int, h: Float): Int = if (h > -0.15f && sandMask.isNotEmpty() && (sandAt(ii, jj) || h > 0f)) COL_SAND else bedCol(h)
                val c00 = if (mode == 0) bc(i, j, h00) else if (mode == 1) COL_SAND else 0
                val c10 = if (mode == 0) bc(i + 1, j, h10) else if (mode == 1) COL_SAND else 0
                val c01 = if (mode == 0) bc(i, j + 1, h01) else if (mode == 1) COL_SAND else 0
                val c11 = if (mode == 0) bc(i + 1, j + 1, h11) else if (mode == 1) COL_SAND else 0
                // normais por vértice (diferença central)
                fun nv(ii: Int, jj: Int, h: Float, x: Float, z: Float, c0: Int) {
                    val dx = (hh(ii + 1, jj) - hh(ii - 1, jj)) / (2f * g); val dz = (hh(ii, jj + 1) - hh(ii, jj - 1)) / (2f * g)
                    val l = sqrt(dx * dx + 1f + dz * dz)
                    var c = c0
                    if (mode == 2) {
                        val rk = ((sqrt(dx * dx + dz * dz) - 0.55f) / 0.45f).coerceIn(0f, 1f)
                        c = mix(grassCol(h), COL_ROCK, rk * rk * 0.85f)
                        if (h < 1.3f && sandMask.isEmpty()) c = mix(c, COL_SAND, 0.75f)
                    }
                    b.v(x, h, z, -dx / l, 1f / l, -dz / l, c, x, z)
                }
                nv(i, j, h00, x0, z0, c00); nv(i + 1, j, h10, x1, z0, c10); nv(i + 1, j + 1, h11, x1, z1, c11)
                nv(i, j, h00, x0, z0, c00); nv(i + 1, j + 1, h11, x1, z1, c11); nv(i, j + 1, h01, x0, z1, c01)
                if (lo < -0.15f) {
                    b.m(Mt.PLAIN, 1f)
                    // Etapa 183: cor por profundidade (rasa turquesa -> funda azul) com espuma onde encosta na margem
                    fun wc(h: Float): Int {
                        val d = (-0.2f - h).coerceIn(0f, 9f) / 9f
                        val body = mix(COL_SHAL, COL_DEEP, sqrt(d))
                        return mix(body, COL_FOAM, (1f - (-0.2f - h) / 0.55f).coerceIn(0f, 1f) * 0.8f)
                    }
                    val w00 = wc(h00); val w10 = wc(h10); val w01 = wc(h01); val w11 = wc(h11)
                    b.v(x0, -0.2f, z0, 0f, 1f, 0f, w00, x0, z0); b.v(x1, -0.2f, z0, 0f, 1f, 0f, w10, x1, z0); b.v(x1, -0.2f, z1, 0f, 1f, 0f, w11, x1, z1)
                    b.v(x0, -0.2f, z0, 0f, 1f, 0f, w00, x0, z0); b.v(x1, -0.2f, z1, 0f, 1f, 0f, w11, x1, z1); b.v(x0, -0.2f, z1, 0f, 1f, 0f, w01, x0, z1)
                }
            }
            var ext = 0f
            val sl = segs[cj * 1000 + ci]
            if (sl != null) {
                ext = 40f
                for (s in sl) { val r = roads[s[0]]; emitSeg(b, r, s[1]); ymax = max(ymax, max(r.y[s[1]], r.y[s[1] + 1]) + 1.5f) }
            }
            val hl = hubB[cj * 1000 + ci]
            if (hl != null) { ext = 40f; for (h in hl) { emitHub(b, h); ymax = max(ymax, h.y + 1f) } }
            val pdl = padB[cj * 1000 + ci]
            if (pdl != null) { ext = 40f; for (p in pdl) { emitPad(b, p); ymax = max(ymax, p.y + 1f) } }
            bldB[cj * 1000 + ci]?.let { l -> ext = 40f; for (k in l) ymax = max(ymax, emitBuilding(b, k)) }
            lampB[cj * 1000 + ci]?.let { l -> ext = 40f; for (k in l) emitLamp(b, k); ymax += 9.5f }
            hydB[cj * 1000 + ci]?.let { l -> ext = 40f; for (k in l) emitHydrant(b, k) }
            if (sub) subCells[cj * 1000 + ci]?.let { l ->   // Etapa 185: casas, garagens, cercas, carros, caixas de correio, postes...
                ext = 40f
                for (rc in l) {
                    b.m(rc.mat, 1f)
                    for (q in 0 until rc.nv) {
                        val o = q * 8
                        b.v(rc.f[o] + CX, rc.f[o + 1], rc.f[o + 2] + CZ, rc.f[o + 3], rc.f[o + 4], rc.f[o + 5],
                            android.graphics.Color.rgb(rc.c[q * 3].toInt() and 255, rc.c[q * 3 + 1].toInt() and 255, rc.c[q * 3 + 2].toInt() and 255), rc.f[o + 6], rc.f[o + 7])
                    }
                    ymax = max(ymax, rc.ymax)
                }
            }
            if (!b.isEmpty()) {
                val c = City.Chunk(b.toMesh(true).gpuOnly(), null, tx0 - ext, tz0 - ext, tx1 + ext, tz1 + ext, ymax + 1.5f)
                c.terrain = true   // pedaço de terreno: aparece de mais longe (ver Renderer3D)
                out.add(c)
            }
            // árvores deste pedaço (chunk à parte: só aparecem de perto)
            val tb = MB()
            val tdata = ArrayList<Float>()   // Etapa 183b: árvores modeladas do HDS, montadas só perto do jogador (cada uma tem ~7 mil vértices)
            var ty1 = 0f
            treeB[cj * 1000 + ci]?.let { l ->
                for (k in l) {
                    val o = k * 6
                    val px = treeA[o] + CX; val pz = treeA[o + 1] + CZ; val sp = treeA[o + 2].toInt().coerceIn(0, 3); val sc = treeA[o + 3]
                    val h = groundH(px, pz)
                    if (h < 1.0f) continue
                    tree(tb, px, h - 0.05f, pz, sc * 0.9f, TREE_COL[sp])   // versão leve, sempre visível
                    tdata.add(sp.toFloat()); tdata.add(px); tdata.add(h - 0.05f); tdata.add(pz); tdata.add(sc); tdata.add(treeA[o + 4]); tdata.add(treeA[o + 5])
                    ty1 = max(ty1, h + 9f * sc)
                }
            }
            if (!tb.isEmpty()) {
                val cheap = tb.toMesh(true).gpuOnly()
                val tc = City.Chunk(cheap, null, tx0 - 12f, tz0 - 12f, tx1 + 12f, tz1 + 12f, ty1 + 1f)
                out.add(tc)
                if (tdata.isNotEmpty()) lazyTrees.add(LazyTrees(tc, cheap, tdata.toFloatArray()))
            }
        }
        buildMap()
    }

    /** imagem do mapa (4 m por pixel): água, relevo sombreado, ruas e rotatórias */
    private fun buildMap() {
        val w = (worldW / 4f).toInt(); val hgt = (worldH / 4f).toInt()
        val px = IntArray(w * hgt)
        for (j in 0 until hgt) for (i in 0 until w) {
            val x = CX + (i + 0.5f) * 4f; val z = CZ + (j + 0.5f) * 4f
            val h = height(x, z)
            val sh = ((height(x - 4f, z) - height(x + 4f, z)) + (height(x, z - 4f) - height(x, z + 4f))) * 0.12f
            val k = (1f + sh).coerceIn(0.7f, 1.25f)
            var r: Float; var gg: Float; var bl: Float
            if (h < -0.15f) { val d = (-h / 3f).coerceIn(0f, 1f); r = 100f - 30f * d; gg = 170f - 30f * d; bl = 215f - 20f * d }
            else if (h < 1.3f) { r = 226f; gg = 214f; bl = 168f }
            else { val t = (h / 60f).coerceIn(0f, 1f); r = 150f + 70f * t; gg = 200f + 20f * t; bl = 120f + 30f * t }
            if (h >= -0.15f) { r *= k; gg *= k; bl *= k }
            px[j * w + i] = (0xFF shl 24) or (min(255f, r).toInt() shl 16) or (min(255f, gg).toInt() shl 8) or min(255f, bl).toInt()
        }
        val bmp = Bitmap.createBitmap(w, hgt, Bitmap.Config.ARGB_8888)
        bmp.setPixels(px, 0, w, 0, 0, w, hgt)
        val cv = Canvas(bmp)
        val p = Paint(Paint.ANTI_ALIAS_FLAG)
        p.style = Paint.Style.STROKE; p.strokeCap = Paint.Cap.ROUND; p.strokeJoin = Paint.Join.ROUND
        fun path(r: Road): Path {
            val pa = Path()
            var started = false
            for (q in 0 until r.x.size - 1) {
                if (!r.keep[q]) continue
                if (!started) { pa.moveTo((r.x[q] - CX) / 4f, (r.z[q] - CZ) / 4f); started = true }
                pa.lineTo((r.x[q + 1] - CX) / 4f, (r.z[q + 1] - CZ) / 4f)
            }
            return pa
        }
        for (r in roads) { p.color = 0xFF455A64.toInt(); p.strokeWidth = r.w / 4f * 1.1f + 1.6f; cv.drawPath(path(r), p) }
        p.style = Paint.Style.FILL
        for (pd in pads) { p.color = 0xFF455A64.toInt(); cv.drawCircle((pd.x - CX) / 4f, (pd.z - CZ) / 4f, padR(pd) / 4f + 0.8f, p) }
        p.style = Paint.Style.STROKE
        for (r in roads) {
            p.color = if (r.c == 0) 0xFFFF9800.toInt() else if (r.c == 3) 0xFFEEE6DF.toInt() else 0xFFFFFFFF.toInt()
            p.strokeWidth = r.w / 4f * 1.1f; cv.drawPath(path(r), p)
        }
        p.style = Paint.Style.FILL
        p.color = 0xFFEEE6DF.toInt()
        for (pd in pads) cv.drawCircle((pd.x - CX) / 4f, (pd.z - CZ) / 4f, padR(pd) / 4f, p)
        for (h in hubs) {
            val x = (h.x - CX) / 4f; val z = (h.z - CZ) / 4f
            p.color = 0xFF455A64.toInt(); cv.drawCircle(x, z, h.r / 4f + 1.5f, p)
            p.color = 0xFFFFFFFF.toInt(); cv.drawCircle(x, z, h.r / 4f, p)
            p.color = 0xFF66BB6A.toInt(); cv.drawCircle(x, z, h.r / 4f * 0.45f, p)
        }
        mapBmp = bmp
    }

    /** desenha o mapa do relevo (coordenadas do mundo) */
    fun drawMap(c: Canvas) {
        val bm = mapBmp ?: return
        c.drawBitmap(bm, null, RectF(CX, CZ, CX + worldW, CZ + worldH), null)
    }
}
