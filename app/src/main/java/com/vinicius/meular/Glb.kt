package com.vinicius.meular

import android.content.res.AssetManager
import android.graphics.BitmapFactory
import android.opengl.GLES20
import android.opengl.GLUtils
import android.opengl.Matrix
import org.json.JSONArray
import org.json.JSONObject
import java.nio.ByteBuffer
import java.nio.ByteOrder

// Etapa 83: leitor de GLB (glTF 2.0 binário) da biblioteca de objetos 3D (assets/obj3d/<id>.glb, gerados por
// ferramentas/objetos3d/models.py). Lê nós (com pivô), malhas, materiais, texturas embutidas e os metadados em
// "extras" (animação de cada peça, colisores COL_*, pontos de interação IP_*, superfícies SURF_*).
// A parte de CPU (vértices, colisores) não precisa do GL; as texturas e os buffers de vídeo sobem na primeira vez que
// o objeto é desenhado (thread do GL).

/** Primitiva: vértices já no formato do jogo (STRIDE floats) em espaço do nó. */
class GPrim(val mat: Int, val cut: Boolean, val emit: Boolean, val img: Int, val v: FloatArray, val nv: Int, val idx: ShortArray)

class GNode(
    val name: String,
    var parent: Int,
    val t: FloatArray,
    val q: FloatArray,
    val prims: List<GPrim>,
    val ex: JSONObject?
) {
    val anim: JSONObject? = ex?.optJSONObject("anim")
    /** 0 nenhuma, 1 dobradiça (gira em [ax]), 2 trilho (desliza em [ax]), 3 escala (em [ax]) */
    val aType: Int = when (anim?.optString("tipo")) { "dobradica" -> 1; "trilho" -> 2; "escala" -> 3; else -> 0 }
    val ax = FloatArray(3)
    val aMin: Float
    val aMax: Float
    val aDur: Float
    /** caixa da malha no espaço do nó: x0 y0 z0 x1 y1 z1 (para teste de parede/colisão ao abrir) */
    val bb = floatArrayOf(Float.MAX_VALUE, Float.MAX_VALUE, Float.MAX_VALUE, -Float.MAX_VALUE, -Float.MAX_VALUE, -Float.MAX_VALUE)
    var mesh: Mesh? = null

    init {
        anim?.optJSONArray("eixo")?.let { for (i in 0..2) ax[i] = it.optDouble(i, 0.0).toFloat() }
        aMin = anim?.optDouble("min", 0.0)?.toFloat() ?: 0f
        aMax = anim?.optDouble("max", 0.0)?.toFloat() ?: 0f
        aDur = (anim?.optDouble("dur", 0.5)?.toFloat() ?: 0.5f).coerceAtLeast(0.05f)
        for (p in prims) for (i in 0 until p.nv) for (k in 0..2) {
            val c = p.v[i * STRIDE + k]
            if (c < bb[k]) bb[k] = c
            if (c > bb[3 + k]) bb[3 + k] = c
        }
    }

    /** Valor da animação para o progresso [u] (0 = estado inicial, 1 = aberto/ativo), com curva suave. */
    fun value(u: Float): Float {
        val c = u.coerceIn(0f, 1f)
        val e = c * c * (3f - 2f * c)
        return aMin + (aMax - aMin) * e
    }

    /** Matriz local (pai -> nó) com a animação [v] aplicada no pivô. */
    fun local(out: FloatArray, v: Float) {
        Matrix.setIdentityM(out, 0)
        Matrix.translateM(out, 0, t[0], t[1], t[2])
        if (q[3] < 0.99999f) {
            val ang = (2.0 * Math.acos(q[3].toDouble().coerceIn(-1.0, 1.0))).toFloat()
            val s = Math.sqrt((1.0 - q[3] * q[3]).coerceAtLeast(1e-12)).toFloat()
            Matrix.rotateM(out, 0, Math.toDegrees(ang.toDouble()).toFloat(), q[0] / s, q[1] / s, q[2] / s)
        }
        when (aType) {
            1 -> if (v != 0f) Matrix.rotateM(out, 0, Math.toDegrees(v.toDouble()).toFloat(), ax[0], ax[1], ax[2])
            2 -> if (v != 0f) Matrix.translateM(out, 0, ax[0] * v, ax[1] * v, ax[2] * v)
            3 -> Matrix.scaleM(out, 0, if (ax[0] > 0f) v else 1f, if (ax[1] > 0f) v else 1f, if (ax[2] > 0f) v else 1f)
        }
    }
}

/** Colisor (caixa, cilindro ou esfera) na pose inicial, em espaço do objeto (origem = centro do piso, frente +Z). */
class GCol(val name: String, val shape: String, val cx: Float, val cy: Float, val cz: Float, val sx: Float, val sy: Float, val sz: Float, val blocks: Boolean)

class GModel(val id: String, val nodes: List<GNode>, val meta: JSONObject, private val images: List<ByteArray>) {
    /** matriz de mundo (do objeto) de cada nó na pose inicial */
    val rest: Array<FloatArray>
    val cols = ArrayList<GCol>()
    /** índices dos nós com animação */
    val animated: IntArray
    /** limites da malha inteira na pose inicial: x0 y0 z0 x1 y1 z1 */
    val bounds = floatArrayOf(Float.MAX_VALUE, Float.MAX_VALUE, Float.MAX_VALUE, -Float.MAX_VALUE, -Float.MAX_VALUE, -Float.MAX_VALUE)

    init {
        rest = Array(nodes.size) { FloatArray(16) }
        val done = BooleanArray(nodes.size)
        fun calc(i: Int) {
            if (done[i]) return
            done[i] = true
            val n = nodes[i]
            if (n.parent >= 0) calc(n.parent)
            val loc = FloatArray(16)
            n.local(loc, n.value(0f))
            if (n.parent >= 0) Matrix.multiplyMM(rest[i], 0, rest[n.parent], 0, loc, 0)
            else System.arraycopy(loc, 0, rest[i], 0, 16)
        }
        for (i in nodes.indices) calc(i)
        for ((i, n) in nodes.withIndex()) {
            val m = rest[i]
            if (n.name.startsWith("COL_") && n.ex != null) {
                val sz = n.ex.optJSONArray("size")
                cols.add(GCol(n.name, n.ex.optString("shape", "box"), m[12], m[13], m[14],
                    sz?.optDouble(0, 0.0)?.toFloat() ?: 0f, sz?.optDouble(1, 0.0)?.toFloat() ?: 0f, sz?.optDouble(2, 0.0)?.toFloat() ?: 0f,
                    n.ex.optBoolean("bloqueia", true)))
            }
            for (p in n.prims) for (v in 0 until p.nv) {
                val x = p.v[v * STRIDE]; val y = p.v[v * STRIDE + 1]; val z = p.v[v * STRIDE + 2]
                val wx = m[0] * x + m[4] * y + m[8] * z + m[12]
                val wy = m[1] * x + m[5] * y + m[9] * z + m[13]
                val wz = m[2] * x + m[6] * y + m[10] * z + m[14]
                if (wx < bounds[0]) bounds[0] = wx; if (wy < bounds[1]) bounds[1] = wy; if (wz < bounds[2]) bounds[2] = wz
                if (wx > bounds[3]) bounds[3] = wx; if (wy > bounds[4]) bounds[4] = wy; if (wz > bounds[5]) bounds[5] = wz
            }
        }
        animated = nodes.indices.filter { nodes[it].aType != 0 }.toIntArray()
    }

    /** para cada nó: posição dele em [animated] (-1 = parado) */
    val animSlot: IntArray = IntArray(nodes.size).also { a -> a.fill(-1); for ((k, i) in animated.withIndex()) a[i] = k }
    /** peça que reage a "ocupado" (almofada que afunda), -1 = nenhuma */
    val occSlot: Int = animated.indexOfFirst { nodes[it].anim?.optString("gatilho") == "ocupado" }
    /** Lote 2: gatilho de cada peça animada ("" = interação direta, "ligado", "ocupado") */
    val slotGatilho: Array<String> = Array(animated.size) { nodes[animated[it]].anim?.optString("gatilho", "") ?: "" }
    /** almofada de qual assento (gatilho "ocupado"); "" = qualquer */
    val slotAssento: Array<String> = Array(animated.size) { nodes[animated[it]].anim?.optString("assento", "") ?: "" }
    /** peça que precisa estar aberta antes (gaveta dentro da porta da geladeira); -1 = nenhuma */
    val slotPrecisa: IntArray = IntArray(animated.size) { k ->
        val nm = nodes[animated[k]].anim?.optString("precisa", "") ?: ""
        val i = if (nm.isEmpty()) -1 else nodes.indexOfFirst { it.name == nm }
        if (i < 0) -1 else animSlot[i]
    }
    /** efeito visual de cada nó: 0 nenhum, 1 chama, 2 água, 3 luz */
    val effect: IntArray = IntArray(nodes.size) { i ->
        when (nodes[i].ex?.optJSONObject("efeito")?.optString("tipo")) { "chama" -> 1; "agua" -> 2; "luz" -> 3; else -> 0 }
    }
    /** quando o efeito aparece: -1 = aparelho ligado; senão a peça animada (slot) que precisa estar aberta */
    val effectWhen: IntArray = IntArray(nodes.size) { i ->
        val q = nodes[i].ex?.optJSONObject("efeito")?.optString("quando", "ligado") ?: "ligado"
        if (q == "ligado") -1 else { val j = nodes.indexOfFirst { it.name == q }; if (j < 0) -1 else animSlot[j] }
    }

    /** nós cujo nome começa com [prefix] (ex.: "IP_sentar") */
    fun ips(prefix: String): List<Int> = nodes.indices.filter { nodes[it].name.startsWith(prefix) }

    /** peças que afundam quando o assento [seat] está ocupado */
    fun occSlots(seat: String): List<Int> = animated.indices.filter { slotGatilho[it] == "ocupado" && (slotAssento[it].isEmpty() || slotAssento[it] == seat) }

    fun index(name: String): Int = nodes.indexOfFirst { it.name == name }

    /** Posição (x, y, z) e giro em Y (rad) do nó vazio [name] na pose inicial; null se não existir. */
    fun point(name: String): FloatArray? {
        val i = index(name)
        if (i < 0) return null
        val m = rest[i]
        return floatArrayOf(m[12], m[13], m[14], Math.atan2(m[8].toDouble(), m[10].toDouble()).toFloat())
    }

    /** Ponto (x, y, z) guardado em extras.<key> do nó [name]. */
    fun extraPoint(name: String, key: String): FloatArray? {
        val i = index(name)
        if (i < 0) return null
        val a = nodes[i].ex?.optJSONArray(key) ?: return null
        return floatArrayOf(a.optDouble(0).toFloat(), a.optDouble(1).toFloat(), a.optDouble(2).toFloat())
    }

    fun extraFloat(name: String, key: String, def: Float): Float {
        val i = index(name)
        if (i < 0) return def
        return nodes[i].ex?.optDouble(key, def.toDouble())?.toFloat() ?: def
    }

    /** Pegada para colisão do personagem e encaixe: [x0, z0, x1, z1, altura] em espaço do objeto (colisores que bloqueiam). */
    fun foot(dynamic: Boolean): FloatArray {
        var x0 = Float.MAX_VALUE; var z0 = Float.MAX_VALUE; var x1 = -Float.MAX_VALUE; var z1 = -Float.MAX_VALUE
        for (c in cols) {
            if (!dynamic && !c.blocks) continue
            if (c.cx - c.sx / 2 < x0) x0 = c.cx - c.sx / 2
            if (c.cx + c.sx / 2 > x1) x1 = c.cx + c.sx / 2
            if (c.cz - c.sz / 2 < z0) z0 = c.cz - c.sz / 2
            if (c.cz + c.sz / 2 > z1) z1 = c.cz + c.sz / 2
        }
        if (x1 < x0) { x0 = bounds[0]; z0 = bounds[2]; x1 = bounds[3]; z1 = bounds[5] }
        return floatArrayOf(x0, z0, x1, z1, bounds[4])
    }

    // ---------------------------------------------------------------- GL
    private var tex: IntArray? = null
    private var gen = -1

    /** Sobe texturas e malhas para a placa (na thread do GL). Refaz se o contexto do GL foi recriado. */
    fun ensureGl() {
        if (gen == GlGen.gen && tex != null) return
        gen = GlGen.gen
        val ids = IntArray(images.size)
        if (images.isNotEmpty()) GLES20.glGenTextures(images.size, ids, 0)
        for ((i, b) in images.withIndex()) {
            try {
                val opt = BitmapFactory.Options().apply { inPremultiplied = false }
                val bmp = BitmapFactory.decodeByteArray(b, 0, b.size, opt) ?: continue
                val clamp = nodes.any { n -> n.prims.any { it.img == i && it.cut } }
                GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, ids[i])
                GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bmp, 0)
                GLES20.glGenerateMipmap(GLES20.GL_TEXTURE_2D)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR_MIPMAP_LINEAR)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
                val w = if (clamp) GLES20.GL_CLAMP_TO_EDGE else GLES20.GL_REPEAT
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, w)
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, w)
                bmp.recycle()
            } catch (e: Throwable) {
                android.util.Log.e("Glb", "$id: textura $i falhou", e)
            }
        }
        tex = ids
        for (n in nodes) {
            if (n.prims.isEmpty()) { n.mesh = null; continue }
            val parts = ArrayList<Part>()
            for (p in n.prims) {
                val fb = ByteBuffer.allocateDirect(p.nv * STRIDE * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
                fb.put(p.v, 0, p.nv * STRIDE); fb.position(0)
                val ib = ByteBuffer.allocateDirect(p.idx.size * 2).order(ByteOrder.nativeOrder()).asShortBuffer()
                ib.put(p.idx); ib.position(0)
                val part = Part(p.mat, fb, p.nv, ib, p.idx.size, if (p.img in ids.indices) ids[p.img] else 0)
                part.gpu = true
                if (p.cut) part.cut = 0.5f
                parts.add(part)
            }
            n.mesh = Mesh(parts)
        }
    }

    /** Malha única na pose inicial, deslocada de (dx, 0, dz) (canto da área do móvel -> centro). Só na thread do GL. */
    fun staticMesh(dx: Float, dz: Float): Mesh {
        ensureGl()
        val ids = tex ?: IntArray(0)
        val parts = ArrayList<Part>()
        for ((ni, n) in nodes.withIndex()) {
            val m = rest[ni]
            for (p in n.prims) {
                val v = p.v.copyOf()
                for (i in 0 until p.nv) {
                    val o = i * STRIDE
                    val x = v[o]; val y = v[o + 1]; val z = v[o + 2]
                    v[o] = m[0] * x + m[4] * y + m[8] * z + m[12] + dx
                    v[o + 1] = m[1] * x + m[5] * y + m[9] * z + m[13]
                    v[o + 2] = m[2] * x + m[6] * y + m[10] * z + m[14] + dz
                    val nx = v[o + 3]; val ny = v[o + 4]; val nz = v[o + 5]
                    v[o + 3] = m[0] * nx + m[4] * ny + m[8] * nz
                    v[o + 4] = m[1] * nx + m[5] * ny + m[9] * nz
                    v[o + 5] = m[2] * nx + m[6] * ny + m[10] * nz
                }
                val fb = ByteBuffer.allocateDirect(p.nv * STRIDE * 4).order(ByteOrder.nativeOrder()).asFloatBuffer()
                fb.put(v, 0, p.nv * STRIDE); fb.position(0)
                val ib = ByteBuffer.allocateDirect(p.idx.size * 2).order(ByteOrder.nativeOrder()).asShortBuffer()
                ib.put(p.idx); ib.position(0)
                val part = Part(p.mat, fb, p.nv, ib, p.idx.size, if (p.img in ids.indices) ids[p.img] else 0)
                part.gpu = true
                if (p.cut) part.cut = 0.5f
                parts.add(part)
            }
        }
        return Mesh(parts)
    }
}

object Glb {
    @Volatile var assets: AssetManager? = null
    private val cache = HashMap<String, GModel?>()

    fun get(id: String): GModel? = synchronized(cache) {
        if (cache.containsKey(id)) return cache[id]
        val m = try {
            val am = assets ?: return null          // ainda sem assets: tenta de novo depois
            parse(am.open("obj3d/$id.glb").use { it.readBytes() }, id)
        } catch (e: Throwable) {
            android.util.Log.e("Glb", "$id.glb falhou", e)
            null
        }
        cache[id] = m
        m
    }

    fun parse(b: ByteArray, id: String): GModel {
        val bb = ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN)
        require(bb.getInt(0) == 0x46546C67) { "não é GLB" }
        val jl = bb.getInt(12)
        val js = JSONObject(String(b, 20, jl, Charsets.UTF_8))
        val bo = 20 + jl
        val bl = bb.getInt(bo)
        val bin = bo + 8                      // início do bloco binário dentro de b
        require(bin + bl <= b.size) { "bloco binário cortado" }
        val views = js.getJSONArray("bufferViews")
        val accs = js.getJSONArray("accessors")

        fun floats(ai: Int, comps: Int): FloatArray {
            val a = accs.getJSONObject(ai)
            val v = views.getJSONObject(a.getInt("bufferView"))
            val n = a.getInt("count")
            val ct = a.getInt("componentType")
            val csz = when (ct) { 5126 -> 4; 5123, 5122 -> 2; else -> 1 }
            val stride = v.optInt("byteStride", 0).let { if (it == 0) comps * csz else it }
            val off = bin + v.optInt("byteOffset", 0) + a.optInt("byteOffset", 0)
            val norm = a.optBoolean("normalized", false)
            val out = FloatArray(n * comps)
            for (i in 0 until n) for (k in 0 until comps) {
                val p = off + i * stride + k * csz
                out[i * comps + k] = when (ct) {
                    5126 -> bb.getFloat(p)
                    5121 -> (b[p].toInt() and 255).let { if (norm) it / 255f else it.toFloat() }
                    5123 -> (bb.getShort(p).toInt() and 0xFFFF).let { if (norm) it / 65535f else it.toFloat() }
                    5122 -> bb.getShort(p).toFloat()
                    else -> b[p].toFloat()
                }
            }
            return out
        }

        fun indices(ai: Int): ShortArray {
            val a = accs.getJSONObject(ai)
            val v = views.getJSONObject(a.getInt("bufferView"))
            val n = a.getInt("count")
            val ct = a.getInt("componentType")
            val off = bin + v.optInt("byteOffset", 0) + a.optInt("byteOffset", 0)
            return ShortArray(n) { i ->
                when (ct) {
                    5123 -> bb.getShort(off + i * 2)
                    5125 -> bb.getInt(off + i * 4).toShort()
                    else -> (b[off + i].toInt() and 255).toShort()
                }
            }
        }

        val mats = js.optJSONArray("materials") ?: JSONArray()
        val texs = js.optJSONArray("textures") ?: JSONArray()
        val imgs = js.optJSONArray("images") ?: JSONArray()
        val images = ArrayList<ByteArray>()
        for (i in 0 until imgs.length()) {
            val v = views.getJSONObject(imgs.getJSONObject(i).getInt("bufferView"))
            val o = bin + v.optInt("byteOffset", 0)
            images.add(b.copyOfRange(o, o + v.getInt("byteLength")))
        }
        val meshes = js.optJSONArray("meshes") ?: JSONArray()
        val jn = js.getJSONArray("nodes")
        val parent = IntArray(jn.length()) { -1 }
        for (i in 0 until jn.length()) jn.getJSONObject(i).optJSONArray("children")?.let { ch ->
            for (k in 0 until ch.length()) parent[ch.getInt(k)] = i
        }
        val nodes = ArrayList<GNode>()
        for (i in 0 until jn.length()) {
            val o = jn.getJSONObject(i)
            val t = FloatArray(3); val q = floatArrayOf(0f, 0f, 0f, 1f)
            o.optJSONArray("translation")?.let { for (k in 0..2) t[k] = it.getDouble(k).toFloat() }
            o.optJSONArray("rotation")?.let { for (k in 0..3) q[k] = it.getDouble(k).toFloat() }
            val prims = ArrayList<GPrim>()
            if (o.has("mesh")) {
                val pa = meshes.getJSONObject(o.getInt("mesh")).getJSONArray("primitives")
                for (k in 0 until pa.length()) {
                    val pr = pa.getJSONObject(k)
                    val at = pr.getJSONObject("attributes")
                    val pos = floats(at.getInt("POSITION"), 3)
                    val nv = pos.size / 3
                    val nor = if (at.has("NORMAL")) floats(at.getInt("NORMAL"), 3) else FloatArray(nv * 3)
                    val uv = if (at.has("TEXCOORD_0")) floats(at.getInt("TEXCOORD_0"), 2) else FloatArray(nv * 2)
                    val col = if (at.has("COLOR_0")) floats(at.getInt("COLOR_0"), 4) else FloatArray(nv * 4) { 1f }
                    var mt = Mt.PLAIN; var cut = false; var emit = false; var img = -1
                    var bc = floatArrayOf(1f, 1f, 1f, 1f)
                    if (pr.has("material")) {
                        val m = mats.getJSONObject(pr.getInt("material"))
                        m.optJSONObject("extras")?.let { e ->
                            mt = e.optInt("mt", Mt.PLAIN).coerceIn(0, Mt.COUNT - 1)
                            cut = e.optInt("cut", 0) != 0
                            emit = e.optInt("emit", 0) != 0
                        }
                        if (m.optString("alphaMode") == "MASK") cut = true
                        m.optJSONObject("pbrMetallicRoughness")?.let { pbr ->
                            pbr.optJSONArray("baseColorFactor")?.let { a -> for (c in 0..3) bc[c] = a.optDouble(c, 1.0).toFloat() }
                            pbr.optJSONObject("baseColorTexture")?.let { tx -> img = texs.optJSONObject(tx.getInt("index"))?.optInt("source", -1) ?: -1 }
                        }
                    }
                    val v = FloatArray(nv * STRIDE)
                    for (j in 0 until nv) {
                        val ob = j * STRIDE
                        v[ob] = pos[j * 3]; v[ob + 1] = pos[j * 3 + 1]; v[ob + 2] = pos[j * 3 + 2]
                        if (!emit) { v[ob + 3] = nor[j * 3]; v[ob + 4] = nor[j * 3 + 1]; v[ob + 5] = nor[j * 3 + 2] }
                        for (c in 0..3) v[ob + 6 + c] = col[j * 4 + c] * bc[c]
                        v[ob + 10] = uv[j * 2]; v[ob + 11] = uv[j * 2 + 1]
                    }
                    val idx = if (pr.has("indices")) indices(pr.getInt("indices")) else ShortArray(nv) { it.toShort() }
                    prims.add(GPrim(mt, cut, emit, img, v, nv, idx))
                }
            }
            nodes.add(GNode(o.optString("name", "n$i"), parent[i], t, q, prims, o.optJSONObject("extras")))
        }
        val meta = nodes.firstOrNull()?.ex ?: JSONObject()
        return GModel(id, nodes, meta, images)
    }
}
