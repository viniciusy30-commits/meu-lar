package com.vinicius.meular

import android.opengl.Matrix
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

/**
 * Etapa 128: portas de verdade em todas as construções, cada tipo de lugar com a sua:
 * casa (almofadada pintada, rústica de tábuas, moderna com vidro, pivotante de ripas, de praia com veneziana),
 * comércio (vidro com alumínio, madeira com vidro e sininho, dupla de restaurante, shoji com noren, porta de aço de enrolar),
 * automáticas de correr (mercado, hospital, farmácia, shopping), giratórias (banco, câmbio, hotel),
 * e as de serviço público (polícia, bombeiros, escola) e o portal da igreja.
 *
 * O batente, a soleira e os acessórios fixos entram na malha da cidade; as folhas são malhas pequenas
 * desenhadas à parte, que abrem sozinhas quando o jogador chega perto (as automáticas também para quem passa na calçada).
 *
 * Coordenadas locais da porta: origem no centro do vão, no piso; x ao longo da parede; +z = para fora; y para cima.
 */
object Doors {
    // casas
    const val PANEL = 0; const val RUSTIC = 1; const val HGLASS = 2; const val PIVOT = 3; const val BEACH = 4
    // comércio e serviços
    const val SLIDE = 10; const val REV_STEEL = 11; const val REV_BRASS = 12; const val ALU = 13; const val ALU2 = 14
    const val WOODG = 15; const val WOOD2 = 16; const val SHOJI = 17; const val SHUTTER = 18
    const val POLICE = 19; const val FIRE = 20; const val SCHOOL = 21; const val LOBBY = 22; const val CHURCH = 23

    const val K_SWING = 0; const val K_SLIDE = 1; const val K_SPIN = 2

    /** Folha: malha (local, a partir da dobradiça/origem), como se move, onde fica a dobradiça e para que lado abre. */
    class Leaf(val mesh: Mesh, val kind: Int, val px: Float, val dir: Float, val travel: Float, val pz: Float = 0f, val ang: Float = 92f)

    /** quantos pontos da área varrida pela folha (até [ang] graus, para dentro) caem em móveis/paredes */
    private fun sweep(d: City.Door, px: Float, dir: Float, lw: Float, ang: Float): Int {
        var hit = 0
        var a = 8f
        while (a <= ang + 0.1f) {
            val ar = Math.toRadians(a.toDouble()).toFloat()
            for (ri in 1..6) {
                val r = lw * ri / 6f
                val lx = px + dir * r * cos(ar); val lz = -r * sin(ar) - 0.22f
                if (lz > -0.3f) continue
                if (City.blocked(d.x + d.fz * lx, d.z + d.fz * lz)) hit++
            }
            a += 8f
        }
        return hit
    }

    /** maior abertura (graus) sem a folha bater em nada lá dentro */
    private fun maxAng(d: City.Door, px: Float, dir: Float, lw: Float, want: Float): Float {
        var a = want
        while (a > 40f && sweep(d, px, dir, lw, a) > 0) a -= 8f
        return a
    }

    private const val T = 0.045f            // espessura da folha
    private const val JAMB = 0.04f          // batente de cada lado

    fun automatic(style: Int) = style == SLIDE || style == REV_STEEL || style == REV_BRASS
    fun revolving(style: Int) = style == REV_STEEL || style == REV_BRASS
    private fun double(style: Int) = style == ALU2 || style == WOOD2 || style == POLICE || style == FIRE || style == SCHOOL || style == LOBBY || style == CHURCH
    private fun shopPlaque(style: Int) = style == ALU || style == WOODG || style == SHUTTER
    /** raio do tambor da porta giratória */
    fun drumR(w: Float) = w / 2 + 0.22f

    /** Estilo e cores da porta conforme o lugar (o nome da construção). Devolve (estilo, cor, cor 2). */
    fun pick(name: String, rng: City.Rng): IntArray {
        val n = name.uppercase()
        fun r(st: Int, a: String, b: String) = intArrayOf(st, C(a), C(b))
        return when {
            n == "CASA DE PRAIA" -> r(BEACH, rng.pick(arrayOf("#2A9D8F", "#F7F4EC", "#F4D35E", "#5FA8D3", "#E76F51", "#8FC1A9")), "#FFFFFF")
            n == "MANSÃO" -> r(PIVOT, rng.pick(arrayOf("#5C3D2E", "#3E2C23", "#8C6A4F", "#2F2A26")), "#C9CED3")
            n == "CHALÉ" -> r(RUSTIC, rng.pick(arrayOf("#8B5E3C", "#A47551", "#6E4A30")), "#1E1E1E")
            n == "CASA MODERNA" -> r(HGLASS, rng.pick(arrayOf("#3E3E3E", "#6B4A3A", "#2F3E46", "#8C6A4F", "#B08B64")), "#C9CED3")
            n == "CASA" || n == "SOBRADO" -> r(if (rng.chance(0.25f)) HGLASS else PANEL, rng.pick(arrayOf("#6B3E26", "#2F5D50", "#1F3A5F", "#8C2F39", "#3E3E3E", "#B5835A", "#F4F1EA", "#5B7F95")), "#C9A227")
            n == "BANCO" || n == "CASA DE CÂMBIO" -> r(REV_STEEL, "#AEB4BA", "#3E4A56")
            n == "HOTEL" -> r(REV_BRASS, "#B08D57", "#2B2B2B")
            n == "SUPERMERCADO" -> r(SLIDE, "#B9BEC4", "#D62828")
            n == "SHOPPING" -> r(SLIDE, "#2F3338", "#C9A227")
            n == "HOSPITAL" || n == "PRONTO-SOCORRO" || n == "CLÍNICA" -> r(SLIDE, "#E9EEF2", "#1F6FD1")
            n == "FARMÁCIA" -> r(SLIDE, "#1E9E5A", "#FFFFFF")
            n == "CONVENIÊNCIA" -> r(SLIDE, "#0F7A3D", "#FFE14D")
            n == "ÓTICA" -> r(ALU, "#1A1A1A", "#C9CED3")
            n == "ELETRÔNICOS" -> r(ALU, "#3C4148", "#1565C0")
            n == "PET SHOP" -> r(ALU, "#25A8E0", "#FFFFFF")
            n == "SALÃO DE BELEZA" -> r(ALU, "#C9A0A0", "#F2D7C9")
            n == "SORVETERIA" -> r(ALU, "#F48FB1", "#FFFFFF")
            n == "MODA" -> r(ALU, "#111111", "#C9A227")
            n == "ACADEMIA" -> r(ALU2, "#151515", "#FF8A00")
            n == "PADARIA" -> r(WOODG, "#A8743F", "#C9A227")
            n == "CAFÉ" -> r(WOODG, "#4A2C1A", "#C9A227")
            n == "LIVRARIA" -> r(WOODG, "#6B1F24", "#C9A227")
            n == "FLORICULTURA" -> r(WOODG, "#3E7D3A", "#E8E8E8")
            n == "BARBEARIA" -> r(WOODG, "#2B2B2B", "#C9A227")
            n == "PIZZARIA" -> r(WOODG, "#7A4A2A", "#1A1A1A")
            n == "RESTAURANTE" -> r(WOOD2, "#5A2E1E", "#C9A227")
            n == "SUSHI" -> r(SHOJI, "#D8B98A", "#1F2A44")
            n == "MERCADINHO" -> r(SHUTTER, "#2B2B2B", "#9EA4AA")
            n == "PAPELARIA" -> r(SHUTTER, "#2B2B2B", "#1565C0")
            n == "LANCHONETE" -> r(SHUTTER, "#2B2B2B", "#C0392B")
            n == "AÇAÍ" -> r(SHUTTER, "#4A148C", "#9EA4AA")
            n == "HAMBÚRGUER" -> r(SHUTTER, "#1A1A1A", "#FF6F00")
            n == "POLÍCIA" -> r(POLICE, "#1E3A6E", "#D0D4D8")
            n == "BOMBEIROS" -> r(FIRE, "#C62828", "#D0D4D8")
            n == "ESCOLA" -> r(SCHOOL, "#2E6B30", "#F2C14E")
            n.startsWith("IGREJA") -> r(CHURCH, "#4A2C1E", "#2B2B2B")
            n == "RESIDENCIAL" || n == "CONDOMÍNIO" || n == "ESCRITÓRIOS" || n == "PRÉDIO" ->
                if (rng.chance(0.5f)) r(LOBBY, "#3B3026", "#C9A227") else r(LOBBY, "#1E1E1E", "#C9CED3")
            else -> r(ALU, "#9EA4AA", "#C9CED3")
        }
    }

    // ------------------------------------------------------------------ peças fixas (malha da cidade)

    /** Batente, soleira e acessórios fixos, em coordenadas do mundo. [th] = espessura da parede. */
    fun statics(b: MB, d: City.Door, th: Float) {
        val f = d.fz; val w = d.w; val h = d.h; val y = d.y
        fun bx(x0: Float, x1: Float, y0: Float, y1: Float, z0: Float, z1: Float, c: Int, lit: Boolean = true) {
            val wx0 = d.x + f * x0; val wx1 = d.x + f * x1; val wz0 = d.z + f * z0; val wz1 = d.z + f * z1
            b.box((wx0 + wx1) / 2, y + (y0 + y1) / 2, (wz0 + wz1) / 2, abs(wx1 - wx0), abs(y1 - y0), abs(wz1 - wz0), c, lit)
        }
        fun cy(x: Float, y0: Float, z: Float, r: Float, hh: Float, c: Int, seg: Int = 10) = b.cyl(d.x + f * x, y + y0, d.z + f * z, r, r, hh, c, true, seg)
        val st = d.style
        val wood = st == PANEL || st == RUSTIC || st == HGLASS || st == PIVOT || st == BEACH || st == WOODG || st == WOOD2 || st == SHOJI || st == CHURCH
        val jc = if (wood) shade(d.col, -10) else if (st == SHUTTER) C("#3A3F45") else d.col
        // soleira (cobre a junta piso × calçada) e batentes
        b.m(Mt.STONE, 0.6f); bx(-w / 2 - 0.04f, w / 2 + 0.04f, -0.004f, 0.012f, -th / 2 - 0.02f, th / 2 + 0.05f, C(if (st == CHURCH) "#CFC6B6" else "#D9D5CE"))
        b.m(if (wood) Mt.WOOD else Mt.METAL, 1f)
        if (!revolving(st)) {
            bx(-w / 2, -w / 2 + JAMB, 0f, h, -th / 2 - 0.005f, th / 2 + 0.005f, jc); bx(w / 2 - JAMB, w / 2, 0f, h, -th / 2 - 0.005f, th / 2 + 0.005f, jc)
            bx(-w / 2, w / 2, h - JAMB, h, -th / 2 - 0.005f, th / 2 + 0.005f, jc)
            // batente com rebaixo (onde a folha encosta)
            bx(-w / 2 + JAMB, -w / 2 + JAMB + 0.015f, 0f, h - JAMB, T / 2 + 0.002f, T / 2 + 0.03f, shade(jc, -8)); bx(w / 2 - JAMB - 0.015f, w / 2 - JAMB, 0f, h - JAMB, T / 2 + 0.002f, T / 2 + 0.03f, shade(jc, -8))
        }
        when (st) {
            PANEL, HGLASS, PIVOT, BEACH, RUSTIC -> {
                // campainha, número, capacho
                b.m(Mt.PLAIN); bx(w / 2 + 0.2f, w / 2 + 0.28f, 1.24f, 1.36f, th / 2, th / 2 + 0.02f, C("#EDEDED")); bx(w / 2 + 0.225f, w / 2 + 0.255f, 1.285f, 1.315f, th / 2 + 0.02f, th / 2 + 0.03f, C("#FFD54F"), false)
                b.m(Mt.METAL, 1f); bx(w / 2 + 0.16f, w / 2 + 0.36f, 1.55f, 1.7f, th / 2, th / 2 + 0.012f, if (st == RUSTIC) C("#2B2B2B") else C("#C9A227"))
                b.m(Mt.RUG, 0.5f); bx(-0.42f, 0.42f, 0.012f, 0.026f, th / 2 + 0.12f, th / 2 + 0.62f, C(if (st == BEACH) "#C8A26B" else "#4E3B2C"))
                if (st == PIVOT) { b.m(Mt.PLAIN); bx(-w / 2 - 0.05f, w / 2 + 0.05f, h + 0.02f, h + 0.05f, th / 2, th / 2 + 0.03f, C("#FFF1C9"), false) }   // fita de luz em cima
            }
            SLIDE -> {
                // caixa do mecanismo com sensor e luz verde
                b.m(Mt.METAL, 1f); bx(-w / 2 - 0.12f, w / 2 + 0.12f, h, h + 0.24f, th / 2, th / 2 + 0.17f, d.col)
                b.m(Mt.PLAIN); bx(-0.09f, 0.09f, h + 0.02f, h + 0.08f, th / 2 + 0.17f, th / 2 + 0.19f, C("#1C1C1C")); bx(0.12f, 0.14f, h + 0.04f, h + 0.06f, th / 2 + 0.17f, th / 2 + 0.195f, C("#53FF7A"), false)
                bx(-w / 2 - 0.12f, w / 2 + 0.12f, h + 0.2f, h + 0.215f, th / 2 + 0.17f, th / 2 + 0.172f, d.col2, false)
                b.m(Mt.METAL, 1f); bx(-w / 2, w / 2, 0.012f, 0.02f, -0.03f, 0.03f, C("#8E959C"))   // trilho no piso
            }
            REV_STEEL, REV_BRASS -> {
                val R = drumR(w); val n = 14
                b.m(Mt.METAL, 1f)
                cy(0f, h, 0f, R + 0.06f, 0.3f, d.col, 24)                       // tampa do tambor
                b.m(Mt.PLAIN); b.cyl(d.x, y + h - 0.004f, d.z, R - 0.02f, R - 0.02f, 0.006f, C("#FFF4D6"), false, 20)   // luz embaixo da tampa
                b.m(Mt.STONE, 0.5f); cy(0f, -0.002f, 0f, R + 0.04f, 0.016f, C(if (st == REV_BRASS) "#3B2F2A" else "#4A4F55"), 24)
                // paredes curvas de vidro nas laterais (com perfis em cima/embaixo e colunas nas pontas)
                for (side in floatArrayOf(1f, -1f)) {
                    val a0 = -0.95f; val a1 = 0.95f
                    for (k in 0 until n) {
                        val t0 = a0 + (a1 - a0) * k / n; val t1 = a0 + (a1 - a0) * (k + 1) / n
                        val x0 = side * R * cos(t0); val z0 = R * sin(t0); val x1 = side * R * cos(t1); val z1 = R * sin(t1)
                        val wx0 = d.x + f * x0; val wz0 = d.z + f * z0; val wx1 = d.x + f * x1; val wz1 = d.z + f * z1
                        b.m(Mt.GLASS); b.al = 0.28f
                        CityGeo.q(b, CityGeo.P(wx0, y + 0.08f, wz0) + CityGeo.P(wx1, y + 0.08f, wz1) + CityGeo.P(wx1, y + h - 0.02f, wz1) + CityGeo.P(wx0, y + h - 0.02f, wz0), C("#CFE7F0"))
                        b.al = 1f
                        // perfis curvos (faixas de metal em cima e embaixo)
                        b.m(Mt.METAL, 1f)
                        for (yy in floatArrayOf(0f, h - 0.1f)) {
                            for (rr in floatArrayOf(R - 0.02f, R + 0.02f)) {
                                val ax0 = d.x + f * side * rr * cos(t0); val az0 = d.z + f * rr * sin(t0); val ax1 = d.x + f * side * rr * cos(t1); val az1 = d.z + f * rr * sin(t1)
                                CityGeo.q(b, CityGeo.P(ax0, y + yy, az0) + CityGeo.P(ax1, y + yy, az1) + CityGeo.P(ax1, y + yy + 0.1f, az1) + CityGeo.P(ax0, y + yy + 0.1f, az0), d.col)
                            }
                        }
                    }
                    for (a in floatArrayOf(a0, a1)) cy(side * R * cos(a), 0f, R * sin(a), 0.035f, h, d.col, 8)
                }
                // escudo de "detector de metais" (banco) / placa dourada (hotel)
                b.m(Mt.PLAIN)
                if (st == REV_STEEL) { bx(-0.25f, 0.25f, h + 0.08f, h + 0.22f, R + 0.06f, R + 0.075f, C("#3E4A56")); bx(-0.2f, 0.2f, h + 0.13f, h + 0.17f, R + 0.075f, R + 0.08f, C("#F2C14E"), false) }
                else { b.m(Mt.METAL, 1f); bx(-0.35f, 0.35f, h + 0.09f, h + 0.21f, R + 0.06f, R + 0.075f, C("#D4AF37")) }
            }
            SHOJI -> {
                // noren: cortina de tecido dividida em 3, num bastão de bambu, por fora
                b.m(Mt.WOOD, 1f); bx(-w / 2 - 0.08f, w / 2 + 0.08f, h - 0.04f, h, th / 2 + 0.04f, th / 2 + 0.08f, C("#C9B27C"))
                b.m(Mt.FABRIC, 1f)
                val sw = (w - 0.06f) / 3
                for (k in 0 until 3) { val x0 = -w / 2 + 0.03f + k * sw; bx(x0 + 0.012f, x0 + sw - 0.012f, h - 0.62f, h - 0.04f, th / 2 + 0.055f, th / 2 + 0.065f, d.col2) }
                b.m(Mt.PLAIN); b.cyl(d.x, y + h - 0.42f, d.z + f * (th / 2 + 0.068f), 0.11f, 0.11f, 0.004f, C("#F5F0E6"), false, 14)
                bx(-0.05f, 0.05f, h - 0.37f, h - 0.33f, th / 2 + 0.066f, th / 2 + 0.07f, C("#B71C1C"), false)
                // lanterna de papel ao lado
                b.m(Mt.PLAIN); CityGeo.ball(b, d.x + f * (w / 2 + 0.38f), y + 2.0f, d.z + f * (th / 2 + 0.22f), 0.16f, C("#E53935"), 0.22f, 8)
                b.m(Mt.WOOD, 1f); bx(w / 2 + 0.36f, w / 2 + 0.4f, 2.22f, 2.4f, th / 2 + 0.2f, th / 2 + 0.24f, C("#2B2B2B"))
            }
            SHUTTER -> {
                // porta de aço de enrolar recolhida: caixa do rolo, guias e a última lâmina aparecendo
                b.m(Mt.METAL, 1f)
                bx(-w / 2 - 0.1f, w / 2 + 0.1f, h + 0.02f, h + 0.44f, th / 2, th / 2 + 0.36f, d.col2)
                bx(-w / 2 - 0.1f, w / 2 + 0.1f, h + 0.02f, h + 0.05f, th / 2 + 0.36f, th / 2 + 0.38f, shade(d.col2, -15))
                for (s in floatArrayOf(-1f, 1f)) bx(s * (w / 2 + 0.01f) - 0.035f, s * (w / 2 + 0.01f) + 0.035f, 0f, h + 0.05f, th / 2, th / 2 + 0.08f, C("#7D848B"))
                for (k in 0 until 6) bx(-w / 2 + 0.02f, w / 2 - 0.02f, h - 0.34f + k * 0.056f, h - 0.29f + k * 0.056f, th / 2 + 0.035f + (k % 2) * 0.006f, th / 2 + 0.05f + (k % 2) * 0.006f, shade(d.col2, if (k % 2 == 0) 6 else -6))
                bx(-w / 2 + 0.02f, w / 2 - 0.02f, h - 0.37f, h - 0.33f, th / 2 + 0.03f, th / 2 + 0.06f, C("#5A6168"))
                bx(-0.07f, 0.07f, h - 0.42f, h - 0.37f, th / 2 + 0.05f, th / 2 + 0.07f, C("#3A3F45"))   // puxador
                for (s in floatArrayOf(-1f, 1f)) bx(s * (w / 2 - 0.12f) - 0.02f, s * (w / 2 - 0.12f) + 0.02f, 0.02f, 0.1f, th / 2 + 0.02f, th / 2 + 0.06f, C("#8E959C"))   // argolas do cadeado no chão
            }
            WOODG -> {
                // sininho por dentro, em cima da porta
                b.m(Mt.METAL, 1f); bx(w / 2 - 0.2f, w / 2 - 0.12f, h - 0.1f, h - 0.06f, -th / 2 - 0.08f, -th / 2, C("#3A2A1A"))
                b.cyl(d.x + f * (w / 2 - 0.16f), y + h - 0.2f, d.z + f * (-th / 2 - 0.07f), 0.035f, 0.012f, 0.1f, C("#D4AF37"), true, 8)
            }
            WOOD2 -> {
                // arandelas dos dois lados
                for (s in floatArrayOf(-1f, 1f)) {
                    b.m(Mt.METAL, 1f); bx(s * (w / 2 + 0.3f) - 0.06f, s * (w / 2 + 0.3f) + 0.06f, 1.9f, 2.25f, th / 2, th / 2 + 0.03f, C("#1A1A1A"))
                    b.m(Mt.PLAIN); bx(s * (w / 2 + 0.3f) - 0.05f, s * (w / 2 + 0.3f) + 0.05f, 1.95f, 2.2f, th / 2 + 0.03f, th / 2 + 0.12f, C("#FFD99A"), false)
                }
            }
            LOBBY -> {
                // porteiro eletrônico com teclado e câmera
                b.m(Mt.METAL, 1f); bx(w / 2 + 0.32f, w / 2 + 0.52f, 1.18f, 1.52f, th / 2, th / 2 + 0.04f, C("#B8BEC4"))
                b.m(Mt.PLAIN); bx(w / 2 + 0.35f, w / 2 + 0.49f, 1.22f, 1.36f, th / 2 + 0.04f, th / 2 + 0.045f, C("#202428"))
                for (r in 0 until 3) for (c in 0 until 3) bx(w / 2 + 0.36f + c * 0.045f, w / 2 + 0.39f + c * 0.045f, 1.235f + r * 0.04f, 1.26f + r * 0.04f, th / 2 + 0.045f, th / 2 + 0.05f, C("#DADADA"), false)
                bx(w / 2 + 0.4f, w / 2 + 0.44f, 1.43f, 1.47f, th / 2 + 0.04f, th / 2 + 0.05f, C("#111111"))
                bx(w / 2 + 0.38f, w / 2 + 0.46f, 1.39f, 1.405f, th / 2 + 0.04f, th / 2 + 0.046f, C("#4FC3F7"), false)
            }
            POLICE -> {
                b.m(Mt.METAL, 1f); bx(-0.08f, 0.08f, h + 0.18f, h + 0.26f, th / 2, th / 2 + 0.14f, C("#E0E0E0"))
                CityGeo.ball(b, d.x, y + h + 0.16f, d.z + f * (th / 2 + 0.11f), 0.06f, C("#202020"), 0.05f, 6)   // câmera
                b.m(Mt.PLAIN); bx(-w / 2 - 0.3f, -w / 2 - 0.14f, 2.2f, 2.4f, th / 2, th / 2 + 0.08f, C("#3D7BFF"), false)
                bx(w / 2 + 0.14f, w / 2 + 0.3f, 2.2f, 2.4f, th / 2, th / 2 + 0.08f, C("#3D7BFF"), false)
            }
            FIRE -> {
                // faixa zebrada na soleira e luz vermelha de saída de viatura
                b.m(Mt.PLAIN)
                for (k in 0 until 8) bx(-w / 2 + k * w / 8, -w / 2 + (k + 0.5f) * w / 8, 0.012f, 0.016f, th / 2 + 0.02f, th / 2 + 0.2f, C("#F2C14E"), false)
                bx(-0.12f, 0.12f, h + 0.12f, h + 0.26f, th / 2, th / 2 + 0.1f, C("#FF3B30"), false)
            }
            SCHOOL -> {
                b.m(Mt.METAL, 1f); bx(-w / 2 - 0.25f, w / 2 + 0.25f, h + 0.05f, h + 0.12f, th / 2, th / 2 + 0.9f, C("#2E6B30"))   // marquisinha
                for (s in floatArrayOf(-1f, 1f)) cy(s * (w / 2 + 0.2f), 0f, th / 2 + 0.85f, 0.035f, h + 0.08f, C("#2E6B30"), 8)
                b.m(Mt.PLAIN); bx(-w / 2 - 0.25f, w / 2 + 0.25f, h + 0.03f, h + 0.05f, th / 2, th / 2 + 0.9f, C("#FFF4D6"), false)
            }
            CHURCH -> {
                // portal de pedra com pilastras e verga
                b.m(Mt.STONE, 0.5f)
                for (s in floatArrayOf(-1f, 1f)) { bx(s * (w / 2 + 0.22f) - 0.22f, s * (w / 2 + 0.22f) + 0.22f, 0f, h + 0.35f, th / 2, th / 2 + 0.14f, C("#D9CDB8")); bx(s * (w / 2 + 0.22f) - 0.27f, s * (w / 2 + 0.22f) + 0.27f, 0f, 0.3f, th / 2, th / 2 + 0.18f, C("#CBBEA6")) }
                bx(-w / 2 - 0.5f, w / 2 + 0.5f, h + 0.35f, h + 0.62f, th / 2, th / 2 + 0.2f, C("#D2C5AE"))
                bx(-0.32f, 0.32f, h + 0.62f, h + 0.85f, th / 2, th / 2 + 0.14f, C("#D9CDB8"))
                b.m(Mt.METAL, 1f); bx(-0.03f, 0.03f, h + 0.66f, h + 0.82f, th / 2 + 0.14f, th / 2 + 0.16f, C("#C9A227")); bx(-0.08f, 0.08f, h + 0.75f, h + 0.78f, th / 2 + 0.14f, th / 2 + 0.16f, C("#C9A227"))
            }
        }
    }

    // ------------------------------------------------------------------ folhas

    fun leaves(d: City.Door): List<Leaf> {
        val wi = d.w - 2 * JAMB
        val out = ArrayList<Leaf>()
        val want = if (d.style == CHURCH) 82f else 92f
        fun mk(kind: Int, px: Float, dir: Float, lw: Float, travel: Float, zoff: Float = 0f, idx: Int = 0) {
            val b = MB()
            leaf(b, d, lw, dir, zoff, idx)
            out.add(Leaf(b.toMesh(), kind, px, dir, travel, 0f, if (kind == K_SWING) maxAng(d, px, dir, lw, want) else 0f))
        }
        when {
            revolving(d.style) -> { val b = MB(); wings(b, d); out.add(Leaf(b.toMesh(), K_SPIN, 0f, 1f, 0f)) }
            d.style == SLIDE -> { mk(K_SLIDE, -wi / 2, 1f, wi / 2 + 0.02f, wi / 2, 0.012f, 0); mk(K_SLIDE, wi / 2, -1f, wi / 2 + 0.02f, wi / 2, -0.012f, 1) }
            d.style == SHOJI -> mk(K_SLIDE, -wi / 2, 1f, wi, wi * 0.97f)
            double(d.style) -> { mk(K_SWING, -wi / 2, 1f, wi / 2 - 0.006f, 0f, 0f, 0); mk(K_SWING, wi / 2, -1f, wi / 2 - 0.006f, 0f, 0f, 1) }
            else -> {
                // Etapa 128: dobradiça do lado em que a folha abre sem bater nos móveis
                // se dos dois lados bate (vitrine/balcão logo na entrada), vira porta de duas folhas, que varrem metade
                val lw = wi - 0.01f
                val sl = sweep(d, -wi / 2, 1f, lw, want); val sr = sweep(d, wi / 2, -1f, lw, want)
                if (sl > 0 && sr > 0) { mk(K_SWING, -wi / 2, 1f, wi / 2 - 0.006f, 0f, 0f, 0); mk(K_SWING, wi / 2, -1f, wi / 2 - 0.006f, 0f, 0f, 1) }
                else if (sl > sr) mk(K_SWING, wi / 2, -1f, lw, 0f) else mk(K_SWING, -wi / 2, 1f, lw, 0f)
            }
        }
        return out
    }

    /** Matriz da folha (porta [d], abertura 0..1 já suavizada em [k], giro [spin] em graus). */
    fun leafMatrix(out: FloatArray, d: City.Door, l: Leaf, k: Float) {
        Matrix.setIdentityM(out, 0)
        Matrix.translateM(out, 0, d.x, d.y, d.z)
        if (d.fz < 0f) Matrix.rotateM(out, 0, 180f, 0f, 1f, 0f)
        Matrix.translateM(out, 0, l.px, 0f, l.pz)
        when (l.kind) {
            K_SWING -> Matrix.rotateM(out, 0, l.dir * l.ang * k, 0f, 1f, 0f)
            K_SLIDE -> Matrix.translateM(out, 0, -l.dir * l.travel * k, 0f, 0f)
            K_SPIN -> Matrix.rotateM(out, 0, d.spin, 0f, 1f, 0f)
        }
    }

    /** Folha [lw] de largura, a partir da dobradiça, indo para [dir] (±1) no eixo x. */
    private fun leaf(b: MB, d: City.Door, lw: Float, dir: Float, zoff: Float, idx: Int) {
        val h = d.h - JAMB - 0.008f; val st = d.style; val c = d.col; val c2 = d.col2
        fun R(x0: Float, x1: Float, y0: Float, y1: Float, z0: Float, z1: Float, col: Int, lit: Boolean = true) {
            val a = dir * x0; val e = dir * x1
            b.box((a + e) / 2, (y0 + y1) / 2, (z0 + z1) / 2 + zoff, abs(e - a), abs(y1 - y0), abs(z1 - z0), col, lit)
        }
        /** dos dois lados da folha (por fora z>0 e por dentro z<0), [dz] = saliência */
        fun both(x0: Float, x1: Float, y0: Float, y1: Float, dz: Float, col: Int, lit: Boolean = true) {
            R(x0, x1, y0, y1, T / 2, T / 2 + dz, col, lit); R(x0, x1, y0, y1, -T / 2 - dz, -T / 2, col, lit)
        }
        fun glass(x0: Float, x1: Float, y0: Float, y1: Float, col: Int = C("#CFE8F0"), al: Float = 0.3f, th: Float = 0.012f) {
            b.m(Mt.GLASS); b.al = al; R(x0, x1, y0, y1, -th / 2, th / 2, col); b.al = 1f
        }
        /** maçaneta de alavanca dos dois lados (com espelho) */
        fun lever(x: Float, y: Float, col: Int) {
            b.m(Mt.METAL, 1f)
            for (s in floatArrayOf(1f, -1f)) {
                val z0 = s * T / 2; val zz = s * (T / 2 + 0.012f); val zh = s * (T / 2 + 0.055f)
                R(x - 0.025f, x + 0.025f, y - 0.09f, y + 0.09f, min(z0, zz), max(z0, zz), col)
                R(x - 0.012f, x + 0.012f, y - 0.012f, y + 0.012f, min(zz, zh), max(zz, zh), col)
                R(x - 0.14f, x + 0.012f, y - 0.012f, y + 0.012f, min(zh, zh + s * 0.022f), max(zh, zh + s * 0.022f), col)
                R(x - 0.008f, x + 0.008f, y - 0.06f, y - 0.035f, min(zz, zz + s * 0.002f), max(zz, zz + s * 0.002f), C("#1A1A1A"))
            }
        }
        /** puxador vertical (barra) dos dois lados */
        fun bar(x: Float, y0: Float, y1: Float, col: Int, r: Float = 0.014f, off: Float = 0.06f) {
            b.m(Mt.METAL, 1f)
            for (s in floatArrayOf(1f, -1f)) {
                val zb = s * (T / 2 + off)
                R(x - r, x + r, y0, y1, min(zb - r, zb + r), max(zb - r, zb + r), col)
                for (yy in floatArrayOf(y0 + 0.06f, y1 - 0.06f)) R(x - r * 0.7f, x + r * 0.7f, yy - r * 0.7f, yy + r * 0.7f, min(s * T / 2, zb), max(s * T / 2, zb), col)
            }
        }
        /** barra antipânico por dentro */
        fun push(x0: Float, x1: Float, y: Float, col: Int) {
            b.m(Mt.METAL, 1f)
            R(x0, x1, y - 0.03f, y + 0.03f, -T / 2 - 0.085f, -T / 2 - 0.045f, col)
            for (x in floatArrayOf(x0 + 0.04f, x1 - 0.04f)) R(x - 0.03f, x + 0.03f, y - 0.05f, y + 0.05f, -T / 2 - 0.05f, -T / 2, C("#3A3A3A"))
        }
        /** plaquinha ABERTO pendurada no vidro, por fora */
        fun plaque(x: Float) {
            b.m(Mt.PLAIN)
            R(x - 0.17f, x + 0.17f, 1.55f, 1.69f, T / 2 + 0.006f, T / 2 + 0.014f, C("#C62828"), false)
            R(x - 0.13f, x + 0.13f, 1.6f, 1.64f, T / 2 + 0.014f, T / 2 + 0.017f, C("#FFFFFF"), false)
            b.m(Mt.METAL, 1f); R(x - 0.003f, x + 0.003f, 1.69f, 1.82f, T / 2 + 0.006f, T / 2 + 0.01f, C("#555555"))
        }
        /** caixilho de alumínio: montantes, travessas e vidro */
        fun aluFrame(st0: Float, top: Float, kick: Float, col: Int, gcol: Int = C("#CFE8F0"), al: Float = 0.3f) {
            b.m(Mt.METAL, 1f)
            R(0.004f, st0, 0f, h, -T / 2, T / 2, col); R(lw - st0, lw - 0.004f, 0f, h, -T / 2, T / 2, col)
            R(st0, lw - st0, h - top, h, -T / 2, T / 2, col); R(st0, lw - st0, 0.004f, kick, -T / 2, T / 2, col)
            glass(st0, lw - st0, kick, h - top, gcol, al)
        }
        when (st) {
            PANEL -> {
                b.m(Mt.WOOD, 0.8f); R(0.004f, lw - 0.004f, 0.004f, h, -T / 2, T / 2, c)
                val rows = arrayOf(floatArrayOf(0.14f, 0.78f), floatArrayOf(0.92f, 1.42f), floatArrayOf(1.56f, h - 0.14f))
                for (rw in rows) for (cc in 0..1) {
                    val x0 = if (cc == 0) 0.11f else lw / 2 + 0.035f; val x1 = if (cc == 0) lw / 2 - 0.035f else lw - 0.11f
                    both(x0 - 0.02f, x1 + 0.02f, rw[0] - 0.02f, rw[1] + 0.02f, 0.006f, shade(c, -9))     // moldura rebaixada
                    both(x0 + 0.02f, x1 - 0.02f, rw[0] + 0.02f, rw[1] - 0.02f, 0.014f, shade(c, 6))      // almofada saltada
                }
                lever(lw - 0.09f, 1.02f, C("#C9A227"))
                b.m(Mt.METAL, 1f); R(lw / 2 - 0.012f, lw / 2 + 0.012f, 1.5f, 1.524f, T / 2, T / 2 + 0.012f, C("#C9A227"))   // olho mágico
                R(lw / 2 - 0.16f, lw / 2 + 0.16f, 1.2f, 1.235f, T / 2 + 0.006f, T / 2 + 0.016f, C("#C9A227"))               // aldrava/fresta de cartas
            }
            RUSTIC -> {
                b.m(Mt.WOOD, 1.4f)
                val n = 5; val pw = lw / n
                for (k in 0 until n) R(k * pw + 0.004f, (k + 1) * pw - 0.004f, 0.004f, h, -T / 2 + (k % 2) * 0.003f, T / 2 - (k % 3) * 0.002f, shade(c, (k * 7) % 11 - 5))
                // travessas e mão-francesa por dentro
                for (yy in floatArrayOf(0.32f, h - 0.4f)) R(0.05f, lw - 0.05f, yy, yy + 0.13f, -T / 2 - 0.028f, -T / 2, shade(c, -6))
                val steps = 9
                for (k in 0 until steps) { val t = (k + 0.5f) / steps; val x = 0.1f + (lw - 0.2f) * t; val yy = 0.45f + (h - 0.98f) * t; R(x - 0.06f, x + 0.06f, yy - 0.07f, yy + 0.07f, -T / 2 - 0.025f, -T / 2, shade(c, -6)) }
                // dobradiças de ferro, postigo com grade e argola
                b.m(Mt.METAL, 1f)
                for (yy in floatArrayOf(0.38f, h - 0.36f)) { R(0f, lw * 0.62f, yy, yy + 0.055f, T / 2, T / 2 + 0.008f, c2); R(lw * 0.62f - 0.03f, lw * 0.62f + 0.03f, yy - 0.015f, yy + 0.07f, T / 2, T / 2 + 0.008f, c2) }
                b.m(Mt.WOOD, 1f); both(lw / 2 - 0.15f, lw / 2 + 0.15f, 1.48f, 1.8f, 0.012f, shade(c, -14))
                b.m(Mt.PLAIN); R(lw / 2 - 0.11f, lw / 2 + 0.11f, 1.52f, 1.76f, T / 2 + 0.01f, T / 2 + 0.013f, C("#1E140E"))
                b.m(Mt.METAL, 1f); for (k in 0 until 3) R(lw / 2 - 0.07f + k * 0.07f - 0.008f, lw / 2 - 0.07f + k * 0.07f + 0.008f, 1.52f, 1.76f, T / 2 + 0.013f, T / 2 + 0.025f, c2)
                for (k in 0 until 10) { val a = 2 * PI.toFloat() * k / 10; R(lw - 0.15f + 0.06f * cos(a) - 0.01f, lw - 0.15f + 0.06f * cos(a) + 0.01f, 1.0f + 0.06f * sin(a) - 0.01f, 1.0f + 0.06f * sin(a) + 0.01f, T / 2 + 0.01f, T / 2 + 0.03f, c2) }
                R(lw - 0.17f, lw - 0.13f, 1.05f, 1.1f, T / 2, T / 2 + 0.02f, c2)
            }
            HGLASS -> {
                b.m(Mt.WOOD, 0.8f)
                R(0.004f, 0.11f, 0.004f, h, -T / 2, T / 2, c); R(lw - 0.11f, lw - 0.004f, 0.004f, h, -T / 2, T / 2, c)
                R(0.11f, lw - 0.11f, 0.004f, 0.22f, -T / 2, T / 2, c); R(0.11f, lw - 0.11f, h - 0.11f, h, -T / 2, T / 2, c)
                val n = 3; val gw = (lw - 0.22f) / n
                for (k in 0 until n) {
                    val x0 = 0.11f + k * gw
                    if (k > 0) { b.m(Mt.WOOD, 0.8f); R(x0 - 0.03f, x0 + 0.03f, 0.22f, h - 0.11f, -T / 2, T / 2, c) }
                    glass(x0 + 0.03f, x0 + gw - 0.03f, 0.22f, h - 0.11f, C("#E4EEF1"), 0.62f)
                }
                bar(lw - 0.17f, 0.6f, 1.55f, c2, 0.012f)
            }
            PIVOT -> {
                b.m(Mt.WOOD, 0.9f); R(0.004f, lw - 0.004f, 0.004f, h, -T / 2, T / 2, shade(c, -12))
                val n = 16; val sh = (h - 0.02f) / n
                for (k in 0 until n) both(0.02f, lw - 0.02f, 0.01f + k * sh + 0.008f, 0.01f + (k + 1) * sh - 0.008f, 0.012f, shade(c, (k * 5) % 9 - 4))
                bar(lw - 0.13f, 0.35f, 1.95f, c2, 0.016f, 0.07f)
            }
            BEACH -> {
                b.m(Mt.WOOD, 0.8f)
                R(0.004f, 0.1f, 0.004f, h, -T / 2, T / 2, c); R(lw - 0.1f, lw - 0.004f, 0.004f, h, -T / 2, T / 2, c)
                R(0.1f, lw - 0.1f, 0.004f, 0.16f, -T / 2, T / 2, c); R(0.1f, lw - 0.1f, 0.88f, 1.0f, -T / 2, T / 2, c); R(0.1f, lw - 0.1f, h - 0.1f, h, -T / 2, T / 2, c)
                R(0.1f, lw - 0.1f, 0.16f, 0.88f, -T / 2 + 0.01f, T / 2 - 0.01f, c)
                both(0.16f, lw - 0.16f, 0.24f, 0.8f, 0.012f, shade(c, 6))
                // veneziana: palhetas com fundo escuro aparecendo entre elas
                b.m(Mt.PLAIN); R(0.1f, lw - 0.1f, 1.0f, h - 0.1f, -0.004f, 0.004f, shade(c, -45))
                b.m(Mt.WOOD, 0.8f)
                val n = 13; val sp = (h - 1.12f) / n
                for (k in 0 until n) { val yy = 1.02f + k * sp; R(0.1f, lw - 0.1f, yy, yy + sp * 0.62f, 0.004f, 0.016f, shade(c, 4)); R(0.1f, lw - 0.1f, yy + sp * 0.3f, yy + sp * 0.92f, -0.016f, -0.004f, shade(c, 4)) }
                lever(lw - 0.07f, 1.0f, C("#C9CED3"))
            }
            SLIDE -> {
                val col = c
                b.m(Mt.METAL, 1f)
                R(0f, 0.035f, 0f, h, -0.02f, 0.02f, col); R(lw - 0.035f, lw, 0f, h, -0.02f, 0.02f, col)
                R(0.035f, lw - 0.035f, h - 0.07f, h, -0.02f, 0.02f, col); R(0.035f, lw - 0.035f, 0f, 0.07f, -0.02f, 0.02f, col)
                glass(0.035f, lw - 0.035f, 0.07f, h - 0.07f, C("#D6EEF5"), 0.24f, 0.01f)
                // bolinhas de aviso no vidro e a faixa da marca
                b.m(Mt.PLAIN)
                val nd = (lw / 0.12f).toInt()
                for (k in 0 until nd) { val x = 0.08f + k * (lw - 0.16f) / max(1, nd - 1); R(x - 0.02f, x + 0.02f, 1.43f, 1.47f, 0.006f, 0.008f, C("#FFFFFF"), false) }
                R(0.035f, lw - 0.035f, 0.98f, 1.0f, 0.006f, 0.008f, c2, false)
                if (idx == 0) { R(lw - 0.32f, lw - 0.08f, 1.12f, 1.2f, 0.006f, 0.009f, C("#FFFFFF"), false) }   // adesivo "ENTRADA"
            }
            ALU, SHUTTER -> {
                aluFrame(0.06f, 0.08f, 0.2f, c)
                if (d.name == "MODA") bar(lw - 0.09f, 0.4f, 1.85f, c2, 0.013f) else bar(lw - 0.09f, 0.72f, 1.5f, if (st == SHUTTER) C("#C9CED3") else c2)
                b.m(Mt.PLAIN); R(0.2f, lw - 0.2f, 1.08f, 1.12f, 0.007f, 0.009f, C("#FFFFFF"), false)   // adesivo jateado
                b.m(Mt.METAL, 1f); R(lw - 0.1f, lw - 0.06f, 0.1f, 0.16f, -T / 2 - 0.01f, T / 2 + 0.01f, C("#3A3A3A"))   // fechadura no rodapé
                if (idx == 0) plaque(lw * 0.48f)
            }
            ALU2 -> {
                aluFrame(0.06f, 0.09f, 0.22f, c)
                push(0.1f, lw - 0.08f, 1.0f, c2)
                bar(lw - 0.08f, 0.8f, 1.5f, C("#C9CED3"), 0.013f)
                b.m(Mt.PLAIN); R(0.12f, lw - 0.12f, 1.28f, 1.36f, 0.007f, 0.009f, c2, false)
            }
            LOBBY -> {
                b.m(Mt.METAL, 1f)
                R(0.004f, 0.05f, 0f, h, -T / 2, T / 2, c); R(lw - 0.05f, lw - 0.004f, 0f, h, -T / 2, T / 2, c)
                R(0.05f, lw - 0.05f, h - 0.06f, h, -T / 2, T / 2, c); R(0.05f, lw - 0.05f, 0f, 0.1f, -T / 2, T / 2, c)
                glass(0.05f, lw - 0.05f, 0.1f, h - 0.06f, C("#BFD8E2"), 0.34f)
                // puxador horizontal comprido, dos dois lados
                for (s in floatArrayOf(1f, -1f)) {
                    val zb = s * (T / 2 + 0.06f)
                    R(lw - 0.75f, lw - 0.08f, 1.03f, 1.06f, min(zb - 0.015f, zb + 0.015f), max(zb - 0.015f, zb + 0.015f), c2)
                    for (x in floatArrayOf(lw - 0.7f, lw - 0.13f)) R(x - 0.012f, x + 0.012f, 1.035f, 1.055f, min(s * T / 2, zb), max(s * T / 2, zb), c2)
                }
                if (idx == 0) { b.m(Mt.PLAIN); R(0.15f, 0.45f, 1.55f, 1.6f, 0.007f, 0.009f, C("#FFFFFF"), false) }
            }
            WOODG -> {
                b.m(Mt.WOOD, 0.9f)
                R(0.004f, 0.11f, 0.004f, h, -T / 2, T / 2, c); R(lw - 0.11f, lw - 0.004f, 0.004f, h, -T / 2, T / 2, c)
                R(0.11f, lw - 0.11f, 0.004f, 0.2f, -T / 2, T / 2, c); R(0.11f, lw - 0.11f, 0.84f, 0.98f, -T / 2, T / 2, c); R(0.11f, lw - 0.11f, h - 0.12f, h, -T / 2, T / 2, c)
                R(0.11f, lw - 0.11f, 0.2f, 0.84f, -T / 2 + 0.012f, T / 2 - 0.012f, c)
                both(0.17f, lw - 0.17f, 0.27f, 0.77f, 0.014f, shade(c, 7))
                glass(0.11f, lw - 0.11f, 0.98f, h - 0.12f, C("#D9ECF0"), 0.28f)
                // baguetes (2 colunas × 3 linhas) dos dois lados
                b.m(Mt.WOOD, 0.9f)
                val gx = (0.11f + lw - 0.11f) / 2
                both(gx - 0.014f, gx + 0.014f, 0.98f, h - 0.12f, 0.008f, c)
                for (k in 1..2) { val yy = 0.98f + (h - 1.1f) * k / 3; both(0.11f, lw - 0.11f, yy - 0.014f, yy + 0.014f, 0.008f, c) }
                lever(lw - 0.075f, 1.0f, c2)
                if (idx == 0) plaque(gx)
            }
            WOOD2 -> {
                b.m(Mt.WOOD, 0.9f)
                R(0.004f, 0.1f, 0.004f, h, -T / 2, T / 2, c); R(lw - 0.1f, lw - 0.004f, 0.004f, h, -T / 2, T / 2, c)
                R(0.1f, lw - 0.1f, 0.004f, 0.18f, -T / 2, T / 2, c); R(0.1f, lw - 0.1f, 1.0f, 1.12f, -T / 2, T / 2, c); R(0.1f, lw - 0.1f, h - 0.12f, h, -T / 2, T / 2, c)
                R(0.1f, lw - 0.1f, 0.18f, 1.0f, -T / 2 + 0.012f, T / 2 - 0.012f, c)
                both(0.15f, lw - 0.15f, 0.25f, 0.55f, 0.014f, shade(c, 8)); both(0.15f, lw - 0.15f, 0.62f, 0.93f, 0.014f, shade(c, 8))
                glass(0.1f, lw - 0.1f, 1.12f, h - 0.12f, C("#F3E3C3"), 0.4f)   // vidro âmbar
                b.m(Mt.WOOD, 0.9f); both((lw) / 2 - 0.012f, lw / 2 + 0.012f, 1.12f, h - 0.12f, 0.008f, c); both(0.1f, lw - 0.1f, (1.12f + h - 0.12f) / 2 - 0.012f, (1.12f + h - 0.12f) / 2 + 0.012f, 0.008f, c)
                bar(lw - 0.07f, 0.8f, 1.45f, c2, 0.012f, 0.05f)
            }
            SHOJI -> {
                b.m(Mt.WOOD, 0.8f)
                R(0.004f, 0.06f, 0.004f, h, -T / 2, T / 2, c); R(lw - 0.06f, lw - 0.004f, 0.004f, h, -T / 2, T / 2, c)
                R(0.06f, lw - 0.06f, 0.004f, 0.32f, -T / 2, T / 2, shade(c, -10)); R(0.06f, lw - 0.06f, h - 0.06f, h, -T / 2, T / 2, c)
                glass(0.06f, lw - 0.06f, 0.32f, h - 0.06f, C("#F7F2E4"), 0.82f, 0.006f)   // papel washi
                b.m(Mt.WOOD, 0.8f)
                val nc = 4; val nr = 7
                for (k in 1 until nc) { val x = 0.06f + (lw - 0.12f) * k / nc; both(x - 0.011f, x + 0.011f, 0.32f, h - 0.06f, 0.012f, c) }
                for (k in 1 until nr) { val yy = 0.32f + (h - 0.38f) * k / nr; both(0.06f, lw - 0.06f, yy - 0.011f, yy + 0.011f, 0.012f, c) }
                b.m(Mt.PLAIN); R(lw - 0.15f, lw - 0.09f, 0.95f, 1.1f, T / 2 - 0.004f, T / 2 + 0.002f, C("#2B2116"))   // puxador cavado
            }
            POLICE -> {
                b.m(Mt.METAL, 1f)
                R(0.004f, 0.08f, 0f, h, -T / 2, T / 2, c); R(lw - 0.08f, lw - 0.004f, 0f, h, -T / 2, T / 2, c)
                R(0.08f, lw - 0.08f, 0f, 1.0f, -T / 2, T / 2, c); R(0.08f, lw - 0.08f, h - 0.1f, h, -T / 2, T / 2, c)
                both(0.14f, lw - 0.14f, 0.15f, 0.9f, 0.01f, shade(c, 8))
                glass(0.08f, lw - 0.08f, 1.0f, h - 0.1f, C("#C7DCE8"), 0.32f)
                for (k in 0 until 4) { val x = 0.08f + (lw - 0.16f) * (k + 0.5f) / 4; R(x - 0.01f, x + 0.01f, 1.0f, h - 0.1f, T / 2, T / 2 + 0.03f, C("#1A2A44")) }
                push(0.1f, lw - 0.08f, 1.0f, c2); bar(lw - 0.08f, 0.85f, 1.35f, c2, 0.013f)
            }
            FIRE -> {
                b.m(Mt.METAL, 1f)
                R(0.004f, lw - 0.004f, 0f, h, -T / 2, T / 2, c)
                for (k in 0 until 5) both(0.06f, lw - 0.06f, 0.1f + k * 0.17f, 0.18f + k * 0.17f, 0.008f, shade(c, -10))
                b.m(Mt.PLAIN); both(lw / 2 - 0.15f, lw / 2 + 0.15f, 1.15f, 1.85f, 0.006f, C("#E8E8E8"))
                glass(lw / 2 - 0.13f, lw / 2 + 0.13f, 1.17f, 1.83f, C("#CFE8F0"), 0.35f, T + 0.016f)
                push(0.1f, lw - 0.08f, 1.0f, c2)
                b.m(Mt.PLAIN); R(0.12f, lw - 0.12f, 2.0f, 2.1f, T / 2, T / 2 + 0.004f, C("#FFFFFF"), false)
            }
            SCHOOL -> {
                b.m(Mt.METAL, 1f)
                R(0.004f, 0.08f, 0f, h, -T / 2, T / 2, c); R(lw - 0.08f, lw - 0.004f, 0f, h, -T / 2, T / 2, c)
                R(0.08f, lw - 0.08f, 0f, 1.05f, -T / 2, T / 2, c); R(0.08f, lw - 0.08f, h - 0.1f, h, -T / 2, T / 2, c)
                b.m(Mt.PLAIN); for (k in 0 until 6) R(0.16f, lw - 0.16f, 0.2f + k * 0.09f, 0.24f + k * 0.09f, T / 2 - 0.002f, T / 2 + 0.002f, C("#16351A"))   // venezianas de ventilação
                glass(0.08f, lw - 0.08f, 1.05f, h - 0.1f, C("#D2E6EC"), 0.3f)
                b.m(Mt.METAL, 1f)
                for (k in 1..2) { val x = 0.08f + (lw - 0.16f) * k / 3; both(x - 0.01f, x + 0.01f, 1.05f, h - 0.1f, 0.02f, c) }
                for (k in 1..2) { val yy = 1.05f + (h - 1.15f) * k / 3; both(0.08f, lw - 0.08f, yy - 0.01f, yy + 0.01f, 0.02f, c) }
                push(0.1f, lw - 0.08f, 1.0f, C("#9E9E9E")); lever(lw - 0.06f, 1.0f, C("#BDBDBD"))
            }
            CHURCH -> {
                val tt = 0.04f
                b.m(Mt.WOOD, 1.2f)
                val n = 5; val pw = lw / n
                for (k in 0 until n) R(k * pw + 0.003f, (k + 1) * pw - 0.003f, 0f, h, -T / 2 - tt, T / 2 + tt, shade(c, (k * 5) % 9 - 4))
                // almofadas grandes, cravos de ferro e ferragens
                b.m(Mt.WOOD, 1.2f)
                for (yy in floatArrayOf(0.25f, 1.55f, 2.75f)) R(0.12f, lw - 0.12f, yy, yy + 1.0f, T / 2 + tt, T / 2 + tt + 0.025f, shade(c, -12))
                b.m(Mt.METAL, 1f)
                for (yy in floatArrayOf(0.25f, 1.55f, 2.75f)) for (r in 0..1) for (k in 0 until 4) { val x = 0.16f + (lw - 0.32f) * k / 3; val y2 = yy + 0.06f + r * 0.88f; R(x - 0.018f, x + 0.018f, y2 - 0.018f, y2 + 0.018f, T / 2 + tt + 0.025f, T / 2 + tt + 0.045f, C("#1E1E1E")) }
                for (yy in floatArrayOf(0.5f, 2.0f, h - 0.5f)) R(0f, lw * 0.55f, yy, yy + 0.07f, T / 2 + tt, T / 2 + tt + 0.012f, c2)
                for (k in 0 until 12) { val a = 2 * PI.toFloat() * k / 12; R(lw - 0.22f + 0.1f * cos(a) - 0.014f, lw - 0.22f + 0.1f * cos(a) + 0.014f, 1.25f + 0.1f * sin(a) - 0.014f, 1.25f + 0.1f * sin(a) + 0.014f, T / 2 + tt + 0.02f, T / 2 + tt + 0.045f, c2) }
                R(lw - 0.25f, lw - 0.19f, 1.33f, 1.4f, T / 2 + tt, T / 2 + tt + 0.03f, c2)
            }
        }
    }

    /** Porta giratória: coluna no meio e 4 folhas de vidro com perfis e barra de empurrar. */
    private fun wings(b: MB, d: City.Door) {
        val R = drumR(d.w) - 0.05f; val h = d.h - 0.02f; val c = d.col
        b.m(Mt.METAL, 1f); b.cyl(0f, 0f, 0f, 0.07f, 0.07f, h, c, true, 12)
        for (k in 0 until 4) {
            val ax = if (k == 0) 1f else if (k == 2) -1f else 0f; val az = if (k == 1) 1f else if (k == 3) -1f else 0f
            fun W(r0: Float, r1: Float, y0: Float, y1: Float, t: Float, col: Int, lit: Boolean = true) {
                val cx = (r0 + r1) / 2; val len = r1 - r0
                if (ax != 0f) b.box(ax * cx, (y0 + y1) / 2, 0f, len, y1 - y0, t, col, lit) else b.box(0f, (y0 + y1) / 2, az * cx, t, y1 - y0, len, col, lit)
            }
            b.m(Mt.GLASS); b.al = 0.26f; W(0.07f, R - 0.04f, 0.1f, h - 0.08f, 0.014f, C("#D2ECF4")); b.al = 1f
            b.m(Mt.METAL, 1f)
            W(0.07f, R, 0.02f, 0.1f, 0.05f, c); W(0.07f, R, h - 0.08f, h, 0.05f, c); W(R - 0.04f, R, 0.1f, h - 0.08f, 0.05f, c)
            W(0.2f, R - 0.12f, 1.0f, 1.04f, 0.09f, if (d.style == REV_BRASS) C("#D4AF37") else C("#E0E0E0"))
            // escova de vedação na ponta
            b.m(Mt.PLAIN); W(R, R + 0.03f, 0.1f, h - 0.08f, 0.02f, C("#2B2B2B"))
        }
    }
}
