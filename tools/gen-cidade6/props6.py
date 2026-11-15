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
        self.nlights = 0; self.ncars = 0; self.ntrees = 0; self.app_trees = []

    # ------------------------------------------------------------ arvores
    APP_TREE = {'folhosa': (0, 1), 'oval': (1, 0), 'ornamental': (1,), 'frutifera': (0,), 'conifera': (3,)}

    def tree(self, x, z, kind='folhosa', sc=1.0, y=Y_LAWN, lod=1):
        """arvores comuns vao para a camada 'arvores' (no jogo viram as arvores modeladas do proprio app: lista app_trees);
        palmeiras, floridas, colunares, arbustos, flores e cercas vivas ficam na camada 'vegetacao' (malha propria)"""
        mata = getattr(self, 'layer_tree', None) == 'mata'
        if kind in self.APP_TREE:
            layer = 'mata' if mata else 'arvores'
            sp = self.rnd.choice(self.APP_TREE[kind])
            self.app_trees.append([round(x, 1), round(z, 1), sp, round(sc * (0.62 if kind in ('ornamental', 'frutifera') else 1.0), 2), round(self.rnd.uniform(0, 6.28), 2), round(self.rnd.random(), 2)])
        else: layer = 'vegetacao'
        PL.tree(self.M, self.rnd, x, z, kind, sc, y, layer, 0 if mata else lod)
        self.ntrees += 1

    # ------------------------------------------------------------ mobiliario urbano
    def streetlight(self, x, z, nx, nz, double=False):
        """poste: base na calcada, braco sobre a pista (nx, nz = direcao da pista)"""
        M = self.M; M.at(x, z, 'mobiliario')
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
        for i, rd in enumerate(P.roads):
            pr = PROFILE[rd['kind']]; pth = rd['path']
            def at(s, off=0.0):
                x, z, tx, tz = pth.at(s); return x - tz * off, z + tx * off, tx, tz
            for (s0, s1) in G.free_spans(i, pad=2.0):
                if s1 - s0 < 8: continue
                # postes: alternados de lado a cada ~32 m (avenidas: no canteiro central, duplos)
                k = 0; s = s0 + 6
                while s < s1 - 4:
                    px, pz, tx, tz = at(s); nx, nz = -tz, tx
                    if pr['med'] > 0.5:
                        if not P.river.buffer(6).contains(Point(px, pz)): self.streetlight(px, pz, nx, nz, True)
                    else:
                        sg = 1 if k % 2 == 0 else -1
                        off = pr['road'] + (pr['verge'] * 0.5 if pr['verge'] else 0.6)
                        lx, lz = px + nx * sg * off, pz + nz * sg * off
                        if not P.river.buffer(4).contains(Point(lx, lz)) and not self.near_drive(lx, lz, 0.4): self.streetlight(lx, lz, -nx * sg, -nz * sg)
                    s += 32; k += 1
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
        M.m('paver'); M.shp(pth, Y_LAWN + 0.03, WHITE)
        # lago com borda de pedra e fonte
        M.m('pedra'); ring2 = list(lake.exterior.coords)
        for k in range(len(ring2) - 1):
            a, b = ring2[k], ring2[k + 1]; M.at((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); M.wall_strip([a, b], -0.6, Y_LAWN + 0.25, 0.8, WHITE)
        M.free('parques'); M.m('agua'); M.shp(lake, 0.03, (200, 225, 215))
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
        M = self.M; M.at(x, z, 'mobiliario'); M.m('metal'); M.cyl(x, z, 0.07, y, y + 3.6, (52, 56, 60), 6)
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
        walk = LineString([pt(5.0, z) for z in zs]).buffer(4.5, cap_style='flat').intersection(poly)
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
        cross = [LineString([pt(0.5, z), pt(wid(z) + 4, z)]).buffer(2.0 if z == fz else 1.6, cap_style='flat') for z in zc]
        paths = unary_union([trail] + cross).intersection(poly).difference(walk)
        M.free('parques'); M.m('paver')
        for z0 in range(int(minz // 60) * 60, int(maxz) + 1, 60):
            M.shp(walk.intersection(sbox(minx - 5, z0, maxx + 5, z0 + 60)), Y_LAWN + 0.05, (245, 238, 228))
            M.shp(paths.intersection(sbox(minx - 5, z0, maxx + 5, z0 + 60)), Y_LAWN + 0.05, (236, 226, 208))
        allpaths = unary_union([walk, paths])
        # equipamentos: um de cada lado da trilha a cada ~46 m
        names = list(park6.STATIONS); r.shuffle(names); ni = 0
        occ = []
        z = minz + 30
        while z < maxz - 24:
            for lane in (0, 1):
                for _try in range(len(names)):
                    nm = names[_try]
                    fn, ha, hb = park6.STATIONS[nm]
                    u0, u1 = (11.5, um(z) - 5.5 - 2) if lane == 0 else (um(z) + 5.5 + 2, wid(z) - 4)
                    if u1 - u0 < 2 * hb: continue
                    u = (u0 + u1) / 2 + r.uniform(-1, 1) * max(0.0, (u1 - u0) / 2 - hb) * 0.5
                    zz = z + r.uniform(-3, 3)
                    x, _ = pt(u, zz)
                    tx = xq(zz + 2) - xq(zz - 2); tl = math.hypot(tx, 4.0)
                    from shapely.geometry import Polygon as _Pg
                    F = Frame((x, zz), (tx / tl, 4.0 / tl))
                    fp = _Pg(F.rect(-ha, ha, -hb, hb))
                    if not inner.contains(fp) or fp.intersects(allpaths) or any(fp.distance(o) < 3 for o in occ): continue
                    park6.place(self, nm, x, zz, tx / tl, 4.0 / tl, r); occ.append(fp); names.remove(nm); names.append(nm)
                    # acesso: do equipamento ate a trilha
                    tp = trail_line.interpolate(trail_line.project(Point(x, zz)))
                    acc = LineString([(x, zz), (tp.x, tp.y)]).buffer(1.1).difference(fp).difference(allpaths).intersection(poly)
                    M.free('parques'); M.m('paver'); M.shp(acc, Y_LAWN + 0.05, (236, 226, 208))
                    occ.append(acc.buffer(0.5))
                    break
            z += 40
        occu = unary_union(occ).buffer(1.5) if occ else None
        blocked = allpaths.buffer(1.6) if occu is None else unary_union([allpaths.buffer(1.6), occu])
        # calcadao: postes junto ao guarda-corpo, bancos virados para o rio, palmeiras/arvores em fila
        k = 0
        for z in np.arange(minz + 6, maxz - 5, 6.0):
            if any(abs(z - q) < 3.2 for q in zc): k += 1; continue
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
        # fila de arvores do lado da rua e bosques no resto
        for z in np.arange(minz + 8, maxz - 6, 11.0):
            p = Point(*pt(wid(z) - 3.5, z))
            if inner.contains(p) and not blocked.contains(p): self.tree(p.x, p.y, self.street_species(int(z // 200)) if hasattr(self, 'street_species') and False else 'oval', r.uniform(0.95, 1.2))
        pts = []
        for _ in range(int(poly.area / 85)):
            x, z = r.uniform(minx, maxx), r.uniform(minz, maxz); p = Point(x, z)
            if not inner.buffer(-1.5).contains(p) or blocked.buffer(1.2).contains(p): continue
            u = abs(x - xq(z))
            if u < 13.5 or u > wid(z) - 6: continue
            if any((x - a) ** 2 + (z - b) ** 2 < 30 for (a, b) in pts): continue
            pts.append((x, z))
            kd = r.choice(('folhosa', 'folhosa', 'oval', 'conifera', 'florida', 'ornamental', 'frutifera', 'arbusto'))
            self.tree(x, z, kd, r.uniform(0.9, 1.3))

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
        L.fill_free(poly, c0, (), True, 3, ('quiosque', 'jardim', 'coreto', 'piquenique'))

    def boat(self, x, z, dx, dz, y=Y_SEA):
        M = self.M; r = self.rnd; M.at(x, z, 'orla'); F = Frame((x, z), (dx, dz))
        L, Wd = r.uniform(6, 10), r.uniform(2.2, 3.0)
        M.m('liso'); hull = (245, 245, 242)
        pts = [F.xz(-L / 2, -Wd / 2), F.xz(L * 0.25, -Wd / 2), F.xz(L / 2, 0), F.xz(L * 0.25, Wd / 2), F.xz(-L / 2, Wd / 2)]
        M.prism(pts, y - 0.2, y + 0.9, hull, True, False, (170, 120, 80))
        M.prism(F.rect(-L * 0.3, L * 0.05, -Wd * 0.3, Wd * 0.3), y + 0.9, y + 2.0, (235, 238, 240))
        M.box(*(lambda p: (p[0] - 0.05, p[0] + 0.05))(F.xz(0, 0)), y + 2.0, y + 2.0 + (8 if r.random() < 0.4 else 0.3), *(lambda p: (p[1] - 0.05, p[1] + 0.05))(F.xz(0, 0)), (200, 200, 205))
        M.free()

    def harbor(self):
        """pieres flutuantes e barcos na foz do rio e no mar perto da marina"""
        M = self.M; r = self.rnd
        x0 = river_x(1760) + 60
        for k in range(3):
            px = x0 + 40 + k * 70; zA = shore_z(px) - 6; zB = shore_z(px) + 70
            M.at(px, (zA + zB) / 2, 'orla'); M.m('madeira')
            M.prism([(px - 1.5, zA), (px + 1.5, zA), (px + 1.5, zB), (px - 1.5, zB)], 0.2, 0.5, WHITE)
            M.prism([(px - 1.5, 1718.6), (px + 1.5, 1718.6), (px + 1.5, zA), (px - 1.5, zA)], 0.2, 0.5, WHITE)       # passarela sobre a areia, da mureta ate o pier
            for zz in np.arange(1722.0, zA, 6.0):
                for s in (-1.3, 1.3): M.cyl(px + s, zz, 0.14, -1.6, 0.2, (120, 92, 66), 6)
            for s in (-1.45, 1.45):
                M.prism([(px + s - 0.04, 1718.6), (px + s + 0.04, 1718.6), (px + s + 0.04, zB), (px + s - 0.04, zB)], 1.25, 1.33, (240, 238, 232))
                for zz in np.arange(1719.0, zB, 3.0): M.prism([(px + s - 0.04, zz - 0.04), (px + s + 0.04, zz - 0.04), (px + s + 0.04, zz + 0.04), (px + s - 0.04, zz + 0.04)], 0.5, 1.25, (240, 238, 232))
            for zz in np.arange(zA + 8, zB, 11):
                for s in (-1, 1):
                    M.prism([(px + s * 1.5, zz - 0.8), (px + s * 9, zz - 0.8), (px + s * 9, zz + 0.8), (px + s * 1.5, zz + 0.8)], 0.2, 0.45, WHITE)
                    if r.random() < 0.7: self.boat(px + s * 5.5, zz + s * 3.2 + 2.5, 1 if s > 0 else -1, 0, Y_SEA + 0.1); M.at(px, (zA + zB) / 2, 'orla'); M.m('madeira')
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
        self.harbor(); self.forest()
        print(f'  vida: {self.ntrees} arvores, {self.nlights} postes, {self.ncars} carros')
        return self
