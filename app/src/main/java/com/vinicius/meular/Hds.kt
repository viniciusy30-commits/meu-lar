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

    /** Etapa 166: grade de 25 cm de uma casa: máscara de paredes por faixa de 50 cm de altura e alturas de chão (andares, escadas, porão). */
    private class WG(val x0: Float, val z0: Float, val nx: Int, val nz: Int, val wall: IntArray, val off: IntArray, val fl: ShortArray, val dy: Float = 0f)
    @Volatile private var walk: List<WG> = emptyList()
    private const val WCS = 0.25f
    /** altura dos pés do jogador (a Renderer3D atualiza a cada quadro) */
    @Volatile var refY = 0f

    private fun wgAt(x: Float, z: Float): WG? {
        for (g in walk) if (x >= g.x0 && z >= g.z0 && x < g.x0 + g.nx * WCS && z < g.z0 + g.nz * WCS) return g
        return null
    }

    /** Chão sob (x, z) para quem está com os pés em [ref]: o mais alto que dê para subir (degrau até 55 cm); NaN se não há piso de casa ali. */
    fun surface(x: Float, z: Float, ref: Float): Float {
        val g = wgAt(x, z) ?: return Float.NaN
        val i = ((x - g.x0) / WCS).toInt(); val j = ((z - g.z0) / WCS).toInt()
        val c = j * g.nx + i
        var best = Float.NaN
        for (k in g.off[c] until g.off[c + 1]) {
            val h = g.fl[k] / 100f + g.dy   // Etapa 178: a casa pode estar num platô do relevo
            if (h <= ref + 0.55f && (best.isNaN() || h > best)) best = h
        }
        return best
    }

    /** -1: fora das casas ou no térreo (vale a colisão antiga); 0/1: andar de cima/escada/porão, livre/bloqueado pelas paredes daquele andar. */
    fun upper(x: Float, z: Float): Int {
        val g = wgAt(x, z) ?: return -1
        val ry = refY - g.dy   // altura dos pés em relação ao térreo desta casa
        if (ry < 1.2f && ry > -1.0f) return -1
        val lo = Math.floor(((ry + 0.25f + 3f) / 0.5f).toDouble()).toInt().coerceIn(0, 31)
        val hi = Math.floor(((ry + 1.8f + 3f) / 0.5f).toDouble()).toInt().coerceIn(0, 31)
        var mask = 0
        for (b in lo..hi) mask = mask or (1 shl b)
        for (k in 0 until 5) {
            val px = x + (if (k == 1) 0.15f else if (k == 2) -0.15f else 0f)
            val pz = z + (if (k == 3) 0.15f else if (k == 4) -0.15f else 0f)
            val i = Math.floor(((px - g.x0) / WCS).toDouble()).toInt(); val j = Math.floor(((pz - g.z0) / WCS).toDouble()).toInt()
            if (i < 0 || j < 0 || i >= g.nx || j >= g.nz) continue
            if (g.wall[j * g.nx + i] and mask != 0) return 1
        }
        return 0
    }

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
    @Volatile var offX = 0f; @Volatile var offZ = 0f
    /** Etapa 178: altura do térreo de cada casa no relevo (nível do platô + 8 cm, para a grama da casa não brigar com o terreno) */
    @Volatile private var plotY = FloatArray(0)
    private const val HOUSE_UP = 0.08f
    /** Etapa 178: altura dos pés ao nascer na Casa 1 */
    @Volatile var spY = 0f

    /** Etapa 174: ponto de partida do jogador dentro da Casa 1 (sala da esquerda, perto da porta); null enquanto a cidade não montou. */
    fun spawn(): FloatArray? = if (roofs.isEmpty()) null else floatArrayOf(spX, spZ)
    /** Etapa 174: retângulo (x0, z0, x1, z1) do lote k no mundo */
    fun plot(k: Int): FloatArray? = mplots.getOrNull(k)

    private const val CELL = 64f
    private const val PAD = 0.15f

    /** jogador dentro da caixa de alguma casa? (câmera usa plano próximo menor) */
    fun inside(x: Float, z: Float): Boolean { for (r in roofs) if (x > r.x0 && x < r.x1 && z > r.z0 && z < r.z1) return true; return false }

    /** Altura real de caminhada da Cidade 2: pisos internos, asfalto e calçadas. */
    fun groundH(x: Float, z: Float): Float {
        if (Relevo.on) {   // Etapa 178: cidade com relevo
            val py = plotY
            for (i in mplots.indices) {
                if (i >= py.size) break
                val p = mplots[i]
                if (x > p[0] + 0.05f && x < p[2] - 0.05f && z > p[1] + 0.05f && z < p[3] - 0.05f) return City.FLOOR + py[i]
                if (x > p[0] - 4f && x < p[2] + 4f && z > p[1] - 4f && z < p[3] + 4f) return py[i]   // quintal plano em volta da casa
            }
            return Relevo.groundH(x, z)
        }
        for (p in mplots) if (x > p[0] + 0.05f && x < p[2] - 0.05f && z > p[1] + 0.05f && z < p[3] - 0.05f) return City.FLOOR
        var dx = Float.MAX_VALUE
        for (v in mxr) dx = minOf(dx, kotlin.math.abs(x - v))
        var dz = Float.MAX_VALUE
        for (v in mzr) dz = minOf(dz, kotlin.math.abs(z - v))
        if (dx <= 5.25f || dz <= 5.25f) return 0.04f
        if (dx <= 8f || dz <= 8f) return 0.02f
        return 0f
    }

    fun clear() {
        jobs.clear()
        for (r in roofs) r.mesh?.release()
        roofs = emptyList()
        model = null
        if (texIds.any { it != 0 }) { try { GLES20.glDeleteTextures(texIds.size, texIds, 0) } catch (e: Throwable) { } }
        texIds = IntArray(0)
        mxr = FloatArray(0); mzr = FloatArray(0); mplots = emptyList()
        walk = emptyList(); refY = 0f
        plotY = FloatArray(0); spY = 0f
        Relevo.clear()
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
            val h0 = vh(a.v, (base + i0) * STRIDE)
            val h1 = vh(a.v, (base + i1) * STRIDE)
            val h2 = vh(a.v, (base + i2) * STRIDE)
            val lo = minOf(h0, h1, h2); val hi = maxOf(h0, h1, h2); val mid = h0 + h1 + h2 - lo - hi
            var h = lo xor java.lang.Long.rotateLeft(mid, 21) xor java.lang.Long.rotateLeft(hi, 42)
            h = (h xor (h ushr 30)) * -4658895280553007687L
            h = (h xor (h ushr 27)) * -7723592293110705685L
            h = h xor (h ushr 31)
            if (seen.add(h)) {
                a.idx[a.ni] = (i0 + base).toShort(); a.idx[a.ni + 1] = (i1 + base).toShort(); a.idx[a.ni + 2] = (i2 + base).toShort()
                a.ni += 3
            } else dropped++
            k += 3
        }
    }

    /**
     * Etapas 167/168: peças baixas que não são de casa (grama, faixas de grama de beira de rua, cruzamentos) tapavam porões, escadas e piscinas.
     * Recorta cada triângulo pelos buracos (retângulos): corta o polígono pelas 4 linhas do buraco e joga fora o miolo.
     * Tudo em coordenadas de mundo; atributos (normal, cor, UV) interpolados. Devolve false se a peça não toca nenhum buraco.
     */
    private val IDM = floatArrayOf(1f, 0f, 0f, 0f, 0f, 1f, 0f, 0f, 0f, 0f, 1f, 0f)

    private fun clipPoly(poly: List<FloatArray>, axis: Int, v: Float, keepLess: Boolean): List<FloatArray> {
        if (poly.isEmpty()) return poly
        val out = ArrayList<FloatArray>()
        for (i in poly.indices) {
            val a = poly[i]; val b = poly[(i + 1) % poly.size]
            val da = if (keepLess) v - a[axis] else a[axis] - v
            val db = if (keepLess) v - b[axis] else b[axis] - v
            if (da >= 0f) out.add(a)
            if ((da >= 0f) != (db >= 0f)) {
                val t = da / (da - db)
                out.add(FloatArray(STRIDE) { a[it] + (b[it] - a[it]) * t })
            }
        }
        return if (out.size >= 3) out else emptyList()
    }

    private fun addClipped(g: Group, p: GPrim, m: FloatArray, ox: Float, oz: Float, cg: CG?, holes: FloatArray): Boolean {
        // vértices em mundo
        val w = FloatArray(p.nv * STRIDE)
        var y0 = 1e9f; var y1 = -1e9f; var x0 = 1e9f; var x1 = -1e9f; var z0 = 1e9f; var z1 = -1e9f
        for (i in 0 until p.nv) {
            val o = i * STRIDE
            System.arraycopy(p.v, o, w, o, STRIDE)
            val x = p.v[o]; val y = p.v[o + 1]; val z = p.v[o + 2]
            val wx = m[0] * x + m[1] * y + m[2] * z + m[3] + ox
            val wy = m[4] * x + m[5] * y + m[6] * z + m[7]
            val wz = m[8] * x + m[9] * y + m[10] * z + m[11] + oz
            w[o] = wx; w[o + 1] = wy; w[o + 2] = wz
            val nx = p.v[o + 3]; val ny = p.v[o + 4]; val nz = p.v[o + 5]
            var tx = m[0] * nx + m[1] * ny + m[2] * nz; var ty = m[4] * nx + m[5] * ny + m[6] * nz; var tz = m[8] * nx + m[9] * ny + m[10] * nz
            val l = sqrt(tx * tx + ty * ty + tz * tz); if (l > 1e-6f) { tx /= l; ty /= l; tz /= l }
            w[o + 3] = tx; w[o + 4] = ty; w[o + 5] = tz
            if (wy < y0) y0 = wy; if (wy > y1) y1 = wy
            if (wx < x0) x0 = wx; if (wx > x1) x1 = wx
            if (wz < z0) z0 = wz; if (wz > z1) z1 = wz
        }
        if (y0 < -0.15f || y1 > 0.4f) return false   // só peças rente ao chão
        val mine = ArrayList<FloatArray>()
        var hi = 0
        while (hi + 3 < holes.size) {
            val h = floatArrayOf(holes[hi] + ox, holes[hi + 1] + oz, holes[hi + 2] + ox, holes[hi + 3] + oz); hi += 4
            if (h[0] < x1 && h[2] > x0 && h[1] < z1 && h[3] > z0) mine.add(h)
        }
        if (mine.isEmpty()) return false
        val ov = ArrayList<FloatArray>(); val oi = ArrayList<Int>()
        fun emit(poly: List<FloatArray>) {
            val b = ov.size
            for (q in poly) ov.add(q)
            for (k in 1 until poly.size - 1) { oi.add(b); oi.add(b + k); oi.add(b + k + 1) }
        }
        var k = 0
        while (k + 2 < p.idx.size) {
            val ta = FloatArray(STRIDE); val tb = FloatArray(STRIDE); val tc = FloatArray(STRIDE)
            System.arraycopy(w, (p.idx[k].toInt() and 0xFFFF) * STRIDE, ta, 0, STRIDE)
            System.arraycopy(w, (p.idx[k + 1].toInt() and 0xFFFF) * STRIDE, tb, 0, STRIDE)
            System.arraycopy(w, (p.idx[k + 2].toInt() and 0xFFFF) * STRIDE, tc, 0, STRIDE)
            var polys: List<List<FloatArray>> = listOf(listOf(ta, tb, tc))
            for (h in mine) {
                val nxt = ArrayList<List<FloatArray>>()
                for (pl in polys) {
                    var bx0 = 1e9f; var bx1 = -1e9f; var bz0 = 1e9f; var bz1 = -1e9f
                    for (q in pl) { if (q[0] < bx0) bx0 = q[0]; if (q[0] > bx1) bx1 = q[0]; if (q[2] < bz0) bz0 = q[2]; if (q[2] > bz1) bz1 = q[2] }
                    if (!(h[0] < bx1 && h[2] > bx0 && h[1] < bz1 && h[3] > bz0)) { nxt.add(pl); continue }
                    val a = clipPoly(pl, 0, h[0], true)
                    val rest = clipPoly(pl, 0, h[0], false)
                    val b = clipPoly(rest, 0, h[2], false)
                    val mid = clipPoly(rest, 0, h[2], true)
                    val c = clipPoly(mid, 2, h[1], true)
                    val d = clipPoly(mid, 2, h[3], false)
                    for (q in listOf(a, b, c, d)) if (q.size >= 3) nxt.add(q)
                }
                polys = nxt
            }
            for (pl in polys) emit(pl)
            k += 3
        }
        if (ov.isEmpty()) return true
        if (ov.size > 60000) return false
        val v = FloatArray(ov.size * STRIDE)
        for (i in ov.indices) System.arraycopy(ov[i], 0, v, i * STRIDE, STRIDE)
        val idx = ShortArray(oi.size) { oi[it].toShort() }
        addPrim(g, GPrim(p.mat, p.cut, p.emit, p.img, v, ov.size, idx), IDM, 0f, 0f, cg)
        return true
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
    /** Etapa 177: a cidade foi ampliada. Ruas/quarteirões originais (160 m) são repetidos em ncx x ncz quarteirões e cada casa fica no seu próprio quarteirão, bem longe das outras. */
    private class Dst(val cx: Int, val cz: Int, val sx: Int, val sz: Int, val plot: Int)
    @Volatile var spX = 0f; @Volatile var spZ = 0f

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
        val rel = Relevo.load(am, (City.C3 && !City.C4) || City.C5, City.C4, City.C5)   // Etapa 178: relevo.bin + city3.json (Etapa 185: ou sub.bin + sub.json da Cidade 3); sem eles vale a Cidade 2 antiga
        val ox = if (rel) 0f else (City.lotX0 + City.lotX1) / 2f - res.getDouble(0).toFloat()
        val oz = if (rel) 0f else (City.lotZ0 + City.lotZ1) / 2f - res.getDouble(1).toFloat()
        offX = ox; offZ = oz
        val plots = js.getJSONArray("plots"); val np0 = plots.length()
        val np = if (rel && Relevo.sub) minOf(1, np0) else np0   // Etapa 185: na Cidade 3 só existe a Casa 1; o resto do bairro é malha assada
        val ha = js.optJSONArray("holes"); val holes = FloatArray(ha?.length() ?: 0) { ha!!.getDouble(it).toFloat() }
        val ncx = js.getInt("ncx"); val ncz = js.getInt("ncz")
        val bcell = js.getJSONArray("bcell"); val spA = js.getJSONArray("sp"); val hpA = js.getJSONArray("hp"); val wpA = js.getJSONArray("wp")
        val CW = 160f
        val wx = CW * ncx - 20f; val wz = CW * ncz - 20f   // borda direita / de baixo dos últimos quarteirões

        // quarteirões de destino: um por casa (com o contexto de onde ela nasceu) + os vazios (praças com árvores)
        val dst = ArrayList<Dst>()
        val pdx = FloatArray(np0); val pdz = FloatArray(np0)
        val py = FloatArray(np0)
        if (rel) {
            // Etapa 178: cada casa vai para a posição dela no mapa novo e sobe/desce para o platô do terreno
            for (k in 0 until np) {
                val hs = Relevo.house(k) ?: continue
                val pb = plots.getJSONObject(k)
                val cxs = (pb.getDouble("x0") + pb.getDouble("x1")).toFloat() / 2f
                val czs = (pb.getDouble("z0") + pb.getDouble("z1")).toFloat() / 2f
                pdx[k] = Relevo.CX + hs.x - cxs; pdz[k] = Relevo.CZ + hs.z - czs
                py[k] = hs.lvl + HOUSE_UP
            }
        } else {
            val host = js.getJSONArray("host")
            for (k in 0 until np) {
                val h = host.getJSONArray(k)
                dst.add(Dst(h.getInt(0), h.getInt(1), h.getInt(2), h.getInt(3), k))
                pdx[k] = (h.getInt(0) - h.getInt(2)) * CW; pdz[k] = (h.getInt(1) - h.getInt(3)) * CW
            }
            val fa = js.getJSONArray("fill")
            for (k in 0 until fa.length()) { val h = fa.getJSONArray(k); dst.add(Dst(h.getInt(0), h.getInt(1), h.getInt(2), h.getInt(3), -1)) }
        }

        val clamp = BooleanArray(gm.images.size)
        for (n in gm.nodes) for (p in n.prims) if (p.cut && p.img in clamp.indices) clamp[p.img] = true

        val roofG = Array(np) { Group() }
        val cells = HashMap<Long, CG>()
        val inst = js.getJSONArray("inst")
        val m = FloatArray(12)

        fun addInst(a: org.json.JSONArray, j: Int, dx: Float, dz: Float, hl: FloatArray, mm: FloatArray?, dy: Float = 0f) {
            val pi = a.getInt(0)
            if (mm == null) for (k in 0 until 12) m[k] = a.getDouble(1 + k).toFloat() else for (k in 0 until 12) m[k] = mm[k]
            m[7] += dy   // Etapa 178: altura do platô
            val kind = a.getInt(13); val plot = a.getInt(14)
            val node = gm.nodes.getOrNull(pi) ?: return
            if (node.prims.isEmpty()) return
            val ox2 = ox + dx; val oz2 = oz + dz
            if (kind == 2 && plot in 0 until np) {
                for (p in node.prims) addPrim(roofG[plot], p, m, ox2, oz2, null)
            } else {
                val cx = Math.floor(((m[3] + ox2) / CELL).toDouble()).toInt(); val cz = Math.floor(((m[11] + oz2) / CELL).toDouble()).toInt()
                val key = (cx + 4096).toLong() * 65536L + (cz + 4096).toLong()
                val cg = cells.getOrPut(key) { CG() }
                for (p in node.prims) {
                    // Etapas 167/168: grama e faixas rente ao chão ganham buracos sobre porões, escadas e piscinas
                    if (kind == 0 && plot < 0 && hl.isNotEmpty() && addClipped(cg.g, p, m, ox2, oz2, cg, hl)) continue
                    addPrim(cg.g, p, m, ox2, oz2, cg)
                }
            }
        }

        if (rel) {
            for (k in 0 until np) {
                if (!Relevo.has(k)) continue   // Etapa 187: casa que não foi colocada no mapa
                for (j in 0 until inst.length()) {
                    if (bcell.getInt(j) != -1) continue
                    val a = inst.getJSONArray(j)
                    if (a.getInt(14) != k) continue
                    addInst(a, j, pdx[k], pdz[k], FloatArray(0), null, py[k])
                }
                City.step(0.5f + 0.05f * (k + 1) / np)
            }
        }
        for ((di, d) in dst.withIndex()) {
            val dx = (d.cx - d.sx) * CW; val dz = (d.cz - d.sz) * CW
            val src = d.sx + d.sz * 8
            val hl = if (d.plot >= 0) {
                val l = ArrayList<Float>()
                for (q in 0 until hpA.length()) if (hpA.getInt(q) == d.plot) for (c in 0 until 4) l.add(holes[q * 4 + c])
                l.toFloatArray()
            } else FloatArray(0)
            for (j in 0 until inst.length()) {
                val bc = bcell.getInt(j)
                val a = inst.getJSONArray(j)
                val ok = if (bc == -1) a.getInt(14) == d.plot else bc == src
                if (ok) addInst(a, j, dx, dz, hl, null)
            }
            City.step(0.5f + 0.4f * di / dst.size)
        }
        // anéis de grama em volta da cidade, esticados para o novo tamanho (o relevo tem o terreno dele)
        if (!rel) for (j in 0 until inst.length()) {
            val bc = bcell.getInt(j)
            if (bc > -3) continue
            val sxs = (wx + 540f) / 1200f; val szs = (wz + 20f) / 360f
            val mm = when (bc) {
                -3 -> floatArrayOf(sxs, 0f, 0f, -280f + 280f * sxs, 0f, 1f, 0f, 0f, 0f, 0f, 1f, 0f)
                -4 -> floatArrayOf(sxs, 0f, 0f, -280f + 280f * sxs, 0f, 1f, 0f, 0f, 0f, 0f, 1f, wz - 340f)
                -5 -> floatArrayOf(1f, 0f, 0f, 0f, 0f, 1f, 0f, 0f, 0f, 0f, szs, -20f + 20f * szs)
                else -> floatArrayOf(1f, 0f, 0f, wx - 660f, 0f, 1f, 0f, 0f, 0f, 0f, szs, -20f + 20f * szs)
            }
            addInst(inst.getJSONArray(j), j, 0f, 0f, FloatArray(0), mm)
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
            if (rel && !Relevo.has(k)) {   // Etapa 187: retângulo vazio, longe do mapa, para manter os índices
                pl.add(floatArrayOf(-1e5f, -1e5f, -1e5f, -1e5f)); rl.add(Roof(-1e5f, -1e5f, -1e5f, -1e5f)); continue
            }
            val b = plots.getJSONObject(k)
            val x0 = b.getDouble("x0").toFloat() + ox + pdx[k]; val z0 = b.getDouble("z0").toFloat() + oz + pdz[k]
            val x1 = b.getDouble("x1").toFloat() + ox + pdx[k]; val z1 = b.getDouble("z1").toFloat() + oz + pdz[k]
            pl.add(floatArrayOf(x0, z0, x1, z1))
            val r = Roof(x0 - 0.3f, z0 - 0.3f, x1 + 0.3f, z1 + 0.3f)
            rl.add(r)
            if (roofG[k].all.isNotEmpty()) jobs.add(Job(null, r, roofG[k].all))
            City.addPlace(City.Place(HdsEstate.label(k), (x0 + x1) / 2f, (z0 + z1) / 2f, 0xFFFF7043.toInt(), 'C'))
        }
        spX = 47.84f + ox + pdx[0]; spZ = 19.9f + oz + pdz[0]; spY = py[0] + City.FLOOR
        if (rel) Relevo.build(out, pl)   // Etapa 178: terreno, água, ruas curvas, rotatórias, pontes e árvores

        // colisões (paredes e cercas, já com os vãos de porta); as das casas vão com a casa, as de árvores/ruas repetem em cada quarteirão
        val so = js.getJSONArray("solids")
        var i = 0
        while (i + 3 < so.length()) {
            val v = spA.getInt(i / 4)
            val sx0 = so.getDouble(i).toFloat(); val sz0 = so.getDouble(i + 1).toFloat(); val sx1 = so.getDouble(i + 2).toFloat(); val sz1 = so.getDouble(i + 3).toFloat()
            if (rel && v >= 0 && !Relevo.has(v)) { i += 4; continue }   // Etapas 185/187: casas que não existem neste mapa
            if (v >= 0) {
                City.addSolid(floatArrayOf(sx0 + ox + pdx[v] - PAD, sz0 + oz + pdz[v] - PAD, sx1 + ox + pdx[v] + PAD, sz1 + oz + pdz[v] + PAD))
            } else if (v != -99) {
                val c = -1 - v
                for (d in dst) if (d.sx + d.sz * 8 == c) {
                    val dx = (d.cx - d.sx) * CW; val dz = (d.cz - d.sz) * CW
                    City.addSolid(floatArrayOf(sx0 + ox + dx - PAD, sz0 + oz + dz - PAD, sx1 + ox + dx + PAD, sz1 + oz + dz + PAD))
                }
            }
            i += 4
        }

        if (rel && Relevo.sub) for (r in Relevo.subSolids()) City.addSolid(r)   // Etapa 185: casas, cercas, postes e carros do bairro

        // Etapa 166: chão e paredes por andar (escadas, andar de cima, porão)
        try {
            val bb = java.nio.ByteBuffer.wrap(am.open("hds/city2walk.bin").use { it.readBytes() }).order(ByteOrder.LITTLE_ENDIAN)
            val ng = bb.getInt(); bb.getFloat()
            val wl = ArrayList<WG>()
            for (gk in 0 until ng) {
                val pk = wpA.getInt(gk)
                val gx = bb.getFloat() + ox + pdx[pk]; val gz = bb.getFloat() + oz + pdz[pk]; val nx = bb.getInt(); val nz = bb.getInt()
                val wall = IntArray(nx * nz) { bb.getInt() }
                val off = IntArray(nx * nz + 1)
                var fl = ShortArray(nx * nz * 2)
                var n = 0
                for (c in 0 until nx * nz) {
                    val cnt = bb.get().toInt() and 0xFF
                    off[c] = n
                    if (n + cnt > fl.size) fl = fl.copyOf(maxOf(fl.size * 2, n + cnt))
                    for (q in 0 until cnt) fl[n++] = bb.getShort()
                }
                off[nx * nz] = n
                if ((!rel || Relevo.has(pk)) && pk < np) wl.add(WG(gx, gz, nx, nz, wall, off, fl.copyOf(n), py[pk]))   // Etapa 185: Cidade 3 só tem a Casa 1
            }
            walk = wl
        } catch (e: Throwable) { android.util.Log.w("Hds", "city2walk.bin: $e") }

        if (rel) {
            minX = Relevo.CX; minZ = Relevo.CZ
            maxX = Relevo.CX + Relevo.worldW; maxZ = Relevo.CZ + Relevo.worldH
            mxr = FloatArray(0); mzr = FloatArray(0)
        } else {
            minX = ox - 20f - 250f; minZ = oz - 20f - 250f
            maxX = ox + wx + 250f; maxZ = oz + wz + 250f
            mxr = FloatArray(ncx) { ox + CW * it }
            mzr = FloatArray(ncz) { oz + CW * it }
        }
        plotY = py
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
        if (Relevo.on) {   // Etapa 178: mapa do relevo + os lotes das casas
            Relevo.drawMap(c)
            fill.color = 0xFFBCAAA4.toInt()
            for (p in mplots) c.drawRect(p[0] - 3f, p[1] - 3f, p[2] + 3f, p[3] + 3f, fill)
            return
        }
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
