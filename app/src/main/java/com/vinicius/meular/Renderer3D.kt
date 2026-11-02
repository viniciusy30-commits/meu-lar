package com.vinicius.meular

import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.opengl.Matrix
import javax.microedition.khronos.egl.EGL10
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.egl.EGLDisplay
import javax.microedition.khronos.opengles.GL10
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.atan2
import kotlin.math.floor
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/** Etapa 11: velocidade da corrida (m/s); é a velocidade natural do clipe Slow_Run.fbx (medida: pé de apoio recua a 2,44 m/s), sem o pé deslizar. */
private const val RUN_SPEED = 2.05f

class MsaaChooser : GLSurfaceView.EGLConfigChooser {
    override fun chooseConfig(egl: EGL10, display: EGLDisplay): EGLConfig {
        for (depth in intArrayOf(24, 16)) for (s in intArrayOf(4, 0)) {
            val attr = intArrayOf(
                EGL10.EGL_RED_SIZE, 8, EGL10.EGL_GREEN_SIZE, 8, EGL10.EGL_BLUE_SIZE, 8,
                EGL10.EGL_ALPHA_SIZE, 8, EGL10.EGL_DEPTH_SIZE, depth,
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
    /** 0 = primeira pessoa, 1 = vista aérea */
    @Volatile var mode = 0

    // primeira pessoa
    @Volatile var fyaw = 0f
    @Volatile var fpitch = -0.06f
    @Volatile var px = 0f
    @Volatile var pz = 0f
    @Volatile var moveX = 0f
    @Volatile var moveY = 0f
    /** true = câmera em 3ª pessoa (vê o personagem); false = 1ª pessoa */
    @Volatile var third = true
    /** pedido de pulo (botão na tela) */
    @Volatile var jumpReq = false
    /** Etapa 10: true enquanto o analógico está quase todo arrastado (corrida); arrasto leve = andar. */
    @Volatile var pRun = false
    @Volatile var py = 0f
    private var vy = 0f
    private var pYaw = 0f
    private var pMoving = false
    private var jumpT = 0f

    // vista aérea
    @Volatile var yaw = 0.75f
    @Volatile var pitch = 0.8f
    @Volatile var zoom = 1f
    @Volatile var selected: Item? = null

    // criador de personagem (modo 2)
    @Volatile var cyaw = 0.35f
    @Volatile var cTargetDist = 5.0f
    @Volatile var cTargetY = 1.0f
    /** Etapa 6: ângulo (rad) para onde a câmera do criador gira sozinha (NaN = livre). O toque do jogador cancela. */
    @Volatile var cTargetYaw = Float.NaN
    /** Etapa 6: deslocamento vertical da imagem (coordenada da tela, 1 = meia altura) para o personagem ficar acima do painel. */
    @Volatile var cShift = 0f
    /** Etapa 6 (paisagem): deslocamento horizontal da imagem (negativo = personagem para a esquerda, painel na direita). */
    @Volatile var cShiftX = 0f
    private var cshXCur = 0f
    private var cshCur = 0f
    private val shM = FloatArray(16)
    private val pjT = FloatArray(16)
    @Volatile var autoSpin = true
    @Volatile var avDirty = true
    private var cdist = 5.0f
    private var cfy = 1.0f
    private var avMesh: Mesh? = null
    private var stageM: Mesh? = null
    // Etapa 34: na vista aérea o jogador é o MESMO personagem da câmera de perto (px, pz, pYaw); toque no chão = andar até lá
    @Volatile private var walkReq: FloatArray? = null
    @Volatile private var stopReq = false
    private var path: ArrayList<FloatArray>? = null
    private var markX = Float.NaN
    private var markZ = Float.NaN
    private val STX = -60f
    private val STZ = -60f

    @Volatile var grabbed: Item? = null
    @Volatile var aimed: Item? = null
    @Volatile var focus: Item? = null
    @Volatile var eyeX = 0f
    @Volatile var eyeZ = 0f
    @Volatile var fwdX = 0f
    @Volatile var fwdZ = -1f
    var onFocus: ((Item?, Boolean) -> Unit)? = null
    var onNeedSave: (() -> Unit)? = null

    private var lastFocus: Item? = null
    private var lastGrab = false
    private var lastT = 0L
    private var posInit = false

    private val proj = FloatArray(16)
    private val view = FloatArray(16)
    private val vp = FloatArray(16)
    private val tmp = FloatArray(16)
    private val inv = FloatArray(16)
    private var invOk = false
    private val mdl = FloatArray(16)
    private val mvp = FloatArray(16)
    private var aspect = 0.5f
    private var ex = 0f
    private var ey = 0f
    private var ez = 0f

    private var prog = 0
    private var aPos = 0
    private var aNor = 0
    private var aCol = 0
    private var aUV = 0
    private var uMVP = 0
    private var uModel = 0
    private var uAlpha = 0
    private var uTex = 0
    private var uSpec = 0
    private var uPush = 0
    private var uEye = 0
    private var uRoom = 0
    private var uLight = 0

    private val fm = HashMap<Type, Mesh>()
    private val sm = HashMap<Int, Mesh>()
    private val rm = HashMap<String, Mesh>()
    private var skyM: Mesh? = null
    private var yardM: Mesh? = null
    private var floorM: Mesh? = null
    private var ceilM: Mesh? = null
    private val walls = arrayOfNulls<Mesh>(4)
    private var bw = -1
    private var bh = -1
    private var bf = -1
    private var bwl = -1

    private val VS = """
        attribute vec3 aPos; attribute vec3 aNor; attribute vec4 aCol; attribute vec2 aUV;
        uniform mat4 uMVP; uniform mat4 uModel; uniform float uPush;
        varying vec4 vCol; varying vec3 vN; varying vec3 vW; varying vec2 vUV;
        void main() {
            gl_Position = uMVP * vec4(aPos, 1.0);
            gl_Position.z += uPush * (gl_Position.z + 0.2) / max(gl_Position.w, 0.05);
            vec4 w = uModel * vec4(aPos, 1.0);
            vW = w.xyz;
            vN = (uModel * vec4(aNor, 0.0)).xyz;
            vCol = aCol;
            vUV = aUV;
        }
    """.trimIndent()

    private val FS = """
        #ifdef GL_FRAGMENT_PRECISION_HIGH
        precision highp float;
        #else
        precision mediump float;
        #endif
        varying vec4 vCol; varying vec3 vN; varying vec3 vW; varying vec2 vUV;
        uniform sampler2D uTex; uniform float uAlpha; uniform float uSpec;
        uniform vec3 uEye; uniform vec2 uRoom; uniform vec3 uLight;
        void main() {
            vec4 t = texture2D(uTex, vUV);
            vec3 base = t.rgb * vCol.rgb;
            float a = t.a * vCol.a * uAlpha;
            if (length(vN) < 0.1) { gl_FragColor = vec4(base, a); return; }
            vec3 n = normalize(vN);
            vec3 L = normalize(vec3(0.45, 1.0, 0.65));
            float diff = max(dot(n, L), 0.0);
            vec3 amb = mix(vec3(0.40, 0.37, 0.36), vec3(0.60, 0.67, 0.78), 0.5 + 0.5 * n.y);
            vec3 pl = uLight - vW;
            float d2 = dot(pl, pl);
            vec3 pL = pl * inversesqrt(max(d2, 0.001));
            float att = 1.0 / (1.0 + 0.10 * d2);
            float pd = max(dot(n, pL), 0.0) * att;
            float ao = 1.0;
            float side = 1.0 - abs(n.y);
            ao *= mix(1.0, 0.72 + 0.28 * clamp(vW.y * 1.6, 0.0, 1.0), side);
            if (vW.y < 0.12 && n.y > 0.8 && vW.x > 0.0 && vW.x < uRoom.x && vW.z > 0.0 && vW.z < uRoom.y) {
                float e = min(min(vW.x, uRoom.x - vW.x), min(vW.z, uRoom.y - vW.z));
                ao *= 0.78 + 0.22 * smoothstep(0.0, 0.8, e);
            }
            vec3 light = amb + vec3(1.0, 0.96, 0.88) * 0.55 * diff + vec3(1.0, 0.80, 0.52) * 0.85 * pd;
            vec3 col = base * light * ao;
            vec3 V = normalize(uEye - vW);
            vec3 H = normalize(L + V);
            float s = pow(max(dot(n, H), 0.0), 42.0) * uSpec;
            float sp2 = pow(max(dot(n, normalize(pL + V)), 0.0), 30.0) * uSpec * 0.5 * att * 3.0;
            col += (s + sp2) * vec3(1.0, 0.97, 0.9);
            gl_FragColor = vec4(col, a);
        }
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
        aUV = GLES20.glGetAttribLocation(prog, "aUV")
        uMVP = GLES20.glGetUniformLocation(prog, "uMVP")
        uModel = GLES20.glGetUniformLocation(prog, "uModel")
        uAlpha = GLES20.glGetUniformLocation(prog, "uAlpha")
        uTex = GLES20.glGetUniformLocation(prog, "uTex")
        uSpec = GLES20.glGetUniformLocation(prog, "uSpec")
        uPush = GLES20.glGetUniformLocation(prog, "uPush")
        uEye = GLES20.glGetUniformLocation(prog, "uEye")
        uRoom = GLES20.glGetUniformLocation(prog, "uRoom")
        uLight = GLES20.glGetUniformLocation(prog, "uLight")
        GLES20.glUseProgram(prog)
        GLES20.glEnableVertexAttribArray(aPos)
        GLES20.glEnableVertexAttribArray(aNor)
        GLES20.glEnableVertexAttribArray(aCol)
        GLES20.glEnableVertexAttribArray(aUV)
        Tex.init()
        CuteChar.initGl()
        skyM = Models.sky()
        stageM = AvatarModel.stage()
        avDirty = true
        bw = -1
    }

    override fun onSurfaceChanged(gl: GL10?, w: Int, h: Int) {
        GLES20.glViewport(0, 0, w, h)
        aspect = w.toFloat() / maxOf(1, h).toFloat()
    }

    private fun draw(m: Mesh, model: FloatArray, alpha: Float, glass: Boolean = false) {
        Matrix.multiplyMM(mvp, 0, vp, 0, model, 0)
        GLES20.glUniformMatrix4fv(uMVP, 1, false, mvp, 0)
        GLES20.glUniformMatrix4fv(uModel, 1, false, model, 0)
        GLES20.glUniform1f(uAlpha, alpha)
        for (p in m.parts) {
            if ((p.mat == Mt.GLASS) != glass) continue
            GLES20.glActiveTexture(GLES20.GL_TEXTURE0)
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, if (p.tex != 0) p.tex else Tex.ids[p.mat])
            GLES20.glUniform1i(uTex, 0)
            GLES20.glUniform1f(uSpec, Mt.SPEC[p.mat])
            GLES20.glUniform1f(uPush, p.push)
            val bytes = STRIDE * 4
            p.buf.position(0)
            GLES20.glVertexAttribPointer(aPos, 3, GLES20.GL_FLOAT, false, bytes, p.buf)
            p.buf.position(3)
            GLES20.glVertexAttribPointer(aNor, 3, GLES20.GL_FLOAT, false, bytes, p.buf)
            p.buf.position(6)
            GLES20.glVertexAttribPointer(aCol, 4, GLES20.GL_FLOAT, false, bytes, p.buf)
            p.buf.position(10)
            GLES20.glVertexAttribPointer(aUV, 2, GLES20.GL_FLOAT, false, bytes, p.buf)
            val ib = p.idx
            if (ib != null) {
                ib.position(0)
                GLES20.glDrawElements(GLES20.GL_TRIANGLES, p.icount, GLES20.GL_UNSIGNED_SHORT, ib)
            } else {
                GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, p.count)
            }
        }
    }

    private fun rebuild() {
        val gw = st.gw
        val gh = st.gh
        val fl = Finish.floors[st.floorIdx]
        val wl = Finish.walls[st.wallIdx]
        yardM = Models.yard(gw, gh)
        floorM = Models.interior(gw, gh, fl)
        ceilM = Models.ceiling(gw, gh)
        val W = gw.toDouble()
        val H = gh.toDouble()
        walls[0] = Models.wall(W, listOf(Opening(W / 2, 1.9, false)), wl.cor, true, false)
        walls[1] = Models.wall(W, listOf(Opening(W / 2, 1.1, true), Opening(W * 0.22, 1.25, false), Opening(W * 0.78, 1.25, false)), wl.cor, true, false)
        walls[2] = Models.wall(H, listOf(Opening(H / 2, 1.6, false)), wl.cor, false, false)
        walls[3] = Models.wall(H, emptyList(), wl.cor, false, true)
        bw = gw; bh = gh; bf = st.floorIdx; bwl = st.wallIdx
    }

    private fun wallModel(i: Int, gw: Float, gh: Float) {
        Matrix.setIdentityM(mdl, 0)
        when (i) {
            1 -> { Matrix.translateM(mdl, 0, gw, 0f, gh); Matrix.rotateM(mdl, 0, 180f, 0f, 1f, 0f) }
            2 -> { Matrix.translateM(mdl, 0, 0f, 0f, gh); Matrix.rotateM(mdl, 0, 90f, 0f, 1f, 0f) }
            3 -> { Matrix.translateM(mdl, 0, gw, 0f, 0f); Matrix.rotateM(mdl, 0, -90f, 0f, 1f, 0f) }
        }
    }

    // ------------------------------------------------------------ movimento em 1ª pessoa

    private fun inside(o: Item, x: Float, z: Float): Boolean =
        x > o.x - 0.3f && x < o.x + o.w + 0.3f && z > o.y - 0.3f && z < o.y + o.h + 0.3f

    private fun walkable(nx: Float, nz: Float, ox: Float, oz: Float): Boolean {
        val gw = st.gw.toFloat()
        val gh = st.gh.toFloat()
        val inFoot = nx > -0.45f && nx < gw + 0.45f && nz > -0.45f && nz < gh + 0.45f
        if (inFoot) {
            val ins = nx > 0.32f && nx < gw - 0.32f && nz > 0.32f && nz < gh - 0.32f
            val door = abs(nx - gw / 2f) < 0.42f && nz > gh - 0.4f && nz < gh + 0.45f
            if (!ins && !door) return false
        } else {
            if (!(nx > -6.6f && nx < gw + 6.6f && nz > -6.6f && nz < gh + 8.6f)) return false
        }
        val g = grabbed
        for (o in st.items) {
            if (o.type == Type.RUG || o === g) continue
            if (inside(o, nx, nz) && !inside(o, ox, oz)) return false
        }
        return true
    }

    /** Vista aérea: manda o personagem andar até o ponto (x, z) do chão (chamado pela thread de toque). */
    fun walkTo(x: Float, z: Float) { walkReq = floatArrayOf(x, z) }

    /** Cancela a caminhada em andamento. */
    fun stopWalk() { stopReq = true }

    /** Ao voltar para a câmera de perto, a câmera fica atrás do personagem, olhando para onde ele está virado. */
    fun faceCameraBehindPlayer() {
        fyaw = (Math.PI - Math.toRadians(pYaw.toDouble())).toFloat()
        fpitch = -0.06f
    }

    /** Ponto bloqueado para o personagem (parede, móvel, fora da casa/porta); sem a exceção "já estava dentro" de [walkable]. */
    private fun blockedAt(x: Float, z: Float): Boolean {
        val gw = st.gw.toFloat()
        val gh = st.gh.toFloat()
        val inFoot = x > -0.45f && x < gw + 0.45f && z > -0.45f && z < gh + 0.45f
        if (inFoot) {
            val ins = x > 0.32f && x < gw - 0.32f && z > 0.32f && z < gh - 0.32f
            val door = abs(x - gw / 2f) < 0.42f && z > gh - 0.4f && z < gh + 0.45f
            if (!ins && !door) return true
        } else return true
        for (o in st.items) {
            if (o.type == Type.RUG) continue
            if (inside(o, x, z)) return true
        }
        return false
    }

    private fun clearLine(ax: Float, az: Float, bx: Float, bz: Float): Boolean {
        val d = kotlin.math.hypot(bx - ax, bz - az)
        val n = maxOf(1, kotlin.math.ceil(d / 0.1f).toInt())
        for (k in 1..n) {
            val t = k.toFloat() / n
            if (blockedAt(ax + (bx - ax) * t, az + (bz - az) * t)) return false
        }
        return true
    }

    /** Acha um caminho até o ponto livre alcançável mais perto de (tx, tz) (grade de 25 cm, 8 vizinhos, depois alisa em linhas retas). */
    private fun planPath(tx: Float, tz: Float): ArrayList<FloatArray>? {
        val gw = st.gw.toFloat()
        val gh = st.gh.toFloat()
        val res = 0.25f
        val x0 = -0.5f
        val z0 = -0.5f
        val nx = ((gw + 1f) / res).toInt() + 1
        val nz = ((gh + 1.5f) / res).toInt() + 1
        val pre = ArrayList<FloatArray>()
        var sx = px
        var sz = pz
        var si = ((sx - x0) / res + 0.5f).toInt()
        var sj = ((sz - z0) / res + 0.5f).toInt()
        if (si !in 0 until nx || sj !in 0 until nz) {
            // está no quintal: entra pela porta e segue de lá
            pre.add(floatArrayOf(gw / 2f, gh + 0.5f))
            sx = gw / 2f; sz = gh - 0.6f
            pre.add(floatArrayOf(sx, sz))
            si = ((sx - x0) / res + 0.5f).toInt()
            sj = ((sz - z0) / res + 0.5f).toInt()
        }
        val blocked = BooleanArray(nx * nz) { blockedAt(x0 + (it % nx) * res, z0 + (it / nx) * res) }
        val start = sj * nx + si
        val parent = IntArray(nx * nz) { -2 }
        val queue = IntArray(nx * nz)
        var qh = 0
        var qt = 0
        parent[start] = -1
        queue[qt++] = start
        var best = start
        var bd = Float.MAX_VALUE
        while (qh < qt) {
            val c = queue[qh++]
            val ci = c % nx
            val cj = c / nx
            val dx = x0 + ci * res - tx
            val dz = z0 + cj * res - tz
            val d = dx * dx + dz * dz
            if (d < bd) { bd = d; best = c }
            for (oj in -1..1) for (oi in -1..1) {
                if (oi == 0 && oj == 0) continue
                val ni = ci + oi
                val nj = cj + oj
                if (ni < 0 || nj < 0 || ni >= nx || nj >= nz) continue
                val n = nj * nx + ni
                if (parent[n] != -2 || blocked[n]) continue
                if (oi != 0 && oj != 0 && (blocked[cj * nx + ni] || blocked[nj * nx + ci])) continue  // não corta quina
                parent[n] = c
                queue[qt++] = n
            }
        }
        if (best == start && pre.isEmpty()) return null
        val pts = ArrayList<FloatArray>()
        var c = best
        while (c != -1 && c != start) {
            pts.add(floatArrayOf(x0 + (c % nx) * res, z0 + (c / nx) * res))
            c = parent[c]
        }
        pts.reverse()
        if (!blockedAt(tx, tz) && bd < res * res * 2f && pts.isNotEmpty()) pts[pts.size - 1] = floatArrayOf(tx, tz)
        // alisa: de cada ponto, vai direto ao mais distante que ainda dá para ver em linha reta
        val out = ArrayList<FloatArray>(pre)
        var ax = sx
        var az = sz
        var i = 0
        while (i < pts.size) {
            var j = pts.size - 1
            while (j > i && !clearLine(ax, az, pts[j][0], pts[j][1])) j--
            out.add(pts[j])
            ax = pts[j][0]; az = pts[j][1]
            i = j + 1
        }
        return if (out.isEmpty()) null else out
    }

    private fun startWalk(tx: Float, tz: Float) {
        val p = planPath(tx, tz)
        if (p == null) { path = null; markX = Float.NaN; return }
        path = p
        val last = p[p.size - 1]
        markX = last[0]; markZ = last[1]
    }

    /** Segue o caminho em vista aérea (anda; corre se o trecho for longo). */
    private fun followPath(dt: Float) {
        val p = path
        if (p == null || p.isEmpty()) {
            pMoving = false; pRun = false
            if (p != null) { path = null; markX = Float.NaN }
            return
        }
        var rem = 0f
        var lx = px
        var lz = pz
        for (w in p) { rem += kotlin.math.hypot(w[0] - lx, w[1] - lz); lx = w[0]; lz = w[1] }
        pRun = if (pRun) rem > 2.0f else rem > 3.8f
        var budget = (if (pRun) RUN_SPEED else 1.28f) * dt
        pMoving = false
        while (budget > 0f && p.isNotEmpty()) {
            val w = p[0]
            val dx = w[0] - px
            val dz = w[1] - pz
            val d = kotlin.math.hypot(dx, dz)
            if (d < 0.03f) { p.removeAt(0); continue }
            val s = min(d, budget)
            val mx = dx / d * s
            val mz = dz / d * s
            var moved = false
            if (abs(mx) > 1e-5f && walkable(px + mx, pz, px, pz)) { px += mx; moved = true }
            if (abs(mz) > 1e-5f && walkable(px, pz + mz, px, pz)) { pz += mz; moved = true }
            if (!moved) { p.clear(); break }   // preso (móvel novo no caminho): para
            pMoving = true
            val dir = Math.toDegrees(atan2(dx.toDouble(), dz.toDouble())).toFloat()
            var dl = dir - pYaw
            while (dl > 180f) dl -= 360f
            while (dl < -180f) dl += 360f
            pYaw += dl * min(1f, dt * 12f)
            budget -= s
            if (s < d) break
        }
        if (p.isEmpty()) { path = null; pMoving = false; pRun = false; markX = Float.NaN }
    }

    private fun updateFP(dt: Float) {
        if (!posInit) {
            px = st.gw / 2f
            pz = st.gh - 0.9f
            posInit = true
            pYaw = Math.toDegrees(atan2(sin(fyaw).toDouble(), (-cos(fyaw)).toDouble())).toFloat()
        }
        if (stopReq) { stopReq = false; path = null; markX = Float.NaN }
        val req = walkReq
        if (req != null) { walkReq = null; if (mode == 1) startWalk(req[0], req[1]) }
        if (mode != 0 && mode != 1) { jumpReq = false; return }
        // pulo
        if (jumpReq && mode == 0) {
            jumpReq = false
            if (py <= 0.001f && vy <= 0f) { vy = 3.9f; jumpT = 0f }
        } else jumpReq = false
        if (py > 0f || vy > 0f) {
            vy -= 11f * dt
            jumpT += dt
            py += vy * dt
            if (py <= 0f) { py = 0f; vy = 0f }
        }
        if (mode == 1) { followPath(dt); return }
        if (path != null) { path = null; markX = Float.NaN }   // câmera de perto: o analógico manda
        pMoving = false
        if (moveX * moveX + moveY * moveY <= 0.0004f) pRun = false
        val mx = moveX
        val my = moveY
        val mag2 = mx * mx + my * my
        if (mag2 > 0.0004f) {
            val mag = sqrt(mag2)
            // histerese: corre com o analógico quase no limite; solta abaixo disso e volta a andar
            pRun = if (pRun) mag > 0.70f else mag > 0.88f
            // andar: velocidade proporcional ao arrasto (como antes); correr: velocidade fixa (casada com o clipe)
            val sp = if (pRun) RUN_SPEED * dt / mag else 1.28f * dt  // casado com o passo da animação (CuteChar.WALK_RATE / RUN)
            val fx = sin(fyaw)
            val fz = -cos(fyaw)
            val rx = cos(fyaw)
            val rz = sin(fyaw)
            val dx = (fx * my + rx * mx) * sp
            val dz = (fz * my + rz * mx) * sp
            if (walkable(px + dx, pz, px, pz)) px += dx
            if (walkable(px, pz + dz, px, pz)) pz += dz
            pMoving = true
            val dir = Math.toDegrees(atan2(dx.toDouble(), dz.toDouble())).toFloat()
            var dl = dir - pYaw
            while (dl > 180f) dl -= 360f
            while (dl < -180f) dl += 360f
            pYaw += dl * min(1f, dt * 12f)
        }
    }

    /** Desenha o personagem do jogador (câmera em 3ª pessoa). */
    private fun drawPlayer(now: Long) {
        val t = (now / 1_000_000L % 100000L) / 1000f
        val air = py > 0.02f
        val cute = if (air) CuteChar.frame(CuteChar.JUMP, minOf(jumpT, CuteChar.clipSeconds(CuteChar.JUMP) * 0.999f))
                   else CuteChar.frame(if (pMoving) (if (pRun) CuteChar.RUN else CuteChar.WALK) else CuteChar.IDLE, t)
        val m = cute ?: avMesh ?: return
        val up = if (cute != null) CuteChar.lift(0) else 0f   // Etapa 20: sola em cima do chão
        Matrix.setIdentityM(mdl, 0)
        Matrix.translateM(mdl, 0, px, py + up, pz)
        Matrix.rotateM(mdl, 0, pYaw, 0f, 1f, 0f)
        draw(m, mdl, 1f)
    }

    // ------------------------------------------------------------ personagem

    private fun drawCreator(now: Long) {
        GLES20.glClearColor(0.105f, 0.125f, 0.19f, 1f)
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
        GLES20.glUniform3f(uEye, ex, ey, ez)
        GLES20.glUniform2f(uRoom, 0f, 0f)
        GLES20.glUniform3f(uLight, STX + 0.9f, 2.4f, STZ + 1.7f)
        Matrix.setIdentityM(mdl, 0)
        Matrix.translateM(mdl, 0, STX, 0f, STZ)
        stageM?.let { draw(it, mdl, 1f) }
        val t = (now / 1_000_000L % 100000L) / 1000f
        val br = 1f + 0.006f * sin(t * 2.2f)
        val cute = CuteChar.frame(CuteChar.IDLE, t, 2)
        Matrix.setIdentityM(mdl, 0)
        Matrix.translateM(mdl, 0, STX, 0.082f + (if (cute != null) CuteChar.lift(2) else 0f), STZ)
        if (cute != null) {
            draw(cute, mdl, 1f)
        } else {
            Matrix.scaleM(mdl, 0, 1f, br, 1f)
            avMesh?.let { draw(it, mdl, 1f) }
        }
    }

    // ------------------------------------------------------------ picking

    private fun hitBox(ry: FloatArray, x0: Float, y0: Float, z0: Float, x1: Float, y1: Float, z1: Float): Float {
        var tmin = 0f
        var tmax = 1e9f
        val mn = floatArrayOf(x0, y0, z0)
        val mx = floatArrayOf(x1, y1, z1)
        for (i in 0..2) {
            val o = ry[i]
            val d = ry[3 + i]
            if (abs(d) < 1e-6f) {
                if (o < mn[i] || o > mx[i]) return -1f
            } else {
                var t1 = (mn[i] - o) / d
                var t2 = (mx[i] - o) / d
                if (t1 > t2) { val s = t1; t1 = t2; t2 = s }
                if (t1 > tmin) tmin = t1
                if (t2 < tmax) tmax = t2
                if (tmin > tmax) return -1f
            }
        }
        return tmin
    }

    /** Item atingido por um raio (origem+direção). maxT limita o alcance. */
    fun pickRay(ry: FloatArray, maxT: Float = 1e9f): Item? {
        var best: Item? = null
        var bt = maxT
        for (o in st.items) {
            if (o.type == Type.RUG) continue
            val t = hitBox(ry, o.x.toFloat(), 0f, o.y.toFloat(), (o.x + o.w).toFloat(), o.type.alt, (o.y + o.h).toFloat())
            if (t >= 0f && t < bt) { bt = t; best = o }
        }
        if (best != null) return best
        if (abs(ry[4]) < 1e-6f) return null
        val t = -ry[1] / ry[4]
        if (t < 0f || t > maxT) return null
        val cx = floor(ry[0] + t * ry[3]).toInt()
        val cz = floor(ry[2] + t * ry[5]).toInt()
        return st.items.lastOrNull { o ->
            o.type == Type.RUG && cx >= o.x && cx < o.x + o.w && cz >= o.y && cz < o.y + o.h
        }
    }

    fun floorPoint(ry: FloatArray): FloatArray? {
        if (ry[4] > -1e-4f) return null
        val t = -ry[1] / ry[4]
        if (t < 0f) return null
        return floatArrayOf(ry[0] + t * ry[3], ry[2] + t * ry[5], t)
    }

    /** Raio do centro da tela (primeira pessoa). */
    private fun centerRay(): FloatArray {
        val cp = cos(fpitch)
        return floatArrayOf(ex, ey, ez, sin(fyaw) * cp, sin(fpitch), -cos(fyaw) * cp)
    }

    private fun updateGrab() {
        if (mode != 0) return
        val g = grabbed
        if (g != null) {
            val fp = floorPoint(centerRay())
            if (fp != null && fp[2] < 7f) {
                val nx = floor(fp[0] - g.w / 2f + 0.5f).toInt().coerceIn(0, maxOf(0, st.gw - g.w))
                val nz = floor(fp[1] - g.h / 2f + 0.5f).toInt().coerceIn(0, maxOf(0, st.gh - g.h))
                if ((nx != g.x || nz != g.y) && st.canPlace(g, nx, nz, g.rot)) { g.x = nx; g.y = nz }
            }
            aimed = null
        } else {
            aimed = pickRay(centerRay(), 5.5f)
        }
    }

    private fun updateFocus() {
        val f = if (mode == 0) (grabbed ?: aimed) else selected
        focus = f
        val gr = grabbed != null
        if (f !== lastFocus || gr != lastGrab) {
            lastFocus = f
            lastGrab = gr
            onFocus?.invoke(f, gr)
        }
    }

    // ------------------------------------------------------------ quadro

    override fun onDrawFrame(gl: GL10?) {
        val now = System.nanoTime()
        var dt = if (lastT == 0L) 0.016f else (now - lastT) / 1e9f
        lastT = now
        if (dt > 0.05f) dt = 0.05f

        if (st.gw != bw || st.gh != bh || st.floorIdx != bf || st.wallIdx != bwl) rebuild()
        updateFP(dt)

        val gw = st.gw
        val gh = st.gh
        val cx = gw / 2f
        val cz = gh / 2f
        val fp = mode == 0
        val cr = mode == 2

        if (cr) {
            val k = min(1f, dt * 6f)
            cdist += (cTargetDist - cdist) * k
            cfy += (cTargetY - cfy) * k
            cshCur += (cShift - cshCur) * k
            cshXCur += (cShiftX - cshXCur) * k
            if (autoSpin) cyaw += dt * 0.45f
            val tyaw = cTargetYaw
            if (!tyaw.isNaN()) {
                val twoPi = (2.0 * Math.PI).toFloat()
                var dy = (tyaw - cyaw) % twoPi
                if (dy > Math.PI.toFloat()) dy -= twoPi
                if (dy < -Math.PI.toFloat()) dy += twoPi
                cyaw += dy * min(1f, dt * 5f)
                if (abs(dy) < 0.004f) cTargetYaw = Float.NaN
            }
            val cp = 0.10f
            ex = STX + cdist * cos(cp) * sin(cyaw)
            ey = cfy + cdist * sin(cp)
            ez = STZ + cdist * cos(cp) * cos(cyaw)
            Matrix.perspectiveM(proj, 0, 34f, aspect, 0.1f, 200f)
            if (cshCur != 0f || cshXCur != 0f) {
                Matrix.setIdentityM(shM, 0)
                Matrix.translateM(shM, 0, cshXCur, cshCur, 0f)
                System.arraycopy(proj, 0, pjT, 0, 16)
                Matrix.multiplyMM(proj, 0, shM, 0, pjT, 0)
            }
            Matrix.setLookAtM(view, 0, ex, ey, ez, STX, cfy, STZ, 0f, 1f, 0f)
        } else if (fp) {
            val cp = cos(fpitch)
            val fx = sin(fyaw) * cp
            val fy = sin(fpitch)
            val fz = -cos(fyaw) * cp
            fwdX = sin(fyaw); fwdZ = -cos(fyaw)
            if (third) {
                // 3ª pessoa: câmera atrás do personagem, orbitando com o olhar
                val tx = px; val ty = py * 0.6f + 1.05f; val tz = pz
                val inRoom = px > 0.32f && px < gw - 0.32f && pz > 0.32f && pz < gh - 0.32f
                var t = 1f
                var ox = tx; var oy = ty; var oz = tz
                for (i in 0..12) {
                    ox = tx - fx * 2.7f * t; oy = ty - fy * 2.7f * t; oz = tz - fz * 2.7f * t
                    val okRoom = !inRoom || (ox > 0.2f && ox < gw - 0.2f && oz > 0.2f && oz < gh - 0.2f && oy < 2.3f)
                    if (okRoom) break
                    t -= 0.07f
                }
                ex = ox; ey = maxOf(oy, 0.25f); ez = oz
                Matrix.perspectiveM(proj, 0, 60f, aspect, 0.08f, 260f)
                Matrix.setLookAtM(view, 0, ex, ey, ez, tx, ty, tz, 0f, 1f, 0f)
            } else {
                ex = px; ey = 1.62f + py; ez = pz
                Matrix.perspectiveM(proj, 0, 68f, aspect, 0.08f, 260f)
                Matrix.setLookAtM(view, 0, ex, ey, ez, ex + fx, ey + fy, ez + fz, 0f, 1f, 0f)
            }
        } else {
            val dist = maxOf(gw, gh) * 2.0f / minOf(aspect, 1f) * zoom
            ex = cx + dist * cos(pitch) * sin(yaw)
            ey = 0.5f + dist * sin(pitch)
            ez = cz + dist * cos(pitch) * cos(yaw)
            Matrix.perspectiveM(proj, 0, 40f, aspect, 0.3f, 260f)
            Matrix.setLookAtM(view, 0, ex, ey, ez, cx, 0.4f, cz, 0f, 1f, 0f)
        }
        if (fp && third) { eyeX = px; eyeZ = pz } else { eyeX = ex; eyeZ = ez }
        Matrix.multiplyMM(vp, 0, proj, 0, view, 0)
        if (Matrix.invertM(tmp, 0, vp, 0)) {
            synchronized(inv) { System.arraycopy(tmp, 0, inv, 0, 16); invOk = true }
        }

        updateGrab()
        updateFocus()

        if (avDirty) {
            avDirty = false
            if (!CuteChar.ready) AvatarBuilder.request(st.avatar)
        }
        AvatarBuilder.take()?.let { avMesh = it }
        if (cr) {
            drawCreator(now)
            return
        }
        GLES20.glClearColor(0.66f, 0.85f, 0.94f, 1f)
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
        GLES20.glUniform3f(uEye, ex, ey, ez)
        GLES20.glUniform2f(uRoom, gw.toFloat(), gh.toFloat())
        GLES20.glUniform3f(uLight, cx, 2.1f, cz)

        // céu
        GLES20.glDisable(GLES20.GL_DEPTH_TEST)
        Matrix.setIdentityM(mdl, 0)
        Matrix.translateM(mdl, 0, ex, ey, ez)
        skyM?.let { draw(it, mdl, 1f) }
        GLES20.glEnable(GLES20.GL_DEPTH_TEST)

        Matrix.setIdentityM(mdl, 0)
        yardM?.let { draw(it, mdl, 1f) }
        floorM?.let { draw(it, mdl, 1f) }

        val shown = BooleanArray(4)
        shown[0] = fp || ez >= cz
        shown[1] = fp || ez < cz
        shown[2] = fp || ex >= cx
        shown[3] = fp || ex < cx
        for (i in 0..3) if (shown[i]) {
            wallModel(i, gw.toFloat(), gh.toFloat())
            walls[i]?.let { draw(it, mdl, 1f) }
        }
        if (fp) {
            Matrix.setIdentityM(mdl, 0)
            ceilM?.let { draw(it, mdl, 1f) }
        }

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
            val lift = if (item === grabbed) 0.08f else 0f
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, item.x + item.w / 2f, lift, item.y + item.h / 2f)
            Matrix.rotateM(mdl, 0, item.rot * 90f, 0f, 1f, 0f)
            Matrix.scaleM(mdl, 0, s, s, s)
            Matrix.translateM(mdl, 0, -t.w / 2f, 0f, -t.h / 2f)
            draw(mesh, mdl, 1f)
        }

        if (mode == 1 || (fp && third)) drawPlayer(now)

        GLES20.glDepthMask(false)
        val tt = (now / 1_000_000L % 100000L) / 1000f
        for (item in items) {
            if (item.type == Type.RUG) continue
            val key = item.w * 10 + item.h
            val shm = sm.getOrPut(key) { Models.shadow(item.w, item.h) }
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, item.x.toFloat(), 0f, item.y.toFloat())
            draw(shm, mdl, 1f)
        }
        if (mode == 1 || (fp && third)) {
            val shm = sm.getOrPut(11) { Models.shadow(1, 1) }
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, px - 0.5f, 0f, pz - 0.5f)
            draw(shm, mdl, 1f)
        }
        if (mode == 1 && path != null && !markX.isNaN()) {
            val rg = rm.getOrPut("walk") { Models.ring(1, 1, C("#5CE08A")) }
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, floor(markX), 0f, floor(markZ))
            draw(rg, mdl, 0.6f + 0.4f * sin(tt * 6f))
        }
        val sel = focus
        if (sel != null) {
            val green = grabbed != null
            val key = "${sel.w}x${sel.h}${if (green) "g" else "y"}"
            val rg = rm.getOrPut(key) { Models.ring(sel.w, sel.h, if (green) C("#5CE08A") else C("#FFE066")) }
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, sel.x.toFloat(), 0f, sel.y.toFloat())
            draw(rg, mdl, 0.7f + 0.3f * sin(tt * 5f))
        }
        // vidros por último
        for (i in 0..3) if (shown[i]) {
            wallModel(i, gw.toFloat(), gh.toFloat())
            walls[i]?.let { draw(it, mdl, 1f, true) }
        }
        GLES20.glDepthMask(true)
    }

    /** Raio (origem + direção) no mundo para um toque na tela (vista aérea). */
    fun ray(pxl: Float, pyl: Float, w: Int, h: Int): FloatArray? {
        val nx = 2f * pxl / w - 1f
        val ny = 1f - 2f * pyl / h
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
