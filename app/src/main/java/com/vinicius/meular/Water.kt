package com.vinicius.meular

import android.opengl.GLES20
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.nio.ShortBuffer

/**
 * Etapa 120: água da piscina com programa próprio.
 * - Superfície em malha (40 × 50) com ondas suaves no vertex shader.
 * - Ondinhas em anel saindo de onde o personagem mexe na água (mergulho, nado, entrar pela borda).
 * - Fresnel (de cima vê o fundo, de lado reflete o céu), brilho do sol, cáusticas falsas no fundo
 *   (o raio do olho até o fundo da piscina) e cor que escurece com a profundidade vista.
 * Substitui o plano de vidro da Etapa 118.
 */
object Water {
    private const val NX = 30
    private const val NZ = 38
    private const val NRIP = 8

    private var prog = 0
    private var gen = -1
    private var vbo = 0
    private var ibo = 0
    private var icount = 0
    private var uVP = 0; private var uEye = 0; private var uTime = 0; private var uBox = 0; private var uRip = 0; private var uDepth = 0; private var uWav = 0; private var uShore = 0
    private var seaVbo = 0; private var seaIbo = 0; private var seaCount = 0; private var seaKey = ""
    private val zeroRip = FloatArray(NRIP * 4)

    private val rip = FloatArray(NRIP * 4)   // x, z, início (s), força
    private var ripN = 0
    private val t0 = System.nanoTime()

    private fun now(): Float = ((System.nanoTime() - t0) / 1_000_000L % 600_000L) / 1000f

    /** Nova ondinha em anel no ponto (x, z) do mundo. [strength] 0..1 (1 = mergulho). */
    fun ripple(x: Float, z: Float, strength: Float) {
        synchronized(rip) {
            val i = (ripN % NRIP) * 4
            rip[i] = x; rip[i + 1] = z; rip[i + 2] = now(); rip[i + 3] = strength
            ripN++
        }
    }

    // Etapa 121: altura e inclinação calculadas juntas (derivada analítica) — antes cada vértice
    // somava as ondas e as 8 ondinhas 3 vezes; o fragment shader usa precisão média e cáusticas mais baratas.
    private val VS = """
        attribute vec2 aXZ;
        uniform mat4 uVP; uniform float uTime; uniform vec4 uBox; uniform vec4 uRip[$NRIP]; uniform vec3 uWav;   // y da água, amplitude, frequência
        varying vec3 vW; varying vec3 vN; varying float vFoam;
        void main() {
            vec2 p = aXZ;
            float t = uTime;
            vec2 q = p * uWav.z;
            float e = smoothstep(0.0, 0.25, min(min(p.x - uBox.x, uBox.z - p.x), min(p.y - uBox.y, uBox.w - p.y)));
            float a1 = q.x * 1.7 + t * 1.3; float a2 = q.y * 2.3 - t * 1.1; float a3 = (q.x + q.y) * 3.9 + t * 2.1; float a4 = (q.x - q.y) * 6.1 - t * 2.7;
            float h = 0.010 * sin(a1) + 0.008 * sin(a2) + 0.005 * sin(a3) + 0.003 * sin(a4);
            vec2 g = vec2(0.017 * cos(a1) + 0.0195 * cos(a3) + 0.0183 * cos(a4),
                          0.0184 * cos(a2) + 0.0195 * cos(a3) - 0.0183 * cos(a4));
            float foam = 0.0;
            for (int i = 0; i < $NRIP; i++) {
                vec4 r = uRip[i];
                float age = t - r.z;
                if (age < 0.0 || age > 3.0 || r.w <= 0.0) continue;
                vec2 dv = p - r.xy;
                float d = length(dv) + 0.0001;
                float x = d - age * 1.25;
                float env = exp(-x * x * 9.0) * (1.0 - age / 3.0) * r.w / (1.0 + d * 1.5);
                h += 0.05 * env * cos(x * 16.0);
                g += (-0.8 * env * sin(x * 16.0)) * (dv / d);
                foam += env * smoothstep(0.6, 0.0, age);
            }
            h *= uWav.y; g *= uWav.y * uWav.z;
            h *= e; g *= e;
            vN = normalize(vec3(-g.x, 1.0, -g.y));
            vFoam = foam;
            vW = vec3(p.x, uWav.x + h, p.y);
            gl_Position = uVP * vec4(vW, 1.0);
        }
    """.trimIndent()

    private val FS = """
        precision mediump float;
        varying vec3 vW; varying vec3 vN; varying float vFoam;
        uniform vec3 uEye; uniform float uTime; uniform vec4 uBox; uniform float uDepth; uniform vec2 uShore;   // largura da espuma, praia (0/1)
        void main() {
            vec3 n = normalize(vN);
            vec3 V = normalize(uEye - vW);
            float cosv = clamp(dot(n, V), 0.0, 1.0);
            float f1 = 1.0 - cosv; float f2 = f1 * f1;
            float fres = 0.04 + 0.96 * f2 * f2 * f1;
            vec3 R = refract(-V, n, 0.75);
            float dd = uDepth / max(-R.y, 0.15);
            vec3 hit = vW + R * dd;
            vec2 hp = clamp(hit.xz, uBox.xy, uBox.zw);
            float path = dd - length(hit.xz - hp);
            float k = 1.0 - exp(-path * 0.55);
            k = mix(k, k * smoothstep(0.0, 28.0, vW.z - uBox.y), uShore.y);
            vec3 body = mix(vec3(0.45, 0.86, 0.93), vec3(0.06, 0.42, 0.66), k);
            vec2 q = hp * 2.2; float t = uTime;
            float c = 1.0 - abs(sin(q.x + sin(q.y * 1.3 + t * 0.9) * 1.4 + t * 0.7) + sin(q.y * 1.1 + sin(q.x * 1.7 - t * 0.8) * 1.2 - t * 0.6)) * 0.5;
            c = clamp(c, 0.0, 1.0); c = c * c; c = c * c * c;
            body += vec3(0.9, 1.0, 1.0) * c * 0.35 * (1.0 - k * 0.6);
            vec3 Rf = reflect(-V, n);
            vec3 sky = mix(vec3(0.86, 0.93, 0.98), vec3(0.36, 0.60, 0.88), clamp(Rf.y, 0.0, 1.0));
            float sd = max(dot(Rf, vec3(0.3592, 0.7982, 0.5188)), 0.0);
            float s2 = sd * sd; float s4 = s2 * s2; float s16 = s4 * s4; s16 *= s16;
            float s256 = s16 * s16; s256 *= s256; s256 *= s256; s256 *= s256;
            float sun = s256 * 3.0 + s16 * sd * sd * 0.18;
            vec3 col = mix(body, sky, fres) + vec3(1.0, 0.97, 0.88) * sun;
            float ed = min(min(vW.x - uBox.x, uBox.z - vW.x), min(vW.z - uBox.y, uBox.w - vW.z));
            float rim = smoothstep(uShore.x, 0.0, ed) * (0.35 + uShore.y * 0.4 * (0.5 + 0.5 * sin(uTime * 1.6 + vW.x * 0.3)));
            col = mix(col, vec3(1.0), clamp(vFoam * 0.55 + rim, 0.0, 0.8));
            float a = clamp(mix(0.55, 0.92, fres) + k * 0.25 + vFoam * 0.3, 0.0, 0.96);
            vec3 fd = (vW - uEye) * 0.01;
            float fz = dot(fd, fd);
            float fog = smoothstep(0.49, 5.29, fz) * 0.85;
            col = mix(col, vec3(0.86, 0.92, 0.96), fog);
            a = mix(a, 1.0, fog);
            gl_FragColor = vec4(col, a);
        }
    """.trimIndent()

    private fun sh(type: Int, src: String): Int {
        val s = GLES20.glCreateShader(type)
        GLES20.glShaderSource(s, src)
        GLES20.glCompileShader(s)
        return s
    }

    private fun build(gw: Int) {
        val y = Pool.WATER_Y
        prog = GLES20.glCreateProgram()
        GLES20.glAttachShader(prog, sh(GLES20.GL_VERTEX_SHADER, VS))
        GLES20.glAttachShader(prog, sh(GLES20.GL_FRAGMENT_SHADER, FS))
        GLES20.glBindAttribLocation(prog, 0, "aXZ")
        GLES20.glLinkProgram(prog)
        val ok = IntArray(1)
        GLES20.glGetProgramiv(prog, GLES20.GL_LINK_STATUS, ok, 0)
        if (ok[0] == 0) { GLES20.glDeleteProgram(prog); prog = 0; return }
        uVP = GLES20.glGetUniformLocation(prog, "uVP"); uEye = GLES20.glGetUniformLocation(prog, "uEye")
        uTime = GLES20.glGetUniformLocation(prog, "uTime"); uBox = GLES20.glGetUniformLocation(prog, "uBox")
        uRip = GLES20.glGetUniformLocation(prog, "uRip"); uDepth = GLES20.glGetUniformLocation(prog, "uDepth")
        uWav = GLES20.glGetUniformLocation(prog, "uWav"); uShore = GLES20.glGetUniformLocation(prog, "uShore")

        val x0 = Pool.x0(gw); val x1 = Pool.x1(gw)
        val fb: FloatBuffer = ByteBuffer.allocateDirect((NX + 1) * (NZ + 1) * 2 * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
        for (j in 0..NZ) for (i in 0..NX) {
            fb.put(x0 + (x1 - x0) * i / NX); fb.put(Pool.Z0 + (Pool.Z1 - Pool.Z0) * j / NZ)
        }
        fb.position(0)
        icount = NX * NZ * 6
        val ib: ShortBuffer = ByteBuffer.allocateDirect(icount * 2).order(ByteOrder.nativeOrder()).asShortBuffer()
        for (j in 0 until NZ) for (i in 0 until NX) {
            val a = (j * (NX + 1) + i).toShort(); val b = (a + 1).toShort()
            val c = ((j + 1) * (NX + 1) + i).toShort(); val d = (c + 1).toShort()
            ib.put(a); ib.put(c); ib.put(b); ib.put(b); ib.put(c); ib.put(d)
        }
        ib.position(0)
        val ids = IntArray(2)
        GLES20.glGenBuffers(2, ids, 0)
        vbo = ids[0]; ibo = ids[1]
        GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, vbo)
        GLES20.glBufferData(GLES20.GL_ARRAY_BUFFER, fb.capacity() * 4, fb, GLES20.GL_STATIC_DRAW)
        GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, 0)
        GLES20.glBindBuffer(GLES20.GL_ELEMENT_ARRAY_BUFFER, ibo)
        GLES20.glBufferData(GLES20.GL_ELEMENT_ARRAY_BUFFER, icount * 2, ib, GLES20.GL_STATIC_DRAW)
        GLES20.glBindBuffer(GLES20.GL_ELEMENT_ARRAY_BUFFER, 0)
    }

    private var builtGw = -1

    /** Desenha a água (passe transparente, depth mask desligado). Devolve false se o programa não compilou. */
    fun draw(vp: FloatArray, ex: Float, ey: Float, ez: Float, gw: Int): Boolean {
        if (gen != GlGen.gen || builtGw != gw) {
            if (gen == GlGen.gen && vbo != 0) { GLES20.glDeleteBuffers(2, intArrayOf(vbo, ibo), 0); if (prog != 0) GLES20.glDeleteProgram(prog) }
            gen = GlGen.gen; builtGw = gw
            build(gw)
        }
        if (prog == 0) return false
        GLES20.glUseProgram(prog)
        GLES20.glUniformMatrix4fv(uVP, 1, false, vp, 0)
        GLES20.glUniform3f(uEye, ex, ey, ez)
        val t = now()
        GLES20.glUniform1f(uTime, t)
        GLES20.glUniform4f(uBox, Pool.x0(gw), Pool.Z0, Pool.x1(gw), Pool.Z1)
        GLES20.glUniform1f(uDepth, Pool.DEPTH + Pool.WATER_Y)
        GLES20.glUniform3f(uWav, Pool.WATER_Y, 1f, 1f)
        GLES20.glUniform2f(uShore, 0.1f, 0f)
        synchronized(rip) { GLES20.glUniform4fv(uRip, NRIP, rip, 0) }
        GLES20.glDisableVertexAttribArray(1); GLES20.glDisableVertexAttribArray(2); GLES20.glDisableVertexAttribArray(3)
        GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, vbo)
        GLES20.glVertexAttribPointer(0, 2, GLES20.GL_FLOAT, false, 8, 0)
        GLES20.glBindBuffer(GLES20.GL_ELEMENT_ARRAY_BUFFER, ibo)
        GLES20.glDrawElements(GLES20.GL_TRIANGLES, icount, GLES20.GL_UNSIGNED_SHORT, 0)
        GLES20.glBindBuffer(GLES20.GL_ELEMENT_ARRAY_BUFFER, 0)
        GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, 0)
        GLES20.glEnableVertexAttribArray(1); GLES20.glEnableVertexAttribArray(2); GLES20.glEnableVertexAttribArray(3)
        return true
    }

    /** Etapa 122: o mar. Mesma água (programa da piscina), malha grande, ondas maiores e mais largas, espuma na beira. */
    fun drawSea(vp: FloatArray, ex: Float, ey: Float, ez: Float, x0: Float, z0: Float, x1: Float, z1: Float, gw: Int): Boolean {
        if (gen != GlGen.gen || prog == 0) { if (gen != GlGen.gen || builtGw != gw) { gen = GlGen.gen; builtGw = gw; build(gw); seaKey = "" } }
        if (prog == 0) return false
        val key = "$x0|$z0|$x1|$z1|${GlGen.gen}"
        if (key != seaKey || seaVbo == 0) {
            if (seaVbo != 0) GLES20.glDeleteBuffers(2, intArrayOf(seaVbo, seaIbo), 0)
            val nx = 90; val nz = 50
            val fb = ByteBuffer.allocateDirect((nx + 1) * (nz + 1) * 2 * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
            for (j in 0..nz) {
                // linhas mais juntas perto da praia (as ondas e a espuma ficam bonitas onde se olha)
                val tz = j.toFloat() / nz
                val z = z0 + (z1 - z0) * tz * tz
                for (i in 0..nx) { fb.put(x0 + (x1 - x0) * i / nx); fb.put(z) }
            }
            fb.position(0)
            seaCount = nx * nz * 6
            val ib = ByteBuffer.allocateDirect(seaCount * 2).order(ByteOrder.nativeOrder()).asShortBuffer()
            for (j in 0 until nz) for (i in 0 until nx) {
                val a = (j * (nx + 1) + i).toShort(); val b = (a + 1).toShort()
                val c = ((j + 1) * (nx + 1) + i).toShort(); val d = (c + 1).toShort()
                ib.put(a); ib.put(c); ib.put(b); ib.put(b); ib.put(c); ib.put(d)
            }
            ib.position(0)
            val ids = IntArray(2); GLES20.glGenBuffers(2, ids, 0); seaVbo = ids[0]; seaIbo = ids[1]
            GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, seaVbo); GLES20.glBufferData(GLES20.GL_ARRAY_BUFFER, fb.capacity() * 4, fb, GLES20.GL_STATIC_DRAW); GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, 0)
            GLES20.glBindBuffer(GLES20.GL_ELEMENT_ARRAY_BUFFER, seaIbo); GLES20.glBufferData(GLES20.GL_ELEMENT_ARRAY_BUFFER, seaCount * 2, ib, GLES20.GL_STATIC_DRAW); GLES20.glBindBuffer(GLES20.GL_ELEMENT_ARRAY_BUFFER, 0)
            seaKey = key
        }
        GLES20.glUseProgram(prog)
        GLES20.glUniformMatrix4fv(uVP, 1, false, vp, 0)
        GLES20.glUniform3f(uEye, ex, ey, ez)
        GLES20.glUniform1f(uTime, now())
        GLES20.glUniform4f(uBox, x0 - 1000f, z0, x1 + 1000f, z1 + 1000f)
        GLES20.glUniform1f(uDepth, 7f)
        GLES20.glUniform3f(uWav, 0f, 7f, 0.32f)
        GLES20.glUniform2f(uShore, 1.6f, 1f)
        GLES20.glUniform4fv(uRip, NRIP, zeroRip, 0)
        GLES20.glDisableVertexAttribArray(1); GLES20.glDisableVertexAttribArray(2); GLES20.glDisableVertexAttribArray(3)
        GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, seaVbo)
        GLES20.glVertexAttribPointer(0, 2, GLES20.GL_FLOAT, false, 8, 0)
        GLES20.glBindBuffer(GLES20.GL_ELEMENT_ARRAY_BUFFER, seaIbo)
        GLES20.glDrawElements(GLES20.GL_TRIANGLES, seaCount, GLES20.GL_UNSIGNED_SHORT, 0)
        GLES20.glBindBuffer(GLES20.GL_ELEMENT_ARRAY_BUFFER, 0)
        GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, 0)
        GLES20.glEnableVertexAttribArray(1); GLES20.glEnableVertexAttribArray(2); GLES20.glEnableVertexAttribArray(3)
        return true
    }
}
