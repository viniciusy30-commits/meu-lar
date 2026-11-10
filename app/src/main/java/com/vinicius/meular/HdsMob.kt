package com.vinicius.meular

import android.content.res.AssetManager
import org.json.JSONObject

/** Etapa 171: catálogo de mobília do Hds (portas, janelas, sofás, camas...). Dados em assets/hds/mobilia/mobilia.json. */
object HdsMob {
    class Cat(val nome: String)

    @Volatile var cats: List<Cat> = emptyList()
    private val porCat = HashMap<Int, ArrayList<Type>>()
    @Volatile private var pronto = false

    @Synchronized fun load(am: AssetManager) {
        if (pronto) return
        try {
            val js = JSONObject(am.open("hds/mobilia/mobilia.json").bufferedReader(Charsets.UTF_8).use { it.readText() })
            val ca = js.getJSONArray("cats")
            cats = (0 until ca.length()).map { Cat(ca.getJSONObject(it).getString("n")) }
            val m = js.getJSONArray("m")
            for (i in 0 until m.length()) {
                val o = m.getJSONObject(i)
                Type.addHds(o.getString("id"), o.getString("n"), o.getInt("w"), o.getInt("h"), o.getDouble("a").toFloat(), o.getInt("c"))
            }
            for (t in Type.values()) if (t.cat >= 100) porCat.getOrPut(t.cat - 100) { ArrayList() }.add(t)
            for (l in porCat.values) l.sortBy { it.nome }
            pronto = true
        } catch (e: Throwable) {
            android.util.Log.e("HdsMob", "catálogo falhou", e)
        }
    }

    fun items(cat: Int): List<Type> = porCat[cat] ?: emptyList()
    fun count(cat: Int): Int = porCat[cat]?.size ?: 0
}
