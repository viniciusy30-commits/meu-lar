package com.vinicius.meular

import android.opengl.GLES20
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Cidade 6, à noite: feixes do farol girando (dois fachos opostos, como os faróis de verdade, uma volta a cada 12 s),
 * o brilho da lanterna (mais forte quando o facho aponta para quem olha) e o farolete verde piscando a cada 3 s.
 * Lê as luzes do c6.json (tipo "farol" e "farolete"). Programa próprio, mistura aditiva, poucos triângulos.
 */
object Beacon {
    private class L(val x: Float, val y: Float, val z: Float, val r: Float, val g: Float, val b: Float, val farol: Boolean, val per: Float)
    private var lights: List<L>? = null
    private var srcKey = ""
    private var prog = 0; private var pgen = -1
    private var aPos = 0; private var aA = 0; private var uVP = 0; private var uCol = 0
    private val buf: FloatBuffer = ByteBuffer.allocateDirect(4 * 4 * 600).order(ByteOrder.nativeOrder()).asFloatBuffer()
    private val t0 = System.nanoTime()

    private const val VS = "attribute vec3 aPos; attribute float aA; uniform mat4 uVP; varying float vA; void main(){ vA = aA; gl_Position = uVP * vec4(aPos, 1.0); }"
    private const val FS = "precision mediump float; varying float vA; uniform vec3 uCol; void main(){ gl_FragColor = vec4(uCol * vA, vA); }"

    private fun parse() {
        val s = Relevo.luzesJ
        if (s == srcKey && lights != null) return
        srcKey = s
        val out = ArrayList<L>()
        try {
            val a = org.json.JSONArray(s)
            for (i in 0 until a.length()) {
                val o = a.getJSONObject(i)
                val tp = o.optString("tipo")
                if (tp != "farol" && tp != "farolete") continue
                val c = o.optJSONArray("cor")
                out.add(L(o.getDouble("x").toFloat() + Relevo.CX, o.getDouble("y").toFloat() + 0.7f, o.getDouble("z").toFloat() + Relevo.CZ,
                    (c?.optDouble(0, 255.0) ?: 255.0).toFloat() / 255f, (c?.optDouble(1, 240.0) ?: 240.0).toFloat() / 255f, (c?.optDouble(2, 190.0) ?: 190.0).toFloat() / 255f,
                    tp == "farol", o.optDouble(if (tp == "farol") "giro_s" else "pisca_s", 12.0).toFloat()))
            }
        } catch (e: Throwable) { }
        lights = out
    }

    private fun build() {
        prog = GLES20.glCreateProgram()
        fun sh(t: Int, src: String): Int { val s = GLES20.glCreateShader(t); GLES20.glShaderSource(s, src); GLES20.glCompileShader(s); return s }
        GLES20.glAttachShader(prog, sh(GLES20.GL_VERTEX_SHADER, VS)); GLES20.glAttachShader(prog, sh(GLES20.GL_FRAGMENT_SHADER, FS))
        GLES20.glBindAttribLocation(prog, 0, "aPos"); GLES20.glBindAttribLocation(prog, 1, "aA")
        GLES20.glLinkProgram(prog)
        aPos = 0; aA = 1; uVP = GLES20.glGetUniformLocation(prog, "uVP"); uCol = GLES20.glGetUniformLocation(prog, "uCol")
        pgen = GlGen.gen
    }

    private fun v(x: Float, y: Float, z: Float, a: Float) { buf.put(x); buf.put(y); buf.put(z); buf.put(a) }

    /** desenha no passe transparente; [ex], [ey], [ez] = olho */
    fun draw(vp: FloatArray, ex: Float, ey: Float, ez: Float) {
        val n = DayNight.night
        if (n < 0.05f || !(City.C6 && Relevo.on)) return
        parse()
        val ls = lights ?: return
        if (ls.isEmpty()) return
        if (prog == 0 || pgen != GlGen.gen) build()
        val t = (System.nanoTime() - t0) / 1e9f
        GLES20.glUseProgram(prog)
        GLES20.glUniformMatrix4fv(uVP, 1, false, vp, 0)
        GLES20.glEnable(GLES20.GL_BLEND); GLES20.glBlendFunc(GLES20.GL_ONE, GLES20.GL_ONE)
        GLES20.glDepthMask(false)
        GLES20.glDisableVertexAttribArray(2); GLES20.glDisableVertexAttribArray(3)
        GLES20.glEnableVertexAttribArray(0); GLES20.glEnableVertexAttribArray(1)
        for (l in ls) {
            buf.clear()
            var count = 0
            // vetor para a câmera (para os brilhos virados para ela)
            var cx = ex - l.x; var cy = ey - l.y; var cz = ez - l.z
            val cl = sqrt(cx * cx + cy * cy + cz * cz).coerceAtLeast(0.01f); cx /= cl; cy /= cl; cz /= cl
            // eixos do brilho (billboard)
            var rx = cz; var rz = -cx; val rl = sqrt(rx * rx + rz * rz).coerceAtLeast(0.01f); rx /= rl; rz /= rl
            val ux = -cy * rz; val uy = cz * rx - cx * rz; val uz = cy * rx
            if (l.farol) {
                val ang = t * (2f * Math.PI.toFloat() / l.per)
                for (k in 0..1) {
                    val a = ang + k * Math.PI.toFloat()
                    val dx = cos(a); val dz = sin(a)
                    val len = 320f; val rad = 16f
                    val px = -dz; val pz = dx
                    val seg = 10
                    for (s in 0 until seg) {
                        val b0 = 2f * Math.PI.toFloat() * s / seg; val b1 = 2f * Math.PI.toFloat() * (s + 1) / seg
                        val e0x = l.x + dx * len + px * cos(b0) * rad; val e0y = l.y - 6f + sin(b0) * rad * 0.5f; val e0z = l.z + dz * len + pz * cos(b0) * rad
                        val e1x = l.x + dx * len + px * cos(b1) * rad; val e1y = l.y - 6f + sin(b1) * rad * 0.5f; val e1z = l.z + dz * len + pz * cos(b1) * rad
                        v(l.x + dx * 0.6f, l.y, l.z + dz * 0.6f, 0.30f * n); v(e0x, e0y, e0z, 0f); v(e1x, e1y, e1z, 0f); count += 3
                    }
                    // brilho forte quando o facho aponta para quem olha
                    val face = (dx * cx + dz * cz).coerceAtLeast(0f)
                    val g = (0.35f + 2.2f * face * face * face * face) * n
                    val s = 2.5f + 6f * face * face
                    v(l.x, l.y, l.z, g); v(l.x + rx * s, l.y, l.z + rz * s, 0f); v(l.x + ux * s, l.y + uy * s, l.z + uz * s, 0f)
                    v(l.x, l.y, l.z, g); v(l.x + ux * s, l.y + uy * s, l.z + uz * s, 0f); v(l.x - rx * s, l.y, l.z - rz * s, 0f)
                    v(l.x, l.y, l.z, g); v(l.x - rx * s, l.y, l.z - rz * s, 0f); v(l.x - ux * s, l.y - uy * s, l.z - uz * s, 0f)
                    v(l.x, l.y, l.z, g); v(l.x - ux * s, l.y - uy * s, l.z - uz * s, 0f); v(l.x + rx * s, l.y, l.z + rz * s, 0f)
                    count += 12
                }
            } else {
                // farolete: lampejo de 0,6 s a cada período
                val ph = (t % l.per) / l.per
                val on = if (ph < 0.2f) sin(ph / 0.2f * Math.PI.toFloat()) else 0f
                val g = (0.15f + 1.4f * on) * n; val s = 1.5f + 3f * on
                v(l.x, l.y, l.z, g); v(l.x + rx * s, l.y, l.z + rz * s, 0f); v(l.x + ux * s, l.y + uy * s, l.z + uz * s, 0f)
                v(l.x, l.y, l.z, g); v(l.x + ux * s, l.y + uy * s, l.z + uz * s, 0f); v(l.x - rx * s, l.y, l.z - rz * s, 0f)
                v(l.x, l.y, l.z, g); v(l.x - rx * s, l.y, l.z - rz * s, 0f); v(l.x - ux * s, l.y - uy * s, l.z - uz * s, 0f)
                v(l.x, l.y, l.z, g); v(l.x - ux * s, l.y - uy * s, l.z - uz * s, 0f); v(l.x + rx * s, l.y, l.z + rz * s, 0f)
                count += 12
            }
            buf.position(0)
            GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, 0)
            GLES20.glVertexAttribPointer(0, 3, GLES20.GL_FLOAT, false, 16, buf)
            buf.position(3)
            GLES20.glVertexAttribPointer(1, 1, GLES20.GL_FLOAT, false, 16, buf)
            GLES20.glUniform3f(uCol, l.r, l.g, l.b)
            GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, count)
        }
        GLES20.glDepthMask(true)
        GLES20.glBlendFunc(GLES20.GL_SRC_ALPHA, GLES20.GL_ONE_MINUS_SRC_ALPHA)
        GLES20.glEnableVertexAttribArray(2); GLES20.glEnableVertexAttribArray(3)
    }
}
