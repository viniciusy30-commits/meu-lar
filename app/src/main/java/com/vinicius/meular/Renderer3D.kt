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
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/** Etapa 11: velocidade da corrida (m/s); é a velocidade natural do clipe Slow_Run.fbx (medida: pé de apoio recua a 2,44 m/s), sem o pé deslizar. */
private const val JUMP_PRE = 0.14f   // agachada antes do pulo parado (= trecho pré-decolagem do clipe 2)
private const val WALK_SPEED = 1.7f   // Etapa 63: casado com o passo dos clipes de andar novos (Mixamo)
private const val RUN_SPEED = 3.2f
private const val CROUCH_SPEED = 0.85f
/** Etapa 89: animação de interagir (braço esticado) desligada; o clipe 8 continua nos arquivos */
private const val USE_ANIM = false  // Etapa 88: andando agachado (Crouch_Fwd_Loop)   // Etapa 63: casado com o passo da corrida nova (Mixamo Running_1)

class MsaaChooser : GLSurfaceView.EGLConfigChooser {
    override fun chooseConfig(egl: EGL10, display: EGLDisplay): EGLConfig {
        for (depth in intArrayOf(24, 16)) for (s in intArrayOf(4, 2, 0)) {
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
    /** Etapa 89: quadros por segundo (média móvel) */
    @Volatile var fpsAvg = 60f
    @Volatile var showFps = false
    /** Etapa 88: agachado (botão de agachar); pular levanta */
    @Volatile var crouch = false
    private var crouchK = 0f
    /** Etapa 10: true enquanto o analógico está quase todo arrastado (corrida); arrasto leve = andar. */
    @Volatile var pRun = false
    @Volatile var py = 0f
    private var vy = 0f
    // ---- Etapa 128: voo livre para explorar (subir/descer, turbo) ----
    @Volatile var flyReq = false
    @Volatile var flyUp = false
    @Volatile var flyDown = false
    @Volatile var turbo = false
    @Volatile var flying = false; private set
    @Volatile var flySpeed = 0f; private set
    private var landing = false
    private var landX = 0f; private var landZ = 0f
    private var flyAlt = 0f
    private var fvx = 0f; private var fvy = 0f; private var fvz = 0f
    private var flyTilt = 0f
    private var pYaw = 0f
    private var pMoving = false
    private var jumpT = 0f
    private var jumping = false
    private var jumpLaunched = false
    private var jumpRun = false
    private var jumpPre = 0f

    // ---- Etapa 118: piscina ----
    // 0 = fora d'água; 1 = mergulhando (Run_To_Dive); 2 = na água (boiando / nadando); 3 = nadando até a borda (Swimming_To_Edge); 4 = saindo da borda para o deck
    private var swimPh = 0
    private var swimT = 0f
    private var swX = 0f; private var swZ = 0f      // posição de partida do mergulho / da saída
    private var swDX = 0f; private var swDZ = 0f    // direção (x, z) do mergulho / da saída (vetor unitário)
    private var swYaw = 0f
    private var swToX = 0f; private var swToZ = 0f  // destino da etapa atual
    // 5 = sentando na borda (SIT_IN); 6 = sentado na borda, pernas na água; 7 = escorregando para a água; 8 = levantando (SIT_OUT)
    // Etapa 120: velocidade na água, histerese nadar/boiar, ondinhas
    private var swVX = 0f
    private var swVZ = 0f
    private var swimAnimMove = false
    private var swimStill = 0f
    private var ripT = 0f
    private var waterT = 0f
    private var diveSplash = false
    private var swimJump = false                    // o botão de pulo foi apertado neste quadro
    private var edgeHold = 0f                       // tempo empurrando o analógico contra a água

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
    /** Etapa 40: inclinação da câmera do criador (rad), arrastar para cima/baixo; alvo NaN = livre. */
    @Volatile var cPitch = 0.10f
    @Volatile var cTargetPitch = Float.NaN
    /** Etapa 40: deslocamento extra da imagem (arrastar com dois dedos), mesma unidade de cShift. */
    @Volatile var cPanX = 0f
    @Volatile var cPanY = 0f
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
    private val cloth = ClothCurtains()
    /** Usa o que está ao alcance (porta ou cortina). Chamado pela thread da interface. */
    fun interact() { useReq = true }
    @Volatile private var useReq = false
    /** Etapa 83: objeto com física dormiu (posição estável): a interface grava o jogo */
    @Volatile var saveReq = false
    private var nearItem: Item? = null
    private var nearPart = -1
    private var msgText = ""
    private var msgT = 0f
    // ---- Etapa 83: sentar (poltrona). Fases: 0 nada, 1 andando até o assento, 2 virando, 3 sentando, 4 sentado, 5 levantando
    private var sitItem: Item? = null
    @Volatile private var sitPh = 0
    private var sitT = 0f
    private var sitStuck = 0f
    private var sitCancel = false
    private var sitPath: ArrayList<FloatArray>? = null
    private var sitStartPt: FloatArray? = null
    private val sitPt = FloatArray(4)          // raiz sentada (x, z) e ponto de início (x, z)
    private var sitYaw = 0f
    private var sitDY = 0f
    private var sitLift = 0f
    private val sitWhere = FloatArray(3)
    // Lote 2: vários assentos, deitar (cama)
    private var nearSeat = ""
    private var sitSeat = ""
    private var sitPressed = false
    private var lieMode = false
    private var lieK = 0f
    private var lieT = 0f
    private val lieRoot = FloatArray(3)
    private var lieYaw = 0f
    private val plM = FloatArray(16)
    // Etapa 86: puxar a cadeira (peça com gatilho "puxar") e usar peças com a animação de interagir
    private var pullSlot = -1
    private var pullTgt = 0f
    private var pullPush = 0.7f
    private val sitBase = FloatArray(2)
    private var usePh = 0
    private var useT = 0f
    private var useItem: Item? = null
    private var useK = -1
    private var useDone = false
    private var useYaw = 0f        // onde o assento estava ao começar (se o móvel for mexido, a ação é cancelada)
    // ---- Etapa 83: física e peças animadas
    private val statics = ArrayList<SBox>()
    private val partBoxes = ArrayList<FloatArray>()
    private var physT = 0L
    private var lastPhX = Float.NaN
    private var lastPhZ = 0f
    private val gmA = FloatArray(16)
    private val gmB = FloatArray(16)
    private val gmL = FloatArray(16)
    private var nodeW = Array(32) { FloatArray(16) }
    private val baseM = FloatArray(16)

    /** Porta aberta/fechada (agora por interação, não mais automática). */
    @Volatile var doorOpen = false
    /** O que está ao alcance do personagem: 0 nada, 1 porta, 2 cortina (para o botão de interação). */
    /** Etapa 125: foto da cidade vista de cima (mapa e minimapa). Devolve o bitmap e o retângulo do mundo (x0, z0, x1, z1). */
    @Volatile var mapReq = false
    var onMap: ((android.graphics.Bitmap, FloatArray) -> Unit)? = null
    private var fogOn = 1f
    private var mapGen = -1
    private var mapBuilt = -1

    private fun captureMap() {
        if (!City.on) return
        mapReq = false
        val x0 = City.X0 - 6f; val x1 = City.X1 + 6f; val z0 = City.Z0 - 6f; val z1 = City.SEA_Z + 75f
        val wW = x1 - x0; val wH = z1 - z0
        val n = 2048; val nh = (n * wH / wW).toInt().coerceAtMost(2048)
        val fb = IntArray(1); val tx = IntArray(1); val rb = IntArray(1)
        GLES20.glGenFramebuffers(1, fb, 0); GLES20.glGenTextures(1, tx, 0); GLES20.glGenRenderbuffers(1, rb, 0)
        val saved = vp.copyOf()
        try {
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, tx[0])
            GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D, 0, GLES20.GL_RGBA, n, nh, 0, GLES20.GL_RGBA, GLES20.GL_UNSIGNED_BYTE, null)
            GLES20.glBindRenderbuffer(GLES20.GL_RENDERBUFFER, rb[0])
            GLES20.glRenderbufferStorage(GLES20.GL_RENDERBUFFER, GLES20.GL_DEPTH_COMPONENT16, n, nh)
            GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER, fb[0])
            GLES20.glFramebufferTexture2D(GLES20.GL_FRAMEBUFFER, GLES20.GL_COLOR_ATTACHMENT0, GLES20.GL_TEXTURE_2D, tx[0], 0)
            GLES20.glFramebufferRenderbuffer(GLES20.GL_FRAMEBUFFER, GLES20.GL_DEPTH_ATTACHMENT, GLES20.GL_RENDERBUFFER, rb[0])
            if (GLES20.glCheckFramebufferStatus(GLES20.GL_FRAMEBUFFER) != GLES20.GL_FRAMEBUFFER_COMPLETE) return
            GLES20.glViewport(0, 0, n, nh)
            GLES20.glClearColor(0f, 0f, 0f, 0f)
            GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
            val pj = FloatArray(16); val vw = FloatArray(16)
            Matrix.orthoM(pj, 0, -wW / 2, wW / 2, -wH / 2, wH / 2, 1f, 900f)
            val cx = (x0 + x1) / 2; val cz = (z0 + z1) / 2
            Matrix.setLookAtM(vw, 0, cx, 500f, cz, cx, 0f, cz, 0f, 0f, -1f)
            Matrix.multiplyMM(vp, 0, pj, 0, vw, 0)
            fogOn = 0f
            frameUniforms(cx, 500f, cz, 0f, 0f, cx, -100f, cz)
            useProg(0)
            Matrix.setIdentityM(mdl, 0)
            City.farAll?.let { fa -> for (p in fa.parts) p.skips = null; draw(fa, mdl, 1f) }
            for (c in City.chunks) if (c.lazyI < 0 && c.x1 - c.x0 < 900f) c.near?.let { draw(it, mdl, 1f) }   // ruas, praia, parque (sem o anel de morros)
            yardM?.let { draw(it, mdl, 1f) }
            City.lightMeshes[0]?.let { draw(it, mdl, 1f) }
            val bb = java.nio.ByteBuffer.allocateDirect(n * nh * 4).order(java.nio.ByteOrder.nativeOrder())
            GLES20.glReadPixels(0, 0, n, nh, GLES20.GL_RGBA, GLES20.GL_UNSIGNED_BYTE, bb)
            val raw = android.graphics.Bitmap.createBitmap(n, nh, android.graphics.Bitmap.Config.ARGB_8888)
            raw.copyPixelsFromBuffer(bb)
            val fl = android.graphics.Matrix(); fl.preScale(1f, -1f)
            val bmp = android.graphics.Bitmap.createBitmap(raw, 0, 0, n, nh, fl, true)
            raw.recycle()
            mapGen = GlGen.gen; mapBuilt = City.builds
            onMap?.invoke(bmp, floatArrayOf(x0, z0, x1, z1))
        } finally {
            fogOn = 1f
            System.arraycopy(saved, 0, vp, 0, 16)
            useProg(0)
            GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER, 0)
            GLES20.glDeleteFramebuffers(1, fb, 0); GLES20.glDeleteTextures(1, tx, 0); GLES20.glDeleteRenderbuffers(1, rb, 0)
            GLES20.glViewport(0, 0, surfW, surfH)
        }
    }

    /** Etapa 124: pedido de foto de corpo inteiro (menu inicial). */
    @Volatile var fullReq = false
    var onFullBody: ((android.graphics.Bitmap) -> Unit)? = null
    @Volatile var nearKind = 0
    /** Etapa 174: a casa antiga some quando se joga na Cidade 2 (o jogador mora na Casa 1 do Hds) */
    private val homeOn: Boolean get() = !(City.on && City.HDS)
    @Volatile var toast: String? = null
    private var hdsSpawned = false
    private var buyIdx = -1
    @Volatile var nearId = 0
    @Volatile var nearLabel = ""
    private var clothT = 0L
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
    private var uCut = 0
    private var uSpec = 0
    private var uPush = 0
    private var uEye = 0
    private var uRoom = 0
    private var uLight = 0
    private var uSoft = 0

    private val fm = HashMap<Type, Mesh>()
    private val sm = HashMap<Int, Mesh>()
    private val rm = HashMap<String, Mesh>()
    private var skyM: Mesh? = null
    private var cloudM: Mesh? = null
    private val skyPrep = Sky.prepare()   // nuvens calculadas fora da thread do GL
    private var yardM: Mesh? = null
    private var floorM: Mesh? = null
    private var ceilM: Mesh? = null
    private var doorM: Mesh? = null
    private var doorAng = 0f
    private var doorT = 0L
    private val walls = arrayOfNulls<Mesh>(4)
    private var bw = -1
    private var bh = -1
    private var bf = -1
    private var bwl = -1
    private var bTest = false
    private var cityW = -1; private var cityH = -1; private var cityTest = false

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
        precision mediump float;
        varying vec4 vCol; varying vec3 vN; varying vec3 vW; varying vec2 vUV;
        uniform sampler2D uTex; uniform float uAlpha; uniform float uSpec; uniform float uCut;
        uniform vec3 uEye; uniform vec2 uRoom; uniform vec3 uLight; uniform float uSoft; uniform float uFog;
        void main() {
            vec4 t = texture2D(uTex, vUV);
            CUT_LINE
            vec3 base = t.rgb * vCol.rgb;
            float a = t.a * vCol.a * uAlpha;
            if (length(vN) < 0.1) { gl_FragColor = vec4(base, a); return; }
            vec3 n = normalize(vN);
            vec3 L = normalize(vec3(0.45, 1.0, 0.65));
            float diff = max(dot(n, L), 0.0);
            vec3 amb = mix(vec3(0.40, 0.37, 0.36), vec3(0.60, 0.67, 0.78), 0.5 + 0.5 * n.y);
            vec3 pl = uLight - vW;
            float d2 = dot(pl, pl);
            vec3 pL = vec3(0.0); float att = 0.0; float pd = 0.0;
            if (d2 < 1600.0) {   // Etapa 161: luz pontual some além de 40 m (contribuição < 1,5%): economiza conta por pixel
                pL = pl * inversesqrt(max(d2, 0.001));
                att = 1.0 / (1.0 + 0.10 * d2);
                pd = max(dot(n, pL), 0.0) * att;
            }
            float ao = 1.0;
            float side = 1.0 - abs(n.y);
            ao *= mix(1.0, 0.72 + 0.28 * clamp(vW.y * 1.6, 0.0, 1.0), side);
            if (vW.y < 0.12 && n.y > 0.8 && vW.x > 0.0 && vW.x < uRoom.x && vW.z > 0.0 && vW.z < uRoom.y) {
                float e = min(min(vW.x, uRoom.x - vW.x), min(vW.z, uRoom.y - vW.z));
                ao *= 0.78 + 0.22 * smoothstep(0.0, 0.8, e);
            }
            vec3 light = amb + vec3(1.0, 0.96, 0.88) * 0.55 * diff + vec3(1.0, 0.80, 0.52) * 0.85 * pd;
            if (uSoft > 0.5) {
                float m = max(light.r, max(light.g, light.b));
                if (m > 1.05) light *= (1.05 + (m - 1.05) * 0.25) / m;
            }
            vec3 col = base * light * ao;
            if (uSpec > 0.045) {   // Etapa 161: material fosco (quase sem brilho) pula os dois pow() por pixel
                vec3 V = normalize(uEye - vW);
                vec3 H = normalize(L + V);
                float s = pow(max(dot(n, H), 0.0), 42.0) * uSpec;
                float sp2 = 0.0;
                if (att > 0.002) sp2 = pow(max(dot(n, normalize(pL + V)), 0.0), 30.0) * uSpec * 0.5 * att * 3.0;
                col += (s + sp2) * vec3(1.0, 0.97, 0.9);
            }
            // Etapa 121: névoa leve ao longe (a cidade some no horizonte em vez de terminar seca)
            vec3 fd = (vW - uEye) * 0.01;
            float fz = dot(fd, fd);
            if (fz > 1.2) col = mix(col, vec3(0.80, 0.88, 0.96), smoothstep(1.2, 8.0, fz) * 0.8 * uFog);
            gl_FragColor = vec4(col, a);
        }
    """.trimIndent()

    // Etapa 89: dois programas — opaco (sem "discard", o que deixa a GPU do celular descartar pixels escondidos antes de
    // pintar) e recorte (folhas, cabelo). O programa ativo troca só quando a peça pede; os uniformes do quadro são reaplicados.
    private class Loc { var prog = 0; var uMVP = 0; var uModel = 0; var uAlpha = 0; var uTex = 0; var uCut = 0; var uSpec = 0; var uPush = 0
        var uEye = 0; var uRoom = 0; var uLight = 0; var uSoft = 0; var uFog = 0 }
    private val locs = arrayOf(Loc(), Loc())
    private var curProg = 0
    private val frameU = FloatArray(8)       // olho (3), sala (2), luz (3)

    private fun buildProg(l: Loc, fs: String) {
        l.prog = GLES20.glCreateProgram()
        GLES20.glAttachShader(l.prog, sh(GLES20.GL_VERTEX_SHADER, VS))
        GLES20.glAttachShader(l.prog, sh(GLES20.GL_FRAGMENT_SHADER, fs))
        GLES20.glBindAttribLocation(l.prog, 0, "aPos"); GLES20.glBindAttribLocation(l.prog, 1, "aNor")
        GLES20.glBindAttribLocation(l.prog, 2, "aCol"); GLES20.glBindAttribLocation(l.prog, 3, "aUV")
        GLES20.glLinkProgram(l.prog)
        l.uMVP = GLES20.glGetUniformLocation(l.prog, "uMVP"); l.uModel = GLES20.glGetUniformLocation(l.prog, "uModel")
        l.uAlpha = GLES20.glGetUniformLocation(l.prog, "uAlpha"); l.uTex = GLES20.glGetUniformLocation(l.prog, "uTex")
        l.uCut = GLES20.glGetUniformLocation(l.prog, "uCut"); l.uSpec = GLES20.glGetUniformLocation(l.prog, "uSpec")
        l.uPush = GLES20.glGetUniformLocation(l.prog, "uPush"); l.uEye = GLES20.glGetUniformLocation(l.prog, "uEye")
        l.uRoom = GLES20.glGetUniformLocation(l.prog, "uRoom"); l.uLight = GLES20.glGetUniformLocation(l.prog, "uLight")
        l.uSoft = GLES20.glGetUniformLocation(l.prog, "uSoft")
        l.uFog = GLES20.glGetUniformLocation(l.prog, "uFog")
    }

    private fun useProg(i: Int) {
        curProg = i
        resetDrawCache()
        val l = locs[i]
        GLES20.glUseProgram(l.prog)
        prog = l.prog; uMVP = l.uMVP; uModel = l.uModel; uAlpha = l.uAlpha; uTex = l.uTex; uCut = l.uCut; uSpec = l.uSpec; uPush = l.uPush
        uEye = l.uEye; uRoom = l.uRoom; uLight = l.uLight; uSoft = l.uSoft
        GLES20.glUniform1f(l.uFog, fogOn)
        GLES20.glUniform3f(uEye, frameU[0], frameU[1], frameU[2])
        GLES20.glUniform2f(uRoom, frameU[3], frameU[4])
        GLES20.glUniform3f(uLight, frameU[5], frameU[6], frameU[7])
    }

    /** uniformes do quadro (olho, tamanho da sala, luz do teto): guardados para valer nos dois programas */
    private fun frameUniforms(exx: Float, eyy: Float, ezz: Float, rw: Float, rh: Float, lx: Float, ly: Float, lz: Float) {
        frameU[0] = exx; frameU[1] = eyy; frameU[2] = ezz; frameU[3] = rw; frameU[4] = rh; frameU[5] = lx; frameU[6] = ly; frameU[7] = lz
        GLES20.glUniform3f(uEye, exx, eyy, ezz); GLES20.glUniform2f(uRoom, rw, rh); GLES20.glUniform3f(uLight, lx, ly, lz)
    }

    private fun sh(type: Int, src: String): Int {
        val s = GLES20.glCreateShader(type)
        GLES20.glShaderSource(s, src)
        GLES20.glCompileShader(s)
        return s
    }

    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        GlGen.gen++
        GLES20.glClearColor(0.80f, 0.88f, 0.96f, 1f)
        GLES20.glEnable(GLES20.GL_DEPTH_TEST)
        GLES20.glEnable(GLES20.GL_BLEND)
        GLES20.glBlendFunc(GLES20.GL_SRC_ALPHA, GLES20.GL_ONE_MINUS_SRC_ALPHA)
        buildProg(locs[0], FS.replace("CUT_LINE", ""))
        buildProg(locs[1], FS.replace("CUT_LINE", "if (t.a < uCut) discard;"))
        aPos = 0; aNor = 1; aCol = 2; aUV = 3
        useProg(0)
        GLES20.glEnableVertexAttribArray(aPos)
        GLES20.glEnableVertexAttribArray(aNor)
        GLES20.glEnableVertexAttribArray(aCol)
        GLES20.glEnableVertexAttribArray(aUV)
        Tex.init()
        fm.clear()          // móveis do pack: as texturas do contexto antigo não valem mais
        Flora.reset()
        CuteChar.initGl()
        skyM = Sky.dome()
        cloudM = Sky.clouds()   // Etapa 127: céu com degradê real, sol e nuvens
        stageM = AvatarModel.stage()
        avDirty = true
        bw = -1
    }

    override fun onSurfaceChanged(gl: GL10?, w: Int, h: Int) {
        GLES20.glViewport(0, 0, w, h)
        surfW = w; surfH = h
        aspect = w.toFloat() / maxOf(1, h).toFloat()
    }

    // Etapa 122: estado de desenho guardado — só manda ao GL o que mudou (textura, brilho, recorte...).
    // Mesma imagem, bem menos chamadas por quadro (a cidade tem centenas de peças).
    private var dTex = -1; private var dSpec = -1f; private var dSoft = -1f; private var dPush = -99f; private var dCut = -1f; private var dAlpha = -1f
    private fun resetDrawCache() { dTex = -1; dSpec = -1f; dSoft = -1f; dPush = -99f; dCut = -1f; dAlpha = -1f }

    private fun draw(m: Mesh, model: FloatArray, alpha: Float, glass: Boolean = false) {
        var any = false
        for (p in m.parts) if ((p.mat == Mt.GLASS) == glass) { any = true; break }
        if (!any) return
        Matrix.multiplyMM(mvp, 0, vp, 0, model, 0)
        GLES20.glUniformMatrix4fv(uMVP, 1, false, mvp, 0)
        GLES20.glUniformMatrix4fv(uModel, 1, false, model, 0)
        if (alpha != dAlpha) { GLES20.glUniform1f(uAlpha, alpha); dAlpha = alpha }
        for (p in m.parts) {
            if ((p.mat == Mt.GLASS) != glass) continue
            val want = if (p.cut > 0f) 1 else 0
            if (want != curProg) {
                useProg(want)
                GLES20.glUniformMatrix4fv(uMVP, 1, false, mvp, 0)
                GLES20.glUniformMatrix4fv(uModel, 1, false, model, 0)
                GLES20.glUniform1f(uAlpha, alpha); dAlpha = alpha
                GLES20.glActiveTexture(GLES20.GL_TEXTURE0)
                GLES20.glUniform1i(uTex, 0)
            }
            val tx = if (p.tex != 0) p.tex else Tex.ids[p.mat]
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, tx)   // textura sempre (carregamentos no meio do quadro mudam o vínculo)
            val sp = Mt.SPEC[p.mat]
            if (sp != dSpec) { GLES20.glUniform1f(uSpec, sp); dSpec = sp }
            val so = if (p.soft) 1f else 0f
            if (so != dSoft) { GLES20.glUniform1f(uSoft, so); dSoft = so }
            if (p.push != dPush) { GLES20.glUniform1f(uPush, p.push); dPush = p.push }
            if (p.cut != dCut) { GLES20.glUniform1f(uCut, p.cut); dCut = p.cut }
            if (p.cull) GLES20.glEnable(GLES20.GL_CULL_FACE)
            if (p.solid) GLES20.glDisable(GLES20.GL_BLEND)
            val bytes = STRIDE * 4
            if (p.gpu) {
                if (p.vbo == 0 || p.gpuGen != GlGen.gen) {
                    if (!p.upload()) {
                        // Etapa 126: malha só da placa perdida junto com o contexto: pula e pede a cidade de novo
                        if (p.cull) GLES20.glDisable(GLES20.GL_CULL_FACE)
                        if (p.solid) GLES20.glEnable(GLES20.GL_BLEND)
                        City.builtGen = -1
                        continue
                    }
                }
                GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, p.vbo)
                GLES20.glVertexAttribPointer(aPos, 3, GLES20.GL_FLOAT, false, bytes, 0)
                GLES20.glVertexAttribPointer(aNor, 3, GLES20.GL_FLOAT, false, bytes, 12)
                GLES20.glVertexAttribPointer(aCol, 4, GLES20.GL_FLOAT, false, bytes, 24)
                GLES20.glVertexAttribPointer(aUV, 2, GLES20.GL_FLOAT, false, bytes, 40)
                if (p.ibo != 0) {
                    GLES20.glBindBuffer(GLES20.GL_ELEMENT_ARRAY_BUFFER, p.ibo)
                    GLES20.glDrawElements(GLES20.GL_TRIANGLES, p.icount, GLES20.GL_UNSIGNED_SHORT, 0)
                    GLES20.glBindBuffer(GLES20.GL_ELEMENT_ARRAY_BUFFER, 0)
                } else if (p.skips != null) {
                    val sk = p.skips!!
                    var from = 0
                    var k = 0
                    while (k + 1 < sk.size) {
                        if (sk[k] > from) GLES20.glDrawArrays(GLES20.GL_TRIANGLES, from, sk[k] - from)
                        from = max(from, sk[k + 1]); k += 2
                    }
                    if (p.count > from) GLES20.glDrawArrays(GLES20.GL_TRIANGLES, from, p.count - from)
                } else if (p.skipA >= 0 && p.skipB > p.skipA) {
                    if (p.skipA > 0) GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, p.skipA)
                    if (p.count > p.skipB) GLES20.glDrawArrays(GLES20.GL_TRIANGLES, p.skipB, p.count - p.skipB)
                } else {
                    GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, p.count)
                }
                GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, 0)
            } else {
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
            if (p.cull) GLES20.glDisable(GLES20.GL_CULL_FACE)
            if (p.solid) GLES20.glEnable(GLES20.GL_BLEND)
        }
    }

    private fun rebuild() {
        val gw = st.gw
        val gh = st.gh
        val fl = Finish.floors[st.floorIdx]
        val wl = Finish.walls[st.wallIdx]
        yardM?.release(); floorM?.release(); ceilM?.release(); doorM?.release(); for (w in walls) w?.release()   // devolve os buffers da placa de vídeo
        yardM = Models.yard(gw, gh, st.testRoom)
        inBld = null
        // Etapa 151: a cidade só é montada de novo se o tamanho da casa mudou (trocar piso/parede ou voltar do fundo não refaz tudo)
        if (gw != cityW || gh != cityH || st.testRoom != cityTest) {
            cityW = gw; cityH = gh; cityTest = st.testRoom
            City.clear()
            if (!st.testRoom) City.buildAsync(gw, gh)   // Etapa 122: a cidade é montada em segundo plano
        }
        floorM = Models.interior(gw, gh, fl, wl.cor)
        ceilM = Models.ceiling(gw, gh)
        doorM = Models.doorLeaf()
        val W = gw.toDouble()
        val H = gh.toDouble()
        val plan = HouseLayout.active(gw, gh)   // Etapa 144: casa com cômodos — uma janela por cômodo
        walls[0] = Models.wall(W, if (plan) listOf(Opening(2.2, 1.6, false), Opening(8.0, 1.25, false), Opening(11.5, 1.6, false), Opening(15.6, 1.25, false)) else listOf(Opening(W / 2, 1.9, false)), wl.cor, true, false)
        walls[1] = Models.wall(W, listOf(Opening(W / 2, 1.1, true), Opening(W * 0.22, 1.25, false), Opening(W * 0.78, 1.25, false)), wl.cor, true, false)
        walls[2] = Models.wall(H, if (plan) listOf(Opening(H * 0.25, 1.25, false), Opening(H * 0.75, 1.25, false)) else listOf(Opening(H / 2, 1.6, false)), wl.cor, false, false)
        walls[3] = Models.wall(H, if (plan) listOf(Opening(H * 0.25, 1.25, false), Opening(H * 0.75, 1.25, false)) else emptyList(), wl.cor, false, true)
        bw = gw; bh = gh; bf = st.floorIdx; bwl = st.wallIdx; bTest = st.testRoom
        // cortinas simuladas (uma por janela; a cor segue a regra antiga: rosada na metade esquerda, dourada na direita)
        cloth.clear()
        fun cur(wall: Int, c: Double, w: Double, len: Double) =
            cloth.addWindow(wall, c, w, if (c < len / 2) C("#D9786B") else C("#E4B25F"))
        if (plan) { cur(0, 2.2, 1.6, W); cur(0, 11.5, 1.6, W); cur(2, H * 0.25, 1.25, H); cur(2, H * 0.75, 1.25, H); cur(3, H * 0.25, 1.25, H); cur(3, H * 0.75, 1.25, H) }
        else { cur(0, W / 2, 1.9, W); cur(2, H / 2, 1.6, H) }
        cur(1, W * 0.22, 1.25, W); cur(1, W * 0.78, 1.25, W)
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

    // O personagem bate no corpo real do móvel (mais uma folga de 24 cm), e não na casa inteira.
    private fun inside(o: Item, x: Float, z: Float): Boolean {
        val r = o.rect()
        return x > r[0] - 0.24f && x < r[2] + 0.24f && z > r[1] - 0.24f && z < r[3] + 0.24f
    }

    private fun walkable(nx: Float, nz: Float, ox: Float, oz: Float): Boolean {
        val gw = st.gw.toFloat()
        val gh = st.gh.toFloat()
        val inFoot = homeOn && nx > -0.45f && nx < gw + 0.45f && nz > -0.45f && nz < gh + 0.45f
        if (inFoot) {
            val ins = nx > 0.32f && nx < gw - 0.32f && nz > 0.32f && nz < gh - 0.32f
            val door = abs(nx - gw / 2f) < 0.42f && nz > gh - 0.4f && nz < gh + 0.45f
            if (!ins && !door) return false
            if (HouseLayout.blocks(st.gw, st.gh, nx, nz) && !HouseLayout.blocks(st.gw, st.gh, ox, oz)) return false
        } else if (!yardOk(nx, nz)) return false
        else if (homeOn && HouseLayout.yardBlocks(st.gw, st.gh, nx, nz) && !HouseLayout.yardBlocks(st.gw, st.gh, ox, oz)) return false
        if (homeOn && swimPh == 0 && Pool.blocksWalker(st.gw, nx, nz)) return false   // Etapa 118: a água só se entra correndo (mergulho)
        val g = grabbed
        if (homeOn) for (o in st.items) {
            if (o.type.rug || o.type.dyn || o === g || Foot.height(o.type) < 0.12f) continue   // coisa baixinha dá para pisar por cima; objeto solto é empurrado
            if (inside(o, nx, nz) && !inside(o, ox, oz)) return false
        }
        // portas e gavetas abertas (Etapa 83); se já está dentro, deixa sair
        for (b in partBoxes) if (nx > b[0] && nx < b[2] && nz > b[1] && nz < b[3] && !(ox > b[0] && ox < b[2] && oz > b[1] && oz < b[3])) return false
        return true
    }

    /** Etapa 121: dentro do quintal valem os limites de antes; o portão da frente leva à cidade, onde só prédios, muros e carros bloqueiam. */
    private fun yardOk(x: Float, z: Float): Boolean {
        val gw = st.gw.toFloat(); val gh = st.gh.toFloat()
        if (homeOn && x > -6.6f && x < gw + 6.6f && z > Pool.WALK_Z && z < gh + 8.6f) return true
        if (!City.on) return false
        if (abs(x - gw / 2f) < 1.25f && z >= gh + 8.4f && z < gh + 9.8f) return true   // portão
        if (homeOn && x > -7.4f && x < gw + 7.4f && z > -19.4f && z < gh + 9.4f) return false     // cerca do quintal
        if (Elevado.blockedWalk(x, z, baseY)) return false   // Etapa 145: pilares, aterro e guarda-corpo do elevado
        return baseY > 0.45f || !City.blocked(x, z)
    }

    // ================================================================ Etapa 123: dirigir
    /** Veículo do jogador (tipo/cor escolhidos na loja). Fica estacionado na rua em frente de casa. */
    @Volatile var driving = false; private set
    @Volatile var carSpeed = 0f; private set
    private var carX = Float.NaN; private var carZ = 0f; private var carH = 0f   // posição e rumo (rad: frente = (sin h, -cos h))
    private var carY = 0f
    private var carMesh: Mesh? = null
    private var carKey = ""
    private var steerS = 0f
    private var thirdBefore = true
    private var camYawPull = 0f

    /** Loja: "Trazer para casa" — o veículo volta para a vaga em frente de casa. */
    fun resetCar() { if (!driving) carX = Float.NaN }
    private fun isMoto() = st.vehKind == Vehicles.MOTO || st.vehKind == Vehicles.SCOOTER
    private fun carHalfL() = if (isMoto()) 1.05f else if (st.vehKind == Vehicles.TESLA) TeslaCar.HALF_L else if (st.vehKind == Vehicles.VAN || st.vehKind == Vehicles.PICKUP) 2.7f else 2.35f
    private fun carHalfW() = if (isMoto()) 0.45f else if (st.vehKind == Vehicles.TESLA) TeslaCar.HALF_W else 1.0f
    /** Etapa 162: Tesla com rodas e portas animadas (null = outro veículo ou GLB indisponível) */
    private var tesla: TeslaCar? = null
    private var carT0 = 0L

    /** Garante a malha e a vaga do carro; põe na rua em frente de casa na primeira vez. */
    private fun ensureCar() {
        if (st.vehKind < 0 || !City.on) { carMesh?.release(); carMesh = null; tesla = null; carKey = ""; City.ownCar = null; return }
        val key = "${st.vehKind}|${st.vehColor}|${GlGen.gen}"
        if (key != carKey) {
            if (st.vehKind == Vehicles.TESLA && Glb.assets == null) return    // ainda sem assets: tenta de novo no próximo quadro
            carMesh?.release()
            val gm = if (st.vehKind == Vehicles.TESLA) Glb.get("veic_tesla") else null
            if (gm != null) {
                // Etapa 162: o desenho vem do GLB (drawTesla); a malha vazia só marca que existe um veículo
                tesla = TeslaCar(gm); carMesh = Mesh(emptyList())
            } else {
                tesla = null
                val b = MB()
                // sem o GLB do Tesla: sedã branco no lugar
                if (st.vehKind == Vehicles.TESLA) Vehicles.geom(Vehicles.XF(b, 0f, 0f, 0f, 1), Vehicles.SEDAN, 0xFFF5F5F5.toInt())
                else Vehicles.geom(Vehicles.XF(b, 0f, 0f, 0f, 1), st.vehKind, st.vehColor)
                carMesh = b.toMesh(true)
            }
            carKey = key
        }
        if (carX.isNaN()) {
            // vaga junto da calçada, do lado da casa, virado no sentido da mão (-x)
            val zc = if (City.bandZ.size > 9) (City.bandZ[8] + City.bandZ[9]) / 2f else 33f   // Etapa 131: R. das Magnólias, em frente de casa
            carX = st.gw / 2f + 7f; carZ = zc - 2.25f; carH = (-Math.PI / 2).toFloat()
        }
        City.ownCar = if (driving) null else floatArrayOf(carX, carZ, carH, carHalfL(), carHalfW())
    }

    /** O jogador some e assume o veículo; a câmera passa a seguir de trás. */
    private fun enterCar() {
        if (carMesh == null) return
        driving = true; carSpeed = 0f; steerS = 0f; carVx = 0f; carVz = 0f; yawRate = 0f; gasIn = false; brakeIn = false; hbIn = false
        thirdBefore = third; third = true
        path = null; markX = Float.NaN; jumping = false; crouch = false
        flying = false; landing = false; py = 0f; fvx = 0f; fvy = 0f; fvz = 0f
        px = carX; pz = carZ
        fyaw = carH
        City.ownCar = null
    }

    private fun exitCar() {
        driving = false
        City.driverHalf = 0f
        carSpeed = 0f; carVx = 0f; carVz = 0f; yawRate = 0f; gasIn = false; brakeIn = false; hbIn = false
        val rx = cos(carH); val rz = sin(carH)
        // sai pelo lado do motorista (esquerda); se estiver bloqueado, pela direita
        var ok = false
        for (side in floatArrayOf(-1f, 1f)) {
            val ex = carX + rx * side * (carHalfW() + 0.8f); val ez = carZ + rz * side * (carHalfW() + 0.8f)
            val up = carY > 0.45f   // Etapa 145: em cima do elevado, desce do carro na própria pista
            if (!City.on || (if (up) !Elevado.blockedWalk(ex, ez, carY) && !Elevado.surface(ex, ez, carY).isNaN() else !City.blocked(ex, ez))) { px = ex; pz = ez; ok = true; break }
        }
        baseY = carY
        if (!ok) { px = carX - sin(carH) * (carHalfL() + 1f); pz = carZ + cos(carH) * (carHalfL() + 1f) }
        pYaw = Math.toDegrees(carH.toDouble()).toFloat() + 90f
        third = thirdBefore
        City.ownCar = floatArrayOf(carX, carZ, carH, carHalfL(), carHalfW())
    }

    /** Etapa 126: pedais na tela (segurar). */
    @Volatile var gasIn = false
    @Volatile var brakeIn = false
    @Volatile var hbIn = false
    /** marcha mostrada no painel (R, N, 1..6) */
    @Volatile var gear = "N"; private set
    @Volatile var drifting = false; private set
    private var carVx = 0f
    private var carVz = 0f
    private var yawRate = 0f
    private var camRoll = 0f

    /**
     * Etapa 126: direção estilo jogo de corrida (arcade): acelerador e freio/ré nos pedais (ou analógico para cima/baixo),
     * volante no analógico; o carro tem aderência lateral — nas curvas rápidas ou com o freio de mão ele derrapa e volta.
     */
    private fun updateDrive(dt: Float) {
        val moto = isMoto()
        val k = st.vehKind
        val vmax = when (k) { Vehicles.TESLA -> 50f; Vehicles.SPORT -> 52f; Vehicles.MOTO -> 44f; Vehicles.SCOOTER -> 20f; Vehicles.BUS -> 24f; Vehicles.VAN -> 30f; Vehicles.PICKUP -> 38f; else -> 42f }
        val acc = when (k) { Vehicles.TESLA -> 10.5f; Vehicles.SPORT -> 11.5f; Vehicles.MOTO -> 11f; Vehicles.SCOOTER -> 4.5f; Vehicles.BUS -> 3.2f; Vehicles.VAN -> 4.8f; else -> 7.6f }
        val grip = when (k) { Vehicles.TESLA -> 9.2f; Vehicles.SPORT -> 9.5f; Vehicles.MOTO -> 8.5f; Vehicles.BUS, Vehicles.VAN -> 6.5f; else -> 8f }
        val wb = if (moto) 1.45f else if (k == Vehicles.BUS) 5.5f else if (k == Vehicles.TESLA) 2.96f else 2.7f
        val joyT = moveY.coerceIn(-1f, 1f)
        val thr = if (gasIn) 1f else max(0f, joyT)
        val brk = if (brakeIn) 1f else max(0f, -joyT)
        val hb = hbIn
        val fx = sin(carH); val fz = -cos(carH); val rx = cos(carH); val rz = sin(carH)
        // velocidade separada em frente e lado (o carro desliza de lado conforme a aderência)
        var vF = carVx * fx + carVz * fz
        var vS = carVx * rx + carVz * rz
        // motor: força cai perto da final (curva de torque); "marchas" dão pequenos trancos de aceleração
        val sp01 = (abs(vF) / vmax).coerceIn(0f, 1f)
        if (thr > 0.02f) {
            if (vF < -0.4f) vF += 16f * thr * dt                       // estava de ré: freia primeiro
            else vF += acc * (1f - sp01 * sp01) * (0.85f + 0.15f * sin(sp01 * 18.8f).let { it * it }) * thr * dt
        }
        if (brk > 0.02f) {
            if (vF > 0.6f) vF -= 22f * brk * dt                        // freio forte
            else if (thr < 0.02f) vF = max(-11f, vF - 6f * brk * dt)   // parado: ré
        }
        // arrasto do ar + rolagem
        val drag = (0.9f + abs(vF) * 0.018f + if (thr < 0.02f && brk < 0.02f) 1.6f else 0f) * dt
        vF = if (vF > 0f) max(0f, vF - drag) else min(0f, vF + drag)
        if (hb) vF = if (vF > 0f) max(0f, vF - 7f * dt) else min(0f, vF + 7f * dt)
        vF = vF.coerceIn(-11f, vmax)
        // volante: rápido de virar, menos ângulo em alta velocidade (sensibilidade de jogo de corrida)
        val st0 = moveX.coerceIn(-1f, 1f)
        val stIn = st0 * abs(st0) * 0.35f + st0 * 0.65f               // curva de resposta: suave no centro
        val maxSteer = (if (moto) 0.55f else 0.6f) / (1f + abs(vF) / 15f)
        val rate = if (abs(stIn * maxSteer) > abs(steerS)) 7f else 10f      // volta ao centro mais rápido
        steerS += (stIn * maxSteer - steerS) * min(1f, dt * rate)
        // giro: o carro tende ao giro "ideal" do volante; com freio de mão a traseira solta
        val ideal = vF / wb * kotlin.math.tan(steerS) * (if (hb) 1.55f else 1f)
        yawRate += (ideal - yawRate) * min(1f, dt * (if (hb) 3f else 9f))
        carH += yawRate * dt
        // aderência lateral: com freio de mão ou rápido demais na curva, desliza (drift)
        val latGrip = if (hb) 1.3f else grip * (1f - 0.45f * sp01 * min(1f, abs(steerS) * 3f))
        vS *= kotlin.math.exp(-latGrip * dt)
        drifting = abs(vS) > 2.2f && abs(vF) > 6f
        if (drifting) vF -= kotlin.math.sign(vF) * abs(vS) * 0.35f * dt      // derrapar segura um pouco
        // de volta ao mundo, já com a nova direção do carro
        val nfx = sin(carH); val nfz = -cos(carH); val nrx = cos(carH); val nrz = sin(carH)
        carVx = nfx * vF + nrx * vS; carVz = nfz * vF + nrz * vS
        carSpeed = vF
        val nx = carX + carVx * dt; val nz = carZ + carVz * dt
        // Etapa 128: se a batida deixou uma quina do carro dentro de algo, qualquer movimento que AFASTE do obstáculo vale
        // (antes nada era "livre" e o carro ficava travado sem ré nem acelerador)
        val hitNow = carHits(carX, carZ, carH); val hcx = hitCX; val hcz = hitCZ
        if (carFree(nx, nz, carH)) { carX = nx; carZ = nz }
        else if (hitNow > 0 && carHits(nx, nz, carH) <= hitNow && (nx - carX) * (carX - hcx) + (nz - carZ) * (carZ - hcz) > 0f) { carX = nx; carZ = nz }
        else {
            // batida: raspa na parede (desliza no eixo livre) ou quica para trás
            val hard = abs(vF) > 9f
            if (carFree(nx, carZ, carH)) { carX = nx; carVz = 0f }
            else if (carFree(carX, nz, carH)) { carZ = nz; carVx = 0f }
            else { carVx = -carVx * 0.25f; carVz = -carVz * 0.25f; yawRate *= 0.3f }
            carVx *= if (hard) 0.45f else 0.75f; carVz *= if (hard) 0.45f else 0.75f
            if (!carFree(carX, carZ, carH)) carH -= yawRate * dt   // não deixa a quina entrar girando
            carSpeed = carVx * nfx + carVz * nfz
        }
        // ainda preso depois de um instante: empurra para o lugar livre mais perto (sem teletransporte longe)
        if (carHits(carX, carZ, carH) > 0) { stuckT += dt; if (stuckT > 0.4f) { unstickCar(); stuckT = 0f } } else stuckT = 0f
        carY += (groundH(carX, carZ) - carY) * min(1f, dt * 10f)
        px = carX; pz = carZ
        City.driverHalf = carHalfL()
        val kmh = abs(carSpeed) * 3.6f
        gear = when {
            carSpeed < -0.3f -> "R"
            kmh < 1f -> "N"
            else -> (1 + (kmh / (vmax * 3.6f) * 5.6f).toInt()).coerceAtMost(6).toString()
        }
        // câmera: segue a direção em que o carro anda (mostra a derrapagem), mais rápida em alta velocidade
        val mvYaw = if (abs(vF) > 3f && vF > 0f) kotlin.math.atan2(carVx, -carVz) else carH
        var dv = mvYaw - carH
        while (dv > Math.PI) dv -= (2 * Math.PI).toFloat()
        while (dv < -Math.PI) dv += (2 * Math.PI).toFloat()
        val tgt = if (vF < -2f) carH else carH + dv * 0.35f
        var dl = tgt - fyaw
        while (dl > Math.PI) dl -= (2 * Math.PI).toFloat()
        while (dl < -Math.PI) dl += (2 * Math.PI).toFloat()
        if (abs(carSpeed) > 0.5f) fyaw += dl * min(1f, dt * (2.2f + abs(carSpeed) * 0.08f))
        fpitch += (-0.16f - fpitch) * min(1f, dt * 1.5f)
        camRoll += (-yawRate * min(1f, abs(vF) / 20f) * 0.06f - camRoll) * min(1f, dt * 4f)
    }

    // ================================================================ Etapa 128: voar
    private fun toggleFly() {
        if (flying) { beginLanding(); return }
        if (landing) { landing = false; flying = true; return }
        if (!City.on || mode != 0 || sitPh != 0 || swimPh != 0 || usePh != 0 || washPh != 0 || lieK > 0.01f) return
        flying = true; landing = false; jumping = false; crouch = false; path = null; markX = Float.NaN
        flyAlt = baseY + py
        fvx = 0f; fvz = 0f; fvy = if (py < 0.6f) 5f else 0f   // decola com um impulso
    }

    /** chão livre para pousar: o mesmo teste de quem anda (paredes, móveis, carros, mar fundo, cerca do quintal) */
    private fun landOk(x: Float, z: Float) = walkable(x, z, x, z) && !(City.on && !City.inLot(x, z) && City.blocked(x, z))

    private fun findLand(): Boolean {
        if (landOk(px, pz)) { landX = px; landZ = pz; return true }
        var r = 0.6f
        while (r < 90f) {
            val n = max(8, (r * 4f).toInt())
            for (i in 0 until n) {
                val a = 2f * Math.PI.toFloat() * i / n
                val x = px + cos(a) * r; val z = pz + sin(a) * r
                if (landOk(x, z)) { landX = x; landZ = z; return true }
            }
            r += 0.6f
        }
        return false
    }

    private fun beginLanding() {
        flying = false
        if (!findLand()) { landX = px; landZ = pz }
        landing = true
    }

    /** trocou para a vista de cima voando: pousa na hora */
    private fun landNow() {
        flying = false; landing = false
        if (!findLand()) { landX = px; landZ = pz }
        px = landX; pz = landZ; py = 0f; fvx = 0f; fvy = 0f; fvz = 0f; flyTilt = 0f; flySpeed = 0f
    }

    private fun updateFly(dt: Float) {
        pMoving = false
        if (landing) {
            // vai até o ponto livre mais perto e desce devagar no fim
            val dx = landX - px; val dz = landZ - pz; val dl = sqrt(dx * dx + dz * dz)
            val hs = min(dl, (6f + dl * 1.5f) * dt)
            if (dl > 1e-3f) { px += dx / dl * hs; pz += dz / dl * hs; if (third && dl > 0.3f) turnBody(dx, dz, dt) }
            flyAlt = max(groundH(px, pz), flyAlt - min(18f, 1.6f + (flyAlt - groundH(px, pz)) * 1.4f) * dt)
            py = max(0f, flyAlt - baseY)
            flyTilt += (0f - flyTilt) * min(1f, dt * 4f)
            flySpeed = hs / max(dt, 1e-3f)
            if (dl < 0.02f && flyAlt - groundH(px, pz) < 0.02f) { landing = false; py = 0f; fvx = 0f; fvy = 0f; fvz = 0f; flyTilt = 0f; flySpeed = 0f }
            return
        }
        val fx = sin(fyaw); val fz = -cos(fyaw); val rx = cos(fyaw); val rz = sin(fyaw)
        val base = if (turbo) 44f else 11f
        var tx = 0f; var ty = 0f; var tz = 0f
        val mag2 = moveX * moveX + moveY * moveY
        if (mag2 > 0.0004f) {
            val mx = moveX.coerceIn(-1f, 1f); val my = moveY.coerceIn(-1f, 1f)
            // olhando bem para cima ou para baixo, o voo segue o olhar (na 1ª pessoa, sempre)
            val pe = if (!third) fpitch else kotlin.math.sign(fpitch) * max(0f, abs(fpitch) - 0.3f)
            val cp = cos(pe)
            tx = (fx * my * cp + rx * mx) * base; tz = (fz * my * cp + rz * mx) * base
            ty = my * sin(pe) * base
        }
        val vs = if (turbo) 18f else 6.5f
        if (flyUp) ty += vs
        if (flyDown) ty -= vs
        val k = min(1f, dt * (if (turbo) 2.2f else 3.5f))
        fvx += (tx - fvx) * k; fvy += (ty - fvy) * k; fvz += (tz - fvz) * k
        px += fvx * dt; pz += fvz * dt
        if (City.on) { px = px.coerceIn(City.X0 + 2f, City.X1 - 2f); pz = pz.coerceIn(City.Z0 + 2f, City.SEA_Z + 380f) }
        flyAlt += fvy * dt
        val g2 = groundH(px, pz)
        if (flyAlt < g2) { flyAlt = g2; if (fvy < 0f) fvy = 0f }
        if (flyAlt > g2 + 160f) { flyAlt = g2 + 160f; if (fvy > 0f) fvy = 0f }
        py = max(0f, flyAlt - baseY)
        val hsp = sqrt(fvx * fvx + fvz * fvz)
        flySpeed = sqrt(hsp * hsp + fvy * fvy)
        if (!third) pYaw = Math.toDegrees(atan2(sin(fyaw).toDouble(), (-cos(fyaw)).toDouble())).toFloat()
        else if (hsp > 0.6f) turnBody(fvx, fvz, dt)
        // corpo inclina para a frente com a velocidade (pose de super-herói)
        flyTilt += (min(1f, hsp / 30f) * 38f - flyTilt) * min(1f, dt * 3f)
    }

    private fun turnBody(dx: Float, dz: Float, dt: Float) {
        val dir = Math.toDegrees(atan2(dx.toDouble(), dz.toDouble())).toFloat()
        var dl = dir - pYaw
        while (dl > 180f) dl -= 360f
        while (dl < -180f) dl += 360f
        pYaw += dl * min(1f, dt * 8f)
    }

    // ================================================================ Etapa 128: portas que abrem sozinhas
    private val dmdl = FloatArray(16)
    private var cityDoorT = 0L

    private fun updateDoors(ex: Float, ez: Float) {
        val now = System.nanoTime()
        val dt = if (cityDoorT == 0L) 0.016f else ((now - cityDoorT) / 1e9f).coerceIn(0f, 0.05f)
        cityDoorT = now
        for (d in City.doors) {
            val dx = d.x - ex; val dz = d.z - ez
            val d2 = dx * dx + dz * dz
            if (d2 > 105f * 105f) {
                if (d.leaves != null && d2 > 125f * 125f) d.leaves = null
                d.open = 0f; d.spinV = 0f
                continue
            }
            val auto = Doors.automatic(d.style)
            val reach = if (auto) 2.9f else 1.75f
            val qx = px - d.x; val qz = pz - d.z
            var near = !driving && py < 2.2f && qx * qx + qz * qz < reach * reach
            if (!near && auto) for (p in City.peds) { val a = p.x - d.x; val b = p.z - d.z; if (a * a + b * b < 2.3f * 2.3f) { near = true; break } }
            if (Doors.revolving(d.style)) {
                d.spinV += ((if (near) 60f else 0f) - d.spinV) * min(1f, dt * 1.6f)
                d.spin = (d.spin + d.spinV * dt) % 360f
            } else {
                val sp = if (auto) 1.7f else 2.3f
                d.open = if (near) min(1f, d.open + dt * sp) else max(0f, d.open - dt * sp * 0.7f)
            }
        }
    }

    private fun drawDoors(ex: Float, ez: Float, glass: Boolean) {
        val ib = if (mode == 1) inBld else null
        var built = 0
        for (d in City.doors) {
            val dx = d.x - ex; val dz = d.z - ez
            if (dx * dx + dz * dz > 100f * 100f) continue
            val r = if (Doors.revolving(d.style)) Doors.drumR(d.w) + 0.1f else d.w + 0.1f
            if (!boxVisible(d.x - r, d.y, d.z - r, d.x + r, d.y + d.h + 0.1f, d.z + r)) continue
            if (ib != null && d.x > ib.x0 && d.x < ib.x1 && d.z > ib.z0 - 0.6f && d.z < ib.z1 + 0.6f) continue   // vista de cima dentro do prédio
            var ls = d.leaves
            if (ls == null) {
                if (glass || built >= 6) continue      // monta poucas por quadro (sem engasgo ao chegar num bairro)
                ls = Doors.leaves(d); d.leaves = ls; built++
            }
            val k = d.open * d.open * (3f - 2f * d.open)
            for (l in ls) { Doors.leafMatrix(dmdl, d, l, k); draw(l.mesh, dmdl, 1f, glass) }
        }
        Matrix.setIdentityM(mdl, 0)
    }

    private var stuckT = 0f
    private var hitCX = 0f; private var hitCZ = 0f

    /** quantos pontos do contorno do carro estão dentro de algo; guarda o centro deles (para saber o lado do obstáculo) */
    private fun carHits(x: Float, z: Float, h: Float): Int {
        if (!City.on) return 0
        val fx = sin(h); val fz = -cos(h); val rx = cos(h); val rz = sin(h)
        val hl = carHalfL(); val hw = carHalfW()
        var n = 0; var sx = 0f; var sz = 0f
        for (a in floatArrayOf(-hl, -hl * 0.5f, 0f, hl * 0.5f, hl)) for (b in floatArrayOf(-hw, 0f, hw)) {
            if (b == 0f && a != -hl && a != hl) continue
            val qx = x + fx * a + rx * b; val qz = z + fz * a + rz * b
            if (City.inLot(qx, qz) || (carY < 0.9f && City.blocked(qx, qz)) || Elevado.blockedCar(qx, qz, carY)) { n++; sx += qx; sz += qz }
        }
        if (n > 0) { hitCX = sx / n; hitCZ = sz / n }
        return n
    }

    private fun unstickCar() {
        var r = 0.2f
        while (r < 6f) {
            for (i in 0 until 16) {
                val a = 2f * Math.PI.toFloat() * i / 16
                val x = carX + cos(a) * r; val z = carZ + sin(a) * r
                if (carFree(x, z, carH)) { carX = x; carZ = z; carVx *= 0.2f; carVz *= 0.2f; yawRate = 0f; return }
            }
            r += 0.2f
        }
    }

    private fun carFree(x: Float, z: Float, h: Float): Boolean = carHits(x, z, h) == 0

    private val teslaBase = FloatArray(16)

    /** Etapa 162: Tesla — rodas giram com a velocidade, as da frente esterçam com o volante, a porta mais perto abre quando você chega. */
    private fun drawTesla(t: TeslaCar) {
        val tn = System.nanoTime()
        val dt = if (carT0 == 0L) 0.016f else ((tn - carT0) / 1e9f).coerceIn(0f, 0.1f)
        carT0 = tn
        val a = Math.PI.toFloat() - carH
        val dx = px - carX; val dz = pz - carZ
        val lx = dx * cos(a) - dz * sin(a); val lz = dx * sin(a) + dz * cos(a)
        t.update(dt, driving, lx, lz, if (driving) carSpeed else 0f, if (driving) yawRate else 0f)
        t.g.ensureGl()
        Matrix.setIdentityM(teslaBase, 0)
        Matrix.translateM(teslaBase, 0, carX, if (driving || carY > 0.45f) carY else groundH(carX, carZ), carZ)
        Matrix.rotateM(teslaBase, 0, 180f - Math.toDegrees(carH.toDouble()).toFloat(), 0f, 1f, 0f)
        if (t.pitch != 0f) Matrix.rotateM(teslaBase, 0, t.pitch, 1f, 0f, 0f)     // acelera: frente sobe (pitch < 0); freia: frente mergulha
        if (t.lean != 0f) Matrix.rotateM(teslaBase, 0, t.lean, 0f, 0f, 1f)
        t.pose(teslaBase, if (driving) -Math.toDegrees(steerS.toDouble()).toFloat() else 0f)
        val nodes = t.g.nodes
        for (i in nodes.indices) {
            val ms = nodes[i].mesh ?: continue
            draw(ms, t.world(i), 1f)                                                   // opaco agora
            if (ms.parts.any { it.mat == Mt.GLASS }) carGlassQ.add(Pair(ms, t.world(i).copyOf()))   // vidros no fim do quadro
        }
        Matrix.setIdentityM(mdl, 0)
    }
    private val carGlassQ = ArrayList<Pair<Mesh, FloatArray>>()

    private fun drawOwnCar() {
        val m = carMesh ?: return
        if (carX.isNaN()) return
        if (!boxVisible(carX - 6f, 0f, carZ - 6f, carX + 6f, 3.5f, carZ + 6f)) return
        tesla?.let { drawTesla(it); return }
        Matrix.setIdentityM(mdl, 0)
        Matrix.translateM(mdl, 0, carX, if (driving || carY > 0.45f) carY else groundH(carX, carZ), carZ)
        Matrix.rotateM(mdl, 0, 180f - Math.toDegrees(carH.toDouble()).toFloat(), 0f, 1f, 0f)
        if (driving && isMoto()) Matrix.rotateM(mdl, 0, -steerS * min(1f, abs(carSpeed) / 8f) * 40f, 0f, 0f, 1f)   // moto inclina na curva
        draw(m, mdl, 1f)
        Matrix.setIdentityM(mdl, 0)
    }

    // ================================================================ Etapa 122: cidade
    private var inBld: City.Bld? = null
    private val cityGlass = ArrayList<Mesh>()
    private val farHide = ArrayList<HashMap<Int, IntArray>>()
    private var routeMesh: Mesh? = null
    private var routeVer = -1
    private var beaconMesh: Mesh? = null

    /** Jogador entrou/saiu de uma construção: paredes de cima, telhado e placas dela deixam de ser desenhados. */
    private fun setInside(b: City.Bld?) {
        if (b === inBld) return
        inBld?.let { applySkip(it, false) }
        inBld = b
        b?.let { applySkip(it, true) }
    }

    /** Etapa 126: prédio da cidade em que o jogador está (para a câmera de 3ª pessoa não atravessar a parede). */
    private var camBld: City.Bld? = null

    private fun applySkip(b: City.Bld, on: Boolean) {
        val c = City.chunks.getOrNull(b.chunk) ?: return
        for ((mat, r) in b.ranges) {
            val pi = c.nearIdx[mat] ?: continue
            val p = c.near?.parts?.getOrNull(pi) ?: continue
            if (on) { p.skipA = r[0]; p.skipB = r[1] } else { p.skipA = -1; p.skipB = -1 }
        }
    }

    /** Desenha a cidade: quarteirões perto em detalhe, longe simplificados; semáforos, veículos, pedestres, brinquedos. */
    private fun drawCity(ex: Float, ez: Float) {
        City.service(ex, ez)
        setInside(if (mode == 1 && !driving) City.bldAt(px, pz) else null)   // Etapa 126: paredes e teto só somem na vista de cima
        inBld?.let { applySkip(it, true) }   // a malha detalhada pode ter sido recarregada
        cityGlass.clear()
        Matrix.setIdentityM(mdl, 0)
        val ib = inBld
        for ((ci, c) in City.chunks.withIndex()) {
            val dx = max(0f, max(c.x0 - ex, ex - c.x1)); val dz = max(0f, max(c.z0 - ez, ez - c.z1))
            val d2 = dx * dx + dz * dz
            if (d2 > 245f * 245f) continue
            if (!boxVisible(c.x0, -0.6f, c.z0, c.x1, c.h, c.z1)) continue
            val wantNear = d2 < City.NEAR * City.NEAR || (c.far == null && c.farRanges == null) || (ib != null && ib.chunk == ci)
            val nm = c.near
            if (wantNear && nm != null) {
                draw(nm, mdl, 1f); if (c.glass) cityGlass.add(nm)
                c.farRanges?.let { farHide.add(it) }   // a versão de longe dele sai da malha única
            } else if (c.farRanges == null) { val fm = c.far ?: nm ?: continue; draw(fm, mdl, 1f) }
        }
        // Cidade 2: telhado/forro de cada casa (some quando o jogador está dentro dela na vista de cima)
        if (City.HDS) for (rf in Hds.roofs) {
            val rm = rf.mesh ?: continue
            val dx = max(0f, max(rf.x0 - ex, ex - rf.x1)); val dz = max(0f, max(rf.z0 - ez, ez - rf.z1))
            if (dx * dx + dz * dz > 245f * 245f) continue
            if (mode == 1 && !driving && px > rf.x0 && px < rf.x1 && pz > rf.z0 && pz < rf.z1) continue
            if (!boxVisible(rf.x0, -0.6f, rf.z0, rf.x1, 12f, rf.z1)) continue
            draw(rm, mdl, 1f)
        }
        // quarteirões vistos de longe: uma malha só, pulando os que já foram desenhados em detalhe
        City.farAll?.let { fa ->
            for ((pi, p) in fa.parts.withIndex()) {
                val mat = p.mat
                val list = ArrayList<IntArray>()
                for (r in farHide) r[mat]?.let { list.add(it) }
                if (list.isEmpty()) { p.skips = null; continue }
                list.sortBy { it[0] }
                val arr = IntArray(list.size * 2)
                for ((k, it) in list.withIndex()) { arr[k * 2] = it[0]; arr[k * 2 + 1] = it[1] }
                p.skips = arr
            }
            draw(fa, mdl, 1f)
        }
        farHide.clear()
        City.lightMeshes[City.lightPhase]?.let { draw(it, mdl, 1f) }
        updateDoors(ex, ez)
        drawDoors(ex, ez, false)
        val cm = Vehicles.meshes
        for (car in City.cars) {
            val dx = car.x - ex; val dz = car.z - ez
            if (dx * dx + dz * dz > 150f * 150f) continue
            if (!boxVisible(car.x - 6f, 0f, car.z - 6f, car.x + 6f, 3.4f, car.z + 6f)) continue
            val m = cm.getOrNull(car.mesh) ?: continue
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, car.x, Town.terrain(car.x, car.z), car.z)
            Matrix.rotateM(mdl, 0, car.yaw, 0f, 1f, 0f)
            draw(m, mdl, 1f)
        }
        for (d in CityFun.dyn) {
            val dx = d.x - ex; val dz = d.z - ez
            if (dx * dx + dz * dz > 230f * 230f) continue
            draw(d.mesh, d.m, 1f)
        }
        drawOwnCar()
        // Etapa 158: carpas e patos nadando no lago do parque
        run { val sm = TownPark.swimMesh; val tt = (System.nanoTime() / 1_000_000L % 3_600_000L) / 1000f
            for (sw in TownPark.swimmers) {
                val dx = sw.cx - ex; val dz = sw.cz - ez
                if (dx * dx + dz * dz > 90f * 90f) continue
                val mesh = sm.getOrNull(sw.mesh) ?: continue
                val a = sw.ph + tt * sw.spd / sw.rad
                val x = sw.cx + cos(a) * sw.rad; val z = sw.cz + sin(a) * sw.rad
                val sg = if (sw.spd >= 0f) 1f else -1f
                val yaw = Math.toDegrees(atan2((-sin(a) * sg).toDouble(), (cos(a) * sg).toDouble())).toFloat() + (if (sw.mesh < 6) sin(tt * 5f + sw.ph * 7f) * 9f else 0f)
                Matrix.setIdentityM(pmdl, 0)
                Matrix.translateM(pmdl, 0, x, sw.y + (if (sw.mesh >= 6) sin(tt * 2f + sw.ph) * 0.015f else 0f), z)
                Matrix.rotateM(pmdl, 0, yaw, 0f, 1f, 0f)
                draw(mesh, pmdl, 1f)
            } }
        val pb = City.pedBody; val pl = City.pedLeg; val pa = City.pedArm
        for (p in City.peds) {
            val dx = p.x - ex; val dz = p.z - ez
            if (dx * dx + dz * dz > 45f * 45f) continue
            if (!boxVisible(p.x - 0.5f, 0f, p.z - 0.5f, p.x + 0.5f, 2f, p.z + 0.5f)) continue
            val body = pb.getOrNull(p.look) ?: continue
            val sw = sin(p.ph) * 28f * min(1f, p.v / 0.6f)
            val bob = abs(cos(p.ph)) * 0.03f * min(1f, p.v / 0.6f)
            Matrix.setIdentityM(pmdl, 0)
            Matrix.translateM(pmdl, 0, p.x, City.CURB + bob + Town.terrain(p.x, p.z), p.z)
            Matrix.rotateM(pmdl, 0, p.yaw, 0f, 1f, 0f)
            draw(body, pmdl, 1f)
            for (side in 0..1) {
                val sg = if (side == 0) 1f else -1f
                pl.getOrNull(p.look)?.let { lg ->
                    System.arraycopy(pmdl, 0, mdl, 0, 16)
                    Matrix.translateM(mdl, 0, 0.1f * sg, 0.88f, 0f)
                    Matrix.rotateM(mdl, 0, sw * sg, 1f, 0f, 0f)
                    draw(lg, mdl, 1f)
                }
                pa.getOrNull(p.look)?.let { ar ->
                    System.arraycopy(pmdl, 0, mdl, 0, 16)
                    Matrix.translateM(mdl, 0, 0.27f * sg, 1.42f, 0f)
                    Matrix.rotateM(mdl, 0, -sw * sg * 0.8f, 1f, 0f, 0f)
                    draw(ar, mdl, 1f)
                }
            }
        }
        Matrix.setIdentityM(mdl, 0)
    }

    /** Passe transparente da cidade: mar, vidros das construções perto, faixa do GPS e farol do destino. */
    private fun drawCityGlass(ex: Float, ey: Float, ez: Float) {
        if (!City.on) return
        if (!City.HDS && boxVisible(City.X0 - 500f, -1f, City.SEA_Z - 6f, City.X1 + 500f, 0.5f, City.SEA_Z + 450f)) {
            Water.drawSea(vp, ex, ey, ez, City.X0 - 500f, City.SEA_Z - 6f, City.X1 + 500f, City.SEA_Z + 450f, st.gw)
            useProg(curProg)
        }
        // Etapa 127: lagos com água de verdade
        for (lk in City.lakes) {
            val dx = lk[0] - ex; val dz = lk[1] - ez
            if (dx * dx + dz * dz > 220f * 220f) continue
            val lr = kotlin.math.abs(lk[2])
            if (!boxVisible(lk[0] - lr, lk[3] - 1f, lk[1] - lr, lk[0] + lr, lk[3] + 0.5f, lk[1] + lr)) continue
            Water.drawLake(vp, ex, ey, ez, lk[0], lk[1], lk[2], lk[3])
            useProg(curProg)
        }
        Matrix.setIdentityM(mdl, 0)
        // Etapa 127: sombras do sol (grava profundidade: sombras sobrepostas no mesmo plano não escurecem em dobro)
        Shade.mesh?.let { GLES20.glDepthMask(true); draw(it, mdl, 1f, true); GLES20.glDepthMask(false) }
        for (m in cityGlass) draw(m, mdl, 1f, true)
        drawDoors(ex, ez, true)
        if (Gps.ver != routeVer) {
            routeVer = Gps.ver
            routeMesh?.release(); routeMesh = null
            val r = Gps.route
            if (Gps.active && r.size >= 4) {
                val b = MB(); b.m(Mt.GLASS)
                val n = r.size / 2
                var acc = 0f
                for (i in 0 until n - 1) {
                    val ax = r[i * 2]; val az = r[i * 2 + 1]; val bx = r[i * 2 + 2]; val bz = r[i * 2 + 3]
                    val len = kotlin.math.hypot(bx - ax, bz - az)
                    if (len < 0.05f) continue
                    val ux = (bx - ax) / len; val uz = (bz - az) / len
                    val nx = -uz * 0.6f; val nz = ux * 0.6f
                    val steps = max(1, (len / 1.5f).toInt())
                    for (k in 0 until steps) {
                        val t0 = k.toFloat() / steps; val t1 = (k + 1).toFloat() / steps
                        val x0 = ax + (bx - ax) * t0; val z0 = az + (bz - az) * t0; val x1 = ax + (bx - ax) * t1; val z1 = az + (bz - az) * t1
                        val y0 = groundH(x0, z0) + 0.06f; val y1 = groundH(x1, z1) + 0.06f
                        b.al = 0.78f
                        CityGeo.q(b, CityGeo.P(x0 - nx, y0, z0 - nz) + CityGeo.P(x0 + nx, y0, z0 + nz) + CityGeo.P(x1 + nx, y1, z1 + nz) + CityGeo.P(x1 - nx, y1, z1 - nz), C("#29B6F6"), false)
                        // setinhas brancas apontando o caminho
                        val sAt = acc + len * t0
                        if ((sAt % 5f) < (len / steps)) {
                            b.al = 0.95f
                            val cx = x0 + ux * 0.2f; val cz = z0 + uz * 0.2f
                            CityGeo.q(b, CityGeo.P(cx - nx * 0.7f, y0 + 0.005f, cz - nz * 0.7f) + CityGeo.P(cx + ux * 0.55f, y0 + 0.005f, cz + uz * 0.55f) + CityGeo.P(cx + ux * 0.55f, y0 + 0.005f, cz + uz * 0.55f) + CityGeo.P(cx + ux * 0.2f, y0 + 0.005f, cz + uz * 0.2f), C("#FFFFFF"), false)
                            CityGeo.q(b, CityGeo.P(cx + nx * 0.7f, y0 + 0.005f, cz + nz * 0.7f) + CityGeo.P(cx + ux * 0.2f, y0 + 0.005f, cz + uz * 0.2f) + CityGeo.P(cx + ux * 0.55f, y0 + 0.005f, cz + uz * 0.55f) + CityGeo.P(cx + ux * 0.55f, y0 + 0.005f, cz + uz * 0.55f), C("#FFFFFF"), false)
                        }
                    }
                    acc += len
                }
                b.al = 1f
                routeMesh = b.toMesh(true)
            }
        }
        if (Gps.active) {
            routeMesh?.let { Matrix.setIdentityM(mdl, 0); draw(it, mdl, 1f, true) }
            if (beaconMesh == null) {
                val b = MB(); b.m(Mt.GLASS)
                b.al = 0.28f; b.cyl(0f, 0f, 0f, 1.1f, 1.1f, 40f, C("#4FC3F7"), false, 18)
                b.al = 0.6f; b.cyl(0f, 0f, 0f, 2.2f, 2.2f, 0.06f, C("#29B6F6"), false, 24)
                b.al = 0.9f; b.cyl(0f, 0.07f, 0f, 1.3f, 1.3f, 0.04f, C("#FFFFFF"), false, 24)
                b.al = 1f
                beaconMesh = b.toMesh(true)
            }
            beaconMesh?.let {
                Matrix.setIdentityM(mdl, 0)
                Matrix.translateM(mdl, 0, Gps.destX, groundH(Gps.destX, Gps.destZ) + 0.02f, Gps.destZ)
                draw(it, mdl, 1f, true)
            }
        }
        Matrix.setIdentityM(mdl, 0)
    }

    private val pmdl = FloatArray(16)

    /** Vista aérea: manda o personagem andar até o ponto (x, z) do chão (chamado pela thread de toque). */
    fun walkTo(x: Float, z: Float) { walkReq = floatArrayOf(x, z) }

    /** Cancela a caminhada em andamento. */
    fun stopWalk() { stopReq = true }

    /** Ao voltar para a câmera de perto, a câmera fica atrás do personagem, olhando para onde ele está virado. */
    /** Etapa 126: área da casa e do quintal (onde vale a grade de caminho e a câmera aérea da casa). */
    private fun atHome(x: Float, z: Float): Boolean {
        val gw = st.gw.toFloat(); val gh = st.gh.toFloat()
        return homeOn && x > -6.6f && x < gw + 6.6f && z > Pool.WALK_Z && z < gh + 8.6f
    }
    /** Etapa 126: vista aérea na rua: a câmera segue o personagem pela cidade. */
    private fun cityAer() = mode == 1 && City.on && !atHome(px, pz)
    val streetAerial: Boolean get() = cityAer()
    private var acx = Float.NaN
    private var acz = 0f

    fun faceCameraBehindPlayer() {
        fyaw = (Math.PI - Math.toRadians(pYaw.toDouble())).toFloat()
        fpitch = -0.06f
    }

    /** Ponto bloqueado para o personagem (parede, móvel, fora da casa/porta); sem a exceção "já estava dentro" de [walkable]. */
    private fun blockedAt(x: Float, z: Float): Boolean {
        val gw = st.gw.toFloat()
        val gh = st.gh.toFloat()
        val inFoot = homeOn && x > -0.45f && x < gw + 0.45f && z > -0.45f && z < gh + 0.45f
        if (inFoot) {
            val ins = x > 0.32f && x < gw - 0.32f && z > 0.32f && z < gh - 0.32f
            val door = abs(x - gw / 2f) < 0.42f && z > gh - 0.4f && z < gh + 0.45f
            if (!ins && !door) return true
            if (HouseLayout.blocks(st.gw, st.gh, x, z)) return true   // Etapa 144: paredes internas
        } else if (!yardOk(x, z)) return true   // fora do quintal (ou prédio/carro da cidade)
        else if (homeOn && HouseLayout.yardBlocks(st.gw, st.gh, x, z)) return true
        if (homeOn && Pool.blocksWalker(st.gw, x, z)) return true   // Etapa 118: piscina
        if (homeOn) for (o in st.items) {
            if (o.type.rug || o.type.dyn || Foot.height(o.type) < 0.12f) continue
            if (inside(o, x, z)) return true
        }
        for (b in partBoxes) if (x > b[0] && x < b[2] && z > b[1] && z < b[3]) return true
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
        val x0 = -6.6f   // a grade cobre a casa e o quintal
        val z0 = Pool.WALK_Z   // Etapa 118: fundos do quintal maiores
        val nx = ((gw + 13.2f) / res).toInt() + 1
        val nz = ((gh + 8.6f - Pool.WALK_Z) / res).toInt() + 1
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
        if (cityAer() && !atHome(tx, tz)) {
            // na cidade: vai em linha reta até o ponto (para se esbarrar em algo)
            path = arrayListOf(floatArrayOf(tx, tz)); markX = tx; markZ = tz; return
        }
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
        var budget = (if (pRun) RUN_SPEED else WALK_SPEED) * dt
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
        City.update(dt, px, pz)   // Etapa 121: trânsito e pedestres
        if (!posInit && !homeOn) {
            val sp = Hds.spawn()
            if (sp != null) {
                px = sp[0]; pz = sp[1]; posInit = true; hdsSpawned = true
                pYaw = 180f
                fyaw = 0f
            }
        }
        if (!homeOn && st.money < HdsEstate.INFINITE / 2) st.money = HdsEstate.INFINITE   // dinheiro infinito por enquanto
        if (!posInit && homeOn) {
            px = st.gw / 2f
            pz = st.gh - 0.9f
            posInit = true
            pYaw = Math.toDegrees(atan2(sin(fyaw).toDouble(), (-cos(fyaw)).toDouble())).toFloat()
        }
        if (!sleepChecked && CuteChar.ready) {
            sleepChecked = true
            if (sitPh == 0) st.items.firstOrNull { it.sleep.isNotEmpty() }?.let { o ->
                val seat = o.sleep; o.sleep = ""
                startSit(o, seat, true, true)
                if (sitPh == 10) o.sleep = seat
            }
        }
        ensureCar()
        if (driving) { if (mode != 0) mode = 0; updateDrive(dt); return }
        // Etapa 128: voo
        if (flyReq) { flyReq = false; toggleFly() }
        if (flying || landing) {
            if (mode != 0) landNow() else { updateFly(dt); return }
        }
        if (stopReq) { stopReq = false; path = null; markX = Float.NaN }
        val req = walkReq
        if (req != null) { walkReq = null; if (mode == 1) startWalk(req[0], req[1]) }
        if (mode != 0 && mode != 1) { jumpReq = false; jumping = false; py = 0f; vy = 0f; flying = false; landing = false; return }
        if (sitPh != 0) { jumpReq = false; updateSit(dt); return }
        if (washPh != 0) { jumpReq = false; updateWash(dt); return }
        if (usePh != 0) { jumpReq = false; updateUse(dt); return }
        if (swimPh != 0) { swimJump = jumpReq; jumpReq = false; path = null; markX = Float.NaN; updateSwim(dt); swimJump = false; return }   // Etapa 118: mergulho / nado
        // Etapa 119: pulo olhando para a piscina, perto da borda = mergulho
        if (jumpReq && mode == 0 && !crouch && !jumping && tryDive(true)) { jumpReq = false; return }
        // pulo
        if (jumpReq && mode == 0 && crouch) { jumpReq = false; crouch = false }
        if (jumpReq && mode == 0) {
            jumpReq = false
            if (!jumping && py <= 0.001f && vy <= 0f) {
                jumping = true; jumpLaunched = false; jumpT = 0f
                jumpRun = pRun && pMoving
                jumpPre = if (jumpRun) 0f else JUMP_PRE   // pulo parado: agacha um instante antes de sair do chão
            }
        } else jumpReq = false
        if (jumping) {
            jumpT += dt
            if (!jumpLaunched && jumpT >= jumpPre) { jumpLaunched = true; vy = 3.9f }
            if (jumpLaunched) {
                vy -= 11f * dt
                py += vy * dt
                if (py <= 0f) { py = 0f; vy = 0f }
            }
            val clipLen = CuteChar.clipSeconds(if (jumpRun) CuteChar.RUNJUMP else CuteChar.JUMP)
            // depois de pousar, termina a recuperação do clipe; se o jogador andar, volta logo ao andar/correr
            if (jumpLaunched && py <= 0f && (jumpT >= clipLen * 0.999f || (pMoving && jumpT > jumpPre + 0.8f))) jumping = false
        }
        val joyOn = moveX * moveX + moveY * moveY > 0.0004f
        if (mode == 1 && !(cityAer() && joyOn)) { followPath(dt); return }
        if (path != null) { path = null; markX = Float.NaN }   // câmera de perto (ou analógico na rua): o analógico manda
        pMoving = false
        if (moveX * moveX + moveY * moveY <= 0.0004f) pRun = false
        val mx = moveX
        val my = moveY
        val mag2 = mx * mx + my * my
        if (!third) {
            // 1ª pessoa: o corpo vira junto com o olhar
            pYaw = Math.toDegrees(atan2(sin(fyaw).toDouble(), (-cos(fyaw)).toDouble())).toFloat()
        }
        if (mag2 > 0.0004f) {
            val mag = sqrt(mag2)
            // histerese: corre com o analógico quase no limite; solta abaixo disso e volta a andar
            pRun = if (crouch) false else if (pRun) mag > 0.70f else mag > 0.88f
            // andar: velocidade proporcional ao arrasto (como antes); correr: velocidade fixa (casada com o clipe)
            val sp = if (crouch) CROUCH_SPEED * dt else if (pRun) RUN_SPEED * dt / mag else WALK_SPEED * dt  // casado com o passo da animação (CuteChar.WALK_RATE / RUN)
            val fyw = if (mode == 1) -yaw else fyaw   // vista aérea: o analógico segue a direção da câmera
            val fx = sin(fyw)
            val fz = -cos(fyw)
            val rx = cos(fyw)
            val rz = sin(fyw)
            val dx = (fx * my + rx * mx) * sp
            val dz = (fz * my + rz * mx) * sp
            if (walkable(px + dx, pz, px, pz)) px += dx
            if (walkable(px, pz + dz, px, pz)) pz += dz
            pMoving = true
            val dir = Math.toDegrees(atan2(dx.toDouble(), dz.toDouble())).toFloat()
            var dl = dir - pYaw
            while (dl > 180f) dl -= 360f
            while (dl < -180f) dl += 360f
            if (third || mode == 1) pYaw += dl * min(1f, dt * 12f)
            // Etapa 119: andando (sem correr) contra a água por um instante: senta na borda e entra na piscina
            if (!pRun && !crouch && mode == 0 && Pool.blocksWalker(st.gw, px + dx * 2f, pz + dz * 2f)) {
                edgeHold += dt
                if (edgeHold >= Pool.EDGE_HOLD) { edgeHold = 0f; trySitEdge() }
            } else edgeHold = 0f
            if (pRun && mode == 0) tryDive(false)   // Etapa 118: correndo em direção à piscina
        }
    }

    // ------------------------------------------------------------ Etapa 118: piscina

    /** Correndo em direção à água e perto o bastante: começa o mergulho (Run_To_Dive) sozinho. */
    private fun tryDive(force: Boolean): Boolean {
        if (swimPh != 0 || jumping || crouch || py > 0.001f || !CuteChar.ready || !CuteChar.hasPool()) return false
        val gw = st.gw
        val yr = Math.toRadians(pYaw.toDouble())
        val dx = sin(yr).toFloat(); val dz = cos(yr).toFloat()
        var tmin = 0f; var tmax = 1e9f
        val x0 = Pool.x0(gw); val x1 = Pool.x1(gw)
        if (abs(dx) < 1e-5f) { if (px < x0 || px > x1) return false }
        else { var ta = (x0 - px) / dx; var tb = (x1 - px) / dx; if (ta > tb) { val q = ta; ta = tb; tb = q }; tmin = max(tmin, ta); tmax = min(tmax, tb) }
        if (abs(dz) < 1e-5f) { if (pz < Pool.Z0 || pz > Pool.Z1) return false }
        else { var ta = (Pool.Z0 - pz) / dz; var tb = (Pool.Z1 - pz) / dz; if (ta > tb) { val q = ta; ta = tb; tb = q }; tmin = max(tmin, ta); tmax = min(tmax, tb) }
        if (tmin <= 0.05f || tmin > tmax) return false                   // já dentro, atrás ou fora da linha
        val hs = CuteChar.bodyScale()
        val start = Pool.DIVE_START * hs
        if (tmin > start) return false                                  // ainda longe
        var skip = start - tmin                                     // perto da água: entra no meio do clipe (sem teletransporte)
        if (force) skip = min(skip, 1.4f * hs)                      // pulo parado: o mergulho começa no começo do clipe
        else if (skip > 2.2f * hs) return false                     // perto demais: não dá tempo de mergulhar, para na borda
        // o ponto de chegada precisa ficar dentro da água (nada de mergulhar em cima da quina)
        val ex = px + dx * (tmin + 0.9f * hs); val ez = pz + dz * (tmin + 0.9f * hs)
        if (!Pool.inWater(gw, ex, ez, 0.1f)) return false
        swDX = dx; swDZ = dz; swYaw = pYaw
        swX = px - dx * skip; swZ = pz - dz * skip                  // onde o quadril estaria no 1º quadro do clipe
        swimT = Pool.diveTimeAt(skip / hs)
        swimPh = 1; pMoving = false
        return true
    }

    /** Etapa 119: andando contra a borda da água: senta na borda (pernas para a água) e depois entra. */
    private fun trySitEdge() {
        if (swimPh != 0 || jumping || crouch || py > 0.001f || !CuteChar.ready || !CuteChar.hasPool() || !CuteChar.hasSit()) return
        val gw = st.gw
        val x0 = Pool.x0(gw); val x1 = Pool.x1(gw)
        val ox = if (px < x0) x0 - px else if (px > x1) px - x1 else 0f
        val oz = if (pz < Pool.Z0) Pool.Z0 - pz else if (pz > Pool.Z1) pz - Pool.Z1 else 0f
        if (ox > 0.7f || oz > 0.7f) return
        var wx = 0f; var wz = 0f           // direção da borda para a água
        if (ox > 0f && oz == 0f) wx = if (px < x0) 1f else -1f
        else if (oz > 0f && ox == 0f) wz = if (pz < Pool.Z0) 1f else -1f
        else return                         // quina ou dentro da água: não senta
        if (wx != 0f && (pz < Pool.Z0 + 0.5f || pz > Pool.Z1 - 0.5f)) return
        if (wz != 0f && (px < x0 + 0.5f || px > x1 - 0.5f)) return
        swX = px; swZ = pz
        swToX = if (wx > 0f) x0 else if (wx < 0f) x1 else px      // a borda da água: o quadril fica ~0,23 m para trás
        swToZ = if (wz > 0f) Pool.Z0 else if (wz < 0f) Pool.Z1 else pz
        swDX = wx; swDZ = wz
        swYaw = Math.toDegrees(atan2(wx.toDouble(), wz.toDouble())).toFloat()
        pMoving = false; pRun = false; path = null; markX = Float.NaN
        swimPh = 5; swimT = 0f
    }

    /** Altura (deslocamento da origem do corpo) para o assento ficar no topo da borda branca. */
    private fun sitEdgeLift(): Float = Pool.SIT_SEAT_Y - CuteChar.sitSeat()

    private fun clampWater(x: Float, z: Float): FloatArray {
        val gw = st.gw
        return floatArrayOf(x.coerceIn(Pool.x0(gw) + Pool.INSET, Pool.x1(gw) - Pool.INSET), z.coerceIn(Pool.Z0 + Pool.INSET, Pool.Z1 - Pool.INSET))
    }

    private fun updateSwim(dt: Float) {
        val hs = CuteChar.bodyScale()
        val gw = st.gw
        swimT += dt
        when (swimPh) {
            1 -> {   // mergulho: o clipe leva o personagem para frente
                val len = CuteChar.clipSeconds(CuteChar.RUN_DIVE)
                pYaw = swYaw; pMoving = false; py = 0f
                val d = Pool.diveZ(swimT) * hs   // o clipe não traz deslocamento: o quadril avança pela tabela (a câmera acompanha)
                px = swX + swDX * d; pz = swZ + swDZ * d
                if (!diveSplash && Pool.inWater(gw, px + swDX * 0.4f * hs, pz + swDZ * 0.4f * hs)) {
                    diveSplash = true; Water.ripple(px + swDX * 0.5f * hs, pz + swDZ * 0.5f * hs, 1.0f)
                }
                if (swimT >= len * 0.999f) {
                    val c = clampWater(px, pz)
                    px = c[0]; pz = c[1]; swimPh = 2; swimT = 0f; pMoving = false
                    swVX = swDX * Pool.SWIM_SPEED * 0.6f; swVZ = swDZ * Pool.SWIM_SPEED * 0.6f   // ainda desliza um pouco depois do mergulho
                    swimAnimMove = false; swimStill = 0f; ripT = 0.4f; diveSplash = false
                    Water.ripple(px, pz, 0.7f)
                }
            }
            2 -> {   // na água: parado = boiando (Treading_Water), movendo = nadando (Swimming)
                // Etapa 120: boia subindo e descendo de leve; velocidade com aceleração (sem arrancar/parar seco)
                waterT += dt
                val bob = (if (swimAnimMove) 0.012f else 0.028f) * sin(waterT * 2.2f)
                py += (Pool.WATER_Y + bob - py) * min(1f, dt * 3.5f)
                if (!third) pYaw = Math.toDegrees(atan2(sin(fyaw).toDouble(), (-cos(fyaw)).toDouble())).toFloat()
                val mag2 = moveX * moveX + moveY * moveY
                var tvx = 0f; var tvz = 0f
                if (mag2 > 0.0004f) {
                    val mg = min(1f, sqrt(mag2))
                    val fx = sin(fyaw); val fz = -cos(fyaw); val rx = cos(fyaw); val rz = sin(fyaw)
                    tvx = (fx * moveY + rx * moveX) / sqrt(mag2) * Pool.SWIM_SPEED * mg
                    tvz = (fz * moveY + rz * moveX) / sqrt(mag2) * Pool.SWIM_SPEED * mg
                }
                val acc = min(1f, dt * (if (mag2 > 0.0004f) 2.6f else 1.8f))   // a água segura: acelera e desacelera devagar
                swVX += (tvx - swVX) * acc; swVZ += (tvz - swVZ) * acc
                val spd = sqrt(swVX * swVX + swVZ * swVZ)
                // troca nadar/boiar com histerese (antes piscava entre os dois clipes com o analógico perto do centro)
                if (swimAnimMove) { if (spd < 0.25f && mag2 < 0.01f) swimStill += dt else swimStill = 0f; if (swimStill > 0.18f) { swimAnimMove = false; swimStill = 0f } }
                else { if (spd > 0.35f) swimStill += dt else swimStill = 0f; if (swimStill > 0.08f) { swimAnimMove = true; swimStill = 0f } }
                pMoving = swimAnimMove
                ripT -= dt
                if (ripT <= 0f) { Water.ripple(px, pz, if (swimAnimMove) 0.55f else 0.25f); ripT = if (swimAnimMove) 0.32f else 1.1f }
                if (spd > 0.02f) {
                    val c0 = clampWater(px + swVX * dt, pz + swVZ * dt)
                    px = c0[0]; pz = c0[1]
                }
                if (mag2 > 0.0004f) {
                    val mag = min(1f, sqrt(mag2))
                    val sp = Pool.SWIM_SPEED * mag * dt
                    val fx = sin(fyaw); val fz = -cos(fyaw); val rx = cos(fyaw); val rz = sin(fyaw)
                    val dx = (fx * moveY + rx * moveX) * sp / mag
                    val dz = (fz * moveY + rz * moveX) * sp / mag
                    val dir = Math.toDegrees(atan2(dx.toDouble(), dz.toDouble())).toFloat()
                    var dl = dir - pYaw
                    while (dl > 180f) dl -= 360f
                    while (dl < -180f) dl += 360f
                    if (third) pYaw += dl * min(1f, dt * 4.5f)   // Etapa 120: vira devagar na água
                    // chegou perto da borda empurrando para ela: nada até a borda e sai da água
                    val l = kotlin.math.hypot(dx, dz).coerceAtLeast(1e-6f)
                    val ux = dx / l; val uz = dz / l
                    val x0 = Pool.x0(gw); val x1 = Pool.x1(gw)
                    val near = Pool.EDGE_START * hs + 0.25f
                    var wx = 0f; var wz = 0f   // normal da parede, apontando para fora da água
                    if (mag > 0.5f) {
                        if (-ux > 0.7f && px - x0 <= near) wx = -1f
                        else if (ux > 0.7f && x1 - px <= near) wx = 1f
                        else if (-uz > 0.7f && pz - Pool.Z0 <= near) wz = -1f
                        else if (uz > 0.7f && Pool.Z1 - pz <= near) wz = 1f
                    }
                    if (wx != 0f || wz != 0f) {
                        val st0 = Pool.EDGE_START * hs
                        swX = px; swZ = pz
                        // posição ideal de partida: a distância certa da parede, no mesmo ponto ao longo dela
                        swToX = if (wx < 0f) x0 + st0 else if (wx > 0f) x1 - st0 else px
                        swToZ = if (wz < 0f) Pool.Z0 + st0 else if (wz > 0f) Pool.Z1 - st0 else pz
                        swDX = wx; swDZ = wz
                        swYaw = Math.toDegrees(atan2(wx.toDouble(), wz.toDouble())).toFloat()
                        swimPh = 3; swimT = 0f
                    }
                }
            }
            3 -> {   // nadar até a borda (clipe de 5 s; usamos até EDGE_END_T)
                ripT -= dt
                if (ripT <= 0f && swimT < 2.6f) { Water.ripple(px, pz, 0.45f); ripT = 0.45f }
                swVX = 0f; swVZ = 0f
                val k = smooth(min(1f, swimT / 0.5f))
                val ad = Pool.edgeZ(swimT) * hs
                px = swX + (swToX - swX) * k + swDX * ad; pz = swZ + (swToZ - swZ) * k + swDZ * ad
                var dl = swYaw - pYaw
                while (dl > 180f) dl -= 360f
                while (dl < -180f) dl += 360f
                pYaw += dl * min(1f, dt * 14f)
                py = Pool.WATER_Y * (1f - smooth(min(1f, swimT / 1.2f)))   // Etapa 120: sobe para a borda sem tranco
                pMoving = false
                if (swimT >= Pool.EDGE_END_T) {
                    swX = px; swZ = pz
                    // sobe para o deck: 0,6 m depois da borda da água
                    swToX = if (swDX < 0f) Pool.x0(gw) - 0.6f else if (swDX > 0f) Pool.x1(gw) + 0.6f else px
                    swToZ = if (swDZ < 0f) Pool.Z0 - 0.6f else if (swDZ > 0f) Pool.Z1 + 0.6f else pz
                    swimPh = 4; swimT = 0f; py = 0f
                }
            }
            5 -> {   // sentando na borda (clipe de sentar; o corpo desliza até a borda e abaixa até o topo da borda)
                pMoving = false; py = 0f
                var dl = swYaw - pYaw
                while (dl > 180f) dl -= 360f
                while (dl < -180f) dl += 360f
                pYaw += dl.coerceIn(-330f * dt, 330f * dt)
                val dur = CuteChar.clipSeconds(CuteChar.SIT_IN)
                val u = min(1f, swimT / dur)
                val k = smooth(u / 0.6f)
                px = swX + (swToX - swX) * k; pz = swZ + (swToZ - swZ) * k
                sitLift = sitEdgeLift() * smooth((u - 0.3f) / 0.55f)
                if (swimJump) { swimPh = 7; swimT = 0f; return }
                if (u >= 1f) { swimPh = 6; swimT = 0f }
            }
            6 -> {   // sentado na borda, pernas dentro d'água: entra sozinho, ou empurrando para a água / pulando; para trás levanta
                pMoving = false; py = 0f; pYaw = swYaw
                px = swToX; pz = swToZ; sitLift = sitEdgeLift()
                val mag2 = moveX * moveX + moveY * moveY
                var go = swimJump || swimT >= Pool.SIT_WAIT
                if (mag2 > 0.09f) {
                    val fx = sin(fyaw); val fz = -cos(fyaw); val rx = cos(fyaw); val rz = sin(fyaw)
                    val vx = fx * moveY + rx * moveX; val vz = fz * moveY + rz * moveX
                    val dot = (vx * swDX + vz * swDZ) / sqrt(mag2)
                    if (dot > 0.5f) go = true
                    else { swimPh = 8; swimT = 0f; return }
                }
                if (go) { swimPh = 7; swimT = 0f }
            }
            7 -> {   // escorrega da borda para a água e passa a boiar
                pMoving = false
                val dur = Pool.ENTER_T
                val k = smooth(min(1f, swimT / dur))
                val d = Pool.ENTER_DIST * hs * k
                px = swToX + swDX * d; pz = swToZ + swDZ * d
                pYaw = swYaw
                sitLift = sitEdgeLift() * (1f - k)
                py = Pool.WATER_Y * k + 0.10f * sin(Math.PI.toFloat() * k)
                if (swimT >= dur) {
                    val c = clampWater(px, pz)
                    px = c[0]; pz = c[1]; sitLift = 0f; py = Pool.WATER_Y
                    swimPh = 2; swimT = 0f; pMoving = false
                    swVX = 0f; swVZ = 0f; swimAnimMove = false; swimStill = 0f; ripT = 0.5f
                    Water.ripple(px, pz, 0.8f)
                }
            }
            8 -> {   // desistiu: levanta da borda (clipe de levantar) e volta para onde estava
                pMoving = false; py = 0f; pYaw = swYaw
                val dur = CuteChar.clipSeconds(CuteChar.SIT_OUT)
                val u = min(1f, swimT / dur)
                val k = smooth((u - 0.45f) / 0.5f)
                px = swToX + (swX - swToX) * k; pz = swToZ + (swZ - swToZ) * k
                sitLift = sitEdgeLift() * (1f - smooth(u / 0.6f))
                if (u >= 1f) { px = swX; pz = swZ; sitLift = 0f; swimPh = 0; swimT = 0f }
            }
            else -> {   // saindo da água: de pendurado na borda para em pé no deck
                val k = smooth(min(1f, swimT / 0.8f))
                px = swX + (swToX - swX) * k; pz = swZ + (swToZ - swZ) * k
                py = 0f; pMoving = false
                if (swimT >= 0.8f) { swimPh = 0; swimT = 0f }
            }
        }
    }

    /** Altura do chão sob (x, z): varanda, degrau e caminho de pedras ficam acima da grama. */
    private fun groundH(x: Float, z: Float): Float {
        val gw = st.gw.toFloat(); val gh = st.gh.toFloat()
        if (City.on && !City.inLot(x, z)) {   // Etapa 121: calçada 15 cm acima do asfalto
            var g = City.groundH(x, z)
            if (City.HDS && !driving) { val hs = Hds.surface(x, z, baseY); if (!hs.isNaN()) g = hs }   // Etapa 166: pisos reais, escadas e andares das casas
            val e = Elevado.surface(x, z, if (driving) carY else baseY)   // Etapa 145: pista do elevado/alça
            return if (!e.isNaN() && e > g) e else g
        }
        val cx = abs(x - gw / 2f)
        if (z > gh + 0.15f) {
            if (cx < 1.4f && z < gh + 1.75f) return 0.09f
            if (cx < 1.0f && z >= gh + 1.725f && z < gh + 2.175f) return 0.07f
            if (cx < 0.75f && z >= gh + 2.1f && z < gh + 9.5f) return 0.02f
        }
        return 0f
    }
    private var baseY = 0f

    /** Põe o personagem na porta da casa de novo (ao trocar de casa/sala de testes). */
    fun resetPlayer() { posInit = false; baseY = 0f; sleepChecked = false; if (swimPh >= 5) sitLift = 0f; swimPh = 0; edgeHold = 0f; if (py < 0f) py = 0f }
    private var sleepChecked = false

    /** Desenha o personagem do jogador (câmera em 3ª pessoa). */
    private fun drawPlayer(now: Long) {
        baseY += (groundH(px, pz) - baseY) * 0.3f
        if (City.HDS) Hds.refY = baseY
        val t = (now / 1_000_000L % 100000L) / 1000f
        val air = jumping
        val jc = if (jumpRun) CuteChar.RUNJUMP else CuteChar.JUMP
        CuteChar.fpOn = mode == 0 && !third && CuteChar.ready   // 1ª pessoa: cabeça fora da frente da câmera
        val sp = sitPh
        val cute = if (swimPh != 0 && CuteChar.hasPool()) CuteChar.frame(when (swimPh) {
                       1 -> CuteChar.RUN_DIVE
                       2 -> if (pMoving) CuteChar.SWIM else CuteChar.TREAD
                       3 -> CuteChar.SWIM_EDGE
                       5 -> CuteChar.SIT_IN
                       6 -> CuteChar.SIT_LOOP
                       7 -> CuteChar.TREAD
                       8 -> CuteChar.SIT_OUT
                       else -> CuteChar.IDLE
                   }, if (swimPh == 1 || swimPh == 3 || swimPh == 5 || swimPh == 8) swimT else t)
                   else if (usePh != 0 && sp == 0) CuteChar.frame(CuteChar.INTERACT, useT)
                   else if (sp >= 3) CuteChar.frame(when (sp) {
                       3 -> CuteChar.SIT_IN
                       4 -> CuteChar.SIT_LOOP
                       6, 8 -> if (lieK > 0.45f) CuteChar.IDLE else CuteChar.SIT_LOOP
                       7, 10 -> CuteChar.IDLE
                       9 -> CuteChar.SIT_LOOP
                       else -> CuteChar.SIT_OUT
                   }, if (sp == 3 || sp == 5) sitT else t)
                   else if ((flying || landing) && py > 0.05f) CuteChar.frame(if (flySpeed > 14f) CuteChar.RUNJUMP else CuteChar.JUMP, CuteChar.clipSeconds(if (flySpeed > 14f) CuteChar.RUNJUMP else CuteChar.JUMP) * 0.42f)   // Etapa 128: voando
                   else if (air) CuteChar.frame(jc, minOf(jumpT, CuteChar.clipSeconds(jc) * 0.999f))
                   else if (crouch && CuteChar.hasCrouch()) CuteChar.frame(if (pMoving) CuteChar.CROUCH_WALK else CuteChar.CROUCH, t)
                   else CuteChar.frame(if (pMoving) (if (pRun) CuteChar.RUN else CuteChar.WALK) else CuteChar.IDLE, t)
        val m = cute ?: avMesh ?: return
        val up = if (cute != null) CuteChar.lift(0) else 0f   // Etapa 20: sola em cima do chão
        playerMatrix(mdl, up)
        draw(m, mdl, 1f)
    }

    // ------------------------------------------------------------ personagem

    // ---- retrato do HUD: o rosto real do personagem, desenhado fora da tela e entregue como Bitmap ----
    @Volatile var portraitReq = false
    @Volatile var onPortrait: ((android.graphics.Bitmap) -> Unit)? = null
    private var surfW = 1
    private var surfH = 1

    private fun capturePortrait() = captureShot(false)

    /** Etapa 124: foto do personagem — rosto (retrato) ou corpo inteiro com fundo transparente (menu inicial). */
    private fun captureShot(full: Boolean) {
        val wasFp = CuteChar.fpOn
        CuteChar.fpOn = false
        val cute = if (CuteChar.ready) CuteChar.frame(CuteChar.IDLE, 0.4f, 2) else null
        CuteChar.fpOn = wasFp
        if (cute == null) return                       // personagem ainda não carregou: o pedido continua pendente
        if (full) fullReq = false else portraitReq = false
        val n = if (full) 512 else 256
        val nh = if (full) 896 else 256
        val fb = IntArray(1); val tx = IntArray(1); val rb = IntArray(1)
        GLES20.glGenFramebuffers(1, fb, 0); GLES20.glGenTextures(1, tx, 0); GLES20.glGenRenderbuffers(1, rb, 0)
        try {
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, tx[0])
            GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D, 0, GLES20.GL_RGBA, n, nh, 0, GLES20.GL_RGBA, GLES20.GL_UNSIGNED_BYTE, null)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
            GLES20.glBindRenderbuffer(GLES20.GL_RENDERBUFFER, rb[0])
            GLES20.glRenderbufferStorage(GLES20.GL_RENDERBUFFER, GLES20.GL_DEPTH_COMPONENT16, n, nh)
            GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER, fb[0])
            GLES20.glFramebufferTexture2D(GLES20.GL_FRAMEBUFFER, GLES20.GL_COLOR_ATTACHMENT0, GLES20.GL_TEXTURE_2D, tx[0], 0)
            GLES20.glFramebufferRenderbuffer(GLES20.GL_FRAMEBUFFER, GLES20.GL_DEPTH_ATTACHMENT, GLES20.GL_RENDERBUFFER, rb[0])
            if (GLES20.glCheckFramebufferStatus(GLES20.GL_FRAMEBUFFER) != GLES20.GL_FRAMEBUFFER_COMPLETE) return
            GLES20.glViewport(0, 0, n, nh)
            if (full) GLES20.glClearColor(0f, 0f, 0f, 0f) else GLES20.glClearColor(0.60f, 0.82f, 0.95f, 1f)
            GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
            GLES20.glEnable(GLES20.GL_DEPTH_TEST)
            val top = CuteChar.bodyTop()
            val cyH = if (full) 0.082f + CuteChar.lift(2) + top * 0.5f else 0.082f + CuteChar.lift(2) + top * 0.915f
            val dist = if (full) top * 2.15f else top * 0.56f
            val pj = FloatArray(16); val vw = FloatArray(16); val pv = FloatArray(16)
            Matrix.perspectiveM(pj, 0, 30f, n.toFloat() / nh, 0.05f, 20f)
            Matrix.setLookAtM(vw, 0, STX, cyH, STZ + dist, STX, cyH - 0.01f, STZ, 0f, 1f, 0f)
            Matrix.multiplyMM(pv, 0, pj, 0, vw, 0)
            val saved = vp.copyOf()
            System.arraycopy(pv, 0, vp, 0, 16)
            frameUniforms(STX, cyH, STZ + dist, 0f, 0f, STX + 0.6f, cyH + 0.9f, STZ + 1.6f)
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, STX, 0.082f + CuteChar.lift(2), STZ)
            draw(cute, mdl, 1f)
            System.arraycopy(saved, 0, vp, 0, 16)
            val bb = java.nio.ByteBuffer.allocateDirect(n * nh * 4).order(java.nio.ByteOrder.nativeOrder())
            GLES20.glReadPixels(0, 0, n, nh, GLES20.GL_RGBA, GLES20.GL_UNSIGNED_BYTE, bb)
            val raw = android.graphics.Bitmap.createBitmap(n, nh, android.graphics.Bitmap.Config.ARGB_8888)
            raw.copyPixelsFromBuffer(bb)
            val fl = android.graphics.Matrix(); fl.preScale(1f, -1f)
            val bmp = android.graphics.Bitmap.createBitmap(raw, 0, 0, n, nh, fl, true)
            raw.recycle()
            if (full) onFullBody?.invoke(bmp) else onPortrait?.invoke(bmp)
        } finally {
            GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER, 0)
            GLES20.glDeleteFramebuffers(1, fb, 0); GLES20.glDeleteTextures(1, tx, 0); GLES20.glDeleteRenderbuffers(1, rb, 0)
            GLES20.glViewport(0, 0, surfW, surfH)
        }
    }

    private fun drawCreator(now: Long) {
        GLES20.glClearColor(0.40f, 0.74f, 0.93f, 1f)
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
        frameUniforms(ex, ey, ez, 0f, 0f, STX + 0.9f, 2.4f, STZ + 1.7f)
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
            if (o.type.rug) continue
            val rc = o.rect()
            val t = hitBox(ry, rc[0] - 0.06f, 0f, rc[1] - 0.06f, rc[2] + 0.06f, maxOf(Foot.height(o.type), 0.12f) + 0.06f, rc[3] + 0.06f)
            if (t >= 0f && t < bt) { bt = t; best = o }
        }
        if (best != null) return best
        if (abs(ry[4]) < 1e-6f) return null
        val t = -ry[1] / ry[4]
        if (t < 0f || t > maxT) return null
        val wx = ry[0] + t * ry[3]
        val wz = ry[2] + t * ry[5]
        return st.items.lastOrNull { o ->
            val rc = o.rect()
            o.type.rug && wx >= rc[0] && wx <= rc[2] && wz >= rc[1] && wz <= rc[3]
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
                val p = st.placeAt(g, g.rot, snapQ(fp[0] - g.w / 2f), snapQ(fp[1] - g.h / 2f))
                if (p != null) { g.x = p[0].toInt(); g.y = p[1].toInt(); g.ox = p[2]; g.oz = p[3] }
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

    private val shownB = BooleanArray(4)
    override fun onDrawFrame(gl: GL10?) {
        val now = System.nanoTime()
        var dt = if (lastT == 0L) 0.016f else (now - lastT) / 1e9f
        lastT = now
        if (dt > 0.0001f && dt < 1f) fpsAvg += (1f / dt - fpsAvg) * 0.05f      // Etapa 89: FPS médio (resolução dinâmica e contador)
        if (dt > 0.05f) dt = 0.05f

        if (st.gw != bw || st.gh != bh || st.floorIdx != bf || st.wallIdx != bwl || st.testRoom != bTest) rebuild()
        // Etapa 124: o contexto GL caiu (app foi para o fundo): a cidade não tem cópia na memória, então é montada de novo
        else if (City.on && (City.builtGen != GlGen.gen || City.hdsBuilt != City.HDS) && !st.testRoom) { City.clear(); City.buildAsync(st.gw, st.gh) }
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
            val tp = cTargetPitch
            if (!tp.isNaN()) {
                cPitch += (tp - cPitch) * min(1f, dt * 6f)
                if (abs(tp - cPitch) < 0.003f) cTargetPitch = Float.NaN
            }
            val cp = cPitch
            ex = STX + cdist * cos(cp) * sin(cyaw)
            ey = cfy + cdist * sin(cp)
            ez = STZ + cdist * cos(cp) * cos(cyaw)
            Matrix.perspectiveM(proj, 0, 34f, aspect, 0.1f, 200f)
            if (cshCur != 0f || cshXCur != 0f || cPanX != 0f || cPanY != 0f) {
                Matrix.setIdentityM(shM, 0)
                Matrix.translateM(shM, 0, cshXCur + cPanX, cshCur + cPanY, 0f)
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
            if (third && driving) {
                // Etapa 123: câmera de perseguição atrás do veículo
                // Etapa 126: câmera de corrida: afasta e abre o campo de visão com a velocidade, inclina de leve nas curvas
                val spd = min(1f, abs(carSpeed) / 40f)
                val dist = (if (isMoto()) 4.4f else if (st.vehKind == Vehicles.BUS) 11f else 6.6f) + spd * 1.8f
                val tx = carX + sin(carH) * spd * 2.5f; val ty = carY + (if (isMoto()) 1.2f else 1.35f); val tz = carZ - cos(carH) * spd * 2.5f
                ex = tx - fx * dist; ey = maxOf(ty - fy * dist + 0.9f - spd * 0.25f, carY + 0.6f); ez = tz - fz * dist
                Matrix.perspectiveM(proj, 0, 60f + spd * 16f, aspect, 0.35f, 300f)
                Matrix.setLookAtM(view, 0, ex, ey, ez, tx, ty, tz, sin(camRoll) * fz, cos(camRoll), -sin(camRoll) * fx)
            } else if (third) {
                // 3ª pessoa: câmera atrás do personagem, orbitando com o olhar
                crouchK += ((if (crouch) 1f else 0f) - crouchK) * 0.15f
                val fly = flying || landing
                val tx = px; val ty = if (fly) baseY + py + 1.05f else py * 0.6f + 1.05f - 0.36f * crouchK; val tz = pz
                val inRoom = px > 0.32f && px < gw - 0.32f && pz > 0.32f && pz < gh - 0.32f && !(fly && py > 1.2f)
                val cb = if (City.on && !(fly && py > 2.2f)) City.bldAt(px, pz) else null
                camBld = cb
                var t = 1f
                var ox = tx; var oy = ty; var oz = tz
                for (i in 0..12) {
                    val cd = if (fly) 3.6f + min(2.6f, flySpeed / 15f) else 2.7f   // Etapa 128: voando, a câmera afasta com a velocidade
                    ox = tx - fx * cd * t; oy = ty - fy * cd * t; oz = tz - fz * cd * t
                    val okRoom = !inRoom || (ox > 0.2f && ox < gw - 0.2f && oz > 0.2f && oz < gh - 0.2f && oy < 2.3f && !HouseLayout.crosses(st.gw, st.gh, tx, tz, ox, oz))
                    // Etapa 126: dentro de loja/prédio a câmera fica do lado de dentro das paredes e abaixo do teto
                    val okBld = cb == null || (ox > cb.x0 + 0.45f && ox < cb.x1 - 0.45f && oz > cb.z0 + 0.45f && oz < cb.z1 - 0.45f && oy < 2.75f)
                    if (okRoom && okBld) break
                    t -= 0.07f
                }
                if (t < 0.12f) t = 0.12f
                ex = ox; ey = maxOf(oy, 0.25f); ez = oz
                // Etapa 126: plano próximo maior fora de casa = profundidade bem mais precisa ao longe (janelas, guias e lajes paravam de piscar)
                val nearP = if (inRoom) 0.08f else if (cb != null) 0.16f else if (Hds.inside(px, pz)) 0.25f else if (fly && py > 6f) 0.5f else 0.3f
                Matrix.perspectiveM(proj, 0, 60f + (if (fly) min(14f, flySpeed / 3.5f) else 0f), aspect, nearP, if (fly) 520f else 260f)
                Matrix.setLookAtM(view, 0, ex, ey, ez, tx, ty, tz, 0f, 1f, 0f)
            } else {
                // 1ª pessoa: a câmera fica no olho do personagem, seguindo a cabeça animada (corrida, pulo...)
                val lift = if (CuteChar.ready) CuteChar.lift(0) else 0f
                val dn = maxOf(0f, -fpitch).coerceAtMost(1.45f)
                val adj = 0.11f * sin(dn)          // olhando para baixo, a cabeça se inclina e o olho vai para a frente do peito
                CuteChar.fpAdjF = adj
                val er = Math.toRadians(pYaw.toDouble())
                val ecs = cos(er).toFloat(); val esn = sin(er).toFloat()
                val mex = CuteChar.fpEye[0]; val mez = CuteChar.fpEye[2] + adj
                ex = px + mex * ecs + mez * esn
                ez = pz - mex * esn + mez * ecs
                ey = baseY + py + lift + sitLift + (if (CuteChar.fpEye[1] > 0.5f) CuteChar.fpEye[1] else 1.5f) - 0.03f * sin(dn)
                if (lieK > 0.001f) {
                    // deitado/deitando: o olho segue o corpo inclinado
                    playerMatrix(plM, lift)
                    val e0 = CuteChar.fpEye[0]; val e1 = CuteChar.fpEye[1]; val e2 = CuteChar.fpEye[2]
                    ex = plM[0] * e0 + plM[4] * e1 + plM[8] * e2 + plM[12]
                    ey = plM[1] * e0 + plM[5] * e1 + plM[9] * e2 + plM[13]
                    ez = plM[2] * e0 + plM[6] * e1 + plM[10] * e2 + plM[14]
                }
                Matrix.perspectiveM(proj, 0, 72f, aspect, if (atHome(px, pz)) 0.04f else 0.09f, if (flying || landing) 520f else 260f)
                Matrix.setLookAtM(view, 0, ex, ey, ez, ex + fx, ey + fy, ez + fz, 0f, 1f, 0f)
            }
        } else if (cityAer()) {
            // Etapa 126: vista de cima na cidade, seguindo o personagem (o prédio em que ele está fica sem teto e paredes altas)
            if (acx.isNaN()) { acx = px; acz = pz }
            val k = min(1f, dt * 5f)
            acx += (px - acx) * k; acz += (pz - acz) * k
            val dist = 19f / minOf(aspect, 1f) * zoom
            ex = acx + dist * cos(pitch) * sin(yaw)
            ey = 0.5f + dist * sin(pitch)
            ez = acz + dist * cos(pitch) * cos(yaw)
            Matrix.perspectiveM(proj, 0, 40f, aspect, 0.3f, 300f)
            Matrix.setLookAtM(view, 0, ex, ey, ez, acx, 0.4f, acz, 0f, 1f, 0f)
        } else {
            acx = Float.NaN
            val dist = maxOf(gw, gh) * 2.0f / minOf(aspect, 1f) * zoom
            ex = cx + dist * cos(pitch) * sin(yaw)
            ey = 0.5f + dist * sin(pitch)
            ez = cz + dist * cos(pitch) * cos(yaw)
            Matrix.perspectiveM(proj, 0, 40f, aspect, 0.3f, 260f)
            Matrix.setLookAtM(view, 0, ex, ey, ez, cx, 0.4f, cz, 0f, 1f, 0f)
        }
        if ((fp && third) || cityAer()) { eyeX = px; eyeZ = pz } else { eyeX = ex; eyeZ = ez }
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
        if (portraitReq) capturePortrait()
        if (fullReq) captureShot(true)
        if (City.on && (mapReq || mapGen != GlGen.gen || mapBuilt != City.builds) && onMap != null) captureMap()
        if (cr) {
            drawCreator(now)
            return
        }
        GLES20.glClearColor(0.80f, 0.88f, 0.96f, 1f)
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
        frameUniforms(ex, ey, ez, gw.toFloat(), gh.toFloat(), cx, 2.1f, cz)

        // céu
        GLES20.glDisable(GLES20.GL_DEPTH_TEST)
        Matrix.setIdentityM(mdl, 0)
        Matrix.translateM(mdl, 0, ex, ey, ez)
        skyM?.let { draw(it, mdl, 1f) }
        cloudM?.let {
            // as nuvens andam devagar (uma volta a cada ~1 h)
            val ang = ((now / 1_000_000L) % 3_600_000L) / 3_600_000f * 360f
            Matrix.rotateM(mdl, 0, ang, 0f, 1f, 0f)
            draw(it, mdl, 1f)
        }
        GLES20.glEnable(GLES20.GL_DEPTH_TEST)

        Matrix.setIdentityM(mdl, 0)
        if (homeOn) yardM?.let { draw(it, mdl, 1f) }
        if (City.on) drawCity(ex, ez)
        Matrix.setIdentityM(mdl, 0)
        if (homeOn) floorM?.let { draw(it, mdl, 1f) }

        val shown = shownB
        shown[0] = homeOn && (fp || ez >= cz)
        shown[1] = homeOn && (fp || ez < cz)
        shown[2] = homeOn && (fp || ex >= cx)
        shown[3] = homeOn && (fp || ex < cx)
        for (i in 0..3) if (shown[i]) {
            wallModel(i, gw.toFloat(), gh.toFloat())
            walls[i]?.let { draw(it, mdl, 1f) }
        }
        // cortinas: física de tecido (só quando há alguém dentro da casa a ver; no criador/sala de testes também roda)
        run {
            val tn = System.nanoTime()
            val dtc = if (clothT == 0L) 0.016f else ((tn - clothT) / 1e9f).coerceIn(0f, 0.05f)
            clothT = tn
            cloth.step(dtc, (tn / 1_000_000L % 1_000_000L) / 1000f, gw.toFloat(), gh.toFloat(), px, pz, st.items)
            // Etapa 83: peças animadas, física dos objetos soltos e o que dá para usar daqui
            stepObjects(dtc)
            findNear(dtc)
            // Etapa 123: veículo
            if (driving) { nearKind = 21; nearLabel = if (isMoto()) "Descer da moto" else "Sair do carro" }
            else if (mode == 0 && sitPh == 0 && swimPh == 0 && !carX.isNaN() && carMesh != null && kotlin.math.hypot(px - carX, pz - carZ) < carHalfL() + 1.6f) {
                nearKind = 20; nearLabel = if (isMoto()) "Subir na moto" else "Dirigir"
            }
            // Etapa 174: casas à venda na Cidade 2
            buyIdx = -1
            if (!homeOn && !driving && mode == 0 && sitPh == 0 && swimPh == 0 && nearKind == 0) {
                for (h in HdsEstate.houses) {
                    if (HdsEstate.isOwned(h.idx)) continue
                    val r = Hds.plot(h.idx) ?: continue
                    if (px > r[0] - 3f && px < r[2] + 3f && pz > r[1] - 3f && pz < r[3] + 3f) {
                        buyIdx = h.idx; nearKind = 30
                        nearLabel = "Comprar casa · ${h.area} m² · ${HdsEstate.brl(h.price)}"
                        break
                    }
                }
            }
            if ((flying || landing) && py > 0.4f) { nearKind = 0; nearLabel = "" }   // Etapa 128: no ar não dá para usar nada
            if (useReq) {
                useReq = false
                when (nearKind) {
                    1 -> doorOpen = !doorOpen
                    2 -> cloth.toggle(nearId)
                    3 -> nearItem?.let { startSit(it, nearSeat, false) }
                    6 -> nearItem?.let { startUse(it, -1) }
                    7 -> nearItem?.let { startSit(it, nearSeat, true) }
                    4 -> nearItem?.let { startUse(it, nearPart) }
                    5 -> { sitCancel = true; if (washPh != 0) washPh = 0 }
                    8 -> sitItem?.let { o ->
                        // Etapa 87: dormir / acordar (o sono fica gravado no save)
                        if (sitPh == 7) { sitPh = 10; o.sleep = sitSeat; saveReq = true }
                        else if (sitPh == 10) { sitPh = 7; o.sleep = ""; saveReq = true }
                    }
                    9 -> nearItem?.let { startWash(it, nearSeat) }
                    20 -> enterCar()
                    21 -> exitCar()
                    30 -> if (buyIdx >= 0) {
                        val h = HdsEstate.houses[buyIdx]
                        HdsEstate.buy(h.idx)
                        toast = "Comprou a ${HdsEstate.label(h.idx)} (${h.classe}) por ${HdsEstate.brl(h.price)}"
                        nearKind = 0
                    }
                }
            }
            for (pn in cloth.panels) if (shown[pn.wall]) {
                wallModel(pn.wall, gw.toFloat(), gh.toFloat())
                draw(pn.mesh, mdl, 1f)
            }
        }
        // porta animada: abre sozinha quando o personagem chega perto e fecha quando ele se afasta
        doorM?.let { dm ->
            val now2 = System.nanoTime()
            val dtd = ((now2 - doorT) / 1e9f).coerceIn(0f, 0.1f)
            doorT = now2
            val tgt = if (doorOpen) 100f else 0f
            doorAng += (tgt - doorAng) * Math.min(1f, dtd * 5f)
            if (Math.abs(tgt - doorAng) < 0.3f) doorAng = tgt
            if (shown[1]) {
                wallModel(1, gw.toFloat(), gh.toFloat())
                Matrix.translateM(mdl, 0, gw / 2f - 0.49f, 0f, -0.04f)
                Matrix.rotateM(mdl, 0, doorAng, 0f, 1f, 0f)
                draw(dm, mdl, 1f)
            }
        }
        if (fp && homeOn) {
            Matrix.setIdentityM(mdl, 0)
            ceilM?.let { draw(it, mdl, 1f) }
        }

        val items = if (homeOn) st.items else java.util.concurrent.CopyOnWriteArrayList<Item>()
        glassQ.clear(); lateQ.clear()
        for (item in items) {
            val t = item.type
            // Etapa 89: fora do campo de visão não desenha (caixa do item contra os planos da câmera)
            if (item.body == null) {
                val rc = item.rect()
                if (!boxVisible(rc[0] - 0.3f, 0f, rc[1] - 0.3f, rc[2] + 0.3f, Foot.height(t) + 0.3f, rc[3] + 0.3f)) continue
            }
            if (t.glb != null) { drawGlbItem(item, now); continue }
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
            val es = Foot.scale(t)
            Matrix.translateM(mdl, 0, item.x + item.ox + item.w / 2f, lift, item.y + item.oz + item.h / 2f)
            Matrix.rotateM(mdl, 0, item.rot * 90f, 0f, 1f, 0f)
            Matrix.scaleM(mdl, 0, s * es, s * es, s * es)
            Matrix.translateM(mdl, 0, -t.w / 2f, 0f, -t.h / 2f)
            draw(mesh, mdl, 1f)
        }

        if ((mode == 1 || fp) && !driving) drawPlayer(now)

        GLES20.glDepthMask(false)
        val tt = (now / 1_000_000L % 100000L) / 1000f
        for (item in items) {
            if (item.type.rug) continue
            val bd = item.body
            if (bd != null && bd.p[1] - bd.extent(0f, 1f, 0f) > topUnder(bd.p[0], bd.p[2], bd.p[1]) + 0.25f) continue   // no ar alto: sem sombra
            val rc = item.rect()
            val sa = Math.round((rc[2] - rc[0]) * 20f)
            val sb = Math.round((rc[3] - rc[1]) * 20f)
            val shm = sm.getOrPut(1000000 + sa * 10000 + sb) { Models.shadowF(sa / 20.0, sb / 20.0) }
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, (rc[0] + rc[2]) / 2f, if (bd != null) topUnder(bd.p[0], bd.p[2], bd.p[1]) + 0.002f else 0f, (rc[1] + rc[3]) / 2f)
            draw(shm, mdl, 1f)
        }
        if ((mode == 1 || fp) && (swimPh == 0 || swimPh in 5..6 || swimPh == 8)) {
            val shm = sm.getOrPut(11) { Models.shadow(1, 1) }
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, px - 0.5f, baseY + 0.02f, pz - 0.5f)
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
            val rc = sel.rect()
            val ra = Math.round(maxOf(rc[2] - rc[0], 0.35f) * 20f)
            val rb = Math.round(maxOf(rc[3] - rc[1], 0.35f) * 20f)
            val key = "${ra}x${rb}${if (green) "g" else "y"}"
            val rg = rm.getOrPut(key) { Models.ringF(ra / 20.0, rb / 20.0, if (green) C("#5CE08A") else C("#FFE066")) }
            Matrix.setIdentityM(mdl, 0)
            Matrix.translateM(mdl, 0, (rc[0] + rc[2]) / 2f - ra / 40f, 0f, (rc[1] + rc[3]) / 2f - rb / 40f)
            draw(rg, mdl, 0.7f + 0.3f * sin(tt * 5f))
        }
        // vidros por último
        run {   // Etapa 120: água com ondas, reflexo e ondinhas (programa próprio); se não compilar, volta ao plano de vidro da Etapa 118
            val ym = yardM
            if (homeOn && ym != null && boxVisible(Pool.x0(st.gw), -2f, Pool.Z0, Pool.x1(st.gw), 0.2f, Pool.Z1)) {   // Etapa 121: fora da câmera não desenha
                val ok = Water.draw(vp, frameU[0], frameU[1], frameU[2], st.gw)
                useProg(curProg)
                if (!ok) { Matrix.setIdentityM(mdl, 0); draw(ym, mdl, 1f, true) }
            }
        }
        if (City.on) drawCityGlass(frameU[0], frameU[1], frameU[2])   // Etapa 122: mar, vidros da cidade, GPS
        for ((m, mx) in carGlassQ) draw(m, mx, 1f, true)    // Etapa 162: vidros do Tesla
        carGlassQ.clear()
        for ((m, mx) in glassQ) draw(m, mx, 1f, true)
        for ((m, mx) in lateQ) draw(m, mx, 1f)
        for (i in 0..3) if (shown[i]) {
            wallModel(i, gw.toFloat(), gh.toFloat())
            walls[i]?.let { draw(it, mdl, 1f, true) }
        }
        GLES20.glDepthMask(true)
    }

    // ================================================================ Etapa 83: biblioteca 3D (GLB)

    /** centro do item no mundo */
    private fun itemBase(item: Item, out: FloatArray) {
        Matrix.setIdentityM(out, 0)
        Matrix.translateM(out, 0, item.x + item.ox + item.w / 2f, 0f, item.y + item.oz + item.h / 2f)
        Matrix.rotateM(out, 0, item.rot * 90f, 0f, 1f, 0f)
    }

    /** ponto (x, z) do espaço do objeto -> mundo */
    private fun toWorld(o: Item, lx: Float, lz: Float): FloatArray {
        val cx = o.x + o.ox + o.w / 2f; val cz = o.y + o.oz + o.h / 2f
        return when (((o.rot % 4) + 4) % 4) {
            1 -> floatArrayOf(cx + lz, cz - lx)
            2 -> floatArrayOf(cx - lx, cz - lz)
            3 -> floatArrayOf(cx - lz, cz + lx)
            else -> floatArrayOf(cx + lx, cz + lz)
        }
    }

    /** matriz de mundo do nó [ni] com a peça animada [ak] no progresso [u] (as outras no progresso atual) */
    private fun nodeWorld(item: Item, g: GModel, ni: Int, ak: Int, u: Float, out: FloatArray) {
        val chain = IntArray(24); var n = 0; var c = ni
        while (c >= 0 && n < 24) { chain[n++] = c; c = g.nodes[c].parent }
        itemBase(item, out)
        for (k in n - 1 downTo 0) {
            val idx = chain[k]; val nd = g.nodes[idx]
            val slot = g.animSlot[idx]
            val uu = if (slot >= 0 && slot == ak) u else if (slot >= 0) (item.animCur?.getOrNull(slot) ?: 0f) else 0f
            nd.local(gmL, nd.value(uu))
            Matrix.multiplyMM(gmB, 0, out, 0, gmL, 0)
            System.arraycopy(gmB, 0, out, 0, 16)
        }
    }

    private fun groundAt(x: Float, z: Float): Float =
        if (x > 0f && x < st.gw && z > 0f && z < st.gh) 0f else groundH(x, z)

    /** topo da coisa mais alta (abaixo de [maxY]) sob o ponto (x, z): piso, tampo de mesa, braço da poltrona... */
    private fun topUnder(x: Float, z: Float, maxY: Float): Float {
        var best = groundAt(x, z)
        for (s in statics) if (x > s.x0 && x < s.x1 && z > s.z0 && z < s.z1 && s.y1 <= maxY && s.y1 > best) best = s.y1
        return best
    }

    private fun buildStatics() {
        statics.clear()
        if (HouseLayout.active(st.gw, st.gh)) for (r in HouseLayout.rects + HouseLayout.fixtures) statics.add(SBox(r[0], 0f, r[1], r[2], Models.HH.toFloat(), r[3]))
        for (o in st.items) {
            if (o.type.rug || o.type.dyn) continue
            val g = o.type.glb?.let { Glb.get(it) }
            if (g != null && g.cols.isNotEmpty()) {
                val q = ((o.rot % 4) + 4) % 4
                for (c in g.cols) {
                    val w = toWorld(o, c.cx, c.cz)
                    val sx = if (q % 2 == 1) c.sz else c.sx
                    val sz = if (q % 2 == 1) c.sx else c.sz
                    statics.add(SBox(w[0] - sx / 2f, c.cy - c.sy / 2f, w[1] - sz / 2f, w[0] + sx / 2f, c.cy + c.sy / 2f, w[1] + sz / 2f))
                }
            } else {
                val h = Foot.height(o.type)
                if (h < 0.03f) continue
                val r = o.rect()
                statics.add(SBox(r[0], 0f, r[1], r[2], h, r[3]))
            }
        }
    }

    private fun makeBody(o: Item): Body? {
        val g = Glb.get(o.type.glb ?: return null) ?: return null
        val c = g.cols.firstOrNull() ?: return null
        val f = g.meta.optJSONObject("fisica")
        fun fv(k: String, d: Double): Float = (f?.optDouble(k, d) ?: d).toFloat()
        val b = Body(o, c.shape == "sphere", c.sx / 2f, c.sy / 2f, c.sz / 2f, c.cy,
            fv("massa", 1.0), fv("atrito", 0.6), fv("restituicao", 0.2), fv("amortecimento", 0.05), fv("amortecimento_ang", 0.1), fv("rolamento", 0.0))
        var ok = false
        if (o.st.isNotEmpty()) {
            try {
                val m = HashMap<String, String>()
                for (kv in o.st.split('~')) { val i = kv.indexOf('='); if (i > 0) m[kv.substring(0, i)] = kv.substring(i + 1) }
                val qs = m["q"]?.split(':')?.map { it.toFloat() }
                val sx = m["px"]?.toFloat(); val sy = m["py"]?.toFloat(); val sz = m["pz"]?.toFloat()
                if (sx != null && sy != null && sz != null && qs != null && qs.size == 4) {
                    b.p[0] = sx; b.p[1] = sy; b.p[2] = sz
                    for (k in 0..3) b.q[k] = qs[k]
                    b.updR(); b.sleep = true; ok = true
                }
            } catch (e: Exception) { }
        }
        // posição gravada longe do lugar do item (o item foi mexido): põe no lugar do item
        if (ok && (abs(b.p[0] - (o.x + o.ox + o.w / 2f)) > 0.06f || abs(b.p[2] - (o.y + o.oz + o.h / 2f)) > 0.06f)) ok = false
        if (!ok) placeBody(b)
        b.lastX = o.x + o.ox; b.lastZ = o.y + o.oz
        return b
    }

    /** põe o corpo parado em cima do que houver no lugar do item (piso, mesa...) */
    private fun placeBody(b: Body) {
        val o = b.item
        b.p[0] = o.x + o.ox + o.w / 2f; b.p[2] = o.y + o.oz + o.h / 2f
        b.setYaw(o.rot * 90f)
        b.p[1] = topUnder(b.p[0], b.p[2], 1.25f) + b.extent(0f, 1f, 0f) + 0.01f
        for (k in 0..2) { b.v[k] = 0f; b.w[k] = 0f }
        b.sleep = false; b.still = 0f
    }

    /** Peças animadas (portas, gavetas, almofada) e física dos objetos soltos, uma vez por quadro. */
    private fun stepObjects(dt: Float) {
        partBoxes.clear()
        for (o in st.items) {
            val gid = o.type.glb ?: continue
            val g = Glb.get(gid) ?: continue
            val na = g.animated.size
            if (na == 0) continue
            if (o.animTgt?.size != na) o.animTgt = FloatArray(na)
            if (o.animCur?.size != na) o.animCur = o.animTgt!!.copyOf()
            if (o.animLim?.size != na) o.animLim = FloatArray(na) { 1f }
            val cur = o.animCur!!; val tgt = o.animTgt!!; val lim = o.animLim!!
            for (k in 0 until na) {
                val nd = g.nodes[g.animated[k]]
                when (g.slotGatilho[k]) {
                    "ligado" -> tgt[k] = if (o.on) 1f else 0f
                    "ocupado" -> tgt[k] = if (sitItem === o && sitPressed && (g.slotAssento[k].isEmpty() || g.slotAssento[k] == sitSeat)) 1f else 0f
                    "puxar" -> tgt[k] = if (sitItem === o) pullTgt else 0f
                }
                val goal = tgt[k] * lim[k]
                val sp = dt / nd.aDur
                val d = goal - cur[k]
                cur[k] += d.coerceIn(-sp, sp)
                if (cur[k] > 0.05f && nd.aType != 3) {
                    // caixa (chão) da peça aberta: o personagem não atravessa a porta/gaveta aberta
                    nodeWorld(o, g, g.animated[k], k, cur[k], gmA)
                    val bb = nd.bb
                    var x0 = Float.MAX_VALUE; var z0 = Float.MAX_VALUE; var x1 = -Float.MAX_VALUE; var z1 = -Float.MAX_VALUE
                    for (c in 0 until 8) {
                        val x = if (c and 1 != 0) bb[3] else bb[0]; val y = if (c and 2 != 0) bb[4] else bb[1]; val z = if (c and 4 != 0) bb[5] else bb[2]
                        val wx = gmA[0] * x + gmA[4] * y + gmA[8] * z + gmA[12]
                        val wz = gmA[2] * x + gmA[6] * y + gmA[10] * z + gmA[14]
                        if (wx < x0) x0 = wx; if (wx > x1) x1 = wx; if (wz < z0) z0 = wz; if (wz > z1) z1 = wz
                    }
                    partBoxes.add(floatArrayOf(x0 - 0.16f, z0 - 0.16f, x1 + 0.16f, z1 + 0.16f))
                }
            }
        }
        // física
        buildStatics()
        Physics.sync(st.items) { makeBody(it) }
        if (Physics.bodies.isEmpty()) { lastPhX = Float.NaN; return }
        val g0 = grabbed
        for (b in Physics.bodies) {
            val it = b.item
            val ix = it.x + it.ox; val iz = it.y + it.oz
            if (it === g0) {
                // sendo arrastado pela interface: segue o item, um pouco acima do apoio
                b.kinematic = true
                b.p[0] = ix + it.w / 2f; b.p[2] = iz + it.h / 2f
                b.setYaw(it.rot * 90f)
                b.p[1] = topUnder(b.p[0], b.p[2], 1.25f) + b.extent(0f, 1f, 0f) + 0.08f
                for (k in 0..2) { b.v[k] = 0f; b.w[k] = 0f }
                b.sleep = false; b.lastX = ix; b.lastZ = iz
            } else if (b.kinematic || abs(ix - b.lastX) > 0.002f || abs(iz - b.lastZ) > 0.002f) {
                b.kinematic = false
                placeBody(b)
                b.lastX = ix; b.lastZ = iz
            }
        }
        var pvx = 0f; var pvz = 0f
        if (!lastPhX.isNaN() && dt > 1e-4f) { pvx = (px - lastPhX) / dt; pvz = (pz - lastPhZ) / dt }
        lastPhX = px; lastPhZ = pz
        if (pvx * pvx + pvz * pvz > 36f) { pvx = 0f; pvz = 0f }      // teletransporte (troca de casa): ignora
        val w = Physics.World(statics, st.gw.toFloat(), st.gh.toFloat(), doorOpen, { x, z -> groundH(x, z) },
            px, pz, pvx, pvz, pRun && pMoving, (mode == 0 || mode == 1) && sitPh < 3)
        Physics.step(dt, w)
        for (b in Physics.bodies) if (!b.kinematic) Physics.writeBack(b)
        if (Physics.settled) { Physics.settled = false; saveReq = true }
    }

    /** O que dá para usar daqui: porta, cortina, assento ou peça (gaveta/porta de móvel) mais perto e à frente. */
    private fun findNear(dt: Float) {
        if (msgT > 0f) msgT -= dt
        if (sitPh != 0) {
            aimHas = false; aimOn = false
            nearItem = null; nearPart = -1
            val canSleep = sitItem?.type?.glb?.let { Glb.get(it) }?.let { g -> g.nodes.getOrNull(g.index(sitSeat))?.ex?.optBoolean("dormir", false) } ?: false
            when (sitPh) {
                1, 2 -> { nearKind = 5; nearLabel = "Cancelar" }
                7 -> if (canSleep) { nearKind = 8; nearLabel = "Dormir" } else { nearKind = 5; nearLabel = "Levantar" }
                10 -> { nearKind = 8; nearLabel = "Acordar" }
                3, 4, 6 -> { nearKind = 5; nearLabel = "Levantar" }
                else -> nearKind = 0
            }
            return
        }
        if (washPh != 0) { aimHas = false; aimOn = false; nearItem = null; nearPart = -1; nearKind = 5; nearLabel = "Parar"; return }
        if (mode != 0 || usePh != 0) { aimHas = false; aimOn = false; nearKind = 0; return }
        // Etapa 88: interação pela MIRA. Um raio sai do centro da tela; cada coisa usável tem uma caixa (peça móvel do GLB no
        // estado atual, assento, lado da cama, cuba, porta da casa, cortina). Vale a primeira caixa que o raio atravessa, perto
        // do personagem. A caixa escolhida é projetada na tela para a mira envolver o alvo (Overlay).
        val gw = st.gw.toFloat(); val gh = st.gh.toFloat()
        var best = Float.MAX_VALUE; var kind = 0; var lab = ""; var bi: Item? = null; var bp = -1; var bid = 0; var seat = ""
        val ry = centerRay()
        aimHas = false
        fun consider(t: Float, reach: Float, M: FloatArray, b0: Float, b1: Float, b2: Float, b3: Float, b4: Float, b5: Float): Boolean {
            if (t < 0f || t >= best) return false
            val hx = ry[0] + ry[3] * t; val hz = ry[2] + ry[5] * t
            if (kotlin.math.hypot(hx - px, hz - pz) > reach) return false
            // na 3ª pessoa o raio passa pelo personagem: só vale o que está na frente dele
            if (third && (hx - px) * ry[3] + (hz - pz) * ry[5] < -0.1f) return false
            best = t
            System.arraycopy(M, 0, aimM, 0, 16)
            aimB[0] = b0; aimB[1] = b1; aimB[2] = b2; aimB[3] = b3; aimB[4] = b4; aimB[5] = b5
            aimHas = true
            return true
        }
        Matrix.setIdentityM(gmB, 0)
        // porta da casa
        run {
            val b = floatArrayOf(gw / 2f - 0.55f, 0f, gh - 0.14f, gw / 2f + 0.55f, 2.1f, gh + 0.14f)
            if (consider(hitBox(ry, b[0], b[1], b[2], b[3], b[4], b[5]), 1.9f, gmB, b[0], b[1], b[2], b[3], b[4], b[5])) {
                kind = 1; lab = if (doorOpen) "Fechar porta" else "Abrir porta"; bi = null; bp = -1
            }
        }
        // cortinas (a janela inteira)
        for ((wi, w) in cloth.wins.withIndex()) {
            val b = when (w.wall) {
                1 -> floatArrayOf(gw - w.c - w.w / 2f, 0.55f, gh - 0.22f, gw - w.c + w.w / 2f, 2.15f, gh)
                2 -> floatArrayOf(0f, 0.55f, gh - w.c - w.w / 2f, 0.22f, 2.15f, gh - w.c + w.w / 2f)
                else -> floatArrayOf(w.c - w.w / 2f, 0.55f, 0f, w.c + w.w / 2f, 2.15f, 0.22f)
            }
            if (consider(hitBox(ry, b[0], b[1], b[2], b[3], b[4], b[5]), 1.8f, gmB, b[0], b[1], b[2], b[3], b[4], b[5])) {
                kind = 2; bid = wi; lab = if (w.closed) "Abrir cortina" else "Fechar cortina"; bi = null; bp = -1
            }
        }
        for (o in st.items) {
            val gid = o.type.glb ?: continue
            val g = Glb.get(gid) ?: continue
            val cx = o.x + o.ox + o.w / 2f; val cz = o.y + o.oz + o.h / 2f
            if (kotlin.math.hypot(cx - px, cz - pz) > 3.2f) continue
            itemBase(o, gmC)
            // assentos, lados da cama e a cuba da pia (caixa "alvo" do ponto de interação)
            for (pref in arrayOf("IP_sentar", "IP_deitar", "IP_lavar")) {
                for (ni in g.ips(pref)) {
                    val nm = g.nodes[ni].name
                    if (pref != "IP_lavar" && nm in o.occ) continue
                    val al = g.nodes[ni].ex?.optJSONArray("alvo") ?: continue
                    val ax = al.optDouble(0).toFloat(); val ay = al.optDouble(1).toFloat(); val az = al.optDouble(2).toFloat()
                    val sx = al.optDouble(3).toFloat() / 2f; val sy = al.optDouble(4).toFloat() / 2f; val sz = al.optDouble(5).toFloat() / 2f
                    val t = rayLocal(ry, gmC, ax - sx, ay - sy, az - sz, ax + sx, ay + sy, az + sz, 0f)
                    if (consider(t, if (pref == "IP_lavar") 1.5f else 1.9f, gmC, ax - sx, ay - sy, az - sz, ax + sx, ay + sy, az + sz)) {
                        bi = o; bp = -1; seat = nm
                        when (pref) {
                            "IP_sentar" -> { kind = 3; lab = "Sentar" }
                            "IP_deitar" -> { kind = 7; lab = "Deitar" }
                            else -> { kind = 9; lab = g.nodes[ni].ex?.optString("rotulo", "Lavar as mãos") ?: "Lavar as mãos" }
                        }
                    }
                }
            }
            // peças móveis (portas, gavetas, botões, alavanca) na posição em que estão agora
            for (k in g.animated.indices) {
                val ni = g.animated[k]; val nd = g.nodes[ni]
                if (nd.aType == 3 || g.slotGatilho[k].isNotEmpty()) continue
                val pre = g.slotPrecisa[k]
                if (pre >= 0 && (o.animCur?.getOrNull(pre) ?: 0f) < 0.6f) continue
                val b = nd.bb
                if (b[0] > b[3]) continue
                nodeWorld(o, g, ni, k, o.animCur?.getOrNull(k) ?: 0f, gmA)
                // peça pequena (botão) ganha uma folga para ser fácil de mirar
                val small = (b[3] - b[0]) < 0.06f && (b[4] - b[1]) < 0.06f
                val pad = if (small) 0.012f else 0f
                val t = rayLocal(ry, gmA, b[0], b[1], b[2], b[3], b[4], b[5], pad)
                if (consider(t, 1.7f, gmA, b[0] - pad, b[1] - pad, b[2] - pad, b[3] + pad, b[4] + pad, b[5] + pad)) {
                    kind = 4; bi = o; bp = k; seat = ""
                    val open = (o.animTgt?.getOrNull(k) ?: 0f) > 0.5f
                    val vb = g.slotVerbs[k]
                    lab = (if (vb != null) (if (open) vb[1] else vb[0]) else (if (open) "Fechar" else "Abrir")) + " " + (nd.anim?.optString("rotulo", "peça") ?: "peça")
                }
            }
        }
        if (aimHas) projectAim()
        if (!aimHas) aimOn = false
        aimKind = kind
        nearItem = bi; nearPart = bp; nearId = bid; nearSeat = seat
        nearLabel = if (msgT > 0f && kind != 0) msgText else lab
        nearKind = kind
    }

    // ---------------------------------------------------------------- Etapa 88: mira
    private var aimHas = false
    private val aimM = FloatArray(16)
    private val aimB = FloatArray(6)
    private val gmC = FloatArray(16)
    private val invA = FloatArray(16)
    private val lray = FloatArray(6)
    /** retângulo do alvo na tela (0..1, y para baixo): x0, y0, x1, y1; aimOn = há alvo */
    @Volatile var aimOn = false
    val aimRect = FloatArray(4)
    @Volatile var aimKind = 0

    /** raio contra a caixa [b] no espaço da matriz [M] (objeto -> mundo); devolve t no mundo (matriz rígida) ou -1 */
    private fun rayLocal(ry: FloatArray, M: FloatArray, x0: Float, y0: Float, z0: Float, x1: Float, y1: Float, z1: Float, pad: Float): Float {
        if (!Matrix.invertM(invA, 0, M, 0)) return -1f
        val ox = ry[0]; val oy = ry[1]; val oz = ry[2]; val dx = ry[3]; val dy = ry[4]; val dz = ry[5]
        lray[0] = invA[0] * ox + invA[4] * oy + invA[8] * oz + invA[12]
        lray[1] = invA[1] * ox + invA[5] * oy + invA[9] * oz + invA[13]
        lray[2] = invA[2] * ox + invA[6] * oy + invA[10] * oz + invA[14]
        lray[3] = invA[0] * dx + invA[4] * dy + invA[8] * dz
        lray[4] = invA[1] * dx + invA[5] * dy + invA[9] * dz
        lray[5] = invA[2] * dx + invA[6] * dy + invA[10] * dz
        return hitBox(lray, x0 - pad, y0 - pad, z0 - pad, x1 + pad, y1 + pad, z1 + pad)
    }

    /** projeta os 8 cantos da caixa do alvo na tela (vp do quadro atual) */
    private fun projectAim() {
        var x0 = 9f; var y0 = 9f; var x1 = -9f; var y1 = -9f; var ok = true
        val b = aimB; val M = aimM
        for (c in 0 until 8) {
            val lx = if (c and 1 != 0) b[3] else b[0]; val ly = if (c and 2 != 0) b[4] else b[1]; val lz = if (c and 4 != 0) b[5] else b[2]
            val wx = M[0] * lx + M[4] * ly + M[8] * lz + M[12]
            val wy = M[1] * lx + M[5] * ly + M[9] * lz + M[13]
            val wz = M[2] * lx + M[6] * ly + M[10] * lz + M[14]
            val cx = vp[0] * wx + vp[4] * wy + vp[8] * wz + vp[12]
            val cy = vp[1] * wx + vp[5] * wy + vp[9] * wz + vp[13]
            val cw = vp[3] * wx + vp[7] * wy + vp[11] * wz + vp[15]
            if (cw < 0.02f) { ok = false; continue }
            val sx = (cx / cw * 0.5f + 0.5f); val sy = (0.5f - cy / cw * 0.5f)
            if (sx < x0) x0 = sx; if (sx > x1) x1 = sx; if (sy < y0) y0 = sy; if (sy > y1) y1 = sy
        }
        if (x1 < x0) { aimOn = false; return }
        if (!ok) { x0 = minOf(x0, 0f); y0 = minOf(y0, 0f); x1 = maxOf(x1, 1f); y1 = maxOf(y1, 1f) }
        aimRect[0] = x0.coerceIn(-0.05f, 1.05f); aimRect[1] = y0.coerceIn(-0.05f, 1.05f); aimRect[2] = x1.coerceIn(-0.05f, 1.05f); aimRect[3] = y1.coerceIn(-0.05f, 1.05f)
        aimOn = true
    }

    /** quanto (0..1) a peça [k] pode abrir sem entrar na parede ou em outro móvel */
    private fun openLimit(item: Item, g: GModel, k: Int): Float {
        val ni = g.animated[k]; val b = g.nodes[ni].bb
        if (b[0] > b[3]) return 1f
        val cx = item.x + item.ox + item.w / 2f; val cz = item.y + item.oz + item.h / 2f
        val inHouse = cx > 0f && cx < st.gw && cz > 0f && cz < st.gh
        var ok = 0f
        for (s in 1..12) {
            val u = s / 12f
            nodeWorld(item, g, ni, k, u, gmA)
            var hit = false
            for (c in 0 until 8) {
                val x = if (c and 1 != 0) b[3] else b[0]; val y = if (c and 2 != 0) b[4] else b[1]; val z = if (c and 4 != 0) b[5] else b[2]
                val wx = gmA[0] * x + gmA[4] * y + gmA[8] * z + gmA[12]
                val wy = gmA[1] * x + gmA[5] * y + gmA[9] * z + gmA[13]
                val wz = gmA[2] * x + gmA[6] * y + gmA[10] * z + gmA[14]
                if (inHouse && (wx < 0.01f || wx > st.gw - 0.01f || wz < 0.01f || wz > st.gh - 0.01f)) { hit = true; break }
                for (o in st.items) {
                    if (o === item || o.type.rug || o.type.dyn) continue
                    val h = Foot.height(o.type)
                    if (h < 0.1f || wy > h) continue
                    // colisores separados (pernas da mesa) contam um a um; senão, o retângulo do móvel
                    val rs = Foot.blockRects(o.type, o.rot, o.x, o.y, o.ox, o.oz) ?: listOf(o.rect())
                    if (rs.any { r -> wx > r[0] && wx < r[2] && wz > r[1] && wz < r[3] }) { hit = true; break }
                }
                if (hit) break
            }
            if (hit) break
            ok = u
        }
        return ok
    }

    private fun togglePart(item: Item, k: Int) {
        val g = Glb.get(item.type.glb ?: return) ?: return
        val tgt = item.animTgt ?: return; val lim = item.animLim ?: return
        if (k !in tgt.indices) return
        if (tgt[k] > 0.5f) { tgt[k] = 0f; saveReq = true; return }
        val l = openLimit(item, g, k)
        if (l < 0.15f) { msgText = "Sem espaço para abrir"; msgT = 1.4f; return }
        lim[k] = l; tgt[k] = 1f; saveReq = true
        if (l < 0.99f) { msgText = "Abriu até onde deu"; msgT = 1.2f }
    }

    /** Desenha um objeto GLB: estático (centro do item) ou com física (pose do corpo). */
    private fun drawGlbItem(item: Item, now: Long) {
        val g = Glb.get(item.type.glb ?: return) ?: return
        g.ensureGl()
        val b = item.body
        if (b != null) {
            Matrix.setIdentityM(baseM, 0)
            Matrix.translateM(baseM, 0, b.p[0], b.p[1], b.p[2])
            val r = b.r
            gmA[0] = r[0]; gmA[1] = r[3]; gmA[2] = r[6]; gmA[3] = 0f
            gmA[4] = r[1]; gmA[5] = r[4]; gmA[6] = r[7]; gmA[7] = 0f
            gmA[8] = r[2]; gmA[9] = r[5]; gmA[10] = r[8]; gmA[11] = 0f
            gmA[12] = 0f; gmA[13] = 0f; gmA[14] = 0f; gmA[15] = 1f
            Matrix.multiplyMM(gmB, 0, baseM, 0, gmA, 0)
            Matrix.translateM(gmB, 0, 0f, -b.comY, 0f)
            System.arraycopy(gmB, 0, baseM, 0, 16)
        } else {
            itemBase(item, baseM)
            val age = if (item.born == 0L) 99f else (now - item.born) / 1e9f
            if (age < 0.4f) {
                val u = age / 0.4f - 1f
                val s = (1f + 2.70158f * u * u * u + 1.70158f * u * u).coerceAtLeast(0.01f)
                Matrix.scaleM(baseM, 0, s, s, s)
            }
            if (item === grabbed) { baseM[13] += 0.08f }
        }
        val nodes = g.nodes
        if (nodeW.size < nodes.size) nodeW = Array(nodes.size) { FloatArray(16) }
        val cur = item.animCur
        val vm = g.meshes(item.cores)      // Etapa 172: malhas com as cores escolhidas (null = padrão)
        for (i in nodes.indices) {
            val n = nodes[i]
            val slot = g.animSlot[i]
            val u = if (slot >= 0) (cur?.getOrNull(slot) ?: 0f) else 0f
            n.local(gmL, n.value(u))
            val pw = if (n.parent >= 0 && n.parent < i) nodeW[n.parent] else baseM
            Matrix.multiplyMM(nodeW[i], 0, pw, 0, gmL, 0)
            val sw = g.showWhen[i]
            if (sw != null && sw.none { (cur?.getOrNull(it) ?: 0f) > 0.02f }) continue      // conteúdo interno com tudo fechado: não desenha
            val ef = g.effect[i]
            if (ef != 0) {
                val w = g.effectWhen[i]
                val active = if (w < 0) item.on else (cur?.getOrNull(w) ?: 0f) > 0.08f
                if (!active) continue
                val tt = (now / 1_000_000L % 100000L) / 1000f
                if (ef == 1) Matrix.scaleM(nodeW[i], 0, 1f, 0.82f + 0.18f * sin(tt * 23f) * sin(tt * 7.3f + item.x) + 0.12f * sin(tt * 41f), 1f)
                if (ef == 2) Matrix.scaleM(nodeW[i], 0, 1f + 0.08f * sin(tt * 37f), 1f, 1f + 0.08f * cos(tt * 29f))
            }
            val ms = vm?.getOrNull(i) ?: n.mesh ?: continue
            // Etapa 87: água e vapor são translúcidos: vão para o fim do quadro (sem gravar profundidade), junto com os vidros
            if (ef == 2 || ef == 4) { lateQ.add(Pair(ms, nodeW[i].copyOf())); continue }
            draw(ms, nodeW[i], 1f)
            if (ms.parts.any { it.mat == Mt.GLASS }) glassQ.add(Pair(ms, nodeW[i].copyOf()))
        }
    }

    /** Etapa 89: a caixa (mundo) aparece na tela? false só se os 8 cantos estão todos do mesmo lado de fora de um plano. */
    private fun boxVisible(x0: Float, y0: Float, z0: Float, x1: Float, y1: Float, z1: Float): Boolean {
        var l = 0; var r = 0; var b = 0; var t = 0; var n = 0
        for (c in 0 until 8) {
            val x = if (c and 1 != 0) x1 else x0; val y = if (c and 2 != 0) y1 else y0; val z = if (c and 4 != 0) z1 else z0
            val cx = vp[0] * x + vp[4] * y + vp[8] * z + vp[12]
            val cy = vp[1] * x + vp[5] * y + vp[9] * z + vp[13]
            val cw = vp[3] * x + vp[7] * y + vp[11] * z + vp[15]
            if (cx < -cw) l++; if (cx > cw) r++; if (cy < -cw) b++; if (cy > cw) t++; if (cw < 0.05f) n++
        }
        return !(l == 8 || r == 8 || b == 8 || t == 8 || n == 8)
    }

    /** Etapa 87: partes de vidro (prateleiras da geladeira, visor do forno, gelo) e efeitos translúcidos dos GLB, desenhados por último */
    private val glassQ = ArrayList<Pair<Mesh, FloatArray>>()
    private val lateQ = ArrayList<Pair<Mesh, FloatArray>>()

    // ---------------------------------------------------------------- sentar
    /** deslocamento no mundo (x, z) da cadeira puxada no progresso [u] */
    private fun pullOff(o: Item, g: GModel, u: Float): FloatArray {
        if (pullSlot < 0) return floatArrayOf(0f, 0f)
        val nd = g.nodes[g.animated[pullSlot]]
        val v = nd.value(u)
        val a = toWorld(o, nd.ax[0] * v, nd.ax[2] * v); val b = toWorld(o, 0f, 0f)
        return floatArrayOf(a[0] - b[0], a[1] - b[1])
    }

    // ---------------------------------------------------------------- usar (abrir/fechar peça, ligar aparelho) com a animação de interagir
    private fun startUse(o: Item, k: Int) {
        // Etapa 89: sem a animação de levantar a mão (pedido do jogador): a peça responde na hora
        if (USE_ANIM.not() || !CuteChar.hasInteract()) { applyUse(o, k); return }
        // vira para a alça (ou para o aparelho)
        var tx = o.x + o.ox + o.w / 2f; var tz = o.y + o.oz + o.h / 2f
        val g = o.type.glb?.let { Glb.get(it) }
        if (g != null && k >= 0) {
            val ni = g.animated[k]; val al = g.nodes[ni].anim?.optJSONArray("alca")
            if (al != null) {
                nodeWorld(o, g, ni, k, o.animCur?.getOrNull(k) ?: 0f, gmA)
                val lx = al.optDouble(0).toFloat() - g.rest[ni][12]; val ly = al.optDouble(1).toFloat() - g.rest[ni][13]; val lz = al.optDouble(2).toFloat() - g.rest[ni][14]
                tx = gmA[0] * lx + gmA[4] * ly + gmA[8] * lz + gmA[12]; tz = gmA[2] * lx + gmA[6] * ly + gmA[10] * lz + gmA[14]
            }
        }
        useYaw = Math.toDegrees(atan2((tx - px).toDouble(), (tz - pz).toDouble())).toFloat()
        useItem = o; useK = k; useT = 0f; useDone = false; usePh = 1
        jumping = false; py = 0f; vy = 0f; flying = false; landing = false; path = null; markX = Float.NaN
    }

    private fun applyUse(o: Item, k: Int) {
        if (k >= 0) togglePart(o, k) else { o.on = !o.on; saveReq = true }
    }

    private fun updateUse(dt: Float) {
        val o = useItem
        if (o == null || !st.items.contains(o)) { usePh = 0; return }
        val mag2 = moveX * moveX + moveY * moveY
        pMoving = false; pRun = false
        if (mag2 > 0.09f || (mode == 1 && path != null)) { usePh = 0; return }     // cancelou: se ainda não mexeu na peça, nada muda
        var dl = useYaw - pYaw
        while (dl > 180f) dl -= 360f
        while (dl < -180f) dl += 360f
        pYaw += dl.coerceIn(-480f * dt, 480f * dt)
        useT += dt
        // a mão chega na alça por volta de 0,55 s: aí a peça começa a se mexer
        if (!useDone && useT >= 0.55f) { useDone = true; applyUse(o, useK) }
        if (useT >= 1.6f) usePh = 0
    }

    private fun startSit(o: Item, seat: String, lie: Boolean, instant: Boolean = false) {
        crouch = false
        val g = Glb.get(o.type.glb ?: return) ?: return
        val nm = if (seat.isNotEmpty()) seat else (g.ips(if (lie) "IP_deitar" else "IP_sentar").firstOrNull()?.let { g.nodes[it].name } ?: return)
        val ip = g.point(nm) ?: return
        val ap = g.extraPoint(nm, "aproximacao") ?: return
        val ini = g.extraPoint(nm, "inicio") ?: return
        val sy = g.extraFloat(nm, "assento_y", 0.34f)
        if (nm in o.occ) return          // Etapa 87: ocupação por lugar/lado
        if (!CuteChar.hasSit()) {
            // sem os clipes de sentar (clips_<g>.bin com 8 clipes) ou corpo sem esqueleto do Sims: avisa em vez de sumir com o botão
            msgText = if (CuteChar.bodyGroup() == null) "Este corpo não tem animação de sentar" else "Falta a animação de sentar (etapa83-clipes.zip)"
            msgT = 2.5f
            return
        }
        val w0 = toWorld(o, ip[0], ip[2]); sitPt[0] = w0[0]; sitPt[1] = w0[1]
        val w1 = toWorld(o, ini[0], ini[2]); sitPt[2] = w1[0]; sitPt[3] = w1[1]
        var w2 = toWorld(o, ap[0], ap[2])
        // cadeira: puxada para trás antes de sentar; os pontos de início/chegada valem com ela puxada
        pullSlot = g.animated.indices.firstOrNull { g.slotGatilho[it] == "puxar" } ?: -1
        sitBase[0] = w0[0]; sitBase[1] = w0[1]
        if (pullSlot >= 0 && openLimit(o, g, pullSlot) < 0.99f) {
            // parede ou móvel atrás: não dá para puxar a cadeira inteira (o PDF manda nunca atravessar)
            pullSlot = -1; msgText = "Sem espaço para puxar a cadeira"; msgT = 1.6f; return
        }
        if (pullSlot >= 0) {
            val pn = g.nodes[g.animated[pullSlot]]
            pullPush = (pn.anim?.optDouble("empurrada", 0.7) ?: 0.7).toFloat().coerceIn(0f, 1f)
            val off = pullOff(o, g, 1f)
            sitPt[0] += off[0]; sitPt[1] += off[1]; sitPt[2] += off[0]; sitPt[3] += off[1]
            // chega pelo lado livre (esquerdo ou direito da cadeira)
            val wl = toWorld(o, ap[0], ap[2]); val wr = toWorld(o, -ap[0], ap[2])
            val cl = floatArrayOf(wl[0] + off[0], wl[1] + off[1]); val cr = floatArrayOf(wr[0] + off[0], wr[1] + off[1])
            val okl = !blockedAt(cl[0], cl[1]); val okr = !blockedAt(cr[0], cr[1])
            w2 = if (okl && (!okr || kotlin.math.hypot(px - cl[0], pz - cl[1]) <= kotlin.math.hypot(px - cr[0], pz - cr[1]))) cl else if (okr) cr else cl
            pullTgt = 1f
        }
        sitYaw = o.rot * 90f + Math.toDegrees(ip[3].toDouble()).toFloat()
        sitDY = (sy - CuteChar.sitSeat()).coerceIn(-0.015f, 0.25f)
        lieMode = false
        if (lie) {
            val dp = g.extraPoint(nm, "deitado") ?: return
            // deitado de costas: a cabeça no travesseiro (z da cabeça), os pés para o pé da cama
            val hsz = CuteChar.bodyTop()
            val wr = toWorld(o, dp[0], dp[2] + hsz)
            lieRoot[0] = wr[0]; lieRoot[1] = dp[1] + 0.105f; lieRoot[2] = wr[1]   // as costas do corpo ficam ~10 cm atrás da linha da raiz
            lieYaw = o.rot * 90f
            lieMode = true
        }
        if (instant) {
            // Etapa 87: volta dormindo na cama (estado salvo): sem caminho nem animação de entrada
            sitItem = o; sitSeat = nm; o.occ.add(nm); o.busy = true; sitPath = null; sitCancel = false; sitPressed = true
            px = sitPt[0]; pz = sitPt[1]; pYaw = sitYaw; sitLift = sitDY; lieK = 1f; lieT = 1f
            sitWhere[0] = o.x + o.ox; sitWhere[1] = o.y + o.oz; sitWhere[2] = o.rot.toFloat()
            jumping = false; py = 0f; vy = 0f; flying = false; landing = false; path = null; markX = Float.NaN
            sitPh = 10
            return
        }
        val pth: ArrayList<FloatArray> = if (kotlin.math.hypot(px - w2[0], pz - w2[1]) < 0.12f) ArrayList()
            else (planPath(w2[0], w2[1]) ?: run { msgText = "Não dá para chegar"; msgT = 1.4f; return })
        val sp = floatArrayOf(w1[0], w1[1])
        pth.add(sp)
        sitStartPt = sp
        sitPath = pth; sitItem = o; sitSeat = nm; sitT = 0f; sitStuck = 0f; sitCancel = false; sitPressed = false
        lieK = 0f; lieT = 0f
        sitWhere[0] = o.x + o.ox; sitWhere[1] = o.y + o.oz; sitWhere[2] = o.rot.toFloat()
        jumping = false; py = 0f; vy = 0f; flying = false; landing = false
        path = null; markX = Float.NaN
        sitPh = 1
    }

    // ---------------------------------------------------------------- Etapa 87: lavar as mãos na pia (IP_lavar)
    private var washPh = 0
    private var washT = 0f
    private var washItem: Item? = null
    private var washK = -1
    private var washYaw = 0f
    private var washDur = 3.5f
    private var washPath: ArrayList<FloatArray>? = null
    private var washStuck = 0f

    private fun startWash(o: Item, nm: String) {
        val g = Glb.get(o.type.glb ?: return) ?: return
        val ip = g.point(nm) ?: return
        val lvName = g.nodes[g.index(nm)].ex?.optString("alavanca", "") ?: ""
        val li = g.index(lvName)
        washK = if (li >= 0) g.animSlot[li] else -1
        washDur = g.extraFloat(nm, "duracao", 3.5f)
        val w = toWorld(o, ip[0], ip[2])
        washYaw = o.rot * 90f + Math.toDegrees(ip[3].toDouble()).toFloat() + 180f      // olhar -Z: virado para a pia
        val pth = if (kotlin.math.hypot(px - w[0], pz - w[1]) < 0.1f) ArrayList() else (planPath(w[0], w[1]) ?: run { msgText = "Não dá para chegar"; msgT = 1.4f; return })
        pth.add(floatArrayOf(w[0], w[1]))
        washPath = pth; washItem = o; washT = 0f; washStuck = 0f
        jumping = false; py = 0f; vy = 0f; flying = false; landing = false; path = null; markX = Float.NaN
        washPh = 1
    }

    private fun updateWash(dt: Float) {
        val o = washItem
        if (o == null || !st.items.contains(o)) { washPh = 0; return }
        val mag2 = moveX * moveX + moveY * moveY
        pRun = false
        if (mag2 > 0.09f || (mode == 1 && path != null)) { washPh = 0; pMoving = false; return }
        val tgt = o.animTgt
        fun lever(on: Boolean) { if (washK >= 0 && tgt != null && washK < tgt.size && (tgt[washK] > 0.5f) != on) togglePart(o, washK) }
        when (washPh) {
            1 -> {
                val pth = washPath
                if (pth == null || pth.isEmpty()) { washPh = 2; pMoving = false; return }
                var budget = WALK_SPEED * dt
                val bx = px; val bz = pz
                while (budget > 0f && pth.isNotEmpty()) {
                    val wpt = pth[0]
                    val dx = wpt[0] - px; val dz = wpt[1] - pz
                    val d = sqrt(dx * dx + dz * dz)
                    if (d < 0.02f) { pth.removeAt(0); continue }
                    val s2 = min(d, budget)
                    val mx = dx / d * s2; val mz = dz / d * s2
                    if (walkable(px + mx, pz, px, pz)) px += mx
                    if (walkable(px, pz + mz, px, pz)) pz += mz
                    val dir = Math.toDegrees(atan2(dx.toDouble(), dz.toDouble())).toFloat()
                    var dl = dir - pYaw
                    while (dl > 180f) dl -= 360f
                    while (dl < -180f) dl += 360f
                    pYaw += dl * min(1f, dt * 12f)
                    budget -= s2
                    if (s2 < d) break
                }
                pMoving = true
                if (kotlin.math.hypot(px - bx, pz - bz) < 0.0005f && pth.isNotEmpty()) washStuck += dt else washStuck = 0f
                if (washStuck > 1.0f) { msgText = "Não dá para chegar"; msgT = 1.4f; washPh = 0; pMoving = false; return }
                if (pth.isEmpty()) { washPh = 2; pMoving = false }
            }
            2 -> {
                pMoving = false
                var dl = washYaw - pYaw
                while (dl > 180f) dl -= 360f
                while (dl < -180f) dl += 360f
                pYaw += dl.coerceIn(-330f * dt, 330f * dt)
                if (abs(dl) < 1.5f) { pYaw = washYaw; washPh = 3; washT = 0f }
            }
            3 -> {   // abre a torneira (sem levantar a mão)
                pMoving = false; lever(true); washPh = 4; washT = 0f
            }
            4 -> {   // lavando: água correndo na cuba
                pMoving = false; washT += dt
                if (washT >= washDur) { washPh = 5; washT = 0f }
            }
            5 -> {   // fecha a torneira
                pMoving = false; lever(false); washPh = 0
            }
        }
    }

    private fun occ(o: Item?, v: Float) { if (o != null && o === sitItem) sitPressed = v > 0.5f }

    /** matriz do personagem: posição e giro; deitando, também a inclinação para trás até ficar de costas na cama */
    private fun playerMatrix(out: FloatArray, up: Float) {
        Matrix.setIdentityM(out, 0)
        if (lieK <= 0.001f) {
            Matrix.translateM(out, 0, px, py + up + baseY + sitLift, pz)
            Matrix.rotateM(out, 0, pYaw, 0f, 1f, 0f)
            if (flyTilt > 0.5f && (flying || landing)) { Matrix.translateM(out, 0, 0f, 0.95f, 0f); Matrix.rotateM(out, 0, flyTilt, 1f, 0f, 0f); Matrix.translateM(out, 0, 0f, -0.95f, 0f) }
            return
        }
        val k = smooth(lieK)
        val x = px + (lieRoot[0] - px) * k
        val y = (py + up + baseY + sitLift) * (1f - k) + lieRoot[1] * k + 0.08f * sin(Math.PI.toFloat() * k)
        val z = pz + (lieRoot[2] - pz) * k
        Matrix.translateM(out, 0, x, y, z)
        // rotação: slerp entre Ry(pYaw) (sentado) e Ry(lieYaw)*Rx(-90°) (deitado de costas)
        val a = Math.toRadians(pYaw.toDouble()) / 2
        val q0y = Math.sin(a); val q0w = Math.cos(a)
        val b = Math.toRadians(lieYaw.toDouble()) / 2; val c = Math.toRadians(-90.0) / 2
        var q1w = Math.cos(b) * Math.cos(c); var q1x = Math.cos(b) * Math.sin(c); var q1y = Math.sin(b) * Math.cos(c); var q1z = -Math.sin(b) * Math.sin(c)
        var dot = q0y * q1y + q0w * q1w
        if (dot < 0) { dot = -dot; q1x = -q1x; q1y = -q1y; q1z = -q1z; q1w = -q1w }
        val om = Math.acos(dot.coerceIn(-1.0, 1.0)); val so = Math.sin(om)
        val w0 = if (so < 1e-6) 1 - k.toDouble() else Math.sin((1 - k) * om) / so
        val w1 = if (so < 1e-6) k.toDouble() else Math.sin(k * om) / so
        val qx = w1 * q1x; val qy = w0 * q0y + w1 * q1y; val qz = w1 * q1z; val qw = w0 * q0w + w1 * q1w
        val l = Math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw)
        val cw = (qw / l).coerceIn(-1.0, 1.0)
        val ang = 2 * Math.acos(cw)
        val sn = Math.sqrt(1 - cw * cw)
        if (sn > 1e-6) Matrix.rotateM(out, 0, Math.toDegrees(ang).toFloat(), (qx / l / sn).toFloat(), (qy / l / sn).toFloat(), (qz / l / sn).toFloat())
    }

    private fun sitAbort() {
        sitItem?.let { it.occ.remove(sitSeat); it.busy = it.occ.isNotEmpty(); if (it.sleep.isNotEmpty()) { it.sleep = ""; saveReq = true } }
        sitPressed = false
        pullTgt = 0f
        sitItem = null; sitPh = 0; sitLift = 0f; sitPath = null; pMoving = false; lieK = 0f; lieMode = false
    }

    private fun smooth(x: Float): Float { val c = x.coerceIn(0f, 1f); return c * c * (3f - 2f * c) }

    private fun updateSit(dt: Float) {
        val o = sitItem
        if (o == null || !st.items.contains(o) || o === grabbed ||
            abs(o.x + o.ox - sitWhere[0]) > 0.01f || abs(o.y + o.oz - sitWhere[1]) > 0.01f || o.rot.toFloat() != sitWhere[2]) { sitAbort(); return }
        val mag2 = moveX * moveX + moveY * moveY
        val out = sitCancel || mag2 > 0.09f || (mode == 1 && path != null)
        sitCancel = false
        pRun = false
        when (sitPh) {
            1 -> {
                if (out) { sitAbort(); return }
                val pth = sitPath
                if (pth == null || pth.isEmpty()) { sitPh = 2; sitT = 0f; pMoving = false; return }
                var budget = WALK_SPEED * dt
                val bx = px; val bz = pz
                while (budget > 0f && pth.isNotEmpty()) {
                    val w = pth[0]
                    val dx = w[0] - px; val dz = w[1] - pz
                    val d = sqrt(dx * dx + dz * dz)
                    if (d < 0.02f) { pth.removeAt(0); continue }
                    val s = min(d, budget)
                    val mx = dx / d * s; val mz = dz / d * s
                    if (w === sitStartPt) { px += mx; pz += mz }          // último passo: entra na folga do próprio assento
                    else {
                        if (walkable(px + mx, pz, px, pz)) px += mx
                        if (walkable(px, pz + mz, px, pz)) pz += mz
                    }
                    val dir = Math.toDegrees(atan2(dx.toDouble(), dz.toDouble())).toFloat()
                    var dl = dir - pYaw
                    while (dl > 180f) dl -= 360f
                    while (dl < -180f) dl += 360f
                    pYaw += dl * min(1f, dt * 12f)
                    budget -= s
                    if (s < d) break
                }
                pMoving = true
                if (kotlin.math.hypot(px - bx, pz - bz) < 0.0005f && pth.isNotEmpty()) sitStuck += dt else sitStuck = 0f
                if (sitStuck > 1.0f) { msgText = "Não dá para chegar"; msgT = 1.4f; sitAbort(); return }
                if (pth.isEmpty()) { sitPh = 2; sitT = 0f; pMoving = false }
            }
            2 -> {
                if (out) { sitAbort(); return }
                pMoving = false
                var dl = sitYaw - pYaw
                while (dl > 180f) dl -= 360f
                while (dl < -180f) dl += 360f
                val st_ = 330f * dt
                pYaw += dl.coerceIn(-st_, st_)
                px += (sitPt[2] - px) * min(1f, dt * 10f); pz += (sitPt[3] - pz) * min(1f, dt * 10f)
                val pulled = pullSlot < 0 || (o.animCur?.getOrNull(pullSlot) ?: 1f) > 0.97f
                if (abs(dl) < 1.5f && pulled) {
                    pYaw = sitYaw; px = sitPt[2]; pz = sitPt[3]
                    o.busy = true; o.occ.add(sitSeat); sitPh = 3; sitT = 0f
                }
            }
            3 -> {
                pMoving = false; pYaw = sitYaw
                sitT += dt
                val dur = CuteChar.clipSeconds(CuteChar.SIT_IN)
                val u = sitT / dur
                val k = smooth(u / 0.55f)
                px = sitPt[2] + (sitPt[0] - sitPt[2]) * k; pz = sitPt[3] + (sitPt[1] - sitPt[3]) * k
                sitLift = sitDY * smooth((u - 0.35f) / 0.5f)
                if (u > 0.55f) occ(o, 1f)
                if (out) {
                    if (u < 0.35f) { sitAbort(); return }
                    sitPh = 5; sitT = 0f; return
                }
                if (u >= 1f) { sitT = 0f; sitPh = if (lieMode) 6 else 4; lieT = 0f; if (pullSlot >= 0) pullTgt = pullPush }
            }
            6 -> {
                pMoving = false; pYaw = sitYaw; px = sitPt[0]; pz = sitPt[1]; sitLift = sitDY
                lieT += dt; lieK = (lieT / 1.1f).coerceAtMost(1f)
                if (out) { sitPh = 8; lieT = lieK * 1.0f; return }
                if (lieK >= 1f) sitPh = 7
            }
            7 -> {
                pMoving = false; pYaw = sitYaw; px = sitPt[0]; pz = sitPt[1]; sitLift = sitDY; lieK = 1f
                if (out) { sitPh = 8; lieT = 1.0f }
            }
            10 -> {
                // Etapa 87: dormindo (botão Acordar volta para deitado; mexer o controle acorda e levanta)
                pMoving = false; pYaw = sitYaw; px = sitPt[0]; pz = sitPt[1]; sitLift = sitDY; lieK = 1f
                if (out) { o.sleep = ""; saveReq = true; sitPh = 8; lieT = 1.0f }
            }
            8 -> {
                pMoving = false; pYaw = sitYaw; px = sitPt[0]; pz = sitPt[1]; sitLift = sitDY
                lieT -= dt; lieK = (lieT / 1.0f).coerceIn(0f, 1f)
                if (lieK <= 0f) { sitPh = 5; sitT = 0f }
            }
            4 -> {
                pMoving = false; pYaw = sitYaw; sitLift = sitDY
                if (pullSlot >= 0) {
                    // sentado, a cadeira volta para a mesa levando o personagem junto
                    val g = Glb.get(o.type.glb ?: "")
                    val cur = o.animCur?.getOrNull(pullSlot) ?: 1f
                    val off = if (g != null) pullOff(o, g, cur) else floatArrayOf(0f, 0f)
                    px = sitBase[0] + off[0]; pz = sitBase[1] + off[1]
                    if (out) { sitPh = 9; pullTgt = 1f }
                } else {
                    px = sitPt[0]; pz = sitPt[1]
                    if (out) { sitPh = 5; sitT = 0f }
                }
            }
            9 -> {
                // afasta a cadeira da mesa (com o personagem) antes de levantar
                pMoving = false; pYaw = sitYaw; sitLift = sitDY
                val g = Glb.get(o.type.glb ?: "")
                val cur = o.animCur?.getOrNull(pullSlot) ?: 1f
                val off = if (g != null) pullOff(o, g, cur) else floatArrayOf(0f, 0f)
                px = sitBase[0] + off[0]; pz = sitBase[1] + off[1]
                if (cur > 0.97f) { sitPt[0] = px; sitPt[1] = pz; sitPh = 5; sitT = 0f }
            }
            5 -> {
                pMoving = false; pYaw = sitYaw
                sitT += dt
                val dur = CuteChar.clipSeconds(CuteChar.SIT_OUT)
                val u = sitT / dur
                if (u > 0.1f) occ(o, 0f)
                val k = smooth((u - 0.45f) / 0.5f)
                px = sitPt[0] + (sitPt[2] - sitPt[0]) * k; pz = sitPt[1] + (sitPt[3] - sitPt[1]) * k
                sitLift = sitDY * (1f - smooth(u / 0.6f))
                if (u >= 1f) { sitAbort(); px = sitPt[2]; pz = sitPt[3] }
            }
        }
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
