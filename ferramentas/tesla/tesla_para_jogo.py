#!/usr/bin/env python3
"""Tesla Model S (branco) -> GLB no formato da biblioteca do jogo (assets/obj3d/veic_tesla.glb).

Separa a malha do tesla_branco.glb em peças com pivô:
  corpo (carroceria + vidros + interior simples que eu acrescentei)
  roda_FE/FD/TE/TD  (giram em X; as da frente ficam dentro de dir_FE/dir_FD, que viram em Y)
  porta_FE/FD/TE/TD (dobradiça vertical na quina da frente da porta)
Convenção do jogo: metros, Y para cima, frente +Z, origem no centro do piso. +X = lado esquerdo (motorista).
"""
import struct, json, sys, collections, math
import numpy as np

SRC = sys.argv[1]
OUT = sys.argv[2]

MT_PLAIN, MT_FABRIC, MT_METAL, MT_GLASS = 0, 7, 11, 12

b = open(SRC, 'rb').read()
jl = struct.unpack_from('<I', b, 12)[0]
g = json.loads(b[20:20 + jl]); bin0 = 20 + jl + 8
bv = g['bufferViews']; ac = g['accessors']
def rd(i, dt, n):
    a = ac[i]; v = bv[a['bufferView']]; o = bin0 + v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.frombuffer(b, dtype=dt, count=a['count'] * n, offset=o).reshape(a['count'], n)
P = rd(0, '<f4', 3).astype(np.float64); N = rd(1, '<f4', 3).astype(np.float64); UV = rd(2, '<f4', 2).astype(np.float64)
prims = g['meshes'][0]['primitives']
T = [rd(p['indices'], '<u2', 1).ravel().reshape(-1, 3).astype(int) for p in prims]
img = bv[g['images'][0]['bufferView']]
PNG = b[bin0 + img.get('byteOffset', 0): bin0 + img.get('byteOffset', 0) + img['byteLength']]

def comps(tri):
    par = {}
    def f(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for t in tri:
        a, b_, c = map(f, t); par[b_] = a; par[c] = a
    d = collections.defaultdict(list)
    for i, t in enumerate(tri): d[f(t[0])].append(i)
    return list(d.values())

# ------------------------------------------------------------------ classificação
WHEELS = {'FE': (+1, 1.56), 'FD': (-1, 1.56), 'TE': (+1, -1.41), 'TD': (-1, -1.41)}
WY = 0.355; WR = 0.37; WX = 0.845
DOORS = {  # nome: (lado, z_min, z_max, dobradiça z)
    'FE': (+1, -0.245, 0.915, 0.905), 'FD': (-1, -0.245, 0.915, 0.905),
    'TE': (+1, -1.29, -0.245, -0.245), 'TD': (-1, -1.29, -0.245, -0.245)}
HINGE_X = 0.93

group = [np.full(len(t), 'corpo', dtype=object) for t in T]
for k in range(6):
    tri = T[k]
    for c in comps(tri):
        vs = np.unique(tri[c].ravel()); q = P[vs]
        side = 1 if q[:, 0].mean() > 0 else -1
        ax = np.abs(q[:, 0])
        # rodas: tudo dentro do cilindro do pneu
        done = False
        for nm, (s, zc) in WHEELS.items():
            if s != side: continue
            r = np.hypot(q[:, 1] - WY, q[:, 2] - zc)
            if ax.min() >= 0.58 and ax.max() <= 1.02 and r.max() <= WR:
                group[k][c] = 'roda_' + nm; done = True; break
        if done: continue
        if k in (0, 1):
            for nm, (s, z0, z1, hz) in DOORS.items():
                if s != side: continue
                if ax.min() >= 0.55 and ax.max() <= 1.15 and q[:, 1].min() >= 0.2 and q[:, 2].min() >= z0 - 0.005 and q[:, 2].max() <= z1 + 0.012:
                    group[k][c] = 'porta_' + nm; break
        elif k == 2:   # vidros: por componente
            zc = (q[:, 2].min() + q[:, 2].max()) / 2
            for nm, (s, z0, z1, hz) in DOORS.items():
                if s != side: continue
                lo = z0 if nm[0] == 'F' else -1.12
                if ax.min() >= 0.6 and q[:, 2].min() >= lo - 0.005 and z0 <= zc <= z1:
                    group[k][c] = 'porta_' + nm; break
        elif k == 3:   # cromados: por triângulo (a moldura da janela é cortada na divisa)
            for ti in c:
                cen = P[tri[ti]].mean(0); sd = 1 if cen[0] > 0 else -1
                for nm, (s, z0, z1, hz) in DOORS.items():
                    if s != sd: continue
                    lo = z0 if nm[0] == 'F' else -1.15
                    if abs(cen[0]) >= 0.6 and cen[1] >= 0.2 and lo <= cen[2] <= z1:
                        group[k][ti] = 'porta_' + nm; break

cnt = collections.Counter()
for k in range(6):
    for gname in group[k]: cnt[gname] += 1
print({k: cnt[k] for k in sorted(cnt)})

# ------------------------------------------------------------------ montagem de nós
class Node:
    def __init__(s, name, t=(0, 0, 0), parent=None, extras=None):
        s.name = name; s.t = t; s.parent = parent; s.extras = extras; s.prims = []   # (mat, pos, nor, uv, col, idx)
nodes = []
def add(name, t=(0, 0, 0), parent=None, extras=None):
    n = Node(name, t, parent, extras); nodes.append(n); return n

root = add('veic_tesla', extras={'id': 'veic_tesla', 'nome': 'Tesla Model S (branco)', 'categoria': 'veiculo',
                                 'classe': 'veiculo', 'escala': 'm (frente +Z, +X = lado do motorista)'})
corpo = add('corpo', parent=root)
nd = {}
for nm, (s, zc) in WHEELS.items():
    cx = s * WX
    par = root
    if nm[0] == 'F':
        par = add('dir_' + nm, (cx, WY, zc), root, {'giro': 'direcao'})
        nd['roda_' + nm] = add('roda_' + nm, (0, 0, 0), par, {'giro': 'roda'})
    else:
        nd['roda_' + nm] = add('roda_' + nm, (cx, WY, zc), root, {'giro': 'roda'})
for nm, (s, z0, z1, hz) in DOORS.items():
    nd['porta_' + nm] = add('porta_' + nm, (s * HINGE_X, 0, hz), root,
                            {'anim': {'tipo': 'dobradica', 'eixo': [0, 1, 0], 'min': 0.0, 'max': (-1.15 if s > 0 else 1.15), 'dur': 0.5}})
nd['corpo'] = corpo
origin = {'corpo': np.zeros(3)}
for nm, (s, zc) in WHEELS.items(): origin['roda_' + nm] = np.array([s * WX, WY, zc])
for nm, (s, z0, z1, hz) in DOORS.items(): origin['porta_' + nm] = np.array([s * HINGE_X, 0, hz])

def emit(node, mat, tris, off):
    if len(tris) == 0: return
    vs = np.unique(np.array(tris).ravel()); remap = {v: i for i, v in enumerate(vs)}
    pos = (P[vs] - off).astype(np.float32); nor = N[vs].astype(np.float32); uv = UV[vs].astype(np.float32)
    idx = np.array([[remap[x] for x in t] for t in tris], dtype=np.uint16)
    node.prims.append((mat, pos, nor, uv, None, idx))

for k in range(6):
    for gname in set(group[k]):
        sel = np.where(group[k] == gname)[0]
        emit(nd[gname], k, T[k][sel], origin[gname])

# ------------------------------------------------------------------ interior simples (para as portas abertas não mostrarem o vazio)
def box(cx, cy, cz, sx, sy, sz, uvs=2.0):
    P_, N_, U_, I_ = [], [], [], []
    for axis in range(3):
        for sgn in (-1, 1):
            n = np.zeros(3); n[axis] = sgn
            u = np.zeros(3); v = np.zeros(3); u[(axis + 1) % 3] = 1; v[(axis + 2) % 3] = 1
            sz3 = np.array([sx, sy, sz]) / 2
            base = len(P_)
            for (a, bb) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = np.array([cx, cy, cz]) + n * sz3 + u * sz3 * a + v * sz3 * bb
                P_.append(p); N_.append(n); U_.append([p[0] * uvs + p[2] * uvs, p[1] * uvs + p[2] * 0.5 * uvs])
            if sgn > 0: I_ += [[base, base + 1, base + 2], [base, base + 2, base + 3]]
            else: I_ += [[base, base + 2, base + 1], [base, base + 3, base + 2]]
    return np.array(P_), np.array(N_), np.array(U_), np.array(I_)

def torus(c, rr, tr, tilt_deg, seg=20, ring=6):
    P_, N_, U_, I_ = [], [], [], []
    ca, sa = math.cos(math.radians(tilt_deg)), math.sin(math.radians(tilt_deg))
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for j in range(ring):
            bj = 2 * math.pi * j / ring
            lx = (rr + tr * math.cos(bj)) * math.cos(a); ly = (rr + tr * math.cos(bj)) * math.sin(a); lz = tr * math.sin(bj)
            nx_, ny_, nz_ = math.cos(bj) * math.cos(a), math.cos(bj) * math.sin(a), math.sin(bj)
            # anel no plano XY, inclinado em torno de X
            def rot(x, y, z): return (x, y * ca - z * sa, y * sa + z * ca)
            p = rot(lx, ly, lz); n = rot(nx_, ny_, nz_)
            P_.append([c[0] + p[0], c[1] + p[1], c[2] + p[2]]); N_.append(n); U_.append([i / seg * 4, j / ring])
    for i in range(seg):
        for j in range(ring):
            a0 = i * ring + j; a1 = ((i + 1) % seg) * ring + j; a2 = ((i + 1) % seg) * ring + (j + 1) % ring; a3 = i * ring + (j + 1) % ring
            I_ += [[a0, a1, a2], [a0, a2, a3]]
    return np.array(P_), np.array(N_), np.array(U_), np.array(I_)

def addgeo(lst, geo):
    p, n, u, i = geo; base = sum(len(x[0]) for x in lst)
    lst.append((p, n, u, i + base))
def pack(lst):
    return (np.concatenate([x[0] for x in lst]).astype(np.float32), np.concatenate([x[1] for x in lst]).astype(np.float32),
            np.concatenate([x[2] for x in lst]).astype(np.float32), np.concatenate([x[3] for x in lst]).astype(np.uint16))

seat, plastic, screen = [], [], []
for s in (+1, -1):
    addgeo(seat, box(s * 0.36, 0.38, 0.40, 0.50, 0.14, 0.56))          # assento dianteiro
    addgeo(seat, box(s * 0.36, 0.70, 0.12, 0.50, 0.56, 0.14))          # encosto
    addgeo(seat, box(s * 0.36, 1.07, 0.10, 0.26, 0.20, 0.10))          # apoio de cabeça
addgeo(seat, box(0, 0.38, -0.85, 1.36, 0.14, 0.52)); addgeo(seat, box(0, 0.70, -1.12, 1.36, 0.56, 0.14))
for s in (-0.42, 0, 0.42): addgeo(seat, box(s, 1.04, -1.12, 0.26, 0.18, 0.10))
addgeo(plastic, box(0, 0.76, 0.92, 1.50, 0.22, 0.40))                     # painel
addgeo(plastic, box(0, 0.36, 0.15, 0.26, 0.20, 1.10))                     # console central
addgeo(plastic, torus((0.36, 0.84, 0.66), 0.17, 0.014, 25))               # volante
addgeo(plastic, box(0.36, 0.76, 0.76, 0.05, 0.05, 0.16))                  # coluna de direção
addgeo(screen, box(0, 0.93, 0.86, 0.42, 0.26, 0.03))                      # tela central
for lst, mat in ((seat, 6), (plastic, 7), (screen, 8)):
    p, n, u, i = pack(lst)
    corpo.prims.append((mat, p, n, u, None, i))

# ------------------------------------------------------------------ materiais
def srgb_keep(c): return list(c)
MATS = []
def mat(name, col, a=1.0, tex=False, rough=0.5, metal=0.0, mt=MT_PLAIN, blend=False, emit=0):
    d = {'name': name, 'pbrMetallicRoughness': {'baseColorFactor': [col[0], col[1], col[2], a], 'metallicFactor': metal, 'roughnessFactor': rough},
         'doubleSided': True, 'extras': {'mt': mt, 'emit': emit}}
    if tex: d['pbrMetallicRoughness']['baseColorTexture'] = {'index': 0}
    if blend: d['alphaMode'] = 'BLEND'
    MATS.append(d)
for m in g['materials']:
    pb = m['pbrMetallicRoughness']; col = pb['baseColorFactor']
    mtk = {'carroceria': MT_METAL, 'difuso_interior_pneus': MT_PLAIN, 'vidro_janelas': MT_GLASS, 'cromado': MT_METAL, 'rodas': MT_METAL, 'vidro_farol': MT_GLASS}[m['name']]
    mat(m['name'], col[:3], col[3], 'baseColorTexture' in pb, pb['roughnessFactor'], pb['metallicFactor'], mtk, m.get('alphaMode') == 'BLEND')
mat('interior_tecido', (0.10, 0.10, 0.11), mt=MT_FABRIC)
mat('interior_plastico', (0.07, 0.07, 0.08), mt=MT_PLAIN)
mat('tela_central', (0.28, 0.42, 0.60), mt=MT_PLAIN, emit=1)

# ------------------------------------------------------------------ gravar GLB
blob = bytearray(); views = []; acc = []; meshes = []
def addview(data, target=None):
    while len(blob) % 4: blob.append(0)
    o = len(blob); blob.extend(data); v = {'buffer': 0, 'byteOffset': o, 'byteLength': len(data)}
    if target: v['target'] = target
    views.append(v); return len(views) - 1
def addacc(arr, ctype, typ, target, minmax=False):
    vi = addview(arr.tobytes(), target)
    a = {'bufferView': vi, 'componentType': ctype, 'count': len(arr), 'type': typ}
    if minmax: a['min'] = arr.min(0).astype(float).tolist(); a['max'] = arr.max(0).astype(float).tolist()
    acc.append(a); return len(acc) - 1
imgv = addview(PNG)
jn = []
for i, n in enumerate(nodes):
    d = {'name': n.name}
    if n.t != (0, 0, 0): d['translation'] = [float(x) for x in n.t]
    if n.extras: d['extras'] = n.extras
    if n.prims:
        pl = []
        for (m, pos, nor, uv, col, idx) in n.prims:
            at = {'POSITION': addacc(pos, 5126, 'VEC3', 34962, True), 'NORMAL': addacc(nor, 5126, 'VEC3', 34962),
                  'TEXCOORD_0': addacc(uv, 5126, 'VEC2', 34962)}
            pl.append({'attributes': at, 'indices': addacc(idx.reshape(-1), 5123, 'SCALAR', 34963), 'material': m})
        meshes.append({'name': n.name, 'primitives': pl}); d['mesh'] = len(meshes) - 1
    jn.append(d)
for i, n in enumerate(nodes):
    if n.parent is not None:
        pi = nodes.index(n.parent); jn[pi].setdefault('children', []).append(i)
G = {'asset': {'version': '2.0', 'generator': 'Meu Lar tesla_para_jogo.py'}, 'scene': 0, 'scenes': [{'name': 'veic_tesla', 'nodes': [0]}],
     'nodes': jn, 'meshes': meshes, 'materials': MATS, 'textures': [{'source': 0, 'sampler': 0}],
     'samplers': [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}], 'images': [{'bufferView': imgv, 'mimeType': 'image/png'}],
     'accessors': acc, 'bufferViews': views, 'buffers': [{'byteLength': 0}]}
while len(blob) % 4: blob.append(0)
G['buffers'][0]['byteLength'] = len(blob)
js = json.dumps(G, separators=(',', ':')).encode()
while len(js) % 4: js += b' '
total = 12 + 8 + len(js) + 8 + len(blob)
open(OUT, 'wb').write(struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(blob), 0x004E4942) + bytes(blob))
print('ok', OUT, total, 'bytes;', len(nodes), 'nós;', sum(len(p[1]) for n in nodes for p in n.prims), 'vértices')
