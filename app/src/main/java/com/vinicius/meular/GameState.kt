package com.vinicius.meular

import android.content.Context
import java.util.concurrent.CopyOnWriteArrayList

enum class Type(val nome: String, val w: Int, val h: Int, val preco: Int, val alt: Float) {
    CHAIR("Cadeira", 1, 1, 20, 1.05f),
    TABLE("Mesa", 2, 1, 60, 1.25f),
    BED("Cama", 1, 2, 120, 1.05f),
    SOFA("Sofá", 2, 1, 150, 1.0f),
    SHELF("Estante", 2, 1, 100, 1.9f),
    PLANT("Planta", 1, 1, 30, 1.45f),
    RUG("Tapete", 2, 2, 40, 0.07f),
    TV("TV com rack", 2, 1, 250, 1.4f),
    FRIDGE("Geladeira", 1, 1, 300, 1.9f),
    STOVE("Fogão", 1, 1, 220, 1.2f),
    LAMP("Abajur", 1, 1, 35, 1.6f)
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
    val items = CopyOnWriteArrayList<Item>()

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
        if (item.type == Type.RUG) return true
        return items.none { o ->
            o !== item && o.type != Type.RUG &&
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

    fun findSpot(t: Type): Pair<Int, Int>? {
        val probe = Item(t, 0, 0)
        for (y in 0 until gh) for (x in 0 until gw) {
            if (canPlace(probe, x, y, 0)) return Pair(x, y)
        }
        return null
    }

    fun save() {
        val s = items.joinToString(";") { "${it.type.name},${it.x},${it.y},${it.rot}" }
        prefs.edit().putString("state", "$money|$gw|$gh|$s").apply()
    }
}
