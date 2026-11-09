package com.vinicius.meular

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * Etapa 141: locais de trabalho únicos (um por profissão), com fachada própria, letreiro, porta que abre,
 * terreno arrumado (calçada, canteiros, vagas, mastro) e interior completo, cada um com a sua planta.
 */
object TownJobs {
    private const val CURB = Town.CURB
    private val FL = City.FLOOR

    /** Espaço do prédio: u = x (mundo), v = profundidade a partir da fachada (para dentro). */
    class S(val g: CityGeo.Gen, val x0: Float, val x1: Float, val zf: Float, val fz: Float, val depth: Float, val h: Float) {
        val b get() = g.A
        fun z(v: Float) = zf - fz * v
        val cx get() = (x0 + x1) / 2
        val w get() = x1 - x0
        fun box(u: Float, y: Float, v: Float, su: Float, sy: Float, sv: Float, c: Int, mat: Int = Mt.PLAIN, sc: Float = 1f) { b.m(mat, sc); b.box(u, y + sy / 2, z(v), su, sy, sv, c) }
        fun solid(u0: Float, v0: Float, u1: Float, v1: Float) { val a = z(v0); val c = z(v1); g.solid(min(u0, u1), min(a, c), max(u0, u1), max(a, c)) }
        // móveis
        fun desk(u: Float, v: Float, w: Float = 1.6f, c: Int = C("#8A6A4A")) { box(u, FL + 0.72f, v, w, 0.05f, 0.8f, c, Mt.WOOD, 0.5f); box(u - w / 2 + 0.05f, FL, v, 0.06f, 0.72f, 0.75f, shade(c, -20)); box(u + w / 2 - 0.05f, FL, v, 0.06f, 0.72f, 0.75f, shade(c, -20)); solid(u - w / 2, v - 0.4f, u + w / 2, v + 0.4f) }
        fun pc(u: Float, v: Float) { box(u, FL + 0.77f, v, 0.55f, 0.36f, 0.04f, C("#1C1C1C")); box(u, FL + 0.8f, v - 0.025f, 0.5f, 0.3f, 0.01f, C("#3B6FA8")); box(u, FL + 0.77f, v + 0.18f, 0.45f, 0.02f, 0.15f, C("#2A2A2A")) }
        fun chair(u: Float, v: Float, c: Int = C("#2E3135")) { box(u, FL + 0.42f, v, 0.48f, 0.07f, 0.46f, c, Mt.FABRIC); box(u, FL + 0.45f, v + 0.22f, 0.48f, 0.5f, 0.06f, c, Mt.FABRIC); box(u, FL, v, 0.06f, 0.42f, 0.06f, C("#555555")) }
        fun shelf(u: Float, v: Float, len: Float, alongU: Boolean = true, c: Int = C("#B0B6BC"), goods: Boolean = true) {
            val su = if (alongU) len else 0.45f; val sv = if (alongU) 0.45f else len
            // estante de verdade: painel central, prateleiras e produtos dos dois lados
            box(u, FL, v, if (alongU) su else 0.05f, 1.9f, if (alongU) 0.05f else sv, c, Mt.METAL)
            for (k in 0..4) box(u, FL + 0.08f + k * 0.44f, v, su, 0.04f, sv, shade(c, -15), Mt.METAL)
            if (goods) for (k in 0..3) box(u, FL + 0.12f + k * 0.44f, v, su - 0.08f, 0.3f, sv - 0.06f, C(arrayOf("#D32F2F", "#1976D2", "#FBC02D", "#388E3C", "#F57C00", "#7B1FA2")[Math.floorMod(k + (u * 3).toInt(), 6)]), Mt.GOODS, 0.7f)
            solid(u - su / 2, v - sv / 2, u + su / 2, v + sv / 2)
        }
        fun counter(u0: Float, u1: Float, v: Float, d: Float = 0.7f, c: Int = C("#5A3A22"), top: Int = C("#E8E2D6")) { box((u0 + u1) / 2, FL, v, u1 - u0, 1.0f, d, c, Mt.WOOD, 0.5f); box((u0 + u1) / 2, FL + 1.0f, v, u1 - u0 + 0.06f, 0.05f, d + 0.06f, top, Mt.STONE, 1f); solid(u0, v - d / 2, u1, v + d / 2) }
        fun table(u: Float, v: Float, su: Float = 1.2f, sv: Float = 0.8f, c: Int = C("#9A7350")) { box(u, FL + 0.74f, v, su, 0.05f, sv, c, Mt.WOOD, 0.5f); box(u, FL, v, 0.08f, 0.74f, 0.08f, C("#3B3F44")); solid(u - su / 2, v - sv / 2, u + su / 2, v + sv / 2) }
        fun sofa(u: Float, v: Float, w: Float = 2.2f, c: Int = C("#4A5A6A")) { box(u, FL, v, w, 0.45f, 0.9f, c, Mt.FABRIC); box(u, FL + 0.45f, v + 0.35f, w, 0.45f, 0.2f, c, Mt.FABRIC); solid(u - w / 2, v - 0.45f, u + w / 2, v + 0.45f) }
        fun plant(u: Float, v: Float) { box(u, FL, v, 0.45f, 0.45f, 0.45f, C("#B5643C")); CityGeo.ball(b, u, FL + 0.95f, z(v), 0.42f, C("#3E8E41"), 0.5f, 7) }
        fun board(u: Float, v: Float, w: Float, c: Int = C("#FAFAFA")) { box(u, FL + 1.0f, v, w, 1.2f, 0.04f, c); box(u, FL + 0.95f, v, w + 0.1f, 0.05f, 0.1f, C("#9E9E9E")) }
        fun bed(u: Float, v: Float, c: Int = C("#E8EEF2")) { box(u, FL, v, 1.0f, 0.55f, 2.0f, C("#B0B6BC"), Mt.METAL); box(u, FL + 0.55f, v, 0.95f, 0.15f, 1.95f, c, Mt.FABRIC); box(u, FL + 0.7f, v + 0.75f, 0.6f, 0.12f, 0.35f, C("#FFFFFF"), Mt.FABRIC); solid(u - 0.5f, v - 1f, u + 0.5f, v + 1f) }
        fun lockers(u: Float, v: Float, n: Int, c: Int = C("#5C7A8E")) { for (k in 0 until n) { box(u + (k - (n - 1) / 2f) * 0.5f, FL, v, 0.47f, 1.9f, 0.5f, c, Mt.METAL); box(u + (k - (n - 1) / 2f) * 0.5f + 0.15f, FL + 1.1f, v - 0.26f, 0.04f, 0.12f, 0.02f, C("#DDDDDD")) }; solid(u - n * 0.25f, v - 0.25f, u + n * 0.25f, v + 0.25f) }
        fun wallTo(v: Float, u0: Float, u1: Float, doorU: Float = Float.NaN, c: Int = C("#F2EEE6")) {
            val ops = if (doorU.isNaN()) emptyList() else listOf(CityGeo.Op(doorU, 1.0f, FL, FL + 2.2f, true))
            CityGeo.wall(g, 0, z(v), u0, u1, FL, FL + h, if (fz > 0) -1 else 1, ops, c, c, Mt.PLASTER, 0.12f, true)
            if (doorU.isNaN()) solid(u0, v - 0.08f, u1, v + 0.08f) else { solid(u0, v - 0.08f, doorU - 0.55f, v + 0.08f); solid(doorU + 0.55f, v - 0.08f, u1, v + 0.08f) }
        }
        fun wallAlong(u: Float, v0: Float, v1: Float, doorV: Float = Float.NaN, c: Int = C("#F2EEE6")) {
            val a = min(z(v0), z(v1)); val e = max(z(v0), z(v1))
            val ops = if (doorV.isNaN()) emptyList() else listOf(CityGeo.Op(z(doorV), 1.0f, FL, FL + 2.2f, true))
            CityGeo.wall(g, 1, u, a, e, FL, FL + h, 1, ops, c, c, Mt.PLASTER, 0.12f, true)
            if (doorV.isNaN()) solid(u - 0.08f, v0, u + 0.08f, v1) else { solid(u - 0.08f, v0, u + 0.08f, doorV - 0.55f); solid(u - 0.08f, doorV + 0.55f, u + 0.08f, v1) }
        }
    }

    fun build(g: CityGeo.Gen, u: Town.Urban, ui: Int): Float {
        val job = Jobs.byId(u.type.removePrefix("job:")) ?: return 1f
        val r = City.Rng(ui * 4513 + 7)
        // frente para a rua mais perto (só frente em z, que é o que a porta aceita)
        val fz = if (Town.clearance((u.x0 + u.x1) / 2, u.z1 + 3f) < Town.clearance((u.x0 + u.x1) / 2, u.z0 - 3f)) 1f else -1f
        val front = if (fz > 0) u.z1 else u.z0
        // tamanho do prédio por profissão
        val (bw0, bd0, hh) = when (job.id) {
            "medico" -> Triple(46f, 30f, 4.2f); "juiz" -> Triple(34f, 26f, 5f); "prefeito" -> Triple(40f, 26f, 5f); "empresario" -> Triple(30f, 24f, 4.2f)
            "professor" -> Triple(40f, 26f, 3.8f); "policial", "bombeiro" -> Triple(30f, 24f, 4.4f); "repositor" -> Triple(40f, 30f, 5f); "lixeiro" -> Triple(28f, 20f, 6f)
            "frentista" -> Triple(14f, 10f, 3.6f); "mecanico" -> Triple(24f, 18f, 5.2f); "entregador" -> Triple(24f, 16f, 5f)
            else -> Triple(22f, 16f, 3.8f)
        }
        val bw = min(bw0, u.x1 - u.x0 - 10f); val bd = min(bd0, u.z1 - u.z0 - 16f)
        val set = 7f
        val zf = front - fz * set; val zb = zf - fz * bd
        val cx = (u.x0 + u.x1) / 2
        val x0 = cx - bw / 2; val x1 = cx + bw / 2
        val z0 = min(zf, zb); val z1 = max(zf, zb)
        // terreno: calçado na frente, gramado com árvores em volta, vagas nos lados
        CityGeo.groundBox(g.b, u.x0, u.z0, u.x1, u.z1, Mt.GRASS, 0.3f, C("#CFE8BC"))
        CityGeo.groundBox(g.f, u.x0, u.z0, u.x1, u.z1, Mt.GRASS, 0.3f, C("#CFE8BC"))
        g.b.m(Mt.PAVER, 0.6f); g.b.plane(x0 - 3f, min(zf, front), x1 + 3f, max(zf, front), CURB + 0.012f, C("#E2DCCF"))
        g.b.m(Mt.ASPHALT, 0.3f)
        val pz0 = min(zf, zb) + 1f; val pz1 = max(zf, zb) - 1f
        for (sd in floatArrayOf(-1f, 1f)) {
            val px0 = if (sd < 0) u.x0 + 1f else x1 + 3f; val px1 = if (sd < 0) x0 - 3f else u.x1 - 1f
            if (px1 - px0 > 6f) {
                g.b.plane(px0, pz0, px1, pz1, CURB + 0.012f, C("#CFCFCF"))
                g.b.m(Mt.PLAIN); var zz = pz0 + 1f; while (zz < pz1 - 1f) { g.b.plane(px0 + 0.5f, zz - 0.05f, px0 + 5.5f, zz + 0.05f, CURB + 0.02f, C("#F4F4F4")); g.b.plane(px1 - 5.5f, zz - 0.05f, px1 - 0.5f, zz + 0.05f, CURB + 0.02f, C("#F4F4F4")); zz += 2.6f }
                g.b.m(Mt.ASPHALT, 0.3f)
            }
        }
        for (k in 0 until 6) { val tx = r.r(u.x0 + 3f, u.x1 - 3f); val tz = if (fz > 0) r.r(u.z0 + 2f, z0 - 3f) else r.r(z1 + 3f, u.z1 - 2f); if (abs(tx - cx) > bw / 2 + 2f || (tz > z1 + 2f || tz < z0 - 2f)) { CityGeo.tree(g, tx, tz, r.r(0.8f, 1.1f)); g.solid(tx - 0.3f, tz - 0.3f, tx + 0.3f, tz + 0.3f) } }
        // mastro com bandeira e placa no gramado
        run { val mx = x1 + 2f; val mz = front - fz * 3f; g.b.m(Mt.METAL, 1f); g.b.cyl(mx, CURB, mz, 0.06f, 0.05f, 8f, C("#DDDDDD"), true, 6); g.b.m(Mt.FABRIC, 1f); g.b.box(mx + 0.7f, CURB + 7.3f, mz, 1.3f, 0.85f, 0.03f, C(arrayOf("#1B5E20", "#0D47A1", "#B71C1C", "#F9A825")[job.level - 1])); g.solid(mx - 0.1f, mz - 0.1f, mx + 0.1f, mz + 0.1f) }
        // casca do prédio
        val floors = when (job.level) { 1 -> 1; 2 -> 2; 3 -> 3; else -> 4 }
        val wallC = C(when (job.id) {
            "medico" -> "#F4F6F8"; "juiz" -> "#E8DCC4"; "prefeito" -> "#F1E9D8"; "empresario" -> "#2B2F35"; "policial" -> "#D9DEE5"; "bombeiro" -> "#B8322A"
            "professor" -> "#E9C46A"; "programador" -> "#EDEFF2"; "advogado" -> "#3A3330"; "engenheiro" -> "#C9C2B6"; "lixeiro" -> "#7FA37A"; "entregador" -> "#F2A65A"
            "diarista" -> "#BFE6EE"; "atendente" -> "#F7D66B"; "mecanico" -> "#6E7B85"; "repositor" -> "#F2F0EA"; "enfermeiro" -> "#E4F2EF"; else -> "#E8E1D3" })
        val bd2 = g.begin(x0, z0, x1, z1, job.place)
        val A = g.A; val H = g.H
        A.m(Mt.STONE, 0.6f); A.box(cx, FL / 2, (z0 + z1) / 2, bw, FL, bd, C("#A8A39B"))
        A.m(if (job.level >= 3) Mt.TILE else Mt.FLOOR_L, 0.6f); A.box(cx, FL - 0.005f, (z0 + z1) / 2, bw - 0.3f, 0.012f, bd - 0.3f, C(if (job.level >= 3) "#EDEBE6" else "#E7DCC8"))
        val dw = if (job.level >= 3) 2.4f else 1.6f
        val ops = ArrayList<CityGeo.Op>(); ops.add(CityGeo.Op(cx, dw, FL, FL + 2.7f, true))
        val nwin = max(2, ((bw - 4f) / 3.2f).toInt())
        for (k in 0 until nwin) { val wx = x0 + 1.5f + (bw - 3f) * (k + 0.5f) / nwin; if (abs(wx - cx) > dw / 2 + 1f) ops.add(CityGeo.Op(wx, 1.6f, FL + 0.9f, FL + 2.7f, false)) }
        val mat = when (job.id) { "lixeiro", "mecanico", "entregador" -> Mt.STONE; else -> Mt.PLASTER }
        CityGeo.wall(g, 0, zf, x0, x1, FL, FL + hh, if (fz > 0) 1 else -1, ops, wallC, C("#F2EEE6"), mat, 0.25f)
        CityGeo.wall(g, 0, zb, x0, x1, FL, FL + hh, if (fz > 0) -1 else 1, ops.filter { !it.door }, wallC, C("#F2EEE6"), mat, 0.25f)
        CityGeo.wall(g, 1, x0, z0 + 0.12f, z1 - 0.12f, FL, FL + hh, -1, emptyList(), wallC, C("#F2EEE6"), mat, 0.25f)
        CityGeo.wall(g, 1, x1, z0 + 0.12f, z1 - 0.12f, FL, FL + hh, 1, emptyList(), wallC, C("#F2EEE6"), mat, 0.25f)
        g.solid(x0 - 0.15f, z0 - 0.15f, x0 + 0.2f, z1 + 0.15f); g.solid(x1 - 0.2f, z0 - 0.15f, x1 + 0.15f, z1 + 0.15f); g.solid(x0, zb - 0.2f, x1, zb + 0.2f)
        g.solid(x0, zf - 0.2f, cx - dw / 2 - 0.1f, zf + 0.2f); g.solid(cx + dw / 2 + 0.1f, zf - 0.2f, x1, zf + 0.2f)
        g.door(job.place, cx, zf, fz, dw, 2.7f, 0.25f)
        // andares de cima (fachada) e cobertura
        val top = FL + hh + (floors - 1) * 3.6f
        if (floors > 1) {
            H.m(if (job.id == "empresario" || job.id == "programador" || job.id == "advogado") Mt.METAL else Mt.FACADE, if (job.id == "empresario" || job.id == "programador" || job.id == "advogado") 1f else 1f / 3f, 0f, -(FL + hh) / 3f)
            H.box(cx, FL + hh + (floors - 1) * 1.8f, (z0 + z1) / 2, bw, (floors - 1) * 3.6f, bd, if (job.id == "empresario" || job.id == "programador" || job.id == "advogado") C("#3F5F6E") else wallC)
        }
        H.m(Mt.STONE, 0.5f); H.box(cx, top + 0.3f, (z0 + z1) / 2, bw + 0.3f, 0.6f, bd + 0.3f, shade(wallC, -25))
        H.m(Mt.PLASTER, 0.4f); H.box(cx, FL + hh - 0.05f, (z0 + z1) / 2, bw - 0.4f, 0.1f, bd - 0.4f, C("#F7F7F5"))   // forro do térreo
        // marquise e letreiro
        H.m(Mt.METAL, 1f); H.box(cx, FL + 2.95f, zf + fz * 1.3f, dw + 3f, 0.16f, 2.6f, C("#3B3F44"))
        H.m(Mt.PLAIN); H.box(cx, FL + 2.86f, zf + fz * 1.3f, dw + 2.6f, 0.02f, 2.3f, C("#FFF6D8"), false)
        val si = City.signIdx(job.sign)
        Signs.mount(H, si, cx, FL + hh - 1.0f, zf, fz, min(bw - 2f, 12f), 0.95f)
        g.place(City.Place(job.place, cx, zf + fz * 4f, C(arrayOf("#2E7D32", "#1565C0", "#C62828", "#F9A825")[job.level - 1]), job.name.first()))
        // interior
        val inn = S(g, x0 + 0.3f, x1 - 0.3f, zf - fz * 0.3f, fz, bd - 0.6f, hh)
        decorate(inn, job, r)
        when (job.id) {
            "diarista" -> diarista(inn); "lixeiro" -> lixeiro(inn); "atendente" -> lanchonete(inn); "entregador" -> entregas(inn); "frentista" -> posto(inn, g, cx, zf, fz, r); "repositor" -> mercado(inn)
            "professor" -> escola(inn); "secretario" -> escritorio(inn); "policial" -> delegacia(inn); "bombeiro" -> quartel(inn); "mecanico" -> oficina(inn); "enfermeiro" -> clinica(inn)
            "medico" -> hospital(inn); "advogado" -> advocacia(inn); "juiz" -> forum(inn); "engenheiro" -> construtora(inn); "programador" -> tech(inn); "empresario" -> sede(inn); else -> prefeitura(inn)
        }
        g.end()
        // versão de longe
        g.f.m(mat, 0.6f); g.f.box(cx, FL / 2 + hh / 2, (z0 + z1) / 2, bw, hh + FL, bd, wallC)
        if (floors > 1) { g.f.m(Mt.FACADE, 1f / 3f); g.f.box(cx, FL + hh + (floors - 1) * 1.8f, (z0 + z1) / 2, bw, (floors - 1) * 3.6f, bd, wallC) }
        // extras do terreno por profissão
        extras(g, job.id, cx, x0, x1, zf, zb, fz, u, r)
        return top + 4f
    }

    /** Acabamento comum a todos: luminárias no forro, rodapé, quadros, relógio, extintor, bebedouro, lixeiras, ar-condicionado, vasos nos cantos, capacho. */
    private fun decorate(s: S, job: Jobs.Job, r: City.Rng) {
        val d = s.depth; val yc = FL + s.h - 0.12f
        val accent = C(arrayOf("#2E7D32", "#1565C0", "#C62828", "#C9A227")[job.level - 1])
        // luminárias embutidas em grade
        var u = s.x0 + 2f
        while (u < s.x1 - 1f) { var v = 1.8f; while (v < d - 0.8f) { s.box(u, yc, v, 1.2f, 0.06f, 0.6f, C("#FFFBEA")); v += 3.4f }; u += 3.4f }
        // rodapé nas laterais e no fundo
        s.box(s.x0 + 0.04f, FL, d / 2, 0.06f, 0.12f, d, C("#8D8D8D")); s.box(s.x1 - 0.04f, FL, d / 2, 0.06f, 0.12f, d, C("#8D8D8D")); s.box(s.cx, FL, d - 0.04f, s.w, 0.12f, 0.06f, C("#8D8D8D"))
        // quadros nas paredes laterais (cores diferentes) e faixa da cor do nível
        var v = 2.5f; var k = 0
        while (v < d - 1.5f) {
            for (side in floatArrayOf(-1f, 1f)) {
                val wu = if (side < 0) s.x0 + 0.07f else s.x1 - 0.07f
                s.box(wu, FL + 1.4f, v, 0.04f, 0.8f, 1.1f, C("#3B3F44")); s.box(wu - side * 0.02f, FL + 1.47f, v, 0.03f, 0.66f, 0.96f, C(arrayOf("#E57373", "#64B5F6", "#81C784", "#FFD54F", "#BA68C8", "#4DB6AC", "#FF8A65")[(k + job.level) % 7]))
            }
            v += 4.2f; k++
        }
        s.box(s.x0 + 0.05f, FL + 0.95f, d / 2, 0.04f, 0.08f, d - 0.4f, accent); s.box(s.x1 - 0.05f, FL + 0.95f, d / 2, 0.04f, 0.08f, d - 0.4f, accent)
        // relógio, extintor, bebedouro, lixeiras, ar-condicionado
        s.box(s.cx, FL + s.h - 0.9f, d - 0.06f, 0.4f, 0.4f, 0.04f, C("#FAFAFA")); s.box(s.cx, FL + s.h - 0.9f, d - 0.09f, 0.05f, 0.18f, 0.01f, C("#212121"))
        s.box(s.x0 + 0.25f, FL + 0.2f, 0.9f, 0.18f, 0.55f, 0.18f, C("#D32F2F")); s.box(s.x0 + 0.12f, FL + 1.1f, 0.9f, 0.02f, 0.3f, 0.3f, C("#D32F2F"))
        s.box(s.x1 - 0.4f, FL, 1.2f, 0.32f, 1.0f, 0.32f, C("#ECEFF1"), Mt.METAL); s.box(s.x1 - 0.4f, FL + 1.0f, 1.2f, 0.26f, 0.4f, 0.26f, C("#90CAF9")); s.solid(s.x1 - 0.6f, 1.0f, s.x1 - 0.2f, 1.4f)
        for (q in 0..1) s.box(if (q == 0) s.x0 + 0.5f else s.x1 - 0.5f, FL, d - 0.5f, 0.35f, 0.5f, 0.35f, C("#546E7A"), Mt.METAL)
        s.box(s.x0 + 0.12f, FL + s.h - 0.7f, d * 0.5f, 0.22f, 0.3f, 1.0f, C("#F5F5F5")); s.box(s.x1 - 0.12f, FL + s.h - 0.7f, d * 0.5f, 0.22f, 0.3f, 1.0f, C("#F5F5F5"))
        // vasos nos cantos da frente e capacho na entrada
        s.plant(s.x0 + 0.6f, d - 0.6f); s.plant(s.x1 - 0.6f, d - 0.6f)
        s.box(s.cx, FL, 0.9f, 2.2f, 0.015f, 1.2f, shade(accent, -20), Mt.RUG, 1f)
        if (r.chance(2f)) Unit
    }

    // ------------------------------------------------------------ interiores (cada um com a sua planta)

    private fun diarista(s: S) {
        val w = s.w; val d = s.depth
        s.counter(s.cx - 2.5f, s.cx + 2.5f, 3f); s.pc(s.cx - 1f, 2.8f); s.chair(s.cx - 1f, 3.9f)
        s.sofa(s.x0 + 2f, 1.5f, 2.2f, C("#00ACC1")); s.plant(s.x0 + 0.6f, 0.6f); s.plant(s.x1 - 0.6f, 0.6f)
        s.wallTo(d * 0.62f, s.x0, s.x1, s.cx)
        // depósito: estantes com produtos de limpeza, carrinhos, baldes
        for (k in 0..2) s.shelf(s.x0 + 2f + k * 3.5f, d - 0.6f, 3f)
        for (k in 0..3) { s.box(s.x1 - 1.5f - k * 1.3f, FL, d * 0.75f, 0.9f, 0.9f, 0.6f, C("#1976D2"), Mt.PLASTER); s.box(s.x1 - 1.5f - k * 1.3f, FL + 0.9f, d * 0.75f, 0.2f, 0.6f, 0.04f, C("#FBC02D")) }
        s.lockers(s.cx, d * 0.6f, 6, C("#80DEEA"))
    }

    private fun lixeiro(s: S) {
        val d = s.depth
        // garagem dos caminhões ocupa a parte da frente; vestiário e escritório no fundo
        s.box(s.cx, FL, 4.5f, 2.5f, 3.2f, 7.5f, C("#2E7D32"), Mt.METAL); s.box(s.cx, FL + 0.5f, 0.6f, 2.4f, 1.8f, 1.2f, C("#E8E8E8"), Mt.METAL); s.solid(s.cx - 1.3f, 0.5f, s.cx + 1.3f, 8.3f)
        s.box(s.cx + 4f, FL, 4.5f, 2.5f, 3.2f, 7.5f, C("#388E3C"), Mt.METAL); s.solid(s.cx + 2.7f, 0.7f, s.cx + 5.3f, 8.3f)
        s.wallTo(d * 0.6f, s.x0, s.x1, s.x0 + 3f)
        s.lockers(s.x0 + 4f, d - 0.6f, 8, C("#2E7D32")); s.table(s.cx + 3f, d * 0.8f, 2.4f, 1f); s.chair(s.cx + 2f, d * 0.8f + 0.9f); s.chair(s.cx + 4f, d * 0.8f + 0.9f)
        s.board(s.x1 - 3f, d - 0.25f, 2.6f, C("#E8F5E9"))
        for (k in 0..5) s.box(s.x1 - 1.2f, FL, 1.5f + k * 1.2f, 0.9f, 1.1f, 0.9f, C(arrayOf("#2E7D32", "#1565C0", "#F9A825", "#C62828")[k % 4]), Mt.PLASTER)
    }

    private fun lanchonete(s: S) {
        val d = s.depth
        s.counter(s.x0 + 2f, s.x1 - 2f, d * 0.55f, 0.8f, C("#C0392B"), C("#F2F2F2"))
        s.box(s.cx, FL + 2.2f, d - 0.3f, s.w - 3f, 0.6f, 0.05f, C("#2B2B2B"))   // cardápio
        for (k in 0..3) s.box(s.x0 + 3f + k * (s.w - 6f) / 3, FL + 2.25f, d - 0.33f, 1.6f, 0.45f, 0.02f, C(arrayOf("#F9A825", "#E53935", "#43A047", "#FB8C00")[k]))
        s.box(s.cx - 3f, FL, d - 0.5f, 2.2f, 0.95f, 0.7f, C("#B0B6BC"), Mt.METAL); s.box(s.cx + 1f, FL, d - 0.5f, 1.6f, 1.8f, 0.7f, C("#D0D4D8"), Mt.METAL); s.box(s.cx + 3.5f, FL, d - 0.5f, 1.2f, 1.5f, 0.6f, C("#C8CCD0"), Mt.METAL)
        s.box(s.cx - 1f, FL + 1.05f, d * 0.55f, 0.4f, 0.4f, 0.4f, C("#212121")); s.box(s.cx + 2f, FL + 1.05f, d * 0.55f, 0.6f, 0.5f, 0.4f, C("#E0E0E0"))   // caixa e máquina de suco
        for (k in 0 until 4) { val tu = s.x0 + 2.5f + k * (s.w - 5f) / 3; s.table(tu, d * 0.25f, 0.9f, 0.9f, C("#F2F2F2")); for (sg in floatArrayOf(-0.7f, 0.7f)) s.chair(tu + sg, d * 0.25f, C("#C0392B")) }
    }

    private fun entregas(s: S) {
        val d = s.depth
        s.counter(s.x0 + 1.5f, s.x0 + 6f, 2.5f); s.pc(s.x0 + 3f, 2.3f); s.chair(s.x0 + 3f, 3.4f)
        for (k in 0 until 4) for (q in 0..1) s.shelf(s.x0 + 9f + k * 3.2f, d * 0.45f + q * 3.5f, 2.6f, true, C("#8D6E63"))
        for (k in 0 until 4) { val mu = s.x1 - 2f - k * 1.6f; s.box(mu, FL + 0.3f, d - 2f, 0.4f, 0.7f, 1.7f, C("#E65100"), Mt.METAL); s.box(mu, FL + 1f, d - 1.3f, 0.5f, 0.45f, 0.45f, C("#FFFFFF")); s.solid(mu - 0.3f, d - 2.9f, mu + 0.3f, d - 1.1f) }
        s.board(s.cx, d - 0.25f, 4f, C("#FFF3E0"))
    }

    private fun posto(s: S, g: CityGeo.Gen, cx: Float, zf: Float, fz: Float, r: City.Rng) {
        // loja de conveniência
        s.counter(s.x0 + 1f, s.x0 + 4f, 2.2f); s.pc(s.x0 + 2f, 2f)
        s.shelf(s.cx + 1f, s.depth * 0.5f, 3f); s.shelf(s.cx + 1f, s.depth * 0.8f, 3f)
        s.box(s.x1 - 0.6f, FL, s.depth * 0.5f, 0.7f, 2f, 3.5f, C("#D0D4D8"), Mt.METAL)
    }

    private fun mercado(s: S) {
        val d = s.depth
        for (k in 0 until 4) s.counter(s.x0 + 2f + k * 3.2f, s.x0 + 3.6f + k * 3.2f, 3f, 0.8f, C("#424242"), C("#BDBDBD"))
        for (k in 0 until 4) s.pc(s.x0 + 2.8f + k * 3.2f, 3f)
        val rows = ((s.w - 6f) / 3.4f).toInt()
        for (k in 0 until rows) s.shelf(s.x0 + 3f + k * 3.4f, d * 0.55f, d * 0.55f, false)
        s.box(s.cx, FL, d - 0.6f, s.w - 3f, 2.0f, 0.8f, C("#E0F2F1"), Mt.METAL); s.solid(s.x0 + 1.5f, d - 1f, s.x1 - 1.5f, d - 0.2f)   // geladeiras do fundo
        for (k in 0 until 6) s.box(s.x1 - 1.5f, FL, 1.5f + k * 0.9f, 0.6f, 0.9f, 0.8f, C("#B0BEC5"), Mt.METAL)   // carrinhos
    }

    private fun escola(s: S) {
        val d = s.depth
        // recepção + corredor no meio + 4 salas de aula
        s.counter(s.cx - 2f, s.cx + 2f, 2f); s.plant(s.x0 + 0.6f, 0.6f)
        s.wallTo(4f, s.x0, s.x1, s.cx)
        val mid = s.cx
        for (sd in floatArrayOf(-1f, 1f)) {
            val ua = if (sd < 0) s.x0 else mid + 1.5f; val ub = if (sd < 0) mid - 1.5f else s.x1
            s.wallAlong(if (sd < 0) ub else ua, 4f, d, (4f + d) / 2)
            s.wallTo((4f + d) / 2, ua, ub)
            for (q in 0..1) {
                val v0 = if (q == 0) 4f else (4f + d) / 2; val v1 = if (q == 0) (4f + d) / 2 else d
                s.board((ua + ub) / 2, v1 - 0.25f, 3.2f, C("#2E5D3A")); s.desk((ua + ub) / 2, v1 - 1.6f, 1.4f)
                for (i in 0 until 3) for (j in 0 until 2) { val su = ua + 1.5f + i * (ub - ua - 3f) / 2; val sv = v0 + 1.4f + j * 1.6f; if (sv < v1 - 2.6f) { s.table(su, sv, 0.9f, 0.6f, C("#D7B98E")); s.chair(su, sv + 0.6f, C("#1565C0")) } }
            }
        }
    }

    private fun escritorio(s: S) {
        val d = s.depth
        s.counter(s.cx - 2.5f, s.cx + 2.5f, 2.5f, 0.7f, C("#37474F"), C("#ECEFF1")); s.pc(s.cx, 2.3f); s.chair(s.cx, 3.4f)
        s.sofa(s.x0 + 2f, 1.3f, 2.4f, C("#546E7A")); s.plant(s.x1 - 0.7f, 0.7f)
        for (i in 0 until 3) for (j in 0 until 2) { val du = s.x0 + 3f + i * (s.w - 6f) / 2; val dv = d * 0.45f + j * 3f; s.desk(du, dv); s.pc(du, dv - 0.1f); s.chair(du, dv + 0.8f) }
        s.wallAlong(s.x1 - 5f, d * 0.7f, d, d * 0.8f, C("#CFD8DC")); s.table(s.x1 - 2.5f, d * 0.85f, 2.6f, 1.2f, C("#5D4037")); for (k in 0..2) s.chair(s.x1 - 3.5f + k, d * 0.85f + 0.9f)
        s.box(s.x0 + 0.5f, FL, d - 0.5f, 0.6f, 1.4f, 2.5f, C("#90A4AE"), Mt.METAL)   // arquivo
    }

    private fun delegacia(s: S) {
        val d = s.depth
        s.counter(s.cx - 3f, s.cx + 3f, 3f, 0.8f, C("#0E2A5C"), C("#ECEFF1")); s.pc(s.cx - 1f, 2.8f); s.pc(s.cx + 1.5f, 2.8f)
        for (k in 0..3) s.chair(s.x0 + 1.5f + k * 0.6f, 1f, C("#455A64"))
        s.wallTo(d * 0.5f, s.x0, s.x1, s.cx)
        // celas com grade no fundo
        val n = 3; val cw = (s.w * 0.55f) / n
        for (k in 0 until n) {
            val ua = s.x1 - (k + 1) * cw; val ub = ua + cw
            s.box(ua, FL, d - 2f, 0.12f, s.h, 4f, C("#B0B6BC"), Mt.PLASTER); s.solid(ua - 0.06f, d - 4f, ua + 0.06f, d)
            var gu = ua + 0.2f; while (gu < ub - 0.1f) { s.box(gu, FL, d - 4f, 0.04f, 2.6f, 0.04f, C("#333333"), Mt.METAL); gu += 0.25f }
            s.solid(ua, d - 4.05f, ub, d - 3.95f)
            s.box((ua + ub) / 2, FL, d - 1f, cw - 0.6f, 0.45f, 0.8f, C("#757575"))
        }
        for (k in 0 until 2) { val du = s.x0 + 2.5f + k * 3.5f; s.desk(du, d * 0.55f); s.pc(du, d * 0.55f - 0.1f); s.chair(du, d * 0.55f + 0.8f) }
        s.lockers(s.x0 + 3f, d - 0.6f, 6, C("#0E2A5C")); s.board(s.x0 + 6f, 5.3f, 3f, C("#ECEFF1"))
    }

    private fun quartel(s: S) {
        val d = s.depth
        // garagem com o caminhão e a ambulância
        s.box(s.cx - 3.5f, FL, d * 0.4f, 2.6f, 3.2f, 8f, C("#C62828"), Mt.METAL); s.box(s.cx - 3.5f, FL + 3.2f, d * 0.4f, 0.6f, 0.2f, 7f, C("#B0B6BC"), Mt.METAL); s.solid(s.cx - 4.9f, d * 0.4f - 4f, s.cx - 2.1f, d * 0.4f + 4f)
        s.box(s.cx + 1.5f, FL, d * 0.4f, 2.3f, 2.6f, 6f, C("#F5F5F5"), Mt.METAL); s.box(s.cx + 1.5f, FL + 1.4f, d * 0.4f - 3.02f, 2.2f, 0.25f, 0.02f, C("#C62828")); s.solid(s.cx + 0.3f, d * 0.4f - 3f, s.cx + 2.7f, d * 0.4f + 3f)
        s.box(s.cx + 5.5f, FL + 0.6f, 1.5f, 0.1f, 0.1f, 3f, C("#B0B6BC"), Mt.METAL)   // cano para escorregar
        s.lockers(s.x0 + 3f, d - 0.6f, 8, C("#C62828")); for (k in 0 until 8) s.box(s.x0 + 1.25f + k * 0.5f, FL + 1.95f, d - 0.6f, 0.4f, 0.35f, 0.4f, C("#FBC02D"))
        s.wallAlong(s.x1 - 6f, d * 0.75f, d, d * 0.85f); s.bed(s.x1 - 1.5f, d - 1.2f, C("#B71C1C")); s.bed(s.x1 - 3.5f, d - 1.2f, C("#B71C1C"))
    }

    private fun oficina(s: S) {
        val d = s.depth
        for (k in 0..1) { val lu = s.x0 + 4f + k * 7f; s.box(lu - 1.2f, FL, d * 0.45f, 0.25f, 1.8f, 4.5f, C("#FFC107"), Mt.METAL); s.box(lu + 1.2f, FL, d * 0.45f, 0.25f, 1.8f, 4.5f, C("#FFC107"), Mt.METAL); s.box(lu, FL + 1.8f, d * 0.45f, 2.6f, 0.15f, 4.5f, C("#3B3F44"), Mt.METAL); s.solid(lu - 1.4f, d * 0.45f - 2.3f, lu + 1.4f, d * 0.45f + 2.3f) }
        s.box(s.x0 + 4f, FL + 1.95f, d * 0.45f, 1.8f, 1.2f, 4.2f, C("#1565C0"), Mt.METAL)   // carro no elevador
        s.box(s.cx + 3f, FL, d - 0.5f, 6f, 1.0f, 0.7f, C("#B71C1C"), Mt.METAL); s.box(s.cx + 3f, FL + 1.0f, d - 0.3f, 6f, 1.2f, 0.05f, C("#424242"))   // bancada e painel de ferramentas
        for (k in 0..5) s.box(s.x1 - 1f, FL + k * 0.25f, 2f, 0.8f, 0.24f, 0.8f, C("#212121"))   // pilha de pneus
        s.counter(s.x1 - 5f, s.x1 - 1.5f, 1.8f); s.pc(s.x1 - 3.5f, 1.6f)
    }

    private fun clinica(s: S) {
        val d = s.depth
        s.counter(s.cx - 2f, s.cx + 2f, 2.5f, 0.7f, C("#00897B"), C("#FFFFFF")); s.pc(s.cx, 2.3f)
        for (k in 0 until 6) s.chair(s.x0 + 1f + k * 0.6f, 1.2f, C("#26A69A")); s.plant(s.x1 - 0.7f, 0.7f)
        s.wallTo(5f, s.x0, s.x1, s.cx)
        val n = 3; val rw = s.w / n
        for (k in 0 until n) { val ua = s.x0 + k * rw; if (k > 0) s.wallAlong(ua, 5f, d, (5f + d) / 2); s.bed(ua + rw / 2 + 1f, d - 1.3f, C("#E0F2F1")); s.desk(ua + rw / 2 - 1.2f, 6.2f, 1.2f, C("#ECEFF1")); s.chair(ua + rw / 2 - 1.2f, 7f) }
    }

    private fun hospital(s: S) {
        val d = s.depth
        s.counter(s.cx - 4f, s.cx + 4f, 4f, 0.8f, C("#FFFFFF"), C("#E3F2FD")); s.pc(s.cx - 2f, 3.8f); s.pc(s.cx + 2f, 3.8f)
        for (i in 0 until 3) for (k in 0 until 6) s.chair(s.x0 + 2f + k * 0.6f, 1.2f + i * 1.1f, C("#1E88E5"))
        s.plant(s.x0 + 0.7f, 0.7f); s.plant(s.x1 - 0.7f, 0.7f)
        s.wallTo(7f, s.x0, s.x1, s.cx)
        // corredor no meio, quartos dos lados com leitos e cortinas
        val mid = s.cx
        for (sd in floatArrayOf(-1f, 1f)) {
            val ua = if (sd < 0) s.x0 else mid + 2f; val ub = if (sd < 0) mid - 2f else s.x1
            s.wallAlong(if (sd < 0) ub else ua, 7f, d, Float.NaN)
            val nr = 3; val rw = (ub - ua) / nr
            for (k in 0 until nr) {
                val ra = ua + k * rw
                if (k > 0) s.wallAlong(ra, 7f, d)
                s.bed(ra + rw / 2, d - 1.6f); s.box(ra + rw / 2 + 0.9f, FL, d - 0.6f, 0.4f, 1.5f, 0.3f, C("#90A4AE"), Mt.METAL)
                s.box(ra + rw / 2, FL + 1.7f, d - 3.1f, rw - 1f, 1.1f, 0.03f, C("#B2DFDB"), Mt.FABRIC)
            }
        }
        // centro cirúrgico no fim do corredor
        s.box(mid, FL, d - 1.5f, 1.4f, 0.9f, 2f, C("#CFD8DC"), Mt.METAL); s.box(mid, FL + 2.6f, d - 1.5f, 1.2f, 0.15f, 1.2f, C("#FFFDE7"))
    }

    private fun advocacia(s: S) {
        val d = s.depth
        s.counter(s.cx - 2f, s.cx + 2f, 2.5f, 0.7f, C("#1A1A1A"), C("#D4AF37")); s.sofa(s.x0 + 2.2f, 1.4f, 2.4f, C("#3E2723")); s.plant(s.x1 - 0.7f, 0.7f)
        s.wallTo(5f, s.x0, s.x1, s.cx, C("#EFE6D8"))
        s.wallAlong(s.cx, 5f, d, (5f + d) / 2, C("#EFE6D8"))
        // sala de reunião (mesa comprida) e sala do sócio (mesa grande, estante de livros)
        s.table(s.x0 + (s.cx - s.x0) / 2, (5f + d) / 2, 4f, 1.4f, C("#4E342E")); for (k in 0..3) { s.chair(s.x0 + (s.cx - s.x0) / 2 - 1.5f + k, (5f + d) / 2 - 1f, C("#3E2723")); s.chair(s.x0 + (s.cx - s.x0) / 2 - 1.5f + k, (5f + d) / 2 + 1f, C("#3E2723")) }
        s.desk(s.cx + (s.x1 - s.cx) / 2, d - 2.5f, 2.2f, C("#3E2723")); s.chair(s.cx + (s.x1 - s.cx) / 2, d - 1.6f, C("#1A1A1A")); s.chair(s.cx + (s.x1 - s.cx) / 2 - 0.6f, d - 3.6f); s.chair(s.cx + (s.x1 - s.cx) / 2 + 0.6f, d - 3.6f)
        for (k in 0..2) s.box(s.cx + 1.5f + k * 1.2f, FL, d - 0.35f, 1.1f, 2.4f, 0.4f, C("#5D4037"), Mt.BOOKS, 0.6f)
    }

    private fun forum(s: S) {
        val d = s.depth
        // saguão com colunas e detector de metal; tribunal no fundo
        for (k in 0..3) s.box(s.x0 + 2f + k * (s.w - 4f) / 3, FL, 3f, 0.6f, s.h, 0.6f, C("#EFE6D8"), Mt.STONE, 0.6f)
        s.box(s.cx, FL, 4.5f, 0.9f, 2.2f, 0.3f, C("#424242"), Mt.METAL); s.box(s.cx + 1.6f, FL, 4.5f, 1.8f, 0.9f, 0.6f, C("#616161"), Mt.METAL)
        s.wallTo(7f, s.x0, s.x1, s.cx, C("#E8DCC4"))
        // tribunal: bancada do juiz elevada, mesas das partes, bancos do público, bandeiras
        s.box(s.cx, FL, d - 1.6f, 6f, 0.45f, 3f, C("#5D4037"), Mt.WOOD, 0.5f); s.box(s.cx, FL + 0.45f, d - 2.4f, 5f, 1.1f, 0.6f, C("#4E342E"), Mt.WOOD, 0.5f); s.solid(s.cx - 3f, d - 3.1f, s.cx + 3f, d - 0.1f)
        s.chair(s.cx, d - 1f, C("#1A1A1A")); s.box(s.cx, FL + 2.4f, d - 0.25f, 1.2f, 1.2f, 0.04f, C("#C9A227"))
        for (sd in floatArrayOf(-1f, 1f)) { s.table(s.cx + sd * 3f, d - 6f, 2.4f, 1f, C("#6D4C41")); s.chair(s.cx + sd * 3f, d - 5.2f); s.box(s.cx + sd * 4.5f, FL, d - 0.6f, 0.06f, 2.6f, 0.06f, C("#C9A227"), Mt.METAL); s.box(s.cx + sd * 4.5f + 0.4f, FL + 1.8f, d - 0.6f, 0.8f, 0.6f, 0.02f, C(if (sd < 0) "#1B5E20" else "#0D47A1"), Mt.FABRIC) }
        for (row in 0 until 3) for (sd in floatArrayOf(-1f, 1f)) s.box(s.cx + sd * 3.5f, FL, 8.5f + row * 1.4f, 4.5f, 0.45f, 0.5f, C("#6D4C41"), Mt.WOOD, 0.5f)
        for (row in 0 until 3) for (sd in floatArrayOf(-1f, 1f)) s.solid(s.cx + sd * 3.5f - 2.25f, 8.25f + row * 1.4f, s.cx + sd * 3.5f + 2.25f, 8.75f + row * 1.4f)
    }

    private fun construtora(s: S) {
        val d = s.depth
        s.counter(s.cx - 2f, s.cx + 2f, 2.3f, 0.7f, C("#F9A825"), C("#FFFFFF"))
        s.box(s.cx - 5f, FL, 1.8f, 2.2f, 0.9f, 1.6f, C("#ECEFF1")); s.box(s.cx - 5f, FL + 0.9f, 1.8f, 1.8f, 0.6f, 1.2f, C("#B0BEC5"))   // maquete
        for (i in 0 until 4) { val du = s.x0 + 2.5f + i * (s.w - 5f) / 3; s.box(du, FL, d * 0.55f, 1.8f, 0.9f, 1.1f, C("#CFD8DC"), Mt.METAL); s.box(du, FL + 0.9f, d * 0.55f, 1.6f, 0.03f, 1f, C("#E3F2FD")); s.chair(du, d * 0.55f + 0.9f); s.solid(du - 0.9f, d * 0.55f - 0.55f, du + 0.9f, d * 0.55f + 0.55f) }
        for (k in 0..5) s.box(s.x0 + 1f + k * 0.5f, FL + 1.6f, d - 0.3f, 0.35f, 0.3f, 0.3f, C(if (k % 2 == 0) "#FBC02D" else "#FFFFFF"))   // capacetes
        s.board(s.cx + 3f, d - 0.25f, 3.4f, C("#E3F2FD"))
    }

    private fun tech(s: S) {
        val d = s.depth
        s.counter(s.cx - 2.2f, s.cx + 2.2f, 2.3f, 0.7f, C("#0D1B2A"), C("#4FC3F7")); s.sofa(s.x0 + 2.5f, 1.5f, 3f, C("#26C6DA")); s.sofa(s.x1 - 2.5f, 1.5f, 3f, C("#AB47BC"))
        // ilhas de mesas com 2 monitores, pufes, mesa de sinuca e máquina de café
        for (i in 0 until 3) for (j in 0 until 2) { val du = s.x0 + 3f + i * (s.w - 6f) / 2; val dv = d * 0.42f + j * 2.6f; s.desk(du, dv, 1.8f, C("#ECEFF1")); s.pc(du - 0.35f, dv - 0.1f); s.pc(du + 0.35f, dv - 0.1f); s.chair(du, dv + 0.8f, C("#212121")) }
        s.table(s.cx, d - 2f, 2.4f, 1.3f, C("#1B5E20")); s.box(s.x1 - 0.6f, FL, d - 0.6f, 0.6f, 1.6f, 0.6f, C("#3E2723"))
        for (k in 0..2) s.box(s.x0 + 1f + k * 1.1f, FL, d - 1f, 0.8f, 0.5f, 0.8f, C(arrayOf("#FF7043", "#66BB6A", "#42A5F5")[k]), Mt.FABRIC)
    }

    private fun sede(s: S) {
        val d = s.depth
        s.counter(s.cx - 3f, s.cx + 3f, 3f, 0.9f, C("#111111"), C("#E8C26E")); s.box(s.cx, FL + 1.2f, d * 0.35f, 4f, 2.5f, 0.1f, C("#C9A227"))   // logo
        s.sofa(s.x0 + 2.5f, 1.6f, 3f, C("#2B2B2B")); s.sofa(s.x1 - 2.5f, 1.6f, 3f, C("#2B2B2B")); s.plant(s.x0 + 0.7f, 4f); s.plant(s.x1 - 0.7f, 4f)
        s.wallTo(d * 0.45f, s.x0, s.x1, s.cx, C("#ECEFF1"))
        // sala de diretoria: mesa enorme de reunião, painel de TV, bar
        s.table(s.cx, d * 0.72f, 7f, 2f, C("#3E2723")); for (k in 0..5) { s.chair(s.cx - 3f + k * 1.2f, d * 0.72f - 1.4f, C("#111111")); s.chair(s.cx - 3f + k * 1.2f, d * 0.72f + 1.4f, C("#111111")) }
        s.box(s.cx, FL + 1.2f, d - 0.3f, 4f, 2.2f, 0.06f, C("#101418")); s.counter(s.x1 - 4f, s.x1 - 1f, d - 1f, 0.7f, C("#4E342E"), C("#212121"))
    }

    private fun prefeitura(s: S) {
        val d = s.depth
        for (k in 0..5) s.box(s.x0 + 2f + k * (s.w - 4f) / 5, FL, 2.5f, 0.6f, s.h, 0.6f, C("#F1E9D8"), Mt.STONE, 0.6f)
        s.counter(s.cx - 4f, s.cx + 4f, 6f, 0.8f, C("#1B3A5C"), C("#ECEFF1")); for (k in 0..3) s.pc(s.cx - 3f + k * 2f, 5.8f)
        s.box(s.cx, FL, d * 0.5f, 3f, 0.6f, 3f, C("#C9A227")); s.box(s.cx, FL + 0.6f, d * 0.5f, 1f, 2.2f, 1f, C("#E0D8C8"), Mt.STONE, 0.6f); s.solid(s.cx - 1.5f, d * 0.5f - 1.5f, s.cx + 1.5f, d * 0.5f + 1.5f)   // monumento do saguão
        s.wallTo(d * 0.7f, s.x0, s.x1, s.cx, C("#F1E9D8"))
        // gabinete do prefeito
        s.desk(s.cx, d - 2.5f, 2.6f, C("#3E2723")); s.chair(s.cx, d - 1.6f, C("#5D4037")); for (sd in floatArrayOf(-1f, 1f)) s.box(s.cx + sd * 2.2f, FL, d - 0.6f, 0.06f, 2.6f, 0.06f, C("#C9A227"), Mt.METAL)
        s.sofa(s.x0 + 3f, d * 0.85f, 2.6f, C("#1B3A5C")); s.box(s.x1 - 1f, FL, d - 0.35f, 1.6f, 2.4f, 0.4f, C("#5D4037"), Mt.BOOKS, 0.6f)
    }

    // ------------------------------------------------------------ terreno de cada lugar

    private fun extras(g: CityGeo.Gen, id: String, cx: Float, x0: Float, x1: Float, zf: Float, zb: Float, fz: Float, u: Town.Urban, r: City.Rng) {
        val b = g.b
        when (id) {
            "frentista" -> { // cobertura das bombas na frente
                val pz = zf + fz * 9f
                b.m(Mt.PLAIN); b.box(cx, CURB + 5.2f, pz, 18f, 0.6f, 10f, C("#0F7A3D")); b.box(cx, CURB + 4.85f, pz, 17.6f, 0.1f, 9.6f, C("#FFFDE7"), false)
                for (sd in floatArrayOf(-4.5f, 4.5f)) { b.m(Mt.METAL, 1f); b.box(cx + sd, CURB + 2.5f, pz, 0.4f, 5f, 0.4f, C("#E0E0E0")); b.box(cx + sd, CURB + 0.9f, pz + 2f, 0.9f, 1.8f, 0.5f, C("#FFE14D")); b.box(cx + sd, CURB + 0.9f, pz - 2f, 0.9f, 1.8f, 0.5f, C("#FFE14D")); g.solid(cx + sd - 0.5f, pz - 2.3f, cx + sd + 0.5f, pz + 2.3f) }
            }
            "lixeiro" -> { for (k in 0..2) { val tx = x1 + 5f + k * 4f; if (tx < u.x1 - 3f) { b.m(Mt.METAL, 1f); b.box(tx, CURB + 1.5f, (zf + zb) / 2, 2.5f, 3f, 7.5f, C("#2E7D32")); g.solid(tx - 1.3f, (zf + zb) / 2 - 3.8f, tx + 1.3f, (zf + zb) / 2 + 3.8f) } } }
            "bombeiro", "policial" -> { // viaturas estacionadas na frente
                for (k in 0..1) { val vx = x0 - 4f - k * 3f; if (vx > u.x0 + 2f) { b.m(Mt.METAL, 1f); b.box(vx, CURB + 0.75f, zf + fz * 3f, 1.9f, 1.5f, 4.6f, C(if (id == "policial") "#FFFFFF" else "#C62828")); b.box(vx, CURB + 1.6f, zf + fz * 3f, 1.2f, 0.18f, 0.4f, C("#1565C0")); g.solid(vx - 1f, zf + fz * 3f - 2.3f, vx + 1f, zf + fz * 3f + 2.3f) } }
            }
            "medico" -> { // heliponto no telhado e entrada de ambulância
                b.m(Mt.PLAIN); b.box(x1 + 4f, CURB + 0.8f, zf + fz * 3f, 2.3f, 1.6f, 5.5f, C("#FFFFFF")); b.box(x1 + 4f, CURB + 1.0f, zf + fz * 0.24f, 2.2f, 0.25f, 0.02f, C("#C62828")); g.solid(x1 + 2.8f, zf + fz * 3f - 2.8f, x1 + 5.2f, zf + fz * 3f + 2.8f)
            }
            "professor" -> { // quadra e playground ao lado
                val qx = if (x1 + 18f < u.x1) x1 + 10f else x0 - 10f
                b.m(Mt.PLAIN); b.plane(qx - 7f, min(zf, zb) + 1f, qx + 7f, max(zf, zb) - 1f, CURB + 0.02f, C("#3E6FA8"))
            }
            "prefeito", "juiz" -> { // escadaria e colunas na fachada
                b.m(Mt.STONE, 0.6f); for (k in 0..3) b.box(cx, CURB + k * 0.2f + 0.1f, zf + fz * (2.2f - k * 0.5f), 14f - k * 0.6f, 0.2f, 2f, C("#E0D8C8"))
                for (k in 0..5) { val px = cx - 6f + k * 2.4f; if (abs(px - cx) < 1.6f) continue; b.m(Mt.PLAIN); b.cyl(px, CURB, zf + fz * 1.6f, 0.4f, 0.4f, 7.5f, C("#F5F0E6"), true, 12); g.solid(px - 0.45f, zf + fz * 1.6f - 0.45f, px + 0.45f, zf + fz * 1.6f + 0.45f) }
                b.m(Mt.PLAIN); b.box(cx, CURB + 7.6f, zf + fz * 1.6f, 15f, 0.8f, 1.6f, C("#F5F0E6"))
            }
            else -> {}
        }
    }
}
