"""Monta a cidade: rede organica + pontes sobre o rio + pontes vermelhas + rotatorias + marcacoes."""
import math
from collections import defaultdict
from plan import *
import geo as G
import network as N

def elen(p): return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(p, p[1:]))

class City:
    def __init__(self, geo):
        self.geo = geo
        fld, nodes, edges, stats = N.generate(geo)
        self.fld = fld; self.stats = stats
        self.nodes = [list(n) for n in nodes]
        self.edges = [{'a': e['a'], 'b': e['b'], 'p': [tuple(q) for q in e['p']], 'lvl': e['lvl'], 'kind': 'n', 'name': ''} for e in edges]
        self.rounds = []
        self.red = []
        self.drop_unused()

    def drop_unused(self):
        used = sorted({e['a'] for e in self.edges} | {e['b'] for e in self.edges})
        m = {o: i for i, o in enumerate(used)}
        self.nodes = [self.nodes[o] for o in used]
        for e in self.edges: e['a'] = m[e['a']]; e['b'] = m[e['b']]

    def add_node(self, x, z):
        for i, n in enumerate(self.nodes):
            if math.hypot(n[0] - x, n[1] - z) < 1.0: return i
        self.nodes.append([x, z]); return len(self.nodes) - 1

    def nearest(self, x, z, within=1e9, pred=None):
        best = None
        for i, n in enumerate(self.nodes):
            if pred and not pred(i): continue
            d = math.hypot(n[0] - x, n[1] - z)
            if d < within and (best is None or d < best[0]): best = (d, i)
        return best[1] if best else None

    def add_edge(self, a, b, pts, lvl, kind, name=''):
        p = [tuple(self.nodes[a])] + [tuple(q) for q in pts] + [tuple(self.nodes[b])]
        self.edges.append({'a': a, 'b': b, 'p': p, 'lvl': lvl, 'kind': kind, 'name': name})

    def crosses(self, path, ends):
        from network import seg_inter
        for e in self.edges:
            if e['kind'] in ('bridge', 'redbridge'): continue
            for a, b in zip(e['p'], e['p'][1:]):
                for c_, d_ in zip(path, path[1:]):
                    r = seg_inter(a, b, c_, d_)
                    if r and 0.02 < r[0] < 0.98 and 0.02 < r[1] < 0.98: return True
        return False

    def lagoon_ring(self):
        lx, lz, rx, rz = LAGOON
        ex, ez = rx + 46, rz + 46
        def inside(p): return ((p[0] - lx) / (ex + 24)) ** 2 + ((p[1] - lz) / (ez + 24)) ** 2 < 1.0
        self.edges = [e for e in self.edges if not any(inside(q) for q in e['p'])]
        self.drop_unused()
        n = 36; pts = [(lx + ex * math.cos(2 * math.pi * k / n), lz + ez * math.sin(2 * math.pi * k / n)) for k in range(n)]
        pts = [p for p in pts]
        idx = [self.add_node(*pts[k]) for k in range(0, n, 3)]
        for q in range(len(idx)):
            k0 = q * 3; seg = [pts[(k0 + t) % n] for t in range(1, 3)]
            self.add_edge(idx[q], idx[(q + 1) % len(idx)], seg, 0, 'n', 'Anel da Lagoa')
        ring = set(idx); added = 0
        for k in range(0, len(idx), 3):          # 4 ligacoes: N, L, S, O
            r = idx[k]; x0, z0 = self.nodes[r]
            cands = sorted((i for i in range(len(self.nodes)) if i not in ring and len(self.nodes[i]) == 2), key=lambda i: math.hypot(self.nodes[i][0] - x0, self.nodes[i][1] - z0))
            for tgt in cands[:30]:
                tx, tz = self.nodes[tgt][:2]
                path = [(x0, z0), ((x0 + tx) / 2, (z0 + tz) / 2), (tx, tz)]
                if math.hypot(tx - x0, tz - z0) < 420 and not self.crosses(path, ()) and not self.too_close(path) and not any(self.geo.is_water(*q) for q in path):
                    self.edges.append({'a': r, 'b': tgt, 'p': path, 'lvl': 0, 'kind': 'n', 'name': 'Av. da Lagoa'}); added += 1; break
        self.ring = idx

    def too_close(self, path, r=22.0, skip=38.0):
        import numpy as np
        A = []; B = []
        for e in self.edges:
            for a, b in zip(e['p'], e['p'][1:]): A.append(a[:2]); B.append(b[:2])
        if not A: return False
        A = np.array(A, float); B = np.array(B, float); D = B - A; L2 = (D ** 2).sum(1) + 1e-9
        total = elen(path); n = max(2, int(total / 10))
        for s in range(1, n):
            t = s / n; L = total * t
            if L < skip or total - L < skip: continue
            # ponto na polilinha
            acc = 0.0
            for a, b in zip(path, path[1:]):
                seg = math.hypot(b[0] - a[0], b[1] - a[1])
                if acc + seg >= L:
                    f = (L - acc) / (seg or 1); px, pz = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f; break
                acc += seg
            u = np.clip(((px - A[:, 0]) * D[:, 0] + (pz - A[:, 1]) * D[:, 1]) / L2, 0, 1)
            d = np.hypot(A[:, 0] + u * D[:, 0] - px, A[:, 1] + u * D[:, 1] - pz)
            if d.min() < r: return True
        return False

    def components(self):
        adj = defaultdict(list)
        for e in self.edges: adj[e['a']].append(e['b']); adj[e['b']].append(e['a'])
        comp = {}; groups = []
        for i in range(len(self.nodes)):
            if i in comp: continue
            st = [i]; comp[i] = len(groups); g = [i]
            while st:
                u = st.pop()
                for w in adj[u]:
                    if w not in comp: comp[w] = len(groups); st.append(w); g.append(w)
            groups.append(g)
        return comp, groups

    def river_bridges(self, zs=(820, 1250, 1750, 2150), names=('Ponte do Moinho', 'Ponte Central', 'Ponte Real', 'Ponte da Foz')):
        rp = RIVER['pts']
        for z, nm in zip(zs, names):
            # centro do rio nesse z
            cx = None
            for a, b in zip(rp, rp[1:]):
                if min(a[1], b[1]) <= z <= max(a[1], b[1]) and a[1] != b[1]:
                    t = (z - a[1]) / (b[1] - a[1]); cx = a[0] + (b[0] - a[0]) * t; break
            if cx is None: continue
            w = self.nearest(cx - 70, z, 260, lambda i: self.nodes[i][0] < cx - 30)
            e = self.nearest(cx + 70, z, 260, lambda i: self.nodes[i][0] > cx + 30)
            if w is None or e is None: continue
            self.add_edge(w, e, [], 0, 'bridge', nm)

    def connect_components(self):
        for _ in range(12):
            comp, groups = self.components()
            if len(groups) == 1: return
            groups.sort(key=len, reverse=True)
            main = set(groups[0]); done = False
            for g in groups[1:]:
                if len(g) < 5:
                    ids = set(g); self.edges = [e for e in self.edges if e['a'] not in ids and e['b'] not in ids]; continue
                best = None
                for i in g:
                    j = self.nearest(self.nodes[i][0], self.nodes[i][1], 700, lambda k: k in main)
                    if j is None: continue
                    d = math.hypot(self.nodes[i][0] - self.nodes[j][0], self.nodes[i][1] - self.nodes[j][1])
                    if best is None or d < best[0]: best = (d, i, j)
                if best:
                    d, i, j = best
                    mx, mz = (self.nodes[i][0] + self.nodes[j][0]) / 2, (self.nodes[i][1] + self.nodes[j][1]) / 2
                    self.add_edge(i, j, [], 1, 'bridge' if self.geo.is_water(mx, mz) else 'n', 'Ligacao'); done = True
                else:
                    ids = set(g); self.edges = [e for e in self.edges if e['a'] not in ids and e['b'] not in ids]
            self.drop_unused()

    def red_bridges(self):
        """Pontes vermelhas: SO CENARIO (sem acesso, sem estrada alem do mirante). A via da cidade termina num mirante com cancela."""
        self.lookouts = []
        for tag, rb, name in (('W', RED_BRIDGE_W, 'Ponte Vermelha Oeste'), ('E', RED_BRIDGE_E, 'Ponte Vermelha Leste')):
            z = rb['z']; sgn = 1 if tag == 'W' else -1
            lx = rb['x_b'] + sgn * 30.0                      # mirante, 30 m antes da cabeceira
            self.red.append({'name': name, 'z': z, 'x_a': rb['x_a'], 'x_b': rb['x_b'], 'towers': rb['towers'], 'deck': rb['deck'],
                             'portal': rb['portal'], 'lookout': (lx, z), 'drivable': False})
            lk = self.add_node(lx, z); self.nodes[lk].append('lookout'); self.lookouts.append(lk)
            cands = sorted((i for i in range(len(self.nodes)) if len(self.nodes[i]) == 2 and i != lk and abs(self.nodes[i][0] - lx) > 60),
                           key=lambda i: math.hypot(self.nodes[i][0] - lx - sgn * 260, self.nodes[i][1] - z - 60))
            for tgt in cands[:60]:
                tx, tz = self.nodes[tgt][:2]
                mid = [((lx * 2 + tx) / 3, z + (tz - z) * 0.25 + 18), ((lx + tx * 2) / 3, z + (tz - z) * 0.75 - 18)]
                path = [(lx, z)] + mid + [(tx, tz)]
                if not self.crosses(path, ()) and not self.too_close(path) and not any(self.geo.is_water(*q) for q in path[1:]):
                    self.edges.append({'a': lk, 'b': tgt, 'p': path, 'lvl': 1, 'kind': 'n', 'name': 'Estrada da ' + name}); break

    def degrees(self):
        deg = defaultdict(int); inc = defaultdict(list)
        for k, e in enumerate(self.edges): deg[e['a']] += 1; deg[e['b']] += 1; inc[e['a']].append(k); inc[e['b']].append(k)
        return deg, inc

    def fix_dead_ends(self):
        """cada fim de rua precisa ter sentido: liga a outra rua, termina em cais/praia, vira bolsao de retorno (rua local curta) ou e apagado"""
        self.legit_xy = {}
        for it in range(400):
            deg, inc = self.degrees(); changed = False
            for i in [i for i, d in deg.items() if d == 1 and len(self.nodes[i]) == 2]:
                if (round(self.nodes[i][0], 2), round(self.nodes[i][1], 2)) in self.legit_xy: continue
                k = inc[i][0]; e = self.edges[k]; L = elen(e['p'])
                x, z = self.nodes[i][:2]
                # direcao de chegada
                p = e['p'] if e['a'] == i else e['p'][::-1]
                hx, hz = p[0][0] - p[1][0], p[0][1] - p[1][1]; hl = math.hypot(hx, hz) or 1; hx /= hl; hz /= hl
                j_, i_ = self.geo.idx(x, z); dwater = float(self.geo.D[j_, i_])
                # 1) cais / praia
                if dwater < 70 and e['lvl'] >= 1:
                    self.legit_xy[(round(x, 2), round(z, 2))] = 'cais'; continue
                # 2) tenta ligar a uma rua proxima (de preferencia a frente)
                cands = []
                for t in range(len(self.nodes)):
                    if t == i or len(self.nodes[t]) != 2 and self.nodes[t][2] != 'lookout': continue
                    d = math.hypot(self.nodes[t][0] - x, self.nodes[t][1] - z)
                    if d < 60 or d > 330: continue
                    ca = ((self.nodes[t][0] - x) * hx + (self.nodes[t][1] - z) * hz) / d
                    if ca < 0.35: continue
                    cands.append((d * (2 - ca), t, d))
                cands.sort(); done = False
                for _, t, d in cands[:25]:
                    tx, tz = self.nodes[t][:2]
                    nxp, nzp = -(tz - z) / d, (tx - x) / d
                    path = [(x, z), (x + (tx - x) / 3 + nxp * d * 0.07, z + (tz - z) / 3 + nzp * d * 0.07), (x + (tx - x) * 2 / 3 - nxp * d * 0.05, z + (tz - z) * 2 / 3 - nzp * d * 0.05), (tx, tz)]
                    if any(self.geo.is_water(*q) for q in path) or not self.geo.is_urban(path[1][0], path[1][1]): continue
                    if abs(self.geo.height(tx, tz) - self.geo.height(x, z)) / d > 0.10: continue
                    if any({ee['a'], ee['b']} == {i, t} for ee in self.edges): continue
                    if self.crosses(path, ()) or self.too_close(path): continue
                    self.edges.append({'a': i, 'b': t, 'p': path, 'lvl': max(e['lvl'], 1) if e['lvl'] < 2 else 2, 'kind': 'n', 'name': 'Ligacao'}); done = True; break
                if done: changed = True; break
                # 3) bolsao de retorno so em rua local de 60..320 m
                if e['lvl'] == 2 and 60 <= L <= 320:
                    self.legit_xy[(round(x, 2), round(z, 2))] = 'bolsao'; continue
                # 4) sem sentido: apaga o trecho
                self.edges.pop(k); changed = True; break
            if not changed: break
        self.drop_unused()

    def contract_short(self, min_len=40.0):
        """funde nos ligados por trechos muito curtos (Y e cruzamentos colados viram um cruzamento so)"""
        n = 0
        for _ in range(500):
            deg, inc = self.degrees(); best = None
            for k, e in enumerate(self.edges):
                if e['kind'] != 'n' or e['a'] == e['b']: continue
                if len(self.nodes[e['a']]) > 2 or len(self.nodes[e['b']]) > 2: continue
                L = elen(e['p'])
                if L < min_len and (best is None or L < best[0]): best = (L, k)
            if not best: break
            k = best[1]; e = self.edges[k]; a, b = e['a'], e['b']
            na, nb = self.nodes[a][:2], self.nodes[b][:2]
            mx, mz = (na[0] + nb[0]) / 2, (na[1] + nb[1]) / 2
            self.nodes[a][0], self.nodes[a][1] = mx, mz
            out = []
            for i, ed in enumerate(self.edges):
                if i == k: continue
                if ed['a'] == b: ed['a'] = a; ed['p'][0] = (mx, mz)
                if ed['b'] == b: ed['b'] = a; ed['p'][-1] = (mx, mz)
                if ed['a'] == a: ed['p'][0] = (mx, mz)
                if ed['b'] == a: ed['p'][-1] = (mx, mz)
                if ed['a'] == ed['b']: continue
                out.append(ed)
            self.edges = out; n += 1
        self.dedupe(); self.drop_unused(); self.contracted = n

    def arm_dir(self, k, node):
        e = self.edges[k]; p = e['p'] if e['a'] == node else e['p'][::-1]
        acc = 0.0
        for a, b in zip(p, p[1:]):
            acc += math.hypot(b[0] - a[0], b[1] - a[1])
            if acc >= 16.0: return math.atan2(b[1] - p[0][1], b[0] - p[0][0])
        return math.atan2(p[-1][1] - p[0][1], p[-1][0] - p[0][0])

    def connected_without(self, k):
        adj = defaultdict(list)
        for i, e in enumerate(self.edges):
            if i != k: adj[e['a']].append(e['b']); adj[e['b']].append(e['a'])
        seen = {self.edges[k]['a']}; st = [self.edges[k]['a']]
        while st:
            u = st.pop()
            for w in adj[u]:
                if w not in seen: seen.add(w); st.append(w)
        return self.edges[k]['b'] in seen

    def fix_acute(self, min_gap=math.radians(52.0)):
        """remove a rua de menor hierarquia que sai de um cruzamento colada demais a outra (cantos que nao se desenham bem)"""
        removed = 0
        for _ in range(300):
            deg, inc = self.degrees(); victim = None
            for ni, ks in inc.items():
                if len(ks) < 3 or len(self.nodes[ni]) > 2: continue
                ang = sorted((self.arm_dir(k, ni), k) for k in ks)
                for q in range(len(ang)):
                    a, b = ang[q], ang[(q + 1) % len(ang)]
                    gap = (b[0] - a[0]) % (2 * math.pi)
                    if gap < min_gap:
                        ka, kb = a[1], b[1]
                        cand = sorted((ka, kb), key=lambda k: (-self.edges[k]['lvl'], elen(self.edges[k]['p'])))
                        for k in cand:
                            if self.edges[k]['kind'] == 'n' and self.connected_without(k): victim = k; break
                    if victim is not None: break
                if victim is not None: break
            if victim is None: break
            self.edges.pop(victim); removed += 1
        self.drop_unused(); self.acute_removed = removed

    def dedupe(self):
        seen = set(); out = []
        for e in self.edges:
            k = frozenset((e['a'], e['b']))
            if k in seen and e['a'] != e['b']: continue
            seen.add(k); out.append(e)
        self.edges = out

    def make_rounds(self, n=9, mind=420.0):
        deg = defaultdict(int); hi = defaultdict(int)
        for e in self.edges:
            deg[e['a']] += 1; deg[e['b']] += 1
            if e['lvl'] <= 1: hi[e['a']] += 1; hi[e['b']] += 1
        cand = [i for i in deg if deg[i] >= 4 and hi[i] >= 3 and len(self.nodes[i]) == 2]
        cand.sort(key=lambda i: -hi[i] * 1000 + math.hypot(self.nodes[i][0] - CITY_CENTER[0], self.nodes[i][1] - CITY_CENTER[1]))
        for i in cand:
            x, z = self.nodes[i][:2]
            if all(math.hypot(x - r['x'], z - r['z']) > mind for r in self.rounds):
                self.rounds.append({'x': x, 'z': z, 'r': 30.0 + 6 * min(hi[i] - 3, 3), 'node': i})
            if len(self.rounds) >= n: break

    def flags(self):
        deg = defaultdict(int)
        for e in self.edges: deg[e['a']] += 1; deg[e['b']] += 1
        self.cul = {i for i, d in deg.items() if d == 1 and len(self.nodes[i]) == 2}
        self.portals = {i for i, n in enumerate(self.nodes) if len(n) > 2 and n[2] == 'portal'}
        self.lookouts = [i for i, n in enumerate(self.nodes) if len(n) > 2 and n[2] == 'lookout']
        self.legit = {i: self.legit_xy[(round(n[0], 2), round(n[1], 2))] for i, n in enumerate(self.nodes) if (round(n[0], 2), round(n[1], 2)) in self.legit_xy}

def build(geo):
    c = City(geo)
    c.lagoon_ring(); c.river_bridges(); c.connect_components(); c.red_bridges(); c.fix_dead_ends(); c.connect_components(); c.dedupe(); c.contract_short(); c.fix_acute(); c.fix_dead_ends(); c.contract_short(); c.make_rounds(); c.flags()
    return c
