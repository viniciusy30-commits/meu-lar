"""Exporta a Cidade 5 para o app Android (assets/hds/c5*): relevo, malha assada, atlas de placas, arvores e a Casa 1 provisoria."""
import json, math, os, shutil, struct
import numpy as np


def _grid_dist(points, hf, step=8.0):
    """distancia (m) ate o ponto mais proximo (chanfro de 2 passadas, grade de 8 m)"""
    ny, nx = hf.shape
    D = np.full((ny, nx), 1e9)
    for x, z in points:
        i = int(round(x / step)); j = int(round(z / step))
        if 0 <= i < nx and 0 <= j < ny: D[j, i] = 0.0
    r2 = step * 1.41421356
    for j in range(ny):
        for i in range(nx):
            v = D[j, i]
            if v == 0: continue
            if i > 0: v = min(v, D[j, i - 1] + step)
            if j > 0:
                v = min(v, D[j - 1, i] + step)
                if i > 0: v = min(v, D[j - 1, i - 1] + r2)
                if i < nx - 1: v = min(v, D[j - 1, i + 1] + r2)
            D[j, i] = v
    for j in range(ny - 1, -1, -1):
        for i in range(nx - 1, -1, -1):
            v = D[j, i]
            if v == 0: continue
            if i < nx - 1: v = min(v, D[j, i + 1] + step)
            if j < ny - 1:
                v = min(v, D[j + 1, i] + step)
                if i < nx - 1: v = min(v, D[j + 1, i + 1] + r2)
                if i > 0: v = min(v, D[j + 1, i - 1] + r2)
            D[j, i] = v
    return D


def run(out, geo, hf, assets):
    roads = json.load(open(os.path.join(out, 'city5_roads.json')))
    pts = []
    for e in roads['edges']:
        p = e['p']
        for a, b in zip(p, p[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L // 6))
            for k in range(n + 1): pts.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    for r in roads['rounds']:
        for k in range(16): pts.append((r['x'] + math.cos(k / 16 * 6.283) * r['r'], r['z'] + math.sin(k / 16 * 6.283) * r['r']))
    dist = _grid_dist(pts, hf)
    ny, nx = hf.shape
    # Casa 1 provisoria: terreno mais plano em zona urbana, 22-60 m de uma rua
    best = None
    gx, gz = np.gradient(hf, 8.0, 8.0, edge_order=1)[1], np.gradient(hf, 8.0, 8.0)[0]
    for j in range(4, ny - 4, 2):
        for i in range(4, nx - 4, 2):
            x, z = i * 8.0, j * 8.0
            if not geo.is_urban(x, z): continue
            if not (22 <= dist[j, i] <= 60): continue
            h = hf[j, i]
            if h < 6 or h > 40: continue
            sl = float(np.abs(hf[j - 2:j + 3, i - 2:i + 3] - h).max())
            if best is None or sl < best[0]: best = (sl, x, z, float(h))
    sl, hx, hz, hh = best
    print(f'  Casa 1 provisoria em ({hx:.0f},{hz:.0f}) h={hh:.2f} desnivel={sl:.2f} m')
    # arvores: fora de ruas (>30 m), fora da zona urbana e das praias, acima da praia
    rng = np.random.default_rng(5)
    trees = []
    for j in range(2, ny - 2):
        for i in range(2, nx - 2):
            x, z = i * 8.0, j * 8.0
            h = hf[j, i]
            if h < 2.5 or dist[j, i] < 30: continue
            if geo.is_urban(x, z): continue
            dens = 0.55 if h < 140 else 0.2
            for _ in range(2):
                if rng.random() > dens * 0.55: continue
                tx = x + rng.uniform(-4, 4); tz = z + rng.uniform(-4, 4)
                sp = 3 if h > 90 and rng.random() < 0.7 else int(rng.choice([0, 1, 0, 3], p=[.4, .3, .1, .2]))
                trees.append([round(tx, 1), round(tz, 1), sp, round(float(rng.uniform(0.8, 1.5)), 2), round(float(rng.uniform(0, 6.28)), 2), round(float(rng.uniform(0, 1)), 2)])
    cap = 16000
    if len(trees) > cap:
        idx = rng.choice(len(trees), cap, replace=False); trees = [trees[k] for k in sorted(idx)]
    print(f'  {len(trees)} arvores')
    flat = [v for t in trees for v in t]
    js = {'world': roads['world'], 'roads': [], 'rounds': [], 'nodes': [], 'houses': [{'k': 0, 'x': hx, 'z': hz, 'lvl': round(hh, 2)}],
          'bld': [], 'lamp': [], 'hyd': [], 'tree': flat, 'solid': []}
    os.makedirs(assets, exist_ok=True)
    json.dump(js, open(os.path.join(assets, 'c5.json'), 'w'), separators=(',', ':'))
    shutil.copy(os.path.join(out, 'relevo5.bin'), os.path.join(assets, 'c5.bin'))
    shutil.copy(os.path.join(out, 'city5_ground.bin'), os.path.join(assets, 'c5_mesh.bin'))
    shutil.copy(os.path.join(out, 'signs_atlas.png'), os.path.join(assets, 'c5_signs.png'))
    print('  exportado para', assets)
