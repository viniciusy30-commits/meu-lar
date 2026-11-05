"""Biblioteca de objetos 3D do Meu Lar: modelo com nós (peças com pivô), gravação GLB (glTF 2.0) e verificação.

Convenção (Plano Mestre v3, definida na auditoria da Etapa 0):
  * metros; Y para cima; frente do objeto = +Z; origem no centro do chão do objeto (y = 0 é o piso).
  * cada peça que se move é um nó próprio com o pivô no eixo físico (dobradiça, trilho, eixo).
  * nós vazios COL_* = colisores (extras.shape box|cyl|sphere, extras.size); IP_* = pontos de interação
    (posição = onde a raiz do personagem fica; rotação Y = para onde ele olha); SURF_* = superfícies de apoio.
  * comportamento em extras (campo oficial de metadados do glTF): no nó raiz (meta do asset) e em cada peça móvel.
A geometria é construída em espaço do objeto (como se tudo estivesse parado na pose inicial); ao gravar, cada nó recebe
translation = pivô - pivô do pai e os vértices ficam relativos ao pivô.
"""
import json, struct, math, os, io
import numpy as np
from PIL import Image

GEO_CLASS = None   # geom.Geo (com as primitivas) é registrado ao importar geom
HERE = os.path.dirname(os.path.abspath(__file__))
TEXDIR = os.path.join(HERE, 'tex')

# código de material do jogo (Mt.*) -> parâmetros PBR aproximados (para visualizadores de GLB)
PBR = {0: (0.0, 0.55), 6: (0.0, 0.62), 7: (0.0, 0.92), 10: (0.0, 0.95), 11: (1.0, 0.32), 12: (0.0, 0.05), 8: (0.0, 0.8)}


class Geo:
    """Geometria acumulada por chave (textura, material do jogo, recorte)."""
    def __init__(s): s.parts = {}

    def add(s, key, P, N, C, UV, T):
        a = s.parts.setdefault(key, dict(P=[], N=[], C=[], UV=[], T=[], n=0))
        P = np.asarray(P, float).reshape(-1, 3); n = len(P)
        C = np.asarray(C, float).reshape(n, -1)
        if C.shape[1] == 3: C = np.hstack([C, np.ones((n, 1))])
        a['P'].append(P); a['N'].append(np.asarray(N, float).reshape(-1, 3)); a['C'].append(C)
        a['UV'].append(np.asarray(UV, float).reshape(-1, 2)); a['T'].append(np.asarray(T, int).reshape(-1, 3) + a['n']); a['n'] += n

    def arrays(s):
        out = []
        for k, a in s.parts.items():
            if a['n'] == 0: continue
            out.append((k, np.vstack(a['P']), np.vstack(a['N']), np.vstack(a['C']), np.vstack(a['UV']), np.vstack(a['T'])))
        return out

    def counts(s):
        return sum(a['n'] for a in s.parts.values()), sum(sum(len(t) for t in a['T']) for a in s.parts.values())


class Node:
    def __init__(s, name, pivot=(0, 0, 0), parent=None, extras=None, yaw=0.0, empty=False):
        s.name = name; s.pivot = np.asarray(pivot, float); s.parent = parent; s.children = []
        s.extras = extras or {}; s.yaw = yaw; s.geo = None if empty else (GEO_CLASS or Geo)()
        if parent is not None: parent.children.append(s)


class Model:
    def __init__(s, aid, meta):
        s.id = aid; s.meta = meta
        s.root = Node(aid, (0, 0, 0), None, meta)
        s.matnames = {}

    def node(s, name, pivot=(0, 0, 0), parent=None, extras=None):
        return Node(name, pivot, parent or s.root, extras)

    def empty(s, name, pos, parent=None, extras=None, yaw=0.0):
        return Node(name, pos, parent or s.root, extras, yaw, empty=True)

    def nodes(s):
        out = []
        def rec(n):
            out.append(n)
            for c in n.children: rec(c)
        rec(s.root); return out

    # ---------- oclusão ambiente do objeto inteiro (pose inicial), gravada na cor dos vértices
    def bake_ao(s, **kw):
        from ao_core import bake_arrays
        items = []
        for n in s.nodes():
            if n.geo is None: continue
            for k, a in n.geo.parts.items():
                if a['n'] == 0: continue
                items.append((n, k))
        arrs = []
        for n, k in items:
            a = n.geo.parts[k]
            arrs.append((np.vstack(a['P']), np.vstack(a['N']), np.vstack(a['T'])))
        ks = bake_arrays(arrs, **kw)
        for (n, k), kk in zip(items, ks):
            a = n.geo.parts[k]; off = 0
            for i, C in enumerate(a['C']):
                m = len(C); C = C.copy(); C[:, :3] *= kk[off:off + m, None]; a['C'][i] = C; off += m

    def bounds(s):
        allP = [P for n in s.nodes() if n.geo for _, P, *_ in n.geo.arrays()]
        P = np.vstack(allP); return P.min(0), P.max(0)

    def counts(s):
        v = t = 0
        for n in s.nodes():
            if n.geo:
                a, b = n.geo.counts(); v += a; t += b
        return v, t

    # ---------- GLB
    def write_glb(s, path):
        bin_ = bytearray(); views = []; accs = []; meshes = []; mats = []; matidx = {}; images = []; imgidx = {}; texs = []; samplers = []
        nodes_out = []

        def view(data, target=None):
            while len(bin_) % 4: bin_.append(0)
            off = len(bin_); bin_.extend(data)
            v = dict(buffer=0, byteOffset=off, byteLength=len(data))
            if target: v['target'] = target
            views.append(v); return len(views) - 1

        def acc(arr, ctype, typ, target, normalized=False, minmax=False):
            arr = np.ascontiguousarray(arr)
            vi = view(arr.tobytes(), target)
            a = dict(bufferView=vi, componentType=ctype, count=int(arr.shape[0]), type=typ)
            if normalized: a['normalized'] = True
            if minmax:
                a['min'] = [float(x) for x in arr.min(0)]; a['max'] = [float(x) for x in arr.max(0)]
            accs.append(a); return len(accs) - 1

        def sampler(clamp):
            w = 33071 if clamp else 10497
            for i, sm in enumerate(samplers):
                if sm['wrapS'] == w: return i
            samplers.append(dict(magFilter=9729, minFilter=9987, wrapS=w, wrapT=w)); return len(samplers) - 1

        def image(tex):
            if tex in imgidx: return imgidx[tex]
            im = Image.open(os.path.join(TEXDIR, tex)); bio = io.BytesIO(); im.save(bio, 'PNG', optimize=True)
            vi = view(bio.getvalue()); images.append(dict(name=tex, bufferView=vi, mimeType='image/png'))
            imgidx[tex] = len(images) - 1; return imgidx[tex]

        def material(key, emit):
            kk = (key, emit)
            if kk in matidx: return matidx[kk]
            tex, mt, cut = key
            met, rough = PBR.get(mt, (0.0, 0.6))
            nm = s.matnames.get(key) or ('%s_%s' % (os.path.splitext(tex)[0], mt))
            m = dict(name=nm, pbrMetallicRoughness=dict(baseColorFactor=[1, 1, 1, 1], metallicFactor=met, roughnessFactor=rough))
            ti = len(texs); texs.append(dict(sampler=sampler(bool(cut)), source=image(tex)))
            m['pbrMetallicRoughness']['baseColorTexture'] = dict(index=ti)
            if cut: m['alphaMode'] = 'MASK'; m['alphaCutoff'] = 0.5; m['doubleSided'] = True
            elif mt == 12: m['alphaMode'] = 'BLEND'
            if emit: m['emissiveFactor'] = [1, 1, 1]; m['emissiveTexture'] = dict(index=ti); m['doubleSided'] = True
            m['extras'] = dict(mt=int(mt), cut=int(cut), emit=int(emit), tex=tex)
            mats.append(m); matidx[kk] = len(mats) - 1; return matidx[kk]

        allnodes = s.nodes(); index = {id(n): i for i, n in enumerate(allnodes)}
        for n in allnodes:
            par = n.parent.pivot if n.parent is not None else np.zeros(3)
            d = dict(name=n.name)
            t = n.pivot - par
            if np.abs(t).max() > 1e-9: d['translation'] = [float(x) for x in t]
            if n.yaw: d['rotation'] = [0.0, math.sin(n.yaw / 2), 0.0, math.cos(n.yaw / 2)]
            if n.children: d['children'] = [index[id(c)] for c in n.children]
            if n.extras: d['extras'] = n.extras
            if n.geo is not None and n.geo.arrays():
                prims = []
                for key, P, N, C, UV, T in n.geo.arrays():
                    P = P - n.pivot
                    # limpeza: tira triângulos degenerados e acerta a ordem dos vértices pela normal (faces para fora)
                    T = np.asarray(T, int)
                    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); ar = np.linalg.norm(fn, axis=1)
                    keep = ar > 1e-11; T = T[keep]; fn = fn[keep]
                    vn = N[T[:, 0]] + N[T[:, 1]] + N[T[:, 2]]
                    flip = (fn * vn).sum(1) < 0; T[flip] = T[flip][:, [0, 2, 1]]
                    used = np.zeros(len(P), bool); used[T.reshape(-1)] = True
                    if not used.all():
                        remap = np.cumsum(used) - 1; P, N, C, UV = P[used], N[used], C[used], UV[used]; T = remap[T]
                    nl = np.linalg.norm(N, axis=1); emit = bool((nl < 0.1).all())
                    N = np.where(nl[:, None] > 0.1, N / np.maximum(nl[:, None], 1e-12), np.array([0, 1.0, 0]))
                    # partes com mais de 65535 vértices são divididas (o jogo usa índices de 16 bits)
                    chunks = [(P, N, C, UV, T)] if len(P) < 65536 else split_tris(P, N, C, UV, T)
                    for (p, nn, c, uv, tt) in chunks:
                        attrs = dict(POSITION=acc(p.astype('<f4'), 5126, 'VEC3', 34962, minmax=True),
                                     NORMAL=acc(nn.astype('<f4'), 5126, 'VEC3', 34962),
                                     TEXCOORD_0=acc(uv.astype('<f4'), 5126, 'VEC2', 34962),
                                     COLOR_0=acc((np.clip(c, 0, 1) * 255 + 0.5).astype('<u1'), 5121, 'VEC4', 34962, normalized=True))
                        ind = acc(tt.reshape(-1).astype('<u2'), 5123, 'SCALAR', 34963)
                        prims.append(dict(attributes=attrs, indices=ind, material=material(key, emit)))
                meshes.append(dict(name=n.name, primitives=prims)); d['mesh'] = len(meshes) - 1
            nodes_out.append(d)
        while len(bin_) % 4: bin_.append(0)
        gj = dict(asset=dict(version='2.0', generator='Meu Lar obj3d/glb_lib.py'), scene=0, scenes=[dict(name=s.id, nodes=[0])],
                  nodes=nodes_out, meshes=meshes, materials=mats, textures=texs, images=images, samplers=samplers,
                  accessors=accs, bufferViews=views, buffers=[dict(byteLength=len(bin_))])
        js = json.dumps(gj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        while len(js) % 4: js += b' '
        total = 12 + 8 + len(js) + 8 + len(bin_)
        out = struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(bin_), 0x004E4942) + bytes(bin_)
        open(path, 'wb').write(out)
        return len(out)


def split_tris(P, N, C, UV, T):
    out = []; i = 0
    while i < len(T):
        used = {}; tl = []
        while i < len(T) and len(used) + 3 < 65535:
            for v in T[i]:
                if v not in used: used[v] = len(used)
            tl.append([used[v] for v in T[i]]); i += 1
        ids = np.array(list(used.keys()))
        out.append((P[ids], N[ids], C[ids], UV[ids], np.array(tl)))
    return out


# ------------------------------------------------------------------------------------------------ leitura e verificação
def read_glb(path):
    b = open(path, 'rb').read()
    magic, ver, ln = struct.unpack_from('<III', b, 0)
    assert magic == 0x46546C67, 'não é GLB'; assert ver == 2; assert ln == len(b), 'tamanho do cabeçalho não bate'
    jl, jt = struct.unpack_from('<II', b, 12); assert jt == 0x4E4F534A
    gj = json.loads(b[20:20 + jl]); o = 20 + jl
    bl, bt = struct.unpack_from('<II', b, o); assert bt == 0x004E4942
    return gj, b[o + 8:o + 8 + bl]


CT = {5120: ('i1', 1), 5121: ('u1', 1), 5122: ('i2', 2), 5123: ('u2', 2), 5125: ('u4', 4), 5126: ('f4', 4)}
NC = dict(SCALAR=1, VEC2=2, VEC3=3, VEC4=4, MAT4=16)


def accessor(gj, bin_, i):
    a = gj['accessors'][i]; v = gj['bufferViews'][a['bufferView']]
    dt, sz = CT[a['componentType']]; n = NC[a['type']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    end = off + a['count'] * n * sz
    assert end <= v.get('byteOffset', 0) + v['byteLength'], 'acessor %d passa do fim do bufferView' % i
    assert off % sz == 0, 'acessor %d desalinhado' % i
    arr = np.frombuffer(bin_, '<' + dt, a['count'] * n, off).reshape(a['count'], n) if n > 1 else np.frombuffer(bin_, '<' + dt, a['count'], off)
    if a.get('normalized'): arr = arr.astype(float) / (255.0 if dt == 'u1' else 65535.0)
    return arr


def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def world_mats(gj):
    W = {}
    def rec(i, M):
        nd = gj['nodes'][i]; L = np.eye(4)
        if 'matrix' in nd: L = np.array(nd['matrix']).reshape(4, 4).T
        else:
            R = quat_mat(nd.get('rotation', [0, 0, 0, 1])); S = np.diag(nd.get('scale', [1, 1, 1]))
            L[:3, :3] = R @ S; L[:3, 3] = nd.get('translation', [0, 0, 0])
        W[i] = M @ L
        for c in nd.get('children', []): rec(c, W[i])
    for r in gj['scenes'][gj.get('scene', 0)]['nodes']: rec(r, np.eye(4))
    return W


def verify(path, expect=None):
    """Confere o arquivo. Devolve (erros, avisos, info). expect: dict com 'dims' (x, y, z em m) para comparar."""
    err = []; warn = []; info = {}
    gj, bin_ = read_glb(path)
    if gj.get('asset', {}).get('version') != '2.0': err.append('asset.version != 2.0')
    nn = len(gj['nodes']); parent = [-1] * nn
    for i, nd in enumerate(gj['nodes']):
        for c in nd.get('children', []):
            if c >= nn: err.append('nó %d aponta para filho inexistente' % i)
            elif parent[c] != -1: err.append('nó %d tem dois pais' % c)
            else: parent[c] = i
    W = world_mats(gj)
    if len(W) != nn: err.append('%d nós fora da cena' % (nn - len(W)))
    for i, v in enumerate(gj['bufferViews']):
        if v['byteOffset'] + v['byteLength'] > len(bin_): err.append('bufferView %d passa do fim do buffer' % i)
    for i, im in enumerate(gj.get('images', [])):
        v = gj['bufferViews'][im['bufferView']]
        try:
            Image.open(io.BytesIO(bin_[v['byteOffset']:v['byteOffset'] + v['byteLength']])).load()
        except Exception as e: err.append('imagem %d não abre: %s' % (i, e))
    allP = []; vt = tt = 0; degen = 0; open_edges = 0; nmesh = 0
    for i, nd in enumerate(gj['nodes']):
        if 'mesh' not in nd: continue
        nmesh += 1
        for pi, pr in enumerate(gj['meshes'][nd['mesh']]['primitives']):
            at = pr['attributes']
            for need in ('POSITION', 'NORMAL', 'TEXCOORD_0'):
                if need not in at: err.append('%s: primitiva %d sem %s' % (nd['name'], pi, need))
            P = accessor(gj, bin_, at['POSITION']).astype(float)
            a = gj['accessors'][at['POSITION']]
            if not (np.allclose(P.min(0), a['min'], atol=1e-5) and np.allclose(P.max(0), a['max'], atol=1e-5)): err.append('%s: min/max de POSITION errados' % nd['name'])
            if not np.isfinite(P).all(): err.append('%s: posição NaN/inf' % nd['name'])
            N = accessor(gj, bin_, at['NORMAL']).astype(float); nl = np.linalg.norm(N, axis=1)
            if np.abs(nl - 1).max() > 0.01: err.append('%s: normais não unitárias (%.3f)' % (nd['name'], np.abs(nl - 1).max()))
            for k in ('NORMAL', 'TEXCOORD_0', 'COLOR_0'):
                if k in at and gj['accessors'][at[k]]['count'] != len(P): err.append('%s: %s com contagem diferente' % (nd['name'], k))
            I = accessor(gj, bin_, pr['indices']).astype(int).reshape(-1, 3)
            if I.max() >= len(P): err.append('%s: índice fora da malha' % nd['name'])
            if pr.get('material', -1) >= len(gj.get('materials', [])): err.append('%s: material inexistente' % nd['name'])
            Pw = (W[i][:3, :3] @ P.T).T + W[i][:3, 3]; allP.append(Pw)
            ar = np.linalg.norm(np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]), axis=1)
            degen += int((ar < 1e-12).sum()); vt += len(P); tt += len(I)
            # normal geométrica x normal do vértice: faces invertidas
            fn = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]); ok = ar > 1e-10
            vn = N[I[:, 0]] + N[I[:, 1]] + N[I[:, 2]]
            dots = (fn[ok] * vn[ok]).sum(1)
            mat = gj['materials'][pr['material']] if 'material' in pr else {}
            if not mat.get('doubleSided') and (dots < 0).mean() > 0.02:
                err.append('%s: %.1f%% das faces invertidas em relação às normais' % (nd['name'], 100 * (dots < 0).mean()))
    if degen: warn.append('%d triângulos degenerados (área ~0)' % degen)
    P = np.vstack(allP); lo, hi = P.min(0), P.max(0)
    info.update(vertices=vt, triangulos=tt, malhas=nmesh, nos=nn, materiais=len(gj.get('materials', [])), texturas=len(gj.get('images', [])),
                bbox_min=[round(float(x), 4) for x in lo], bbox_max=[round(float(x), 4) for x in hi], bytes=os.path.getsize(path))
    if lo[1] < -0.002: err.append('objeto abaixo do piso (y mín %.4f)' % lo[1])
    if lo[1] > 0.02 and not (expect or {}).get('mural'): warn.append('objeto flutuando %.3f m acima do piso' % lo[1])
    meta = gj['nodes'][0].get('extras', {})
    for k in ('id', 'nome', 'categoria', 'classe', 'dimensoes', 'fisica'):
        if k not in meta: err.append('metadados sem "%s"' % k)
    if 'dimensoes' in meta:
        d = meta['dimensoes']; real = hi - lo
        for ax, nm in enumerate(('largura', 'altura', 'profundidade')):
            if abs(d[nm] - real[ax]) > 0.012: err.append('dimensão %s declarada %.3f, malha %.3f' % (nm, d[nm], real[ax]))
    for i, nd in enumerate(gj['nodes']):
        nm = nd.get('name', '')
        if nm.startswith('COL_') and 'shape' not in nd.get('extras', {}): err.append('%s sem extras.shape' % nm)
        if nm.startswith('IP_') and 'acao' not in nd.get('extras', {}): err.append('%s sem extras.acao' % nm)
        if nm.startswith('COL_'):
            ex = nd['extras']; c = W[i][:3, 3]; sz = np.array(ex.get('size', [0, 0, 0]))
            if ex['shape'] == 'box' and (((c - sz / 2) < lo - 0.03).any() or ((c + sz / 2) > hi + 0.03).any()):
                warn.append('%s maior que a malha' % nm)
        if 'extras' in nd and 'anim' in nd['extras']:
            an = nd['extras']['anim']
            for k in ('tipo', 'eixo', 'min', 'max', 'dur'):
                if k not in an: err.append('%s: anim sem %s' % (nm, k))
    return err, warn, info


def load_arrays(path):
    """Relê o GLB e devolve uma lista (chave, P, N, C, UV, T) em espaço do objeto (para pré-visualização)."""
    gj, bin_ = read_glb(path); W = world_mats(gj); out = []
    for i, nd in enumerate(gj['nodes']):
        if 'mesh' not in nd: continue
        for pr in gj['meshes'][nd['mesh']]['primitives']:
            at = pr['attributes']; m = gj['materials'][pr['material']]
            P = accessor(gj, bin_, at['POSITION']).astype(float); N = accessor(gj, bin_, at['NORMAL']).astype(float)
            UV = accessor(gj, bin_, at['TEXCOORD_0']).astype(float)
            C = accessor(gj, bin_, at['COLOR_0']).astype(float) if 'COLOR_0' in at else np.ones((len(P), 4))
            T = accessor(gj, bin_, pr['indices']).astype(int).reshape(-1, 3)
            P = (W[i][:3, :3] @ P.T).T + W[i][:3, 3]; N = (W[i][:3, :3] @ N.T).T
            ex = m['extras']
            if ex.get('emit'): N = N * 0
            out.append(((ex['tex'], ex['mt'], ex['cut']), P, N, C, UV, T))
    return out, gj
