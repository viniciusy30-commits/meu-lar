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
from mesh import shade, WHITE

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
        a = r.uniform(-2.6, -0.4); px, pz = lx + math.cos(a) * RX * 1.02, lz + math.sin(a) * RZ * 1.05
        M.at(px, pz, 'parques'); M.m('pedra'); M.sphere(px, Y_LAWN + 0.05, pz, r.uniform(0.5, 1.3), r.choice(((150, 146, 138), (128, 124, 118), (170, 164, 152))), 7, 4, 0.6, 0.2, r)
    cascade(M, r, lx - RX * 0.98, lz - 4, fauna)
    # taboas e vitorias-regias
    for k in range(10):
        a = r.uniform(0.3, 2.4); bx, bz = lx + math.cos(a) * RX * 0.93, lz + math.sin(a) * RZ * 0.9
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
    deck(M, pr, r, lake, lx + RX * 0.55, lz - RZ * 0.85, lx + RX * 1.02, lz + RZ * 0.2)
    pier(M, r, lx + RX * 0.35, lz + RZ * 0.98, fauna)
    # ---------------- repuxo
    fx, fz = lx + RX * 0.4, lz - RZ * 0.05
    M.at(fx, fz, 'parques'); M.m('pedra'); M.cyl(fx, fz, 1.4, WY - 0.2, WY + 0.25, (200, 196, 188), 16)
    M.m('liso'); M.cyl(fx, fz, 0.12, WY + 0.25, WY + 7.5, (235, 245, 250), 8, True, 0.04); M.cyl(fx, fz, 1.6, WY + 0.02, WY + 0.6, (230, 242, 248), 12, False, 0.2)
    for k in range(10):
        a = 2 * math.pi * k / 10; M.cyl(fx + math.cos(a) * 1.0, fz + math.sin(a) * 1.0, 0.05, WY + 0.25, WY + 2.6, (230, 242, 248), 6, True, 0.02)
    # ---------------- praca do relogio, coreto, playground, portais
    clock_square(M, pr, r, *rel)
    bandstand(M, *cor)
    playground(M, *ply)
    for (gx, gz) in ((minx + 2.5, minz + 2.5), (maxx - 2.5, maxz - 2.5), (minx + 2.5, maxz - 2.5), (maxx - 2.5, minz + 2.5)):
        dx, dz = (cx - gx), (cz - gz); L = math.hypot(dx, dz); gate(M, gx + dx / L * 4, gz + dz / L * 4, -dz / L, dx / L)
    # ---------------- plantio: chorao e palmeiras na margem, bosques por especie, canteiros nas bordas dos caminhos
    occ = unary_union([lake.buffer(7), pth.buffer(1.8), Point(*rel).buffer(19), Point(*cor).buffer(13), Point(*ply).buffer(16), isl.buffer(2)])
    for k in range(16):
        a = 2 * math.pi * k / 16 + 0.2; px, pz = lx + math.cos(a) * (RX + 14), lz + math.sin(a) * (RZ + 14)
        if poly.buffer(-4).contains(Point(px, pz)) and not pth.buffer(2.5).contains(Point(px, pz)): pr.tree(px, pz, 'palmeira' if k % 3 else 'folhosa', r.uniform(1.0, 1.35))
    groves = [('florida', (minx + W_ * 0.15, minz + D_ * 0.15)), ('conifera', (minx + W_ * 0.12, minz + D_ * 0.5)), ('oval', (minx + W_ * 0.5, minz + D_ * 0.9)),
              ('folhosa', (maxx - W_ * 0.12, minz + D_ * 0.5)), ('ornamental', (minx + W_ * 0.42, minz + D_ * 0.12))]
    for (sp, (gx, gz)) in groves:
        for k in range(18):
            px, pz = gx + r.gauss(0, 10), gz + r.gauss(0, 10)
            if poly.buffer(-4).contains(Point(px, pz)) and not occ.contains(Point(px, pz)): pr.tree(px, pz, sp, r.uniform(0.9, 1.25)); occ = occ.union(Point(px, pz).buffer(4.5))
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
        M.m('liso')
        for s in (-1, 1):
            M.quad((x + s * 1.3, yy(t0) - 0.35, a0), (x + s * 1.3, yy(t1) - 0.35, a1), (x + s * 1.3, yy(t1), a1), (x + s * 1.3, yy(t0), a0), (190, 40, 36), (s, 0, 0))
            M.quad((x + s * 1.25, yy(t0) + 0.95, a0), (x + s * 1.25, yy(t1) + 0.95, a1), (x + s * 1.25, yy(t1) + 1.05, a1), (x + s * 1.25, yy(t0) + 1.05, a0), (200, 44, 40), (s, 0, 0))
            if k % 2 == 0: M.box(x + s * 1.25 - 0.06, x + s * 1.25 + 0.06, yy(t0), yy(t0) + 1.15, a0 - 0.06, a0 + 0.06, (200, 44, 40))
    for zz in (z0, z1):
        for s in (-1, 1): M.box(x + s * 1.25 - 0.1, x + s * 1.25 + 0.1, Y_LAWN, Y_LAWN + 1.5, zz - 0.1, zz + 0.1, (200, 44, 40)); M.sphere(x + s * 1.25, Y_LAWN + 1.6, zz, 0.13, (230, 190, 80), 6, 4)


def deck(M, pr, r, lake, u0, v0, u1, v1):
    """deque de madeira sobre a agua junto da margem leste, com guarda-corpo do lado da agua e bancos"""
    box = Polygon([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    dk = box.intersection(lake.buffer(3.0)).difference(lake.buffer(-6.0))
    M.free('parques'); M.m('madeira'); M.shp(dk, Y_LAWN + 0.32, (168, 124, 84))
    inner = lake.buffer(-6.0).exterior.intersection(box)
    for g in getattr(inner, 'geoms', [inner]):
        cs = list(g.coords) if hasattr(g, 'coords') else []
        for k in range(len(cs) - 1):
            a, b = cs[k], cs[k + 1]
            M.at((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 'parques'); M.m('madeira')
            M.quad((a[0], Y_LAWN + 1.2, a[1]), (b[0], Y_LAWN + 1.2, b[1]), (b[0], Y_LAWN + 1.3, b[1]), (a[0], Y_LAWN + 1.3, a[1]), (150, 108, 70), None)
            M.box(a[0] - 0.06, a[0] + 0.06, Y_LAWN + 0.32, Y_LAWN + 1.3, a[1] - 0.06, a[1] + 0.06, (150, 108, 70))
    for k in range(int(dk.area / 40)):
        p = dk.representative_point()
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
