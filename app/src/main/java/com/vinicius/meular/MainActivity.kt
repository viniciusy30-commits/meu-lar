package com.vinicius.meular

import android.app.AlertDialog
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private lateinit var st: GameState
    private lateinit var game: GameView
    private lateinit var dinheiro: TextView
    private lateinit var barra: ProgressBar
    private lateinit var selBar: LinearLayout
    private var progresso = 0

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()

    private fun botao(txt: String, cor: String, acao: () -> Unit): Button {
        val b = Button(this)
        b.text = txt
        b.isAllCaps = false
        b.setTextColor(Color.WHITE)
        b.textSize = 16f
        val g = GradientDrawable()
        g.setColor(Color.parseColor(cor)); g.cornerRadius = dp(14).toFloat()
        b.background = g
        val lp = LinearLayout.LayoutParams(0, dp(52), 1f)
        lp.setMargins(dp(4), dp(4), dp(4), dp(4))
        b.layoutParams = lp
        b.setOnClickListener { v ->
            v.animate().scaleX(.93f).scaleY(.93f).setDuration(70).withEndAction {
                v.animate().scaleX(1f).scaleY(1f).setDuration(90).start()
            }.start()
            acao()
        }
        return b
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        st = GameState(this)
        game = GameView(this, st)

        val raiz = LinearLayout(this)
        raiz.orientation = LinearLayout.VERTICAL
        raiz.setBackgroundColor(Color.parseColor("#2B2D42"))

        dinheiro = TextView(this)
        dinheiro.textSize = 26f
        dinheiro.setTextColor(Color.parseColor("#FFEB3B"))
        dinheiro.gravity = Gravity.CENTER
        dinheiro.setPadding(0, dp(14), 0, dp(6))
        raiz.addView(dinheiro, ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)

        raiz.addView(game, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))

        selBar = LinearLayout(this)
        selBar.orientation = LinearLayout.HORIZONTAL
        selBar.visibility = View.GONE
        selBar.addView(botao("Girar", "#5C6BC0") { girar() })
        selBar.addView(botao("Vender (50%)", "#E53935") { vender() })
        raiz.addView(selBar, ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)

        barra = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal)
        barra.max = 100
        val lpB = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(10))
        lpB.setMargins(dp(12), dp(6), dp(12), dp(2))
        raiz.addView(barra, lpB)

        val rodape = LinearLayout(this)
        rodape.orientation = LinearLayout.HORIZONTAL
        rodape.setPadding(dp(4), 0, dp(4), dp(8))
        rodape.addView(botao("Trabalhar", "#43A047") { trabalhar() })
        rodape.addView(botao("Loja", "#FF8A65") { loja() })
        rodape.addView(botao("Config.", "#78909C") { config() })
        raiz.addView(rodape, ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)

        setContentView(raiz)

        game.onSelect = { s -> selBar.visibility = if (s == null) View.GONE else View.VISIBLE }
        game.onChanged = { st.save() }
        atualizarDinheiro(false)
        mostrarNovidades()
        Updater.autoCheck(this)
    }

    private fun atualizarDinheiro(pulso: Boolean) {
        dinheiro.text = "R$ ${st.money}"
        if (pulso) dinheiro.animate().scaleX(1.3f).scaleY(1.3f).setDuration(120).withEndAction {
            dinheiro.animate().scaleX(1f).scaleY(1f).setDuration(160).start()
        }.start()
    }

    private fun trabalhar() {
        progresso += 12
        if (progresso >= 100) {
            progresso = 0
            st.money += 25
            st.save()
            atualizarDinheiro(true)
            Toast.makeText(this, "Pagamento recebido: +R$ 25", Toast.LENGTH_SHORT).show()
        }
        barra.progress = progresso
    }

    private fun girar() {
        val s = game.selected ?: return
        if (st.canPlace(s, s.x, s.y, !s.rot)) {
            s.rot = !s.rot; st.save(); game.invalidate()
        } else Toast.makeText(this, "Sem espaço para girar aqui.", Toast.LENGTH_SHORT).show()
    }

    private fun vender() {
        val s = game.selected ?: return
        st.items.remove(s)
        st.money += s.type.preco / 2
        st.save()
        game.selected = null
        atualizarDinheiro(true)
    }

    private fun loja() {
        val tipos = Type.values()
        val nomes = ArrayList<String>()
        for (t in tipos) nomes.add("${t.nome} — R$ ${t.preco}")
        nomes.add(if (st.podeAmpliar()) "Ampliar casa — R$ ${st.precoAmpliar()}" else "Casa no tamanho máximo")
        AlertDialog.Builder(this)
            .setTitle("Loja")
            .setItems(nomes.toTypedArray()) { _, i ->
                if (i < tipos.size) comprar(tipos[i]) else ampliarCasa()
            }
            .setNegativeButton("Fechar", null)
            .show()
    }

    private fun comprar(t: Type) {
        if (st.money < t.preco) { Toast.makeText(this, "Dinheiro insuficiente. Vá trabalhar!", Toast.LENGTH_SHORT).show(); return }
        val spot = st.findSpot(t)
        if (spot == null) { Toast.makeText(this, "Sem espaço na casa. Venda algo ou amplie.", Toast.LENGTH_LONG).show(); return }
        st.money -= t.preco
        val novo = Item(t, spot.first, spot.second)
        st.items.add(novo)
        st.save()
        atualizarDinheiro(true)
        game.selected = novo
        Toast.makeText(this, "${t.nome} colocado! Arraste para posicionar.", Toast.LENGTH_SHORT).show()
    }

    private fun ampliarCasa() {
        if (!st.podeAmpliar()) { Toast.makeText(this, "A casa já está no tamanho máximo.", Toast.LENGTH_SHORT).show(); return }
        val preco = st.precoAmpliar()
        if (st.money < preco) { Toast.makeText(this, "Dinheiro insuficiente.", Toast.LENGTH_SHORT).show(); return }
        st.money -= preco; st.gw += 1; st.gh += 1
        st.save(); atualizarDinheiro(true); game.invalidate()
        Toast.makeText(this, "Casa ampliada para ${st.gw}x${st.gh}!", Toast.LENGTH_SHORT).show()
    }

    private fun config() {
        AlertDialog.Builder(this)
            .setTitle("Configurações")
            .setItems(arrayOf("Verificar atualização", "O que mudou")) { _, i ->
                if (i == 0) Updater.check(this, true) else mostrarNovidades(true)
            }
            .setNegativeButton("Fechar", null)
            .show()
    }

    private fun mostrarNovidades(forcar: Boolean = false) {
        try {
            val linhas = assets.open("novidades.txt").bufferedReader().readLines()
            var id = ""
            var titulo = ""
            val itens = StringBuilder()
            var secoes = 0
            for (l in linhas) {
                if (l.startsWith("#id")) { secoes++; if (secoes > 1) break; id = l.removePrefix("#id").trim() }
                else if (l.startsWith("#titulo") && secoes == 1) titulo = l.removePrefix("#titulo").trim()
                else if (l.startsWith("-") && secoes == 1) itens.append("• ").append(l.removePrefix("-").trim()).append("\n")
            }
            val p = getSharedPreferences("novidades", MODE_PRIVATE)
            val visto = p.getString("id", null)
            p.edit().putString("id", id).apply()
            if (forcar || (visto != null && visto != id)) {
                AlertDialog.Builder(this).setTitle(titulo).setMessage(itens.toString().trim())
                    .setPositiveButton("Legal!", null).show()
            }
        } catch (e: Exception) { }
    }
}
