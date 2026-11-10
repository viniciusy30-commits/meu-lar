package com.vinicius.meular

import android.opengl.Matrix
import kotlin.math.hypot
import kotlin.math.min

/**
 * Etapa 162: Tesla Model S branco, vindo do GLB `assets/obj3d/veic_tesla.glb` (ferramentas/tesla/tesla_para_jogo.py).
 * O GLB tem carroceria, 4 rodas (nós roda_*, giram em X; as da frente ficam dentro de dir_*, que viram em Y) e 4 portas
 * (nós porta_*, dobradiça vertical na quina da frente). Frente +Z, +X = lado do motorista (esquerda).
 * Aqui ficam só o estado das animações (abertura das portas) e a pose de cada nó; quem desenha é o Renderer3D.
 */
class TeslaCar(val g: GModel) {
    private val n = g.nodes.size
    /** 0 parado, 1 roda (gira em X), 2 direção (gira em Y) */
    private val kind = IntArray(n)
    /** índice da porta (FE, FD, TE, TD) de cada nó; -1 = não é porta */
    private val doorOf = IntArray(n) { -1 }
    private val w = Array(n) { FloatArray(16) }
    private val loc = FloatArray(16)
    /** abertura de cada porta, 0..1: frente-esquerda (motorista), frente-direita, trás-esquerda, trás-direita */
    val door = FloatArray(4)
    /** giro acumulado das rodas (rad) */
    var roll = 0f
    /** inclinação suavizada da carroceria (graus): cabeceio e rolagem */
    var pitch = 0f
    var lean = 0f
    private var lastSpeed = 0f

    init {
        for ((i, nd) in g.nodes.withIndex()) {
            when {
                nd.name.startsWith("roda_") -> kind[i] = 1
                nd.name.startsWith("dir_") -> kind[i] = 2
                nd.name.startsWith("porta_") -> doorOf[i] = DOORS.indexOf(nd.name.substring(6))
            }
        }
    }

    /**
     * Avança as animações. [lx], [lz] = posição do jogador no espaço do carro (+x esquerda, +z frente); [driving] = dirigindo.
     * A porta mais perto do jogador abre quando ele chega; dirigindo, todas fecham.
     */
    fun update(dt: Float, driving: Boolean, lx: Float, lz: Float, speed: Float, yawRate: Float) {
        var best = -1; var bd = 2.7f
        if (!driving) for (k in 0..3) {
            val sx = if (k % 2 == 0) 1f else -1f
            val hz = if (k < 2) 0.2f else -0.75f
            val d = hypot(lx - sx * 1.5f, lz - hz)
            if (d < bd) { bd = d; best = k }
        }
        for (k in 0..3) {
            val tgt = if (k == best) 1f else 0f
            door[k] += (tgt - door[k]) * min(1f, dt * (if (tgt > door[k]) 5f else 4f))
            if (door[k] < 0.002f) door[k] = 0f
        }
        roll += speed * dt / WHEEL_R
        if (roll > 6.2831853f) roll -= 6.2831853f else if (roll < -6.2831853f) roll += 6.2831853f
        // cabeceio (agacha ao acelerar, mergulha ao frear) e rolagem nas curvas — bem leve
        val acc = if (dt > 1e-4f) (speed - lastSpeed) / dt else 0f
        lastSpeed = speed
        val pt = (-acc * 0.10f).coerceIn(-1.4f, 1.4f)
        val lt = (-yawRate * speed * 0.05f).coerceIn(-2.2f, 2.2f)   // inclina para fora da curva
        pitch += (pt - pitch) * min(1f, dt * 6f)
        lean += (lt - lean) * min(1f, dt * 6f)
    }

    /** Calcula a matriz de mundo de cada nó; [base] = carro no mundo; [steerDeg] = esterço das rodas da frente. */
    fun pose(base: FloatArray, steerDeg: Float) {
        val rollDeg = Math.toDegrees(roll.toDouble()).toFloat()
        for (i in 0 until n) {
            val nd = g.nodes[i]
            val di = doorOf[i]
            if (di >= 0) nd.local(loc, nd.value(door[di]))
            else {
                nd.local(loc, 0f)
                if (kind[i] == 1) Matrix.rotateM(loc, 0, rollDeg, 1f, 0f, 0f)
                else if (kind[i] == 2) Matrix.rotateM(loc, 0, steerDeg, 0f, 1f, 0f)
            }
            val pw = if (nd.parent >= 0 && nd.parent < i) w[nd.parent] else base
            Matrix.multiplyMM(w[i], 0, pw, 0, loc, 0)
        }
    }

    fun world(i: Int): FloatArray = w[i]

    companion object {
        val DOORS = listOf("FE", "FD", "TE", "TD")
        const val WHEEL_R = 0.355f
        const val HALF_L = 2.5f
        const val HALF_W = 1.05f
    }
}
