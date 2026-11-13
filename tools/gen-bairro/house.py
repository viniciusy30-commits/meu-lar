"""Casas e adereços no estilo americano de bairro (subúrbio). Tudo em coordenadas locais da casa:
u = ao longo da largura, v = profundidade (a FRENTE é -v), y = altura. ang como no Relevo.kt:
  x = cx + cos(a)*u - sin(a)*v ; z = cz + sin(a)*u + cos(a)*v   (frente = (sin a, -cos a))
"""
import math, random
from bake import *

WHITE = rgb('#F7F5F0'); TRIM = rgb('#F4F1E8'); GLASS = rgb('#3B536B'); GLASS2 = rgb('#6E8CA6')
CONC = rgb('#B9B5AC'); CONC_D = rgb('#A29E95'); FOUND = rgb('#9B978E'); BRICK = rgb('#9C5A44'); BRICK_D = rgb('#7E4636')
WOODC = rgb('#8B6B4A'); DARK = rgb('#33363B')

SIDING = ['#F1ECDD', '#E4D9BC', '#C9D8E3', '#BCCFC1', '#E8CFA8', '#D6C7B0', '#F3E6B8', '#B8C7D2', '#E7D3CF', '#D9D9D2', '#A9BCAE', '#EADFC8']
ROOFC = ['#4F4A47', '#5B514B', '#3F4448', '#6B4F44', '#57606A', '#463F3A']
ACCENT = ['#2E4A6B', '#8B2E2E', '#2F5D45', '#1F2D3D', '#6E3B2A', '#3B3B3B', '#7C2D3A']
CARS = ['#B71C1C', '#1E3A5F', '#CFD2D6', '#2B2B2E', '#7B8189', '#3E6B4B', '#E0B64A', '#F5F5F5']


class H:
    def __init__(self, bk, hfun, cx, cz, ang):
        self.b = bk; self.h = hfun; self.cx = cx; self.cz = cz; self.a = ang
        self.c = math.cos(ang); self.s = math.sin(ang)

    def W(self, u, v):
        return (self.cx + self.c * u - self.s * v, self.cz + self.s * u + self.c * v)

    def N(self, nu, nv):
        return (self.c * nu - self.s * nv, self.s * nu + self.c * nv)

    # caixa local [u0,u1]x[v0,v1]x[y0,y1]
    def box(self, u0, u1, v0, v1, y0, y1, col, mat=PLAIN, top=True, bottom=False):
        c4 = [self.W(u0, v0), self.W(u1, v0), self.W(u1, v1), self.W(u0, v1)]
        self.b.obox_pts(c4, y0, y1, col, mat, top, bottom)

    def quadL(self, pts, n, col, mat=PLAIN, uv=None, lit=True):
        """pts: lista de (u, v, y); n: normal local (nu, ny, nv)"""
        P = []
        for (u, v, y) in pts:
            x, z = self.W(u, v)
            P.append((x, y, z))
        nx, nz = self.N(n[0], n[2])
        self.b.quad(mat, P, (nx, n[1], nz), col, uv, lit)

    def triL(self, pts, n, col, mat=PLAIN):
        P = []
        for (u, v, y) in pts:
            x, z = self.W(u, v)
            P.append((x, y, z))
        nx, nz = self.N(n[0], n[2])
        self.b.tri(mat, P[0], P[1], P[2], (nx, n[1], nz), col)

    # prisma de telhado: seção no plano (s, y) extrudada ao longo do outro eixo.
    # axis 'u': extrude ao longo de u (seção em v,y);  axis 'v': extrude ao longo de v (seção em u,y)
    def roof(self, axis, t0, t1, s0, s1, ye, ridge, col, gable_col, fascia=TRIM, thick=0.22, flatridge=0.0):
        sm = (s0 + s1) / 2
        yb = ye; yt = ye + thick; yr = ye + thick + ridge
        sec = [(s0, yb), (s0, yt), (sm, yr), (s1, yt), (s1, yb)]

        def L(s, t, y):
            return (t, s, y) if axis == 'u' else (s, t, y)   # (u, v, y)
        # fachadas das 5 arestas
        norms = []
        for i in range(5):
            a = sec[i]; b = sec[(i + 1) % 5]
            ds, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(ds, dy)
            ns, ny = dy / ln, -ds / ln       # perpendicular
            ms, my = (a[0] + b[0]) / 2 - sm, (a[1] + b[1]) / 2 - (yb + yr) / 2
            if ns * ms + ny * my < 0:
                ns, ny = -ns, -ny
            norms.append((ns, ny))
        for i in range(5):
            a = sec[i]; b = sec[(i + 1) % 5]
            ns, ny = norms[i]
            nloc = (0.0, ny, ns) if axis == 'u' else (ns, ny, 0.0)
            c = col
            if i in (0, 3):
                c = fascia
            elif i == 4:
                c = shade(col, -25)
            p = [L(a[0], t0, a[1]), L(a[0], t1, a[1]), L(b[0], t1, b[1]), L(b[0], t0, b[1])]
            self.quadL(p, nloc, c, ROOF if i in (1, 2) else PLAIN)
        # tampas (empenas)
        for (t, sgn) in ((t0, -1.0), (t1, 1.0)):
            nloc = (sgn, 0.0, 0.0) if axis == 'v' else (0.0, 0.0, sgn)
            nloc = (0.0, 0.0, sgn) if axis == 'u' else nloc
            if axis == 'u':
                nloc = (sgn, 0.0, 0.0)
            else:
                nloc = (0.0, 0.0, sgn)
            pts = [L(s, t, y) for (s, y) in sec]
            for k in range(1, 4):
                self.triL([pts[0], pts[k], pts[k + 1]], nloc, gable_col)

    # peça sobre a parede: face 'F' frente (v=-d/2), 'B' fundos, 'L' esquerda (u=-w/2), 'R' direita
    def wall_item(self, face, w, d, t0, t1, y0, y1, depth, col, mat=PLAIN, inset=0.0):
        if face == 'F':
            self.box(t0, t1, -d / 2 - depth, -d / 2 + inset, y0, y1, col, mat)
        elif face == 'B':
            self.box(t0, t1, d / 2 - inset, d / 2 + depth, y0, y1, col, mat)
        elif face == 'L':
            self.box(-w / 2 - depth, -w / 2 + inset, t0, t1, y0, y1, col, mat)
        else:
            self.box(w / 2 - inset, w / 2 + depth, t0, t1, y0, y1, col, mat)

    def window(self, face, w, d, t, y0, ww, wh, shut=None, flower=False):
        # vidro, moldura branca, travessas, peitoril, venezianas
        g = 0.045
        self.wall_item(face, w, d, t - ww / 2, t + ww / 2, y0, y0 + wh, 0.03, GLASS)
        # reflexo claro na metade de cima
        self.wall_item(face, w, d, t - ww / 2 + 0.04, t + ww / 2 - 0.04, y0 + wh * 0.55, y0 + wh - 0.05, 0.035, GLASS2)
        f = 0.07
        self.wall_item(face, w, d, t - ww / 2 - f, t + ww / 2 + f, y0 + wh, y0 + wh + f, 0.08, WHITE)
        self.wall_item(face, w, d, t - ww / 2 - f, t - ww / 2, y0, y0 + wh, 0.08, WHITE)
        self.wall_item(face, w, d, t + ww / 2, t + ww / 2 + f, y0, y0 + wh, 0.08, WHITE)
        self.wall_item(face, w, d, t - ww / 2 - 0.1, t + ww / 2 + 0.1, y0 - 0.07, y0, 0.13, WHITE)
        self.wall_item(face, w, d, t - 0.025, t + 0.025, y0, y0 + wh, 0.07, WHITE)
        self.wall_item(face, w, d, t - ww / 2, t + ww / 2, y0 + wh * 0.5 - 0.025, y0 + wh * 0.5 + 0.025, 0.07, WHITE)
        if shut is not None:
            sw = ww * 0.32
            self.wall_item(face, w, d, t - ww / 2 - f - sw, t - ww / 2 - f, y0 - 0.05, y0 + wh + f, 0.06, shut)
            self.wall_item(face, w, d, t + ww / 2 + f, t + ww / 2 + f + sw, y0 - 0.05, y0 + wh + f, 0.06, shut)
        if flower:   # floreira
            self.wall_item(face, w, d, t - ww / 2, t + ww / 2, y0 - 0.32, y0 - 0.07, 0.22, WOODC)
            self.wall_item(face, w, d, t - ww / 2 + 0.05, t + ww / 2 - 0.05, y0 - 0.12, y0 + 0.06, 0.2, rgb('#C2457A'))


def lamp_free(r, *a):
    return r.random() < 0.5


def make_house(bk, hfun, spec, rnd):
    """spec: x, z, ang, style, w, d, floors, garage(0/1/2), gside(-1/1), seed.  Devolve dict com pegada e extras."""
    st = spec['style']
    cx, cz, ang = spec['x'], spec['z'], spec['ang']
    w, d, fl = spec['w'], spec['d'], spec['floors']
    h = H(bk, hfun, cx, cz, ang)
    wall = rgb(spec['wall']); roofc = rgb(spec['roof']); acc = rgb(spec['accent'])
    # alturas do terreno sob a pegada (cantos) para assentar a casa
    gs = []
    for (u, v) in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2), (0, 0), (0, -d / 2 - 3.0)):
        x, z = h.W(u, v); gs.append(hfun(x, z))
    gmin, gmax = min(gs), max(gs)
    y0 = gmax + 0.42                     # piso: fundação aparente de ~40 cm
    floorH = 2.75
    H1 = floorH * fl + (0.25 if fl > 1 else 0.0)
    ytop = y0 + H1
    gw_ = spec.get('garage', 0); gside = spec.get('gside', 1)
    gwid = 3.5 if gw_ == 1 else 6.1
    gdep = 6.6; ghgt = 2.7
    gre = spec.get('grecess', 0.0)       # recuo da garagem em relação à frente da casa

    # ---- fundação e paredes
    h.box(-w / 2 - 0.12, w / 2 + 0.12, -d / 2 - 0.12, d / 2 + 0.12, gmin - 0.7, y0 + 0.02, FOUND, PLAIN, top=False)
    h.box(-w / 2, w / 2, -d / 2, d / 2, y0, ytop, wall, PLASTER, top=False)
    # tábuas de canto + faixa entre andares + rodapé
    for (u, v) in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
        h.box(u - 0.07, u + 0.07, v - 0.07, v + 0.07, y0, ytop, WHITE, PLAIN, top=False)
    if fl > 1:
        h.box(-w / 2 - 0.04, w / 2 + 0.04, -d / 2 - 0.04, d / 2 + 0.04, y0 + floorH, y0 + floorH + 0.2, WHITE, PLAIN, top=False)
    # ---- telhado principal
    ridge_h = min(d, w) * 0.30 + 0.25
    front_gable = st in ('craftsman', 'cape') and spec.get('fg', False)
    ov = 0.55
    if not front_gable:
        h.roof('u', -w / 2 - 0.4, w / 2 + 0.4, -d / 2 - ov, d / 2 + ov, ytop, ridge_h, roofc, wall)
        ridge_y = ytop + 0.22 + ridge_h
    else:
        h.roof('v', -d / 2 - ov, d / 2 + ov, -w / 2 - 0.4, w / 2 + 0.4, ytop, w * 0.30 + 0.2, roofc, wall)
        ridge_y = ytop + 0.22 + w * 0.30 + 0.2
    # ---- janelas da frente (e laterais/fundos)
    door_u = spec.get('door_u', 0.0)
    shut = acc if spec.get('shutters', st == 'colonial') else None
    cols = max(2, int(w // 3.2))
    for f_i in range(fl):
        yb = y0 + f_i * (floorH + 0.25) + 0.85
        for k in range(cols):
            t = -w / 2 + (k + 0.5) * w / cols
            if f_i == 0 and abs(t - door_u) < 1.25:
                continue
            if gw_ and f_i == 0 and ((gside > 0 and t > w / 2 - 1.0 and False)):
                continue
            h.window('F', w, d, t, yb, 1.05, 1.35, shut, flower=(f_i == 0 and spec.get('flowers', False) and k % 2 == 0))
        for k in range(max(1, int(d // 3.6))):
            t = -d / 2 + (k + 0.5) * d / max(1, int(d // 3.6))
            if not (gw_ and ((gside < 0))):
                h.window('L', w, d, t, yb, 1.0, 1.3, None)
            if not (gw_ and ((gside > 0))):
                h.window('R', w, d, t, yb, 1.0, 1.3, None)
        for k in range(cols):
            t = -w / 2 + (k + 0.5) * w / cols
            h.window('B', w, d, t, yb, 1.0, 1.3, None)
    # ---- porta e varanda
    dw, dh = 1.05, 2.15
    doorc = acc
    h.wall_item('F', w, d, door_u - dw / 2 - 0.09, door_u + dw / 2 + 0.09, y0, y0 + dh + 0.09, 0.07, WHITE)
    h.wall_item('F', w, d, door_u - dw / 2, door_u + dw / 2, y0, y0 + dh, 0.12, doorc)
    h.wall_item('F', w, d, door_u - 0.32, door_u + 0.32, y0 + 1.35, y0 + 1.95, 0.14, GLASS)
    h.wall_item('F', w, d, door_u + dw / 2 - 0.22, door_u + dw / 2 - 0.14, y0 + 0.95, y0 + 1.05, 0.17, rgb('#D6B24A'))   # maçaneta
    pw = 3.0 if st in ('colonial', 'craftsman') else 2.4
    pd = 1.9
    pu0, pu1 = door_u - pw / 2, door_u + pw / 2
    h.box(pu0, pu1, -d / 2 - pd, -d / 2, gmin - 0.4, y0 + 0.04, CONC, PLAIN)           # plataforma
    h.box(pu0 + 0.25, pu1 - 0.25, -d / 2 - pd - 0.55, -d / 2 - pd, gmin - 0.4, y0 - 0.2, CONC_D, PLAIN)   # degrau
    # colunas e telhadinho
    pcols = [pu0 + 0.18, pu1 - 0.18]
    for u in pcols:
        h.box(u - 0.09, u + 0.09, -d / 2 - pd + 0.1, -d / 2 - pd + 0.28, y0 + 0.04, y0 + 2.75, WHITE, PLAIN, top=False)
    if st in ('colonial', 'craftsman', 'cape'):
        h.roof('v', -d / 2 - pd - 0.35, -d / 2 + 0.02, pu0 - 0.35, pu1 + 0.35, y0 + 2.75, 0.75, roofc, wall)
    else:   # rancho: aba inclinada simples
        h.roof('v', -d / 2 - pd - 0.35, -d / 2 + 0.02, pu0 - 0.3, pu1 + 0.3, y0 + 2.75, 0.15, roofc, wall)
    # corrimão baixo na varanda (lado oposto à porta fica aberto)
    if spec.get('flag', False):
        x1, z1 = h.W(pu0 + 0.18, -d / 2 - pd + 0.2)
        # mastro inclinado simples (haste) e bandeira (listras)
        for i in range(7):
            col = rgb('#B22234') if i % 2 == 0 else rgb('#FFFFFF')
            h.box(pu0 - 0.62, pu0 - 0.2, -d / 2 - pd + 0.05, -d / 2 - pd + 0.08, y0 + 1.95 - i * 0.075, y0 + 1.95 - (i + 1) * 0.075, col, PLAIN, False)
        h.box(pu0 - 0.62, pu0 - 0.42, -d / 2 - pd + 0.049, -d / 2 - pd + 0.081, y0 + 1.95 - 0.30, y0 + 1.95, rgb('#3C3B6E'), PLAIN, False)
        h.box(pu0 - 0.66, pu0 - 0.62, -d / 2 - pd + 0.0, -d / 2 - pd + 0.1, y0 + 1.7, y0 + 2.2, WHITE, PLAIN, True)
    # ---- garagem
    foot = [(-w / 2 - 0.5, -d / 2 - pd - 0.6, w / 2 + 0.5, d / 2 + 0.5)]   # (u0, v0, u1, v1) da pegada
    drive = None
    if gw_:
        if gside > 0:
            gu0, gu1 = w / 2 - 0.05, w / 2 - 0.05 + gwid
        else:
            gu1, gu0 = -w / 2 + 0.05, -w / 2 + 0.05 - gwid
        gv0 = -d / 2 + gre; gv1 = gv0 + gdep
        yg = y0 - 0.12
        h.box(gu0 - 0.1, gu1 + 0.1, gv0 - 0.1, gv1 + 0.1, gmin - 0.7, yg + 0.02, FOUND, PLAIN, top=False)
        h.box(gu0, gu1, gv0, gv1, yg, yg + ghgt, wall, PLASTER, top=False)
        h.roof('v', gv0 - 0.5, gv1 + 0.1, gu0 - 0.35, gu1 + 0.35, yg + ghgt, gwid * 0.22 + 0.1, roofc, wall)
        # porta de garagem com painéis e janelinhas
        gdw = gwid - 0.55
        gc = (gu0 + gu1) / 2
        gdoor = rgb('#EFEBE1') if sum(wall) > 620 else rgb('#E7E2D6')
        h.box(gc - gdw / 2 - 0.08, gc + gdw / 2 + 0.08, gv0 - 0.09, gv0 - 0.0, yg, yg + 2.28, WHITE, PLAIN)
        h.box(gc - gdw / 2, gc + gdw / 2, gv0 - 0.14, gv0 - 0.03, yg, yg + 2.2, gdoor, PLAIN)
        for k in range(1, 4):
            h.box(gc - gdw / 2, gc + gdw / 2, gv0 - 0.16, gv0 - 0.14, yg + k * 0.55 - 0.02, yg + k * 0.55 + 0.02, shade(gdoor, -45), PLAIN)
        npan = 4 if gw_ == 2 else 3
        for k in range(npan):
            uc = gc - gdw / 2 + (k + 0.5) * gdw / npan
            h.box(uc - 0.2, uc + 0.2, gv0 - 0.17, gv0 - 0.14, yg + 1.72, yg + 1.98, GLASS, PLAIN)
        if gw_ == 2:
            h.box(gc - 0.02, gc + 0.02, gv0 - 0.17, gv0 - 0.14, yg, yg + 2.2, shade(gdoor, -45), PLAIN)
        foot.append((min(gu0, gu1) - 0.5, gv0 - 0.5, max(gu0, gu1) + 0.5, gv1 + 0.5))
        drive = dict(u0=gc - gdw / 2, u1=gc + gdw / 2, v=gv0 - 0.1, yg=yg)
    # ---- chaminé
    if spec.get('chimney', True) and not front_gable:
        cu = (-w / 2 + 1.0) if (not gw_ or gside > 0) else (w / 2 - 1.0)
        h.box(cu - 0.45, cu + 0.45, -0.35, 0.35, y0 + 0.2, ridge_y + 0.9, BRICK, PLAIN, False)
        h.box(cu - 0.52, cu + 0.52, -0.42, 0.42, ridge_y + 0.9, ridge_y + 1.05, BRICK_D, PLAIN, True)
    # ---- caminho/entrada, arbustos junto à fundação
    for sgn, uu in ((-1, pu0 - 0.9), (1, pu1 + 0.9)):
        n = 3
        for k in range(n):
            ub = uu + sgn * k * 1.5
            if abs(ub - door_u) < pw / 2 + 0.4:
                continue
            if gw_ and ((gside > 0 and ub > w / 2 - 0.6) or (gside < 0 and ub < -w / 2 + 0.6)):
                continue
            if abs(ub) > w / 2 - 0.2:
                continue
            bush(h, ub, -d / 2 - 0.55, rnd)
    return dict(h=h, y0=y0, foot=foot, drive=drive, pd=pd, pw=pw, door_u=door_u, gmin=gmin, w=w, d=d, ridge=ridge_y)


def bush(h, u, v, rnd, s=None):
    s = s or rnd.uniform(0.38, 0.6)
    x, z = h.W(u, v)
    g = h.h(x, z)
    c = mixc(rgb('#3F8A4B'), rgb('#5FAE5A'), rnd.random())
    h.b.cyl(x, z, s, g - 0.05, g + s * 1.5, shade(c, -10), 7, PLAIN, True, s * 0.55)
    h.b.cyl(x, z, s * 0.75, g + s * 1.3, g + s * 1.9, c, 7, PLAIN, True, s * 0.15)
    if rnd.random() < 0.35:
        h.b.cyl(x, z, s * 0.9, g + s * 0.9, g + s * 1.2, rgb('#D95F8F'), 6, PLAIN, False, s * 0.6)


def car(bk, hfun, x, z, ang, color):
    """carro simples de passeio: ang = direção do comprimento (rad)"""
    h = H(bk, hfun, x, z, ang)
    g = hfun(x, z)
    col = rgb(color)
    L = 4.5; Wd = 1.8
    h.box(-L / 2, L / 2, -Wd / 2, Wd / 2, g + 0.28, g + 0.82, col, PLAIN)
    h.box(-L * 0.18, L * 0.22, -Wd / 2 + 0.07, Wd / 2 - 0.07, g + 0.82, g + 1.32, shade(col, 8), PLAIN)
    h.box(-L * 0.17, L * 0.21, -Wd / 2 + 0.05, Wd / 2 - 0.05, g + 0.86, g + 1.26, GLASS, PLAIN, False)
    h.box(-L * 0.19, L * 0.23, -Wd / 2 + 0.09, Wd / 2 - 0.09, g + 1.3, g + 1.34, shade(col, -20), PLAIN)
    for (uu, vv) in ((-L * 0.3, -Wd / 2), (L * 0.3, -Wd / 2), (-L * 0.3, Wd / 2), (L * 0.3, Wd / 2)):
        h.box(uu - 0.33, uu + 0.33, vv - 0.1, vv + 0.1, g + 0.0, g + 0.62, rgb('#1B1B1D'), PLAIN)
    h.box(L / 2 - 0.02, L / 2 + 0.02, -Wd / 2 + 0.15, -Wd / 2 + 0.45, g + 0.55, g + 0.7, rgb('#FFF3C4'), PLAIN)
    h.box(L / 2 - 0.02, L / 2 + 0.02, Wd / 2 - 0.45, Wd / 2 - 0.15, g + 0.55, g + 0.7, rgb('#FFF3C4'), PLAIN)
    h.box(-L / 2 - 0.02, -L / 2 + 0.02, -Wd / 2 + 0.12, -Wd / 2 + 0.5, g + 0.6, g + 0.72, rgb('#B3261E'), PLAIN)
    h.box(-L / 2 - 0.02, -L / 2 + 0.02, Wd / 2 - 0.5, Wd / 2 - 0.12, g + 0.6, g + 0.72, rgb('#B3261E'), PLAIN)


def mailbox(bk, hfun, x, z, ang, rnd):
    """caixa de correio na beira da calçada; ang = rumo da frente (para a casa)"""
    h = H(bk, hfun, x, z, ang)
    g = hfun(x, z)
    h.box(-0.05, 0.05, -0.05, 0.05, g, g + 1.0, WOODC, PLAIN)
    h.box(-0.12, 0.12, -0.3, 0.3, g + 1.0, g + 1.26, rgb('#2D2F33') if rnd.random() < 0.6 else rgb('#2E5C9A'), PLAIN)
    h.box(0.12, 0.15, 0.12, 0.2, g + 1.14, g + 1.42, rgb('#C62828'), PLAIN)


def trash_cans(bk, hfun, x, z, ang):
    h = H(bk, hfun, x, z, ang)
    g = hfun(x, z)
    for k, c in enumerate(('#2F5D45', '#2E4A6B')):
        u = k * 0.7
        h.box(u - 0.27, u + 0.27, -0.27, 0.27, g, g + 0.95, rgb(c), PLAIN)
        h.box(u - 0.3, u + 0.3, -0.3, 0.3, g + 0.95, g + 1.02, shade(rgb(c), -25), PLAIN)


def picket_fence(bk, hfun, x0, z0, x1, z1, col=WHITE, hgt=0.95):
    L = math.hypot(x1 - x0, z1 - z0)
    if L < 0.5:
        return
    n = max(2, int(L / 0.42))
    ang = math.atan2(z1 - z0, x1 - x0)
    h = H(bk, hfun, x0, z0, ang)
    for k in range(n + 1):
        u = L * k / n
        x, z = h.W(u, 0)
        g = hfun(x, z)
        h.box(u - 0.035, u + 0.035, -0.012, 0.012, g, g + hgt, col, PLAIN)
    for k in range(0, n, 6):
        u0 = L * k / n; u1 = L * min(n, k + 6) / n
        xa, za = h.W(u0, 0); g = hfun(xa, za)
        h.box(u0, u1, -0.03, 0.03, g + 0.22, g + 0.3, col, PLAIN)
        h.box(u0, u1, -0.03, 0.03, g + 0.62, g + 0.7, col, PLAIN)
        h.box(u0 - 0.05, u0 + 0.05, -0.05, 0.05, g, g + hgt + 0.08, col, PLAIN)


def hedge(bk, hfun, x0, z0, x1, z1, hgt=0.9, wid=0.7, rnd=None):
    L = math.hypot(x1 - x0, z1 - z0)
    n = max(1, int(L / 1.2))
    ang = math.atan2(z1 - z0, x1 - x0)
    h = H(bk, hfun, x0, z0, ang)
    for k in range(n):
        u0 = L * k / n; u1 = L * (k + 1) / n
        xa, za = h.W((u0 + u1) / 2, 0); g = hfun(xa, za)
        c = rgb('#3C7F49')
        h.box(u0, u1 + 0.02, -wid / 2, wid / 2, g - 0.05, g + hgt, shade(c, (k % 3) * 6 - 6), PLAIN)


def utility_pole(bk, hfun, x, z, ang):
    g = hfun(x, z)
    h = H(bk, hfun, x, z, ang)
    h.box(-0.12, 0.12, -0.12, 0.12, g, g + 9.0, rgb('#6B5538'), PLAIN)
    h.box(-1.1, 1.1, -0.07, 0.07, g + 8.2, g + 8.36, rgb('#5B4A33'), PLAIN)
    h.box(-0.9, 0.9, -0.07, 0.07, g + 7.5, g + 7.64, rgb('#5B4A33'), PLAIN)
    for u in (-1.0, 0.0, 1.0):
        h.box(u - 0.04, u + 0.04, -0.04, 0.04, g + 8.36, g + 8.52, rgb('#E8E8E8'), PLAIN)
    bk.cyl(*h.W(0.45, 0.0), 0.22, g + 6.6, g + 7.35, rgb('#7A8086'), 8, PLAIN, True)


def stop_sign(bk, hfun, x, z, ang):
    """placa PARE com as duas faces; ang = direção para onde a face aponta (rad, frente = (sin a, -cos a))"""
    g = hfun(x, z)
    h = H(bk, hfun, x, z, ang)
    h.box(-0.04, 0.04, -0.04, 0.04, g, g + 2.2, rgb('#8E9298'), PLAIN)
    n = 8
    ys = g + 2.05

    def octa(r, vv, col, nrm):
        pts = []
        for k in range(n):
            a = math.pi / 8 + 2 * math.pi * k / n
            pts.append((r * math.cos(a), vv, ys + r * math.sin(a)))
        for k in range(1, n - 1):
            h.triL([pts[0], pts[k], pts[k + 1]], (0, 0, nrm), col)
    octa(0.4, -0.06, rgb('#FFFFFF'), -1)
    octa(0.36, -0.065, rgb('#C62828'), -1)
    octa(0.4, 0.06, rgb('#FFFFFF'), 1)
    octa(0.36, 0.065, rgb('#C62828'), 1)
    # "tarja" branca (o texto PARE não tem textura aqui)
    h.box(-0.24, 0.24, -0.07, -0.066, ys - 0.045, ys + 0.045, rgb('#FFFFFF'), PLAIN, False)


def street_sign(bk, hfun, x, z, ang):
    """plaquinha verde de nome de rua"""
    g = hfun(x, z)
    h = H(bk, hfun, x, z, ang)
    h.box(-0.035, 0.035, -0.035, 0.035, g, g + 2.6, rgb('#8E9298'), PLAIN)
    h.box(-0.5, 0.5, -0.03, 0.03, g + 2.42, g + 2.7, rgb('#1F6B3A'), PLAIN)
    h.box(-0.46, 0.46, -0.035, -0.031, g + 2.46, g + 2.66, rgb('#F4F4F0'), PLAIN, False)
