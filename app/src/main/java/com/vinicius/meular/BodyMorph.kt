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

    /** true se nenhuma proporção (exceto a altura, que é feita à parte) está ativa. */
    fun isIdentity(b: FloatArray): Boolean {
        for (i in 1 until NB) if (abs(b[i]) > 1e-4f) return false
        return true
    }

    /**
     * Copia [src] (xyz por vértice, unidades do FBX: personagem com ~162 de altura, frente +Z, lado +X) para [dst] já deformado.
     * [b] = 10 valores de -1 a 1 (ordem de BODY_NAMES; o índice 0, altura, é ignorado aqui).
     */
    fun warp(src: FloatArray, dst: FloatArray, nv: Int, b: FloatArray) {
        if (isIdentity(b)) {
            System.arraycopy(src, 0, dst, 0, nv * 3)
            return
        }
        val peso = 0.14f * b[1]
        val ombro = 3.0f * b[2]
        val peito = 0.10f * b[3]
        val busto = 2.6f * b[4]
        val cint = 0.15f * b[5]
        val quad = 0.12f * b[6]
        val coxa = 0.25f * b[7]
        val braco = 0.25f * b[8]
        val cab = 0.12f * b[9]
        // eixo do braço (pose de repouso em A): do ombro (13,3; 142,5; -2,9) na direção do cotovelo
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
                dz += z * peito * w
            }
            if (busto != 0f) {
                val w = gs(y, 121f, 7f) * gs(ax, 8f, 6f) * sm(-1f, 5f, z)
                dz += busto * w
            }
            if (cint != 0f) {
                val w = sm(92f, 100f, y) * (1f - sm(110f, 118f, y)) * (1f - sm(20f, 30f, ax))
                dx += x * cint * w
                dz += z * cint * w
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
            dst[v * 3] = x + dx
            dst[v * 3 + 1] = y + dy
            dst[v * 3 + 2] = z + dz
        }
    }
}
