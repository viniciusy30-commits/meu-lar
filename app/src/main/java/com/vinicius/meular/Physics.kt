package com.vinicius.meular

import java.util.Locale
import kotlin.math.abs
import kotlin.math.ceil
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

// Etapa 83: física de corpos rígidos para objetos soltos (caixa, bola...). Pequena e própria (sem biblioteca):
//  - gravidade, massa, atrito, quique (restituição), amortecimento e resistência ao rolamento;
//  - contato por impulsos (cantos da caixa / esfera) contra o piso, as paredes, os colisores dos móveis
//    (COL_* dos GLB, ou a caixa do móvel antigo), outros corpos e o personagem (cilindro que empurra e chuta);
//  - quinas dos móveis entram na conta (a caixa tomba ao passar da borda da mesa);
//  - passos fixos de 1/120 s e "sono" quando o corpo para (nada treme parado e não gasta processamento).
// Móveis grandes NÃO entram aqui: são estáticos (Plano Mestre: "nunca deixar um armário tombar").

/** Caixa estática alinhada aos eixos (mundo). */
class SBox(@JvmField val x0: Float, @JvmField val y0: Float, @JvmField val z0: Float,
           @JvmField val x1: Float, @JvmField val y1: Float, @JvmField val z1: Float)

class Body(
    val item: Item,
    val sphere: Boolean,
    val hx: Float, val hy: Float, val hz: Float,
    /** altura do centro de massa acima da origem do modelo (origem = piso do objeto) */
    val comY: Float,
    mass: Float,
    val mu: Float,
    val e: Float,
    val lin: Float,
    val ang: Float,
    val roll: Float
) {
    val p = FloatArray(3)
    val v = FloatArray(3)
    val q = floatArrayOf(0f, 0f, 0f, 1f)
    val w = FloatArray(3)
    val invM = 1f / mass
    private val ib = FloatArray(3)
    /** rotação (linhas) atual */
    val r = FloatArray(9)
    var sleep = false
    var still = 0f
    var supT = 0f
    var supportY = 0f
    var lastX = Float.NaN
    var lastZ = Float.NaN
    var kinematic = false

    init {
        if (sphere) {
            val i = 2f / 3f * mass * hx * hx         // esfera oca (bola de borracha)
            ib[0] = 1f / i; ib[1] = 1f / i; ib[2] = 1f / i
        } else {
            ib[0] = 3f / (mass * (hy * hy + hz * hz))
            ib[1] = 3f / (mass * (hx * hx + hz * hz))
            ib[2] = 3f / (mass * (hx * hx + hy * hy))
        }
        updR()
    }

    fun updR() {
        val x = q[0]; val y = q[1]; val z = q[2]; val ww = q[3]
        r[0] = 1 - 2 * (y * y + z * z); r[1] = 2 * (x * y - z * ww); r[2] = 2 * (x * z + y * ww)
        r[3] = 2 * (x * y + z * ww); r[4] = 1 - 2 * (x * x + z * z); r[5] = 2 * (y * z - x * ww)
        r[6] = 2 * (x * z - y * ww); r[7] = 2 * (y * z + x * ww); r[8] = 1 - 2 * (x * x + y * y)
    }

    /** out = I⁻¹(mundo) · a */
    fun iw(ax: Float, ay: Float, az: Float, out: FloatArray) {
        // local = Rᵀ a
        val lx = r[0] * ax + r[3] * ay + r[6] * az
        val ly = r[1] * ax + r[4] * ay + r[7] * az
        val lz = r[2] * ax + r[5] * ay + r[8] * az
        val bx = lx * ib[0]; val by = ly * ib[1]; val bz = lz * ib[2]
        out[0] = r[0] * bx + r[1] * by + r[2] * bz
        out[1] = r[3] * bx + r[4] * by + r[5] * bz
        out[2] = r[6] * bx + r[7] * by + r[8] * bz
    }

    fun setYaw(deg: Float) {
        val a = Math.toRadians(deg.toDouble()) / 2
        q[0] = 0f; q[1] = Math.sin(a).toFloat(); q[2] = 0f; q[3] = Math.cos(a).toFloat(); updR()
    }

    /** extensão (meia largura) do corpo ao longo da direção unitária (dx, dy, dz) */
    fun extent(dx: Float, dy: Float, dz: Float): Float {
        if (sphere) return hx
        return abs(r[0] * dx + r[3] * dy + r[6] * dz) * hx + abs(r[1] * dx + r[4] * dy + r[7] * dz) * hy + abs(r[2] * dx + r[5] * dy + r[8] * dz) * hz
    }

    fun encode(): String = String.format(Locale.US, "px=%.4f~py=%.4f~pz=%.4f~q=%.5f:%.5f:%.5f:%.5f", p[0], p[1], p[2], q[0], q[1], q[2], q[3])
}

object Physics {
    val bodies = ArrayList<Body>()
    private const val H = 1f / 120f
    private const val SLOP = 0.002f
    /** um corpo dormiu (posição estável): vale a pena gravar */
    @Volatile var settled = false

    // contatos do passo atual
    private var nc = 0
    private val cb = arrayOfNulls<Body>(256)        // corpo A
    private val co = arrayOfNulls<Body>(256)        // corpo B (null = mundo/personagem)
    private val cp = FloatArray(256 * 3)
    private val cn = FloatArray(256 * 3)
    private val cd = FloatArray(256)
    private val cv = FloatArray(256 * 3)            // velocidade do outro lado (personagem); mundo = 0
    private val tmp = FloatArray(3)
    private val tmp2 = FloatArray(3)
    // solver com impulsos acumulados (por contato): normal, 2 tangentes, rigidez efetiva e velocidade-alvo de quique
    private val pn = FloatArray(256)
    private val pt1 = FloatArray(256)
    private val pt2 = FloatArray(256)
    private val t1 = FloatArray(256 * 3)
    private val t2 = FloatArray(256 * 3)
    private val kn = FloatArray(256)
    private val k1 = FloatArray(256)
    private val k2 = FloatArray(256)
    private val bias = FloatArray(256)

    /** Mundo visto pela física. */
    class World(
        val statics: List<SBox>,
        val gw: Float, val gh: Float,
        val doorOpen: Boolean,
        val ground: (Float, Float) -> Float,
        val px: Float, val pz: Float, val pvx: Float, val pvz: Float, val pRun: Boolean, val pOn: Boolean
    )

    /** Cria/remove corpos para os itens dinâmicos. [make] cria o corpo de um item novo. */
    fun sync(items: List<Item>, make: (Item) -> Body?) {
        val it = bodies.iterator()
        while (it.hasNext()) { val b = it.next(); if (!items.contains(b.item)) { b.item.body = null; it.remove() } }
        for (o in items) if (o.type.dyn && o.body == null) make(o)?.let { o.body = it; bodies.add(it) }
    }

    fun clear() { for (b in bodies) b.item.body = null; bodies.clear() }

    fun step(dt: Float, wd: World) {
        if (bodies.isEmpty()) return
        val n = min(6, max(1, ceil(dt / H).toInt()))
        for (s in 0 until n) sub(H, wd)
    }

    private fun addC(a: Body, b: Body?, px: Float, py: Float, pz: Float, nx: Float, ny: Float, nz: Float, d: Float, vx: Float = 0f, vy: Float = 0f, vz: Float = 0f) {
        if (nc >= 256) return
        cb[nc] = a; co[nc] = b
        cp[nc * 3] = px; cp[nc * 3 + 1] = py; cp[nc * 3 + 2] = pz
        cn[nc * 3] = nx; cn[nc * 3 + 1] = ny; cn[nc * 3 + 2] = nz
        cd[nc] = d; cv[nc * 3] = vx; cv[nc * 3 + 1] = vy; cv[nc * 3 + 2] = vz
        nc++
    }

    private fun sub(h: Float, wd: World) {
        // 1. forças
        for (b in bodies) {
            if (b.sleep || b.kinematic) continue
            b.v[1] -= 9.81f * h
            val ld = 1f / (1f + b.lin * h); val ad = 1f / (1f + b.ang * h)
            for (k in 0..2) { b.v[k] *= ld; b.w[k] *= ad }
        }
        // 2. contatos
        nc = 0
        for (b in bodies) if (!b.kinematic) detect(b, wd)
        for (i in bodies.indices) for (j in i + 1 until bodies.size) pair(bodies[i], bodies[j])
        // dormindo sem nada encostando (o apoio sumiu, ex.: o móvel de baixo foi tirado): acorda e cai
        for (b in bodies) if (b.sleep) {
            var any = false
            for (c in 0 until nc) if (cb[c] === b || co[c] === b) { any = true; break }
            if (!any) { b.sleep = false; b.still = 0f }
        }
        // acorda quem foi tocado por algo acordado ou pelo personagem
        for (c in 0 until nc) {
            val a = cb[c]!!; val o = co[c]
            if (a.sleep && ((o != null && !o.sleep) || cv[c * 3] != 0f || cv[c * 3 + 2] != 0f)) a.sleep = false
            if (o != null && o.sleep && !a.sleep) o.sleep = false
        }
        // 3. impulsos acumulados (8 voltas) e correção de posição
        for (c in 0 until nc) prepare(c)
        for (it in 0 until 8) for (c in 0 until nc) solve(c)
        for (b in bodies) {
            if (b.sleep || b.kinematic) continue
            var sx = 0f; var sy = 0f; var sz = 0f; var k = 0
            for (c in 0 until nc) {
                val d = cd[c] - SLOP
                if (d <= 0f) continue
                if (cb[c] === b) { sx += cn[c * 3] * d; sy += cn[c * 3 + 1] * d; sz += cn[c * 3 + 2] * d; k++ }
                else if (co[c] === b) { sx -= cn[c * 3] * d * 0.5f; sy -= cn[c * 3 + 1] * d * 0.5f; sz -= cn[c * 3 + 2] * d * 0.5f; k++ }
            }
            if (k > 0) { val f = 0.8f / k; b.p[0] += sx * f; b.p[1] += sy * f; b.p[2] += sz * f }
        }
        // 4. integra e dorme
        for (b in bodies) {
            if (b.sleep || b.kinematic) continue
            if (b.sphere && b.roll > 0f) {
                // resistência ao rolamento (só quando encostado em algo)
                var touch = false
                for (c in 0 until nc) if (cb[c] === b && cn[c * 3 + 1] > 0.5f) { touch = true; break }
                if (touch) { val f = max(0f, 1f - b.roll * 9.81f * h / max(0.05f, sqrt(b.v[0] * b.v[0] + b.v[2] * b.v[2]))); b.v[0] *= f; b.v[2] *= f; b.w[0] *= f; b.w[2] *= f }
            }
            for (k in 0..2) b.p[k] += b.v[k] * h
            val wx = b.w[0]; val wy = b.w[1]; val wz = b.w[2]
            val q = b.q
            val dx = 0.5f * h * (wx * q[3] + wy * q[2] - wz * q[1])
            val dy = 0.5f * h * (wy * q[3] + wz * q[0] - wx * q[2])
            val dz = 0.5f * h * (wz * q[3] + wx * q[1] - wy * q[0])
            val dw = 0.5f * h * (-wx * q[0] - wy * q[1] - wz * q[2])
            q[0] += dx; q[1] += dy; q[2] += dz; q[3] += dw
            val ql = sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3])
            for (k in 0..3) q[k] /= ql
            b.updR()
            val e2 = b.v[0] * b.v[0] + b.v[1] * b.v[1] + b.v[2] * b.v[2]
            val a2 = b.w[0] * b.w[0] + b.w[1] * b.w[1] + b.w[2] * b.w[2]
            var supported = false
            for (c in 0 until nc) if ((cb[c] === b && cn[c * 3 + 1] > 0.6f) || (co[c] === b && cn[c * 3 + 1] < -0.6f)) { supported = true; break }
            if (supported) b.supT = 0.12f else b.supT -= h
            if (b.supT > 0f && e2 < 0.006f && a2 < 0.03f) {
                b.still += h
                if (b.still > 0.45f) { b.sleep = true; for (k in 0..2) { b.v[k] = 0f; b.w[k] = 0f }; settled = true }
            } else b.still = 0f
            if (b.p[1] < -2f) { b.p[1] = 1f; for (k in 0..2) { b.v[k] = 0f; b.w[k] = 0f } }   // segurança: caiu do mundo
        }
    }

    private fun detect(b: Body, wd: World) {
        val gx = b.p[0]; val gz = b.p[2]
        val inside = gx > 0f && gx < wd.gw && gz > 0f && gz < wd.gh
        val g = if (inside) 0f else wd.ground(gx, gz)
        b.supportY = g
        if (b.sphere) {
            val r = b.hx
            if (b.p[1] - r < g) addC(b, null, gx, g, gz, 0f, 1f, 0f, g - (b.p[1] - r))
            if (inside) {
                if (b.p[0] - r < 0f) addC(b, null, 0f, b.p[1], gz, 1f, 0f, 0f, r - b.p[0])
                if (b.p[0] + r > wd.gw) addC(b, null, wd.gw, b.p[1], gz, -1f, 0f, 0f, b.p[0] + r - wd.gw)
                if (b.p[2] - r < 0f) addC(b, null, gx, b.p[1], 0f, 0f, 0f, 1f, r - b.p[2])
                val door = wd.doorOpen && abs(gx - wd.gw / 2f) < 0.42f
                if (b.p[2] + r > wd.gh && !door) addC(b, null, gx, b.p[1], wd.gh, 0f, 0f, -1f, b.p[2] + r - wd.gh)
            }
            for (s in wd.statics) sphereBox(b, s)
        } else {
            for (i in 0 until 8) {
                corner(b, i, tmp)
                val x = tmp[0]; val y = tmp[1]; val z = tmp[2]
                if (y < g) addC(b, null, x, y, z, 0f, 1f, 0f, g - y)
                if (inside) {
                    if (x < 0f) addC(b, null, x, y, z, 1f, 0f, 0f, -x)
                    if (x > wd.gw) addC(b, null, x, y, z, -1f, 0f, 0f, x - wd.gw)
                    if (z < 0f) addC(b, null, x, y, z, 0f, 0f, 1f, -z)
                    val door = wd.doorOpen && abs(x - wd.gw / 2f) < 0.42f
                    if (z > wd.gh && !door) addC(b, null, x, y, z, 0f, 0f, -1f, z - wd.gh)
                }
                for (s in wd.statics) pointInStatic(b, s, x, y, z)
            }
            for (s in wd.statics) staticEdgesInBox(b, s)
        }
        if (!inside) {
            // a casa vista de fora: um bloco sólido (a porta é ignorada aqui)
            val s = SBox(-0.17f, 0f, -0.17f, wd.gw + 0.17f, 2.6f, wd.gh + 0.17f)
            if (b.sphere) sphereBox(b, s) else for (i in 0 until 8) { corner(b, i, tmp); pointInStatic(b, s, tmp[0], tmp[1], tmp[2]) }
        }
        if (wd.pOn) player(b, wd)
    }

    private val EDGE = arrayOf(
        floatArrayOf(0f, -1f, -1f), floatArrayOf(0f, 1f, -1f), floatArrayOf(0f, -1f, 1f), floatArrayOf(0f, 1f, 1f),
        floatArrayOf(-1f, 0f, -1f), floatArrayOf(1f, 0f, -1f), floatArrayOf(-1f, 0f, 1f), floatArrayOf(1f, 0f, 1f),
        floatArrayOf(-1f, -1f, 0f), floatArrayOf(1f, -1f, 0f), floatArrayOf(-1f, 1f, 0f), floatArrayOf(1f, 1f, 0f))

    /** pontos de teste da caixa: 0..7 cantos, 8..19 meios das arestas; recuados 1,5 mm para dentro */
    private fun boxPoint(b: Body, i: Int, out: FloatArray) {
        val sx: Float; val sy: Float; val sz: Float
        if (i < 8) { sx = if (i and 1 != 0) 1f else -1f; sy = if (i and 2 != 0) 1f else -1f; sz = if (i and 4 != 0) 1f else -1f }
        else { val e = EDGE[i - 8]; sx = e[0]; sy = e[1]; sz = e[2] }
        val lx = sx * (b.hx - 0.0015f); val ly = sy * (b.hy - 0.0015f); val lz = sz * (b.hz - 0.0015f)
        val r = b.r
        out[0] = b.p[0] + r[0] * lx + r[1] * ly + r[2] * lz
        out[1] = b.p[1] + r[3] * lx + r[4] * ly + r[5] * lz
        out[2] = b.p[2] + r[6] * lx + r[7] * ly + r[8] * lz
    }

    private fun corner(b: Body, i: Int, out: FloatArray) {
        val lx = if (i and 1 != 0) b.hx else -b.hx
        val ly = if (i and 2 != 0) b.hy else -b.hy
        val lz = if (i and 4 != 0) b.hz else -b.hz
        val r = b.r
        out[0] = b.p[0] + r[0] * lx + r[1] * ly + r[2] * lz
        out[1] = b.p[1] + r[3] * lx + r[4] * ly + r[5] * lz
        out[2] = b.p[2] + r[6] * lx + r[7] * ly + r[8] * lz
    }

    private fun pointInStatic(b: Body, s: SBox, x: Float, y: Float, z: Float) {
        if (x <= s.x0 || x >= s.x1 || y <= s.y0 || y >= s.y1 || z <= s.z0 || z >= s.z1) return
        val top = (s.y1 - y) * 0.7f           // prefere o tampo: quem chega por cima fica em cima
        val d0 = x - s.x0; val d1 = s.x1 - x; val d2 = y - s.y0; val d4 = z - s.z0; val d5 = s.z1 - z
        var m = top; var nx = 0f; var ny = 1f; var nz = 0f; var dd = s.y1 - y
        if (d0 < m) { m = d0; nx = -1f; ny = 0f; nz = 0f; dd = d0 }
        if (d1 < m) { m = d1; nx = 1f; ny = 0f; nz = 0f; dd = d1 }
        if (d2 < m) { m = d2; nx = 0f; ny = -1f; nz = 0f; dd = d2 }
        if (d4 < m) { m = d4; nx = 0f; ny = 0f; nz = -1f; dd = d4 }
        if (d5 < m) { m = d5; nx = 0f; ny = 0f; nz = 1f; dd = d5 }
        addC(b, null, x, y, z, nx, ny, nz, dd)
    }

    /** quinas e bordas de cima do móvel dentro da caixa (o corpo tomba sobre a borda). */
    private fun staticEdgesInBox(b: Body, s: SBox) {
        // descarta rápido: longe demais
        val rr = b.hx + b.hy + b.hz
        if (b.p[0] + rr < s.x0 || b.p[0] - rr > s.x1 || b.p[2] + rr < s.z0 || b.p[2] - rr > s.z1 || b.p[1] - rr > s.y1 || b.p[1] + rr < s.y0) return
        val y = s.y1
        edge(b, s.x0, y, s.z0, s.x1, y, s.z0)
        edge(b, s.x0, y, s.z1, s.x1, y, s.z1)
        edge(b, s.x0, y, s.z0, s.x0, y, s.z1)
        edge(b, s.x1, y, s.z0, s.x1, y, s.z1)
    }

    private fun edge(b: Body, ax: Float, ay: Float, az: Float, bx: Float, by: Float, bz: Float) {
        val len = sqrt((bx - ax) * (bx - ax) + (bz - az) * (bz - az))
        val n = max(1, (len / 0.05f).toInt())
        val r = b.r
        for (i in 0..n) {
            val t = i / n.toFloat()
            val x = ax + (bx - ax) * t; val y = ay + (by - ay) * t; val z = az + (bz - az) * t
            val dx = x - b.p[0]; val dy = y - b.p[1]; val dz = z - b.p[2]
            val lx = r[0] * dx + r[3] * dy + r[6] * dz
            val ly = r[1] * dx + r[4] * dy + r[7] * dz
            val lz = r[2] * dx + r[5] * dy + r[8] * dz
            val px = b.hx - abs(lx); val py = b.hy - abs(ly); val pz = b.hz - abs(lz)
            if (px <= 0f || py <= 0f || pz <= 0f) continue
            // face do corpo mais perto do ponto; o corpo é empurrado para longe dele
            var nx: Float; var ny: Float; var nz: Float; var d: Float
            if (py <= px && py <= pz) { val sg = if (ly > 0) -1f else 1f; nx = r[1] * sg; ny = r[4] * sg; nz = r[7] * sg; d = py }
            else if (px <= pz) { val sg = if (lx > 0) -1f else 1f; nx = r[0] * sg; ny = r[3] * sg; nz = r[6] * sg; d = px }
            else { val sg = if (lz > 0) -1f else 1f; nx = r[2] * sg; ny = r[5] * sg; nz = r[8] * sg; d = pz }
            addC(b, null, x, y, z, nx, ny, nz, d)
        }
    }

    private fun sphereBox(b: Body, s: SBox) {
        val r = b.hx
        val x = b.p[0].coerceIn(s.x0, s.x1); val y = b.p[1].coerceIn(s.y0, s.y1); val z = b.p[2].coerceIn(s.z0, s.z1)
        val dx = b.p[0] - x; val dy = b.p[1] - y; val dz = b.p[2] - z
        val d2 = dx * dx + dy * dy + dz * dz
        if (d2 >= r * r) return
        if (d2 > 1e-10f) {
            val d = sqrt(d2)
            addC(b, null, x, y, z, dx / d, dy / d, dz / d, r - d)
        } else pointInStatic(b, s, b.p[0], b.p[1] - r, b.p[2])
    }

    private fun pair(a: Body, b: Body) {
        if (a.kinematic && b.kinematic) return
        val rr = a.hx + a.hy + a.hz + b.hx + b.hy + b.hz
        val dx = b.p[0] - a.p[0]; val dy = b.p[1] - a.p[1]; val dz = b.p[2] - a.p[2]
        if (dx * dx + dy * dy + dz * dz > rr * rr) return
        if (a.sphere && b.sphere) {
            val d = sqrt(dx * dx + dy * dy + dz * dz); val pen = a.hx + b.hx - d
            if (pen > 0f && d > 1e-6f) {
                val nx = -dx / d; val ny = -dy / d; val nz = -dz / d
                addC(a, b, a.p[0] - nx * a.hx, a.p[1] - ny * a.hx, a.p[2] - nz * a.hx, nx, ny, nz, pen)
            }
            return
        }
        if (a.sphere != b.sphere) {
            val sp = if (a.sphere) a else b; val bx = if (a.sphere) b else a
            sphereObb(sp, bx)
            return
        }
        // cantos e meios das arestas, um pouco para dentro (faces e arestas que coincidem também contam)
        for (i in 0 until 20) { boxPoint(a, i, tmp2); pointInBody(a, b, tmp2[0], tmp2[1], tmp2[2]) }
        for (i in 0 until 20) { boxPoint(b, i, tmp2); pointInBody(b, a, tmp2[0], tmp2[1], tmp2[2]) }
    }

    /** ponto do corpo [a] dentro da caixa [b]: contato que empurra [a] para fora de [b]. */
    private fun pointInBody(a: Body, b: Body, x: Float, y: Float, z: Float) {
        val r = b.r
        val dx = x - b.p[0]; val dy = y - b.p[1]; val dz = z - b.p[2]
        val lx = r[0] * dx + r[3] * dy + r[6] * dz
        val ly = r[1] * dx + r[4] * dy + r[7] * dz
        val lz = r[2] * dx + r[5] * dy + r[8] * dz
        val px = b.hx - abs(lx); val py = b.hy - abs(ly); val pz = b.hz - abs(lz)
        if (px <= 0f || py <= 0f || pz <= 0f) return
        var nx: Float; var ny: Float; var nz: Float; var d: Float
        if (py <= px && py <= pz) { val sg = if (ly > 0) 1f else -1f; nx = r[1] * sg; ny = r[4] * sg; nz = r[7] * sg; d = py }
        else if (px <= pz) { val sg = if (lx > 0) 1f else -1f; nx = r[0] * sg; ny = r[3] * sg; nz = r[6] * sg; d = px }
        else { val sg = if (lz > 0) 1f else -1f; nx = r[2] * sg; ny = r[5] * sg; nz = r[8] * sg; d = pz }
        addC(a, b, x, y, z, nx, ny, nz, d)
    }

    private fun sphereObb(sp: Body, bx: Body) {
        val r = bx.r
        val dx = sp.p[0] - bx.p[0]; val dy = sp.p[1] - bx.p[1]; val dz = sp.p[2] - bx.p[2]
        val lx = (r[0] * dx + r[3] * dy + r[6] * dz).coerceIn(-bx.hx, bx.hx)
        val ly = (r[1] * dx + r[4] * dy + r[7] * dz).coerceIn(-bx.hy, bx.hy)
        val lz = (r[2] * dx + r[5] * dy + r[8] * dz).coerceIn(-bx.hz, bx.hz)
        val cx = bx.p[0] + r[0] * lx + r[1] * ly + r[2] * lz
        val cy = bx.p[1] + r[3] * lx + r[4] * ly + r[5] * lz
        val cz = bx.p[2] + r[6] * lx + r[7] * ly + r[8] * lz
        val ex = sp.p[0] - cx; val ey = sp.p[1] - cy; val ez = sp.p[2] - cz
        val d2 = ex * ex + ey * ey + ez * ez
        if (d2 >= sp.hx * sp.hx || d2 < 1e-10f) return
        val d = sqrt(d2)
        addC(sp, bx, cx, cy, cz, ex / d, ey / d, ez / d, sp.hx - d)
    }

    /** personagem: cilindro (pernas 0,25 m; mãos alcançam 0,36 m acima de 0,45 m) que empurra; correndo, chuta. */
    private fun player(b: Body, wd: World) {
        val bottom = b.p[1] - b.extent(0f, 1f, 0f)
        if (bottom > 1.35f) return
        val pr = if (bottom > 0.45f) 0.36f else 0.25f
        val dx = b.p[0] - wd.px; val dz = b.p[2] - wd.pz
        val d = sqrt(dx * dx + dz * dz)
        if (d < 1e-4f) return
        val nx = dx / d; val nz = dz / d
        val ext = b.extent(nx, 0f, nz)
        val pen = pr + ext - d
        if (pen <= 0f) return
        val sp = sqrt(wd.pvx * wd.pvx + wd.pvz * wd.pvz)
        val kick = if (b.sphere && wd.pRun && bottom < 0.3f) 0.35f * sp else 0f
        val py = min(b.p[1], 1.1f)
        addC(b, null, b.p[0] - nx * ext, py, b.p[2] - nz * ext, nx, 0f, nz, pen, wd.pvx * (if (b.sphere && wd.pRun) 1.2f else 1f), kick, wd.pvz * (if (b.sphere && wd.pRun) 1.2f else 1f))
        b.sleep = false
    }

    private fun relVel(c: Int, a: Body, o: Body?, out: FloatArray) {
        val px = cp[c * 3]; val py = cp[c * 3 + 1]; val pz = cp[c * 3 + 2]
        val rax = px - a.p[0]; val ray = py - a.p[1]; val raz = pz - a.p[2]
        var vx = a.v[0] + a.w[1] * raz - a.w[2] * ray
        var vy = a.v[1] + a.w[2] * rax - a.w[0] * raz
        var vz = a.v[2] + a.w[0] * ray - a.w[1] * rax
        if (o != null) {
            val rbx = px - o.p[0]; val rby = py - o.p[1]; val rbz = pz - o.p[2]
            vx -= o.v[0] + o.w[1] * rbz - o.w[2] * rby
            vy -= o.v[1] + o.w[2] * rbx - o.w[0] * rbz
            vz -= o.v[2] + o.w[0] * rby - o.w[1] * rbx
        } else { vx -= cv[c * 3]; vy -= cv[c * 3 + 1]; vz -= cv[c * 3 + 2] }
        out[0] = vx; out[1] = vy; out[2] = vz
    }

    private fun prepare(c: Int) {
        val a = cb[c]!!; val o = co[c]
        pn[c] = 0f; pt1[c] = 0f; pt2[c] = 0f
        val nx = cn[c * 3]; val ny = cn[c * 3 + 1]; val nz = cn[c * 3 + 2]
        // base tangente
        var ax: Float; var ay: Float; var az: Float
        if (abs(ny) < 0.9f) { ax = nz; ay = 0f; az = -nx } else { ax = 0f; ay = -nz; az = ny }
        val l = sqrt(ax * ax + ay * ay + az * az); ax /= l; ay /= l; az /= l
        t1[c * 3] = ax; t1[c * 3 + 1] = ay; t1[c * 3 + 2] = az
        t2[c * 3] = ny * az - nz * ay; t2[c * 3 + 1] = nz * ax - nx * az; t2[c * 3 + 2] = nx * ay - ny * ax
        val px = cp[c * 3]; val py = cp[c * 3 + 1]; val pz = cp[c * 3 + 2]
        val rax = px - a.p[0]; val ray = py - a.p[1]; val raz = pz - a.p[2]
        var rbx = 0f; var rby = 0f; var rbz = 0f
        if (o != null) { rbx = px - o.p[0]; rby = py - o.p[1]; rbz = pz - o.p[2] }
        kn[c] = kEff(a, o, rax, ray, raz, rbx, rby, rbz, nx, ny, nz)
        k1[c] = kEff(a, o, rax, ray, raz, rbx, rby, rbz, t1[c * 3], t1[c * 3 + 1], t1[c * 3 + 2])
        k2[c] = kEff(a, o, rax, ray, raz, rbx, rby, rbz, t2[c * 3], t2[c * 3 + 1], t2[c * 3 + 2])
        relVel(c, a, o, tmp2)
        val vn = tmp2[0] * nx + tmp2[1] * ny + tmp2[2] * nz
        val e = if (o != null) min(a.e, o.e) else a.e
        bias[c] = if (vn < -0.7f) -e * vn else 0f
    }

    private fun solve(c: Int) {
        val a = cb[c]!!; val o = co[c]
        if (a.sleep && (o == null || o.sleep)) return
        val nx = cn[c * 3]; val ny = cn[c * 3 + 1]; val nz = cn[c * 3 + 2]
        val px = cp[c * 3]; val py = cp[c * 3 + 1]; val pz = cp[c * 3 + 2]
        val rax = px - a.p[0]; val ray = py - a.p[1]; val raz = pz - a.p[2]
        var rbx = 0f; var rby = 0f; var rbz = 0f
        if (o != null) { rbx = px - o.p[0]; rby = py - o.p[1]; rbz = pz - o.p[2] }
        // normal
        relVel(c, a, o, tmp2)
        val vn = tmp2[0] * nx + tmp2[1] * ny + tmp2[2] * nz
        var lam = (bias[c] - vn) / kn[c]
        val np = max(pn[c] + lam, 0f); lam = np - pn[c]; pn[c] = np
        if (lam != 0f) imp(a, o, rax, ray, raz, rbx, rby, rbz, nx * lam, ny * lam, nz * lam)
        // atrito (2 direções), limitado pelo impulso normal acumulado
        val mu = if (o != null) sqrt(a.mu * o.mu) else a.mu
        val lim = mu * pn[c]
        relVel(c, a, o, tmp2)
        val ax = t1[c * 3]; val ay = t1[c * 3 + 1]; val az = t1[c * 3 + 2]
        var l1 = -(tmp2[0] * ax + tmp2[1] * ay + tmp2[2] * az) / k1[c]
        val n1 = (pt1[c] + l1).coerceIn(-lim, lim); l1 = n1 - pt1[c]; pt1[c] = n1
        if (l1 != 0f) imp(a, o, rax, ray, raz, rbx, rby, rbz, ax * l1, ay * l1, az * l1)
        relVel(c, a, o, tmp2)
        val bx = t2[c * 3]; val by = t2[c * 3 + 1]; val bz = t2[c * 3 + 2]
        var l2 = -(tmp2[0] * bx + tmp2[1] * by + tmp2[2] * bz) / k2[c]
        val n2 = (pt2[c] + l2).coerceIn(-lim, lim); l2 = n2 - pt2[c]; pt2[c] = n2
        if (l2 != 0f) imp(a, o, rax, ray, raz, rbx, rby, rbz, bx * l2, by * l2, bz * l2)
    }

    private fun kEff(a: Body, o: Body?, rax: Float, ray: Float, raz: Float, rbx: Float, rby: Float, rbz: Float, nx: Float, ny: Float, nz: Float): Float {
        // (r × n)
        var cx = ray * nz - raz * ny; var cy = raz * nx - rax * nz; var cz = rax * ny - ray * nx
        a.iw(cx, cy, cz, tmp)
        var k = a.invM + nx * (tmp[1] * raz - tmp[2] * ray) + ny * (tmp[2] * rax - tmp[0] * raz) + nz * (tmp[0] * ray - tmp[1] * rax)
        if (o != null && !o.kinematic) {
            cx = rby * nz - rbz * ny; cy = rbz * nx - rbx * nz; cz = rbx * ny - rby * nx
            o.iw(cx, cy, cz, tmp)
            k += o.invM + nx * (tmp[1] * rbz - tmp[2] * rby) + ny * (tmp[2] * rbx - tmp[0] * rbz) + nz * (tmp[0] * rby - tmp[1] * rbx)
        }
        return max(k, 1e-6f)
    }

    private fun imp(a: Body, o: Body?, rax: Float, ray: Float, raz: Float, rbx: Float, rby: Float, rbz: Float, jx: Float, jy: Float, jz: Float) {
        if (!a.kinematic) {
            a.v[0] += jx * a.invM; a.v[1] += jy * a.invM; a.v[2] += jz * a.invM
            a.iw(ray * jz - raz * jy, raz * jx - rax * jz, rax * jy - ray * jx, tmp)
            a.w[0] += tmp[0]; a.w[1] += tmp[1]; a.w[2] += tmp[2]
        }
        if (o != null && !o.kinematic) {
            o.v[0] -= jx * o.invM; o.v[1] -= jy * o.invM; o.v[2] -= jz * o.invM
            o.iw(rby * jz - rbz * jy, rbz * jx - rbx * jz, rbx * jy - rby * jx, tmp)
            o.w[0] -= tmp[0]; o.w[1] -= tmp[1]; o.w[2] -= tmp[2]
        }
    }

    /** Escreve a posição do corpo no item (para seleção, arrasto e gravação). */
    fun writeBack(b: Body) {
        val it = b.item
        val cx = b.p[0] - it.w / 2f; val cz = b.p[2] - it.h / 2f
        it.x = floor(cx).toInt(); it.ox = cx - it.x
        it.y = floor(cz).toInt(); it.oz = cz - it.y
        b.lastX = it.x + it.ox; b.lastZ = it.y + it.oz
        if (b.sleep) it.st = b.encode()
    }
}
