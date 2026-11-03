package com.vinicius.meular

import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.sqrt

/**
 * Etapa 7 — proporções do corpo e formato do rosto.
 *
 * As proporções são uma deformação suave aplicada às posições de REPOUSO (antes da pele) de TODAS as malhas
 * (corpo-base e peças), com a mesma função para todas: assim roupas, cabelo e sapatos acompanham o corpo e os clips
 * Idle/Walk/Jump (matrizes de osso) continuam exatamente como estão. A altura é só uma escala final em torno dos pés.
 * Valores dos controles: inteiros de -100 a 100 (0 = como o personagem original).
 */
object BodyMorph {
    /** Etapa 50: 27 controles de corpo (os 10 primeiros são os antigos, na mesma ordem; o save guarda os 10 antigos no lugar de sempre e os 17 novos no fim). */
    val BODY_NAMES = listOf(
        "Altura", "Peso", "Ombros (largura)", "Peito", "Busto (tamanho)", "Cintura", "Quadril", "Coxas", "Braços (espessura)", "Cabeça",
        "Busto (altura)", "Busto (distância)", "Bumbum", "Barriga", "Postura", "Pescoço (espessura)", "Pescoço (comprimento)",
        "Ombros (altura)", "Antebraços", "Braços (comprimento)", "Mãos", "Panturrilhas", "Pernas (comprimento)", "Vão das coxas",
        "Tornozelos", "Pés", "Torso (comprimento)"
    )
    /** Grupos da tela do criador (índices de BODY_NAMES). */
    val BODY_GROUPS: List<Pair<String, IntArray>> = listOf(
        "Geral" to intArrayOf(0, 1, 9),
        "Tronco" to intArrayOf(2, 17, 3, 5, 13, 14, 26),
        "Busto" to intArrayOf(4, 10, 11),
        "Quadril e pernas" to intArrayOf(6, 12, 7, 23, 21, 24, 22),
        "Braços e mãos" to intArrayOf(8, 18, 19, 20),
        "Pescoço e pés" to intArrayOf(15, 16, 25)
    )
    val FACE_NAMES = listOf(
        "Masculinidade", "Cílios", "Sobrancelha grossa", "Ponte do nariz", "Nariz largo", "Nariz para baixo", "Nariz para cima",
        "Boca larga", "Boca fina", "Cantos dos olhos para baixo", "Cantos dos olhos para cima", "Olhos quadrados", "Orelha élfica"
    )
    const val NB = 27
    /** Quantidade de controles de corpo que o save guarda no lugar original (formato antigo). */
    const val NB_OLD = 10
    const val RIG_N = 23
    const val NF = 13

    /** Ganho de cada canal do rosto (100% do controle = ganho x o deslocamento do pack). Mesma ordem de FACE_NAMES / morph.bin. */
    val FACE_GAIN = floatArrayOf(1f, 2f, 2f, 2f, 2f, 2f, 2f, 2f, 2f, 2f, 2f, 2f, 0.8f)

    /** Altura: -100..100 vira -6%..+6%. */
    fun heightScale(b: Float): Float = 1f + 0.06f * b

    private fun sm(e0: Float, e1: Float, x: Float): Float {
        val t = ((x - e0) / (e1 - e0)).coerceIn(0f, 1f)
        return t * t * (3f - 2f * t)
    }

    private fun gs(x: Float, c: Float, s: Float): Float {
        val u = (x - c) / s
        return exp(-u * u)
    }

    // ---- Etapa 13: corpo masculino x feminino e busto maior ----
    // Busto: duas cúpulas suaves empurradas para frente (altura em função da distância ao mamilo). Feminino já nasce com um busto
    // visível (BUST_BASE_F); o controle "Busto" vai de -3 cm (-100) a +8 cm (+100) sobre isso. Masculino: peito reto.
    private const val BUST_CX = 9.0f
    private const val BUST_CY = 127.0f
    private const val BUST_R = 11.0f
    private const val BUST_UP = 0.85f      // acima do mamilo a curva é mais larga (inclinação suave)
    private const val BUST_DN = 1.1f       // abaixo é mais cheia e mais firme
    private const val BUST_P = 0.8f
    private const val BUST_SPREAD = 0.9f
    private const val BUST_DROP = 0.10f
    private const val BUST_POS = 8.0f
    private const val BUST_NEG = 3.0f
    private const val LOOSE_R = 1.8f   // roupa larga: raio da cúpula do busto x1,8
    private const val LOOSE_A = 0.5f   // roupa larga: altura da cúpula x0,5
    private const val BUST_BASE_F = 2.0f
    private const val BUST_BASE_M = -1.0f
    // Masculino = mesmos controles somados a estes valores (ombros largos, peito/cintura mais cheios, quadril estreito, braços e pescoço grossos)
    private const val M_OMBRO = 0.6f
    private const val M_PEITO = 0.15f
    private const val M_CINT = 0.0f
    private const val M_QUAD = 0.0f
    private const val M_BRACO = 0.15f
    private const val M_PESCOCO = 0.12f
    // Etapa 16: valores do personagem masculino do pack BoZo (John): corpo neutro com clavícula x1,10 e shoulder_twist x1,12 (ombros mais largos);
    // o resto dos ossos em 1,0; rosto BodyType 100. Antes (etapa 14) eram bem mais fortes e deixavam o corpo torto.
    // Etapa 14: mais peso lateral, peito/cintura quase só para os lados, peitoral, deltoide, trapézio, coxa mais fina, glúteo reto
    private const val M_PESO = 0.0f
    private const val M_ZFAC = 0.25f
    private const val M_PEC = 0.0f
    private const val M_PEC_Y = 121.0f
    private const val M_PEC_R = 14.0f
    private const val M_DELT = 0.7f
    private const val M_COXA = 0.0f
    private const val M_BUTT = 0.0f
    private const val M_TRAP = 0.0f
    /** Altura extra do corpo masculino (multiplica a altura do criador). */
    const val M_ALTURA = 1.0f
    /** Rosto: Masculinidade padrão do corpo masculino (somada ao controle, em fração de 1). */
    const val M_ROSTO = 1.0f

    /**
     * Copia [src] (xyz por vértice, unidades do FBX: personagem com ~162 de altura, frente +Z, lado +X) para [dst] já deformado.
     * [b] = 10 valores de -1 a 1 (ordem de BODY_NAMES; o índice 0, altura, é ignorado aqui).
     */
    fun warp(src: FloatArray, dst: FloatArray, nv: Int, b: FloatArray, masc: Boolean = false, loose: Boolean = false) {
        val m = if (masc) 1f else 0f
        val peso = 0.14f * (b[1] + M_PESO * m)
        val ombro = 3.0f * (b[2] + M_OMBRO * m)
        val peito = 0.10f * (b[3] + M_PEITO * m)
        val busto = (if (b[4] > 0f) BUST_POS * b[4] else BUST_NEG * b[4]) + (if (masc) BUST_BASE_M else BUST_BASE_F)
        val cint = 0.15f * (b[5] + M_CINT * m)
        val quad = 0.12f * (b[6] + M_QUAD * m)
        val coxa = 0.25f * (b[7] + M_COXA * m)
        val braco = 0.25f * (b[8] + M_BRACO * m)
        val cab = 0.12f * b[9]
        // eixo do braço (pose de repouso em A): do ombro (13,3; 142,5; -2,9) na direção do cotovelo
        val zf = 1f - m * (1f - M_ZFAC)
        val dnx = 0.6012f
        val dny = -0.7991f
        val dnz = -0.0076f
        for (v in 0 until nv) {
            val x = src[v * 3]
            val y = src[v * 3 + 1]
            val z = src[v * 3 + 2]
            val ax = abs(x)
            val sx = if (x < 0f) -1f else 1f
            var dx = 0f
            var dy = 0f
            var dz = 0f
            val low = 1f - sm(146f, 156f, y)   // tudo menos a cabeça
            if (peso != 0f) {
                val xc = if (ax > 24f) 24f else ax   // além de 24 o braço só se desloca (não estica)
                dx += sx * xc * peso * low
                dz += (z - 3f) * peso * low
            }
            if (ombro != 0f) {
                val w = sm(22f, 34f, ax) * sm(62f, 78f, y) * low
                dx += sx * ombro * w
            }
            if (peito != 0f) {
                val w = sm(100f, 114f, y) * (1f - sm(128f, 140f, y)) * (1f - sm(18f, 28f, ax))
                dx += x * peito * w
                dz += z * peito * w * zf
            }
            if (busto != 0f) {
                // Etapa 31: roupa larga (camiseta skatista) não vira "bola" no busto: cúpula mais larga e bem mais suave, sem espalhar o tecido
                val bR = if (loose) BUST_R * LOOSE_R else BUST_R
                val bA = if (loose) busto * LOOSE_A else busto
                val bSp = if (loose) 0f else BUST_SPREAD
                val bDr = if (loose) 0f else BUST_DROP
                val bdx = x - sx * BUST_CX
                val bdy0 = y - BUST_CY
                val bdy = if (bdy0 > 0f) bdy0 * BUST_UP else bdy0 * BUST_DN
                val rho = sqrt(bdx * bdx + bdy * bdy)
                if (rho < bR) {
                    val t = 1f - rho / bR
                    val h = Math.pow((t * t * (3f - 2f * t)).toDouble(), BUST_P.toDouble()).toFloat() * sm(-3f, 3f, z)
                    dz += bA * h
                    dx += bdx / bR * bSp * bA * h
                    dy += bdy / bR * bSp * bA * h - bDr * bA * h
                }
            }
            if (cint != 0f) {
                val w = sm(92f, 100f, y) * (1f - sm(110f, 118f, y)) * (1f - sm(20f, 30f, ax))
                dx += x * cint * w
                dz += z * cint * w * zf
            }
            if (quad != 0f) {
                val w = sm(66f, 78f, y) * (1f - sm(94f, 104f, y)) * (1f - sm(26f, 36f, ax))
                dx += x * quad * w
                dz += (z - 3f) * quad * 0.5f * w
            }
            if (coxa != 0f) {
                val rx = x - sx * 9.3f
                val rz = z - 3.8f
                val r = sqrt(rx * rx + rz * rz)
                val w = sm(44f, 58f, y) * (1f - sm(86f, 98f, y)) * (1f - sm(11f, 19f, r)) * sm(0f, 5f, ax)
                dx += rx * coxa * w
                dz += rz * coxa * w
            }
            if (braco != 0f) {
                val vx = x - sx * 13.3f
                val vy = y - 142.5f
                val vz = z + 2.9f
                val ux = dnx * sx
                val t = vx * ux + vy * dny + vz * dnz
                val px = vx - t * ux
                val py = vy - t * dny
                val pz = vz - t * dnz
                val r = sqrt(px * px + py * py + pz * pz)
                val w = sm(6f, 16f, t) * (1f - sm(44f, 52f, t)) * (1f - sm(9f, 15f, r))
                dx += px * braco * w
                dy += py * braco * w
                dz += pz * braco * w
            }
            if (cab != 0f) {
                val w = sm(146f, 156f, y)
                dx += x * cab * w
                dy += (y - 148f) * cab * w
                dz += z * cab * w
            }
            if (masc) {   // pescoço mais grosso
                val w = gs(y, 149f, 5f)
                dx += x * M_PESCOCO * w
                dz += (z + 0.3f) * M_PESCOCO * w
                // peitoral: placa larga e baixa, para frente
                val pdx = x - sx * 8.5f
                val pdy = y - M_PEC_Y
                val tp = (1f - sqrt(pdx * pdx + pdy * pdy) / M_PEC_R).coerceIn(0f, 1f)
                dz += M_PEC * (tp * tp * (3f - 2f * tp)) * sm(-3f, 3f, z)
                // deltoide
                val ddx = x - sx * 19f
                val ddy = y - 137f
                val td = (1f - sqrt(ddx * ddx + ddy * ddy) / 15f).coerceIn(0f, 1f)
                dx += sx * M_DELT * (td * td * (3f - 2f * td))
                // trapézio
                dy += M_TRAP * gs(ax, 11f, 7f) * gs(y, 146f, 4.5f)
                // glúteo mais reto
                if (z < 3.8f) dz += M_BUTT * (z - 3.8f) * sm(66f, 78f, y) * (1f - sm(94f, 104f, y))
            }
            dst[v * 3] = x + dx
            dst[v * 3 + 1] = y + dy
            dst[v * 3 + 2] = z + dz
        }
    }

    // ---- Etapa 50: sliders de corpo do esqueleto do Sims 3 ----
    // r = 23 valores de bodyrig.txt (ver ferramentas/etapa50_rig_sliders.py). Portado linha a linha de ferramentas/etapa50_sliders_ref.py.
    private fun segCalc(px: Float, py: Float, pz: Float, ax: Float, ay: Float, az: Float, bx: Float, by: Float, bz: Float, o: FloatArray) {
        val abx = bx - ax; val aby = by - ay; val abz = bz - az
        val l2 = abx * abx + aby * aby + abz * abz
        val t = ((px - ax) * abx + (py - ay) * aby + (pz - az) * abz) / l2
        val tc = t.coerceIn(0f, 1f)
        val qx = px - (ax + tc * abx); val qy = py - (ay + tc * aby); val qz = pz - (az + tc * abz)
        o[0] = t; o[1] = tc; o[2] = sqrt(qx * qx + qy * qy + qz * qz); o[3] = qx; o[4] = qy; o[5] = qz
    }

    fun warpSim(src: FloatArray, dst: FloatArray, nv: Int, b: FloatArray, r: FloatArray) {
        val sX = r[0]; val sY = r[1]; val sZ = r[2]
        val eX = r[3]; val eY = r[4]; val eZ = r[5]
        val wX = r[6]; val wY = r[7]; val wZ = r[8]
        val hX = r[9]; val hY = r[10]; val hZ = r[11]
        val kX = r[12]; val kY = r[13]; val kZ = r[14]
        val aX = r[15]; val aY = r[16]; val aZ = r[17]
        val topY = r[18]; val neckY = r[19]; val zc = r[21]
        val hipY = hY; val kneeY = kY; val ankY = aY
        val tt = topY - hipY
        val waistY = hipY + 0.58f * tt
        val chestY = hipY + 0.78f * tt
        val bustY = hipY + 0.80f * tt
        val bustX = 0.52f * sX
        val crotchY = hipY - 0.26f * (hipY - kneeY)
        val fLeg = 1f + 0.07f * b[22]; val fTor = 1f + 0.08f * b[26]; val fNeck = 1f + 0.35f * b[16]
        fun extra(yy: Float): Float =
            (fLeg - 1f) * (yy.coerceIn(ankY, hipY) - ankY) +
            (fTor - 1f) * (yy.coerceIn(hipY, topY) - hipY) +
            (fNeck - 1f) * (yy.coerceIn(topY + 3f, neckY + 2f) - (topY + 3f))
        val exS = extra(sY)
        val oS = FloatArray(6); val oU = FloatArray(6); val oF = FloatArray(6); val oL = FloatArray(6); val oC = FloatArray(6)
        val ulx = wX - sX; val uly = wY - sY; val ulz = wZ - sZ
        val uln = sqrt(ulx * ulx + uly * uly + ulz * ulz)
        for (v in 0 until nv) {
            val x = src[v * 3]; val y = src[v * 3 + 1]; val z = src[v * 3 + 2]
            val ax = abs(x)
            val sx = if (x < 0f) -1f else 1f
            var dx = 0f; var dy = 0f; var dz = 0f
            val zr = z - zc
            val low = 1f - sm(neckY - 8f, neckY + 2f, y)
            segCalc(ax, y, z, sX, sY, sZ, wX, wY, wZ, oS)
            val tS = oS[0]; val dS = oS[2]
            val armAll = sm(-0.18f, 0.04f, tS) * (1f - sm(13f, 19f, dS))
            segCalc(ax, y, z, sX, sY, sZ, eX, eY, eZ, oU)
            segCalc(ax, y, z, eX, eY, eZ, wX, wY, wZ, oF)
            val useF = oF[2] < oU[2]
            val armD = if (useF) oF[2] else oU[2]
            val armT = if (useF) 0.5f + 0.5f * oF[1] else 0.5f * oU[1]
            val armX = if (useF) oF[3] else oU[3]
            val armY = if (useF) oF[4] else oU[4]
            val armZ = if (useF) oF[5] else oU[5]
            val armIn = 1f - sm(9f, 14f, armD)
            val notArm = 1f - armAll
            // Peso
            if (b[1] != 0f) {
                val xc = if (ax < sX + 6f) ax else sX + 6f
                dx += sx * xc * 0.14f * b[1] * low
                dz += zr * 0.14f * b[1] * low * (1f - armAll * 0.5f)
            }
            // Ombros: largura e altura
            val capW = sm(4f, sX, ax) * sm(topY - 12f, topY, y) * (1f - sm(neckY - 2f, neckY + 6f, y))
            val shW = if (armAll > capW) armAll else capW
            if (b[2] != 0f) dx += sx * 3f * b[2] * shW
            if (b[17] != 0f) dy += 2.5f * b[17] * shW
            // Peito
            if (b[3] != 0f) {
                val w = sm(waistY + 4f, chestY - 2f, y) * (1f - sm(topY - 2f, topY + 6f, y)) * (1f - sm(sX - 4f, sX + 2f, ax)) * notArm
                dx += x * 0.10f * b[3] * w
                dz += zr * 0.10f * b[3] * w * 0.6f
            }
            // Busto: tamanho, altura, distância
            if (b[4] != 0f || b[10] != 0f || b[11] != 0f) {
                val bdx = ax - bustX
                val bdy0 = y - bustY
                val bdy = if (bdy0 > 0f) bdy0 * 0.85f else bdy0 * 1.1f
                val rr = 0.24f * tt
                val rho = sqrt(bdx * bdx + bdy * bdy)
                val t = (1f - rho / rr).coerceIn(0f, 1f)
                val hw = Math.pow((t * t * (3f - 2f * t)).toDouble(), 0.8).toFloat() * sm(-3f, 3f, zr) * notArm
                val amp = if (b[4] > 0f) 5.5f * b[4] else 2.5f * b[4]
                dz += amp * hw
                dx += sx * 0.5f * amp * hw * (bdx / rr)
                dy += (bdy / rr) * 0.9f * amp * hw * 0.4f - 0.1f * amp * hw
                dy += 3.2f * b[10] * hw
                dx += sx * 3f * b[11] * hw * sm(0f, 5f, ax)
            }
            // Cintura
            if (b[5] != 0f) {
                val w = sm(waistY - 9f, waistY - 2f, y) * (1f - sm(waistY + 2f, waistY + 9f, y)) * (1f - sm(13f, 19f, ax)) * notArm
                dx += x * 0.15f * b[5] * w
                dz += zr * 0.15f * b[5] * w * 0.6f
            }
            // Quadril
            if (b[6] != 0f) {
                val w = sm(crotchY - 8f, crotchY + 4f, y) * (1f - sm(waistY - 8f, waistY, y)) * (1f - sm(21f, 29f, ax)) * notArm
                dx += x * 0.12f * b[6] * w
                dz += zr * 0.06f * b[6] * w
            }
            // Barriga
            if (b[13] != 0f) {
                val ex = ax / 13f; val ey = (y - (waistY - 6f)) / 11f
                val t = (1f - sqrt(ex * ex + ey * ey)).coerceIn(0f, 1f)
                dz += 4.5f * b[13] * (t * t * (3f - 2f * t)) * sm(-2f, 4f, zr) * notArm
            }
            // Bumbum
            if (b[12] != 0f) {
                val cx = ax - 0.5f * hX * 0.9f
                val cy = y - (hipY + 3f)
                val t = (1f - sqrt(cx * cx + cy * cy) / 14f).coerceIn(0f, 1f)
                val hb = (t * t * (3f - 2f * t)) * sm(0f, 6f, -zr) * notArm
                dz -= 4f * b[12] * hb
                dx += sx * 0.8f * b[12] * hb * sm(0f, 5f, ax)
                dy += 0.6f * b[12] * hb
            }
            // Coxas e vão das coxas
            segCalc(ax, y, z, hX, hY, hZ, kX, kY, kZ, oL)
            val tL = oL[0]
            val thighW = (1f - sm(11f, 17f, oL[2])) * sm(0.04f, 0.2f, tL) * (1f - sm(0.82f, 1f, tL)) * sm(0f, 5f, ax)
            if (b[7] != 0f) {
                dx += sx * oL[3] * 0.25f * b[7] * thighW
                dz += oL[5] * 0.25f * b[7] * thighW
            }
            if (b[23] != 0f) dx += sx * 1.2f * b[23] * thighW
            // Panturrilhas e tornozelos
            segCalc(ax, y, z, kX, kY, kZ, aX, aY, aZ, oC)
            val tC = oC[0]; val dC = oC[2]
            if (b[21] != 0f) {
                val w = (1f - sm(10f, 15f, dC)) * sm(0.05f, 0.25f, tC) * (1f - sm(0.55f, 0.85f, tC)) * sm(0f, 4f, ax)
                dx += sx * oC[3] * 0.22f * b[21] * w
                dz += oC[5] * 0.22f * b[21] * w
            }
            if (b[24] != 0f) {
                val w = (1f - sm(8f, 12f, dC)) * gs(y, ankY + 5f, 4.5f) * sm(0f, 4f, ax)
                dx += sx * oC[3] * 0.30f * b[24] * w
                dz += oC[5] * 0.30f * b[24] * w
            }
            // Pés
            if (b[25] != 0f) {
                val w = 1f - sm(ankY + 1f, ankY + 8f, y)
                dx += (ax - aX) * sx * 0.25f * b[25] * w * 0.7f
                dz += (z - aZ) * 0.25f * b[25] * w
            }
            // Braços: espessura, antebraços, comprimento, mãos
            if (b[8] != 0f) {
                val w = sm(0.06f, 0.28f, armT) * (1f - sm(0.86f, 1f, armT)) * armIn
                dx += sx * armX * 0.25f * b[8] * w
                dy += armY * 0.25f * b[8] * w
                dz += armZ * 0.25f * b[8] * w
            }
            if (b[18] != 0f) {
                val w = sm(0.42f, 0.58f, armT) * (1f - sm(0.88f, 1f, armT)) * armIn
                dx += sx * armX * 0.28f * b[18] * w
                dy += armY * 0.28f * b[18] * w
                dz += armZ * 0.28f * b[18] * w
            }
            if (b[19] != 0f) {
                val k = 0.12f * b[19] * uln * sm(0.05f, 0.9f, tS) * (1f - sm(13f, 19f, dS))
                dx += sx * ulx / uln * k
                dy += uly / uln * k
                dz += ulz / uln * k
            }
            if (b[20] != 0f) {
                val w = sm(0.92f, 1.06f, tS) * (1f - sm(13f, 19f, dS))
                dx += sx * (ax - wX) * 0.35f * b[20] * w
                dy += (y - wY) * 0.35f * b[20] * w
                dz += (z - wZ) * 0.35f * b[20] * w
            }
            // Pescoço e cabeça
            if (b[15] != 0f) {
                val w = gs(y, 0.5f * (topY + neckY) + 2f, 6f) * (1f - sm(7f, 12f, ax))
                dx += x * 0.25f * b[15] * w
                dz += zr * 0.25f * b[15] * w
            }
            if (b[9] != 0f) {
                val w = sm(neckY - 2f, neckY + 8f, y)
                val c = 0.12f * b[9]
                dx += x * c * w
                dy += (y - neckY) * c * w
                dz += zr * c * w
            }
            // Postura
            if (b[14] != 0f) {
                val th = -0.10f * b[14] * sm(waistY, chestY, y)
                val yr = y - waistY
                val sn = kotlin.math.sin(th); val cs = kotlin.math.cos(th)
                dz += -yr * sn + zr * (cs - 1f)
                dy += zr * sn + yr * (cs - 1f)
            }
            // Comprimentos (pernas, torso, pescoço); o braço acompanha o ombro
            var exY = extra(y)
            exY += (exS - exY) * armAll
            dy += exY
            dst[v * 3] = x + dx
            dst[v * 3 + 1] = y + dy
            dst[v * 3 + 2] = z + dz
        }
    }

    /**
     * Normais depois da deformação: soma à normal original a DIFERENÇA entre as normais suaves calculadas na malha deformada ([p1]) e na
     * original ([p0]). As emendas de UV (vértices duplicados) aparecem nas duas e se cancelam; só o que a deformação mudou entra.
     * [out] recebe o resultado; [n0] são as normais originais.
     */
    fun fixNormals(p0: FloatArray, p1: FloatArray, n0: FloatArray, out: FloatArray, idx: ShortArray, ni: Int, nv: Int) {
        val a = FloatArray(nv * 3)
        val c = FloatArray(nv * 3)
        var t = 0
        while (t + 2 < ni) {
            val i0 = (idx[t].toInt() and 0xFFFF) * 3
            val i1 = (idx[t + 1].toInt() and 0xFFFF) * 3
            val i2 = (idx[t + 2].toInt() and 0xFFFF) * 3
            accTri(p0, i0, i1, i2, a)
            accTri(p1, i0, i1, i2, c)
            t += 3
        }
        for (v in 0 until nv) {
            val o = v * 3
            val la = sqrt(a[o] * a[o] + a[o + 1] * a[o + 1] + a[o + 2] * a[o + 2])
            val lc = sqrt(c[o] * c[o] + c[o + 1] * c[o + 1] + c[o + 2] * c[o + 2])
            var nx = n0[o]
            var ny = n0[o + 1]
            var nz = n0[o + 2]
            if (la > 1e-9f && lc > 1e-9f) {
                nx += c[o] / lc - a[o] / la
                ny += c[o + 1] / lc - a[o + 1] / la
                nz += c[o + 2] / lc - a[o + 2] / la
            }
            val l = sqrt(nx * nx + ny * ny + nz * nz)
            if (l > 1e-6f) {
                out[o] = nx / l; out[o + 1] = ny / l; out[o + 2] = nz / l
            } else {
                out[o] = n0[o]; out[o + 1] = n0[o + 1]; out[o + 2] = n0[o + 2]
            }
        }
    }

    private fun accTri(p: FloatArray, i0: Int, i1: Int, i2: Int, acc: FloatArray) {
        val ux = p[i1] - p[i0]; val uy = p[i1 + 1] - p[i0 + 1]; val uz = p[i1 + 2] - p[i0 + 2]
        val vx = p[i2] - p[i0]; val vy = p[i2 + 1] - p[i0 + 1]; val vz = p[i2 + 2] - p[i0 + 2]
        val nx = uy * vz - uz * vy
        val ny = uz * vx - ux * vz
        val nz = ux * vy - uy * vx
        acc[i0] += nx; acc[i0 + 1] += ny; acc[i0 + 2] += nz
        acc[i1] += nx; acc[i1 + 1] += ny; acc[i1 + 2] += nz
        acc[i2] += nx; acc[i2 + 1] += ny; acc[i2 + 2] += nz
    }
}
