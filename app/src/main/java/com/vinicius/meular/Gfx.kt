package com.vinicius.meular

import android.graphics.Bitmap
import android.graphics.Color
import android.opengl.GLES20
import android.opengl.GLUtils
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.sign
import kotlin.math.sin
import kotlin.math.sqrt

/** Vértice: posição(3) normal(3) cor(4) uv(2). Normal zero = sem iluminação. */
const val STRIDE = 12

object Mt {
    const val PLAIN = 0
    const val FLOOR_L = 1
    const val FLOOR_D = 2
    const val TILE = 3
    const val STONE = 4
    const val PLASTER = 5
    const val WOOD = 6
    const val FABRIC = 7
    const val GRASS = 8
    const val PAVER = 9
    const val RUG = 10
    const val METAL = 11
    const val GLASS = 12
    const val COUNT = 13
    val SPEC = floatArrayOf(0.05f, 0.35f, 0.40f, 0.75f, 0.05f, 0.02f, 0.25f, 0.0f, 0.0f, 0.10f, 0.0f, 0.85f, 0.9f)
}

class Part(val mat: Int, val buf: FloatBuffer, val count: Int)
class Mesh(val parts: List<Part>)

fun C(s: String): Int = Color.parseColor(s)

fun shade(c: Int, d: Int): Int {
    fun k(v: Int) = (v + d).coerceIn(0, 255)
    return Color.rgb(k(Color.red(c)), k(Color.green(c)), k(Color.blue(c)))
}

fun mix(a: Int, b: Int, t: Float): Int {
    fun k(x: Int, y: Int) = (x + (y - x) * t).toInt().coerceIn(0, 255)
    return Color.rgb(k(Color.red(a), Color.red(b)), k(Color.green(a), Color.green(b)), k(Color.blue(a), Color.blue(b)))
}

// ---------------------------------------------------------------- ruído

object Noise {
    fun h(x: Int, y: Int, s: Int): Float {
        var n = x * 374761393 + y * 668265263 + s * 1274126177.toInt()
        n = (n xor (n ushr 13)) * 1274126177
        n = n xor (n ushr 16)
        return (n and 0xffff) / 65535f
    }

    private fun vn(x: Float, y: Float, px: Int, py: Int, s: Int): Float {
        val x0 = floor(x).toInt()
        val y0 = floor(y).toInt()
        val fx = x - x0
        val fy = y - y0
        val ux = fx * fx * (3f - 2f * fx)
        val uy = fy * fy * (3f - 2f * fy)
        fun g(ix: Int, iy: Int) = h(Math.floorMod(ix, px), Math.floorMod(iy, py), s)
        val a = g(x0, y0) + (g(x0 + 1, y0) - g(x0, y0)) * ux
        val b = g(x0, y0 + 1) + (g(x0 + 1, y0 + 1) - g(x0, y0 + 1)) * ux
        return a + (b - a) * uy
    }

    /** Ruído fractal que repete (tileável) em u,v de 0 a 1. */
    fun fbm(u: Float, v: Float, fx: Int, fy: Int, oct: Int, s: Int): Float {
        var a = 0f
        var amp = 0.5f
        var tot = 0f
        var cx = fx
        var cy = fy
        for (o in 0 until oct) {
            a += amp * vn(u * cx, v * cy, cx, cy, s + o * 11)
            tot += amp
            amp *= 0.5f
            cx *= 2
            cy *= 2
        }
        return a / tot
    }
}

// ---------------------------------------------------------------- texturas procedurais

object Tex {
    val ids = IntArray(Mt.COUNT)
    private val cache = arrayOfNulls<IntArray>(Mt.COUNT)
    private const val S = 256
    private const val TP = 6.2831853f

    private fun px(r: Float, g: Float, b: Float): Int =
        Color.rgb((r * 255f).coerceIn(0f, 255f).toInt(), (g * 255f).coerceIn(0f, 255f).toInt(), (b * 255f).coerceIn(0f, 255f).toInt())

    private fun plank(x: Int, y: Int, u: Float, v: Float, r: Float, g: Float, b: Float, seed: Int): Int {
        val row = y / 64
        val yy = y % 64
        val jx = (Noise.h(row, 0, seed) * 200f).toInt() + 28
        val seg = if (x >= jx) 1 else 0
        val tone = 0.88f + 0.24f * Noise.h(row, seg, seed + 3)
        val gr = Noise.fbm(u + Noise.h(row, seg, seed + 5), v, 3, 40, 3, seed + 7)
        var k = tone * (0.80f + 0.40f * gr)
        k *= 0.96f + 0.08f * Noise.h(x, y / 2, seed + 9)
        if (yy < 2) k *= 0.55f else if (yy == 2) k *= 0.9f else if (yy == 3) k *= 1.06f
        if (x == jx || x == jx + 1 || x == 0 || x == 1) k *= 0.62f
        return px(r * k, g * k, b * k)
    }

    private fun tile(x: Int, y: Int, u: Float, v: Float): Int {
        val tx = x / 128
        val ty = y / 128
        val lx = x % 128
        val ly = y % 128
        if (lx < 3 || ly < 3) {
            val n = 0.9f + 0.1f * Noise.h(x, y, 3)
            return px(0.58f * n, 0.57f * n, 0.55f * n)
        }
        val n = Noise.fbm(u, v, 3, 3, 4, 21)
        val t = abs(sin(TP * (2f * u + 1.5f * n)))
        val line = if (t < 0.07f) 0.13f * (1f - t / 0.07f) else 0f
        var k = 0.91f + 0.07f * n - line
        k *= 0.97f + 0.05f * Noise.h(tx, ty, 5)
        if (lx < 6 || ly < 6) k *= 0.965f
        k *= 0.985f + 0.03f * Noise.h(x, y, 8)
        return px(0.93f * k, 0.92f * k, 0.89f * k)
    }

    private fun bricks(x: Int, y: Int, u: Float, v: Float, r: Float, g: Float, b: Float, seed: Int): Int {
        val row = y / 64
        val off = if (row % 2 == 0) 0 else 64
        val xx = (x + off) % 256
        val bx = xx / 128
        val lx = xx % 128
        val ly = y % 64
        if (lx < 3 || ly < 3) {
            val n = 0.45f + 0.15f * Noise.h(x, y, seed)
            return px(r * n, g * n, b * n)
        }
        val tone = 0.86f + 0.26f * Noise.h(row, bx, seed + 1)
        val m = 0.88f + 0.24f * Noise.fbm(u, v, 8, 8, 3, seed + 2)
        val sp = 0.94f + 0.12f * Noise.h(x, y, seed + 4)
        var k = tone * m * sp
        if (lx < 6 || ly < 6) k *= 1.05f
        return px(r * k, g * k, b * k)
    }

    private fun gen(m: Int): IntArray {
        val a = IntArray(S * S)
        for (y in 0 until S) for (x in 0 until S) {
            val u = x.toFloat() / S
            val v = y.toFloat() / S
            a[y * S + x] = when (m) {
                Mt.FLOOR_L -> plank(x, y, u, v, 0.86f, 0.66f, 0.43f, 11)
                Mt.FLOOR_D -> plank(x, y, u, v, 0.50f, 0.31f, 0.19f, 23)
                Mt.TILE -> tile(x, y, u, v)
                Mt.STONE -> bricks(x, y, u, v, 0.60f, 0.60f, 0.63f, 31)
                Mt.PAVER -> bricks(x, y, u, v, 0.78f, 0.69f, 0.57f, 41)
                Mt.PLASTER -> {
                    val n = Noise.fbm(u, v, 16, 16, 3, 51)
                    val k = 0.93f + 0.05f * n + 0.03f * (Noise.h(x, y, 9) - 0.5f)
                    px(k, k, k * 0.99f)
                }
                Mt.WOOD -> {
                    val n = Noise.fbm(u, v, 2, 24, 3, 61)
                    val n2 = Noise.fbm(u, v, 4, 64, 2, 67)
                    val k = 0.90f + 0.12f * sin(TP * (v * 10f + 1.2f * n)) + 0.06f * (n2 - 0.5f)
                    px(k, k * 0.98f, k * 0.95f)
                }
                Mt.FABRIC -> {
                    val chk = ((x / 2 + y / 2) and 1)
                    val th = if (chk == 0) 1.0f else 0.86f
                    val fib = 0.94f + 0.06f * Noise.h(x, y, 31)
                    val k = th * fib * (0.96f + 0.08f * Noise.fbm(u, v, 8, 8, 2, 3))
                    px(k, k, k)
                }
                Mt.GRASS -> {
                    val n1 = Noise.fbm(u, v, 6, 6, 4, 71)
                    val n2 = Noise.h(x, y, 77)
                    var r = 0.20f + 0.25f * n1
                    var g = 0.42f + 0.28f * n1
                    var b = 0.14f + 0.11f * n1
                    val k = 0.88f + 0.22f * n2
                    r *= k; g *= k; b *= k
                    if (Noise.h(x, y, 79) > 0.94f) { r *= 1.25f; g *= 1.2f }
                    px(r, g, b)
                }
                Mt.RUG -> rug(x, y, u, v)
                Mt.METAL -> {
                    val k = 0.80f + 0.16f * Noise.fbm(u, v, 2, 96, 2, 41)
                    px(k, k, k * 1.02f)
                }
                else -> Color.WHITE
            }
        }
        return a
    }

    private fun rug(x: Int, y: Int, u: Float, v: Float): Int {
        val dx = abs(u - 0.5f)
        val dy = abs(v - 0.5f)
        val d = max(dx, dy) * 2f
        val man = (dx + dy) * 2f
        var r: Float; var g: Float; var b: Float
        if (d > 0.90f) { r = 0.62f; g = 0.16f; b = 0.18f }
        else if (d > 0.86f) { r = 0.90f; g = 0.72f; b = 0.34f }
        else if (d > 0.78f) { r = 0.96f; g = 0.90f; b = 0.78f }
        else if (d > 0.74f) { r = 0.62f; g = 0.16f; b = 0.18f }
        else {
            r = 0.78f; g = 0.30f; b = 0.28f
            if (man in 0.62f..0.68f) { r = 0.96f; g = 0.90f; b = 0.78f }
            if (man in 0.36f..0.42f) { r = 0.96f; g = 0.90f; b = 0.78f }
            if (man < 0.16f) { r = 0.90f; g = 0.72f; b = 0.34f }
            else if (man in 0.42f..0.62f) { r = 0.30f; g = 0.38f; b = 0.55f }
            else if (man in 0.16f..0.36f) { r = 0.62f; g = 0.16f; b = 0.18f }
        }
        val wv = if (((x / 2 + y / 2) and 1) == 0) 1f else 0.92f
        val k = wv * (0.94f + 0.06f * Noise.h(x, y, 91))
        return px(r * k, g * k, b * k)
    }

    @Synchronized
    private fun pix(m: Int): IntArray {
        var c = cache[m]
        if (c == null) { c = gen(m); cache[m] = c }
        return c
    }

    /** Gera as texturas em segundo plano, para não travar o primeiro quadro. */
    fun pregen() {
        Thread {
            for (m in 0 until Mt.COUNT) if (m != Mt.PLAIN && m != Mt.GLASS) pix(m)
        }.start()
    }

    fun init() {
        GLES20.glGenTextures(Mt.COUNT, ids, 0)
        for (m in 0 until Mt.COUNT) {
            val small = m == Mt.PLAIN || m == Mt.GLASS
            val sz = if (small) 4 else S
            val data = if (small) IntArray(16) { Color.WHITE } else pix(m)
            val bmp = Bitmap.createBitmap(data, sz, sz, Bitmap.Config.ARGB_8888)
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, ids[m])
            GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bmp, 0)
            if (!small) GLES20.glGenerateMipmap(GLES20.GL_TEXTURE_2D)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, if (small) GLES20.GL_LINEAR else GLES20.GL_LINEAR_MIPMAP_LINEAR)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_REPEAT)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_REPEAT)
            bmp.recycle()
        }
    }
}

// ---------------------------------------------------------------- construtor de malhas

class MB {
    private class FA {
        var a = FloatArray(4096)
        var n = 0
        fun put(x: Float) {
            if (n == a.size) a = a.copyOf(n * 2)
            a[n++] = x
        }
    }

    private val bufs = HashMap<Int, FA>()
    private var cur = FA()
    private var us = 1f
    private var ux = 0f
    private var uy = 0f

    /** Opacidade aplicada aos próximos vértices (usado no vidro). */
    var al = 1f

    init { bufs[0] = cur }

    /** Escolhe o material (textura) e a escala/deslocamento do UV para o que vier a seguir. */
    fun m(mat: Int, s: Float = 1f, ox: Float = 0f, oy: Float = 0f): MB {
        us = s; ux = ox; uy = oy
        cur = bufs.getOrPut(mat) { FA() }
        return this
    }

    fun v(x: Float, y: Float, z: Float, nx: Float, ny: Float, nz: Float, c: Int, u: Float, w: Float) {
        val f = cur
        f.put(x); f.put(y); f.put(z); f.put(nx); f.put(ny); f.put(nz)
        f.put(Color.red(c) / 255f); f.put(Color.green(c) / 255f); f.put(Color.blue(c) / 255f); f.put(al)
        f.put(u * us + ux); f.put(w * us + uy)
    }

    /** Vértice com UV projetado pelo eixo dominante da face (0=x, 1=y, 2=z). */
    private fun vp(ax: Int, x: Float, y: Float, z: Float, nx: Float, ny: Float, nz: Float, c: Int) {
        when (ax) {
            0 -> v(x, y, z, nx, ny, nz, c, z, y)
            1 -> v(x, y, z, nx, ny, nz, c, x, z)
            else -> v(x, y, z, nx, ny, nz, c, x, y)
        }
    }

    private fun quad(ax: Int, p: FloatArray, nx: Float, ny: Float, nz: Float, c: Int) {
        for (i in intArrayOf(0, 1, 2, 0, 2, 3)) vp(ax, p[i * 3], p[i * 3 + 1], p[i * 3 + 2], nx, ny, nz, c)
    }

    fun box(cx: Number, cy: Number, cz: Number, sx: Number, sy: Number, sz: Number, c: Int, lit: Boolean = true) {
        val x0 = cx.toFloat() - sx.toFloat() / 2f
        val x1 = cx.toFloat() + sx.toFloat() / 2f
        val y0 = cy.toFloat() - sy.toFloat() / 2f
        val y1 = cy.toFloat() + sy.toFloat() / 2f
        val z0 = cz.toFloat() - sz.toFloat() / 2f
        val z1 = cz.toFloat() + sz.toFloat() / 2f
        val l = if (lit) 1f else 0f
        quad(1, floatArrayOf(x0, y1, z0, x1, y1, z0, x1, y1, z1, x0, y1, z1), 0f, l, 0f, c)
        quad(1, floatArrayOf(x0, y0, z1, x1, y0, z1, x1, y0, z0, x0, y0, z0), 0f, -l, 0f, c)
        quad(2, floatArrayOf(x0, y0, z1, x1, y0, z1, x1, y1, z1, x0, y1, z1), 0f, 0f, l, c)
        quad(2, floatArrayOf(x1, y0, z0, x0, y0, z0, x0, y1, z0, x1, y1, z0), 0f, 0f, -l, c)
        quad(0, floatArrayOf(x1, y0, z1, x1, y0, z0, x1, y1, z0, x1, y1, z1), l, 0f, 0f, c)
        quad(0, floatArrayOf(x0, y0, z0, x0, y0, z1, x0, y1, z1, x0, y1, z0), -l, 0f, 0f, c)
    }

    private fun axisPos(h: Float, r: Float, bv: Int): FloatArray {
        val l = FloatArray(2 * (bv + 1))
        for (k in 0..bv) {
            l[k] = -h + r * k / bv
            l[bv + 1 + k] = h - r + r * k / bv
        }
        return l
    }

    /** Caixa com quinas arredondadas (bevel suave, normais contínuas). */
    fun rbox(cx: Number, cy: Number, cz: Number, sx: Number, sy: Number, sz: Number, rr: Number, c: Int, lit: Boolean = true, bv: Int = 2) {
        val hx = sx.toFloat() / 2f
        val hy = sy.toFloat() / 2f
        val hz = sz.toFloat() / 2f
        val r = min(rr.toFloat(), min(hx, min(hy, hz)) * 0.98f)
        if (r < 0.004f) { box(cx, cy, cz, sx, sy, sz, c, lit); return }
        val h = floatArrayOf(hx, hy, hz)
        val b = floatArrayOf(hx - r, hy - r, hz - r)
        val pos = Array(3) { axisPos(h[it], r, bv) }
        val o = floatArrayOf(cx.toFloat(), cy.toFloat(), cz.toFloat())
        val p = FloatArray(3)
        val idx = intArrayOf(0, 1, 2, 0, 2, 3)
        val cu = FloatArray(4)
        val cv = FloatArray(4)
        for (a in 0..2) for (s in intArrayOf(-1, 1)) {
            val ua = (a + 1) % 3
            val va = (a + 2) % 3
            val pu = pos[ua]
            val pv = pos[va]
            for (i in 0 until pu.size - 1) for (j in 0 until pv.size - 1) {
                cu[0] = pu[i]; cu[1] = pu[i + 1]; cu[2] = pu[i + 1]; cu[3] = pu[i]
                cv[0] = pv[j]; cv[1] = pv[j]; cv[2] = pv[j + 1]; cv[3] = pv[j + 1]
                for (k in idx) {
                    p[a] = s * h[a]; p[ua] = cu[k]; p[va] = cv[k]
                    val ix = p[0].coerceIn(-b[0], b[0])
                    val iy = p[1].coerceIn(-b[1], b[1])
                    val iz = p[2].coerceIn(-b[2], b[2])
                    var dx = p[0] - ix
                    var dy = p[1] - iy
                    var dz = p[2] - iz
                    val ln = sqrt(dx * dx + dy * dy + dz * dz)
                    if (ln < 1e-6f) {
                        dx = 0f; dy = 0f; dz = 0f
                        if (a == 0) dx = s.toFloat() else if (a == 1) dy = s.toFloat() else dz = s.toFloat()
                    } else { dx /= ln; dy /= ln; dz /= ln }
                    val wx = o[0] + ix + dx * r
                    val wy = o[1] + iy + dy * r
                    val wz = o[2] + iz + dz * r
                    val l = if (lit) 1f else 0f
                    vp(a, wx, wy, wz, dx * l, dy * l, dz * l, c)
                }
            }
        }
    }

    fun tube(cx: Number, by: Number, cz: Number, r: Number, h: Number, c: Int, lit: Boolean = true) =
        cyl(cx, by, cz, r, r, h, c, lit)

    /** Cilindro/cone vertical: r1 embaixo, r2 em cima. */
    fun cyl(cx: Number, by: Number, cz: Number, r1: Number, r2: Number, h: Number, c: Int, lit: Boolean = true, seg: Int = 20) {
        val x = cx.toFloat(); val y = by.toFloat(); val z = cz.toFloat()
        val ra = r1.toFloat(); val rb = r2.toFloat(); val hh = h.toFloat()
        val sl = (ra - rb) / hh
        val l = if (lit) 1f else 0f
        val inv = l / sqrt(1f + sl * sl)
        val tp = 2f * PI.toFloat()
        val circ = tp * (ra + rb) / 2f
        for (i in 0 until seg) {
            val a0 = tp * i / seg
            val a1 = tp * (i + 1) / seg
            val c0 = cos(a0); val s0 = sin(a0); val c1 = cos(a1); val s1 = sin(a1)
            val u0 = circ * i / seg
            val u1 = circ * (i + 1) / seg
            v(x + ra * c0, y, z + ra * s0, c0 * inv, sl * inv, s0 * inv, c, u0, 0f)
            v(x + ra * c1, y, z + ra * s1, c1 * inv, sl * inv, s1 * inv, c, u1, 0f)
            v(x + rb * c1, y + hh, z + rb * s1, c1 * inv, sl * inv, s1 * inv, c, u1, hh)
            v(x + ra * c0, y, z + ra * s0, c0 * inv, sl * inv, s0 * inv, c, u0, 0f)
            v(x + rb * c1, y + hh, z + rb * s1, c1 * inv, sl * inv, s1 * inv, c, u1, hh)
            v(x + rb * c0, y + hh, z + rb * s0, c0 * inv, sl * inv, s0 * inv, c, u0, hh)
            if (rb > 0f) {
                v(x, y + hh, z, 0f, l, 0f, c, x, z)
                v(x + rb * c0, y + hh, z + rb * s0, 0f, l, 0f, c, x + rb * c0, z + rb * s0)
                v(x + rb * c1, y + hh, z + rb * s1, 0f, l, 0f, c, x + rb * c1, z + rb * s1)
            }
            if (ra > 0f) {
                v(x, y, z, 0f, -l, 0f, c, x, z)
                v(x + ra * c1, y, z + ra * s1, 0f, -l, 0f, c, x + ra * c1, z + ra * s1)
                v(x + ra * c0, y, z + ra * s0, 0f, -l, 0f, c, x + ra * c0, z + ra * s0)
            }
        }
    }

    /** Sólido de revolução: prof = [raio0, y0, raio1, y1, ...]. Normais suaves. */
    fun lathe(cx: Number, by: Number, cz: Number, prof: FloatArray, c: Int, lit: Boolean = true, seg: Int = 24) {
        val x = cx.toFloat(); val y = by.toFloat(); val z = cz.toFloat()
        val n = prof.size / 2
        if (n < 2) return
        val nr = FloatArray(n)
        val ny = FloatArray(n)
        val sr = FloatArray(n - 1)
        val sy = FloatArray(n - 1)
        for (i in 0 until n - 1) {
            val dr = prof[(i + 1) * 2] - prof[i * 2]
            val dy = prof[(i + 1) * 2 + 1] - prof[i * 2 + 1]
            val ln = max(sqrt(dr * dr + dy * dy), 1e-6f)
            sr[i] = dy / ln; sy[i] = -dr / ln
        }
        for (i in 0 until n) {
            var a = 0f; var b = 0f
            if (i > 0) { a += sr[i - 1]; b += sy[i - 1] }
            if (i < n - 1) { a += sr[i]; b += sy[i] }
            val ln = max(sqrt(a * a + b * b), 1e-6f)
            nr[i] = a / ln; ny[i] = b / ln
        }
        val l = if (lit) 1f else 0f
        val tp = 2f * PI.toFloat()
        for (j in 0 until seg) {
            val a0 = tp * j / seg
            val a1 = tp * (j + 1) / seg
            val c0 = cos(a0); val s0 = sin(a0); val c1 = cos(a1); val s1 = sin(a1)
            val u0 = a0 * 0.25f
            val u1 = a1 * 0.25f
            for (i in 0 until n - 1) {
                val r0 = prof[i * 2]; val y0 = prof[i * 2 + 1]
                val r1 = prof[(i + 1) * 2]; val y1 = prof[(i + 1) * 2 + 1]
                v(x + r0 * c0, y + y0, z + r0 * s0, nr[i] * c0 * l, ny[i] * l, nr[i] * s0 * l, c, u0, y0)
                v(x + r0 * c1, y + y0, z + r0 * s1, nr[i] * c1 * l, ny[i] * l, nr[i] * s1 * l, c, u1, y0)
                v(x + r1 * c1, y + y1, z + r1 * s1, nr[i + 1] * c1 * l, ny[i + 1] * l, nr[i + 1] * s1 * l, c, u1, y1)
                v(x + r0 * c0, y + y0, z + r0 * s0, nr[i] * c0 * l, ny[i] * l, nr[i] * s0 * l, c, u0, y0)
                v(x + r1 * c1, y + y1, z + r1 * s1, nr[i + 1] * c1 * l, ny[i + 1] * l, nr[i + 1] * s1 * l, c, u1, y1)
                v(x + r1 * c0, y + y1, z + r1 * s0, nr[i + 1] * c0 * l, ny[i + 1] * l, nr[i + 1] * s0 * l, c, u0, y1)
            }
        }
    }

    fun sphere(cx: Number, cy: Number, cz: Number, r: Number, c: Int, ry: Number = r, seg: Int = 10, lit: Boolean = true) {
        val x = cx.toFloat(); val y = cy.toFloat(); val z = cz.toFloat()
        val rr = r.toFloat(); val rv = ry.toFloat()
        val lon = seg * 2
        val pi = PI.toFloat()
        val l = if (lit) 1f else 0f
        for (i in 0 until seg) {
            val t0 = pi * i / seg
            val t1 = pi * (i + 1) / seg
            for (j in 0 until lon) {
                val p0 = 2f * pi * j / lon
                val p1 = 2f * pi * (j + 1) / lon
                fun pt(t: Float, p: Float) {
                    val nx = sin(t) * cos(p); val nyy = cos(t); val nz = sin(t) * sin(p)
                    // normal corrigida para esferóides achatados
                    var ax = nx / rr; var ay = nyy / rv; var az = nz / rr
                    val ln = max(sqrt(ax * ax + ay * ay + az * az), 1e-6f)
                    ax /= ln; ay /= ln; az /= ln
                    v(x + rr * nx, y + rv * nyy, z + rr * nz, ax * l, ay * l, az * l, c, p * rr, t * rv)
                }
                pt(t0, p0); pt(t1, p0); pt(t1, p1)
                pt(t0, p0); pt(t1, p1); pt(t0, p1)
            }
        }
    }

    /** Plano horizontal (normal para cima, ou para baixo se flip). */
    fun plane(x0: Number, z0: Number, x1: Number, z1: Number, y: Number, c: Int, lit: Boolean = true, flip: Boolean = false) {
        val a = x0.toFloat(); val b = z0.toFloat(); val d = x1.toFloat(); val e = z1.toFloat(); val yy = y.toFloat()
        val ny = if (!lit) 0f else if (flip) -1f else 1f
        quad(1, floatArrayOf(a, yy, b, d, yy, b, d, yy, e, a, yy, e), 0f, ny, 0f, c)
    }

    /** Retângulo vertical (virado para +z) com gradiente, sem luz. */
    fun gradQuadZ(x0: Number, x1: Number, y0: Number, y1: Number, z: Number, cBot: Int, cTop: Int) {
        val a = x0.toFloat(); val b = x1.toFloat(); val c0 = y0.toFloat(); val c1 = y1.toFloat(); val zz = z.toFloat()
        v(a, c0, zz, 0f, 0f, 0f, cBot, a, c0); v(b, c0, zz, 0f, 0f, 0f, cBot, b, c0); v(b, c1, zz, 0f, 0f, 0f, cTop, b, c1)
        v(a, c0, zz, 0f, 0f, 0f, cBot, a, c0); v(b, c1, zz, 0f, 0f, 0f, cTop, b, c1); v(a, c1, zz, 0f, 0f, 0f, cTop, a, c1)
    }

    /** Vértice solto sem luz com cor própria (céu). */
    fun raw(x: Float, y: Float, z: Float, c: Int) = v(x, y, z, 0f, 0f, 0f, c, 0f, 0f)

    /** Sombra suave com gradiente radial. */
    fun blob(cx: Number, y: Number, cz: Number, rx: Number, rz: Number, alpha: Float) {
        val x = cx.toFloat(); val yy = y.toFloat(); val z = cz.toFloat()
        val ax = rx.toFloat(); val az = rz.toFloat()
        val seg = 28
        val tp = 2f * PI.toFloat()
        val fs = floatArrayOf(0f, 0.5f, 0.78f, 1f)
        val al2 = floatArrayOf(alpha, alpha * 0.65f, alpha * 0.25f, 0f)
        val old = al
        fun pt(f: Float, a: Float, aa: Float) {
            al = aa
            val cc = cos(a); val ss = sin(a)
            v(x + f * ax * sign(cc) * sqrt(abs(cc)), yy, z + f * az * sign(ss) * sqrt(abs(ss)), 0f, 0f, 0f, Color.BLACK, 0f, 0f)
        }
        for (k in 0 until 3) for (i in 0 until seg) {
            val a0 = tp * i / seg
            val a1 = tp * (i + 1) / seg
            pt(fs[k], a0, al2[k]); pt(fs[k + 1], a0, al2[k + 1]); pt(fs[k + 1], a1, al2[k + 1])
            pt(fs[k], a0, al2[k]); pt(fs[k + 1], a1, al2[k + 1]); pt(fs[k], a1, al2[k])
        }
        al = old
    }

    fun toMesh(): Mesh {
        val parts = ArrayList<Part>()
        for ((mat, f) in bufs) {
            if (f.n == 0) continue
            val bb = ByteBuffer.allocateDirect(f.n * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
            bb.put(f.a, 0, f.n)
            bb.position(0)
            parts.add(Part(mat, bb, f.n / STRIDE))
        }
        return Mesh(parts)
    }
}
