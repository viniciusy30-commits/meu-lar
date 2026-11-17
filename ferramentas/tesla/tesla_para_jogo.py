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
                lo = z0 - 0.10 if nm[0] == 'F' else -1.12        # o vidro da porta da frente passa 7 cm da divisa (fica na porta)
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

def rbox(c, sz, rx=0.0, ry=0.0):
    """caixa centrada em c, tamanho sz, girada rx graus em X e ry em Y (em torno do proprio centro)"""
    p, n, u, i = box(0, 0, 0, *sz)
    ax, ay = math.radians(rx), math.radians(ry)
    Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    Ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    R = Ry @ Rx
    p = p @ R.T + np.array(c); n = n @ R.T
    U = np.stack([p[:, 0] * 2 + p[:, 2] * 2, p[:, 1] * 2 + p[:, 2]], 1)
    return p, n, U, i

def cyl(c, r, h, axis='y', seg=14, rx=0.0):
    P_, N_, U_, I_ = [], [], [], []
    for k in range(seg + 1):
        a = 2 * math.pi * k / seg; ca, sa = math.cos(a), math.sin(a)
        for yy in (-h / 2, h / 2):
            if axis == 'y': p = (r * ca, yy, r * sa); nn = (ca, 0, sa)
            elif axis == 'x': p = (yy, r * ca, r * sa); nn = (0, ca, sa)
            else: p = (r * ca, r * sa, yy); nn = (ca, sa, 0)
            P_.append(p); N_.append(nn); U_.append((k / seg * 2, yy))
    for k in range(seg):
        a0 = k * 2; I_ += [[a0, a0 + 2, a0 + 3], [a0, a0 + 3, a0 + 1]]
    base = len(P_)
    for e, yy in enumerate((-h / 2, h / 2)):     # tampas
        ci = len(P_)
        if axis == 'y': P_.append((0, yy, 0)); N_.append((0, 1 if e else -1, 0))
        elif axis == 'x': P_.append((yy, 0, 0)); N_.append((1 if e else -1, 0, 0))
        else: P_.append((0, 0, yy)); N_.append((0, 0, 1 if e else -1))
        U_.append((0.5, 0.5))
        for k in range(seg):
            i0 = k * 2 + e; i1 = (k + 1) * 2 + e
            I_.append([ci, i1, i0] if e else [ci, i0, i1])
    p = np.array(P_, float); n = np.array(N_, float)
    ax = math.radians(rx); Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    p = p @ Rx.T + np.array(c); n = n @ Rx.T
    return p, n, np.array(U_, float), np.array(I_)

# ------------------------------------------------------------------ interior detalhado (cabine estilo Model S)
# couro creme nos bancos, painel escuro com friso de madeira, tela vertical de 17", quadro de instrumentos digital,
# carpete, pedais, console com descansa-braco e porta-copos, saidas de ar, retrovisor, quebra-sois, cintos.
couro, costura, plast, madeira, carpete, tela, cromo, cluster = [], [], [], [], [], [], [], []
# medidas do interior tiradas da carroceria (raios: teto/para-brisa, paredes, assoalho em y=0,14) -> nada atravessa a lataria
addgeo(carpete, box(0, 0.17, 0.01, 1.44, 0.04, 1.96))                 # assoalho (topo 0,22: pe do motorista apoiado)
addgeo(carpete, rbox((0, 0.30, 1.08), (1.16, 0.04, 0.30), rx=-40))       # rampa dos pes (parede de fogo)
for s_ in (+1, -1):
    x = s_ * 0.37
    # banco dianteiro: base, almofada com abas laterais, encosto inclinado com abas, cabeceira
    addgeo(plast, box(x, 0.33, 0.33, 0.40, 0.18, 0.36))
    addgeo(couro, box(x, 0.47, 0.36, 0.46, 0.10, 0.48))
    for e in (-1, 1): addgeo(couro, box(x + e * 0.21, 0.52, 0.36, 0.06, 0.08, 0.46))
    addgeo(couro, rbox((x, 0.82, -0.02), (0.48, 0.62, 0.12), rx=-12))
    for e in (-1, 1): addgeo(couro, rbox((x + e * 0.22, 0.80, 0.01), (0.06, 0.56, 0.15), rx=-12))
    addgeo(costura, rbox((x, 0.82, 0.045), (0.30, 0.50, 0.01), rx=-12))           # painel central do encosto (costura)
    addgeo(costura, box(x, 0.525, 0.36, 0.30, 0.01, 0.38))
    addgeo(couro, rbox((x, 1.22, -0.11), (0.26, 0.20, 0.10), rx=-8))                # cabeceira
    for e in (-1, 1): addgeo(cromo, box(x + e * 0.07, 1.10, -0.10, 0.012, 0.08, 0.012))
    addgeo(plast, rbox((x + s_ * 0.24, 0.86, 0.05), (0.05, 0.50, 0.012), rx=-12))   # cinto (faixa junto a coluna)
    # banco traseiro (assento inteirico + encostos)
    addgeo(couro, box(x, 0.46, -0.76, 0.54, 0.12, 0.48))
addgeo(couro, rbox((0, 0.80, -1.06), (1.22, 0.60, 0.12), rx=-14))
for xx in (-0.40, 0, 0.40): addgeo(couro, rbox((xx, 1.17, -1.12), (0.24, 0.18, 0.10), rx=-10))
addgeo(costura, rbox((0, 0.80, -0.995), (0.02, 0.56, 0.01), rx=-14))
# console central com descansa-braco, porta-copos e tampa de madeira
addgeo(plast, box(0, 0.40, 0.42, 0.26, 0.26, 0.86))
addgeo(madeira, box(0, 0.535, 0.55, 0.22, 0.01, 0.40))
addgeo(couro, box(0, 0.60, 0.05, 0.24, 0.08, 0.36))
for zz in (0.62, 0.74): addgeo(plast, cyl((0, 0.54, zz), 0.04, 0.012, seg=12))
# painel: corpo, tampo macio, friso de madeira de lado a lado, saidas de ar, porta-luvas
addgeo(plast, rbox((0, 0.77, 0.92), (1.46, 0.24, 0.34), rx=8))
addgeo(plast, rbox((0, 0.905, 0.88), (1.44, 0.05, 0.30), rx=-6))
addgeo(madeira, box(0, 0.80, 0.765, 1.46, 0.06, 0.02))
addgeo(cromo, box(0, 0.835, 0.76, 1.46, 0.006, 0.012))
for xx in (-0.62, -0.20, 0.20, 0.62):
    addgeo(plast, box(xx, 0.88, 0.755, 0.16, 0.035, 0.01))
    for k in range(3): addgeo(cromo, box(xx, 0.872 + k * 0.009, 0.749, 0.15, 0.003, 0.004))
addgeo(plast, box(-0.40, 0.68, 0.78, 0.46, 0.14, 0.02))
# tela central vertical (17") com moldura
addgeo(plast, rbox((0, 0.88, 0.78), (0.27, 0.34, 0.03), rx=-14))
addgeo(tela, rbox((0, 0.88, 0.763), (0.24, 0.31, 0.005), rx=-14))
# quadro de instrumentos atras do volante
addgeo(plast, rbox((0.352, 0.955, 0.82), (0.34, 0.12, 0.05), rx=-18))
addgeo(cluster, rbox((0.352, 0.955, 0.795), (0.30, 0.095, 0.005), rx=-18))
addgeo(plast, rbox((0.352, 0.835, 0.745), (0.09, 0.09, 0.16), rx=-20))          # coluna de direcao ate o cubo
# pedais
for xx, w_ in ((0.30, 0.10), (0.44, 0.06)):
    addgeo(plast, rbox((xx, 0.37, 0.92), (w_, 0.12, 0.015), rx=-35))
    addgeo(cromo, rbox((xx, 0.37, 0.912), (w_ - 0.01, 0.10, 0.004), rx=-35))
# retrovisor interno e quebra-sois
addgeo(plast, rbox((0, 1.15, 0.58), (0.24, 0.065, 0.03), rx=-10)); addgeo(cromo, rbox((0, 1.15, 0.564), (0.22, 0.05, 0.004), rx=-10))
addgeo(plast, box(0, 1.205, 0.61, 0.02, 0.07, 0.02))                            # haste colada no para-brisa
# (sem quebra-sois: na altura do teto do Model S eles tapavam a vista do motorista em 1a pessoa)
# soleiras e colunas internas
for s_ in (+1, -1):
    addgeo(cromo, box(s_ * 0.80, 0.30, 0.0, 0.06, 0.02, 1.86))
    addgeo(plast, box(s_ * 0.80, 0.27, 0.0, 0.10, 0.06, 1.88))

# volante: no proprio no (gira com a direcao); centro do aro no centro do no, aro no plano XY inclinado
VOL = (0.352, 0.89, 0.66); VTILT = -20.0
vol, volc, vols = [], [], []
addgeo(vol, torus((0, 0, 0), 0.165, 0.017, VTILT, seg=32, ring=8))
addgeo(vols, rbox((0, -0.005, 0.0), (0.12, 0.09, 0.05), rx=VTILT))              # cubo (airbag)
for ang in (0, 180, 270):                                                        # 3 raios
    a_ = math.radians(ang); cx_, cy_ = math.cos(a_) * 0.10, math.sin(a_) * 0.10
    ca_, sa_ = math.cos(math.radians(VTILT)), math.sin(math.radians(VTILT))
    addgeo(vols, rbox((cx_, cy_ * ca_, cy_ * sa_), (0.11 if ang != 270 else 0.03, 0.03 if ang != 270 else 0.11, 0.02), rx=VTILT))
addgeo(volc, rbox((0, 0.026 * math.sin(math.radians(VTILT)), -0.026 * math.cos(math.radians(VTILT))), (0.05, 0.035, 0.002), rx=VTILT))            # logo cromado
volante = add('volante', VOL, root, {'giro': 'volante', 'eixo': [0, -math.sin(math.radians(VTILT)), math.cos(math.radians(VTILT))]})

# forro interno das portas da frente e de tras (vista de dentro com a porta aberta: nada de vazio escuro)
def door_trim(side, z0, z1):
    """painel interno no referencial do no da porta (origem na dobradica: x=0 na face, z de z0 a z1)"""
    L = {'couro': [], 'plast': [], 'madeira': [], 'cromo': []}
    xi = -side * 0.10                                       # para dentro do carro
    zc = (z0 + z1) / 2; zl = (z1 - z0)
    addgeo(L['plast'], box(xi, 0.61, zc, 0.04, 0.58, zl - 0.06))                       # forro
    addgeo(L['couro'], box(xi - side * 0.03, 0.70, zc, 0.03, 0.16, zl - 0.14))         # faixa de couro
    addgeo(L['madeira'], box(xi - side * 0.025, 0.86, zc, 0.03, 0.05, zl - 0.12))     # friso de madeira
    addgeo(L['couro'], box(xi - side * 0.07, 0.62, zc - 0.05, 0.10, 0.05, zl * 0.55)) # descansa-braco
    addgeo(L['cromo'], box(xi - side * 0.03, 0.78, z1 - 0.20, 0.02, 0.03, 0.10))      # macaneta interna
    addgeo(L['plast'], cyl((xi - side * 0.025, 0.42, z0 + 0.22), 0.08, 0.01, 'x', 14)) # alto-falante
    addgeo(L['cromo'], cyl((xi - side * 0.031, 0.42, z0 + 0.22), 0.06, 0.004, 'x', 14))
    addgeo(L['plast'], box(xi - side * 0.06, 0.36, zc, 0.08, 0.08, zl - 0.25))        # bolsa da porta
    return L
for nm, (s_, z0, z1, hz) in DOORS.items():
    L = door_trim(s_, z0 - hz + (0.04 if nm[0] == 'F' else 0.36), z1 - hz - 0.05 if nm[0] == 'F' else -0.03)
    for lst, mt_ in ((L['plast'], 'plast'), (L['couro'], 'couro'), (L['madeira'], 'madeira'), (L['cromo'], 'cromo')):
        if lst: p, n, u, i = pack(lst); nd['porta_' + nm].prims.append((mt_, p, n, u, None, i))

for lst, mat_ in ((couro, 'couro'), (costura, 'costura'), (plast, 'plast'), (madeira, 'madeira'), (carpete, 'carpete'), (tela, 'tela'), (cromo, 'cromo'), (cluster, 'cluster')):
    p, n, u, i = pack(lst); corpo.prims.append((mat_, p, n, u, None, i))
for lst, mat_ in ((vol, 'couro_escuro'), (vols, 'plast'), (volc, 'cromo')):
    p, n, u, i = pack(lst); volante.prims.append((mat_, p, n, u, None, i))

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
NEWM = {'couro': len(MATS), 'costura': len(MATS) + 1, 'plast': len(MATS) + 2, 'madeira': len(MATS) + 3, 'carpete': len(MATS) + 4,
        'tela': len(MATS) + 5, 'cromo': 3, 'cluster': len(MATS) + 6, 'couro_escuro': len(MATS) + 7}
mat('interior_couro', (0.86, 0.82, 0.74), mt=MT_FABRIC, rough=0.6)
mat('interior_costura', (0.70, 0.64, 0.56), mt=MT_FABRIC)
mat('interior_plastico', (0.20, 0.20, 0.22), mt=MT_PLAIN, rough=0.7)
mat('interior_madeira', (0.52, 0.34, 0.20), mt=MT_PLAIN, rough=0.4)
mat('interior_carpete', (0.24, 0.23, 0.22), mt=MT_FABRIC, rough=0.9)
mat('tela_central', (0.42, 0.62, 0.86), mt=MT_PLAIN, emit=1)
mat('quadro_instrumentos', (0.30, 0.55, 0.80), mt=MT_PLAIN, emit=1)
mat('volante_couro', (0.16, 0.15, 0.15), mt=MT_FABRIC, rough=0.6)
for nd_ in nodes:
    nd_.prims = [((NEWM[p[0]] if isinstance(p[0], str) else p[0]),) + tuple(p[1:]) for p in nd_.prims]

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
