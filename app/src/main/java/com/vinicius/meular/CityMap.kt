package com.vinicius.meular

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.graphics.Shader
import android.graphics.Typeface
import android.view.Gravity
import android.view.MotionEvent
import android.view.ScaleGestureDetector
import android.view.View
import android.widget.FrameLayout
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.TextView
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Etapa 122: GPS. Rota pelas ruas (grade de cruzamentos), instrução da próxima conversão,
 * faixa azul no chão (desenhada pelo renderizador) e reroteamento quando o jogador sai do caminho.
 */
object Gps {
    @Volatile var active = false; private set
    @Volatile var ver = 0; private set
    @Volatile var route = FloatArray(0); private set          // x, z
    @Volatile var destX = 0f; private set
    @Volatile var destZ = 0f; private set
    @Volatile var destName = ""; private set
    // HUD
    @Volatile var turn = 0; private set          // -1 esquerda, 0 em frente, 1 direita, 2 chegou
    @Volatile var nextDist = 0f; private set
    @Volatile var remain = 0f; private set
    @Volatile var street = ""; private set
    @Volatile var arrivedAt = 0L; private set
    private var lastRoute = 0L
    private var lastPx = 0f; private var lastPz = 0f

    fun clear() { active = false; route = FloatArray(0); ver++; turn = 0 }

    fun setDest(x: Float, z: Float, name: String, px: Float, pz: Float) {
        destX = x; destZ = z; destName = name
        active = true; arrivedAt = 0L
        compute(px, pz)
    }

    private fun centers(b: FloatArray) = FloatArray(b.size / 2) { (b[it * 2] + b[it * 2 + 1]) / 2 }

    /** Ponto da rua mais perto: (eixo, índice da rua, x, z). eixo 0 = rua ao longo de x. */
    private fun snap(x: Float, z: Float): FloatArray {
        val zs = centers(City.bandZ); val xs = centers(City.bandX)
        var best = Float.MAX_VALUE; var r = floatArrayOf(0f, 0f, x, z)
        for ((k, zc) in zs.withIndex()) {
            val cx = x.coerceIn(xs.first(), xs.last())
            val d = abs(z - zc) + abs(x - cx)
            if (d < best) { best = d; r = floatArrayOf(0f, k.toFloat(), cx, zc) }
        }
        for ((k, xc) in xs.withIndex()) {
            val cz = z.coerceIn(zs.first(), zs.last())
            val d = abs(x - xc) + abs(z - cz)
            if (d < best) { best = d; r = floatArrayOf(1f, k.toFloat(), xc, cz) }
        }
        return r
    }

    /** Cruzamentos vizinhos de um ponto na rua (pares i, j). */
    private fun ends(s: FloatArray): List<IntArray> {
        val zs = centers(City.bandZ); val xs = centers(City.bandX)
        return if (s[0] == 0f) {
            val j = s[1].toInt()
            var i0 = 0; while (i0 < xs.size - 1 && xs[i0 + 1] <= s[2]) i0++
            val i1 = min(xs.size - 1, if (xs[i0] >= s[2]) i0 else i0 + 1)
            listOf(intArrayOf(i0, j), intArrayOf(i1, j))
        } else {
            val i = s[1].toInt()
            var j0 = 0; while (j0 < zs.size - 1 && zs[j0 + 1] <= s[3]) j0++
            val j1 = min(zs.size - 1, if (zs[j0] >= s[3]) j0 else j0 + 1)
            listOf(intArrayOf(i, j0), intArrayOf(i, j1))
        }
    }

    fun compute(px: Float, pz: Float) {
        if (!City.on) return
        if (City.bandX.isEmpty()) { route = floatArrayOf(px, pz, destX, destZ); ver++; lastPx = px; lastPz = pz; return }
        lastRoute = System.currentTimeMillis()
        val xs = centers(City.bandX); val zs = centers(City.bandZ)
        val s = snap(px, pz); val t = snap(destX, destZ)
        val pts = ArrayList<Float>()
        fun add(x: Float, z: Float) { if (pts.size >= 2 && abs(pts[pts.size - 2] - x) < 0.05f && abs(pts[pts.size - 1] - z) < 0.05f) return; pts.add(x); pts.add(z) }
        add(px, pz); add(s[2], s[3])
        val sameRoad = s[0] == t[0] && s[1] == t[1]
        if (!sameRoad) {
            var best = Float.MAX_VALUE; var bp: List<FloatArray> = emptyList()
            for (a in ends(s)) for (bb in ends(t)) {
                val ax = xs[a[0]]; val az = zs[a[1]]; val bx = xs[bb[0]]; val bz = zs[bb[1]]
                val c = abs(s[2] - ax) + abs(s[3] - az) + abs(ax - bx) + abs(az - bz) + abs(bx - t[2]) + abs(bz - t[3])
                if (c < best) {
                    best = c
                    // primeiro trecho continua no eixo da rua de partida (menos curvas)
                    val corner = if (s[0] == 0f) floatArrayOf(bx, az) else floatArrayOf(ax, bz)
                    bp = listOf(floatArrayOf(ax, az), corner, floatArrayOf(bx, bz))
                }
            }
            for (p in bp) add(p[0], p[1])
        }
        add(t[2], t[3]); add(destX, destZ)
        route = pts.toFloatArray()
        ver++
        lastPx = px; lastPz = pz
    }

    private fun roadName(x0: Float, z0: Float, x1: Float, z1: Float): String {
        val xs = centers(City.bandX); val zs = centers(City.bandZ)
        if (xs.isEmpty() || zs.isEmpty()) return ""
        if (abs(z1 - z0) < 0.5f) { val k = zs.indices.minByOrNull { abs(zs[it] - z0) } ?: 0; if (abs(zs[k] - z0) < 3f) return City.ROAD_NAMES_X[k] }
        if (abs(x1 - x0) < 0.5f) { val k = xs.indices.minByOrNull { abs(xs[it] - x0) } ?: 0; if (abs(xs[k] - x0) < 3f) return City.ROAD_NAMES_Z[k] }
        return ""
    }

    fun update(px: Float, pz: Float) {
        if (!active) return
        val r = route
        val n = r.size / 2
        if (n < 2) return
        // ponto mais perto da rota
        var bi = 0; var bd = Float.MAX_VALUE; var bt = 0f
        for (i in 0 until n - 1) {
            val ax = r[i * 2]; val az = r[i * 2 + 1]; val ex = r[i * 2 + 2]; val ez = r[i * 2 + 3]
            val dx = ex - ax; val dz = ez - az; val l2 = dx * dx + dz * dz
            val tt = if (l2 < 1e-4f) 0f else (((px - ax) * dx + (pz - az) * dz) / l2).coerceIn(0f, 1f)
            val qx = ax + dx * tt; val qz = az + dz * tt
            val d = hypot(px - qx, pz - qz)
            if (d < bd) { bd = d; bi = i; bt = tt }
        }
        val now = System.currentTimeMillis()
        val dd = hypot(px - destX, pz - destZ)
        if (dd < 7f) {
            if (arrivedAt == 0L) arrivedAt = now
            turn = 2; nextDist = 0f; remain = 0f
            if (now - arrivedAt > 4000L) clear()
            return
        }
        if (bd > 14f && now - lastRoute > 1200L) { compute(px, pz); return }
        // distância restante e próxima conversão
        var rem = hypot(r[bi * 2 + 2] - (r[bi * 2] + (r[bi * 2 + 2] - r[bi * 2]) * bt), r[bi * 2 + 3] - (r[bi * 2 + 1] + (r[bi * 2 + 3] - r[bi * 2 + 1]) * bt))
        var nd = rem; var tn = 0; var st = ""
        var found = false
        for (i in bi + 1 until n - 1) {
            val d1x = r[i * 2] - r[i * 2 - 2]; val d1z = r[i * 2 + 1] - r[i * 2 - 1]
            val d2x = r[i * 2 + 2] - r[i * 2]; val d2z = r[i * 2 + 3] - r[i * 2 + 1]
            val l1 = hypot(d1x, d1z); val l2 = hypot(d2x, d2z)
            if (!found && l1 > 0.5f && l2 > 0.5f) {
                val cr = (d1x * d2z - d1z * d2x) / (l1 * l2)
                if (abs(cr) > 0.5f) { found = true; nd = rem; tn = if (cr > 0f) 1 else -1; st = roadName(r[i * 2], r[i * 2 + 1], r[i * 2 + 2], r[i * 2 + 3]) }
            }
            rem += l2
        }
        if (!found) { nd = rem; tn = 0; st = destName }
        turn = tn; nextDist = nd; remain = rem; street = st
        arrivedAt = 0L
    }

    fun distText(d: Float): String = if (d >= 1000f) String.format(java.util.Locale("pt", "BR"), "%.1f km", d / 1000f) else "${(d / 5f).toInt() * 5} m"
}

// ============================================================ desenho comum do mapa

object MapPaint {
    /** Etapa 125: foto da cidade vista de cima (tirada pelo jogo) e o retângulo do mundo que ela cobre. */
    @Volatile var photo: android.graphics.Bitmap? = null
    @Volatile var photoRect = FloatArray(4)
    private val photoPaint = Paint(Paint.FILTER_BITMAP_FLAG or Paint.ANTI_ALIAS_FLAG)
    /** Lugares que sempre aparecem; os outros (lojas) só com zoom. */
    val MAIN = setOf("Sua casa", "Praia", "Píer", "Parque de Diversões", "Hospital", "Shopping", "Praça Central", "Igreja Matriz", "Escola", "Polícia", "Supermercado", "Parque", "Mansões", "Hotel", "Posto")
    val bg = Paint().apply { color = 0xFFCFE6C0.toInt() }
    val sea = Paint().apply { color = 0xFF5FB4DC.toInt() }
    val sand = Paint().apply { color = 0xFFF2E1B5.toInt() }
    val road = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt() }
    val roadEdge = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFB9B9B9.toInt() }
    val bld = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFD7CCC8.toInt() }
    val bldEdge = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFA1887F.toInt(); style = Paint.Style.STROKE; strokeWidth = 1.5f }
    val route = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFF1E88E5.toInt(); style = Paint.Style.STROKE; strokeCap = Paint.Cap.ROUND; strokeJoin = Paint.Join.ROUND }
    val routeEdge = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFF0D47A1.toInt(); style = Paint.Style.STROKE; strokeCap = Paint.Cap.ROUND; strokeJoin = Paint.Join.ROUND }
    val text = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE; typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD); textAlign = Paint.Align.CENTER }
    val label = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFF263238.toInt(); typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD); textAlign = Paint.Align.CENTER }
    val halo = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xE6FFFFFF.toInt(); typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD); textAlign = Paint.Align.CENTER; style = Paint.Style.STROKE; strokeWidth = 5f }
    val fill = Paint(Paint.ANTI_ALIAS_FLAG)

    fun blockColor(t: String): Int = when (t) {
        "res", "lots" -> 0xFFE8E3D3.toInt(); "mansion" -> 0xFFE6DCC0.toInt(); "apt" -> 0xFFE0DCE8.toInt()
        "down", "hotel", "mall" -> 0xFFDCD6E4.toInt(); "shops", "super", "gas" -> 0xFFF6E2C8.toInt()
        "hospital" -> 0xFFF6D6D6.toInt(); "school", "police", "church" -> 0xFFE4E0D8.toInt()
        "praca", "park" -> 0xFFB5DDA0.toInt(); "fun" -> 0xFFF1D6F2.toInt(); else -> 0xFFE8E3D3.toInt()
    }

    /** Desenha a cidade com a transformação mundo -> tela (escala s, mundo (cx, cz) no centro (ox, oy), giro rot em graus). */
    fun drawCity(c: Canvas, s: Float, cx: Float, cz: Float, ox: Float, oy: Float, rot: Float, detail: Boolean) {
        c.save()
        c.translate(ox, oy)
        c.rotate(rot)
        c.scale(s, s)
        c.translate(-cx, -cz)
        c.drawRect(City.X0 - 400f, City.Z0 - 400f, City.X1 + 400f, City.BEACH_Z + 400f, bg)
        if (!City.HDS) {
        c.drawRect(City.X0 - 400f, City.Z1, City.X1 + 400f, City.SEA_Z, sand)
        c.drawRect(City.X0 - 400f, City.SEA_Z - 4f, City.X1 + 400f, City.SEA_Z + 600f, sea)
        fill.color = 0xFFF4F1EA.toInt(); c.drawRect(City.X0 - 400f, City.Z1, City.X1 + 400f, City.BEACH_Z, fill)
        fill.color = 0xFF8D6E63.toInt(); c.drawRect(City.PIER_X - 2.5f, City.BEACH_Z + 4f, City.PIER_X + 2.5f, City.SEA_Z + 62f, fill); c.drawRect(City.PIER_X - 6f, City.SEA_Z + 62f, City.PIER_X + 6f, City.SEA_Z + 70f, fill)
        }
        val ph = photo
        if (ph != null) {
            val r = photoRect
            c.drawBitmap(ph, null, RectF(r[0], r[1], r[2], r[3]), photoPaint)
        } else for (i in 0 until City.NB) for (j in 0 until City.NB) {
            val t = City.types.getOrNull(i)?.getOrNull(j) ?: continue
            fill.color = if (t == "home") 0xFFC8E6C9.toInt() else blockColor(t)
            c.drawRect(City.blkX[i * 2], City.blkZ[j * 2], City.blkX[i * 2 + 1], City.blkZ[j * 2 + 1], fill)
        }
        if (City.HDS && ph == null) Hds.drawMap(c, fill, road)
        if (Town.on) {
            // Etapa 131: cidade nova — quarteirões e ruas curvas
            fill.color = 0xFFE8E3D3.toInt()
            for (bl in Town.blocks) { val p = Path(); p.moveTo(bl[0], bl[1]); var i = 2; while (i < bl.size) { p.lineTo(bl[i], bl[i + 1]); i += 2 }; p.close(); c.drawPath(p, fill) }
            val rp = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE; strokeCap = Paint.Cap.ROUND; strokeJoin = Paint.Join.ROUND }
            for (ed in Town.edges) {
                val p = Path(); p.moveTo(ed.pts[0], ed.pts[1]); var i = 2; while (i < ed.pts.size) { p.lineTo(ed.pts[i], ed.pts[i + 1]); i += 2 }
                rp.color = 0xFFDCD8D0.toInt(); rp.strokeWidth = ed.w + 2 * Town.SW; c.drawPath(p, rp)
                rp.color = road.color; rp.strokeWidth = ed.w; c.drawPath(p, rp)
            }
            for (nd in Town.nodes) { val p = Path(); p.moveTo(nd.poly[0], nd.poly[1]); var i = 2; while (i < nd.poly.size) { p.lineTo(nd.poly[i], nd.poly[i + 1]); i += 2 }; p.close(); c.drawPath(p, road) }
            for (nd in Town.nodes) if (nd.round > 0f) { fill.color = 0xFFB5DDA0.toInt(); c.drawCircle(nd.x, nd.z, nd.round - 8f, fill) }
            // Etapa 145: elevados (borda escura, pista clara e faixa amarela no meio)
            for (e in Elevado.list) {
                val ax = e.px(e.a0, 0f); val az = e.pz(e.a0, 0f); val bx2 = e.px(e.a1, 0f); val bz2 = e.pz(e.a1, 0f)
                rp.strokeCap = Paint.Cap.BUTT
                rp.color = 0xFF6E6A62.toInt(); rp.strokeWidth = Elevado.HW * 2 + 3f; c.drawLine(ax, az, bx2, bz2, rp)
                rp.color = 0xFF8C8F94.toInt(); rp.strokeWidth = Elevado.HW * 2; c.drawLine(ax, az, bx2, bz2, rp)
                rp.color = 0xFFF2C230.toInt(); rp.strokeWidth = 0.8f; c.drawLine(ax, az, bx2, bz2, rp)
                rp.strokeCap = Paint.Cap.ROUND
            }
        }
        val bx = City.bandX; val bz = City.bandZ
        if (ph == null && !Town.on) {
            fill.color = 0xFFDCD8D0.toInt()
            for (k in 0 until bz.size / 2) c.drawRect(City.X0, bz[k * 2], City.X1, bz[k * 2 + 1], fill)
            for (k in 0 until bx.size / 2) c.drawRect(bx[k * 2], City.Z0, bx[k * 2 + 1], City.Z1, fill)
            for (k in 0 until bz.size / 2) c.drawRect(City.X0, bz[k * 2] + City.SIDE, City.X1, bz[k * 2 + 1] - City.SIDE, road)
            for (k in 0 until bx.size / 2) c.drawRect(bx[k * 2] + City.SIDE, City.Z0, bx[k * 2 + 1] - City.SIDE, City.Z1, road)
        }
        if (detail && s > 1.1f) {
            // nomes das ruas
            label.textSize = 5.5f; halo.textSize = 5.5f
            for (k in 1 until bz.size / 2 - 1) {
                val zc = (bz[k * 2] + bz[k * 2 + 1]) / 2
                for (q in 0..1) { val x = City.X0 + (City.X1 - City.X0) * (0.22f + q * 0.56f); c.drawText(City.ROAD_NAMES_X[k], x, zc + 2f, halo); c.drawText(City.ROAD_NAMES_X[k], x, zc + 2f, label) }
            }
            for (k in 1 until bx.size / 2 - 1) {
                val xc = (bx[k * 2] + bx[k * 2 + 1]) / 2
                c.save(); c.rotate(-90f, xc, (City.Z0 + City.Z1) / 2)
                c.drawText(City.ROAD_NAMES_Z[k], xc, (City.Z0 + City.Z1) / 2 + 2f, halo); c.drawText(City.ROAD_NAMES_Z[k], xc, (City.Z0 + City.Z1) / 2 + 2f, label)
                c.restore()
            }
        }
        // rota
        val r = Gps.route
        if (Gps.active && r.size >= 4) {
            val p = Path(); p.moveTo(r[0], r[1])
            var i = 2; while (i < r.size) { p.lineTo(r[i], r[i + 1]); i += 2 }
            routeEdge.strokeWidth = max(4f, 9f / s * 1.0f).coerceAtMost(9f); c.drawPath(p, routeEdge)
            route.strokeWidth = max(2.6f, 6f / s).coerceAtMost(6f); c.drawPath(p, route)
        }
        c.restore()
    }

    fun pin(c: Canvas, x: Float, y: Float, col: Int, ch: Char, r: Float) {
        fill.color = 0x55000000; c.drawCircle(x + r * 0.08f, y + r * 0.12f, r * 1.05f, fill)
        fill.color = Color.WHITE; c.drawCircle(x, y, r * 1.08f, fill)
        fill.color = col; c.drawCircle(x, y, r * 0.9f, fill)
        text.textSize = r * 1.05f
        c.drawText(ch.toString(), x, y + r * 0.37f, text)
    }

    fun tag(c: Canvas, t: String, x: Float, y: Float, size: Float) {
        label.textSize = size; halo.textSize = size; halo.strokeWidth = size * 0.35f
        c.drawText(t, x, y, halo); c.drawText(t, x, y, label)
    }

    fun arrow(c: Canvas, x: Float, y: Float, ang: Float, r: Float) {
        c.save(); c.translate(x, y); c.rotate(ang)
        fill.color = 0x44000000; c.drawCircle(0f, 0f, r * 1.6f, fill)
        val p = Path(); p.moveTo(0f, -r * 1.3f); p.lineTo(r, r); p.lineTo(0f, r * 0.45f); p.lineTo(-r, r); p.close()
        fill.color = Color.WHITE; c.drawPath(p, fill)
        c.scale(0.72f, 0.72f); fill.color = 0xFF1E88E5.toInt(); c.drawPath(p, fill)
        c.restore()
    }
}

// ============================================================ mapa em tela cheia

@SuppressLint("ViewConstructor")
class MapOverlay(ctx: Context, private val player: () -> FloatArray, private val onClose: () -> Unit) : FrameLayout(ctx) {
    private val dens = resources.displayMetrics.density
    private fun dp(v: Float) = v * dens
    private var scale = 1.2f
    private var cx = 0f; private var cz = 0f
    private var selX = Float.NaN; private var selZ = 0f; private var selName = ""
    private val map: View
    private val sheet: LinearLayout
    private val sheetTitle: TextView
    private val sheetSub: TextView
    private val goBtn: TextView

    init {
        setBackgroundColor(0xFF0F1A24.toInt())
        isClickable = true
        val p = player()
        cx = p[0]; cz = p[1]
        map = object : View(ctx) {
            override fun onDraw(c: Canvas) {
                val pl = player()
                MapPaint.drawCity(c, scale, cx, cz, width / 2f, height / 2f, 0f, true)
                fun sx(x: Float) = width / 2f + (x - cx) * scale
                fun sy(z: Float) = height / 2f + (z - cz) * scale
                // lugares principais sempre; lojas e terrenos só com zoom (com o nome embaixo)
                for (pl2 in City.places) {
                    val main = pl2.name in MapPaint.MAIN
                    if (!main && scale < 2.2f) continue
                    MapPaint.pin(c, sx(pl2.x), sy(pl2.z), pl2.color, pl2.icon, dp(if (main) 11f else 8f))
                    if (main || scale > 3f) MapPaint.tag(c, pl2.name, sx(pl2.x), sy(pl2.z) + dp(if (main) 22f else 17f), dp(11f))
                }
                if (!selX.isNaN()) {
                    val x = sx(selX); val y = sy(selZ)
                    MapPaint.fill.color = 0xFFE53935.toInt()
                    val path = Path(); path.moveTo(x, y); path.lineTo(x - dp(9f), y - dp(18f)); path.lineTo(x + dp(9f), y - dp(18f)); path.close()
                    c.drawPath(path, MapPaint.fill); c.drawCircle(x, y - dp(22f), dp(11f), MapPaint.fill)
                    MapPaint.fill.color = Color.WHITE; c.drawCircle(x, y - dp(22f), dp(4.5f), MapPaint.fill)
                }
                if (Gps.active) MapPaint.pin(c, sx(Gps.destX), sy(Gps.destZ), 0xFFE53935.toInt(), '★', dp(11f))
                // jogador: seta na direção da câmera
                MapPaint.arrow(c, sx(pl[0]), sy(pl[1]), Math.toDegrees(pl[2].toDouble()).toFloat(), dp(9f))
                // escala
                val m = 100f * scale
                MapPaint.fill.color = 0xCC000000.toInt(); c.drawRoundRect(RectF(dp(14f), height - dp(40f), dp(30f) + m, height - dp(16f)), dp(6f), dp(6f), MapPaint.fill)
                MapPaint.fill.color = Color.WHITE; c.drawRect(dp(22f), height - dp(24f), dp(22f) + m, height - dp(21f), MapPaint.fill)
                MapPaint.text.textSize = dp(10f); c.drawText("100 m", dp(22f) + m / 2, height - dp(27f), MapPaint.text)
            }
        }
        addView(map, LayoutParams(-1, -1))
        val sg = ScaleGestureDetector(ctx, object : ScaleGestureDetector.SimpleOnScaleGestureListener() {
            override fun onScale(d: ScaleGestureDetector): Boolean { scale = (scale * d.scaleFactor).coerceIn(0.35f, 6f); map.invalidate(); return true }
        })
        var lx = 0f; var ly = 0f; var moved = 0f; var multi = false
        map.setOnTouchListener { _, e ->
            sg.onTouchEvent(e)
            when (e.actionMasked) {
                MotionEvent.ACTION_DOWN -> { lx = e.x; ly = e.y; moved = 0f; multi = false }
                MotionEvent.ACTION_POINTER_DOWN -> multi = true
                MotionEvent.ACTION_MOVE -> if (!sg.isInProgress && e.pointerCount == 1) {
                    val dx = e.x - lx; val dy = e.y - ly
                    cx -= dx / scale; cz -= dy / scale; moved += abs(dx) + abs(dy)
                    lx = e.x; ly = e.y; map.invalidate()
                }
                MotionEvent.ACTION_UP -> if (!multi && moved < dp(10f)) {
                    val wx = cx + (e.x - map.width / 2f) / scale; val wz = cz + (e.y - map.height / 2f) / scale
                    select(wx, wz)
                }
            }
            true
        }
        // barra de cima: título, fechar, atalhos
        val top = LinearLayout(ctx); top.orientation = LinearLayout.VERTICAL
        top.setPadding(dp(12f).toInt(), dp(10f).toInt(), dp(12f).toInt(), dp(6f).toInt())
        top.background = android.graphics.drawable.GradientDrawable(android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM, intArrayOf(0xEE0F1A24.toInt(), 0x000F1A24))
        val row = LinearLayout(ctx); row.orientation = LinearLayout.HORIZONTAL; row.gravity = Gravity.CENTER_VERTICAL
        val title = TextView(ctx); title.text = "Mapa da cidade"; title.textSize = 20f; title.setTextColor(Color.WHITE); title.typeface = Typeface.DEFAULT_BOLD
        row.addView(title, LinearLayout.LayoutParams(0, -2, 1f))
        val me = chip("Eu", 0xFF1E88E5.toInt()) { val pl = player(); cx = pl[0]; cz = pl[1]; scale = max(scale, 1.4f); map.invalidate() }
        row.addView(me)
        val close = TextView(ctx); close.text = "✕"; close.textSize = 22f; close.setTextColor(Color.WHITE); close.gravity = Gravity.CENTER
        close.background = Ui.frost(dp(20f), 0x26394F, 0xE0, 0xB0, dp(1.2f)); close.setOnClickListener { onClose() }
        row.addView(close, LinearLayout.LayoutParams(dp(42f).toInt(), dp(42f).toInt()).also { it.leftMargin = dp(8f).toInt() })
        top.addView(row)
        val hs = HorizontalScrollView(ctx); hs.isHorizontalScrollBarEnabled = false
        val chips = LinearLayout(ctx); chips.orientation = LinearLayout.HORIZONTAL
        val seen = HashSet<String>()
        for (pl in City.places) {
            if (!seen.add(pl.name)) continue
            chips.addView(chip(pl.name, pl.color) { cx = pl.x; cz = pl.z; scale = max(scale, 1.6f); select(pl.x, pl.z, pl.name); })
        }
        hs.addView(chips)
        top.addView(hs, LinearLayout.LayoutParams(-1, -2).also { it.topMargin = dp(8f).toInt() })
        addView(top, LayoutParams(-1, -2, Gravity.TOP))
        // painel de baixo: destino escolhido
        sheet = LinearLayout(ctx); sheet.orientation = LinearLayout.HORIZONTAL; sheet.gravity = Gravity.CENTER_VERTICAL
        sheet.setPadding(dp(16f).toInt(), dp(12f).toInt(), dp(12f).toInt(), dp(12f).toInt())
        sheet.background = Ui.frost(dp(22f), 0x16273A, 0xF4, 0xD8, dp(1.4f))
        val col = LinearLayout(ctx); col.orientation = LinearLayout.VERTICAL
        sheetTitle = TextView(ctx); sheetTitle.textSize = 17f; sheetTitle.setTextColor(Color.WHITE); sheetTitle.typeface = Typeface.DEFAULT_BOLD
        sheetSub = TextView(ctx); sheetSub.textSize = 13f; sheetSub.setTextColor(0xFFB0C4D8.toInt())
        col.addView(sheetTitle); col.addView(sheetSub)
        sheet.addView(col, LinearLayout.LayoutParams(0, -2, 1f))
        goBtn = TextView(ctx); goBtn.text = "  Ir com GPS  "; goBtn.textSize = 15f; goBtn.setTextColor(Color.WHITE); goBtn.typeface = Typeface.DEFAULT_BOLD; goBtn.gravity = Gravity.CENTER
        goBtn.background = Ui.chunky(Tn.SIMS_BLUE, dp(18f), dp(3f), true, 0xFFFFFFFF.toInt(), dp(1.6f))
        goBtn.setPadding(dp(14f).toInt(), dp(10f).toInt(), dp(14f).toInt(), dp(12f).toInt())
        goBtn.setOnClickListener {
            if (!selX.isNaN()) { val pl = player(); Gps.setDest(selX, selZ, selName, pl[0], pl[1]); onClose() }
        }
        sheet.addView(goBtn)
        sheet.visibility = if (Gps.active) VISIBLE else GONE
        addView(sheet, LayoutParams(-1, -2, Gravity.BOTTOM).also { it.setMargins(dp(14f).toInt(), 0, dp(14f).toInt(), dp(56f).toInt()) })
        if (Gps.active) {
            sheetTitle.text = "Rota para ${Gps.destName}"; sheetSub.text = Gps.distText(Gps.remain) + " restantes"
            goBtn.text = "  Cancelar rota  "; goBtn.background = Ui.chunky(Tn.CORAL, dp(18f), dp(3f), true, 0xFFFFFFFF.toInt(), dp(1.6f))
            goBtn.setOnClickListener { Gps.clear(); onClose() }
        }
    }

    private fun chip(t: String, col: Int, act: () -> Unit): TextView {
        val v = TextView(context); v.text = t; v.textSize = 13f; v.setTextColor(Color.WHITE); v.typeface = Typeface.DEFAULT_BOLD
        v.setPadding(dp(12f).toInt(), dp(7f).toInt(), dp(12f).toInt(), dp(7f).toInt())
        val g = android.graphics.drawable.GradientDrawable(); g.cornerRadius = dp(16f); g.setColor(col); g.setStroke(dp(1.2f).toInt(), 0xAAFFFFFF.toInt())
        v.background = g
        v.setOnClickListener { act() }
        v.layoutParams = LinearLayout.LayoutParams(-2, -2).also { it.rightMargin = dp(6f).toInt() }
        return v
    }

    private fun select(x: Float, z: Float, name0: String? = null) {
        if (!City.on) return
        selX = x.coerceIn(City.X0 + 2f, City.X1 - 2f); selZ = z.coerceIn(City.Z0 + 2f, City.SEA_Z + 60f)
        var name = name0
        if (name == null) {
            var bd = 30f
            for (p in City.places) { val d = hypot(p.x - selX, p.z - selZ); if (d < bd) { bd = d; name = p.name } }
            if (name == null) City.bldAt(selX, selZ)?.let { name = it.name + (if (it.forSale) " (à venda)" else "") }
            if (name == null) name = if (selZ > City.Z1) "Praia" else "Ponto no mapa"
        }
        selName = name ?: ""
        val pl = player()
        sheetTitle.text = selName
        sheetSub.text = Gps.distText(abs(pl[0] - selX) + abs(pl[1] - selZ)) + " a pé, pelas ruas"
        goBtn.text = "  Ir com GPS  "; goBtn.background = Ui.chunky(Tn.SIMS_BLUE, dp(18f), dp(3f), true, 0xFFFFFFFF.toInt(), dp(1.6f))
        goBtn.setOnClickListener { if (!selX.isNaN()) { val p2 = player(); Gps.setDest(selX, selZ, selName, p2[0], p2[1]); onClose() } }
        sheet.visibility = VISIBLE
        map.invalidate()
    }
}

// ============================================================ HUD do GPS (faixa de cima) e minimapa

class GpsHud(ctx: Context) : View(ctx) {
    private val dens = resources.displayMetrics.density
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)
    private val path = Path()
    private val rf = RectF()

    override fun onDraw(c: Canvas) {
        if (!Gps.active) return
        val w = width.toFloat(); val h = height.toFloat()
        rf.set(0f, 0f, w, h)
        p.shader = LinearGradient(0f, 0f, 0f, h, 0xF21565C0.toInt(), 0xF20D47A1.toInt(), Shader.TileMode.CLAMP)
        c.drawRoundRect(rf, 18 * dens, 18 * dens, p)
        p.shader = null
        p.style = Paint.Style.STROKE; p.strokeWidth = 1.5f * dens; p.color = 0x66FFFFFF
        c.drawRoundRect(rf, 18 * dens, 18 * dens, p)
        p.style = Paint.Style.FILL
        // ícone da manobra
        val ix = h / 2; val iy = h / 2; val s = h * 0.32f
        p.color = Color.WHITE
        c.save(); c.translate(ix, iy)
        when (Gps.turn) {
            2 -> { c.drawCircle(0f, -s * 0.2f, s * 0.55f, p); path.reset(); path.moveTo(-s * 0.45f, 0f); path.lineTo(0f, s * 0.95f); path.lineTo(s * 0.45f, 0f); path.close(); c.drawPath(path, p); p.color = 0xFF1565C0.toInt(); c.drawCircle(0f, -s * 0.2f, s * 0.22f, p) }
            0 -> { c.drawRect(-s * 0.16f, -s * 0.2f, s * 0.16f, s * 0.95f, p); path.reset(); path.moveTo(0f, -s); path.lineTo(s * 0.55f, -s * 0.15f); path.lineTo(-s * 0.55f, -s * 0.15f); path.close(); c.drawPath(path, p) }
            else -> {
                val d = Gps.turn.toFloat()
                c.drawRect(-s * 0.16f - d * s * 0.25f, -s * 0.26f, s * 0.16f - d * s * 0.25f, s * 0.95f, p)
                c.drawRect(min(-d * s * 0.25f, d * s * 0.4f), -s * 0.26f, max(-d * s * 0.25f, d * s * 0.4f), s * 0.06f, p)
                path.reset(); path.moveTo(d * s * 0.98f, -s * 0.1f); path.lineTo(d * s * 0.36f, -s * 0.62f); path.lineTo(d * s * 0.36f, s * 0.42f); path.close(); c.drawPath(path, p)
            }
        }
        c.restore()
        val tx = h + 6 * dens
        p.color = Color.WHITE; p.typeface = Typeface.DEFAULT_BOLD; p.textAlign = Paint.Align.LEFT
        p.textSize = 20 * dens
        val big = when (Gps.turn) { 2 -> "Você chegou!"; else -> Gps.distText(Gps.nextDist) }
        c.drawText(big, tx, h * 0.45f, p)
        p.textSize = 13 * dens; p.typeface = Typeface.DEFAULT; p.color = 0xFFDDEBFF.toInt()
        val small = when (Gps.turn) {
            2 -> Gps.destName
            1 -> "Vire à direita" + (if (Gps.street.isNotEmpty()) " na ${Gps.street}" else "")
            -1 -> "Vire à esquerda" + (if (Gps.street.isNotEmpty()) " na ${Gps.street}" else "")
            else -> "Siga em frente até ${Gps.destName}"
        }
        c.drawText(ellipsize(small, w - tx - 10 * dens), tx, h * 0.72f, p)
        if (Gps.turn != 2) {
            p.textAlign = Paint.Align.RIGHT; p.textSize = 11 * dens; p.color = 0xFFB3D4FF.toInt()
            c.drawText("${Gps.distText(Gps.remain)} · ${max(1, (Gps.remain / 1.4f / 60f).toInt())} min", w - 12 * dens, h * 0.3f, p)
        }
    }

    private fun ellipsize(s: String, w: Float): String {
        if (p.measureText(s) <= w) return s
        var t = s
        while (t.length > 3 && p.measureText("$t…") > w) t = t.dropLast(1)
        return "$t…"
    }
}

class MiniMap(ctx: Context, private val player: () -> FloatArray) : View(ctx) {
    private val dens = resources.displayMetrics.density
    private val clip = Path()
    private val p = Paint(Paint.ANTI_ALIAS_FLAG)

    override fun onDraw(c: Canvas) {
        if (!City.on) return
        val w = width.toFloat(); val r = w / 2f
        val pl = player()
        clip.reset(); clip.addCircle(r, r, r - 2 * dens, Path.Direction.CW)
        c.save(); c.clipPath(clip)
        // gira com a câmera: para onde se olha fica para cima
        val rot = -Math.toDegrees(pl[2].toDouble()).toFloat()
        val s = r / 55f
        MapPaint.drawCity(c, s, pl[0], pl[1], r, r, rot, false)
        if (Gps.active) {
            c.save(); c.translate(r, r); c.rotate(rot); c.scale(s, s); c.translate(-pl[0], -pl[1])
            MapPaint.fill.color = 0xFFE53935.toInt(); c.drawCircle(Gps.destX, Gps.destZ, 5f, MapPaint.fill)
            c.restore()
        }
        c.restore()
        MapPaint.arrow(c, r, r, 0f, 6 * dens)
        p.style = Paint.Style.STROKE; p.strokeWidth = 3 * dens; p.color = Color.WHITE
        c.drawCircle(r, r, r - 2 * dens, p)
        p.strokeWidth = 1 * dens; p.color = 0x55000000
        c.drawCircle(r, r, r - 0.5f * dens, p)
        // norte
        p.style = Paint.Style.FILL
        val na = Math.toRadians(rot.toDouble())
        val nx = r + (r - 9 * dens) * sin(na).toFloat() * -1f * -1f
        val ny = r - (r - 9 * dens) * cos(na).toFloat()
        p.color = 0xFFE53935.toInt(); c.drawCircle(nx, ny, 7 * dens, p)
        p.color = Color.WHITE; p.textSize = 9 * dens; p.textAlign = Paint.Align.CENTER; p.typeface = Typeface.DEFAULT_BOLD
        c.drawText("N", nx, ny + 3.2f * dens, p)
    }
}
