"""CAIS das pontas da orla: muralha de pedra de 2,8 m com calcadao de pavimento, parapeito, balizadores, postes, bancos, palmeiras, escadas para a agua,
marina com pontoes e barcos (veleiros e lanchas), galpao do clube nautico e formacoes de rocha nas pontas.
Roda sobre as linhas de margem de margens.py (tipo 'cais')."""
import math
import numpy as np
from bake import rgb, shade, PLAIN, STONE, WOOD, METAL, PAVER, ROOF
from plan import *
import margens as M

Y_DECK = 2.63                    # nivel do cais (praca 2,61 + 0,02)
W_WALL = 0.6
DECK_W = 5.6                     # largura do calcadao do cais, da muralha ate o meio-fio
C = {'stone1': rgb('#9A958A'), 'stone2': rgb('#85807A'), 'stone3': rgb('#6F6B64'), 'cope': rgb('#D7D1C4'), 'deck1': rgb('#E9E4D8'), 'deck2': rgb('#D2CCBD'),
     'curb': rgb('#9C9486'), 'bollard': rgb('#2A2C30'), 'red': rgb('#D6402A'), 'shed': rgb('#E8E0CC'), 'shed2': rgb('#B9553B'), 'win': rgb('#6C93B5'),
     'door': rgb('#3F5D7A'), 'sail': rgb('#F7F7F2'), 'sail2': rgb('#F1D36B')}


def run_cais(m, fr, i0, i1):
    """constroi o cais ao longo do trecho (frames de 3 m; normal 'n' aponta para a terra)"""
    seg = fr[i0:i1 + 1]; B = m.B
    ok = []
    for f in seg:
        x, z = f['x'] + f['nx'] * 3.0, f['z'] + f['nz'] * 3.0
        x2, z2 = f['x'] + f['nx'] * 6.2, f['z'] + f['nz'] * 6.2
        r = (m.blocked(x, z, 0), m.blocked(x2, z2, 0), m.sample(x, z) <= -0.05 or m.sample(x2, z2) <= 0.7); m.dbg[r] = m.dbg.get(r, 0) + 1
        ok.append(not any(r))
    k = 0
    while k < len(seg):
        if not ok[k]: k += 1; continue
        j = k
        while j + 1 < len(seg) and ok[j + 1]: j += 1
        if j - k >= 6: _piece(m, seg, k, j)
        k = j + 1


def P(f, o, y): return (f['x'] + f['nx'] * o, y, f['z'] + f['nz'] * o)


def _piece(m, seg, k0, k1):
    B = m.B; g = m.g; rnd = m.rnd
    n = k1 - k0
    # paradas para escada (a cada ~84 m) e para as docas/pontoes
    stairs = set(range(k0 + 14, k1 - 6, 28))
    for k in range(k0, k1):
        a, b = seg[k], seg[k + 1]
        if k in stairs: m.stairs_at.append((a['x'], a['z'], a['nx'], a['nz']));
    def near_stair(k): return any(abs(k - s) <= 2 for s in stairs)
    for k in range(k0, k1):
        a, b = seg[k], seg[k + 1]
        # --- parede de pedra em fiadas (3 faixas de tons) do fundo ate o topo
        for (ya, yb, col) in ((-1.4, 0.15, C['stone3']), (0.15, 1.45, C['stone2']), (1.45, Y_DECK, C['stone1'] if (k // 2) % 2 == 0 else shade(C['stone1'], 8))):
            B.quad(STONE, [P(a, 0.0, ya), P(b, 0.0, ya), P(b, 0.0, yb), P(a, 0.0, yb)], (-a['nx'], 0, -a['nz']), col, None, True)
        # --- coroamento (laje clara) e calcadao
        q = [P(a, -0.12, Y_DECK + 0.03), P(b, -0.12, Y_DECK + 0.03), P(b, W_WALL, Y_DECK + 0.03), P(a, W_WALL, Y_DECK + 0.03)]
        B.quad(PAVER, q, (0, 1, 0), C['cope']); g.poly('mprom', [(p[0], p[2]) for p in q])
        # a face frontal do coroamento
        B.quad(STONE, [P(a, -0.12, Y_DECK - 0.18), P(b, -0.12, Y_DECK - 0.18), P(b, -0.12, Y_DECK + 0.03), P(a, -0.12, Y_DECK + 0.03)], (-a['nx'], 0, -a['nz']), C['cope'], None, True)
        for bi in range(2):                                                          # duas faixas de pavimento alternadas (xadrez em ondas, como a orla)
            o0 = W_WALL + (DECK_W - W_WALL) * bi / 2; o1 = W_WALL + (DECK_W - W_WALL) * (bi + 1) / 2
            col = C['deck1'] if ((k // 3) + bi) % 2 == 0 else C['deck2']
            q = [P(a, o0, Y_DECK), P(b, o0, Y_DECK), P(b, o1, Y_DECK), P(a, o1, Y_DECK)]
            B.quad(PAVER, q, (0, 1, 0), col); g.poly('mprom', [(p[0], p[2]) for p in q])
        # saia de pedra do lado da terra (onde o terreno fica abaixo do piso do cais)
        ta, tb = m.sample(*P(a, DECK_W + 0.3, 0)[::2]), m.sample(*P(b, DECK_W + 0.3, 0)[::2])
        if min(ta, tb) < Y_DECK - 0.12:
            B.quad(STONE, [P(a, DECK_W + 0.3, min(ta, Y_DECK) - 0.25), P(b, DECK_W + 0.3, min(tb, Y_DECK) - 0.25), P(b, DECK_W + 0.3, Y_DECK), P(a, DECK_W + 0.3, Y_DECK)], (a['nx'], 0, a['nz']), C['stone1'], None, True)
        q = [P(a, DECK_W, Y_DECK + 0.01), P(b, DECK_W, Y_DECK + 0.01), P(b, DECK_W + 0.3, Y_DECK + 0.01), P(a, DECK_W + 0.3, Y_DECK + 0.01)]
        B.quad(PAVER, q, (0, 1, 0), C['curb']); g.poly('mprom', [(p[0], p[2]) for p in q])
        # --- parapeito baixo (0,55 m) com colisao, exceto nas escadas
        if not near_stair(k):
            c4 = [(a['x'] + a['nx'] * 0.15, a['z'] + a['nz'] * 0.15), (b['x'] + b['nx'] * 0.15, b['z'] + b['nz'] * 0.15), (b['x'] + b['nx'] * 0.6, b['z'] + b['nz'] * 0.6), (a['x'] + a['nx'] * 0.6, a['z'] + a['nz'] * 0.6)]
            B.obox_pts(c4, Y_DECK, Y_DECK + 0.55, C['cope'], STONE, True, False)
            m.solids.append([round(min(p[0] for p in c4) - 0.25, 2), round(min(p[1] for p in c4) - 0.25, 2), round(max(p[0] for p in c4) + 0.25, 2), round(max(p[1] for p in c4) + 0.25, 2)])
    # --- escadas para a agua (6 degraus de 0,45 m ate o espelho d'agua)
    for s in stairs:
        a, b = seg[s], seg[s + 1]; W = 2.6
        tx, tz = a['tx'], a['tz']
        for st in range(6):
            yt = Y_DECK - (st + 1) * 0.46
            o0, o1 = -0.12 - st * 0.42, -0.12 - (st + 1) * 0.42
            for sg in (0,):
                p0 = (a['x'] + a['nx'] * o0 - tx * W / 2, yt, a['z'] + a['nz'] * o0 - tz * W / 2); p1 = (a['x'] + a['nx'] * o0 + tx * W / 2, yt, a['z'] + a['nz'] * o0 + tz * W / 2)
                p2 = (a['x'] + a['nx'] * o1 + tx * W / 2, yt, a['z'] + a['nz'] * o1 + tz * W / 2); p3 = (a['x'] + a['nx'] * o1 - tx * W / 2, yt, a['z'] + a['nz'] * o1 - tz * W / 2)
                B.quad(PAVER, [p0, p1, p2, p3], (0, 1, 0), C['deck2'] if st % 2 == 0 else C['deck1'])
                B.quad(STONE, [(p3[0], yt, p3[2]), (p2[0], yt, p2[2]), (p2[0], yt + 0.46, p2[2]), (p3[0], yt + 0.46, p3[2])], (-a['nx'], 0, -a['nz']), C['stone1'], None, True)
        for sg in (-1, 1):
            px, pz = a['x'] + tx * sg * (W / 2 + 0.15) + a['nx'] * 0.2, a['z'] + tz * sg * (W / 2 + 0.15) + a['nz'] * 0.2
            B.cyl(px, pz, 0.09, Y_DECK, Y_DECK + 1.0, C['bollard'], 6, METAL, True)
            B.cyl(px - a['nx'] * 1.0, pz - a['nz'] * 1.0, 0.09, Y_DECK - 1.2, Y_DECK + 0.1, C['bollard'], 6, METAL, True)
        m.items['stairs_cais'].append({'x': round(a['x'], 1), 'z': round(a['z'], 1), 'nx': round(a['nx'], 3), 'nz': round(a['nz'], 3)})
    # --- balizadores (a cada 12 m), postes (21 m), bancos (42 m), palmeiras (14 m) em canteiros
    acc = 0.0
    for k in range(k0, k1 + 1):
        f = seg[k]
        if k > k0: acc += 3.0
        if near_stair(k): continue
        if int(acc // 12) != int((acc - 3.0) // 12):
            x, z = f['x'] + f['nx'] * 1.3, f['z'] + f['nz'] * 1.3
            B.cyl(x, z, 0.17, Y_DECK, Y_DECK + 0.55, C['bollard'], 8, METAL, True); B.cyl(x, z, 0.19, Y_DECK + 0.5, Y_DECK + 0.58, C['red'], 8, PLAIN, True)
        if int(acc // 21) != int((acc - 3.0) // 21) or k == k0:
            x, z = f['x'] + f['nx'] * (DECK_W - 0.4), f['z'] + f['nz'] * (DECK_W - 0.4)
            if not m.blocked(x, z, 0): m.lamp(x, z, Y_DECK + 0.02)
        if int((acc + 10.5) // 42) != int((acc + 7.5) // 42):
            x, z = f['x'] + f['nx'] * 3.4, f['z'] + f['nz'] * 3.4
            m.bench(x, z, Y_DECK + 0.02, f['nx'], f['nz'])
        if int((acc + 7.0) // 14) != int((acc + 4.0) // 14):
            x, z = f['x'] + f['nx'] * (DECK_W + 2.2), f['z'] + f['nz'] * (DECK_W + 2.2)
            if not m.blocked(x, z, 1) and m.sample(x, z) > 1.5:
                m.o.palm_at(x, z, m.sample(x, z) + 0.28, rnd.uniform(1.0, 1.3)); m.o.items['palms'].append({'x': round(x, 2), 'z': round(z, 2), 'y': round(m.sample(x, z) + 0.3, 2), 'sp': 'palmeira', 'scale': 1.0, 'baked': True})
        m.band_pts.append((f['x'], f['z']))
    m.stats['cais_m'] = m.stats.get('cais_m', 0.0) + 3.0 * n


# ------------------------------------------------------------------------------------------------ marina
def sailboat(m, x, z, dx, dz, L, W, hull, accent):
    rx, rz = -dz, dx
    def Pt(a, b): return (x + dx * a + rx * b, z + dz * a + rz * b)
    B = m.B; y0, y1 = M.WATER_Y - 0.6, 0.36
    pts = [Pt(-L / 2, -W / 2 * 0.8), Pt(L * 0.1, -W / 2), Pt(L / 2, 0), Pt(L * 0.1, W / 2), Pt(-L / 2, W / 2 * 0.8)]
    for k in range(5):
        a, b = pts[k], pts[(k + 1) % 5]; ex, ez = b[0] - a[0], b[1] - a[1]; ln = math.hypot(ex, ez) or 1
        B.quad(PLAIN, [(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])], (ez / ln, 0, -ex / ln), hull)
    B.poly(PLAIN, [(p[0], y1, p[1]) for p in pts], (0, 1, 0), C['sail'])
    c4 = [Pt(-L * 0.2, -W * 0.28), Pt(L * 0.12, -W * 0.28), Pt(L * 0.12, W * 0.28), Pt(-L * 0.2, W * 0.28)]
    B.obox_pts(c4, y1, y1 + 0.5, accent, PLAIN, True, False)
    mx, mz = Pt(L * 0.02, 0)
    B.cyl(mx, mz, 0.05, y1, y1 + L * 1.15, rgb('#CFCFCF'), 6, METAL, True)
    a0, a1 = Pt(L * 0.02 - 0.05, 0), Pt(-L * 0.4, 0)
    top = (mx, y1 + L * 1.1, mz)
    B.tri(PLAIN, (a0[0], y1 + 0.5, a0[1]), (a1[0], y1 + 0.7, a1[1]), top, (rx, 0, rz), C['sail'], None, True)
    B.tri(PLAIN, (a0[0], y1 + 0.5, a0[1]), (a1[0], y1 + 0.7, a1[1]), top, (-rx, 0, -rz), C['sail'], None, True)
    m.items['boats'].append({'x': round(x, 1), 'z': round(z, 1), 'dx': round(dx, 3), 'dz': round(dz, 3), 'len': round(L, 1), 'vela': True})


def marina(m, a, nx, nz, n_main=3):
    """a: ponto da margem (x,z); (nx,nz): normal para a terra. Pontoes saem perpendiculares para a agua; cada pontao tem dedos e barcos nas vagas."""
    B = m.B; rnd = m.rnd
    wx, wz = -nx, -nz; rx, rz = -wz, wx
    placed = 0
    for q in range(n_main):
        off = (q - (n_main - 1) / 2) * 26.0
        x0, z0 = a[0] + rx * off + nx * 0.0, a[1] + rz * off + nz * 0.0
        L = 0.0
        while L < 34 and m.sample(x0 + wx * (L + 1), z0 + wz * (L + 1)) > -1.2: L += 1.0
        if L >= 34 or L < 6: continue
        Lm = min(L + 20.0, 30.0)
        deck = 0.38; W = 2.4
        def PP(u, v, y=0.0): return (x0 + wx * u + rx * v, y, z0 + wz * u + rz * v)
        # passarela de acesso do cais (rampa de 0 a Lm) + pontao principal
        n_seg = int(Lm / 1.2) + 1
        for s in range(n_seg):
            u0, u1 = s * 1.2, (s + 1) * 1.2
            c4 = [(PP(u0, -W / 2)[0], PP(u0, -W / 2)[2]), (PP(u1, -W / 2)[0], PP(u1, -W / 2)[2]), (PP(u1, W / 2)[0], PP(u1, W / 2)[2]), (PP(u0, W / 2)[0], PP(u0, W / 2)[2])]
            B.obox_pts(c4, deck - 0.2, deck, rgb('#8B6B47') if s % 2 == 0 else rgb('#977650'), WOOD, True, False, 0.5)
        for u in np.arange(1.0, Lm, 4.0):
            for sg in (-1, 1):
                px, _, pz = PP(u, sg * (W / 2 - 0.1))
                B.cyl(px, pz, 0.12, -2.8, deck + 0.7, rgb('#6E5236'), 6, WOOD, True)
        m.items['docks'].append({'x': round(x0, 2), 'z': round(z0, 2), 'dx': round(wx, 3), 'dz': round(wz, 3), 'len': round(Lm, 1), 'w': W, 'deck': deck})
        # dedos (1,3 m x 9 m) dos dois lados, a cada 7 m, com um barco entre cada par
        slots = [u for u in np.arange(6.0, Lm - 3.0, 8.0)]
        for u in slots:
            for sg in (-1, 1):
                fx0, fz0 = PP(u, sg * W / 2)[0], PP(u, sg * W / 2)[2]
                fl = 8.0
                if m.sample(fx0 + rx * sg * fl, fz0 + rz * sg * fl) > -0.6: continue
                n2 = int(fl / 1.2)
                for s in range(n2):
                    u0, u1 = s * 1.2, (s + 1) * 1.2
                    c4 = [(fx0 + rx * sg * u0 - wx * 0.6, fz0 + rz * sg * u0 - wz * 0.6), (fx0 + rx * sg * u1 - wx * 0.6, fz0 + rz * sg * u1 - wz * 0.6), (fx0 + rx * sg * u1 + wx * 0.6, fz0 + rz * sg * u1 + wz * 0.6), (fx0 + rx * sg * u0 + wx * 0.6, fz0 + rz * sg * u0 + wz * 0.6)]
                    B.obox_pts(c4, deck - 0.2, deck, rgb('#8B6B47'), WOOD, True, False, 0.5)
                m.items['docks'].append({'x': round(fx0 - wx * 0.6, 2), 'z': round(fz0 - wz * 0.6, 2), 'dx': round(rx * sg, 3), 'dz': round(rz * sg, 3), 'len': round(fl, 1), 'w': 1.2, 'deck': deck})
        # barcos nas vagas: entre os dedos, paralelos ao pontao (proa para o mar)
        for i, u in enumerate(slots):
            for sg in (-1, 1):
                bl = rnd.uniform(5.5, 9.5); bw = bl * 0.32
                bx, bz = PP(u + 4.0, sg * (W / 2 + 1.5 + bw / 2))[0], PP(u + 4.0, sg * (W / 2 + 1.5 + bw / 2))[2]
                if not all(m.sample(bx + wx * q_, bz + wz * q_) < -0.4 for q_ in (-bl / 2, 0.0, bl / 2)): continue
                hull, cab = rnd.choice(M.BOAT)
                if rnd.random() < 0.45: sailboat(m, bx, bz, wx, wz, bl, bw, hull, cab)
                else: m.boat(bx, bz, wx, wz, bl, bw, hull, cab)
                placed += 1
    return placed


def shed(m, a, nx, nz):
    """galpao do clube nautico (22 x 9 m, telhado de duas aguas) 14 m para dentro do cais, com portoes, janelas e placa"""
    B = m.B
    cx, cz = a[0] + nx * 17.0, a[1] + nz * 17.0
    tx, tz = -nz, nx
    ok = all((not m.blocked(cx + tx * u + nx * v, cz + tz * u + nz * v, 1)) and m.sample(cx + tx * u + nx * v, cz + tz * u + nz * v) > 1.8 for u in (-13, 0, 13) for v in (-6, 0, 6))
    if not ok: return False
    y = m.sample(cx, cz) + 0.05; hl, hw, hh = 11.0, 4.6, 4.6
    def Q(u, v, yy): return (cx + tx * u + nx * v, yy, cz + tz * u + nz * v)
    B.obox_pts([(Q(-hl, -hw, 0)[0], Q(-hl, -hw, 0)[2]), (Q(hl, -hw, 0)[0], Q(hl, -hw, 0)[2]), (Q(hl, hw, 0)[0], Q(hl, hw, 0)[2]), (Q(-hl, hw, 0)[0], Q(-hl, hw, 0)[2])], y, y + hh, C['shed'], PLAIN, False, False)
    ridge = hh + 2.4
    for sg in (-1, 1):                                                           # telhado de duas aguas
        B.quad(ROOF, [Q(-hl - 0.5, sg * (hw + 0.6), y + hh - 0.2), Q(hl + 0.5, sg * (hw + 0.6), y + hh - 0.2), Q(hl + 0.5, 0, y + ridge), Q(-hl - 0.5, 0, y + ridge)], (nx * sg * 0.7, 0.7, nz * sg * 0.7), C['shed2'], None, True)
        B.quad(ROOF, [Q(-hl - 0.5, 0, y + ridge), Q(hl + 0.5, 0, y + ridge), Q(hl + 0.5, sg * (hw + 0.6), y + hh - 0.2), Q(-hl - 0.5, sg * (hw + 0.6), y + hh - 0.2)], (-nx * sg * 0.7, -0.7, -nz * sg * 0.7), shade(C['shed2'], -30), None, True)
    for sg in (-1, 1):                                                           # empenas triangulares
        B.tri(PLAIN, Q(sg * hl, -hw, y + hh), Q(sg * hl, hw, y + hh), Q(sg * hl, 0, y + ridge - 0.2), (tx * sg, 0, tz * sg), C['shed'], None, True)
    for q in range(4):                                                           # portoes grandes (para a agua) e janelas
        u = -8.0 + q * 5.4
        B.quad(PLAIN, [Q(u - 1.7, -hw - 0.02, y + 0.0), Q(u + 1.7, -hw - 0.02, y + 0.0), Q(u + 1.7, -hw - 0.02, y + 3.4), Q(u - 1.7, -hw - 0.02, y + 3.4)], (-nx, 0, -nz), C['door'], None, True)
        B.quad(PLAIN, [Q(u - 1.2, hw + 0.02, y + 1.8), Q(u + 1.2, hw + 0.02, y + 1.8), Q(u + 1.2, hw + 0.02, y + 3.4), Q(u - 1.2, hw + 0.02, y + 3.4)], (nx, 0, nz), C['win'], None, True)
    sx, sz = Q(0, -hw - 0.3, 0)[0], Q(0, -hw - 0.3, 0)[2]
    B.box(sx, sz, 5.0, 0.15, y + 3.55, y + 4.35, C['red'], PLAIN, True, False)                    # placa "CLUBE NAUTICO" (so a cor)
    c = [(Q(-hl, -hw, 0)[0], Q(-hl, -hw, 0)[2]), (Q(hl, -hw, 0)[0], Q(hl, -hw, 0)[2]), (Q(hl, hw, 0)[0], Q(hl, hw, 0)[2]), (Q(-hl, hw, 0)[0], Q(-hl, hw, 0)[2])]
    m.solids.append([round(min(p[0] for p in c) - 0.3, 2), round(min(p[1] for p in c) - 0.3, 2), round(max(p[0] for p in c) + 0.3, 2), round(max(p[1] for p in c) + 0.3, 2)])
    m.items['galpoes'].append({'x': round(cx, 1), 'z': round(cz, 1)})
    return True


# ------------------------------------------------------------------------------------------------ rochas grandes
def outcrop(m, x, z, n=12, rmax=3.4):
    """formacao de rocha: n blocos grandes empilhados (blocos de 1,2 a rmax, os maiores no centro)"""
    rnd = m.rnd
    for i in range(n):
        ang = rnd.uniform(0, 6.283); d = abs(rnd.gauss(0, 3.0)); px, pz = x + math.cos(ang) * d, z + math.sin(ang) * d
        r = max(1.1, rmax * (1.0 - d / 9.0)) * rnd.uniform(0.7, 1.15)
        if m.blocked(px, pz, 0): continue
        y = max(m.sample(px, pz), M.WATER_Y - 0.4) + (0.4 if d < 2 else 0.0)
        m.rock(px, y, pz, r, rnd.choice((M.COLM['rock1'], M.COLM['rock2'], M.COLM['rock3'], M.COLM['rock4'], M.COLM['rockd'])), 0.9)


# ------------------------------------------------------------------------------------------------ forte do farol
def _ring_wall(B, cx, cz, R, y0, y1, n, col, col2, nx_skip=None):
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n; am = (a0 + a1) / 2
        p0 = (cx + math.cos(a0) * R, cz + math.sin(a0) * R); p1 = (cx + math.cos(a1) * R, cz + math.sin(a1) * R)
        h = (y1 - y0)
        for (ya, yb, c) in ((y0, y0 + h * 0.5, col2), (y0 + h * 0.5, y1, col)):
            B.quad(STONE, [(p0[0], ya, p0[1]), (p1[0], ya, p1[1]), (p1[0], yb, p1[1]), (p0[0], yb, p0[1])], (math.cos(am), 0, math.sin(am)), c if (k % 2 == 0) else shade(c, 7), None, True)


def _annulus(B, g, cx, cz, r0, r1, y, n, cols):
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        q = [(cx + math.cos(a0) * r0, y, cz + math.sin(a0) * r0), (cx + math.cos(a0) * r1, y, cz + math.sin(a0) * r1), (cx + math.cos(a1) * r1, y, cz + math.sin(a1) * r1), (cx + math.cos(a1) * r0, y, cz + math.sin(a1) * r0)]
        B.quad(PAVER, q, (0, 1, 0), cols[k % len(cols)])
        g.poly('mprom', [(p[0], p[2]) for p in q])


def _stairs_radial(m, cx, cz, ang, R_up, y_low, y_up, W=3.2, rise=0.21, run=0.32):
    B = m.B; n = max(2, int(round((y_up - y_low) / rise))); rise = (y_up - y_low) / n
    ca, sa = math.cos(ang), math.sin(ang); ta, tb = -sa, ca
    for i in range(n):
        ro = R_up + (n - i) * run; ri = ro - run; y = y_low + (i + 1) * rise
        P4 = [(cx + ca * ri - ta * W / 2, y, cz + sa * ri - tb * W / 2), (cx + ca * ro - ta * W / 2, y, cz + sa * ro - tb * W / 2), (cx + ca * ro + ta * W / 2, y, cz + sa * ro + tb * W / 2), (cx + ca * ri + ta * W / 2, y, cz + sa * ri + tb * W / 2)]
        B.quad(PAVER, P4, (0, 1, 0), C['deck1'] if i % 2 == 0 else C['deck2']); m.g.poly('mprom', [(p[0], p[2]) for p in P4])
        B.quad(STONE, [(P4[1][0], y - rise, P4[1][2]), (P4[2][0], y - rise, P4[2][2]), (P4[2][0], y, P4[2][2]), (P4[1][0], y, P4[1][2])], (ca, 0, sa), C['stone1'], None, True)
    for sg in (-1, 1):                                                           # muretas laterais da escada (acompanham a altura)
        for i in range(n):
            ro = R_up + (n - i) * run; ri = ro - run; y = y_low + (i + 1) * rise
            o = sg * (W / 2 + 0.17)
            c4 = [(cx + ca * ri + ta * o - ta * 0.17, cz + sa * ri + tb * o - tb * 0.17), (cx + ca * ro + ta * o - ta * 0.17, cz + sa * ro + tb * o - tb * 0.17), (cx + ca * ro + ta * o + ta * 0.17, cz + sa * ro + tb * o + tb * 0.17), (cx + ca * ri + ta * o + ta * 0.17, cz + sa * ri + tb * o + tb * 0.17)]
            B.obox_pts(c4, y_low - 0.3, y + 0.7, C['cope'], STONE, True, False)


def lighthouse2(m, x, z, y0, scheme):
    """farol alto: base de pedra, torre afunilada em 6 faixas, porta e frestas, galeria com guarda-corpo, lanterna de vidro com 8 paineis, telhado e para-raios"""
    B = m.B; col = M.COLM[scheme]; white = M.COLM['white']; iron = M.COLM['iron']
    B.cyl(x, z, 4.0, y0, y0 + 1.6, C['stone2'], 16, STONE, True, 3.6)
    B.cyl(x, z, 3.7, y0 + 1.6, y0 + 1.9, C['cope'], 16, STONE, True)
    h = y0 + 1.9; r = 3.1
    for i in range(6):
        r2 = r - 0.2; c = white if i % 2 == 0 else col
        B.cyl(x, z, r, h, h + 3.6, c, 16, PLAIN, False, r2)
        for q in range(8):                                                            # frestas de luz em espiral
            a = 2 * math.pi * q / 8 + i * 0.9
            ra = (r + r2) / 2 + 0.02
            B.quad(PLAIN, [(x + math.cos(a - 0.04) * ra, h + 1.2, z + math.sin(a - 0.04) * ra), (x + math.cos(a + 0.04) * ra, h + 1.2, z + math.sin(a + 0.04) * ra), (x + math.cos(a + 0.04) * ra, h + 2.1, z + math.sin(a + 0.04) * ra), (x + math.cos(a - 0.04) * ra, h + 2.1, z + math.sin(a - 0.04) * ra)], (math.cos(a), 0, math.sin(a)), C['door'], None, True) if (q + i) % 3 == 0 else None
        h += 3.6; r = r2
    B.cyl(x, z, r + 1.15, h, h + 0.3, iron, 16, METAL, True)
    for q in range(20):
        a = 2 * math.pi * q / 20
        B.box(x + math.cos(a) * (r + 1.1), z + math.sin(a) * (r + 1.1), 0.07, 0.07, h + 0.3, h + 1.3, iron, METAL, True, False)
    B.cyl(x, z, r + 1.1, h + 1.22, h + 1.32, iron, 16, METAL, True)
    B.cyl(x, z, r - 0.1, h + 0.3, h + 2.7, M.COLM['glass'], 8, PLAIN, False)
    for q in range(8):
        a = 2 * math.pi * q / 8 + math.pi / 8
        B.box(x + math.cos(a) * (r - 0.05), z + math.sin(a) * (r - 0.05), 0.14, 0.14, h + 0.3, h + 2.75, iron, METAL, True, False)
    B.cyl(x, z, r - 0.3, h + 0.5, h + 1.6, M.COLM['lantern'], 8, PLAIN, True)
    B.cyl(x, z, r + 0.5, h + 2.7, h + 4.3, col, 16, PLAIN, False, 0.12)
    B.cyl(x, z, 0.12, h + 4.3, h + 6.0, iron, 6, METAL, True)
    # porta
    B.quad(PLAIN, [(x + 3.02, y0 + 1.9, z - 0.7), (x + 3.02, y0 + 1.9, z + 0.7), (x + 3.02, y0 + 4.1, z + 0.7), (x + 3.02, y0 + 4.1, z - 0.7)], (1, 0, 0), C['door'], None, True)
    m.items['lighthouses'].append({'x': round(x, 1), 'z': round(z, 1), 'y': round(y0, 2), 'h': round(h + 6.0 - y0, 1)})


def forte(m, hx, hz, dx, dz, yd, scheme):
    """Forte do Farol: tres patamares de pedra (raios 17, 10,5 e 6,2) em degraus, merlons, canhoes, casa do faroleiro e o farol alto no topo; entra pelo molhe"""
    B = m.B; g = m.g; rnd = m.rnd
    R1, R2, R3 = 17.0, 10.5, 6.2
    y1, y2, y3 = yd + 1.7, yd + 5.7, yd + 9.5
    cx, cz = hx + dx * (R1 - 1.0), hz + dz * (R1 - 1.0)
    bot = min(m.sample(cx, cz), -2.5) - 0.6
    ang_in = math.atan2(-dz, -dx)
    # paredes (fiadas) e pisos
    _ring_wall(B, cx, cz, R1, bot, y1, 40, C['stone1'], C['stone3'])
    _ring_wall(B, cx, cz, R2, y1, y2, 32, C['stone1'], C['stone2'])
    _ring_wall(B, cx, cz, R3, y2, y3, 24, C['stone1'], C['stone2'])
    _annulus(B, g, cx, cz, R2, R1, y1, 40, [C['deck1'], C['deck2']])
    _annulus(B, g, cx, cz, R3, R2, y2, 32, [C['deck2'], C['deck1']])
    for k in range(24):
        a0, a1 = 2 * math.pi * k / 24, 2 * math.pi * (k + 1) / 24
        B.tri(PAVER, (cx, y3, cz), (cx + math.cos(a1) * R3, y3, cz + math.sin(a1) * R3), (cx + math.cos(a0) * R3, y3, cz + math.sin(a0) * R3), (0, 1, 0), C['deck1'] if k % 2 == 0 else C['deck2'])
    g.poly('mprom', [(cx + math.cos(2 * math.pi * k / 24) * R3, cz + math.sin(2 * math.pi * k / 24) * R3) for k in range(24)])
    A1, A2, A3 = ang_in + math.pi / 2, ang_in - math.pi / 2, ang_in               # degraus 1->2, 2->3 e a entrada (molhe -> patamar 1)
    def near(a, aa, w): return abs((a - aa + math.pi) % (2 * math.pi) - math.pi) < w
    # coroamento + merlons (com vaos nas escadas/entrada); colisao por trecho
    for (R, y, n, aa_list) in ((R1, y1, 40, (A1, A3)), (R2, y2, 32, (A2,))):
        for k in range(n):
            a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n; am = (a0 + a1) / 2
            if any(near(am, aa, math.radians(14)) for aa in aa_list): continue
            q = [(cx + math.cos(a0) * (R + 0.3), cz + math.sin(a0) * (R + 0.3)), (cx + math.cos(a1) * (R + 0.3), cz + math.sin(a1) * (R + 0.3)), (cx + math.cos(a1) * (R - 0.45), cz + math.sin(a1) * (R - 0.45)), (cx + math.cos(a0) * (R - 0.45), cz + math.sin(a0) * (R - 0.45))]
            B.obox_pts(q, y - 0.02, y + 0.45, C['cope'], STONE, True, False)
            if k % 2 == 0:
                B.obox_pts([(cx + math.cos(a0) * (R + 0.25), cz + math.sin(a0) * (R + 0.25)), (cx + math.cos(am) * (R + 0.25), cz + math.sin(am) * (R + 0.25)), (cx + math.cos(am) * (R - 0.4), cz + math.sin(am) * (R - 0.4)), (cx + math.cos(a0) * (R - 0.4), cz + math.sin(a0) * (R - 0.4))], y + 0.45, y + 1.15, C['stone1'], STONE, True, False)
            xs = [p[0] for p in q]; zs = [p[1] for p in q]
            m.solids.append([round(min(xs) - 0.2, 2), round(min(zs) - 0.2, 2), round(max(xs) + 0.2, 2), round(max(zs) + 0.2, 2)])
    # escadas
    _stairs_radial(m, cx, cz, A1, R2, y1, y2, 3.4)
    _stairs_radial(m, cx, cz, A2, R3, y2, y3, 3.0)
    _stairs_radial(m, cx, cz, A3, R1, yd, y1, 4.0, 0.2, 0.34)                      # entrada: do molhe para o patamar 1
    # casa do faroleiro (lado oposto a entrada) + canhoes + mastro
    ah = ang_in + math.pi + 0.35; hxx, hzz = cx + math.cos(ah) * (R1 - 5.3), cz + math.sin(ah) * (R1 - 5.3)
    ca, sa = math.cos(ah + math.pi / 2), math.sin(ah + math.pi / 2)
    def Q(u, v, y): return (hxx + ca * u - sa * v, y, hzz + sa * u + ca * v)
    hl, hw, hh = 4.2, 2.5, 3.0
    B.obox_pts([(Q(-hl, -hw, 0)[0], Q(-hl, -hw, 0)[2]), (Q(hl, -hw, 0)[0], Q(hl, -hw, 0)[2]), (Q(hl, hw, 0)[0], Q(hl, hw, 0)[2]), (Q(-hl, hw, 0)[0], Q(-hl, hw, 0)[2])], y1, y1 + hh, C['shed'], PLAIN, False, False)
    for sg in (-1, 1):
        B.quad(ROOF, [Q(-hl - 0.3, sg * (hw + 0.4), y1 + hh - 0.1), Q(hl + 0.3, sg * (hw + 0.4), y1 + hh - 0.1), Q(hl + 0.3, 0, y1 + hh + 1.7), Q(-hl - 0.3, 0, y1 + hh + 1.7)], (-sa * sg * 0.7, 0.7, ca * sg * 0.7), C['shed2'], None, True)
        B.quad(ROOF, [Q(-hl - 0.3, 0, y1 + hh + 1.7), Q(hl + 0.3, 0, y1 + hh + 1.7), Q(hl + 0.3, sg * (hw + 0.4), y1 + hh - 0.1), Q(-hl - 0.3, sg * (hw + 0.4), y1 + hh - 0.1)], (sa * sg * 0.7, -0.7, -ca * sg * 0.7), shade(C['shed2'], -30), None, True)
        B.tri(PLAIN, Q(sg * hl, -hw, y1 + hh), Q(sg * hl, hw, y1 + hh), Q(sg * hl, 0, y1 + hh + 1.6), (ca * sg, 0, sa * sg), C['shed'], None, True)
    for u in (-2.4, 0.0, 2.4):
        B.quad(PLAIN, [Q(u - 0.5, hw + 0.02, y1 + 1.2), Q(u + 0.5, hw + 0.02, y1 + 1.2), Q(u + 0.5, hw + 0.02, y1 + 2.4), Q(u - 0.5, hw + 0.02, y1 + 2.4)], (-sa, 0, ca), C['win'], None, True)
    B.quad(PLAIN, [Q(-0.6, -hw - 0.02, y1), Q(0.6, -hw - 0.02, y1), Q(0.6, -hw - 0.02, y1 + 2.2), Q(-0.6, -hw - 0.02, y1 + 2.2)], (sa, 0, -ca), C['door'], None, True)
    cc = [(Q(-hl, -hw, 0)[0], Q(-hl, -hw, 0)[2]), (Q(hl, -hw, 0)[0], Q(hl, -hw, 0)[2]), (Q(hl, hw, 0)[0], Q(hl, hw, 0)[2]), (Q(-hl, hw, 0)[0], Q(-hl, hw, 0)[2])]
    m.solids.append([round(min(p[0] for p in cc) - 0.3, 2), round(min(p[1] for p in cc) - 0.3, 2), round(max(p[0] for p in cc) + 0.3, 2), round(max(p[1] for p in cc) + 0.3, 2)])
    for dda in (math.radians(55), -math.radians(55), math.radians(125), -math.radians(125)):                  # canhoes apontados para fora
        a = ang_in + dda
        if near(a, A1, math.radians(20)): continue
        px, pz = cx + math.cos(a) * (R1 - 1.9), cz + math.sin(a) * (R1 - 1.9)
        c4 = [(px - math.sin(a) * 0.3, pz + math.cos(a) * 0.3), (px + math.sin(a) * 0.3, pz - math.cos(a) * 0.3), (px + math.sin(a) * 0.3 + math.cos(a) * 2.0, pz - math.cos(a) * 0.3 + math.sin(a) * 2.0), (px - math.sin(a) * 0.3 + math.cos(a) * 2.0, pz + math.cos(a) * 0.3 + math.sin(a) * 2.0)]
        B.obox_pts(c4, y1 + 0.35, y1 + 0.85, C['bollard'], METAL, True, False)
        B.box(px, pz, 0.9, 0.9, y1, y1 + 0.35, C['stone3'], STONE, True, False)
    B.cyl(cx + math.cos(ang_in + math.pi * 0.75) * (R2 - 1.6), cz + math.sin(ang_in + math.pi * 0.75) * (R2 - 1.6), 0.07, y2, y2 + 8.0, C['cope'], 8, METAL, True)
    # 4 postes de luz no patamar 1
    for dda in (math.radians(25), -math.radians(25), math.radians(155), -math.radians(155)):
        a = ang_in + dda; px, pz = cx + math.cos(a) * (R1 - 1.2), cz + math.sin(a) * (R1 - 1.2)
        if near(a, A1, math.radians(18)): continue
        m.lamp(px, pz, y1)
    lighthouse2(m, cx, cz, y3, scheme)
    # rochas ao redor do pe do forte (na linha d'agua)
    for k in range(34):
        a = 2 * math.pi * k / 34 + rnd.uniform(-0.05, 0.05); rr = R1 + rnd.uniform(0.4, 2.8)
        if near(a, ang_in, math.radians(18)): continue
        m.rock(cx + math.cos(a) * rr, M.WATER_Y + rnd.uniform(-0.1, 0.3), cz + math.sin(a) * rr, rnd.uniform(1.0, 2.0), rnd.choice((M.COLM['rock1'], M.COLM['rock2'], M.COLM['rock3'], M.COLM['rock4'])), 0.8)
    m.items.setdefault('fortes', []).append({'x': round(cx, 1), 'z': round(cz, 1)})
