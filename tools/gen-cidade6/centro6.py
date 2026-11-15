"""Cidade 6 - predios do centro e da orla (v2): terreo com lojas individuais (pilastras, letreiro, toldo, porta),
5 familias de fachada, cornijas, recuos com terraco, sacadas, caixas d'agua, torres de vidro escalonadas, art-deco,
redondas e laminas residenciais; hoteis de praia com podio e piscina; edificio-garagem."""
import math
from mesh import rgb, shade, mix, WHITE, Frame
from textures6 import MATS

Y0 = 0.13
SIGNS = [rgb(c) for c in ('#C8102E', '#0057B8', '#FFB81C', '#00843D', '#E35205', '#6D2077', '#2D2926', '#00A3AD', '#F2F0EA', '#8A1538', '#1B365D', '#D45D00', '#4A7729', '#B58500')]
AWN = [rgb(c) for c in ('#B83A3A', '#2E6A4A', '#2F4A7A', '#C9822E', '#6A2E5A', '#3A3A3A', '#D8C9A0', '#1F6E78', '#A84A2E', '#F2F0EA')]
WALLS = [rgb(c) for c in ('#F2ECE0', '#E7D9C4', '#D9DDE2', '#F4E8D8', '#E2CFC0', '#CFD8D2', '#EADFCF', '#DCD3E3', '#C9B8A6', '#E8E1D5', '#F6F2EA', '#D7C4B0', '#BFCAD2', '#EBD8C8', '#C8D2C0')]
BRICKS = [(255, 255, 255), (255, 232, 214), (226, 214, 204), (255, 244, 226), (214, 196, 190)]
GLASS = [(205, 215, 222), (225, 225, 215), (190, 208, 200), (215, 205, 190), (175, 190, 210), (200, 220, 215), (230, 215, 200), (160, 180, 190)]


def storefronts(B, F, w, gh, wall, v=0.0, u0=0.0):
    """terreo comercial ao longo de u (frente em v): lojas de 5-8 m, cada uma com pilastra, vitrine, letreiro e toldo proprios"""
    r = B.rnd; M = B.M; y0 = Y0
    u = u0
    while u < u0 + w - 0.2:
        bw = min(r.uniform(5.0, 8.5), u0 + w - u)
        if u0 + w - (u + bw) < 3.5: bw = u0 + w - u
        a, b = u + 0.35, u + bw - 0.35
        B.box(F, u - 0.02, u + 0.35, v - 0.12, v + 0.2, y0, y0 + gh, shade(wall, -14), 'concreto', top=False)            # pilastra
        kind = r.random()
        if kind < 0.12:                                                    # portaria / entrada do predio
            B.panel(F, a, b, v, y0, y0 + gh - 1.0, (60, 62, 66), 'liso', -1, 0.04)
            B.panel(F, (a + b) / 2 - 1.1, (a + b) / 2 + 1.1, v, y0, y0 + 2.6, WHITE, 'janela', -1, 0.07)
            B.box(F, (a + b) / 2 - 1.6, (a + b) / 2 + 1.6, v - 1.5, v, y0 + 2.9, y0 + 3.05, (226, 224, 218), 'concreto')
        else:
            n = max(1, round((b - a) / 3.0))
            B.panel(F, a, b, v, y0 + 0.45, y0 + gh - 1.25, WHITE, 'vitrine', -1, 0.05, [(0, 1), (n, 1), (n, 0), (0, 0)])
            B.panel(F, a, b, v, y0, y0 + 0.45, shade(wall, -40), 'concreto', -1, 0.06)
            dz = a + (b - a) * r.choice((0.2, 0.5, 0.8))                   # porta de vidro
            B.panel(F, dz - 0.55, dz + 0.55, v, y0, y0 + 2.35, (40, 44, 50), 'liso', -1, 0.07)
            B.panel(F, dz - 0.47, dz + 0.47, v, y0 + 0.08, y0 + 2.27, (74, 96, 110), 'liso', -1, 0.085)
            sc = r.choice(SIGNS)
            B.box(F, a - 0.1, b + 0.1, v - 0.16, v, y0 + gh - 1.15, y0 + gh - 0.35, sc, 'liso', top=True)                # letreiro
            lw = (b - a) * r.uniform(0.35, 0.6); lc = (a + b) / 2
            B.panel(F, lc - lw / 2, lc + lw / 2, v - 0.16, y0 + gh - 0.95, y0 + gh - 0.55, (250, 250, 246) if sum(sc) < 480 else (40, 40, 44), 'liso', -1, 0.02)
            if r.random() < 0.55:                                          # toldo
                ac = r.choice(AWN); dep = r.uniform(1.1, 1.7); ya = y0 + gh - 1.2
                q = [F.p(a, v - 0.14, ya), F.p(b, v - 0.14, ya), F.p(b, v - dep, ya - 0.55), F.p(a, v - dep, ya - 0.55)]
                M.m('liso'); M.quad(*q, ac, (-F.vx * 0.5, 0.85, -F.vz * 0.5)); M.quad(*q[::-1], shade(ac, -45), (F.vx * 0.5, -0.85, F.vz * 0.5))
                M.quad(F.p(a, v - dep, ya - 0.8), F.p(b, v - dep, ya - 0.8), F.p(b, v - dep, ya - 0.55), F.p(a, v - dep, ya - 0.55), shade(ac, -15), F.nv(-1))
        u += bw
    B.box(F, u0 + w - 0.35, u0 + w + 0.02, v - 0.12, v + 0.2, y0, y0 + gh, shade(wall, -14), 'concreto', top=False)
    B.box(F, u0 - 0.1, u0 + w + 0.1, v - 0.2, v + 0.1, y0 + gh - 0.3, y0 + gh, shade(wall, -22), 'concreto')              # faixa sobre as lojas


def balconies(B, F, u0, u1, v, y0, fh, n, depth=1.3, glass=True, every=1):
    for k in range(0, n, every):
        y = y0 + k * fh
        B.box(F, u0, u1, v - depth, v, y - 0.14, y, (232, 230, 224), 'concreto')
        if glass: B.box(F, u0, u1, v - depth, v - depth + 0.05, y, y + 1.0, (150, 180, 190), 'liso', top=False)
        else: B.box(F, u0, u1, v - depth, v - depth + 0.05, y, y + 1.0, (255, 255, 255), 'cerca', top=False)


def roof_stuff(B, F, u0, u1, v0, v1, y, wall, tank=0.3, garden=0.1, sign=0.06):
    r = B.rnd; M = B.M
    B.flat_roof(F, u0, u1, v0, v1, y, 0.9, shade(wall, -8), True)
    if (u1 - u0) < 9 or (v1 - v0) < 9: return
    if r.random() < 0.6:                                                   # casa de maquinas / caixa de escada
        a = r.uniform(u0 + 2, u1 - 6); b = r.uniform(v0 + 2, v1 - 5)
        B.box(F, a, a + 4.0, b, b + 3.2, y, y + 3.0, shade(wall, -6), 'reboco', mat_top='cascalho', colt=(196, 194, 188))
        B.panel(F, a + 1.4, a + 2.4, b, y, y + 2.1, (90, 94, 98), 'porta', -1, 0.04)
    if r.random() < tank:                                                  # caixa d'agua de madeira sobre pernas
        cx, cz = F.xz(r.uniform(u0 + 3, u1 - 3), r.uniform(v0 + 3, v1 - 3))
        M.m('metal')
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2; M.cyl(cx + math.cos(a) * 1.1, cz + math.sin(a) * 1.1, 0.08, y, y + 2.4, (70, 72, 76), 4, False)
        M.m('madeira'); M.cyl(cx, cz, 1.5, y + 2.4, y + 5.0, (220, 190, 160), 10, False)
        M.m('metal'); M.cyl(cx, cz, 1.65, y + 5.0, y + 5.9, (110, 100, 96), 10, False, 0.05)
    elif r.random() < garden:                                              # terraco-jardim com pergolado
        a, b = u0 + 1.5, v0 + 1.5; c, d = min(u1 - 1.5, a + 9), min(v1 - 1.5, b + 7)
        M.m('grama'); M.poly([F.p(a, b, y + 0.06), F.p(c, b, y + 0.06), F.p(c, d, y + 0.06), F.p(a, d, y + 0.06)], WHITE, (0, 1, 0))
        for (pu, pv) in ((a + 1, b + 1), (a + 4, b + 1), (a + 1, b + 4), (a + 4, b + 4)): B.box(F, pu - 0.08, pu + 0.08, pv - 0.08, pv + 0.08, y, y + 2.4, (150, 108, 70), 'madeira', top=False)
        for k in range(5): B.box(F, a + 0.6 + k * 0.9, a + 0.75 + k * 0.9, b + 0.7, b + 4.3, y + 2.4, y + 2.52, (150, 108, 70), 'madeira')
    if r.random() < sign and (u1 - u0) > 12:                               # outdoor no topo
        a = r.uniform(u0 + 1, u1 - 9)
        for uu in (a + 1, a + 7): B.box(F, uu - 0.1, uu + 0.1, v0 + 0.6, v0 + 0.8, y, y + 5.2, (70, 72, 76), 'metal', top=False)
        B.box(F, a, a + 8, v0 + 0.45, v0 + 0.6, y + 1.8, y + 5.4, r.choice(SIGNS), 'liso')
        B.panel(F, a + 1.2, a + 6.8, v0 + 0.45, y + 2.6, y + 4.6, (250, 250, 246), 'liso', -1, 0.02)


def midrise(B, F, w, d, floors, wall=None, facade=None, shop=True, awn=None, roof_equip=True, style=None):
    """predio de meio de quadra colado na calcada: lojas no terreo + andares; varia fachada, cornija, recuo, sacadas e cobertura"""
    r = B.rnd; M = B.M
    style = style or (facade if facade in ('escritorio',) and r.random() < 0.5 else r.choice(('classica', 'classica', 'janelas', 'janelas', 'moderna', 'escritorio', 'vidro')))
    if style == 'vidro' and floors < 5: style = 'escritorio'
    fh = {'classica': 3.6, 'janelas': 3.0, 'moderna': 3.0, 'escritorio': 3.6, 'vidro': 3.6}[style]
    su = MATS[style][1][0]
    if style == 'classica': col = r.choice(BRICKS); floors = min(floors, 9)
    elif style == 'vidro': col = r.choice(GLASS)
    elif style == 'escritorio': col = r.choice(((255, 255, 255), (238, 232, 222), (222, 228, 232), (246, 240, 228), (214, 206, 196)))
    else: col = wall or r.choice(WALLS)
    base = shade(col, -10) if style not in ('classica', 'vidro') else r.choice(((226, 220, 208), (200, 196, 188), (70, 72, 78)))
    gh = 4.6 if shop else 3.2
    y0 = Y0; yg = y0 + gh
    B.box(F, 0, w, 0.12, d, y0, yg, shade(base, -30), 'concreto', top=False)
    if shop: storefronts(B, F, w, gh, base)
    else:
        B.box(F, 0, w, 0, 0.12, y0, yg, base, 'reboco', top=False)
        B.panel(F, w / 2 - 1.5, w / 2 + 1.5, 0, y0, y0 + 2.7, WHITE, 'janela', -1, 0.05)
    # corpo, com recuo opcional dos ultimos andares
    setb = floors >= 5 and r.random() < 0.35
    nf_main = floors - (r.choice((1, 2)) if setb else 0)
    y1 = yg + nf_main * fh
    B.box(F, 0, w, 0, d, yg, y1, col, style, top=False, wall_uv=(su, fh, y1))
    ytop = y1
    if style == 'classica':                                                # cornija saliente + friso
        B.box(F, -0.35, w + 0.35, -0.35, d + 0.2, y1 - 0.15, y1 + 0.45, (226, 218, 202), 'concreto')
        B.box(F, -0.2, w + 0.2, -0.2, 0.1, y1 - 0.7, y1 - 0.45, (214, 206, 190), 'concreto')
    elif style in ('janelas', 'moderna') and r.random() < 0.55:            # sacadas na fachada
        nb = max(1, int(w / 6.5)); bw = w / nb
        for k in range(nb):
            balconies(B, F, k * bw + bw * 0.12, k * bw + bw * 0.88, 0, yg + fh, fh, nf_main - 1, 1.2, style == 'moderna')
    elif style == 'escritorio' and r.random() < 0.5:                       # brises verticais
        nb = max(2, int(w / 3.0))
        for k in range(nb + 1): B.box(F, w * k / nb - 0.12, w * k / nb + 0.12, -0.35, 0, yg, y1, shade(col, -16), 'concreto', top=False)
    if setb:
        rs = 2.6; y2 = y1 + (floors - nf_main) * fh
        B.box(F, rs * 0.4, w - rs * 0.4, rs, d - 0.5, y1, y2, col, style, top=False, wall_uv=(su, fh, y2))
        M.m('paver'); M.poly([F.p(0.3, 0.3, y1 + 0.04), F.p(w - 0.3, 0.3, y1 + 0.04), F.p(w - 0.3, rs, y1 + 0.04), F.p(0.3, rs, y1 + 0.04)], WHITE, (0, 1, 0))
        B.box(F, 0.05, w - 0.05, 0.05, 0.12, y1, y1 + 1.05, (160, 186, 196), 'liso', top=False)
        B.box(F, rs * 0.4 - 0.2, w - rs * 0.4 + 0.2, rs - 0.2, d - 0.3, y2, y2 + 0.3, shade(col, -14), 'concreto', top=False)
        roof_stuff(B, F, rs * 0.4, w - rs * 0.4, rs, d - 0.5, y2 + 0.3, col); ytop = y2
    else:
        if style != 'classica': B.box(F, -0.15, w + 0.15, -0.15, d + 0.15, y1, y1 + 0.35, shade(col, -12), 'concreto', top=False)
        roof_stuff(B, F, 0.15, w - 0.15, 0.15, d - 0.15, y1 + 0.35, col)
    B.solid(F, 0, w, 0, d)
    return ytop


def _round(B, cx, cz, R, y0, y1, col, mat, seg=20, fh=3.6):
    """corpo cilindrico com fachada texturizada (uv em andares e baias)"""
    M = B.M; M.m(mat); su = MATS[mat][1][0]
    nb = max(1, round(2 * math.pi * R / su / seg))
    for i in range(seg):
        a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg; am = (a0 + a1) / 2
        p0 = (cx + math.cos(a0) * R, cz + math.sin(a0) * R); p1 = (cx + math.cos(a1) * R, cz + math.sin(a1) * R)
        M.quad((p0[0], y0, p0[1]), (p1[0], y0, p1[1]), (p1[0], y1, p1[1]), (p0[0], y1, p0[1]), col if i % 2 else shade(col, -6), (math.cos(am), 0, math.sin(am)),
               [(i * nb, (y1 - y0) / fh), ((i + 1) * nb, (y1 - y0) / fh), ((i + 1) * nb, 0), (i * nb, 0)])


def tower(B, F, w, d, floors, glass_tint=None, podium_col=None, crown_col=None, kind=None):
    r = B.rnd; M = B.M
    kind = kind or r.choice(('vidro', 'vidro', 'deco', 'redonda', 'lamina', 'vidro2'))
    tint = glass_tint or r.choice(GLASS); pod = podium_col or r.choice(((70, 75, 82), (150, 140, 128), (205, 200, 190), (110, 100, 92), (226, 220, 208)))
    crown = crown_col or r.choice(((230, 228, 222), (60, 64, 70), (180, 160, 120)))
    y0 = Y0; fh = 3.6
    # podio com lojas, marquise e terraco
    pf = r.choice((2, 3)); ph = 4.6 + (pf - 1) * 4.0
    B.box(F, 0, w, 0.12, d, y0, y0 + 4.6, shade(pod, -20), 'concreto', top=False)
    storefronts(B, F, w, 4.6, pod)
    B.box(F, 0, w, 0, d, y0 + 4.6, y0 + ph, pod if sum(pod) > 400 else (226, 222, 214), 'escritorio', top=False, wall_uv=(3.0, 4.0, y0 + ph))
    B.box(F, w * 0.35, w * 0.65, -2.8, 0, y0 + 4.3, y0 + 4.6, (236, 236, 232), 'concreto')
    B.flat_roof(F, 0, w, 0, d, y0 + ph, 1.0, pod if sum(pod) > 400 else (226, 222, 214), False)
    y = y0 + ph; ins = 3.0
    u0, u1, v0, v1 = ins, w - ins, ins, d - ins
    cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
    if kind in ('vidro', 'vidro2'):
        tiers = 1 if floors < 16 else (2 if floors < 28 else 3); left = floors
        for t in range(tiers):
            nf = left if t == tiers - 1 else int(floors * (0.55 if t == 0 else 0.3)); left -= nf
            yt = y + nf * fh
            B.box(F, u0, u1, v0, v1, y, yt, tint, 'vidro', top=False, wall_uv=(3.0, fh, yt))
            if kind == 'vidro':
                for (a, b) in ((u0 - 0.25, u0 + 0.35), (u1 - 0.35, u1 + 0.25)):
                    B.box(F, a, b, v0 - 0.25, v0 + 0.35, y, yt, crown, 'concreto', top=False); B.box(F, a, b, v1 - 0.35, v1 + 0.25, y, yt, crown, 'concreto', top=False)
            else:                                                          # faixas horizontais a cada 4 andares
                for k in range(4, nf, 4): B.box(F, u0 - 0.2, u1 + 0.2, v0 - 0.2, v1 + 0.2, y + k * fh - 0.25, y + k * fh + 0.25, crown, 'concreto', top=False)
            y = yt
            if t < tiers - 1:
                B.flat_roof(F, u0, u1, v0, v1, y, 0.9, crown, False)
                if r.random() < 0.5: u0 += 2.5; u1 -= 2.5; v0 += 2.5; v1 -= 2.5
                else: u0 += 4.0; v1 -= 4.0
        B.box(F, u0 - 0.3, u1 + 0.3, v0 - 0.3, v1 + 0.3, y, y + 1.6, crown, 'concreto', top=False)
        B.flat_roof(F, u0, u1, v0, v1, y + 0.2, 1.4, crown, True)
    elif kind == 'deco':                                                   # art-deco: pedra clara, recuos em piramide, coroa e agulha
        stone = r.choice(BRICKS[1:] + [(244, 236, 220), (232, 226, 214)]); left = floors; t = 0
        while left > 0:
            nf = max(3, int(left * 0.5)) if left > 6 else left; left -= nf
            yt = y + nf * fh
            B.box(F, u0, u1, v0, v1, y, yt, stone, 'classica', top=False, wall_uv=(6.0, fh, yt))
            for (a, b, c, e) in ((u0, u0 + 0.5, v0, v0 + 0.5), (u1 - 0.5, u1, v0, v0 + 0.5), (u0, u0 + 0.5, v1 - 0.5, v1), (u1 - 0.5, u1, v1 - 0.5, v1)):
                B.box(F, a - 0.2, b + 0.2, c - 0.2, e + 0.2, y, yt + 1.2, (226, 218, 202), 'concreto')
            B.box(F, u0 - 0.25, u1 + 0.25, v0 - 0.25, v1 + 0.25, yt - 0.3, yt + 0.3, (226, 218, 202), 'concreto', mat_top='cascalho', colt=(196, 194, 188))
            y = yt; t += 1
            if left > 0:
                sx = min(3.0, (u1 - u0) * 0.14); sz = min(3.0, (v1 - v0) * 0.14); u0 += sx; u1 -= sx; v0 += sz; v1 -= sz
        cx, cz = F.xz((u0 + u1) / 2, (v0 + v1) / 2); rr = min(u1 - u0, v1 - v0) / 2
        M.m('metal'); M.cyl(cx, cz, rr * 0.85, y + 0.3, y + 5.0, (150, 170, 160), 8, False, rr * 0.3)
        M.cyl(cx, cz, rr * 0.3, y + 5.0, y + 9.0, (150, 170, 160), 8, False, 0.12); M.cyl(cx, cz, 0.12, y + 9.0, y + 9.0 + r.uniform(8, 14), (210, 210, 214), 5, False)
    elif kind == 'redonda':
        cx, cz = F.xz(cu, cv); R = min(u1 - u0, v1 - v0) / 2
        yt = y + floors * fh
        _round(B, cx, cz, R, y, yt, tint, 'vidro', 20, fh)
        for k in range(6, floors, 6):
            M.m('concreto'); M.cyl(cx, cz, R + 0.35, y + k * fh - 0.25, y + k * fh + 0.25, crown, 20, True)
        M.m('concreto'); M.cyl(cx, cz, R + 0.4, yt, yt + 1.2, crown, 20, True, None, (196, 194, 188))
        M.cyl(cx, cz, R * 0.5, yt + 1.2, yt + 4.2, crown, 12, True); M.m('metal'); M.cyl(cx, cz, 0.15, yt + 4.2, yt + 14, (210, 60, 60), 5, False)
        y = yt
    else:                                                                  # lamina residencial com sacadas nas duas faces longas
        wall = r.choice(WALLS)
        if (u1 - u0) < (v1 - v0): v0 += (v1 - v0) * 0.0
        yt = y + floors * 3.0
        B.box(F, u0, u1, v0 + 2, v1 - 2, y, yt, wall, 'moderna', top=False, wall_uv=(3.0, 3.0, yt))
        nb = max(1, int((u1 - u0) / 6.0)); bw = (u1 - u0) / nb
        for k in range(nb):
            balconies(B, F, u0 + k * bw + 0.5, u0 + (k + 1) * bw - 0.5, v0 + 2, y + 3.0, 3.0, floors - 1, 1.3, True, 1 if floors < 22 else 2)
        B.box(F, u0 - 0.2, u1 + 0.2, v0 + 1.8, v1 - 1.8, yt, yt + 0.4, shade(wall, -14), 'concreto', top=False)
        roof_stuff(B, F, u0, u1, v0 + 2, v1 - 2, yt + 0.4, wall, 0.0, 0.3, 0.0)
        y = yt
    B.solid(F, 0, w, 0, d)
    return y


def beach_hotel(B, F, w, d, floors, name_col=None):
    """hotel / residencial de frente para o mar (v=0 e a frente): podio com restaurante e lojas, torre com sacadas de vidro,
    piscina no terraco do podio, letreiro na cobertura"""
    r = B.rnd; M = B.M; y0 = Y0
    wall = r.choice(((250, 248, 242), (244, 236, 222), (232, 240, 244), (250, 240, 232), (240, 244, 236), (255, 250, 240)))
    acc = name_col or r.choice(((40, 110, 160), (200, 120, 60), (60, 140, 110), (180, 60, 70), (230, 180, 60)))
    pd = min(d, 26.0); ph = 4.6 + 3.6
    B.box(F, 0, w, 0.12, pd, y0, y0 + 4.6, (90, 92, 96), 'concreto', top=False)
    storefronts(B, F, w, 4.6, wall)
    B.box(F, 0, w, 0, pd, y0 + 4.6, y0 + ph, wall, 'moderna', top=False, wall_uv=(3.0, 3.6, y0 + ph))
    # terraco do podio com piscina, deck e guarda-corpo de vidro
    M.m('madeira'); M.poly([F.p(0.3, 0.3, y0 + ph + 0.05), F.p(w - 0.3, 0.3, y0 + ph + 0.05), F.p(w - 0.3, 8.0, y0 + ph + 0.05), F.p(0.3, 8.0, y0 + ph + 0.05)], WHITE, (0, 1, 0))
    B.box(F, 0.05, w - 0.05, 0.05, 0.12, y0 + ph, y0 + ph + 1.05, (160, 190, 200), 'liso', top=False)
    pw = min(w - 8, 16.0)
    B.box(F, w / 2 - pw / 2 - 0.4, w / 2 + pw / 2 + 0.4, 1.6, 6.4, y0 + ph + 0.05, y0 + ph + 0.2, (240, 236, 226), 'concreto')
    M.m('agua'); M.poly([F.p(w / 2 - pw / 2, 2.0, y0 + ph + 0.24), F.p(w / 2 + pw / 2, 2.0, y0 + ph + 0.24), F.p(w / 2 + pw / 2, 6.0, y0 + ph + 0.24), F.p(w / 2 - pw / 2, 6.0, y0 + ph + 0.24)], (150, 235, 245), (0, 1, 0))
    for k in range(int(pw / 2.2)):
        uu = w / 2 - pw / 2 + 0.6 + k * 2.2
        B.box(F, uu, uu + 0.7, 6.8, 7.7, y0 + ph + 0.05, y0 + ph + 0.4, r.choice(((250, 250, 250), acc)), 'liso')
    # torre
    tu0, tu1 = (w * 0.08, w * 0.92) if r.random() < 0.6 else ((w * 0.05, w * 0.6) if r.random() < 0.5 else (w * 0.4, w * 0.95))
    tv0, tv1 = 8.5, min(pd - 0.5, 8.5 + r.uniform(13, 17)); y = y0 + ph; yt = y + floors * 3.0
    B.box(F, tu0, tu1, tv0, tv1, y, yt, wall, 'moderna', top=False, wall_uv=(3.0, 3.0, yt))
    nb = max(1, int((tu1 - tu0) / 6.0)); bw = (tu1 - tu0) / nb
    for k in range(nb): balconies(B, F, tu0 + k * bw + 0.4, tu0 + (k + 1) * bw - 0.4, tv0, y + 3.0, 3.0, floors - 1, 1.4, True, 1 if floors <= 16 else 2)
    for uu in (tu0, tu1): B.box(F, uu - 0.3, uu + 0.3, tv0 - 1.5, tv1 + 0.2, y, yt + 1.5, acc, 'reboco', top=True)           # empenas coloridas
    B.box(F, tu0, tu1, tv0 - 0.2, tv1 + 0.2, yt, yt + 0.4, shade(wall, -12), 'concreto', top=False)
    roof_stuff(B, F, tu0 + 0.3, tu1 - 0.3, tv0, tv1, yt + 0.4, wall, 0.0, 0.25, 0.0)
    lw = min(12.0, (tu1 - tu0) * 0.6); lc = (tu0 + tu1) / 2                # letreiro luminoso
    B.box(F, lc - lw / 2, lc + lw / 2, tv0 - 0.1, tv0 + 0.15, yt + 1.6, yt + 3.6, acc, 'liso')
    B.panel(F, lc - lw / 2 + 0.8, lc + lw / 2 - 0.8, tv0 - 0.1, yt + 2.1, yt + 3.1, (252, 250, 240), 'liso', -1, 0.02)
    B.solid(F, 0, w, 0, pd)
    return yt


def parking_garage(B, F, w, d, levels=5):
    """edificio-garagem: lajes abertas com muretas, rampa lateral, carros nas vagas de cima"""
    r = B.rnd; M = B.M; y0 = Y0; lh = 3.1
    for k in range(levels + 1):
        y = y0 + k * lh
        if k: B.box(F, 0, w, 0, d, y - 0.3, y, (206, 204, 198), 'concreto')
        if k < levels:
            for (a, b, c, e) in ((0, w, 0, 0.25), (0, w, d - 0.25, d), (0, 0.25, 0.25, d - 0.25), (w - 0.25, w, 0.25, d - 0.25)):
                B.box(F, a, b, c, e, y, y + 1.1, (226, 224, 218), 'concreto')
            nu = max(2, int(w / 8));
            for i in range(nu + 1):
                for vv in (0.6, d / 2, d - 0.6): B.box(F, w * i / nu - 0.3 if i else 0.3, (w * i / nu + 0.3) if i < nu else w - 0.3, vv - 0.3, vv + 0.3, y, y + lh - 0.3, (190, 188, 182), 'concreto', top=False)
    yt = y0 + levels * lh
    B.box(F, w - 5.0, w - 0.5, 0.5, 5.0, yt, yt + 3.0, (226, 224, 218), 'reboco', mat_top='cascalho', colt=(196, 194, 188))
    B.box(F, 0.5, 9.0, -0.12, 0.0, y0 + 3.4, y0 + 4.6, (0, 87, 184), 'liso'); B.panel(F, 1.5, 4.0, -0.12, y0 + 3.6, y0 + 4.4, (250, 250, 250), 'liso', -1, 0.02)
    B.solid(F, 0, w, 0, d)
    return [(F.xz(4 + i * 2.7, 4.0), yt) for i in range(int((w - 12) / 2.7)) if r.random() < 0.6]
