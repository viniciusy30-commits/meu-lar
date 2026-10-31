package com.vinicius.meular

import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView

/** Tela do personagem: só mostra o personagem novo (pack Cute Characters) girando, com o botão "Pronto". */
class CreatorUi(
    ctx: Context,
    private val st: GameState,
    private val game: GameView,
    private val onDone: () -> Unit
) : FrameLayout(ctx) {

    private val d = ctx.resources.displayMetrics.density
    private fun dp(v: Int) = (v * d).toInt()
    private fun dpf(v: Float) = v * d

    private val panel = LinearLayout(ctx)

    init {
        panel.orientation = LinearLayout.VERTICAL
        panel.setPadding(dp(14), dp(12), dp(14), dp(12))
        val ok = TextView(ctx)
        ok.text = "Pronto"
        ok.textSize = 18f
        ok.typeface = Ui.BOLD
        ok.setTextColor(Color.WHITE)
        ok.gravity = Gravity.CENTER
        ok.background = Ui.bg(Pal.GREEN, dpf(22f))
        ok.setOnClickListener { st.avatarSet = true; st.save(); onDone() }
        panel.addView(ok, LinearLayout.LayoutParams(-1, dp(50)))
        addView(panel, LayoutParams(-1, -2, Gravity.BOTTOM))
    }

    fun setInsets(topPx: Int, bottomPx: Int) {
        panel.setPadding(dp(14), dp(12), dp(14), dp(12) + bottomPx)
    }

    fun open() { camera() }

    private fun camera() {
        // corpo inteiro (≈1,5 m)
        game.r.cTargetDist = 4.2f
        game.r.cTargetY = 0.85f
    }
}
