package com.vinicius.meular

import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import com.vinicius.meular.CityGeo.L
import com.vinicius.meular.CityGeo.lb
import com.vinicius.meular.CityGeo.lcyl
import com.vinicius.meular.CityGeo.lsph
import com.vinicius.meular.CityGeo.ball

/**
 * Etapa 126: interiores próprios e realistas de cada estabelecimento da cidade (hospital, barbearia, supermercado, banco,
 * academia, hotel, escola, polícia...). Cada um com mobília, equipamentos e detalhes do que existe de verdade nesse lugar.
 * Tudo vai no construtor A (fica visível de dentro); o forro e as luminárias ficam em H (somem só na vista de cima).
 */
object CityInt {
    private val FL = City.FLOOR

    /** Área útil de um térreo: x0..x1, z0..z1; a porta fica na parede zf, virada para fz (fora). */
    class Room(val g: CityGeo.Gen, val x0: Float, val z0: Float, val x1: Float, val z1: Float, val zf: Float, val fz: Float, val doorX: Float) {
        val A = g.A
        val rng = g.rng
        val w = x1 - x0
        val cx = (x0 + x1) / 2
        val cz = (z0 + z1) / 2
        val inF = -fz
        val back = if (fz > 0) z0 else z1
        val depth = abs(back - zf)
        /** [d] metros para dentro a partir da parede da porta */
        fun Zi(d: Float) = zf + inF * d
        /** referencial virado para a porta, [d] para dentro */
        fun toDoor(x: Float, d: Float) = L(x, Zi(d), 0f, fz)
        /** referencial virado para o fundo */
        fun toBack(x: Float, d: Float) = L(x, Zi(d), 0f, inF)
        fun solid(xa: Float, da: Float, xb: Float, db: Float) = g.solid(min(xa, xb), min(Zi(da), Zi(db)), max(xa, xb), max(Zi(da), Zi(db)))
        /** a passagem da porta fica livre */
        fun nearDoor(x: Float, d: Float) = abs(x - doorX) < 1.3f && d < 2.4f
    }

    /** Piso de cada tipo (material, cor, escala da textura) ou null = o piso padrão. */
    fun floor(name: String): Triple<Int, Int, Float>? = when (name) {
        "HOSPITAL", "PRONTO-SOCORRO", "CLÍNICA" -> Triple(Mt.TILE, C("#E9F1F5"), 0.8f)
        "SUPERMERCADO", "MERCADINHO", "CONVENIÊNCIA", "FARMÁCIA" -> Triple(Mt.TILE, C("#F7F7F4"), 1.0f)
        "BARBEARIA" -> Triple(Mt.TILE, C("#F4F4F2"), 1.0f)
        "SALÃO DE BELEZA" -> Triple(Mt.TILE, C("#FFF3F7"), 0.8f)
        "ACADEMIA" -> Triple(Mt.STONE, C("#3A3D42"), 0.5f)
        "BANCO", "CASA DE CÂMBIO", "HOTEL" -> Triple(Mt.STONE, C("#E8E2D6"), 0.35f)
        "ESCOLA" -> Triple(Mt.TILE, C("#D8E4D0"), 0.7f)
        "POLÍCIA", "BOMBEIROS" -> Triple(Mt.TILE, C("#D6D9DC"), 0.7f)
        "RESTAURANTE", "PIZZARIA", "LIVRARIA", "CAFÉ" -> Triple(Mt.FLOOR_D, C("#E6D3BC"), 0.6f)
        "SHOPPING" -> Triple(Mt.STONE, C("#F2EEE6"), 0.3f)
        else -> null
    }

    /** Monta o interior; false = não tem interior próprio aqui (fica o de CityGeo). */
    fun build(g: CityGeo.Gen, name: String, x0: Float, z0: Float, x1: Float, z1: Float, zf: Float, fz: Float, doorX: Float): Boolean {
        val r = Room(g, x0, z0, x1, z1, zf, fz, doorX)
        when (name) {
            "HOSPITAL", "PRONTO-SOCORRO", "CLÍNICA" -> hospital(r, name)
            "BARBEARIA" -> barber(r)
            "SALÃO DE BELEZA" -> salon(r)
            "SUPERMERCADO", "MERCADINHO", "CONVENIÊNCIA" -> market(r, name)
            "FARMÁCIA" -> pharmacy(r)
            "BANCO", "CASA DE CÂMBIO" -> bank(r, name)
            "ACADEMIA" -> gym(r)
            "HOTEL" -> hotel(r)
            "ESCOLA" -> school(r)
            "POLÍCIA" -> police(r)
            "BOMBEIROS" -> fire(r)
            "ESCRITÓRIOS", "RESIDENCIAL", "CONDOMÍNIO" -> lobby(r, name)
            "SHOPPING" -> mall(r)
            "RESTAURANTE" -> restaurant(r)
            else -> return false
        }
        ceiling(r, name)
        common(r, name)
        return true
    }

    // ============================================================ partes comuns

    /** Forro com luminárias embutidas (H: some na vista de cima). */
    private fun ceiling(r: Room, name: String) {
        val H = r.g.H
        val warm = name in arrayOf("RESTAURANTE", "HOTEL", "BARBEARIA", "LIVRARIA")
        H.m(Mt.PLASTER, 0.5f); H.box(r.cx, FL + 4.35f, r.cz, r.w, 0.1f, r.depth, C(if (name == "ACADEMIA") "#2E3136" else "#F4F4F4"))
        H.m(Mt.PLAIN)
        var x = r.x0 + 1.8f
        while (x < r.x1 - 1.2f) {
            var d = 1.6f
            while (d < r.depth - 1f) {
                if (warm) { H.cyl(x, FL + 4.27f, r.Zi(d), 0.16f, 0.16f, 0.03f, C("#FFE8B8"), false, 10) }
                else H.box(x, FL + 4.285f, r.Zi(d), 1.2f, 0.02f, 0.3f, C("#FDFEFF"), false)
                d += 3f
            }
            x += 3.2f
        }
    }

    /** Detalhes que todo estabelecimento tem: rodapé, extintor, placa de saída, lixeira, relógio, ar-condicionado, câmera. */
    private fun common(r: Room, name: String) {
        val A = r.A
        val dark = name in arrayOf("ACADEMIA", "BARBEARIA")
        // rodapé nas três paredes
        A.m(Mt.WOOD, 1f)
        val rod = C(if (dark) "#1E1E1E" else "#D9D4CC")
        A.box(r.x0 + 0.02f, FL + 0.06f, r.cz, 0.03f, 0.12f, r.depth - 0.1f, rod)
        A.box(r.x1 - 0.02f, FL + 0.06f, r.cz, 0.03f, 0.12f, r.depth - 0.1f, rod)
        A.box(r.cx, FL + 0.06f, r.back - r.inF * 0.02f, r.w - 0.1f, 0.12f, 0.03f, rod)
        // extintor vermelho na parede ao lado da porta, com placa
        val ex = if (r.doorX - r.x0 > 1.6f) r.doorX - 1.1f else r.doorX + 1.1f
        val le = r.toBack(ex, 0.12f)
        A.m(Mt.METAL, 1f)
        lcyl(A, le, 0f, FL + 0.45f, 0f, 0.08f, 0.08f, 0.5f, C("#C62828"), 10)
        lcyl(A, le, 0f, FL + 0.95f, 0f, 0.03f, 0.03f, 0.08f, C("#212121"), 6)
        A.m(Mt.PLAIN); lb(A, le, 0f, FL + 1.45f, 0.1f, 0.22f, 0.3f, 0.01f, C("#D32F2F"), false)
        // placa de SAÍDA verde acima da porta (por dentro)
        lb(A, r.toBack(r.doorX, 0.14f), 0f, FL + 2.8f, 0f, 0.42f, 0.16f, 0.04f, C("#1B9E4B"), false)
        lb(A, r.toBack(r.doorX, 0.11f), 0f, FL + 2.8f, 0f, 0.3f, 0.05f, 0.01f, C("#E8FFE8"), false)
        // relógio na parede do fundo
        val lc = r.toDoor(r.x1 - 1.2f, r.depth - 0.04f)
        A.m(Mt.PLAIN)
        lb(A, lc, 0f, FL + 2.85f, 0f, 0.36f, 0.36f, 0.04f, C("#263238"))
        lb(A, lc, 0f, FL + 2.85f, -0.025f, 0.3f, 0.3f, 0.01f, C("#FAFAFA"), false)
        lb(A, lc, 0.04f, FL + 2.87f, -0.035f, 0.1f, 0.015f, 0.005f, C("#212121"), false)
        lb(A, lc, 0f, FL + 2.9f, -0.035f, 0.015f, 0.12f, 0.005f, C("#212121"), false)
        // ar-condicionado split na parede lateral
        val la = L(r.x0 + 0.13f, r.Zi(r.depth * 0.5f), 1f, 0f)
        A.m(Mt.METAL, 1f); lb(A, la, 0f, FL + 3.4f, 0f, 1.0f, 0.3f, 0.22f, C("#F5F5F5"))
        A.m(Mt.PLAIN); lb(A, la, 0f, FL + 3.29f, -0.1f, 0.9f, 0.03f, 0.04f, C("#B0BEC5"))
        // câmera de segurança no canto
        A.m(Mt.METAL, 1f); A.box(r.x1 - 0.25f, FL + 3.9f, r.back - r.inF * 0.25f, 0.1f, 0.1f, 0.22f, C("#EEEEEE"))
        A.m(Mt.PLAIN); A.box(r.x1 - 0.25f, FL + 3.9f, r.back - r.inF * 0.37f, 0.06f, 0.06f, 0.02f, C("#111111"))
        // lixeira perto da porta
        if (!r.nearDoor(r.x0 + 0.4f, 0.6f)) bin(A, r.x0 + 0.35f, r.Zi(0.6f), C(if (dark) "#424242" else "#9E9E9E"))
        // capacho
        A.m(Mt.RUG, 0.4f); A.box(r.doorX, FL + 0.008f, r.Zi(0.75f), 1.3f, 0.016f, 0.9f, C("#5D4037"))
    }

    private fun bench(b: MB, l: L) {
        b.m(Mt.WOOD, 1f)
        for (k in 0 until 4) lb(b, l, 0f, FL + 0.45f, -0.18f + k * 0.12f, 1.6f, 0.04f, 0.1f, C("#A1887F"))
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-0.7f, 0.7f)) lb(b, l, s, FL + 0.22f, 0f, 0.06f, 0.44f, 0.46f, C("#37474F"))
    }

    private fun bin(b: MB, x: Float, z: Float, c: Int) {
        b.m(Mt.METAL, 1f)
        b.cyl(x, FL, z, 0.17f, 0.2f, 0.6f, c, true, 10)
        b.cyl(x, FL + 0.6f, z, 0.21f, 0.21f, 0.04f, shade(c, -30), true, 10)
    }

    private fun poster(b: MB, l: L, lx: Float, y: Float, sx: Float, sy: Float, bg: Int, fg: Int) {
        b.m(Mt.PLAIN)
        lb(b, l, lx, y, 0f, sx + 0.06f, sy + 0.06f, 0.02f, C("#2B2B2B"))
        lb(b, l, lx, y, -0.012f, sx, sy, 0.005f, bg, false)
        lb(b, l, lx - sx * 0.15f, y + sy * 0.15f, -0.016f, sx * 0.5f, sy * 0.35f, 0.004f, fg, false)
        lb(b, l, lx, y - sy * 0.28f, -0.016f, sx * 0.75f, sy * 0.08f, 0.004f, shade(fg, -40), false)
    }

    private fun waterCooler(b: MB, l: L) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.5f, 0f, 0.32f, 1.0f, 0.32f, C("#ECEFF1"))
        b.m(Mt.GLASS); b.al = 0.55f; lcyl(b, l, 0f, FL + 1.0f, 0f, 0.14f, 0.14f, 0.42f, C("#81D4FA"), 10); b.al = 1f
        b.m(Mt.PLAIN); lb(b, l, -0.06f, FL + 0.82f, -0.17f, 0.04f, 0.05f, 0.04f, C("#1E88E5")); lb(b, l, 0.06f, FL + 0.82f, -0.17f, 0.04f, 0.05f, 0.04f, C("#E53935"))
    }

    private fun tvWall(b: MB, l: L, y: Float, w: Float, screen: Int) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, y, 0f, w, w * 0.57f, 0.05f, C("#111111"))
        b.m(Mt.PLAIN); lb(b, l, 0f, y, -0.03f, w - 0.06f, w * 0.57f - 0.06f, 0.005f, screen, false)
        lb(b, l, -w * 0.2f, y + w * 0.1f, -0.034f, w * 0.35f, w * 0.18f, 0.004f, shade(screen, 50), false)
    }

    /** Fileira de cadeiras de espera presas numa barra (aeroporto/hospital). */
    private fun beamSeats(b: MB, l: L, n: Int, seat: Int) {
        val w = n * 0.58f
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.38f, 0.05f, w, 0.05f, 0.08f, C("#9EA7AD"))
        for (s in floatArrayOf(-w / 2 + 0.2f, w / 2 - 0.2f)) { lb(b, l, s, FL + 0.19f, 0.05f, 0.05f, 0.38f, 0.05f, C("#9EA7AD")); lb(b, l, s, FL + 0.01f, 0.05f, 0.08f, 0.02f, 0.5f, C("#9EA7AD")) }
        b.m(Mt.FABRIC, 1f)
        for (k in 0 until n) {
            val sx = -w / 2 + 0.29f + k * 0.58f
            lb(b, l, sx, FL + 0.45f, 0f, 0.5f, 0.06f, 0.46f, seat)
            lb(b, l, sx, FL + 0.75f, 0.24f, 0.5f, 0.5f, 0.05f, seat)
        }
        b.m(Mt.METAL, 1f)
        for (k in 0..n) lb(b, l, -w / 2 + k * 0.58f, FL + 0.62f, 0.02f, 0.04f, 0.04f, 0.42f, C("#78909C"))
    }

    private fun computer(b: MB, l: L, lx: Float, y: Float, lz: Float) {
        b.m(Mt.METAL, 1f)
        lb(b, l, lx, y + 0.01f, lz + 0.05f, 0.2f, 0.02f, 0.16f, C("#212121"))
        lb(b, l, lx, y + 0.12f, lz + 0.06f, 0.04f, 0.2f, 0.03f, C("#212121"))
        lb(b, l, lx, y + 0.3f, lz + 0.04f, 0.56f, 0.34f, 0.03f, C("#1A1A1A"))
        b.m(Mt.PLAIN); lb(b, l, lx, y + 0.3f, lz + 0.023f, 0.52f, 0.3f, 0.004f, C("#2E5C8A"), false)
        lb(b, l, lx - 0.1f, y + 0.36f, lz + 0.019f, 0.22f, 0.12f, 0.003f, C("#E3F2FD"), false)
        b.m(Mt.METAL, 1f); lb(b, l, lx, y + 0.012f, lz - 0.22f, 0.42f, 0.02f, 0.14f, C("#2A2A2A"))
    }

    /** Preenche a faixa [d0, d1] (metros para dentro) com células de cw × cd: chama [fn](x, d) no centro de cada uma. */
    private fun grid(r: Room, d0: Float, d1: Float, cw: Float, cd: Float, xm: Float = 1.2f, fn: (Float, Float, Int) -> Unit) {
        val nx = ((r.w - 2 * xm) / cw).toInt(); val nd = ((d1 - d0) / cd).toInt()
        if (nx < 1 || nd < 1) return
        val ox = r.cx - nx * cw / 2 + cw / 2
        var i = 0
        for (j in 0 until nd) for (k in 0 until nx) { val x = ox + k * cw; val d = d0 + cd / 2 + j * cd; if (!r.nearDoor(x, d)) fn(x, d, i); i++ }
    }

    /** Cama hospitalar: cabeceira para trás de [l] (pés para F), grades, colchão com cabeceira elevada, lençol, travesseiro, mesinha, soro. */
    private fun hospitalBed(b: MB, l: L, blanket: Int) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.42f, 0f, 0.95f, 0.14f, 2.0f, C("#CFD8DC"))
        for (s in floatArrayOf(-0.42f, 0.42f)) for (t in floatArrayOf(-0.9f, 0.9f)) { lb(b, l, s, FL + 0.2f, t, 0.05f, 0.4f, 0.05f, C("#90A4AE")); lb(b, l, s, FL + 0.05f, t, 0.08f, 0.1f, 0.08f, C("#37474F")) }
        lb(b, l, 0f, FL + 0.75f, 1.0f, 1.0f, 0.65f, 0.06f, C("#ECEFF1"))   // cabeceira
        lb(b, l, 0f, FL + 0.65f, -1.0f, 1.0f, 0.4f, 0.05f, C("#ECEFF1"))   // pezeira
        for (s in floatArrayOf(-0.5f, 0.5f)) lb(b, l, s, FL + 0.72f, 0.3f, 0.03f, 0.22f, 0.9f, C("#B0BEC5"))   // grades
        b.m(Mt.FABRIC, 1f)
        lb(b, l, 0f, FL + 0.58f, -0.25f, 0.9f, 0.16f, 1.4f, C("#FAFAFA"))
        lb(b, l, 0f, FL + 0.72f, 0.55f, 0.9f, 0.16f, 0.65f, C("#FAFAFA"))
        lb(b, l, 0f, FL + 0.67f, -0.35f, 0.92f, 0.06f, 1.1f, blanket)
        lb(b, l, 0f, FL + 0.84f, 0.7f, 0.55f, 0.12f, 0.32f, C("#FFFFFF"))
        // mesa de cabeceira e suporte de soro
        b.m(Mt.WOOD, 1f); lb(b, l, 0.85f, FL + 0.38f, 0.75f, 0.45f, 0.76f, 0.42f, C("#ECEFF1"))
        b.m(Mt.PLAIN); lcyl(b, l, 0.8f, FL + 0.76f, 0.75f, 0.04f, 0.035f, 0.14f, C("#90CAF9"), 8)
        b.m(Mt.METAL, 1f); lcyl(b, l, -0.75f, FL, 0.85f, 0.16f, 0.16f, 0.03f, C("#90A4AE"), 5); lcyl(b, l, -0.75f, FL, 0.85f, 0.014f, 0.014f, 1.9f, C("#B0BEC5"), 6)
        b.m(Mt.GLASS); b.al = 0.6f; lb(b, l, -0.75f, FL + 1.72f, 0.85f, 0.1f, 0.2f, 0.05f, C("#E1F5FE")); b.al = 1f
    }

    // ============================================================ hospital / pronto-socorro / clínica

    private fun hospital(r: Room, name: String) {
        val A = r.A; val rng = r.rng
        val blue = C("#1E88E5"); val teal = C("#00897B")
        // faixas-guia coloridas no piso (verde = emergência, azul = consultórios)
        A.m(Mt.PLAIN)
        A.plane(r.doorX - 0.08f, min(r.Zi(1.2f), r.Zi(r.depth - 4.5f)), r.doorX + 0.08f, max(r.Zi(1.2f), r.Zi(r.depth - 4.5f)), FL + 0.006f, C("#2E7D32"))
        A.plane(r.doorX + 0.2f, min(r.Zi(1.2f), r.Zi(r.depth - 4.5f)), r.doorX + 0.36f, max(r.Zi(1.2f), r.Zi(r.depth - 4.5f)), FL + 0.006f, blue)
        // corrimão/para-choque nas paredes laterais
        A.m(Mt.WOOD, 1f)
        for (sx in floatArrayOf(r.x0 + 0.05f, r.x1 - 0.05f)) A.box(sx, FL + 0.9f, r.cz, 0.08f, 0.12f, r.depth - 1f, C("#B0BEC5"))
        // recepção: balcão em L, branco com faixa azul, computadores e placa
        val rw = min(4.6f, r.w * 0.32f)
        val rx = r.x0 + 0.6f + rw / 2
        val rd = 2.6f
        val lr = r.toDoor(rx, rd)
        A.m(Mt.WOOD, 1f); lb(A, lr, 0f, FL + 0.55f, 0f, rw, 1.1f, 0.6f, C("#FAFAFA"))
        A.m(Mt.PLAIN); lb(A, lr, 0f, FL + 0.82f, -0.305f, rw, 0.12f, 0.01f, if (name == "CLÍNICA") teal else blue, false)
        A.m(Mt.STONE, 1.5f); lb(A, lr, 0f, FL + 1.12f, -0.05f, rw + 0.1f, 0.04f, 0.45f, C("#ECEFF1"))
        A.m(Mt.WOOD, 1f); lb(A, lr, 0f, FL + 0.74f, 0.35f, rw, 0.04f, 0.5f, C("#ECEFF1"))
        for (k in 0 until 2) computer(A, L(lr.wx(-rw / 4 + k * rw / 2, 0.35f), lr.wz(-rw / 4 + k * rw / 2, 0.35f), -lr.fx, -lr.fz), 0f, FL + 0.76f, 0f)
        for (k in 0 until 2) CityGeo.officeChair(A, L(lr.wx(-rw / 4 + k * rw / 2, 0.95f), lr.wz(-rw / 4 + k * rw / 2, 0.95f), lr.fx, lr.fz), C("#37474F"))
        A.m(Mt.PLAIN); lb(A, r.toDoor(rx, r.depth - 0.03f), 0f, FL + 2.6f, 0f, 2.0f, 0.45f, 0.03f, if (name == "CLÍNICA") teal else C("#D62828"), false)
        lb(A, r.toDoor(rx, r.depth - 0.05f), -0.75f, FL + 2.6f, 0f, 0.28f, 0.09f, 0.01f, C("#FFFFFF"), false); lb(A, r.toDoor(rx, r.depth - 0.05f), -0.75f, FL + 2.6f, 0f, 0.09f, 0.28f, 0.01f, C("#FFFFFF"), false)
        r.solid(rx - rw / 2 - 0.1f, rd - 0.45f, rx + rw / 2 + 0.1f, rd + 0.45f)
        // painel de senhas acima da recepção
        A.m(Mt.METAL, 1f); lb(A, lr, 0f, FL + 2.5f, 0.2f, 1.0f, 0.4f, 0.08f, C("#111111"))
        A.m(Mt.PLAIN); lb(A, lr, -0.2f, FL + 2.5f, 0.155f, 0.4f, 0.24f, 0.005f, C("#FF1744"), false); lb(A, lr, 0.25f, FL + 2.5f, 0.155f, 0.35f, 0.24f, 0.005f, C("#FFEA00"), false)
        // sala de espera: fileiras de cadeiras viradas para uma TV
        val wx0 = rx + rw / 2 + 1.6f
        // salas grandes: vários blocos de espera ao longo do saguão
        var bx0 = wx0 + 8.6f
        while (bx0 + 6.5f < r.x1 - 2.5f) {
            val bc = bx0 + 3.2f
            for (row in 0 until 3) { val d = 2.2f + row * 1.25f; if (d > r.depth - 5f) break; beamSeats(A, r.toBack(bc, d), 9, if (name == "CLÍNICA") teal else C("#1565C0")); r.solid(bc - 2.6f, d - 0.35f, bc + 2.6f, d + 0.35f) }
            tvWall(A, L(bc, r.Zi(0.12f), 0f, r.inF), FL + 2.3f, 1.3f, C("#3949AB"))
            CityGeo.plant(A, bx0 - 0.3f, r.Zi(1.2f), 1.2f, rng)
            bx0 += 8.6f
        }
        val wx1 = min(r.x1 - 1.2f, wx0 + 7f)
        if (wx1 - wx0 > 2f) {
            val n = ((wx1 - wx0) / 0.58f).toInt().coerceIn(3, 10)
            val sxc = (wx0 + wx1) / 2
            for (row in 0 until 3) {
                val d = 2.2f + row * 1.25f
                if (d > r.depth - 5f) break
                beamSeats(A, r.toBack(sxc, d), n, if (name == "CLÍNICA") teal else C("#1565C0"))
                r.solid(sxc - n * 0.29f, d - 0.35f, sxc + n * 0.29f, d + 0.35f)
            }
            tvWall(A, L(sxc, r.Zi(0.12f), 0f, r.inF), FL + 2.3f, 1.3f, C("#3949AB"))
            waterCooler(A, L(wx1 + 0.6f, r.Zi(1.0f), -1f, 0f))
            r.solid(wx1 + 0.4f, 0.8f, wx1 + 0.8f, 1.2f)
            CityGeo.plant(A, wx0 - 0.6f, r.Zi(1.0f), 1.1f, rng)
            // mesinha com revistas
            A.m(Mt.WOOD, 1f); A.box(wx0 - 0.6f, FL + 0.25f, r.Zi(3.0f), 0.6f, 0.5f, 0.6f, C("#B0BEC5"))
            A.m(Mt.PLAIN); for (k in 0 until 3) A.box(wx0 - 0.6f + (k - 1) * 0.12f, FL + 0.51f + k * 0.008f, r.Zi(3.0f), 0.2f, 0.008f, 0.28f, rng.pick(arrayOf(C("#E57373"), C("#64B5F6"), C("#FFF176"))))
        }
        // consultórios/boxes no fundo: divisórias, maca com papel, mesa, pia, cortina
        val rooms = max(2, min(5, (r.w / 3.4f).toInt()))
        val rwid = r.w / rooms
        val dz0 = r.depth - 3.6f
        A.m(Mt.PLASTER, 0.5f)
        for (k in 0..rooms) {
            val px = r.x0 + k * rwid
            if (k in 1 until rooms) A.box(px, FL + 1.25f, r.Zi(dz0 + 1.8f), 0.1f, 2.5f, 3.6f, C("#EAF2F6"))
        }
        for (k in 0 until rooms) {
            val ox = r.x0 + k * rwid
            // parede da frente do consultório com vão de porta
            A.m(Mt.PLASTER, 0.5f)
            val dw = 1.0f
            val doorC = ox + rwid - 0.8f
            A.box((ox + doorC - dw / 2) / 2, FL + 1.25f, r.Zi(dz0), doorC - dw / 2 - ox, 2.5f, 0.1f, C("#EAF2F6"))
            A.box((doorC + dw / 2 + ox + rwid) / 2, FL + 1.25f, r.Zi(dz0), ox + rwid - doorC - dw / 2, 2.5f, 0.1f, C("#EAF2F6"))
            A.box(doorC, FL + 2.35f, r.Zi(dz0), dw, 0.3f, 0.1f, C("#EAF2F6"))
            A.m(Mt.PLAIN); A.box(doorC - dw / 2 - 0.25f, FL + 2.0f, r.Zi(dz0 - 0.06f), 0.3f, 0.12f, 0.01f, if (name == "PRONTO-SOCORRO") C("#D62828") else blue, false)
            r.solid(ox, dz0 - 0.1f, doorC - dw / 2, dz0 + 0.1f); r.solid(doorC + dw / 2, dz0 - 0.1f, ox + rwid, dz0 + 0.1f)
            // maca de exame encostada na parede do fundo, com papel e escadinha
            val bx = ox + rwid * 0.38f
            val lm = L(bx, r.Zi(r.depth - 1.25f), 1f, 0f)
            A.m(Mt.METAL, 1f); lb(A, lm, 0f, FL + 0.38f, 0f, 1.85f, 0.6f, 0.62f, C("#ECEFF1"))
            A.m(Mt.FABRIC, 1f); lb(A, lm, 0f, FL + 0.74f, 0f, 1.85f, 0.12f, 0.62f, C("#455A64")); lb(A, lm, -0.75f, FL + 0.88f, 0f, 0.45f, 0.16f, 0.62f, C("#455A64"))
            A.m(Mt.PLAIN); lb(A, lm, 0.1f, FL + 0.805f, 0f, 1.6f, 0.005f, 0.5f, C("#FFFFFF"))
            A.m(Mt.METAL, 1f); lb(A, lm, 0.2f, FL + 0.1f, -0.45f, 0.45f, 0.2f, 0.3f, C("#B0BEC5"))
            r.solid(bx - 0.4f, r.depth - 2.25f, bx + 0.4f, r.depth - 0.3f)
            if (name == "PRONTO-SOCORRO" || k % 2 == 0) {
                // monitor de sinais vitais e suporte de soro
                val mx = bx + 0.7f
                A.m(Mt.METAL, 1f); A.cyl(mx, FL, r.Zi(r.depth - 0.6f), 0.18f, 0.18f, 0.04f, C("#90A4AE"), true, 5); A.cyl(mx, FL, r.Zi(r.depth - 0.6f), 0.015f, 0.015f, 1.9f, C("#B0BEC5"), true, 6)
                A.box(mx, FL + 1.85f, r.Zi(r.depth - 0.6f), 0.3f, 0.02f, 0.02f, C("#B0BEC5"))
                A.m(Mt.GLASS); A.al = 0.6f; A.box(mx + 0.12f, FL + 1.68f, r.Zi(r.depth - 0.6f), 0.1f, 0.2f, 0.05f, C("#E1F5FE")); A.al = 1f
                val lmon = L(mx - 0.1f, r.Zi(r.depth - 0.25f), 0f, r.fz)
                A.m(Mt.METAL, 1f); lb(A, lmon, 0f, FL + 1.55f, 0f, 0.42f, 0.32f, 0.12f, C("#37474F"))
                A.m(Mt.PLAIN); lb(A, lmon, 0f, FL + 1.55f, -0.065f, 0.36f, 0.25f, 0.005f, C("#0A1A12"), false)
                lb(A, lmon, -0.05f, FL + 1.6f, -0.07f, 0.24f, 0.012f, 0.003f, C("#00E676"), false); lb(A, lmon, -0.05f, FL + 1.52f, -0.07f, 0.2f, 0.012f, 0.003f, C("#FFEB3B"), false)
            }
            // mesa do médico com computador e cadeiras
            val tx = ox + rwid * 0.75f
            if (rwid > 2.8f) {
                val lt = L(tx, r.Zi(dz0 + 1.2f), 0f, r.inF)
                A.m(Mt.WOOD, 1f); lb(A, lt, 0f, FL + 0.74f, 0f, 1.1f, 0.04f, 0.6f, C("#FAFAFA"))
                for (s in floatArrayOf(-0.5f, 0.5f)) lb(A, lt, s, FL + 0.37f, 0f, 0.04f, 0.74f, 0.56f, C("#CFD8DC"))
                computer(A, lt, 0f, FL + 0.76f, 0.05f)
                CityGeo.officeChair(A, L(lt.wx(0f, 0.6f), lt.wz(0f, 0.6f), -lt.fx, -lt.fz), C("#263238"))
                r.solid(tx - 0.6f, dz0 + 0.8f, tx + 0.6f, dz0 + 1.6f)
            }
            // pia com armário e dispensers na parede lateral do consultório
            val lp = L(ox + 0.32f, r.Zi(r.depth - 2.6f), 1f, 0f)
            A.m(Mt.WOOD, 1f); lb(A, lp, 0f, FL + 0.43f, 0f, 0.8f, 0.86f, 0.5f, C("#F5F5F5"))
            A.m(Mt.STONE, 1.5f); lb(A, lp, 0f, FL + 0.88f, 0f, 0.84f, 0.04f, 0.54f, C("#E0E0E0"))
            A.m(Mt.METAL, 1f); lb(A, lp, 0f, FL + 0.87f, -0.02f, 0.4f, 0.04f, 0.3f, C("#CFD8DC")); lb(A, lp, 0f, FL + 1.0f, 0.18f, 0.03f, 0.22f, 0.03f, C("#B0BEC5"))
            A.m(Mt.PLAIN); lb(A, lp, -0.28f, FL + 1.35f, 0.24f, 0.14f, 0.24f, 0.08f, C("#FFFFFF")); lb(A, lp, 0.26f, FL + 1.35f, 0.24f, 0.24f, 0.16f, 0.08f, C("#90CAF9"))
            // cortina de privacidade
            A.m(Mt.METAL, 1f); A.box(bx, FL + 2.3f, r.Zi(r.depth - 2.35f), rwid * 0.6f, 0.03f, 0.03f, C("#B0BEC5"))
            A.m(Mt.FABRIC, 1f); A.box(bx - rwid * 0.18f, FL + 1.3f, r.Zi(r.depth - 2.35f), rwid * 0.22f, 1.9f, 0.04f, if (name == "PRONTO-SOCORRO") C("#80CBC4") else C("#9FA8DA"))
        }
        // faixa do meio (salas grandes): enfermaria, posto de enfermagem, raio-x, máquinas de lanche, mais espera
        val m0 = 6.6f; val m1 = dz0 - 1.6f
        if (m1 - m0 > 3.2f) {
            val mods = max(1, (r.w / 9f).toInt())
            val mw = r.w / mods
            for (k in 0 until mods) {
                val mx = r.x0 + mw * (k + 0.5f)
                val md = (m0 + m1) / 2
                // cada módulo é uma sala fechada (divisórias com porta para o corredor e visor de vidro)
                val wc = C("#E3EEF2")
                A.m(Mt.PLASTER, 0.5f)
                A.box(mx, FL + 1.3f, r.Zi(m0 - 0.4f), mw - 0.1f, 2.6f, 0.12f, wc)
                if (k > 0) A.box(mx - mw / 2, FL + 1.3f, r.Zi((m0 + m1) / 2 - 0.2f), 0.12f, 2.6f, m1 - m0 + 0.4f, wc)
                val dW = 1.2f
                A.box((mx - mw / 2 + mx - dW / 2) / 2, FL + 1.3f, r.Zi(m1 + 0.2f), mw / 2 - dW / 2, 2.6f, 0.12f, wc)
                A.box((mx + dW / 2 + mx + mw / 2) / 2, FL + 1.3f, r.Zi(m1 + 0.2f), mw / 2 - dW / 2, 2.6f, 0.12f, wc)
                A.box(mx, FL + 2.45f, r.Zi(m1 + 0.2f), dW, 0.3f, 0.12f, wc)
                A.m(Mt.GLASS); A.al = 0.35f; A.box(mx - mw / 4, FL + 1.6f, r.Zi(m1 + 0.2f), mw / 4, 0.9f, 0.14f, C("#E1F5FE")); A.al = 1f
                A.m(Mt.PLAIN); A.box(mx + dW / 2 + 0.35f, FL + 2.0f, r.Zi(m1 + 0.27f), 0.35f, 0.14f, 0.01f, arrayOf(C("#00897B"), C("#1E88E5"), C("#F9A825"), C("#8E24AA"))[k % 4], false)
                r.solid(mx - mw / 2, m0 - 0.5f, mx + mw / 2, m0 - 0.3f)
                if (k > 0) r.solid(mx - mw / 2 - 0.1f, m0 - 0.4f, mx - mw / 2 + 0.1f, m1 + 0.3f)
                r.solid(mx - mw / 2, m1 + 0.1f, mx - dW / 2, m1 + 0.3f); r.solid(mx + dW / 2, m1 + 0.1f, mx + mw / 2, m1 + 0.3f)
                when ((k + if (name == "PRONTO-SOCORRO") 0 else 1) % 4) {
                    0 -> {   // enfermaria: camas lado a lado com divisória de cabeceira e cortinas
                        val nb = max(1, ((mw - 1f) / 2.2f).toInt())
                        A.m(Mt.PLASTER, 0.5f); A.box(mx, FL + 1.0f, r.Zi(m1 - 0.1f), mw - 1f, 2.0f, 0.12f, C("#E3EEF2"))
                        A.m(Mt.PLAIN); A.box(mx, FL + 1.4f, r.Zi(m1 - 0.17f), mw - 1.2f, 0.18f, 0.02f, C("#80CBC4"))   // régua de gases
                        for (i in 0 until nb) {
                            val bx = mx - (nb - 1) * 1.1f + i * 2.2f
                            hospitalBed(A, L(bx, r.Zi(m1 - 1.15f), 0f, r.fz), rng.pick(arrayOf(C("#90CAF9"), C("#A5D6A7"), C("#FFCC80"))))
                            if (i < nb - 1) { A.m(Mt.METAL, 1f); A.box(bx + 1.1f, FL + 2.2f, r.Zi(m1 - 1.2f), 0.02f, 0.02f, 2.2f, C("#B0BEC5")); A.m(Mt.FABRIC, 1f); A.box(bx + 1.1f, FL + 1.25f, r.Zi(m1 - 0.9f), 0.03f, 1.8f, 1.2f, C("#B2DFDB")) }
                        }
                        r.solid(mx - mw / 2 + 0.5f, m1 - 2.3f, mx + mw / 2 - 0.5f, m1)
                    }
                    1 -> {   // posto de enfermagem em ilha
                        val l = L(mx, r.Zi(md), 0f, r.fz)
                        A.m(Mt.WOOD, 1f); lb(A, l, 0f, FL + 0.55f, 0f, 3.2f, 1.1f, 0.6f, C("#FAFAFA")); lb(A, l, 0f, FL + 0.55f, 1.2f, 3.2f, 1.1f, 0.6f, C("#FAFAFA"))
                        for (s0 in floatArrayOf(-1.6f, 1.6f)) lb(A, l, s0, FL + 0.55f, 0.6f, 0.6f, 1.1f, 1.8f, C("#FAFAFA"))
                        A.m(Mt.PLAIN); lb(A, l, 0f, FL + 0.82f, -0.305f, 3.2f, 0.14f, 0.01f, C("#26A69A"), false)
                        A.m(Mt.STONE, 1.5f); lb(A, l, 0f, FL + 1.12f, 0f, 3.3f, 0.04f, 0.7f, C("#ECEFF1"))
                        for (i in 0 until 3) computer(A, L(l.wx(-1f + i, 0.6f), l.wz(-1f + i, 0.6f), 0f, -r.fz).let { L(it.ox, it.oz, -l.fx, -l.fz) }, 0f, FL + 0.76f, -0.25f)
                        for (i in 0 until 2) CityGeo.officeChair(A, L(l.wx(-0.6f + i * 1.2f, 0.6f), l.wz(-0.6f + i * 1.2f, 0.6f), l.fx, l.fz), C("#00796B"))
                        A.m(Mt.PLAIN); lb(A, l, 0f, FL + 2.7f, 0.6f, 1.6f, 0.4f, 0.05f, C("#00897B"), false)
                        A.m(Mt.METAL, 1f); for (s0 in floatArrayOf(-0.6f, 0.6f)) lb(A, l, s0, FL + 3.55f, 0.6f, 0.02f, 1.3f, 0.02f, C("#9E9E9E"))
                        r.solid(mx - 1.9f, md - 0.4f, mx + 1.9f, md + 1.6f)
                    }
                    2 -> {   // sala de raio-x: aparelho, mesa e biombo de chumbo
                        val l = L(mx, r.Zi(md), 1f, 0f)
                        A.m(Mt.METAL, 1f); lb(A, l, 0f, FL + 0.45f, 0f, 0.8f, 0.9f, 2.0f, C("#ECEFF1")); lb(A, l, 0f, FL + 0.92f, 0f, 0.7f, 0.06f, 2.0f, C("#90A4AE"))
                        lb(A, l, 0f, FL + 1.9f, 0f, 0.12f, 1.1f, 0.12f, C("#CFD8DC")); lb(A, l, 0f, FL + 1.5f, 0f, 0.5f, 0.3f, 0.5f, C("#B0BEC5"))
                        lb(A, l, 0f, FL + 2.45f, 0f, 0.15f, 0.15f, 3.0f, C("#CFD8DC"))
                        lb(A, l, 1.4f, FL + 1.0f, 0.8f, 1.2f, 2.0f, 0.06f, C("#78909C"))
                        A.m(Mt.PLAIN); lb(A, l, 1.4f, FL + 1.5f, 0.76f, 0.5f, 0.3f, 0.01f, C("#B3E5FC"), false)
                        A.box(mx, FL + 0.007f, r.Zi(md), 2.6f, 0.01f, 3.0f, C("#FFF59D"))
                        r.solid(mx - 0.5f, md - 1.1f, mx + 0.5f, md + 1.1f)
                    }
                    else -> {   // lanche: máquinas, mesinhas e mais cadeiras
                        for (i in 0 until 2) {
                            val l = L(mx - 1.2f + i * 0.9f, r.Zi(m1 - 0.45f), 0f, r.fz)
                            A.m(Mt.METAL, 1f); lb(A, l, 0f, FL + 0.95f, 0f, 0.8f, 1.9f, 0.7f, if (i == 0) C("#C62828") else C("#263238"))
                            A.m(Mt.GLASS); A.al = 0.4f; lb(A, l, -0.1f, FL + 1.15f, -0.36f, 0.55f, 1.2f, 0.02f, C("#E1F5FE")); A.al = 1f
                            goods(A, l.wx(-0.1f, -0.1f), FL + 0.65f, l.wz(-0.1f, -0.1f), if (l.alongX) 0.5f else 0.3f, 1.0f, if (l.alongX) 0.3f else 0.5f)
                        }
                        r.solid(mx - 1.7f, m1 - 0.9f, mx - 0.3f, m1)
                        CityGeo.cafeTable(A, mx + 0.6f, r.Zi(md), rng); r.solid(mx, md - 0.9f, mx + 1.2f, md + 0.9f)
                        beamSeats(A, L(mx - 0.6f, r.Zi(m0 + 0.6f), 0f, r.inF), 4, C("#1565C0")); r.solid(mx - 1.8f, m0 + 0.2f, mx + 0.6f, m0 + 1f)
                        CityGeo.plant(A, mx + mw / 2 - 0.6f, r.Zi(m1 - 0.5f), 1.3f, rng)
                    }
                }
            }
        }
        // equipamento no corredor: cadeira de rodas, carrinho de emergência, maca, álcool em gel
        val cd = dz0 - 1.0f
        wheelchair(A, L(r.x1 - 0.9f, r.Zi(cd), -1f, 0f))
        crashCart(A, L(r.x0 + 0.5f, r.Zi(cd), 1f, 0f))
        if (r.w > 9f) CityGeo.stretcher(A, L(r.cx + 2f, r.Zi(cd - 0.3f), 1f, 0f).let { L(r.cx + 2f, r.Zi(cd - 0.4f), 0f, r.fz) }.let { L(it.ox, it.oz, 1f, 0f) })
        A.m(Mt.PLAIN); for (k in 0 until 2) A.box(r.x0 + 0.08f, FL + 1.3f, r.Zi(1.5f + k * 4f), 0.06f, 0.22f, 0.1f, C("#FFFFFF"))
        poster(A, L(r.x1 - 0.03f, r.Zi(3.5f), -1f, 0f), 0f, FL + 1.7f, 0.6f, 0.8f, C("#E3F2FD"), C("#1E88E5"))
        poster(A, L(r.x1 - 0.03f, r.Zi(5f), -1f, 0f), 0f, FL + 1.7f, 0.6f, 0.8f, C("#FFF3E0"), C("#EF6C00"))
    }

    private fun wheelchair(b: MB, l: L) {
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-0.3f, 0.3f)) {
            lb(b, l, s, FL + 0.3f, 0.05f, 0.03f, 0.6f, 0.6f, C("#263238"))   // roda grande (perfil)
            lb(b, l, s, FL + 0.08f, -0.35f, 0.03f, 0.14f, 0.14f, C("#263238"))
            lb(b, l, s, FL + 0.7f, 0.25f, 0.025f, 0.5f, 0.025f, C("#B0BEC5"))
            lb(b, l, s, FL + 0.62f, -0.05f, 0.03f, 0.03f, 0.45f, C("#B0BEC5"))
        }
        b.m(Mt.FABRIC, 1f)
        lb(b, l, 0f, FL + 0.48f, -0.05f, 0.5f, 0.05f, 0.45f, C("#1A237E"))
        lb(b, l, 0f, FL + 0.75f, 0.2f, 0.5f, 0.45f, 0.04f, C("#1A237E"))
        b.m(Mt.METAL, 1f); lb(b, l, 0f, FL + 0.12f, -0.42f, 0.4f, 0.02f, 0.14f, C("#90A4AE"))
    }

    private fun crashCart(b: MB, l: L) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.55f, 0f, 0.75f, 0.95f, 0.5f, C("#D32F2F"))
        b.m(Mt.PLAIN)
        for (k in 0 until 4) lb(b, l, 0f, FL + 0.25f + k * 0.2f, -0.255f, 0.66f, 0.15f, 0.01f, C("#E57373"))
        for (k in 0 until 4) lb(b, l, 0f, FL + 0.25f + k * 0.2f, -0.262f, 0.2f, 0.02f, 0.01f, C("#EEEEEE"))
        b.m(Mt.METAL, 1f); lb(b, l, 0f, FL + 1.06f, 0f, 0.8f, 0.05f, 0.55f, C("#EEEEEE"))
        lb(b, l, 0.15f, FL + 1.2f, 0.05f, 0.35f, 0.22f, 0.25f, C("#FFB300"))   // desfibrilador
        for (s in floatArrayOf(-0.3f, 0.3f)) for (t in floatArrayOf(-0.2f, 0.2f)) lb(b, l, s, FL + 0.04f, t, 0.06f, 0.08f, 0.06f, C("#212121"))
    }

    // ============================================================ barbearia

    private fun barber(r: Room) {
        val A = r.A; val rng = r.rng
        // piso xadrez preto e branco (só as casas pretas sobre o piso claro)
        A.m(Mt.STONE, 0.8f)
        var gx = 0
        var x = r.x0 + 0.05f
        while (x < r.x1 - 0.1f) {
            var gz = 0
            var d = 0.05f
            while (d < r.depth - 0.1f) {
                if ((gx + gz) % 2 == 0) A.plane(x, min(r.Zi(d), r.Zi(d + 0.5f)), min(x + 0.5f, r.x1 - 0.05f), max(r.Zi(d), r.Zi(d + 0.5f)), FL + 0.005f, C("#26292C"))
                d += 0.5f; gz++
            }
            x += 0.5f; gx++
        }
        // lambri de madeira escura na parede das cadeiras
        A.m(Mt.WOOD, 1f); A.box(r.x0 + 0.03f, FL + 0.6f, r.cz, 0.04f, 1.2f, r.depth - 0.2f, C("#3E2723"))
        A.box(r.x0 + 0.05f, FL + 1.22f, r.cz, 0.08f, 0.05f, r.depth - 0.2f, C("#2B1B17"))
        // cadeiras de barbeiro clássicas viradas para espelhos com moldura
        var d = 1.9f
        var n = 0
        while (d < r.depth - 2.2f && n < 4) {
            val z = r.Zi(d)
            val lm = L(r.x0 + 0.06f, z, 1f, 0f)
            A.m(Mt.WOOD, 1f); lb(A, lm, 0f, FL + 1.75f, 0.02f, 1.0f, 1.3f, 0.05f, C("#5D4037"))
            A.m(Mt.METAL, 1f); lb(A, lm, 0f, FL + 1.75f, -0.01f, 0.86f, 1.16f, 0.02f, C("#DCEFF5"))
            // bancada com produtos (pomadas, frascos, borrifador)
            A.m(Mt.WOOD, 1f); lb(A, lm, 0f, FL + 1.0f, -0.2f, 1.0f, 0.05f, 0.4f, C("#4E342E")); lb(A, lm, 0f, FL + 0.55f, -0.1f, 1.0f, 0.9f, 0.3f, C("#3E2723"))
            A.m(Mt.PLAIN)
            for (i in 0 until 5) lcyl(A, lm, -0.38f + i * 0.17f, FL + 1.025f, -0.24f, 0.04f, 0.035f, 0.1f + (i % 3) * 0.05f, rng.pick(arrayOf(C("#1565C0"), C("#F9A825"), C("#2E7D32"), C("#B71C1C"), C("#FAFAFA"))), 8)
            A.m(Mt.METAL, 1f); lb(A, lm, 0.38f, FL + 1.06f, -0.3f, 0.14f, 0.06f, 0.06f, C("#212121"))   // máquina de cortar
            barberChair(A, L(r.x0 + 1.25f, z, -1f, 0f))
            A.m(Mt.FABRIC, 1f); lb(A, L(r.x0 + 1.25f, z, -1f, 0f), 0f, FL + 0.02f, 0f, 0.9f, 0.01f, 0.9f, C("#8D6E63"))   // tapetinho
            r.g.solid(r.x0, min(z, z) - 0.55f, r.x0 + 1.75f, z + 0.55f)
            d += 1.7f; n++
        }
        // lavatório no fundo e prateleira de produtos à venda
        val lw = r.toDoor(r.x0 + 1.2f, r.depth - 0.35f)
        A.m(Mt.STONE, 1f); lb(A, lw, 0f, FL + 0.45f, 0f, 1.0f, 0.9f, 0.5f, C("#212121"))
        A.m(Mt.PLAIN); lcyl(A, lw, 0f, FL + 0.9f, -0.05f, 0.26f, 0.2f, 0.1f, C("#FAFAFA"), 12)
        A.m(Mt.METAL, 1f); lb(A, lw, 0f, FL + 1.05f, 0.18f, 0.04f, 0.25f, 0.04f, C("#BDBDBD"))
        val ls = r.toDoor(r.x1 - 1.4f, r.depth - 0.2f)
        A.m(Mt.WOOD, 1f); lb(A, ls, 0f, FL + 1.3f, 0.05f, 1.6f, 2.0f, 0.06f, C("#3E2723"))
        for (k in 0 until 4) lb(A, ls, 0f, FL + 0.6f + k * 0.42f, -0.1f, 1.6f, 0.03f, 0.25f, C("#5D4037"))
        A.m(Mt.PLAIN)
        for (k in 0 until 4) for (i in 0 until 7) lcyl(A, ls, -0.66f + i * 0.22f, FL + 0.62f + k * 0.42f, -0.1f, 0.045f, 0.04f, 0.14f, rng.pick(arrayOf(C("#263238"), C("#C9A227"), C("#ECEFF1"), C("#6D4C41"), C("#1B5E20"))), 8)
        r.solid(r.x1 - 2.3f, r.depth - 0.5f, r.x1 - 0.5f, r.depth)
        // espera: sofá de couro, mesinha com revistas, TV
        val sz = 1.5f
        CityGeo.sofa(A, L(r.x1 - 0.65f, r.Zi(sz + 1.1f), -1f, 0f), 2.0f, C("#6D4C41"))
        r.solid(r.x1 - 1.2f, sz + 0.1f, r.x1, sz + 2.1f)
        A.m(Mt.WOOD, 1f); A.box(r.x1 - 1.7f, FL + 0.22f, r.Zi(sz + 1.1f), 0.5f, 0.44f, 0.9f, C("#3E2723"))
        A.m(Mt.PLAIN); for (k in 0 until 2) A.box(r.x1 - 1.7f, FL + 0.45f + k * 0.01f, r.Zi(sz + 0.9f + k * 0.35f), 0.25f, 0.01f, 0.3f, rng.pick(arrayOf(C("#FFCA28"), C("#EF5350"), C("#42A5F5"))))
        tvWall(A, L(r.x1 - 0.06f, r.Zi(sz + 3.6f), -1f, 0f), FL + 2.1f, 1.1f, C("#2E7D32"))
        // poste de barbeiro listrado na entrada (por dentro, ao lado da porta)
        val px = if (r.doorX - r.x0 > 2f) r.doorX - 1.0f else r.doorX + 1.0f
        A.m(Mt.METAL, 1f); A.cyl(px, FL, r.Zi(0.3f), 0.12f, 0.12f, 0.12f, C("#C9A227"), true, 10)
        A.m(Mt.PLAIN)
        for (k in 0 until 9) A.cyl(px, FL + 0.12f + k * 0.12f, r.Zi(0.3f), 0.09f, 0.09f, 0.12f, arrayOf(C("#D32F2F"), C("#FAFAFA"), C("#1565C0"))[k % 3], true, 10)
        A.m(Mt.METAL, 1f); A.cyl(px, FL + 1.2f, r.Zi(0.3f), 0.12f, 0.12f, 0.1f, C("#C9A227"), true, 10); ball(A, px, FL + 1.36f, r.Zi(0.3f), 0.08f, C("#C9A227"), 0.08f, 8)
        // caixa / balcão de atendimento com maquininha
        val lc = r.toDoor(r.x1 - 1.2f, 0.9f).let { L(it.ox, r.Zi(r.depth * 0.62f), -1f, 0f) }
        A.m(Mt.WOOD, 1f); lb(A, lc, 0f, FL + 0.55f, 0f, 1.2f, 1.1f, 0.5f, C("#4E342E"))
        A.m(Mt.STONE, 1.5f); lb(A, lc, 0f, FL + 1.12f, 0f, 1.25f, 0.04f, 0.55f, C("#212121"))
        A.m(Mt.METAL, 1f); lb(A, lc, 0.3f, FL + 1.17f, 0f, 0.1f, 0.06f, 0.16f, C("#263238"))
        r.g.solid(lc.ox - 0.35f, lc.oz - 0.65f, lc.ox + 0.35f, lc.oz + 0.65f)
        // cabideiro e quadros (fotos de cortes)
        A.m(Mt.WOOD, 1f); A.cyl(r.x1 - 0.4f, FL, r.Zi(0.8f), 0.18f, 0.18f, 0.03f, C("#3E2723"), true, 8); A.cyl(r.x1 - 0.4f, FL, r.Zi(0.8f), 0.025f, 0.025f, 1.8f, C("#3E2723"), true, 6)
        for (k in 0 until 3) poster(A, L(r.x1 - 0.03f, r.Zi(r.depth * 0.3f + k * 0.7f), -1f, 0f), 0f, FL + 2.3f, 0.45f, 0.6f, C("#ECEFF1"), C("#263238"))
        // letreiro neon na parede do fundo
        A.m(Mt.PLAIN); lb(A, r.toDoor(r.cx, r.depth - 0.03f), 0f, FL + 3.0f, 0f, 1.6f, 0.08f, 0.02f, C("#FF4081"), false)
        lb(A, r.toDoor(r.cx, r.depth - 0.03f), 0f, FL + 2.8f, 0f, 1.2f, 0.08f, 0.02f, C("#40C4FF"), false)
    }

    private fun barberChair(b: MB, l: L) {
        b.m(Mt.METAL, 1f)
        lcyl(b, l, 0f, FL, 0f, 0.32f, 0.32f, 0.04f, C("#CFD8DC"), 14)
        lcyl(b, l, 0f, FL + 0.04f, 0f, 0.1f, 0.08f, 0.32f, C("#ECEFF1"), 10)
        lb(b, l, 0f, FL + 0.38f, 0f, 0.5f, 0.06f, 0.5f, C("#B0BEC5"))
        b.m(Mt.FABRIC, 1f)
        val leather = C("#7B1E1E")
        lb(b, l, 0f, FL + 0.5f, -0.02f, 0.56f, 0.16f, 0.56f, leather)
        lb(b, l, 0f, FL + 0.88f, 0.28f, 0.56f, 0.7f, 0.14f, leather)
        lb(b, l, 0f, FL + 1.32f, 0.3f, 0.26f, 0.2f, 0.1f, leather)   // encosto de cabeça
        for (s in floatArrayOf(-0.32f, 0.32f)) { lb(b, l, s, FL + 0.7f, 0.0f, 0.1f, 0.06f, 0.5f, leather); b.m(Mt.METAL, 1f); lb(b, l, s, FL + 0.6f, 0.1f, 0.04f, 0.18f, 0.04f, C("#ECEFF1")); b.m(Mt.FABRIC, 1f) }
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.32f, -0.42f, 0.04f, 0.3f, 0.04f, C("#ECEFF1"))
        lb(b, l, 0f, FL + 0.2f, -0.5f, 0.4f, 0.03f, 0.18f, C("#CFD8DC"))   // descanso de pés
    }

    // ============================================================ salão de beleza

    private fun salon(r: Room) {
        val A = r.A; val rng = r.rng
        val pink = C("#EC407A")
        // bancadas com espelho iluminado (bolinhas de luz) e cadeiras brancas
        var d = 1.8f
        var n = 0
        while (d < r.depth - 2.6f && n < 4) {
            val z = r.Zi(d)
            val lm = L(r.x0 + 0.06f, z, 1f, 0f)
            A.m(Mt.METAL, 1f); lb(A, lm, 0f, FL + 1.75f, 0f, 0.9f, 1.1f, 0.03f, C("#DCEFF5"))
            A.m(Mt.PLAIN)
            for (i in 0 until 4) { lsph(A, lm, -0.5f, FL + 1.3f + i * 0.3f, -0.03f, 0.04f, C("#FFF8E1"), 0.04f, 6); lsph(A, lm, 0.5f, FL + 1.3f + i * 0.3f, -0.03f, 0.04f, C("#FFF8E1"), 0.04f, 6) }
            A.m(Mt.WOOD, 1f); lb(A, lm, 0f, FL + 0.95f, -0.18f, 1.1f, 0.05f, 0.36f, C("#FAFAFA"))
            A.m(Mt.PLAIN); for (i in 0 until 4) lcyl(A, lm, -0.35f + i * 0.22f, FL + 0.975f, -0.2f, 0.035f, 0.03f, 0.14f, rng.pick(arrayOf(pink, C("#AB47BC"), C("#FFD54F"), C("#FFFFFF"))), 8)
            A.m(Mt.METAL, 1f); lb(A, lm, 0.4f, FL + 1.02f, -0.25f, 0.18f, 0.08f, 0.08f, C("#212121"))   // secador
            CityGeo.officeChair(A, L(r.x0 + 1.2f, z, -1f, 0f), C("#FAFAFA"))
            r.g.solid(r.x0, z - 0.5f, r.x0 + 1.6f, z + 0.5f)
            d += 1.6f; n++
        }
        // lavatórios reclinados no fundo
        val nw = max(1, min(3, ((r.w - 3f) / 1.1f).toInt()))
        for (k in 0 until nw) {
            val wx = r.x0 + 1.2f + k * 1.1f
            val l = r.toBack(wx, r.depth - 1.3f)
            A.m(Mt.FABRIC, 1f); lb(A, l, 0f, FL + 0.45f, -0.2f, 0.6f, 0.15f, 0.6f, C("#212121")); lb(A, l, 0f, FL + 0.75f, 0.2f, 0.6f, 0.5f, 0.15f, C("#212121"))
            A.m(Mt.WOOD, 1f); lb(A, l, 0f, FL + 0.45f, 0.65f, 0.6f, 0.9f, 0.45f, C("#212121"))
            A.m(Mt.PLAIN); lcyl(A, l, 0f, FL + 0.9f, 0.6f, 0.25f, 0.18f, 0.12f, C("#FAFAFA"), 12)
            r.solid(wx - 0.35f, r.depth - 2.1f, wx + 0.35f, r.depth)
        }
        // manicure: mesinha com luminária e esmaltes
        val mx = r.x1 - 1.3f; val mz = r.depth * 0.55f
        val lt = L(mx, r.Zi(mz), -1f, 0f)
        A.m(Mt.WOOD, 1f); lb(A, lt, 0f, FL + 0.74f, 0f, 1.0f, 0.04f, 0.5f, C("#FAFAFA")); for (s in floatArrayOf(-0.45f, 0.45f)) lb(A, lt, s, FL + 0.37f, 0f, 0.04f, 0.74f, 0.45f, C("#F8BBD0"))
        A.m(Mt.PLAIN); for (i in 0 until 8) lcyl(A, lt, -0.35f + i * 0.08f, FL + 0.76f, 0.15f, 0.018f, 0.015f, 0.07f, rng.pick(arrayOf(C("#D50000"), pink, C("#6A1B9A"), C("#FFAB91"), C("#212121"))), 6)
        A.m(Mt.METAL, 1f); lcyl(A, lt, 0.4f, FL + 0.76f, 0.15f, 0.07f, 0.07f, 0.02f, C("#FAFAFA"), 8); lb(A, lt, 0.4f, FL + 1.05f, 0.1f, 0.02f, 0.55f, 0.02f, C("#FAFAFA")); lb(A, lt, 0.3f, FL + 1.32f, 0f, 0.25f, 0.06f, 0.12f, C("#FAFAFA"))
        CityGeo.chair(A, L(mx - 0.75f, r.Zi(mz), 1f, 0f), C("#FAFAFA"), pink); CityGeo.chair(A, L(mx + 0.55f, r.Zi(mz), -1f, 0f), C("#FAFAFA"), pink)
        r.solid(mx - 1.1f, mz - 0.6f, mx + 0.9f, mz + 0.6f)
        // capacete secador
        val hx = r.x1 - 0.8f; val hz = r.depth * 0.3f
        CityGeo.chair(A, L(hx, r.Zi(hz), -1f, 0f), C("#FAFAFA"), C("#212121"))
        A.m(Mt.METAL, 1f); A.cyl(hx + 0.25f, FL, r.Zi(hz), 0.02f, 0.02f, 1.3f, C("#BDBDBD"), true, 6); ball(A, hx, FL + 1.25f, r.Zi(hz), 0.28f, C("#F48FB1"), 0.24f, 10)
        r.solid(hx - 0.35f, hz - 0.35f, hx + 0.4f, hz + 0.35f)
        // recepção e vitrine de produtos
        val lr = L(r.x1 - 0.9f, r.Zi(1.6f), -1f, 0f)
        A.m(Mt.WOOD, 1f); lb(A, lr, 0f, FL + 0.55f, 0f, 1.4f, 1.1f, 0.5f, C("#FAFAFA")); A.m(Mt.PLAIN); lb(A, lr, 0f, FL + 0.55f, -0.255f, 1.4f, 0.12f, 0.01f, pink, false)
        computer(A, L(lr.ox + 0.3f, lr.oz, 1f, 0f), 0f, FL + 1.1f, 0f)
        r.g.solid(lr.ox - 0.3f, lr.oz - 0.75f, lr.ox + 0.3f, lr.oz + 0.75f)
        for (k in 0 until 3) poster(A, L(r.x1 - 0.03f, r.Zi(r.depth * 0.75f + (k - 1) * 0.7f), -1f, 0f), 0f, FL + 2.1f, 0.5f, 0.65f, C("#FCE4EC"), pink)
        CityGeo.plant(A, r.x1 - 0.5f, r.Zi(0.6f), 1.2f, rng)
    }

    // ============================================================ supermercado / mercadinho / conveniência

    private fun market(r: Room, name: String) {
        val A = r.A; val rng = r.rng
        val big = name == "SUPERMERCADO"
        val brand = C(if (name == "CONVENIÊNCIA") "#0F7A3D" else if (big) "#D62828" else "#2E7D32")
        // caixas registradoras perto da porta (cada uma com esteira, monitor, sacolas e número)
        val nCk = if (big) max(2, min(6, ((r.w - 8f) / 2.6f).toInt())) else 1
        val ckD = 2.4f
        for (k in 0 until nCk) {
            val x = if (big) r.x0 + 2f + k * 2.6f else (if (r.doorX - r.x0 > 3.5f) r.doorX - 2.2f else r.doorX + 2.2f)
            if (r.nearDoor(x, ckD)) continue
            val l = L(x, r.Zi(ckD), 1f, 0f)
            A.m(Mt.WOOD, 1f); lb(A, l, 0f, FL + 0.45f, 0f, 0.7f, 0.9f, 1.9f, C("#ECEFF1"))
            A.m(Mt.METAL, 1f); lb(A, l, 0f, FL + 0.91f, 0.35f, 0.5f, 0.02f, 1.0f, C("#212121"))   // esteira
            lb(A, l, 0f, FL + 0.95f, -0.15f, 0.05f, 0.08f, 0.02f, C("#9E9E9E"))
            lb(A, l, -0.1f, FL + 1.05f, -0.5f, 0.4f, 0.2f, 0.32f, C("#263238"))   // registradora
            lb(A, l, -0.1f, FL + 1.3f, -0.45f, 0.32f, 0.22f, 0.03f, C("#212121"))
            A.m(Mt.PLAIN); lb(A, l, -0.1f, FL + 1.3f, -0.465f, 0.28f, 0.18f, 0.004f, C("#4FC3F7"), false)
            lb(A, l, 0f, FL + 0.93f, -0.85f, 0.5f, 0.06f, 0.18f, C("#FFFFFF"))   // sacolas
            A.m(Mt.METAL, 1f); lb(A, l, 0.45f, FL + 1.1f, -0.6f, 0.04f, 2.2f, 0.04f, C("#9E9E9E"))   // poste com número aceso
            A.m(Mt.PLAIN); lb(A, l, 0.45f, FL + 2.25f, -0.6f, 0.26f, 0.26f, 0.06f, brand, false)
            lb(A, l, 0.45f, FL + 2.25f, -0.635f, 0.1f, 0.14f, 0.01f, C("#FFFFFF"), false)
            r.g.solid(x - 0.4f, min(r.Zi(ckD - 1f), r.Zi(ckD + 1f)), x + 0.4f, max(r.Zi(ckD - 1f), r.Zi(ckD + 1f)))
        }
        // carrinhos e cestinhas na entrada
        val cartX = if (r.doorX + 2.5f < r.x1 - 0.5f) r.doorX + 1.8f else r.doorX - 1.8f
        for (k in 0 until (if (big) 4 else 1)) cart(A, L(cartX, r.Zi(0.8f + k * 0.28f), 0f, r.fz))
        A.m(Mt.PLAIN)
        for (k in 0 until 5) A.box(cartX + (if (cartX > r.doorX) 1.0f else -1.0f), FL + 0.12f + k * 0.08f, r.Zi(1.0f), 0.45f, 0.08f, 0.32f, brand)
        // gôndolas (corredores) com pontas de gôndola e placas penduradas
        val aisleD0 = ckD + 2.2f
        val aisleD1 = r.depth - (if (big) 3.4f else 2.0f)
        val gw = if (big) 6f else min(3.2f, r.w - 3.2f)
        var ai = 0
        var x = r.x0 + (if (big) 2.2f else 1.6f) + gw / 2
        if (aisleD1 - aisleD0 <= 2.4f) {
            // loja rasa: gôndolas atravessadas (ao longo da largura), entre os caixas e as geladeiras
            val dz = min(ckD + 1.6f, r.depth - 2.2f)
            val len = min(r.w - 4.4f, 6f)
            if (len > 1.5f && dz > ckD + 0.9f) {
                for (gx in floatArrayOf(r.cx - len / 2 - 0.3f, r.cx + len / 2 + 0.3f).take(if (r.w > 2 * len + 3f) 2 else 1)) {
                    val cxg = if (r.w > 2 * len + 3f) gx else r.cx
                    gondola(A, cxg, r.Zi(dz), len, rng, r.fz, true)
                    r.solid(cxg - len / 2 - 0.5f, dz - 0.5f, cxg + len / 2 + 0.5f, dz + 0.5f)
                }
            }
        }
        while (x + gw / 2 < r.x1 - 1.4f && aisleD1 - aisleD0 > 2.4f) {
            val len = aisleD1 - aisleD0
            // gôndola ao longo da profundidade: prateleiras dos dois lados
            gondola(A, x, r.Zi((aisleD0 + aisleD1) / 2), len, rng, r.fz)
            r.solid(x - 0.4f, aisleD0, x + 0.4f, aisleD1)
            // placa do corredor pendurada
            A.m(Mt.METAL, 1f); A.box(x, FL + 3.6f, r.Zi(aisleD0 + 0.6f), 0.02f, 1.2f, 0.02f, C("#9E9E9E"))
            A.m(Mt.PLAIN); A.box(x, FL + 2.8f, r.Zi(aisleD0 + 0.6f), 1.1f, 0.42f, 0.05f, brand, false); A.box(x, FL + 2.8f, r.Zi(aisleD0 + 0.6f), 0.5f, 0.2f, 0.06f, C("#FFFFFF"), false)
            ai++
            x += if (big) 2.6f else gw + 2f
            if (!big) break
        }
        // hortifrúti perto da entrada: bancas inclinadas com frutas
        val hx0 = r.x1 - (if (big) 6.2f else 2.6f)
        if (hx0 > r.x0 + 2f) {
            val nb = if (big) 3 else 1
            for (k in 0 until nb) {
                val bx = hx0 + k * 1.9f + 0.9f
                val bd = ckD + 2.6f
                if (bx > r.x1 - 0.8f) break
                fruitStand(A, L(bx, r.Zi(bd), 0f, r.fz), k, rng)
                r.solid(bx - 0.85f, bd - 0.55f, bx + 0.85f, bd + 0.55f)
            }
            // balança
            A.m(Mt.METAL, 1f); A.box(hx0 + 0.2f, FL + 0.95f, r.Zi(ckD + 1.4f), 0.35f, 0.08f, 0.3f, C("#ECEFF1"))
            A.box(hx0 + 0.2f, FL + 0.45f, r.Zi(ckD + 1.4f), 0.3f, 0.9f, 0.3f, C("#B0BEC5"))
        }
        // fundo: geladeiras abertas de laticínios, freezers, açougue/padaria (no supermercado)
        val fridges = max(1, ((r.w - 2.5f) / 1.35f).toInt())
        for (k in 0 until fridges) {
            val fx = r.x0 + 0.9f + k * 1.35f
            if (big && k >= fridges / 2 && fx < r.x1 - 5f) {
                if (k == fridges / 2) butcher(A, L(fx + 1.2f, r.Zi(r.depth - 0.55f), 0f, r.fz), rng)
                if (fx < r.x1 - 5f) continue
            }
            openFridge(A, L(fx, r.Zi(r.depth - 0.45f), 0f, r.fz), rng)
        }
        r.solid(r.x0, r.depth - 1.0f, r.x1, r.depth)
        if (big) {
            // freezers horizontais com tampa de vidro no meio do fundo
            for (k in 0 until 3) {
                val fx = r.cx - 3f + k * 2.2f
                val fd = r.depth - 2.4f
                A.m(Mt.METAL, 1f); A.box(fx, FL + 0.42f, r.Zi(fd), 2.0f, 0.84f, 0.9f, C("#ECEFF1"))
                A.m(Mt.PLAIN); for (i in 0 until 6) A.box(fx - 0.8f + i * 0.32f, FL + 0.8f, r.Zi(fd), 0.28f, 0.06f, 0.7f, rng.pick(arrayOf(C("#FFFFFF"), C("#81D4FA"), C("#FFAB91"), C("#C5E1A5"))))
                A.m(Mt.GLASS); A.al = 0.35f; A.box(fx, FL + 0.86f, r.Zi(fd), 1.95f, 0.02f, 0.85f, C("#E1F5FE")); A.al = 1f
                r.solid(fx - 1f, fd - 0.5f, fx + 1f, fd + 0.5f)
            }
        }
        if (name == "CONVENIÊNCIA") {
            // máquina de café e estufa de salgados no balcão
            val l = L(r.x1 - 0.5f, r.Zi(r.depth * 0.5f), -1f, 0f)
            A.m(Mt.WOOD, 1f); lb(A, l, 0f, FL + 0.45f, 0f, 2.0f, 0.9f, 0.6f, C("#ECEFF1"))
            A.m(Mt.METAL, 1f); lb(A, l, -0.5f, FL + 1.15f, 0.05f, 0.5f, 0.5f, 0.45f, C("#212121")); lb(A, l, 0.4f, FL + 1.1f, 0f, 0.7f, 0.4f, 0.45f, C("#B0BEC5"))
            A.m(Mt.PLAIN); for (i in 0 until 4) lsph(A, l, 0.15f + i * 0.15f, FL + 1.0f, -0.05f, 0.06f, C("#E0A050"), 0.04f, 6)
            r.g.solid(l.ox - 0.35f, l.oz - 1.05f, l.ox + 0.35f, l.oz + 1.05f)
        }
        // cartazes de oferta nas paredes
        for (k in 0 until 3) poster(A, L(r.x0 + 0.03f, r.Zi(aisleD0 + k * 1.8f), 1f, 0f), 0f, FL + 2.6f, 0.9f, 0.55f, C("#FFEB3B"), C("#D32F2F"))
    }

    private fun cart(b: MB, l: L) {
        b.m(Mt.METAL, 1f)
        val c = C("#B0BEC5")
        lb(b, l, 0f, FL + 0.62f, 0f, 0.55f, 0.03f, 0.85f, c)
        for (s in floatArrayOf(-0.27f, 0.27f)) lb(b, l, s, FL + 0.8f, 0f, 0.02f, 0.4f, 0.85f, c)
        lb(b, l, 0f, FL + 0.8f, -0.42f, 0.55f, 0.4f, 0.02f, c); lb(b, l, 0f, FL + 0.8f, 0.42f, 0.55f, 0.4f, 0.02f, c)
        b.m(Mt.PLAIN); lb(b, l, 0f, FL + 1.02f, 0.5f, 0.55f, 0.04f, 0.04f, C("#D32F2F"))
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-0.22f, 0.22f)) for (t in floatArrayOf(-0.35f, 0.35f)) { lb(b, l, s, FL + 0.32f, t, 0.02f, 0.6f, 0.02f, c); lb(b, l, s, FL + 0.05f, t, 0.04f, 0.1f, 0.1f, C("#212121")) }
        lb(b, l, 0f, FL + 0.2f, 0f, 0.5f, 0.02f, 0.75f, c)
    }

    /** Fileira de mercadorias (textura de embalagens) de [y0] a [y0]+[h], centro (x,z), tamanho sx × sz. */
    fun goods(b: MB, x: Float, y0: Float, z: Float, sx: Float, h: Float, sz: Float, tint: Int = C("#FFFFFF"), mat: Int = Mt.GOODS) {
        val sc = 0.5f / h
        b.m(mat, sc, 0.37f * (x + z), -y0 * sc)
        b.box(x, y0 + h / 2, z, sx, h, sz, tint)
    }

    private fun gondola(b: MB, x: Float, z: Float, len: Float, rng: City.Rng, fz: Float, alongX: Boolean = false) {
        // base, costas, 4 prateleiras por lado com mercadorias, faixa de preços, pontas de gôndola com promoção
        // a = ao longo da gôndola, c = de um lado ao outro
        fun bx(a: Float, y: Float, c: Float, sa: Float, sy: Float, sc: Float, col: Int, lit: Boolean = true) =
            if (alongX) b.box(x + a, y, z + c, sa, sy, sc, col, lit) else b.box(x + c, y, z + a, sc, sy, sa, col, lit)
        fun gd(a: Float, y0: Float, c: Float, sa: Float, h: Float, sc: Float, tint: Int = C("#FFFFFF")) =
            if (alongX) goods(b, x + a, y0, z + c, sa, h, sc, tint) else goods(b, x + c, y0, z + a, sc, h, sa, tint)
        b.m(Mt.METAL, 1f)
        bx(0f, FL + 0.1f, 0f, len, 0.2f, 0.92f, C("#8A8F94"))
        bx(0f, FL + 1.0f, 0f, len, 1.8f, 0.06f, C("#DADDE0"))
        bx(0f, FL + 1.92f, 0f, len, 0.06f, 0.1f, C("#B0B5BA"))
        for (k in 0..3) bx(0f, FL + 0.3f + k * 0.42f, 0f, len, 0.025f, 0.92f, C("#ECEEF0"))
        for (k in 0..3) for (side in floatArrayOf(-1f, 1f)) {
            gd(0f, FL + 0.315f + k * 0.42f, side * 0.24f, len - 0.06f, 0.34f, 0.38f, if (rng.chance(0.3f)) C("#F2F2F2") else C("#FFFFFF"))
            b.m(Mt.PLAIN); bx(0f, FL + 0.29f + k * 0.42f, side * 0.462f, len, 0.045f, 0.006f, C("#FFF59D"), false)
            b.m(Mt.METAL, 1f)
        }
        gd(0f, FL + 0.2f, 0f, len - 0.06f, 0.1f, 0.86f, C("#DDDDDD"))
        for (e in floatArrayOf(-1f, 1f)) {
            val ea = e * (len / 2 + 0.25f)
            b.m(Mt.METAL, 1f); bx(ea, FL + 0.1f, 0f, 0.45f, 0.2f, 0.92f, C("#8A8F94")); bx(ea - e * 0.2f, FL + 0.95f, 0f, 0.05f, 1.7f, 0.92f, C("#DADDE0"))
            for (k in 0 until 3) { b.m(Mt.METAL, 1f); bx(ea, FL + 0.3f + k * 0.45f, 0f, 0.45f, 0.025f, 0.92f, C("#ECEEF0")); gd(ea + e * 0.02f, FL + 0.315f + k * 0.45f, 0f, 0.38f, 0.36f, 0.86f) }
            b.m(Mt.PLAIN); bx(ea, FL + 1.75f, 0f, 0.04f, 0.3f, 0.92f, C("#FFEB3B"), false); bx(ea + e * 0.025f, FL + 1.75f, 0f, 0.01f, 0.14f, 0.6f, C("#D32F2F"), false)
        }
    }

    private fun fruitStand(b: MB, l: L, k: Int, rng: City.Rng) {
        b.m(Mt.WOOD, 1f)
        lb(b, l, 0f, FL + 0.4f, 0f, 1.7f, 0.8f, 1.0f, C("#8D6E63"))
        // engradados inclinados (dois degraus)
        lb(b, l, 0f, FL + 0.85f, 0.15f, 1.6f, 0.1f, 0.45f, C("#A1887F"))
        lb(b, l, 0f, FL + 1.05f, -0.25f, 1.6f, 0.1f, 0.4f, C("#A1887F"))
        b.m(Mt.PLAIN)
        val kinds = arrayOf(C("#D32F2F"), C("#FB8C00"), C("#FDD835"), C("#7CB342"), C("#6A1B9A"), C("#F57F17"))
        for (row in 0 until 2) for (bin in 0 until 3) {
            val c = kinds[(k * 3 + bin + row) % kinds.size]
            for (i in 0 until 4) for (j in 0 until 2)
                lsph(b, l, -0.6f + bin * 0.55f + i * 0.1f - 0.15f, FL + (if (row == 0) 0.96f else 1.16f), (if (row == 0) 0.05f else -0.33f) + j * 0.12f, 0.055f, if (rng.chance(0.2f)) shade(c, -25) else c, 0.05f, 6)
        }
        b.m(Mt.PLAIN); for (bin in 0 until 3) lb(b, l, -0.55f + bin * 0.55f, FL + 1.32f, -0.48f, 0.3f, 0.12f, 0.01f, C("#FFFFFF"), false)
    }

    private fun openFridge(b: MB, l: L, rng: City.Rng) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 1.0f, 0f, 1.3f, 2.0f, 0.8f, C("#ECEFF1"))
        lb(b, l, 0f, FL + 1.0f, -0.36f, 1.2f, 1.8f, 0.1f, C("#37474F"))
        b.m(Mt.PLAIN)
        for (k in 0 until 4) {
            lb(b, l, 0f, FL + 0.3f + k * 0.42f, -0.42f, 1.2f, 0.02f, 0.06f, C("#CFD8DC"))
            goods(b, l.wx(0f, -0.3f), FL + 0.31f + k * 0.42f, l.wz(0f, -0.3f), if (l.alongX) 1.18f else 0.3f, 0.3f, if (l.alongX) 0.3f else 1.18f, C("#F4F8FF"))
            b.m(Mt.PLAIN)
        }
        lb(b, l, 0f, FL + 2.05f, -0.4f, 1.3f, 0.12f, 0.02f, C("#1E88E5"), false)
    }

    private fun butcher(b: MB, l: L, rng: City.Rng) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.5f, 0f, 2.6f, 1.0f, 0.9f, C("#ECEFF1"))
        b.m(Mt.PLAIN)
        for (i in 0 until 10) lb(b, l, -1.1f + i * 0.24f, FL + 1.04f, -0.05f, 0.2f, 0.05f, 0.3f, rng.pick(arrayOf(C("#C62828"), C("#E57373"), C("#B71C1C"), C("#FFCDD2"))))
        b.m(Mt.GLASS); b.al = 0.35f; lb(b, l, 0f, FL + 1.2f, -0.35f, 2.55f, 0.35f, 0.02f, C("#E1F5FE")); b.al = 1f
        b.m(Mt.PLAIN); lb(b, l, 0f, FL + 2.6f, 0.4f, 2.0f, 0.4f, 0.03f, C("#B71C1C"), false)
    }

    // ============================================================ farmácia

    private fun pharmacy(r: Room) {
        val A = r.A; val rng = r.rng
        val green = C("#1E9E5A")
        // prateleiras de vidro nas laterais com caixinhas
        for (sx in floatArrayOf(r.x0 + 0.25f, r.x1 - 0.25f)) {
            var d = 1.4f
            while (d < r.depth - 3f) {
                val l = L(sx, r.Zi(d), if (sx < r.cx) 1f else -1f, 0f)
                A.m(Mt.WOOD, 1f); lb(A, l, 0f, FL + 1.1f, 0.12f, 1.2f, 2.2f, 0.04f, C("#FFFFFF"))
                for (k in 0 until 5) { lb(A, l, 0f, FL + 0.2f + k * 0.42f, 0f, 1.2f, 0.03f, 0.35f, C("#FAFAFA")) }
                for (k in 0 until 5) goods(A, l.wx(0f, -0.02f), FL + 0.215f + k * 0.42f, l.wz(0f, -0.02f), if (l.alongX) 1.16f else 0.26f, 0.2f, if (l.alongX) 0.26f else 1.16f, C("#FFFFFF"))
                d += 1.25f
            }
            r.g.solid(sx - 0.3f, min(r.Zi(1.3f), r.Zi(r.depth - 3f)), sx + 0.3f, max(r.Zi(1.3f), r.Zi(r.depth - 3f)))
        }
        // gôndola central de higiene/beleza
        if (r.w > 5f) { gondola(A, r.cx, r.Zi(r.depth * 0.42f), min(3.2f, r.depth - 5.5f), rng, r.fz); r.solid(r.cx - 0.5f, r.depth * 0.42f - 1.9f, r.cx + 0.5f, r.depth * 0.42f + 1.9f) }
        // balcão do farmacêutico com estante de remédios atrás
        val bw = min(r.w - 1.5f, 4.5f)
        val lb0 = r.toDoor(r.cx, r.depth - 1.6f)
        A.m(Mt.WOOD, 1f); lb(A, lb0, 0f, FL + 0.55f, 0f, bw, 1.1f, 0.6f, C("#FFFFFF")); A.m(Mt.PLAIN); lb(A, lb0, 0f, FL + 0.85f, -0.305f, bw, 0.15f, 0.01f, green, false)
        A.m(Mt.GLASS); A.al = 0.35f; lb(A, lb0, 0f, FL + 1.45f, 0f, bw, 0.6f, 0.02f, C("#E0F7FA")); A.al = 1f
        computer(A, L(lb0.wx(-bw / 4, 0f), lb0.wz(-bw / 4, 0f), -lb0.fx, -lb0.fz), 0f, FL + 1.1f, 0f)
        r.solid(r.cx - bw / 2, r.depth - 1.95f, r.cx + bw / 2, r.depth - 1.25f)
        val ls = r.toDoor(r.cx, r.depth - 0.25f)
        A.m(Mt.WOOD, 1f); lb(A, ls, 0f, FL + 1.2f, 0.05f, bw + 0.4f, 2.4f, 0.1f, C("#F5F5F5"))
        for (k in 0 until 6) { A.m(Mt.WOOD, 1f); lb(A, ls, 0f, FL + 0.28f + k * 0.36f, -0.08f, bw + 0.3f, 0.02f, 0.2f, C("#FAFAFA")); goods(A, ls.wx(0f, -0.08f), FL + 0.29f + k * 0.36f, ls.wz(0f, -0.08f), if (ls.alongX) bw + 0.2f else 0.16f, 0.18f, if (ls.alongX) 0.16f else bw + 0.2f, C("#FFFFFF")) }
        // cruz verde luminosa e medidor de pressão
        lb(A, r.toDoor(r.cx, r.depth - 0.08f), 0f, FL + 3.0f, 0f, 0.8f, 0.26f, 0.04f, green, false); lb(A, r.toDoor(r.cx, r.depth - 0.08f), 0f, FL + 3.0f, 0f, 0.26f, 0.8f, 0.04f, green, false)
        val lp = L(r.x1 - 0.6f, r.Zi(1.2f), -1f, 0f)
        A.m(Mt.METAL, 1f); lb(A, lp, 0f, FL + 0.6f, 0f, 0.6f, 1.2f, 0.5f, C("#ECEFF1")); A.m(Mt.FABRIC, 1f); lb(A, lp, 0f, FL + 0.5f, -0.45f, 0.5f, 0.08f, 0.45f, C("#1E88E5"))
        A.m(Mt.PLAIN); lb(A, lp, 0f, FL + 1.0f, -0.255f, 0.25f, 0.15f, 0.01f, C("#B2FF59"), false)
        r.g.solid(lp.ox - 0.3f, lp.oz - 0.35f, lp.ox + 0.3f, lp.oz + 0.35f)
    }

    // ============================================================ banco / câmbio

    private fun bank(r: Room, name: String) {
        val A = r.A; val rng = r.rng
        val navy = C("#14306B"); val gold = C("#C9A227")
        // guichês de caixa com vidro e divisórias
        val nT = max(2, min(5, ((r.w - 2f) / 1.8f).toInt()))
        val tw = nT * 1.8f
        val td = r.depth - 2.2f
        val lt = r.toDoor(r.cx, td)
        A.m(Mt.WOOD, 1f); lb(A, lt, 0f, FL + 0.55f, 0f, tw, 1.1f, 0.7f, C("#5D4037"))
        A.m(Mt.STONE, 1f); lb(A, lt, 0f, FL + 1.12f, 0f, tw + 0.1f, 0.05f, 0.8f, C("#F5F5F5"))
        A.m(Mt.GLASS); A.al = 0.3f; lb(A, lt, 0f, FL + 1.75f, 0.1f, tw, 1.2f, 0.03f, C("#E0F2F1")); A.al = 1f
        A.m(Mt.METAL, 1f)
        for (k in 0..nT) lb(A, lt, -tw / 2 + k * 1.8f, FL + 1.75f, 0.1f, 0.05f, 1.25f, 0.05f, C("#B0BEC5"))
        for (k in 0 until nT) {
            val sx = -tw / 2 + 0.9f + k * 1.8f
            computer(A, L(lt.wx(sx, 0.2f), lt.wz(sx, 0.2f), -lt.fx, -lt.fz), 0f, FL + 1.15f, 0f)
            CityGeo.officeChair(A, L(lt.wx(sx, 0.9f), lt.wz(sx, 0.9f), lt.fx, lt.fz), navy)
            A.m(Mt.PLAIN); lb(A, lt, sx, FL + 2.5f, 0.15f, 0.3f, 0.2f, 0.04f, navy, false); lb(A, lt, sx, FL + 2.5f, 0.125f, 0.12f, 0.12f, 0.01f, gold, false)
        }
        r.solid(r.cx - tw / 2, td - 0.4f, r.cx + tw / 2, td + 0.4f)
        // painel de senha
        A.m(Mt.METAL, 1f); lb(A, r.toDoor(r.x0 + 1.5f, r.depth - 0.08f), 0f, FL + 2.6f, 0f, 1.2f, 0.5f, 0.06f, C("#111111"))
        A.m(Mt.PLAIN); lb(A, r.toDoor(r.x0 + 1.5f, r.depth - 0.12f), 0f, FL + 2.6f, 0f, 1.0f, 0.34f, 0.01f, C("#FF1744"), false)
        // fila com pedestais e fita
        val qd = td - 2.0f
        var qx = r.cx - min(3f, r.w / 3f)
        A.m(Mt.METAL, 1f)
        val posts = 5
        for (k in 0 until posts) {
            val px = qx + k * 1.4f
            if (r.nearDoor(px, qd)) continue
            A.cyl(px, FL, r.Zi(qd), 0.15f, 0.15f, 0.03f, gold, true, 10); A.cyl(px, FL, r.Zi(qd), 0.025f, 0.025f, 0.95f, gold, true, 8); ball(A, px, FL + 0.97f, r.Zi(qd), 0.04f, gold, 0.04f, 6)
            if (k < posts - 1) { A.m(Mt.FABRIC, 1f); A.box(px + 0.7f, FL + 0.85f, r.Zi(qd), 1.35f, 0.06f, 0.01f, C("#B71C1C")); A.m(Mt.METAL, 1f) }
        }
        // caixas eletrônicos numa parede lateral
        for (k in 0 until min(4, ((r.depth - 4f) / 1.1f).toInt())) {
            CityGeo.atm(A, L(r.x0 + 0.4f, r.Zi(1.6f + k * 1.1f), 1f, 0f))
            r.g.solid(r.x0, r.Zi(1.6f + k * 1.1f) - 0.4f, r.x0 + 0.8f, r.Zi(1.6f + k * 1.1f) + 0.4f)
        }
        // mesa do gerente e espera
        if (r.w > 7f) {
            val mx = r.x1 - 1.6f; val md = r.depth * 0.42f
            CityGeo.desk(A, L(mx, r.Zi(md), -1f, 0f), C("#5D4037"), navy)
            CityGeo.chair(A, L(mx - 1.0f, r.Zi(md - 0.3f), 1f, 0f), C("#5D4037"), navy); CityGeo.chair(A, L(mx - 1.0f, r.Zi(md + 0.3f), 1f, 0f), C("#5D4037"), navy)
            r.solid(mx - 1.3f, md - 0.7f, mx + 0.8f, md + 0.7f)
            CityGeo.sofa(A, L(r.x1 - 0.6f, r.Zi(md + 2.2f), -1f, 0f), 1.8f, C("#455A64"))
            r.g.solid(r.x1 - 1.1f, r.Zi(md + 2.2f) - 1f, r.x1, r.Zi(md + 2.2f) + 1f)
            CityGeo.plant(A, r.x1 - 0.5f, r.Zi(0.7f), 1.3f, rng)
        }
        // salas grandes: ilhas de atendimento (mesa + 2 cadeiras do cliente) e sofás de espera
        if (r.depth > 11f && r.w > 12f) {
            grid(r, 2.4f, td - 3.2f, 3.4f, 3.0f, 2.4f) { x, d, i ->
                if (i % 3 == 2) {
                    CityGeo.sofa(A, L(x, r.Zi(d + 0.4f), 0f, r.inF), 2.0f, C("#455A64")); CityGeo.coffeeTable(A, L(x, r.Zi(d - 0.5f), 0f, r.inF), C("#5D4037"))
                    r.solid(x - 1.1f, d - 0.9f, x + 1.1f, d + 0.9f)
                } else {
                    CityGeo.desk(A, L(x, r.Zi(d), 0f, r.fz), C("#6D4C41"), navy)
                    for (s0 in floatArrayOf(-0.35f, 0.35f)) CityGeo.chair(A, L(x + s0, r.Zi(d - 0.75f), 0f, r.inF), C("#3E2723"), C("#90A4AE"))
                    A.m(Mt.PLAIN); A.box(x + 0.45f, FL + 0.79f, r.Zi(d), 0.22f, 0.08f, 0.06f, gold)
                    r.solid(x - 0.75f, d - 1.0f, x + 0.75f, d + 1.0f)
                }
            }
        }
        // porta-cofre redonda na parede do fundo
        val lv = r.toDoor(r.x1 - 1.4f, r.depth - 0.06f)
        lb(A, lv, 0f, FL + 1.1f, 0f, 1.6f, 1.9f, 0.05f, C("#90A4AE"))
        lb(A, lv, 0f, FL + 1.1f, -0.06f, 1.2f, 1.2f, 0.12f, C("#B0BEC5"))
        lb(A, lv, 0f, FL + 1.1f, -0.14f, 0.3f, 0.3f, 0.06f, C("#78909C"))
        lb(A, lv, 0f, FL + 1.1f, -0.18f, 0.7f, 0.05f, 0.04f, gold); lb(A, lv, 0f, FL + 1.1f, -0.18f, 0.05f, 0.7f, 0.04f, gold)
        if (name == "CASA DE CÂMBIO") {
            // quadro de cotações
            A.m(Mt.METAL, 1f); lb(A, r.toDoor(r.cx, r.depth - 0.06f), 0f, FL + 2.9f, 0f, 2.4f, 0.9f, 0.05f, C("#111111"))
            A.m(Mt.PLAIN); for (i in 0 until 4) lb(A, r.toDoor(r.cx, r.depth - 0.1f), 0f, FL + 2.6f + i * 0.2f, 0f, 2.1f, 0.1f, 0.01f, arrayOf(C("#00E676"), C("#FFEA00"), C("#00E676"), C("#FF5252"))[i], false)
        }
    }

    // ============================================================ academia

    private fun gym(r: Room) {
        val A = r.A; val rng = r.rng
        val orange = C("#FF8A00")
        // espelho na parede lateral inteira
        A.m(Mt.METAL, 1f); A.box(r.x0 + 0.03f, FL + 1.4f, r.cz, 0.03f, 2.2f, r.depth - 1.5f, C("#DCEFF5"))
        // esteiras e bicicletas viradas para a vitrine
        val nT = max(2, min(6, ((r.w - 2f) / 1.0f).toInt()))
        for (k in 0 until nT) {
            val x = r.x0 + 1.0f + k * 1.0f
            if (r.nearDoor(x, 1.6f)) continue
            if (k % 3 == 2) bike(A, L(x, r.Zi(1.9f), 0f, r.fz)) else CityGeo.treadmill(A, L(x, r.Zi(2.0f), 0f, r.fz))
            r.solid(x - 0.45f, 1.0f, x + 0.45f, 3.0f)
        }
        // área de pesos: bancos, barras, halteres, anilhas
        val wd = 4.5f
        if (r.depth > 7f) {
            for (k in 0 until min(3, ((r.w - 3f) / 2.4f).toInt())) {
                CityGeo.weightBench(A, L(r.x0 + 1.6f + k * 2.4f, r.Zi(wd), 1f, 0f).let { L(it.ox, it.oz, 0f, r.fz) })
                r.solid(r.x0 + 1.0f + k * 2.4f, wd - 0.8f, r.x0 + 2.2f + k * 2.4f, wd + 0.8f)
            }
        }
        CityGeo.dumbbells(A, L(r.x1 - 0.4f, r.Zi(r.depth * 0.5f), -1f, 0f))
        r.g.solid(r.x1 - 0.7f, r.Zi(r.depth * 0.5f) - 1.3f, r.x1, r.Zi(r.depth * 0.5f) + 1.3f)
        // suporte de anilhas
        val lp = L(r.x1 - 0.5f, r.Zi(r.depth * 0.5f + 2f), -1f, 0f)
        A.m(Mt.METAL, 1f); lb(A, lp, 0f, FL + 0.6f, 0f, 0.6f, 1.2f, 0.06f, C("#212121"))
        for (i in 0 until 4) lcyl(A, L(lp.wx(0f, -0.08f - i * 0.05f), lp.wz(0f, -0.08f - i * 0.05f), 0f, 1f), 0f, FL + 0.3f + (i % 2) * 0.45f, 0f, 0.22f - i * 0.03f, 0.22f - i * 0.03f, 0.04f, C("#1A1A1A"), 12)
        // gaiola de agachamento (rack) no fundo
        val lr = r.toDoor(r.x0 + 1.6f, r.depth - 1.0f)
        A.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-0.7f, 0.7f)) for (t in floatArrayOf(-0.6f, 0.6f)) lb(A, lr, s, FL + 1.15f, t, 0.08f, 2.3f, 0.08f, C("#212121"))
        for (s in floatArrayOf(-0.7f, 0.7f)) lb(A, lr, s, FL + 2.3f, 0f, 0.08f, 0.08f, 1.3f, C("#212121"))
        lb(A, lr, 0f, FL + 1.4f, -0.6f, 2.2f, 0.04f, 0.04f, C("#BDBDBD"))
        for (s in floatArrayOf(-0.95f, 0.95f)) lb(A, lr, s, FL + 1.4f, -0.6f, 0.06f, 0.45f, 0.45f, C("#111111"))
        r.solid(r.x0 + 0.8f, r.depth - 1.8f, r.x0 + 2.4f, r.depth - 0.2f)
        // salas grandes: aparelhos em fileiras (esteiras, bicicletas, estação de polia, bancos)
        if (r.depth > 10f && r.w > 10f) {
            grid(r, 6.4f, r.depth - 2.6f, 2.2f, 2.6f, 1.6f) { x, d, i ->
                when (i % 4) {
                    0 -> { CityGeo.treadmill(A, L(x, r.Zi(d), 0f, r.fz)); r.solid(x - 0.45f, d - 1f, x + 0.45f, d + 1f) }
                    1 -> { bike(A, L(x, r.Zi(d), 0f, r.fz)); r.solid(x - 0.35f, d - 0.6f, x + 0.35f, d + 0.6f) }
                    2 -> { cableMachine(A, L(x, r.Zi(d), 0f, r.fz)); r.solid(x - 0.8f, d - 0.6f, x + 0.8f, d + 0.6f) }
                    else -> { CityGeo.weightBench(A, L(x, r.Zi(d), 1f, 0f)); r.solid(x - 0.9f, d - 0.5f, x + 0.9f, d + 0.5f) }
                }
            }
        }
        // saco de pancada pendurado
        val bx = r.x1 - 1.4f; val bd = r.depth - 1.2f
        A.m(Mt.METAL, 1f); A.box(bx, FL + 3.9f, r.Zi(bd), 0.04f, 0.9f, 0.04f, C("#424242"))
        A.m(Mt.FABRIC, 1f); A.cyl(bx, FL + 0.7f, r.Zi(bd), 0.2f, 0.2f, 1.1f, C("#B71C1C"), true, 12)
        r.solid(bx - 0.3f, bd - 0.3f, bx + 0.3f, bd + 0.3f)
        // tapete de borracha nas áreas de peso e kettlebells
        A.m(Mt.RUG, 0.3f); A.box(r.cx, FL + 0.006f, r.Zi(wd), r.w - 1.0f, 0.012f, 2.6f, C("#212121"))
        A.m(Mt.METAL, 1f); for (i in 0 until 6) ball(A, r.x0 + 1.0f + i * 0.35f, FL + 0.13f, r.Zi(r.depth - 2.2f), 0.12f, arrayOf(C("#1A1A1A"), C("#FF8A00"), C("#1565C0"))[i % 3], 0.12f, 8)
        // recepção com catraca e armários
        val lc = L(r.x1 - 0.7f, r.Zi(1.3f), -1f, 0f)
        A.m(Mt.WOOD, 1f); lb(A, lc, 0f, FL + 0.55f, 0f, 1.4f, 1.1f, 0.5f, C("#212121")); A.m(Mt.PLAIN); lb(A, lc, 0f, FL + 0.8f, -0.255f, 1.4f, 0.12f, 0.01f, orange, false)
        computer(A, L(lc.ox + 0.3f, lc.oz, 1f, 0f), 0f, FL + 1.1f, 0f)
        r.g.solid(lc.ox - 0.3f, lc.oz - 0.75f, lc.ox + 0.3f, lc.oz + 0.75f)
        A.m(Mt.METAL, 1f); A.box(r.x1 - 1.9f, FL + 0.5f, r.Zi(1.3f), 0.25f, 1.0f, 0.4f, C("#B0BEC5")); A.box(r.x1 - 1.9f, FL + 0.9f, r.Zi(1.3f) - r.inF * 0.3f, 0.04f, 0.04f, 0.5f, C("#ECEFF1"))
        for (k in 0 until 6) { val ld = r.depth * 0.5f + 3.2f + k * 0.42f; if (ld < r.depth - 0.3f) A.box(r.x1 - 0.2f, FL + 0.95f, r.Zi(ld), 0.36f, 1.9f, 0.4f, if (k % 2 == 0) C("#455A64") else C("#546E7A")) }
        for (k in 0 until 2) poster(A, L(r.x1 - 0.03f, r.Zi(3.0f + k * 1.2f), -1f, 0f), 0f, FL + 2.3f, 0.7f, 0.9f, C("#212121"), orange)
    }

    private fun cableMachine(b: MB, l: L) {
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-0.7f, 0.7f)) { lb(b, l, s, FL + 1.1f, 0.3f, 0.1f, 2.2f, 0.1f, C("#263238")); lb(b, l, s, FL + 0.03f, 0f, 0.14f, 0.06f, 0.9f, C("#263238")) }
        lb(b, l, 0f, FL + 2.2f, 0.3f, 1.5f, 0.1f, 0.1f, C("#263238"))
        lb(b, l, 0f, FL + 0.55f, 0.32f, 0.3f, 0.9f, 0.14f, C("#111111"))   // pilha de pesos
        lb(b, l, 0f, FL + 1.6f, 0.32f, 0.02f, 1.1f, 0.02f, C("#BDBDBD"))
        lb(b, l, 0f, FL + 1.05f, 0.32f, 0.36f, 0.02f, 0.18f, C("#FF8A00"))
        b.m(Mt.FABRIC, 1f); lb(b, l, 0f, FL + 0.48f, -0.25f, 0.4f, 0.08f, 0.45f, C("#111111")); lb(b, l, 0f, FL + 0.85f, 0.05f, 0.4f, 0.6f, 0.08f, C("#111111"))
    }

    private fun bike(b: MB, l: L) {
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, FL + 0.05f, 0f, 0.5f, 0.1f, 1.1f, C("#212121"))
        lb(b, l, 0f, FL + 0.45f, -0.35f, 0.1f, 0.8f, 0.1f, C("#37474F"))
        lb(b, l, 0f, FL + 0.4f, 0.25f, 0.08f, 0.7f, 0.08f, C("#37474F"))
        lb(b, l, 0f, FL + 0.38f, -0.4f, 0.06f, 0.5f, 0.5f, C("#FF8A00"))   // volante (roda)
        b.m(Mt.FABRIC, 1f); lb(b, l, 0f, FL + 0.78f, 0.25f, 0.2f, 0.06f, 0.28f, C("#111111"))
        b.m(Mt.METAL, 1f); lb(b, l, 0f, FL + 1.05f, -0.4f, 0.45f, 0.04f, 0.04f, C("#212121"))
        lb(b, l, 0f, FL + 1.12f, -0.38f, 0.22f, 0.14f, 0.03f, C("#263238"))
    }

    // ============================================================ hotel

    private fun hotel(r: Room) {
        val A = r.A; val rng = r.rng
        val gold = C("#C9A227"); val wood = C("#4E342E")
        // tapete grande do lobby
        CityGeo.rug(A, r.cx - min(4f, r.w / 3), min(r.Zi(2f), r.Zi(r.depth - 3.5f)), r.cx + min(4f, r.w / 3), max(r.Zi(2f), r.Zi(r.depth - 3.5f)), C("#7B1F2B"))
        // recepção de mármore e madeira com parede de chaves
        val rw = min(5f, r.w * 0.4f)
        val lr = r.toDoor(r.cx, r.depth - 2.0f)
        A.m(Mt.WOOD, 1f); lb(A, lr, 0f, FL + 0.55f, 0f, rw, 1.1f, 0.7f, wood)
        A.m(Mt.STONE, 0.6f); lb(A, lr, 0f, FL + 1.13f, 0f, rw + 0.1f, 0.06f, 0.8f, C("#F2EEE6"))
        A.m(Mt.METAL, 1f); lb(A, lr, 0f, FL + 0.95f, -0.36f, rw, 0.04f, 0.02f, gold)
        computer(A, L(lr.wx(-rw / 4, 0.1f), lr.wz(-rw / 4, 0.1f), -lr.fx, -lr.fz), 0f, FL + 1.16f, 0f)
        A.m(Mt.METAL, 1f); lb(A, lr, rw / 4, FL + 1.2f, 0f, 0.12f, 0.05f, 0.12f, gold); ball(A, lr.wx(rw / 4, 0f), FL + 1.27f, lr.wz(rw / 4, 0f), 0.04f, gold, 0.03f, 6)   // campainha
        r.solid(r.cx - rw / 2, r.depth - 2.45f, r.cx + rw / 2, r.depth - 1.55f)
        val lk = r.toDoor(r.cx, r.depth - 0.08f)
        A.m(Mt.WOOD, 1f); lb(A, lk, 0f, FL + 1.8f, 0f, rw, 1.4f, 0.1f, C("#3E2723"))
        A.m(Mt.METAL, 1f); for (i in 0 until 8) for (j in 0 until 4) lb(A, lk, -rw / 2 + 0.35f + i * (rw - 0.7f) / 7, FL + 1.3f + j * 0.32f, -0.07f, 0.04f, 0.1f, 0.02f, gold)
        // sofás em volta de mesinhas, poltronas
        for (s in floatArrayOf(-1f, 1f)) {
            val sx = r.cx + s * min(3.2f, r.w / 3.5f)
            val sd = 3.0f
            if (sx < r.x0 + 1.5f || sx > r.x1 - 1.5f) continue
            CityGeo.sofa(A, L(sx, r.Zi(sd + 1.0f), 0f, r.fz), 2.0f, C("#3E4A61"))
            CityGeo.coffeeTable(A, L(sx, r.Zi(sd), 0f, r.fz), wood)
            CityGeo.armchair(A, L(sx - 1.4f, r.Zi(sd), 1f, 0f), C("#8D6E63")); CityGeo.armchair(A, L(sx + 1.4f, r.Zi(sd), -1f, 0f), C("#8D6E63"))
            r.solid(sx - 1.8f, sd - 0.5f, sx + 1.8f, sd + 1.5f)
        }
        // salas grandes: colunas revestidas e mais grupos de estar com tapetes e luminárias de piso
        if (r.w > 12f && r.depth > 10f) {
            for (sx in floatArrayOf(r.x0 + r.w * 0.25f, r.x0 + r.w * 0.75f)) for (sd in floatArrayOf(r.depth * 0.3f, r.depth * 0.62f)) {
                A.m(Mt.STONE, 0.5f); A.box(sx, FL + 2.2f, r.Zi(sd), 0.6f, 4.4f, 0.6f, C("#EFE8DC"))
                A.m(Mt.METAL, 1f); A.box(sx, FL + 0.08f, r.Zi(sd), 0.7f, 0.16f, 0.7f, gold); A.box(sx, FL + 4.2f, r.Zi(sd), 0.7f, 0.12f, 0.7f, gold)
                r.solid(sx - 0.35f, sd - 0.35f, sx + 0.35f, sd + 0.35f)
            }
            for ((gi, gx) in floatArrayOf(r.x0 + 3.0f, r.x1 - 3.0f).withIndex()) {
                val gd = r.depth * 0.46f
                CityGeo.rug(A, gx - 1.8f, min(r.Zi(gd - 1.4f), r.Zi(gd + 1.4f)), gx + 1.8f, max(r.Zi(gd - 1.4f), r.Zi(gd + 1.4f)), C("#C9B48A"))
                CityGeo.sofa(A, L(gx, r.Zi(gd + 0.9f), 0f, r.fz), 2.2f, if (gi == 0) C("#2F4858") else C("#5B3A29"))
                CityGeo.coffeeTable(A, L(gx, r.Zi(gd), 0f, r.fz), wood)
                CityGeo.armchair(A, L(gx, r.Zi(gd - 1.0f), 0f, r.inF), C("#C9A227"))
                CityGeo.floorLamp(A, gx + 1.5f, r.Zi(gd + 0.9f))
                r.solid(gx - 1.3f, gd - 1.4f, gx + 1.3f, gd + 1.4f)
            }
        }
        // lustre de cristal (bolinhas) no meio
        val H = r.g.H
        H.m(Mt.METAL, 1f); H.box(r.cx, FL + 3.95f, r.Zi(r.depth * 0.45f), 0.03f, 0.7f, 0.03f, gold)
        H.m(Mt.PLAIN)
        for (ring in 0 until 3) for (k in 0 until 10) {
            val a = k * 0.628f + ring * 0.3f; val rr = 0.55f - ring * 0.15f
            ball(H, r.cx + cos(a) * rr, FL + 3.4f - ring * 0.18f, r.Zi(r.depth * 0.45f) + sin(a) * rr, 0.05f, C("#FFF8E1"), 0.07f, 6, false)
        }
        // carrinho de malas dourado, elevadores, vasos altos
        val bx = r.x0 + 1.2f; val bd = 1.8f
        A.m(Mt.METAL, 1f); A.box(bx, FL + 0.15f, r.Zi(bd), 0.7f, 0.05f, 1.1f, C("#B71C1C"))
        for (s in floatArrayOf(-0.33f, 0.33f)) A.box(bx + s, FL + 0.9f, r.Zi(bd), 0.03f, 1.5f, 0.03f, gold)
        A.box(bx, FL + 1.65f, r.Zi(bd), 0.72f, 0.03f, 0.03f, gold)
        A.m(Mt.FABRIC, 1f); A.box(bx, FL + 0.45f, r.Zi(bd), 0.45f, 0.55f, 0.3f, C("#1A237E")); A.box(bx + 0.05f, FL + 0.82f, r.Zi(bd) + 0.1f, 0.35f, 0.2f, 0.25f, C("#5D4037"))
        r.g.solid(bx - 0.4f, r.Zi(bd) - 0.6f, bx + 0.4f, r.Zi(bd) + 0.6f)
        for (k in 0 until 2) {
            val ex = r.x1 - 1.2f - k * 1.6f
            val le = r.toDoor(ex, r.depth - 0.12f)
            A.m(Mt.METAL, 1f); lb(A, le, 0f, FL + 1.15f, 0f, 1.3f, 2.3f, 0.06f, gold); lb(A, le, 0f, FL + 1.1f, -0.04f, 1.1f, 2.2f, 0.03f, C("#B8C0C8")); lb(A, le, 0f, FL + 1.1f, -0.06f, 0.02f, 2.2f, 0.02f, C("#78909C"))
        }
        for (s in floatArrayOf(r.x0 + 0.5f, r.x1 - 0.5f)) CityGeo.plant(A, s, r.Zi(0.7f), 1.6f, rng)
        // piano de cauda (quando cabe)
        if (r.w > 12f) {
            val px = r.x0 + 2.2f; val pd = r.depth - 3.2f
            A.m(Mt.WOOD, 1f); A.box(px, FL + 0.85f, r.Zi(pd), 1.4f, 0.3f, 1.8f, C("#111111"))
            for (s in floatArrayOf(-0.6f, 0.6f)) for (t in floatArrayOf(-0.7f, 0.7f)) A.box(px + s, FL + 0.35f, r.Zi(pd) + t, 0.08f, 0.7f, 0.08f, C("#111111"))
            A.m(Mt.PLAIN); A.box(px, FL + 0.75f, r.Zi(pd - 0.95f), 1.3f, 0.05f, 0.15f, C("#FAFAFA"))
            r.solid(px - 0.8f, pd - 1.2f, px + 0.8f, pd + 1f)
        }
    }

    // ============================================================ escola

    private fun school(r: Room) {
        val A = r.A; val rng = r.rng
        // lousa verde no fundo com bordas de madeira e mesa do professor
        val lbd = r.toDoor(r.cx, r.depth - 0.06f)
        A.m(Mt.WOOD, 1f); lb(A, lbd, 0f, FL + 1.6f, 0f, min(r.w - 2f, 4.6f), 1.3f, 0.05f, C("#6D4C41"))
        A.m(Mt.PLAIN); lb(A, lbd, 0f, FL + 1.6f, -0.03f, min(r.w - 2f, 4.6f) - 0.12f, 1.18f, 0.01f, C("#2E5E3E"))
        for (i in 0 until 4) lb(A, lbd, -1.2f + i * 0.5f, FL + 1.9f - i * 0.12f, -0.036f, 0.6f, 0.02f, 0.003f, C("#E8F5E9"), false)
        A.m(Mt.WOOD, 1f); lb(A, lbd, 0f, FL + 0.93f, -0.06f, min(r.w - 2f, 4.6f), 0.03f, 0.08f, C("#6D4C41"))
        val lt = r.toDoor(r.cx + 1.5f, r.depth - 1.3f)
        A.m(Mt.WOOD, 1f); lb(A, lt, 0f, FL + 0.75f, 0f, 1.3f, 0.05f, 0.7f, C("#8D6E63")); lb(A, lt, 0f, FL + 0.37f, 0.3f, 1.3f, 0.74f, 0.04f, C("#6D4C41"))
        for (s in floatArrayOf(-0.6f, 0.6f)) lb(A, lt, s, FL + 0.37f, 0f, 0.04f, 0.74f, 0.66f, C("#6D4C41"))
        A.m(Mt.PLAIN); lb(A, lt, -0.3f, FL + 0.82f, 0f, 0.3f, 0.08f, 0.22f, C("#1565C0")); ball(A, lt.wx(0.4f, 0f), FL + 0.92f, lt.wz(0.4f, 0f), 0.13f, C("#42A5F5"), 0.13f, 8)   // livros e globo
        CityGeo.chair(A, L(lt.wx(0f, 0.6f), lt.wz(0f, 0.6f), -lt.fx, -lt.fz), C("#6D4C41"), C("#455A64"))
        r.solid(r.cx + 0.7f, r.depth - 1.8f, r.cx + 2.3f, r.depth - 0.8f)
        // carteiras em grade viradas para a lousa
        val cols = max(2, min(6, ((r.w - 2f) / 1.1f).toInt()))
        val rows = max(2, min(5, ((r.depth - 4.5f) / 1.1f).toInt()))
        for (i in 0 until cols) for (j in 0 until rows) {
            val x = r.cx - (cols - 1) * 0.55f + i * 1.1f
            val d = r.depth - 2.8f - j * 1.1f
            if (r.nearDoor(x, d)) continue
            val l = r.toBack(x, d)
            A.m(Mt.WOOD, 1f); lb(A, l, 0f, FL + 0.7f, -0.1f, 0.6f, 0.03f, 0.42f, C("#D7B98E"))
            A.m(Mt.METAL, 1f); for (s in floatArrayOf(-0.27f, 0.27f)) lb(A, l, s, FL + 0.35f, -0.1f, 0.03f, 0.7f, 0.38f, C("#455A64"))
            CityGeo.chair(A, L(l.wx(0f, 0.35f), l.wz(0f, 0.35f), l.fx, l.fz).let { L(it.ox, it.oz, -l.fx, -l.fz) }, C("#455A64"), C("#1E88E5"))
            if ((i + j) % 3 == 0) { A.m(Mt.PLAIN); lb(A, l, 0.1f, FL + 0.725f, -0.1f, 0.25f, 0.02f, 0.18f, rng.pick(arrayOf(C("#FFFFFF"), C("#FFEB3B"), C("#EF5350")))) }
            r.solid(x - 0.32f, d - 0.3f, x + 0.32f, d + 0.6f)
        }
        if (r.w > 13f) {
            // segunda sala ao lado (divisória com porta e visor), com lousa e carteiras próprias
            val wx = r.x0 + r.w * 0.36f
            A.m(Mt.PLASTER, 0.5f)
            A.box(wx, FL + 1.5f, r.Zi(r.depth * 0.5f + 0.9f), 0.12f, 3.0f, r.depth - 1.8f, C("#EEF2E6"))
            r.g.solid(wx - 0.1f, min(r.Zi(1.8f), r.Zi(r.depth)), wx + 0.1f, max(r.Zi(1.8f), r.Zi(r.depth)))
            val c2 = (r.x0 + wx) / 2
            val lb2 = L(r.x0 + 0.06f, r.Zi(r.depth * 0.55f), 1f, 0f)
            A.m(Mt.WOOD, 1f); lb(A, lb2, 0f, FL + 1.6f, 0f, 3.6f, 1.2f, 0.05f, C("#6D4C41")); A.m(Mt.PLAIN); lb(A, lb2, 0f, FL + 1.6f, -0.03f, 3.48f, 1.08f, 0.01f, C("#2E5E3E"))
            for (i in 0 until 3) for (j in 0 until 4) {
                val x = r.x0 + 2.0f + i * 1.15f; val d = r.depth * 0.55f - 1.6f + j * 1.05f
                if (x > wx - 0.6f) continue
                val l = L(x, r.Zi(d), -1f, 0f)
                A.m(Mt.WOOD, 1f); lb(A, l, 0f, FL + 0.7f, 0f, 0.6f, 0.03f, 0.42f, C("#D7B98E")); A.m(Mt.METAL, 1f); for (s0 in floatArrayOf(-0.27f, 0.27f)) lb(A, l, s0, FL + 0.35f, 0f, 0.03f, 0.7f, 0.38f, C("#455A64"))
                CityGeo.chair(A, L(x + 0.4f, r.Zi(d), -1f, 0f), C("#455A64"), C("#EF5350"))
                r.g.solid(x - 0.3f, r.Zi(d) - 0.35f, x + 0.6f, r.Zi(d) + 0.35f)
            }
            poster(A, L(wx - 0.08f, r.Zi(r.depth * 0.3f), -1f, 0f), 0f, FL + 1.8f, 0.9f, 0.7f, C("#FFE0B2"), C("#E65100"))
            CityGeo.bookshelf(A, L(r.x0 + 0.25f, r.Zi(r.depth - 1.0f), 1f, 0f), C("#8D6E63"), rng)
        }
        // cartazes, mapa, armário e lixeiras de reciclagem
        for (k in 0 until 3) poster(A, L(r.x0 + 0.03f, r.Zi(1.6f + k * 1.4f), 1f, 0f), 0f, FL + 1.8f, 0.8f, 0.6f, arrayOf(C("#FFF59D"), C("#B3E5FC"), C("#C8E6C9"))[k], arrayOf(C("#F44336"), C("#3F51B5"), C("#4CAF50"))[k])
        CityGeo.bookshelf(A, L(r.x1 - 0.25f, r.Zi(r.depth - 1.2f), -1f, 0f), C("#8D6E63"), rng)
        r.g.solid(r.x1 - 0.45f, r.Zi(r.depth - 1.2f) - 0.55f, r.x1, r.Zi(r.depth - 1.2f) + 0.55f)
        for (k in 0 until 3) bin(A, r.x1 - 0.35f, r.Zi(1.2f + k * 0.5f), arrayOf(C("#1565C0"), C("#C62828"), C("#2E7D32"))[k])
        // armários de alunos (lockers) na parede da porta
        for (k in 0 until 6) {
            val lx = r.x0 + 0.5f + k * 0.42f
            if (abs(lx - r.doorX) < 1.1f) continue
            val ll = r.toBack(lx, 0.25f)
            A.m(Mt.METAL, 1f); lb(A, ll, 0f, FL + 0.95f, 0f, 0.4f, 1.9f, 0.35f, if (k % 2 == 0) C("#1E88E5") else C("#1976D2"))
            A.m(Mt.PLAIN); lb(A, ll, 0.12f, FL + 1.0f, 0.18f, 0.03f, 0.1f, 0.01f, C("#ECEFF1"))
        }
    }

    // ============================================================ polícia

    private fun police(r: Room) {
        val A = r.A; val rng = r.rng
        val navy = C("#0E2A5C")
        // balcão de atendimento alto com vidro
        val bw = min(r.w - 3f, 5f)
        val lb0 = r.toDoor(r.cx, 3.2f)
        A.m(Mt.WOOD, 1f); lb(A, lb0, 0f, FL + 0.6f, 0f, bw, 1.2f, 0.7f, C("#37474F"))
        A.m(Mt.PLAIN); lb(A, lb0, 0f, FL + 0.95f, -0.355f, bw, 0.18f, 0.01f, navy, false)
        A.m(Mt.GLASS); A.al = 0.3f; lb(A, lb0, 0f, FL + 1.75f, 0f, bw, 1.0f, 0.03f, C("#E3F2FD")); A.al = 1f
        computer(A, L(lb0.wx(0f, 0.2f), lb0.wz(0f, 0.2f), -lb0.fx, -lb0.fz), 0f, FL + 1.22f, 0f)
        r.solid(r.cx - bw / 2, 2.8f, r.cx + bw / 2, 3.6f)
        // bandeiras e brasão na parede atrás do balcão
        A.m(Mt.METAL, 1f); for (s in floatArrayOf(-1f, 1f)) A.cyl(r.cx + s * (bw / 2 + 0.5f), FL, r.Zi(4.2f), 0.02f, 0.02f, 2.2f, C("#C9A227"), true, 6)
        A.m(Mt.FABRIC, 1f); A.box(r.cx - bw / 2 - 0.25f, FL + 1.8f, r.Zi(4.2f), 0.5f, 0.35f, 0.01f, C("#2E7D32")); A.box(r.cx + bw / 2 + 0.75f, FL + 1.8f, r.Zi(4.2f), 0.5f, 0.35f, 0.01f, C("#1565C0"))
        // cadeiras de espera
        beamSeats(A, L(r.x0 + 2f, r.Zi(1.6f), 1f, 0f).let { L(it.ox, it.oz, 0f, r.inF) }.let { L(r.x0 + 0.45f, r.Zi(2.2f), 1f, 0f) }, 4, navy)
        r.g.solid(r.x0, min(r.Zi(1f), r.Zi(3.4f)), r.x0 + 0.8f, max(r.Zi(1f), r.Zi(3.4f)))
        // mesas de trabalho com computadores e arquivos
        var d = 4.6f
        while (d < r.depth - 3f) {
            for (k in 0 until min(3, ((r.w - 2f) / 2.5f).toInt())) {
                val x = r.x0 + 1.6f + k * 2.5f
                CityGeo.desk(A, L(x, r.Zi(d), 0f, r.inF), C("#90A4AE"), navy)
                r.solid(x - 0.7f, d - 0.9f, x + 0.7f, d + 0.4f)
            }
            d += 2.2f
        }
        for (k in 0 until 3) { val l = L(r.x1 - 0.35f, r.Zi(4.5f + k * 0.55f), -1f, 0f); A.m(Mt.METAL, 1f); lb(A, l, 0f, FL + 0.7f, 0f, 0.5f, 1.4f, 0.6f, C("#78909C")); A.m(Mt.PLAIN); for (i in 0 until 4) lb(A, l, 0f, FL + 0.25f + i * 0.33f, -0.305f, 0.12f, 0.03f, 0.01f, C("#CFD8DC")) }
        r.g.solid(r.x1 - 0.7f, min(r.Zi(4.2f), r.Zi(6f)), r.x1, max(r.Zi(4.2f), r.Zi(6f)))
        // cela com grades no fundo
        val cw = min(3.4f, r.w * 0.4f)
        val cxc = r.x1 - cw / 2 - 0.2f
        val cd = r.depth - 2.2f
        A.m(Mt.METAL, 1f)
        var bx = cxc - cw / 2
        while (bx <= cxc + cw / 2 + 0.01f) { A.box(bx, FL + 1.25f, r.Zi(cd), 0.04f, 2.5f, 0.04f, C("#424242")); bx += 0.15f }
        A.box(cxc, FL + 2.5f, r.Zi(cd), cw, 0.08f, 0.08f, C("#424242")); A.box(cxc, FL + 1.2f, r.Zi(cd), cw, 0.06f, 0.06f, C("#424242"))
        A.box(cxc - cw / 2, FL + 1.25f, r.Zi(cd + 1.1f), 0.08f, 2.5f, 2.2f, C("#9E9E9E"))
        A.m(Mt.WOOD, 1f); A.box(cxc, FL + 0.45f, r.Zi(r.depth - 0.4f), cw - 0.3f, 0.08f, 0.6f, C("#9E9E9E"))
        r.solid(cxc - cw / 2 - 0.1f, cd - 0.1f, cxc + cw / 2 + 0.2f, r.depth)
        // quadro de avisos e mapa
        poster(A, L(r.x0 + 0.03f, r.Zi(r.depth - 2f), 1f, 0f), 0f, FL + 1.8f, 1.4f, 0.9f, C("#D7CCC8"), C("#795548"))
        poster(A, L(r.x0 + 0.03f, r.Zi(r.depth - 3.8f), 1f, 0f), 0f, FL + 1.8f, 1.2f, 0.9f, C("#E8F5E9"), C("#1565C0"))
        waterCooler(A, L(r.x0 + 0.35f, r.Zi(4.0f), 1f, 0f))
    }

    // ============================================================ bombeiros

    private fun fire(r: Room) {
        val A = r.A; val rng = r.rng
        val red = C("#C62828")
        // armários abertos com roupas amarelas e capacetes vermelhos
        val n = max(3, min(8, ((r.w - 2f) / 0.9f).toInt()))
        for (k in 0 until n) {
            val x = r.x0 + 0.8f + k * 0.9f
            val l = r.toDoor(x, r.depth - 0.35f)
            A.m(Mt.METAL, 1f); lb(A, l, 0f, FL + 1.0f, 0.05f, 0.85f, 2.0f, 0.05f, C("#90A4AE")); for (s in floatArrayOf(-0.42f, 0.42f)) lb(A, l, s, FL + 1.0f, -0.15f, 0.03f, 2.0f, 0.45f, C("#90A4AE"))
            lb(A, l, 0f, FL + 1.75f, -0.15f, 0.84f, 0.03f, 0.45f, C("#90A4AE"))
            A.m(Mt.FABRIC, 1f); lb(A, l, 0f, FL + 1.1f, -0.15f, 0.55f, 0.85f, 0.25f, C("#FBC02D")); lb(A, l, 0f, FL + 1.1f, -0.28f, 0.56f, 0.06f, 0.01f, C("#E0E0E0")); lb(A, l, 0f, FL + 0.4f, -0.15f, 0.5f, 0.5f, 0.3f, C("#F9A825"))
            A.m(Mt.PLAIN); lsph(A, l, 0f, FL + 1.88f, -0.15f, 0.17f, red, 0.12f, 8)
            A.m(Mt.FABRIC, 1f); lb(A, l, 0f, FL + 0.1f, -0.25f, 0.4f, 0.2f, 0.25f, C("#212121"))   // botas
        }
        r.solid(r.x0, r.depth - 0.8f, r.x0 + 0.8f + n * 0.9f, r.depth)
        // rolos de mangueira, extintores, cano de descida (poste)
        A.m(Mt.FABRIC, 1f)
        for (k in 0 until 4) lcyl(A, L(r.x1 - 0.6f, r.Zi(2f + k * 0.5f), 0f, 1f).let { L(it.ox, it.oz, -1f, 0f) }, 0f, FL, 0f, 0.28f, 0.28f, 0.14f, C("#ECEFF1"), 12)
        r.g.solid(r.x1 - 1f, min(r.Zi(1.7f), r.Zi(3.8f)), r.x1, max(r.Zi(1.7f), r.Zi(3.8f)))
        A.m(Mt.METAL, 1f); A.cyl(r.cx, FL, r.Zi(r.depth * 0.5f), 0.05f, 0.05f, 4.3f, C("#E0E0E0"), true, 10); A.cyl(r.cx, FL, r.Zi(r.depth * 0.5f), 0.5f, 0.5f, 0.06f, C("#212121"), true, 14)
        r.solid(r.cx - 0.15f, r.depth * 0.5f - 0.15f, r.cx + 0.15f, r.depth * 0.5f + 0.15f)
        for (k in 0 until 4) { A.m(Mt.METAL, 1f); A.cyl(r.x0 + 0.4f + k * 0.3f, FL, r.Zi(1.3f), 0.09f, 0.09f, 0.55f, red, true, 10) }
        if (r.depth > 10f) {
            // dormitório com beliches de um lado, sala de TV do outro
            for (k in 0 until min(3, ((r.w * 0.45f) / 1.6f).toInt())) {
                val bx = r.x0 + 1.0f + k * 1.6f; val bd = r.depth * 0.5f + 1.5f
                val l = L(bx, r.Zi(bd), 0f, r.fz)
                for (lv in 0 until 2) { A.m(Mt.METAL, 1f); lb(A, l, 0f, FL + 0.35f + lv * 1.1f, 0f, 0.95f, 0.1f, 2.0f, C("#546E7A")); A.m(Mt.FABRIC, 1f); lb(A, l, 0f, FL + 0.46f + lv * 1.1f, 0f, 0.9f, 0.14f, 1.95f, C("#ECEFF1")); lb(A, l, 0f, FL + 0.55f + lv * 1.1f, -0.3f, 0.92f, 0.06f, 1.3f, red); lb(A, l, 0f, FL + 0.58f + lv * 1.1f, 0.75f, 0.5f, 0.1f, 0.3f, C("#FFFFFF")) }
                A.m(Mt.METAL, 1f); for (s0 in floatArrayOf(-0.46f, 0.46f)) for (t in floatArrayOf(-0.98f, 0.98f)) lb(A, l, s0, FL + 0.9f, t, 0.04f, 1.8f, 0.04f, C("#37474F"))
                r.solid(bx - 0.5f, bd - 1.05f, bx + 0.5f, bd + 1.05f)
            }
            val sx = r.x1 - 2.6f; val sd = r.depth * 0.5f + 1.2f
            CityGeo.sofa(A, L(sx, r.Zi(sd + 0.9f), 0f, r.fz), 2.2f, C("#5D4037")); CityGeo.coffeeTable(A, L(sx, r.Zi(sd), 0f, r.fz), C("#6D4C41"))
            CityGeo.tvUnit(A, L(sx, r.Zi(sd - 1.4f), 0f, r.inF), C("#3E2723"))
            r.solid(sx - 1.2f, sd - 1.6f, sx + 1.2f, sd + 1.4f)
            CityGeo.kitchen(A, L(r.x1 - 1.6f, r.Zi(r.depth - 2.0f), 0f, r.fz).let { L(r.x1 - 0.35f, r.Zi(r.depth * 0.5f - 1.2f), -1f, 0f) }, 2.4f, C("#ECEFF1"), C("#424242"), rng)
            r.g.solid(r.x1 - 0.7f, r.Zi(r.depth * 0.5f - 1.2f) - 1.3f, r.x1, r.Zi(r.depth * 0.5f - 1.2f) + 1.3f)
        }
        // mesa comprida do refeitório e quadro de plantão
        val lt = r.toBack(r.cx + 2f, 2.6f)
        if (r.w > 7f) { CityGeo.diningSet(A, L(lt.ox, lt.oz, 1f, 0f), C("#8D6E63"), 6, red); r.solid(r.cx + 0.6f, 2.0f, r.cx + 3.4f, 3.2f) }
        poster(A, L(r.x0 + 0.03f, r.Zi(3f), 1f, 0f), 0f, FL + 1.8f, 1.4f, 0.9f, C("#FFFFFF"), red)
        A.m(Mt.PLAIN); lb(A, L(r.x0 + 0.04f, r.Zi(5f), 1f, 0f), 0f, FL + 2.6f, 0f, 0.6f, 0.4f, 0.04f, red, false)
    }

    // ============================================================ portaria de prédio / escritórios

    private fun lobby(r: Room, name: String) {
        val A = r.A; val rng = r.rng
        val wood = C("#3E2723")
        // painel de madeira na parede do fundo e balcão do porteiro com monitores de câmera
        A.m(Mt.WOOD, 1f); A.box(r.cx, FL + 1.6f, r.back - r.inF * 0.04f, r.w - 0.4f, 3.2f, 0.04f, C("#6D4C41"))
        val lc = r.toDoor(r.x0 + 2.2f, 2.8f)
        A.m(Mt.WOOD, 1f); lb(A, lc, 0f, FL + 0.55f, 0f, 2.4f, 1.1f, 0.6f, wood)
        A.m(Mt.STONE, 0.8f); lb(A, lc, 0f, FL + 1.12f, 0f, 2.5f, 0.05f, 0.7f, C("#212121"))
        A.m(Mt.METAL, 1f)
        for (i in 0 until 2) for (j in 0 until 2) { lb(A, lc, -0.5f + i * 0.5f, FL + 1.35f + j * 0.3f, 0.2f, 0.46f, 0.28f, 0.04f, C("#111111")); A.m(Mt.PLAIN); lb(A, lc, -0.5f + i * 0.5f, FL + 1.35f + j * 0.3f, 0.177f, 0.42f, 0.24f, 0.004f, C(rng.pick(arrayOf("#37474F", "#455A64", "#263238", "#546E7A"))), false); A.m(Mt.METAL, 1f) }
        CityGeo.officeChair(A, L(lc.wx(0f, 0.75f), lc.wz(0f, 0.75f), lc.fx, lc.fz), C("#212121"))
        r.solid(r.x0 + 0.9f, 2.4f, r.x0 + 3.5f, 3.2f)
        // caixas de correio na parede lateral
        val lm = L(r.x1 - 0.12f, r.Zi(2.5f), -1f, 0f)
        A.m(Mt.METAL, 1f); lb(A, lm, 0f, FL + 1.4f, 0f, 1.6f, 1.2f, 0.25f, C("#8D8D8D"))
        A.m(Mt.PLAIN); for (i in 0 until 6) for (j in 0 until 4) lb(A, lm, -0.65f + i * 0.26f, FL + 0.95f + j * 0.28f, -0.13f, 0.22f, 0.22f, 0.01f, C("#B0B0B0"))
        for (i in 0 until 6) for (j in 0 until 4) lb(A, lm, -0.65f + i * 0.26f, FL + 1.01f + j * 0.28f, -0.137f, 0.12f, 0.02f, 0.004f, C("#424242"), false)
        // sofá, mesinha, espelho e plantas
        CityGeo.sofa(A, L(r.cx + 1f, r.Zi(1.6f), 0f, r.inF).let { L(r.x1 - 0.6f, r.Zi(4.8f), -1f, 0f) }, 2.0f, C("#37474F"))
        r.g.solid(r.x1 - 1.1f, r.Zi(4.8f) - 1f, r.x1, r.Zi(4.8f) + 1f)
        CityGeo.coffeeTable(A, L(r.x1 - 1.6f, r.Zi(4.8f), -1f, 0f), C("#5D4037"))
        CityGeo.mirrorWall(A, r.x0 + 0.04f, r.Zi(4.5f))
        CityGeo.plant(A, r.x0 + 0.5f, r.Zi(0.6f), 1.4f, rng); CityGeo.plant(A, r.x1 - 0.5f, r.Zi(0.6f), 1.4f, rng)
        // elevadores com painel e indicador
        for (k in 0 until 2) {
            val ex = r.cx + 0.8f + k * 1.7f
            if (ex > r.x1 - 0.8f) break
            val le = r.toDoor(ex, r.depth - 0.1f)
            A.m(Mt.METAL, 1f); lb(A, le, 0f, FL + 1.15f, 0f, 1.25f, 2.3f, 0.06f, C("#9E9E9E")); lb(A, le, 0f, FL + 1.1f, -0.04f, 1.1f, 2.2f, 0.03f, C("#CFD8DC")); lb(A, le, 0f, FL + 1.1f, -0.06f, 0.02f, 2.2f, 0.02f, C("#78909C"))
            A.m(Mt.PLAIN); lb(A, le, 0f, FL + 2.45f, -0.04f, 0.3f, 0.12f, 0.01f, C("#FF6E40"), false); lb(A, le, 0.8f, FL + 1.2f, -0.04f, 0.08f, 0.2f, 0.01f, C("#FFECB3"), false)
        }
        if (r.w > 12f && r.depth > 9f) {
            grid(r, 3.6f, r.depth - 3.2f, 5.0f, 3.6f, 3.6f) { x, d, i ->
                if (i % 2 == 0) {
                    CityGeo.rug(A, x - 1.5f, min(r.Zi(d - 1.1f), r.Zi(d + 1.1f)), x + 1.5f, max(r.Zi(d - 1.1f), r.Zi(d + 1.1f)), C("#B0A48C"))
                    CityGeo.sofa(A, L(x, r.Zi(d + 0.7f), 0f, r.fz), 1.9f, C("#455A64")); CityGeo.coffeeTable(A, L(x, r.Zi(d - 0.1f), 0f, r.fz), C("#5D4037"))
                    CityGeo.armchair(A, L(x, r.Zi(d - 0.95f), 0f, r.inF), C("#8D6E63"))
                    r.solid(x - 1.1f, d - 1.3f, x + 1.1f, d + 1.2f)
                } else {
                    A.m(Mt.STONE, 1f); A.box(x, FL + 0.3f, r.Zi(d), 2.2f, 0.6f, 1.0f, C("#9E9E9E")); A.m(Mt.PLAIN); A.box(x, FL + 0.6f, r.Zi(d), 2.0f, 0.02f, 0.8f, C("#4E342E"))
                    for (k in 0 until 3) CityGeo.plant(A, x - 0.7f + k * 0.7f, r.Zi(d), 1.0f, rng, FL + 0.6f)
                    r.solid(x - 1.1f, d - 0.5f, x + 1.1f, d + 0.5f)
                }
            }
        }
        if (name == "ESCRITÓRIOS") {
            // catracas de acesso
            for (k in 0 until 3) { val tx = r.cx - 0.8f + k * 0.8f; A.m(Mt.METAL, 1f); A.box(tx, FL + 0.5f, r.Zi(r.depth - 2.6f), 0.25f, 1.0f, 0.9f, C("#B0BEC5")); A.m(Mt.GLASS); A.al = 0.4f; A.box(tx + 0.3f, FL + 0.7f, r.Zi(r.depth - 2.6f), 0.35f, 0.6f, 0.02f, C("#E1F5FE")); A.al = 1f; r.solid(tx - 0.15f, r.depth - 3.1f, tx + 0.15f, r.depth - 2.1f) }
        }
    }

    // ============================================================ shopping

    private fun mall(r: Room) {
        val A = r.A; val rng = r.rng
        // vitrines de lojas nas paredes laterais e no fundo (fachadas de vidro com letreiro colorido)
        val cols = arrayOf(C("#E91E63"), C("#3F51B5"), C("#009688"), C("#FF9800"), C("#795548"), C("#9C27B0"), C("#F44336"), C("#4CAF50"))
        var x = r.x0 + 0.5f
        var k = 0
        while (x < r.x1 - 4f) {
            val l = r.toDoor(x + 2f, r.depth - 0.3f)
            A.m(Mt.METAL, 1f); lb(A, l, 0f, FL + 3.0f, 0f, 3.9f, 0.5f, 0.2f, C("#424242"))
            A.m(Mt.PLAIN); lb(A, l, 0f, FL + 3.0f, -0.105f, 2.6f, 0.36f, 0.01f, cols[k % cols.size], false)
            A.m(Mt.GLASS); A.al = 0.35f; lb(A, l, 0f, FL + 1.35f, 0f, 3.9f, 2.7f, 0.03f, C("#E0F2F1")); A.al = 1f
            A.m(Mt.FABRIC, 1f); for (i in 0 until 3) { lb(A, l, -1.2f + i * 1.2f, FL + 0.9f, 0.4f, 0.35f, 1.0f, 0.2f, rng.pick(cols)); A.m(Mt.PLAIN); lsph(A, l, -1.2f + i * 1.2f, FL + 1.55f, 0.4f, 0.1f, C("#ECEFF1"), 0.12f, 6); A.m(Mt.FABRIC, 1f) }
            x += 4.2f; k++
        }
        r.solid(r.x0, r.depth - 0.6f, r.x1, r.depth)
        // quiosques no meio, bancos e canteiros com plantas
        var qx = r.x0 + 4f
        while (qx < r.x1 - 3f) {
            val qd = r.depth * 0.5f
            A.m(Mt.WOOD, 1f); A.box(qx, FL + 0.55f, r.Zi(qd), 2.0f, 1.1f, 1.2f, C("#FAFAFA")); A.m(Mt.PLAIN); A.box(qx, FL + 0.8f, r.Zi(qd), 2.02f, 0.14f, 1.22f, rng.pick(cols))
            A.m(Mt.METAL, 1f); A.box(qx, FL + 2.3f, r.Zi(qd), 2.2f, 0.1f, 1.4f, C("#ECEFF1")); for (s in floatArrayOf(-0.95f, 0.95f)) A.box(qx + s, FL + 1.7f, r.Zi(qd), 0.05f, 1.2f, 0.05f, C("#B0BEC5"))
            r.solid(qx - 1.05f, qd - 0.65f, qx + 1.05f, qd + 0.65f)
            // canteiro redondo com árvore e banco em volta
            val px = qx + 5f
            if (px < r.x1 - 2f) {
                A.m(Mt.STONE, 1f); A.cyl(px, FL, r.Zi(qd), 0.9f, 0.9f, 0.45f, C("#BDBDBD"), true, 16)
                A.m(Mt.PLAIN); A.cyl(px, FL + 0.45f, r.Zi(qd), 0.8f, 0.8f, 0.02f, C("#4E342E"), true, 16)
                CityGeo.plant(A, px, r.Zi(qd), 2.2f, rng, FL + 0.45f)
                r.solid(px - 0.9f, qd - 0.9f, px + 0.9f, qd + 0.9f)
            }
            qx += 10f
        }
        // vitrines também nas paredes laterais
        for (side in floatArrayOf(-1f, 1f)) {
            var d = 6f
            var kk = 0
            while (d < r.depth - 4f) {
                val l = L(if (side < 0) r.x0 + 0.3f else r.x1 - 0.3f, r.Zi(d), -side, 0f)
                A.m(Mt.METAL, 1f); lb(A, l, 0f, FL + 3.0f, 0f, 3.9f, 0.5f, 0.2f, C("#424242"))
                A.m(Mt.PLAIN); lb(A, l, 0f, FL + 3.0f, -0.105f, 2.6f, 0.36f, 0.01f, cols[(kk + 3) % cols.size], false)
                A.m(Mt.GLASS); A.al = 0.35f; lb(A, l, 0f, FL + 1.35f, 0f, 3.9f, 2.7f, 0.03f, C("#E0F2F1")); A.al = 1f
                goods(A, l.wx(0f, 0.35f), FL + 0.6f, l.wz(0f, 0.35f), if (l.alongX) 3.2f else 0.3f, 1.4f, if (l.alongX) 0.3f else 3.2f, C("#FFFFFF"), if (kk % 3 == 1) Mt.BOOKS else Mt.GOODS)
                d += 4.3f; kk++
            }
            r.g.solid(if (side < 0) r.x0 else r.x1 - 0.5f, min(r.Zi(5.5f), r.Zi(r.depth - 4f)), if (side < 0) r.x0 + 0.5f else r.x1, max(r.Zi(5.5f), r.Zi(r.depth - 4f)))
        }
        // bancos e canteiros pelo corredor
        if (r.depth > 14f) grid(r, 5.5f, r.depth * 0.5f - 1.5f, 6f, 4.5f, 5f) { x, d, i ->
            if (i % 2 == 0) { bench(A, L(x - 0.9f, r.Zi(d), 0f, r.fz)); bench(A, L(x + 0.9f, r.Zi(d), 0f, r.fz)); r.solid(x - 1.8f, d - 0.3f, x + 1.8f, d + 0.3f) }
            else { A.m(Mt.STONE, 1f); A.box(x, FL + 0.3f, r.Zi(d), 1.6f, 0.6f, 1.6f, C("#BDBDBD")); CityGeo.plant(A, x, r.Zi(d), 1.8f, rng, FL + 0.6f); r.solid(x - 0.85f, d - 0.85f, x + 0.85f, d + 0.85f) }
        }
        if (r.depth > 14f) grid(r, r.depth * 0.5f + 1.5f, r.depth - 4.5f, 7f, 4.5f, 5f) { x, d, i ->
            A.m(Mt.WOOD, 1f); A.box(x, FL + 0.55f, r.Zi(d), 2.0f, 1.1f, 1.2f, C("#FAFAFA")); A.m(Mt.PLAIN); A.box(x, FL + 0.8f, r.Zi(d), 2.02f, 0.14f, 1.22f, cols[(i + 2) % cols.size])
            goods(A, x, FL + 1.1f, r.Zi(d), 1.8f, 0.25f, 1.0f)
            A.m(Mt.METAL, 1f); A.box(x, FL + 2.3f, r.Zi(d), 2.2f, 0.1f, 1.4f, C("#ECEFF1")); for (s0 in floatArrayOf(-0.95f, 0.95f)) A.box(x + s0, FL + 1.7f, r.Zi(d), 0.05f, 1.2f, 0.05f, C("#B0BEC5"))
            r.solid(x - 1.05f, d - 0.65f, x + 1.05f, d + 0.65f)
        }
        // praça de alimentação perto da entrada
        var tx = r.x0 + 2f
        while (tx < r.x1 - 2f) {
            if (!r.nearDoor(tx, 2.5f)) { CityGeo.cafeTable(A, tx, r.Zi(2.6f), rng); r.solid(tx - 0.5f, 2.0f, tx + 0.5f, 3.2f) }
            tx += 2.4f
        }
        // escada rolante
        if (r.w > 14f) {
            val ex = r.x1 - 2.2f
            val l = L(ex, r.Zi(r.depth * 0.5f - 2f), 0f, r.fz)
            A.m(Mt.METAL, 1f)
            for (i in 0 until 14) lb(A, l, 0f, FL + 0.15f + i * 0.28f, 0.3f * i, 1.0f, 0.2f, 0.32f, C("#9E9E9E"))
            for (s in floatArrayOf(-0.55f, 0.55f)) for (i in 0 until 14) lb(A, l, s, FL + 0.55f + i * 0.28f, 0.3f * i, 0.08f, 0.9f, 0.32f, C("#ECEFF1"))
            r.g.solid(ex - 0.65f, min(l.oz, l.wz(0f, 4.2f)), ex + 0.65f, max(l.oz, l.wz(0f, 4.2f)))
        }
    }

    // ============================================================ restaurante

    private fun restaurant(r: Room) {
        val A = r.A; val rng = r.rng
        val wine = C("#8E1B1B")
        // bar com garrafas iluminadas no fundo
        val bw = min(r.w - 3f, 4.5f)
        val lbar = r.toDoor(r.x0 + 0.6f + bw / 2, r.depth - 1.5f)
        A.m(Mt.WOOD, 1f); lb(A, lbar, 0f, FL + 0.55f, 0f, bw, 1.1f, 0.6f, C("#3E2723")); A.m(Mt.STONE, 0.8f); lb(A, lbar, 0f, FL + 1.12f, 0f, bw + 0.1f, 0.05f, 0.7f, C("#212121"))
        A.m(Mt.METAL, 1f); for (i in 0 until 4) { lcyl(A, lbar, -bw / 2 + 0.5f + i * (bw - 1f) / 3, FL, -0.65f, 0.05f, 0.05f, 0.75f, C("#9E9E9E"), 6); lcyl(A, lbar, -bw / 2 + 0.5f + i * (bw - 1f) / 3, FL + 0.75f, -0.65f, 0.2f, 0.2f, 0.06f, wine, 10) }
        r.solid(r.x0 + 0.6f, r.depth - 1.9f, r.x0 + 0.6f + bw, r.depth - 1.1f)
        val lsh = r.toDoor(r.x0 + 0.6f + bw / 2, r.depth - 0.12f)
        A.m(Mt.WOOD, 1f); lb(A, lsh, 0f, FL + 1.8f, 0f, bw, 1.6f, 0.06f, C("#4E342E"))
        for (k in 0 until 3) lb(A, lsh, 0f, FL + 1.2f + k * 0.5f, -0.12f, bw, 0.03f, 0.22f, C("#6D4C41"))
        A.m(Mt.GLASS); A.al = 0.85f
        for (k in 0 until 3) { var p = -bw / 2 + 0.15f; while (p < bw / 2 - 0.1f) { lcyl(A, lsh, p, FL + 1.22f + k * 0.5f, -0.12f, 0.035f, 0.03f, 0.3f, rng.pick(arrayOf(C("#1B5E20"), C("#4E342E"), C("#B71C1C"), C("#F9A825"), C("#E0F2F1"))), 6); p += 0.13f } }
        A.al = 1f
        // janela de passagem da cozinha
        A.m(Mt.METAL, 1f); lb(A, r.toDoor(r.x1 - 1.5f, r.depth - 0.08f), 0f, FL + 1.4f, 0f, 1.8f, 0.8f, 0.04f, C("#B0BEC5")); A.m(Mt.PLAIN); lb(A, r.toDoor(r.x1 - 1.5f, r.depth - 0.11f), 0f, FL + 1.4f, 0f, 1.6f, 0.6f, 0.01f, C("#FFF3E0"), false)
        // mesas com toalha branca, taças, pratos e cadeiras estofadas (grade uniforme, no máximo ~28 mesas)
        val area = (r.w - 2.4f) * (r.depth - 5f)
        val cell = max(2.6f, kotlin.math.sqrt(area / 30f))
        val H = r.g.H
        grid(r, 1.6f, r.depth - 3.2f, cell, cell * 1.08f) { x, d, _ ->
            val l = L(x, r.Zi(d), 0f, r.fz)
            A.m(Mt.WOOD, 1f); lb(A, l, 0f, FL + 0.37f, 0f, 0.06f, 0.74f, 0.06f, C("#3E2723"))
            A.m(Mt.FABRIC, 1f); lb(A, l, 0f, FL + 0.75f, 0f, 0.95f, 0.03f, 0.95f, C("#FAFAFA")); lb(A, l, 0f, FL + 0.6f, 0f, 1.0f, 0.3f, 1.0f, C("#F5F5F5"))
            A.m(Mt.PLAIN)
            for (s0 in floatArrayOf(-1f, 1f)) {
                lcyl(A, l, 0f, FL + 0.77f, s0 * 0.28f, 0.12f, 0.12f, 0.01f, C("#FFFFFF"), 10)
                A.m(Mt.GLASS); A.al = 0.5f; lcyl(A, l, 0.2f, FL + 0.77f, s0 * 0.3f, 0.03f, 0.04f, 0.16f, C("#E1F5FE"), 6); A.al = 1f; A.m(Mt.PLAIN)
                CityGeo.chair(A, L(l.wx(0f, s0 * 0.7f), l.wz(0f, s0 * 0.7f), l.fx * s0, l.fz * s0), C("#3E2723"), wine)
            }
            lcyl(A, l, 0f, FL + 0.77f, 0f, 0.035f, 0.03f, 0.12f, C("#FFF8E1"), 8)   // vela
            r.solid(x - 0.55f, d - 0.9f, x + 0.55f, d + 0.9f)
            // pendente de luz sobre a mesa (H)
            H.m(Mt.METAL, 1f); H.box(x, FL + 3.4f, r.Zi(d), 0.01f, 1.8f, 0.01f, C("#212121")); H.cyl(x, FL + 2.3f, r.Zi(d), 0.22f, 0.08f, 0.2f, C("#212121"), true, 10)
            H.m(Mt.PLAIN); H.cyl(x, FL + 2.28f, r.Zi(d), 0.2f, 0.2f, 0.02f, C("#FFE0A0"), false, 10)
        }
        // quadros e plantas
        for (k in 0 until 3) poster(A, L(r.x1 - 0.03f, r.Zi(2f + k * 1.6f), -1f, 0f), 0f, FL + 1.9f, 0.8f, 0.6f, C("#FBE3B0"), wine)
        CityGeo.plant(A, r.x0 + 0.5f, r.Zi(0.6f), 1.5f, rng)
    }
}
