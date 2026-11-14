"""Cidade 6 - construcoes: casas de suburbio americano (5 estilos), predios do centro (fachadas texturizadas por andar),
torres de vidro, construcoes civicas e comerciais. Tudo no referencial do lote (Frame: u ao longo da rua, v para dentro)."""
import math, random
import numpy as np
from mesh import rgb, shade, mix, WHITE, Frame

Y0 = 0.13          # gramado do lote

SIDING = [rgb(c) for c in ('#F4F1E8', '#E8E2D0', '#DCE6EA', '#C9D8DE', '#E9DCC4', '#D6DDC8', '#F1E6D2', '#BFD0D8', '#E6D3C3', '#D9D2E2', '#B8C7B0', '#F3E9C9', '#A9C3D6', '#E7C9A9', '#C8D9B8', '#F2D7CF')]
BRICK_T = [rgb(c) for c in ('#FFFFFF', '#F0E6E0', '#E8D8CC')]
STUCCO = [rgb(c) for c in ('#F2EBDD', '#EDE3D1', '#E9E0D6', '#F5F0E6', '#E4D7C3', '#D8CDBE')]
ROOF = [rgb(c) for c in ('#A3A6AC', '#8E9197', '#B0907A', '#7F8C9C', '#A88B78', '#8F7462', '#9AA493', '#B5A492', '#7A6F69', '#B88A73')]
TRIM = (246, 244, 238)
DOORC = [rgb(c) for c in ('#7A2E2E', '#2F4A66', '#2E5B3E', '#3B3B3B', '#8A5A2E', '#F2F0EA', '#1F2F4A')]
SHUT = [rgb(c) for c in ('#2E3E2E', '#2F3E56', '#3A3A3A', '#5A2A2A', '#F4F2EC')]
FENCE_W = [rgb(c) for c in ('#FFFFFF', '#F4E9DA', '#E9DDCB', '#FFF8EE', '#D9CBB6')]


class Builder:
    def __init__(self, M, rnd):
        self.M = M; self.rnd = rnd
        self.colliders = []          # retangulos girados: (cx, cz, ux, uz, hu, hv)
        self.drives = []             # pontos das entradas de carro na faixa de grama (sem arvore/carro ali)

    # ------------------------------------------------------------ primitivas no referencial
    def box(self, F, u0, u1, v0, v1, y0, y1, col, mat, top=True, mat_top=None, colt=None, wall_uv=None):
        self.M.m(mat); self.M.prism(F.rect(u0, u1, v0, v1), y0, y1, col, top, False, colt, None, mat_top, wall_uv)

    def panel(self, F, u0, u1, v, y0, y1, col, mat, side=-1, off=0.04, uv=None):
        """painel vertical numa face de v fixo (side=-1: olha para a rua)"""
        M = self.M; old = M.m(mat); vv = v + side * off
        uv = uv or [(0, 1), (1, 1), (1, 0), (0, 0)]
        a, b, c, d = F.p(u0, vv, y0), F.p(u1, vv, y0), F.p(u1, vv, y1), F.p(u0, vv, y1)
        if side > 0: a, b, c, d = b, a, d, c; uv = [uv[1], uv[0], uv[3], uv[2]]
        M.quad(a, b, c, d, col, F.nv(side), uv); M.m(old)

    def panel_u(self, F, v0, v1, u, y0, y1, col, mat, side=-1, off=0.04, uv=None):
        """painel numa face de u fixo (side=-1: olha para -u)"""
        M = self.M; old = M.m(mat); uu = u + side * off
        uv = uv or [(0, 1), (1, 1), (1, 0), (0, 0)]
        a, b, c, d = F.p(uu, v1, y0), F.p(uu, v0, y0), F.p(uu, v0, y1), F.p(uu, v1, y1)
        if side > 0: a, b, c, d = b, a, d, c; uv = [uv[1], uv[0], uv[3], uv[2]]
        M.quad(a, b, c, d, col, F.nu(side), uv); M.m(old)

    def solid(self, F, u0, u1, v0, v1):
        cx, cz = F.xz((u0 + u1) / 2, (v0 + v1) / 2)
        self.colliders.append([round(cx, 2), round(cz, 2), round(F.ux, 4), round(F.uz, 4), round((u1 - u0) / 2, 2), round((v1 - v0) / 2, 2)])

    def window(self, F, u, v, y, w, h, side=-1, shutters=None, face='v', trim=True):
        if face == 'v':
            if trim: self.panel(F, u - w / 2 - 0.12, u + w / 2 + 0.12, v, y - 0.14, y + h + 0.12, TRIM, 'liso', side, 0.03)
            self.panel(F, u - w / 2, u + w / 2, v, y, y + h, WHITE, 'janela', side, 0.05)
            if shutters:
                for s in (-1, 1):
                    c0 = u + s * (w / 2 + 0.2); self.panel(F, min(c0, c0 + s * 0.45), max(c0, c0 + s * 0.45), v, y, y + h, shutters, 'liso', side, 0.05)
        else:
            if trim: self.panel_u(F, v - w / 2 - 0.12, v + w / 2 + 0.12, u, y - 0.14, y + h + 0.12, TRIM, 'liso', side, 0.03)
            self.panel_u(F, v - w / 2, v + w / 2, u, y, y + h, WHITE, 'janela', side, 0.05)

    # ------------------------------------------------------------ telhados
    def gable(self, F, u0, u1, v0, v1, y, rh, col, along_u=True, over=0.45, mat='telha', wallc=None, wallm='siding'):
        M = self.M
        if along_u:      # cumeeira paralela a rua (u); aguas para frente e fundo
            vm = (v0 + v1) / 2
            for (va, s) in ((v0 - over, -1), (v1 + over, 1)):
                q = [F.p(u0 - over, va, y - over * rh / ((v1 - v0) / 2)), F.p(u1 + over, va, y - over * rh / ((v1 - v0) / 2)), F.p(u1 + over, vm, y + rh), F.p(u0 - over, vm, y + rh)]
                M.m(mat); n = (F.vx * s * 0.6, 0.8, F.vz * s * 0.6)
                L = math.hypot(vm - va, rh + over * rh / ((v1 - v0) / 2)); W_ = u1 - u0 + 2 * over
                M.quad(*q, col, n, [(0, 0), (W_ / 3, 0), (W_ / 3, L / 3), (0, L / 3)])
                M.m('liso'); M.quad(*q, shade(col, -45), (-n[0], -0.8, -n[2]))
            if wallc:
                M.m(wallm)
                for (ua, s) in ((u0, -1), (u1, 1)):
                    M.tri(F.p(ua, v0, y), F.p(ua, v1, y), F.p(ua, vm, y + rh), wallc, F.nu(s))
        else:            # cumeeira perpendicular a rua (v): empena virada para a rua
            um = (u0 + u1) / 2
            for (ua, s) in ((u0 - over, -1), (u1 + over, 1)):
                q = [F.p(ua, v0 - over, y - over * rh / ((u1 - u0) / 2)), F.p(ua, v1 + over, y - over * rh / ((u1 - u0) / 2)), F.p(um, v1 + over, y + rh), F.p(um, v0 - over, y + rh)]
                M.m(mat); n = (F.ux * s * 0.6, 0.8, F.uz * s * 0.6)
                L = math.hypot(um - ua, rh); W_ = v1 - v0 + 2 * over
                M.quad(*q, col, n, [(0, 0), (W_ / 3, 0), (W_ / 3, L / 3), (0, L / 3)])
                M.m('liso'); M.quad(*q, shade(col, -45), (-n[0], -0.8, -n[2]))
            if wallc:
                M.m(wallm)
                for (va, s) in ((v0, -1), (v1, 1)):
                    M.tri(F.p(u0, va, y), F.p(u1, va, y), F.p(um, va, y + rh), wallc, F.nv(s))

    def hip(self, F, u0, u1, v0, v1, y, rh, col, over=0.5, mat='telha'):
        M = self.M
        ins = min(u1 - u0, v1 - v0) / 2
        c = [F.p(u0 - over, v0 - over, y - 0.15), F.p(u1 + over, v0 - over, y - 0.15), F.p(u1 + over, v1 + over, y - 0.15), F.p(u0 - over, v1 + over, y - 0.15)]
        if (u1 - u0) >= (v1 - v0): t = [F.p(u0 + ins, (v0 + v1) / 2, y + rh), F.p(u1 - ins, (v0 + v1) / 2, y + rh)]; tt = [t[0], t[1], t[1], t[0]]
        else: t = [F.p((u0 + u1) / 2, v0 + ins, y + rh), F.p((u0 + u1) / 2, v1 - ins, y + rh)]; tt = [t[0], t[0], t[1], t[1]]
        nrm = [F.nv(-1), F.nu(1), F.nv(1), F.nu(-1)]
        for k in range(4):
            a, b = c[k], c[(k + 1) % 4]
            if (u1 - u0) >= (v1 - v0): ta, tb = ((t[0], t[1]), (t[1], t[1]), (t[1], t[0]), (t[0], t[0]))[k]
            else: ta, tb = ((t[0], t[0]), (t[0], t[1]), (t[1], t[1]), (t[1], t[0]))[k]
            n = (nrm[k][0] * 0.6, 0.8, nrm[k][2] * 0.6)
            M.m(mat)
            if ta == tb: M.tri(a, b, ta, col if k % 2 == 0 else shade(col, -8), n)
            else: M.quad(a, b, tb, ta, col if k % 2 == 0 else shade(col, -8), n)

    def flat_roof(self, F, u0, u1, v0, v1, y, parapet=0.9, pcol=(232, 230, 224), equip=True):
        M = self.M
        M.m('cascalho'); M.poly([F.p(u0, v0, y), F.p(u1, v0, y), F.p(u1, v1, y), F.p(u0, v1, y)], (205, 203, 198), (0, 1, 0))
        t = 0.3
        for (a, b, c, d) in ((u0, u1, v0, v0 + t), (u0, u1, v1 - t, v1), (u0, u0 + t, v0 + t, v1 - t), (u1 - t, u1, v0 + t, v1 - t)):
            self.box(F, a, b, c, d, y, y + parapet, pcol, 'concreto')
        if equip and (u1 - u0) > 8 and (v1 - v0) > 8:
            r = self.rnd
            for _ in range(r.choice((1, 2, 3))):
                uu = r.uniform(u0 + 2, u1 - 3); vv = r.uniform(v0 + 2, v1 - 3)
                self.box(F, uu, uu + 1.4, vv, vv + 1.0, y, y + 1.0, (200, 204, 208), 'metal')
            if r.random() < 0.6:
                uu = r.uniform(u0 + 3, u1 - 4); vv = r.uniform(v0 + 3, v1 - 4)
                self.box(F, uu, uu + 3, vv, vv + 3, y, y + 2.6, (225, 222, 215), 'concreto')

    # ================================================================== CASAS
    def house(self, F, w, d, style, pal, sf=6.5, garage_side=1, picket=False, fence=True, first=False, last=False, extras=True):
        """casa no lote w x d (u ao longo da rua, v para dentro; v=0 = divisa da frente)"""
        r = self.rnd; M = self.M
        ss = 2.2
        wall, wallm, roofc, roofm, doorc, shut = pal
        gw = 6.4 if w >= 17.5 else 0.0                  # garagem dupla ao lado (se couber)
        hw = min(w - 2 * ss - gw, 15.5)
        if hw < 8: gw = 0; hw = min(w - 2 * ss, 14.0)
        hd = min(d - sf - 9, r.uniform(10.0, 12.5))
        if garage_side > 0: hu0 = ss; hu1 = ss + hw; gu0, gu1 = hu1, hu1 + gw
        else: gu0 = ss; gu1 = ss + gw; hu0 = gu1; hu1 = hu0 + hw
        if gw == 0: hu0 = (w - hw) / 2; hu1 = hu0 + hw
        v0, v1 = sf, sf + hd
        yb = Y0 + 0.35
        self.box(F, hu0 - 0.1, hu1 + 0.1, v0 - 0.1, v1 + 0.1, Y0 - 0.05, yb, (190, 186, 178), 'concreto', top=False)
        fh = 2.85
        floors = {'ranch': 1, 'colonial': 2, 'craftsman': 1, 'cape': 1, 'moderna': 2}[style]
        wu = (3.0, 2.4, 1.0) if wallm == 'siding' else (2.4, 2.4, 1.0)
        y1 = yb + floors * fh
        self.box(F, hu0, hu1, v0, v1, yb, y1, wall, wallm, top=False)
        # janelas da frente e laterais
        nwin = max(2, int(hw / 3.2))
        door_u = (hu0 + hu1) / 2 if style in ('colonial', 'cape') else hu0 + hw * (0.32 if garage_side > 0 else 0.68)
        for fl in range(floors):
            yy = yb + fl * fh + 0.95
            for k in range(nwin):
                uc = hu0 + hw * (k + 0.5) / nwin
                if fl == 0 and abs(uc - door_u) < 1.6: continue
                self.window(F, uc, v0, yy, 1.25 if style != 'moderna' else 2.2, 1.45, -1, shut if style in ('colonial', 'cape') else None)
            for (uu, sd) in ((hu0, -1), (hu1, 1)):
                if gw and ((sd > 0 and garage_side > 0) or (sd < 0 and garage_side < 0)) and fl == 0: continue
                for k in range(max(1, int(hd / 4.5))):
                    self.window(F, uu, v0 + hd * (k + 0.5) / max(1, int(hd / 4.5)), yy, 1.1, 1.35, sd, None, 'u')
            for k in range(max(2, int(hw / 4))):                      # fundos
                self.window(F, hu0 + hw * (k + 0.5) / max(2, int(hw / 4)), v1, yy, 1.2, 1.35, 1)
        # porta + soleira
        self.panel(F, door_u - 0.62, door_u + 0.62, v0, yb, yb + 2.25, TRIM, 'liso', -1, 0.03)
        self.panel(F, door_u - 0.5, door_u + 0.5, v0, yb, yb + 2.15, doorc, 'porta', -1, 0.05)
        self.box(F, door_u - 1.2, door_u + 1.2, v0 - 1.4, v0, Y0, yb, (205, 202, 196), 'concreto')
        # telhado por estilo
        if style == 'ranch':
            if r.random() < 0.5: self.hip(F, hu0, hu1 + (gw if garage_side > 0 else 0), v0, v1, y1, 1.9, roofc, 0.6, roofm)
            else: self.gable(F, hu0, hu1, v0, v1, y1, 2.0, roofc, True, 0.5, roofm, wall, wallm)
        elif style == 'colonial':
            self.gable(F, hu0, hu1, v0, v1, y1, 2.6, roofc, True, 0.45, roofm, wall, wallm)
            # portico com colunas e frontao
            self.box(F, door_u - 1.6, door_u + 1.6, v0 - 1.8, v0, Y0, yb, (215, 212, 206), 'concreto')
            for s in (-1, 1): M.m('liso'); M.cyl(*F.xz(door_u + s * 1.35, v0 - 1.5), 0.13, yb, yb + 2.8, TRIM, 8)
            self.box(F, door_u - 1.7, door_u + 1.7, v0 - 1.9, v0, yb + 2.8, yb + 3.05, TRIM, 'liso')
            M.m('liso'); M.tri(F.p(door_u - 1.7, v0 - 1.9, yb + 3.05), F.p(door_u + 1.7, v0 - 1.9, yb + 3.05), F.p(door_u, v0 - 1.9, yb + 3.9), TRIM, F.nv(-1))
            M.m(roofm); M.quad(F.p(door_u - 1.8, v0 - 2.0, yb + 3.0), F.p(door_u, v0 - 2.0, yb + 3.95), F.p(door_u, v0, yb + 3.95), F.p(door_u - 1.8, v0, yb + 3.0), roofc, (0, 1, 0))
            M.quad(F.p(door_u + 1.8, v0 - 2.0, yb + 3.0), F.p(door_u + 1.8, v0, yb + 3.0), F.p(door_u, v0, yb + 3.95), F.p(door_u, v0 - 2.0, yb + 3.95), roofc, (0, 1, 0))
        elif style == 'craftsman':
            self.gable(F, hu0, hu1, v0, v1, y1, 2.6, roofc, False, 0.6, roofm, wall, wallm)
            # varanda larga com colunas de base de pedra
            pu0, pu1 = hu0 + 0.3, hu1 - 0.3
            self.box(F, pu0, pu1, v0 - 2.6, v0, Y0, yb, (200, 196, 188), 'concreto')
            for uu in (pu0 + 0.3, (pu0 + pu1) / 2, pu1 - 0.3):
                self.box(F, uu - 0.3, uu + 0.3, v0 - 2.4, v0 - 1.8, yb, yb + 0.9, WHITE, 'pedra')
                self.box(F, uu - 0.16, uu + 0.16, v0 - 2.27, v0 - 1.93, yb + 0.9, yb + 2.7, TRIM, 'liso')
            self.box(F, pu0 - 0.2, pu1 + 0.2, v0 - 2.8, v0, yb + 2.7, yb + 2.9, TRIM, 'liso', mat_top=roofm, colt=roofc)
            self.box(F, pu0, pu1, v0 - 2.4, v0 - 2.32, yb + 0.55, yb + 0.65, TRIM, 'liso')
        elif style == 'cape':
            self.gable(F, hu0, hu1, v0, v1, y1, 4.2, roofc, True, 0.35, roofm, wall, wallm)
            # aguas-furtadas (dormers)
            for k in range(2 if hw > 10 else 1):
                uc = hu0 + hw * (k + 0.5) / (2 if hw > 10 else 1)
                vd = v0 + hd * 0.3; yd = y1 + 4.2 * 0.6 * (vd - v0) / (hd / 2) * 0.5 + 0.2
                self.box(F, uc - 0.9, uc + 0.9, vd - 0.4, vd + 1.6, y1 + 0.9, y1 + 2.5, wall, wallm, top=False)
                self.window(F, uc, vd - 0.4, y1 + 1.2, 1.0, 1.0, -1, None)
                self.gable(F, uc - 0.9, uc + 0.9, vd - 0.4, vd + 1.6, y1 + 2.5, 0.8, roofc, False, 0.15, roofm, wall, wallm)
        else:   # moderna: dois volumes, laje plana, painel de madeira
            self.flat_roof(F, hu0, hu1, v0, v1, y1, 0.5, (240, 238, 232), False)
            self.box(F, hu0 - 0.3, hu1 + 0.3, v0 - 0.6, v1 + 0.3, y1 - 0.05, y1 + 0.25, (240, 238, 232), 'concreto')
            self.box(F, hu0 + hw * 0.55, hu1 - 0.3, v0 - 0.08, v0, yb + fh, y1, WHITE, 'madeira', top=False)
        # chamine
        if style in ('colonial', 'cape', 'craftsman') or (style == 'ranch' and r.random() < 0.5):
            cu = hu1 - 1.5 if r.random() < 0.5 else hu0 + 1.0
            self.box(F, cu, cu + 0.9, v0 + hd * 0.55, v0 + hd * 0.55 + 0.9, yb, y1 + 3.3, WHITE, 'tijolo')
        # garagem
        if gw:
            gy1 = yb + 2.9
            self.box(F, gu0, gu1, v0 + 0.6, v0 + 7.0, Y0 + 0.05, gy1, wall, wallm, top=False)
            self.panel(F, gu0 + 0.5, gu1 - 0.5, v0 + 0.6, Y0 + 0.05, Y0 + 2.4, (245, 243, 238), 'garagem', -1, 0.05)
            if style == 'moderna': self.flat_roof(F, gu0, gu1, v0 + 0.6, v0 + 7.0, gy1, 0.3, (240, 238, 232), False)
            elif style == 'ranch' and garage_side > 0: pass
            else: self.gable(F, gu0, gu1, v0 + 0.6, v0 + 7.0, gy1, 1.5, roofc, True, 0.4, roofm, wall, wallm)
            dr0, dr1 = gu0 + 0.3, gu1 - 0.3
        else:
            dr0, dr1 = (w - 3.4, w - 0.6) if garage_side > 0 else (0.6, 3.4)
        # entrada de carro (concreto) ate o meio-fio, e caminho da porta
        self.M.m('concreto')
        self.M.poly([F.p(dr0, -3.6, 0.175), F.p(dr1, -3.6, 0.175), F.p(dr1, v0 + 0.6, Y0 + 0.04), F.p(dr0, v0 + 0.6, Y0 + 0.04)], WHITE, (0, 1, 0))
        self.M.poly([F.p(door_u - 0.6, 0.0, Y0 + 0.03), F.p(door_u + 0.6, 0.0, Y0 + 0.03), F.p(door_u + 0.6, v0 - 1.4, Y0 + 0.03), F.p(door_u - 0.6, v0 - 1.4, Y0 + 0.03)], WHITE, (0, 1, 0))
        self.drives.append(F.xz((dr0 + dr1) / 2, -1.8))
        # caixa de correio
        mu = dr0 - 0.8 if dr0 > 1.5 else dr1 + 0.8
        self.box(F, mu - 0.05, mu + 0.05, 0.4, 0.5, Y0, Y0 + 1.05, (90, 90, 92), 'metal')
        self.box(F, mu - 0.22, mu + 0.22, 0.3, 0.75, Y0 + 1.0, Y0 + 1.3, rgb('#2F3E56') if r.random() < 0.6 else (60, 60, 62), 'metal')
        # cercas: quintal (madeira alta) e cerquinha branca na frente
        if fence:
            fc = FENCE_W[r.randrange(len(FENCE_W))]
            vf = v0 + hd * 0.6
            self.box(F, w - 0.12, w, vf, d - 0.1, Y0, Y0 + 1.8, fc, 'cerca')
            if first: self.box(F, 0, 0.12, vf, d - 0.1, Y0, Y0 + 1.8, fc, 'cerca')
            self.box(F, 0, w, d - 0.22, d - 0.1, Y0, Y0 + 1.8, fc, 'cerca')
            self.box(F, hu1, w - 0.12, vf, vf + 0.12, Y0, Y0 + 1.8, fc, 'cerca') if not (gw and garage_side > 0) else None
        if picket:      # cerquinha branca: painel de tabuas (textura) + travessa de cima
            for (a, b) in ((0.3, min(dr0, door_u - 0.8) - 0.3), (door_u + 0.8, dr0 - 0.3 if dr0 > door_u else w - 0.3)):
                if b - a > 0.6:
                    self.box(F, a, b, 0.26, 0.31, Y0, Y0 + 0.95, (255, 255, 255), 'cerca')
                    self.box(F, a, b, 0.24, 0.33, Y0 + 0.95, Y0 + 1.02, TRIM, 'liso')
        # quintal: deck/patio, piscina, deposito
        if extras and d - v1 > 9:
            self.box(F, hu0 + 1, hu0 + 1 + min(5, hw - 2), v1, v1 + 3.2, Y0, Y0 + 0.25, WHITE, 'madeira')
            if r.random() < 0.28 and w > 15 and d - v1 > 13:
                pu0, pu1 = hu0 + 1.5, min(hu0 + 9, w - 2.5); pv0, pv1 = v1 + 4.5, min(v1 + 9.5, d - 2.5)
                self.box(F, pu0 - 0.6, pu1 + 0.6, pv0 - 0.6, pv1 + 0.6, Y0, Y0 + 0.12, WHITE, 'concreto')
                M.m('agua'); M.poly([F.p(pu0, pv0, Y0 + 0.14), F.p(pu1, pv0, Y0 + 0.14), F.p(pu1, pv1, Y0 + 0.14), F.p(pu0, pv1, Y0 + 0.14)], (150, 230, 240), (0, 1, 0))
            elif r.random() < 0.4:
                su = w - 4.5 if garage_side < 0 else 1.0
                self.box(F, su, su + 3.2, d - 4.0, d - 1.2, Y0, Y0 + 2.3, wall, 'madeira', top=False)
                self.gable(F, su, su + 3.2, d - 4.0, d - 1.2, Y0 + 2.3, 0.9, roofc, True, 0.2, roofm, wall, 'madeira')
        self.solid(F, hu0, hu1, v0, v1)
        if gw: self.solid(F, gu0, gu1, v0 + 0.6, v0 + 7.0)
        return {'door': F.xz(door_u, v0), 'trees_front': [(r.uniform(1.5, w - 1.5), r.uniform(1.5, v0 - 2.5))] if v0 > 5 else [], 'back': (v1, d)}

    # ================================================================== CENTRO
    def midrise(self, F, w, d, floors, wall, facade='janelas', shop=True, awn=None, roof_equip=True):
        """predio de esquina/meio de quadra colado na calcada: loja no terreo + andares com fachada texturizada"""
        r = self.rnd; M = self.M
        gh = 4.5 if shop else 3.0; fh = 3.0 if facade == 'janelas' else 3.6
        y0 = Y0; yg = y0 + gh; y1 = yg + floors * fh
        # terreo: vitrines
        if shop:
            self.box(F, 0, w, 0, d, y0, yg, (70, 72, 76), 'concreto', top=False)
            nb = max(1, int(w / 3.0))
            M.m('vitrine')
            for (vv, side, pu, pv) in ((0, -1, None, None),):
                self.panel(F, 0.3, w - 0.3, 0, y0 + 0.4, yg - 0.5, WHITE, 'vitrine', -1, 0.05, [(0, 1), (w / 3.0, 1), (w / 3.0, 0), (0, 0)])
            if awn:
                q = [F.p(0.4, -0.05, yg - 0.3), F.p(w - 0.4, -0.05, yg - 0.3), F.p(w - 0.4, -1.6, yg - 0.9), F.p(0.4, -1.6, yg - 0.9)]
                M.m('liso'); M.quad(*q, awn, (F.vx * -0.5, 0.85, F.vz * -0.5)); M.quad(*q, shade(awn, -40), (F.vx * 0.5, -0.85, F.vz * 0.5))
            self.box(F, -0.1, w + 0.1, -0.15, d, yg - 0.3, yg, shade(wall, -20), 'concreto', top=False)
        self.box(F, 0, w, 0, d, yg, y1, wall, facade, top=False, wall_uv=(3.0, fh, y1))
        self.box(F, -0.15, w + 0.15, -0.15, d + 0.15, y1, y1 + 0.35, shade(wall, -12), 'concreto', top=False)
        self.flat_roof(F, 0.15, w - 0.15, 0.15, d - 0.15, y1 + 0.35, 0.8, shade(wall, -8), roof_equip)
        self.solid(F, 0, w, 0, d)
        return y1

    def tower(self, F, w, d, floors, glass_tint, podium_col, crown_col):
        r = self.rnd; M = self.M
        y0 = Y0; ph = 3 * 4.2
        self.box(F, 0, w, 0, d, y0, y0 + ph, podium_col, 'escritorio', top=False, wall_uv=(3.0, 4.2, y0 + ph))
        self.panel(F, w * 0.3, w * 0.7, 0, y0, y0 + 4.0, WHITE, 'vitrine', -1, 0.06, [(0, 1), (w * 0.4 / 3, 1), (w * 0.4 / 3, 0), (0, 0)])
        self.box(F, w * 0.28, w * 0.72, -2.6, 0, y0 + 4.2, y0 + 4.5, (230, 230, 228), 'concreto')
        self.flat_roof(F, 0, w, 0, d, y0 + ph, 1.0, podium_col, False)
        # corpo da torre com recuos
        ins = 3.0; y = y0 + ph; left = floors
        tiers = 1 if floors < 18 else (2 if floors < 30 else 3)
        u0, u1, v0, v1 = ins, w - ins, ins, d - ins
        for t in range(tiers):
            nf = left if t == tiers - 1 else int(floors * (0.55 if t == 0 else 0.3))
            left -= nf
            yt = y + nf * 3.6
            self.box(F, u0, u1, v0, v1, y, yt, glass_tint, 'vidro', top=False, wall_uv=(3.0, 3.6, yt))
            # aletas verticais nas quinas
            for (a, b) in ((u0 - 0.25, u0 + 0.35), (u1 - 0.35, u1 + 0.25)):
                self.box(F, a, b, v0 - 0.25, v0 + 0.35, y, yt, crown_col, 'concreto', top=False)
                self.box(F, a, b, v1 - 0.35, v1 + 0.25, y, yt, crown_col, 'concreto', top=False)
            y = yt
            if t < tiers - 1:
                self.flat_roof(F, u0, u1, v0, v1, y, 0.9, crown_col, False)
                u0 += 2.5; u1 -= 2.5; v0 += 2.5; v1 -= 2.5
        self.box(F, u0 - 0.3, u1 + 0.3, v0 - 0.3, v1 + 0.3, y, y + 1.6, crown_col, 'concreto', top=False)
        self.flat_roof(F, u0, u1, v0, v1, y + 0.2, 1.4, crown_col, True)
        if r.random() < 0.7:
            cx, cz = F.xz((u0 + u1) / 2, (v0 + v1) / 2)
            M.m('metal'); M.cyl(cx, cz, 0.25, y + 1.6, y + 1.6 + r.uniform(8, 16), (210, 60, 60), 6)
        self.solid(F, 0, w, 0, d)
        return y

    # ================================================================== COMERCIO E CIVICOS
    def parking(self, F, u0, u1, v0, v1, cars=None, y=Y0):
        """estacionamento: asfalto com vagas pintadas; cars(callback x,z,dx,dz) para os carros"""
        M = self.M
        M.m('asfalto'); M.poly([F.p(u0, v0, y + 0.02), F.p(u1, v0, y + 0.02), F.p(u1, v1, y + 0.02), F.p(u0, v1, y + 0.02)], WHITE, (0, 1, 0))
        M.m('liso')
        for row in ((v0 + 0.5, v0 + 5.5), (v1 - 5.5, v1 - 0.5)):
            u = u0 + 1
            while u < u1 - 2.5:
                M.poly([F.p(u, row[0], y + 0.035), F.p(u + 0.12, row[0], y + 0.035), F.p(u + 0.12, row[1], y + 0.035), F.p(u, row[1], y + 0.035)], (245, 245, 240), (0, 1, 0))
                if cars and self.rnd.random() < 0.45: cars(*F.xz(u + 1.3, (row[0] + row[1]) / 2), F.vx, F.vz)
                u += 2.6

    def shop_row(self, F, w, d, sign, wall, hgt=5.5, glass=True):
        """loja de galeria/supermercado: caixa com vitrine e faixa de letreiro colorida"""
        M = self.M
        self.box(F, 0, w, 0, d, Y0, Y0 + hgt, wall, 'reboco', top=False)
        if glass: self.panel(F, 0.4, w - 0.4, 0, Y0 + 0.1, Y0 + 3.4, WHITE, 'vitrine', -1, 0.05, [(0, 1), (w / 3, 1), (w / 3, 0), (0, 0)])
        self.box(F, -0.25, w + 0.25, -0.4, 0.1, Y0 + 3.7, Y0 + hgt + 0.6, sign, 'liso', top=True)
        self.box(F, -0.2, w + 0.2, -2.2, 0, Y0 + 3.4, Y0 + 3.6, (220, 220, 216), 'concreto')
        self.flat_roof(F, 0, w, 0, d, Y0 + hgt, 0.6, wall, True)
        self.solid(F, 0, w, 0, d)

    def gas_station(self, F, w, d, brand=(200, 40, 40)):
        M = self.M
        self.parking(F, 0.5, w - 0.5, 0.5, d - 0.5)
        cu0, cu1, cv0, cv1 = w * 0.15, w * 0.75, 4, 18
        for (u, v) in ((cu0 + 1, cv0 + 1), (cu1 - 1, cv0 + 1), (cu0 + 1, cv1 - 1), (cu1 - 1, cv1 - 1)):
            self.box(F, u - 0.3, u + 0.3, v - 0.3, v + 0.3, Y0, Y0 + 5.2, (235, 235, 235), 'metal')
        self.box(F, cu0, cu1, cv0, cv1, Y0 + 5.2, Y0 + 5.8, (245, 245, 245), 'liso', colt=(240, 240, 240))
        self.box(F, cu0 - 0.1, cu1 + 0.1, cv0 - 0.1, cv1 + 0.1, Y0 + 5.25, Y0 + 5.75, brand, 'liso', top=False)
        for v in (cv0 + 4.5, cv1 - 4.5):
            for u in (cu0 + (cu1 - cu0) * 0.3, cu0 + (cu1 - cu0) * 0.7):
                self.box(F, u - 2.2, u + 2.2, v - 0.6, v + 0.6, Y0, Y0 + 0.25, (210, 210, 205), 'concreto')
                self.box(F, u - 0.4, u + 0.4, v - 0.3, v + 0.3, Y0 + 0.25, Y0 + 1.9, (240, 240, 240), 'metal')
                self.box(F, u - 0.42, u + 0.42, v - 0.32, v + 0.32, Y0 + 1.5, Y0 + 1.9, brand, 'liso')
        self.shop_row(Frame(F.xz(w * 0.15, d - 14), (F.ux, F.uz)), w * 0.6, 12, brand, (240, 238, 232), 4.6)
        # totem de precos
        self.box(F, w - 3.2, w - 1.4, 1.2, 1.8, Y0, Y0 + 6.5, (245, 245, 245), 'metal')
        self.box(F, w - 3.4, w - 1.2, 1.15, 1.85, Y0 + 5.0, Y0 + 6.6, brand, 'liso')

    def church(self, F, w, d):
        M = self.M; wall = (246, 242, 232)
        nw = min(w * 0.55, 22); nd = min(d - 10, 42); u0 = (w - nw) / 2; v0 = 8
        self.box(F, u0, u0 + nw, v0, v0 + nd, Y0, Y0 + 11, wall, 'reboco', top=False)
        self.gable(F, u0, u0 + nw, v0, v0 + nd, Y0 + 11, 6.5, (190, 110, 80), False, 0.6, 'ceramica', wall, 'reboco')
        for k in range(5):
            vv = v0 + 6 + k * (nd - 10) / 4
            for (uu, sd) in ((u0, -1), (u0 + nw, 1)): self.window(F, uu, vv, Y0 + 3.0, 1.6, 4.5, sd, None, 'u')
        # torre sineira
        tw = 6.0; tu = u0 + nw - tw + 2
        self.box(F, tu, tu + tw, v0 - 4, v0 + 2, Y0, Y0 + 24, wall, 'reboco', top=False)
        for (vv, sd) in ((v0 - 4, -1),):
            self.panel(F, tu + 1.8, tu + tw - 1.8, vv, Y0 + 18, Y0 + 21.5, (60, 60, 64), 'liso', sd, 0.05)
        cx, cz = F.xz(tu + tw / 2, v0 - 1); M.m('ceramica'); M.cyl(cx, cz, tw * 0.75, Y0 + 24, Y0 + 31, (190, 110, 80), 4, False, 0.0)
        M.m('metal'); M.box(cx - 0.08, cx + 0.08, Y0 + 31, Y0 + 34, cz - 0.08, cz + 0.08, (200, 180, 90)); M.box(cx - 0.8, cx + 0.8, Y0 + 32.6, Y0 + 32.8, cz - 0.08, cz + 0.08, (200, 180, 90))
        # fachada: porta grande, rosacea, escadaria
        self.panel(F, u0 + nw / 2 - 1.6, u0 + nw / 2 + 1.6, v0, Y0 + 0.6, Y0 + 5.6, (110, 70, 45), 'porta', -1, 0.05)
        cx, cz = F.xz(u0 + nw / 2, v0 - 0.06); M.m('janela')
        pts = [(cx + F.ux * math.cos(a) * 1.8, Y0 + 8 + math.sin(a) * 1.8, cz + F.uz * math.cos(a) * 1.8) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
        M.poly(pts, (230, 200, 160), F.nv(-1))
        for k in range(3): self.box(F, u0 + nw / 2 - 4 + k * 0.0, u0 + nw / 2 + 4, v0 - 3 + k, v0 - 2 + k, Y0, Y0 + 0.2 + k * 0.2, (215, 210, 200), 'pedra')
        self.solid(F, u0, u0 + nw, v0, v0 + nd); self.solid(F, tu, tu + tw, v0 - 4, v0 + 2)

    def city_hall(self, F, w, d):
        M = self.M; wall = (240, 234, 220)
        bw, bd = w - 16, min(d - 20, 46); u0 = 8; v0 = 14
        self.box(F, u0, u0 + bw, v0, v0 + bd, Y0, Y0 + 2.0, WHITE, 'pedra', top=False)
        self.box(F, u0, u0 + bw, v0, v0 + bd, Y0 + 2.0, Y0 + 15, wall, 'reboco', top=False)
        for fl in range(3):
            for k in range(int(bw / 4)):
                self.window(F, u0 + 2 + k * 4, v0, Y0 + 3.0 + fl * 4, 1.4, 2.6, -1)
        # portico: 8 colunas, frontao
        pu0, pu1 = u0 + bw * 0.28, u0 + bw * 0.72
        for k in range(8):
            uu = pu0 + (pu1 - pu0) * k / 7; cx, cz = F.xz(uu, v0 - 4); M.m('concreto'); M.cyl(cx, cz, 0.55, Y0 + 2.0, Y0 + 14, (250, 248, 242), 10)
        self.box(F, pu0 - 0.8, pu1 + 0.8, v0 - 5.2, v0, Y0 + 14, Y0 + 15.5, wall, 'concreto')
        M.m('reboco'); M.tri(F.p(pu0 - 0.8, v0 - 5.2, Y0 + 15.5), F.p(pu1 + 0.8, v0 - 5.2, Y0 + 15.5), F.p((pu0 + pu1) / 2, v0 - 5.2, Y0 + 19.5), wall, F.nv(-1))
        self.gable(F, pu0 - 1, pu1 + 1, v0 - 5.4, v0, Y0 + 15.5, 4.0, (150, 150, 150), True, 0.2, 'telha', None)
        for k in range(6): self.box(F, pu0 - 2, pu1 + 2, v0 - 12 + k * 1.2, v0 - 10.8 + k * 1.2, Y0, Y0 + 0.33 * (k + 1), (225, 220, 210), 'pedra')
        self.flat_roof(F, u0, u0 + bw, v0, v0 + bd, Y0 + 15, 1.2, wall, False)
        # cupula
        cx, cz = F.xz(u0 + bw / 2, v0 + bd / 2)
        M.m('reboco'); M.cyl(cx, cz, 9, Y0 + 15, Y0 + 21, wall, 16)
        M.m('metal'); M.sphere(cx, Y0 + 21, cz, 9, (120, 160, 150), 16, 6, 0.85)
        M.m('metal'); M.cyl(cx, cz, 0.12, Y0 + 28, Y0 + 34, (220, 220, 220), 6)
        self.solid(F, u0, u0 + bw, v0, v0 + bd)

    def school(self, F, w, d, field_cb=None):
        M = self.M
        bw = min(w * 0.45, 80); bd = 16
        self.box(F, 6, 6 + bw, 10, 10 + bd, Y0, Y0 + 8.2, (255, 255, 255), 'tijolo', top=False)
        for fl in range(2):
            for k in range(int(bw / 3.5)):
                self.window(F, 8 + k * 3.5, 10, Y0 + 1.0 + fl * 3.8, 2.4, 1.8, -1)
        self.flat_roof(F, 6, 6 + bw, 10, 10 + bd, Y0 + 8.2, 0.8, (230, 226, 218), True)
        self.box(F, 6, 6 + 16, 10 + bd, 10 + bd + 26, Y0, Y0 + 8.2, (255, 255, 255), 'tijolo', top=False)
        self.flat_roof(F, 6, 6 + 16, 10 + bd, 10 + bd + 26, Y0 + 8.2, 0.8, (230, 226, 218), False)
        self.panel(F, 6 + bw / 2 - 2, 6 + bw / 2 + 2, 10, Y0, Y0 + 2.8, WHITE, 'vitrine', -1, 0.05)
        self.box(F, 6 + bw / 2 - 3, 6 + bw / 2 + 3, 7, 10, Y0 + 3.0, Y0 + 3.3, (230, 230, 228), 'concreto')
        self.box(F, 6 + bw / 2 - 3.2, 6 + bw / 2 + 3.2, 9.5, 10.05, Y0 + 6.6, Y0 + 7.8, (40, 70, 120), 'liso', top=False)
        # bandeira
        cx, cz = F.xz(4, 5); M.m('metal'); M.cyl(cx, cz, 0.08, Y0, Y0 + 10, (230, 230, 230), 6)
        M.m('liso'); M.quad(F.p(4, 5, Y0 + 8.4), F.p(6.4, 5, Y0 + 8.4), F.p(6.4, 5, Y0 + 9.9), F.p(4, 5, Y0 + 9.9), (40, 140, 70), F.nv(-1))
        # campo de futebol + pista
        fu0, fu1 = 10 + bw, w - 8; fv0, fv1 = 8, d - 8
        if fu1 - fu0 > 50:
            M.m('quadra'); M.poly([F.p(fu0, fv0, Y0 + 0.03), F.p(fu1, fv0, Y0 + 0.03), F.p(fu1, fv1, Y0 + 0.03), F.p(fu0, fv1, Y0 + 0.03)], (200, 120, 90), (0, 1, 0))
            M.m('grama'); M.poly([F.p(fu0 + 6, fv0 + 6, Y0 + 0.05), F.p(fu1 - 6, fv0 + 6, Y0 + 0.05), F.p(fu1 - 6, fv1 - 6, Y0 + 0.05), F.p(fu0 + 6, fv1 - 6, Y0 + 0.05)], (230, 255, 220), (0, 1, 0))
            M.m('liso'); um = (fu0 + fu1) / 2
            for (a, b, c, e) in ((um - 0.06, um + 0.06, fv0 + 6, fv1 - 6), (fu0 + 6, fu1 - 6, fv0 + 6, fv0 + 6.12), (fu0 + 6, fu1 - 6, fv1 - 6.12, fv1 - 6)):
                M.poly([F.p(a, c, Y0 + 0.07), F.p(b, c, Y0 + 0.07), F.p(b, e, Y0 + 0.07), F.p(a, e, Y0 + 0.07)], (250, 250, 248), (0, 1, 0))
            for uu in (fu0 + 6.5, fu1 - 6.5):
                vm = (fv0 + fv1) / 2
                self.box(F, uu - 0.06, uu + 0.06, vm - 3.7, vm - 3.6, Y0, Y0 + 2.4, (250, 250, 250), 'liso'); self.box(F, uu - 0.06, uu + 0.06, vm + 3.6, vm + 3.7, Y0, Y0 + 2.4, (250, 250, 250), 'liso')
                self.box(F, uu - 0.06, uu + 0.06, vm - 3.7, vm + 3.7, Y0 + 2.3, Y0 + 2.42, (250, 250, 250), 'liso')
        self.parking(F, 6, 6 + bw, 10 + bd + 4, min(d - 6, 10 + bd + 28), field_cb)
        self.solid(F, 6, 6 + bw, 10, 10 + bd)

    def hospital(self, F, w, d):
        M = self.M
        self.midrise(F, w, d, 7, (248, 248, 250), 'escritorio', False)
        cx, cz = F.xz(w / 2, -0.08)
        y = Y0 + 3.0 + 7 * 3.6 - 3.0
        M.m('liso')
        for (a, b, c, e) in ((-0.6, 0.6, -2.0, 2.0), (-2.0, 2.0, -0.6, 0.6)):
            M.quad(F.p(w / 2 + a, -0.1, y + c), F.p(w / 2 + b, -0.1, y + c), F.p(w / 2 + b, -0.1, y + e), F.p(w / 2 + a, -0.1, y + e), (210, 30, 40), F.nv(-1))
        self.box(F, w / 2 - 6, w / 2 + 6, -5, 0, Y0 + 3.2, Y0 + 3.5, (235, 235, 235), 'concreto')
