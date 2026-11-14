package com.vinicius.meular

import android.content.SharedPreferences

/**
 * Etapa 174: imobiliária da Cidade 2 (Hds). As 17 casas ganham bairro, classe e preço pelo tamanho do lote.
 * O jogador começa dono da Casa 1 (a menor). Dinheiro é infinito por enquanto.
 */
object HdsEstate {
    class Info(val idx: Int, val bairro: String, val classe: String, val area: Int, val price: Int, val venda: Boolean)

    // área (m²) de cada lote, na ordem de city2.json "plots"
    private val AREA = intArrayOf(76, 850, 619, 439, 355, 326, 357, 154, 215, 254, 274, 131, 208, 253, 351, 363, 1002)
    private val BAIRRO = arrayOf(
        "Vila Esperança", "Alto da Colina", "Alto da Colina", "Alto da Colina",
        "Jardim Central", "Jardim Central", "Jardim Central", "Recanto do Sul",
        "Vila Esperança", "Vila Esperança", "Recanto do Sul", "Parque das Flores",
        "Vila Esperança", "Parque das Flores", "Parque das Flores", "Parque das Flores",
        "Alto da Colina")

    private fun classe(a: Int) = when { a < 200 -> "Popular"; a < 400 -> "Médio"; a < 700 -> "Alto padrão"; else -> "Nobre" }
    private fun perM2(a: Int) = when { a < 200 -> 900; a < 400 -> 1500; a < 700 -> 2400; else -> 3800 }

    // Etapa 177: cada casa fica no seu próprio quarteirão da cidade ampliada; todas à venda
    private val housesOld: List<Info> = AREA.indices.map { i -> Info(i, BAIRRO[i], classe(AREA[i]), AREA[i], AREA[i] * perM2(AREA[i]) / 1000 * 1000, true) }
    // Cidade 5 (Meular City): bairros do zoneamento do prompt (Casa k+1 = índice k)
    private val BAIRRO_C5 = arrayOf(
        "Vila Esperança", "Alto da Colina", "Alto da Colina", "Recanto do Sul",
        "Jardim Central", "Jardim Central", "Jardim Central", "Vila Esperança",
        "Vila Esperança", "Parque das Flores", "Parque das Flores", "Vila Esperança",
        "Vila Esperança", "Parque das Flores", "Recanto do Sul", "Recanto do Sul",
        "Península Real")
    private val housesC5: List<Info> = AREA.indices.map { i -> Info(i, BAIRRO_C5[i], classe(AREA[i]), AREA[i], AREA[i] * perM2(AREA[i]) / 1000 * 1000, true) }
    val houses: List<Info> get() = if (City.C5) housesC5 else housesOld
    /** distância em metros da sua primeira casa até a casa i */
    fun dist(i: Int): Int {
        val a = Hds.plot(0) ?: return 0; val b = Hds.plot(i) ?: return 0
        return Math.hypot(((a[0] + a[2]) / 2 - (b[0] + b[2]) / 2).toDouble(), ((a[1] + a[3]) / 2 - (b[1] + b[3]) / 2).toDouble()).toInt()
    }

    const val START = 0   // Casa 1 do Hds
    const val INFINITE = 999_999_999

    private var prefs: SharedPreferences? = null
    private val owned = HashSet<Int>()

    fun init(p: SharedPreferences) {
        prefs = p
        owned.clear()
        owned.add(START)
        p.getString("hds_owned", "")?.split(",")?.mapNotNull { it.toIntOrNull() }?.let { owned.addAll(it) }
    }

    fun isOwned(i: Int) = owned.contains(i)
    fun buy(i: Int) { owned.add(i); prefs?.edit()?.putString("hds_owned", owned.joinToString(","))?.apply() }
    fun label(i: Int): String { val h = houses.getOrNull(i) ?: return "Casa ${i + 1}"; return "Casa ${i + 1} · ${h.bairro}" + (if (i == START) " (sua)" else if (!h.venda) " (ocupada)" else "") }
    fun brl(v: Int): String = "R$ " + String.format(java.util.Locale("pt", "BR"), "%,d", v)
}
