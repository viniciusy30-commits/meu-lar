package com.vinicius.meular

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Typeface
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

/**
 * Etapa 122: a cidade de verdade.
 * 7 × 7 quarteirões (o da casa no meio), bairros com estilos diferentes, praia com calçadão e píer,
 * parque de diversões, mansões, terrenos à venda, prédios e casas onde dá para entrar (mobiliados).
 *
 * Desempenho:
 *  - cada quarteirão tem duas malhas: "perto" (tudo, com interiores) e "longe" (só volumes e fachadas);
 *  - corte por câmera e por distância; névoa esconde o fim do mundo;
 *  - prédio em que o jogador entra: paredes de cima e telhado ficam de fora do desenho (faixa de vértices pulada),
 *    sem malha extra e sem chamada extra.
 */
object City {
    const val ROAD = 16f
    /** Etapa 130: largura de cada rua entre quarteirões (0..5). As avenidas (24 m) têm canteiro central; as travessas (14 m) são mais estreitas.
     *  As ruas coladas no lote da casa (2 e 3) ficam em 16 m para não deslocar a praça e o que já está posicionado em volta dela. */
    val SW_X = floatArrayOf(14f, 24f, 16f, 16f, 24f, 14f)
    val SW_Z = floatArrayOf(24f, 14f, 16f, 16f, 24f, 14f)
    fun isAvenue(w: Float) = w >= 22f
    const val SIDE = 3.5f
    /** raio médio da margem do lago em relação à meia largura da malha da água */
    const val LAKE_EDGE = 0.78f
    const val CURB = 0.15f
    const val FLOOR = 0.27f          // piso de dentro das construções
    const val NEAR = 70f             // até aqui o quarteirão usa a malha detalhada

    /** Construção em que se entra. [ranges]: material -> (início, fim) dos vértices escondidos quando o jogador está dentro. */
    class Bld(val x0: Float, val z0: Float, val x1: Float, val z1: Float, val chunk: Int, val name: String) {
        val ranges = HashMap<Int, IntArray>()
        var forSale = false
        var price = 0
    }

    /**
     * Pedaço da cidade. [near] = malha detalhada (pode ser nula: quarteirões são carregados perto do jogador, em segundo plano,
     * e descartados quando ficam longe); [far] = versão simplificada, sempre presente.
     */
    class Chunk(@Volatile var near: Mesh?, val far: Mesh?, val x0: Float, val z0: Float, val x1: Float, val z1: Float, val h: Float) {
        val nearIdx = HashMap<Int, Int>()   // material -> índice da peça (só as do construtor, não as da flora)
        var glass = false
        var pend: Flora.Batch? = null       // flora a montar na thread do GL (precisa criar texturas)
        var lazyI = -1; var lazyJ = -1      // quarteirão que se recarrega sob demanda
        @Volatile var loading = false
        @Volatile var failed = false
        @Volatile var result: Pair<Mesh, Flora.Batch>? = null
        var lastNear = 0L
        /** Faixas (material -> início, fim) desta parte dentro da malha única de longe [farAll]. */
        var farRanges: HashMap<Int, IntArray>? = null
        var farMB: MB? = null
    }

    /** Etapa 122: todos os quarteirões vistos de longe numa malha só (poucas chamadas de desenho). */
    @Volatile var farAll: Mesh? = null
        private set

    /** Ponto de interesse do mapa. */
    class Place(val name: String, val x: Float, val z: Float, val color: Int, val icon: Char)

    @Volatile var on = false
        private set
    var chunks: List<Chunk> = emptyList()
        private set
    var lightMeshes: Array<Mesh?> = arrayOfNulls(4)
        private set
    fun setLights(a: Array<Mesh?>) { lightMeshes = a }
    val blds = ArrayList<Bld>()
    val places = ArrayList<Place>()

    // grade
    var bandX = FloatArray(0); private set
    var bandZ = FloatArray(0); private set
    var blkX = FloatArray(0); private set
    var blkZ = FloatArray(0); private set
    var X0 = 0f; private set
    var X1 = 0f; private set
    var Z0 = 0f; private set
    var Z1 = 0f; private set
    var lotX0 = 0f; private set
    var lotX1 = 0f; private set
    var lotZ0 = 0f; private set
    var lotZ1 = 0f; private set
    /** Praia: calçadão de Z1 até BEACH_Z, areia até SEA_Z, mar depois. */
    var BEACH_Z = 0f; private set
    var SEA_Z = 0f; private set
    var PIER_X = 0f; private set
    const val NB = 7
    /** Tipo de cada quarteirão [i][j] (i = coluna em x, j = linha em z). */
    var types: Array<Array<String>> = emptyArray(); private set
    val ROAD_NAMES_X = arrayOf("R. dos Ipês", "R. das Flores", "Av. Paulista", "R. do Sol", "Av. Atlântica", "R. das Palmeiras", "Av. Central", "Av. Beira-Mar")   // ruas ao longo de x (por faixa de z)
    val ROAD_NAMES_Z = arrayOf("R. Aurora", "Av. Brasil", "R. da Paz", "Av. das Nações", "R. Primavera", "Av. Santos Dumont", "R. do Porto", "Av. Litorânea")   // ruas ao longo de z (por faixa de x)

    private val solidsBy = HashMap<Int, ArrayList<FloatArray>>()   // por célula de 32 m
    private val bldBy = HashMap<Int, ArrayList<Bld>>()
    private fun cell(x: Float, z: Float) = (Math.floor(x / 32.0).toInt() + 1000) * 4096 + (Math.floor(z / 32.0).toInt() + 1000)

    fun addPlace(p: Place) { places.add(p) }

    fun addSolid(r: FloatArray) {
        val a = Math.floor(r[0] / 32.0).toInt(); val b = Math.floor(r[2] / 32.0).toInt()
        val c = Math.floor(r[1] / 32.0).toInt(); val d = Math.floor(r[3] / 32.0).toInt()
        for (i in a..b) for (j in c..d) solidsBy.getOrPut((i + 1000) * 4096 + (j + 1000)) { ArrayList() }.add(r)
    }

    fun addBld(bd: Bld) {
        blds.add(bd)
        val a = Math.floor(bd.x0 / 32.0).toInt(); val b = Math.floor(bd.x1 / 32.0).toInt()
        val c = Math.floor(bd.z0 / 32.0).toInt(); val d = Math.floor(bd.z1 / 32.0).toInt()
        for (i in a..b) for (j in c..d) bldBy.getOrPut((i + 1000) * 4096 + (j + 1000)) { ArrayList() }.add(bd)
    }

    fun bldAt(x: Float, z: Float): Bld? {
        val l = bldBy[cell(x, z)] ?: return null
        for (b in l) if (x > b.x0 && x < b.x1 && z > b.z0 && z < b.z1) return b
        return null
    }

    // ------------------------------------------------------------ letreiros (atlas 2048 × 1024: 4 colunas × 16 linhas de 512 × 64)

    val SIGNS = arrayOf(
        Triple("HOSPITAL", "#FFFFFF", "#D62828"), Triple("FARMÁCIA", "#1E9E5A", "#FFFFFF"), Triple("PADARIA", "#F4E1C1", "#7A4A1E"),
        Triple("SUPERMERCADO", "#D62828", "#FFFFFF"), Triple("LANCHONETE", "#FFD23F", "#C0392B"), Triple("PIZZARIA", "#1F5E3A", "#FFFFFF"),
        Triple("BANCO", "#14306B", "#F2C14E"), Triple("ACADEMIA", "#151515", "#FF8A00"), Triple("SALÃO DE BELEZA", "#F7A1C4", "#FFFFFF"),
        Triple("POSTO", "#0F7A3D", "#FFE14D"), Triple("CONVENIÊNCIA", "#FFFFFF", "#0F7A3D"), Triple("ESCOLA", "#1F6FD1", "#FFFFFF"),
        Triple("POLÍCIA", "#0E2A5C", "#FFFFFF"), Triple("CAFÉ", "#4A2C1A", "#F6E7CF"), Triple("LIVRARIA", "#2C3E50", "#F1C40F"),
        Triple("PET SHOP", "#25A8E0", "#FFFFFF"), Triple("ÓTICA", "#FFFFFF", "#222222"), Triple("SORVETERIA", "#FFC6DA", "#C2185B"),
        Triple("MODA", "#000000", "#FFFFFF"), Triple("RESTAURANTE", "#8E1B1B", "#FBE3B0"), Triple("BOMBEIROS", "#C62828", "#FFFFFF"),
        Triple("HOTEL", "#2B2B2B", "#E8C26E"), Triple("ELETRÔNICOS", "#1565C0", "#FFFFFF"), Triple("FLORICULTURA", "#7CB342", "#FFFFFF"),
        Triple("PRONTO-SOCORRO", "#D62828", "#FFFFFF"), Triple("ESTACIONAMENTO", "#1F4FA8", "#FFFFFF"), Triple("PRAÇA CENTRAL", "#5D4037", "#FFF3D6"),
        Triple("ACADEMIA AO AR LIVRE", "#2E7D32", "#FFFFFF"), Triple("À VENDA", "#C62828", "#FFFFFF"), Triple("TERRENO À VENDA", "#F2C230", "#1A1A1A"),
        Triple("PARQUE DE DIVERSÕES", "#6A1B9A", "#FFD54F"), Triple("QUIOSQUE", "#00838F", "#FFFFFF"), Triple("SALVA-VIDAS", "#D32F2F", "#FFEB3B"),
        Triple("IGREJA MATRIZ", "#4E342E", "#FFF3E0"), Triple("HAMBÚRGUER", "#FF6F00", "#FFFFFF"), Triple("SUSHI", "#111111", "#FF5252"),
        Triple("BARBEARIA", "#263238", "#FFFFFF"), Triple("PAPELARIA", "#FFEB3B", "#1565C0"), Triple("AÇAÍ", "#4A148C", "#E1BEE7"),
        Triple("MERCADINHO", "#2E7D32", "#FFEB3B"), Triple("CASA DE CÂMBIO", "#004D40", "#FFD54F"), Triple("CONDOMÍNIO", "#37474F", "#FFFFFF"),
        Triple("RESIDENCIAL", "#455A64", "#ECEFF1"), Triple("SHOPPING", "#880E4F", "#FFFFFF"), Triple("CINEMA", "#B71C1C", "#FFD600"),
        Triple("MONTANHA-RUSSA", "#E65100", "#FFFFFF"), Triple("RODA-GIGANTE", "#1565C0", "#FFFFFF"), Triple("CARROSSEL", "#AD1457", "#FFF59D"),
        Triple("BATE-BATE", "#2E7D32", "#FFFFFF"), Triple("PIPOCA", "#FBC02D", "#C62828"), Triple("ALGODÃO DOCE", "#F8BBD0", "#AD1457"),
        Triple("BEIRA-MAR", "#0277BD", "#FFFFFF"), Triple("PÍER", "#5D4037", "#FFFFFF"), Triple("ESCRITÓRIOS", "#263238", "#B0BEC5"),
        Triple("AV. BRASIL", "#1B7F3B", "#FFFFFF"), Triple("R. DAS FLORES", "#1B7F3B", "#FFFFFF"), Triple("AV. PAULISTA", "#1B7F3B", "#FFFFFF"),
        Triple("R. DO SOL", "#1B7F3B", "#FFFFFF"), Triple("AV. ATLÂNTICA", "#1B7F3B", "#FFFFFF"), Triple("R. DA PAZ", "#1B7F3B", "#FFFFFF"),
        Triple("AV. CENTRAL", "#1B7F3B", "#FFFFFF"), Triple("POUSADA", "#6D4C41", "#FFFFFF"), Triple("CLÍNICA", "#00897B", "#FFFFFF"))

    fun signIdx(name: String): Int { for (i in SIGNS.indices) if (SIGNS[i].first == name) return i; return 0 }

    fun signBitmap(): Bitmap {
        val bmp = Bitmap.createBitmap(2048, 1024, Bitmap.Config.ARGB_8888)
        val cv = Canvas(bmp)
        val p = Paint(Paint.ANTI_ALIAS_FLAG)
        p.typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD)
        for (i in 0 until 64) {
            val cx = (i % 4) * 512f; val cy = (i / 4) * 64f
            val s = SIGNS.getOrNull(i) ?: Triple("", "#FFFFFF", "#000000")
            val name = s.first
            p.style = Paint.Style.FILL; p.shader = null
            p.color = C(s.second)
            cv.drawRect(cx, cy, cx + 512f, cy + 64f, p)
            // brilho suave de cima para baixo (placa de acrílico)
            p.shader = android.graphics.LinearGradient(0f, cy, 0f, cy + 64f, 0x30FFFFFF, 0x20000000, android.graphics.Shader.TileMode.CLAMP)
            cv.drawRect(cx, cy, cx + 512f, cy + 64f, p)
            p.shader = null
            p.color = shade(C(s.second), -45)
            cv.drawRect(cx, cy, cx + 512f, cy + 3f, p); cv.drawRect(cx, cy + 61f, cx + 512f, cy + 64f, p)
            cv.drawRect(cx, cy, cx + 3f, cy + 64f, p); cv.drawRect(cx + 509f, cy, cx + 512f, cy + 64f, p)
            p.textSize = 42f
            var w = p.measureText(name)
            if (w > 470f) { p.textSize = 42f * 470f / w; w = p.measureText(name) }
            val fm = p.fontMetrics
            val ty = cy + 32f - (fm.ascent + fm.descent) / 2f
            p.color = 0x40000000
            cv.drawText(name, cx + 256f - w / 2f + 2f, ty + 2f, p)
            p.color = C(s.third)
            cv.drawText(name, cx + 256f - w / 2f, ty, p)
        }
        return bmp
    }

    // ------------------------------------------------------------ montagem

    class Rng(seed: Int) {
        private var s = seed.toLong() * 2654435761L + 12345L
        fun f(): Float { s = (s * 6364136223846793005L + 1442695040888963407L); return ((s ushr 33) and 0xFFFFFFL).toFloat() / 0xFFFFFF.toFloat() }
        fun r(a: Float, b: Float) = a + (b - a) * f()
        fun i(n: Int) = (f() * n).toInt().coerceIn(0, n - 1)
        fun <T> pick(a: Array<T>): T = a[i(a.size)]
        fun chance(p: Float) = f() < p
    }

    @Volatile private var token = 0
    /** Etapa 123: andamento da montagem (0..1) para a tela de carregamento. */
    @Volatile var progress = 0f
    /** Geração do contexto GL em que a cidade foi montada (sem cópia na memória, é preciso montar de novo se o contexto cair). */
    @Volatile var builtGen = -1
    /** Etapa 127: lagos (centro x, z, meia largura da malha, altura da água). */
    val lakes = java.util.concurrent.CopyOnWriteArrayList<FloatArray>()
    /** pontes em arco (x0, z0, x1, z1, altura da ponta, altura do arco) — andando por cima */
    val bridges = java.util.concurrent.CopyOnWriteArrayList<FloatArray>()
    /** Etapa 128: porta de uma construção — centro do vão (x, piso y, plano da parede z), lado de fora fz, vão w × h. */
    class Door(val x: Float, val y: Float, val z: Float, val fz: Float, val w: Float, val h: Float, val style: Int, val col: Int, val col2: Int, val name: String) {
        @JvmField var open = 0f
        @JvmField var spin = 0f
        @JvmField var spinV = 0f
        @JvmField var leaves: List<Doors.Leaf>? = null
    }
    val doors = java.util.concurrent.CopyOnWriteArrayList<Door>()
    @Volatile private var startGen = -1
    @Volatile var builds = 0
    /** Erro da montagem (mostrado na tela de carregamento em vez de travar). */
    @Volatile var error: String? = null

    /** Fração dos quarteirões perto de (x, z) que já têm o detalhe carregado. */
    fun nearFraction(x: Float, z: Float): Float {
        if (!on) return 0f
        var n = 0; var ok = 0
        for (c in chunks) {
            if (c.lazyI < 0) continue
            val dx = max(0f, max(c.x0 - x, x - c.x1)); val dz = max(0f, max(c.z0 - z, z - c.z1))
            if (dx * dx + dz * dz < NEAR * NEAR) { n++; if (c.near != null || c.failed) ok++ }
        }
        return if (n == 0) 1f else ok.toFloat() / n
    }

    /** Thread do GL: devolve buffers e zera tudo (antes de montar de novo). */
    fun clear() {
        token++
        on = false
        progress = 0f
        chunks.forEach { it.near?.release(); it.far?.release() }; chunks = emptyList()
        farAll?.release(); farAll = null
        Shade.mesh?.release(); Shade.mesh = null
        lakes.clear(); bridges.clear(); doors.clear()
        lightMeshes.forEach { it?.release() }; lightMeshes = arrayOfNulls(4)
        Vehicles.release(); CityFun.release()
        pedBody.forEach { it?.release() }; pedLeg.forEach { it?.release() }; pedArm.forEach { it?.release() }
        solidsBy.clear(); bldBy.clear(); blds.clear(); places.clear(); cars.clear(); peds.clear()
        Gps.clear()
        Town.clear()
    }

    /** Monta a cidade numa thread separada (o jogo continua rodando dentro de casa enquanto isso). */
    fun buildAsync(gw: Int, gh: Int) {
        val tk = token
        startGen = GlGen.gen
        Thread {
            try { error = null; build(gw, gh, tk) } catch (e: Throwable) { error = e.toString(); android.util.Log.e("City", "falha ao montar a cidade", e) }
        }.apply { priority = Thread.NORM_PRIORITY - 1 }.start()
    }

    private fun build(gw: Int, gh: Int, tk: Int) {
        val W = gw.toFloat(); val H = gh.toFloat()
        lotX0 = -10f; lotX1 = W + 10f; lotZ0 = -22f; lotZ1 = H + 9f
        // larguras dos quarteirões (a casa é a coluna/linha 3)
        val wx = floatArrayOf(48f, 52f, 48f, lotX1 - lotX0, 48f, 52f, 84f)
        val wz = floatArrayOf(48f, 50f, 48f, lotZ1 - lotZ0, 48f, 50f, 64f)
        blkX = FloatArray(14); blkZ = FloatArray(14)
        blkX[6] = lotX0; blkX[7] = lotX1; blkZ[6] = lotZ0; blkZ[7] = lotZ1
        for (k in 2 downTo 0) { blkX[k * 2 + 1] = blkX[(k + 1) * 2] - SW_X[k]; blkX[k * 2] = blkX[k * 2 + 1] - wx[k]; blkZ[k * 2 + 1] = blkZ[(k + 1) * 2] - SW_Z[k]; blkZ[k * 2] = blkZ[k * 2 + 1] - wz[k] }
        for (k in 4..6) { blkX[k * 2] = blkX[(k - 1) * 2 + 1] + SW_X[k - 1]; blkX[k * 2 + 1] = blkX[k * 2] + wx[k]; blkZ[k * 2] = blkZ[(k - 1) * 2 + 1] + SW_Z[k - 1]; blkZ[k * 2 + 1] = blkZ[k * 2] + wz[k] }
        bandX = FloatArray(16); bandZ = FloatArray(16)
        for (k in 0 until 8) {
            bandX[k * 2] = if (k == 0) blkX[0] - ROAD else blkX[k * 2 - 1]
            bandX[k * 2 + 1] = if (k == 7) blkX[13] + ROAD else blkX[k * 2]
            bandZ[k * 2] = if (k == 0) blkZ[0] - ROAD else blkZ[k * 2 - 1]
            bandZ[k * 2 + 1] = if (k == 7) blkZ[13] + ROAD else blkZ[k * 2]
        }
        X0 = bandX[0]; X1 = bandX[15]; Z0 = bandZ[0]; Z1 = bandZ[15]
        BEACH_Z = Z1 + 10f; SEA_Z = Z1 + 52f
        PIER_X = (blkX[6] + blkX[7]) / 2f

        // bairros: linha j = 0 é o fundo (longe da praia), j = 6 é a beira-mar
        types = Array(NB) { i -> Array(NB) { j -> T[j][i] } }

        val out = ArrayList<Chunk>()
        Shade.reset()   // Etapa 127: sombras projetadas
        progress = 0.04f
        if (TOWN) { buildTown(out, W, H, tk); return }
        CityGeo.roads(out)
        progress = 0.12f
        for (i in 0 until NB) for (j in 0 until NB) {
            val t = types[i][j]
            if (t == "home") continue
            val x0 = blkX[i * 2]; val x1 = blkX[i * 2 + 1]; val z0 = blkZ[j * 2]; val z1 = blkZ[j * 2 + 1]
            val g = CityGeo.Gen(out.size, Rng(i * 131 + j * 17 + 7), x0, z0, x1, z1)
            val h = CityGeo.block(g, t, i, j)
            if (t == "fun") out.add(g.finish(h))
            else { val c = g.finishFar(h); c.lazyI = i; c.lazyJ = j; c.farMB = g.f; out.add(c) }   // detalhe carregado quando o jogador chegar perto
            if (tk != token) return
            progress = 0.12f + 0.7f * (i * NB + j + 1) / (NB * NB)
        }
        // junta as versões de longe numa malha só, guardando a faixa de cada quarteirão
        run {
            val all = MB()
            for (c in out) {
                val f = c.farMB ?: continue
                val c0 = all.counts(); all.append(f); val c1 = all.counts()
                val r = HashMap<Int, IntArray>()
                for ((m, n1) in c1) { val n0 = c0[m] ?: 0; if (n1 > n0) r[m] = intArrayOf(n0, n1) }
                c.farRanges = r; c.farMB = null
            }
            farAll = all.toMesh(true)
        }
        progress = 0.84f
        out.add(CityFun.beach(out.size))
        out.add(CityGeo.ring())
        chunks = out
        progress = 0.9f
        CityGeo.buildLights()
        Vehicles.build()
        CityFun.buildRides()
        spawnTraffic()
        buildPeds()
        // pontos do mapa
        places.add(0, Place("Sua casa", W / 2f, H + 4f, 0xFF4CAF50.toInt(), 'C'))
        places.add(Place("Praia", PIER_X - 40f, (BEACH_Z + SEA_Z) / 2f, 0xFFFFC107.toInt(), 'P'))
        places.add(Place("Píer", PIER_X, SEA_Z + 20f, 0xFF8D6E63.toInt(), 'Í'))
        if (tk != token) return
        Shade.finish(); Shade.mesh?.gpuOnly()
        for (c in out) { c.near?.gpuOnly(); c.far?.gpuOnly() }
        farAll?.gpuOnly(); lightMeshes.forEach { it?.gpuOnly() }; Vehicles.meshes.forEach { it?.gpuOnly() }
        pedBody.forEach { it?.gpuOnly() }; pedLeg.forEach { it?.gpuOnly() }; pedArm.forEach { it?.gpuOnly() }
        for (d in CityFun.dyn) d.mesh.gpuOnly()
        builtGen = startGen   // Etapa 126: se o contexto caiu durante a montagem, monta de novo
        builds++
        on = true
    }

    /** Etapa 131: cidade nova (ruas curvas). A antiga (grade) fica no código só até a nova ficar completa. */
    const val TOWN = true

    private fun buildTown(out: ArrayList<Chunk>, W: Float, H: Float, tk: Int) {
        Town.clear()
        bandX = FloatArray(0); bandZ = FloatArray(0); blkX = FloatArray(0); blkZ = FloatArray(0)
        types = emptyArray()
        Town.build(out)
        X0 = Town.minX - 200f; X1 = Town.maxX + 200f; Z0 = Town.minZ - 200f; Z1 = Town.maxZ + 200f
        BEACH_Z = 1e6f; SEA_Z = 1e6f; PIER_X = -1e6f
        progress = 0.6f
        chunks = out
        Vehicles.build()
        spawnTownTraffic()
        buildPeds()
        places.add(0, Place("Sua casa", W / 2f, H + 4f, 0xFF4CAF50.toInt(), 'C'))
        if (tk != token) return
        Shade.finish(); Shade.mesh?.gpuOnly()
        for (c in out) { c.near?.gpuOnly(); c.far?.gpuOnly() }
        Vehicles.meshes.forEach { it?.gpuOnly() }
        pedBody.forEach { it?.gpuOnly() }; pedLeg.forEach { it?.gpuOnly() }; pedArm.forEach { it?.gpuOnly() }
        builtGen = startGen
        builds++
        progress = 1f
        on = true
    }

    private val loader = java.util.concurrent.Executors.newSingleThreadExecutor { r -> Thread(r, "cidade-detalhe").apply { priority = Thread.NORM_PRIORITY - 1 } }

    /** Pede a malha detalhada de um quarteirão (gerada de novo, igual à primeira vez, sem registrar colisões de novo). */
    fun requestNear(ci: Int) {
        val c = chunks.getOrNull(ci) ?: return
        if (c.lazyI < 0 || c.near != null || c.loading || c.result != null || c.failed) return
        c.loading = true
        val tk = token
        val i = c.lazyI; val j = c.lazyJ
        loader.execute {
            try {
                if (tk == token && TOWN) {
                    val g = CityGeo.Gen(ci, Rng(i * 13 + 1), c.x0, c.z0, c.x1, c.z1, false)
                    TownGeo.tile(g, i, false)
                    if (tk == token) c.result = Pair(g.b.toMesh(true), g.fl)
                } else if (tk == token) {
                    val g = CityGeo.Gen(ci, Rng(i * 131 + j * 17 + 7), blkX[i * 2], blkZ[j * 2], blkX[i * 2 + 1], blkZ[j * 2 + 1], false)
                    CityGeo.block(g, types[i][j], i, j)
                    if (tk == token) c.result = Pair(g.b.toMesh(true), g.fl)
                }
            } catch (e: Throwable) { c.failed = true; error = "quarteirão $i,$j: $e"; android.util.Log.e("City", "detalhe", e) }
            c.loading = false
        }
    }

    /** Thread do GL: instala malhas prontas, monta flora pendente e descarta detalhe de quarteirões longe. */
    fun service(ex: Float, ez: Float) {
        if (!on) return
        val now = System.currentTimeMillis()
        for ((ci, c) in chunks.withIndex()) {
            c.pend?.let { fl -> val n = c.near; if (n != null) { c.near = Mesh(n.parts + fl.build()).gpuOnly() }; c.pend = null }
            val r = c.result
            if (r != null) {
                c.result = null
                c.nearIdx.clear(); c.glass = false
                for ((k, p) in r.first.parts.withIndex()) { c.nearIdx[p.mat] = k; if (p.mat == Mt.GLASS) c.glass = true }
                c.near = Mesh(r.first.parts + r.second.build()).gpuOnly()
                c.lastNear = now
            }
            if (c.lazyI < 0) continue
            val dx = max(0f, max(c.x0 - ex, ex - c.x1)); val dz = max(0f, max(c.z0 - ez, ez - c.z1))
            val d2 = dx * dx + dz * dz
            if (d2 < NEAR * NEAR) { requestNear(ci); c.lastNear = now }
            else if (c.near != null && d2 > (NEAR + 45f) * (NEAR + 45f) && now - c.lastNear > 3000L) { c.near?.release(); c.near = null }
        }
    }

    /** Planta da cidade, por linha (z) e coluna (x). */
    private val T = arrayOf(
        arrayOf("res", "res", "apt", "school", "res", "park", "gas"),
        arrayOf("res", "church", "res", "police", "res", "apt", "super"),
        arrayOf("lots", "res", "res", "res", "res", "shops", "hospital"),
        arrayOf("res", "res", "shops", "home", "res", "shops", "down"),
        arrayOf("mansion", "lots", "res", "praca", "shops", "down", "hotel"),
        arrayOf("mansion", "res", "apt", "down", "mall", "hotel", "down"),
        arrayOf("mansion", "mansion", "park", "shops", "apt", "hotel", "fun"))

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

    fun inLot(x: Float, z: Float) = x > lotX0 && x < lotX1 && z > lotZ0 && z < lotZ1
    fun onRoad(x: Float, z: Float) = z <= Z1 && (inBands(x, bandX, true) || inBands(z, bandZ, true))

    /** Etapa 130: em cima do canteiro central de uma avenida (o chão sobe um pouco, como a calçada). */
    fun onMedian(x: Float, z: Float): Boolean {
        if (z > Z1) return false
        fun clear(v: Float, bands: FloatArray): Boolean { var j = 0; while (j < bands.size) { if (v > bands[j] + SIDE - 3.2f && v < bands[j + 1] - SIDE + 3.2f) return false; j += 2 }; return true }
        var k = 0
        while (k < bandX.size) { if (isAvenue(bandX[k + 1] - bandX[k]) && abs(x - (bandX[k] + bandX[k + 1]) / 2) < 1.5f && clear(z, bandZ)) return true; k += 2 }
        k = 0
        while (k < bandZ.size) { if (isAvenue(bandZ[k + 1] - bandZ[k]) && abs(z - (bandZ[k] + bandZ[k + 1]) / 2) < 1.5f && clear(x, bandX)) return true; k += 2 }
        return false
    }

    fun groundH(x: Float, z: Float): Float {
        if (!on || inLot(x, z)) return 0f
        for (br in bridges) if (x > br[0] && x < br[2] && z > br[1] && z < br[3]) return br[4] - 0.03f + br[5] * kotlin.math.sin(Math.PI.toFloat() * (z - br[1]) / (br[3] - br[1]))
        bldAt(x, z)?.let { return FLOOR }
        if (TOWN) return Town.groundH(x, z)
        if (z > Z1) {
            if (z < BEACH_Z) return CURB
            val pz0 = BEACH_Z + 4f
            if (abs(x - PIER_X) < 2.5f && z > pz0) return if (z < pz0 + 6f) CityFun.sandH(pz0) + (1.2f - CityFun.sandH(pz0)) * (z - pz0) / 6f else 1.2f
            if (abs(x - PIER_X) < 6f && z > SEA_Z + 62f) return 1.2f
            return CityFun.sandH(z)
        }
        if (onMedian(x, z)) return CURB + 0.04f
        return if (onRoad(x, z)) 0f else CURB
    }

    /** Etapa 123: carro do jogador estacionado (x, z, rumo, meio comprimento, meia largura) — bloqueia quem anda e o trânsito para. */
    @Volatile var ownCar: FloatArray? = null

    fun blocked(x: Float, z: Float): Boolean {
        ownCar?.let { o ->
            val dx = x - o[0]; val dz = z - o[1]
            val fx = sin(o[2]); val fz = -cos(o[2])
            if (abs(dx * fx + dz * fz) < o[3] + 0.2f && abs(dx * fz - dz * fx) < o[4] + 0.2f) return true
        }
        if (x < X0 + 0.5f || x > X1 - 0.5f || z < Z0 + 0.5f) return true
        if (z > SEA_Z + 2f) {   // mar: dá para molhar os pés; mais fundo, só pelo píer
            val onPier = (abs(x - PIER_X) < 2.3f && z < SEA_Z + 62f) || (abs(x - PIER_X) < 5.8f && z >= SEA_Z + 62f && z < SEA_Z + 67.8f)
            if (!onPier) return true
        }
        if (TOWN && TownHouses.blocked(x, z)) return true
        val l = solidsBy[cell(x, z)]
        if (l != null) for (r in l) if (x > r[0] && x < r[2] && z > r[1] && z < r[3]) return true
        for (c in cars) {
            val dx = x - c.x; val dz = z - c.z
            if (dx * dx + dz * dz > 16f) continue
            val yr = Math.toRadians(c.yaw.toDouble()).toFloat()
            val fx = sin(yr); val fz = cos(yr)
            val along = dx * fx + dz * fz; val side = dx * fz - dz * fx
            if (abs(along) < c.halfL + 0.25f && abs(side) < c.halfW + 0.25f) return true
        }
        return false
    }

    // ------------------------------------------------------------ trânsito

    class Car(val lane: Int, var s: Float, var v: Float, val vmax: Float, val mesh: Int, val halfL: Float, val halfW: Float) {
        var x = 0f; var z = 0f; var axis = 0; var dir = 1; var yaw = 0f
        var wheel = 0f
        var brake = false
        // Etapa 131: trajeto livre (cidade nova)
        var path = FloatArray(0); var cum = FloatArray(0)
        var edge = -1; var fwd = true; var laneO = 0f; var onTurn = false; var node = -1; var nextEdge = -1; var nextFwd = true
        var holding = -1; var wait = 0f
    }
    class Lane(val axis: Int, val dir: Int, val c: Float, val lo: Float, val hi: Float)
    val lanes = ArrayList<Lane>()
    val cars = ArrayList<Car>()
    private var crossX = FloatArray(0)
    private var crossZ = FloatArray(0)
    private var crossHX = FloatArray(0)
    private var crossHZ = FloatArray(0)
    /** Etapa 130: distância do eixo da rua até o centro de cada faixa (de um lado): avenida = 2 faixas por sentido, junto do canteiro. */
    fun laneOffsets(w: Float): FloatArray = if (isAvenue(w)) floatArrayOf(3.25f, 6.75f) else if (w >= 15f) floatArrayOf(2.25f) else floatArrayOf(1.9f)
    private var tLight = 0f
    val lightPhase: Int get() { val t = tLight % 24f; return if (t < 10f) 0 else if (t < 12f) 1 else if (t < 22f) 2 else 3 }
    var time = 0f; private set

    private fun spawnTraffic() {
        lanes.clear(); cars.clear()
        for (k in 0 until 8) {
            val zc = (bandZ[k * 2] + bandZ[k * 2 + 1]) / 2
            for (o in laneOffsets(bandZ[k * 2 + 1] - bandZ[k * 2])) { lanes.add(Lane(0, 1, zc + o, X0, X1)); lanes.add(Lane(0, -1, zc - o, X0, X1)) }
            val xc = (bandX[k * 2] + bandX[k * 2 + 1]) / 2
            for (o in laneOffsets(bandX[k * 2 + 1] - bandX[k * 2])) { lanes.add(Lane(1, 1, xc - o, Z0, Z1)); lanes.add(Lane(1, -1, xc + o, Z0, Z1)) }
        }
        crossX = FloatArray(6) { (bandX[(it + 1) * 2] + bandX[(it + 1) * 2 + 1]) / 2 }
        crossZ = FloatArray(6) { (bandZ[(it + 1) * 2] + bandZ[(it + 1) * 2 + 1]) / 2 }
        crossHX = FloatArray(6) { (bandX[(it + 1) * 2 + 1] - bandX[(it + 1) * 2]) / 2 }
        crossHZ = FloatArray(6) { (bandZ[(it + 1) * 2 + 1] - bandZ[(it + 1) * 2]) / 2 }
        val rng = Rng(4242)
        for ((i, ln) in lanes.withIndex()) {
            val n = 2 + rng.i(2)
            for (k in 0 until n) {
                val s = ln.lo + (ln.hi - ln.lo) * (k + rng.r(0.1f, 0.6f)) / n
                val m = Vehicles.pick(rng)
                val vm = rng.r(8f, 12.5f) * Vehicles.speedK(m)
                cars.add(Car(i, s, vm * 0.5f, vm, m, Vehicles.halfL(m), Vehicles.halfW(m)))
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

    // ------------------------------------------------------------ trânsito da cidade nova

    private val nodeOcc = HashMap<Int, IntArray>()   // nó -> (chave da entrada, quantos dentro)

    private fun setPath(c: Car, p: FloatArray) {
        c.path = p; val n = p.size / 2; val cu = FloatArray(n); for (i in 1 until n) cu[i] = cu[i - 1] + kotlin.math.hypot(p[i * 2] - p[i * 2 - 2], p[i * 2 + 1] - p[i * 2 - 1]); c.cum = cu; c.s = 0f
    }

    private fun laneOff(ei: Int, k: Int): Float { val o = laneOffsets(Town.edges[ei].w); return o[k.coerceIn(0, o.size - 1)] }

    private fun chooseNext(c: Car, rng: Rng) {
        val to = if (c.fwd) Town.edges[c.edge].b else Town.edges[c.edge].a
        val nd = Town.nodes[to]
        val opts = nd.edges.filter { it != c.edge }
        val ne = if (opts.isEmpty()) c.edge else opts[rng.i(opts.size)]
        c.node = to; c.nextEdge = ne; c.nextFwd = Town.edges[ne].a == to
    }

    private val trng = Rng(999)

    private fun spawnTownTraffic() {
        cars.clear(); lanes.clear(); nodeOcc.clear()
        val rng = Rng(4242)
        for ((ei, ed) in Town.edges.withIndex()) {
            if (ed.len < 30f) continue
            val per = if (ed.avenue) 70f else 110f
            val n = max(1, (ed.len / per).toInt())
            for (k in 0 until n) {
                val fwd = (k % 2 == 0); val lk = if (ed.avenue) rng.i(2) else 0
                val m = Vehicles.pick(rng)
                val vm = rng.r(8f, 12.5f) * Vehicles.speedK(m) * (if (ed.avenue) 1.15f else 0.9f)
                val c = Car(0, 0f, vm * 0.5f, vm, m, Vehicles.halfL(m), Vehicles.halfW(m))
                c.edge = ei; c.fwd = fwd; c.laneO = laneOff(ei, lk)
                setPath(c, Town.lanePath(ei, fwd, c.laneO))
                c.s = c.cum.last() * (k + rng.r(0.15f, 0.7f)) / n
                chooseNext(c, rng)
                placeT(c)
                cars.add(c)
            }
        }
    }

    private fun placeT(c: Car) {
        val p = c.path; val cu = c.cum; val n = p.size / 2
        if (n < 2) return
        var i = 0; while (i < n - 2 && cu[i + 1] < c.s) i++
        val f = ((c.s - cu[i]) / max(1e-4f, cu[i + 1] - cu[i])).coerceIn(0f, 1f)
        c.x = p[i * 2] + (p[i * 2 + 2] - p[i * 2]) * f; c.z = p[i * 2 + 1] + (p[i * 2 + 3] - p[i * 2 + 1]) * f
        // rumo olhando um pouco à frente (suaviza as curvas)
        val ahead = c.s + 2.5f
        var j = i; while (j < n - 2 && cu[j + 1] < ahead) j++
        val f2 = ((ahead - cu[j]) / max(1e-4f, cu[j + 1] - cu[j])).coerceIn(0f, 1f)
        val ax = p[j * 2] + (p[j * 2 + 2] - p[j * 2]) * f2; val az = p[j * 2 + 1] + (p[j * 2 + 3] - p[j * 2 + 1]) * f2
        val dx = ax - c.x; val dz = az - c.z
        if (dx * dx + dz * dz > 1e-4f) {
            val y = Math.toDegrees(kotlin.math.atan2(dx.toDouble(), dz.toDouble())).toFloat()
            var dl = y - c.yaw; while (dl > 180f) dl -= 360f; while (dl < -180f) dl += 360f
            c.yaw += dl * 0.5f
        }
    }

    private fun updateTown(dt: Float, px: Float, pz: Float) {
        for (c in cars) {
            val len = c.cum.last()
            var target = c.vmax * (if (c.onTurn) 0.55f else 1f)
            val yr = Math.toRadians(c.yaw.toDouble()).toFloat()
            val fx = sin(yr); val fz = cos(yr)
            fun obstacle(ox: Float, oz: Float, half: Float, lat: Float) {
                val dx = ox - c.x; val dz = oz - c.z
                val along = dx * fx + dz * fz; val side = abs(dx * fz - dz * fx)
                if (along > 0f && along < 20f && side < lat) target = min(target, max(0f, along - c.halfL - half - 1.6f) * 1.1f)
            }
            for (o in cars) {
                if (o === c) continue
                val dx = o.x - c.x; val dz = o.z - c.z
                if (dx * dx + dz * dz > 400f) continue
                obstacle(o.x, o.z, o.halfL, 1.7f)
            }
            obstacle(px, pz, if (driverHalf > 0f) driverHalf else 0.2f, 2.0f)
            ownCar?.let { o -> obstacle(o[0], o[1], o[3], 2.2f) }
            // cruzamento: só entra quem vem da mesma rua enquanto houver carro de outra direção dentro
            if (!c.onTurn && c.node >= 0) {
                val nd = Town.nodes[c.node]
                if (nd.round <= 0f && nd.edges.size >= 3) {
                    val key = c.edge * 2 + (if (c.fwd) 1 else 0)
                    val occ = nodeOcc[c.node]
                    val free = occ == null || occ[1] == 0 || occ[0] == key
                    if (!free && c.holding != c.node) {
                        val d = len - c.s
                        if (d < 12f) target = min(target, max(0f, d - c.halfL - 0.6f) * 1.4f)
                        c.wait += dt
                    }
                }
            }
            val acc = if (target > c.v) 2.6f else 7f
            c.brake = target < c.v - 0.3f
            c.v += (target - c.v).coerceIn(-acc * dt, acc * dt)
            if (c.v < 0f) c.v = 0f
            c.s += c.v * dt
            c.wheel += c.v * dt / 0.34f
            // reserva o cruzamento perto da entrada
            if (!c.onTurn && c.node >= 0 && c.holding != c.node && len - c.s < 4f) {
                val nd = Town.nodes[c.node]
                if (nd.round <= 0f && nd.edges.size >= 3) {
                    val key = c.edge * 2 + (if (c.fwd) 1 else 0)
                    val occ = nodeOcc.getOrPut(c.node) { intArrayOf(key, 0) }
                    if (occ[1] == 0 || occ[0] == key) { occ[0] = key; occ[1]++; c.holding = c.node }
                    else c.s = min(c.s, len - 4f)
                }
            }
            if (c.s >= len) {
                val over = c.s - len
                if (!c.onTurn) {
                    // fim da faixa: entra na conversão
                    val lk = if (Town.edges[c.nextEdge].avenue) (if (laneOffsets(Town.edges[c.edge].w).size > 1 && c.laneO > 5f) 1 else 0) else 0
                    val nl = laneOff(c.nextEdge, lk)
                    val a = c.path; val b = Town.lanePath(c.nextEdge, c.nextFwd, nl)
                    setPath(c, Town.turnPath(c.node, a, b)); c.onTurn = true; c.s = over
                    c.edge = c.nextEdge; c.fwd = c.nextFwd; c.laneO = nl
                } else {
                    // saiu do cruzamento
                    if (c.holding >= 0) { nodeOcc[c.holding]?.let { it[1] = max(0, it[1] - 1) }; c.holding = -1 }
                    setPath(c, Town.lanePath(c.edge, c.fwd, c.laneO)); c.onTurn = false; c.s = over
                    chooseNext(c, trng); c.wait = 0f
                }
            }
            placeT(c)
        }
        for (p in peds) {
            val dx = px - p.x; val dz = pz - p.z
            val near = dx * dx + dz * dz < 1.4f
            val tv = if (near) 0f else p.vmax
            p.v += (tv - p.v) * min(1f, dt * 4f)
            p.t += p.v * dt * p.dir
            val per = p.per
            if (p.t > per) p.t -= per else if (p.t < 0f) p.t += per
            pedPlace(p, dt)
            p.ph += p.v * dt * 5.2f
        }
        Gps.update(px, pz)
    }

    /** Meio comprimento do veículo que o jogador dirige (0 = a pé). */
    @Volatile var driverHalf = 0f

    fun update(dt0: Float, px: Float, pz: Float) {
        if (!on) return
        val dt = dt0.coerceIn(0f, 0.1f)
        tLight += dt; time += dt
        if (TOWN) { updateTown(dt, px, pz); return }
        val ph = lightPhase
        for (c in cars) {
            val ln = lanes[c.lane]
            var target = c.vmax
            val green = if (ln.axis == 0) ph == 0 else ph == 2
            val yellow = if (ln.axis == 0) ph == 1 else ph == 3
            if (!green) {
                val cross = if (ln.axis == 0) crossX else crossZ
                val crossH = if (ln.axis == 0) crossHX else crossHZ
                for ((ci, cc) in cross.withIndex()) {
                    val half = crossH[ci] + 3.3f + c.halfL + 0.4f
                    val dist = (cc - ln.dir * half - c.s) * ln.dir
                    if (dist > -0.5f && dist < 32f) {
                        if (yellow && dist < 7f) break
                        target = min(target, sqrt(max(0f, dist - 0.2f) * 2f * 5f))
                        break
                    }
                }
            }
            var gap = Float.MAX_VALUE; var other: Car? = null
            for (o in cars) {
                if (o === c || o.lane != c.lane) continue
                var d = (o.s - c.s) * ln.dir
                if (d < 0f) d += (ln.hi - ln.lo)
                if (d < gap) { gap = d; other = o }
            }
            if (other != null && gap < 45f) target = min(target, max(0f, gap - c.halfL - other.halfL - 2.2f) * 1.2f)
            fun obstacle(ox: Float, oz: Float, half: Float) {
                val ax = if (ln.axis == 0) ox else oz; val pc = if (ln.axis == 0) oz else ox
                if (abs(pc - ln.c) < 2.3f) {
                    val d = (ax - c.s) * ln.dir
                    if (d > 0f && d < 18f) target = min(target, max(0f, d - c.halfL - half - 1.4f) * 1.0f)
                }
            }
            obstacle(px, pz, if (driverHalf > 0f) driverHalf else 0.2f)
            ownCar?.let { o -> obstacle(o[0], o[1], o[3]) }
            val acc = if (target > c.v) 2.6f else 7f
            c.brake = target < c.v - 0.3f
            c.v += (target - c.v).coerceIn(-acc * dt, acc * dt)
            if (c.v < 0f) c.v = 0f
            c.s += c.v * dt * ln.dir
            c.wheel += c.v * dt / 0.34f
            if (c.s > ln.hi) c.s -= (ln.hi - ln.lo) else if (c.s < ln.lo) c.s += (ln.hi - ln.lo)
            place(c)
        }
        for (p in peds) {
            val dx = px - p.x; val dz = pz - p.z
            val near = dx * dx + dz * dz < 1.4f
            val tv = if (near) 0f else p.vmax
            p.v += (tv - p.v) * min(1f, dt * 4f)
            p.t += p.v * dt * p.dir
            val per = p.per
            if (p.t > per) p.t -= per else if (p.t < 0f) p.t += per
            pedPlace(p, dt)
            p.ph += p.v * dt * 5.2f
        }
        CityFun.update(dt)
        Gps.update(px, pz)
    }

    // ------------------------------------------------------------ pedestres

    class Ped(val x0: Float, val z0: Float, val x1: Float, val z1: Float, var t: Float, val dir: Int, val vmax: Float, val look: Int, val path: FloatArray? = null) {
        var x = 0f; var z = 0f; var yaw = 0f; var v = 0f; var ph = 0f
        val cum: FloatArray? = path?.let { p -> val n = p.size / 2; val c = FloatArray(n + 1); for (i in 0 until n) { val j = (i + 1) % n; c[i + 1] = c[i] + kotlin.math.hypot(p[j * 2] - p[i * 2], p[j * 2 + 1] - p[i * 2 + 1]) }; c }
        val per: Float = cum?.last() ?: (2 * (x1 - x0) + 2 * (z1 - z0))
    }
    val peds = ArrayList<Ped>()
    var pedBody: Array<Mesh?> = arrayOfNulls(0); private set
    var pedLeg: Array<Mesh?> = arrayOfNulls(0); private set
    var pedArm: Array<Mesh?> = arrayOfNulls(0); private set

    private fun pedPlace(p: Ped, dt: Float) {
        val pp = p.path; val cu = p.cum
        if (pp != null && cu != null) {
            val n = pp.size / 2
            var i = 0; while (i < n - 1 && cu[i + 1] < p.t) i++
            val j = (i + 1) % n
            val f = ((p.t - cu[i]) / max(1e-4f, cu[i + 1] - cu[i])).coerceIn(0f, 1f)
            p.x = pp[i * 2] + (pp[j * 2] - pp[i * 2]) * f; p.z = pp[i * 2 + 1] + (pp[j * 2 + 1] - pp[i * 2 + 1]) * f
            var yaw = Math.toDegrees(kotlin.math.atan2((pp[j * 2] - pp[i * 2]).toDouble(), (pp[j * 2 + 1] - pp[i * 2 + 1]).toDouble())).toFloat()
            if (p.dir < 0) yaw += 180f
            var dl = yaw - p.yaw
            while (dl > 180f) dl -= 360f
            while (dl < -180f) dl += 360f
            p.yaw += dl * min(1f, dt * 8f)
            return
        }
        val w = p.x1 - p.x0; val d = p.z1 - p.z0
        var t = p.t
        val tx: Float; val tz: Float; var yaw: Float
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

    private fun buildPeds() {
        val skins = arrayOf("#F1C7A5", "#D9A27E", "#A86F4C", "#7A4B2F", "#F6D8C0", "#E8B894")
        val shirts = arrayOf("#D7263D", "#1B98E0", "#2A9D8F", "#F4A261", "#6A4C93", "#FFFFFF", "#333333", "#F2C14E", "#8BC34A", "#E91E63")
        val pants = arrayOf("#2B3A55", "#4A4A4A", "#6B4F3A", "#1F1F1F", "#3D5A80", "#C8B89A")
        val hairs = arrayOf("#2B1B12", "#5A3A22", "#C9A15B", "#111111", "#8C4A2F", "#9E9E9E")
        val bl = ArrayList<Mesh?>(); val ll = ArrayList<Mesh?>(); val al = ArrayList<Mesh?>()
        for (k in 0 until 14) {
            val sk = C(skins[k % 6]); val sh = C(shirts[(k * 3) % 10]); val pn = C(pants[(k * 5) % 6]); val hr = C(hairs[(k * 7) % 6])
            val woman = k % 2 == 1
            val b = MB(); b.m(Mt.FABRIC, 1f)
            b.rbox(0f, 1.2f, 0f, if (woman) 0.38f else 0.44f, 0.52f, 0.24f, 0.08f, sh, true, 2)
            b.rbox(0f, 0.92f, 0f, 0.38f, 0.16f, 0.23f, 0.05f, pn, true, 2)
            if (woman && k % 4 == 1) b.cyl(0f, 0.6f, 0f, 0.28f, 0.2f, 0.36f, pn, true, 12)
            b.m(Mt.PLAIN)
            b.cyl(0f, 1.44f, 0f, 0.055f, 0.055f, 0.1f, sk, true, 8)
            CityGeo.ball(b, 0f, 1.62f, 0f, 0.115f, sk, 0.135f, 10)
            CityGeo.ball(b, 0f, 1.68f, -0.012f, 0.122f, hr, 0.11f, 10)
            if (woman) b.rbox(0f, 1.48f, -0.09f, 0.22f, 0.34f, 0.06f, 0.03f, hr, true, 2)
            b.box(0.042f, 1.63f, 0.11f, 0.022f, 0.022f, 0.01f, C("#2A2A2A")); b.box(-0.042f, 1.63f, 0.11f, 0.022f, 0.022f, 0.01f, C("#2A2A2A"))
            b.box(0f, 1.575f, 0.115f, 0.04f, 0.008f, 0.01f, C("#B5654E"))
            if (k % 5 == 2) { b.m(Mt.FABRIC, 1f); b.rbox(0f, 1.25f, -0.17f, 0.3f, 0.36f, 0.12f, 0.04f, C("#37474F"), true, 2) }   // mochila
            bl.add(b.toMesh(true))
            val lg = MB(); lg.m(Mt.FABRIC, 1f)
            lg.rbox(0f, -0.42f, 0f, 0.14f, 0.82f, 0.15f, 0.05f, if (woman && k % 4 == 1) sk else pn, true, 2)
            lg.m(Mt.PLAIN)
            lg.rbox(0f, -0.84f, 0.04f, 0.13f, 0.08f, 0.27f, 0.03f, C(if (k % 3 == 0) "#FFFFFF" else "#2A2A2A"), true, 2)
            ll.add(lg.toMesh(true))
            val ar = MB(); ar.m(Mt.FABRIC, 1f)
            ar.rbox(0f, -0.14f, 0f, 0.1f, 0.3f, 0.11f, 0.04f, sh, true, 2)
            ar.m(Mt.PLAIN)
            ar.rbox(0f, -0.42f, 0f, 0.08f, 0.3f, 0.085f, 0.035f, sk, true, 2)
            al.add(ar.toMesh(true))
        }
        pedBody = bl.toTypedArray(); pedLeg = ll.toTypedArray(); pedArm = al.toTypedArray()
        peds.clear()
        val rng = Rng(77)
        if (TOWN) {
            for (bl in Town.blocks) {
                val path = Town.polyOffset(bl, 1.5f)
                val n = max(1, (kotlin.math.abs(Town.polyArea(bl)) / 2500f).toInt().coerceAtMost(4))
                for (k in 0 until n) {
                    val p = Ped(0f, 0f, 0f, 0f, 0f, if (rng.f() < 0.5f) 1 else -1, rng.r(1.0f, 1.45f), rng.i(14), path)
                    p.t = rng.r(0f, p.per); p.v = p.vmax
                    pedPlace(p, 1f)
                    peds.add(p)
                }
            }
            return
        }
        for (i in 0 until NB) for (j in 0 until NB) {
            val x0 = blkX[i * 2] - SIDE * 0.5f; val x1 = blkX[i * 2 + 1] + SIDE * 0.5f
            val z0 = blkZ[j * 2] - SIDE * 0.5f; val z1 = blkZ[j * 2 + 1] + SIDE * 0.5f
            val t = types[i][j]
            val n = when (t) { "down", "shops", "mall", "praca", "hotel", "fun" -> 3; "res", "lots", "mansion" -> 1; else -> 2 }
            for (k in 0 until n) {
                val p = Ped(x0, z0, x1, z1, 0f, if (rng.f() < 0.5f) 1 else -1, rng.r(1.0f, 1.45f), rng.i(14))
                p.t = rng.r(0f, p.per); p.v = p.vmax
                pedPlace(p, 1f)
                peds.add(p)
            }
        }
    }
}
