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


    /** Largura, fundo e pé-direito do prédio de cada profissão. */
    fun size(id: String): Triple<Float, Float, Float> = when (id) {
        "medico" -> Triple(34f, 26f, 4.2f); "juiz" -> Triple(28f, 24f, 5f); "prefeito" -> Triple(30f, 22f, 5f); "empresario" -> Triple(26f, 20f, 4.2f)
            "professor" -> Triple(30f, 22f, 3.8f); "policial" -> Triple(26f, 22f, 4.0f); "bombeiro" -> Triple(26f, 22f, 4.6f); "repositor" -> Triple(34f, 26f, 4.6f); "lixeiro" -> Triple(26f, 20f, 5.2f)
            "frentista" -> Triple(14f, 10f, 3.6f); "mecanico" -> Triple(22f, 16f, 5.0f); "entregador" -> Triple(22f, 16f, 4.6f); "programador" -> Triple(24f, 18f, 3.8f)
            "diarista" -> Triple(16f, 13f, 3.4f); "atendente" -> Triple(18f, 14f, 3.6f); "advogado" -> Triple(18f, 15f, 3.6f)
            else -> Triple(20f, 15f, 3.6f)
        }

    fun build(g: CityGeo.Gen, u: Town.Urban, ui: Int): Float {
        val job = Jobs.byId(u.type.removePrefix("job:")) ?: return 1f
        val r = City.Rng(ui * 4513 + 7)
        // frente para a rua mais perto (só frente em z, que é o que a porta aceita)
        val fz = if (Town.clearance((u.x0 + u.x1) / 2, u.z1 + 3f) < Town.clearance((u.x0 + u.x1) / 2, u.z0 - 3f)) 1f else -1f
        val front = if (fz > 0) u.z1 else u.z0
        val (bw0, bd0, hh) = size(job.id)
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
        val (fm, fc) = when (job.id) {
            "lixeiro", "mecanico", "bombeiro", "entregador" -> Pair(Mt.STONE, "#A9A9A6")
            "medico", "enfermeiro", "atendente", "repositor", "frentista", "programador", "engenheiro", "policial" -> Pair(Mt.TILE, "#EDEBE6")
            "advogado", "juiz", "empresario", "prefeito" -> Pair(Mt.STONE, "#E4DCCB")
            "professor" -> Pair(Mt.TILE, "#E2E6D8")
            else -> Pair(Mt.FLOOR_L, "#E7DCC8")
        }
        A.m(fm, if (fm == Mt.STONE) 0.6f else 0.6f); A.box(cx, FL - 0.005f, (z0 + z1) / 2, bw - 0.3f, 0.012f, bd - 0.3f, C(fc))
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
        val inn = JobSpace(g, x0 + 0.3f, x1 - 0.3f, zf - fz * 0.3f, fz, bd - 0.6f, hh, ui)
        JobRooms.fill(inn, job)
        g.end()
        // versão de longe
        g.f.m(mat, 0.6f); g.f.box(cx, FL / 2 + hh / 2, (z0 + z1) / 2, bw, hh + FL, bd, wallC)
        if (floors > 1) { g.f.m(Mt.FACADE, 1f / 3f); g.f.box(cx, FL + hh + (floors - 1) * 1.8f, (z0 + z1) / 2, bw, (floors - 1) * 3.6f, bd, wallC) }
        // extras do terreno por profissão
        extras(g, job.id, cx, x0, x1, zf, zb, fz, u, r)
        return top + 4f
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
