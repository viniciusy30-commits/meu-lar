package com.vinicius.meular

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.provider.OpenableColumns
import com.vinicius.meular.mods.Importer
import java.io.File

/**
 * Roupas e cabelos importados de arquivos .package (The Sims 2, 3 e 4), direto pelo jogo.
 * Cada peça fica em filesDir/mods: <id>.cup (malha já encaixada no corpo), <id>.png (textura), index.txt e worn.txt.
 */
object ModStore {
    class Item(val id: String, var name: String, val slot: String, val grp: String, val game: Int, var hasTex: Boolean, val alpha: Boolean, val builtin: Boolean = false) {
        val key: String get() = "$slot/M_$id"
    }

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
                if (f.size >= 7 && File(d, f[0] + ".cup").exists())
                    items.add(Item(f[0], f[1], f[2], f[3], f[4].toIntOrNull() ?: 3, f[5] == "1", f[6] == "1"))
            }
            File(d, "worn.txt").takeIf { it.exists() }?.readText()?.split(',')?.forEach { if (it.isNotBlank()) worn.add(it.trim()) }
        } catch (e: Throwable) {
            android.util.Log.e("ModStore", "índice ilegível", e)
        }
        // roupas que já vêm no jogo (assets/cute/skate): camiseta oversized CHAOS, calça cargo baggy e tênis preto e branco
        for (g in listOf("af", "am", "tf", "tm", "ef", "em")) {
            items.add(Item("tee_$g", "Camiseta CHAOS", "top", g, 0, true, false, true))
            items.add(Item("jacket_$g", "Jaqueta jeans preta", "jacket", g, 0, true, false, true))
            items.add(Item("cargo_$g", "Cargo baggy preta", "bottom", g, 0, true, false, true))
            items.add(Item("shoe_$g", "Jordan preto e branco", "feet", g, 0, true, false, true))
            items.add(Item("hair_$g", "Wolf cut preto", "hairBack", g, 0, true, true, true))
        }
        // regata baggy do pacote "Baggy Singlet Set" (Mod The Sims, ArthurGoring), já convertida: corpos masculinos jovem/adulto/idoso
        for (g in listOf("am", "tm", "em")) {
            items.add(Item("singlet_white_$g", "Regata baggy branca", "top", g, 0, true, true, true))
            items.add(Item("singlet_black_$g", "Regata baggy preta", "top", g, 0, true, true, true))
            items.add(Item("singlet_love_$g", "Regata love you (preta)", "top", g, 0, true, true, true))
            items.add(Item("singlet_haters_$g", "Regata haters (preta)", "top", g, 0, true, true, true))
        }
        worn.retainAll(items.map { it.key }.toSet())
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
    fun assetThumb(name: String): Bitmap? = try {
        CuteChar.assets?.open("cute/thumbs/$name.png")?.use { BitmapFactory.decodeStream(it) }
    } catch (e: Throwable) { null }

    /** Miniatura da peça: embutida, ou gerada na primeira vez (peças importadas) e guardada em disco. Chamar fora da thread da tela. */
    fun thumb(it: Item): Bitmap? {
        if (it.builtin) return assetThumb(it.id)
        val d = dir ?: return null
        val f = File(d, it.id + (if (it.hasTex) ".t1" else ".t0") + ".thumb.png")
        if (f.exists()) BitmapFactory.decodeFile(f.path)?.let { b -> return b }
        val b = try { renderThumb(it) } catch (e: Throwable) { android.util.Log.e("ModStore", "miniatura " + it.id, e); null } ?: return null
        try { f.outputStream().use { o -> b.compress(Bitmap.CompressFormat.PNG, 100, o) } } catch (e: Throwable) { }
        return b
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
                    val bm = Thumb.parse(am.open("cute/p_body_" + it.grp + "1.bin").use { s -> s.readBytes() })
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
    fun wornKeys(grp: String): List<String> = items.filter { it.key in worn && it.grp == grp }.map { it.key }

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
                cup = am.open("cute/skate/" + it.id + ".cup").use { s -> s.readBytes() }
                bmp = am.open("cute/skate/" + it.id + ".png").use { s -> BitmapFactory.decodeStream(s, null, opts) } ?: return
            } else {
                cup = File(d, it.id + ".cup").readBytes()
                bmp = BitmapFactory.decodeFile(File(d, it.id + ".png").path, opts) ?: return
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
