"""ETAPA E: construcoes decorativas nos lotes comuns (casas, sobrados, geminadas, mansoes, apartamentos, torres, hoteis, comercio, igreja, escola, posto, mercado, galpao, pracinhas).
Cada lote vira uma construcao alinhada a rua (referencial do lote: u ao longo da rua, v para dentro). Tudo assado num arquivo SUB1 proprio (c5_bld.bin); colisoes em retangulos girados."""
import math, random
import numpy as np
from bake import Bake, rgb, shade, PLAIN, STONE, WOOD, METAL, PAVER, ROOF, TILE, PLASTER
from plan import *
import terrain_final as T

WALLS_WARM = [rgb(c) for c in ('#F2E3C6', '#EAD3A8', '#F4EBDD', '#E9C9B0', '#F0DCC0', '#DCC9A8', '#F7E8B8', '#E6D5C3')]
WALLS_COOL = [rgb(c) for c in ('#E4ECEF', '#D3E3E8', '#EDEFE8', '#DDE6D8', '#E8E3F0', '#F1F1EC', '#D9E5F2')]
WALLS_BRIGHT = [rgb(c) for c in ('#F4A261', '#E9C46A', '#8AB17D', '#6FA8DC', '#E76F51', '#F2CC8F', '#B5C99A', '#F28482', '#84A59D')]
ROOFS = [rgb(c) for c in ('#B5543A', '#A64B35', '#7A5238', '#6B6F76', '#3E5C7A', '#8C3B2E', '#5B4636')]
TRIM = rgb('#F7F4EC'); GLASS = rgb('#7FA8C4'); GLASS_D = rgb('#3E5F7A'); DARK = rgb('#33363C'); DOOR = [rgb(c) for c in ('#5B3A29', '#2F4A66', '#7A2E2E', '#2E5B3E', '#3B3B3B')]
CONC = rgb('#BDB8AE'); CONC2 = rgb('#A39E94'); GRASS_C = rgb('#6FA84A'); PAVE = rgb('#CFC9BC')
TOWER_GLASS = [rgb(c) for c in ('#5E8CAE', '#6F9AB5', '#4D7596', '#7FA8C4', '#86A9B8')]
TOWER_WALL = [rgb(c) for c in ('#E8E4DA', '#D2CBBE', '#B9B3A8', '#EFEAE0', '#C9C0AE')]


class Frame:
    def __init__(self, rect, T_=None):
        a, b, c, d = rect
        self.a = a; w = math.hypot(b[0] - a[0], b[1] - a[1]); dd = math.hypot(d[0] - a[0], d[1] - a[1])
        self.w, self.d = w, dd
        self.tx, self.tz = (b[0] - a[0]) / w, (b[1] - a[1]) / w
        self.nx, self.nz = (d[0] - a[0]) / dd, (d[1] - a[1]) / dd

    def xz(self, u, v): return (self.a[0] + self.tx * u + self.nx * v, self.a[1] + self.tz * u + self.nz * v)

    def pt(self, u, v, y): x, z = self.xz(u, v); return (x, y, z)


class Gen:
    def __init__(self, plan, hf, geo, seed=RNG + 11):
        self.P = plan; self.hf = hf; self.geo = geo; self.rnd = random.Random(seed)
        self.B = Bake(); self.solids = []; self.trees = []; self.stats = {'tris0': 0}; self.kinds = {}; self.items = []

    # ------------------------------------------------------------------ primitivas
    def sample(self, x, z): return float(T.sample8(self.hf, x, z))

    def box(self, F, u0, u1, v0, v1, y0, y1, col, mat=PLASTER, top=True, uvs=1.0):
        c4 = [F.xz(u0, v0), F.xz(u1, v0), F.xz(u1, v1), F.xz(u0, v1)]
        self.B.obox_pts(c4, y0, y1, col, mat, top, False, uvs)

    def quad_v(self, F, u0, u1, v, y0, y1, col, side, mat=PLAIN, off=0.03):
        """painel vertical numa parede de frente/fundo (v fixo); side=-1 olha para a rua, +1 para o fundo"""
        v2 = v + side * off
        n = (F.nx * side, 0, F.nz * side)
        self.B.quad(mat, [F.pt(u0, v2, y0), F.pt(u1, v2, y0), F.pt(u1, v2, y1), F.pt(u0, v2, y1)] if side < 0 else [F.pt(u1, v2, y0), F.pt(u0, v2, y0), F.pt(u0, v2, y1), F.pt(u1, v2, y1)], n, col, None, True)

    def quad_u(self, F, v0, v1, u, y0, y1, col, side, mat=PLAIN, off=0.03):
        """painel vertical numa parede lateral (u fixo); side=-1 olha para -T, +1 para +T"""
        u2 = u + side * off
        n = (F.tx * side, 0, F.tz * side)
        self.B.quad(mat, [F.pt(u2, v1, y0), F.pt(u2, v0, y0), F.pt(u2, v0, y1), F.pt(u2, v1, y1)] if side < 0 else [F.pt(u2, v0, y0), F.pt(u2, v1, y0), F.pt(u2, v1, y1), F.pt(u2, v0, y1)], n, col, None, True)

    def windows_front(self, F, u0, u1, v, y0, floor_h, floors, wcol, wide=1.3, high=1.35, sill=0.9, gap=3.0, frame=True, side=-1, skip=None):
        """janelas individuais por andar, distribuidas ao longo da parede"""
        n = max(1, int((u1 - u0) / gap)); step = (u1 - u0) / n
        for fl in range(floors):
            for k in range(n):
                if skip and skip(fl, k, n): continue
                uc = u0 + step * (k + 0.5)
                ya = y0 + fl * floor_h + sill
                if frame: self.quad_v(F, uc - wide / 2 - 0.1, uc + wide / 2 + 0.1, v, ya - 0.1, ya + high + 0.1, TRIM, side, PLAIN, 0.02)
                self.quad_v(F, uc - wide / 2, uc + wide / 2, v, ya, ya + high, wcol, side, PLAIN, 0.035)

    def windows_side(self, F, v0, v1, u, y0, floor_h, floors, wcol, side, wide=1.2, high=1.3, sill=0.9, gap=3.6):
        n = max(1, int((v1 - v0) / gap)); step = (v1 - v0) / n
        for fl in range(floors):
            for k in range(n):
                vc = v0 + step * (k + 0.5); ya = y0 + fl * floor_h + sill
                self.quad_u(F, vc - wide / 2, vc + wide / 2, u, ya, ya + high, wcol, side, PLAIN, 0.035)

    def gable_roof(self, F, u0, u1, v0, v1, y, rh, col, ridge_u=True, over=0.5, trim=True):
        """telhado de duas aaguas; ridge_u: cumeeira ao longo de u (aguas para frente/fundo)"""
        B = self.B
        if ridge_u:
            vm = (v0 + v1) / 2
            for (va, vb, sd) in ((v0 - over, vm, -1), (v1 + over, vm, 1)):
                q = [F.pt(u0 - over, va, y - 0.1), F.pt(u1 + over, va, y - 0.1), F.pt(u1 + over, vb, y + rh), F.pt(u0 - over, vb, y + rh)]
                nn = (F.nx * sd * 0.6, 0.8, F.nz * sd * 0.6)
                B.quad(ROOF, q if sd < 0 else q[::-1], nn, col, None, True)
                B.quad(ROOF, q[::-1] if sd < 0 else q, (-nn[0], -0.8, -nn[2]), shade(col, -28), None, True)
            for (ua, sd) in ((u0 - over * 0.3, -1), (u1 + over * 0.3, 1)):                          # empenas
                B.tri(PLASTER, F.pt(ua, v0, y), F.pt(ua, v1, y), F.pt(ua, vm, y + rh - 0.1), (F.tx * sd, 0, F.tz * sd), TRIM if trim else col, None, True)
        else:
            um = (u0 + u1) / 2
            for (ua, ub, sd) in ((u0 - over, um, -1), (u1 + over, um, 1)):
                q = [F.pt(ua, v0 - over, y - 0.1), F.pt(ua, v1 + over, y - 0.1), F.pt(ub, v1 + over, y + rh), F.pt(ub, v0 - over, y + rh)]
                nn = (F.tx * sd * 0.6, 0.8, F.tz * sd * 0.6)
                B.quad(ROOF, q if sd > 0 else q[::-1], nn, col, None, True)
                B.quad(ROOF, q[::-1] if sd > 0 else q, (-nn[0], -0.8, -nn[2]), shade(col, -28), None, True)
            for (va, sd) in ((v0 - over * 0.3, -1), (v1 + over * 0.3, 1)):
                B.tri(PLASTER, F.pt(u0, va, y), F.pt(u1, va, y), F.pt(um, va, y + rh - 0.1), (F.nx * sd, 0, F.nz * sd), TRIM if trim else col, None, True)

    def hip_roof(self, F, u0, u1, v0, v1, y, rh, col, over=0.5):
        B = self.B; um, vm = (u0 + u1) / 2, (v0 + v1) / 2
        inset = min((u1 - u0), (v1 - v0)) * 0.28
        r0, r1 = (u0 + inset, u1 - inset), (v0 + inset, v1 - inset)
        c = [F.pt(u0 - over, v0 - over, y - 0.1), F.pt(u1 + over, v0 - over, y - 0.1), F.pt(u1 + over, v1 + over, y - 0.1), F.pt(u0 - over, v1 + over, y - 0.1)]
        t = [F.pt(r0[0], r1[0] * 0 + r1[0] if False else r1[0], y + rh), F.pt(r0[1], r1[0], y + rh), F.pt(r0[1], r1[1], y + rh), F.pt(r0[0], r1[1], y + rh)]
        t = [F.pt(r0[0], r1[0], y + rh), F.pt(r0[1], r1[0], y + rh), F.pt(r0[1], r1[1], y + rh), F.pt(r0[0], r1[1], y + rh)]
        t = [F.pt(u0 + inset, v0 + inset, y + rh), F.pt(u1 - inset, v0 + inset, y + rh), F.pt(u1 - inset, v1 - inset, y + rh), F.pt(u0 + inset, v1 - inset, y + rh)]
        nrm = [(-F.nx, 0.8, -F.nz), (F.tx, 0.8, F.tz), (F.nx, 0.8, F.nz), (-F.tx, 0.8, -F.tz)]
        for k in range(4):
            q = [c[k], c[(k + 1) % 4], t[(k + 1) % 4], t[k]]
            B.quad(ROOF, q, nrm[k], col if k % 2 == 0 else shade(col, -12), None, True)
            B.quad(ROOF, q[::-1], (-nrm[k][0], -0.8, -nrm[k][2]), shade(col, -30), None, True)
        B.quad(ROOF, t, (0, 1, 0), shade(col, -6), None, True)

    def flat_roof(self, F, u0, u1, v0, v1, y, col=CONC, parapet=0.9, pcol=None, equip=True):
        B = self.B; pcol = pcol or shade(col, 12)
        B.quad(PLAIN, [F.pt(u0, v0, y), F.pt(u1, v0, y), F.pt(u1, v1, y), F.pt(u0, v1, y)], (0, 1, 0), CONC2, None, True)
        t = 0.3
        self.box(F, u0 - 0.1, u1 + 0.1, v0 - 0.1, v0 + t, y, y + parapet, pcol, PLASTER)
        self.box(F, u0 - 0.1, u1 + 0.1, v1 - t, v1 + 0.1, y, y + parapet, pcol, PLASTER)
        self.box(F, u0 - 0.1, u0 + t, v0 + t, v1 - t, y, y + parapet, pcol, PLASTER)
        self.box(F, u1 - t, u1 + 0.1, v0 + t, v1 - t, y, y + parapet, pcol, PLASTER)
        if equip:
            rnd = self.rnd
            for _ in range(rnd.choice((1, 2, 2, 3))):                                               # ar-condicionado / casa de maquinas
                uu = rnd.uniform(u0 + 1.5, u1 - 1.5); vv = rnd.uniform(v0 + 1.5, v1 - 1.5)
                self.box(F, uu - 0.6, uu + 0.6, vv - 0.5, vv + 0.5, y, y + 0.8, rgb('#C8CCD0'), METAL)
            if rnd.random() < 0.6:                                                                   # caixa d'agua
                uu = rnd.uniform(u0 + 2.2, u1 - 2.2); vv = rnd.uniform(v0 + 2.2, v1 - 2.2); x, z = F.xz(uu, vv)
                B.cyl(x, z, 0.95, y, y + 1.6, rgb('#5D88A8') if rnd.random() < 0.5 else rgb('#E8E8E8'), 10, PLAIN, True)
                B.cyl(x, z, 0.1, y + 1.6, y + 2.0, DARK, 6, METAL, True)

    def door(self, F, u, v, y, side, col, w=1.1, h=2.2):
        self.quad_v(F, u - w / 2 - 0.12, u + w / 2 + 0.12, v, y, y + h + 0.1, TRIM, side, PLAIN, 0.03)
        self.quad_v(F, u - w / 2, u + w / 2, v, y, y + h, col, side, PLAIN, 0.045)

    def awning(self, F, u0, u1, v, y, depth, col):
        B = self.B
        q = [F.pt(u0, v - 0.05, y), F.pt(u1, v - 0.05, y), F.pt(u1, v - depth, y - 0.5), F.pt(u0, v - depth, y - 0.5)]
        B.quad(PLAIN, q, (-F.nx * 0.5, 0.85, -F.nz * 0.5), col, None, True); B.quad(PLAIN, q[::-1], (F.nx * 0.5, -0.85, F.nz * 0.5), shade(col, -35), None, True)
        for (ua) in (u0, u1):
            B.quad(PLAIN, [F.pt(ua, v - 0.05, y), F.pt(ua, v - depth, y - 0.5), F.pt(ua, v - depth, y - 0.5 - 0.02), F.pt(ua, v - 0.05, y - 0.02)], (F.tx, 0, F.tz), shade(col, -20), None, True)

    def wall_fence(self, F, v, u0, u1, y, h, col, gate=None, solid=True):
        """muro/grade baixa paralela a rua (v fixo) com portao opcional (gate=(g0,g1))"""
        segs = [(u0, u1)] if not gate else [(u0, gate[0]), (gate[1], u1)]
        for a, b in segs:
            if b - a > 0.1: self.box(F, a, b, v - 0.1, v + 0.1, y, y + h, col, PLASTER)

    def tree(self, F, u, v, sp=None, sc=None):
        x, z = F.xz(u, v)
        self.trees.append([round(x, 1), round(z, 1), sp if sp is not None else self.rnd.choice((0, 1, 1, 3)), round(sc if sc else self.rnd.uniform(0.7, 1.15), 2), round(self.rnd.uniform(0, 6.28), 2), round(self.rnd.uniform(0, 1), 2)])

    def solid_rect(self, F, u0, u1, v0, v1, pad=0.2):
        a = F.xz((u0 + u1) / 2, (v0 + v1) / 2)
        # retangulo girado: centro, cos, sen do referencial do lote e retangulo local
        cx, cz = a
        hu, hv = (u1 - u0) / 2 + pad, (v1 - v0) / 2 + pad
        self.solids.append([round(cx, 2), round(cz, 2), round(F.tx, 4), round(F.tz, 4), round(-hu, 2), round(-hv, 2), round(hu, 2), round(hv, 2)])

    def foundation(self, F, u0, u1, v0, v1, y_base, y_floor):
        """soco de pedra do terreno ate o piso (lotes inclinados)"""
        ymin = min(self.sample(*F.xz(u, v)) for u in (u0, u1) for v in (v0, v1)) - 0.4
        if y_floor - ymin > 0.2: self.box(F, u0 - 0.05, u1 + 0.05, v0 - 0.05, v1 + 0.05, ymin, y_floor, CONC2, STONE, False)

    # ================================================================== volumes e fachadas genericas
    def block(self, F, u0, u1, v0, v1, yb, floors, fh, wall, wcol=GLASS, win_front=True, win_sides=True, win_back=True, gap=3.0, wide=1.3, high=1.4, sill=0.9, frame=True, base_h=0.0):
        y1 = yb + floors * fh
        self.box(F, u0, u1, v0, v1, yb, y1, wall, PLASTER, False)
        if win_front: self.windows_front(F, u0 + 0.9, u1 - 0.9, v0, yb, fh, floors, wcol, wide, high, sill, gap, frame, -1)
        if win_back: self.windows_front(F, u0 + 0.9, u1 - 0.9, v1, yb, fh, floors, wcol, wide, high, sill, gap * 1.1, frame, +1)
        if win_sides:
            self.windows_side(F, v0 + 0.9, v1 - 0.9, u0, yb, fh, floors, wcol, -1, high=high, sill=sill)
            self.windows_side(F, v0 + 0.9, v1 - 0.9, u1, yb, fh, floors, wcol, +1, high=high, sill=sill)
        return y1

    def ribbon_block(self, F, u0, u1, v0, v1, yb, floors, fh, wall, glass, bay=3.0, spandrel=None):
        """torre: andares com janelas em baias (vidro) e peitoril de cor diferente, nas 4 faces"""
        y1 = yb + floors * fh
        self.box(F, u0, u1, v0, v1, yb, y1, wall, PLASTER, False)
        sp = spandrel or shade(wall, -18)
        for fl in range(floors):
            ya = yb + fl * fh
            # peitoril
            for (a, b, v, sd, front) in ((u0, u1, v0, -1, True), (u0, u1, v1, 1, True)):
                self.quad_v(F, a + 0.15, b - 0.15, v, ya + 0.05, ya + fh * 0.38, sp, sd, PLASTER, 0.02)
            for (a, b, u, sd) in ((v0, v1, u0, -1), (v0, v1, u1, 1)):
                self.quad_u(F, a + 0.15, b - 0.15, u, ya + 0.05, ya + fh * 0.38, sp, sd, PLASTER, 0.02)
            nb = max(1, int((u1 - u0) / bay)); st = (u1 - u0) / nb
            for k in range(nb):
                ua = u0 + st * k + 0.18; ub = u0 + st * (k + 1) - 0.18
                self.quad_v(F, ua, ub, v0, ya + fh * 0.4, ya + fh * 0.88, glass, -1, PLAIN, 0.03)
                self.quad_v(F, ua, ub, v1, ya + fh * 0.4, ya + fh * 0.88, glass, +1, PLAIN, 0.03)
            nb = max(1, int((v1 - v0) / bay)); st = (v1 - v0) / nb
            for k in range(nb):
                va = v0 + st * k + 0.18; vb = v0 + st * (k + 1) - 0.18
                self.quad_u(F, va, vb, u0, ya + fh * 0.4, ya + fh * 0.88, glass, -1, PLAIN, 0.03)
                self.quad_u(F, va, vb, u1, ya + fh * 0.4, ya + fh * 0.88, glass, +1, PLAIN, 0.03)
        return y1

    def balconies(self, F, u0, u1, v, yb, fh, floors, col, every=2, side=-1, depth=1.3, start=1):
        """sacadas (laje + guarda-corpo) em andares alternados, nas baias pares"""
        n = max(1, int((u1 - u0) / 3.2)); st = (u1 - u0) / n
        for fl in range(start, floors):
            for k in range(0, n, every):
                ua = u0 + st * k + 0.4; ub = u0 + st * (k + 1) - 0.4
                y = yb + fl * fh
                vv = v + side * depth
                self.box(F, ua, ub, min(v, vv), max(v, vv), y - 0.15, y, col, PLASTER)
                self.box(F, ua, ub, min(vv, vv - side * 0.08), max(vv, vv + side * 0.08), y, y + 1.0, shade(col, -10) if True else col, METAL, True)

    def shop_front(self, F, u0, u1, v, yb, h, glass, awn):
        n = max(1, int((u1 - u0) / 3.4)); st = (u1 - u0) / n
        for k in range(n):
            ua = u0 + st * k + 0.25; ub = u0 + st * (k + 1) - 0.25
            self.quad_v(F, ua, ub, v, yb + 0.35, yb + h, glass, -1, PLAIN, 0.03)
        self.awning(F, u0 + 0.1, u1 - 0.1, v, yb + h + 0.25, 1.4, awn)

    # ================================================================== construcoes
    def garden_common(self, F, yb, sf, ss, trees=2, gate_u=None):
        """muro frontal baixo + arvores"""
        w = F.w
        sp = getattr(self, 'cur', None) or {}
        if sp.get('yard'):
            self.yard_fence(F, yb, sp, sf)
            if sp.get('front') == 'picket':
                g0 = gate_u if gate_u is not None else w * 0.3
                for (a, b) in ((0.3, g0 - 0.7), (g0 + 0.7, w - 0.3)):
                    if b - a > 0.3:
                        self.box(F, a, b, 0.35, 0.45, yb + 0.25, yb + 0.85, TRIM, WOOD)
                        self.box(F, a, b, 0.33, 0.47, yb - 0.05, yb + 0.12, TRIM, WOOD)
            for _ in range(trees):
                self.tree(F, self.rnd.uniform(1.5, w - 1.5), self.rnd.uniform(1.2, max(1.6, sf - 1.0)) if self.rnd.random() < 0.5 else self.rnd.uniform(F.d - 6, F.d - 2))
            return
        wc = self.rnd.choice((TRIM, rgb('#E6D5C3'), rgb('#B8B2A6'), rgb('#C9B79C')))
        if self.rnd.random() < 0.7:
            g0 = gate_u if gate_u is not None else w / 2
            self.wall_fence(F, 0.4, 0.4, w - 0.4, yb - 0.1, 0.9, wc, (g0 - 1.5, g0 + 1.5))
        for _ in range(trees):
            side = self.rnd.choice((0, 1))
            self.tree(F, self.rnd.uniform(1.0, w - 1.0), self.rnd.uniform(1.5, max(2.0, sf - 0.5)) if side == 0 else self.rnd.uniform(F.d - 5, F.d - 1.5))

    def yard_fence(self, F, yb, sp, sf):
        """quintal cercado (bairro americano): cerca alta de madeira nas laterais (do meio da casa para tras) e no fundo"""
        w, d = F.w, F.d; col = sp.get('fcol', rgb('#B08A5E')); h = 1.8
        v0 = min(d - 4.0, sf + 6.0)
        if d - v0 < 3: return
        back = d - (sf + 13.0)
        if back > 7.5 and w > 11 and self.rnd.random() < 0.6:                                     # edicula / garagem de fundo
            eu0 = self.rnd.choice((0.8, w - 0.8 - 5.0)); ev1 = d - 0.9; ev0 = ev1 - min(5.5, back - 2.0)
            wc = self.rnd.choice((rgb('#E9E4D8'), rgb('#D8CBB4'), rgb('#C9B79C'), rgb('#B5654A')))
            self.box(F, eu0, eu0 + 5.0, ev0, ev1, yb, yb + 2.7, wc, PLASTER, False)
            self.gable_roof(F, eu0, eu0 + 5.0, ev0, ev1, yb + 2.7, 1.1, self.rnd.choice(ROOFS), ridge_u=False, over=0.3)
            self.solid_rect(F, eu0, eu0 + 5.0, ev0, ev1)
        self.box(F, w - 0.18, w - 0.04, v0, d - 0.1, yb - 0.05, yb + h, col, WOOD)                 # lateral direita
        if sp.get('first'): self.box(F, 0.04, 0.18, v0, d - 0.1, yb - 0.05, yb + h, col, WOOD)     # primeira do quarteirao: esquerda tambem
        self.box(F, 0.04, w - 0.04, d - 0.24, d - 0.1, yb - 0.05, yb + h, col, WOOD)              # fundo
        self.box(F, 0.04, w - 0.04, d - 0.27, d - 0.23, yb + h - 0.12, yb + h - 0.02, shade(col, -25), WOOD, False)

    def drive(self, F, u, w, vlen, y):
        B = self.B
        q = [F.pt(u - w / 2, 0.0, y + 0.03), F.pt(u + w / 2, 0.0, y + 0.03), F.pt(u + w / 2, vlen, y + 0.03), F.pt(u - w / 2, vlen, y + 0.03)]
        B.quad(PAVER, q, (0, 1, 0), PAVE, None, True)

    def casa_terrea(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        ss = sp.get('ss') or rnd.uniform(1.8, 3.0); sf = sp.get('sf') or rnd.uniform(4.0, 6.5); df = min(rnd.uniform(11.0, 14.5), d - sf - 6.0 if d > sf + 18 else d - sf - 3.0)
        if df < 6: return False
        u0, u1 = ss, w - ss; v0, v1 = sf, sf + df
        gar = rnd.random() < 0.8 and (u1 - u0) > 9
        wall = sp['wall']; roof = sp['roof']
        self.foundation(F, u0, u1, v0, v1, yb, yb + 0.25)
        y1 = self.block(F, u0, u1, v0, v1, yb + 0.25, 1, 2.9, wall, sp['glass'], gap=3.2)
        if rnd.random() < 0.5: self.hip_roof(F, u0, u1, v0, v1, y1, 1.6 + (u1 - u0) * 0.05, roof)
        else: self.gable_roof(F, u0, u1, v0, v1, y1, 1.9, roof, ridge_u=True)
        du = u0 + 2.0 if not gar else u1 - 2.5 - 3.3
        self.door(F, (u0 + (u1 - u0) * 0.3) if gar else (u0 + u1) / 2, v0, yb + 0.25, -1, sp['door'])
        # alpendre
        pu0, pu1 = (u0 + 1.0, u0 + (u1 - u0) * 0.55) if gar else (u0 + 1.5, u1 - 1.5)
        self.box(F, pu0, pu1, v0 - 2.0, v0, yb, yb + 0.25, CONC, PLASTER)
        self.box(F, pu0, pu1, v0 - 2.2, v0 - 1.9, yb + 2.6, yb + 2.85, TRIM, PLASTER)
        for uu in (pu0 + 0.15, pu1 - 0.15):
            x, z = F.xz(uu, v0 - 2.0); self.B.cyl(x, z, 0.1, yb + 0.25, yb + 2.65, TRIM, 6, PLASTER, True)
        # garagem
        if gar:
            ga0, ga1 = u1 - 3.8 - 0.3, u1 - 0.3
            self.quad_v(F, ga0, ga1, v0, yb + 0.25, yb + 2.3, rgb('#8A8F96'), -1, METAL, 0.04)
            self.drive(F, (ga0 + ga1) / 2, 3.4, v0 - 0.0, yb + 0.1)
        self.garden_common(F, yb, sf, ss, 2)
        self.solid_rect(F, u0, u1, v0, v1)
        return True

    def sobrado(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        ss = sp.get('ss') or rnd.uniform(1.5, 2.6); sf = sp.get('sf') or rnd.uniform(3.5, 5.5); df = min(rnd.uniform(11.0, 14.5), d - sf - 6.0 if d > sf + 18 else d - sf - 3.0)
        if df < 7: return False
        u0, u1 = ss, w - ss; v0, v1 = sf, sf + df
        self.foundation(F, u0, u1, v0, v1, yb, yb + 0.25)
        y1 = self.block(F, u0, u1, v0, v1, yb + 0.25, 2, 2.85, sp['wall'], sp['glass'], gap=3.0)
        self.gable_roof(F, u0, u1, v0, v1, y1, 2.2, sp['roof'], ridge_u=rnd.random() < 0.6)
        self.door(F, u0 + (u1 - u0) * 0.28, v0, yb + 0.25, -1, sp['door'])
        # sacada no andar de cima
        bu0, bu1 = u0 + (u1 - u0) * 0.45, u1 - 0.8
        y = yb + 0.25 + 2.85
        self.box(F, bu0, bu1, v0 - 1.3, v0, y - 0.15, y, CONC, PLASTER)
        self.box(F, bu0, bu1, v0 - 1.38, v0 - 1.3, y, y + 1.0, TRIM, METAL, True)
        self.box(F, bu0, bu0 + 0.08, v0 - 1.3, v0, y, y + 1.0, TRIM, METAL); self.box(F, bu1 - 0.08, bu1, v0 - 1.3, v0, y, y + 1.0, TRIM, METAL)
        self.quad_v(F, bu0 + 0.5, bu1 - 0.5, v0, y + 0.2, y + 2.2, sp['glass'], -1, PLAIN, 0.04)
        if rnd.random() < 0.5:                                                          # garagem integrada
            self.quad_v(F, u0 + 0.5, u0 + 3.9, v0, yb + 0.25, yb + 2.3, rgb('#8A8F96'), -1, METAL, 0.04); self.drive(F, u0 + 2.2, 3.4, v0, yb + 0.1)
        if rnd.random() < 0.4:                                                          # chamine
            self.box(F, u1 - 1.8, u1 - 1.1, v0 + 2, v0 + 2.7, y1, y1 + 2.8, rgb('#A5614A'), PLASTER)
        self.garden_common(F, yb, sf, ss, 2)
        self.solid_rect(F, u0, u1, v0, v1)
        return True

    def casa_moderna(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        ss = sp.get('ss') or rnd.uniform(2.0, 3.2); sf = sp.get('sf') or rnd.uniform(5.0, 7.5); df = min(rnd.uniform(10.0, 14.0), d - sf - 3.5)
        if df < 8: return False
        u0, u1 = ss, w - ss; v0, v1 = sf, sf + df
        wall = rnd.choice((rgb('#F4F4F2'), rgb('#E7E5DF'), rgb('#CFCFCB'), rgb('#3F4247'), rgb('#D8CBB4')))
        self.foundation(F, u0, u1, v0, v1, yb, yb + 0.25)
        yb0 = yb + 0.25
        # volume terreo mais largo e volume superior recuado/balanco
        self.box(F, u0, u1, v0, v1, yb0, yb0 + 3.0, wall, PLASTER, False)
        su0 = u0 + (u1 - u0) * rnd.choice((0.0, 0.3)); su1 = u1 - (u1 - u0) * rnd.choice((0.0, 0.25))
        sv0 = v0 - 1.4; sv1 = v1 - 3.0
        wall2 = rnd.choice((rgb('#F4F4F2'), rgb('#C9A57A'), rgb('#8D6E50'), rgb('#E7E5DF')))
        self.box(F, su0, su1, sv0, sv1, yb0 + 3.0, yb0 + 5.9, wall2, WOOD if wall2 in (rgb('#C9A57A'), rgb('#8D6E50')) else PLASTER, False)
        self.box(F, u0 - 0.3, u1 + 0.3, v0 - 0.3, v1 + 0.3, yb0 + 3.0, yb0 + 3.25, TRIM, PLASTER)                  # laje
        self.box(F, su0 - 0.3, su1 + 0.3, sv0 - 0.3, sv1 + 0.3, yb0 + 5.9, yb0 + 6.15, TRIM, PLASTER)
        # envidracamento: faixas largas
        self.quad_v(F, u0 + 0.8, u0 + (u1 - u0) * 0.62, v0, yb0 + 0.3, yb0 + 2.7, GLASS_D, -1, PLAIN, 0.04)
        self.quad_v(F, su0 + 0.8, su1 - 0.8, sv0, yb0 + 3.5, yb0 + 5.4, GLASS_D, -1, PLAIN, 0.04)
        self.quad_u(F, v0 + 1.0, v1 - 1.0, u1, yb0 + 0.6, yb0 + 2.5, GLASS_D, +1, PLAIN, 0.04)
        self.door(F, u0 + (u1 - u0) * 0.72, v0, yb0, -1, DARK, 1.2, 2.3)
        self.quad_v(F, u1 - 3.7, u1 - 0.4, v0, yb0, yb0 + 2.3, rgb('#707680'), -1, METAL, 0.05)                       # garagem
        self.drive(F, u1 - 2.0, 3.3, v0, yb + 0.1)
        # piscina
        if rnd.random() < 0.55 and d - v1 > 5:
            pv0, pv1 = v1 + 1.2, min(v1 + 6.5, d - 1.5); pu0, pu1 = u0 + 1.0, u0 + min(6.5, (u1 - u0) * 0.5)
            self.B.quad(PLAIN, [F.pt(pu0, pv0, yb + 0.05), F.pt(pu1, pv0, yb + 0.05), F.pt(pu1, pv1 if False else pv1, yb + 0.05), F.pt(pu0, pv1 if False else pv1, yb + 0.05)] if False else [F.pt(pu0, pv0, yb + 0.06), F.pt(pu1, pv0, yb + 0.06), F.pt(pu1, pv1 if pv1 > pv0 else pv0 + 3, yb + 0.06), F.pt(pu0, pv1 if pv1 > pv0 else pv0 + 3, yb + 0.06)], (0, 1, 0), rgb('#56B4D3'), None, True)
        self.flat_roof(F, su0, su1, sv0, sv1, yb0 + 6.15, parapet=0.0, equip=True) if False else None
        self.garden_common(F, yb, sf, ss, 3)
        self.solid_rect(F, u0, u1, min(v0, sv0), v1)
        return True

    def colonial(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        ss = sp.get('ss') or rnd.uniform(2.0, 3.0); sf = sp.get('sf') or rnd.uniform(5.0, 7.0); df = min(rnd.uniform(10.0, 13.0), d - sf - 3.0)
        if df < 8: return False
        u0, u1 = ss, w - ss; v0, v1 = sf, sf + df
        floors = rnd.choice((1, 2)); fh = 3.0
        self.foundation(F, u0, u1, v0, v1, yb, yb + 0.45)
        yb0 = yb + 0.45
        y1 = self.block(F, u0, u1, v0, v1, yb0, floors, fh, sp['wall'], sp['glass'], gap=3.4, wide=1.1, high=1.6, frame=True)
        self.gable_roof(F, u0, u1, v0, v1, y1, 2.6, sp['roof'], ridge_u=False)
        # varanda com colunas e frontao
        pu0, pu1 = u0 + (u1 - u0) * 0.2, u1 - (u1 - u0) * 0.2
        self.box(F, pu0, pu1, v0 - 2.6, v0, yb, yb0, CONC, STONE)
        n = max(2, int((pu1 - pu0) / 2.6))
        for k in range(n + 1):
            x, z = F.xz(pu0 + 0.3 + (pu1 - pu0 - 0.6) * k / n, v0 - 2.4); self.B.cyl(x, z, 0.16, yb0, yb0 + fh * floors * 0.92, TRIM, 8, PLASTER, True)
        yy = yb0 + fh * floors * 0.92
        self.box(F, pu0 - 0.2, pu1 + 0.2, v0 - 2.8, v0, yy, yy + 0.35, TRIM, PLASTER)
        self.B.tri(PLASTER, F.pt(pu0 - 0.3, v0 - 2.8, yy + 0.35), F.pt(pu1 + 0.3, v0 - 2.8, yy + 0.35), F.pt((pu0 + pu1) / 2, v0 - 2.8, yy + 1.5), (-F.nx, 0, -F.nz), TRIM, None, True)
        self.door(F, (pu0 + pu1) / 2, v0, yb0, -1, sp['door'], 1.3, 2.4)
        for k in (-1, 1):                                                              # janelas com venezianas
            for fl in range(floors):
                uc = (pu0 + pu1) / 2 + k * (pu1 - pu0) * 0.33; ya = yb0 + fl * fh + 0.9
                for sgn in (-1, 1): self.quad_v(F, uc + sgn * 0.7 - 0.22, uc + sgn * 0.7 + 0.22, v0, ya, ya + 1.6, sp['shutter'], -1, PLAIN, 0.045)
        for sg in (-1, 1):                                                             # degraus
            pass
        self.box(F, (pu0 + pu1) / 2 - 1.2, (pu0 + pu1) / 2 + 1.2, v0 - 3.2, v0 - 2.6, yb, yb0 - 0.2, CONC, STONE)
        self.garden_common(F, yb, sf, ss, 3, gate_u=(pu0 + pu1) / 2)
        self.solid_rect(F, u0, u1, v0 - 2.8, v1)
        return True

    def geminadas(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        n = 2 if w < 20 else rnd.choice((2, 3)); ss = 0.6; sf = sp.get('sf') or rnd.uniform(2.5, 4.0); df = min(rnd.uniform(9.0, 12.0), d - sf - 2.5)
        if df < 7: return False
        uw = (w - 2 * ss) / n
        cols = rnd.sample(WALLS_BRIGHT + WALLS_WARM, min(3, n)) if rnd.random() < 0.8 else [sp['wall']] * n
        for k in range(n):
            u0 = ss + uw * k + 0.05; u1 = ss + uw * (k + 1) - 0.05
            c = cols[k % len(cols)]
            self.foundation(F, u0, u1, sf, sf + df, yb, yb + 0.25)
            y1 = self.block(F, u0, u1, sf, sf + df, yb + 0.25, 2, 2.8, c, sp['glass'], gap=2.6, wide=1.1, high=1.3, win_sides=False)
            # laje plana inclinada (agua unica) com platibanda frontal
            self.B.quad(ROOF, [F.pt(u0 - 0.2, sf - 0.4, y1 + 0.35), F.pt(u1 + 0.2, sf - 0.4, y1 + 0.35), F.pt(u1 + 0.2, sf + df + 0.3, y1 - 0.1), F.pt(u0 - 0.2, sf + df + 0.3, y1 - 0.1)], (0, 1, 0), sp['roof'], None, True)
            self.box(F, u0, u1, sf - 0.35, sf - 0.1, y1, y1 + 0.5, shade(c, 12), PLASTER)
            self.door(F, u0 + (u1 - u0) * 0.3, sf, yb + 0.25, -1, rnd.choice(DOOR), 1.0, 2.1)
            self.quad_v(F, u0 + (u1 - u0) * 0.58, u1 - 0.5, sf, yb + 0.25, yb + 2.2, rgb('#8A8F96'), -1, METAL, 0.04) if rnd.random() < 0.4 else None
            if k:
                self.box(F, u0 - 0.05, u0 + 0.05, sf, sf + df, yb + 0.25, y1 + 0.3, shade(c, -30), PLASTER)
        self.wall_fence(F, 0.5, 0.2, w - 0.2, yb - 0.1, 0.7, rgb('#D8CDB8'), (w / 2 - 1.2, w / 2 + 1.2)) if rnd.random() < 0.6 else None
        self.solid_rect(F, ss, w - ss, sf, sf + df)
        return True

    def mansao(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        ss = sp.get('ss') or rnd.uniform(3.5, 5.5); sf = sp.get('sf') or rnd.uniform(7.0, 10.0)
        df = min(rnd.uniform(11.0, 15.0), d - sf - 4.0)
        if df < 9 or w < 18: return False
        u0, u1 = ss, w - ss; v0, v1 = sf, sf + df
        self.foundation(F, u0, u1, v0, v1, yb, yb + 0.5)
        yb0 = yb + 0.5; fh = 3.4
        y1 = self.block(F, u0, u1, v0, v1, yb0, 2, fh, sp['wall'], sp['glass'], gap=3.6, wide=1.5, high=1.9)
        # ala lateral mais baixa
        wu = (u1 - u0) * 0.32
        y2 = self.block(F, u0 - wu * 0.0, u0 + wu, v0 - 4.0, v0 + 1.0, yb0, 1, fh, shade(sp['wall'], -6), sp['glass'], gap=3.3)
        self.hip_roof(F, u0 + wu * 0.0, u0 + wu, v0 - 4.0, v0 + 1.0, y2, 1.6, sp['roof'])
        self.hip_roof(F, u0, u1, v0, v1, y1, 2.8, sp['roof'], over=0.8)
        # portico com colunas altas
        pu = (u0 + u1) / 2 + (u1 - u0) * 0.1; pw = 6.0
        self.box(F, pu - pw / 2, pu + pw / 2, v0 - 3.0, v0, yb, yb0, CONC, STONE)
        for k in range(4):
            x, z = F.xz(pu - pw / 2 + 0.4 + (pw - 0.8) * k / 3, v0 - 2.7); self.B.cyl(x, z, 0.28, yb0, yb0 + 2 * fh - 0.2, TRIM, 10, PLASTER, True)
        self.box(F, pu - pw / 2 - 0.3, pu + pw / 2 + 0.3, v0 - 3.3, v0, yb0 + 2 * fh - 0.2, yb0 + 2 * fh + 0.3, TRIM, PLASTER)
        self.door(F, pu, v0, yb0, -1, rnd.choice(DOOR), 1.8, 2.8)
        # muro alto com portao + pilares, jardim, piscina, quadra de entrada
        self.wall_fence(F, 0.6, 0.0, w, yb - 0.1, 2.0, rgb('#CFC6B4'), (w / 2 - 2.4, w / 2 + 2.4))
        for sg in (-1, 1): self.box(F, w / 2 + sg * 2.6 - 0.35, w / 2 + sg * 2.6 + 0.35, 0.3, 1.0, yb - 0.1, yb + 2.6, TRIM, PLASTER)
        self.quad_v(F, w / 2 - 2.3, w / 2 + 2.3, 0.6, yb, yb + 1.9, DARK, -1, METAL, 0.04)
        if d - v1 > 6:
            pv0, pv1 = v1 + 1.5, min(v1 + 9.0, d - 1.5); pu0, pu1 = u0 + 2, u0 + min(9.0, (u1 - u0) * 0.6)
            self.B.quad(PLAIN, [F.pt(pu0 - 0.4, pv0 - 0.4, yb + 0.05), F.pt(pu1 + 0.4, pv0 - 0.4, yb + 0.05), F.pt(pu1 + 0.4, pv1 + 0.4, yb + 0.05), F.pt(pu0 - 0.4, pv1 + 0.4, yb + 0.05)], (0, 1, 0), rgb('#E7E1D3'), None, True)
            self.B.quad(PLAIN, [F.pt(pu0, pv0, yb + 0.08), F.pt(pu1, pv0, yb + 0.08), F.pt(pu1, pv1, yb + 0.08), F.pt(pu0, pv1, yb + 0.08)], (0, 1, 0), rgb('#4FB3D6'), None, True)
        for _ in range(5): self.tree(F, rnd.uniform(1.5, w - 1.5), rnd.choice((rnd.uniform(1.5, sf - 1.2), rnd.uniform(v1 + 1, d - 1.2))))
        self.drive(F, w / 2, 4.2, v0 - 3.0, yb + 0.1)
        self.solid_rect(F, u0, u1, v0 - 3.0, v1)
        return True

    def predio_apto(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        ss = sp.get('ss') or rnd.uniform(2.2, 3.5); sf = sp.get('sf') or rnd.uniform(5.0, 8.0); df = min(rnd.uniform(14.0, 20.0), d - sf - 3.0)
        if df < 10 or w < 14: return False
        u0, u1 = ss, w - ss; v0, v1 = sf, sf + df
        fl = sp['floors']; fh = 3.0; yb0 = yb + 0.6
        self.foundation(F, u0, u1, v0, v1, yb, yb0)
        wall = sp['wall']
        y1 = self.block(F, u0, u1, v0, v1, yb0 + 3.4, fl - 1, fh, wall, sp['glass'], gap=3.0, wide=1.5, high=1.5, sill=0.8)
        # terreo (pilotis/lobby): vidro e entrada com marquise
        self.box(F, u0, u1, v0, v1, yb0, yb0 + 3.4, shade(wall, -10), PLASTER, False)
        self.quad_v(F, u0 + 1.5, u0 + (u1 - u0) * 0.45, v0, yb0 + 0.3, yb0 + 3.0, GLASS_D, -1, PLAIN, 0.04)
        self.door(F, u0 + (u1 - u0) * 0.65, v0, yb0, -1, rgb('#3B3B3B'), 2.0, 2.6)
        self.awning(F, u0 + (u1 - u0) * 0.5, u0 + (u1 - u0) * 0.8, v0, yb0 + 3.1, 2.2, rnd.choice(WALLS_BRIGHT))
        self.quad_v(F, u0 + (u1 - u0) * 0.84, u1 - 0.8, v0, yb0, yb0 + 2.3, rgb('#707680'), -1, METAL, 0.05)               # garagem
        self.balconies(F, u0 + 0.4, u1 - 0.4, v0, yb0 + 3.4, fh, fl - 1, shade(wall, 10), every=2, side=-1, start=0)
        self.flat_roof(F, u0, u1, v0, v1, y1, parapet=0.9, pcol=shade(wall, 6))
        # cobertura recuada com casinha de maquinas
        self.box(F, u0 + 3, u1 - 3, v0 + 3, v1 - 3, y1, y1 + 2.8, shade(wall, -8), PLASTER)
        # jardim frontal, muro, arvores
        self.wall_fence(F, 0.5, 0.2, w - 0.2, yb - 0.1, 1.0, TRIM, (w * 0.62 - 1.4, w * 0.62 + 1.4))
        self.drive(F, w * 0.9, 3.2, v0, yb + 0.1)
        for _ in range(3): self.tree(F, rnd.uniform(1.5, w - 1.5), rnd.uniform(1.5, sf - 1.0))
        self.solid_rect(F, u0, u1, v0, v1)
        return True

    def torre(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        fl = sp['floors']; fh = 3.2
        ss = sp.get('ss') or rnd.uniform(1.0, 2.2); sf = sp.get('sf') or rnd.uniform(1.5, 3.5)
        pv1 = min(d - 2.0, sf + rnd.uniform(26.0, 34.0))
        if pv1 - sf < 16 or w < 20: return False
        u0, u1 = ss, w - ss; v0 = sf
        yb0 = yb + 0.5
        self.foundation(F, u0, u1, v0, pv1, yb, yb0)
        glass = sp['glass']; wall = sp['wall']
        # podio de 2 andares (comercio/lobby)
        self.box(F, u0, u1, v0, pv1, yb0, yb0 + 7.0, shade(wall, -6), PLASTER, False)
        self.quad_v(F, u0 + 1.0, u1 - 1.0, v0, yb0 + 0.4, yb0 + 3.4, GLASS_D, -1, PLAIN, 0.04)
        self.quad_v(F, u0 + 1.0, u1 - 1.0, v0, yb0 + 4.0, yb0 + 6.4, glass, -1, PLAIN, 0.04)
        self.awning(F, u0 + 1.0, u1 - 1.0, v0, yb0 + 3.7, 2.4, sp['accent'])
        self.door(F, w / 2, v0, yb0, -1, rgb('#303030'), 2.4, 2.8)
        self.flat_roof(F, u0, u1, v0, pv1, yb0 + 7.0, parapet=1.0, equip=False)
        # torre: ate 3 blocos com recuos
        ty = yb0 + 7.0; tiers = 1 if fl < 12 else (2 if fl < 20 else 3)
        fl_left = fl; tu0, tu1, tv0, tv1 = u0 + 2.5, u1 - 2.5, v0 + 3.0, pv1 - 3.0
        for t in range(tiers):
            nfl = max(3, int(fl_left * (0.55 if t < tiers - 1 else 1.0)))
            top = self.ribbon_block(F, tu0, tu1, tv0, tv1, ty, nfl, fh, wall, glass, bay=rnd.choice((2.8, 3.2, 3.6)))
            # faixas verticais (aletas) laterais para dar volume
            if rnd.random() < 0.7:
                for k in range(3):
                    uc = tu0 + (tu1 - tu0) * (k + 0.5) / 3
                    self.box(F, uc - 0.12, uc + 0.12, tv0 - 0.25, tv0, ty, top, shade(wall, 14), PLASTER, False)
            ty = top; fl_left -= nfl
            if t < tiers - 1:
                self.flat_roof(F, tu0, tu1, tv0, tv1, ty, parapet=0.7, equip=False)
                tu0 += 2.2; tu1 -= 2.2; tv0 += 2.6; tv1 -= 2.6
        # coroa: casa de maquinas + antena
        self.flat_roof(F, tu0, tu1, tv0, tv1, ty, parapet=0.8, pcol=sp['accent'])
        self.box(F, tu0 + 2, tu1 - 2, tv0 + 2, tv1 - 2, ty, ty + 3.2, sp['accent'], PLASTER)
        x, z = F.xz((tu0 + tu1) / 2, (tv0 + tv1) / 2); self.B.cyl(x, z, 0.1, ty + 3.2, ty + 3.2 + rnd.uniform(5, 11), rgb('#E24A4A') if rnd.random() < 0.5 else DARK, 6, METAL, True)
        if sp.get('hotel'):                                                           # faixa colorida + piscina no podio
            self.box(F, u0 - 0.05, u1 + 0.05, v0 - 0.05, v0 + 0.3, yb0 + 6.2, yb0 + 7.0, sp['accent'], PLASTER)
            self.B.quad(PLAIN, [F.pt(u1 - 9, pv1 - 8, yb0 + 7.02), F.pt(u1 - 2.5, pv1 - 8, yb0 + 7.02), F.pt(u1 - 2.5, pv1 - 3.2, yb0 + 7.02), F.pt(u1 - 9, pv1 - 3.2, yb0 + 7.02)], (0, 1, 0), rgb('#4FB3D6'), None, True)
        self.drive(F, w * 0.85, 4.0, v0, yb + 0.1)
        for _ in range(2): self.tree(F, rnd.uniform(2, w - 2), rnd.uniform(0.8, max(1.0, v0 - 0.6)))
        self.solid_rect(F, u0, u1, v0, pv1)
        return True

    def comercial(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        fl = sp['floors']; fh = 3.1
        sf = sp.get('sf') or rnd.choice((0.5, 0.5, 1.5)); df = min(rnd.uniform(14.0, 22.0), d - sf - 2.5)
        if df < 9: return False
        u0, u1 = 0.4, w - 0.4; v0, v1 = sf, sf + df
        yb0 = yb + 0.25
        self.foundation(F, u0, u1, v0, v1, yb, yb0)
        wall = sp['wall']
        y1 = self.block(F, u0, u1, v0, v1, yb0 + 3.6, fl - 1, fh, wall, sp['glass'], gap=3.0, wide=1.7, high=1.4, win_sides=True)
        self.box(F, u0, u1, v0, v1, yb0, yb0 + 3.6, shade(wall, -8), PLASTER, False)
        self.shop_front(F, u0 + 0.4, u1 - 0.4, v0, yb0, 2.9, sp['glass'], sp['accent'])
        # placa/letreiro
        self.box(F, u0 + 1.0, u1 - 1.0, v0 - 0.15, v0, yb0 + 3.0, yb0 + 3.55, sp['sign'], PLAIN)
        self.flat_roof(F, u0, u1, v0, v1, y1, parapet=1.0, pcol=shade(wall, 8))
        if rnd.random() < 0.45: self.balconies(F, u0 + 0.5, u1 - 0.5, v0, yb0 + 3.6, fh, fl - 1, shade(wall, 10), every=2, side=-1, depth=1.0, start=0)
        self.solid_rect(F, u0, u1, v0, v1)
        return True

    def igreja(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        if w < 18 or d < 30: return False
        u0, u1 = 3.0, w - 3.0; v0 = 4.0; v1 = min(d - 3.0, v0 + 26.0)
        yb0 = yb + 0.5; self.foundation(F, u0, u1, v0, v1, yb, yb0)
        wall = rgb('#F3EEE2')
        self.box(F, u0, u1, v0, v1, yb0, yb0 + 8.0, wall, PLASTER, False)
        self.gable_roof(F, u0, u1, v0, v1, yb0 + 8.0, 4.0, rgb('#B5543A'), ridge_u=False, over=0.6)
        # torre do sino na frente
        tu0, tu1 = (u0 + u1) / 2 - 2.6, (u0 + u1) / 2 + 2.6
        self.box(F, tu0, tu1, v0 - 2.0, v0 + 3.2, yb0, yb0 + 17.0, wall, PLASTER, False)
        self.hip_roof(F, tu0, tu1, v0 - 2.0, v0 + 3.2, yb0 + 17.0, 7.0, rgb('#6B6F76'), over=0.3)
        x, z = F.xz((tu0 + tu1) / 2, v0 + 0.6); self.B.cyl(x, z, 0.08, yb0 + 24.0, yb0 + 27.0, rgb('#C9A24A'), 6, METAL, True)
        self.box(F, (tu0 + tu1) / 2 - 0.9, (tu0 + tu1) / 2 + 0.9, v0 - 2.05, v0 - 1.95, yb0 + 25.4, yb0 + 25.8, rgb('#C9A24A'), METAL)
        self.quad_v(F, (tu0 + tu1) / 2 - 0.8, (tu0 + tu1) / 2 + 0.8, v0 - 2.0, yb0 + 12.0, yb0 + 15.0, DARK, -1, PLAIN, 0.04)
        self.door(F, (tu0 + tu1) / 2, v0 - 2.0, yb0, -1, rgb('#5B3A29'), 2.6, 3.8)
        self.quad_v(F, u0 + 1.0, tu0 - 0.6, v0, yb0 + 2.2, yb0 + 6.2, rgb('#9C6FBF'), -1, PLAIN, 0.04); self.quad_v(F, tu1 + 0.6, u1 - 1.0, v0, yb0 + 2.2, yb0 + 6.2, rgb('#9C6FBF'), -1, PLAIN, 0.04)
        self.windows_side(F, v0 + 2, v1 - 2, u0, yb0, 8.0, 1, rgb('#9C6FBF'), -1, wide=1.4, high=4.0, sill=1.8, gap=4.5)
        self.windows_side(F, v0 + 2, v1 - 2, u1, yb0, 8.0, 1, rgb('#9C6FBF'), +1, wide=1.4, high=4.0, sill=1.8, gap=4.5)
        self.box(F, tu0 - 1.6, tu1 + 1.6, v0 - 5.0, v0 - 2.0, yb, yb0 - 0.15, CONC, STONE)                      # escadaria/adro
        for k in range(4): self.tree(F, rnd.uniform(1.5, w - 1.5), rnd.uniform(0.5, 2.5)) if k < 2 else self.tree(F, rnd.uniform(1.5, w - 1.5), rnd.uniform(v1 + 1, d - 1))
        self.solid_rect(F, u0, u1, v0 - 2.0, v1)
        return True

    def escola(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        if w < 24 or d < 28: return False
        u0, u1 = 2.5, w - 2.5; v0 = 5.0; v1 = v0 + 12.0
        yb0 = yb + 0.4; self.foundation(F, u0, u1, v0, v1, yb, yb0)
        wall = rnd.choice((rgb('#F2D675'), rgb('#9CC4E4'), rgb('#F3EEE2'), rgb('#EAA786')))
        y1 = self.block(F, u0, u1, v0, v1, yb0, 2, 3.4, wall, GLASS, gap=3.2, wide=1.9, high=1.7)
        self.flat_roof(F, u0, u1, v0, v1, y1, parapet=0.8, pcol=rgb('#E24A4A'))
        self.door(F, w / 2, v0, yb0, -1, rgb('#E24A4A'), 2.8, 2.8)
        self.awning(F, w / 2 - 3.5, w / 2 + 3.5, v0, yb0 + 3.0, 2.5, rgb('#E24A4A'))
        x, z = F.xz(w - 3.5, 2.5); self.B.cyl(x, z, 0.08, yb0, yb0 + 8.0, rgb('#E8E8E8'), 6, METAL, True)
        self.wall_fence(F, 0.6, 0.0, w, yb - 0.1, 1.6, rgb('#D8CDB8'), (w / 2 - 3, w / 2 + 3))
        # quadrinha no fundo
        cu0, cu1 = u0 + 2, u1 - 2; cv0, cv1 = v1 + 2.5, d - 1.5
        if cv1 - cv0 > 6: self.B.quad(PLAIN, [F.pt(cu0, cv0, yb + 0.06), F.pt(cu1, cv0, yb + 0.06), F.pt(cu1, cv1, yb + 0.06), F.pt(cu0, cv1, yb + 0.06)], (0, 1, 0), rgb('#E08A5C'), None, True)
        for _ in range(3): self.tree(F, rnd.uniform(1.5, w - 1.5), rnd.uniform(1.0, 4.0))
        self.solid_rect(F, u0, u1, v0, v1)
        return True

    def posto(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        if w < 20 or d < 24: return False
        B = self.B
        self.B.quad(PAVER, [F.pt(0.5, 0.2, yb + 0.04), F.pt(w - 0.5, 0.2, yb + 0.04), F.pt(w - 0.5, d - 0.5, yb + 0.04), F.pt(0.5, d - 0.5, yb + 0.04)], (0, 1, 0), rgb('#8E8F93'), None, True)
        cu0, cu1 = 3.0, w - 3.0; cv0, cv1 = 6.0, 15.0; ch = 5.0
        self.box(F, cu0, cu1, cv0, cv1, yb + ch, yb + ch + 0.7, sp['accent'], PLAIN)
        for (uu, vv) in ((cu0 + 0.8, cv0 + 0.8), (cu1 - 0.8, cv0 + 0.8), (cu0 + 0.8, cv1 - 0.8), (cu1 - 0.8, cv1 - 0.8)):
            x, z = F.xz(uu, vv); B.cyl(x, z, 0.2, yb, yb + ch, rgb('#E8E8E8'), 8, PLAIN, True)
        for k in range(4):
            uu = cu0 + (cu1 - cu0) * (k + 0.5) / 4; self.box(F, uu - 0.35, uu + 0.35, (cv0 + cv1) / 2 - 0.25, (cv0 + cv1) / 2 + 0.25, yb, yb + 1.5, sp['accent'], METAL)
        # loja de conveniencia
        su0, su1 = 3.0, min(w - 3.0, 3.0 + 12.0); sv0, sv1 = d - 9.5, d - 2.5
        y1 = self.block(F, su0, su1, sv0, sv1, yb, 1, 3.3, rgb('#F3EEE2'), GLASS, gap=3.0, wide=2.0, high=1.9, sill=0.5)
        self.quad_v(F, su0 + 0.8, su1 - 0.8, sv0, yb + 0.3, yb + 2.7, GLASS_D, -1, PLAIN, 0.04)
        self.flat_roof(F, su0, su1, sv0, sv1, y1, parapet=0.5, pcol=sp['accent'])
        x, z = F.xz(w - 2.0, 1.5); B.cyl(x, z, 0.15, yb, yb + 7.0, rgb('#C0C0C0'), 8, METAL, True); self.box(F, w - 3.2, w - 0.8, 1.2, 1.8, yb + 7.0, yb + 9.0, sp['accent'], PLAIN)
        self.solid_rect(F, su0, su1, sv0, sv1)
        self.solid_rect(F, cu0, cu1, cv0, cv1, 0.0) if False else None
        return True

    def mercado(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        if w < 22 or d < 28: return False
        u0, u1 = 2.0, w - 2.0; v0 = 11.0; v1 = min(d - 2.0, v0 + 18.0)
        B = self.B
        B.quad(PAVER, [F.pt(0.5, 0.2, yb + 0.04), F.pt(w - 0.5, 0.2, yb + 0.04), F.pt(w - 0.5, v0 - 0.3, yb + 0.04), F.pt(0.5, v0 - 0.3, yb + 0.04)], (0, 1, 0), rgb('#8E8F93'), None, True)
        for k in range(int((w - 3) / 2.8)):                                       # vagas pintadas
            uu = 1.8 + k * 2.8; B.quad(PLAIN, [F.pt(uu, 1.5, yb + 0.06), F.pt(uu + 0.1, 1.5, yb + 0.06), F.pt(uu + 0.1, 6.0, yb + 0.06), F.pt(uu, 6.0, yb + 0.06)], (0, 1, 0), rgb('#F2F2F2'), None, True)
        yb0 = yb + 0.3
        y1 = self.block(F, u0, u1, v0, v1, yb0, 1, 5.2, sp['wall'], GLASS, win_front=False, win_sides=False, win_back=False)
        self.quad_v(F, u0 + 2, u1 - 2, v0, yb0 + 0.4, yb0 + 3.2, GLASS_D, -1, PLAIN, 0.04)
        self.box(F, u0 + 1.0, u1 - 1.0, v0 - 0.2, v0, yb0 + 3.6, yb0 + 4.9, sp['sign'], PLAIN)
        self.awning(F, u0 + 1.0, u1 - 1.0, v0, yb0 + 3.4, 2.4, sp['accent'])
        self.flat_roof(F, u0, u1, v0, v1, y1, parapet=0.7, pcol=sp['accent'])
        self.solid_rect(F, u0, u1, v0, v1)
        return True

    def galpao(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        if w < 20 or d < 26: return False
        u0, u1 = 2.5, w - 2.5; v0 = 4.0; v1 = min(d - 2.5, v0 + 22.0)
        yb0 = yb + 0.3
        self.foundation(F, u0, u1, v0, v1, yb, yb0)
        self.box(F, u0, u1, v0, v1, yb0, yb0 + 6.0, rnd.choice((rgb('#C9CDD2'), rgb('#B9C4A8'), rgb('#D6B98C'))), METAL, False)
        self.gable_roof(F, u0, u1, v0, v1, yb0 + 6.0, 2.4, rgb('#8C8F95'), ridge_u=True, over=0.3, trim=False)
        for k in range(2):
            uc = u0 + (u1 - u0) * (0.28 + 0.44 * k); self.quad_v(F, uc - 2.2, uc + 2.2, v0, yb0, yb0 + 4.6, rnd.choice((rgb('#3F6EA5'), rgb('#B5543A'), rgb('#2E7D5B'))), -1, METAL, 0.05)
        self.quad_v(F, u0 + 1.0, u1 - 1.0, v0, yb0 + 5.0, yb0 + 5.7, GLASS_D, -1, PLAIN, 0.03)
        B = self.B
        B.quad(PAVER, [F.pt(0.5, 0.2, yb + 0.04), F.pt(w - 0.5, 0.2, yb + 0.04), F.pt(w - 0.5, v0, yb + 0.04), F.pt(0.5, v0, yb + 0.04)], (0, 1, 0), rgb('#8E8F93'), None, True)
        self.solid_rect(F, u0, u1, v0, v1)
        return True

    def pracinha(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        B = self.B; cu, cv = w / 2, min(d / 2, 16.0)
        q = [F.pt(1.0, 0.6, yb + 0.05), F.pt(w - 1.0, 0.6, yb + 0.05), F.pt(w - 1.0, d - 1.0, yb + 0.05), F.pt(1.0, d - 1.0, yb + 0.05)]
        B.quad(PLAIN, q, (0, 1, 0), rgb('#7CB05A'), None, True)
        for (a, b, c2, e) in ((cu - 1.2, 0.6, cu + 1.2, d - 1.0), (1.0, cv - 1.2, w - 1.0, cv + 1.2)):
            B.quad(PAVER, [F.pt(a, b, yb + 0.08), F.pt(c2, b, yb + 0.08), F.pt(c2, e if e > b + 3 else b + 2.4, yb + 0.08), F.pt(a, e if e > b + 3 else b + 2.4, yb + 0.08)], (0, 1, 0), rgb('#D8D2C4'), None, True)
        x, z = F.xz(cu, cv); B.cyl(x, z, 2.0, yb + 0.05, yb + 0.5, rgb('#CFCABF'), 14, STONE, True); B.cyl(x, z, 1.7, yb + 0.5, yb + 0.55, rgb('#6FB5D6'), 14, PLAIN, True)
        for (uu, vv, s) in ((cu - 2.6, cv, 1), (cu + 2.6, cv, -1)):
            xx, zz = F.xz(uu, vv); c4 = [F.xz(uu - 0.3, vv - 1.0), F.xz(uu + 0.3, vv - 1.0), F.xz(uu + 0.3, vv + 1.0), F.xz(uu - 0.3, vv + 1.0)]
            B.obox_pts(c4, yb + 0.45, yb + 0.55, rgb('#7A5A3A'), WOOD, True, False)
        for (uu, vv) in ((cu - 2.4, cv - 3.4), (cu + 2.4, cv + 3.4)):
            x, z = F.xz(uu, vv); B.cyl(x, z, 0.08, yb, yb + 4.2, DARK, 6, METAL, True); self.box(F, uu - 0.35, uu + 0.35, vv - 0.15, vv + 0.15, yb + 4.1, yb + 4.3, rgb('#FFF0B8'), PLAIN)
        for _ in range(6): self.tree(F, rnd.uniform(1.5, w - 1.5), rnd.uniform(1.5, d - 1.5), sc=rnd.uniform(0.9, 1.3))
        return True

    def vago(self, F, yb, sp):
        rnd = self.rnd; w, d = F.w, F.d
        for _ in range(rnd.choice((4, 5, 6))): self.tree(F, rnd.uniform(1.2, w - 1.2), rnd.uniform(1.5, d - 1.5), sc=rnd.uniform(0.8, 1.3))
        if rnd.random() < 0.5:
            self.wall_fence(F, 0.4, 0.4, w - 0.4, yb - 0.1, 0.8, rgb('#CFC6B4'), (w / 2 - 1.6, w / 2 + 1.6))
        return True

    # ================================================================== zoneamento e sorteio
    def zone(self, cx, cz):
        j, i = self.geo.idx(cx, cz); h = self.sample(cx, cz); Ds = float(self.geo.Dsea[j, i]); sl = self.geo.slope_at(cx, cz)
        if cz > 2300 and Ds < 260: return 'orla'
        if math.hypot(cx - LAGOON[0], cz - LAGOON[1]) < 720 and h < 16: return 'centro'
        if sl > 0.12 or h > 38: return 'colina'
        return 'res'

    def bairro(self, cx, cz):
        import lots as L
        best = None
        for nm, (bx, bz) in L.BAIRROS.items():
            d = math.hypot(cx - bx, cz - bz)
            if d < 520 and (best is None or d < best[0]): best = (d, nm)
        return best[1] if best else None

    TABLE = {
        (0, 'centro'): {'torre': .40, 'apto': .22, 'comercial': .25, 'mercado': .06, 'posto': .04, 'vago': 0.015},
        (0, 'orla'): {'hotel': .50, 'torre': .28, 'apto': .10, 'comercial': .08, 'posto': .02, 'pracinha': .02},
        (0, 'res'): {'apto': .28, 'comercial': .28, 'mercado': .12, 'posto': .08, 'galpao': .08, 'torre': .10, 'vago': 0.015},
        (0, 'colina'): {'mansao': .5, 'moderna': .35, 'vago': 0.075},
        (1, 'centro'): {'comercial': .30, 'apto': .28, 'torre': .17, 'sobrado': .05, 'igreja': .02, 'escola': .02, 'pracinha': .03, 'geminadas': .04, 'hotel': .06, 'vago': .03},
        (1, 'orla'): {'apto': .36, 'hotel': .12, 'moderna': .10, 'colonial': .05, 'sobrado': .08, 'comercial': .12, 'torre': .10, 'pracinha': .02, 'geminadas': .03, 'vago': .02},
        (1, 'res'): {'sobrado': .21, 'terrea': .18, 'moderna': .11, 'apto': .14, 'comercial': .11, 'geminadas': .08, 'igreja': .02, 'escola': .02, 'pracinha': 0.028, 'colonial': .05, 'vago': 0.020},
        (1, 'colina'): {'mansao': .33, 'moderna': .30, 'colonial': .14, 'vago': 0.115},
        (2, 'centro'): {'sobrado': .24, 'geminadas': .20, 'terrea': .10, 'apto': .14, 'comercial': .14, 'moderna': .06, 'pracinha': 0.035, 'vago': 0.035},
        (2, 'orla'): {'terrea': .22, 'moderna': .24, 'colonial': .14, 'sobrado': .16, 'geminadas': .10, 'pracinha': 0.028, 'vago': 0.050},
        (2, 'res'): {'terrea': .29, 'sobrado': .24, 'moderna': .12, 'colonial': .10, 'geminadas': .10, 'pracinha': 0.021, 'vago': 0.030, 'apto': .06},
        (2, 'colina'): {'mansao': .22, 'moderna': .30, 'colonial': .14, 'terrea': .09, 'vago': 0.125},
    }

    def pick(self, lvl, zone, bairro):
        t = dict(self.TABLE[(min(lvl, 2), zone)])
        if bairro in ('Alto da Colina', 'Península Real'):
            for k in list(t): t[k] *= 0.4 if k in ('terrea', 'geminadas', 'sobrado', 'apto') else 1.0
            t['mansao'] = t.get('mansao', 0) + 0.35; t['moderna'] = t.get('moderna', 0) + 0.2
        if bairro == 'Vila Esperança':
            t['geminadas'] = t.get('geminadas', 0) + 0.15; t['terrea'] = t.get('terrea', 0) + 0.1
            t.pop('mansao', None)
        r = self.rnd.random() * sum(t.values()); acc = 0.0
        for k, v in t.items():
            acc += v
            if r <= acc: return k
        return 'vago'

    FAMILIAS = (('terrea', 'sobrado'), ('sobrado', 'colonial'), ('moderna', 'sobrado'), ('colonial', 'terrea'), ('terrea', 'moderna'), ('sobrado', 'terrea'))
    FENCE_COLS = [rgb(c) for c in ('#B08A5E', '#9C7A55', '#C4A27A', '#8C6B4A', '#E9E4D8', '#7E6A58')]

    def pick_char(self, l, ch, bairro):
        """construcao conforme o carater da rua: a mesma familia de construcoes e o mesmo recuo de ponta a ponta"""
        rf = random.Random(l['front'] * 7919 + 17); st = l.get('style', 0.5); rnd = self.rnd
        w, d = l['w'], l['d']
        def roll(t):
            r = rnd.random() * sum(t.values()); a = 0.0
            for k, v in t.items():
                a += v
                if r <= a: return k
            return k
        ex = {}
        if ch == 'centro':
            if w >= 22 and d >= 26: k = roll({'torre': .45, 'apto': .25, 'comercial': .25, 'hotel': .05})
            else: k = roll({'apto': .5, 'comercial': .5})
            ex['sf'] = 0.6; ex['ss'] = 0.4
        elif ch == 'centro2':
            k = roll({'apto': .45, 'comercial': .35, 'geminadas': .2}); ex['sf'] = 1.0; ex['ss'] = 0.5
        elif ch == 'orla':
            k = roll({'hotel': .35, 'torre': .35, 'apto': .3}) if w >= 22 and d >= 26 else 'apto'
        elif ch == 'avenida':
            k = roll({'comercial': .45, 'apto': .25, 'mercado': .1, 'posto': .06, 'galpao': .07, 'igreja': .03, 'escola': .04}); ex['sf'] = 1.0 if k == 'comercial' else None
        elif ch == 'misto':
            fam = rf.choice((('apto', 'sobrado'), ('sobrado', 'geminadas'), ('apto', 'comercial'), ('geminadas', 'comercial')))
            k = fam[0] if rnd.random() < 0.65 else fam[1]
            ex['sf'] = l.get('setback') or None
        elif ch == 'nobre':
            k = roll({'mansao': .45, 'moderna': .35, 'colonial': .2}) if w >= 23 else roll({'moderna': .6, 'colonial': .4})
            ex['sf'] = l.get('setback') or None; ex['yard'] = True; ex['fcol'] = rf.choice(self.FENCE_COLS)
        elif ch == 'condo_predio':
            k = 'apto'; ex['sf'] = 3.0
        elif ch == 'condo':
            fam = self.FAMILIAS[int(st * len(self.FAMILIAS)) % len(self.FAMILIAS)]
            k = fam[0] if rnd.random() < 0.8 else fam[1]
            ex['sf'] = 4.5; ex['ss'] = 1.6; ex['yard'] = True; ex['front'] = 'aberto'
            ex['fcol'] = self.FENCE_COLS[int(l.get('fcol', 0.5) * len(self.FENCE_COLS)) % len(self.FENCE_COLS)]; ex['first'] = l.get('pos', 0) == 0
        else:   # suburbio: rua de casas, mesma familia e mesmo recuo, quintal cercado
            fam = self.FAMILIAS[int(st * len(self.FAMILIAS)) % len(self.FAMILIAS)]
            if bairro == 'Vila Esperança': fam = ('terrea', 'geminadas')
            if bairro in ('Alto da Colina', 'Península Real'): fam = ('moderna', 'colonial')
            k = fam[0] if rnd.random() < 0.7 else fam[1]
            if rnd.random() < 0.012: k = 'pracinha'
            ex['sf'] = l.get('setback') or 5.5; ex['ss'] = rf.choice((1.5, 1.8, 2.1)); ex['yard'] = True
            ex['front'] = 'picket' if rf.random() < 0.35 else 'aberto'; ex['fcol'] = rf.choice(self.FENCE_COLS)
            ex['first'] = l.get('pos', 0) == 0
        return k, {a: b for a, b in ex.items() if b is not None}

    def spec(self, kind, zone, bairro):
        rnd = self.rnd
        if zone == 'orla': walls = WALLS_BRIGHT + WALLS_WARM[:3]
        elif zone == 'centro': walls = WALLS_WARM + WALLS_COOL + WALLS_BRIGHT[:3]
        elif zone == 'colina': walls = WALLS_COOL + WALLS_WARM[:4]
        else: walls = WALLS_WARM + WALLS_BRIGHT[:5] + WALLS_COOL[:3]
        sp = {'wall': rnd.choice(walls), 'roof': rnd.choice(ROOFS), 'glass': rnd.choice((GLASS, GLASS_D, rgb('#8FB4C9'))), 'door': rnd.choice(DOOR),
              'shutter': rnd.choice((rgb('#2E5B3E'), rgb('#2F4A66'), rgb('#7A2E2E'), rgb('#F7F4EC'))), 'accent': rnd.choice((rgb('#E24A4A'), rgb('#2F6DB5'), rgb('#F2A93B'), rgb('#2E9D4B'), rgb('#8E44AD'), rgb('#E24A8A'))),
              'sign': rnd.choice((rgb('#E24A4A'), rgb('#F2A93B'), rgb('#2F6DB5'), rgb('#2E9D4B'), rgb('#F4F4F2'), rgb('#3F4247')))}
        if kind in ('torre', 'hotel'):
            sp['wall'] = rnd.choice(TOWER_WALL); sp['glass'] = rnd.choice(TOWER_GLASS)
            sp['floors'] = rnd.randint(14, 26) if (zone == 'centro' and kind == 'torre') else rnd.randint(10, 18)
            sp['hotel'] = kind == 'hotel'
        if kind == 'apto':
            sp['floors'] = rnd.randint(6, 10) if zone == 'centro' else rnd.randint(4, 8)
            if zone != 'orla': sp['wall'] = rnd.choice(WALLS_WARM + WALLS_COOL)
        if kind == 'comercial': sp['floors'] = rnd.randint(3, 5) if zone == 'centro' else rnd.randint(2, 3)
        return sp

    def run(self):
        P = self.P
        counts = {}
        for l in sorted(P.lots, key=lambda q: q['id']):
            rect = l['rect']; F = Frame(rect)
            cx, cz = F.xz(F.w / 2, F.d / 2)
            zone = self.zone(cx, cz); br = self.bairro(cx, cz)
            ch = l.get('char')
            if ch: kind, extra = self.pick_char(l, ch, br)
            else:
                kind = self.pick(l['lvl'], zone, br); extra = {}
            # altura da base: media do terreno no miolo do lote; muito inclinado vira jardim
            hs = [self.sample(*F.xz(u * F.w, v * F.d)) for u in (0.2, 0.5, 0.8) for v in (0.2, 0.5, 0.8)]
            level = l['slope'] <= T.LOT_SLOPE_MAX
            yb = (l['y'] + 0.12) if level else float(np.mean(hs)) + 0.05
            if not level and kind not in ('vago', 'pracinha'):
                self.stats['v_slope'] = self.stats.get('v_slope', 0) + 1; kind = 'vago'
            sp = self.spec('torre' if kind == 'hotel' else kind, zone, br)
            if kind == 'hotel': sp['hotel'] = True
            sp.update(extra); self.cur = sp
            fn = {'terrea': self.casa_terrea, 'sobrado': self.sobrado, 'moderna': self.casa_moderna, 'colonial': self.colonial, 'geminadas': self.geminadas, 'mansao': self.mansao,
                  'apto': self.predio_apto, 'torre': self.torre, 'hotel': self.torre, 'comercial': self.comercial, 'igreja': self.igreja, 'escola': self.escola, 'posto': self.posto,
                  'mercado': self.mercado, 'galpao': self.galpao, 'pracinha': self.pracinha, 'vago': self.vago}[kind]
            ok = fn(F, yb, sp)
            if not ok:
                altk = {'torre': 'apto', 'hotel': 'apto', 'apto': 'sobrado', 'mansao': 'moderna', 'comercial': 'sobrado', 'igreja': 'sobrado', 'escola': 'sobrado',
                        'posto': 'comercial', 'mercado': 'comercial', 'galpao': 'comercial', 'moderna': 'terrea', 'colonial': 'terrea', 'sobrado': 'terrea'}.get(kind, 'terrea')
                fn2 = {'terrea': self.casa_terrea, 'sobrado': self.sobrado, 'moderna': self.casa_moderna, 'apto': self.predio_apto, 'comercial': self.comercial}[altk]
                sp2 = self.spec(altk, zone, br); sp2.update(extra); self.cur = sp2
                ok = fn2(F, yb, sp2)
                if not ok and altk != 'terrea': ok = self.casa_terrea(F, yb, self.spec('terrea', zone, br)); altk = 'terrea'
                if not ok: self.vago(F, yb, sp); kind = 'vago'; self.stats['v_fail'] = self.stats.get('v_fail', 0) + 1
                else: kind = 'alt_' + kind
            counts[kind] = counts.get(kind, 0) + 1
            if kind == 'vago' and ok is True and self.stats.get('v_pick') is not None: pass
            self.items.append({'id': l['id'], 'kind': kind, 'zone': zone, 'bairro': br})
        self.kinds = counts
        # vielas dos condominios (bloquete), em pedacos de ~8 m acompanhando o terreno
        for q in getattr(P, 'lanes', []):
            a, b, c, d = q
            L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L / 3.0)); m = 3
            def P_(t, s_):
                x0, z0 = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t; x1, z1 = d[0] + (c[0] - d[0]) * t, d[1] + (c[1] - d[1]) * t
                x, z = x0 + (x1 - x0) * s_, z0 + (z1 - z0) * s_
                return (x, self.sample(x, z) + 0.28, z)
            for k in range(n):
                for j in range(m):
                    t0, t1, s0, s1 = k / n, (k + 1) / n, j / m, (j + 1) / m
                    self.B.quad(PAVER, [P_(t0, s0), P_(t1, s0), P_(t1, s1), P_(t0, s1)], (0, 1, 0), rgb('#BDB6A8'), None, True)
            # meio-fio das vielas
            for (p0, p1) in ((a, b), (d, c)):
                for k in range(n):
                    t0, t1 = k / n, (k + 1) / n
                    x0, z0 = p0[0] + (p1[0] - p0[0]) * t0, p0[1] + (p1[1] - p0[1]) * t0; x1, z1 = p0[0] + (p1[0] - p0[0]) * t1, p0[1] + (p1[1] - p0[1]) * t1
                    y = min(self.sample(x0, z0), self.sample(x1, z1))
                    dx, dz = x1 - x0, z1 - z0; ll = math.hypot(dx, dz) or 1; nx, nz = -dz / ll * 0.12, dx / ll * 0.12
                    self.B.obox_pts([(x0 - nx, z0 - nz), (x1 - nx, z1 - nz), (x1 + nx, z1 + nz), (x0 + nx, z0 + nz)], y - 0.1, y + 0.22, rgb('#D9D4C8'), STONE, True, False)
        return self


def write_sub2(B, path):
    """SUB2: mesmo cabecalho do SUB1, vertice compacto de 20 bytes:
    posicao int16 x3 (unidade 2 cm, relativa ao canto da celula de 64 m), normal int8 x3 (*127), uv float32 x2, cor uint8 x3"""
    import struct
    dt = np.dtype([('p', '<i2', 3), ('n', 'i1', 3), ('uv', '<f4', 2), ('c', 'u1', 3)])
    assert dt.itemsize == 20
    recs = [(cell, mat, v) for (cell, mat), v in sorted(B.tris.items()) if v]
    with open(path, 'wb') as f:
        f.write(b'SUB2'); f.write(struct.pack('<i', len(recs)))
        for cell, mat, verts in recs:
            a = np.array(verts, dtype=np.float64)
            ox, oz = (cell % 1000) * 64.0, (cell // 1000) * 64.0
            rel = np.stack([a[:, 0] - ox, a[:, 1], a[:, 2] - oz], 1) * 50.0
            if np.abs(rel).max() >= 32760:
                bad = np.nonzero(np.abs(rel).max(1) >= 32760)[0]; print('SUB2: vertices fora da faixa', cell, mat, len(bad), a[bad[:3], :3].tolist())
                keep = np.ones(len(a), bool)
                for t in set((bad // 3).tolist()): keep[t * 3:t * 3 + 3] = False
                a = a[keep]; rel = rel[keep]
                if not len(a): continue
            o = np.zeros(len(a), dt)
            o['p'] = np.round(rel).astype('<i2'); o['n'] = np.round(np.clip(a[:, 3:6], -1, 1) * 127).astype('i1')
            o['uv'] = a[:, 6:8].astype('<f4'); o['c'] = a[:, 8:11].astype('u1')
            f.write(struct.pack('<iiif', cell, mat, len(a), float(a[:, 1].max()))); f.write(o.tobytes())
    return len(recs)
