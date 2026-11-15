"""Cidade 6 - quadras -> lotes -> construcoes. Reserva os lotes das 17 casas do jogador (Cidade 5, city2.glb)."""
import math, random, json, os
import numpy as np
from shapely.geometry import Polygon, box as sbox, Point
from mesh import rgb, shade, mix, WHITE, Frame
from plan6 import *
from roads6 import Y_LAWN, Y_WALK
import buildings6 as B6
import houses6 as H6

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
FAMILIES = (('ranch', 'craftsman'), ('colonial', 'cape'), ('craftsman', 'farmhouse'), ('cape', 'colonial'), ('ranch', 'moderna'), ('colonial', 'farmhouse'),
            ('craftsman', 'colonial'), ('farmhouse', 'ranch'), ('mediterranea', 'ranch'), ('moderna', 'mediterranea'), ('cape', 'craftsman'))


class Lots:
    def __init__(self, P, G, M, seed=66):
        self.P, self.G, self.M = P, G, M
        self.rnd = random.Random(seed)
        self.B = B6.Builder(M, self.rnd)
        self.player = []              # manifesto das casas do jogador
        self.trees = []               # (x, z, tipo, escala) -> props
        self.lots = []
        self.plots = json.load(open(CITY2))['plots']
        self.ext = json.load(open(os.path.join(HERE, '..', 'gen-cidade5', 'house_extents.json')))

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
    SPECIAL = {'prefeitura': (1140, 940, 'W'), 'igreja': (770, 1060, 'E'), 'hospital': (1375, 695, 'N'),
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

    def park_car(self, x, z, dx, dz, y=None):
        self.parked.append((x, z, dx, dz, y if y is not None else Y_LAWN + 0.04))

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

    def yard(self, k):
        """tamanho efetivo do quintal real da casa k (malha do city2.glb, cerca incluida), no formato usado pelo loteamento:
        largura do lote = hw + 9, profundidade minima = hd + 7"""
        x0, x1, z0, z1 = self.ext[str(k)]
        return (x1 - x0) - 7.0, (z1 - z0) - 4.5

    def player_lot(self, F, w, d, val, side, blk):
        """lote de uma casa do jogador: fica vazio (a casa e o quintal vem do city2.glb no jogo); so caminho e caixa de correio.
        Mesma convencao da Cidade 5: x,z = centro da caixa da casa; yaw gira a frente (0, face) para a rua."""
        k = val[0]
        r = self.rnd; B = self.B; M = self.M
        pl = self.plots[k]; pcx, pcz = (pl['x0'] + pl['x1']) / 2, (pl['z0'] + pl['z1']) / 2
        face = 1.0 if (pl['z'] - pcz) > 0 else -1.0
        x0, x1, z0, z1 = self.ext[str(k)]
        flip = abs(F.vx - F.uz) < 1e-6 and abs(F.vz + F.ux) < 1e-6          # v = (uz, -ux)
        su = face if flip else -face                                       # x local -> u
        umin, umax = (x0, x1) if su > 0 else (-x1, -x0)
        zfront = z1 if face > 0 else -z0
        cu = (w - (umax - umin)) / 2 - umin; cv = 1.5 + zfront
        cx, cz = F.xz(cu, cv)
        yaw = math.atan2(F.vx * face, -F.vz * face)
        du = cu + su * (pl['x'] - pcx)                                     # porta/portao: caminho ate a calcada
        hh = H6.House.__new__(H6.House); hh.F = F; hh.M = M; hh.B = B; hh.r = r
        M.at(*F.xz(w / 2, 2), 'lotes'); hh.walkway(du, 0.0, 1.6, 1.4); hh.mailbox(max(0.8, du - 2.0)); M.free('lotes')
        B.drives.append((*F.xz(du, -2.6), 1.5))
        self.player.append({'k': k, 'casa': f'Casa {k + 1}', 'modelo': pl['name'], 'bairro': HOUSE_BAIRRO[k],
                            'centro': [round(cx, 3), round(Y_LAWN, 2), round(cz, 3)], 'yaw': round(yaw, 5), 'yaw_graus': round(math.degrees(yaw), 2),
                            'frente': [round(-F.vx, 4), round(-F.vz, 4)], 'face_modelo': 'sul(+z)' if face > 0 else 'norte(-z)',
                            'lote': [[round(p[0], 2), round(p[1], 2)] for p in F.rect(0, w, 0, d)], 'lote_m': [round(w, 1), round(d, 1)],
                            'quintal_m': [round(x1 - x0, 1), round(z1 - z0, 1)]})
        if d < (z1 - z0) + 2.0: print(f'  aviso: lote da casa {k + 1} raso ({d:.1f} m para quintal de {z1 - z0:.1f} m)')

    # ------------------------------------------------------------ centro
    def fountain(self, x, z, R=4.5, y=Y_WALK):
        M = self.M; M.at(x, z, 'lotes')
        M.m('pedra'); M.cyl(x, z, R, y, y + 0.55, WHITE, 16, True)
        M.m('agua'); M.cyl(x, z, R - 0.45, y + 0.55, y + 0.57, (200, 232, 240), 16, True)
        M.m('pedra'); M.cyl(x, z, 0.5, y + 0.5, y + 1.8, WHITE, 8, True); M.cyl(x, z, 1.5, y + 1.8, y + 2.0, WHITE, 10, True)
        M.m('agua'); M.cyl(x, z, 1.25, y + 2.0, y + 2.03, (200, 232, 240), 10, True)
        M.m('liso'); M.cyl(x, z, 0.12, y + 2.0, y + 3.4, (225, 240, 248), 5, False, 0.02)
        M.free('lotes')

    def planter(self, x0, z0, x1, z1, y=Y_WALK, trees=True, flowers=True):
        """canteiro elevado com borda de pedra, grama, flores e arvores"""
        r = self.rnd; M = self.M; M.at((x0 + x1) / 2, (z0 + z1) / 2, 'lotes')
        M.m('pedra'); M.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y, y + 0.42, WHITE, False)
        M.m('grama'); M.poly([(x0 + 0.25, y + 0.4, z0 + 0.25), (x1 - 0.25, y + 0.4, z0 + 0.25), (x1 - 0.25, y + 0.4, z1 - 0.25), (x0 + 0.25, y + 0.4, z1 - 0.25)], WHITE, (0, 1, 0))
        M.free('lotes')
        if trees:
            n = max(1, int((x1 - x0) * (z1 - z0) / 60))
            for _ in range(n): self.trees.append((r.uniform(x0 + 1.5, x1 - 1.5), r.uniform(z0 + 1.5, z1 - 1.5), r.choice(('folhosa', 'oval', 'florida', 'ornamental')), r.uniform(0.8, 1.05), y + 0.4))
        if flowers:
            for _ in range(int((x1 - x0 + z1 - z0) / 3)):
                self.trees.append((r.uniform(x0 + 0.7, x1 - 0.7), r.choice((z0 + 0.7, z1 - 0.7)), 'flores', 0.7, y + 0.4))

    def plaza(self, x0, z0, x1, z1, fountain=True):
        """praca: fonte no centro, quatro canteiros, bancos virados para a fonte, postes baixos"""
        r = self.rnd; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        w, d = x1 - x0, z1 - z0
        if w < 16 or d < 16:
            self.planter(x0 + 2, z0 + 2, x1 - 2, z1 - 2); return
        g = 5.0 if fountain else 2.0
        for (a, b, c, e) in ((x0 + 3, z0 + 3, cx - g, cz - g), (cx + g, z0 + 3, x1 - 3, cz - g), (x0 + 3, cz + g, cx - g, z1 - 3), (cx + g, cz + g, x1 - 3, z1 - 3)):
            if c - a > 4 and e - b > 4: self.planter(a, b, c, e)
        if fountain and min(w, d) > 26: self.fountain(cx, cz, min(4.5, min(w, d) / 8))
        else: self.trees.append((cx, cz, 'folhosa', 1.2, Y_WALK))
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            self.benches.append((cx + dx * 7.5, cz + dz * 7.5, -dx, -dz, Y_WALK))
            if min(w, d) > 40: self.benches.append((cx + dx * 7.5 + dz * 3, cz + dz * 7.5 + dx * 3, -dx, -dz, Y_WALK))

    def centro(self, bi, blk, resid=False):
        import centro6 as C6
        poly = blk['poly']; r = self.rnd; B = self.B
        minx, minz, maxx, maxz = poly.bounds
        self.lawn(poly, 'paver', Y_WALK, (236, 232, 224))
        cx, cz = (minx + maxx) / 2, (minz + maxz) / 2
        dc = math.hypot(cx - 1140, cz - 1000)
        hmax = int(max(5, 30 - dc / 22))
        w, d = maxx - minx, maxz - minz
        kind = r.random()
        self.M.free('lotes')
        # ---- quadra-praca
        if kind < 0.07 and dc > 150:
            self.plaza(minx + 2, minz + 2, maxx - 2, maxz - 2)
            # quiosques / bancas nos cantos
            for (kx, kz) in ((minx + 7, minz + 7), (maxx - 7, maxz - 7)):
                Fk = Frame((kx - 2.5, kz - 2), (1, 0))
                B.box(Fk, 0, 5, 0, 4, Y_WALK, Y_WALK + 2.7, r.choice(C6.SIGNS), 'liso', top=False)
                B.panel(Fk, 0.4, 4.6, 0, Y_WALK + 1.0, Y_WALK + 2.2, (60, 64, 70), 'liso', -1, 0.04)
                B.box(Fk, -0.5, 5.5, -1.2, 4.3, Y_WALK + 2.7, Y_WALK + 2.9, (240, 238, 232), 'concreto'); B.solid(Fk, 0, 5, 0, 4)
            return
        # ---- quadra de torres sobre praca
        if dc < 380 and kind < 0.55 and min(w, d) > 80:
            n = r.choice((1, 2, 2, 3, 3, 4)); sides = ['N', 'S', 'E', 'W']; r.shuffle(sides); used = []
            for side in sides[:n]:
                tw = r.uniform(30, 42); td = r.uniform(28, 38)
                if n == 1: tw, td = r.uniform(44, 56), r.uniform(40, 50)
                Ls = w if side in ('N', 'S') else d
                s0 = 2.0 if n > 1 else (Ls - tw) / 2
                F = self.frame(side, minx, maxx, minz, maxz, s0)
                fp = Polygon(F.rect(0, tw, 0, td))
                if any(fp.buffer(4).intersects(u) for u in used): continue
                fl = r.randint(max(12, hmax - 10), hmax + 12)
                self.M.at(*F.xz(tw / 2, td / 2), 'lotes'); C6.tower(B, F, tw, td, fl); self.M.free('lotes')
                used.append(fp)
            from shapely.ops import unary_union
            free = sbox(minx + 2, minz + 2, maxx - 2, maxz - 2).difference(unary_union(used).buffer(3))
            for g in getattr(free, 'geoms', [free]):
                if g.area < 150: continue
                # maior retangulo simples dentro da sobra: tenta os 4 quadrantes
                bx0, bz0, bx1, bz1 = g.bounds
                for (a, b_, c, e) in ((bx0, bz0, cx - 2, cz - 2), (cx + 2, bz0, bx1, cz - 2), (bx0, cz + 2, cx - 2, bz1), (cx + 2, cz + 2, bx1, bz1)):
                    q = sbox(a + 1, b_ + 1, c - 1, e - 1)
                    if c - a > 12 and e - b_ > 12 and q.within(g): self.plaza(a + 1, b_ + 1, c - 1, e - 1, r.random() < 0.4)
            return
        # ---- edificio-garagem em meia quadra
        garage = kind > 0.94 and w > 70
        # ---- perimetro de predios colados (frente para as 4 ruas)
        depths = {sd: r.uniform(16, 23) for sd in 'NESW'}
        for side in ('N', 'E', 'S', 'W'):
            Lside = w if side in ('N', 'S') else d
            nxt = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}[side]
            s = 0.0; end = Lside - depths[nxt]
            if garage and side == 'S':
                F = self.frame(side, minx, maxx, minz, maxz, 0.5)
                self.M.at(*F.xz(20, 15), 'lotes')
                for ((px, pz), py) in C6.parking_garage(B, F, min(end - 1, 46), 30, r.choice((4, 5, 6))): self.parked.append((px, pz, F.vx, F.vz, py))
                self.M.free('lotes'); s = min(end - 1, 46) + 1.5
            while s < end - 6:
                pw = min(r.uniform(13, 30), end - s)
                if end - s - pw < 9: pw = end - s
                F = self.frame(side, minx, maxx, minz, maxz, s)
                fl = max(3, min(hmax + 3, int(r.uniform(0.35, 1.1) * hmax)))
                if resid: fl = max(4, int(fl * 0.9))
                self.M.at(*F.xz(pw / 2, depths[side] / 2), 'lotes')
                C6.midrise(B, F, pw - 0.15, depths[side] - r.choice((0, 0, 1.5, 3.0)), fl, None, None, True, None, True, r.choice(('moderna', 'janelas', 'moderna', 'classica')) if resid else None)
                self.M.free('lotes')
                s += pw
        # ---- miolo: jardim, estacionamento ou parquinho
        ix0, iz0, ix1, iz1 = minx + depths['W'] + 1.5, minz + depths['N'] + 1.5, maxx - depths['E'] - 1.5, maxz - depths['S'] - 1.5
        if garage: iz1 -= 12
        if ix1 - ix0 > 10 and iz1 - iz0 > 10:
            opt = r.random()
            if opt < 0.4:
                Fp = Frame((ix0, iz0), (1, 0)); self.M.at((ix0 + ix1) / 2, (iz0 + iz1) / 2, 'lotes')
                B.parking(Fp, 0.5, ix1 - ix0 - 0.5, 0.5, iz1 - iz0 - 0.5, self.park_car, Y_WALK + 0.01); self.M.free('lotes')
            elif opt < 0.85: self.plaza(ix0, iz0, ix1, iz1, False)
            else:
                self.M.free('lotes'); self.M.m('grama'); self.M.shp(sbox(ix0, iz0, ix1, iz1), Y_WALK + 0.03, WHITE)
                for _ in range(int((ix1 - ix0) * (iz1 - iz0) / 110)): self.trees.append((r.uniform(ix0 + 2, ix1 - 2), r.uniform(iz0 + 2, iz1 - 2), r.choice(('folhosa', 'oval', 'florida')), r.uniform(0.8, 1.1), Y_WALK))

    def orla(self, bi, blk):
        import centro6 as C6
        poly = blk['poly']; r = self.rnd; B = self.B
        minx, minz, maxx, maxz = poly.bounds
        w, d = maxx - minx, maxz - minz
        if maxz < 1650: self.centro(bi, blk, True); return
        self.lawn(poly, 'paver', Y_WALK, (236, 232, 224))
        # frente para o mar (lado sul): 1 ou 2 hoteis/residenciais; fundos (lado norte): predios; miolo: jardim com palmeiras e estacionamento
        n = 2 if w > 84 else 1; gap = 8.0; hw = (w - 4 - gap * (n - 1)) / n
        hd = min(30.0, d * 0.45)
        for k in range(n):
            F = self.frame('S', minx, maxx, minz, maxz, 2 + k * (hw + gap))
            self.M.at(*F.xz(hw / 2, hd / 2), 'lotes')
            C6.beach_hotel(B, F, hw, hd, r.randint(10, 22)); self.M.free('lotes')
            if k: 
                gx = maxx - (2 + k * (hw + gap)) + gap / 2
                for zz in (maxz - 4, maxz - 12, maxz - 20): self.trees.append((gx, zz, 'palmeira', r.uniform(0.9, 1.15), Y_WALK))
        Dn = r.uniform(16, 20); s = 0.0
        while s < w - 6:
            pw = min(r.uniform(16, 30), w - s)
            if w - s - pw < 10: pw = w - s
            F = self.frame('N', minx, maxx, minz, maxz, s)
            self.M.at(*F.xz(pw / 2, Dn / 2), 'lotes')
            C6.midrise(B, F, pw - 0.15, Dn, r.randint(4, 9), None, None, True, None, True, r.choice(('moderna', 'janelas', 'moderna'))); self.M.free('lotes')
            s += pw
        iz0, iz1 = minz + Dn + 2, maxz - hd - 2
        if iz1 - iz0 > 12:
            half = (minx + maxx) / 2
            Fp = Frame((minx + 3, iz0), (1, 0)); self.M.at(minx + w / 4, (iz0 + iz1) / 2, 'lotes')
            B.parking(Fp, 0, half - minx - 5, 0.5, iz1 - iz0 - 0.5, self.park_car, Y_WALK + 0.01); self.M.free('lotes')
            self.plaza(half + 1, iz0, maxx - 3, iz1, False)
            for xx in (half + 2, maxx - 4): self.trees.append((xx, (iz0 + iz1) / 2, 'palmeira', 1.0, Y_WALK))

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
            if len(cands) < len(ks):                      # bairro com poucas ruas longas: usa as mais proximas do bairro
                cx_, cz_ = (x0 + x1) / 2, (z0 + z1) / 2
                extra = []
                for fi, f in enumerate(fronts):
                    if f[0] != 'rua' or P.roads[f[1]]['kind'] != 'rua' or f[5] < 90 or fi in cands or fi in reserve: continue
                    mx, mz = P.roads[f[1]]['path'].pt((f[3] + f[4]) / 2)
                    extra.append((math.hypot(mx - cx_, mz - cz_), fi))
                cands += [fi for _, fi in sorted(extra)[:len(ks) - len(cands)]]
            for j, k in enumerate(ks):
                if j < len(cands): reserve.setdefault(cands[j], []).append(k)
        order = sorted(range(len(fronts)), key=lambda q: (q not in reserve, -fronts[q][5]))
        for fi in order:
            f = fronts[fi]
            if f[0] == 'bulb': self.bulb_lots(f[1])
            else: self.front_lots(f, reserve.get(fi, []))
        placed = {h['k'] for h in self.player}
        for k in [k for k in HOUSE_BAIRRO if k not in placed]:
            for fi in sorted(range(len(fronts)), key=lambda q: -fronts[q][5]):
                f = fronts[fi]
                if f[0] != 'rua': continue
                n0 = len(self.player); self.front_lots_player_only(f, k)
                if len(self.player) > n0: break
        self.pocket_parks()
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
                hw, hd = self.yard(kres)
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
            D, A = self._depth_to_middle(mx, mz, inx, inz, 60 if (avenue or kres is not None) else 44)
            if kres is not None and D < hd + 9: D = min(A * 0.7, hd + 12)
            placed = False
            for Dq in (D, D * 0.93, D * 0.86, D * 0.78, D * 0.7):
                if Dq < (24 if avenue else 15): break
                if kres is not None and Dq < hd + 7: break
                poly = Polygon(F.rect(0, cl, 0, Dq))
                if not self._free(poly): continue
                self._take(poly)
                if kres is not None: self.player_lot(F, cl, Dq, (kres, cl, hw, hd), None, None)
                elif avenue: self.commercial_lot(F, cl, Dq)
                else:
                    style = fam[0] if r.random() < 0.68 else fam[1]
                    r3 = r.random(); style = fam[0] if r3 < 0.55 else (fam[1] if r3 < 0.9 else r.choice(H6.STYLES))
                    self.put_house(F, cl, Dq, style, pal_base, sf, 1 if q % 2 == 0 else -1, picket, True, q == 0)
                placed = True; q += 1; break
            if not placed and kres is not None: res.insert(0, kres); res_at.insert(0, pos + 3); self.retry = getattr(self, 'retry', {}); self.retry[kres] = self.retry.get(kres, 0) + 1
            pos += (cl + 0.3) if placed else 3.0

    def front_lots_player_only(self, f, k):
        """segunda chance para uma casa do jogador: procura qualquer trecho livre na frente"""
        P = self.P; _, i, sg, s0, s1, L = f
        rd = P.roads[i]; pth = rd['path']; hr = half_row(rd['kind'])
        hw, hd = self.yard(k); w = max(hw + 9.0, 18.0)
        pos = s0 + 1.0
        while pos + w < s1 - 1:
            a = pth.pt(pos, sg * (hr + 0.15)); b = pth.pt(pos + w, sg * (hr + 0.15))
            ux, uz = b[0] - a[0], b[1] - a[1]; cl = math.hypot(ux, uz) or 1; ux, uz = ux / cl, uz / cl
            _, _, tx, tz = pth.at(pos + w / 2); inx, inz = -tz * sg, tx * sg
            F = Frame(a, (ux, uz), (-uz * inx + ux * inz) < 0)
            D, A = self._depth_to_middle((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, inx, inz, 60)
            for Dq in (D, A * 0.7, hd + 9):
                if Dq < hd + 7: continue
                poly = Polygon(F.rect(0, cl, 0, Dq))
                if self._free(poly):
                    self._take(poly); self.player_lot(F, cl, Dq, (k, cl, hw, hd), None, None); return
            pos += 2.0

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
                self.put_house(F, cl, min(Dq, 30.0), style, pal_base, sf, 1 if q % 2 == 0 else -1, False, False, False)
                break

    def pocket_parks(self):
        """sobras no miolo das quadras: pracinhas de bairro (caminho, bancos, playground ou quadra, arvores)"""
        from shapely.ops import unary_union
        taken = unary_union([q for lst in self.occ.values() for q in lst]).buffer(0.5)
        left = self.sub_free.difference(taken).buffer(-2.0)
        r = self.rnd; n = 0
        for g in getattr(left, 'geoms', [left]):
            if g.geom_type != 'Polygon' or g.area < 500: continue
            g = g.buffer(1.0)
            n += 1
            self.M.free('parques'); self.M.m('grama'); self.M.shp(g, Y_LAWN + 0.05, (225, 245, 215))
            c = g.representative_point()
            # caminho em cruz e mobiliario
            mnx, mnz, mxx, mxz = g.bounds
            from shapely.geometry import LineString as _L
            pth = unary_union([_L([(mnx, c.y), (mxx, c.y)]).buffer(1.2), _L([(c.x, mnz), (c.x, mxz)]).buffer(1.2)]).intersection(g.buffer(-1))
            self.M.m('paver'); self.M.shp(pth, Y_LAWN + 0.09, WHITE)
            if g.area > 1200:
                px, pz = c.x + 8, c.y + 8
                if g.contains(Point(px, pz).buffer(6)):
                    self.M.at(px, pz); self.M.m('areia'); self.M.prism([(px - 5, pz - 4), (px + 5, pz - 4), (px + 5, pz + 4), (px - 5, pz + 4)], Y_LAWN, Y_LAWN + 0.12, WHITE)
                    self.M.m('liso'); col = r.choice(((220, 60, 50), (40, 120, 200), (240, 190, 40)))
                    self.M.box(px - 1.4, px + 1.4, Y_LAWN, Y_LAWN + 2.2, pz - 1.4, pz + 1.4, col); self.M.box(px - 1.6, px + 1.6, Y_LAWN + 2.2, Y_LAWN + 2.5, pz - 1.6, pz + 1.6, shade(col, -40))
                    self.M.quad((px + 1.4, Y_LAWN + 2.0, pz - 0.7), (px + 4.4, Y_LAWN + 0.2, pz - 0.7), (px + 4.4, Y_LAWN + 0.2, pz + 0.7), (px + 1.4, Y_LAWN + 2.0, pz + 0.7), (240, 200, 40), (0.5, 1, 0))
                    self.M.free()
            for _ in range(int(g.area / 110)):
                x, z = r.uniform(mnx, mxx), r.uniform(mnz, mxz)
                if g.buffer(-2).contains(Point(x, z)) and not pth.buffer(2).contains(Point(x, z)):
                    self.trees.append((x, z, r.choice(('folhosa', 'folhosa', 'oval', 'conifera', 'arbusto')), r.uniform(0.9, 1.3)))
            self.benches.append((c.x + 3, c.y + 2.2, 0, -1)); self.benches.append((c.x - 3, c.y - 2.2, 0, 1))
        print(f'  pracinhas no miolo das quadras: {n}')

    def put_house(self, F, w, d, style, pal_base, sf, gside, picket, fence, first):
        r = self.rnd
        cx, cz = F.xz(w / 2, min(d, 30) / 2)
        self.M.at(cx, cz, 'lotes')
        self.B.M.ao = True
        h = H6.House(self.B, F, w, d, style, H6.palette(style, r, pal_base), sf, gside, r, fence, first, picket)
        info = h.build()
        self.M.free('lotes')
        for (pu, pv, kind, sc) in info['plants']: self.trees.append((*F.xz(pu, pv), kind, sc))

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
        self.parked = []; self.benches = []
        self.find_specials()
        for bi, blk in enumerate(self.P.blocks):
            z = blk['zone']
            if bi in self.special: self.special_block(bi, blk, *self.special[bi])
            elif z == 'suburbio': pass
            elif z == 'centro': self.centro(bi, blk)
            elif z == 'orla': self.orla(bi, blk)
            elif z in ('parque', 'ribeirinho'): self.lawn(blk['poly'])
            elif z == 'praia': pass                     # calcadao, mureta e areia: orla6.py
        self.suburbs()
        return self
