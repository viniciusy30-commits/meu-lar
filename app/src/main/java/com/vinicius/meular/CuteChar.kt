package com.vinicius.meular
// versao etapa45-esqueleto-sims (etapa20-pes-no-chao) (codigo vivo do object CuteChar; se esta linha aparece no GitHub, este zip foi aplicado)

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
    const val RUNJUMP = 4   // Etapa 63: pulo correndo (só nos corpos do Sims; sem eles vira JUMP)
    const val RUN = 3   // Etapa 11: corrida (Slow_Run.fbx do Mixamo, ferramentas/etapa11_retarget.py)
    /** Etapa 83: sentar (entrar), sentado (laço) e levantar; só nos corpos do Sims (clips_<g>.bin com 8 clipes, ferramentas/etapa83_sentar.py) */
    const val SIT_IN = 5
    const val SIT_LOOP = 6
    const val SIT_OUT = 7
    /** Etapa 86: interagir (estica o braço e mexe na peça), clipe 8 */
    const val INTERACT = 8
    /** Etapa 88: agachado parado e andando agachado (Crouch_Idle_Loop / Crouch_Fwd_Loop da UAL), clipes 9 e 10 */
    const val CROUCH = 9
    const val CROUCH_WALK = 10
    /** Velocidade de reprodução do andar (Etapa 11): o clip (Walking.fbx do Mixamo) anda a 1,335 m/s; × 0,96 = 1,28 m/s no jogo, sem o pé deslizar no chão. */
    private const val WALK_RATE = 1.0f
    /** Etapa 16: o masculino do pack usa as mesmas animações do feminino. true = volta aos clipes 4-6 (etapa 14). */
    private const val MALE_CLIPS = true   // Etapa 23: parado e andar masculinos novos (clipes 4 e 5); correr continua o clipe 3
    // Etapa 17: no masculino os braços ficam mais junto do corpo (a pose A original abre ~26 graus e parece feminina).
    // Graus que o braço inteiro (ombro para baixo, mão e dedos) gira em direção ao corpo. 0 = como antes; 8 ficou colado demais; 12 encosta no quadril.
    private const val MALE_ARM_IN = 0f
    // Graus extras só do antebraço e da mão (em torno do cotovelo): deixa o cotovelo afastado e a mão perto da coxa.
    private const val MALE_FOREARM_IN = 3f
    private val ARM_L = IntArray(18) { if (it < 3) 10 + it else 22 + it }   // upperarm, lowerarm, hand, dedos (25..39)
    private val ARM_R = IntArray(18) { if (it < 3) 14 + it else 37 + it }   // idem, lado direito (40..54)
    private val slotFist = FloatArray(3)   // 0..1: mão fechando ao correr
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
        var mod = false              // peça importada de .package (Sims 2/3/4)
        var modAlpha = false         // textura com recorte (cabelo)
        var legCol = false           // saia rodada: as coxas empurram a malha para fora (colisão perna x saia, a cada quadro)
        var legMask: BooleanArray? = null   // vértices abaixo do quadril (os únicos que a colisão mexe)
        var legIdx: IntArray? = null        // índices dos vértices da máscara (a colisão só percorre estes)
        var legRef: FloatArray? = null      // folga de cada vértice até o eixo das coxas na pose parada (cm)
        var legRefVer = -1
        var legRefSet: Any? = null
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
    /** Etapa 74 (1ª pessoa): tudo acima desta altura (m) é recolhido num ponto no pescoço, para a cabeça não tapar a câmera. NaN = desligado. */
    @Volatile var hideAbove = Float.NaN   // (antigo, não usado)
    /** 1ª pessoa ligada: a cabeça sai da frente da câmera e o olho passa a seguir a cabeça animada. */
    @Volatile var fpOn = false
    /** Deslocamento extra do olho para a frente (m) quando olha para baixo. */
    @Volatile var fpAdjF = 0f
    /** Posição do olho no espaço do modelo (m): x, y, z (z = para a frente), seguindo a cabeça animada. */
    val fpEye = FloatArray(3)
    private var fpEyeInit = false
    private val fpRing = FloatArray(3)
    private var fpRingOk = false
    private var topRef = 0f
    private var fpRestTop = 0f   // altura do corpo-base na pose de repouso (cm)
    /** Distância (m) do olho à frente do eixo do corpo na 1ª pessoa (a câmera fica um pouco adiante do rosto). */
    const val FP_FWD = 0.13f
    @Volatile private var topObs = 0f   // topo da cabeça medido no último quadro (já com pose e escala)
    private val HEAD_SLOTS = setOf("hairBack", "hairFront", "hat", "glasses", "beard", "headAcc")
    /** Altura do corpo-base (m, já com a escala do personagem): topo da cabeça na pose de referência. */
    fun bodyTop(): Float {
        if (topObs > 0.8f) return topObs
        val bs = baseSkin ?: return 1.6f * heightS
        if (topRef <= 0f) {
            var m = 0f
            for (v in 0 until bs.nv) { val y = bs.pos[v * 3 + 1]; if (y > m) m = y }
            topRef = if (m > 0.5f && m < 3f) m else 1.7f
        }
        return topRef * heightS
    }
    @Volatile private var simOn = false       // Etapa 44
    @Volatile private var simH = 1f
    private val simRatio = HashMap<String, Float>()
    @Volatile private var texPending = false
    @Volatile private var mascV = false   // Etapa 13: corpo masculino
    // Etapa 50: tabela de pontos do esqueleto de cada corpo do Sims 3 (bodyrig.txt) e a tabela do corpo em uso
    private val rigs = HashMap<String, FloatArray>()
    @Volatile private var simKey = ""
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
    @Volatile private var simV = FloatArray(SimSliders.NS)   // Etapa 65: sliders do Sims 3 (-1..1)
    @Volatile private var simSlidersOn = false

    /** Etapa 65: o grupo do corpo do Sims 3 em uso ("af", "cu"...) ou null; usado pelo criador para saber se mostra os sliders do Sims. */
    fun simSlidersAvailable(): Boolean = simOn && SimSliders.ready

    fun setShape(body: IntArray, face: IntArray, masc: Boolean = false, ss: IntArray? = null) {
        if (ss != null) {
            val v = FloatArray(SimSliders.NS) { i -> if (i < ss.size) ss[i].coerceIn(-100, 100) / 100f else 0f }
            simV = v
            simSlidersOn = SimSliders.any(v)
        }
        val b = FloatArray(BodyMorph.NB) { i -> if (i < body.size) body[i].coerceIn(-100, 100) / 100f else 0f }
        val f = FloatArray(BodyMorph.NF) { i ->
            var v = if (i < face.size) face[i].coerceIn(-100, 100) / 100f else 0f
            if (masc && i == 0) v = (v + BodyMorph.M_ROSTO).coerceAtMost(1.5f)   // Etapa 16: como o pack (BodyType 100), só a Masculinidade
            v * BodyMorph.FACE_GAIN[i]
        }
        mascV = masc
        if (simOn) {   // Etapa 44: corpo do Sims 3; a altura vem da idade/sexo. Etapa 50: os 27 sliders de corpo valem aqui
            heightS = simH * BodyMorph.heightScale(b[0])
            bodyP = b
            faceP = FloatArray(BodyMorph.NF)
        } else {
            heightS = BodyMorph.heightScale(b[0]) * (if (masc) BodyMorph.M_ALTURA else 1f)
            bodyP = b
            faceP = f
        }
        shapeVer++
    }

    private var nb = 0
    // Etapa 45: conjunto de clipes trocado de uma vez (o corpo do Sims 3 tem esqueleto proprio, um conjunto por estagio+sexo)
    private class ClipSet(val len: FloatArray, val frames: IntArray, val data: Array<FloatArray?>)   // data: frames * nb * 12
    @Volatile private var clipSet = ClipSet(FloatArray(0), IntArray(0), arrayOfNulls(0))
    private var bozoClips: ClipSet? = null
    @Volatile private var simGrp = ""
    @Volatile private var simWant = ""      // Etapa 53: grupo desejado; frame() tenta de novo se os assets ainda não estavam prontos em setWear
    @Volatile private var simFail = false
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
    private var skateTex = 0
    @Volatile private var wear: Set<String>? = null   // null = roupa padrão do manifesto (a Mary)
    private val MANAGED = setOf("body", "hairBack", "hairFront", "top", "jacket", "bottom", "overall", "feet", "gloves", "hat", "glasses", "beard", "headAcc")

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
    @Volatile private var wearBodyKey: String? = null
    fun setWear(keys: List<String>) {
        wear = keys.toSet()
        wearBodyKey = keys.firstOrNull { it.startsWith("body/S_") }
        applySimState()
        rebuildActive()
    }

    /**
     * Etapa 44/45/50: estado do corpo do Sims 3 (altura, clipes de animação, tabela do esqueleto).
     * Corrige o T-pose ao abrir o jogo: o setWear do save rodava ANTES do initGl (sem clipes/alturas carregados),
     * então os clipes falhavam e o boneco ficava parado na pose original até o jogador escolher um corpo no criador.
     * Agora o initGl chama isto de novo, quando tudo já está carregado.
     */
    private fun applySimState() {
        val bk = wearBodyKey
        simOn = bk != null
        simH = if (bk != null) (simRatio[bk] ?: 1f) else 1f
        simWant = if (bk != null && bk.length >= 9) bk.substring(7, 9) + (if (bk.length >= 10 && bk[9] == '5') "5" else "") else ""   // Etapa 90f: corpo do TS4 usa clips_<g>5.bin (juntas do esqueleto original do TS4)
        simFail = false
        simTryNs = 0L
        useSimClips(simWant)   // Etapa 45: clipes do esqueleto do Sims (estagio+sexo)
        simKey = if (bk != null && bk.length >= 10) bk.substring(7) else ""   // Etapa 50: "body/S_af1" -> "af1"
        if (simOn) { heightS = simH * BodyMorph.heightScale(bodyP[0]); faceP = FloatArray(BodyMorph.NF); shapeVer++ }
    }
    @Volatile private var simTryNs = 0L

    /** Etapa 45: carrega clips_<grupo>.bin (CLP1: nb, nc, clipes) do esqueleto do Sims 3; "" volta aos clipes do base.bin. Falhando, mantém os atuais. */
    private fun useSimClips(grp: String) {
        if (grp == simGrp) return
        if (grp.isNotEmpty() && (assets == null || nb == 0 || !loaded)) return   // ainda não carregou: frame()/initGl tentam de novo
        try {
            if (grp.isEmpty()) {
                bozoClips?.let { clipSet = it }
                simGrp = ""
                return
            }
            val am = assets ?: return
            val raw = am.open("cute/clips_$grp.bin").use { it.readBytes() }
            val b = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN)
            require(b.get().toInt() == 'C'.code && b.get().toInt() == 'L'.code && b.get().toInt() == 'P'.code && b.get().toInt() == '1'.code)
            val nb2 = b.int
            val nc = b.int
            require(nb2 == nb && nc > 0)
            val len = FloatArray(nc)
            val fr = IntArray(nc)
            val data = arrayOfNulls<FloatArray>(nc)
            for (c in 0 until nc) {
                len[c] = b.float
                val nf = b.int
                fr[c] = nf
                val d = FloatArray(nf * nb * 12)
                b.asFloatBuffer().get(d)
                b.position(b.position() + d.size * 4)
                data[c] = d
            }
            clipSet = ClipSet(len, fr, data)
            simGrp = grp
        } catch (e: Throwable) {
            simFail = true
            android.util.Log.e("CuteChar", "clips_$grp.bin falhou", e)
        }
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
            val p = s.part
            if (p == null) { if (s.tex.startsWith("sk_")) texPending = true; continue }   // Etapa 44: textura ainda não subiu (próximo quadro)
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
        // peças importadas: esconde os triângulos do corpo do Sims que ficam por baixo do tecido
        val sims = act.firstOrNull { it.key.startsWith("body/S_") }
        val simsPart = sims?.part
        if (sims != null && simsPart != null) {
            val mk = BooleanArray(sims.ni / 3)
            var any = false
            var bidx: IntArray? = null
            for (m in act) {
                if (!m.mod || m.modAlpha) continue
                val sl = m.key.substringBefore('/')
                if (sl != "top" && sl != "jacket" && sl != "bottom" && sl != "overall" && sl != "feet") continue
                val ck = m.key + "@" + sims.key
                val cv = coverCache.getOrPut(ck) {
                    val bi = bidx ?: IntArray(sims.ni) { sims.idx[it].toInt() and 0xFFFF }.also { bidx = it }
                    val r = BooleanArray(sims.ni / 3)
                    val nk = rigs[simKey]?.let { it[19] } ?: 999f   // altura do pescoço: a pele do pescoço/cabeça nunca é escondida
                    val lim = if (sl == "top" || sl == "jacket" || sl == "overall") nk - 7f else 9999f
                    com.vinicius.meular.mods.Cover.mark(sims.pos0, bi, m.pos0, m.nor0, 3.2f, r, lim)
                    r
                }
                for (i in cv.indices) if (cv[i]) { mk[i] = true; any = true }
            }
            val at = parts.indexOf(simsPart)
            if (any && at >= 0) {
                var keep = 0
                for (h in mk) if (!h) keep++
                val ib = ByteBuffer.allocateDirect(keep * 3 * 2).order(ByteOrder.nativeOrder()).asShortBuffer()
                for (t in mk.indices) {
                    if (mk[t]) continue
                    ib.put(sims.idx[t * 3]); ib.put(sims.idx[t * 3 + 1]); ib.put(sims.idx[t * 3 + 2])
                }
                ib.position(0)
                parts[at] = Part(Mt.PLAIN, sims.fb, sims.nv, ib, keep * 3, simsPart.tex).also { it.soft = simsPart.soft; it.push = simsPart.push }
            }
        }
        // jaqueta vestida: some a manga da blusa/roupa de baixo (fica só o tronco, o resto da manga atravessaria a jaqueta)
        if (act.any { it.mod && it.key.startsWith("jacket/") }) {
            val rg = rigs[simKey]
            if (rg != null && rg.size >= 6) {
                val ux0 = rg[3] - rg[0]; val uy0 = rg[4] - rg[1]; val uz0 = rg[5] - rg[2]
                val ul = Math.sqrt((ux0 * ux0 + uy0 * uy0 + uz0 * uz0).toDouble()).toFloat().coerceAtLeast(1e-3f)
                val ux = ux0 / ul; val uy = uy0 / ul; val uz = uz0 / ul
                for (m in act) {
                    if (!m.mod || m.modAlpha) continue
                    val sl = m.key.substringBefore('/')
                    if (sl != "top" && sl != "overall") continue
                    val mp = m.part ?: continue
                    val at = parts.indexOf(mp)
                    if (at < 0) continue
                    val nt = m.ni / 3
                    val gone = BooleanArray(nt)
                    var keep = 0
                    for (t in 0 until nt) {
                        val a = m.idx[t * 3].toInt() and 0xFFFF; val b = m.idx[t * 3 + 1].toInt() and 0xFFFF; val c = m.idx[t * 3 + 2].toInt() and 0xFFFF
                        val cx = Math.abs(m.pos0[a * 3] + m.pos0[b * 3] + m.pos0[c * 3]) / 3f - rg[0]
                        val cy = (m.pos0[a * 3 + 1] + m.pos0[b * 3 + 1] + m.pos0[c * 3 + 1]) / 3f - rg[1]
                        val cz = (m.pos0[a * 3 + 2] + m.pos0[b * 3 + 2] + m.pos0[c * 3 + 2]) / 3f - rg[2]
                        val tt = cx * ux + cy * uy + cz * uz
                        val px = cx - tt * ux; val py = cy - tt * uy; val pz = cz - tt * uz
                        val perp = Math.sqrt((px * px + py * py + pz * pz).toDouble()).toFloat()
                        gone[t] = tt > 2f && tt < ul * 1.15f && perp < 14.5f
                        if (!gone[t]) keep++
                    }
                    val ib = ByteBuffer.allocateDirect(keep * 3 * 2).order(ByteOrder.nativeOrder()).asShortBuffer()
                    for (t in 0 until nt) {
                        if (gone[t]) continue
                        ib.put(m.idx[t * 3]); ib.put(m.idx[t * 3 + 1]); ib.put(m.idx[t * 3 + 2])
                    }
                    ib.position(0)
                    parts[at] = Part(Mt.PLAIN, m.fb, m.nv, ib, keep * 3, mp.tex).also { np -> np.cut = mp.cut; np.cull = mp.cull; np.solid = mp.solid; np.soft = mp.soft; np.push = mp.push }
                }
            }
        }
        cur = Active(act, Mesh(parts))
    }

    // ---- peças importadas de .package (ModStore) ----
    private class ModJob(val key: String, val cup: ByteArray?, val bmp: android.graphics.Bitmap?, val alpha: Boolean)
    private val modJobs = java.util.concurrent.ConcurrentLinkedQueue<ModJob>()
    private val coverCache = HashMap<String, BooleanArray>()

    /** Chamar de qualquer thread: coloca (ou troca) a peça importada [key]; cup == null remove. A GL cuida do resto no próximo quadro. */
    fun enqueueMod(key: String, cup: ByteArray?, bmp: android.graphics.Bitmap?, alpha: Boolean) {
        modJobs.add(ModJob(key, cup, bmp, alpha))
    }

    private fun runModJobs() {
        if (!loaded || baseSkin == null) return
        var changed = false
        while (true) {
            val j = modJobs.poll() ?: break
            try {
                val old = library.remove(j.key)
                if (old != null) {
                    val tid = texIds.remove(old.tex)
                    if (tid != null) GLES20.glDeleteTextures(1, intArrayOf(tid), 0)
                    coverCache.keys.removeAll { it.startsWith(j.key + "@") }
                    changed = true
                }
                if (j.cup == null || j.bmp == null) continue
                val tname = "mod:" + j.key
                val sk = readPieceBytes(j.cup, j.key, tname)
                sk.mod = true
                sk.modAlpha = j.alpha
                sk.legCol = j.key.startsWith("bottom/") && j.key.contains("autumn")
                val ids = IntArray(1)
                GLES20.glGenTextures(1, ids, 0)
                GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, ids[0])
                GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, j.bmp, 0)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)
                if (j.alpha) {
                    GLES20.glGenerateMipmap(GLES20.GL_TEXTURE_2D)
                    GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR_MIPMAP_LINEAR)
                }
                texIds[tname] = ids[0]
                sk.part = Part(Mt.PLAIN, sk.fb, sk.nv, sk.ib, sk.ni, ids[0]).also { p -> if (j.alpha) { p.cut = 0.45f; p.cull = false; p.solid = true } }
                library[j.key] = sk
                j.bmp.recycle()
                changed = true
            } catch (e: Throwable) {
                android.util.Log.e("CuteChar", "peça importada falhou: " + j.key, e)
            }
        }
        if (changed) rebuildActive()
    }

    /** Corpo do Sims em uso (tipo "normal" do grupo idade+sexo) como molde para encaixar peças importadas; null se não houver corpo do Sims. */
    fun bodyRef(): com.vinicius.meular.mods.BodyRef? {
        val grp = bodyGroup() ?: return null
        val key = "body/S_" + grp + "1"
        val sk = library[key] ?: return null
        val idx = IntArray(sk.ni) { sk.idx[it].toInt() and 0xFFFF }
        val rg = rigs[grp + "1"]
        val ratio = simRatio[key] ?: 1f
        return com.vinicius.meular.mods.BodyRef(sk.pos0.copyOf(), sk.nor0.copyOf(), sk.bi.copyOf(), sk.bw.copyOf(), idx, rg, 96.8f / ratio)
    }

    /** "af", "am", "tf", "cu", "pu"... do corpo atual (idade+sexo) ou null. */
    /** Etapa 91: corpo do The Sims 4 (chave "am5"/"af5"). */
    fun isTs4(): Boolean = simOn && simKey.length >= 3 && simKey[2] == '5'

    fun bodyGroup(): String? = if (simOn && simKey.length >= 2) simKey.substring(0, 2) else null

    /** Chamar na thread GL (onSurfaceCreated): carrega o modelo e cria as texturas. */
    fun initGl() {
        if (!ENABLED) return
        val am = assets ?: return
        try {
            if (!loaded && !failed) load(am)
            if (loaded) {
                library.entries.removeAll { it.value.mod }   // peças importadas sobem de novo (ModStore.requeue) depois
                coverCache.clear()
                texIds.clear()
                val names = LinkedHashSet<String>()
                baseSkin?.let { names.add(it.tex) }
                for (s in library.values) names.add(s.tex)
                // contexto GL novo (ex.: voltou do seletor de arquivos): as texturas de pele antigas morreram, sobem de novo sob demanda
                for (s in library.values) if (s.tex.startsWith("sk_")) s.part = null
                texPending = true
                for (n in names) if (!n.startsWith("sk_")) texIds[n] = uploadTexture(am, n)   // Etapa 44: atlas de pele do Sims 3 sobem só quando usados
                baseSkin?.let { it.part = Part(Mt.PLAIN, it.fb, it.nv, it.ib, it.ni, texIds[it.tex] ?: 0).also { p -> p.push = SKIN_PUSH } }
                for (s in library.values) if (!s.tex.startsWith("sk_")) s.part = Part(Mt.PLAIN, s.fb, s.nv, s.ib, s.ni, texIds[s.tex] ?: 0).also { p -> if (isAlphaHair(s.tex)) { p.cut = 0.45f; p.cull = true; p.solid = true } }   // Etapa 41: mechas com alfa
                applySimState()
                rebuildActive()
                atlasTex = texIds["textures.png"] ?: 0
                hairTex = texIds["extra.png"] ?: 0
                extra2Tex = texIds["extra2.png"] ?: 0
                skateTex = texIds["skatetee.png"] ?: 0
                CuteColor.start(am)   // Etapa 2: cores escolhidas (carrega em segundo plano e sobe a textura recolorida)
                ModStore.requeue()
            }
        } catch (e: Throwable) {
            failed = true
            loaded = false
            cur = null
        }
    }

    /** Etapa 42: cabelos de mod com mechas em alfa (Faye, Heartbeat): recorte opaco, culling, sem pré-multiplicar e com mipmaps. */
    private fun isAlphaHair(name: String) = name == "faye.png" || name == "heartbeat.png"

    private fun uploadTexture(am: AssetManager, name: String): Int {
        val ids = IntArray(1)
        GLES20.glGenTextures(1, ids, 0)
        val opts = BitmapFactory.Options()
        if (isAlphaHair(name)) opts.inPremultiplied = false   // Etapa 41: sem pré-multiplicar (senão o fundo transparente vira preto nas bordas das mechas)
        val bmp = am.open("cute/$name").use { BitmapFactory.decodeStream(it, null, opts) }!!
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, ids[0])
        GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bmp, 0)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)
        if (isAlphaHair(name)) {   // Etapa 41/42: mipmaps (mechas finas sem chiado)
            GLES20.glGenerateMipmap(GLES20.GL_TEXTURE_2D)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR_MIPMAP_LINEAR)
        }
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
            clipSet = ClipSet(FloatArray(0), IntArray(0), arrayOfNulls(0))
            modular = false
            loadLegacy(am)
        }
        loaded = true
    }

    private fun loadModular(am: AssetManager) {
        baseSkin = readBase(am, "cute/base.bin", "base", "textures.png")
        loadMorph(am, baseSkin!!.nv)
        loadRigs(am)
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
            if (f.size >= 5) f[4].toFloatOrNull()?.let { simRatio[key] = it }
        }
        wanted = outfit
    }

    /** Etapa 50: bodyrig.txt, uma linha por corpo: chave|23 valores (cm). Se faltar, os sliders novos não deformam nada. */
    private fun loadRigs(am: AssetManager) {
        rigs.clear()
        try { if (!SimSliders.ready) SimSliders.load(am.open("cute/simsliders.txt").bufferedReader(Charsets.UTF_8).use { it.readText() }) } catch (e: Throwable) { }
        try {
            am.open("cute/bodyrig.txt").bufferedReader(Charsets.UTF_8).use { rd ->
                for (raw in rd.readLines()) {
                    val ln = raw.trim()
                    if (ln.isEmpty()) continue
                    val f = ln.split('|')
                    if (f.size < 2) continue
                    val v = f[1].split(',').map { it.trim().toFloat() }
                    if (v.size >= BodyMorph.RIG_N) rigs[f[0].trim()] = v.toFloatArray()
                }
            }
        } catch (e: Throwable) {
            rigs.clear()
        }
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
        val rg = if (simOn) rigs[simKey] else null
        if (simOn && rg != null) {
            // Etapa 65: sliders reais do Sims 3 (ajustes de osso do BOND); sem eles o corpo fica exatamente como o original
            val k = rg[19] / SimSliders.neckY(simKey.substring(0, 2))
            if (!SimSliders.warp(src, s.pos, s.nv, simV, simKey.substring(0, 2), k, s.pos0)) System.arraycopy(src, 0, s.pos, 0, s.nv * 3)
        }
        else BodyMorph.warp(src, s.pos, s.nv, bp, mascV, !isBase && s.tex == "skatetee.png")
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
        val cLen = FloatArray(nc)
        val cFrames = IntArray(nc)
        val cData = arrayOfNulls<FloatArray>(nc)
        for (c in 0 until nc) {
            cLen[c] = b.float
            val nf = b.int
            cFrames[c] = nf
            val d = FloatArray(nf * nb * 12)
            for (i in d.indices) d[i] = b.float
            cData[c] = d
        }
        clipSet = ClipSet(cLen, cFrames, cData)
        bozoClips = clipSet
        simGrp = ""
        return sk
    }

    /** CUP1: "CUP1", nv, ni, flags, vértices (44 bytes), índices locais (uint16) e, se flags&1, nHide + nHide ids (uint16) de triângulos do corpo cobertos. */
    private fun readPiece(am: AssetManager, path: String, key: String, tex: String): Skin =
        readPieceBytes(am.open(path).use { it.readBytes() }, key, tex)

    private fun readPieceBytes(raw: ByteArray, key: String, tex: String): Skin {
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

    /** Etapa 83: o corpo atual tem os clipes de sentar? */
    fun hasSit(): Boolean = loaded && simGrp.isNotEmpty() && clipSet.data.size >= 8
    /** Etapa 86: o corpo atual tem o clipe de interagir? */
    fun hasInteract(): Boolean = loaded && simGrp.isNotEmpty() && clipSet.data.size >= 9
    /** Etapa 88: o corpo atual tem os clipes de agachar? */
    fun hasCrouch(): Boolean = loaded && simGrp.isNotEmpty() && clipSet.data.size >= 11

    private val sitSeats = HashMap<String, Float>()
    /** Etapa 83: altura (m) do assento que este personagem precisa sentado (traseiro), já com a altura do slider. */
    fun sitSeat(): Float {
        if (sitSeats.isEmpty()) {
            try {
                assets?.open("cute/sit.txt")?.bufferedReader()?.useLines { ls ->
                    for (ln in ls) {
                        if (ln.startsWith("#") || ln.isBlank()) continue
                        val f = ln.split('|')
                        if (f.size >= 2) f[1].toFloatOrNull()?.let { sitSeats[f[0]] = it }
                    }
                }
            } catch (e: Throwable) { }
        }
        val base = sitSeats[simGrp] ?: sitSeats[simGrp.take(2)] ?: 0.335f
        val k = if (simH > 0.05f) heightS / simH else 1f
        return base * k
    }

    /** Duração (s) do clip. */
    fun clipSeconds(clip: Int): Float =
        clipSet.let { if (loaded && clip in it.len.indices) it.len[clip] else 1f }

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
    /** Etapa 44: sobe (na thread GL) a textura de pele do Sims 3 das peças em uso e refaz o conjunto ativo. */
    private fun loadPendingTex() {
        val am = assets ?: return
        texPending = false
        val w = wear ?: return
        var any = false
        try {
            for ((k, s) in library) {
                if (s.part != null || !s.tex.startsWith("sk_") || k !in w) continue
                val id = texIds.getOrPut(s.tex) { uploadTexture(am, s.tex) }
                s.part = Part(Mt.PLAIN, s.fb, s.nv, s.ib, s.ni, id).also { p -> p.soft = true }   // Etapa 47: pele sem estourar
                any = true
            }
        } catch (e: Throwable) {
        }
        if (any) rebuildActive()
    }

    fun frame(clip: Int, t: Float, slot: Int = 0): Mesh? {
        if (texPending) loadPendingTex()
        if (!modJobs.isEmpty()) runModJobs()
        if (simWant != simGrp && assets != null) {
            val nowT = System.nanoTime()
            if (!simFail || nowT - simTryNs > 1_500_000_000L) { simTryNs = nowT; useSimClips(simWant) }
        }
        val cs = cur ?: return null
        CuteColor.uploadIfPending(atlasTex, hairTex, extra2Tex, skateTex)
        val bs = baseSkin ?: return null
        if (!loaded) return null
        // Etapa 14: corpo masculino usa clipes próprios (4 parado, 5 andar, 6 correr) quando existem no base.bin
        val cset = clipSet
        val clipR = if (clip == RUNJUMP && (simGrp.isEmpty() || cset.data.size < 5)) JUMP else clip
        val c0 = clipR.coerceIn(0, cset.data.size - 1)
        val c = if (MALE_CLIPS && mascV && simGrp.isEmpty() && cset.data.size >= 7 && (c0 == IDLE || c0 == WALK)) (if (c0 == IDLE) 4 else 5) else c0
        val sl = slot.coerceIn(0, slotClip.size - 1)
        val nf = cset.frames[c]
        val len = cset.len[c].coerceAtLeast(0.001f)
        val d = cset.data[c] ?: return null
        val n12 = nb * 12
        if (bone.size != n12) bone = FloatArray(n12)

        val now = System.nanoTime()
        var dt = (now - slotNs[sl]) / 1_000_000_000f
        if (dt < 0f || dt > 0.25f) dt = 0.016f
        slotNs[sl] = now

        if (slotClip[sl] != c) {
            slotBlend[sl] = if (slotClip[sl] < 0) 0f else if (c == JUMP || c == RUNJUMP) 0.06f else 0.25f
            slotClip[sl] = c
            slotT0[sl] = t
        }
        val isJ = c == JUMP || c == RUNJUMP
        val once = isJ || ((c == SIT_IN || c == SIT_OUT || c == INTERACT) && simGrp.isNotEmpty())   // clipes que tocam uma vez, no tempo [t] dado
        var lt = if (once) t else (t - slotT0[sl]) * (if (c0 == WALK) WALK_RATE else 1f)
        if (once && lt > len) lt = len
        if (!once) {
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
            val dur = if (isJ) 0.06f else 0.25f
            val k = smooth01(1f - slotBlend[sl] / dur)
            for (j in 0 until n12) bone[j] = prev[j] + (bone[j] - prev[j]) * k
            slotBlend[sl] -= dt
        } else {
            slotBlend[sl] = 0f
        }
        val keep: FloatArray = if (prev != null && prev.size == n12) prev else FloatArray(n12).also { slotLast[sl] = it }
        System.arraycopy(bone, 0, keep, 0, n12)

        // Etapa 17: braços do masculino mais para dentro (depois do keep, para não acumular na mistura entre clipes)
        val armTarget = if (simOn || !mascV) 0f else if (c0 == IDLE || c0 == WALK) 1f else if (c0 == RUN) 0.5f else 0f
        slotArm[sl] += (armTarget - slotArm[sl]) * (dt * 10f).coerceAtMost(1f)
        if (slotArm[sl] > 0.01f) armIn(bone, MALE_ARM_IN * slotArm[sl], MALE_FOREARM_IN * slotArm[sl])
        // mãos fechadas só na corrida (andar e parado seguem com a mão solta)
        val fistT = if (c0 == RUN || clip == RUNJUMP) 1f else 0f
        slotFist[sl] += (fistT - slotFist[sl]) * (dt * 14f).coerceAtMost(1f)
        if (slotFist[sl] > 0.01f) fistHands(bone, slotFist[sl])

        // as mesmas matrizes de osso vestem o corpo-base e todas as peças ativas
        // Etapa 7: rosto/proporções (só recalcula quando os controles mudam)
        val sv = shapeVer
        val bp = bodyP
        val fp0 = faceP
        if (sl == 0) exprAuto = if (isJ) 4 else 0
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
        skinInto(bs, bone, !simOn)
        val bodySk = cs.skins.firstOrNull { it.key.startsWith("body/S_") }
        for (s in cs.skins) {
            if (s.warpVer != sv) refit(s, false, sv, bp, fp)
            skinInto(s, bone, s.key.startsWith("body/"))
            if (s.legCol && bodySk != null) legCollide(s, bodySk, bone)
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
        val cset = clipSet
        val d = cset.data.getOrNull(c) ?: return 0f
        val nf = cset.frames[c]
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
        if (!simOn) scan(bs)
        for (s in cs.skins) if (s.key.startsWith("feet/") || s.key.startsWith("body/S_")) scan(s)
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


    // ---- Etapa 77: mão fechada ao correr ----
    // Ossos dos dedos da mão esquerda (a direita é +15): indicador 25-27, médio 28-30, anelar 31-33, mindinho 34-36, polegar 37-39.
    // Juntas (x,y em cm, pose de repouso) medidas no malha da mão: nós, meio e ponta de cada dedo. Os dedos se espalham em Z e
    // apontam para baixo/fora; a palma olha para o corpo, então o fechar é um giro em torno do eixo Z do repouso.
    private val FIST_BONES = arrayOf(intArrayOf(25, 26, 27), intArrayOf(28, 29, 30), intArrayOf(31, 32, 33), intArrayOf(34, 35, 36), intArrayOf(37, 38, 39))
    private val FIST_J = arrayOf(
        floatArrayOf(64.7f, 100.5f, 66.7f, 98.45f, 68.6f, 96.5f),
        floatArrayOf(65.05f, 100.35f, 67.15f, 98.05f, 69.15f, 96.05f),
        floatArrayOf(64.7f, 100.15f, 66.9f, 98.05f, 68.8f, 96.3f),
        floatArrayOf(64.55f, 100.45f, 66.85f, 98.35f, 68.8f, 96.6f),
        floatArrayOf(59.35f, 103.5f, 60.25f, 101.1f, 62.65f, 99.65f))
    // Corpo do Sims 4: juntas dos dedos (Index/Mid/Ring/Pinky/Thumb 0..2) do esqueleto original do TS4 (skel_s4.txt), trazidas para a escala da malha
    // (o corpo do TS4 é reescalado para 182 cm: punho do esqueleto -> punho do bodyrig, escala 0.969). A versão da etapa 97 usava a escala do esqueleto e errava o pivô.
    private val FIST_J_TS4 = arrayOf(
        floatArrayOf(61.99f, 101.95f, 64.99f, 98.96f, 66.7f, 97.27f),
        floatArrayOf(62.46f, 101.84f, 65.52f, 98.61f, 67.45f, 96.57f),
        floatArrayOf(62.5f, 101.78f, 65.39f, 98.65f, 67.16f, 96.73f),
        floatArrayOf(62.09f, 101.92f, 64.8f, 99.15f, 66.29f, 97.63f),
        floatArrayOf(58.03f, 105.24f, 58.55f, 102.98f, 59.21f, 100.14f))
    private val FIST_ANG = arrayOf(
        floatArrayOf(72f, 95f, 55f), floatArrayOf(75f, 95f, 55f), floatArrayOf(78f, 95f, 55f), floatArrayOf(80f, 95f, 55f),
        floatArrayOf(18f, 28f, 18f))
    // Corpo Sims 4, polegar: só girar em Z (como os outros dedos) deixava o polegar esticado para fora, na frente da mão. Agora ele primeiro
    // "entra" girando em X (eixo da frente para trás da palma) em torno da base do polegar e só depois dobra as 3 juntas, assim ele cruza
    // por cima dos outros dedos fechados. THUMB_TUCK_DEG = graus da entrada; THUMB_TUCK_P = pivô (x,y,z em cm, mão esquerda; a direita espelha x).
    private val THUMB_ANG_TS4 = floatArrayOf(-18f, 5f, 25f)
    private const val THUMB_TUCK_DEG = 35f
    private val THUMB_TUCK_P = floatArrayOf(58.03f, 105.24f, 2.1f)

    /** Fecha a mão: cada junta gira em torno do seu pivô (no espaço de repouso) e a matriz do osso recebe esse giro antes da pose da animação. */
    private fun fistHands(mm: FloatArray, k: Float) {
        val rc = FloatArray(9); val tc = FloatArray(3); val rn = FloatArray(9); val tn = FloatArray(3)
        for (side in 0..1) {
            val sx = if (side == 0) 1f else -1f
            val off = if (side == 0) 0 else 15
            for (f in 0 until 5) {
                val ts4 = isTs4()
                val bones = FIST_BONES[f]; val j = if (ts4) FIST_J_TS4[f] else FIST_J[f]
                val a = if (f == 4 && ts4) THUMB_ANG_TS4 else FIST_ANG[f]
                // acumulado = identidade (polegar do Sims 4: começa com a "entrada" em X em torno da base do polegar)
                rc[0] = 1f; rc[1] = 0f; rc[2] = 0f; rc[3] = 0f; rc[4] = 1f; rc[5] = 0f; rc[6] = 0f; rc[7] = 0f; rc[8] = 1f
                tc[0] = 0f; tc[1] = 0f; tc[2] = 0f
                if (f == 4 && ts4) {
                    val th = Math.toRadians((THUMB_TUCK_DEG * k).toDouble())
                    val c0 = Math.cos(th).toFloat(); val s0 = Math.sin(th).toFloat()
                    val qx = sx * THUMB_TUCK_P[0]; val qy = THUMB_TUCK_P[1]; val qz = THUMB_TUCK_P[2]
                    // R = [[1,0,0],[0,c,-s],[0,s,c]], t = Q - R*Q
                    rc[4] = c0; rc[5] = -s0; rc[7] = s0; rc[8] = c0
                    tc[1] = qy - (c0 * qy - s0 * qz)
                    tc[2] = qz - (s0 * qy + c0 * qz)
                }
                for (jt in 0 until 3) {
                    val ang = -sx * Math.toRadians((a[jt] * k).toDouble())
                    val cs = Math.cos(ang).toFloat(); val sn = Math.sin(ang).toFloat()
                    val px = sx * j[jt * 2]; val py = j[jt * 2 + 1]
                    // C = giro em Z em torno do pivô: R = [[c,-s,0],[s,c,0],[0,0,1]], t = P - R*P
                    val tx = px - (cs * px - sn * py)
                    val ty = py - (sn * px + cs * py)
                    // novo = acumulado * C
                    for (r in 0..2) {
                        val a0 = rc[r * 3]; val a1 = rc[r * 3 + 1]; val a2 = rc[r * 3 + 2]
                        rn[r * 3] = a0 * cs + a1 * sn
                        rn[r * 3 + 1] = -a0 * sn + a1 * cs
                        rn[r * 3 + 2] = a2
                        tn[r] = a0 * tx + a1 * ty + tc[r]
                    }
                    System.arraycopy(rn, 0, rc, 0, 9); System.arraycopy(tn, 0, tc, 0, 3)
                    // aplica na matriz do osso desta junta: M = M * acumulado
                    val o = (bones[jt] + off) * 12
                    // Etapa 100 (Sims 4): o clipe de correr traz uma pose relaxada dos dedos gravada em cada osso; o punho girava POR CIMA dela e abria os dedos em leque.
                    // Agora a base de cada dedo vai para a matriz do pulso (osso da mão: 12 esquerda, 16 direita) na proporção do punho, ignorando essa pose gravada.
                    if (ts4) {
                        val w = (12 + side * 4) * 12
                        for (q in 0 until 12) mm[o + q] = mm[o + q] + (mm[w + q] - mm[o + q]) * k
                    }
                    for (r in 0..2) {
                        val m0 = mm[o + r * 4]; val m1 = mm[o + r * 4 + 1]; val m2 = mm[o + r * 4 + 2]; val mt = mm[o + r * 4 + 3]
                        mm[o + r * 4] = m0 * rc[0] + m1 * rc[3] + m2 * rc[6]
                        mm[o + r * 4 + 1] = m0 * rc[1] + m1 * rc[4] + m2 * rc[7]
                        mm[o + r * 4 + 2] = m0 * rc[2] + m1 * rc[5] + m2 * rc[8]
                        mm[o + r * 4 + 3] = m0 * tc[0] + m1 * tc[1] + m2 * tc[2] + mt
                    }
                }
            }
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

    // ---- Colisão perna x saia ----
    // A saia é uma malha rígida presa aos ossos (coxa 55%, pelve 45%); sem isso a perna atravessa o tecido ao andar, correr e sentar.
    // Cada coxa vira uma cápsula (quadril -> joelho, raio medido no corpo do Sims em repouso); vértice da saia dentro dela é empurrado para a superfície.
    private val legRadCache = HashMap<String, FloatArray>()
    private const val LEG_BINS = 6
    private const val LEG_MARGIN = 0.9f   // cm de folga entre a coxa e o tecido

    /** Raios da coxa (cm) em LEG_BINS faixas do quadril ao joelho, para cada lado (esquerdo, depois direito). */
    private fun legRadii(key: String, rg: FloatArray, body: Skin): FloatArray {
        legRadCache[key]?.let { return it }
        val res = FloatArray(2 * LEG_BINS)
        for (side in 0..1) {
            val sx = if (side == 0) 1f else -1f
            val hx = sx * rg[9]; val hy = rg[10]; val hz = rg[11]
            val kx = sx * rg[12]; val ky = rg[13]; val kz = rg[14]
            val ax = kx - hx; val ay = ky - hy; val az = kz - hz
            val l2 = ax * ax + ay * ay + az * az
            val bins = Array(LEG_BINS) { ArrayList<Float>() }
            for (v in 0 until body.nv) {
                val px = body.pos0[v * 3]; val py = body.pos0[v * 3 + 1]; val pz = body.pos0[v * 3 + 2]
                if (px * sx < 0.5f) continue
                val t = ((px - hx) * ax + (py - hy) * ay + (pz - hz) * az) / l2
                if (t < 0f || t > 1f) continue
                val qx = px - (hx + t * ax); val qy = py - (hy + t * ay); val qz = pz - (hz + t * az)
                val d = Math.sqrt((qx * qx + qy * qy + qz * qz).toDouble()).toFloat()
                if (d > 14f) continue
                bins[(t * LEG_BINS).toInt().coerceAtMost(LEG_BINS - 1)].add(d)
            }
            var last = 8f
            for (b in 0 until LEG_BINS) {
                val l = bins[b]
                if (l.size >= 4) { l.sort(); last = l[(l.size * 0.9f).toInt().coerceAtMost(l.size - 1)] }
                res[side * LEG_BINS + b] = last
            }
        }
        legRadCache[key] = res
        return res
    }

    /** Folga (em cm) de cada vértice da saia até o eixo de cada coxa NA POSE PARADA: a colisão nunca empurra além dela, então parada nada muda. */
    private fun legRef(s: Skin, rg: FloatArray, mask: BooleanArray): FloatArray? {
        val cur = s.legRef
        val cset = clipSet
        if (cur != null && s.legRefVer == s.warpVer && s.legRefSet === cset) return cur
        val d = cset.data.getOrNull(IDLE) ?: return null
        if (d.size < nb * 12) return null
        val ref = cur ?: FloatArray(2 * s.nv)
        for (side in 0..1) {
            val sx = if (side == 0) 1f else -1f
            val tb = (if (side == 0) 17 else 21) * 12
            val cb = (if (side == 0) 18 else 22) * 12
            val hx = sx * rg[9]; val hy = rg[10]; val hz = rg[11]
            val kx = sx * rg[12]; val ky = rg[13]; val kz = rg[14]
            val h0 = d[tb] * hx + d[tb + 1] * hy + d[tb + 2] * hz + d[tb + 3]
            val h1 = d[tb + 4] * hx + d[tb + 5] * hy + d[tb + 6] * hz + d[tb + 7]
            val h2 = d[tb + 8] * hx + d[tb + 9] * hy + d[tb + 10] * hz + d[tb + 11]
            val k0 = d[cb] * kx + d[cb + 1] * ky + d[cb + 2] * kz + d[cb + 3]
            val k1 = d[cb + 4] * kx + d[cb + 5] * ky + d[cb + 6] * kz + d[cb + 7]
            val k2 = d[cb + 8] * kx + d[cb + 9] * ky + d[cb + 10] * kz + d[cb + 11]
            val c0 = d[tb]; val c1 = d[tb + 4]; val c2 = d[tb + 8]
            val sc = Math.sqrt((c0 * c0 + c1 * c1 + c2 * c2).toDouble()).toFloat()
            val ax = k0 - h0; val ay = k1 - h1; val az = k2 - h2
            val l2 = ax * ax + ay * ay + az * az
            for (v in 0 until s.nv) {
                if (!mask[v] || sc < 1e-6f || l2 < 1e-12f) { ref[side * s.nv + v] = 0f; continue }
                val px = s.pos[v * 3]; val py = s.pos[v * 3 + 1]; val pz = s.pos[v * 3 + 2]
                var x = 0f; var y = 0f; var z = 0f
                for (k in 0 until 4) {
                    val w = s.bw[v * 4 + k]
                    if (w <= 0f) continue
                    val bo = s.bi[v * 4 + k] * 12
                    x += w * (d[bo] * px + d[bo + 1] * py + d[bo + 2] * pz + d[bo + 3])
                    y += w * (d[bo + 4] * px + d[bo + 5] * py + d[bo + 6] * pz + d[bo + 7])
                    z += w * (d[bo + 8] * px + d[bo + 9] * py + d[bo + 10] * pz + d[bo + 11])
                }
                val t = (((x - h0) * ax + (y - h1) * ay + (z - h2) * az) / l2).coerceIn(0f, 1f)
                val qx = x - (h0 + t * ax); val qy = y - (h1 + t * ay); val qz = z - (h2 + t * az)
                ref[side * s.nv + v] = Math.sqrt((qx * qx + qy * qy + qz * qz).toDouble()).toFloat() / sc
            }
        }
        s.legRef = ref; s.legRefVer = s.warpVer; s.legRefSet = cset
        return ref
    }

    private fun legCollide(s: Skin, body: Skin, mm: FloatArray) {
        val rg = rigs[simKey] ?: return
        if (rg.size < 18) return
        val rad = legRadii(simKey, rg, body)
        var mask = s.legMask
        if (mask == null) {
            val lim = rg[10] + 3f   // quadril + 3 cm: cintura e cinto não são mexidos
            mask = BooleanArray(s.nv) { s.pos0[it * 3 + 1] < lim }
            s.legMask = mask
            var n = 0
            for (v in 0 until s.nv) if (mask[v]) n++
            val li = IntArray(n); var q = 0
            for (v in 0 until s.nv) if (mask[v]) li[q++] = v
            s.legIdx = li
        }
        val idxs = s.legIdx ?: return
        val ref = legRef(s, rg, mask) ?: return
        val hs = heightS
        val out = s.out
        val nv = s.nv
        for (side in 0..1) {
            val sx = if (side == 0) 1f else -1f
            val tb = (if (side == 0) 17 else 21) * 12
            val cb = (if (side == 0) 18 else 22) * 12
            val hx = sx * rg[9]; val hy = rg[10]; val hz = rg[11]
            val kx = sx * rg[12]; val ky = rg[13]; val kz = rg[14]
            // quadril pelo osso da coxa, joelho pelo osso da perna (acompanha o joelho dobrando)
            val h0 = (mm[tb] * hx + mm[tb + 1] * hy + mm[tb + 2] * hz + mm[tb + 3]) * hs
            val h1 = (mm[tb + 4] * hx + mm[tb + 5] * hy + mm[tb + 6] * hz + mm[tb + 7]) * hs
            val h2 = (mm[tb + 8] * hx + mm[tb + 9] * hy + mm[tb + 10] * hz + mm[tb + 11]) * hs
            val k0 = (mm[cb] * kx + mm[cb + 1] * ky + mm[cb + 2] * kz + mm[cb + 3]) * hs
            val k1 = (mm[cb + 4] * kx + mm[cb + 5] * ky + mm[cb + 6] * kz + mm[cb + 7]) * hs
            val k2 = (mm[cb + 8] * kx + mm[cb + 9] * ky + mm[cb + 10] * kz + mm[cb + 11]) * hs
            // escala cm -> unidade de saída (o osso carrega a escala)
            val c0 = mm[tb]; val c1 = mm[tb + 4]; val c2 = mm[tb + 8]
            val sc = Math.sqrt((c0 * c0 + c1 * c1 + c2 * c2).toDouble()).toFloat() * hs
            if (sc < 1e-6f) continue
            val ax = k0 - h0; val ay = k1 - h1; val az = k2 - h2
            val l2 = ax * ax + ay * ay + az * az
            if (l2 < 1e-12f) continue
            val rmax = (rad[side * LEG_BINS] + LEG_MARGIN) * sc   // raio máximo possível desta perna (cota rápida)
            for (i in idxs.indices) {
                val v = idxs[i]
                val cap = ref[side * nv + v]
                if (cap <= 0f) continue
                val o = v * STRIDE
                val px = out[o]; val py = out[o + 1]; val pz = out[o + 2]
                val ox = px - h0; val oy = py - h1; val oz = pz - h2
                if (ox > 4f * rmax || ox < -4f * rmax) continue   // longe demais da coxa: nada a fazer
                val t = ((ox * ax + oy * ay + oz * az) / l2).coerceIn(0f, 1f)
                val qx = ox - t * ax; val qy = oy - t * ay; val qz = oz - t * az
                val d2 = qx * qx + qy * qy + qz * qz
                val bf = t * (LEG_BINS - 1)
                val b0 = bf.toInt().coerceAtMost(LEG_BINS - 1); val b1 = (b0 + 1).coerceAtMost(LEG_BINS - 1)
                val rcm = rad[side * LEG_BINS + b0] * (1f - (bf - b0)) + rad[side * LEG_BINS + b1] * (bf - b0) + LEG_MARGIN
                val r = rcm * sc   // Etapa 101: sem teto pela folga parada (o teto da etapa 98 deixava a coxa atravessar a saia)
                if (d2 >= r * r) continue
                val d = Math.sqrt(d2.toDouble()).toFloat()
                if (d < 1e-6f) continue
                val k = r / d
                out[o] = h0 + t * ax + qx * k; out[o + 1] = h1 + t * ay + qy * k; out[o + 2] = h2 + t * az + qz * k
            }
        }
        val buf = s.fb
        buf.position(0)
        buf.put(out, 0, s.nv * STRIDE)
        buf.position(0)
    }

    private fun skinInto(s: Skin, mm: FloatArray, base: Boolean = false) {
        val pos = s.pos
        val nor = s.nor
        val bi = s.bi
        val bw = s.bw
        val out = s.out
        val hs = heightS
        val fp = fpOn
        val slotName = s.key.substringBefore('/')
        val headSlot = fp && !base && slotName in HEAD_SLOTS
        var topMax = 0f
        for (v in 0 until s.nv) {
            val px = pos[v * 3]; val py = pos[v * 3 + 1]; val pz = pos[v * 3 + 2]
            val nx = nor[v * 3]; val ny = nor[v * 3 + 1]; val nz = nor[v * 3 + 2]
            var x = 0f; var y = 0f; var z = 0f
            var snx = 0f; var sny = 0f; var snz = 0f
            for (k in 0 until 4) {
                val w = bw[v * 4 + k]
                if (w <= 0f) continue
                val bo = bi[v * 4 + k] * 12
                x += w * (mm[bo] * px + mm[bo + 1] * py + mm[bo + 2] * pz + mm[bo + 3])
                y += w * (mm[bo + 4] * px + mm[bo + 5] * py + mm[bo + 6] * pz + mm[bo + 7])
                z += w * (mm[bo + 8] * px + mm[bo + 9] * py + mm[bo + 10] * pz + mm[bo + 11])
                snx += w * (mm[bo] * nx + mm[bo + 1] * ny + mm[bo + 2] * nz)
                sny += w * (mm[bo + 4] * nx + mm[bo + 5] * ny + mm[bo + 6] * nz)
                snz += w * (mm[bo + 8] * nx + mm[bo + 9] * ny + mm[bo + 10] * nz)
            }
            val o = v * STRIDE
            if (base && y * hs > topMax) topMax = y * hs
            out[o] = x * hs; out[o + 1] = y * hs; out[o + 2] = z * hs
            val nl = Math.sqrt((snx * snx + sny * sny + snz * snz).toDouble()).toFloat()
            val inv = if (nl > 1e-9f) 1f / nl else 0f
            out[o + 3] = snx * inv; out[o + 4] = if (nl > 1e-9f) sny * inv else 1f; out[o + 5] = snz * inv
        }
        if (base && topMax > 0.8f) topObs = topMax

        if (fp) {
            // altura de repouso do corpo (cm) e o corte do queixo, medidos na pose de repouso (não mudam com a animação)
            val p0 = s.pos0
            if (base) {
                var rt = 0f
                for (v in 0 until s.nv) { val yy = p0[v * 3 + 1]; if (yy > rt) rt = yy }
                if (rt > 0.5f) fpRestTop = rt
            }
            val rtop = if (fpRestTop > 0.5f) fpRestTop else 0f
            if (rtop > 0f) {
                val cut = rtop * 0.862f
                val band = rtop * 0.035f
                // anel do pescoço (logo abaixo do queixo) na pose atual: o centro dele fecha o pescoço e ancora o olho
                if (base) {
                    var sx = 0f; var sy = 0f; var sz = 0f; var cn = 0
                    for (v in 0 until s.nv) {
                        val yy = p0[v * 3 + 1]
                        if (yy <= cut && yy >= cut - band) { val o = v * STRIDE; sx += out[o]; sy += out[o + 1]; sz += out[o + 2]; cn++ }
                    }
                    if (cn > 0) {
                        fpRing[0] = sx / cn; fpRing[1] = sy / cn; fpRing[2] = sz / cn; fpRingOk = true
                        // rtop está em cm (pose de repouso); a malha de saída está em metros. A altura em metros vem da escala do osso raiz.
                        var us = mm[0] * hs
                        if (us < 0.004f || us > 0.02f) us = 0.0082f * hs
                        val tm = rtop * us
                        val tx = fpRing[0]; val ty = fpRing[1] + 0.068f * tm; val tz = fpRing[2] + 0.060f * tm
                        if (!fpEyeInit) { fpEye[0] = tx; fpEye[1] = ty; fpEye[2] = tz; fpEyeInit = true }
                        else { fpEye[0] += (tx - fpEye[0]) * 0.5f; fpEye[1] += (ty - fpEye[1]) * 0.5f; fpEye[2] += (tz - fpEye[2]) * 0.5f }
                    }
                }
                val ex = fpEye[0]; val ey = fpEye[1]; val ez = fpEye[2] + fpAdjF
                val rr2 = 0.12f * 0.12f
                val rx = fpRing[0]; val ry = fpRing[1]; val rz = fpRing[2]
                for (v in 0 until s.nv) {
                    val o = v * STRIDE
                    if (headSlot) { out[o] = 0f; out[o + 1] = 0f; out[o + 2] = 0f; continue }
                    if (fpRingOk && p0[v * 3 + 1] > cut) { out[o] = rx; out[o + 1] = ry; out[o + 2] = rz; continue }
                    // braços/mãos/roupa que passam colados na lente: vão para o olho (triângulo visto "de lado" = invisível)
                    val dx = out[o] - ex; val dy = out[o + 1] - ey; val dz = out[o + 2] - ez
                    if (dx * dx + dy * dy + dz * dz < rr2) { out[o] = ex; out[o + 1] = ey; out[o + 2] = ez }
                }
            }
        } else if (base) {
            fpEyeInit = false; fpRingOk = false
        }

        val buf = s.fb
        buf.position(0)
        buf.put(out, 0, s.nv * STRIDE)
        buf.position(0)
    }
}
