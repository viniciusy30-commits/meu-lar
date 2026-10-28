package com.vinicius.meular

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.view.MotionEvent
import android.view.View

class GameView(ctx: Context, private val st: GameState) : View(ctx) {
    var onSelect: ((Item?) -> Unit)? = null
    var onChanged: (() -> Unit)? = null
    var selected: Item? = null
        set(v) { field = v; onSelect?.invoke(v); invalidate() }

    private var cell = 1f
    private var ox = 0f
    private var oy = 0f
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private var dragDx = 0
    private var dragDy = 0
    private var dragging = false

    private fun fill(c: String) { p.style = Paint.Style.FILL; p.color = Color.parseColor(c) }

    private fun rr(c: Canvas, r: RectF, rad: Float) = c.drawRoundRect(r, rad, rad, p)

    override fun onDraw(c: Canvas) {
        cell = minOf(width / (st.gw + 1f), height / (st.gh + 1f))
        ox = (width - cell * st.gw) / 2f
        oy = (height - cell * st.gh) / 2f
        c.drawColor(Color.parseColor("#2B2D42"))
        fill("#8D6E63")
        c.drawRoundRect(ox - cell * .25f, oy - cell * .25f, ox + cell * st.gw + cell * .25f,
            oy + cell * st.gh + cell * .25f, cell * .2f, cell * .2f, p)
        for (y in 0 until st.gh) for (x in 0 until st.gw) {
            fill(if ((x + y) % 2 == 0) "#E8C9A0" else "#DDB98A")
            c.drawRect(ox + x * cell, oy + y * cell, ox + (x + 1) * cell, oy + (y + 1) * cell, p)
        }
        for (item in st.items.sortedBy { if (it.type == Type.RUG) 0 else 1 }) drawItem(c, item)
    }

    private fun drawItem(c: Canvas, i: Item) {
        val g = cell * .07f
        val r = RectF(ox + i.x * cell + g, oy + i.y * cell + g, ox + (i.x + i.w) * cell - g, oy + (i.y + i.h) * cell - g)
        val rad = cell * .14f
        val w = r.width()
        val h = r.height()
        if (i.type != Type.RUG) {
            fill("#33000000")
            rr(c, RectF(r.left + 3, r.top + 6, r.right + 3, r.bottom + 6), rad)
        }
        when (i.type) {
            Type.CHAIR -> {
                fill("#A1887F"); rr(c, r, rad)
                fill("#6D4C41"); rr(c, RectF(r.left, r.top, r.right, r.top + h * .3f), rad)
            }
            Type.TABLE -> {
                fill("#8D6E63"); rr(c, r, rad)
                fill("#A98274"); rr(c, RectF(r.left + w * .06f, r.top + h * .12f, r.right - w * .06f, r.bottom - h * .12f), rad)
            }
            Type.BED -> {
                fill("#5C6BC0"); rr(c, r, rad)
                fill("#7986CB"); rr(c, RectF(r.left + w * .08f, r.top + h * .3f, r.right - w * .08f, r.bottom - h * .06f), rad)
                fill("#FFFFFF")
                if (w >= h) rr(c, RectF(r.left + w * .06f, r.top + h * .12f, r.left + w * .3f, r.bottom - h * .12f), rad)
                else rr(c, RectF(r.left + w * .12f, r.top + h * .05f, r.right - w * .12f, r.top + h * .25f), rad)
            }
            Type.SOFA -> {
                fill("#26A69A"); rr(c, r, rad)
                fill("#4DB6AC"); rr(c, RectF(r.left + w * .06f, r.top + h * .3f, r.right - w * .06f, r.bottom - h * .08f), rad)
                fill("#00897B"); rr(c, RectF(r.left, r.top, r.right, r.top + h * .28f), rad)
            }
            Type.SHELF -> {
                fill("#5D4037"); rr(c, r, rad)
                val cores = listOf("#EF5350", "#FFCA28", "#66BB6A", "#42A5F5", "#AB47BC")
                var k = 0
                var x = r.left + w * .08f
                while (x < r.right - w * .12f) {
                    fill(cores[k % cores.size]); k++
                    c.drawRect(x, r.top + h * .2f, x + w * .07f, r.bottom - h * .2f, p)
                    x += w * .1f
                }
            }
            Type.PLANT -> {
                fill("#43A047")
                c.drawCircle(r.centerX(), r.centerY() - h * .1f, w * .38f, p)
                fill("#66BB6A"); c.drawCircle(r.centerX() - w * .12f, r.centerY() - h * .18f, w * .2f, p)
                fill("#D2691E"); rr(c, RectF(r.centerX() - w * .22f, r.bottom - h * .3f, r.centerX() + w * .22f, r.bottom - h * .04f), rad / 2)
            }
            Type.RUG -> {
                fill("#C62828"); rr(c, r, rad * 1.5f)
                fill("#EF9A9A"); rr(c, RectF(r.left + w * .1f, r.top + h * .1f, r.right - w * .1f, r.bottom - h * .1f), rad)
                fill("#C62828"); c.drawCircle(r.centerX(), r.centerY(), minOf(w, h) * .18f, p)
            }
            Type.TV -> {
                fill("#37474F"); rr(c, r, rad)
                fill("#4FC3F7"); rr(c, RectF(r.left + w * .1f, r.top + h * .12f, r.right - w * .1f, r.bottom - h * .3f), rad / 2)
            }
            Type.FRIDGE -> {
                fill("#ECEFF1"); rr(c, r, rad)
                fill("#B0BEC5"); c.drawRect(r.left, r.centerY() - 2, r.right, r.centerY() + 2, p)
                c.drawRect(r.right - w * .22f, r.top + h * .15f, r.right - w * .14f, r.top + h * .38f, p)
            }
            Type.STOVE -> {
                fill("#78909C"); rr(c, r, rad)
                fill("#263238")
                c.drawCircle(r.left + w * .3f, r.top + h * .3f, w * .12f, p)
                c.drawCircle(r.right - w * .3f, r.top + h * .3f, w * .12f, p)
                c.drawCircle(r.left + w * .3f, r.bottom - h * .3f, w * .12f, p)
                c.drawCircle(r.right - w * .3f, r.bottom - h * .3f, w * .12f, p)
            }
            Type.LAMP -> {
                fill("#FFF59D"); c.drawCircle(r.centerX(), r.centerY(), w * .38f, p)
                fill("#FBC02D"); c.drawCircle(r.centerX(), r.centerY(), w * .16f, p)
            }
        }
        if (i === selected) {
            p.style = Paint.Style.STROKE
            p.strokeWidth = cell * .08f
            p.color = Color.parseColor("#FFEB3B")
            c.drawRoundRect(RectF(r.left - g, r.top - g, r.right + g, r.bottom + g), rad, rad, p)
        }
    }

    private fun hit(gx: Int, gy: Int): Item? {
        fun inside(o: Item) = gx >= o.x && gx < o.x + o.w && gy >= o.y && gy < o.y + o.h
        return st.items.lastOrNull { it.type != Type.RUG && inside(it) }
            ?: st.items.lastOrNull { it.type == Type.RUG && inside(it) }
    }

    override fun onTouchEvent(e: MotionEvent): Boolean {
        val gx = Math.floor(((e.x - ox) / cell).toDouble()).toInt()
        val gy = Math.floor(((e.y - oy) / cell).toDouble()).toInt()
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                val h = hit(gx, gy)
                selected = h
                if (h != null) { dragDx = gx - h.x; dragDy = gy - h.y; dragging = true }
            }
            MotionEvent.ACTION_MOVE -> {
                val s = selected
                if (dragging && s != null) {
                    val nx = gx - dragDx
                    val ny = gy - dragDy
                    if ((nx != s.x || ny != s.y) && st.canPlace(s, nx, ny, s.rot)) {
                        s.x = nx; s.y = ny; invalidate()
                    }
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                if (dragging) { dragging = false; onChanged?.invoke() }
            }
        }
        return true
    }
}
