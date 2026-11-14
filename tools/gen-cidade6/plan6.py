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
        DX = [600, 720, 840, 960, 1080, 1200, 1320, 1440]
        DZ = [640, 760, 880, 1000, 1120, 1240, 1360, 1480, 1590]
        park = (840, 1080, 880, 1120)                                   # Parque Central (2x2 quadras)
        for x in DX:
            if x == 1200: continue                                      # Av. Central (abaixo)
            zz0, zz1 = 640, Z_ORLA
            if park[0] < x < park[1]:                                   # x=960 interrompida pelo parque
                self.add(f'Rua {x}', 'centro', [(x, zz0), (x, park[2])]); self.add(f'Rua {x}b', 'centro', [(x, park[3]), (x, zz1)]); continue
            self.add(f'Rua {x}', 'centro' if x not in (600, 1440) else 'centro', [(x, zz0), (x, zz1)])
        for z in DZ:
            if z == 1240: continue                                      # Av. das Nacoes (abaixo)
            if park[2] < z < park[3]:
                self.add(f'Rua z{z}', 'centro', [(600, z), (park[0], z)]); self.add(f'Rua z{z}b', 'centro', [(park[1], z), (1440, z)]); continue
            self.add(f'Rua z{z}', 'centro', [(600, z), (1440, z)])
        # avenidas
        self.add('Av. Central', 'av', [(1200, 0), (1200, Z_ORLA)])
        self.add('Av. das Nacoes', 'av', [(0, 1240), (W, 1240)])
        self.add('Av. Norte', 'av', [(0, 440), (W, 440)])
        self.add('Av. Oeste', 'av', [(360, 140), (360, Z_ORLA)])
        self.add('Av. Beira-Mar', 'orla', [(0, Z_ORLA), (W, Z_ORLA)])
        # suburbio oeste: N-S x=120, 600 ; E-W a cada 100 m (quadras compridas, lotes de frente para as ruas E-W)
        self.add('Rua Oeste 1', 'rua', [(120, 140), (120, Z_ORLA)])
        self.add('Rua 600 norte', 'rua', [(600, 140), (600, 640)])
        for z in range(140, 1641, 100):
            if z in (440, 1240): continue
            self.add(f'Rua O{z}', 'rua', [(120, z), (600, z)])
        # suburbio norte (entre x=600 e o rio): N-S a cada 240 m, E-W a cada 100 m
        for x in (840, 1080, 1320, 1560):
            if x == 1560: self.add('Rua Ribeirinha Oeste', 'rua', [(1560, 140), (1560, 640)]); continue
            self.add(f'Rua N{x}', 'rua', [(x, 140), (x, 640)])
        for z in range(140, 641, 100):
            if z == 440: continue
            self.add(f'Rua Nz{z}', 'rua', [(600, z), (1560, z)])
        self.add('Rua 1440 sul', 'centro', [(1440, 640), (1440, Z_ORLA)])
        # leste do rio
        XE0 = 1800
        self.add('Rua Ribeirinha Leste', 'rua', [(XE0, 140), (XE0, Z_ORLA)])
        for x in (2040, 2280):
            self.add(f'Rua L{x}', 'rua', [(x, 140), (x, Z_ORLA)])
        self.add('Rua L2440', 'rua', [(2440, 140), (2440, Z_ORLA)])
        for z in range(140, 1541, 100):
            if z in (440, 1240): continue
            self.add(f'Rua Lz{z}', 'rua', [(XE0, z), (2440, z)])
        # ponte de pedestre do Parque Ribeirinho
        self.footbridge = (880.0,)
        # ---------------- geometria das faixas de dominio
        self.make_geometry()
        self.make_sites()

    def make_geometry(self):
        rows, roads, meds = [], [], []
        for r in self.roads:
            p = PROFILE[r['kind']]; L = LineString(r['pts'])
            r['line'] = L
            roads.append(L.buffer(p['road'], cap_style='flat', join_style='mitre'))
            rows.append(L.buffer(half_row(r['kind']), cap_style='flat', join_style='mitre'))
        self.asphalt_raw = unary_union(roads)
        # esquinas arredondadas: guia com raio ~6 m (pista) e calcada acompanhando
        self.asphalt = self.asphalt_raw.buffer(6.0, join_style='round').buffer(-6.0, join_style='round')
        self.row = unary_union(rows).buffer(4.0, join_style='round').buffer(-4.0, join_style='round')
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
        if 600 <= cx <= 1440 and 640 <= cz <= 1360: return 'centro'
        if 600 <= cx <= 1440 and 1360 < cz <= 1690: return 'orla'
        if cz < 140 or cx < 120 or cx > 2440: return 'mata'
        if cx > 1800 and cz > 1540: return 'marina'
        return 'suburbio'


if __name__ == '__main__':
    P = Plan()
    from collections import Counter
    print(len(P.roads), 'vias;', len(P.blocks), 'quadras', Counter(b['zone'] for b in P.blocks))
