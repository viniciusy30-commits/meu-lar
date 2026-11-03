package com.vinicius.meular

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Miniaturas (a "foto de prévia" de cada peça, como no The Sims): rasterizador de software que desenha a malha da peça
 * (formato CUP1/CUT1 de 44 bytes por vértice) com a textura dela, vista de frente, com sombreado suave e contorno.
 * Código puro (sem android.*): é usado pelo jogo para peças importadas e pela ferramenta que gera as miniaturas embutidas.
 */
object Thumb {
    class Mesh(val pos: FloatArray, val nor: FloatArray, val uv: FloatArray, val idx: IntArray) {
        val nv: Int get() = pos.size / 3
    }

    /** [pixels] = ARGB (w*h) da textura, ou null para cor lisa [color]. [cut] = recorte por alfa (mechas de cabelo). */
    class Piece(val mesh: Mesh, val pixels: IntArray?, val tw: Int, val th: Int, val color: Int, val cut: Boolean = false, val support: Boolean = false)

    fun parse(b: ByteArray): Mesh {
        val bb = ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN)
        val nv = bb.getInt(4)
        val ni = bb.getInt(8)
        val pos = FloatArray(nv * 3)
        val nor = FloatArray(nv * 3)
        val uv = FloatArray(nv * 2)
        for (i in 0 until nv) {
            val o = 16 + i * 44
            for (k in 0 until 3) { pos[i * 3 + k] = bb.getFloat(o + k * 4); nor[i * 3 + k] = bb.getFloat(o + 12 + k * 4) }
            uv[i * 2] = bb.getFloat(o + 24)
            uv[i * 2 + 1] = bb.getFloat(o + 28)
        }
        val io = 16 + nv * 44
        val idx = IntArray(ni) { bb.getShort(io + it * 2).toInt() and 0xFFFF }
        return Mesh(pos, nor, uv, idx)
    }

    /** Só a cabeça e o pescoço do corpo (para mostrar o cabelo sobre uma cabeça). */
    fun headOf(body: Mesh): Mesh {
        var ymax = -1e9f
        for (i in 0 until body.nv) ymax = maxOf(ymax, body.pos[i * 3 + 1])
        val lim = ymax * 0.86f
        val keep = ArrayList<Int>()
        var t = 0
        while (t + 2 < body.idx.size) {
            val a = body.idx[t]; val b = body.idx[t + 1]; val c = body.idx[t + 2]
            if (body.pos[a * 3 + 1] > lim && body.pos[b * 3 + 1] > lim && body.pos[c * 3 + 1] > lim) { keep.add(a); keep.add(b); keep.add(c) }
            t += 3
        }
        return Mesh(body.pos, body.nor, body.uv, keep.toIntArray())
    }

    /**
     * Desenha as peças. [slot]: "feet" = vista 3/4 de cima; "hairBack"/"hat" etc. = vista 3/4 leve; o resto, de frente.
     * Devolve ARGB (size*size), fundo transparente.
     */
    fun render(parts: List<Piece>, slot: String, size: Int = 256): IntArray {
        val ss = 2
        val W = size * ss
        val yaw = when (slot) { "feet" -> -0.62f; "hairBack", "hairFront", "hat", "headAcc", "glasses", "beard" -> -0.28f; else -> 0f }
        val pitch = when (slot) { "feet" -> 0.30f; else -> 0.04f }
        val cy = Math.cos(yaw.toDouble()).toFloat(); val sy = Math.sin(yaw.toDouble()).toFloat()
        val cp = Math.cos(pitch.toDouble()).toFloat(); val sp = Math.sin(pitch.toDouble()).toFloat()
        // projeção ortográfica: gira em y (yaw) e depois em x (pitch); câmera olhando para -z
        fun proj(m: Mesh): FloatArray {
            val o = FloatArray(m.nv * 3)
            for (i in 0 until m.nv) {
                val x = m.pos[i * 3]; val y = m.pos[i * 3 + 1]; val z = m.pos[i * 3 + 2]
                val x1 = x * cy + z * sy; val z1 = -x * sy + z * cy
                val y2 = y * cp - z1 * sp; val z2 = y * sp + z1 * cp
                o[i * 3] = x1; o[i * 3 + 1] = y2; o[i * 3 + 2] = z2
            }
            return o
        }
        val pr = parts.map { proj(it.mesh) }
        var x0 = 1e9f; var x1 = -1e9f; var y0 = 1e9f; var y1 = -1e9f
        // o enquadramento usa só as peças "principais" (a cabeça de apoio do cabelo não conta além do cabelo)
        for ((k, p) in parts.withIndex()) {
            if (p.support) continue
            val m = p.mesh
            val used = BooleanArray(m.nv)
            for (i in m.idx) used[i] = true
            for (i in 0 until m.nv) if (used[i]) {
                val x = pr[k][i * 3]; val y = pr[k][i * 3 + 1]
                if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y
            }
        }
        if (x1 <= x0 || y1 <= y0) return IntArray(size * size)
        val padK = if (slot == "hairBack" || slot == "hairFront") 1.22f else 1.12f
        val span = maxOf(x1 - x0, y1 - y0) * padK
        val sc = W / span
        val cx = (x0 + x1) / 2f; val cyy = (y0 + y1) / 2f
        val col = IntArray(W * W)
        val zb = FloatArray(W * W) { -1e9f }
        val lx = 0.35f; val ly = 0.55f; val lz = 0.76f
        val ll = Math.sqrt((lx * lx + ly * ly + lz * lz).toDouble()).toFloat()
        for ((k, p) in parts.withIndex()) {
            val m = p.mesh; val P = pr[k]
            // normais giradas igual às posições
            val N = FloatArray(m.nv * 3)
            for (i in 0 until m.nv) {
                val x = m.nor[i * 3]; val y = m.nor[i * 3 + 1]; val z = m.nor[i * 3 + 2]
                val xa = x * cy + z * sy; val za = -x * sy + z * cy
                N[i * 3] = xa; N[i * 3 + 1] = y * cp - za * sp; N[i * 3 + 2] = y * sp + za * cp
            }
            val sX = FloatArray(m.nv) { W / 2f + (P[it * 3] - cx) * sc }
            val sY = FloatArray(m.nv) { W / 2f - (P[it * 3 + 1] - cyy) * sc }
            var t = 0
            while (t + 2 < m.idx.size) {
                val a = m.idx[t]; val b = m.idx[t + 1]; val c = m.idx[t + 2]; t += 3
                val xa = sX[a]; val xb = sX[b]; val xc = sX[c]; val ya = sY[a]; val yb = sY[b]; val yc = sY[c]
                val mnx = maxOf(0, Math.floor(minOf(xa, xb, xc).toDouble()).toInt()); val mxx = minOf(W - 1, Math.ceil(maxOf(xa, xb, xc).toDouble()).toInt())
                val mny = maxOf(0, Math.floor(minOf(ya, yb, yc).toDouble()).toInt()); val mxy = minOf(W - 1, Math.ceil(maxOf(ya, yb, yc).toDouble()).toInt())
                val den = (yb - yc) * (xa - xc) + (xc - xb) * (ya - yc)
                if (Math.abs(den) < 1e-9f) continue
                for (py in mny..mxy) for (px in mnx..mxx) {
                    val fx = px + 0.5f; val fy = py + 0.5f
                    val wa = ((yb - yc) * (fx - xc) + (xc - xb) * (fy - yc)) / den
                    val wb = ((yc - ya) * (fx - xc) + (xa - xc) * (fy - yc)) / den
                    val wc = 1f - wa - wb
                    if (wa < -0.001f || wb < -0.001f || wc < -0.001f) continue
                    val z = wa * P[a * 3 + 2] + wb * P[b * 3 + 2] + wc * P[c * 3 + 2]
                    val zi = py * W + px
                    if (z <= zb[zi]) continue
                    var r: Int; var g: Int; var bl: Int
                    if (p.pixels != null) {
                        val u = wa * m.uv[a * 2] + wb * m.uv[b * 2] + wc * m.uv[c * 2]
                        val v = wa * m.uv[a * 2 + 1] + wb * m.uv[b * 2 + 1] + wc * m.uv[c * 2 + 1]
                        val tx = (u * p.tw).toInt().coerceIn(0, p.tw - 1)
                        val ty = (v * p.th).toInt().coerceIn(0, p.th - 1)
                        val px4 = p.pixels[ty * p.tw + tx]
                        if (p.cut && (px4 ushr 24) < 115) continue
                        r = (px4 shr 16) and 255; g = (px4 shr 8) and 255; bl = px4 and 255
                    } else {
                        r = (p.color shr 16) and 255; g = (p.color shr 8) and 255; bl = p.color and 255
                    }
                    val nx = wa * N[a * 3] + wb * N[b * 3] + wc * N[c * 3]
                    val ny = wa * N[a * 3 + 1] + wb * N[b * 3 + 1] + wc * N[c * 3 + 1]
                    val nz = wa * N[a * 3 + 2] + wb * N[b * 3 + 2] + wc * N[c * 3 + 2]
                    val nl = Math.sqrt((nx * nx + ny * ny + nz * nz).toDouble()).toFloat().coerceAtLeast(1e-6f)
                    val d = Math.abs(nx * lx + ny * ly + nz * lz) / (nl * ll)
                    val sh = 0.55f + 0.55f * d
                    r = (r * sh).toInt().coerceAtMost(255); g = (g * sh).toInt().coerceAtMost(255); bl = (bl * sh).toInt().coerceAtMost(255)
                    zb[zi] = z
                    col[zi] = (255 shl 24) or (r shl 16) or (g shl 8) or bl
                }
            }
        }
        // reduz (média 2x2) e contorno suave
        val out = IntArray(size * size)
        for (y in 0 until size) for (x in 0 until size) {
            var a = 0; var r = 0; var g = 0; var b = 0
            for (dy in 0 until ss) for (dx in 0 until ss) {
                val c = col[(y * ss + dy) * W + x * ss + dx]
                if ((c ushr 24) != 0) { a += 255; r += (c shr 16) and 255; g += (c shr 8) and 255; b += c and 255 }
            }
            val n = ss * ss
            if (a > 0) {
                val cnt = a / 255
                out[y * size + x] = ((a / n) shl 24) or ((r / cnt) shl 16) or ((g / cnt) shl 8) or (b / cnt)
            }
        }
        // contorno cinza-azulado fino ao redor da silhueta
        val res = out.copyOf()
        for (y in 0 until size) for (x in 0 until size) {
            if ((out[y * size + x] ushr 24) > 40) continue
            var near = 0
            for (dy in -2..2) for (dx in -2..2) {
                val xx = x + dx; val yy = y + dy
                if (xx < 0 || yy < 0 || xx >= size || yy >= size) continue
                if ((out[yy * size + xx] ushr 24) > 200) near++
            }
            if (near > 0) res[y * size + x] = (minOf(150, 40 + near * 14) shl 24) or 0x4B6378
        }
        return res
    }
}
