"""ORLA das praias: calcadao com ondas + ciclovia, muro com escadas para a areia, faixa de palmeiras, quiosques, salva-vidas, chuveiros, redes de volei, guarda-sois e PIERES."""
import math, random
import numpy as np
from bake import rgb, shade, PLAIN, STONE, WOOD, METAL, PAVER, ROOF, TILE
from plan import *
import shore, scenery

YP = 2.40           # nivel do calcadao (acima do mar)
HALF_W = 7.0        # meia-largura do calcadao (de -7 mar a +7 avenida)
COL = {'wave1': rgb('#EDE7DA'), 'wave2': rgb('#2F2F33'), 'wave3': rgb('#C9C3B5'), 'bike': rgb('#B8452F'), 'wall': rgb('#CFCABF'), 'wall2': rgb('#B3AD9F'), 'grass': rgb('#6FA84A'),
       'wood': rgb('#8B6B47'), 'wood2': rgb('#6E5236'), 'rail': rgb('#E9E6DE'), 'lamp': rgb('#2B2E33'), 'bench': rgb('#7A5A3A'), 'iron': rgb('#2A2C30'), 'sand': rgb('#E4D4B4'),
       'roof': rgb('#B58A4A'), 'towerR': rgb('#D6402A'), 'towerW': rgb('#F2F2F2'), 'net': rgb('#E5E5E5'), 'step': rgb('#D8D3C7'), 'step2': rgb('#BEB8AA'), 'white': rgb('#F5F5F5'), 'water': rgb('#4F9BD0'),
       'trunk': rgb('#7A5A3A'), 'leaf': rgb('#3F8A3F'), 'shower': rgb('#A8B0B8')}
UMB = [rgb(c) for c in ('#E53935', '#FDD835', '#1E88E5', '#43A047', '#FB8C00', '#8E24AA', '#00ACC1')]

def norm(dx, dz):
    l = math.hypot(dx, dz) or 1e-9
    return dx / l, dz / l

class Orla:
    def __init__(self, gr, geo, hf, seed=RNG):
        self.g = gr; self.geo = geo; self.hf = hf; self.B = gr.B; self.rnd = random.Random(seed)
        self.gy, self.gx = np.gradient(geo.Dsea, CELL)
        self.items = {'palms': [], 'lamps': [], 'benches': [], 'kiosks': [], 'towers': [], 'showers': [], 'courts': [], 'umbrellas': [], 'stairs': [], 'piers': [], 'paths': [], 'bins': []}
        self.stats = {'prom_m': 0.0, 'wall_m': 0.0, 'stairs': 0, 'piers': 0}
        self.lines = shore.beach_lines(geo, 31.0, 120.0)
        self.polys = []          # (layer, pts) p/ validar
        self.frames_all = []

    # ---------------------------------------------------------- geometria basica
    def grad(self, x, z):
        fx = min(max(x / CELL, 0), NX - 1.001); fz = min(max(z / CELL, 0), NZ - 1.001); i, j = int(fx), int(fz); a, b = fx - i, fz - j
        def bl(A): return (A[j, i] * (1 - a) + A[j, i + 1] * a) * (1 - b) + (A[j + 1, i] * (1 - a) + A[j + 1, i + 1] * a) * b
        return bl(self.gx), bl(self.gy)

    def frames(self, line, step=4.0):
        pts = shore.resample(line, step); out = []
        for k, p in enumerate(pts):
            a = pts[max(k - 2, 0)]; b = pts[min(k + 2, len(pts) - 1)]
            tx, tz = norm(b[0] - a[0], b[1] - a[1]); gx, gz = self.grad(*p)
            nx_, nz_ = -tz, tx
            if nx_ * gx + nz_ * gz < 0: nx_, nz_ = -nx_, -nz_              # normal para o lado da AVENIDA (aumenta a distancia ao mar)
            out.append({'x': p[0], 'z': p[1], 'tx': tx, 'tz': tz, 'nx': nx_, 'nz': nz_, 's': 0.0})
        acc = 0.0
        for k in range(1, len(out)):
            acc += math.hypot(out[k]['x'] - out[k - 1]['x'], out[k]['z'] - out[k - 1]['z']); out[k]['s'] = acc
        return out

    def P(self, f, o, dy=0.0, s_off=0.0):
        return (f['x'] + f['nx'] * o + f['tx'] * s_off, YP + dy, f['z'] + f['nz'] * o + f['tz'] * s_off)

    def strip(self, fr, o0, o1, dy, mat, col, layer=None, i0=0, i1=None):
        i1 = len(fr) - 1 if i1 is None else i1
        for k in range(i0, i1):
            a, b = fr[k], fr[k + 1]
            q = [self.P(a, o0, dy), self.P(b, o0, dy), self.P(b, o1, dy), self.P(a, o1, dy)]
            self.g.quad(mat, q, col, layer)

    def vwall(self, fr, o, y0, y1, col, face, mat=STONE, gaps=()):
        for k in range(len(fr) - 1):
            a, b = fr[k], fr[k + 1]
            if any(g0 <= a['s'] <= g1 or g0 <= b['s'] <= g1 for g0, g1 in gaps): continue
            pa, pb = self.P(a, o, y0), self.P(b, o, y0)
            nv = (a['nx'] * face, 0, a['nz'] * face)
            self.B.quad(mat, [pa, pb, (pb[0], YP + y1, pb[2]), (pa[0], YP + y1, pa[2])], nv, col, None, True)

    # ---------------------------------------------------------- construcao por segmento
    def build_line(self, line, idx):
        fr = self.frames(line)
        if len(fr) < 10: return
        L = fr[-1]['s']; self.stats['prom_m'] += L
        # posicoes de escada / pier
        stairs = []; s = 45.0
        while s < L - 30: stairs.append(s); s += 92.0 + self.rnd.uniform(-8, 8)
        piers = []
        if L > 500: piers.append(L * (0.42 if idx % 2 == 0 else 0.55))
        gaps = [(s_ - 3.4, s_ + 3.4) for s_ in stairs] + [(p_ - 4.8, p_ + 4.8) for p_ in piers]
        # --- piso com ondas: 7 faixas de 2 m, fase deslocada com a distancia (dai o desenho de onda)
        nb = 7
        for b in range(nb):
            o0 = -HALF_W + 2.0 * b; o1 = o0 + 2.0
            for k in range(len(fr) - 1):
                a_, b_ = fr[k], fr[k + 1]
                ph = math.sin((a_['s'] + b * 3.5) / 7.0) > 0
                col = COL['wave1'] if (ph and b % 2 == 0) or (not ph and b % 2 == 1) else (COL['wave2'] if b % 3 == 0 else COL['wave3'])
                if b in (5, 6): col = COL['bike']
                q = [self.P(a_, o0, 0.06), self.P(b_, o0, 0.06), self.P(b_, o1, 0.06), self.P(a_, o1, 0.06)]
                self.g.quad(PAVER, q, col, 'bike' if b in (5, 6) else ('prom2' if col == COL['wave2'] else 'prom'))
        # linhas da ciclovia
        self.strip(fr, 3.0 - 0.08, 3.0 + 0.08, 0.08, PLAIN, COL['white'], None)
        self.strip(fr, 6.0 - 0.08, 6.0 + 0.08, 0.08, PLAIN, COL['white'], None)
        # --- meio-fio do lado da avenida + canteiro de palmeiras/gramado
        self.strip(fr, HALF_W, HALF_W + 0.25, 0.20, PAVER, COL['wall'], 'curb')
        self.vwall(fr, HALF_W, 0.06, 0.20, COL['wall'], 1)
        self.strip(fr, HALF_W + 0.25, HALF_W + 2.7, 0.14, TILE if False else PAVER, COL['grass'], 'verge')
        # --- muro de contencao/balaustrada do lado do mar, com vaos nas escadas e nos piers
        self.vwall(fr, -HALF_W, -1.5, 0.98, COL['wall'], -1, STONE, gaps)
        self.vwall(fr, -HALF_W - 0.35, 0.0, 0.98, COL['wall2'], 1, STONE, gaps)
        for k in range(len(fr) - 1):
            a_, b_ = fr[k], fr[k + 1]
            if any(g0 <= a_['s'] <= g1 or g0 <= b_['s'] <= g1 for g0, g1 in gaps): continue
            q = [self.P(a_, -HALF_W - 0.35, 0.98), self.P(b_, -HALF_W - 0.35, 0.98), self.P(b_, -HALF_W + 0.05, 0.98), self.P(a_, -HALF_W + 0.05, 0.98)]
            self.B.quad(STONE, q, (0, 1, 0), COL['wall'], None, True); self.stats['wall_m'] += 4.0
            self.polys.append(('wall', [(p[0], p[2]) for p in q]))
        # --- escadas
        for s_ in stairs: self.stairs(fr, s_)
        # --- piers
        for s_ in piers: self.pier(fr, s_)
        # --- mobiliario: palmeiras, postes, bancos, lixeiras
        gp = gaps
        pp_ = [(q['x'], q['z']) for q in self.items['paths']]
        def in_gap(s_, pad=0.0):
            if any(g0 - pad <= s_ <= g1 + pad for g0, g1 in gp): return True
            f_ = self.at(fr, s_)
            return any(math.hypot(f_['x'] + f_['nx'] * 9.0 - px, f_['z'] + f_['nz'] * 9.0 - pz) < 5.5 + pad for px, pz in pp_)
        s_ = 6.0
        while s_ < L - 4:
            f = self.at(fr, s_)
            if not in_gap(s_, 2.5): self.palm(f, HALF_W + 1.5)
            s_ += 15.0
        s_ = 12.0; alt = 1
        while s_ < L - 4:
            f = self.at(fr, s_)
            if not in_gap(s_, 2.0):
                self.lamp(f, HALF_W - 0.4 if alt > 0 else -HALF_W + 0.9); alt = -alt
            s_ += 26.0
        s_ = 30.0
        while s_ < L - 4:
            f = self.at(fr, s_)
            if not in_gap(s_, 3.0): self.bench(f, -HALF_W + 1.6)
            s_ += 42.0
        # --- areia: quiosques, salva-vidas, redes de volei, chuveiros, guarda-sois
        s_ = 70.0
        while s_ < L - 40:
            if not in_gap(s_, 8.0): self.kiosk(self.at(fr, s_), -HALF_W - 9.0, idx)
            s_ += 148.0
        s_ = 110.0
        while s_ < L - 40:
            if not in_gap(s_, 8.0): self.tower(self.at(fr, s_), -HALF_W - 17.0)
            s_ += 236.0
        s_ = 175.0
        while s_ < L - 50:
            if not in_gap(s_, 8.0): self.court(self.at(fr, s_), -HALF_W - 15.0)
            s_ += 205.0
        for s_ in stairs: self.shower(self.at(fr, s_ + 5.5), -HALF_W - 4.0)
        # guarda-sois em manchas
        for _ in range(int(L / 9)):
            s_ = self.rnd.uniform(10, L - 10); f = self.at(fr, s_); o = -HALF_W - self.rnd.uniform(9, 17)
            if not in_gap(s_, 5.0): self.umbrella(f, o)
        # --- acessos da avenida ao calcadao (calcada cruzando a faixa de palmeiras) onde ha rua em T
        self.frames_all.append(fr)

    def at(self, fr, s):
        lo, hi = 0, len(fr) - 1
        while hi - lo > 1:
            m = (lo + hi) // 2
            if fr[m]['s'] <= s: lo = m
            else: hi = m
        a, b = fr[lo], fr[hi]; t = (s - a['s']) / max(b['s'] - a['s'], 1e-6)
        f = {k: a[k] + (b[k] - a[k]) * t for k in ('x', 'z', 'tx', 'tz', 'nx', 'nz', 's')}
        l = math.hypot(f['tx'], f['tz']) or 1; f['tx'] /= l; f['tz'] /= l; l = math.hypot(f['nx'], f['nz']) or 1; f['nx'] /= l; f['nz'] /= l
        return f

    # ---------------------------------------------------------- objetos
    def groundy(self, x, z): return max(0.0, self.sample(x, z))

    def sample(self, x, z):
        import terrain_final as T
        return T.sample8(self.hf, x, z)

    def stairs(self, fr_, s0):
        f = self.at(fr_, s0); W = 6.0; rise = 0.14
        x0, z0 = f['x'] + f['nx'] * (-HALF_W), f['z'] + f['nz'] * (-HALF_W)       # topo, na borda do mar do calcadao
        sx, sz = -f['nx'], -f['nz']                                                # sentido de descida (para o mar)
        yb = self.sample(x0 + sx * 3.4, z0 + sz * 3.4)
        n = max(3, int(round((YP - yb) / rise))); rise = (YP - yb) / n; tread = 0.32
        for i in range(n):
            yt = YP - (i + 1) * rise
            c0 = (x0 + sx * (i * tread) - f['tx'] * W / 2, z0 + sz * (i * tread) - f['tz'] * W / 2); c1 = (x0 + sx * ((i + 1) * tread) - f['tx'] * W / 2, z0 + sz * ((i + 1) * tread) - f['tz'] * W / 2)
            c2 = (c1[0] + f['tx'] * W, c1[1] + f['tz'] * W); c3 = (c0[0] + f['tx'] * W, c0[1] + f['tz'] * W)
            col = COL['step'] if i % 2 == 0 else COL['step2']
            self.g.quad(PAVER, [(c0[0], yt + 0.01, c0[1]), (c1[0], yt + 0.01, c1[1]), (c2[0], yt + 0.01, c2[1]), (c3[0], yt + 0.01, c3[1])], col, None)
            # espelho
            self.B.quad(PLAIN, [(c0[0], yt + rise, c0[1]), (c3[0], yt + rise, c3[1]), (c3[0], yt, c3[1]), (c0[0], yt, c0[1])], (-sx, 0, -sz), COL['step2'], None, True)
            self.polys.append(('stairs', [c0, c1, c2, c3]))
        # corrimaos (dois lados + central) e muretas laterais
        for sg in (-1, 1):
            px, pz = x0 - f['tx'] * (W / 2 + 0.05) * (-sg), z0 - f['tz'] * (W / 2 + 0.05) * (-sg)
            for i in range(0, n + 1, 3):
                self.B.cyl(px + sx * i * tread, pz + sz * i * tread, 0.04, YP - i * rise, YP - i * rise + 1.0, COL['iron'], 6)
            self.B.quad(PLAIN, [(px, YP + 0.95, pz), (px + sx * n * tread, YP - n * rise + 0.95, pz + sz * n * tread), (px + sx * n * tread, YP - n * rise + 1.02, pz + sz * n * tread), (px, YP + 1.02, pz)], (-f['nx'] * 0 + f['tx'] * sg, 0, f['tz'] * sg), COL['iron'], None, True)
        self.items['stairs'].append({'x': round(x0, 2), 'z': round(z0, 2), 'dx': round(sx, 3), 'dz': round(sz, 3), 'steps': n, 'w': W, 'top': YP})
        self.stats['stairs'] += 1

    def pier(self, fr_, s0):
        f = self.at(fr_, s0); sx, sz = -f['nx'], -f['nz']                           # do calcadao para o mar
        x0, z0 = f['x'] + f['nx'] * (-HALF_W - 0.3), f['z'] + f['nz'] * (-HALF_W - 0.3)
        W = 7.0; deck = YP + 0.55
        # comprimento ate encontrar agua >= 3,5 m + 20 m
        Lp = 0.0
        while Lp < 220:
            d = -self.sample(x0 + sx * Lp, z0 + sz * Lp)
            if d > 3.5 and Lp > 70: break
            Lp += 4.0
        Lp = max(110.0, Lp + 24.0)
        rx, rz = -sz, sx                                       # lateral do pier
        def PP(a, b, y): return (x0 + sx * a + rx * b, y, z0 + sz * a + rz * b)
        n = int(Lp / 3.0)
        for i in range(n):
            a0, a1 = i * 3.0, (i + 1) * 3.0
            for k in range(4):                                 # tabuas: 4 faixas de 1,75 m, tons alternados
                b0, b1 = -W / 2 + k * (W / 4), -W / 2 + (k + 1) * (W / 4)
                col = COL['wood'] if (i + k) % 2 == 0 else COL['wood2']
                q = [PP(a0, b0, deck), PP(a1, b0, deck), PP(a1, b1, deck), PP(a0, b1, deck)]
                self.g.quad(WOOD, q, col, None); 
            self.polys.append(('pier', [(PP(a0, -W / 2, 0)[0], PP(a0, -W / 2, 0)[2]), (PP(a1, -W / 2, 0)[0], PP(a1, -W / 2, 0)[2]), (PP(a1, W / 2, 0)[0], PP(a1, W / 2, 0)[2]), (PP(a0, W / 2, 0)[0], PP(a0, W / 2, 0)[2])]))
            # vigas sob o deck e corrimao
            if i % 2 == 0:
                for sg in (-1, 1):
                    scenery.bar(self.B, PP(a0, sg * (W / 2 - 0.05), deck + 1.0), PP(a1 + 3.0, sg * (W / 2 - 0.05), deck + 1.0), 0.08, COL['rail'], METAL)
        for i in range(0, int(Lp / 4.5) + 1):
            a = i * 4.5
            for sg in (-1, 1):
                px, pz = PP(a, sg * (W / 2 - 0.05), 0)[0], PP(a, sg * (W / 2 - 0.05), 0)[2]
                self.B.cyl(px, pz, 0.05, deck, deck + 1.05, COL['rail'], 6)
                # estacas de madeira ate o fundo
                bot = min(self.sample(px, pz), -0.5) - 1.0
                self.B.box(px, pz, 0.45, 0.45, bot, deck - 0.05, COL['wood2'], WOOD, False, False)
        # luminarias e bancos
        for i in range(1, int(Lp / 22) + 1):
            a = i * 22.0
            for sg in (-1, 1):
                px, pz = PP(a, sg * (W / 2 - 0.3), 0)[0], PP(a, sg * (W / 2 - 0.3), 0)[2]
                self.B.cyl(px, pz, 0.07, deck, deck + 4.2, COL['lamp'], 8); self.B.box(px, pz, 0.5, 0.5, deck + 4.1, deck + 4.3, rgb('#FFF0B8'), PLAIN, True, False)
                self.items['lamps'].append({'x': round(px, 2), 'z': round(pz, 2), 'y': deck, 'pier': True})
        for i in range(1, int(Lp / 34) + 1):
            a = i * 34.0 + 5
            bx, bz = PP(a, W / 2 - 0.9, 0)[0], PP(a, W / 2 - 0.9, 0)[2]
            self.B.box(bx, bz, 1.5, 0.5, deck + 0.35, deck + 0.50, COL['bench'], WOOD, True, False); self.B.box(bx, bz, 0.3, 0.3, deck, deck + 0.35, COL['iron'], PLAIN, True, False)
        # plataforma do fim (22 x 14) com gazebo
        a0, a1 = Lp, Lp + 16.0
        for k in range(7):
            for j in range(8):
                aa0, aa1 = a0 + j * 2.0, a0 + (j + 1) * 2.0; bb0, bb1 = -11 + k * 3.14, -11 + (k + 1) * 3.14
                col = COL['wood'] if (j + k) % 2 == 0 else COL['wood2']
                self.g.quad(WOOD, [PP(aa0, bb0, deck), PP(aa1, bb0, deck), PP(aa1, bb1, deck), PP(aa0, bb1, deck)], col, None)
        self.polys.append(('pier', [(PP(a0, -11, 0)[0], PP(a0, -11, 0)[2]), (PP(a1, -11, 0)[0], PP(a1, -11, 0)[2]), (PP(a1, 11, 0)[0], PP(a1, 11, 0)[2]), (PP(a0, 11, 0)[0], PP(a0, 11, 0)[2])]))
        for (aa, bb) in ((a0, -11), (a0, 11), (a1, -11), (a1, 11)):
            px, pz = PP(aa, bb, 0)[0], PP(aa, bb, 0)[2]; bot = min(self.sample(px, pz), -0.5) - 1.0
            self.B.box(px, pz, 0.5, 0.5, bot, deck + 3.0, COL['wood2'], WOOD, False, False)
        cx, cz = PP(a0 + 8.0, 0, 0)[0], PP(a0 + 8.0, 0, 0)[2]
        for sgx in (-1, 1):
            for sgz in (-1, 1): self.B.cyl(cx + sgx * 3.2, cz + sgz * 3.2, 0.12, deck, deck + 3.2, COL['rail'], 8)
        for q in range(4):          # telhado piramidal do gazebo
            ang0 = math.pi / 4 + q * math.pi / 2; ang1 = ang0 + math.pi / 2
            self.B.tri(ROOF, (cx + math.cos(ang0) * 4.2, deck + 3.1, cz + math.sin(ang0) * 4.2), (cx + math.cos(ang1) * 4.2, deck + 3.1, cz + math.sin(ang1) * 4.2), (cx, deck + 5.0, cz), (math.cos((ang0 + ang1) / 2), 0.6, math.sin((ang0 + ang1) / 2)), COL['roof'], None, True)
        # rampa de entrada (do calcadao ao deck): 6 m
        for i in range(6):
            y0 = YP + 0.06 + (deck - YP - 0.06) * i / 6.0; y1 = YP + 0.06 + (deck - YP - 0.06) * (i + 1) / 6.0
            self.g.quad(WOOD, [PP(-0.0 - 6 + i, -W / 2, y0), PP(-6 + i + 1, -W / 2, y1), PP(-6 + i + 1, W / 2, y1), PP(-6 + i, W / 2, y0)], COL['wood'], None)
        self.items['piers'].append({'x': round(x0, 2), 'z': round(z0, 2), 'dx': round(sx, 3), 'dz': round(sz, 3), 'len': round(Lp + 16.0, 1), 'w': W, 'deck': round(deck, 2)})
        self.stats['piers'] += 1

    def palm(self, f, o):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o
        self.B.cyl(x, z, 0.18, YP, YP + 0.2, COL['wall'], 8)
        self.items['palms'].append({'x': round(x, 2), 'z': round(z, 2), 'y': YP + 0.1, 'sp': 'palmeira', 'scale': round(self.rnd.uniform(0.9, 1.2), 2)})

    def lamp(self, f, o):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o
        self.B.cyl(x, z, 0.08, YP + 0.06, YP + 4.6, COL['lamp'], 8); self.B.box(x, z, 0.7, 0.3, YP + 4.5, YP + 4.7, rgb('#FFF0B8'), PLAIN, True, False)
        self.items['lamps'].append({'x': round(x, 2), 'z': round(z, 2), 'y': YP + 0.06})

    def bench(self, f, o):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o
        t = (f['tx'], f['tz']); n = (f['nx'], f['nz'])
        c4 = [(x - t[0] * 0.9 - n[0] * 0.25, z - t[1] * 0.9 - n[1] * 0.25), (x + t[0] * 0.9 - n[0] * 0.25, z + t[1] * 0.9 - n[1] * 0.25), (x + t[0] * 0.9 + n[0] * 0.25, z + t[1] * 0.9 + n[1] * 0.25), (x - t[0] * 0.9 + n[0] * 0.25, z - t[1] * 0.9 + n[1] * 0.25)]
        self.B.obox_pts(c4, YP + 0.4, YP + 0.52, COL['bench'], WOOD, True, False)
        for sg in (-1, 1): self.B.box(x + t[0] * 0.7 * sg, z + t[1] * 0.7 * sg, 0.15, 0.4, YP + 0.06, YP + 0.4, COL['iron'], PLAIN, True, False)
        self.items['benches'].append({'x': round(x, 2), 'z': round(z, 2), 'nx': round(-n[0], 3), 'nz': round(-n[1], 3)})

    def kiosk(self, f, o, idx):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o
        yb = self.sample(x, z); t = (f['tx'], f['tz']); n = (f['nx'], f['nz']); S = 2.4
        col = self.rnd.choice([rgb('#F2E8D0'), rgb('#9ED8D8'), rgb('#F4B6A0'), rgb('#C8E0A0')])
        c4 = [(x - t[0] * S - n[0] * S, z - t[1] * S - n[1] * S), (x + t[0] * S - n[0] * S, z + t[1] * S - n[1] * S), (x + t[0] * S + n[0] * S, z + t[1] * S + n[1] * S), (x - t[0] * S + n[0] * S, z - t[1] * S + n[1] * S)]
        self.B.obox_pts(c4, yb, yb + 2.6, col, PLAIN, False, False)
        # balcao frontal (para o mar) e telhado de palha piramidal
        cxx, czz = x - n[0] * (S + 0.5), z - n[1] * (S + 0.5)
        c2 = [(cxx - t[0] * S * 0.8 - n[0] * 0.3, czz - t[1] * S * 0.8 - n[1] * 0.3), (cxx + t[0] * S * 0.8 - n[0] * 0.3, czz + t[1] * S * 0.8 - n[1] * 0.3), (cxx + t[0] * S * 0.8 + n[0] * 0.3, czz + t[1] * S * 0.8 + n[1] * 0.3), (cxx - t[0] * S * 0.8 + n[0] * 0.3, czz - t[1] * S * 0.8 + n[1] * 0.3)]
        self.B.obox_pts(c2, yb, yb + 1.05, rgb('#8B6B47'), WOOD, True, False)
        R = S * 1.9
        for q in range(4):
            a0 = math.pi / 4 + q * math.pi / 2; a1 = a0 + math.pi / 2
            P0 = (x + (math.cos(a0) * t[0] + math.sin(a0) * n[0]) * R, yb + 2.5, z + (math.cos(a0) * t[1] + math.sin(a0) * n[1]) * R)
            P1 = (x + (math.cos(a1) * t[0] + math.sin(a1) * n[0]) * R, yb + 2.5, z + (math.cos(a1) * t[1] + math.sin(a1) * n[1]) * R)
            self.B.tri(ROOF, P0, P1, (x, yb + 4.4, z), (math.cos((a0 + a1) / 2), 0.7, math.sin((a0 + a1) / 2)), COL['roof'], None, True)
        # mesas e guarda-sois
        for j in (-1, 0, 1):
            tx_, tz_ = cxx - n[0] * 3.0 + t[0] * j * 3.0, czz - n[1] * 3.0 + t[1] * j * 3.0
            self.B.cyl(tx_, tz_, 0.55, yb + 0.7, yb + 0.76, rgb('#F5F5F5'), 8); self.B.cyl(tx_, tz_, 0.05, yb, yb + 0.7, COL['iron'], 6)
        self.items['kiosks'].append({'x': round(x, 2), 'z': round(z, 2), 'nx': round(-n[0], 3), 'nz': round(-n[1], 3), 'y': round(yb, 2)})

    def tower(self, f, o):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o; yb = self.sample(x, z)
        for sx_ in (-1, 1):
            for sz_ in (-1, 1): self.B.cyl(x + sx_ * 1.0, z + sz_ * 1.0, 0.09, yb, yb + 3.1, COL['towerW'], 6)
        self.B.box(x, z, 3.0, 3.0, yb + 3.1, yb + 5.4, COL['towerR'], PLAIN, True, False)
        self.B.box(x, z, 3.3, 3.3, yb + 5.4, yb + 5.6, COL['towerW'], PLAIN, True, False)
        self.B.cyl(x + 1.3, z + 1.3, 0.04, yb + 5.6, yb + 7.6, COL['iron'], 6)
        self.B.quad(PLAIN, [(x + 1.3, yb + 7.0, z + 1.3), (x + 2.5, yb + 7.0, z + 1.3), (x + 2.5, yb + 7.6, z + 1.3), (x + 1.3, yb + 7.6, z + 1.3)], (0, 0, -1), rgb('#E53935'), None, True)
        self.items['towers'].append({'x': round(x, 2), 'z': round(z, 2), 'y': round(yb, 2)})

    def court(self, f, o):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o; yb = self.sample(x, z); t = (f['tx'], f['tz'])
        for sg in (-1, 1):
            self.B.cyl(x + t[0] * 4.5 * sg, z + t[1] * 4.5 * sg, 0.06, yb, yb + 2.4, COL['iron'], 6)
        self.B.quad(PLAIN, [(x - t[0] * 4.5, yb + 1.5, z - t[1] * 4.5), (x + t[0] * 4.5, yb + 1.5, z + t[1] * 4.5), (x + t[0] * 4.5, yb + 2.4, z + t[1] * 4.5), (x - t[0] * 4.5, yb + 2.4, z - t[1] * 4.5)], (f['nx'], 0, f['nz']), COL['net'], None, True)
        self.B.quad(PLAIN, [(x + t[0] * 4.5, yb + 1.5, z + t[1] * 4.5), (x - t[0] * 4.5, yb + 1.5, z - t[1] * 4.5), (x - t[0] * 4.5, yb + 2.4, z - t[1] * 4.5), (x + t[0] * 4.5, yb + 2.4, z + t[1] * 4.5)], (-f['nx'], 0, -f['nz']), COL['net'], None, True)
        self.items['courts'].append({'x': round(x, 2), 'z': round(z, 2), 'tx': round(t[0], 3), 'tz': round(t[1], 3)})

    def shower(self, f, o):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o; yb = self.sample(x, z)
        self.B.cyl(x, z, 0.05, yb, yb + 2.4, COL['shower'], 6); self.B.box(x, z, 0.5, 0.5, yb, yb + 0.1, COL['wall'], PLAIN, True, False)
        self.B.cyl(x, z, 0.14, yb + 2.35, yb + 2.45, COL['shower'], 8)
        self.items['showers'].append({'x': round(x, 2), 'z': round(z, 2), 'y': round(yb, 2)})

    def umbrella(self, f, o):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o; yb = self.sample(x, z)
        if yb < 0.3: return
        col = UMB[self.rnd.randrange(len(UMB))]
        self.B.cyl(x, z, 0.03, yb, yb + 2.0, COL['iron'], 5)
        for q in range(6):
            a0 = q * math.pi / 3; a1 = a0 + math.pi / 3
            self.B.tri(PLAIN, (x + math.cos(a0) * 1.1, yb + 1.85, z + math.sin(a0) * 1.1), (x + math.cos(a1) * 1.1, yb + 1.85, z + math.sin(a1) * 1.1), (x, yb + 2.2, z), (0, 1, 0), col if q % 2 == 0 else COL['white'], None, True)
        self.items['umbrellas'].append({'x': round(x, 2), 'z': round(z, 2)})

    def access_paths(self):
        """calcada de acesso da travessia da avenida ate o calcadao (corta a faixa de palmeiras)"""
        out = []
        for (x, z) in getattr(self.g, 'xw_beach', []):
            D = float(self.geo.Dsea[self.geo.idx(x, z)])
            if not (50 < D < 68): continue
            gx, gz = self.grad(x, z); sx, sz = norm(-gx, -gz); tx, tz = -sz, sx
            p0 = (x + sx * 14.0, z + sz * 14.0); p1 = (x + sx * 19.0, z + sz * 19.0)
            y0 = self.sample(*p0) + 0.27; y1 = YP + 0.06
            W = 2.4
            q = [(p0[0] - tx * W, y0, p0[1] - tz * W), (p0[0] + tx * W, y0, p0[1] + tz * W), (p1[0] + tx * W, y1, p1[1] + tz * W), (p1[0] - tx * W, y1, p1[1] - tz * W)]
            self.g.quad(PAVER, q, COL['wave1'], 'prom')
            out.append({'x': round(x, 2), 'z': round(z, 2), 'sx': round(sx, 3), 'sz': round(sz, 3)})
        self.items['paths'] = out
        return out

    def build(self):
        self.access_paths()
        for i, ln in enumerate(self.lines): self.build_line(ln, i)
        self.g.layers.extend(self.polys)
        return self
