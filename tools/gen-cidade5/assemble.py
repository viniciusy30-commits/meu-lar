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
        self.edges = [{'a': e['a'], 'b': e['b'], 'p': [tuple(q) for q in e['p']], 'lvl': e['lvl'], 'kind': 'n', 'name': e.get('name', ''), **({'protect': True} if e.get('protect') else {})} for e in edges]
        self.rounds = []
        self.noconnect = []
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
            self.add_edge(idx[q], idx[(q + 1) % len(idx)], seg, 0, 'n', 'Anel da Lagoa'); self.edges[-1]['protect'] = True
        ring = set(idx); added = 0
        for k in range(0, len(idx), 3):          # 4 ligacoes: N, L, S, O
            r = idx[k]; x0, z0 = self.nodes[r]
            cands = sorted((i for i in range(len(self.nodes)) if i not in ring and len(self.nodes[i]) == 2), key=lambda i: math.hypot(self.nodes[i][0] - x0, self.nodes[i][1] - z0))
            for tgt in cands[:30]:
                tx, tz = self.nodes[tgt][:2]
                path = [(x0, z0), ((x0 + tx) / 2, (z0 + tz) / 2), (tx, tz)]
                if math.hypot(tx - x0, tz - z0) < 420 and not self.crosses(path, ()) and not self.too_close(path) and not any(self.geo.is_water(*q) for q in path):
                    self.edges.append({'a': r, 'b': tgt, 'p': path, 'lvl': 0, 'kind': 'n', 'name': 'Av. da Lagoa', 'protect': True}); added += 1; break
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

    def crosses_except(self, path, k0):
        from network import seg_inter
        for k, e in enumerate(self.edges):
            if k == k0 or e['kind'] in ('bridge', 'redbridge'): continue
            for a, b in zip(e['p'], e['p'][1:]):
                for c_, d_ in zip(path, path[1:]):
                    r = seg_inter(a, b, c_, d_)
                    if r and 0.02 < r[0] < 0.98 and 0.02 < r[1] < 0.98: return True
        return False

    def add_beach_avenue(self):
        """Av. Beira-Mar: contorno a 58 m do mar; ligada a rede por ruas coletoras a cada ~230 m"""
        import shore
        self.beach_nodes = []
        made = sum(1 for e in self.edges if e.get('name') == 'Av. Beira-Mar')      # a avenida ja vem da rede (network.generate)
        self.beach_made = made
        # Ponte da Orla: liga as duas metades da Av. Beira-Mar sobre a foz do rio
        deg = defaultdict(int)
        for e in self.edges: deg[e['a']] += 1; deg[e['b']] += 1
        ends = sorted({n for e in self.edges if e.get('name') == 'Av. Beira-Mar' for n in (e['a'], e['b']) if deg[n] == 1})
        best = None
        for i in ends:
            for j in ends:
                if i >= j: continue
                xi, zi = self.nodes[i][:2]; xj, zj = self.nodes[j][:2]
                d = math.hypot(xi - xj, zi - zj)
                if d < 380 and self.geo.is_water((xi + xj) / 2, (zi + zj) / 2) and (best is None or d < best[0]): best = (d, i, j)
        if best:
            d, i, j = best
            self.add_edge(i, j, [], 0, 'bridge', 'Ponte da Orla'); self.edges[-1]['protect'] = True
        # conectores: amostra pontos da avenida e liga ao ponto mais proximo da rede
        for k0 in [k for k, e in enumerate(self.edges) if e.get('name') == 'Av. Beira-Mar']:
            pass
        links = 0
        for _round in range(1):
            ks = [k for k, e in enumerate(self.edges) if e.get('name') == 'Av. Beira-Mar' and e.get('protect')]
            for k in ks:
                e = self.edges[k]; L = elen(e['p']); s = 70.0
                targets = []
                while s < L - 60: targets.append(s); s += 230.0
                for s in targets:
                    # ponto da avenida em s (a aresta pode ter sido dividida: procura pela aresta atual mais proxima)
                    pt = None; acc = 0.0
                    for p, q in zip(e['p'], e['p'][1:]):
                        sl = math.hypot(q[0] - p[0], q[1] - p[1])
                        if acc + sl >= s: f = (s - acc) / (sl or 1); pt = (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f); break
                        acc += sl
                    if pt is None: continue
                    # procura a rede mais proxima que NAO seja avenida da praia
                    best = None
                    for kk, ee in enumerate(self.edges):
                        if ee.get('protect') or ee['kind'] == 'redbridge': continue
                        for i, (p, q) in enumerate(zip(ee['p'], ee['p'][1:])):
                            dx, dz = q[0] - p[0], q[1] - p[1]; L2 = dx * dx + dz * dz
                            if L2 < 1e-9: continue
                            t = max(0.0, min(1.0, ((pt[0] - p[0]) * dx + (pt[1] - p[1]) * dz) / L2)); px, pz = p[0] + dx * t, p[1] + dz * t
                            d = math.hypot(px - pt[0], pz - pt[1])
                            if 25 < d < 330 and (best is None or d < best[0]): best = (d, kk, i, (px, pz))
                    if not best: continue
                    d, kk, i, Q = best
                    path = [pt, Q]
                    if self.crosses(path, ()) or any(self.geo.is_water(*q_) for q_ in path): continue
                    if abs(self.geo.height(*Q) - self.geo.height(*pt)) / d > 0.09: continue
                    # divide a avenida em pt e a rede em Q
                    na_ = self._split_any(pt); nq = self._split_edge_near(kk, i, Q)
                    if na_ is None or nq is None: continue
                    self.edges.append({'a': na_, 'b': nq, 'p': [pt, Q], 'lvl': 1, 'kind': 'n', 'name': 'Acesso a orla', 'protect': True}); links += 1
                    break
        self.beach_links = links

    def _split_any(self, pt):
        # divide a aresta protegida da avenida que passa por pt
        for k, e in enumerate(self.edges):
            if not e.get('protect') or e.get('name') != 'Av. Beira-Mar': continue
            for i, (p, q) in enumerate(zip(e['p'], e['p'][1:])):
                dx, dz = q[0] - p[0], q[1] - p[1]; L2 = dx * dx + dz * dz
                if L2 < 1e-9: continue
                t = ((pt[0] - p[0]) * dx + (pt[1] - p[1]) * dz) / L2
                if 0 <= t <= 1 and math.hypot(p[0] + dx * t - pt[0], p[1] + dz * t - pt[1]) < 0.6:
                    e2 = self.split_edge(k, i, pt); return e2
        return None

    def _split_edge_near(self, k, seg, Q):
        e = self.edges[k]
        if seg >= len(e['p']) - 1: return None
        return self.split_edge(k, seg, Q)

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
                if dwater < 35 and e['lvl'] >= 1:
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
                    mxp, mzp = path[1][0], path[1][1]
                    if any(math.hypot(mxp - ux, mzp - uz) < 90 for ux, uz in self.noconnect): continue
                    if abs(self.geo.height(tx, tz) - self.geo.height(x, z)) / d > 0.10: continue
                    if any({ee['a'], ee['b']} == {i, t} for ee in self.edges): continue
                    if self.crosses(path, ()) or self.too_close(path): continue
                    self.edges.append({'a': i, 'b': t, 'p': path, 'lvl': max(e['lvl'], 1) if e['lvl'] < 2 else 2, 'kind': 'n', 'name': 'Ligacao'}); done = True; break
                if done: changed = True; break
                # 3) bolsao de retorno so em rua local de 60..320 m
                if e['lvl'] == 2 and 60 <= L <= 320:
                    self.legit_xy[(round(x, 2), round(z, 2))] = 'bolsao'; continue
                # 4) sem sentido: apaga o trecho (a Av. Beira-Mar e as ligacoes da orla nunca sao apagadas: terminam em cais/praia)
                if e.get('protect'): self.legit_xy[(round(x, 2), round(z, 2))] = 'bolsao' if e.get('name') == 'Av. Beira-Mar' else 'cais'; continue
                self.edges.pop(k); changed = True; break
            if not changed: break
        self.drop_unused()

    def contract_short(self, min_len=40.0):
        """funde nos ligados por trechos muito curtos (Y e cruzamentos colados viram um cruzamento so)"""
        n = 0
        for _ in range(500):
            deg, inc = self.degrees(); best = None
            pn = {x for ed in self.edges if ed.get('protect') and ed.get('name') == 'Anel da Lagoa' for x in (ed['a'], ed['b'])}
            for k, e in enumerate(self.edges):
                if e['kind'] != 'n' or e['a'] == e['b']: continue
                if len(self.nodes[e['a']]) > 2 or len(self.nodes[e['b']]) > 2: continue
                if e.get('protect') or ((e['a'] in pn or e['b'] in pn) and elen(e['p']) > 14.0): continue
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

    def arm_dir(self, k, node, dist=26.0):
        e = self.edges[k]; p = e['p'] if e['a'] == node else e['p'][::-1]
        acc = 0.0
        for a, b in zip(p, p[1:]):
            acc += math.hypot(b[0] - a[0], b[1] - a[1])
            if acc >= dist: return math.atan2(b[1] - p[0][1], b[0] - p[0][0])
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

    def fix_acute(self, min_gap=math.radians(72.0)):
        """remove a rua de menor hierarquia que sai de um cruzamento colada demais a outra (cantos que nao se desenham bem)"""
        removed = 0
        for _ in range(300):
            deg, inc = self.degrees(); victim = None
            for ni, ks in inc.items():
                if len(ks) < 3 or len(self.nodes[ni]) > 2: continue
                angs = {d_: sorted((self.arm_dir(k, ni, d_), k) for k in ks) for d_ in (12.0, 26.0)}
                for d_, ang in angs.items():
                  for q in range(len(ang)):
                    a, b = ang[q], ang[(q + 1) % len(ang)]
                    gap = (b[0] - a[0]) % (2 * math.pi)
                    if gap < min_gap:
                        ka, kb = a[1], b[1]
                        cand = sorted((ka, kb), key=lambda k: (-self.edges[k]['lvl'], elen(self.edges[k]['p'])))
                        for k in cand:
                            if self.edges[k]['kind'] == 'n' and not self.edges[k].get('protect') and self.connected_without(k): victim = k; break
                    if victim is not None: break
                if victim is not None: break
            if victim is None: break
            self.edges.pop(victim); removed += 1
        self.drop_unused(); self.acute_removed = removed

    def dedupe(self):
        """remove arestas REPETIDAS (mesmas pontas e mesmo tracado); dois caminhos diferentes entre os mesmos nos (ex.: as duas metades de um anel) ficam"""
        def mid(e):
            p = e['p']; L = elen(p) / 2; acc = 0.0
            for u, v in zip(p, p[1:]):
                s = math.hypot(v[0] - u[0], v[1] - u[1])
                if acc + s >= L: f = (L - acc) / (s or 1); return (u[0] + (v[0] - u[0]) * f, u[1] + (v[1] - u[1]) * f)
                acc += s
            return p[-1][:2]
        seen = {}; out = []
        for e in self.edges:
            k = frozenset((e['a'], e['b']))
            if e['a'] != e['b'] and k in seen:
                m = mid(e)
                if any(math.hypot(m[0] - q[0], m[1] - q[1]) < 15.0 for q in seen[k]): continue
            seen.setdefault(k, []).append(mid(e)); out.append(e)
        self.edges = out

    def clean_polylines(self):
        """tira espinhos/laços de curto alcance das polilinhas (ficam depois de fundir nos) e pontos quase repetidos"""
        n_fix = 0
        for e in self.edges:
            p = e['p']; changed = True
            while changed and len(p) > 2:
                changed = False
                for i in range(1, len(p) - 1):
                    v1 = (p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]); v2 = (p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1])
                    l1 = math.hypot(*v1); l2 = math.hypot(*v2)
                    if l1 < 2.5 or l2 < 2.5 or (l1 * l2 > 0 and (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2) < -0.25):
                        del p[i]; changed = True; n_fix += 1; break
            e['p'] = p
        self.polys_fixed = n_fix

    def smooth_polylines(self, passes=2):
        """arredonda curvas fechadas (corte de cantos de Chaikin); as pontas (nos) ficam exatamente onde estao"""
        for e in self.edges:
            if e['kind'] != 'n': continue
            p = [tuple(q) for q in e['p']]
            for _ in range(passes):
                if len(p) < 3: break
                out = [p[0]]
                for i in range(len(p) - 1):
                    a_, b_ = p[i], p[i + 1]
                    L = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
                    f = min(0.25, 14.0 / max(L, 1e-6)) if (i > 0 and i < len(p) - 2) else min(0.25, 14.0 / max(L, 1e-6))
                    q0 = (a_[0] + (b_[0] - a_[0]) * f, a_[1] + (b_[1] - a_[1]) * f); q1 = (b_[0] - (b_[0] - a_[0]) * f, b_[1] - (b_[1] - a_[1]) * f)
                    if i > 0: out.append(q0)
                    if i < len(p) - 2: out.append(q1)
                out.append(p[-1])
                p = out
            e['p'] = p

    def merge_degree2(self):
        """nos de grau 2 sem funcao (so uma emenda entre dois trechos) somem: os dois trechos viram uma polilinha so"""
        merged = 0
        for _ in range(400):
            deg, inc = self.degrees(); did = False
            lx_ = getattr(self, 'legit_xy', {})
            special = set(getattr(self, 'lookouts', [])) | {i for i, n in enumerate(self.nodes) if (round(n[0], 2), round(n[1], 2)) in lx_} | {r['node'] for r in self.rounds}
            for ni, ks in inc.items():
                if len(ks) != 2 or ni in special or len(self.nodes[ni]) > 2: continue
                e1, e2 = self.edges[ks[0]], self.edges[ks[1]]
                if e1['kind'] != 'n' or e2['kind'] != 'n' or ks[0] == ks[1]: continue
                p1 = e1['p'] if e1['b'] == ni else e1['p'][::-1]; o1 = e1['a'] if e1['b'] == ni else e1['b']
                p2 = e2['p'] if e2['a'] == ni else e2['p'][::-1]; o2 = e2['b'] if e2['a'] == ni else e2['a']
                if o1 == o2: continue
                new = {'a': o1, 'b': o2, 'p': list(p1) + list(p2[1:]), 'lvl': min(e1['lvl'], e2['lvl']) if (e1.get('protect') or e2.get('protect')) else max(e1['lvl'], e2['lvl']), 'kind': 'n', 'name': e1['name'] or e2['name'], 'protect': bool(e1.get('protect') or e2.get('protect'))}
                for kk in sorted(ks, reverse=True): self.edges.pop(kk)
                self.edges.append(new); did = True; merged += 1; break
            if not did: break
        self.drop_unused(); self.merged2 = merged

    def simplify_polylines(self, tol=3.0):
        import network
        for e in self.edges:
            if e['kind'] != 'n' or len(e['p']) < 3: continue
            e['p'] = [tuple(q) for q in network.rdp([tuple(q) for q in e['p']], tol)]

    def fillet_edge(self, e):
        HALF = {0: 14.0, 1: 10.0, 2: 7.5, 3: 18.0}
        p = [tuple(q) for q in e['p']]
        if len(p) < 3: return
        h = HALF[min(e['lvl'], 3)]
        out = [p[0]]
        for i in range(1, len(p) - 1):
            v1 = (p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]); v2 = (p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1])
            L1 = math.hypot(*v1); L2 = math.hypot(*v2)
            if L1 < 1e-6 or L2 < 1e-6: out.append(p[i]); continue
            u1 = (v1[0] / L1, v1[1] / L1); u2 = (v2[0] / L2, v2[1] / L2)
            dot = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1])); th = math.acos(dot)
            if th < 0.08: out.append(p[i]); continue
            R = max(1.4 * h, 14.0); t = R * math.tan(th / 2)
            tmax = 0.48 * min(L1, L2)
            if t > tmax: t = tmax; R = t / max(math.tan(th / 2), 1e-6)
            T1 = (p[i][0] - u1[0] * t, p[i][1] - u1[1] * t); T2 = (p[i][0] + u2[0] * t, p[i][1] + u2[1] * t)
            sign = 1.0 if (u1[0] * u2[1] - u1[1] * u2[0]) > 0 else -1.0
            n1 = (-u1[1] * sign, u1[0] * sign); C = (T1[0] + n1[0] * R, T1[1] + n1[1] * R)
            a0 = math.atan2(T1[1] - C[1], T1[0] - C[0]); k = max(2, int(th * R / 4.0))
            for q in range(k + 1):
                ang = a0 + sign * th * q / k
                out.append((C[0] + math.cos(ang) * R, C[1] + math.sin(ang) * R))
        out.append(p[-1]); e['p'] = out

    def fillet_polylines(self):
        """substitui cada curva por um arco de raio >= 1,4 x meia-largura da rua (limitado pelo comprimento dos trechos)"""
        for e in self.edges:
            if e['kind'] == 'n': self.fillet_edge(e)

    def relax_tight_curves(self, passes=3):
        """curvas mais fechadas do que a faixa externa aguenta (raio < offset + 8 m) ganham suavizacao extra"""
        import traffic as TR
        fixed = 0
        for e in self.edges:
            if e['kind'] != 'n' or len(e['p']) < 3: continue
            need = TR.lane_offsets(min(e['lvl'], 2))[-1] + 7.0
            if TR.min_radius(e['p']) >= need: continue
            p = [tuple(q) for q in e['p']]
            for _ in range(passes):
                out = [p[0]]
                for i in range(len(p) - 1):
                    a_, b_ = p[i], p[i + 1]; L = math.hypot(b_[0] - a_[0], b_[1] - a_[1]); f = min(0.25, 12.0 / max(L, 1e-6))
                    if i > 0: out.append((a_[0] + (b_[0] - a_[0]) * f, a_[1] + (b_[1] - a_[1]) * f))
                    if i < len(p) - 2: out.append((b_[0] - (b_[0] - a_[0]) * f, b_[1] - (b_[1] - a_[1]) * f))
                out.append(p[-1]); p = out
                if TR.min_radius(p) >= need: break
            e['p'] = p
            for _try in range(4):                                   # ainda apertada: retifica a regiao e arredonda de novo
                if TR.min_radius(e['p']) >= need: break
                rs = TR.resample(e['p'], 6.0); bad = None
                for i in range(1, len(rs) - 1):
                    A, B_, C_ = rs[i - 1], rs[i], rs[i + 1]
                    ab = math.hypot(B_[0] - A[0], B_[1] - A[1]); bc = math.hypot(C_[0] - B_[0], C_[1] - B_[1]); ca = math.hypot(A[0] - C_[0], A[1] - C_[1])
                    ar = abs((B_[0] - A[0]) * (C_[1] - A[1]) - (B_[1] - A[1]) * (C_[0] - A[0]))
                    if ar > 1e-6 and ab * bc * ca / (2 * ar) < need: bad = B_; break
                if bad is None: break
                if not self.local_bezier(e, bad, need):
                    keep = [e['p'][0]] + [q for q in e['p'][1:-1] if math.hypot(q[0] - bad[0], q[1] - bad[1]) > 26.0] + [e['p'][-1]]
                    e['p'] = keep; self.fillet_edge(e)
            fixed += 1
        self.curves_relaxed = fixed

    def local_bezier(self, e, bad, need):
        """troca o trecho de +-span m em volta da curva apertada por uma curva de Bezier tangente (raio maior)"""
        import traffic as TR
        p = e['p']; cum = [0.0]
        for a_, b_ in zip(p, p[1:]): cum.append(cum[-1] + math.hypot(b_[0] - a_[0], b_[1] - a_[1]))
        L = cum[-1]
        sb = min(range(len(p)), key=lambda i: math.hypot(p[i][0] - bad[0], p[i][1] - bad[1])); s_bad = cum[sb]
        def at(s):
            s = min(max(s, 0.0), L)
            for i in range(len(p) - 1):
                if cum[i + 1] >= s:
                    f = (s - cum[i]) / ((cum[i + 1] - cum[i]) or 1); return (p[i][0] + (p[i + 1][0] - p[i][0]) * f, p[i][1] + (p[i + 1][1] - p[i][1]) * f), (p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1])
            return p[-1], (1, 0)
        for span in (30.0, 45.0, 65.0, 90.0):
            s0, s1 = max(s_bad - span, 6.0), min(s_bad + span, L - 6.0)
            if s1 - s0 < 25: continue
            P0, d0 = at(s0); P1, d1 = at(s1); l0 = math.hypot(*d0) or 1; l1 = math.hypot(*d1) or 1
            ch = math.hypot(P1[0] - P0[0], P1[1] - P0[1]); k = 0.42 * ch
            new = TR.bez(P0, (P0[0] + d0[0] / l0 * k, P0[1] + d0[1] / l0 * k), (P1[0] - d1[0] / l1 * k, P1[1] - d1[1] / l1 * k), P1, 22)
            q = [pt for pt, c_ in zip(p, cum) if c_ < s0] + [tuple(n_) for n_ in new] + [pt for pt, c_ in zip(p, cum) if c_ > s1]
            if TR.min_radius(q) >= need * 0.98 and not self.crosses_except(q, self.edges.index(e)):
                e['p'] = q; return True
        return False

    def drop_tight_edges(self):
        import traffic as TR
        n = 0
        for _ in range(20):
            hit = None
            for k, e in enumerate(self.edges):
                if e['kind'] != 'n': continue
                need = TR.lane_offsets(min(e['lvl'], 2))[-1] + 7.0
                if TR.min_radius(e['p']) < need:
                    if e.get('protect'): continue
                    if self.connected_without(k): hit = k; break
                    # essencial: refaz a rua como uma curva de Bezier suave entre as duas pontas, mantendo as direcoes de chegada
                    p = e['p']; A, B_ = p[0], p[-1]
                    def dirn(pts):
                        acc = 0.0
                        for s_, t_ in zip(pts, pts[1:]):
                            acc += math.hypot(t_[0] - s_[0], t_[1] - s_[1])
                            if acc >= 18.0: return ((t_[0] - pts[0][0]), (t_[1] - pts[0][1]))
                        return ((pts[-1][0] - pts[0][0]), (pts[-1][1] - pts[0][1]))
                    dA = dirn(p); dB = dirn(p[::-1]); la = math.hypot(*dA) or 1; lb = math.hypot(*dB) or 1
                    ch = math.hypot(B_[0] - A[0], B_[1] - A[1]); kk = 0.38 * ch
                    P1 = (A[0] + dA[0] / la * kk, A[1] + dA[1] / la * kk); P2 = (B_[0] + dB[0] / lb * kk, B_[1] + dB[1] / lb * kk)
                    new = TR.bez(A, P1, P2, B_, 24)
                    if TR.min_radius(new) >= need * 0.95 and not self.crosses_except(new, k):
                        e['p'] = [tuple(q) for q in new]; n += 1; continue
            if hit is None: break
            self.edges.pop(hit); n += 1; self.drop_unused()
        if n:
            self.fix_dead_ends(); self.connect_components(); self.resolve_bulbs(); self.merge_degree2(); self.clean_polylines()
        self.tight_dropped = n

    def fix_close_parallel(self, margin=1.5, max_iter=120):
        """duas ruas cujos eixos chegam mais perto que (meia-largura A + meia-largura B): calcadas/pistas se sobrepoem -> remove a de menor hierarquia"""
        import numpy as np
        HALF = {0: 14.0, 1: 10.0, 2: 7.5, 3: 18.0}
        removed = 0
        for _ in range(max_iter):
            segs = []   # (x0,z0,x1,z1,edge)
            for k, e in enumerate(self.edges):
                if e['kind'] == 'redbridge': continue
                for p, q in zip(e['p'], e['p'][1:]): segs.append((p[0], p[1], q[0], q[1], k))
            if not segs: break
            S = np.array(segs, float); A = S[:, :2]; D = S[:, 2:4] - S[:, :2]; L2 = (D ** 2).sum(1) + 1e-9; K = S[:, 4].astype(int)
            worst = None
            for k, e in enumerate(self.edges):
                if e['kind'] != 'n': continue
                Le = elen(e['p'])
                ha = HALF[min(e['lvl'], 3)]
                for t in np.arange(40.0, Le - 40.0, 7.0):
                    # ponto em t
                    acc = 0.0; pt = None
                    for p, q in zip(e['p'], e['p'][1:]):
                        sl = math.hypot(q[0] - p[0], q[1] - p[1])
                        if acc + sl >= t: f = (t - acc) / (sl or 1); pt = (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f); break
                        acc += sl
                    if pt is None: continue
                    u = np.clip(((pt[0] - A[:, 0]) * D[:, 0] + (pt[1] - A[:, 1]) * D[:, 1]) / L2, 0, 1)
                    dist = np.hypot(A[:, 0] + u * D[:, 0] - pt[0], A[:, 1] + u * D[:, 1] - pt[1])
                    for j in np.nonzero((dist < 40) & (K != k))[0]:
                        eb = self.edges[K[j]]; hb = HALF[min(eb['lvl'], 3)]
                        need = ha + hb - margin
                        if dist[j] >= need: continue
                        # arestas que dividem um no: ignora perto desse no (cruzamento)
                        shared = {e['a'], e['b']} & {eb['a'], eb['b']}
                        near_shared = False
                        for n_ in shared:
                            nx_, nz_ = self.nodes[n_][:2]
                            if math.hypot(pt[0] - nx_, pt[1] - nz_) < 75: near_shared = True
                        if near_shared: continue
                        sev = need - dist[j]
                        if worst is None or sev > worst[0]: worst = (sev, k, int(K[j]))
            if worst is None: break
            _, ka, kb = worst
            ea, eb = self.edges[ka], self.edges[kb]
            pick = sorted((ka, kb), key=lambda kk: (-self.edges[kk]['lvl'], elen(self.edges[kk]['p'])))
            done = False
            for kk in pick:
                if self.edges[kk]['kind'] == 'n' and not self.edges[kk].get('protect') and self.connected_without(kk): self.edges.pop(kk); done = True; break
            if not done: break
            removed += 1
        self.drop_unused(); self.close_removed = removed

    def repair_overlaps(self, max_iter=60, verbose=True):
        """gera o chao com altura zero, acha onde calcada/ilha/canteiro cobre asfalto e remove/funde a rua menos importante ali"""
        import numpy as np
        import ground, validate_ground
        removed = 0; skip = set()
        for it in range(max_iter):
            self.rounds = []; self.make_rounds(); self.flags()
            hf = np.zeros((int(WZ / 8) + 1, int(WX / 8) + 1)); gr = ground.Ground(self, self.geo, hf, [0.0] * len(self.nodes)); gr.build()
            M = validate_ground.raster(gr, ['asphalt', 'sidewalk', 'median', 'island'])
            er = lambda m: m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
            E = {k: er(v) for k, v in M.items()}
            bad = (E['asphalt'] & (E['sidewalk'] | E['median'] | E['island']))
            ys, xs = np.nonzero(bad)
            if len(xs) < 6: break
            cell = defaultdict(int)
            for x, y in zip(xs, ys): cell[(int(x // 30), int(y // 30))] += 1
            done = False
            for (cx_, cz_), cnt in sorted(cell.items(), key=lambda kv: -kv[1]):
                if cnt < 3 or (cx_, cz_) in skip: continue
                cx, cz = cx_ * 30 + 15, cz_ * 30 + 15
                if verbose: print(f'  reparo {it}: {len(xs)} m2 sobrepostos; tentando ({cx},{cz}) {cnt} m2')
                cands = []
                for k, e in enumerate(self.edges):
                    if e['kind'] != 'n' or e['a'] in self.lookouts or e['b'] in self.lookouts: continue
                    dmin = min(math.hypot(p[0] - cx, p[1] - cz) for p in e['p'])
                    for p, q in zip(e['p'], e['p'][1:]):
                        L = math.hypot(q[0] - p[0], q[1] - p[1])
                        for t in range(1, int(L // 10) + 1):
                            dmin = min(dmin, math.hypot(p[0] + (q[0] - p[0]) * t * 10 / L - cx, p[1] + (q[1] - p[1]) * t * 10 / L - cz))
                    if dmin < 42 and not e.get('protect'): cands.append((-e['lvl'], elen(e['p']), k))
                for _, L, k in sorted(cands, key=lambda t: (t[0], t[1])):
                    if self.connected_without(k): self.edges.pop(k); done = True; break
                if done: break
                skip.add((cx_, cz_))
            if not done: break
            removed += 1; self.noconnect.append((cx, cz))
            self.drop_unused(); self.dedupe()
            if it % 4 == 3: self.fix_acute()
        self.fix_dead_ends(); self.connect_components(); self.drop_unused(); self.merge_degree2(); self.clean_polylines(); self.simplify_polylines(); self.fillet_polylines()
        self.rounds = []; self.make_rounds(); self.flags(); self.repairs = removed

    # ------------------------------------------------------------ becos sem saida com bolsao bloqueado
    def nearest_on_edges(self, x, z, skip_edge=None, maxd=1e9):
        best = None
        for k, e in enumerate(self.edges):
            if k == skip_edge or e['kind'] == 'redbridge': continue
            for i, (p, q) in enumerate(zip(e['p'], e['p'][1:])):
                dx, dz = q[0] - p[0], q[1] - p[1]; L2 = dx * dx + dz * dz
                if L2 < 1e-9: continue
                t = max(0.0, min(1.0, ((x - p[0]) * dx + (z - p[1]) * dz) / L2))
                px, pz = p[0] + dx * t, p[1] + dz * t; d = math.hypot(px - x, pz - z)
                if d < maxd and (best is None or d < best[0]): best = (d, k, i, (px, pz), t)
        return best

    def split_edge(self, k, seg, pt):
        """cria um no em pt (sobre a polilinha da aresta k, entre os vertices seg e seg+1) e divide a aresta"""
        e = self.edges[k]
        ni = self.add_node(pt[0], pt[1])
        p1 = list(e['p'][:seg + 1]) + [pt]; p2 = [pt] + list(e['p'][seg + 1:])
        e1 = dict(e); e1['b'] = ni; e1['p'] = p1
        e2 = dict(e); e2['a'] = ni; e2['p'] = p2
        self.edges[k] = e1; self.edges.append(e2)
        return ni

    def bulb_blocked_xy(self, ni, k_own, Rb):
        nx, nz = self.nodes[ni][:2]
        HALF = {0: 14.0, 1: 10.0, 2: 7.5, 3: 18.0}
        for k, e in enumerate(self.edges):
            if k == k_own or e['kind'] == 'redbridge': continue
            for p, q in zip(e['p'], e['p'][1:]):
                L = math.hypot(q[0] - p[0], q[1] - p[1]) or 1e-9
                for t in range(0, int(L // 3) + 2):
                    f = min(1.0, t * 3.0 / L); x, z = p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f
                    if math.hypot(x - nx, z - nz) < Rb + 2.6 + HALF[min(e['lvl'], 3)] * 0.6: return True
        return False

    def resolve_bulbs(self):
        """nenhuma rua 'cortada': bolsao bloqueado -> liga na rua vizinha (T), ou encurta a rua ate caber o bolsao, ou apaga o toco"""
        fixed = {'conectado': 0, 'encurtado': 0, 'apagado': 0}
        for _ in range(60):
            deg, inc = self.degrees(); lx = getattr(self, 'legit_xy', {}); target = None
            for ni, ks in inc.items():
                if len(ks) != 1 or len(self.nodes[ni]) > 2: continue
                if lx.get((round(self.nodes[ni][0], 2), round(self.nodes[ni][1], 2))) != 'bolsao': continue
                if self.bulb_blocked_xy(ni, ks[0], 11.0): target = (ni, ks[0]); break
            if not target: break
            ni, k = target; e = self.edges[k]
            pts = e['p'] if e['a'] == ni else e['p'][::-1]          # pts[0] = ponta morta
            x, z = pts[0]
            hx, hz = pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]; hl = math.hypot(hx, hz) or 1; hx, hz = hx / hl, hz / hl   # sentido para fora da rua (alem da ponta)
            done = False
            # 1) liga numa rua proxima, a frente, em T (>= 60 graus)
            for _r in range(1):
                nb = self.nearest_on_edges(x + hx * 2, z + hz * 2, skip_edge=k, maxd=75.0)
                if not nb: break
                d, k2, seg, P, t = nb
                dx, dz = P[0] - x, P[1] - z; dl = math.hypot(dx, dz)
                if dl < 6 or dl > 75: break
                e2 = self.edges[k2]; ex, ez = e2['p'][seg + 1][0] - e2['p'][seg][0], e2['p'][seg + 1][1] - e2['p'][seg][1]; el = math.hypot(ex, ez) or 1
                ang = abs(((dx * ex + dz * ez) / (dl * el)))
                if ang > 0.5: break                                      # menos de 60 graus com a rua alvo
                if (dx * hx + dz * hz) / dl < 0.3: break                 # nao e "a frente" da rua
                path = [(x, z), P]
                if self.crosses(path, ()) or any(self.geo.is_water(*q) for q in path): break
                n2 = self.split_edge(k2, seg, P)
                self.edges.append({'a': ni, 'b': n2, 'p': [(x, z), P], 'lvl': e['lvl'], 'kind': 'n', 'name': ''})
                self.legit_xy.pop((round(x, 2), round(z, 2)), None); fixed['conectado'] += 1; done = True
            if done: self.drop_unused(); continue
            # 2) encurta a rua ate o bolsao caber (minimo 45 m sobrando)
            L = elen(e['p'])
            if L > 70:
                cut = 14.0
                for _s in range(8):
                    new = self.trim_end(e, ni, cut)
                    if new is None: break
                    nx_, nz_ = new
                    # recoloca o no na nova ponta
                    old = tuple(self.nodes[ni][:2]); self.nodes[ni][0], self.nodes[ni][1] = nx_, nz_
                    self.legit_xy.pop((round(old[0], 2), round(old[1], 2)), None); self.legit_xy[(round(nx_, 2), round(nz_, 2))] = 'bolsao'
                    if not self.bulb_blocked_xy(ni, k, 11.0): fixed['encurtado'] += 1; done = True; break
                    cut += 12.0
            if done: self.drop_unused(); continue
            # 3) apaga o toco
            self.edges.pop(k); self.legit_xy.pop((round(x, 2), round(z, 2)), None); fixed['apagado'] += 1
            self.drop_unused()
        self.bulbs_fixed = fixed

    def trim_end(self, e, ni, dist):
        """remove `dist` metros da ponta da aresta (no ni); devolve a nova ponta ou None"""
        p = list(e['p']) if e['a'] == ni else list(e['p'][::-1])
        total = elen(p)
        if total - dist < 45: return None
        acc = 0.0; out = [p[0]]; newpt = None
        for a_, b_ in zip(p, p[1:]):
            L = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
            if newpt is None and acc + L >= dist:
                f = (dist - acc) / (L or 1); newpt = (a_[0] + (b_[0] - a_[0]) * f, a_[1] + (b_[1] - a_[1]) * f); out = [newpt, b_]
            elif newpt is not None: out.append(b_)
            acc += L
        if newpt is None: return None
        e['p'] = out if e['a'] == ni else out[::-1]
        return newpt

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
    c.add_beach_avenue(); c.lagoon_ring(); c.river_bridges(); c.connect_components(); c.red_bridges(); c.fix_dead_ends(); c.connect_components(); c.dedupe(); c.contract_short(); c.fix_acute(); c.fix_dead_ends(); c.contract_short(); c.merge_degree2(); c.clean_polylines(); c.simplify_polylines(); c.fillet_polylines(); c.fix_close_parallel(); c.fix_dead_ends(); c.connect_components(); c.contract_short(); c.fix_acute(); c.fix_dead_ends(); c.connect_components(); c.merge_degree2(); c.clean_polylines(); c.simplify_polylines(); c.fillet_polylines(); c.make_rounds(); c.flags(); c.repair_overlaps(); c.fix_acute(); c.resolve_bulbs(); c.merge_degree2(); c.clean_polylines(); c.relax_tight_curves(); c.drop_tight_edges(); c.make_rounds(); c.flags()
    # rotatorias: reassocia o no pela POSICAO (drop_unused renumera os nos depois de make_rounds)
    for r in c.rounds:
        r['node'] = min(range(len(c.nodes)), key=lambda i: math.hypot(c.nodes[i][0] - r['x'], c.nodes[i][1] - r['z']))
    return c
