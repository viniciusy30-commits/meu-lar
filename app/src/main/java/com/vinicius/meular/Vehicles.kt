package com.vinicius.meular

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Etapa 122: veículos detalhados.
 * Carroceria por perfil lateral extrudado (capô, para-brisa, teto e porta-malas com chanfro), caixas de roda,
 * rodas com pneu, aro e raios, faróis, lanternas, grade, retrovisores, maçanetas, placas, para-choques.
 * Tipos: sedã, hatch, SUV, picape, esportivo, táxi, van, ônibus, viatura, ambulância, bombeiros, moto esportiva e scooter (com piloto).
 * Comprimento sempre em +z local (frente), largura em x, chão em y = 0.
 */
object Vehicles {
    const val SEDAN = 0; const val HATCH = 1; const val SUV = 2; const val PICKUP = 3; const val SPORT = 4; const val TAXI = 5
    const val VAN = 6; const val BUS = 7; const val POLICE = 8; const val AMBULANCE = 9; const val FIRE = 10; const val MOTO = 11; const val SCOOTER = 12

    private val PAINT = arrayOf("#C62828", "#1565C0", "#F5F5F5", "#212121", "#9E9E9E", "#2E7D32", "#6D4C41", "#0D47A1", "#B0BEC5", "#E65100", "#4A148C", "#00695C", "#F9A825", "#37474F", "#AD1457")

    /** Variantes de trânsito: tipo + cor. */
    private class Var(val kind: Int, val color: Int)
    private val vars = ArrayList<Var>()
    var meshes: Array<Mesh?> = arrayOfNulls(0)
        private set

    fun release() { meshes.forEach { it?.release() }; meshes = arrayOfNulls(0); vars.clear() }

    fun build() {
        release()
        val r = City.Rng(31337)
        fun add(k: Int, n: Int) { for (i in 0 until n) vars.add(Var(k, C(PAINT[r.i(PAINT.size)]))) }
        add(SEDAN, 6); add(HATCH, 5); add(SUV, 5); add(PICKUP, 3); add(SPORT, 3); add(TAXI, 2); add(VAN, 2); add(BUS, 1); add(POLICE, 1); add(MOTO, 4); add(SCOOTER, 3)
        meshes = Array(vars.size) { i -> val b = MB(); geom(XF(b, 0f, 0f, 0f, 1), vars[i].kind, vars[i].color); b.toMesh(true) }
    }

    fun pick(r: City.Rng): Int {
        // ônibus e viatura mais raros
        while (true) {
            val i = r.i(vars.size)
            val k = vars[i].kind
            if ((k == BUS || k == POLICE) && !r.chance(0.35f)) continue
            return i
        }
    }
    fun kind(m: Int) = vars.getOrNull(m)?.kind ?: SEDAN
    fun halfL(m: Int) = when (kind(m)) { BUS -> 5.6f; VAN -> 2.6f; PICKUP -> 2.6f; SUV -> 2.4f; MOTO, SCOOTER -> 1.05f; HATCH -> 2.0f; else -> 2.3f }
    fun halfW(m: Int) = when (kind(m)) { BUS -> 1.3f; MOTO, SCOOTER -> 0.4f; else -> 0.95f }
    fun speedK(m: Int) = when (kind(m)) { BUS -> 0.75f; MOTO -> 1.15f; SPORT -> 1.12f; SCOOTER -> 0.85f; else -> 1f }

    /** Veículo parado, gravado direto na malha do quarteirão. */
    fun parked(g: CityGeo.Gen, x: Float, z: Float, axis: Int, y: Float, r: City.Rng) {
        val k = arrayOf(SEDAN, SEDAN, HATCH, HATCH, SUV, SUV, PICKUP, SPORT, VAN)[r.i(9)]
        place(g, x, z, axis, y, k, C(PAINT[r.i(PAINT.size)]))
    }

    fun parkedKind(g: CityGeo.Gen, x: Float, z: Float, axis: Int, y: Float, kind: Int) = place(g, x, z, axis, y, kind, C("#FFFFFF"))

    private fun place(g: CityGeo.Gen, x: Float, z: Float, axis: Int, y: Float, kind: Int, col: Int) {
        geom(XF(g.b, x, y, z, axis), kind, col)
        val hl = when (kind) { BUS -> 5.6f; VAN, PICKUP, FIRE, AMBULANCE -> 2.7f; else -> 2.3f } + 0.1f
        val hw = if (kind == BUS || kind == FIRE) 1.35f else 1.0f
        if (axis == 1) g.solid(x - hw, z - hl, x + hw, z + hl) else g.solid(x - hl, z - hw, x + hl, z + hw)
        // longe: só um bloco na cor
        g.f.m(Mt.METAL, 1f)
        val hh = if (kind == BUS || kind == FIRE) 3.0f else if (kind == SUV || kind == VAN || kind == AMBULANCE) 1.8f else 1.4f
        if (axis == 1) g.f.box(x, y + hh / 2, z, hw * 1.8f, hh, hl * 1.9f, col) else g.f.box(x, y + hh / 2, z, hl * 1.9f, hh, hw * 1.8f, col)
    }

    // ------------------------------------------------------------ transformação local -> mundo

    /** Escreve em [b] com origem (ox, oy, oz); axis 1 = comprimento em z, axis 0 = comprimento em x (gira 90°). */
    class XF(val b: MB, val ox: Float, val oy: Float, val oz: Float, val axis: Int) {
        fun px(lx: Float, lz: Float) = if (axis == 1) ox + lx else ox + lz
        fun pz(lx: Float, lz: Float) = if (axis == 1) oz + lz else oz - lx
        fun nx(lx: Float, lz: Float) = if (axis == 1) lx else lz
        fun nz(lx: Float, lz: Float) = if (axis == 1) lz else -lx
        fun box(lx: Float, ly: Float, lz: Float, sx: Float, sy: Float, sz: Float, c: Int, lit: Boolean = true) {
            if (axis == 1) b.box(ox + lx, oy + ly, oz + lz, sx, sy, sz, c, lit) else b.box(ox + lz, oy + ly, oz - lx, sz, sy, sx, c, lit)
        }
        fun v(lx: Float, ly: Float, lz: Float, nlx: Float, ny: Float, nlz: Float, c: Int) {
            b.v(px(lx, lz), oy + ly, pz(lx, lz), nx(nlx, nlz), ny, nz(nlx, nlz), c, px(lx, lz), oy + ly)
        }
        fun quad(a: FloatArray, bb: FloatArray, cc: FloatArray, d: FloatArray, c: Int, lit: Boolean = true) {
            val ux = bb[0] - a[0]; val uy = bb[1] - a[1]; val uz = bb[2] - a[2]
            val vx = d[0] - a[0]; val vy = d[1] - a[1]; val vz = d[2] - a[2]
            var nx = uy * vz - uz * vy; var ny = uz * vx - ux * vz; var nz = ux * vy - uy * vx
            val l = sqrt(nx * nx + ny * ny + nz * nz).coerceAtLeast(1e-6f); nx /= l; ny /= l; nz /= l
            if (!lit) { nx = 0f; ny = 0f; nz = 0f }
            for (p in arrayOf(a, bb, cc, a, cc, d)) v(p[0], p[1], p[2], nx, ny, nz, c)
        }
        /** Cilindro deitado (eixo em x local), centro (lx, ly, lz), raio r, largura w. */
        fun cylX(lx: Float, ly: Float, lz: Float, r: Float, w: Float, c: Int, seg: Int = 14, cap: Int = c) {
            val x0 = lx - w / 2; val x1 = lx + w / 2
            for (i in 0 until seg) {
                val a0 = 2f * PI.toFloat() * i / seg; val a1 = 2f * PI.toFloat() * (i + 1) / seg
                val y0 = cos(a0); val z0 = sin(a0); val y1 = cos(a1); val z1 = sin(a1)
                val p00 = floatArrayOf(x0, ly + r * y0, lz + r * z0); val p01 = floatArrayOf(x1, ly + r * y0, lz + r * z0)
                val p11 = floatArrayOf(x1, ly + r * y1, lz + r * z1); val p10 = floatArrayOf(x0, ly + r * y1, lz + r * z1)
                val ny = (y0 + y1) / 2; val nz = (z0 + z1) / 2
                for (p in arrayOf(p00, p01, p11, p00, p11, p10)) v(p[0], p[1], p[2], 0f, ny, nz, c)
                for (sx in floatArrayOf(x0, x1)) {
                    val n = if (sx == x1) 1f else -1f
                    v(sx, ly, lz, n, 0f, 0f, cap); v(sx, ly + r * y0, lz + r * z0, n, 0f, 0f, cap); v(sx, ly + r * y1, lz + r * z1, n, 0f, 0f, cap)
                }
            }
        }
        /** Disco na lateral (x = [x], normal ±x) — sombra da caixa de roda, faces de aro. */
        fun discX(x: Float, ly: Float, lz: Float, r: Float, c: Int, n: Float, half: Boolean = false, seg: Int = 14) {
            val tot = if (half) seg / 2 else seg
            for (i in 0 until tot) {
                val a0 = (if (half) 0f else 0f) + PI.toFloat() * (if (half) 1f else 2f) * i / tot
                val a1 = PI.toFloat() * (if (half) 1f else 2f) * (i + 1) / tot
                v(x, ly, lz, n, 0f, 0f, c)
                v(x, ly + r * sin(a0), lz + r * cos(a0), n, 0f, 0f, c)
                v(x, ly + r * sin(a1), lz + r * cos(a1), n, 0f, 0f, c)
            }
        }
    }

    // ------------------------------------------------------------ peças

    /**
     * Extrusão de um perfil lateral: [pr] = pares (z, y) da linha de cima, de trás para a frente; base em [yb]; meia largura [hw];
     * chanfro [bv] nas bordas de cima (dá o arredondado da lataria).
     */
    private fun extrude(f: XF, pr: FloatArray, yb: Float, hw: Float, bv: Float, c: Int) {
        val n = pr.size / 2
        val iw = hw - bv
        for (i in 0 until n - 1) {
            val z0 = pr[i * 2]; val y0 = pr[i * 2 + 1]; val z1 = pr[i * 2 + 2]; val y1 = pr[i * 2 + 3]
            // topo (entre os chanfros)
            f.quad(floatArrayOf(-iw, y0, z0), floatArrayOf(iw, y0, z0), floatArrayOf(iw, y1, z1), floatArrayOf(-iw, y1, z1), c)
            // chanfros e laterais
            for (s in floatArrayOf(-1f, 1f)) {
                val dz = z1 - z0; val dy = y1 - y0; val l = sqrt(dz * dz + dy * dy).coerceAtLeast(1e-5f)
                val ny = dz / l; val nzz = -dy / l   // normal do segmento no plano lateral
                val ox = bv * 0.7f
                val a = floatArrayOf(s * iw, y0, z0); val b = floatArrayOf(s * hw, y0 - ny * ox, z0 - nzz * ox)
                val cc = floatArrayOf(s * hw, y1 - ny * ox, z1 - nzz * ox); val d = floatArrayOf(s * iw, y1, z1)
                if (s > 0) f.quad(a, b, cc, d, c) else f.quad(b, a, d, cc, c)
                // lateral: do chanfro até a base
                val sa = floatArrayOf(s * hw, yb, z0); val sb = floatArrayOf(s * hw, yb, z1)
                if (s > 0) f.quad(sa, sb, cc, b, c) else f.quad(sb, sa, b, cc, c)
            }
        }
    }

    private fun wheel(f: XF, lx: Float, lz: Float, r: Float, w: Float, rim: Int, spokes: Int = 5) {
        val tire = C("#1B1B1B")
        f.cylX(lx, r, lz, r, w, tire, 12, C("#262626"))
        val s = if (lx > 0) 1f else -1f
        val face = lx + s * (w / 2 + 0.004f)
        f.discX(face, r, lz, r * 0.66f, rim, s, false, 12)
        f.discX(face + s * 0.004f, r, lz, r * 0.5f, shade(rim, -45), s, false, 10)
        for (k in 0 until spokes) {
            val a = 2f * PI.toFloat() * k / spokes
            val cy = r + sin(a) * r * 0.33f; val cz = lz + cos(a) * r * 0.33f
            f.box(face + s * 0.008f, cy, cz, 0.012f, if (abs(sin(a)) > 0.7f) r * 0.5f else 0.07f, if (abs(sin(a)) > 0.7f) 0.07f else r * 0.5f, rim)
        }
        f.discX(face + s * 0.012f, r, lz, r * 0.14f, shade(rim, 25), s, false, 8)
    }

    private fun arch(f: XF, hw: Float, lz: Float, r: Float) {
        for (s in floatArrayOf(-1f, 1f)) f.discX(s * (hw + 0.004f), r, lz, r * 1.22f, C("#111111"), s, true, 12)
    }

    private fun lightsAndTrim(f: XF, hw: Float, front: Float, rear: Float, yl: Float, body: Int, grille: Boolean = true) {
        val dark = C("#1E1E1E"); val chrome = C("#C9CED3")
        // faróis com moldura e luz diurna
        for (s in floatArrayOf(-1f, 1f)) {
            f.box(s * (hw - 0.27f), yl, front - 0.01f, 0.42f, 0.14f, 0.06f, C("#2A2F35"))
            f.box(s * (hw - 0.27f), yl, front + 0.015f, 0.38f, 0.1f, 0.02f, C("#F5FBFF"), false)
            f.box(s * (hw - 0.3f), yl - 0.09f, front + 0.012f, 0.3f, 0.025f, 0.02f, C("#E8F6FF"), false)
            f.box(s * (hw - 0.25f), yl + 0.02f, rear + 0.01f, 0.42f, 0.13f, 0.05f, C("#7A0E0E"))
            f.box(s * (hw - 0.25f), yl + 0.02f, rear - 0.015f, 0.38f, 0.09f, 0.02f, C("#E53935"), false)
            f.box(s * (hw - 0.45f), yl - 0.05f, rear - 0.016f, 0.1f, 0.05f, 0.02f, C("#FFA000"), false)
        }
        if (grille) {
            f.box(0f, yl - 0.02f, front, hw * 0.9f, 0.18f, 0.05f, dark)
            for (k in 0 until 4) f.box(0f, yl - 0.08f + k * 0.04f, front + 0.026f, hw * 0.86f, 0.01f, 0.01f, C("#3A3A3A"))
            f.box(0f, yl - 0.02f, front + 0.03f, 0.14f, 0.08f, 0.01f, chrome)
        }
        // para-choques
        f.box(0f, 0.38f, front + 0.04f, hw * 2 + 0.02f, 0.2f, 0.12f, shade(body, -18))
        f.box(0f, 0.3f, front + 0.06f, hw * 1.2f, 0.06f, 0.1f, dark)
        f.box(0f, 0.4f, rear - 0.04f, hw * 2 + 0.02f, 0.2f, 0.12f, shade(body, -18))
        // placas
        f.box(0f, 0.48f, front + 0.105f, 0.4f, 0.12f, 0.01f, C("#F4F4F4"))
        f.box(0f, 0.53f, front + 0.11f, 0.4f, 0.025f, 0.01f, C("#1565C0"))
        f.box(0f, 0.62f, rear - 0.105f, 0.4f, 0.12f, 0.01f, C("#F4F4F4"))
        f.box(0f, 0.67f, rear - 0.11f, 0.4f, 0.025f, 0.01f, C("#1565C0"))
        // escapamento
        f.box(hw * 0.5f, 0.24f, rear - 0.05f, 0.08f, 0.08f, 0.2f, C("#5A5A5A"))
    }

    private fun sideDetails(f: XF, hw: Float, z0: Float, z1: Float, ylow: Float, yhigh: Float, doorsZ: FloatArray) {
        val line = C("#141414"); val chrome = C("#C9CED3")
        for (s in floatArrayOf(-1f, 1f)) {
            val x = s * (hw + 0.003f)
            for (dz in doorsZ) f.box(x, (ylow + yhigh) / 2, dz, 0.006f, yhigh - ylow, 0.012f, line)
            f.box(x, ylow, (z0 + z1) / 2, 0.006f, 0.012f, z1 - z0, line)
            for (k in 0 until doorsZ.size - 1) f.box(s * (hw + 0.01f), yhigh - 0.12f, doorsZ[k + 1] - 0.25f, 0.02f, 0.035f, 0.14f, chrome)
            f.box(s * (hw + 0.004f), 0.36f, (z0 + z1) / 2, 0.01f, 0.08f, (z1 - z0) - 1.6f, C("#2A2A2A"))   // saia lateral
        }
    }

    private fun mirrors(f: XF, hw: Float, z: Float, y: Float, body: Int) {
        for (s in floatArrayOf(-1f, 1f)) {
            f.box(s * (hw + 0.1f), y, z, 0.18f, 0.12f, 0.09f, body)
            f.box(s * (hw + 0.19f), y, z - 0.03f, 0.01f, 0.1f, 0.06f, C("#B0C4D0"))
        }
    }

    // ------------------------------------------------------------ montagem por tipo

    fun geom(f: XF, kind: Int, col0: Int) {
        val b = f.b
        val glass = C("#1C2733")
        val rimS = C("#C0C6CC"); val rimD = C("#3A3D42")
        when (kind) {
            SEDAN, TAXI, POLICE -> {
                val col = if (kind == TAXI) C("#F9C80E") else if (kind == POLICE) C("#F5F5F5") else col0
                val hw = 0.9f; val L2 = 2.3f
                b.m(Mt.METAL, 1f)
                extrude(f, floatArrayOf(-L2, 0.42f, -L2, 0.78f, -2.05f, 0.93f, -1.35f, 0.98f, 0.95f, 0.98f, 1.75f, 0.86f, L2, 0.72f, L2, 0.42f), 0.3f, hw, 0.12f, col)
                extrude(f, floatArrayOf(-1.4f, 0.97f, -0.75f, 1.42f, 0.35f, 1.45f, 1.0f, 0.97f), 0.95f, hw - 0.1f, 0.08f, glass)
                extrude(f, floatArrayOf(-0.7f, 1.435f, 0.3f, 1.465f), 1.42f, hw - 0.12f, 0.05f, if (kind == POLICE) C("#101820") else col)
                f.box(0f, 1.18f, -0.18f, (hw - 0.1f) * 2 + 0.02f, 0.5f, 0.1f, if (kind == POLICE) C("#101820") else col)   // coluna B
                if (kind == POLICE) {   // portas pretas e giroflex
                    b.m(Mt.METAL, 1f)
                    for (s in floatArrayOf(-1f, 1f)) f.box(s * (hw + 0.003f), 0.66f, 0.1f, 0.006f, 0.55f, 2.2f, C("#101820"))
                    b.m(Mt.PLAIN)
                    f.box(-0.3f, 1.53f, -0.15f, 0.5f, 0.12f, 0.24f, C("#E53935"), false); f.box(0.3f, 1.53f, -0.15f, 0.5f, 0.12f, 0.24f, C("#1E88E5"), false)
                    f.box(0f, 1.49f, -0.15f, 1.15f, 0.04f, 0.28f, C("#222222"))
                }
                if (kind == TAXI) { b.m(Mt.PLAIN); f.box(0f, 1.55f, -0.2f, 0.62f, 0.18f, 0.22f, C("#212121")); f.box(0f, 1.55f, -0.2f, 0.56f, 0.12f, 0.24f, C("#FFF59D"), false); for (s in floatArrayOf(-1f, 1f)) f.box(s * (hw + 0.004f), 0.62f, 0f, 0.005f, 0.1f, 3.2f, C("#111111")) }
                b.m(Mt.METAL, 1f)
                arch(f, hw, -1.45f, 0.34f); arch(f, hw, 1.45f, 0.34f)
                for (s in floatArrayOf(-1f, 1f)) { wheel(f, s * (hw - 0.08f), -1.45f, 0.34f, 0.24f, if (kind == SEDAN) rimS else rimD); wheel(f, s * (hw - 0.08f), 1.45f, 0.34f, 0.24f, if (kind == SEDAN) rimS else rimD) }
                lightsAndTrim(f, hw, L2, -L2, 0.66f, col)
                sideDetails(f, hw, -2.0f, 1.9f, 0.45f, 0.97f, floatArrayOf(-1.3f, -0.18f, 1.0f))
                mirrors(f, hw, 0.95f, 1.03f, col)
            }
            HATCH -> {
                val hw = 0.86f; val L2 = 1.95f
                b.m(Mt.METAL, 1f)
                extrude(f, floatArrayOf(-L2, 0.42f, -L2, 0.95f, -1.75f, 1.0f, 0.75f, 0.98f, 1.5f, 0.85f, L2, 0.7f, L2, 0.42f), 0.3f, hw, 0.12f, col0)
                extrude(f, floatArrayOf(-1.8f, 0.99f, -1.6f, 1.48f, 0.15f, 1.5f, 0.8f, 0.97f), 0.95f, hw - 0.1f, 0.08f, glass)
                extrude(f, floatArrayOf(-1.55f, 1.49f, 0.1f, 1.515f), 1.47f, hw - 0.12f, 0.05f, col0)
                f.box(0f, 1.2f, -0.45f, (hw - 0.1f) * 2 + 0.02f, 0.5f, 0.1f, col0)
                f.box(0f, 1.22f, -1.62f, (hw - 0.1f) * 2 + 0.02f, 0.5f, 0.06f, col0)
                f.box(0f, 1.52f, -1.62f, 1.0f, 0.06f, 0.18f, C("#151515"))   // aerofólio
                arch(f, hw, -1.25f, 0.32f); arch(f, hw, 1.25f, 0.32f)
                for (s in floatArrayOf(-1f, 1f)) { wheel(f, s * (hw - 0.08f), -1.25f, 0.32f, 0.22f, rimS); wheel(f, s * (hw - 0.08f), 1.25f, 0.32f, 0.22f, rimS) }
                lightsAndTrim(f, hw, L2, -L2, 0.68f, col0)
                sideDetails(f, hw, -1.7f, 1.6f, 0.45f, 0.97f, floatArrayOf(-0.45f, 0.8f))
                mirrors(f, hw, 0.75f, 1.05f, col0)
            }
            SUV -> {
                val hw = 0.97f; val L2 = 2.35f
                b.m(Mt.METAL, 1f)
                extrude(f, floatArrayOf(-L2, 0.55f, -L2, 1.12f, -2.15f, 1.18f, 0.95f, 1.18f, 1.85f, 1.05f, L2, 0.92f, L2, 0.55f), 0.42f, hw, 0.13f, col0)
                extrude(f, floatArrayOf(-2.15f, 1.17f, -2.0f, 1.78f, 0.45f, 1.8f, 1.0f, 1.17f), 1.15f, hw - 0.1f, 0.08f, glass)
                extrude(f, floatArrayOf(-1.98f, 1.79f, 0.4f, 1.815f), 1.77f, hw - 0.1f, 0.05f, col0)
                f.box(0f, 1.45f, -0.6f, (hw - 0.1f) * 2 + 0.02f, 0.6f, 0.1f, col0); f.box(0f, 1.45f, -2.0f, (hw - 0.1f) * 2 + 0.02f, 0.6f, 0.08f, col0)
                for (s in floatArrayOf(-0.55f, 0.55f)) f.box(s, 1.86f, -0.8f, 0.05f, 0.06f, 2.2f, C("#2B2B2B"))   // rack
                b.m(Mt.METAL, 1f)
                f.box(0f, 0.75f, -L2 - 0.12f, 0.36f, 0.36f, 0.14f, C("#1E1E1E")); f.cylX(0f, 0.75f, -L2 - 0.2f, 0.3f, 0.2f, C("#1B1B1B"), 14)   // estepe
                arch(f, hw, -1.5f, 0.4f); arch(f, hw, 1.5f, 0.4f)
                for (s in floatArrayOf(-1f, 1f)) { wheel(f, s * (hw - 0.06f), -1.5f, 0.4f, 0.28f, rimD, 6); wheel(f, s * (hw - 0.06f), 1.5f, 0.4f, 0.28f, rimD, 6) }
                lightsAndTrim(f, hw, L2, -L2, 0.86f, col0)
                sideDetails(f, hw, -2.1f, 2.0f, 0.55f, 1.17f, floatArrayOf(-1.35f, -0.6f, 0.95f))
                mirrors(f, hw, 0.95f, 1.25f, col0)
            }
            PICKUP -> {
                val hw = 0.98f; val L2 = 2.6f
                b.m(Mt.METAL, 1f)
                extrude(f, floatArrayOf(-L2, 0.55f, -L2, 1.1f, 0.0f, 1.1f, 1.0f, 1.12f, 2.0f, 1.0f, L2, 0.9f, L2, 0.55f), 0.42f, hw, 0.12f, col0)
                extrude(f, floatArrayOf(-0.6f, 1.11f, -0.5f, 1.75f, 0.55f, 1.76f, 1.05f, 1.11f), 1.09f, hw - 0.1f, 0.08f, glass)
                extrude(f, floatArrayOf(-0.5f, 1.745f, 0.5f, 1.77f), 1.72f, hw - 0.1f, 0.05f, col0)
                f.box(0f, 1.43f, -0.58f, (hw - 0.1f) * 2, 0.64f, 0.08f, col0)
                // caçamba
                f.box(0f, 1.11f, -1.35f, hw * 2 - 0.25f, 0.02f, 2.3f, C("#1E1E1E"))
                for (s in floatArrayOf(-1f, 1f)) f.box(s * (hw - 0.06f), 1.2f, -1.35f, 0.1f, 0.2f, 2.4f, col0)
                f.box(0f, 1.2f, -L2 + 0.05f, hw * 2, 0.2f, 0.1f, col0)
                arch(f, hw, -1.7f, 0.42f); arch(f, hw, 1.65f, 0.42f)
                for (s in floatArrayOf(-1f, 1f)) { wheel(f, s * (hw - 0.06f), -1.7f, 0.42f, 0.3f, rimS, 6); wheel(f, s * (hw - 0.06f), 1.65f, 0.42f, 0.3f, rimS, 6) }
                lightsAndTrim(f, hw, L2, -L2, 0.85f, col0)
                sideDetails(f, hw, -0.6f, 2.3f, 0.6f, 1.1f, floatArrayOf(-0.55f, 0.3f, 1.05f))
                mirrors(f, hw, 1.0f, 1.25f, col0)
            }
            SPORT -> {
                val hw = 0.96f; val L2 = 2.25f
                b.m(Mt.METAL, 1f)
                extrude(f, floatArrayOf(-L2, 0.36f, -L2, 0.72f, -1.9f, 0.82f, -1.0f, 0.86f, 0.6f, 0.82f, 1.6f, 0.66f, L2, 0.5f, L2, 0.32f), 0.22f, hw, 0.14f, col0)
                extrude(f, floatArrayOf(-1.15f, 0.85f, -0.5f, 1.18f, 0.15f, 1.2f, 0.85f, 0.83f), 0.8f, hw - 0.14f, 0.1f, glass)
                extrude(f, floatArrayOf(-0.45f, 1.19f, 0.1f, 1.21f), 1.17f, hw - 0.16f, 0.05f, col0)
                f.box(0f, 0.95f, -L2 + 0.25f, 1.6f, 0.05f, 0.35f, C("#151515"))   // aerofólio
                for (s in floatArrayOf(-0.6f, 0.6f)) f.box(s, 0.86f, -L2 + 0.3f, 0.05f, 0.14f, 0.08f, C("#151515"))
                for (s in floatArrayOf(-1f, 1f)) f.box(s * (hw + 0.003f), 0.62f, -0.4f, 0.006f, 0.16f, 0.6f, C("#111111"))   // entrada de ar
                arch(f, hw, -1.4f, 0.34f); arch(f, hw, 1.4f, 0.33f)
                for (s in floatArrayOf(-1f, 1f)) { wheel(f, s * (hw - 0.06f), -1.4f, 0.34f, 0.3f, rimD, 10); wheel(f, s * (hw - 0.06f), 1.4f, 0.33f, 0.26f, rimD, 10) }
                lightsAndTrim(f, hw, L2, -L2, 0.5f, col0, false)
                f.box(0f, 0.3f, L2 + 0.02f, hw * 1.6f, 0.12f, 0.08f, C("#151515"))
                sideDetails(f, hw, -1.6f, 1.4f, 0.3f, 0.84f, floatArrayOf(-0.6f, 0.8f))
                mirrors(f, hw - 0.04f, 0.6f, 0.92f, col0)
            }
            VAN, AMBULANCE -> {
                val col = if (kind == AMBULANCE) C("#FAFAFA") else col0
                val hw = 1.0f; val L2 = 2.65f
                b.m(Mt.METAL, 1f)
                extrude(f, floatArrayOf(-L2, 0.5f, -L2, 2.3f, -2.5f, 2.45f, 1.0f, 2.45f, 1.55f, 1.3f, 2.4f, 1.05f, L2, 0.9f, L2, 0.5f), 0.38f, hw, 0.12f, col)
                extrude(f, floatArrayOf(1.1f, 2.2f, 1.58f, 1.28f), 1.2f, hw - 0.04f, 0.06f, glass)   // para-brisa
                for (s in floatArrayOf(-1f, 1f)) {
                    f.box(s * (hw + 0.005f), 1.75f, 0.75f, 0.01f, 0.6f, 0.75f, glass)
                    if (kind == VAN) f.box(s * (hw + 0.005f), 1.75f, -0.8f, 0.01f, 0.55f, 2.2f, glass)
                }
                if (kind == AMBULANCE) {
                    b.m(Mt.PLAIN)
                    for (s in floatArrayOf(-1f, 1f)) {
                        f.box(s * (hw + 0.006f), 1.15f, -0.4f, 0.01f, 0.22f, 4.2f, C("#D62828"))
                        f.box(s * (hw + 0.008f), 1.75f, -1.2f, 0.01f, 0.7f, 0.22f, C("#D62828")); f.box(s * (hw + 0.008f), 1.75f, -1.2f, 0.01f, 0.22f, 0.7f, C("#D62828"))
                    }
                    f.box(-0.4f, 2.52f, 0.9f, 0.5f, 0.14f, 0.3f, C("#E53935"), false); f.box(0.4f, 2.52f, 0.9f, 0.5f, 0.14f, 0.3f, C("#E53935"), false)
                    f.box(0f, 2.5f, -L2 + 0.2f, 0.4f, 0.12f, 0.12f, C("#1E88E5"), false)
                }
                b.m(Mt.METAL, 1f)
                arch(f, hw, -1.75f, 0.38f); arch(f, hw, 1.7f, 0.38f)
                for (s in floatArrayOf(-1f, 1f)) { wheel(f, s * (hw - 0.06f), -1.75f, 0.38f, 0.26f, rimS); wheel(f, s * (hw - 0.06f), 1.7f, 0.38f, 0.26f, rimS) }
                lightsAndTrim(f, hw, L2, -L2, 0.85f, col)
                sideDetails(f, hw, -2.5f, 2.3f, 0.55f, 2.2f, floatArrayOf(-2.4f, 0.4f, 1.1f))
                mirrors(f, hw, 1.2f, 1.5f, col)
            }
            BUS, FIRE -> {
                val col = if (kind == FIRE) C("#C62828") else if (col0 == C("#FFFFFF")) C("#F2C230") else C("#1976D2")
                val hw = 1.27f; val L2 = if (kind == FIRE) 3.6f else 5.6f
                b.m(Mt.METAL, 1f)
                extrude(f, floatArrayOf(-L2, 0.45f, -L2, 3.0f, -L2 + 0.2f, 3.15f, L2 - 0.3f, 3.15f, L2, 2.9f, L2, 0.45f), 0.35f, hw, 0.14f, col)
                if (kind == BUS) {
                    for (s in floatArrayOf(-1f, 1f)) {
                        f.box(s * (hw + 0.005f), 2.1f, -0.2f, 0.01f, 1.0f, 9.6f, glass)
                        var z = -L2 + 0.9f
                        while (z < L2 - 0.6f) { f.box(s * (hw + 0.008f), 2.1f, z, 0.01f, 1.0f, 0.08f, col); z += 1.3f }
                        f.box(s * (hw + 0.006f), 1.2f, 0f, 0.01f, 0.12f, 10.6f, C("#FFFFFF"))
                    }
                    f.box(0f, 1.95f, L2 + 0.005f, hw * 2 - 0.15f, 1.6f, 0.01f, glass)
                    f.box(0f, 2.85f, L2 + 0.01f, 1.4f, 0.22f, 0.01f, C("#111111"))
                    b.m(Mt.PLAIN); f.box(0f, 2.85f, L2 + 0.015f, 1.3f, 0.14f, 0.01f, C("#FF9800"), false); b.m(Mt.METAL, 1f)
                    f.box(hw + 0.006f, 1.3f, L2 - 1.0f, 0.01f, 2.1f, 1.0f, glass)   // porta
                } else {
                    f.box(0f, 2.0f, L2 + 0.005f, hw * 2 - 0.2f, 0.9f, 0.01f, glass)
                    for (s in floatArrayOf(-1f, 1f)) { f.box(s * (hw + 0.005f), 2.0f, L2 - 0.7f, 0.01f, 0.8f, 0.9f, glass); f.box(s * (hw + 0.006f), 1.2f, -1f, 0.01f, 1.6f, 4.0f, C("#B0BEC5")) }
                    f.box(0f, 3.35f, -0.8f, 0.5f, 0.3f, 5.5f, C("#9E9E9E"))   // escada
                    for (k in 0 until 8) f.box(0f, 3.52f, -3.2f + k * 0.65f, 0.6f, 0.05f, 0.06f, C("#BDBDBD"))
                    b.m(Mt.PLAIN); f.box(-0.4f, 3.25f, L2 - 0.5f, 0.6f, 0.15f, 0.3f, C("#E53935"), false); f.box(0.4f, 3.25f, L2 - 0.5f, 0.6f, 0.15f, 0.3f, C("#E53935"), false); b.m(Mt.METAL, 1f)
                }
                val wz = if (kind == FIRE) floatArrayOf(-2.3f, 2.3f) else floatArrayOf(-3.6f, 3.6f)
                for (z in wz) { arch(f, hw, z, 0.5f); for (s in floatArrayOf(-1f, 1f)) wheel(f, s * (hw - 0.1f), z, 0.5f, 0.32f, rimS, 8) }
                lightsAndTrim(f, hw, L2, -L2, 0.8f, col)
                mirrors(f, hw, L2 - 0.3f, 2.4f, C("#212121"))
            }
            MOTO, SCOOTER -> moto(f, kind, col0)
        }
    }

    private fun moto(f: XF, kind: Int, col: Int) {
        val b = f.b
        val dark = C("#1A1A1A"); val chrome = C("#C9CED3")
        b.m(Mt.METAL, 1f)
        val r = if (kind == MOTO) 0.32f else 0.24f
        val wb = if (kind == MOTO) 0.72f else 0.6f
        // rodas finas com aro
        for (z in floatArrayOf(-wb, wb)) {
            f.cylX(0f, r, z, r, 0.14f, dark, 16, C("#2A2A2A"))
            for (s in floatArrayOf(-1f, 1f)) { f.discX(s * 0.074f, r, z, r * 0.7f, chrome, s, false, 12); f.discX(s * 0.078f, r, z, r * 0.2f, C("#555555"), s, false, 6) }
        }
        if (kind == MOTO) {
            f.box(0f, 0.62f, 0f, 0.24f, 0.22f, 0.9f, C("#333333"))       // motor/quadro
            f.box(0f, 0.86f, 0.12f, 0.36f, 0.24f, 0.55f, col)            // tanque
            f.box(0f, 0.86f, -0.4f, 0.3f, 0.1f, 0.55f, dark)             // banco
            f.box(0f, 0.92f, -0.72f, 0.24f, 0.14f, 0.3f, col)            // rabeta
            f.box(0f, 0.95f, 0.6f, 0.42f, 0.4f, 0.28f, col)              // carenagem
            f.box(0f, 1.18f, 0.66f, 0.3f, 0.18f, 0.03f, C("#405060"))    // bolha
            b.m(Mt.PLAIN); f.box(0f, 0.95f, 0.75f, 0.16f, 0.1f, 0.03f, C("#F5FBFF"), false); f.box(0f, 0.92f, -0.875f, 0.14f, 0.05f, 0.02f, C("#E53935"), false); b.m(Mt.METAL, 1f)
            f.box(0.16f, 0.45f, -0.45f, 0.08f, 0.08f, 0.6f, chrome)      // escapamento
            f.box(0f, 0.7f, 0.66f, 0.06f, 0.6f, 0.06f, chrome)           // garfo
            f.box(0f, 1.05f, 0.5f, 0.7f, 0.04f, 0.04f, dark)             // guidão
        } else {
            f.box(0f, 0.36f, 0f, 0.36f, 0.12f, 0.8f, col)                // assoalho
            f.box(0f, 0.62f, -0.3f, 0.42f, 0.42f, 0.6f, col)             // carenagem traseira
            f.box(0f, 0.88f, -0.32f, 0.32f, 0.1f, 0.6f, dark)            // banco
            f.box(0f, 0.78f, 0.5f, 0.34f, 0.8f, 0.14f, col)              // escudo frontal
            f.box(0f, 1.18f, 0.48f, 0.6f, 0.05f, 0.05f, dark)
            b.m(Mt.PLAIN); f.box(0f, 1.15f, 0.56f, 0.18f, 0.1f, 0.03f, C("#F5FBFF"), false); f.box(0f, 0.7f, -0.61f, 0.16f, 0.06f, 0.02f, C("#E53935"), false); b.m(Mt.METAL, 1f)
            f.box(0f, 0.6f, -0.95f + 0.25f, 0.4f, 0.32f, 0.36f, C("#B71C1C"))   // baú de entrega
        }
        // piloto: jaqueta, calça, botas, luvas, capacete com viseira
        val jacket = if (kind == MOTO) C("#263238") else C("#E65100")
        b.m(Mt.FABRIC, 1f)
        val lean = if (kind == MOTO) 0.18f else 0.04f
        f.box(0f, 1.2f, -0.28f + lean, 0.4f, 0.55f, 0.26f, jacket)
        for (s in floatArrayOf(-1f, 1f)) {
            f.box(s * 0.16f, 0.92f, -0.15f, 0.15f, 0.15f, 0.45f, C("#1F2A44"))           // coxa
            f.box(s * 0.19f, 0.6f, 0.08f, 0.13f, 0.5f, 0.14f, C("#1F2A44"))              // canela
            f.box(s * 0.19f, 0.36f, 0.12f, 0.13f, 0.1f, 0.24f, dark)                     // bota
            f.box(s * 0.25f, 1.18f, 0.12f + lean, 0.11f, 0.11f, 0.5f, jacket)              // braço
            f.box(s * 0.3f, 1.08f, 0.45f, 0.1f, 0.08f, 0.1f, dark)                        // luva
        }
        b.m(Mt.METAL, 1f)
        CityGeo.ball(b, f.px(0f, -0.2f + lean), f.oy + 1.62f, f.pz(0f, -0.2f + lean), 0.17f, if (kind == MOTO) col else C("#FAFAFA"), 0.17f, 10)
        f.box(0f, 1.62f, -0.06f + lean, 0.22f, 0.09f, 0.04f, C("#111111"))
    }
}
