"""Cidade 6 - plano urbano (desenhado do zero, 2,5 x 2 km).

   N (z=0)  morros com mata
   +---------------------------------------------------------------+
   |  suburbio norte (casas)          | rio |  suburbio leste      |
   | sub. |-------------------------|  |     |                      |
   | oeste|  CENTRO (grade 120 m)   |  |parque|                     |
   |      |  Parque Central, torres |  |ribei-|                     |
   |      |  ORLA (hoteis)          |  | rinho| marina              |
   |======== Av. Beira-Mar ===================================== ==|
   |  calcadao / praia / pier                                      |
   |  MAR (z ~ 1830+)                                              |
   +---------------------------------------------------------------+
X leste, Z sul, Y para cima. Cidade plana em y=0 (asfalto), calcada +0,15, gramado dos lotes +0,13."""
import math
import numpy as np
from shapely.geometry import LineString, Polygon, Point, box as sbox, MultiPolygon
from shapely.ops import unary_union

W, H = 2500.0, 2000.0

# ---------------------------------------------------------------- perfis de via
# meia largura: pista (asfalto), faixa de grama (canteiro de arvores) e calcada
PROFILE = {
    'av':     {'road': 9.5, 'med': 1.6, 'verge': 2.0, 'walk': 3.0, 'lanes': 2, 'park': False},   # avenida: 2+2 faixas, canteiro central
    'centro': {'road': 6.5, 'med': 0.0, 'verge': 0.0, 'walk': 4.5, 'lanes': 1, 'park': True},    # rua do centro: calcada larga com covas de arvore
    'rua':    {'road': 5.2, 'med': 0.0, 'verge': 1.8, 'walk': 1.8, 'lanes': 1, 'park': True},    # rua de bairro: estaciona dos dois lados
    'orla':   {'road': 9.5, 'med': 2.5, 'verge': 0.0, 'walk': 3.5, 'lanes': 2, 'park': False},   # Av. Beira-Mar
}


class Path:
    """eixo de uma via (polilinha): ponto e tangente na distancia s, ponto deslocado lateralmente, faixa entre dois deslocamentos"""
    def __init__(self, pts):
        self.pts = np.array(pts, float)
        seg = np.hypot(*(self.pts[1:] - self.pts[:-1]).T)
        self.cs = np.concatenate([[0.0], np.cumsum(seg)]); self.L = float(self.cs[-1])

    def at(self, s):
        s = min(max(s, 0.0), self.L)
        i = min(int(np.searchsorted(self.cs, s, 'right') - 1), len(self.pts) - 2)
        a, b = self.pts[i], self.pts[i + 1]; L = self.cs[i + 1] - self.cs[i] or 1.0
        t = (s - self.cs[i]) / L
        tx, tz = (b - a) / L
        return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, tx, tz

    def pt(self, s, off=0.0):
        x, z, tx, tz = self.at(s); return x - tz * off, z + tx * off

    def band(self, s0, s1, r0, r1, step=2.0):
        n = max(1, int(math.ceil((s1 - s0) / step)))
        ss = [s0 + (s1 - s0) * k / n for k in range(n + 1)]
        return Polygon([self.pt(q, r0) for q in ss] + [self.pt(q, r1) for q in ss[::-1]])


def half_row(kind):
    p = PROFILE[kind]; return p['road'] + p['verge'] + p['walk']


# ---------------------------------------------------------------- agua
def shore_z(x):
    return 1832.0 + 14.0 * math.sin(x / 290.0) + 9.0 * math.sin(x / 117.0 + 1.3)


def river_x(z):
    return 1688.0 + 26.0 * math.sin(z / 300.0 + 0.5) + 8.0 * math.sin(z / 97.0)


RIVER_W = 46.0           # largura da agua
RIVER_WALL = 3.0         # cais de pedra de cada lado


class Plan:
    def __init__(self):
        self.roads = []      # dict(name, kind, pts)
        self.sites = []      # areas especiais: dict(kind, poly, name)
        self.build()

    # ------------------------------------------------------------ desenho
    def add(self, name, kind, pts):
        self.roads.append({'name': name, 'kind': kind, 'pts': [(float(a), float(b)) for a, b in pts]})

    def build(self):
        # agua
        zs = np.arange(-20, shore_z(1690) + 60, 10.0)
        left = [(river_x(z) - RIVER_W / 2, z) for z in zs]; right = [(river_x(z) + RIVER_W / 2, z) for z in zs[::-1]]
        self.river = Polygon(left + right)
        xs = np.arange(-40, W + 41, 10.0)
        self.sea = Polygon([(x, shore_z(x)) for x in xs] + [(W + 40, H + 40), (-40, H + 40)])
        self.beach = Polygon([(x, shore_z(x) - 78.0) for x in xs] + [(x, shore_z(x) + 18.0) for x in xs[::-1]])
        self.water = unary_union([self.river, self.sea])
        # ---------------- ruas
        Z_ORLA = 1688.0
        XR = lambda z: river_x(z)
        # centro: grade 120 m
        # centro: grade IRREGULAR (quadras de tamanhos diferentes) com trechos de rua suprimidos (superquadras)
        DX = [600, 705, 840, 960, 1080, 1200, 1310, 1440]
        DZ = [640, 750, 880, 1000, 1120, 1240, 1345, 1470, 1590]
        park = (840, 1080, 880, 1120)                                   # Parque Central (2x2 quadras)
        cutx = {960: [(park[2], park[3]), (640, 750)], 705: [(1345, 1470)]}      # rua N-S x: trechos sem rua
        cutz = {1000: [(park[0], park[1])], 1470: [(1310, 1440)], 750: [(600, 705)]}
        def pieces(lo, hi, cuts):
            out = []; cur = lo
            for (c0, c1) in sorted(cuts):
                if c0 > cur: out.append((cur, c0))
                cur = max(cur, c1)
            if cur < hi: out.append((cur, hi))
            return out
        for x in DX:
            if x == 1200: continue                                      # Av. Central (abaixo)
            for k, (z0_, z1_) in enumerate(pieces(640, Z_ORLA, cutx.get(x, []))): self.add(f'Rua {x}.{k}', 'centro', [(x, z0_), (x, z1_)])
        for z in DZ:
            if z == 1240: continue                                      # Av. das Nacoes (abaixo)
            for k, (x0_, x1_) in enumerate(pieces(600, 1440, cutz.get(z, []))): self.add(f'Rua z{z}.{k}', 'centro', [(x0_, z), (x1_, z)])
        # avenidas
        self.add('Av. Central', 'av', [(1200, 0), (1200, Z_ORLA)])
        self.add('Av. das Nacoes', 'av', [(0, 1240), (W, 1240)])
        self.add('Av. Norte', 'av', [(0, 440), (W, 440)])
        self.add('Av. Oeste', 'av', [(360, 140), (360, Z_ORLA)])
        self.add('Av. Beira-Mar', 'orla', [(0, Z_ORLA), (W, Z_ORLA)])
        # ---- suburbios: ruas curvas (cada uma com sua ondulacao) e cul-de-sacs
        import random as _rnd
        R = _rnd.Random(606)
        self.bulbs = []

        def wave(a, b, A, k, ph, step=8.0):
            (x0, z0), (x1, z1) = a, b; L = math.hypot(x1 - x0, z1 - z0); n = max(2, int(L / step))
            nx, nz = -(z1 - z0) / L, (x1 - x0) / L
            out = []
            for q in range(n + 1):
                t = q / n; env = math.sin(math.pi * t) ** 0.8
                o = A * env * math.sin(2 * math.pi * k * t + ph)
                out.append((x0 + (x1 - x0) * t + nx * o, z0 + (z1 - z0) * t + nz * o))
            return out

        def wavy(name, a, b, Amin=11, Amax=22):
            self.add(name, 'rua', wave(a, b, R.uniform(Amin, Amax) * R.choice((-1, 1)), R.uniform(0.55, 1.25), R.uniform(0, 6.28)))

        # oeste
        wavy('Rua Oeste 1', (120, 140), (120, Z_ORLA), 6, 12)
        self.add('Rua 600 norte', 'rua', [(600, 140), (600, 640)])
        ew_streets = []
        for z in range(140, 1641, 100):
            if z in (440, 1240): continue
            if z == 140: self.add(f'Rua O{z}', 'rua', [(120, z), (600, z)]); continue
            wavy(f'Rua O{z}', (120, z), (600, z)); ew_streets.append((self.roads[-1], 120, 600))
        # norte (entre x=600 e o rio)
        for x in (840, 1080, 1320):
            wavy(f'Rua N{x}', (x, 140), (x, 640), 12, 24)
        self.add('Rua Ribeirinha Oeste', 'rua', wave((1560, 140), (1560, 640), 10, 0.8, 1.0))
        for z in range(140, 641, 100):
            if z == 440: continue
            if z in (140, 640): self.add(f'Rua Nz{z}', 'rua', [(600, z), (1560, z)]); continue
            wavy(f'Rua Nz{z}', (600, z), (1560, z), 10, 18); ew_streets.append((self.roads[-1], 600, 1560))
        self.add('Rua 1440 sul', 'centro', [(1440, 640), (1440, Z_ORLA)])
        # leste do rio
        XE0 = 1800
        self.add('Rua Ribeirinha Leste', 'rua', wave((XE0, 140), (XE0, Z_ORLA), 9, 1.4, 0.4))
        for x in (2040, 2280):
            wavy(f'Rua L{x}', (x, 140), (x, Z_ORLA), 14, 26)
        self.add('Rua L2440', 'rua', wave((2440, 140), (2440, Z_ORLA), 8, 1.1, 2.0))
        for z in range(140, 1541, 100):
            if z in (440, 1240): continue
            if z == 140: self.add(f'Rua Lz{z}', 'rua', [(XE0, z), (2440, z)]); continue
            wavy(f'Rua Lz{z}', (XE0, z), (2440, z)); ew_streets.append((self.roads[-1], XE0, 2440))
        # cul-de-sacs: rua curta sem saida com retorno redondo entrando no miolo das quadras
        for (rd, xa, xb) in ew_streets:
            pts = rd['pts']; n_cul = 0
            for frac in (0.18, 0.5, 0.82):
                if R.random() > 0.42: continue
                xm = xa + (xb - xa) * frac + R.uniform(-15, 15)
                if any(abs(xm - xv) < 45 for xv in (360, 840, 1080, 1200, 1320, 2040, 2280)): continue
                i = min(range(len(pts)), key=lambda q: abs(pts[q][0] - xm))
                if i <= 0 or i >= len(pts) - 1: continue
                (x0, z0), (x1, z1) = pts[i - 1], pts[i + 1]; L = math.hypot(x1 - x0, z1 - z0)
                sd = R.choice((-1, 1)); nx, nz = -(z1 - z0) / L * sd, (x1 - x0) / L * sd
                bx, bz = pts[i]; Lc = 30.0
                self.add(f'Cul-de-sac {len(self.bulbs) + 1}', 'rua', [(bx, bz), (bx + nx * Lc, bz + nz * Lc)])
                self.roads[-1]['cul'] = True
                self.bulbs.append((bx + nx * Lc, bz + nz * Lc, 11.5))
        # ponte de pedestre do Parque Ribeirinho
        self.footbridge = (880.0,)
        # ---------------- geometria das faixas de dominio
        self.make_geometry()
        self.make_sites()

    def make_geometry(self):
        rows, roads, meds = [], [], []
        for r in self.roads:
            p = PROFILE[r['kind']]; L = LineString(r['pts'])
            r['line'] = L; r['path'] = Path(r['pts'])
            roads.append(L.buffer(p['road'], cap_style='flat', join_style='mitre', quad_segs=4))
            rows.append(L.buffer(half_row(r['kind']), cap_style='flat', join_style='mitre', quad_segs=4))
        from shapely.geometry import Point as _P
        for (bx, bz, br) in getattr(self, 'bulbs', []):
            roads.append(_P(bx, bz).buffer(br, 6)); rows.append(_P(bx, bz).buffer(br + PROFILE['rua']['verge'] + PROFILE['rua']['walk'], 6))
        self.asphalt_raw = unary_union(roads)
        # esquinas arredondadas: guia com raio ~6 m (pista) e calcada acompanhando
        self.asphalt = self.asphalt_raw.buffer(6.0, join_style='round', quad_segs=4).buffer(-6.0, join_style='round', quad_segs=4).simplify(0.25)
        self.row = unary_union(rows).buffer(4.0, join_style='round', quad_segs=4).buffer(-4.0, join_style='round', quad_segs=4).simplify(0.25)
        land = sbox(0, 0, W, H).difference(self.water.buffer(RIVER_WALL))
        self.land = land
        self.blocks_geom = land.difference(self.row)

    def make_sites(self):
        """quadras (componentes) com zona"""
        self.blocks = []
        for g in getattr(self.blocks_geom, 'geoms', [self.blocks_geom]):
            if g.area < 200: continue
            c = g.representative_point(); cx, cz = c.x, c.y
            self.blocks.append({'poly': g, 'cx': cx, 'cz': cz, 'zone': self.zone(g, cx, cz)})

    def zone(self, g, cx, cz):
        minx, minz, maxx, maxz = g.bounds
        if cz > 1700: return 'praia'
        if abs(cx - river_x(cz)) < 140 and (cx > 1450 and cx < 1800): return 'ribeirinho'
        if 840 <= cx <= 1080 and 880 <= cz <= 1120: return 'parque'
        if 600 <= cx <= 1440 and 640 <= cz <= 1345: return 'centro'
        if 600 <= cx <= 1440 and 1345 < cz <= 1690: return 'orla'
        if cz < 140 or cx < 120 or cx > 2440: return 'mata'
        if cx > 1800 and cz > 1540: return 'marina'
        return 'suburbio'


if __name__ == '__main__':
    P = Plan()
    from collections import Counter
    print(len(P.roads), 'vias;', len(P.blocks), 'quadras', Counter(b['zone'] for b in P.blocks))
