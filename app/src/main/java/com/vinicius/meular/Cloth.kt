package com.vinicius.meular

import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Etapa 75: cortinas com física de tecido de verdade (integração de Verlet + restrições de distância).
 * Cada cortina é uma malha de partículas presa na barra; o tecido tem largura sobrando (pregas), é amarrado
 * por uma faixa, cai com a gravidade, balança com uma brisa, não atravessa a parede nem os móveis e é
 * empurrado pelo personagem. A simulação roda no espaço da parede (z = para dentro do cômodo).
 */
class ClothCurtains {
    private val NX = 11
    private val NY = 17
    private val TOP = 2.04f
    private val HEM = 0.58f
    private val TIE_Y = 1.22f
    private val PW = 0.5f        // largura presa na barra
    private val FULL = 1.85f     // largura do tecido (fullness): sobra vira prega
    private val Z0 = 0.075f      // distância mínima da parede

    inner class Panel(val wall: Int, val xTop0: Float, val xTop1: Float, val tieX: Float, val col: Int, val phase: Float) {
        val n = NX * NY
        val x = FloatArray(n); val y = FloatArray(n); val z = FloatArray(n)
        val ox = FloatArray(n); val oy = FloatArray(n); val oz = FloatArray(n)
        val ax = FloatArray(n); val az = FloatArray(n)   // forma de pregas "de costura" (a física se move em volta dela)
        val rowT = Math.round((TOP - TIE_Y) / (TOP - HEM) * (NY - 1))
        val restX = FULL * PW / (NX - 1)
        val restY = (TOP - HEM) / (NY - 1)
        val fb = ByteBuffer.allocateDirect(n * STRIDE * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
        val ib: java.nio.ShortBuffer
        val tmp = FloatArray(n * STRIDE)
        val mesh: Mesh
        val ni: Int

        init {
            for (j in 0 until NY) for (i in 0 until NX) {
                val k = j * NX + i
                val u = i / (NX - 1f)
                x[k] = xTop0 + (xTop1 - xTop0) * u
                y[k] = TOP - restY * j
                z[k] = 0.118f + 0.05f * (i % 2) * (j / (NY - 1f))
                ox[k] = x[k]; oy[k] = y[k]; oz[k] = z[k]
                val v = j / (NY - 1f)
                val mid = (xTop0 + xTop1) / 2f
                val bandX = tieX + (u - 0.5f) * 0.09f
                val ux = xTop0 + (xTop1 - xTop0) * u
                ax[k] = if (j <= rowT) ux + (bandX - ux) * (j / rowT.toFloat())
                        else { val t2 = (j - rowT) / (NY - 1f - rowT); bandX + ((mid + (u - 0.5f) * PW * 1.22f) - bandX) * t2 }
                az[k] = 0.118f + 0.10f * (i % 2) * (0.25f + 0.75f * v)
            }
            val idx = ShortArray((NX - 1) * (NY - 1) * 6)
            var c = 0
            for (j in 0 until NY - 1) for (i in 0 until NX - 1) {
                val a = (j * NX + i).toShort(); val b = (j * NX + i + 1).toShort()
                val d = ((j + 1) * NX + i).toShort(); val e = ((j + 1) * NX + i + 1).toShort()
                idx[c++] = a; idx[c++] = d; idx[c++] = b
                idx[c++] = b; idx[c++] = d; idx[c++] = e
            }
            ni = idx.size
            ib = ByteBuffer.allocateDirect(ni * 2).order(ByteOrder.nativeOrder()).asShortBuffer()
            ib.put(idx); ib.position(0)
            val part = Part(Mt.FABRIC, fb, n, ib, ni)
            mesh = Mesh(listOf(part))
            writeMesh()
        }

        fun writeMesh() {
            val cr = android.graphics.Color.red(col) / 255f
            val cg = android.graphics.Color.green(col) / 255f
            val cb = android.graphics.Color.blue(col) / 255f
            for (j in 0 until NY) for (i in 0 until NX) {
                val k = j * NX + i
                val il = max(0, i - 1); val ir = min(NX - 1, i + 1)
                val ju = max(0, j - 1); val jd = min(NY - 1, j + 1)
                val a = j * NX + il; val b = j * NX + ir; val u = ju * NX + i; val d = jd * NX + i
                val rx = x[b] - x[a]; val ry = y[b] - y[a]; val rz = z[b] - z[a]
                val dx = x[d] - x[u]; val dy = y[d] - y[u]; val dz = z[d] - z[u]
                var nx = dy * rz - dz * ry; var ny = dz * rx - dx * rz; var nz = dx * ry - dy * rx
                val l = sqrt(nx * nx + ny * ny + nz * nz)
                if (l > 1e-6f) { nx /= l; ny /= l; nz /= l } else { nx = 0f; ny = 0f; nz = 1f }
                if (nz < 0f) { nx = -nx; ny = -ny; nz = -nz }
                // sombra de prega: o que está mais fundo (perto da parede) fica mais escuro
                val depth = ((z[k] - Z0) / 0.12f).coerceIn(0f, 1f)
                var sh = 0.70f + 0.42f * depth
                // faixa de amarração: mais escura e dourada
                var tr = 1f; var tg = 1f; var tb = 1f
                if (abs(j - rowT) <= 0) { tr = 0.95f; tg = 0.78f; tb = 0.55f; sh *= 0.9f }
                // bainha
                if (j >= NY - 2) sh *= 0.9f
                val o = k * STRIDE
                tmp[o] = x[k]; tmp[o + 1] = y[k]; tmp[o + 2] = z[k]
                tmp[o + 3] = nx; tmp[o + 4] = ny; tmp[o + 5] = nz
                tmp[o + 6] = min(1.4f, cr * sh * tr * 1.15f); tmp[o + 7] = min(1.4f, cg * sh * tg * 1.15f); tmp[o + 8] = min(1.4f, cb * sh * tb * 1.15f); tmp[o + 9] = 1f
                tmp[o + 10] = i / (NX - 1f) * 1.2f; tmp[o + 11] = j / (NY - 1f) * 1.6f
            }
            fb.position(0)
            fb.put(tmp, 0, n * STRIDE)
            fb.position(0)
        }
    }

    val panels = ArrayList<Panel>()
    private var gw = 0f
    private var gh = 0f
    private var tAcc = 0f

    fun clear() { panels.clear() }

    /** Cria as duas folhas (esquerda e direita) de uma janela da parede [wall] (coordenadas locais da parede). */
    fun addWindow(wall: Int, c: Double, w: Double, col: Int) {
        val xin = (w / 2 + 0.10).toFloat()
        val cc = c.toFloat()
        // esquerda: borda externa em c - xin - PW, interna em c - xin
        panels.add(Panel(wall, cc - xin - PW, cc - xin, cc - xin - 0.05f, col, 0f))
        // direita
        panels.add(Panel(wall, cc + xin, cc + xin + PW, cc + xin + 0.05f, col, 1.7f))
    }

    /** Passo da física. Posição do personagem e móveis em coordenadas do mundo. */
    fun step(dtIn: Float, time: Float, gw: Float, gh: Float, plx: Float, plz: Float, items: List<Item>) {
        this.gw = gw; this.gh = gh
        val dt = min(dtIn, 0.033f)
        if (dt <= 0f) return
        for (p in panels) stepPanel(p, dt, time, plx, plz, items)
    }

    private fun toLocal(wall: Int, wx: Float, wz: Float, out: FloatArray) {
        when (wall) {
            1 -> { out[0] = gw - wx; out[1] = gh - wz }
            2 -> { out[0] = gh - wz; out[1] = wx }
            else -> { out[0] = wx; out[1] = wz }
        }
    }

    private val tl = FloatArray(2)
    private val rc = FloatArray(4)

    private fun stepPanel(p: Panel, dt: Float, time: Float, plx: Float, plz: Float, items: List<Item>) {
        val n = p.n
        val g = -9.0f * dt * dt
        // personagem e móveis no espaço local da parede
        toLocal(p.wall, plx, plz, tl)
        val pcx = tl[0]; val pcz = tl[1]
        // 1) integração de Verlet
        for (j in 1 until NY) for (i in 0 until NX) {
            val k = j * NX + i
            val vx = (p.x[k] - p.ox[k]) * 0.975f
            val vy = (p.y[k] - p.oy[k]) * 0.985f
            val vz = (p.z[k] - p.oz[k]) * 0.96f
            p.ox[k] = p.x[k]; p.oy[k] = p.y[k]; p.oz[k] = p.z[k]
            val hv = 1f - j / (NY - 1f)   // 1 no alto, 0 na bainha
            // brisa vinda da janela: infla o tecido para dentro do cômodo, mais forte embaixo
            val wnd = (0.5f + 0.5f * sin(time * 0.8f + p.phase + p.x[k] * 1.3f)) * (0.55f + 0.45f * sin(time * 0.37f + p.phase * 2f))
            val az = 2.2f * wnd * (0.25f + 0.75f * (1f - hv)) * dt * dt
            val ax = 0.35f * sin(time * 0.6f + p.phase + p.y[k]) * (1f - hv) * dt * dt
            p.x[k] += vx + ax
            p.y[k] += vy + g
            p.z[k] += vz + az
        }
        // 2) restrições (várias passadas)
        for (iter in 0 until 5) {
            for (j in 0 until NY) for (i in 0 until NX) {
                val k = j * NX + i
                if (i + 1 < NX) satisfy(p, k, k + 1, p.restX, j == 0)
                if (j + 1 < NY) satisfy(p, k, k + NX, p.restY, false)
            }
            // flexão leve: pontos a dois de distância não se afastam demais (evita dobras duras)
            for (j in 0 until NY) for (i in 0 until NX - 2) {
                val k = j * NX + i
                limitMax(p, k, k + 2, p.restX * 2f * 0.98f)
            }
            for (j in 0 until NY - 2) for (i in 0 until NX) {
                val k = j * NX + i
                limitMax(p, k, k + 2 * NX, p.restY * 2f * 1.01f)
            }
            // presa na barra (linha de cima)
            for (i in 0 until NX) {
                p.x[i] = p.xTop0 + (p.xTop1 - p.xTop0) * (i / (NX - 1f))
                p.y[i] = TOP
                p.z[i] = 0.118f
            }
            // faixa de amarração: a linha do laço fica junta, ao lado da janela
            val rt = p.rowT
            val half = 0.045f
            for (i in 0 until NX) {
                val k = rt * NX + i
                val u = i / (NX - 1f) - 0.5f
                val tx = p.tieX + u * 2f * half
                p.x[k] += (tx - p.x[k]) * 0.8f
                val tz = 0.14f + 0.03f * (i % 2)
                p.z[k] += (tz - p.z[k]) * 0.35f
                p.y[k] += ((TIE_Y) - p.y[k]) * 0.5f
            }
            // memória das pregas: puxão leve para a forma costurada (o tecido balança em volta dela)
            for (j in 1 until NY) {
                if (j == rt) continue
                for (i in 0 until NX) {
                    val k = j * NX + i
                    p.x[k] += (p.ax[k] - p.x[k]) * 0.05f
                    p.z[k] += (p.az[k] - p.z[k]) * 0.035f
                }
            }
            // colisões
            for (j in 1 until NY) for (i in 0 until NX) {
                val k = j * NX + i
                if (p.z[k] < Z0) p.z[k] = Z0
                if (p.y[k] < 0.02f) { p.y[k] = 0.02f }
                // personagem: cilindro de 30 cm de raio
                if (p.y[k] < 1.8f) {
                    val dx = p.x[k] - pcx; val dz = p.z[k] - pcz
                    val d2 = dx * dx + dz * dz
                    val r = 0.30f
                    if (d2 < r * r) {
                        val d = sqrt(max(d2, 1e-6f))
                        // sempre empurra para o lado de dentro do cômodo (z) quando está atrás do personagem
                        val nx = dx / d; var nz = dz / d
                        if (nz < 0f) nz = abs(nz) * 0.2f
                        p.x[k] = pcx + nx * r
                        p.z[k] = max(p.z[k], pcz + nz * r)
                    }
                }
            }
            // móveis: o tecido cobre por cima ou fica na frente
            for (it in items) {
                if (it.type.rug) continue
                val r = it.rect()
                // retângulo do móvel no espaço local da parede
                val lx0: Float; val lx1: Float; val lz0: Float; val lz1: Float
                when (p.wall) {
                    1 -> { lx0 = gw - r[2]; lx1 = gw - r[0]; lz0 = gh - r[3]; lz1 = gh - r[1] }
                    2 -> { lx0 = gh - r[3]; lx1 = gh - r[1]; lz0 = r[0]; lz1 = r[2] }
                    else -> { lx0 = r[0]; lx1 = r[2]; lz0 = r[1]; lz1 = r[3] }
                }
                if (lz0 > 1.3f || lx1 < p.xTop0 - 0.2f || lx0 > p.xTop1 + 0.2f) continue
                val top = it.type.alt
                if (top < HEM - 0.05f) continue
                for (j in 1 until NY) for (i in 0 until NX) {
                    val k = j * NX + i
                    val px = p.x[k]; val py = p.y[k]; val pz = p.z[k]
                    if (px > lx0 - 0.02f && px < lx1 + 0.02f && pz < lz1 + 0.02f && pz > lz0 - 0.05f && py < top + 0.02f) {
                        val over = top + 0.02f - py
                        val front = lz1 + 0.025f - pz
                        if (over < 0.10f && over < front) p.y[k] = top + 0.02f else p.z[k] = lz1 + 0.025f
                    }
                }
            }
        }
        p.writeMesh()
    }

    private fun satisfy(p: Panel, a: Int, b: Int, rest: Float, topRow: Boolean) {
        val dx = p.x[b] - p.x[a]; val dy = p.y[b] - p.y[a]; val dz = p.z[b] - p.z[a]
        val d = sqrt(dx * dx + dy * dy + dz * dz)
        if (d < 1e-6f) return
        // na horizontal o tecido pode comprimir (vira prega) mas quase não estica
        val diff = (d - rest) / d
        val vertical = abs(dy) > abs(dx)
        if (!vertical && d < rest) return   // horizontal comprimido: o tecido junta (vira prega), não empurra
        val aTop = a < NX; val bTop = b < NX
        val wa = if (aTop) 0f else 0.5f
        val wb = if (bTop) 0f else 0.5f
        val s = wa + wb
        if (s == 0f) return
        val ka = diff * (wa / s); val kb = diff * (wb / s)
        p.x[a] += dx * ka; p.y[a] += dy * ka; p.z[a] += dz * ka
        p.x[b] -= dx * kb; p.y[b] -= dy * kb; p.z[b] -= dz * kb
    }

    private fun limitMax(p: Panel, a: Int, b: Int, max: Float) {
        val dx = p.x[b] - p.x[a]; val dy = p.y[b] - p.y[a]; val dz = p.z[b] - p.z[a]
        val d = sqrt(dx * dx + dy * dy + dz * dz)
        if (d <= max || d < 1e-6f) return
        val diff = (d - max) / d * 0.5f
        val wa = if (a < NX) 0f else 1f
        val wb = if (b < NX) 0f else 1f
        val s = wa + wb
        if (s == 0f) return
        p.x[a] += dx * diff * (wa / s) * 2f * 0.5f; p.y[a] += dy * diff * (wa / s) * 2f * 0.5f; p.z[a] += dz * diff * (wa / s) * 2f * 0.5f
        p.x[b] -= dx * diff * (wb / s) * 2f * 0.5f; p.y[b] -= dy * diff * (wb / s) * 2f * 0.5f; p.z[b] -= dz * diff * (wb / s) * 2f * 0.5f
    }

    fun release() { /* buffers são diretos (client arrays): nada a liberar na GPU */ }
}
