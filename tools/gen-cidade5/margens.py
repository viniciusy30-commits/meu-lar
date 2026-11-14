"""ETAPA E0: margens e bordas da cidade.
Enrocamento (pedra + blocos) em toda margem urbana (rio, lagoa, pontas das orlas, cabeceiras dos canais), calcadao ribeirinho com guarda-corpo, postes, bancos e arvores,
docas com barcos, molhes de pedra com farois nas pontas das orlas e balizas na foz do rio. Tudo assado na malha (mesmo caminho do chao); o piso caminhavel e PAVER/madeira sobre a agua."""
import math, random, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from bake import rgb, shade, PLAIN, STONE, WOOD, METAL, PAVER, TILE
from plan import *
import shore
import terrain_final as T

COLM = {'rock1': rgb('#8F8B82'), 'rock2': rgb('#77746C'), 'rock3': rgb('#A29C90'), 'rock4': rgb('#6A665F'), 'rockd': rgb('#5C5952'),
        'rip1': rgb('#8C877D'), 'rip2': rgb('#79756C'), 'path': rgb('#CDC3B2'), 'path2': rgb('#BFB4A1'), 'edge': rgb('#9C9486'),
        'rail': rgb('#E9E6DE'), 'post': rgb('#3B3F45'), 'lamp': rgb('#2B2E33'), 'lampH': rgb('#FFF0B8'), 'bench': rgb('#7A5A3A'), 'iron': rgb('#2A2C30'),
        'wood': rgb('#8B6B47'), 'wood2': rgb('#6E5236'), 'white': rgb('#F4F4F2'), 'red': rgb('#D6402A'), 'blue': rgb('#2F6DB5'), 'green': rgb('#2E9D4B'),
        'glass': rgb('#CFE9F2'), 'lantern': rgb('#FFE79A'), 'conc': rgb('#CFCABF'), 'conc2': rgb('#B3AD9F'), 'sea': rgb('#4F9BD0')}
BOAT = [(rgb('#F4F4F2'), rgb('#2F6DB5')), (rgb('#F4F4F2'), rgb('#D6402A')), (rgb('#E8C547'), rgb('#F4F4F2')), (rgb('#2E9D4B'), rgb('#F4F4F2')), (rgb('#F4F4F2'), rgb('#1C3F73'))]
WATER_Y = -0.2
TREE_SP = [0, 1, 3]


def seg_dist_pt(px, pz, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dz * dz or 1e-9
    t = min(max(((px - a[0]) * dx + (pz - a[1]) * dz) / L2, 0), 1)
    return math.hypot(px - (a[0] + t * dx), pz - (a[1] + t * dz))


def poly_d(px, pz, pts):
    return min(seg_dist_pt(px, pz, a, b) for a, b in zip(pts, pts[1:]))


class Margens:
    def __init__(self, gr, geo, hf, orla, plan, seed=RNG + 5):
        self.g = gr; self.geo = geo; self.hf = hf; self.o = orla; self.P = plan; self.B = gr.B; self.c = gr.c
        self.rnd = random.Random(seed)
        self.items = {'solids': [], 'stairs_cais': [], 'galpoes': [], 'runs': [], 'lamps': [], 'benches': [], 'docks': [], 'boats': [], 'jetties': [], 'lighthouses': [], 'rocks': 0, 'trees': 0}
        self.stats = {'rip_m': 0.0, 'prom_m': 0.0, 'rocks': 0}
        self.band_pts = []                                   # pontos (3 m) do calcadao: reserva para os lotes
        self.plazas = list(orla.items.get('plazas', [])); self.dock_sites = []; self.solids = []; self.stairs_at = []; self.cais_runs = []
        self.ends = [(p['x'], p['z']) for p in self.plazas if p['x'] < 1500 or p['x'] > 3000]
        self.occ = self.occupied(); self.dbg = {}

    # ------------------------------------------------------------------ base
    def sample(self, x, z): return float(T.sample8(self.hf, x, z))

    def occupied(self):
        """mascara (1 m) de tudo o que o chao ja ocupa (ruas, calcadas, orla, pontes) dilatada 3 m + lotes das casas"""
        im = Image.new('L', (int(WX), int(WZ)), 0); d = ImageDraw.Draw(im)
        for name, pts in self.g.layers:
            if name in ('zebra', 'mark', 'tact', 'lotpath'): continue
            if len(pts) >= 3: d.polygon([(p[0], p[1]) for p in pts], fill=255)
        for h in self.P.houses:
            d.polygon([(p[0], p[1]) for p in h['lot']['rect']], fill=255)
        im = im.filter(ImageFilter.MaxFilter(9))
        return np.array(im) > 0

    def blocked(self, x, z, pad=0):
        i, j = int(x), int(z)
        if i < 0 or j < 0 or j >= self.occ.shape[0] or i >= self.occ.shape[1]: return True
        if pad:
            return bool(self.occ[max(j - pad, 0):j + pad + 1, max(i - pad, 0):i + pad + 1].any())
        return bool(self.occ[j, i])

    # ------------------------------------------------------------------ formas simples
    def rock(self, x, y, z, r, col, flat=0.62):
        """bloco de pedra irregular: anel de 6 vertices (raios variados) + topo deslocado (10 triangulos)"""
        rnd = self.rnd; n = 6; a0 = rnd.uniform(0, 6.28)
        ring = []
        for k in range(n):
            a = a0 + 2 * math.pi * k / n; rr = r * rnd.uniform(0.75, 1.15)
            ring.append((x + math.cos(a) * rr, y + rnd.uniform(-0.05, 0.12) * r, z + math.sin(a) * rr))
        top = (x + rnd.uniform(-0.2, 0.2) * r, y + r * flat * rnd.uniform(0.8, 1.15), z + rnd.uniform(-0.2, 0.2) * r)
        base = (x, y - r * 0.35, z)
        for k in range(n):
            p0, p1 = ring[k], ring[(k + 1) % n]
            c = shade(col, int(rnd.uniform(-9, 7)))
            for (a, b, cc, up) in ((p0, p1, top, True), (p1, p0, base, False)):
                u = (b[0] - a[0], b[1] - a[1], b[2] - a[2]); v = (cc[0] - a[0], cc[1] - a[1], cc[2] - a[2])
                nrm = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]); l = math.sqrt(nrm[0] ** 2 + nrm[1] ** 2 + nrm[2] ** 2) or 1
                nrm = (nrm[0] / l, nrm[1] / l, nrm[2] / l)
                if up and nrm[1] < 0: nrm = (-nrm[0], -nrm[1], -nrm[2])
                self.B.tri(STONE, a, b, cc, nrm, c)
        self.stats['rocks'] += 1

    def lamp(self, x, z, y):
        self.B.cyl(x, z, 0.08, y, y + 4.6, COLM['lamp'], 8, METAL)
        self.B.cyl(x, z, 0.14, y, y + 0.35, COLM['lamp'], 8, METAL)
        self.B.box(x, z, 0.62, 0.3, y + 4.5, y + 4.68, COLM['lampH'], PLAIN, True, False)
        self.items['lamps'].append({'x': round(x, 2), 'z': round(z, 2), 'y': round(y, 2)})

    def bench(self, x, z, y, nx, nz):
        tx, tz = -nz, nx
        c4 = [(x - tx * 0.95 - nx * 0.24, z - tz * 0.95 - nz * 0.24), (x + tx * 0.95 - nx * 0.24, z + tz * 0.95 - nz * 0.24), (x + tx * 0.95 + nx * 0.24, z + tz * 0.95 + nz * 0.24), (x - tx * 0.95 + nx * 0.24, z - tz * 0.95 + nz * 0.24)]
        self.B.obox_pts(c4, y + 0.4, y + 0.52, COLM['bench'], WOOD, True, False)
        c4b = [(x - tx * 0.95 + nx * 0.2, z - tz * 0.95 + nz * 0.2), (x + tx * 0.95 + nx * 0.2, z + tz * 0.95 + nz * 0.2), (x + tx * 0.95 + nx * 0.26, z + tz * 0.95 + nz * 0.26), (x - tx * 0.95 + nx * 0.26, z - tz * 0.95 + nz * 0.26)]
        self.B.obox_pts(c4b, y + 0.55, y + 0.95, COLM['bench'], WOOD, True, False)
        for sg in (-1, 1): self.B.box(x + tx * 0.75 * sg, z + tz * 0.75 * sg, 0.14, 0.44, y + 0.0, y + 0.4, COLM['iron'], PLAIN, True, False)
        self.items['benches'].append({'x': round(x, 2), 'z': round(z, 2), 'nx': round(-nx, 3), 'nz': round(-nz, 3)})

    def ribbon(self, fr, o0, o1, dy, mat, col, i0=0, i1=None, layer=None, alt=None):
        i1 = len(fr) - 1 if i1 is None else i1
        for k in range(i0, i1):
            a, b = fr[k], fr[k + 1]
            def pt(f, o): x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o; return (x, self.sample(x, z) + dy, z)
            q = [pt(a, o0), pt(b, o0), pt(b, o1), pt(a, o1)]
            c = col if alt is None or (k // 3) % 2 == 0 else alt
            self.B.quad(mat, q, (0, 1, 0), c)
            if layer: self.g.poly(layer, [(p[0], p[2]) for p in q])

    # ------------------------------------------------------------------ linhas de margem
    def shorelines(self):
        lines = shore.contour(self.hf, WATER_Y, None, cell=8.0); out = []
        for l in lines:
            if shore.length(l) < 120: continue
            closed = math.hypot(l[0][0] - l[-1][0], l[0][1] - l[-1][1]) < 1.0
            l = shore.resample(shore.smooth_line(shore.resample(l, 8.0), 3, keep_ends=True), 3.0)
            # lado da terra: mediana do teste de altura (consistente ao longo da linha)
            votes = 0
            for k in range(2, len(l) - 2, 3):
                tx, tz = l[k + 2][0] - l[k - 2][0], l[k + 2][1] - l[k - 2][1]; n = math.hypot(tx, tz) or 1; nx, nz = -tz / n, tx / n
                votes += 1 if self.sample(l[k][0] + nx * 9, l[k][1] + nz * 9) > self.sample(l[k][0] - nx * 9, l[k][1] - nz * 9) else -1
            sg = 1.0 if votes >= 0 else -1.0
            fr = []
            for k, p in enumerate(l):
                a = l[max(k - 2, 0)]; b = l[min(k + 2, len(l) - 1)]; tx, tz = b[0] - a[0], b[1] - a[1]; n = math.hypot(tx, tz) or 1
                fr.append({'x': p[0], 'z': p[1], 'tx': tx / n, 'tz': tz / n, 'nx': -tz / n * sg, 'nz': tx / n * sg})
            out.append((fr, closed))
        return out

    def bm_dist(self, x, z):
        if not hasattr(self, '_bm'):
            self._bm = [e['p'] for e in self.c.edges if e.get('name') == 'Av. Beira-Mar']
        return min((poly_d(x, z, p) for p in self._bm), default=1e9)

    def classify(self, fr, closed):
        """tipo de cada ponto: lagoa / rio / canal / mar / praia"""
        lx, lz, rx, rz = LAGOON
        kinds = []
        for f in fr:
            x, z = f['x'], f['z']
            if closed and math.hypot((x - lx) / (rx + 50), (z - lz) / (rz + 50)) < 1.3: kinds.append('lagoa'); continue
            dr = poly_d(x, z, RIVER['pts'])
            if dr < 190 and z < 2790: kinds.append('rio'); continue
            ii_ = int(min(max(round(x / CELL), 0), NX - 1)); jj_ = int(min(max(round(z / CELL), 0), NZ - 1))
            if self.bm_dist(x, z) < 150.0 and not any(math.hypot(x - a, z - b) < 45 for a, b in self.ends): kinds.append('praia'); continue
            dw = min(poly_d(x, z, CHANNEL_W['pts']), poly_d(x, z, CHANNEL_E['pts']))
            if 700 < x < 3700 and any(math.hypot(x - a, z - b) < 560 for a, b in self.ends): kinds.append('cais'); continue
            if dw < 330: kinds.append('canal'); continue
            kinds.append('mar')
        return kinds

    def active_runs(self, fr, kinds):
        """trechos com tratamento: (i0, i1, tipo, calcadao?)"""
        plz = [(p['x'], p['z']) for p in self.plazas]
        looks = [tuple(r['lookout']) for r in self.c.red]
        act = []
        for k, (f, kd) in enumerate(zip(fr, kinds)):
            x, z = f['x'], f['z']
            ok = False; prom = False
            if kd == 'rio' and 560 < z < 2700: ok = True; prom = True
            elif kd == 'lagoa': ok = True; prom = True
            elif kd == 'cais': ok = True
            elif kd == 'canal' and any(math.hypot(x - a, z - b) < 190 for a, b in looks): ok = True
            elif kd == 'mar' and any(math.hypot(x - a, z - b) < 230 for a, b in plz): ok = True; prom = any(math.hypot(x - a, z - b) < 140 for a, b in plz)
            elif kd == 'rio' and any(math.hypot(x - a, z - b) < 120 for a, b in plz): ok = True
            if ok and self.blocked(x + f['nx'] * 1.0, z + f['nz'] * 1.0, 1): ok = False
            if ok:                                                           # a faixa de pedra tem que estar livre de ruas, calcadas, orla e lotes
                for o in (2.0, 4.0):
                    if self.blocked(x + f['nx'] * o, z + f['nz'] * o, 0): ok = False; break
            act.append((ok, prom))
        runs = []; k = 0; n = len(fr)
        while k < n:
            if not act[k][0]: k += 1; continue
            j = k
            while j + 1 < n and act[j + 1][0]: j += 1
            if j - k >= 4: runs.append((k, j, kinds[k], all(a[1] for a in act[k:j + 1])))
            k = j + 1
        return runs

    def run_stone(self, fr, i0, i1, kind):
        seg = fr[i0:i1 + 1]
        # faixa de pedra (do espelho d'agua ate 3 m para dentro) + blocos soltos
        self.ribbon(seg, -0.5, 3.0, 0.035, PAVER, COLM['rip1'], alt=COLM['rip2'])
        self.stats['rip_m'] += 3.0 * (len(seg) - 1)
        for k in range(0, len(seg) - 1):
            f = seg[k]
            for _ in range(3 if kind != 'canal' else 2):
                o = self.rnd.uniform(-0.3, 2.9); s = self.rnd.uniform(0, 3.0)
                x = f['x'] + f['nx'] * o + f['tx'] * s; z = f['z'] + f['nz'] * o + f['tz'] * s
                if self.blocked(x, z, 0) or self.near_site(x, z, 2.6, -8.0, 4.0): continue
                y = max(self.sample(x, z), WATER_Y - 0.25)
                r = self.rnd.uniform(0.5, 1.15)
                self.rock(x, y, z, r, self.rnd.choice((COLM['rock1'], COLM['rock2'], COLM['rock3'], COLM['rock4'])))

    def run_prom(self, fr, i0, i1, kind):
        """calcadao ribeirinho: faixa de pedra (3 m) + grama (2 m) + caminho de 3,4 m + guarda-corpo na beira + postes e bancos do lado de dentro + arvores"""
        seg = fr[i0:i1 + 1]
        P0, P1 = 5.4, 8.8
        good = []
        for f in seg:
            x0, z0 = f['x'] + f['nx'] * P0, f['z'] + f['nz'] * P0; x1, z1 = f['x'] + f['nx'] * P1, f['z'] + f['nz'] * P1
            h0, h1 = self.sample(x0, z0), self.sample(x1, z1)
            r = (self.blocked(x0, z0, 0) or self.blocked(x1, z1, 0), abs(h1 - h0) / (P1 - P0) >= 0.16, h0 <= -0.05)
            self.dbg[r] = self.dbg.get(r, 0) + 1
            ok = not any(r)
            good.append(ok)
        # sub-trechos livres
        k = 0
        while k < len(seg):
            if not good[k]: k += 1; continue
            j = k
            while j + 1 < len(seg) and good[j + 1]: j += 1
            if j - k >= 6:
                self.prom_piece(seg, k, j)
            k = j + 1

    def prom_piece(self, seg, k0, k1):
        P0, P1 = 5.4, 8.8
        self.ribbon(seg, P0, P1, 0.05, PAVER, COLM['path'], k0, k1, 'mprom', alt=COLM['path2'])
        self.ribbon(seg, P0 - 0.25, P0, 0.05, PAVER, COLM['edge'], k0, k1)
        self.ribbon(seg, P1, P1 + 0.25, 0.05, PAVER, COLM['edge'], k0, k1)
        self.stats['prom_m'] += 3.0 * (k1 - k0)
        for k in range(k0, k1 + 1): self.band_pts.append((seg[k]['x'], seg[k]['z']))
        self.rail(seg, k0, k1, P0 - 0.5)
        # postes (21 m), bancos (42 m, defasados), arvores (15 m)
        acc = 0.0; nl = 0
        for k in range(k0, k1 + 1):
            f = seg[k]
            if k > k0: acc += 3.0
            if int(acc // 21) != int((acc - 3.0) // 21) or k == k0:
                x, z = f['x'] + f['nx'] * (P1 + 0.7), f['z'] + f['nz'] * (P1 + 0.7)
                if not self.blocked(x, z, 0) and not self.near_site(x, z, 3.0, -12, 4): self.lamp(x, z, self.sample(x, z) + 0.04); nl += 1
            if int((acc + 10.5) // 42) != int((acc + 7.5) // 42):
                x, z = f['x'] + f['nx'] * (P1 + 0.55), f['z'] + f['nz'] * (P1 + 0.55)
                if not self.blocked(x, z, 0) and not self.near_site(x, z, 3.0, -12, 4): self.bench(x, z, self.sample(x, z) + 0.04, -f['nx'], -f['nz'])
            if int((acc + 4.5) // 15) != int((acc + 1.5) // 15):
                x, z = f['x'] + f['nx'] * (P1 + 4.2 + self.rnd.uniform(0, 1.5)), f['z'] + f['nz'] * (P1 + 4.2 + self.rnd.uniform(0, 1.5))
                if not self.blocked(x, z, 2) and self.sample(x, z) > 0.4:
                    self.P.trees.append([round(x, 1), round(z, 1), self.rnd.choice(TREE_SP), round(self.rnd.uniform(0.9, 1.3), 2), round(self.rnd.uniform(0, 6.28), 2), round(self.rnd.uniform(0, 1), 2)])
                    self.items['trees'] += 1

    def rail(self, seg, k0, k1, o):
        """guarda-corpo: poste a cada 3 m + 2 corrimaos; cada vao vira uma colisao (o jogador nao chega na agua)"""
        for k in range(k0, k1):
            a, b = seg[k], seg[k + 1]
            xa, za = a['x'] + a['nx'] * o, a['z'] + a['nz'] * o; xb, zb = b['x'] + b['nx'] * o, b['z'] + b['nz'] * o
            if self.near_site(xa, za, 2.3, -9.0, 6.5) or self.near_site(xb, zb, 2.3, -9.0, 6.5): continue
            ya, yb = self.sample(xa, za) + 0.04, self.sample(xb, zb) + 0.04
            self.B.box(xa, za, 0.09, 0.09, ya, ya + 1.0, COLM['post'], METAL, True, False)
            dx, dz = xb - xa, zb - za; L = math.hypot(dx, dz) or 1; px, pz = -dz / L * 0.04, dx / L * 0.04
            for yy in (0.95, 0.5):
                self.B.obox_pts([(xa - px, za - pz), (xb - px, zb - pz), (xb + px, zb + pz), (xa + px, za + pz)], min(ya, yb) + yy - 0.04 + (0 if yy > 0.9 else 0), max(ya, yb) + yy + 0.03 if yy > 0.9 else max(ya, yb) + yy, COLM['rail'], METAL, True, False)
            self.solids.append([round(min(xa, xb) - 0.3, 2), round(min(za, zb) - 0.3, 2), round(max(xa, xb) + 0.3, 2), round(max(za, zb) + 0.3, 2)])

    def run_rail(self, fr, i0, i1):
        """trechos so de pedra (cabeceiras de canal, pontas): guarda-corpo a 3,9 m da agua onde o chao e livre"""
        seg = fr[i0:i1 + 1]; good = []
        for f in seg:
            x, z = f['x'] + f['nx'] * 3.9, f['z'] + f['nz'] * 3.9
            good.append((not self.blocked(x, z, 0)) and self.sample(x, z) > 0.2)
        k = 0
        while k < len(seg):
            if not good[k]: k += 1; continue
            j = k
            while j + 1 < len(seg) and good[j + 1]: j += 1
            if j - k >= 3: self.rail(seg, k, j, 3.9)
            k = j + 1

    # ------------------------------------------------------------------ docas e barcos
    def dock_geom(self, f, width=2.3):
        x0, z0 = f['x'] + f['nx'] * 1.8, f['z'] + f['nz'] * 1.8                         # comeca na margem (em cima da pedra)
        wx, wz = -f['nx'], -f['nz']; rx, rz = -wz, wx                                  # (wx,wz): para a agua; (rx,rz): lateral
        L = 0.0
        while L < 22 and self.sample(x0 + wx * L, z0 + wz * L) > -1.0: L += 0.5
        if L >= 22 or L < 4.5: return None
        for a in np.arange(-6.0, L + 2.0, 3.0):                                         # a margem (incluindo o acesso a partir do calcadao) precisa estar livre
            for b in (-5.0, 0.0, 5.0):
                if self.blocked(x0 + rx * b + wx * a, z0 + rz * b + wz * a, 1) and a < 0: return None
        if self.blocked(x0 - wx * 4.0, z0 - wz * 4.0, 1): return None
        return {'x0': x0, 'z0': z0, 'wx': wx, 'wz': wz, 'rx': rx, 'rz': rz, 'L': L, 'width': width, 'nx': f['nx'], 'nz': f['nz']}

    def near_site(self, x, z, r=2.4, lo=-7.5, hi=3.5):
        """(x,z) esta no corredor de acesso de alguma doca (do calcadao ate a margem)?"""
        for d in self.dock_sites:
            u = (x - d['x0']) * d['wx'] + (z - d['z0']) * d['wz']; v = (x - d['x0']) * d['rx'] + (z - d['z0']) * d['rz']
            if lo < u < hi and abs(v) < r: return True
        return False

    def draw_dock(self, d):
        x0, z0, wx, wz, rx, rz, L, width = d['x0'], d['z0'], d['wx'], d['wz'], d['rx'], d['rz'], d['L'], d['width']
        deck = 0.42; tot = L + 1.6
        def PP(a, b, y): return (x0 + wx * a + rx * b, y, z0 + wz * a + rz * b)
        # caminho de acesso: do calcadao (5,6 m da margem) ate a doca
        acc = [PP(-7.4, -1.0, 0), PP(-7.4, 1.0, 0)]
        steps = 8
        for q in range(steps):
            a0, a1 = -7.4 + (7.4 - 0.2) * q / steps, -7.4 + (7.4 - 0.2) * (q + 1) / steps
            pts = []
            for (a, b) in ((a0, -1.0), (a1, -1.0), (a1, 1.0), (a0, 1.0)):
                p = PP(a, b, 0); pts.append((p[0], max(self.sample(p[0], p[2]) + 0.05, 0.0 if a > -1.0 else -9), p[2]))
            self.B.quad(PAVER, [(p[0], max(p[1], 0.06) if a_ > -2.0 else p[1], p[2]) for p, a_ in zip(pts, (a0, a1, a1, a0))], (0, 1, 0), COLM['wood'] if q % 2 == 0 else rgb('#977650'))
        n = int(tot / 1.2) + 1
        for q in range(n):
            a0, a1 = q * 1.2, (q + 1) * 1.2
            c4 = [(PP(a0, -width / 2, 0)[0], PP(a0, -width / 2, 0)[2]), (PP(a1, -width / 2, 0)[0], PP(a1, -width / 2, 0)[2]), (PP(a1, width / 2, 0)[0], PP(a1, width / 2, 0)[2]), (PP(a0, width / 2, 0)[0], PP(a0, width / 2, 0)[2])]
            self.B.obox_pts(c4, deck - 0.16, deck, COLM['wood'] if q % 2 == 0 else rgb('#977650'), WOOD, True, False, 0.5)
        for a in np.arange(0.9, tot, 3.0):                                              # estacas
            for sg in (-1, 1):
                px, _, pz = PP(a, sg * (width / 2 - 0.08), 0)
                self.B.cyl(px, pz, 0.11, -2.4, deck + 0.55, COLM['wood2'], 6, WOOD, True)
        px, _, pz = PP(tot - 0.4, 0, 0)
        self.B.cyl(px, pz, 0.14, deck, deck + 0.5, COLM['iron'], 6, METAL, True)        # cabeco
        self.items['docks'].append({'x': round(x0, 2), 'z': round(z0, 2), 'dx': round(wx, 3), 'dz': round(wz, 3), 'len': round(tot, 1), 'w': width, 'deck': deck})
        # barco ao lado (tenta os dois lados)
        bl = self.rnd.uniform(5.5, 8.5); bw = bl * 0.33; hull, cab = self.rnd.choice(BOAT)
        placed = False
        for sgn in self.rnd.sample((-1, 1), 2):
            for la in (tot - bl * 0.45, tot - bl * 0.2, tot + bl * 0.1, tot + bl * 0.35):
                bx, bz = x0 + wx * la + rx * sgn * (width / 2 + 0.8 + bw / 2), z0 + wz * la + rz * sgn * (width / 2 + 0.8 + bw / 2)
                if all(self.sample(bx + wx * q, bz + wz * q) < -0.35 for q in (-bl / 2, 0.0, bl / 2)):
                    self.boat(bx, bz, wx, wz, bl, bw, hull, cab); placed = True; break
            if placed: break

    def boat(self, x, z, dx, dz, L, W, hull, cab):
        rx, rz = -dz, dx
        def Pt(a, b): return (x + dx * a + rx * b, z + dz * a + rz * b)
        y0, y1 = WATER_Y - 0.5, 0.38
        # casco: popa larga, proa afilada (pentagono)
        pts = [Pt(-L / 2, -W / 2), Pt(L * 0.18, -W / 2), Pt(L / 2, 0), Pt(L * 0.18, W / 2), Pt(-L / 2, W / 2)]
        for k in range(5):
            a, b = pts[k], pts[(k + 1) % 5]; ex, ez = b[0] - a[0], b[1] - a[1]; ln = math.hypot(ex, ez) or 1
            self.B.quad(PLAIN, [(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])], (ez / ln, 0, -ex / ln), hull)
        self.B.poly(PLAIN, [(p[0], y1, p[1]) for p in pts], (0, 1, 0), shade(hull, 14))
        # convés claro + cabine
        self.B.poly(PLAIN, [(Pt(-L / 2 + 0.2, -W / 2 + 0.2)[0], y1 + 0.01, Pt(-L / 2 + 0.2, -W / 2 + 0.2)[1]), (Pt(L * 0.1, -W / 2 + 0.2)[0], y1 + 0.01, Pt(L * 0.1, -W / 2 + 0.2)[1]), (Pt(L * 0.1, W / 2 - 0.2)[0], y1 + 0.01, Pt(L * 0.1, W / 2 - 0.2)[1]), (Pt(-L / 2 + 0.2, W / 2 - 0.2)[0], y1 + 0.01, Pt(-L / 2 + 0.2, W / 2 - 0.2)[1])], (0, 1, 0), COLM['white'])
        cw = W * 0.62
        c4 = [Pt(-L * 0.28, -cw / 2), Pt(L * 0.02, -cw / 2), Pt(L * 0.02, cw / 2), Pt(-L * 0.28, cw / 2)]
        self.B.obox_pts(c4, y1, y1 + 1.15, cab, PLAIN, True, False)
        gl = [Pt(L * 0.02, -cw / 2 + 0.05), Pt(L * 0.02 + 0.02, -cw / 2 + 0.05), Pt(L * 0.02 + 0.02, cw / 2 - 0.05), Pt(L * 0.02, cw / 2 - 0.05)]
        self.B.obox_pts(gl, y1 + 0.55, y1 + 1.0, COLM['glass'], PLAIN, False, False)
        self.items['boats'].append({'x': round(x, 1), 'z': round(z, 1), 'dx': round(dx, 3), 'dz': round(dz, 3), 'len': round(L, 1)})

    # ------------------------------------------------------------------ molhes e farois
    def lighthouse(self, x, z, y0, scheme):
        base = COLM['conc']
        self.B.cyl(x, z, 3.6, y0, y0 + 1.2, COLM['conc2'], 12, STONE, True)
        bands = [COLM['white'], COLM[scheme], COLM['white'], COLM[scheme], COLM['white']]
        h = y0 + 1.2; r = 2.5
        for k, c in enumerate(bands):
            r2 = r - 0.18
            self.B.cyl(x, z, r, h, h + 3.0, c, 12, PLAIN, False, r2)
            h += 3.0; r = r2
        # galeria
        self.B.cyl(x, z, r + 0.9, h, h + 0.25, COLM['iron'], 12, METAL, True)
        for q in range(12):
            a = 2 * math.pi * q / 12
            self.B.box(x + math.cos(a) * (r + 0.85), z + math.sin(a) * (r + 0.85), 0.07, 0.07, h + 0.25, h + 1.25, COLM['iron'], METAL, True, False)
        self.B.cyl(x, z, r + 0.85, h + 1.18, h + 1.28, COLM['iron'], 12, METAL, True)
        # lanterna e telhado
        self.B.cyl(x, z, r - 0.15, h + 0.25, h + 2.35, COLM['lantern'], 10, PLAIN, False)
        for q in range(5):
            a = 2 * math.pi * q / 5
            self.B.box(x + math.cos(a) * (r - 0.1), z + math.sin(a) * (r - 0.1), 0.12, 0.12, h + 0.25, h + 2.4, COLM['iron'], METAL, True, False)
        self.B.cyl(x, z, r + 0.35, h + 2.35, h + 3.6, COLM[scheme], 12, PLAIN, False, 0.08)
        self.items['lighthouses'].append({'x': round(x, 1), 'z': round(z, 1), 'y': round(y0, 2), 'h': round(h + 3.6 - y0, 1)})

    def beacon(self, x, z, y0, col):
        self.B.cyl(x, z, 1.5, y0, y0 + 0.9, COLM['conc2'], 8, STONE, True)
        self.B.cyl(x, z, 0.5, y0 + 0.9, y0 + 4.6, COLM['white'], 8, PLAIN, False, 0.42)
        self.B.cyl(x, z, 0.62, y0 + 4.4, y0 + 5.6, COLM[col], 8, PLAIN, True)
        self.B.cyl(x, z, 0.75, y0 + 5.6, y0 + 5.8, COLM['iron'], 8, METAL, True)
        self.items['lighthouses'].append({'x': round(x, 1), 'z': round(z, 1), 'y': round(y0, 2), 'h': 5.8, 'baliza': col})

    def jetty_dir(self, px, pz, sx, sz, ytop, length, kind, scheme):
        rx, rz = -sz, sx
        W = 7.0 if kind == 'farol' else 4.6; yd = ytop
        def PP(a, b, y): return (px + sx * a + rx * b, y, pz + sz * a + rz * b)
        n = int(length / 3.0)
        # profundidade: o corpo de pedra desce ate o fundo
        for q in range(n):
            a0, a1 = q * 3.0, (q + 1) * 3.0
            xm, zm = px + sx * (a0 + 1.5), pz + sz * (a0 + 1.5); bot = min(self.sample(xm, zm), -0.4) - 0.3
            # deck caminhavel
            d4 = [PP(a0, -W / 2, yd), PP(a1, -W / 2, yd), PP(a1, W / 2, yd), PP(a0, W / 2, yd)]
            self.B.quad(PAVER, d4, (0, 1, 0), COLM['path'] if q % 2 == 0 else COLM['path2'])
            self.g.poly('mprom', [(p[0], p[2]) for p in d4])
            # corpo de pedra: lados inclinados (1:1,3) ate o fundo
            run = 1.5 + (yd - bot) * 0.75
            for sg in (-1, 1):
                t0, t1 = PP(a0, sg * (W / 2 + 0.55), yd - 0.35), PP(a1, sg * (W / 2 + 0.55), yd - 0.35)
                b0, b1 = PP(a0, sg * (W / 2 + 0.55 + run), bot), PP(a1, sg * (W / 2 + 0.55 + run), bot)
                nrm = (rx * sg, 0.8, rz * sg); l = math.sqrt(nrm[0] ** 2 + nrm[1] ** 2 + nrm[2] ** 2); nrm = (nrm[0] / l, nrm[1] / l, nrm[2] / l)
                self.B.quad(STONE, [t0, t1, b1, b0], nrm, COLM['rock2'] if q % 2 else COLM['rock1'])
                e0, e1 = PP(a0, sg * (W / 2), yd), PP(a1, sg * (W / 2), yd)
                self.B.quad(STONE, [PP(a0, sg * (W / 2), yd), PP(a1, sg * (W / 2), yd), t1, t0], (rx * sg * 0.5, 0.8, rz * sg * 0.5), COLM['conc2'])
                # mureta
                c4 = [(PP(a0, sg * W / 2, 0)[0], PP(a0, sg * W / 2, 0)[2]), (PP(a1, sg * W / 2, 0)[0], PP(a1, sg * W / 2, 0)[2]), (PP(a1, sg * (W / 2 - 0.35), 0)[0], PP(a1, sg * (W / 2 - 0.35), 0)[2]), (PP(a0, sg * (W / 2 - 0.35), 0)[0], PP(a0, sg * (W / 2 - 0.35), 0)[2])]
                self.B.obox_pts(c4, yd, yd + 0.55, COLM['conc'], STONE, True, False)
            # fundo da mureta so ate onde o corpo de pedra e visivel
            # blocos (enrocamento) em cima do talude, da linha d'agua para cima
            tw = (yd - 0.35 + 0.2) / max(yd - 0.35 - bot, 1.0)
            for sg in (-1, 1):
                for _ in range(2):
                    t = self.rnd.uniform(0.0, min(tw + 0.12, 0.95)); a_ = a0 + self.rnd.uniform(0, 3.0)
                    o = sg * (W / 2 + 0.55 + run * t); yy = (yd - 0.35) + (bot - (yd - 0.35)) * t
                    p = PP(a_, o, 0)
                    self.rock(p[0], max(yy, WATER_Y - 0.1) - 0.1, p[2], self.rnd.uniform(0.7, 1.25), self.rnd.choice((COLM['rock1'], COLM['rock2'], COLM['rock3'], COLM['rock4'])), 0.75)
        hx, _, hz = PP(length, 0, 0)
        if kind == 'farol':
            import cais; cais.forte(self, hx, hz, sx, sz, yd, scheme)
        else:
            self.B.cyl(hx, hz, 5.2, min(self.sample(hx, hz), -3.0) - 0.4, yd, COLM['rock2'], 14, STONE, False)
            for k in range(14):
                a0, a1 = 2 * math.pi * k / 14, 2 * math.pi * (k + 1) / 14
                self.B.tri(PAVER, (hx, yd, hz), (hx + math.cos(a1) * 5.0, yd, hz + math.sin(a1) * 5.0), (hx + math.cos(a0) * 5.0, yd, hz + math.sin(a0) * 5.0), (0, 1, 0), COLM['path'])
            self.g.poly('mprom', [(hx + math.cos(2 * math.pi * k / 14) * 5.0, hz + math.sin(2 * math.pi * k / 14) * 5.0) for k in range(14)])
            for k in range(14):
                a0, a1 = 2 * math.pi * k / 14, 2 * math.pi * (k + 1) / 14
                self.B.obox_pts([(hx + math.cos(a0) * 5.1, hz + math.sin(a0) * 5.1), (hx + math.cos(a1) * 5.1, hz + math.sin(a1) * 5.1), (hx + math.cos(a1) * 4.7, hz + math.sin(a1) * 4.7), (hx + math.cos(a0) * 4.7, hz + math.sin(a0) * 4.7)], yd, yd + 0.5, COLM['conc'], STONE, True, False)
            for k in range(10):
                a = 2 * math.pi * k / 10 + 0.2
                self.rock(hx + math.cos(a) * 6.4, WATER_Y + self.rnd.uniform(0, 0.25), hz + math.sin(a) * 6.4, self.rnd.uniform(0.8, 1.2), self.rnd.choice((COLM['rock1'], COLM['rock3'], COLM['rock2'])), 0.7)
        if kind != 'farol': self.beacon(hx, hz, yd, scheme)
        # postes ao longo do molhe
        for a in np.arange(14.0, length - 8.0, 22.0):
            p = PP(a, W / 2 - 0.55, 0); self.lamp(p[0], p[2], yd)
        self.items['jetties'].append({'x': round(px, 1), 'z': round(pz, 1), 'dx': round(sx, 3), 'dz': round(sz, 3), 'len': round(length, 1), 'kind': kind})

    # ------------------------------------------------------------------ orquestra
    def build(self):
        plan = []
        for fr, closed in self.shorelines():
            kinds = self.classify(fr, closed); runs = self.active_runs(fr, kinds); plan.append((fr, runs))
            for (i0, i1, kind, prom) in runs:
                if kind == 'rio' and prom:
                    for k in range(i0 + 20, i1 - 20, 45):
                        if self.rnd.random() < 0.8 and len(self.dock_sites) < 60:
                            g = self.dock_geom(fr[k])
                            if g and not any(math.hypot(g['x0'] - o['x0'], g['z0'] - o['z0']) < 60 for o in self.dock_sites): self.dock_sites.append(g)
        for fr, runs in plan:
            for (i0, i1, kind, prom) in runs:
                if kind == 'cais':
                    import cais; cais.run_cais(self, fr, i0, i1)
                    self.items['runs'].append({'kind': 'cais', 'len': round(3.0 * (i1 - i0), 1), 'x0': round(fr[i0]['x']), 'z0': round(fr[i0]['z']), 'x1': round(fr[i1]['x']), 'z1': round(fr[i1]['z'])})
                    self.cais_runs.append((fr, i0, i1)); continue
                self.run_stone(fr, i0, i1, kind)
                if prom: self.run_prom(fr, i0, i1, kind)
                else: self.run_rail(fr, i0, i1)
                self.items['runs'].append({'kind': kind, 'len': round(3.0 * (i1 - i0), 1), 'x0': round(fr[i0]['x']), 'z0': round(fr[i0]['z']), 'x1': round(fr[i1]['x']), 'z1': round(fr[i1]['z'])})
        for d in self.dock_sites: self.draw_dock(d)
        self.build_marinas()
        import cais
        for fr, i0, i1 in self.cais_runs:                               # as pontas de cada trecho de cais terminam em formacoes de rocha
            for (k, sg) in ((i0, -1), (i1, 1)):
                f = fr[k]; cais.outcrop(self, f['x'] + f['nx'] * 1.5 + f['tx'] * sg * 2.0, f['z'] + f['nz'] * 1.5 + f['tz'] * sg * 2.0, 12, 3.6)
        for fr, runs in plan: self.fringe(fr, runs)
        self.items['solids'] = self.solids
        return self

    def build_marinas(self):
        """uma marina (3 pontoes + clube nautico) em cada ponta, no cais, depois do calcadao da praca (60 a 330 m)"""
        import cais
        for (ex, ez) in self.ends:
            cands = []
            for fr, i0, i1 in self.cais_runs:
                for k in range(i0 + 6, i1 - 6, 4):
                    f = fr[k]; d = math.hypot(f['x'] - ex, f['z'] - ez)
                    if 70 < d < 340: cands.append((d, fr, k))
            cands.sort(key=lambda t: t[0]); done = 0
            for d, fr, k in cands:
                if done >= 2: break
                f = fr[k]
                if any(math.hypot(f['x'] - ox, f['z'] - oz) < 150 for ox, oz in getattr(self, '_mar_pos', [])): continue
                a = (f['x'], f['z']); nx_, nz_ = f['nx'], f['nz']
                if self.sample(a[0] - nx_ * 22, a[1] - nz_ * 22) > -1.0: continue
                n_boats = cais.marina(self, a, nx_, nz_)
                if n_boats < 4: continue
                cais.shed(self, a, nx_, nz_)
                self._mar_pos = getattr(self, '_mar_pos', []) + [a]; done += 1
                self.items.setdefault('marinas', []).append({'x': round(a[0], 1), 'z': round(a[1], 1), 'barcos': n_boats})

    def fringe(self, fr, runs):
        """margem natural (resto do litoral das terras da cidade): faixa de blocos grandes de pedra, para a borda d'agua nunca ser so grama"""
        if len(fr) < 600: return                                        # so os contornos grandes (terras da cidade); costas de fora nao sao alcancaveis
        covered = np.zeros(len(fr), bool)
        for (i0, i1, kind, prom) in runs: covered[max(i0 - 3, 0):i1 + 4] = True
        ii = lambda x: int(min(max(round(x / CELL), 0), NX - 1)); jj = lambda z: int(min(max(round(z / CELL), 0), NZ - 1))
        n = 0
        import cais
        for k in range(0, len(fr), 3):                                  # a cada ~9 m
            if covered[k]: continue
            if k % 24 == 0 and not (self.geo.beach_zone[jj(fr[k]['z']), ii(fr[k]['x'])] and self.geo.Dsea[jj(fr[k]['z']), ii(fr[k]['x'])] < 80): cais.outcrop(self, fr[k]['x'] + fr[k]['nx'] * 1.0, fr[k]['z'] + fr[k]['nz'] * 1.0, 8, 3.2)
            f = fr[k]; x, z = f['x'], f['z']
            if self.geo.beach_zone[jj(z), ii(x)] and self.geo.Dsea[jj(z), ii(x)] < 80: continue            # praia: areia, sem pedra
            if self.rnd.random() < 0.1: continue
            for _ in range(self.rnd.choice((2, 2, 3))):
                o = self.rnd.uniform(-0.3, 3.0); s = self.rnd.uniform(0, 8.0)
                px, pz = x + f['nx'] * o + f['tx'] * s, z + f['nz'] * o + f['tz'] * s
                if self.blocked(px, pz, 0): continue
                y = max(self.sample(px, pz), WATER_Y - 0.3)
                self.rock(px, y, pz, self.rnd.uniform(1.0, 2.6), self.rnd.choice((COLM['rock1'], COLM['rock2'], COLM['rock3'], COLM['rock4'], COLM['rockd'])), 0.85); n += 1
        self.stats['fringe'] = self.stats.get('fringe', 0) + n

    def sea_dir(self, x, z, r):
        """direcao (em graus de varredura de 4) para a agua funda mais proxima: distancia ate hf < -1.5"""
        best = None
        for q in range(0, 360, 4):
            a = math.radians(q); dx, dz = math.cos(a), math.sin(a); d = r
            while d < 300 and self.sample(x + dx * d, z + dz * d) > -1.5: d += 4.0
            if d >= 300: continue
            # nao pode atravessar a cidade: o trecho ate a agua nao pode passar por rua/orla alem da propria praca
            if best is None or d < best[0] - 1e-6: best = (d, dx, dz)
        return best

    def jetties(self):
        for p in self.plazas:
            x, z, r, y = p['x'], p['z'], p['r'], p['y']
            if 1500 < x < 3000:                                              # foz do rio: dois molhes paralelos ao canal, abrindo um pouco para fora
                sx, sz = (-0.18, 0.984) if x < 2450 else (0.18, 0.984)
                px, pz = x + sx * (r - 1.0), z + sz * (r - 1.0)
                self.jetty_dir(px, pz, sx, sz, y + 0.03, 100.0, 'baliza', 'red' if x < 2450 else 'green')
                continue
            bd = self.sea_dir(x, z, r)
            if bd is None: continue
            d, sx, sz = bd
            px, pz = x + sx * (r - 1.0), z + sz * (r - 1.0)
            self.jetty_dir(px, pz, sx, sz, y + 0.03, min(max(d + 60.0, 110.0), 200.0), 'farol', 'red' if x < 1500 else 'blue')
        return self

    # ------------------------------------------------------------------ lotes e validacao
    def reserve_lots(self, clearance=14.0, setback=45.0):
        """REGRA DA BORDA D'AGUA: nenhum lote (casa ou predio da Etapa E) a menos de 'setback' m da agua (rio, lagoa, canais) nem encostado no calcadao ribeirinho;
        esses lotes viram parque/praca/estacionamento (Etapa F). A frente de praia e a Av. Beira-Mar ja ficam a mais de 70 m do mar."""
        grid = {}
        for (x, z) in self.band_pts: grid.setdefault((int(x // 32), int(z // 32)), []).append((x, z))
        def near(x, z, r):
            ci, cj = int(x // 32), int(z // 32); k = int(r // 32) + 1
            for i in range(ci - k, ci + k + 1):
                for j in range(cj - k, cj + k + 1):
                    for (px, pz) in grid.get((i, j), ()):
                        if math.hypot(px - x, pz - z) < r: return True
            return False
        D = T._chamfer8(self.hf < WATER_Y)
        def dwater(x, z): return float(D[min(max(int(round(z / 8.0)), 0), D.shape[0] - 1), min(max(int(round(x / 8.0)), 0), D.shape[1] - 1)])
        keep = []; drop = 0; drop_w = 0
        for l in self.P.lots:
            r = l['rect']; pts = [(p[0], p[1]) for p in r] + [(sum(p[0] for p in r) / 4, sum(p[1] for p in r) / 4)]
            if any(near(x, z, clearance) for x, z in pts): drop += 1
            elif any(dwater(x, z) < setback for x, z in pts): drop_w += 1
            else: keep.append(l)
        self.P.lots = keep; self.stats['lots_dropped'] = drop + drop_w; self.stats['lots_dropped_water'] = drop_w
        bad = [h['k'] + 1 for h in self.P.houses if any(near(p[0], p[1], 6.0) for p in h['lot']['rect'])]
        self.stats['houses_in_band'] = bad
        self.stats['houses_water'] = [(h['k'] + 1, round(min(dwater(p[0], p[1]) for p in h['lot']['rect']))) for h in self.P.houses if min(dwater(p[0], p[1]) for p in h['lot']['rect']) < 30.0]
        self.items['setback_m'] = setback
        self.items['bordas_uso'] = {'rio': 'calcadao ribeirinho + docas; predios so a 45 m ou mais', 'lagoa': 'calcadao + parque', 'canal': 'enrocamento natural; sem construcao',
                                    'pontas': 'Parque do Farol (praca, alameda, quadra, playground, quiosque, mirante)', 'praia': 'orla + Av. Beira-Mar; predios do outro lado da avenida'}
        return self

    def validate(self):
        from validate_ground import raster
        out = []; ok = True
        M = raster(self.g, ['mprom', 'asphalt', 'sidewalk', 'curb', 'median', 'island', 'prom', 'wall', 'stairs', 'pier'])
        er = lambda m: m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
        for nm in ('asphalt', 'sidewalk', 'curb', 'median', 'island', 'prom', 'wall', 'stairs'):
            ov = int((er(M['mprom']) & er(M[nm])).sum())
            good = ov < 60; ok &= good
            out.append(f'  calcadao ribeirinho x {nm}: {ov} m2 {"ok" if good else "SOBREPOE"}')
        good = len(self.items['lighthouses']) >= 4; ok &= good
        out.append(f'  farois/balizas: {len(self.items["lighthouses"])} (esperado 4: 2 farois + 2 balizas) {"ok" if good else "FALTAM"}')
        bad = [j for j in self.items['jetties'] if self.sample(j['x'] + j['dx'] * j['len'], j['z'] + j['dz'] * j['len']) > -1.0]
        good = not bad; ok &= good
        out.append(f'  molhes terminam em agua funda: {len(self.items["jetties"]) - len(bad)}/{len(self.items["jetties"])} {"ok" if good else "CURTOS"}')
        bad = [d for d in self.items['docks'] if d.get('w', 2.3) >= 2.3 and self.sample(d['x'] + d['dx'] * d['len'], d['z'] + d['dz'] * d['len']) > -0.6]
        good = not bad; ok &= good
        out.append(f'  docas terminam na agua: {len(self.items["docks"]) - len(bad)}/{len(self.items["docks"])}; barcos {len(self.items["boats"])} {"ok" if good else "RASAS"}')
        good = not self.stats.get('houses_in_band') and not self.stats.get('houses_water'); ok &= good
        out.append(f'  casas do jogador longe da margem urbana: {"ok" if good else "CONFLITO " + str(self.stats.get("houses_in_band"))}; lotes comuns retirados da margem: {self.stats.get("lots_dropped", 0)} ({self.stats.get("lots_dropped_water", 0)} por ficarem a menos de 45 m da agua); blocos de pedra natural: {self.stats.get("fringe", 0)}; colisoes de guarda-corpo: {len(self.solids)}')
        out.append(f'  enrocamento {self.stats["rip_m"]:.0f} m, calcadao {self.stats["prom_m"]:.0f} m, {self.stats["rocks"]} blocos de pedra, {len(self.items["lamps"])} postes, {len(self.items["benches"])} bancos, {self.items["trees"]} arvores')
        return ok, out
