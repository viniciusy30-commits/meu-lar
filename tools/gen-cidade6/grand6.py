"""Cidade 6 - igreja matriz e escola em versao grande e detalhada (substituem B.church / B.school).
Frame F na divisa com a calcada (u ao longo da rua, v para dentro); tudo apoiado no chao (Y0 do lote)."""
import math
import numpy as np
from mesh import shade, Frame
from buildings6 import Y0

GLOW = (255, 238, 196)


def _cyl(M, F, u, v, r, y0, y1, col, mat, seg=12, top=True, r1=None):
    x, z = F.xz(u, v); M.m(mat); M.cyl(x, z, r, y0, y1, col, seg, top, r1)


def _sph(M, F, u, v, y, r, col, mat, seg=10, rings=6, sy=1.0):
    x, z = F.xz(u, v); M.m(mat); M.sphere(x, y, z, r, col, seg, rings, sy)


def church(B, F, w, d):
    """Igreja Matriz: nave alta com transepto, fachada com duas torres de sineiro e flechas, tres portais em arco,
    rosacea de vitral colorido, janelas ogivais com vitrais, pilastras-contraforte, abside, adro com escadaria,
    chafariz, canteiros e postes."""
    M = B.M; wall = (244, 238, 224); trim = (214, 204, 186); roof = (120, 72, 60); stone = (206, 198, 182)
    nw = min(w * 0.5, 26.0); u0 = (w - nw) / 2; v0 = 16.0; nd = min(d - v0 - 10, 52.0); uc = u0 + nw / 2
    H = 15.0
    # nave
    B.box(F, u0, u0 + nw, v0, v0 + nd, Y0, Y0 + 1.2, stone, 'pedra', top=False)
    B.box(F, u0, u0 + nw, v0, v0 + nd, Y0 + 1.2, Y0 + H, wall, 'reboco', top=False)
    B.gable(F, u0, u0 + nw, v0, v0 + nd, Y0 + H, 8.0, roof, False, 0.7, 'telha', wall, 'reboco')
    # transepto
    tv = v0 + nd * 0.62; tw_ = 10.0
    B.box(F, u0 - 8, u0 + nw + 8, tv, tv + tw_, Y0, Y0 + H - 1.5, wall, 'reboco', top=False)
    B.gable(F, u0 - 8, u0 + nw + 8, tv, tv + tw_, Y0 + H - 1.5, 6.0, roof, True, 0.6, 'telha', wall, 'reboco')
    # abside semicircular
    x, z = F.xz(uc, v0 + nd); M.m('reboco'); M.cyl(x, z, nw * 0.42, Y0, Y0 + H - 3, wall, 16)
    M.m('telha'); M.cyl(x, z, nw * 0.46, Y0 + H - 3, Y0 + H + 2.5, roof, 16, False, 0.3)
    # contrafortes e janelas ogivais com vitral
    nwin = int(nd / 6.5)
    for k in range(nwin + 1):
        vv = v0 + 2 + k * (nd - 4) / max(1, nwin)
        if tv - 1 < vv < tv + tw_ + 1: continue
        for (uu, sd) in ((u0, -1), (u0 + nw, 1)):
            B.box(F, uu - 0.6 + (0.6 if sd > 0 else 0), uu + (0.6 if sd > 0 else 0) - (0 if sd > 0 else 0), vv - 0.5, vv + 0.5, Y0, Y0 + H - 2, stone, 'pedra')
        if k < nwin:
            vm = vv + (nd - 4) / max(1, nwin) / 2
            if tv - 2 < vm < tv + tw_ + 2: continue
            for (uu, sd) in ((u0, -1), (u0 + nw, 1)):
                B.panel_u(F, vm - 1.0, vm + 1.0, uu, Y0 + 4.0, Y0 + 11.0, trim, 'liso', sd, 0.05)
                for q, c_ in enumerate(((60, 90, 170), (180, 40, 50), (220, 170, 60), (60, 140, 90))):
                    B.panel_u(F, vm - 0.8, vm + 0.8, uu, Y0 + 4.2 + q * 1.6, Y0 + 5.7 + q * 1.6, c_, 'vidro', sd, 0.09)
    # fachada: torres
    tw = 7.0
    for tu in (u0 - tw + 1.0, u0 + nw - 1.0):
        B.box(F, tu, tu + tw, v0 - 2, v0 + 5, Y0, Y0 + 1.6, stone, 'pedra')
        B.box(F, tu, tu + tw, v0 - 2, v0 + 5, Y0 + 1.6, Y0 + 30, wall, 'reboco', top=False)
        for yy in (Y0 + 12, Y0 + 21, Y0 + 30): B.box(F, tu - 0.3, tu + tw + 0.3, v0 - 2.3, v0 + 5.3, yy - 0.4, yy, trim, 'concreto')
        for (fu, sd) in ((tu + tw / 2, -1),):
            B.panel(F, fu - 0.9, fu + 0.9, v0 - 2, Y0 + 14, Y0 + 19, (70, 90, 150), 'vidro', sd, 0.06)
            B.panel(F, fu - 1.4, fu + 1.4, v0 - 2, Y0 + 23, Y0 + 28, (40, 40, 46), 'liso', sd, 0.06)       # janela do sino
        # flecha e cruz
        cu, cv = tu + tw / 2, v0 + 1.5
        _cyl(M, F, cu, cv, tw * 0.72, Y0 + 30, Y0 + 41, (90, 110, 110), 'telha', 8, False, 0.05)
        _cyl(M, F, cu, cv, 0.1, Y0 + 41, Y0 + 44, (210, 180, 80), 'metal', 6)
        x, z = F.xz(cu, cv); M.m('metal'); M.box(x - 0.7, x + 0.7, Y0 + 43.0, Y0 + 43.2, z - 0.1, z + 0.1, (210, 180, 80))
        # relogio na torre esquerda
        if tu < u0:
            x, z = F.xz(cu, v0 - 2.08); M.m('liso')
            pts = [(x + F.ux * math.cos(a) * 1.4, Y0 + 26 + math.sin(a) * 1.4, z + F.uz * math.cos(a) * 1.4) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
            M.poly(pts, (250, 246, 230), F.nv(-1))
        B.solid(F, tu, tu + tw, v0 - 2, v0 + 5)
    # frontao entre as torres com rosacea de vitral
    B.box(F, u0, u0 + nw, v0 - 0.6, v0, Y0 + H, Y0 + H + 7.5, wall, 'reboco')
    x, z = F.xz(uc, v0 - 0.66)
    cols = [(180, 40, 50), (60, 90, 170), (220, 170, 60), (60, 140, 90), (140, 60, 150), (60, 90, 170)]
    M.m('vidro')
    for k in range(12):
        a0 = 2 * math.pi * k / 12; a1 = 2 * math.pi * (k + 1) / 12; R = 3.0
        M.poly([(x, Y0 + H + 1.8, z), (x + F.ux * math.cos(a0) * R, Y0 + H + 1.8 + math.sin(a0) * R, z + F.uz * math.cos(a0) * R), (x + F.ux * math.cos(a1) * R, Y0 + H + 1.8 + math.sin(a1) * R, z + F.uz * math.cos(a1) * R)], cols[k % 6], F.nv(-1))
    M.m('liso'); M.poly([(x + F.ux * math.cos(a) * 3.4 + F.vx * 0.01, Y0 + H + 1.8 + math.sin(a) * 3.4, z + F.uz * math.cos(a) * 3.4 + F.vz * 0.01) for a in np.linspace(0, 2 * math.pi, 20, endpoint=False)], trim, F.nv(-1))
    # tres portais em arco
    for (pu, pw_, ph) in ((uc, 3.6, 6.2), (uc - nw * 0.3, 2.2, 4.4), (uc + nw * 0.3, 2.2, 4.4)):
        B.panel(F, pu - pw_ / 2 - 0.5, pu + pw_ / 2 + 0.5, v0, Y0 + 1.2, Y0 + 1.2 + ph + 1.0, trim, 'pedra', -1, 0.12)
        B.panel(F, pu - pw_ / 2, pu + pw_ / 2, v0, Y0 + 1.2, Y0 + 1.2 + ph, (110, 70, 45), 'porta', -1, 0.18)
    B.drives.append((*F.xz(uc, v0 - 4.0), 4.5))
    # escadaria do adro
    for k in range(5): B.box(F, uc - 10 + k * 0.0, uc + 10, v0 - 7 + k * 1.2, v0 - 5.8 + k * 1.2, Y0, Y0 + 0.24 * (k + 1), (220, 214, 202), 'pedra')
    B.solid(F, u0, u0 + nw, v0, v0 + nd); B.solid(F, u0 - 8, u0 + nw + 8, tv, tv + tw_)
    # adro: piso, chafariz, canteiros, postes e bancos
    M.m('paver'); M.poly([F.p(2, 1, Y0 + 0.03), F.p(w - 2, 1, Y0 + 0.03), F.p(w - 2, v0 - 7.2, Y0 + 0.03), F.p(2, v0 - 7.2, Y0 + 0.03)], (230, 222, 208), (0, 1, 0))
    fx = uc; fv = (v0 - 7) / 2
    _cyl(M, F, fx, fv, 2.6, Y0, Y0 + 0.6, stone, 'pedra', 20); _cyl(M, F, fx, fv, 2.3, Y0 + 0.5, Y0 + 0.55, (150, 200, 220), 'agua', 20)
    _cyl(M, F, fx, fv, 0.3, Y0 + 0.55, Y0 + 1.8, stone, 'pedra', 10); _cyl(M, F, fx, fv, 0.9, Y0 + 1.8, Y0 + 2.0, stone, 'pedra', 12)
    for s_ in (-1, 1):
        for q in range(2):
            pu = uc + s_ * (8 + q * 7)
            if 3 < pu < w - 3:
                B.box(F, pu - 1.5, pu + 1.5, 2.5, 5.0, Y0, Y0 + 0.5, stone, 'pedra')
                M.m('grama'); M.poly([F.p(pu - 1.3, 2.7, Y0 + 0.52), F.p(pu + 1.3, 2.7, Y0 + 0.52), F.p(pu + 1.3, 4.8, Y0 + 0.52), F.p(pu - 1.3, 4.8, Y0 + 0.52)], (110, 160, 80), (0, 1, 0))
                B.solid(F, pu - 1.5, pu + 1.5, 2.5, 5.0)


def school(B, F, w, d, field_cb=None):
    """Escola: predio principal de 3 andares em U com faixas coloridas, entrada com marquise e letreiro, relogio,
    bloco do ginasio com telhado em arco, quadra coberta, campo com pista, bicicletario, mastros e estacionamento."""
    M = B.M
    wall = (246, 240, 228); band = [(230, 120, 40), (60, 140, 200), (90, 170, 80)]
    bw = min(w * 0.5, 84.0); bd = 16.0; u0 = 6.0; v0 = 12.0; FH = 3.8; nf = 3
    top = Y0 + nf * FH + 0.6
    B.box(F, u0, u0 + bw, v0, v0 + bd, Y0, top, wall, 'tijolo', top=False)
    for f in range(nf):
        y = Y0 + 1.0 + f * FH
        B.panel(F, u0, u0 + bw, v0, y - 0.6, y - 0.35, band[f], 'liso', -1, 0.04)
        for k in range(int((bw - 4) / 3.5)):
            uu = u0 + 3 + k * 3.5
            if abs(uu - (u0 + bw / 2)) < 4.5 and f == 0: continue
            B.window(F, uu, v0, y, 2.4, 1.9, -1)
    B.flat_roof(F, u0, u0 + bw, v0, v0 + bd, top, 1.0, (230, 226, 218), True)
    # alas laterais (U)
    for au in (u0, u0 + bw - 16):
        B.box(F, au, au + 16, v0 + bd, v0 + bd + 30, Y0, top - FH, wall, 'tijolo', top=False)
        B.flat_roof(F, au, au + 16, v0 + bd, v0 + bd + 30, top - FH, 0.8, (230, 226, 218), False)
    # entrada: avanco envidracado de pe-direito duplo, marquise, letreiro e relogio
    uc = u0 + bw / 2
    B.box(F, uc - 5, uc + 5, v0 - 3, v0, Y0, Y0 + 2 * FH + 0.6, (70, 110, 150), 'vidro')
    B.box(F, uc - 5.4, uc + 5.4, v0 - 3.4, v0 + 0.2, Y0 + 2 * FH + 0.6, Y0 + 2 * FH + 1.2, (240, 236, 228), 'concreto')
    B.box(F, uc - 7, uc + 7, v0 - 7, v0 - 3, Y0 + 3.2, Y0 + 3.5, (240, 236, 228), 'concreto')
    for s_ in (-1, 1): _cyl(M, F, uc + s_ * 6.6, v0 - 6.6, 0.18, Y0, Y0 + 3.2, (230, 120, 40), 'metal', 10)
    B.panel(F, uc - 2.0, uc + 2.0, v0 - 3, Y0, Y0 + 2.9, (180, 210, 225), 'vidro', -1, 0.05)
    B.box(F, uc - 6, uc + 6, v0 - 3.5, v0 - 3.2, top - 2.6, top - 0.6, (40, 70, 120), 'liso')
    for k in range(6): B.box(F, uc - 5.2 + k * 1.8, uc - 4.0 + k * 1.8, v0 - 3.55, v0 - 3.5, top - 2.2, top - 1.0, band[k % 3], 'liso')
    x, z = F.xz(uc, v0 - 0.06); M.m('liso')
    M.poly([(x + F.ux * math.cos(a) * 1.0, top - 3.8 + math.sin(a) * 1.0, z + F.uz * math.cos(a) * 1.0) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)], (250, 248, 240), F.nv(-1))
    B.drives.append((*F.xz(uc, v0 - 5.0), 4.0))
    # ginasio com telhado em arco atras da ala direita
    gu0, gv0 = u0 + bw + 6, v0 + 4; gw, gd = 30.0, 22.0
    if gu0 + gw < w - 4:
        B.box(F, gu0, gu0 + gw, gv0, gv0 + gd, Y0, Y0 + 7.0, (200, 205, 210), 'concreto', top=False)
        n = 12; M.m('metal')
        for k in range(n):
            a0 = math.pi * k / n; a1 = math.pi * (k + 1) / n
            v_a = gv0 + gd / 2 - math.cos(a0) * gd / 2; v_b = gv0 + gd / 2 - math.cos(a1) * gd / 2
            ya = Y0 + 7.0 + math.sin(a0) * 4.5; yb = Y0 + 7.0 + math.sin(a1) * 4.5
            M.quad(F.p(gu0, v_a, ya), F.p(gu0 + gw, v_a, ya), F.p(gu0 + gw, v_b, yb), F.p(gu0, v_b, yb), (60, 140, 200), None)
        for uu in (gu0, gu0 + gw):
            pts = [F.p(uu, gv0 + gd / 2 - math.cos(math.pi * k / n) * gd / 2, Y0 + 7.0 + math.sin(math.pi * k / n) * 4.5) for k in range(n + 1)]
            M.m('concreto'); M.poly(pts, (200, 205, 210), F.nu(1 if uu > gu0 else -1))
        for k in range(int(gw / 4)): B.window(F, gu0 + 2 + k * 4, gv0, Y0 + 4.2, 2.6, 1.4, -1)
        B.solid(F, gu0, gu0 + gw, gv0, gv0 + gd)
    # campo com pista nos fundos
    fu0, fu1 = u0 + 18, u0 + bw - 18; fv0, fv1 = v0 + bd + 4, min(d - 6, v0 + bd + 30)
    if fu1 - fu0 > 20 and fv1 - fv0 > 14:
        M.m('quadra'); M.poly([F.p(fu0, fv0, Y0 + 0.06), F.p(fu1, fv0, Y0 + 0.06), F.p(fu1, fv1, Y0 + 0.06), F.p(fu0, fv1, Y0 + 0.06)], (200, 120, 90), (0, 1, 0))
        M.m('grama'); M.poly([F.p(fu0 + 3, fv0 + 3, Y0 + 0.1), F.p(fu1 - 3, fv0 + 3, Y0 + 0.1), F.p(fu1 - 3, fv1 - 3, Y0 + 0.1), F.p(fu0 + 3, fv1 - 3, Y0 + 0.1)], (110, 170, 90), (0, 1, 0))
    # mastros, bicicletario e jardim da frente
    for q, fc in enumerate(((40, 140, 70), (30, 60, 150), (230, 120, 40))):
        mu = u0 + 4 + q * 1.6
        _cyl(M, F, mu, 4.0, 0.06, Y0, Y0 + 9.0, (230, 230, 232), 'metal', 8)
        a, b = F.xz(mu + 0.06, 4.0); c_, e = F.xz(mu + 1.8, 4.0); M.m('liso'); M.box(min(a, c_), max(a, c_), Y0 + 7.7, Y0 + 8.8, min(b, e) - 0.02, max(b, e) + 0.02, fc)
    for k in range(8):
        bu = u0 + bw - 14 + k * 0.8; _cyl(M, F, bu, 6.0, 0.03, Y0, Y0 + 0.8, (160, 164, 170), 'metal', 5)
    B.parking(F, u0 + bw + 4, w - 4, v0 + gd + 10 if gu0 + gw < w - 4 else v0, min(d - 6, v0 + gd + 30), field_cb)
    B.solid(F, u0, u0 + bw, v0, v0 + bd); B.solid(F, uc - 5, uc + 5, v0 - 3, v0)
