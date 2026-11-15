"""Cidade 6 - equipamentos de parque/praca (quadras, playground, quiosque, coreto, jardim, lago, pista de skate...).
Cada equipamento e desenhado num Frame centrado (a = comprimento, b = largura) e devolve nada; a tabela STATIONS
da o meio-comprimento e a meia-largura de cada um para quem distribui (parque ribeirinho, pracas, escolas)."""
import math
from mesh import Frame, shade
from roads6 import Y_LAWN

WHITE = (255, 255, 255)
Y = Y_LAWN
TOY = ((222, 62, 52), (44, 122, 204), (242, 192, 42), (60, 170, 90), (240, 130, 40))
STEEL = (70, 74, 80)


def _pad(M, F, a, b, mat, col, h=0.08):
    M.m(mat); M.prism(F.rect(-a, a, -b, b), Y, Y + h, col)


def _post(M, F, u, v, y0, y1, col=STEEL, t=0.06):
    M.prism(F.rect(u - t, u + t, v - t, v + t), y0, y1, col)


def _bar(M, F, u0, v0, u1, v1, y, col=STEEL, t=0.05):
    """barra horizontal fina entre dois pontos do frame"""
    if abs(u1 - u0) >= abs(v1 - v0): M.prism(F.rect(min(u0, u1), max(u0, u1), v0 - t, v0 + t), y - t, y + t, col)
    else: M.prism(F.rect(u0 - t, u0 + t, min(v0, v1), max(v0, v1)), y - t, y + t, col)


def _lines(M, F, segs, y, w=0.06, col=(250, 250, 246)):
    M.m('liso')
    for (u0, v0, u1, v1) in segs:
        if abs(u1 - u0) >= abs(v1 - v0): M.prism(F.rect(min(u0, u1), max(u0, u1), v0 - w, v0 + w), y, y + 0.03, col, True)
        else: M.prism(F.rect(u0 - w, u0 + w, min(v0, v1), max(v0, v1)), y, y + 0.03, col, True)


def _fence(M, F, a, b, h=3.0, gap=None):
    """alambrado: postes e duas barras (sem tela, para nao piscar)"""
    M.m('metal')
    pts = []
    n = max(2, int(2 * a / 3.5)); m = max(2, int(2 * b / 3.5))
    for i in range(n + 1): pts += [(-a + 2 * a * i / n, -b), (-a + 2 * a * i / n, b)]
    for j in range(1, m): pts += [(-a, -b + 2 * b * j / m), (a, -b + 2 * b * j / m)]
    for (u, v) in pts:
        if gap and abs(u - gap[0]) < 1.6 and abs(v - gap[1]) < 0.3: continue
        _post(M, F, u, v, Y, Y + h, (86, 96, 92), 0.045)
    for yy in (Y + h, Y + h * 0.5):
        for (u0, v0, u1, v1) in ((-a, -b, a, -b), (-a, b, a, b), (-a, -b, -a, b), (a, -b, a, b)): _bar(M, F, u0, v0, u1, v1, yy, (86, 96, 92), 0.035)


def basket(pr, F, r):
    M = pr.M; _pad(M, F, 15, 9, 'quadra', (205, 122, 92))
    y = Y + 0.08
    _lines(M, F, [(-14, -8, 14, -8), (-14, 8, 14, 8), (-14, -8, -14, 8), (14, -8, 14, 8), (0, -8, 0, 8), (-14, -2.4, -8.2, -2.4), (-14, 2.4, -8.2, 2.4), (-8.2, -2.4, -8.2, 2.4), (14, -2.4, 8.2, -2.4), (14, 2.4, 8.2, 2.4), (8.2, -2.4, 8.2, 2.4)], y)
    M.m('liso'); M.cyl(*F.xz(0, 0), 1.8, y, y + 0.025, (236, 200, 150), 14)
    for s in (-1, 1):
        M.m('metal'); _post(M, F, s * 14.6, 0, Y, Y + 3.3, STEEL, 0.09); _bar(M, F, s * 14.6, 0, s * 13.4, 0, Y + 3.25, STEEL, 0.06)
        M.m('liso'); M.prism(F.rect(s * 13.4 - 0.04, s * 13.4 + 0.04, -0.9, 0.9), Y + 2.9, Y + 3.95, (245, 245, 245))
        M.cyl(*F.xz(s * 13.05, 0), 0.24, Y + 3.03, Y + 3.07, (230, 90, 40), 8)
    _fence(M, F, 15.6, 9.6, 3.0, (0, -9.6))


def futsal(pr, F, r):
    M = pr.M; _pad(M, F, 17, 10, 'quadra', r.choice(((92, 150, 196), (96, 168, 120))))
    y = Y + 0.08
    _lines(M, F, [(-16, -9, 16, -9), (-16, 9, 16, 9), (-16, -9, -16, 9), (16, -9, 16, 9), (0, -9, 0, 9), (-16, -4, -11, -4), (-16, 4, -11, 4), (-11, -4, -11, 4), (16, -4, 11, -4), (16, 4, 11, 4), (11, -4, 11, 4)], y)
    M.m('metal')
    for s in (-1, 1):
        for v in (-1.5, 1.5): _post(M, F, s * 16, v, Y, Y + 2.0, (245, 245, 245), 0.06); _post(M, F, s * 17, v, Y, Y + 1.2, (245, 245, 245), 0.04)
        _bar(M, F, s * 16, -1.5, s * 16, 1.5, Y + 2.0, (245, 245, 245), 0.06)
    _fence(M, F, 17.8, 10.8, 3.6, (0, -10.8))


def tennis(pr, F, r):
    M = pr.M; _pad(M, F, 17, 9, 'quadra', (86, 150, 110))
    M.m('quadra'); M.prism(F.rect(-11.9, 11.9, -5.5, 5.5), Y + 0.08, Y + 0.1, (190, 105, 84))
    y = Y + 0.1
    _lines(M, F, [(-11.9, -5.5, 11.9, -5.5), (-11.9, 5.5, 11.9, 5.5), (-11.9, -5.5, -11.9, 5.5), (11.9, -5.5, 11.9, 5.5), (-11.9, -4.1, 11.9, -4.1), (-11.9, 4.1, 11.9, 4.1), (-6.4, -4.1, -6.4, 4.1), (6.4, -4.1, 6.4, 4.1), (-6.4, 0, 6.4, 0)], y)
    M.m('metal'); _post(M, F, 0, -6.2, Y, Y + 1.1, STEEL); _post(M, F, 0, 6.2, Y, Y + 1.1, STEEL)
    M.m('liso'); M.prism(F.rect(-0.02, 0.02, -6.2, 6.2), Y + 0.25, Y + 1.0, (40, 42, 46)); M.prism(F.rect(-0.035, 0.035, -6.2, 6.2), Y + 1.0, Y + 1.07, (245, 245, 245))
    _fence(M, F, 17.6, 9.6, 3.4, (0, -9.6))


def playground(pr, F, r):
    M = pr.M; _pad(M, F, 10, 7.5, 'areia', (250, 240, 215), 0.1)
    M.m('madeira')
    for (u0, v0, u1, v1) in ((-10, -7.5, 10, -7.5), (-10, 7.5, 10, 7.5), (-10, -7.5, -10, 7.5), (10, -7.5, 10, 7.5)): _bar(M, F, u0, v0, u1, v1, Y + 0.14, (150, 110, 74), 0.12)
    cs = list(TOY); r.shuffle(cs)
    # balanco
    M.m('metal')
    for u in (-8, -4):
        for v in (3.0, 5.6): _post(M, F, u, v, Y, Y + 2.5, cs[0], 0.06)
    _bar(M, F, -8.4, 4.3, -3.6, 4.3, Y + 2.5, cs[0], 0.07)
    _bar(M, F, -8, 3.0, -8, 5.6, Y + 2.5, cs[0], 0.05); _bar(M, F, -4, 3.0, -4, 5.6, Y + 2.5, cs[0], 0.05)
    for u in (-7, -5):
        for du in (-0.28, 0.28): _post(M, F, u + du, 4.3, Y + 0.6, Y + 2.5, (60, 60, 64), 0.018)
        M.m('liso'); M.prism(F.rect(u - 0.32, u + 0.32, 4.1, 4.5), Y + 0.55, Y + 0.61, (40, 40, 44)); M.m('metal')
    # torre com escorregador
    M.m('liso')
    for (u, v) in ((0.2, -5.2), (2.6, -5.2), (0.2, -2.8), (2.6, -2.8)): _post(M, F, u, v, Y, Y + 3.3, cs[1], 0.09)
    M.prism(F.rect(0.1, 2.7, -5.3, -2.7), Y + 1.5, Y + 1.62, (170, 128, 84))
    M.prism(F.rect(-0.2, 3.0, -5.6, -2.4), Y + 3.3, Y + 3.45, cs[2])
    M.quad(F.p(2.7, -4.6, Y + 1.6), F.p(6.4, -4.6, Y + 0.25), F.p(6.4, -3.4, Y + 0.25), F.p(2.7, -3.4, Y + 1.6), cs[3], (0.34, 0.94, 0))
    for v in (-4.6, -3.4): M.quad(F.p(2.7, v, Y + 1.6), F.p(6.4, v, Y + 0.25), F.p(6.4, v, Y + 0.55), F.p(2.7, v, Y + 1.9), shade(cs[3], -30), F.nv(1 if v > -4 else -1))
    for k in range(4): M.prism(F.rect(-0.9 + k * 0.28, -0.62 + k * 0.28, -4.6, -3.4), Y + 0.3 + k * 0.33, Y + 0.38 + k * 0.33, (150, 110, 74))
    # gangorra e molas
    M.m('metal'); _post(M, F, 6, 3.5, Y, Y + 0.6, STEEL, 0.1)
    M.m('liso'); M.quad(F.p(4.2, 3.3, Y + 0.38), F.p(7.8, 3.3, Y + 0.86), F.p(7.8, 3.7, Y + 0.86), F.p(4.2, 3.7, Y + 0.38), cs[4], (-0.13, 1, 0))
    for (u, v, c) in ((0.5, 3.2, cs[0]), (2.2, 4.8, cs[3])):
        M.cyl(*F.xz(u, v), 0.1, Y, Y + 0.45, (60, 60, 64), 6); M.prism(F.rect(u - 0.45, u + 0.45, v - 0.16, v + 0.16), Y + 0.45, Y + 0.95, c)
    # carrossel
    M.cyl(*F.xz(-5.5, -3.5), 1.5, Y + 0.25, Y + 0.33, cs[2], 12); M.m('metal'); M.cyl(*F.xz(-5.5, -3.5), 0.08, Y, Y + 1.1, STEEL, 6)
    for k in range(4):
        a = k * math.pi / 2; _post(M, F, -5.5 + math.cos(a) * 1.3, -3.5 + math.sin(a) * 1.3, Y + 0.33, Y + 1.05, cs[0], 0.03)
    for (u, v, fu) in ((-6, -9.2, 1), (6, -9.2, 1)): pr.bench(*F.xz(u, v), F.vx, F.vz, Y)


def picnic(pr, F, r):
    M = pr.M; _pad(M, F, 6.5, 5, 'paver', (236, 228, 214), 0.06)
    M.m('madeira')
    for (u, v) in ((-5, -3.5), (5, -3.5), (5, 3.5), (-5, 3.5), (0, -3.5), (0, 3.5)): _post(M, F, u, v, Y, Y + 2.9, (120, 86, 58), 0.11)
    M.prism(F.rect(-5.4, 5.4, -3.9, 3.9), Y + 2.9, Y + 3.05, (120, 86, 58))
    M.m('telha')
    M.quad(F.p(-6, -4.6, Y + 3.0), F.p(6, -4.6, Y + 3.0), F.p(6, 0, Y + 4.5), F.p(-6, 0, Y + 4.5), (168, 84, 62), (0, 0.95, -0.31))
    M.quad(F.p(-6, 0, Y + 4.5), F.p(6, 0, Y + 4.5), F.p(6, 4.6, Y + 3.0), F.p(-6, 4.6, Y + 3.0), (168, 84, 62), (0, 0.95, 0.31))
    M.m('madeira')
    for s in (-1, 1): M.tri(F.p(s * 6, -4.6, Y + 3.0), F.p(s * 6, 4.6, Y + 3.0), F.p(s * 6, 0, Y + 4.5), (196, 170, 130), F.nu(s))
    for (u, v) in ((-3, 0), (3, 0), (-9.5, -2), (9.5, 2)): table(pr, F, u, v)
    M.m('pedra'); M.prism(F.rect(-0.5, 0.5, 6.0, 6.9), Y, Y + 0.9, (150, 146, 140)); M.m('metal'); M.prism(F.rect(-0.45, 0.45, 6.05, 6.85), Y + 0.9, Y + 0.94, (40, 40, 44))


def table(pr, F, u, v):
    M = pr.M; M.m('madeira'); c = (164, 122, 82)
    M.prism(F.rect(u - 0.95, u + 0.95, v - 0.42, v + 0.42), Y + 0.72, Y + 0.78, c)
    for s in (-1, 1):
        M.prism(F.rect(u - 0.95, u + 0.95, v + s * 0.85 - 0.15, v + s * 0.85 + 0.15), Y + 0.42, Y + 0.47, c)
        M.prism(F.rect(u + s * 0.7 - 0.05, u + s * 0.7 + 0.05, v - 0.95, v + 0.95), Y, Y + 0.42, shade(c, -30))
        M.prism(F.rect(u + s * 0.7 - 0.05, u + s * 0.7 + 0.05, v - 0.3, v + 0.3), Y + 0.42, Y + 0.72, shade(c, -30))


def garden(pr, F, r):
    M = pr.M; cx, cz = F.xz(0, 0)
    from shapely.geometry import Point
    ring = Point(cx, cz).buffer(9.2, 12).difference(Point(cx, cz).buffer(6.4, 12))
    M.m('paver'); M.shp(ring, Y + 0.06, (240, 232, 218))
    M.shp(Point(cx, cz).buffer(3.6, 10), Y + 0.06, (240, 232, 218))
    for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
        ca, sa = math.cos(a + 0.785), math.sin(a + 0.785)
        M.quad(F.p(ca * 3.4 - sa * 0.8, sa * 3.4 + ca * 0.8, Y + 0.06), F.p(ca * 6.6 - sa * 0.8, sa * 6.6 + ca * 0.8, Y + 0.06), F.p(ca * 6.6 + sa * 0.8, sa * 6.6 - ca * 0.8, Y + 0.06), F.p(ca * 3.4 + sa * 0.8, sa * 3.4 - ca * 0.8, Y + 0.06), (240, 232, 218), (0, 1, 0))
    # chafariz
    M.m('pedra'); M.cyl(cx, cz, 2.6, Y, Y + 0.55, WHITE, 14); M.m('agua'); M.cyl(cx, cz, 2.25, Y + 0.55, Y + 0.6, (200, 230, 240), 14)
    M.m('pedra'); M.cyl(cx, cz, 0.35, Y + 0.55, Y + 1.7, WHITE, 8); M.cyl(cx, cz, 1.1, Y + 1.7, Y + 1.85, WHITE, 10); M.m('agua'); M.cyl(cx, cz, 0.95, Y + 1.85, Y + 1.9, (200, 230, 240), 10)
    for k in range(8):
        a = k * math.pi / 4 + 0.39; rr = 5.0
        pr.tree(*F.xz(math.cos(a) * rr, math.sin(a) * rr), 'flores', r.uniform(0.9, 1.2))
    for k in range(4):
        a = k * math.pi / 2; pr.bench(*F.xz(math.cos(a) * 8.6, math.sin(a) * 8.6), *((lambda p, q: (p[0] - q[0], p[1] - q[1]))(F.xz(0, 0), F.xz(math.cos(a), math.sin(a)))), Y + 0.06)
    for k in range(4):
        a = k * math.pi / 2 + 0.785; pr.tree(*F.xz(math.cos(a) * 11.5, math.sin(a) * 11.5), 'buxo', 1.0)


def gazebo(pr, F, r):
    M = pr.M; cx, cz = F.xz(0, 0)
    M.m('paver'); M.cyl(cx, cz, 8.2, Y, Y + 0.06, (238, 230, 216), 16)
    M.m('concreto'); M.cyl(cx, cz, 5.2, Y + 0.06, Y + 0.7, WHITE, 8)
    M.prism(F.rect(-1.2, 1.2, -6.4, -5.0), Y + 0.06, Y + 0.38, WHITE)
    M.m('liso')
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8; M.cyl(cx + math.cos(a) * 4.7, cz + math.sin(a) * 4.7, 0.14, Y + 0.7, Y + 3.7, (246, 246, 240), 6)
    M.m('telha'); M.cyl(cx, cz, 5.9, Y + 3.7, Y + 5.9, (128, 74, 62), 8, False, 0.05)
    M.m('liso'); M.cyl(cx, cz, 5.6, Y + 3.55, Y + 3.7, (246, 246, 240), 8); M.cyl(cx, cz, 0.12, Y + 5.9, Y + 6.8, (200, 170, 60), 5)


def gym(pr, F, r):
    M = pr.M; _pad(M, F, 8, 4.5, 'quadra', (120, 128, 138), 0.07)
    y = Y + 0.07
    M.m('metal')
    for k, u in enumerate((-6, -3, 0, 3, 6)):
        c = TOY[k % len(TOY)]
        if k % 3 == 0:        # barras paralelas
            for v in (-1.2, 1.2): _post(M, F, u, v, y, y + 2.3, c, 0.05)
            _bar(M, F, u, -1.2, u, 1.2, y + 2.3, c, 0.045); _bar(M, F, u, -1.2, u, 1.2, y + 1.4, c, 0.045)
        elif k % 3 == 1:      # roda / simulador
            _post(M, F, u, 0, y, y + 1.5, c, 0.07); M.cyl(*F.xz(u, 0.5), 0.45, y + 1.0, y + 1.08, (240, 200, 50), 8); M.cyl(*F.xz(u, -0.5), 0.45, y + 1.0, y + 1.08, (240, 200, 50), 8)
        else:                 # banco de abdominal
            M.quad(F.p(u - 0.3, -1.1, y + 0.3), F.p(u + 0.3, -1.1, y + 0.3), F.p(u + 0.3, 1.1, y + 0.75), F.p(u - 0.3, 1.1, y + 0.75), c, (0, 0.93, -0.37))
            _post(M, F, u, 1.1, y, y + 1.0, STEEL, 0.05); _post(M, F, u, -1.0, y, y + 0.3, STEEL, 0.05)


def skate(pr, F, r):
    M = pr.M; _pad(M, F, 14, 8, 'concreto', (214, 212, 206), 0.07)
    y = Y + 0.07; c = (196, 194, 188)
    M.m('concreto')
    for s in (-1, 1):       # rampas nas pontas (plano inclinado + plataforma)
        M.prism(F.rect(*(sorted((s * 14, s * 12))), -7, 7), y, y + 1.6, c)
        M.quad(*((F.p(s * 12, -7, y + 1.6), F.p(s * 8.5, -7, y), F.p(s * 8.5, 7, y), F.p(s * 12, 7, y + 1.6)) if s > 0 else (F.p(s * 8.5, -7, y), F.p(s * 12, -7, y + 1.6), F.p(s * 12, 7, y + 1.6), F.p(s * 8.5, 7, y))), shade(c, 8), (-s * 0.42, 0.9, 0))
        for v in (-7, 7): M.tri(F.p(s * 12, v, y), F.p(s * 8.5, v, y), F.p(s * 12, v, y + 1.6), shade(c, -20), F.nv(1 if v > 0 else -1))
    # caixote central com rampas e corrimao
    M.prism(F.rect(-2.2, 2.2, -1.6, 1.6), y, y + 0.55, shade(c, -10))
    for s in (-1, 1):
        M.quad(*((F.p(2.2, -1.6, y + 0.55), F.p(4.6, -1.6, y), F.p(4.6, 1.6, y), F.p(2.2, 1.6, y + 0.55)) if s > 0 else (F.p(-4.6, -1.6, y), F.p(-2.2, -1.6, y + 0.55), F.p(-2.2, 1.6, y + 0.55), F.p(-4.6, 1.6, y))), shade(c, 4), (s * 0.22, 0.97, 0))
        for v in (-1.6, 1.6): M.tri(F.p(s * 2.2, v, y), F.p(s * 4.6, v, y), F.p(s * 2.2, v, y + 0.55), shade(c, -24), F.nv(1 if v > 0 else -1))
    M.m('metal'); _bar(M, F, -4, 4.6, 4, 4.6, y + 0.5, (230, 190, 40), 0.05)
    for u in (-3.8, 0, 3.8): _post(M, F, u, 4.6, y, y + 0.5, (230, 190, 40), 0.04)
    M.m('concreto'); M.prism(F.rect(-3.5, 3.5, -5.6, -4.8), y, y + 0.4, shade(c, -14))


def umbrella(pr, F, u, v, col):
    M = pr.M; x, z = F.xz(u, v)
    M.m('metal'); M.cyl(x, z, 0.035, Y, Y + 2.4, (230, 230, 230), 5)
    M.m('liso'); M.cyl(x, z, 1.5, Y + 2.05, Y + 2.5, col, 8, False, 0.05)
    M.cyl(x, z, 0.5, Y, Y + 0.72, (245, 245, 242), 8)
    for k in range(3):
        a = k * 2.1 + 0.5; M.cyl(x + math.cos(a) * 0.95, z + math.sin(a) * 0.95, 0.2, Y, Y + 0.45, (60, 62, 66), 6)


def kiosk(pr, F, r):
    M = pr.M; _pad(M, F, 10, 7, 'paver', (238, 230, 216), 0.06)
    y = Y + 0.06; wall = r.choice(((244, 236, 220), (226, 240, 236), (250, 226, 200)))
    M.m('reboco'); M.prism(F.rect(-3, 3, -2.5, 2.5), y, y + 3.0, wall, False)
    M.m('madeira'); M.prism(F.rect(-3.3, 3.3, -3.0, -2.5), y + 1.0, y + 1.1, (150, 104, 66))
    M.m('liso'); M.prism(F.rect(-2.4, 2.4, -2.56, -2.5), y + 1.1, y + 2.3, (52, 60, 70))
    roof = r.choice(((176, 70, 52), (60, 110, 96), (70, 92, 140)))
    M.m('telha'); M.prism(F.rect(-4.2, 4.2, -4.0, 3.2), y + 3.0, y + 3.25, roof)
    M.prism(F.rect(-2.2, 2.2, -1.8, 1.8), y + 3.25, y + 3.9, shade(roof, -20))
    M.m('metal')
    for u in (-4, 4): _post(M, F, u, -3.8, y, y + 3.0, (240, 240, 236), 0.06)
    cols = list(TOY); r.shuffle(cols)
    for k, (u, v) in enumerate(((-7.2, -4), (-7.2, 1.5), (7.2, -4), (7.2, 1.5), (0, -5.6))): umbrella(pr, F, u, v, cols[k % 2])


def pond(pr, F, r):
    from shapely.geometry import Polygon
    M = pr.M; cx, cz = F.xz(0, 0); ph = r.uniform(0, 6.28)
    pts = [F.xz(math.cos(a) * 11 * (1 + 0.16 * math.sin(3 * a + ph)), math.sin(a) * 7 * (1 + 0.14 * math.cos(2 * a + ph))) for a in [2 * math.pi * k / 28 for k in range(28)]]
    lake = Polygon(pts)
    rim = lake.buffer(1.0)
    M.m('pedra'); M.shp(rim.difference(lake), Y + 0.24, WHITE)
    for k in range(len(pts)):
        a, b = pts[k], pts[(k + 1) % len(pts)]; M.quad((b[0], Y + 0.06, b[1]), (a[0], Y + 0.06, a[1]), (a[0], Y + 0.24, a[1]), (b[0], Y + 0.24, b[1]), (200, 200, 196), (cx - a[0], 0, cz - a[1]))
    ro = list(rim.exterior.coords)
    for k in range(len(ro) - 1):
        a, b = ro[k], ro[k + 1]; M.quad((a[0], Y, a[1]), (b[0], Y, b[1]), (b[0], Y + 0.24, b[1]), (a[0], Y + 0.24, a[1]), (200, 200, 196), (a[0] - cx, 0, a[1] - cz))
    M.m('agua'); M.shp(lake, Y + 0.09, (196, 224, 214))
    # ponte de madeira
    M.m('madeira'); n = 8
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n; v0, v1 = -8.5 + 17 * t0, -8.5 + 17 * t1
        y0, y1 = Y + 0.26 + 1.0 * math.sin(math.pi * t0), Y + 0.26 + 1.0 * math.sin(math.pi * t1)
        M.quad(F.p(1.1, v0, y0), F.p(-1.1, v0, y0), F.p(-1.1, v1, y1), F.p(1.1, v1, y1), (168, 124, 84), (0, 1, 0))
        for s in (-1, 1):
            M.quad(F.p(s * 1.1, v0, y0 - 0.25), F.p(s * 1.1, v1, y1 - 0.25), F.p(s * 1.1, v1, y1), F.p(s * 1.1, v0, y0), (120, 88, 60), F.nu(s))
            _post(M, F, s * 1.05, v0, y0, y0 + 0.95, (240, 238, 232), 0.04)
            M.quad(F.p(s * 1.05, v0, y0 + 0.88), F.p(s * 1.05, v1, y1 + 0.88), F.p(s * 1.05, v1, y1 + 0.96), F.p(s * 1.05, v0, y0 + 0.96), (240, 238, 232), F.nu(s))
    for k in range(7):
        a = r.uniform(0, 6.28); pr.tree(*F.xz(math.cos(a) * 13.2, math.sin(a) * 9.2), r.choice(('arbusto', 'flores', 'arbusto')), r.uniform(0.8, 1.1))


def dogpark(pr, F, r):
    M = pr.M; _pad(M, F, 11, 7, 'cascalho', (236, 226, 204), 0.05)
    M.m('metal')
    n = 8; m = 5
    for i in range(n + 1):
        for v in (-7, 7):
            if v < 0 and i == n // 2: continue
            _post(M, F, -11 + 22 * i / n, v, Y, Y + 1.25, (60, 110, 80), 0.045)
    for j in range(1, m):
        for u in (-11, 11): _post(M, F, u, -7 + 14 * j / m, Y, Y + 1.25, (60, 110, 80), 0.045)
    for yy in (Y + 1.2, Y + 0.65, Y + 0.2):
        for (u0, v0, u1, v1) in ((-11, 7, 11, 7), (-11, -7, -2.2, -7), (0.6, -7, 11, -7), (-11, -7, -11, 7), (11, -7, 11, 7)): _bar(M, F, u0, v0, u1, v1, yy, (60, 110, 80), 0.03)
    M.m('liso')
    for k, u in enumerate((-7, -4.5, -2)):
        _post(M, F, u, -1.2, Y, Y + 0.9, TOY[k], 0.05); _post(M, F, u, 1.2, Y, Y + 0.9, TOY[k], 0.05); _bar(M, F, u, -1.2, u, 1.2, Y + 0.35 + 0.2 * k, (245, 245, 245), 0.04)
    M.quad(F.p(2, 2, Y + 0.05), F.p(4.5, 2, Y + 1.0), F.p(4.5, 3.2, Y + 1.0), F.p(2, 3.2, Y + 0.05), TOY[2], (-0.35, 0.93, 0))
    M.quad(F.p(4.5, 2, Y + 1.0), F.p(7, 2, Y + 0.05), F.p(7, 3.2, Y + 0.05), F.p(4.5, 3.2, Y + 1.0), TOY[2], (0.35, 0.93, 0))
    M.cyl(*F.xz(6, -3), 0.7, Y + 0.05, Y + 0.5, TOY[1], 10)
    pr.bench(*F.xz(-8, 5.8), -F.vx, -F.vz, Y + 0.05)


def amphi(pr, F, r):
    M = pr.M; cx, cz = F.xz(0, 0)
    M.m('concreto')
    for k in range(4):
        r0 = 5 + k * 1.5
        n = 12
        for i in range(n):
            a0 = math.pi * i / n; a1 = math.pi * (i + 1) / n
            q = [F.xz(math.cos(a0) * r0, math.sin(a0) * r0), F.xz(math.cos(a0) * (r0 + 1.5), math.sin(a0) * (r0 + 1.5)), F.xz(math.cos(a1) * (r0 + 1.5), math.sin(a1) * (r0 + 1.5)), F.xz(math.cos(a1) * r0, math.sin(a1) * r0)]
            M.prism(q[::-1], Y, Y + 0.45 * (k + 1), (212, 208, 200) if k % 2 else (226, 222, 214))
    M.m('madeira'); M.prism(F.rect(-4.5, 4.5, -4.5, 0), Y, Y + 0.5, (170, 128, 88))
    M.m('metal')
    for u in (-4.3, 4.3): _post(M, F, u, -4.3, Y + 0.5, Y + 4.2, STEEL, 0.08)
    M.m('liso'); M.prism(F.rect(-4.6, 4.6, -4.6, -1.5), Y + 4.2, Y + 4.4, (240, 240, 236))


class _Queue:
    """bancos e plantas pedidos por um equipamento entram depois dele (eles trocam a camada/ancora da malha)"""
    def __init__(self, pr): self.M = pr.M; self.todo = []
    def bench(self, *a): self.todo.append(('b', a))
    def tree(self, *a): self.todo.append(('t', a))


# nome -> (funcao, meio-comprimento, meia-largura) com folga
STATIONS = {
    'basquete': (basket, 16.5, 10.5), 'futsal': (futsal, 18.5, 11.5), 'tenis': (tennis, 18.5, 10.5), 'playground': (playground, 11, 10),
    'piquenique': (picnic, 11, 7.5), 'jardim': (garden, 12.5, 12.5), 'coreto': (gazebo, 8.6, 8.6), 'academia': (gym, 8.6, 5),
    'skate': (skate, 14.6, 8.6), 'quiosque': (kiosk, 10.5, 7.5), 'lago': (pond, 14.5, 10.5), 'caes': (dogpark, 11.6, 7.6), 'anfiteatro': (amphi, 11.2, 11.2),
}


def place(pr, name, x, z, ux, uz, r, y=None):
    """desenha o equipamento centrado em (x, z), comprimento ao longo de (ux, uz), no nivel y (padrao: gramado);
    devolve o retangulo ocupado (shapely)"""
    global Y
    from shapely.geometry import Polygon
    fn, a, b = STATIONS[name]
    F = Frame((x, z), (ux, uz))
    old = Y
    if y is not None: Y = y
    try:
        q = _Queue(pr)
        pr.M.at(x, z, 'parques'); fn(q, F, r); pr.M.free('parques')
        for (k, args) in q.todo:
            if k == 'b': pr.bench(*args)
            else: pr.tree(*(args if len(args) > 4 else (*args, Y)))
        pr.M.free('parques')
    finally: Y = old
    return Polygon(F.rect(-a, a, -b, b))
