#!/usr/bin/env python3
"""Etapa 184 - povoa a cidade: prédios, casas, postes, hidrantes e árvores (só onde faz sentido).
Lê city3.json + relevo.bin (saída de gen_city7.py) e acrescenta ao city3.json as chaves:
  bld   : lista plana, 9 números por prédio  [x, z, w, d, andares, ang, tipo, seed, pódio]
          tipo 0 casa, 1 sobrado/mansão, 2 loja/comércio, 3 apartamentos, 4 escritórios, 5 torre
  lamp  : 4 por poste [x, z, ang, tipo]   (ang = direção da luminária; tipo 0 rua, 1 avenida)
  hyd   : 2 por hidrante [x, z]
  tree  : 6 por árvore [x, z, espécie, escala, giro, tom]  (0 carvalho, 1 bordo, 2 cerejeira, 3 pinheiro)
Determinístico (semente fixa). Uso: python3 gen_pop.py [city3.json] [relevo.bin]
"""
import json, math, struct, sys, random
import numpy as np

SRC = sys.argv[1] if len(sys.argv) > 1 else 'city3.json'
BIN = sys.argv[2] if len(sys.argv) > 2 else 'relevo.bin'
d = json.load(open(SRC))
raw = open(BIN, 'rb').read()
NX, NZ, G = struct.unpack('<iif', raw[:12])
H = np.frombuffer(raw[12:12 + NX * NZ * 2], dtype='<i2').reshape(NZ, NX) / 100.0
WX, WZ = d['world']
rng = random.Random(184)
CW = {0: 1.4, 1: 1.4, 2: 2.0, 3: 2.4}   # largura da calçada/borda (= curbW do Relevo.kt)


def hgt(x, z):
    fx = min(max(x / G, 0), NX - 1.001); fz = min(max(z / G, 0), NZ - 1.001)
    i = int(fx); j = int(fz); tx = fx - i; tz = fz - j
    a = H[j, i]; b = H[j, i + 1]; c = H[j + 1, i]; e = H[j + 1, i + 1]
    return float((a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + e * tx) * tz)


def slope(x, z):
    return max(abs(hgt(x + 4, z) - hgt(x - 4, z)), abs(hgt(x, z + 4) - hgt(x, z - 4))) / 8.0


# ---------------------------------------------------------------- ruas: amostras para colisão
CELL = 16.0
road_grid = {}
def gadd(grid, x, z, item):
    grid.setdefault((int(x // CELL), int(z // CELL)), []).append(item)
def gnear(grid, x, z, r=1):
    cx, cz = int(x // CELL), int(z // CELL)
    for i in range(cx - r, cx + r + 1):
        for j in range(cz - r, cz + r + 1):
            yield from grid.get((i, j), ())

ROADS = []
for r in d['roads']:
    p = r['p']; n = len(p) // 4
    P = [(p[4 * q], p[4 * q + 1], p[4 * q + 2], p[4 * q + 3]) for q in range(n)]
    cs = [0.0]
    for q in range(1, n):
        cs.append(cs[-1] + math.hypot(P[q][0] - P[q - 1][0], P[q][1] - P[q - 1][1]))
    ROADS.append(dict(c=r['c'], w=r['w'], P=P, cs=cs, a=r.get('a', 0.0), b=r.get('b', 0.0),
                      cl=r.get('cl', []), cr=r.get('cr', [])))
    hw = r['w'] / 2 + CW[r['c']] + 0.6
    for q in range(n - 1):
        x0, z0, _, b0 = P[q]; x1, z1, _, b1 = P[q + 1]
        L = math.hypot(x1 - x0, z1 - z0)
        k = max(1, int(L / 4))
        for t in range(k + 1):
            f = t / k
            gadd(road_grid, x0 + (x1 - x0) * f, z0 + (z1 - z0) * f, (x0 + (x1 - x0) * f, z0 + (z1 - z0) * f, hw + (6.0 if (b0 or b1) else 0.0), math.atan2(z1 - z0, x1 - x0)))
HUBS = [(h['x'], h['z'], h['r']) for h in d['rounds']]
for hx, hz, hr in HUBS:
    for a in range(0, 360, 10):
        gadd(road_grid, hx + math.cos(math.radians(a)) * hr * 0.9, hz + math.sin(math.radians(a)) * hr * 0.9, (hx + math.cos(math.radians(a)) * hr * 0.9, hz + math.sin(math.radians(a)) * hr * 0.9, hr * 0.25 + 4.0, 0.0))
    gadd(road_grid, hx, hz, (hx, hz, hr + 5.0, 0.0))
HOUSES = [(h['x'], h['z']) for h in d['houses']]


def road_clear(x, z, margin):
    """distância livre até a rua mais próxima (negativo = em cima da rua)"""
    best = 1e9
    for sx, sz, hw, _a in gnear(road_grid, x, z, 2):
        v = math.hypot(x - sx, z - sz) - hw
        if v < best: best = v
    for hx, hz, hr in HUBS:
        v = math.hypot(x - hx, z - hz) - (hr + 4.0)
        if v < best: best = v
    return best - margin


def near_house(x, z, r=62.0):
    return any(math.hypot(x - hx, z - hz) < r for hx, hz in HOUSES)


# ---------------------------------------------------------------- zonas
CENTER = (HUBS[0][0], HUBS[0][1]) if HUBS else (1051, 1063)
def urban(x, z):
    u = math.exp(-(math.hypot(x - CENTER[0], z - CENTER[1]) / 520.0) ** 2)
    for hx, hz, _ in HUBS[1:]:
        u = max(u, 0.6 * math.exp(-(math.hypot(x - hx, z - hz) / 240.0) ** 2))
    return u


# ---------------------------------------------------------------- prédios
BLD = []          # dicts
bld_grid = {}

def obb(b):
    c, s = math.cos(b['ang']), math.sin(b['ang'])
    return c, s

def inside(b, x, z, pad=0.0):
    c, s = obb(b)
    dx, dz = x - b['x'], z - b['z']
    u = dx * c + dz * s; v = -dx * s + dz * c
    return abs(u) <= b['w'] / 2 + pad and abs(v) <= b['d'] / 2 + pad

def corners(x, z, w, dd, ang, pad=0.0):
    c, s = math.cos(ang), math.sin(ang)
    out = []
    for a, bb in ((-1, -1), (1, -1), (1, 1), (-1, 1), (0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)):
        lu = a * (w / 2 + pad); lv = bb * (dd / 2 + pad)
        out.append((x + c * lu - s * lv, z + s * lu + c * lv))
    return out

def fits(x, z, w, dd, ang, kind):
    pts = corners(x, z, w, dd, ang, 1.0)
    hs = []
    for px, pz in pts:
        if px < 14 or pz < 14 or px > WX - 14 or pz > WZ - 14: return False
        h = hgt(px, pz)
        if h < 1.4: return False           # água / areia molhada
        hs.append(h)
        if road_clear(px, pz, 0.6) < 0: return False
    lim = 2.0 if kind <= 2 else 3.2
    if max(hs) - min(hs) > lim: return False
    if near_house(x, z): return False
    # sobreposição com prédios já postos
    rad = 0.5 * math.hypot(w, dd) + 2
    for o in list(gnear(bld_grid, x, z, 3)):
        if math.hypot(o['x'] - x, o['z'] - z) > rad + 0.5 * math.hypot(o['w'], o['d']) + 2: continue
        for px, pz in pts:
            if inside(o, px, pz, 0.8): return False
        for qx, qz in corners(o['x'], o['z'], o['w'], o['d'], o['ang'], 0.8):
            if inside(dict(x=x, z=z, w=w, d=dd, ang=ang), qx, qz): return False
    return True

def put(x, z, w, dd, fl, ang, kind, podium=0):
    b = dict(x=x, z=z, w=w, d=dd, fl=fl, ang=ang, k=kind, seed=rng.randrange(1, 10 ** 6), pod=podium)
    BLD.append(b); gadd(bld_grid, x, z, b)
    return b

TREES = []   # [x, z, esp, escala, giro, tom]
def tree(x, z, sp, sc):
    TREES.append([round(x, 1), round(z, 1), sp, round(sc, 2), round(rng.uniform(0, 6.28), 2), round(rng.uniform(0.92, 1.08), 3)])

def pick_kind(u, rc, onave):
    r = rng.random()
    if onave:
        if u > 0.62: return 5 if r < 0.35 else (4 if r < 0.75 else 3)
        if u > 0.3: return 4 if r < 0.3 else (3 if r < 0.6 else 2)
        return 2 if r < 0.8 else 3
    if u > 0.62: return 5 if r < 0.3 else (3 if r < 0.7 else 4)
    if u > 0.3: return 3 if r < 0.6 else (2 if r < 0.8 else 0)
    if u > 0.12: return 0 if r < 0.55 else (3 if r < 0.75 else (1 if r < 0.9 else 2))
    return 0 if r < 0.82 else 1

def dims(kind, u):
    if kind == 0: return rng.uniform(9, 13), rng.uniform(9, 12.5), rng.choice((1, 1, 2)), 5.0
    if kind == 1: return rng.uniform(13, 19), rng.uniform(12, 16), 2, 7.0
    if kind == 2: return rng.uniform(10, 17), rng.uniform(13, 20), rng.choice((1, 2, 2, 3)), 2.5
    if kind == 3: return rng.uniform(17, 28), rng.uniform(15, 22), rng.randint(4, 4 + int(5 * u + 3)), 4.0
    if kind == 4: return rng.uniform(20, 30), rng.uniform(18, 26), rng.randint(5, 8 + int(8 * u)), 3.0
    return rng.uniform(26, 36), rng.uniform(24, 32), rng.randint(14, 16 + int(14 * u)), 3.0

def frontage(r):
    c = r['c']
    if c == 0: return
    P, cs = r['P'], r['cs']
    hw = r['w'] / 2 + CW[c]
    s_a, s_b = max(r['a'], 0) + 6.0, cs[-1] - max(r['b'], 0) - 6.0
    for sg in (1, -1):
        s = s_a
        while s < s_b:
            # ponto e tangente em s
            q = max(1, next((i for i in range(1, len(cs)) if cs[i] >= s), len(cs) - 1))
            f = (s - cs[q - 1]) / max(cs[q] - cs[q - 1], 1e-6)
            x = P[q - 1][0] + (P[q][0] - P[q - 1][0]) * f; z = P[q - 1][1] + (P[q][1] - P[q - 1][1]) * f
            ry = P[q - 1][2] + (P[q][2] - P[q - 1][2]) * f
            tx, tz = P[q][0] - P[q - 1][0], P[q][1] - P[q - 1][1]
            L = math.hypot(tx, tz) or 1.0; tx /= L; tz /= L
            if P[q][3] or P[q - 1][3] or abs(ry - hgt(x, z)) > 2.5:
                s += 8.0; continue
            u = urban(x, z)
            onave = (c == 1) or (c == 2 and u > 0.45)
            kind = pick_kind(u, c, onave)
            if c == 3 and kind in (4, 5): kind = 3
            w, dd, fl, setb = dims(kind, u)
            if rng.random() < 0.07 and kind <= 1:        # lote vazio / pracinha
                for _ in range(rng.randint(1, 3)):
                    ox = x - tz * sg * (hw + setb + rng.uniform(1, 9)) + tx * rng.uniform(-6, 6)
                    oz = z + tx * sg * (hw + setb + rng.uniform(1, 9)) + tz * rng.uniform(-6, 6)
                    if road_clear(ox, oz, 2.5) > 0 and hgt(ox, oz) > 2.2 and not near_house(ox, oz): tree(ox, oz, rng.choice((0, 1, 2)), rng.uniform(0.95, 1.4))
                s += w + 3; continue
            off = hw + setb + dd / 2
            nx_, nz_ = -tz * sg, tx * sg           # normal para o lado do lote
            bx, bz = x + nx_ * off + tx * w / 2, z + nz_ * off + tz * w / 2
            ang = math.atan2(tz, tx) + (0 if sg == 1 else math.pi)
            ok = fits(bx, bz, w, dd, ang, kind)
            if not ok and kind >= 3:     # tenta algo menor
                kind = 2 if c != 3 else 0; w, dd, fl, setb = dims(kind, u); off = hw + setb + dd / 2
                bx, bz = x + nx_ * off + tx * w / 2, z + nz_ * off + tz * w / 2
                ok = fits(bx, bz, w, dd, ang, kind)
            if ok:
                pod = 0
                if kind == 5: pod = 3
                elif kind == 4 and fl > 7: pod = 2
                b = put(bx, bz, w, dd, fl, ang, kind, pod)
                if kind <= 1 and rng.random() < 0.55:   # árvore no jardim da frente
                    fx = x + nx_ * (hw + setb * 0.45) + tx * rng.uniform(1.5, w - 1.5); fz = z + nz_ * (hw + setb * 0.45) + tz * rng.uniform(1.5, w - 1.5)
                    if road_clear(fx, fz, 1.2) > 0: tree(fx, fz, rng.choice((0, 1, 2, 2)), rng.uniform(0.7, 1.05))
                s += w + (rng.uniform(0.6, 2.5) if kind <= 1 else rng.uniform(0.0, 1.5))
            else:
                s += 7.0

for r in ROADS: frontage(r)

def nearest_road(x, z):
    best = 1e9; ang = 0.0
    for sx, sz, hw, a in gnear(road_grid, x, z, 5):
        v = math.hypot(x - sx, z - sz) - hw
        if v < best: best = v; ang = a
    return best, ang

# preenchimento: o miolo dos quarteirões e os vãos do centro (alinhado à rua mais próxima)
for gx in range(0, int(WX), 15):
    for gz in range(0, int(WZ), 15):
        x = gx + rng.uniform(0, 10); z = gz + rng.uniform(0, 10)
        u = urban(x, z)
        if u < 0.06: continue
        if rng.random() > min(0.92, 0.22 + 0.95 * u): continue
        dist, ang = nearest_road(x, z)
        if dist < 9 or dist > 85: continue
        kind = pick_kind(u, 3, False)
        if dist > 40 and kind in (4, 5): kind = 3
        w, dd, fl, _ = dims(kind, u)
        if rng.random() < 0.5: ang += math.pi / 2
        if fits(x, z, w, dd, ang, kind):
            b = put(x, z, w, dd, fl, ang, kind, 3 if kind == 5 else (2 if kind == 4 and fl > 7 else 0))

# ---------------------------------------------------------------- postes, hidrantes, árvores de rua
LAMP, HYD = [], []
lamp_pts = []
def in_gap(gaps, s):
    for i in range(0, len(gaps) - 1, 2):
        if gaps[i] - 3 <= s <= gaps[i + 1] + 3: return True
    return False

for r in ROADS:
    c = r['c']
    if c == 0: continue
    P, cs = r['P'], r['cs']
    hw = r['w'] / 2
    cw = CW[c]
    s_a, s_b = max(r['a'], 0) + 8.0, cs[-1] - max(r['b'], 0) - 8.0
    step = 34.0 if c <= 2 else 44.0
    off_lamp = hw + 0.35 + (0.55 if c <= 1 else (cw - 0.35) * 0.45)
    s = s_a + rng.uniform(0, step * 0.5); side = 1; k = 0
    while s < s_b:
        q = max(1, next((i for i in range(1, len(cs)) if cs[i] >= s), len(cs) - 1))
        f = (s - cs[q - 1]) / max(cs[q] - cs[q - 1], 1e-6)
        x = P[q - 1][0] + (P[q][0] - P[q - 1][0]) * f; z = P[q - 1][1] + (P[q][1] - P[q - 1][1]) * f
        tx, tz = P[q][0] - P[q - 1][0], P[q][1] - P[q - 1][1]
        L = math.hypot(tx, tz) or 1.0; tx /= L; tz /= L
        sides = (1, -1) if c <= 1 else (side,)
        for sg in sides:
            gaps = r['cl'] if sg == 1 else r['cr']
            if P[q][3] or P[q - 1][3]: continue
            if in_gap(gaps, s): continue
            lx = x - tz * sg * off_lamp; lz = z + tx * sg * off_lamp
            if hgt(lx, lz) < 1.2: continue
            if any(math.hypot(lx - hx, lz - hz) < hr + 8 for hx, hz, hr in HUBS): continue
            # a luminária aponta do poste para o eixo da rua
            LAMP.append([round(lx, 1), round(lz, 1), round(math.atan2(-(tx * sg), tz * sg), 3), 1 if c <= 1 else 0])
            lamp_pts.append((lx, lz))
        if c >= 2 and k % 2 == 1:   # hidrante a cada ~90 m, alternando o lado
            sg = side
            gaps = r['cl'] if sg == 1 else r['cr']
            if not in_gap(gaps, s + 9) and not (P[q][3] or P[q - 1][3]):
                hx_ = x - tz * sg * (hw + 0.55) + tx * 9; hz_ = z + tx * sg * (hw + 0.55) + tz * 9
                if hgt(hx_, hz_) > 1.2 and not any(math.hypot(hx_ - hx, hz_ - hz) < hr + 10 for hx, hz, hr in HUBS): HYD.append([round(hx_, 1), round(hz_, 1)])
        side = -side; k += 1; s += step

# árvores de rua (calçadas de bairro): a cada ~15 m, só onde há bairro
for r in ROADS:
    c = r['c']
    if c < 2: continue
    P, cs = r['P'], r['cs']
    hw = r['w'] / 2; cw = CW[c]
    s_a, s_b = max(r['a'], 0) + 10.0, cs[-1] - max(r['b'], 0) - 10.0
    s = s_a + rng.uniform(0, 7); side = 1
    while s < s_b:
        q = max(1, next((i for i in range(1, len(cs)) if cs[i] >= s), len(cs) - 1))
        f = (s - cs[q - 1]) / max(cs[q] - cs[q - 1], 1e-6)
        x = P[q - 1][0] + (P[q][0] - P[q - 1][0]) * f; z = P[q - 1][1] + (P[q][1] - P[q - 1][1]) * f
        tx, tz = P[q][0] - P[q - 1][0], P[q][1] - P[q - 1][1]
        L = math.hypot(tx, tz) or 1.0; tx /= L; tz /= L
        sg = side
        gaps = r['cl'] if sg == 1 else r['cr']
        px = x - tz * sg * (hw + 0.35 + (cw - 0.35) * 0.62); pz = z + tx * sg * (hw + 0.35 + (cw - 0.35) * 0.62)
        if (not in_gap(gaps, s)) and not (P[q][3] or P[q - 1][3]) and hgt(px, pz) > 1.6 and rng.random() < 0.8 \
           and not any(math.hypot(px - lx, pz - lz) < 4.5 for lx, lz in lamp_pts[-60:]) \
           and not any(math.hypot(px - hx, pz - hz) < hr + 9 for hx, hz, hr in HUBS) and urban(px, pz) < 0.75:
            tree(px, pz, rng.choice((1, 2, 2, 0)) if urban(px, pz) < 0.4 else 1, rng.uniform(0.62, 0.85))
        side = -side; s += 15.0

# árvores nas ilhas das rotatórias (menos a Praça Central, onde passa a rodovia)
for hx, hz, hr in HUBS[1:]:
    ri = hr * 0.45
    for k in range(6):
        a = k * math.pi / 3 + rng.uniform(-0.2, 0.2)
        tree(hx + math.cos(a) * ri * 0.55, hz + math.sin(a) * ri * 0.55, 2 if k % 2 else 1, rng.uniform(0.7, 0.9))

# mata/morro: só fora da cidade, em manchas (ruído de baixa frequência), longe de ruas e prédios
def noise(x, z):
    return (math.sin(x * 0.0051 + 1.3) * math.sin(z * 0.0043 + 0.4) + math.sin(x * 0.0113 + z * 0.0071 + 2.0) * 0.6
            + math.sin(x * 0.0021 - z * 0.0089) * 0.5) / 2.1
bld_free = lambda x, z, m: all(math.hypot(o['x'] - x, o['z'] - z) > 0.5 * math.hypot(o['w'], o['d']) + m for o in gnear(bld_grid, x, z, 2))
for gx in range(0, int(WX), 22):
    for gz in range(0, int(WZ), 22):
        x = gx + rng.uniform(0, 14); z = gz + rng.uniform(0, 14)
        if x < 12 or z < 12 or x > WX - 12 or z > WZ - 12: continue
        h = hgt(x, z)
        if h < 2.4: continue
        n = noise(x, z)
        p = 0.10 + 0.55 * max(0.0, n) + 0.30 * min(1.0, max(0.0, (h - 20) / 30))
        if urban(x, z) > 0.18: p *= 0.15
        if rng.random() > p: continue
        if slope(x, z) > 0.32: continue
        if road_clear(x, z, 16) < 0 or near_house(x, z, 80) or not bld_free(x, z, 14): continue
        sp = 3 if (h > 28 or (h > 14 and rng.random() < (h - 14) / 22)) else rng.choice((0, 0, 1, 1, 2))
        tree(x, z, sp, rng.uniform(0.8, 1.45) if sp != 3 else rng.uniform(1.1, 1.7))

d['bld'] = [round(v, 2) if isinstance(v, float) else v for b in BLD for v in (b['x'], b['z'], b['w'], b['d'], b['fl'], b['ang'], b['k'], b['seed'], b['pod'])]
d['lamp'] = [v for l in LAMP for v in l]
d['hyd'] = [v for h in HYD for v in h]
d['tree'] = [v for t in TREES for v in t]
json.dump(d, open(SRC, 'w'), separators=(',', ':'))
from collections import Counter
print('prédios', len(BLD), dict(Counter(b['k'] for b in BLD)), '| postes', len(LAMP), '| hidrantes', len(HYD), '| árvores', len(TREES))
