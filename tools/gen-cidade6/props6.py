"""Cidade 6 - vida: arvores, postes, semaforos, placas, hidrantes, bancos, carros estacionados; Parque Central, margens do rio,
orla (calcadao, quiosques, salva-vidas, guarda-sois, pier), marina, mata nos morros."""
import math, random
import numpy as np
from shapely.geometry import Point, Polygon, LineString, box as sbox
from mesh import rgb, shade, mix, WHITE, Frame
from plan6 import *
import plants6 as PL
from roads6 import Y_ASF, Y_WALK, Y_LAWN, Y_SEA, Y_RIVER, axis

LEAF = [rgb(c) for c in ('#5E9B4A', '#6FAE52', '#4F8A43', '#7DB55A', '#88B84E', '#5A8F3C', '#A4B84E', '#C9862F')]
CARS = [rgb(c) for c in ('#E8E8E8', '#1F1F22', '#7A7D82', '#B52B2B', '#2B4E8C', '#F2F0EA', '#3C5A3C', '#C9B48A', '#5A6D82', '#8C1F2E', '#D9D9D4', '#2F2F33')]


class Props:
    def __init__(self, P, G, L, M, seed=77):
        self.P, self.G, self.L, self.M = P, G, L, M
        self.rnd = random.Random(seed)
        self.drives = L.B.drives
        self.nlights = 0; self.ncars = 0; self.ntrees = 0; self.app_trees = []; self.app_y = []

    # ------------------------------------------------------------ arvores
    APP_TREE = {'folhosa': (0, 1), 'oval': (1, 0), 'ornamental': (1,), 'frutifera': (0,), 'conifera': (3,), 'florida': (2,), 'colunar': (3,)}

    # arbustos e flores: no jogo viram os modelos com textura do proprio app (assets/flora): 4 bush_a, 5 bush_b,
    # 6 bush_pink, 7 bush_white, 8 hedge, 9..13 flores (daisy, tulip, lav, poppy, yellow)
    APP_PLANT = {'arbusto': ((4, 5, 4, 6, 7), 0.9), 'buxo': ((4, 8), 0.7), 'flores': ((9, 10, 11, 12, 13), 1.25)}

    def tree(self, x, z, kind='folhosa', sc=1.0, y=Y_LAWN, lod=1):
        """arvores comuns, arbustos e flores vao para a lista do jogo (app_trees + app_y): la viram a arvore da Cidade 2 e os
        modelos de arbusto/flor do app. No GLB continuam com a malha propria (camadas 'arvores' e 'arbustos').
        Palmeiras ficam na camada 'vegetacao' (malha propria tambem no jogo)."""
        mata = getattr(self, 'layer_tree', None) == 'mata'
        if not mata and kind not in ('flores', 'buxo') and hasattr(self, 'drive_idx'):
            big = kind not in ('arbusto',)
            if self.near_light(x, z, 3.0 if big else 1.2) or self.near_drive(x, z, 1.0 if big else 0.2): return     # nada de arvore no poste nem na porta
        if kind in self.APP_TREE:
            layer = 'mata' if mata else 'arvores'
            sp = self.rnd.choice(self.APP_TREE[kind])
            self.app_trees.append([round(x, 1), round(z, 1), sp, round(sc * (0.62 if kind in ('ornamental', 'frutifera') else 1.0), 2), round(self.rnd.uniform(0, 6.28), 2), round(self.rnd.random(), 2)])
            self.app_y.append(round(y, 2))
        elif kind in self.APP_PLANT:
            layer = 'arbustos'
            ids, f = self.APP_PLANT[kind]
            self.app_trees.append([round(x, 1), round(z, 1), self.rnd.choice(ids), round(sc * f, 2), round(self.rnd.uniform(0, 6.28), 2), round(self.rnd.random(), 2)])
            self.app_y.append(round(y, 2))
        else: layer = 'vegetacao'
        PL.tree(self.M, self.rnd, x, z, kind, sc, y, layer, 0 if mata else lod)
        self.ntrees += 1

    # ------------------------------------------------------------ mobiliario urbano
    def streetlight(self, x, z, nx, nz, double=False):
        """poste: base na calcada, braco sobre a pista (nx, nz = direcao da pista)"""
        M = self.M; M.at(x, z, 'mobiliario'); self.add_light(x, z)
        M.m('metal'); col = (78, 82, 88)
        M.cyl(x, z, 0.12, Y_WALK, Y_WALK + 8.5, col, 6, True, 0.09)
        for s in ((1,) if not double else (1, -1)):
            ex, ez = x + nx * 2.2 * s, z + nz * 2.2 * s
            M.quad((x, Y_WALK + 8.4, z), (ex, Y_WALK + 8.6, ez), (ex, Y_WALK + 8.75, ez), (x, Y_WALK + 8.55, z), col, (-nz, 0, nx))
            M.box(ex - 0.35, ex + 0.35, Y_WALK + 8.35, Y_WALK + 8.6, ez - 0.2, ez + 0.2, col)
            M.m('liso'); M.quad((ex - 0.3, Y_WALK + 8.34, ez - 0.16), (ex + 0.3, Y_WALK + 8.34, ez - 0.16), (ex + 0.3, Y_WALK + 8.34, ez + 0.16), (ex - 0.3, Y_WALK + 8.34, ez + 0.16), (255, 244, 200), (0, -1, 0)); M.m('metal')
        self.nlights += 1; M.free()

    def traffic_light(self, x, z, dx, dz, arm):
        """semaforo de braco: dx,dz = direcao para o meio da pista que ele controla"""
        M = self.M; M.at(x, z, 'mobiliario'); M.m('metal'); col = (60, 64, 70)
        M.cyl(x, z, 0.16, Y_WALK, Y_WALK + 6.2, col, 6)
        ex, ez = x + dx * arm, z + dz * arm
        M.quad((x, Y_WALK + 5.9, z), (ex, Y_WALK + 5.9, ez), (ex, Y_WALK + 6.1, ez), (x, Y_WALK + 6.1, z), col, (-dz, 0, dx))
        for t in (0.55, 0.95):
            hx, hz = x + dx * arm * t, z + dz * arm * t
            M.box(hx - 0.22, hx + 0.22, Y_WALK + 4.7, Y_WALK + 5.9, hz - 0.22, hz + 0.22, (40, 42, 46))
            M.m('liso')
            for k, c in enumerate(((210, 40, 40), (230, 170, 30), (40, 190, 80))):
                yy = Y_WALK + 5.65 - k * 0.38
                M.box(hx - 0.13, hx + 0.13, yy - 0.13, yy + 0.13, hz - 0.25, hz + 0.25, c if k == 2 else shade(c, -90))
            M.m('metal')
        M.box(x - 0.2, x + 0.2, Y_WALK + 2.2, Y_WALK + 2.9, z - 0.15, z + 0.15, (40, 42, 46))      # botoeira/pedestre
        M.free()

    def stop_sign(self, x, z, fx, fz):
        M = self.M; M.at(x, z, 'mobiliario'); M.m('metal')
        M.cyl(x, z, 0.04, Y_WALK, Y_WALK + 2.4, (150, 152, 156), 5)
        M.m('liso'); px, pz = -fz, fx
        pts = [(x + px * 0.35 * math.cos(a) + fx * 0.06, Y_WALK + 2.45 + 0.35 * math.sin(a), z + pz * 0.35 * math.cos(a) + fz * 0.06) for a in [math.pi / 8 + k * math.pi / 4 for k in range(8)]]
        M.poly(pts, (196, 32, 36), (fx, 0, fz)); M.poly([(p[0] - fx * 0.05, p[1], p[2] - fz * 0.05) for p in pts], (180, 180, 182), (-fx, 0, -fz))
        M.free()

    def hydrant(self, x, z):
        M = self.M; M.at(x, z, 'mobiliario'); M.m('liso')
        M.cyl(x, z, 0.16, Y_WALK, Y_WALK + 0.7, (200, 40, 36), 6); M.cyl(x, z, 0.1, Y_WALK + 0.7, Y_WALK + 0.85, (200, 40, 36), 6)
        M.box(x - 0.25, x + 0.25, Y_WALK + 0.42, Y_WALK + 0.52, z - 0.06, z + 0.06, (200, 40, 36)); M.free()

    def bench(self, x, z, fx, fz, y=Y_WALK):
        M = self.M; M.at(x, z, 'mobiliario'); F = Frame((x, z), (-fz, fx))
        M.m('madeira'); M.prism(F.rect(-0.9, 0.9, -0.25, 0.25), y + 0.42, y + 0.48, WHITE)
        M.prism(F.rect(-0.9, 0.9, 0.22, 0.28), y + 0.48, y + 0.92, WHITE)
        M.m('metal')
        for u in (-0.75, 0.75): M.prism(F.rect(u - 0.04, u + 0.04, -0.22, 0.25), y, y + 0.42, (50, 52, 56))
        M.free()

    def bin(self, x, z):
        M = self.M; M.at(x, z, 'mobiliario'); M.m('metal'); M.cyl(x, z, 0.28, Y_WALK, Y_WALK + 0.95, (46, 80, 60), 8); M.free()

    def car(self, x, z, dx, dz, col=None, yb=Y_ASF):
        PL.car(self.M, self.rnd, x, z, dx, dz, col, yb); self.ncars += 1

    def street_species(self, i):
        return ('folhosa', 'folhosa', 'oval', 'florida', 'folhosa', 'oval', 'folhosa', 'ornamental')[i % 8]

    # ------------------------------------------------------------ ruas: postes, arvores de calcada, carros
    def near_light(self, x, z, d):
        for (a, b) in getattr(self, 'light_idx', {}).get((int(x // 20), int(z // 20)), []):
            if (a - x) ** 2 + (b - z) ** 2 < d * d: return True
        return False

    def add_light(self, x, z):
        li = self.__dict__.setdefault('light_idx', {})
        for i in range(int(x // 20) - 1, int(x // 20) + 2):
            for j in range(int(z // 20) - 1, int(z // 20) + 2): li.setdefault((i, j), []).append((x, z))

    def near_drive(self, x, z, d=1.2):
        """perto de uma entrada de carro ou caminho de porta (cada um com seu raio)"""
        for (a, b, rad) in self.drive_idx.get((int(x // 20), int(z // 20)), []):
            if math.hypot(a - x, b - z) < rad + d: return True
        return False

    def streets(self):
        P, G, r = self.P, self.G, self.rnd
        self.drive_idx = {}
        for d_ in self.drives:
            a, b = d_[0], d_[1]; rad = d_[2] if len(d_) > 2 else 3.2
            for i in range(int(a // 20) - 1, int(a // 20) + 2):
                for j in range(int(b // 20) - 1, int(b // 20) + 2): self.drive_idx.setdefault((i, j), []).append((a, b, rad))
        for pass_ in (1, 2):
          for i, rd in enumerate(P.roads):
            pr = PROFILE[rd['kind']]; pth = rd['path']
            def at(s, off=0.0):
                x, z, tx, tz = pth.at(s); return x - tz * off, z + tx * off, tx, tz
            for (s0, s1) in G.free_spans(i, pad=2.0):
                if s1 - s0 < 8: continue
                # postes: alternados de lado a cada ~32 m (avenidas: no canteiro central, duplos)
                k = 0; s = s0 + 6
                while pass_ == 1 and s < s1 - 4:
                    px, pz, tx, tz = at(s); nx, nz = -tz, tx
                    if pr['med'] > 0.5:
                        if not P.river.buffer(6).contains(Point(px, pz)): self.streetlight(px, pz, nx, nz, True)
                    else:
                        sg = 1 if k % 2 == 0 else -1
                        off = pr['road'] + (pr['verge'] * 0.5 if pr['verge'] else 0.6)
                        lx, lz = px + nx * sg * off, pz + nz * sg * off
                        if not P.river.buffer(4).contains(Point(lx, lz)) and not self.near_drive(lx, lz, 0.4): self.streetlight(lx, lz, -nx * sg, -nz * sg)
                    s += 32; k += 1
                if pass_ == 1: continue
                if rd['kind'] in ('rua', 'av'):
                    for sg in (-1, 1):
                        off = sg * (pr['road'] + pr['verge'] * 0.5 + 0.12)
                        s = s0 + r.uniform(4, 9)
                        while s < s1 - 3:
                            tx_, tz_, _, _ = at(s, off)
                            if not self.near_drive(tx_, tz_, 1.4) and not P.river.buffer(6).contains(Point(tx_, tz_)):
                                self.tree(tx_, tz_, self.street_species(i), r.uniform(0.8, 1.05), Y_LAWN + 0.02)
                            s += r.uniform(11, 14)
                elif rd['kind'] == 'centro':
                    for sg in (-1, 1):
                        off = sg * (pr['road'] + 1.4); s = s0 + 5
                        while s < s1 - 3:
                            tx_, tz_, dx, dz = at(s, off); nx, nz = -dz, dx
                            if self.near_drive(tx_, tz_, 1.6) or self.near_light(tx_, tz_, 3.0): s += 3.0; continue
                            M = self.M; M.at(tx_, tz_, 'mobiliario'); M.m('metal'); M.prism([(tx_ - 0.8, tz_ - 0.8), (tx_ + 0.8, tz_ - 0.8), (tx_ + 0.8, tz_ + 0.8), (tx_ - 0.8, tz_ + 0.8)], Y_WALK, Y_WALK + 0.06, (70, 72, 76)); M.free()
                            self.tree(tx_, tz_, 'folhosa', r.uniform(0.75, 0.95), Y_WALK + 0.06)
                            if r.random() < 0.25: self.bench(tx_ + dx * 3.5 + nx * sg * 0.6, tz_ + dz * 3.5 + nz * sg * 0.6, -nx * sg, -nz * sg)
                            if r.random() < 0.15: self.bin(tx_ - dx * 3 + nx * sg * 0.6, tz_ - dz * 3 + nz * sg * 0.6)
                            s += r.uniform(9, 12)
                elif rd['kind'] == 'orla':
                    s = s0 + 8
                    while s < s1 - 4:
                        px, pz, _, _ = at(s); self.tree(px, pz, 'palmeira', r.uniform(0.95, 1.2), 0.22); s += 16
                if pr['park']:
                    for sg in (-1, 1):
                        off = sg * (pr['road'] - 1.15)
                        s = s0 + 3
                        while s < s1 - 5:
                            cx, cz, dx, dz = at(s, off); nx, nz = -dz, dx
                            if r.random() < (0.2 if rd['kind'] == 'rua' else 0.38) and not self.near_drive(cx - nx * sg * 1.6, cz - nz * sg * 1.6, 2.6) and not P.river.buffer(6).contains(Point(cx, cz)):
                                self.car(cx, cz, dx * -sg, dz * -sg)
                            s += 6.2
                if rd['kind'] in ('rua', 'centro'):
                    s = s0 + 20
                    while s < s1 - 10:
                        hx, hz, _, _ = at(s, pr['road'] + 0.55)
                        if not self.near_drive(hx, hz, 0.6): self.hydrant(hx, hz)
                        s += 90
        # sinalizacao dos cruzamentos: semaforos onde ha avenida, PARE nas ruas de bairro
        done = set()
        for (x, z, ka, kb, i, j) in G.inter_pts:
            key = (round(x), round(z))
            if key in done: continue
            done.add(key)
            ri, rj = P.roads[i], P.roads[j]
            av = 'av' in (ka, kb) or 'orla' in (ka, kb)
            for (ra, rb) in ((ri, rj), (rj, ri)):
                pa = PROFILE[ra['kind']]
                _, _, dtx, dtz = ra['path'].at(ra['line'].project(Point(x, z))); da = (dtx, dtz)
                hb = half_row(rb['kind'])
                for sg in (-1, 1):
                    # canto de chegada (mao direita): lado direito de quem chega
                    sx = x - da[0] * sg * (hb + 1.0); sz = z - da[1] * sg * (hb + 1.0)
                    nxa, nza = -da[1], da[0]
                    side = -sg
                    px, pz = sx + nxa * side * (pa['road'] + 1.2), sz + nza * side * (pa['road'] + 1.2)
                    if P.river.buffer(4).contains(Point(px, pz)) or not P.row.contains(Point(px, pz)): continue
                    if av: self.traffic_light(px, pz, -nxa * side, -nza * side, pa['road'] - 0.5)
                    elif ra['kind'] == 'rua' and rb['kind'] != 'rua': self.stop_sign(px, pz, da[0] * sg, da[1] * sg)
                    elif ra['kind'] == 'rua' and (hash(key) + (0 if ra is ri else 1)) % 2 == 0: self.stop_sign(px, pz, da[0] * sg, da[1] * sg)

    # ------------------------------------------------------------ parques
    def central_park(self, blk):
        M = self.M; r = self.rnd; poly = blk['poly']
        minx, minz, maxx, maxz = poly.bounds; cx, cz = (minx + maxx) / 2, (minz + maxz) / 2
        lake = Point(cx + 18, cz + 12).buffer(62, 32)
        lake = Polygon([(cx + 18 + math.cos(a) * 70 * (1 + 0.12 * math.sin(3 * a)), cz + 12 + math.sin(a) * 48 * (1 + 0.1 * math.cos(2 * a))) for a in np.linspace(0, 2 * math.pi, 64, endpoint=False)])
        M.free('parques'); M.m('grama')
        # caminhos (paver): anel e diagonais
        paths = []
        ring = lake.buffer(9).exterior.buffer(2.2)
        paths.append(ring)
        for (a, b) in (((minx, minz), (maxx, maxz)), ((minx, maxz), (maxx, minz)), ((cx, minz), (cx, maxz)), ((minx, cz), (maxx, cz))):
            paths.append(LineString([a, b]).buffer(2.0))
        from shapely.ops import unary_union
        pth = unary_union(paths).intersection(poly).difference(lake.buffer(1.5))
        M.m('paver'); M.shp(pth, Y_LAWN + 0.07, WHITE)
        # lago com borda de pedra e fonte
        M.m('pedra'); ring2 = list(lake.exterior.coords)
        for k in range(len(ring2) - 1):
            a, b = ring2[k], ring2[k + 1]; M.at((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); M.wall_strip([a, b], -0.6, Y_LAWN + 0.25, 0.8, WHITE)
        M.free('parques'); M.m('agua'); M.shp(lake, Y_LAWN + 0.09, (200, 225, 215))
        fx, fz = cx + 18, cz + 12
        M.m('pedra'); M.cyl(fx, fz, 4.5, -0.3, 0.5, WHITE, 16); M.m('agua'); M.cyl(fx, fz, 4.0, 0.5, 0.52, (200, 230, 240), 16)
        M.m('liso'); M.cyl(fx, fz, 0.5, 0.5, 2.4, (235, 240, 245), 8); M.cyl(fx, fz, 1.4, 2.4, 3.6, (210, 235, 245), 8, True, 0.2)
        # coreto
        kx, kz = minx + 40, minz + 40
        M.at(kx, kz); M.m('concreto'); M.cyl(kx, kz, 6, Y_LAWN, Y_LAWN + 0.6, WHITE, 8)
        M.m('liso')
        for k in range(8):
            a = 2 * math.pi * k / 8; M.cyl(kx + math.cos(a) * 5.4, kz + math.sin(a) * 5.4, 0.15, Y_LAWN + 0.6, Y_LAWN + 3.6, (245, 245, 240), 6)
        M.m('telha'); M.cyl(kx, kz, 6.6, Y_LAWN + 3.6, Y_LAWN + 6.0, (120, 70, 60), 8, False, 0.0)
        # playground
        px, pz = maxx - 40, minz + 35
        M.at(px, pz); M.m('areia'); M.prism([(px - 12, pz - 9), (px + 12, pz - 9), (px + 12, pz + 9), (px - 12, pz + 9)], Y_LAWN, Y_LAWN + 0.08, WHITE)
        M.m('liso')
        for (dx, c) in ((-6, (220, 60, 50)), (0, (40, 120, 200)), (6, (240, 190, 40))):
            M.box(px + dx - 1.5, px + dx + 1.5, Y_LAWN, Y_LAWN + 2.2, pz - 1.5, pz + 1.5, c)
            M.box(px + dx - 1.7, px + dx + 1.7, Y_LAWN + 2.2, Y_LAWN + 2.5, pz - 1.7, pz + 1.7, shade(c, -40))
        M.quad((px - 4.5, Y_LAWN + 2.2, pz + 1.5), (px - 7.5, Y_LAWN + 2.2, pz + 1.5), (px - 7.5, Y_LAWN + 0.2, pz + 6), (px - 4.5, Y_LAWN + 0.2, pz + 6), (240, 200, 40), (0, 1, 0.5))
        M.free()
        # arvores e bancos
        for _ in range(140):
            x, z = r.uniform(minx + 4, maxx - 4), r.uniform(minz + 4, maxz - 4); p = Point(x, z)
            if lake.buffer(12).contains(p) or pth.buffer(2.5).contains(p) or Point(kx, kz).buffer(9).contains(p) or Point(px, pz).buffer(15).contains(p): continue
            self.tree(x, z, r.choice(('folhosa', 'folhosa', 'folhosa', 'conifera')), r.uniform(0.9, 1.35))
        for k in range(0, len(ring2) - 1, 5):
            a = ring2[k]; dx, dz = a[0] - fx, a[1] - fz; L = math.hypot(dx, dz) or 1
            bx, bz = a[0] + dx / L * 13, a[1] + dz / L * 13
            self.bench(bx, bz, -dx / L, -dz / L, Y_LAWN + 0.03)

    def parklight(self, x, z, y=Y_LAWN):
        """poste baixo de parque (globo)"""
        M = self.M; M.at(x, z, 'mobiliario'); self.add_light(x, z); M.m('metal'); M.cyl(x, z, 0.07, y, y + 3.6, (52, 56, 60), 6)
        M.m('liso'); M.sphere(x, y + 3.85, z, 0.32, (255, 246, 214), 6, 4); self.nlights += 1; M.free()

    def riverside(self, blk):
        """parque linear do rio: calcadao junto ao cais (postes, bancos, palmeiras), trilha sinuosa, equipamentos dos dois
        lados (quadras, playground, quiosque, coreto, jardim, lago, skate...), travessas ate a rua e bosques"""
        import park6
        from shapely.ops import unary_union
        M = self.M; r = self.rnd; poly = blk['poly']
        minx, minz, maxx, maxz = poly.bounds
        side = 1 if (minx + maxx) / 2 < river_x((minz + maxz) / 2) else -1
        QD = RIVER_W / 2 + RIVER_WALL
        xq = lambda z: river_x(z) - side * QD                    # borda do cais
        xs_ = lambda z: (minx if side > 0 else maxx)             # lado da rua (aprox.)
        wid = lambda z: abs(xq(z) - xs_(z))
        pt = lambda u, z: (xq(z) - side * u, z)                  # u = distancia do cais
        inner = poly.buffer(-2.0)
        zs = np.arange(minz + 1, maxz - 1 + 0.01, 3.0)
        # calcadao do cais
        walk = LineString([pt(4.7, z) for z in zs]).buffer(4.9, cap_style='flat').intersection(poly.buffer(0.3))         # encosta na pedra do cais (sem faixa de grama/agua)
        # trilha sinuosa no meio
        ph = r.uniform(0, 6.28)
        um = lambda z: wid(z) * 0.5 + 2 + 5.0 * math.sin(z / 19.0 + ph)
        trail_line = LineString([pt(um(z), z) for z in zs])
        trail = trail_line.buffer(1.7, cap_style='flat')
        # travessas (cais <-> rua): nas pontas, na ponte de pedestre e a cada ~70 m
        zc = [minz + 7, maxz - 7] if maxz - minz > 40 else [(minz + maxz) / 2]
        fz = self.P.footbridge[0]
        if minz + 12 < fz < maxz - 12: zc.append(fz)
        z = minz + 7 + 70
        while z < maxz - 40:
            if all(abs(z - q) > 30 for q in zc): zc.append(z)
            z += 70
        zl = getattr(self.G, 'foot_land', {}).get(-side, fz)                 # ponta da passarela deste lado (rio inclinado)
        cross = [(LineString([pt(0.5, zl), pt(14.0, zl), pt(18.0, z), pt(wid(z) + 4, z)]) if z == fz else LineString([pt(0.5, z), pt(wid(z) + 4, z)])).buffer(2.0 if z == fz else 1.6, cap_style='flat', join_style='round') for z in zc]
        paths = unary_union([trail] + cross).intersection(poly).difference(walk)
        M.free('parques'); M.m('paver')
        for z0 in range(int(minz // 60) * 60, int(maxz) + 1, 60):
            M.shp(walk.intersection(sbox(minx - 5, z0, maxx + 5, z0 + 60)), Y_LAWN + 0.05, (245, 238, 228))
            M.shp(paths.intersection(sbox(minx - 5, z0, maxx + 5, z0 + 60)), Y_LAWN + 0.05, (236, 226, 208))
        allpaths = unary_union([walk, paths])
        # trechos tematicos entre as travessas: cada trecho e um parque com cara propria (equipamentos + plantio do tema)
        from shapely.geometry import Polygon as _Pg
        if not hasattr(self, 'theme_bag'): self.theme_bag = []; self.last_theme = None
        occ = []; theme_areas = []; acc_all = []
        zcs = sorted(zc)
        bounds_z = [minz] + [(zcs[i] + zcs[i + 1]) / 2 if False else zcs[i] for i in range(len(zcs))] + [maxz]
        secs = [(bounds_z[i], bounds_z[i + 1]) for i in range(len(bounds_z) - 1) if bounds_z[i + 1] - bounds_z[i] > 24]
        for (za, zb) in secs:
            if not self.theme_bag: self.theme_bag = list(park6.THEMES); r.shuffle(self.theme_bag)
            th = self.theme_bag.pop()
            if th == self.last_theme and self.theme_bag: self.theme_bag.insert(0, th); th = self.theme_bag.pop()
            self.last_theme = th
            names, plant = park6.THEMES[th]
            todo = list(names)
            # pontos candidatos: varre o trecho nos dois lados da trilha, do centro para as pontas
            zmid = (za + zb) / 2; cand = []
            for dz in sorted(np.arange(-(zb - za) / 2 + 12, (zb - za) / 2 - 11, 4.0), key=abs):
                for lane in (0, 1): cand.append((zmid + dz, lane))
            def place_one(nm):
                fn, ha, hb = park6.STATIONS[nm]
                for (zz, lane) in cand:
                    u0, u1 = (11.5, um(zz) - 2.5) if lane == 0 else (um(zz) + 2.5, wid(zz) - 6.0)
                    for rot in ((0, 1) if u1 - u0 >= 2 * hb + 1 else ()) + ((1,) if u1 - u0 >= 2 * ha + 1 else ()):
                        aa, bb = (ha, hb) if rot == 0 else (hb, ha)
                        if u1 - u0 < 2 * bb + 0.5: continue
                        for frac in (0.5, 0.25, 0.75):
                            u = u0 + bb + (u1 - u0 - 2 * bb) * frac
                            x, _ = pt(u, zz)
                            tx = xq(zz + 2) - xq(zz - 2); tl = math.hypot(tx, 4.0); ax, az = tx / tl, 4.0 / tl
                            if rot: ax, az = az * side, -ax * side
                            F = Frame((x, zz), (ax, az))
                            fp = _Pg(F.rect(-ha, ha, -hb, hb))
                            if zz - max(ha, hb) < za + 1 or zz + max(ha, hb) > zb - 1: continue
                            if not inner.contains(fp) or fp.intersects(allpaths) or any(fp.distance(o) < 2.5 for o in occ): continue
                            park6.place(self, nm, x, zz, ax, az, r); occ.append(fp)
                            tp = trail_line.interpolate(trail_line.project(Point(x, zz)))
                            acc = LineString([(x, zz), (tp.x, tp.y)]).buffer(1.1).difference(fp).difference(allpaths).intersection(poly)
                            acc = acc.difference(unary_union(acc_all + [o for o in occ if o.geom_type == 'Polygon' and o.area > 30]))   # nao passa por cima de outro piso
                            if acc_all and acc.distance(unary_union(acc_all)) < 3.5 and acc.area > 0: acc = acc.intersection(fp.buffer(0.1))   # dois acessos paralelos colados: fica so um
                            M.free('parques'); M.m('paver'); M.shp(acc, Y_LAWN + 0.05, (236, 226, 208)); acc_all.append(acc)
                            occ.append(acc.buffer(0.5)); return True
                return False
            nst = 0
            for nm in todo: nst += place_one(nm)
            extra = ['canteiros', 'pergola', 'piquenique', 'fonte', 'quiosque', 'academia', 'canteiros', 'pergola']; r.shuffle(extra)
            for nm in extra:
                if nst >= 6: break
                nst += place_one(nm)
            theme_areas.append((za, zb, plant))
        occu = unary_union(occ).buffer(1.5) if occ else None
        blocked = allpaths.buffer(1.6) if occu is None else unary_union([allpaths.buffer(1.6), occu])
        # calcadao: postes junto ao guarda-corpo, bancos virados para o rio, palmeiras/arvores em fila
        k = 0
        for z in np.arange(minz + 6, maxz - 5, 6.0):
            if any(abs(z - q) < 3.2 for q in zc) or abs(z - zl) < 4.0: k += 1; continue
            if k % 4 == 0 and poly.contains(Point(*pt(1.3, z))): self.parklight(*pt(1.3, z))
            if k % 4 == 2 and poly.contains(Point(*pt(8.4, z))): self.bench(*pt(8.4, z), side, 0, Y_LAWN + 0.05)
            if k % 2 == 1:
                p = Point(*pt(11.0, z))
                if inner.contains(p) and not (occu is not None and occu.contains(p)) and not paths.buffer(1.5).contains(p):
                    self.tree(p.x, p.y, 'palmeira' if (k // 2) % 3 else 'folhosa', r.uniform(0.9, 1.15))
            k += 1
        # trilha: postes e bancos alternados, canteiros de flores
        L = trail_line.length; d = 8.0; k = 0
        while d < L - 6:
            p = trail_line.interpolate(d); p2 = trail_line.interpolate(d + 1.0)
            tx, tz = p2.x - p.x, p2.y - p.y; tl = math.hypot(tx, tz) or 1; nx, nz = -tz / tl, tx / tl
            s = 1 if k % 2 else -1
            q = Point(p.x + nx * s * 3.0, p.y + nz * s * 3.0)
            ok = inner.contains(q) and not blocked.buffer(-1.2).contains(q) if True else False
            if inner.contains(q) and not (occu is not None and occu.contains(q)) and not walk.buffer(1).contains(q) and all(not c.buffer(1.5).contains(q) for c in cross):
                if k % 3 == 0: self.parklight(q.x, q.y)
                elif k % 3 == 1: self.bench(q.x, q.y, -nx * s, -nz * s, Y_LAWN)
                else:
                    for j in range(3): self.tree(q.x + tx / tl * (j - 1) * 1.3 + nx * s * 0.8, q.y + tz / tl * (j - 1) * 1.3 + nz * s * 0.8, 'flores' if j != 1 else 'arbusto', r.uniform(0.85, 1.15))
            d += 9.0; k += 1
        # fila de arvores do lado da rua
        for z in np.arange(minz + 8, maxz - 6, 11.0):
            p = Point(*pt(wid(z) - 3.5, z))
            if inner.contains(p) and not blocked.contains(p): self.tree(p.x, p.y, 'oval', r.uniform(0.95, 1.2))
        # plantio de cada trecho conforme o tema: bosques em grupos (nao espalhado por igual), pomar em fileiras, mata densa...
        free_pts = []
        for (za, zb, plant) in theme_areas:
            lo_u = 13.5

            def ok(x, z, gap=5.5):
                p = Point(x, z)
                if not inner.buffer(-1.5).contains(p) or blocked.buffer(1.2).contains(p): return False
                u = abs(x - xq(z))
                if u < lo_u or u > wid(z) - 6 or z < za + 2 or z > zb - 2: return False
                return not any((x - a) ** 2 + (z - b) ** 2 < gap * gap for (a, b) in free_pts)
            if plant in ('grupos', 'bosque', 'mata', 'jardim'):
                ng = {'grupos': 3, 'bosque': 4, 'mata': 7, 'jardim': 2}[plant]
                per = {'grupos': 7, 'bosque': 9, 'mata': 14, 'jardim': 5}[plant]
                kinds = {'grupos': ('folhosa', 'oval', 'florida', 'ornamental'), 'bosque': ('folhosa', 'folhosa', 'oval', 'conifera'),
                         'mata': ('folhosa', 'conifera', 'oval', 'folhosa', 'conifera'), 'jardim': ('ornamental', 'florida', 'colunar')}[plant]
                for _ in range(ng * 6):
                    if ng <= 0: break
                    cxg, czg = r.uniform(minx, maxx), r.uniform(za + 6, zb - 6)
                    if not ok(cxg, czg, 9.0): continue
                    ng -= 1; rad = r.uniform(7, 13); kind_main = r.choice(kinds)
                    for _ in range(per * 3):
                        a_ = r.uniform(0, 6.28); d_ = rad * math.sqrt(r.random())
                        x, z = cxg + math.cos(a_) * d_, czg + math.sin(a_) * d_
                        if ok(x, z, 4.2 if plant != 'mata' else 3.6):
                            free_pts.append((x, z)); self.tree(x, z, kind_main if r.random() < 0.7 else r.choice(kinds), r.uniform(0.85, 1.3))
                    for _ in range(6):                                      # orla do bosque: arbustos e flores
                        a_ = r.uniform(0, 6.28); x, z = cxg + math.cos(a_) * (rad + 2), czg + math.sin(a_) * (rad + 2)
                        if ok(x, z, 2.0): self.tree(x, z, r.choice(('arbusto', 'flores', 'arbusto')), r.uniform(0.8, 1.1))
            # arvores soltas no gramado entre os grupos (parque, nao campo vazio)
            for _ in range(int((zb - za) * 2.2)):
                x, z = r.uniform(minx, maxx), r.uniform(za + 3, zb - 3)
                if ok(x, z, 10.0): free_pts.append((x, z)); self.tree(x, z, r.choice(('folhosa', 'oval', 'florida', 'ornamental', 'folhosa')), r.uniform(0.9, 1.3))
            if plant in ('fileiras', 'pomar', 'palmeiras'):
                kind = {'fileiras': 'colunar', 'pomar': 'frutifera', 'palmeira': 'palmeira', 'palmeiras': 'palmeira'}[plant]
                step = 6.5 if plant != 'pomar' else 5.0
                for uu in np.arange(lo_u + 2, 80, step if plant == 'pomar' else 14.0):
                    for z in np.arange(za + 4, zb - 4, step):
                        x, _ = pt(uu, z)
                        if ok(x, z, step * 0.7): free_pts.append((x, z)); self.tree(x, z, kind, r.uniform(0.9, 1.1))

    def beach(self):
        """calcadao da orla (ondas em paver), quiosques, postos de salva-vidas, guarda-sois, pier"""
        M = self.M; r = self.rnd; P = self.P
        z0 = 1688 + half_row('orla')
        for blk in P.blocks:
            if blk['zone'] != 'praia': continue
            poly = blk['poly']; minx, minz, maxx, maxz = poly.bounds
            # faixa de areia mais clara no fim do calcadao + mureta
            for x in np.arange(minx + 10, maxx - 10, 110):
                if abs(x - river_x(1700)) < 50: continue
                kx, kz = x, minz + 12
                M.at(kx, kz, 'orla'); M.m('madeira')
                M.prism([(kx - 4, kz - 3), (kx + 4, kz - 3), (kx + 4, kz + 3), (kx - 4, kz + 3)], Y_WALK, Y_WALK + 2.8, (255, 240, 220))
                M.m('vitrine'); M.quad((kx - 3.5, Y_WALK + 1.0, kz - 3.05), (kx + 3.5, Y_WALK + 1.0, kz - 3.05), (kx + 3.5, Y_WALK + 2.4, kz - 3.05), (kx - 3.5, Y_WALK + 2.4, kz - 3.05), WHITE, (0, 0, -1))
                M.m('telha'); M.cyl(kx, kz, 6.0, Y_WALK + 2.8, Y_WALK + 4.4, (200, 150, 90), 6, False, 0.1)
                M.free()
                for k in range(4):
                    a = 2 * math.pi * k / 4 + 0.4
                    self.bench(kx + math.cos(a) * 7, kz + math.sin(a) * 6 + 2, -math.cos(a), -math.sin(a))
        xs = np.arange(30, W - 30, 3.0)
        # guarda-sois e salva-vidas na areia
        for x in np.arange(60, W - 60, 160):
            if abs(x - river_x(1800)) < 60: continue
            sz = shore_z(x) - 38
            M.at(x, sz, 'orla'); M.m('madeira'); hb = self.G.h_at(x, sz)
            for (dx, dz) in ((-1.2, -1.2), (1.2, -1.2), (1.2, 1.2), (-1.2, 1.2)): M.box(x + dx - 0.1, x + dx + 0.1, hb, hb + 2.6, sz + dz - 0.1, sz + dz + 0.1, WHITE)
            M.box(x - 1.6, x + 1.6, hb + 2.6, hb + 2.8, sz - 1.6, sz + 1.6, WHITE)
            M.m('liso'); M.box(x - 1.4, x + 1.4, hb + 2.8, hb + 4.4, sz - 1.4, sz + 1.4, (230, 70, 50))
            M.m('telha'); M.cyl(x, sz, 2.2, hb + 4.4, hb + 5.3, (240, 240, 235), 4, False, 0.1)
            M.free()
        cols = [(230, 70, 60), (40, 120, 200), (245, 200, 40), (60, 170, 120), (240, 240, 240), (240, 130, 40)]
        for _ in range(260):
            x = r.uniform(40, W - 40)
            if abs(x - river_x(1800)) < 70: continue
            z = shore_z(x) - r.uniform(14, 60); hb = self.G.h_at(x, z)
            M.at(x, z, 'orla'); M.m('metal'); M.cyl(x, z, 0.04, hb, hb + 2.3, (220, 220, 220), 4)
            M.m('liso'); c = r.choice(cols)
            M.cyl(x, z, 1.4, hb + 2.0, hb + 2.45, c, 8, False, 0.05)
            if r.random() < 0.5: M.box(x + 0.6, x + 2.4, hb, hb + 0.05, z - 0.4, z + 0.4, r.choice(cols))
            M.free()
        # pier
        px = 1000.0; zA = z0 + 4; zB = shore_z(px) + 180
        M.at(px, (zA + zB) / 2, 'orla'); M.m('madeira')
        M.prism([(px - 3, zA), (px + 3, zA), (px + 3, zB), (px - 3, zB)], 1.0, 1.25, WHITE)
        for zz in np.arange(zA, zB, 6):
            hb = min(self.G.h_at(px, zz), 0.0) - 0.5
            for s in (-1, 1): M.cyl(px + s * 2.7, zz, 0.22, hb - 2, 1.0, (200, 180, 150), 6)
            M.m('liso'); M.box(px - 3, px - 2.92, 1.25, 2.3, zz - 0.04, zz + 0.04, (245, 245, 240)); M.box(px + 2.92, px + 3, 1.25, 2.3, zz - 0.04, zz + 0.04, (245, 245, 240)); M.m('madeira')
        M.m('liso'); M.box(px - 3, px - 2.92, 2.2, 2.3, zA, zB, (245, 245, 240)); M.box(px + 2.92, px + 3, 2.2, 2.3, zA, zB, (245, 245, 240))
        M.m('madeira'); M.prism([(px - 9, zB - 14), (px + 9, zB - 14), (px + 9, zB), (px - 9, zB)], 1.0, 1.25, WHITE)
        M.m('telha'); M.box(px - 6, px + 6, 4.2, 4.5, zB - 12, zB - 2, (90, 120, 150)); M.m('metal')
        for (dx, dz) in ((-5.5, -11.5), (5.5, -11.5), (5.5, -2.5), (-5.5, -2.5)): M.box(px + dx - 0.1, px + dx + 0.1, 1.25, 4.2, zB + dz - 0.1, zB + dz + 0.1, (90, 90, 95))
        # rampa do calcadao ate o pier
        M.m('madeira'); M.quad((px - 3, Y_WALK, zA - 8), (px + 3, Y_WALK, zA - 8), (px + 3, 1.25, zA), (px - 3, 1.25, zA), WHITE, (0, 1, -0.1))
        M.free()

    def marina(self, blk):
        """iate clube: sede de frente para a avenida, galpao de barcos, patio com barcos em cavaletes, estacionamento, palmeiras"""
        import centro6 as C6
        M = self.M; r = self.rnd; poly = blk['poly']; minx, minz, maxx, maxz = poly.bounds; L = self.L; B = L.B
        for _ in range(20):
            if sbox(minx, minz, maxx, maxz).buffer(-0.5).within(poly): break
            minx += 1.5; minz += 1.5; maxx -= 1.5; maxz -= 1.5
        L.lawn(poly, 'paver', Y_WALK, (236, 232, 224))
        L.pocc = []; c0 = len(B.colliders)
        # galpao (fundos, lado do rio)
        F = Frame((minx + 4, minz + 4), (1, 0)); w = 56
        M.at(minx + 4 + w / 2, minz + 16, 'lotes')
        B.box(F, 0, w, 0, 24, Y_WALK, Y_WALK + 9, (235, 235, 238), 'metal', top=False)
        B.gable(F, 0, w, 0, 24, Y_WALK + 9, 3.5, (60, 90, 120), True, 0.4, 'metal', (235, 235, 238), 'metal')
        for k in range(3): B.panel(F, 4 + k * 17, 16 + k * 17, 24, Y_WALK, Y_WALK + 6, (210, 214, 220), 'garagem', 1, 0.06, [(0, 1), (3, 1), (3, 0), (0, 0)])
        B.solid(F, 0, w, 0, 24); M.free('lotes')
        # patio de barcos em cavaletes (duas filas)
        bx0 = minx + 4 + w + 8
        for row, z in enumerate((minz + 10, minz + 26)):
            for x in np.arange(bx0 + 4, maxx - 8, 8.5):
                M.at(x, z, 'orla'); M.m('metal')
                for dz in (-2.2, 2.2):
                    M.box(x - 1.2, x + 1.2, Y_WALK, Y_WALK + 0.9, z + dz - 0.12, z + dz + 0.12, (60, 90, 150))
                self.boat(x, z, 0, 1, Y_WALK + 1.25)
        L.pocc.append(sbox(bx0, minz + 3, maxx - 2, minz + 33))
        # sede do clube + predio de frente para a Beira-Mar
        s = 2.0
        for (pw, fl, tex) in ((46, 3, 'moderna'), (34, 6, 'janelas'), (40, 4, 'moderna')):
            if s + pw > (maxx - minx) - 4: break
            Fs = L.frame('S', minx, maxx, minz, maxz, s)
            M.at(*Fs.xz(pw / 2, 9), 'lotes'); C6.midrise(B, Fs, pw - 0.15, 18, fl, None, None, True, None, True, tex); M.free('lotes')
            s += pw + 10
        # estacionamento no miolo
        pz0, pz1 = minz + 38, maxz - 24
        if pz1 - pz0 > 14:
            Fp = Frame((minx + 6, pz0), (1, 0)); M.at((minx + maxx) / 2, (pz0 + pz1) / 2, 'lotes')
            B.parking(Fp, 0, (maxx - minx) * 0.55, 0, pz1 - pz0, L.park_car, Y_WALK + 0.01); M.free('lotes')
            L.pocc.append(sbox(minx + 5, pz0 - 1, minx + 7 + (maxx - minx) * 0.55, pz1 + 1))
            zc = (pz0 + pz1) / 2; L.access(L.frame('W', minx, maxx, minz, maxz, maxz - zc - 3.6), 0.0, 7.2, 6.2)
        L.fill_free(poly, c0, (), True, 3, ('quiosque', 'jardim', 'coreto', 'piquenique'))

    def boat(self, x, z, dx, dz, y=Y_SEA, kind=None, L=None):
        """barco atracado: lancha, veleiro (mastro, retranca, vela enrolada) ou iate de dois andares; casco com proa
        afilada, faixa colorida, convés de madeira e para-brisa"""
        M = self.M; r = self.rnd; M.at(x, z, 'orla'); F = Frame((x, z), (dx, dz))
        kind = kind or r.choice(('lancha', 'lancha', 'veleiro', 'veleiro', 'iate'))
        L = L or {'lancha': r.uniform(6, 9), 'veleiro': r.uniform(8, 12), 'iate': r.uniform(13, 18)}[kind]
        Wd = L * (0.34 if kind != 'veleiro' else 0.3); stripe = r.choice(((30, 60, 120), (180, 40, 40), (20, 110, 110), (40, 40, 44), (240, 190, 40)))
        hull = (248, 248, 246) if r.random() < 0.8 else r.choice(((30, 50, 90), (40, 40, 44)))
        M.m('liso')
        out = [(-L / 2, -Wd * 0.45), (L * 0.15, -Wd / 2), (L * 0.38, -Wd * 0.38), (L / 2, 0), (L * 0.38, Wd * 0.38), (L * 0.15, Wd / 2), (-L / 2, Wd * 0.45)]
        bot = [(u * 0.92, v * 0.7) for (u, v) in out]
        hb = 0.9 if kind != 'iate' else 1.4
        for k in range(len(out)):                                         # casco em V (de baixo estreito para cima largo)
            a0, a1 = out[k], out[(k + 1) % len(out)]; b0, b1 = bot[k], bot[(k + 1) % len(out)]
            M.quad(F.p(b0[0], b0[1], y - 0.35), F.p(b1[0], b1[1], y - 0.35), F.p(a1[0], a1[1], y + hb), F.p(a0[0], a0[1], y + hb), hull, (0, 0.1, 0))
            M.quad(F.p(a0[0], a0[1], y + hb - 0.35), F.p(a1[0], a1[1], y + hb - 0.35), F.p(a1[0] * 1.002, a1[1] * 1.002, y + hb - 0.2), F.p(a0[0] * 1.002, a0[1] * 1.002, y + hb - 0.2), stripe, (0, 0, 0))
        M.m('madeira'); M.poly([F.p(u, v, y + hb) for (u, v) in out[::-1]], (190, 150, 110), (0, 1, 0))
        M.m('liso')
        if kind == 'lancha':
            M.prism(F.rect(-L * 0.1, L * 0.12, -Wd * 0.32, Wd * 0.32), y + hb, y + hb + 0.6, (240, 240, 238))
            M.quad(F.p(L * 0.12, -Wd * 0.32, y + hb + 0.6), F.p(L * 0.12, Wd * 0.32, y + hb + 0.6), F.p(L * 0.2, Wd * 0.3, y + hb + 1.2), F.p(L * 0.2, -Wd * 0.3, y + hb + 1.2), (60, 80, 100), F.nu(1))
            M.prism(F.rect(-L / 2 + 0.1, -L / 2 + 0.5, -0.3, 0.3), y - 0.2, y + 0.9, (40, 40, 44))                      # motor de popa
        elif kind == 'veleiro':
            M.prism(F.rect(-L * 0.25, L * 0.05, -Wd * 0.28, Wd * 0.28), y + hb, y + hb + 0.7, (244, 244, 240))
            mx, mz = F.xz(L * 0.1, 0); hm = L * 1.25
            M.m('metal'); M.cyl(mx, mz, 0.07, y + hb, y + hb + hm, (220, 222, 226), 5, False)
            M.box(*sorted((F.xz(L * 0.1, 0)[0], F.xz(-L * 0.35, 0)[0])), y + hb + 1.3, y + hb + 1.45, *(lambda a_, b_: (min(a_, b_) - 0.06, max(a_, b_) + 0.06))(F.xz(L * 0.1, 0)[1], F.xz(-L * 0.35, 0)[1]), (220, 222, 226))
            M.m('liso'); M.prism(F.rect(-L * 0.33, L * 0.08, -0.18, 0.18), y + hb + 1.45, y + hb + 1.8, (40, 70, 130))   # capa da vela
            M.quad(F.p(L * 0.1, 0, y + hb + hm), F.p(L / 2, 0, y + hb), F.p(L / 2, 0.02, y + hb), F.p(L * 0.1, 0.02, y + hb + hm), (200, 200, 205), (0, 0, 1))   # estai
        else:
            M.prism(F.rect(-L * 0.35, L * 0.2, -Wd * 0.4, Wd * 0.4), y + hb, y + hb + 1.6, (246, 246, 244))
            M.prism(F.rect(-L * 0.3, L * 0.2, -Wd * 0.41, Wd * 0.41), y + hb + 0.7, y + hb + 1.3, (40, 50, 62))
            M.prism(F.rect(-L * 0.25, L * 0.05, -Wd * 0.32, Wd * 0.32), y + hb + 1.6, y + hb + 2.6, (246, 246, 244))
            M.prism(F.rect(-L * 0.22, L * 0.05, -Wd * 0.33, Wd * 0.33), y + hb + 1.9, y + hb + 2.4, (40, 50, 62))
            M.cyl(*F.xz(-L * 0.05, 0), 0.06, y + hb + 2.6, y + hb + 4.0, (220, 222, 226), 5, False)
        M.free()

    def harbor(self):
        """MARINA: bacia protegida por dois quebra-mares (passeio de concreto por cima, guarda-corpo, postes e faroletes
        vermelho/verde na boca), cais largo de concreto ao longo da praia (borda de granito, cabecos, postes, bancos,
        palmeiras), clube nautico de dois andares, capitania com torre, posto de combustivel, portico de icar barcos,
        e cinco pieres flutuantes com rampas e fingers cheios de lanchas, veleiros e iates"""
        M = self.M; r = self.rnd
        px = river_x(1760) + 205.0
        zS = shore_z(px); yq = 0.9; yp = Y_SEA + 0.45
        X0, X1 = px - 100.0, px + 112.0
        QZ0, QZ1 = zS - 8.0, zS + 16.0                         # cais
        def slab(x0, x1, z0, z1, y, mat='concreto', col=(214, 210, 202), th=0.6, piles=True, layer='pier'):
            z = z0
            while z < z1:
                zz = min(z + 12, z1)
                M.at((x0 + x1) / 2, (z + zz) / 2, layer); M.m(mat)
                M.prism([(x0, z), (x1, z), (x1, zz), (x0, zz)], y - th, y, col, True, True)
                if piles:
                    M.m('concreto')
                    for xx in np.arange(x0 + 0.8, x1, 6.0):
                        for zp in np.arange(z + 1, zz, 6.0):
                            hb = -1.0 if zp < zS else -1.5 - min((zp - zS) / 120, 1) * 5.0
                            M.cyl(xx, zp, 0.35, hb - 1, y - th, (190, 186, 178), 6, False)
                M.free(); z = zz
        x = X0
        while x < X1:
            x1 = min(x + 30, X1); slab(x, x1, QZ0, QZ1, yq); x = x1
        # borda de granito com cabecos, postes, bancos, palmeiras em floreiras
        M.at(px, QZ1, 'orla'); M.m('pedra'); M.prism([(X0, QZ1 - 0.6), (X1, QZ1 - 0.6), (X1, QZ1), (X0, QZ1)], yq - 0.2, yq + 0.08, (196, 190, 182))
        M.m('pedra'); M.prism([(X0, QZ1 - 0.05), (X1, QZ1 - 0.05), (X1, QZ1 + 0.3), (X0, QZ1 + 0.3)], -3.0, yq + 0.08, (150, 146, 140), False)
        for xx in np.arange(X0 + 3, X1, 7.0):
            M.m('metal'); M.cyl(xx, QZ1 - 0.9, 0.2, yq, yq + 0.5, (40, 42, 46), 8); M.cyl(xx, QZ1 - 0.9, 0.3, yq + 0.5, yq + 0.6, (40, 42, 46), 8)
        M.free()
        for xx in np.arange(X0 + 6, X1, 16.0):
            self.parklight(xx, QZ1 - 2.2, yq)
            self.bench(xx + 8, QZ1 - 2.4, 0, 1, yq)
        for xx in np.arange(X0 + 14, X1, 32.0):
            M.at(xx, QZ0 + 6, 'orla'); M.m('pedra'); M.box(xx - 1.5, xx + 1.5, yq, yq + 0.6, QZ0 + 4.5, QZ0 + 7.5, (214, 206, 192)); M.free()
            self.tree(xx, QZ0 + 6, 'palmeira', r.uniform(1.1, 1.5), yq + 0.6)
        # pieres flutuantes com rampa (gangway) e fingers
        PZ1 = zS + 125.0
        for k, pxk in enumerate((px - 78, px - 44, px - 10, px + 24, px + 58, px + 92)):
            z = QZ1 + 6.0
            M.at(pxk, (QZ1 + z) / 2, 'pier'); M.m('metal')
            M.quad((pxk - 1.0, yq, QZ1), (pxk + 1.0, yq, QZ1), (pxk + 1.0, yp, z), (pxk - 1.0, yp, z), (170, 172, 176), (0, 1, 0))
            for s_ in (-1, 1):
                M.quad((pxk + s_ * 1.0, yq + 1.0, QZ1), (pxk + s_ * 1.0, yp + 1.0, z), (pxk + s_ * 1.0, yp + 1.08, z), (pxk + s_ * 1.0, yq + 1.08, QZ1), (200, 202, 206), (s_, 0, 0))
            M.free()
            zend = PZ1 - (12 if k in (0, 5) else 0)
            slab(pxk - 1.6, pxk + 1.6, z, zend, yp, 'concreto', (176, 178, 180), 0.5, False)
            M.at(pxk, (z + zend) / 2, 'orla'); M.m('metal')
            for zz in np.arange(z + 4, zend, 12.0):
                for s_ in (-1, 1): M.cyl(pxk + s_ * 2.2, zz, 0.22, -4.0, yp + 1.6, (90, 94, 100), 8, False)
            M.free()
            for zz in np.arange(z + 4, zend - 2, 9.5):
                for s_ in (-1, 1):
                    if (k == 0 and s_ < 0) or (k == 5 and s_ > 0): continue
                    M.at(pxk + s_ * 6, zz, 'pier'); M.m('concreto')
                    M.prism([(min(pxk + s_ * 1.6, pxk + s_ * 11), zz - 0.5), (max(pxk + s_ * 1.6, pxk + s_ * 11), zz - 0.5), (max(pxk + s_ * 1.6, pxk + s_ * 11), zz + 0.5), (min(pxk + s_ * 1.6, pxk + s_ * 11), zz + 0.5)], yp - 0.4, yp, (176, 178, 180), True, True)
                    M.m('metal'); M.cyl(pxk + s_ * 10.6, zz, 0.12, yp, yp + 0.3, (240, 240, 240), 6); M.free()
                    if r.random() < 0.85:
                        kind = r.choice(('lancha', 'lancha', 'veleiro', 'veleiro', 'iate')) if zz < PZ1 - 30 else r.choice(('iate', 'veleiro'))
                        self.boat(pxk + s_ * 7.0, zz + 4.75, s_, 0, Y_SEA + 0.1, kind)
            M.at(pxk, zend, 'orla'); M.m('liso'); M.cyl(pxk, zend - 1.0, 0.1, yp, yp + 2.6, (240, 240, 240), 5, False); M.sphere(pxk, yp + 2.8, zend - 1.0, 0.2, (255, 246, 214), 5, 3); M.free()
        # quebra-mares (oeste e leste) com passeio por cima e a boca da marina ao sul
        def breakwater(pts, beacon_col):
            for i in range(len(pts) - 1):
                (ax, az), (bx, bz) = pts[i], pts[i + 1]
                L = math.hypot(bx - ax, bz - az); ux, uz = (bx - ax) / L, (bz - az) / L; nx, nz = -uz, ux
                M.at((ax + bx) / 2, (az + bz) / 2, 'pier'); M.m('concreto')
                M.prism([(ax - nx * 2.4, az - nz * 2.4), (bx - nx * 2.4, bz - nz * 2.4), (bx + nx * 2.4, bz + nz * 2.4), (ax + nx * 2.4, az + nz * 2.4)], -3.5, 1.6, (206, 202, 194), True)
                M.m('pedra')
                for t in np.arange(0.8, L, 1.8):
                    for s_ in (-1, 1):
                        for j in range(2):
                            cx_, cz_ = ax + ux * t + nx * s_ * (3.2 + j * 1.4), az + uz * t + nz * s_ * (3.2 + j * 1.4)
                            M.sphere(cx_, -0.4 + (0.6 if j == 0 else -0.2), cz_, r.uniform(1.0, 1.5), r.choice(((150, 146, 138), (128, 124, 118), (170, 164, 152))), 6, 3, 0.75, 0.18, r)
                M.m('metal')
                for s_ in (-1, 1):
                    M.quad((ax + nx * s_ * 2.3, 2.6, az + nz * s_ * 2.3), (bx + nx * s_ * 2.3, 2.6, bz + nz * s_ * 2.3), (bx + nx * s_ * 2.3, 2.7, bz + nz * s_ * 2.3), (ax + nx * s_ * 2.3, 2.7, az + nz * s_ * 2.3), (60, 64, 70), (nx * s_, 0, nz * s_))
                    for t in np.arange(0, L, 3.0): M.box(ax + ux * t + nx * s_ * 2.3 - 0.04, ax + ux * t + nx * s_ * 2.3 + 0.04, 1.6, 2.7, az + uz * t + nz * s_ * 2.3 - 0.04, az + uz * t + nz * s_ * 2.3 + 0.04, (60, 64, 70))
                M.free()
                if i % 2 == 0: self.parklight(ax + nx * 1.6, az + nz * 1.6, 1.6)
            (ex, ez) = pts[-1]
            M.at(ex, ez, 'orla'); M.m('reboco'); M.cyl(ex, ez, 1.1, 1.6, 7.0, (240, 238, 232), 10, False, 0.8)
            M.cyl(ex, ez, 0.95, 3.0, 4.6, beacon_col, 10, False, 0.9); M.m('vidro'); M.cyl(ex, ez, 0.5, 7.0, 8.0, (220, 240, 240), 8, False)
            M.m('liso'); M.sphere(ex, 7.5, ez, 0.3, beacon_col, 6, 4); M.m('reboco'); M.cyl(ex, ez, 0.65, 8.0, 8.6, beacon_col, 8, False, 0.1); M.free()
            self.luzes.append({'tipo': 'farolete', 'x': round(ex, 2), 'y': 7.5, 'z': round(ez, 2), 'cor': list(beacon_col), 'alcance_m': 250, 'pisca_s': 2.0})
        west = [(px - 112, QZ0 + 4)] + [(px - 112 + 70 * (1 - math.cos(t)), zS + 30 + 120 * math.sin(t)) for t in np.linspace(0, math.pi / 2, 7)][1:] + [(px + 18, zS + 150)]
        east = [(px + 124, QZ0 + 4), (px + 124, zS + 110)] + [(px + 124 - 50 * (1 - math.cos(t)), zS + 110 + 30 * math.sin(t)) for t in np.linspace(0, math.pi / 2, 5)][1:] + [(px + 60, zS + 142)]
        breakwater(west, (220, 50, 40)); breakwater(east, (40, 170, 80))
        # clube nautico (2 andares, vidro, terraco com guarda-sois), capitania com torre, posto de combustivel, portico
        cx0, cz0 = px - 60.0, QZ0 + 1.0
        M.at(cx0 + 15, cz0 + 6, 'orla'); M.m('reboco'); M.box(cx0, cx0 + 30, yq, yq + 7.6, cz0, cz0 + 11, (248, 246, 240), top=False)
        M.m('vidro')
        for yy in (yq + 0.6, yq + 4.4): M.quad((cx0 + 1, yy, cz0 + 11.03), (cx0 + 29, yy, cz0 + 11.03), (cx0 + 29, yy + 2.7, cz0 + 11.03), (cx0 + 1, yy + 2.7, cz0 + 11.03), WHITE, (0, 0, 1))
        M.m('concreto'); M.box(cx0 - 1, cx0 + 31, yq + 3.8, yq + 4.1, cz0 - 0.5, cz0 + 14.5, (240, 238, 232)); M.box(cx0 - 1.5, cx0 + 31.5, yq + 7.6, yq + 8.0, cz0 - 1, cz0 + 13, (240, 238, 232))
        M.m('liso')
        for xx in np.arange(cx0 - 1, cx0 + 31.1, 1.5): M.box(xx - 0.03, xx + 0.03, yq + 4.1, yq + 5.1, cz0 + 14.4, cz0 + 14.5, (200, 220, 230))
        M.box(cx0 - 1, cx0 + 31, yq + 5.05, yq + 5.15, cz0 + 14.4, cz0 + 14.5, (240, 240, 240))
        M.box(cx0 + 8, cx0 + 22, yq + 8.0, yq + 9.2, cz0 + 11.5, cz0 + 11.7, (30, 70, 130))
        M.free()
        for k in range(4): umbrella_marina(self, cx0 + 4 + k * 7.5, cz0 + 13.0, yq + 4.1, r)
        hx, hz = px + 40.0, QZ0 + 6.0
        M.at(hx, hz, 'orla'); M.m('reboco'); M.box(hx - 5, hx + 5, yq, yq + 6.4, hz - 4, hz + 4, (246, 244, 238), top=False)
        M.m('vidro'); M.quad((hx - 4.5, yq + 1, hz + 4.03), (hx + 4.5, yq + 1, hz + 4.03), (hx + 4.5, yq + 5.6, hz + 4.03), (hx - 4.5, yq + 5.6, hz + 4.03), WHITE, (0, 0, 1))
        M.m('concreto'); M.box(hx - 5.5, hx + 5.5, yq + 6.4, yq + 6.8, hz - 4.5, hz + 4.5, (236, 234, 228))
        M.m('reboco'); M.box(hx - 1.8, hx + 1.8, yq + 6.8, yq + 12.0, hz - 1.8, hz + 1.8, (246, 244, 238), top=False)
        M.m('vidro'); M.cyl(hx, hz, 2.1, yq + 10.0, yq + 11.8, WHITE, 8, False)
        M.m('telha'); M.cyl(hx, hz, 2.6, yq + 12.0, yq + 13.8, (40, 90, 140), 8, False, 0.1)
        M.m('metal'); M.cyl(hx + 1.4, hz, 0.04, yq + 13.0, yq + 18.0, (220, 222, 226), 4, False)
        M.m('liso'); M.box(hx + 1.45, hx + 2.9, yq + 16.9, yq + 17.7, hz - 0.02, hz + 0.02, (40, 90, 160))
        M.free()
        self.luzes.append({'tipo': 'capitania', 'x': round(hx, 2), 'y': round(yq + 11, 2), 'z': round(hz, 2), 'cor': [255, 240, 200], 'alcance_m': 150})
        fx, fz = px + 80.0, QZ1 - 4.0
        M.at(fx, fz, 'orla'); M.m('liso'); M.box(fx - 4, fx + 4, yq + 3.6, yq + 4.0, fz - 3, fz + 3, (220, 60, 50))
        for dx in (-3.6, 3.6):
            for dz in (-2.6, 2.6): M.box(fx + dx - 0.12, fx + dx + 0.12, yq, yq + 3.6, fz + dz - 0.12, fz + dz + 0.12, (240, 240, 240))
        for dx in (-1.6, 1.6): M.box(fx + dx - 0.4, fx + dx + 0.4, yq, yq + 1.7, fz - 0.3, fz + 0.3, (250, 250, 248)); M.box(fx + dx - 0.35, fx + dx + 0.35, yq + 1.0, yq + 1.5, fz + 0.3, fz + 0.32, (40, 44, 50))
        M.free()
        gx, gz = px + 100.0, QZ1 + 2.0                         # portico de icar barcos (travel lift) sobre a doca
        M.at(gx, gz, 'orla'); M.m('metal'); blue = (40, 90, 170)
        for dx in (-3.5, 3.5):
            for dz in (-4, 4): M.box(gx + dx - 0.25, gx + dx + 0.25, yq, yq + 8.0, gz + dz - 0.25, gz + dz + 0.25, blue)
            M.box(gx + dx - 0.3, gx + dx + 0.3, yq + 7.6, yq + 8.4, gz - 4.3, gz + 4.3, blue)
        M.box(gx - 3.8, gx + 3.8, yq + 8.0, yq + 8.6, gz - 0.3, gz + 0.3, blue)
        for dx in (-3.5, 3.5):
            for dz in (-4, 4): M.cyl(gx + dx, gz + dz, 0.45, yq - 0.2, yq + 0.6, (30, 30, 32), 8)
        M.free()
        self.boat(gx, gz, 0, 1, yq + 2.2, 'lancha', 8.0)
        M.at(gx, gz, 'orla'); M.m('metal')
        for dz in (-2.0, 2.0): M.box(gx - 0.03, gx + 0.03, yq + 2.0, yq + 8.0, gz + dz - 0.03, gz + dz + 0.03, (60, 60, 64))
        M.free()


    def forest(self):
        """mata fechada nos morros das bordas"""
        r = self.rnd; G = self.G
        n = 0; tries = 0
        while n < 2600 and tries < 60000:
            tries += 1
            side = r.random()
            if side < 0.5: x, z = r.uniform(0, W), r.uniform(0, 150)
            elif side < 0.75: x, z = r.uniform(0, 140), r.uniform(0, 1700)
            else: x, z = r.uniform(W - 140, W), r.uniform(0, 1700)
            h = G.h_at(x, z)
            if h < 1.5: continue
            if self.P.row.buffer(8).contains(Point(x, z)): continue
            self.layer_tree = 'mata'; self.tree(x, z, r.choice(('conifera', 'conifera', 'folhosa')), r.uniform(1.0, 1.6), h - 0.3); self.layer_tree = None
            n += 1

    def build(self):
        self.streets()
        for blk in self.P.blocks:
            if blk['zone'] == 'marina' and not blk.get('feito'): self.marina(blk)         # antes: ela ainda pede arvores/bancos ao Lots
        for t in self.L.trees: self.tree(t[0], t[1], t[2], t[3], t[4] if len(t) > 4 else Y_LAWN)
        for c in self.L.parked: self.car(c[0], c[1], c[2], c[3], None, c[4] if len(c) > 4 else Y_LAWN + 0.04)
        for b in self.L.benches: self.bench(b[0], b[1], b[2], b[3], b[4] if len(b) > 4 else Y_LAWN + 0.09)
        for q in getattr(self.L, 'plights', []): self.parklight(*q)
        for blk in self.P.blocks:
            if blk['zone'] == 'parque': self.central_park(blk)
            elif blk['zone'] == 'ribeirinho': self.riverside(blk)
        import orla6; orla6.build(self.P, self.G, self.L, self.M, self)
        self.forest()
        print(f'  vida: {self.ntrees} arvores, {self.nlights} postes, {self.ncars} carros')
        return self


def umbrella_marina(pr, x, z, y, r):
    M = pr.M; M.at(x, z, 'orla'); M.m('liso'); col = (30, 70, 130) if r.random() < 0.5 else (250, 250, 246)
    M.cyl(x, z, 0.04, y, y + 2.4, (230, 230, 230), 5, False); M.cyl(x, z, 1.5, y + 2.1, y + 2.5, col, 8, False, 0.05)
    M.cyl(x, z, 0.5, y + 0.72, y + 0.76, (250, 250, 248), 8); M.free()
