"""Modelo de TRANSITO (mao direita): faixas por sentido, movimentos nos cruzamentos/rotatorias, semaforos, controle (PARE/preferencial), lombadas, placas."""
import math
import numpy as np
from collections import defaultdict
from plan import *

LANES = {0: dict(n=2, w=3.5, first=3.75, speed=60), 1: dict(n=1, w=3.5, first=1.75, speed=40), 2: dict(n=1, w=3.0, first=1.5, speed=30)}
SEC_A = {0: 11.5, 1: 6.0, 2: 5.0}; SEC_INS = {0: 2.0, 1: 0.0, 2: 0.0}; SEC_H = {0: 15.8, 1: 10.0, 2: 7.5}

def lane_offsets(lvl):
    L = LANES[min(lvl, 2)]
    return [L['first'] + i * L['w'] for i in range(L['n'])]

def bez(p0, p1, p2, p3, n=14):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0], u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out

def resample(pts, step=6.0):
    out = [pts[0]]; acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        while acc + step <= L + 1e-9 and L > 0:
            acc += step; f = acc / L; out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
        acc -= L
        if acc < 0: acc = 0.0 if abs(acc) < 1e-9 else acc
    out.append(pts[-1]); return out

def min_radius(pts):
    """menor raio de curvatura (circunraio de 3 pontos reamostrados a cada ~6 m)"""
    if len(pts) > 3: pts = resample(pts, 6.0)
    best = 1e9
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        ab = math.hypot(b[0] - a[0], b[1] - a[1]); bc = math.hypot(c[0] - b[0], c[1] - b[1]); ca = math.hypot(a[0] - c[0], a[1] - c[1])
        area2 = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        if area2 < 1e-6: continue
        best = min(best, ab * bc * ca / (2 * area2))
    return best

class Traffic:
    def __init__(self, gr):
        self.g = gr; self.c = gr.c
        self.moves = []          # movimentos: dict(node, kind, from=(k,end), to=(k,end), lane_from, lane_to, turn, path)
        self.signals = {}        # node -> dict(phases, cycle)
        self.control = {}        # (node,k,end) -> 'signal' | 'stop' | 'yield' | 'priority'
        self.bumps = []          # dict(k, s, x, z, y, tx, tz, w)
        self.signs = []          # dict(type, x, z, y, yaw, text, pole)
        self.heads = []          # cabecas de semaforo
        self.arrows = []
        self.curve_report = []

    # ------------------------------------------------------------ movimentos
    def turn_type(self, ai, aj):
        # angulo de giro do rumo de chegada (-d_i) ao de saida (d_j); z para sul => positivo = direita (horario visto de cima, norte para cima)
        h0 = (-ai['d'][0], -ai['d'][1]); h1 = aj['d']
        cr = h0[0] * h1[1] - h0[1] * h1[0]; dot = h0[0] * h1[0] + h0[1] * h1[1]
        ang = math.degrees(math.atan2(cr, dot))
        if abs(ang) < 28: return 'straight', ang
        if abs(ang) > 160: return 'uturn', ang
        return ('right' if ang > 0 else 'left'), ang

    def arm_frame(self, a):
        """ponto do corte e direcao para fora do no"""
        f = self.g.frame(a)          # x,z,y, rx, rz (normal direita de quem sai)
        # direcao para fora = rotaciona (rx,rz) -90 graus: d = (rz, -rx)
        d = (f[4], -f[3])
        return f[0], f[1], f[2], d

    def build_moves(self):
        g = self.g
        for ni, arms in g.arms.items():
            n = len(arms)
            nx, nz = self.c.nodes[ni][:2]
            if n == 2 and arms[0].get('merge'): continue       # curva suave: so segue
            if ni in g.rounds and n >= 3:
                self.round_moves(ni, arms, g.rounds[ni]); continue
            if n == 1:
                self.deadend_move(ni, arms[0]); continue
            for ai in arms:
                lvl_i = min(ai['lvl'], 2); offs_i = lane_offsets(lvl_i)
                xi, zi, yi, di = self.arm_frame(ai)
                for aj in arms:
                    if aj is ai: continue
                    kind, ang = self.turn_type(ai, aj)
                    if kind == 'uturn' and n > 2: continue
                    lvl_j = min(aj['lvl'], 2); offs_j = lane_offsets(lvl_j)
                    xj, zj, yj, dj = self.arm_frame(aj)
                    for u, off_u in enumerate(offs_i):
                        # faixa 0 = mais perto do centro (esquerda); ultima = mais a direita (meio-fio)
                        last_i = len(offs_i) - 1
                        if kind == 'right' and u != last_i: continue
                        if kind == 'left' and u != 0: continue
                        if kind == 'straight': pass
                        v = {'right': len(offs_j) - 1, 'left': 0}.get(kind, min(u, len(offs_j) - 1))
                        off_v = offs_j[v]
                        # lado direito de quem CHEGA = (d_iz, -d_ix) ; lado direito de quem SAI = (-d_jz, d_jx)
                        r_in = (di[1], -di[0]); r_out = (-dj[1], dj[0])
                        p0 = (xi + r_in[0] * off_u, zi + r_in[1] * off_u); p3 = (xj + r_out[0] * off_v, zj + r_out[1] * off_v)
                        chord = math.hypot(p3[0] - p0[0], p3[1] - p0[1]); k_ = max(3.0, 0.45 * chord)
                        h0 = (-di[0], -di[1]); h1 = dj
                        p1 = (p0[0] + h0[0] * k_, p0[1] + h0[1] * k_); p2 = (p3[0] - h1[0] * k_, p3[1] - h1[1] * k_)
                        path = bez(p0, p1, p2, p3, 16)
                        self.moves.append({'node': ni, 'kind': kind, 'from': (ai['k'], ai['end']), 'to': (aj['k'], aj['end']), 'lane_from': u, 'lane_to': v, 'path': path,
                                           'y': float(self.g.yn[ni]), 'radius': min_radius(path)})

    def round_moves(self, ni, arms, Ro):
        g = self.g; nx, nz = self.c.nodes[ni][:2]; Ri = Ro - 9.5; rm = (Ri + Ro) / 2 - 1.2         # faixa interna do anel (sentido anti-horario visto do norte: angulo DIMINUI)
        for ai in arms:
            xi, zi, yi, di = self.arm_frame(ai); lvl_i = min(ai['lvl'], 2); off_i = lane_offsets(lvl_i)[-1]
            r_in = (di[1], -di[0])
            p0 = (xi + r_in[0] * off_i, zi + r_in[1] * off_i)
            ang_i = math.atan2(zi - nz, xi - nx)
            for aj in arms:
                xj, zj, yj, dj = self.arm_frame(aj); lvl_j = min(aj['lvl'], 2); off_j = lane_offsets(lvl_j)[-1]
                r_out = (-dj[1], dj[0]); p3 = (xj + r_out[0] * off_j, zj + r_out[1] * off_j)
                ang_j = math.atan2(zj - nz, xj - nx)
                if aj is ai:
                    if len(arms) > 2: continue
                # entra no anel a ~ -20 graus do braco, circula com angulo diminuindo, sai a +20 graus do braco de saida
                a0 = ang_i - 0.35; a1 = ang_j + 0.35
                sweep = (a0 - a1) % (2 * math.pi)
                if sweep < 0.2: sweep = 2 * math.pi - 0.0 if aj is ai else sweep
                ring = [(nx + math.cos(a0 - sweep * t / 18) * rm, nz + math.sin(a0 - sweep * t / 18) * rm) for t in range(19)]
                e1 = (nx + math.cos(a0) * rm, nz + math.sin(a0) * rm); e2 = ring[-1]
                c1 = bez(p0, (p0[0] - di[0] * 5, p0[1] - di[1] * 5), (e1[0] + math.sin(a0) * 4, e1[1] - math.cos(a0) * 4), e1, 6)
                c2 = bez(e2, (e2[0] - math.sin(a1) * 4, e2[1] + math.cos(a1) * 4), (p3[0] - dj[0] * 5, p3[1] - dj[1] * 5), p3, 6)
                path = c1 + ring[1:] + c2[1:]
                self.moves.append({'node': ni, 'kind': 'roundabout', 'from': (ai['k'], ai['end']), 'to': (aj['k'], aj['end']), 'lane_from': 0, 'lane_to': 0, 'path': path, 'y': float(g.yn[ni]), 'radius': min_radius(path)})

    def deadend_move(self, ni, a):
        g = self.g; x, z, y, d = self.arm_frame(a); lvl = min(a['lvl'], 2); off = lane_offsets(lvl)[-1]
        r_in = (d[1], -d[0]); r_out = (-d[1], d[0])
        p0 = (x + r_in[0] * off, z + r_in[1] * off); p3 = (x + r_out[0] * off, z + r_out[1] * off)
        nx, nz = self.c.nodes[ni][:2]; R = 8.0
        c = (nx - d[0] * 0.0, nz - d[1] * 0.0)
        p1 = (p0[0] - d[0] * 12, p0[1] - d[1] * 12); p2 = (p3[0] - d[0] * 12, p3[1] - d[1] * 12)
        path = bez(p0, p1, p2, p3, 18)
        self.moves.append({'node': ni, 'kind': 'uturn', 'from': (a['k'], a['end']), 'to': (a['k'], a['end']), 'lane_from': 0, 'lane_to': 0, 'path': path, 'y': float(g.yn[ni]), 'radius': min_radius(path)})

    # ------------------------------------------------------------ controle: semaforos, PARE, preferencial
    def plan_control(self):
        g = self.g; c = self.c
        cand = []
        for ni, arms in g.arms.items():
            n = len(arms)
            if n < 3 or ni in g.rounds: continue
            lv = sorted(a['lvl'] for a in arms)
            important = (lv[0] <= 1 and lv[1] <= 1 and (n >= 4 or lv[0] == 0))
            if important: cand.append((lv[0] + lv[1], -n, ni))
        cand.sort()
        sig_nodes = []
        for _, _, ni in cand:
            x, z = c.nodes[ni][:2]
            if any(math.hypot(x - sx, z - sz) < 150 for sx, sz in sig_nodes): continue
            sig_nodes.append((x, z)); self.signals[ni] = None
        for ni in list(self.signals):
            arms = g.arms[ni]
            # fases: agrupa bracos por eixo (angulo modulo 180)
            groups = []
            for a in sorted(arms, key=lambda a: a['lvl']):
                ax = a['ang'] % math.pi
                for gp in groups:
                    d = abs(((ax - gp['ax']) + math.pi / 2) % math.pi - math.pi / 2)
                    if d < math.radians(38): gp['arms'].append(a); break
                else: groups.append({'ax': ax, 'arms': [a]})
            groups.sort(key=lambda gp: min(a['lvl'] for a in gp['arms']))
            t = 0.0; phases = []
            for gi, gp in enumerate(groups):
                gtime = 30.0 if gi == 0 else 22.0
                phases.append({'arms': [(a['k'], a['end']) for a in gp['arms']], 'start': t, 'green': gtime, 'yellow': 3.0, 'allred': 2.0}); t += gtime + 5.0
            self.signals[ni] = {'phases': phases, 'cycle': t, 'x': float(c.nodes[ni][0]), 'z': float(c.nodes[ni][1])}
            for a in arms: self.control[(ni, a['k'], a['end'])] = 'signal'
        for ni, arms in g.arms.items():
            n = len(arms)
            if n < 3 or ni in self.signals: continue
            if ni in g.rounds:
                for a in arms: self.control[(ni, a['k'], a['end'])] = 'yield'
                continue
            lv = [a['lvl'] for a in arms]; mn = min(lv)
            if all(l >= 2 for l in lv) and n >= 4:
                for a in arms: self.control[(ni, a['k'], a['end'])] = 'stop'                    # PARE em todas as direcoes
                continue
            # rua principal = as duas de maior hierarquia; as demais: PARE
            order = sorted(arms, key=lambda a: a['lvl'])
            main = {id(order[0]), id(order[1])}
            if order[1]['lvl'] > order[0]['lvl'] and n == 3 and order[1]['lvl'] > mn:
                pass
            for a in arms:
                self.control[(ni, a['k'], a['end'])] = 'priority' if id(a) in main else 'stop'

    # ------------------------------------------------------------ lombadas
    def plan_bumps(self):
        g = self.g; c = self.c
        xw = g.xw_centers
        placed = []
        def ok_pos(x, z):
            if any(math.hypot(x - px, z - pz) < 65 for px, pz in placed): return False
            if any(math.hypot(x - cx, z - cz) < 30 for cx, cz in xw): return False
            return True
        def add(k, s, why):
            x, z, y, tx, tz = g.at(k, s)
            self.bumps.append({'k': k, 's': float(s), 'x': float(x), 'z': float(z), 'y': float(y), 'tx': tx, 'tz': tz, 'why': why, 'lvl': c.edges[k]['lvl']})
            placed.append((x, z))
        for k, e in enumerate(c.edges):
            if e['kind'] != 'n' or e['lvl'] == 0: continue
            L = g.elen(k)
            ca = max([a['cut'] for a in g.arms.get(e['a'], []) if a['k'] == k and a['end'] == 'a'] or [1.0]); cb = max([a['cut'] for a in g.arms.get(e['b'], []) if a['k'] == k and a['end'] == 'b'] or [1.0])
            lo, hi = ca + 28.0, L - cb - 28.0
            if hi - lo < 4: continue
            mx, mz, _, _, _ = g.at(k, L / 2); zone = g.zone(mx, mz)
            # 1) entrada de rotatoria: 30 m antes (rua nao-avenida)
            for ni, end, cut in ((e['a'], 'a', ca), (e['b'], 'b', cb)):
                if ni in g.rounds:
                    s = cut + 32.0 if end == 'a' else L - cut - 32.0
                    if lo <= s <= hi:
                        x, z, *_ = g.at(k, s)
                        if ok_pos(x, z): add(k, s, 'rotatoria')
            # 2) locais de bairro/colina: a cada ~80 m
            if e['lvl'] == 2 and zone in ('res', 'colina'):
                s = lo + 10.0
                while s <= hi:
                    x, z, *_ = g.at(k, s)
                    # evita curvas fechadas
                    xa, za, *_ = g.at(k, max(s - 10, 0)); xb, zb, *_ = g.at(k, min(s + 10, L))
                    straight = (math.hypot(xb - xa, zb - za) / 20.0) > 0.985
                    if straight and ok_pos(x, z): add(k, s, 'rua-local'); s += 80.0
                    else: s += 6.0
            # 3) antes de faixa de pedestre em coletoras e locais (35 m)
            for ni, end, cut in ((e['a'], 'a', ca), (e['b'], 'b', cb)):
                for a in g.arms.get(ni, []):
                    if a['k'] == k and a['end'] == end and a.get('xw'):
                        s = cut + 36.0 if end == 'a' else L - cut - 36.0
                        if lo <= s <= hi:
                            x, z, *_ = g.at(k, s)
                            if ok_pos(x, z): add(k, s, 'faixa-de-pedestre')

    # ------------------------------------------------------------ analise
    def curve_check(self):
        c = self.c; worst = []
        for k, e in enumerate(c.edges):
            if e['kind'] != 'n': continue
            r = min_radius(e['p']); lvl = min(e['lvl'], 2)
            need = lane_offsets(lvl)[-1] + 7.0
            if r < need: worst.append((r, need, k))
        self.curve_report = sorted(worst)
        return self.curve_report

    def lane_graph_connected(self):
        """grafo dirigido (aresta, sentido): todo estado alcanca todo outro?"""
        succ = defaultdict(set); nodes = set()
        c = self.c
        # estados: (k, 'f') = trafegando de a para b ; (k, 'b') = de b para a
        for k, e in enumerate(c.edges):
            if e['kind'] == 'redbridge': continue
            nodes.add((k, 'f')); nodes.add((k, 'b'))
        def state_in(k, end):    # chegando ao no 'end' (a|b)
            return (k, 'b') if end == 'b' else (k, 'f')     # chegando em b => indo de a->b = 'f' ; chegando em a => indo b->a = 'b'
        def state_out(k, end):   # saindo do no 'end'
            return (k, 'f') if end == 'a' else (k, 'b')
        for m in self.moves:
            ki, ei = m['from']; ko, eo = m['to']
            succ[(ki, 'f' if ei == 'b' else 'b')].add((ko, 'f' if eo == 'a' else 'b'))
        # nos de grau 2 merge: estado continua
        g = self.g
        for ni, arms in g.arms.items():
            if len(arms) == 2 and arms[0].get('merge'):
                a1, a2 = arms
                succ[(a1['k'], 'f' if a1['end'] == 'b' else 'b')].add((a2['k'], 'f' if a2['end'] == 'a' else 'b'))
                succ[(a2['k'], 'f' if a2['end'] == 'b' else 'b')].add((a1['k'], 'f' if a1['end'] == 'a' else 'b'))
        pred = defaultdict(set)
        for s_, ts in succ.items():
            for t_ in ts: pred[t_].add(s_)
        start = next(iter(nodes))
        def reach(adj):
            seen = {start}; st = [start]
            while st:
                u = st.pop()
                for w in adj[u]:
                    if w not in seen: seen.add(w); st.append(w)
            return seen
        f = reach(succ); b = reach(pred)
        bad = [s_ for s_ in nodes if s_ not in f or s_ not in b]
        return len(nodes), bad
