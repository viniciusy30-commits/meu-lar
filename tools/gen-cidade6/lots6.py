"""Cidade 6 - quadras -> lotes -> construcoes. Reserva os lotes das 17 casas do jogador (Cidade 5, city2.glb)."""
import math, random, json, os
GLOW6 = (255, 238, 196)
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


class _Sink:
    """adaptador para park6: bancos e plantas pedidos entram nas listas do Lots"""
    def __init__(self, L): self.L = L; self.M = L.M
    def bench(self, x, z, fx, fz, y=Y_WALK): self.L.benches.append((x, z, fx, fz, y))
    def tree(self, x, z, kind='folhosa', sc=1.0, y=Y_LAWN): self.L.trees.append((x, z, kind, sc, y))




class Lots:
    def __init__(self, P, G, M, seed=66):
        self.P, self.G, self.M = P, G, M
        self.rnd = random.Random(seed)
        self.B = B6.Builder(M, self.rnd)
        self.player = []              # manifesto das casas do jogador
        self.trees = []               # (x, z, tipo, escala) -> props
        self.jobs = []                # predios das profissoes e prefeitura (porta) -> c6.json 'jobs'
        self.props_lights = []        # luminarias internas e das pracas dos predios -> pocas de luz
        self.lots = []
        self.plots = json.load(open(CITY2))['plots']
        self.ext = json.load(open(os.path.join(HERE, '..', 'gen-cidade5', 'house_extents.json')))
        H6.ROW = P.row.difference(P.asphalt).buffer(0)                         # rampas de garagem medidas na calcada real
        self.gates = json.load(open(os.path.join(HERE, 'player_gates.json')))      # centro x do portao da cerca de cada casa (city2.glb)

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
        # predios das profissoes: um por quadra do centro, espalhados (cada um num canto diferente do centro),
        # na fileira de predios do lado que da para a via mais importante (avenida > rua do centro)
        import jobs2_6
        from shapely.geometry import LineString as _LS
        avs = [_LS(r_['pts']) for r_ in self.P.roads if r_['kind'] == 'av']
        cand = []
        for bi, blk in enumerate(self.P.blocks):
            if blk['zone'] != 'centro' or bi in self.special: continue
            x0, z0, x1, z1 = blk['poly'].bounds
            if z1 > 1640 or x1 - x0 < 60 or z1 - z0 < 60: continue
            if blk['poly'].area < 0.95 * (x1 - x0) * (z1 - z0): continue      # so quadras retangulares (o campus ocupa a quadra toda)
            cand.append((bi, (x0 + x1) / 2, (z0 + z1) / 2, (x0, z0, x1, z1)))
        self.jobblk = {}
        chosen = []
        px_, pz_ = self.SPECIAL['prefeitura'][:2]
        ids = list(jobs2_6.ORDER)
        while ids and cand:
            # o mais longe dos ja escolhidos (e da prefeitura), mas sem fugir do centro
            def score(c):
                dmin = min([math.hypot(c[1] - a, c[2] - b) for (a, b) in chosen + [(px_, pz_)]])
                return dmin - 0.15 * math.hypot(c[1] - px_, c[2] - pz_)
            c = max(cand, key=score); cand.remove(c)
            bi, cx, cz, (x0, z0, x1, z1) = c
            jid = ids.pop(0)
            need = 50.0                                     # o campus usa a quadra inteira
            sides = []
            for sd, mid, Ls in (('N', ((x0 + x1) / 2, z0 - 6), x1 - x0), ('S', ((x0 + x1) / 2, z1 + 6), x1 - x0), ('W', (x0 - 6, (z0 + z1) / 2), z1 - z0), ('E', (x1 + 6, (z0 + z1) / 2), z1 - z0)):
                if Ls < need + 30: continue
                dav = min([a.distance(Point(*mid)) for a in avs] or [999])
                sides.append((dav, sd))
            if not sides: ids.insert(0, jid); continue
            sides.sort()
            self.jobblk[bi] = (jid, sides[0][1]); chosen.append((cx, cz))

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
            if kind == 'posto': B.gas_station(F, w, depth - 1, r.choice(signs)); self.access(F, 1.5, 7.5, 0.6); self.access(F, w - 7.5, w - 1.5, 0.6)   # entrada e saida rebaixadas na guia
            else:
                pk = 15.0 if depth > 30 else 8.0
                B.parking(F, 1, w - 1, 0.5, pk, self.park_car)
                self.access(F, 2.0, 8.0, 0.6); self.access(F, w - 8.0, w - 2.0, 0.6)
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
        if nm.startswith('jobs:'):
            import jobs6
            self.lawn(poly, 'paver', Y_WALK, (236, 232, 224))
            ids = nm[5:].split(',')
            for k, jid in enumerate(ids):
                sd = 'N' if k == 0 else 'S'
                Fk = self.frame(sd, minx, maxx, minz, maxz, 0.0)
                jobs6.place_job(self, Fk, L, jid)
                nm_, br, fl, w, d, _ = jobs6.JOBS[jid]
                ww = min(w, L - 4); off = (L - ww) / 2
                self.pocc.append(Polygon(Fk.rect(off - 4, off + ww + 4, 0, 6.0 + d + 2)))
            return
        if nm == 'prefeitura':
            import jobs6
            self.lawn(poly, 'paver', Y_WALK, (236, 232, 224))
            jobs6.prefeitura(self, F, L, D)
            self.pocc.append(Polygon(F.rect(0, L, 0, D)))
            return
        if nm == 'hospital':
            self.campus(bi, blk, 'medico', side); return
        if nm.startswith('escola'):
            self.lawn(poly); import grand6; grand6.school(B, F, L, D, self.park_car)
            self.access(F, 0.6, 5.6, min(D - 6, 52.0), Y_LAWN + 0.07)          # acesso ao estacionamento dos fundos, pela lateral
            bw = min(L * 0.45, 80)
            ex = [Polygon(F.rect(0, 10 + bw, 0, min(D - 6, 54) + 2))]
            if L - 8 - (10 + bw) > 50: ex.append(Polygon(F.rect(10 + bw, L - 8, 8, D - 8)))
            self.fill_free(poly, len(B.colliders), ex, False, 4, ('basquete', 'futsal', 'tenis', 'playground', 'piquenique', 'academia'))
            return
        self.lawn(poly, 'paver', Y_WALK, (236, 232, 224))
        if nm == 'prefeitura': B.city_hall(F, L, D)
        elif nm == 'igreja':
            import grand6; grand6.church(B, F, L * 0.6, D)
            # praca da matriz: jardim e arvores na outra metade
            Fp = Frame(F.xz(L * 0.62, 6), (F.ux, F.uz))
            self.M.free('lotes'); self.M.m('grama')
            self.M.poly([Fp.p(0, 0, Y_WALK + 0.06), Fp.p(L * 0.36, 0, Y_WALK + 0.06), Fp.p(L * 0.36, D - 12, Y_WALK + 0.06), Fp.p(0, D - 12, Y_WALK + 0.06)], WHITE, (0, 1, 0))
            for k in range(14): self.trees.append((*Fp.xz(r.uniform(3, L * 0.36 - 3), r.uniform(3, D - 15)), 'folhosa', r.uniform(0.9, 1.2), Y_WALK + 0.06))
            self.pocc.append(Polygon(Fp.rect(0, L * 0.36, 0, D - 12)))
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
        gx, gw, door_x, front_z = self.gates[str(k)][:4]
        du = cu + su * (gx - pcx)                                          # portao da cerca
        door_u = cu + su * (door_x - pcx)                                  # porta da casa
        v_of = lambda zm: cv - face * (zm - pcz)                           # z do modelo -> v do lote
        v_gate = v_of(pl['z']); v_front = v_of(front_z)
        hh = H6.House.__new__(H6.House); hh.F = F; hh.M = M; hh.B = B; hh.r = r
        from shapely.geometry import Polygon as _Pg
        M.at(*F.xz(w / 2, 2), 'lotes')
        # calcada da rua -> portao: so a largura do portao, recortada na borda real da calcada
        band = _Pg(F.rect(du - gw / 2 - 0.15, du + gw / 2 + 0.15, -3.0, v_gate + 0.1)).difference(self.G.walks)
        M.m('concreto')
        for g in getattr(band, 'geoms', [band]):
            if g.geom_type == 'Polygon' and g.intersects(_Pg(F.rect(du - 0.3, du + 0.3, 0.2, v_gate))): M.shp(g, Y_WALK, WHITE)
        # portao -> porta: reto; se a porta nao fica de frente para o portao, caminho em L no meio do jardim
        wk = 1.2
        if abs(door_u - du) < 0.7:
            hh.walkway(du, v_gate + 0.1, v_front, wk)
        else:
            vm = v_gate + max(1.2, (v_front - v_gate) * 0.5)
            hh.walkway(du, v_gate + 0.1, vm - wk / 2, wk)
            hh.walk_L(min(du, door_u) - wk / 2, max(du, door_u) + wk / 2, vm, wk)
            hh.walkway(door_u, vm + wk / 2, v_front, wk)
        hh.mailbox(du - (gw / 2 + 1.0)); M.free('lotes')
        # conferencia: portao do modelo (city2) levado ao mundo pelo mesmo giro do jogo, contra o fim do caminho
        c_, s_ = math.cos(yaw), math.sin(yaw); gzm = (pl['z'] - pcz)
        gwx = cx + c_ * (gx - pcx) - s_ * gzm; gwz = cz + s_ * (gx - pcx) + c_ * gzm
        ex_, ez_ = F.xz(du, cv - zfront)
        self.gate_err = max(getattr(self, 'gate_err', 0.0), math.hypot(gwx - ex_, gwz - ez_))
        if os.environ.get('DBG_GATE'): print('   portao', k, 'face', face, 'flip', flip, 'du_err', round((gwx - ex_) * F.ux + (gwz - ez_) * F.uz, 2), 'dv_err', round((gwx - ex_) * F.vx + (gwz - ez_) * F.vz, 2))
        B.drives.append((*F.xz(du, -2.6), 1.5))
        # vaga do carro do jogador: na rua, encostada no meio-fio, ao lado do portao (paralela a calcada)
        from shapely.geometry import Point as _Pt
        car = None
        for cu_ in (du + 6.5, du - 6.5, du + 11.0, du - 11.0):
            vc = None
            for i in range(1, 60):
                vv = -0.25 * i
                if not self.G.walks.buffer(0.05).contains(_Pt(*F.xz(cu_, vv))): vc = vv; break
            if vc is None: continue
            vcar = vc - 1.25
            ok = all(not self.G.walks.contains(_Pt(*F.xz(cu_ + a, vcar + b))) for a in (-2.6, 0, 2.6) for b in (-1.0, 1.0))
            if ok: car = [round(c, 3) for c in F.xz(cu_, vcar)] + [round(math.atan2(F.ux, -F.uz), 5)]; break
        self.player.append({'k': k, 'carro': car, 'casa': f'Casa {k + 1}', 'modelo': pl['name'], 'bairro': HOUSE_BAIRRO[k],
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
        self.pocc.append(sbox(x0, z0, x1, z1))
        M.m('pedra'); M.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y, y + 0.42, WHITE, False)
        M.m('grama'); M.poly([(x0 + 0.25, y + 0.4, z0 + 0.25), (x1 - 0.25, y + 0.4, z0 + 0.25), (x1 - 0.25, y + 0.4, z1 - 0.25), (x0 + 0.25, y + 0.4, z1 - 0.25)], WHITE, (0, 1, 0))
        M.free('lotes')
        if trees:
            n = max(1, int((x1 - x0) * (z1 - z0) / 60))
            for _ in range(n): self.trees.append((r.uniform(x0 + 1.5, x1 - 1.5), r.uniform(z0 + 1.5, z1 - 1.5), r.choice(('folhosa', 'oval', 'florida', 'ornamental')), r.uniform(0.8, 1.05), y + 0.4))
        if flowers:
            for _ in range(int((x1 - x0 + z1 - z0) / 3)):
                self.trees.append((r.uniform(x0 + 0.7, x1 - 0.7), r.choice((z0 + 0.7, z1 - 0.7)), 'flores', 0.7, y + 0.4))

    # ------------------------------------------------------------ preenchimento das sobras (nada de piso/gramado vazio)
    PAVER_ST = ('quiosque', 'coreto', 'jardim', 'playground', 'academia', 'anfiteatro', 'quiosque', 'jardim')
    LAWN_ST = ('basquete', 'futsal', 'tenis', 'playground', 'piquenique', 'academia', 'jardim', 'coreto', 'lago', 'skate', 'caes')

    def fill_free(self, poly, c0, extra=(), paver=True, max_st=3, names=None):
        """sobras de uma quadra (fora de predios, pracas, estacionamentos): equipamentos onde cabe e, no resto,
        arvores em golas com bancos e postes (piso) ou bosques (gramado)"""
        import park6, shapely
        from shapely.ops import unary_union
        r = self.rnd; M = self.M; y = Y_WALK if paver else Y_LAWN
        occ = [Polygon(Frame((c[0], c[1]), (c[2], c[3])).rect(-c[4], c[4], -c[5], c[5])) for c in self.B.colliders[c0:]] + list(self.pocc) + list(extra)
        occ = [o for o in occ if o.intersects(poly)]
        free = poly.buffer(-3.5)
        if occ: free = free.difference(unary_union(occ).buffer(2.5))
        names = list(names or (self.PAVER_ST if paver else self.LAWN_ST)); r.shuffle(names)
        sink = _Sink(self); nst = 0
        for _ in range(max_st * 3):
            if nst >= max_st: break
            gs = [g for g in getattr(free, 'geoms', [free]) if g.geom_type == 'Polygon' and g.area > 300]
            if not gs: break
            g = max(gs, key=lambda q: q.area)
            mic = shapely.maximum_inscribed_circle(g); c = mic.coords[0]; R = mic.length
            if R < 6.5: break
            bx0, bz0, bx1, bz1 = g.bounds; done = False
            for nm in names:
                fn, ha, hb = park6.STATIONS[nm]
                for (ux, uz) in (((1, 0), (0, 1)) if bx1 - bx0 >= bz1 - bz0 else ((0, 1), (1, 0))):
                    fp = Polygon(Frame(c, (ux, uz)).rect(-ha, ha, -hb, hb))
                    if fp.buffer(1.0).within(g):
                        park6.place(sink, nm, c[0], c[1], ux, uz, r, y); M.free('lotes')
                        free = free.difference(fp.buffer(3.0)); names.remove(nm); names.append(nm); nst += 1; done = True; break
                if done: break
            if not done: free = free.difference(Point(c).buffer(R * 0.7))
        if free.is_empty: return
        if paver:
            kinds = r.choice((('oval', 'oval', 'florida'), ('folhosa', 'folhosa', 'ornamental'), ('palmeira', 'palmeira', 'oval'), ('oval', 'folhosa', 'florida')))
            bx0, bz0, bx1, bz1 = free.bounds; st = 8.5; k = 0
            ox, oz = bx0 + ((bx1 - bx0) % st) / 2, bz0 + ((bz1 - bz0) % st) / 2
            for i, x in enumerate(np.arange(ox, bx1, st)):
                for j, z in enumerate(np.arange(oz, bz1, st)):
                    p = Point(x, z)
                    if not p.buffer(1.6).within(free): continue
                    if (i * 3 + j * 5) % 7 == 0:
                        self.plights.append((x, z, y)); self.benches.append((x + 1.4, z, -1, 0, y)); self.benches.append((x - 1.4, z, 1, 0, y)); continue
                    pass                                                  # sem arvores no meio dos patios (so peso; postes e bancos bastam)
        else:
            bx0, bz0, bx1, bz1 = free.bounds; pts = []
            for _ in range(int(free.area / 70)):
                x, z = r.uniform(bx0, bx1), r.uniform(bz0, bz1)
                if not free.contains(Point(x, z)) or any((x - a) ** 2 + (z - b) ** 2 < 36 for (a, b) in pts): continue
                pts.append((x, z)); self.trees.append((x, z, r.choice(('folhosa', 'folhosa', 'oval', 'conifera', 'florida', 'frutifera')), r.uniform(0.9, 1.3), y))

    def plaza(self, x0, z0, x1, z1, fountain=True, trees=True):
        """praca: fonte no centro, quatro canteiros, bancos virados para a fonte, postes baixos"""
        r = self.rnd; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        w, d = x1 - x0, z1 - z0
        self.pocc.append(sbox(x0, z0, x1, z1))
        if w < 16 or d < 16:
            self.planter(x0 + 2, z0 + 2, x1 - 2, z1 - 2); return
        g = 5.0 if fountain else 2.0
        for (a, b, c, e) in ((x0 + 3, z0 + 3, cx - g, cz - g), (cx + g, z0 + 3, x1 - 3, cz - g), (x0 + 3, cz + g, cx - g, z1 - 3), (cx + g, cz + g, x1 - 3, z1 - 3)):
            if c - a > 4 and e - b > 4: self.planter(a, b, c, e, Y_WALK, trees)
        if fountain and min(w, d) > 26: self.fountain(cx, cz, min(4.5, min(w, d) / 8))
        elif trees: self.trees.append((cx, cz, 'folhosa', 1.2, Y_WALK))
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            self.benches.append((cx + dx * 7.5, cz + dz * 7.5, -dx, -dz, Y_WALK))
            if min(w, d) > 40: self.benches.append((cx + dx * 7.5 + dz * 3, cz + dz * 7.5 + dx * 3, -dx, -dz, Y_WALK))

    # ------------------------------------------------------------ patios internos (miolo das quadras)
    # ------------------------------------------------------------ campus das profissoes (quadra inteira)
    CAMPUS_FLOORS = {'medico': 8, 'professor': 4, 'policial': 5, 'bombeiro': 4, 'juiz': 5, 'enfermeiro': 6, 'repositor': 2,
                     'empresario': 28, 'programador': 16, 'engenheiro': 12, 'secretario': 14, 'advogado': 10}

    def campus(self, bi, blk, jid, side):
        """a profissao ocupa a quadra inteira: predio principal em toda a frente, duas alas laterais formando um U,
        e o patio tematico no meio (ligado a rua de tras por uma entrada de carros)"""
        import jobs2_6
        poly = blk['poly']; minx, minz, maxx, maxz = poly.bounds
        for _ in range(20):
            if sbox(minx, minz, maxx, maxz).buffer(-0.5).within(poly): break
            minx += 1.5; minz += 1.5; maxx -= 1.5; maxz -= 1.5
        L = (maxx - minx) if side in ('N', 'S') else (maxz - minz); D = (maxz - minz) if side in ('N', 'S') else (maxx - minx)
        self.lawn(poly, 'paver', Y_WALK, (236, 232, 224))
        spec = jobs2_6.SPEC[jid]
        mw = min(L - 4.0, 104.0); md = max(22.0, min(34.0, D * 0.36)); off = (L - mw) / 2
        F = self.frame(side, minx, maxx, minz, maxz, off)
        jobs2_6.place(self, F, jid, mw, md, self.CAMPUS_FLOORS.get(jid, max(3, spec[2])))
        self.M.free('lotes')
        Ff = self.frame(side, minx, maxx, minz, maxz, 0.0)
        self.pocc.append(Polygon(Ff.rect(off - 1, off + mw + 1, -1, md + 1)))
        # alas laterais (U): mesmo acabamento, menos andares, janelas nas duas faces longas
        wall, acc = spec[6], spec[7]
        wf = max(2, min(5, self.CAMPUS_FLOORS.get(jid, spec[2]) // 2)); hh = 3.4 * wf + 1.2
        ww = min(16.0, L * 0.18); v0, v1 = md + 2.0, D - 2.0
        if v1 - v0 > 12:
            for (u0, u1) in ((2.0, 2.0 + ww), (L - 2.0 - ww, L - 2.0)):
                self.M.at(*Ff.xz((u0 + u1) / 2, (v0 + v1) / 2), 'lotes')
                self.B.box(Ff, u0, u1, v0, v1, Y_WALK, Y_WALK + hh, wall, 'reboco' if spec[1] != 'tijolo' else 'tijolo', top=False)
                self.B.flat_roof(Ff, u0, u1, v0, v1, Y_WALK + hh, 0.8, shade(wall, -8), True)
                for f in range(wf):
                    y = Y_WALK + 1.0 + f * 3.4
                    q = v0 + 1.6
                    while q < v1 - 1.2:
                        for (uu, sd) in ((u0, -1), (u1, 1)): self.B.window(Ff, uu, q, y, 1.6, 1.8, sd, None, 'u')
                        q += 3.2
                    self.B.panel_u(Ff, v0, v1, u0, y - 0.5, y - 0.3, acc, 'liso', -1, 0.04); self.B.panel_u(Ff, v0, v1, u1, y - 0.5, y - 0.3, acc, 'liso', 1, 0.04)
                self.B.solid(Ff, u0, u1, v0, v1)
                self.M.free('lotes')
            self.pocc.append(Polygon(Ff.rect(2.0, L - 2.0, v0, v1)))
            # patio tematico entre as alas + entrada de carros pela rua de tras
            ya0, ya1 = 2.0 + ww + 1.5, L - 2.0 - ww - 1.5
            a = Ff.xz(ya0, v0 + 0.5); b = Ff.xz(ya1, v1 - 2.5)
            x0, x1 = sorted((a[0], b[0])); z0, z1 = sorted((a[1], b[1]))
            Fb = self.frame({'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}[side], minx, maxx, minz, maxz, 0.0)
            self.access(self.frame({'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}[side], minx, maxx, minz, maxz, L / 2 - 3.8), 0.0, 7.6, 3.0)
            if x1 - x0 > 14 and z1 - z0 > 14: self.job_yard(jid, x0, z0, x1, z1)

    def job_yard(self, jid, x0, z0, x1, z1):
        import yards6
        yards6.build(self, jid, x0, z0, x1, z1)

    def courtyard(self, x0, z0, x1, z1):
        """patio interno de verdade, cada um com um uso: terraco de cafe, jardim com pergolado, patio da escultura,
        descanso com redario e mesas de jogos. Sempre com postes, bancos, lixeiras e painel de cartazes."""
        r = self.rnd; M = self.M; y = Y_WALK + 0.06                          # piso do patio 6 cm acima do piso da quadra (sem piscar)
        self.pocc.append(sbox(x0, z0, x1, z1))
        w, d = x1 - x0, z1 - z0; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        M.at(cx, cz, 'lotes'); M.free('lotes'); M.m('paver'); M.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], Y_WALK - 0.05, y, (226, 220, 210))
        if w < 12 or d < 12: self.planter(x0 + 1, z0 + 1, x1 - 1, z1 - 1); return
        kind = r.choice(('cafe', 'jardim', 'escultura', 'descanso'))
        G = (242, 240, 236)
        def bed(a, b, c, e, flowers=True):                                   # canteiro elevado com borda de pedra
            M.m('pedra'); M.prism([(a, b), (c, b), (c, e), (a, e)], y, y + 0.45, (200, 194, 182))
            M.m('grama'); M.prism([(a + 0.25, b + 0.25), (c - 0.25, b + 0.25), (c - 0.25, e - 0.25), (a + 0.25, e - 0.25)], y + 0.45, y + 0.47, (110, 160, 80))
            if flowers:
                q = a + 0.8
                while q < c - 0.5: self.trees.append((q, (b + e) / 2, 'flores', 1.0, y + 0.47)); q += 1.4
        if kind == 'cafe':
            ni = min(4, int((w - 6) / 4.5)); nk = min(3, int((d - 6) / 4.5))       # terraco compacto no meio (nada de mar de mesas)
            ox_ = cx - (ni - 1) * 2.25; oz_ = cz - (nk - 1) * 2.25
            # o resto do patio vira jardim: canteiros com arvores nas bordas
            if w > 26 or d > 22:
                for (a, b) in ((x0 + 2, x0 + 5), (x1 - 5, x1 - 2)):
                    if a > ox_ - 4 or b < ox_ + (ni - 1) * 4.5 + 4: continue
                bed(x0 + 2, z0 + 2, x0 + 4.5, z1 - 2, False); bed(x1 - 4.5, z0 + 2, x1 - 2, z1 - 2, False)
                for q in range(int((d - 6) / 7)):
                    self.trees.append((x0 + 3.25, z0 + 4 + q * 7, 'folhosa', 1.0, y + 0.47)); self.trees.append((x1 - 3.25, z0 + 4 + q * 7, 'ornamental', 1.0, y + 0.47))
            for i in range(ni):
                for k in range(nk):
                    tx, tz = ox_ + i * 4.5, oz_ + k * 4.5
                    M.m('metal'); M.cyl(tx, tz, 0.05, y, y + 0.74, (50, 52, 56), 6); M.cyl(tx, tz, 0.3, y, y + 0.03, (50, 52, 56), 8)
                    M.m('madeira'); M.cyl(tx, tz, 0.42, y + 0.74, y + 0.78, (180, 140, 96), 12)
                    for (ox, oz) in ((0.75, 0), (-0.75, 0)):
                        M.m('metal'); M.box(tx + ox - 0.2, tx + ox + 0.2, y + 0.44, y + 0.48, tz - 0.2, tz + 0.2, (40, 80, 70))
                        M.box(tx + ox * 1.25 - 0.03, tx + ox * 1.25 + 0.03, y + 0.48, y + 0.9, tz - 0.2, tz + 0.2, (40, 80, 70))
                        for (ex, ez) in ((-0.17, -0.17), (0.17, -0.17), (0.17, 0.17), (-0.17, 0.17)): M.box(tx + ox + ex - 0.015, tx + ox + ex + 0.015, y, y + 0.44, tz + ez - 0.015, tz + ez + 0.015, (40, 44, 48))
                    if (i + k) % 2 == 0:
                        M.m('metal'); M.cyl(tx, tz, 0.03, y + 0.78, y + 2.4, (220, 220, 224), 6)
                        M.m('liso'); M.cyl(tx, tz, 1.3, y + 2.0, y + 2.45, r.choice(((200, 60, 50), (240, 230, 210), (40, 110, 90))), 8, False, 0.05)
            # cordao de luzes atravessando o patio
            M.m('liso')
            lw = ni * 4.5 + 2
            for k in range(int(lw / 1.5)): M.sphere(cx - lw / 2 + 0.75 + k * 1.5, y + 3.2 - 0.25 * math.sin(math.pi * k / max(1, int(lw / 1.5))), cz, 0.07, GLOW6, 4, 3)
        elif kind == 'jardim':
            bed(x0 + 1.5, z0 + 1.5, x1 - 1.5, z0 + 3.0); bed(x0 + 1.5, z1 - 3.0, x1 - 1.5, z1 - 1.5)
            # pergolado central com bancos dos dois lados
            M.m('madeira'); L_ = min(w - 8, 14.0); u0 = cx - L_ / 2
            n = max(2, int(L_ / 3.5))
            for i in range(n + 1):
                u = u0 + i * L_ / n
                for s_ in (-1, 1): M.box(u - 0.1, u + 0.1, y, y + 2.6, cz + s_ * 1.6 - 0.1, cz + s_ * 1.6 + 0.1, (150, 108, 70))
            for s_ in (-1, 1): M.box(u0 - 0.3, u0 + L_ + 0.3, y + 2.45, y + 2.62, cz + s_ * 1.6 - 0.07, cz + s_ * 1.6 + 0.07, (150, 108, 70))
            q = u0
            while q <= u0 + L_: M.box(q - 0.03, q + 0.03, y + 2.62, y + 2.7, cz - 2.0, cz + 2.0, (150, 108, 70)); q += 0.6
            M.m('folhagem')
            for i in range(int(L_ / 1.4)): M.sphere(u0 + 0.7 + i * 1.4, y + 2.78, cz, 0.8, (80, 140, 70) if i % 3 else (200, 90, 150), 6, 3, 0.35)
            for i in range(n):
                u = u0 + (i + 0.5) * L_ / n
                for s_ in (-1, 1): self.benches.append((u, cz + s_ * 0.9, 0, -s_, y))
        elif kind == 'escultura':
            self.fountain(cx, cz, min(3.2, min(w, d) / 7)) if min(w, d) > 18 else None
            # escultura abstrata em pedestal num canto e arcos de metal
            sx, sz = x0 + 4, z0 + 4
            M.m('pedra'); M.box(sx - 0.8, sx + 0.8, y, y + 1.0, sz - 0.8, sz + 0.8, (220, 216, 208))
            M.m('metal'); M.sphere(sx, y + 2.0, sz, 0.75, (200, 90, 50), 8, 6); M.cyl(sx, sz, 0.12, y + 1.0, y + 1.4, (60, 60, 64), 6)
            for k in range(4):
                a = k * math.pi / 2 + 0.4; M.sphere(cx + math.cos(a) * (min(w, d) / 2 - 3), y + 0.4, cz + math.sin(a) * (min(w, d) / 2 - 3), 0.4, (190, 186, 178), 6, 4)
            for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)): self.benches.append((cx + dx * 6.0, cz + dz * 6.0, -dx, -dz, y))
        else:   # descanso: espreguicadeiras, mesas de xadrez e redes
            for i in range(int((w - 6) / 6)):
                tx = x0 + 4 + i * 6
                M.m('liso'); M.box(tx - 0.45, tx + 0.45, y + 0.68, y + 0.74, z0 + 3.5, z0 + 4.4, (210, 208, 202))
                for c_ in range(8):
                    for k_ in range(8):
                        if (c_ + k_) % 2: M.box(tx - 0.32 + c_ * 0.08, tx - 0.24 + c_ * 0.08, y + 0.741, y + 0.745, z0 + 3.63 + k_ * 0.08, z0 + 3.71 + k_ * 0.08, (40, 40, 40))
                M.m('concreto'); M.cyl(tx, z0 + 3.95, 0.16, y, y + 0.68, (200, 198, 192), 8)
                for s_ in (-1, 1): M.m('concreto'); M.cyl(tx + s_ * 0.85, z0 + 3.95, 0.2, y, y + 0.45, (200, 198, 192), 8)
            for i in range(int((w - 6) / 3.0)):
                lx = x0 + 3.5 + i * 3.0; lz = z1 - 4.0
                M.m('madeira'); M.poly([(lx - 0.35, y + 0.35, lz - 1.0), (lx + 0.35, y + 0.35, lz - 1.0), (lx + 0.35, y + 0.75, lz + 0.8), (lx - 0.35, y + 0.75, lz + 0.8)], (200, 170, 120), None)
                M.box(lx - 0.35, lx + 0.35, y, y + 0.35, lz - 1.0, lz - 0.9, (150, 110, 70)); M.box(lx - 0.35, lx + 0.35, y, y + 0.75, lz + 0.7, lz + 0.8, (150, 110, 70))
                M.m('liso'); M.box(lx - 0.3, lx + 0.3, y + 0.37, y + 0.43, lz - 0.9, lz - 0.1, r.choice(((240, 240, 240), (90, 160, 210), (240, 190, 60))))
            for k in range(2): self.trees.append((cx + (k * 2 - 1) * w * 0.25, cz, 'folhosa', 1.1, y))
        # patio grande: fileiras de arvores em golas nas bordas (sombra e sem piso vazio), com bancos entre elas
        if kind != 'cafe' and w > 28 and d > 22:
            for zz in (z0 + 3.0, z1 - 3.0):
                q = x0 + 5.0
                while q < x1 - 4.0:
                    M.m('pedra'); M.prism([(q - 0.9, zz - 0.9), (q + 0.9, zz - 0.9), (q + 0.9, zz + 0.9), (q - 0.9, zz + 0.9)], y, y + 0.12, (200, 194, 182))
                    self.trees.append((q, zz, r.choice(('folhosa', 'ornamental', 'florida')), r.uniform(0.9, 1.15), y + 0.12))
                    if q + 3.5 < x1 - 4.0: self.benches.append((q + 3.5, zz, 0, 1 if zz < cz else -1, y))
                    q += 7.0
        # sempre: postes baixos nos cantos, lixeiras e painel de cartazes
        for (px, pz) in ((x0 + 1.2, z0 + 1.2), (x1 - 1.2, z1 - 1.2), (x0 + 1.2, z1 - 1.2), (x1 - 1.2, z0 + 1.2)):
            self.plights.append((px, pz, y))
        M.m('metal'); M.cyl(x1 - 2.2, z0 + 1.0, 0.25, y, y + 0.9, (46, 80, 60), 8); M.cyl(x0 + 2.2, z1 - 1.0, 0.25, y, y + 0.9, (46, 80, 60), 8)
        self.poster(x0 + 0.6, cz, 0, 1)
        M.free()

    def poster(self, x, z, ux, uz):
        """painel de cartazes (mupi) de dupla face, aceso por dentro, com propaganda colorida"""
        r = self.rnd; M = self.M; y = Y_WALK; vx, vz = -uz, ux
        F = Frame((x, z), (ux if ux or uz else 1, uz))
        M.m('metal'); M.prism(F.rect(-0.62, 0.62, -0.12, 0.12), y, y + 2.1, (60, 64, 70))
        M.m('liso')
        for s_ in (-1, 1):
            c1 = r.choice(((230, 70, 60), (40, 120, 200), (250, 190, 40), (90, 170, 80), (160, 80, 200)))
            M.poly([F.p(-0.5, s_ * 0.125, y + 0.3), F.p(0.5, s_ * 0.125, y + 0.3), F.p(0.5, s_ * 0.125, y + 1.95), F.p(-0.5, s_ * 0.125, y + 1.95)], (250, 248, 240), None)
            M.poly([F.p(-0.42, s_ * 0.127, y + 1.0), F.p(0.42, s_ * 0.127, y + 1.0), F.p(0.42, s_ * 0.127, y + 1.85), F.p(-0.42, s_ * 0.127, y + 1.85)], c1, None)
            M.poly([F.p(-0.42, s_ * 0.127, y + 0.45), F.p(0.42, s_ * 0.127, y + 0.45), F.p(0.42, s_ * 0.127, y + 0.85), F.p(-0.42, s_ * 0.127, y + 0.85)], shade(c1, -40), None)
        self.B.solid(F, -0.62, 0.62, -0.12, 0.12)

    def billboard(self, F, u, v):
        """outdoor de duas colunas (frente para a rua), com refletores e propaganda"""
        r = self.rnd; M = self.M; y = Y_WALK
        x, z = F.xz(u, v); M.at(x, z, 'lotes')
        for s_ in (-1, 1):
            M.m('metal'); a, b = F.xz(u + s_ * 3.0, v); M.cyl(a, b, 0.18, y, y + 5.2, (90, 94, 100), 8)
        G = Frame(F.xz(u, v), (F.ux, F.uz))
        M.m('metal'); M.prism(G.rect(-4.4, 4.4, -0.15, 0.15), y + 5.0, y + 8.2, (70, 74, 80))
        c1 = r.choice(((230, 70, 60), (40, 120, 200), (250, 190, 40), (90, 170, 80), (30, 30, 40)))
        M.m('liso')
        M.poly([G.p(-4.2, -0.16, y + 5.2), G.p(4.2, -0.16, y + 5.2), G.p(4.2, -0.16, y + 8.0), G.p(-4.2, -0.16, y + 8.0)], c1, None)
        M.poly([G.p(-3.6, -0.17, y + 6.2), G.p(1.0, -0.17, y + 6.2), G.p(1.0, -0.17, y + 7.5), G.p(-3.6, -0.17, y + 7.5)], (250, 248, 240), None)
        M.poly([G.p(1.6, -0.17, y + 5.6), G.p(3.8, -0.17, y + 5.6), G.p(3.8, -0.17, y + 7.7), G.p(1.6, -0.17, y + 7.7)], shade(c1, 40), None)
        M.m('metal'); M.prism(G.rect(-4.2, 4.2, -0.9, -0.15), y + 4.9, y + 5.0, (90, 94, 100))
        for k in range(3):
            a, b = G.xz(-3.0 + k * 3.0, -1.0); M.box(a - 0.2, a + 0.2, y + 4.95, y + 5.2, b - 0.2, b + 0.2, (40, 40, 44))
        self.B.solid(F, u - 3.3, u + 3.3, v - 0.4, v + 0.4)
        M.free('lotes')

    def access(self, F, u0, u1, v_in, y=None):
        """acesso de carros a um estacionamento: rebaixo na guia + faixa de concreto sobre a calcada (recortada na calcada
        real) e pista de asfalto da divisa ate dentro do lote (v de 0 a v_in). F: frame na divisa, v para dentro."""
        from shapely.geometry import Polygon as _Pg
        M = self.M; y = Y_WALK + 0.035 if y is None else y
        M.at(*F.xz((u0 + u1) / 2, v_in / 2), 'lotes')
        strip = _Pg(F.rect(u0 - 0.4, u1 + 0.4, -14.0, 0.05)).intersection(H6.ROW)
        seed = _Pg(F.rect(u0, u1, -0.6, 0.05)); M.m('concreto')
        for g in getattr(strip, 'geoms', [strip]):
            if g.geom_type == 'Polygon' and g.intersects(seed): M.shp(g, Y_WALK + 0.025, WHITE)
        M.m('asfalto'); M.poly([F.p(u0, -0.02, y), F.p(u1, -0.02, y), F.p(u1, v_in, y), F.p(u0, v_in, y)], WHITE, (0, 1, 0))
        M.m('liso'); um = (u0 + u1) / 2                          # faixa central tracejada
        vv = 1.0
        while vv < v_in - 1.5:
            M.poly([F.p(um - 0.06, vv, y + 0.03), F.p(um + 0.06, vv, y + 0.03), F.p(um + 0.06, vv + 1.5, y + 0.03), F.p(um - 0.06, vv + 1.5, y + 0.03)], (245, 245, 240), (0, 1, 0))
            vv += 3.0
        M.free('lotes')
        self.B.drives.append((*F.xz(um, -2.4), (u1 - u0) / 2 + 3.0)); self.B.drives.append((*F.xz(um, v_in * 0.5), (u1 - u0) / 2 + 1.0))
        self.pocc.append(_Pg(F.rect(u0 - 1, u1 + 1, -0.5, v_in)))

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
        job = getattr(self, 'jobblk', {}).get(bi)
        if job: kind = 0.6                                  # quadra com predio de profissao: fileira de predios
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
        if dc < 380 and kind < 0.55 and min(w, d) > 80 and not job:
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
        garage = kind > 0.94 and w > 70 and not job
        # ---- perimetro de predios colados (frente para as 4 ruas)
        depths = {sd: r.uniform(16, 23) for sd in 'NESW'}
        if job:
            import jobs2_6
            depths[job[1]] = max(depths[job[1]], jobs2_6.depth(job[0]))
            opp = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}[job[1]]
            span = d if job[1] in ('N', 'S') else w
            depths[opp] = max(8.0, min(depths[opp], span - depths[job[1]] - 4.0))     # o predio grande nao encosta nos fundos do vizinho
        # ---- o miolo vira estacionamento? entao duas aberturas no perimetro, no eixo do miolo (entrada e saida em lados opostos)
        opt = r.random() if not job else 0.6; gaps = {}
        ix0_, iz0_ = minx + depths['W'] + 1.5, minz + depths['N'] + 1.5
        ix1_, iz1_ = maxx - depths['E'] - 1.5, maxz - depths['S'] - 1.5 - (12 if garage else 0)
        if opt < 0.4 and ix1_ - ix0_ > 12 and iz1_ - iz0_ > 12:
            pair = ('W', 'E') if (garage or w > d) else ('N', 'S')
            xc, zc = (ix0_ + ix1_) / 2, (iz0_ + iz1_) / 2
            for sd in pair:
                s_c = {'N': xc - minx, 'S': maxx - xc, 'W': maxz - zc, 'E': zc - minz}[sd]
                gaps[sd] = (s_c - 3.6, s_c + 3.6)
        if job and ix1_ - ix0_ > 12 and iz1_ - iz0_ > 12:
            # patio do predio da profissao ligado a rua: entrada no lado oposto ao predio
            opp = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}[job[1]]
            xc, zc = (ix0_ + ix1_) / 2, (iz0_ + iz1_) / 2
            s_c = {'N': xc - minx, 'S': maxx - xc, 'W': maxz - zc, 'E': zc - minz}[opp]
            gaps = {opp: (s_c - 3.8, s_c + 3.8)}
        for side in ('N', 'E', 'S', 'W'):
            Lside = w if side in ('N', 'S') else d
            nxt = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}[side]
            s = 0.0; end = Lside - depths[nxt]
            if garage and side == 'S':
                F = self.frame(side, minx, maxx, minz, maxz, 0.5)
                self.M.at(*F.xz(20, 15), 'lotes')
                for ((px, pz), py) in C6.parking_garage(B, F, min(end - 1, 46), 30, r.choice((4, 5, 6))): self.parked.append((px, pz, F.vx, F.vz, py))
                self.M.free('lotes'); s = min(end - 1, 46) + 1.5
            gap = gaps.get(side)
            jdo = job is not None and job[1] == side
            if jdo:
                import jobs2_6
                jw = jobs2_6.width(job[0]); s_job = max(s + 2.0, (end - jw) / 2)
            while s < end - 6:
                if jdo and s >= s_job - 0.01:
                    Fj = self.frame(side, minx, maxx, minz, maxz, s_job)
                    jobs2_6.place(self, Fj, job[0]); self.M.free('lotes')
                    s = s_job + jw; jdo = False; continue
                if gap and gap[0] - 0.01 <= s < gap[1]: s = gap[1]; continue
                pw = min(r.uniform(13, 30), end - s)
                if end - s - pw < 9: pw = end - s
                if jdo and s + pw > s_job - 0.01:
                    pw = s_job - s
                    if pw < 6: s = s_job; continue
                if gap and s < gap[0] < s + pw:
                    pw = gap[0] - s
                    if pw < 6: s = gap[1]; continue
                F = self.frame(side, minx, maxx, minz, maxz, s)
                _fp = Polygon(F.rect(0, pw, 0, depths[side]))                    # quadra em L: nada de predio fora dela (em cima do hospital etc.)
                if _fp.intersection(poly).area < 0.85 * _fp.area: s += pw; continue
                fl = max(3, min(hmax + 3, int(r.uniform(0.35, 1.1) * hmax)))
                if resid: fl = max(4, int(fl * 0.9))
                self.M.at(*F.xz(pw / 2, depths[side] / 2), 'lotes')
                C6.midrise(B, F, pw - 0.15, depths[side] - r.choice((0, 0, 1.5, 3.0)), fl, None, None, True, None, True, r.choice(('moderna', 'janelas', 'moderna', 'classica')) if resid else None)
                self.M.free('lotes')
                s += pw
        # ---- miolo: jardim, estacionamento ou parquinho
        ix0, iz0, ix1, iz1 = minx + depths['W'] + 1.5, minz + depths['N'] + 1.5, maxx - depths['E'] - 1.5, maxz - depths['S'] - 1.5
        if garage: iz1 -= 12
        # quadra em L ou torta: o miolo tem que caber DENTRO da quadra (antes o retangulo do contorno invadia as ruas)
        inner = poly.buffer(-max(min(depths.values()), 6.0) - 1.5)
        if not inner.is_empty and not sbox(ix0, iz0, ix1, iz1).within(poly.buffer(-1.0)):
            q = sbox(ix0, iz0, ix1, iz1).intersection(inner)
            ok = False
            for _ in range(40):
                bx0, bz0, bx1, bz1 = q.bounds if not q.is_empty else (0, 0, 0, 0)
                cand = sbox(bx0, bz0, bx1, bz1)
                if not q.is_empty and cand.within(poly.buffer(-1.0)) and cand.difference(q).area < 1.0: ix0, iz0, ix1, iz1 = bx0, bz0, bx1, bz1; ok = True; break
                q = q.buffer(-1.5, join_style='mitre') if not q.is_empty else q
                if q.is_empty: break
                q = max(getattr(q, 'geoms', [q]), key=lambda g: g.area)
            if not ok:
                # quadra em L: os dois maiores retangulos que cabem dentro dela viram patios (nada de piso vazio)
                ix1 = ix0
                free = inner.buffer(0)
                for _ in range(2):
                    best = None
                    bx0, bz0, bx1, bz1 = free.bounds
                    gx = bx0
                    while gx < bx1 - 14:
                        gz = bz0
                        while gz < bz1 - 14:
                            if free.contains(Point(gx + 1, gz + 1)):
                                x1_ = gx + 14
                                while x1_ + 4 <= bx1 and sbox(gx, gz, x1_ + 4, gz + 14).within(free): x1_ += 4
                                z1_ = gz + 14
                                while z1_ + 4 <= bz1 and sbox(gx, gz, x1_, z1_ + 4).within(free): z1_ += 4
                                if sbox(gx, gz, x1_, z1_).within(free):
                                    a = (x1_ - gx) * (z1_ - gz)
                                    if best is None or a > best[0]: best = (a, gx, gz, x1_, z1_)
                            gz += 6
                        gx += 6
                    if best is None: break
                    _, a0, b0, a1, b1 = best
                    self.courtyard(a0, b0, a1, b1)
                    free = free.difference(sbox(a0 - 3, b0 - 3, a1 + 3, b1 + 3))
                    if free.is_empty: break
        if ix1 - ix0 > 10 and iz1 - iz0 > 10:
            if job and gaps:
                for sd, (g0, g1) in gaps.items():
                    self.access(self.frame(sd, minx, maxx, minz, maxz, g0), 0.0, g1 - g0, depths[sd] + 1.6)
                self.job_yard(job[0], ix0, iz0, ix1, iz1)
                return
            if opt < 0.4 and not gaps: opt = 0.5                     # sem abertura no perimetro nao ha estacionamento
            if opt < 0.4:
                for sd, (g0, g1) in gaps.items():
                    self.access(self.frame(sd, minx, maxx, minz, maxz, g0), 0.0, g1 - g0, depths[sd] + 1.6)
                Fp = Frame((ix0, iz0), (1, 0)); self.M.at((ix0 + ix1) / 2, (iz0 + iz1) / 2, 'lotes')
                B.parking(Fp, 0.5, ix1 - ix0 - 0.5, 0.5, iz1 - iz0 - 0.5, self.park_car, Y_WALK + 0.01); self.M.free('lotes'); self.pocc.append(sbox(ix0, iz0, ix1, iz1))
            else: self.courtyard(ix0, iz0, ix1, iz1)                  # patio interno com uso (varia de quadra para quadra)

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
            B.parking(Fp, 0, half - minx - 5, 0.5, iz1 - iz0 - 0.5, self.park_car, Y_WALK + 0.01); self.M.free('lotes'); self.pocc.append(sbox(minx + 3, iz0, half - 2, iz1))
            zc = (iz0 + iz1) / 2
            self.access(self.frame('W', minx, maxx, minz, maxz, maxz - zc - 3.6), 0.0, 7.2, 3.2)
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
        def missing():
            placed = {h['k'] for h in self.player}
            for k in [k for k in HOUSE_BAIRRO if k not in placed]:
                for fi in sorted(range(len(fronts)), key=lambda q: -fronts[q][5]):
                    f = fronts[fi]
                    if f[0] != 'rua' or fi in reserve: continue
                    n0 = len(self.player); self.front_lots_player_only(f, k)
                    if len(self.player) > n0: break
        for fi in order:
            if fi not in reserve: continue
            f = fronts[fi]
            if f[0] == 'bulb': self.bulb_lots(f[1])
            else: self.front_lots(f, reserve.get(fi, []))
        missing()                                         # casa do jogador que nao coube na fileira reservada: outra rua ainda vazia
        for fi in order:
            if fi in reserve: continue
            f = fronts[fi]
            if f[0] == 'bulb': self.bulb_lots(f[1])
            else: self.front_lots(f, [])
        self.pocket_parks()
        print(f'  casas do jogador reservadas: {len(self.player)}/17; caminho x portao: erro maximo {getattr(self, "gate_err", -1):.2f} m')

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
                    self.put_house(F, cl, Dq, style, pal_base, sf, 1 if q % 2 == 0 else -1, picket, r.random() < 0.72, q == 0)
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
                self.put_house(F, cl, min(Dq, 30.0), style, pal_base, sf, 1 if q % 2 == 0 else -1, False, r.random() < 0.5, False)
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
            # equipamentos (quadra, playground, piquenique...) onde couber, fora do caminho
            import park6, shapely
            rest = g.buffer(-2.0).difference(pth.buffer(1.2)); stn = []
            names = ['playground', 'piquenique', 'academia', 'basquete', 'coreto', 'jardim', 'caes', 'tenis', 'futsal', 'quiosque']; r.shuffle(names)
            for _ in range(4):
                gs = [q for q in getattr(rest, 'geoms', [rest]) if q.geom_type == 'Polygon' and q.area > 150]
                if not gs or len(stn) >= 3: break
                q = max(gs, key=lambda t: t.area)
                mic = shapely.maximum_inscribed_circle(q); cc = mic.coords[0]; ok = False
                bb = q.bounds
                for nm in names:
                    fn, ha, hb = park6.STATIONS[nm]
                    for (ux, uz) in (((1, 0), (0, 1)) if bb[2] - bb[0] >= bb[3] - bb[1] else ((0, 1), (1, 0))):
                        fp = Polygon(Frame(cc, (ux, uz)).rect(-ha, ha, -hb, hb))
                        if fp.within(q):
                            park6.place(_Sink(self), nm, cc[0], cc[1], ux, uz, r, Y_LAWN + 0.05); self.M.free('lotes')
                            stn.append(fp.buffer(2.5)); rest = rest.difference(fp.buffer(3)); names.remove(nm); ok = True; break
                    if ok: break
                if not ok: rest = rest.difference(Point(cc).buffer(mic.length * 0.8))
            for _ in range(int(g.area / 110)):
                x, z = r.uniform(mnx, mxx), r.uniform(mnz, mxz)
                if g.buffer(-2).contains(Point(x, z)) and not pth.buffer(2).contains(Point(x, z)) and not any(s_.contains(Point(x, z)) for s_ in stn):
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
        if w < 50 and r.random() < 0.45: B.gas_station(F, w, d - 1, r.choice(signs)); self.access(F, 1.5, 7.5, 0.6); self.access(F, w - 7.5, w - 1.5, 0.6); return
        pk = 15.0 if d > 30 else 8.0
        B.parking(F, 1, w - 1, 0.5, pk, self.park_car)
        if pk >= 8 and w > 30 and r.random() < 0.55: self.billboard(F, 6.0 if r.random() < 0.5 else w - 6.0, 1.2)   # outdoor na frente do estacionamento
        self.access(F, 2.0, 8.0, 0.6); self.access(F, w - 8.0, w - 2.0, 0.6)
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
        self.plights = []
        for bi, blk in enumerate(self.P.blocks):
            z = blk['zone']; self.pocc = []; c0 = len(self.B.colliders)
            if self.special.get(bi, ('',))[0] == 'hospital' or bi in getattr(self, 'jobblk', {}): pass
            elif z in ('centro', 'orla') or (z == 'marina' and blk['poly'].bounds[0] > 2040) or (bi in self.special and not self.special[bi][0].startswith('escola') and self.special[bi][0] != 'hospital'): blk['encher'] = c0
            if bi in self.special: self.special_block(bi, blk, *self.special[bi])
            elif z == 'suburbio': pass
            elif bi in getattr(self, 'jobblk', {}): self.campus(bi, blk, *self.jobblk[bi])
            elif z == 'centro': self.centro(bi, blk)
            elif z == 'orla': self.orla(bi, blk)
            elif z == 'marina' and blk['poly'].bounds[0] > 2040: blk['feito'] = True; self.orla(bi, blk)      # orla leste: hoteis e predios (a marina fica so na quadra junto ao rio)
            elif z in ('parque', 'ribeirinho'): self.lawn(blk['poly'])
            elif z == 'praia': pass                     # calcadao, mureta e areia: orla6.py
            if 'encher' in blk: self.fill_free(blk['poly'], c0, (), True, 2)
        self.suburbs()
        return self
