package com.vinicius.meular

import java.util.WeakHashMap
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.sqrt

/**
 * Etapa 65 — sliders de corpo e rosto do The Sims 3 (Slider_Master_Files).
 *
 * Cada slider do jogo é um BlendUnit (FBLN) que aponta para um conjunto de ajustes de OSSO (BOND): deslocamento, escala e rotação
 * por osso do esqueleto de 257 ossos do Sims 3 (au/cu/pu). Aqui os ajustes são aplicados exatamente como no jogo: transformação
 * local do osso = repouso + ajuste (deslocamento e escala somados, quaternion somado e normalizado) e a malha é deformada por
 * M = W'·W⁻¹ de cada osso. Os pesos de pele são APROXIMADOS por proximidade (cápsulas em volta dos ossos), porque o GEOM original
 * com os pesos reais não existe para o corpo do app. Tudo é calculado sobre as posições de repouso (como o resto do BodyMorph),
 * então roupas, cabelo e sapatos acompanham e os clipes de animação não mudam.
 *
 * Arquivo cute/simsliders.txt (gerado por sl/export.py): RIG/B/SEG/S (esqueletos e cápsulas) e SL/D (sliders).
 */
object SimSliders {
    const val NS = 163          // número de posições da tabela original (alguns ids não têm dados e ficam sem uso)
    private const val K = 6     // ossos por vértice
    private const val EPS = 0.012f

    class Rig(val n: Int, val names: Array<String>, val par: IntArray, val lp: FloatArray, val lq: FloatArray, val ls: FloatArray) {
        val idx = HashMap<String, Int>()
        val w0 = FloatArray(n * 16)
        val iw0 = FloatArray(n * 16)
        var segBone = IntArray(0)
        var segA = FloatArray(0)
        var segB = FloatArray(0)
        var segR = FloatArray(0)
        var segC = FloatArray(0)      // centro
        var segReach = FloatArray(0)  // raio de busca
        var segNames = emptyArray<String>()
        init { for (i in 0 until n) idx[names[i]] = i }
    }

    class Delta(val bone: Array<String>, val v: FloatArray)   // v: 10 valores por osso (off3, scale3, quat4)
    class Slider(val id: Int, val name: String, val cat: String, val face: Boolean) {
        val dirs = HashMap<String, Array<Delta?>>()   // grupo do app (af, am, ...) -> [positivo, negativo]
    }

    val sliders = ArrayList<Slider>()
    private val byId = arrayOfNulls<Slider>(NS)
    private val rigs = HashMap<String, Rig>()
    @Volatile var ready = false
        private set

    /** Altura (m) do osso do pescoço no repouso do rig do grupo; usada para converter as unidades do app em metros do Sims. */
    fun neckY(grp: String): Float {
        val r = rigFor(grp) ?: return 1.607f
        val b = r.idx["b__Neck__"] ?: return 1.607f
        return r.w0[b * 16 + 7]
    }

    fun slider(id: Int): Slider? = if (id in 0 until NS) byId[id] else null

    // ---------- carregamento ----------
    private fun f3(s: String): FloatArray { val p = s.split(','); return FloatArray(p.size) { p[it].toFloat() } }

    private fun parseDelta(s: String): Delta? {
        if (s.isEmpty()) return null
        val parts = s.split(';')
        val names = Array(parts.size) { "" }
        val v = FloatArray(parts.size * 10)
        for ((i, p) in parts.withIndex()) {
            val q = p.split(':')
            names[i] = q[0]
            val o = f3(q[1]); val sc = f3(q[2]); val r = f3(q[3])
            for (k in 0 until 3) { v[i * 10 + k] = o[k]; v[i * 10 + 3 + k] = sc[k] }
            for (k in 0 until 4) v[i * 10 + 6 + k] = r[k]
        }
        return Delta(names, v)
    }

    @Synchronized
    fun load(text: String) {
        if (ready) return
        val lines = text.split('\n')
        var i = 0
        var cur: Slider? = null
        while (i < lines.size) {
            val ln = lines[i++]
            if (ln.isEmpty()) continue
            val p = ln.split('|')
            when (p[0]) {
                "RIG" -> {
                    val n = p[2].toInt()
                    val names = Array(n) { "" }; val par = IntArray(n)
                    val lp = FloatArray(n * 3); val lq = FloatArray(n * 4); val ls = FloatArray(n * 3)
                    for (b in 0 until n) {
                        val q = lines[i++].split('|')
                        names[b] = q[1]; par[b] = q[2].toInt()
                        val a = f3(q[3]); val c = f3(q[4]); val d = f3(q[5])
                        for (k in 0 until 3) { lp[b * 3 + k] = a[k]; ls[b * 3 + k] = d[k] }
                        for (k in 0 until 4) lq[b * 4 + k] = c[k]
                    }
                    val rig = Rig(n, names, par, lp, lq, ls)
                    world(rig, null, rig.w0)
                    for (b in 0 until n) invAffine(rig.w0, b * 16, rig.iw0, b * 16)
                    val sh = lines[i++].split('|')   // SEG|n
                    val ns = sh[1].toInt()
                    val sb = IntArray(ns); val sa = FloatArray(ns * 3); val sbb = FloatArray(ns * 3); val sr = FloatArray(ns)
                    val sn = Array(ns) { "" }
                    for (s in 0 until ns) {
                        val q = lines[i++].split('|')
                        sn[s] = q[1]; sb[s] = rig.idx[q[1]] ?: 0
                        val a = f3(q[2]); val b2 = f3(q[3])
                        for (k in 0 until 3) { sa[s * 3 + k] = a[k]; sbb[s * 3 + k] = b2[k] }
                        sr[s] = q[4].toFloat()
                    }
                    rig.segBone = sb; rig.segA = sa; rig.segB = sbb; rig.segR = sr; rig.segNames = sn
                    rig.segC = FloatArray(ns * 3); rig.segReach = FloatArray(ns)
                    for (s in 0 until ns) {
                        var l2 = 0f
                        for (k in 0 until 3) { rig.segC[s * 3 + k] = (sa[s * 3 + k] + sbb[s * 3 + k]) * 0.5f; val d = sbb[s * 3 + k] - sa[s * 3 + k]; l2 += d * d }
                        rig.segReach[s] = sqrt(l2) * 0.5f + sr[s] + 0.45f
                    }
                    rigs[p[1]] = rig
                }
                "SL" -> {
                    val id = p[1].toInt()
                    val s = Slider(id, p[2], p[3], p[4] == "face")
                    if (id in 0 until NS) { byId[id] = s; sliders.add(s) }
                    cur = s
                }
                "D" -> {
                    val c = cur ?: continue
                    val arr = arrayOf(parseDelta(p[2]), parseDelta(p[3]))
                    for (g in p[1].split(',')) c.dirs[g] = arr
                }
            }
        }
        ready = rigs.isNotEmpty() && sliders.isNotEmpty()
    }

    // ---------- matrizes 4x4 (linha-maior) ----------
    private fun invAffine(m: FloatArray, o: Int, out: FloatArray, oo: Int) {
        val a = m[o]; val b = m[o + 1]; val c = m[o + 2]
        val d = m[o + 4]; val e = m[o + 5]; val f = m[o + 6]
        val g = m[o + 8]; val h = m[o + 9]; val i = m[o + 10]
        val det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
        val id = if (abs(det) < 1e-12f) 0f else 1f / det
        val r00 = (e * i - f * h) * id; val r01 = (c * h - b * i) * id; val r02 = (b * f - c * e) * id
        val r10 = (f * g - d * i) * id; val r11 = (a * i - c * g) * id; val r12 = (c * d - a * f) * id
        val r20 = (d * h - e * g) * id; val r21 = (b * g - a * h) * id; val r22 = (a * e - b * d) * id
        val tx = m[o + 3]; val ty = m[o + 7]; val tz = m[o + 11]
        out[oo] = r00; out[oo + 1] = r01; out[oo + 2] = r02; out[oo + 3] = -(r00 * tx + r01 * ty + r02 * tz)
        out[oo + 4] = r10; out[oo + 5] = r11; out[oo + 6] = r12; out[oo + 7] = -(r10 * tx + r11 * ty + r12 * tz)
        out[oo + 8] = r20; out[oo + 9] = r21; out[oo + 10] = r22; out[oo + 11] = -(r20 * tx + r21 * ty + r22 * tz)
        out[oo + 12] = 0f; out[oo + 13] = 0f; out[oo + 14] = 0f; out[oo + 15] = 1f
    }

    /** Mundo de todos os ossos; [acc] = 10 valores por osso (off3, dscale3, dquat4) somados ao repouso, ou null. */
    private fun world(rig: Rig, acc: FloatArray?, out: FloatArray) {
        val l = FloatArray(16)
        for (b in 0 until rig.n) {
            var px = rig.lp[b * 3]; var py = rig.lp[b * 3 + 1]; var pz = rig.lp[b * 3 + 2]
            var sx = rig.ls[b * 3]; var sy = rig.ls[b * 3 + 1]; var sz = rig.ls[b * 3 + 2]
            var qx = rig.lq[b * 4]; var qy = rig.lq[b * 4 + 1]; var qz = rig.lq[b * 4 + 2]; var qw = rig.lq[b * 4 + 3]
            if (acc != null) {
                val o = b * 10
                px += acc[o]; py += acc[o + 1]; pz += acc[o + 2]
                sx += acc[o + 3]; sy += acc[o + 4]; sz += acc[o + 5]
                qx += acc[o + 6]; qy += acc[o + 7]; qz += acc[o + 8]; qw += acc[o + 9]
            }
            val qn = sqrt(qx * qx + qy * qy + qz * qz + qw * qw)
            if (qn > 1e-9f) { qx /= qn; qy /= qn; qz /= qn; qw /= qn }
            val r00 = 1 - 2 * (qy * qy + qz * qz); val r01 = 2 * (qx * qy - qz * qw); val r02 = 2 * (qx * qz + qy * qw)
            val r10 = 2 * (qx * qy + qz * qw); val r11 = 1 - 2 * (qx * qx + qz * qz); val r12 = 2 * (qy * qz - qx * qw)
            val r20 = 2 * (qx * qz - qy * qw); val r21 = 2 * (qy * qz + qx * qw); val r22 = 1 - 2 * (qx * qx + qy * qy)
            l[0] = r00 * sx; l[1] = r01 * sy; l[2] = r02 * sz; l[3] = px
            l[4] = r10 * sx; l[5] = r11 * sy; l[6] = r12 * sz; l[7] = py
            l[8] = r20 * sx; l[9] = r21 * sy; l[10] = r22 * sz; l[11] = pz
            l[12] = 0f; l[13] = 0f; l[14] = 0f; l[15] = 1f
            val pr = rig.par[b]
            val o = b * 16
            if (pr < 0) { System.arraycopy(l, 0, out, o, 16) } else mul(out, pr * 16, l, 0, out, o)
        }
    }

    private fun mul(a: FloatArray, ao: Int, b: FloatArray, bo: Int, out: FloatArray, oo: Int) {
        val t = FloatArray(12)
        for (r in 0 until 3) for (c in 0 until 4) {
            var s = a[ao + r * 4] * b[bo + c] + a[ao + r * 4 + 1] * b[bo + 4 + c] + a[ao + r * 4 + 2] * b[bo + 8 + c]
            if (c == 3) s += a[ao + r * 4 + 3]
            t[r * 4 + c] = s
        }
        System.arraycopy(t, 0, out, oo, 12)
        out[oo + 12] = 0f; out[oo + 13] = 0f; out[oo + 14] = 0f; out[oo + 15] = 1f
    }

    // ---------- pesos de pele por proximidade ----------
    private class Wt(val grp: String, val nv: Int, val ix: IntArray, val w: FloatArray)
    private val cache = WeakHashMap<FloatArray, Wt>()

    private fun rigFor(grp: String): Rig? = rigs[if (grp.startsWith("cu")) "cu" else if (grp.startsWith("pu")) "pu" else "au"]

    private fun segDist2(rig: Rig, s: Int, x: Float, y: Float, z: Float): Float {
        val ax = rig.segA[s * 3]; val ay = rig.segA[s * 3 + 1]; val az = rig.segA[s * 3 + 2]
        val bx = rig.segB[s * 3] - ax; val by = rig.segB[s * 3 + 1] - ay; val bz = rig.segB[s * 3 + 2] - az
        val l2 = bx * bx + by * by + bz * bz
        val px = x - ax; val py = y - ay; val pz = z - az
        var t = 0f
        if (l2 > 1e-12f) { t = (px * bx + py * by + pz * bz) / l2; if (t < 0f) t = 0f else if (t > 1f) t = 1f }
        val dx = px - t * bx; val dy = py - t * by; val dz = pz - t * bz
        return dx * dx + dy * dy + dz * dz
    }

    private fun computeW(rig: Rig, grp: String, src: FloatArray, nv: Int, k: Float): Wt {
        val ix = IntArray(nv * K); val w = FloatArray(nv * K)
        val ns = rig.segBone.size
        val bw = FloatArray(K); val bi = IntArray(K)
        val inv = 1f / k
        for (v in 0 until nv) {
            val x = src[v * 3] * inv; val y = src[v * 3 + 1] * inv; val z = src[v * 3 + 2] * inv
            java.util.Arrays.fill(bw, 0f); java.util.Arrays.fill(bi, 0)
            for (pass in 0..1) {
                for (s in 0 until ns) {
                    if (pass == 0) {
                        val dx = x - rig.segC[s * 3]; val dy = y - rig.segC[s * 3 + 1]; val dz = z - rig.segC[s * 3 + 2]
                        val rc = rig.segReach[s]
                        if (dx * dx + dy * dy + dz * dz > rc * rc) continue
                    }
                    val d = max(sqrt(segDist2(rig, s, x, y, z)) - rig.segR[s], 0f) + EPS
                    val wt = 1f / (d * d * d)
                    if (wt <= bw[K - 1]) continue
                    var j = K - 1
                    while (j > 0 && bw[j - 1] < wt) { bw[j] = bw[j - 1]; bi[j] = bi[j - 1]; j-- }
                    bw[j] = wt; bi[j] = s
                }
                if (bw[0] > 0f) break
            }
            var sum = 0f
            for (j in 0 until K) sum += bw[j]
            val o = v * K
            if (sum <= 0f) { ix[o] = 0; w[o] = 1f; continue }
            for (j in 0 until K) { ix[o + j] = bi[j]; w[o + j] = bw[j] / sum }
        }
        return Wt(grp, nv, ix, w)
    }

    // ---------- aplicação ----------
    /** true se algum slider tem valor (≠0) */
    fun any(vals: FloatArray): Boolean { for (v in vals) if (v != 0f) return true; return false }

    /**
     * Deforma [src] (posições de repouso em unidades do app, 3 floats por vértice) em [dst].
     * [vals]: valor de cada slider de -1 a 1 (índice = id da tabela). [grp]: grupo do corpo ("af","am","tf","tm","ef","em","cu","pu").
     * [k]: unidades do app por metro do Sims (altura do pescoço do corpo / altura do pescoço do rig). [key]: identidade da malha (cache de pesos).
     */
    fun warp(src: FloatArray, dst: FloatArray, nv: Int, vals: FloatArray, grp: String, k: Float, key: FloatArray): Boolean {
        val rig = rigFor(grp)
        if (!ready || rig == null || !any(vals)) return false
        val acc = FloatArray(rig.n * 10)
        for (sl in sliders) {
            val t = if (sl.id < vals.size) vals[sl.id] else 0f
            if (t == 0f) continue
            val arr = sl.dirs[grp] ?: continue
            var d = arr[if (t > 0f) 0 else 1]
            var sg = 1f
            if (d == null) { d = arr[if (t > 0f) 1 else 0]; sg = -1f }
            if (d == null) continue
            val kk = abs(t) * sg
            for ((j, nm) in d.bone.withIndex()) {
                val bi = rig.idx[nm] ?: continue
                for (c in 0 until 10) acc[bi * 10 + c] += d.v[j * 10 + c] * kk
            }
        }
        val w2 = FloatArray(rig.n * 16)
        world(rig, acc, w2)
        val ns = rig.segBone.size
        val m = FloatArray(ns * 16)
        for (s in 0 until ns) { val b = rig.segBone[s]; mul(w2, b * 16, rig.iw0, b * 16, m, s * 16) }
        // posição dos pés (footOffset/footWorld do jogo deslocam o pé em coordenadas do mundo)
        for (side in arrayOf("L", "R")) {
            var tx = 0f; var ty = 0f; var tz = 0f
            for (nm in arrayOf(side + "_footOffset", side + "_footWorld")) {
                val bi = rig.idx[nm] ?: continue
                tx += acc[bi * 10]; ty += acc[bi * 10 + 1]; tz += acc[bi * 10 + 2]
            }
            if (tx != 0f || ty != 0f || tz != 0f) for (s in 0 until ns) {
                val n = rig.segNames[s]
                if (n == "b__${side}_Foot__" || n == "b__${side}_Toe__") { m[s * 16 + 3] += tx; m[s * 16 + 7] += ty; m[s * 16 + 11] += tz }
            }
        }
        // os pés continuam no chão: sobe/desce pelo deslocamento médio das pontas dos pés
        var gy = 0f; var gn = 0
        for (side in arrayOf("L", "R")) {
            val bi = rig.idx["b__${side}_Toe__"] ?: continue
            var ty = 0f
            val fo = rig.idx[side + "_footOffset"]; val fw = rig.idx[side + "_footWorld"]
            if (fo != null) ty += acc[fo * 10 + 1]
            if (fw != null) ty += acc[fw * 10 + 1]
            gy += w2[bi * 16 + 7] - rig.w0[bi * 16 + 7] + ty; gn++
        }
        val ground = if (gn > 0) gy / gn * k else 0f

        var wt = synchronized(cache) { cache[key] }
        if (wt == null || wt.grp != grp || wt.nv != nv) {
            wt = computeW(rig, grp, src, nv, k)
            synchronized(cache) { cache[key] = wt }
        }
        val inv = 1f / k
        for (v in 0 until nv) {
            val x = src[v * 3] * inv; val y = src[v * 3 + 1] * inv; val z = src[v * 3 + 2] * inv
            var ox = 0f; var oy = 0f; var oz = 0f
            val o = v * K
            for (j in 0 until K) {
                val w = wt.w[o + j]
                if (w == 0f) continue
                val mo = wt.ix[o + j] * 16
                ox += w * (m[mo] * x + m[mo + 1] * y + m[mo + 2] * z + m[mo + 3])
                oy += w * (m[mo + 4] * x + m[mo + 5] * y + m[mo + 6] * z + m[mo + 7])
                oz += w * (m[mo + 8] * x + m[mo + 9] * y + m[mo + 10] * z + m[mo + 11])
            }
            dst[v * 3] = ox * k; dst[v * 3 + 1] = oy * k - ground; dst[v * 3 + 2] = oz * k
        }
        return true
    }
}
