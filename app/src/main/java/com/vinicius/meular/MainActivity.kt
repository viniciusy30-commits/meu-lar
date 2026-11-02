package com.vinicius.meular

import android.app.Dialog
import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.LayerDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.Window
import android.widget.FrameLayout
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.RecyclerView

class MainActivity : AppCompatActivity() {
    private lateinit var st: GameState
    private lateinit var game: GameView
    private lateinit var moneyTv: TextView
    private lateinit var workBar: PillBar
    private lateinit var editBar: LinearLayout
    private lateinit var moveIcon: IconView
    private lateinit var moveLbl: TextView
    private lateinit var moveBox: LinearLayout
    private lateinit var msgTv: TextView
    private lateinit var viewIcon: IconView
    private lateinit var hud: LinearLayout
    private lateinit var bottom: LinearLayout
    private lateinit var jumpBtn: FrameLayout
    private lateinit var dockR: LinearLayout
    private lateinit var creator: CreatorUi
    private var prevMode = 0
    private var progresso = 0
    private var bottomInset = 0

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
    private fun dpf(v: Float) = v * resources.displayMetrics.density

    private fun tv(txt: String, size: Float, color: Int, bold: Boolean = false): TextView {
        val t = TextView(this)
        t.text = txt; t.textSize = size; t.setTextColor(color)
        t.typeface = if (bold) Ui.BOLD else Ui.MED
        return t
    }

    private fun press(v: View, acao: () -> Unit) {
        v.setOnClickListener {
            it.animate().scaleX(.92f).scaleY(.92f).setDuration(70).withEndAction {
                it.animate().scaleX(1f).scaleY(1f).setDuration(100).start()
            }.start()
            acao()
        }
    }

    private fun tvShadow(t: TextView): TextView {
        t.setShadowLayer(dpf(1.5f), 0f, dpf(1f), 0x99000000.toInt())
        return t
    }

    /** Botão redondo "gostosinho" (degrau escuro embaixo + brilho) com ícone. */
    private fun roundBtn(icon: Int, size: Int, tone: Tone, acao: () -> Unit): Pair<FrameLayout, IconView> {
        val f = FrameLayout(this)
        f.background = Ui.chunky(tone, dpf(size.toFloat()), dpf(3f))
        f.setPadding(0, 0, 0, dp(3))
        val ic = IconView(this, icon, Color.WHITE, tone.edge)
        val isz = (size * 0.54f).toInt()
        f.addView(ic, FrameLayout.LayoutParams(dp(isz), dp(isz), Gravity.CENTER))
        f.layoutParams = LinearLayout.LayoutParams(dp(size), dp(size)).also { it.leftMargin = dp(8) }
        press(f, acao)
        return Pair(f, ic)
    }

    private val DARK = 0x0B1624
    private val SOFT_ACC = Color.argb(110, 15, 35, 70)

    /** Botão redondo de vidro escuro translúcido com aro de luz; ícone com degradê e brilho. */
    private fun glassBtn(icon: Int, size: Int, acao: () -> Unit): Pair<FrameLayout, IconView> {
        val f = FrameLayout(this)
        f.background = Ui.frost(0f, DARK, 0x8C, 0x5C, dpf(1.4f), oval = true)
        val ic = IconView(this, icon, Color.WHITE, SOFT_ACC).fancy()
        val isz = (size * 0.58f).toInt()
        f.addView(ic, FrameLayout.LayoutParams(dp(isz), dp(isz), Gravity.CENTER))
        f.layoutParams = LinearLayout.LayoutParams(dp(size), dp(size)).also { it.leftMargin = dp(10) }
        press(f, acao)
        return Pair(f, ic)
    }

    /** Botão da barra inferior: vidro colorido translúcido, só ícone (sem texto). */
    private fun simsSeg(icon: Int, tint: Int, acao: () -> Unit): FrameLayout {
        val f = FrameLayout(this)
        f.background = Ui.frost(dpf(19f), tint, 0xC0, 0x7A, dpf(1.4f))
        f.addView(IconView(this, icon, Color.WHITE, SOFT_ACC).fancy(0xAAFFFFFF.toInt()), FrameLayout.LayoutParams(dp(32), dp(32), Gravity.CENTER))
        f.layoutParams = LinearLayout.LayoutParams(dp(54), dp(54)).also { it.setMargins(dp(3), dp(3), dp(3), dp(3)) }
        press(f, acao)
        return f
    }

    private fun editBtn(icon: Int, label: String, tone: Tone, acao: () -> Unit): Triple<LinearLayout, IconView, TextView> {
        val l = LinearLayout(this)
        l.orientation = LinearLayout.VERTICAL
        l.gravity = Gravity.CENTER_HORIZONTAL
        val circ = FrameLayout(this)
        circ.background = Ui.frost(0f, tone.bot, 0xC0, 0x7A, dpf(1.4f), oval = true)
        val ic = IconView(this, icon, Color.WHITE, SOFT_ACC).fancy(0xAAFFFFFF.toInt())
        circ.addView(ic, FrameLayout.LayoutParams(dp(25), dp(25), Gravity.CENTER))
        l.addView(circ, LinearLayout.LayoutParams(dp(46), dp(46)))
        val t = tvShadow(tv(label, 11f, Pal.TEXT, true))
        t.gravity = Gravity.CENTER
        l.addView(t, LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT).also { it.topMargin = dp(4) })
        l.layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT).also { it.setMargins(dp(8), 0, dp(8), 0) }
        press(l, acao)
        return Triple(l, ic, t)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        CuteChar.assets = assets
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = Color.TRANSPARENT
        window.navigationBarColor = Color.TRANSPARENT

        st = GameState(this)
        game = GameView(this, st)
        val overlay = Overlay(this, game)

        val root = FrameLayout(this)
        root.setBackgroundColor(Color.BLACK)
        root.addView(game, FrameLayout.LayoutParams(-1, -1))
        root.addView(overlay, FrameLayout.LayoutParams(-1, -1))

        // topo: painel de dinheiro (esquerda) + botões pequenos (direita), como no The Sims
        hud = LinearLayout(this)
        hud.orientation = LinearLayout.HORIZONTAL
        hud.gravity = Gravity.CENTER_VERTICAL
        hud.setPadding(dp(12), dp(8), dp(12), dp(4))
        val chip = LinearLayout(this)
        chip.orientation = LinearLayout.HORIZONTAL
        chip.gravity = Gravity.CENTER_VERTICAL
        chip.setPadding(dp(7), dp(5), dp(7), dp(5))
        chip.background = Ui.frost(dpf(24f), DARK, 0x8C, 0x5C, dpf(1.3f))
        chip.addView(IconView(this, Ic.COIN).fancy(0x99FFC94D.toInt()), LinearLayout.LayoutParams(dp(30), dp(30)).also { it.rightMargin = dp(8) })
        moneyTv = tvShadow(tv("", 16f, Color.WHITE, true))
        chip.addView(moneyTv)
        val plus = FrameLayout(this)
        plus.background = Ui.frost(0f, 0x3CD68A, 0xD0, 0x90, dpf(1.2f), oval = true)
        plus.addView(IconView(this, Ic.PLUS, Color.WHITE, SOFT_ACC).fancy(0xAAFFFFFF.toInt()), FrameLayout.LayoutParams(dp(18), dp(18), Gravity.CENTER))
        plus.layoutParams = LinearLayout.LayoutParams(dp(26), dp(26)).also { it.leftMargin = dp(10) }
        press(plus) { loja(0) }
        chip.addView(plus)
        hud.addView(chip)
        hud.addView(View(this), LinearLayout.LayoutParams(0, 1, 1f))
        val vb = glassBtn(Ic.HOME, 44) { alternarVista() }
        viewIcon = vb.second
        hud.addView(vb.first)
        hud.addView(glassBtn(Ic.PERSON, 44) { abrirCriador() }.first)
        root.addView(hud, FrameLayout.LayoutParams(-1, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP))

        msgTv = tvShadow(tv("", 13f, Pal.TEXT, true))
        msgTv.gravity = Gravity.CENTER
        msgTv.setPadding(dp(18), dp(9), dp(18), dp(9))
        msgTv.background = Ui.frost(dpf(22f), DARK, 0xA0, 0x7A, dpf(1.3f))
        msgTv.visibility = View.GONE
        root.addView(msgTv, FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP or Gravity.CENTER_HORIZONTAL).also { it.topMargin = dp(60) })

        // base: painel de controle compacto no centro + botão de pular à direita
        bottom = LinearLayout(this)
        bottom.orientation = LinearLayout.VERTICAL
        bottom.gravity = Gravity.CENTER_HORIZONTAL
        bottom.setPadding(0, 0, 0, dp(8))
        editBar = LinearLayout(this)
        editBar.orientation = LinearLayout.HORIZONTAL
        editBar.gravity = Gravity.CENTER
        editBar.visibility = View.GONE
        val mv = editBtn(Ic.MOVE, "Pegar", Tn.CORAL) { pegarSoltar() }
        moveBox = mv.first; moveIcon = mv.second; moveLbl = mv.third
        editBar.addView(moveBox)
        editBar.addView(editBtn(Ic.ROTATE, "Girar", Tn.LAV) { girar() }.first)
        editBar.addView(editBtn(Ic.TRASH, "Vender", Tn.ROSE) { vender() }.first)
        bottom.addView(editBar, LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT).also { it.bottomMargin = dp(6) })

        root.addView(bottom, FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL))

        // barra de ícones no canto inferior direito (azul / roxo / verde), como no The Sims
        dockR = LinearLayout(this)
        dockR.orientation = LinearLayout.VERTICAL
        val frame = LinearLayout(this)
        frame.orientation = LinearLayout.HORIZONTAL
        frame.setPadding(dp(4), dp(4), dp(4), dp(4))
        frame.background = Ui.frost(dpf(27f), DARK, 0x80, 0x52, dpf(1.3f))
        frame.addView(simsSeg(Ic.CASE, 0x2FA8F0) { trabalhar() })
        frame.addView(simsSeg(Ic.CART, 0x9B5CF0) { loja(0) })
        frame.addView(simsSeg(Ic.DOTS, 0x3CD68A) { config() })
        dockR.addView(frame, LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        workBar = PillBar(this)
        dockR.addView(workBar, LinearLayout.LayoutParams(-1, dp(9)).also { it.topMargin = dp(7); it.leftMargin = dp(8); it.rightMargin = dp(8) })
        root.addView(dockR, FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(14), dp(10)) })

        // botão de pular (só na primeira pessoa)
        jumpBtn = FrameLayout(this)
        jumpBtn.background = Ui.frost(0f, 0x2FA8F0, 0xB8, 0x72, dpf(1.5f), oval = true)
        jumpBtn.addView(IconView(this, Ic.JUMP, Color.WHITE, SOFT_ACC).fancy(0xAAFFFFFF.toInt()), FrameLayout.LayoutParams(dp(32), dp(32), Gravity.CENTER))
        press(jumpBtn) { if (game.mode == 0) game.r.jumpReq = true }
        root.addView(jumpBtn, FrameLayout.LayoutParams(dp(60), dp(60), Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(78), dp(108)) })

        creator = CreatorUi(this, st, game) { fecharCriador() }
        creator.visibility = View.GONE
        root.addView(creator, FrameLayout.LayoutParams(-1, -1))

        setContentView(root)

        ViewCompat.setOnApplyWindowInsetsListener(root) { _, ins ->
            val b = ins.getInsets(WindowInsetsCompat.Type.systemBars())
            hud.setPadding(dp(12) + b.left, b.top + dp(6), dp(12) + b.right, dp(4))
            bottom.setPadding(0, 0, 0, b.bottom + dp(8))
            (jumpBtn.layoutParams as FrameLayout.LayoutParams).setMargins(0, 0, dp(78) + b.right, dp(108) + b.bottom)
            (dockR.layoutParams as FrameLayout.LayoutParams).setMargins(0, 0, dp(14) + b.right, dp(10) + b.bottom)
            dockR.requestLayout()
            jumpBtn.requestLayout()
            bottomInset = b.bottom
            val cb = ins.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout())
            creator.setInsets(cb.left, cb.top, cb.right, cb.bottom)
            (msgTv.layoutParams as FrameLayout.LayoutParams).topMargin = b.top + dp(56)
            ins
        }

        game.onFocus = { item, grabbed -> aoMudarFoco(item, grabbed) }
        game.onChanged = { st.save() }
        atualizarDinheiro(false)
        mostrarNovidades()
        Updater.autoCheck(this)
        if (!st.avatarSet) root.post { abrirCriador() }
    }

    override fun onResume() { super.onResume(); game.onResume() }

    override fun onPause() { super.onPause(); st.save(); game.onPause() }

    // ------------------------------------------------------------ HUD

    private fun atualizarDinheiro(pulso: Boolean) {
        moneyTv.text = "R$ ${st.money}"
        if (pulso) moneyTv.animate().scaleX(1.25f).scaleY(1.25f).setDuration(120).withEndAction {
            moneyTv.animate().scaleX(1f).scaleY(1f).setDuration(160).start()
        }.start()
    }

    private val hideMsg = Runnable {
        msgTv.animate().alpha(0f).setDuration(250).withEndAction { msgTv.visibility = View.GONE }.start()
    }

    private fun msg(s: String) {
        msgTv.text = s
        msgTv.animate().cancel()
        msgTv.removeCallbacks(hideMsg)
        msgTv.visibility = View.VISIBLE
        msgTv.alpha = 0f
        msgTv.animate().alpha(1f).setDuration(150).start()
        msgTv.postDelayed(hideMsg, 2000)
    }

    private fun aoMudarFoco(item: Item?, grabbed: Boolean) {
        editBar.visibility = if (item == null) View.GONE else View.VISIBLE
        moveBox.visibility = if (game.mode == 0) View.VISIBLE else View.GONE
        if (grabbed) { moveIcon.set(Ic.CHECK); moveLbl.text = "Soltar" }
        else { moveIcon.set(Ic.MOVE); moveLbl.text = "Pegar" }
    }

    private fun abrirCriador() {
        if (game.mode == 2) return
        prevMode = game.mode
        game.r.avDirty = true
        game.mode = 2
        editBar.visibility = View.GONE
        hud.visibility = View.GONE
        bottom.visibility = View.GONE
        dockR.visibility = View.GONE
        jumpBtn.visibility = View.GONE
        creator.visibility = View.VISIBLE
        creator.open()
    }

    private fun fecharCriador() {
        st.avatarSet = true
        st.save()
        creator.visibility = View.GONE
        hud.visibility = View.VISIBLE
        bottom.visibility = View.VISIBLE
        dockR.visibility = View.VISIBLE
        game.mode = prevMode
        jumpBtn.visibility = if (prevMode == 0) View.VISIBLE else View.GONE
        viewIcon.set(if (prevMode == 0) Ic.HOME else Ic.EYE)
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (game.mode == 2) fecharCriador() else super.onBackPressed()
    }

    private fun alternarVista() {
        if (game.mode == 2) return
        val novo = if (game.mode == 0) 1 else 0
        game.mode = novo
        viewIcon.set(if (novo == 0) Ic.HOME else Ic.EYE)
        jumpBtn.visibility = if (novo == 0) View.VISIBLE else View.GONE
        editBar.visibility = View.GONE
        if (novo == 1) st.save()
        msg(if (novo == 0) "Primeira pessoa" else "Vista aérea: toque no chão para andar, arraste os móveis")
    }

    private fun trabalhar() {
        progresso += 12
        if (progresso >= 100) {
            progresso = 0
            st.money += 25
            st.save()
            atualizarDinheiro(true)
            msg("Pagamento recebido: +R$ 25")
        }
        workBar.value = progresso / 100f
    }

    // ------------------------------------------------------------ edição

    private fun pegarSoltar() {
        if (game.mode != 0) return
        if (game.r.grabbed != null) {
            game.r.grabbed = null
            st.save()
            msg("Móvel colocado")
        } else {
            val f = game.r.focus ?: return
            game.r.grabbed = f
            msg("Olhe para onde quer pôr e toque em Soltar")
        }
    }

    private fun girar() {
        val s = game.r.focus ?: return
        if (st.rotate(s)) st.save() else msg("Sem espaço para girar aqui.")
    }

    private fun vender() {
        val s = game.r.focus ?: return
        game.r.grabbed = null
        game.selected = null
        st.items.remove(s)
        st.money += s.type.preco / 2
        st.save()
        atualizarDinheiro(true)
        editBar.visibility = View.GONE
        msg("${s.type.nome} vendido: +R$ ${s.type.preco / 2}")
    }

    // ------------------------------------------------------------ loja

    private class Entry(val titulo: String, val sub: String, val icon: Int, val swatch: Int, val ok: Boolean, val acao: () -> Unit)

    private class VH(val root: LinearLayout, val icon: IconView, val sw: View, val name: TextView, val price: TextView) : RecyclerView.ViewHolder(root)

    private inner class ShopAdapter : RecyclerView.Adapter<VH>() {
        var data: List<Entry> = emptyList()

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
            val l = LinearLayout(this@MainActivity)
            l.orientation = LinearLayout.VERTICAL
            l.gravity = Gravity.CENTER
            l.setPadding(dp(6), dp(10), dp(6), dp(13))
            l.layoutParams = RecyclerView.LayoutParams(-1, dp(138)).also { it.setMargins(dp(4), dp(4), dp(4), dp(4)) }
            l.background = Ui.chunky(Tn.CARD, dpf(20f), dpf(3f), false, Pal.LINE, dpf(1f))
            val ic = IconView(this@MainActivity, 0, Color.parseColor("#8EB8FF"), Pal.CARD)
            ic.background = Ui.bg(0x406CA0FF, dpf(14f))
            ic.setPadding(dp(9), dp(9), dp(9), dp(9))
            l.addView(ic, LinearLayout.LayoutParams(dp(58), dp(58)))
            val sw = View(this@MainActivity)
            l.addView(sw, LinearLayout.LayoutParams(dp(52), dp(52)))
            val n = tv("", 12f, Pal.TEXT, true)
            n.gravity = Gravity.CENTER
            n.maxLines = 2
            l.addView(n, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(6) })
            val pr = tv("", 12f, Pal.GOLD, true)
            pr.gravity = Gravity.CENTER
            l.addView(pr, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(2) })
            return VH(l, ic, sw, n, pr)
        }

        override fun onBindViewHolder(h: VH, i: Int) {
            val e = data[i]
            if (e.swatch != 0) {
                h.icon.visibility = View.GONE
                h.sw.visibility = View.VISIBLE
                h.sw.background = Ui.oval(e.swatch, Color.parseColor("#99FFF4E6"), dpf(2.5f))
            } else {
                h.sw.visibility = View.GONE
                h.icon.visibility = View.VISIBLE
                h.icon.set(e.icon)
            }
            h.name.text = e.titulo
            h.price.text = e.sub
            h.price.setTextColor(if (e.ok) Pal.GOLD else Pal.SUB)
            h.root.alpha = if (e.ok) 1f else 0.5f
            h.root.setOnClickListener { e.acao() }
        }

        override fun getItemCount() = data.size
    }

    private var shopDialog: Dialog? = null
    private var shopAdapter: ShopAdapter? = null
    private var shopTab = 0
    private var shopMoney: TextView? = null
    private var tabViews = ArrayList<TextView>()

    private fun entries(tab: Int): List<Entry> {
        val out = ArrayList<Entry>()
        if (tab in 0..3) {
            for (t in Type.values()) if (t.cat == tab) out.add(Entry(t.nome, "R$ ${t.preco}", t.ordinal, 0, st.money >= t.preco) { comprar(t) })
        } else if (tab == 4) {
            Finish.floors.forEachIndexed { i, f ->
                val own = (st.ownFloors shr i) and 1 == 1
                val sub = if (st.floorIdx == i) "Em uso" else if (own) "Comprado" else "R$ ${f.preco}"
                out.add(Entry("Piso\n${f.nome}", sub, 0, f.amostra, own || st.money >= f.preco) { comprarPiso(i) })
            }
            Finish.walls.forEachIndexed { i, w ->
                val own = (st.ownWalls shr i) and 1 == 1
                val sub = if (st.wallIdx == i) "Em uso" else if (own) "Comprado" else "R$ ${w.preco}"
                out.add(Entry("Parede\n${w.nome}", sub, 0, w.cor, own || st.money >= w.preco) { comprarParede(i) })
            }
        } else {
            if (st.podeAmpliar()) {
                val p = st.precoAmpliar()
                out.add(Entry("Ampliar casa\n${st.gw}x${st.gh} → ${st.gw + 1}x${st.gh + 1}", "R$ $p", Ic.HOME, 0, st.money >= p) { ampliarCasa() })
            } else {
                out.add(Entry("Tamanho máximo\n${st.gw}x${st.gh}", "—", Ic.HOME, 0, false) { })
            }
        }
        return out
    }

    private fun refreshShop() {
        shopAdapter?.data = entries(shopTab)
        shopAdapter?.notifyDataSetChanged()
        shopMoney?.text = "R$ ${st.money}"
        for ((i, t) in tabViews.withIndex()) {
            val sel = i == shopTab
            t.background = Ui.chunky(if (sel) Tn.CORAL else Tn.GHOST, dpf(20f), dpf(3f), sel)
            t.setTextColor(if (sel) Color.WHITE else Pal.SUB)
        }
    }

    private fun sheet(titulo: String, ic: Int = -1, tone: Tone = Tn.LAV, build: (LinearLayout) -> Unit): Dialog {
        val d = Dialog(this)
        d.requestWindowFeature(Window.FEATURE_NO_TITLE)
        val panel = LinearLayout(this)
        panel.orientation = LinearLayout.VERTICAL
        panel.background = Ui.sheetBg(dpf(30f), dpf(2f))
        panel.setPadding(dp(16), dp(14), dp(16), dp(16) + bottomInset)
        // alça no topo
        val grip = View(this)
        grip.background = Ui.bg(0x556A5A9C, dpf(3f))
        panel.addView(grip, LinearLayout.LayoutParams(dp(44), dp(5)).also { it.gravity = Gravity.CENTER_HORIZONTAL; it.bottomMargin = dp(10) })
        val head = LinearLayout(this)
        head.orientation = LinearLayout.HORIZONTAL
        head.gravity = Gravity.CENTER_VERTICAL
        if (ic >= 0) {
            val badge = FrameLayout(this)
            badge.background = Ui.chunky(tone, dpf(42f), dpf(3f))
            badge.setPadding(0, 0, 0, dp(3))
            badge.addView(IconView(this, ic, Color.WHITE, tone.edge), FrameLayout.LayoutParams(dp(23), dp(23), Gravity.CENTER))
            head.addView(badge, LinearLayout.LayoutParams(dp(42), dp(42)).also { it.rightMargin = dp(12) })
        }
        head.addView(tvShadow(tv(titulo, 23f, Pal.TEXT, true)), LinearLayout.LayoutParams(0, -2, 1f))
        val x = FrameLayout(this)
        x.background = Ui.chunky(Tn.CORAL, dpf(40f), dpf(3f))
        x.setPadding(0, 0, 0, dp(3))
        x.addView(IconView(this, Ic.CLOSE, Color.WHITE, Tn.CORAL.edge), FrameLayout.LayoutParams(dp(19), dp(19), Gravity.CENTER))
        press(x) { d.dismiss() }
        head.addView(x, LinearLayout.LayoutParams(dp(40), dp(40)))
        panel.addView(head, LinearLayout.LayoutParams(-1, -2).also { it.bottomMargin = dp(12) })
        build(panel)
        d.setContentView(panel)
        d.window?.apply {
            setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT))
            setGravity(Gravity.BOTTOM)
            setLayout(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            setDimAmount(0.55f)
        }
        return d
    }

    private fun loja(tab: Int) {
        shopTab = tab
        tabViews = ArrayList()
        val adapter = ShopAdapter()
        shopAdapter = adapter
        val d = sheet("Loja", Ic.SHOP, Tn.MINT) { panel ->
            val money = tvShadow(tv("R$ ${st.money}", 16f, Pal.GOLD, true))
            shopMoney = money
            val moneyChip = LinearLayout(this)
            moneyChip.orientation = LinearLayout.HORIZONTAL
            moneyChip.gravity = Gravity.CENTER_VERTICAL
            moneyChip.setPadding(dp(6), dp(3), dp(14), dp(6))
            moneyChip.background = Ui.panel(dpf(20f), dpf(3f), dpf(1.2f))
            moneyChip.addView(IconView(this, Ic.COIN), LinearLayout.LayoutParams(dp(22), dp(22)).also { it.rightMargin = dp(7) })
            moneyChip.addView(money)
            val sc = HorizontalScrollView(this)
            sc.isHorizontalScrollBarEnabled = false
            val row = LinearLayout(this)
            row.orientation = LinearLayout.HORIZONTAL
            val nomes = listOf("Sala", "Quarto", "Cozinha", "Decoração", "Piso e parede", "Casa")
            nomes.forEachIndexed { i, n ->
                val t = tv(n, 14f, Pal.SUB, true)
                t.setPadding(dp(16), dp(8), dp(16), dp(11))
                t.layoutParams = LinearLayout.LayoutParams(-2, -2).also { it.rightMargin = dp(8) }
                t.setOnClickListener { shopTab = i; refreshShop() }
                tabViews.add(t)
                row.addView(t)
            }
            sc.addView(row)
            panel.addView(moneyChip, LinearLayout.LayoutParams(-2, -2).also { it.bottomMargin = dp(10) })
            panel.addView(sc, LinearLayout.LayoutParams(-1, -2).also { it.bottomMargin = dp(10) })
            val rv = RecyclerView(this)
            rv.layoutManager = GridLayoutManager(this, 3)
            rv.adapter = adapter
            panel.addView(rv, LinearLayout.LayoutParams(-1, dp(310)))
        }
        shopDialog = d
        refreshShop()
        d.show()
    }

    private fun comprar(t: Type) {
        if (st.money < t.preco) { msg("Dinheiro insuficiente. Vá trabalhar!"); return }
        val alvo = game.frontTarget()
        val spot = st.findSpotNear(t, alvo[0], alvo[1])
        if (spot == null) { msg("Sem espaço na casa. Venda algo ou amplie."); return }
        st.money -= t.preco
        val novo = Item(t, spot.first, spot.second)
        novo.born = System.nanoTime()
        st.items.add(novo)
        st.save()
        atualizarDinheiro(true)
        if (game.mode == 0) game.r.grabbed = novo else game.selected = novo
        shopDialog?.dismiss()
        msg(if (game.mode == 0) "${t.nome} na sua mão! Olhe onde quer pôr e toque em Soltar" else "${t.nome} colocado! Arraste para posicionar.")
    }

    private fun comprarPiso(i: Int) {
        val f = Finish.floors[i]
        val own = (st.ownFloors shr i) and 1 == 1
        if (!own) {
            if (st.money < f.preco) { msg("Dinheiro insuficiente."); return }
            st.money -= f.preco
            st.ownFloors = st.ownFloors or (1 shl i)
        }
        st.floorIdx = i
        st.save(); atualizarDinheiro(true); refreshShop()
    }

    private fun comprarParede(i: Int) {
        val w = Finish.walls[i]
        val own = (st.ownWalls shr i) and 1 == 1
        if (!own) {
            if (st.money < w.preco) { msg("Dinheiro insuficiente."); return }
            st.money -= w.preco
            st.ownWalls = st.ownWalls or (1 shl i)
        }
        st.wallIdx = i
        st.save(); atualizarDinheiro(true); refreshShop()
    }

    private fun ampliarCasa() {
        if (!st.podeAmpliar()) { msg("A casa já está no tamanho máximo."); return }
        val preco = st.precoAmpliar()
        if (st.money < preco) { msg("Dinheiro insuficiente."); return }
        st.money -= preco; st.gw += 1; st.gh += 1
        st.save(); atualizarDinheiro(true); refreshShop()
        msg("Casa ampliada para ${st.gw}x${st.gh}!")
    }

    // ------------------------------------------------------------ configurações e novidades

    private fun linha(panel: LinearLayout, icon: Int, txt: String, tone: Tone, acao: () -> Unit): TextView {
        val l = LinearLayout(this)
        l.orientation = LinearLayout.HORIZONTAL
        l.gravity = Gravity.CENTER_VERTICAL
        l.setPadding(dp(12), dp(10), dp(16), dp(13))
        l.background = Ui.chunky(Tn.CARD, dpf(22f), dpf(3f), false, Pal.LINE, dpf(1f))
        val badge = FrameLayout(this)
        badge.background = Ui.chunky(tone, dpf(44f), dpf(3f))
        badge.setPadding(0, 0, 0, dp(3))
        badge.addView(IconView(this, icon, Color.WHITE, tone.edge), FrameLayout.LayoutParams(dp(24), dp(24), Gravity.CENTER))
        l.addView(badge, LinearLayout.LayoutParams(dp(44), dp(44)).also { it.rightMargin = dp(14) })
        val t = tv(txt, 16f, Pal.TEXT, true)
        l.addView(t, LinearLayout.LayoutParams(0, -2, 1f))
        l.addView(IconView(this, Ic.CHEV, Pal.SUB), LinearLayout.LayoutParams(dp(16), dp(16)))
        panel.addView(l, LinearLayout.LayoutParams(-1, -2).also { it.bottomMargin = dp(10) })
        press(l, acao)
        return t
    }

    private fun config() {
        val nomes = arrayOf("Baixa", "Média", "Alta")
        var dlg: Dialog? = null
        dlg = sheet("Configurações", Ic.GEAR, Tn.LAV) { panel ->
            linha(panel, Ic.REFRESH, "Verificar atualização", Tn.MINT) { dlg?.dismiss(); Updater.check(this, true) }
            linha(panel, Ic.PERSON, "Meu personagem", Tn.ROSE) { dlg?.dismiss(); abrirCriador() }
            linha(panel, Ic.INFO, "O que mudou", Tn.SKY) { dlg?.dismiss(); mostrarNovidades(true) }
            var sens: TextView? = null
            sens = linha(panel, Ic.EYE, "Sensibilidade do olhar: ${nomes[st.sens]}", Tn.SUN) {
                st.sens = (st.sens + 1) % 3
                st.save()
                sens?.text = "Sensibilidade do olhar: ${nomes[st.sens]}"
            }
        }
        dlg?.show()
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
                else if (l.startsWith("-") && secoes == 1) itens.append("•  ").append(l.removePrefix("-").trim()).append("\n\n")
            }
            val p = getSharedPreferences("novidades", MODE_PRIVATE)
            val visto = p.getString("id", null)
            p.edit().putString("id", id).apply()
            if (forcar || (visto != null && visto != id)) {
                var dlg: Dialog? = null
                dlg = sheet(titulo, Ic.SPARK, Tn.SUN) { panel ->
                    val t = tv(itens.toString().trim(), 15f, Pal.TEXT)
                    t.setLineSpacing(0f, 1.1f)
                    panel.addView(t, LinearLayout.LayoutParams(-1, -2).also { it.bottomMargin = dp(16) })
                    val b = tvShadow(tv("Legal!", 18f, Color.WHITE, true))
                    b.gravity = Gravity.CENTER
                    b.background = Ui.chunky(Tn.CORAL, dpf(26f), dpf(4f))
                    b.setPadding(0, dp(14), 0, dp(18))
                    press(b) { dlg?.dismiss() }
                    panel.addView(b, LinearLayout.LayoutParams(-1, -2))
                }
                dlg?.show()
            }
        } catch (e: Exception) { }
    }
}
