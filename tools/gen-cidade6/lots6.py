"""Cidade 6 - quadras -> lotes -> construcoes. Reserva os lotes das 17 casas do jogador (Cidade 5, city2.glb)."""
import math, random, json, os
import numpy as np
from shapely.geometry import Polygon, box as sbox, Point
from mesh import rgb, shade, mix, WHITE, Frame
from plan6 import *
from roads6 import Y_LAWN, Y_WALK
import buildings6 as B6

HERE = os.path.dirname(os.path.abspath(__file__))
CITY2 = os.path.join(HERE, '..', '..', 'app', 'src', 'main', 'assets', 'hds', 'city2.json')

# casas do jogador: bairro da Cidade 5 (indice k = "Casa k+1")
HOUSE_BAIRRO = {0: 'Vila Esperança', 11: 'Vila Esperança', 7: 'Vila Esperança', 12: 'Vila Esperança', 8: 'Vila Esperança',
                9: 'Parque das Flores', 10: 'Parque das Flores', 13: 'Parque das Flores',
                4: 'Jardim Central', 5: 'Jardim Central', 6: 'Jardim Central',
                14: 'Recanto do Sul', 15: 'Recanto do Sul', 3: 'Recanto do Sul',
                2: 'Alto da Colina', 1: 'Alto da Colina', 16: 'Península Real'}
# regiao (x0, x1, z0, z1) de cada bairro na Cidade 6
BAIRRO_REG = {'Vila Esperança': (120, 600, 1340, 1650), 'Parque das Flores': (600, 1560, 240, 640), 'Jardim Central': (1800, 2440, 540, 1040),
              'Recanto do Sul': (1800, 2440, 1340, 1540), 'Alto da Colina': (600, 1560, 140, 240), 'Península Real': (1800, 2440, 1040, 1240)}
FRONT_SB = 7.0       # recuo da frente dos lotes das casas do jogador
FAMILIES = (('ranch', 'craftsman'), ('colonial', 'cape'), ('craftsman', 'ranch'), ('cape', 'colonial'), ('ranch', 'moderna'), ('colonial', 'ranch'), ('craftsman', 'colonial'))


class Lots:
    def __init__(self, P, G, M, seed=66):
        self.P, self.G, self.M = P, G, M
        self.rnd = random.Random(seed)
        self.B = B6.Builder(M, self.rnd)
        self.player = []              # manifesto das casas do jogador
        self.trees = []               # (x, z, tipo, escala) -> props
        self.lots = []
        self.plots = json.load(open(CITY2))['plots']

    # ------------------------------------------------------------ chao das quadras
    def lawn(self, poly, mat='grama', y=Y_LAWN, col=WHITE):
        M = self.M
        c = poly.centroid
        for x0 in range(int(poly.bounds[0] // 125) * 125, int(poly.bounds[2]) + 1, 125):
            for z0 in range(int(poly.bounds[1] // 125) * 125, int(poly.bounds[3]) + 1, 125):
                q = poly.intersection(sbox(x0, z0, x0 + 125, z0 + 125))
                if q.is_empty: continue
                M.free('lotes'); M.m(mat); M.shp(q, y, col)
        # borda (degrau ate o chao): so aparece onde nao ha calcada encostada
        M.m('concreto')
        for g in getattr(poly, 'geoms', [poly]):
            pts = list(g.exterior.coords)
            for k in range(len(pts) - 1):
                a, b = pts[k], pts[k + 1]
                if math.hypot(b[0] - a[0], b[1] - a[1]) < 0.05: continue
                M.at((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                M.quad((a[0], -0.3, a[1]), (b[0], -0.3, b[1]), (b[0], y, b[1]), (a[0], y, a[1]), (215, 212, 205))
        M.free()

    # ------------------------------------------------------------ especiais
    SPECIAL = {'prefeitura': (1140, 940, 'W'), 'igreja': (780, 1060, 'E'), 'hospital': (1380, 700, 'N'),
               'escola_o': (240, 790, 'N'), 'escola_n': (960, 390, 'N'), 'escola_l': (2160, 790, 'N')}

    def find_specials(self):
        self.special = {}
        for nm, (x, z, side) in self.SPECIAL.items():
            for bi, blk in enumerate(self.P.blocks):
                if blk['poly'].contains(Point(x, z)): self.special[bi] = (nm, side); break

    def row_on_avenue(self, blk, side):
        minx, minz, maxx, maxz = blk['poly'].bounds
        line = {'N': ('z', minz), 'S': ('z', maxz), 'W': ('x', minx), 'E': ('x', maxx)}[side]
        for r in self.P.roads:
            if r['kind'] not in ('av', 'orla'): continue
            (x0, z0), (x1, z1) = r['pts'][0], r['pts'][-1]
            hr = half_row(r['kind'])
            if line[0] == 'z' and abs(z0 - z1) < 1 and abs(abs(line[1] - z0) - hr) < 3 and min(x0, x1) - 5 <= (minx + maxx) / 2 <= max(x0, x1) + 5: return True
            if line[0] == 'x' and abs(x0 - x1) < 1 and abs(abs(line[1] - x0) - hr) < 3 and min(z0, z1) - 5 <= (minz + maxz) / 2 <= max(z0, z1) + 5: return True
        return False

    # ------------------------------------------------------------ casas do jogador
    def plan_player(self):
        """distribui as 17 casas nas fileiras dos seus bairros (no maximo 1 por fileira, longe das esquinas)"""
        rows = {}
        by = {}
        for k, b in HOUSE_BAIRRO.items(): by.setdefault(b, []).append(k)
        cand = {}
        for bi, blk in enumerate(self.P.blocks):
            if blk['zone'] != 'suburbio' or bi in self.special: continue
            for nm, (x0, x1, z0, z1) in BAIRRO_REG.items():
                if x0 <= blk['cx'] <= x1 and z0 <= blk['cz'] <= z1: cand.setdefault(nm, []).append(bi)
        self.reserved = {}            # (bloco, lado) -> [k]
        for nm, ks in by.items():
            bl = sorted(cand.get(nm, []), key=lambda i: (self.P.blocks[i]['cz'], self.P.blocks[i]['cx']))
            if nm in ('Vila Esperança', 'Recanto do Sul'): bl = bl[::-1]          # perto da praia primeiro
            slots = [(b, s) for b in bl for s in (('S', 'N') if nm in ('Vila Esperança', 'Recanto do Sul') else ('N', 'S')) if not self.row_on_avenue(self.P.blocks[b], s)]
            step = max(1, len(slots) // max(1, len(ks)))
            for i, k in enumerate(ks):
                sl = slots[min(i * step, len(slots) - 1)] if slots else None
                if sl is None: continue
                while sl in self.reserved and slots:                              # nao repete fileira
                    j = slots.index(sl) + 1; sl = slots[j % len(slots)]
                self.reserved.setdefault(sl, []).append(k)

    # ------------------------------------------------------------ suburbio
    def suburb(self, bi, blk):
        P = self.P; poly = blk['poly']
        minx, minz, maxx, maxz = poly.bounds
        Lx, Lz = maxx - minx, maxz - minz
        self.lawn(poly)
        horiz = Lx >= Lz
        L, D = (Lx, Lz) if horiz else (Lz, Lx)
        two = D >= 46
        sides = ('N', 'S') if horiz else ('W', 'E')
        rnd = self.rnd
        for si, side in enumerate(sides if two else sides[:1]):
            depth = D / 2 if two else D
            if self.row_on_avenue(blk, side):
                self.commercial_row(side, minx, maxx, minz, maxz, L, depth); continue
            res = self.reserved.get((bi, side), [])
            if not res and (bi, sides[1 - si]) in self.reserved and not two: res = []
            fam = FAMILIES[rnd.randrange(len(FAMILIES))]
            w0 = rnd.uniform(16.5, 19.0)
            sf = rnd.choice((6.0, 6.5, 7.0, 7.5))
            picket = rnd.random() < 0.35
            pal_base = rnd.random()
            # sequencia de larguras: lotes reservados no meio da fileira
            res_w = []
            for k in res:
                pl = self.plots[k]; hw, hd = pl['x1'] - pl['x0'], pl['z1'] - pl['z0']
                res_w.append((k, max(hw + 9.0, 18.0), hw, hd))
            free_len = L - sum(r[1] for r in res_w)
            n = max(0, int(free_len / w0)); wn = free_len / n if n else 0
            seq = [('n', wn)] * n
            for j, r in enumerate(res_w):
                pos = int(len(seq) * (j + 1) / (len(res_w) + 1)); pos = max(2, min(len(seq) - 2, pos)) if len(seq) >= 4 else len(seq) // 2
                seq.insert(pos, ('p', r))
            s = 0.0
            for q, (kind, val) in enumerate(seq):
                wl = val if kind == 'n' else val[1]
                F = self.frame(side, minx, maxx, minz, maxz, s)
                if kind == 'p':
                    self.player_lot(F, wl, depth, val, side, blk)
                else:
                    style = fam[0] if rnd.random() < 0.7 else fam[1]
                    pal = self.palette(style, pal_base)
                    gside = 1 if (q % 2 == 0) else -1
                    info = self.B.house(F, wl, depth, style, pal, sf, gside, picket, True, q == 0, q == len(seq) - 1)
                    for (tu, tv) in info['trees_front']: self.trees.append((*F.xz(tu, tv), 'folhosa', rnd.uniform(0.8, 1.1)))
                    if rnd.random() < 0.7: self.trees.append((*F.xz(rnd.uniform(2, wl - 2), rnd.uniform(info['back'][0] + 3, depth - 2.5)), rnd.choice(('folhosa', 'folhosa', 'conifera')), rnd.uniform(0.9, 1.3)))
                s += wl

    def commercial_row(self, side, minx, maxx, minz, maxz, L, depth):
        r = self.rnd; B = self.B
        signs = [rgb(c) for c in ('#C8102E', '#0057B8', '#FFB81C', '#00843D', '#E35205', '#6D2077', '#2D2926', '#00A3AD')]
        walls = [rgb(c) for c in ('#F2EDE4', '#E9DFD0', '#DDE3E6', '#EFE3D3', '#D8D2C6')]
        s = 0.0; first = True
        while s < L - 15:
            rest = L - s
            if first: kind = 'posto' if r.random() < 0.6 else 'galeria'
            else: kind = r.choice(('mercado', 'galeria', 'galeria', 'lanchonete', 'posto'))
            w = {'posto': 42, 'mercado': 80, 'galeria': r.uniform(45, 70), 'lanchonete': 26}[kind]
            if rest - w < 20: w = rest
            F = self.frame(side, minx, maxx, minz, maxz, s)
            if kind == 'posto': B.gas_station(F, w, depth - 1, r.choice(signs))
            else:
                pk = 15.0 if depth > 30 else 8.0
                B.parking(F, 1, w - 1, 0.5, pk, self.park_car)
                bd = min(depth - pk - 2, 24 if kind == 'mercado' else 16)
                Fs = Frame(F.xz(1, pk + 0.5), (F.ux, F.uz))
                if kind == 'galeria':
                    n = max(2, int((w - 2) / 12)); uw = (w - 2) / n
                    for k in range(n): B.shop_row(Frame(Fs.xz(k * uw, 0), (F.ux, F.uz)), uw - 0.05, bd, r.choice(signs), r.choice(walls), r.choice((5.0, 5.5, 6.2)))
                else:
                    B.shop_row(Fs, w - 2, bd, r.choice(signs), r.choice(walls), 7.5 if kind == 'mercado' else 5.0)
            s += w; first = False

    def park_car(self, x, z, dx, dz):
        self.parked.append((x, z, dx, dz))

    def special_block(self, bi, blk, nm, side):
        poly = blk['poly']; minx, minz, maxx, maxz = poly.bounds; B = self.B; r = self.rnd
        for _ in range(20):                                   # retangulo interno (quadras de bordas curvas)
            if sbox(minx, minz, maxx, maxz).buffer(-0.5).within(poly): break
            minx += 1.5; minz += 1.5; maxx -= 1.5; maxz -= 1.5
        L = (maxx - minx) if side in ('N', 'S') else (maxz - minz); D = (maxz - minz) if side in ('N', 'S') else (maxx - minx)
        F = self.frame(side, minx, maxx, minz, maxz, 0.0)
        if nm.startswith('escola'):
            self.lawn(poly); B.school(F, L, D, self.park_car)
            for _ in range(30):
                x, z = r.uniform(minx + 3, maxx - 3), r.uniform(minz + 3, maxz - 3)
                if not any(abs(x - c[0]) < 3 and abs(z - c[1]) < 3 for c in []): pass
            return
        self.lawn(poly, 'paver', Y_WALK, (236, 232, 224))
        if nm == 'prefeitura': B.city_hall(F, L, D)
        elif nm == 'igreja':
            B.church(F, L * 0.6, D)
            # praca da matriz: jardim e arvores na outra metade
            Fp = Frame(F.xz(L * 0.62, 6), (F.ux, F.uz))
            self.M.free('lotes'); self.M.m('grama')
            self.M.poly([Fp.p(0, 0, Y_WALK + 0.03), Fp.p(L * 0.36, 0, Y_WALK + 0.03), Fp.p(L * 0.36, D - 12, Y_WALK + 0.03), Fp.p(0, D - 12, Y_WALK + 0.03)], WHITE, (0, 1, 0))
            for k in range(14): self.trees.append((*Fp.xz(r.uniform(3, L * 0.36 - 3), r.uniform(3, D - 15)), 'folhosa', r.uniform(0.9, 1.2)))
        elif nm == 'hospital': B.hospital(F, L - 4, min(D - 4, 40))

    def frame(self, side, minx, maxx, minz, maxz, s):
        if side == 'N': return Frame((minx + s, minz), (1, 0))
        if side == 'S': return Frame((maxx - s, maxz), (-1, 0))
        if side == 'W': return Frame((minx, maxz - s), (0, -1))
        return Frame((maxx, minz + s), (0, 1))

    def palette(self, style, base):
        r = self.rnd
        if style == 'moderna':
            wall = r.choice(B6.STUCCO); wm = 'reboco'
        elif r.random() < 0.22:
            wall = r.choice(B6.BRICK_T); wm = 'tijolo'
        else:
            wall = B6.SIDING[int((base * 7 + r.random() * 5)) % len(B6.SIDING)]; wm = 'siding'
        roof = r.choice(B6.ROOF); rm = 'telha'
        return (wall, wm, roof, rm, r.choice(B6.DOORC), r.choice(B6.SHUT))

    def player_lot(self, F, w, d, val, side, blk):
        k, W_, hw, hd = val
        r = self.rnd; B = self.B; M = self.M
        # gramado ja existe; cerca de fundo/laterais e caixa de correio; casa em si vem do city2.glb no jogo
        fc = B6.FENCE_W[r.randrange(len(B6.FENCE_W))]
        vf = FRONT_SB + hd * 0.6
        B.box(F, w - 0.12, w, vf, d - 0.1, Y_LAWN, Y_LAWN + 1.8, fc, 'cerca')
        B.box(F, 0, 0.12, vf, d - 0.1, Y_LAWN, Y_LAWN + 1.8, fc, 'cerca')
        B.box(F, 0, w, d - 0.22, d - 0.1, Y_LAWN, Y_LAWN + 1.8, fc, 'cerca')
        B.box(F, 1.0, 1.1, 0.4, 0.5, Y_LAWN, Y_LAWN + 1.05, (90, 90, 92), 'metal')
        B.box(F, 0.83, 1.27, 0.3, 0.75, Y_LAWN + 1.0, Y_LAWN + 1.3, rgb('#7A2E2E'), 'metal')
        cx, cz = F.xz(w / 2, FRONT_SB + hd / 2)
        fx, fz = -F.vx, -F.vz                                     # frente da casa: para a rua
        self.player.append({'k': k, 'casa': f'Casa {k + 1}', 'modelo': self.plots[k]['name'], 'bairro': HOUSE_BAIRRO[k],
                            'centro': [round(cx, 2), round(Y_LAWN, 2), round(cz, 2)], 'frente': [round(fx, 4), round(fz, 4)],
                            'yaw_graus': round(math.degrees(math.atan2(fx, fz)), 2),
                            'lote': [[round(p[0], 2), round(p[1], 2)] for p in F.rect(0, w, 0, d)], 'lote_m': [round(w, 1), round(d, 1)],
                            'casa_m': [round(hw, 1), round(hd, 1)], 'recuo_frente_m': FRONT_SB})
        if d < FRONT_SB + hd + 3: print(f'  aviso: lote da casa {k + 1} raso ({d:.1f} m para {hd:.1f} m de casa)')

    # ------------------------------------------------------------ centro
    def centro(self, bi, blk):
        poly = blk['poly']; r = self.rnd; B = self.B
        minx, minz, maxx, maxz = poly.bounds
        self.lawn(poly, 'paver', Y_WALK, (236, 232, 224))
        cx, cz = (minx + maxx) / 2, (minz + maxz) / 2
        dc = math.hypot(cx - 1140, cz - 1000)
        hmax = int(max(5, 30 - dc / 22))
        w, d = maxx - minx, maxz - minz
        # quadras de torres: 2 a 4 torres de 30-40 m sobre praca, com jardins e espelho d'agua
        if dc < 360 and r.random() < 0.62:
            tints = ((205, 215, 222), (225, 225, 215), (190, 208, 200), (215, 205, 190), (175, 190, 210))
            pods = ((70, 75, 82), (150, 140, 128), (205, 200, 190), (110, 100, 92))
            n = r.choice((2, 2, 3, 4)); placed = []
            slots = [(minx + 4, minz + 4), (maxx - 4, minz + 4), (minx + 4, maxz - 4), (maxx - 4, maxz - 4)]
            r.shuffle(slots)
            for (sx, sz) in slots[:n]:
                tw = r.uniform(30, 40); td = r.uniform(28, 38)
                x0 = sx if sx < cx else sx - tw; z0 = sz if sz < cz else sz - td
                B.tower(Frame((x0, z0), (1, 0)), tw, td, r.randint(max(12, hmax - 8), hmax + 10), r.choice(tints), r.choice(pods), r.choice(((230, 228, 222), (60, 64, 70), (180, 160, 120))))
                placed.append(sbox(x0 - 3, z0 - 3, x0 + tw + 3, z0 + td + 3))
            from shapely.ops import unary_union
            free = sbox(minx + 3, minz + 3, maxx - 3, maxz - 3).difference(unary_union(placed))
            self.M.free('lotes'); self.M.m('grama')
            for g in getattr(free, 'geoms', [free]):
                if g.area < 60: continue
                gg = g.buffer(-3)
                if gg.is_empty: continue
                self.M.shp(gg, Y_WALK + 0.03, WHITE)
                for _ in range(int(gg.area / 90)):
                    p = gg.representative_point() if False else None
                    x = r.uniform(gg.bounds[0], gg.bounds[2]); z = r.uniform(gg.bounds[1], gg.bounds[3])
                    if gg.contains(Point(x, z)): self.trees.append((x, z, 'folhosa', r.uniform(0.9, 1.2)))
            return
        # perimetro de predios colados (frente para as 4 ruas), patio no miolo
        Dp = r.uniform(17, 22)
        walls = [rgb(c) for c in ('#F2ECE0', '#E7D9C4', '#D9DDE2', '#F4E8D8', '#E2CFC0', '#CFD8D2', '#EADFCF', '#DCD3E3', '#C9B8A6', '#E8E1D5')]
        awns = [rgb(c) for c in ('#B83A3A', '#2E6A4A', '#2F4A7A', '#C9822E', '#6A2E5A', '#3A3A3A')]
        for side in ('N', 'E', 'S', 'W'):
            Lside = w if side in ('N', 'S') else d
            s = 0.0
            start, end = (0.0, Lside - Dp)                       # cada lado comeca na sua quina (quinas sem sobreposicao)
            s = start
            while s < end - 6:
                pw = min(r.uniform(14, 28), end - s)
                if end - s - pw < 9: pw = end - s
                F = self.frame(side, minx, maxx, minz, maxz, s)
                fl = max(3, min(hmax, int(r.uniform(0.45, 1.0) * hmax)))
                fac = 'janelas' if r.random() < 0.6 else 'escritorio'
                if fac == 'escritorio': fl = max(3, int(fl * 0.85))
                B.midrise(F, pw - 0.15, Dp, fl, r.choice(walls), fac, True, r.choice(awns) if r.random() < 0.6 else None)
                s += pw
        # miolo: patio ajardinado
        inner = sbox(minx + Dp + 1, minz + Dp + 1, maxx - Dp - 1, maxz - Dp - 1)
        if inner.area > 50:
            self.M.free('lotes'); self.M.m('grama'); self.M.shp(inner, Y_WALK + 0.02, WHITE)
            for _ in range(int(inner.area / 120)):
                x = r.uniform(inner.bounds[0] + 2, inner.bounds[2] - 2); z = r.uniform(inner.bounds[1] + 2, inner.bounds[3] - 2)
                self.trees.append((x, z, 'folhosa', r.uniform(0.8, 1.1)))

    def orla(self, bi, blk):
        poly = blk['poly']; r = self.rnd; B = self.B
        minx, minz, maxx, maxz = poly.bounds
        self.lawn(poly, 'paver', Y_WALK, (236, 232, 224))
        w, d = maxx - minx, maxz - minz
        near_sea = maxz > 1650
        if near_sea:      # hotel/residencial de frente para o mar: podio + 2 laminas, deck com piscina
            F = Frame((maxx - 2, maxz - 2), (-1, 0))
            hw = (w - 10) / 2
            for k in range(2):
                Fk = Frame(F.xz(2 + k * (hw + 6), 0), (-1, 0))
                B.midrise(Fk, hw, min(18, d - 6), r.randint(14, 24), r.choice([rgb(c) for c in ('#F4F1EA', '#EFE6D6', '#E2ECEF', '#F2E9E1')]), 'janelas', True, r.choice(((40, 110, 160), (200, 120, 60), (60, 140, 110))))
            pu0, pu1 = 6, w - 6; pv0, pv1 = min(18, d - 6) + 4, d - 6
            if pv1 - pv0 > 6:
                B.box(F, pu0, pu1, pv0, pv1, Y_WALK, Y_WALK + 0.15, WHITE, 'madeira')
                self.M.m('agua'); self.M.poly([F.p(pu0 + 3, pv0 + 2, Y_WALK + 0.26), F.p(pu1 - 3, pv0 + 2, Y_WALK + 0.26), F.p(pu1 - 3, pv1 - 2, Y_WALK + 0.26), F.p(pu0 + 3, pv1 - 2, Y_WALK + 0.26)], (150, 230, 240), (0, 1, 0))
                for _ in range(4): self.trees.append((*F.xz(r.uniform(pu0, pu1), r.choice((pv0 - 1, pv1 + 1))), 'palmeira', r.uniform(0.9, 1.2)))
        else:
            self.centro(bi, blk)

    # ------------------------------------------------------------ suburbios: lotes ao longo das ruas curvas
    def _depth_to_middle(self, mx, mz, nx, nz, dmax=46.0):
        """distancia ate a faixa de dominio do outro lado da quadra, andando para dentro"""
        from shapely.geometry import LineString as _L
        ray = _L([(mx + nx * 0.5, mz + nz * 0.5), (mx + nx * 140, mz + nz * 140)])
        g = ray.intersection(self.P.row)
        if g.is_empty: A = 140.0
        else:
            A = 140.0
            for q in getattr(g, 'geoms', [g]):
                for c in (q.coords if hasattr(q, 'coords') else []):
                    A = min(A, math.hypot(c[0] - mx, c[1] - mz))
        if A < 2 * 17: return A - 0.6, A
        return min(dmax, A / 2 - 0.3), A

    def _free(self, poly):
        """lote cabe: dentro do terreno livre do suburbio e sem encostar em outro lote"""
        if not poly.buffer(-0.4).within(self.sub_free): return False
        bb = poly.bounds
        for i in range(int(bb[0] // 40), int(bb[2] // 40) + 1):
            for j in range(int(bb[1] // 40), int(bb[3] // 40) + 1):
                for q in self.occ.get((i, j), []):
                    if q.intersects(poly.buffer(-0.35)): return False
        return True

    def _take(self, poly):
        bb = poly.bounds
        for i in range(int(bb[0] // 40), int(bb[2] // 40) + 1):
            for j in range(int(bb[1] // 40), int(bb[3] // 40) + 1): self.occ.setdefault((i, j), []).append(poly)

    def suburbs(self):
        P, G, r = self.P, self.G, self.rnd
        from shapely.ops import unary_union
        sub = [b['poly'] for bi, b in enumerate(P.blocks) if b['zone'] == 'suburbio' and bi not in self.special]
        self.sub_free = unary_union(sub)
        for bi, b in enumerate(P.blocks):
            if b['zone'] == 'suburbio' and bi not in self.special: self.lawn(b['poly'])
        self.occ = {}
        fronts = []
        for i, rd in enumerate(P.roads):
            if rd['kind'] not in ('rua', 'av') or rd.get('cul'): continue
            for (s0, s1) in G.free_spans(i, pad=0.5):
                for sg in (-1, 1): fronts.append(('rua', i, sg, s0, s1, s1 - s0))
        for k, (bx, bz, br) in enumerate(P.bulbs): fronts.append(('bulb', k, 1, 0, 0, 999))
        # casas do jogador: reservar frentes nos bairros
        want = {}
        for k, b in HOUSE_BAIRRO.items(): want.setdefault(b, []).append(k)
        reserve = {}
        for nm, ks in want.items():
            x0, x1, z0, z1 = BAIRRO_REG[nm]
            cands = []
            for fi, f in enumerate(fronts):
                if f[0] != 'rua' or P.roads[f[1]]['kind'] != 'rua' or f[5] < 110: continue
                mx, mz = P.roads[f[1]]['path'].pt((f[3] + f[4]) / 2)
                if x0 <= mx <= x1 and z0 <= mz <= z1: cands.append(fi)
            r.shuffle(cands)
            for j, k in enumerate(ks):
                if j < len(cands): reserve.setdefault(cands[j], []).append(k)
        order = sorted(range(len(fronts)), key=lambda q: (q not in reserve, -fronts[q][5]))
        for fi in order:
            f = fronts[fi]
            if f[0] == 'bulb': self.bulb_lots(f[1])
            else: self.front_lots(f, reserve.get(fi, []))
        print(f'  casas do jogador reservadas: {len(self.player)}/17')

    def front_lots(self, f, res):
        P, r, B = self.P, self.rnd, self.B
        _, i, sg, s0, s1, L = f
        rd = P.roads[i]; pth = rd['path']; hr = half_row(rd['kind'])
        avenue = rd['kind'] == 'av'
        fam = FAMILIES[r.randrange(len(FAMILIES))]
        w0 = r.uniform(16.5, 19.5) if not avenue else 0
        sf = r.choice((6.0, 6.5, 7.0, 7.5)); picket = r.random() < 0.35; pal_base = r.random()
        res = list(res); res_at = [s0 + (s1 - s0) * (j + 1) / (len(res) + 1) for j in range(len(res))]
        pos = s0 + 0.5; q = 0
        while pos < s1 - 8:
            kres = None
            if res and pos >= res_at[0] - 10:
                kres = res.pop(0); res_at.pop(0)
                pl = self.plots[kres]; hw, hd = pl['x1'] - pl['x0'], pl['z1'] - pl['z0']
                w = max(hw + 9.0, 18.0)
            elif avenue: w = r.choice((42.0, 55.0, 70.0))
            else: w = w0 + r.uniform(-0.4, 0.4)
            if pos + w > s1 - 0.5:
                if kres is not None: res.insert(0, kres); res_at.insert(0, pos)
                break
            a = pth.pt(pos, sg * (hr + 0.15)); b = pth.pt(pos + w, sg * (hr + 0.15))
            ux, uz = b[0] - a[0], b[1] - a[1]; cl = math.hypot(ux, uz) or 1; ux, uz = ux / cl, uz / cl
            _, _, tx, tz = pth.at(pos + w / 2); inx, inz = -tz * sg, tx * sg
            flip = (-uz * inx + ux * inz) < 0
            F = Frame(a, (ux, uz), flip)
            mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            D, A = self._depth_to_middle(mx, mz, inx, inz, 60 if avenue else 44)
            placed = False
            for Dq in (D, D * 0.85, D * 0.7):
                if Dq < (24 if avenue else 15): break
                if kres is not None and Dq < FRONT_SB + hd + 3: break
                poly = Polygon(F.rect(0, cl, 0, Dq))
                if not self._free(poly): continue
                self._take(poly)
                if kres is not None: self.player_lot(F, cl, Dq, (kres, cl, hw, hd), None, None)
                elif avenue: self.commercial_lot(F, cl, Dq)
                else:
                    style = fam[0] if r.random() < 0.68 else fam[1]
                    info = B.house(F, cl, Dq, style, self.palette(style, pal_base), sf, 1 if q % 2 == 0 else -1, picket, True, True, False)
                    self.yard_plants(F, cl, Dq, info)
                placed = True; q += 1; break
            if not placed and kres is not None: res.insert(0, kres); res_at.insert(0, pos + 6)
            pos += (cl + 0.3) if placed else 3.0

    def bulb_lots(self, k):
        """lotes em leque em volta do retorno do cul-de-sac"""
        P, r, B = self.P, self.rnd, self.B
        bx, bz, br = P.bulbs[k]; Rf = br + PROFILE['rua']['verge'] + PROFILE['rua']['walk'] + 0.2
        fam = FAMILIES[r.randrange(len(FAMILIES))]; pal_base = r.random(); sf = 6.5
        n = 7; ang0 = r.uniform(0, 6.28)
        for q in range(n):
            a0 = ang0 + 2 * math.pi * q / n; a1 = ang0 + 2 * math.pi * (q + 1) / n
            pa = (bx + math.cos(a0) * Rf, bz + math.sin(a0) * Rf); pb = (bx + math.cos(a1) * Rf, bz + math.sin(a1) * Rf)
            ux, uz = pb[0] - pa[0], pb[1] - pa[1]; cl = math.hypot(ux, uz); ux, uz = ux / cl, uz / cl
            am = (a0 + a1) / 2; inx, inz = math.cos(am), math.sin(am)
            flip = (-uz * inx + ux * inz) < 0
            F = Frame(pa, (ux, uz), flip)
            D, A = self._depth_to_middle((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, inx, inz, 34)
            for Dq in (D, D * 0.8):
                if Dq < 18: break
                # lote em leque: frente estreita no retorno, abre para o fundo (usa o retangulo da frente para a casa)
                poly = Polygon([pa, pb, (pb[0] + math.cos(a1) * Dq, pb[1] + math.sin(a1) * Dq), (pa[0] + math.cos(a0) * Dq, pa[1] + math.sin(a0) * Dq)])
                if not self._free(poly): continue
                self._take(poly)
                style = fam[0] if r.random() < 0.6 else fam[1]
                info = B.house(F, cl, Dq, style, self.palette(style, pal_base), sf, 1, False, False, False, False)
                self.yard_plants(F, cl, Dq, info)
                break

    def yard_plants(self, F, w, d, info):
        r = self.rnd
        for (tu, tv) in info['trees_front']: self.trees.append((*F.xz(tu, tv), r.choice(('folhosa', 'oval', 'folhosa')), r.uniform(0.8, 1.1)))
        if r.random() < 0.75: self.trees.append((*F.xz(r.uniform(2, w - 2), r.uniform(info['back'][0] + 3, d - 2.5)), r.choice(('folhosa', 'folhosa', 'conifera', 'colunar')), r.uniform(0.9, 1.3)))
        # arbustos junto a frente da casa e no jardim
        v0 = info['back'][0] - 11.0
        for k in range(r.choice((2, 3, 4))):
            self.trees.append((*F.xz(r.uniform(1.5, w - 1.5), max(1.2, info.get('v0', 6.5) - 1.0) if k < 2 else r.uniform(1.0, 3.0)), 'arbusto', r.uniform(0.7, 1.1)))

    def commercial_lot(self, F, w, d):
        r = self.rnd; B = self.B
        signs = [rgb(c) for c in ('#C8102E', '#0057B8', '#FFB81C', '#00843D', '#E35205', '#6D2077', '#2D2926', '#00A3AD')]
        walls = [rgb(c) for c in ('#F2EDE4', '#E9DFD0', '#DDE3E6', '#EFE3D3', '#D8D2C6')]
        if w < 50 and r.random() < 0.45: B.gas_station(F, w, d - 1, r.choice(signs)); return
        pk = 15.0 if d > 30 else 8.0
        B.parking(F, 1, w - 1, 0.5, pk, self.park_car)
        bd = min(d - pk - 2, 22)
        Fs = Frame(F.xz(1, pk + 0.5), (F.ux, F.uz)); Fs.vx, Fs.vz = F.vx, F.vz
        n = max(1, int((w - 2) / 13)); uw = (w - 2) / n
        for k in range(n):
            Fk = Frame(Fs.xz(k * uw, 0), (F.ux, F.uz)); Fk.vx, Fk.vz = F.vx, F.vz
            B.shop_row(Fk, uw - 0.05, bd, r.choice(signs), r.choice(walls), r.choice((5.0, 5.5, 6.2, 7.5)))

    # ------------------------------------------------------------ geral
    def build(self):
        self.parked = []
        self.find_specials()
        for bi, blk in enumerate(self.P.blocks):
            z = blk['zone']
            if bi in self.special: self.special_block(bi, blk, *self.special[bi])
            elif z == 'suburbio': pass
            elif z == 'centro': self.centro(bi, blk)
            elif z == 'orla': self.orla(bi, blk)
            elif z in ('parque', 'ribeirinho'): self.lawn(blk['poly'])
            elif z == 'praia': self.lawn(blk['poly'], 'paver', Y_WALK, (240, 236, 228))
        self.suburbs()
        return self
