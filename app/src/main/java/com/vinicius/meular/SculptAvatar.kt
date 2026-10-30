package com.vinicius.meular

import com.vinicius.meular.sculpt.Figure
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicInteger

/**
 * Ponte entre o [Avatar] (dados salvos) e o motor de escultura em Java (pacote sculpt):
 * corpo, rosto, mãos, cabelo, roupas e óculos como superfícies contínuas e lisas.
 */
object SculptAvatar {
    private fun at(arr: IntArray, i: Int): Int = arr[i.coerceIn(0, arr.size - 1)]

    private fun spec(a: Avatar): Figure.Spec {
        val s = Figure.Spec()
        s.female = a.female
        s.build = a.body.coerceIn(0, 2)
        s.hair = a.hair.coerceIn(0, AvaPal.HAIR_N.size - 1)
        s.top = a.top.coerceIn(0, AvaPal.TOP_N.size - 1)
        s.bottom = a.bottom.coerceIn(0, AvaPal.BOT_N.size - 1)
        s.glasses = a.glasses.coerceIn(0, AvaPal.GLASS_N.size - 1)
        s.beard = a.beard.coerceIn(0, AvaPal.BEARD_N.size - 1)
        return s
    }

    private fun pal(a: Avatar): Figure.Pal {
        val p = Figure.Pal()
        val hair = at(AvaPal.HAIR, a.hairC)
        p.skin = at(AvaPal.SKIN, a.skin)
        p.hair = hair
        p.beard = if (a.hairC >= 7) C("#3A2A20") else hair
        p.eye = at(AvaPal.EYE, a.eye)
        p.top = at(AvaPal.TOP, a.topC)
        p.bottom = at(AvaPal.BOT, a.botC)
        p.shoe = at(AvaPal.SHOE, a.shoeC)
        return p
    }

    /** Pesado (alguns segundos na primeira vez): chame fora da thread de desenho. */
    fun build(a: Avatar): Mesh {
        val chunks = Figure.buildChunks(spec(a), pal(a))
        val parts = ArrayList<Part>()
        for (c in chunks) {
            val vb = ByteBuffer.allocateDirect(c.nv * STRIDE * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
            vb.put(c.v, 0, c.nv * STRIDE)
            vb.position(0)
            val ib = ByteBuffer.allocateDirect(c.ni * 2).order(ByteOrder.nativeOrder()).asShortBuffer()
            ib.put(c.idx, 0, c.ni)
            ib.position(0)
            parts.add(Part(Mt.PLAIN, vb, c.nv, ib, c.ni))
        }
        return Mesh(parts)
    }
}

/** Monta o personagem em segundo plano; a thread de desenho só pega o resultado pronto. */
object AvatarBuilder {
    private val exec = Executors.newSingleThreadExecutor { r ->
        Thread(r, "avatar-build").also { it.isDaemon = true }
    }
    private val ticket = AtomicInteger(0)
    @Volatile private var done: Mesh? = null

    fun request(a: Avatar) {
        val code = a.encode()
        val t = ticket.incrementAndGet()
        exec.execute {
            if (t != ticket.get()) return@execute
            val av = Avatar.decode(code) ?: return@execute
            val m: Mesh? = try {
                AvatarModel.build(av)
            } catch (e: Throwable) {
                null
            }
            if (m != null && t == ticket.get()) done = m
        }
    }

    fun take(): Mesh? {
        val m = done
        if (m != null) done = null
        return m
    }
}
