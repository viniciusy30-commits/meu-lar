"""Cidade 6 - vegetacao e carros (v2).
Arvores: tronco afilado + copa de varias massas arredondadas (normais suaves), especies com silhuetas diferentes;
niveis de detalhe: 2 = rua/jardim, 1 = parques, 0 = mata (leve). Carros: perfil lateral extrudado (capô, para-brisa, teto, porta-malas)."""
import math
from mesh import rgb, shade, mix, WHITE, Frame

GREENS = [rgb(c) for c in ('#4F7F3A', '#5C8C42', '#6A9A4A', '#487436', '#7BA050', '#557F45', '#3F6B33', '#668F3C')]
AUTUMN = [rgb(c) for c in ('#C98A2E', '#B8642A', '#D9A63A')]
BLOSSOM = [rgb(c) for c in ('#F2A7C4', '#F7D154', '#B98AE0', '#F6F2F4', '#F08A6A')]
BARK = (236, 220, 200)
CARS = [rgb(c) for c in ('#E9E9E6', '#1E1F22', '#7C7F85', '#B32A2A', '#2A4D8A', '#F3F1EB', '#3B593B', '#C8B38A', '#5A6C80', '#8A1E2C', '#D8D8D3', '#303034',
                         '#A9B4BC', '#D08A2E', '#2E6E7A', '#6E1F4A')]


def tree(M, r, x, z, kind='folhosa', sc=1.0, y=0.13, layer='vegetacao', lod=2):
    M.at(x, z, layer)
    seg, rings = ((6, 4), (7, 4), (8, 5))[lod]; ls, lr = ((5, 3), (5, 3), (6, 4))[lod]
    if kind in ('folhosa', 'oval', 'ornamental', 'florida', 'frutifera'):
        small = kind in ('ornamental', 'florida', 'frutifera')
        h = r.uniform(2.3, 3.2) * sc * (0.62 if small else 1.0)
        R = r.uniform(2.3, 3.0) * sc * (0.62 if small else 1.0)
        syc = 1.3 if kind == 'oval' else (0.78 if kind == 'folhosa' else 0.9)
        if kind == 'florida': col = r.choice(BLOSSOM)
        elif kind == 'ornamental': col = r.choice(GREENS[2:5] + [rgb('#8FB04E'), rgb('#9A5A6A')])
        else: col = r.choice(GREENS) if r.random() > 0.05 else r.choice(AUTUMN)
        M.m('casca'); M.smooth_cyl(x, z, (0.22 if not small else 0.12) * sc, y, y + h + R * 0.35, BARK, 5, (0.13 if not small else 0.07) * sc)
        if lod == 2 and not small:                       # dois galhos abrindo
            for a in (r.uniform(0, 3.14), r.uniform(3.14, 6.28)):
                bx, bz = x + math.cos(a) * R * 0.45, z + math.sin(a) * R * 0.45
                M.quad((x - 0.07, y + h * 0.75, z), (x + 0.07, y + h * 0.75, z), (bx + 0.04, y + h + R * 0.3, bz), (bx - 0.04, y + h + R * 0.3, bz), BARK, (math.sin(a), 0.3, -math.cos(a)))
        M.m('folhagem')
        yc = y + h + R * 0.72 * syc
        M.sphere(x, yc, z, R, col, seg, rings, syc, 0.06, r)
        nl = (0, 2, 3)[lod] if kind != 'oval' else (0, 1, 1)[lod]
        a0 = r.uniform(0, 6.28)
        for k in range(nl):
            a = a0 + k * 6.28 / max(nl, 1) + r.uniform(-0.4, 0.4); rr = R * r.uniform(0.52, 0.68)
            M.sphere(x + math.cos(a) * R * 0.6, yc + R * r.uniform(-0.3, 0.3) * syc, z + math.sin(a) * R * 0.6, rr, shade(col, r.randint(-14, 12)), ls, lr, syc, 0.06, r)
        if kind == 'frutifera' and lod == 2:
            M.m('liso'); fc = r.choice(((230, 120, 30), (210, 40, 40), (240, 210, 60)))
            for _ in range(6):
                a = r.uniform(0, 6.28); e = r.uniform(-0.4, 0.5)
                fx, fy, fz = x + math.cos(a) * R * 0.98 * math.cos(e), yc + math.sin(e) * R * syc, z + math.sin(a) * R * 0.98 * math.cos(e)
                M.box(fx - 0.09, fx + 0.09, fy - 0.09, fy + 0.09, fz - 0.09, fz + 0.09, fc)
    elif kind == 'conifera':
        h = r.uniform(8, 12) * sc
        M.m('casca'); M.smooth_cyl(x, z, 0.2 * sc, y, y + h * 0.2, BARK, 5)
        M.m('folhagem'); col = r.choice((rgb('#35603A'), rgb('#2E5533'), rgb('#3F6C40'), rgb('#476F3A')))
        tiers = 3 if lod == 0 else 4
        for k in range(tiers):
            t0 = 0.12 + 0.2 * k; t1 = min(1.0, t0 + 0.42)
            rr = (2.6 - 0.55 * k) * sc
            M.smooth_cyl(x, z, rr, y + h * t0, y + h * t1, shade(col, k * 7), 6 if lod == 0 else 7, 0.0 if k == tiers - 1 else rr * 0.25)
    elif kind == 'colunar':
        h = r.uniform(1.0, 1.5) * sc
        M.m('casca'); M.smooth_cyl(x, z, 0.14 * sc, y, y + h + 0.6, BARK, 5, 0.09 * sc)
        M.m('folhagem'); col = r.choice((rgb('#3C6A35'), rgb('#47763A'), rgb('#527C3C')))
        M.sphere(x, y + h + 3.3 * sc, z, 1.15 * sc, col, seg, rings + 1, 3.0, 0.05, r)
    elif kind == 'palmeira':
        h = 7.5 * sc; lean = r.uniform(-0.7, 0.7); la = r.uniform(0, 6.28); segn = 5
        P, N, UV, C, T = [], [], [], [], []
        for k in range(segn + 1):
            t = k / segn; cx, cy, cz = x + math.cos(la) * lean * t * t, y + h * t, z + math.sin(la) * lean * t * t
            rr = (0.26 - 0.1 * t) * (1.25 if k == 0 else 1.0)
            for i in range(6):
                a = 2 * math.pi * i / 5
                P.append((cx + math.cos(a) * rr, cy, cz + math.sin(a) * rr)); N.append((math.cos(a), 0.1, math.sin(a))); UV.append((i / 5, -cy / 2)); C.append((228, 214, 190))
        for k in range(segn):
            for i in range(5):
                a, b, c, d = k * 6 + i, k * 6 + i + 1, (k + 1) * 6 + i + 1, (k + 1) * 6 + i
                T.append((a, d, c)); T.append((a, c, b))
        M.m('casca'); M.indexed(P, N, UV, C, T)
        tx, ty, tz = x + math.cos(la) * lean, y + h, z + math.sin(la) * lean
        M.m('folhagem'); leaf = r.choice((rgb('#4F8A38'), rgb('#5C9A3E'), rgb('#487E34')))
        nf = 9 if lod else 7
        for i in range(nf):
            a = 2 * math.pi * i / nf + r.uniform(-0.2, 0.2); L = r.uniform(3.2, 3.9) * sc; dx, dz = math.cos(a), math.sin(a); px, pz = -dz, dx
            up = r.uniform(0.3, 0.9)
            pts = [(0.0, 0.0, 0.25), (L * 0.4, up, 0.6), (L * 0.75, up * 0.4 - 0.3, 0.45), (L, -1.5, 0.05)]
            for k in range(3):
                (l0, y0, w0), (l1, y1, w1) = pts[k], pts[k + 1]
                q = [(tx + dx * l0 + px * w0, ty + y0, tz + dz * l0 + pz * w0), (tx + dx * l0 - px * w0, ty + y0, tz + dz * l0 - pz * w0),
                     (tx + dx * l1 - px * w1, ty + y1, tz + dz * l1 - pz * w1), (tx + dx * l1 + px * w1, ty + y1, tz + dz * l1 + pz * w1)]
                M.quad(*q, shade(leaf, -6 * k), (0, 1, 0))
        M.sphere(tx, ty - 0.1, tz, 0.42, rgb('#7A6A44'), 5, 3)
    elif kind == 'arbusto':
        M.m('folhagem'); col = r.choice(GREENS[:6] + [rgb('#7A8F3E')])
        for _ in range(r.choice((1, 2))):
            M.sphere(x + r.uniform(-0.35, 0.35), y + 0.45 * sc, z + r.uniform(-0.35, 0.35), r.uniform(0.55, 0.85) * sc, col, 6, 3, 0.8, 0.08, r)
    elif kind == 'buxo':                       # cerca viva / topiaria aparada
        M.m('folhagem'); col = r.choice((rgb('#3F6B33'), rgb('#487436'), rgb('#4F7F3A')))
        if r.random() < 0.3: M.sphere(x, y + 0.55 * sc, z, 0.6 * sc, col, 6, 4, 0.95)
        else: M.box(x - 0.62 * sc, x + 0.62 * sc, y, y + 1.0 * sc, z - 0.45 * sc, z + 0.45 * sc, col, True, False, shade(col, 14))
    elif kind == 'flores':
        fc = r.choice(((232, 78, 120), (250, 214, 80), (244, 244, 248), (190, 110, 224), (246, 148, 56), (236, 60, 60), (120, 150, 240)))
        M.m('folhagem'); s = 0.42 * sc / 0.7
        M.box(x - s, x + s, y, y + 0.22, z - s, z + s, (120, 170, 90), True, False, mix(fc, (150, 190, 110), 0.25))
        M.box(x - s * 0.5, x + s * 0.5, y + 0.22, y + 0.36, z - s * 0.5, z + s * 0.5, mix(fc, (255, 255, 255), 0.1), True, False, fc)
    elif kind == 'muda':
        M.m('folhagem'); M.box(x - 0.22, x + 0.22, y + 0.25, y + 0.55, z - 0.22, z + 0.22, r.choice(((110, 170, 80), (140, 190, 90), (90, 150, 80))))
    M.free()


def _extrude(M, F, prof, v0, v1, col, yb, caps=True, colt=None):
    """perfil convexo [(u, y)] extrudado ao longo de v (carroceria)"""
    n = len(prof)
    cu = sum(p[0] for p in prof) / n; cy = sum(p[1] for p in prof) / n
    for i in range(n):
        (ua, ya), (ub, yb_) = prof[i], prof[(i + 1) % n]
        mu, my = (ua + ub) / 2 - cu, (ya + yb_) / 2 - cy
        nrm = (F.ux * mu, my, F.uz * mu)
        c = colt if (colt and my > abs(mu) * 0.8) else col
        M.quad(F.p(ua, v0, yb + ya), F.p(ub, v0, yb + yb_), F.p(ub, v1, yb + yb_), F.p(ua, v1, yb + ya), c, nrm)
    if caps:
        M.poly([F.p(u, v0, yb + y) for u, y in prof], shade(col, -8), F.nv(-1))
        M.poly([F.p(u, v1, yb + y) for u, y in prof], shade(col, -8), F.nv(1))


def car(M, r, x, z, dx, dz, col=None, yb=0.03, layer='carros'):
    """carro estacionado apontando para (dx, dz): sedan, hatch, SUV, picape ou van"""
    M.at(x, z, layer)
    col = col or r.choice(CARS); F = Frame((x, z), (dx, dz))
    kind = r.choice(('sedan', 'sedan', 'hatch', 'suv', 'suv', 'picape', 'van'))
    L = {'sedan': 4.6, 'hatch': 4.0, 'suv': 4.7, 'picape': 5.3, 'van': 4.9}[kind]; Wd = 1.84 if kind in ('suv', 'picape', 'van') else 1.76
    h0 = 0.28 if kind in ('sedan', 'hatch') else 0.36                    # vao livre
    belt = h0 + (0.55 if kind in ('sedan', 'hatch') else 0.68)           # linha de cintura
    top = belt + (0.48 if kind in ('sedan', 'hatch') else (0.62 if kind != 'van' else 0.85))
    a, b = -L / 2, L / 2
    M.m('liso')
    body = [(a, h0 + 0.1), (a + 0.12, h0), (b - 0.15, h0), (b, h0 + 0.12), (b, belt - 0.14), (b - 0.25, belt - 0.02), (a + 0.1, belt), (a, belt - 0.1)]
    _extrude(M, F, body, -Wd / 2, Wd / 2, col, yb)
    if kind == 'sedan': cab = [(a + 0.75, belt), (b - 1.35, belt - 0.02), (b - 2.0, top), (a + 1.35, top)]
    elif kind == 'hatch': cab = [(a + 0.2, belt), (b - 1.2, belt - 0.02), (b - 1.85, top), (a + 0.55, top)]
    elif kind == 'suv': cab = [(a + 0.15, belt), (b - 1.35, belt - 0.02), (b - 1.9, top), (a + 0.35, top)]
    elif kind == 'picape': cab = [(a + 1.9, belt), (b - 1.45, belt - 0.02), (b - 2.0, top), (a + 2.05, top)]
    else: cab = [(a + 0.1, belt), (b - 0.75, belt - 0.02), (b - 1.25, top), (a + 0.15, top)]
    cw = Wd / 2 - 0.1
    _extrude(M, F, cab, -cw, cw, col, yb, True, shade(col, 6))
    if kind == 'picape':                                                 # cacamba aberta
        M.poly([F.p(a + 0.12, -Wd / 2 + 0.12, yb + belt - 0.3), F.p(a + 1.85, -Wd / 2 + 0.12, yb + belt - 0.3), F.p(a + 1.85, Wd / 2 - 0.12, yb + belt - 0.3), F.p(a + 0.12, Wd / 2 - 0.12, yb + belt - 0.3)], (40, 40, 44), (0, 1, 0))
    # vidros: para-brisa, vigia e laterais (um pouco para fora da cabine)
    M.m('liso'); g = (52, 62, 74)
    (c0, c1, c2, c3) = cab; e = 0.035
    for s in (-1, 1):
        vv = s * (cw + e)
        M.quad(F.p(c0[0] + 0.12, vv, yb + c0[1] + 0.06), F.p(c1[0] - 0.12, vv, yb + c1[1] + 0.06), F.p(c2[0] - 0.05, vv, yb + c2[1] - 0.07), F.p(c3[0] + 0.05, vv, yb + c3[1] - 0.07), g, F.nv(s))
    for (p0, p1, sgn) in ((c1, c2, 1), (c0, c3, -1)):
        du, dy = p1[0] - p0[0], p1[1] - p0[1]; nrm = (F.ux * sgn, 0.5, F.uz * sgn)
        M.quad(F.p(p0[0] + du * 0.12 + sgn * e, -cw + 0.1, yb + p0[1] + dy * 0.12), F.p(p0[0] + du * 0.12 + sgn * e, cw - 0.1, yb + p0[1] + dy * 0.12),
               F.p(p0[0] + du * 0.92 + sgn * e, cw - 0.12, yb + p0[1] + dy * 0.92), F.p(p0[0] + du * 0.92 + sgn * e, -cw + 0.12, yb + p0[1] + dy * 0.92), g, nrm)
    # rodas: eixo escuro entre as duas rodas + calota hexagonal por fora
    M.m('liso'); R = 0.31 if kind in ('sedan', 'hatch') else 0.36
    for uu in (a + 0.85, b - 0.9):
        M.prism(F.rect(uu - R * 0.8, uu + R * 0.8, -Wd / 2 + 0.03, Wd / 2 - 0.03), yb + 0.02, yb + 2 * R - 0.04, (26, 26, 28), False)
        hexa = [(uu + math.cos(k * math.pi / 3) * R, R + math.sin(k * math.pi / 3) * R) for k in range(6)]
        for s in (-1, 1):
            M.poly([F.p(u, s * (Wd / 2 + 0.03), yb + y) for u, y in hexa], (34, 34, 36), F.nv(s))
    # farois, lanternas, para-choques, placa
    for vv in (-Wd / 2 + 0.32, Wd / 2 - 0.32):
        M.quad(F.p(b + 0.03, vv - 0.24, yb + belt - 0.36), F.p(b + 0.03, vv + 0.24, yb + belt - 0.36), F.p(b + 0.03, vv + 0.24, yb + belt - 0.2), F.p(b + 0.03, vv - 0.24, yb + belt - 0.2), (252, 248, 226), F.nu(1))
        M.quad(F.p(a - 0.03, vv - 0.24, yb + belt - 0.3), F.p(a - 0.03, vv + 0.24, yb + belt - 0.3), F.p(a - 0.03, vv + 0.24, yb + belt - 0.14), F.p(a - 0.03, vv - 0.24, yb + belt - 0.14), (196, 30, 30), F.nu(-1))
    M.quad(F.p(b + 0.05, -0.45, yb + h0 + 0.12), F.p(b + 0.05, 0.45, yb + h0 + 0.12), F.p(b + 0.05, 0.45, yb + h0 + 0.3), F.p(b + 0.05, -0.45, yb + h0 + 0.3), (40, 40, 44), F.nu(1))
    M.free()
    return kind
