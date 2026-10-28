package com.vinicius.meular

import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.opengl.Matrix
import javax.microedition.khronos.egl.EGL10
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.egl.EGLDisplay
import javax.microedition.khronos.opengles.GL10
import kotlin.math.cos
import kotlin.math.sin

class MsaaChooser : GLSurfaceView.EGLConfigChooser {
    override fun chooseConfig(egl: EGL10, display: EGLDisplay): EGLConfig {
        for (s in intArrayOf(4, 0)) {
            val attr = intArrayOf(
                EGL10.EGL_RED_SIZE, 8, EGL10.EGL_GREEN_SIZE, 8, EGL10.EGL_BLUE_SIZE, 8,
                EGL10.EGL_ALPHA_SIZE, 8, EGL10.EGL_DEPTH_SIZE, 16,
                0x3040, 4,
                0x3032, if (s > 0) 1 else 0,
                0x3031, s,
                EGL10.EGL_NONE
            )
            val n = IntArray(1)
            val cfg = arrayOfNulls<EGLConfig>(1)
            if (egl.eglChooseConfig(display, attr, cfg, 1, n) && n[0] > 0 && cfg[0] != null) return cfg[0]!!
        }
        throw IllegalStateException("Sem configuração EGL")
    }
}

class Renderer3D(private val st: GameState) : GLSurfaceView.Renderer {
    @Volatile var yaw = 0.75f
    @Volatile var pitch = 0.8f
    @Volatile var zoom = 1f
    @Volatile var selected: Item? = null

    private val proj = FloatArray(16)
    private val view = FloatArray(16)
    private val vp = FloatArray(16)
    private val tmp = FloatArray(16)
    private val inv = FloatArray(16)
    private var invOk = false
    private val mdl = FloatArray(16)
    private val mvp = FloatArray(16)
    private var aspect = 0.75f

    private var prog = 0
    private var aPos = 0
    private var aNor = 0
    private var aCol = 0
    private var uMVP = 0
    private var uModel = 0
    private var uAlpha = 0

    private val fm = HashMap<Type, Mesh>()
    private val sm = HashMap<Int, Mesh>()
    private val rm = HashMap<Int, Mesh>()
    private var floorM: Mesh? = null
    private val walls = arrayOfNulls<Mesh>(4)
    private var bw = -1
    private var bh = -1

    private val VS = """
        attribute vec3 aPos; attribute vec3 aNor; attribute vec4 aCol;
        uniform mat4 uMVP; uniform mat4 uModel;
        varying vec4 vCol;
        void main() {
            gl_Position = uMVP * vec4(aPos, 1.0);
            float l = 1.0;
            if (length(aNor) > 0.1) {
                vec3 n = normalize((uModel * vec4(aNor, 0.0)).xyz);
                vec3 L = normalize(vec3(0.45, 1.0, 0.65));
                float d = max(dot(n, L), 0.0);
                l = 0.45 + 0.15 * n.y + 0.5 * d;
            }
            vCol = vec4(aCol.rgb * l, aCol.a);
        }
    """.trimIndent()

    private val FS = """
        precision mediump float;
        varying vec4 vCol; uniform float uAlpha;
        void main() { gl_FragColor = vec4(vCol.rgb, vCol.a * uAlpha); }
    """.trimIndent()

    private fun sh(type: Int, src: String): Int {
        val s = GLES20.glCreateShader(type)
        GLES20.glShaderSource(s, src)
        GLES20.glCompileShader(s)
        return s
    }

    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        GLES20.glClearColor(0.66f, 0.85f, 0.94f, 1f)
        GLES20.glEnable(GLES20.GL_DEPTH_TEST)
        GLES20.glEnable(GLES20.GL_BLEND)
        GLES20.glBlendFunc(GLES20.GL_SRC_ALPHA, GLES20.GL_ONE_MINUS_SRC_ALPHA)
        prog = GLES20.glCreateProgram()
        GLES20.glAttachShader(prog, sh(GLES20.GL_VERTEX_SHADER, VS))
        GLES20.glAttachShader(prog, sh(GLES20.GL_FRAGMENT_SHADER, FS))
        GLES20.glLinkProgram(prog)
        aPos = GLES20.glGetAttribLocation(prog, "aPos")
        aNor = GLES20.glGetAttribLocation(prog, "aNor")
        aCol = GLES20.glGetAttribLocation(prog, "aCol")
        uMVP = GLES20.glGetUniformLocation(prog, "uMVP")
        uModel = GLES20.glGetUniformLocation(prog, "uModel")
        uAlpha = GLES20.glGetUniformLocation(prog, "uAlpha")
        GLES20.glUseProgram(prog)
        GLES20.glEnableVertexAttribArray(aPos)
        GLES20.glEnableVertexAttribArray(aNor)
        GLES20.glEnableVertexAttribArray(aCol)
        bw = -1
    }

    override fun onSurfaceChanged(gl: GL10?, w: Int, h: Int) {
        GLES20.glViewport(0, 0, w, h)
        aspect = w.toFloat() / maxOf(1, h).toFloat()
        Matrix.perspectiveM(proj, 0, 40f, aspect, 0.1f, 150f)
    }

    private fun draw(m: Mesh, model: FloatArray, alpha: Float) {
        Matrix.multiplyMM(mvp, 0, vp, 0, model, 0)
        GLES20.glUniformMatrix4fv(uMVP, 1, false, mvp, 0)
        GLES20.glUniformMatrix4fv(uModel, 1, false, model, 0)
        GLES20.glUniform1f(uAlpha, alpha)
        m.buf.position(0)
        GLES20.glVertexAttribPointer(aPos, 3, GLES20.GL_FLOAT, false, 40, m.buf)
        m.buf.position(3)
        GLES20.glVertexAttribPointer(aNor, 3, GLES20.GL_FLOAT, false, 40, m.buf)
        m.buf.position(6)
        GLES20.glVertexAttribPointer(aCol, 4, GLES20.GL_FLOAT, false, 40, m.buf)
        GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, m.count)
    }

    private fun rebuildRoom() {
        val gw = st.gw
        val gh = st.gh
        floorM = Models.floor(gw, gh)
        walls[0] = Models.wall(gw.toDouble(), true, true)
        walls[1] = Models.wall(gw.toDouble(), false, true)
        walls[2] = Models.wall(gh.toDouble(), false, false)
        walls[3] = Models.wall(gh.toDouble(), false, false)
        bw = gw
        bh = gh
    }

    override fun onDrawFrame(gl: GL10?) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
        if (st.gw != bw || st.gh != bh) rebuildRoom()
        val gw = st.gw
        val gh = st.gh
        val cx = gw / 2f
        val cz = gh / 2f
        val dist = maxOf(gw, gh) * 2.0f / minOf(aspect, 1f) * zoom
        val ex = cx + dist * cos(pitch) * sin(yaw)
        val ey = 0.5f + dist * sin(pitch)
        val ez = cz + dist * cos(pitch) * cos(yaw)
        Matrix.setLookAtM(view, 0, ex, ey, ez, cx, 0.4f, cz, 0f, 1f, 0f)
        Matrix.multiplyMM(vp, 0, proj, 0, view, 0)
        if (Matrix.invertM(tmp, 0, vp, 0)) {
            synchronized(inv) { System.arraycopy(tmp, 0, inv, 0, 16); invOk = true }
        }

        Matrix.setIdentityM(mdl, 0)
        floorM?.let { draw(it, mdl, 1f) }
        if (ez >= cz) walls[0]?.let { draw(it, mdl, 1f) }
        if (ez < cz) {
            Matrix.setIdentityM(mdl, 0); Matrix.translateM(mdl, 0, gw.toFloat(), 0f, gh.toFloat()); Matrix.rotateM(mdl, 0, 180f, 0f, 1f, 0f)
            walls[1]?.let { draw(it, mdl, 1f) }
        }
        if (ex >= cx) {
            Matrix.setIdentityM(mdl, 0); Matrix.translateM(mdl, 0, 0f, 0f, gh.toFloat()); Matrix.rotateM(mdl, 0, 90f, 0f, 1f, 0f)
            walls[2]?.let { draw(it, mdl, 1f) }
        }
        if (ex < cx) {
            Matrix.setIdentityM(mdl, 0); Matrix.translateM(mdl, 0, gw.toFloat(), 0f, 0f); Matrix.rotateM(mdl, 0, -90f, 0f, 1f, 0f)
            walls[3]?.let { draw(it, mdl, 1f) }
        }

        val now = System.nanoTime()
        val items = st.items
        for (item in items) {
            val t = item.type
            val mesh = fm.getOrPut(t) { Models.furniture(t) }
            val age = if (item.born == 0L) 99f else (now - item.born) / 1e9f
            var s = 1f
            if (age < 0.4f) {
                val u = age / 0.4f - 1f
                s = 1f + 2.70158f * u * u * u + 1.70158f * u * u
                if (s < 0.01f) s = 0.01f
            }
            val lift = if (item === selected) 0.06f else 0f
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, item.x + item.w / 2f, lift, item.y + item.h / 2f)
            Matrix.rotateM(mdl, 0, item.rot * 90f, 0f, 1f, 0f)
            Matrix.scaleM(mdl, 0, s, s, s)
            Matrix.translateM(mdl, 0, -t.w / 2f, 0f, -t.h / 2f)
            draw(mesh, mdl, 1f)
        }

        GLES20.glDepthMask(false)
        val tt = (now / 1_000_000L % 100000L) / 1000f
        for (item in items) {
            if (item.type == Type.RUG) continue
            val key = item.w * 10 + item.h
            val sh = sm.getOrPut(key) { Models.shadow(item.w, item.h) }
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, item.x.toFloat(), 0f, item.y.toFloat())
            draw(sh, mdl, 1f)
        }
        val sel = selected
        if (sel != null) {
            val key = sel.w * 10 + sel.h
            val rg = rm.getOrPut(key) { Models.ring(sel.w, sel.h) }
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, sel.x.toFloat(), 0f, sel.y.toFloat())
            draw(rg, mdl, 0.65f + 0.3f * sin(tt * 5f))
        }
        GLES20.glDepthMask(true)
    }

    /** Raio (origem + direção) no mundo para um toque na tela. */
    fun ray(px: Float, py: Float, w: Int, h: Int): FloatArray? {
        val nx = 2f * px / w - 1f
        val ny = 1f - 2f * py / h
        val a = FloatArray(4)
        val b = FloatArray(4)
        synchronized(inv) {
            if (!invOk) return null
            Matrix.multiplyMV(a, 0, inv, 0, floatArrayOf(nx, ny, -1f, 1f), 0)
            Matrix.multiplyMV(b, 0, inv, 0, floatArrayOf(nx, ny, 1f, 1f), 0)
        }
        for (i in 0..2) { a[i] /= a[3]; b[i] /= b[3] }
        return floatArrayOf(a[0], a[1], a[2], b[0] - a[0], b[1] - a[1], b[2] - a[2])
    }
}
