package com.vinicius.meular
import android.content.res.AssetManager
import kotlin.math.*

fun main() {
    Glb.assets = AssetManager("/home/claude/work/merged/app/src/main/assets")
    for (id in listOf("decor_vaso_costela", "fis_caixa_papelao", "fis_bola", "int_poltrona", "int_aparador")) {
        val g = Glb.get(id)!!
        g.ensureGl()
        println("== $id: ${g.nodes.size} nós, animados=${g.animated.toList()} occ=${g.occSlot} cols=${g.cols.map { it.name + "(" + it.shape + ")" }}")
        println("   bounds=${g.bounds.map { "%.3f".format(it) }} foot(static)=${g.foot(false).map { "%.3f".format(it) }} foot(dyn)=${g.foot(true).map { "%.3f".format(it) }}")
        println("   meta.nome=${g.meta.optString("nome")} fisica=${g.meta.optJSONObject("fisica")?.optString("tipo")} massa=${g.meta.optJSONObject("fisica")?.optDouble("massa", -1.0)}")
        for (k in g.animated) { val n = g.nodes[k]; println("   anim ${n.name}: tipo=${n.aType} eixo=${n.ax.toList()} ${n.aMin}..${n.aMax} dur=${n.aDur} bb=${n.bb.map { "%.3f".format(it) }} v(0)=${n.value(0f)} v(1)=${n.value(1f)} alca=${n.anim?.optJSONArray("alca")?.let { a -> (0 until a.length()).map { a.optDouble(it) } }}") }
        g.point("IP_sentar")?.let { println("   IP_sentar=${it.toList()} aprox=${g.extraPoint("IP_sentar", "aproximacao")?.toList()} inicio=${g.extraPoint("IP_sentar", "inicio")?.toList()} assento=${g.extraFloat("IP_sentar", "assento_y", -1f)}") }
        val tex = g.nodes.sumOf { it.mesh?.parts?.size ?: 0 }
        println("   partes GL=$tex vértices=${g.nodes.sumOf { n -> n.prims.sumOf { it.nv } }}")
        val sm = g.staticMesh(0.5f, 0.5f); println("   staticMesh partes=${sm.parts.size}")
    }
    // hinge check: porta_E a 100° — onde vai a borda da porta?
    val ap = Glb.get("int_aparador")!!
    val i = ap.index("porta_E"); val n = ap.nodes[i]
    val m = FloatArray(16); n.local(m, n.value(1f))
    val x = n.bb[3]; val z = n.bb[5]
    println("porta_E aberta: canto (${n.bb[3]}, ${n.bb[5]}) local -> (%.3f, %.3f) relativo à dobradiça".format(m[0] * x + m[8] * z + m[12] - n.t[0], m[2] * x + m[10] * z + m[14] - n.t[2]))
    val x2 = n.bb[0]; println("   canto livre (${n.bb[0]}): -> (%.3f, %.3f)".format(m[0] * x2 + m[8] * z + m[12] - n.t[0], m[2] * x2 + m[10] * z + m[14] - n.t[2]))
    physicsTests()
}

fun world(statics: List<SBox>, px: Float = 50f, pz: Float = 50f, vx: Float = 0f, vz: Float = 0f, run: Boolean = false) =
    Physics.World(statics, 6f, 5f, false, { _, _ -> 0f }, px, pz, vx, vz, run, true)

fun mkBox(it: Item, x: Float, y: Float, z: Float): Body {
    val b = Body(it, false, 0.2f, 0.15f, 0.16f, 0.15f, 1.2f, 0.62f, 0.12f, 0.08f, 0.25f, 0f)
    b.p[0] = x; b.p[1] = y; b.p[2] = z; return b
}
fun mkBall(it: Item, x: Float, y: Float, z: Float): Body {
    val b = Body(it, true, 0.11f, 0.11f, 0.11f, 0.11f, 0.35f, 0.55f, 0.62f, 0.03f, 0.06f, 0.012f)
    b.p[0] = x; b.p[1] = y; b.p[2] = z; return b
}
fun fmt(b: Body) = "w=(%.2f %.2f %.2f) p=(%.3f, %.3f, %.3f) v=(%.2f %.2f %.2f) sleep=%s q=(%.2f %.2f %.2f %.2f)".format(b.w[0], b.w[1], b.w[2], b.p[0], b.p[1], b.p[2], b.v[0], b.v[1], b.v[2], b.sleep, b.q[0], b.q[1], b.q[2], b.q[3])

fun run(sec: Float, w: () -> Physics.World, every: Float = 0f, tag: String = "") {
    var t = 0f; var next = every
    while (t < sec) { Physics.step(1f / 60f, w()); t += 1f / 60f
        if (every > 0 && t >= next) { next += every; println("  t=%.2f %s".format(t, Physics.bodies.joinToString(" | ") { fmt(it) })) } }
}

fun physicsTests() {
    println("\n--- 1) caixa cai de 0,6 m no piso")
    Physics.bodies.clear()
    val b1 = mkBox(Item(Type.CAIXA, 2, 2), 2.5f, 0.75f, 2.5f); Physics.bodies.add(b1)
    run(2f, { world(emptyList()) }, 0.25f)
    println("  esperado: y=0,150 parada e dormindo -> ${fmt(b1)}")

    println("\n--- 2) caixa inclinada 30° cai e assenta numa face")
    Physics.bodies.clear()
    val b2 = mkBox(Item(Type.CAIXA, 2, 2), 2.5f, 0.6f, 2.5f); val a = Math.toRadians(30.0) / 2
    b2.q[0] = sin(a).toFloat(); b2.q[3] = cos(a).toFloat(); b2.updR(); Physics.bodies.add(b2)
    run(3f, { world(emptyList()) }, 0.5f)
    println("  -> ${fmt(b2)} (y deve ser 0,15 ou 0,16/0,20 conforme a face)")

    println("\n--- 3) caixa em cima da mesa (tampo 0,75), personagem empurra para a borda")
    Physics.bodies.clear()
    val table = SBox(1.0f, 0f, 1.0f, 2.0f, 0.75f, 2.0f)
    val b3 = mkBox(Item(Type.CAIXA, 1, 1), 1.75f, 0.92f, 1.5f); Physics.bodies.add(b3)
    run(1f, { world(listOf(table)) })
    println("  pousou: ${fmt(b3)}")
    // personagem a 0,5 m à esquerda, andando para +x a 1,7 m/s (para na borda da mesa: x = 1.0 - 0.24)... aqui chega pelo lado
    var ppx = 1.3f
    var t = 0f
    while (t < 3f) { val pv = if (ppx < 1.62f) 1.0f else 0f; ppx += pv / 60f; Physics.step(1f / 60f, world(listOf(table), ppx, 1.5f, pv, 0f)); t += 1f / 60f }
    println("  depois de empurrar: ${fmt(b3)}  (esperado: caiu da mesa, x>2,0, y≈0,15..0,2 no piso)")

    println("\n--- 4) bola cai de 1 m (quica) e para")
    Physics.bodies.clear()
    val b4 = mkBall(Item(Type.BOLA, 3, 3), 3.5f, 1.0f, 3.5f); Physics.bodies.add(b4)
    var maxB = 0f; var tt = 0f; var falling = true; var bounces = 0; var lastVy = 0f
    while (tt < 4f) { Physics.step(1f / 60f, world(emptyList())); tt += 1f / 60f
        if (lastVy < 0 && b4.v[1] > 0) { bounces++ }
        if (bounces == 1 && b4.v[1] < 0 && lastVy >= 0) maxB = b4.p[1]
        lastVy = b4.v[1] }
    println("  quiques=$bounces altura do 1º quique=%.3f (esperado ~0,11+0,89*0,62²≈0,45) final ${fmt(b4)}".format(maxB))

    println("\n--- 5) personagem correndo chuta a bola")
    Physics.bodies.clear()
    val b5 = mkBall(Item(Type.BOLA, 3, 3), 3.0f, 0.11f, 2.5f); Physics.bodies.add(b5)
    run(0.5f, { world(emptyList()) })
    var cx = 2.0f; tt = 0f; var maxV = 0f
    while (tt < 4f) { val pv = if (tt < 0.5f) 3.2f else 0f; cx += pv / 60f; Physics.step(1f / 60f, world(emptyList(), cx, 2.5f, pv, 0f, pv > 0)); tt += 1f / 60f; maxV = max(maxV, b5.v[0]) }
    println("  velocidade máx da bola %.2f m/s; final ${fmt(b5)} (bola rolou e parou; bateu na parede x=6 se passou)".format(maxV))

    println("\n--- 6) duas caixas empilhadas")
    Physics.bodies.clear()
    val c1 = mkBox(Item(Type.CAIXA, 2, 2), 2.5f, 0.16f, 2.5f); val c2 = mkBox(Item(Type.CAIXA, 2, 2), 2.55f, 0.6f, 2.5f)
    Physics.bodies.add(c1); Physics.bodies.add(c2)
    run(3f, { world(emptyList()) }, 1f)
    println("  baixo ${fmt(c1)}\n  cima  ${fmt(c2)}  (esperado: y 0,15 e 0,45)")

    println("\n--- 6b) caixa cai girada 40° sobre outra")
    Physics.bodies.clear()
    val d1 = mkBox(Item(Type.CAIXA, 2, 2), 2.5f, 0.15f, 2.5f); val d2 = mkBox(Item(Type.CAIXA, 2, 2), 2.5f, 0.7f, 2.5f); d2.setYaw(40f)
    Physics.bodies.add(d1); Physics.bodies.add(d2)
    run(3f, { world(emptyList()) })
    println("  baixo ${fmt(d1)}\n  cima  ${fmt(d2)}  (esperado: cima y≈0,45)")
    println("\n--- 6c) bola cai sobre a caixa")
    Physics.bodies.clear()
    val e1 = mkBox(Item(Type.CAIXA, 2, 2), 2.5f, 0.15f, 2.5f); val e2 = mkBall(Item(Type.BOLA, 2, 2), 2.5f, 1.0f, 2.5f)
    Physics.bodies.add(e1); Physics.bodies.add(e2)
    run(4f, { world(emptyList()) })
    println("  caixa ${fmt(e1)}\n  bola  ${fmt(e2)}  (a bola quica na caixa e acaba rolando para o chão ou parada em cima)")
    println("\n--- 7) bola encostada na parede x=6 não atravessa")
    Physics.bodies.clear()
    val b7 = mkBall(Item(Type.BOLA, 3, 3), 5.5f, 0.11f, 2.5f); b7.v[0] = 6f; Physics.bodies.add(b7)
    run(2f, { world(emptyList()) })
    println("  ${fmt(b7)} (x <= 5,89)")
}
