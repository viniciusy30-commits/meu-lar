"""Cidade 6 - casas de suburbio americano (v2): 7 estilos com volumes compostos (alas, varandas, aguas-furtadas), beirais com
testeira, janelas com verga/peitoril/floreira, garagem ligada a rua por entrada com rampa na guia, caminho da porta,
jardim de fundacao e quintal mobiliado (patio, piscina, deck, balanco, cama elastica, horta, deposito, cerca viva).
Referencial do lote: u ao longo da rua (0..w), v para dentro (0..d). A calcada fica em v<0 (1,8 m) e a faixa de grama ate -3,6."""
import math
from mesh import rgb, shade, mix, WHITE, Frame

Y0 = 0.13
TRIM = (246, 244, 238)
ROOFS = [rgb(c) for c in ('#5F6266', '#4A4D52', '#6E5A4C', '#3F4650', '#7A5F52', '#54463E', '#5E6B5C', '#7C7068', '#8A4A3E', '#4E5A66')]
SIDING = [rgb(c) for c in ('#F3F0E8', '#E6DFCC', '#DAE4E8', '#C4D4DA', '#E8D9BF', '#D2DAC2', '#F0E3CC', '#B9CCD6', '#E3CFBE', '#D5CEE0', '#B2C2AA',
                           '#F2E6C4', '#A7C0D2', '#E4C4A4', '#C4D6B2', '#F0D2CA', '#8FA9BC', '#C9B79C', '#9DB29A', '#E9E9E4', '#7F98A8', '#D6A58C')]
STUCCO = [rgb(c) for c in ('#F3ECDF', '#EEE2CE', '#F6F1E7', '#E6D6C0', '#F1DCC2', '#EFD9C8', '#E4E0D4')]
DOORS = [rgb(c) for c in ('#8A2A2A', '#27445F', '#2B5A3C', '#33363A', '#9A6A34', '#F3F1EB', '#1D2C47', '#C7A13A', '#6A3E7A', '#C2552E')]
SHUTTERS = [rgb(c) for c in ('#2C3C2C', '#2B3A52', '#353535', '#5A2828', '#F5F3ED', '#3E5A6A', '#6A4A2E')]
FENCES = [((252, 252, 250), 'cerca'), ((214, 186, 150), 'cerca'), ((190, 160, 124), 'cerca'), ((236, 224, 204), 'cerca'), ((168, 140, 110), 'cerca'), ((250, 248, 242), 'cerca')]
FLOWERS = [(232, 78, 120), (250, 214, 80), (244, 244, 248), (190, 110, 224), (246, 148, 56), (236, 60, 60), (120, 150, 240)]
STYLES = ('ranch', 'colonial', 'craftsman', 'cape', 'moderna', 'farmhouse', 'mediterranea')
FLOORS = {'ranch': 1, 'colonial': 2, 'craftsman': 1, 'cape': 1, 'moderna': 2, 'farmhouse': 2, 'mediterranea': 1}


def palette(style, rnd, base=None):
    """(parede, material, telhado, material do telhado, porta, veneziana, acabamento)"""
    if style == 'moderna': return (rnd.choice(STUCCO[:3] + [rgb('#D9DADC'), rgb('#3E4247')]), 'reboco', (236, 234, 228), 'concreto', rnd.choice(DOORS), None, (60, 62, 66))
    if style == 'mediterranea': return (rnd.choice(STUCCO), 'reboco', (255, 255, 255), 'ceramica', rnd.choice(DOORS[:5]), None, (240, 232, 216))
    if style == 'farmhouse': return (rnd.choice(((250, 250, 246), (236, 238, 234), (58, 64, 70), (222, 228, 232))), 'siding', rnd.choice(((70, 74, 80), (56, 58, 62), (110, 60, 50))), 'metal', rnd.choice(DOORS), None, TRIM)
    if rnd.random() < (0.45 if style == 'colonial' else 0.18): wall, wm = (255, 255, 255), 'tijolo'
    else:
        i = int((base if base is not None else rnd.random()) * len(SIDING) + rnd.randint(0, 6)) % len(SIDING); wall, wm = SIDING[i], 'siding'
    return (wall, wm, rnd.choice(ROOFS), 'telha', rnd.choice(DOORS), rnd.choice(SHUTTERS) if style in ('colonial', 'cape') or rnd.random() < 0.25 else None, TRIM)


class House:
    def __init__(self, B, F, w, d, style, pal, sf, gside, rnd, fence=True, first=False, picket=False, corner=False):
        self.B, self.F, self.M, self.r = B, F, B.M, rnd
        self.w, self.d, self.style, self.sf, self.gs = w, d, style, sf, gside
        self.wall, self.wm, self.roofc, self.rm, self.doorc, self.shut, self.trim = pal
        self.plants = []            # (u, v, tipo, escala)
        self.fence, self.first, self.picket = fence, first, picket
        self.yb = Y0 + (0.5 if style in ('colonial', 'farmhouse', 'craftsman') else 0.32)
        self.fh = 2.8
        self.lights = []

    # ------------------------------------------------------------ pecas
    def box(self, u0, u1, v0, v1, y0, y1, col, mat, top=True, **k): self.B.box(self.F, u0, u1, v0, v1, y0, y1, col, mat, top, **k)

    def axes(self, along_u):
        F = self.F
        if along_u: return (lambda a, b, y: F.p(a, b, y)), F.nu, F.nv
        return (lambda a, b, y: F.p(b, a, y)), F.nv, F.nu

    def gable(self, u0, u1, v0, v1, y, rh, along_u=True, over=0.45, walls=True, wallc=None, wallm=None):
        """telhado de duas aguas com beiral, testeira branca e forro; along_u: cumeeira paralela a rua"""
        M = self.M; P, na, nb = self.axes(along_u)
        a0, a1, b0, b1 = (u0, u1, v0, v1) if along_u else (v0, v1, u0, u1)
        bm = (b0 + b1) / 2; k = rh / ((b1 - b0) / 2); ye = y - over * k; t = 0.16
        La = a1 - a0 + 2 * over; Ls = math.hypot(bm - b0 + over, rh + over * k)
        fc = self.trim
        for s, be in ((-1, b0 - over), (1, b1 + over)):
            q = [P(a0 - over, be, ye), P(a1 + over, be, ye), P(a1 + over, bm, y + rh), P(a0 - over, bm, y + rh)]
            nrm = tuple(nb(s)[i] * k + (0, 1, 0)[i] for i in range(3))
            M.m(self.rm); M.quad(*q, self.roofc if s < 0 else shade(self.roofc, -8), nrm, [(0, Ls / 3), (La / 3, Ls / 3), (La / 3, 0), (0, 0)])
            M.m('liso')
            M.quad(P(a0 - over, be, ye - t), P(a1 + over, be, ye - t), P(a1 + over, be, ye), P(a0 - over, be, ye), fc, nb(s))                                   # testeira do beiral
            M.quad(P(a0 - over, be, ye - t), P(a1 + over, be, ye - t), P(a1 + over, bm, y + rh - t), P(a0 - over, bm, y + rh - t), shade(fc, -30), tuple(-v for v in nrm))  # forro
            for sa, ae in ((-1, a0 - over), (1, a1 + over)):                                                                                                     # testeira da empena
                M.quad(P(ae, be, ye - t), P(ae, bm, y + rh - t), P(ae, bm, y + rh), P(ae, be, ye), fc, na(sa))
        if walls:
            M.m(wallm or self.wm)
            for sa, ae in ((-1, a0), (1, a1)):
                M.tri(P(ae, b0, y), P(ae, b1, y), P(ae, bm, y + rh), wallc or self.wall, na(sa))

    def hip(self, u0, u1, v0, v1, y, rh, over=0.5):
        M = self.M; F = self.F; t = 0.16
        ins = min(u1 - u0, v1 - v0) / 2; k = rh / ins; ye = y - over * k
        c = [(u0 - over, v0 - over), (u1 + over, v0 - over), (u1 + over, v1 + over), (u0 - over, v1 + over)]
        if (u1 - u0) >= (v1 - v0): t0, t1 = (u0 + ins, (v0 + v1) / 2), (u1 - ins, (v0 + v1) / 2); tops = ((t0, t1), (t1, t1), (t1, t0), (t0, t0))
        else: t0, t1 = ((u0 + u1) / 2, v0 + ins), ((u0 + u1) / 2, v1 - ins); tops = ((t0, t0), (t0, t1), (t1, t1), (t1, t0))
        nrm = [F.nv(-1), F.nu(1), F.nv(1), F.nu(-1)]
        for i in range(4):
            a, b = c[i], c[(i + 1) % 4]; ta, tb = tops[i]
            n = tuple(nrm[i][j] * k + (0, 1, 0)[j] for j in range(3))
            M.m(self.rm); col = self.roofc if i % 2 == 0 else shade(self.roofc, -9)
            L = math.hypot(b[0] - a[0], b[1] - a[1]) / 3; Ls = math.hypot(ins + over, rh + over * k) / 3
            if ta == tb: M.tri(F.p(*a, ye), F.p(*b, ye), F.p(*ta, y + rh), col, n, [(0, Ls), (L, Ls), (L / 2, 0)])
            else: M.quad(F.p(*a, ye), F.p(*b, ye), F.p(*tb, y + rh), F.p(*ta, y + rh), col, n, [(0, Ls), (L, Ls), (L * 0.75, 0), (L * 0.25, 0)])
            M.m('liso'); M.quad(F.p(*a, ye - t), F.p(*b, ye - t), F.p(*b, ye), F.p(*a, ye), self.trim, nrm[i])
        M.m('liso'); M.poly([F.p(*p, ye - t) for p in c], shade(self.trim, -30), (0, -1, 0))

    def shed(self, u0, u1, v0, v1, y_hi, y_lo, hi_at_v1=True):
        """agua unica (varanda): alta junto a casa (v1), baixa na frente (v0)"""
        M = self.M; F = self.F; t = 0.12
        ya, yb_ = (y_lo, y_hi) if hi_at_v1 else (y_hi, y_lo)
        q = [F.p(u0, v0, ya), F.p(u1, v0, ya), F.p(u1, v1, yb_), F.p(u0, v1, yb_)]
        M.m(self.rm); M.quad(*q, shade(self.roofc, 4), (0, 1, 0))
        M.m('liso'); M.quad(F.p(u0, v0, ya - t), F.p(u1, v0, ya - t), F.p(u1, v1, yb_ - t), F.p(u0, v1, yb_ - t), shade(self.trim, -25), (0, -1, 0))
        M.quad(F.p(u0, v0, ya - t), F.p(u1, v0, ya - t), F.p(u1, v0, ya), F.p(u0, v0, ya), self.trim, F.nv(-1))
        for s, uu in ((-1, u0), (1, u1)): M.quad(F.p(uu, v0, ya - t), F.p(uu, v1, yb_ - t), F.p(uu, v1, yb_), F.p(uu, v0, ya), self.trim, F.nu(s))

    def win(self, u, v, y, w=1.2, h=1.45, side=-1, face='v', deep=False, shut=None, flowers=False):
        """janela: vidro texturizado; na fachada (deep) ganha verga e peitoril em volume, venezianas e floreira"""
        B, F = self.B, self.F
        if face == 'v':
            B.panel(F, u - w / 2 - 0.1, u + w / 2 + 0.1, v, y - 0.1, y + h + 0.1, self.trim, 'liso', side, 0.05)
            B.panel(F, u - w / 2, u + w / 2, v, y, y + h, WHITE, 'janela', side, 0.1)
            if deep:
                va, vb = (v - 0.1, v) if side < 0 else (v, v + 0.1)
                self.box(u - w / 2 - 0.16, u + w / 2 + 0.16, va, vb, y + h + 0.06, y + h + 0.18, self.trim, 'liso')
                self.box(u - w / 2 - 0.14, u + w / 2 + 0.14, va - (0.04 if side < 0 else 0), vb + (0.04 if side > 0 else 0), y - 0.14, y - 0.05, self.trim, 'liso')
            if shut:
                for s in (-1, 1):
                    c0 = u + s * (w / 2 + 0.14); B.panel(F, min(c0, c0 + s * 0.42), max(c0, c0 + s * 0.42), v, y - 0.04, y + h + 0.04, shut, 'cerca', side, 0.05)
            if flowers and side < 0:
                self.box(u - w / 2, u + w / 2, v - 0.3, v - 0.04, y - 0.36, y - 0.14, (120, 84, 56), 'madeira')
                fc = self.r.choice(FLOWERS)
                self.M.m('folhagem'); self.M.prism(F.rect(u - w / 2 + 0.03, u + w / 2 - 0.03, v - 0.28, v - 0.06), y - 0.14, y + 0.02, mix(fc, (90, 150, 70), 0.35), True)
        else:
            B.panel_u(F, v - w / 2 - 0.1, v + w / 2 + 0.1, u, y - 0.1, y + h + 0.1, self.trim, 'liso', side, 0.05)
            B.panel_u(F, v - w / 2, v + w / 2, u, y, y + h, WHITE, 'janela', side, 0.1)

    def volume(self, u0, u1, v0, v1, floors, yb=None, corner_boards=True):
        yb = self.yb if yb is None else yb; y1 = yb + floors * self.fh
        self.box(u0 - 0.06, u1 + 0.06, v0 - 0.06, v1 + 0.06, Y0 - 0.05, yb, (176, 172, 164), 'concreto', top=False)
        self.box(u0, u1, v0, v1, yb, y1, self.wall, self.wm, top=False)
        if corner_boards and self.wm == 'siding':
            for (cu, cv) in ((u0, v0), (u1, v0)):
                self.box(cu - 0.07, cu + 0.07, cv - 0.07, cv + 0.07, yb, y1, self.trim, 'liso', top=False)
        self.B.solid(self.F, u0, u1, v0, v1)
        return y1

    def front_wins(self, u0, u1, v, floors, yb=None, skip=(), bay=3.0, w=1.2, h=1.45, flowers=0.0):
        yb = self.yb if yb is None else yb
        n = max(1, int((u1 - u0) / bay))
        for fl in range(floors):
            for k in range(n):
                uc = u0 + (u1 - u0) * (k + 0.5) / n
                if fl == 0 and any(a - 0.3 < uc < b + 0.3 for a, b in skip): continue
                self.win(uc, v, yb + fl * self.fh + 0.9, w, h, -1, 'v', True, self.shut, fl == 0 and self.r.random() < flowers)
                if fl == 0: self.fwin.append(uc)

    def side_back_wins(self, u0, u1, v0, v1, floors, yb=None, skip_side=0):
        yb = self.yb if yb is None else yb
        for fl in range(floors):
            yy = yb + fl * self.fh + 0.9
            for (uu, sd) in ((u0, -1), (u1, 1)):
                if sd == skip_side and fl == 0: continue
                n = max(1, int((v1 - v0) / 4.2))
                for k in range(n): self.win(uu, v0 + (v1 - v0) * (k + 0.5) / n, yy, 1.05, 1.35, sd, 'u')
            n = max(2, int((u1 - u0) / 3.8))
            for k in range(n):
                uc = u0 + (u1 - u0) * (k + 0.5) / n
                if fl == 0 and abs(uc - self.back_door) < 1.3: continue
                self.win(uc, v1, yy, 1.15, 1.35, 1, 'v')

    def door(self, u, v, wide=1.0, sidelights=False, fan=False):
        B, F = self.B, self.F; yb = self.yb
        B.panel(F, u - wide / 2 - 0.13, u + wide / 2 + 0.13, v, yb, yb + 2.24, self.trim, 'liso', -1, 0.05)
        B.panel(F, u - wide / 2, u + wide / 2, v, yb, yb + 2.1, self.doorc, 'porta', -1, 0.1)
        if sidelights:
            for s in (-1, 1): B.panel(F, u + s * (wide / 2 + 0.2) - 0.14, u + s * (wide / 2 + 0.2) + 0.14, v, yb + 0.3, yb + 2.1, WHITE, 'janela', -1, 0.05)
        if fan: B.panel(F, u - wide / 2, u + wide / 2, v, yb + 2.14, yb + 2.5, WHITE, 'janela', -1, 0.05)
        self.box(u + wide / 2 + 0.3, u + wide / 2 + 0.44, v - 0.16, v, yb + 1.75, yb + 2.0, (40, 40, 42), 'liso')     # luminaria
        self.door_u = u

    def steps(self, u, v_top, wide=1.6, y_top=None, n=None):
        """degraus descendo da soleira (v_top) para a frente"""
        y_top = self.yb if y_top is None else y_top
        n = n or max(1, int(round((y_top - Y0) / 0.17)))
        for k in range(n):
            y = y_top - (y_top - Y0) * (k + 1) / (n + 0) + (y_top - Y0) / n * 0.0
            self.box(u - wide / 2, u + wide / 2, v_top - 0.3 * (k + 1), v_top - 0.3 * k, Y0, y_top - (y_top - Y0) * (k + 1) / (n + 1), (208, 204, 196), 'concreto')
        return v_top - 0.3 * n

    def post(self, u, v, y0, y1, th=0.16, col=None, base=None):
        if base:
            self.box(u - 0.26, u + 0.26, v - 0.26, v + 0.26, y0, y0 + 0.8, WHITE, base)
            y0 += 0.8
        self.box(u - th / 2, u + th / 2, v - th / 2, v + th / 2, y0, y1, col or self.trim, 'liso', top=False)

    def rail(self, u0, u1, v, y, gaps=()):
        """guarda-corpo de varanda (paineis de ripas brancas)"""
        segs = []; cur = u0
        for a, b in sorted(gaps):
            if a > cur: segs.append((cur, a))
            cur = max(cur, b)
        if cur < u1: segs.append((cur, u1))
        for a, b in segs:
            if b - a > 0.4:
                self.box(a, b, v - 0.03, v + 0.03, y + 0.1, y + 0.82, (255, 255, 255), 'cerca', top=False)
                self.box(a, b, v - 0.05, v + 0.05, y + 0.82, y + 0.9, self.trim, 'liso')

    def chimney(self, u, v, y_top, wide=0.9, mat='tijolo'):
        self.box(u, u + wide, v, v + wide * 0.8, self.yb, y_top, WHITE if mat == 'tijolo' else self.wall, mat, top=False)
        self.box(u - 0.08, u + wide + 0.08, v - 0.08, v + wide * 0.8 + 0.08, y_top, y_top + 0.14, (190, 186, 178), 'concreto')
        self.box(u + 0.2, u + wide - 0.2, v + 0.18, v + wide * 0.8 - 0.18, y_top + 0.14, y_top + 0.5, (70, 60, 56), 'liso')

    # ------------------------------------------------------------ garagem e acessos
    def garage(self, gu0, gu1, v0, depth=6.6, roof='gable', double=True, yb=None):
        B, F = self.B, self.F; yg = Y0 + 0.06; y1 = yg + 2.85
        self.box(gu0, gu1, v0, v0 + depth, yg, y1, self.wall, self.wm, top=False)
        B.solid(F, gu0, gu1, v0, v0 + depth)
        gw = gu1 - gu0
        if double and gw > 5.6 and self.r.random() < 0.5:                 # duas portas
            for c in (gu0 + gw * 0.27, gu0 + gw * 0.73):
                B.panel(F, c - 1.35, c + 1.35, v0, yg, yg + 2.3, self.trim, 'liso', -1, 0.05)
                B.panel(F, c - 1.25, c + 1.25, v0, yg, yg + 2.2, (246, 244, 240) if self.style != 'moderna' else (70, 72, 76), 'garagem', -1, 0.1)
        else:
            B.panel(F, gu0 + 0.4, gu1 - 0.4, v0, yg, yg + 2.32, self.trim, 'liso', -1, 0.05)
            B.panel(F, gu0 + 0.5, gu1 - 0.5, v0, yg, yg + 2.22, (246, 244, 240) if self.style != 'moderna' else (70, 72, 76), 'garagem', -1, 0.1, [(0, 1), (max(1, round(gw / 3)), 1), (max(1, round(gw / 3)), 0), (0, 0)])
        self.box((gu0 + gu1) / 2 - 0.12, (gu0 + gu1) / 2 + 0.12, v0 - 0.14, v0, yg + 2.45, yg + 2.7, (40, 40, 42), 'liso')
        if roof == 'gable': self.gable(gu0, gu1, v0, v0 + depth, y1, 1.5, False, 0.4)
        elif roof == 'gable_u': self.gable(gu0, gu1, v0, v0 + depth, y1, 1.5, True, 0.4)
        elif roof == 'hip': self.hip(gu0, gu1, v0, v0 + depth, y1, 1.4, 0.45)
        elif roof == 'flat':
            self.box(gu0 - 0.25, gu1 + 0.25, v0 - 0.4, v0 + depth + 0.2, y1, y1 + 0.28, (236, 234, 228), 'concreto', mat_top='cascalho', colt=(200, 198, 192))
        # janela lateral da garagem
        sd = 1 if self.gs > 0 else -1
        self.win(gu1 if sd > 0 else gu0, v0 + depth * 0.5, yg + 1.2, 0.9, 0.9, sd, 'u')
        return y1

    def driveway(self, u0, u1, v_end, mat='concreto', col=WHITE):
        """entrada de carro: rampa na guia (abre em leque), cruza a faixa de grama e a calcada e sobe ate a garagem"""
        M = self.M; F = self.F; M.m(mat)
        yw = 0.185
        M.poly([F.p(u0 - 0.9, -3.74, 0.05), F.p(u1 + 0.9, -3.74, 0.05), F.p(u1 + 0.25, -3.1, yw), F.p(u0 - 0.25, -3.1, yw)], col, (0, 1, 0))
        M.poly([F.p(u0 - 0.25, -3.1, yw), F.p(u1 + 0.25, -3.1, yw), F.p(u1, -1.8, yw), F.p(u0, -1.8, yw)], col, (0, 1, 0))
        M.poly([F.p(u0, -1.8, yw), F.p(u1, -1.8, yw), F.p(u1, 0.0, yw), F.p(u0, 0.0, yw)], col, (0, 1, 0))
        M.poly([F.p(u0, 0.0, yw), F.p(u1, 0.0, yw), F.p(u1, v_end, Y0 + 0.07), F.p(u0, v_end, Y0 + 0.07)], col, (0, 1, 0))
        # juntas de dilatacao
        M.m('liso')
        for vv in (v_end * 0.33, v_end * 0.66):
            y = yw + (Y0 + 0.07 - yw) * vv / max(v_end, 0.1) + 0.03
            M.poly([F.p(u0, vv - 0.03, y), F.p(u1, vv - 0.03, y), F.p(u1, vv + 0.03, y), F.p(u0, vv + 0.03, y)], (170, 168, 162), (0, 1, 0))
        cx, cz = F.xz((u0 + u1) / 2, -2.6)
        self.B.drives.append((cx, cz, (u1 - u0) / 2 + 1.6))
        self.drive = (u0, u1)

    def walkway(self, u, v0, v1, wide=1.2, mat='concreto'):
        M = self.M; F = self.F; M.m(mat)
        M.poly([F.p(u - wide / 2, v0, Y0 + 0.045), F.p(u + wide / 2, v0, Y0 + 0.045), F.p(u + wide / 2, v1, Y0 + 0.045), F.p(u - wide / 2, v1, Y0 + 0.045)], WHITE, (0, 1, 0))

    def walk_L(self, ua, ub, v, wide=1.1, mat='concreto'):
        M = self.M; F = self.F; M.m(mat); a, b = min(ua, ub), max(ua, ub)
        M.poly([F.p(a, v - wide / 2, Y0 + 0.045), F.p(b, v - wide / 2, Y0 + 0.045), F.p(b, v + wide / 2, Y0 + 0.045), F.p(a, v + wide / 2, Y0 + 0.045)], WHITE, (0, 1, 0))

    def mailbox(self, u):
        self.box(u - 0.05, u + 0.05, -2.2, -2.1, 0.15, 1.15, (90, 72, 56), 'madeira')
        self.box(u - 0.14, u + 0.14, -2.45, -1.95, 1.12, 1.38, self.r.choice(((40, 44, 50), (245, 245, 245), (150, 40, 40), (40, 70, 110))), 'liso')

    # ------------------------------------------------------------ estilos
    def build(self):
        r = self.r; w, d, sf = self.w, self.d, self.sf; st = self.style
        ss = 1.7
        gw = 6.2 if w >= 17.0 else (3.7 if w >= 13.6 else 0.0)
        if st == 'craftsman' and r.random() < 0.5 and d > 34: gw = 0.0; self.rear_garage = True
        else: self.rear_garage = False
        hw = min(w - 2 * ss - gw, 14.5 if st != 'ranch' else 17.0)
        floors = FLOORS[st]
        hd = min(d - sf - 8.0, r.uniform(9.5, 11.5) + (2.0 if floors == 1 else 0.0))
        gs = self.gs
        if gw:
            if gs > 0: hu0 = max(ss, w - ss - gw - hw); hu1 = hu0 + hw; gu0, gu1 = hu1, hu1 + gw
            else: gu0 = ss; gu1 = ss + gw; hu0 = gu1; hu1 = hu0 + hw
        else:
            hu0 = (w - hw) / 2 + (1.6 * (-gs) if self.rear_garage or w - hw > 6 else 0); hu0 = max(ss, min(hu0, w - ss - hw)); hu1 = hu0 + hw
            gu0 = gu1 = None
        v0, v1 = sf, sf + hd
        self.fwin = []; self.back_door = hu0 + hw * 0.5
        self.hu0, self.hu1, self.v0, self.v1 = hu0, hu1, v0, v1
        yb, fh = self.yb, self.fh
        getattr(self, 'st_' + st)(hu0, hu1, v0, v1, gu0, gu1)
        # porta dos fundos + degrau
        self.B.panel(self.F, self.back_door - 0.5, self.back_door + 0.5, v1, yb, yb + 2.1, self.trim, 'porta', 1, 0.05)
        # acessos
        if gw: self.driveway(gu0 + 0.35, gu1 - 0.35, self.gv0)
        elif self.rear_garage:                                   # garagem destacada no fundo, entrada longa pela lateral
            du0 = (w - 3.4) if gs > 0 else 0.4
            gv = min(d - 8.2, v1 + 4.0)
            self.driveway(du0, du0 + 3.0, gv)
            gu0_, gu1_ = (w - 5.6, w - 0.5) if gs > 0 else (0.5, 5.6)
            self.garage(gu0_, gu1_, gv, 6.4, 'gable', False)
            self.rear_g = (gu0_, gu1_, gv, gv + 6.4)
        else:
            du0 = (w - 3.4) if gs > 0 else 0.5
            self.driveway(du0, du0 + 2.9, min(v0 + 5.5, d - 3))
        # caminho da porta: da calcada ate a varanda (ou saindo da entrada de carro quando a porta fica ao lado dela)
        du0, du1 = self.drive
        if du0 - 1.2 < self.door_u < du1 + 1.2: pass
        elif abs(self.door_u - (du0 if self.door_u < du0 else du1)) < 4.5 and r.random() < 0.6:
            vv = self.walk_v0 - 0.7; edge = du0 if self.door_u < du0 else du1
            self.walk_L(self.door_u - 0.55 if self.door_u < edge else edge, edge if self.door_u < edge else self.door_u + 0.55, vv)
            self.walkway(self.door_u, vv, self.walk_v0)
        else:
            self.walkway(self.door_u, 0.0, self.walk_v0, 1.2, r.choice(('concreto', 'concreto', 'paver')))
            cx, cz = self.F.xz(self.door_u, -2.6); self.B.drives.append((cx, cz, 1.3))
        self.mailbox(du0 - 0.7 if du0 > 1.6 else du1 + 0.7)
        self.front_garden(); self.fences(); self.backyard()
        return {'plants': self.plants}

    def st_ranch(self, u0, u1, v0, v1, gu0, gu1):
        r = self.r; yb = self.yb; hw = u1 - u0
        y1 = self.volume(u0, u1, v0, v1, 1)
        wing = hw > 11 and r.random() < 0.6                       # ala com empena para a rua (planta em L)
        hipr = r.random() < 0.45
        du = u0 + hw * (0.62 if self.gs > 0 else 0.38)
        if wing:
            wu0, wu1 = (u0, u0 + hw * 0.42) if self.gs > 0 else (u1 - hw * 0.42, u1)
            self.volume(wu0, wu1, v0 - 2.4, v0 + 0.5, 1)
            self.gable(wu0, wu1, v0 - 2.4, (v0 + v1) / 2, y1, 1.7, False, 0.45)
            self.front_wins(wu0 + 0.4, wu1 - 0.4, v0 - 2.4, 1, bay=4.0, w=2.0, h=1.5, flowers=0.3)
            rest = (wu1, u1) if self.gs > 0 else (u0, wu0)
            du = (rest[0] + rest[1]) / 2 + (0.8 if self.gs > 0 else -0.8)
            self.front_wins(rest[0] + 0.3, rest[1] - 0.3, v0, 1, skip=[(du - 1.3, du + 1.3)], flowers=0.3)
            # varandinha coberta no recuo
            self.box(rest[0], rest[1], v0 - 1.8, v0, Y0, yb, (206, 202, 194), 'concreto')
            self.shed(rest[0] - 0.1, rest[1] + 0.3, v0 - 2.1, v0, y1 + 0.05, y1 - 0.45)
            self.post(rest[1] - 0.15 if self.gs > 0 else rest[0] + 0.15, v0 - 1.7, yb, y1 - 0.5)
            self.walk_v0 = self.steps(du, v0 - 1.8, 1.5)
        else:
            self.front_wins(u0 + 0.4, u1 - 0.4, v0, 1, skip=[(du - 1.3, du + 1.3)], flowers=0.3, w=1.5)
            self.box(du - 1.3, du + 1.3, v0 - 1.3, v0, Y0, yb, (206, 202, 194), 'concreto')
            self.gable(du - 1.5, du + 1.5, v0 - 1.5, v0 + 0.6, yb + 2.45, 0.7, False, 0.2, walls=True, wallc=self.trim, wallm='liso')
            for s in (-1, 1): self.post(du + s * 1.25, v0 - 1.2, yb, yb + 2.45, 0.12)
            self.walk_v0 = self.steps(du, v0 - 1.3, 1.5)
        self.door(du, v0, 1.0)
        if hipr: self.hip(u0, u1, v0, v1, y1, 1.9, 0.55)
        else: self.gable(u0, u1, v0, v1, y1, 2.0, True, 0.5)
        self.side_back_wins(u0, u1, v0, v1, 1, skip_side=(1 if self.gs > 0 else -1) if gu0 is not None else 0)
        if r.random() < 0.6: self.chimney(u0 + hw * r.choice((0.2, 0.75)), v0 + (v1 - v0) * 0.55, y1 + 2.7)
        if gu0 is not None: self.gv0 = v0 + 0.8; self.garage(gu0, gu1, self.gv0, 6.6, 'hip' if hipr else 'gable_u')

    def st_colonial(self, u0, u1, v0, v1, gu0, gu1):
        r = self.r; yb = self.yb; hw = u1 - u0; du = (u0 + u1) / 2
        y1 = self.volume(u0, u1, v0, v1, 2)
        self.front_wins(u0 + 0.3, du - 1.2, v0, 2, bay=2.8, flowers=0.15)
        self.front_wins(du + 1.2, u1 - 0.3, v0, 2, bay=2.8, flowers=0.15)
        self.win(du, v0, yb + self.fh + 0.9, 1.2, 1.45, -1, 'v', True, self.shut)
        self.door(du, v0, 1.05, sidelights=True, fan=True)
        self.gable(u0, u1, v0, v1, y1, 2.7, True, 0.4)
        # portico com colunas e frontao
        self.box(du - 1.9, du + 1.9, v0 - 2.0, v0, Y0, yb, (212, 208, 200), 'concreto')
        for s in (-1, 1):
            cx, cz = self.F.xz(du + s * 1.55, v0 - 1.7); self.M.m('liso'); self.M.cyl(cx, cz, 0.14, yb, yb + 2.75, self.trim, 8, False)
        self.box(du - 1.95, du + 1.95, v0 - 2.05, v0, yb + 2.75, yb + 3.0, self.trim, 'liso')
        self.gable(du - 1.8, du + 1.8, v0 - 1.9, v0 + 0.5, yb + 3.0, 0.85, False, 0.2, walls=True, wallc=self.trim, wallm='liso')
        self.walk_v0 = self.steps(du, v0 - 2.0, 2.2)
        self.side_back_wins(u0, u1, v0, v1, 2, skip_side=(1 if self.gs > 0 else -1) if gu0 is not None else 0)
        self.chimney(u0 - 0.0 if self.gs > 0 else u1 - 0.9, v0 + (v1 - v0) * 0.45, y1 + 3.4)
        if gu0 is not None: self.gv0 = v0 + 1.5; self.garage(gu0, gu1, self.gv0, 6.6, 'gable_u')

    def st_craftsman(self, u0, u1, v0, v1, gu0, gu1):
        r = self.r; yb = self.yb; hw = u1 - u0; du = u0 + hw * (0.3 if self.gs > 0 else 0.7)
        y1 = self.volume(u0, u1, v0, v1, 1)
        self.front_wins(u0 + 0.4, u1 - 0.4, v0, 1, skip=[(du - 1.2, du + 1.2)], bay=3.4, w=1.7, h=1.5)
        self.door(du, v0, 1.0)
        self.gable(u0, u1, v0, v1, y1, 3.0, False, 0.6)
        self.win((u0 + u1) / 2, v0, y1 + 0.9, 1.4, 0.9, -1, 'v', True)                       # janela do sotao na empena
        # varanda larga: pilares com base de pedra, guarda-corpo, telhado proprio
        pd = 2.6; pu0, pu1 = u0, u1
        self.box(pu0, pu1, v0 - pd, v0, Y0, yb, (198, 194, 186), 'concreto', mat_top='madeira', colt=(230, 220, 205))
        n = 4 if hw > 11 else 3
        for k in range(n): self.post(pu0 + 0.3 + (pu1 - pu0 - 0.6) * k / (n - 1), v0 - pd + 0.3, yb, yb + 2.55, 0.2, None, 'pedra')
        self.gable(pu0, pu1, v0 - pd, v0 + 1.2, yb + 2.55, 1.25, False, 0.4, walls=True)
        self.rail(pu0 + 0.5, pu1 - 0.5, v0 - pd + 0.3, yb, gaps=[(du - 0.9, du + 0.9)])
        self.walk_v0 = self.steps(du, v0 - pd, 1.8)
        self.side_back_wins(u0, u1, v0, v1, 1, skip_side=(1 if self.gs > 0 else -1) if gu0 is not None else 0)
        self.chimney(u1 - 0.9 if self.gs < 0 else u0, v0 + (v1 - v0) * 0.6, y1 + 3.2, mat='pedra' if r.random() < 0.5 else 'tijolo')
        if gu0 is not None: self.gv0 = v0 + 1.2; self.garage(gu0, gu1, self.gv0, 6.6, 'gable')

    def st_cape(self, u0, u1, v0, v1, gu0, gu1):
        r = self.r; yb = self.yb; hw = u1 - u0; du = (u0 + u1) / 2
        y1 = self.volume(u0, u1, v0, v1, 1)
        self.front_wins(u0 + 0.3, du - 1.1, v0, 1, bay=3.0, flowers=0.5)
        self.front_wins(du + 1.1, u1 - 0.3, v0, 1, bay=3.0, flowers=0.5)
        self.door(du, v0, 1.0, fan=True)
        rh = 4.0; self.gable(u0, u1, v0, v1, y1, rh, True, 0.35)
        hd = v1 - v0; k = rh / (hd / 2)
        for uc in ((u0 + hw * 0.25, u0 + hw * 0.75) if hw > 9.5 else ((u0 + u1) / 2,)):      # aguas-furtadas
            vd = v0 + 1.3; yd = y1 + (vd - v0) * k
            self.box(uc - 0.85, uc + 0.85, vd, vd + 2.0, yd - 0.4, yd + 1.25, self.wall, self.wm, top=False)
            self.win(uc, vd, yd + 0.1, 1.0, 1.0, -1, 'v', True)
            self.gable(uc - 0.85, uc + 0.85, vd, vd + 2.4, yd + 1.25, 0.7, False, 0.18)
        self.box(du - 1.2, du + 1.2, v0 - 1.2, v0, Y0, yb, (206, 202, 194), 'concreto')
        self.gable(du - 1.3, du + 1.3, v0 - 1.3, v0 + 0.5, yb + 2.5, 0.75, False, 0.15, walls=True, wallc=self.trim, wallm='liso')
        for s in (-1, 1): self.post(du + s * 1.1, v0 - 1.1, yb, yb + 2.5, 0.12)
        self.walk_v0 = self.steps(du, v0 - 1.2, 1.5)
        self.side_back_wins(u0, u1, v0, v1, 1, skip_side=(1 if self.gs > 0 else -1) if gu0 is not None else 0)
        for (uu, sd) in ((u0, -1), (u1, 1)): self.win(uu, (v0 + v1) / 2, y1 + 0.9, 1.0, 1.2, sd, 'u')
        self.chimney((u0 + u1) / 2 + 1.5, v0 + hd * 0.5 - 0.3, y1 + rh + 0.9)
        if gu0 is not None: self.gv0 = v0 + 1.0; self.garage(gu0, gu1, self.gv0, 6.6, 'gable_u')

    def st_moderna(self, u0, u1, v0, v1, gu0, gu1):
        r = self.r; yb = self.yb; hw = u1 - u0; fh = self.fh
        split = u0 + hw * (0.45 if self.gs > 0 else 0.55)
        a = (u0, split) if self.gs > 0 else (split, u1)          # volume alto (2 andares)
        b = (split, u1) if self.gs > 0 else (u0, split)          # volume baixo recuado
        yA = self.volume(a[0], a[1], v0 - 1.2, v1, 2, corner_boards=False)
        yB = self.volume(b[0], b[1], v0, v1 - 1.0, 1, corner_boards=False)
        for (uu0, uu1, vv0, vv1, yy) in ((a[0], a[1], v0 - 1.2, v1, yA), (b[0], b[1], v0, v1 - 1.0, yB)):
            self.box(uu0 - 0.35, uu1 + 0.35, vv0 - 0.6, vv1 + 0.3, yy, yy + 0.28, (238, 236, 230), 'concreto', mat_top='cascalho', colt=(200, 198, 192))
        self.B.panel(self.F, a[0] + 0.5, a[1] - 0.5, v0 - 1.2, yb + 0.3, yb + 2.5, WHITE, 'janela', -1, 0.05, [(0, 1), (2, 1), (2, 0), (0, 0)])
        self.B.panel(self.F, a[0] + 0.5, a[1] - 0.5, v0 - 1.2, yb + fh + 0.4, yb + fh + 2.4, WHITE, 'janela', -1, 0.05, [(0, 1), (2, 1), (2, 0), (0, 0)])
        self.box(a[0] + 0.2, a[0] + 1.4, v0 - 1.3, v0 - 1.2, yb, yA, WHITE, 'madeira', top=False)               # painel de madeira
        du = b[0] + 1.3 if self.gs > 0 else b[1] - 1.3
        self.door(du, v0, 1.1)
        self.front_wins(b[0] + (2.4 if self.gs > 0 else 0.3), b[1] - (0.3 if self.gs > 0 else 2.4), v0, 1, bay=3.5, w=2.2, h=1.6)
        self.box(du - 1.5, du + 1.5, v0 - 1.4, v0, Y0, yb, (214, 212, 206), 'concreto')
        self.box(du - 1.7, du + 1.7, v0 - 1.6, v0, yb + 2.5, yb + 2.66, (238, 236, 230), 'concreto')
        self.post(du + (1.5 if self.gs > 0 else -1.5), v0 - 1.4, yb, yb + 2.5, 0.12, (60, 62, 66))
        self.walk_v0 = self.steps(du, v0 - 1.4, 2.0)
        self.side_back_wins(u0, u1, v0, v1 - 1.0, 1, skip_side=(1 if self.gs > 0 else -1) if gu0 is not None else 0)
        self.B.panel(self.F, a[0] + 0.6, a[1] - 0.6, v1, yb + fh + 0.5, yb + fh + 2.2, WHITE, 'janela', 1, 0.05, [(0, 1), (2, 1), (2, 0), (0, 0)])
        if gu0 is not None: self.gv0 = v0 + 0.6; self.garage(gu0, gu1, self.gv0, 6.6, 'flat')

    def st_farmhouse(self, u0, u1, v0, v1, gu0, gu1):
        r = self.r; yb = self.yb; hw = u1 - u0
        y1 = self.volume(u0, u1, v0, v1, 2)
        wu0, wu1 = (u0, u0 + hw * 0.45) if self.gs > 0 else (u1 - hw * 0.45, u1)       # ala frontal de 2 andares com empena
        self.volume(wu0, wu1, v0 - 1.8, v0 + 0.5, 2)
        self.gable(u0, u1, v0, v1, y1, 2.6, True, 0.45)
        self.gable(wu0, wu1, v0 - 1.8, (v0 + v1) / 2, y1, 2.3, False, 0.45)
        self.front_wins(wu0 + 0.3, wu1 - 0.3, v0 - 1.8, 2, bay=3.0, w=1.1, h=1.7)
        self.win((wu0 + wu1) / 2, v0 - 1.8, y1 + 0.5, 0.8, 0.8, -1, 'v', True)
        rest = (wu1, u1) if self.gs > 0 else (u0, wu0)
        du = (rest[0] + rest[1]) / 2
        self.front_wins(rest[0] + 0.3, rest[1] - 0.3, v0, 2, skip=[(du - 1.2, du + 1.2)], bay=3.0, w=1.1, h=1.7)
        self.door(du, v0, 1.05, sidelights=True)
        # varanda coberta no recuo, com guarda-corpo
        pv = v0 - 2.4
        self.box(rest[0], rest[1], pv, v0, Y0, yb, (198, 194, 186), 'concreto', mat_top='madeira', colt=(226, 218, 204))
        self.shed(rest[0] - 0.2, rest[1] + 0.3, pv - 0.3, v0, yb + 2.9, yb + 2.45)
        e = rest[1] - 0.2 if self.gs > 0 else rest[0] + 0.2
        self.post(e, pv + 0.2, yb, yb + 2.45); self.post((rest[0] + rest[1]) / 2 + (1.3 if self.gs > 0 else -1.3), pv + 0.2, yb, yb + 2.45)
        self.rail(rest[0] + 0.2, rest[1] - 0.2, pv + 0.2, yb, gaps=[(du - 0.9, du + 0.9)])
        self.walk_v0 = self.steps(du, pv, 1.8)
        self.side_back_wins(u0, u1, v0, v1, 2, skip_side=(1 if self.gs > 0 else -1) if gu0 is not None else 0)
        self.chimney(u1 - 0.9 if self.gs < 0 else u0, v0 + (v1 - v0) * 0.6, y1 + 3.0)
        if gu0 is not None: self.gv0 = v0 + 1.4; self.garage(gu0, gu1, self.gv0, 6.6, 'gable')

    def st_mediterranea(self, u0, u1, v0, v1, gu0, gu1):
        r = self.r; yb = self.yb; hw = u1 - u0
        y1 = self.volume(u0, u1, v0, v1, 1, corner_boards=False)
        tu0, tu1 = (u0 + hw * 0.55, u1) if self.gs < 0 else (u0, u0 + hw * 0.45)        # torreao de 2 andares
        yT = self.volume(tu0, tu1, v0 - 1.2, v0 + 5.0, 2, corner_boards=False)
        self.hip(u0, u1, v0, v1, y1, 1.5, 0.55)
        self.hip(tu0, tu1, v0 - 1.2, v0 + 5.0, yT, 1.3, 0.5)
        self.front_wins(tu0 + 0.3, tu1 - 0.3, v0 - 1.2, 2, bay=3.4, w=1.3, h=1.6)
        rest = (tu1, u1) if self.gs >= 0 else (u0, tu0)
        du = rest[0] + 1.6 if self.gs >= 0 else rest[1] - 1.6
        self.front_wins(rest[0] + (3.0 if self.gs >= 0 else 0.3), rest[1] - (0.3 if self.gs >= 0 else 3.0), v0, 1, bay=3.2, w=1.3, h=1.5, flowers=0.4)
        self.door(du, v0, 1.1, fan=True)
        # entrada em arco (portal de alvenaria) e patio de lajota
        self.box(du - 1.5, du - 1.1, v0 - 1.5, v0, yb, yb + 2.7, self.wall, 'reboco', top=False); self.box(du + 1.1, du + 1.5, v0 - 1.5, v0, yb, yb + 2.7, self.wall, 'reboco', top=False)
        self.box(du - 1.5, du + 1.5, v0 - 1.5, v0, yb + 2.5, yb + 3.1, self.wall, 'reboco', mat_top='ceramica', colt=(255, 255, 255))
        self.box(du - 1.6, du + 1.6, v0 - 1.6, v0, Y0, yb, WHITE, 'paver')
        self.walk_v0 = self.steps(du, v0 - 1.6, 2.0)
        self.side_back_wins(u0, u1, v0, v1, 1, skip_side=(1 if self.gs > 0 else -1) if gu0 is not None else 0)
        if gu0 is not None: self.gv0 = v0 + 0.8; self.garage(gu0, gu1, self.gv0, 6.6, 'hip')

    # ------------------------------------------------------------ jardins, cercas, quintal
    def blocked_front(self, u, pad=1.0):
        du0, du1 = self.drive
        return (du0 - pad < u < du1 + pad) or abs(u - self.door_u) < pad + 0.6

    def front_garden(self):
        r = self.r; w = self.w; v0 = self.v0
        # arbustos de fundacao sob as janelas (nunca na porta nem na garagem)
        u = self.hu0 + 0.8
        while u < self.hu1 - 0.6:
            if not self.blocked_front(u, 0.9) and r.random() < 0.8:
                self.plants.append((u, v0 - 0.75 - (2.4 if self.style in ('craftsman',) else 0), r.choice(('arbusto', 'arbusto', 'flores', 'buxo')), r.uniform(0.7, 1.0)))
            u += r.uniform(1.5, 2.3)
        # canteiro de flores ao longo do caminho da porta
        if r.random() < 0.4 and not (self.drive[0] - 1.2 < self.door_u < self.drive[1] + 1.2):
            for vv in (1.2, 2.6, 4.0):
                if vv < self.walk_v0 - 0.5:
                    for s in (-1, 1): self.plants.append((self.door_u + s * 1.05, vv, 'flores', 0.6))
        # uma arvore ornamental no meio do maior trecho de gramado da frente (longe da porta, da garagem e das janelas)
        spans = []; cuts = sorted([(self.drive[0] - 1.5, self.drive[1] + 1.5), (self.door_u - 1.6, self.door_u + 1.6)])
        cur = 1.5
        for a, b in cuts:
            if a > cur: spans.append((cur, a))
            cur = max(cur, b)
        if cur < w - 1.5: spans.append((cur, w - 1.5))
        spans = [s for s in spans if s[1] - s[0] >= 4.5]
        if spans and self.sf >= 6.0 and r.random() < 0.8:
            a, b = max(spans, key=lambda s: s[1] - s[0])
            self.plants.append(((a + b) / 2 + r.uniform(-0.6, 0.6), min(3.0, self.sf * 0.45), r.choice(('ornamental', 'florida', 'oval', 'ornamental')), r.uniform(0.75, 0.95)))

    def fences(self):
        if not self.fence: return
        r = self.r; w, d = self.w, self.d
        fc, fm = FENCES[r.randrange(len(FENCES))]
        vf = self.v0 + (self.v1 - self.v0) * 0.55
        if self.rear_garage: vf = self.v1 + 0.2
        h = 1.8
        self.box(w - 0.1, w, vf, d - 0.08, Y0, Y0 + h, fc, fm, top=True)
        if self.first: self.box(0, 0.1, vf, d - 0.08, Y0, Y0 + h, fc, fm)
        self.box(0, w, d - 0.18, d - 0.08, Y0, Y0 + h, fc, fm)
        # fechamento entre a casa e a divisa (com portao) dos dois lados
        hu0 = self.hu0 if self.gs > 0 or self.drive[0] > self.hu0 else self.drive[1]
        if self.hu0 > 0.6: self.box(0.1, self.hu0, vf - 0.05, vf + 0.05, Y0, Y0 + h, fc, fm)
        right0 = max(self.hu1, self.drive[1] if self.drive[0] >= self.hu1 - 0.5 else self.hu1)
        if not self.rear_garage or self.gs < 0:
            if w - 0.1 - right0 > 0.5: self.box(right0, w - 0.1, vf - 0.05, vf + 0.05, Y0, Y0 + h, fc, fm)
        if self.picket:
            du0, du1 = self.drive
            cuts = sorted([(du0 - 0.3, du1 + 0.3), (self.door_u - 0.8, self.door_u + 0.8)]); cur = 0.3
            for a, b in cuts + [(w - 0.3, w)]:
                if a - cur > 0.8:
                    self.box(cur, a, 0.24, 0.3, Y0, Y0 + 0.92, (255, 255, 255), 'cerca', top=False)
                    self.box(cur, a, 0.22, 0.32, Y0 + 0.92, Y0 + 0.99, TRIM, 'liso')
                cur = max(cur, b)

    def backyard(self):
        r = self.r; M = self.M; F = self.F; w, d = self.w, self.d; v1 = self.v1
        depth = d - v1
        if depth < 5: return
        taken = []
        if self.rear_garage: taken.append(self.rear_g)
        def free(u0, u1, a, b):
            if u0 < 0.8 or u1 > w - 0.8 or a < v1 + 0.3 or b > d - 0.8: return False
            return all(u1 < t[0] - 0.4 or u0 > t[1] + 0.4 or b < t[2] - 0.4 or a > t[3] + 0.4 for t in taken)
        bd = self.back_door
        # patio / deck junto a porta dos fundos
        pw, pdp = min(6.0, self.hu1 - self.hu0 - 1.0), min(4.2, depth - 2.0)
        pu0 = max(self.hu0 + 0.3, min(bd - pw / 2, self.hu1 - pw - 0.3))
        deck = r.random() < 0.45
        if deck:
            self.box(pu0, pu0 + pw, v1, v1 + pdp, Y0, self.yb - 0.04, (250, 240, 225), 'madeira')
            self.rail(pu0, pu0 + pw - 1.4, v1 + pdp - 0.05, self.yb - 0.1)
            self.box(pu0 + pw - 1.3, pu0 + pw, v1 + pdp, v1 + pdp + 0.3, Y0, Y0 + 0.2, (250, 240, 225), 'madeira')
            yt = self.yb - 0.04
        else:
            M.m('paver'); M.poly([F.p(pu0, v1, Y0 + 0.05), F.p(pu0 + pw, v1, Y0 + 0.05), F.p(pu0 + pw, v1 + pdp, Y0 + 0.05), F.p(pu0, v1 + pdp, Y0 + 0.05)], WHITE, (0, 1, 0))
            self.box(bd - 0.7, bd + 0.7, v1, v1 + 0.5, Y0, self.yb - 0.02, (206, 202, 194), 'concreto')
            yt = Y0 + 0.05
        taken.append((pu0, pu0 + pw, v1, v1 + pdp))
        # mesa com guarda-sol e cadeiras; churrasqueira
        if pw > 3.5 and pdp > 3.0:
            tx, tv = pu0 + pw * 0.62, v1 + pdp * 0.55; cx, cz = F.xz(tx, tv)
            M.m('liso'); M.cyl(cx, cz, 0.55, yt + 0.68, yt + 0.74, (236, 236, 232), 8); M.cyl(cx, cz, 0.05, yt, yt + 0.68, (120, 120, 124), 4, False)
            if r.random() < 0.7:
                M.cyl(cx, cz, 0.03, yt + 0.74, yt + 2.3, (200, 200, 204), 4, False); M.cyl(cx, cz, 1.35, yt + 2.05, yt + 2.5, r.choice(FLOWERS + [(240, 236, 224), (40, 90, 80)]), 8, False, 0.04)
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2; ux, uv = tx + math.cos(a) * 0.95, tv + math.sin(a) * 0.95
                self.box(ux - 0.22, ux + 0.22, uv - 0.22, uv + 0.22, yt, yt + 0.45, (250, 250, 248), 'liso')
            gx = pu0 + 0.5
            self.box(gx - 0.3, gx + 0.3, v1 + pdp - 0.9, v1 + pdp - 0.4, yt, yt + 0.9, (36, 36, 38), 'liso')
        # itens do quintal, do maior para o menor, sem sobrepor
        opts = []
        if depth > 11 and w > 14 and r.random() < 0.38: opts.append('piscina')
        if r.random() < 0.38: opts.append('deposito')
        if r.random() < 0.30: opts.append('balanco')
        if r.random() < 0.16: opts.append('cama')
        if r.random() < 0.30: opts.append('horta')
        for it in opts:
            for _ in range(8):
                if it == 'piscina':
                    pl, pwd = r.uniform(6.5, 8.5), r.uniform(3.6, 4.4)
                    a = r.uniform(1.6, max(1.7, w - pl - 1.6)); b = r.uniform(v1 + pdp + 1.5, max(v1 + pdp + 1.6, d - pwd - 2.0))
                    if not free(a - 0.9, a + pl + 0.9, b - 0.9, b + pwd + 0.9): continue
                    self.box(a - 0.8, a + pl + 0.8, b - 0.8, b + pwd + 0.8, Y0, Y0 + 0.1, (238, 232, 220), 'concreto')
                    M.m('agua'); M.poly([F.p(a, b, Y0 + 0.16), F.p(a + pl, b, Y0 + 0.16), F.p(a + pl, b + pwd, Y0 + 0.16), F.p(a, b + pwd, Y0 + 0.16)], (150, 235, 245), (0, 1, 0))
                    for k in range(2):
                        self.box(a + 1.0 + k * 1.3, a + 1.7 + k * 1.3, b - 0.75, b - 0.1 + 1.2 * 0, Y0 + 0.1, Y0 + 0.38, r.choice(((250, 250, 250), (60, 150, 200), (240, 200, 60))), 'liso')
                    taken.append((a - 0.9, a + pl + 0.9, b - 0.9, b + pwd + 0.9)); break
                if it == 'deposito':
                    a = r.choice((1.0, w - 4.2)); b = d - 4.0
                    if not free(a, a + 3.2, b, b + 2.8): continue
                    wc = r.choice(((176, 88, 62), self.wall, (250, 246, 236), (120, 140, 120)))
                    self.box(a, a + 3.2, b, b + 2.8, Y0, Y0 + 2.2, wc, 'siding', top=False)
                    self.gable(a, a + 3.2, b, b + 2.8, Y0 + 2.2, 0.9, True, 0.2, True, wc, 'siding')
                    self.B.panel(F, a + 0.9, a + 2.3, b, Y0, Y0 + 1.9, (240, 238, 232), 'porta', -1, 0.04)
                    self.B.solid(F, a, a + 3.2, b, b + 2.8); taken.append((a, a + 3.2, b, b + 2.8)); break
                if it == 'balanco':
                    a = r.uniform(1.5, max(1.6, w - 5.5)); b = r.uniform(v1 + pdp + 1.0, max(v1 + pdp + 1.1, d - 4.5))
                    if not free(a, a + 4.0, b, b + 3.0): continue
                    wd = (150, 104, 66)
                    for uu in (a + 0.2, a + 2.6): self.box(uu - 0.07, uu + 0.07, b + 1.0, b + 1.14, Y0, Y0 + 2.2, wd, 'madeira', top=False)
                    self.box(a + 0.1, a + 2.7, b + 1.0, b + 1.14, Y0 + 2.2, Y0 + 2.34, wd, 'madeira')
                    for uu in (a + 0.9, a + 1.9):
                        self.box(uu - 0.22, uu + 0.22, b + 0.98, b + 1.16, Y0 + 0.5, Y0 + 0.55, r.choice(FLOWERS), 'liso')
                        for s in (-1, 1): self.box(uu + s * 0.2 - 0.012, uu + s * 0.2 + 0.012, b + 1.06, b + 1.08, Y0 + 0.55, Y0 + 2.2, (90, 90, 94), 'liso', top=False)
                    self.box(a + 2.8, a + 3.8, b + 0.6, b + 1.5, Y0 + 1.3, Y0 + 1.4, wd, 'madeira')                                  # plataforma + escorregador
                    for (uu, vv) in ((a + 2.85, b + 0.65), (a + 3.75, b + 0.65), (a + 2.85, b + 1.45), (a + 3.75, b + 1.45)): self.box(uu - 0.05, uu + 0.05, vv - 0.05, vv + 0.05, Y0, Y0 + 1.3, wd, 'madeira', top=False)
                    M.m('liso'); M.quad(F.p(a + 3.0, b + 1.5, Y0 + 1.38), F.p(a + 3.6, b + 1.5, Y0 + 1.38), F.p(a + 3.6, b + 3.0, Y0 + 0.15), F.p(a + 3.0, b + 3.0, Y0 + 0.15), r.choice(((240, 196, 40), (220, 60, 50), (50, 140, 220))), (0, 1, 0.6))
                    taken.append((a, a + 4.0, b, b + 3.0)); break
                if it == 'cama':
                    a = r.uniform(2.5, max(2.6, w - 2.5)); b = r.uniform(v1 + pdp + 2.5, max(v1 + pdp + 2.6, d - 3.0))
                    if not free(a - 1.9, a + 1.9, b - 1.9, b + 1.9): continue
                    cx, cz = F.xz(a, b); M.m('liso')
                    M.cyl(cx, cz, 1.7, Y0 + 0.7, Y0 + 0.78, (30, 30, 34), 10, True, None, (46, 46, 52)); M.cyl(cx, cz, 1.75, Y0 + 0.62, Y0 + 0.72, (40, 100, 190), 10, False)
                    for k in range(4):
                        an = k * math.pi / 2 + 0.4; px, pz = cx + math.cos(an) * 1.6, cz + math.sin(an) * 1.6
                        M.cyl(px, pz, 0.04, Y0, Y0 + 0.7, (120, 120, 124), 4, False)
                    taken.append((a - 1.9, a + 1.9, b - 1.9, b + 1.9)); break
                if it == 'horta':
                    a = r.uniform(1.2, max(1.3, w - 5.0)); b = r.uniform(v1 + pdp + 1.0, max(v1 + pdp + 1.1, d - 3.6))
                    if not free(a, a + 3.8, b, b + 2.8): continue
                    for k in range(2):
                        self.box(a + k * 2.0, a + k * 2.0 + 1.5, b, b + 2.8, Y0, Y0 + 0.28, (150, 108, 70), 'madeira', mat_top='terreno', colt=(110, 84, 60))
                        for j in range(4): self.plants.append((a + k * 2.0 + 0.75, b + 0.4 + j * 0.65, 'muda', 0.5))
                    taken.append((a, a + 3.8, b, b + 2.8)); break
        # arvores de quintal nos cantos do fundo (sombra, longe da casa) e cerca viva em parte da divisa
        for (a, b) in ((w * 0.2, d - 3.2), (w * 0.8, d - 3.2), (w * 0.5, d - 2.8)):
            if r.random() < 0.6 and b > v1 + pdp + 2.5 and free(a - 2.0, a + 2.0, b - 2.0, b + 2.0):
                self.plants.append((a, b, r.choice(('folhosa', 'folhosa', 'oval', 'conifera', 'florida', 'frutifera')), r.uniform(0.9, 1.25)))
                taken.append((a - 2.0, a + 2.0, b - 2.0, b + 2.0))
        if self.fence and r.random() < 0.35:
            u = 1.2
            while u < w - 1.2:
                if free(u - 0.6, u + 0.6, d - 1.6, d - 0.9): self.plants.append((u, d - 1.1, 'buxo', 1.0))
                u += 1.3
