package com.vinicius.meular
import java.nio.FloatBuffer
import java.nio.ShortBuffer
const val STRIDE = 12
object Mt { const val PLAIN = 0; const val COUNT = 15; const val GLASS = 12 }
class Part(val mat: Int, val buf: FloatBuffer, val count: Int, val idx: ShortBuffer? = null, val icount: Int = 0, val tex: Int = 0) { var cut = 0f; var gpu = false }
class Mesh(val parts: List<Part>)
object GlGen { @JvmField var gen = 1 }
enum class Type(val w: Int, val h: Int, val dyn: Boolean) { CAIXA(1, 1, true), BOLA(1, 1, true) }
class Item(val type: Type, var x: Int, var y: Int, var rot: Int = 0) {
    var ox = 0f; var oz = 0f
    val w: Int get() = if (rot % 2 == 1) type.h else type.w
    val h: Int get() = if (rot % 2 == 1) type.w else type.h
    var st = ""
    var body: Body? = null
}
