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
PIER_X = 520.0                          # pier de diversoes (praia oeste, longe da foz)
PIER_A, PIER_B = PIER_X - 80.0, PIER_X + 62.0   # faixa da praia ocupada pela plataforma
COLS = [(230, 70, 60), (40, 120, 200), (245, 200, 40), (60, 170, 120), (244, 244, 244), (240, 130, 40), (200, 80, 160), (30, 160, 170)]


def sand_y(x, z):
    t = min(max((z - ZW) / max(shore_z(x) - ZW, 1.0), 0.0), 1.0)
    return -0.35 - 0.55 * t ** 1.2


def build(P, G, L, M, pr):
    r = pr.rnd
    rx = river_x(1760)
    QW = RIVER_W / 2 + RIVER_WALL                                  # do eixo do rio ate a face de fora do cais
    spans = [(2.0, river_x(ZW) - QW), (river_x(ZW) + QW, W - 2.0)]   # o calcadao e a mureta encostam no cais do rio
    y = Y_WALK
    pr.luzes = getattr(pr, 'luzes', [])
    for si, (xa, xb) in enumerate(spans):
        # ------------------------------------------------------------ calcadao de pedra portuguesa
        x = xa - (6.0 if si == 1 else 0.0)
        xe = xb + (6.0 if si == 0 else 0.0)
        while x < xe:
            x1 = min(x + 25.0, xe)
            g = sbox(x, Z0, x1, ZW - 0.25).intersection(P.land)
            M.free('orla'); M.m('ondas'); M.shp(g, y, WHITE)
            x = x1
        # ------------------------------------------------------------ ciclovia continua: na ponta do rio ela sobe na ponte da ciclovia
        rq = river_x(Z0 + 2.2) - QW if si == 0 else river_x(Z0 + 2.2) + QW
        ca, cb = (xa, rq) if si == 0 else (rq, xb)
        x = ca
        while x < cb:
            x1 = min(x + 25.0, cb)
            M.free('orla'); M.m('asfalto'); M.poly([(x, y + 0.03, Z0 + 0.8), (x1, y + 0.03, Z0 + 0.8), (x1, y + 0.03, Z0 + 3.6), (x, y + 0.03, Z0 + 3.6)], (255, 150, 120), (0, 1, 0))
            M.m('liso')
            for zz in (Z0 + 0.8, Z0 + 3.5): M.poly([(x, y + 0.06, zz), (x1, y + 0.06, zz), (x1, y + 0.06, zz + 0.1), (x, y + 0.06, zz + 0.1)], (250, 250, 246), (0, 1, 0))
            for k in range(int((x1 - x) / 5)):
                xd = x + k * 5 + 1; M.poly([(xd, y + 0.06, Z0 + 2.15), (xd + 2, y + 0.06, Z0 + 2.15), (xd + 2, y + 0.06, Z0 + 2.25), (xd, y + 0.06, Z0 + 2.25)], (250, 220, 80), (0, 1, 0))
            x = x1
        # bicicleta pintada no chao a cada ~60 m
        for bx in np.arange(ca + 20, cb - 10, 60.0): bike_icon(M, bx, Z0 + 2.2, y + 0.07)
        # ------------------------------------------------------------ mureta com aberturas e escadas a cada ~70 m
        gaps = [g for g in np.arange(xa + 35, xb - 22, 70.0) if abs(g - PIER_X) > 16]
        cur = xa
        for g in gaps + [None]:
            end = (g - 3.0) if g is not None else xb
            x = cur
            while x < end:
                x1 = min(x + 20.0, end)
                if x < PIER_X + 10.2 and x1 > PIER_X - 10.2:                 # abertura da entrada do pier
                    if x < PIER_X - 10.2: x1 = PIER_X - 10.2
                    else: x = PIER_X + 10.2; continue
                M.at((x + x1) / 2, ZW, 'orla'); M.m('pedra'); M.prism([(x, ZW - 0.25), (x1, ZW - 0.25), (x1, ZW + 0.25), (x, ZW + 0.25)], -1.0, y + 0.5, WHITE, False)
                M.m('concreto'); M.prism([(x, ZW - 0.32), (x1, ZW - 0.32), (x1, ZW + 0.32), (x, ZW + 0.32)], y + 0.5, y + 0.6, (236, 232, 222), True)
                x = x1
            if g is not None:
                stairs(M, pr, g, y); cur = g + 3.0
        px = xb if si == 0 else xa
        M.at(px, ZW, 'orla'); M.m('pedra'); M.prism([(px - 0.6, ZW - 0.6), (px + 0.6, ZW - 0.6), (px + 0.6, ZW + 0.6), (px - 0.6, ZW + 0.6)], -1.0, y + 0.95, WHITE, False)
        M.m('concreto'); M.prism([(px - 0.7, ZW - 0.7), (px + 0.7, ZW - 0.7), (px + 0.7, ZW + 0.7), (px - 0.7, ZW + 0.7)], y + 0.95, y + 1.08, (236, 232, 222), True)
        M.free()
        # ------------------------------------------------------------ calcadao: postes, bancos para o mar, lixeiras, canteiros, bicicletarios,
        # carrinhos de coco, bebedouros, totens; quiosques de dois tipos (nada de coqueiro no meio da calcada)
        kx_list = [kx + (12 if any(abs(kx - g) < 9 for g in gaps) else 0) for kx in np.arange(xa + 60, xb - 40, 115.0)]
        kx_list = [kx for kx in kx_list if abs(kx - PIER_X) > 26]
        busy = [(kx - 11, kx + 11) for kx in kx_list] + [(PIER_X - 13.0, PIER_X + 13.0)]      # entrada do pier
        free_x = lambda xx, pad=0: not any(a_ - pad < xx < b_ + pad for (a_, b_) in busy) and not any(abs(xx - g) < 4.5 + pad for g in gaps)
        x = xa + 6; k = 0
        while x < xb - 4:
            if k % 3 == 0 and free_x(x + 3): pr.streetlight(x + 3, Z0 + 4.6, 0, -1)
            if k % 2 == 1 and free_x(x + 3): pr.bench(x + 3, ZW - 1.2, 0, 1, y)
            if k % 4 == 1 and free_x(x + 5.5): pr.bin(x + 5.5, ZW - 1.2)
            x += 12; k += 1
        x = xa + 30; k = 0
        while x < xb - 20:
            if free_x(x, 6):
                what = ('canteiro', 'bici', 'canteiro', 'coco', 'canteiro', 'bebedouro', 'canteiro', 'totem')[k % 8]
                if what == 'canteiro': planter_orla(M, pr, x, Z0 + 7.4, y, r)
                elif what == 'bici': bike_rack(M, x, Z0 + 6.2, y)
                elif what == 'coco': coconut_cart(M, x, Z0 + 7.0, y, r)
                elif what == 'bebedouro': drinking_fountain(M, x, Z0 + 6.4, y)
                else: totem(M, x, Z0 + 6.4, y, r)
                k += 1
            x += 24
        for j, kx in enumerate(kx_list):
            if j % 2 == 0: kiosk(M, pr, kx, Z0 + 9.5, y, r)
            else: kiosk_glass(M, pr, kx, Z0 + 9.5, y, r)
    # ------------------------------------------------------------ areia
    for si, (xa, xb) in enumerate(spans):
        # coqueiros na areia, em grupos de 2 a 5 com alturas bem diferentes, logo depois da mureta (sombra para quem chega)
        x = xa + r.uniform(8, 16)
        while x < xb - 8:
            if not (PIER_A < x < PIER_B) and not any(abs(x - g) < 5 for g in np.arange(xa + 35, xb - 22, 70.0)):
                for _ in range(r.randint(2, 5)):
                    px, pz = x + r.uniform(-4.5, 4.5), ZW + r.uniform(2.5, 9.0)
                    pr.tree(px, pz, 'palmeira', r.choice((0.85, 1.0, 1.15, 1.3, 1.5, 1.75)) * r.uniform(0.95, 1.05), sand_y(px, pz) - 0.05)
            x += r.uniform(14, 26)
        # faixas de uso: esportes e postos perto da mureta, barracas no meio, brincadeira na areia molhada
        x = xa + 30; k = 0
        while x < xb - 30:
            if PIER_A - 15 < x < PIER_B + 15: x += 30; continue        # pier
            what = ('volei', 'barraca', 'futebol', 'barraca', 'salva', 'barraca', 'tenis', 'barraca', 'aluguel', 'barraca')[k % 10]
            if what == 'volei': volley(M, x, ZW + 22, r)
            elif what == 'futebol': soccer(M, x, ZW + 26, r)
            elif what == 'tenis': beach_tennis(M, x, ZW + 22, r)
            elif what == 'salva': lifeguard(M, x, shore_z(x) - 34, r); flags(M, x + 6, shore_z(x) - 30, r)
            elif what == 'aluguel': rental(M, pr, x, r)
            else: sunset(M, x, r)
            x += r.uniform(34, 46); k += 1
        # gente "de passagem": guarda-sois avulsos com canga, cooler e bolsa; castelos e baldes na areia molhada; pranchas
        for _ in range(int((xb - xa) / 11)):
            x = r.uniform(xa + 10, xb - 10)
            if PIER_A < x < PIER_B: continue
            z = r.uniform(ZW + 30, shore_z(x) - 10)
            family(M, x, z, r)
        for _ in range(int((xb - xa) / 45)):
            x = r.uniform(xa + 10, xb - 10)
            if PIER_A < x < PIER_B: continue
            sandcastle(M, x, shore_z(x) - r.uniform(3, 7), r)
        for _ in range(int((xb - xa) / 60)):
            x = r.uniform(xa + 10, xb - 10)
            if PIER_A < x < PIER_B: continue
            vendor_cart(M, x, r.uniform(ZW + 14, shore_z(x) - 20), r)
    pier(M, pr, PIER_X, y, r)
    bike_bridge(M, pr, spans, y, r)
    jetties_and_lighthouse(M, pr, r)


# ================================================================ pecas novas da orla
def bike_icon(M, x, z, y):
    """bicicleta branca pintada no asfalto da ciclovia"""
    M.at(x, z, 'orla'); M.m('liso'); c = (250, 250, 246)
    for cx in (x - 0.55, x + 0.55):
        for k in range(10):
            a0, a1 = 2 * math.pi * k / 10, 2 * math.pi * (k + 1) / 10
            M.quad((cx + math.cos(a0) * 0.38, y, z + math.sin(a0) * 0.38), (cx + math.cos(a1) * 0.38, y, z + math.sin(a1) * 0.38), (cx + math.cos(a1) * 0.3, y, z + math.sin(a1) * 0.3), (cx + math.cos(a0) * 0.3, y, z + math.sin(a0) * 0.3), c, (0, 1, 0))
    for (a, b) in (((x - 0.55, z), (x, z - 0.35)), ((x, z - 0.35), (x + 0.55, z)), ((x - 0.55, z), (x + 0.15, z)), ((x + 0.15, z), (x, z - 0.35))):
        dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz) or 1; nx, nz = -dz / L * 0.04, dx / L * 0.04
        M.quad((a[0] - nx, y, a[1] - nz), (b[0] - nx, y, b[1] - nz), (b[0] + nx, y, b[1] + nz), (a[0] + nx, y, a[1] + nz), c, (0, 1, 0))
    M.free()


def planter_orla(M, pr, x, z, y, r):
    """canteiro elevado de pedra no calcadao: forracao, flores tropicais e arbustos baixos"""
    M.at(x, z, 'orla'); L = r.uniform(7, 10); D = 2.2
    M.m('pedra'); M.prism([(x - L / 2, z - D / 2), (x + L / 2, z - D / 2), (x + L / 2, z + D / 2), (x - L / 2, z + D / 2)], y, y + 0.45, (214, 206, 192), False)
    M.m('concreto'); M.prism([(x - L / 2 - 0.08, z - D / 2 - 0.08), (x + L / 2 + 0.08, z - D / 2 - 0.08), (x + L / 2 + 0.08, z - D / 2 + 0.12), (x - L / 2 - 0.08, z - D / 2 + 0.12)], y + 0.45, y + 0.52, (236, 232, 222))
    M.prism([(x - L / 2 - 0.08, z + D / 2 - 0.12), (x + L / 2 + 0.08, z + D / 2 - 0.12), (x + L / 2 + 0.08, z + D / 2 + 0.08), (x - L / 2 - 0.08, z + D / 2 + 0.08)], y + 0.45, y + 0.52, (236, 232, 222))
    M.m('grama'); M.poly([(x - L / 2 + 0.1, y + 0.42, z - D / 2 + 0.1), (x + L / 2 - 0.1, y + 0.42, z - D / 2 + 0.1), (x + L / 2 - 0.1, y + 0.42, z + D / 2 - 0.1), (x - L / 2 + 0.1, y + 0.42, z + D / 2 - 0.1)], WHITE, (0, 1, 0))
    M.free()
    u = x - L / 2 + 0.8
    while u < x + L / 2 - 0.6:
        pr.tree(u, z + r.uniform(-0.45, 0.45), r.choice(('flores', 'flores', 'arbusto', 'buxo')), r.uniform(0.6, 0.85), y + 0.42); u += r.uniform(0.9, 1.4)
    pr.bench(x - L / 2 - 1.2, z, 1, 0, y); pr.bench(x + L / 2 + 1.2, z, -1, 0, y)


def bike_rack(M, x, z, y):
    M.at(x, z, 'orla'); M.m('metal')
    for k in range(6):
        u = x - 3 + k * 1.2
        for s in (-0.35, 0.35): M.box(u - 0.03, u + 0.03, y, y + 0.75, z + s - 0.03, z + s + 0.03, (90, 96, 104))
        M.box(u - 0.03, u + 0.03, y + 0.72, y + 0.8, z - 0.38, z + 0.38, (90, 96, 104))
    M.free()


def coconut_cart(M, x, z, y, r):
    """carrinho de agua de coco com guarda-sol e cocos empilhados"""
    M.at(x, z, 'orla'); col = r.choice(((40, 140, 80), (240, 190, 40), (220, 70, 50)))
    M.m('liso'); M.box(x - 1.0, x + 1.0, y + 0.45, y + 1.1, z - 0.6, z + 0.6, col)
    M.box(x - 1.05, x + 1.05, y + 1.1, y + 1.16, z - 0.65, z + 0.65, (245, 245, 242))
    for s in (-1, 1): M.cyl(x + s * 0.7, z + 0.62, 0.32, y, y + 0.64, (30, 30, 32), 8)
    for k in range(9): M.sphere(x - 0.6 + (k % 3) * 0.6, y + 1.32 + (k // 3) * 0.05, z - 0.3 + (k // 3) * 0.3, 0.17, (96, 140, 50), 5, 3)
    M.m('metal'); M.cyl(x + 0.9, z, 0.03, y + 1.1, y + 2.6, (220, 220, 220), 4, False)
    M.m('liso'); M.cyl(x + 0.9, z, 1.2, y + 2.3, y + 2.65, (250, 250, 246) if col != (240, 190, 40) else (230, 70, 50), 8, False, 0.04)
    M.free()


def drinking_fountain(M, x, z, y):
    M.at(x, z, 'orla'); M.m('metal')
    M.cyl(x, z, 0.16, y, y + 0.9, (70, 120, 160), 8); M.cyl(x, z, 0.28, y + 0.9, y + 1.0, (200, 206, 212), 10)
    M.box(x + 0.6 - 0.12, x + 0.6 + 0.12, y, y + 0.55, z - 0.12, z + 0.12, (70, 120, 160))
    M.free()


def totem(M, x, z, y, r):
    """totem de informacao / mapa da praia"""
    M.at(x, z, 'orla'); M.m('metal'); M.box(x - 0.6, x + 0.6, y, y + 2.2, z - 0.12, z + 0.12, (40, 80, 120))
    M.m('liso'); M.box(x - 0.5, x + 0.5, y + 0.9, y + 2.0, z - 0.15, z + 0.15, (230, 236, 240))
    M.box(x - 0.45, x + 0.45, y + 1.85, y + 1.95, z - 0.17, z + 0.17, (240, 190, 40))
    M.free()


def kiosk_glass(M, pr, x, z, y, r):
    """quiosque moderno: caixa envidracada, deck de madeira, telhado plano em balanco e mesas com ombrelones"""
    M.at(x, z, 'orla'); ac = r.choice(COLS)
    M.m('madeira'); M.prism([(x - 7, z - 3.5), (x + 7, z - 3.5), (x + 7, z + 4.5), (x - 7, z + 4.5)], y, y + 0.18, (176, 132, 92))
    M.m('reboco'); M.box(x - 2.8, x + 2.8, y + 0.18, y + 3.0, z - 2.0, z + 2.0, (246, 244, 238), top=False)
    M.m('vidro'); M.quad((x - 2.6, y + 1.1, z - 2.03), (x + 2.6, y + 1.1, z - 2.03), (x + 2.6, y + 2.7, z - 2.03), (x - 2.6, y + 2.7, z - 2.03), WHITE, (0, 0, -1))
    M.quad((x + 2.6, y + 1.1, z + 2.03), (x - 2.6, y + 1.1, z + 2.03), (x - 2.6, y + 2.7, z + 2.03), (x + 2.6, y + 2.7, z + 2.03), WHITE, (0, 0, 1))
    M.m('madeira'); M.box(x - 2.9, x + 2.9, y + 1.0, y + 1.1, z + 2.0, z + 2.6, (150, 108, 70))
    M.m('concreto'); M.box(x - 4.5, x + 4.5, y + 3.0, y + 3.35, z - 3.2, z + 3.8, (240, 238, 232))
    M.m('liso'); M.box(x - 4.55, x + 4.55, y + 3.05, y + 3.3, z + 3.8, z + 3.86, ac)
    for k in range(4):
        tx = x - 5.2 + k * 3.5; tz = z + 3.6 + (k % 2) * 0.3
        M.cyl(tx, tz, 0.45, y + 0.86, y + 0.9, (250, 250, 248), 10); M.cyl(tx, tz, 0.05, y + 0.18, y + 0.86, (60, 60, 64), 5, False)
        for s in (-1, 1): M.box(tx + s * 0.75 - 0.2, tx + s * 0.75 + 0.2, y + 0.18, y + 0.62, tz - 0.2, tz + 0.2, (60, 62, 66))
    M.free()
    for k in (0, 2): umbrella(M, x - 5.2 + k * 3.5, z + 3.6, ac, r, False, y_fix=y + 0.18)


def wet_sand(M, xa, xb):
    """faixa de areia molhada (mais escura) junto da agua"""
    M.free('orla'); M.m('areia'); x = xa
    while x < xb:
        x1 = min(x + 6.0, xb)
        za, zb = shore_z(x), shore_z(x1)
        M.quad((x, sand_y(x, za - 9) + 0.015, za - 9), (x1, sand_y(x1, zb - 9) + 0.015, zb - 9), (x1, Y_SEA + 0.02, zb - 1.0), (x, Y_SEA + 0.02, za - 1.0), (176, 158, 124), (0, 1, 0))
        x = x1
    M.free()


def lounger(M, x, z, ang, col, yb):
    """espreguicadeira: estrutura branca, assento e encosto inclinado em lona colorida"""
    F = Frame((x, z), (math.cos(ang), math.sin(ang)))
    M.m('liso')
    for (u, v) in ((-0.85, -0.3), (-0.85, 0.3), (0.85, -0.3), (0.85, 0.3)): M.prism(F.rect(u - 0.03, u + 0.03, v - 0.03, v + 0.03), yb, yb + 0.3, (245, 245, 242))
    M.prism(F.rect(-0.9, 0.35, -0.32, 0.32), yb + 0.3, yb + 0.36, col)
    M.quad(F.p(0.35, -0.32, yb + 0.36), F.p(0.35, 0.32, yb + 0.36), F.p(0.95, 0.32, yb + 0.95), F.p(0.95, -0.32, yb + 0.95), col, (-0.7, 0.7, 0))


def umbrella(M, x, z, col, r, chairs=True, y_fix=None, col2=None):
    """guarda-sol de 8 gomos (cores alternadas), haste inclinada levemente, com espreguicadeiras"""
    yb = sand_y(x, z) if y_fix is None else y_fix
    col2 = col2 or ((250, 250, 246) if r.random() < 0.7 else r.choice(COLS))
    M.at(x, z, 'orla'); M.m('liso')
    tilt = r.uniform(-0.25, 0.25) if y_fix is None else 0.0
    tx, tz = x + tilt, z + tilt * 0.5
    M.quad((x - 0.02, yb - 0.2, z), (x + 0.02, yb - 0.2, z), (tx + 0.02, yb + 2.35, tz), (tx - 0.02, yb + 2.35, tz), (230, 230, 230), (0, 0, 1))
    M.quad((x, yb - 0.2, z - 0.02), (x, yb - 0.2, z + 0.02), (tx, yb + 2.35, tz + 0.02), (tx, yb + 2.35, tz - 0.02), (230, 230, 230), (1, 0, 0))
    R = r.uniform(1.3, 1.6); apex = (tx, yb + 2.5, tz)
    for k in range(8):
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        p0 = (tx + math.cos(a0) * R, yb + 2.0, tz + math.sin(a0) * R); p1 = (tx + math.cos(a1) * R, yb + 2.0, tz + math.sin(a1) * R)
        M.tri(apex, p1, p0, col if k % 2 == 0 else col2, (0, 1, 0))
        pm = (tx + math.cos((a0 + a1) / 2) * R * 0.97, yb + 1.88, tz + math.sin((a0 + a1) / 2) * R * 0.97)       # babado
        M.tri(p0, p1, pm, shade(col if k % 2 == 0 else col2, -18), (math.cos((a0 + a1) / 2), 0.2, math.sin((a0 + a1) / 2)))
    if chairs:
        cc = col if r.random() < 0.6 else (250, 250, 248)
        for s in (-1, 1): lounger(M, x + s * 0.9, z + 0.6, math.pi / 2 + r.uniform(-0.15, 0.15), cc, yb)
    M.free()


def towel(M, x, z, ang, r):
    yb = sand_y(x, z) + 0.02
    F = Frame((x, z), (math.cos(ang), math.sin(ang))); c1, c2 = r.sample(COLS, 2)
    M.at(x, z, 'orla'); M.m('liso')
    for k in range(5):
        M.poly([F.p(-0.9 + k * 0.36, -0.45, yb), F.p(-0.54 + k * 0.36, -0.45, yb), F.p(-0.54 + k * 0.36, 0.45, yb), F.p(-0.9 + k * 0.36, 0.45, yb)], c1 if k % 2 == 0 else c2, (0, 1, 0))
    M.free()


def cooler(M, x, z, r):
    yb = sand_y(x, z); col = r.choice(((40, 110, 200), (220, 60, 50), (240, 190, 40)))
    M.at(x, z, 'orla'); M.m('liso'); M.box(x - 0.3, x + 0.3, yb, yb + 0.38, z - 0.2, z + 0.2, col)
    M.box(x - 0.32, x + 0.32, yb + 0.38, yb + 0.45, z - 0.22, z + 0.22, (250, 250, 248)); M.free()


def surfboard(M, x, z, ang, r, flat=False):
    """prancha: casco alongado com bico; em pe na areia ou deitada"""
    yb = sand_y(x, z); col = r.choice(COLS + [(250, 250, 248), (250, 250, 248)]); L = r.uniform(1.8, 2.6); Wb = 0.27
    c, s = math.cos(ang), math.sin(ang)
    out = [(-L / 2, 0), (-L / 2 + 0.1, Wb), (L * 0.15, Wb), (L / 2, 0), (L * 0.15, -Wb), (-L / 2 + 0.1, -Wb)]
    M.at(x, z, 'orla'); M.m('liso')
    if flat:
        pts = [(x + c * u - s * v, z + s * u + c * v) for (u, v) in out]
        M.prism(pts, yb + 0.02, yb + 0.08, col)
    else:
        for side in (-1, 1):
            M.poly([(x + c * v * 1.0 + c * 0.03 * side * 0, yb - 0.3 + (u + L / 2), z + s * v) for (u, v) in out][::side], col, (-s * side, 0, c * side))
    M.free()


def family(M, x, z, r):
    """grupo de banhistas sem gente: guarda-sol, cangas, cooler, bolsa, prancha ou bola"""
    umbrella(M, x, z, r.choice(COLS), r, r.random() < 0.6)
    for k in range(r.randint(1, 3)): towel(M, x + r.uniform(-2.2, 2.2), z + r.uniform(1.2, 3.0), r.uniform(-0.4, 0.4) + math.pi / 2, r)
    if r.random() < 0.6: cooler(M, x + r.uniform(-1.4, 1.4), z - r.uniform(0.6, 1.4), r)
    if r.random() < 0.35: surfboard(M, x + r.uniform(-2.5, 2.5), z + r.uniform(-2.0, 0.0), r.uniform(0, 6.28), r, True)
    if r.random() < 0.3:
        bx, bz = x + r.uniform(-3, 3), z + r.uniform(2, 4); yb = sand_y(bx, bz)
        M.at(bx, bz, 'orla'); M.m('liso'); M.sphere(bx, yb + 0.18, bz, 0.18, r.choice(COLS), 6, 4); M.free()


def sandcastle(M, x, z, r):
    """castelo de areia: torres, muralha e um balde virado"""
    yb = sand_y(x, z); M.at(x, z, 'orla'); M.m('areia'); c = (214, 190, 140)
    M.cyl(x, z, 0.75, yb - 0.05, yb + 0.25, c, 10)
    for k in range(4):
        a = k * math.pi / 2 + 0.4; M.cyl(x + math.cos(a) * 0.6, z + math.sin(a) * 0.6, 0.2, yb + 0.2, yb + 0.6, c, 8); M.cyl(x + math.cos(a) * 0.6, z + math.sin(a) * 0.6, 0.22, yb + 0.6, yb + 0.68, c, 8)
    M.cyl(x, z, 0.3, yb + 0.25, yb + 0.85, c, 8); M.cyl(x, z, 0.32, yb + 0.85, yb + 1.1, c, 8, True, 0.02)
    M.m('liso'); col = r.choice(COLS); bx, bz = x + 1.3, z + 0.4
    M.cyl(bx, bz, 0.18, yb, yb + 0.25, col, 8, True, 0.13); M.free()


def vendor_cart(M, x, z, r):
    """carrinho de ambulante (mate, picole) com guarda-sol"""
    yb = sand_y(x, z); M.at(x, z, 'orla'); col = r.choice(((40, 110, 200), (250, 196, 50), (230, 70, 50)))
    M.m('liso'); M.box(x - 0.6, x + 0.6, yb + 0.35, yb + 1.15, z - 0.4, z + 0.4, col)
    M.box(x - 0.62, x + 0.62, yb + 1.15, yb + 1.22, z - 0.42, z + 0.42, (250, 250, 248))
    for s in (-1, 1): M.cyl(x + s * 0.45, z + 0.42, 0.3, yb, yb + 0.6, (30, 30, 32), 8)
    M.free()
    umbrella(M, x + 0.7, z, (250, 250, 246), r, False, col2=col)


def flags(M, x, z, r):
    """bandeiras do salva-vidas (vermelha e amarela)"""
    yb = sand_y(x, z); M.at(x, z, 'orla'); M.m('liso')
    for k, col in enumerate(((220, 40, 40), (250, 210, 40))):
        fx = x + k * 2.5; M.cyl(fx, z, 0.04, yb - 0.4, yb + 4.0, (230, 230, 230), 5, False)
        M.box(fx + 0.04, fx + 1.2, yb + 3.2, yb + 3.95, z - 0.01, z + 0.01, col)
    M.free()


def beach_tennis(M, x, z, r):
    yb = sand_y(x, z) + 0.04
    M.at(x, z, 'orla'); M.m('liso')
    for (a, b, c, d) in ((x - 8, x + 8, z - 4, z - 3.92), (x - 8, x + 8, z + 3.92, z + 4), (x - 8, x - 7.92, z - 4, z + 4), (x + 7.92, x + 8, z - 4, z + 4)):
        M.poly([(a, yb, c), (b, yb, c), (b, yb, d), (a, yb, d)], (230, 70, 50), (0, 1, 0))
    for zz in (z - 4.4, z + 4.4): M.cyl(x, zz, 0.05, yb - 0.3, yb + 1.85, (250, 250, 250), 5, False)
    M.box(x - 0.015, x + 0.015, yb + 1.0, yb + 1.75, z - 4.4, z + 4.4, (40, 42, 46)); M.box(x - 0.03, x + 0.03, yb + 1.75, yb + 1.82, z - 4.4, z + 4.4, (250, 250, 248))
    M.free()


def kayak(M, x, z, ang, col):
    yb = sand_y(x, z); c, s = math.cos(ang), math.sin(ang); L = 3.6
    out = [(-L / 2, 0), (-L * 0.25, 0.35), (L * 0.25, 0.35), (L / 2, 0), (L * 0.25, -0.35), (-L * 0.25, -0.35)]
    pts = [(x + c * u - s * v, z + s * u + c * v) for (u, v) in out]
    M.at(x, z, 'orla'); M.m('liso'); M.prism(pts, yb, yb + 0.32, col, True, False, shade(col, 20))
    M.cyl(x, z, 0.28, yb + 0.32, yb + 0.36, (30, 30, 34), 8); M.free()


def rental(M, pr, x, r):
    """aluguel de caiaques e pranchas: barraca, prateleira de pranchas e caiaques na areia molhada"""
    z = shore_z(x) - 18; yb = sand_y(x, z)
    M.at(x, z, 'orla'); M.m('madeira')
    for (dx, dz) in ((-1.8, -1.2), (1.8, -1.2), (1.8, 1.2), (-1.8, 1.2)): M.box(x + dx - 0.07, x + dx + 0.07, yb - 0.3, yb + 2.4, z + dz - 0.07, z + dz + 0.07, (150, 108, 70))
    M.m('liso'); M.box(x - 2.1, x + 2.1, yb + 2.4, yb + 2.5, z - 1.5, z + 1.5, (40, 140, 180)); M.box(x - 1.6, x + 1.6, yb + 0.6, yb + 1.0, z - 1.2, z - 1.0, (245, 245, 240))
    M.m('madeira')
    for k in range(2): M.box(x + 3.0, x + 6.2, yb + 0.5 + k * 0.6, yb + 0.56 + k * 0.6, z - 0.05, z + 0.05, (150, 108, 70))
    M.free()
    for k in range(4): surfboard(M, x + 3.3 + k * 0.8, z + 0.3, 0.0, r, False)
    for k in range(4): kayak(M, x - 4 + k * 2.4, shore_z(x) - 3.5, math.pi / 2 + r.uniform(-0.2, 0.2), r.choice(COLS))


def bike_bridge(M, pr, spans, y, r):
    """passarela da ciclovia sobre a foz do rio (liga as duas orlas): tabuleiro em arco, ciclovia vermelha, guarda-corpo e postes"""
    za, zb = Z0 + 0.3, Z0 + 4.1; zm = (za + zb) / 2
    xa = river_x(zm) - RIVER_W / 2 - RIVER_WALL - 0.4; xb = river_x(zm) + RIVER_W / 2 + RIVER_WALL + 0.4
    n = 24; rise = 1.1
    yy = lambda t: y + rise * math.sin(math.pi * t)
    M.at((xa + xb) / 2, zm, 'orla')
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n; x0, x1 = xa + (xb - xa) * t0, xa + (xb - xa) * t1; y0, y1 = yy(t0), yy(t1)
        M.m('asfalto'); M.quad((x0, y0 + 0.03, za + 0.5), (x1, y1 + 0.03, za + 0.5), (x1, y1 + 0.03, zb - 0.5), (x0, y0 + 0.03, zb - 0.5), (255, 150, 120), (0, 1, 0))
        M.m('concreto')
        M.quad((x0, y0 + 0.03, za), (x1, y1 + 0.03, za), (x1, y1 + 0.03, za + 0.5), (x0, y0 + 0.03, za + 0.5), (236, 232, 224), (0, 1, 0))
        M.quad((x0, y0 + 0.03, zb - 0.5), (x1, y1 + 0.03, zb - 0.5), (x1, y1 + 0.03, zb), (x0, y0 + 0.03, zb), (236, 232, 224), (0, 1, 0))
        for zz, s in ((za, -1), (zb, 1)): M.quad((x0, y0 - 0.55, zz), (x1, y1 - 0.55, zz), (x1, y1 + 0.03, zz), (x0, y0 + 0.03, zz), (214, 210, 202), (0, 0, s))
        M.quad((x0, y0 - 0.55, zb), (x1, y1 - 0.55, zb), (x1, y1 - 0.55, za), (x0, y0 - 0.55, za), (190, 186, 178), (0, -1, 0))
        M.m('liso')
        for zz in (za + 0.52, zb - 0.6): M.quad((x0, y0 + 0.06, zz), (x1, y1 + 0.06, zz), (x1, y1 + 0.06, zz + 0.08), (x0, y0 + 0.06, zz + 0.08), (250, 250, 246), (0, 1, 0))
        M.m('metal')
        for zz in (za + 0.08, zb - 0.08):
            M.quad((x0, y0 + 1.05, zz), (x1, y1 + 1.05, zz), (x1, y1 + 1.15, zz), (x0, y0 + 1.15, zz), (60, 64, 70), (0, 0, 1))
            M.quad((x0, y0 + 0.55, zz), (x1, y1 + 0.55, zz), (x1, y1 + 0.6, zz), (x0, y0 + 0.6, zz), (60, 64, 70), (0, 0, 1))
            M.box(x0 - 0.04, x0 + 0.04, y0 + 0.03, y0 + 1.15, zz - 0.04, zz + 0.04, (60, 64, 70))
    M.m('concreto')
    for xp in (river_x(zm) - RIVER_W / 4, river_x(zm) + RIVER_W / 4): M.box(xp - 0.5, xp + 0.5, -3.5, yy((xp - xa) / (xb - xa)) - 0.55, za + 0.3, zb - 0.3, (196, 192, 184))
    M.free()
    for t in (0.25, 0.75):
        xx = xa + (xb - xa) * t; M.at(xx, za, 'orla'); M.m('metal'); M.cyl(xx, za + 0.1, 0.06, yy(t), yy(t) + 4.2, (60, 64, 70), 6, False)
        M.m('liso'); M.sphere(xx, yy(t) + 4.4, za + 0.1, 0.26, (255, 246, 214), 6, 4); M.free()


def jetties_and_lighthouse(M, pr, r):
    """molhes de pedra prolongando o cais mar adentro (dividem a agua do rio que chega na praia) e o farol na ponta
    do molhe oeste; farolete verde na ponta do leste. Luzes registradas em pr.luzes para o ciclo de dia e noite."""
    zs = shore_z(river_x(1840)) + 14.0
    zt = zs + 70.0
    for sgn in (-1, 1):
        x0 = river_x(1840) + sgn * (RIVER_W / 2 + RIVER_WALL / 2)
        # passeio de concreto em cima do molhe, levemente alargando ate a plataforma da ponta
        z = zs - 2
        while z < zt:
            z1 = min(z + 6, zt); w = 2.2 + 1.8 * (z - zs) / (zt - zs)
            M.at(x0, (z + z1) / 2, 'orla'); M.m('concreto')
            M.prism([(x0 - w, z), (x0 + w, z), (x0 + w, z1), (x0 - w, z1)], -3.5, 0.9, (206, 202, 194), True)
            M.m('pedra')                                                                            # enrocamento dos dois lados
            for s in (-1, 1):
                for zz in np.arange(z + 0.8, z1, 1.7):
                    for j in range(2):
                        rx_ = x0 + s * (w + 0.9 + j * 1.3) + r.uniform(-0.3, 0.3)
                        M.sphere(rx_, -0.5 + (0.7 if j == 0 else 0.0) + r.uniform(-0.2, 0.2), zz + r.uniform(-0.4, 0.4), r.uniform(0.9, 1.4), r.choice(((150, 146, 138), (128, 124, 118), (170, 164, 152))), 6, 3, 0.75, 0.18, r)
            M.m('metal')
            for s in (-1, 1): M.box(x0 + s * (w - 0.1) - 0.04, x0 + s * (w - 0.1) + 0.04, 1.85, 1.95, z, z1, (200, 60, 50) if sgn < 0 else (40, 140, 80))
            for s in (-1, 1): M.box(x0 + s * (w - 0.1) - 0.05, x0 + s * (w - 0.1) + 0.05, 0.9, 1.95, z - 0.05, z + 0.05, (90, 94, 100))
            M.free(); z = z1
        # plataforma redonda na ponta
        cx, cz = x0, zt + 6.0
        M.at(cx, cz, 'orla'); M.m('pedra')
        for k in range(26):
            a = 2 * math.pi * k / 26; M.sphere(cx + math.cos(a) * 9.8, -0.4 + r.uniform(-0.2, 0.3), cz + math.sin(a) * 9.8, r.uniform(1.2, 1.7), r.choice(((150, 146, 138), (128, 124, 118))), 6, 3, 0.75, 0.18, r)
        M.m('concreto'); M.cyl(cx, cz, 8.4, -3.5, 1.1, (206, 202, 194), 24)
        M.prism([(cx - 4.0, cz - 9.0), (cx + 4.0, cz - 9.0), (cx + 4.0, cz - 4.0), (cx - 4.0, cz - 4.0)], -3.5, 1.0, (206, 202, 194))
        M.m('metal')
        for k in range(24):
            a0, a1 = 2 * math.pi * k / 24, 2 * math.pi * (k + 1) / 24
            if abs(math.sin((a0 + a1) / 2)) > 0.92 and math.sin((a0 + a1) / 2) < 0: continue           # entrada vinda do molhe
            p0 = (cx + math.cos(a0) * 8.2, cz + math.sin(a0) * 8.2); p1 = (cx + math.cos(a1) * 8.2, cz + math.sin(a1) * 8.2)
            M.quad((p0[0], 2.05, p0[1]), (p1[0], 2.05, p1[1]), (p1[0], 2.15, p1[1]), (p0[0], 2.15, p0[1]), (90, 94, 100), (math.cos(a0), 0, math.sin(a0)))
            M.box(p0[0] - 0.05, p0[0] + 0.05, 1.1, 2.15, p0[1] - 0.05, p0[1] + 0.05, (90, 94, 100))
        M.free()
        if sgn < 0: lighthouse(M, pr, cx, cz, 1.1, r)
        else: beacon(M, pr, cx, cz, 1.1)


def lighthouse(M, pr, x, z, y0, r):
    """farol: torre conica de 34 m em faixas brancas e vermelhas, porta, janelinhas, galeria com guarda-corpo,
    lanterna envidracada com a lampada, cupula vermelha com cata-vento; casa do faroleiro ao lado"""
    H = 34.0; R0, R1 = 3.6, 2.2
    M.at(x, z, 'orla')
    M.m('concreto'); M.cyl(x, z, R0 + 0.6, y0, y0 + 1.2, (214, 208, 198), 20)
    nb = 7
    for k in range(nb):
        t0, t1 = k / nb, (k + 1) / nb
        ya, yb_ = y0 + 1.2 + (H - 1.2) * t0, y0 + 1.2 + (H - 1.2) * t1
        ra, rb = R0 + (R1 - R0) * t0, R0 + (R1 - R0) * t1
        M.m('reboco'); M.cyl(x, z, ra, ya, yb_, (240, 238, 232) if k % 2 == 0 else (196, 40, 36), 24, False, rb)
    yt = y0 + H
    M.m('liso')
    for k in range(5):                                                  # janelinhas subindo em espiral
        a = k * 1.3 + 0.4; yy = y0 + 5 + k * 5.6; rr = R0 + (R1 - R0) * (yy - y0) / H + 0.05
        wx, wz = x + math.cos(a) * rr, z + math.sin(a) * rr; tx_, tz_ = -math.sin(a), math.cos(a)
        M.quad((wx - tx_ * 0.35, yy, wz - tz_ * 0.35), (wx + tx_ * 0.35, yy, wz + tz_ * 0.35), (wx + tx_ * 0.35, yy + 1.0, wz + tz_ * 0.35), (wx - tx_ * 0.35, yy + 1.0, wz - tz_ * 0.35), (40, 50, 62), (math.cos(a), 0, math.sin(a)))
    a = -math.pi / 2; dx_, dz_ = math.cos(a) * (R0 + 0.06), math.sin(a) * (R0 + 0.06)
    M.quad((x + dx_ - 0.6, y0 + 1.2, z + dz_), (x + dx_ + 0.6, y0 + 1.2, z + dz_), (x + dx_ + 0.6, y0 + 3.6, z + dz_), (x + dx_ - 0.6, y0 + 3.6, z + dz_), (60, 80, 70), (0, 0, -1))
    # galeria
    M.m('concreto'); M.cyl(x, z, R1 + 1.3, yt, yt + 0.35, (230, 226, 218), 24)
    M.m('metal')
    for k in range(32):
        a0, a1 = 2 * math.pi * k / 32, 2 * math.pi * (k + 1) / 32; rr = R1 + 1.2
        p0 = (x + math.cos(a0) * rr, z + math.sin(a0) * rr); p1 = (x + math.cos(a1) * rr, z + math.sin(a1) * rr)
        M.quad((p0[0], yt + 1.35, p0[1]), (p1[0], yt + 1.35, p1[1]), (p1[0], yt + 1.45, p1[1]), (p0[0], yt + 1.45, p0[1]), (40, 44, 50), (math.cos(a0), 0, math.sin(a0)))
        M.box(p0[0] - 0.04, p0[0] + 0.04, yt + 0.35, yt + 1.45, p0[1] - 0.04, p0[1] + 0.04, (40, 44, 50))
    # lanterna
    M.m('reboco'); M.cyl(x, z, R1 - 0.2, yt + 0.35, yt + 1.3, (196, 40, 36), 16)
    M.m('vidro'); M.cyl(x, z, R1 - 0.35, yt + 1.3, yt + 4.2, (210, 236, 246), 16, False)
    M.m('metal')
    for k in range(8):
        a = 2 * math.pi * k / 8; M.box(x + math.cos(a) * (R1 - 0.33) - 0.06, x + math.cos(a) * (R1 - 0.33) + 0.06, yt + 1.3, yt + 4.2, z + math.sin(a) * (R1 - 0.33) - 0.06, z + math.sin(a) * (R1 - 0.33) + 0.06, (40, 44, 50))
    M.m('liso'); M.sphere(x, yt + 2.75, z, 0.75, (255, 244, 190), 10, 6)            # lampada (emissiva no ciclo de noite)
    M.cyl(x, z, 0.18, yt + 1.3, yt + 2.2, (60, 60, 64), 8)
    M.m('reboco'); M.cyl(x, z, R1 - 0.1, yt + 4.2, yt + 5.6, (196, 40, 36), 16, False, 0.25)
    M.m('metal'); M.cyl(x, z, 0.05, yt + 5.6, yt + 7.0, (40, 44, 50), 5, False); M.sphere(x, yt + 5.7, z, 0.25, (40, 44, 50), 6, 4)
    M.box(x - 0.6, x + 0.6, yt + 6.6, yt + 6.66, z - 0.03, z + 0.03, (40, 44, 50))
    # casa do faroleiro
    hx, hz = x + 5.0, z - 1.0
    M.m('reboco'); M.box(hx - 2.0, hx + 2.0, y0, y0 + 3.0, hz - 2.6, hz + 2.6, (244, 242, 236), top=False)
    M.m('telha'); M.quad((hx - 2.3, y0 + 3.0, hz - 2.9), (hx - 2.3, y0 + 3.0, hz + 2.9), (hx, y0 + 4.4, hz + 2.9), (hx, y0 + 4.4, hz - 2.9), (180, 70, 50), (-0.5, 0.85, 0))
    M.quad((hx, y0 + 4.4, hz - 2.9), (hx, y0 + 4.4, hz + 2.9), (hx + 2.3, y0 + 3.0, hz + 2.9), (hx + 2.3, y0 + 3.0, hz - 2.9), (180, 70, 50), (0.5, 0.85, 0))
    M.m('reboco')
    for s in (-1, 1): M.tri((hx - 2.0, y0 + 3.0, hz + s * 2.6), (hx + 2.0, y0 + 3.0, hz + s * 2.6), (hx, y0 + 4.4, hz + s * 2.6), (244, 242, 236), (0, 0, s))
    M.m('liso')
    M.quad((hx - 0.5, y0, hz - 2.64), (hx + 0.5, y0, hz - 2.64), (hx + 0.5, y0 + 2.1, hz - 2.64), (hx - 0.5, y0 + 2.1, hz - 2.64), (60, 80, 70), (0, 0, -1))
    for s in (-1, 1): M.quad((hx + 2.04, y0 + 1.1, hz + s * 1.2 - 0.5), (hx + 2.04, y0 + 1.1, hz + s * 1.2 + 0.5), (hx + 2.04, y0 + 2.1, hz + s * 1.2 + 0.5), (hx + 2.04, y0 + 2.1, hz + s * 1.2 - 0.5), (40, 50, 62), (1, 0, 0))
    M.free()
    pr.luzes.append({'tipo': 'farol', 'x': round(x, 2), 'y': round(yt + 2.75, 2), 'z': round(z, 2), 'cor': [255, 244, 190], 'alcance_m': 900, 'giro_s': 12.0})


def beacon(M, pr, x, z, y0):
    """farolete verde na ponta do molhe leste"""
    M.at(x, z, 'orla'); M.m('reboco'); M.cyl(x, z, 1.4, y0, y0 + 7.5, (240, 238, 232), 12, False, 1.0)
    M.cyl(x, z, 1.05, y0 + 3.0, y0 + 5.0, (40, 140, 80), 12, False, 0.95)
    M.m('concreto'); M.cyl(x, z, 1.6, y0 + 7.5, y0 + 7.8, (230, 226, 218), 12)
    M.m('vidro'); M.cyl(x, z, 0.6, y0 + 7.8, y0 + 9.0, (200, 240, 210), 10, False)
    M.m('liso'); M.sphere(x, y0 + 8.4, z, 0.35, (140, 255, 160), 8, 5)
    M.m('reboco'); M.cyl(x, z, 0.75, y0 + 9.0, y0 + 9.7, (40, 140, 80), 10, False, 0.1)
    M.free()
    pr.luzes.append({'tipo': 'farolete', 'x': round(x, 2), 'y': round(y0 + 8.4, 2), 'z': round(z, 2), 'cor': [140, 255, 160], 'alcance_m': 300, 'pisca_s': 3.0})


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


def G_h(x, z):
    return sand_y(x, z) if z < shore_z(x) else -1.5 - min((z - shore_z(x)) / 120, 1) * 5.0


# ================================================================ pier de diversoes (estilo pier californiano)
def _pile(M, x, z, yd):
    hb = min(G_h(x, z), -0.4); M.cyl(x, z, 0.28, hb - 1.5, yd - 0.45, (120, 96, 72), 6, False)


def _rail_line(M, pts, yd, col=(246, 246, 242)):
    for i in range(len(pts) - 1):
        (x0, z0), (x1, z1) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, z1 - z0); nx, nz = (z1 - z0) / L * 0.05, -(x1 - x0) / L * 0.05
        for yy, hh in ((yd + 1.0, 0.1), (yd + 0.5, 0.06)):
            M.prism([(x0 - nx, z0 - nz), (x1 - nx, z1 - nz), (x1 + nx, z1 + nz), (x0 + nx, z0 + nz)], yy, yy + hh, col)
        for t in np.arange(0, L, 2.5):
            px, pz = x0 + (x1 - x0) * t / L, z0 + (z1 - z0) * t / L
            M.box(px - 0.05, px + 0.05, yd, yd + 1.1, pz - 0.05, pz + 0.05, col)


def _deck(M, x0, x1, z0, z1, yd):
    z = z0
    while z < z1:
        zz = min(z + 12, z1)
        M.at((x0 + x1) / 2, (z + zz) / 2, 'pier'); M.m('madeira')
        M.prism([(x0, z), (x1, z), (x1, zz), (x0, zz)], yd - 0.45, yd, (176, 140, 104), True, True)
        M.m('madeira')
        for xx in np.arange(x0 + 1, x1, 5.0):
            for zp in np.arange(z + 1, zz, 6.0): _pile(M, xx, zp, yd)
        M.free(); z = zz


def stall(M, x, z, yd, col, face=1, w=4.0):
    """barraca de comida/jogo: caixa com balcao, toldo listrado e placa colorida"""
    M.at(x, z, 'orla'); M.m('reboco'); M.box(x - w / 2, x + w / 2, yd, yd + 2.8, z - 1.5, z + 1.5, (246, 242, 232), top=False)
    M.m('liso'); M.box(x - w / 2 - 0.1, x + w / 2 + 0.1, yd + 2.8, yd + 3.0, z - 1.6, z + 1.6, (240, 238, 232))
    fz = z + face * 1.52
    M.box(x - w / 2 + 0.3, x + w / 2 - 0.3, yd + 1.0, yd + 2.3, fz - 0.02, fz + 0.02, (60, 64, 72))
    M.box(x - w / 2, x + w / 2, yd + 0.95, yd + 1.05, fz, fz + face * 0.6, (150, 108, 70))
    for k in range(int(w / 0.5)):
        xa = x - w / 2 + k * 0.5
        M.quad((xa, yd + 2.75, fz), (xa + 0.5, yd + 2.75, fz), (xa + 0.5, yd + 2.35, fz + face * 1.2), (xa, yd + 2.35, fz + face * 1.2), col if k % 2 == 0 else (250, 250, 246), (0, 0.8, face * 0.5))
    M.box(x - w / 2 + 0.2, x + w / 2 - 0.2, yd + 3.0, yd + 3.9, z - 0.05, z + 0.05, col)
    M.free()


def ferris_wheel(M, pr, x, z, yd, r, R=15.0, ncab=20):
    """roda-gigante: dois aros com treliça, 16 raios, cubo, 20 cabines coloridas, cavaletes em A e lâmpadas no aro"""
    cy = yd + R + 3.0; wid = 2.6 + R * 0.06
    M.at(x, z, 'orla'); M.m('metal'); white = (244, 244, 240); n = 48
    for s in (-1, 1):
        zz = z + s * wid / 2
        for k in range(n):                                   # aros externo e interno
            a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
            for rr in (R, R - 1.2):
                p0 = (x + math.cos(a0) * rr, cy + math.sin(a0) * rr); p1 = (x + math.cos(a1) * rr, cy + math.sin(a1) * rr)
                M.quad((p0[0], p0[1], zz - 0.08), (p1[0], p1[1], zz - 0.08), (p1[0], p1[1], zz + 0.08), (p0[0], p0[1], zz + 0.08), white, (math.cos(a0), math.sin(a0), 0))
                M.quad((p0[0], p0[1], zz), (p1[0], p1[1], zz), (p1[0] * 0.999 + x * 0.001, p1[1] - 0.12, zz), (p0[0] * 0.999 + x * 0.001, p0[1] - 0.12, zz), white, (0, 0, s))
            if k % 2 == 0:                                   # treliça entre os aros
                pa = (x + math.cos(a0) * R, cy + math.sin(a0) * R); pb = (x + math.cos(a1) * (R - 1.2), cy + math.sin(a1) * (R - 1.2))
                M.quad((pa[0], pa[1], zz - 0.05), (pb[0], pb[1], zz - 0.05), (pb[0], pb[1], zz + 0.05), (pa[0], pa[1], zz + 0.05), white, (0, 0, s))
        for k in range(16):                                  # raios
            a = 2 * math.pi * k / 16; ex, ey = x + math.cos(a) * (R - 1.2), cy + math.sin(a) * (R - 1.2)
            M.quad((x, cy - 0.06, zz), (ex, ey - 0.06, zz), (ex, ey + 0.06, zz), (x, cy + 0.06, zz), white, (0, 0, s))
        for dx in (-1, 1):                                   # cavaletes em A
            fx = x + dx * R * 0.6
            M.quad((fx - 0.25, yd, zz + s * 1.6), (fx + 0.25, yd, zz + s * 1.6), (x + 0.25, cy, zz), (x - 0.25, cy, zz), white, (0, 0.3, s))
    M.cyl(x, z, 0.7, cy - 0.7, cy + 0.7, white, 10) if False else M.box(x - 0.6, x + 0.6, cy - 0.6, cy + 0.6, z - wid / 2 - 0.4, z + wid / 2 + 0.4, (200, 200, 196))
    cols = [(230, 60, 60), (250, 190, 40), (40, 140, 220), (60, 180, 100), (220, 90, 180)]
    for k in range(ncab):
        a = 2 * math.pi * k / ncab; gx, gy = x + math.cos(a) * R, cy + math.sin(a) * R
        c = cols[k % len(cols)]
        M.box(gx - 0.05, gx + 0.05, gy - 1.2, gy, z - 0.05, z + 0.05, (80, 84, 90))
        M.box(gx - 1.0, gx + 1.0, gy - 2.6, gy - 1.2, z - 0.9, z + 0.9, c)
        M.box(gx - 1.05, gx + 1.05, gy - 1.25, gy - 1.1, z - 0.95, z + 0.95, (246, 246, 242))
        M.box(gx - 0.95, gx + 0.95, gy - 2.1, gy - 1.5, z - 0.92, z + 0.92, (60, 70, 84))
    M.m('liso')
    for k in range(32):                                      # lâmpadas no aro (acendem no ciclo de noite)
        a = 2 * math.pi * k / 32; M.sphere(x + math.cos(a) * (R + 0.15), cy + math.sin(a) * (R + 0.15), z + wid / 2 + 0.1, 0.16, (255, 236, 160), 4, 3)
    M.m('concreto'); M.box(x - 4, x + 4, yd, yd + 0.6, z - 3.2, z + 3.2, (220, 216, 208))
    M.free()
    pr.luzes.append({'tipo': 'roda_gigante', 'x': round(x, 2), 'y': round(cy, 2), 'z': round(z, 2), 'cor': [255, 236, 160], 'raio_m': R, 'alcance_m': 120})


def coaster(M, x0, x1, z0, z1, yd, r, hmax=11.5):
    """montanha-russa: circuito fechado em volta do parque, sobe e desce, trilho duplo vermelho sobre pilares brancos, carrinhos"""
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; ax, az = (x1 - x0) / 2, (z1 - z0) / 2
    n = 160; pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        px = cx + ax * math.cos(t); pz = cz + az * math.sin(t) * (1 + 0.12 * math.sin(3 * t))
        h = 6.0 + (hmax - 6.0) * (0.5 + 0.5 * math.sin(2 * t + 0.6)) * 0.6 + (hmax - 6.0) * 0.9 * max(0.0, math.sin(t)) ** 6
        pts.append((px, yd + h, pz))
    M.at(cx, cz, 'orla'); M.m('metal'); red = (210, 40, 40); white = (240, 240, 236)
    for k in range(n):
        (xa, ya, za), (xb, yb, zb) = pts[k], pts[(k + 1) % n]
        L = math.hypot(xb - xa, zb - za) or 1; nx, nz = (zb - za) / L, -(xb - xa) / L
        for s in (-0.55, 0.55):
            M.quad((xa + nx * s - nx * 0.06, ya, za + nz * s - nz * 0.06), (xb + nx * s - nx * 0.06, yb, zb + nz * s - nz * 0.06), (xb + nx * s + nx * 0.06, yb, zb + nz * s + nz * 0.06), (xa + nx * s + nx * 0.06, ya, za + nz * s + nz * 0.06), red, (0, 1, 0))
            M.quad((xa + nx * s, ya - 0.18, za + nz * s), (xb + nx * s, yb - 0.18, zb + nz * s), (xb + nx * s, yb, zb + nz * s), (xa + nx * s, ya, za + nz * s), shade(red, -25), (nx, 0, nz))
        M.quad((xa - nx * 0.5, ya - 0.05, za - nz * 0.5), (xa + nx * 0.5, ya - 0.05, za + nz * 0.5), (xa + nx * 0.5, ya - 0.12, za + nz * 0.5), (xa - nx * 0.5, ya - 0.12, za - nz * 0.5), (60, 60, 64), (0, 1, 0))
        if k % 5 == 0:
            M.cyl(xa, za, 0.22, yd, ya - 0.18, white, 6, False)
            if k % 10 == 0: M.box(xa - 0.06, xa + 0.06, (yd + ya) / 2 - 0.05, (yd + ya) / 2 + 0.05, za - 0.8, za + 0.8, white)
    M.m('liso')
    for j in range(5):                                      # trem de 5 carrinhos
        (xa, ya, za), (xb, yb, zb) = pts[30 + j * 2], pts[31 + j * 2]
        M.box(xa - 0.7, xa + 0.7, ya + 0.05, ya + 0.8, za - 0.7, za + 0.7, (250, 196, 40) if j % 2 else (40, 120, 220))
    M.free()


def carousel(M, x, z, yd, r):
    """carrossel: prédio redondo de 12 lados com telhado em cone listrado, cavalos em postes dourados"""
    M.at(x, z, 'orla'); M.m('madeira'); M.cyl(x, z, 7.0, yd, yd + 0.4, (190, 150, 110), 12)
    M.m('liso'); cols = [(230, 60, 60), (250, 250, 246)]
    for k in range(12):
        a = 2 * math.pi * k / 12; M.cyl(x + math.cos(a) * 6.6, z + math.sin(a) * 6.6, 0.15, yd + 0.4, yd + 4.0, (240, 210, 120), 6)
    for k in range(12):
        a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
        M.tri((x, yd + 8.0, z), (x + math.cos(a1) * 7.6, yd + 4.0, z + math.sin(a1) * 7.6), (x + math.cos(a0) * 7.6, yd + 4.0, z + math.sin(a0) * 7.6), cols[k % 2], (0, 1, 0))
        M.quad((x + math.cos(a0) * 7.6, yd + 4.0, z + math.sin(a0) * 7.6), (x + math.cos(a1) * 7.6, yd + 4.0, z + math.sin(a1) * 7.6), (x + math.cos(a1) * 7.6, yd + 3.4, z + math.sin(a1) * 7.6), (x + math.cos(a0) * 7.6, yd + 3.4, z + math.sin(a0) * 7.6), (240, 210, 120), (math.cos(a0), 0, math.sin(a0)))
    M.cyl(x, z, 0.2, yd + 8.0, yd + 9.2, (240, 210, 120), 6); M.sphere(x, yd + 9.3, z, 0.3, (240, 210, 120), 6, 4)
    M.cyl(x, z, 1.4, yd + 0.4, yd + 3.4, (230, 220, 200), 12)
    hcols = [(250, 250, 246), (200, 150, 100), (60, 60, 64), (240, 200, 120)]
    for ring, rr in enumerate((3.2, 5.0)):
        for k in range(10 + ring * 4):
            a = 2 * math.pi * k / (10 + ring * 4) + ring * 0.2; hx, hz = x + math.cos(a) * rr, z + math.sin(a) * rr
            hy = yd + 1.0 + 0.35 * math.sin(k * 1.7)
            M.cyl(hx, hz, 0.04, yd + 0.4, yd + 3.4, (240, 210, 120), 4)
            tx, tz = -math.sin(a), math.cos(a); c = hcols[k % 4]
            M.box(min(hx - tx * 0.6, hx + tx * 0.6) - 0.1, max(hx - tx * 0.6, hx + tx * 0.6) + 0.1, hy, hy + 0.5, min(hz - tz * 0.6, hz + tz * 0.6) - 0.1, max(hz - tz * 0.6, hz + tz * 0.6) + 0.1, c)
            M.box(hx + tx * 0.55 - 0.12, hx + tx * 0.55 + 0.12, hy + 0.4, hy + 0.95, hz + tz * 0.55 - 0.12, hz + tz * 0.55 + 0.12, c)
    M.free()


def arch(M, x, z, yd, w):
    """portal de entrada do pier: dois pilares, arco com placa e lâmpadas"""
    M.at(x, z, 'orla'); M.m('reboco')
    for s in (-1, 1): M.box(x + s * w / 2 - 0.6, x + s * w / 2 + 0.6, yd, yd + 7.0, z - 0.6, z + 0.6, (244, 240, 230))
    M.m('liso'); n = 16
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        a0, a1 = math.pi * t0, math.pi * t1
        x0, x1 = x - math.cos(a0) * w / 2, x - math.cos(a1) * w / 2
        y0, y1 = yd + 7.0 + math.sin(a0) * 2.2, yd + 7.0 + math.sin(a1) * 2.2
        M.quad((x0, y0, z - 0.3), (x1, y1, z - 0.3), (x1, y1 + 0.5, z - 0.3), (x0, y0 + 0.5, z - 0.3), (40, 110, 180), (0, 0, -1))
        M.quad((x1, y1, z + 0.3), (x0, y0, z + 0.3), (x0, y0 + 0.5, z + 0.3), (x1, y1 + 0.5, z + 0.3), (40, 110, 180), (0, 0, 1))
        M.quad((x0, y0 + 0.5, z - 0.3), (x1, y1 + 0.5, z - 0.3), (x1, y1 + 0.5, z + 0.3), (x0, y0 + 0.5, z + 0.3), (40, 110, 180), (0, 1, 0))
        M.sphere(x0, y0 + 0.75, z - 0.32, 0.12, (255, 236, 160), 4, 3)
    M.box(x - w * 0.3, x + w * 0.3, yd + 5.4, yd + 6.8, z - 0.35, z + 0.35, (250, 196, 40))
    M.box(x - w * 0.28, x + w * 0.28, yd + 5.55, yd + 6.65, z - 0.38, z + 0.38, (210, 50, 50))
    M.free()


def drop_tower(M, pr, x, z, yd, H=46.0):
    """torre de queda livre: mastro trelicado, anel de assentos, topo com luzes"""
    M.at(x, z, 'orla'); M.m('metal'); white = (240, 240, 236)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4; px, pz = x + math.cos(a) * 1.1, z + math.sin(a) * 1.1
        M.box(px - 0.18, px + 0.18, yd, yd + H, pz - 0.18, pz + 0.18, white)
    for h in np.arange(yd + 2, yd + H, 3.0):
        M.box(x - 1.2, x + 1.2, h, h + 0.12, z - 1.2, z + 1.2, white)
    M.m('liso'); M.cyl(x, z, 3.2, yd + H * 0.62, yd + H * 0.62 + 1.6, (230, 60, 60), 16)
    for k in range(16):
        a = 2 * math.pi * k / 16; M.box(x + math.cos(a) * 3.2 - 0.3, x + math.cos(a) * 3.2 + 0.3, yd + H * 0.62 - 0.6, yd + H * 0.62, z + math.sin(a) * 3.2 - 0.3, z + math.sin(a) * 3.2 + 0.3, (250, 196, 40))
    M.cyl(x, z, 2.2, yd + H, yd + H + 2.2, (40, 110, 200), 12, True, 0.6)
    for k in range(12): a = 2 * math.pi * k / 12; M.sphere(x + math.cos(a) * 2.25, yd + H + 0.3, z + math.sin(a) * 2.25, 0.16, (255, 236, 160), 4, 3)
    M.m('concreto'); M.cyl(x, z, 4.5, yd, yd + 0.5, (220, 216, 208), 16)
    M.free()
    pr.luzes.append({'tipo': 'torre_queda', 'x': round(x, 2), 'y': round(yd + H + 1, 2), 'z': round(z, 2), 'cor': [255, 236, 160], 'alcance_m': 150})


def bumper_cars(M, x, z, yd, r):
    """pavilhao dos carrinhos de bate-bate: pista, cobertura em arco com lampadas, carrinhos coloridos"""
    M.at(x, z, 'orla'); M.m('liso')
    M.box(x - 11, x + 11, yd, yd + 0.25, z - 8, z + 8, (60, 64, 72))
    M.box(x - 11.2, x + 11.2, yd + 0.25, yd + 0.85, z - 8.2, z - 7.9, (250, 196, 40)); M.box(x - 11.2, x + 11.2, yd + 0.25, yd + 0.85, z + 7.9, z + 8.2, (250, 196, 40))
    for (dx, dz) in ((-11, -8), (11, -8), (11, 8), (-11, 8), (0, -8), (0, 8)): M.cyl(x + dx, z + dz, 0.2, yd, yd + 5.0, (230, 60, 60), 8)
    for k in range(12):
        t0, t1 = k / 12, (k + 1) / 12; z0_, z1_ = z - 9 + 18 * t0, z - 9 + 18 * t1
        y0_, y1_ = yd + 5.0 + 1.6 * math.sin(math.pi * t0), yd + 5.0 + 1.6 * math.sin(math.pi * t1)
        M.quad((x - 12, y0_, z0_), (x + 12, y0_, z0_), (x + 12, y1_, z1_), (x - 12, y1_, z1_), (250, 250, 246) if k % 2 else (230, 60, 60), (0, 1, 0))
    for k in range(10):
        cx_, cz_ = x + r.uniform(-9, 9), z + r.uniform(-6, 6); col = r.choice(COLS)
        M.box(cx_ - 0.9, cx_ + 0.9, yd + 0.25, yd + 0.85, cz_ - 0.6, cz_ + 0.6, col)
        M.cyl(cx_, cz_, 0.04, yd + 0.85, yd + 5.0, (90, 94, 100), 4)
    M.free()


def stage(M, x, z, yd, face):
    """palco com telhado, caixas de som e torre de luz"""
    M.at(x, z, 'orla'); M.m('madeira'); M.box(x - 9, x + 9, yd, yd + 1.2, z - 5, z + 5, (90, 70, 56))
    M.m('metal')
    for dx in (-9, 9):
        for dz in (-5, 5): M.box(x + dx - 0.15, x + dx + 0.15, yd + 1.2, yd + 8.0, z + dz - 0.15, z + dz + 0.15, (50, 54, 60))
    M.box(x - 9.4, x + 9.4, yd + 8.0, yd + 8.6, z - 5.4, z + 5.4, (50, 54, 60))
    M.m('liso')
    for dx in (-7.5, 7.5): M.box(x + dx - 0.8, x + dx + 0.8, yd + 1.2, yd + 3.6, z + face * 3.8 - 0.6, z + face * 3.8 + 0.6, (30, 30, 34))
    M.box(x - 6, x + 6, yd + 1.2, yd + 7.0, z - face * 4.8 - 0.05, z - face * 4.8 + 0.05, (40, 60, 120))
    for k in range(6): M.sphere(x - 7.5 + k * 3.0, yd + 7.8, z + face * 4.8, 0.25, (255, 240, 200), 6, 4)
    M.free()


def food_court(M, pr, x0, x1, z0, z1, yd, r):
    """praca de alimentacao: mesas com guarda-sol listrado entre floreiras"""
    for xx in np.arange(x0 + 3, x1 - 2, 6.0):
        for zz in np.arange(z0 + 3, z1 - 2, 6.0):
            M.at(xx, zz, 'orla'); M.m('liso'); col = r.choice(COLS)
            M.cyl(xx, zz, 0.55, yd + 0.72, yd + 0.78, (250, 250, 248), 10); M.cyl(xx, zz, 0.05, yd, yd + 0.72, (60, 60, 64), 5)
            for k in range(4):
                a = k * math.pi / 2 + 0.4; M.box(xx + math.cos(a) * 0.95 - 0.2, xx + math.cos(a) * 0.95 + 0.2, yd, yd + 0.46, zz + math.sin(a) * 0.95 - 0.2, zz + math.sin(a) * 0.95 + 0.2, (240, 240, 236))
            M.free()
            umbrella(M, xx, zz, col, r, False, y_fix=yd)


def pier(M, pr, px, y, r):
    """PIER DE DIVERSOES (ponto turistico): rampa de acesso desde a mureta subindo ate 4,2 m (da para andar por baixo
    na areia), portal com arco, alameda de barracas, plataforma de 140 x 120 m com roda-gigante gigante, montanha-russa,
    torre de queda livre, carrossel, bate-bate, fliperama, palco, praca de alimentacao, e o braco de pesca de 140 m
    ate o mirante com restaurante na ponta."""
    yd = 4.2; zA = ZW - 0.3
    W1 = 10.0
    zR = zA + 34.0                                               # fim da rampa
    # rampa (tabuleiro em declive, sobre estacas)
    n = 10
    for k in range(n):
        za, zb = zA + (zR - zA) * k / n, zA + (zR - zA) * (k + 1) / n
        ya, yb = y + (yd - y) * k / n, y + (yd - y) * (k + 1) / n
        M.at(px, (za + zb) / 2, 'pier'); M.m('madeira')
        M.quad((px - W1, ya, za), (px + W1, ya, za), (px + W1, yb, zb), (px - W1, yb, zb), (176, 140, 104), (0, 1, 0))
        M.quad((px + W1, ya - 0.45, za), (px - W1, ya - 0.45, za), (px - W1, yb - 0.45, zb), (px + W1, yb - 0.45, zb), (120, 96, 72), (0, -1, 0))
        for s_ in (-1, 1): M.quad((px + s_ * W1, ya - 0.45, za), (px + s_ * W1, yb - 0.45, zb), (px + s_ * W1, yb, zb), (px + s_ * W1, ya, za), (150, 118, 86), (s_, 0, 0))
        M.m('madeira')
        if k % 2 == 1:
            for xx in np.arange(px - W1 + 1, px + W1, 5.0): _pile(M, xx, za, ya)
        M.free()
    PX0, PX1, zP0, zP1 = px - 80.0, px + 60.0, zR + 30.0, zR + 150.0   # plataforma do parque
    zF = zP1 + 140.0                                                 # fim do braco de pesca
    _deck(M, px - W1, px + W1, zR, zP0, yd)
    _deck(M, PX0, PX1, zP0, zP1, yd)
    _deck(M, px - 6, px + 6, zP1, zF, yd)
    _deck(M, px - 22, px + 22, zF, zF + 34, yd)
    outline = [(px - W1, zA), (px - W1, zP0), (PX0, zP0), (PX0, zP1), (px - 6, zP1), (px - 6, zF), (px - 22, zF), (px - 22, zF + 34),
               (px + 22, zF + 34), (px + 22, zF), (px + 6, zF), (px + 6, zP1), (PX1, zP1), (PX1, zP0), (px + W1, zP0), (px + W1, zA)]
    for i in range(len(outline) - 1):
        a_, b_ = outline[i], outline[i + 1]
        if a_[1] < zR + 0.1 and b_[1] < zR + 0.1: continue
        M.at((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2, 'orla'); M.m('liso'); _rail_line(M, [(a_[0], max(a_[1], zR)), (b_[0], max(b_[1], zR))], yd); M.free()
    arch(M, px, zR + 2.0, yd, 2 * W1 - 2.0)
    cols = [(230, 60, 60), (40, 140, 220), (250, 190, 40), (60, 180, 100), (220, 90, 180), (240, 130, 40)]
    for k, z in enumerate(np.arange(zR + 6, zP0 - 4, 7.0)):
        stall_side(M, px - W1 + 2.0, z, yd, cols[k % 6], 1)
        stall_side(M, px + W1 - 2.0, z + 3.5, yd, cols[(k + 3) % 6], -1)
    # postes de globo duplo pelo pier todo
    lamps = [(px + s * (W1 - 0.8), z) for z in np.arange(zR + 4, zP0, 10.0) for s in (-1, 1)]
    lamps += [(px + s * 5.2, z) for z in np.arange(zP1 + 6, zF, 12.0) for s in (-1, 1)]
    lamps += [(xx, zz) for xx in np.arange(PX0 + 2, PX1, 14.0) for zz in (zP0 + 1.5, zP1 - 1.5)]
    for (xx, z) in lamps:
        M.at(xx, z, 'orla'); M.m('metal'); M.cyl(xx, z, 0.09, yd, yd + 4.4, (40, 50, 60), 6, False)
        M.box(xx - 0.5, xx + 0.5, yd + 4.2, yd + 4.3, z - 0.05, z + 0.05, (40, 50, 60))
        M.m('liso'); M.sphere(xx - 0.5, yd + 4.5, z, 0.22, (255, 246, 214), 6, 4); M.sphere(xx + 0.5, yd + 4.5, z, 0.22, (255, 246, 214), 6, 4); M.free()
    # atracoes
    ferris_wheel(M, pr, px + 34, zP1 - 30, yd, r, 26.0, 32)
    coaster(M, PX0 + 4, px - 14, zP0 + 6, zP1 - 6, yd, r, 22.0)
    drop_tower(M, pr, px + 46, zP0 + 18, yd)
    carousel(M, px + 14, zP0 + 16, yd, r)
    bumper_cars(M, px + 18, zP0 + 50, yd, r)
    arcade(M, px - 2, zP1 - 14, yd, r)
    stage(M, px + 6, zP1 - 52, yd, -1)
    food_court(M, pr, px - 10, px + 4, zP0 + 30, zP0 + 70, yd, r)
    for k, (sx, sz) in enumerate(((px - 4, zP0 + 6), (px + 36, zP0 + 4), (px + 50, zP0 + 75), (px - 10, zP1 - 30), (px + 30, zP1 - 6))):
        stall(M, sx, sz, yd, cols[k % 6], 1 if k % 2 == 0 else -1)
    for (bx, bz) in ((px - 8, zP0 + 22), (px + 30, zP0 + 34), (px + 50, zP0 + 98), (px - 8, zP1 - 4), (px + 54, zP0 + 50)):
        planter_pier(M, pr, bx, bz, yd, r)
    for k, z in enumerate(np.arange(zP1 + 10, zF - 4, 12.0)):
        pr.bench(px + 4.6, z, -1, 0, yd); pr.bench(px - 4.6, z + 6, 1, 0, yd)
    # mirante e restaurante na ponta
    rx0, rz0 = px - 14, zF + 6
    M.at(px, zF + 17, 'orla'); M.m('madeira'); M.box(rx0, rx0 + 28, yd, yd + 4.6, rz0, rz0 + 16, (226, 206, 176), top=False)
    M.m('vidro')
    for (x0_, x1_, zf, s_) in ((rx0 + 1, rx0 + 27, rz0, -1), (rx0 + 1, rx0 + 27, rz0 + 16, 1)):
        M.quad((x0_, yd + 1.0, zf + s_ * 0.03), (x1_, yd + 1.0, zf + s_ * 0.03), (x1_, yd + 4.0, zf + s_ * 0.03), (x0_, yd + 4.0, zf + s_ * 0.03), WHITE, (0, 0, s_))
    M.m('telha'); M.quad((rx0 - 1.5, yd + 4.6, rz0 - 1.5), (rx0 + 29.5, yd + 4.6, rz0 - 1.5), (rx0 + 29.5, yd + 7.4, rz0 + 8), (rx0 - 1.5, yd + 7.4, rz0 + 8), (60, 110, 120), (0, 1, -0.4))
    M.quad((rx0 - 1.5, yd + 7.4, rz0 + 8), (rx0 + 29.5, yd + 7.4, rz0 + 8), (rx0 + 29.5, yd + 4.6, rz0 + 17.5), (rx0 - 1.5, yd + 4.6, rz0 + 17.5), (60, 110, 120), (0, 1, 0.4))
    M.m('madeira')
    for s_ in (-1, 1): M.tri((rx0 + (0 if s_ < 0 else 28), yd + 4.6, rz0 - 1.5), (rx0 + (0 if s_ < 0 else 28), yd + 4.6, rz0 + 17.5), (rx0 + (0 if s_ < 0 else 28), yd + 7.4, rz0 + 8), (226, 206, 176), (s_, 0, 0))
    M.m('liso'); M.box(px - 6, px + 6, yd + 4.8, yd + 6.0, rz0 - 1.6, rz0 - 1.4, (250, 196, 40))
    M.free()
    food_court(M, pr, px - 20, px + 20, zF + 0.5, zF + 5.5, yd, r)


def stall_side(M, x, z, yd, col, face):
    """barraca no acesso, com a frente virada para o meio (eixo x)"""
    M.at(x, z, 'orla'); M.m('reboco'); M.box(x - 1.4, x + 1.4, yd, yd + 2.8, z - 2.0, z + 2.0, (246, 242, 232), top=False)
    M.m('liso'); M.box(x - 1.5, x + 1.5, yd + 2.8, yd + 3.0, z - 2.1, z + 2.1, (240, 238, 232))
    fx = x + face * 1.42
    M.box(fx - 0.02, fx + 0.02, yd + 1.0, yd + 2.3, z - 1.7, z + 1.7, (60, 64, 72))
    M.box(min(fx, fx + face * 0.6), max(fx, fx + face * 0.6), yd + 0.95, yd + 1.05, z - 2.0, z + 2.0, (150, 108, 70))
    for k in range(8):
        za = z - 2.0 + k * 0.5
        M.quad((fx, yd + 2.75, za), (fx, yd + 2.75, za + 0.5), (fx + face * 1.2, yd + 2.35, za + 0.5), (fx + face * 1.2, yd + 2.35, za), col if k % 2 == 0 else (250, 250, 246), (face * 0.5, 0.8, 0))
    M.box(x - 0.05, x + 0.05, yd + 3.0, yd + 3.9, z - 1.8, z + 1.8, col)
    M.free()


def arcade(M, x, z, yd, r):
    """fliperama: galpão com fachada de vidro, letreiro grande e faixa de lâmpadas"""
    M.at(x, z, 'orla'); M.m('reboco'); M.box(x - 9, x + 9, yd, yd + 6.0, z - 5, z + 5, (250, 236, 210), top=False)
    M.m('concreto'); M.box(x - 9.2, x + 9.2, yd + 6.0, yd + 6.4, z - 5.2, z + 5.2, (236, 230, 220))
    M.m('vitrine'); M.quad((x - 7, yd + 0.3, z + 5.03), (x + 7, yd + 0.3, z + 5.03), (x + 7, yd + 3.6, z + 5.03), (x - 7, yd + 3.6, z + 5.03), WHITE, (0, 0, 1), [(0, 1), (5, 1), (5, 0), (0, 0)])
    M.m('liso'); M.box(x - 8, x + 8, yd + 4.0, yd + 5.6, z + 5.0, z + 5.3, (220, 50, 140))
    M.box(x - 7.6, x + 7.6, yd + 4.2, yd + 5.4, z + 5.3, z + 5.4, (250, 230, 60))
    for k in range(24): M.sphere(x - 8.6 + k * 0.75, yd + 6.2, z + 5.3, 0.1, (255, 236, 160), 4, 3)
    M.free()


def planter_pier(M, pr, x, z, yd, r):
    M.at(x, z, 'orla'); M.m('madeira'); M.box(x - 1.5, x + 1.5, yd, yd + 0.7, z - 1.5, z + 1.5, (150, 108, 70))
    M.m('terreno'); M.box(x - 1.35, x + 1.35, yd + 0.6, yd + 0.66, z - 1.35, z + 1.35, (96, 72, 54)); M.free()
    pr.tree(x, z, 'palmeira', r.uniform(0.7, 0.9), yd + 0.66)
    pr.bench(x + 2.4, z, -1, 0, yd); pr.bench(x - 2.4, z, 1, 0, yd)
