package com.vinicius.meular

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.provider.OpenableColumns
import com.vinicius.meular.mods.Importer
import java.io.File

/**
 * Peças importadas de arquivos .package e itens nativos compatíveis com os corpos do The Sims 4.
 * Cada peça fica em filesDir/mods: <id>.cup (malha já encaixada no corpo), <id>.png (textura), index.txt e worn.txt.
 */
object ModStore {
    class Item(val id: String, var name: String, val slot: String, val grp: String, val game: Int, var hasTex: Boolean, val alpha: Boolean, val builtin: Boolean = false) {
        val key: String get() = "$slot/M_$id"
    }

    class VarColor(val slug: String, val nome: String, val argb: Int)
    /** Peça de modelo único com várias cores: uma malha e uma textura por cor (a escolhida no seletor de cores). */
    class Var(val label: String, val colors: List<VarColor>, val thumb: String, val cupOf: (String) -> String, val pngOf: (String) -> String)

    const val LOTUS_ID = "lotusc_af5"
    const val BLOOM_ID = "bloom_af5"
    const val AUTUMN_ID = "autumn_af5"
    const val HOOD_ID = "hood_af5"
    const val HCARGO_ID = "hcargo_af5"
    // Etapa 107: as mesmas peças refeitas para o corpo masculino do Sims 4 (am5)
    const val HOOD_M_ID = "hood_am5"
    const val HCARGO_M_ID = "hcargo_am5"

    val LOTUS = listOf(
        VarColor("preto", "Preto", 0xFF262326.toInt()),
        VarColor("castanhoe", "Castanho escuro", 0xFF4A3225.toInt()),
        VarColor("castanho", "Castanho", 0xFF7A5238.toInt()),
        VarColor("ruivo", "Ruivo", 0xFFB5532D.toInt()),
        VarColor("loiroe", "Loiro escuro", 0xFFA07C48.toInt()),
        VarColor("loiro", "Loiro", 0xFFD9B96A.toInt()),
        VarColor("platina", "Platinado", 0xFFE8DFC8.toInt()),
        VarColor("cinza", "Cinza", 0xFF8E9096.toInt()),
        VarColor("rosa", "Rosa", 0xFFE0517F.toInt()),
        VarColor("azul", "Azul", 0xFF2F62C0.toInt())
    )
    val BLOOM = listOf(
        VarColor("branco", "Branca", 0xFFF2F0EC.toInt()),
        VarColor("creme", "Creme", 0xFFE8DCBF.toInt()),
        VarColor("azul", "Azul claro", 0xFFA9CBEA.toInt()),
        VarColor("lavanda", "Lavanda", 0xFFB7A6DB.toInt()),
        VarColor("pessego", "Pêssego", 0xFFF4B79B.toInt()),
        VarColor("coral", "Coral", 0xFFF26D5F.toInt()),
        VarColor("vermelho", "Vermelha", 0xFFC4283A.toInt()),
        VarColor("cinza", "Cinza", 0xFF9B9DA3.toInt()),
        VarColor("preto", "Preta", 0xFF2A282B.toInt()),
        VarColor("verde", "Verde", 0xFF5E9E5A.toInt()),
        VarColor("amarelo", "Amarela", 0xFFEFCB4A.toInt()),
        VarColor("rosa", "Rosa pink", 0xFFD8337F.toInt())
    )
    val AUTUMN = listOf(
        VarColor("mostarda", "Xadrez mostarda", 0xFFD9A441.toInt()),
        VarColor("cinza", "Xadrez cinza", 0xFFB8B2A8.toInt()),
        VarColor("oliva", "Xadrez verde-oliva", 0xFF7C7A3C.toInt()),
        VarColor("ferrugem", "Xadrez ferrugem", 0xFFB4502A.toInt()),
        VarColor("petroleo", "Xadrez azul petróleo", 0xFF4C95A8.toInt()),
        VarColor("preto", "Preta", 0xFF26262A.toInt())
    )
    // Etapa 105: conjunto "Hooded short jacket" (finistudio, Sims 4): jaqueta com capuz e calça cargo com cintos, 6 cores (a textura é a mesma para as duas peças)
    val HOOD = listOf(
        VarColor("preto", "Preto", 0xFF26262A.toInt()),
        VarColor("grafite", "Grafite", 0xFF55565A.toInt()),
        VarColor("branco", "Branco", 0xFFEDEDEF.toInt()),
        VarColor("azul", "Azul", 0xFF2A2FA8.toInt()),
        VarColor("bege", "Bege", 0xFFC9A98E.toInt()),
        VarColor("ardosia", "Azul ardósia", 0xFF5A6578.toInt())
    )
    val ROSS = listOf(
        VarColor("preto", "Preto", 0xFF29252A.toInt()),
        VarColor("castanhoe", "Castanho escuro", 0xFF493126.toInt()),
        VarColor("castanho", "Castanho", 0xFF795039.toInt()),
        VarColor("loiroe", "Loiro escuro", 0xFF9C7848.toInt()),
        VarColor("loiro", "Loiro", 0xFFD6B66D.toInt()),
        VarColor("platinado", "Platinado", 0xFFE8E2D5.toInt()),
        VarColor("ruivo", "Ruivo", 0xFFAD4F2B.toInt()),
        VarColor("azul", "Azul", 0xFF416BC5.toInt()),
        VarColor("rosa", "Rosa", 0xFFD65A91.toInt())
    )
    val VARS: Map<String, Var> = mapOf(
        "ross1_am5" to Var("Cabelo Ross masculino", ROSS, "ross1_am5", { _ -> "ross1_am5" }, { _ -> "ross1_am5" }),
        "ross1_af5" to Var("Cabelo Ross feminino", ROSS, "ross1_af5", { _ -> "ross1_af5" }, { _ -> "ross1_af5" }),
        LOTUS_ID to Var("Cabelo Lotus — coque", LOTUS, "lotusc_preto_af5", { _ -> "lotus_coque" }, { c -> "lotus_$c" }),
        BLOOM_ID to Var("Blusa Bloom", BLOOM, "bloom_branco_af5", { c -> "bloom_${c}_af5" }, { c -> "bloom_${c}_af5" }),
        AUTUMN_ID to Var("Saia Autumn Grace", AUTUMN, "autumn_mostarda_af5", { _ -> "autumn_af5" }, { c -> "autumn_$c" }),
        HOOD_ID to Var("Jaqueta com capuz", HOOD, "hood_preto_af5", { _ -> "hood_af5" }, { c -> "hood_$c" }),
        HCARGO_ID to Var("Calça cargo com cintos", HOOD, "hcargo_preto_af5", { _ -> "hcargo_af5" }, { c -> "hood_$c" }),
        HOOD_M_ID to Var("Jaqueta com capuz", HOOD, "hood_preto_am5", { _ -> "hood_am5" }, { c -> "hood_$c" }),
        HCARGO_M_ID to Var("Calça cargo com cintos", HOOD, "hcargo_preto_am5", { _ -> "hcargo_am5" }, { c -> "hood_$c" })
    )
    private val sel = HashMap<String, Int>()   // id da peça -> índice da cor escolhida (0 = a primeira)
    fun variantIndex(id: String): Int = synchronized(this) { sel[id] ?: 0 }

    val items = ArrayList<Item>()
    private val worn = LinkedHashSet<String>()
    private var dir: File? = null
    @Volatile private var busy = false
    val isBusy: Boolean get() = busy

    val SLOT_NAMES = mapOf("top" to "Blusa", "jacket" to "Jaqueta", "bottom" to "Calça/saia", "overall" to "Roupa inteira", "feet" to "Sapatos", "hairBack" to "Cabelo", "hat" to "Chapéu", "gloves" to "Luvas", "glasses" to "Óculos", "beard" to "Barba", "headAcc" to "Acessório")

    @Synchronized
    fun init(ctx: Context) {
        if (dir != null) return
        val d = File(ctx.filesDir, "mods")
        d.mkdirs()
        dir = d
        try {
            File(d, "index.txt").takeIf { it.exists() }?.readLines(Charsets.UTF_8)?.forEach { ln ->
                val f = ln.split('|')
                if (f.size >= 7) {
                    val game = f[4].toIntOrNull() ?: 0
                    if (game == 4 && File(d, f[0] + ".cup").exists()) {
                        items.add(Item(f[0], f[1], f[2], f[3], game, f[5] == "1", f[6] == "1"))
                    } else if (game != 4) {
                        // Remove do armazenamento local peças importadas de The Sims 2/3.
                        for (suffix in listOf(".cup", ".png", ".t0.thumb.png", ".t1.thumb.png")) {
                            File(d, f[0] + suffix).delete()
                        }
                    }
                }
            }
            File(d, "worn.txt").takeIf { it.exists() }?.readText()?.split(',')?.forEach { if (it.isNotBlank()) worn.add(it.trim()) }
        } catch (e: Throwable) {
            android.util.Log.e("ModStore", "índice ilegível", e)
        }
        // Cabelo Bernard (JohnnySims), preparado exclusivamente para os corpos adultos do Sims 4.
        for (g in listOf("af5", "am5")) {
            items.add(Item("bern1_$g", "Bernard (JohnnySims)", "hairBack", g.substring(0, 2), 0, true, true, true))
        }
        // Ross JohnnySims: apenas V1; V2 foi removido por ser visualmente igual.
        items.add(Item("ross1_am5", "Cabelo Ross", "hairBack", "am", 0, true, true, true))
        items.add(Item("ross1_af5", "Cabelo Ross", "hairBack", "af", 0, true, true, true))
        // Etapa 95: Aurum Bloom Top (Sims 4), blusa de renda off-shoulder só para o corpo feminino do Sims 4 (af5): um item, 12 cores no seletor
        items.add(Item(BLOOM_ID, "Blusa renda Bloom", "top", "af", 0, true, true, true))
        // Etapa 94: Aurum Hairstyle FMM 146 "Lotus" (Sims 4), só o coque, um único item (preto); a cor troca no seletor de cores do Cabelo
        items.add(Item(LOTUS_ID, "Lotus — coque", "hairBack", "af", 0, true, true, true))
        // Etapa 95: GoldFish Autumn Grace (Sims 4), saia rodada com cinto, só para o corpo feminino do Sims 4 (af5): um item, 6 cores no seletor
        items.add(Item(AUTUMN_ID, "Saia Autumn Grace", "bottom", "af", 0, true, true, true))
        // Etapa 105: jaqueta com capuz (slot jaqueta) e calça cargo com cintos (slot calça), só para o corpo feminino do Sims 4 (af5)
        items.add(Item(HOOD_ID, "Jaqueta com capuz", "jacket", "af", 0, true, false, true))
        items.add(Item(HCARGO_ID, "Calça cargo com cintos", "bottom", "af", 0, true, false, true))
        // Etapa 107: versão masculina (corpo am5) da jaqueta com capuz e da calça cargo
        items.add(Item(HOOD_M_ID, "Jaqueta com capuz", "jacket", "am", 0, true, false, true))
        items.add(Item(HCARGO_M_ID, "Calça cargo com cintos", "bottom", "am", 0, true, false, true))
        loadVariants(d)
        // quem já tinha Lotus/Bloom vestido num item por cor (Etapas 92/93) passa para o item único, com a mesma cor
        for (k in worn.toList()) {
            val m = Regex("(hairBack|top)/M_(lotusc|bloom)_([a-z]+)_af5").matchEntire(k) ?: continue
            val id = if (m.groupValues[2] == "lotusc") LOTUS_ID else BLOOM_ID
            val i = VARS[id]!!.colors.indexOfFirst { c -> c.slug == m.groupValues[3] }
            worn.remove(k)
            if (i >= 0) sel[id] = i
            worn.add(m.groupValues[1] + "/M_" + id)
        }
        // Low fade texturizado removido do catálogo a pedido do usuário.
        // regata baggy do pacote "Baggy Singlet Set" (Mod The Sims, ArthurGoring), já convertida: corpos masculinos jovem/adulto/idoso
        for (g in listOf("am", "tm", "em")) {
            items.add(Item("singlet_white_$g", "Regata baggy branca", "top", g, 0, true, true, true))
            items.add(Item("singlet_black_$g", "Regata baggy preta", "top", g, 0, true, true, true))
            items.add(Item("singlet_love_$g", "Regata love you (preta)", "top", g, 0, true, true, true))
            items.add(Item("singlet_haters_$g", "Regata haters (preta)", "top", g, 0, true, true, true))
        }
        // Remove também qualquer low fade antigo que tenha ficado salvo como equipado.
        for (key in worn.filter { it.startsWith("hairBack/M_fade1_") }) {
            worn.remove(key)
            CuteChar.enqueueMod(key, null, null, false)
        }
        worn.retainAll(items.map { it.key }.toSet())
        saveIndex()   // regrava o índice sem os mods antigos do Sims 2/3
    }

    /** Escolhe a cor (índice em VARS[id].colors) de uma peça de modelo único; se está vestida, a textura troca na hora. */
    fun setVariant(id: String, i: Int) {
        val v = VARS[id] ?: return
        if (i !in v.colors.indices) return
        val item = synchronized(this) {
            sel[id] = i
            try { dir?.let { d -> File(d, "variants.txt").writeText(sel.entries.joinToString("\n") { e -> e.key + "=" + (VARS[e.key]?.colors?.getOrNull(e.value)?.slug ?: "") }) } } catch (e: Throwable) { }
            items.firstOrNull { x -> x.id == id }
        }
        if (item != null && isWorn(item)) Thread { load(item) }.start()
    }

    private fun loadVariants(d: File) {
        try {
            val f = File(d, "variants.txt")
            if (f.exists()) {
                for (ln in f.readLines(Charsets.UTF_8)) {
                    val p = ln.split('=')
                    if (p.size != 2) continue
                    val i = VARS[p[0]]?.colors?.indexOfFirst { c -> c.slug == p[1] } ?: -1
                    if (i >= 0) sel[p[0]] = i
                }
            } else {
                // Etapa 94 guardava só o índice da cor do Lotus
                File(d, "lotuscolor.txt").takeIf { it.exists() }?.readText()?.trim()?.toIntOrNull()?.let { i -> if (i in LOTUS.indices) sel[LOTUS_ID] = i }
            }
        } catch (e: Throwable) { }
    }

    /** Veste a peça (troca a do mesmo tipo). Já vestida: não faz nada. */
    @Synchronized
    fun select(it: Item) { if (it.key !in worn) toggle(it) }

    /** Tira tudo o que está vestido nesses tipos (ex.: "top") para o corpo [grp]. */
    @Synchronized
    fun clear(grp: String, slots: Collection<String>) {
        for (o in items.filter { x -> x.grp == grp && x.slot in slots && x.key in worn }) toggle(o)
    }

    // ---- miniaturas (a "foto de prévia" de cada peça) ----
    /** Miniatura embutida (assets/cute/thumbs/<nome>.png). Chamar fora da thread da tela. */
    fun assetThumb(name: String): Bitmap? {
        return try {
        val src = CuteChar.assets?.open("cute/thumbs/$name.png")?.use { BitmapFactory.decodeStream(it) } ?: return null
        // Padroniza todas as miniaturas em um canvas quadrado, com a mesma margem e sem distorcer a peça.
        val side = 256
        val out = Bitmap.createBitmap(side, side, Bitmap.Config.ARGB_8888)
        val canvas = android.graphics.Canvas(out)
        val paint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG or android.graphics.Paint.FILTER_BITMAP_FLAG)
        val scale = minOf((side * 0.88f) / src.width, (side * 0.88f) / src.height)
        val w = src.width * scale; val h = src.height * scale
        val dst = android.graphics.RectF((side - w) / 2f, (side - h) / 2f, (side + w) / 2f, (side + h) / 2f)
        canvas.drawBitmap(src, null, dst, paint)
        if (src !== out && !src.isRecycled) src.recycle()
        out
        } catch (e: Throwable) { null }
    }

    private fun tintBitmap(src: Bitmap, argb: Int): Bitmap {
        val w = src.width; val h = src.height
        val px = IntArray(w * h); src.getPixels(px, 0, w, 0, 0, w, h)
        val tr = (argb shr 16) and 255; val tg = (argb shr 8) and 255; val tb = argb and 255
        for (i in px.indices) {
            val c = px[i]; val a = c ushr 24
            if (a == 0) continue
            val r = (((c shr 16) and 255) * tr / 255).coerceIn(0, 255)
            val g = (((c shr 8) and 255) * tg / 255).coerceIn(0, 255)
            val b = ((c and 255) * tb / 255).coerceIn(0, 255)
            px[i] = (a shl 24) or (r shl 16) or (g shl 8) or b
        }
        return Bitmap.createBitmap(px, w, h, Bitmap.Config.ARGB_8888)
    }

    /** Miniatura da peça: embutida, ou gerada na primeira vez (peças importadas) e guardada em disco. Chamar fora da thread da tela. */
    fun thumb(it: Item): Bitmap? {
        if (it.builtin) {
            // Gera a miniatura com o Sim usando a peça, em vez de usar recortes isolados e inconsistentes.
            return try { renderBuiltinThumb(it) ?: assetThumb(VARS[it.id]?.thumb ?: it.id) }
            catch (e: Throwable) {
                android.util.Log.e("ModStore", "prévia 3D " + it.id, e)
                assetThumb(VARS[it.id]?.thumb ?: it.id)
            }
        }
        val d = dir ?: return null
        val f = File(d, it.id + (if (it.hasTex) ".t1" else ".t0") + ".thumb.png")
        if (f.exists()) BitmapFactory.decodeFile(f.path)?.let { b -> return b }
        val b = try { renderThumb(it) } catch (e: Throwable) { android.util.Log.e("ModStore", "miniatura " + it.id, e); null } ?: return null
        try { f.outputStream().use { o -> b.compress(Bitmap.CompressFormat.PNG, 100, o) } } catch (e: Throwable) { }
        return b
    }

    /** Miniatura de item nativo: corpo/cabeça de apoio + peça real + textura selecionada. */
    private fun renderBuiltinThumb(it: Item): Bitmap? {
        val am = CuteChar.assets ?: return null
        val vr = VARS[it.id]
        val slug = vr?.colors?.get(variantIndex(it.id))?.slug
        val cupName = if (vr != null && slug != null) vr.cupOf(slug) else it.id
        val pngName = if (vr != null && slug != null) vr.pngOf(slug) else it.id
        val cup = am.open("cute/skate/$cupName.cup").use { it.readBytes() }
        val opts = BitmapFactory.Options().apply { inPremultiplied = false }
        var bmp = am.open("cute/skate/$pngName.png").use { BitmapFactory.decodeStream(it, null, opts) } ?: return null
        if (it.id.startsWith("ross1_") && vr != null) {
            val tinted = tintBitmap(bmp, vr.colors[variantIndex(it.id)].argb)
            if (!bmp.isRecycled) bmp.recycle()
            bmp = tinted
        }
        val tw = bmp.width
        val th = bmp.height
        val pixels = IntArray(tw * th)
        bmp.getPixels(pixels, 0, tw, 0, 0, tw, th)
        val parts = ArrayList<Thumb.Piece>()
        val isHead = it.slot in setOf("hairBack", "hairFront", "hat", "headAcc", "glasses", "beard")
        // Os corpos-base disponíveis são os adultos Sims 4; o grupo do item escolhe o sexo correspondente.
        val bodyName = if (it.grp.startsWith("am") || it.grp == "tm" || it.grp == "em") "p_body_am5.bin" else "p_body_af5.bin"
        try {
            val body = Thumb.parse(am.open("cute/$bodyName").use { it.readBytes() })
            val support = if (isHead) Thumb.headOf(body) else body
            parts.add(Thumb.Piece(support, null, 0, 0, 0xFFE3BFA2.toInt(), false, true))
        } catch (e: Throwable) {
            android.util.Log.w("ModStore", "corpo de apoio indisponível para " + it.id, e)
        }
        parts.add(Thumb.Piece(Thumb.parse(cup), pixels, tw, th, 0xFFFFFFFF.toInt(), it.alpha))
        val rendered = Thumb.render(parts, it.slot, 256)
        if (!bmp.isRecycled) bmp.recycle()
        return Bitmap.createBitmap(rendered, 256, 256, Bitmap.Config.ARGB_8888)
    }

    private fun renderThumb(it: Item): Bitmap? {
        val d = dir ?: return null
        var cup = File(d, it.id + ".cup").readBytes()
        var pixels: IntArray? = null
        var tw = 0
        var th = 0
        if (it.hasTex) {
            val o = BitmapFactory.Options()
            o.inPremultiplied = false
            var bmp = BitmapFactory.decodeFile(File(d, it.id + ".png").path, o)
            if (bmp != null) {
                if (bmp.width > 1024 || bmp.height > 1024) {
                    val k = 1024f / maxOf(bmp.width, bmp.height)
                    bmp = Bitmap.createScaledBitmap(bmp, (bmp.width * k).toInt().coerceAtLeast(1), (bmp.height * k).toInt().coerceAtLeast(1), true)
                }
                tw = bmp.width
                th = bmp.height
                pixels = IntArray(tw * th)
                bmp.getPixels(pixels, 0, tw, 0, 0, tw, th)
                if (it.game == 2) cup = Importer.cullBlack(cup, pixels, tw, th)
            }
        }
        val parts = ArrayList<Thumb.Piece>()
        if (it.slot == "hairBack" || it.slot == "hat") {
            try {
                val am = CuteChar.assets
                if (am != null) {
                    val bm = Thumb.parse(am.open("cute/p_body_" + it.grp + (if (CuteChar.isTs4()) "5" else "1") + ".bin").use { s -> s.readBytes() })
                    parts.add(Thumb.Piece(Thumb.headOf(bm), null, 0, 0, 0xFFE3BFA2.toInt(), false, true))
                }
            } catch (e: Throwable) { }
        }
        parts.add(Thumb.Piece(Thumb.parse(cup), pixels, tw, th, 0xFF9AA3AD.toInt(), it.alpha))
        val px = Thumb.render(parts, it.slot, 256)
        return Bitmap.createBitmap(px, 256, 256, Bitmap.Config.ARGB_8888)
    }

    private fun saveIndex() {
        val d = dir ?: return
        try {
            File(d, "index.txt").writeText(items.filter { !it.builtin }.joinToString("\n") { listOf(it.id, it.name.replace('|', ' '), it.slot, it.grp, it.game, if (it.hasTex) 1 else 0, if (it.alpha) 1 else 0).joinToString("|") }, Charsets.UTF_8)
            File(d, "worn.txt").writeText(worn.joinToString(","))
        } catch (e: Throwable) {
            android.util.Log.e("ModStore", "não salvou", e)
        }
    }

    /** Chaves das peças vestidas que servem para o corpo [grp] (idade+sexo, ex.: "af"). */
    @Synchronized
    /** O catálogo aceita somente itens nativos Sims 4 e arquivos .package identificados como Sims 4. */
    fun visible(it: Item, ts4: Boolean): Boolean = it.builtin || it.game == 4

    fun wornKeys(grp: String): List<String> = items.filter { it.key in worn && it.grp == grp && visible(it, CuteChar.isTs4()) }.map { it.key }

    @Synchronized
    fun isWorn(it: Item) = it.key in worn

    @Synchronized
    fun toggle(it: Item) {
        if (it.key in worn) {
            worn.remove(it.key)
            if (it.builtin) CuteChar.enqueueMod(it.key, null, null, false)   // libera a textura
        } else {
            // um por tipo; roupa inteira troca blusa e calça
            val same = items.filter { o -> o.grp == it.grp && o.key in worn }
            for (o in same) {
                val clash = o.slot == it.slot ||
                    (it.slot == "overall" && (o.slot == "top" || o.slot == "bottom")) ||
                    (o.slot == "overall" && (it.slot == "top" || it.slot == "bottom"))
                if (clash) {
                    worn.remove(o.key)
                    if (o.builtin) CuteChar.enqueueMod(o.key, null, null, false)
                }
            }
            worn.add(it.key)
            if (it.builtin) Thread { load(it) }.start()
        }
        saveIndex()
    }

    @Synchronized
    fun remove(it: Item) {
        if (it.builtin) return
        worn.remove(it.key)
        items.remove(it)
        val d = dir
        if (d != null) { File(d, it.id + ".cup").delete(); File(d, it.id + ".png").delete(); File(d, it.id + ".t0.thumb.png").delete(); File(d, it.id + ".t1.thumb.png").delete() }
        saveIndex()
        CuteChar.enqueueMod(it.key, null, null, false)
    }

    /** Manda todas as peças para a GL (ao iniciar ou quando o contexto GL é recriado). */
    fun requeue() {
        val list = synchronized(this) { items.filter { !it.builtin || it.key in worn } }
        if (list.isEmpty()) return
        Thread { for (it in list) load(it) }.start()
    }

    private fun load(it: Item) {
        val d = dir ?: return
        try {
            val opts = BitmapFactory.Options()
            opts.inPremultiplied = false
            var cup: ByteArray
            val bmp: Bitmap
            if (it.builtin) {
                val am = CuteChar.assets ?: return
                // peças de modelo único: malha e textura da cor escolhida
                val vr = VARS[it.id]
                val slug = vr?.colors?.get(variantIndex(it.id))?.slug
                val cupName = if (vr != null && slug != null) vr.cupOf(slug) else it.id
                val pngName = if (vr != null && slug != null) vr.pngOf(slug) else it.id
                cup = am.open("cute/skate/" + cupName + ".cup").use { s -> s.readBytes() }
                bmp = am.open("cute/skate/" + pngName + ".png").use { s -> BitmapFactory.decodeStream(s, null, opts) } ?: return
            } else {
                cup = File(d, it.id + ".cup").readBytes()
                bmp = BitmapFactory.decodeFile(File(d, it.id + ".png").path, opts) ?: return
            }
            val colorVar = VARS[it.id]
            if (it.id.startsWith("ross1_") && colorVar != null) {
                val tinted = tintBitmap(bmp, colorVar.colors[variantIndex(it.id)].argb)
                if (tinted !== bmp && !bmp.isRecycled) bmp.recycle()
                // A malha é a mesma; somente a textura recebe a cor selecionada.
                CuteChar.enqueueMod(it.key, cup, tinted, it.alpha)
                return
            }
            if (it.game == 2 && it.hasTex) {
                val px = IntArray(bmp.width * bmp.height)
                bmp.getPixels(px, 0, bmp.width, 0, 0, bmp.width, bmp.height)
                cup = Importer.cullBlack(cup, px, bmp.width, bmp.height)
            }
            CuteChar.enqueueMod(it.key, cup, bmp, it.alpha)
        } catch (e: Throwable) {
            android.util.Log.e("ModStore", "falhou ao carregar " + it.id, e)
        }
    }

    /** .package vira ele mesmo; .zip e .rar viram os .package de dentro. */
    private fun expand(ctx: Context, name: String, raw: ByteArray): List<Pair<String, ByteArray>> {
        val res = ArrayList<Pair<String, ByteArray>>()
        if (raw.size >= 4 && raw[0] == 'D'.code.toByte() && raw[1] == 'B'.code.toByte() && raw[2] == 'P'.code.toByte() && raw[3] == 'F'.code.toByte()) {
            res.add(name to raw)
        } else if (raw.size >= 4 && raw[0] == 'P'.code.toByte() && raw[1] == 'K'.code.toByte()) {
            java.util.zip.ZipInputStream(java.io.ByteArrayInputStream(raw)).use { z ->
                while (true) {
                    val e = z.nextEntry ?: break
                    if (!e.isDirectory && e.name.endsWith(".package", true)) res.add(e.name to z.readBytes())
                }
            }
        } else if (raw.size >= 4 && raw[0] == 'R'.code.toByte() && raw[1] == 'a'.code.toByte() && raw[2] == 'r'.code.toByte()) {
            val tmp = File(ctx.cacheDir, "rar_" + System.nanoTime())
            tmp.mkdirs()
            try {
                com.github.junrar.Junrar.extract(java.io.ByteArrayInputStream(raw), tmp)
                tmp.walkTopDown().filter { it.isFile && it.name.endsWith(".package", true) }.forEach { res.add(it.name to it.readBytes()) }
            } catch (e: Throwable) {
                throw Exception("Não consegui abrir o RAR (formato novo?). Extraia no celular e escolha o .package.")
            } finally {
                tmp.deleteRecursively()
            }
        } else {
            throw Exception("Arquivo não reconhecido (esperava .package, .zip ou .rar).")
        }
        return res
    }

    private fun displayName(ctx: Context, u: Uri): String {
        try {
            ctx.contentResolver.query(u, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { c ->
                if (c.moveToFirst()) return c.getString(0) ?: "mod"
            }
        } catch (e: Throwable) {
        }
        return u.lastPathSegment ?: "mod"
    }

    /**
     * Importa os arquivos escolhidos (em segundo plano). [target] = id de uma peça que deve receber a textura de um package só de cor.
     * [done] recebe a mensagem final (thread de fundo: quem chama troca para a thread da tela).
     */
    fun importAsync(ctx: Context, uris: List<Uri>, target: String?, done: (String) -> Unit) {
        if (busy) { done("Ainda importando, espere um pouco."); return }
        busy = true
        val app = ctx.applicationContext
        Thread {
            val msgs = ArrayList<String>()
            try {
                val body = CuteChar.bodyRef()
                if (body == null) {
                    msgs.add("Escolha primeiro um corpo na aba Base (o importador encaixa a roupa no corpo atual).")
                } else {
                    val grp = CuteChar.bodyGroup() ?: "af"
                    // expande .zip e .rar em arquivos .package
                    val entries = ArrayList<Pair<String, ByteArray>>()
                    for (u in uris) {
                        val un = displayName(app, u)
                        try {
                            val raw = app.contentResolver.openInputStream(u)!!.use { it.readBytes() }
                            val got = expand(app, un, raw)
                            if (got.isEmpty()) msgs.add("$un: não achei nenhum .package dentro.")
                            entries.addAll(got)
                        } catch (e: Throwable) {
                            android.util.Log.e("ModStore", "abrir $un", e)
                            msgs.add("$un: ${e.message ?: e.toString()}")
                        }
                    }
                    for ((nm, data) in entries) {
                        try {
                            val out = Importer.convert(data, nm, body)
                            val tx = out.texOnly
                            if (tx != null) {
                                val tgt = synchronized(this) { items.firstOrNull { x -> x.id == target } ?: items.lastOrNull { x -> !x.hasTex && x.grp == grp } ?: items.lastOrNull { x -> x.grp == grp } }
                                if (tgt == null) msgs.add("$nm: " + out.notes.joinToString(" "))
                                else {
                                    setTexture(tgt, (if (tgt.alpha) tx else tx.opaque()).png())
                                    msgs.add("$nm: textura aplicada em ${tgt.name}.")
                                }
                            } else {
                                for (p in out.pieces) {
                                    val id = java.lang.Long.toHexString(System.nanoTime() xor (System.currentTimeMillis() shl 20)).takeLast(8)
                                    val d = dir!!
                                    File(d, "$id.cup").writeBytes(p.cup)
                                    File(d, "$id.png").writeBytes(p.png)
                                    val itm = Item(id, p.name, p.slot, grp, p.game, p.hasTex, p.alpha)
                                    synchronized(this) { items.add(itm); saveIndex() }
                                    load(itm)
                                    msgs.add("$nm: ${SLOT_NAMES[p.slot] ?: p.slot} importado" + if (!p.hasTex) " (sem textura: importe o package de cor)" else "")
                                }
                            }
                        } catch (e: Throwable) {
                            android.util.Log.e("ModStore", "importar $nm", e)
                            msgs.add("$nm: ${e.message ?: e.toString()}")
                        }
                    }
                }
            } catch (e: Throwable) {
                msgs.add("Erro: ${e.message ?: e.toString()}")
            } finally {
                busy = false
            }
            done(msgs.joinToString("\n"))
        }.start()
    }

    private fun setTexture(it: Item, png: ByteArray) {
        val d = dir ?: return
        File(d, it.id + ".png").writeBytes(png)
        synchronized(this) { it.hasTex = true; saveIndex() }
        load(it)
    }
}

// Build acionado apos a inclusao dos quatro cabelos Ross convertidos em assets.
