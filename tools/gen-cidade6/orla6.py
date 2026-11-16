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
PIER_A, PIER_B = -1e9, -1e9 + 1          # sem pier   # faixa da praia ocupada pela plataforma
COLS = [(230, 70, 60), (40, 120, 200), (245, 200, 40), (60, 170, 120), (244, 244, 244), (240, 130, 40), (200, 80, 160), (30, 160, 170)]


def sand_y(x, z):
    t = min(max((z - ZW) / max(shore_z(x) - ZW, 1.0), 0.0), 1.0)
    return -1.5 - 1.4 * t ** 1.2


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
        for j_, bx in enumerate(np.arange(ca + 15, cb - 10, 30.0)):
            bike_arrow(M, bx, Z0 + 2.9, y + 0.07, 1); bike_arrow(M, bx + 15, Z0 + 1.5, y + 0.07, -1)
        # ------------------------------------------------------------ mureta com aberturas e escadas a cada ~70 m
        gaps = [g for g in np.arange(xa + 35, xb - 22, 70.0) if abs(g - PIER_X) > 16]
        cur = xa
        for g in gaps + [None]:
            end = (g - 3.0) if g is not None else xb
            x = cur
            while x < end:
                x1 = min(x + 20.0, end)
                if False:
                    if x < PIER_X - 10.2: x1 = PIER_X - 10.2
                    else: x = PIER_X + 10.2; continue
                M.at((x + x1) / 2, ZW, 'orla'); M.m('pedra'); M.prism([(x, ZW - 0.25), (x1, ZW - 0.25), (x1, ZW + 0.25), (x, ZW + 0.25)], -2.2, y + 0.5, WHITE, False)
                M.m('concreto'); M.prism([(x, ZW - 0.32), (x1, ZW - 0.32), (x1, ZW + 0.32), (x, ZW + 0.32)], y + 0.5, y + 0.6, (236, 232, 222), True)
                x = x1
            if g is not None:
                stairs(M, pr, g, y); cur = g + 3.0
        px = xb if si == 0 else xa
        M.at(px, ZW, 'orla'); M.m('pedra'); M.prism([(px - 0.6, ZW - 0.6), (px + 0.6, ZW - 0.6), (px + 0.6, ZW + 0.6), (px - 0.6, ZW + 0.6)], -2.2, y + 0.95, WHITE, False)
        M.m('concreto'); M.prism([(px - 0.7, ZW - 0.7), (px + 0.7, ZW - 0.7), (px + 0.7, ZW + 0.7), (px - 0.7, ZW + 0.7)], y + 0.95, y + 1.08, (236, 232, 222), True)
        M.free()
        # ------------------------------------------------------------ calcadao: postes, bancos para o mar, lixeiras, canteiros, bicicletarios,
        # carrinhos de coco, bebedouros, totens; quiosques de dois tipos (nada de coqueiro no meio da calcada)
        kx_list = [kx + (12 if any(abs(kx - g) < 9 for g in gaps) else 0) for kx in np.arange(xa + 60, xb - 40, 115.0)]
        kx_list = [kx for kx in kx_list if abs(kx - PIER_X) > 26]
        busy = [(kx - 11, kx + 11) for kx in kx_list] + []
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
        beach(M, pr, xa, xb, [g for g in np.arange(xa + 35, xb - 22, 70.0)], r)
    bike_bridge(M, pr, spans, y, r)
    jetties_and_lighthouse(M, pr, r)


# ================================================================ pecas novas da orla
def bike_arrow(M, x, z, y, d):
    """seta branca pintada na faixa da ciclovia; d = +1 (para leste) ou -1 (para oeste)"""
    M.at(x, z, 'orla'); M.m('liso'); c = (250, 250, 246)
    M.poly([(x - d * 1.1, y, z - 0.09), (x + d * 0.3, y, z - 0.09), (x + d * 0.3, y, z + 0.09), (x - d * 1.1, y, z + 0.09)], c, (0, 1, 0))
    M.poly([(x + d * 0.2, y, z - 0.42), (x + d * 1.1, y, z), (x + d * 0.2, y, z + 0.42)], c, (0, 1, 0))
    M.free()


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
    for xp in (river_x(zm) - RIVER_W / 4, river_x(zm) + RIVER_W / 4): M.box(xp - 0.5, xp + 0.5, -5.5, yy((xp - xa) / (xb - xa)) - 0.55, za + 0.3, zb - 0.3, (196, 192, 184))
    M.free()
    for t in (0.25, 0.75):
        xx = xa + (xb - xa) * t; M.at(xx, za, 'orla'); M.m('metal'); M.cyl(xx, za + 0.1, 0.06, yy(t), yy(t) + 4.2, (60, 64, 70), 6, False)
        M.m('liso'); M.sphere(xx, yy(t) + 4.4, za + 0.1, 0.26, (255, 246, 214), 6, 4); M.free()


def jetties_and_lighthouse(M, pr, r):
    """molhes: calcadas de concreto sobre enrocamento que comecam no calcadao (no lugar das paredes do cais na areia),
    atravessam a praia e entram no mar ate as plataformas dos farois. Escadas descem do molhe para a areia.
    Farol grande na ponta oeste e farol menor (verde) na leste, ambos com escada externa ate a galeria da lanterna."""
    zsh = shore_z(river_x(1840))
    za, zt = ZW + 0.3, zsh + 84.0
    YT = 0.9
    for sgn in (-1, 1):
        def cx_at(z): return river_x(z) + sgn * (RIVER_W / 2 + RIVER_WALL / 2)
        def w_at(z): return 1.9 + 1.3 * min(max((z - zsh) / (zt - zsh), 0.0), 1.0)
        def y_at(z): return Y_WALK + (YT - Y_WALK) * min((z - za) / 7.0, 1.0)      # rampa saindo do calcadao
        stairs_z = [ZW + 26.0, ZW + 64.0]
        z = za
        k = 0
        while z < zt - 0.01:
            z1 = min(z + 3.0, zt)
            xa_, xb_ = cx_at(z), cx_at(z1); wa, wb = w_at(z), w_at(z1); ya, yb = y_at(z), y_at(z1)
            M.at((xa_ + xb_) / 2, (z + z1) / 2, 'orla')
            # corpo do molhe (laterais de pedra aparelhada) e piso de concreto com juntas
            M.m('pedra')
            for s in (-1, 1):
                M.quad((xa_ + s * wa, -5.5, z), (xb_ + s * wb, -5.5, z1), (xb_ + s * wb, yb - 0.05, z1), (xa_ + s * wa, ya - 0.05, z), (170, 164, 152), (s, 0, 0))
            M.m('concreto')
            M.quad((xa_ - wa + 0.3, ya, z), (xa_ + wa - 0.3, ya, z), (xb_ + wb - 0.3, yb, z1), (xb_ - wb + 0.3, yb, z1), (214, 210, 202), (0, 1, 0))
            M.quad((xa_ - wa + 0.3, ya + 0.004, z), (xa_ + wa - 0.3, ya + 0.004, z), (xa_ + wa - 0.3, ya + 0.004, z + 0.08), (xa_ - wa + 0.3, ya + 0.004, z + 0.08), (176, 172, 164), (0, 1, 0))
            for s in (-1, 1):                                              # meio-fio dos dois lados
                o0, o1 = xa_ + s * (wa - 0.3), xb_ + s * (wb - 0.3); e0, e1 = xa_ + s * wa, xb_ + s * wb
                M.quad((o0, ya + 0.22, z), (e0, ya + 0.22, z), (e1, yb + 0.22, z1), (o1, yb + 0.22, z1), (232, 228, 220), (0, 1, 0))
                M.quad((o0, ya - 0.05, z), (o0, ya + 0.22, z), (o1, yb + 0.22, z1), (o1, yb - 0.05, z1), (222, 218, 210), (-s, 0, 0))
                M.quad((e0, ya - 0.05, z), (e0, ya + 0.22, z), (e1, yb + 0.22, z1), (e1, yb - 0.05, z1), (222, 218, 210), (s, 0, 0))
            # guarda-corpo de tubo galvanizado (aberto onde ha escada)
            M.m('metal'); rc = (196, 200, 206)
            for s in (-1, 1):
                if s == sgn and any(sz_ - 1.6 < (z + z1) / 2 < sz_ + 1.6 for sz_ in stairs_z): continue
                px0, px1 = xa_ + s * (wa - 0.15), xb_ + s * (wb - 0.15)
                for hy in (1.05, 0.6):
                    M.quad((px0, ya + 0.22 + hy - 0.04, z), (px1, yb + 0.22 + hy - 0.04, z1), (px1, yb + 0.22 + hy + 0.04, z1), (px0, ya + 0.22 + hy + 0.04, z), rc, (s, 0, 0))
                    M.quad((px0 - s * 0.05, ya + 0.22 + hy + 0.04, z), (px1 - s * 0.05, yb + 0.22 + hy + 0.04, z1), (px1 + s * 0.05, yb + 0.22 + hy + 0.04, z1), (px0 + s * 0.05, ya + 0.22 + hy + 0.04, z), rc, (0, 1, 0))
                M.box(px0 - 0.05, px0 + 0.05, ya + 0.22, ya + 1.32, z - 0.05, z + 0.05, rc)
            M.free()
            # enrocamento: do lado do rio na agua; do lado de fora meio enterrado na areia (e no mar alem da praia)
            M.at((xa_ + xb_) / 2, (z + z1) / 2, 'orla'); M.m('pedra')
            for s in (-1, 1):
                zz = z + 0.6
                while zz < z1:
                    xx = cx_at(zz) + s * (w_at(zz) + 0.9)
                    inner = (s == -sgn)
                    on_sand = (not inner) and zz < shore_z(xx) - 1.0
                    if on_sand and any(abs(zz - sz_) < 2.2 for sz_ in stairs_z): zz += 1.5; continue
                    base = (sand_y(xx, zz) - 0.35) if on_sand else Y_SEA
                    for j in range(2 if not on_sand else 1):
                        rx_ = xx + s * j * 1.3 + r.uniform(-0.25, 0.25)
                        M.sphere(rx_, base + (0.35 if j == 0 else -0.2) + r.uniform(-0.15, 0.15), zz + r.uniform(-0.4, 0.4), r.uniform(0.8, 1.25) * (0.8 if on_sand else 1.0),
                                 r.choice(((150, 146, 138), (128, 124, 118), (170, 164, 152), (138, 132, 120))), 6, 3, 0.7, 0.18, r)
                    zz += 1.5
            M.free()
            # postes a cada ~24 m e bancos
            zm = (z + z1) / 2
            if k % 8 == 4: classic_lamp(M, cx_at(zm) - sgn * (w_at(zm) - 0.5), zm, y_at(zm) + 0.0); pr.luzes.append({'tipo': 'poste', 'x': round(cx_at(zm), 1), 'y': round(y_at(zm) + 4.4, 2), 'z': round(zm, 1), 'cor': [255, 230, 180], 'alcance_m': 14})
            if k % 10 == 7 and zm > zsh:
                bx = cx_at(zm) + sgn * (w_at(zm) - 0.9)
                M.at(bx, zm, 'orla'); M.m('madeira'); M.box(bx - 0.25, bx + 0.25, YT + 0.42, YT + 0.5, zm - 0.9, zm + 0.9, (150, 108, 70))
                M.box(bx + sgn * 0.22 - 0.04, bx + sgn * 0.22 + 0.04, YT + 0.5, YT + 0.95, zm - 0.9, zm + 0.9, (150, 108, 70))
                M.m('metal'); [M.box(bx - 0.22, bx + 0.22, YT, YT + 0.42, zm + d_ - 0.04, zm + d_ + 0.04, (60, 64, 70)) for d_ in (-0.75, 0.75)]; M.free()
            z = z1; k += 1
        # escadas do molhe para a areia (lado de fora)
        for sz_ in stairs_z:
            if sz_ > shore_z(cx_at(sz_)) - 8: continue
            e = cx_at(sz_) + sgn * w_at(sz_); yy = YT + 0.22; n = 0
            M.at(e, sz_, 'orla'); M.m('concreto')
            while True:
                xe = e + sgn * 0.34 * n; ytop = yy - 0.2 * (n + 1)
                ground = sand_y(xe + sgn * 0.17, sz_)
                if ytop < ground - 0.02: break
                xa2, xb2 = sorted((xe, xe + sgn * 0.34))
                M.box(xa2, xb2, ground - 0.4, ytop, sz_ - 1.2, sz_ + 1.2, (220, 216, 206))
                n += 1
            M.m('metal')
            for dz in (-1.25, 1.25):
                x_end = e + sgn * 0.34 * n
                M.quad((e, yy + 0.95, sz_ + dz - 0.03), (x_end, yy - 0.2 * n + 0.95, sz_ + dz - 0.03), (x_end, yy - 0.2 * n + 1.03, sz_ + dz + 0.03), (e, yy + 1.03, sz_ + dz + 0.03), (196, 200, 206), (0, 1, 0))
                for xx in (e, x_end): M.box(xx - 0.04, xx + 0.04, yy - (0.2 * n if xx == x_end else 0) - 0.1, yy - (0.2 * n if xx == x_end else 0) + 1.03, sz_ + dz - 0.04, sz_ + dz + 0.04, (196, 200, 206))
            M.free()
        # plataforma redonda na ponta, com enrocamento, guarda-corpo e entrada vinda do molhe
        cx, cz = cx_at(zt), zt + 7.0
        M.at(cx, cz, 'orla'); M.m('pedra')
        for kk in range(30):
            a = 2 * math.pi * kk / 30; M.sphere(cx + math.cos(a) * 10.4, Y_SEA + 0.4 + r.uniform(-0.2, 0.3), cz + math.sin(a) * 10.4, r.uniform(1.2, 1.7), r.choice(((150, 146, 138), (128, 124, 118), (170, 164, 152))), 6, 3, 0.75, 0.18, r)
        M.cyl(cx, cz, 9.2, -5.5, YT - 0.05, (170, 164, 152), 28, False)
        M.m('concreto'); M.cyl(cx, cz, 9.0, YT - 0.05, YT, (214, 210, 202), 28)
        M.cyl(cx, cz, 9.25, YT, YT + 0.22, (232, 228, 220), 28, False)
        M.prism([(cx - w_at(zt), zt - 0.5), (cx + w_at(zt), zt - 0.5), (cx + w_at(zt), cz - 7.5), (cx - w_at(zt), cz - 7.5)], -5.5, YT, (214, 210, 202))
        M.m('metal')
        for kk in range(32):
            a0, a1 = 2 * math.pi * kk / 32, 2 * math.pi * (kk + 1) / 32
            if math.sin((a0 + a1) / 2) < -0.9: continue
            p0 = (cx + math.cos(a0) * 9.05, cz + math.sin(a0) * 9.05); p1 = (cx + math.cos(a1) * 9.05, cz + math.sin(a1) * 9.05)
            for hy in (0.82, 1.27): M.quad((p0[0], YT + hy - 0.04, p0[1]), (p1[0], YT + hy - 0.04, p1[1]), (p1[0], YT + hy + 0.04, p1[1]), (p0[0], YT + hy + 0.04, p0[1]), (196, 200, 206), (math.cos(a0), 0, math.sin(a0)))
            M.box(p0[0] - 0.05, p0[0] + 0.05, YT + 0.22, YT + 1.31, p0[1] - 0.05, p0[1] + 0.05, (196, 200, 206))
        M.free()
        for kk in range(3):                                              # cabecos de amarracao
            a = math.pi * (0.25 + 0.25 * kk); bx, bz = cx + math.cos(a) * 7.8, cz + math.sin(a) * 7.8
            M.at(bx, bz, 'orla'); M.m('metal'); M.cyl(bx, bz, 0.22, YT, YT + 0.5, (40, 44, 50), 8); M.cyl(bx, bz, 0.3, YT + 0.5, YT + 0.6, (40, 44, 50), 8); M.free()
        if sgn < 0: lighthouse(M, pr, cx, cz, YT, r, 34.0, (196, 40, 36), 3.6, 2.2, True)
        else: lighthouse(M, pr, cx, cz, YT, r, 16.0, (40, 140, 80), 2.0, 1.4, False)


def lighthouse(M, pr, x, z, y0, r, H, band, R0, R1, big):
    """farol: embasamento octogonal com degraus, torre conica em faixas, porta com marquise, janelas com moldura,
    escada helicoidal externa de aco (com guarda-corpo) da porta ate a galeria, galeria com piso andavel e guarda-corpo,
    lanterna com montantes, lente de Fresnel e lampada, cupula com respiro e para-raios."""
    M.at(x, z, 'orla')
    M.m('concreto')
    for kk in range(3): M.cyl(x, z, R0 + 2.4 - kk * 0.6, y0 + kk * 0.2, y0 + (kk + 1) * 0.2, (226, 222, 212), 8)
    yb = y0 + 0.6
    M.m('pedra'); M.cyl(x, z, R0 + 0.35, yb, yb + 1.4, (180, 172, 158), 20)
    nb = 7 if big else 4
    Hb = H - 1.4
    for kk in range(nb):
        t0, t1 = kk / nb, (kk + 1) / nb
        M.m('reboco'); M.cyl(x, z, R0 + (R1 - R0) * t0, yb + 1.4 + Hb * t0, yb + 1.4 + Hb * t1, (242, 240, 234) if kk % 2 == 0 else band, 24, False, R0 + (R1 - R0) * t1)
    yt = yb + H
    rad = lambda yy: R0 + (R1 - R0) * min(max((yy - yb - 1.4) / Hb, 0.0), 1.0)
    # porta (virada para o molhe, -z) com moldura e marquise
    a = -math.pi / 2; nx_, nz_ = math.cos(a), math.sin(a)
    dx_, dz_ = nx_ * (R0 + 0.38), nz_ * (R0 + 0.38)
    M.m('liso')
    M.quad((x + dx_ - 0.75, yb, z + dz_ - 0.01), (x + dx_ + 0.75, yb, z + dz_ - 0.01), (x + dx_ + 0.75, yb + 2.7, z + dz_ - 0.01), (x + dx_ - 0.75, yb + 2.7, z + dz_ - 0.01), (240, 238, 232), (0, 0, -1))
    M.quad((x + dx_ - 0.55, yb, z + dz_ - 0.03), (x + dx_ + 0.55, yb, z + dz_ - 0.03), (x + dx_ + 0.55, yb + 2.45, z + dz_ - 0.03), (x + dx_ - 0.55, yb + 2.45, z + dz_ - 0.03), (54, 84, 70), (0, 0, -1))
    M.box(x + dx_ - 0.9, x + dx_ + 0.9, yb + 2.75, yb + 2.85, z + dz_ - 1.0, z + dz_, (90, 94, 100))
    M.sphere(x + dx_ + 0.45, yb + 1.25, z + dz_ - 0.06, 0.05, (210, 180, 60), 4, 2)
    # janelas com moldura subindo pela torre
    nw = 6 if big else 2
    for kk in range(nw):
        aa = kk * 2.4 + 1.2; yy = yb + 5 + kk * (Hb - 8) / max(nw - 1, 1); rr = rad(yy) + 0.04
        wx, wz = x + math.cos(aa) * rr, z + math.sin(aa) * rr; tx_, tz_ = -math.sin(aa), math.cos(aa); nn = (math.cos(aa), 0, math.sin(aa))
        M.quad((wx - tx_ * 0.5, yy - 0.15, wz - tz_ * 0.5), (wx + tx_ * 0.5, yy - 0.15, wz + tz_ * 0.5), (wx + tx_ * 0.5, yy + 1.25, wz + tz_ * 0.5), (wx - tx_ * 0.5, yy + 1.25, wz - tz_ * 0.5), (236, 234, 228), nn)
        wx2, wz2 = wx + nn[0] * 0.02, wz + nn[2] * 0.02
        M.quad((wx2 - tx_ * 0.35, yy, wz2 - tz_ * 0.35), (wx2 + tx_ * 0.35, yy, wz2 + tz_ * 0.35), (wx2 + tx_ * 0.35, yy + 1.0, wz2 + tz_ * 0.35), (wx2 - tx_ * 0.35, yy + 1.0, wz2 - tz_ * 0.35), (40, 52, 66), nn)
    # escada helicoidal externa: degraus de chapa, coluna de apoio e guarda-corpo do lado de fora
    M.m('metal'); sc = (70, 76, 84)
    rise = 0.22; nst = int((yt - yb) / rise); turns = max(2.0, H / 11.0)
    a0 = -math.pi / 2 + 0.55
    prev = None
    for kk in range(nst):
        yy = yb + rise * (kk + 1); aa = a0 + 2 * math.pi * turns * kk / nst; da = 2 * math.pi * turns / nst * 1.15
        ri = rad(yy) + 0.05; ro = ri + 1.0
        c0, s0, c1, s1 = math.cos(aa), math.sin(aa), math.cos(aa + da), math.sin(aa + da)
        tread = [(x + c0 * ri, z + s0 * ri), (x + c0 * ro, z + s0 * ro), (x + c1 * ro, z + s1 * ro), (x + c1 * ri, z + s1 * ri)]
        M.prism(tread, yy - 0.05, yy, sc)
        px, pz = x + c0 * (ro - 0.05), z + s0 * (ro - 0.05)
        if kk % 3 == 0: M.box(px - 0.03, px + 0.03, yy, yy + 1.0, pz - 0.03, pz + 0.03, sc)
        if kk % 6 == 0: M.box(px - 0.04, px + 0.04, yy - 0.05 - 1.3, yy - 0.05, pz - 0.04, pz + 0.04, sc)        # mao-francesa
        if prev:
            (qx, qy, qz) = prev
            M.quad((qx, qy + 0.96, qz), (px, yy + 0.96, pz), (px, yy + 1.04, pz), (qx, qy + 1.04, qz), sc, (c0, 0, s0))
            M.quad((qx, qy + 0.5, qz), (px, yy + 0.5, pz), (px, yy + 0.55, pz), (qx, qy + 0.55, qz), sc, (c0, 0, s0))
        prev = (px, yy, pz)
    # galeria (piso andavel no 'pier' = andar de cima do jogo) com guarda-corpo
    M.free(); M.at(x, z, 'pier'); M.m('concreto')
    M.cyl(x, z, R1 + 1.5, yt - 0.35, yt, (230, 226, 218), 24)
    M.free(); M.at(x, z, 'orla'); M.m('concreto')
    for kk in range(12):                                                 # misulas sob a galeria
        aa = 2 * math.pi * kk / 12; bx, bz = x + math.cos(aa) * (R1 + 0.6), z + math.sin(aa) * (R1 + 0.6)
        M.box(bx - 0.15, bx + 0.15, yt - 1.0, yt - 0.35, bz - 0.15, bz + 0.15, (226, 222, 212))
    M.m('metal')
    for kk in range(36):
        b0, b1 = 2 * math.pi * kk / 36, 2 * math.pi * (kk + 1) / 36; rr = R1 + 1.4
        p0 = (x + math.cos(b0) * rr, z + math.sin(b0) * rr); p1 = (x + math.cos(b1) * rr, z + math.sin(b1) * rr)
        for hy in (0.55, 1.1): M.quad((p0[0], yt + hy - 0.04, p0[1]), (p1[0], yt + hy - 0.04, p1[1]), (p1[0], yt + hy + 0.04, p1[1]), (p0[0], yt + hy + 0.04, p0[1]), (40, 44, 50), (math.cos(b0), 0, math.sin(b0)))
        M.box(p0[0] - 0.04, p0[0] + 0.04, yt, yt + 1.14, p0[1] - 0.04, p0[1] + 0.04, (40, 44, 50))
    # lanterna
    RL = R1 - 0.25
    M.m('reboco'); M.cyl(x, z, RL + 0.1, yt, yt + 1.0, band, 16)
    M.m('vidro'); M.cyl(x, z, RL, yt + 1.0, yt + 3.6, (210, 236, 246), 16, False)
    M.m('metal')
    for kk in range(10):
        aa = 2 * math.pi * kk / 10; mx, mz = x + math.cos(aa) * RL, z + math.sin(aa) * RL
        M.box(mx - 0.05, mx + 0.05, yt + 1.0, yt + 3.6, mz - 0.05, mz + 0.05, (40, 44, 50))
    for hy in (1.9, 2.75): M.cyl(x, z, RL + 0.02, yt + hy, yt + hy + 0.05, (40, 44, 50), 16, False)
    M.m('liso')
    M.cyl(x, z, 0.25, yt + 1.0, yt + 1.9, (60, 60, 64), 8)
    for kk in range(4): M.cyl(x, z, 0.55 - kk * 0.03, yt + 1.95 + kk * 0.3, yt + 2.2 + kk * 0.3, (250, 236, 170), 12, False)       # lente de Fresnel
    M.sphere(x, yt + 2.4, z, 0.4, (255, 244, 190), 10, 6)
    M.m('reboco'); M.cyl(x, z, RL + 0.25, yt + 3.6, yt + 3.8, band, 16); M.cyl(x, z, RL + 0.15, yt + 3.8, yt + 5.0, band, 16, False, 0.3)
    M.m('metal'); M.sphere(x, yt + 5.15, z, 0.3, (40, 44, 50), 6, 4); M.cyl(x, z, 0.04, yt + 5.3, yt + 6.8, (40, 44, 50), 5, False)
    M.box(x - 0.5, x + 0.5, yt + 6.2, yt + 6.26, z - 0.03, z + 0.03, (40, 44, 50))
    M.free()
    if big:
        # casa do faroleiro ao lado
        hx, hz = x + 5.4, z + 1.0
        M.at(hx, hz, 'orla')
        M.m('reboco'); M.box(hx - 2.0, hx + 2.0, y0, y0 + 3.0, hz - 2.6, hz + 2.6, (244, 242, 236), top=False)
        M.m('telha'); M.quad((hx - 2.3, y0 + 3.0, hz - 2.9), (hx - 2.3, y0 + 3.0, hz + 2.9), (hx, y0 + 4.4, hz + 2.9), (hx, y0 + 4.4, hz - 2.9), (180, 70, 50), (-0.5, 0.85, 0))
        M.quad((hx, y0 + 4.4, hz - 2.9), (hx, y0 + 4.4, hz + 2.9), (hx + 2.3, y0 + 3.0, hz + 2.9), (hx + 2.3, y0 + 3.0, hz - 2.9), (180, 70, 50), (0.5, 0.85, 0))
        M.m('reboco')
        for s in (-1, 1): M.tri((hx - 2.0, y0 + 3.0, hz + s * 2.6), (hx + 2.0, y0 + 3.0, hz + s * 2.6), (hx, y0 + 4.4, hz + s * 2.6), (244, 242, 236), (0, 0, s))
        M.m('liso')
        M.quad((hx - 0.5, y0, hz - 2.64), (hx + 0.5, y0, hz - 2.64), (hx + 0.5, y0 + 2.1, hz - 2.64), (hx - 0.5, y0 + 2.1, hz - 2.64), (60, 80, 70), (0, 0, -1))
        for s in (-1, 1): M.quad((hx + 2.04, y0 + 1.1, hz + s * 1.2 - 0.5), (hx + 2.04, y0 + 1.1, hz + s * 1.2 + 0.5), (hx + 2.04, y0 + 2.1, hz + s * 1.2 + 0.5), (hx + 2.04, y0 + 2.1, hz + s * 1.2 - 0.5), (40, 50, 62), (1, 0, 0))
        M.free()
        pr.luzes.append({'tipo': 'farol', 'x': round(x, 2), 'y': round(yt + 2.4, 2), 'z': round(z, 2), 'cor': [255, 244, 190], 'alcance_m': 900, 'giro_s': 12.0})
    else:
        pr.luzes.append({'tipo': 'farolete', 'x': round(x, 2), 'y': round(yt + 2.4, 2), 'z': round(z, 2), 'cor': [140, 255, 160], 'alcance_m': 300, 'pisca_s': 3.0})


def stairs(M, pr, x, y):
    """abertura na mureta: escadaria de concreto do calcadao ate a areia (degraus de 17 cm), muretas laterais com
    corrimao e chuveiro ao lado"""
    M.at(x, ZW, 'orla'); M.m('concreto')
    k = 0; ys = y
    while True:
        top = y - 0.17 * (k + 1); z0 = ZW - 0.3 + 0.32 * k
        if top < sand_y(x, z0 + 0.32) - 0.02: break
        M.box(x - 3.0, x + 3.0, -2.2, top, z0, z0 + 0.32, (226, 222, 212)); k += 1
    zE = ZW - 0.3 + 0.32 * k
    for s_ in (-1, 1):
        M.prism([(x + s_ * 3.0 - 0.2, ZW - 0.3), (x + s_ * 3.0 + 0.2, ZW - 0.3), (x + s_ * 3.0 + 0.2, zE), (x + s_ * 3.0 - 0.2, zE)], -2.2, y + 0.6, (236, 232, 222))
    M.m('metal')
    for s_ in (-1, 1):
        hx = x + s_ * 2.7; yt0, yt1 = y + 0.9, y - 0.17 * k + 0.9
        M.quad((hx - 0.04, yt0, ZW - 0.2), (hx + 0.04, yt0, ZW - 0.2), (hx + 0.04, yt1, zE), (hx - 0.04, yt1, zE), (200, 204, 208), (0, 1, 0))
        for (zz, yy) in ((ZW - 0.2, y), (zE - 0.2, y - 0.17 * k)): M.box(hx - 0.04, hx + 0.04, yy, yy + 0.92, zz - 0.04, zz + 0.04, (200, 204, 208))
    sx = x + 4.2; sz_ = zE + 1.0                                       # chuveiro (na areia, ao pe da escada)
    M.cyl(sx, sz_, 0.05, sand_y(sx, sz_), sand_y(sx, sz_) + 2.3, (200, 204, 208), 5, False)
    M.box(sx - 0.05, sx + 0.05, sand_y(sx, sz_) + 2.25, sand_y(sx, sz_) + 2.35, sz_, sz_ + 0.5, (200, 204, 208)); M.cyl(sx, sz_ + 0.5, 0.12, sand_y(sx, sz_) + 2.15, sand_y(sx, sz_) + 2.25, (220, 224, 228), 6)
    M.m('concreto'); M.cyl(sx, sz_ + 0.3, 0.8, sand_y(sx, sz_) - 0.2, sand_y(sx, sz_) + 0.06, (226, 222, 212), 8)
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
        xs_ = list(np.arange(x0 + 1, x1, 5.0))
        for zp in np.arange(z + 1, zz, 6.0):
            for xx in xs_: _pile(M, xx, zp, yd)
            for a_, b_ in zip(xs_[:-1], xs_[1:]):                     # contraventamento em X entre as estacas
                hb = min(G_h((a_ + b_) / 2, zp), -0.4) + 0.3; ht = yd - 0.6
                if ht - hb < 1.0: continue
                for (p0, p1) in (((a_, hb), (b_, ht)), ((a_, ht), (b_, hb))):
                    M.quad((p0[0], p0[1] - 0.09, zp), (p1[0], p1[1] - 0.09, zp), (p1[0], p1[1] + 0.09, zp), (p0[0], p0[1] + 0.09, zp), (104, 82, 62), (0, 0, 1))
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


def hippodrome(M, x0, x1, z0, z1, yd):
    """predio historico do carrossel: alvenaria creme, janelas em arco, torreoes de canto com cupula e telhado em
    pavilhao com lanternim"""
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; H = 7.5
    M.at(cx, cz, 'orla'); M.m('reboco'); M.box(x0, x1, yd, yd + H, z0, z1, (238, 226, 196), top=False)
    M.m('liso')
    for (fx0, fx1, fz, s_) in ((x0, x1, z0, -1), (x0, x1, z1, 1)):
        n = int((fx1 - fx0) / 3.2)
        for k in range(n):
            u = fx0 + 1.4 + k * 3.2
            M.quad((u, yd + 2.0, fz + s_ * 0.03), (u + 1.6, yd + 2.0, fz + s_ * 0.03), (u + 1.6, yd + 5.0, fz + s_ * 0.03), (u, yd + 5.0, fz + s_ * 0.03), (52, 64, 80), (0, 0, s_))
            for j in range(4):                                       # arco da janela
                a0, a1 = math.pi * j / 4, math.pi * (j + 1) / 4
                M.tri((u + 0.8, yd + 5.0, fz + s_ * 0.03), (u + 0.8 - math.cos(a0) * 0.8, yd + 5.0 + math.sin(a0) * 0.6, fz + s_ * 0.03), (u + 0.8 - math.cos(a1) * 0.8, yd + 5.0 + math.sin(a1) * 0.6, fz + s_ * 0.03), (52, 64, 80), (0, 0, s_))
    M.box(x0 - 0.2, x1 + 0.2, yd + H - 0.4, yd + H, z0 - 0.2, z1 + 0.2, (200, 70, 50))
    M.m('telha'); rh = 4.0
    M.quad((x0 - 0.3, yd + H, z0 - 0.3), (x1 + 0.3, yd + H, z0 - 0.3), (cx + 3, yd + H + rh, cz - 2), (cx - 3, yd + H + rh, cz - 2), (150, 70, 56), (0, 0.8, -0.6))
    M.quad((x1 + 0.3, yd + H, z1 + 0.3), (x0 - 0.3, yd + H, z1 + 0.3), (cx - 3, yd + H + rh, cz + 2), (cx + 3, yd + H + rh, cz + 2), (150, 70, 56), (0, 0.8, 0.6))
    M.quad((x0 - 0.3, yd + H, z1 + 0.3), (x0 - 0.3, yd + H, z0 - 0.3), (cx - 3, yd + H + rh, cz - 2), (cx - 3, yd + H + rh, cz + 2), (150, 70, 56), (-0.6, 0.8, 0))
    M.quad((x1 + 0.3, yd + H, z0 - 0.3), (x1 + 0.3, yd + H, z1 + 0.3), (cx + 3, yd + H + rh, cz + 2), (cx + 3, yd + H + rh, cz - 2), (150, 70, 56), (0.6, 0.8, 0))
    M.m('reboco'); M.box(cx - 3, cx + 3, yd + H + rh, yd + H + rh + 1.4, cz - 2, cz + 2, (238, 226, 196), top=False)
    M.m('telha'); M.quad((cx - 3.3, yd + H + rh + 1.4, cz - 2.3), (cx + 3.3, yd + H + rh + 1.4, cz - 2.3), (cx + 3.3, yd + H + rh + 1.4, cz + 2.3), (cx - 3.3, yd + H + rh + 1.4, cz + 2.3), (150, 70, 56), (0, 1, 0))
    for (tx, tz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        M.m('reboco'); M.box(tx - 1.6, tx + 1.6, yd, yd + H + 3.0, tz - 1.6, tz + 1.6, (238, 226, 196), top=False)
        M.m('telha'); M.cyl(tx, tz, 2.0, yd + H + 3.0, yd + H + 5.6, (150, 70, 56), 8, False, 0.05)
        M.m('liso'); M.cyl(tx, tz, 0.05, yd + H + 5.6, yd + H + 7.0, (220, 200, 120), 4, False)
    M.free()


def shop_cottage(M, x, z, yd, face, w, r):
    """loja de pier: casinha de madeira com empena para o deck, vitrine, toldo e letreiro"""
    wall = r.choice(((246, 240, 224), (214, 232, 236), (244, 222, 210), (226, 240, 216), (250, 236, 196)))
    M.at(x, z, 'orla'); M.m('siding'); d = 7.0
    zb = z - face * d / 2
    M.box(x - w / 2, x + w / 2, yd, yd + 3.4, zb - d / 2, zb + d / 2, wall, top=False)
    M.m('telha'); rc = r.choice(((120, 60, 50), (60, 90, 110), (70, 80, 70)))
    for s_ in (-1, 1):
        M.quad((x + s_ * (w / 2 + 0.3), yd + 3.4, zb - d / 2 - 0.3), (x, yd + 5.4, zb - d / 2 - 0.3), (x, yd + 5.4, zb + d / 2 + 0.3), (x + s_ * (w / 2 + 0.3), yd + 3.4, zb + d / 2 + 0.3), rc, (s_ * 0.6, 0.8, 0))
    M.m('siding')
    for zf in (zb - d / 2, zb + d / 2): M.tri((x - w / 2, yd + 3.4, zf), (x + w / 2, yd + 3.4, zf), (x, yd + 5.4, zf), wall, (0, 0, face))
    zf = z + 0.03 * face
    M.m('vitrine'); M.quad((x - w / 2 + 0.6, yd + 0.4, zf), (x + w / 2 - 0.6, yd + 0.4, zf), (x + w / 2 - 0.6, yd + 2.6, zf), (x - w / 2 + 0.6, yd + 2.6, zf), WHITE, (0, 0, face), [(0, 1), (2, 1), (2, 0), (0, 0)])
    M.m('liso'); ac = r.choice(COLS)
    for k in range(int(w / 0.6)):
        xa = x - w / 2 + k * 0.6
        M.quad((xa, yd + 3.0, zf), (xa + 0.6, yd + 3.0, zf), (xa + 0.6, yd + 2.6, zf + face * 1.1), (xa, yd + 2.6, zf + face * 1.1), ac if k % 2 == 0 else (250, 250, 246), (0, 0.8, face * 0.5))
    M.box(x - w * 0.3, x + w * 0.3, yd + 3.5, yd + 4.2, zf + face * 0.02, zf + face * 0.12, ac) if face > 0 else M.box(x - w * 0.3, x + w * 0.3, yd + 3.5, yd + 4.2, zf - 0.12, zf - 0.02, ac)
    M.free()


def swing_ship(M, x, z, yd):
    """barco pirata (balanco): cavalete em A, barco em arco"""
    M.at(x, z, 'orla'); M.m('metal')
    for s_ in (-1, 1):
        M.quad((x - 5, yd, z + s_ * 3), (x - 4.6, yd, z + s_ * 3), (x + 0.2, yd + 11, z + s_ * 1.6), (x - 0.2, yd + 11, z + s_ * 1.6), (250, 196, 40), (0, 0, s_))
        M.quad((x + 4.6, yd, z + s_ * 3), (x + 5, yd, z + s_ * 3), (x + 0.2, yd + 11, z + s_ * 1.6), (x - 0.2, yd + 11, z + s_ * 1.6), (250, 196, 40), (0, 0, s_))
    M.box(x - 0.3, x + 0.3, yd + 10.8, yd + 11.3, z - 1.8, z + 1.8, (250, 196, 40))
    M.m('madeira')
    for k in range(12):
        t0, t1 = k / 12, (k + 1) / 12
        x0_, x1_ = x - 7 + 14 * t0, x - 7 + 14 * t1
        y0_, y1_ = yd + 2.2 + 1.6 * (2 * t0 - 1) ** 2, yd + 2.2 + 1.6 * (2 * t1 - 1) ** 2
        M.quad((x0_, y0_, z - 1.3), (x1_, y1_, z - 1.3), (x1_, y1_ + 1.3, z - 1.3), (x0_, y0_ + 1.3, z - 1.3), (150, 60, 40), (0, 0, -1))
        M.quad((x1_, y1_, z + 1.3), (x0_, y0_, z + 1.3), (x0_, y0_ + 1.3, z + 1.3), (x1_, y1_ + 1.3, z + 1.3), (150, 60, 40), (0, 0, 1))
        M.quad((x0_, y0_, z + 1.3), (x1_, y1_, z + 1.3), (x1_, y1_, z - 1.3), (x0_, y0_, z - 1.3), (110, 50, 36), (0, -1, 0))
    M.m('metal')
    for s_ in (-0.9, 0.9): M.quad((x - 0.1, yd + 11, z + s_), (x + 0.1, yd + 11, z + s_), (x + 0.1, yd + 3.4, z + s_), (x - 0.1, yd + 3.4, z + s_), (80, 84, 90), (0, 0, 1))
    M.free()


def scrambler(M, x, z, yd, r):
    """brinquedo giratorio: base, mastro central, 3 bracos com 4 carrinhos cada, toldo listrado"""
    M.at(x, z, 'orla'); M.m('concreto'); M.cyl(x, z, 7.5, yd, yd + 0.3, (220, 216, 208), 16)
    M.m('metal'); M.cyl(x, z, 0.4, yd + 0.3, yd + 3.0, (230, 60, 60), 8)
    for k in range(3):
        a = 2 * math.pi * k / 3; ex, ez = x + math.cos(a) * 4.0, z + math.sin(a) * 4.0
        M.box(min(x, ex) - 0.15, max(x, ex) + 0.15, yd + 2.6, yd + 2.9, min(z, ez) - 0.15, max(z, ez) + 0.15, (250, 196, 40))
        for j in range(4):
            b = a + j * math.pi / 2; cx_, cz_ = ex + math.cos(b) * 2.0, ez + math.sin(b) * 2.0
            M.m('liso'); M.box(cx_ - 0.7, cx_ + 0.7, yd + 0.4, yd + 1.3, cz_ - 0.5, cz_ + 0.5, COLS[(k * 4 + j) % len(COLS)]); M.m('metal')
    M.m('liso')
    for k in range(12):
        a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
        M.tri((x, yd + 5.0, z), (x + math.cos(a1) * 3, yd + 3.4, z + math.sin(a1) * 3), (x + math.cos(a0) * 3, yd + 3.4, z + math.sin(a0) * 3), (230, 60, 60) if k % 2 else (250, 250, 246), (0, 1, 0))
    M.free()


def park_gate(M, x, z, yd, w):
    """portico do parque de diversoes (vermelho e amarelo, com estrelas de lampadas)"""
    M.at(x, z, 'orla'); M.m('liso')
    for s_ in (-1, 1): M.box(x - 0.6, x + 0.6, yd, yd + 7.5, z + s_ * w / 2 - 0.6, z + s_ * w / 2 + 0.6, (220, 50, 50))
    M.box(x - 0.8, x + 0.8, yd + 6.0, yd + 8.4, z - w / 2 - 0.8, z + w / 2 + 0.8, (250, 196, 40))
    M.box(x - 0.85, x + 0.85, yd + 6.3, yd + 8.1, z - w / 2 + 0.4, z + w / 2 - 0.4, (220, 50, 50))
    for k in range(14): M.sphere(x - 0.9, yd + 8.6, z - w / 2 + k * w / 13, 0.18, (255, 236, 160), 4, 3)
    M.free()


def classic_lamp(M, x, z, yd):
    M.at(x, z, 'orla'); M.m('metal'); M.cyl(x, z, 0.18, yd, yd + 0.6, (30, 40, 50), 8); M.cyl(x, z, 0.08, yd + 0.6, yd + 4.2, (30, 40, 50), 6, False)
    M.box(x - 0.55, x + 0.55, yd + 4.0, yd + 4.1, z - 0.05, z + 0.05, (30, 40, 50))
    M.m('liso')
    for s_ in (-0.55, 0.55): M.sphere(x + s_, yd + 4.35, z, 0.24, (255, 246, 214), 6, 4)
    M.sphere(x, yd + 4.55, z, 0.24, (255, 246, 214), 6, 4)
    M.free()


def pier(M, pr, px, y, r):
    """PIER no estilo do pier de Santa Monica: portal em arco iluminado na entrada, tabuleiro comprido de madeira sobre
    estacas contraventadas (alto: passa-se por baixo na areia), predio historico do carrossel, fileira de lojinhas,
    parque de diversoes ao lado (portico, roda-gigante, montanha-russa contornando o parque, barco pirata, giratorio,
    fliperama, barracas) e na ponta o restaurante de dois andares, a capitania e a area de pesca."""
    yd = 4.2; zA = ZW - 0.3; HW = 11.0
    zR = zA + 34.0
    n = 10
    for k in range(n):
        za, zb = zA + (zR - zA) * k / n, zA + (zR - zA) * (k + 1) / n
        ya, yb = y + (yd - y) * k / n, y + (yd - y) * (k + 1) / n
        M.at(px, (za + zb) / 2, 'pier'); M.m('madeira')
        M.quad((px - HW, ya, za), (px + HW, ya, za), (px + HW, yb, zb), (px - HW, yb, zb), (176, 140, 104), (0, 1, 0))
        M.quad((px + HW, ya - 0.45, za), (px - HW, ya - 0.45, za), (px - HW, yb - 0.45, zb), (px + HW, yb - 0.45, zb), (120, 96, 72), (0, -1, 0))
        for s_ in (-1, 1): M.quad((px + s_ * HW, ya - 0.45, za), (px + s_ * HW, yb - 0.45, zb), (px + s_ * HW, yb, zb), (px + s_ * HW, ya, za), (150, 118, 86), (s_, 0, 0))
        M.m('madeira')
        if k % 2 == 1:
            for xx in np.arange(px - HW + 1, px + HW, 5.0): _pile(M, xx, za, ya)
        M.free()
    zE = zR + 300.0                                                  # comeco da cabeca do pier
    PK0, PK1, PZ0, PZ1 = px + HW, px + HW + 72.0, zR + 50.0, zR + 190.0   # parque de diversoes (lado leste)
    SH0 = px - HW - 12.0                                               # fileira de lojas (lado oeste)
    _deck(M, px - HW, px + HW, zR, zE, yd)
    _deck(M, PK0, PK1, PZ0, PZ1, yd)
    _deck(M, px - HW - 30, px - HW, zR + 6, zR + 34, yd)               # carrossel
    _deck(M, SH0, px - HW, zR + 50, zR + 180, yd)                      # lojas
    _deck(M, px - 32, px + 32, zE, zE + 44, yd)                        # cabeca
    outline = [(px - HW, zA), (px - HW, zR + 6), (px - HW - 30, zR + 6), (px - HW - 30, zR + 34), (px - HW, zR + 34), (px - HW, zR + 50), (SH0, zR + 50),
               (SH0, zR + 180), (px - HW, zR + 180), (px - HW, zE), (px - 32, zE), (px - 32, zE + 44), (px + 32, zE + 44), (px + 32, zE),
               (px + HW, zE), (px + HW, PZ1), (PK1, PZ1), (PK1, PZ0), (px + HW, PZ0), (px + HW, zA)]
    for i in range(len(outline) - 1):
        a_, b_ = outline[i], outline[i + 1]
        if a_[1] < zR + 0.1 and b_[1] < zR + 0.1: continue
        M.at((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2, 'orla'); M.m('liso'); _rail_line(M, [(a_[0], max(a_[1], zR)), (b_[0], max(b_[1], zR))], yd); M.free()
    # portal da entrada (arco azul com letreiro e lampadas) no comeco da rampa e outro no alto
    arch(M, px, zA + 3.0, y + (yd - y) * 3.0 / 34.0, 2 * HW - 2.0)
    arch(M, px, zR + 1.0, yd, 2 * HW - 2.0)
    hippodrome(M, px - HW - 27, px - HW - 3, zR + 9, zR + 31, yd)
    # lojinhas (fileira oeste, frente para o deck)
    for k, z in enumerate(np.arange(zR + 54, zR + 176, 9.5)):
        shop_cottage(M, px - HW - 6.0, z, yd, 1, 8.5, r) if False else None
    for k, z in enumerate(np.arange(zR + 55, zR + 177, 9.5)):
        shop_cottage_x(M, SH0 + 5.5, z, yd, 1, 8.5, r)
    # parque
    park_gate(M, px + HW, PZ0 + 22, yd, 12.0)
    ferris_wheel(M, pr, PK0 + 40, PZ1 - 26, yd, r, 26.0, 32)
    coaster(M, PK0 + 3, PK1 - 3, PZ0 + 3, PZ1 - 3, yd, r, 18.0)
    swing_ship(M, PK0 + 22, PZ0 + 40, yd)
    scrambler(M, PK0 + 48, PZ0 + 34, yd, r)
    carousel(M, PK0 + 20, PZ0 + 78, yd, r)
    bumper_cars(M, PK0 + 48, PZ0 + 82, yd, r)
    arcade(M, PK0 + 16, PZ1 - 14, yd, r)
    cols = [(230, 60, 60), (40, 140, 220), (250, 190, 40), (60, 180, 100), (220, 90, 180), (240, 130, 40)]
    for k, z in enumerate(np.arange(PZ0 + 6, PZ1 - 6, 11.0)):
        stall_side(M, PK1 - 3.0, z, yd, cols[k % 6], -1)
    for k, xx in enumerate(np.arange(PK0 + 8, PK1 - 6, 9.0)):
        stall(M, xx, PZ0 + 3.0, yd, cols[(k + 2) % 6], 1)
    food_court(M, pr, PK0 + 30, PK0 + 44, PZ0 + 52, PZ0 + 68, yd, r)
    # deck principal: postes classicos, bancos, floreiras com palmeiras
    for z in np.arange(zR + 6, zE, 9.0):
        for s_ in (-1, 1): classic_lamp(M, px + s_ * (HW - 0.8), z, yd)
    for z in np.arange(zR + 10, zE, 18.0):
        pr.bench(px - HW + 1.8, z, 1, 0, yd); pr.bench(px + HW - 1.8, z + 9, -1, 0, yd)
    for z in np.arange(zR + 200, zE, 24.0): planter_pier(M, pr, px, z, yd, r)
    # cabeca: restaurante de dois andares, capitania com sino, pesca
    rx0, rz0 = px - 28, zE + 20
    M.at(px - 14, rz0 + 10, 'orla'); M.m('siding'); M.box(rx0, rx0 + 28, yd, yd + 7.6, rz0, rz0 + 20, (240, 236, 226), top=False)
    M.m('vidro')
    for yy in (yd + 0.8, yd + 4.6):
        M.quad((rx0 + 1, yy, rz0 - 0.03), (rx0 + 27, yy, rz0 - 0.03), (rx0 + 27, yy + 2.6, rz0 - 0.03), (rx0 + 1, yy + 2.6, rz0 - 0.03), WHITE, (0, 0, -1))
        M.quad((rx0 + 28.03, yy, rz0 + 1), (rx0 + 28.03, yy, rz0 + 19), (rx0 + 28.03, yy + 2.6, rz0 + 19), (rx0 + 28.03, yy + 2.6, rz0 + 1), WHITE, (1, 0, 0))
    M.m('madeira'); M.box(rx0 - 0.2, rx0 + 28.2, yd + 3.8, yd + 4.0, rz0 - 3.0, rz0, (150, 110, 74))         # varanda do 2o andar
    M.m('liso')
    for xx in np.arange(rx0, rx0 + 28.1, 1.2): M.box(xx - 0.04, xx + 0.04, yd + 4.0, yd + 5.0, rz0 - 3.0, rz0 - 2.92, (250, 250, 246))
    M.box(rx0, rx0 + 28, yd + 4.95, yd + 5.05, rz0 - 3.0, rz0 - 2.9, (250, 250, 246))
    M.m('telha'); M.quad((rx0 - 1, yd + 7.6, rz0 - 1), (rx0 + 29, yd + 7.6, rz0 - 1), (rx0 + 29, yd + 10.0, rz0 + 10), (rx0 - 1, yd + 10.0, rz0 + 10), (60, 90, 110), (0, 1, -0.4))
    M.quad((rx0 - 1, yd + 10.0, rz0 + 10), (rx0 + 29, yd + 10.0, rz0 + 10), (rx0 + 29, yd + 7.6, rz0 + 21), (rx0 - 1, yd + 7.6, rz0 + 21), (60, 90, 110), (0, 1, 0.4))
    M.m('siding')
    for s_, xe in ((-1, rx0), (1, rx0 + 28)): M.tri((xe, yd + 7.6, rz0 - 1), (xe, yd + 7.6, rz0 + 21), (xe, yd + 10.0, rz0 + 10), (240, 236, 226), (s_, 0, 0))
    M.m('liso'); M.box(rx0 + 6, rx0 + 22, yd + 8.0, yd + 9.2, rz0 - 1.3, rz0 - 1.1, (40, 110, 180))
    M.free()
    hx, hz = px + 20, zE + 30
    M.at(hx, hz, 'orla'); M.m('siding'); M.box(hx - 4, hx + 4, yd, yd + 4.0, hz - 4, hz + 4, (250, 250, 246), top=False)
    M.m('telha'); M.cyl(hx, hz, 5.6, yd + 4.0, yd + 6.2, (60, 90, 110), 4, False, 0.1)
    M.m('siding'); M.box(hx - 1, hx + 1, yd + 6.0, yd + 8.4, hz - 1, hz + 1, (250, 250, 246), top=False)
    M.m('metal'); M.sphere(hx, yd + 7.4, hz, 0.45, (200, 160, 60), 6, 4); M.m('telha'); M.cyl(hx, hz, 1.5, yd + 8.4, yd + 9.6, (60, 90, 110), 4, False, 0.05)
    M.free()
    for k, xx in enumerate(np.arange(px - 30, px + 31, 4.0)):
        if px + 10 < xx < px + 26: continue
        pr.bench(xx, zE + 42.6, 0, -1, yd)
    for xx in np.arange(px + 4, px + 31, 6.0): classic_lamp(M, xx, zE + 8, yd)
    pr.luzes.append({'tipo': 'roda_gigante', 'x': round(PK0 + 40, 2), 'y': round(yd + 29, 2), 'z': round(PZ1 - 26, 2), 'cor': [255, 236, 160], 'alcance_m': 200})


def shop_cottage_x(M, x, z, yd, face, w, r):
    """loja da fileira oeste: frente virada para o leste (para o deck principal)"""
    wall = r.choice(((246, 240, 224), (214, 232, 236), (244, 222, 210), (226, 240, 216), (250, 236, 196)))
    rc = r.choice(((120, 60, 50), (60, 90, 110), (70, 80, 70))); ac = r.choice(COLS)
    d = 9.0; x0, x1 = x - d / 2, x + d / 2; z0, z1 = z - w / 2, z + w / 2
    M.at(x, z, 'orla'); M.m('siding'); M.box(x0, x1, yd, yd + 3.4, z0, z1, wall, top=False)
    M.m('telha')
    for s_ in (-1, 1):
        M.quad((x0 - 0.3, yd + 3.4, z + s_ * (w / 2 + 0.3)), (x1 + 0.3, yd + 3.4, z + s_ * (w / 2 + 0.3)), (x1 + 0.3, yd + 5.4, z), (x0 - 0.3, yd + 5.4, z), rc, (0, 0.8, s_ * 0.6))
    M.m('siding')
    for xf, s_ in ((x0, -1), (x1, 1)): M.tri((xf, yd + 3.4, z0), (xf, yd + 3.4, z1), (xf, yd + 5.4, z), wall, (s_, 0, 0))
    xf = x1 + 0.03
    M.m('vitrine'); M.quad((xf, yd + 0.4, z0 + 0.6), (xf, yd + 0.4, z1 - 0.6), (xf, yd + 2.6, z1 - 0.6), (xf, yd + 2.6, z0 + 0.6), WHITE, (1, 0, 0), [(0, 1), (2, 1), (2, 0), (0, 0)])
    M.m('liso')
    for k in range(int(w / 0.6)):
        za = z0 + k * 0.6
        M.quad((xf, yd + 3.0, za), (xf, yd + 3.0, za + 0.6), (xf + 1.1, yd + 2.6, za + 0.6), (xf + 1.1, yd + 2.6, za), ac if k % 2 == 0 else (250, 250, 246), (0.5, 0.8, 0))
    M.box(xf, xf + 0.1, yd + 3.5, yd + 4.2, z - w * 0.3, z + w * 0.3, ac)
    M.free()


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


# ================================================================ praia (v3): restinga, barracas com kits, esportes, banhistas
class Occ:
    def __init__(self): self.c = []
    def free(self, x, z, rad): return all(math.hypot(x - a, z - b) > rad + c for (a, b, c) in self.c)
    def add(self, x, z, rad): self.c.append((x, z, rad))


def grass_tuft(M, x, z, r, h=0.5):
    """touceira de capim da restinga: laminas finas em leque"""
    yb = sand_y(x, z) - 0.03; col = r.choice(((112, 140, 70), (132, 150, 78), (96, 128, 62), (150, 156, 90)))
    for k in range(7):
        a = r.uniform(0, 6.28); l = h * r.uniform(0.6, 1.1); dx, dz = math.cos(a), math.sin(a)
        M.tri((x - dz * 0.05, yb, z + dx * 0.05), (x + dz * 0.05, yb, z - dx * 0.05), (x + dx * l * 0.45, yb + l, z + dz * l * 0.45), shade(col, r.randint(-12, 12)), (dx, 0.6, dz))


def ipomoea(M, x, z, r):
    """salsa-da-praia: manta verde rasteira com florzinhas roxas"""
    yb = sand_y(x, z); n = 9; R = r.uniform(0.9, 1.6)
    pts = [(x + math.cos(2 * math.pi * k / n) * R * r.uniform(0.7, 1.1), z + math.sin(2 * math.pi * k / n) * R * r.uniform(0.7, 1.1)) for k in range(n)]
    for k in range(n):
        p0, p1 = pts[k], pts[(k + 1) % n]
        M.tri((x, yb + 0.12, z), (p1[0], sand_y(*p1) + 0.01, p1[1]), (p0[0], sand_y(*p0) + 0.01, p0[1]), (78, 128, 60), (0, 1, 0))
    for _ in range(4):
        fx, fz = x + r.uniform(-R, R) * 0.6, z + r.uniform(-R, R) * 0.6
        M.sphere(fx, yb + 0.12, fz, 0.07, (190, 90, 190), 4, 2)


def plastic_chair(M, x, z, ang, col, yb):
    """cadeira de praia de aluminio com lona listrada, reclinada"""
    F = Frame((x, z), (math.cos(ang), math.sin(ang)))
    for v in (-0.26, 0.26):
        M.quad(F.p(-0.3, v, yb), F.p(-0.26, v, yb), F.p(0.34, v, yb + 0.32), F.p(0.3, v, yb + 0.32), (210, 212, 216), (0, 0, 1))
        M.quad(F.p(0.3, v, yb), F.p(0.34, v, yb), F.p(-0.26, v, yb + 0.84), F.p(-0.3, v, yb + 0.84), (210, 212, 216), (0, 0, 1))
    M.quad(F.p(-0.3, -0.27, yb + 0.3), F.p(-0.3, 0.27, yb + 0.3), F.p(0.3, 0.27, yb + 0.28), F.p(0.3, -0.27, yb + 0.28), col, (0, 1, 0))
    M.quad(F.p(-0.3, 0.27, yb + 0.3), F.p(-0.3, -0.27, yb + 0.3), F.p(-0.46, -0.27, yb + 0.86), F.p(-0.46, 0.27, yb + 0.86), shade(col, 10), (0.9, 0.4, 0))


def beach_table(M, x, z, yb, col=(250, 250, 248)):
    M.cyl(x, z, 0.04, yb, yb + 0.6, (200, 200, 204), 4, False)
    M.cyl(x, z, 0.36, yb + 0.6, yb + 0.65, col, 10)
    M.cyl(x - 0.12, z + 0.05, 0.035, yb + 0.65, yb + 0.85, (200, 140, 40), 5)       # garrafa / copo
    M.cyl(x + 0.1, z - 0.08, 0.04, yb + 0.65, yb + 0.76, (240, 240, 236), 5)


def kit(M, x, z, col, col2, r, n=2):
    """kit de barraca: guarda-sol + mesinha + 2 ou 3 cadeiras viradas pro mar"""
    yb = sand_y(x, z)
    umbrella(M, x, z, col, r, False, col2=col2)
    M.at(x, z, 'orla'); M.m('liso')
    beach_table(M, x + 0.15, z + 0.2, yb)
    for k in range(n):
        u = (k - (n - 1) / 2) * 0.85
        plastic_chair(M, x + u + r.uniform(-0.1, 0.1), z + 1.05 + r.uniform(-0.1, 0.15), -math.pi / 2 + r.uniform(-0.25, 0.25), col if k % 2 == 0 else col2, yb)
    M.free()


def tent(M, x, z, col, r):
    """barraca de praia: tenda de lona 5x4 m com balcao, isopores, cadeiras empilhadas, placa e varal de cangas"""
    yb = sand_y(x, z); M.at(x, z, 'orla')
    M.m('metal')
    for (dx, dz) in ((-2.5, -2), (2.5, -2), (2.5, 2), (-2.5, 2)): M.cyl(x + dx, z + dz, 0.05, yb - 0.3, yb + 2.4, (210, 212, 216), 5, False)
    M.m('liso')
    for k in range(6):                                                  # lona listrada em duas aguas
        x0, x1 = x - 2.7 + k * 0.9, x - 1.8 + k * 0.9; c = col if k % 2 == 0 else (250, 250, 246)
        M.quad((x0, yb + 2.4, z - 2.2), (x1, yb + 2.4, z - 2.2), (x1, yb + 3.2, z), (x0, yb + 3.2, z), c, (0, 0.9, -0.4))
        M.quad((x0, yb + 3.2, z), (x1, yb + 3.2, z), (x1, yb + 2.4, z + 2.2), (x0, yb + 2.4, z + 2.2), c, (0, 0.9, 0.4))
        M.quad((x1, yb + 2.4, z + 2.2), (x0, yb + 2.4, z + 2.2), (x0, yb + 2.1, z + 2.2), (x1, yb + 2.1, z + 2.2), shade(c, -15), (0, 0, 1))    # babado
    for s in (-1, 1): M.tri((x + s * 2.7, yb + 2.4, z - 2.2), (x + s * 2.7, yb + 2.4, z + 2.2), (x + s * 2.7, yb + 3.2, z), col, (s, 0, 0))
    M.m('madeira'); M.box(x - 2.0, x + 2.0, yb, yb + 1.05, z - 0.4, z + 0.3, (190, 150, 100))          # balcao
    M.box(x - 2.1, x + 2.1, yb + 1.05, yb + 1.12, z - 0.5, z + 0.4, (150, 108, 70))
    M.m('liso')
    for k in range(3): M.box(x - 1.8 + k * 1.0, x - 1.1 + k * 1.0, yb, yb + 0.5, z - 1.6, z - 1.0, r.choice(((40, 110, 200), (220, 60, 50), (250, 250, 248))))   # isopores
    for k in range(6): plastic_chair(M, x + 2.0, z - 1.4 + k * 0.03, 0.0, col, yb + k * 0.08)                # pilha de cadeiras
    M.box(x - 1.3, x + 1.3, yb + 2.45, yb + 3.0, z + 2.21, z + 2.26, (250, 250, 246))                   # placa
    M.box(x - 1.1, x + 1.1, yb + 2.55, yb + 2.9, z + 2.26, z + 2.28, col)
    M.box(x + 1.4, x + 1.5, yb + 1.12, yb + 1.6, z - 0.2, z - 0.1, (60, 160, 70))                       # coco
    M.sphere(x - 1.4, yb + 1.25, z - 0.1, 0.14, (90, 150, 60), 5, 3); M.sphere(x - 1.1, yb + 1.25, z, 0.14, (90, 150, 60), 5, 3)
    for k in range(4): M.quad((x - 2.6, yb + 2.3, z - 1.6 + k * 0.9), (x - 2.6, yb + 2.3, z - 0.9 + k * 0.9), (x - 2.6, yb + 1.3, z - 0.9 + k * 0.9), (x - 2.6, yb + 1.3, z - 1.6 + k * 0.9), r.choice(COLS), (-1, 0, 0))   # cangas
    M.free()


def jangada(M, x, z, r):
    """jangada / barco de pesca puxado para a areia, com mastro e rede"""
    yb = sand_y(x, z); col = r.choice(((40, 110, 200), (230, 70, 50), (40, 150, 110), (250, 200, 50)))
    out = [(-3.0, 0), (-2.4, 0.8), (2.2, 0.8), (3.2, 0), (2.2, -0.8), (-2.4, -0.8)]
    a = math.pi / 2 + r.uniform(-0.3, 0.3); c, s = math.cos(a), math.sin(a)
    pts = [(x + c * u - s * v, z + s * u + c * v) for (u, v) in out]
    M.at(x, z, 'orla'); M.m('madeira'); M.prism(pts, yb - 0.1, yb + 0.55, col, True, False, (200, 170, 120))
    M.m('liso'); M.prism([(x + c * u * 1.01 - s * v * 1.03, z + s * u * 1.01 + c * v * 1.03) for (u, v) in out], yb + 0.55, yb + 0.65, (250, 250, 246))
    M.cyl(x, z, 0.06, yb + 0.55, yb + 4.5, (150, 108, 70), 5, False)
    M.m('cerca'); M.sphere(x + 1.6 * c, yb + 0.75, z + 1.6 * s, 0.5, (90, 110, 90), 6, 3, 0.4)
    M.free()


def footvolley(M, x, z, r):
    volley(M, x, z, r)


def beach(M, pr, xa, xb, gaps, r):
    occ = Occ()
    for g in gaps: occ.add(g, ZW + 12, 4.0)                               # passarelas
    # restinga + coqueiros junto da mureta (nunca na frente das escadas)
    x = xa + r.uniform(6, 12)
    while x < xb - 6:
        if all(abs(x - g) > 6 for g in gaps):
            for _ in range(r.randint(2, 4)):
                px, pz = x + r.uniform(-4, 4), ZW + r.uniform(3.0, 9.0)
                if all(abs(px - g) > 5 for g in gaps):
                    pr.tree(px, pz, 'palmeira', r.choice((0.85, 1.0, 1.15, 1.3, 1.5, 1.75)), sand_y(px, pz) - 0.05)
        x += r.uniform(16, 26)
    M.free('orla'); M.m('liso')
    x = xa + 3
    while x < xb - 3:
        if all(abs(x - g) > 4.5 for g in gaps):
            z = ZW + r.uniform(1.2, 11)
            grass_tuft(M, x, z, r, r.uniform(0.35, 0.7))
            if r.random() < 0.25: ipomoea(M, x + r.uniform(-1, 1), ZW + r.uniform(4, 13), r)
        x += r.uniform(0.9, 2.2)
    M.free()
    x = xa + 8
    while x < xb - 8:
        if all(abs(x - g) > 5 for g in gaps): pr.tree(x, ZW + r.uniform(1.6, 3.0), 'arbusto', r.uniform(0.5, 0.8), sand_y(x, ZW + 2) - 0.05)
        x += r.uniform(5, 11)
    # barraca no fim de cada passarela, com o seu leque de kits ate perto do mar
    for i, g in enumerate(gaps):
        col = COLS[(i * 3 + 1) % len(COLS)]; col2 = (250, 250, 246) if i % 3 else r.choice(COLS)
        tx, tz = g + (7.5 if i % 2 else -7.5), ZW + 25
        tent(M, tx, tz, col, r); occ.add(tx, tz, 4.5)
        nr, nc = r.choice((3, 4)), r.choice((3, 4, 5))
        for row in range(nr):
            for c in range(nc):
                kx = g + (c - (nc - 1) / 2) * 5.2 + r.uniform(-0.6, 0.6) + (row % 2) * 1.3
                kz = ZW + 34 + row * 6.2 + r.uniform(-0.6, 0.6)
                if kz > shore_z(kx) - 14 or not occ.free(kx, kz, 2.0): continue
                kit(M, kx, kz, col, col2, r, r.choice((2, 2, 3))); occ.add(kx, kz, 2.2)
    # entre as barracas: esportes, salva-vidas e aluguel
    mids = [(gaps[i] + gaps[i + 1]) / 2 for i in range(len(gaps) - 1)]
    for k, mx in enumerate(mids):
        what = ('volei', 'salva', 'futebol', 'tenis', 'aluguel', 'futevolei', 'salva', 'volei')[k % 8]
        if what == 'volei' or what == 'futevolei': volley(M, mx, ZW + 22, r); occ.add(mx, ZW + 22, 9)
        elif what == 'futebol': soccer(M, mx, ZW + 24, r); occ.add(mx - 7, ZW + 24, 8); occ.add(mx + 7, ZW + 24, 8)
        elif what == 'tenis': beach_tennis(M, mx, ZW + 22, r); occ.add(mx, ZW + 22, 8)
        elif what == 'aluguel': rental(M, pr, mx, r); occ.add(mx, shore_z(mx) - 18, 5); occ.add(mx, shore_z(mx) - 4, 6)
        else:
            lz = shore_z(mx) - 34; lifeguard(M, mx, lz, r); flags(M, mx + 6, lz + 4, r); occ.add(mx, lz + 2, 6)
            if r.random() < 0.6: volley(M, mx, ZW + 22, r); occ.add(mx, ZW + 22, 9)
    # banhistas avulsos (guarda-sol, cangas, cooler), castelos, jangadas e ambulantes
    tries = int((xb - xa) / 4)
    for _ in range(tries):
        x = r.uniform(xa + 8, xb - 8); z = r.uniform(ZW + 30, shore_z(x) - 9)
        if occ.free(x, z, 3.0): family(M, x, z, r); occ.add(x, z, 3.0)
    for _ in range(int((xb - xa) / 40)):
        x = r.uniform(xa + 8, xb - 8); z = shore_z(x) - r.uniform(3.5, 7)
        if occ.free(x, z, 1.5): sandcastle(M, x, z, r); occ.add(x, z, 1.5)
    for _ in range(int((xb - xa) / 160)):
        x = r.uniform(xa + 20, xb - 20); z = shore_z(x) - r.uniform(9, 13)
        if occ.free(x, z, 4): jangada(M, x, z, r); occ.add(x, z, 4)
    for _ in range(int((xb - xa) / 70)):
        x = r.uniform(xa + 10, xb - 10); z = r.uniform(ZW + 30, shore_z(x) - 20)
        if occ.free(x, z, 2): vendor_cart(M, x, z, r); occ.add(x, z, 2)
