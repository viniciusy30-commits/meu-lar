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

    private class Sub(
        val name: String,
        val yaw: Float,
        val style: Any?,
        val colors: IntArray,
        val dist: Float = Float.NaN,
        val y: Float = Float.NaN,
        val sl: Int = 0,   // 1 = proporções do corpo, 3 = expressões, 4 = escolha da base, 6 = grade de peças (ver [slots])
        val slots: List<String> = emptyList()   // sl = 6: tipos de peça mostrados (top, bottom, overall, feet, hairBack, hat...)
    )

    private class Cat(val name: String, val dist: Float, val y: Float, val subs: List<Sub>)

    private val PI_F = Math.PI.toFloat()

    // Alturas reais: personagem ~1,55 m (com chifres ~1,65); olhos ~1,45; pés em 0. Altura visível = 0,61 x distância.
    private val cats: List<Cat> = listOf(
        Cat("Corpo", 3.5f, 0.82f, listOf(
            Sub("Pele", 0.3f, null, intArrayOf(0)),
            Sub("Proporções", 0.3f, null, intArrayOf(), sl = 1)
        )),
        Cat("Cabelo", 1.6f, 1.36f, listOf(
            Sub("Cabelos", 0.35f, null, intArrayOf(), sl = 6, slots = listOf("hairBack"))
        )),
        Cat("Rosto", 1.3f, 1.43f, listOf(
            Sub("Olhos", 0f, null, intArrayOf(1)),
            Sub("Lábios", 0f, null, intArrayOf(12)),
            Sub("Expressão", 0f, null, intArrayOf(), sl = 3)
        )),
        Cat("Roupas", 2.6f, 0.95f, listOf(
            Sub("Blusas", 0.3f, null, intArrayOf(), dist = 2.0f, y = 1.1f, sl = 6, slots = listOf("top")),
            Sub("Jaquetas", 0.3f, null, intArrayOf(), dist = 2.0f, y = 1.1f, sl = 6, slots = listOf("jacket")),
            Sub("Calças", 0.3f, null, intArrayOf(), dist = 2.4f, y = 0.55f, sl = 6, slots = listOf("bottom")),
            Sub("Inteiras", 0.3f, null, intArrayOf(), sl = 6, slots = listOf("overall"))
        )),
        Cat("Sapatos", 1.7f, 0.22f, listOf(
            Sub("Sapatos", 0.55f, null, intArrayOf(), sl = 6, slots = listOf("feet"))
        )),
        Cat("Acessórios", 1.5f, 1.4f, listOf(
            Sub("Acessórios", 0.3f, null, intArrayOf(), sl = 6, slots = listOf("hat", "glasses", "headAcc", "gloves", "beard"))
        ))
    )

    private val CAT_ICONS = intArrayOf(Ic.BODY, Ic.HAIR, Ic.FACE, Ic.SHIRT, Ic.SHOE, Ic.HAT)

    private var cat = 0
    private var sub = 0

    private val TXT = 0xFF2F4B5E.toInt()
    private val SUB2 = 0xFF6B8798.toInt()
    private val GREEN = 0xFF6FD06A.toInt()
    private val rail = LinearLayout(ctx)
    private val railScroll = ScrollView(ctx)
    private val titleTv = TextView(ctx)
    private val idCol = LinearLayout(ctx)
    private val nameTab = TextView(ctx)
    private val tab = LinearLayout(ctx)
    private val okBtn = FrameLayout(ctx)
    private val zoomIn = FrameLayout(ctx)
    private val zoomOut = FrameLayout(ctx)
    private val rings = RingsView(ctx)
    private val subRow = LinearLayout(ctx)
    private val body = LinearLayout(ctx)
    private val scroll = ScrollView(ctx)
    private val panel = LinearLayout(ctx)
    private val backBtn = FrameLayout(ctx)
    private val rotL = FrameLayout(ctx)
    private val rotR = FrameLayout(ctx)
    private val icons = HashMap<String, Bitmap?>()
    private var insL = 0
    private var insT = 0
    private var insR = 0
    private var insB = 0

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
        // fundo: o 3D já vem azul; aqui entram os brilhos azul/verde do The Sims 4
        addView(CasBgView(ctx), LayoutParams(-1, -1))
        addView(rings, LayoutParams(-1, -1))

        // aba branca "Olá, meu nome é..." + botão do plumbob (canto superior esquerdo)
        nameTab.text = "OLÁ, MEU NOME É…"
        nameTab.textSize = 13.5f
        nameTab.typeface = Ui.BOLD
        nameTab.letterSpacing = 0.08f
        nameTab.setTextColor(0xFF1F5FA8.toInt())
        nameTab.gravity = Gravity.CENTER_VERTICAL
        nameTab.setPadding(dp(72), 0, dp(34), 0)
        nameTab.background = GradientDrawable().also { g -> g.setColor(0xF5FFFFFF.toInt()); val r = dpf(30f); g.cornerRadii = floatArrayOf(0f, 0f, 0f, 0f, r, r, 0f, 0f) }
        addView(nameTab, LayoutParams(-2, dp(50), Gravity.TOP or Gravity.START))
        backBtn.background = Ui.frost(0f, 0xDDF2FF, 0xFF, 0xE8, dpf(2.2f), oval = true, edge = 0xFF9ED0F0.toInt())
        backBtn.addView(IconView(ctx, Ic.PLUMB, 0xFF6BE04A.toInt(), 0xFF2FA83A.toInt()), LayoutParams(dp(30), dp(30), Gravity.CENTER))
        backBtn.setOnClickListener { finish() }
        addView(backBtn, LayoutParams(dp(54), dp(54), Gravity.TOP or Gravity.START).also { it.setMargins(dp(8), dp(4), 0, 0) })

        // coluna de identidade (sexo, idade e corpo), como o painel do alto à esquerda do Sims 4
        idCol.orientation = LinearLayout.HORIZONTAL
        idCol.setPadding(dp(6), dp(8), dp(6), dp(8))
        idCol.background = Ui.frost(dpf(18f), 0xDCEEFB, 0xC8, 0xA8, dpf(1.4f), edge = 0xCCFFFFFF.toInt())
        addView(idCol, LayoutParams(-2, -2, Gravity.TOP or Gravity.START).also { it.setMargins(dp(10), dp(64), 0, 0) })

        // setas grandes de girar, embaixo (como no Sims)
        for ((box, flip, dir) in listOf(Triple(rotL, true, -1.0f), Triple(rotR, false, 1.0f))) {
            val ic = IconView(ctx, Ic.ROTATE, Color.WHITE, Color.WHITE).fancy(0xCC4C86B8.toInt())
            if (flip) ic.scaleX = -1f
            box.addView(ic, LayoutParams(dp(54), dp(54), Gravity.CENTER))
            box.setOnClickListener { game.r.autoSpin = false; game.r.cTargetYaw = game.r.cyaw + dir }
            addView(box, LayoutParams(dp(62), dp(62), Gravity.BOTTOM or Gravity.START))
        }

        // zoom (+/-)
        for ((box, plus) in listOf(Pair(zoomIn, true), Pair(zoomOut, false))) {
            box.background = Ui.frost(0f, 0xFFFFFF, 0xD8, 0xB0, dpf(1.4f), oval = true, edge = 0xEEFFFFFF.toInt())
            val t = TextView(ctx)
            t.text = if (plus) "+" else "\u2212"
            t.textSize = 24f
            t.typeface = Ui.BOLD
            t.setTextColor(0xFF2E78AE.toInt())
            t.gravity = Gravity.CENTER
            t.setPadding(0, 0, 0, dp(3))
            box.addView(t, LayoutParams(-1, -1))
            box.setOnClickListener {
                game.r.autoSpin = false
                game.r.cTargetDist = (game.r.cTargetDist + (if (plus) -0.35f else 0.35f)).coerceIn(0.9f, 5f)
            }
            addView(box, LayoutParams(dp(42), dp(42), Gravity.TOP or Gravity.START))
        }

        // aba inferior central: sortear e zerar
        tab.orientation = LinearLayout.HORIZONTAL
        tab.gravity = Gravity.CENTER
        tab.setPadding(dp(10), dp(6), dp(10), 0)
        tab.background = GradientDrawable().also { g -> g.setColor(0xE8FFFFFF.toInt()); val r = dpf(24f); g.cornerRadii = floatArrayOf(r, r, r, r, 0f, 0f, 0f, 0f) }
        fun tabBtn(icon: Int, label: String, click: () -> Unit): View {
            val l = LinearLayout(ctx)
            l.orientation = LinearLayout.HORIZONTAL
            l.gravity = Gravity.CENTER
            l.setPadding(dp(8), 0, dp(10), 0)
            l.addView(IconView(ctx, icon, 0xFF3C8FC4.toInt(), Color.WHITE), LinearLayout.LayoutParams(dp(22), dp(22)).also { it.rightMargin = dp(5) })
            val t = TextView(ctx)
            t.text = label
            t.textSize = 12.5f
            t.typeface = Ui.BOLD
            t.setTextColor(0xFF2E78AE.toInt())
            l.addView(t)
            l.setOnClickListener { click() }
            return l
        }
        tab.addView(tabBtn(Ic.DICE, "Sortear") { randomize() }, LinearLayout.LayoutParams(-2, dp(38)))
        val sepv = View(ctx)
        sepv.setBackgroundColor(0x3382B4CE)
        tab.addView(sepv, LinearLayout.LayoutParams(dp(1), dp(22)).also { it.setMargins(dp(4), 0, dp(4), 0) })
        tab.addView(tabBtn(Ic.REFRESH, "Zerar aba") { resetCurrent() }, LinearLayout.LayoutParams(-2, dp(38)))
        addView(tab, LayoutParams(-2, dp(46), Gravity.BOTTOM or Gravity.START))

        // botão de confirmar (canto inferior direito)
        okBtn.background = Ui.frost(0f, 0x34C77B, 0xFF, 0xEA, dpf(2.4f), oval = true, edge = 0xFFE9FFF1.toInt())
        okBtn.addView(IconView(ctx, Ic.CHECK, Color.WHITE, 0xFF1F8A52.toInt()).fancy(0x88FFFFFF.toInt()), LayoutParams(dp(32), dp(32), Gravity.CENTER))
        okBtn.setOnClickListener { finish() }
        addView(okBtn, LayoutParams(dp(58), dp(58), Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(14), dp(10)) })

        // categorias: coluna de medalhões ao lado do painel
        rail.orientation = LinearLayout.VERTICAL
        rail.gravity = Gravity.END
        railScroll.isVerticalScrollBarEnabled = false
        railScroll.addView(rail, FrameLayout.LayoutParams(-2, -2))
        addView(railScroll, LayoutParams(-2, -2, Gravity.END or Gravity.CENTER_VERTICAL))

        // painel da direita: lista de peças
        panel.orientation = LinearLayout.VERTICAL
        panel.background = Ui.frost(dpf(22f), 0xF4FAFF, 0xF0, 0xDC, dpf(1.4f), edge = 0xFFFFFFFF.toInt())
        panel.setPadding(dp(12), dp(10), dp(12), dp(12))

        val head = LinearLayout(ctx)
        head.orientation = LinearLayout.HORIZONTAL
        head.gravity = Gravity.CENTER_VERTICAL
        titleTv.textSize = 13f
        titleTv.typeface = Ui.BOLD
        titleTv.setTextColor(0xFF1F5FA8.toInt())
        titleTv.letterSpacing = 0.12f
        head.addView(titleTv, LinearLayout.LayoutParams(0, -2, 1f))
        val dice = FrameLayout(ctx)
        dice.background = Ui.frost(0f, 0xFFFFFF, 0xE0, 0xC0, dpf(1.2f), oval = true, edge = 0xFFB5D8EC.toInt())
        dice.addView(IconView(ctx, Ic.DICE, 0xFF3C8FC4.toInt(), Color.WHITE), LayoutParams(dp(18), dp(18), Gravity.CENTER))
        dice.setOnClickListener { randomize() }
        head.addView(dice, LinearLayout.LayoutParams(dp(30), dp(30)))
        panel.addView(head, LinearLayout.LayoutParams(-1, -2))
        val hsep = View(ctx)
        hsep.setBackgroundColor(0x4482B4CE)
        panel.addView(hsep, LinearLayout.LayoutParams(-1, dp(1)).also { it.topMargin = dp(8) })

        subRow.orientation = LinearLayout.HORIZONTAL
        subRow.gravity = Gravity.CENTER_HORIZONTAL
        val hs2 = HorizontalScrollView(ctx)
        hs2.isHorizontalScrollBarEnabled = false
        hs2.isFillViewport = true
        hs2.addView(subRow, FrameLayout.LayoutParams(-2, -2))
        panel.addView(hs2, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(8) })

        body.orientation = LinearLayout.VERTICAL
        scroll.isVerticalScrollBarEnabled = true
        scroll.scrollBarStyle = View.SCROLLBARS_INSIDE_OVERLAY
        scroll.addView(body)
        panel.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f).also { it.topMargin = dp(8) })

        addView(panel, LayoutParams(dp(360), -1, Gravity.END).also { it.setMargins(0, dp(10), dp(10), dp(78)) })
        refresh(false)
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        if (w <= 0) return
        val pw = (w * 0.38f).toInt().coerceIn(dp(300), dp(420))
        val lp = panel.layoutParams
        if (lp.width != pw) { lp.width = pw; panel.layoutParams = lp }
        layoutStage()
        post { layoutStage() }
    }

    fun setInsets(l: Int, t: Int, r: Int, b: Int) {
        insL = l; insT = t; insR = r; insB = b
        (panel.layoutParams as LayoutParams).setMargins(0, dp(10) + t, dp(10) + r, dp(78) + b)
        (okBtn.layoutParams as LayoutParams).setMargins(0, 0, dp(14) + r, dp(10) + b)
        panel.requestLayout(); okBtn.requestLayout()
        layoutStage()
    }

    /** Tudo é centralizado na "área do palco" (entre o painel de identidade e a coluna de categorias). */
    private fun layoutStage() {
        val w = width
        val h = height
        if (w <= 0 || h <= 0) return
        val pw = panel.layoutParams.width
        val panelL = w - pw - dp(10) - insR
        val railW = dp(64)
        val stageL = (insL + dp(10) + dp(100)).toFloat()
        val stageR = (panelL - dp(8) - railW).toFloat()
        val cx = (stageL + stageR) / 2f
        val sw = stageR - stageL

        (nameTab.layoutParams as LayoutParams).setMargins(insL, insT, 0, 0)
        (backBtn.layoutParams as LayoutParams).setMargins(dp(8) + insL, dp(2) + insT, 0, 0)
        (idCol.layoutParams as LayoutParams).setMargins(dp(10) + insL, dp(62) + insT, 0, 0)
        val asz = dp(62)
        val lx = (cx - sw * 0.34f - asz / 2f).toInt()
        val rx = (cx + sw * 0.34f - asz / 2f).toInt()
        (rotL.layoutParams as LayoutParams).setMargins(lx, 0, 0, dp(16) + insB)
        (rotR.layoutParams as LayoutParams).setMargins(rx, 0, 0, dp(16) + insB)
        (zoomIn.layoutParams as LayoutParams).setMargins((stageR - dp(44)).toInt(), (h / 2f - dp(50)).toInt(), 0, 0)
        (zoomOut.layoutParams as LayoutParams).setMargins((stageR - dp(44)).toInt(), (h / 2f + dp(4)).toInt(), 0, 0)
        (tab.layoutParams as LayoutParams).setMargins((cx - dp(100)).toInt(), 0, 0, insB)
        (railScroll.layoutParams as LayoutParams).setMargins(0, dp(8) + insT, pw + dp(10) + insR + dp(6), dp(8) + insB)
        for (v in listOf<View>(nameTab, backBtn, idCol, rotL, rotR, zoomIn, zoomOut, tab, railScroll)) v.requestLayout()

        // personagem no centro da área do palco (um pouco acima, para não ficar atrás das setas)
        game.r.cShift = 0.07f
        game.r.cShiftX = (cx - w / 2f) / (w / 2f)
        rings.cx = cx
        rings.cy = h / 2f - 0.07f * h / 2f
        rings.r = kotlin.math.min(h * 0.44f, sw * 0.48f)
        rings.invalidate()
    }

    /** Coluna de categorias (Corpo, Cabelo, Rosto, Roupas, Sapatos, Acessórios): medalhão + etiqueta na selecionada. */
    private fun buildRail() {
        rail.removeAllViews()
        for (i in cats.indices) {
            val on = i == cat
            val row = LinearLayout(context)
            row.orientation = LinearLayout.HORIZONTAL
            row.gravity = Gravity.CENTER_VERTICAL or Gravity.END
            if (on) {
                val bub = TextView(context)
                bub.text = cats[i].name
                bub.textSize = 11.5f
                bub.typeface = Ui.BOLD
                bub.setTextColor(0xFF1F5FA8.toInt())
                bub.setPadding(dp(10), dp(3), dp(10), dp(4))
                bub.background = Ui.frost(dpf(12f), 0xFFFFFF, 0xFA, 0xF0, dpf(1.1f), edge = 0xFFB5D8EC.toInt())
                row.addView(bub, LinearLayout.LayoutParams(-2, -2).also { it.rightMargin = dp(6) })
            }
            val circ = FrameLayout(context)
            circ.background = if (on) Ui.frost(0f, 0x35B5E0, 0xFC, 0xEC, dpf(2.6f), oval = true, edge = GREEN)
                              else Ui.frost(0f, 0xFFFFFF, 0xE4, 0xC0, dpf(1.3f), oval = true, edge = 0xDDFFFFFF.toInt())
            val sz = if (on) 52 else 44
            circ.addView(IconView(context, CAT_ICONS[i], if (on) Color.WHITE else 0xFF5F8FAA.toInt(), if (on) 0xFF2E78AE.toInt() else Color.WHITE), LayoutParams(dp((sz * 0.52f).toInt()), dp((sz * 0.52f).toInt()), Gravity.CENTER))
            row.addView(circ, LinearLayout.LayoutParams(dp(sz), dp(sz)))
            row.setOnClickListener { cat = i; sub = 0; refresh(false); camera() }
            rail.addView(row, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(5); it.bottomMargin = dp(5); it.rightMargin = dp(if (on) 0 else 4) })
        }
    }

    // ---- painel de identidade: sexo, idade e corpo (sempre visível, como no Sims 4) ----
    private fun idBtn(on: Boolean, enabled: Boolean, content: View, click: () -> Unit): View {
        val f = FrameLayout(context)
        f.background = if (on) Ui.frost(dpf(12f), 0xFFFFFF, 0xFF, 0xF4, dpf(2.2f), edge = GREEN) else Ui.frost(dpf(12f), 0xFFFFFF, 0x99, 0x66, dpf(1f), edge = 0x99FFFFFF.toInt())
        f.addView(content, LayoutParams(dp(24), dp(24), Gravity.CENTER))
        f.alpha = if (enabled) 1f else 0.35f
        if (enabled) f.setOnClickListener { click() }
        return f
    }

    private fun buildIdentity() {
        idCol.removeAllViews()
        val av = st.avatar
        val a = LinearLayout(context); a.orientation = LinearLayout.VERTICAL
        val b = LinearLayout(context); b.orientation = LinearLayout.VERTICAL
        fun add(col: LinearLayout, v: View) = col.addView(v, LinearLayout.LayoutParams(dp(36), dp(36)).also { it.setMargins(dp(2), dp(2), dp(2), dp(2)) })
        for ((txt, m) in listOf("\u2642" to true, "\u2640" to false)) {
            val t = TextView(context)
            t.text = txt
            t.textSize = 20f
            t.typeface = Ui.BOLD
            t.gravity = Gravity.CENTER
            val on = av.masc == m
            t.setTextColor(if (on) 0xFF3BB04B.toInt() else 0xFF5F8FAA.toInt())
            add(a, idBtn(on, av.simAge >= 2, t) { av.masc = m; av.female = !m; simApply() })
        }
        val tipos = listOf(0, 1, 3)
        for ((k, tp) in tipos.withIndex()) {
            val cur = av.simTypeFor(av.simAge, av.simType) == tp
            add(a, idBtn(cur, av.simTypeFor(av.simAge, tp) == tp, FigView(context, 10 + k, if (cur) 0xFF3BB04B.toInt() else 0xFF5F8FAA.toInt())) { av.simType = tp; simApply() })
        }
        for (i in 0..4) {
            val cur = av.simAge == i
            add(b, idBtn(cur, true, FigView(context, i, if (cur) 0xFF3BB04B.toInt() else 0xFF5F8FAA.toInt())) { av.simAge = i; simApply() })
        }
        idCol.addView(a)
        idCol.addView(b)
    }

    /** Zera só a aba atual: cores voltam ao original, proporções a zero, peças são tiradas. */
    private fun resetCurrent() {
        val s = cats[cat].subs[sub]
        val av = st.avatar
        for (slot in s.colors) av.cc[slot] = -1
        CuteColor.setColors(av.cc)
        if (s.sl == 1) { java.util.Arrays.fill(av.ss, 0); java.util.Arrays.fill(av.bs, 0); CuteChar.setShape(av.bs, av.fs, av.masc, av.ss) }
        if (s.sl == 6) {
            val grp = CuteChar.bodyGroup()
            if (grp != null) ModStore.clear(grp, s.slots)
            if ("hairBack" in s.slots) av.simHair = false
            CuteChar.setWear(av.wearKeys())
        }
        st.save()
        refresh(true)
    }

    /** Dado: sorteia uma peça (aba de peças), as cores ou as proporções da aba atual. */
    private fun randomize() {
        val s = cats[cat].subs[sub]
        val av = st.avatar
        val rnd = java.util.Random()
        if (s.sl == 6) {
            val grp = CuteChar.bodyGroup()
            val list = if (grp == null) emptyList() else ModStore.items.filter { it.grp == grp && it.slot in s.slots }
            if (list.isNotEmpty()) { ModStore.select(list[rnd.nextInt(list.size)]); itemsChanged(); return }
        }
        for (slot in s.colors) {
            val n = CuteColor.palette(slot).size
            if (n > 0) av.cc[slot] = rnd.nextInt(n)
        }
        CuteColor.setColors(av.cc)
        if (s.sl == 1) {
            for (i in av.bs.indices) av.bs[i] = rnd.nextInt(81) - 40
            CuteChar.setShape(av.bs, av.fs, av.masc, av.ss)
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
        post { layoutStage() }
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
        buildRail()
        buildIdentity()

        val c = cats[cat]
        titleTv.text = (if (c.subs.size == 1) c.subs[0].name else c.name).uppercase()
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
        for (slot in s.colors) colorRow(slot)
        if (s.sl == 6) itemsPanel(s.slots) else if (s.sl == 4) baseChoice() else if (s.sl == 3) expressions() else if (s.sl == 1) sliders(1)
        body.addView(View(context), LinearLayout.LayoutParams(-1, dp(8)))
        scroll.post { scroll.scrollTo(0, if (keepScroll) keep else 0) }
    }

    // ---- Peças (roupas, cabelos, sapatos, acessórios): grade de fotos de prévia, como no The Sims ----
    private var modMsg = ""

    /** Chamado pela MainActivity quando a importação termina (já na thread da tela). */
    fun modsChanged(msg: String) {
        modMsg = msg
        CuteChar.setWear(st.avatar.wearKeys())
        refresh(true)
    }

    private fun itemsChanged() {
        CuteChar.setWear(st.avatar.wearKeys())
        st.save()
        refresh(true)
    }

    private class Entry(
        val key: String,
        val label: String,
        val sel: Boolean,
        val none: Boolean,
        val loader: (() -> Bitmap?)?,
        val onClick: () -> Unit,
        val onDelete: (() -> Unit)? = null,
        val onTex: (() -> Unit)? = null
    )

    private val thumbCache = HashMap<String, Bitmap?>()

    private fun loadThumb(iv: ImageView, e: Entry) {
        val loader = e.loader ?: return
        val hit = thumbCache[e.key]
        if (hit != null) { iv.setImageBitmap(hit); return }
        if (thumbCache.containsKey(e.key)) return
        Thread {
            val b = try { loader() } catch (x: Throwable) { null }
            post {
                thumbCache[e.key] = b
                if (b != null && iv.tag == e.key) iv.setImageBitmap(b)
            }
        }.start()
    }

    private fun smallBadge(text: String, click: () -> Unit): TextView {
        val t = TextView(context)
        t.text = text
        t.textSize = 11f
        t.typeface = Ui.BOLD
        t.setTextColor(Color.WHITE)
        t.gravity = Gravity.CENTER
        t.background = Ui.oval(0xCC6F93A6.toInt())
        t.setOnClickListener { click() }
        return t
    }

    private fun entryTile(e: Entry): View {
        val f = FrameLayout(context)
        f.background = if (e.sel) Ui.frost(dpf(14f), 0xFFFFFF, 0xFF, 0xF2, dpf(2.6f), edge = GREEN) else cardBg(dpf(14f))
        if (e.none) {
            val x = TextView(context)
            x.text = "∅"
            x.textSize = 34f
            x.setTextColor(SUB2)
            x.gravity = Gravity.CENTER
            f.addView(x, LayoutParams(-1, dp(116), Gravity.TOP).also { it.topMargin = dp(6) })
        } else {
            // fundo claro atrás da foto (peças brancas/pretas aparecem bem)
            val back = View(context)
            back.background = GradientDrawable().also { g -> g.cornerRadius = dpf(10f); g.setColor(0xFFE9F3F9.toInt()) }
            f.addView(back, LayoutParams(-1, dp(114), Gravity.TOP).also { it.setMargins(dp(6), dp(6), dp(6), 0) })
            val iv = ImageView(context)
            iv.scaleType = ImageView.ScaleType.FIT_CENTER
            iv.tag = e.key
            f.addView(iv, LayoutParams(-1, dp(114), Gravity.TOP).also { it.setMargins(dp(6), dp(6), dp(6), 0) })
            loadThumb(iv, e)
        }
        val n = TextView(context)
        n.text = e.label
        n.textSize = 11f
        n.typeface = Ui.MED
        n.maxLines = 2
        n.gravity = Gravity.CENTER
        n.setTextColor(if (e.sel) TXT else SUB2)
        n.setPadding(dp(4), 0, dp(4), dp(6))
        f.addView(n, LayoutParams(-1, dp(34), Gravity.BOTTOM))
        if (e.sel) {
            val ck = TextView(context)
            ck.text = "✓"
            ck.textSize = 12f
            ck.typeface = Ui.BOLD
            ck.setTextColor(Color.WHITE)
            ck.gravity = Gravity.CENTER
            ck.background = Ui.oval(0xFF4CBF6B.toInt())
            f.addView(ck, LayoutParams(dp(24), dp(24), Gravity.TOP or Gravity.END).also { it.setMargins(0, dp(9), dp(9), 0) })
        }
        e.onDelete?.let { del -> f.addView(smallBadge("✕", del), LayoutParams(dp(22), dp(22), Gravity.TOP or Gravity.START).also { it.setMargins(dp(8), dp(8), 0, 0) }) }
        e.onTex?.let { tx ->
            val b = smallBadge("sem textura  +", tx)
            b.background = pillBg(true, dpf(10f))
            b.textSize = 9.5f
            f.addView(b, LayoutParams(-2, dp(20), Gravity.TOP or Gravity.CENTER_HORIZONTAL).also { it.topMargin = dp(92) })
        }
        f.setOnClickListener { e.onClick() }
        return f
    }

    private fun importTile(): View {
        val act = context as? MainActivity
        val f = FrameLayout(context)
        f.background = GradientDrawable().also { g ->
            g.cornerRadius = dpf(14f)
            g.setColor(0x55FFFFFF)
            g.setStroke(dp(2), 0xFF9BC3D6.toInt(), dpf(6f), dpf(4f))
        }
        f.addView(IconView(context, Ic.PLUS, 0xFF4B9CC4.toInt(), Color.WHITE), LayoutParams(dp(34), dp(34), Gravity.TOP or Gravity.CENTER_HORIZONTAL).also { it.topMargin = dp(26) })
        val n = TextView(context)
        n.text = if (ModStore.isBusy) "Importando..." else "Importar\n.package"
        n.textSize = 11f
        n.typeface = Ui.MED
        n.maxLines = 2
        n.gravity = Gravity.CENTER
        n.setTextColor(SUB2)
        n.setPadding(dp(4), 0, dp(4), dp(6))
        f.addView(n, LayoutParams(-1, dp(40), Gravity.BOTTOM))
        f.setOnClickListener { if (!ModStore.isBusy) act?.pickMods(null) }
        return f
    }

    private fun itemsPanel(slots: List<String>) {
        val av = st.avatar
        val act = context as? MainActivity
        val grp = CuteChar.bodyGroup()
        val hair = "hairBack" in slots
        val list = if (grp == null) emptyList() else ModStore.items.filter { it.grp == grp && it.slot in slots }
        val anyWorn = list.any { ModStore.isWorn(it) }
        val entries = ArrayList<Entry>()
        if (hair) {
            entries.add(Entry("none", "Careca", !av.simHair && !anyWorn, true, null, {
                av.simHair = false
                if (grp != null) ModStore.clear(grp, slots)
                itemsChanged()
            }))
            if (grp != null && av.simAge >= 2) {
                entries.add(Entry("hairdef_$grp", "Liso longo", av.simHair && !anyWorn, false, { ModStore.assetThumb("hairdef_$grp") }, {
                    av.simHair = true
                    ModStore.clear(grp, slots)
                    itemsChanged()
                }))
            }
        } else {
            entries.add(Entry("none", "Nenhum", !anyWorn, true, null, {
                if (grp != null) ModStore.clear(grp, slots)
                itemsChanged()
            }))
        }
        for (m in list) {
            entries.add(Entry("m_" + m.id + (if (m.hasTex) "1" else "0"), m.name, ModStore.isWorn(m), false, { ModStore.thumb(m) },
                { ModStore.select(m); itemsChanged() },
                if (!m.builtin) ({ ModStore.remove(m); itemsChanged() }) else null,
                if (!m.builtin && !m.hasTex) ({ act?.pickMods(m.id) }) else null))
        }
        val cols = 2
        val total = entries.size + 1
        var row: LinearLayout? = null
        for (i in 0 until total) {
            if (i % cols == 0) {
                row = LinearLayout(context)
                row.orientation = LinearLayout.HORIZONTAL
                body.addView(row, LinearLayout.LayoutParams(-1, -2))
            }
            val v = if (i < entries.size) entryTile(entries[i]) else importTile()
            row!!.addView(v, LinearLayout.LayoutParams(0, dp(156), 1f).also { it.setMargins(dp(4), dp(4), dp(4), dp(4)) })
        }
        val rest = (cols - total % cols) % cols
        for (k in 0 until rest) row!!.addView(View(context), LinearLayout.LayoutParams(0, dp(156), 1f).also { it.setMargins(dp(4), dp(4), dp(4), dp(4)) })
        if (modMsg.isNotEmpty()) {
            val m = TextView(context)
            m.text = modMsg
            m.textSize = 12f
            m.setTextColor(TXT)
            body.addView(m, LinearLayout.LayoutParams(-1, -2).also { it.setMargins(dp(4), dp(6), dp(4), dp(4)) })
        }
        val info = TextView(context)
        info.text = "Importe roupas, sapatos e cabelos de arquivos .package do The Sims 2, 3 ou 4 (também .zip e .rar). Se a peça vier sem cor, toque em \"sem textura\" e escolha o package de textura."
        info.textSize = 11f
        info.setTextColor(SUB2)
        body.addView(info, LinearLayout.LayoutParams(-1, -2).also { it.setMargins(dp(4), dp(10), dp(4), dp(4)) })
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
        if (kind != 1) return   // o rosto vem do Sims 3 (sem sliders); os sliders de corpo valem para o corpo do Sims 3
        val av = st.avatar
        if (CuteChar.simSlidersAvailable()) { simSlidersUi(); return }   // Etapa 65: sliders reais do Sims 3
        val names = if (kind == 1) BodyMorph.BODY_NAMES else BodyMorph.FACE_NAMES
        val arr = if (kind == 1) av.bs else av.fs
        if (false) {
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
                        CuteChar.setShape(av.bs, av.fs, av.masc, av.ss)
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
            CuteChar.setShape(av.bs, av.fs, av.masc, av.ss)
            st.save()
            refresh(true)
        }
        body.addView(reset, LinearLayout.LayoutParams(-2, dp(34)).also { it.topMargin = dp(6); it.leftMargin = dp(4) })
        val order = ArrayList<Pair<String?, Int>>()
        for ((gn, ids) in BodyMorph.BODY_GROUPS) for ((k, id) in ids.withIndex()) order.add((if (k == 0) gn else null) to id)
        for ((grupo, i) in order) {
            if (grupo != null) {
                val gh = TextView(context)
                gh.text = grupo
                gh.textSize = 15f
                gh.typeface = Ui.BOLD
                gh.setTextColor(TXT)
                body.addView(gh, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(20); it.leftMargin = dp(4) })
            }
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
                    CuteChar.setShape(av.bs, av.fs, av.masc, av.ss)
                }
                override fun onStartTrackingTouch(s: SeekBar?) { s?.parent?.requestDisallowInterceptTouchEvent(true) }
                override fun onStopTrackingTouch(s: SeekBar?) { st.save() }
            })
            body.addView(sb, LinearLayout.LayoutParams(-1, dp(36)))
        }
    }


    private val openCats = HashSet<String>()
    private val BODY_CATS = listOf("Tronco e postura", "Ombros", "Busto", "Quadril e bumbum", "Pernas", "Braços", "Mãos", "Pés", "Pescoço")
    private val FACE_CATS = listOf("Cabeça", "Olhos", "Sobrancelhas", "Bochechas", "Nariz", "Boca", "Mandíbula e queixo", "Orelhas")

    /** Uma linha "nome ........ valor" + barra -100..100 (ímã no zero). */
    private fun seekRow(label: String, cur: Int, onChange: (Int) -> Unit) {
        val head = LinearLayout(context)
        head.orientation = LinearLayout.HORIZONTAL
        head.gravity = Gravity.CENTER_VERTICAL
        val lab = TextView(context)
        lab.text = label
        lab.textSize = 13f
        lab.typeface = Ui.BOLD
        lab.setTextColor(TXT)
        head.addView(lab, LinearLayout.LayoutParams(0, -2, 1f))
        val value = TextView(context)
        value.text = pct(cur)
        value.textSize = 12f
        value.typeface = Ui.MED
        value.setTextColor(SUB2)
        head.addView(value, LinearLayout.LayoutParams(-2, -2))
        body.addView(head, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(10); it.leftMargin = dp(4); it.rightMargin = dp(4) })
        val sb = SeekBar(context)
        sb.max = 200
        sb.progress = cur + 100
        sb.progressTintList = ColorStateList.valueOf(0xFF35B5E0.toInt())
        sb.progressBackgroundTintList = ColorStateList.valueOf(0xFFBFD6E0.toInt())
        sb.thumbTintList = ColorStateList.valueOf(0xFF2E9BD1.toInt())
        sb.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(s: SeekBar?, p: Int, fromUser: Boolean) {
                if (!fromUser) return
                var v = p - 100
                if (v in -4..4) { v = 0; s?.progress = 100 }
                value.text = pct(v)
                onChange(v)
            }
            override fun onStartTrackingTouch(s: SeekBar?) { s?.parent?.requestDisallowInterceptTouchEvent(true) }
            override fun onStopTrackingTouch(s: SeekBar?) { st.save() }
        })
        body.addView(sb, LinearLayout.LayoutParams(-1, dp(36)))
    }

    /** Etapa 65: os sliders de corpo e rosto do The Sims 3, agrupados e recolhíveis. */
    private fun simSlidersUi() {
        val av = st.avatar
        val reset = TextView(context)
        reset.text = "Zerar tudo"
        reset.textSize = 12f
        reset.typeface = Ui.BOLD
        reset.setTextColor(TXT)
        reset.gravity = Gravity.CENTER
        reset.setPadding(dp(14), 0, dp(14), dp(2))
        reset.background = pillBg(false, dpf(15f))
        reset.setOnClickListener {
            java.util.Arrays.fill(av.ss, 0)
            java.util.Arrays.fill(av.bs, 0)
            CuteChar.setShape(av.bs, av.fs, av.masc, av.ss)
            st.save()
            refresh(true)
        }
        body.addView(reset, LinearLayout.LayoutParams(-2, dp(34)).also { it.topMargin = dp(6); it.leftMargin = dp(4) })
        fun title(t: String, size: Float, top: Int) {
            val gh = TextView(context)
            gh.text = t
            gh.textSize = size
            gh.typeface = Ui.BOLD
            gh.setTextColor(TXT)
            body.addView(gh, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(top); it.leftMargin = dp(4) })
        }
        title("Geral", 15f, 18)
        seekRow("Altura", av.bs[0]) { v -> av.bs[0] = v; CuteChar.setShape(av.bs, av.fs, av.masc, av.ss) }
        fun cats(titulo: String, face: Boolean, names: List<String>) {
            title(titulo, 17f, 24)
            for (c in names) {
                val list = SimSliders.sliders.filter { it.face == face && it.cat == c }
                if (list.isEmpty()) continue
                val open = c in openCats
                val used = list.count { av.ss[it.id] != 0 }
                val h = TextView(context)
                h.text = (if (open) "▾  " else "▸  ") + c + "  (" + list.size + ")" + (if (used > 0) "  •  $used alterado(s)" else "")
                h.textSize = 14f
                h.typeface = Ui.BOLD
                h.setTextColor(TXT)
                h.setPadding(dp(10), 0, dp(10), 0)
                h.gravity = Gravity.CENTER_VERTICAL
                h.background = pillBg(open, dpf(14f)).also { }
                h.setTextColor(if (open) Color.WHITE else TXT)
                h.setOnClickListener { if (open) openCats.remove(c) else openCats.add(c); refresh(true) }
                body.addView(h, LinearLayout.LayoutParams(-1, dp(42)).also { it.topMargin = dp(8); it.leftMargin = dp(4); it.rightMargin = dp(4) })
                if (open) for (sl in list) seekRow(sl.name, av.ss[sl.id]) { v -> av.ss[sl.id] = v; CuteChar.setShape(av.bs, av.fs, av.masc, av.ss) }
            }
        }
        cats("Corpo", false, BODY_CATS)
        cats("Rosto", true, FACE_CATS)
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
        CuteChar.setShape(av.bs, av.fs, av.masc, av.ss)
        st.save()
        refresh(true)
    }

    /** Etapa 44: corpo igual ao The Sims 3 (idade, sexo, tipo de corpo e cabelo). */
    private fun simSelector() {
        val av = st.avatar
        val info = TextView(context)
        info.text = "Corpo e rosto do The Sims 3."
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
    }

    /** Etapa 14: escolha da base. Recomeça o personagem do zero (roupa de baixo, cabelo simples, proporções zeradas). */
    private fun baseChoice() {
        val av = st.avatar
        val info = TextView(context)
        info.text = "Escolha a idade, o sexo e o tipo de corpo. Roupas, cabelo e sapatos ficam nas outras categorias."
        info.textSize = 12f
        info.setTextColor(SUB2)
        body.addView(info, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(6); it.leftMargin = dp(4); it.rightMargin = dp(4) })
        simSelector()
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


/** Fundo do criador: brilhos azul-turquesa e verde suaves por cima do 3D, como a tela do Sims 4. */
private class CasBgView(ctx: Context) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    override fun onDraw(c: Canvas) {
        val w = width.toFloat()
        val h = height.toFloat()
        if (w <= 0f) return
        p.shader = android.graphics.LinearGradient(0f, 0f, 0f, h, intArrayOf(0x3347A9E8, 0x00FFFFFF, 0x3338C98A), floatArrayOf(0f, 0.5f, 1f), android.graphics.Shader.TileMode.CLAMP)
        c.drawRect(0f, 0f, w, h, p)
        p.shader = android.graphics.RadialGradient(w * 0.38f, h * 0.55f, h * 0.75f, intArrayOf(0x55FFFFFF, 0x00FFFFFF), null, android.graphics.Shader.TileMode.CLAMP)
        c.drawRect(0f, 0f, w, h, p)
        p.shader = null
    }
}

/** Silhuetas simples: 0..4 = bebê, criança, jovem, adulto, idoso; 10..12 = magro, médio, forte. */
private class FigView(ctx: Context, private val kind: Int, private val col: Int) : View(ctx) {
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    override fun onDraw(c: Canvas) {
        val w = width.toFloat()
        val h = height.toFloat()
        if (w <= 0f) return
        p.color = col
        p.style = Paint.Style.FILL
        // altura relativa, largura do corpo, tamanho da cabeça
        val (hh, bw, hr) = when (kind) {
            0 -> Triple(0.50f, 0.34f, 0.20f)
            1 -> Triple(0.68f, 0.30f, 0.17f)
            2 -> Triple(0.86f, 0.34f, 0.14f)
            3 -> Triple(1.00f, 0.38f, 0.13f)
            4 -> Triple(0.92f, 0.38f, 0.13f)
            10 -> Triple(1.00f, 0.26f, 0.13f)
            11 -> Triple(1.00f, 0.38f, 0.13f)
            else -> Triple(1.00f, 0.56f, 0.14f)
        }
        val fh = h * hh
        val top = h - fh
        val r = h * hr * 1.05f
        val cx = w / 2f
        c.drawCircle(cx, top + r, r, p)
        val bt = top + r * 2.2f
        val rr = bw * w * 0.5f
        val path = android.graphics.RectF(cx - rr, bt, cx + rr, h)
        c.drawRoundRect(path, rr * 0.7f, rr * 0.7f, p)
        if (kind == 4) { // bengala
            p.style = Paint.Style.STROKE
            p.strokeWidth = w * 0.06f
            c.drawLine(cx + rr + w * 0.06f, bt + fh * 0.2f, cx + rr + w * 0.06f, h, p)
        }
    }
}
