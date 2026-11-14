"""ETAPA C: chao da cidade (asfalto, guias, calcadas, canteiros, faixas, cruzamentos, cercas, muros, pontes) -> malha assada (formato SUB1).
Convencao do motor: Y do asfalto = Y da rua + ROADY (0,12 m); guia/calcada +0,15 sobre o asfalto; decals +0,02 (o motor NAO tem polygonOffset)."""
import math, os, sys, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen-bairro'))
from bake import Bake, rgb, shade, mixc, PLAIN, TILE, STONE, GRASS, PAVER, METAL
from plan import *
import terrain_final as T
import scenery

ASPHALT = 15
ROADY = 0.12; CURB_H = 0.15; SW_Y = ROADY + CURB_H; VERGE_Y = SW_Y - 0.05; MARK_Y = ROADY + 0.02
SEC = {0: dict(inner=2.0, asph=11.5, half=15.8, R=8.0), 1: dict(inner=0.0, asph=6.0, half=10.0, R=6.0), 2: dict(inner=0.0, asph=5.0, half=7.5, R=5.0)}
COL = {'asph': rgb('#4A4B50'), 'asph2': rgb('#55565B'), 'curb': rgb('#B8B5AD'), 'white': rgb('#F2F2F2'), 'yellow': rgb('#F5C518'), 'grass': rgb('#6FA84A'),
       'brick': rgb('#9C4A35'), 'brick2': rgb('#B56B4A'), 'conc': rgb('#C9C6BE'), 'conc2': rgb('#BDB9B0'), 'sand': rgb('#E4D4B4'), 'sand2': rgb('#D6C39C'), 'tact': rgb('#C9A24A'),
       'soil': rgb('#5A4332'), 'iron': rgb('#2A2C30'), 'rail': rgb('#9AA0A6'), 'wall': rgb('#A29B8D'), 'wall2': rgb('#8F887A'), 'bridge': rgb('#C4BFB6'), 'under': rgb('#8A8580'),
       'lamp': rgb('#2B2E33'), 'orange': rgb('#C0361B'), 'orange2': rgb('#A82B14'), 'tunnel': rgb('#2A2A2E'), 'conc3': rgb('#D2CEC4')}

def norm(dx, dz):
    l = math.hypot(dx, dz) or 1e-9
    return dx / l, dz / l

def lerp(a, b, t): return a + (b - a) * t

def compute_all_cuts(city, geo):
    """comprimento do cruzamento (corte) de cada ponta de rua; so depende da geometria no plano"""
    gr = Ground.__new__(Ground)
    gr.c = city; gr.geo = geo; gr.yn = [0.0] * len(city.nodes); gr.hf = None
    gr.profiles = []
    for e in city.edges:
        gr.profiles.append(None if e['kind'] == 'redbridge' else [(p[0], p[1], 0.0) for p in e['p']])
    gr.arms = {}; gr.layers = []; gr.stats = {}
    gr.rounds = {r['node']: r['r'] for r in city.rounds}
    gr.tan_ov = {}
    gr.build_arms()
    out = {}
    for ni in gr.arms:
        gr.compute_cuts(ni)
        for a in gr.arms[ni]: out[(a['k'], a['end'])] = float(a['cut'])
    return out

class Ground:
    def __init__(self, city, geo, hf, ynode):
        self.c = city; self.geo = geo; self.hf = hf; self.yn = ynode
        self.B = Bake(); self.layers = []            # (layer, [(x,z),...]) para validar/prever
        self.profiles = []
        self.stats = {'quads': 0, 'junctions': 0, 'short_edges': 0, 'guard_m': 0.0, 'wall_m': 0.0}
        self.fronts = []                              # linhas de frente de lote (para a Etapa D)
        self.arms = {}
        self.rounds = {r['node']: r['r'] for r in city.rounds}
        self.xw_centers = []
        self.tan_ov = {}
        self.build_profiles()
        self.build_arms()

    # ------------------------------------------------------------ utilitarios
    def build_profiles(self):
        for k, e in enumerate(self.c.edges):
            pp = T.profile_pts(e, self.yn[e['a']], self.yn[e['b']]) if e['kind'] != 'redbridge' else None
            self.profiles.append(pp)

    def at(self, k, s):
        pp = self.profiles[k]; acc = 0.0
        for a, b in zip(pp, pp[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if acc + L >= s or b is pp[-1]:
                f = min(max((s - acc) / (L or 1), 0), 1)
                dx, dz = norm(b[0] - a[0], b[1] - a[1])
                return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, dx, dz
            acc += L
        a = pp[-1]; return a[0], a[1], a[2], 1.0, 0.0

    def elen(self, k):
        pp = self.profiles[k]; return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pp, pp[1:]))

    def zone(self, x, z):
        j, i = self.geo.idx(x, z)
        h = self.geo.height(x, z); D = float(self.geo.D[j, i]); sl = self.geo.slope_at(x, z)
        if z > 2300 and float(self.geo.Dsea[j, i]) < 260: return 'orla'
        if math.hypot(x - LAGOON[0], z - LAGOON[1]) < 720 and h < 16: return 'centro'
        if sl > 0.12 or h > 38: return 'colina'
        return 'res'

    def poly(self, layer, pts): self.layers.append((layer, pts))

    def quad(self, mat, p, col, layer=None, lit=True, n=(0, 1, 0)):
        self.B.quad(mat, p, n, col, None, lit); self.stats['quads'] += 1
        if layer: self.poly(layer, [(q[0], q[2]) for q in p])

    # ------------------------------------------------------------ bracos por no
    def build_arms(self):
        for k, e in enumerate(self.c.edges):
            if e['kind'] == 'redbridge': continue
            for end, ni in (('a', e['a']), ('b', e['b'])):
                L = self.elen(k); s = 0.0 if end == 'a' else L
                s2 = min(12.0, L * 0.5) if end == 'a' else max(L - 12.0, L * 0.5)
                x0, z0, y0, _, _ = self.at(k, s); x1, z1, y1, _, _ = self.at(k, s2)
                dx, dz = norm(x1 - x0, z1 - z0)
                self.arms.setdefault(ni, []).append({'k': k, 'end': end, 'd': (dx, dz), 'lvl': e['lvl'], 'kind': e['kind'], 'ang': math.atan2(dz, dx)})
        for ni in self.arms: self.arms[ni].sort(key=lambda a: a['ang'])

    # ------------------------------------------------------------ cantos
    def frame(self, a):
        """posicao e normal (direita de quem sai do no) do corte real do braco"""
        L = self.elen(a['k']); s = a['cut'] if a['end'] == 'a' else L - a['cut']
        x, z, y, tx, tz = self.at(a['k'], min(max(s, 0.0), L))
        xa, za, _, _, _ = self.at(a['k'], max(s - 3, 0)); xb, zb, _, _, _ = self.at(a['k'], min(s + 3, L))
        tx, tz = norm(xb - xa, zb - za)
        if a['end'] == 'b': tx, tz = -tx, -tz
        return (x, z, y, -tz, tx)

    def outer_corner(self, ai, aj, hi, hj):
        di, dj = ai['d'], aj['d']; ri = (-di[1], di[0]); rj = (-dj[1], dj[0])
        bx = -(ri[0] * hi + rj[0] * hj); bz = -(ri[1] * hi + rj[1] * hj)
        det = -(di[0] * dj[1] - di[1] * dj[0])
        if abs(det) < 1e-6: return None
        si = (-bx * dj[1] + dj[0] * bz) / det
        px, pz = di[0] * si + ri[0] * hi, di[1] * si + ri[1] * hi
        lim = 1.9 * max(hi, hj); r = math.hypot(px, pz)
        if r > lim: px, pz = px / r * lim, pz / r * lim            # esquina cortada (miter limitado)
        return (px, pz)

    def corner(self, ai, aj, hi, hj, R):
        """ponto de encontro das bordas de dois bracos + comprimento de tangente do arredondamento; None se quase colineares"""
        di, dj = ai['d'], aj['d']
        gap = (aj['ang'] - ai['ang']) % (2 * math.pi)
        if gap >= math.pi - 0.14 or gap < 0.10: return None
        ri = (-di[1], di[0]); rj = (-dj[1], dj[0])
        bx = -(ri[0] * hi + rj[0] * hj); bz = -(ri[1] * hi + rj[1] * hj)
        cr = di[0] * dj[1] - di[1] * dj[0]
        det = -cr
        if abs(det) < 1e-6: return None
        si = (-bx * dj[1] + dj[0] * bz) / det; sj = (di[0] * bz - di[1] * bx) / det
        t = R / math.tan(gap / 2)
        t = min(t, 24.0)
        return {'si': si, 'sj': sj, 't': t, 'gap': gap}

    def bulb_blocked(self, ni, a, Rb):
        """o bulbo de retorno (+calcada) bateria em outra rua?"""
        nx, nz = self.c.nodes[ni][:2]
        for k, e in enumerate(self.c.edges):
            if k == a['k'] or e['kind'] == 'redbridge': continue
            for p, q in zip(e['p'], e['p'][1:]):
                L = math.hypot(q[0] - p[0], q[1] - p[1]) or 1e-9
                for t in np.linspace(0, 1, max(2, int(L / 4))):
                    x, z = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
                    h = SEC[min(e['lvl'], 2)]['half']
                    if math.hypot(x - nx, z - nz) < Rb + 2.6 + h * 0.6: return True
        return False

    def compute_cuts(self, ni):
        arms = self.arms[ni]; n = len(arms)
        nx, nz = self.c.nodes[ni][:2]
        for a in arms:
            sec = SEC[min(a['lvl'], 2)]; a['a'] = sec['asph']; a['h'] = sec['half']; a['R'] = sec['R']
            a['cut'] = 1.0
        if ni in self.rounds and n >= 3:
            Ro = self.rounds[ni]
            for a in arms: a['cut'] = math.sqrt(max(Ro * Ro - a['h'] * a['h'] * 0.0 - a['a'] ** 2, 1.0)) + 0.4; a['round'] = Ro
            return None
        if n == 2 and ni not in self.rounds:
            a1, a2 = arms; d1, d2 = a1['d'], a2['d']
            if a1['lvl'] == a2['lvl'] and a1['kind'] == a2['kind'] and d1[0] * d2[0] + d1[1] * d2[1] < -0.82:
                # curva suave da mesma rua: sem cruzamento; as duas pontas dividem a mesma normal (bissetriz) e o canteiro continua
                tx, tz = norm(d2[0] - d1[0], d2[1] - d1[1])
                for a, sgn in ((a1, -1), (a2, 1)):
                    out = (tx * sgn, tz * sgn)                                  # sentido para fora do no ao longo deste braco
                    self.tan_ov[(a['k'], a['end'])] = out if a['end'] == 'a' else (-out[0], -out[1])
                    a['cut'] = 0.0; a['merge'] = True
                return None
        if n == 1:
            a = arms[0]; kind = self.c.legit.get(ni) or ('lookout' if ni in self.c.lookouts else 'cais')
            a['cut'] = 0.5; a['bulb'] = kind
            if kind == 'lookout':                                   # a rua segue reta para o tabuleiro da ponte (sem retorno redondo)
                a['cut'] = 0.0; return None
            if kind in ('bolsao', 'lookout') and self.bulb_blocked(ni, a, 11.0 if kind == 'bolsao' else 12.5): a['bulb'] = 'cais'; kind = 'cais'
            if kind in ('bolsao', 'lookout'):
                Rb = 11.0 if kind == 'bolsao' else 12.5; a['Rb'] = Rb
                a['cut'] = math.sqrt(max(Rb * Rb - a['a'] ** 2, 1))
            return None
        info = []
        for idx in range(n):
            ai = arms[idx]; aj = arms[(idx + 1) % n]
            if n == 2 and idx == 1: gapok = True
            res = {}
            for nm, (hi, hj, R) in (('a', (ai['a'], aj['a'], ai['R'])), ('c', (ai['a'] + 0.2, aj['a'] + 0.2, ai['R'] + 0.2)), ('o', (ai['h'], aj['h'], ai['R'] + (ai['h'] - ai['a'])))):
                cr = self.corner(ai, aj, hi, hj, R)
                res[nm] = cr
                if cr:
                    ai['cut'] = max(ai['cut'], cr['si'] + cr['t'] + 0.3); aj['cut'] = max(aj['cut'], cr['sj'] + cr['t'] + 0.3)
            info.append(res)
        for a in arms: a['cut'] = min(a['cut'], 60.0)
        return info

    def junction(self, ni):
        arms = self.arms[ni]; n = len(arms)
        nx, nz = self.c.nodes[ni][:2]; ny = self.yn[ni]
        if n == 2 and arms[0].get('merge'): return
        self.stats['junctions'] += 1
        if n == 1:
            a = arms[0]
            if a.get('bulb') == 'lookout': self.lookout_gate(ni, a)
            elif a.get('bulb') in ('bolsao', 'lookout'): self.bulb(ni, a, a['Rb'], a['bulb'])
            else: self.cais_cap(ni, a)
            return
        if ni in self.rounds and n >= 3:
            self.roundabout(ni, self.rounds[ni]); return
        if arms[0].get('merge'): return
        info = self.infos[ni]
        # monta os contornos de cada canto
        center = (nx, nz, ny)
        poly_a = []                           # contorno do asfalto
        for idx in range(n):
            ai = arms[idx]; aj = arms[(idx + 1) % n]; res = info[idx]
            di, dj = ai['d'], aj['d']; ri = (-di[1], di[0]); rj = (-dj[1], dj[0])
            fi = self.frame(ai); fj = self.frame(aj)
            def side(nm, hi, hj, R, samples=7):
                cr = res.get(nm)
                pi_ = (fi[0] + fi[3] * hi, fi[1] + fi[4] * hi)                 # ponto REAL do corte (segue a curvatura da rua)
                pj_ = (fj[0] - fj[3] * hj, fj[1] - fj[4] * hj)
                if not cr:
                    gap = (aj['ang'] - ai['ang']) % (2 * math.pi)
                    if math.pi + 0.14 < gap < 2 * math.pi - 0.10:              # canto externo convexo: esquina viva (cobre o no)
                        oc = self.outer_corner(ai, aj, hi, hj)
                        if oc: return [pi_, (nx + oc[0], nz + oc[1]), pj_]
                    return [pi_, pj_]
                P = (nx + di[0] * cr['si'] + ri[0] * hi, nz + di[1] * cr['si'] + ri[1] * hi)
                T1 = (P[0] + di[0] * cr['t'], P[1] + di[1] * cr['t']); T2 = (P[0] + dj[0] * cr['t'], P[1] + dj[1] * cr['t'])
                out = [pi_, T1]
                for q in range(1, samples):
                    t = q / samples; u = 1 - t
                    out.append((u * u * T1[0] + 2 * u * t * P[0] + t * t * T2[0], u * u * T1[1] + 2 * u * t * P[1] + t * t * T2[1]))
                return out + [T2, pj_]
            ai['_side'] = ai.get('_side', {})
            res['A'] = side('a', ai['a'], aj['a'], ai['R']); res['C'] = side('c', ai['a'] + 0.2, aj['a'] + 0.2, ai['R'] + 0.2)
            res['O'] = side('o', ai['h'], aj['h'], ai['R'] + (ai['h'] - ai['a']))
            # igualar quantidades de pontos para as faixas (calcada)
            m = max(len(res['C']), len(res['O']))
            for key in ('C', 'O'):
                pts = res[key]
                if len(pts) < m:       # lado reto: reamostra linearmente
                    res[key] = [(lerp(pts[0][0], pts[-1][0], q / (m - 1)), lerp(pts[0][1], pts[-1][1], q / (m - 1))) for q in range(m)] if len(pts) == 2 else pts + [pts[-1]] * (m - len(pts))
            poly_a += res['A']
        # asfalto: leque a partir do centro
        yc = ny + ROADY
        col = COL['asph']
        for q in range(len(poly_a)):
            p, r = poly_a[q], poly_a[(q + 1) % len(poly_a)]
            if math.hypot(p[0] - r[0], p[1] - r[1]) < 1e-3: continue
            self.B.m = None
            self.quad(ASPHALT, [(nx, yc, nz), (p[0], yc + 0.0, p[1]), (r[0], yc + 0.0, r[1]), (nx, yc, nz)], col, None)
        self.poly('asphalt', poly_a)
        # guia + calcada de cada canto
        beach_node = any(self.is_beach(a['k']) for a in arms)
        d0 = float(self.geo.Dsea[self.geo.idx(nx, nz)])
        for idx in range(n):
            res = info[idx]
            A, C, O = res['A'], res['C'], res['O']
            if beach_node and self.is_beach(arms[idx]['k']) and self.is_beach(arms[(idx + 1) % n]['k']):
                mo = O[len(O) // 2]
                if float(self.geo.Dsea[self.geo.idx(*mo)]) < d0: continue        # canto voltado para o mar: a orla continua ali
            if len(A) == len(C):
                for q in range(len(A) - 1):
                    self.quad(PAVER, [(A[q][0], yc + CURB_H, A[q][1]), (A[q + 1][0], yc + CURB_H, A[q + 1][1]), (C[q + 1][0], yc + CURB_H, C[q + 1][1]), (C[q][0], yc + CURB_H, C[q][1])], COL['curb'], 'curb')
                    # face da guia voltada para a rua
                    self.B.quad(PLAIN, [(A[q][0], yc, A[q][1]), (A[q + 1][0], yc, A[q + 1][1]), (A[q + 1][0], yc + CURB_H, A[q + 1][1]), (A[q][0], yc + CURB_H, A[q][1])],
                                (-(A[q + 1][1] - A[q][1]), 0, (A[q + 1][0] - A[q][0])), COL['curb'], None, True)
            m = len(C)
            zone = self.zone(nx, nz)
            sc = {'centro': COL['brick'], 'res': COL['conc'], 'colina': COL['conc2'], 'orla': COL['sand']}[zone]
            for q in range(m - 1):
                self.quad(PAVER, [(C[q][0], yc + CURB_H, C[q][1]), (C[q + 1][0], yc + CURB_H, C[q + 1][1]), (O[q + 1][0], yc + CURB_H, O[q + 1][1]), (O[q][0], yc + CURB_H, O[q][1])], sc, 'sidewalk')
            # saia externa (esconde o degrau ate o terreno)
            for q in range(m - 1):
                self.B.quad(PLAIN, [(O[q][0], yc + CURB_H - 0.45, O[q][1]), (O[q + 1][0], yc + CURB_H - 0.45, O[q + 1][1]), (O[q + 1][0], yc + CURB_H, O[q + 1][1]), (O[q][0], yc + CURB_H, O[q][1])],
                            ((O[q + 1][1] - O[q][1]), 0, -(O[q + 1][0] - O[q][0])), COL['conc2'], None, True)
            if len(O) >= 2: self.fronts.append({'node': ni, 'zone': zone, 'pts': [[round(p[0], 2), round(p[1], 2)] for p in O], 'y': round(ny + SW_Y, 2), 'kind': 'corner'})
        # faixas de pedestre e linha de retencao (so em cruzamentos de 3+ bracos)
        if n >= 3:
            for a in arms:
                if a.get('xw'): self.crosswalk(ni, a, nx, nz, yc)
        self.cuts_done = True

    def plan_crosswalks(self):
        """decide ONDE ha faixa de pedestre: so em cruzamentos de 3+ bracos, 1 por braco, trecho com >= 45 m livres e nunca a menos de 40 m de outra faixa"""
        cand = []
        for ni, arms in self.arms.items():
            if len(arms) < 3: continue
            if all(x['lvl'] >= 2 for x in arms): continue            # cruzamento so de ruas locais: sem faixa (so PARE)
            for a in arms:
                if a['kind'] == 'bridge': continue
                e = self.c.edges[a['k']]; oth = e['b'] if a['end'] == 'a' else e['a']
                oc = max([x['cut'] for x in self.arms.get(oth, []) if x['k'] == a['k']] or [0])
                L = self.elen(a['k'])
                if L < a['cut'] + oc + (30.0 if self.c.edges[a['k']].get('protect') else 45.0): continue
                s = a['cut'] + 2.5 if a['end'] == 'a' else L - a['cut'] - 2.5
                x, z, _, _, _ = self.at(a['k'], s)
                cand.append((a['lvl'] - (1 if self.c.edges[a['k']].get('protect') and a['lvl'] == 0 else 0), -len(arms), x, z, a))
        cand.sort(key=lambda t: (t[0], t[1]))                      # avenidas primeiro
        for lvl, _, x, z, a in cand:
            sp = 38.0 if (self.c.edges[a['k']].get('protect') and a['lvl'] == 0) else 60.0
            if any(math.hypot(x - cx, z - cz) < sp for cx, cz in self.xw_centers): continue
            a['xw'] = True; self.xw_centers.append((x, z))
            if self.c.edges[a['k']].get('protect'): self.xw_beach = getattr(self, 'xw_beach', []) + [(x, z)]

    def cais_cap(self, ni, a):
        """fim de rua na beira d'agua/cais: meio-fio atravessado, pracinha de calcada e balizas (nada de pista 'cortada')"""
        nx, nz = self.c.nodes[ni][:2]; yc = self.yn[ni] + ROADY
        d = a['d']; r = (-d[1], d[0]); h = a['h']; ap = a['a']
        zone = self.zone(nx, nz); sc = {'centro': COL['brick'], 'res': COL['conc'], 'colina': COL['conc2'], 'orla': COL['sand']}[zone]
        def P(s, o): return (nx + d[0] * s + r[0] * o, nz + d[1] * s + r[1] * o)
        # meio-fio transversal (0,3 m) e face voltada para a rua
        c0, c1, c2, c3 = P(0.5, -ap), P(0.5, ap), P(0.2, ap), P(0.2, -ap)
        self.quad(PAVER, [(c0[0], yc + CURB_H, c0[1]), (c1[0], yc + CURB_H, c1[1]), (c2[0], yc + CURB_H, c2[1]), (c3[0], yc + CURB_H, c3[1])], COL['curb'], 'curb')
        self.B.quad(PLAIN, [(c0[0], yc, c0[1]), (c1[0], yc, c1[1]), (c1[0], yc + CURB_H, c1[1]), (c0[0], yc + CURB_H, c0[1])], (d[0], 0, d[1]), COL['curb'], None, True)
        # pracinha atras do meio-fio (4,5 m) com a largura da rua + calcadas
        q0, q1, q2, q3 = P(0.2, -h), P(0.2, h), P(-4.5, h), P(-4.5, -h)
        self.quad(PAVER, [(q0[0], yc + CURB_H, q0[1]), (q1[0], yc + CURB_H, q1[1]), (q2[0], yc + CURB_H, q2[1]), (q3[0], yc + CURB_H, q3[1])], sc, 'sidewalk')
        for p0, p1, nv in ((q3, q2, (-d[0], 0, -d[1])), (q0, q3, (-r[0], 0, -r[1])), (q2, q1, (r[0], 0, r[1]))):
            self.B.quad(PLAIN, [(p0[0], yc + CURB_H - 0.45, p0[1]), (p1[0], yc + CURB_H - 0.45, p1[1]), (p1[0], yc + CURB_H, p1[1]), (p0[0], yc + CURB_H, p0[1])], nv, COL['conc2'], None, True)
        # balizas (bollards) na borda da agua
        for o in np.arange(-h + 1.0, h - 0.5, 2.4):
            bx, bz = P(-3.9, o); self.B.cyl(bx, bz, 0.11, yc + CURB_H, yc + CURB_H + 0.95, COL['iron'], 8)
        self.cais_info = getattr(self, 'cais_info', []) + [{'node': ni, 'x': nx, 'z': nz, 'dx': d[0], 'dz': d[1]}]

    def lookout_gate(self, ni, a):
        """a rua entra reta no tabuleiro da ponte vermelha (cenario): cancela listrada + barreiras de concreto 3 m a frente do fim da rua"""
        nx, nz = self.c.nodes[ni][:2]; yc = self.yn[ni] + ROADY
        d = a['d']; r = (-d[1], d[0]); out = (-d[0], -d[1])           # out = sentido da ponte
        cx, cz = nx + out[0] * 4.0, nz + out[1] * 4.0
        for sgn in (-1, 1):
            self.B.obox_pts([(cx + r[0] * (4.6 * sgn + o1) + d[0] * o2, cz + r[1] * (4.6 * sgn + o1) + d[1] * o2) for (o1, o2) in ((-1.4, -0.4), (1.4, -0.4), (1.4, 0.4), (-1.4, 0.4))], yc, yc + 0.85, COL['conc3'], PLAIN)
            self.B.cyl(cx + r[0] * 2.0 * sgn, cz + r[1] * 2.0 * sgn, 0.1, yc, yc + 1.25, COL['iron'], 8)
        for q in range(8):
            col = COL['white'] if q % 2 == 0 else COL['orange']
            u0, u1 = -2.0 + q * 0.5, -2.0 + (q + 1) * 0.5
            for fx, nrm in ((1, d), (-1, out)):
                self.B.quad(PLAIN, [(cx + r[0] * u0, yc + 1.05, cz + r[1] * u0), (cx + r[0] * u1, yc + 1.05, cz + r[1] * u1), (cx + r[0] * u1, yc + 1.25, cz + r[1] * u1), (cx + r[0] * u0, yc + 1.25, cz + r[1] * u0)][::fx], (nrm[0], 0, nrm[1]), col, None, True)
        self.cais_info = getattr(self, 'cais_info', []) + []

    def bulb(self, ni, a, Rb, kind):
        nx, nz = self.c.nodes[ni][:2]; yc = self.yn[ni] + ROADY
        d = a['d']; ang0 = math.atan2(d[1], d[0]); half = math.atan2(a['a'], a['cut'])
        pts = []
        steps = 18
        for q in range(steps + 1):
            t = ang0 + half + (2 * math.pi - 2 * half) * q / steps
            pts.append((nx + math.cos(t) * Rb, nz + math.sin(t) * Rb))
        for q in range(len(pts) - 1):
            self.quad(ASPHALT, [(nx, yc, nz), (pts[q][0], yc, pts[q][1]), (pts[q + 1][0], yc, pts[q + 1][1]), (nx, yc, nz)], COL['asph'])
        self.quad(ASPHALT, [(nx, yc, nz), (pts[-1][0], yc, pts[-1][1]), (pts[0][0], yc, pts[0][1]), (nx, yc, nz)], COL['asph'])      # fecha o triangulo da corda
        self.poly('asphalt', [(nx, nz)] + pts); self.poly('asphalt', [(nx, nz), pts[-1], pts[0]])
        # guia + calcada em arco; no mirante: cancela e blocos
        for q in range(len(pts) - 1):
            p, r = pts[q], pts[q + 1]
            for (r0, r1, col, layer, mat) in ((Rb, Rb + 0.2, COL['curb'], 'curb', PAVER), (Rb + 0.2, Rb + 2.4, COL['conc'] if kind == 'bolsao' else COL['conc3'], 'sidewalk', PAVER)):
                f0, f1 = r0 / Rb, r1 / Rb
                P0 = (nx + (p[0] - nx) * f0, nz + (p[1] - nz) * f0); P1 = (nx + (r[0] - nx) * f0, nz + (r[1] - nz) * f0)
                Q0 = (nx + (p[0] - nx) * f1, nz + (p[1] - nz) * f1); Q1 = (nx + (r[0] - nx) * f1, nz + (r[1] - nz) * f1)
                self.quad(mat, [(P0[0], yc + CURB_H, P0[1]), (P1[0], yc + CURB_H, P1[1]), (Q1[0], yc + CURB_H, Q1[1]), (Q0[0], yc + CURB_H, Q0[1])], col, layer)
        if kind == 'lookout':
            # cancela: barreira de concreto + 2 postes listrados + placa; a colisao e criada na Etapa I
            cx, cz = nx - d[0] * (Rb - 1.0), nz - d[1] * (Rb - 1.0); r = (-d[1], d[0])
            for sgn in (-1, 1):
                self.B.obox_pts([(cx + r[0] * (3 * sgn + o1) + d[0] * o2, cz + r[1] * (3 * sgn + o1) + d[1] * o2) for (o1, o2) in ((-1.2, -0.4), (1.2, -0.4), (1.2, 0.4), (-1.2, 0.4))], yc, yc + 0.85, COL['conc3'], PLAIN)
            self.B.cyl(cx + r[0] * 0.0, cz + r[1] * 0.0, 0.1, yc, yc + 1.2, COL['iron'], 8)
            for q in range(7):
                col = COL['white'] if q % 2 == 0 else COL['orange']
                u0, u1 = -2.0 + q * 0.55, -2.0 + (q + 1) * 0.55
                self.B.quad(PLAIN, [(cx + r[0] * u0, yc + 1.05, cz + r[1] * u0), (cx + r[0] * u1, yc + 1.05, cz + r[1] * u1), (cx + r[0] * u1, yc + 1.25, cz + r[1] * u1), (cx + r[0] * u0, yc + 1.25, cz + r[1] * u0)], (d[0], 0, d[1]), col, None, True)
                self.B.quad(PLAIN, [(cx + r[0] * u1, yc + 1.05, cz + r[1] * u1), (cx + r[0] * u0, yc + 1.05, cz + r[1] * u0), (cx + r[0] * u0, yc + 1.25, cz + r[1] * u0), (cx + r[0] * u1, yc + 1.25, cz + r[1] * u1)], (-d[0], 0, -d[1]), col, None, True)

    def roundabout(self, ni, Ro):
        arms = self.arms[ni]; n = len(arms)
        nx, nz = self.c.nodes[ni][:2]; ny = self.yn[ni]; yc = ny + ROADY
        W = 9.5; Ri = Ro - W
        zone = self.zone(nx, nz)
        sc = {'centro': COL['brick'], 'res': COL['conc'], 'colina': COL['conc2'], 'orla': COL['sand']}[zone]
        N = 56
        def P(r, ang): return (nx + math.cos(ang) * r, nz + math.sin(ang) * r)
        for q in range(N):
            a0, a1 = 2 * math.pi * q / N, 2 * math.pi * (q + 1) / N
            p = [P(Ri, a0), P(Ro, a0), P(Ro, a1), P(Ri, a1)]
            self.quad(ASPHALT, [(v[0], yc, v[1]) for v in p], COL['asph'], 'asphalt')
            # ilha central: grama + guia
            c0, c1 = P(Ri - 0.2, a0), P(Ri - 0.2, a1)
            self.quad(PAVER, [(P(Ri, a0)[0], yc + CURB_H, P(Ri, a0)[1]), (P(Ri, a1)[0], yc + CURB_H, P(Ri, a1)[1]), (c1[0], yc + CURB_H, c1[1]), (c0[0], yc + CURB_H, c0[1])], COL['curb'], 'island')
            self.B.quad(PLAIN, [(P(Ri, a0)[0], yc, P(Ri, a0)[1]), (P(Ri, a1)[0], yc, P(Ri, a1)[1]), (P(Ri, a1)[0], yc + CURB_H, P(Ri, a1)[1]), (P(Ri, a0)[0], yc + CURB_H, P(Ri, a0)[1])], (-math.cos((a0 + a1) / 2), 0, -math.sin((a0 + a1) / 2)), COL['curb'], None, True)
            self.B.tri(GRASS, (nx, yc + CURB_H - 0.05, nz), (c0[0], yc + CURB_H - 0.05, c0[1]), (c1[0], yc + CURB_H - 0.05, c1[1]), (0, 1, 0), COL['grass'], None, True)
            self.poly('island', [(nx, nz), c0, c1])
            # linha tracejada no meio do anel
            if q % 2 == 0:
                rm = (Ri + Ro) / 2
                self.quad(PLAIN, [(P(rm - 0.06, a0)[0], yc + 0.02, P(rm - 0.06, a0)[1]), (P(rm + 0.06, a0)[0], yc + 0.02, P(rm + 0.06, a0)[1]), (P(rm + 0.06, a1)[0], yc + 0.02, P(rm + 0.06, a1)[1]), (P(rm - 0.06, a1)[0], yc + 0.02, P(rm - 0.06, a1)[1])], COL['white'], 'mark')
        # guia + calcada externas, interrompidas onde as ruas entram
        gaps = []
        for a in arms:
            d = math.asin(min((a['a'] + 0.2) / (Ro + 0.2), 0.95)) + 0.02
            gaps.append((a['ang'] - d, a['ang'] + d))
        sw = max(2.0, 0.5 * sum(a['h'] - a['a'] for a in arms) / n - 0.2)
        for q in range(len(arms)):
            g0 = gaps[q][1]; g1 = gaps[(q + 1) % len(arms)][0]
            if g1 <= g0: g1 += 2 * math.pi
            m = max(4, int((g1 - g0) * Ro / 3.0))
            for t in range(m):
                a0 = g0 + (g1 - g0) * t / m; a1 = g0 + (g1 - g0) * (t + 1) / m
                P0, P1 = P(Ro, a0), P(Ro, a1); Q0, Q1 = P(Ro + 0.2, a0), P(Ro + 0.2, a1); S0, S1 = P(Ro + 0.2 + sw, a0), P(Ro + 0.2 + sw, a1)
                self.quad(PAVER, [(P0[0], yc + CURB_H, P0[1]), (P1[0], yc + CURB_H, P1[1]), (Q1[0], yc + CURB_H, Q1[1]), (Q0[0], yc + CURB_H, Q0[1])], COL['curb'], 'curb')
                self.B.quad(PLAIN, [(P0[0], yc, P0[1]), (P1[0], yc, P1[1]), (P1[0], yc + CURB_H, P1[1]), (P0[0], yc + CURB_H, P0[1])], (-math.cos((a0 + a1) / 2), 0, -math.sin((a0 + a1) / 2)), COL['curb'], None, True)
                self.quad(PAVER, [(Q0[0], yc + CURB_H, Q0[1]), (Q1[0], yc + CURB_H, Q1[1]), (S1[0], yc + CURB_H, S1[1]), (S0[0], yc + CURB_H, S0[1])], sc, 'sidewalk')
                self.B.quad(PLAIN, [(S0[0], yc + CURB_H - 0.45, S0[1]), (S1[0], yc + CURB_H - 0.45, S1[1]), (S1[0], yc + CURB_H, S1[1]), (S0[0], yc + CURB_H, S0[1])], (math.cos((a0 + a1) / 2), 0, math.sin((a0 + a1) / 2)), COL['conc2'], None, True)
            self.fronts.append({'node': ni, 'zone': zone, 'kind': 'round', 'pts': [[round(v[0], 2), round(v[1], 2)] for v in [P(Ro + 0.2 + sw, g0 + (g1 - g0) * t / 8) for t in range(9)]], 'y': round(ny + SW_Y, 2)})
        self.round_info = getattr(self, 'round_info', []) + [{'node': ni, 'x': nx, 'z': nz, 'Ro': Ro, 'Ri': Ri, 'y': ny}]
        for a in arms:
            if a.get('xw'): self.crosswalk(ni, a, nx, nz, yc)

    def crosswalk(self, ni, a, nx, nz, yc):
        """faixa zebra (barras ao longo do trafego) + linha de retencao + rampas tateis, alinhadas ao eixo REAL da rua naquele ponto"""
        L = self.elen(a['k']); half = a['a']
        s_mid = a['cut'] + 2.5 if a['end'] == 'a' else L - a['cut'] - 2.5
        x, z, y, _, _ = self.at(a['k'], s_mid)
        xa, za, _, _, _ = self.at(a['k'], max(s_mid - 3, 0)); xb, zb, _, _, _ = self.at(a['k'], min(s_mid + 3, L))
        tx, tz = norm(xb - xa, zb - za)
        d = (tx, tz) if a['end'] == 'a' else (-tx, -tz)          # sentido para fora do cruzamento
        r = (-d[1], d[0])
        ins = SEC[min(a['lvl'], 2)]['inner']
        yy = yc if abs(y + ROADY - yc) < 0.2 else y + ROADY
        if True:
            lo = -half + 0.8; hi = half - 0.5                         # faixa continua (o canteiro central foi aberto ate depois dela)
            for off in np.arange(lo, hi, 1.0):
                o = off
                cx, cz = x + r[0] * o, z + r[1] * o
                p = [(cx - r[0] * 0.25 - d[0] * 1.5, yy + 0.02, cz - r[1] * 0.25 - d[1] * 1.5), (cx + r[0] * 0.25 - d[0] * 1.5, yy + 0.02, cz + r[1] * 0.25 - d[1] * 1.5),
                     (cx + r[0] * 0.25 + d[0] * 1.5, yy + 0.02, cz + r[1] * 0.25 + d[1] * 1.5), (cx - r[0] * 0.25 + d[0] * 1.5, yy + 0.02, cz - r[1] * 0.25 + d[1] * 1.5)]
                self.quad(PLAIN, p, COL['white'], 'zebra')
        # linha de retencao (so na metade que ENTRA no cruzamento: lado esquerdo de quem sai, para a direita de quem chega)
        s1 = 3.6
        for sg in ((-1, 1) if ins > 0 else (1,)):
            lo = (ins + 0.4) if ins > 0 else 0.2; hi = half - 2.4 if ins > 0 else half - 2.4
            p = [(x + d[0] * s1 + r[0] * lo * sg, yy + 0.02, z + d[1] * s1 + r[1] * lo * sg), (x + d[0] * s1 + r[0] * hi * sg, yy + 0.02, z + d[1] * s1 + r[1] * hi * sg),
                 (x + d[0] * (s1 + 0.6) + r[0] * hi * sg, yy + 0.02, z + d[1] * (s1 + 0.6) + r[1] * hi * sg), (x + d[0] * (s1 + 0.6) + r[0] * lo * sg, yy + 0.02, z + d[1] * (s1 + 0.6) + r[1] * lo * sg)]
            if sg == 1 or ins > 0: self.quad(PLAIN, p, COL['white'], 'mark') if False else None
        # rampas tateis nas pontas da faixa (calcada)
        for sg in (-1, 1):
            cx, cz = x + r[0] * (half + 1.0) * sg, z + r[1] * (half + 1.0) * sg
            if self.is_beach(a['k']) and float(self.geo.Dsea[self.geo.idx(cx, cz)]) < float(self.geo.Dsea[self.geo.idx(x, z)]): continue   # lado do mar: patamar da orla
            hw = 0.75
            pp = [(cx - d[0] * 1.5 - r[0] * hw, yy + CURB_H + 0.02, cz - d[1] * 1.5 - r[1] * hw), (cx + d[0] * 1.5 - r[0] * hw, yy + CURB_H + 0.02, cz + d[1] * 1.5 - r[1] * hw),
                  (cx + d[0] * 1.5 + r[0] * hw, yy + CURB_H + 0.02, cz + d[1] * 1.5 + r[1] * hw), (cx - d[0] * 1.5 + r[0] * hw, yy + CURB_H + 0.02, cz - d[1] * 1.5 + r[1] * hw)]
            self.quad(PAVER, pp, COL['tact'], 'tact')

    # ------------------------------------------------------------ corpo das ruas
    def stations(self, k, s0, s1):
        pp = self.profiles[k]; L = self.elen(k)
        # pontos de quebra = vertices da polilinha + passos de ate 18 m
        acc = 0.0; breaks = [0.0]
        for a, b in zip(pp, pp[1:]):
            acc += math.hypot(b[0] - a[0], b[1] - a[1]); breaks.append(acc)
        ss = {s0, s1}
        for b in breaks:
            if s0 < b < s1: ss.add(b)
        ss = sorted(ss); out = []
        for u, v in zip(ss, ss[1:]):
            out.append(u); n = int((v - u) // 18)
            for q in range(1, n + 1): out.append(u + (v - u) * q / (n + 1))
        out.append(ss[-1])
        st = []
        for s in out:
            x, z, y, dx, dz = self.at(k, s)
            # tangente suavizada
            xa, za, _, _, _ = self.at(k, max(s - 3, 0)); xb, zb, _, _, _ = self.at(k, min(s + 3, L))
            tx, tz = norm(xb - xa, zb - za)
            if s <= 1e-6 and (k, 'a') in self.tan_ov: tx, tz = self.tan_ov[(k, 'a')]
            if s >= L - 1e-6 and (k, 'b') in self.tan_ov: tx, tz = self.tan_ov[(k, 'b')]
            st.append({'s': s, 'x': x, 'z': z, 'y': y, 'tx': tx, 'tz': tz, 'nx': -tz, 'nz': tx})
        return st

    def off(self, st, o): return (st['x'] + st['nx'] * o, st['z'] + st['nz'] * o)

    def strip(self, mat, col, stl, o0, o1, dy, layer=None, norm_up=True):
        for q in range(len(stl) - 1):
            a, b = stl[q], stl[q + 1]
            p0, p1, p2, p3 = self.off(a, o0), self.off(b, o0), self.off(b, o1), self.off(a, o1)
            self.quad(mat, [(p0[0], a['y'] + dy, p0[1]), (p1[0], b['y'] + dy, p1[1]), (p2[0], b['y'] + dy, p2[1]), (p3[0], a['y'] + dy, p3[1])], col, layer)

    def vwall(self, stl, o, y0off, y1off, col, face, mat=PLAIN):
        """parede vertical ao longo do corte (face=+1 normal para +n, -1 para -n)"""
        for q in range(len(stl) - 1):
            a, b = stl[q], stl[q + 1]
            p0, p1 = self.off(a, o), self.off(b, o)
            nvec = (a['nx'] * face, 0, a['nz'] * face)
            self.B.quad(mat, [(p0[0], a['y'] + y0off, p0[1]), (p1[0], b['y'] + y0off, p1[1]), (p1[0], b['y'] + y1off, p1[1]), (p0[0], a['y'] + y1off, p0[1])], nvec, col, None, True); self.stats['quads'] += 1

    def edge_body(self, k):
        e = self.c.edges[k]
        if e['kind'] == 'redbridge': return
        lvl = min(e['lvl'], 2); sec = SEC[lvl]
        la = max([a['cut'] for a in self.arms.get(e['a'], []) if a['k'] == k and a['end'] == 'a'] or [1.0])
        lb = max([a['cut'] for a in self.arms.get(e['b'], []) if a['k'] == k and a['end'] == 'b'] or [1.0])
        L = self.elen(k)
        if L - la - lb < 1.5: self.stats['short_edges'] += 1; return
        OV = 0.3                                             # a pista/calcada entra 0,3 m no cruzamento: sem frestas na emenda
        stl = self.stations(k, max(la - OV, 0.0), min(L - lb + OV, L))
        # braco com faixa de pedestre: canteiro central e linhas de faixa so comecam DEPOIS da faixa (5,6 m)
        xa_ = any(a.get('xw') for a in self.arms.get(e['a'], []) if a['k'] == k and a['end'] == 'a')
        xb_ = any(a.get('xw') for a in self.arms.get(e['b'], []) if a['k'] == k and a['end'] == 'b')
        ea = 5.6 if xa_ else 0.0; eb = 5.6 if xb_ else 0.0
        if L - la - lb - ea - eb < 4.0: ea = eb = 0.0
        stl_m = self.stations(k, la + ea, L - lb - eb) if (ea or eb) else stl
        mx, mz, _, _, _ = self.at(k, L / 2)
        zone = self.zone(mx, mz) if e['kind'] != 'bridge' else 'ponte'
        a_, h_, ins = sec['asph'], sec['half'], sec['inner']
        bridge = e['kind'] == 'bridge'
        # --- asfalto
        for sgn in ((1, -1) if ins > 0 else (0,)):
            if ins > 0: self.strip(ASPHALT, COL['asph'], stl, sgn * ins, sgn * a_, ROADY, 'asphalt')
            else: self.strip(ASPHALT, COL['asph'], stl, -a_, a_, ROADY, 'asphalt')
        # faixa de estacionamento levemente diferente (tom)
        for sgn in (1, -1):
            o0 = sgn * (a_ - (2.5 if lvl == 0 else 2.0 if lvl == 2 else 2.5)); self.strip(ASPHALT, COL['asph2'], stl, o0, sgn * a_, ROADY + 0.003, None)
        # --- canteiro central (avenida): termina antes da faixa de pedestre (passagem de pedestres)
        if ins > 0:
            if stl_m is not stl:
                if ea: self.strip(ASPHALT, COL['asph'], self.stations(k, max(la - OV, 0.0), la + ea), -ins, ins, ROADY, 'asphalt')
                if eb: self.strip(ASPHALT, COL['asph'], self.stations(k, L - lb - eb, min(L - lb + OV, L)), -ins, ins, ROADY, 'asphalt')
            self.strip(GRASS, COL['grass'], stl_m, -ins + 0.2, ins - 0.2, VERGE_Y - 0.0, 'median')
            for sgn in (1, -1):
                self.strip(PAVER, COL['curb'], stl_m, sgn * (ins - 0.2), sgn * ins, SW_Y, 'curb')
                self.vwall(stl_m, sgn * ins, ROADY, SW_Y, COL['curb'], -sgn)
                self.vwall(stl_m, sgn * (ins - 0.2), ROADY, SW_Y, COL['curb'], sgn)
        # --- guias, verge e calcadas dos dois lados
        sw_col, sw_col2 = {'centro': (COL['brick'], COL['conc']), 'res': (COL['conc'], COL['conc2']), 'colina': (COL['conc2'], COL['conc']), 'orla': (COL['sand'], COL['sand2']), 'ponte': (COL['bridge'], COL['conc'])}[zone]
        sea = self.sea_sign(k)
        for sgn in (1, -1):
            if sea and sgn == sea: continue                                 # lado do mar da Beira-Mar: vagas, jardim e calcadao (orla.py)
            # guia continua, exceto nos REBAIXOS das garagens das casas (Etapa D)
            lp_ = getattr(self.c, 'lotplan', None)
            gaps_ = sorted((lp_.driveways.get((k, sgn), []) if lp_ else []))
            rng_ = []; cur_ = max(la - OV, 0.0); end_ = min(L - lb + OV, L)
            for g0_, g1_ in gaps_:
                if g1_ <= cur_ or g0_ >= end_: continue
                if g0_ > cur_ + 0.2: rng_.append((cur_, g0_))
                cur_ = max(cur_, g1_)
            if end_ > cur_ + 0.2: rng_.append((cur_, end_))
            for ra_, rb_ in rng_:
                sub_ = self.stations(k, ra_, rb_)
                self.strip(PAVER, COL['curb'], sub_, sgn * a_, sgn * (a_ + 0.2), SW_Y, 'curb')
                self.vwall(sub_, sgn * a_, ROADY, SW_Y, COL['curb'], -sgn)
            o = a_ + 0.2
            if lvl == 0 and not bridge:                                      # AVENIDA: calcada larga ate o fim (com covas de arvore), sem canteiros de grama que parecem buracos
                self.strip(PAVER, sw_col2, stl, sgn * o, sgn * (o + 0.6), SW_Y, 'sidewalk'); self.strip(PAVER, sw_col, stl, sgn * (o + 0.6), sgn * h_, SW_Y, 'sidewalk')
            elif zone == 'res' and lvl == 2:                                  # faixa-jardim com arvore + calcada
                self.strip(PAVER, sw_col2, stl, sgn * o, sgn * (o + 0.6), SW_Y, 'sidewalk'); self.strip(PAVER, sw_col, stl, sgn * (o + 0.6), sgn * h_, SW_Y, 'sidewalk')   # calcada de concreto continua, sem faixa de grama
            elif zone == 'centro' and lvl <= 1:                              # faixa de concreto junto a guia + tijolo
                self.strip(PAVER, sw_col2, stl, sgn * o, sgn * (o + 0.6), SW_Y, 'sidewalk'); self.strip(PAVER, sw_col, stl, sgn * (o + 0.6), sgn * h_, SW_Y, 'sidewalk')
            elif zone == 'orla':                                             # calcadao: listras alternadas
                w = h_ - o; n = 4
                for q in range(n): self.strip(PAVER, sw_col if q % 2 == 0 else sw_col2, stl, sgn * (o + w * q / n), sgn * (o + w * (q + 1) / n), SW_Y, 'sidewalk')
            else:
                self.strip(PAVER, sw_col, stl, sgn * o, sgn * h_, SW_Y, 'sidewalk')
            # saia externa
            self.vwall(stl, sgn * h_, SW_Y - 0.5, SW_Y, COL['conc2'], sgn)
            # frente do lote (Etapa D)
            self.fronts.append({'edge': k, 'side': int(sgn), 'zone': zone, 'lvl': lvl, 'pts': [[round(v, 2) for v in (*self.off(s_, sgn * h_), s_['y'] + SW_Y)] for s_ in stl]})
        # --- marcacoes
        if not bridge or True:
            self.markings(k, stl_m, lvl, sec, bridge)
        # --- covas de arvore (centro e avenidas) a cada 12 m
        if lvl > 0 and zone == 'centro':
            self.tree_pits(k, stl, sec, zone)
        elif lvl == 0 and not bridge and zone != 'ponte':
            self.tree_pits(k, stl, sec, zone)
        # --- cercas, parapeitos, muros
        self.protections(k, stl, sec, bridge, zone)

    def markings(self, k, stl, lvl, sec, bridge):
        a_ = sec['asph']; ins = sec['inner']
        def line(o, w, col, dash=None):
            for q in range(len(stl) - 1):
                a, b = stl[q], stl[q + 1]
                L = math.hypot(b['x'] - a['x'], b['z'] - a['z'])
                if dash is None: spans = [(0.0, 1.0)]
                else:
                    spans = []; t = 0.0
                    while t < L: spans.append((t / L, min(t + dash[0], L) / L)); t += dash[0] + dash[1]
                for (u0, u1) in spans:
                    def P(u, oo):
                        x = lerp(a['x'], b['x'], u) + lerp(a['nx'], b['nx'], u) * oo; z = lerp(a['z'], b['z'], u) + lerp(a['nz'], b['nz'], u) * oo; y = lerp(a['y'], b['y'], u) + MARK_Y
                        return (x, y, z)
                    self.quad(PLAIN, [P(u0, o - w / 2), P(u1, o - w / 2), P(u1, o + w / 2), P(u0, o + w / 2)], col, 'mark')
        if lvl == 0:
            for sgn in (1, -1):
                line(sgn * (ins + 0.25), 0.15, COL['yellow'])
                line(sgn * (ins + 3.5), 0.12, COL['white'], (3.0, 6.0))
                line(sgn * (a_ - 2.5), 0.15, COL['white'])
        elif lvl == 1:
            line(0.12, 0.12, COL['yellow']); line(-0.12, 0.12, COL['yellow'])
            for sgn in (1, -1): line(sgn * (a_ - 2.5), 0.12, COL['white'])
        else:
            line(0.12, 0.12, COL['yellow']); line(-0.12, 0.12, COL['yellow'])
            for sgn in (1, -1): line(sgn * (a_ - 2.0), 0.10, COL['white'])

    def tree_pits(self, k, stl, sec, zone):
        L = stl[-1]['s'] - stl[0]['s']; n = int(L // 12)
        for q in range(1, n + 1):
            s = stl[0]['s'] + q * 12.0 - 6.0
            x, z, y, tx, tz = self.at(k, s); nx_, nz_ = -tz, tx
            if self.c.edges[k]['lvl'] == 0 and (s - stl[0]['s'] < 11.0 or stl[-1]['s'] - s < 11.0): continue
            for sgn in (1, -1):
                if self.sea_sign(k) == sgn: continue
                o = (sec['asph'] + 1.7) if self.c.edges[k]['lvl'] == 0 else sec['asph'] + 0.2 + (1.3 if zone == 'centro' else 1.6)
                cx, cz = x + nx_ * o * sgn, z + nz_ * o * sgn
                hw = 0.65
                p = [(cx - tx * hw - nx_ * hw, y + SW_Y + 0.02, cz - tz * hw - nz_ * hw), (cx + tx * hw - nx_ * hw, y + SW_Y + 0.02, cz + tz * hw - nz_ * hw),
                     (cx + tx * hw + nx_ * hw, y + SW_Y + 0.02, cz + tz * hw + nz_ * hw), (cx - tx * hw + nx_ * hw, y + SW_Y + 0.02, cz - tz * hw + nz_ * hw)]
                self.fronts.append({'pit': [round(cx, 2), round(cz, 2), round(y + SW_Y, 2)], 'edge': k})

    def protections(self, k, stl, sec, bridge, zone):
        h_ = sec['half']; lvl = min(self.c.edges[k]['lvl'], 2)
        if bridge:
            self.parapet(k, stl, sec)
            return
        # amostragem do terreno ao lado do passeio
        runs = {1: [], -1: []}
        for sgn in (1, -1):
            cur = None
            for q, s_ in enumerate(stl):
                x, z = self.off(s_, sgn * (h_ + 2.2)); ht = T.sample8(self.hf, x, z); drop = s_['y'] + SW_Y - ht
                kind = 'rail' if drop > 1.0 else ('wall' if drop < -1.6 else None)
                if kind is None or (cur and cur[0] != kind):
                    if cur: runs[sgn].append((cur[0], cur[1], q)); cur = None
                if kind and not cur: cur = (kind, q)
            if cur: runs[sgn].append((cur[0], cur[1], len(stl) - 1))
        sea = self.sea_sign(k)
        for sgn in (1, -1):
            if sea and sgn == sea: continue
            for kind, i0, i1 in runs[sgn]:
                if i1 <= i0: continue
                sub = stl[i0:i1 + 1]
                if kind == 'rail': self.guardrail(sub, sgn, h_ + 0.25, lvl)
                else: self.retaining(sub, sgn, h_ + 0.1)

    def guardrail(self, stl, sgn, o, lvl):
        L = stl[-1]['s'] - stl[0]['s']
        if L < 3: return
        self.stats['guard_m'] += L
        # trilho (viga W) continuo + postes a cada ~4 m
        for q in range(len(stl) - 1):
            a, b = stl[q], stl[q + 1]
            p0, p1 = self.off(a, sgn * o), self.off(b, sgn * o)
            for (yl, yh) in ((0.55, 0.86),):
                nv = (a['nx'] * sgn, 0, a['nz'] * sgn)
                for fc in (1, -1):
                    nvv = (nv[0] * fc, 0, nv[2] * fc)
                    self.B.quad(METAL, [(p0[0], a['y'] + SW_Y + yl, p0[1]), (p1[0], b['y'] + SW_Y + yl, p1[1]), (p1[0], b['y'] + SW_Y + yh, p1[1]), (p0[0], a['y'] + SW_Y + yh, p0[1])] if fc == 1 else
                                [(p1[0], b['y'] + SW_Y + yl, p1[1]), (p0[0], a['y'] + SW_Y + yl, p0[1]), (p0[0], a['y'] + SW_Y + yh, p0[1]), (p1[0], b['y'] + SW_Y + yh, p1[1])], nvv, COL['rail'], None, True)
            # topo e postes
            seg = math.hypot(b['x'] - a['x'], b['z'] - a['z']); n = max(1, int(seg // 4))
            for t in range(n):
                u = t / n; x = lerp(a['x'], b['x'], u) + lerp(a['nx'], b['nx'], u) * sgn * o; z = lerp(a['z'], b['z'], u) + lerp(a['nz'], b['nz'], u) * sgn * o; y = lerp(a['y'], b['y'], u) + SW_Y
                self.B.box(x, z, 0.12, 0.12, y - 0.3, y + 0.92, COL['iron'], PLAIN, True)
        # (lvl 0): cerca alta de avenida (alambrado de 1,2 m) em cima do trilho
        if lvl == 0:
            for q in range(len(stl) - 1):
                a, b = stl[q], stl[q + 1]
                p0, p1 = self.off(a, sgn * o), self.off(b, sgn * o)
                for fc in (1, -1):
                    pts = [(p0[0], a['y'] + SW_Y + 0.86, p0[1]), (p1[0], b['y'] + SW_Y + 0.86, p1[1]), (p1[0], b['y'] + SW_Y + 1.5, p1[1]), (p0[0], a['y'] + SW_Y + 1.5, p0[1])]
                    if fc == -1: pts = [pts[1], pts[0], pts[3], pts[2]]
                    self.B.quad(METAL, pts, (a['nx'] * sgn * fc, 0, a['nz'] * sgn * fc), COL['iron'], None, True)

    def retaining(self, stl, sgn, o):
        L = stl[-1]['s'] - stl[0]['s']
        if L < 3: return
        self.stats['wall_m'] += L
        for q in range(len(stl) - 1):
            a, b = stl[q], stl[q + 1]
            for dy0, dy1, oo, col in ((SW_Y - 0.9, SW_Y + 0.5, o, COL['wall']),):
                p0, p1 = self.off(a, sgn * oo), self.off(b, sgn * oo)
                nv = (a['nx'] * sgn, 0, a['nz'] * sgn)
                self.B.quad(STONE, [(p0[0], a['y'] + dy0, p0[1]), (p1[0], b['y'] + dy0, p1[1]), (p1[0], b['y'] + dy1, p1[1]), (p0[0], a['y'] + dy1, p0[1])], (-nv[0], 0, -nv[2]), col, None, True)
                p2, p3 = self.off(a, sgn * (oo + 0.5)), self.off(b, sgn * (oo + 0.5))
                self.B.quad(STONE, [(p2[0], a['y'] + dy1, p2[1]), (p3[0], b['y'] + dy1, p3[1]), (p1[0], b['y'] + dy1, p1[1]), (p0[0], a['y'] + dy1, p0[1])], (0, 1, 0), COL['wall2'], None, True)
                self.B.quad(STONE, [(p3[0], b['y'] + dy0, p3[1]), (p2[0], a['y'] + dy0, p2[1]), (p2[0], a['y'] + dy1, p2[1]), (p3[0], b['y'] + dy1, p3[1])], nv, COL['wall'], None, True)

    def parapet(self, k, stl, sec):
        h_ = sec['half']
        for sgn in (1, -1):
            # parede externa + cobertura + parede interna + postes de luz a cada 24 m
            self.vwall(stl, sgn * h_, SW_Y - 1.4, SW_Y + 1.1, COL['bridge'], sgn)
            self.vwall(stl, sgn * (h_ - 0.4), SW_Y, SW_Y + 1.1, COL['conc3'], -sgn)
            self.strip(PAVER, COL['curb'], stl, sgn * (h_ - 0.4), sgn * h_, SW_Y + 1.1, None)
            L = stl[-1]['s'] - stl[0]['s']
            for q in range(1, int(L // 24) + 1):
                x, z, y, tx, tz = self.at(k, stl[0]['s'] + q * 24 - 8); x += -tz * sgn * (h_ - 0.7); z += tx * sgn * (h_ - 0.7)
                self.B.cyl(x, z, 0.08, y + SW_Y, y + SW_Y + 6.0, COL['lamp'], 8)
                self.B.box(x - (-tz) * sgn * 0.5 * -1, z - tx * sgn * 0.5 * -1, 0.9, 0.3, y + SW_Y + 5.9, y + SW_Y + 6.1, COL['lamp'], PLAIN, True)
        # pilares a cada ~28 m
        L = stl[-1]['s'] - stl[0]['s']; piers = []
        for q in range(1, int(L // 28) + 1):
            x, z, y, tx, tz = self.at(k, stl[0]['s'] + q * 28 - 14); piers.append((x, z, y + ROADY, tx, tz))
        scenery.bridge_piers(self.B, piers, self.hf, 0, h_)
        # vigas longitudinais sob o tabuleiro
        for sgn in (-1, 1):
            self.vwall(stl, sgn * 3.5, ROADY - 2.2, ROADY - 0.05, COL['under'], sgn)
            self.vwall(stl, sgn * 3.5 + sgn * 0.7, ROADY - 2.2, ROADY - 0.05, COL['under'], -sgn)
        self.strip(PAVER, COL['under'], stl, -h_, h_, ROADY - 0.05, None)    # fundo do tabuleiro

    # ------------------------------------------------------------ geral
    def red_bridges(self):
        self.red_info = []
        for r in self.c.red:
            lx, lz = r['lookout']
            lk = [i for i in self.c.lookouts if abs(self.c.nodes[i][0] - lx) < 1 and abs(self.c.nodes[i][1] - lz) < 1]
            deck = self.yn[lk[0]] if lk else r['deck']
            rb = {'z': r['z'], 'x_a': r['x_a'], 'x_b': r['x_b'], 'towers': r['towers'], 'portal': r['portal']}
            info = scenery.red_bridge(self.B, rb, self.hf, deck, lx)
            info['name'] = r['name']; self.red_info.append(info)

    def is_beach(self, k): return self.c.edges[k].get('name') == 'Av. Beira-Mar'

    def sea_sign(self, k):
        """+1/-1: lado (normal da estacao) que da para o mar na Av. Beira-Mar; 0 nas outras ruas"""
        if not self.is_beach(k): return 0
        if k in self._sea: return self._sea[k]
        L = self.elen(k); acc = 0.0; n = 0
        for f in (0.25, 0.5, 0.75):
            x, z, y, tx, tz = self.at(k, L * f); nx_, nz_ = -tz, tx
            jp = self.geo.idx(x + nx_ * 25, z + nz_ * 25); jm = self.geo.idx(x - nx_ * 25, z - nz_ * 25)
            acc += float(self.geo.Dsea[jm]) - float(self.geo.Dsea[jp])
        self._sea[k] = 1 if acc > 0 else -1
        return self._sea[k]

    def build(self):
        self._sea = {}
        self.infos = {ni: self.compute_cuts(ni) for ni in self.arms}
        self.plan_crosswalks()
        for ni in self.arms: self.junction(ni)
        for k in range(len(self.c.edges)): self.edge_body(k)
        self.red_bridges()
        if getattr(self.c, 'lotplan', None) is not None:
            import lots; lots.build_ground(self, self.c.lotplan)
        return self
