package com.vinicius.meular

import android.graphics.Color
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.sign
import kotlin.math.sin
import kotlin.math.sqrt

class Mesh(val buf: FloatBuffer, val count: Int)

fun C(s: String): Int = Color.parseColor(s)

fun shade(c: Int, d: Int): Int {
    fun k(v: Int) = (v + d).coerceIn(0, 255)
    return Color.rgb(k(Color.red(c)), k(Color.green(c)), k(Color.blue(c)))
}

/** Construtor de malhas: posição(3) normal(3) cor(4). Normal zero = sem iluminação. */
class MB {
    private var a = FloatArray(8192)
    private var n = 0

    private fun put(x: Float) {
        if (n == a.size) a = a.copyOf(n * 2)
        a[n++] = x
    }

    fun v(x: Float, y: Float, z: Float, nx: Float, ny: Float, nz: Float, c: Int, al: Float = 1f) {
        put(x); put(y); put(z); put(nx); put(ny); put(nz)
        put(Color.red(c) / 255f); put(Color.green(c) / 255f); put(Color.blue(c) / 255f); put(al)
    }

    private fun quad(p: FloatArray, nx: Float, ny: Float, nz: Float, c: Int) {
        for (i in intArrayOf(0, 1, 2, 0, 2, 3)) v(p[i * 3], p[i * 3 + 1], p[i * 3 + 2], nx, ny, nz, c)
    }

    fun box(cx: Number, cy: Number, cz: Number, sx: Number, sy: Number, sz: Number, c: Int, lit: Boolean = true) {
        val x0 = cx.toFloat() - sx.toFloat() / 2f
        val x1 = cx.toFloat() + sx.toFloat() / 2f
        val y0 = cy.toFloat() - sy.toFloat() / 2f
        val y1 = cy.toFloat() + sy.toFloat() / 2f
        val z0 = cz.toFloat() - sz.toFloat() / 2f
        val z1 = cz.toFloat() + sz.toFloat() / 2f
        val l = if (lit) 1f else 0f
        quad(floatArrayOf(x0, y1, z0, x1, y1, z0, x1, y1, z1, x0, y1, z1), 0f, l, 0f, c)
        quad(floatArrayOf(x0, y0, z1, x1, y0, z1, x1, y1, z1, x0, y1, z1), 0f, 0f, l, c)
        quad(floatArrayOf(x1, y0, z0, x0, y0, z0, x0, y1, z0, x1, y1, z0), 0f, 0f, -l, c)
        quad(floatArrayOf(x1, y0, z1, x1, y0, z0, x1, y1, z0, x1, y1, z1), l, 0f, 0f, c)
        quad(floatArrayOf(x0, y0, z0, x0, y0, z1, x0, y1, z1, x0, y1, z0), -l, 0f, 0f, c)
    }

    fun tube(cx: Number, by: Number, cz: Number, r: Number, h: Number, c: Int, lit: Boolean = true) =
        cyl(cx, by, cz, r, r, h, c, lit)

    fun cyl(cx: Number, by: Number, cz: Number, r1: Number, r2: Number, h: Number, c: Int, lit: Boolean = true, seg: Int = 18) {
        val x = cx.toFloat(); val y = by.toFloat(); val z = cz.toFloat()
        val ra = r1.toFloat(); val rb = r2.toFloat(); val hh = h.toFloat()
        val sl = (ra - rb) / hh
        val l = if (lit) 1f else 0f
        val inv = l / sqrt(1f + sl * sl)
        val tp = 2f * PI.toFloat()
        for (i in 0 until seg) {
            val a0 = tp * i / seg
            val a1 = tp * (i + 1) / seg
            val c0 = cos(a0); val s0 = sin(a0); val c1 = cos(a1); val s1 = sin(a1)
            v(x + ra * c0, y, z + ra * s0, c0 * inv, sl * inv, s0 * inv, c)
            v(x + ra * c1, y, z + ra * s1, c1 * inv, sl * inv, s1 * inv, c)
            v(x + rb * c1, y + hh, z + rb * s1, c1 * inv, sl * inv, s1 * inv, c)
            v(x + ra * c0, y, z + ra * s0, c0 * inv, sl * inv, s0 * inv, c)
            v(x + rb * c1, y + hh, z + rb * s1, c1 * inv, sl * inv, s1 * inv, c)
            v(x + rb * c0, y + hh, z + rb * s0, c0 * inv, sl * inv, s0 * inv, c)
            if (rb > 0f) {
                v(x, y + hh, z, 0f, l, 0f, c)
                v(x + rb * c0, y + hh, z + rb * s0, 0f, l, 0f, c)
                v(x + rb * c1, y + hh, z + rb * s1, 0f, l, 0f, c)
            }
        }
    }

    fun sphere(cx: Number, cy: Number, cz: Number, r: Number, c: Int, ry: Number = r, seg: Int = 10) {
        val x = cx.toFloat(); val y = cy.toFloat(); val z = cz.toFloat()
        val rr = r.toFloat(); val rv = ry.toFloat()
        val lon = seg * 2
        val pi = PI.toFloat()
        for (i in 0 until seg) {
            val t0 = pi * i / seg
            val t1 = pi * (i + 1) / seg
            for (j in 0 until lon) {
                val p0 = 2f * pi * j / lon
                val p1 = 2f * pi * (j + 1) / lon
                fun pt(t: Float, p: Float) {
                    v(x + rr * sin(t) * cos(p), y + rv * cos(t), z + rr * sin(t) * sin(p),
                        sin(t) * cos(p), cos(t), sin(t) * sin(p), c)
                }
                pt(t0, p0); pt(t1, p0); pt(t1, p1)
                pt(t0, p0); pt(t1, p1); pt(t0, p1)
            }
        }
    }

    /** Sombra suave (superelipse com borda transparente). */
    fun blob(cx: Number, y: Number, cz: Number, rx: Number, rz: Number, al: Float) {
        val x = cx.toFloat(); val yy = y.toFloat(); val z = cz.toFloat()
        val ax = rx.toFloat(); val az = rz.toFloat()
        val seg = 28
        val tp = 2f * PI.toFloat()
        fun pt(a: Float) {
            val cc = cos(a); val ss = sin(a)
            v(x + ax * sign(cc) * sqrt(abs(cc)), yy, z + az * sign(ss) * sqrt(abs(ss)), 0f, 0f, 0f, Color.BLACK, 0f)
        }
        for (i in 0 until seg) {
            v(x, yy, z, 0f, 0f, 0f, Color.BLACK, al)
            pt(tp * i / seg)
            pt(tp * (i + 1) / seg)
        }
    }

    fun toMesh(): Mesh {
        val bb = ByteBuffer.allocateDirect(n * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
        bb.put(a, 0, n)
        bb.position(0)
        return Mesh(bb, n / 10)
    }
}
