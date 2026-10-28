package com.vinicius.meular

import android.content.Context

enum class Type(val nome: String, val w: Int, val h: Int, val preco: Int) {
    CHAIR("Cadeira", 1, 1, 20),
    TABLE("Mesa", 2, 1, 60),
    BED("Cama", 1, 2, 120),
    SOFA("Sofá", 2, 1, 150),
    SHELF("Estante", 2, 1, 100),
    PLANT("Planta", 1, 1, 30),
    RUG("Tapete", 2, 2, 40),
    TV("TV com rack", 2, 1, 250),
    FRIDGE("Geladeira", 1, 1, 300),
    STOVE("Fogão", 1, 1, 220),
    LAMP("Abajur", 1, 1, 35)
}

class Item(val type: Type, var x: Int, var y: Int, var rot: Boolean = false) {
    val w: Int get() = if (rot) type.h else type.w
    val h: Int get() = if (rot) type.w else type.h
}

class GameState(ctx: Context) {
    private val prefs = ctx.getSharedPreferences("meular", Context.MODE_PRIVATE)
    var money = 50
    var gw = 6
    var gh = 5
    val items = mutableListOf<Item>()

    init {
        val raw = prefs.getString("state", null)
        var ok = false
        if (raw != null) {
            try {
                val parts = raw.split("|")
                money = parts[0].toInt(); gw = parts[1].toInt(); gh = parts[2].toInt()
                if (parts.size > 3 && parts[3].isNotEmpty()) {
                    for (s in parts[3].split(";")) {
                        val f = s.split(",")
                        items.add(Item(Type.valueOf(f[0]), f[1].toInt(), f[2].toInt(), f[3] == "1"))
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

    fun canPlace(item: Item, nx: Int, ny: Int, rot: Boolean): Boolean {
        val w = if (rot) item.type.h else item.type.w
        val h = if (rot) item.type.w else item.type.h
        if (nx < 0 || ny < 0 || nx + w > gw || ny + h > gh) return false
        if (item.type == Type.RUG) return true
        return items.none { o ->
            o !== item && o.type != Type.RUG &&
                nx < o.x + o.w && nx + w > o.x && ny < o.y + o.h && ny + h > o.y
        }
    }

    fun findSpot(t: Type): Pair<Int, Int>? {
        val probe = Item(t, 0, 0)
        for (y in 0 until gh) for (x in 0 until gw) {
            if (canPlace(probe, x, y, false)) return Pair(x, y)
        }
        return null
    }

    fun save() {
        val s = items.joinToString(";") { "${it.type.name},${it.x},${it.y},${if (it.rot) 1 else 0}" }
        prefs.edit().putString("state", "$money|$gw|$gh|$s").apply()
    }
}
