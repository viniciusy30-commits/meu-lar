"""Cidade 6 - orla (v2): calcadao de pedra portuguesa em ondas, ciclovia, coqueiros, postes, bancos, quiosques com mesas,
mureta com escadas para a areia, chuveiros, passarelas de madeira, quadras de volei e futebol de areia, postos de
salva-vidas, conjuntos de guarda-sol com espreguicadeiras e o pier."""
import math
import numpy as np
from shapely.geometry import Point, Polygon, box as sbox
from mesh import rgb, shade, mix, WHITE, Frame
from plan6 import *
from roads6 import Y_ASF, Y_WALK, Y_LAWN, Y_SEA

Z0 = 1688.0 + half_row('orla')          # fim da calcada da avenida
ZW = 1718.0                             # mureta
COLS = [(230, 70, 60), (40, 120, 200), (245, 200, 40), (60, 170, 120), (244, 244, 244), (240, 130, 40), (200, 80, 160), (30, 160, 170)]


def sand_y(x, z):
    t = min(max((z - ZW) / max(shore_z(x) - ZW, 1.0), 0.0), 1.0)
    return -0.35 - 0.55 * t ** 1.2


def build(P, G, L, M, pr):
    r = pr.rnd
    rx = river_x(1760)
    def in_river(x, pad=36): return abs(x - rx) < pad
    QW = RIVER_W / 2 + RIVER_WALL                                  # do eixo do rio ate a face de fora do cais
    spans = [(2.0, river_x(ZW) - QW), (river_x(ZW) + QW, W - 2.0)]   # o calcadao e a mureta encostam no cais do rio
    y = Y_WALK
    # ------------------------------------------------------------ calcadao + ciclovia + mureta
    for si, (xa, xb) in enumerate(spans):
        # piso de pedra portuguesa, recortado pela margem (fecha certinho contra o cais curvo)
        x = xa - (6.0 if si == 1 else 0.0)
        xe = xb + (6.0 if si == 0 else 0.0)
        while x < xe:
            x1 = min(x + 25.0, xe)
            g = sbox(x, Z0, x1, ZW - 0.25).intersection(P.land)
            M.free('orla'); M.m('ondas'); M.shp(g, y, WHITE)
            x = x1
        # ciclovia: termina num retorno redondo antes do rio (nada de faixa cortada no fim)
        ca, cb = (xa, xb - 16.0) if si == 0 else (xa + 16.0, xb)
        x = ca
        while x < cb:
            x1 = min(x + 25.0, cb)
            M.free('orla'); M.m('asfalto'); M.poly([(x, y + 0.03, Z0 + 0.8), (x1, y + 0.03, Z0 + 0.8), (x1, y + 0.03, Z0 + 3.6), (x, y + 0.03, Z0 + 3.6)], (255, 150, 120), (0, 1, 0))
            M.m('liso')
            for zz in (Z0 + 0.8, Z0 + 3.5): M.poly([(x, y + 0.06, zz), (x1, y + 0.06, zz), (x1, y + 0.06, zz + 0.1), (x, y + 0.06, zz + 0.1)], (250, 250, 246), (0, 1, 0))
            for k in range(int((x1 - x) / 5)):
                xd = x + k * 5 + 1; M.poly([(xd, y + 0.06, Z0 + 2.15), (xd + 2, y + 0.06, Z0 + 2.15), (xd + 2, y + 0.06, Z0 + 2.25), (xd, y + 0.06, Z0 + 2.25)], (250, 220, 80), (0, 1, 0))
            x = x1
        ex = cb if si == 0 else ca; ez = Z0 + 2.2; R = 3.4
        M.at(ex, ez, 'orla'); M.m('asfalto')
        ring = [(ex + math.cos(t) * R, ez + math.sin(t) * R) for t in np.linspace(0, 2 * math.pi, 20, endpoint=False)]
        M.poly([(px, y + 0.035, pz) for px, pz in ring], (255, 150, 120), (0, 1, 0))
        M.m('liso')
        for k in range(20):
            (p0, p1) = ring[k], ring[(k + 1) % 20]; f = (R - 0.12) / R
            M.poly([(p0[0], y + 0.065, p0[1]), (p1[0], y + 0.065, p1[1]), (ex + (p1[0] - ex) * f, y + 0.065, ez + (p1[1] - ez) * f), (ex + (p0[0] - ex) * f, y + 0.065, ez + (p0[1] - ez) * f)], (250, 250, 246), (0, 1, 0))
        M.m('folhagem'); M.cyl(ex, ez, 1.1, y, y + 0.5, (70, 120, 60), 10, True)                     # canteiro no meio do retorno
        M.free()
        # mureta com aberturas e escadas a cada ~70 m, de ponta a ponta (ate o cais do rio)
        gaps = [g for g in np.arange(xa + 35, xb - 22, 70.0)]
        cur = xa
        for g in gaps + [None]:
            end = (g - 3.0) if g is not None else xb
            x = cur
            while x < end:
                x1 = min(x + 20.0, end)
                M.at((x + x1) / 2, ZW, 'orla'); M.m('pedra'); M.prism([(x, ZW - 0.25), (x1, ZW - 0.25), (x1, ZW + 0.25), (x, ZW + 0.25)], -1.0, y + 0.5, WHITE, False)
                M.m('concreto'); M.prism([(x, ZW - 0.32), (x1, ZW - 0.32), (x1, ZW + 0.32), (x, ZW + 0.32)], y + 0.5, y + 0.6, (236, 232, 222), True)
                x = x1
            if g is not None:
                stairs(M, pr, g, y); cur = g + 3.0
        # pilar de arremate onde a mureta encontra o cais
        px = xb if si == 0 else xa
        M.at(px, ZW, 'orla'); M.m('pedra'); M.prism([(px - 0.6, ZW - 0.6), (px + 0.6, ZW - 0.6), (px + 0.6, ZW + 0.6), (px - 0.6, ZW + 0.6)], -1.0, y + 0.95, WHITE, False)
        M.m('concreto'); M.prism([(px - 0.7, ZW - 0.7), (px + 0.7, ZW - 0.7), (px + 0.7, ZW + 0.7), (px - 0.7, ZW + 0.7)], y + 0.95, y + 1.08, (236, 232, 222), True)
        M.free()
        # ------------------------------------------------------------ coqueiros, postes, bancos, lixeiras
        x = xa + 6; k = 0
        while x < xb - 4:
            if not any(abs(x - g) < 5 for g in gaps):
                pr.tree(x, ZW - 1.9, 'palmeira', r.uniform(0.95, 1.2), y)
            if k % 2 == 0: pr.tree(x + 6, Z0 + 5.2, 'palmeira', r.uniform(0.85, 1.05), y)
            if k % 3 == 0: pr.streetlight(x + 3, Z0 + 4.6, 0, -1)
            if k % 2 == 1:
                pr.bench(x + 3, ZW - 1.2, 0, 1, y)
                if k % 4 == 1: pr.bin(x + 5, ZW - 1.2)
            x += 12; k += 1
        # ------------------------------------------------------------ quiosques com mesas
        for kx in np.arange(xa + 60, xb - 40, 115.0):
            if any(abs(kx - g) < 9 for g in gaps): kx += 12
            kiosk(M, pr, kx, Z0 + 9.5, y, r)
    # ------------------------------------------------------------ areia: esportes, salva-vidas, guarda-sois, coqueiros
    for (xa, xb) in spans:
        x = xa + 30; k = 0
        while x < xb - 30:
            if abs(x - 1000) < 26: x += 30; continue                 # pier
            what = ('volei', 'sois', 'futebol', 'sois', 'salva', 'sois', 'coqueiros')[k % 7]
            if what == 'volei': volley(M, x, ZW + 22, r)
            elif what == 'futebol': soccer(M, x, ZW + 26, r)
            elif what == 'salva': lifeguard(M, x, shore_z(x) - 34, r)
            elif what == 'coqueiros':
                for _ in range(5):
                    px, pz = x + r.uniform(-9, 9), ZW + r.uniform(5, 16); pr.tree(px, pz, 'palmeira', r.uniform(0.9, 1.25), sand_y(px, pz))
            else: sunset(M, x, r)
            x += r.uniform(32, 44); k += 1
        for _ in range(int((xb - xa) / 14)):                           # guarda-sois avulsos
            x = r.uniform(xa + 10, xb - 10)
            if abs(x - 1000) < 12: continue
            umbrella(M, x, r.uniform(ZW + 8, shore_z(x) - 12), r.choice(COLS), r)
    pier(M, pr, 1000.0, y, r)


def stairs(M, pr, x, y):
    """abertura na mureta: escada de concreto ate a areia, chuveiro ao lado e passarela de madeira"""
    M.at(x, ZW, 'orla'); M.m('concreto')
    for k in range(4):
        M.box(x - 3.0, x + 3.0, -1.0, y - 0.13 * (k + 1), ZW - 0.3 + 0.45 * k, ZW + 0.15 + 0.45 * k, (226, 222, 212))
    for s in (-1, 1): M.box(x + s * 3.0 - 0.2, x + s * 3.0 + 0.2, -1.0, y + 0.75, ZW - 0.3, ZW + 1.5, (236, 232, 222))
    M.m('metal'); sx = x + 4.2                                         # chuveiro
    M.cyl(sx, ZW + 1.2, 0.05, sand_y(sx, ZW + 1.2), y + 2.1, (200, 204, 208), 5, False)
    M.box(sx - 0.05, sx + 0.05, y + 2.05, y + 2.15, ZW + 1.2, ZW + 1.7, (200, 204, 208)); M.cyl(sx, ZW + 1.7, 0.12, y + 1.95, y + 2.05, (220, 224, 228), 6)
    M.m('concreto'); M.cyl(sx, ZW + 1.5, 0.8, sand_y(sx, ZW + 1.5) - 0.2, sand_y(sx, ZW + 1.5) + 0.06, (226, 222, 212), 8)
    M.m('madeira'); z = ZW + 1.8                                       # passarela de tabuas sobre a areia
    while z < ZW + 22:
        y0 = sand_y(x, z); y1 = sand_y(x, z + 4)
        M.quad((x - 1.0, y0 + 0.07, z), (x + 1.0, y0 + 0.07, z), (x + 1.0, y1 + 0.07, z + 4), (x - 1.0, y1 + 0.07, z + 4), WHITE, (0, 1, 0)); z += 4
    M.free()


def kiosk(M, pr, x, z, y, r):
    """quiosque octogonal de madeira com balcao, cobertura de telha e mesas com guarda-sol"""
    M.at(x, z, 'orla'); col = r.choice(((250, 240, 220), (236, 250, 240), (250, 232, 236), (232, 240, 250)))
    M.m('madeira'); M.cyl(x, z, 2.6, y, y + 1.05, col, 8, True)
    M.m('liso'); M.cyl(x, z, 2.75, y + 1.05, y + 1.13, (120, 84, 56), 8, True)
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8; M.cyl(x + math.cos(a) * 2.5, z + math.sin(a) * 2.5, 0.07, y + 1.1, y + 2.6, (120, 84, 56), 4, False)
    M.m('liso'); M.cyl(x, z, 1.6, y + 1.1, y + 2.3, (70, 74, 80), 8, True)        # miolo (geladeiras)
    M.m('ceramica'); M.cyl(x, z, 4.0, y + 2.6, y + 4.0, WHITE, 8, False, 0.25)
    M.m('liso'); M.cyl(x, z, 4.05, y + 2.48, y + 2.62, r.choice(COLS), 8, False)
    ac = r.choice(COLS)
    for k in range(4):
        a = math.pi * (0.15 + 0.23 * k) + (math.pi if z > ZW else 0); tx, tz = x + math.cos(a) * 6.0, z + abs(math.sin(a)) * 4.6 + 0.5
        if tz > ZW - 1.6: tz = ZW - 1.8
        M.cyl(tx, tz, 0.5, y + 0.7, y + 0.75, (240, 240, 236), 8); M.cyl(tx, tz, 0.04, y, y + 2.2, (200, 200, 204), 4, False)
        M.cyl(tx, tz, 1.25, y + 2.0, y + 2.45, ac if k % 2 else (250, 250, 246), 8, False, 0.04)
        for j in range(3):
            b = j * 2.1 + k; M.box(tx + math.cos(b) * 0.85 - 0.2, tx + math.cos(b) * 0.85 + 0.2, y, y + 0.45, tz + math.sin(b) * 0.85 - 0.2, tz + math.sin(b) * 0.85 + 0.2, (250, 250, 248))
    M.free()


def umbrella(M, x, z, col, r, chairs=True):
    yb = sand_y(x, z)
    M.at(x, z, 'orla'); M.m('liso')
    M.cyl(x, z, 0.035, yb, yb + 2.2, (230, 230, 230), 4, False)
    M.cyl(x, z, 1.45, yb + 1.95, yb + 2.4, col, 8, False, 0.04)
    if chairs:
        for s in (-1, 1):
            cx = x + s * 0.95; cc = r.choice(((250, 250, 250), col))
            M.box(cx - 0.32, cx + 0.32, yb + 0.22, yb + 0.3, z - 0.2, z + 1.5, cc)
            M.quad((cx - 0.32, yb + 0.3, z - 0.2), (cx + 0.32, yb + 0.3, z - 0.2), (cx + 0.32, yb + 0.85, z - 0.75), (cx - 0.32, yb + 0.85, z - 0.75), cc, (0, 0.6, 1))
    M.free()


def sunset(M, x, r):
    """conjunto de aluguel: 2 fileiras de guarda-sois da mesma cor com espreguicadeiras"""
    col = r.choice(COLS); n = r.choice((3, 4, 5))
    for row in range(2):
        for k in range(n):
            ux = x + (k - (n - 1) / 2) * 4.2; uz = shore_z(ux) - 14 - row * 5.5
            umbrella(M, ux, uz, col if (k + row) % 2 == 0 or r.random() < 0.6 else (250, 250, 246), r)


def volley(M, x, z, r):
    yb = sand_y(x, z) + 0.04
    M.at(x, z, 'orla'); M.m('liso')
    for (a, b, c, d) in ((x - 8, x + 8, z - 4.5, z - 4.4), (x - 8, x + 8, z + 4.4, z + 4.5), (x - 8, x - 7.9, z - 4.5, z + 4.5), (x + 7.9, x + 8, z - 4.5, z + 4.5)):
        M.poly([(a, yb, c), (b, yb, c), (b, yb, d), (a, yb, d)], (40, 90, 200), (0, 1, 0))
    for zz in (z - 5.0, z + 5.0): M.cyl(x, zz, 0.07, yb - 0.3, yb + 2.5, (240, 200, 60), 5, False)
    M.quad((x, yb + 1.45, z - 5.0), (x, yb + 1.45, z + 5.0), (x, yb + 2.43, z + 5.0), (x, yb + 2.43, z - 5.0), (250, 250, 250), (1, 0, 0))
    M.m('liso'); M.sphere(x + 3, yb + 0.12, z + 1, 0.11, (250, 240, 120), 5, 3)
    M.free()


def soccer(M, x, z, r):
    yb = sand_y(x, z) + 0.04
    M.at(x, z, 'orla'); M.m('liso')
    for s in (-1, 1):
        gx = x + s * 13
        for zz in (z - 2.75, z + 2.75): M.cyl(gx, zz, 0.06, yb - 0.3, yb + 2.2, (250, 250, 250), 5, False)
        M.box(gx - 0.06, gx + 0.06, yb + 2.14, yb + 2.26, z - 2.75, z + 2.75, (250, 250, 250))
        M.m('cerca'); M.quad((gx + s * 1.2, yb, z - 2.75), (gx + s * 1.2, yb, z + 2.75), (gx, yb + 2.2, z + 2.75), (gx, yb + 2.2, z - 2.75), (230, 230, 236), (s, 0.5, 0)); M.m('liso')
    for (a, b, c, d) in ((x - 13, x + 13, z - 8, z - 7.9), (x - 13, x + 13, z + 7.9, z + 8), (x - 0.05, x + 0.05, z - 8, z + 8)):
        M.poly([(a, yb, c), (b, yb, c), (b, yb, d), (a, yb, d)], (220, 60, 50), (0, 1, 0))
    M.free()


def lifeguard(M, x, z, r):
    yb = sand_y(x, z)
    M.at(x, z, 'orla'); M.m('madeira')
    for (dx, dz) in ((-1.3, -1.3), (1.3, -1.3), (1.3, 1.3), (-1.3, 1.3)): M.box(x + dx - 0.1, x + dx + 0.1, yb - 0.3, yb + 2.5, z + dz - 0.1, z + dz + 0.1, WHITE)
    M.box(x - 1.9, x + 1.9, yb + 2.5, yb + 2.7, z - 1.9, z + 2.6, WHITE)
    M.m('liso'); M.box(x - 1.5, x + 1.5, yb + 2.7, yb + 4.5, z - 1.5, z + 1.2, (236, 70, 50))
    M.m('janela'); M.quad((x - 1.2, yb + 3.3, z + 1.22), (x + 1.2, yb + 3.3, z + 1.22), (x + 1.2, yb + 4.2, z + 1.22), (x - 1.2, yb + 4.2, z + 1.22), WHITE, (0, 0, 1), [(0, 1), (2, 1), (2, 0), (0, 0)])
    M.m('liso'); M.quad((x - 1.9, yb + 4.5, z - 1.8), (x + 1.9, yb + 4.5, z - 1.8), (x + 1.9, yb + 4.9, z + 2.4), (x - 1.9, yb + 4.9, z + 2.4), (250, 250, 246), (0, 1, 0))
    M.m('madeira'); M.quad((x - 0.5, yb + 2.6, z + 2.6), (x + 0.5, yb + 2.6, z + 2.6), (x + 0.5, yb + 0.05, z + 5.6), (x - 0.5, yb + 0.05, z + 5.6), WHITE, (0, 1, 0.8))
    M.m('liso'); M.cyl(x + 1.7, z + 2.4, 0.03, yb + 2.7, yb + 6.2, (220, 220, 220), 4, False)
    M.quad((x + 1.7, yb + 5.5, z + 2.4), (x + 2.6, yb + 5.5, z + 2.4), (x + 2.6, yb + 6.1, z + 2.4), (x + 1.7, yb + 6.1, z + 2.4), (236, 70, 50), (0, 0, 1))
    M.free()


def pier(M, pr, px, y, r):
    zA = ZW - 0.3; zB = shore_z(px) + 170; yd = 1.35
    M.at(px, zA + 20, 'orla'); M.m('madeira')
    # rampa do calcadao ate o tabuleiro
    M.quad((px - 3.5, y, zA - 9), (px + 3.5, y, zA - 9), (px + 3.5, yd, zA + 1), (px - 3.5, yd, zA + 1), WHITE, (0, 1, 0))
    for s in (-1, 1): M.quad((px + s * 3.5, y - 0.4, zA - 9), (px + s * 3.5, yd - 0.4, zA + 1), (px + s * 3.5, yd, zA + 1), (px + s * 3.5, y, zA - 9), (200, 170, 130), (s, 0, 0))
    z = zA + 1
    while z < zB:
        z1 = min(z + 12, zB)
        M.at(px, (z + z1) / 2, 'orla'); M.m('madeira')
        M.prism([(px - 3.5, z), (px + 3.5, z), (px + 3.5, z1), (px - 3.5, z1)], yd - 0.3, yd, WHITE, True, True)
        for zz in (z + 0.5, z + 6.5):
            hb = min(G_h(px, zz), -0.6)
            for s in (-1, 1): M.cyl(px + s * 3.0, zz, 0.2, hb - 1.5, yd - 0.3, (214, 190, 156), 6, False)
            M.box(px - 3.3, px + 3.3, yd - 0.55, yd - 0.3, zz - 0.12, zz + 0.12, (214, 190, 156))
        M.m('liso')
        for s in (-1, 1):
            M.box(px + s * 3.45 - 0.05, px + s * 3.45 + 0.05, yd + 0.95, yd + 1.05, z, z1, (246, 246, 242))
            M.box(px + s * 3.45 - 0.03, px + s * 3.45 + 0.03, yd + 0.5, yd + 0.56, z, z1, (246, 246, 242))
            for zz in np.arange(z, z1, 3.0): M.box(px + s * 3.45 - 0.05, px + s * 3.45 + 0.05, yd, yd + 1.0, zz - 0.05, zz + 0.05, (246, 246, 242))
        if int(z) % 24 < 12:
            M.m('metal'); M.cyl(px - 3.2, z + 3, 0.07, yd, yd + 4.2, (70, 74, 80), 5, False); M.m('liso'); M.sphere(px - 3.2, yd + 4.35, z + 3, 0.28, (255, 246, 210), 6, 4)
            pr.bench(px + 2.6, z + 5, -1, 0, yd)
        z = z1
    # pavilhao na ponta
    M.at(px, zB + 8, 'orla'); M.m('madeira')
    M.prism([(px - 11, zB - 2), (px + 11, zB - 2), (px + 11, zB + 18), (px - 11, zB + 18)], yd - 0.3, yd, WHITE, True, True)
    for (dx, dz) in ((-10, 0), (10, 0), (-10, 16), (10, 16), (0, 0), (0, 16)):
        hb = -4.0; M.cyl(px + dx, zB + dz, 0.24, hb, yd - 0.3, (214, 190, 156), 6, False)
    for (dx, dz) in ((-6.5, 2), (6.5, 2), (6.5, 13), (-6.5, 13)): M.box(px + dx - 0.12, px + dx + 0.12, yd, yd + 3.6, zB + dz - 0.12, zB + dz + 0.12, (246, 246, 242))
    M.m('ceramica')
    for (z0, z1, s) in ((zB + 0.5, zB + 7.5, -1), (zB + 14.5, zB + 7.5, 1)):
        M.quad((px - 8, yd + 3.5, z0), (px + 8, yd + 3.5, z0), (px + 8, yd + 5.6, z1), (px - 8, yd + 5.6, z1), WHITE, (0, 1, s * 0.4))
    M.m('liso')
    for s in (-1, 1): M.tri((px + s * 8, yd + 3.5, zB + 0.5), (px + s * 8, yd + 3.5, zB + 14.5), (px + s * 8, yd + 5.6, zB + 7.5), (246, 246, 242), (s, 0, 0))
    M.box(px - 5, px + 5, yd, yd + 1.1, zB + 5, zB + 10, (246, 240, 228))            # balcao do restaurante
    for k in range(4):
        tx, tz = px - 8 + k * 5.3, zB + 15.5
        M.cyl(tx, tz, 0.5, yd + 0.7, yd + 0.75, (240, 240, 236), 8); M.cyl(tx, tz, 0.04, yd, yd + 0.7, (200, 200, 204), 4, False)
    for s in (-1, 1):
        M.box(px + s * 10.95 - 0.05, px + s * 10.95 + 0.05, yd + 0.95, yd + 1.05, zB - 2, zB + 18, (246, 246, 242))
    M.box(px - 11, px + 11, yd + 0.95, yd + 1.05, zB + 17.9, zB + 18, (246, 246, 242))
    M.free()


def G_h(x, z):
    return sand_y(x, z) if z < shore_z(x) else -1.5 - min((z - shore_z(x)) / 120, 1) * 5.0
