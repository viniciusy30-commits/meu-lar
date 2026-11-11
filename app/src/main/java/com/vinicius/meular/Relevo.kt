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
    private class Road(val c: Int, val w: Float, val x: FloatArray, val z: FloatArray, val y: FloatArray, val br: BooleanArray, val nx: FloatArray, val nz: FloatArray, val keep: BooleanArray)
    private class Hub(val x: Float, val z: Float, val r: Float, val y: Float)
    /** Etapa 179: placa de cruzamento (kind 0) ou fim de rua em balão (kind 1) */
    private class Pad(val x: Float, val z: Float, val r: Float, val y: Float, val kind: Int)

    @Volatile var on = false
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
    private fun padR(p: Pad): Float = if (p.kind == 1) p.r else p.r * 1.25f + 1.2f
    private val segGrid = HashMap<Int, ArrayList<IntArray>>()   // células de 32 m -> (rua, trecho) que passam por ali (para o chão)
    private val houses = HashMap<Int, House>()
    @Volatile private var mapBmp: Bitmap? = null

    private val COL_WATER = C("#4F9BD0")
    private val COL_BED = C("#A8966F")
    private val COL_SAND = C("#E6D6A4")
    private val COL_ROCK = C("#A89C84")
    private val COL_ASPH = C("#D0D0D0")
    private val COL_CURB = C("#CFCAC0")
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
        mapBmp = null   // sem recycle: o mapa pode estar sendo desenhado agora
    }

    /** Lê os dados do relevo. false se os arquivos não existem (aí vale a Cidade 2 antiga). */
    fun load(am: AssetManager): Boolean {
        on = false
        try {
            val bb = ByteBuffer.wrap(am.open("hds/relevo.bin").use { it.readBytes() }).order(ByteOrder.LITTLE_ENDIAN)
            nx = bb.getInt(); nz = bb.getInt(); g = bb.getFloat()
            val h = ShortArray(nx * nz)
            for (i in h.indices) h[i] = bb.getShort()
            val js = JSONObject(am.open("hds/city3.json").bufferedReader().use { it.readText() })
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
                val w = o.getDouble("w").toFloat()
                // Etapa 179: cada trecho vai de cruzamento a cruzamento; as pontas dentro do cruzamento (a, b) não são desenhadas
                val ta = o.optDouble("a", 0.0).toFloat(); val tb = o.optDouble("b", 0.0).toFloat()
                val cs = FloatArray(n)
                for (q in 1 until n) cs[q] = cs[q - 1] + hypot(x[q] - x[q - 1], z[q] - z[q - 1])
                val tot = cs[n - 1]
                val keep = BooleanArray(n - 1) { q -> cs[q] >= ta - 0.4f && cs[q + 1] <= tot - tb + 0.4f }
                roads.add(Road(o.getInt("c"), w, x, z, y, br, ex, ez, keep))
            }
            val ro = js.getJSONArray("rounds")
            for (i in 0 until ro.length()) {
                val o = ro.getJSONObject(i)
                hubs.add(Hub(o.getDouble("x").toFloat() + CX, o.getDouble("z").toFloat() + CZ, o.getDouble("r").toFloat(), o.getDouble("y").toFloat()))
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
            hs = h
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

    private fun curbW(r: Road) = if (r.c == 3) 1.2f else 1.8f

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
            val y = r.y[q] + (r.y[q + 1] - r.y[q]) * t + ROADY + (if (d > hw) 0.05f else 0f)
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

    private fun emitSeg(b: MB, r: Road, q: Int) {
        val hw = r.w / 2f
        val x0 = r.x[q]; val z0 = r.z[q]; val y0 = r.y[q] + ROADY
        val x1 = r.x[q + 1]; val z1 = r.z[q + 1]; val y1 = r.y[q + 1] + ROADY
        val ax = r.nx[q]; val az = r.nz[q]; val bx = r.nx[q + 1]; val bz = r.nz[q + 1]
        b.m(Mt.ASPHALT, 0.25f)
        strip(b, x0 + ax * hw, z0 + az * hw, x0 - ax * hw, z0 - az * hw, x1 + bx * hw, z1 + bz * hw, x1 - bx * hw, z1 - bz * hw, y0, y1, COL_ASPH)
        val cw = if (r.c == 3) 1.2f else 1.8f
        b.m(Mt.PAVER, 0.9f)
        strip(b, x0 + ax * hw, z0 + az * hw, x0 + ax * (hw + cw), z0 + az * (hw + cw), x1 + bx * hw, z1 + bz * hw, x1 + bx * (hw + cw), z1 + bz * (hw + cw), y0 + 0.05f, y1 + 0.05f, COL_CURB)
        strip(b, x0 - ax * hw, z0 - az * hw, x0 - ax * (hw + cw), z0 - az * (hw + cw), x1 - bx * hw, z1 - bz * hw, x1 - bx * (hw + cw), z1 - bz * (hw + cw), y0 + 0.05f, y1 + 0.05f, COL_CURB)
        b.m(Mt.PLAIN, 1f)
        if (r.c <= 2) {
            val lc = if (r.c == 0) COL_LINE_Y else COL_LINE
            strip(b, x0 + ax * 0.15f, z0 + az * 0.15f, x0 - ax * 0.15f, z0 - az * 0.15f, x1 + bx * 0.15f, z1 + bz * 0.15f, x1 - bx * 0.15f, z1 - bz * 0.15f, y0 + 0.02f, y1 + 0.02f, lc)
        }
        if (r.br[q] && r.br[q + 1]) {
            // ponte: parede lateral, parapeito e fundo
            val ow = hw + cw
            wall(b, x0 + ax * ow, z0 + az * ow, x1 + bx * ow, z1 + bz * ow, y0 + 0.05f, y0 - 1.3f, ax, az, COL_BRIDGE)
            wall(b, x0 - ax * ow, z0 - az * ow, x1 - bx * ow, z1 - bz * ow, y0 + 0.05f, y0 - 1.3f, -ax, -az, COL_BRIDGE)
            wall(b, x0 + ax * ow, z0 + az * ow, x1 + bx * ow, z1 + bz * ow, y0 + 1.0f, y0 + 0.05f, ax, az, COL_BRIDGE)
            wall(b, x0 - ax * ow, z0 - az * ow, x1 - bx * ow, z1 - bz * ow, y0 + 1.0f, y0 + 0.05f, -ax, -az, COL_BRIDGE)
            tri(b, x0 + ax * ow, y0 - 1.3f, z0 + az * ow, x0 - ax * ow, y0 - 1.3f, z0 - az * ow, x1 - bx * ow, y1 - 1.3f, z1 - bz * ow, 0f, -1f, 0f, COL_UNDER)
            tri(b, x0 + ax * ow, y0 - 1.3f, z0 + az * ow, x1 - bx * ow, y1 - 1.3f, z1 - bz * ow, x1 + bx * ow, y1 - 1.3f, z1 + bz * ow, 0f, -1f, 0f, COL_UNDER)
            if (q % 3 == 0) {   // Etapa 179: pilar sob o viaduto/ponte, do terreno até o fundo da pista
                val top = y0 - 1.3f; val gh = height(x0, z0)
                if (top - gh > 2.2f) { b.m(Mt.PLAIN, 1f); b.box(x0, (top + gh) / 2f, z0, 1.8f, top - gh, 1.8f, COL_UNDER) }
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

    private fun emitHub(b: MB, h: Hub) {
        val n = 28
        val y = h.y + ROADY
        b.m(Mt.ASPHALT, 0.25f)
        for (k in 0 until n) {
            val a0 = (k * 2 * Math.PI / n).toFloat(); val a1 = ((k + 1) * 2 * Math.PI / n).toFloat()
            tri(b, h.x, y, h.z, h.x + cos(a0) * h.r, y, h.z + sin(a0) * h.r, h.x + cos(a1) * h.r, y, h.z + sin(a1) * h.r, 0f, 1f, 0f, COL_ASPH)
        }
        b.m(Mt.PAVER, 0.9f)
        val r2 = h.r + 1.8f; val ri = h.r * 0.45f
        for (k in 0 until n) {
            val a0 = (k * 2 * Math.PI / n).toFloat(); val a1 = ((k + 1) * 2 * Math.PI / n).toFloat()
            strip(b, h.x + cos(a0) * h.r, h.z + sin(a0) * h.r, h.x + cos(a0) * r2, h.z + sin(a0) * r2, h.x + cos(a1) * h.r, h.z + sin(a1) * h.r, h.x + cos(a1) * r2, h.z + sin(a1) * r2, y + 0.05f, y + 0.05f, COL_CURB)
            strip(b, h.x + cos(a0) * ri, h.z + sin(a0) * ri, h.x + cos(a0) * (ri + 1.0f), h.z + sin(a0) * (ri + 1.0f), h.x + cos(a1) * ri, h.z + sin(a1) * ri, h.x + cos(a1) * (ri + 1.0f), h.z + sin(a1) * (ri + 1.0f), y + 0.06f, y + 0.06f, COL_CURB)
        }
        b.m(Mt.GRASS, 0.3f)
        for (k in 0 until n) {
            val a0 = (k * 2 * Math.PI / n).toFloat(); val a1 = ((k + 1) * 2 * Math.PI / n).toFloat()
            tri(b, h.x, y + 0.2f, h.z, h.x + cos(a0) * ri, y + 0.2f, h.z + sin(a0) * ri, h.x + cos(a1) * ri, y + 0.2f, h.z + sin(a1) * ri, 0f, 1f, 0f, COL_ISLAND)
        }
    }

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
        // distância às ruas (grade de 16 m) para não plantar árvores no asfalto
        val gw = (worldW / 16f).toInt() + 2; val gh = (worldH / 16f).toInt() + 2
        val rd = FloatArray(gw * gh) { 1e9f }
        fun mark(px: Float, pz: Float, rad: Float, off: Float) {
            val ci = ((px - CX) / 16f).toInt(); val cj = ((pz - CZ) / 16f).toInt()
            val k = (rad / 16f).toInt() + 1
            for (dj in -k..k) for (di in -k..k) {
                val i = ci + di; val j = cj + dj
                if (i < 0 || j < 0 || i >= gw || j >= gh) continue
                val d = hypot(CX + i * 16f - px, CZ + j * 16f - pz) - off
                if (d < rd[j * gw + i]) rd[j * gw + i] = d
            }
        }
        for (r in roads) for (q in r.x.indices) mark(r.x[q], r.z[q], 40f, r.w / 2f)
        for (h in hubs) mark(h.x, h.z, h.r + 40f, h.r)
        for (p in pads) mark(p.x, p.z, padR(p) + 40f, padR(p))

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
                val steep = max(max(abs(h10 - h00), abs(h01 - h00)), max(abs(h11 - h10), abs(h11 - h01))) / g > 0.5f
                val mode = if (avg < -0.1f) 0 else if (avg < 1.3f) 1 else 2
                if (mode == 2) b.m(Mt.GRASS, 0.3f) else b.m(Mt.PLAIN, 1f)
                val c00 = if (mode == 0) COL_BED else if (mode == 1) COL_SAND else if (steep) COL_ROCK else grassCol(h00)
                val c10 = if (mode == 0) COL_BED else if (mode == 1) COL_SAND else if (steep) COL_ROCK else grassCol(h10)
                val c01 = if (mode == 0) COL_BED else if (mode == 1) COL_SAND else if (steep) COL_ROCK else grassCol(h01)
                val c11 = if (mode == 0) COL_BED else if (mode == 1) COL_SAND else if (steep) COL_ROCK else grassCol(h11)
                // normais por vértice (diferença central)
                fun nv(ii: Int, jj: Int, h: Float, x: Float, z: Float, c: Int) {
                    val dx = (hh(ii + 1, jj) - hh(ii - 1, jj)) / (2f * g); val dz = (hh(ii, jj + 1) - hh(ii, jj - 1)) / (2f * g)
                    val l = sqrt(dx * dx + 1f + dz * dz)
                    b.v(x, h, z, -dx / l, 1f / l, -dz / l, c, x, z)
                }
                nv(i, j, h00, x0, z0, c00); nv(i + 1, j, h10, x1, z0, c10); nv(i + 1, j + 1, h11, x1, z1, c11)
                nv(i, j, h00, x0, z0, c00); nv(i + 1, j + 1, h11, x1, z1, c11); nv(i, j + 1, h01, x0, z1, c01)
                if (lo < -0.15f) {
                    b.m(Mt.PLAIN, 1f)
                    tri(b, x0, -0.2f, z0, x1, -0.2f, z0, x1, -0.2f, z1, 0f, 1f, 0f, COL_WATER)
                    tri(b, x0, -0.2f, z0, x1, -0.2f, z1, x0, -0.2f, z1, 0f, 1f, 0f, COL_WATER)
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
            if (!b.isEmpty()) {
                val c = City.Chunk(b.toMesh(true).gpuOnly(), null, tx0 - ext, tz0 - ext, tx1 + ext, tz1 + ext, ymax + 1.5f)
                c.terrain = true   // pedaço de terreno: aparece de mais longe (ver Renderer3D)
                out.add(c)
            }
            // árvores deste pedaço (chunk à parte: só aparecem de perto)
            val tb = MB()
            val ts = 26f
            val a0 = Math.ceil(((tx0 - CX) / ts).toDouble()).toInt(); val a1 = Math.ceil(((tx1 - CX) / ts).toDouble()).toInt() - 1
            val e0 = Math.ceil(((tz0 - CZ) / ts).toDouble()).toInt(); val e1 = Math.ceil(((tz1 - CZ) / ts).toDouble()).toInt() - 1
            var ty1 = 0f
            for (a in a0..a1) for (e in e0..e1) {
                val rg = java.util.Random((a * 73856093L) xor (e * 19349663L) xor 11L)
                val px = CX + a * ts + (rg.nextFloat() - 0.5f) * 14f; val pz = CZ + e * ts + (rg.nextFloat() - 0.5f) * 14f
                val roll = rg.nextFloat(); val sc = 0.8f + rg.nextFloat() * 0.8f; val cl = TREES[rg.nextInt(TREES.size)]
                if (px < CX + 10f || pz < CZ + 10f || px > CX + worldW - 10f || pz > CZ + worldH - 10f) continue
                val h = height(px, pz)
                if (h < 2.2f) continue
                if (roll > 0.16f + 0.3f * ((h - 18f) / 30f).coerceIn(0f, 1f)) continue
                val gx = abs(height(px + 4f, pz) - height(px - 4f, pz)) / 8f; val gz = abs(height(px, pz + 4f) - height(px, pz - 4f)) / 8f
                if (max(gx, gz) > 0.3f) continue
                val ri = ((px - CX) / 16f).toInt().coerceIn(0, gw - 1); val rj = ((pz - CZ) / 16f).toInt().coerceIn(0, gh - 1)
                if (rd[rj * gw + ri] < 20f) continue
                var near = false
                for (p in plots) if (px > p[0] - 14f && px < p[2] + 14f && pz > p[1] - 14f && pz < p[3] + 14f) { near = true; break }
                if (near) continue
                tree(tb, px, h - 0.05f, pz, sc, cl)
                ty1 = max(ty1, h + 5f * sc)
            }
            if (!tb.isEmpty()) out.add(City.Chunk(tb.toMesh(true).gpuOnly(), null, tx0 - 12f, tz0 - 12f, tx1 + 12f, tz1 + 12f, ty1 + 1f))
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
