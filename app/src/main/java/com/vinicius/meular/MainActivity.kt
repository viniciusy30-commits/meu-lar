package com.vinicius.meular

import android.app.Dialog
import android.graphics.Color
import android.widget.ImageView
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.LayerDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.MotionEvent
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
    private lateinit var casaTv: TextView
    private lateinit var movTv: TextView
    private lateinit var sideCol: LinearLayout
    private lateinit var portrait: FrameLayout
    private lateinit var editBar: LinearLayout
    private lateinit var moveIcon: IconView
    private lateinit var moveLbl: TextView
    private lateinit var moveBox: LinearLayout
    private lateinit var msgTv: TextView
    private lateinit var viewIcon: IconView
    private lateinit var hud: LinearLayout
    private lateinit var bottom: LinearLayout
    private lateinit var jumpBtn: FrameLayout
    private lateinit var useBtn: LinearLayout
    private lateinit var useTxt: TextView
    private lateinit var useIc: IconView
    private lateinit var crouchBtn: FrameLayout
    private lateinit var crouchIc: IconView
    private lateinit var actBox: FrameLayout
    private lateinit var drivePad: FrameLayout
    private var wasDriving = false
    // Etapa 128: voo
    private lateinit var flyBtn: TextView
    private lateinit var flyPad: FrameLayout
    private lateinit var turboBtn: TextView
    private var wasFlying = false
    private lateinit var dockR: LinearLayout
    private lateinit var creator: CreatorUi
    private var prevMode = 0
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


    /** Pílula de status do topo (como no Sims): medalhão colorido com ícone + valor (+ botão de mais). */
    private fun statPill(icon: Int, tone: Tone, value: TextView, plus: (() -> Unit)?, tap: (() -> Unit)?): LinearLayout {
        val chip = LinearLayout(this)
        chip.orientation = LinearLayout.HORIZONTAL
        chip.gravity = Gravity.CENTER_VERTICAL
        chip.setPadding(dp(3), dp(3), dp(plus?.let { 3 } ?: 12), dp(3))
        chip.background = Ui.frost(dpf(22f), 0x0B1624, 0xB8, 0x86, dpf(1.4f), edge = 0xCCFFFFFF.toInt())
        val med = FrameLayout(this)
        med.background = Ui.chunky(tone, dpf(32f), dpf(2f), true, 0xFFFFFFFF.toInt(), dpf(1.6f))
        med.setPadding(0, 0, 0, dp(2))
        med.addView(IconView(this, icon, Color.WHITE, tone.edge), FrameLayout.LayoutParams(dp(19), dp(19), Gravity.CENTER))
        chip.addView(med, LinearLayout.LayoutParams(dp(32), dp(32)))
        value.setPadding(dp(9), 0, dp(plus?.let { 9 } ?: 0), 0)
        chip.addView(value)
        if (plus != null) {
            val p = FrameLayout(this)
            p.background = Ui.chunky(Tn.SIMS_GREEN, dpf(26f), dpf(2f), true, 0xFFFFFFFF.toInt(), dpf(1.4f))
            p.setPadding(0, 0, 0, dp(2))
            p.addView(IconView(this, Ic.PLUS, Color.WHITE, Tn.SIMS_GREEN.edge), FrameLayout.LayoutParams(dp(14), dp(14), Gravity.CENTER))
            press(p) { plus() }
            chip.addView(p, LinearLayout.LayoutParams(dp(26), dp(26)))
        }
        if (tap != null) press(chip) { tap() }
        return chip
    }

    /** Botão quadrado arredondado da coluna da esquerda (rosa, âmbar, verde-água...). */
    private fun sideTile(icon: Int, tone: Tone, acao: () -> Unit): FrameLayout {
        val f = FrameLayout(this)
        f.background = Ui.chunky(tone, dpf(17f), dpf(3.5f), true, 0xFFFFFFFF.toInt(), dpf(2f))
        f.setPadding(0, 0, 0, dp(3))
        f.addView(IconView(this, icon, Color.WHITE, tone.edge).fancy(0x88FFFFFF.toInt()), FrameLayout.LayoutParams(dp(30), dp(30), Gravity.CENTER))
        f.layoutParams = LinearLayout.LayoutParams(dp(50), dp(54)).also { it.topMargin = dp(9) }
        press(f, acao)
        return f
    }

    /** Etapa 88: botão do canto superior direito (vidro colorido com brilho e borda branca); devolve o ícone. */
    private fun topBtn(icon: Int, tone: Tone, acao: () -> Unit): Pair<FrameLayout, IconView> {
        val f = FrameLayout(this)
        f.background = Ui.chunky(tone, dpf(16f), dpf(3f), true, 0xFFFFFFFF.toInt(), dpf(1.8f))
        f.setPadding(0, 0, 0, dp(3))
        f.elevation = dpf(5f)
        val ic = IconView(this, icon, Color.WHITE, tone.edge).fancy(0x99FFFFFF.toInt())
        f.addView(ic, FrameLayout.LayoutParams(dp(26), dp(26), Gravity.CENTER))
        f.layoutParams = LinearLayout.LayoutParams(dp(46), dp(48)).also { it.leftMargin = dp(8) }
        press(f, acao)
        return Pair(f, ic)
    }

    private var rScale = 0f
    private var rW = 0
    private var rH = 0
    private fun ajustarResolucao() {
        val w = game.width; val h = game.height
        if (w <= 0 || h <= 0 || game.mode == 2) return
        val short = minOf(w, h).toFloat()
        // Prioriza nitidez: renderiza em resolução nativa (até 900 px no lado curto).
        // A escala dinâmica só reduz até 82% quando realmente necessário, evitando o antigo visual borrado.
        val maxS = minOf(1f, 900f / short)
        val minS = maxS * 0.76f
        var ns = rScale
        if (w != rW || h != rH || rScale == 0f) { rW = w; rH = h; ns = maxS }
        else {
            val f = game.r.fpsAvg
            if (f < 52f) ns = maxOf(minS, rScale * 0.93f)      // Etapa 161: reage antes de cair dos 60 FPS
            else if (f > 58f) ns = minOf(maxS, rScale * 1.03f)
        }
        if (Math.abs(ns - rScale) > 0.02f || rScale == 0f) {
            rScale = ns
            game.holder.setFixedSize(Math.max(1, (w * ns).toInt()), Math.max(1, (h * ns).toInt()))
        }
    }

    private var crouchOn = false
    /** Etapa 88: botão de agachar aceso (amarelo) quando o personagem está agachado */
    private fun atualizarTurbo() {
        if (!::turboBtn.isInitialized) return
        val on = game.r.turbo
        turboBtn.background = Ui.frost(dpf(18f), if (on) 0xFF6A00 else 0x555F70, 0xE8, 0xA8, dpf(2f), edge = if (on) 0xFFFFE08A.toInt() else 0xCCFFFFFF.toInt())
        turboBtn.text = if (on) "TURBO\nLIGADO" else "TURBO"
    }

    private fun atualizarAgachar() {
        crouchOn = game.r.crouch
        crouchBtn.background = if (crouchOn) Ui.frost(0f, 0xFFB52E, 0xF0, 0xC0, dpf(2f), oval = true, edge = 0xFFFFFFFF.toInt())
            else Ui.frost(0f, 0x3A4A66, 0xC8, 0x90, dpf(1.6f), oval = true, edge = 0xCCFFFFFF.toInt())
    }

    /** Segmento da barra inferior direita; devolve o ícone para poder trocá-lo. */
    private fun dockSeg(icon: Int, tint: Int, acao: () -> Unit): Pair<FrameLayout, IconView> {
        val f = FrameLayout(this)
        f.background = Ui.frost(0f, tint, 0xE8, 0xA8, dpf(1.6f), oval = true, edge = 0xEEFFFFFF.toInt())
        val ic = IconView(this, icon, Color.WHITE, SOFT_ACC).fancy(0xAAFFFFFF.toInt())
        f.addView(ic, FrameLayout.LayoutParams(dp(24), dp(24), Gravity.CENTER))
        f.layoutParams = LinearLayout.LayoutParams(dp(44), dp(44)).also { it.setMargins(dp(3), dp(3), dp(3), dp(3)) }
        press(f, acao)
        return Pair(f, ic)
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
        // Etapa 124: se o jogo fechar sozinho, guarda o erro para mostrar na próxima abertura
        val prev = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { th, e ->
            try {
                val sw = java.io.StringWriter(); e.printStackTrace(java.io.PrintWriter(sw))
                val rt = Runtime.getRuntime()
                getSharedPreferences("crash", MODE_PRIVATE).edit().putString("last", "[${th.name}] mem ${(rt.totalMemory() - rt.freeMemory()) / 1048576}/${rt.maxMemory() / 1048576} MB\n" + sw.toString().take(3500)).commit()
            } catch (x: Throwable) { }
            prev?.uncaughtException(th, e)
        }
        CuteChar.assets = assets
        ModStore.init(this)
        Flora.assets = assets
        Glb.assets = assets
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

        // topo: pílulas de status no centro (dinheiro, casa, móveis), como no The Sims
        hud = LinearLayout(this)
        hud.orientation = LinearLayout.HORIZONTAL
        hud.gravity = Gravity.CENTER
        hud.setPadding(dp(12), dp(8), dp(12), dp(4))
        moneyTv = tvShadow(tv("", 22f, Color.WHITE, true))
        casaTv = tvShadow(tv("", 15f, Color.WHITE, true))
        movTv = tvShadow(tv("", 15f, Color.WHITE, true))
        // Etapa 88: o dinheiro saiu da tela (fica dentro do mercado)
        root.addView(hud, FrameLayout.LayoutParams(-1, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP))

        // canto superior esquerdo: retrato do personagem + coluna de atalhos
        portrait = FrameLayout(this)
        portrait.background = Ui.frost(0f, 0xBFE6FA, 0xF0, 0xCC, dpf(2.4f), oval = true, edge = 0xFFFFFFFF.toInt())
        portrait.addView(IconView(this, Ic.AVATAR, Color.WHITE, Color.WHITE), FrameLayout.LayoutParams(dp(34), dp(34), Gravity.CENTER))
        // rosto real do personagem (renderizado pelo jogo); o desenho fica por baixo até a foto ficar pronta
        val face = ImageView(this)
        face.scaleType = ImageView.ScaleType.CENTER_CROP
        face.outlineProvider = object : android.view.ViewOutlineProvider() {
            override fun getOutline(v: View, o: android.graphics.Outline) { o.setOval(0, 0, v.width, v.height) }
        }
        face.clipToOutline = true
        portrait.addView(face, FrameLayout.LayoutParams(dp(44), dp(44), Gravity.CENTER))
        game.r.onPortrait = { bmp -> runOnUiThread { face.setImageBitmap(bmp); (menuView as? MainMenu)?.face?.setImageBitmap(bmp) } }
        game.r.portraitReq = true
        val hh = android.os.Handler(android.os.Looper.getMainLooper())
        hh.postDelayed({ game.r.portraitReq = true }, 1500)
        hh.postDelayed({ game.r.portraitReq = true }, 4000)
        press(portrait) { abrirCriador() }
        root.addView(portrait, FrameLayout.LayoutParams(dp(50), dp(50), Gravity.TOP or Gravity.START).also { it.setMargins(dp(12), dp(8), 0, 0) })
        sideCol = LinearLayout(this)
        sideCol.orientation = LinearLayout.VERTICAL
        root.addView(sideCol, FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP or Gravity.START).also { it.setMargins(dp(17), dp(76), 0, 0) })

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

        // Etapa 88: canto superior direito — câmera, mercado e ajustes em botões de vidro colorido com brilho
        dockR = LinearLayout(this)
        dockR.orientation = LinearLayout.HORIZONTAL
        dockR.gravity = Gravity.CENTER_VERTICAL
        val dv = topBtn(Ic.CAM3P, Tn.SKY) { alternarVista() }
        viewIcon = dv.second
        dockR.addView(dv.first)
        dockR.addView(topBtn(Ic.MAP, Tn.SUN) { abrirMapa() }.first)   // Etapa 122: mapa da cidade + GPS
        dockR.addView(topBtn(Ic.WORK, Tn.CORAL) { profissoes() }.first)   // Etapa 143: profissões
        dockR.addView(topBtn(Ic.CART, Tn.SIMS_PURPLE) { loja(0) }.first)
        dockR.addView(topBtn(Ic.GEAR, Tn.MINT) { config() }.first)
        root.addView(dockR, FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP or Gravity.END).also { it.setMargins(0, dp(8), dp(10), 0) })

        // Etapa 122: faixa do GPS (próxima conversão) e minimapa redondo
        gpsHud = GpsHud(this)
        gpsHud.visibility = View.GONE
        gpsHud.elevation = dpf(6f)
        root.addView(gpsHud, FrameLayout.LayoutParams(dp(300), dp(62), Gravity.TOP or Gravity.CENTER_HORIZONTAL).also { it.topMargin = dp(66) })
        miniMap = MiniMap(this) { floatArrayOf(game.r.px, game.r.pz, game.r.fyaw) }
        miniMap.visibility = View.GONE
        miniMap.elevation = dpf(5f)
        // Etapa 125: minimapa no canto de cima (no lugar do retrato); tocar abre o mapa
        root.addView(miniMap, FrameLayout.LayoutParams(dp(118), dp(118), Gravity.TOP or Gravity.START).also { it.setMargins(dp(12), dp(8), 0, 0) })
        miniMap.setOnClickListener { abrirMapa() }
        game.r.onMap = { bmp, rect -> runOnUiThread { MapPaint.photo?.let { if (it !== bmp) it.recycle() }; MapPaint.photo = bmp; MapPaint.photoRect = rect; miniMap.invalidate(); mapView?.invalidate() } }
        mapRoot = root
        speedTv = tvShadow(tv("", 22f, Color.WHITE, true))
        speedTv.setPadding(dp(16), dp(6), dp(16), dp(8))
        speedTv.background = Ui.frost(dpf(20f), DARK, 0xB0, 0x80, dpf(1.3f))
        speedTv.visibility = View.GONE
        root.addView(speedTv, FrameLayout.LayoutParams(-2, -2, Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL).also { it.bottomMargin = dp(18) })
        val gpsTick = object : Runnable {
            override fun run() {
                val show = Gps.active && game.mode == 0 && mapView == null
                gpsHud.visibility = if (show) View.VISIBLE else View.GONE
                if (show) gpsHud.invalidate()
                val dv = game.r.driving
                val fl = game.r.flying
                speedTv.visibility = if (dv || fl) View.VISIBLE else View.GONE
                if (dv) speedTv.text = "${(kotlin.math.abs(game.r.carSpeed) * 3.6f).toInt()} km/h   ${game.r.gear}" + (if (game.r.drifting) "   DRIFT!" else "")
                else if (fl) speedTv.text = "VOANDO   ${game.r.py.toInt()} m   ${(game.r.flySpeed * 3.6f).toInt()} km/h" + (if (game.r.turbo) "   TURBO" else "")
                // Etapa 128: botão de voar e controles de voo (subir, descer, turbo)
                if (fl != wasFlying) {
                    wasFlying = fl
                    flyPad.visibility = if (fl) View.VISIBLE else View.GONE
                    flyBtn.text = if (fl) "POUSAR" else "VOAR"
                    flyBtn.background = Ui.frost(dpf(18f), if (fl) 0xE07B22 else 0x7A4DD8, 0xE0, 0xA8, dpf(2f), edge = 0xEEFFFFFF.toInt())
                    if (fl) { jumpBtn.visibility = View.GONE; crouchBtn.visibility = View.GONE }
                    else {
                        game.r.flyUp = false; game.r.flyDown = false; game.r.turbo = false; atualizarTurbo()
                        jumpBtn.visibility = if (!dv && game.mode == 0) View.VISIBLE else View.GONE
                        crouchBtn.visibility = jumpBtn.visibility
                    }
                }
                flyBtn.visibility = if (City.on && !dv && game.mode == 0 && mapView == null && (fl || jumpBtn.visibility == View.VISIBLE)) View.VISIBLE else View.GONE
                if (dv != wasDriving) {
                    // Etapa 126: dirigindo, os pedais substituem pular/agachar
                    wasDriving = dv
                    drivePad.visibility = if (dv) View.VISIBLE else View.GONE
                    jumpBtn.visibility = if (!dv && game.mode == 0) View.VISIBLE else View.GONE
                    crouchBtn.visibility = jumpBtn.visibility
                    actBox.translationY = if (dv) -dpf(150f) else 0f
                    if (!dv) { game.r.gasIn = false; game.r.brakeIn = false; game.r.hbIn = false }
                }
                // Etapa 154: se a cidade falhar ao montar, avisa na hora (em vez de ficar sem aparecer sem explicação)
                City.error?.let { e -> if (e != lastCityErr && jogando) { lastCityErr = e; msg("A cidade não carregou: $e") } }
                val mm = City.on && game.mode == 0 && mapView == null
                miniMap.visibility = if (mm) View.VISIBLE else View.GONE
                portrait.visibility = if (mm) View.GONE else View.VISIBLE   // o retrato volta quando não há cidade (sala de testes, vista aérea)
                (sideCol.layoutParams as FrameLayout.LayoutParams).topMargin = topInset + dp(if (mm) 134 else 76); sideCol.requestLayout()
                if (mm) miniMap.invalidate()
                miniMap.postDelayed(this, 120)
            }
        }
        miniMap.postDelayed(gpsTick, 500)

        // Etapa 88: canto inferior direito — pular no centro, agachar ao lado e o botão de usar logo acima (só com alvo na mira)
        actBox = FrameLayout(this)
        actBox.clipChildren = false; actBox.clipToPadding = false
        jumpBtn = FrameLayout(this)
        jumpBtn.background = Ui.frost(0f, 0x2FA8F0, 0xD8, 0x96, dpf(2f), oval = true, edge = 0xEEFFFFFF.toInt())
        jumpBtn.elevation = dpf(6f)
        jumpBtn.addView(IconView(this, Ic.JUMP, Color.WHITE, SOFT_ACC).fancy(0xAAFFFFFF.toInt()), FrameLayout.LayoutParams(dp(32), dp(32), Gravity.CENTER))
        press(jumpBtn) { if (game.mode == 0) game.r.jumpReq = true }
        actBox.addView(jumpBtn, FrameLayout.LayoutParams(dp(72), dp(72), Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(40), dp(28)) })
        crouchBtn = FrameLayout(this)
        crouchBtn.background = Ui.frost(0f, 0x3A4A66, 0xC8, 0x90, dpf(1.6f), oval = true, edge = 0xCCFFFFFF.toInt())
        crouchBtn.elevation = dpf(5f)
        crouchIc = IconView(this, Ic.CROUCH, Color.WHITE, 0xFFFFD45C.toInt()).fancy(0x99FFFFFF.toInt())
        crouchBtn.addView(crouchIc, FrameLayout.LayoutParams(dp(30), dp(30), Gravity.CENTER))
        press(crouchBtn) {
            if (game.mode == 0) {
                game.r.crouch = !game.r.crouch
                if (game.r.crouch && !CuteChar.hasCrouch()) msg("Este corpo não tem a animação de agachar")
                atualizarAgachar()
            }
        }
        actBox.addView(crouchBtn, FrameLayout.LayoutParams(dp(54), dp(54), Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(128), dp(14)) })
        // botão de usar: pílula com ícone + ação ("Abrir porta da geladeira"); aparece com uma animação curta
        useBtn = LinearLayout(this)
        useBtn.orientation = LinearLayout.HORIZONTAL
        useBtn.gravity = Gravity.CENTER_VERTICAL
        useBtn.setPadding(dp(5), dp(5), dp(16), dp(5))
        useBtn.background = Ui.chunky(Tn.SIMS_GREEN, dpf(26f), dpf(3f), true, 0xFFFFFFFF.toInt(), dpf(1.8f))
        useBtn.elevation = dpf(6f)
        val useDisc = FrameLayout(this)
        useDisc.background = Ui.frost(0f, 0x17805B, 0xF0, 0xD0, dpf(1.4f), oval = true, edge = 0xFFFFFFFF.toInt())
        useIc = IconView(this, Ic.HAND, Color.WHITE, Tn.SIMS_GREEN.edge)
        useDisc.addView(useIc, FrameLayout.LayoutParams(dp(24), dp(24), Gravity.CENTER))
        useBtn.addView(useDisc, LinearLayout.LayoutParams(dp(40), dp(40)).also { it.rightMargin = dp(9) })
        useTxt = tvShadow(tv("", 15f, Color.WHITE, true))
        useTxt.maxWidth = dp(200)
        useBtn.addView(useTxt)
        useBtn.visibility = View.GONE
        press(useBtn) { game.r.interact() }
        actBox.addView(useBtn, FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(14), dp(116)) })
        root.addView(actBox, FrameLayout.LayoutParams(dp(300), dp(220), Gravity.BOTTOM or Gravity.END))
        // Etapa 126: pedais de jogo de corrida (segurar): acelerador, freio/ré e freio de mão; o analógico vira o volante
        drivePad = FrameLayout(this)
        drivePad.clipChildren = false
        fun pedal(txt: String, tint: Int, w: Int, h: Int, endM: Int, botM: Int, on: (Boolean) -> Unit): FrameLayout {
            val f = FrameLayout(this)
            f.background = Ui.frost(dpf(18f), tint, 0xE0, 0xA8, dpf(2f), edge = 0xEEFFFFFF.toInt())
            f.elevation = dpf(6f)
            // ranhuras do pedal
            val lines = LinearLayout(this); lines.orientation = LinearLayout.VERTICAL; lines.gravity = Gravity.CENTER
            for (i in 0 until 3) { val v = View(this); v.setBackgroundColor(0x55FFFFFF); lines.addView(v, LinearLayout.LayoutParams(dp(w - 34), dp(3)).also { it.topMargin = dp(7) }) }
            f.addView(lines, FrameLayout.LayoutParams(-2, -2, Gravity.CENTER or Gravity.TOP).also { it.topMargin = dp(12) })
            val t = tvShadow(tv(txt, 12f, Color.WHITE, true)); t.gravity = Gravity.CENTER
            f.addView(t, FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM).also { it.bottomMargin = dp(10) })
            f.setOnTouchListener { v, e ->
                when (e.actionMasked) {
                    MotionEvent.ACTION_DOWN -> { on(true); v.animate().scaleX(0.92f).scaleY(0.9f).setDuration(60).start() }
                    MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> { on(false); v.animate().scaleX(1f).scaleY(1f).setDuration(90).start() }
                }
                true
            }
            drivePad.addView(f, FrameLayout.LayoutParams(dp(w), dp(h), Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(endM), dp(botM)) })
            return f
        }
        pedal("ACELERAR", 0x22B35A, 84, 128, 16, 20) { game.r.gasIn = it }
        pedal("FREIO / RÉ", 0xD83A3A, 78, 96, 112, 20) { game.r.brakeIn = it }
        pedal("FREIO DE MÃO", 0x3A4A66, 140, 50, 206, 20) { game.r.hbIn = it }
        drivePad.visibility = View.GONE
        root.addView(drivePad, FrameLayout.LayoutParams(dp(360), dp(170), Gravity.BOTTOM or Gravity.END))
        // Etapa 128: voar — liga/desliga ao lado do agachar; voando, subir e descer (segurar) e turbo (liga/desliga)
        flyBtn = tvShadow(tv("VOAR", 12f, Color.WHITE, true))
        flyBtn.gravity = Gravity.CENTER
        flyBtn.background = Ui.frost(dpf(18f), 0x7A4DD8, 0xE0, 0xA8, dpf(2f), edge = 0xEEFFFFFF.toInt())
        flyBtn.elevation = dpf(6f)
        flyBtn.visibility = View.GONE
        press(flyBtn) { game.r.flyReq = true }
        actBox.addView(flyBtn, FrameLayout.LayoutParams(dp(66), dp(40), Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(192), dp(20)) })
        flyPad = FrameLayout(this)
        flyPad.clipChildren = false
        fun hold(txt: String, tint: Int, w: Int, h: Int, endM: Int, botM: Int, on: (Boolean) -> Unit) {
            val t = tvShadow(tv(txt, 13f, Color.WHITE, true)); t.gravity = Gravity.CENTER
            t.background = Ui.frost(dpf(18f), tint, 0xE0, 0xA8, dpf(2f), edge = 0xEEFFFFFF.toInt())
            t.elevation = dpf(6f)
            t.setOnTouchListener { v, e ->
                when (e.actionMasked) {
                    MotionEvent.ACTION_DOWN -> { on(true); v.animate().scaleX(0.92f).scaleY(0.9f).setDuration(60).start() }
                    MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> { on(false); v.animate().scaleX(1f).scaleY(1f).setDuration(90).start() }
                }
                true
            }
            flyPad.addView(t, FrameLayout.LayoutParams(dp(w), dp(h), Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(endM), dp(botM)) })
        }
        hold("▲\nSUBIR", 0x2FA8F0, 78, 76, 22, 118) { game.r.flyUp = it }
        hold("▼\nDESCER", 0x3A4A66, 78, 76, 22, 30) { game.r.flyDown = it }
        turboBtn = tvShadow(tv("TURBO", 13f, Color.WHITE, true)); turboBtn.gravity = Gravity.CENTER
        turboBtn.elevation = dpf(6f)
        press(turboBtn) { game.r.turbo = !game.r.turbo; atualizarTurbo() }
        flyPad.addView(turboBtn, FrameLayout.LayoutParams(dp(78), dp(56), Gravity.BOTTOM or Gravity.END).also { it.setMargins(0, 0, dp(112), dp(40)) })
        atualizarTurbo()
        flyPad.visibility = View.GONE
        root.addView(flyPad, FrameLayout.LayoutParams(dp(300), dp(220), Gravity.BOTTOM or Gravity.END))
        var lastUseKey = ""
        val useTick = object : Runnable {
            override fun run() {
                val k = game.r.nearKind
                if (game.r.saveReq) { game.r.saveReq = false; st.save() }   // Etapa 83: objeto com física parou (grava a posição)
                if ((game.mode == 0 || k == 5) && k != 0 && game.mode != 2) {
                    val lab = game.r.nearLabel
                    if (useTxt.text.toString() != lab) useTxt.text = lab
                    val ic = when (k) { 3 -> Ic.SEAT; 7, 8 -> Ic.BED; 5, 21 -> Ic.BACK; 20 -> Ic.CAR; else -> Ic.HAND }
                    if (useIc.kind != ic) useIc.set(ic)
                    val key = "$k|$lab"
                    if (useBtn.visibility != View.VISIBLE) {
                        useBtn.visibility = View.VISIBLE
                        useBtn.scaleX = 0.6f; useBtn.scaleY = 0.6f; useBtn.alpha = 0f
                        useBtn.pivotX = useBtn.width.toFloat().coerceAtLeast(dpf(120f)); useBtn.pivotY = dpf(25f)
                        useBtn.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(160).start()
                    } else if (key != lastUseKey) {
                        useBtn.animate().cancel()
                        useBtn.scaleX = 0.92f; useBtn.scaleY = 0.92f
                        useBtn.animate().scaleX(1f).scaleY(1f).setDuration(120).start()
                    }
                    lastUseKey = key
                } else if (useBtn.visibility != View.GONE) { useBtn.visibility = View.GONE; lastUseKey = "" }
                if (crouchOn != game.r.crouch) atualizarAgachar()
                useBtn.postDelayed(this, 80)
            }
        }
        useBtn.post(useTick)

        creator = CreatorUi(this, st, game) { fecharCriador() }
        creator.visibility = View.GONE
        root.addView(creator, FrameLayout.LayoutParams(-1, -1))

        setContentView(root)

        ViewCompat.setOnApplyWindowInsetsListener(root) { _, ins ->
            val b = ins.getInsets(WindowInsetsCompat.Type.systemBars())
            hud.setPadding(dp(12) + b.left, b.top + dp(6), dp(12) + b.right, dp(4))
            bottom.setPadding(0, 0, 0, b.bottom + dp(8))
            (actBox.layoutParams as FrameLayout.LayoutParams).setMargins(0, 0, b.right, b.bottom)
            (portrait.layoutParams as FrameLayout.LayoutParams).setMargins(dp(12) + b.left, b.top + dp(8), 0, 0)
            (sideCol.layoutParams as FrameLayout.LayoutParams).setMargins(dp(17) + b.left, b.top + dp(76), 0, 0)
            topInset = b.top
            if (::miniMap.isInitialized) { (miniMap.layoutParams as FrameLayout.LayoutParams).setMargins(dp(12) + b.left, b.top + dp(8), 0, 0); miniMap.requestLayout() }
            portrait.requestLayout(); sideCol.requestLayout()
            (dockR.layoutParams as FrameLayout.LayoutParams).setMargins(0, b.top + dp(8), dp(10) + b.right, 0)
            dockR.requestLayout()
            actBox.requestLayout()
            bottomInset = b.bottom
            val cb = ins.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout())
            creator.setInsets(cb.left, cb.top, cb.right, cb.bottom)
            (msgTv.layoutParams as FrameLayout.LayoutParams).topMargin = b.top + dp(56)
            ins
        }

        // Resolução dinâmica com prioridade para nitidez: começa na resolução máxima e só reduz em quedas persistentes de FPS.
        game.r.showFps = getSharedPreferences("meular", MODE_PRIVATE).getBoolean("fps", false)
        game.post(object : Runnable {
            override fun run() { ajustarResolucao(); game.postDelayed(this, 1200) }
        })

        game.onFocus = { item, grabbed -> aoMudarFoco(item, grabbed) }
        game.onChanged = { st.save() }
        atualizarDinheiro(false)
        Updater.autoCheck(this)
        abrirMenu(root)
    }

    private var modTarget: String? = null

    /** Abre o seletor de arquivos para importar .package (target = id da peça que recebe a textura, ou null). */
    fun pickMods(target: String?) {
        modTarget = target
        val i = android.content.Intent(android.content.Intent.ACTION_OPEN_DOCUMENT)
        i.addCategory(android.content.Intent.CATEGORY_OPENABLE)
        i.type = "*/*"
        i.putExtra(android.content.Intent.EXTRA_ALLOW_MULTIPLE, true)
        startActivityForResult(i, 4711)
    }

    @Suppress("DEPRECATION")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: android.content.Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != 4711 || resultCode != RESULT_OK || data == null) return
        val uris = ArrayList<android.net.Uri>()
        data.data?.let { uris.add(it) }
        val cd = data.clipData
        if (cd != null) for (k in 0 until cd.itemCount) uris.add(cd.getItemAt(k).uri)
        if (uris.isEmpty()) return
        creator.modsChanged("Importando ${uris.size} arquivo(s)...")
        ModStore.importAsync(this, uris, modTarget) { msg -> runOnUiThread { creator.modsChanged(msg) } }
    }

    override fun onResume() { super.onResume(); game.onResume() }

    override fun onPause() { super.onPause(); st.save(); game.onPause() }

    // ------------------------------------------------------------ HUD

    private fun atualizarDinheiro(pulso: Boolean) {
        moneyTv.text = "\u221E"
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
        portrait.visibility = View.GONE
        sideCol.visibility = View.GONE
        jumpBtn.visibility = View.GONE
        crouchBtn.visibility = View.GONE
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
        portrait.visibility = View.VISIBLE
        game.r.portraitReq = true
        sideCol.visibility = View.VISIBLE
        game.mode = prevMode
        jumpBtn.visibility = if (prevMode == 0) View.VISIBLE else View.GONE
        crouchBtn.visibility = jumpBtn.visibility
        viewIcon.set(iconeCamera(prevMode, game.third))
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (mapView != null) { fecharMapa(); return }
        if (menuView != null || loadView != null) { finish(); return }
        if (game.mode == 2) fecharCriador() else super.onBackPressed()
    }

    /** Ícone da câmera atual: 3ª pessoa, 1ª pessoa (olho do personagem) ou vista aérea. */
    private fun iconeCamera(mode: Int, third: Boolean) = if (mode == 1) Ic.CAMAIR else if (third) Ic.CAM3P else Ic.CAM1P

    private lateinit var speedTv: TextView
    private var topInset = 0
    private lateinit var gpsHud: GpsHud
    private lateinit var miniMap: MiniMap
    private lateinit var mapRoot: FrameLayout
    private var mapView: MapOverlay? = null

    /** Etapa 122: mapa da cidade em tela cheia; tocar num ponto e "Ir com GPS" traça a rota. */
    private fun abrirMapa() {
        if (!City.on) { msg("O mapa da cidade não existe na sala de testes"); return }
        if (mapView != null) return
        val mv = MapOverlay(this, { floatArrayOf(game.r.px, game.r.pz, game.r.fyaw) }) { fecharMapa() }
        mv.alpha = 0f; mv.scaleX = 0.96f; mv.scaleY = 0.96f
        mapRoot.addView(mv, FrameLayout.LayoutParams(-1, -1))
        mv.elevation = dpf(20f)
        mv.animate().alpha(1f).scaleX(1f).scaleY(1f).setDuration(180).start()
        mapView = mv
    }

    private fun fecharMapa() {
        val mv = mapView ?: return
        mapView = null
        mv.animate().alpha(0f).setDuration(140).withEndAction { mapRoot.removeView(mv) }.start()
        if (Gps.active) msg("GPS ligado: siga a faixa azul")
    }

    private fun alternarVista() {
        if (game.mode == 2) return
        // ciclo: 3ª pessoa -> 1ª pessoa -> vista aérea -> 3ª pessoa
        val msgTxt: String
        if (game.mode == 0 && game.third) { game.third = false; msgTxt = "1ª pessoa: você vê pelos olhos do personagem" }
        else if (game.mode == 0) { game.mode = 1; msgTxt = "Vista aérea: toque no chão para andar, arraste os móveis" }
        else { game.third = true; game.mode = 0; msgTxt = "3ª pessoa" }
        viewIcon.set(iconeCamera(game.mode, game.third))
        jumpBtn.visibility = if (game.mode == 0) View.VISIBLE else View.GONE
        crouchBtn.visibility = jumpBtn.visibility
        if (game.mode != 0) { game.r.crouch = false; atualizarAgachar() }
        editBar.visibility = View.GONE
        if (game.mode == 1) st.save()
        msg(msgTxt)
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
        msg("${s.type.nome} guardado")
    }

    // ------------------------------------------------------------ loja

    private class Entry(val titulo: String, val sub: String, val icon: Int, val swatch: Int, val ok: Boolean, val thumb: String? = null, val acao: () -> Unit)

    /** Etapa 83: miniaturas dos objetos da biblioteca 3D (assets/obj3d/thumb/<id>.png) */
    private val thumbs = HashMap<String, android.graphics.Bitmap?>()
    private fun thumb(id: String): android.graphics.Bitmap? = thumbs.getOrPut(id) {
        try { assets.open("obj3d/thumb/$id.png").use { android.graphics.BitmapFactory.decodeStream(it) } } catch (e: Exception) { null }
    }

    private class VH(val root: LinearLayout, val icon: IconView, val sw: View, val img: ImageView, val name: TextView, val price: TextView) : RecyclerView.ViewHolder(root)

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
            val img = ImageView(this@MainActivity)
            img.scaleType = ImageView.ScaleType.FIT_CENTER
            img.background = Ui.bg(0x406CA0FF, dpf(14f))
            img.setPadding(dp(4), dp(4), dp(4), dp(4))
            l.addView(img, LinearLayout.LayoutParams(dp(62), dp(62)))
            val n = tv("", 12f, Pal.TEXT, true)
            n.gravity = Gravity.CENTER
            n.maxLines = 2
            l.addView(n, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(6) })
            val pr = tv("", 12f, Pal.GOLD, true)
            pr.gravity = Gravity.CENTER
            l.addView(pr, LinearLayout.LayoutParams(-2, -2).also { it.topMargin = dp(2) })
            return VH(l, ic, sw, img, n, pr)
        }

        override fun onBindViewHolder(h: VH, i: Int) {
            val e = data[i]
            val tb = e.thumb?.let { thumb(it) }
            if (tb != null) {
                h.icon.visibility = View.GONE
                h.sw.visibility = View.GONE
                h.img.visibility = View.VISIBLE
                h.img.setImageBitmap(tb)
            } else if (e.swatch != 0) {
                h.img.visibility = View.GONE
                h.icon.visibility = View.GONE
                h.sw.visibility = View.VISIBLE
                h.sw.background = Ui.oval(e.swatch, Color.parseColor("#99FFF4E6"), dpf(2.5f))
            } else {
                h.img.visibility = View.GONE
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
            for (t in Type.values()) if (t.cat == tab) out.add(Entry(t.nome, "Grátis", t.ordinal, 0, st.money >= t.preco, t.glb) { comprar(t) })
        } else if (tab == 4) {
            Finish.floors.forEachIndexed { i, f ->
                val own = (st.ownFloors shr i) and 1 == 1
                val sub = if (st.floorIdx == i) "Em uso" else if (own) "Comprado" else "Grátis"
                out.add(Entry("Piso\n${f.nome}", sub, 0, f.amostra, own || st.money >= f.preco) { comprarPiso(i) })
            }
            Finish.walls.forEachIndexed { i, w ->
                val own = (st.ownWalls shr i) and 1 == 1
                val sub = if (st.wallIdx == i) "Em uso" else if (own) "Comprado" else "Grátis"
                out.add(Entry("Parede\n${w.nome}", sub, 0, w.cor, own || st.money >= w.preco) { comprarParede(i) })
            }
        } else if (tab == 6) {
            // Etapa 123: garagem — escolher o veículo (fica na rua em frente de casa) e a cor
            for ((k, nome) in VEICULOS) {
                val sel = st.vehKind == k
                out.add(Entry(nome, if (sel) "Seu veículo" else "Grátis", if (k == Vehicles.MOTO || k == Vehicles.SCOOTER) Ic.MOTO else Ic.CAR, 0, true) {
                    st.vehKind = k; st.save(); refreshShop()
                    msg("${nome.replace("\n", " ")} está na rua em frente de casa. Chegue perto e toque em Dirigir.")
                })
            }
            for ((nome, cor) in CORES_VEIC) {
                out.add(Entry("Pintura\n$nome", if (st.vehColor == cor) "Em uso" else "Grátis", 0, cor, st.vehKind >= 0) {
                    if (st.vehKind < 0) msg("Escolha um veículo primeiro")
                    else { st.vehColor = cor; st.save(); refreshShop() }
                })
            }
            if (st.vehKind >= 0) out.add(Entry("Trazer para\ncasa", "Grátis", Ic.HOME, 0, true) { game.r.resetCar(); msg("Seu veículo voltou para a frente de casa") })
        } else {
            if (st.podeAmpliar()) {
                val p = st.precoAmpliar()
                out.add(Entry("Ampliar casa\n${st.gw}x${st.gh} → ${st.gw + 1}x${st.gh + 1}", "Grátis", Ic.HOME, 0, st.money >= p) { ampliarCasa() })
            } else {
                out.add(Entry("Tamanho máximo\n${st.gw}x${st.gh}", "—", Ic.HOME, 0, false) { })
            }
        }
        return out
    }

    private val VEICULOS = listOf(Vehicles.SEDAN to "Sedã", Vehicles.HATCH to "Hatch", Vehicles.SUV to "SUV", Vehicles.PICKUP to "Picape", Vehicles.SPORT to "Esportivo",
        Vehicles.TAXI to "Táxi", Vehicles.VAN to "Van", Vehicles.POLICE to "Viatura", Vehicles.MOTO to "Moto\nesportiva", Vehicles.SCOOTER to "Scooter")
    private val CORES_VEIC = listOf("Vermelho" to 0xFFC62828.toInt(), "Azul" to 0xFF1565C0.toInt(), "Branco" to 0xFFF5F5F5.toInt(), "Preto" to 0xFF212121.toInt(), "Prata" to 0xFFB0BEC5.toInt(),
        "Verde" to 0xFF2E7D32.toInt(), "Amarelo" to 0xFFF9A825.toInt(), "Laranja" to 0xFFE65100.toInt(), "Roxo" to 0xFF6A1B9A.toInt(), "Rosa" to 0xFFEC407A.toInt())

    // ---------------------------------------------------------------- Etapa 123: menu inicial e carregamento
    private var menuView: View? = null
    private var loadView: View? = null
    private var jogando = false

    private fun abrirMenu(root: FrameLayout) {
        val ver = try { "versão " + packageManager.getPackageInfo(packageName, 0).versionName } catch (e: Exception) { "" }
        val m = MainMenu(this, ver, "Meu Lar · casa ${st.gw}×${st.gh}", st.money.toString(), { jogar(root) }, { fecharMenu(); jogando = true; abrirCriador() }, { mostrarNovidades(true) }, { config() })
        m.elevation = dpf(40f)
        root.addView(m, FrameLayout.LayoutParams(-1, -1))
        menuView = m
        // foto de corpo inteiro do personagem para o centro do menu (o renderizador tira quando o corpo terminar de carregar)
        game.r.onFullBody = { bmp -> runOnUiThread { (menuView as? MainMenu)?.setSim(bmp) } }
        game.r.fullReq = true
        val hh = android.os.Handler(android.os.Looper.getMainLooper())
        for (t in longArrayOf(1500, 4000, 8000)) hh.postDelayed({ if (menuView != null && (menuView as? MainMenu)?.sim?.drawable == null) game.r.fullReq = true }, t)
        // o jogo fechou da última vez? mostra o erro para poder mandar
        val cp = getSharedPreferences("crash", MODE_PRIVATE)
        cp.getString("last", null)?.let { txt ->
            cp.edit().remove("last").apply()
            android.app.AlertDialog.Builder(this).setTitle("O jogo fechou da última vez")
                .setMessage("Copie e mande este texto para corrigir:\n\n" + txt.take(1200))
                .setPositiveButton("Copiar") { _, _ ->
                    val cm = getSystemService(android.content.ClipboardManager::class.java)
                    cm?.setPrimaryClip(android.content.ClipData.newPlainText("erro", txt)); msg("Erro copiado")
                }
                .setNegativeButton("Fechar", null).show()
        }
    }

    private fun fecharMenu() {
        val m = menuView ?: return
        menuView = null
        m.animate().alpha(0f).setDuration(300).withEndAction { (m.parent as? ViewGroup)?.removeView(m) }.start()
    }

    /** Jogar: some o menu e entra a tela de carregamento até a cidade e os quarteirões em volta estarem prontos. */
    private var lastCityErr: String? = null
    private fun jogar(root: FrameLayout) {
        if (loadView != null) return
        val ld = LoadingScreen(this, {
            if (st.testRoom) 1f
            else if (City.error != null) 1f
            else if (!City.on) City.progress * 0.85f
            else 0.85f + 0.15f * City.nearFraction(game.r.px, game.r.pz)
        }) {
            val lv = loadView
            loadView = null
            jogando = true
            lv?.animate()?.alpha(0f)?.setDuration(450)?.withEndAction { (lv.parent as? ViewGroup)?.removeView(lv) }?.start()
            City.error?.let { msg("A cidade não carregou: $it") }
            mostrarNovidades()
            if (!st.avatarSet) root.post { abrirCriador() }
        }
        ld.elevation = dpf(41f)
        ld.alpha = 0f
        root.addView(ld, FrameLayout.LayoutParams(-1, -1))
        ld.animate().alpha(1f).setDuration(250).withEndAction { fecharMenu() }.start()
        loadView = ld
    }

    private fun refreshShop() {
        shopAdapter?.data = entries(shopTab)
        shopAdapter?.notifyDataSetChanged()
        shopMoney?.text = "\u221E"
        for ((i, t) in tabViews.withIndex()) {
            val sel = i == shopTab
            t.background = Ui.chunky(if (sel) Tn.CORAL else Tn.GHOST, dpf(20f), dpf(3f), sel)
            t.setTextColor(if (sel) Color.WHITE else Pal.SUB)
        }
    }

    private fun sheet(titulo: String, ic: Int = -1, tone: Tone = Tn.LAV, rolavel: Boolean = true, build: (LinearLayout) -> Unit): Dialog {
        val d = Dialog(this)
        d.requestWindowFeature(Window.FEATURE_NO_TITLE)
        val panel = LinearLayout(this)
        panel.orientation = LinearLayout.VERTICAL
        panel.background = Ui.sheetBg(dpf(30f), dpf(2f))
        panel.setPadding(dp(16), dp(14), dp(16), dp(16) + bottomInset)
        // alça no topo
        val grip = View(this)
        grip.background = Ui.bg(0x555CB4E4, dpf(3f))
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
        // conteúdo com rolagem: antes as opções passavam do fim da tela e não dava para descer
        val rolar = object : android.widget.ScrollView(this) {
            override fun onMeasure(w: Int, h: Int) {
                super.onMeasure(w, View.MeasureSpec.makeMeasureSpec((resources.displayMetrics.heightPixels * 0.62f).toInt(), View.MeasureSpec.AT_MOST))
            }
        }
        rolar.isVerticalScrollBarEnabled = false
        rolar.overScrollMode = View.OVER_SCROLL_NEVER
        val corpo = LinearLayout(this)
        corpo.orientation = LinearLayout.VERTICAL
        rolar.addView(corpo, ViewGroup.LayoutParams(-1, -2))
        if (rolavel) { panel.addView(rolar, LinearLayout.LayoutParams(-1, -2)); build(corpo) } else build(panel)
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
        val d = sheet("Loja", Ic.SHOP, Tn.MINT, false) { panel ->
            val money = tvShadow(tv("\u221E", 18f, Pal.GOLD, true))
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
            val nomes = listOf("Sala", "Quarto", "Cozinha", "Decoração", "Piso e parede", "Casa", "Veículos")
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
            // a grade cabe na tela (deitado, a altura é pequena: antes a 2ª linha ficava fora e não dava para rolar)
            val dm = resources.displayMetrics
            val deitado = dm.widthPixels > dm.heightPixels
            val rv = RecyclerView(this)
            rv.layoutManager = GridLayoutManager(this, if (deitado) 5 else 3)
            rv.adapter = adapter
            rv.isNestedScrollingEnabled = true
            rv.overScrollMode = View.OVER_SCROLL_IF_CONTENT_SCROLLS
            val alturaLivre = dm.heightPixels - dp(235) - bottomInset
            panel.addView(rv, LinearLayout.LayoutParams(-1, alturaLivre.coerceIn(dp(150), dp(310))))
        }
        shopDialog = d
        refreshShop()
        d.show()
    }

    private fun comprar(t: Type) {
        if (st.money < t.preco) { msg("Dinheiro insuficiente."); return }
        val alvo = game.frontTarget()
        val spot = st.findPlaceNear(t, alvo[0], alvo[1])
        if (spot == null) { msg("Sem espaço na casa. Venda algo ou amplie."); return }
        st.money -= t.preco
        val novo = Item(t, spot[0].toInt(), spot[1].toInt())
        novo.ox = spot[2]
        novo.oz = spot[3]
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

    /** Etapa 70: liga/desliga a sala de testes (todos os móveis e decorações do jogo, sem mexer na sua casa). */
    private fun alternarSalaTestes() {
        game.selected = null
        game.r.grabbed = null
        val entrar = !st.testRoom
        // roda na thread do OpenGL: montar a sala lê as malhas dos móveis (texturas)
        game.queueEvent {
            if (entrar) st.enterTest() else st.exitTest()
            game.r.resetPlayer()
            runOnUiThread {
                atualizarDinheiro(false)
                msg(if (entrar) "Sala de testes: tudo do jogo está aqui. Nada do que você mexer aqui é salvo." else "Voltou para a sua casa.")
                refreshShop()
            }
        }
    }

    private fun ampliarCasa() {
        if (!st.podeAmpliar()) { msg("A casa já está no tamanho máximo."); return }
        val preco = st.precoAmpliar()
        if (st.money < preco) { msg("Dinheiro insuficiente."); return }
        st.money -= preco; st.gw += 1; st.gh += 1
        st.save(); atualizarDinheiro(true); refreshShop()
        msg("Casa ampliada para ${st.gw}x${st.gh}!")
    }

    // ------------------------------------------------------------ Etapa 143: profissões

    private fun lugarDe(j: Jobs.Job): City.Place? = City.places.firstOrNull { it.name == j.place }
        ?: Town.urban.firstOrNull { it.type == "job:" + j.id }?.let { City.Place(j.place, (it.x0 + it.x1) / 2, (it.z0 + it.z1) / 2, 0, 'T') }
    private fun distAte(j: Jobs.Job): Float { val p = lugarDe(j) ?: return Float.MAX_VALUE; return kotlin.math.hypot(p.x - game.r.px, p.z - game.r.pz) }
    private fun moeda(v: Long) = "R$ " + String.format(java.util.Locale("pt", "BR"), "%,d", v)

    /** Lista das profissões por nível: atual no topo, bater ponto, ir com GPS e escolher outra. */
    private fun profissoes() {
        if (!City.on) { msg("As profissões ficam na cidade, não na sala de testes"); return }
        var dlg: Dialog? = null
        dlg = sheet("Profissões", Ic.WORK, Tn.CORAL) { panel ->
            val atual = Jobs.byId(st.job)
            val nivelAtual = (1..4).lastOrNull { Jobs.unlocked(it, st.shifts) } ?: 1
            val prox = Jobs.NEED.getOrNull(nivelAtual + 1)
            val resumo = tv(if (atual == null) "Você ainda não tem emprego. Escolha um do nível 1 para começar." else
                "${atual.name} em ${atual.place}\nSalário: ${moeda(atual.salary.toLong())} por turno · Vantagem: ${atual.perk}", 14f, Pal.TEXT, true)
            resumo.setPadding(dp(14), dp(12), dp(14), dp(12)); resumo.background = Ui.chunky(Tn.CARD, dpf(20f), dpf(3f), false, Pal.LINE, dpf(1f))
            panel.addView(resumo, LinearLayout.LayoutParams(-1, -2).also { it.bottomMargin = dp(8) })
            val info = tv("Turnos: ${st.shifts} · Total ganho: ${moeda(st.earned)}" + (if (prox != null && nivelAtual < 4) " · Nível ${nivelAtual + 1} com ${prox} turnos" else " · Todos os níveis liberados"), 13f, Pal.SUB, false)
            panel.addView(info, LinearLayout.LayoutParams(-1, -2).also { it.bottomMargin = dp(10); it.leftMargin = dp(4) })
            if (atual != null) {
                val d = distAte(atual)
                linha(panel, Ic.CHECK, if (d < 30f) "Bater ponto (trabalhar um turno)" else "Bater ponto: vá até ${atual.place}", Tn.MINT) {
                    val agora = System.currentTimeMillis()
                    if (distAte(atual) >= 30f) { dlg?.dismiss(); irPara(atual); return@linha }
                    if (agora - st.lastShift < Jobs.SHIFT_MS) { msg("Descanse um pouco: o próximo turno libera em ${((Jobs.SHIFT_MS - (agora - st.lastShift)) / 1000)} s"); return@linha }
                    val antes = (1..4).lastOrNull { Jobs.unlocked(it, st.shifts) } ?: 1
                    st.shifts++; st.earned += atual.salary; st.lastShift = agora; st.save(); dlg?.dismiss()
                    val depois = (1..4).lastOrNull { Jobs.unlocked(it, st.shifts) } ?: 1
                    msg(if (depois > antes) "Turno feito! +${moeda(atual.salary.toLong())} · Nível ${depois} liberado!" else "Turno feito! +${moeda(atual.salary.toLong())}")
                }
                linha(panel, Ic.MAP, "Ir com GPS até ${atual.place}", Tn.SUN) { dlg?.dismiss(); irPara(atual) }
            }
            for (lv in 1..4) {
                val livre = Jobs.unlocked(lv, st.shifts)
                val cab = tv("Nível $lv · ${Jobs.LEVEL_NAME[lv]}" + (if (livre) "" else "  🔒 ${Jobs.NEED[lv]} turnos"), 15f, if (livre) Pal.TEXT else Pal.SUB, true)
                panel.addView(cab, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(8); it.bottomMargin = dp(6); it.leftMargin = dp(4) })
                for (j in Jobs.ALL.filter { it.level == lv }) {
                    val eu = j.id == st.job
                    val tone = if (eu) Tn.MINT else if (livre) arrayOf(Tn.SKY, Tn.LAV, Tn.SUN, Tn.ROSE)[lv - 1] else Tn.GHOST
                    linha(panel, Ic.WORK, "${j.name}${if (eu) " · atual" else ""}\n${moeda(j.salary.toLong())}/turno · ${j.place}", tone) { detalheProfissao(j) { dlg?.dismiss() } }
                }
            }
        }
        dlg?.show()
    }

    private fun detalheProfissao(j: Jobs.Job, fechar: () -> Unit) {
        var dlg: Dialog? = null
        dlg = sheet(j.name, Ic.WORK, Tn.CORAL) { panel ->
            val livre = Jobs.unlocked(j.level, st.shifts)
            val txt = tv("Local: ${j.place}\nNível ${j.level} (${Jobs.LEVEL_NAME[j.level]})\nSalário: ${moeda(j.salary.toLong())} por turno\nVantagem: ${j.perk}" +
                (if (j.requires.isNotEmpty()) "\nFormação: ${j.requires}" else "") + "\nMinigame: em breve", 15f, Pal.TEXT, false)
            txt.setPadding(dp(14), dp(12), dp(14), dp(12)); txt.background = Ui.chunky(Tn.CARD, dpf(20f), dpf(3f), false, Pal.LINE, dpf(1f))
            panel.addView(txt, LinearLayout.LayoutParams(-1, -2).also { it.bottomMargin = dp(10) })
            if (j.id == st.job) linha(panel, Ic.CLOSE, "Pedir demissão", Tn.ROSE) { st.job = ""; st.save(); dlg?.dismiss(); fechar(); msg("Você saiu de ${j.place}") }
            else if (livre) linha(panel, Ic.CHECK, "Trabalhar aqui", Tn.MINT) { st.job = j.id; st.save(); dlg?.dismiss(); fechar(); msg("Contratado(a) como ${j.name}! Vá até ${j.place} para bater ponto.") }
            else linha(panel, Ic.CLOSE, "Bloqueado: precisa de ${Jobs.NEED[j.level]} turnos (você tem ${st.shifts})", Tn.GHOST) { }
            linha(panel, Ic.MAP, "Ver no mapa com GPS", Tn.SUN) { dlg?.dismiss(); fechar(); irPara(j) }
        }
        dlg?.show()
    }

    private fun irPara(j: Jobs.Job) {
        val p = lugarDe(j) ?: run { msg("${j.place} ainda não apareceu no mapa"); return }
        Gps.setDest(p.x, p.z, j.place, game.r.px, game.r.pz); msg("GPS ligado até ${j.place}: siga a faixa azul")
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
            linha(panel, Ic.HOME, if (st.testRoom) "Sair da sala de testes" else "Sala de testes", Tn.SUN) { dlg?.dismiss(); alternarSalaTestes() }
            var fpsT: TextView? = null
            fpsT = linha(panel, Ic.INFO, if (game.r.showFps) "Contador de FPS: ligado" else "Contador de FPS: desligado", Tn.MINT) {
                game.r.showFps = !game.r.showFps
                getSharedPreferences("meular", MODE_PRIVATE).edit().putBoolean("fps", game.r.showFps).apply()
                fpsT?.text = if (game.r.showFps) "Contador de FPS: ligado" else "Contador de FPS: desligado"
            }
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
