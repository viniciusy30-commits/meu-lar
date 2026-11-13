#!/usr/bin/env python3
"""Gerador do BAIRRO (Cidade 3 / Meu Lar) - estilo americano de subúrbio.
Saídas (copiar para app/src/main/assets/hds/):
  sub.json      ruas, nós (cul-de-sac), casa do jogador (Casa 1 do Hds), postes, hidrantes, árvores, colisões
  sub.bin       terreno (mesmo formato do relevo.bin: nx, nz, passo, alturas em cm)
  sub_mesh.bin  casas, garagens, calçadas de entrada, cercas, carros, caixas de correio, postes... (malha assada)
Rodar:  python3 gen_bairro.py          (usa house.py e bake.py na mesma pasta)
Prévia: python3 preview.py saida.png cx cz meia_largura(m) azimute elevação
"""
import json, math, random, struct, sys
import numpy as np
from bake import *
import house as HS
import fences as FN

WX, WZ, G = 1000.0, 800.0, 8.0
NX, NZ = int(WX / G) + 1, int(WZ / G) + 1
ROADY = 0.12
HX, ZB = 470.0, 360.0             # centro da Casa 1 (x) e eixo da rua Maple na frente dela (z)
CASA1_L, CASA1_R, CASA1_N, CASA1_S = -9.035, 7.065, -10.0, 10.0   # lote da Casa 1 em relação ao centro da casa (cerca do Hds)
rnd = random.Random(186)


def sstep(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def raw_terrain(x, z):
    return (7.0 + 1.3 * math.sin(x / 190 + 0.7) * math.cos(z / 150 + 0.3) + 0.9 * math.sin((x * 0.6 + z) / 210 + 1.1)
            + 0.45 * math.sin(x / 70) * math.sin(z / 85 + 0.5))


HZ = ZB + 3.7 + 3.4 + 0.5 - CASA1_N          # frente da cerca fica 0,5 m depois da calçada
H0 = round(raw_terrain(HX, HZ), 2)


def terrain_node(x, z):
    d = math.hypot(x - HX, z - HZ)
    s = sstep((d - 30.0) / 45.0)
    return H0 * (1 - s) + raw_terrain(x, z) * s


HMAP = np.zeros((NZ, NX), dtype=np.int16)
for j in range(NZ):
    for i in range(NX):
        HMAP[j, i] = int(round(terrain_node(i * G, j * G) * 100))


def height(x, z):
    fx = min(max(x / G, 0.0), NX - 1.001); fz = min(max(z / G, 0.0), NZ - 1.001)
    i = int(fx); j = int(fz); tx = fx - i; tz = fz - j
    a = HMAP[j, i] / 100.0; b = HMAP[j, i + 1] / 100.0; c = HMAP[j + 1, i] / 100.0; d = HMAP[j + 1, i + 1] / 100.0
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz


# ------------------------------------------------------------------------------------------------------------
# ruas
# ------------------------------------------------------------------------------------------------------------
CWF = {4: 3.4, 5: 3.4}


def catmull(pts, step=3.5):
    P = [np.array(p, float) for p in pts]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        L = float(np.hypot(*(p2 - p1)))
        n = max(2, int(L / step))
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return np.array(out)


class Road:
    def __init__(self, name, c, w, ctrl, step=3.5):
        self.name, self.c, self.w = name, c, w
        self.P = catmull(ctrl, step)
        d = np.hypot(*np.diff(self.P, axis=0).T)
        self.cs = np.r_[0, np.cumsum(d)]
        self.L = float(self.cs[-1])
        self.hw = w / 2
        self.cw = CWF[c]
        self.gl, self.gr = [], []
        self.ta = 0.0; self.tb = 0.0

    def at(self, s):
        s = min(max(s, 0.0), self.L)
        k = int(np.searchsorted(self.cs, s, side='right')) - 1
        k = min(max(k, 0), len(self.P) - 2)
        t = (s - self.cs[k]) / max(self.cs[k + 1] - self.cs[k], 1e-9)
        p = self.P[k] * (1 - t) + self.P[k + 1] * t
        tg = self.P[k + 1] - self.P[k]
        tg = tg / max(np.hypot(*tg), 1e-9)
        return p, tg                      # ponto e tangente; normal +n = (-tz, tx)

    def proj(self, x, z):
        best = 1e18; bs = 0.0
        for k in range(len(self.P) - 1):
            a = self.P[k]; b = self.P[k + 1]
            v = b - a; l2 = float(v @ v)
            t = 0.0 if l2 < 1e-9 else max(0.0, min(1.0, float(((np.array([x, z]) - a) @ v) / l2)))
            q = a + v * t
            d = math.hypot(x - q[0], z - q[1])
            if d < best:
                best = d; bs = self.cs[k] + t * math.sqrt(l2)
        return bs, best


def oak_z(x):
    xs = [0, 150, 300, 440, 560, 700, 850, 1000]
    zs = [268, 262, 266, 270, 266, 258, 252, 256]
    return float(np.interp(x, xs, zs))


J1X, J2X, BX = 385.0, 605.0, 545.0
OAK = Road('Oak Avenue', 5, 9.0, [(0, 268), (150, 262), (300, 266), (440, 270), (560, 266), (700, 258), (850, 252), (1000, 256)], 4.0)
# a rua Maple faz um laço: sai da Oak, desce, passa reta na frente da Casa 1 e volta para a Oak
MAPLE = Road('Maple Street', 4, 7.4, [(J1X, oak_z(J1X)), (384.5, 300), (388, 330), (402, 349), (425, 358), (450, 360), (500, 360), (550, 360),
                                       (578, 357), (596, 345), (606, 322), (607, 295), (J2X, oak_z(J2X))], 3.5)
BIRCH_END = (546.0, 492.0)
BIRCH = Road('Birch Court', 4, 7.0, [(BX, ZB), (BX + 0.5, 400), (BX + 1.0, 440), (BIRCH_END[0], BIRCH_END[1])], 3.5)
PAD_R = 12.5
ROADS = [OAK, MAPLE, BIRCH]


def cross_gap(main, pt, other_w, side_of):
    s, _ = main.proj(*pt)
    half = other_w / 2 + 0.7
    return s, half


# bocas de meio-fio: onde uma rua desemboca, some a calçada nos dois lados
def junction_gaps():
    for (road, e0, e1) in ((MAPLE, 0, 1), (MAPLE, 1, 0)):
        pass
    # Maple início e fim sobre a Oak
    hwO = OAK.hw + 0.7
    MAPLE.gl.extend([0.0, hwO]); MAPLE.gr.extend([0.0, hwO])
    MAPLE.gl.extend([MAPLE.L - hwO, MAPLE.L]); MAPLE.gr.extend([MAPLE.L - hwO, MAPLE.L])
    MAPLE.ta = OAK.hw + 1.0; MAPLE.tb = OAK.hw + 1.0
    for x in (J1X, J2X):
        s, d = OAK.proj(x, oak_z(x))
        OAK.gl.extend([s - MAPLE.hw - 0.7, s + MAPLE.hw + 0.7])          # lado sul (+n) da Oak
    # Birch sai da Maple (lado sul = +n quando a Maple vai para leste)
    s, d = MAPLE.proj(BX, ZB)
    MAPLE.gl.extend([s - BIRCH.hw - 0.7, s + BIRCH.hw + 0.7])
    hwM = MAPLE.hw + 0.7
    BIRCH.gl.extend([0.0, hwM]); BIRCH.gr.extend([0.0, hwM])
    BIRCH.gl.extend([BIRCH.L - PAD_R - 0.2, BIRCH.L]); BIRCH.gr.extend([BIRCH.L - PAD_R - 0.2, BIRCH.L])
    BIRCH.ta = MAPLE.hw + 1.0
    for r in ROADS:
        for g in (r.gl, r.gr):
            pairs = sorted((g[i], g[i + 1]) for i in range(0, len(g), 2))
            m = []
            for a, b in pairs:
                if m and a <= m[-1][1] + 0.3:
                    m[-1][1] = max(m[-1][1], b)
                else:
                    m.append([a, b])
            g[:] = [v for ab in m for v in ab]


junction_gaps()


def smooth_y(road):
    """altura do centro da rua: terreno suavizado ao longo do eixo (o app ainda levanta onde o terreno encostar)"""
    hs = np.array([height(p[0], p[1]) for p in road.P])
    k = 5
    ker = np.ones(2 * k + 1) / (2 * k + 1)
    pad = np.r_[np.full(k, hs[0]), hs, np.full(k, hs[-1])]
    sm = np.convolve(pad, ker, mode='valid')
    return sm - 0.09


# ------------------------------------------------------------------------------------------------------------
# lotes
# ------------------------------------------------------------------------------------------------------------
def poly_overlap(A, B):
    for P in (A, B):
        n = len(P)
        for i in range(n):
            a = P[i]; b = P[(i + 1) % n]
            ax, az = -(b[1] - a[1]), b[0] - a[0]
            pa = [ax * p[0] + az * p[1] for p in A]; pb = [ax * p[0] + az * p[1] for p in B]
            if max(pa) < min(pb) - 1e-6 or max(pb) < min(pa) - 1e-6:
                return False
    return True


def dist_poly_road(poly, road, step=2.5):
    pts = []
    n = len(poly)
    for i in range(n):
        a = np.array(poly[i]); b = np.array(poly[(i + 1) % n])
        for t in np.linspace(0, 1, 8, endpoint=False):
            pts.append(a * (1 - t) + b * t)
    c = np.mean(np.array(poly), axis=0)
    xs = np.array(poly)
    for gx in np.arange(xs[:, 0].min(), xs[:, 0].max() + 0.01, 4.0):
        for gz in np.arange(xs[:, 1].min(), xs[:, 1].max() + 0.01, 4.0):
            pts.append(np.array([gx, gz]))
    pts = np.array(pts)
    A = road.P[:-1]; B = road.P[1:]
    best = 1e18
    for q in pts:
        v = B - A; w_ = q - A
        l2 = (v * v).sum(axis=1)
        t = np.clip((w_ * v).sum(axis=1) / np.maximum(l2, 1e-9), 0, 1)
        proj = A + v * t[:, None]
        d = np.hypot(*(proj - q).T).min()
        best = min(best, d)
    return best


CASA1_RECT = [(HX + CASA1_L - 2.5, HZ + CASA1_N - 3.0), (HX + CASA1_R + 2.5, HZ + CASA1_N - 3.0), (HX + CASA1_R + 2.5, HZ + CASA1_S + 3.0), (HX + CASA1_L - 2.5, HZ + CASA1_S + 3.0)]
LOTS = []          # dict(poly, road, side, ...)
BULB_CLEAR = PAD_R + 1.2 + 3.0


def lot_ok(poly):
    for p in poly:
        if p[0] < 40 or p[0] > WX - 40 or p[1] < 40 or p[1] > WZ - 40:
            return False
    if poly_overlap(poly, CASA1_RECT):
        return False
    for L in LOTS:
        if poly_overlap(poly, L['poly']):
            return False
    for r in ROADS:
        if dist_poly_road(poly, r) < r.hw + r.cw + 0.25:
            return False
    bx, bz = BIRCH_END
    for p in poly + [tuple(np.mean(np.array(poly), axis=0))]:
        if math.hypot(p[0] - bx, p[1] - bz) < BULB_CLEAR:
            return False
    return True


def make_spec(road, side, s, wlot, dlot):
    p, tg = road.at(s)
    n = np.array([-tg[1], tg[0]]) * side            # para dentro do lote
    off = road.hw + road.cw + 0.5
    F = p + n * off
    t = tg
    poly = [tuple(F - t * wlot / 2), tuple(F + t * wlot / 2), tuple(F + t * wlot / 2 + n * dlot), tuple(F - t * wlot / 2 + n * dlot)]
    return dict(poly=poly, F=F, t=t, m=n, w=wlot, d=dlot, road=road, side=side, s=s)


def scan_row(road, side, s0, s1, dlot=34.0, wr=(20.0, 25.0)):
    s = s0
    while s < s1:
        wl = rnd.uniform(*wr)
        sp = make_spec(road, side, s + wl / 2, wl, dlot)
        if lot_ok(sp['poly']):
            LOTS.append(sp)
            s += wl + rnd.uniform(0.3, 1.5)
        else:
            s += 2.0


# ordem de prioridade: frente da Casa 1 e arredores primeiro
scan_row(MAPLE, +1, 60.0, MAPLE.L - 14.0)         # lado sul da Maple (frente para o norte)
scan_row(MAPLE, -1, 60.0, MAPLE.L - 14.0)         # lado norte da Maple (dentro do laço)
scan_row(MAPLE, +1, 14.0, 60.0)
scan_row(MAPLE, -1, 14.0, 60.0)
scan_row(OAK, -1, 330.0, 670.0, 36.0)             # Oak, lado norte
scan_row(OAK, +1, 330.0, 670.0, 34.0)             # Oak, lado sul
scan_row(BIRCH, +1, 12.0, BIRCH.L - 6.0, 34.0)    # Birch (oeste / leste)
scan_row(BIRCH, -1, 12.0, BIRCH.L - 6.0, 34.0)
print('lotes:', len(LOTS))

# ------------------------------------------------------------------------------------------------------------
# casas, adereços e objetos
# ------------------------------------------------------------------------------------------------------------
bk = Bake()
SOLIDS = []        # [x0,z0,x1,z1] em coordenadas relativas
HOUSES_INFO = []
DRIVES = []        # (x,z) pontos das entradas de garagem, para afastar árvores/postes
TREES = []         # x,z,sp,scale,rot,tone
LAMPS = []
HYDS = []


def add_solid_obb(cx, cz, ang, u0, u1, v0, v1, pad=0.15):
    """colisão de um retângulo girado em fatias de ~1,5 m (cada fatia vira um retângulo alinhado aos eixos)"""
    c, s = math.cos(ang), math.sin(ang)
    n = max(1, int(math.ceil((u1 - u0) / 1.5)))
    for k in range(n):
        ua = u0 + (u1 - u0) * k / n; ub = u0 + (u1 - u0) * (k + 1) / n
        xs = []; zs = []
        for (u, v) in ((ua, v0), (ub, v0), (ub, v1), (ua, v1)):
            xs.append(cx + c * u - s * v); zs.append(cz + s * u + c * v)
        SOLIDS.append([round(min(xs) - pad, 2), round(min(zs) - pad, 2), round(max(xs) + pad, 2), round(max(zs) + pad, 2)])


def house_for_lot(L, idx):
    r = rnd
    m = L['m']; t = L['t']
    style = r.choice(['colonial', 'craftsman', 'ranch', 'cape', 'colonial', 'ranch'])
    fl = 2 if style in ('colonial', 'cape') and r.random() < 0.75 else 1
    w = r.uniform(9.0, 11.8) if fl == 2 else r.uniform(10.0, 13.0)
    d = r.uniform(7.6, 9.6)
    garage = 2 if r.random() < 0.5 else (1 if r.random() < 0.7 else 0)
    gside = r.choice([-1, 1])
    gwid = {0: 0.0, 1: 3.5, 2: 6.1}[garage]
    # largura total (casa + garagem) cabe no lote?
    while w + gwid > L['w'] - 3.5 and (w > 8.2 or garage > 0):
        if garage == 2:
            garage = 1; gwid = 3.5
        elif w > 8.2:
            w -= 0.6
        else:
            garage = 0; gwid = 0.0
    setb = r.uniform(7.0, 9.5)
    a = math.atan2(-m[0], m[1])
    fvec = np.array([math.sin(a), -math.cos(a)])           # frente da casa (deve ser -m)
    ctr = L['F'] + m * (setb + d / 2) - t * (gside * gwid / 2) * (1 if garage else 0)
    if garage:
        ctr = ctr + t * r.uniform(-0.8, 0.8)
    # u (eixo da largura) = (cos a, sin a)  -> compara com a tangente t para saber o sinal de gside
    ux = np.array([math.cos(a), math.sin(a)])
    sg = 1 if float(ux @ t) >= 0 else -1
    ctr = L['F'] + m * (setb + d / 2) - ux * (gside * gwid / 2)
    spec = dict(x=float(ctr[0]), z=float(ctr[1]), ang=a, style=style, w=w, d=d, floors=fl, garage=garage, gside=gside,
                wall=r.choice(HS.SIDING), roof=r.choice(HS.ROOFC), accent=r.choice(HS.ACCENT),
                door_u=-gside * r.uniform(0.3, 1.2) if garage else r.uniform(-1.2, 1.2),
                grecess=r.choice([0.0, 0.0, 0.8, 1.5]), fg=(style == 'craftsman' and r.random() < 0.6),
                shutters=(style == 'colonial' or r.random() < 0.2), flowers=r.random() < 0.3, flag=r.random() < 0.18,
                chimney=r.random() < 0.55)
    return spec, setb


def hf(x, z):
    return height(x, z)


for idx, L in enumerate(LOTS):
    spec, setb = house_for_lot(L, idx)
    info = HS.make_house(bk, hf, spec, rnd)
    h = info['h']
    L['house'] = spec
    # colisão: corpo + garagem + varanda
    for (u0, v0, u1, v1) in info['foot']:
        add_solid_obb(spec['x'], spec['z'], spec['ang'], u0 + 0.45, u1 - 0.45, v0 + (0.6 if v0 < -spec['d'] / 2 - 1 else 0.45), v1 - 0.45, 0.1)
    # entrada de garagem + caminho até a porta
    m = L['m']; t = L['t']
    yfun = hf
    if info['drive'] is not None:
        dv = info['drive']
        vfront = -spec['d'] / 2 - 0.0
        # do portão da garagem até a borda do lote (frente), em coordenadas locais de v
        vend = -(setb + spec['d'] / 2) + 0.05
        # nota: a casa fica a setb + d/2 da borda; a frente do lote está em v = -(setb + d/2)
        subs = 4
        for k in range(subs):
            v0 = (dv['v'] + (vend - dv['v']) * k / subs); v1 = (dv['v'] + (vend - dv['v']) * (k + 1) / subs)
            pts = []
            for (u, v) in ((dv['u0'], v0), (dv['u1'], v0), (dv['u1'], v1), (dv['u0'], v1)):
                x, z = h.W(u, v); pts.append((x, hf(x, z) + 0.035, z))
            bk.quad(PLAIN, pts, (0, 1, 0), HS.CONC)
        xc, zc = h.W((dv['u0'] + dv['u1']) / 2, vend)
        DRIVES.append((xc, zc))
        # juntas de concreto
        for k in range(1, 5):
            vv = dv['v'] + (vend - dv['v']) * k / 5
            pts = []
            for (u, v) in ((dv['u0'], vv - 0.02), (dv['u1'], vv - 0.02), (dv['u1'], vv + 0.02), (dv['u0'], vv + 0.02)):
                x, z = h.W(u, v); pts.append((x, hf(x, z) + 0.04, z))
            bk.quad(PLAIN, pts, (0, 1, 0), HS.CONC_D)
        # carro na garagem
        if rnd.random() < 0.75:
            vc = dv['v'] - 3.2
            cxw, czw = h.W((dv['u0'] + dv['u1']) / 2 + (0 if spec['garage'] == 1 else rnd.choice([-1.4, 1.4])), vc)
            HS.car(bk, hf, cxw, czw, spec['ang'] + math.pi / 2, rnd.choice(HS.CARS))
    # caminho da porta até a calçada
    pw = info['pw']; du = spec['door_u']
    vstart = -spec['d'] / 2 - info['pd'] - 0.5
    vend = -(setb + spec['d'] / 2) + 0.05
    for k in range(4):
        v0 = vstart + (vend - vstart) * k / 4; v1 = vstart + (vend - vstart) * (k + 1) / 4
        pts = []
        for (u, v) in ((du - 0.6, v0), (du + 0.6, v0), (du + 0.6, v1), (du - 0.6, v1)):
            x, z = h.W(u, v); pts.append((x, hf(x, z) + 0.03, z))
        bk.quad(PLAIN, pts, (0, 1, 0), HS.CONC)
    # vãos da cerca da frente: entrada de carros e caminho da porta (u ao longo da rua, a partir do centro do lote)
    def uproj(u_, v_):
        x_, z_ = h.W(u_, v_); return float((np.array([x_, z_]) - L['F']) @ L['t'])
    gaps_ = []
    if info['drive'] is not None:
        ua = uproj(info['drive']['u0'], vend); ub = uproj(info['drive']['u1'], vend)
        gaps_.append((min(ua, ub) - 0.25, max(ua, ub) + 0.25))
    uc = uproj(du, vend); gaps_.append((uc - 0.75, uc + 0.75))
    L['gaps'] = gaps_; L['setb'] = setb
    # caixa de correio na borda da calçada, do lado oposto à garagem
    mx, mz = h.W(du + (spec['gside'] * -1) * 3.5 if spec['garage'] else du + 3.0, vend - 0.8 - 2.2)
    # posição: no gramado entre calçada e meio-fio
    ptc = L['F'] - m * (0.5 + 1.5 + 0.35) + t * float((np.array([mx, mz]) - L['F']) @ t)
    HS.mailbox(bk, hf, float(ptc[0]), float(ptc[1]), spec['ang'] + math.pi, rnd)
    # lixeiras (às vezes)
    if rnd.random() < 0.3 and info['drive'] is not None:
        dv = info['drive']
        tx_, tz_ = h.W(dv['u1'] + 0.8 if spec['gside'] > 0 else dv['u0'] - 1.7, -spec['d'] / 2 + 0.2 + spec['grecess'])
        HS.trash_cans(bk, hf, tx_, tz_, spec['ang'])
    # cerca branca na frente (às vezes) ou sebe
    ff = rnd.random()
    if False:   # cercas agora vêm de fences.py (por lote, com vãos)
        ux = np.array([math.cos(spec['ang']), math.sin(spec['ang'])])
        a0 = L['F'] - L['t'] * (L['w'] / 2 - 1.2) + m * 0.2
        a1 = L['F'] + L['t'] * (L['w'] / 2 - 1.2) + m * 0.2
        HS.picket_fence(bk, hf, float(a0[0]), float(a0[1]), float(a1[0]), float(a1[1]))
    # um carro na calçada (rua) de vez em quando
    # árvores do lote: frente e fundos
    for k in range(rnd.choice([1, 1, 2])):
        tp = L['F'] + L['t'] * rnd.uniform(-L['w'] / 2 + 3, L['w'] / 2 - 3) + m * rnd.uniform(2.2, setb - 2.5)
        ok = all(math.hypot(tp[0] - dx_, tp[1] - dz_) > 5.5 for (dx_, dz_) in DRIVES)
        if ok:
            TREES.append((float(tp[0]), float(tp[1]), rnd.choice([0, 0, 1, 2]), rnd.uniform(1.0, 1.6), rnd.uniform(0, 6.28), rnd.uniform(0.9, 1.1)))
    for k in range(rnd.choice([1, 2, 2])):
        tp = L['F'] + L['t'] * rnd.uniform(-L['w'] / 2 + 3, L['w'] / 2 - 3) + m * rnd.uniform(setb + spec['d'] + 3, L['d'] - 3)
        TREES.append((float(tp[0]), float(tp[1]), rnd.choice([0, 1, 0, 3]), rnd.uniform(1.3, 2.1), rnd.uniform(0, 6.28), rnd.uniform(0.85, 1.1)))

# cercas, gramados e extras de quintal (fences.py), depois que casas e árvores dos lotes já existem
FN.build_all(bk, hf, lambda cx, cz, a, u0, u1, v0, v1, pad=0.1: add_solid_obb(cx, cz, a, u0, u1, v0, v1, pad), LOTS, TREES)

# ------------------------------------------------------------------------------------------------------------
# Casa 1 (jogador): caminho do portão até a calçada, caixa de correio, carro estacionado na rua é do app (Tesla)
# ------------------------------------------------------------------------------------------------------------
ffz = HZ + CASA1_N           # linha da cerca da frente
gate_x = HX - 1.95
for k in range(2):
    zz0 = ffz - 2.4 + k * 1.2; zz1 = zz0 + 1.2
    bk.quad(PLAIN, [(gate_x - 0.7, height(gate_x, zz0) + 0.03, zz0), (gate_x + 0.7, height(gate_x, zz0) + 0.03, zz0),
                    (gate_x + 0.7, height(gate_x, zz1) + 0.03, zz1), (gate_x - 0.7, height(gate_x, zz1) + 0.03, zz1)], (0, 1, 0), HS.CONC)
HS.mailbox(bk, hf, gate_x + 3.4, ZB + 3.7 + 1.25, math.pi, rnd)
TREES.append((HX + 9.8, ZB + 3.7 + 1.1, 0, 1.5, 1.0, 1.0))

# ------------------------------------------------------------------------------------------------------------
# postes, placas e árvores de rua
# ------------------------------------------------------------------------------------------------------------
def near_any(p, pts, d):
    return any(math.hypot(p[0] - q[0], p[1] - q[1]) < d for q in pts)


def lateral_point(road, s, off, side):
    p, tg = road.at(s)
    n = np.array([-tg[1], tg[0]]) * side
    return p + n * off, tg, n


JUNC_PTS = [(J1X, oak_z(J1X)), (J2X, oak_z(J2X)), (BX, ZB), BIRCH_END]
for road in ROADS:
    s = 14.0
    k = 0
    while s < road.L - 10:
        for side in (1, -1):
            if road is OAK and (s < 120 or s > OAK.L - 120):
                pass
            q, tg, n = lateral_point(road, s + (7.0 if side < 0 else 0.0), road.hw + 1.15, side)
            if near_any(q, DRIVES, 4.0) or near_any(q, JUNC_PTS, road.hw + 9.0):
                continue
            if not (40 < q[0] < WX - 40 and 40 < q[1] < WZ - 40):
                continue
            TREES.append((float(q[0]), float(q[1]), rnd.choice([0, 1, 0, 1, 2]), rnd.uniform(1.35, 1.9), rnd.uniform(0, 6.28), rnd.uniform(0.9, 1.1)))
        s += rnd.uniform(15.0, 19.0)
    # postes de luz a cada ~50 m, alternando o lado
    s = 22.0
    side = 1
    while s < road.L - 14:
        q, tg, n = lateral_point(road, s, road.hw + 1.0, side)
        if not near_any(q, DRIVES, 3.5) and not near_any(q, JUNC_PTS, road.hw + 5.0) and 40 < q[0] < WX - 40:
            ang = math.atan2(-n[1], -n[0])          # braço aponta para a rua
            LAMPS.append((float(q[0]), float(q[1]), float(ang), 0))
        side = -side
        s += 52.0
    # hidrantes
    s = 40.0
    while s < road.L - 20:
        q, tg, n = lateral_point(road, s, road.hw + 1.75, 1)
        if not near_any(q, DRIVES, 3.0) and not near_any(q, JUNC_PTS, road.hw + 6.0) and 40 < q[0] < WX - 40:
            HYDS.append((float(q[0]), float(q[1])))
        s += 96.0

# postes de energia (madeira) ao longo da Oak, atrás da calçada do lado norte
s = 30.0
while s < OAK.L - 20:
    q, tg, n = lateral_point(OAK, s, OAK.hw + OAK.cw + 1.6, -1)
    HS.utility_pole(bk, hf, float(q[0]), float(q[1]), math.atan2(tg[1], tg[0]))
    s += 46.0
# placas de PARE e de nome de rua nas esquinas
for (road, s_, side, nm) in ((MAPLE, 9.0, +1, 'Maple'), (MAPLE, MAPLE.L - 9.0, +1, 'Maple'), (BIRCH, 9.0, +1, 'Birch')):
    q, tg, n = lateral_point(road, s_, road.hw + 0.9, side)
    # a placa fica no lado direito de quem sai da rua para a Oak/Maple, virada para a rua
    face = math.atan2(-tg[0] if s_ < 5 else tg[0], 0.0)
    ang = math.atan2(tg[0], -tg[1])
    HS.stop_sign(bk, hf, float(q[0]), float(q[1]), math.atan2(float(tg[1]), -float(tg[0])) if False else math.atan2(-float(tg[0]) * (1 if s_ < 20 else -1), float(tg[1]) * (1 if s_ < 20 else -1)) * 0 + (math.pi / 2 if s_ < 20 else -math.pi / 2) + math.atan2(float(tg[1]), float(tg[0])) - math.pi / 2)
    HS.street_sign(bk, hf, float(q[0]) + 0.6, float(q[1]), 0.0)

# ------------------------------------------------------------------------------------------------------------
# floresta em volta (bordas do mapa) e bosques soltos
# ------------------------------------------------------------------------------------------------------------
def min_dist_roads(x, z):
    best = 1e9
    for r in ROADS:
        s, d = r.proj(x, z)
        best = min(best, d - r.hw - r.cw)
    return best


lot_polys = [L['poly'] for L in LOTS]


def in_any_lot(x, z, margin=1.5):
    for L in LOTS:
        p = L['poly']
        # distância aproximada ao centro do lote
        c = np.mean(np.array(p), axis=0)
        if math.hypot(x - c[0], z - c[1]) < L['w'] * 0.7 + L['d'] * 0.35 + margin:
            # teste exato por projeção
            rel = np.array([x, z]) - L['F']
            u = float(rel @ L['t']); v = float(rel @ L['m'])
            if abs(u) < L['w'] / 2 + margin and -margin < v < L['d'] + margin:
                return True
    return False


spacing = 8.5
forest = 0
for gx in np.arange(10, WX - 10, spacing):
    for gz in np.arange(10, WZ - 10, spacing):
        x = gx + rnd.uniform(-3.2, 3.2); z = gz + rnd.uniform(-3.2, 3.2)
        edge = min(x, WX - x, z, WZ - z)
        # densidade: mata fechada nas bordas, bosques manchados no resto
        n1 = math.sin(x / 61.0 + 1.3) * math.cos(z / 47.0 + 0.4) + 0.6 * math.sin((x + 1.7 * z) / 83.0)
        dens = 0.0
        if edge < 55:
            dens = 0.92
        elif n1 > 0.75:
            dens = 0.55
        elif n1 > 0.35:
            dens = 0.18
        if rnd.random() > dens:
            continue
        if min_dist_roads(x, z) < 6.0 or in_any_lot(x, z, 4.0):
            continue
        if math.hypot(x - HX, z - HZ) < 55:
            continue
        # não invadir o miolo do bairro (entre ruas/lotes)
        if 350 < x < 650 and 245 < z < 520 and edge > 55:
            continue
        sp = rnd.choice([0, 1, 0, 1, 3, 3, 2 if rnd.random() < 0.1 else 0])
        TREES.append((float(x), float(z), sp, rnd.uniform(1.5, 2.5), rnd.uniform(0, 6.28), rnd.uniform(0.8, 1.1)))
        forest += 1
print('árvores:', len(TREES), '(floresta', forest, ')')

# miolo verde entre as casas do laço (quintais: árvores soltas)
for k in range(60):
    x = rnd.uniform(390, 600); z = rnd.uniform(290, 345)
    if not in_any_lot(x, z, 0.5) and min_dist_roads(x, z) > 8:
        TREES.append((x, z, rnd.choice([0, 1]), rnd.uniform(1.3, 2.0), rnd.uniform(0, 6.28), rnd.uniform(0.9, 1.1)))

# ------------------------------------------------------------------------------------------------------------
# saídas
# ------------------------------------------------------------------------------------------------------------
roads_json = []
for r in ROADS:
    y = smooth_y(r)
    flat = []
    for i in range(len(r.P)):
        flat += [round(float(r.P[i, 0]), 2), round(float(r.P[i, 1]), 2), round(float(y[i]), 2), 0]
    d = dict(c=r.c, w=r.w, a=round(r.ta, 1), b=round(r.tb, 1), n=r.name, p=flat)
    if r.gl:
        d['cl'] = [round(v, 1) for v in r.gl]
    if r.gr:
        d['cr'] = [round(v, 1) for v in r.gr]
    roads_json.append(d)
py = round(float(height(BIRCH_END[0], BIRCH_END[1])) - 0.14, 2)
js = dict(world=[WX, WZ], roads=roads_json, rounds=[], nodes=[[BIRCH_END[0], BIRCH_END[1], py, PAD_R, 1]],
          houses=[dict(k=0, x=HX, z=HZ, lvl=H0)], bld=[], lamp=[], hyd=[], tree=[], solid=SOLIDS)
for l in LAMPS:
    js['lamp'] += [round(l[0], 1), round(l[1], 1), round(l[2], 3), l[3]]
for h_ in HYDS:
    js['hyd'] += [round(h_[0], 1), round(h_[1], 1)]
for t in TREES:
    js['tree'] += [round(t[0], 1), round(t[1], 1), t[2], round(t[3], 2), round(t[4], 2), round(t[5], 2)]
out = sys.argv[1] if len(sys.argv) > 1 else '.'
json.dump(js, open(out + '/sub.json', 'w'), separators=(',', ':'))
with open(out + '/sub.bin', 'wb') as f:
    f.write(struct.pack('<iif', NX, NZ, G)); f.write(HMAP.astype('<i2').tobytes())
nrec = bk.write(out + '/sub_mesh.bin')
print('ok: casas', len(LOTS), 'registros de malha', nrec, 'triângulos', bk.ntri, 'solids', len(SOLIDS), 'postes', len(LAMPS), 'hidrantes', len(HYDS))
import pickle
pickle.dump(dict(LOTS=[{k: v for k, v in L.items() if k != 'road'} for L in LOTS], ROADS=[(r.name, r.c, r.w, r.P, r.gl, r.gr, r.cs) for r in ROADS], TREES=TREES, HX=HX, HZ=HZ, H0=H0), open(out + '/state.pkl', 'wb'))
