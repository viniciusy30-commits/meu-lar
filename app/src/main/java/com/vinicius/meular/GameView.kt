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
    val joyR = 46f * ctx.resources.displayMetrics.density

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
    private var dragDx = 0f
    private var dragDz = 0f

    var mode: Int
        get() = r.mode
        set(v) {
            if (v == r.mode) return
            if (v == 0 && r.mode == 1) r.faceCameraBehindPlayer()   // Etapa 34: volta com a câmera atrás do personagem
            if (v == 1) r.stopWalk()
            if (v != 0) {
                r.grabbed = null
                r.aimed = null
                clearFp()
            }
            if (v != 1) r.selected = null
            if (v == 2) r.autoSpin = true
            r.mode = v
        }

    /** true = 3ª pessoa, false = 1ª pessoa (olho do personagem); só vale na câmera de perto. */
    var third: Boolean
        get() = r.third
        set(v) { r.third = v }

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
                        r.fpitch = (r.fpitch - (y - ly) * sens).coerceIn(-1.45f, 1.3f)
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

    private fun floorXZ(px: Float, py: Float): FloatArray? {
        val ry = r.ray(px, py, width, height) ?: return null
        return r.floorPoint(ry)
    }

    private fun pick(px: Float, py: Float): Item? {
        val ry = r.ray(px, py, width, height) ?: return null
        return r.pickRay(ry)
    }

    private fun dist(e: MotionEvent): Float = hypot(e.getX(0) - e.getX(1), e.getY(0) - e.getY(1))

    /** Etapa 126: vista de cima na rua: analógico no canto esquerdo; o resto da tela continua girando/tocando para andar. */
    private fun aerialCityTouch(e: MotionEvent): Boolean {
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN, MotionEvent.ACTION_POINTER_DOWN -> {
                val i = e.actionIndex
                val x = e.getX(i); val y = e.getY(i)
                if (joyId == -1 && amode == 0 && x < width * 0.45f && y > height * 0.35f) {
                    joyId = e.getPointerId(i); joyBx = x; joyBy = y; joyKx = x; joyKy = y; joyActive = true
                    r.stopWalk()
                    return true
                }
            }
            MotionEvent.ACTION_MOVE -> if (joyId != -1) {
                val i = e.findPointerIndex(joyId)
                if (i >= 0) {
                    var dx = e.getX(i) - joyBx; var dy = e.getY(i) - joyBy
                    val d = hypot(dx, dy)
                    if (d > joyR) { dx = dx / d * joyR; dy = dy / d * joyR }
                    joyKx = joyBx + dx; joyKy = joyBy + dy
                    if (d < 8f) { r.moveX = 0f; r.moveY = 0f } else { r.moveX = dx / joyR; r.moveY = -dy / joyR }
                }
                return true
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_POINTER_UP -> if (e.getPointerId(e.actionIndex) == joyId) {
                joyId = -1; joyActive = false; r.moveX = 0f; r.moveY = 0f
                return true
            }
            MotionEvent.ACTION_CANCEL -> clearFp()
        }
        if (joyId != -1) return true
        return aerialTouch(e)
    }

    private fun aerialTouch(e: MotionEvent): Boolean {
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                ax = e.x; ay = e.y; amoved = false
                val h = pick(e.x, e.y)
                if (h != null) {
                    selected = h
                    amode = 2
                    val c = floorXZ(e.x, e.y)
                    dragDx = if (c != null) c[0] - (h.x + h.ox) else 0f
                    dragDz = if (c != null) c[1] - (h.y + h.oz) else 0f
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
                    val c = floorXZ(e.x, e.y)
                    if (s != null && c != null) {
                        val p = st.placeAt(s, s.rot, snapQ(c[0] - dragDx), snapQ(c[1] - dragDz))
                        if (p != null) { s.x = p[0].toInt(); s.y = p[1].toInt(); s.ox = p[2]; s.oz = p[3] }
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
                if (amode == 1 && !amoved) {
                    selected = null
                    // Etapa 34: toque no chão = o personagem anda até lá (como no The Sims)
                    if (e.actionMasked == MotionEvent.ACTION_UP) {
                        val ry = r.ray(e.x, e.y, width, height)
                        val fp = if (ry != null) r.floorPoint(ry) else null
                        if (fp != null) r.walkTo(fp[0], fp[1])
                    }
                }
                if (amode == 2) onChanged?.invoke()
                amode = 0
            }
        }
        return true
    }

    // ------------------------------------------------------------ criador de personagem

    private var cay = 0f
    private var cmx = 0f
    private var cmy = 0f

    private fun creatorTouch(e: MotionEvent): Boolean {
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                ax = e.x; cay = e.y; amode = 1
                r.autoSpin = false; r.cTargetYaw = Float.NaN; r.cTargetPitch = Float.NaN
            }
            MotionEvent.ACTION_POINTER_DOWN -> {
                if (e.pointerCount >= 2) {
                    amode = 3; pinchD = dist(e)
                    cmx = (e.getX(0) + e.getX(1)) / 2f; cmy = (e.getY(0) + e.getY(1)) / 2f
                }
            }
            MotionEvent.ACTION_MOVE -> {
                if (amode == 1) {
                    // 1 dedo: gira em volta do personagem e inclina a câmera para cima/baixo
                    r.cyaw = r.cyaw - (e.x - ax) * 0.011f
                    r.cPitch = (r.cPitch + (e.y - cay) * 0.004f).coerceIn(-0.25f, 0.75f)
                    ax = e.x; cay = e.y
                } else if (amode == 3 && e.pointerCount >= 2) {
                    // 2 dedos: pinça = zoom; arrastar = move a câmera (o personagem anda pela tela)
                    val d = dist(e)
                    if (pinchD > 0f && d > 0f) r.cTargetDist = (r.cTargetDist * pinchD / d).coerceIn(0.9f, 6.0f)
                    pinchD = d
                    val mx = (e.getX(0) + e.getX(1)) / 2f
                    val my = (e.getY(0) + e.getY(1)) / 2f
                    if (width > 0 && height > 0) {
                        r.cPanX = (r.cPanX + (mx - cmx) * 2f / width).coerceIn(-1.2f, 1.2f)
                        r.cPanY = (r.cPanY - (my - cmy) * 2f / height).coerceIn(-1.0f, 1.0f)
                    }
                    cmx = mx; cmy = my
                }
            }
            MotionEvent.ACTION_POINTER_UP -> {
                if (amode == 3) {
                    val idx = if (e.actionIndex == 0) 1 else 0
                    if (idx < e.pointerCount) { ax = e.getX(idx); cay = e.getY(idx) }
                    amode = 1
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> amode = 0
        }
        return true
    }

    override fun onTouchEvent(e: MotionEvent): Boolean = when (r.mode) {
        0 -> fpTouch(e)
        1 -> if (r.streetAerial) aerialCityTouch(e) else aerialTouch(e)
        else -> creatorTouch(e)
    }
}
