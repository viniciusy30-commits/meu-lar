package com.vinicius.meular

import android.content.Context
import android.opengl.GLSurfaceView
import android.view.MotionEvent
import kotlin.math.abs
import kotlin.math.floor
import kotlin.math.hypot

class GameView(ctx: Context, private val st: GameState) : GLSurfaceView(ctx) {
    val r = Renderer3D(st)
    var onFocus: ((Item?, Boolean) -> Unit)? = null
    var onChanged: (() -> Unit)? = null

    // joystick virtual (primeira pessoa)
    @Volatile var joyActive = false
    @Volatile var joyBx = 0f
    @Volatile var joyBy = 0f
    @Volatile var joyKx = 0f
    @Volatile var joyKy = 0f
    val joyR = 58f * ctx.resources.displayMetrics.density

    private var joyId = -1
    private var lookId = -1
    private var lx = 0f
    private var ly = 0f

    // vista aérea
    private var amode = 0
    private var ax = 0f
    private var ay = 0f
    private var amoved = false
    private var pinchD = 0f
    private var dragDx = 0
    private var dragDz = 0

    var mode: Int
        get() = r.mode
        set(v) {
            if (v == r.mode) return
            if (v != 0) {
                r.grabbed = null
                r.aimed = null
                clearFp()
            }
            if (v != 1) r.selected = null
            if (v == 2) r.autoSpin = true
            r.mode = v
        }

    var selected: Item?
        get() = r.selected
        set(v) { r.selected = v }

    init {
        Tex.pregen()
        setEGLContextClientVersion(2)
        setEGLConfigChooser(MsaaChooser())
        setRenderer(r)
        renderMode = RENDERMODE_CONTINUOUSLY
        r.onFocus = { f, g -> post { onFocus?.invoke(f, g) } }
    }

    /** Ponto no chão (x, z) a uns passos à frente do jogador, ou o centro da casa na vista aérea. */
    fun frontTarget(): FloatArray =
        if (r.mode == 0) floatArrayOf(r.eyeX + r.fwdX * 2.4f, r.eyeZ + r.fwdZ * 2.4f)
        else floatArrayOf(st.gw / 2f, st.gh / 2f)

    private fun clearFp() {
        joyId = -1; lookId = -1; joyActive = false
        r.moveX = 0f; r.moveY = 0f
    }

    override fun onPause() {
        clearFp()
        super.onPause()
    }

    // ------------------------------------------------------------ primeira pessoa

    private fun fpTouch(e: MotionEvent): Boolean {
        val sens = 0.0052f * floatArrayOf(0.65f, 1f, 1.6f)[st.sens]
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN, MotionEvent.ACTION_POINTER_DOWN -> {
                val i = e.actionIndex
                val id = e.getPointerId(i)
                val x = e.getX(i)
                val y = e.getY(i)
                if (joyId == -1 && x < width * 0.45f && y > height * 0.35f) {
                    joyId = id; joyBx = x; joyBy = y; joyKx = x; joyKy = y; joyActive = true
                } else if (lookId == -1) {
                    lookId = id; lx = x; ly = y
                }
            }
            MotionEvent.ACTION_MOVE -> {
                for (i in 0 until e.pointerCount) {
                    val id = e.getPointerId(i)
                    val x = e.getX(i)
                    val y = e.getY(i)
                    if (id == joyId) {
                        var dx = x - joyBx
                        var dy = y - joyBy
                        val d = hypot(dx, dy)
                        if (d > joyR) { dx = dx / d * joyR; dy = dy / d * joyR }
                        joyKx = joyBx + dx; joyKy = joyBy + dy
                        if (d < 8f) { r.moveX = 0f; r.moveY = 0f }
                        else { r.moveX = dx / joyR; r.moveY = -dy / joyR }
                    } else if (id == lookId) {
                        r.fyaw = r.fyaw + (x - lx) * sens
                        r.fpitch = (r.fpitch - (y - ly) * sens).coerceIn(-1.3f, 1.3f)
                        lx = x; ly = y
                    }
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_POINTER_UP -> {
                val id = e.getPointerId(e.actionIndex)
                if (id == joyId) { joyId = -1; joyActive = false; r.moveX = 0f; r.moveY = 0f }
                if (id == lookId) lookId = -1
            }
            MotionEvent.ACTION_CANCEL -> clearFp()
        }
        return true
    }

    // ------------------------------------------------------------ vista aérea

    private fun floorCell(px: Float, py: Float): Pair<Int, Int>? {
        val ry = r.ray(px, py, width, height) ?: return null
        val fp = r.floorPoint(ry) ?: return null
        return Pair(floor(fp[0]).toInt(), floor(fp[1]).toInt())
    }

    private fun pick(px: Float, py: Float): Item? {
        val ry = r.ray(px, py, width, height) ?: return null
        return r.pickRay(ry)
    }

    private fun dist(e: MotionEvent): Float = hypot(e.getX(0) - e.getX(1), e.getY(0) - e.getY(1))

    private fun aerialTouch(e: MotionEvent): Boolean {
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                ax = e.x; ay = e.y; amoved = false
                val h = pick(e.x, e.y)
                if (h != null) {
                    selected = h
                    amode = 2
                    val c = floorCell(e.x, e.y)
                    dragDx = (c?.first ?: h.x) - h.x
                    dragDz = (c?.second ?: h.y) - h.y
                } else amode = 1
            }
            MotionEvent.ACTION_POINTER_DOWN -> {
                if (e.pointerCount >= 2) { amode = 3; pinchD = dist(e) }
            }
            MotionEvent.ACTION_MOVE -> {
                if (amode == 1) {
                    val dx = e.x - ax
                    val dy = e.y - ay
                    if (abs(dx) + abs(dy) > 6f) amoved = true
                    r.yaw = r.yaw - dx * 0.008f
                    r.pitch = (r.pitch + dy * 0.006f).coerceIn(0.4f, 1.35f)
                    ax = e.x; ay = e.y
                } else if (amode == 2) {
                    val s = selected
                    val c = floorCell(e.x, e.y)
                    if (s != null && c != null) {
                        val nx = (c.first - dragDx).coerceIn(0, maxOf(0, st.gw - s.w))
                        val nz = (c.second - dragDz).coerceIn(0, maxOf(0, st.gh - s.h))
                        if ((nx != s.x || nz != s.y) && st.canPlace(s, nx, nz, s.rot)) { s.x = nx; s.y = nz }
                    }
                } else if (amode == 3 && e.pointerCount >= 2) {
                    val d = dist(e)
                    if (pinchD > 0f && d > 0f) r.zoom = (r.zoom * pinchD / d).coerceIn(0.5f, 1.7f)
                    pinchD = d
                }
            }
            MotionEvent.ACTION_POINTER_UP -> {
                if (amode == 3) {
                    val idx = if (e.actionIndex == 0) 1 else 0
                    if (idx < e.pointerCount) { ax = e.getX(idx); ay = e.getY(idx) }
                    amode = 1
                    amoved = true
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                if (amode == 1 && !amoved) selected = null
                if (amode == 2) onChanged?.invoke()
                amode = 0
            }
        }
        return true
    }

    // ------------------------------------------------------------ criador de personagem

    private fun creatorTouch(e: MotionEvent): Boolean {
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> { ax = e.x; amode = 1; r.autoSpin = false }
            MotionEvent.ACTION_POINTER_DOWN -> {
                if (e.pointerCount >= 2) { amode = 3; pinchD = dist(e) }
            }
            MotionEvent.ACTION_MOVE -> {
                if (amode == 1) {
                    r.cyaw = r.cyaw - (e.x - ax) * 0.011f
                    ax = e.x
                } else if (amode == 3 && e.pointerCount >= 2) {
                    val d = dist(e)
                    if (pinchD > 0f && d > 0f) r.cTargetDist = (r.cTargetDist * pinchD / d).coerceIn(1.6f, 6.0f)
                    pinchD = d
                }
            }
            MotionEvent.ACTION_POINTER_UP -> {
                if (amode == 3) {
                    val idx = if (e.actionIndex == 0) 1 else 0
                    if (idx < e.pointerCount) ax = e.getX(idx)
                    amode = 1
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> amode = 0
        }
        return true
    }

    override fun onTouchEvent(e: MotionEvent): Boolean = when (r.mode) {
        0 -> fpTouch(e)
        1 -> aerialTouch(e)
        else -> creatorTouch(e)
    }
}
