"""Cidade 6 - chao: terreno (morros nas bordas, praia, leito do rio e do mar), agua, ruas completas
(asfalto, guias, calcadas, faixas de grama, canteiros centrais, faixas pintadas, faixas de pedestre, pontes)."""
import math, random
import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box as sbox
from shapely.ops import unary_union
from mesh import rgb, shade, mix, WHITE
from plan6 import *

Y_ASF = 0.03          # asfalto
Y_WALK = 0.16         # calcada
Y_LAWN = 0.13         # gramado
Y_RIVER = -1.5        # espelho d'agua do rio
Y_SEA = -0.9

C_ASF = rgb('#55575C'); C_ASF2 = rgb('#4D4F54'); C_CURB = rgb('#C9C5BC'); C_WALK = rgb('#D8D3C8'); C_WALK2 = rgb('#CFC9BC')
C_GRASS = rgb('#6FA34E'); C_GRASS2 = rgb('#7DB159'); C_WHITE = rgb('#F2F2EE'); C_YEL = rgb('#F2C230'); C_SAND = rgb('#E6D5A4')
C_ROCK = rgb('#8C877C'); C_WATER = rgb('#3F86B8'); C_SEA = rgb('#2F78B0'); C_BED = rgb('#9C8F6E'); C_STONE = rgb('#9E978A')


def axis(r):
    (x0, z0), (x1, z1) = r['pts'][0], r['pts'][-1]
    L = math.hypot(x1 - x0, z1 - z0); return (x0, z0), ((x1 - x0) / L, (z1 - z0) / L), L


class Ground:
    def __init__(self, P, M, seed=6):
        self.P = P; self.M = M; self.rnd = random.Random(seed)
        self.nodes_on = {}       # road index -> lista de (s, raio de exclusao, outra via)
        self.inter_pts = []      # (x, z, kinds)

    # ------------------------------------------------------------ cruzamentos
    def intersections(self):
        R = self.P.roads
        for i, a in enumerate(R): self.nodes_on[i] = []
        for i in range(len(R)):
            for j in range(i + 1, len(R)):
                g = R[i]['line'].intersection(R[j]['line'])
                if g.is_empty: continue
                pts = [g] if g.geom_type == 'Point' else list(getattr(g, 'geoms', []))
                for p in pts:
                    if p.geom_type != 'Point': continue
                    si = R[i]['line'].project(p); sj = R[j]['line'].project(p)
                    self.nodes_on[i].append((si, half_row(R[j]['kind']) + 7.0, j))
                    self.nodes_on[j].append((sj, half_row(R[i]['kind']) + 7.0, i))
                    self.inter_pts.append((p.x, p.y, R[i]['kind'], R[j]['kind'], i, j))
        # extremidades das vias (pontas sem cruzamento) tambem cortam faixas
        for i, r in enumerate(R):
            L = r['line'].length
            self.nodes_on[i].append((0.0, 4.0, -1)); self.nodes_on[i].append((L, 4.0, -1))
        return self

    def free_spans(self, i, pad=0.0):
        """trechos de uma via livres de cruzamentos"""
        L = self.P.roads[i]['line'].length
        cuts = sorted((s - r - pad, s + r + pad) for s, r, _ in self.nodes_on[i])
        spans = []; cur = 0.0
        for a, b in cuts:
            if a > cur: spans.append((cur, a))
            cur = max(cur, b)
        if cur < L: spans.append((cur, L))
        return [(a, b) for a, b in spans if b - a > 1.0]

    # ------------------------------------------------------------ terreno
    def height(self, X, Z):
        """terreno natural: plano na cidade, morros nas bordas (fora da faixa das vias), praia/mar e leito do rio"""
        P = self.P
        h = np.full_like(X, -0.25)          # chao da cidade fica abaixo do asfalto/gramados (sem disputa de profundidade)
        # morros: norte (z<130), oeste (x<105), leste (x>2455)
        # distancia ate a borda da cidade (morros comecam ~20 m antes das ultimas ruas e sobem ate a borda do mapa)
        e = np.minimum.reduce([Z - 4, X - 4, W - 4 - X])
        e = e + 14 * np.sin(X / 83.0 + 1.1) * np.cos(Z / 71.0) + 8 * np.sin((X + Z) / 37.0)
        hill = np.clip((115 - e) / 115, 0, 1)
        nz = np.sin(X / 61.0) * np.cos(Z / 47.0) * 0.5 + np.sin(X / 29.0 + Z / 41.0) * 0.3
        hh = (hill * hill * (3 - 2 * hill)) * (26 + 12 * nz)
        hh = np.where(Z > 1650, hh * np.clip((1760 - Z) / 110, 0, 1), hh)          # morros somem perto da praia
        # vias que entram nos morros: corredor plano
        pts = shapely.points(X.ravel(), Z.ravel())
        d = shapely.distance(P.row, pts).reshape(X.shape)
        h += hh * np.clip((d - 6) / 30, 0, 1)
        # praia e mar
        sz = np.vectorize(shore_z)(X)
        ZW = 1718.0                                              # mureta do calcadao: dali para o sul e areia
        t = np.clip((Z - ZW) / np.maximum(sz - ZW, 1.0), 0, 1)
        hb = -0.35 - 0.55 * t ** 1.2
        h = np.where(Z > ZW, hb, h)
        h = np.where(Z > sz, -0.9 - np.clip((Z - sz) / 120, 0, 1) * 6.0, h)
        # rio (leito)
        rx = np.vectorize(river_x)(Z)
        dr = np.abs(X - rx)
        h = np.where(dr < RIVER_W / 2 + RIVER_WALL, np.minimum(h, -3.6 + 1.2 * (dr / (RIVER_W / 2)) ** 2), h)
        return h

    def terrain(self):
        M = self.M.free('terreno'); M.m('terreno')
        st = 10.0
        xs = np.arange(0, W + 0.1, st); zs = np.arange(0, H + 0.1, st)
        X, Z = np.meshgrid(xs, zs)
        Hh = self.height(X, Z)
        gz, gx = np.gradient(Hh, st)
        N = np.dstack([-gx, np.ones_like(Hh), -gz]); N /= np.linalg.norm(N, axis=2, keepdims=True)
        slope = np.hypot(gx, gz)
        sz = np.vectorize(shore_z)(X)
        C = np.zeros(Hh.shape + (3,))
        grass = np.array(C_GRASS, float); dark = np.array(rgb('#4F8A3E'), float); rock = np.array(C_ROCK, float); sand = np.array(C_SAND, float); bed = np.array(C_BED, float)
        nn = (np.sin(X / 13.0) * np.cos(Z / 17.0) + 1) / 2
        C[:] = grass * (1 - 0.25 * nn[..., None]) + dark * 0.25 * nn[..., None]
        C = np.where((Hh > 6)[..., None], C * 0.85 + dark * 0.15, C)
        C = np.where((slope > 0.75)[..., None], C * 0.45 + rock * 0.55, C)
        C = np.where((Z > 1712)[..., None] & (Hh < 0.3)[..., None], sand, C)
        C = np.where((Hh < -1.0)[..., None], bed, C)
        P3 = np.dstack([X, Hh, Z])
        self.H = Hh; self.st = st
        M.smooth_grid(P3, N, C.astype(np.uint8))

    def h_at(self, x, z):
        i = min(max(int(round(x / self.st)), 0), self.H.shape[1] - 1); j = min(max(int(round(z / self.st)), 0), self.H.shape[0] - 1)
        return float(self.H[j, i])

    # ------------------------------------------------------------ agua
    def water(self):
        M = self.M.free('agua'); M.m('agua')
        P = self.P
        # mar: faixas largas (cada pedaco no seu tile)
        for x0 in range(0, int(W), 125):
            for z0 in range(1700, int(H), 125):
                q = sbox(x0, z0, x0 + 125, z0 + 125).intersection(P.sea)
                M.shp(q, Y_SEA, (215, 228, 240))
        # rio
        for z0 in range(-20, int(shore_z(1700)) + 40, 60):
            q = sbox(0, z0, W, z0 + 60).intersection(P.river).difference(P.sea)
            M.shp(q, Y_RIVER, (200, 214, 205))
        # espuma na beira da praia
        xs = np.arange(0, W, 6.0); M.m('liso')
        for x in xs:
            z0, z1 = shore_z(x), shore_z(x + 6)
            M.quad((x, Y_SEA + 0.03, z0 - 1.2), (x + 6, Y_SEA + 0.03, z1 - 1.2), (x + 6, Y_SEA + 0.03, z1 + 1.8), (x, Y_SEA + 0.03, z0 + 1.8), rgb('#E8F4F2'), (0, 1, 0))
        # cais de pedra nas margens do rio (de -3 a +0,2) e guarda-corpo
        M.free('ruas'); M.m('pedra')
        for sgn in (-1, 1):
            zs = np.arange(-10, shore_z(1700) - 4, 4.0)
            line = [(river_x(z) + sgn * (RIVER_W / 2 + RIVER_WALL / 2), z) for z in zs]
            M.m('pedra'); M.wall_strip(line, -3.2, 0.25, RIVER_WALL, WHITE); M.m('metal')
            # guarda-corpo (fora das pontes)
            for i in range(len(line) - 1):
                a, b = line[i], line[i + 1]
                if any(abs(a[1] - zb) < 18 for zb in self.bridge_z): continue
                M.wall_strip([a, b], 1.05, 1.15, 0.08, rgb('#3E4247'))
                if i % 2 == 0: M.box(a[0] - 0.05, a[0] + 0.05, 0.25, 1.1, a[1] - 0.05, a[1] + 0.05, rgb('#3E4247'))

    # ------------------------------------------------------------ ruas
    def roads(self):
        M = self.M; P = self.P
        M.free('ruas')
        self.bridge_z = []
        # asfalto em pedacos de tile (fica no tile certo)
        for x0 in range(0, int(W), 250):
            for z0 in range(0, int(H), 250):
                cell = sbox(x0, z0, x0 + 250, z0 + 250)
                a = P.asphalt.intersection(cell)
                M.m('asfalto'); M.shp(a, Y_ASF, WHITE)
                walk = P.row.difference(P.asphalt).intersection(cell)
                self.walk_cells = getattr(self, 'walk_cells', []) ; self.walk_cells.append(walk)
        # faixas de grama (entre guia e calcada) e canteiros centrais: fora dos cruzamentos
        verges = []; meds = []
        for i, r in enumerate(P.roads):
            pr = PROFILE[r['kind']]; pth = r['path']
            for (s0, s1) in self.free_spans(i, pad=3.0):
                if pr['verge'] > 0:
                    for sg in (-1, 1):
                        r0, r1 = pr['road'] + 0.25, pr['road'] + pr['verge']
                        verges.append(pth.band(s0, s1, sg * r0, sg * r1).buffer(0))
                if pr['med'] > 0:
                    meds.append((pth.band(s0, s1, -pr['med'], pr['med']).buffer(0), r, pth.pt(s0), pth.pt(s1)))
        V = unary_union(verges).difference(P.river.buffer(RIVER_WALL))
        self.verges = V
        W_ = P.row.difference(P.asphalt).difference(V)
        self.walks = W_
        for x0 in range(0, int(W), 250):
            for z0 in range(0, int(H), 250):
                cell = sbox(x0, z0, x0 + 250, z0 + 250)
                M.m('calcada'); M.shp(W_.intersection(cell), Y_WALK, WHITE)
                M.m('grama'); M.shp(V.intersection(cell), Y_LAWN + 0.02, WHITE)
        # guias (meio-fio): ao longo de todo o contorno do asfalto
        M.m('concreto')
        for g in getattr(P.asphalt, 'geoms', [P.asphalt]):
            for ring in [g.exterior] + list(g.interiors):
                pts = list(ring.coords)
                for k in range(len(pts) - 1):
                    a, b = pts[k], pts[k + 1]
                    dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz)
                    if L < 0.05: continue
                    mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                    if P.river.contains(Point(mx, mz)): continue
                    M.at(mx, mz)
                    M.wall_strip([a, b], Y_ASF - 0.02, Y_WALK + 0.01, 0.22, (236, 234, 228))
                    M.free()
        # bordas de calcada/gramado contra os lotes (degrauzinho) ficam escondidas pelo lote
        # canteiro central das avenidas: guia + grama + palmeiras/arvores (as arvores entram em props)
        self.medians = []
        for (q, r, a, b) in meds:
            if q.intersects(P.river.buffer(2)):
                for part in getattr(q.difference(P.river.buffer(8)), 'geoms', [q.difference(P.river.buffer(8))]):
                    if part.area > 5: self._median(part); self.medians.append((part, r))
                continue
            self._median(q); self.medians.append((q, r))
        self.markings()
        self.bridges()

    def _median(self, q):
        M = self.M
        c = q.centroid; M.at(c.x, c.y)
        pts = list(q.exterior.coords)[:-1]
        M.m('concreto'); M.prism(pts, Y_ASF - 0.02, 0.22, (236, 234, 228), top=False)
        M.m('grama'); M.flat(pts, 0.22, WHITE)
        M.free()

    # ------------------------------------------------------------ pintura
    def stripe(self, pth, s0, s1, off, w, col, dash=None, gap=None, y=Y_ASF + 0.012):
        """faixa pintada ao longo do eixo (curvas: em pedacos de ate 3 m)"""
        M = self.M
        segs = []
        if dash:
            s = s0
            while s < s1:
                segs.append((s, min(s + dash, s1))); s += dash + gap
        else: segs = [(s0, s1)]
        old = M.m('liso')
        for a, b in segs:
            if b - a < 0.2: continue
            n = max(1, int(math.ceil((b - a) / 3.0)))
            for k in range(n):
                q0, q1 = a + (b - a) * k / n, a + (b - a) * (k + 1) / n
                p = [pth.pt(q0, off - w / 2), pth.pt(q1, off - w / 2), pth.pt(q1, off + w / 2), pth.pt(q0, off + w / 2)]
                M.at((p[0][0] + p[2][0]) / 2, (p[0][1] + p[2][1]) / 2); M.poly([(x, y, z) for x, z in p], col, (0, 1, 0)); M.free()
        M.m(old)

    def markings(self):
        P = self.P; self.crossings = []
        for i, r in enumerate(P.roads):
            pr = PROFILE[r['kind']]; pth = r['path']; L = pth.L
            for (s0, s1) in self.free_spans(i, pad=1.0):
                k = r['kind']
                if k in ('av', 'orla'):
                    for sg in (-1, 1):
                        self.stripe(pth, s0, s1, sg * (pr['med'] + 0.35), 0.15, C_YEL)                    # amarela junto ao canteiro
                        self.stripe(pth, s0, s1, sg * (pr['med'] + 0.35 + 3.4), 0.13, C_WHITE, 3.0, 6.0)  # tracejada entre faixas
                        self.stripe(pth, s0, s1, sg * (pr['road'] - 0.45), 0.14, C_WHITE)                  # bordo
                elif k == 'centro':
                    self.stripe(pth, s0, s1, 0.0, 0.14, C_YEL, 3.0, 5.0)
                    for sg in (-1, 1): self.stripe(pth, s0, s1, sg * (pr['road'] - 2.3), 0.12, C_WHITE)      # linha da faixa de estacionamento
                else:
                    self.stripe(pth, s0, s1, -0.12, 0.11, C_YEL); self.stripe(pth, s0, s1, 0.12, 0.11, C_YEL)  # dupla amarela
            # faixas de pedestre e linhas de retencao: em cada aproximacao de cruzamento entre vias da cidade
            for (s, rr, j) in self.nodes_on[i]:
                if j < 0: continue
                other = P.roads[j]
                for sg in (-1, 1):
                    sc = s + sg * (half_row(other['kind']) + 1.5)       # faixa de pedestre logo apos a calcada da transversal
                    if sc < 4 or sc > L - 4: continue
                    n = int((2 * pr['road'] - 0.6) / 1.1)
                    for q in range(n):
                        off = -pr['road'] + 0.5 + q * 1.1 + 0.25
                        if pr['med'] and abs(off) < pr['med'] + 0.2: continue
                        self.stripe(pth, sc - 1.6, sc + 1.6, off, 0.55, C_WHITE, y=Y_ASF + 0.014)
                    # linha de retencao (lado de quem chega)
                    sl = sc + sg * 2.6
                    lane_side = -sg            # mao direita: quem chega em direcao ao cruzamento
                    self.stripe(pth, sl - 0.2, sl + 0.2, lane_side * (pr['road'] + (pr['med'] or 0.2)) / 2, pr['road'] - (pr['med'] or 0.2) - 0.4, C_WHITE, y=Y_ASF + 0.014)
                    cx_, cz_, tx_, tz_ = pth.at(sc); self.crossings.append((cx_, cz_, (tx_, tz_), i, sg))

    # ------------------------------------------------------------ pontes
    def bridges(self):
        M = self.M; P = self.P
        self.bridge_z = []
        for i, r in enumerate(P.roads):
            g = r['line'].intersection(P.river)
            if g.is_empty: continue
            o, d, L = axis(r)
            if abs(d[0]) < 0.9: continue
            z = o[1]; hw = half_row(r['kind'])
            xa = river_x(z) - RIVER_W / 2 - RIVER_WALL - 2; xb = river_x(z) + RIVER_W / 2 + RIVER_WALL + 2
            self.bridge_z.append(z)
            M.at((xa + xb) / 2, z, 'ruas'); M.m('concreto')
            # tabuleiro (laje) com viga lateral e parapeito
            M.box(xa, xb, -1.1, Y_ASF - 0.01, z - hw, z + hw, rgb('#B9B3A8'), top=False, bottom=True)
            for sg in (-1, 1):
                zz = z + sg * hw
                M.box(xa, xb, -1.2, Y_WALK + 1.05, zz - (0.35 if sg > 0 else 0), zz + (0.35 if sg < 0 else 0), rgb('#D7D1C4'))
                M.box(xa, xb, Y_WALK + 1.05, Y_WALK + 1.18, zz - 0.4, zz + 0.4, rgb('#9C968B'))
                M.m('metal')
                for x in np.arange(xa + 2, xb - 1, 6.0):              # postes da ponte
                    M.box(x - 0.12, x + 0.12, Y_WALK, Y_WALK + 6.5, zz - sg * 0.6 - 0.12, zz - sg * 0.6 + 0.12, rgb('#3E4247'))
                    M.box(x - 0.12, x + 0.12, Y_WALK + 6.3, Y_WALK + 6.45, zz - sg * 0.6 - sg * 1.6, zz - sg * 0.6 + 0.1, rgb('#3E4247'))
                    M.box(x - 0.3, x + 0.3, Y_WALK + 6.1, Y_WALK + 6.3, zz - sg * 2.0 - 0.25, zz - sg * 2.0 + 0.25, rgb('#FFF3C4'))
            # pilares no rio
            M.m('concreto')
            for xp in (river_x(z) - RIVER_W / 6, river_x(z) + RIVER_W / 6):
                for zp in np.linspace(z - hw + 2, z + hw - 2, 3):
                    M.cyl(xp, zp, 0.9, -3.6, -1.1, rgb('#A9A397'), 10)
            M.free()
        # ponte de pedestre (arco) no Parque Ribeirinho
        z = self.P.footbridge[0]; xa = river_x(z) - RIVER_W / 2 - RIVER_WALL - 1; xb = river_x(z) + RIVER_W / 2 + RIVER_WALL + 1
        M.at((xa + xb) / 2, z, 'ruas'); M.m('madeira')
        n = 16
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            x0, x1 = xa + (xb - xa) * t0, xa + (xb - xa) * t1
            y0, y1 = 0.2 + 2.2 * math.sin(math.pi * t0), 0.2 + 2.2 * math.sin(math.pi * t1)
            M.quad((x0, y0, z - 2), (x1, y1, z - 2), (x1, y1, z + 2), (x0, y0, z + 2), rgb('#A47A52'), (0, 1, 0))
            M.quad((x0, y0 - 0.4, z + 2), (x1, y1 - 0.4, z + 2), (x1, y1 - 0.4, z - 2), (x0, y0 - 0.4, z - 2), rgb('#7A5A3C'), (0, -1, 0))
            for sg in (-1, 1):
                M.quad((x0, y0 - 0.4, z + sg * 2), (x1, y1 - 0.4, z + sg * 2), (x1, y1, z + sg * 2), (x0, y0, z + sg * 2), rgb('#7A5A3C'), (0, 0, sg))
                M.quad((x0, y0 + 1.0, z + sg * 1.95), (x1, y1 + 1.0, z + sg * 1.95), (x1, y1 + 1.1, z + sg * 1.95), (x0, y0 + 1.1, z + sg * 1.95), rgb('#F2F0EA'), (0, 0, sg))
                M.box(x0 - 0.05, x0 + 0.05, y0, y0 + 1.05, z + sg * 1.95 - 0.05, z + sg * 1.95 + 0.05, rgb('#F2F0EA'))
            # arco branco por baixo
            ya0, ya1 = -1.2 + 3.0 * math.sin(math.pi * t0), -1.2 + 3.0 * math.sin(math.pi * t1)
            for sg in (-1, 1):
                M.box(min(x0, x1), max(x0, x1), min(ya0, ya1) - 0.15, max(ya0, ya1) + 0.15, z + sg * 1.7 - 0.15, z + sg * 1.7 + 0.15, rgb('#F2F0EA'))
        M.free()

    def build(self):
        self.intersections()
        self.terrain()
        self.roads()
        self.water()
        return self
