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
    # terreno abaixo da malha + mapa de altura de caminhada
    print('  ajustando terreno a malha...')
    h2, tris = fit_terrain(hf, os.path.join(out, 'city5_ground.bin'))
    drop = hf - h2
    print(f'  vertices abaixados: {int((drop > 0.001).sum())} (max {drop.max():.2f} m); viraram areia/agua: {int(((hf >= 1.3) & (h2 < 1.3)).sum())}/{int(((hf >= -0.1) & (h2 < -0.1)).sum())}')
    import terrain_final as T
    T.write_bin(h2, os.path.join(assets, 'c5.bin'))
    # mascara de AREIA (so a praia de verdade; margens de rio/lagoa ficam de grama)
    from plan import CELL as _C, NX as _NX, NZ as _NZ
    ny8, nx8 = h2.shape
    X8 = np.arange(nx8) * 8.0; Z8 = np.arange(ny8) * 8.0
    ii = np.clip(np.round(X8 / _C).astype(int), 0, _NX - 1)[None, :]; jj = np.clip(np.round(Z8 / _C).astype(int), 0, _NZ - 1)[:, None]
    sand = geo.beach_zone[jj, ii] & (geo.Dsea[jj, ii] < 66.0) & (h2 < 1.6)
    with open(os.path.join(assets, 'c5_sand.bin'), 'wb') as f:
        f.write(struct.pack('<ii', nx8, ny8)); f.write(sand.astype(np.uint8).tobytes())
    print(f'  areia: {int(sand.sum())} vertices')
    W, wnx, wnz, wst = walk_raster(tris)
    write_walk(W, wnx, wnz, wst, os.path.join(assets, 'c5_walk.bin'))
    shutil.copy(os.path.join(out, 'city5_ground.bin'), os.path.join(assets, 'c5_mesh.bin'))
    shutil.copy(os.path.join(out, 'signs_atlas.png'), os.path.join(assets, 'c5_signs.png'))
    print('  exportado para', assets)


# ------------------------------------------------------------------------------------------------
# terreno x malha assada: o terreno do app (grade de 8 m, 2 triangulos por celula) nunca pode ficar acima do asfalto/calcada
PAVED = (15, 9, 3, 8)


def _read_ground(path):
    import struct
    b = open(path, 'rb').read(); n = struct.unpack_from('<i', b, 4)[0]; o = 8
    out = {}
    dt = np.dtype([('f', '<f4', 8), ('c', 'u1', 3)])
    for _ in range(n):
        cell, mat, nv, ymax = struct.unpack_from('<iiif', b, o); o += 16
        arr = np.frombuffer(b, dtype=dt, count=nv, offset=o); o += nv * 35
        if mat in PAVED:
            out.setdefault(mat, []).append(arr['f'][:, :6].copy())
    return {m: np.concatenate(v) for m, v in out.items()}


def _terr(hf, g, x, z):
    ny, nx = hf.shape
    fx = np.clip(x / g, 0, nx - 1.001); fz = np.clip(z / g, 0, ny - 1.001)
    i = fx.astype(int); j = fz.astype(int); tx = fx - i; tz = fz - j
    h00 = hf[j, i]; h10 = hf[j, i + 1]; h01 = hf[j + 1, i]; h11 = hf[j + 1, i + 1]
    up = tx >= tz
    return np.where(up, h00 + (h10 - h00) * tx + (h11 - h10) * tz, h00 + (h11 - h01) * tx + (h01 - h00) * tz), i, j, up


def fit_terrain(hf, ground_path, g=8.0, margin=0.05, tunnel=3.0):
    """abaixa os vertices do terreno onde ele cobriria a malha; devolve (hf novo, amostras pavimentadas x,z,y)"""
    G = _read_ground(ground_path)
    pts = []
    tris = []
    for m, V in G.items():
        if m != 15 and m != 9 and m != 3 and m != 8: continue
        T = V.reshape(-1, 3, 6)
        up = T[:, :, 4].mean(1) > 0.5
        T = T[up]
        tris.append(T[:, :, [0, 1, 2]])
    tris = np.concatenate(tris)                       # (n, 3, xyz)
    a, b_, c = tris[:, 0], tris[:, 1], tris[:, 2]
    S = np.concatenate([a, b_, c, (a + b_ + c) / 3, (a + b_) / 2, (b_ + c) / 2, (a + c) / 2, (2 * a + b_ + c) / 4, (a + 2 * b_ + c) / 4, (a + b_ + 2 * c) / 4])
    ny, nx = hf.shape
    h = hf.copy()
    t0, _, _, _ = _terr(h, g, S[:, 0], S[:, 2])
    act = (t0 - (S[:, 1] - margin)) < tunnel            # tunel/portal (terreno muito acima) fica de fora desde o inicio
    for it in range(8):
        t, i, j, up = _terr(h, g, S[:, 0], S[:, 2])
        viol = t - (S[:, 1] - margin)
        bad = (viol > 0.005) & act
        print(f'   passo {it}: {int(bad.sum())} amostras sob o terreno (max {viol[bad].max() if bad.any() else 0:.2f} m)')
        if not bad.any(): break
        i, j, up, v = i[bad], j[bad], up[bad], viol[bad]
        flat = h.reshape(-1); base = flat.copy()
        for (di, dj) in ((0, 0), (1, 0), (1, 1)):
            idx = (j + dj) * nx + (i + di)
            sel = up
            np.minimum.at(flat, idx[sel], base[idx[sel]] - v[sel])
        for (di, dj) in ((0, 0), (1, 1), (0, 1)):
            idx = (j + dj) * nx + (i + di)
            sel = ~up
            np.minimum.at(flat, idx[sel], base[idx[sel]] - v[sel])
        h = flat.reshape(ny, nx)
    return h, tris


def walk_raster(tris, step=2.0, size=(4400.0, 3600.0)):
    """alturas do chao pavimentado a cada 2 m (para o jogador/carro andarem em cima do asfalto); -32768 = sem pavimento"""
    nx = int(size[0] / step) + 1; nz = int(size[1] / step) + 1
    W = np.full((nz, nx), -1e9, np.float32)
    for t in tris:
        x0 = t[:, 0].min(); x1 = t[:, 0].max(); z0 = t[:, 2].min(); z1 = t[:, 2].max()
        i0 = max(int(np.ceil(x0 / step)), 0); i1 = min(int(np.floor(x1 / step)), nx - 1)
        j0 = max(int(np.ceil(z0 / step)), 0); j1 = min(int(np.floor(z1 / step)), nz - 1)
        if i1 < i0 or j1 < j0: continue
        xs = np.arange(i0, i1 + 1) * step; zs = np.arange(j0, j1 + 1) * step
        X, Z = np.meshgrid(xs, zs)
        ax, az = t[0, 0], t[0, 2]; bx, bz = t[1, 0] - ax, t[1, 2] - az; cx, cz = t[2, 0] - ax, t[2, 2] - az
        den = bx * cz - bz * cx
        if abs(den) < 1e-9: continue
        u = ((X - ax) * cz - (Z - az) * cx) / den; v = ((Z - az) * bx - (X - ax) * bz) / den
        ins = (u >= -1e-4) & (v >= -1e-4) & (u + v <= 1 + 1e-4)
        if not ins.any(): continue
        Y = t[0, 1] + u * (t[1, 1] - t[0, 1]) + v * (t[2, 1] - t[0, 1])
        sub = W[j0:j1 + 1, i0:i1 + 1]
        np.maximum(sub, np.where(ins, Y, -1e9), out=sub)
    return W, nx, nz, step


def write_walk(W, nx, nz, step, path):
    import struct
    cm = np.where(W < -1e8, -32768, np.clip(np.round(W * 100.0), -32000, 32000)).astype('<i2')
    with open(path, 'wb') as f:
        f.write(struct.pack('<iif', nx, nz, step)); f.write(cm.tobytes())
