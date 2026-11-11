package com.vinicius.meular

import android.content.res.AssetManager
import org.json.JSONObject

/** Etapa 171/172: catálogo de mobília do Hds (portas, janelas, sofás, camas...). Dados em assets/hds/mobilia/mobilia.json:
 *  categorias com ícone e subcategorias do próprio Hds; cada móvel tem subcategoria e se tem partes coloríveis. */
object HdsMob {
    class Cat(val nome: String, val icone: String, val subs: List<String>)

    @Volatile var cats: List<Cat> = emptyList()
    private val porCat = HashMap<Int, ArrayList<Type>>()
    private val subDe = HashMap<Type, String>()
    private val comCor = HashSet<Type>()
    @Volatile private var pronto = false

    @Synchronized fun load(am: AssetManager) {
        if (pronto) return
        try {
            val js = JSONObject(am.open("hds/mobilia/mobilia.json").bufferedReader(Charsets.UTF_8).use { it.readText() })
            val ca = js.getJSONArray("cats")
            cats = (0 until ca.length()).map {
                val o = ca.getJSONObject(it)
                val sa = o.optJSONArray("s")
                Cat(o.getString("n"), o.optString("i", ""), if (sa == null) emptyList() else (0 until sa.length()).map { k -> sa.getString(k) })
            }
            val m = js.getJSONArray("m")
            val ordem = ArrayList<Pair<Type, Int>>()
            for (i in 0 until m.length()) {
                val o = m.getJSONObject(i)
                val t = Type.addHds(o.getString("id"), o.getString("n"), o.getInt("w"), o.getInt("h"), o.getDouble("a").toFloat(), o.getInt("c")) ?: continue
                subDe[t] = o.optString("s", "")
                if (o.optInt("k", 0) == 1) comCor.add(t)
                ordem.add(Pair(t, i))
            }
            // mesma ordem do índice (categoria, subcategoria, nome)
            for ((t, _) in ordem) porCat.getOrPut(t.cat - 100) { ArrayList() }.add(t)
            pronto = true
        } catch (e: Throwable) {
            android.util.Log.e("HdsMob", "catálogo falhou", e)
        }
    }

    fun items(cat: Int): List<Type> = porCat[cat] ?: emptyList()
    /** móveis da categoria [cat] só da subcategoria [sub] (índice em Cat.subs; -1 = todas) */
    fun items(cat: Int, sub: Int): List<Type> {
        val l = items(cat)
        if (sub < 0) return l
        val nome = cats.getOrNull(cat)?.subs?.getOrNull(sub) ?: return l
        return l.filter { subDe[it] == nome }
    }
    fun count(cat: Int): Int = porCat[cat]?.size ?: 0
    fun sub(t: Type): String = subDe[t] ?: ""
    fun temCor(t: Type): Boolean = comCor.contains(t)
}
