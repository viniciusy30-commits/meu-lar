"""Cercas, gramados e quintais no estilo americano de subúrbio, por lote.
Cada lote tem: gramado próprio (tom de verde e listras de corte diferentes), cerca da frente (nenhuma, branca de estacas,
sebe, rústica de trilhos, mureta ou alambrado) com vão para a entrada de carros e para o caminho da porta,
e cercas de lado/fundos (madeira fechada, alambrado, estacas) sem duplicar entre vizinhos. Também alguns extras de quintal."""
import math, random
import numpy as np
from bake import *
import house as HS

WOODS = ['#9A7650', '#B08A5E', '#8A6A48', '#C9B79A', '#7B5B3E', '#A68A64']
PAINT = ['#F7F5F0', '#F1ECDD', '#DDE6EC', '#E9E2CF']
GRASS_TONES = ['#A9D48C', '#9CCB82', '#B4DA95', '#A2CE8A', '#B9DC9B', '#97C47E']


def lp(L, u, v):
    p = L['F'] + L['t'] * u + L['m'] * v
    return float(p[0]), float(p[1])


def in_lot(O, x, z, margin=0.0):
    rel = np.array([x, z]) - O['F']
    u = float(rel @ O['t']); v = float(rel @ O['m'])
    return abs(u) <= O['w'] / 2 + margin and -margin <= v <= O['d'] + margin


def _H(bk, hf, x0, z0, ang):
    return HS.H(bk, hf, x0, z0, ang)


def privacy(bk, hf, x0, z0, x1, z1, col, hgt=1.85):
    L = math.hypot(x1 - x0, z1 - z0)
    if L < 0.4:
        return
    ang = math.atan2(z1 - z0, x1 - x0)
    h = _H(bk, hf, x0, z0, ang)
    c = rgb(col)
    n = max(1, int(L / 0.5))
    bw = L / n
    for k in range(n):
        u0 = k * bw; u1 = u0 + bw - 0.02
        x, z = h.W((u0 + u1) / 2, 0); g = hf(x, z)
        h.box(u0, u1, -0.025, 0.025, g - 0.05, g + hgt - (0.06 if k % 2 else 0.0), shade(c, (k % 3) * 5 - 5), PLAIN)
    for k in range(0, int(L / 2.4) + 2):
        u = min(L, k * 2.4)
        x, z = h.W(u, 0); g = hf(x, z)
        h.box(u - 0.07, u + 0.07, -0.06, 0.06, g - 0.05, g + hgt + 0.08, shade(c, -18), PLAIN)
    xa, za = h.W(L / 2, 0)
    h.box(0, L, -0.045, 0.045, hf(xa, za) + hgt, hf(xa, za) + hgt + 0.05, shade(c, -22), PLAIN)


def chain(bk, hf, x0, z0, x1, z1, hgt=1.2):
    L = math.hypot(x1 - x0, z1 - z0)
    if L < 0.4:
        return
    ang = math.atan2(z1 - z0, x1 - x0)
    h = _H(bk, hf, x0, z0, ang)
    post = rgb('#9AA0A6'); wire = rgb('#C7CCD1')
    n = max(2, int(L / 0.32))
    for k in range(n + 1):
        u = L * k / n
        x, z = h.W(u, 0); g = hf(x, z)
        h.box(u - 0.006, u + 0.006, -0.006, 0.006, g, g + hgt - 0.05, wire, PLAIN, top=False)
    xa, za = h.W(L / 2, 0); g = hf(xa, za)
    h.box(0, L, -0.02, 0.02, g + hgt - 0.05, g + hgt, post, PLAIN)
    h.box(0, L, -0.015, 0.015, g + 0.04, g + 0.08, post, PLAIN)
    for k in range(0, int(L / 3.0) + 2):
        u = min(L, k * 3.0)
        x, z = h.W(u, 0); g = hf(x, z)
        h.box(u - 0.035, u + 0.035, -0.035, 0.035, g, g + hgt + 0.06, post, PLAIN)


def splitrail(bk, hf, x0, z0, x1, z1):
    L = math.hypot(x1 - x0, z1 - z0)
    if L < 0.4:
        return
    ang = math.atan2(z1 - z0, x1 - x0)
    h = _H(bk, hf, x0, z0, ang)
    c = rgb('#8B7355')
    n = max(1, int(L / 2.5))
    for k in range(n + 1):
        u = L * k / n
        x, z = h.W(u, 0); g = hf(x, z)
        h.box(u - 0.07, u + 0.07, -0.07, 0.07, g - 0.05, g + 1.0, shade(c, -12), PLAIN)
    xa, za = h.W(L / 2, 0); g = hf(xa, za)
    h.box(0, L, -0.04, 0.04, g + 0.42, g + 0.5, c, PLAIN)
    h.box(0, L, -0.04, 0.04, g + 0.78, g + 0.86, c, PLAIN)


def lowwall(bk, hf, x0, z0, x1, z1, col):
    L = math.hypot(x1 - x0, z1 - z0)
    if L < 0.4:
        return
    ang = math.atan2(z1 - z0, x1 - x0)
    h = _H(bk, hf, x0, z0, ang)
    c = rgb(col)
    n = max(1, int(L / 2.0))
    for k in range(n):
        u0 = L * k / n; u1 = L * (k + 1) / n
        x, z = h.W((u0 + u1) / 2, 0); g = hf(x, z)
        h.box(u0, u1 + 0.01, -0.16, 0.16, g - 0.05, g + 0.55, shade(c, (k % 2) * 6 - 3), PLAIN)
        h.box(u0, u1 + 0.01, -0.2, 0.2, g + 0.55, g + 0.62, shade(c, 25), PLAIN)


def draw_run(bk, hf, solid, style, col, p0, p1, gaps=(), hgt=None, rnd=None):
    """desenha uma cerca de p0 a p1 (mundo); gaps = intervalos (s0, s1) em metros ao longo do trecho"""
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    if L < 0.6 or style == 'none':
        return
    ux = (p1[0] - p0[0]) / L; uz = (p1[1] - p0[1]) / L
    cuts = [0.0]
    for (a, b) in sorted(gaps):
        a = max(0.0, a); b = min(L, b)
        if b <= a:
            continue
        cuts += [a, b]
    cuts.append(L)
    ang = math.atan2(uz, ux)
    for i in range(0, len(cuts), 2):
        s0, s1 = cuts[i], cuts[i + 1]
        if s1 - s0 < 0.5:
            continue
        a = (p0[0] + ux * s0, p0[1] + uz * s0); b = (p0[0] + ux * s1, p0[1] + uz * s1)
        if style == 'picket':
            HS.picket_fence(bk, hf, a[0], a[1], b[0], b[1], rgb(col), hgt or 0.95)
        elif style == 'privacy':
            privacy(bk, hf, a[0], a[1], b[0], b[1], col, hgt or 1.85)
        elif style == 'chain':
            chain(bk, hf, a[0], a[1], b[0], b[1])
        elif style == 'rail':
            splitrail(bk, hf, a[0], a[1], b[0], b[1])
        elif style == 'wall':
            lowwall(bk, hf, a[0], a[1], b[0], b[1], col)
        elif style == 'hedge':
            HS.hedge(bk, hf, a[0], a[1], b[0], b[1], hgt or 1.0, 0.8, rnd)
        solid(a[0], a[1], ang, 0.0, s1 - s0, -0.1, 0.1, 0.08)


def lawn(bk, hf, L, rng):
    """gramado do lote em quadrados de ~4 m (seguem o relevo), cada lote com seu tom e suas listras de corte"""
    base = rgb(rng.choice(GRASS_TONES))
    stripe = rng.random() < 0.7
    nu = max(1, int(L['w'] / 4.0)); nv = max(1, int(L['d'] / 4.0))
    du = L['w'] / nu; dv = L['d'] / nv
    for i in range(nu):
        for j in range(nv):
            u0 = -L['w'] / 2 + i * du; u1 = u0 + du; v0 = 0.1 + j * (L['d'] - 0.1) / nv; v1 = 0.1 + (j + 1) * (L['d'] - 0.1) / nv
            c = shade(base, ((i % 2) * 7 - 3) if stripe else ((i * 7 + j * 3) % 3 - 1) * 2)
            pts = []
            for (u, v) in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
                x, z = lp(L, u, v)
                pts.append((x, hf(x, z) + 0.02, z))
            bk.quad(GRASS, pts, (0, 1, 0), c, [(q[0] * 0.3, q[2] * 0.3) for q in pts])


def yard_extras(bk, hf, solid, L, rng, trees):
    sp = L['house']; setb = L['setb']
    v0 = setb + sp['d'] + 4.0; v1 = L['d'] - 3.0
    if v1 - v0 < 5:
        return
    def free(x, z, r):
        return all(math.hypot(x - t[0], z - t[1]) > r + 1.8 for t in trees)
    r = rng.random()
    u = rng.uniform(-L['w'] / 2 + 5, L['w'] / 2 - 5); v = rng.uniform(v0 + 2, v1 - 2)
    x, z = lp(L, u, v); g = hf(x, z)
    ang = math.atan2(float(L['t'][1]), float(L['t'][0]))
    if not free(x, z, 2.5):
        return
    if r < 0.28:        # casinha de ferramentas
        h = _H(bk, hf, x, z, ang)
        wall = rgb(rng.choice(['#8B2E2E', '#6E7F8D', '#D9D2BE', '#4C6B57', '#9A7650']))
        h.box(-1.2, 1.2, -1.0, 1.0, g - 0.05, g + 2.1, wall, PLAIN)
        h.roof('u', -1.35, 1.35, -1.15, 1.15, g + 2.1, 0.45, rgb('#4F4A47'), wall)
        h.box(-0.5, 0.5, -1.03, -1.0, g, g + 1.8, rgb('#F4F1E8'), PLAIN)
        solid(x, z, ang, -1.3, 1.3, -1.1, 1.1, 0.1)
    elif r < 0.42:      # trampolim
        bk.cyl(x, z, 1.8, g + 0.65, g + 0.7, rgb('#2B2B2E'), 14, PLAIN, True)
        bk.cyl(x, z, 1.9, g + 0.62, g + 0.72, rgb('#2F5DA8'), 14, PLAIN, False)
        for k in range(6):
            a = k * math.pi / 3
            bk.cyl(x + math.cos(a) * 1.8, z + math.sin(a) * 1.8, 0.04, g, g + 0.65, rgb('#9AA0A6'), 4, PLAIN, True)
        solid(x, z, 0.0, -1.9, 1.9, -1.9, 1.9, 0.1)
    elif r < 0.52:      # piscina rasa de lona (acima do solo)
        bk.cyl(x, z, 3.0, g, g + 1.1, rgb('#C9D3DB'), 16, PLAIN, False)
        bk.cyl(x, z, 2.9, g + 0.95, g + 0.96, rgb('#4F9BD0'), 16, PLAIN, True)
        solid(x, z, 0.0, -3.1, 3.1, -3.1, 3.1, 0.1)
    elif r < 0.68:      # mesa de piquenique
        h = _H(bk, hf, x, z, ang)
        wc = rgb(rng.choice(['#8B6B4A', '#A68A64', '#7B5B3E']))
        h.box(-0.9, 0.9, -0.4, 0.4, g + 0.72, g + 0.78, wc, PLAIN)
        h.box(-0.9, 0.9, -0.85, -0.45, g + 0.42, g + 0.47, wc, PLAIN)
        h.box(-0.9, 0.9, 0.45, 0.85, g + 0.42, g + 0.47, wc, PLAIN)
        for s_ in (-0.6, 0.6):
            h.box(s_ - 0.05, s_ + 0.05, -0.8, 0.8, g, g + 0.72, shade(wc, -15), PLAIN)
        solid(x, z, ang, -1.0, 1.0, -0.9, 0.9, 0.05)
    elif r < 0.78:      # balanço de quintal
        h = _H(bk, hf, x, z, ang)
        fc = rgb('#B5502F')
        for s_ in (-1.4, 1.4):
            h.box(s_ - 0.05, s_ + 0.05, -0.7, -0.6, g, g + 2.0, fc, PLAIN)
            h.box(s_ - 0.05, s_ + 0.05, 0.6, 0.7, g, g + 2.0, fc, PLAIN)
        h.box(-1.5, 1.5, -0.05, 0.05, g + 1.95, g + 2.05, fc, PLAIN)
        for s_ in (-0.5, 0.5):
            h.box(s_ - 0.25, s_ + 0.25, -0.1, 0.1, g + 0.5, g + 0.55, rgb('#2B2B2E'), PLAIN)
        solid(x, z, ang, -1.5, 1.5, -0.8, 0.8, 0.05)


def build_all(bk, hf, solid, LOTS, TREES, seed=777):
    rng = random.Random(seed)
    N = len(LOTS)
    for idx, L in enumerate(LOTS):
        lawn(bk, hf, L, rng)
    # estilos: escolhidos com sorteio ponderado e sem repetir o mesmo da vizinha (diversidade)
    fronts = [('none', .36), ('picket', .22), ('hedge', .14), ('rail', .08), ('wall', .06), ('chain', .08), ('privacy', .0)]
    for idx, L in enumerate(LOTS):
        prev = LOTS[idx - 1].get('fstyle') if idx else None
        opts = [(s, w) for (s, w) in fronts if s != prev or s == 'none' and rng.random() < 0.4]
        tot = sum(w for _, w in opts); r = rng.random() * tot; acc = 0; fs = 'none'
        for s, w in opts:
            acc += w
            if r <= acc:
                fs = s; break
        L['fstyle'] = fs
        L['fcol'] = rng.choice(PAINT) if fs == 'picket' else rng.choice(['#9C5A44', '#B9B5AC', '#8E8A82']) if fs == 'wall' else '#3C7F49'
        encl = fs in ('picket', 'chain', 'rail') and rng.random() < 0.55       # cerca fechando o lote inteiro
        r2 = rng.random()
        L['sstyle'] = fs if encl else ('privacy' if r2 < 0.42 else 'chain' if r2 < 0.72 else 'picket' if r2 < 0.80 else 'none')
        L['scol'] = L['fcol'] if L['sstyle'] == 'picket' else rng.choice(WOODS + PAINT[:1]) if L['sstyle'] == 'privacy' else '#9AA0A6'
        L['bstyle'] = L['sstyle'] if rng.random() < 0.85 else rng.choice(['privacy', 'chain', 'none'])
        L['bcol'] = L['scol'] if L['bstyle'] == L['sstyle'] else rng.choice(WOODS)
        L['encl'] = encl
    for idx, L in enumerate(LOTS):
        w2 = L['w'] / 2; d = L['d']; sp = L['house']
        # frente
        if L['fstyle'] != 'none':
            p0 = lp(L, -w2 + 0.1, 0.35); p1 = lp(L, w2 - 0.1, 0.35)
            gaps = [(a + w2 - 0.1, b + w2 - 0.1) for (a, b) in L.get('gaps', [])]
            hg = 1.0 if L['fstyle'] == 'picket' else (1.15 if L['fstyle'] == 'hedge' else None)
            draw_run(bk, hf, solid, L['fstyle'], L['fcol'], p0, p1, gaps, hg, rng)
        # lados
        vs = 0.35 if L['encl'] else L['setb'] + sp['d'] * 0.4
        for s in (-1, 1):
            if L['sstyle'] == 'none':
                continue
            vm = (vs + d) / 2
            qx, qz = lp(L, s * (w2 + 1.7), vm)
            nb = [j for j, O in enumerate(LOTS) if j != idx and in_lot(O, qx, qz)]
            if nb and nb[0] < idx:
                continue
            p0 = lp(L, s * w2, vs); p1 = lp(L, s * w2, d)
            draw_run(bk, hf, solid, L['sstyle'], L['scol'], p0, p1, (), None, rng)
        # fundos
        if L['bstyle'] != 'none':
            qx, qz = lp(L, 0, d + 1.2)
            nb = [j for j, O in enumerate(LOTS) if j != idx and in_lot(O, qx, qz)]
            if not (nb and nb[0] < idx):
                draw_run(bk, hf, solid, L['bstyle'], L['bcol'], lp(L, -w2, d), lp(L, w2, d), (), None, rng)
        yard_extras(bk, hf, solid, L, rng, TREES)
