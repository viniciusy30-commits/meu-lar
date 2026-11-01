package com.vinicius.meular
// versao etapa20-pes-no-chao (codigo vivo do object CuteChar; se esta linha aparece no GitHub, este zip foi aplicado)

import android.content.res.AssetManager
import android.graphics.BitmapFactory
import android.opengl.GLES20
import android.opengl.GLUtils
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.nio.ShortBuffer

/**
 * Personagem modular (BoZo Stylized Modular Characters), convertido para assets/cute:
 *  - base.bin (CUT1): corpo + boca + cabeça + olhos + os clips Idle/Walk/Jump já "assados" em matrizes de osso por quadro;
 *  - p_*.bin (CUP1): uma peça por arquivo (roupa, cabelo, sapato...), só malha + pesos + UV para o MESMO esqueleto;
 *  - pieces.txt: manifesto das peças (slot|id|arquivo|textura) e a roupa padrão (outfit=slot/id,...).
 * A pele é feita na CPU a cada quadro: os 55 ossos são interpolados uma vez e cada peça ativa usa as mesmas matrizes,
 * então qualquer peça acompanha Idle/Walk/Jump sem alterar as animações.
 * Se o carregamento modular falhar, volta ao arquivo antigo f_1.bin (personagem inteiro, sem peças);
 * se isso também falhar, [frame] devolve null e o app usa o personagem antigo esculpido.
 */
object CuteChar {
    const val ENABLED = true
    /** Etapa 21: a pele recua 7 mm na profundidade para a roupa sempre ganhar (acaba o pisca-pisca/pele aparecendo no tecido). */
    private const val SKIN_PUSH = 0f
    const val IDLE = 0
    const val WALK = 1
    const val JUMP = 2
    const val RUN = 3   // Etapa 11: corrida (Slow_Run.fbx do Mixamo, ferramentas/etapa11_retarget.py)
    /** Velocidade de reprodução do andar (Etapa 11): o clip (Walking.fbx do Mixamo) anda a 1,335 m/s; × 0,96 = 1,28 m/s no jogo, sem o pé deslizar no chão. */
    private const val WALK_RATE = 0.96f
    /** Etapa 16: o masculino do pack usa as mesmas animações do feminino. true = volta aos clipes 4-6 (etapa 14). */
    private const val MALE_CLIPS = false
    // Etapa 17: no masculino os braços ficam mais junto do corpo (a pose A original abre ~26 graus e parece feminina).
    // Graus que o braço inteiro (ombro para baixo, mão e dedos) gira em direção ao corpo. 0 = como antes; 8 ficou colado demais; 12 encosta no quadril.
    private const val MALE_ARM_IN = 4f
    // Graus extras só do antebraço e da mão (em torno do cotovelo): deixa o cotovelo afastado e a mão perto da coxa.
    private const val MALE_FOREARM_IN = 6f
    private val ARM_L = IntArray(18) { if (it < 3) 10 + it else 22 + it }   // upperarm, lowerarm, hand, dedos (25..39)
    private val ARM_R = IntArray(18) { if (it < 3) 14 + it else 37 + it }   // idem, lado direito (40..54)
    private val slotArm = FloatArray(3)   // 0..1: suaviza a entrada/saída do ajuste dos braços (ex.: pulo)

    @Volatile var assets: AssetManager? = null

    /** true quando o personagem novo carregou e pode ser desenhado. */
    val ready: Boolean get() = ENABLED && loaded && cur != null

    /** true quando está usando base.bin + peças (false = reserva f_1.bin inteiro). */
    @Volatile var modular = false
        private set

    /** Malha rígida que segue o esqueleto: o corpo-base ou uma peça. */
    private class Skin(
        val key: String,
        val tex: String,
        val nv: Int,
        val ni: Int,
        val pos: FloatArray,      // 3 por vértice (pose de referência)
        val nor: FloatArray,      // 3 por vértice
        val bi: IntArray,         // 4 por vértice
        val bw: FloatArray,       // 4 por vértice
        val out: FloatArray,      // STRIDE por vértice (já com cor e UV; pos/normal são reescritos por quadro)
        val fb: FloatBuffer,
        val ib: ShortBuffer,
        val idx: ShortArray       // índices (cópia em array, para o corpo-base poder esconder triângulos)
    ) {
        var part: Part? = null
        var hide: ShortArray? = null   // triângulos do corpo-base cobertos por esta peça (Etapa 4)
        val pos0: FloatArray = pos.copyOf()   // Etapa 7: posições originais de repouso (pos = pos0 com rosto/proporções aplicados)
        val nor0: FloatArray = nor.copyOf()   // Etapa 13: normais originais (nor = nor0 corrigida pela deformação)
        var warpVer = -1
        var foot: IntArray? = null   // Etapa 20: vértices da região do pé/sola (para apoiar a sola no chão)
    }

    /** Conjunto ativo: as peças e a malha pronta para desenhar (trocados juntos, sem quadro "pela metade"). */
    private class Active(val skins: List<Skin>, val mesh: Mesh)

    // Etapa 7: formato do rosto (morfos do corpo-base, de morph.bin) e proporções do corpo (BodyMorph, em todas as peças)
    private var morphIdx: Array<IntArray> = emptyArray()
    private var morphDel: Array<FloatArray> = emptyArray()
    @Volatile private var bodyP = FloatArray(BodyMorph.NB)
    @Volatile private var faceP = FloatArray(BodyMorph.NF)
    @Volatile private var shapeVer = 0
    @Volatile private var heightS = 1f
    @Volatile private var mascV = false   // Etapa 13: corpo masculino
    private var faceTmp = FloatArray(0)

    // Etapa 8: piscar e expressões (canais dinâmicos 13..17 do morph.bin; só rosto, não mexem nas animações)
    private val EXPR_N = 5   // 0 piscar, 1 feliz, 2 triste, 3 brava, 4 surpresa
    private val exprCur = FloatArray(EXPR_N)
    private val exprApplied = FloatArray(EXPR_N)
    private var fpAll = FloatArray(BodyMorph.NF + EXPR_N)
    @Volatile private var exprManual = -1      // -1 = automático; 0..3 = expressão escolhida no criador (0 neutra, 1 feliz, 2 triste, 3 brava, 4 surpresa)
    @Volatile private var exprAuto = 0         // expressão automática pedida pelo jogo (ex.: surpresa no pulo)
    private var blinkNext = 0L
    private var blinkStart = 0L
    private var exprNs = 0L
    private var exprForce = false

    /** Etapa 8: fixa uma expressão (0 neutra, 1 feliz, 2 triste, 3 brava, 4 surpresa) ou -1 para voltar ao automático. */
    fun setExpression(e: Int) {
        exprManual = if (e < 0) -1 else e.coerceIn(0, EXPR_N - 1)
    }

    private fun exprWeights(now: Long, wantAuto: Int) {
        var dt = (now - exprNs) / 1_000_000_000f
        if (dt < 0f || dt > 0.25f) dt = 0.016f
        exprNs = now
        val man = exprManual
        val tgt = if (man >= 0) man else wantAuto
        val k = (dt / 0.18f).coerceAtMost(1f)
        for (i in 1 until EXPR_N) {
            val goal = if (tgt == i) (if (man >= 0) 1f else 0.7f) else 0f
            exprCur[i] += (goal - exprCur[i]) * k
            if (Math.abs(exprCur[i] - goal) < 0.004f) exprCur[i] = goal
        }
        // piscar: a cada 2,5 a 5,5 s, fechando e abrindo em ~0,17 s (não pisca com expressão forte de surpresa/brava)
        if (blinkNext == 0L) blinkNext = now + 2_000_000_000L
        var bl = 0f
        if (blinkStart != 0L) {
            val u = (now - blinkStart) / 1_000_000_000f / 0.17f
            if (u >= 1f) blinkStart = 0L else bl = if (u < 0.4f) u / 0.4f else (1f - u) / 0.6f
        } else if (now >= blinkNext) {
            blinkStart = now
            blinkNext = now + (2_500_000_000L + (Math.random() * 3_000_000_000.0).toLong())
        }
        val blockBlink = exprCur[4] > 0.5f
        exprCur[0] = if (blockBlink) 0f else (bl * (1f - 0.6f * exprCur[1])).coerceIn(0f, 1f)
        // quantiza para não recalcular o rosto à toa
        for (i in 0 until EXPR_N) exprCur[i] = Math.round(exprCur[i] * 64f) / 64f
    }

    /** Etapa 7: controles do criador (inteiros -100..100): [body] na ordem de BodyMorph.BODY_NAMES, [face] na de FACE_NAMES. */
    fun setShape(body: IntArray, face: IntArray, masc: Boolean = false) {
        val b = FloatArray(BodyMorph.NB) { i -> if (i < body.size) body[i].coerceIn(-100, 100) / 100f else 0f }
        val f = FloatArray(BodyMorph.NF) { i ->
            var v = if (i < face.size) face[i].coerceIn(-100, 100) / 100f else 0f
            if (masc && i == 0) v = (v + BodyMorph.M_ROSTO).coerceAtMost(1.5f)   // Etapa 16: como o pack (BodyType 100), só a Masculinidade
            v * BodyMorph.FACE_GAIN[i]
        }
        mascV = masc
        heightS = BodyMorph.heightScale(b[0]) * (if (masc) BodyMorph.M_ALTURA else 1f)
        bodyP = b
        faceP = f
        shapeVer++
    }

    private var nb = 0
    private var clipLen = FloatArray(0)
    private var clipFrames = IntArray(0)
    private var clipData = arrayOfNulls<FloatArray>(0) // frames * nb * 12
    private var baseSkin: Skin? = null
    private val library = LinkedHashMap<String, Skin>()   // todas as peças conhecidas, na ordem do manifesto
    @Volatile private var wanted: List<String> = emptyList()
    @Volatile private var cur: Active? = null
    private val texIds = HashMap<String, Int>()
    private var loaded = false
    private var failed = false
    private var atlasTex = 0
    private var hairTex = 0
    private var extra2Tex = 0
    @Volatile private var wear: Set<String>? = null   // null = roupa padrão do manifesto (a Mary)
    private val MANAGED = setOf("hairBack", "hairFront", "top", "bottom", "overall", "feet", "gloves", "hat", "glasses", "beard", "headAcc")

    /** Chaves ("slot/id") de todas as peças disponíveis. */
    fun available(): List<String> = library.keys.toList()

    /** Peças em uso agora (chaves "slot/id", na ordem de desenho). */
    fun outfit(): List<String> = wanted

    /** Troca a roupa: lista de chaves "slot/id". Chaves desconhecidas são ignoradas. A ordem de desenho é a do manifesto. */
    fun setOutfit(keys: List<String>) {
        wanted = keys.toList()
        rebuildActive()
    }

    /** Etapas 3 e 4: peças escolhidas no criador (chaves "slot/id" de cabelo, blusa, calça/saia, vestido e roupa de baixo). */
    fun setWear(keys: List<String>) {
        wear = keys.toSet()
        rebuildActive()
    }

    private fun rebuildActive() {
        val bs = baseSkin ?: return
        val bp = bs.part ?: return        // GL ainda não pronto: o initGl chama de novo
        val w = wear
        val act = ArrayList<Skin>()
        val parts = ArrayList<Part>()
        val hide = BooleanArray(bs.ni / 3)
        var anyHide = false
        for ((k, s) in library) {
            val slot = k.substringBefore('/')
            val on = if (w != null && slot in MANAGED) k in w else k in wanted
            if (!on) continue
            val p = s.part ?: continue
            act.add(s)
            parts.add(p)
            s.hide?.let { h ->
                for (t in h) {
                    val ti = t.toInt() and 0xFFFF
                    if (ti < hide.size) { hide[ti] = true; anyHide = true }
                }
            }
        }
        // corpo-base: sem os triângulos cobertos pelas roupas (a pele não atravessa o tecido)
        var body = bp
        if (anyHide) {
            var keep = 0
            for (h in hide) if (!h) keep++
            val ib = ByteBuffer.allocateDirect(keep * 3 * 2).order(ByteOrder.nativeOrder()).asShortBuffer()
            for (t in hide.indices) {
                if (hide[t]) continue
                ib.put(bs.idx[t * 3]); ib.put(bs.idx[t * 3 + 1]); ib.put(bs.idx[t * 3 + 2])
            }
            ib.position(0)
            body = Part(Mt.PLAIN, bs.fb, bs.nv, ib, keep * 3, bp.tex)
            body.push = SKIN_PUSH
        }
        parts.add(0, body)
        cur = Active(act, Mesh(parts))
    }

    /** Chamar na thread GL (onSurfaceCreated): carrega o modelo e cria as texturas. */
    fun initGl() {
        if (!ENABLED) return
        val am = assets ?: return
        try {
            if (!loaded && !failed) load(am)
            if (loaded) {
                texIds.clear()
                val names = LinkedHashSet<String>()
                baseSkin?.let { names.add(it.tex) }
                for (s in library.values) names.add(s.tex)
                for (n in names) texIds[n] = uploadTexture(am, n)
                baseSkin?.let { it.part = Part(Mt.PLAIN, it.fb, it.nv, it.ib, it.ni, texIds[it.tex] ?: 0).also { p -> p.push = SKIN_PUSH } }
                for (s in library.values) s.part = Part(Mt.PLAIN, s.fb, s.nv, s.ib, s.ni, texIds[s.tex] ?: 0)
                rebuildActive()
                atlasTex = texIds["textures.png"] ?: 0
                hairTex = texIds["extra.png"] ?: 0
                extra2Tex = texIds["extra2.png"] ?: 0
                CuteColor.start(am)   // Etapa 2: cores escolhidas (carrega em segundo plano e sobe a textura recolorida)
            }
        } catch (e: Throwable) {
            failed = true
            loaded = false
            cur = null
        }
    }

    private fun uploadTexture(am: AssetManager, name: String): Int {
        val ids = IntArray(1)
        GLES20.glGenTextures(1, ids, 0)
        val bmp = am.open("cute/$name").use { BitmapFactory.decodeStream(it) }
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, ids[0])
        GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bmp, 0)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)
        bmp.recycle()
        return ids[0]
    }

    private fun load(am: AssetManager) {
        try {
            loadModular(am)
            modular = true
        } catch (e: Throwable) {
            // modular falhou (arquivo ausente/corrompido): volta ao personagem inteiro antigo
            baseSkin = null
            library.clear()
            wanted = emptyList()
            morphIdx = emptyArray()
            morphDel = emptyArray()
            clipData = arrayOfNulls(0)
            modular = false
            loadLegacy(am)
        }
        loaded = true
    }

    private fun loadModular(am: AssetManager) {
        baseSkin = readBase(am, "cute/base.bin", "base", "textures.png")
        loadMorph(am, baseSkin!!.nv)
        library.clear()
        var outfit: List<String> = emptyList()
        val lines = am.open("cute/pieces.txt").bufferedReader(Charsets.UTF_8).use { it.readLines() }
        for (raw in lines) {
            val ln = raw.trim()
            if (ln.isEmpty() || ln.startsWith("#")) continue
            if (ln.startsWith("outfit=")) {
                outfit = ln.substring(7).split(',').map { it.trim() }.filter { it.isNotEmpty() }
                continue
            }
            val f = ln.split('|').map { it.trim() }
            require(f.size >= 4)
            val key = f[0] + "/" + f[1]
            library[key] = readPiece(am, "cute/" + f[2], key, f[3])
        }
        wanted = outfit
    }

    /** CMF1: "CMF1", nCanais, e por canal: n, n x (índice do vértice do base.bin, dx, dy, dz). Se faltar, o rosto fica sem controles. */
    private fun loadMorph(am: AssetManager, nvBase: Int) {
        morphIdx = emptyArray()
        morphDel = emptyArray()
        try {
            val raw = am.open("cute/morph.bin").use { it.readBytes() }
            val b = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN)
            require(b.get().toInt() == 'C'.code && b.get().toInt() == 'M'.code && b.get().toInt() == 'F'.code && b.get().toInt() == '1'.code)
            val nc = b.int
            val ix = ArrayList<IntArray>()
            val dl = ArrayList<FloatArray>()
            for (c in 0 until nc) {
                val n = b.int
                val a = IntArray(n)
                val d = FloatArray(n * 3)
                for (k in 0 until n) {
                    a[k] = b.int
                    d[k * 3] = b.float
                    d[k * 3 + 1] = b.float
                    d[k * 3 + 2] = b.float
                    require(a[k] in 0 until nvBase)
                }
                ix.add(a)
                dl.add(d)
            }
            morphIdx = ix.toTypedArray()
            morphDel = dl.toTypedArray()
        } catch (e: Throwable) {
            morphIdx = emptyArray()
            morphDel = emptyArray()
        }
    }

    /** Recalcula as posições de repouso de uma malha: (rosto, só no corpo-base) e depois as proporções do corpo. */
    private fun refit(s: Skin, isBase: Boolean, ver: Int, bp: FloatArray, fp: FloatArray) {
        var src = s.pos0
        if (isBase && morphIdx.isNotEmpty()) {
            var any = false
            for (c in fp.indices) if (c < morphIdx.size && fp[c] != 0f) { any = true; break }
            if (any) {
                if (faceTmp.size != s.pos0.size) faceTmp = FloatArray(s.pos0.size)
                System.arraycopy(s.pos0, 0, faceTmp, 0, s.pos0.size)
                for (c in morphIdx.indices) {
                    val w = if (c < fp.size) fp[c] else 0f
                    if (w == 0f) continue
                    val ix = morphIdx[c]
                    val dl = morphDel[c]
                    for (k in ix.indices) {
                        val v = ix[k] * 3
                        faceTmp[v] += dl[k * 3] * w
                        faceTmp[v + 1] += dl[k * 3 + 1] * w
                        faceTmp[v + 2] += dl[k * 3 + 2] * w
                    }
                }
                src = faceTmp
            }
        }
        BodyMorph.warp(src, s.pos, s.nv, bp, mascV)
        BodyMorph.fixNormals(s.pos0, s.pos, s.nor0, s.nor, s.idx, s.ni, s.nv)   // Etapa 13: sombreado acompanha o busto/corpo novo
        s.warpVer = ver
    }

    private fun loadLegacy(am: AssetManager) {
        baseSkin = readBase(am, "cute/f_1.bin", "base", "textures.png")
        library.clear()
        wanted = emptyList()
    }

    /** CUT1: cabeçalho, vértices, índices e clips. O f_1.bin antigo tem o mesmo formato (só com mais vértices). */
    private fun readBase(am: AssetManager, path: String, key: String, tex: String): Skin {
        val raw = am.open(path).use { it.readBytes() }
        val b = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN)
        require(b.get().toInt() == 'C'.code && b.get().toInt() == 'U'.code && b.get().toInt() == 'T'.code && b.get().toInt() == '1'.code)
        val nv = b.int
        val ni = b.int
        nb = b.int
        val nc = b.int
        val sk = readSkin(b, key, tex, nv, ni)
        clipLen = FloatArray(nc)
        clipFrames = IntArray(nc)
        clipData = arrayOfNulls(nc)
        for (c in 0 until nc) {
            clipLen[c] = b.float
            val nf = b.int
            clipFrames[c] = nf
            val d = FloatArray(nf * nb * 12)
            for (i in d.indices) d[i] = b.float
            clipData[c] = d
        }
        return sk
    }

    /** CUP1: "CUP1", nv, ni, flags, vértices (44 bytes), índices locais (uint16) e, se flags&1, nHide + nHide ids (uint16) de triângulos do corpo cobertos. */
    private fun readPiece(am: AssetManager, path: String, key: String, tex: String): Skin {
        val raw = am.open(path).use { it.readBytes() }
        val b = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN)
        require(b.get().toInt() == 'C'.code && b.get().toInt() == 'U'.code && b.get().toInt() == 'P'.code && b.get().toInt() == '1'.code)
        val nv = b.int
        val ni = b.int
        val flags = b.int  // bit 0: depois dos índices vem a lista de triângulos do corpo que esta peça cobre
        val sk = readSkin(b, key, tex, nv, ni)
        if (flags and 1 != 0) {
            val nh = b.int
            val h = ShortArray(nh)
            for (i in 0 until nh) h[i] = b.short
            sk.hide = h
        }
        return sk
    }

    /** nv vértices (pos, normal, uv, cor, ossos, pesos) e ni índices, a partir da posição atual do buffer. */
    private fun readSkin(b: ByteBuffer, key: String, tex: String, nv: Int, ni: Int): Skin {
        val pos = FloatArray(nv * 3)
        val nor = FloatArray(nv * 3)
        val bi = IntArray(nv * 4)
        val bw = FloatArray(nv * 4)
        val out = FloatArray(nv * STRIDE)
        for (v in 0 until nv) {
            for (k in 0 until 3) pos[v * 3 + k] = b.float
            for (k in 0 until 3) nor[v * 3 + k] = b.float
            val u = b.float
            val w = b.float
            val o = v * STRIDE
            out[o + 10] = u
            out[o + 11] = w
            out[o + 6] = (b.get().toInt() and 255) / 255f
            out[o + 7] = (b.get().toInt() and 255) / 255f
            out[o + 8] = (b.get().toInt() and 255) / 255f
            out[o + 9] = (b.get().toInt() and 255) / 255f
            for (k in 0 until 4) bi[v * 4 + k] = b.get().toInt() and 255
            for (k in 0 until 4) bw[v * 4 + k] = (b.get().toInt() and 255) / 255f
        }
        val idx = ShortArray(ni)
        for (i in 0 until ni) idx[i] = b.short
        val fb = ByteBuffer.allocateDirect(nv * STRIDE * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
        val ib = ByteBuffer.allocateDirect(ni * 2).order(ByteOrder.nativeOrder()).asShortBuffer().also {
            it.put(idx)
            it.position(0)
        }
        return Skin(key, tex, nv, ni, pos, nor, bi, bw, out, fb, ib, idx)
    }

    /** Duração (s) do clip. */
    fun clipSeconds(clip: Int): Float =
        if (loaded && clip in clipLen.indices) clipLen[clip] else 1f

    // estado por "slot" (0 = jogador, 1 = avatar da casa, 2 = criador): fase do laço e transição suave
    private val slotClip = IntArray(3) { -1 }
    private val slotT0 = FloatArray(3)
    private val slotBlend = FloatArray(3)
    private val slotNs = LongArray(3)
    private val slotLast = arrayOfNulls<FloatArray>(3)
    private var bone = FloatArray(0)

    private fun smooth01(x: Float): Float {
        val c = if (x < 0f) 0f else if (x > 1f) 1f else x
        return c * c * (3f - 2f * c)
    }

    /**
     * Pose do clip [clip] no tempo [t] (segundos). Devolve a malha (corpo + peças ativas) pronta para desenhar.
     * Nos clips em laço (parado/andar) a fase recomeça do zero quando o clip muda, e a troca
     * de clip é suavizada (≈0,15 s), sem "pulo" de pose. [slot] separa quem está desenhando.
     */
    fun frame(clip: Int, t: Float, slot: Int = 0): Mesh? {
        val cs = cur ?: return null
        CuteColor.uploadIfPending(atlasTex, hairTex, extra2Tex)
        val bs = baseSkin ?: return null
        if (!loaded) return null
        // Etapa 14: corpo masculino usa clipes próprios (4 parado, 5 andar, 6 correr) quando existem no base.bin
        val c0 = clip.coerceIn(0, clipData.size - 1)
        val c = if (MALE_CLIPS && mascV && clipData.size >= 7 && (c0 == IDLE || c0 == WALK || c0 == RUN)) (if (c0 == IDLE) 4 else if (c0 == WALK) 5 else 6) else c0
        val sl = slot.coerceIn(0, slotClip.size - 1)
        val nf = clipFrames[c]
        val len = clipLen[c].coerceAtLeast(0.001f)
        val d = clipData[c] ?: return null
        val n12 = nb * 12
        if (bone.size != n12) bone = FloatArray(n12)

        val now = System.nanoTime()
        var dt = (now - slotNs[sl]) / 1_000_000_000f
        if (dt < 0f || dt > 0.25f) dt = 0.016f
        slotNs[sl] = now

        if (slotClip[sl] != c) {
            slotBlend[sl] = if (slotClip[sl] < 0) 0f else if (c == JUMP) 0.06f else 0.25f
            slotClip[sl] = c
            slotT0[sl] = t
        }
        var lt = if (c == JUMP) t else (t - slotT0[sl]) * (if (c0 == WALK) WALK_RATE else 1f)
        if (c != JUMP) {
            lt %= len
            if (lt < 0f) lt += len
        } else if (lt < 0f) lt = 0f

        val ft = (lt / len) * (nf - 1).coerceAtLeast(1)
        val f0 = ft.toInt().coerceIn(0, nf - 1)
        val f1 = (f0 + 1).coerceAtMost(nf - 1)
        val a = ft - f0
        val o0 = f0 * n12
        val o1 = f1 * n12
        for (j in 0 until n12) bone[j] = d[o0 + j] + (d[o1 + j] - d[o0 + j]) * a

        val prev = slotLast[sl]
        if (slotBlend[sl] > 0f && prev != null && prev.size == n12) {
            val dur = if (c == JUMP) 0.06f else 0.25f
            val k = smooth01(1f - slotBlend[sl] / dur)
            for (j in 0 until n12) bone[j] = prev[j] + (bone[j] - prev[j]) * k
            slotBlend[sl] -= dt
        } else {
            slotBlend[sl] = 0f
        }
        val keep: FloatArray = if (prev != null && prev.size == n12) prev else FloatArray(n12).also { slotLast[sl] = it }
        System.arraycopy(bone, 0, keep, 0, n12)

        // Etapa 17: braços do masculino mais para dentro (depois do keep, para não acumular na mistura entre clipes)
        val armTarget = if (!mascV) 0f else if (c0 == IDLE || c0 == WALK) 1f else if (c0 == RUN) 0.5f else 0f
        slotArm[sl] += (armTarget - slotArm[sl]) * (dt * 10f).coerceAtMost(1f)
        if (slotArm[sl] > 0.01f) armIn(bone, MALE_ARM_IN * slotArm[sl], MALE_FOREARM_IN * slotArm[sl])

        // as mesmas matrizes de osso vestem o corpo-base e todas as peças ativas
        // Etapa 7: rosto/proporções (só recalcula quando os controles mudam)
        val sv = shapeVer
        val bp = bodyP
        val fp0 = faceP
        if (sl == 0) exprAuto = if (c == JUMP) 4 else 0
        exprWeights(now, exprAuto)
        var exprChanged = false
        for (i in 0 until EXPR_N) if (exprCur[i] != exprApplied[i]) { exprChanged = true; break }
        if (fpAll.size != fp0.size + EXPR_N) fpAll = FloatArray(fp0.size + EXPR_N)
        System.arraycopy(fp0, 0, fpAll, 0, fp0.size)
        System.arraycopy(exprCur, 0, fpAll, fp0.size, EXPR_N)
        val fp = fpAll
        if (exprChanged) {
            System.arraycopy(exprCur, 0, exprApplied, 0, EXPR_N)
            refit(bs, true, sv, bp, fp)   // só o corpo-base tem o rosto
        } else if (bs.warpVer != sv) refit(bs, true, sv, bp, fp)
        skinInto(bs, bone)
        for (s in cs.skins) {
            if (s.warpVer != sv) refit(s, false, sv, bp, fp)
            skinInto(s, bone)
        }
        updateLift(sl, c, cs, bs, sv, dt)
        return cs.mesh
    }

    // ---- Etapa 20: sola apoiada no chão ----
    // A sola dos sapatos (All Star, chinelo, botas...) fica 1 a 3 cm ABAIXO do y=0 do corpo-base, então afundava no piso.
    // Para cada clip medimos o ponto mais baixo (corpo-base + sapato) e o personagem sobe essa distância ao ser desenhado.
    private var liftFor: Active? = null
    private var liftSv = -1
    private val liftClip = FloatArray(16) { Float.NaN }   // metros (já com a altura do personagem), um por clip
    private val slotLift = FloatArray(3)
    private val slotLiftOk = BooleanArray(3)

    /** Quanto (em metros) o personagem do slot [slot] deve subir no eixo Y para a sola ficar em cima do chão. Chamar logo depois de [frame]. */
    fun lift(slot: Int = 0): Float = slotLift[slot.coerceIn(0, slotLift.size - 1)]

    private fun updateLift(sl: Int, c: Int, cs: Active, bs: Skin, sv: Int, dt: Float) {
        try {
            if (liftFor !== cs || liftSv != sv) {
                java.util.Arrays.fill(liftClip, Float.NaN)
                liftFor = cs
                liftSv = sv
            }
            val known = c in liftClip.indices
            var target = if (known) liftClip[c] else Float.NaN
            if (target.isNaN()) {
                target = computeLift(c, cs, bs)
                if (known) liftClip[c] = target
            }
            if (!slotLiftOk[sl]) {
                slotLift[sl] = target
                slotLiftOk[sl] = true
            } else {
                slotLift[sl] += (target - slotLift[sl]) * (dt * 12f).coerceAtMost(1f)
            }
        } catch (e: Throwable) {
            slotLift[sl] = 0f
            slotLiftOk[sl] = true
        }
    }

    /** Vértices de repouso com y < 8 (sola, calcanhar, biqueira): só eles podem ser o ponto mais baixo. */
    private fun footIdx(s: Skin): IntArray {
        s.foot?.let { return it }
        var n = 0
        for (v in 0 until s.nv) if (s.pos0[v * 3 + 1] < 8f) n++
        val r = IntArray(n)
        var k = 0
        for (v in 0 until s.nv) if (s.pos0[v * 3 + 1] < 8f) r[k++] = v
        s.foot = r
        return r
    }

    /** Menor y (m) do corpo-base e dos sapatos em todos os quadros do clip; devolve a subida necessária (m), com folga de 1,5 mm. */
    private fun computeLift(c: Int, cs: Active, bs: Skin): Float {
        val d = clipData.getOrNull(c) ?: return 0f
        val nf = clipFrames[c]
        val n12 = nb * 12
        var low = 0f
        fun scan(s: Skin) {
            val ids = footIdx(s)
            val pos = s.pos
            for (f in 0 until nf) {
                val o = f * n12
                for (v in ids) {
                    val px = pos[v * 3]; val py = pos[v * 3 + 1]; val pz = pos[v * 3 + 2]
                    var y = 0f
                    for (k in 0 until 4) {
                        val w = s.bw[v * 4 + k]
                        if (w <= 0f) continue
                        val bo = o + s.bi[v * 4 + k] * 12
                        y += w * (d[bo + 4] * px + d[bo + 5] * py + d[bo + 6] * pz + d[bo + 7])
                    }
                    if (y < low) low = y
                }
            }
        }
        scan(bs)
        for (s in cs.skins) if (s.key.startsWith("feet/")) scan(s)
        val up = -low * heightS + 0.0015f
        return up.coerceIn(0f, 0.06f)
    }

    // Postura masculina dos braços, no plano frente (X/Y): deg gira o braço inteiro em torno do ombro e
    // deg2 gira só antebraço e mão em torno do cotovelo (cotovelo afastado, mão perto da coxa).
    // mm = matrizes 3x4 de osso (12 floats por osso). Ombro (13,3; 142,5; -2,9) e cotovelo (32,1; 122,0; 0) de repouso, em cm.
    private fun armIn(mm: FloatArray, deg: Float, deg2: Float) {
        for (side in 0..1) {
            val sx = if (side == 0) 1f else -1f
            val bones = if (side == 0) ARM_L else ARM_R
            rotArm(mm, bones, 0, 0, sx * 13.3f, 142.5f, -2.9f, -sx * Math.toRadians(deg.toDouble()))
            // cotovelo: usa a matriz do antebraço já com o giro do ombro
            rotArm(mm, bones, 1, 1, sx * 32.1f, 122.0f, 0f, -sx * Math.toRadians(deg2.toDouble()))
        }
    }

    // Gira os ossos da lista a partir do indice from, em torno do ponto de repouso (rx,ry,rz) posado pelo osso de indice pivotIdx.
    private fun rotArm(mm: FloatArray, bones: IntArray, pivotIdx: Int, from: Int, rx: Float, ry: Float, rz: Float, ang: Double) {
        val u = bones[pivotIdx] * 12
        val px = mm[u] * rx + mm[u + 1] * ry + mm[u + 2] * rz + mm[u + 3]
        val py = mm[u + 4] * rx + mm[u + 5] * ry + mm[u + 6] * rz + mm[u + 7]
        val c = Math.cos(ang).toFloat()
        val s = Math.sin(ang).toFloat()
        val tx = px - (c * px - s * py)
        val ty = py - (s * px + c * py)
        for (i in from until bones.size) {
            val o = bones[i] * 12
            for (k in 0..3) {
                val r0 = mm[o + k]
                val r1 = mm[o + 4 + k]
                mm[o + k] = c * r0 - s * r1
                mm[o + 4 + k] = s * r0 + c * r1
            }
            mm[o + 3] += tx
            mm[o + 7] += ty
        }
    }

    private fun skinInto(s: Skin, mm: FloatArray) {
        val pos = s.pos
        val nor = s.nor
        val bi = s.bi
        val bw = s.bw
        val out = s.out
        val hs = heightS
        for (v in 0 until s.nv) {
            val px = pos[v * 3]; val py = pos[v * 3 + 1]; val pz = pos[v * 3 + 2]
            val nx = nor[v * 3]; val ny = nor[v * 3 + 1]; val nz = nor[v * 3 + 2]
            var x = 0f; var y = 0f; var z = 0f
            var X = 0f; var Y = 0f; var Z = 0f
            for (k in 0 until 4) {
                val w = bw[v * 4 + k]
                if (w <= 0f) continue
                val bo = bi[v * 4 + k] * 12
                x += w * (mm[bo] * px + mm[bo + 1] * py + mm[bo + 2] * pz + mm[bo + 3])
                y += w * (mm[bo + 4] * px + mm[bo + 5] * py + mm[bo + 6] * pz + mm[bo + 7])
                z += w * (mm[bo + 8] * px + mm[bo + 9] * py + mm[bo + 10] * pz + mm[bo + 11])
                X += w * (mm[bo] * nx + mm[bo + 1] * ny + mm[bo + 2] * nz)
                Y += w * (mm[bo + 4] * nx + mm[bo + 5] * ny + mm[bo + 6] * nz)
                Z += w * (mm[bo + 8] * nx + mm[bo + 9] * ny + mm[bo + 10] * nz)
            }
            val o = v * STRIDE
            out[o] = x * hs; out[o + 1] = y * hs; out[o + 2] = z * hs
            val nl = Math.sqrt((X * X + Y * Y + Z * Z).toDouble()).toFloat()
            val inv = if (nl > 1e-9f) 1f / nl else 0f
            out[o + 3] = X * inv; out[o + 4] = if (nl > 1e-9f) Y * inv else 1f; out[o + 5] = Z * inv
        }
        val buf = s.fb
        buf.position(0)
        buf.put(out, 0, s.nv * STRIDE)
        buf.position(0)
    }
}
