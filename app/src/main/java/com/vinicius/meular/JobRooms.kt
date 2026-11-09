package com.vinicius.meular

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * Etapa 142: interiores de cada local de trabalho, móvel por móvel.
 * Regras: corredor livre da porta até o primeiro ambiente (|u - cx| < 1.4), nada encostado na porta,
 * móveis de parede sempre virados para dentro, cada lugar com a sua planta e as suas peças próprias.
 * Direções: 0 olha p/ porta, 1 olha p/ fundo, 2 olha p/ -u (parede esquerda), 3 olha p/ +u (parede direita).
 */
object JobRooms {
    private val FL = City.FLOOR

    fun fill(s: JobSpace, job: Jobs.Job) {
        when (job.id) {
            "diarista" -> diarista(s); "lixeiro" -> lixeiro(s); "atendente" -> lanchonete(s); "entregador" -> entregas(s); "frentista" -> conveniencia(s); "repositor" -> mercado(s)
            "professor" -> escola(s); "secretario" -> escritorio(s); "policial" -> delegacia(s); "bombeiro" -> quartel(s); "mecanico" -> oficina(s); "enfermeiro" -> clinica(s)
            "medico" -> hospital(s); "advogado" -> advocacia(s); "juiz" -> forum(s); "engenheiro" -> construtora(s); "programador" -> tech(s); "empresario" -> sede(s); else -> prefeitura(s)
        }
        finish(s, job)
    }

    /** Acabamento: luminárias que não cruzam paredes, rodapé nas 4 paredes, faixa alta na cor do nível, saída de emergência, extintor e capacho. */
    private fun finish(s: JobSpace, job: Jobs.Job) {
        val d = s.depth; val yc = FL + s.h - 0.13f
        val accent = C(arrayOf("#2E7D32", "#1565C0", "#C62828", "#C9A227")[job.level - 1])
        var u = s.x0 + 1.7f
        while (u < s.x1 - 1.2f) { var v = 1.6f
            while (v < d - 0.9f) { if (s.wallsV.none { abs(it - v) < 0.6f } && s.wallsU.none { abs(it - u) < 0.9f }) { s.box(u, yc, v, 1.2f, 0.05f, 0.6f, C("#E6E6E6"), Mt.METAL); s.box(u, yc - 0.006f, v, 1.1f, 0.01f, 0.5f, C("#FFFBEA"), Mt.PLAIN, 1f, false) }; v += 3.2f }
            u += 3.4f }
        val bb = C("#7A7A7A")
        s.box(s.x0 + 0.03f, FL, d / 2, 0.04f, 0.1f, d, bb); s.box(s.x1 - 0.03f, FL, d / 2, 0.04f, 0.1f, d, bb); s.box(s.cx, FL, d - 0.03f, s.w, 0.1f, 0.04f, bb)
        s.box((s.x0 + s.cx - 1.4f) / 2, FL, 0.03f, s.cx - 1.4f - s.x0, 0.1f, 0.04f, bb); s.box((s.cx + 1.4f + s.x1) / 2, FL, 0.03f, s.x1 - s.cx - 1.4f, 0.1f, 0.04f, bb)
        val ys = FL + min(2.75f, s.h - 0.6f)
        s.box(s.x0 + 0.035f, ys, d / 2, 0.03f, 0.07f, d - 0.1f, accent); s.box(s.x1 - 0.035f, ys, d / 2, 0.03f, 0.07f, d - 0.1f, accent)
        s.exitSign(s.cx, 0.06f, 0, FL + 2.8f)
        s.extinguisher(s.cx + 1.9f, 0.04f, 0)
        s.rug(s.cx, 1.0f, 2.0f, 1.3f, shade(accent, -30), C("#2B2B2B"))
    }

    // ================================================================ NÍVEL 1

    /** Agência "Limpa Tudo": recepção turquesa, espera com sofá e TV, sala de treino e depósito com carrinhos de limpeza. */
    private fun diarista(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth; val wv = max(6.5f, d * 0.55f)
        s.reception(L + 3.6f, 3.2f, 1, 3.6f, C("#00838F"), C("#F5F5F5"), C("#4DD0E1"), 2)
        s.board(L + 3.6f, wv - 0.08f, 1, 2.6f, 2, FL + 1.0f, 1.0f)
        s.fileCab(L + 0.4f, 4.8f, 3, 2, C("#80CBC4"), 3)
        s.sofa(R - 0.5f, 3.4f, 2, 2.4f, C("#26A69A"), C("#FFF3E0")); s.sofa(R - 2.6f, wv - 0.55f, 0, 1.0f, C("#4DB6AC")); s.table(R - 1.8f, 3.4f, 0.6f, 1.0f, C("#ECEFF1"), C("#90A4AE"), 0.42f)
        s.papers(R - 1.8f, 3.2f, 0, FL + 0.42f); s.smallPlant(R - 1.8f, 3.7f, FL + 0.42f); s.rug(R - 1.9f, 3.4f, 2.4f, 2.6f, C("#B2DFDB"))
        s.tv(R - 0.03f, 6.0f, 3, 1.2f, FL + 1.3f, C("#00ACC1"))
        s.plant(R - 0.5f, 1.0f, 2, C("#ECEFF1")); s.plant(L + 0.5f, 1.0f, 1, C("#ECEFF1")); s.cooler(L + 0.4f, 6.0f)
        s.art(L + 0.03f, 2.2f, 2, 0.9f, 0.7f)
        s.box(c + 2.4f, FL, wv - 1.4f, 1.2f, 0.9f, 0.6f, C("#00838F"), Mt.WOOD, 0.5f); s.box(c + 2.4f, FL + 0.9f, wv - 1.4f, 1.15f, 0.5f, 0.55f, C("#E0F7FA"), Mt.GLASS); for (k in 0..3) s.oc(c + 2.0f + k * 0.26f, wv - 1.4f, 0, 0f, FL + 0.9f, 0f, 0.06f, 0.3f, pcU(k), Mt.PLAIN, 8); s.solid(c + 1.8f, wv - 1.7f, c + 3.0f, wv - 1.1f)
        s.box(c - 2.4f, FL, wv - 1.0f, 0.5f, 0.05f, 0.3f, C("#37474F"), Mt.METAL); s.box(c - 2.4f, FL + 0.05f, wv - 1.0f, 0.8f, 1.8f, 0.03f, C("#00ACC1")); s.box(c - 2.4f, FL + 1.2f, wv - 1.02f, 0.6f, 0.4f, 0.01f, C("#FFFFFF"), Mt.PLAIN, 1f, false)
        s.wallTo(wv, L, R, c, C("#E0F7FA"))
        // depósito / treino
        s.rack(c - 3f, d - 0.6f, 1, min(5f, (R - L) * 0.35f), 2.2f, C("#00ACC1"), C("#37474F"), 0.8f)
        for (k in 0 until 4) cart(s, R - 1.3f - k * 1.2f, wv + 1.6f, if (k % 2 == 0) C("#1E88E5") else C("#FDD835"))
        for (k in 0 until 3) { val wu = L + 0.6f + k * 0.75f; s.box(wu, FL, d - 0.4f, 0.68f, 0.88f, 0.62f, C("#FAFAFA"), Mt.METAL); s.oc(wu, d - 0.4f, 1, 0f, FL + 0.5f, -0.31f, 0.2f, 0.01f, C("#90A4AE"), Mt.METAL); s.box(wu, FL + 0.88f, d - 0.4f, 0.64f, 0.02f, 0.58f, C("#ECEFF1"), Mt.METAL); s.solid(wu - 0.34f, d - 0.72f, wu + 0.34f, d - 0.08f) }
        s.table(L + 2.6f, (wv + d) / 2 + 0.3f, 2.0f, 0.9f, C("#FAFAFA")); for (k in 0..2) s.box(L + 2.0f + k * 0.55f, FL + 0.75f, (wv + d) / 2 + 0.3f, 0.4f, 0.06f + k * 0.05f, 0.3f, pcU(k))
        s.chairW(L + 2.1f, (wv + d) / 2 - 0.5f, 1, C("#00838F"), metal = true); s.chairW(L + 3.1f, (wv + d) / 2 - 0.5f, 1, C("#00838F"), metal = true)
        s.board(R - 0.03f, (wv + d) / 2, 3, 2.0f, 0)
        s.clock(c, d - 0.03f, 1, FL + 2.3f)
    }
    private fun pcU(k: Int) = C(arrayOf("#4FC3F7", "#81C784", "#FFB74D")[k % 3])
    private fun cart(s: JobSpace, u: Float, v: Float, bucket: Int) {
        for (a in floatArrayOf(-0.3f, 0.3f)) for (e in floatArrayOf(-0.4f, 0.4f)) s.oc(u + a, v + e, 0, 0f, FL, 0f, 0.05f, 0.08f, C("#212121"), Mt.PLAIN, 6)
        s.box(u, FL + 0.1f, v, 0.65f, 0.04f, 0.9f, C("#ECEFF1"), Mt.METAL); s.box(u, FL + 0.6f, v, 0.65f, 0.04f, 0.9f, C("#ECEFF1"), Mt.METAL)
        for (a in floatArrayOf(-0.31f, 0.31f)) s.box(u + a, FL + 0.1f, v + 0.43f, 0.03f, 0.9f, 0.03f, C("#90A4AE"), Mt.METAL)
        s.box(u, FL + 1.0f, v + 0.43f, 0.65f, 0.03f, 0.03f, C("#90A4AE"), Mt.METAL)
        s.oc(u, v - 0.15f, 0, 0f, FL + 0.14f, 0f, 0.2f, 0.3f, bucket, Mt.PLAIN, 10, 0.24f)
        s.box(u + 0.15f, FL + 0.64f, v + 0.15f, 0.2f, 0.25f, 0.12f, C("#E91E63")); s.box(u - 0.12f, FL + 0.64f, v + 0.2f, 0.12f, 0.3f, 0.12f, C("#7CB342"))
        s.oc(u - 0.2f, v - 0.25f, 0, 0f, FL + 0.2f, 0f, 0.015f, 1.4f, C("#8D6E63"), Mt.WOOD, 5)
        s.solid(u - 0.35f, v - 0.5f, u + 0.35f, v + 0.5f)
    }

    /** Garagem da coleta: caminhões compactadores nas laterais, contêineres, bancada, vestiário e copa no fundo. */
    private fun lixeiro(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth; val wv = max(9f, d * 0.62f)
        s.box(c, FL + 0.003f, wv / 2, 2.2f, 0.004f, wv - 0.4f, C("#FBC02D"), Mt.PLAIN, 1f)
        s.box(c, FL + 0.004f, wv / 2, 2.0f, 0.004f, wv - 0.6f, C("#9E9E9E"), Mt.STONE, 0.6f)
        for (sd in floatArrayOf(-1f, 1f)) { val tu = c + sd * min(5f, (R - L) / 2 - 2.6f); truck(s, tu, wv / 2, 1, C(if (sd < 0) "#2E7D32" else "#388E3C")) }
        // contêineres coloridos da coleta seletiva encostados na esquerda
        val cols = arrayOf("#1565C0", "#C62828", "#2E7D32", "#F9A825", "#6D4C41")
        for (k in 0 until 5) { val bv = 1.4f + k * 1.15f; if (bv > wv - 1f) break
            s.box(L + 0.6f, FL + 0.08f, bv, 0.95f, 1.0f, 1.05f, C(cols[k]), Mt.PLASTER, 0.4f); s.box(L + 0.6f, FL + 1.08f, bv, 1.0f, 0.06f, 1.1f, shade(C(cols[k]), -25))
            for (e in floatArrayOf(-0.4f, 0.4f)) s.oc(L + 0.6f, bv + e, 0, 0f, FL, 0f, 0.06f, 0.08f, C("#212121"), Mt.PLAIN, 6); s.solid(L + 0.1f, bv - 0.55f, L + 1.1f, bv + 0.55f) }
        // bancada de ferramentas na direita
        s.counter(R - 0.4f, 2.6f, 3, 2.4f, 0.7f, C("#455A64"), C("#8D6E63"), 0.9f, false)
        s.board(R - 0.03f, 2.6f, 3, 2.2f, 2, FL + 1.2f, 0.9f)
        for (k in 0 until 3) s.oc(R - 0.5f, 4.6f + k * 0.7f, 0, 0f, FL, 0f, 0.28f, 0.9f, C(arrayOf("#1565C0", "#E65100", "#424242")[k]), Mt.METAL, 12)
        s.solid(R - 0.8f, 4.2f, R - 0.2f, 6.2f)
        s.wallTo(wv, L, R, c - 2.5f, C("#E8F5E9"))
        // vestiário (esquerda) e copa (direita) separados por parede
        s.wallAlong(c, wv, d, Float.NaN, C("#E8F5E9"))
        s.lockers(L + (c - L) / 2, d - 0.3f, 1, min(10, ((c - L - 1f) / 0.48f).toInt()), C("#2E7D32"))
        s.box(L + 0.6f, FL + 1.8f, wv + 1.2f, 0.05f, 0.05f, 1.6f, C("#9E9E9E"), Mt.METAL); for (k in 0..3) s.box(L + 0.6f, FL + 1.1f, wv + 0.6f + k * 0.4f, 0.4f, 0.7f, 0.08f, C(if (k % 2 == 0) "#FF6F00" else "#2E7D32"), Mt.FABRIC)
        val ku = c + (R - c) / 2
        s.table(ku, (wv + d) / 2, 1.8f, 0.9f, C("#ECEFF1")); for (sd in floatArrayOf(-1f, 1f)) for (q in floatArrayOf(-0.5f, 0.5f)) s.chairW(ku + q, (wv + d) / 2 + sd * 0.75f, if (sd < 0) 1 else 0, C("#2E7D32"), metal = true)
        s.counter(R - 1.6f, d - 0.35f, 1, 2.6f, 0.6f, C("#FAFAFA"), C("#607D8B")); s.microwave(R - 2.2f, d - 0.35f, 1); s.coffeeMachine(R - 1.2f, d - 0.35f, 1); s.homeFridge(R - 0.45f, wv + 0.8f, 2)
        s.board(c + 0.09f, (wv + d) / 2, 3, 1.6f, 2, FL + 1.1f, 0.9f)
    }
    private fun truck(s: JobSpace, u: Float, v: Float, dir: Int, c: Int) {
        for (a in floatArrayOf(-1.1f, 1.1f)) for (e in floatArrayOf(-2.4f, -1.2f, 2.6f)) { s.ob(u, v, dir, a, FL, e, 0.32f, 1.0f, 1.0f, C("#1A1A1A")); s.ob(u, v, dir, a * 1.03f, FL + 0.3f, e, 0.3f, 0.4f, 0.4f, C("#9E9E9E"), Mt.METAL) }
        s.ob(u, v, dir, 0f, FL + 0.55f, 0f, 2.3f, 0.35f, 7.4f, C("#263238"), Mt.METAL)
        s.ob(u, v, dir, 0f, FL + 0.9f, 2.6f, 2.3f, 1.9f, 2.0f, C("#FAFAFA"), Mt.METAL)
        s.ob(u, v, dir, 0f, FL + 1.85f, 3.61f, 2.1f, 0.8f, 0.03f, C("#2A3A48"), Mt.GLASS)
        for (sd in floatArrayOf(-1f, 1f)) s.ob(u, v, dir, sd * 0.85f, FL + 1.1f, 3.61f, 0.3f, 0.15f, 0.03f, C("#FFF9C4"), Mt.PLAIN, 1f, false)
        s.ob(u, v, dir, 0f, FL + 0.9f, -1.0f, 2.4f, 2.4f, 5.0f, c, Mt.METAL)
        s.ob(u, v, dir, 0f, FL + 1.8f, -1.0f, 2.42f, 0.25f, 5.0f, C("#FAFAFA"))
        s.ob(u, v, dir, 0f, FL + 0.8f, -3.6f, 2.3f, 2.3f, 0.4f, shade(c, -20), Mt.METAL)
        s.ob(u, v, dir, 0f, FL + 2.8f, 2.2f, 0.7f, 0.12f, 0.25f, C("#FF6F00"), Mt.PLAIN, 1f, false)
        for (sd in floatArrayOf(-1f, 1f)) s.ob(u, v, dir, sd * 0.95f, FL + 0.6f, -3.85f, 0.3f, 0.06f, 0.5f, C("#BDBDBD"), Mt.METAL)
        s.os(u, v, dir, -1.25f, -3.9f, 1.25f, 3.7f)
    }

    /** Lanchonete "Burguer da Esquina": balcão com banquetas, cozinha aberta, cabines estofadas, mesas e quadro de cardápio iluminado. */
    private fun lanchonete(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth; val cv = d * 0.6f
        s.box(c, FL + 0.002f, cv / 2, s.w - 0.1f, 0.004f, cv, C("#FAFAFA"), Mt.TILE, 0.5f)
        // balcão de atendimento com caixa e vitrine
        s.counter(c, cv, 1, min(s.w - 4f, 9f), 0.8f, C("#C62828"), C("#ECEFF1"), 1.05f, false)
        s.box(c, FL + 0.2f, cv - 0.41f, min(s.w - 4f, 9f), 0.08f, 0.01f, C("#FFFFFF"), Mt.PLAIN, 1f, false)
        s.box(c - 2.2f, FL + 1.09f, cv, 0.4f, 0.12f, 0.35f, C("#212121")); s.monitor(c - 2.2f, cv, 0, FL + 1.21f, 0.34f, C("#FFB300"))
        s.box(c + 1.5f, FL + 1.09f, cv, 1.6f, 0.45f, 0.6f, C("#E1F5FE"), Mt.GLASS); for (k in 0..3) s.box(c + 0.95f + k * 0.37f, FL + 1.12f, cv, 0.3f, 0.12f, 0.4f, C(arrayOf("#8D6E63", "#FFB74D", "#F06292", "#A1887F")[k]))
        for (k in 0 until max(2, ((min(s.w - 4f, 9f)) / 1.1f).toInt() - 1)) s.stool(c - min(s.w - 4f, 9f) / 2 + 0.7f + k * 1.1f, cv - 0.85f, C("#C62828"), 0.78f)
        // cozinha atrás do balcão
        s.counter(c - 2.5f, d - 0.4f, 1, 3.4f, 0.7f, C("#B0BEC5"), C("#CFD8DC"), 0.9f)
        s.box(c - 3.4f, FL + 0.9f, d - 0.4f, 1.4f, 0.06f, 0.6f, C("#212121"), Mt.METAL); for (k in 0..1) s.box(c - 1.8f + k * 0.55f, FL + 0.9f, d - 0.4f, 0.45f, 0.12f, 0.5f, C("#455A64"), Mt.METAL)
        s.box(c - 2.5f, FL + 2.0f, d - 0.5f, 3.6f, 0.6f, 0.9f, C("#B0BEC5"), Mt.METAL); s.box(c - 2.5f, FL + 2.6f, d - 0.3f, 0.5f, s.h - 2.6f, 0.4f, C("#B0BEC5"), Mt.METAL)
        s.fridge(c + 2.5f, d - 0.45f, 1, 2.4f); s.counter(c + 0.3f, (cv + d) / 2 + 0.3f, 0, 1.8f, 0.7f, C("#B0BEC5"), C("#CFD8DC"))
        // cardápio luminoso sobre a cozinha
        val mw = min(s.w - 3f, 8f); s.box(c, FL + 2.75f, d - 0.06f, mw, 0.75f, 0.05f, C("#1A1A1A"))
        for (k in 0..3) s.box(c - mw / 2 + mw * (k + 0.5f) / 4, FL + 2.82f, d - 0.09f, mw / 4 - 0.15f, 0.6f, 0.01f, C(arrayOf("#FFB300", "#E53935", "#43A047", "#FB8C00")[k]), Mt.PLAIN, 1f, false)
        // cabines na parede esquerda
        var bv = 1.8f
        while (bv + 1.9f < cv - 0.6f) { booth(s, L + 0.95f, bv + 0.95f, C("#B71C1C")); bv += 2.1f }
        // mesas redondas na direita
        var tv2 = 2.0f
        while (tv2 < cv - 1.2f) { val tu = R - 1.6f; s.tableRound(tu, tv2, 0.45f, C("#FAFAFA")); s.chairW(tu - 0.75f, tv2, 3, C("#C62828"), metal = true); s.chairW(tu + 0.75f, tv2, 2, C("#C62828"), metal = true)
            s.box(tu - 0.1f, FL + 0.75f, tv2, 0.1f, 0.14f, 0.07f, C("#E53935")); s.box(tu + 0.06f, FL + 0.75f, tv2, 0.06f, 0.16f, 0.06f, C("#FDD835")); tv2 += 2.1f }
        for (sd in floatArrayOf(-1f, 1f)) { val tu = c + sd * 2.6f; val tv3 = cv * 0.45f; s.table(tu, tv3, 1.2f, 0.8f, C("#FAFAFA"), C("#9E9E9E")); for (q in floatArrayOf(-0.3f, 0.3f)) { s.chairW(tu + q, tv3 - 0.65f, 1, C("#C62828"), metal = true); s.chairW(tu + q, tv3 + 0.65f, 0, C("#C62828"), metal = true) }; s.box(tu, FL + 0.75f, tv3, 0.1f, 0.14f, 0.07f, C("#E53935")) }
        s.art(L + 0.03f, cv / 2 + 0.6f, 2, 0.8f, 0.6f, FL + 1.6f); s.tv(R - 0.03f, cv * 0.5f, 3, 1.1f, FL + 1.9f, C("#2E7D32"))
        s.plant(c - 2.0f, 0.7f, 0); s.bin(c + 2.6f, 0.5f, C("#C62828"))
        for (k in 0..2) s.pendant(c - 2f + k * 2f, cv - 0.4f, 1.0f, C("#C62828"))
    }
    private fun booth(s: JobSpace, u: Float, v: Float, c: Int) {
        for (sd in floatArrayOf(-1f, 1f)) { val bv = v + sd * 0.72f
            s.box(u, FL, bv, 1.3f, 0.45f, 0.5f, shade(c, -15), Mt.FABRIC); s.box(u, FL + 0.45f, bv, 1.3f, 0.08f, 0.5f, c, Mt.FABRIC)
            s.box(u, FL + 0.45f, bv + sd * 0.2f, 1.3f, 0.7f, 0.12f, c, Mt.FABRIC); s.box(u, FL + 1.15f, bv + sd * 0.2f, 1.32f, 0.05f, 0.14f, C("#3E2723"), Mt.WOOD)
            s.solid(u - 0.65f, bv - 0.25f, u + 0.65f, bv + 0.25f) }
        s.box(u - 0.05f, FL + 0.72f, v, 1.1f, 0.04f, 0.75f, C("#FAFAFA"), Mt.STONE); s.box(u - 0.05f, FL, v, 0.08f, 0.72f, 0.08f, C("#9E9E9E"), Mt.METAL)
        s.box(u - 0.2f, FL + 0.76f, v, 0.25f, 0.02f, 0.25f, C("#FAFAFA")); s.box(u - 0.2f, FL + 0.78f, v, 0.14f, 0.07f, 0.14f, C("#D7A35B")); s.box(u + 0.25f, FL + 0.76f, v - 0.15f, 0.08f, 0.18f, 0.08f, C("#C62828"))
        s.solid(u - 0.6f, v - 0.38f, u + 0.6f, v + 0.38f)
    }

    /** Central "Entrega Já": balcão de despacho, esteira de pacotes, porta-paletes, mesas de embalagem e motos estacionadas. */
    private fun entregas(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth
        s.reception(L + 2.8f, 2.6f, 1, 3.0f, C("#E65100"), C("#FFF3E0"), C("#FFB74D"), 1)
        s.board(L + 0.03f, 4.4f, 2, 2.0f, 2, FL + 1.0f, 1.0f); s.cooler(L + 0.4f, 1.3f)
        // esteira transversal no meio
        val ev = d * 0.48f; val e0 = L + 4.8f; val e1 = R - 4.8f
        if (e1 - e0 > 3f) {
            for (k in 0..((e1 - e0) / 1.4f).toInt()) { val lu = e0 + k * 1.4f; s.box(lu, FL, ev, 0.08f, 0.8f, 0.9f, C("#455A64"), Mt.METAL) }
            s.box((e0 + e1) / 2, FL + 0.8f, ev, e1 - e0, 0.08f, 0.9f, C("#212121")); for (sd in floatArrayOf(-0.47f, 0.47f)) s.box((e0 + e1) / 2, FL + 0.8f, ev + sd, e1 - e0, 0.14f, 0.04f, C("#FDD835"), Mt.METAL)
            var pu = e0 + 0.5f; while (pu < e1 - 0.5f) { val pw = s.rr(0.35f, 0.6f); s.box(pu, FL + 0.88f, ev + s.rr(-0.15f, 0.15f), pw, s.rr(0.2f, 0.4f), s.rr(0.3f, 0.5f), s.pc(arrayOf("#C49A6C", "#B8895A", "#D2AE82")), Mt.PLAIN); pu += pw + s.rr(0.4f, 1.0f) }
            s.solid(e0, ev - 0.5f, e1, ev + 0.5f)
            for (sd in floatArrayOf(-1f, 1f)) { s.table(c + sd * 2.4f, ev + sd * 1.6f, 1.8f, 0.8f, C("#BCAAA4"), C("#5D4037"), 0.9f); s.box(c + sd * 2.4f - 0.4f, FL + 0.9f, ev + sd * 1.6f, 0.5f, 0.3f, 0.4f, C("#C49A6C")); s.oc(c + sd * 2.4f + 0.5f, ev + sd * 1.6f, 0, 0f, FL + 0.9f, 0f, 0.08f, 0.06f, C("#8D6E63"), Mt.PLAIN, 8) }
        }
        s.rack(c - 0.5f, d - 0.6f, 1, min(s.w - 9f, 9.6f), min(3.2f, s.h - 0.8f))
        // motos com baú na direita, viradas para a porta
        for (k in 0 until 3) { val mu = R - 1.0f - k * 1.3f; moto(s, mu, 3.0f) }
        s.box(R - 2.3f, FL + 0.003f, 3.0f, 4.0f, 0.004f, 3.0f, C("#FDD835"), Mt.PLAIN, 1f)
        s.board(R - 0.03f, d * 0.7f, 3, 2.4f, 0, FL + 1.0f, 1.1f)
        s.plant(L + 0.5f, d - 0.6f, 2, C("#ECEFF1"))
    }
    private fun moto(s: JobSpace, u: Float, v: Float) {
        s.box(u, FL, v - 0.7f, 0.12f, 0.6f, 0.6f, C("#1A1A1A")); s.box(u, FL, v + 0.7f, 0.12f, 0.6f, 0.6f, C("#1A1A1A"))
        s.box(u, FL + 0.35f, v, 0.3f, 0.35f, 1.3f, C("#E65100"), Mt.METAL); s.box(u, FL + 0.7f, v + 0.25f, 0.28f, 0.1f, 0.6f, C("#212121"), Mt.FABRIC)
        s.box(u, FL + 0.6f, v - 0.6f, 0.06f, 0.6f, 0.06f, C("#9E9E9E"), Mt.METAL); s.box(u, FL + 1.18f, v - 0.6f, 0.7f, 0.04f, 0.04f, C("#212121"))
        s.box(u, FL + 0.8f, v + 0.6f, 0.5f, 0.48f, 0.48f, C("#E65100")); s.box(u, FL + 0.95f, v + 0.35f, 0.4f, 0.12f, 0.01f, C("#FFFFFF"), Mt.PLAIN, 1f, false)
        s.box(u, FL + 0.95f, v - 0.67f, 0.12f, 0.1f, 0.04f, C("#FFF9C4"), Mt.PLAIN, 1f, false)
        s.solid(u - 0.3f, v - 1.0f, u + 0.3f, v + 1.0f)
    }

    /** Loja de conveniência do posto: caixa com cigarreira, gôndolas, geladeiras, freezer de sorvete, café e caixa eletrônico. */
    private fun conveniencia(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth
        s.reception(L + 2.2f, 2.2f, 3, 2.4f, C("#0F7A3D"), C("#ECEFF1"), C("#FFE14D"), 1)
        s.ob(L + 0.25f, 2.2f, 3, 0f, FL + 1.1f, -0.1f, 2.2f, 1.2f, 0.3f, C("#4E342E"), Mt.WOOD); for (j in 0..3) for (i in 0..6) s.ob(L + 0.25f, 2.2f, 3, -0.95f + i * 0.32f, FL + 1.15f + j * 0.28f, -0.26f, 0.26f, 0.2f, 0.02f, C(arrayOf("#FAFAFA", "#C62828", "#1565C0", "#FDD835")[(i + j) % 4]))
        val gl = min(3.2f, d - 4.5f)
        for (k in 0..1) { val gu = c + 0.8f + k * 2.4f; if (gu > R - 3.2f) break; s.gondola(gu, d * 0.5f, 3, gl, false) }
        s.fridge(R - 0.45f, d / 2, 2, min(d - 2.5f, 6f))
        s.box(c - 1.6f, FL, d - 0.6f, 1.6f, 0.85f, 0.8f, C("#ECEFF1"), Mt.METAL); s.box(c - 1.6f, FL + 0.85f, d - 0.6f, 1.5f, 0.03f, 0.7f, C("#CFE8F2"), Mt.GLASS); for (k in 0..3) s.box(c - 2.1f + k * 0.33f, FL + 0.6f, d - 0.6f, 0.28f, 0.24f, 0.6f, C(arrayOf("#F48FB1", "#FFF59D", "#80DEEA", "#BCAAA4")[k]), Mt.PLAIN, 1f, false); s.solid(c - 2.4f, d - 1.0f, c - 0.8f, d - 0.2f)
        s.counter(L + 1.6f, d - 0.4f, 1, 2.6f, 0.6f, C("#4E342E"), C("#212121")); s.coffeeMachine(L + 1.1f, d - 0.4f, 1); s.coffeeMachine(L + 1.7f, d - 0.4f, 1); for (k in 0..2) s.oc(L + 2.3f + k * 0.12f, d - 0.4f, 0, 0f, FL + 0.92f, 0f, 0.04f, 0.3f, C("#FAFAFA"), Mt.PLAIN, 8)
        s.box(L + 0.4f, FL, d - 2.2f, 0.7f, 1.7f, 0.6f, C("#37474F"), Mt.METAL); s.box(L + 0.72f, FL + 1.1f, d - 2.2f, 0.02f, 0.3f, 0.4f, C("#4FC3F7"), Mt.PLAIN, 1f, false); s.solid(L + 0.05f, d - 2.5f, L + 0.75f, d - 1.9f)
        s.bin(c + 2.0f, 0.5f, C("#0F7A3D")); s.vending(R - 0.45f, 1.2f, 2, C("#1565C0"))
    }

    /** Supermercado "Super Bom": frente de caixas, hortifrúti, corredores de gôndolas, açougue/padaria e geladeiras no fundo. */
    private fun mercado(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth
        // caixas dos dois lados do corredor de entrada
        val nck = max(1, ((c - 1.6f - L - 1f) / 2.0f).toInt())
        for (k in 0 until min(nck, 4)) { s.checkout(c - 2.2f - k * 2.0f, 3.2f, 1); s.checkout(c + 2.6f + k * 2.0f, 3.2f, 1, C("#1E88E5")) }
        s.box(c, FL + s.h - 1.1f, 3.2f, s.w - 2f, 0.4f, 0.06f, C("#E53935")); for (k in -3..3) s.box(c + k * 2f, FL + s.h - 1.05f, 3.17f, 1.2f, 0.28f, 0.01f, C("#FFFFFF"), Mt.PLAIN, 1f, false)
        // carrinhos na entrada (direita) e hortifrúti (esquerda)
        for (k in 0 until 5) trolley(s, R - 1.0f, 0.9f + k * 0.5f)
        val hv = 6.0f
        for (k in 0..2) { val hu = L + 1.3f + k * 2.0f; if (hu > c - 2.5f) break
            s.box(hu, FL, hv, 1.6f, 0.75f, 1.1f, C("#6D4C41"), Mt.WOOD, 0.5f); s.solid(hu - 0.8f, hv - 0.55f, hu + 0.8f, hv + 0.55f)
            for (i in 0..3) for (j in 0..2) s.ball(hu - 0.6f + i * 0.4f, FL + 0.82f, hv - 0.35f + j * 0.35f, 0.14f, C(arrayOf("#E53935", "#FB8C00", "#FDD835", "#7CB342", "#8E24AA", "#43A047")[(k * 2 + (i + j) / 2) % 6])) }
        // corredores
        val g0 = 8.5f; val g1 = d - 3.0f
        if (g1 - g0 > 2.5f) { var gu = L + 2.0f; var k = 0
            while (gu < R - 1.8f) { if (abs(gu - c) > 1.9f) s.gondola(gu, (g0 + g1) / 2, 3, g1 - g0 - 1.2f); gu += 2.6f; k++ }
            s.box(c, FL + s.h - 1.3f, (g0 + g1) / 2, 0.06f, 0.5f, 1.4f, C("#1565C0")) }
        s.fridge(c, d - 0.45f, 1, s.w - 1.2f)
        // ilha de congelados no corredor central não bloqueia: só pendurados
        for (k in 0..2) s.pendant(c, 5f + k * 3f, 0.8f, C("#E53935"))
        s.art(L + 0.03f, 4.0f, 2, 1.6f, 1.0f, FL + 2.0f, C("#E53935"))
    }
    private fun trolley(s: JobSpace, u: Float, v: Float) {
        s.box(u, FL + 0.12f, v, 0.55f, 0.05f, 0.4f, C("#9E9E9E"), Mt.METAL); s.box(u, FL + 0.45f, v, 0.55f, 0.45f, 0.42f, C("#B0BEC5"), Mt.METAL); s.box(u, FL + 0.95f, v + 0.2f, 0.55f, 0.04f, 0.04f, C("#E53935"))
        s.solid(u - 0.3f, v - 0.22f, u + 0.3f, v + 0.25f)
    }

    // ================================================================ NÍVEL 2

    /** Escola "Saber": secretaria, mural, corredor central e quatro salas de aula diferentes (lousa, mesa do professor, carteiras, estante, globo). */
    private fun escola(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth; val hv = 5.0f
        s.reception(L + 3.0f, 2.4f, 1, 3.0f, C("#F9A825"), C("#FFFDE7"), C("#1565C0"), 1)
        s.waitRow(R - 2.6f, 1.3f, 1, 4, C("#1565C0")); s.board(R - 0.03f, 3.0f, 3, 2.2f, 2, FL + 1.0f, 1.0f); s.cooler(R - 0.4f, hv - 0.6f)
        s.plant(L + 0.5f, 0.7f, 3); s.fileCab(L + 0.4f, 4.0f, 3, 2, C("#FFE082"), 3)
        for (sd in floatArrayOf(-1f, 1f)) { val tu = c + sd * 3.2f
            s.box(tu, FL, hv - 0.3f, 2.2f, 0.8f, 0.45f, C("#6D4C41"), Mt.WOOD, 0.5f); s.box(tu, FL + 0.8f, hv - 0.3f, 2.2f, 1.2f, 0.45f, C("#E3F2FD"), Mt.GLASS); s.box(tu, FL + 2.0f, hv - 0.3f, 2.24f, 0.06f, 0.48f, C("#6D4C41"), Mt.WOOD)
            for (k in 0..3) { s.oc(tu - 0.75f + k * 0.5f, hv - 0.3f, 0, 0f, FL + 0.85f, 0f, 0.06f, 0.2f + (k % 2) * 0.1f, C("#C9A227"), Mt.METAL, 8); s.ball(tu - 0.75f + k * 0.5f, FL + 1.12f + (k % 2) * 0.1f, hv - 0.3f, 0.09f, C("#E8C26E")) }
            s.box(tu, FL + 1.38f, hv - 0.3f, 2.1f, 0.02f, 0.4f, C("#CFE8F2"), Mt.GLASS); s.solid(tu - 1.1f, hv - 0.55f, tu + 1.1f, hv - 0.05f)
            s.bench(tu, hv - 1.6f, 1, 2.0f, C("#1565C0"), C("#424242")) }
        s.wallTo(hv, L, R, c, C("#FFF8E1"))
        val mid = c; val dv = (hv + d) / 2
        for (sd in floatArrayOf(-1f, 1f)) {
            val ua = if (sd < 0) L else mid + 1.5f; val ub = if (sd < 0) mid - 1.5f else R
            s.wallAlong(if (sd < 0) ub else ua, hv, dv, hv + 1.2f, C("#FFF8E1")); s.wallAlong(if (sd < 0) ub else ua, dv, d, dv + 1.2f, C("#FFF8E1"))
            s.wallTo(dv, ua, ub, Float.NaN, C("#FFF8E1"))
            for (q in 0..1) {
                val v0 = if (q == 0) hv else dv; val v1 = if (q == 0) dv else d
                classroom(s, ua, ub, v0, v1, (q + (if (sd < 0) 0 else 2)))
            }
        }
        // armários de alunos no corredor
        s.lockers(mid - 1.25f, d - 0.3f, 1, 2, C("#1565C0"), false)
        s.clock(mid, d - 0.03f, 1, FL + 2.2f)
    }
    private fun classroom(s: JobSpace, ua: Float, ub: Float, v0: Float, v1: Float, k: Int) {
        val cu = (ua + ub) / 2; val rw = ub - ua
        val wallC = arrayOf("#C8E6C9", "#BBDEFB", "#FFE0B2", "#E1BEE7")[k % 4]
        s.box(cu, FL + 1.0f, v1 - 0.07f, rw - 0.2f, 0.06f, 0.02f, C(wallC))
        s.board(cu, v1 - 0.08f, 1, min(3.4f, rw - 1.6f), if (k % 2 == 0) 1 else 0, FL + 0.9f, 1.15f)
        s.desk(cu - rw * 0.28f, v1 - 1.4f, 0, 1.3f, 0.7f, C("#8D6E63")); s.chairO(cu - rw * 0.28f, v1 - 0.75f, 0, C("#455A64")); s.papers(cu - rw * 0.28f - 0.3f, v1 - 1.4f, 0); s.mug(cu - rw * 0.28f + 0.3f, v1 - 1.3f)
        s.oc(cu - rw * 0.28f + 0.45f, v1 - 1.45f, 0, 0f, FL + 0.76f, 0f, 0.05f, 0.18f, C("#5D4037"), Mt.PLAIN, 6); s.ball(cu - rw * 0.28f + 0.45f, FL + 1.06f, v1 - 1.45f, 0.13f, C("#1E88E5"))
        val cols = max(2, ((rw - 1.6f) / 1.15f).toInt()); val rows = max(1, ((v1 - v0 - 3.4f) / 1.2f).toInt())
        for (i in 0 until cols) for (j in 0 until rows) { val su = ua + 0.9f + i * (rw - 1.8f) / max(1, cols - 1); val sv = v1 - 2.8f - j * 1.2f
            if (sv < v0 + 0.7f) continue
            s.box(su, FL + 0.7f, sv, 0.7f, 0.035f, 0.5f, C("#D7B98E"), Mt.WOOD, 0.5f); s.box(su, FL, sv + 0.05f, 0.05f, 0.7f, 0.05f, C("#607D8B"), Mt.METAL); s.box(su, FL + 0.35f, sv, 0.6f, 0.03f, 0.4f, C("#607D8B"), Mt.METAL); s.solid(su - 0.35f, sv - 0.25f, su + 0.35f, sv + 0.25f)
            s.chairW(su, sv - 0.55f, 1, C("#607D8B"), C(arrayOf("#1565C0", "#E53935", "#43A047", "#FB8C00")[k % 4]), true)
            if ((i + j + k) % 3 == 0) s.box(su - 0.1f, FL + 0.735f, sv, 0.25f, 0.03f, 0.32f, C(arrayOf("#E53935", "#1E88E5", "#FDD835")[(i + j) % 3])) }
        val side = if (ua < s.cx) ua + 0.03f else ub - 0.03f; val sdir = if (ua < s.cx) 2 else 3
        s.bookcase(if (ua < s.cx) ua + 0.25f else ub - 0.25f, v0 + 1.2f, if (ua < s.cx) 2 else 3, 1.6f, C("#A1887F"), 1.4f)
        s.board(side, (v0 + v1) / 2 + 0.6f, sdir, 1.2f, 2, FL + 1.2f, 0.8f)
        s.ac(cu, v0 + 0.08f, 0)
    }

    /** Escritório "Adm & Cia": recepção, baias com divisórias, sala de reunião de vidro, copiadora, arquivos e copa. */
    private fun escritorio(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth
        s.reception(L + 3.2f, 2.4f, 1, 3.2f, C("#37474F"), C("#ECEFF1"), C("#29B6F6"), 1)
        s.sofa(R - 2.2f, 1.0f, 1, 2.4f, C("#546E7A"), C("#FFCC80")); s.table(R - 2.2f, 2.1f, 1.0f, 0.55f, C("#ECEFF1"), C("#90A4AE"), 0.42f); s.plant(R - 0.5f, 2.6f, 1)
        s.art(R - 0.03f, 4.2f, 3, 1.2f, 0.8f)
        val mr = R - min(5.5f, s.w * 0.33f); val mv = d * 0.55f
        // baias em pares (de costas) com divisória
        val bv = 5.2f
        var bu = L + 1.6f
        while (bu < mr - 1.4f) { for (j in 0 until 2) { val vv = bv + j * 3.4f; if (vv > d - 2.2f) break
                s.station(bu, vv, 0, 1.4f, 1, C("#ECEFF1"), C("#37474F")); s.station(bu, vv - 0.77f, 1, 1.4f, 1, C("#ECEFF1"), C("#37474F"))
                s.box(bu, FL + 0.76f, vv - 0.385f, 1.4f, 0.45f, 0.04f, C("#78909C"), Mt.FABRIC); s.box(bu + 0.73f, FL, vv - 0.385f, 0.05f, 1.21f, 1.55f, C("#78909C"), Mt.FABRIC) }
            bu += 2.0f; if (abs(bu - c) < 1.3f) bu = c + 1.3f }
        // sala de reunião com parede de vidro
        s.wallAlong(mr, mv, d, (mv + d) / 2, C("#ECEFF1"), true); s.wallTo(mv, mr, R, Float.NaN, C("#ECEFF1"), true)
        val tu = (mr + R) / 2; val tv = (mv + d) / 2 + 0.2f
        s.table(tu, tv, min(3.0f, R - mr - 1.6f), 1.2f, C("#5D4037"))
        for (k in 0..2) { s.chairO(tu - 1.0f + k * 1.0f, tv - 0.95f, 1, C("#263238")); s.chairO(tu - 1.0f + k * 1.0f, tv + 0.95f, 0, C("#263238")) }
        s.tv(R - 0.03f, tv, 3, 1.4f, FL + 1.2f)
        // apoio: copiadora, arquivos, copa
        s.copier(c + 0.8f, d - 0.4f, 1); s.fileCab(L + 1.4f, d - 0.33f, 1, 4, C("#90A4AE")); s.counter(c - 2.2f, d - 0.35f, 1, 1.8f, 0.6f, C("#FAFAFA"), C("#455A64")); s.coffeeMachine(c - 2.6f, d - 0.35f, 1); s.microwave(c - 1.8f, d - 0.35f, 1)
        s.cooler(L + 0.4f, 4.4f); s.clock(c, d - 0.03f, 1, FL + 2.3f)
    }

    /** Delegacia: balcão de ocorrências com vidro, bancos, mural de procurados, sala do delegado, mesas dos agentes, celas com grade e armário de armas. */
    private fun delegacia(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth; val wv = d * 0.45f
        s.box(c, FL + 0.002f, wv / 2, s.w - 0.1f, 0.004f, wv, C("#CFD8DC"), Mt.TILE, 0.6f)
        s.reception(c - 3.6f, 3.0f, 1, 4.0f, C("#0E2A5C"), C("#ECEFF1"), C("#FFD54F"), 2)
        s.box(c - 3.6f, FL + 1.15f, 2.8f, 4.0f, 1.0f, 0.03f, C("#CFE8F2"), Mt.GLASS); s.box(c - 3.6f, FL + 2.15f, 2.8f, 4.0f, 0.06f, 0.06f, C("#263238"), Mt.METAL)
        s.box(c - 3.6f, FL + 2.3f, 2.75f, 2.2f, 0.4f, 0.04f, C("#0E2A5C")); s.box(c - 3.6f, FL + 2.37f, 2.72f, 1.9f, 0.25f, 0.01f, C("#FFD54F"), Mt.PLAIN, 1f, false)
        s.bench(R - 1.6f, 1.0f, 0, 2.6f, C("#455A64"), C("#263238")); s.bench(R - 1.6f, 3.0f, 0, 2.6f, C("#455A64"), C("#263238"))
        s.board(R - 0.03f, 2.2f, 3, 2.2f, 2, FL + 1.0f, 1.1f)
        for (k in 0..5) s.box(R - 0.06f, FL + 1.25f + (k / 3) * 0.45f, 1.5f + (k % 3) * 0.6f, 0.01f, 0.36f, 0.28f, C("#FFFDE7"))
        s.oc(L + 0.6f, 0.8f, 0, 0f, FL, 0f, 0.03f, 2.4f, C("#C9A227"), Mt.METAL, 6); s.box(L + 0.95f, FL + 1.7f, 0.8f, 0.7f, 0.5f, 0.02f, C("#1B5E20"), Mt.FABRIC)
        s.waitRow(c + 2.8f, wv - 1.0f, 0, 4, C("#0E2A5C")); s.plant(c + 1.8f, wv - 0.5f, 2, C("#ECEFF1")); s.cooler(c + 4.6f, wv - 0.4f); s.tv(c + 2.8f, wv - 0.08f, 1, 1.2f, FL + 1.5f, C("#1565C0"))
        s.art(c - 3.6f, wv - 0.04f, 1, 1.8f, 0.9f, FL + 1.3f, C("#0E2A5C"))
        s.wallTo(wv, L, R, c, C("#ECEFF1"))
        // mesas dos agentes no meio
        for (k in 0 until 2) for (q in 0..1) { val du = c - 3.2f + k * 2.6f + (if (k == 1) 1.4f else 0f); val dv = wv + 1.6f + q * 2.2f; if (dv > d - 4.8f) break; s.station(du, dv, 0, 1.4f, 1, C("#90A4AE"), C("#0E2A5C")) }
        // sala do delegado à esquerda
        val ou = L + min(5f, s.w * 0.3f)
        s.wallAlong(ou, wv, d - 4.6f, (wv + d - 4.6f) / 2, C("#ECEFF1"), true)
        s.desk((L + ou) / 2, wv + 2.0f, 1, 1.8f, 0.8f, C("#4E342E")); s.chairO((L + ou) / 2, wv + 1.25f, 1, C("#1A1A1A")); s.monitor((L + ou) / 2 - 0.3f, wv + 2.1f, 1)
        s.bookcase(L + 0.25f, wv + 2.0f, 2, 2.0f, C("#4E342E"), 2.0f)
        // celas
        val cv0 = d - 4.2f
        s.wallTo(cv0 - 0.4f, L, ou, (L + ou) / 2 + 1.2f, C("#ECEFF1")); s.rack((L + ou) / 2, d - 0.6f, 1, ou - L - 1.0f, 2.2f, C("#455A64"), C("#263238"), 0.8f)
        val n = 3; val cw = (R - ou - 0.2f) / n
        for (k in 0 until n) { val ua = ou + 0.1f + k * cw; val ub = ua + cw
            if (k > 0) { s.box(ua, FL, (cv0 + d) / 2, 0.15f, s.h, d - cv0, C("#B0BEC5"), Mt.PLASTER, 0.5f); s.solid(ua - 0.08f, cv0, ua + 0.08f, d) }
            var gu = ua + 0.12f; while (gu < ub - 0.08f) { s.oc(gu, cv0, 0, 0f, FL, 0f, 0.025f, 2.5f, C("#37474F"), Mt.METAL, 5); gu += 0.18f }
            s.box((ua + ub) / 2, FL + 2.5f, cv0, cw, 0.1f, 0.1f, C("#37474F"), Mt.METAL); s.box((ua + ub) / 2, FL + 1.0f, cv0, cw, 0.06f, 0.06f, C("#37474F"), Mt.METAL); s.solid(ua, cv0 - 0.06f, ub, cv0 + 0.06f)
            s.box((ua + ub) / 2, FL + 0.45f, d - 0.5f, cw - 0.5f, 0.08f, 0.75f, C("#757575"), Mt.STONE); s.box((ua + ub) / 2, FL, d - 0.5f, cw - 0.7f, 0.45f, 0.6f, C("#9E9E9E"), Mt.STONE); s.box((ua + ub) / 2, FL + 0.53f, d - 0.5f, cw - 0.6f, 0.06f, 0.65f, C("#E0E0E0"), Mt.FABRIC)
            s.box(ub - 0.5f, FL, cv0 + 1.0f, 0.45f, 0.42f, 0.55f, C("#ECEFF1"), Mt.METAL); s.solid((ua + ub) / 2 - cw / 2 + 0.2f, d - 0.9f, (ua + ub) / 2 + cw / 2 - 0.2f, d - 0.1f) }
        s.lockers((L + ou) / 2 - 0.8f, cv0 - 0.7f, 0, 3, C("#263238"), false)
    }

    /** Quartel dos bombeiros: garagem com caminhão e ambulância, cabideiro de equipamentos, cano de descida, alojamento com beliches e cozinha. */
    private fun quartel(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth; val gv = d * 0.62f
        s.box(c, FL + 0.003f, gv / 2, s.w - 0.2f, 0.004f, gv, C("#B0B0B0"), Mt.STONE, 0.6f)
        fireTruck(s, c - 3.6f, gv / 2 + 0.3f); s.car(c + 3.6f, gv / 2 + 0.3f, 0, C("#FAFAFA")); s.ob(c + 3.6f, gv / 2 + 0.3f, 0, 0f, FL + 0.6f, 0f, 1.78f, 0.15f, 4.22f, C("#C62828")); s.ob(c + 3.6f, gv / 2 + 0.3f, 0, 0f, FL + 1.35f, 0.6f, 0.9f, 0.12f, 0.3f, C("#E53935"), Mt.PLAIN, 1f, false); s.os(c + 3.6f, gv / 2 + 0.3f, 0, -0.95f, -2.2f, 0.95f, 2.2f)
        // equipamentos no lado esquerdo: cabides com capacete, jaqueta e botas
        val nk = min(6, ((gv - 1.5f) / 0.8f).toInt())
        s.box(L + 0.15f, FL + 1.9f, 1.0f + nk * 0.4f, 0.1f, 0.06f, nk * 0.8f, C("#616161"), Mt.METAL)
        for (k in 0 until nk) { val gv2 = 1.4f + k * 0.8f
            s.box(L + 0.35f, FL + 0.9f, gv2, 0.3f, 0.95f, 0.6f, C("#5D4037"), Mt.FABRIC); s.box(L + 0.36f, FL + 1.25f, gv2, 0.31f, 0.06f, 0.61f, C("#FDD835"), Mt.PLAIN, 1f, false)
            s.oc(L + 0.35f, gv2, 0, 0f, FL + 1.98f, 0f, 0.17f, 0.18f, C("#FDD835"), Mt.PLAIN, 10, 0.12f)
            s.box(L + 0.35f, FL, gv2 - 0.1f, 0.28f, 0.35f, 0.14f, C("#212121")); s.box(L + 0.35f, FL, gv2 + 0.1f, 0.28f, 0.35f, 0.14f, C("#212121")) }
        s.solid(L, 1.0f, L + 0.65f, 1.0f + nk * 0.8f)
        // cano de descida e mangueiras
        s.oc(c, gv - 1.2f, 0, 0f, FL, 0f, 0.06f, s.h, C("#E0E0E0"), Mt.METAL, 8); s.oc(c, gv - 1.2f, 0, 0f, FL, 0f, 0.6f, 0.12f, C("#C62828"), Mt.FABRIC, 12); s.solid(c - 0.1f, gv - 1.3f, c + 0.1f, gv - 1.1f)
        for (k in 0..2) s.oc(R - 0.5f, 1.2f + k * 0.9f, 0, 0f, FL, 0f, 0.38f, 0.22f, C("#ECEFF1"), Mt.FABRIC, 12)
        s.solid(R - 0.9f, 0.8f, R - 0.1f, 3.4f)
        s.wallTo(gv, L, R, c - 2f, C("#FFEBEE"))
        // alojamento à esquerda, cozinha à direita
        s.wallAlong(c + 0.5f, gv, d, Float.NaN, C("#FFEBEE"))
        var bu = L + 0.6f; while (bu < c - 0.8f) { s.bunk(bu, d - 1.1f, 1, C("#B71C1C")); bu += 1.4f }
        s.lockers(L + (c - L) / 2 + 0.6f, gv + 0.35f, 0, min(6, ((c - L - 2f) / 0.48f).toInt()), C("#C62828"), false)
        val ku = c + 0.5f + (R - c - 0.5f) / 2
        s.counter(ku, d - 0.35f, 1, R - c - 1.4f, 0.65f, C("#ECEFF1"), C("#37474F")); s.homeFridge(R - 0.45f, gv + 1.0f, 2, C("#B0BEC5")); s.microwave(ku - 0.8f, d - 0.35f, 1); s.coffeeMachine(ku + 0.6f, d - 0.35f, 1)
        s.table(ku, (gv + d) / 2, 2.0f, 0.9f, C("#8D6E63")); for (q in floatArrayOf(-0.55f, 0.55f)) { s.chairW(ku + q, (gv + d) / 2 - 0.75f, 1); s.chairW(ku + q, (gv + d) / 2 + 0.75f, 0) }
        s.tv(c + 0.62f, (gv + d) / 2, 3, 1.1f, FL + 1.4f, C("#C62828"))
    }
    private fun fireTruck(s: JobSpace, u: Float, v: Float) {
        val dir = 0
        for (a in floatArrayOf(-1.1f, 1.1f)) for (e in floatArrayOf(-2.6f, -1.4f, 2.4f)) { s.ob(u, v, dir, a, FL, e, 0.32f, 1.0f, 1.0f, C("#1A1A1A")); s.ob(u, v, dir, a * 1.03f, FL + 0.3f, e, 0.3f, 0.4f, 0.4f, C("#BDBDBD"), Mt.METAL) }
        s.ob(u, v, dir, 0f, FL + 0.5f, 0f, 2.4f, 2.2f, 7.6f, C("#C62828"), Mt.METAL)
        s.ob(u, v, dir, 0f, FL + 1.6f, 3.0f, 2.2f, 0.9f, 0.02f, C("#2A3A48"), Mt.GLASS); s.ob(u, v, dir, 0f, FL + 1.3f, -0.6f, 2.42f, 0.12f, 6.0f, C("#ECEFF1"))
        for (k in 0..3) s.ob(u, v, dir, 1.21f, FL + 0.7f, -2.6f + k * 1.3f, 0.02f, 0.5f, 1.1f, C("#9E9E9E"), Mt.METAL)
        s.ob(u, v, dir, 0f, FL + 2.75f, -0.8f, 0.6f, 0.12f, 5.6f, C("#BDBDBD"), Mt.METAL); for (k in 0..9) s.ob(u, v, dir, 0f, FL + 2.75f, -3.4f + k * 0.55f, 0.6f, 0.13f, 0.04f, C("#9E9E9E"), Mt.METAL)
        s.ob(u, v, dir, 0f, FL + 2.72f, 3.2f, 1.4f, 0.12f, 0.25f, C("#FF1744"), Mt.PLAIN, 1f, false)
        for (sd in floatArrayOf(-0.85f, 0.85f)) s.ob(u, v, dir, sd, FL + 0.8f, 3.81f, 0.3f, 0.15f, 0.02f, C("#FFF9C4"), Mt.PLAIN, 1f, false)
        s.os(u, v, dir, -1.25f, -3.85f, 1.25f, 3.85f)
    }

    /** Oficina "Motor Forte": elevadores com carros, painel de ferramentas, bancada com morsa, prateleira de pneus, tambores de óleo, compressor e balcão. */
    private fun oficina(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth
        s.box(c, FL + 0.003f, d / 2, s.w - 0.2f, 0.004f, d - 0.2f, C("#9E9E9E"), Mt.STONE, 0.6f)
        // dois boxes com elevador
        for ((k, sd) in floatArrayOf(-1f, 1f).withIndex()) { val lu = c + sd * min(4.5f, s.w / 2 - 3f); val lv = d * 0.48f
            s.box(lu, FL + 0.004f, lv, 3.2f, 0.004f, 5.4f, C("#FDD835")); s.box(lu, FL + 0.005f, lv, 3.0f, 0.004f, 5.2f, C("#8E8E8E"), Mt.STONE, 0.6f)
            for (a in floatArrayOf(-1.3f, 1.3f)) { s.box(lu + a, FL, lv, 0.3f, 2.2f, 0.4f, C("#1565C0"), Mt.METAL); s.box(lu + a, FL + 1.55f, lv, 0.12f, 0.08f, 3.6f, C("#FFC107"), Mt.METAL) }
            s.box(lu, FL + 2.2f, lv, 2.9f, 0.15f, 0.3f, C("#1565C0"), Mt.METAL)
            s.car(lu, lv, 1, C(if (k == 0) "#1E88E5" else "#7B1FA2"), FL + 1.6f); s.solid(lu - 1.45f, lv - 2.2f, lu + 1.45f, lv + 2.2f)
            s.box(lu + 0.9f, FL, lv + 2.8f, 0.6f, 0.9f, 0.45f, C("#C62828"), Mt.METAL); for (j in 0..3) s.box(lu + 0.9f, FL + 0.15f + j * 0.2f, lv + 2.57f, 0.5f, 0.15f, 0.01f, C("#B71C1C")); s.solid(lu + 0.6f, lv + 2.55f, lu + 1.2f, lv + 3.05f) }
        // parede do fundo: bancada + painel de ferramentas
        val bl = min(6f, s.w - 6f)
        s.counter(c, d - 0.4f, 1, bl, 0.75f, C("#455A64"), C("#8D6E63"), 0.9f, false); s.box(c - bl / 2 + 0.4f, FL + 0.94f, d - 0.4f, 0.25f, 0.2f, 0.18f, C("#37474F"), Mt.METAL)
        s.box(c, FL + 1.1f, d - 0.05f, bl, 1.2f, 0.03f, C("#ECEFF1"), Mt.METAL)
        for (i in 0 until (bl / 0.3f).toInt()) for (j in 0..2) s.box(c - bl / 2 + 0.15f + i * 0.3f, FL + 1.25f + j * 0.35f, d - 0.08f, 0.04f, s.rr(0.15f, 0.28f), 0.02f, s.pc(arrayOf("#D32F2F", "#212121", "#9E9E9E", "#1565C0")))
        // pneus empilhados e tambores
        for (k in 0 until 3) for (j in 0..4) s.oc(R - 0.5f, 1.2f + k * 0.8f, 0, 0f, FL + j * 0.24f, 0f, 0.34f, 0.22f, C("#1A1A1A"), Mt.PLAIN, 12)
        s.solid(R - 0.9f, 0.8f, R - 0.1f, 3.4f)
        for (k in 0..2) { s.oc(L + 0.45f, d - 1.0f - k * 0.7f, 0, 0f, FL, 0f, 0.3f, 0.9f, C(arrayOf("#1565C0", "#C62828", "#2E7D32")[k]), Mt.METAL, 12); s.oc(L + 0.45f, d - 1.0f - k * 0.7f, 0, 0f, FL + 0.9f, 0f, 0.3f, 0.01f, C("#9E9E9E"), Mt.METAL, 12) }
        s.solid(L + 0.1f, d - 2.8f, L + 0.8f, d - 0.6f)
        s.oc(L + 0.6f, d - 3.6f, 0, 0f, FL + 0.2f, 0f, 0.3f, 0.9f, C("#D32F2F"), Mt.METAL, 12); s.box(L + 0.6f, FL, d - 3.6f, 0.7f, 0.2f, 0.5f, C("#424242"), Mt.METAL); s.solid(L + 0.2f, d - 3.9f, L + 1.0f, d - 3.3f)
        // balcão de atendimento perto da porta
        s.reception(L + 2.6f, 2.0f, 1, 2.8f, C("#37474F"), C("#8D6E63"), C("#FFC107"), 1); s.waitRow(R - 2.6f, 4.2f, 2, 3, C("#455A64"))
        s.vending(L + 0.5f, 3.6f, 3, C("#FFC107")); s.board(L + 0.03f, 1.0f, 2, 1.0f, 2, FL + 1.2f, 0.8f)
    }

    /** Posto de saúde: recepção, triagem, espera, três consultórios com maca, pia, armário e mesa, e sala de vacina. */
    private fun clinica(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth; val wv = max(5.5f, d * 0.4f)
        s.reception(L + 3.0f, 2.6f, 1, 3.4f, C("#00897B"), C("#FFFFFF"), C("#80CBC4"), 2)
        s.waitRow(R - 2.5f, 1.4f, 1, 5, C("#26A69A")); s.waitRow(R - 2.5f, 3.6f, 0, 5, C("#26A69A")); s.plant(R - 0.5f, wv - 0.6f, 3)
        s.tv(R - 0.03f, 2.5f, 3, 1.0f, FL + 1.8f, C("#00897B")); s.cooler(L + 0.4f, wv - 0.6f); s.board(L + 0.03f, 1.4f, 2, 1.2f, 2, FL + 1.1f, 0.9f)
        val n = 3; val rw = s.w / n
        for (k in 0 until n) s.wallTo(wv, L + k * rw, L + (k + 1) * rw, if (k == 1) c else L + k * rw + rw - 1.2f - (if (k == 0) 0f else rw - 2.4f), C("#E0F2F1"))
        for (k in 0 until n) { val ua = L + k * rw; val ub = ua + rw; val dc = if (k == 1) c - 1.2f else (ua + ub) / 2
            if (k > 0) s.wallAlong(ua, wv, d, Float.NaN, C("#E0F2F1"))
            val du = (ua + ub) / 2
            s.bedH(ub - 0.9f, d - 1.4f, 1, C(arrayOf("#B2DFDB", "#BBDEFB", "#F8BBD0")[k]))
            s.desk(ua + 1.4f, wv + 1.6f, 1, 1.4f, 0.7f, C("#ECEFF1")); s.chairO(ua + 1.4f, wv + 0.9f, 1, C("#00695C")); s.monitor(ua + 1.25f, wv + 1.7f, 1); s.chairW(ua + 1.4f, wv + 2.45f, 0, C("#90A4AE"), metal = true)
            s.sinkCab(ua + 0.4f, d - 0.9f, 2, 1.2f); s.fileCab(ua + 0.35f, (wv + d) / 2 + 0.2f, 3, 1, C("#ECEFF1"), 3)
            s.art(du, d - 0.03f, 1, 0.7f, 0.5f, FL + 1.5f)
            if (dc < 0f) Unit }
    }

    // ================================================================ NÍVEL 3

    /** Hospital: recepção dupla, espera, posto de enfermagem, corredor com enfermarias de 2 leitos e centro cirúrgico no fim. */
    private fun hospital(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth; val hv = 7.0f
        s.reception(c - 4.5f, 3.6f, 1, 4.0f, C("#FAFAFA"), C("#E3F2FD"), C("#1E88E5"), 2)
        s.box(c - 4.5f, FL + s.h - 1.0f, 3.2f, 3.4f, 0.5f, 0.06f, C("#1565C0")); s.box(c - 4.5f, FL + s.h - 0.95f, 3.16f, 3.0f, 0.36f, 0.01f, C("#FFFFFF"), Mt.PLAIN, 1f, false)
        for (i in 0 until 2) s.waitRow(c + 4.2f, 1.6f + i * 1.6f, 1, 6, C("#1E88E5"))
        s.plant(L + 0.6f, 0.7f, 1); s.plant(R - 0.6f, 0.7f, 1); s.vending(R - 0.45f, 5.2f, 2, C("#1565C0")); s.cooler(R - 0.4f, 6.2f); s.tv(R - 0.03f, 3.0f, 3, 1.3f, FL + 1.8f, C("#00ACC1"))
        for (sd in floatArrayOf(-1f, 1f)) { s.plant(c + sd * 2.0f, hv - 0.7f, 1, C("#ECEFF1")); s.box(c + sd * 2.0f, FL, hv - 1.6f, 0.6f, 1.2f, 0.4f, C("#1E88E5"), Mt.METAL); s.box(c + sd * 2.0f, FL + 0.7f, hv - 1.81f, 0.5f, 0.4f, 0.01f, C("#E3F2FD"), Mt.PLAIN, 1f, false); s.solid(c + sd * 2.0f - 0.3f, hv - 1.8f, c + sd * 2.0f + 0.3f, hv - 1.4f) }
        s.wallTo(hv, L, R, c, C("#E3F2FD"))
        val mid = c
        for (sd in floatArrayOf(-1f, 1f)) {
            val ua = if (sd < 0) L else mid + 2f; val ub = if (sd < 0) mid - 2f else R
            val nr = max(1, ((d - hv) / 6.5f).toInt()); val rd = (d - hv) / nr
            val wallU = if (sd < 0) ub else ua; val outer = if (sd < 0) ua else ub; val bdir = if (sd < 0) 2 else 3
            for (k in 0 until nr) { val v0 = hv + k * rd; val v1 = v0 + rd
                s.wallAlong(wallU, v0, v1, v0 + 1.0f, C("#E3F2FD"))
                if (k < nr - 1) s.wallTo(v1, ua, ub, Float.NaN, C("#E3F2FD"))
                for (q in 0..1) { val bv = v0 + rd * (0.3f + q * 0.45f) + 0.3f; val bu = outer - sd * 1.2f
                    s.bedH(bu, bv, bdir, C(if (q == 0) "#90CAF9" else "#A5D6A7"))
                    if (q == 0) { s.box((ua + ub) / 2 + sd * 0.4f, FL + 2.3f, (v0 + v1) / 2 + 0.15f, ub - ua - 1.6f, 0.04f, 0.04f, C("#B0BEC5"), Mt.METAL); s.box((ua + ub) / 2 + sd * 0.4f - sd * 0.0f, FL + 0.25f, (v0 + v1) / 2 + 0.15f, 1.8f, 2.05f, 0.03f, C("#B2DFDB"), Mt.FABRIC) } }
                s.chairW(wallU - sd * 1.6f, v1 - 0.6f, if (sd < 0) 2 else 3, C("#90A4AE"), C("#1E88E5"), true)
                s.art(outer + sd * 0.03f - sd * 0f, (v0 + v1) / 2 + 0.15f, if (sd < 0) 2 else 3, 0.6f, 0.45f, FL + 1.6f)
                s.ac((ua + ub) / 2, v0 + 0.1f, 1) }
        }
        // posto de enfermagem no corredor e centro cirúrgico
        s.counter(mid - 1.55f, hv + 2.5f, 3, 1.8f, 0.5f, C("#1E88E5"), C("#FAFAFA")); s.monitor(mid - 1.55f, hv + 2.3f, 3, FL + 0.96f, 0.4f); s.papers(mid - 1.55f, hv + 2.9f, 3, FL + 0.96f)
        s.wallTo(d - 4f, mid - 2f, mid + 2f, mid, C("#E3F2FD"))
        s.box(mid, FL, d - 2.0f, 0.8f, 0.85f, 2.0f, C("#CFD8DC"), Mt.METAL); s.box(mid, FL + 0.85f, d - 2.0f, 0.7f, 0.1f, 1.9f, C("#4DB6AC"), Mt.FABRIC); s.solid(mid - 0.4f, d - 3.0f, mid + 0.4f, d - 1.0f)
        s.oc(mid, d - 2.0f, 0, 0f, FL + s.h - 1.2f, 0f, 0.5f, 0.15f, C("#ECEFF1"), Mt.METAL, 14); s.oc(mid, d - 2.0f, 0, 0f, FL + s.h - 1.21f, 0f, 0.42f, 0.01f, C("#FFFDE7"), Mt.PLAIN, 14, 0.42f, false)
        s.box(mid + 1.4f, FL, d - 2.0f, 0.6f, 1.1f, 0.5f, C("#90A4AE"), Mt.METAL); s.box(mid + 1.4f, FL + 1.1f, d - 2.0f, 0.5f, 0.35f, 0.08f, C("#263238")); s.solid(mid + 1.1f, d - 2.25f, mid + 1.7f, d - 1.75f)
        s.box(mid - 1.4f, FL + 0.9f, d - 2.0f, 0.7f, 0.04f, 0.5f, C("#B0BEC5"), Mt.METAL); s.box(mid - 1.4f, FL, d - 2.0f, 0.05f, 0.9f, 0.05f, C("#9E9E9E"), Mt.METAL); s.solid(mid - 1.75f, d - 2.25f, mid - 1.05f, d - 1.75f)
    }

    /** Escritório de advocacia: recepção em mármore e madeira, sala de espera com poltronas, biblioteca jurídica, sala de reunião e sala do sócio. */
    private fun advocacia(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth; val wv = max(5.5f, d * 0.4f)
        s.box(c, FL + 0.002f, wv / 2, s.w - 0.1f, 0.004f, wv, C("#8D6E58"), Mt.FLOOR_D, 0.5f); s.rug(c, wv / 2 + 0.3f, 2.2f, wv - 1.6f, C("#7B2D26"), C("#C9A227"))
        s.reception(L + 3.0f, 2.6f, 1, 3.0f, C("#2B1D16"), C("#EDE7DC"), C("#D4AF37"), 1)
        s.box(L + 3.0f, FL + 1.6f, wv - 0.08f, 2.4f, 0.6f, 0.03f, C("#D4AF37"), Mt.METAL)
        s.sofa(R - 0.5f, 2.6f, 2, 2.2f, C("#5D4037"), C("#D7CCC8")); s.sofa(R - 2.4f, 0.9f, 1, 1.0f, C("#3E2723")); s.table(R - 1.7f, 2.6f, 0.7f, 1.2f, C("#2B1D16"), C("#D4AF37"), 0.45f); s.floorLamp(R - 0.5f, 0.6f)
        s.rug(R - 1.8f, 2.6f, 2.8f, 3.0f, C("#8D6E63"), C("#3E2723")); s.art(L + 0.03f, 2.6f, 2, 1.2f, 0.9f, FL + 1.1f, C("#C9A227"))
        s.bookcase(c + 2.2f, wv - 0.22f, 1, 2.4f, C("#3E2723"), 2.2f); s.plant(c - 1.8f, wv - 0.5f, 1, C("#212121"))
        s.wallTo(wv, L, R, c, C("#EFE6D8"))
        s.wallAlong(c, wv, d, (wv + d) / 2, C("#EFE6D8"), true)
        // sala de reunião
        val mu = (L + c) / 2; val mv = (wv + d) / 2
        s.table(mu, mv, min(4f, c - L - 2f), 1.3f, C("#4E342E"))
        for (k in 0 until 4) { val cu = mu - 1.35f + k * 0.9f; s.chairO(cu, mv - 1.0f, 1, C("#3E2723")); s.chairO(cu, mv + 1.0f, 0, C("#3E2723")) }
        s.bookcase(mu, d - 0.22f, 1, min(4.5f, c - L - 1f), C("#4E342E"), 2.3f); s.tv(L + 0.03f, mv, 2, 1.3f, FL + 1.2f)
        // sala do sócio
        val pu = (c + R) / 2
        s.desk(pu, d - 2.4f, 0, 2.2f, 0.9f, C("#3E2723")); s.chairO(pu, d - 1.6f, 0, C("#1A1A1A")); s.monitor(pu - 0.3f, d - 2.5f, 0); s.deskLamp(pu + 0.8f, d - 2.6f, FL + 0.76f, C("#C9A227")); s.papers(pu + 0.3f, d - 2.3f, 0)
        s.chairW(pu - 0.6f, d - 3.5f, 1, C("#3E2723"), C("#8D6E63")); s.chairW(pu + 0.6f, d - 3.5f, 1, C("#3E2723"), C("#8D6E63"))
        s.bookcase(pu, d - 0.22f, 1, min(4.5f, R - c - 1f), C("#3E2723"), 2.3f); s.plant(R - 0.5f, wv + 0.6f, 1, C("#212121"))
        s.oc(R - 0.5f, d - 1.0f, 0, 0f, FL, 0f, 0.25f, 0.9f, C("#ECEFF1"), Mt.STONE, 10); s.ball(R - 0.5f, FL + 1.15f, d - 1.0f, 0.22f, C("#1E3A6E"))
    }

    /** Fórum: saguão com colunas e detector de metal, balcão de protocolo, tribunal com bancada elevada, mesas das partes, júri e plateia. */
    private fun forum(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth; val hv = 6.5f
        s.box(c, FL + 0.002f, hv / 2, s.w - 0.1f, 0.004f, hv, C("#E8E0D0"), Mt.STONE, 0.5f)
        for (k in 0..3) { val pu = L + 2f + k * (s.w - 4f) / 3; if (abs(pu - c) < 1.6f) continue; s.oc(pu, 3.5f, 0, 0f, FL, 0f, 0.35f, s.h, C("#EFE6D8"), Mt.STONE, 14); s.box(pu, FL, 3.5f, 0.9f, 0.2f, 0.9f, C("#D8CCB4"), Mt.STONE); s.solid(pu - 0.45f, 3.05f, pu + 0.45f, 3.95f) }
        // detector de metal e esteira de raio-x
        for (sd in floatArrayOf(-0.5f, 0.5f)) s.box(c + sd, FL, 2.2f, 0.12f, 2.2f, 0.5f, C("#9E9E9E"), Mt.METAL); s.box(c, FL + 2.2f, 2.2f, 1.12f, 0.15f, 0.5f, C("#9E9E9E"), Mt.METAL)
        s.solid(c - 0.56f, 1.95f, c - 0.44f, 2.45f); s.solid(c + 0.44f, 1.95f, c + 0.56f, 2.45f)
        s.box(c + 1.8f, FL, 2.2f, 0.8f, 0.85f, 2.2f, C("#616161"), Mt.METAL); s.box(c + 1.8f, FL + 0.85f, 2.2f, 0.6f, 0.03f, 2.2f, C("#212121")); s.box(c + 1.8f, FL + 0.85f, 2.2f, 0.85f, 0.6f, 0.9f, C("#757575"), Mt.METAL); s.solid(c + 1.4f, 1.1f, c + 2.2f, 3.3f)
        s.reception(L + 2.8f, 1.6f, 3, 2.4f, C("#5D4037"), C("#EFE6D8"), C("#C9A227"), 1); s.waitRow(R - 2.0f, 5.4f, 0, 4, C("#6D4C41"))
        s.wallTo(hv, L, R, c, C("#E8DCC4"))
        // tribunal
        s.box(c, FL + 0.002f, (hv + d) / 2, s.w - 0.1f, 0.004f, d - hv, C("#6D4C41"), Mt.FLOOR_D, 0.5f)
        s.box(c, FL, d - 1.7f, 6.4f, 0.4f, 3.2f, C("#5D4037"), Mt.WOOD, 0.5f); s.box(c, FL + 0.4f, d - 2.85f, 5.4f, 1.15f, 0.12f, C("#4E342E"), Mt.WOOD, 0.5f); s.box(c, FL + 1.55f, d - 2.85f, 5.6f, 0.06f, 0.5f, C("#3E2723"), Mt.WOOD, 0.5f)
        for (k in 0..4) s.box(c - 2.2f + k * 1.1f, FL + 0.6f, d - 2.92f, 0.8f, 0.7f, 0.01f, C("#5D4037"), Mt.WOOD, 0.5f)
        s.solid(c - 3.2f, d - 3.3f, c + 3.2f, d - 0.1f)
        val juu = c; s.chairO(juu, d - 1.7f, 0, C("#1A1A1A")); s.box(juu, FL + 0.4f + 1.3f, d - 0.9f, 0.6f, 0.9f, 0.08f, C("#1A1A1A"), Mt.FABRIC)
        s.box(c + 0.6f, FL + 1.61f, d - 2.75f, 0.1f, 0.06f, 0.25f, C("#8D6E63"), Mt.WOOD); s.box(c - 0.8f, FL + 1.61f, d - 2.75f, 0.3f, 0.03f, 0.4f, C("#FAFAFA"))
        s.box(c, FL + 2.3f, d - 0.05f, 1.6f, 1.6f, 0.04f, C("#C9A227"), Mt.METAL); s.box(c, FL + 2.45f, d - 0.08f, 1.3f, 1.3f, 0.01f, C("#E8DCC4"))
        for (sd in floatArrayOf(-1f, 1f)) { s.oc(c + sd * 3.8f, d - 0.5f, 0, 0f, FL, 0f, 0.03f, 2.6f, C("#C9A227"), Mt.METAL, 6); s.box(c + sd * 3.8f + 0.35f, FL + 1.8f, d - 0.5f, 0.7f, 0.6f, 0.02f, C(if (sd < 0) "#1B5E20" else "#0D47A1"), Mt.FABRIC)
            s.table(c + sd * 2.6f, d - 5.2f, 2.2f, 0.9f, C("#6D4C41")); s.chairO(c + sd * 2.6f - 0.5f, d - 6.0f, 1, C("#3E2723")); s.chairO(c + sd * 2.6f + 0.5f, d - 6.0f, 1, C("#3E2723")); s.papers(c + sd * 2.6f, d - 5.2f, 1); s.box(c + sd * 2.6f + 0.6f, FL + 0.75f, d - 5.1f, 0.3f, 0.2f, 0.06f, C("#212121")) }
        // júri lateral
        if (R - c > 7f) { for (r in 0..1) for (k in 0..3) s.chairW(R - 0.8f - r * 0.8f, d - 5.5f + k * 0.65f, 2, C("#5D4037"), C("#8D6E63")); s.box(R - 1.9f, FL, d - 4.5f, 0.08f, 1.0f, 3.0f, C("#4E342E"), Mt.WOOD, 0.5f); s.solid(R - 1.95f, d - 6.0f, R - 1.85f, d - 3.0f) }
        // grade e plateia
        val gv = d - 7.0f
        if (gv > hv + 1.5f) { for (sd in floatArrayOf(-1f, 1f)) { s.box(c + sd * (1.0f + (s.w / 2 - 1.5f) / 2), FL + 0.85f, gv, s.w / 2 - 1.5f, 0.08f, 0.1f, C("#4E342E"), Mt.WOOD); var gu = c + sd * 1.0f; while (abs(gu - c) < s.w / 2 - 0.5f) { s.box(gu, FL, gv, 0.05f, 0.85f, 0.05f, C("#4E342E"), Mt.WOOD); gu += sd * 0.25f }; s.solid(c + sd * 1.0f, gv - 0.06f, c + sd * (s.w / 2 - 0.5f), gv + 0.06f) }
            var rv = hv + 1.0f; while (rv < gv - 0.8f) { for (sd in floatArrayOf(-1f, 1f)) { val pu = c + sd * (1.0f + (s.w / 2 - 2f) / 2); s.bench(pu, rv, 1, s.w / 2 - 2.4f, C("#6D4C41"), C("#3E2723")); s.box(pu, FL + 0.45f, rv - 0.22f, s.w / 2 - 2.4f, 0.5f, 0.05f, C("#6D4C41"), Mt.WOOD, 0.5f) }; rv += 1.2f } }
        for (k in 0..2) s.pendant(c - 3f + k * 3f, (hv + d) / 2, 1.2f, C("#C9A227"))
    }

    /** Construtora: recepção amarela, maquete iluminada, pranchetas, plotter, mesa de reunião, cabideiro de capacetes e plantas de obra na parede. */
    private fun construtora(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth
        s.reception(L + 2.8f, 2.4f, 1, 3.0f, C("#F9A825"), C("#FFFFFF"), C("#37474F"), 1)
        s.box(c - 3.0f, FL, 2.2f, 1.6f, 0.9f, 0.8f, C("#37474F"), Mt.METAL); for (k in 0..3) s.box(c - 3.55f + k * 0.37f, FL + 0.9f, 2.2f, 0.3f, 0.05f + k * 0.04f, 0.6f, C(arrayOf("#BDBDBD", "#8D6E63", "#E0E0E0", "#A1887F")[k]), Mt.STONE); s.solid(c - 3.8f, 1.8f, c - 2.2f, 2.6f)
        // maquete
        val mu = R - 3.0f; val mv = 3.0f
        s.box(mu, FL, mv, 2.4f, 0.85f, 1.8f, C("#37474F"), Mt.METAL); s.box(mu, FL + 0.85f, mv, 2.3f, 0.03f, 1.7f, C("#A5D6A7"))
        for (i in 0..2) for (j in 0..1) { val bh = 0.15f + ((i * 3 + j * 5) % 5) * 0.12f; s.box(mu - 0.75f + i * 0.75f, FL + 0.88f, mv - 0.4f + j * 0.8f, 0.4f, bh, 0.4f, C("#ECEFF1")); s.box(mu - 0.75f + i * 0.75f, FL + 0.88f + bh, mv - 0.4f + j * 0.8f, 0.42f, 0.02f, 0.42f, C("#90CAF9")) }
        s.box(mu, FL + 0.885f, mv, 2.2f, 0.004f, 0.12f, C("#616161")); for (k in 0..3) s.ball(mu - 1.0f + k * 0.65f, FL + 0.95f, mv + 0.75f, 0.06f, C("#2E7D32"))
        s.box(mu, FL + 0.88f, mv, 2.32f, 0.7f, 1.72f, C("#E3F2FD"), Mt.GLASS); s.solid(mu - 1.2f, mv - 0.9f, mu + 1.2f, mv + 0.9f)
        s.plant(R - 0.5f, 0.7f, 2, C("#37474F"))
        // pranchetas inclinadas
        val pv = max(4.6f, d * 0.36f); var pu = L + 1.8f
        while (pu < R - 1.8f) { if (abs(pu - c) > 1.3f) { s.box(pu, FL, pv, 0.06f, 0.85f, 0.06f, C("#424242"), Mt.METAL); s.box(pu - 0.6f, FL, pv, 0.05f, 0.05f, 0.9f, C("#424242"), Mt.METAL); s.box(pu + 0.6f, FL, pv, 0.05f, 0.05f, 0.9f, C("#424242"), Mt.METAL)
                for (k in 0..9) s.box(pu, FL + 0.85f + k * 0.022f, pv - 0.45f + k * 0.1f, 1.3f, 0.03f, 0.11f, C("#FAFAFA"))
                for (k in 1..8) s.box(pu, FL + 0.88f + k * 0.022f, pv - 0.45f + k * 0.1f, 1.0f, 0.003f, 0.1f, C("#BBDEFB"), Mt.PLAIN, 1f, false)
                s.box(pu - 0.3f, FL + 0.9f, pv - 0.4f, 0.6f, 0.03f, 0.03f, C("#37474F"), Mt.METAL); s.deskLamp(pu + 0.55f, pv + 0.4f, FL + 1.08f); s.solid(pu - 0.65f, pv - 0.5f, pu + 0.65f, pv + 0.5f); s.stool(pu, pv - 0.8f, C("#37474F"), 0.7f) }
            pu += 2.4f }
        val sv2 = pv + 2.6f
        if (sv2 < d - 4f) { var su = L + 1.8f; while (su < R - 1.5f) { if (abs(su - c) > 1.4f) s.station(su, sv2, 1, 1.6f, 2, C("#FAFAFA"), C("#F9A825"), C("#263238")); su += 2.0f } }
        // fundo: mesa de reunião, plotter, armário de capacetes e plantas
        s.table(c + 2.0f, d - 2.0f, 2.6f, 1.2f, C("#ECEFF1"), C("#424242")); for (k in 0..2) { s.chairO(c + 1.2f + k * 0.8f, d - 2.85f, 1, C("#F9A825")); s.chairO(c + 1.2f + k * 0.8f, d - 1.15f, 0, C("#F9A825")) }
        s.box(c + 2.0f, FL + 0.75f, d - 2.0f, 1.0f, 0.005f, 0.7f, C("#BBDEFB"))
        s.box(L + 1.2f, FL, d - 0.5f, 1.8f, 1.0f, 0.6f, C("#37474F"), Mt.METAL); s.box(L + 1.2f, FL + 1.0f, d - 0.5f, 1.8f, 0.15f, 0.65f, C("#263238"), Mt.METAL); s.box(L + 1.2f, FL + 0.9f, d - 0.82f, 1.4f, 0.02f, 0.4f, C("#E3F2FD")); s.solid(L + 0.3f, d - 0.85f, L + 2.1f, d - 0.15f)
        for (k in 0..3) { s.oc(c - 2.2f + k * 0.45f, d - 0.2f, 0, 0f, FL + 1.6f, 0f, 0.16f, 0.16f, C(if (k % 2 == 0) "#FDD835" else "#FAFAFA"), Mt.PLAIN, 10, 0.1f); s.box(c - 2.2f + k * 0.45f, FL + 1.0f, d - 0.15f, 0.36f, 0.55f, 0.06f, C("#FF6F00"), Mt.FABRIC); s.box(c - 2.2f + k * 0.45f, FL + 1.25f, d - 0.12f, 0.37f, 0.05f, 0.07f, C("#E0E0E0"), Mt.PLAIN, 1f, false) }
        s.box(c - 1.5f, FL + 1.55f, d - 0.06f, 2.0f, 0.04f, 0.06f, C("#616161"), Mt.METAL)
        s.board(L + 0.03f, d * 0.75f, 2, 2.2f, 0, FL + 1.0f, 1.1f); s.art(R - 0.03f, d * 0.6f, 3, 1.4f, 1.0f, FL + 1.1f, C("#1565C0"))
        s.fileCab(R - 0.35f, d - 0.9f, 2, 2, C("#FFB300"))
    }

    /** Empresa de tecnologia: recepção neon, lounge com pufes, ilhas com dois monitores, sala de vídeo, mesa de pingue-pongue, cozinha e paredes coloridas. */
    private fun tech(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth
        s.reception(L + 3.0f, 2.2f, 1, 2.8f, C("#0D1B2A"), C("#FAFAFA"), C("#00E5FF"), 1)
        s.box(L + 3.0f, FL + 1.7f, 4.2f, 2.8f, 0.5f, 0.06f, C("#0D1B2A")); s.box(L + 3.0f, FL + 1.75f, 4.17f, 2.4f, 0.36f, 0.01f, C("#00E5FF"), Mt.PLAIN, 1f, false); s.solid(L + 1.6f, 4.15f, L + 4.4f, 4.25f)
        // lounge na direita com pufes e tapete
        s.rug(R - 2.4f, 2.4f, 3.6f, 3.2f, C("#7E57C2"), C("#311B92"))
        s.sofa(R - 2.4f, 0.8f, 1, 2.6f, C("#26C6DA"), C("#FFEB3B"))
        for (k in 0..2) { val pu = R - 3.6f + k * 1.2f; s.oc(pu, 3.4f, 0, 0f, FL, 0f, 0.4f, 0.45f, C(arrayOf("#FF7043", "#66BB6A", "#42A5F5")[k]), Mt.FABRIC, 12, 0.3f); s.solid(pu - 0.4f, 3.0f, pu + 0.4f, 3.8f) }
        s.tableRound(R - 2.4f, 2.2f, 0.4f, C("#FAFAFA"), 0.42f); s.tv(R - 0.03f, 2.4f, 3, 1.6f, FL + 1.2f, C("#7C4DFF"))
        // ilhas: 2 fileiras de mesas, frente a frente, dois monitores
        val iv = max(6.6f, d * 0.42f); var iu = L + 1.7f
        while (iu < R - 1.6f) { if (abs(iu - c) > 1.5f) for (j in 0 until 2) { val vv = iv + j * 3.2f; if (vv > d - 3.5f) break
                s.station(iu, vv, 0, 1.6f, 2, C("#FAFAFA"), C("#212121"), C("#2E3440")); s.station(iu, vv - 0.77f, 1, 1.6f, 2, C("#FAFAFA"), C("#212121"), C("#2E3440")) }
            iu += 1.75f; if (abs(iu - c) < 1.5f) iu = c + 1.6f }
        // fundo: pingue-pongue, cozinha, cabines de foco
        val tt = c - 0.5f
        s.table(tt, d - 1.8f, 2.7f, 1.5f, C("#1565C0"), C("#212121"), 0.76f, Mt.PLAIN); s.box(tt, FL + 0.76f, d - 1.8f, 0.03f, 0.15f, 1.55f, C("#FAFAFA")); s.box(tt, FL + 0.761f, d - 1.8f, 2.7f, 0.003f, 0.02f, C("#FAFAFA"))
        s.counter(R - 2.0f, d - 0.35f, 1, 3.0f, 0.6f, C("#263238"), C("#FAFAFA")); s.coffeeMachine(R - 2.8f, d - 0.35f, 1); s.coffeeMachine(R - 2.3f, d - 0.35f, 1); s.homeFridge(R - 0.45f, d - 1.4f, 2, C("#263238"))
        for (k in 0..2) s.stool(R - 3.0f + k * 0.8f, d - 1.2f, C("#00BCD4"), 0.75f)
        s.vending(L + 0.5f, d - 1.0f, 3, C("#6200EA")); s.plant(L + 0.5f, d - 2.4f, 2, C("#263238"))
        for (k in 0..3) s.pendant(L + 2f + k * (s.w - 4f) / 3, iv + 1.2f, 1.0f, C("#00BCD4"))
        s.box(L + 0.035f, FL + 0.1f, d * 0.6f, 0.02f, s.h - 0.4f, 3.0f, C("#FF7043")); s.box(R - 0.035f, FL + 0.1f, d * 0.6f, 0.02f, s.h - 0.4f, 3.0f, C("#26C6DA"))
    }

    // ================================================================ NÍVEL 4

    /** Sede corporativa: saguão de mármore com logotipo, poltronas de couro, bar, diretoria com mesa enorme, telão e escritório do presidente. */
    private fun sede(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth; val wv = d * 0.45f
        s.box(c, FL + 0.002f, wv / 2, s.w - 0.1f, 0.004f, wv, C("#F5F5F5"), Mt.STONE, 0.4f)
        s.reception(c - 3.6f, 3.2f, 1, 3.6f, C("#111111"), C("#E8C26E"), C("#E8C26E"), 1)
        s.box(c, FL + 1.0f, wv - 0.08f, 5.0f, 2.2f, 0.04f, C("#1A1A1A")); s.box(c, FL + 1.6f, wv - 0.11f, 3.0f, 1.0f, 0.01f, C("#E8C26E"), Mt.METAL)
        for (sd in floatArrayOf(-1f, 1f)) { s.sofa(c + sd * 4.2f, wv - 1.0f, 0, 2.4f, C("#2B2B2B"), C("#E8C26E")); s.plant(c + sd * 2.8f, wv - 0.6f, 3, C("#212121")) }
        s.sofa(R - 0.5f, 2.2f, 2, 2.2f, C("#4E342E")); s.table(R - 1.8f, 2.2f, 0.7f, 1.2f, C("#111111"), C("#E8C26E"), 0.42f); s.floorLamp(R - 0.5f, 0.6f); s.rug(R - 1.8f, 2.2f, 2.6f, 2.8f, C("#BCAAA4"), C("#4E342E"))
        s.art(L + 0.03f, 2.2f, 2, 1.6f, 1.0f, FL + 1.1f, C("#C9A227"))
        s.wallTo(wv, L, R, c, C("#ECEFF1"), true)
        // diretoria (meio) e presidência (direita, sala de vidro)
        val pu0 = R - min(6f, s.w * 0.32f)
        s.wallAlong(pu0, wv, d, (wv + d) / 2, C("#ECEFF1"), true)
        val tu = (L + pu0) / 2; val tv = (wv + d) / 2 + 0.2f; val tl = min(6.4f, pu0 - L - 2.4f)
        s.table(tu, tv, tl, 1.6f, C("#3E2723"), C("#111111")); val nch = max(2, (tl / 1.05f).toInt())
        for (k in 0 until nch) { val cu = tu - tl / 2 + 0.5f + k * (tl - 1f) / max(1, nch - 1); s.chairO(cu, tv - 1.1f, 1, C("#111111")); s.chairO(cu, tv + 1.1f, 0, C("#111111")) }
        s.chairO(tu - tl / 2 - 0.6f, tv, 3, C("#4E342E"))
        s.tv(L + 0.03f, tv, 2, 2.4f, FL + 1.0f, C("#1565C0")); s.counter(tu, d - 0.35f, 1, 2.6f, 0.6f, C("#3E2723"), C("#111111")); for (k in 0..4) s.oc(tu - 1.0f + k * 0.5f, d - 0.3f, 0, 0f, FL + 0.92f, 0f, 0.05f, 0.3f, C(arrayOf("#1B5E20", "#5D4037", "#E8C26E", "#B71C1C", "#ECEFF1")[k]), Mt.GLASS, 8)
        val ou = (pu0 + R) / 2
        s.desk(ou, d - 2.2f, 0, 2.4f, 1.0f, C("#111111"), C("#E8C26E")); s.chairO(ou, d - 1.4f, 0, C("#4E342E")); s.monitor(ou - 0.4f, d - 2.3f, 0, FL + 0.76f, 0.7f); s.deskLamp(ou + 0.9f, d - 2.4f, FL + 0.76f, C("#E8C26E"))
        s.chairW(ou - 0.6f, d - 3.3f, 1, C("#111111"), C("#4E342E")); s.chairW(ou + 0.6f, d - 3.3f, 1, C("#111111"), C("#4E342E"))
        s.bookcase(ou, d - 0.22f, 1, min(4f, R - pu0 - 1f), C("#111111"), 2.4f, 0.6f); s.plant(R - 0.5f, wv + 0.6f, 1, C("#212121"))
        s.oc(pu0 + 0.7f, wv + 0.9f, 0, 0f, FL, 0f, 0.25f, 0.9f, C("#ECEFF1"), Mt.STONE, 10); s.ball(pu0 + 0.7f, FL + 1.12f, wv + 0.9f, 0.2f, C("#1E3A6E"))
        for (k in 0..2) s.pendant(tu - tl / 3 + k * tl / 3, tv, 1.0f, C("#E8C26E"))
    }

    /** Prefeitura: saguão com colunas e brasão, balcões de serviço, bandeiras, estátua, mural da cidade, gabinete do prefeito e sala de reuniões. */
    private fun prefeitura(s: JobSpace) {
        val L = s.x0; val R = s.x1; val c = s.cx; val d = s.depth; val wv = d * 0.62f
        s.box(c, FL + 0.002f, wv / 2, s.w - 0.1f, 0.004f, wv, C("#ECE3D0"), Mt.STONE, 0.5f)
        for (k in 0..5) { val pu = L + 2f + k * (s.w - 4f) / 5; if (abs(pu - c) < 1.6f) continue; s.oc(pu, 2.6f, 0, 0f, FL, 0f, 0.35f, s.h, C("#F1E9D8"), Mt.STONE, 14); s.box(pu, FL, 2.6f, 0.85f, 0.2f, 0.85f, C("#D8CCB4"), Mt.STONE); s.solid(pu - 0.42f, 2.18f, pu + 0.42f, 3.02f) }
        // balcões de atendimento numerados nas laterais
        for (sd in floatArrayOf(-1f, 1f)) { val bu = c + sd * (s.w / 2 - 3.2f); s.reception(bu, 5.5f, 1, 3.6f, C("#1B3A5C"), C("#ECEFF1"), C("#C9A227"), 2)
            s.box(bu, FL + 2.4f, 6.3f, 1.4f, 0.4f, 0.05f, C("#1B3A5C")); s.box(bu, FL + 2.45f, 6.27f, 1.2f, 0.3f, 0.01f, C("#FFF59D"), Mt.PLAIN, 1f, false)
            s.waitRow(c + sd * (s.w / 2 - 3.2f), 3.9f, 1, 4, C("#1B3A5C")) }
        s.rug(c, (wv - 3.4f) / 2 + 0.2f, 1.8f, wv - 3.6f, C("#8E2424"), C("#C9A227"))
        // estátua do fundador no centro do saguão (depois do corredor)
        val sv = wv - 2.2f
        s.box(c, FL, sv, 2.4f, 0.5f, 2.4f, C("#C9A227"), Mt.STONE); s.box(c, FL + 0.5f, sv, 1.0f, 1.2f, 1.0f, C("#E0D8C8"), Mt.STONE, 0.6f); s.oc(c, sv, 0, 0f, FL + 1.7f, 0f, 0.25f, 1.0f, C("#8D6E63"), Mt.METAL, 10, 0.2f); s.ball(c, FL + 2.85f, sv, 0.2f, C("#8D6E63")); s.solid(c - 1.2f, sv - 1.2f, c + 1.2f, sv + 1.2f)
        for (k in 0..3) s.plant(c + (if (k < 2) -1.6f else 1.6f), sv + (if (k % 2 == 0) -1.6f else 1.6f), 0, C("#C9A227"))
        s.board(L + 0.03f, wv / 2 + 1.5f, 2, 2.6f, 2, FL + 1.0f, 1.2f); s.art(R - 0.03f, wv / 2 + 1.5f, 3, 2.4f, 1.3f, FL + 1.0f, C("#C9A227"))
        s.wallTo(wv, L, R, c, C("#F1E9D8"))
        // gabinete do prefeito
        val gu0 = c - 1.0f
        s.wallAlong(gu0, wv, d, (wv + d) / 2, C("#F1E9D8"))
        val ou = (gu0 + R) / 2
        s.rug(ou, d - 2.2f, 4.0f, 3.0f, C("#8E2424"), C("#C9A227"))
        s.desk(ou, d - 2.0f, 0, 2.6f, 1.0f, C("#3E2723"), C("#C9A227")); s.chairO(ou, d - 1.2f, 0, C("#5D4037")); s.monitor(ou - 0.5f, d - 2.1f, 0); s.papers(ou + 0.4f, d - 2.0f, 0); s.phone(ou + 1.0f, d - 2.2f, 0)
        s.chairW(ou - 0.6f, d - 3.1f, 1, C("#3E2723"), C("#8E2424")); s.chairW(ou + 0.6f, d - 3.1f, 1, C("#3E2723"), C("#8E2424"))
        for (sd in floatArrayOf(-1f, 1f)) { s.oc(ou + sd * 1.8f, d - 0.5f, 0, 0f, FL, 0f, 0.03f, 2.6f, C("#C9A227"), Mt.METAL, 6); s.box(ou + sd * 1.8f + 0.35f, FL + 1.8f, d - 0.5f, 0.7f, 0.55f, 0.02f, C(if (sd < 0) "#1B5E20" else "#0D47A1"), Mt.FABRIC) }
        s.box(ou, FL + 1.6f, d - 0.05f, 1.0f, 1.2f, 0.04f, C("#C9A227"), Mt.METAL); s.box(ou, FL + 1.7f, d - 0.08f, 0.8f, 1.0f, 0.01f, C("#1B3A5C"))
        s.sofa(R - 0.5f, wv + 2.0f, 2, 2.2f, C("#1B3A5C")); s.bookcase(gu0 + 0.25f, d - 1.8f, 3, 2.4f, C("#4E342E"), 2.3f)
        // sala de reuniões do secretariado
        val mu = (L + gu0) / 2; val mv = (wv + d) / 2
        s.table(mu, mv, min(4.4f, gu0 - L - 2f), 1.4f, C("#5D4037")); for (k in 0 until 4) { val cu = mu - 1.4f + k * 0.95f; s.chairO(cu, mv - 1.05f, 1, C("#1B3A5C")); s.chairO(cu, mv + 1.05f, 0, C("#1B3A5C")) }
        s.tv(L + 0.03f, mv, 2, 1.5f, FL + 1.2f); s.cooler(L + 0.4f, d - 0.5f)
    }
}
