package com.vinicius.meular

import android.content.Context
import java.util.concurrent.CopyOnWriteArrayList

/** cat: 0 Sala, 1 Quarto, 2 Cozinha, 3 Decoração */
enum class Type(val nome: String, val w: Int, val h: Int, val preco: Int, val alt: Float, val cat: Int, val mob: String? = null, val rug: Boolean = false) {
    CHAIR("Cadeira", 1, 1, 20, 1.0f, 2),
    TABLE("Mesa de jantar", 2, 1, 60, 1.25f, 2),
    BED("Cama", 1, 2, 120, 1.1f, 1),
    SOFA("Sofá", 2, 1, 150, 1.05f, 0),
    SHELF("Estante", 2, 1, 100, 1.9f, 0),
    PLANT("Planta", 1, 1, 30, 1.5f, 3),
    RUG("Tapete", 2, 2, 40, 0.07f, 3),
    TV("TV com rack", 2, 1, 250, 1.4f, 0),
    FRIDGE("Geladeira", 1, 1, 300, 1.9f, 2),
    STOVE("Fogão", 1, 1, 220, 1.2f, 2),
    LAMP("Abajur de chão", 1, 1, 35, 1.6f, 3),
    NIGHT("Criado-mudo", 1, 1, 45, 0.9f, 1),
    COFFEE("Mesa de centro", 2, 1, 70, 0.55f, 0),
    WARDROBE("Guarda-roupa", 2, 1, 180, 2.1f, 1),
    // Pack "home-set-2020s": modelos 3D originais em assets/mob/<mob>.bin (ferramentas/moveis)
    MOB_SOFA01("Sofá de canto", 5, 3, 260, 1.20f, 0, mob = "sofa01"),
    MOB_SOFA02("Sofá baixo", 5, 3, 220, 1.07f, 0, mob = "sofa02"),
    MOB_CASUAL_CHAIR01("Poltrona", 1, 2, 110, 1.00f, 0, mob = "casual-chair01"),
    MOB_COFFEE_TABLE01("Mesa de centro redonda", 2, 2, 80, 0.61f, 0, mob = "coffee-table01"),
    MOB_COFFEE_TABLE02("Mesa de centro baixa", 2, 1, 70, 0.60f, 0, mob = "coffee-table02"),
    MOB_CABINET01("Aparador", 3, 1, 160, 0.82f, 0, mob = "cabinet01"),
    MOB_SHELF01("Estante aberta", 2, 1, 120, 2.02f, 0, mob = "shelf01"),
    MOB_STOOL01("Pufe azul", 1, 1, 35, 0.55f, 0, mob = "stool01"),
    MOB_STOOL02("Banqueta", 1, 1, 40, 0.46f, 0, mob = "stool02"),
    MOB_SMALL_CUSHION01("Almofada grande", 1, 1, 15, 0.82f, 0, mob = "small-cushion01"),
    MOB_SMALL_CUSHION02("Almofada comprida", 1, 1, 15, 0.39f, 0, mob = "small-cushion02"),
    MOB_SPEAKER01("Caixa de som", 1, 1, 45, 0.20f, 0, mob = "speaker01"),
    MOB_OFFICE_DESK01("Escrivaninha", 3, 2, 130, 0.94f, 1, mob = "office-desk01"),
    MOB_OFFICE_CHAIR01("Cadeira de escritório", 1, 1, 140, 1.50f, 1, mob = "office-chair01"),
    MOB_COMPUTER_CASE("Gabinete de PC", 1, 1, 90, 0.31f, 1, mob = "computer-case"),
    MOB_MONITOR01("Monitor curvo", 1, 1, 180, 0.66f, 1, mob = "monitor01"),
    MOB_KEYBOARD01("Teclado", 1, 1, 30, 0.10f, 1, mob = "keyboard01"),
    MOB_COMPUTER_MOUSE("Mouse", 1, 1, 15, 0.10f, 1, mob = "computer-mouse"),
    MOB_MOUSE_PAD01("Mousepad grande", 1, 1, 15, 0.10f, 1, mob = "mouse_pad01", rug = true),
    MOB_DESK_LAMP01("Luminária articulada", 1, 1, 40, 0.79f, 1, mob = "desk-lamp01"),
    MOB_DESK_LAMP02("Luminária de mesa", 1, 1, 30, 0.37f, 1, mob = "desk-lamp02"),
    MOB_CLOCK01("Relógio de mesa", 1, 1, 20, 0.12f, 1, mob = "clock01"),
    MOB_BASKET01("Cesto de vime", 1, 1, 25, 0.26f, 2, mob = "basket01"),
    MOB_BIN("Lixeira", 1, 1, 20, 0.58f, 2, mob = "bin"),
    MOB_STORAGE_BOX01("Caixa organizadora", 1, 1, 18, 0.19f, 2, mob = "storage-box01"),
    MOB_TRAY01("Bandeja de madeira", 1, 1, 15, 0.10f, 2, mob = "tray01"),
    MOB_TISSUE_BOX("Caixa de lenços", 1, 1, 8, 0.18f, 2, mob = "tissue-box"),
    MOB_CARPET01("Tapete longo 1", 5, 2, 60, 0.10f, 3, mob = "carpet01", rug = true),
    MOB_CARPET02("Tapete longo 2", 5, 2, 60, 0.10f, 3, mob = "carpet02", rug = true),
    MOB_CARPET03("Tapete redondo 1", 2, 2, 45, 0.10f, 3, mob = "carpet03", rug = true),
    MOB_CARPET04("Tapete redondo 2", 2, 2, 45, 0.10f, 3, mob = "carpet04", rug = true),
    MOB_INDOOR_PLANT01("Planta grande", 1, 2, 70, 2.33f, 3, mob = "indoor-plant01"),
    MOB_POT_CACTUS("Cacto", 1, 1, 15, 0.22f, 3, mob = "pot-cactus"),
    MOB_VASE01("Vaso de vime", 1, 1, 18, 0.15f, 3, mob = "vase01"),
    MOB_VASE02("Vaso de argila", 1, 1, 18, 0.24f, 3, mob = "vase02"),
    MOB_VASE03("Vaso com folhas", 1, 1, 30, 0.55f, 3, mob = "vase03"),
    MOB_VASE04("Vaso baixo", 1, 1, 12, 0.10f, 3, mob = "vase04"),
    MOB_VASE05("Vaso fino", 1, 1, 14, 0.34f, 3, mob = "vase05"),
    MOB_BOOK01("Livro", 1, 1, 8, 0.36f, 3, mob = "book01"),
    MOB_BOOK02("Livro pequeno", 1, 1, 8, 0.25f, 3, mob = "book02"),
    MOB_BOOKS01("Pilha de livros", 1, 1, 14, 0.29f, 3, mob = "books01"),
    MOB_BOOKS02("Livros deitados", 1, 1, 14, 0.26f, 3, mob = "books02"),
    MOB_BOOKS03("Livros em pé", 1, 1, 16, 0.30f, 3, mob = "books03"),
    MOB_SCULPTURE01("Escultura", 1, 1, 55, 0.32f, 3, mob = "sculpture01"),
    MOB_TRINKET_ABS("Letreiro ABS", 1, 1, 25, 0.19f, 3, mob = "trinket-abs"),
    MOB_TRINKET_DUCK("Patinho amarelo", 1, 1, 12, 0.13f, 3, mob = "trinket-duck"),
    MOB_TRINKET_WOODEN_BALL("Bola de madeira", 1, 1, 10, 0.15f, 3, mob = "trinket_wooden_ball"),
    MOB_PHOTO_FRAME01("Porta-retrato largo", 1, 1, 12, 0.16f, 3, mob = "photo-frame01"),
    MOB_PHOTO_FRAME02("Porta-retrato alto", 1, 1, 12, 0.24f, 3, mob = "photo-frame02")
}

class Item(val type: Type, var x: Int, var y: Int, var rot: Int = 0) {
    var born = 0L
    val w: Int get() = if (rot % 2 == 1) type.h else type.w
    val h: Int get() = if (rot % 2 == 1) type.w else type.h
}

class GameState(ctx: Context) {
    private val prefs = ctx.getSharedPreferences("meular", Context.MODE_PRIVATE)
    var money = 50
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

    init {
        floorIdx = prefs.getInt("floor", 0).coerceIn(0, Finish.floors.size - 1)
        wallIdx = prefs.getInt("wall", 0).coerceIn(0, Finish.walls.size - 1)
        ownFloors = prefs.getInt("ownF", 1) or 1
        ownWalls = prefs.getInt("ownW", 1) or 1
        sens = prefs.getInt("sens", 1).coerceIn(0, 2)
        Avatar.decode(prefs.getString("avatar", null))?.let { avatar = it; avatarSet = true }
        CuteColor.setColors(avatar.cc)
        CuteChar.setWear(avatar.wearKeys())
        CuteChar.setShape(avatar.bs, avatar.fs, avatar.masc)
        val raw = prefs.getString("state", null)
        var ok = false
        if (raw != null) {
            try {
                val parts = raw.split("|")
                money = parts[0].toInt(); gw = parts[1].toInt(); gh = parts[2].toInt()
                if (parts.size > 3 && parts[3].isNotEmpty()) {
                    for (s in parts[3].split(";")) {
                        val f = s.split(",")
                        items.add(Item(Type.valueOf(f[0]), f[1].toInt(), f[2].toInt(), f[3].toInt() % 4))
                    }
                }
                ok = true
            } catch (e: Exception) {
                items.clear(); money = 50; gw = 6; gh = 5
            }
        }
        if (!ok) {
            items.add(Item(Type.BED, 0, 0))
            items.add(Item(Type.TABLE, 3, 2))
            items.add(Item(Type.CHAIR, 2, 2))
            save()
        }
    }

    fun nivelCasa(): Int = gw - 5

    fun precoAmpliar(): Int = 200 * nivelCasa()

    fun podeAmpliar(): Boolean = gw < 10

    fun canPlace(item: Item, nx: Int, ny: Int, rot: Int): Boolean {
        val w = if (rot % 2 == 1) item.type.h else item.type.w
        val h = if (rot % 2 == 1) item.type.w else item.type.h
        if (nx < 0 || ny < 0 || nx + w > gw || ny + h > gh) return false
        if (item.type.rug) return true
        return items.none { o ->
            o !== item && !o.type.rug &&
                nx < o.x + o.w && nx + w > o.x && ny < o.y + o.h && ny + h > o.y
        }
    }

    fun rotate(item: Item): Boolean {
        val nr = (item.rot + 1) % 4
        val w = if (nr % 2 == 1) item.type.h else item.type.w
        val h = if (nr % 2 == 1) item.type.w else item.type.h
        val nx = item.x.coerceIn(0, maxOf(0, gw - w))
        val ny = item.y.coerceIn(0, maxOf(0, gh - h))
        if (!canPlace(item, nx, ny, nr)) return false
        item.x = nx; item.y = ny; item.rot = nr
        return true
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
        val s = items.joinToString(";") { "${it.type.name},${it.x},${it.y},${it.rot}" }
        prefs.edit()
            .putString("state", "$money|$gw|$gh|$s")
            .putInt("floor", floorIdx).putInt("wall", wallIdx)
            .putInt("ownF", ownFloors).putInt("ownW", ownWalls)
            .putInt("sens", sens)
            .putString("avatar", avatar.encode())
            .apply()
    }
}
