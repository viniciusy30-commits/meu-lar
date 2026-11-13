"""Validadores da ETAPA A. Cada um devolve (ok, [mensagens])."""
import math
from collections import defaultdict
from plan import *


def v_connect(g):
    adj = defaultdict(set)
    for e in g.edges: adj[e['a']].add(e['b']); adj[e['b']].add(e['a'])
    nodes = list(g.nodes)
    seen = set(); comps = []
    for n in nodes:
        if n in seen: continue
        st = [n]; comp = []; seen.add(n)
        while st:
            u = st.pop(); comp.append(u)
            for w in adj[u]:
                if w not in seen: seen.add(w); st.append(w)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    msgs = [f'componentes: {len(comps)} (maior {len(comps[0])} nos)']
    for c in comps[1:]:
        msgs.append(f'  ilha desconectada: {len(c)} nos, ex. {c[0]}')
    return len(comps) == 1, msgs


def v_deadends(g):
    deg = defaultdict(int)
    for e in g.edges: deg[e['a']] += 1; deg[e['b']] += 1
    bad = []
    for k, d in deg.items():
        if d == 1 and g.nodes[k]['kind'] not in ('cul', 'edge'):
            bad.append(f'  rua termina no ar em {k}')
    return not bad, [f'pontas soltas: {len(bad)}'] + bad[:30]


def v_nodes_close(g):
    ks = list(g.nodes); grid = defaultdict(list)
    for k in ks: grid[(int(k[0] // 4), int(k[1] // 4))].append(k)
    bad = []
    for k in ks:
        cx, cz = int(k[0] // 4), int(k[1] // 4)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for o in grid[(cx + dx, cz + dz)]:
                    if o > k and math.hypot(o[0] - k[0], o[1] - k[1]) < 1.0: bad.append(f'  nos a <1 m: {k} {o}')
    return not bad, [f'nos muito proximos: {len(bad)}'] + bad[:30]


def v_mask(g):
    bad = []
    for e in g.edges:
        if e['infra']: continue
        for p in e['pts']:
            if not in_mask(*p): bad.append(f'  {e["name"]} fora da mascara em {p}'); break
    return not bad, [f'vias urbanas fora da mascara: {len(bad)}'] + bad[:30]


def segs(g):
    out = []
    for e in g.edges:
        for u, v in zip(e['pts'], e['pts'][1:]):
            out.append((u, v, e))
    return out


def cross(p1, p2, p3, p4):
    d1 = (p2[0] - p1[0], p2[1] - p1[1]); d2 = (p4[0] - p3[0], p4[1] - p3[1])
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-9: return False
    t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / den
    u = ((p3[0] - p1[0]) * d1[1] - (p3[1] - p1[1]) * d1[0]) / den
    return 1e-6 < t < 1 - 1e-6 and 1e-6 < u < 1 - 1e-6


def v_crossings(g):
    S = segs(g); grid = defaultdict(list)
    for i, (u, v, e) in enumerate(S):
        x0, x1 = sorted((u[0], v[0])); z0, z1 = sorted((u[1], v[1]))
        for cx in range(int(x0 // 40), int(x1 // 40) + 1):
            for cz in range(int(z0 // 40), int(z1 // 40) + 1): grid[(cx, cz)].append(i)
    bad = set()
    for lst in grid.values():
        for a in range(len(lst)):
            for b in range(a + 1, len(lst)):
                i, j = lst[a], lst[b]
                (u1, v1, e1), (u2, v2, e2) = S[i], S[j]
                if e1 is e2: continue
                if e1['kind'] in ('elev', 'bridge') or e2['kind'] in ('elev', 'bridge'): continue
                if cross(u1, v1, u2, v2):
                    bad.add((e1['name'], e2['name'], round(u1[0]), round(u1[1])))
    return not bad, [f'cruzamentos sem no (rua atravessa rua): {len(bad)}'] + [f'  {b}' for b in sorted(bad)[:30]]


def v_tjunction(g):
    """no encostado no meio de outra aresta sem ser extremo dela"""
    S = segs(g); grid = defaultdict(list)
    for i, (u, v, e) in enumerate(S):
        x0, x1 = sorted((u[0], v[0])); z0, z1 = sorted((u[1], v[1]))
        for cx in range(int(x0 // 40), int(x1 // 40) + 1):
            for cz in range(int(z0 // 40), int(z1 // 40) + 1): grid[(cx, cz)].append(i)
    bad = []
    for k in g.nodes:
        for i in grid[(int(k[0] // 40), int(k[1] // 40))]:
            u, v, e = S[i]
            if e['kind'] in ('elev', 'bridge'): continue
            if k in (e['a'], e['b']) or k in (u, v): continue
            dx, dz = v[0] - u[0], v[1] - u[1]; L2 = dx * dx + dz * dz
            if L2 < 1e-9: continue
            t = ((k[0] - u[0]) * dx + (k[1] - u[1]) * dz) / L2
            if 0 < t < 1:
                d = math.hypot(k[0] - (u[0] + t * dx), k[1] - (u[1] + t * dz))
                if d < 0.6: bad.append(f'  no {k} encosta em "{e["name"]}" sem emenda')
    bad = sorted(set(bad))
    return not bad, [f'T sem no: {len(bad)}'] + bad[:30]


def v_grades(g):
    bad = []
    for e in g.edges:
        L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(e['pts'], e['pts'][1:]))
        if L > 1 and e['kind'] in ('ramp', 'elev'):
            gr = abs(e['y1'] - e['y0']) / L * 100
            lim = 6.5
            if gr > lim: bad.append(f'  {e["name"]}: {gr:.1f}% > {lim}% ({L:.0f} m)')
    return not bad, [f'declives de rampa: {len(bad)} acima do limite'] + bad


def v_names(g):
    names = set(e['name'] for e in g.edges if e['tag'].startswith('sq'))
    return True, [f'{len(names)} ruas internas nomeadas, {len(g.edges)} arestas, {len(g.nodes)} nos']


def run_all(g):
    res = []
    for name, f in (('conexao do grafo', v_connect), ('pontas soltas', v_deadends), ('nos proximos', v_nodes_close),
                    ('vias dentro da mascara', v_mask), ('rua atravessa rua', v_crossings), ('T sem no', v_tjunction),
                    ('declives (rampas)', v_grades), ('resumo', v_names)):
        ok, m = f(g); res.append((name, ok, m))
    return res
