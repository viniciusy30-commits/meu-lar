"""Validadores de TRANSITO e SINALIZACAO (etapa C2)."""
import math
import numpy as np
from collections import defaultdict
from plan import *
import traffic as TR, validate_ground

def run(g, tr, fu):
    out = []; ok = True
    c = g.c
    # 1) grafo de faixas fortemente conexo
    n, bad = tr.lane_graph_connected()
    good = not bad; ok &= good
    out.append(f'  grafo de trafego (mao direita): {n} sentidos de rua, {len(bad)} sem entrada ou sem saida {"ok" if good else "PROBLEMA"}')
    # 2) todo cruzamento tem controle em todos os bracos e fases cobrem cada braco uma vez
    miss = 0; dup = 0
    for ni, arms in g.arms.items():
        if len(arms) < 3: continue
        for a in arms:
            if (ni, a['k'], a['end']) not in tr.control: miss += 1
    for ni, s in tr.signals.items():
        seen = defaultdict(int)
        for ph in s['phases']:
            for k, e in ph['arms']: seen[(k, e)] += 1
        for a in g.arms[ni]:
            if seen[(a['k'], a['end'])] != 1: dup += 1
    good = miss == 0 and dup == 0; ok &= good
    out.append(f'  controle de transito: {len(tr.signals)} semaforos, {sum(1 for v in tr.control.values() if v=="stop")} PARE, {sum(1 for v in tr.control.values() if v=="yield")} preferenciais de rotatoria; bracos sem controle: {miss}; bracos fora de fase: {dup} {"ok" if good else "PROBLEMA"}')
    # 3) movimentos: dentro do asfalto e raio minimo
    M = validate_ground.raster(g, ['asphalt', 'island', 'median'])
    outside = 0; tot = 0; tight = []
    for m in tr.moves:
        P = m['path']
        for q in range(len(P) - 1):
            L = math.hypot(P[q + 1][0] - P[q][0], P[q + 1][1] - P[q][1])
            for t in np.linspace(0, 1, max(2, int(L))):
                x = P[q][0] + (P[q + 1][0] - P[q][0]) * t; z = P[q][1] + (P[q + 1][1] - P[q][1]) * t
                i, j = int(x), int(z); tot += 1
                if not (M['asphalt'][j, i] or M['asphalt'][min(j + 1, M['asphalt'].shape[0] - 1), i] or M['asphalt'][j, min(i + 1, M['asphalt'].shape[1] - 1)]): outside += 1
        if m['kind'] in ('left', 'right') and m['radius'] < 4.4: tight.append(m)
    pct = 100.0 * outside / max(tot, 1); good = pct < 1.0 and len(tight) == 0; ok &= good
    out.append(f'  trajetorias dos carros (curvas/cruzamentos): {len(tr.moves)} movimentos; fora do asfalto: {pct:.2f}%; curvas com raio < 4,4 m: {len(tight)} {"ok" if good else "PROBLEMA"}')
    # 4) curvas ao longo das ruas
    cr = tr.curve_check(); good = len(cr) == 0; ok &= good
    out.append(f'  curvas das ruas apertadas demais para a faixa externa: {len(cr)} {"ok" if good else "PROBLEMA"}' + (f' piores raios: {[round(r,1) for r,_,_ in cr[:4]]}' if cr else ''))
    # 5) postes/placas: na calcada/canteiro, longe de faixas de pedestre e covas
    Mz = validate_ground.raster(g, ['asphalt', 'zebra', 'tact', 'sidewalk', 'verge', 'curb'])
    er = lambda m: m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
    Mz['asphalt'] = er(Mz['asphalt']); Mz['zebra'] = er(Mz['zebra'])
    on_road = 0; near_x = 0
    pits = [(f['pit'][0], f['pit'][1]) for f in g.fronts if 'pit' in f]
    for (x, z) in fu.poles:
        i, j = int(x), int(z)
        if Mz['asphalt'][j, i] or Mz['zebra'][j, i]: on_road += 1
        else:
            for dj in (-1, 0, 1):
                for di in (-1, 0, 1):
                    if Mz['tact'][min(max(j + dj, 0), Mz['tact'].shape[0] - 1), min(max(i + di, 0), Mz['tact'].shape[1] - 1)]: near_x += 1; break
                else: continue
                break
    near_pit = sum(1 for (x, z) in fu.poles if any(math.hypot(x - px, z - pz) < 0.9 for px, pz in pits))
    good = on_road == 0 and near_x == 0 and near_pit == 0; ok &= good
    out.append(f'  postes de semaforo/placas ({len(fu.poles)}): sobre a pista: {on_road}; atrapalhando a rampa da faixa: {near_x}; em cima de cova de arvore: {near_pit} {"ok" if good else "PROBLEMA"}')
    # 6) lombadas
    mb = validate_ground.raster  # reuse
    bump_out = 0
    for b in tr.bumps:
        P = b['poly']; cx = sum(p[0] for p in P) / 4; cz = sum(p[1] for p in P) / 4
        if not Mz['asphalt'][int(cz), int(cx)]: bump_out += 1
    close = 0
    for a in range(len(tr.bumps)):
        for b in range(a + 1, len(tr.bumps)):
            if math.hypot(tr.bumps[a]['x'] - tr.bumps[b]['x'], tr.bumps[a]['z'] - tr.bumps[b]['z']) < 60: close += 1
    bad_lvl = sum(1 for b in tr.bumps if b['lvl'] == 0)
    good = bump_out == 0 and close == 0 and bad_lvl == 0; ok &= good
    out.append(f'  lombadas: {len(tr.bumps)} (fora do asfalto: {bump_out}; pares a < 60 m: {close}; em avenida: {bad_lvl}) {"ok" if good else "PROBLEMA"}')
    # 7) semaforos distantes
    sx = [(s['x'], s['z']) for s in tr.signals.values()]; closep = sum(1 for a in range(len(sx)) for b in range(a + 1, len(sx)) if math.hypot(sx[a][0] - sx[b][0], sx[a][1] - sx[b][1]) < 150)
    good = closep == 0; ok &= good
    out.append(f'  semaforos a menos de 150 m um do outro: {closep} {"ok" if good else "PROBLEMA"}')
    return ok, out
