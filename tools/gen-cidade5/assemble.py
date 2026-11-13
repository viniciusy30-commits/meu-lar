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
                tx, tz = self.nodes[tgt]
                path = [(x0, z0), ((x0 + tx) / 2, (z0 + tz) / 2), (tx, tz)]
                if math.hypot(tx - x0, tz - z0) < 420 and not self.crosses(path, ()) and not any(self.geo.is_water(*q) for q in path):
                    self.edges.append({'a': r, 'b': tgt, 'p': path, 'lvl': 0, 'kind': 'n', 'name': 'Av. da Lagoa'}); added += 1; break
        self.ring = idx

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
        for tag, rb, name in (('W', RED_BRIDGE_W, 'Ponte Vermelha Oeste'), ('E', RED_BRIDGE_E, 'Ponte Vermelha Leste')):
            z = rb['z']
            a = self.add_node(rb['x_a'], z); b = self.add_node(rb['x_b'], z)
            self.edges.append({'a': a, 'b': b, 'p': [(rb['x_a'], z), (rb['x_b'], z)], 'lvl': 3, 'kind': 'redbridge', 'name': name})
            self.red.append({'name': name, 'z': z, 'x_a': rb['x_a'], 'x_b': rb['x_b'], 'towers': rb['towers'], 'deck': rb['deck']})
            # estrada de montanha ate o portal do tunel (borda do mapa)
            px, pz = rb['portal']; pn = self.add_node(px, pz)
            sgn = -1 if tag == 'W' else 1
            mid = [(rb['x_a'] + sgn * 70, z + 10), (rb['x_a'] + sgn * 120, z - 25), (rb['x_a'] + sgn * 170, z - 60), (px - sgn * 30, pz + 15)]
            self.edges.append({'a': a, 'b': pn, 'p': [(rb['x_a'], z)] + mid + [(px, pz)], 'lvl': 3, 'kind': 'n', 'name': 'Rodovia do Tunel ' + tag})
            self.nodes[pn].append('portal')
            # acesso do lado da cidade: curva suave ate o no mais proximo da rede
            cands = sorted((i for i in range(len(self.nodes)) if len(self.nodes[i]) == 2 and i != b and abs(self.nodes[i][0] - rb['x_b']) > 60),
                           key=lambda i: math.hypot(self.nodes[i][0] - rb['x_b'] - (260 if tag == 'W' else -260), self.nodes[i][1] - z - 60))
            for tgt in cands[:40]:
                tx, tz = self.nodes[tgt]
                mid = [((rb['x_b'] * 2 + tx) / 3, z + (tz - z) * 0.25), ((rb['x_b'] + tx * 2) / 3, z + (tz - z) * 0.75)]
                path = [(rb['x_b'], z)] + mid + [(tx, tz)]
                if not self.crosses(path, (b, tgt)) and not any(self.geo.is_water(*q) for q in path[1:]):
                    self.edges.append({'a': b, 'b': tgt, 'p': path, 'lvl': 3, 'kind': 'n', 'name': 'Acesso ' + name}); break

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
        self.portals = {i for i, n in enumerate(self.nodes) if len(n) > 2}

def build(geo):
    c = City(geo)
    c.lagoon_ring(); c.river_bridges(); c.connect_components(); c.red_bridges(); c.make_rounds(); c.flags()
    return c
