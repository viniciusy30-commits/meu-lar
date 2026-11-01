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
    val BODY_NAMES = listOf("Altura", "Peso", "Ombros", "Peito", "Busto", "Cintura", "Quadril", "Coxas", "Braços", "Cabeça")
    val FACE_NAMES = listOf(
        "Masculinidade", "Cílios", "Sobrancelha grossa", "Ponte do nariz", "Nariz largo", "Nariz para baixo", "Nariz para cima",
        "Boca larga", "Boca fina", "Cantos dos olhos para baixo", "Cantos dos olhos para cima", "Olhos quadrados", "Orelha élfica"
    )
    const val NB = 10
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
