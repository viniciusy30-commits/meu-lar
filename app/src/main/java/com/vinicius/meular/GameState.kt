package com.vinicius.meular

import android.content.Context
import java.util.concurrent.CopyOnWriteArrayList
import kotlin.math.floor

// Posição fina: os móveis andam de 25 em 25 cm, e não de metro em metro.
fun snapQ(v: Float): Float = Math.round(v * 4f) / 4f

/** cat: 0 Sala, 1 Quarto, 2 Cozinha, 3 Decoração, 4 Externo (só aparece na sala de testes) */
enum class Type(val nome: String, val w: Int, val h: Int, val preco: Int, val alt: Float, val cat: Int, val rug: Boolean = false, val fl: String? = null,
                /** Etapa 83: modelo da biblioteca 3D (assets/obj3d/<glb>.glb) */ val glb: String? = null,
                /** Etapa 83: objeto solto com física (caixa, bola...) */ val dyn: Boolean = false) {
    X_OAK_A("Carvalho", 6, 6, 0, 5.6f, 4, fl = "oak_a"),
    X_OAK_B("Bordo", 7, 7, 0, 5.6f, 4, fl = "oak_b"),
    X_CHERRY("Cerejeira", 6, 6, 0, 4.8f, 4, fl = "cherry_a"),
    X_PINE("Pinheiro", 4, 4, 0, 4.8f, 4, fl = "pine_a"),
    X_BUSH_A("Arbusto folhudo", 2, 2, 0, 1.0f, 4, fl = "bush_a"),
    X_BUSH_B("Arbusto de bordo", 2, 2, 0, 1.1f, 4, fl = "bush_b"),
    X_BUSH_PINK("Arbusto rosa", 2, 2, 0, 1.1f, 4, fl = "bush_pink"),
    X_BUSH_WHITE("Arbusto branco", 2, 2, 0, 0.9f, 4, fl = "bush_white"),
    X_HEDGE("Cerca-viva", 3, 2, 0, 1.2f, 4, fl = "hedge"),
    X_FL_DAISY("Margaridas", 1, 1, 0, 0.5f, 4, fl = "fl_daisy"),
    X_FL_TULIP("Tulipas", 1, 1, 0, 0.5f, 4, fl = "fl_tulip"),
    X_FL_LAV("Lavanda", 1, 1, 0, 0.5f, 4, fl = "fl_lav"),
    X_FL_POPPY("Papoulas", 1, 1, 0, 0.45f, 4, fl = "fl_poppy"),
    X_FL_YELLOW("Flores amarelas", 1, 1, 0, 0.5f, 4, fl = "fl_yellow"),
    // Protótipos da biblioteca 3D (Etapa 0/83), revisados pelas regras v4: vaso, caixa e bola com física, poltrona e aparador
    G_POLTRONA("Poltrona de linho", 1, 1, 0, 0.77f, 0, glb = "int_poltrona"),
    G_APARADOR("Aparador de carvalho", 2, 1, 0, 0.66f, 0, glb = "int_aparador"),
    G_VASO("Vaso com costela-de-adão", 1, 1, 0, 0.78f, 3, glb = "decor_vaso_costela"),
    G_CAIXA("Caixa de papelão", 1, 1, 0, 0.30f, 3, glb = "fis_caixa_papelao", dyn = true),
    G_BOLA("Bola de borracha", 1, 1, 0, 0.22f, 3, glb = "fis_bola", dyn = true),
    // Etapa 87: o jogo só tem o que vem do Plano Mestre (os móveis anteriores ao PDF foram retirados; saves antigos ignoram esses itens).
    // ETAPA 1 do Plano Mestre: cadeira, mesa e armário com porta e gaveta
    G_CADEIRA("Cadeira de jantar", 1, 1, 0, 0.78f, 2, glb = "int_cadeira_jantar"),
    G_MESA("Mesa de jantar", 2, 1, 0, 0.60f, 2, glb = "int_mesa_jantar"),
    G_GUARDA_ROUPA("Guarda-roupa", 2, 1, 0, 1.64f, 1, glb = "int_guarda_roupa"),
    // ETAPA 2 do Plano Mestre: cama, sofá, geladeira, fogão e pia (refeitos pelas fichas e pelas regras v4)
    G_SOFA3("Sofá de 3 lugares", 2, 1, 0, 0.76f, 0, glb = "int_sofa3"),
    G_CAMA("Cama de casal", 2, 2, 0, 0.97f, 1, glb = "int_cama_casal"),
    G_GELADEIRA("Geladeira duplex", 1, 1, 0, 1.51f, 2, glb = "int_geladeira"),
    G_FOGAO("Fogão 4 bocas com forno", 1, 1, 0, 0.84f, 2, glb = "int_fogao"),
    G_PIA("Pia com gabinete", 1, 1, 0, 1.05f, 2, glb = "int_pia")
}

class Item(val type: Type, var x: Int, var y: Int, var rot: Int = 0) {
    var born = 0L
    // Deslocamento fino (metros) somado à casa (x, y).
    var ox = 0f
    var oz = 0f
    val w: Int get() = if (rot % 2 == 1) type.h else type.w
    val h: Int get() = if (rot % 2 == 1) type.w else type.h

    // Retângulo que o móvel ocupa de verdade no mundo: [x0, z0, x1, z1].
    fun rect(): FloatArray = Foot.rect(type, rot, x, y, ox, oz)

    // ---- Etapa 83: estado dos objetos da biblioteca 3D
    /** estado gravado da física (posição/rotação do corpo), "" = nenhum */
    var st: String = ""
    /** corpo rígido (só itens com type.dyn), criado pela física */
    var body: Body? = null
    /** progresso atual (0..1) e alvo (0 ou 1) de cada peça animada do GLB (mesma ordem de GModel.animated) */
    var animCur: FloatArray? = null
    var animTgt: FloatArray? = null
    /** limite de abertura (0..1) de cada peça, calculado ao abrir (parede ou móvel na frente) */
    var animLim: FloatArray? = null
    /** ocupado (alguém sentado) */
    var busy = false
    /** Etapa 87: lugares ocupados (IP_sentar_N / IP_deitar_E...): o sofá e a cama têm ocupação por lugar/lado */
    val occ = HashSet<String>()
    /** Etapa 87: lado da cama em que o personagem está dormindo ("" = ninguém); gravado no save */
    var sleep = ""
    /** Lote 2: aparelho ligado (fogão aceso, torneira aberta) */
    var on = false

    fun encodeState(): String {
        val sb = StringBuilder(st)
        animTgt?.let { a -> if (a.isNotEmpty()) { if (sb.isNotEmpty()) sb.append('~'); sb.append("a="); sb.append(a.joinToString(":") { if (it > 0.5f) "1" else "0" }) } }
        if (on) { if (sb.isNotEmpty()) sb.append('~'); sb.append("on=1") }
        if (sleep.isNotEmpty()) { if (sb.isNotEmpty()) sb.append('~'); sb.append("sono="); sb.append(sleep) }
        return sb.toString()
    }

    fun decodeState(s: String) {
        val keep = ArrayList<String>()
        for (kv in s.split('~')) {
            if (kv.startsWith("a=")) {
                val v = kv.substring(2).split(':').map { if (it == "1") 1f else 0f }.toFloatArray()
                animTgt = v; animCur = v.copyOf()
            } else if (kv == "on=1") on = true
            else if (kv.startsWith("sono=")) sleep = kv.substring(5)
            else if (kv.isNotEmpty()) keep.add(kv)
        }
        st = keep.joinToString("~")
    }
}

class GameState(ctx: Context) {
    private val prefs = ctx.getSharedPreferences("meular", Context.MODE_PRIVATE)
    /** Dinheiro infinito (o trabalho saiu do jogo): sempre alto; gastar e ganhar não mudam o valor. */
    var money: Int
        get() = 999_999_999
        set(_) {}
    var gw = 6
    var gh = 5
    var floorIdx = 0
    var wallIdx = 0
    var ownFloors = 1
    var ownWalls = 1
    var sens = 1
    var avatar = Avatar()
    var avatarSet = false
    val items = CopyOnWriteArrayList<Item>()

    // Etapa 70: sala de testes. Guarda a casa de verdade, mostra uma sala grande com tudo do jogo e não grava nada enquanto está ligada.
    var testRoom = false
        private set
    private var bkMoney = 0; private var bkGw = 6; private var bkGh = 5; private var bkFloor = 0; private var bkWall = 0
    private val bkItems = ArrayList<Item>()

    fun enterTest() {
        if (testRoom) return
        bkMoney = money; bkGw = gw; bkGh = gh; bkFloor = floorIdx; bkWall = wallIdx
        bkItems.clear(); bkItems.addAll(items)
        testRoom = true
        items.clear()
        gw = 26; gh = 30
        // Etapa 87: plantas e árvores (cat 4) ficam do lado de fora da casa, no quintal (Models.yard com vitrine); dentro só os móveis do PDF
        val list = Type.values().filter { it.cat != 4 }.sortedBy { it.cat }
        var cx = 0.4f; var cz = 0.4f; var rowH = 0f
        var lastCat = -1
        for (t in list) {
            val b = Foot.box(t)
            val big = t.cat == 4
            val iw = if (big) t.w.toFloat() else (b[2] - b[0]) + 0.35f
            val ih = if (big) t.h.toFloat() else (b[3] - b[1]) + 0.35f
            if (t.cat != lastCat && lastCat != -1 && t.cat == 4) { cx = 0.4f; cz += rowH; rowH = 0f }
            lastCat = t.cat
            if (cx + iw > gw - 0.2f) { cx = 0.4f; cz += rowH; rowH = 0f }
            val it = Item(t, 0, 0)
            // posição do canto da área w x h; o corpo fica centrado nela
            val tx = cx + (if (big) 0f else -b[0] + 0.1f)
            val tz = cz + (if (big) 0f else -b[1] + 0.1f)
            val p = placeAt(it, 0, tx, tz)
            if (p != null) {
                it.x = p[0].toInt(); it.y = p[1].toInt(); it.ox = p[2]; it.oz = p[3]
                items.add(it)
            }
            cx += iw
            if (ih > rowH) rowH = ih
        }
    }

    fun exitTest() {
        if (!testRoom) return
        testRoom = false
        money = bkMoney; gw = bkGw; gh = bkGh; floorIdx = bkFloor; wallIdx = bkWall
        items.clear(); items.addAll(bkItems); bkItems.clear()
    }

    init {
        floorIdx = prefs.getInt("floor", 0).coerceIn(0, Finish.floors.size - 1)
        wallIdx = prefs.getInt("wall", 0).coerceIn(0, Finish.walls.size - 1)
        ownFloors = prefs.getInt("ownF", 1) or 1
        ownWalls = prefs.getInt("ownW", 1) or 1
        sens = prefs.getInt("sens", 1).coerceIn(0, 2)
        Avatar.decode(prefs.getString("avatar", null))?.let { avatar = it; avatarSet = true }
        CuteColor.setColors(avatar.cc)
        CuteChar.setWear(avatar.wearKeys())
        CuteChar.setShape(avatar.bs, avatar.fs, avatar.masc, avatar.ss)
        val raw = prefs.getString("state", null)
        var ok = false
        if (raw != null) {
            try {
                val parts = raw.split("|")
                money = parts[0].toInt(); gw = parts[1].toInt(); gh = parts[2].toInt()
                if (parts.size > 3 && parts[3].isNotEmpty()) {
                    for (s in parts[3].split(";")) {
                        val f = s.split(",")
                        // móveis que não existem mais (pacote antigo) são ignorados em vez de derrubar o save
                        val tp = try { Type.valueOf(f[0]) } catch (e: Exception) { continue }
                        val novo = Item(tp, f[1].toInt(), f[2].toInt(), f[3].toInt() % 4)
                        if (f.size > 5) { novo.ox = f[4].toInt() / 100f; novo.oz = f[5].toInt() / 100f }
                        if (f.size > 6) novo.decodeState(f[6])
                        items.add(novo)
                    }
                }
                ok = true
            } catch (e: Exception) {
                items.clear(); money = 50; gw = 6; gh = 5
            }
        }
        if (!ok) {
            // casa inicial só com móveis do Plano Mestre: cama de casal, mesa de jantar e duas cadeiras viradas para a mesa
            items.add(Item(Type.G_CAMA, 0, 0))
            items.add(Item(Type.G_MESA, 3, 3))
            items.add(Item(Type.G_CADEIRA, 3, 2))
            items.add(Item(Type.G_CADEIRA, 4, 2))
            save()
        }
    }

    fun nivelCasa(): Int = gw - 5

    fun precoAmpliar(): Int = 200 * nivelCasa()

    fun podeAmpliar(): Boolean = gw < 10

    // Cabe aqui? Usa o tamanho real do móvel (não a casa inteira): dois móveis só colidem se os corpos se encostam.
    fun canPlace(item: Item, nx: Int, ny: Int, rot: Int, ox: Float = item.ox, oz: Float = item.oz): Boolean {
        val r = Foot.rect(item.type, rot, nx, ny, ox, oz)
        if (r[0] < -0.001f || r[1] < -0.001f || r[2] > gw + 0.001f || r[3] > gh + 0.001f) return false
        if (item.type.rug || item.type.dyn) return true      // objeto solto: a física resolve onde ele fica
        val mine = Foot.blockRects(item.type, rot, nx, ny, ox, oz) ?: listOf(r)
        return items.none { o ->
            if (o === item || o.type.rug || o.type.dyn) return@none false
            // Etapa 86: com colisores separados (pernas da mesa), a cadeira pode entrar embaixo do tampo
            val theirs = Foot.blockRects(o.type, o.rot, o.x, o.y, o.ox, o.oz) ?: listOf(o.rect())
            mine.any { a -> theirs.any { b -> a[0] < b[2] - 0.01f && a[2] > b[0] + 0.01f && a[1] < b[3] - 0.01f && a[3] > b[1] + 0.01f } }
        }
    }

    // Tenta pôr o móvel com o canto (tx, tz) em metros, empurrando-o para dentro da casa se passar da parede.
    // Devolve [x, y, ox, oz] ou null se bater em outro móvel.
    fun placeAt(item: Item, rot: Int, tx0: Float, tz0: Float): FloatArray? {
        var tx = tx0
        var tz = tz0
        val r = Foot.rect(item.type, rot, floor(tx).toInt(), floor(tz).toInt(), tx - floor(tx), tz - floor(tz))
        if (r[0] < 0f) tx -= r[0]
        if (r[2] > gw) tx -= r[2] - gw
        if (r[1] < 0f) tz -= r[1]
        if (r[3] > gh) tz -= r[3] - gh
        val nx = floor(tx).toInt()
        val nz = floor(tz).toInt()
        val ox = tx - nx
        val oz = tz - nz
        if (!canPlace(item, nx, nz, rot, ox, oz)) return null
        return floatArrayOf(nx.toFloat(), nz.toFloat(), ox, oz)
    }

    fun rotate(item: Item): Boolean {
        val nr = (item.rot + 1) % 4
        val nw = if (nr % 2 == 1) item.type.h else item.type.w
        val nh = if (nr % 2 == 1) item.type.w else item.type.h
        // gira em volta do centro, sem o móvel andar
        val cx = item.x + item.ox + item.w / 2f
        val cz = item.y + item.oz + item.h / 2f
        val p = placeAt(item, nr, cx - nw / 2f, cz - nh / 2f) ?: return false
        item.x = p[0].toInt(); item.y = p[1].toInt(); item.ox = p[2]; item.oz = p[3]; item.rot = nr
        return true
    }

    // Primeiro lugar livre mais perto de (fx, fz), de 25 em 25 cm. Devolve [x, y, ox, oz] ou null.
    fun findPlaceNear(t: Type, fx: Float, fz: Float): FloatArray? {
        val probe = Item(t, 0, 0)
        var best: FloatArray? = null
        var bd = Float.MAX_VALUE
        var tz = -t.h.toFloat()
        while (tz <= gh) {
            var tx = -t.w.toFloat()
            while (tx <= gw) {
                val p = placeAt(probe, 0, tx, tz)
                if (p != null) {
                    val dx = p[0] + p[2] + t.w / 2f - fx
                    val dz = p[1] + p[3] + t.h / 2f - fz
                    val d = dx * dx + dz * dz
                    if (d < bd) { bd = d; best = p }
                }
                tx += 0.25f
            }
            tz += 0.25f
        }
        return best
    }

    fun findSpot(t: Type): Pair<Int, Int>? = findSpotNear(t, 0f, 0f)

    /** Primeiro lugar livre mais próximo do ponto (fx, fz) em coordenadas de mundo. */
    fun findSpotNear(t: Type, fx: Float, fz: Float): Pair<Int, Int>? {
        val probe = Item(t, 0, 0)
        var best: Pair<Int, Int>? = null
        var bd = Float.MAX_VALUE
        for (y in 0 until gh) for (x in 0 until gw) {
            if (!canPlace(probe, x, y, 0)) continue
            val dx = x + t.w / 2f - fx
            val dz = y + t.h / 2f - fz
            val d = dx * dx + dz * dz
            if (d < bd) { bd = d; best = Pair(x, y) }
        }
        return best
    }

    fun save() {
        if (testRoom) return
        val s = items.joinToString(";") { "${it.type.name},${it.x},${it.y},${it.rot},${Math.round(it.ox * 100f)},${Math.round(it.oz * 100f)},${it.encodeState()}" }
        prefs.edit()
            .putString("state", "$money|$gw|$gh|$s")
            .putInt("floor", floorIdx).putInt("wall", wallIdx)
            .putInt("ownF", ownFloors).putInt("ownW", ownWalls)
            .putInt("sens", sens)
            .putString("avatar", avatar.encode())
            .apply()
    }
}
