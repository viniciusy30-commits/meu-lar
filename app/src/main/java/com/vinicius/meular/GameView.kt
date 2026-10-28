package com.vinicius.meular

import android.content.Context
import android.opengl.GLSurfaceView
import android.view.MotionEvent
import kotlin.math.abs
import kotlin.math.floor
import kotlin.math.hypot

class GameView(ctx: Context, private val st: GameState) : GLSurfaceView(ctx) {
    var onSelect: ((Item?) -> Unit)? = null
    var onChanged: (() -> Unit)? = null
    private val r = Renderer3D(st)

    var selected: Item? = null
        set(v) { field = v; r.selected = v; onSelect?.invoke(v) }

    private var mode = 0
    private var lx = 0f
    private var ly = 0f
    private var moved = false
    private var pinchD = 0f
    private var dragDx = 0
    private var dragDz = 0

    init {
        setEGLContextClientVersion(2)
        setEGLConfigChooser(MsaaChooser())
        setRenderer(r)
        renderMode = RENDERMODE_CONTINUOUSLY
    }

    private fun floorCell(px: Float, py: Float): Pair<Int, Int>? {
        val ry = r.ray(px, py, width, height) ?: return null
        if (abs(ry[4]) < 1e-6f) return null
        val t = -ry[1] / ry[4]
        if (t < 0f) return null
        return Pair(floor(ry[0] + t * ry[3]).toInt(), floor(ry[2] + t * ry[5]).toInt())
    }

    private fun hitBox(ry: FloatArray, x0: Float, y0: Float, z0: Float, x1: Float, y1: Float, z1: Float): Float {
        var tmin = 0f
        var tmax = 1e9f
        val mn = floatArrayOf(x0, y0, z0)
        val mx = floatArrayOf(x1, y1, z1)
        for (i in 0..2) {
            val o = ry[i]
            val d = ry[3 + i]
            if (abs(d) < 1e-6f) {
                if (o < mn[i] || o > mx[i]) return -1f
            } else {
                var t1 = (mn[i] - o) / d
                var t2 = (mx[i] - o) / d
                if (t1 > t2) { val s = t1; t1 = t2; t2 = s }
                if (t1 > tmin) tmin = t1
                if (t2 < tmax) tmax = t2
                if (tmin > tmax) return -1f
            }
        }
        return tmin
    }

    private fun pick(px: Float, py: Float): Item? {
        val ry = r.ray(px, py, width, height) ?: return null
        var best: Item? = null
        var bt = 1e9f
        for (o in st.items) {
            if (o.type == Type.RUG) continue
            val t = hitBox(ry, o.x.toFloat(), 0f, o.y.toFloat(), (o.x + o.w).toFloat(), o.type.alt, (o.y + o.h).toFloat())
            if (t >= 0f && t < bt) { bt = t; best = o }
        }
        if (best != null) return best
        val c = floorCell(px, py) ?: return null
        return st.items.lastOrNull { o ->
            o.type == Type.RUG && c.first >= o.x && c.first < o.x + o.w && c.second >= o.y && c.second < o.y + o.h
        }
    }

    private fun dist(e: MotionEvent): Float = hypot(e.getX(0) - e.getX(1), e.getY(0) - e.getY(1))

    override fun onTouchEvent(e: MotionEvent): Boolean {
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                lx = e.x; ly = e.y; moved = false
                val h = pick(e.x, e.y)
                if (h != null) {
                    selected = h
                    mode = 2
                    val c = floorCell(e.x, e.y)
                    dragDx = (c?.first ?: h.x) - h.x
                    dragDz = (c?.second ?: h.y) - h.y
                } else mode = 1
            }
            MotionEvent.ACTION_POINTER_DOWN -> {
                if (e.pointerCount >= 2) { mode = 3; pinchD = dist(e) }
            }
            MotionEvent.ACTION_MOVE -> {
                if (mode == 1) {
                    val dx = e.x - lx
                    val dy = e.y - ly
                    if (abs(dx) + abs(dy) > 6f) moved = true
                    r.yaw = r.yaw - dx * 0.008f
                    r.pitch = (r.pitch + dy * 0.006f).coerceIn(0.4f, 1.35f)
                    lx = e.x; ly = e.y
                } else if (mode == 2) {
                    val s = selected
                    val c = floorCell(e.x, e.y)
                    if (s != null && c != null) {
                        val nx = (c.first - dragDx).coerceIn(0, maxOf(0, st.gw - s.w))
                        val nz = (c.second - dragDz).coerceIn(0, maxOf(0, st.gh - s.h))
                        if ((nx != s.x || nz != s.y) && st.canPlace(s, nx, nz, s.rot)) { s.x = nx; s.y = nz }
                    }
                } else if (mode == 3 && e.pointerCount >= 2) {
                    val d = dist(e)
                    if (pinchD > 0f && d > 0f) r.zoom = (r.zoom * pinchD / d).coerceIn(0.5f, 1.7f)
                    pinchD = d
                }
            }
            MotionEvent.ACTION_POINTER_UP -> {
                if (mode == 3) {
                    val idx = if (e.actionIndex == 0) 1 else 0
                    if (idx < e.pointerCount) { lx = e.getX(idx); ly = e.getY(idx) }
                    mode = 1
                    moved = true
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                if (mode == 1 && !moved) selected = null
                if (mode == 2) onChanged?.invoke()
                mode = 0
            }
        }
        return true
    }
}
