"""Rede viaria ORGANICA: campo de tensores + linhas de fluxo (hierarquia ave/col/loc), planarizacao e limpeza."""
import math, random
import numpy as np
from collections import defaultdict
from plan import *
import geo as G

# ---------------------------------------------------------------- campo de tensores (angulo da direcao principal)
def tensor_field(geo):
    X, Z = geo.X, geo.Z
    Tx = np.zeros_like(X); Tz = np.zeros_like(X)
    def add(theta, w):
        nonlocal Tx, Tz
        Tx = Tx + w * np.cos(2 * theta); Tz = Tz + w * np.sin(2 * theta)
    add(np.radians(8.0), 0.05 * np.ones_like(X))                                  # base global
    for cx, cz, s, a, w in ((2050, 1900, 560, 10, 1.0), (1250, 1900, 480, -24, 1.0), (3050, 1850, 520, 27, 1.0), (2150, 1100, 520, -8, 0.8),
                            (2200, 2450, 420, 38, 0.7), (1500, 2400, 330, -15, 0.8), (3000, 2400, 330, 5, 0.8)):
        add(np.radians(a), w * np.exp(-((X - cx) ** 2 + (Z - cz) ** 2) / (2 * s * s)))
    # radial em volta da lagoa e da praca do centro
    lx, lz = LAGOON[0], LAGOON[1]
    dx, dz = X - lx, Z - lz; r = np.hypot(dx, dz) + 1e-6
    add(np.arctan2(dz, dx) + 0.0, 1.35 * np.exp(-(r / 380.0) ** 2))
    add(np.arctan2(dz, dx) + math.pi / 2, 0.55 * np.exp(-(r / 300.0) ** 2))
    # alinha com agua (costa, rio, canais, lagoa)
    water = geo.water
    D = np.full(water.shape, 1e9); D[water] = 0
    for _ in range(2):   # chanfro
        for j in range(1, NZ):
            D[j, 1:] = np.minimum(D[j, 1:], np.minimum(D[j - 1, 1:], D[j, :-1]) + CELL)
        for j in range(NZ - 2, -1, -1):
            D[j, :-1] = np.minimum(D[j, :-1], np.minimum(D[j + 1, :-1], D[j, 1:]) + CELL)
        for j in range(NZ):
            for i in range(1, NX): D[j, i] = min(D[j, i], D[j, i - 1] + CELL)
            for i in range(NX - 2, -1, -1): D[j, i] = min(D[j, i], D[j, i + 1] + CELL)
    gz, gx = np.gradient(D, CELL)
    add(np.arctan2(gz, gx) + math.pi / 2, 1.5 * np.exp(-(D / 150.0) ** 2) * (D < 1e8))
    # colinas: acompanha as curvas de nivel
    hz, hx = np.gradient(geo.h, CELL)
    sl = np.hypot(hx, hz)
    add(np.arctan2(hz, hx) + math.pi / 2, 2.4 * np.clip((sl - 0.11) / 0.14, 0, 1))
    geo.D = D
    # ruido leve no angulo => ruas menos retas
    nz_ = (G.fbm(X, Z, 260.0, 3, 5) - 0.5) * 0.35
    th = 0.5 * np.arctan2(Tz, Tx) + nz_
    return np.cos(2 * th), np.sin(2 * th)

class Field:
    def __init__(self, geo):
        self.geo = geo; self.cx, self.cz = tensor_field(geo)
    def dirs(self, x, z):
        fx = min(max(x / CELL, 0), NX - 1.001); fz = min(max(z / CELL, 0), NZ - 1.001)
        i, j = int(fx), int(fz); a, b = fx - i, fz - j
        def bl(A): return (A[j, i] * (1 - a) + A[j, i + 1] * a) * (1 - b) + (A[j + 1, i] * (1 - a) + A[j + 1, i + 1] * a) * b
        c, s = bl(self.cx), bl(self.cz)
        th = 0.5 * math.atan2(s, c)
        return (math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))

# ---------------------------------------------------------------- tracado
class Occ:
    def __init__(self, cs=40.0): self.cs = cs; self.g = defaultdict(list)
    def add(self, x, z, lid, lvl): self.g[(int(x // self.cs), int(z // self.cs))].append((x, z, lid, lvl))
    def nearest(self, x, z, r, skip=-1, maxlvl=9):
        best = None; cs = self.cs; n = int(r // cs) + 1
        for a in range(int(x // cs) - n, int(x // cs) + n + 1):
            for b in range(int(z // cs) - n, int(z // cs) + n + 1):
                for (px, pz, lid, lvl) in self.g.get((a, b), ()):
                    if lid == skip or lvl > maxlvl: continue
                    d = math.hypot(px - x, pz - z)
                    if d < r and (best is None or d < best[0]): best = (d, px, pz, lid)
        return best

def trace_level(geo, fld, occs, lvl, dsep, maxslope, minor_factor, rng, lines):
    step = 9.0
    cs = dsep * 0.55
    cand = []
    for x in np.arange(0, WX, cs):
        for z in np.arange(0, WZ, cs):
            px, pz = x + rng.uniform(-0.45, 0.45) * cs, z + rng.uniform(-0.45, 0.45) * cs
            if 0 < px < WX and 0 < pz < WZ and geo.is_urban(px, pz): cand.append((px, pz))
    rng.shuffle(cand)
    made = 0
    for rnd in (0, 1, 0, 1):                       # alterna sentidos principal/secundario (Chen et al.)
        minor = bool(rnd)
        occ = occs[minor]
        ds = dsep * (minor_factor if minor else 1.0); dtest = 0.55 * ds
        for (sx, sz) in cand:
            if occ.nearest(sx, sz, 0.9 * ds, maxlvl=lvl): continue
            lid = len(lines) + 1000 * lvl + (500 if minor else 0)
            fwd = trace_dir(geo, fld, occ, sx, sz, minor, +1, step, dtest, maxslope, lid, lvl)
            bwd = trace_dir(geo, fld, occ, sx, sz, minor, -1, step, dtest, maxslope, lid, lvl)
            pts = bwd[::-1][:-1] + fwd if len(bwd) > 1 else fwd
            if len(pts) < 2: continue
            L = sum(math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]) for k in range(len(pts) - 1))
            if L < max(60.0, 1.1 * ds): continue
            lines.append({'pts': pts, 'lvl': lvl, 'id': lid})
            for (px, pz) in pts: occ.add(px, pz, lid, lvl)
            made += 1
    return made

def trace_dir(geo, fld, occ, x, z, minor, sign, step, dtest, maxslope, lid, lvl):
    pts = [(x, z)]; hx = hz = None
    prevh = geo.height(x, z)
    for it in range(900):
        a, b = fld.dirs(x, z)
        d = b if minor else a
        if hx is None: dx, dz = d[0] * sign, d[1] * sign
        else:
            if d[0] * hx + d[1] * hz < 0: d = (-d[0], -d[1])
            dx, dz = d
        # passo medio
        mx, mz = x + dx * step * 0.5, z + dz * step * 0.5
        a2, b2 = fld.dirs(mx, mz); d2 = b2 if minor else a2
        if d2[0] * dx + d2[1] * dz < 0: d2 = (-d2[0], -d2[1])
        nx_, nz_ = x + d2[0] * step, z + d2[1] * step
        if not geo.is_urban(nx_, nz_): break
        h2 = geo.height(nx_, nz_)
        if abs(h2 - prevh) / step > maxslope: break
        near = occ.nearest(nx_, nz_, dtest, skip=lid, maxlvl=lvl)
        if near:
            # estende ate encostar na linha vizinha (junta) ou desiste
            ex, ez = nx_, nz_; ok = False
            for k in range(int(1.7 * dtest / step) + 2):
                n2 = occ.nearest(ex, ez, step * 0.75, skip=lid, maxlvl=lvl)
                if n2: pts.append((n2[1], n2[2])); ok = True; break
                ex += d2[0] * step; ez += d2[1] * step
                if not geo.is_urban(ex, ez): break
            if not ok and len(pts) > 1: pts.pop()
            break
        if len(pts) > 3 and math.hypot(nx_ - pts[-4][0], nz_ - pts[-4][1]) < step * 1.2: break   # laco/volta
        hx, hz = d2[0], d2[1]
        x, z = nx_, nz_; prevh = h2
        pts.append((x, z))
    return pts

# ---------------------------------------------------------------- geometria
def rdp(pts, tol):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz) or 1e-9
    dm, im = 0, 0
    for k in range(1, len(pts) - 1):
        d = abs((pts[k][0] - a[0]) * dz - (pts[k][1] - a[1]) * dx) / L
        if d > dm: dm, im = d, k
    if dm > tol: return rdp(pts[:im + 1], tol)[:-1] + rdp(pts[im:], tol)
    return [a, b]

def seg_inter(p1, p2, p3, p4):
    d1x, d1z = p2[0] - p1[0], p2[1] - p1[1]; d2x, d2z = p4[0] - p3[0], p4[1] - p3[1]
    den = d1x * d2z - d1z * d2x
    if abs(den) < 1e-9: return None
    t = ((p3[0] - p1[0]) * d2z - (p3[1] - p1[1]) * d2x) / den
    u = ((p3[0] - p1[0]) * d1z - (p3[1] - p1[1]) * d1x) / den
    return t, u

def planarize(lines, snap=7.0):
    """quebra as linhas em todos os cruzamentos e devolve (nos, arestas)"""
    segs = []   # (p, q, line index)
    for li, ln in enumerate(lines):
        ln['pts'] = rdp(ln['pts'], 1.6)
        for a, b in zip(ln['pts'], ln['pts'][1:]): segs.append([a, b, li])
    grid = defaultdict(list)
    for si, (a, b, li) in enumerate(segs):
        for cx in range(int(min(a[0], b[0]) // 60), int(max(a[0], b[0]) // 60) + 1):
            for cz in range(int(min(a[1], b[1]) // 60), int(max(a[1], b[1]) // 60) + 1): grid[(cx, cz)].append(si)
    splits = defaultdict(set)
    for lst in grid.values():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                s1, s2 = segs[lst[i]], segs[lst[j]]
                if s1[2] == s2[2]: continue
                r = seg_inter(s1[0], s1[1], s2[0], s2[1])
                if r is None: continue
                t, u = r
                L1 = math.hypot(s1[1][0] - s1[0][0], s1[1][1] - s1[0][1]) or 1; L2 = math.hypot(s2[1][0] - s2[0][0], s2[1][1] - s2[0][1]) or 1
                e1, e2 = snap / L1, snap / L2
                if -e1 <= t <= 1 + e1 and -e2 <= u <= 1 + e2:
                    t = min(max(t, 0), 1); u = min(max(u, 0), 1)
                    # so conta se for cruzamento verdadeiro ou encosto de ponta
                    px, pz = s1[0][0] + (s1[1][0] - s1[0][0]) * t, s1[0][1] + (s1[1][1] - s1[0][1]) * t
                    splits[lst[i]].add((round(px, 2), round(pz, 2))); splits[lst[j]].add((round(px, 2), round(pz, 2)))
    # reconstroi cada linha com os pontos de corte
    pieces = []
    for li, ln in enumerate(lines):
        poly = []
        sl = [si for si, s in enumerate(segs) if s[2] == li] if False else None
    byline = defaultdict(list)
    for si, s in enumerate(segs): byline[s[2]].append(si)
    for li, sis in byline.items():
        poly = [segs[sis[0]][0]]; cuts = set()
        for si in sis:
            a, b, _ = segs[si]
            ps = sorted(splits.get(si, ()), key=lambda p: (p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2)
            for p in ps:
                if math.hypot(p[0] - poly[-1][0], p[1] - poly[-1][1]) > 0.5: poly.append(p); cuts.add(len(poly) - 1)
            if math.hypot(b[0] - poly[-1][0], b[1] - poly[-1][1]) > 0.5: poly.append(b)
        cuts.add(0); cuts.add(len(poly) - 1)
        if len(cuts) == 2 and math.hypot(poly[0][0] - poly[-1][0], poly[0][1] - poly[-1][1]) < 1.0 and len(poly) > 6:
            cuts.add(len(poly) // 2)          # laco fechado (anel da lagoa): divide ao meio
        cs = sorted(cuts)
        for u, v in zip(cs, cs[1:]):
            pieces.append({'pts': poly[u:v + 1], 'lvl': lines[li]['lvl'], 'name': lines[li].get('name', ''), 'protect': lines[li].get('protect', False)})
    return pieces

def build_graph(pieces, merge=9.0):
    # agrupa pontas/juncoes proximas em um unico no
    pts = []
    for pc in pieces: pts.append(pc['pts'][0]); pts.append(pc['pts'][-1])
    cell = defaultdict(list); rep = {}
    nodes = []
    def find(p):
        cx, cz = int(p[0] // merge), int(p[1] // merge)
        for a in (cx - 1, cx, cx + 1):
            for b in (cz - 1, cz, cz + 1):
                for k in cell.get((a, b), ()):
                    if math.hypot(nodes[k][0] - p[0], nodes[k][1] - p[1]) < merge: return k
        nodes.append(p); cell[(cx, cz)].append(len(nodes) - 1); return len(nodes) - 1
    edges = []
    for pc in pieces:
        a = find(pc['pts'][0]); b = find(pc['pts'][-1])
        if a == b: continue
        p = [nodes[a]] + pc['pts'][1:-1] + [nodes[b]]
        edges.append({'a': a, 'b': b, 'p': p, 'lvl': pc['lvl'], 'name': pc.get('name', ''), 'protect': pc.get('protect', False)})
    return nodes, edges

def clean(nodes, edges, min_dead=80.0):
    def elen(e): return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(e['p'], e['p'][1:]))
    # arestas duplicadas
    seen = {}; out = []
    for e in edges:
        k = (min(e['a'], e['b']), max(e['a'], e['b']))
        if k in seen:
            o = seen[k]
            if elen(e) < 1.15 * elen(o) and e['lvl'] < o['lvl']: o.update(e)
            continue
        seen[k] = e; out.append(e)
    edges = out
    for _ in range(6):   # poda pontas soltas curtas
        deg = defaultdict(int)
        for e in edges: deg[e['a']] += 1; deg[e['b']] += 1
        keep = []; ch = False
        for e in edges:
            if not e.get('protect') and (deg[e['a']] == 1 or deg[e['b']] == 1) and elen(e) < min_dead * (1.6 if e['lvl'] == 2 else 1.0): ch = True; continue
            keep.append(e)
        edges = keep
        if not ch: break
    # maior componente
    adj = defaultdict(list)
    for i, e in enumerate(edges): adj[e['a']].append(e['b']); adj[e['b']].append(e['a'])
    comp = {}; cid = 0
    for n in adj:
        if n in comp: continue
        st = [n]; comp[n] = cid
        while st:
            u = st.pop()
            for w in adj[u]:
                if w not in comp: comp[w] = cid; st.append(w)
        cid += 1
    cnt = defaultdict(int)
    for n, c in comp.items(): cnt[c] += 1
    edges = [e for e in edges if cnt[comp[e['a']]] >= 12]
    return nodes, edges

def orla_grid(geo, runs, lines, occs):
    """bairro da orla (estilo Joao Pessoa): ruas paralelas a praia a +110 m e +220 m da avenida e transversais a cada ~110 m
    saindo da Av. Beira-Mar para dentro da cidade (os quarteiroes de frente para o mar ficam entre a avenida e a 1a paralela)"""
    import shore
    gz, gx = np.gradient(geo.Dsea, CELL)
    def grad(x, z):
        j, i = geo.idx(x, z); l = math.hypot(gx[j, i], gz[j, i]) or 1e-9
        return gx[j, i] / l, gz[j, i] / l
    lid = 90
    for k, off in enumerate((ORLA_AXIS + 110.0, ORLA_AXIS + 220.0)):
        msk = (~geo.water) & (geo.Z > 1800)
        for r in shore.contour(geo.Dsea, off, msk):
            if shore.length(r) < 160: continue
            pts = shore.resample(shore.smooth_line(shore.resample(r, 12.0), 3), 8.0)
            # corta trechos fora da zona urbana (morros, rio)
            seg = []
            for p in pts:
                if geo.is_urban(*p) and not geo.is_water(*p): seg.append(p)
                else:
                    if len(seg) > 12: lines.append({'pts': seg, 'lvl': 1 if k == 0 else 2, 'id': lid, 'name': 'Rua Paralela da Orla'}); [occs[m].add(q[0], q[1], lid, 1 if k == 0 else 2) for q in seg for m in (False, True)]; lid += 1
                    seg = []
            if len(seg) > 12: lines.append({'pts': seg, 'lvl': 1 if k == 0 else 2, 'id': lid, 'name': 'Rua Paralela da Orla'}); [occs[m].add(q[0], q[1], lid, 1 if k == 0 else 2) for q in seg for m in (False, True)]; lid += 1
    for r in runs:
        L = 0.0; acc = [0.0]
        for a, b in zip(r, r[1:]): acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        L = acc[-1]; s = 55.0; n = 0
        while s < L - 50:
            q = next(i for i in range(len(acc)) if acc[i] >= s) ; p = r[max(q, 1) - 1]; p2 = r[q]
            f = (s - acc[max(q, 1) - 1]) / max(acc[q] - acc[max(q, 1) - 1], 1e-6); x, z = p[0] + (p2[0] - p[0]) * f, p[1] + (p2[1] - p[1]) * f
            pts = [(x, z)]; lvl = 1 if n % 3 == 1 else 2
            Lmax = 340.0 if lvl == 2 else 900.0
            for it in range(int(Lmax / 9)):
                dx, dz = grad(x, z)
                nx_, nz_ = x + dx * 9.0, z + dz * 9.0
                if geo.is_water(nx_, nz_): break
                if it > 3 and not geo.is_urban(nx_, nz_): break
                if abs(geo.height(nx_, nz_) - geo.height(x, z)) / 9.0 > 0.10: break
                x, z = nx_, nz_; pts.append((x, z))
            if len(pts) > 10:
                lines.append({'pts': pts, 'lvl': lvl, 'id': lid, 'name': 'Travessa da Orla'})
                for q_ in pts: occs[False].add(q_[0], q_[1], lid, lvl); occs[True].add(q_[0], q_[1], lid, lvl)
                lid += 1
            s += 110.0; n += 1

def generate(geo, seed=RNG):
    rng = random.Random(seed)
    fld = Field(geo); occs = {False: Occ(), True: Occ()}; lines = []
    # Av. Beira-Mar: contorno a 58 m do mar (areia 0-22 m, muro/escadas, calcadao 25-40 m, faixa de palmeiras, avenida)
    import shore
    runs = []
    for r in shore.beach_lines(geo, ORLA_AXIS):
        wet = [geo.is_water(*p) or any(geo.is_water(p[0] + dx, p[1] + dz) for dx, dz in ((24, 0), (-24, 0), (0, 24), (0, -24))) for p in r]
        i0 = 0; i1 = len(r)
        while i0 < i1 and wet[i0]: i0 += 1
        while i1 > i0 and wet[i1 - 1]: i1 -= 1
        if i1 - i0 > 12: runs.append(r[i0:i1])
    for r in runs:
        lines.append({'pts': r, 'lvl': 0, 'id': 1, 'name': 'Av. Beira-Mar', 'protect': True})
        for (px, pz) in r: occs[False].add(px, pz, 1, 0); occs[True].add(px, pz, 1, 0)
    orla_grid(geo, runs, lines, occs)
    stats = []
    for lvl, (nm, c, w, dsep, ms) in enumerate(LEVELS):
        n = trace_level(geo, fld, occs, lvl, dsep, ms, 1.0 if lvl == 0 else 1.2, rng, lines)
        stats.append((nm, n))
    pieces = planarize(lines)
    nodes, edges = build_graph(pieces)
    nodes, edges = clean(nodes, edges)
    return fld, nodes, edges, stats
