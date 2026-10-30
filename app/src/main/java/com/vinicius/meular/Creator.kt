package com.vinicius.meular

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.view.View
import android.widget.FrameLayout
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/** Tela de criação de personagem (estilo The Sims): painel por cima do palco 3D. */
class CreatorUi(
    ctx: Context,
    private val st: GameState,
    private val game: GameView,
    private val onDone: () -> Unit
) : FrameLayout(ctx) {

    private val d = ctx.resources.displayMetrics.density
    private fun dp(v: Int) = (v * d).toInt()
    private fun dpf(v: Float) = v * d

    private var tab = 0
    private val tabs = listOf("Corpo", "Rosto", "Cabelo", "Roupa")
    private val body = LinearLayout(ctx)
    private val tabRow = LinearLayout(ctx)
    private val genM = TextView(ctx)
    private val genF = TextView(ctx)
    private val panel = LinearLayout(ctx)
    private val top = LinearLayout(ctx)
    private val av get() = st.avatar

    init {
        // topo: gênero + dado
        top.orientation = LinearLayout.HORIZONTAL
        top.gravity = Gravity.CENTER_VERTICAL
        top.setPadding(dp(12), dp(36), dp(12), dp(4))
        styleGender(genM, "Masculino"); styleGender(genF, "Feminino")
        genM.setOnClickListener { setGender(false) }
        genF.setOnClickListener { setGender(true) }
        val seg = LinearLayout(ctx)
        seg.orientation = LinearLayout.HORIZONTAL
        seg.background = Ui.bg(Pal.GLASS, dpf(24f), Color.parseColor("#33FFFFFF"), dpf(1f))
        seg.setPadding(dp(4), dp(4), dp(4), dp(4))
        seg.addView(genM); seg.addView(genF)
        top.addView(seg)
        top.addView(View(ctx), LinearLayout.LayoutParams(0, 1, 1f))
        val dice = FrameLayout(ctx)
        dice.background = Ui.oval(Pal.GLASS, Color.parseColor("#33FFFFFF"), dpf(1f))
        dice.addView(IconView(ctx, Ic.DICE), FrameLayout.LayoutParams(dp(24), dp(24), Gravity.CENTER))
        dice.setOnClickListener { sortear() }
        top.addView(dice, LinearLayout.LayoutParams(dp(46), dp(46)))
        addView(top, LayoutParams(-1, -2, Gravity.TOP))

        // base: abas + opções + pronto
        panel.orientation = LinearLayout.VERTICAL
        panel.background = Ui.topSheet(Pal.BG, dpf(28f))
        panel.setPadding(dp(14), dp(12), dp(14), dp(12))
        tabRow.orientation = LinearLayout.HORIZONTAL
        val hs = HorizontalScrollView(ctx)
        hs.isHorizontalScrollBarEnabled = false
        hs.addView(tabRow)
        panel.addView(hs, LinearLayout.LayoutParams(-1, -2).also { it.bottomMargin = dp(8) })
        val sc = ScrollView(ctx)
        sc.isVerticalScrollBarEnabled = false
        body.orientation = LinearLayout.VERTICAL
        sc.addView(body)
        panel.addView(sc, LinearLayout.LayoutParams(-1, dp(190)))
        val ok = TextView(ctx)
        ok.text = "Pronto"
        ok.textSize = 18f
        ok.typeface = Ui.BOLD
        ok.setTextColor(Color.WHITE)
        ok.gravity = Gravity.CENTER
        ok.background = Ui.bg(Pal.GREEN, dpf(22f))
        ok.setOnClickListener { st.avatarSet = true; st.save(); onDone() }
        panel.addView(ok, LinearLayout.LayoutParams(-1, dp(50)).also { it.topMargin = dp(10) })
        addView(panel, LayoutParams(-1, -2, Gravity.BOTTOM))

        refresh()
    }

    fun setInsets(topPx: Int, bottomPx: Int) {
        top.setPadding(dp(12), topPx + dp(10), dp(12), dp(4))
        panel.setPadding(dp(14), dp(12), dp(14), dp(12) + bottomPx)
    }

    fun open() { tab = 0; refresh(); camera() }

    private fun styleGender(t: TextView, s: String) {
        t.text = s; t.textSize = 14f; t.typeface = Ui.BOLD
        t.gravity = Gravity.CENTER
        t.setPadding(dp(16), dp(9), dp(16), dp(9))
    }

    private fun setGender(f: Boolean) {
        if (av.female == f) return
        av.applyGender(f)
        changed()
    }

    private fun sortear() {
        val n = Avatar.random(av.female)
        st.avatar = n
        changed()
    }

    private fun changed() {
        game.r.avDirty = true
        st.avatarSet = true
        st.save()
        refresh()
    }

    private fun camera() {
        // palco a 0,082 de altura: cTargetY é o centro do que aparece (rosto, cabelo ou corpo inteiro)
        when (tab) {
            1 -> { game.r.cTargetDist = 1.25f; game.r.cTargetY = 1.54f }
            2 -> { game.r.cTargetDist = 1.85f; game.r.cTargetY = 1.46f }
            else -> { game.r.cTargetDist = 5.0f; game.r.cTargetY = 0.88f }
        }
    }

    private fun refresh() {
        genM.setTextColor(if (!av.female) Color.WHITE else Pal.SUB)
        genM.background = if (!av.female) Ui.bg(Pal.CORAL, dpf(20f)) else null
        genF.setTextColor(if (av.female) Color.WHITE else Pal.SUB)
        genF.background = if (av.female) Ui.bg(Pal.CORAL, dpf(20f)) else null

        tabRow.removeAllViews()
        for (i in tabs.indices) {
            val t = TextView(context)
            t.text = tabs[i]; t.textSize = 15f; t.typeface = Ui.BOLD
            t.setPadding(dp(16), dp(8), dp(16), dp(8))
            val sel = i == tab
            t.setTextColor(if (sel) Color.WHITE else Pal.SUB)
            t.background = Ui.bg(if (sel) Pal.CORAL else Pal.CARD, dpf(18f))
            t.setOnClickListener { tab = i; camera(); refresh() }
            tabRow.addView(t, LinearLayout.LayoutParams(-2, -2).also { it.rightMargin = dp(8) })
        }

        body.removeAllViews()
        when (tab) {
            0 -> {
                label("Tom de pele"); swatches(AvaPal.SKIN, av.skin) { av.skin = it }
                label("Porte"); chips(AvaPal.BODY_N, av.body) { av.body = it }
            }
            1 -> {
                label("Olhos"); swatches(AvaPal.EYE, av.eye) { av.eye = it }
                label("Barba"); chips(AvaPal.BEARD_N, av.beard) { av.beard = it }
                label("Óculos"); chips(AvaPal.GLASS_N, av.glasses) { av.glasses = it }
            }
            2 -> {
                label("Estilo"); chips(AvaPal.HAIR_N, av.hair) { av.hair = it }
                label("Cor do cabelo"); swatches(AvaPal.HAIR, av.hairC) { av.hairC = it }
            }
            else -> {
                label("Parte de cima"); chips(AvaPal.TOP_N, av.top) { av.top = it }
                swatches(AvaPal.TOP, av.topC) { av.topC = it }
                label("Parte de baixo"); chips(AvaPal.BOT_N, av.bottom) { av.bottom = it }
                swatches(AvaPal.BOT, av.botC) { av.botC = it }
                label("Sapatos"); swatches(AvaPal.SHOE, av.shoeC) { av.shoeC = it }
            }
        }
    }

    private fun label(s: String) {
        val t = TextView(context)
        t.text = s; t.textSize = 13f; t.typeface = Ui.BOLD; t.setTextColor(Pal.SUB)
        body.addView(t, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(6); it.bottomMargin = dp(6) })
    }

    private fun chips(names: List<String>, sel: Int, set: (Int) -> Unit) {
        val row = LinearLayout(context)
        row.orientation = LinearLayout.HORIZONTAL
        for (i in names.indices) {
            val t = TextView(context)
            t.text = names[i]; t.textSize = 14f; t.typeface = Ui.MED
            t.setPadding(dp(14), dp(8), dp(14), dp(8))
            val on = i == sel
            t.setTextColor(if (on) Color.WHITE else Pal.TEXT)
            t.background = Ui.bg(if (on) Pal.CORAL2 else Pal.CARD, dpf(16f))
            t.setOnClickListener { set(i); changed() }
            row.addView(t, LinearLayout.LayoutParams(-2, -2).also { it.rightMargin = dp(8) })
        }
        val hs = HorizontalScrollView(context)
        hs.isHorizontalScrollBarEnabled = false
        hs.addView(row)
        body.addView(hs, LinearLayout.LayoutParams(-1, -2))
    }

    private fun swatches(cols: IntArray, sel: Int, set: (Int) -> Unit) {
        val row = LinearLayout(context)
        row.orientation = LinearLayout.HORIZONTAL
        for (i in cols.indices) {
            val v = View(context)
            val on = i == sel
            v.background = Ui.oval(cols[i], if (on) Color.WHITE else Color.parseColor("#44FFFFFF"), dpf(if (on) 3f else 1f))
            v.setOnClickListener { set(i); changed() }
            row.addView(v, LinearLayout.LayoutParams(dp(36), dp(36)).also { it.rightMargin = dp(10) })
        }
        val hs = HorizontalScrollView(context)
        hs.isHorizontalScrollBarEnabled = false
        hs.addView(row)
        body.addView(hs, LinearLayout.LayoutParams(-1, -2).also { it.bottomMargin = dp(4) })
    }
}
