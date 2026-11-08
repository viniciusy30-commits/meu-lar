package com.vinicius.meular

import android.opengl.Matrix
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Etapa 122: praia (calçadão de ondas, areia, quiosques, guarda-sóis, salva-vidas, vôlei, píer) e
 * parque de diversões (roda-gigante, montanha-russa, carrossel, elevador, bate-bate, barracas de comida).
 * Brinquedos se mexem: [dyn] tem malha + matriz, atualizadas em [update] e desenhadas pelo renderizador.
 */
object CityFun {
    class Dyn(val mesh: Mesh, val x: Float, val z: Float) { val m = FloatArray(16) }
    val dyn = ArrayList<Dyn>()
    private val own = ArrayList<Mesh>()

    // parque: posição no mundo
    private var px0 = 0f; private var pz0 = 0f; private var px1 = 0f; private var pz1 = 0f
    private var built = false

    fun release() { own.forEach { it.release() }; own.clear(); dyn.clear(); built = false; coaster = FloatArray(0) }

    private val CURB = City.CURB

    // ============================================================ praia

    fun sandH(z: Float): Float {
        val t = ((z - City.BEACH_Z) / (City.SEA_Z - City.BEACH_Z)).coerceIn(0f, 1.4f)
        return if (t <= 1f) 0.14f * (1f - t) - 0.03f else -0.03f - 1.6f * (t - 1f)
    }

    fun beach(idx: Int): City.Chunk {
        val X0 = City.X0; val X1 = City.X1; val Z1 = City.Z1; val BZ = City.BEACH_Z; val SZ = City.SEA_Z
        val g = CityGeo.Gen(idx, City.Rng(555), X0 - 60f, Z1, X1 + 60f, SZ + 70f)
        val b = g.b
        // calçadão com ondas pretas e brancas
        CityGeo.groundBox(b, X0 - 60f, Z1, X1 + 60f, BZ, Mt.STONE, 1.2f, C("#F4F1EA"))
        CityGeo.groundBox(g.f, X0 - 60f, Z1, X1 + 60f, BZ, Mt.STONE, 1.2f, C("#F4F1EA"))
        b.m(Mt.PLAIN)
        val black = C("#2B2B2B")
        for (band in 0 until 3) {
            val zc = Z1 + 2.2f + band * 2.6f
            var x = X0 - 60f
            val st = 0.5f
            while (x < X1 + 60f) {
                val z0 = zc + 0.8f * sin(x * 0.75f); val z1 = zc + 0.8f * sin((x + st) * 0.75f)
                CityGeo.q(b, CityGeo.P(x, CURB + 0.006f, z0 - 0.35f) + CityGeo.P(x + st, CURB + 0.006f, z1 - 0.35f) + CityGeo.P(x + st, CURB + 0.006f, z1 + 0.35f) + CityGeo.P(x, CURB + 0.006f, z0 + 0.35f), black)
                x += st
            }
        }
        // mureta e escadas para a areia
        b.m(Mt.STONE, 0.8f)
        for (iv in stairsGaps()) b.box((iv[0] + iv[1]) / 2, CURB + 0.25f, BZ - 0.15f, iv[1] - iv[0], 0.5f, 0.3f, C("#D8D2C4"))
        for (iv in stairsGaps()) g.solid(iv[0], BZ - 0.3f, iv[1], BZ)
        // areia em degradê (seca -> molhada), afundando até o mar
        val n = 12
        for (k in 0 until n) {
            val za = BZ + (SZ + 14f - BZ) * k / n; val zb = BZ + (SZ + 14f - BZ) * (k + 1) / n
            val ya = sandH(za); val yb = sandH(zb)
            val ca = mix(C("#EED9A8"), C("#C9B07D"), ((za - BZ) / (SZ - BZ)).coerceIn(0f, 1f) * 0.9f)
            for (bb in arrayOf(b, g.f)) {
                bb.m(Mt.PLASTER, 0.7f)
                CityGeo.q(bb, CityGeo.P(X0 - 60f, ya, za) + CityGeo.P(X0 - 60f, yb, zb) + CityGeo.P(X1 + 60f, yb, zb) + CityGeo.P(X1 + 60f, ya, za), ca)
            }
        }
        // palmeiras, postes, bancos e quiosques no calçadão
        val rng = g.rng
        var x = X0 - 50f; var k = 0
        while (x < X1 + 50f) {
            if (abs(x - City.PIER_X) > 6f) {
                if (k % 2 == 0) CityGeo.palm(g, x, Z1 + 8.5f, rng.r(0.85f, 1.1f)) else CityGeo.streetLamp(b, x, Z1 + 8.6f, 0f, 0f)
                if (k % 3 == 1) CityGeo.publicBench(b, x + 3f, Z1 + 7.8f, 0f, 1f)
            }
            x += 9f; k++
        }
        x = X0 + 20f
        while (x < X1 - 10f) { if (abs(x - City.PIER_X) > 14f) kiosk(g, x, BZ + 5f); x += rng.r(55f, 75f) }
        // guarda-sóis, cadeiras, toalhas
        val pal = arrayOf(C("#E53935"), C("#1E88E5"), C("#FDD835"), C("#43A047"), C("#FB8C00"), C("#8E24AA"), C("#FFFFFF"), C("#00ACC1"))
        for (i in 0 until 70) {
            val ux = rng.r(X0 - 40f, X1 + 40f); val uz = rng.r(BZ + 9f, SZ - 8f)
            if (abs(ux - City.PIER_X) < 6f) continue
            umbrella(b, ux, uz, rng.pick(pal), rng)
        }
        // salva-vidas, vôlei, futevôlei, pranchas
        for (lx in floatArrayOf(X0 + 60f, City.PIER_X + 70f, X1 - 50f)) lifeguard(g, lx, SZ - 10f)
        volleyNet(g, City.PIER_X - 40f, BZ + 18f)
        volleyNet(g, X0 + 120f, BZ + 20f)
        for (i in 0 until 6) { val sx = rng.r(X0, X1); b.m(Mt.PLAIN); b.box(sx, sandH(SZ - 14f) + 1.0f, SZ - 14f, 0.55f, 2.0f, 0.08f, rng.pick(pal)) }
        // píer
        pier(g)
        g.place(City.Place("Quiosques", City.PIER_X + 40f, BZ + 5f, 0xFF00838F.toInt(), 'Q'))
        return g.finish(12f)
    }

    private fun stairsGaps(): List<FloatArray> {
        val out = ArrayList<FloatArray>()
        var x = City.X0 - 60f
        while (x < City.X1 + 60f) { val e = min(City.X1 + 60f, x + 36f); out.add(floatArrayOf(x, e - 4f)); x = e }
        return out
    }

    private fun kiosk(g: CityGeo.Gen, x: Float, z: Float) {
        val b = g.b; val y = sandH(z)
        b.m(Mt.WOOD, 1f)
        b.box(x, y + 0.1f, z, 7f, 0.2f, 7f, C("#B48A60"))
        b.m(Mt.PLASTER, 0.5f)
        b.box(x, y + 1.3f, z + 1.2f, 3.2f, 2.4f, 2.4f, C("#FAFAFA"))
        b.m(Mt.WOOD, 1f)
        b.box(x, y + 1.15f, z - 0.15f, 3.4f, 0.1f, 0.5f, C("#8D6E63"))
        for (s in floatArrayOf(-1.4f, 0f, 1.4f)) { b.cyl(x + s, y + 0.2f, z - 0.7f, 0.15f, 0.15f, 0.04f, C("#5D4037"), true, 8); b.cyl(x + s, y + 0.2f, z - 0.7f, 0.03f, 0.03f, 0.75f, C("#5D4037"), true, 5); b.cyl(x + s, y + 0.95f, z - 0.7f, 0.2f, 0.2f, 0.05f, C("#8D6E63"), true, 10) }
        b.m(Mt.ROOF, 0.6f)
        CityGeo.q(b, CityGeo.P(x - 3.6f, y + 2.8f, z - 1.6f) + CityGeo.P(x + 3.6f, y + 2.8f, z - 1.6f) + CityGeo.P(x + 2f, y + 4.0f, z + 1.2f) + CityGeo.P(x - 2f, y + 4.0f, z + 1.2f), C("#C9A15B"))
        CityGeo.q(b, CityGeo.P(x + 3.6f, y + 2.8f, z + 4f) + CityGeo.P(x - 3.6f, y + 2.8f, z + 4f) + CityGeo.P(x - 2f, y + 4.0f, z + 1.2f) + CityGeo.P(x + 2f, y + 4.0f, z + 1.2f), C("#B88F4A"))
        CityGeo.q(b, CityGeo.P(x - 3.6f, y + 2.8f, z + 4f) + CityGeo.P(x - 3.6f, y + 2.8f, z - 1.6f) + CityGeo.P(x - 2f, y + 4.0f, z + 1.2f) + CityGeo.P(x - 2f, y + 4.0f, z + 1.2f), C("#C9A15B"))
        CityGeo.q(b, CityGeo.P(x + 3.6f, y + 2.8f, z - 1.6f) + CityGeo.P(x + 3.6f, y + 2.8f, z + 4f) + CityGeo.P(x + 2f, y + 4.0f, z + 1.2f) + CityGeo.P(x + 2f, y + 4.0f, z + 1.2f), C("#B88F4A"))
        b.m(Mt.WOOD, 1f)
        for (cx in floatArrayOf(-3.2f, 3.2f)) for (cz in floatArrayOf(-1.3f, 3.7f)) b.cyl(x + cx, y + 0.2f, z + cz, 0.1f, 0.1f, 2.65f, C("#6D4C41"), true, 6)
        CityGeo.sign(b, x, y + 2.45f, z - 1.62f, 0f, -1f, 2.6f, 0.4f, City.signIdx("QUIOSQUE"))
        for (t in 0 until 3) {
            val tx = x - 2.4f + t * 2.4f; val tz = z - 4f
            CityGeo.cafeTableOut(b, tx, tz, if (t % 2 == 0) C("#E53935") else C("#FDD835"))
        }
        g.solid(x - 1.7f, z, x + 1.7f, z + 2.5f)
    }

    private fun umbrella(b: MB, x: Float, z: Float, c: Int, rng: City.Rng) {
        val y = sandH(z)
        b.m(Mt.METAL, 1f)
        b.cyl(x, y, z, 0.025f, 0.025f, 2.2f, C("#E0E0E0"), true, 5)
        b.m(Mt.FABRIC, 1f)
        val seg = 8
        for (i in 0 until seg) {
            val a0 = 2f * PI.toFloat() * i / seg; val a1 = 2f * PI.toFloat() * (i + 1) / seg
            CityGeo.tri(b, CityGeo.P(x, y + 2.35f, z) + CityGeo.P(x + 1.15f * cos(a0), y + 1.85f, z + 1.15f * sin(a0)) + CityGeo.P(x + 1.15f * cos(a1), y + 1.85f, z + 1.15f * sin(a1)), if (i % 2 == 0) c else C("#FFFFFF"))
        }
        // cadeiras de praia e toalha
        for (s in floatArrayOf(-0.6f, 0.6f)) {
            b.m(Mt.FABRIC, 1f)
            CityGeo.q(b, CityGeo.P(x + s - 0.25f, y + 0.25f, z + 0.3f) + CityGeo.P(x + s + 0.25f, y + 0.25f, z + 0.3f) + CityGeo.P(x + s + 0.25f, y + 0.75f, z + 0.85f) + CityGeo.P(x + s - 0.25f, y + 0.75f, z + 0.85f), shade(c, -10))
            CityGeo.q(b, CityGeo.P(x + s - 0.25f, y + 0.25f, z + 0.3f) + CityGeo.P(x + s + 0.25f, y + 0.25f, z + 0.3f) + CityGeo.P(x + s + 0.25f, y + 0.3f, z - 0.3f) + CityGeo.P(x + s - 0.25f, y + 0.3f, z - 0.3f), shade(c, -10))
        }
        if (rng.chance(0.6f)) { b.m(Mt.FABRIC, 1f); b.box(x + 1.3f, y + 0.01f, z - 0.4f, 0.9f, 0.015f, 1.8f, rng.pick(arrayOf(C("#F06292"), C("#4FC3F7"), C("#AED581"), C("#FFD54F")))) }
        if (rng.chance(0.3f)) { b.m(Mt.PLAIN); b.box(x - 1.2f, y + 0.2f, z - 0.2f, 0.5f, 0.4f, 0.35f, C("#1565C0")); b.box(x - 1.2f, y + 0.41f, z - 0.2f, 0.52f, 0.04f, 0.37f, C("#FFFFFF")) }   // caixa térmica
    }

    private fun lifeguard(g: CityGeo.Gen, x: Float, z: Float) {
        val b = g.b; val y = sandH(z)
        b.m(Mt.WOOD, 1f)
        for (cx in floatArrayOf(-0.9f, 0.9f)) for (cz in floatArrayOf(-0.9f, 0.9f)) b.box(x + cx, y + 1.3f, z + cz, 0.14f, 2.6f, 0.14f, C("#FAFAFA"))
        b.box(x, y + 2.6f, z, 2.2f, 0.12f, 2.2f, C("#FAFAFA"))
        b.m(Mt.PLASTER, 0.5f)
        b.box(x, y + 3.5f, z, 2.0f, 1.7f, 2.0f, C("#E53935"))
        b.m(Mt.METAL, 1f); b.box(x, y + 3.6f, z + 1.0f, 1.6f, 0.7f, 0.03f, C("#2E3A46"))
        b.m(Mt.ROOF, 0.6f); b.box(x, y + 4.45f, z, 2.5f, 0.15f, 2.5f, C("#FDD835"))
        b.m(Mt.WOOD, 1f)
        CityGeo.q(b, CityGeo.P(x - 0.4f, y, z - 2.6f) + CityGeo.P(x + 0.4f, y, z - 2.6f) + CityGeo.P(x + 0.4f, y + 2.6f, z - 1.1f) + CityGeo.P(x - 0.4f, y + 2.6f, z - 1.1f), C("#D7CCC8"))
        CityGeo.sign(b, x, y + 4.0f, z - 1.02f, 0f, -1f, 1.8f, 0.3f, City.signIdx("SALVA-VIDAS"))
        b.m(Mt.FABRIC, 1f); b.box(x + 1.5f, y + 4.8f, z, 0.6f, 0.4f, 0.02f, C("#FF1744")); b.m(Mt.METAL, 1f); b.box(x + 1.2f, y + 4.0f, z, 0.04f, 2.0f, 0.04f, C("#BDBDBD"))
        g.solid(x - 1.1f, z - 1.1f, x + 1.1f, z + 1.1f)
    }

    private fun volleyNet(g: CityGeo.Gen, x: Float, z: Float) {
        val b = g.b; val y = sandH(z)
        b.m(Mt.METAL, 1f)
        b.cyl(x - 4.5f, y, z, 0.05f, 0.05f, 2.6f, C("#FAFAFA"), true, 6); b.cyl(x + 4.5f, y, z, 0.05f, 0.05f, 2.6f, C("#FAFAFA"), true, 6)
        b.m(Mt.PLAIN); b.al = 0.6f
        b.box(x, y + 2.05f, z, 9f, 0.9f, 0.01f, C("#FFFFFF"))
        b.al = 1f
        b.box(x, y + 2.5f, z, 9f, 0.06f, 0.02f, C("#FFFFFF"))
        b.box(x, y + 0.01f, z, 9.2f, 0.01f, 0.06f, C("#1E88E5")); b.box(x, y + 0.01f, z - 8f, 9.2f, 0.01f, 0.06f, C("#1E88E5")); b.box(x, y + 0.01f, z + 8f, 9.2f, 0.01f, 0.06f, C("#1E88E5"))
        b.box(x - 4.6f, y + 0.01f, z, 0.06f, 0.01f, 16f, C("#1E88E5")); b.box(x + 4.6f, y + 0.01f, z, 0.06f, 0.01f, 16f, C("#1E88E5"))
        b.m(Mt.PLAIN); CityGeo.ball(b, x + 2f, y + 0.11f, z + 3f, 0.11f, C("#FFEB3B"), 0.11f, 8)
    }

    private fun pier(g: CityGeo.Gen) {
        val b = g.b; val x = City.PIER_X; val z0 = City.BEACH_Z + 4f; val z1 = City.SEA_Z + 62f
        val w = 5f; val y = 1.2f
        b.m(Mt.FLOOR_D, 0.8f)
        b.box(x, y - 0.08f, (z0 + 6f + z1) / 2, w, 0.16f, z1 - z0 - 6f, C("#FFFFFF"))
        // rampa
        CityGeo.q(b, CityGeo.P(x - w / 2, sandH(z0), z0) + CityGeo.P(x + w / 2, sandH(z0), z0) + CityGeo.P(x + w / 2, y, z0 + 6f) + CityGeo.P(x - w / 2, y, z0 + 6f), C("#FFFFFF"))
        b.m(Mt.WOOD, 1f)
        var z = z0 + 6f
        while (z < z1) {
            for (s in floatArrayOf(-1f, 1f)) {
                b.cyl(x + s * (w / 2 - 0.2f), -3f, z, 0.18f, 0.18f, y + 3f - 0.1f, C("#5D4037"), true, 8)
                b.box(x + s * (w / 2 - 0.05f), y + 0.55f, z, 0.1f, 1.1f, 0.1f, C("#6D4C41"))
            }
            z += 4f
        }
        for (s in floatArrayOf(-1f, 1f)) {
            b.box(x + s * (w / 2 - 0.05f), y + 1.1f, (z0 + 6f + z1) / 2, 0.12f, 0.08f, z1 - z0 - 6f, C("#8D6E63"))
            b.box(x + s * (w / 2 - 0.05f), y + 0.6f, (z0 + 6f + z1) / 2, 0.06f, 0.05f, z1 - z0 - 6f, C("#8D6E63"))
        }
        z = z0 + 12f
        while (z < z1 - 4f) { CityGeo.streetLamp(b, x - w / 2 + 0.3f, z, 0f, 0f, y); z += 16f }
        // plataforma do fim com gazebo
        b.m(Mt.FLOOR_D, 0.8f); b.box(x, y - 0.08f, z1 + 4f, 12f, 0.16f, 8f, C("#FFFFFF"))
        b.m(Mt.WOOD, 1f)
        for (cx in floatArrayOf(-3f, 3f)) for (cz in floatArrayOf(2f, 6f)) b.cyl(x + cx, y, z1 + cz, 0.12f, 0.12f, 2.6f, C("#FAFAFA"), true, 8)
        b.m(Mt.ROOF, 0.6f); b.cyl(x, y + 2.6f, z1 + 4f, 4.8f, 0.2f, 1.6f, C("#1565C0"), true, 8)
        for (k in 0 until 3) CityGeo.publicBench(b, x - 3f + k * 3f, z1 + 7f, 0f, -1f)
        CityGeo.sign(b, x, y + 2.2f, z0 + 6.2f, 0f, -1f, 2.4f, 0.4f, City.signIdx("PÍER"))
    }

    // ============================================================ parque de diversões

    fun park(g: CityGeo.Gen) {
        val b = g.b; val rng = g.rng
        px0 = g.x0; pz0 = g.z0; px1 = g.x1; pz1 = g.z1
        val cx = (px0 + px1) / 2
        CityGeo.groundBox(b, px0, pz0, px1, pz1, Mt.PAVER, 0.6f, C("#EADCC8"))
        CityGeo.groundBox(g.f, px0, pz0, px1, pz1, Mt.PAVER, 0.6f, C("#EADCC8"))
        // canteiros de grama
        b.m(Mt.GRASS, 0.3f)
        for (k in 0 until 6) { val gx = px0 + 6f + (k % 3) * 34f; val gz = pz0 + 6f + (k / 3) * 46f; b.box(gx, CURB + 0.02f, gz, 6f, 0.04f, 4f, C("#BFE0A4")) }
        // cerca com entrada (lado -z)
        b.m(Mt.METAL, 1f)
        val fc = C("#6A1B9A")
        for (seg in arrayOf(floatArrayOf(px0, cx - 5f), floatArrayOf(cx + 5f, px1))) {
            b.box((seg[0] + seg[1]) / 2, CURB + 1.0f, pz0 + 0.2f, seg[1] - seg[0], 0.06f, 0.06f, fc); b.box((seg[0] + seg[1]) / 2, CURB + 2.0f, pz0 + 0.2f, seg[1] - seg[0], 0.06f, 0.06f, fc)
            var x = seg[0]; while (x <= seg[1]) { b.box(x, CURB + 1.05f, pz0 + 0.2f, 0.06f, 2.1f, 0.06f, fc); x += 0.25f }
            g.solid(seg[0], pz0, seg[1], pz0 + 0.4f)
        }
        b.box(cx, CURB + 1.0f, pz1 - 0.2f, px1 - px0, 2.0f, 0.06f, fc); g.solid(px0, pz1 - 0.4f, px1, pz1)
        b.box(px0 + 0.2f, CURB + 1.0f, (pz0 + pz1) / 2, 0.06f, 2.0f, pz1 - pz0, fc); g.solid(px0, pz0, px0 + 0.4f, pz1)
        b.box(px1 - 0.2f, CURB + 1.0f, (pz0 + pz1) / 2, 0.06f, 2.0f, pz1 - pz0, fc); g.solid(px1 - 0.4f, pz0, px1, pz1)
        // arco de entrada com letreiro e bilheterias
        b.m(Mt.PLASTER, 0.5f)
        for (s in floatArrayOf(-1f, 1f)) { b.box(cx + s * 5.6f, CURB + 3.5f, pz0 + 0.2f, 1.2f, 7f, 1.2f, C("#8E24AA")); b.m(Mt.PLAIN); CityGeo.ball(b, cx + s * 5.6f, CURB + 7.6f, pz0 + 0.2f, 0.8f, C("#FFD54F"), 0.8f, 10); b.m(Mt.PLASTER, 0.5f) }
        b.box(cx, CURB + 7.2f, pz0 + 0.2f, 12.4f, 1.6f, 0.8f, C("#6A1B9A"))
        CityGeo.sign(b, cx, CURB + 6.6f, pz0 - 0.22f, 0f, -1f, 10f, 1.25f, City.signIdx("PARQUE DE DIVERSÕES"))
        CityGeo.sign(b, cx, CURB + 6.6f, pz0 + 0.62f, 0f, 1f, 10f, 1.25f, City.signIdx("PARQUE DE DIVERSÕES"))
        for (s in floatArrayOf(-1f, 1f)) {
            val bx = cx + s * 9f
            b.m(Mt.PLASTER, 0.5f); b.box(bx, CURB + 1.4f, pz0 + 2.5f, 2.6f, 2.8f, 2.2f, C("#FFF3E0"))
            b.m(Mt.METAL, 1f); b.box(bx, CURB + 1.6f, pz0 + 1.38f, 1.6f, 0.9f, 0.03f, C("#37474F"))
            b.m(Mt.ROOF, 0.6f); b.box(bx, CURB + 2.95f, pz0 + 2.5f, 3.0f, 0.2f, 2.6f, C("#E53935"))
            g.solid(bx - 1.3f, pz0 + 1.4f, bx + 1.3f, pz0 + 3.6f)
        }
        lightString(b, cx - 5.6f, CURB + 6.8f, pz0 + 0.2f, cx - 14f, CURB + 2.2f, pz0 + 0.2f)
        lightString(b, cx + 5.6f, CURB + 6.8f, pz0 + 0.2f, cx + 14f, CURB + 2.2f, pz0 + 0.2f)

        // roda-gigante (estrutura fixa; roda e cabines giram)
        val wx = px1 - 16f; val wz = pz0 + 22f; val axY = CURB + 16f; val R = 13f
        b.m(Mt.METAL, 1f)
        for (s in floatArrayOf(-1f, 1f)) for (t in floatArrayOf(-1f, 1f)) {
            CityGeo.q(b, CityGeo.P(wx + t * 6f - 0.25f, CURB, wz + s * 2.2f) + CityGeo.P(wx + t * 6f + 0.25f, CURB, wz + s * 2.2f) + CityGeo.P(wx + 0.2f, axY, wz + s * 1.2f) + CityGeo.P(wx - 0.2f, axY, wz + s * 1.2f), C("#ECEFF1"))
        }
        b.cyl(wx, axY - 0.6f, wz, 0.1f, 0.1f, 1.2f, C("#B0BEC5"), true, 8)
        b.m(Mt.PLASTER, 0.5f); b.box(wx, CURB + 0.6f, wz - 5f, 6f, 1.2f, 3f, C("#1565C0"))
        CityGeo.sign(b, wx, CURB + 1.6f, wz - 6.6f, 0f, -1f, 3.2f, 0.45f, City.signIdx("RODA-GIGANTE"))
        g.solid(wx - 6.5f, wz - 2.6f, wx + 6.5f, wz + 2.6f)
        // carrossel (base fixa)
        val cx2 = px0 + 16f; val cz2 = pz0 + 18f
        b.m(Mt.STONE, 0.6f); b.cyl(cx2, CURB, cz2, 7.2f, 7.2f, 0.45f, C("#F8BBD0"), true, 28)
        b.m(Mt.METAL, 1f); b.cyl(cx2, CURB, cz2, 0.5f, 0.5f, 5.2f, C("#FFD54F"), true, 12)
        CityGeo.sign(b, cx2, CURB + 0.6f, cz2 - 7.5f, 0f, -1f, 3f, 0.45f, City.signIdx("CARROSSEL"))
        g.solid(cx2 - 7.2f, cz2 - 7.2f, cx2 + 7.2f, cz2 + 7.2f)
        // elevador (torre fixa; anel sobe e desce)
        val tx = px1 - 10f; val tz = pz1 - 12f
        b.m(Mt.METAL, 1f); b.box(tx, CURB + 22f, tz, 1.6f, 44f, 1.6f, C("#455A64"))
        for (k in 0 until 22) b.box(tx, CURB + 1f + k * 2f, tz, 1.75f, 0.12f, 1.75f, C("#78909C"))
        b.m(Mt.PLAIN); CityGeo.ball(b, tx, CURB + 44.5f, tz, 0.6f, C("#FF1744"), 0.6f, 8, false)
        b.m(Mt.STONE, 0.6f); b.cyl(tx, CURB, tz, 4.5f, 4.5f, 0.3f, C("#90A4AE"), true, 20)
        g.solid(tx - 3.6f, tz - 3.6f, tx + 3.6f, tz + 3.6f)
        // bate-bate (pista coberta)
        val bx0 = px0 + 6f; val bz0 = pz1 - 26f; val bx1 = px0 + 30f; val bz1 = pz1 - 8f
        b.m(Mt.PLAIN); b.box((bx0 + bx1) / 2, CURB + 0.05f, (bz0 + bz1) / 2, bx1 - bx0, 0.1f, bz1 - bz0, C("#37474F"))
        b.m(Mt.METAL, 1f)
        for (s in arrayOf(floatArrayOf(bx0, bz0), floatArrayOf(bx1, bz0), floatArrayOf(bx0, bz1), floatArrayOf(bx1, bz1))) b.cyl(s[0], CURB, s[1], 0.18f, 0.18f, 5f, C("#FFD54F"), true, 8)
        b.box((bx0 + bx1) / 2, CURB + 5.1f, (bz0 + bz1) / 2, bx1 - bx0 + 0.6f, 0.25f, bz1 - bz0 + 0.6f, C("#2E7D32"))
        b.m(Mt.PLAIN)
        b.box((bx0 + bx1) / 2, CURB + 4.95f, (bz0 + bz1) / 2, bx1 - bx0 - 1f, 0.02f, bz1 - bz0 - 1f, C("#FFF8E1"), false)
        b.m(Mt.FABRIC, 1f)
        b.box((bx0 + bx1) / 2, CURB + 0.4f, bz0, bx1 - bx0, 0.6f, 0.3f, C("#FDD835")); b.box((bx0 + bx1) / 2, CURB + 0.4f, bz1, bx1 - bx0, 0.6f, 0.3f, C("#FDD835"))
        b.box(bx0, CURB + 0.4f, (bz0 + bz1) / 2, 0.3f, 0.6f, bz1 - bz0, C("#FDD835")); b.box(bx1, CURB + 0.4f, (bz0 + bz1) / 2, 0.3f, 0.6f, bz1 - bz0, C("#FDD835"))
        CityGeo.sign(b, (bx0 + bx1) / 2, CURB + 4.2f, bz0 - 0.32f, 0f, -1f, 3.4f, 0.5f, City.signIdx("BATE-BATE"))
        g.solid(bx0 - 0.2f, bz0 - 0.2f, bx1 + 0.2f, bz0 + 0.2f); g.solid(bx0 - 0.2f, bz1 - 0.2f, bx1 + 0.2f, bz1 + 0.2f)
        g.solid(bx0 - 0.2f, bz0, bx0 + 0.2f, bz1); g.solid(bx1 - 0.2f, bz0, bx1 + 0.2f, bz1)
        bumper = floatArrayOf(bx0 + 1f, bz0 + 1f, bx1 - 1f, bz1 - 1f)
        // barracas de comida
        val foods = arrayOf("PIPOCA", "ALGODÃO DOCE", "HAMBÚRGUER", "SORVETERIA")
        for (k in 0 until 4) {
            val sx = cx - 13f + k * 8.5f; val sz = pz0 + 40f
            b.m(Mt.WOOD, 1f); b.box(sx, CURB + 0.6f, sz, 3f, 1.2f, 2.2f, C("#FFF8E1"))
            b.m(Mt.METAL, 1f); for (cx3 in floatArrayOf(-1.4f, 1.4f)) b.box(sx + cx3, CURB + 1.6f, sz - 1f, 0.08f, 2.0f, 0.08f, C("#BDBDBD"))
            b.m(Mt.FABRIC, 1f)
            for (st in 0 until 6) CityGeo.q(b, CityGeo.P(sx - 1.7f + st * 0.567f, CURB + 2.6f, sz + 1.2f) + CityGeo.P(sx - 1.7f + (st + 1) * 0.567f, CURB + 2.6f, sz + 1.2f) + CityGeo.P(sx - 1.7f + (st + 1) * 0.567f, CURB + 2.3f, sz - 1.4f) + CityGeo.P(sx - 1.7f + st * 0.567f, CURB + 2.3f, sz - 1.4f), if (st % 2 == 0) C("#E53935") else C("#FFFFFF"))
            CityGeo.sign(b, sx, CURB + 2.65f, sz - 1.45f, 0f, -1f, 2.6f, 0.38f, City.signIdx(foods[k]))
            g.solid(sx - 1.5f, sz - 1.1f, sx + 1.5f, sz + 1.1f)
        }
        for (k in 0 until 5) CityGeo.cafeTableOut(b, cx - 12f + k * 6f, pz0 + 46f, if (k % 2 == 0) C("#E53935") else C("#1E88E5"))
        for (k in 0 until 6) CityGeo.palm(g, px0 + 3f + k * 15.5f, pz1 - 3f, 0.9f)
        // montanha-russa: trilho fixo, trem anda
        buildCoaster(g)
        g.place(City.Place("Parque de Diversões", cx, pz0 - 2f, 0xFF6A1B9A.toInt(), 'D'))
    }

    private fun lightString(b: MB, x0: Float, y0: Float, z0: Float, x1: Float, y1: Float, z1: Float) {
        b.m(Mt.PLAIN)
        val n = 14
        val pal = arrayOf(C("#FF5252"), C("#FFEB3B"), C("#69F0AE"), C("#40C4FF"), C("#E040FB"))
        for (k in 0..n) {
            val t = k.toFloat() / n
            val sag = 0.8f * sin(PI.toFloat() * t)
            CityGeo.ball(b, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t - sag, z0 + (z1 - z0) * t, 0.09f, pal[k % pal.size], 0.09f, 5, false)
        }
    }

    // ------------------------------------------------------------ montanha-russa

    private var coaster = FloatArray(0)   // amostras x,y,z
    private var cLen = FloatArray(0)      // comprimento acumulado
    private var bumper = FloatArray(4)

    private fun buildCoaster(g: CityGeo.Gen) {
        // pontos de controle (x, z relativos ao canto px0,pz0; y altura acima da calçada)
        val ctl = floatArrayOf(
            40f, 30f, 2.5f, 52f, 30f, 2.5f, 60f, 34f, 14f, 66f, 42f, 20f, 70f, 52f, 9f, 62f, 58f, 4f,
            48f, 58f, 11f, 40f, 54f, 6f, 46f, 46f, 3f, 56f, 46f, 7f, 58f, 38f, 5f, 48f, 36f, 3f)
        val nc = ctl.size / 3
        val N = 360
        val pts = FloatArray(N * 3)
        for (i in 0 until N) {
            val u = i.toFloat() / N * nc
            val k = u.toInt(); val t = u - k
            fun c(j: Int, a: Int) = ctl[(((k + j) % nc + nc) % nc) * 3 + a]
            for (a in 0..2) {
                val p0 = c(-1, a); val p1 = c(0, a); val p2 = c(1, a); val p3 = c(2, a)
                pts[i * 3 + a] = 0.5f * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)
            }
        }
        for (i in 0 until N) { pts[i * 3] += px0; pts[i * 3 + 1] += CURB; pts[i * 3 + 2] += pz0 }
        coaster = pts
        cLen = FloatArray(N + 1)
        for (i in 0 until N) {
            val j = (i + 1) % N
            val dx = pts[j * 3] - pts[i * 3]; val dy = pts[j * 3 + 1] - pts[i * 3 + 1]; val dz = pts[j * 3 + 2] - pts[i * 3 + 2]
            cLen[i + 1] = cLen[i] + sqrt(dx * dx + dy * dy + dz * dz)
        }
        val b = g.b
        b.m(Mt.METAL, 1f)
        val rail = C("#E53935"); val tie = C("#424242"); val sup = C("#ECEFF1")
        for (i in 0 until N) {
            val j = (i + 1) % N
            val f = frame(i)
            val fj = frame(j)
            for (s in floatArrayOf(-0.55f, 0.55f)) prism(b, pts[i * 3] + f[0] * s, pts[i * 3 + 1] + f[1] * s, pts[i * 3 + 2] + f[2] * s, pts[j * 3] + fj[0] * s, pts[j * 3 + 1] + fj[1] * s, pts[j * 3 + 2] + fj[2] * s, f, 0.07f, rail)
            prism(b, pts[i * 3] - f[3] * 0.25f, pts[i * 3 + 1] - f[4] * 0.25f, pts[i * 3 + 2] - f[5] * 0.25f, pts[j * 3] - fj[3] * 0.25f, pts[j * 3 + 1] - fj[4] * 0.25f, pts[j * 3 + 2] - fj[5] * 0.25f, f, 0.12f, rail)   // viga central
            if (i % 3 == 0) prism(b, pts[i * 3] - f[0] * 0.6f, pts[i * 3 + 1] - f[1] * 0.6f - 0.05f, pts[i * 3 + 2] - f[2] * 0.6f, pts[i * 3] + f[0] * 0.6f, pts[i * 3 + 1] + f[1] * 0.6f - 0.05f, pts[i * 3 + 2] + f[2] * 0.6f, floatArrayOf(f[6], f[7], f[8], f[3], f[4], f[5]), 0.06f, tie)
            if (i % 9 == 0 && pts[i * 3 + 1] > CURB + 1.2f) {
                b.cyl(pts[i * 3], CURB, pts[i * 3 + 2], 0.2f, 0.16f, pts[i * 3 + 1] - CURB - 0.35f, sup, true, 8)
                g.solid(pts[i * 3] - 0.4f, pts[i * 3 + 2] - 0.4f, pts[i * 3] + 0.4f, pts[i * 3 + 2] + 0.4f)
            }
        }
        // estação
        val sx = pts[0]; val sz = pts[2]
        b.m(Mt.PLASTER, 0.5f); b.box(sx + 6f, CURB + 1f, sz, 12f, 2f, 4f, C("#FFB74D"))
        b.m(Mt.ROOF, 0.6f); b.box(sx + 6f, CURB + 5f, sz, 13f, 0.3f, 5f, C("#E65100"))
        b.m(Mt.METAL, 1f); for (k in 0 until 4) b.box(sx + 0.5f + k * 3.7f, CURB + 3f, sz - 2.2f, 0.15f, 4f, 0.15f, C("#BDBDBD"))
        CityGeo.sign(b, sx + 6f, CURB + 4.2f, sz - 2.6f, 0f, -1f, 4f, 0.55f, City.signIdx("MONTANHA-RUSSA"))
    }

    /** Base no ponto i: direita (0..2), cima (3..5), frente (6..8). */
    private fun frame(i: Int): FloatArray {
        val N = coaster.size / 3
        val j = (i + 1) % N; val h = (i - 1 + N) % N
        var tx = coaster[j * 3] - coaster[h * 3]; var ty = coaster[j * 3 + 1] - coaster[h * 3 + 1]; var tz = coaster[j * 3 + 2] - coaster[h * 3 + 2]
        val tl = sqrt(tx * tx + ty * ty + tz * tz).coerceAtLeast(1e-5f); tx /= tl; ty /= tl; tz /= tl
        // direita = T x up
        var rx = -tz; val ry = 0f; var rz = tx
        val rl = sqrt(rx * rx + rz * rz).coerceAtLeast(1e-5f); rx /= rl; rz /= rl
        // cima = R x T
        val ux = ry * tz - rz * ty; val uy = rz * tx - rx * tz; val uz = rx * ty - ry * tx
        return floatArrayOf(rx, ry, rz, ux, uy, uz, tx, ty, tz)
    }

    /** Barra de seção quadrada [s] entre dois pontos, com eixos laterais tirados de [f] (direita, cima). */
    private fun prism(b: MB, ax: Float, ay: Float, az: Float, bx: Float, by: Float, bz: Float, f: FloatArray, s: Float, c: Int) {
        val rx = f[0] * s; val ry = f[1] * s; val rz = f[2] * s; val ux = f[3] * s; val uy = f[4] * s; val uz = f[5] * s
        val corners = arrayOf(floatArrayOf(-1f, -1f), floatArrayOf(1f, -1f), floatArrayOf(1f, 1f), floatArrayOf(-1f, 1f))
        for (k in 0 until 4) {
            val c0 = corners[k]; val c1 = corners[(k + 1) % 4]
            val p0 = floatArrayOf(ax + rx * c0[0] + ux * c0[1], ay + ry * c0[0] + uy * c0[1], az + rz * c0[0] + uz * c0[1])
            val p1 = floatArrayOf(ax + rx * c1[0] + ux * c1[1], ay + ry * c1[0] + uy * c1[1], az + rz * c1[0] + uz * c1[1])
            val p2 = floatArrayOf(bx + rx * c1[0] + ux * c1[1], by + ry * c1[0] + uy * c1[1], bz + rz * c1[0] + uz * c1[1])
            val p3 = floatArrayOf(bx + rx * c0[0] + ux * c0[1], by + ry * c0[0] + uy * c0[1], bz + rz * c0[0] + uz * c0[1])
            CityGeo.q(b, p0 + p1 + p2 + p3, c)
        }
    }

    // ------------------------------------------------------------ brinquedos animados

    private var wheelD: Dyn? = null
    private val cabins = ArrayList<Dyn>()
    private var carousel: Dyn? = null
    private var drop: Dyn? = null
    private val train = ArrayList<Dyn>()
    private val bumpers = ArrayList<Dyn>()
    private var t = 0f

    fun buildRides() {
        dyn.clear(); cabins.clear(); train.clear(); bumpers.clear()
        if (px1 <= px0) return
        val wx = px1 - 16f; val wz = pz0 + 22f; val axY = CURB + 16f; val R = 13f
        // roda: dois aros, raios e luzes
        run {
            val b = MB(); b.m(Mt.METAL, 1f)
            val seg = 36
            for (side in floatArrayOf(-1.1f, 1.1f)) {
                for (i in 0 until seg) {
                    val a0 = 2f * PI.toFloat() * i / seg; val a1 = 2f * PI.toFloat() * (i + 1) / seg
                    val f = floatArrayOf(0f, 0f, 1f, -sin((a0 + a1) / 2), cos((a0 + a1) / 2), 0f, 0f, 0f, 0f)
                    prism(b, R * cos(a0), R * sin(a0), side, R * cos(a1), R * sin(a1), side, floatArrayOf(-sin(a0), cos(a0), 0f, 0f, 0f, 1f), 0.12f, C("#ECEFF1"))
                    prism(b, R * 0.6f * cos(a0), R * 0.6f * sin(a0), side, R * 0.6f * cos(a1), R * 0.6f * sin(a1), side, floatArrayOf(-sin(a0), cos(a0), 0f, 0f, 0f, 1f), 0.07f, C("#ECEFF1"))
                    if (i % 3 == 0) {
                        prism(b, 0f, 0f, side, R * cos(a0), R * sin(a0), side, floatArrayOf(-sin(a0), cos(a0), 0f, 0f, 0f, 1f), 0.05f, C("#CFD8DC"))
                        b.m(Mt.PLAIN); CityGeo.ball(b, R * cos(a0), R * sin(a0), side * 1.2f, 0.14f, if (i % 2 == 0) C("#FFEB3B") else C("#FF4081"), 0.14f, 5, false); b.m(Mt.METAL, 1f)
                    }
                }
            }
            b.cyl(0f, -0.5f, 0f, 0.6f, 0.6f, 1f, C("#B0BEC5"), true, 12)
            for (k in 0 until 12) { val a = 2f * PI.toFloat() * k / 12; prism(b, R * cos(a), R * sin(a), -1.1f, R * cos(a), R * sin(a), 1.1f, floatArrayOf(1f, 0f, 0f, 0f, 1f, 0f), 0.06f, C("#B0BEC5")) }
            val m = b.toMesh(true); own.add(m)
            wheelD = Dyn(m, wx, wz).also { dyn.add(it) }
        }
        val cabC = arrayOf(C("#E53935"), C("#1E88E5"), C("#FDD835"), C("#43A047"), C("#8E24AA"), C("#FB8C00"))
        for (k in 0 until 12) {
            val b = MB(); b.m(Mt.METAL, 1f)
            b.box(0f, -0.25f, 0f, 0.08f, 0.5f, 0.08f, C("#9E9E9E"))
            b.box(0f, -1.55f, 0f, 1.7f, 1.4f, 1.4f, cabC[k % cabC.size])
            b.m(Mt.GLASS); b.al = 0.35f; b.box(0f, -1.25f, 0f, 1.72f, 0.6f, 1.42f, C("#E1F5FE")); b.al = 1f
            b.m(Mt.METAL, 1f); b.box(0f, -0.5f, 0f, 1.9f, 0.12f, 1.6f, shade(cabC[k % cabC.size], -30))
            val m = b.toMesh(true); own.add(m)
            cabins.add(Dyn(m, wx, wz).also { dyn.add(it) })
        }
        // carrossel: teto listrado, cavalos em hastes
        run {
            val b = MB()
            b.m(Mt.FABRIC, 1f)
            val seg = 16
            for (i in 0 until seg) {
                val a0 = 2f * PI.toFloat() * i / seg; val a1 = 2f * PI.toFloat() * (i + 1) / seg
                CityGeo.tri(b, CityGeo.P(0f, 7.6f, 0f) + CityGeo.P(7.4f * cos(a0), 5.2f, 7.4f * sin(a0)) + CityGeo.P(7.4f * cos(a1), 5.2f, 7.4f * sin(a1)), if (i % 2 == 0) C("#E91E63") else C("#FFF59D"))
                CityGeo.q(b, CityGeo.P(7.4f * cos(a0), 5.2f, 7.4f * sin(a0)) + CityGeo.P(7.4f * cos(a1), 5.2f, 7.4f * sin(a1)) + CityGeo.P(7.4f * cos(a1), 4.6f, 7.4f * sin(a1)) + CityGeo.P(7.4f * cos(a0), 4.6f, 7.4f * sin(a0)), if (i % 2 == 0) C("#FFF59D") else C("#E91E63"))
            }
            b.m(Mt.PLAIN); CityGeo.ball(b, 0f, 8f, 0f, 0.5f, C("#FFD54F"), 0.5f, 8)
            b.m(Mt.WOOD, 1f); b.cyl(0f, 0.45f, 0f, 6.9f, 6.9f, 0.12f, C("#FFE0B2"), true, 28)
            val hc = arrayOf(C("#FFFFFF"), C("#8D6E63"), C("#F5F5F5"), C("#212121"))
            for (k in 0 until 12) {
                val a = 2f * PI.toFloat() * k / 12
                val r = if (k % 2 == 0) 5.6f else 3.8f
                val hx = r * cos(a); val hz = r * sin(a)
                b.m(Mt.METAL, 1f); b.cyl(hx, 0.5f, hz, 0.04f, 0.04f, 4.2f, C("#FFD54F"), true, 6)
                // cavalo virado na tangente
                val tx = -sin(a); val tz = cos(a)
                val y = 1.6f + (k % 3) * 0.25f
                val col = hc[k % hc.size]
                b.m(Mt.PLAIN)
                b.box(hx, y, hz, if (abs(tx) > abs(tz)) 1.1f else 0.35f, 0.45f, if (abs(tx) > abs(tz)) 0.35f else 1.1f, col)
                b.box(hx + tx * 0.6f, y + 0.4f, hz + tz * 0.6f, 0.26f, 0.6f, 0.26f, col)
                b.box(hx + tx * 0.78f, y + 0.68f, hz + tz * 0.78f, if (abs(tx) > abs(tz)) 0.45f else 0.22f, 0.24f, if (abs(tx) > abs(tz)) 0.22f else 0.45f, col)
                for (s in floatArrayOf(-0.35f, 0.35f)) b.box(hx + tx * s, y - 0.5f, hz + tz * s, 0.1f, 0.6f, 0.1f, col)
                b.box(hx, y + 0.27f, hz, 0.4f, 0.08f, 0.4f, C("#C62828"))
                b.box(hx - tx * 0.62f, y + 0.05f, hz - tz * 0.62f, 0.1f, 0.5f, 0.1f, C("#5D4037"))
            }
            val m = b.toMesh(true); own.add(m)
            carousel = Dyn(m, px0 + 16f, pz0 + 18f).also { dyn.add(it) }
        }
        // elevador: anel de assentos
        run {
            val b = MB(); b.m(Mt.METAL, 1f)
            b.cyl(0f, -0.4f, 0f, 2.6f, 2.6f, 0.8f, C("#FF6F00"), true, 20)
            for (k in 0 until 10) { val a = 2f * PI.toFloat() * k / 10; b.box(2.4f * cos(a), -1.0f, 2.4f * sin(a), 0.5f, 1.0f, 0.5f, C("#263238")) }
            val m = b.toMesh(true); own.add(m)
            drop = Dyn(m, px1 - 10f, pz1 - 12f).also { dyn.add(it) }
        }
        // trem da montanha-russa (5 carrinhos)
        for (k in 0 until 5) {
            val b = MB(); b.m(Mt.METAL, 1f)
            val col = if (k == 0) C("#1565C0") else C("#FDD835")
            b.box(0f, 0.55f, 0f, 1.5f, 0.7f, 1.8f, col)
            b.box(0f, 0.95f, -0.75f, 1.3f, 0.5f, 0.15f, shade(col, -30))
            b.m(Mt.PLAIN); b.box(0f, 0.95f, 0.1f, 1.1f, 0.12f, 0.9f, C("#212121"))
            if (k == 0) { b.m(Mt.METAL, 1f); b.box(0f, 0.75f, 0.95f, 1.2f, 0.5f, 0.3f, C("#0D47A1")) }
            // passageiros
            b.m(Mt.FABRIC, 1f)
            for (s in floatArrayOf(-0.35f, 0.35f)) { b.box(s, 1.25f, -0.2f, 0.36f, 0.5f, 0.3f, if ((k + s.toInt()) % 2 == 0) C("#43A047") else C("#E53935")); b.m(Mt.PLAIN); CityGeo.ball(b, s, 1.62f, -0.2f, 0.14f, C("#E0B48A"), 0.16f, 7); b.m(Mt.FABRIC, 1f) }
            val m = b.toMesh(true); own.add(m)
            train.add(Dyn(m, coaster.getOrElse(0) { 0f }, coaster.getOrElse(2) { 0f }).also { dyn.add(it) })
        }
        // carrinhos do bate-bate
        val bc = arrayOf(C("#E53935"), C("#1E88E5"), C("#FDD835"), C("#43A047"), C("#8E24AA"), C("#FB8C00"))
        for (k in 0 until 6) {
            val b = MB(); b.m(Mt.METAL, 1f)
            b.box(0f, 0.35f, 0f, 1.3f, 0.45f, 1.9f, bc[k])
            b.m(Mt.FABRIC, 1f); b.box(0f, 0.3f, 0f, 1.45f, 0.25f, 2.05f, C("#212121"))
            b.m(Mt.METAL, 1f); b.cyl(0f, 0.55f, -0.7f, 0.03f, 0.03f, 4.3f, C("#9E9E9E"), true, 5)
            b.box(0f, 0.8f, 0.4f, 0.3f, 0.3f, 0.05f, C("#212121"))
            b.m(Mt.FABRIC, 1f); b.box(0f, 0.95f, -0.2f, 0.4f, 0.5f, 0.3f, bc[(k + 2) % 6]); b.m(Mt.PLAIN); CityGeo.ball(b, 0f, 1.33f, -0.2f, 0.14f, C("#E0B48A"), 0.16f, 7)
            val m = b.toMesh(true); own.add(m)
            bumpers.add(Dyn(m, (bumper[0] + bumper[2]) / 2, (bumper[1] + bumper[3]) / 2).also { dyn.add(it) })
        }
        built = true
        update(0f)
    }

    fun update(dt: Float) {
        if (!built) return
        t += dt
        val wx = px1 - 16f; val wz = pz0 + 22f; val axY = CURB + 16f; val R = 13f
        val ang = t * 0.12f
        wheelD?.let { d -> Matrix.setIdentityM(d.m, 0); Matrix.translateM(d.m, 0, wx, axY, wz); Matrix.rotateM(d.m, 0, Math.toDegrees(ang.toDouble()).toFloat(), 0f, 0f, 1f) }
        for ((k, d) in cabins.withIndex()) {
            val a = ang + 2f * PI.toFloat() * k / cabins.size
            Matrix.setIdentityM(d.m, 0); Matrix.translateM(d.m, 0, wx + R * cos(a), axY + R * sin(a), wz)
            Matrix.rotateM(d.m, 0, 4f * sin(t * 1.3f + k), 0f, 0f, 1f)
        }
        carousel?.let { d -> Matrix.setIdentityM(d.m, 0); Matrix.translateM(d.m, 0, d.x, CURB, d.z); Matrix.rotateM(d.m, 0, t * 25f, 0f, 1f, 0f) }
        drop?.let { d ->
            // sobe devagar, segura, cai rápido, freia
            val c = t % 14f
            val h = when { c < 7f -> 2f + 38f * (c / 7f); c < 9f -> 40f; c < 10.2f -> 40f - 38f * ((c - 9f) / 1.2f) * ((c - 9f) / 1.2f); else -> 2f }
            Matrix.setIdentityM(d.m, 0); Matrix.translateM(d.m, 0, d.x, CURB + h, d.z)
        }
        if (coaster.isNotEmpty()) {
            val total = cLen[cLen.size - 1]
            // velocidade varia com a altura (desce rápido, sobe devagar)
            val headS = (t * 11f) % total
            for ((k, d) in train.withIndex()) {
                var s = headS - k * 2.0f
                if (s < 0f) s += total
                var i = 0
                var lo = 0; var hi = cLen.size - 1
                while (hi - lo > 1) { val mid = (lo + hi) / 2; if (cLen[mid] <= s) lo = mid else hi = mid }
                i = lo.coerceIn(0, coaster.size / 3 - 1)
                val f = frame(i)
                val x = coaster[i * 3]; val y = coaster[i * 3 + 1]; val z = coaster[i * 3 + 2]
                val m = d.m
                m[0] = f[0]; m[1] = f[1]; m[2] = f[2]; m[3] = 0f
                m[4] = f[3]; m[5] = f[4]; m[6] = f[5]; m[7] = 0f
                m[8] = f[6]; m[9] = f[7]; m[10] = f[8]; m[11] = 0f
                m[12] = x; m[13] = y; m[14] = z; m[15] = 1f
            }
        }
        for ((k, d) in bumpers.withIndex()) {
            val cx = (bumper[0] + bumper[2]) / 2; val cz = (bumper[1] + bumper[3]) / 2
            val rx = (bumper[2] - bumper[0]) / 2 - 1.5f; val rz = (bumper[3] - bumper[1]) / 2 - 1.5f
            val a = t * (0.35f + k * 0.07f) + k * 1.3f
            val x = cx + rx * sin(a * 1.0f + k) * cos(a * 0.37f)
            val z = cz + rz * sin(a * 0.8f + k * 2f)
            val dx = rx * (cos(a + k) * cos(a * 0.37f) - 0.37f * sin(a + k) * sin(a * 0.37f)); val dz = rz * 0.8f * cos(a * 0.8f + k * 2f)
            Matrix.setIdentityM(d.m, 0); Matrix.translateM(d.m, 0, x, CURB + 0.1f, z)
            Matrix.rotateM(d.m, 0, Math.toDegrees(kotlin.math.atan2(dx.toDouble(), dz.toDouble())).toFloat(), 0f, 1f, 0f)
        }
    }
}
