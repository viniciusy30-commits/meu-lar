package com.vinicius.meular

import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

/**
 * Etapa 127: sombras projetadas pelo sol (que é fixo) — calculadas uma vez na montagem da cidade.
 * Cada prédio/árvore/poste projeta no chão o "fecho convexo" da base + base deslocada na direção oposta ao sol.
 * O polígono é recortado nas faixas de asfalto (desenhado rente ao asfalto) e no resto (rente à calçada/grama),
 * para nunca flutuar nem afundar. Tudo vai numa malha só, desenhada num passe com mistura (uma chamada).
 * Sombras sobrepostas não escurecem em dobro: ficam no mesmo plano e o teste de profundidade descarta a segunda.
 */
object Shade {
    private val LX = -Sky.SUN[0] / Sky.SUN[1]
    private val LZ = -Sky.SUN[2] / Sky.SUN[1]
    private const val Y_ROAD = 0.025f
    private const val Y_HIGH = City.CURB + 0.045f

    /** Construtor da malha das sombras (só na montagem principal; thread da montagem). */
    @Volatile var b = MB()

    /** Só a montagem principal da cidade grava sombras (o detalhe carregado depois não repete). */
    @Volatile var on = false

    @Synchronized fun reset() { b = MB().also { it.warp = City.TOWN; it.warpElev = true }; on = true; probes.clear() }

    // ---------------------------------------------------------------- geometria 2D
    private fun cross(o: FloatArray, a: FloatArray, c: FloatArray) = (a[0] - o[0]) * (c[1] - o[1]) - (a[1] - o[1]) * (c[0] - o[0])

    private fun hull(p: List<FloatArray>): List<FloatArray> {
        if (p.size < 3) return p
        val s = p.sortedWith(compareBy({ it[0] }, { it[1] }))
        val lo = ArrayList<FloatArray>(); val up = ArrayList<FloatArray>()
        for (q in s) { while (lo.size >= 2 && cross(lo[lo.size - 2], lo[lo.size - 1], q) <= 0f) lo.removeAt(lo.size - 1); lo.add(q) }
        for (q in s.asReversed()) { while (up.size >= 2 && cross(up[up.size - 2], up[up.size - 1], q) <= 0f) up.removeAt(up.size - 1); up.add(q) }
        lo.removeAt(lo.size - 1); up.removeAt(up.size - 1)
        return lo + up
    }

    /** Recorta um polígono convexo num retângulo (Sutherland–Hodgman). */
    private fun clip(poly: List<FloatArray>, x0: Float, z0: Float, x1: Float, z1: Float): List<FloatArray> {
        var out = poly
        for (e in 0 until 4) {
            if (out.isEmpty()) return out
            val inp = out; out = ArrayList()
            fun inside(q: FloatArray) = when (e) { 0 -> q[0] >= x0; 1 -> q[0] <= x1; 2 -> q[1] >= z0; else -> q[1] <= z1 }
            fun cut(a: FloatArray, c: FloatArray): FloatArray {
                val t = when (e) { 0 -> (x0 - a[0]) / (c[0] - a[0]); 1 -> (x1 - a[0]) / (c[0] - a[0]); 2 -> (z0 - a[1]) / (c[1] - a[1]); else -> (z1 - a[1]) / (c[1] - a[1]) }
                return floatArrayOf(a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t)
            }
            for (i in inp.indices) {
                val cur = inp[i]; val prev = inp[(i + inp.size - 1) % inp.size]
                val ci = inside(cur); val pi = inside(prev)
                if (ci) { if (!pi) out.add(cut(prev, cur)); out.add(cur) } else if (pi) out.add(cut(prev, cur))
            }
        }
        return out
    }

    private fun emit(poly: List<FloatArray>, y: Float, alpha: Float) {
        if (poly.size < 3) return
        val m = b
        synchronized(m) {
            m.m(Mt.GLASS); m.al = alpha
            val c = C("#0E1622")
            for (i in 1 until poly.size - 1) { m.raw(poly[0][0], y, poly[0][1], c); m.raw(poly[i][0], y, poly[i][1], c); m.raw(poly[i + 1][0], y, poly[i + 1][1], c) }
            m.al = 1f
        }
    }

    /** Distribui o polígono pelo chão da cidade: asfalto (baixo) e calçadas/quarteirões (alto). Fora da cidade (praia): [yAt]. */
    private fun cast(pts: List<FloatArray>, alpha: Float, yAt: Float = Float.NaN) {
        if (!on) return
        val h = hull(pts)
        if (h.size < 3) return
        if (!yAt.isNaN()) { emit(h, yAt, alpha); return }
        if (City.TOWN) {   // Etapa 131: cidade nova — altura do chão no meio da sombra
            var cx = 0f; var cz = 0f; for (q in h) { cx += q[0]; cz += q[1] }
            emit(h, if (Town.groundFlat(cx / h.size, cz / h.size) > 0.05f) Y_HIGH else Y_ROAD, alpha); return
        }
        val bx = City.bandX; val bz = City.bandZ
        val S = City.SIDE
        val nX = bx.size / 2; val nZ = bz.size / 2
        // faixas de asfalto (ruas ao longo de x e ao longo de z)
        for (k in 0 until nZ) emit(clip(h, City.X0 - 60f, bz[k * 2] + S, City.X1 + 60f, bz[k * 2 + 1] - S), Y_ROAD, alpha)
        for (k in 0 until nX) emit(clip(h, bx[k * 2] + S, City.Z0 - 60f, bx[k * 2 + 1] - S, City.Z1), Y_ROAD, alpha)
        // o resto: retângulos entre as faixas de asfalto (calçadas + quarteirões)
        for (i in 0..nX) {
            val xa = if (i == 0) City.X0 - 60f else bx[i * 2 - 1] - S
            val xb = if (i == nX) City.X1 + 60f else bx[i * 2] + S
            if (xb <= xa) continue
            for (j in 0..nZ) {
                val za = if (j == 0) City.Z0 - 60f else bz[j * 2 - 1] - S
                val zb = if (j == nZ) City.Z1 else bz[j * 2] + S
                if (zb <= za) continue
                if (City.inLot((xa + xb) / 2, (za + zb) / 2) && zb - za < 200f) continue   // o quintal do jogador tem chão próprio
                emit(clip(h, xa, za, xb, zb), Y_HIGH, alpha)
            }
        }
    }

    /** Caixa (prédio, casa, muro) de altura [h]. */
    @Synchronized fun box(x0: Float, z0: Float, x1: Float, z1: Float, h: Float, alpha: Float = 0.34f) {
        val dx = LX * h; val dz = LZ * h
        val p = ArrayList<FloatArray>(8)
        for (q in arrayOf(floatArrayOf(x0, z0), floatArrayOf(x1, z0), floatArrayOf(x1, z1), floatArrayOf(x0, z1))) { p.add(q); p.add(floatArrayOf(q[0] + dx, q[1] + dz)) }
        cast(p, alpha)
    }

    /** Árvore: tronco (do pé à copa) + elipse da copa projetada. [y] = chão. */
    /** pontos de árvores/postes registrados (para conferir sobreposição no simulador) */
    val probes = ArrayList<FloatArray>()

    @Synchronized fun tree(x: Float, z: Float, cx: Float, cz: Float, cy: Float, r: Float, ry: Float, y: Float, alpha: Float = 0.27f) {
        if (on && probes.size < 6000) probes.add(floatArrayOf(x, z, 0f))
        val hc = cy - y
        val ox = cx + LX * hc; val oz = cz + LZ * hc
        val p = ArrayList<FloatArray>(14)
        // copa: círculo esticado na direção da luz (a projeção de uma esfera achatada)
        val n = 12
        for (k in 0 until n) {
            val a = k * 6.2832f / n
            val ex = cos(a) * r; val ez = sin(a) * r
            p.add(floatArrayOf(ox + ex + LX * ry * sin(a) * 0.5f, oz + ez + LZ * ry * sin(a) * 0.5f))
        }
        val crown = hull(p)
        val yy = if (y > City.CURB + 0.2f || y < -0.1f) y + 0.04f else Float.NaN
        cast(crown, alpha, yy)
        // tronco: faixa fina do pé até a copa
        val tw = 0.14f
        val trunk = listOf(floatArrayOf(x - tw, z), floatArrayOf(x + tw, z), floatArrayOf(x + LX * hc * 0.85f + tw, z + LZ * hc * 0.85f), floatArrayOf(x + LX * hc * 0.85f - tw, z + LZ * hc * 0.85f))
        cast(trunk, alpha * 0.9f, yy)
    }

    /** Poste fino (luminária, semáforo, placa). */
    @Synchronized fun pole(x: Float, z: Float, h: Float, w: Float = 0.12f, alpha: Float = 0.24f) {
        if (on && probes.size < 6000) probes.add(floatArrayOf(x, z, 1f))
        val ex = x + LX * h; val ez = z + LZ * h
        val nx = -LZ; val nz = LX
        val l = max(0.001f, kotlin.math.sqrt(nx * nx + nz * nz))
        val px = nx / l * w; val pz = nz / l * w
        cast(listOf(floatArrayOf(x - px, z - pz), floatArrayOf(x + px, z + pz), floatArrayOf(ex + px, ez + pz), floatArrayOf(ex - px, ez - pz)), alpha)
    }

    /** Sombra de algo sobre um chão de altura conhecida (praia, píer). */
    @Synchronized fun boxAt(x0: Float, z0: Float, x1: Float, z1: Float, h: Float, y: Float, alpha: Float = 0.3f) {
        val dx = LX * h; val dz = LZ * h
        val p = ArrayList<FloatArray>(8)
        for (q in arrayOf(floatArrayOf(x0, z0), floatArrayOf(x1, z0), floatArrayOf(x1, z1), floatArrayOf(x0, z1))) { p.add(q); p.add(floatArrayOf(q[0] + dx, q[1] + dz)) }
        cast(p, alpha, y + 0.04f)
    }

    @Volatile var mesh: Mesh? = null

    @Synchronized fun finish() {
        on = false
        val m = b
        mesh = if (m.isEmpty()) null else m.toMesh(true)
        b = MB().also { it.warp = City.TOWN; it.warpElev = true }
    }
}
