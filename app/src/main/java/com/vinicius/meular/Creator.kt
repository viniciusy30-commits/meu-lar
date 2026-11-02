package com.vinicius.meular

import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.view.Gravity
import android.view.View
import android.widget.FrameLayout
import android.widget.HorizontalScrollView
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.SeekBar
import android.widget.TextView

/**
 * Etapa 6 — tela do criador estilo The Sims.
 * Em cima: o personagem 3D; a câmera dá zoom e gira para a parte que está sendo editada
 * (cabelo de trás = vista de costas, rosto = close, sapatos = pés, etc.).
 * Embaixo: categorias, sub-abas, grade de miniaturas (ícones do próprio pack) e cores.
 */
class CreatorUi(
    ctx: Context,
    private val st: GameState,
    private val game: GameView,
    private val onDone: () -> Unit
) : FrameLayout(ctx) {

    private val d = ctx.resources.displayMetrics.density
    private fun dp(v: Int) = (v * d).toInt()
    private fun dpf(v: Float) = v * d

    private class Style(
        val key: String,
        val ids: List<String>,
        val names: List<String>,
        val get: (Avatar) -> Int,
        val set: (Avatar, Int) -> Unit
    )

    private class Sub(
        val name: String,
        val yaw: Float,
        val style: Style?,
        val colors: IntArray,
        val dist: Float = Float.NaN,
        val y: Float = Float.NaN,
        val sl: Int = 0   // Etapa 7: 1 = controles de proporção do corpo, 2 = controles do formato do rosto, 3 = expressões, 4 = escolha da base
    )

    private class Cat(val name: String, val dist: Float, val y: Float, val subs: List<Sub>)

    private val PI_F = Math.PI.toFloat()

    // Alturas reais: personagem ~1,55 m (com chifres ~1,65); olhos ~1,45; pés em 0. Altura visível = 0,61 x distância.
    private val cats: List<Cat> = listOf(
        Cat("Base", 3.5f, 0.82f, listOf(
            Sub("Masculino / Feminino", 0.3f, null, intArrayOf(0), sl = 4)
        )),
        Cat("Corpo", 3.5f, 0.82f, listOf(
            Sub("Pele", 0.3f, null, intArrayOf(0)),
            Sub("Proporções", 0.3f, null, intArrayOf(), sl = 1)
        )),
        Cat("Cabelo", 2.3f, 1.12f, listOf(
            Sub("Atrás", PI_F, Style("hairBack", AvaPal.HB_IDS, AvaPal.HB_N, { a -> a.hb }, { a, i -> a.hb = i }), intArrayOf(2, 3)),
            Sub("Frente", 0f, Style("hairFront", AvaPal.HF_IDS, AvaPal.HF_N, { a -> a.hf }, { a, i -> a.hf = i }), intArrayOf(2, 3), 1.6f, 1.33f)
        )),
        Cat("Rosto", 1.3f, 1.43f, listOf(
            Sub("Formato", 0f, null, intArrayOf(), sl = 2),
            Sub("Olhos", 0f, null, intArrayOf(1)),
            Sub("Lábios", 0f, null, intArrayOf(12)),
            Sub("Expressão", 0f, null, intArrayOf(), sl = 3),
            Sub("Óculos", 0f, Style("glasses", AvaPal.GS_IDS, AvaPal.GS_N, { a -> a.cgls }, { a, i -> a.cgls = i }), intArrayOf(10, 11)),
            Sub("Barba", 0f, Style("beard", AvaPal.BD_IDS, AvaPal.BD_N, { a -> a.cbrd }, { a, i -> a.cbrd = i }), intArrayOf(2, 3))
        )),
        Cat("Roupa", 2.3f, 1.12f, listOf(
            Sub("Blusa", 0.3f, Style("top", AvaPal.CT_IDS, AvaPal.CT_N, { a -> a.ctop }, { a, i -> a.ctop = i }), intArrayOf(4, 5)),
            Sub("Calça/saia", 0.3f, Style("bottom", AvaPal.CB_IDS, AvaPal.CB_N, { a -> a.cbot }, { a, i -> a.cbot = i }), intArrayOf(6, 9), 2.6f, 0.68f),
            Sub("Vestido", 0.3f, Style("overall", AvaPal.CO_IDS, AvaPal.CO_N, { a -> a.cov }, { a, i -> a.cov = i }), intArrayOf(4, 5, 6, 9), 3.2f, 0.85f)
        )),
        Cat("Sapatos", 1.7f, 0.28f, listOf(
            Sub("Sapatos", 0.3f, Style("feet", AvaPal.FT_IDS, AvaPal.FT_N, { a -> a.cfeet }, { a, i -> a.cfeet = i }), intArrayOf(7, 8))
        )),
        Cat("Acessórios", 1.6f, 1.42f, listOf(
            Sub("Chapéu", 0.3f, Style("hat", AvaPal.HT_IDS, AvaPal.HT_N, { a -> a.chat }, { a, i -> a.chat = i }), intArrayOf(10, 11)),
            Sub("Cabeça", 0.3f, Style("headAcc", AvaPal.HA_IDS, AvaPal.HA_N, { a -> a.chac }, { a, i -> a.chac = i }), intArrayOf(10, 11)),
            Sub("Luvas", 0.3f, Style("gloves", AvaPal.GV_IDS, AvaPal.GV_N, { a -> a.cglove }, { a, i -> a.cglove = i }), intArrayOf(10, 11), 2.4f, 0.8f)
        ))
    )

    private val CAT_ICONS = intArrayOf(Ic.BASE, Ic.BODY, Ic.HAIR, Ic.FACE, Ic.SHIRT, Ic.SHOE, Ic.HAT)

    private var cat = 0
    private var sub = 0

    private val rail = LinearLayout(ctx)
    private val subRow = LinearLayout(ctx)
    private val body = LinearLayout(ctx)
    private val scroll = ScrollView(ctx)
    private val panel = LinearLayout(ctx)
    private val titleTv = TextView(ctx)
    private val stageTitle = TextView(ctx)
    private val stageBtns = LinearLayout(ctx)
    private val icons = HashMap<String, Bitmap?>()

    private fun grad(c1: Int, c2: Int, r: Float, stroke: Int = 0, sw: Float = 0f): GradientDrawable {
        val g = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(c1, c2))
        g.cornerRadius = r
        if (stroke != 0) g.setStroke(sw.toInt().coerceAtLeast(1), stroke)
        return g
    }

    init {
        // título sobre o palco (esquerda)
        stageTitle.text = "Meu personagem"
        stageTitle.textSize = 18f
        stageTitle.typeface = Ui.BOLD
        stageTitle.setTextColor(Pal.TEXT)
        stageTitle.setShadowLayer(dpf(2f), 0f, dpf(1f), 0x99000000.toInt())
        stageTitle.setPadding(dp(18), dp(9), dp(20), dp(13))
        stageTitle.background = Ui.panel(dpf(22f), dpf(3f), dpf(1.3f))
        addView(stageTitle, LayoutParams(-2, -2, Gravity.TOP or Gravity.START).also { it.setMargins(dp(20), dp(14), 0, 0) })

        // botões de girar (esquerda embaixo)
        stageBtns.orientation = LinearLayout.HORIZONTAL
        stageBtns.gravity = Gravity.CENTER_VERTICAL
        stageBtns.addView(roundBtn("\u21BA") { game.r.autoSpin = false; game.r.cTargetYaw = game.r.cyaw - 1.0f }, LinearLayout.LayoutParams(dp(52), dp(52)).also { it.rightMargin = dp(12) })
        stageBtns.addView(roundBtn("\u21BB") { game.r.autoSpin = false; game.r.cTargetYaw = game.r.cyaw + 1.0f }, LinearLayout.LayoutParams(dp(52), dp(52)))
        addView(stageBtns, LayoutParams(-2, -2, Gravity.BOTTOM or Gravity.START).also { it.setMargins(dp(20), 0, 0, dp(18)) })

        // painel da direita
        panel.orientation = LinearLayout.HORIZONTAL
        val pbg = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(0xF533275A.toInt(), 0xF5231A38.toInt()))
        pbg.cornerRadii = floatArrayOf(dpf(30f), dpf(30f), 0f, 0f, 0f, 0f, dpf(30f), dpf(30f))
        pbg.setStroke(dpf(2f).toInt(), Pal.LINE)
        panel.background = pbg
        panel.setPadding(dp(8), dp(10), dp(10), dp(10))

        rail.orientation = LinearLayout.VERTICAL
        rail.gravity = Gravity.CENTER_HORIZONTAL
        val railScroll = ScrollView(ctx)
        railScroll.isVerticalScrollBarEnabled = false
        railScroll.addView(rail)
        panel.addView(railScroll, LinearLayout.LayoutParams(dp(74), -1))

        val content = LinearLayout(ctx)
        content.orientation = LinearLayout.VERTICAL
        content.setPadding(dp(8), dp(4), 0, 0)
        titleTv.textSize = 24f
        titleTv.typeface = Ui.BOLD
        titleTv.setTextColor(Pal.TEXT)
        titleTv.setShadowLayer(dpf(2f), 0f, dpf(1f), 0x99000000.toInt())
        content.addView(titleTv, LinearLayout.LayoutParams(-2, -2).also { it.leftMargin = dp(4) })
        subRow.orientation = LinearLayout.HORIZONTAL
        val hs2 = HorizontalScrollView(ctx)
        hs2.isHorizontalScrollBarEnabled = false
        hs2.addView(subRow)
        content.addView(hs2, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(8) })
        body.orientation = LinearLayout.VERTICAL
        scroll.isVerticalScrollBarEnabled = false
        scroll.addView(body)
        content.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f).also { it.topMargin = dp(8) })
        val ok = TextView(ctx)
        ok.text = "Pronto  \u2713"
        ok.textSize = 19f
        ok.typeface = Ui.BOLD
        ok.setTextColor(Color.WHITE)
        ok.setShadowLayer(dpf(1.5f), 0f, dpf(1f), 0x99000000.toInt())
        ok.gravity = Gravity.CENTER
        ok.setPadding(0, 0, 0, dp(4))
        ok.background = Ui.chunky(Tn.MINT, dpf(26f), dpf(4f))
        ok.setOnClickListener { CuteChar.setExpression(-1); exprSel = -1; st.avatarSet = true; st.save(); onDone() }
        content.addView(ok, LinearLayout.LayoutParams(-1, dp(56)).also { it.topMargin = dp(8) })
        panel.addView(content, LinearLayout.LayoutParams(0, -1, 1f))
        addView(panel, LayoutParams(dp(380), -1, Gravity.END))
        refresh(false)
    }

    private fun roundBtn(text: String, click: () -> Unit): TextView {
        val t = TextView(context)
        t.text = text
        t.textSize = 24f
        t.setTextColor(Pal.TEXT)
        t.gravity = Gravity.CENTER
        t.setPadding(0, 0, 0, dp(3))
        t.background = Ui.panel(dpf(52f), dpf(3f), dpf(1.3f))
        t.setOnClickListener { click() }
        return t
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        if (w <= 0) return
        val pw = (w * 0.46f).toInt().coerceIn(dp(330), dp(480))
        val lp = panel.layoutParams
        if (lp.width != pw) { lp.width = pw; panel.layoutParams = lp }
        // personagem no centro da parte livre à esquerda do painel
        game.r.cShift = 0f
        game.r.cShiftX = -(pw.toFloat() / w.toFloat())
    }

    fun setInsets(l: Int, t: Int, r: Int, b: Int) {
        panel.setPadding(dp(8), dp(10) + t, dp(10) + r, dp(10) + b)
        (stageTitle.layoutParams as LayoutParams).setMargins(dp(20) + l, dp(14) + t, 0, 0)
        (stageBtns.layoutParams as LayoutParams).setMargins(dp(20) + l, 0, 0, dp(18) + b)
        stageTitle.requestLayout(); stageBtns.requestLayout()
    }

    fun open() {
        cat = 0; sub = 0
        exprSel = -1
        CuteChar.setExpression(-1)
        game.r.autoSpin = false
        refresh(false)
        camera()
    }

    private fun camera() {
        val c = cats[cat]
        val s = c.subs[sub]
        game.r.autoSpin = false
        game.r.cTargetDist = if (s.dist.isNaN()) c.dist else s.dist
        game.r.cTargetY = if (s.y.isNaN()) c.y else s.y
        game.r.cTargetYaw = s.yaw
    }

    private fun refresh(keepScroll: Boolean) {
        val av = st.avatar
        rail.removeAllViews()
        for (i in cats.indices) {
            val on = i == cat
            val b = LinearLayout(context)
            b.orientation = LinearLayout.VERTICAL
            b.gravity = Gravity.CENTER
            b.setPadding(0, 0, 0, dp(3))
            b.background = Ui.chunky(if (on) Tn.CORAL else Tn.GHOST, dpf(20f), dpf(3f), on)
            b.addView(IconView(context, CAT_ICONS[i], if (on) Color.WHITE else Pal.SUB, if (on) Tn.CORAL.edge else Tn.GHOST.edge), LinearLayout.LayoutParams(dp(28), dp(28)))
            val n = TextView(context)
            n.text = cats[i].name
            n.textSize = 10.5f
            n.typeface = Ui.BOLD
            n.maxLines = 1
            n.setTextColor(if (on) Color.WHITE else Pal.SUB)
            b.addView(n, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(2) })
            b.setOnClickListener { cat = i; sub = 0; refresh(false); camera() }
            rail.addView(b, LinearLayout.LayoutParams(dp(66), dp(66)).also { it.bottomMargin = dp(8) })
        }

        val c = cats[cat]
        titleTv.text = c.name
        subRow.removeAllViews()
        for (i in c.subs.indices) {
            val t = TextView(context)
            t.text = c.subs[i].name
            t.textSize = 13f
            t.typeface = Ui.BOLD
            t.gravity = Gravity.CENTER
            t.setPadding(dp(16), 0, dp(16), dp(3))
            val on = i == sub
            t.setTextColor(if (on) Color.WHITE else Pal.SUB)
            t.background = Ui.chunky(if (on) Tn.CORAL else Tn.GHOST, dpf(18f), dpf(3f), on)
            t.setOnClickListener { sub = i; refresh(false); camera() }
            subRow.addView(t, LinearLayout.LayoutParams(-2, dp(36)).also { it.rightMargin = dp(8) })
        }
        (subRow.parent as View).visibility = if (c.subs.size > 1) View.VISIBLE else View.GONE

        val keep = scroll.scrollY
        body.removeAllViews()
        val s = c.subs[sub]
        val stl = s.style
        if (stl != null) grid(stl, stl.get(av))
        if (s.sl == 4) baseChoice() else if (s.sl == 3) expressions() else if (s.sl != 0) sliders(s.sl)
        for (slot in s.colors) colorRow(slot)
        body.addView(View(context), LinearLayout.LayoutParams(-1, dp(8)))
        scroll.post { scroll.scrollTo(0, if (keepScroll) keep else 0) }
    }

    private fun icon(key: String): Bitmap? = icons.getOrPut(key) {
        try {
            context.assets.open("cute/icons/$key.png").use { BitmapFactory.decodeStream(it) }
        } catch (e: Exception) { null }
    }

    private fun grid(stl: Style, cur: Int) {
        val cols = 3
        var row: LinearLayout? = null
        for (i in stl.ids.indices) {
            if (i % cols == 0) {
                row = LinearLayout(context)
                row.orientation = LinearLayout.HORIZONTAL
                body.addView(row, LinearLayout.LayoutParams(-1, -2))
            }
            row!!.addView(tile(stl, i, i == cur), LinearLayout.LayoutParams(0, dp(120), 1f).also {
                it.setMargins(dp(4), dp(4), dp(4), dp(4))
            })
        }
        val rest = (cols - stl.ids.size % cols) % cols
        for (k in 0 until rest) {
            row!!.addView(View(context), LinearLayout.LayoutParams(0, dp(120), 1f).also {
                it.setMargins(dp(4), dp(4), dp(4), dp(4))
            })
        }
    }

    private fun tile(stl: Style, i: Int, sel: Boolean): View {
        val f = FrameLayout(context)
        f.background = if (sel) Ui.chunky(Tn.CARD, dpf(20f), dpf(3f), false, 0xFF55DDA3.toInt(), dpf(2.5f))
                       else Ui.chunky(Tn.CARD, dpf(20f), dpf(3f), false, 0x33FFFFFF, dpf(1f))
        val id = stl.ids[i]
        val bmp = if (id.isEmpty()) null else icon((stl.key + "_" + id).lowercase())
        if (bmp != null) {
            val iv = ImageView(context)
            iv.scaleType = ImageView.ScaleType.FIT_CENTER
            iv.setImageBitmap(bmp)
            f.addView(iv, LayoutParams(-1, dp(78), Gravity.TOP).also { it.topMargin = dp(8) })
        } else {
            val x = TextView(context)
            x.text = if (id.isEmpty()) "\u2205" else "?"
            x.textSize = 30f
            x.setTextColor(Pal.SUB)
            x.gravity = Gravity.CENTER
            f.addView(x, LayoutParams(-1, dp(78), Gravity.TOP).also { it.topMargin = dp(8) })
        }
        val n = TextView(context)
        n.text = stl.names[i]
        n.textSize = 11f
        n.typeface = Ui.MED
        n.maxLines = 2
        n.gravity = Gravity.CENTER
        n.setTextColor(if (sel) Color.WHITE else Pal.SUB)
        n.setPadding(dp(4), 0, dp(4), dp(5))
        n.setPadding(dp(4), 0, dp(4), dp(8))
        f.addView(n, LayoutParams(-1, dp(32), Gravity.BOTTOM))
        if (sel) {
            val ck = TextView(context)
            ck.text = "\u2713"
            ck.textSize = 12f
            ck.typeface = Ui.BOLD
            ck.setTextColor(Color.WHITE)
            ck.gravity = Gravity.CENTER
            ck.background = Ui.oval(0xFF25AD7B.toInt())
            f.addView(ck, LayoutParams(dp(22), dp(22), Gravity.TOP or Gravity.END).also { it.setMargins(0, dp(6), dp(6), 0) })
        }
        f.setOnClickListener { pickStyle(stl, i) }
        return f
    }

    private fun pickStyle(stl: Style, i: Int) {
        val a = st.avatar
        stl.set(a, i)
        CuteChar.setWear(a.wearKeys())
        st.save()
        refresh(true)
    }

    private fun colorRow(slot: Int) {
        val av = st.avatar
        val cur = av.cc[slot]
        val head = LinearLayout(context)
        head.orientation = LinearLayout.HORIZONTAL
        head.gravity = Gravity.CENTER_VERTICAL
        val lab = TextView(context)
        lab.text = "Cor: " + CuteColor.SLOT_NAMES[slot]
        lab.textSize = 13f
        lab.typeface = Ui.BOLD
        lab.setTextColor(Pal.TEXT)
        head.addView(lab, LinearLayout.LayoutParams(0, -2, 1f))
        val orig = TextView(context)
        orig.text = "Original"
        orig.textSize = 12f
        orig.typeface = Ui.BOLD
        orig.setTextColor(Color.WHITE)
        orig.gravity = Gravity.CENTER
        orig.setPadding(dp(14), 0, dp(14), 0)
        orig.setPadding(dp(14), 0, dp(14), dp(2))
        orig.background = Ui.chunky(Tn.GHOST, dpf(15f), dpf(2f), false, if (cur < 0) Color.WHITE else 0, dpf(2.5f))
        orig.setOnClickListener { pickColor(slot, -1) }
        head.addView(orig, LinearLayout.LayoutParams(-2, dp(32)))
        body.addView(head, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(12); it.bottomMargin = dp(6); it.leftMargin = dp(4); it.rightMargin = dp(4) })

        val pal = CuteColor.palette(slot)
        val cols = 6
        var row: LinearLayout? = null
        for (i in pal.indices) {
            if (i % cols == 0) {
                row = LinearLayout(context)
                row.orientation = LinearLayout.HORIZONTAL
                body.addView(row, LinearLayout.LayoutParams(-1, -2))
            }
            val cell = FrameLayout(context)
            val v = View(context)
            val on = i == cur
            v.background = Ui.oval(pal[i], if (on) Pal.TEXT else 0x66FFFFFF, if (on) dpf(3.5f) else dpf(1f))
            v.setOnClickListener { pickColor(slot, i) }
            cell.addView(v, LayoutParams(dp(38), dp(38), Gravity.CENTER))
            row!!.addView(cell, LinearLayout.LayoutParams(0, dp(46), 1f))
        }
        val rest = (cols - pal.size % cols) % cols
        for (k in 0 until rest) row!!.addView(View(context), LinearLayout.LayoutParams(0, dp(46), 1f))
    }

    private fun pct(v: Int): String = if (v > 0) "+$v%" else "$v%"

    /** Etapa 7: controles deslizantes (-100..100) de proporção do corpo (kind 1) ou formato do rosto (kind 2). */
    private fun sliders(kind: Int) {
        val av = st.avatar
        val names = if (kind == 1) BodyMorph.BODY_NAMES else BodyMorph.FACE_NAMES
        val arr = if (kind == 1) av.bs else av.fs
        if (kind == 1) {
            // Etapa 13: sexo do corpo (feminino = corpo original; masculino = ombros largos, peito reto, quadril estreito, mais alto)
            val sexRow = LinearLayout(context)
            sexRow.orientation = LinearLayout.HORIZONTAL
            for ((nome, m) in listOf("Feminino" to false, "Masculino" to true)) {
                val on = av.masc == m
                val t = TextView(context)
                t.text = nome
                t.textSize = 14f
                t.typeface = Ui.BOLD
                t.gravity = Gravity.CENTER
                t.setTextColor(if (on) Color.WHITE else Pal.SUB)
                t.setPadding(0, 0, 0, dp(3))
                t.background = Ui.chunky(if (on) Tn.CORAL else Tn.GHOST, dpf(20f), dpf(3f), on)
                t.setOnClickListener {
                    if (av.masc != m) {
                        av.masc = m
                        CuteChar.setShape(av.bs, av.fs, av.masc)
                        st.save()
                        refresh(true)
                    }
                }
                sexRow.addView(t, LinearLayout.LayoutParams(0, dp(44), 1f).also { it.rightMargin = dp(6) })
            }
            body.addView(sexRow, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(6); it.leftMargin = dp(4); it.rightMargin = dp(4) })
        }
        val reset = TextView(context)
        reset.text = "Zerar tudo"
        reset.textSize = 12f
        reset.typeface = Ui.BOLD
        reset.setTextColor(Color.WHITE)
        reset.gravity = Gravity.CENTER
        reset.setPadding(dp(14), 0, dp(14), dp(2))
        reset.background = Ui.chunky(Tn.GHOST, dpf(15f), dpf(2f), false)
        reset.setOnClickListener {
            java.util.Arrays.fill(arr, 0)
            CuteChar.setShape(av.bs, av.fs, av.masc)
            st.save()
            refresh(true)
        }
        body.addView(reset, LinearLayout.LayoutParams(-2, dp(34)).also { it.topMargin = dp(6); it.leftMargin = dp(4) })
        for (i in names.indices) {
            val head = LinearLayout(context)
            head.orientation = LinearLayout.HORIZONTAL
            head.gravity = Gravity.CENTER_VERTICAL
            val lab = TextView(context)
            lab.text = names[i]
            lab.textSize = 13f
            lab.typeface = Ui.BOLD
            lab.setTextColor(Pal.TEXT)
            head.addView(lab, LinearLayout.LayoutParams(0, -2, 1f))
            val value = TextView(context)
            value.text = pct(arr[i])
            value.textSize = 12f
            value.typeface = Ui.MED
            value.setTextColor(Pal.SUB)
            head.addView(value, LinearLayout.LayoutParams(-2, -2))
            body.addView(head, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(12); it.leftMargin = dp(4); it.rightMargin = dp(4) })
            val sb = SeekBar(context)
            sb.max = 200
            sb.progress = arr[i] + 100
            sb.progressTintList = ColorStateList.valueOf(0xFF6DE8B4.toInt())
            sb.thumbTintList = ColorStateList.valueOf(0xFFFFF4E6.toInt())
            sb.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(s: SeekBar?, p: Int, fromUser: Boolean) {
                    if (!fromUser) return
                    var v = p - 100
                    if (v in -4..4) { v = 0; s?.progress = 100 }   // ímã no zero
                    arr[i] = v
                    value.text = pct(v)
                    CuteChar.setShape(av.bs, av.fs, av.masc)
                }
                override fun onStartTrackingTouch(s: SeekBar?) { s?.parent?.requestDisallowInterceptTouchEvent(true) }
                override fun onStopTrackingTouch(s: SeekBar?) { st.save() }
            })
            body.addView(sb, LinearLayout.LayoutParams(-1, dp(36)))
        }
    }

    private var exprSel = -1

    /** Etapa 14: escolha da base. Recomeça o personagem do zero (roupa de baixo, cabelo simples, proporções zeradas). */
    private fun baseChoice() {
        val av = st.avatar
        val info = TextView(context)
        info.text = "Escolha a base e monte seu personagem do zero. Trocar a base apaga roupas, cabelo e ajustes (mantém pele e olhos)."
        info.textSize = 12f
        info.setTextColor(Pal.SUB)
        body.addView(info, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(6); it.leftMargin = dp(4); it.rightMargin = dp(4) })
        for ((nome, m) in listOf("Masculino" to true, "Feminino" to false)) {
            val on = av.masc == m
            val t = TextView(context)
            t.text = (if (m) "\u2642  " else "\u2640  ") + nome + (if (on) "  \u2713" else "")
            t.textSize = 18f
            t.typeface = Ui.BOLD
            t.gravity = Gravity.CENTER
            t.setTextColor(if (on) Color.WHITE else Pal.SUB)
            t.setPadding(0, 0, 0, dp(4))
            t.background = Ui.chunky(if (on) Tn.CORAL else Tn.GHOST, dpf(26f), dpf(4f), on)
            t.setOnClickListener {
                av.applyBase(m)
                CuteColor.setColors(av.cc)
                CuteChar.setWear(av.wearKeys())
                CuteChar.setShape(av.bs, av.fs, av.masc)
                st.save()
                refresh(true)
            }
            body.addView(t, LinearLayout.LayoutParams(-1, dp(64)).also { it.topMargin = dp(12); it.leftMargin = dp(4); it.rightMargin = dp(4) })
        }
    }

    /** Etapa 8: testar expressões do rosto (só visualização; o jogo continua piscando e fazendo cara de surpresa no pulo). */
    private fun expressions() {
        val names = listOf("Automático", "Neutra", "Feliz", "Triste", "Brava", "Surpresa")
        val code = intArrayOf(-1, 0, 1, 2, 3, 4)
        val row = LinearLayout(context)
        row.orientation = LinearLayout.VERTICAL
        for (i in names.indices) {
            val on = exprSel == code[i]
            val t = TextView(context)
            t.text = names[i]
            t.textSize = 14f
            t.typeface = Ui.BOLD
            t.gravity = Gravity.CENTER
            t.setTextColor(if (on) Color.WHITE else Pal.SUB)
            t.setPadding(0, 0, 0, dp(3))
            t.background = Ui.chunky(if (on) Tn.CORAL else Tn.GHOST, dpf(20f), dpf(3f), on)
            t.setOnClickListener {
                exprSel = code[i]
                CuteChar.setExpression(exprSel)
                refresh(true)
            }
            row.addView(t, LinearLayout.LayoutParams(-1, dp(40)).also { it.topMargin = dp(8); it.leftMargin = dp(4); it.rightMargin = dp(4) })
        }
        body.addView(row, LinearLayout.LayoutParams(-1, -2))
    }

    private fun pickColor(slot: Int, i: Int) {
        st.avatar.cc[slot] = i
        CuteColor.setColors(st.avatar.cc)
        st.save()
        refresh(true)
    }
}
