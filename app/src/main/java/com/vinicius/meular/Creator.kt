package com.vinicius.meular

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.view.Gravity
import android.view.View
import android.widget.FrameLayout
import android.widget.HorizontalScrollView
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
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
        val y: Float = Float.NaN
    )

    private class Cat(val name: String, val dist: Float, val y: Float, val subs: List<Sub>)

    private val PI_F = Math.PI.toFloat()

    private val cats: List<Cat> = listOf(
        Cat("Corpo", 4.3f, 0.65f, listOf(
            Sub("Pele", 0.3f, null, intArrayOf(0))
        )),
        Cat("Cabelo", 2.0f, 1.14f, listOf(
            Sub("Atrás", PI_F, Style("hairBack", AvaPal.HB_IDS, AvaPal.HB_N, { a -> a.hb }, { a, i -> a.hb = i }), intArrayOf(2, 3)),
            Sub("Frente", 0f, Style("hairFront", AvaPal.HF_IDS, AvaPal.HF_N, { a -> a.hf }, { a, i -> a.hf = i }), intArrayOf(2, 3))
        )),
        Cat("Rosto", 1.45f, 1.15f, listOf(
            Sub("Olhos", 0f, null, intArrayOf(1)),
            Sub("Óculos", 0f, Style("glasses", AvaPal.GS_IDS, AvaPal.GS_N, { a -> a.cgls }, { a, i -> a.cgls = i }), intArrayOf(10, 11)),
            Sub("Barba", 0f, Style("beard", AvaPal.BD_IDS, AvaPal.BD_N, { a -> a.cbrd }, { a, i -> a.cbrd = i }), intArrayOf(2, 3))
        )),
        Cat("Roupa", 3.1f, 0.85f, listOf(
            Sub("Blusa", 0.3f, Style("top", AvaPal.CT_IDS, AvaPal.CT_N, { a -> a.ctop }, { a, i -> a.ctop = i }), intArrayOf(4, 5)),
            Sub("Calça/saia", 0.3f, Style("bottom", AvaPal.CB_IDS, AvaPal.CB_N, { a -> a.cbot }, { a, i -> a.cbot = i }), intArrayOf(6, 9), 3.4f, 0.6f),
            Sub("Vestido", 0.3f, Style("overall", AvaPal.CO_IDS, AvaPal.CO_N, { a -> a.cov }, { a, i -> a.cov = i }), intArrayOf(4, 5, 6, 9), 3.6f, 0.7f)
        )),
        Cat("Sapatos", 2.3f, 0.22f, listOf(
            Sub("Sapatos", 0.3f, Style("feet", AvaPal.FT_IDS, AvaPal.FT_N, { a -> a.cfeet }, { a, i -> a.cfeet = i }), intArrayOf(7, 8))
        )),
        Cat("Acessórios", 2.0f, 1.1f, listOf(
            Sub("Chapéu", 0.3f, Style("hat", AvaPal.HT_IDS, AvaPal.HT_N, { a -> a.chat }, { a, i -> a.chat = i }), intArrayOf(10, 11)),
            Sub("Cabeça", 0.3f, Style("headAcc", AvaPal.HA_IDS, AvaPal.HA_N, { a -> a.chac }, { a, i -> a.chac = i }), intArrayOf(10, 11)),
            Sub("Luvas", 0.3f, Style("gloves", AvaPal.GV_IDS, AvaPal.GV_N, { a -> a.cglove }, { a, i -> a.cglove = i }), intArrayOf(10, 11), 3.0f, 0.75f)
        ))
    )

    private var cat = 0
    private var sub = 0
    private var viewBack = false

    private val catRow = LinearLayout(ctx)
    private val subRow = LinearLayout(ctx)
    private val body = LinearLayout(ctx)
    private val scroll = ScrollView(ctx)
    private val panel = LinearLayout(ctx)
    private val topBar = LinearLayout(ctx)
    private val icons = HashMap<String, Bitmap?>()

    init {
        // barra de cima: título, girar, pronto
        topBar.orientation = LinearLayout.HORIZONTAL
        topBar.gravity = Gravity.CENTER_VERTICAL
        topBar.setPadding(dp(14), dp(36), dp(14), dp(4))
        val title = TextView(ctx)
        title.text = "Meu personagem"
        title.textSize = 18f
        title.typeface = Ui.BOLD
        title.setTextColor(Color.WHITE)
        topBar.addView(title, LinearLayout.LayoutParams(0, -2, 1f))
        val rot = pill("Girar", Pal.GLASS)
        rot.setOnClickListener {
            viewBack = !viewBack
            game.r.autoSpin = false
            game.r.cTargetYaw = if (viewBack) PI_F else 0.3f
        }
        topBar.addView(rot, LinearLayout.LayoutParams(-2, dp(40)).also { it.rightMargin = dp(8) })
        val ok = pill("Pronto", Pal.GREEN)
        ok.setOnClickListener { st.avatarSet = true; st.save(); onDone() }
        topBar.addView(ok, LinearLayout.LayoutParams(-2, dp(40)))
        addView(topBar, LayoutParams(-1, -2, Gravity.TOP))

        // painel de baixo
        panel.orientation = LinearLayout.VERTICAL
        panel.background = Ui.topSheet(Pal.BG, dpf(26f))
        panel.setPadding(dp(12), dp(12), dp(12), dp(10))
        catRow.orientation = LinearLayout.HORIZONTAL
        val hs1 = HorizontalScrollView(ctx)
        hs1.isHorizontalScrollBarEnabled = false
        hs1.addView(catRow)
        panel.addView(hs1, LinearLayout.LayoutParams(-1, -2))
        subRow.orientation = LinearLayout.HORIZONTAL
        val hs2 = HorizontalScrollView(ctx)
        hs2.isHorizontalScrollBarEnabled = false
        hs2.addView(subRow)
        panel.addView(hs2, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(8) })
        body.orientation = LinearLayout.VERTICAL
        scroll.isVerticalScrollBarEnabled = false
        scroll.addView(body)
        panel.addView(scroll, LinearLayout.LayoutParams(-1, dp(214)).also { it.topMargin = dp(8) })
        addView(panel, LayoutParams(-1, -2, Gravity.BOTTOM))

        // mantém o personagem centralizado na parte livre da tela (acima do painel)
        panel.addOnLayoutChangeListener { _, _, t, _, b, _, _, _, _ -> updateShift(b - t) }
        refresh()
    }

    private fun pill(text: String, color: Int): TextView {
        val t = TextView(context)
        t.text = text
        t.textSize = 15f
        t.typeface = Ui.BOLD
        t.setTextColor(Color.WHITE)
        t.gravity = Gravity.CENTER
        t.setPadding(dp(18), 0, dp(18), 0)
        t.background = Ui.bg(color, dpf(20f), 0x33FFFFFF, dpf(1f))
        return t
    }

    private fun updateShift(panelH: Int) {
        val h = height
        if (h <= 0 || panelH <= 0) return
        game.r.cShift = (panelH.toFloat() / h.toFloat()).coerceIn(0.2f, 0.62f)
    }

    fun setInsets(topPx: Int, bottomPx: Int) {
        topBar.setPadding(dp(14), topPx + dp(10), dp(14), dp(4))
        panel.setPadding(dp(12), dp(12), dp(12), dp(10) + bottomPx)
    }

    fun open() {
        cat = 0; sub = 0; viewBack = false
        game.r.autoSpin = false
        updateShift(panel.height)
        refresh()
        camera()
    }

    private fun camera() {
        val c = cats[cat]
        val s = c.subs[sub]
        game.r.autoSpin = false
        game.r.cTargetDist = if (s.dist.isNaN()) c.dist else s.dist
        game.r.cTargetY = if (s.y.isNaN()) c.y else s.y
        game.r.cTargetYaw = s.yaw
        viewBack = s.yaw > 3f
        updateShift(panel.height)
    }

    private fun refresh() {
        val av = st.avatar
        catRow.removeAllViews()
        for (i in cats.indices) {
            val t = TextView(context)
            t.text = cats[i].name
            t.textSize = 15f
            t.typeface = Ui.BOLD
            t.gravity = Gravity.CENTER
            t.setPadding(dp(16), 0, dp(16), 0)
            val on = i == cat
            t.setTextColor(if (on) Color.WHITE else Pal.SUB)
            t.background = Ui.bg(if (on) Pal.CORAL else Pal.CARD, dpf(18f))
            t.setOnClickListener { cat = i; sub = 0; refresh(); camera() }
            catRow.addView(t, LinearLayout.LayoutParams(-2, dp(38)).also { it.rightMargin = dp(8) })
        }

        val c = cats[cat]
        subRow.removeAllViews()
        for (i in c.subs.indices) {
            val t = TextView(context)
            t.text = c.subs[i].name
            t.textSize = 13f
            t.typeface = Ui.MED
            t.gravity = Gravity.CENTER
            t.setPadding(dp(14), 0, dp(14), 0)
            val on = i == sub
            t.setTextColor(if (on) Color.WHITE else Pal.TEXT)
            t.background = Ui.bg(if (on) Pal.CORAL2 else Pal.CARD_HI, dpf(15f))
            t.setOnClickListener { sub = i; refresh(); camera() }
            subRow.addView(t, LinearLayout.LayoutParams(-2, dp(30)).also { it.rightMargin = dp(8) })
        }
        subRow.visibility = if (c.subs.size > 1) View.VISIBLE else View.GONE

        body.removeAllViews()
        val s = c.subs[sub]
        val stl = s.style
        if (stl != null) grid(stl, stl.get(av))
        for (slot in s.colors) colorRow(slot)
    }

    private fun icon(key: String): Bitmap? = icons.getOrPut(key) {
        try {
            context.assets.open("cute/icons/$key.png").use { BitmapFactory.decodeStream(it) }
        } catch (e: Exception) { null }
    }

    private fun grid(stl: Style, cur: Int) {
        val cols = 4
        var row: LinearLayout? = null
        for (i in stl.ids.indices) {
            if (i % cols == 0) {
                row = LinearLayout(context)
                row.orientation = LinearLayout.HORIZONTAL
                body.addView(row, LinearLayout.LayoutParams(-1, -2))
            }
            row!!.addView(tile(stl, i, i == cur), LinearLayout.LayoutParams(0, dp(100), 1f).also {
                it.setMargins(dp(3), dp(3), dp(3), dp(3))
            })
        }
        // completa a última linha para as miniaturas manterem o mesmo tamanho
        val rest = (cols - stl.ids.size % cols) % cols
        for (k in 0 until rest) {
            row!!.addView(View(context), LinearLayout.LayoutParams(0, dp(100), 1f).also {
                it.setMargins(dp(3), dp(3), dp(3), dp(3))
            })
        }
    }

    private fun tile(stl: Style, i: Int, sel: Boolean): View {
        val f = FrameLayout(context)
        f.background = Ui.bg(Pal.CARD_HI, dpf(14f), if (sel) Color.WHITE else 0, dpf(3f))
        val id = stl.ids[i]
        val bmp = if (id.isEmpty()) null else icon((stl.key + "_" + id).lowercase())
        if (bmp != null) {
            val iv = ImageView(context)
            iv.scaleType = ImageView.ScaleType.FIT_CENTER
            iv.setImageBitmap(bmp)
            f.addView(iv, LayoutParams(-1, dp(66), Gravity.TOP).also { it.topMargin = dp(6) })
        } else {
            val x = TextView(context)
            x.text = if (id.isEmpty()) "Sem" else "?"
            x.textSize = 16f
            x.typeface = Ui.BOLD
            x.setTextColor(Pal.SUB)
            x.gravity = Gravity.CENTER
            f.addView(x, LayoutParams(-1, dp(66), Gravity.TOP).also { it.topMargin = dp(6) })
        }
        val n = TextView(context)
        n.text = stl.names[i]
        n.textSize = 10f
        n.typeface = Ui.MED
        n.maxLines = 2
        n.gravity = Gravity.CENTER
        n.setTextColor(if (sel) Color.WHITE else Pal.SUB)
        n.setPadding(dp(3), 0, dp(3), dp(4))
        f.addView(n, LayoutParams(-1, dp(28), Gravity.BOTTOM))
        f.setOnClickListener { pickStyle(stl, i) }
        return f
    }

    private fun pickStyle(stl: Style, i: Int) {
        val a = st.avatar
        stl.set(a, i)
        CuteChar.setWear(a.wearKeys())
        st.save()
        val keep = scroll.scrollY
        refresh()
        scroll.post { scroll.scrollTo(0, keep) }
    }

    private fun colorRow(slot: Int) {
        val av = st.avatar
        val cur = av.cc[slot]
        val lab = TextView(context)
        lab.text = CuteColor.SLOT_NAMES[slot]
        lab.textSize = 12f
        lab.typeface = Ui.BOLD
        lab.setTextColor(Pal.SUB)
        body.addView(lab, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(10); it.bottomMargin = dp(4); it.leftMargin = dp(3) })

        val row = LinearLayout(context)
        row.orientation = LinearLayout.HORIZONTAL
        row.gravity = Gravity.CENTER_VERTICAL
        val orig = TextView(context)
        orig.text = "Original"
        orig.textSize = 12f
        orig.typeface = Ui.BOLD
        orig.setTextColor(Color.WHITE)
        orig.gravity = Gravity.CENTER
        orig.setPadding(dp(12), 0, dp(12), 0)
        orig.background = Ui.bg(Pal.CARD_HI, dpf(18f), if (cur < 0) Color.WHITE else 0, dpf(3f))
        orig.setOnClickListener { pickColor(slot, -1) }
        row.addView(orig, LinearLayout.LayoutParams(-2, dp(38)).also { it.rightMargin = dp(10) })
        val pal = CuteColor.palette(slot)
        for (i in pal.indices) {
            val v = View(context)
            val on = i == cur
            v.background = Ui.oval(pal[i], if (on) Color.WHITE else 0x66FFFFFF, if (on) dpf(3f) else dpf(1f))
            v.setOnClickListener { pickColor(slot, i) }
            row.addView(v, LinearLayout.LayoutParams(dp(38), dp(38)).also { it.rightMargin = dp(10) })
        }
        val hs = HorizontalScrollView(context)
        hs.isHorizontalScrollBarEnabled = false
        hs.addView(row)
        body.addView(hs, LinearLayout.LayoutParams(-1, -2))
    }

    private fun pickColor(slot: Int, i: Int) {
        st.avatar.cc[slot] = i
        CuteColor.setColors(st.avatar.cc)
        st.save()
        val keep = scroll.scrollY
        refresh()
        scroll.post { scroll.scrollTo(0, keep) }
    }
}
