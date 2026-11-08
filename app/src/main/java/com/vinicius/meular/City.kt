package com.vinicius.meular

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Typeface
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Etapa 121: a cidade em volta da casa.
 * Grade de 5 × 5 quarteirões (a casa é o do meio), ruas de mão dupla com calçada, faixas, semáforos e placas de rua.
 * Quarteirões: praça, comércio com letreiros, supermercado, posto, hospital, prédios no centro, escola, polícia, bombeiros, casas.
 * Vivo: carros que respeitam semáforo, fila e o jogador; pedestres andando nas calçadas.
 * Cada quarteirão e cada rua é um pedaço de malha separado (a câmera só desenha o que vê e o que está perto).
 */
object City {
    const val ROAD = 16f      // largura total da rua (calçadas incluídas)
    const val SIDE = 3.5f     // calçada
    const val CURB = 0.15f    // altura da calçada / dos lotes
    const val BLK = 48f       // quarteirão

    class Chunk(val mesh: Mesh, val x0: Float, val z0: Float, val x1: Float, val z1: Float, val h: Float)

    @Volatile var on = false
        private set
    var chunks: List<Chunk> = emptyList()
        private set
    /** Brilho dos semáforos: 4 malhas, uma por fase. */
    var lightMeshes: Array<Mesh?> = arrayOfNulls(4)
        private set

    // faixas (a, b) das ruas e dos quarteirões nos dois eixos
    private var bandX = FloatArray(0); private var bandZ = FloatArray(0)   // pares a,b
    private var blkX = FloatArray(0); private var blkZ = FloatArray(0)
    var X0 = 0f; var X1 = 0f; var Z0 = 0f; var Z1 = 0f
        private set
    private var lotX0 = 0f; private var lotX1 = 0f; private var lotZ0 = 0f; private var lotZ1 = 0f   // quarteirão da casa

    private val solids = ArrayList<FloatArray>()   // retângulos (x0, z0, x1, z1) que bloqueiam quem anda

    // ------------------------------------------------------------ letreiros

    private val SIGNS = arrayOf(
        Triple("HOSPITAL", "#FFFFFF", "#D62828"), Triple("FARMÁCIA", "#1E9E5A", "#FFFFFF"), Triple("PADARIA", "#F4E1C1", "#7A4A1E"),
        Triple("SUPERMERCADO", "#D62828", "#FFFFFF"), Triple("LANCHONETE", "#FFD23F", "#C0392B"), Triple("PIZZARIA", "#1F5E3A", "#FFFFFF"),
        Triple("BANCO", "#14306B", "#F2C14E"), Triple("ACADEMIA", "#151515", "#FF8A00"), Triple("SALÃO DE BELEZA", "#F7A1C4", "#FFFFFF"),
        Triple("POSTO", "#0F7A3D", "#FFE14D"), Triple("CONVENIÊNCIA", "#FFFFFF", "#0F7A3D"), Triple("ESCOLA", "#1F6FD1", "#FFFFFF"),
        Triple("POLÍCIA", "#0E2A5C", "#FFFFFF"), Triple("CAFÉ", "#4A2C1A", "#F6E7CF"), Triple("LIVRARIA", "#2C3E50", "#F1C40F"),
        Triple("PET SHOP", "#25A8E0", "#FFFFFF"), Triple("ÓTICA", "#FFFFFF", "#222222"), Triple("SORVETERIA", "#FFC6DA", "#C2185B"),
        Triple("MODA", "#000000", "#FFFFFF"), Triple("RESTAURANTE", "#8E1B1B", "#FBE3B0"), Triple("BOMBEIROS", "#C62828", "#FFFFFF"),
        Triple("HOTEL", "#2B2B2B", "#E8C26E"), Triple("ELETRÔNICOS", "#1565C0", "#FFFFFF"), Triple("FLORICULTURA", "#7CB342", "#FFFFFF"),
        Triple("PRONTO-SOCORRO", "#D62828", "#FFFFFF"), Triple("ESTACIONAMENTO", "#1F4FA8", "#FFFFFF"), Triple("AV. BRASIL", "#1B7F3B", "#FFFFFF"),
        Triple("R. DAS FLORES", "#1B7F3B", "#FFFFFF"), Triple("AV. DO SOL", "#1B7F3B", "#FFFFFF"), Triple("R. DOS IPÊS", "#1B7F3B", "#FFFFFF"),
        Triple("PRAÇA CENTRAL", "#5D4037", "#FFF3D6"), Triple("ACADEMIA AO AR LIVRE", "#2E7D32", "#FFFFFF"))
    private const val S_HOSP = 0; private const val S_FARM = 1; private const val S_PAD = 2; private const val S_SUPER = 3
    private const val S_LANCH = 4; private const val S_PIZZA = 5; private const val S_BANCO = 6; private const val S_ACAD = 7
    private const val S_SALAO = 8; private const val S_POSTO = 9; private const val S_CONV = 10; private const val S_ESC = 11
    private const val S_POL = 12; private const val S_CAFE = 13; private const val S_LIVR = 14; private const val S_PET = 15
    private const val S_OTICA = 16; private const val S_SORV = 17; private const val S_MODA = 18; private const val S_REST = 19
    private const val S_BOMB = 20; private const val S_HOTEL = 21; private const val S_ELET = 22; private const val S_FLOR = 23
    private const val S_PS = 24; private const val S_ESTAC = 25; private const val S_STREET0 = 26; private const val S_PRACA = 30

    /** Atlas 1024 × 1024: 2 colunas × 16 linhas de placas de 512 × 64. */
    fun signBitmap(): Bitmap {
        val bmp = Bitmap.createBitmap(1024, 1024, Bitmap.Config.ARGB_8888)
        val cv = Canvas(bmp)
        val p = Paint(Paint.ANTI_ALIAS_FLAG)
        p.typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD)
        for (i in 0 until 32) {
            val cx = (i % 2) * 512f; val cy = (i / 2) * 64f
            val s = SIGNS.getOrNull(i) ?: Triple("", "#FFFFFF", "#000000")
            p.style = Paint.Style.FILL
            p.color = C(s.second)
            cv.drawRect(cx, cy, cx + 512f, cy + 64f, p)
            p.color = shade(C(s.second), -40)
            cv.drawRect(cx, cy, cx + 512f, cy + 4f, p); cv.drawRect(cx, cy + 60f, cx + 512f, cy + 64f, p)
            p.color = C(s.third)
            p.textSize = 44f
            var w = p.measureText(s.first)
            if (w > 470f) { p.textSize = 44f * 470f / w; w = p.measureText(s.first) }
            val fm = p.fontMetrics
            cv.drawText(s.first, cx + 256f - w / 2f, cy + 32f - (fm.ascent + fm.descent) / 2f, p)
        }
        return bmp
    }

    // ------------------------------------------------------------ montagem

    private class Rng(seed: Int) {
        private var s = seed.toLong() * 2654435761L + 12345L
        fun f(): Float { s = (s * 6364136223846793005L + 1442695040888963407L); return ((s ushr 33) and 0xFFFFFFL).toFloat() / 0xFFFFFF.toFloat() }
        fun r(a: Float, b: Float) = a + (b - a) * f()
        fun i(n: Int) = (f() * n).toInt().coerceIn(0, n - 1)
        fun <T> pick(a: Array<T>): T = a[i(a.size)]
    }

    fun clear() { on = false; carMeshes.forEach { it?.release() }; pedBody.forEach { it?.release() }; pedLeg.forEach { it?.release() }; pedArm.forEach { it?.release() }; chunks.forEach { it.mesh.release() }; chunks = emptyList(); lightMeshes.forEach { it?.release() }; lightMeshes = arrayOfNulls(4); solids.clear(); cars.clear(); peds.clear() }

    fun build(gw: Int, gh: Int) {
        clear()
        val W = gw.toFloat(); val H = gh.toFloat()
        lotX0 = -10f; lotX1 = W + 10f; lotZ0 = -22f; lotZ1 = H + 9f
        // quarteirões: 2 de cada lado do da casa
        blkX = floatArrayOf(lotX0 - 2 * ROAD - 2 * BLK, lotX0 - 2 * ROAD - BLK, lotX0 - ROAD - BLK, lotX0 - ROAD, lotX0, lotX1,
            lotX1 + ROAD, lotX1 + ROAD + BLK, lotX1 + 2 * ROAD + BLK, lotX1 + 2 * ROAD + 2 * BLK)
        blkZ = floatArrayOf(lotZ0 - 2 * ROAD - 2 * BLK, lotZ0 - 2 * ROAD - BLK, lotZ0 - ROAD - BLK, lotZ0 - ROAD, lotZ0, lotZ1,
            lotZ1 + ROAD, lotZ1 + ROAD + BLK, lotZ1 + 2 * ROAD + BLK, lotZ1 + 2 * ROAD + 2 * BLK)
        bandX = FloatArray(12); bandZ = FloatArray(12)
        for (k in 0 until 6) {
            bandX[k * 2] = if (k == 0) blkX[0] - ROAD else blkX[k * 2 - 1]
            bandX[k * 2 + 1] = if (k == 5) blkX[9] + ROAD else blkX[k * 2]
            bandZ[k * 2] = if (k == 0) blkZ[0] - ROAD else blkZ[k * 2 - 1]
            bandZ[k * 2 + 1] = if (k == 5) blkZ[9] + ROAD else blkZ[k * 2]
        }
        X0 = bandX[0]; X1 = bandX[11]; Z0 = bandZ[0]; Z1 = bandZ[11]

        val out = ArrayList<Chunk>()
        roads(out)
        // tipos dos quarteirões [i][j] (i = x, j = z; j = 3 é o lado de lá da avenida da frente)
        val type = arrayOf(
            arrayOf("res", "apt", "res", "gas", "hosp"),
            arrayOf("res", "school", "res", "shops", "down"),
            arrayOf("park", "res", "", "praca", "down"),
            arrayOf("apt", "police", "res", "super", "down"),
            arrayOf("res", "apt", "res", "res", "hotel"))
        for (i in 0 until 5) for (j in 0 until 5) {
            val t = type[i][j]
            if (t.isEmpty()) continue
            val x0 = blkX[i * 2]; val x1 = blkX[i * 2 + 1]; val z0 = blkZ[j * 2]; val z1 = blkZ[j * 2 + 1]
            val b = MB(); val fl = Flora.Batch()
            val rng = Rng(i * 31 + j * 7 + 3)
            val h = when (t) {
                "res" -> residential(b, fl, rng, x0, z0, x1, z1)
                "apt" -> apartments(b, fl, rng, x0, z0, x1, z1)
                "down" -> downtown(b, fl, rng, x0, z0, x1, z1)
                "hotel" -> downtown(b, fl, rng, x0, z0, x1, z1, true)
                "shops" -> shops(b, fl, rng, x0, z0, x1, z1)
                "super" -> supermarket(b, fl, rng, x0, z0, x1, z1)
                "gas" -> gasStation(b, fl, rng, x0, z0, x1, z1)
                "hosp" -> hospital(b, fl, rng, x0, z0, x1, z1)
                "praca" -> praca(b, fl, rng, x0, z0, x1, z1)
                "park" -> park(b, fl, rng, x0, z0, x1, z1)
                "school" -> school(b, fl, rng, x0, z0, x1, z1)
                "police" -> police(b, fl, rng, x0, z0, x1, z1)
                else -> 1f
            }
            val m = b.toMesh(true)
            out.add(Chunk(Mesh(m.parts + fl.build()), x0, z0, x1, z1, h))
        }
        // anel verde em volta da cidade (o chão de fora e árvores)
        run {
            val b = MB(); val fl = Flora.Batch()
            b.m(Mt.GRASS, 0.3f)
            val R = 420f
            b.box((X0 - R + X0) / 2f, -0.06f, (Z0 + Z1) / 2f, R, 0.02f, Z1 - Z0 + 2 * R, C("#D6EEC4"))
            b.box((X1 + X1 + R) / 2f, -0.06f, (Z0 + Z1) / 2f, R, 0.02f, Z1 - Z0 + 2 * R, C("#D6EEC4"))
            b.box((X0 + X1) / 2f, -0.06f, (Z0 - R + Z0) / 2f, X1 - X0, 0.02f, R, C("#D6EEC4"))
            b.box((X0 + X1) / 2f, -0.06f, (Z1 + Z1 + R) / 2f, X1 - X0, 0.02f, R, C("#D6EEC4"))
            val rng = Rng(999)
            var a = X0 - 6f
            while (a < X1 + 6f) {
                fl.place("pine_a", a.toDouble(), 0.0, (Z0 - 6f - rng.r(0f, 8f)).toDouble(), rng.r(1.3f, 2.0f).toDouble(), rng.r(0f, 6f).toDouble())
                fl.place("pine_a", a.toDouble(), 0.0, (Z1 + 6f + rng.r(0f, 8f)).toDouble(), rng.r(1.3f, 2.0f).toDouble(), rng.r(0f, 6f).toDouble())
                a += rng.r(7f, 12f)
            }
            a = Z0 - 6f
            while (a < Z1 + 6f) {
                fl.place("pine_a", (X0 - 6f - rng.r(0f, 8f)).toDouble(), 0.0, a.toDouble(), rng.r(1.3f, 2.0f).toDouble(), rng.r(0f, 6f).toDouble())
                fl.place("pine_a", (X1 + 6f + rng.r(0f, 8f)).toDouble(), 0.0, a.toDouble(), rng.r(1.3f, 2.0f).toDouble(), rng.r(0f, 6f).toDouble())
                a += rng.r(7f, 12f)
            }
            // morros ao longe
            for (k in 0 until 18) {
                val ang = k * 2.0 * Math.PI / 18
                val d = 205.0 + (k % 3) * 18
                val cx = ((X0 + X1) / 2 + d * cos(ang)).toFloat(); val cz = ((Z0 + Z1) / 2 + d * sin(ang)).toFloat()
                b.m(Mt.PLAIN)
                b.sphere(cx, -6f, cz, 40f + (k % 4) * 10f, mix(C("#8DB88A"), C("#B9D3BC"), (k % 3) / 3f), 26f + (k % 3) * 6f, 10)
            }
            val m = b.toMesh(true)
            out.add(Chunk(Mesh(m.parts + fl.build()), X0 - 420f, Z0 - 420f, X1 + 420f, Z1 + 420f, 60f))
        }
        chunks = out
        buildLights()
        spawnTraffic()
        buildCarMeshes()
        buildPeds()
        on = true
    }

    // ------------------------------------------------------------ chão / colisão

    private fun inBands(v: Float, bands: FloatArray, inner: Boolean): Boolean {
        var k = 0
        while (k < bands.size) {
            val a = bands[k] + (if (inner) SIDE else 0f); val b = bands[k + 1] - (if (inner) SIDE else 0f)
            if (v >= a && v <= b) return true
            k += 2
        }
        return false
    }

    /** Ponto dentro do quarteirão da casa (lá valem as regras do quintal). */
    fun inLot(x: Float, z: Float) = x > lotX0 && x < lotX1 && z > lotZ0 && z < lotZ1

    /** Está no asfalto? */
    fun onRoad(x: Float, z: Float) = inBands(x, bandX, true) || inBands(z, bandZ, true)

    /** Altura do chão da cidade (asfalto 0, calçada e lotes 15 cm). */
    fun groundH(x: Float, z: Float): Float = if (!on || inLot(x, z)) 0f else if (onRoad(x, z)) 0f else CURB

    /** Bloqueado para quem anda: fora da cidade, prédio, muro, carro. */
    fun blocked(x: Float, z: Float): Boolean {
        if (x < X0 + 0.5f || x > X1 - 0.5f || z < Z0 + 0.5f || z > Z1 - 0.5f) return true
        for (r in solids) if (x > r[0] && x < r[2] && z > r[1] && z < r[3]) return true
        for (c in cars) {
            val dx = x - c.x; val dz = z - c.z
            if (dx * dx + dz * dz > 9f) continue
            val fx = if (c.axis == 0) c.dir.toFloat() else 0f; val fz = if (c.axis == 1) c.dir.toFloat() else 0f
            val along = dx * fx + dz * fz; val side = dx * fz - dz * fx
            if (abs(along) < 2.4f && abs(side) < 1.05f) return true
        }
        return false
    }

    private fun solid(x0: Float, z0: Float, x1: Float, z1: Float) { solids.add(floatArrayOf(min(x0, x1), min(z0, z1), max(x0, x1), max(z0, z1))) }

    // ------------------------------------------------------------ primitivas

    /** Quadrilátero com UV projetado (p = 4 pontos x,y,z). */
    private fun q(b: MB, p: FloatArray, c: Int) {
        val ux = p[3] - p[0]; val uy = p[4] - p[1]; val uz = p[5] - p[2]
        val vx = p[9] - p[0]; val vy = p[10] - p[1]; val vz = p[11] - p[2]
        var nx = uy * vz - uz * vy; var ny = uz * vx - ux * vz; var nz = ux * vy - uy * vx
        val l = sqrt(nx * nx + ny * ny + nz * nz).coerceAtLeast(1e-6f); nx /= l; ny /= l; nz /= l
        val ax = abs(nx); val ay = abs(ny); val az = abs(nz)
        for (i in intArrayOf(0, 1, 2, 0, 2, 3)) {
            val x = p[i * 3]; val y = p[i * 3 + 1]; val z = p[i * 3 + 2]
            if (ay >= ax && ay >= az) b.v(x, y, z, nx, ny, nz, c, x, z)
            else if (ax >= az) b.v(x, y, z, nx, ny, nz, c, z, y)
            else b.v(x, y, z, nx, ny, nz, c, x, y)
        }
    }

    private fun tri(b: MB, p: FloatArray, c: Int) {
        val ux = p[3] - p[0]; val uy = p[4] - p[1]; val uz = p[5] - p[2]
        val vx = p[6] - p[0]; val vy = p[7] - p[1]; val vz = p[8] - p[2]
        var nx = uy * vz - uz * vy; var ny = uz * vx - ux * vz; var nz = ux * vy - uy * vx
        val l = sqrt(nx * nx + ny * ny + nz * nz).coerceAtLeast(1e-6f); nx /= l; ny /= l; nz /= l
        for (i in 0..2) { val x = p[i * 3]; val y = p[i * 3 + 1]; val z = p[i * 3 + 2]; b.v(x, y, z, nx, ny, nz, c, if (abs(nx) > abs(nz)) z else x, y) }
    }

    /** Referencial de um lote: origem na frente (no meio), F = direção para onde a frente olha (para a rua). */
    private class L(val ox: Float, val oz: Float, val fx: Float, val fz: Float) {
        val rx = fz; val rz = -fx
        fun wx(lx: Float, lz: Float) = ox + rx * lx - fx * lz
        fun wz(lx: Float, lz: Float) = oz + rz * lx - fz * lz
        val alongX = abs(rx) > 0.5f
    }

    /** Caixa no referencial do lote: [lx] ao longo da frente, [lz] fundo (0 = frente do lote, positivo = para dentro). */
    private fun lb(b: MB, l: L, lx: Float, y: Float, lz: Float, sx: Float, sy: Float, sz: Float, c: Int, lit: Boolean = true) {
        val cx = l.wx(lx, lz); val cz = l.wz(lx, lz)
        if (l.alongX) b.box(cx, y, cz, sx, sy, sz, c, lit) else b.box(cx, y, cz, sz, sy, sx, c, lit)
    }

    private fun lsolid(l: L, lx: Float, lz: Float, sx: Float, sz: Float) {
        val ax = l.wx(lx - sx / 2, lz - sz / 2); val az = l.wz(lx - sx / 2, lz - sz / 2)
        val bx = l.wx(lx + sx / 2, lz + sz / 2); val bz = l.wz(lx + sx / 2, lz + sz / 2)
        solid(ax, az, bx, bz)
    }

    /** Placa de letreiro [idx] voltada para F, com a frente em [lz] (um pouco à frente da parede). */
    private fun sign(b: MB, l: L, lx: Float, y: Float, lz: Float, w: Float, h: Float, idx: Int) {
        val u0 = (idx % 2) * 0.5f + 0.002f; val u1 = u0 + 0.496f
        val v0 = (idx / 2) / 16f + 0.004f; val v1 = (idx / 2 + 1) / 16f - 0.004f
        // caixa da placa (fundo) e a face com o texto
        b.m(Mt.PLAIN)
        lb(b, l, lx, y + h / 2, lz + 0.08f, w + 0.12f, h + 0.12f, 0.14f, C("#3A3A3A"))
        b.m(Mt.SIGN, 1f)
        val ax = l.wx(lx - w / 2, lz - 0.02f); val az = l.wz(lx - w / 2, lz - 0.02f)
        val bx = l.wx(lx + w / 2, lz - 0.02f); val bz = l.wz(lx + w / 2, lz - 0.02f)
        val nx = l.fx; val nz = l.fz; val c = C("#FFFFFF")
        b.v(ax, y, az, nx, 0f, nz, c, u0, v1); b.v(bx, y, bz, nx, 0f, nz, c, u1, v1); b.v(bx, y + h, bz, nx, 0f, nz, c, u1, v0)
        b.v(ax, y, az, nx, 0f, nz, c, u0, v1); b.v(bx, y + h, bz, nx, 0f, nz, c, u1, v0); b.v(ax, y + h, az, nx, 0f, nz, c, u0, v0)
        b.m(Mt.PLAIN)
    }

    private fun groundBox(b: MB, x0: Float, z0: Float, x1: Float, z1: Float, mat: Int, s: Float, c: Int, top: Float = CURB) {
        b.m(mat, s)
        b.box((x0 + x1) / 2, top / 2, (z0 + z1) / 2, x1 - x0, top, z1 - z0, c)
    }

    private fun roundTree(b: MB, x: Float, z: Float, s: Float, rng: Rng, y: Float = CURB) {
        b.m(Mt.WOOD, 1f)
        b.cyl(x, y, z, 0.13f * s, 0.09f * s, 2.2f * s, C("#7A5A3C"), true, 7)
        b.m(Mt.PLAIN)
        val g = rng.pick(arrayOf(C("#5E9E48"), C("#4F8F3F"), C("#6DAA4F"), C("#7FB25A")))
        b.sphere(x, y + 2.9f * s, z, 1.35f * s, g, 1.15f * s, 8)
        b.sphere(x + 0.6f * s, y + 2.5f * s, z + 0.3f * s, 0.95f * s, shade(g, 10), 0.8f * s, 7)
        b.sphere(x - 0.5f * s, y + 2.6f * s, z - 0.4f * s, 0.9f * s, shade(g, -8), 0.8f * s, 7)
    }

    private fun bench(b: MB, l: L, lx: Float, lz: Float) {
        b.m(Mt.WOOD, 1f)
        lb(b, l, lx, CURB + 0.45f, lz, 1.6f, 0.06f, 0.45f, C("#9C6B3F"))
        lb(b, l, lx, CURB + 0.75f, lz + 0.22f, 1.6f, 0.3f, 0.05f, C("#9C6B3F"))
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-0.7f, 0.7f)) lb(b, l, lx + s, CURB + 0.22f, lz, 0.06f, 0.45f, 0.45f, C("#3B3B3B"))
    }

    private fun streetLamp(b: MB, x: Float, z: Float, ax: Float, az: Float) {
        b.m(Mt.METAL, 1f)
        b.cyl(x, CURB, z, 0.09f, 0.06f, 6.2f, C("#4A4F55"), true, 8)
        b.box(x + ax * 0.7f, CURB + 6.1f, z + az * 0.7f, if (ax != 0f) 1.4f else 0.12f, 0.1f, if (az != 0f) 1.4f else 0.12f, C("#4A4F55"))
        b.m(Mt.PLAIN)
        b.box(x + ax * 1.35f, CURB + 6.0f, z + az * 1.35f, 0.5f, 0.12f, 0.5f, C("#FFF6D8"), false)
    }

    // ------------------------------------------------------------ ruas

    private fun roads(out: ArrayList<Chunk>) {
        val asph = C("#FFFFFF"); val walk = C("#E3E0DA"); val curbC = C("#C9C6C0")
        val yel = C("#F2C230"); val wht = C("#F4F4F4")
        // ruas ao longo de x (faixas de z)
        for (k in 0 until 6) {
            val za = bandZ[k * 2]; val zb = bandZ[k * 2 + 1]; val zc = (za + zb) / 2
            val b = MB()
            b.m(Mt.ASPHALT, 0.25f)
            b.plane(X0, za + SIDE, X1, zb - SIDE, 0f, asph)
            // calçadas: fora das ruas que cruzam
            val xs = freeIntervals(X0, X1, bandX)
            for (iv in xs) {
                groundBox(b, iv[0], za, iv[1], za + SIDE, Mt.PAVER, 0.9f, walk)
                groundBox(b, iv[0], zb - SIDE, iv[1], zb, Mt.PAVER, 0.9f, walk)
                b.m(Mt.STONE, 1f)
                b.box((iv[0] + iv[1]) / 2, CURB / 2 + 0.005f, za + SIDE - 0.12f, iv[1] - iv[0], CURB + 0.01f, 0.24f, curbC)
                b.box((iv[0] + iv[1]) / 2, CURB / 2 + 0.005f, zb - SIDE + 0.12f, iv[1] - iv[0], CURB + 0.01f, 0.24f, curbC)
            }
            // faixas: amarela dupla no meio, branca nas bordas, tracejada entre as faixas; faixa de pedestre perto dos cruzamentos
            b.m(Mt.PLAIN)
            val ri = freeIntervals(X0, X1, bandX, -SIDE)
            for (iv in ri) {
                val a = iv[0] + 3.2f; val e = iv[1] - 3.2f
                if (e <= a) continue
                b.box((a + e) / 2, 0.012f, zc - 0.12f, e - a, 0.02f, 0.1f, yel)
                b.box((a + e) / 2, 0.012f, zc + 0.12f, e - a, 0.02f, 0.1f, yel)
                b.box((a + e) / 2, 0.012f, za + SIDE + 0.35f, e - a, 0.02f, 0.12f, wht)
                b.box((a + e) / 2, 0.012f, zb - SIDE - 0.35f, e - a, 0.02f, 0.12f, wht)
                for (side in intArrayOf(0, 1)) {
                    val x = if (side == 0) iv[0] else iv[1]
                    val dx = if (side == 0) 1f else -1f
                    if ((side == 0 && iv[0] <= X0 + 0.1f) || (side == 1 && iv[1] >= X1 - 0.1f)) continue
                    var zz = za + SIDE + 0.5f
                    while (zz < zb - SIDE - 0.4f) { b.box(x + dx * 1.6f, 0.012f, zz + 0.25f, 2.4f, 0.02f, 0.5f, wht); zz += 1.0f }
                    // linha de parada
                    val stopZ0 = if (side == 0) za + SIDE else zc
                    val stopZ1 = if (side == 0) zc else zb - SIDE
                    b.box(x + dx * 3.3f, 0.012f, (stopZ0 + stopZ1) / 2, 0.35f, 0.02f, stopZ1 - stopZ0, wht)
                }
            }
            // postes de luz e árvores na calçada (entre os cruzamentos)
            val rng = Rng(k * 13 + 1)
            for (iv in freeIntervals(X0, X1, bandX)) {
                var x = iv[0] + 6f
                var n = 0
                while (x < iv[1] - 6f) {
                    if (n % 2 == 0) { streetLamp(b, x, za + 0.6f, 0f, 1f); streetLamp(b, x + 9f, zb - 0.6f, 0f, -1f) }
                    else { roundTree(b, x, za + 1.2f, rng.r(0.8f, 1.0f), rng); roundTree(b, x + 9f, zb - 1.2f, rng.r(0.8f, 1.0f), rng) }
                    x += 12f; n++
                }
            }
            out.add(Chunk(b.toMesh(true), X0, za, X1, zb, 7f))
        }
        // ruas ao longo de z (faixas de x): só os trechos entre as ruas de x
        for (k in 0 until 6) {
            val xa = bandX[k * 2]; val xb = bandX[k * 2 + 1]; val xc = (xa + xb) / 2
            val b = MB()
            val segs = freeIntervals(Z0, Z1, bandZ, -SIDE)
            b.m(Mt.ASPHALT, 0.25f)
            for (iv in segs) b.plane(xa + SIDE, iv[0], xb - SIDE, iv[1], 0f, asph)
            for (iv in freeIntervals(Z0, Z1, bandZ)) {
                groundBox(b, xa, iv[0], xa + SIDE, iv[1], Mt.PAVER, 0.9f, walk)
                groundBox(b, xb - SIDE, iv[0], xb, iv[1], Mt.PAVER, 0.9f, walk)
                b.m(Mt.STONE, 1f)
                b.box(xa + SIDE - 0.12f, CURB / 2 + 0.005f, (iv[0] + iv[1]) / 2, 0.24f, CURB + 0.01f, iv[1] - iv[0], curbC)
                b.box(xb - SIDE + 0.12f, CURB / 2 + 0.005f, (iv[0] + iv[1]) / 2, 0.24f, CURB + 0.01f, iv[1] - iv[0], curbC)
            }
            b.m(Mt.PLAIN)
            for (iv in segs) {
                val a = iv[0] + 3.2f; val e = iv[1] - 3.2f
                if (e <= a) continue
                b.box(xc - 0.12f, 0.012f, (a + e) / 2, 0.1f, 0.02f, e - a, yel)
                b.box(xc + 0.12f, 0.012f, (a + e) / 2, 0.1f, 0.02f, e - a, yel)
                b.box(xa + SIDE + 0.35f, 0.012f, (a + e) / 2, 0.12f, 0.02f, e - a, wht)
                b.box(xb - SIDE - 0.35f, 0.012f, (a + e) / 2, 0.12f, 0.02f, e - a, wht)
                for (side in intArrayOf(0, 1)) {
                    if ((side == 0 && iv[0] <= Z0 + 0.1f) || (side == 1 && iv[1] >= Z1 - 0.1f)) continue
                    val z = if (side == 0) iv[0] else iv[1]
                    val dz = if (side == 0) 1f else -1f
                    var xx = xa + SIDE + 0.5f
                    while (xx < xb - SIDE - 0.4f) { b.box(xx + 0.25f, 0.012f, z + dz * 1.6f, 0.5f, 0.02f, 2.4f, wht); xx += 1.0f }
                    val s0 = if (side == 0) xc else xa + SIDE
                    val s1 = if (side == 0) xb - SIDE else xc
                    b.box((s0 + s1) / 2, 0.012f, z + dz * 3.3f, s1 - s0, 0.02f, 0.35f, wht)
                }
            }
            val rng = Rng(k * 17 + 5)
            for (iv in freeIntervals(Z0, Z1, bandZ)) {
                var z = iv[0] + 6f
                var n = 0
                while (z < iv[1] - 6f) {
                    if (n % 2 == 0) { streetLamp(b, xa + 0.6f, z, 1f, 0f); streetLamp(b, xb - 0.6f, z + 9f, -1f, 0f) }
                    else { roundTree(b, xa + 1.2f, z, rng.r(0.8f, 1.0f), rng); roundTree(b, xb - 1.2f, z + 9f, rng.r(0.8f, 1.0f), rng) }
                    z += 12f; n++
                }
            }
            // semáforos e placas de rua nos cruzamentos desta rua
            for (j in 0 until 6) {
                val za = bandZ[j * 2]; val zb = bandZ[j * 2 + 1]
                if (j == 0 || j == 5 || k == 0 || k == 5) continue   // anel de fora: sem semáforo
                for (cx in intArrayOf(0, 1)) for (cz in intArrayOf(0, 1)) {
                    val x = if (cx == 0) xa + 1.0f else xb - 1.0f
                    val z = if (cz == 0) za + 1.0f else zb - 1.0f
                    b.m(Mt.METAL, 1f)
                    b.cyl(x, CURB, z, 0.1f, 0.08f, 4.2f, C("#2E3236"), true, 8)
                    // cabeças: uma para cada direção (caixas pretas; as luzes acesas são desenhadas por fase)
                    for (h in headPos(x, z, cx, cz)) b.box(h[0], h[1], h[2], 0.34f, 0.95f, 0.34f, C("#1E1F22"))
                    if (cx == 1 && cz == 1) {
                        b.cyl(x - 0.4f, CURB, z - 0.4f, 0.05f, 0.05f, 2.9f, C("#7D8288"), true, 6)
                        sign(b, L(x - 0.4f, z - 0.4f, 0f, 1f), 0f, CURB + 2.6f, 0f, 1.8f, 0.24f, S_STREET0 + (k % 2) * 2)
                        sign(b, L(x - 0.4f, z - 0.4f, 1f, 0f), 0f, CURB + 2.95f, 0f, 1.8f, 0.24f, S_STREET0 + 1 + (j % 2) * 2)
                    }
                }
            }
            out.add(Chunk(b.toMesh(true), xa, Z0, xb, Z1, 7f))
        }
    }

    /** Posições das duas cabeças de semáforo de um poste (índice 0 = para o trânsito em x, 1 = em z). */
    private fun headPos(x: Float, z: Float, cx: Int, cz: Int): Array<FloatArray> {
        val ox = if (cx == 0) 1f else -1f; val oz = if (cz == 0) 1f else -1f
        return arrayOf(floatArrayOf(x, CURB + 3.7f, z + oz * 0.35f), floatArrayOf(x + ox * 0.35f, CURB + 3.7f, z))
    }

    private fun buildLights() {
        // fases: 0 = x verde, 1 = x amarelo, 2 = z verde, 3 = z amarelo
        val red = C("#FF3B30"); val yel = C("#FFC400"); val grn = C("#33E06A")
        for (ph in 0 until 4) {
            val b = MB()
            b.m(Mt.PLAIN)
            for (k in 1 until 5) for (j in 1 until 5) {
                val xa = bandX[k * 2]; val xb = bandX[k * 2 + 1]; val za = bandZ[j * 2]; val zb = bandZ[j * 2 + 1]
                for (cx in intArrayOf(0, 1)) for (cz in intArrayOf(0, 1)) {
                    val x = if (cx == 0) xa + 1.0f else xb - 1.0f
                    val z = if (cz == 0) za + 1.0f else zb - 1.0f
                    val hp = headPos(x, z, cx, cz)
                    for (ax in 0..1) {
                        val st = if (ax == 0) (if (ph == 0) 2 else if (ph == 1) 1 else 0) else (if (ph == 2) 2 else if (ph == 3) 1 else 0)
                        val col = if (st == 2) grn else if (st == 1) yel else red
                        val dy = if (st == 2) -0.3f else if (st == 1) 0f else 0.3f
                        b.box(hp[ax][0], hp[ax][1] + dy, hp[ax][2], 0.37f, 0.22f, 0.37f, col, false)
                    }
                }
            }
            lightMeshes[ph] = b.toMesh(true)
        }
    }

    /** Intervalos de [a, b] fora das faixas [bands] (encolhidas por [shrink] de cada lado; negativo = só o asfalto). */
    private fun freeIntervals(a: Float, b: Float, bands: FloatArray, shrink: Float = 0f): List<FloatArray> {
        val out = ArrayList<FloatArray>()
        var cur = a
        var k = 0
        while (k < bands.size) {
            val s = bands[k] - shrink; val e = bands[k + 1] + shrink
            if (e > cur && s < b) { if (s > cur) out.add(floatArrayOf(cur, s)); cur = max(cur, e) }
            k += 2
        }
        if (cur < b) out.add(floatArrayOf(cur, b))
        return out
    }

    // ------------------------------------------------------------ construções

    private val WALLS = arrayOf("#F3E9DA", "#E8D5C0", "#DCE7EE", "#F2DCD3", "#E9EFD9", "#FFF4D6", "#D9D4E8", "#F6F1EA", "#E7C9A9", "#CFE0D8")
    private val ROOFS = arrayOf("#8E4B3A", "#5B5F66", "#A0522D", "#6B3E2E", "#465A6B", "#7A6A5A")
    private val CARC = arrayOf("#D7263D", "#1B98E0", "#F4F4F4", "#2E2E2E", "#9AA0A6", "#F2C14E", "#2A9D8F", "#6A4C93", "#E76F51", "#264653")

    /** Casa com telhado de duas águas, janelas, porta, garagem, jardim e cerca baixa. */
    private fun house(b: MB, fl: Flora.Batch, rng: Rng, l: L, lotW: Float, lotD: Float) {
        val wall = C(rng.pick(WALLS)); val roof = C(rng.pick(ROOFS)); val trim = C("#FFFFFF")
        val hw = rng.r(8f, min(10.5f, lotW - 3.2f)); val hd = rng.r(7.5f, 9.5f); val set = rng.r(5.5f, 7f)
        val floors = if (rng.f() < 0.45f) 2 else 1
        val wh = 2.9f * floors
        val hx = rng.r(-0.8f, 0.8f) - (if (rng.f() < 0.5f) 1.2f else -1.2f)
        // gramado e calçadinha até a porta
        b.m(Mt.PAVER, 0.8f)
        lb(b, l, hx, CURB + 0.01f, set / 2, 1.2f, 0.02f, set, C("#D8CFC2"))
        val gx = if (hx < 0) hx + hw / 2 + 1.7f else hx - hw / 2 - 1.7f
        b.m(Mt.ASPHALT, 0.3f)
        lb(b, l, gx, CURB + 0.012f, set / 2 + 1f, 3.0f, 0.02f, set + 2f, C("#C9C9C9"))
        // corpo
        b.m(if (rng.f() < 0.5f) Mt.SIDING else Mt.PLASTER, 0.5f)
        lb(b, l, hx, CURB + wh / 2, set + hd / 2, hw, wh, hd, wall)
        lsolid(l, hx, set + hd / 2, hw + 0.3f, hd + 0.3f)
        b.m(Mt.STONE, 0.8f)
        lb(b, l, hx, CURB + 0.25f, set + hd / 2, hw + 0.12f, 0.5f, hd + 0.12f, C("#B9B3AA"))   // rodapé de pedra
        // telhado (cumeeira paralela à frente)
        b.m(Mt.ROOF, 0.6f)
        val y0 = CURB + wh; val rh = rng.r(2.0f, 2.8f); val ov = 0.45f
        val xa = hx - hw / 2 - ov; val xb = hx + hw / 2 + ov; val za = set - ov; val zb = set + hd + ov; val zm = set + hd / 2
        fun P(lx: Float, y: Float, lz: Float) = floatArrayOf(l.wx(lx, lz), y, l.wz(lx, lz))
        fun quad(a: FloatArray, bb: FloatArray, c: FloatArray, d: FloatArray, col: Int) = q(b, a + bb + c + d, col)
        val ye = y0 - rh * ov / (hd / 2)   // beiral abaixo do topo da parede (o telhado encosta na parede)
        quad(P(xa, ye, za), P(xb, ye, za), P(xb, y0 + rh, zm), P(xa, y0 + rh, zm), roof)
        quad(P(xb, ye, zb), P(xa, ye, zb), P(xa, y0 + rh, zm), P(xb, y0 + rh, zm), roof)
        b.m(if (rng.f() < 0.5f) Mt.SIDING else Mt.PLASTER, 0.5f)
        tri(b, P(hx - hw / 2, y0, set) + P(hx - hw / 2, y0, set + hd) + P(hx - hw / 2, y0 + rh, zm), wall)
        tri(b, P(hx + hw / 2, y0, set + hd) + P(hx + hw / 2, y0, set) + P(hx + hw / 2, y0 + rh, zm), wall)
        // chaminé
        if (rng.f() < 0.5f) { b.m(Mt.STONE, 0.8f); lb(b, l, hx + hw * 0.28f, y0 + rh * 0.8f, set + hd * 0.65f, 0.7f, rh * 1.2f, 0.7f, C("#9C5B45")) }
        // porta, janelas, varanda
        b.m(Mt.WOOD, 1f)
        lb(b, l, hx, CURB + 1.05f, set - 0.03f, 1.0f, 2.1f, 0.08f, C(rng.pick(arrayOf("#6B3E26", "#2F5D50", "#1F3A5F", "#8C2F39"))))
        b.m(Mt.PLAIN)
        lb(b, l, hx, CURB + 2.2f, set - 0.04f, 1.3f, 0.12f, 0.1f, trim)
        b.m(Mt.WOOD, 1f)
        lb(b, l, hx, CURB + 0.08f, set - 0.8f, 2.6f, 0.16f, 1.6f, C("#B48A60"))   // degrau/varandinha
        for (f in 0 until floors) {
            val wy = CURB + 1.5f + f * 2.9f
            for (s in floatArrayOf(-1f, 1f)) {
                val wx = hx + s * hw * 0.3f
                if (f == 0 && abs(wx - hx) < 1.3f) continue
                window(b, l, wx, wy, set, 1.4f, 1.3f)
            }
            if (f == 1) window(b, l, hx, wy, set, 1.2f, 1.1f)
            // janelas do lado
            for (s in floatArrayOf(-1f, 1f)) sideWindow(b, l, hx + s * (hw / 2), wy, set + hd * 0.5f, s)
        }
        // garagem
        if (rng.f() < 0.6f) {
            b.m(Mt.PLASTER, 0.5f)
            lb(b, l, gx, CURB + 1.35f, set + 1.5f + 3f, 3.6f, 2.7f, 6f, wall)
            lsolid(l, gx, set + 4.5f, 3.8f, 6.2f)
            b.m(Mt.METAL, 1f)
            lb(b, l, gx, CURB + 1.1f, set + 1.47f, 2.8f, 2.2f, 0.06f, C("#E4E4E4"))
            for (k in 0 until 5) { b.m(Mt.PLAIN); lb(b, l, gx, CURB + 0.3f + k * 0.44f, set + 1.43f, 2.8f, 0.03f, 0.03f, C("#BDBDBD")) }
            b.m(Mt.ROOF, 0.6f)
            lb(b, l, gx, CURB + 2.78f, set + 4.5f, 3.9f, 0.16f, 6.3f, roof)
        }
        // carro na garagem/entrada
        if (rng.f() < 0.65f) parkedCar(b, l.wx(gx, set - 1.2f), l.wz(gx, set - 1.2f), if (l.alongX) 1 else 0, C(rng.pick(CARC)), CURB + 0.012f)
        // cerca baixa e arbustos
        b.m(Mt.WOOD, 1f)
        val fc = C("#FFFFFF")
        for (s in floatArrayOf(-1f, 1f)) {
            val a = s * lotW / 2
            val e2 = if (s < 0) (if (gx < hx) gx - 1.8f else hx - 0.8f) else (if (gx > hx) gx + 1.8f else hx + 0.8f)
            val from = min(a, e2); val to = max(a, e2)
            if (to - from > 0.5f) {
                lb(b, l, (from + to) / 2, CURB + 0.55f, 0.3f, to - from, 0.08f, 0.05f, fc)
                lb(b, l, (from + to) / 2, CURB + 0.3f, 0.3f, to - from, 0.08f, 0.05f, fc)
                var p = from
                while (p <= to) { lb(b, l, p, CURB + 0.42f, 0.3f, 0.08f, 0.84f, 0.08f, fc); p += 0.9f }
            }
        }
        for (k in 0 until 3) {
            val bx = hx + rng.r(-hw / 2, hw / 2)
            fl.place(rng.pick(arrayOf("bush_a", "bush_b", "bush_pink", "bush_white")), l.wx(bx, set - 0.5f).toDouble(), CURB.toDouble(), l.wz(bx, set - 0.5f).toDouble(), rng.r(0.8f, 1.1f).toDouble(), rng.r(0f, 6f).toDouble())
        }
        if (rng.f() < 0.7f) roundTree(b, l.wx(lotW / 2 - 1.8f, lotD - 3f), l.wz(lotW / 2 - 1.8f, lotD - 3f), rng.r(0.9f, 1.25f), rng)
        // caixa de correio
        b.m(Mt.METAL, 1f)
        lb(b, l, hx + 1.4f, CURB + 0.5f, 0.6f, 0.06f, 1.0f, 0.06f, C("#444444"))
        lb(b, l, hx + 1.4f, CURB + 1.05f, 0.6f, 0.25f, 0.22f, 0.42f, C(rng.pick(arrayOf("#C0392B", "#2C3E50", "#27AE60"))))
    }

    private fun window(b: MB, l: L, lx: Float, y: Float, lz: Float, w: Float, h: Float) {
        b.m(Mt.PLAIN)
        lb(b, l, lx, y, lz - 0.03f, w + 0.18f, h + 0.18f, 0.08f, C("#FFFFFF"))
        b.m(Mt.METAL, 1f)
        lb(b, l, lx, y, lz - 0.075f, w, h, 0.03f, C("#5D7A93"))
        b.m(Mt.PLAIN)
        lb(b, l, lx, y, lz - 0.095f, 0.05f, h, 0.02f, C("#FFFFFF"))
        lb(b, l, lx, y - h / 2 - 0.1f, lz - 0.12f, w + 0.3f, 0.07f, 0.18f, C("#EDEDED"))
    }

    private fun sideWindow(b: MB, l: L, lx: Float, y: Float, lz: Float, s: Float) {
        // janela na parede lateral (normal = ±R)
        b.m(Mt.PLAIN)
        val cx = l.wx(lx + s * 0.03f, lz); val cz = l.wz(lx + s * 0.03f, lz)
        if (l.alongX) { b.box(cx, y, cz, 0.08f, 1.4f, 1.5f, C("#FFFFFF")); b.m(Mt.METAL, 1f); b.box(l.wx(lx + s * 0.075f, lz), y, cz, 0.03f, 1.22f, 1.32f, C("#5D7A93")) }
        else { b.box(cx, y, cz, 1.5f, 1.4f, 0.08f, C("#FFFFFF")); b.m(Mt.METAL, 1f); b.box(cx, y, l.wz(lx + s * 0.075f, lz), 1.32f, 1.22f, 0.03f, C("#5D7A93")) }
    }

    /** Carro estacionado (estático) com o comprimento no eixo [axis] (0 = x, 1 = z). */
    private fun parkedCar(b: MB, x: Float, z: Float, axis: Int, col: Int, y: Float) {
        carGeom(b, x, y, z, axis, col, false)
        solid(x - (if (axis == 0) 2.2f else 0.95f), z - (if (axis == 0) 0.95f else 2.2f), x + (if (axis == 0) 2.2f else 0.95f), z + (if (axis == 0) 0.95f else 2.2f))
    }

    /** Geometria de um carro em (x, y, z), comprido no eixo [axis]. [kind]: true = mais alto (van/ambulância). */
    private fun carGeom(b: MB, x: Float, y: Float, z: Float, axis: Int, col: Int, tall: Boolean, roofCol: Int = col) {
        fun bx(along: Float, yy: Float, side: Float, la: Float, hh: Float, ws: Float, c: Int, lit: Boolean = true) {
            if (axis == 0) b.box(x + along, y + yy, z + side, la, hh, ws, c, lit) else b.box(x + side, y + yy, z + along, ws, hh, la, c, lit)
        }
        val len = if (tall) 5.2f else 4.3f
        b.m(Mt.METAL, 1f)
        bx(0f, 0.62f, 0f, len, 0.62f, 1.8f, col)
        val ch = if (tall) 1.2f else 0.62f
        bx(if (tall) 0.4f else -0.2f, 0.93f + ch / 2, 0f, if (tall) len - 1.1f else 2.3f, ch, 1.66f, roofCol)
        b.m(Mt.PLAIN)
        val glass = C("#26323C")
        bx(if (tall) -len / 2 + 1.12f else 0.98f, 0.93f + ch / 2, 0f, 0.06f, ch * 0.8f, 1.5f, glass)   // para-brisa
        bx(if (tall) 0.4f else -0.2f, 0.95f + ch / 2, 0f, if (tall) len - 1.3f else 2.1f, ch * 0.62f, 1.70f, glass)   // janelas laterais
        bx(len / 2 - 0.02f, 0.66f, 0.62f, 0.05f, 0.14f, 0.32f, C("#FFF9E0"), false)
        bx(len / 2 - 0.02f, 0.66f, -0.62f, 0.05f, 0.14f, 0.32f, C("#FFF9E0"), false)
        bx(-len / 2 + 0.02f, 0.68f, 0.66f, 0.05f, 0.14f, 0.3f, C("#C81E1E"), false)
        bx(-len / 2 + 0.02f, 0.68f, -0.66f, 0.05f, 0.14f, 0.3f, C("#C81E1E"), false)
        val tire = C("#1A1A1A")
        for (a in floatArrayOf(-len / 2 + 0.85f, len / 2 - 0.85f)) for (s in floatArrayOf(-0.86f, 0.86f)) bx(a, 0.33f, s, 0.66f, 0.66f, 0.24f, tire)
        bx(len / 2 + 0.02f, 0.45f, 0f, 0.08f, 0.18f, 1.7f, C("#3A3A3A"))
        bx(-len / 2 - 0.02f, 0.45f, 0f, 0.08f, 0.18f, 1.7f, C("#3A3A3A"))
    }

    private fun lawn(b: MB, x0: Float, z0: Float, x1: Float, z1: Float) = groundBox(b, x0, z0, x1, z1, Mt.GRASS, 0.3f, C("#D6EEC4"))
    private fun plaza(b: MB, x0: Float, z0: Float, x1: Float, z1: Float) = groundBox(b, x0, z0, x1, z1, Mt.PAVER, 0.7f, C("#E2DDD3"))

    private fun residential(b: MB, fl: Flora.Batch, rng: Rng, x0: Float, z0: Float, x1: Float, z1: Float): Float {
        lawn(b, x0, z0, x1, z1)
        val n = 4; val lw = (x1 - x0) / n; val ld = (z1 - z0) / 2
        for (k in 0 until n) {
            val cx = x0 + lw * (k + 0.5f)
            house(b, fl, rng, L(cx, z1, 0f, 1f), lw, ld)          // frente para +z
            house(b, fl, rng, L(cx, z0, 0f, -1f), lw, ld)         // frente para -z
            // muro de fundo entre os lotes
            b.m(Mt.WOOD, 1f)
            if (k > 0) { b.box(x0 + lw * k, CURB + 0.75f, (z0 + z1) / 2, 0.08f, 1.5f, (z1 - z0) - 10f, C("#C9A27A")) }
        }
        b.m(Mt.WOOD, 1f)
        b.box((x0 + x1) / 2, CURB + 0.75f, (z0 + z1) / 2, x1 - x0 - 2f, 1.5f, 0.08f, C("#C9A27A"))
        return 9f
    }

    /** Prédio com fachada de janelas: térreo de vidro (loja), andares, platibanda e equipamentos no teto. */
    private fun tower(b: MB, rng: Rng, l: L, lx: Float, lz: Float, w: Float, d: Float, floors: Int, col: Int, shop: Int, balcony: Boolean = false): Float {
        val gh = 4.2f; val h = gh + floors * 3f
        val cx = l.wx(lx, lz + d / 2); val cz = l.wz(lx, lz + d / 2)
        val sx = if (l.alongX) w else d; val sz = if (l.alongX) d else w
        b.m(Mt.STONE, 0.5f)
        b.box(cx, CURB + gh / 2, cz, sx - 0.1f, gh, sz - 0.1f, C("#8C8F94"))
        // vitrine do térreo na frente
        b.m(Mt.METAL, 1f)
        lb(b, l, lx, CURB + 1.75f, lz - 0.03f, w - 1.2f, 3.0f, 0.06f, C("#3E5568"))
        b.m(Mt.PLAIN)
        var p = lx - w / 2 + 0.6f
        while (p <= lx + w / 2 - 0.6f) { lb(b, l, p, CURB + 1.75f, lz - 0.07f, 0.1f, 3.0f, 0.06f, C("#D0D3D6")); p += 2.4f }
        lb(b, l, lx, CURB + 1.15f, lz - 0.09f, 1.8f, 2.3f, 0.04f, C("#5E7C91"))   // porta
        if (shop >= 0) sign(b, l, lx, CURB + 3.35f, lz - 0.12f, min(w - 2f, 7.5f), 0.8f, shop)
        // marquise
        b.m(Mt.METAL, 1f)
        lb(b, l, lx, CURB + 3.2f, lz - 0.9f, w - 0.6f, 0.12f, 1.8f, C("#5A5F66"))
        // andares com janelas
        b.m(Mt.FACADE, 1f / 3f, 0f, -(CURB + gh) / 3f)
        b.box(cx, CURB + gh + floors * 1.5f, cz, sx, floors * 3f, sz, col)
        // faixas a cada 4 andares e platibanda
        b.m(Mt.PLASTER, 0.5f)
        var f = 4
        while (f < floors) { b.box(cx, CURB + gh + f * 3f, cz, sx + 0.25f, 0.3f, sz + 0.25f, shade(col, -25)); f += 4 }
        b.box(cx, CURB + h + 0.5f, cz, sx + 0.3f, 1.0f, sz + 0.3f, shade(col, -30))
        b.m(Mt.STONE, 0.5f)
        b.box(cx, CURB + h + 0.05f, cz, sx - 0.4f, 0.1f, sz - 0.4f, C("#9A9A9A"))
        // varandas na frente
        if (balcony) {
            for (fl in 1 until floors) for (k in 0 until (w / 6f).toInt()) {
                val bxp = lx - w / 2 + 3f + k * 6f
                b.m(Mt.STONE, 0.5f)
                lb(b, l, bxp, CURB + gh + fl * 3f + 0.05f, lz - 0.6f, 3.4f, 0.14f, 1.2f, C("#E9E9E9"))
                b.m(Mt.PLAIN); b.al = 0.9f
                lb(b, l, bxp, CURB + gh + fl * 3f + 0.6f, lz - 1.18f, 3.4f, 0.95f, 0.04f, C("#A8C7D8"))
                b.al = 1f
            }
        }
        // teto: ar-condicionado, caixa d'água, antena
        b.m(Mt.METAL, 1f)
        val tx = l.wx(lx, lz + d / 2); val tz = l.wz(lx, lz + d / 2)
        for (k in 0 until 3) b.box(tx + rng.r(-sx / 3, sx / 3), CURB + h + 0.45f, tz + rng.r(-sz / 3, sz / 3), 1.2f, 0.8f, 1.0f, C("#C8CCD0"))
        if (rng.f() < 0.6f) b.cyl(tx + sx / 4, CURB + h, tz - sz / 4, 1.1f, 1.1f, 2.0f, C("#6F7A84"), true, 10)
        if (rng.f() < 0.5f) b.cyl(tx - sx / 4, CURB + h, tz + sz / 4, 0.05f, 0.03f, 6f, C("#777777"), true, 5)
        solid(cx - sx / 2 - 0.2f, cz - sz / 2 - 0.2f, cx + sx / 2 + 0.2f, cz + sz / 2 + 0.2f)
        return h + 6f
    }

    private fun downtown(b: MB, fl: Flora.Batch, rng: Rng, x0: Float, z0: Float, x1: Float, z1: Float, hotel: Boolean = false): Float {
        plaza(b, x0, z0, x1, z1)
        val cols = arrayOf(C("#F0F0F0"), C("#DDE6EE"), C("#EFE3D3"), C("#C9D6DF"), C("#E6E1EA"), C("#D8D2C4"))
        val shopsA = intArrayOf(S_BANCO, S_CAFE, S_LIVR, S_ELET, S_MODA, S_OTICA, S_REST, S_ACAD)
        var hMax = 0f
        val w = (x1 - x0) / 2f - 2f
        // 2 prédios virados para +z e 2 para -z
        for (k in 0 until 2) {
            val cx = x0 + (x1 - x0) * (0.25f + 0.5f * k)
            val f1 = if (hotel && k == 0) 22 else rng.i(10) + 8
            val f2 = rng.i(12) + 6
            hMax = max(hMax, tower(b, rng, L(cx, z1, 0f, 1f), 0f, 2f, w, 18f, f1, rng.pick(cols), if (hotel && k == 0) S_HOTEL else shopsA[rng.i(shopsA.size)], rng.f() < 0.4f))
            hMax = max(hMax, tower(b, rng, L(cx, z0, 0f, -1f), 0f, 2f, w, 18f, f2, rng.pick(cols), shopsA[rng.i(shopsA.size)], rng.f() < 0.4f))
        }
        // corredor no meio com árvores e bancos
        for (k in 0 until 4) roundTree(b, x0 + 6f + k * (x1 - x0 - 12f) / 3f, (z0 + z1) / 2, 1.0f, rng)
        for (k in 0 until 3) bench(b, L(x0 + 12f + k * (x1 - x0 - 24f) / 2f, (z0 + z1) / 2 + 1.5f, 0f, 1f), 0f, 0f)
        return hMax
    }

    private fun apartments(b: MB, fl: Flora.Batch, rng: Rng, x0: Float, z0: Float, x1: Float, z1: Float): Float {
        lawn(b, x0, z0, x1, z1)
        val cols = arrayOf(C("#F5E6CC"), C("#E3EEF5"), C("#F2D7C9"), C("#E4F0E0"))
        var h = 0f
        val w = (x1 - x0) - 10f
        h = max(h, tower(b, rng, L((x0 + x1) / 2, z1, 0f, 1f), 0f, 4f, w, 13f, rng.i(4) + 5, rng.pick(cols), -1, true))
        h = max(h, tower(b, rng, L((x0 + x1) / 2, z0, 0f, -1f), 0f, 4f, w, 13f, rng.i(4) + 5, rng.pick(cols), -1, true))
        // estacionamento no meio
        b.m(Mt.ASPHALT, 0.3f)
        b.box((x0 + x1) / 2, CURB + 0.01f, (z0 + z1) / 2, x1 - x0 - 6f, 0.02f, 12f, C("#D0D0D0"))
        for (k in 0 until 8) if (rng.f() < 0.7f) parkedCar(b, x0 + 6f + k * 4.9f, (z0 + z1) / 2 + (if (k % 2 == 0) -2.8f else 2.8f), 1, C(rng.pick(CARC)), CURB + 0.02f)
        for (k in 0 until 6) roundTree(b, x0 + 2.5f, z0 + 6f + k * 7f, 1f, rng)
        return h
    }

    /** Fileira de lojas térreas/sobrados com toldo listrado e letreiro, viradas para a rua [l]. */
    private fun shopRow(b: MB, rng: Rng, l: L, len: Float, signs: IntArray, depth: Float) {
        val n = signs.size; val sw = len / n
        for (k in 0 until n) {
            val lx = -len / 2 + sw * (k + 0.5f)
            val col = C(rng.pick(WALLS)); val two = rng.f() < 0.55f
            val hh = if (two) 7.2f else 4.4f
            b.m(Mt.PLASTER, 0.5f)
            lb(b, l, lx, CURB + hh / 2, 1.5f + depth / 2, sw - 0.2f, hh, depth, col)
            lsolid(l, lx, 1.5f + depth / 2, sw, depth + 0.3f)
            b.m(Mt.STONE, 0.5f)
            lb(b, l, lx, CURB + hh + 0.3f, 1.5f + depth / 2, sw, 0.6f, depth + 0.1f, shade(col, -30))
            // vitrine e porta
            b.m(Mt.METAL, 1f)
            lb(b, l, lx, CURB + 1.5f, 1.47f, sw - 1.4f, 2.6f, 0.06f, C("#45647A"))
            b.m(Mt.PLAIN)
            lb(b, l, lx + sw * 0.25f, CURB + 1.15f, 1.43f, 1.1f, 2.3f, 0.04f, C("#2F4858"))
            lb(b, l, lx, CURB + 2.85f, 1.44f, sw - 1.3f, 0.12f, 0.08f, C("#FFFFFF"))
            // toldo listrado (inclinado)
            val ac = C(rng.pick(arrayOf("#D7263D", "#1B98E0", "#2A9D8F", "#F4A261", "#6A4C93", "#2E7D32")))
            val stripes = 8
            for (s in 0 until stripes) {
                val a0 = lx - (sw - 0.8f) / 2 + (sw - 0.8f) * s / stripes; val a1 = a0 + (sw - 0.8f) / stripes
                fun P(px: Float, y: Float, pz: Float) = floatArrayOf(l.wx(px, pz), y, l.wz(px, pz))
                b.m(Mt.FABRIC, 1f)
                q(b, P(a0, CURB + 3.2f, 1.45f) + P(a1, CURB + 3.2f, 1.45f) + P(a1, CURB + 2.6f, 0.15f) + P(a0, CURB + 2.6f, 0.15f), if (s % 2 == 0) ac else C("#FFFFFF"))
            }
            sign(b, l, lx, CURB + 3.4f, 1.38f, min(sw - 1.2f, 6.5f), 0.75f, signs[k])
            if (two) {
                for (s in floatArrayOf(-1f, 1f)) window(b, l, lx + s * sw * 0.22f, CURB + 5.6f, 1.5f, 1.3f, 1.4f)
            }
            // mesinhas na calçada do café/lanchonete
            if (signs[k] == S_CAFE || signs[k] == S_LANCH || signs[k] == S_SORV) {
                for (t in 0 until 2) {
                    val tx = lx - 1.5f + t * 3f
                    b.m(Mt.METAL, 1f)
                    lb(b, l, tx, CURB + 0.37f, -0.7f, 0.06f, 0.74f, 0.06f, C("#333333"))
                    lb(b, l, tx, CURB + 0.75f, -0.7f, 0.8f, 0.04f, 0.8f, C("#F5F5F5"))
                    b.m(Mt.FABRIC, 1f)
                    b.cyl(l.wx(tx, -0.7f), CURB + 2.0f, l.wz(tx, -0.7f), 1.2f, 0.02f, 0.4f, ac, true, 10)
                    b.m(Mt.METAL, 1f)
                    b.cyl(l.wx(tx, -0.7f), CURB + 0.75f, l.wz(tx, -0.7f), 0.025f, 0.025f, 1.3f, C("#888888"), true, 5)
                }
            }
        }
    }

    private fun shops(b: MB, fl: Flora.Batch, rng: Rng, x0: Float, z0: Float, x1: Float, z1: Float): Float {
        plaza(b, x0, z0, x1, z1)
        val len = x1 - x0 - 2f
        shopRow(b, rng, L((x0 + x1) / 2, z0, 0f, -1f), len, intArrayOf(S_PAD, S_FARM, S_CAFE, S_PET, S_SALAO), 10f)   // de frente para a avenida da casa
        shopRow(b, rng, L((x0 + x1) / 2, z1, 0f, 1f), len, intArrayOf(S_PIZZA, S_FLOR, S_SORV, S_ACAD), 10f)
        // estacionamento no meio
        b.m(Mt.ASPHALT, 0.3f)
        b.box((x0 + x1) / 2, CURB + 0.01f, (z0 + z1) / 2, x1 - x0 - 4f, 0.02f, (z1 - z0) - 26f, C("#D0D0D0"))
        b.m(Mt.PLAIN)
        for (k in 0 until 10) b.box(x0 + 4f + k * 4.2f, CURB + 0.025f, (z0 + z1) / 2, 0.12f, 0.02f, 5f, C("#F4F4F4"))
        for (k in 0 until 9) if (rng.f() < 0.6f) parkedCar(b, x0 + 6.1f + k * 4.2f, (z0 + z1) / 2, 1, C(rng.pick(CARC)), CURB + 0.02f)
        return 10f
    }

    private fun supermarket(b: MB, fl: Flora.Batch, rng: Rng, x0: Float, z0: Float, x1: Float, z1: Float): Float {
        plaza(b, x0, z0, x1, z1)
        // lojas viradas para a avenida da casa
        shopRow(b, rng, L((x0 + x1) / 2, z0, 0f, -1f), x1 - x0 - 2f, intArrayOf(S_LANCH, S_BANCO, S_OTICA, S_MODA), 9f)
        // supermercado grande no fundo, de frente para +z, com estacionamento
        val l = L((x0 + x1) / 2, z1, 0f, 1f)
        b.m(Mt.ASPHALT, 0.3f)
        b.box((x0 + x1) / 2, CURB + 0.01f, z1 - 9f, x1 - x0 - 2f, 0.02f, 16f, C("#D0D0D0"))
        b.m(Mt.PLAIN)
        for (k in 0 until 11) { b.box(x0 + 3f + k * 4f, CURB + 0.025f, z1 - 5f, 0.12f, 0.02f, 5f, C("#F4F4F4")); b.box(x0 + 3f + k * 4f, CURB + 0.025f, z1 - 12f, 0.12f, 0.02f, 5f, C("#F4F4F4")) }
        for (k in 0 until 10) if (rng.f() < 0.55f) parkedCar(b, x0 + 5f + k * 4f, if (k % 2 == 0) z1 - 5f else z1 - 12f, 1, C(rng.pick(CARC)), CURB + 0.02f)
        b.m(Mt.PLASTER, 0.5f)
        lb(b, l, 0f, CURB + 3.5f, 18f + 6.5f, x1 - x0 - 6f, 7f, 13f, C("#F6F2EA"))
        lsolid(l, 0f, 24.5f, x1 - x0 - 6f, 13.3f)
        b.m(Mt.PLASTER, 0.5f)
        lb(b, l, 0f, CURB + 6.6f, 17.9f, x1 - x0 - 6f, 0.8f, 0.3f, C("#D62828"))
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, CURB + 1.6f, 17.95f, 14f, 2.9f, 0.06f, C("#45647A"))
        sign(b, l, 0f, CURB + 4.0f, 17.85f, 12f, 1.5f, S_SUPER)
        // carrinhos
        for (k in 0 until 5) { b.m(Mt.METAL, 1f); lb(b, l, 9f + k * 0.35f, CURB + 0.55f, 16.8f, 0.6f, 0.5f, 0.9f, C("#B0B6BC")) }
        return 10f
    }

    private fun gasStation(b: MB, fl: Flora.Batch, rng: Rng, x0: Float, z0: Float, x1: Float, z1: Float): Float {
        plaza(b, x0, z0, x1, z1)
        // posto de frente para a avenida (-z)
        val l = L((x0 + x1) / 2, z0, 0f, -1f)
        b.m(Mt.ASPHALT, 0.3f)
        lb(b, l, 0f, CURB + 0.01f, 9f, x1 - x0 - 4f, 0.02f, 16f, C("#D6D6D6"))
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, CURB + 5.2f, 9f, 18f, 0.7f, 10f, C("#F5F5F5"))
        b.m(Mt.PLAIN)
        lb(b, l, 0f, CURB + 5.2f, 3.95f, 18.05f, 0.5f, 0.06f, C("#0F7A3D"))
        lb(b, l, 0f, CURB + 5.2f, 14.05f, 18.05f, 0.5f, 0.06f, C("#0F7A3D"))
        for (k in 0 until 3) {
            val px = -6f + k * 6f
            b.m(Mt.METAL, 1f)
            lb(b, l, px, CURB + 2.5f, 9f, 0.3f, 5f, 0.3f, C("#DADADA"))
            lb(b, l, px, CURB + 0.1f, 9f, 1.2f, 0.2f, 4f, C("#BDBDBD"))
            for (s in floatArrayOf(-1.2f, 1.2f)) {
                lb(b, l, px, CURB + 0.8f, 9f + s, 0.6f, 1.6f, 0.45f, C("#0F7A3D"))
                lb(b, l, px, CURB + 1.25f, 9f + s - 0.24f, 0.4f, 0.35f, 0.02f, C("#1A1A1A"))
                lsolid(l, px, 9f + s, 0.8f, 0.6f)
            }
        }
        sign(b, l, 0f, CURB + 5.0f, 3.9f, 5f, 0.45f, S_POSTO)
        // totem de preços
        b.m(Mt.METAL, 1f)
        lb(b, l, (x1 - x0) / 2 - 3f, CURB + 2.5f, 1.2f, 0.4f, 5f, 0.4f, C("#777777"))
        lb(b, l, (x1 - x0) / 2 - 3f, CURB + 5.4f, 1.2f, 2.0f, 2.4f, 0.4f, C("#0F7A3D"))
        sign(b, l, (x1 - x0) / 2 - 3f, CURB + 6.0f, 0.98f, 1.8f, 0.25f, S_POSTO)
        // conveniência
        b.m(Mt.PLASTER, 0.5f)
        lb(b, l, 0f, CURB + 2f, 19f + 4f, 14f, 4f, 8f, C("#FFFFFF"))
        lsolid(l, 0f, 23f, 14.3f, 8.3f)
        b.m(Mt.METAL, 1f)
        lb(b, l, 0f, CURB + 1.4f, 18.97f, 9f, 2.4f, 0.06f, C("#45647A"))
        sign(b, l, 0f, CURB + 3.0f, 18.9f, 6f, 0.7f, S_CONV)
        // lado de trás: oficina/lava-jato e casas
        shopRow(b, rng, L((x0 + x1) / 2, z1, 0f, 1f), x1 - x0 - 2f, intArrayOf(S_LANCH, S_ELET, S_PET), 10f)
        return 8f
    }

    private fun hospital(b: MB, fl: Flora.Batch, rng: Rng, x0: Float, z0: Float, x1: Float, z1: Float): Float {
        plaza(b, x0, z0, x1, z1)
        val l = L((x0 + x1) / 2, z0, 0f, -1f)   // entrada virada para a rua de baixo
        val w = x1 - x0 - 8f
        // bloco principal com fachada branca, 6 andares
        val h = tower(b, rng, l, 0f, 12f, w, 20f, 6, C("#F7F9FB"), S_HOSP)
        // ala do pronto-socorro na frente, mais baixa, com cobertura para ambulância
        b.m(Mt.PLASTER, 0.5f)
        lb(b, l, -w / 4, CURB + 2.5f, 7f, w / 2, 5f, 10f, C("#FFFFFF"))
        lsolid(l, -w / 4, 7f, w / 2 + 0.3f, 10.3f)
        lb(b, l, -w / 4, CURB + 4.8f, 6.98f, w / 2 + 0.2f, 0.4f, 10.2f, C("#D62828"))
        b.m(Mt.METAL, 1f)
        lb(b, l, -w / 4, CURB + 1.3f, 1.97f, 6f, 2.6f, 0.06f, C("#45647A"))
        sign(b, l, -w / 4, CURB + 3.2f, 1.9f, 7f, 0.8f, S_PS)
        lb(b, l, w / 6, CURB + 3.6f, 3f, 9f, 0.25f, 6f, C("#E8ECEF"))
        for (s in floatArrayOf(-4f, 4f)) lb(b, l, w / 6 + s, CURB + 1.8f, 0.6f, 0.25f, 3.6f, 0.25f, C("#C8CCD0"))
        // cruz vermelha grande na fachada e no teto
        b.m(Mt.PLAIN)
        lb(b, l, w / 4, CURB + 4.2f + 6 * 3f - 3f, 11.85f, 3.2f, 1.0f, 0.12f, C("#D62828"), false)
        lb(b, l, w / 4, CURB + 4.2f + 6 * 3f - 3f, 11.85f, 1.0f, 3.2f, 0.12f, C("#D62828"), false)
        // heliponto
        val hx = l.wx(w / 4, 22f); val hz = l.wz(w / 4, 22f); val ty = CURB + 4.2f + 18f + 0.12f
        b.cyl(hx, ty, hz, 4.2f, 4.2f, 0.06f, C("#3C3F44"), true, 24)
        b.cyl(hx, ty + 0.01f, hz, 3.9f, 3.9f, 0.06f, C("#F2C230"), true, 24)
        b.cyl(hx, ty + 0.02f, hz, 3.6f, 3.6f, 0.06f, C("#3C3F44"), true, 24)
        b.box(hx - 0.9f, ty + 0.1f, hz, 0.35f, 0.02f, 2.6f, C("#FFFFFF")); b.box(hx + 0.9f, ty + 0.1f, hz, 0.35f, 0.02f, 2.6f, C("#FFFFFF")); b.box(hx, ty + 0.1f, hz, 1.8f, 0.02f, 0.35f, C("#FFFFFF"))
        // ambulâncias
        for (k in 0 until 2) {
            val ax = l.wx(w / 6 - 2f + k * 4f, 3f); val az = l.wz(w / 6 - 2f + k * 4f, 3f)
            carGeom(b, ax, CURB, az, 1, C("#FFFFFF"), true)
            b.m(Mt.PLAIN)
            b.box(ax, CURB + 1.2f, az, 1.84f, 0.18f, 5.0f, C("#D62828"))
            b.box(ax, CURB + 2.2f, az + 1.4f, 1.0f, 0.12f, 0.25f, C("#E53935"), false)
            solid(ax - 1f, az - 2.7f, ax + 1f, az + 2.7f)
        }
        // jardim e bancos na frente
        for (k in 0 until 5) roundTree(b, l.wx(-w / 2 + 3f + k * (w - 6f) / 4f, -0f + 0.2f + 1.2f), l.wz(-w / 2 + 3f + k * (w - 6f) / 4f, 1.4f), 0.9f, rng)
        // estacionamento atrás
        b.m(Mt.ASPHALT, 0.3f)
        b.box((x0 + x1) / 2, CURB + 0.01f, z1 - 7f, x1 - x0 - 4f, 0.02f, 12f, C("#D0D0D0"))
        for (k in 0 until 9) if (rng.f() < 0.6f) parkedCar(b, x0 + 5f + k * 4.4f, z1 - 7f, 1, C(rng.pick(CARC)), CURB + 0.02f)
        return h
    }

    private fun fountain(b: MB, x: Float, z: Float) {
        b.m(Mt.STONE, 0.8f)
        b.cyl(x, CURB, z, 4.2f, 4.2f, 0.55f, C("#D9D3C7"), true, 28)
        b.m(Mt.PLAIN)
        b.cyl(x, CURB + 0.4f, z, 3.9f, 3.9f, 0.18f, C("#5CC6E6"), true, 28)
        b.m(Mt.STONE, 0.8f)
        b.cyl(x, CURB + 0.5f, z, 0.5f, 0.35f, 1.6f, C("#D9D3C7"), true, 14)
        b.cyl(x, CURB + 2.0f, z, 1.6f, 1.2f, 0.25f, C("#D9D3C7"), true, 20)
        b.m(Mt.PLAIN); b.al = 0.75f
        b.cyl(x, CURB + 2.2f, z, 0.12f, 0.04f, 1.1f, C("#BFEFFF"), true, 8)
        b.cyl(x, CURB + 0.55f, z, 1.65f, 1.3f, 1.5f, C("#BFEFFF"), true, 18)
        b.al = 1f
        solid(x - 4.3f, z - 4.3f, x + 4.3f, z + 4.3f)
    }

    private fun praca(b: MB, fl: Flora.Batch, rng: Rng, x0: Float, z0: Float, x1: Float, z1: Float): Float {
        lawn(b, x0, z0, x1, z1)
        val cx = (x0 + x1) / 2; val cz = (z0 + z1) / 2
        b.m(Mt.PAVER, 0.7f)
        b.box(cx, CURB + 0.01f, cz, 4f, 0.02f, z1 - z0, C("#E5DCCB"))
        b.box(cx, CURB + 0.01f, cz, x1 - x0, 0.02f, 4f, C("#E5DCCB"))
        b.cyl(cx, CURB, cz, 9f, 9f, 0.03f, C("#E5DCCB"), true, 32)
        fountain(b, cx, cz)
        // canteiros de flores em volta
        val flw = arrayOf("fl_daisy", "fl_lav", "fl_poppy", "fl_tulip", "fl_yellow")
        for (k in 0 until 4) {
            val a = (k * 90 + 45) * Math.PI / 180
            val fx = cx + 13f * cos(a).toFloat(); val fz = cz + 13f * sin(a).toFloat()
            b.m(Mt.STONE, 0.8f)
            b.cyl(fx, CURB, fz, 2.4f, 2.4f, 0.35f, C("#BCA88E"), true, 16)
            for (m in 0 until 14) {
                val rr = rng.r(0f, 2.0f); val aa = rng.r(0f, 6.28f)
                fl.place(flw[(k + m) % 5], (fx + rr * cos(aa)).toDouble(), (CURB + 0.35f).toDouble(), (fz + rr * sin(aa)).toDouble(), rng.r(1.2f, 1.6f).toDouble(), rng.r(0f, 6f).toDouble())
            }
        }
        // bancos virados para a fonte, árvores e coreto de placa
        for (k in 0 until 8) {
            val a = (k * 45 + 22.5) * Math.PI / 180
            val bx = cx + 7.6f * cos(a).toFloat(); val bz = cz + 7.6f * sin(a).toFloat()
            val ax = if (abs(cos(a)) > abs(sin(a))) (if (cos(a) > 0) 1f else -1f) else 0f
            val az = if (ax == 0f) (if (sin(a) > 0) 1f else -1f) else 0f
            bench(b, L(bx, bz, -ax, -az), 0f, 0f)
        }
        for (k in 0 until 14) {
            val tx = rng.r(x0 + 3f, x1 - 3f); val tz = rng.r(z0 + 3f, z1 - 3f)
            if (abs(tx - cx) < 3.5f || abs(tz - cz) < 3.5f || (abs(tx - cx) < 16f && abs(tz - cz) < 16f)) continue
            if (k % 4 == 0) fl.place("pine_a", tx.toDouble(), CURB.toDouble(), tz.toDouble(), 1.2, rng.r(0f, 6f).toDouble())
            else roundTree(b, tx, tz, rng.r(1.0f, 1.4f), rng)
        }
        for (s in intArrayOf(-1, 1)) {
            streetLamp(b, cx + s * 2.6f, cz - 14f, 0f, 0f); streetLamp(b, cx + s * 2.6f, cz + 14f, 0f, 0f)
        }
        sign(b, L(cx + 3.2f, z0 + 2.5f, 0f, -1f), 0f, CURB + 2.0f, 0f, 4.4f, 0.55f, S_PRACA)
        b.m(Mt.WOOD, 1f)
        for (s in floatArrayOf(-2f, 2f)) b.box(cx + 3.2f + s, CURB + 1.1f, z0 + 2.6f, 0.15f, 2.2f, 0.15f, C("#6D4C33"))
        // academia ao ar livre num canto
        val gx = x0 + 9f; val gz = z1 - 9f
        b.m(Mt.PAVER, 0.7f)
        b.box(gx, CURB + 0.015f, gz, 10f, 0.03f, 10f, C("#F0C987"))
        b.m(Mt.METAL, 1f)
        for (k in 0 until 4) {
            val ex = gx - 3f + (k % 2) * 6f; val ez = gz - 3f + (k / 2) * 6f
            b.box(ex, CURB + 1.0f, ez, 0.12f, 2.0f, 0.12f, C("#F2C230"))
            b.box(ex, CURB + 1.9f, ez, 1.6f, 0.1f, 0.1f, C("#2E7D32"))
            b.box(ex + 0.7f, CURB + 0.9f, ez, 0.1f, 1.8f, 0.1f, C("#2E7D32"))
        }
        sign(b, L(gx, gz + 5.5f, 0f, 1f), 0f, CURB + 1.6f, 0f, 4f, 0.5f, 31)
        return 8f
    }

    private fun park(b: MB, fl: Flora.Batch, rng: Rng, x0: Float, z0: Float, x1: Float, z1: Float): Float {
        lawn(b, x0, z0, x1, z1)
        val cx = (x0 + x1) / 2; val cz = (z0 + z1) / 2
        // lago
        b.m(Mt.PLAIN)
        b.cyl(cx + 4f, CURB - 0.05f, cz - 3f, 11f, 11f, 0.08f, C("#C9B79A"), true, 30)
        b.cyl(cx + 4f, CURB - 0.04f, cz - 3f, 10f, 10f, 0.1f, C("#4FB6D6"), true, 30)
        solid(cx - 6f, cz - 12f, cx + 14f, cz + 6f)
        // pista de caminhada em volta
        b.m(Mt.PAVER, 0.7f)
        for (k in 0 until 40) {
            val a0 = k * 6.283f / 40; val a1 = (k + 1) * 6.283f / 40
            val r = 19f
            b.box(cx + r * cos((a0 + a1) / 2), CURB + 0.012f, cz + r * sin((a0 + a1) / 2), 3.2f, 0.02f, 3.2f, C("#E1D2B6"))
        }
        // playground
        val px = x0 + 7f; val pz = z0 + 7f
        b.m(Mt.PLAIN)
        b.box(px, CURB + 0.02f, pz, 9f, 0.04f, 9f, C("#E8C99A"))
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-1.5f, 1.5f)) b.box(px + s, CURB + 1.2f, pz - 2f, 0.1f, 2.4f, 0.1f, C("#E53935"))
        b.box(px, CURB + 2.4f, pz - 2f, 3.2f, 0.1f, 0.1f, C("#E53935"))
        for (s in floatArrayOf(-0.6f, 0.6f)) { b.box(px + s, CURB + 1.3f, pz - 2f, 0.02f, 2.1f, 0.02f, C("#555555")); b.box(px + s, CURB + 0.3f, pz - 2f, 0.5f, 0.05f, 0.25f, C("#1B98E0")) }
        b.box(px + 1.5f, CURB + 0.9f, pz + 2f, 1.6f, 1.8f, 1.6f, C("#F2C230"))
        b.m(Mt.PLAIN)
        q(b, floatArrayOf(px + 2.3f, CURB + 1.8f, pz + 1.5f, px + 2.3f, CURB + 1.8f, pz + 2.5f, px + 5f, CURB + 0.1f, pz + 2.5f, px + 5f, CURB + 0.1f, pz + 1.5f), C("#2A9D8F"))
        // muitas árvores
        for (k in 0 until 26) {
            val tx = rng.r(x0 + 2f, x1 - 2f); val tz = rng.r(z0 + 2f, z1 - 2f)
            val dx = tx - cx; val dz = tz - cz
            if (dx * dx + dz * dz < 23f * 23f && dx * dx + dz * dz > 15f * 15f) continue
            if ((tx - cx - 4f) * (tx - cx - 4f) + (tz - cz + 3f) * (tz - cz + 3f) < 13f * 13f) continue
            if (abs(tx - px) < 6f && abs(tz - pz) < 6f) continue
            if (k % 3 == 0) fl.place("pine_a", tx.toDouble(), CURB.toDouble(), tz.toDouble(), rng.r(1.1f, 1.5f).toDouble(), rng.r(0f, 6f).toDouble())
            else roundTree(b, tx, tz, rng.r(1.1f, 1.6f), rng)
        }
        for (k in 0 until 6) {
            val a = k * 1.047f + 0.4f
            bench(b, L(cx + 21.5f * cos(a), cz + 21.5f * sin(a), if (abs(cos(a)) > 0.7f) -sign1(cos(a)) else 0f, if (abs(cos(a)) > 0.7f) 0f else -sign1(sin(a))), 0f, 0f)
        }
        return 8f
    }

    private fun sign1(v: Float) = if (v >= 0f) 1f else -1f

    private fun school(b: MB, fl: Flora.Batch, rng: Rng, x0: Float, z0: Float, x1: Float, z1: Float): Float {
        lawn(b, x0, z0, x1, z1)
        val l = L((x0 + x1) / 2, z1, 0f, 1f)   // de frente para a rua de trás da casa
        val h = tower(b, rng, l, 0f, 4f, x1 - x0 - 8f, 14f, 2, C("#FFF1D6"), S_ESC)
        // quadra
        val qx = (x0 + x1) / 2; val qz = z0 + 13f
        b.m(Mt.PLAIN)
        b.box(qx, CURB + 0.015f, qz, 30f, 0.03f, 17f, C("#3C8D5A"))
        b.box(qx, CURB + 0.03f, qz, 28f, 0.03f, 15f, C("#2F6FB0"))
        val wl = C("#FFFFFF")
        b.box(qx, CURB + 0.05f, qz - 7.5f, 28f, 0.02f, 0.1f, wl); b.box(qx, CURB + 0.05f, qz + 7.5f, 28f, 0.02f, 0.1f, wl)
        b.box(qx - 14f, CURB + 0.05f, qz, 0.1f, 0.02f, 15f, wl); b.box(qx + 14f, CURB + 0.05f, qz, 0.1f, 0.02f, 15f, wl)
        b.box(qx, CURB + 0.05f, qz, 0.1f, 0.02f, 15f, wl)
        b.cyl(qx, CURB + 0.045f, qz, 2.5f, 2.5f, 0.01f, C("#2F6FB0"), true, 24)
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-1f, 1f)) {
            b.box(qx + s * 14f, CURB + 1.0f, qz - 1.5f, 0.1f, 2f, 0.1f, wl); b.box(qx + s * 14f, CURB + 1.0f, qz + 1.5f, 0.1f, 2f, 0.1f, wl)
            b.box(qx + s * 14f, CURB + 2.0f, qz, 0.1f, 0.1f, 3.1f, wl)
        }
        // alambrado
        b.m(Mt.PLAIN); b.al = 0.55f
        b.box(qx, CURB + 1.5f, qz - 8.6f, 30f, 3f, 0.03f, C("#9BA3A8")); b.box(qx, CURB + 1.5f, qz + 8.6f, 30f, 3f, 0.03f, C("#9BA3A8"))
        b.box(qx - 15f, CURB + 1.5f, qz, 0.03f, 3f, 17f, C("#9BA3A8")); b.box(qx + 15f, CURB + 1.5f, qz, 0.03f, 3f, 17f, C("#9BA3A8"))
        b.al = 1f
        solid(qx - 15.2f, qz - 8.8f, qx + 15.2f, qz - 8.4f); solid(qx - 15.2f, qz + 8.4f, qx + 15.2f, qz + 8.8f)
        // ônibus escolar
        carGeom(b, x0 + 5f, CURB, z1 - 9f, 1, C("#F2C230"), true)
        solid(x0 + 4f, z1 - 11.7f, x0 + 6f, z1 - 6.3f)
        for (k in 0 until 5) roundTree(b, x1 - 3f, z0 + 4f + k * 9f, 1.1f, rng)
        return h
    }

    private fun police(b: MB, fl: Flora.Batch, rng: Rng, x0: Float, z0: Float, x1: Float, z1: Float): Float {
        plaza(b, x0, z0 + 22f, x1, z1)
        val w = (x1 - x0) / 2 - 3f
        val l1 = L(x0 + (x1 - x0) * 0.27f, z1, 0f, 1f)
        val h1 = tower(b, rng, l1, 0f, 4f, w, 16f, 3, C("#E3E8EE"), S_POL)
        for (k in 0 until 2) {
            val ax = l1.wx(-4f + k * 5f, 1.8f); val az = l1.wz(-4f + k * 5f, 1.8f)
            carGeom(b, ax, CURB, az, 0, C("#FFFFFF"), false, C("#0E2A5C"))
            b.m(Mt.PLAIN); b.box(ax - 0.2f, CURB + 1.62f, az, 0.3f, 0.12f, 1.2f, C("#1E88E5"), false)
            solid(ax - 2.2f, az - 1f, ax + 2.2f, az + 1f)
        }
        val l2 = L(x0 + (x1 - x0) * 0.75f, z1, 0f, 1f)
        val h2 = tower(b, rng, l2, 0f, 4f, w, 16f, 2, C("#F3D9D2"), S_BOMB)
        b.m(Mt.METAL, 1f)
        for (k in 0 until 2) lb(b, l2, -3.5f + k * 7f, CURB + 1.7f, 3.92f, 5f, 3.2f, 0.05f, C("#C62828"))
        carGeom(b, l2.wx(-3.5f, 0.5f), CURB, l2.wz(-3.5f, 0.5f), 1, C("#C62828"), true)
        solid(l2.wx(-3.5f, 0.5f) - 1f, l2.wz(-3.5f, 0.5f) - 2.7f, l2.wx(-3.5f, 0.5f) + 1f, l2.wz(-3.5f, 0.5f) + 2.7f)
        // lado de cá: casas
        lawn(b, x0, z0, x1, z0 + 22f)
        for (k in 0 until 4) house(b, fl, rng, L(x0 + (x1 - x0) / 4f * (k + 0.5f), z0, 0f, -1f), (x1 - x0) / 4f, 22f)
        return max(h1, h2)
    }

    // ------------------------------------------------------------ trânsito

    class Car(val lane: Int, var s: Float, var v: Float, val vmax: Float, val mesh: Int) {
        var x = 0f; var z = 0f; var axis = 0; var dir = 1; var yaw = 0f
    }
    private class Lane(val axis: Int, val dir: Int, val c: Float, val lo: Float, val hi: Float)
    private val lanes = ArrayList<Lane>()
    val cars = ArrayList<Car>()
    var carMeshes: Array<Mesh?> = arrayOfNulls(0)
        private set
    private var crossX = FloatArray(0)   // centros das ruas cruzadas (em x, para quem anda em x)
    private var crossZ = FloatArray(0)
    private var tLight = 0f
    val lightPhase: Int get() { val t = tLight % 24f; return if (t < 10f) 0 else if (t < 12f) 1 else if (t < 22f) 2 else 3 }

    /** Malhas dos carros que andam (centradas, comprimento em +z). */
    fun buildCarMeshes() {
        val list = ArrayList<Mesh?>()
        for (c in CARC) { val b = MB(); carGeom(b, 0f, 0f, 0f, 1, C(c), false); list.add(b.toMesh(true)) }
        run { val b = MB(); carGeom(b, 0f, 0f, 0f, 1, C("#F2C230"), false); b.m(Mt.PLAIN); b.box(0f, 1.66f, -0.2f, 0.7f, 0.18f, 0.3f, C("#222222")); list.add(b.toMesh(true)) }   // táxi
        run { val b = MB(); carGeom(b, 0f, 0f, 0f, 1, C("#F4F4F4"), true, C("#1F6FD1")); list.add(b.toMesh(true)) }   // van
        carMeshes = list.toTypedArray()
    }

    private fun spawnTraffic() {
        lanes.clear(); cars.clear()
        for (k in 0 until 6) {
            val zc = (bandZ[k * 2] + bandZ[k * 2 + 1]) / 2
            lanes.add(Lane(0, 1, zc + 2.2f, X0, X1)); lanes.add(Lane(0, -1, zc - 2.2f, X0, X1))
            val xc = (bandX[k * 2] + bandX[k * 2 + 1]) / 2
            lanes.add(Lane(1, 1, xc - 2.2f, Z0, Z1)); lanes.add(Lane(1, -1, xc + 2.2f, Z0, Z1))
        }
        crossX = FloatArray(4) { (bandX[(it + 1) * 2] + bandX[(it + 1) * 2 + 1]) / 2 }
        crossZ = FloatArray(4) { (bandZ[(it + 1) * 2] + bandZ[(it + 1) * 2 + 1]) / 2 }
        val rng = Rng(4242)
        for ((i, ln) in lanes.withIndex()) {
            val n = 2 + rng.i(2)
            for (k in 0 until n) {
                val s = ln.lo + (ln.hi - ln.lo) * (k + rng.r(0.1f, 0.6f)) / n
                val vm = rng.r(8f, 12f)
                cars.add(Car(i, s, vm * 0.5f, vm, rng.i(12)))
            }
        }
        for (c in cars) place(c)
    }

    private fun place(c: Car) {
        val ln = lanes[c.lane]
        c.axis = ln.axis; c.dir = ln.dir
        if (ln.axis == 0) { c.x = c.s; c.z = ln.c; c.yaw = if (ln.dir > 0) 90f else -90f }
        else { c.x = ln.c; c.z = c.s; c.yaw = if (ln.dir > 0) 0f else 180f }
    }

    /** Anda o trânsito e os pedestres. [px]/[pz] = jogador (os carros param para ele). */
    fun update(dt0: Float, px: Float, pz: Float) {
        if (!on) return
        val dt = dt0.coerceIn(0f, 0.1f)
        tLight += dt
        val ph = lightPhase
        // carro da frente em cada faixa
        for (c in cars) {
            val ln = lanes[c.lane]
            var target = c.vmax
            // semáforo
            val green = if (ln.axis == 0) ph == 0 else ph == 2
            val yellow = if (ln.axis == 0) ph == 1 else ph == 3
            if (!green) {
                val cross = if (ln.axis == 0) crossX else crossZ
                val half = ROAD / 2 + 1.6f + 2.2f   // linha de parada (frente do carro)
                for (cc in cross) {
                    val dist = (cc - ln.dir * half - c.s) * ln.dir   // até a linha de parada
                    if (dist > -0.5f && dist < 30f) {
                        if (yellow && dist < 6f) break   // já em cima: passa no amarelo
                        target = min(target, sqrt(max(0f, dist - 0.3f) * 2f * 5f))
                        break
                    }
                }
            }
            // fila: carro à frente na mesma faixa
            var gap = Float.MAX_VALUE
            for (o in cars) {
                if (o === c || o.lane != c.lane) continue
                var d = (o.s - c.s) * ln.dir
                if (d < 0f) d += (ln.hi - ln.lo)
                if (d < gap) gap = d
            }
            if (gap < 40f) target = min(target, max(0f, (gap - 6.5f)) * 1.2f)
            // jogador na frente
            val ax = if (ln.axis == 0) px else pz; val pc = if (ln.axis == 0) pz else px
            if (abs(pc - ln.c) < 2.2f) {
                val d = (ax - c.s) * ln.dir
                if (d > 0f && d < 14f) target = min(target, max(0f, d - 4f) * 1.0f)
            }
            val acc = if (target > c.v) 3f else 7f
            c.v += (target - c.v).coerceIn(-acc * dt, acc * dt)
            if (c.v < 0f) c.v = 0f
            c.s += c.v * dt * ln.dir
            if (c.s > ln.hi) c.s -= (ln.hi - ln.lo) else if (c.s < ln.lo) c.s += (ln.hi - ln.lo)
            place(c)
        }
        // pedestres
        for (p in peds) {
            val dx = px - p.x; val dz = pz - p.z
            val near = dx * dx + dz * dz < 1.2f
            val tv = if (near) 0f else p.vmax
            p.v += (tv - p.v) * min(1f, dt * 4f)
            p.t += p.v * dt * p.dir
            val per = p.per
            if (p.t > per) p.t -= per else if (p.t < 0f) p.t += per
            pedPlace(p, dt)
            p.ph += p.v * dt * 5.2f
        }
    }

    // ------------------------------------------------------------ pedestres

    class Ped(val x0: Float, val z0: Float, val x1: Float, val z1: Float, var t: Float, val dir: Int, val vmax: Float, val look: Int) {
        var x = 0f; var z = 0f; var yaw = 0f; var v = 0f; var ph = 0f
        val per: Float get() = 2 * (x1 - x0) + 2 * (z1 - z0)
    }
    val peds = ArrayList<Ped>()
    var pedBody: Array<Mesh?> = arrayOfNulls(0)
        private set
    var pedLeg: Array<Mesh?> = arrayOfNulls(0)
        private set
    var pedArm: Array<Mesh?> = arrayOfNulls(0)
        private set

    private fun pedPlace(p: Ped, dt: Float) {
        val w = p.x1 - p.x0; val d = p.z1 - p.z0
        var t = p.t
        var tx: Float; var tz: Float; var yaw: Float
        if (t < w) { tx = p.x0 + t; tz = p.z0; yaw = 90f }
        else if (t < w + d) { t -= w; tx = p.x1; tz = p.z0 + t; yaw = 0f }
        else if (t < 2 * w + d) { t -= w + d; tx = p.x1 - t; tz = p.z1; yaw = -90f }
        else { t -= 2 * w + d; tx = p.x0; tz = p.z1 - t; yaw = 180f }
        if (p.dir < 0) yaw += 180f
        p.x = tx; p.z = tz
        var dl = yaw - p.yaw
        while (dl > 180f) dl -= 360f
        while (dl < -180f) dl += 360f
        p.yaw += dl * min(1f, dt * 8f)
    }

    fun buildPeds() {
        val skins = arrayOf("#F1C7A5", "#D9A27E", "#A86F4C", "#7A4B2F", "#F6D8C0")
        val shirts = arrayOf("#D7263D", "#1B98E0", "#2A9D8F", "#F4A261", "#6A4C93", "#FFFFFF", "#333333", "#F2C14E")
        val pants = arrayOf("#2B3A55", "#4A4A4A", "#6B4F3A", "#1F1F1F", "#3D5A80")
        val hairs = arrayOf("#2B1B12", "#5A3A22", "#C9A15B", "#111111", "#8C4A2F")
        val bl = ArrayList<Mesh?>(); val ll = ArrayList<Mesh?>(); val al = ArrayList<Mesh?>()
        for (k in 0 until 10) {
            val sk = C(skins[k % 5]); val sh = C(shirts[(k * 3) % 8]); val pn = C(pants[(k * 2) % 5]); val hr = C(hairs[(k * 7) % 5])
            val woman = k % 2 == 1
            val b = MB(); b.m(Mt.FABRIC, 1f)
            b.rbox(0f, 1.18f, 0f, 0.42f, 0.56f, 0.24f, 0.06f, sh, true, 2)
            b.rbox(0f, 0.9f, 0f, 0.38f, 0.14f, 0.22f, 0.04f, pn, true, 2)
            if (woman) b.cyl(0f, 0.72f, 0f, 0.26f, 0.2f, 0.26f, pn, true, 10)
            b.m(Mt.PLAIN)
            b.cyl(0f, 1.44f, 0f, 0.06f, 0.06f, 0.1f, sk, true, 8)
            b.sphere(0f, 1.63f, 0f, 0.12f, sk, 0.14f, 9)
            b.sphere(0f, 1.69f, -0.015f, 0.128f, hr, 0.115f, 9)
            if (woman) b.rbox(0f, 1.5f, -0.1f, 0.22f, 0.3f, 0.06f, 0.03f, hr, true, 2)
            b.box(0.045f, 1.64f, 0.115f, 0.025f, 0.025f, 0.01f, C("#222222")); b.box(-0.045f, 1.64f, 0.115f, 0.025f, 0.025f, 0.01f, C("#222222"))
            bl.add(b.toMesh(true))
            val lg = MB(); lg.m(Mt.FABRIC, 1f)
            lg.rbox(0f, -0.4f, 0f, 0.14f, 0.8f, 0.15f, 0.04f, pn, true, 2)
            lg.m(Mt.PLAIN)
            lg.rbox(0f, -0.82f, 0.04f, 0.13f, 0.08f, 0.26f, 0.03f, C(if (k % 3 == 0) "#FFFFFF" else "#2A2A2A"), true, 2)
            ll.add(lg.toMesh(true))
            val ar = MB(); ar.m(Mt.FABRIC, 1f)
            ar.rbox(0f, -0.15f, 0f, 0.1f, 0.3f, 0.11f, 0.03f, sh, true, 2)
            ar.m(Mt.PLAIN)
            ar.rbox(0f, -0.42f, 0f, 0.085f, 0.3f, 0.09f, 0.03f, sk, true, 2)
            al.add(ar.toMesh(true))
        }
        pedBody = bl.toTypedArray(); pedLeg = ll.toTypedArray(); pedArm = al.toTypedArray()
        peds.clear()
        val rng = Rng(77)
        for (i in 0 until 5) for (j in 0 until 5) {
            val x0 = blkX[i * 2] - SIDE * 0.5f; val x1 = blkX[i * 2 + 1] + SIDE * 0.5f
            val z0 = blkZ[j * 2] - SIDE * 0.5f; val z1 = blkZ[j * 2 + 1] + SIDE * 0.5f
            val n = if (i in 1..3 && j in 1..4) 3 else 1
            for (k in 0 until n) {
                val p = Ped(x0, z0, x1, z1, 0f, if (rng.f() < 0.5f) 1 else -1, rng.r(1.0f, 1.45f), rng.i(10))
                p.t = rng.r(0f, p.per); p.v = p.vmax
                pedPlace(p, 1f); p.yaw = p.yaw
                peds.add(p)
            }
        }
    }
}
