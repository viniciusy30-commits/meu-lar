"""ETAPA A - esqueleto viario: grafo de nos/arestas calculado so a partir de plan.py."""
import math
from plan import *


class Graph:
    def __init__(self):
        self.nodes = {}   # key -> dict
        self.edges = []

    @staticmethod
    def key(x, z):
        return (round(x, 2), round(z, 2))

    def node(self, x, z, kind='junction', **kw):
        k = self.key(x, z)
        n = self.nodes.get(k)
        if n is None:
            n = {'x': k[0], 'z': k[1], 'kind': kind}
            self.nodes[k] = n
        if kind != 'junction':
            n['kind'] = kind
        n.update(kw)
        return k

    def edge(self, name, cls, pts, kind='n', y0=0.0, y1=0.0, infra=False, w=None, a=None, b=None, tag=''):
        a = a or self.node(*pts[0]); b = b or self.node(*pts[-1])
        pts = [self.key(*p) for p in pts]
        pts[0] = a; pts[-1] = b
        self.edges.append({'id': len(self.edges), 'name': name, 'cls': cls, 'pts': pts, 'kind': kind, 'y0': y0, 'y1': y1,
                           'infra': infra, 'w': w or WIDTH[cls], 'a': a, 'b': b, 'tag': tag})


def arc(cx, cz, r, a0, a1, n=12):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * t / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * t / n))) for t in range(n + 1)]


def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def bez(p0, p1, p2, p3, n=14):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out


# ---------------------------------------------------------------- linhas da grade
class Line:
    def __init__(self, name, cls, ori, fixed, a, b, infra=False, kind='n', tag=''):
        self.name, self.cls, self.ori, self.fixed, self.a, self.b, self.infra, self.kind, self.tag = name, cls, ori, fixed, a, b, infra, kind, tag
        self.breaks = {a, b}

    def pt(self, t):
        return (self.fixed, t) if self.ori == 'ns' else (t, self.fixed)


def build_lines():
    L = []
    xe_w, xe_e = MARG_W_X, MARG_E_X
    # avenidas norte-sul
    for i, x in enumerate(XA):
        L.append(Line(XA_NAME[i], 'ave', 'ns', x, ZA[0], ZA[-1]))
    # avenidas leste-oeste (Beira-Mar segue ate a rotatoria da peninsula, tratada a parte)
    for j, z in enumerate(ZA):
        end = XA[-1]
        if j == 3: end = xe_w
        if j == 0: end = xe_e
        if j in (1, 2): end = xe_e
        if j == 4: end = xe_e
        L.append(Line(ZA_NAME[j], 'ave' if j in (2, 4) else 'ave', 'ew', z, XA[0], end))
    # marginais da rodovia
    for x, nm in ((xe_w, 'Marginal Oeste'), (xe_e, 'Marginal Leste')):
        L.append(Line(nm, 'col', 'ns', x, ZA[0], ZA[4], infra=True))
    # ruas internas por superquadra
    names = ['Rua dos Ipes', 'Rua das Acacias', 'Rua Maple', 'Rua dos Cedros', 'Rua das Palmeiras', 'Rua Oak', 'Rua das Jabuticabeiras',
             'Rua Cherry', 'Rua dos Pinheiros', 'Rua das Magnolias', 'Rua Elm', 'Rua das Hortensias', 'Rua Willow', 'Rua das Cerejeiras',
             'Rua dos Lirios', 'Rua Birch', 'Rua das Azaleias', 'Rua Aspen', 'Rua das Violetas', 'Rua Cypress', 'Rua das Orquideas',
             'Rua Walnut', 'Rua dos Jasmins', 'Rua Hickory', 'Rua das Camelias', 'Rua Sycamore', 'Rua dos Girassois', 'Rua Poplar',
             'Rua das Begonias', 'Rua Chestnut', 'Rua dos Narcisos', 'Rua Beech', 'Rua das Margaridas', 'Rua Laurel', 'Rua dos Cravos',
             'Rua Juniper', 'Rua das Dalias', 'Rua Hazel', 'Rua dos Crisantemos', 'Rua Holly']
    ni = [0]
    def nm():
        v = names[ni[0] % len(names)]; ni[0] += 1; return v
    for (i, j), t in SQ_TYPE.items():
        x0, z0, x1, z1 = sq_rect(i, j)
        ns, ew, cls = [], [], 'loc'
        if t == 'RES': ns = [x0 + o for o in RES_STREETS]; ew = [z0 + o for o in RES_STREETS]
        elif t == 'CEN': ns = [x0 + o for o in CEN_STREETS]; ew = [z0 + o for o in CEN_STREETS]; cls = 'col'
        elif t == 'CND': ns = [x0 + 180]; ew = [z0 + 120, z0 + 240]
        elif (i, j) == (4, 0): ew = [z0 + 180]; cls = 'col'
        elif (i, j) == (1, 3): ns = [x0 + 300]; cls = 'col'
        for x in ns: L.append(Line(nm(), cls, 'ns', x, ZA[j], ZA[j + 1], tag=f'sq{i}{j}'))
        for z in ew: L.append(Line(nm(), cls, 'ew', z, XA[i], XA[i + 1], tag=f'sq{i}{j}'))
    # faixa de servicos + ligacoes com o Beltway
    L.append(Line('Rua de Servico', 'loc', 'ew', SERVICE_Z, 250.0, 2140.0))
    for x in (250.0, 2140.0): L.append(Line('Ligacao Servico', 'loc', 'ns', x, SERVICE_Z, ZA[0]))
    for x in (976.0, 1752.0): L.append(Line('Acesso Beltway', 'col', 'ns', x, HWY_Z_NORTH, ZA[0], infra=True))
    # Rua Duna
    L.append(Line('Rua Duna', 'loc', 'ew', 1800.0, 250.0, 1000.0))
    for x in (250.0, 500.0, 750.0, 1000.0): L.append(Line('Acesso Duna', 'loc', 'ns', x, ZA[4], 1800.0))
    return L


def intersect_lines(L):
    ns = [l for l in L if l.ori == 'ns']; ew = [l for l in L if l.ori == 'ew']
    for a in ns:
        for b in ew:
            if b.a - 1e-6 <= a.fixed <= b.b + 1e-6 and a.a - 1e-6 <= b.fixed <= a.b + 1e-6:
                a.breaks.add(b.fixed); b.breaks.add(a.fixed)
    # pontos onde vias fora da grade (curvas/rodovia) encostam numa linha da grade
    for ori, fixed, t in ((('ew', 1752.0, HWY_X)), ('ns', 588.0, 480.0), ('ew', 588.0, 700.0), ('ew', 200.0, 420.0), ('ns', 200.0, 700.0), ('ns', 200.0, 1020.0), ('ew', 1752.0, 752.0), ('ew', 1752.0, 868.0)):
        for l in L:
            if l.ori == ori and l.fixed == fixed and l.a <= t <= l.b: l.breaks.add(t)


# ---------------------------------------------------------------- mascara: recorte com fim de rua
def clip_edge(g, e):
    """corta a aresta pela mascara; devolve lista de arestas (pedacos dentro) com cul-de-sac onde cortou"""
    pts = e['pts']
    # amostra a cada ~3 m
    samp = []
    for k in range(len(pts) - 1):
        p, q = pts[k], pts[k + 1]
        n = max(1, int(math.hypot(q[0] - p[0], q[1] - p[1]) / 3))
        for s in range(n):
            samp.append(lerp(p, q, s / n))
    samp.append(pts[-1])
    ins = [in_mask(*p) for p in samp]
    if all(ins): return [e]
    out = []; k = 0; n = len(samp)
    while k < n:
        if not ins[k]: k += 1; continue
        m = k
        while m + 1 < n and ins[m + 1]: m += 1
        run = samp[k:m + 1]
        L = sum(math.hypot(run[t + 1][0] - run[t][0], run[t + 1][1] - run[t][1]) for t in range(len(run) - 1))
        cut_a = k > 0; cut_b = m < n - 1
        trim = 12.0   # raio do cul-de-sac
        def shorten(run, front):
            r = run if front else run[::-1]
            acc = 0.0; idx = 0
            while idx + 1 < len(r) and acc < trim:
                acc += math.hypot(r[idx + 1][0] - r[idx][0], r[idx + 1][1] - r[idx][1]); idx += 1
            r = r[idx:]
            return r if front else r[::-1]
        if cut_a: run = shorten(run, True)
        if cut_b: run = shorten(run, False)
        if len(run) >= 2 and L - trim * (cut_a + cut_b) >= 20:
            sub = dict(e); sub['pts'] = run
            sub['cut_a'] = cut_a; sub['cut_b'] = cut_b
            out.append(sub)
        k = m + 1
    return out


def build():
    g = Graph()
    L = build_lines(); intersect_lines(L)
    # rotatorias: no 'round'
    for nm, (x, z, r) in ROUNDS.items():
        g.node(x, z, 'round', r=r, name=nm)
    for l in L:
        bs = sorted(l.breaks)
        for u, v in zip(bs, bs[1:]):
            if v - u < 0.5: continue
            p0, p1 = l.pt(u), l.pt(v)
            ext = l.ori == 'ew' and u >= XA[-1] - 1e-6          # extensoes a leste da Av. Leste (infraestrutura da rodovia)
            if l.ori == 'ew' and l.fixed == 1752.0 and abs(u - 752.0) < 1e-6 and abs(v - 868.0) < 1e-6:
                g.edge('Ponte da Marina', 'ave', [p0, p1], kind='bridge', y0=0.6, y1=0.6, infra=True, tag='bridge'); continue
            g.edge(l.name, l.cls, [p0, p1], infra=l.infra or ext, tag=l.tag)
    # pontes e extensoes leste (ew ate a margem leste)
    for z, nm in ((588.0, 'Ponte do Moinho'), (976.0, 'Ponte Real'), (1752.0, 'Ponte da Foz')):
        cls = 'ave' if z != 588.0 else 'col'
        a = g.node(MARG_E_X, z)
        b1 = g.node(2350.0, z); b2 = g.node(2440.0, z)
        g.edge(ZA_NAME[ZA.index(z)] + ' (leste)', cls, [(MARG_E_X, z), (2350.0, z)], infra=True, a=a)
        g.edge(nm, cls, [(2350.0, z), (2440.0, z)], kind='bridge', y0=0.6, y1=0.6, infra=True, tag=nm)
    # margem leste + peninsula
    marg = [(2480, 588), (2492, 780), (2478, 976), (2490, 1200), (2505, 1400), (2530, 1500)]
    for (a, b) in zip(marg, marg[1:]):
        g.edge('Estrada da Margem Leste', 'col', [a, b], infra=True)
    g.edge('Estrada da Margem Leste', 'col', [(2530, 1500), (2560, 1500)], infra=True)
    g.edge('Rua Real', 'loc', [(2560, 1500), (2560, 1620)], infra=True)
    g.edge('Rua Real', 'loc', [(2560, 1620), (2560, 1752)], infra=True)
    g.edge('Rua Real (mansoes)', 'loc', [(2560, 1620), (2640, 1620)], infra=True, b=g.node(2640, 1620, 'cul'))
    # liga as pontes ao fim leste
    g.edge('Ponte Moinho (acesso)', 'col', [(2440, 588), (2480, 588)], infra=True)
    g.edge('Ponte Real (acesso)', 'ave', [(2440, 976), (2478, 976)], infra=True)
    g.edge('Ponte da Foz (acesso)', 'ave', [(2440, 1752), (2560, 1752)], infra=True)
    # Beira-Mar: rotatoria da peninsula ja e no; extensao oeste ate o cabo
    cabo = [(200, 1752), (150, 1762), (125, 1790), (126, 1825), (150, 1850)]
    g.edge('Estrada do Cabo', 'col', cabo, infra=False, b=g.node(150, 1850, 'cul'))
    # rodovia
    hw = HWY_Z_NORTH
    pts = sorted({0.0, 976.0, 1752.0, HWY_ARC_C[0]})
    for u, v in zip(pts, pts[1:]):
        g.edge('Rodovia Beltway', 'hwy', [(u, hw), (v, hw)], infra=True, a=g.node(u, hw, 'edge') if u == 0 else None)
    cx, cz = HWY_ARC_C
    g.edge('Rodovia Beltway (curva)', 'hwy', arc(cx, cz, HWY_ARC_R, -90, 0, 14), kind='ramp', y0=0, y1=HWY_Y_DECK, infra=True)
    zs = [HWY_ELEV_Z0, 468.0, 708.0, 1244.0, 1484.0, HWY_ELEV_Z1]
    for u, v in zip(zs, zs[1:]):
        g.edge('Rodovia Leste (elevada)', 'hwy', [(HWY_X, u), (HWY_X, v)], kind='elev', y0=HWY_Y_DECK, y1=HWY_Y_DECK, infra=True)
    g.edge('Rodovia Leste (descida)', 'hwy', [(HWY_X, HWY_ELEV_Z1), (HWY_X, HWY_RAMP_END)], kind='ramp', y0=HWY_Y_DECK, y1=0.0, infra=True)
    g.edge('Rodovia Leste (solo)', 'hwy', [(HWY_X, HWY_RAMP_END), (HWY_X, 1752.0)], infra=True)
    # alcas
    for zc in (588.0, 1364.0):
        zo, zi = zc - 120, zc + 120
        c1 = bez((HWY_X, zo), (HWY_X, zo + 40), (MARG_W_X, zc - 40), (MARG_W_X, zc), 12)
        c2 = bez((MARG_W_X, zc), (MARG_W_X, zc + 40), (HWY_X, zi - 40), (HWY_X, zi), 12)
        g.edge('Alca de saida', 'col', c1, kind='ramp', y0=HWY_Y_DECK, y1=0.0, infra=True, w=8.0, tag='ramp')
        g.edge('Alca de entrada', 'col', c2, kind='ramp', y0=0.0, y1=HWY_Y_DECK, infra=True, w=8.0, tag='ramp')
    # Alto da Colina (ruas curvas)
    ctr = (400.0, 390.0); rx, rz = 120.0, 100.0
    def ell(a): return (ctr[0] + rx * math.cos(math.radians(a)), ctr[1] + rz * math.sin(math.radians(a)))
    angs = [-90, 0, 80, 140, 270]   # topo, direita, spur casa3, spur casa2, volta ao topo
    nodes = [ell(a) for a in angs]
    for k in range(len(angs) - 1):
        a0, a1 = angs[k], angs[k + 1]
        pts = [ell(a0 + (a1 - a0) * t / 10) for t in range(11)]
        g.edge('Rua do Mirante', 'loc', pts)
    g.edge('Portao do Alto da Colina', 'loc', [(420, 200), (415, 245), (400, 290)])
    g.edge('Alameda dos Ipes', 'loc', [ell(0), (548, 420), (572, 462), (588, 480)])
    g.edge('Rua da Casa 3', 'loc', [ell(80), (435, 520), (450, 555)], b=g.node(450, 555, 'cul'))
    g.edge('Rua da Casa 2', 'loc', [ell(140), (285, 500), (270, 540)], b=g.node(270, 540, 'cul'))
    # Mirante
    g.edge('Estrada do Mirante', 'loc', [(700, 588), (715, 545), (745, 505), (780, 470), (798, 440), (785, 420)], b=g.node(785, 420, 'cul'))
    # Estrada da Serra (alca pelo morro oeste)
    g.edge('Estrada da Serra', 'loc', [(200, 700), (150, 745), (112, 820), (105, 900), (130, 960), (200, 1020)])
    return g, L


def finalize(g):
    """quebra arestas de grade nos nos ja existentes, recorta pela mascara e remove orfaos"""
    new = []
    for e in g.edges:
        if e['infra'] or e['kind'] != 'n':
            new.append(e); continue
        for s in clip_edge(g, e):
            if s.get('cut_a'): s['a'] = g.node(*s['pts'][0], 'cul')
            else: s['a'] = g.key(*s['pts'][0])
            if s.get('cut_b'): s['b'] = g.node(*s['pts'][-1], 'cul')
            else: s['b'] = g.key(*s['pts'][-1])
            s['pts'] = [s['a']] + [g.key(*p) for p in s['pts'][1:-1]] + [s['b']]
            new.append(s)
    # remove arestas internas ao campus do hospital (quarteiroes fundidos) e as da fachada do parque
    def inside_rect(e, r):
        mx = (e['pts'][0][0] + e['pts'][-1][0]) / 2; mz = (e['pts'][0][1] + e['pts'][-1][1]) / 2
        return r[0] <= mx <= r[2] and r[1] <= mz <= r[3]
    campus = (1473.0, 309.0, 1643.0, 479.0)
    new = [e for e in new if not (e['tag'] == 'sq30' and inside_rect(e, campus))]
    for i, e in enumerate(new): e['id'] = i
    g.edges = new
    used = set()
    for e in new: used.add(e['a']); used.add(e['b'])
    g.nodes = {k: v for k, v in g.nodes.items() if k in used}
    for e in new:
        for k in (e['a'], e['b']):
            g.nodes.setdefault(k, {'x': k[0], 'z': k[1], 'kind': 'junction'})
    return g
