package com.vinicius.meular

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RadialGradient
import android.graphics.RectF
import android.graphics.Shader
import android.graphics.Typeface
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import com.vinicius.meular.CityGeo.P
import com.vinicius.meular.CityGeo.q

/**
 * Etapa 127: letreiros de verdade. Cada estabelecimento tem marca própria (nome, subtítulo, fonte, cores, ícone)
 * e um tipo de letreiro como na rua de verdade:
 *  - BOX: caixa luminosa (acrílico iluminado por dentro, laterais de alumínio, suportes);
 *  - LETTERS: letra-caixa (letras soltas em relevo presas na fachada, sem placa);
 *  - NEON: tubos de neon brilhando sobre um fundo escuro;
 *  - BOARD: placa de madeira entalhada com moldura;
 *  - AWNING: nome pintado na aba do toldo.
 * Muitas lojas também ganham bandeira lateral (placa quadrada perpendicular com o ícone), toldos de tipos diferentes,
 * plaquinha "ABERTO" na porta, adesivo na vitrine, cavalete na calçada, floreiras.
 *
 * Atlas 2048 × 2048: linhas 0–15 = 64 letreiros-base (índice de City.SIGNS); y 1024–1535 = 16 bandeiras 256 × 256;
 * y 1536–2047 = 32 variantes (outras marcas da mesma categoria).
 */
object Signs {
    const val BOX = 0; const val LETTERS = 1; const val NEON = 2; const val BOARD = 3; const val AWNING = 4; const val PLATE = 5

    // fontes: 0 sans negrito, 1 serifa negrito, 2 serifa itálico, 3 condensada, 4 sans fina, 5 "letra cursiva"
    class Spec(val text: String, val sub: String, val style: Int, val bg: String, val bg2: String, val fg: String, val font: Int,
               val icon: String = "", val blade: Int = -1, val awn: Int = 0, val acc: String = "")

    // ---------------------------------------------------------------- marcas
    private fun S(t: String, sub: String, st: Int, bg: String, bg2: String, fg: String, f: Int, ic: String = "", bl: Int = -1, awn: Int = 0, acc: String = "") = Spec(t, sub, st, bg, bg2, fg, f, ic, bl, awn, acc)

    /** bandeiras (16): ícone + nome curto */
    val BLADES = arrayOf(
        Triple("cross", "FARMÁCIA", "#1E9E5A"), Triple("cup", "CAFÉ", "#4A2C1A"), Triple("pole", "BARBEARIA", "#263238"), Triple("pizza", "PIZZA", "#B71C1C"),
        Triple("bread", "PADARIA", "#8D5524"), Triple("H", "HOTEL", "#1F2A44"), Triple("paw", "PET", "#1E88C8"), Triple("cone", "SORVETE", "#E91E63"),
        Triple("book", "LIVROS", "#1B4332"), Triple("glasses", "ÓTICA", "#212121"), Triple("bowl", "AÇAÍ", "#4A148C"), Triple("burger", "BURGER", "#E65100"),
        Triple("coin", "BANCO", "#14306B"), Triple("cross", "CLÍNICA", "#00897B"), Triple("flower", "FLORES", "#558B2F"), Triple("scissors", "SALÃO", "#AD1457"))

    /** marca-base de cada nome de City.SIGNS (variante 0) */
    private fun base(name: String): Spec = when (name) {
        "HOSPITAL" -> S("HOSPITAL SANTA CLARA", "", LETTERS, "#FFFFFF", "#FFFFFF", "#C62828", 0, "cross")
        "FARMÁCIA" -> S("Drogaria Bem Estar", "FARMÁCIA", BOX, "#1FA463", "#13854C", "#FFFFFF", 0, "cross", 0)
        "PADARIA" -> S("Pão Dourado", "PADARIA & CONFEITARIA", BOARD, "#6B3F1D", "#4E2C12", "#F6E3BF", 2, "bread", 4, 1)
        "SUPERMERCADO" -> S("SuperBom", "SUPERMERCADO", LETTERS, "#000000", "#000000", "#D62828", 0, "cart")
        "LANCHONETE" -> S("Lanchonete do Zé", "SALGADOS · SUCOS · LANCHES", BOX, "#FFD23F", "#F6B800", "#B3261E", 0, "burger", -1, 2)
        "PIZZARIA" -> S("Bella Napoli", "PIZZARIA · FORNO A LENHA", BOARD, "#1F5E3A", "#13432A", "#FFFFFF", 2, "pizza", 3, 3)
        "BANCO" -> S("Banco Horizonte", "", LETTERS, "#000000", "#000000", "#E8C26E", 1, "coin", 12)
        "ACADEMIA" -> S("IRON FIT", "ACADEMIA 24H", NEON, "#111111", "#111111", "#FF8A00", 3, "dumbbell")
        "SALÃO DE BELEZA" -> S("Studio Bella", "SALÃO DE BELEZA", LETTERS, "#000000", "#000000", "#B76E79", 5, "scissors", 15, 4)
        "POSTO" -> S("POSTO ROTA SUL", "", BOX, "#0F7A3D", "#0A5E2E", "#FFE14D", 3, "drop")
        "CONVENIÊNCIA" -> S("Pare & Leve", "CONVENIÊNCIA 24H", BOX, "#FFFFFF", "#EDEDED", "#0F7A3D", 0, "cart")
        "ESCOLA" -> S("ESCOLA ESTADUAL PRIMAVERA", "", LETTERS, "#000000", "#000000", "#1F4E9C", 0, "book")
        "POLÍCIA" -> S("DELEGACIA DE POLÍCIA", "", BOX, "#0E2A5C", "#0A1F45", "#FFFFFF", 0, "star")
        "CAFÉ" -> S("Café Grão Nobre", "CAFETERIA · DOCES", BOARD, "#3B2416", "#2A190F", "#F3DFC1", 2, "cup", 1, 1)
        "LIVRARIA" -> S("Livraria Saber", "LIVROS · PAPELARIA · CAFÉ", BOARD, "#1B4332", "#123024", "#E9C46A", 1, "book", 8)
        "PET SHOP" -> S("Patinhas", "PET SHOP · BANHO & TOSA", BOX, "#29A9E1", "#1A86BA", "#FFFFFF", 0, "paw", 6, 2)
        "ÓTICA" -> S("Ótica Visão", "", LETTERS, "#000000", "#000000", "#1A1A1A", 4, "glasses", 9)
        "SORVETERIA" -> S("Gelato Mio", "SORVETERIA ARTESANAL", BOX, "#FFD3E2", "#FFB8CF", "#C2185B", 5, "cone", 7, 2)
        "MODA" -> S("Maison Lis", "", LETTERS, "#000000", "#000000", "#C9A227", 1, "hanger")
        "RESTAURANTE" -> S("Sabor da Terra", "RESTAURANTE", BOARD, "#8E1B1B", "#6A1212", "#FBE3B0", 2, "fork", -1, 1)
        "BOMBEIROS" -> S("CORPO DE BOMBEIROS", "", LETTERS, "#000000", "#000000", "#FFFFFF", 0, "flame")
        "HOTEL" -> S("Hotel Atlântico", "", LETTERS, "#000000", "#000000", "#E8C26E", 1, "star", 5)
        "ELETRÔNICOS" -> S("TecnoMax", "CELULARES · INFORMÁTICA", BOX, "#1565C0", "#0D47A1", "#FFFFFF", 3, "phone")
        "FLORICULTURA" -> S("Flor de Lis", "FLORICULTURA", AWNING, "#5E8C3A", "#4A7230", "#FFFFFF", 5, "flower", 14, 5)
        "PRONTO-SOCORRO" -> S("PRONTO-SOCORRO", "24 HORAS", BOX, "#D62828", "#A61C1C", "#FFFFFF", 0, "cross")
        "ESTACIONAMENTO" -> S("ESTACIONAMENTO", "", PLATE, "#1F4FA8", "#173E86", "#FFFFFF", 0, "P")
        "PRAÇA CENTRAL" -> S("Praça Central", "", PLATE, "#3E2E22", "#2C2018", "#F1DDB0", 1)
        "ACADEMIA AO AR LIVRE" -> S("ACADEMIA AO AR LIVRE", "", PLATE, "#2E7D32", "#1B5E20", "#FFFFFF", 0, "dumbbell")
        "À VENDA" -> S("VENDE-SE", "TRATAR NO LOCAL", PLATE, "#C62828", "#A31F1F", "#FFFFFF", 0)
        "TERRENO À VENDA" -> S("TERRENO À VENDA", "", PLATE, "#F2C230", "#E0AE14", "#1A1A1A", 0)
        "PARQUE DE DIVERSÕES" -> S("PARQUE DE DIVERSÕES", "", NEON, "#2A0E3D", "#2A0E3D", "#FFD54F", 3, "star")
        "QUIOSQUE" -> S("Quiosque do Mar", "ÁGUA DE COCO · PETISCOS", BOARD, "#00838F", "#006B75", "#FFFFFF", 5)
        "SALVA-VIDAS" -> S("GUARDA-VIDAS", "", PLATE, "#D32F2F", "#B71C1C", "#FFEB3B", 0)
        "IGREJA MATRIZ" -> S("Igreja Matriz", "", PLATE, "#4E342E", "#3E2723", "#FFF3E0", 1, "crossT")
        "HAMBÚRGUER" -> S("Smash Burger", "HAMBURGUERIA", NEON, "#1A1A1A", "#1A1A1A", "#FF5722", 3, "burger", 11)
        "SUSHI" -> S("Sushi Kenzo", "", BOX, "#111111", "#000000", "#FFFFFF", 4, "sun")
        "BARBEARIA" -> S("Barbearia Navalha", "DESDE 1998", BOARD, "#1C1C1C", "#101010", "#E7C98B", 1, "scissors", 2)
        "PAPELARIA" -> S("Papelaria Arco-Íris", "MATERIAL ESCOLAR · XEROX", BOX, "#FFFFFF", "#F2F2F2", "#1565C0", 0, "pencil", -1, 2)
        "AÇAÍ" -> S("Açaí da Praia", "AÇAÍ · CUPUAÇU · SUCOS", BOX, "#5B1A8A", "#41106A", "#F3E5F5", 5, "bowl", 10)
        "MERCADINHO" -> S("Mercadinho São José", "FRUTAS · FRIOS · BEBIDAS", BOX, "#2E7D32", "#1E5E23", "#FFEB3B", 0, "cart", -1, 3)
        "CASA DE CÂMBIO" -> S("Câmbio Global", "DÓLAR · EURO · TURISMO", BOX, "#004D40", "#00332A", "#FFD54F", 1, "coin")
        "CONDOMÍNIO" -> S("Residencial Jardins", "", LETTERS, "#000000", "#000000", "#B0B5BA", 1)
        "RESIDENCIAL" -> S("Edifício Bela Vista", "", LETTERS, "#000000", "#000000", "#B0B5BA", 1)
        "SHOPPING" -> S("Shopping Horizonte", "", LETTERS, "#000000", "#000000", "#FFFFFF", 1, "bag")
        "CINEMA" -> S("CINE STAR", "", NEON, "#1A0A0A", "#1A0A0A", "#FFD600", 3, "star")
        "MONTANHA-RUSSA" -> S("MONTANHA-RUSSA", "", BOX, "#E65100", "#BF4000", "#FFFFFF", 3, "star")
        "RODA-GIGANTE" -> S("RODA-GIGANTE", "", BOX, "#1565C0", "#0D47A1", "#FFFFFF", 3, "star")
        "CARROSSEL" -> S("CARROSSEL", "", BOX, "#AD1457", "#880E4F", "#FFF59D", 5, "star")
        "BATE-BATE" -> S("BATE-BATE", "", BOX, "#2E7D32", "#1B5E20", "#FFFFFF", 3, "star")
        "PIPOCA" -> S("PIPOCA", "", BOX, "#FBC02D", "#F9A825", "#C62828", 3)
        "ALGODÃO DOCE" -> S("ALGODÃO DOCE", "", BOX, "#F8BBD0", "#F48FB1", "#AD1457", 5)
        "BEIRA-MAR" -> S("BEIRA-MAR", "", PLATE, "#0277BD", "#01579B", "#FFFFFF", 0)
        "PÍER" -> S("PÍER", "", PLATE, "#5D4037", "#4E342E", "#FFFFFF", 1)
        "ESCRITÓRIOS" -> S("Atlântico Office", "", LETTERS, "#000000", "#000000", "#C8CDD2", 4)
        "POUSADA" -> S("Pousada Mar Azul", "", BOARD, "#0D5C8C", "#0A4A70", "#FFFFFF", 5)
        "CLÍNICA" -> S("Clínica Vida+", "MEDICINA & SAÚDE", LETTERS, "#000000", "#000000", "#00897B", 0, "cross", 13)
        else -> if (name.startsWith("AV.") || name.startsWith("R.")) S(name, "", PLATE, "#1B7F3B", "#16692F", "#FFFFFF", 3) else S(name, "", BOX, "#37474F", "#263238", "#FFFFFF", 0)
    }

    /** outras marcas para as categorias que se repetem (variantes 100+) */
    private val VARIANTS: List<Pair<String, Spec>> = listOf(
        "ÓTICA" to S("Ótica Foco", "ÓCULOS DE GRAU E SOL", BOX, "#FFFFFF", "#F0F0F0", "#0D47A1", 0, "glasses", 9, 2),
        "ÓTICA" to S("Olhar", "ÓTICA", NEON, "#141414", "#141414", "#4FC3F7", 4, "glasses"),
        "ÓTICA" to S("Ótica Cristal", "", BOARD, "#2B2B2B", "#1A1A1A", "#E0E0E0", 1, "glasses", 9),
        "LIVRARIA" to S("Sebo Cultural", "LIVROS USADOS", BOARD, "#5D4037", "#3E2723", "#FFE0B2", 1, "book", 8, 1),
        "LIVRARIA" to S("Livraria Página Um", "", LETTERS, "#000000", "#000000", "#1B4332", 1, "book", 8),
        "MODA" to S("URBAN STORE", "", BOX, "#111111", "#000000", "#FFFFFF", 3, "hanger"),
        "MODA" to S("Bella Moda", "MODA FEMININA", LETTERS, "#000000", "#000000", "#AD1457", 5, "hanger"),
        "MODA" to S("Jeans & Cia", "", BOX, "#1F3A5F", "#152A45", "#FFFFFF", 3, "hanger", -1, 3),
        "PET SHOP" to S("Mundo Pet", "RAÇÕES · ACESSÓRIOS", BOX, "#FF8F00", "#E07B00", "#FFFFFF", 0, "paw", 6),
        "AÇAÍ" to S("Açaí Tropical", "", NEON, "#1A0A24", "#1A0A24", "#E040FB", 5, "bowl"),
        "PAPELARIA" to S("Ponto do Papel", "PAPELARIA", BOARD, "#0D47A1", "#08306B", "#FFEB3B", 0, "pencil"),
        "ELETRÔNICOS" to S("Eletro Center", "ASSISTÊNCIA TÉCNICA", BOX, "#E53935", "#C62828", "#FFFFFF", 3, "phone"),
        "ELETRÔNICOS" to S("iCell", "", NEON, "#0A0F1A", "#0A0F1A", "#00E5FF", 4, "phone"),
        "PADARIA" to S("Panificadora Trigo Bom", "PÃES · BOLOS · FRIOS", BOX, "#F4E1C1", "#E8CFA5", "#7A4A1E", 1, "bread", 4, 1),
        "PIZZARIA" to S("Pizza Prime", "DELIVERY", NEON, "#160A06", "#160A06", "#FF7043", 3, "pizza", 3),
        "SUSHI" to S("Temaki House", "COMIDA JAPONESA", BOARD, "#2B2B2B", "#1A1A1A", "#FF5252", 1, "sun", -1, 6),
        "SUSHI" to S("Sakura", "", LETTERS, "#000000", "#000000", "#D81B60", 1, "sun"),
        "LANCHONETE" to S("Cantinho do Lanche", "", BOX, "#C62828", "#A31F1F", "#FFFFFF", 5, "burger", -1, 3),
        "SALÃO DE BELEZA" to S("Espaço Glamour", "BELEZA & ESTÉTICA", NEON, "#1A0D14", "#1A0D14", "#FF80AB", 5, "scissors", 15),
        "MERCADINHO" to S("Mini Box Família", "", BOX, "#FFFFFF", "#EEEEEE", "#C62828", 3, "cart", -1, 2),
        "BARBEARIA" to S("Old School", "BARBER SHOP", NEON, "#0F0F0F", "#0F0F0F", "#FF5252", 3, "scissors", 2),
        "ACADEMIA" to S("Corpo em Forma", "ACADEMIA", BOX, "#111111", "#000000", "#FFD600", 3, "dumbbell"),
        "HOTEL" to S("Hotel Copacabana Inn", "", LETTERS, "#000000", "#000000", "#FFFFFF", 1, "star", 5),
        "CLÍNICA" to S("Clínica Sorriso", "ODONTOLOGIA", BOX, "#FFFFFF", "#F2F2F2", "#00897B", 0, "tooth", 13, 2),
        "CLÍNICA" to S("Centro Médico Aurora", "", LETTERS, "#000000", "#000000", "#1565C0", 1, "cross", 13),
        "CAFÉ" to S("Coffee & Co.", "", NEON, "#120B07", "#120B07", "#FFB74D", 5, "cup", 1),
        "FLORICULTURA" to S("Jardim Secreto", "FLORES E PLANTAS", BOARD, "#33691E", "#264D16", "#FFFFFF", 5, "flower", 14, 1),
        "SORVETERIA" to S("Polar", "SORVETES", LETTERS, "#000000", "#000000", "#0288D1", 3, "cone", 7))

    private val byName = HashMap<String, MutableList<Int>>().also { m -> for ((k, v) in VARIANTS.withIndex()) m.getOrPut(v.first) { ArrayList() }.add(100 + k) }

    fun spec(idx: Int): Spec = if (idx >= 100) VARIANTS[idx - 100].second else base(City.SIGNS.getOrNull(idx)?.first ?: "")

    /** Escolhe a marca de uma loja da categoria [name] (variante pelo sorteio da quadra). */
    fun pick(name: String, rng: City.Rng): Int {
        val opts = ArrayList<Int>(); opts.add(City.signIdx(name)); byName[name]?.let { opts.addAll(it) }
        return opts[rng.i(opts.size)]
    }

    // ---------------------------------------------------------------- UV no atlas
    fun uv(idx: Int): FloatArray {
        if (idx >= 200) { val k = idx - 200; val x = (k % 8) * 256f; val y = 1024f + (k / 8) * 256f; return floatArrayOf((x + 2) / 2048f, (y + 2) / 2048f, (x + 254) / 2048f, (y + 254) / 2048f) }
        val (x, y) = if (idx >= 100) { val k = idx - 100; Pair((k % 4) * 512f, 1536f + (k / 4) * 64f) } else Pair((idx % 4) * 512f, (idx / 4) * 64f)
        return floatArrayOf((x + 1.5f) / 2048f, (y + 1.5f) / 2048f, (x + 510.5f) / 2048f, (y + 62.5f) / 2048f)
    }

    // ---------------------------------------------------------------- desenho do atlas
    private fun col(s: String) = C(s)
    private fun tf(f: Int): Typeface = when (f) {
        1 -> Typeface.create(Typeface.SERIF, Typeface.BOLD)
        2 -> Typeface.create(Typeface.SERIF, Typeface.BOLD_ITALIC)
        3 -> Typeface.create("sans-serif-condensed", Typeface.BOLD)
        4 -> Typeface.create("sans-serif-light", Typeface.NORMAL)
        5 -> Typeface.create("cursive", Typeface.BOLD)
        else -> Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD)
    }

    private fun fit(p: Paint, s: String, size: Float, maxW: Float) {
        p.textSize = size; p.textScaleX = 1f
        val w = p.measureText(s)
        if (w > maxW) { val k = maxW / w; if (k > 0.72f) p.textScaleX = k else { p.textScaleX = 0.72f; p.textSize = size * k / 0.72f } }
    }

    fun atlas(): Bitmap {
        val bmp = Bitmap.createBitmap(2048, 2048, Bitmap.Config.ARGB_8888)
        val cv = Canvas(bmp)
        for (i in 0 until 64) drawSlot(cv, (i % 4) * 512f, (i / 4) * 64f, spec(i))
        for (k in VARIANTS.indices) drawSlot(cv, (k % 4) * 512f, 1536f + (k / 4) * 64f, VARIANTS[k].second)
        for (k in BLADES.indices) drawBlade(cv, (k % 8) * 256f, 1024f + (k / 8) * 256f, BLADES[k])
        return bmp
    }

    private val pnt = Paint(Paint.ANTI_ALIAS_FLAG)

    private fun drawSlot(cv: Canvas, x: Float, y: Float, s: Spec) {
        val p = pnt; p.shader = null; p.style = Paint.Style.FILL; p.textScaleX = 1f; p.letterSpacing = 0f
        cv.save(); cv.clipRect(x, y, x + 512f, y + 64f)
        val W = 512f; val H = 64f
        val fg = col(s.fg)
        val transparent = s.style == LETTERS || s.style == NEON
        // fundo
        when (s.style) {
            BOX, AWNING -> {
                p.shader = LinearGradient(0f, y, 0f, y + H, col(s.bg), col(s.bg2), Shader.TileMode.CLAMP); cv.drawRect(x, y, x + W, y + H, p); p.shader = null
                // brilho do acrílico e filete
                p.color = 0x22FFFFFF; cv.drawRect(x, y, x + W, y + H * 0.42f, p)
                if (s.style == BOX) { p.style = Paint.Style.STROKE; p.strokeWidth = 2.5f; p.color = mix(col(s.fg), col(s.bg), 0.55f); cv.drawRoundRect(RectF(x + 6f, y + 6f, x + W - 6f, y + H - 6f), 6f, 6f, p); p.style = Paint.Style.FILL }
            }
            BOARD -> {
                p.shader = LinearGradient(0f, y, 0f, y + H, col(s.bg), col(s.bg2), Shader.TileMode.CLAMP); cv.drawRect(x, y, x + W, y + H, p); p.shader = null
                // veios da madeira
                p.style = Paint.Style.STROKE; p.strokeWidth = 1.2f
                for (k in 0 until 9) { p.color = if (k % 2 == 0) 0x18000000 else 0x10FFFFFF; val yy = y + 6f + k * 6.5f; val path = Path(); path.moveTo(x, yy); var xx = x; while (xx < x + W) { path.quadTo(xx + 20f, yy + (if ((xx / 40).toInt() % 2 == 0) 2.5f else -2.5f), xx + 40f, yy); xx += 40f }; cv.drawPath(path, p) }
                // moldura entalhada
                p.strokeWidth = 4f; p.color = 0x55000000; cv.drawRect(x + 4f, y + 4f, x + W - 4f, y + H - 4f, p)
                p.strokeWidth = 1.5f; p.color = mix(fg, col(s.bg), 0.4f); cv.drawRect(x + 8f, y + 8f, x + W - 8f, y + H - 8f, p)
                p.style = Paint.Style.FILL
            }
            PLATE -> {
                p.color = col(s.bg); cv.drawRect(x, y, x + W, y + H, p)
                p.style = Paint.Style.STROKE; p.strokeWidth = 3f; p.color = fg; cv.drawRoundRect(RectF(x + 5f, y + 5f, x + W - 5f, y + H - 5f), 7f, 7f, p); p.style = Paint.Style.FILL
            }
            NEON -> { p.color = 0x00000000 }
            else -> {}
        }
        // ícone
        var tx0 = x + 14f; var tx1 = x + W - 14f
        if (s.icon.isNotEmpty() && s.style != PLATE || (s.style == PLATE && s.icon.isNotEmpty())) {
            val ic = H * 0.78f
            val icx = x + 12f + ic / 2; val icy = y + H / 2
            if (s.style == BOX || s.style == BOARD || s.style == AWNING) {
                p.color = mix(col(s.bg), 0xFFFFFFFF.toInt(), 0.18f); cv.drawCircle(icx, icy, ic / 2, p)
                p.style = Paint.Style.STROKE; p.strokeWidth = 2f; p.color = fg; cv.drawCircle(icx, icy, ic / 2 - 1.5f, p); p.style = Paint.Style.FILL
                icon(cv, s.icon, icx, icy, ic * 0.62f, fg, col(s.bg))
            } else if (s.style == NEON) {
                glowIcon(cv, s.icon, icx, icy, ic * 0.8f, col(s.acc.ifEmpty { s.fg }))
            } else {
                // letra-caixa: ícone em relevo
                icon(cv, s.icon, icx + 1.8f, icy + 1.8f, ic * 0.85f, shade(fg, -60), 0)
                icon(cv, s.icon, icx, icy, ic * 0.85f, fg, 0)
            }
            tx0 = x + 16f + ic
        }
        // texto
        p.typeface = tf(s.font)
        val hasSub = s.sub.isNotEmpty()
        val mainSize = if (hasSub) 34f else 44f
        val cx = (tx0 + tx1) / 2
        fit(p, s.text, mainSize, tx1 - tx0)
        val fm = p.fontMetrics
        val ty = if (hasSub) y + 6f - fm.ascent * 0.98f else y + H / 2 - (fm.ascent + fm.descent) / 2
        p.textAlign = Paint.Align.CENTER
        when (s.style) {
            NEON -> neonText(cv, s.text, cx, ty, p, fg)
            LETTERS -> {
                // relevo: sombra/espessura em degraus + face
                val dark = shade(fg, -70)
                for (k in 3 downTo 1) { p.color = dark; cv.drawText(s.text, cx + k * 0.8f, ty + k * 0.9f, p) }
                p.color = fg; cv.drawText(s.text, cx, ty, p)
                p.color = 0x30FFFFFF; cv.save(); cv.clipRect(x, y, x + W, ty + fm.ascent * 0.45f); cv.drawText(s.text, cx, ty, p); cv.restore()
            }
            else -> {
                p.color = 0x55000000; cv.drawText(s.text, cx + 1.6f, ty + 2f, p)
                p.color = fg; cv.drawText(s.text, cx, ty, p)
            }
        }
        if (hasSub) {
            p.typeface = tf(if (s.font == 5 || s.font == 2) 0 else s.font)
            fit(p, s.sub, 13f, tx1 - tx0); p.letterSpacing = 0.12f
            val sy = y + H - 7f
            if (s.style == NEON) { p.color = (fg and 0xFFFFFF) or 0x60000000; cv.drawText(s.sub, cx, sy, p); p.color = mix(fg, 0xFFFFFFFF.toInt(), 0.5f); cv.drawText(s.sub, cx, sy, p) }
            else if (s.style == LETTERS) { p.color = shade(fg, -70); cv.drawText(s.sub, cx + 0.8f, sy + 0.8f, p); p.color = fg; cv.drawText(s.sub, cx, sy, p) }
            else { p.color = mix(fg, col(s.bg), 0.15f); cv.drawText(s.sub, cx, sy, p) }
            p.letterSpacing = 0f
        }
        p.textAlign = Paint.Align.LEFT; p.textScaleX = 1f
        cv.restore()
    }

    private fun neonText(cv: Canvas, t: String, cx: Float, ty: Float, p: Paint, c: Int) {
        val glow = c and 0xFFFFFF
        p.style = Paint.Style.STROKE; p.strokeJoin = Paint.Join.ROUND
        p.strokeWidth = 9f; p.color = glow or 0x30000000; cv.drawText(t, cx, ty, p)
        p.strokeWidth = 5f; p.color = glow or 0x70000000; cv.drawText(t, cx, ty, p)
        p.strokeWidth = 2.6f; p.color = mix(c, 0xFFFFFFFF.toInt(), 0.25f); cv.drawText(t, cx, ty, p)
        p.strokeWidth = 1f; p.color = 0xFFFFFFFF.toInt(); cv.drawText(t, cx, ty, p)
        p.style = Paint.Style.FILL
    }

    private fun glowIcon(cv: Canvas, ic: String, x: Float, y: Float, s: Float, c: Int) {
        icon(cv, ic, x, y, s * 1.15f, (c and 0xFFFFFF) or 0x40000000, 0)
        icon(cv, ic, x, y, s, mix(c, 0xFFFFFFFF.toInt(), 0.35f), 0)
    }

    private fun drawBlade(cv: Canvas, x: Float, y: Float, b: Triple<String, String, String>) {
        val p = pnt; p.shader = null; p.style = Paint.Style.FILL
        val bg = col(b.third)
        cv.save(); cv.clipRect(x, y, x + 256f, y + 256f)
        p.shader = RadialGradient(x + 110f, y + 90f, 220f, mix(bg, 0xFFFFFFFF.toInt(), 0.22f), bg, Shader.TileMode.CLAMP)
        cv.drawRect(x, y, x + 256f, y + 256f, p); p.shader = null
        p.style = Paint.Style.STROKE; p.strokeWidth = 7f; p.color = 0xFFFFFFFF.toInt(); cv.drawRoundRect(RectF(x + 12f, y + 12f, x + 244f, y + 244f), 22f, 22f, p); p.style = Paint.Style.FILL
        icon(cv, b.first, x + 128f, y + 108f, 120f, 0xFFFFFFFF.toInt(), bg)
        p.typeface = tf(3); p.textAlign = Paint.Align.CENTER; fit(p, b.second, 38f, 210f); p.color = 0xFFFFFFFF.toInt()
        cv.drawText(b.second, x + 128f, y + 222f, p)
        p.textAlign = Paint.Align.LEFT; p.textScaleX = 1f
        cv.restore()
    }

    /** Ícones vetoriais (centro x, y; tamanho s; cor c; [bg] = cor do furo/detalhe). */
    fun icon(cv: Canvas, name: String, x: Float, y: Float, s: Float, c: Int, bg: Int) {
        val p = Paint(Paint.ANTI_ALIAS_FLAG); p.color = c
        val h = s / 2
        val path = Path()
        fun cut() { p.color = if (bg == 0) (c and 0xFFFFFF) or 0x00000000 else bg }
        when (name) {
            "cross" -> { val t = s * 0.17f; cv.drawRoundRect(RectF(x - t, y - h, x + t, y + h), t * 0.4f, t * 0.4f, p); cv.drawRoundRect(RectF(x - h, y - t, x + h, y + t), t * 0.4f, t * 0.4f, p) }
            "crossT" -> { val t = s * 0.1f; cv.drawRect(x - t, y - h, x + t, y + h, p); cv.drawRect(x - h * 0.6f, y - h * 0.45f, x + h * 0.6f, y - h * 0.45f + 2 * t, p) }
            "cup" -> {
                cv.drawRoundRect(RectF(x - h * 0.7f, y - h * 0.25f, x + h * 0.45f, y + h * 0.75f), h * 0.25f, h * 0.25f, p)
                p.style = Paint.Style.STROKE; p.strokeWidth = s * 0.08f; cv.drawCircle(x + h * 0.55f, y + h * 0.2f, h * 0.22f, p)
                p.strokeCap = Paint.Cap.ROUND
                for (k in 0 until 3) { val px = x - h * 0.4f + k * h * 0.4f; val pp = Path(); pp.moveTo(px, y - h * 0.4f); pp.quadTo(px + h * 0.18f, y - h * 0.65f, px, y - h * 0.9f); cv.drawPath(pp, p) }
            }
            "bread" -> {
                cv.drawRoundRect(RectF(x - h, y - h * 0.4f, x + h, y + h * 0.5f), h * 0.45f, h * 0.45f, p)
                cut(); p.style = Paint.Style.STROKE; p.strokeWidth = s * 0.05f; p.strokeCap = Paint.Cap.ROUND
                for (k in -1..1) cv.drawLine(x + k * h * 0.5f - h * 0.15f, y - h * 0.2f, x + k * h * 0.5f + h * 0.15f, y + h * 0.25f, p)
            }
            "pizza" -> {
                path.moveTo(x, y + h); path.lineTo(x - h * 0.85f, y - h * 0.6f); path.quadTo(x, y - h * 1.0f, x + h * 0.85f, y - h * 0.6f); path.close(); cv.drawPath(path, p)
                cut(); for (q in arrayOf(floatArrayOf(-0.25f, -0.35f), floatArrayOf(0.2f, -0.2f), floatArrayOf(-0.02f, 0.25f))) cv.drawCircle(x + q[0] * h, y + q[1] * h, h * 0.13f, p)
            }
            "paw" -> {
                cv.drawOval(RectF(x - h * 0.5f, y - h * 0.05f, x + h * 0.5f, y + h * 0.75f), p)
                for (q in arrayOf(floatArrayOf(-0.62f, -0.2f), floatArrayOf(-0.24f, -0.62f), floatArrayOf(0.24f, -0.62f), floatArrayOf(0.62f, -0.2f))) cv.drawOval(RectF(x + q[0] * h - h * 0.2f, y + q[1] * h - h * 0.26f, x + q[0] * h + h * 0.2f, y + q[1] * h + h * 0.26f), p)
            }
            "cone" -> {
                path.moveTo(x - h * 0.45f, y - h * 0.1f); path.lineTo(x, y + h); path.lineTo(x + h * 0.45f, y - h * 0.1f); path.close(); cv.drawPath(path, p)
                cv.drawCircle(x, y - h * 0.38f, h * 0.48f, p)
            }
            "book" -> {
                path.moveTo(x, y - h * 0.55f); path.quadTo(x - h * 0.5f, y - h * 0.8f, x - h, y - h * 0.6f); path.lineTo(x - h, y + h * 0.7f); path.quadTo(x - h * 0.5f, y + h * 0.5f, x, y + h * 0.75f)
                path.quadTo(x + h * 0.5f, y + h * 0.5f, x + h, y + h * 0.7f); path.lineTo(x + h, y - h * 0.6f); path.quadTo(x + h * 0.5f, y - h * 0.8f, x, y - h * 0.55f); path.close(); cv.drawPath(path, p)
                cut(); p.strokeWidth = s * 0.04f; cv.drawLine(x, y - h * 0.5f, x, y + h * 0.7f, p)
            }
            "glasses" -> {
                p.style = Paint.Style.STROKE; p.strokeWidth = s * 0.09f
                cv.drawCircle(x - h * 0.5f, y + h * 0.1f, h * 0.38f, p); cv.drawCircle(x + h * 0.5f, y + h * 0.1f, h * 0.38f, p)
                cv.drawArc(RectF(x - h * 0.15f, y - h * 0.1f, x + h * 0.15f, y + h * 0.2f), 200f, 140f, false, p)
                cv.drawLine(x - h * 0.88f, y, x - h, y - h * 0.25f, p); cv.drawLine(x + h * 0.88f, y, x + h, y - h * 0.25f, p)
            }
            "bowl" -> {
                cv.drawArc(RectF(x - h, y - h * 0.6f, x + h, y + h * 0.9f), 0f, 180f, true, p)
                for (k in -2..2) cv.drawCircle(x + k * h * 0.32f, y - h * 0.05f - (2 - abs(k)) * h * 0.08f, h * 0.2f, p)
                p.color = if (bg == 0) c else bg; cv.drawCircle(x + h * 0.15f, y - h * 0.3f, h * 0.1f, p)
            }
            "burger" -> {
                cv.drawArc(RectF(x - h, y - h * 0.9f, x + h, y + h * 0.2f), 180f, 180f, true, p)
                cv.drawRoundRect(RectF(x - h * 1.02f, y - h * 0.15f, x + h * 1.02f, y + h * 0.12f), h * 0.1f, h * 0.1f, p)
                cv.drawRoundRect(RectF(x - h * 0.95f, y + h * 0.22f, x + h * 0.95f, y + h * 0.48f), h * 0.12f, h * 0.12f, p)
                cv.drawRoundRect(RectF(x - h, y + h * 0.56f, x + h, y + h * 0.85f), h * 0.2f, h * 0.2f, p)
            }
            "coin" -> {
                p.style = Paint.Style.STROKE; p.strokeWidth = s * 0.08f; cv.drawCircle(x, y, h * 0.85f, p)
                p.style = Paint.Style.FILL
                path.moveTo(x, y - h * 0.6f); path.lineTo(x + h * 0.55f, y - h * 0.05f); path.lineTo(x, y + h * 0.5f); path.lineTo(x - h * 0.55f, y - h * 0.05f); path.close(); cv.drawPath(path, p)
            }
            "flower" -> {
                for (k in 0 until 6) { val a = k * 1.0472f; cv.drawCircle(x + cos(a) * h * 0.48f, y - h * 0.15f + sin(a) * h * 0.48f, h * 0.3f, p) }
                p.color = if (bg == 0) shade(c, -60) else bg; cv.drawCircle(x, y - h * 0.15f, h * 0.24f, p)
                p.color = c; p.strokeWidth = s * 0.07f; p.style = Paint.Style.STROKE; cv.drawLine(x, y + h * 0.3f, x, y + h, p)
            }
            "scissors" -> {
                p.style = Paint.Style.STROKE; p.strokeWidth = s * 0.08f; p.strokeCap = Paint.Cap.ROUND
                cv.drawLine(x - h * 0.6f, y - h * 0.9f, x + h * 0.35f, y + h * 0.35f, p); cv.drawLine(x + h * 0.6f, y - h * 0.9f, x - h * 0.35f, y + h * 0.35f, p)
                cv.drawCircle(x - h * 0.5f, y + h * 0.62f, h * 0.27f, p); cv.drawCircle(x + h * 0.5f, y + h * 0.62f, h * 0.27f, p)
            }
            "pole" -> {
                cv.drawRoundRect(RectF(x - h * 0.3f, y - h, x + h * 0.3f, y + h), h * 0.2f, h * 0.2f, p)
                cv.save(); cv.clipRect(x - h * 0.24f, y - h * 0.8f, x + h * 0.24f, y + h * 0.8f)
                p.color = if (bg == 0) 0xFFD32F2F.toInt() else bg
                p.strokeWidth = s * 0.1f; p.style = Paint.Style.STROKE
                var k = -h * 2; while (k < h * 2) { cv.drawLine(x - h * 0.3f, y + k, x + h * 0.3f, y + k - h * 0.5f, p); k += h * 0.45f }
                cv.restore()
            }
            "dumbbell" -> {
                cv.drawRect(x - h * 0.6f, y - h * 0.08f, x + h * 0.6f, y + h * 0.08f, p)
                for (sd in floatArrayOf(-1f, 1f)) { cv.drawRoundRect(RectF(x + sd * h * 0.62f - h * 0.14f, y - h * 0.55f, x + sd * h * 0.62f + h * 0.14f, y + h * 0.55f), h * 0.06f, h * 0.06f, p); cv.drawRoundRect(RectF(x + sd * h * 0.86f - h * 0.1f, y - h * 0.38f, x + sd * h * 0.86f + h * 0.1f, y + h * 0.38f), h * 0.05f, h * 0.05f, p) }
            }
            "cart" -> {
                path.moveTo(x - h, y - h * 0.6f); path.lineTo(x - h * 0.7f, y - h * 0.6f); path.lineTo(x - h * 0.45f, y + h * 0.35f); path.lineTo(x + h * 0.75f, y + h * 0.35f); path.lineTo(x + h * 0.95f, y - h * 0.35f); path.lineTo(x - h * 0.6f, y - h * 0.35f)
                p.style = Paint.Style.STROKE; p.strokeWidth = s * 0.08f; p.strokeJoin = Paint.Join.ROUND; cv.drawPath(path, p)
                p.style = Paint.Style.FILL; cv.drawCircle(x - h * 0.3f, y + h * 0.65f, h * 0.15f, p); cv.drawCircle(x + h * 0.6f, y + h * 0.65f, h * 0.15f, p)
            }
            "phone" -> {
                cv.drawRoundRect(RectF(x - h * 0.45f, y - h, x + h * 0.45f, y + h), h * 0.15f, h * 0.15f, p)
                cut(); cv.drawRect(x - h * 0.35f, y - h * 0.78f, x + h * 0.35f, y + h * 0.65f, p); cv.drawCircle(x, y + h * 0.83f, h * 0.08f, p)
            }
            "hanger" -> {
                p.style = Paint.Style.STROKE; p.strokeWidth = s * 0.07f; p.strokeJoin = Paint.Join.ROUND; p.strokeCap = Paint.Cap.ROUND
                path.moveTo(x - h * 0.15f, y - h * 0.55f); path.quadTo(x - h * 0.15f, y - h * 0.95f, x + h * 0.12f, y - h * 0.85f); path.quadTo(x + h * 0.25f, y - h * 0.65f, x, y - h * 0.35f)
                path.lineTo(x + h, y + h * 0.45f); path.lineTo(x - h, y + h * 0.45f); path.lineTo(x, y - h * 0.35f); cv.drawPath(path, p)
            }
            "star" -> {
                for (k in 0 until 10) { val a = -1.5708f + k * 0.62832f; val r = if (k % 2 == 0) h else h * 0.42f; if (k == 0) path.moveTo(x + cos(a) * r, y + sin(a) * r) else path.lineTo(x + cos(a) * r, y + sin(a) * r) }
                path.close(); cv.drawPath(path, p)
            }
            "H" -> { val t = s * 0.14f; cv.drawRect(x - h * 0.7f, y - h, x - h * 0.7f + t, y + h, p); cv.drawRect(x + h * 0.7f - t, y - h, x + h * 0.7f, y + h, p); cv.drawRect(x - h * 0.7f, y - t / 2, x + h * 0.7f, y + t / 2, p) }
            "P" -> { p.typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD); p.textSize = s * 1.3f; p.textAlign = Paint.Align.CENTER; cv.drawText("P", x, y + s * 0.45f, p) }
            "fork" -> {
                cv.drawRoundRect(RectF(x - h * 0.55f - h * 0.08f, y - h * 0.1f, x - h * 0.55f + h * 0.08f, y + h), h * 0.05f, h * 0.05f, p)
                for (k in -1..1) cv.drawRect(x - h * 0.55f + k * h * 0.13f - h * 0.035f, y - h, x - h * 0.55f + k * h * 0.13f + h * 0.035f, y - h * 0.15f, p)
                cv.drawRect(x - h * 0.75f, y - h * 0.2f, x - h * 0.35f, y - h * 0.05f, p)
                cv.drawRoundRect(RectF(x + h * 0.4f, y - h, x + h * 0.7f, y + h * 0.1f), h * 0.2f, h * 0.3f, p); cv.drawRect(x + h * 0.47f, y, x + h * 0.63f, y + h, p)
            }
            "flame" -> { path.moveTo(x, y - h); path.cubicTo(x + h * 0.9f, y - h * 0.2f, x + h * 0.8f, y + h, x, y + h); path.cubicTo(x - h * 0.8f, y + h, x - h * 0.9f, y - h * 0.1f, x - h * 0.1f, y - h * 0.3f); path.cubicTo(x - h * 0.05f, y - h * 0.6f, x, y - h * 0.8f, x, y - h); cv.drawPath(path, p) }
            "drop" -> { path.moveTo(x, y - h); path.cubicTo(x + h * 0.4f, y - h * 0.3f, x + h * 0.75f, y + h * 0.1f, x + h * 0.75f, y + h * 0.35f); path.cubicTo(x + h * 0.75f, y + h * 0.8f, x - h * 0.75f, y + h * 0.8f, x - h * 0.75f, y + h * 0.35f); path.cubicTo(x - h * 0.75f, y + h * 0.1f, x - h * 0.4f, y - h * 0.3f, x, y - h); cv.drawPath(path, p) }
            "pencil" -> { cv.save(); cv.rotate(-35f, x, y); cv.drawRect(x - h * 0.18f, y - h, x + h * 0.18f, y + h * 0.55f, p); path.moveTo(x - h * 0.18f, y + h * 0.55f); path.lineTo(x + h * 0.18f, y + h * 0.55f); path.lineTo(x, y + h); path.close(); cv.drawPath(path, p); cv.restore() }
            "sun" -> { cv.drawCircle(x, y, h * 0.62f, p); cut(); p.style = Paint.Style.STROKE; p.strokeWidth = s * 0.06f; cv.drawLine(x - h * 0.9f, y + h * 0.85f, x + h * 0.6f, y - h * 0.95f, p); cv.drawLine(x - h * 0.6f, y + h * 0.95f, x + h * 0.9f, y - h * 0.85f, p) }
            "bag" -> { cv.drawRoundRect(RectF(x - h * 0.75f, y - h * 0.35f, x + h * 0.75f, y + h), h * 0.12f, h * 0.12f, p); p.style = Paint.Style.STROKE; p.strokeWidth = s * 0.07f; cv.drawArc(RectF(x - h * 0.4f, y - h * 0.9f, x + h * 0.4f, y + h * 0.1f), 180f, 180f, false, p) }
            "tooth" -> { path.moveTo(x - h * 0.75f, y - h * 0.55f); path.cubicTo(x - h * 0.8f, y - h * 1.05f, x - h * 0.15f, y - h * 0.95f, x, y - h * 0.7f); path.cubicTo(x + h * 0.15f, y - h * 0.95f, x + h * 0.8f, y - h * 1.05f, x + h * 0.75f, y - h * 0.55f); path.cubicTo(x + h * 0.7f, y, x + h * 0.5f, y + h, x + h * 0.3f, y + h); path.cubicTo(x + h * 0.1f, y + h, x + h * 0.15f, y + h * 0.15f, x, y + h * 0.15f); path.cubicTo(x - h * 0.15f, y + h * 0.15f, x - h * 0.1f, y + h, x - h * 0.3f, y + h); path.cubicTo(x - h * 0.5f, y + h, x - h * 0.7f, y, x - h * 0.75f, y - h * 0.55f); cv.drawPath(path, p) }
            else -> {}
        }
    }

    // ---------------------------------------------------------------- geometria
    /** Face do atlas num retângulo vertical (centro x, base y, z; virado para (fx, fz); largura w, altura h). [lit] = false brilha. */
    fun face(b: MB, idx: Int, cx: Float, y: Float, cz: Float, fx: Float, fz: Float, w: Float, h: Float, lit: Boolean = true, tint: Int = C("#FFFFFF")) {
        val u = uv(idx)
        val rx = fz; val rz = -fx
        val ax = cx - rx * w / 2; val az = cz - rz * w / 2
        val ex = cx + rx * w / 2; val ez = cz + rz * w / 2
        val nx = if (lit) fx else 0f; val ny = if (lit) 0.15f else 0f; val nz = if (lit) fz else 0f
        b.m(Mt.SIGN, 1f)
        b.v(ax, y, az, nx, ny, nz, tint, u[0], u[3]); b.v(ex, y, ez, nx, ny, nz, tint, u[2], u[3]); b.v(ex, y + h, ez, nx, ny, nz, tint, u[2], u[1])
        b.v(ax, y, az, nx, ny, nz, tint, u[0], u[3]); b.v(ex, y + h, ez, nx, ny, nz, tint, u[2], u[1]); b.v(ax, y + h, az, nx, ny, nz, tint, u[0], u[1])
    }

    private fun bx(b: MB, cx: Float, cy: Float, cz: Float, fz: Float, sw: Float, sh: Float, sd: Float, c: Int, lit: Boolean = true) {
        // caixa com largura sw ao longo da fachada e profundidade sd (fachada virada para ±z)
        b.box(cx, cy, cz, sw, sh, sd, c, lit)
    }

    /**
     * Letreiro da loja [idx] na fachada em z = [zf] virada para [fz] (só ±1 em z), centro [cx], base [y], largura máxima [maxW], altura [h].
     * Devolve a largura usada.
     */
    fun mount(b: MB, idx: Int, cx: Float, y: Float, zf: Float, fz: Float, maxW: Float, h: Float, wallOff: Float = 0.13f): Float {
        val s = spec(idx)
        val w = maxW
        val z = zf + fz * wallOff   // [zf] = meio da parede; a face de fora fica a ~12 cm
        when (s.style) {
            BOX -> {
                // caixa de alumínio com o acrílico iluminado
                b.m(Mt.METAL, 1f)
                bx(b, cx, y + h / 2, z + fz * 0.09f, fz, w + 0.12f, h + 0.12f, 0.18f, C("#3A3F45"))
                for (sd in floatArrayOf(-1f, 1f)) bx(b, cx + sd * (w / 2 - 0.25f), y - 0.06f, z + fz * 0.05f, fz, 0.06f, 0.14f, 0.1f, C("#2B2F33"))
                face(b, idx, cx, y, z + fz * 0.185f, 0f, fz, w, h, false)
            }
            LETTERS -> {
                // letras soltas em relevo: três camadas (fundo escuro = espessura, frente = face) + filete de luz embaixo
                val tint = C("#FFFFFF")
                face(b, idx, cx + 0.012f, y - 0.014f, z + fz * 0.03f, 0f, fz, w, h, true, C("#5A5A5A"))
                face(b, idx, cx + 0.006f, y - 0.007f, z + fz * 0.055f, 0f, fz, w, h, true, C("#9A9A9A"))
                face(b, idx, cx, y, z + fz * 0.08f, 0f, fz, w, h, true, tint)
            }
            NEON -> {
                b.m(Mt.METAL, 1f)
                bx(b, cx, y + h / 2, z + fz * 0.03f, fz, w + 0.3f, h + 0.24f, 0.06f, C("#15171A"))
                b.m(Mt.PLAIN); bx(b, cx, y + h / 2, z + fz * 0.062f, fz, w + 0.18f, h + 0.12f, 0.004f, C("#0B0C0E"))
                face(b, idx, cx, y, z + fz * 0.07f, 0f, fz, w, h, false)
            }
            BOARD -> {
                b.m(Mt.WOOD, 1f)
                bx(b, cx, y + h / 2, z + fz * 0.05f, fz, w + 0.16f, h + 0.16f, 0.09f, C("#4A2E1A"))
                for (sd in floatArrayOf(-1f, 1f)) bx(b, cx + sd * (w / 2 + 0.05f), y + h / 2, z + fz * 0.1f, fz, 0.08f, h + 0.2f, 0.05f, C("#3B2414"))
                bx(b, cx, y + h + 0.06f, z + fz * 0.1f, fz, w + 0.26f, 0.06f, 0.05f, C("#3B2414")); bx(b, cx, y - 0.06f, z + fz * 0.1f, fz, w + 0.26f, 0.06f, 0.05f, C("#3B2414"))
                face(b, idx, cx, y, z + fz * 0.096f, 0f, fz, w, h, true)
                // duas luminárias de haste iluminando a placa
                b.m(Mt.METAL, 1f)
                for (sd in floatArrayOf(-0.32f, 0.32f)) {
                    val lx = cx + sd * w
                    bx(b, lx, y + h + 0.2f, z + fz * 0.25f, fz, 0.03f, 0.03f, 0.5f, C("#222222"))
                    bx(b, lx, y + h + 0.14f, z + fz * 0.5f, fz, 0.16f, 0.1f, 0.12f, C("#222222"))
                    b.m(Mt.PLAIN); bx(b, lx, y + h + 0.085f, z + fz * 0.5f, fz, 0.12f, 0.01f, 0.08f, C("#FFF3C4"), false); b.m(Mt.METAL, 1f)
                }
            }
            PLATE -> face(b, idx, cx, y, z + fz * 0.02f, 0f, fz, w, h, true)
            AWNING -> face(b, idx, cx, y, z + fz * 0.02f, 0f, fz, w, h, true)
        }
        return w
    }

    /** Bandeira lateral (placa quadrada perpendicular à fachada, dos dois lados). */
    fun blade(b: MB, k: Int, x: Float, y: Float, zf0: Float, fz: Float, size: Float = 0.75f) {
        val zf = zf0 + fz * 0.12f
        b.m(Mt.METAL, 1f)
        val armL = size + 0.25f
        b.box(x, y + size + 0.08f, zf + fz * armL / 2, 0.05f, 0.05f, armL, C("#2B2B2B"))
        b.box(x, y + size / 2, zf + fz * 0.03f, 0.08f, size + 0.2f, 0.06f, C("#2B2B2B"))
        // diagonal (mão-francesa)
        CityGeo.limb(b, x, y + 0.1f, zf + fz * 0.03f, x, y + size + 0.05f, zf + fz * armL * 0.8f, 0.018f, 0.018f, C("#2B2B2B"), 4)
        val cz = zf + fz * (0.2f + size / 2)
        b.box(x, y + size / 2, cz, 0.08f, size + 0.06f, size + 0.06f, C("#333333"))
        // as duas faces (uma virada para cada lado da rua)
        val u = 200 + k
        faceSide(b, u, x + 0.042f, y, cz, 1f, fz, size)
        faceSide(b, u, x - 0.042f, y, cz, -1f, fz, size)
        for (q in 0..1) b.box(x, y + size + 0.08f, zf + fz * (0.25f + q * (size - 0.1f)), 0.02f, 0.06f, 0.02f, C("#555555"))
    }

    private fun faceSide(b: MB, idx: Int, x: Float, y: Float, cz: Float, sx: Float, fz: Float, s: Float) {
        // quad no plano x = const, virado para sx; texto lido da esquerda para a direita
        val u = uv(idx)
        val za = cz - fz * s / 2 * (-sx); val zb = cz + fz * s / 2 * (-sx)
        b.m(Mt.SIGN, 1f)
        val n = 0f
        b.v(x, y, za, n, n, n, C("#FFFFFF"), u[0], u[3]); b.v(x, y, zb, n, n, n, C("#FFFFFF"), u[2], u[3]); b.v(x, y + s, zb, n, n, n, C("#FFFFFF"), u[2], u[1])
        b.v(x, y, za, n, n, n, C("#FFFFFF"), u[0], u[3]); b.v(x, y + s, zb, n, n, n, C("#FFFFFF"), u[2], u[1]); b.v(x, y + s, za, n, n, n, C("#FFFFFF"), u[0], u[1])
    }

    /** Toldo: 0 nenhum, 1 lona lisa com aba recortada, 2 listrado, 3 lona escura, 4 rosado, 5 verde floricultura, 6 madeira (pergolado). */
    fun awning(b: MB, type: Int, x0: Float, x1: Float, yTop: Float, zf: Float, fz: Float, depth: Float, color: Int, textIdx: Int = -1) {
        if (type == 0) return
        val y0 = yTop; val y1 = yTop - 0.55f
        val za = zf + fz * 0.13f; val zb = zf + fz * depth
        if (type == 6) {
            b.m(Mt.WOOD, 1f)
            val n = ((x1 - x0) / 0.45f).toInt()
            for (k in 0..n) b.box(x0 + k * (x1 - x0) / n, y0 - 0.06f, (za + zb) / 2, 0.08f, 0.12f, depth, C("#6D4C41"))
            b.box((x0 + x1) / 2, y0 - 0.18f, zb, x1 - x0 + 0.1f, 0.14f, 0.12f, C("#5D4037"))
            for (sd in floatArrayOf(x0 + 0.05f, x1 - 0.05f)) CityGeo.limb(b, sd, y0 - 1.2f, za, sd, y0 - 0.15f, zb - fz * 0.1f, 0.035f, 0.035f, C("#5D4037"), 5)
            return
        }
        val c1 = color
        val c2 = if (type == 2) C("#FFFFFF") else shade(color, -18)
        val n = if (type == 2) max(6, ((x1 - x0) / 0.5f).toInt()) else 1
        b.m(Mt.FABRIC, 1f)
        for (s in 0 until n) {
            val a0 = x0 + (x1 - x0) * s / n; val a1 = x0 + (x1 - x0) * (s + 1) / n
            val c = if (s % 2 == 0) c1 else c2
            // lona levemente curva (dois segmentos)
            val ym = (y0 + y1) / 2 + 0.06f; val zm = (za + zb) / 2
            q(b, P(a0, y0, za) + P(a1, y0, za) + P(a1, ym, zm) + P(a0, ym, zm), c)
            q(b, P(a0, ym, zm) + P(a1, ym, zm) + P(a1, y1, zb) + P(a0, y1, zb), shade(c, -6))
        }
        // aba: recortada (festonada) ou reta, com o nome
        val vh = 0.3f
        if (textIdx >= 0) face(b, textIdx, (x0 + x1) / 2, y1 - vh, zb + fz * 0.008f, 0f, fz, (x1 - x0) * 0.98f, vh, true)
        b.m(Mt.FABRIC, 1f)
        val ns = max(4, ((x1 - x0) / 0.38f).toInt())
        for (s in 0 until ns) {
            val a0 = x0 + (x1 - x0) * s / ns; val a1 = x0 + (x1 - x0) * (s + 1) / ns
            val c = if (type == 2 && s % 2 == 1) c2 else c1
            if (textIdx < 0) q(b, P(a0, y1, zb) + P(a1, y1, zb) + P(a1, y1 - vh, zb) + P(a0, y1 - vh, zb), c)
            // festão (meia-lua embaixo da aba)
            CityGeo.tri(b, P(a0, y1 - vh, zb) + P(a1, y1 - vh, zb) + P((a0 + a1) / 2, y1 - vh - 0.1f, zb), c)
        }
        // braços de ferro
        b.m(Mt.METAL, 1f)
        for (sd in floatArrayOf(x0 + 0.08f, x1 - 0.08f)) CityGeo.limb(b, sd, y0 - 0.02f, za, sd, y1 + 0.02f, zb - fz * 0.02f, 0.02f, 0.02f, C("#2E2E2E"), 4)
    }

    /** Plaquinha "ABERTO" pendurada na porta, número da loja e adesivo na vitrine. */
    fun doorDetails(b: MB, doorX: Float, yFloor: Float, zf: Float, fz: Float, winX: Float, winW: Float, accent: Int, num: Int) {
        val z = zf + fz * 0.03f
        b.m(Mt.PLAIN)
        b.box(doorX, yFloor + 1.62f, z + fz * 0.005f, 0.34f, 0.14f, 0.01f, C("#C62828"), false)
        b.box(doorX, yFloor + 1.62f, z + fz * 0.01f, 0.26f, 0.05f, 0.01f, C("#FFFFFF"), false)
        b.m(Mt.METAL, 1f); b.box(doorX, yFloor + 1.74f, z, 0.005f, 0.12f, 0.005f, C("#555555"))
        // número
        b.m(Mt.PLAIN); b.box(doorX + 0.95f, yFloor + 2.35f, zf + fz * 0.135f, 0.22f, 0.14f, 0.012f, C("#1F3A5F")); b.box(doorX + 0.95f, yFloor + 2.35f, zf + fz * 0.142f, 0.12f, 0.08f, 0.004f, C("#FFFFFF"))
        // faixa decorativa na vitrine (adesivo jateado)
        b.m(Mt.PLAIN); b.al = 0.55f
        b.box(winX, yFloor + 1.1f, zf + fz * 0.02f, winW * 0.92f, 0.12f, 0.004f, C("#FFFFFF"), false)
        b.al = 1f
        b.box(winX, yFloor + 0.5f, zf + fz * 0.022f, winW * 0.92f, 0.04f, 0.004f, accent, false)
    }

    /** Cavalete de giz na calçada. */
    fun aframe(b: MB, x: Float, y: Float, z: Float, fz: Float) {
        b.m(Mt.WOOD, 1f)
        for (sd in floatArrayOf(-1f, 1f)) {
            q(b, P(x - 0.32f, y + 0.95f, z) + P(x + 0.32f, y + 0.95f, z) + P(x + 0.32f, y, z + sd * 0.25f) + P(x - 0.32f, y, z + sd * 0.25f), C("#6D4C41"))
            b.m(Mt.PLAIN)
            q(b, P(x - 0.26f, y + 0.86f, z + sd * 0.035f) + P(x + 0.26f, y + 0.86f, z + sd * 0.035f) + P(x + 0.26f, y + 0.1f, z + sd * 0.235f) + P(x - 0.26f, y + 0.1f, z + sd * 0.235f), C("#263238"))
            for (k in 0 until 4) { val t = 0.2f + k * 0.17f; val yy = y + 0.86f - t * 0.76f; val zz = z + sd * (0.035f + t * 0.2f) + sd * 0.004f
                q(b, P(x - 0.2f + (k % 2) * 0.04f, yy, zz) + P(x + 0.18f - (k % 3) * 0.05f, yy, zz) + P(x + 0.18f - (k % 3) * 0.05f, yy - 0.025f, zz + sd * 0.006f) + P(x - 0.2f + (k % 2) * 0.04f, yy - 0.025f, zz + sd * 0.006f), if (k == 0) C("#FFD54F") else C("#ECEFF1")) }
            b.m(Mt.WOOD, 1f)
        }
    }

    /** Floreira de madeira com flores na frente da vitrine. */
    fun planter(b: MB, x: Float, y: Float, z: Float, w: Float, rng: City.Rng) {
        b.m(Mt.WOOD, 1f); b.box(x, y + 0.2f, z, w, 0.4f, 0.4f, C("#7A5A3A"))
        b.m(Mt.PLAIN); b.box(x, y + 0.39f, z, w - 0.08f, 0.02f, 0.32f, C("#4E3B2A"))
        val cols = arrayOf("#E53935", "#FDD835", "#AB47BC", "#FFFFFF", "#FF7043", "#EC407A")
        val n = (w / 0.14f).toInt()
        for (k in 0 until n) {
            val px = x - w / 2 + 0.08f + k * (w - 0.16f) / max(1, n - 1)
            for (j in 0..1) {
                val pz = z - 0.08f + j * 0.16f
                CityGeo.ball(b, px, y + 0.47f, pz, 0.09f, C(if ((k + j) % 2 == 0) "#4F8A3A" else "#5E9944"), 0.07f, 5)
                if ((k + j) % 2 == 0) CityGeo.ball(b, px + 0.02f, y + 0.55f, pz, 0.05f, C(cols[(k * 3 + j + rng.i(3)) % cols.size]), 0.04f, 5)
            }
        }
    }
}
