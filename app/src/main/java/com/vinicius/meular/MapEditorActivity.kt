package com.vinicius.meular

import android.app.Activity
import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.os.Bundle
import android.view.Gravity
import android.view.MotionEvent
import android.view.ScaleGestureDetector
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.FrameLayout
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import org.json.JSONObject
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min

/**
 * Etapa 187: editor de mapas. Vista de cima do mapa de 1000 x 800 m: desenhe ruas, avenidas, vias expressas e viadutos,
 * rotatórias, rios (água) com pontes automáticas, suba/desça o terreno, escolha onde fica cada casa (a Casa 1 é a do jogador)
 * e plante árvores. Dois dedos: zoom e arrastar. Ao sair, o mapa é salvo e vira a "Cidade 4" nas Configurações.
 */
class MapEditorActivity : Activity() {
    private lateinit var mv: MapView
    private lateinit var hint: TextView
    private lateinit var btnSize: Button
    private lateinit var btnHouse: Button
    private val toolBtns = ArrayList<Button>()

    private val names = arrayOf("Mover", "Rua", "Avenida", "Via expressa", "Viaduto", "Rotatória", "Casa", "Árvores", "Rio/Lago", "Subir terra", "Descer terra", "Nivelar", "Borracha")
    private val hints = arrayOf(
        "Arraste para mover o mapa. Dois dedos: zoom.",
        "Toque para marcar os pontos da rua (curvas ficam suaves) e toque em Concluir. Encosta numa rua ou rotatória para ligar.",
        "Avenida (mais larga, com cerca e grama). Toque os pontos e Concluir.",
        "Via expressa larga. Toque os pontos e Concluir.",
        "Viaduto: sobe, passa por cima das outras ruas e desce. Toque os pontos e Concluir.",
        "Toque onde quer a rotatória (Tamanho muda o raio). Termine as ruas perto dela para encaixar.",
        "Escolha o número da casa e toque (ou arraste) para posicionar. A frente da casa olha para o norte (cima).",
        "Arraste para plantar árvores.",
        "Arraste para cavar rio ou lago. Ruas que cruzam a água viram ponte sozinhas.",
        "Arraste para fazer morro.",
        "Arraste para fazer vale ou buraco.",
        "Arraste para voltar o terreno ao nível normal (aterra água).",
        "Toque numa rua, rotatória ou casa para apagar. Arraste para apagar árvores.")

    override fun onCreate(b: Bundle?) {
        super.onCreate(b)
        UserMap.init(filesDir)
        val root = FrameLayout(this)
        mv = MapView(this)
        root.addView(mv, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))

        val top = LinearLayout(this)
        top.orientation = LinearLayout.HORIZONTAL
        top.setBackgroundColor(Color.argb(200, 20, 24, 32))
        top.gravity = Gravity.CENTER_VERTICAL
        hint = TextView(this); hint.setTextColor(Color.WHITE); hint.textSize = 12f; hint.setPadding(dp(10), dp(4), dp(10), dp(4))
        top.addView(hint, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        fun tb(t: String, act: () -> Unit): Button {
            val bt = Button(this); bt.text = t; bt.textSize = 12f; bt.isAllCaps = false
            bt.setTextColor(Color.WHITE); bt.setBackgroundColor(Color.argb(255, 58, 70, 92))
            bt.setPadding(dp(8), 0, dp(8), 0); bt.minHeight = 0; bt.minimumHeight = dp(36); bt.minWidth = 0; bt.minimumWidth = 0
            bt.setOnClickListener { act() }
            val lp = LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, dp(38)); lp.setMargins(dp(3), dp(3), dp(3), dp(3))
            top.addView(bt, lp)
            return bt
        }
        tb("Concluir") { mv.finishRoad() }
        tb("Voltar ponto") { mv.backPoint() }
        tb("Desfazer") { mv.undo() }
        btnSize = tb("Tamanho: 16 m") { mv.cycleSize() }
        btnHouse = tb("Casa 1") { mv.cycleHouse() }
        tb("Salvar e sair") { UserMap.save(); Toast.makeText(this, "Mapa salvo. Escolha a Cidade 4 em Configurações.", Toast.LENGTH_LONG).show(); finish() }
        root.addView(top, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP))

        val bar = LinearLayout(this)
        bar.orientation = LinearLayout.HORIZONTAL
        bar.setBackgroundColor(Color.argb(200, 20, 24, 32))
        for ((i, n) in names.withIndex()) {
            val bt = Button(this); bt.text = n; bt.textSize = 12f; bt.isAllCaps = false; bt.setTextColor(Color.WHITE)
            bt.minHeight = 0; bt.minimumHeight = dp(38); bt.minWidth = 0; bt.minimumWidth = dp(56)
            bt.setOnClickListener { selectTool(i) }
            val lp = LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, dp(42)); lp.setMargins(dp(3), dp(3), dp(3), dp(3))
            bar.addView(bt, lp); toolBtns.add(bt)
        }
        val hs = HorizontalScrollView(this)
        hs.addView(bar)
        root.addView(hs, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM))
        setContentView(root)
        selectTool(0)
    }

    override fun onPause() {
        super.onPause()
        UserMap.save()
    }

    private fun dp(v: Int): Int = (v * resources.displayMetrics.density).toInt()

    fun selectTool(i: Int) {
        mv.setTool(i)
        hint.text = names[i] + ": " + hints[i]
        for ((k, b) in toolBtns.withIndex()) b.setBackgroundColor(if (k == i) Color.argb(255, 255, 140, 60) else Color.argb(255, 58, 70, 92))
    }

    fun refreshButtons() {
        btnSize.text = "Tamanho: " + mv.sizeM().toInt() + " m"
        btnHouse.text = "Casa " + (mv.house + 1)
    }

    // =====================================================================================================
    inner class MapView(ctx: Context) : View(ctx) {
        var tool = 0
        var house = 0
        private val sizes = floatArrayOf(10f, 16f, 24f, 34f)
        private var sizeI = 1
        private var scale = 0.5f
        private var offX = 0f
        private var offY = 0f
        private var inited = false
        private val cur = ArrayList<FloatArray>()
        private val undoStack = ArrayList<String>()
        private var bmp: Bitmap? = null
        private var bmpDirty = true
        private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
        private val rnd = java.util.Random(7)
        private val scaler = ScaleGestureDetector(ctx, object : ScaleGestureDetector.SimpleOnScaleGestureListener() {
            override fun onScale(d: ScaleGestureDetector): Boolean {
                val ns = (scale * d.scaleFactor).coerceIn(0.15f, 8f)
                val fx = d.focusX; val fy = d.focusY
                offX = fx - (fx - offX) * ns / scale; offY = fy - (fy - offY) * ns / scale
                scale = ns; invalidate(); return true
            }
        })
        private var downX = 0f
        private var downY = 0f
        private var downT = 0L
        private var lastX = 0f
        private var lastY = 0f
        private var moved = false
        private var multi = false
        private var lastBrushX = -1e9f
        private var lastBrushZ = -1e9f
        private var lastTreeX = -1e9f
        private var lastTreeZ = -1e9f
        private var cx0 = 0f
        private var cy0 = 0f

        fun sizeM(): Float = sizes[sizeI]
        fun setTool(t: Int) { tool = t; cur.clear(); invalidate() }
        fun cycleSize() { sizeI = (sizeI + 1) % sizes.size; (context as MapEditorActivity).refreshButtons() }
        fun cycleHouse() { house = (house + 1) % UserMap.MAX_HOUSES; (context as MapEditorActivity).refreshButtons(); invalidate() }

        private fun sx(x: Float) = x * scale + offX
        private fun sy(z: Float) = z * scale + offY
        private fun wx(x: Float) = (x - offX) / scale
        private fun wz(y: Float) = (y - offY) / scale

        private fun push() {
            undoStack.add(UserMap.toJson().toString())
            if (undoStack.size > 25) undoStack.removeAt(0)
        }

        fun undo() {
            if (cur.isNotEmpty()) { cur.clear(); invalidate(); return }
            if (undoStack.isEmpty()) { Toast.makeText(context, "Nada para desfazer", Toast.LENGTH_SHORT).show(); return }
            val s = undoStack.removeAt(undoStack.size - 1)
            try { UserMap.fromJson(JSONObject(s)) } catch (e: Throwable) { }
            bmpDirty = true; invalidate()
        }

        fun backPoint() { if (cur.isNotEmpty()) { cur.removeAt(cur.size - 1); invalidate() } }

        fun finishRoad() {
            if (cur.size < 2) { Toast.makeText(context, "Marque pelo menos 2 pontos", Toast.LENGTH_SHORT).show(); return }
            val kind = when (tool) { 1 -> UserMap.K_STREET; 2 -> UserMap.K_AVENUE; 3 -> UserMap.K_HIGHWAY; else -> UserMap.K_VIADUCT }
            push()
            UserMap.roads.add(UserMap.Road(kind, ArrayList(cur)))
            cur.clear(); invalidate()
        }

        private fun snapPoint(x: Float, z: Float): FloatArray {
            val rad = 16f / scale
            var bd = rad; var bx = x; var bz = z
            for (h in UserMap.hubs) { val d = hypot(x - h.x, z - h.z); if (d < h.r + rad && d < bd + h.r) { bd = 0f; bx = h.x; bz = h.z } }
            if (bd > 0f) {
                for (r in UserMap.roads) {
                    val sm = UserMap.smooth(r.pts)
                    for (q in 0 until sm.size - 1) {
                        val vx = sm[q + 1][0] - sm[q][0]; val vz = sm[q + 1][1] - sm[q][1]
                        val l2 = vx * vx + vz * vz
                        if (l2 < 1e-6f) continue
                        val t = (((x - sm[q][0]) * vx + (z - sm[q][1]) * vz) / l2).coerceIn(0f, 1f)
                        val px = sm[q][0] + vx * t; val pz = sm[q][1] + vz * t
                        val d = hypot(x - px, z - pz)
                        if (d < bd) { bd = d; bx = px; bz = pz }
                    }
                }
            }
            return floatArrayOf(bx.coerceIn(2f, UserMap.WX - 2f), bz.coerceIn(2f, UserMap.WZ - 2f))
        }

        private fun placeHouse(x: Float, z: Float) {
            val px = x.coerceIn(20f, UserMap.WX - 20f); val pz = z.coerceIn(20f, UserMap.WZ - 20f)
            val ex = UserMap.houses.firstOrNull { it.k == house }
            if (ex != null) { ex.x = px; ex.z = pz } else UserMap.houses.add(UserMap.Hs(house, px, pz))
        }

        private fun addTrees(x: Float, z: Float) {
            if (hypot(x - lastTreeX, z - lastTreeZ) < 5f) return
            lastTreeX = x; lastTreeZ = z
            val n = if (sizeM() > 20f) 3 else 1
            for (i in 0 until n) {
                val px = x + (rnd.nextFloat() - 0.5f) * sizeM() * 0.9f; val pz = z + (rnd.nextFloat() - 0.5f) * sizeM() * 0.9f
                val sp = when (rnd.nextInt(10)) { 0, 1 -> 2; 2, 3, 4 -> 1; 5 -> 3; else -> 0 }
                UserMap.trees.add(UserMap.Tree(px, pz, sp, 1.0f + rnd.nextFloat() * 0.8f, rnd.nextFloat() * 6.28f, 0.9f + rnd.nextFloat() * 0.2f))
            }
        }

        private fun eraseTrees(x: Float, z: Float) {
            val r = sizeM()
            UserMap.trees.removeAll { hypot(it.x - x, it.z - z) < r }
        }

        private fun eraseTap(x: Float, z: Float) {
            val rad = 14f / scale + 3f
            for (h in UserMap.houses) if (h.k != 0 && x > h.x - 10f && x < h.x + 8f && z > h.z - 11f && z < h.z + 11f) { UserMap.houses.remove(h); return }
            for (h in UserMap.hubs) if (hypot(x - h.x, z - h.z) < h.r + 2f) { UserMap.hubs.remove(h); return }
            var best: UserMap.Road? = null; var bd = rad
            for (r in UserMap.roads) {
                val sm = UserMap.smooth(r.pts)
                for (q in 0 until sm.size - 1) {
                    val vx = sm[q + 1][0] - sm[q][0]; val vz = sm[q + 1][1] - sm[q][1]
                    val l2 = vx * vx + vz * vz
                    if (l2 < 1e-6f) continue
                    val t = (((x - sm[q][0]) * vx + (z - sm[q][1]) * vz) / l2).coerceIn(0f, 1f)
                    val d = hypot(x - (sm[q][0] + vx * t), z - (sm[q][1] + vz * t))
                    if (d < bd) { bd = d; best = r }
                }
            }
            if (best != null) UserMap.roads.remove(best)
        }

        private fun brushAt(x: Float, z: Float, force: Boolean) {
            if (!force && hypot(x - lastBrushX, z - lastBrushZ) < sizeM() * 0.3f) return
            lastBrushX = x; lastBrushZ = z
            val mode = when (tool) { 8 -> 0; 9 -> 1; 10 -> 2; else -> 3 }
            UserMap.brush(x, z, sizeM(), mode)
            bmpDirty = true
        }

        override fun onTouchEvent(e: MotionEvent): Boolean {
            scaler.onTouchEvent(e)
            val a = e.actionMasked
            if (e.pointerCount >= 2) {
                val mx = (e.getX(0) + e.getX(1)) / 2f; val my = (e.getY(0) + e.getY(1)) / 2f
                if (!multi) { multi = true; cx0 = mx; cy0 = my } else { offX += mx - cx0; offY += my - cy0; cx0 = mx; cy0 = my; invalidate() }
                return true
            }
            if (multi) { if (a == MotionEvent.ACTION_UP || a == MotionEvent.ACTION_CANCEL) multi = false; if (a == MotionEvent.ACTION_POINTER_UP) { lastX = e.x; lastY = e.y }; if (a != MotionEvent.ACTION_DOWN) return true }
            val x = e.x; val y = e.y
            val X = wx(x); val Z = wz(y)
            when (a) {
                MotionEvent.ACTION_DOWN -> {
                    multi = false; moved = false; downX = x; downY = y; downT = System.currentTimeMillis(); lastX = x; lastY = y
                    lastBrushX = -1e9f; lastTreeX = -1e9f
                    when (tool) {
                        6 -> { push(); placeHouse(X, Z) }
                        7 -> { push(); addTrees(X, Z) }
                        8, 9, 10, 11 -> { push(); brushAt(X, Z, true) }
                        12 -> { push(); eraseTrees(X, Z) }
                    }
                    invalidate()
                }
                MotionEvent.ACTION_MOVE -> {
                    if (hypot(x - downX, y - downY) > 14f) moved = true
                    when (tool) {
                        0, 1, 2, 3, 4, 5 -> if (tool == 0 || moved) { if (tool == 0) { offX += x - lastX; offY += y - lastY } }
                        6 -> placeHouse(X, Z)
                        7 -> addTrees(X, Z)
                        8, 9, 10, 11 -> brushAt(X, Z, false)
                        12 -> eraseTrees(X, Z)
                    }
                    lastX = x; lastY = y
                    invalidate()
                }
                MotionEvent.ACTION_UP -> {
                    val tap = !moved && System.currentTimeMillis() - downT < 600
                    if (tap) when (tool) {
                        1, 2, 3, 4 -> { cur.add(snapPoint(X, Z)) }
                        5 -> { push(); UserMap.hubs.add(UserMap.Hub(X.coerceIn(30f, UserMap.WX - 30f), Z.coerceIn(30f, UserMap.WZ - 30f), sizeM())) }
                        12 -> eraseTap(X, Z)
                    }
                    if (tool == 12 && tap) { /* já tratado */ }
                    invalidate()
                }
            }
            return true
        }

        private fun heightColor(h: Float): Int {
            if (h < -0.15f) { val d = ((-0.2f - h) / 3f).coerceIn(0f, 1f); return mix(Color.rgb(110, 195, 225), Color.rgb(27, 95, 166), d) }
            if (h < 1.3f) return Color.rgb(230, 214, 164)
            if (h > 12f) return mix(Color.rgb(130, 185, 110), Color.rgb(168, 156, 132), ((h - 12f) / 18f).coerceIn(0f, 1f))
            return mix(Color.rgb(166, 212, 138), Color.rgb(125, 184, 106), ((h - 1.3f) / 10f).coerceIn(0f, 1f))
        }

        private fun mix(a: Int, b: Int, t: Float): Int =
            Color.rgb((Color.red(a) + (Color.red(b) - Color.red(a)) * t).toInt(), (Color.green(a) + (Color.green(b) - Color.green(a)) * t).toInt(), (Color.blue(a) + (Color.blue(b) - Color.blue(a)) * t).toInt())

        private fun rebuildBmp() {
            val b = bmp ?: Bitmap.createBitmap(UserMap.NX, UserMap.NZ, Bitmap.Config.ARGB_8888).also { bmp = it }
            val px = IntArray(UserMap.NX * UserMap.NZ)
            for (i in px.indices) px[i] = heightColor(UserMap.hs[i] / 100f)
            b.setPixels(px, 0, UserMap.NX, 0, 0, UserMap.NX, UserMap.NZ)
            bmpDirty = false
        }

        override fun onDraw(c: Canvas) {
            if (!inited && width > 0) {
                scale = min(width / UserMap.WX, height / UserMap.WZ) * 0.95f
                offX = (width - UserMap.WX * scale) / 2f; offY = (height - UserMap.WZ * scale) / 2f; inited = true
                (context as MapEditorActivity).refreshButtons()
            }
            c.drawColor(Color.rgb(32, 40, 52))
            if (bmpDirty || bmp == null) rebuildBmp()
            paint.isFilterBitmap = true
            val g = UserMap.G
            c.drawBitmap(bmp!!, null, RectF(sx(-g / 2), sy(-g / 2), sx(UserMap.WX + g / 2), sy(UserMap.WZ + g / 2)), paint)
            // grade de 100 m
            paint.style = Paint.Style.STROKE; paint.strokeWidth = 1f; paint.color = Color.argb(60, 255, 255, 255)
            var gx = 0f
            while (gx <= UserMap.WX) { c.drawLine(sx(gx), sy(0f), sx(gx), sy(UserMap.WZ), paint); gx += 100f }
            var gz = 0f
            while (gz <= UserMap.WZ) { c.drawLine(sx(0f), sy(gz), sx(UserMap.WX), sy(gz), paint); gz += 100f }
            // árvores
            paint.style = Paint.Style.FILL
            val tr = max(1.6f, 2.6f * scale)
            for (t in UserMap.trees) {
                paint.color = when (t.sp) { 2 -> Color.rgb(231, 169, 190); 3 -> Color.rgb(47, 122, 74); else -> Color.rgb(79, 154, 85) }
                c.drawCircle(sx(t.x), sy(t.z), tr, paint)
            }
            // ruas
            paint.strokeCap = Paint.Cap.ROUND; paint.strokeJoin = Paint.Join.ROUND
            for (r in UserMap.roads) drawRoad(c, r.pts, r.kind, false)
            if (cur.isNotEmpty()) {
                drawRoad(c, cur, when (tool) { 1 -> 0; 2 -> 1; 3 -> 2; else -> 3 }, true)
                paint.style = Paint.Style.FILL; paint.color = Color.rgb(255, 140, 60)
                for (p in cur) c.drawCircle(sx(p[0]), sy(p[1]), 5f, paint)
            }
            // rotatórias
            for (h in UserMap.hubs) {
                paint.style = Paint.Style.FILL; paint.color = Color.rgb(95, 99, 104); c.drawCircle(sx(h.x), sy(h.z), h.r * scale, paint)
                paint.color = Color.rgb(120, 180, 100); c.drawCircle(sx(h.x), sy(h.z), h.r * 0.45f * scale, paint)
            }
            // casas
            for (h in UserMap.houses) {
                paint.style = Paint.Style.FILL; paint.color = if (h.k == 0) Color.rgb(255, 112, 67) else Color.rgb(240, 180, 80)
                c.drawRect(sx(h.x - 9f), sy(h.z - 10f), sx(h.x + 7f), sy(h.z + 10f), paint)
                paint.color = Color.WHITE
                val tp = Path(); tp.moveTo(sx(h.x - 1f), sy(h.z - 10f) - 10f); tp.lineTo(sx(h.x - 4f), sy(h.z - 10f)); tp.lineTo(sx(h.x + 2f), sy(h.z - 10f)); tp.close()
                c.drawPath(tp, paint)
                paint.textSize = max(22f, 12f * scale); paint.textAlign = Paint.Align.CENTER; paint.color = Color.BLACK
                c.drawText((h.k + 1).toString(), sx(h.x - 1f), sy(h.z) + 8f, paint)
            }
            paint.textAlign = Paint.Align.LEFT
        }

        private fun drawRoad(c: Canvas, pts: List<FloatArray>, kind: Int, preview: Boolean) {
            if (pts.size < 2) return
            val sm = UserMap.smooth(pts)
            val p = Path()
            p.moveTo(sx(sm[0][0]), sy(sm[0][1]))
            for (q in 1 until sm.size) p.lineTo(sx(sm[q][0]), sy(sm[q][1]))
            paint.style = Paint.Style.STROKE
            paint.strokeWidth = max(3f, UserMap.kindWidth(kind) * scale)
            paint.color = when (kind) { 0 -> Color.rgb(125, 125, 130); 1 -> Color.rgb(96, 99, 104); 2 -> Color.rgb(60, 64, 70); else -> Color.rgb(150, 120, 220) }
            if (preview) paint.alpha = 170
            c.drawPath(p, paint)
            paint.alpha = 255
            if (kind == 3) { paint.strokeWidth = 2f; paint.color = Color.WHITE; c.drawPath(p, paint) }
        }
    }
}
