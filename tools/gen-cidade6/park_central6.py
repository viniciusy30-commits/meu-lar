"""Cidade 6 - Parque Central "Lagoa Azul": o ponto turistico da cidade.

Lagoa de contorno organico com margem natural (prainha de areia, pedras, taboas), vitorias-regias floridas sobre a
agua, ilha com salgueiro-chorao e pavilhao, ponte vermelha em arco ate a ilha, deque de madeira com guarda-corpo e
bancos, pier com pedalinhos de cisne, cascata de pedras caindo na lagoa, repuxo alto no meio; fauna viva (carpas,
patos, cisnes: c6.json 'fauna', o jogo anima). Praca do Relogio (torre com 4 mostradores, piso em mosaico, canteiros
de flores em estrela, bancos), coreto ornamentado, playground, portais nas 4 entradas, caminhos com postes e canteiros.
Tudo apoiado no gramado (Y_LAWN): nada flutua.
"""
import math
import numpy as np
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
from roads6 import Y_LAWN
from mesh import shade, WHITE, Frame

WY = Y_LAWN + 0.06           # espelho d'agua da lagoa (abaixo da borda)
GLOW = (255, 238, 196)


def build(pr, blk):
    M = pr.M; r = pr.rnd; poly = blk['poly']
    minx, minz, maxx, maxz = poly.bounds; cx, cz = (minx + maxx) / 2, (minz + maxz) / 2
    W_, D_ = maxx - minx, maxz - minz
    lx, lz = cx + 8, cz + 14                                 # centro da lagoa
    RX, RZ = min(64, W_ * 0.27), min(42, D_ * 0.18)
    lake = Polygon([(lx + math.cos(a) * RX * (1 + 0.10 * math.sin(3 * a + 0.7)), lz + math.sin(a) * RZ * (1 + 0.12 * math.cos(2 * a))) for a in np.linspace(0, 2 * math.pi, 72, endpoint=False)])
    isl_c = (lx - RX * 0.15, lz - RZ * 0.25); isl = Point(*isl_c).buffer(8.5, 16)
    fauna = pr.__dict__.setdefault('fauna', [])
    # ---------------- caminhos: anel da lagoa, diagonais, eixos e praca do relogio
    rel = (minx + W_ * 0.80, minz + D_ * 0.20)              # praca do relogio (nordeste)
    cor = (minx + W_ * 0.20, minz + D_ * 0.80)              # coreto (sudoeste)
    ply = (minx + W_ * 0.80, minz + D_ * 0.82)              # playground (sudeste)
    ring = lake.buffer(10).exterior.buffer(2.4)
    paths = [ring]
    for (a, b) in (((minx, minz), rel), ((maxx, maxz), ply), ((minx, maxz), cor), ((maxx, minz), rel), ((cx, minz), (cx, lz - RZ - 10)), ((cx, maxz), (cx, lz + RZ + 10)),
                   ((minx, cz), (lx - RX - 10, cz)), ((maxx, cz + 6), (lx + RX + 10, cz + 6)), (rel, (lx + RX * 0.6, lz - RZ - 6)), (cor, (lx - RX * 0.6, lz + RZ + 6)), (ply, (lx + RX * 0.5, lz + RZ + 6))):
        paths.append(LineString([a, b]).buffer(2.0))
    paths.append(Point(*rel).buffer(17, 32)); paths.append(Point(*cor).buffer(11, 24))
    pth = unary_union(paths).intersection(poly.buffer(-0.5)).difference(lake.buffer(2.0))
    M.free('parques'); M.m('paver'); M.shp(pth, Y_LAWN + 0.07, (236, 226, 208))
    # ---------------- lagoa: margem natural (pedra), prainha, agua
    M.m('pedra'); ring2 = list(lake.exterior.coords)
    for k in range(len(ring2) - 1):
        a, b = ring2[k], ring2[k + 1]; M.at((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 'parques'); M.wall_strip([a, b], Y_LAWN - 0.5, Y_LAWN + 0.2, 0.9, (176, 170, 160))
    M.free('parques')
    beach = lake.buffer(5.0).difference(lake.buffer(0.45)).intersection(Polygon([(lx - RX - 8, lz + 2), (lx + 4, lz + 2), (lx + 4, lz + RZ + 10), (lx - RX - 8, lz + RZ + 10)]))
    M.m('areia'); M.shp(beach, Y_LAWN + 0.075, (238, 222, 184))
    M.m('agua'); M.shp(lake.difference(isl), WY, (120, 190, 200))
    M.m('areia'); M.shp(lake.buffer(-1.2).exterior.buffer(0.01) if False else lake.difference(lake.buffer(-1.6)), WY - 0.04, (196, 186, 150))      # rasinho (sob a agua)
    # pedras grandes na margem norte e cascata a oeste
    for k in range(26):
        a = r.uniform(-2.6, -1.15); px, pz = lx + math.cos(a) * RX * 1.02, lz + math.sin(a) * RZ * 1.05
        M.at(px, pz, 'parques'); M.m('pedra'); M.sphere(px, Y_LAWN + 0.05, pz, r.uniform(0.5, 1.3), r.choice(((150, 146, 138), (128, 124, 118), (170, 164, 152))), 7, 4, 0.6, 0.2, r)
    cascade(M, r, lx - RX * 0.98, lz - 4, fauna)
    # taboas e vitorias-regias
    for k in range(10):
        a = r.uniform(0.45, 2.4); bx, bz = lx + math.cos(a) * RX * 0.93, lz + math.sin(a) * RZ * 0.9
        reeds(M, r, bx, bz)
    for k in range(22):
        a = r.uniform(0, 6.28); d = r.uniform(0.55, 0.85)
        px, pz = lx + math.cos(a) * RX * d, lz + math.sin(a) * RZ * d
        if isl.buffer(3).contains(Point(px, pz)): continue
        lily(M, r, px, pz)
    # ---------------- ilha: chorao, pavilhao, flores
    M.at(*isl_c, 'parques'); M.m('pedra'); M.cyl(isl_c[0], isl_c[1], 8.6, Y_LAWN - 0.5, Y_LAWN + 0.2, (176, 170, 160), 24)
    M.m('grama'); M.cyl(isl_c[0], isl_c[1], 8.0, Y_LAWN + 0.2, Y_LAWN + 0.3, (110, 160, 80), 24)
    pavilion(M, isl_c[0] + 2.0, isl_c[1] - 1.0, Y_LAWN + 0.3)
    pr.tree(isl_c[0] - 4.0, isl_c[1] + 2.5, 'folhosa', 1.35, Y_LAWN + 0.3)
    for k in range(8): a = k * 0.8; pr.tree(isl_c[0] + math.cos(a) * 6.6, isl_c[1] + math.sin(a) * 6.6, 'flores', 1.0, Y_LAWN + 0.3)
    # ponte vermelha em arco da margem norte ate a ilha
    shore_n = (isl_c[0], lz - RZ * (1 + 0.12 * math.cos(math.pi)) + 0.0)
    nb = Point(isl_c[0], isl_c[1] - 8.6); sb = LineString([(isl_c[0], isl_c[1] - 8.6), (isl_c[0], lz - RZ * 1.25)]).intersection(lake.exterior)
    z0 = min([p.y for p in getattr(sb, 'geoms', [sb])] or [lz - RZ]) - 1.0
    red_bridge(M, isl_c[0], z0, isl_c[1] - 8.0)
    # ---------------- deque leste com guarda-corpo, bancos e pier com pedalinhos
    deck(M, pr, r, lx, lz, RX, RZ, -0.95, 0.2)
    pier(M, r, lx + RX * 0.35, lz + RZ * 0.98, fauna)
    # ---------------- repuxo
    fx, fz = lx + RX * 0.4, lz - RZ * 0.05
    M.at(fx, fz, 'parques'); M.m('pedra'); M.cyl(fx, fz, 1.4, WY - 0.2, WY + 0.25, (200, 196, 188), 16)
    M.m('liso'); M.cyl(fx, fz, 0.12, WY + 0.25, WY + 7.5, (235, 245, 250), 8, True, 0.04); M.cyl(fx, fz, 1.6, WY + 0.02, WY + 0.6, (230, 242, 248), 12, False, 0.2)
    for k in range(10):
        a = 2 * math.pi * k / 10; M.cyl(fx + math.cos(a) * 1.0, fz + math.sin(a) * 1.0, 0.05, WY + 0.25, WY + 2.6, (230, 242, 248), 6, True, 0.02)
    pr.lagoa = [round(lx, 2), round(lz, 2), round(RX, 2), round(RZ, 2), round(isl_c[0], 2), round(isl_c[1], 2), 8.6, round(WY + 0.012, 3)]
    # ---------------- areas de convivencia em volta: piquenique, cafe, roseiral com pergolado, academia, xadrez
    P_ = lambda fu, fv: (minx + W_ * fu, minz + D_ * fv)
    spots = {'piquenique': P_(0.21, 0.245), 'cafe': P_(0.598, 0.262), 'roseiral': P_(0.105, 0.645), 'academia': P_(0.372, 0.895),
             'piquenique2': P_(0.63, 0.905), 'leste': P_(0.935, 0.665)}
    pr.park_spots = spots
    feat = []
    feat.append(picnic_area(M, pr, r, *spots['piquenique'], 21, 15))
    feat.append(cafe(M, pr, r, *spots['cafe']))
    feat.append(rose_garden(M, pr, r, *spots['roseiral']))
    feat.append(gym(M, pr, *spots['academia']))
    feat.append(picnic_area(M, pr, r, *spots['piquenique2'], 17, 12, chess=True))
    feat.append(east_corner(M, pr, r, *spots['leste']))
    # ---------------- praca do relogio, coreto, playground, portais
    clock_square(M, pr, r, *rel)
    bandstand(M, *cor)
    playground(M, *ply)
    for (gx, gz) in ((minx + 2.5, minz + 2.5), (maxx - 2.5, maxz - 2.5), (minx + 2.5, maxz - 2.5), (maxx - 2.5, minz + 2.5)):
        dx, dz = (cx - gx), (cz - gz); L = math.hypot(dx, dz); gate(M, gx + dx / L * 4, gz + dz / L * 4, -dz / L, dx / L)
    # ---------------- plantio: chorao e palmeiras na margem, bosques por especie, canteiros nas bordas dos caminhos
    occ = unary_union(feat + [lake.buffer(7), pth.buffer(1.8), Point(*rel).buffer(19), Point(*cor).buffer(13), Point(*ply).buffer(16), isl.buffer(2)])
    for k in range(16):
        a = 2 * math.pi * k / 16 + 0.2; px, pz = lx + math.cos(a) * (RX + 14), lz + math.sin(a) * (RZ + 14)
        if poly.buffer(-4).contains(Point(px, pz)) and not pth.buffer(2.5).contains(Point(px, pz)): pr.tree(px, pz, 'palmeira' if k % 3 else 'folhosa', r.uniform(1.0, 1.35))
    groves = [('florida', (minx + W_ * 0.15, minz + D_ * 0.15)), ('conifera', (minx + W_ * 0.12, minz + D_ * 0.5)), ('oval', (minx + W_ * 0.5, minz + D_ * 0.9)),
              ('folhosa', (maxx - W_ * 0.12, minz + D_ * 0.5)), ('ornamental', (minx + W_ * 0.42, minz + D_ * 0.12))]
    for (sp, (gx, gz)) in groves:
        for k in range(18):
            px, pz = gx + r.gauss(0, 10), gz + r.gauss(0, 10)
            if poly.buffer(-4).contains(Point(px, pz)) and not occ.contains(Point(px, pz)): pr.tree(px, pz, sp, r.uniform(0.9, 1.25)); occ = occ.union(Point(px, pz).buffer(4.5))
    # preenchimento: bosque solto em todo gramado livre (grade com sorteio), clareiras deixadas nas areas de convivencia
    kinds = ('folhosa', 'folhosa', 'oval', 'florida', 'conifera', 'ornamental', 'folhosa', 'oval')
    inner = poly.buffer(-4)
    for gx in np.arange(minx + 5, maxx - 4, 10.5):
        for gz in np.arange(minz + 5, maxz - 4, 10.5):
            px, pz = gx + r.uniform(-3.2, 3.2), gz + r.uniform(-3.2, 3.2)
            q = Point(px, pz)
            if inner.contains(q) and not occ.contains(q) and r.random() < 0.82:
                pr.tree(px, pz, r.choice(kinds), r.uniform(0.85, 1.3)); occ = occ.union(q.buffer(5.0))
    # arbustos baixos em grupos nas bordas do parque (cerca viva junto da calcada, com falhas nas entradas)
    bd = poly.buffer(-2.2).exterior; Lb = bd.length; d = 0.0
    while d < Lb:
        q = bd.interpolate(d)
        if not pth.buffer(3.0).contains(q) and not occ.contains(q): pr.tree(q.x, q.y, 'arbusto', r.uniform(0.8, 1.1))
        d += 2.6
    edge = pth.buffer(2.6).difference(pth.buffer(1.0))
    for g in getattr(edge, 'geoms', [edge]):
        cs = list(g.exterior.coords)
        for k in range(0, len(cs), 3):
            px, pz = cs[k]
            if not occ.contains(Point(px, pz)) and poly.buffer(-2).contains(Point(px, pz)) and r.random() < 0.55: pr.tree(px, pz, 'flores', r.uniform(0.9, 1.2))
    # postes e bancos ao longo do anel da lagoa
    rl = lake.buffer(10).exterior; L_ = rl.length; d = 6.0; k = 0
    while d < L_:
        p = rl.interpolate(d); q = rl.interpolate(min(L_, d + 1))
        tx, tz = q.x - p.x, q.y - p.y; tl = math.hypot(tx, tz) or 1; nx, nz = -tz / tl, tx / tl
        if k % 3 == 0: pr.parklight(p.x + nx * 3.2, p.y + nz * 3.2, Y_LAWN, 'globos')
        elif k % 3 == 1: pr.bench(p.x - nx * 3.0, p.y - nz * 3.0, nx, nz, Y_LAWN + 0.03)
        d += 9.0; k += 1
    # fauna: carpas em cardumes, patos em volta da ilha, cisnes passeando
    for k in range(10):
        a = r.uniform(0, 6.28); dd = r.uniform(0.3, 0.75); px, pz = lx + math.cos(a) * RX * dd, lz + math.sin(a) * RZ * dd
        if isl.buffer(3).contains(Point(px, pz)): continue
        sp = r.choice((1, -1)) * r.uniform(0.5, 0.9)
        for q in range(5): fauna.append([round(px + r.uniform(-0.6, 0.6), 2), round(pz + r.uniform(-0.6, 0.6), 2), round(r.uniform(1.2, 3.4), 2), round(r.uniform(0, 6.28), 2), round(sp, 2), r.randint(0, 5), round(WY - 0.06, 3)])
    for k in range(7): fauna.append([round(isl_c[0], 2), round(isl_c[1], 2), round(11.5 + (k % 3) * 1.6, 2), round(k * 0.9, 2), 0.26, 6 + k % 2, round(WY + 0.0, 3)])
    for k in range(3): fauna.append([round(lx + RX * 0.2, 2), round(lz + RZ * 0.25, 2), round(14.0 + k * 3.5, 2), round(k * 2.1, 2), -0.12, 8, round(WY + 0.0, 3)])
    M.free()


# ======================================================================== pecas
def cascade(M, r, x, z, fauna):
    """cascata: monte de pedras com degraus d'agua (laminas) caindo num poco espumante"""
    M.at(x, z, 'parques'); M.m('pedra')
    for k in range(40):
        a = r.uniform(-1.2, 1.2); d = r.uniform(0, 5.5); h = max(0.2, 3.6 - d * 0.55)
        M.sphere(x - 3.0 - math.cos(a) * d, Y_LAWN + h * 0.6, z + math.sin(a) * d * 0.9, r.uniform(0.7, 1.5), r.choice(((140, 136, 128), (120, 116, 110), (160, 154, 144))), 7, 4, 0.8, 0.2, r)
    M.m('agua')
    for k in range(3):
        y1 = Y_LAWN + 3.2 - k * 1.0; y0 = y1 - 1.0; xx = x - 2.0 + k * 0.9
        M.quad((xx, y1, z - 1.2), (xx, y1, z + 1.2), (xx + 0.15, y0, z + 1.2), (xx + 0.15, y0, z - 1.2), (200, 230, 240), (1, 0.2, 0))
        M.quad((xx - 0.9, y1, z - 1.2), (xx, y1, z - 1.2), (xx, y1, z + 1.2), (xx - 0.9, y1, z + 1.2), (160, 210, 220), (0, 1, 0))
    M.m('liso'); M.cyl(x + 0.6, z, 1.6, WY + 0.01, WY + 0.05, (240, 248, 250), 16)


def reeds(M, r, x, z):
    """touceira de taboa: hastes finas e espigas marrons"""
    M.at(x, z, 'parques'); M.m('liso')
    for k in range(9):
        px, pz = x + r.uniform(-0.8, 0.8), z + r.uniform(-0.8, 0.8); h = r.uniform(1.2, 2.0)
        M.cyl(px, pz, 0.025, WY - 0.05, WY + h, (96, 130, 60), 4, False)
        if k % 2 == 0: M.cyl(px, pz, 0.06, WY + h - 0.35, WY + h - 0.05, (110, 74, 44), 6)
        M.quad((px, WY, pz), (px + 0.05, WY, pz), (px + r.uniform(-0.3, 0.3), WY + h * 0.8, pz + r.uniform(-0.3, 0.3)), (px, WY + h * 0.8, pz), (110, 150, 70), (0, 0, 1))


def lily(M, r, x, z):
    """vitoria-regia: folha redonda com borda levantada e flor rosa"""
    R = r.uniform(0.6, 1.1)
    M.at(x, z, 'parques'); M.m('liso')
    M.cyl(x, z, R, WY + 0.01, WY + 0.03, (70, 130, 60), 14)
    M.cyl(x, z, R, WY + 0.03, WY + 0.09, (110, 60, 50), 14, False, R + 0.02)
    if r.random() < 0.5:
        fx, fz = x + R * 0.3, z - R * 0.2
        for k in range(6):
            a = 2 * math.pi * k / 6; M.sphere(fx + math.cos(a) * 0.12, WY + 0.12, fz + math.sin(a) * 0.12, 0.1, (250, 190, 210), 5, 3, 0.6)
        M.sphere(fx, WY + 0.14, fz, 0.07, (250, 220, 90), 5, 3)


def pavilion(M, x, z, y):
    """pavilhao da ilha: piso de madeira, 6 colunas brancas, telhado em pagode com beiral curvo"""
    M.at(x, z, 'parques'); M.m('madeira'); M.cyl(x, z, 3.2, y, y + 0.25, (170, 128, 88), 6)
    M.m('liso')
    for k in range(6):
        a = 2 * math.pi * k / 6; M.cyl(x + math.cos(a) * 2.8, z + math.sin(a) * 2.8, 0.12, y + 0.25, y + 2.9, (246, 246, 240), 8)
    M.m('telha'); M.cyl(x, z, 4.0, y + 2.9, y + 3.2, (160, 40, 36), 6, True)
    M.cyl(x, z, 3.6, y + 3.2, y + 4.4, (170, 46, 40), 6, False, 0.5); M.m('metal'); M.sphere(x, y + 4.6, z, 0.25, (210, 180, 80), 6, 4)


def red_bridge(M, x, z0, z1):
    """ponte em arco vermelha (estilo jardim oriental): tabuas, longarinas, corrimao com postes e remates"""
    n = 14; L = z1 - z0; rise = 1.6
    yy = lambda t: Y_LAWN + 0.25 + rise * math.sin(math.pi * t)
    M.at(x, (z0 + z1) / 2, 'parques')
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n; a0, a1 = z0 + L * t0, z0 + L * t1
        M.m('madeira'); M.quad((x - 1.3, yy(t0), a0), (x + 1.3, yy(t0), a0), (x + 1.3, yy(t1), a1), (x - 1.3, yy(t1), a1), (176, 128, 84), (0, 1, 0))
        M.quad((x - 1.3, yy(t0) - 0.12, a0), (x + 1.3, yy(t0) - 0.12, a0), (x + 1.3, yy(t1) - 0.12, a1), (x - 1.3, yy(t1) - 0.12, a1), (120, 86, 56), (0, -1, 0))
        M.m('liso')
        for s in (-1, 1):
            M.quad((x + s * 1.3, yy(t0) - 0.35, a0), (x + s * 1.3, yy(t1) - 0.35, a1), (x + s * 1.3, yy(t1), a1), (x + s * 1.3, yy(t0), a0), (190, 40, 36), (s, 0, 0))
            M.quad((x + s * 1.25, yy(t0) + 0.95, a0), (x + s * 1.25, yy(t1) + 0.95, a1), (x + s * 1.25, yy(t1) + 1.05, a1), (x + s * 1.25, yy(t0) + 1.05, a0), (200, 44, 40), (s, 0, 0))
            if k % 2 == 0: M.box(x + s * 1.25 - 0.06, x + s * 1.25 + 0.06, yy(t0), yy(t0) + 1.15, a0 - 0.06, a0 + 0.06, (200, 44, 40))
    # pilares: pares de colunas vermelhas sobre sapata de pedra dentro d'agua, com travessa sob o tabuleiro
    for t in (0.22, 0.4, 0.6, 0.78):
        zc = z0 + L * t; yb = yy(t) - 0.35
        for s in (-1, 1):
            M.m('pedra'); M.cyl(x + s * 1.0, zc, 0.42, WY - 0.9, WY + 0.15, (150, 146, 138), 10)
            M.m('liso'); M.cyl(x + s * 1.0, zc, 0.2, WY + 0.15, yb, (190, 40, 36), 10)
        M.box(x - 1.35, x + 1.35, yb - 0.25, yb + 0.02, zc - 0.16, zc + 0.16, (176, 36, 32))
    # cabeceiras de pedra nas duas pontas (o tabuleiro apoia nelas, sem vao por baixo)
    M.m('pedra')
    for (za, zb) in ((z0 - 0.6, z0 + L * 0.06), (z1 - L * 0.06, z1 + 0.6)):
        M.box(x - 1.45, x + 1.45, WY - 0.9, Y_LAWN + 0.3, za, zb, (176, 170, 160))
    M.m('liso')
    for zz in (z0, z1):
        for s in (-1, 1): M.box(x + s * 1.25 - 0.1, x + s * 1.25 + 0.1, Y_LAWN, Y_LAWN + 1.5, zz - 0.1, zz + 0.1, (200, 44, 40)); M.sphere(x + s * 1.25, Y_LAWN + 1.6, zz, 0.13, (230, 190, 80), 6, 4)


def deck(M, pr, r, lx, lz, RX, RZ, a0, a1):
    """deque curvo que acompanha a margem leste: tabuas sobre a agua (4,5 m para dentro) e encostado na margem,
    acabamento em todo o contorno (testeira de madeira ate a agua, pontas retas no sentido do raio, sem corte torto),
    estacas na agua, guarda-corpo do lado da agua e nas pontas, bancos virados para a lagoa e floreiras."""
    def P(a, off):
        sx, sz = math.cos(a) * RX * (1 + 0.10 * math.sin(3 * a + 0.7)), math.sin(a) * RZ * (1 + 0.12 * math.cos(2 * a))
        rr = math.hypot(sx, sz); f = 1 + off / rr
        return (lx + sx * f, lz + sz * f)
    n = 28; As = [a0 + (a1 - a0) * k / n for k in range(n + 1)]
    yt = Y_LAWN + 0.32; IN, OUT = -4.6, 1.2
    inner = [P(a, IN) for a in As]; outer = [P(a, OUT) for a in As]
    poly = Polygon(outer + inner[::-1])
    M.free('parques'); M.m('madeira'); M.shp(poly, yt, (168, 124, 84))
    for k in range(n):                                              # juntas das tabuas (frisos escuros no sentido do raio)
        if k % 2: continue
        p0, p1 = inner[k], outer[k]
        M.at(*p0, 'parques'); M.quad((p0[0], yt + 0.004, p0[1]), (p1[0], yt + 0.004, p1[1]), (p1[0] + 0.0, yt + 0.004, p1[1] + 0.06), (p0[0], yt + 0.004, p0[1] + 0.06), (120, 86, 56), (0, 1, 0))
    def skirt(a, b, y0):
        M.at((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 'parques'); M.m('madeira')
        M.wall_strip([a, b], y0, yt, 0.12, (140, 100, 66))
    for k in range(n): skirt(inner[k], inner[k + 1], WY - 0.25); skirt(outer[k], outer[k + 1], Y_LAWN - 0.05)
    skirt(inner[0], outer[0], WY - 0.25); skirt(inner[-1], outer[-1], WY - 0.25)
    # estacas e guarda-corpo do lado da agua
    for k in range(0, n + 1, 2):
        q = P(As[k], IN + 0.25); M.at(*q, 'parques'); M.m('madeira')
        M.cyl(q[0], q[1], 0.13, WY - 0.8, yt + 1.05, (130, 92, 60), 8)
    for k in range(n):
        a_, b_ = P(As[k], IN + 0.25), P(As[k + 1], IN + 0.25)
        M.at(*a_, 'parques'); M.m('madeira')
        M.wall_strip([a_, b_], yt + 0.98, yt + 1.08, 0.1, (150, 108, 70)); M.wall_strip([a_, b_], yt + 0.52, yt + 0.58, 0.05, (150, 108, 70))
    for a in (a0, a1):                                               # pontas: guarda-corpo da agua ate a margem
        p0, p1 = P(a, IN + 0.25), P(a, -0.2)
        M.at(*p0, 'parques'); M.m('madeira')
        M.wall_strip([p0, p1], yt + 0.98, yt + 1.08, 0.1, (150, 108, 70)); M.wall_strip([p0, p1], yt + 0.52, yt + 0.58, 0.05, (150, 108, 70))
        M.cyl(p1[0], p1[1], 0.11, Y_LAWN - 0.1, yt + 1.05, (130, 92, 60), 8)
    # bancos (de costas para a margem, olhando a agua), floreiras e lampioes no deque
    for k in range(3, n - 1, 5):
        a = As[k]; q = P(a, -1.2); c = P(a, IN); dx, dz = c[0] - q[0], c[1] - q[1]; l = math.hypot(dx, dz) or 1
        pr.bench(q[0], q[1], dx / l, dz / l, yt)
        f = P(As[k + 2], -0.9); M.at(*f, 'parques'); M.m('madeira'); M.box(f[0] - 0.45, f[0] + 0.45, yt, yt + 0.5, f[1] - 0.45, f[1] + 0.45, (120, 86, 56))
        M.m('liso'); M.box(f[0] - 0.38, f[0] + 0.38, yt + 0.5, yt + 0.52, f[1] - 0.38, f[1] + 0.38, (80, 60, 44)); pr.tree(f[0], f[1], 'flores', 0.9, yt + 0.52)
    M.free('parques')


def pier(M, r, x, z, fauna):
    """pier com pedalinhos de cisne amarrados"""
    M.at(x, z, 'parques'); M.m('madeira')
    M.box(x - 1.4, x + 1.4, Y_LAWN + 0.22, Y_LAWN + 0.32, z - 9.0, z + 0.5, (168, 124, 84))
    for zz in np.arange(z - 9.0, z + 0.5, 1.5):
        for s in (-1, 1): M.cyl(x + s * 1.3, zz, 0.1, WY - 0.6, Y_LAWN + 0.22, (120, 88, 60), 6)
    for k in range(3):
        bx, bz = x + (3.0 if k % 2 else -3.0), z - 2.5 - k * 2.6
        swan_boat(M, bx, bz)


def swan_boat(M, x, z):
    M.at(x, z, 'parques'); M.m('liso')
    M.box(x - 0.8, x + 0.8, WY - 0.1, WY + 0.45, z - 1.2, z + 1.1, (250, 250, 250))
    M.box(x - 0.7, x + 0.7, WY + 0.45, WY + 0.5, z - 0.6, z + 0.9, (40, 140, 200))
    M.sphere(x, WY + 0.6, z + 1.0, 0.45, (250, 250, 250), 8, 5, 0.8)
    for k in range(5): M.sphere(x, WY + 0.8 + k * 0.22, z - 1.0 - math.sin(k * 0.4) * 0.3, 0.16, (250, 250, 250), 6, 4)
    M.sphere(x, WY + 1.95, z - 1.35, 0.2, (250, 250, 250), 6, 4); M.box(x - 0.05, x + 0.05, WY + 1.85, WY + 1.95, z - 1.75, z - 1.5, (250, 140, 30))
    for s in (-1, 1): M.box(x + s * 0.8, x + s * 0.82, WY + 0.2, WY + 0.9, z - 0.5, z + 0.8, (245, 245, 245))


def clock_square(M, pr, r, x, z):
    """Praca do Relogio: piso em mosaico concentrico, canteiros em estrela, torre com 4 mostradores e sino, bancos"""
    M.at(x, z, 'parques')
    for k in range(6):
        R = 15.5 - k * 2.4
        M.m('paver' if k % 2 == 0 else 'pedra'); M.cyl(x, z, R, Y_LAWN + 0.08 + k * 0.004, Y_LAWN + 0.082 + k * 0.004, (236, 226, 208) if k % 2 == 0 else (196, 120, 90), 40)
    for k in range(8):                                        # canteiros em estrela
        a = 2 * math.pi * k / 8 + 0.2; px, pz = x + math.cos(a) * 10.5, z + math.sin(a) * 10.5
        M.m('concreto'); M.cyl(px, pz, 1.8, Y_LAWN + 0.1, Y_LAWN + 0.5, (220, 214, 202), 12); M.m('liso'); M.cyl(px, pz, 1.6, Y_LAWN + 0.5, Y_LAWN + 0.52, (92, 70, 50), 12)
        for q in range(4): b = q * 1.57; pr.tree(px + math.cos(b) * 0.9, pz + math.sin(b) * 0.9, 'flores', 1.0, Y_LAWN + 0.52)
        pr.tree(px, pz, 'arbusto', 0.7, Y_LAWN + 0.52)
        bx, bz = x + math.cos(a + 0.39) * 13.5, z + math.sin(a + 0.39) * 13.5
        pr.bench(bx, bz, -math.cos(a + 0.39), -math.sin(a + 0.39), Y_LAWN + 0.08)
    # torre
    M.m('pedra'); M.box(x - 2.2, x + 2.2, Y_LAWN + 0.08, Y_LAWN + 1.2, z - 2.2, z + 2.2, (190, 182, 168))
    M.m('tijolo'); M.box(x - 1.6, x + 1.6, Y_LAWN + 1.2, Y_LAWN + 10.5, z - 1.6, z + 1.6, (190, 90, 70))
    M.m('concreto')
    for yy in (Y_LAWN + 4.0, Y_LAWN + 7.5): M.box(x - 1.75, x + 1.75, yy, yy + 0.25, z - 1.75, z + 1.75, (230, 224, 212))
    M.box(x - 1.9, x + 1.9, Y_LAWN + 10.5, Y_LAWN + 13.4, z - 1.9, z + 1.9, (236, 230, 218))
    M.m('liso')
    for (dx, dz, nx, nz) in ((0, -1.92, 0, -1), (0, 1.92, 0, 1), (-1.92, 0, -1, 0), (1.92, 0, 1, 0)):
        cxx, czz = x + dx, z + dz; tx, tz = -nz, nx
        M.quad((cxx - tx * 1.1, Y_LAWN + 10.8, czz - tz * 1.1), (cxx + tx * 1.1, Y_LAWN + 10.8, czz + tz * 1.1), (cxx + tx * 1.1, Y_LAWN + 13.0, czz + tz * 1.1), (cxx - tx * 1.1, Y_LAWN + 13.0, czz - tz * 1.1), (60, 50, 40), (nx, 0, nz))
        ox, oz = cxx + nx * 0.02, czz + nz * 0.02
        M.quad((ox - tx * 0.9, Y_LAWN + 11.0, oz - tz * 0.9), (ox + tx * 0.9, Y_LAWN + 11.0, oz + tz * 0.9), (ox + tx * 0.9, Y_LAWN + 12.8, oz + tz * 0.9), (ox - tx * 0.9, Y_LAWN + 12.8, oz - tz * 0.9), (250, 246, 230), (nx, 0, nz))
        ox, oz = cxx + nx * 0.04, czz + nz * 0.04
        M.quad((ox - tx * 0.04, Y_LAWN + 11.9, oz - tz * 0.04), (ox + tx * 0.04, Y_LAWN + 11.9, oz + tz * 0.04), (ox + tx * 0.04, Y_LAWN + 12.6, oz + tz * 0.04), (ox - tx * 0.04, Y_LAWN + 12.6, oz - tz * 0.04), (30, 30, 30), (nx, 0, nz))
        M.quad((ox, Y_LAWN + 11.86, oz), (ox + tx * 0.5, Y_LAWN + 11.86, oz + tz * 0.5), (ox + tx * 0.5, Y_LAWN + 11.94, oz + tz * 0.5), (ox, Y_LAWN + 11.94, oz), (30, 30, 30), (nx, 0, nz))
    M.m('telha'); M.cyl(x, z, 2.6, Y_LAWN + 13.4, Y_LAWN + 16.5, (60, 90, 80), 4, False, 0.05)
    M.m('metal'); M.cyl(x, z, 0.05, Y_LAWN + 16.4, Y_LAWN + 18.0, (200, 170, 80), 5); M.sphere(x, Y_LAWN + 17.0, z, 0.2, (200, 170, 80), 6, 4)
    for s in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        lx_, lz_ = x + s[0] * 5.0, z + s[1] * 5.0; pr.parklight(lx_, lz_, Y_LAWN + 0.08, 'globos5')
    pr.__dict__.setdefault('solids_extra', []).append((x - 2.2, z - 2.2, x + 2.2, z + 2.2))


def bandstand(M, x, z):
    """coreto: base de pedra com escadas, 8 colunas, guarda-corpo com balaustres, telhado octogonal com lanterninha"""
    y = Y_LAWN
    M.at(x, z, 'parques'); M.m('pedra'); M.cyl(x, z, 6.4, y, y + 0.9, (200, 194, 182), 8)
    for k in range(4): M.box(x - 1.2, x + 1.2, y, y + 0.9 - k * 0.22, z + 6.0 + k * 0.35, z + 6.4 + k * 0.35, (210, 204, 192))
    M.m('madeira'); M.cyl(x, z, 6.0, y + 0.9, y + 0.95, (170, 128, 88), 8)
    M.m('liso')
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8; px, pz = x + math.cos(a) * 5.6, z + math.sin(a) * 5.6
        M.cyl(px, pz, 0.16, y + 0.95, y + 4.3, (246, 246, 240), 8)
        b = 2 * math.pi * (k + 1) / 8 + math.pi / 8; qx, qz = x + math.cos(b) * 5.6, z + math.sin(b) * 5.6
        if k != 1:
            M.quad((px, y + 1.85, pz), (qx, y + 1.85, qz), (qx, y + 1.95, qz), (px, y + 1.95, pz), (246, 246, 240), None)
            for t in np.linspace(0.12, 0.88, 6): M.cyl(px + (qx - px) * t, pz + (qz - pz) * t, 0.04, y + 0.95, y + 1.85, (246, 246, 240), 5)
        M.quad((px, y + 4.0, pz), (qx, y + 4.0, qz), (qx, y + 4.3, qz), (px, y + 4.3, pz), (200, 60, 50), None)
    M.m('telha'); M.cyl(x, z, 7.0, y + 4.3, y + 6.6, (60, 110, 90), 8, False, 1.0)
    M.cyl(x, z, 1.0, y + 6.6, y + 7.4, (246, 246, 240), 8); M.cyl(x, z, 1.2, y + 7.4, y + 8.2, (60, 110, 90), 8, False, 0.05)


def playground(M, x, z):
    """parquinho: piso emborrachado, torre com escorregador, balancos, gangorra e trepa-trepa"""
    y = Y_LAWN
    M.at(x, z, 'parques'); M.m('quadra'); M.prism([(x - 12, z - 9), (x + 12, z - 9), (x + 12, z + 9), (x - 12, z + 9)], y, y + 0.08, (60, 140, 120))
    M.m('liso')
    # torre e escorregador
    for (a, b) in ((-1, -1), (1, -1), (1, 1), (-1, 1)): M.box(x - 6 + a * 1.2 - 0.08, x - 6 + a * 1.2 + 0.08, y, y + 3.6, z + b * 1.2 - 0.08, z + b * 1.2 + 0.08, (240, 190, 40))
    M.box(x - 7.3, x - 4.7, y + 1.6, y + 1.7, z - 1.3, z + 1.3, (220, 60, 50)); M.cyl(x - 6, z, 1.9, y + 3.6, y + 4.6, (40, 120, 200), 4, False, 0.1)
    M.quad((x - 4.7, y + 1.7, z - 0.5), (x - 4.7, y + 1.7, z + 0.5), (x - 0.8, y + 0.2, z + 0.5), (x - 0.8, y + 0.2, z - 0.5), (40, 170, 90), (0.36, 0.93, 0))
    # balancos
    for s in (-1, 1): M.box(x + 3 + s * 2.5 - 0.08, x + 3 + s * 2.5 + 0.08, y, y + 2.6, z - 4.5, z - 4.3, (220, 60, 50))
    M.box(x + 0.5, x + 5.5, y + 2.5, y + 2.62, z - 4.5, z - 4.3, (220, 60, 50))
    for k in range(2):
        bx = x + 1.8 + k * 2.4
        for s in (-1, 1): M.box(bx + s * 0.25 - 0.01, bx + s * 0.25 + 0.01, y + 0.5, y + 2.5, z - 4.42, z - 4.38, (60, 60, 64))
        M.box(bx - 0.3, bx + 0.3, y + 0.45, y + 0.52, z - 4.6, z - 4.2, (40, 120, 200))
    # gangorra e trepa-trepa
    M.box(x + 2.0, x + 6.0, y + 0.45, y + 0.55, z + 4.0, z + 4.3, (240, 190, 40)); M.box(x + 3.9, x + 4.1, y, y + 0.45, z + 3.95, z + 4.35, (60, 60, 64))
    for i in range(4):
        for k in range(3): M.box(x + 7.5 + i * 0.8 - 0.04, x + 7.5 + i * 0.8 + 0.04, y, y + 2.0, z + 1.0 + k * 0.8 - 0.04, z + 1.0 + k * 0.8 + 0.04, (40, 170, 90))
    M.box(x + 7.4, x + 10.0, y + 2.0, y + 2.08, z + 0.9, z + 2.7, (40, 170, 90))


def gate(M, x, z, ux, uz):
    """portal de entrada: dois pilares de pedra com luminaria e arco de ferro com o nome do parque"""
    for s in (-1, 1):
        px, pz = x + ux * s * 3.2, z + uz * s * 3.2
        M.at(px, pz, 'parques'); M.m('pedra'); M.box(px - 0.5, px + 0.5, Y_LAWN, Y_LAWN + 3.2, pz - 0.5, pz + 0.5, (196, 188, 172))
        M.m('concreto'); M.box(px - 0.6, px + 0.6, Y_LAWN + 3.2, Y_LAWN + 3.4, pz - 0.6, pz + 0.6, (226, 220, 206))
        M.m('liso'); M.sphere(px, Y_LAWN + 3.7, pz, 0.28, GLOW, 8, 5)
    M.m('metal')
    n = 10
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        a0 = (-1 + 2 * t0) * 3.2; a1 = (-1 + 2 * t1) * 3.2
        y0 = Y_LAWN + 3.6 + 0.9 * math.sin(math.pi * t0); y1 = Y_LAWN + 3.6 + 0.9 * math.sin(math.pi * t1)
        M.quad((x + ux * a0, y0, z + uz * a0), (x + ux * a1, y1, z + uz * a1), (x + ux * a1, y1 + 0.12, z + uz * a1), (x + ux * a0, y0 + 0.12, z + uz * a0), (40, 60, 50), None)
    M.m('liso'); M.quad((x - ux * 2.0, Y_LAWN + 3.9, z - uz * 2.0), (x + ux * 2.0, Y_LAWN + 3.9, z + uz * 2.0), (x + ux * 2.0, Y_LAWN + 4.4, z + uz * 2.0), (x - ux * 2.0, Y_LAWN + 4.4, z - uz * 2.0), (40, 90, 60), None)


# ======================================================================== areas de convivencia
def _F(x, z, ang): return Frame((x, z), (math.cos(ang), math.sin(ang)))


def checker(M, F, u0, u1, v0, v1, y, nu, nv, c1, c2):
    du, dv = (u1 - u0) / nu, (v1 - v0) / nv
    for i in range(nu):
        for k in range(nv):
            a, b = u0 + i * du, v0 + k * dv
            M.poly([F.p(a, b, y), F.p(a + du, b, y), F.p(a + du, b + dv, y), F.p(a, b + dv, y)], c1 if (i + k) % 2 == 0 else c2, (0, 1, 0))


def picnic_table(M, F, cloth=None):
    """mesa de piquenique de madeira com bancos presos (estrutura em A), toalha xadrez, cesta e pratos"""
    y = Y_LAWN; wd = (164, 118, 74); dk = (128, 90, 56)
    M.m('madeira')
    M.prism(F.rect(-0.95, 0.95, -0.42, 0.42), y + 0.72, y + 0.77, wd)
    for s in (-1, 1): M.prism(F.rect(-0.95, 0.95, s * 0.58 - 0.15, s * 0.58 + 0.15), y + 0.42, y + 0.46, wd)
    for u in (-0.7, 0.7):
        for s in (-1, 1):
            M.poly([F.p(u - 0.05, s * 0.78, y), F.p(u + 0.05, s * 0.78, y), F.p(u + 0.05, s * 0.05, y + 0.72), F.p(u - 0.05, s * 0.05, y + 0.72)], dk, None)
        M.prism(F.rect(u - 0.05, u + 0.05, -0.75, 0.75), y + 0.36, y + 0.42, dk)
    if cloth:
        M.m('liso'); checker(M, F, -0.8, 0.8, -0.48, 0.48, y + 0.775, 8, 5, cloth, (250, 250, 248))
        M.m('madeira'); M.prism(F.rect(-0.55, -0.2, -0.15, 0.12), y + 0.775, y + 0.98, (190, 150, 90))
        M.prism(F.rect(-0.39, -0.36, -0.15, 0.12), y + 0.98, y + 1.12, (150, 110, 70))
        M.m('liso')
        for (u, v) in ((0.25, -0.22), (0.55, 0.2), (0.1, 0.25)):
            x, z = F.xz(u, v); M.cyl(x, z, 0.12, y + 0.78, y + 0.79, (250, 250, 250), 10)
        x, z = F.xz(0.35, -0.05); M.cyl(x, z, 0.04, y + 0.78, y + 1.04, (60, 150, 80), 6)


def blanket(M, F, col):
    """toalha de piquenique estendida no gramado com cesta, almofadas e garrafa"""
    y = Y_LAWN + 0.025
    M.m('liso'); checker(M, F, -1.0, 1.0, -0.8, 0.8, y, 6, 5, col, (250, 248, 240))
    M.m('madeira'); M.prism(F.rect(0.3, 0.75, -0.55, -0.2), y, y + 0.28, (196, 156, 96)); M.prism(F.rect(0.5, 0.55, -0.55, -0.2), y + 0.28, y + 0.42, (150, 110, 70))
    M.m('liso')
    for (u, v, c) in ((-0.7, 0.55, (240, 200, 60)), (-0.35, 0.6, (90, 160, 210))): M.prism(F.rect(u - 0.18, u + 0.18, v - 0.12, v + 0.12), y, y + 0.12, c)
    x, z = F.xz(-0.2, -0.3); M.cyl(x, z, 0.035, y, y + 0.28, (200, 60, 50), 6)
    x, z = F.xz(0.1, 0.1); M.cyl(x, z, 0.16, y, y + 0.015, (250, 250, 250), 10)


def parasol(M, x, z, col, y=Y_LAWN, h=2.4, rr=1.4):
    M.m('metal'); M.cyl(x, z, 0.035, y, y + h, (230, 230, 230), 6); M.cyl(x, z, 0.25, y, y + 0.06, (90, 90, 96), 8)
    M.m('liso'); M.cyl(x, z, rr, y + h - 0.45, y + h, col, 8, False, 0.05)


def grill(M, x, z):
    """churrasqueira de tijolinho com grelha e chamine"""
    y = Y_LAWN
    M.m('tijolo'); M.box(x - 0.8, x + 0.8, y, y + 0.9, z - 0.45, z + 0.45, (176, 84, 60))
    M.box(x - 0.8, x + 0.8, y + 0.9, y + 1.5, z + 0.3, z + 0.45, (176, 84, 60)); M.box(x - 0.25, x + 0.25, y + 1.5, y + 2.4, z + 0.05, z + 0.45, (176, 84, 60))
    M.m('metal'); M.box(x - 0.65, x + 0.65, y + 0.9, y + 0.93, z - 0.35, z + 0.3, (40, 40, 44))


def picnic_area(M, pr, r, x, z, rw, rd, chess=False):
    """clareira de piquenique: mesas com toalha e guarda-sol, toalhas no gramado, churrasqueiras, lixeiras e bebedouro;
    com chess=True tambem mesas de xadrez de concreto. Devolve a area ocupada (sem arvore nela)."""
    M.at(x, z, 'parques')
    cloths = ((200, 50, 50), (50, 110, 190), (60, 150, 80), (230, 150, 40))
    k = 0
    for i in (-1, 0, 1):
        for jj in (-1, 1):
            tx, tz = x + i * rw * 0.3, z + jj * rd * 0.28
            F = _F(tx, tz, 0.0 if (i + jj) % 2 else 0.12); M.at(tx, tz, 'parques'); picnic_table(M, F, cloths[k % 4])
            if k % 2 == 0: parasol(M, tx, tz, cloths[(k + 1) % 4], h=2.5)
            k += 1
    for q in range(4):
        bx, bz = x + r.uniform(-rw * 0.45, rw * 0.45), z + r.uniform(-0.12, 0.12) * rd
        M.at(bx, bz, 'parques'); blanket(M, _F(bx, bz, r.uniform(0, 3.1)), cloths[(q + 2) % 4])
    for s in (-1, 1):
        M.at(x + s * rw * 0.48, z - rd * 0.42, 'parques'); grill(M, x + s * rw * 0.48, z - rd * 0.42)
        M.m('metal'); M.cyl(x + s * rw * 0.48 + 1.6 * s, z - rd * 0.42, 0.28, Y_LAWN, Y_LAWN + 0.95, (46, 80, 60), 8)
    M.at(x, z + rd * 0.5, 'parques'); M.m('concreto'); M.cyl(x, z + rd * 0.5, 0.25, Y_LAWN, Y_LAWN + 0.9, (200, 200, 196), 8); M.cyl(x, z + rd * 0.5, 0.35, Y_LAWN + 0.9, Y_LAWN + 1.0, (200, 200, 196), 10)
    M.m('metal'); M.cyl(x, z + rd * 0.5, 0.03, Y_LAWN + 1.0, Y_LAWN + 1.12, (180, 180, 186), 6)
    if chess:
        for q in range(3):
            cx_, cz_ = x - rw * 0.3 + q * rw * 0.3, z + rd * 0.72
            M.at(cx_, cz_, 'parques'); M.m('liso'); M.cyl(cx_, cz_, 0.18, Y_LAWN, Y_LAWN + 0.7, (196, 194, 188), 8); M.box(cx_ - 0.45, cx_ + 0.45, Y_LAWN + 0.7, Y_LAWN + 0.76, cz_ - 0.45, cz_ + 0.45, (210, 208, 202))
            M.m('liso'); checker(M, _F(cx_, cz_, 0), -0.32, 0.32, -0.32, 0.32, Y_LAWN + 0.762, 8, 8, (40, 40, 40), (240, 236, 226))
            for s in (-1, 1): M.m('liso'); M.cyl(cx_ + s * 0.85, cz_, 0.2, Y_LAWN, Y_LAWN + 0.45, (196, 194, 188), 8)
    M.free()
    return Polygon([(x - rw / 2 - 2, z - rd / 2 - 2), (x + rw / 2 + 2, z - rd / 2 - 2), (x + rw / 2 + 2, z + rd / 2 + (4 if chess else 2)), (x - rw / 2 - 2, z + rd / 2 + (4 if chess else 2))])


def cafe(M, pr, r, x, z):
    """Cafe da Lagoa: patio de piso, quiosque com balcao, toldo listrado, cardapio, mesas com guarda-sol e cadeiras"""
    y = Y_LAWN
    M.at(x, z, 'parques'); M.m('paver'); M.cyl(x, z, 11.0, y + 0.075, y + 0.09, (226, 214, 196), 32)
    M.m('pedra'); M.cyl(x, z, 11.2, y, y + 0.075, (190, 182, 168), 32, False)
    # quiosque (fundo ao norte), aberto para o sul
    kx, kz = x, z - 5.5
    M.m('madeira'); M.box(kx - 3.2, kx + 3.2, y + 0.09, y + 2.9, kz - 2.0, kz - 1.8, (238, 232, 220))
    for s in (-1, 1): M.box(kx + s * 3.2 - 0.2 * (s > 0), kx + s * 3.2 + 0.2 * (s < 0), y + 0.09, y + 2.9, kz - 2.0, kz + 1.6, (238, 232, 220))
    M.box(kx - 3.0, kx + 3.0, y + 0.09, y + 1.05, kz + 1.4, kz + 1.6, (60, 120, 90))
    M.m('liso'); M.box(kx - 3.1, kx + 3.1, y + 1.05, y + 1.1, kz + 1.2, kz + 1.8, (70, 70, 74))
    M.m('metal'); M.box(kx - 2.6, kx - 1.0, y + 0.09, y + 1.0, kz - 1.8, kz - 1.2, (196, 200, 206)); M.box(kx - 2.4, kx - 1.8, y + 1.0, y + 1.45, kz - 1.7, kz - 1.3, (60, 60, 64))
    M.box(kx + 1.0, kx + 2.9, y + 0.09, y + 1.9, kz - 1.8, kz - 1.2, (220, 224, 228)); M.m('vidro'); M.box(kx + 1.1, kx + 2.8, y + 0.4, y + 1.8, kz - 1.21, kz - 1.19, (180, 210, 225))
    M.m('telha'); M.box(kx - 3.6, kx + 3.6, y + 2.9, y + 3.1, kz - 2.4, kz + 2.0, (120, 80, 60))
    for (za, zb, nz) in ((kz - 2.4, kz - 0.2, -1), (kz + 2.0, kz - 0.2, 1)):          # telhado de duas aguas
        M.quad((kx - 3.6, y + 3.1, za), (kx + 3.6, y + 3.1, za), (kx + 3.6, y + 4.1, zb), (kx - 3.6, y + 4.1, zb), (130, 86, 64), None)
    M.m('madeira')
    for sx in (-1, 1): M.poly([(kx + sx * 3.2, y + 3.1, kz - 1.9), (kx + sx * 3.2, y + 3.1, kz + 1.5), (kx + sx * 3.2, y + 3.95, kz - 0.2)], (238, 232, 220), (sx, 0, 0))
    M.m('liso')                                                          # toldo listrado
    for i in range(8):
        a = kx - 3.4 + i * 0.85
        M.quad((a, y + 2.85, kz + 1.8), (a + 0.85, y + 2.85, kz + 1.8), (a + 0.85, y + 2.25, kz + 3.0), (a, y + 2.25, kz + 3.0), (230, 70, 60) if i % 2 == 0 else (250, 246, 236), None)
    M.m('liso'); M.box(kx - 1.4, kx + 1.4, y + 3.15, y + 3.75, kz + 1.95, kz + 2.05, (40, 90, 60))
    M.box(kx - 1.25, kx + 1.25, y + 3.25, y + 3.65, kz + 2.05, kz + 2.06, (250, 236, 200))
    M.box(kx + 3.6, kx + 3.65, y + 0.09, y + 1.4, kz + 2.0, kz + 2.8, (40, 40, 44)); M.box(kx + 3.66, kx + 3.67, y + 0.5, y + 1.3, kz + 2.1, kz + 2.7, (240, 236, 220))
    pr.L.B.colliders.append([round(kx, 2), round(kz - 0.2, 2), 1.0, 0.0, 3.3, 1.9]) if hasattr(pr.L, 'B') else None
    # mesas no patio
    cols = ((230, 70, 60), (60, 140, 200), (240, 190, 50), (80, 160, 90))
    k = 0
    for (dx, dz) in ((-6.0, 1.5), (-2.5, 4.5), (2.5, 4.5), (6.0, 1.5), (0.0, 8.0), (-5.0, 6.8), (5.0, 6.8)):
        tx, tz = x + dx, z + dz
        M.m('metal'); M.cyl(tx, tz, 0.05, y + 0.09, y + 0.74, (60, 60, 64), 6); M.cyl(tx, tz, 0.3, y + 0.09, y + 0.12, (60, 60, 64), 8)
        M.m('madeira'); M.cyl(tx, tz, 0.45, y + 0.74, y + 0.78, (190, 150, 100), 12)
        for q in range(3):
            a = q * 2.09 + k; cx_, cz_ = tx + math.cos(a) * 0.8, tz + math.sin(a) * 0.8
            Fc = _F(cx_, cz_, a + math.pi / 2)            # v local aponta para fora da mesa (encosto do lado de fora)
            M.m('metal'); M.prism(Fc.rect(-0.2, 0.2, -0.2, 0.2), y + 0.44, y + 0.48, cols[(k + q) % 4])
            for (eu, ev) in ((-0.17, -0.17), (0.17, -0.17), (0.17, 0.17), (-0.17, 0.17)): M.prism(Fc.rect(eu - 0.015, eu + 0.015, ev - 0.015, ev + 0.015), y + 0.09, y + 0.44, (60, 60, 64))
            M.prism(Fc.rect(-0.2, 0.2, 0.17, 0.2), y + 0.48, y + 0.9, cols[(k + q) % 4])
        parasol(M, tx, tz, cols[k % 4], y + 0.78, 1.7, 1.3)
        k += 1
    for (dx, dz) in ((-9.5, -2.0), (9.5, -2.0)):
        M.m('concreto'); M.box(x + dx - 0.5, x + dx + 0.5, y + 0.09, y + 0.6, z + dz - 0.5, z + dz + 0.5, (210, 206, 198)); pr.tree(x + dx, z + dz, 'flores', 1.0, y + 0.6)
    M.free()
    return Point(x, z).buffer(13.0)


def pergola(M, x, z, ang, L=14.0, wd=3.6):
    """pergolado de madeira (pilares, vigas e caibros) com trepadeira florida por cima e bancos dos dois lados"""
    F = _F(x, z, ang); y = Y_LAWN; wd_ = (150, 108, 70)
    M.at(x, z, 'parques'); M.m('paver'); M.prism(F.rect(-L / 2 - 0.5, L / 2 + 0.5, -wd / 2 - 0.5, wd / 2 + 0.5), y, y + 0.08, (226, 214, 196))
    M.m('madeira')
    n = int(L / 3.5)
    for i in range(n + 1):
        u = -L / 2 + i * L / n
        for s in (-1, 1): M.prism(F.rect(u - 0.12, u + 0.12, s * wd / 2 - 0.12, s * wd / 2 + 0.12), y + 0.08, y + 2.7, wd_)
        M.prism(F.rect(u - 0.06, u + 0.06, -wd / 2 - 0.5, wd / 2 + 0.5), y + 2.7, y + 2.92, wd_)
    for s in (-1, 1): M.prism(F.rect(-L / 2 - 0.4, L / 2 + 0.4, s * wd / 2 - 0.08, s * wd / 2 + 0.08), y + 2.5, y + 2.7, wd_)
    q = -L / 2
    while q < L / 2:
        M.prism(F.rect(-L / 2 - 0.3, L / 2 + 0.3, -0.03, 0.03), y + 2.92, y + 3.0, wd_) if False else None
        q += 0.6
    for k in range(int(L / 0.6)):
        u = -L / 2 + 0.3 + k * 0.6; M.prism(F.rect(u - 0.03, u + 0.03, -wd / 2 - 0.3, wd / 2 + 0.3), y + 2.92, y + 3.0, wd_)
    M.m('folhagem')
    for k in range(int(L / 1.4)):
        u = -L / 2 + 0.7 + k * 1.4
        for v in (-wd / 4, wd / 4):
            px, pz = F.xz(u + (k % 2) * 0.2, v); M.sphere(px, y + 3.05, pz, 0.85, (70, 130, 60) if k % 3 else (190, 80, 150), 7, 3, 0.35)
    M.m('madeira')
    for i in range(n):
        u = -L / 2 + (i + 0.5) * L / n
        for s in (-1, 1):
            M.prism(F.rect(u - 0.8, u + 0.8, s * (wd / 2 - 0.5) - 0.22, s * (wd / 2 - 0.5) + 0.22), y + 0.42, y + 0.47, (176, 128, 84))
            M.prism(F.rect(u - 0.8, u + 0.8, s * (wd / 2 - 0.3) - 0.04, s * (wd / 2 - 0.3) + 0.04), y + 0.47, y + 0.9, (176, 128, 84))
            for uu in (u - 0.65, u + 0.65): M.prism(F.rect(uu - 0.04, uu + 0.04, s * (wd / 2 - 0.5) - 0.2, s * (wd / 2 - 0.5) + 0.2), y + 0.08, y + 0.42, (90, 90, 96))
    M.free()
    return F


def rose_garden(M, pr, r, x, z):
    """roseiral: canteiros redondos com borda de buxo e rosas, bebedouro de passaros no meio, pergolado ao lado"""
    M.at(x, z, 'parques'); M.m('paver'); M.cyl(x, z, 9.5, Y_LAWN + 0.075, Y_LAWN + 0.09, (232, 222, 204), 32)
    M.m('pedra'); M.cyl(x, z, 0.5, Y_LAWN + 0.09, Y_LAWN + 0.9, (220, 214, 200), 10); M.cyl(x, z, 0.9, Y_LAWN + 0.9, Y_LAWN + 1.05, (220, 214, 200), 14)
    M.m('agua'); M.cyl(x, z, 0.75, Y_LAWN + 1.05, Y_LAWN + 1.06, (150, 200, 215), 14)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3; px, pz = x + math.cos(a) * 5.6, z + math.sin(a) * 5.6
        M.m('concreto'); M.cyl(px, pz, 2.2, Y_LAWN + 0.09, Y_LAWN + 0.35, (214, 208, 196), 16); M.m('liso'); M.cyl(px, pz, 2.0, Y_LAWN + 0.35, Y_LAWN + 0.37, (92, 70, 50), 16)
        for q in range(6): b = 2 * math.pi * q / 6 + k; pr.tree(px + math.cos(b) * 1.3, pz + math.sin(b) * 1.3, 'flores', 1.1, Y_LAWN + 0.37)
        pr.tree(px, pz, 'arbusto', 0.75, Y_LAWN + 0.37)
        bx, bz = x + math.cos(a + 0.52) * 8.3, z + math.sin(a + 0.52) * 8.3
        pr.bench(bx, bz, -math.cos(a + 0.52), -math.sin(a + 0.52), Y_LAWN + 0.09)
    pergola(M, x, z + 15.5, 0.0, 16.0, 3.6)
    for s in (-1, 1): pr.parklight(x + s * 11.2, z + 15.5, Y_LAWN, 'globos')
    M.free()
    return unary_union([Point(x, z).buffer(11.0), Polygon([(x - 10, z + 12.5), (x + 10, z + 12.5), (x + 10, z + 18.5), (x - 10, z + 18.5)])])


def gym(M, pr, x, z):
    """academia ao ar livre: piso emborrachado, barras, simulador de caminhada, pranchas, bicicleta, placa de uso"""
    y = Y_LAWN; yy = y + 0.08
    M.at(x, z, 'parques'); M.m('liso'); M.prism([(x - 9, z - 6), (x + 9, z - 6), (x + 9, z + 6), (x - 9, z + 6)], y, yy, (190, 90, 60))
    M.m('metal'); C = (40, 120, 200); Y_ = (240, 190, 40)
    # barras paralelas e barra fixa
    for s in (-1, 1):
        for zz in (z - 4.5, z - 2.5): M.cyl(x - 6 + s * 0.3, zz, 0.05, yy, yy + 1.2, C, 6)
        M.box(x - 6 + s * 0.3 - 0.03, x - 6 + s * 0.3 + 0.03, yy + 1.15, yy + 1.22, z - 4.6, z - 2.4, Y_)
    for xx in (x - 2.0, x + 0.2): M.cyl(xx, z - 3.5, 0.06, yy, yy + 2.3, C, 6)
    M.box(x - 2.0, x + 0.2, yy + 2.22, yy + 2.28, z - 3.53, z - 3.47, Y_)
    # simuladores (coluna central com dois pares de pedais/bracos)
    for (ex, ez) in ((x + 3.5, z - 3.2), (x + 6.5, z - 3.2), (x - 4.0, z + 3.0), (x + 0.5, z + 3.0), (x + 5.0, z + 3.0)):
        M.cyl(ex, ez, 0.09, yy, yy + 1.6, C, 8); M.box(ex - 0.55, ex + 0.55, yy + 1.45, yy + 1.55, ez - 0.05, ez + 0.05, C)
        for s in (-1, 1):
            M.box(ex + s * 0.5 - 0.03, ex + s * 0.5 + 0.03, yy + 0.25, yy + 1.5, ez - 0.03, ez + 0.03, Y_)
            M.box(ex + s * 0.5 - 0.15, ex + s * 0.5 + 0.15, yy + 0.25, yy + 0.29, ez - 0.25, ez + 0.25, (60, 60, 64))
    M.m('liso'); M.box(x + 8.4, x + 8.5, yy, yy + 1.9, z + 5.0, z + 5.2, (60, 60, 64)); M.box(x + 7.6, x + 9.3, yy + 1.0, yy + 1.9, z + 5.2, z + 5.22, (40, 120, 70))
    for s in (-1, 1): pr.bench(x + s * 10.4, z, -s, 0, Y_LAWN)
    M.free()
    return Polygon([(x - 12, z - 8), (x + 12, z - 8), (x + 12, z + 8), (x - 12, z + 8)])


def east_corner(M, pr, r, x, z):
    """canto leste: carrinho de sorvete com guarda-sol, bicicletario, gramado de toalhas e redario entre arvores"""
    y = Y_LAWN
    M.at(x, z, 'parques'); M.m('paver'); M.prism([(x - 4, z - 9), (x + 4, z - 9), (x + 4, z - 3), (x - 4, z - 3)], y + 0.075, y + 0.09, (226, 214, 196))
    cx_, cz_ = x, z - 6.0; yy = y + 0.09
    M.m('liso'); M.box(cx_ - 0.9, cx_ + 0.9, yy + 0.35, yy + 1.1, cz_ - 0.5, cz_ + 0.5, (250, 250, 246)); M.box(cx_ - 0.9, cx_ + 0.9, yy + 0.7, yy + 0.8, cz_ + 0.5, cz_ + 0.51, (240, 120, 160))
    M.m('metal')
    for s in (-1, 1): M.cyl(cx_ + s * 0.6, cz_ - 0.55, 0.3, yy, yy + 0.6, (40, 40, 44), 10)
    M.cyl(cx_ + 0.8, cz_ + 0.6, 0.05, yy + 0.3, yy + 0.35, (40, 40, 44), 6)
    parasol(M, cx_, cz_, (240, 120, 160), yy + 1.1, 1.3, 1.2)
    for k in range(6):                                                    # bicicletario
        bx = x - 3.2 + k * 0.7; M.cyl(bx, z - 3.6, 0.03, yy, yy + 0.8, (160, 164, 170), 5); M.box(bx - 0.02, bx + 0.02, yy + 0.75, yy + 0.8, z - 3.9, z - 3.3, (160, 164, 170))
    for q in range(2):
        bx, bz = x + r.uniform(-3, 3), z + 2 + q * 4.5
        M.at(bx, bz, 'parques'); blanket(M, _F(bx, bz, r.uniform(0, 3)), ((200, 50, 50), (60, 150, 80))[q])
    M.free()
    return Polygon([(x - 6, z - 10), (x + 6, z - 10), (x + 6, z + 10), (x - 6, z + 10)])
