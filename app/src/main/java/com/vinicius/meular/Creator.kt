package com.vinicius.meular

import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.drawable.Drawable
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

    private val TXT = 0xFF2F4B5E.toInt()
    private val SUB2 = 0xFF6B8798.toInt()
    private val GREEN = 0xFF6FD06A.toInt()
    private val arc = FrameLayout(ctx)
    private val rings = RingsView(ctx)
    private val subRow = LinearLayout(ctx)
    private val body = LinearLayout(ctx)
    private val scroll = ScrollView(ctx)
    private val panel = LinearLayout(ctx)
    private val titleTv = TextView(ctx)
    private val backBtn = FrameLayout(ctx)
    private val rotL = FrameLayout(ctx)
    private val rotR = FrameLayout(ctx)
    private val diceBar = FrameLayout(ctx)
    private val icons = HashMap<String, Bitmap?>()
    private var insL = 0
    private var insT = 0
    private var insR = 0
    private var insB = 0
    private var arcRad = 0f
    private var arcMidX = 0f
    private var arcCy = 0f

    /** Pílula clara (estilo CAS do Sims 4): ligada = azul-água; desligada = vidro branco. */
    private fun pillBg(on: Boolean, r: Float): Drawable =
        if (on) Ui.frost(r, 0x35B5E0, 0xF4, 0xDC, dpf(1.2f))
        else Ui.frost(r, 0xFFFFFF, 0xC0, 0x90, dpf(1.1f), edge = 0x88A9C6D3.toInt())

    /** Cartão branco (itens, personagens prontos). */
    private fun cardBg(r: Float): Drawable = Ui.frost(r, 0xFFFFFF, 0xF2, 0xE0, dpf(1.1f), edge = 0x66A9C6D3)

    private fun finish() {
        CuteChar.setExpression(-1); exprSel = -1; st.avatarSet = true; st.save(); onDone()
    }

    init {
        // fundo: véu suave azul-água por cima do 3D + anéis translúcidos atrás do personagem
        background = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(0x338CC9EC, 0x00FFFFFF, 0x38E4F8F6))
        addView(rings, LayoutParams(-1, -1))
        addView(arc, LayoutParams(-1, -1))

        // seta de voltar para o jogo (canto superior esquerdo)
        backBtn.background = Ui.frost(0f, 0xFFFFFF, 0xD0, 0xA0, dpf(1.3f), oval = true, edge = 0xEEFFFFFF.toInt())
        backBtn.addView(IconView(ctx, Ic.BACK, 0xFF2E78AE.toInt(), Color.WHITE), LayoutParams(dp(24), dp(24), Gravity.CENTER))
        backBtn.setOnClickListener { finish() }
        addView(backBtn, LayoutParams(dp(46), dp(46), Gravity.TOP or Gravity.START).also { it.setMargins(dp(14), dp(12), 0, 0) })

        // setas grandes de girar, embaixo (como no Sims)
        for ((box, flip, dir) in listOf(Triple(rotL, true, -1.0f), Triple(rotR, false, 1.0f))) {
            val ic = IconView(ctx, Ic.ROTATE, Color.WHITE, Color.WHITE).fancy(0xCC7FB8D8.toInt())
            if (flip) ic.scaleX = -1f
            box.addView(ic, LayoutParams(dp(50), dp(50), Gravity.CENTER))
            box.setOnClickListener { game.r.autoSpin = false; game.r.cTargetYaw = game.r.cyaw + dir }
            addView(box, LayoutParams(dp(60), dp(60), Gravity.BOTTOM or Gravity.START))
        }

        // dado (aleatório) no meio, entre as setas
        diceBar.background = Ui.frost(dpf(21f), 0xFFFFFF, 0xC8, 0x98, dpf(1.2f), edge = 0xEEFFFFFF.toInt())
        diceBar.addView(IconView(ctx, Ic.DICE, 0xFF4B9CC4.toInt(), Color.WHITE), LayoutParams(dp(26), dp(26), Gravity.CENTER))
        diceBar.setOnClickListener { randomize() }
        addView(diceBar, LayoutParams(dp(72), dp(42), Gravity.BOTTOM or Gravity.START))

        // painel da direita: vidro branco flutuante
        panel.orientation = LinearLayout.VERTICAL
        panel.background = Ui.frost(dpf(24f), 0xFFFFFF, 0xEB, 0xD6, dpf(1.3f), edge = 0xFFFFFFFF.toInt())
        panel.setPadding(dp(14), dp(12), dp(14), dp(14))

        titleTv.textSize = 14f
        titleTv.typeface = Ui.BOLD
        titleTv.setTextColor(0xFF2E78AE.toInt())
        titleTv.letterSpacing = 0.14f
        titleTv.gravity = Gravity.CENTER
        panel.addView(titleTv, LinearLayout.LayoutParams(-1, -2))

        subRow.orientation = LinearLayout.HORIZONTAL
        subRow.gravity = Gravity.CENTER_HORIZONTAL
        val hs2 = HorizontalScrollView(ctx)
        hs2.isHorizontalScrollBarEnabled = false
        hs2.isFillViewport = true
        hs2.addView(subRow, FrameLayout.LayoutParams(-2, -2))
        panel.addView(hs2, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(10) })

        body.orientation = LinearLayout.VERTICAL
        scroll.isVerticalScrollBarEnabled = false
        scroll.addView(body)
        panel.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f).also { it.topMargin = dp(8) })

        val ok = TextView(ctx)
        ok.text = "Pronto  \u2713"
        ok.textSize = 17f
        ok.typeface = Ui.BOLD
        ok.setTextColor(Color.WHITE)
        ok.setShadowLayer(dpf(1.5f), 0f, dpf(1f), 0x66000000)
        ok.gravity = Gravity.CENTER
        ok.background = Ui.frost(dpf(24f), 0x34C77B, 0xF6, 0xDC, dpf(1.2f))
        ok.setOnClickListener { finish() }
        panel.addView(ok, LinearLayout.LayoutParams(-1, dp(48)).also { it.topMargin = dp(10) })

        addView(panel, LayoutParams(dp(360), -1, Gravity.END).also { it.setMargins(0, dp(10), dp(10), dp(10)) })
        refresh(false)
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        if (w <= 0) return
        val pw = (w * 0.40f).toInt().coerceIn(dp(320), dp(440))
        val lp = panel.layoutParams
        if (lp.width != pw) { lp.width = pw; panel.layoutParams = lp }
        layoutStage()
    }

    fun setInsets(l: Int, t: Int, r: Int, b: Int) {
        insL = l; insT = t; insR = r; insB = b
        (panel.layoutParams as LayoutParams).setMargins(0, dp(10) + t, dp(10) + r, dp(10) + b)
        panel.requestLayout()
        layoutStage()
    }

    /**
     * Tudo é centralizado na "área do palco" (entre a borda esquerda e o arco de categorias):
     * personagem, anéis, setas de girar e dado ficam no mesmo eixo vertical.
     */
    private fun layoutStage() {
        val w = width
        val h = height
        if (w <= 0 || h <= 0) return
        val pw = panel.layoutParams.width
        val panelL = w - pw - dp(10) - insR
        val half = Math.toRadians(55.0)
        val availH = h - insT - insB - dp(16)
        val btn = dp(50).toFloat()
        arcRad = kotlin.math.min((availH - btn) / (2f * Math.sin(half).toFloat()), dpf(170f))
        arcMidX = (panelL - dp(14) - dp(25)).toFloat()
        arcCy = insT + (h - insT - insB) / 2f
        val arcLeft = arcMidX - arcRad * (1f - Math.cos(half).toFloat()) * 0.9f - btn / 2f
        val stageL = (insL + dp(12)).toFloat()
        val stageR = arcLeft - dp(8)
        val cx = (stageL + stageR) / 2f
        val sw = stageR - stageL

        (backBtn.layoutParams as LayoutParams).setMargins(dp(14) + insL, dp(12) + insT, 0, 0)
        val asz = dp(60)
        val lx = (cx - sw * 0.34f - asz / 2f).toInt()
        val rx = (cx + sw * 0.34f - asz / 2f).toInt()
        (rotL.layoutParams as LayoutParams).setMargins(lx, 0, 0, dp(20) + insB)
        (rotR.layoutParams as LayoutParams).setMargins(rx, 0, 0, dp(20) + insB)
        (diceBar.layoutParams as LayoutParams).setMargins((cx - dp(36)).toInt(), 0, 0, dp(29) + insB)
        backBtn.requestLayout(); rotL.requestLayout(); rotR.requestLayout(); diceBar.requestLayout()

        // personagem no centro da área do palco (um pouco acima, para não ficar atrás das setas)
        game.r.cShift = 0.07f
        game.r.cShiftX = (cx - w / 2f) / (w / 2f)
        rings.cx = cx
        rings.cy = h / 2f - 0.07f * h / 2f
        rings.r = kotlin.math.min(h * 0.44f, sw * 0.48f)
        rings.invalidate()
        buildArc()
    }

    /** Ícones das categorias em arco, ao lado do painel (como no Sims 4), bem espaçados. */
    private fun buildArc() {
        arc.removeAllViews()
        if (arcRad <= 0f) return
        val n = cats.size
        for (i in 0 until n) {
            val on = i == cat
            val ang = Math.toRadians(-55.0 + 110.0 * i / (n - 1))
            val cx = arcMidX - arcRad * (1.0 - Math.cos(ang)).toFloat() * 0.9f
            val cy = arcCy + arcRad * Math.sin(ang).toFloat()
            val sz = dp(if (on) 50 else 42)
            val v = FrameLayout(context)
            v.background = if (on) Ui.frost(0f, 0xFFFFFF, 0xF8, 0xEE, dpf(2.6f), oval = true, edge = GREEN)
                           else Ui.frost(0f, 0xFFFFFF, 0xD0, 0xA8, dpf(1.2f), oval = true, edge = 0xCCFFFFFF.toInt())
            val isz = (sz * 0.56f).toInt()
            v.addView(IconView(context, CAT_ICONS[i], if (on) 0xFF2E9BD1.toInt() else 0xFF6F93A6.toInt(), Color.WHITE), LayoutParams(isz, isz, Gravity.CENTER))
            v.setOnClickListener { cat = i; sub = 0; refresh(false); camera() }
            arc.addView(v, LayoutParams(sz, sz, Gravity.TOP or Gravity.START).also { it.setMargins((cx - sz / 2f).toInt(), (cy - sz / 2f).toInt(), 0, 0) })
        }
    }

    /** Dado: sorteia estilo e cores da aba atual. */
    private fun randomize() {
        val s = cats[cat].subs[sub]
        val av = st.avatar
        val rnd = java.util.Random()
        s.style?.let { stl ->
            if (stl.ids.isNotEmpty()) { stl.set(av, rnd.nextInt(stl.ids.size)); CuteChar.setWear(av.wearKeys()) }
        }
        for (slot in s.colors) {
            val n = CuteColor.palette(slot).size
            if (n > 0) av.cc[slot] = rnd.nextInt(n)
        }
        CuteColor.setColors(av.cc)
        if (s.sl == 1 || s.sl == 2) {
            val arr = if (s.sl == 1) av.bs else av.fs
            for (i in arr.indices) arr[i] = rnd.nextInt(81) - 40
            CuteChar.setShape(av.bs, av.fs, av.masc)
        }
        st.save()
        refresh(true)
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
        game.r.cTargetPitch = 0.10f
        game.r.cPanX = 0f
        game.r.cPanY = 0f
    }

    private fun refresh(keepScroll: Boolean) {
        val av = st.avatar
        buildArc()

        val c = cats[cat]
        titleTv.text = c.name.uppercase()
        subRow.removeAllViews()
        for (i in c.subs.indices) {
            val t = TextView(context)
            t.text = c.subs[i].name
            t.textSize = 13f
            t.typeface = Ui.BOLD
            t.gravity = Gravity.CENTER
            t.setPadding(dp(16), 0, dp(16), 0)
            val on = i == sub
            t.setTextColor(if (on) Color.WHITE else SUB2)
            t.background = pillBg(on, dpf(18f))
            t.setOnClickListener { sub = i; refresh(false); camera() }
            subRow.addView(t, LinearLayout.LayoutParams(-2, dp(36)).also { it.leftMargin = if (i > 0) dp(8) else 0 })
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
            row!!.addView(tile(stl, i, i == cur), LinearLayout.LayoutParams(0, dp(104), 1f).also {
                it.setMargins(dp(4), dp(4), dp(4), dp(4))
            })
        }
        val rest = (cols - stl.ids.size % cols) % cols
        for (k in 0 until rest) {
            row!!.addView(View(context), LinearLayout.LayoutParams(0, dp(104), 1f).also {
                it.setMargins(dp(4), dp(4), dp(4), dp(4))
            })
        }
    }

    private fun tile(stl: Style, i: Int, sel: Boolean): View {
        val f = FrameLayout(context)
        f.background = if (sel) Ui.frost(dpf(14f), 0xFFFFFF, 0xFF, 0xF2, dpf(2.6f), edge = GREEN) else cardBg(dpf(14f))
        val id = stl.ids[i]
        val bmp = if (id.isEmpty()) null else icon((stl.key + "_" + id).lowercase())
        if (bmp != null) {
            val iv = ImageView(context)
            iv.scaleType = ImageView.ScaleType.FIT_CENTER
            iv.setImageBitmap(bmp)
            f.addView(iv, LayoutParams(-1, dp(64), Gravity.TOP).also { it.topMargin = dp(8) })
        } else {
            val x = TextView(context)
            x.text = if (id.isEmpty()) "\u2205" else "?"
            x.textSize = 30f
            x.setTextColor(SUB2)
            x.gravity = Gravity.CENTER
            f.addView(x, LayoutParams(-1, dp(64), Gravity.TOP).also { it.topMargin = dp(8) })
        }
        val n = TextView(context)
        n.text = stl.names[i]
        n.textSize = 11f
        n.typeface = Ui.MED
        n.maxLines = 2
        n.gravity = Gravity.CENTER
        n.setTextColor(if (sel) TXT else SUB2)
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
            ck.background = Ui.oval(0xFF4CBF6B.toInt())
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
        lab.setTextColor(TXT)
        head.addView(lab, LinearLayout.LayoutParams(0, -2, 1f))
        val orig = TextView(context)
        orig.text = "Original"
        orig.textSize = 12f
        orig.typeface = Ui.BOLD
        orig.setTextColor(if (cur < 0) Color.WHITE else TXT)
        orig.gravity = Gravity.CENTER
        orig.setPadding(dp(14), 0, dp(14), 0)
        orig.setPadding(dp(14), 0, dp(14), dp(2))
        orig.background = pillBg(cur < 0, dpf(15f))
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
            v.background = Ui.oval(pal[i], if (on) TXT else 0x33000000, if (on) dpf(3.5f) else dpf(1f))
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
        simSelector()
        if (true) return   // Etapa 44: corpo e rosto vêm do Sims 3; os controles deslizantes antigos não se aplicam
        val av = st.avatar
        val names = if (kind == 1) BodyMorph.BODY_NAMES else BodyMorph.FACE_NAMES
        val arr = if (kind == 1) av.bs else av.fs
        if (kind == 1) {
            // Etapa 13: sexo do corpo (feminino = corpo original; masculino = ombros largos, peito reto, quadril estreito, mais alto)
            val sexRow = LinearLayout(context)
            sexRow.orientation = LinearLayout.HORIZONTAL
            for ((nome, m) in listOf("Feminino" to false, "Masculino" to true)) {
                val on = av.masc == m && !av.julie
                val t = TextView(context)
                t.text = nome
                t.textSize = 14f
                t.typeface = Ui.BOLD
                t.gravity = Gravity.CENTER
                t.setTextColor(if (on) Color.WHITE else SUB2)
                t.setPadding(0, 0, 0, dp(3))
                t.background = pillBg(on, dpf(20f))
                t.setOnClickListener {
                    if (av.masc != m || av.julie) {
                        av.masc = m
                        if (av.julie) { av.julie = false; CuteChar.setWear(av.wearKeys()) }   // Etapa 43: sair da Julie
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
        reset.setTextColor(TXT)
        reset.gravity = Gravity.CENTER
        reset.setPadding(dp(14), 0, dp(14), dp(2))
        reset.background = pillBg(false, dpf(15f))
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
            lab.setTextColor(TXT)
            head.addView(lab, LinearLayout.LayoutParams(0, -2, 1f))
            val value = TextView(context)
            value.text = pct(arr[i])
            value.textSize = 12f
            value.typeface = Ui.MED
            value.setTextColor(SUB2)
            head.addView(value, LinearLayout.LayoutParams(-2, -2))
            body.addView(head, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(12); it.leftMargin = dp(4); it.rightMargin = dp(4) })
            val sb = SeekBar(context)
            sb.max = 200
            sb.progress = arr[i] + 100
            sb.progressTintList = ColorStateList.valueOf(0xFF35B5E0.toInt())
            sb.progressBackgroundTintList = ColorStateList.valueOf(0xFFBFD6E0.toInt())
            sb.thumbTintList = ColorStateList.valueOf(0xFF2E9BD1.toInt())
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

    /** Etapa 44: linha de botões (chips) com um selecionado; [ok] diz se a opção existe. */
    private fun chipRow(titulo: String, nomes: List<String>, sel: Int, ok: (Int) -> Boolean, pick: (Int) -> Unit) {
        val h = TextView(context)
        h.text = titulo
        h.textSize = 13f
        h.typeface = Ui.BOLD
        h.setTextColor(TXT)
        body.addView(h, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(14); it.leftMargin = dp(4) })
        val row = LinearLayout(context)
        row.orientation = LinearLayout.HORIZONTAL
        for (i in nomes.indices) {
            val on = i == sel
            val enabled = ok(i)
            val t = TextView(context)
            t.text = nomes[i]
            t.textSize = 12.5f
            t.typeface = Ui.BOLD
            t.gravity = Gravity.CENTER
            t.setTextColor(if (on) Color.WHITE else SUB2)
            t.alpha = if (enabled) 1f else 0.35f
            t.background = pillBg(on, dpf(18f))
            if (enabled) t.setOnClickListener { pick(i) }
            row.addView(t, LinearLayout.LayoutParams(0, dp(40), 1f).also { it.rightMargin = dp(4) })
        }
        body.addView(row, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(6); it.leftMargin = dp(4); it.rightMargin = dp(4) })
    }

    private fun simApply() {
        val av = st.avatar
        av.simType = av.simTypeFor(av.simAge, av.simType)
        CuteChar.setWear(av.wearKeys())
        CuteChar.setShape(av.bs, av.fs, av.masc)
        st.save()
        refresh(true)
    }

    /** Etapa 44: corpo igual ao The Sims 3 (idade, sexo, tipo de corpo e cabelo). */
    private fun simSelector() {
        val av = st.avatar
        val info = TextView(context)
        info.text = "Corpo e rosto do The Sims 3. As roupas novas entram quando você mandar as peças."
        info.textSize = 12f
        info.setTextColor(SUB2)
        body.addView(info, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(6); it.leftMargin = dp(4); it.rightMargin = dp(4) })
        chipRow("Idade", listOf("Bebê", "Criança", "Jovem", "Adulto", "Idoso"), av.simAge, { true }) { av.simAge = it; simApply() }
        chipRow("Sexo", listOf("\u2640 Feminino", "\u2642 Masculino"), if (av.masc) 1 else 0, { av.simAge >= 2 }) {
            av.masc = it == 1; av.female = !av.masc; simApply()
        }
        val tipos = listOf(0, 1, 3)
        chipRow("Corpo", listOf("Magro", "Normal", "Gordo"), tipos.indexOf(av.simTypeFor(av.simAge, av.simType)), { av.simTypeFor(av.simAge, tipos[it]) == tipos[it] }) {
            av.simType = tipos[it]; simApply()
        }
        chipRow("Cabelo", listOf("Com cabelo", "Careca"), if (av.simHair) 0 else 1, { av.simAge >= 2 }) { av.simHair = it == 0; simApply() }
    }

    /** Etapa 14: escolha da base. Recomeça o personagem do zero (roupa de baixo, cabelo simples, proporções zeradas). */
    private fun baseChoice() {
        val av = st.avatar
        val info = TextView(context)
        info.text = "Escolha a base e monte seu personagem do zero, ou escolha um personagem pronto abaixo. Trocar a base ou o personagem apaga roupas, cabelo e ajustes (mantém a pele)."
        info.textSize = 12f
        info.setTextColor(SUB2)
        body.addView(info, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(6); it.leftMargin = dp(4); it.rightMargin = dp(4) })
        simSelector()
        // Etapa 37: personagens prontos, à parte das bases
        val head = TextView(context)
        head.text = "Personagens prontos"
        head.textSize = 14f
        head.typeface = Ui.BOLD
        head.setTextColor(TXT)
        body.addView(head, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(20); it.leftMargin = dp(4); it.rightMargin = dp(4) })
        for (i in AvaPal.PRESET_N.indices) {
            val card = LinearLayout(context)
            card.orientation = LinearLayout.VERTICAL
            card.setPadding(dp(14), dp(10), dp(14), dp(14))
            card.background = cardBg(dpf(18f))
            val nm = TextView(context)
            nm.text = "\u2605  " + AvaPal.PRESET_N[i]
            nm.textSize = 17f
            nm.typeface = Ui.BOLD
            nm.setTextColor(TXT)
            card.addView(nm, LinearLayout.LayoutParams(-1, -2))
            val ds = TextView(context)
            ds.text = AvaPal.PRESET_D[i]
            ds.textSize = 12f
            ds.setTextColor(SUB2)
            card.addView(ds, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(2) })
            card.setOnClickListener {
                av.applyPreset(i)
                CuteColor.setColors(av.cc)
                CuteChar.setWear(av.wearKeys())
                CuteChar.setShape(av.bs, av.fs, av.masc)
                st.save()
                refresh(true)
            }
            body.addView(card, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(8); it.leftMargin = dp(4); it.rightMargin = dp(4) })
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
            t.setTextColor(if (on) Color.WHITE else SUB2)
            t.setPadding(0, 0, 0, dp(3))
            t.background = pillBg(on, dpf(20f))
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


/** Anéis translúcidos atrás do personagem (como as faixas redondas do Sims 4). */
private class RingsView(ctx: Context) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val d = ctx.resources.displayMetrics.density
    var cx = 0f
    var cy = 0f
    var r = 0f

    override fun onDraw(c: Canvas) {
        if (r <= 0f) return
        p.style = Paint.Style.STROKE
        p.strokeWidth = 26f * d
        p.color = 0x26FFFFFF
        c.drawCircle(cx, cy, r, p)
        p.strokeWidth = 14f * d
        p.color = 0x1CFFFFFF
        c.drawCircle(cx, cy, r * 1.3f, p)
    }
}
