package com.vinicius.meular

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.sin
import kotlin.math.sqrt

/** Elipsoide liso (normais corretas) com rotação opcional em X e Z. Base do visual fofinho. */
fun MB.ell(
    cx: Double, cy: Double, cz: Double,
    rx: Double, ry: Double, rz: Double,
    c: Int, seg: Int = 16, lit: Boolean = true,
    rotZ: Double = 0.0, rotX: Double = 0.0
) {
    val l = if (lit) 1f else 0f
    val czr = cos(rotZ).toFloat(); val szr = sin(rotZ).toFloat()
    val cxr = cos(rotX).toFloat(); val sxr = sin(rotX).toFloat()
    val lon = seg * 2
    val pi = PI.toFloat()
    val fx = cx.toFloat(); val fy = cy.toFloat(); val fz = cz.toFloat()
    fun pt(t: Float, p: Float) {
        val ux = sin(t) * cos(p); val uy = cos(t); val uz = sin(t) * sin(p)
        var px = rx.toFloat() * ux; var py = ry.toFloat() * uy; var pz = rz.toFloat() * uz
        var nx = ux / rx.toFloat(); var ny = uy / ry.toFloat(); var nz = uz / rz.toFloat()
        val ln = max(sqrt(nx * nx + ny * ny + nz * nz), 1e-6f)
        nx /= ln; ny /= ln; nz /= ln
        // rotação em X
        var t1 = py * cxr - pz * sxr; var t2 = py * sxr + pz * cxr; py = t1; pz = t2
        t1 = ny * cxr - nz * sxr; t2 = ny * sxr + nz * cxr; ny = t1; nz = t2
        // rotação em Z
        t1 = px * czr - py * szr; t2 = px * szr + py * czr; px = t1; py = t2
        t1 = nx * czr - ny * szr; t2 = nx * szr + ny * czr; nx = t1; ny = t2
        v(fx + px, fy + py, fz + pz, nx * l, ny * l, nz * l, c, p, t)
    }
    for (i in 0 until seg) {
        val t0 = pi * i / seg
        val t1 = pi * (i + 1) / seg
        for (j in 0 until lon) {
            val p0 = 2f * pi * j / lon
            val p1 = 2f * pi * (j + 1) / lon
            pt(t0, p0); pt(t1, p0); pt(t1, p1)
            pt(t0, p0); pt(t1, p1); pt(t0, p1)
        }
    }
}

/** Membro arredondado (cápsula cônica) entre dois pontos: braços, pernas, mechas. */
fun MB.limb(
    x0: Double, y0: Double, z0: Double,
    x1: Double, y1: Double, z1: Double,
    r0: Double, r1: Double, c: Int, seg: Int = 16, lit: Boolean = true
) {
    var ax = (x1 - x0).toFloat(); var ay = (y1 - y0).toFloat(); var az = (z1 - z0).toFloat()
    val len = max(sqrt(ax * ax + ay * ay + az * az), 1e-5f)
    ax /= len; ay /= len; az /= len
    // eixo perpendicular
    var ux: Float; var uy: Float; var uz: Float
    if (abs(ay) < 0.9f) { ux = az; uy = 0f; uz = -ax } else { ux = 0f; uy = -az; uz = ay }
    val ul = max(sqrt(ux * ux + uy * uy + uz * uz), 1e-6f)
    ux /= ul; uy /= ul; uz /= ul
    val wx = ay * uz - az * uy; val wy = az * ux - ax * uz; val wz = ax * uy - ay * ux
    val steps = 6
    val n = (steps + 1) * 2
    val rad = FloatArray(n); val pos = FloatArray(n); val nr = FloatArray(n); val na = FloatArray(n)
    val half = (PI / 2.0).toFloat()
    for (k in 0..steps) {
        val an = -half + half * k / steps
        rad[k] = (r0 * cos(an)).toFloat(); pos[k] = (r0 * sin(an)).toFloat()
        nr[k] = cos(an); na[k] = sin(an)
        val an2 = half * k / steps
        rad[steps + 1 + k] = (r1 * cos(an2)).toFloat(); pos[steps + 1 + k] = len + (r1 * sin(an2)).toFloat()
        nr[steps + 1 + k] = cos(an2); na[steps + 1 + k] = sin(an2)
    }
    val l = if (lit) 1f else 0f
    val bx = x0.toFloat(); val by = y0.toFloat(); val bz = z0.toFloat()
    val tp = 2f * PI.toFloat()
    fun vx(i: Int, ca: Float, sa: Float) {
        val dx = ux * ca + wx * sa; val dy = uy * ca + wy * sa; val dz = uz * ca + wz * sa
        v(
            bx + ax * pos[i] + dx * rad[i], by + ay * pos[i] + dy * rad[i], bz + az * pos[i] + dz * rad[i],
            (dx * nr[i] + ax * na[i]) * l, (dy * nr[i] + ay * na[i]) * l, (dz * nr[i] + az * na[i]) * l,
            c, ca, pos[i]
        )
    }
    for (j in 0 until seg) {
        val a0 = tp * j / seg; val a1 = tp * (j + 1) / seg
        val c0 = cos(a0); val s0 = sin(a0); val c1 = cos(a1); val s1 = sin(a1)
        for (i in 0 until n - 1) {
            vx(i, c0, s0); vx(i, c1, s1); vx(i + 1, c1, s1)
            vx(i, c0, s0); vx(i + 1, c1, s1); vx(i + 1, c0, s0)
        }
    }
}
