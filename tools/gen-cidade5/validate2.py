"""Validadores v2 (rede organica)."""
import math
from collections import defaultdict
from plan import *

def v_connect(c):
    comp, groups = c.components(); groups.sort(key=len, reverse=True)
    msgs = [f'componentes: {len(groups)} (maior {len(groups[0])} nos de {len(c.nodes)})']
    for g in groups[1:]: msgs.append(f'  ilha desconectada: {len(g)} nos perto de {tuple(round(v) for v in c.nodes[g[0]][:2])}')
    return len(groups) == 1, msgs

def v_deadends(c):
    deg = defaultdict(int)
    for e in c.edges: deg[e['a']] += 1; deg[e['b']] += 1
    ends = [i for i, d in deg.items() if d == 1]
    bad = []; kinds = defaultdict(int)
    for i in ends:
        if i in c.lookouts: kinds['mirante da ponte'] += 1
        elif i in c.legit: kinds[c.legit[i]] += 1
        else: bad.append(f'  fim de rua sem sentido em {round(c.nodes[i][0])},{round(c.nodes[i][1])}')
    msgs = [f'{len(ends)} fins de rua: ' + ', '.join(f'{v} {k}' for k, v in sorted(kinds.items()))]
    return not bad, msgs + bad[:25]

def v_crossings(c):
    from network import seg_inter
    segs = []
    for e in c.edges:
        if e['kind'] in ('bridge', 'redbridge'): continue
        for a, b in zip(e['p'], e['p'][1:]): segs.append((a, b, id(e), e))
    grid = defaultdict(list)
    for i, (a, b, _, _) in enumerate(segs):
        for cx in range(int(min(a[0], b[0]) // 60), int(max(a[0], b[0]) // 60) + 1):
            for cz in range(int(min(a[1], b[1]) // 60), int(max(a[1], b[1]) // 60) + 1): grid[(cx, cz)].append(i)
    bad = set()
    for lst in grid.values():
        for x in range(len(lst)):
            for y in range(x + 1, len(lst)):
                s1, s2 = segs[lst[x]], segs[lst[y]]
                if s1[2] == s2[2]: continue
                r = seg_inter(s1[0], s1[1], s2[0], s2[1])
                if r and 0.02 < r[0] < 0.98 and 0.02 < r[1] < 0.98: bad.add((round(s1[0][0]), round(s1[0][1])))
    return not bad, [f'rua atravessa rua sem no: {len(bad)}'] + [f'  perto de {b}' for b in sorted(bad)[:20]]

def v_grades(c, geo):
    lim = {0: 0.10, 1: 0.12, 2: 0.16, 3: 0.08}
    bad = []
    for e in c.edges:
        if e['kind'] in ('redbridge', 'bridge') or e['lvl'] == 3: continue
        for a, b in zip(e['p'], e['p'][1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 1: continue
            g = abs(geo.height(*b) - geo.height(*a)) / L
            if g > lim[e['lvl']] * 1.5: bad.append(f'  declive {g*100:.0f}% (limite {lim[e["lvl"]]*100:.0f}%) perto de {round(a[0])},{round(a[1])}'); break
    return len(bad) <= 6, [f'trechos acima de 1,5x o limite de declive: {len(bad)} (tolerado ate 6; o Etapa B terraplena)'] + bad[:12]

def v_water(c, geo):
    bad = []
    for e in c.edges:
        if e['kind'] in ('bridge', 'redbridge'): continue
        for p in e['p'][::2]:
            if geo.is_water(*p) and not (e['lvl'] == 3): bad.append(f'  {e["name"] or "rua"} dentro da agua em {round(p[0])},{round(p[1])}'); break
    return not bad, [f'vias dentro da agua sem ponte: {len(bad)}'] + bad[:12]

def v_bridges(c):
    msgs = []; ok = True
    msgs.append(f'pontes vermelhas (so cenario): {len(c.red)} (esperado 2)'); ok &= len(c.red) == 2
    ok &= all(not r['drivable'] for r in c.red)
    ok &= not any(e['kind'] == 'redbridge' for e in c.edges)
    msgs.append(f'pontes vermelhas sem ligacao viaria: {"sim" if ok else "NAO"}; miradouros com cancela: {len(c.lookouts)} (esperado 2)'); ok &= len(c.lookouts) == 2
    br = [e for e in c.edges if e['kind'] == 'bridge' and e['name'].startswith('Ponte')]
    msgs.append(f'pontes sobre o rio: {len(br)}'); ok &= len(br) >= 3
    return ok, msgs

def v_rounds(c):
    return len(c.rounds) >= 6, [f'{len(c.rounds)} rotatorias']

def run_all(c, geo):
    out = []
    for name, f in (('conexao do grafo', lambda: v_connect(c)), ('fins de rua / tocos', lambda: v_deadends(c)), ('rua atravessa rua', lambda: v_crossings(c)),
                    ('declives', lambda: v_grades(c, geo)), ('vias na agua', lambda: v_water(c, geo)), ('pontes e tuneis', lambda: v_bridges(c)), ('rotatorias', lambda: v_rounds(c))):
        ok, m = f(); out.append((name, ok, m))
    return out


def v_final(city, hf, ynode):
    import terrain_final as T
    bad_g, bad_h, bad_w = [], [], []
    maxcut = 0.0
    for e in city.edges:
        if e['kind'] == 'redbridge': continue
        pp = T.profile_pts(e, ynode[e['a']], ynode[e['b']])
        L = T.elen(e['p']); lim = T.GRADE.get(e['lvl'], 0.065) if e['kind'] != 'bridge' else 0.07
        if L > 1 and abs(ynode[e['a']] - ynode[e['b']]) / L > lim * 1.02:
            bad_g.append(f'  declive {abs(ynode[e["a"]]-ynode[e["b"]])/L*100:.1f}% (limite {lim*100:.1f}%) em {round(pp[0][0])},{round(pp[0][1])}')
        if e['kind'] == 'bridge':
            if min(ynode[e['a']], ynode[e['b']]) < 1.0: bad_w.append(f'  ponte {e["name"]} com tabuleiro baixo')
            continue
        for (x, z, y) in pp:
            d = abs(T.sample8(hf, x, z) - y); maxcut = max(maxcut, d)
            if d > 1.2: bad_h.append(f'  rua fora do terreno ({d:.1f} m) em {round(x)},{round(z)}'); break
            if T.sample8(hf, x, z) < 0.2: bad_w.append(f'  rua na agua em {round(x)},{round(z)}'); break
    ok = not (bad_g or bad_h or bad_w)
    return ok, [f'declives finais acima do limite: {len(bad_g)}', f'ruas fora do terreno (>1,2 m): {len(bad_h)}', f'ruas/pontes na agua ou baixas: {len(bad_w)}'] + (bad_g + bad_h + bad_w)[:20]
