"""Cidade 6 -> jogo (assets/hds/c6*), nos MESMOS formatos da Cidade 5:
  c6.bin        relevo (grade de 8 m, int16 em cm)            c6_sand.bin  mascara de areia
  c6_walk.bin   altura do chao andavel a cada 2 m             c6.json      casas do jogador, arvores do app, colisoes
  c6_mesh.bin / c6_bld.bin / c6_veg.bin   malha em pedacos de 64 m (formato SUB2, 20 bytes por vertice)
  c6tex/*.jpg   texturas (512 px) dos materiais da Cidade 6 (ids 26.. no app, na ordem de MAT_ORDER)
Tudo sobe DY = 0,7 m: no jogo a agua e um plano em y = -0,2 (o mar da Cidade 6 fica em -0,9)."""
import os, sys, json, math, struct, shutil
import numpy as np
from PIL import Image
from textures6 import MATS
from plan6 import W, H, shore_z

DY = 0.7
from roads6 import Y_WALK
G8 = 8.0
MAT_BASE = 26
MAT_ORDER = [m for m in sorted(MATS) if m != 'liso']
WALK_MATS = {'asfalto', 'calcada', 'paver', 'grama', 'concreto', 'ondas', 'madeira', 'quadra', 'areia', 'cascalho', 'pedra', 'terreno'}
FILES = {'c6_mesh.bin': ('ruas', 'orla', 'parques', 'mobiliario'), 'c6_bld.bin': ('lotes',), 'c6_veg.bin': ('vegetacao', 'carros')}


def mat_id(m):
    return 0 if m == 'liso' else MAT_BASE + MAT_ORDER.index(m)


def _split(tri, lim=56.0):
    """divide triangulos grandes (o app mostra cada triangulo pelo pedaco de 64 m do seu centro)"""
    out = []; stack = [tri]
    while stack:
        t = stack.pop()
        d = [np.abs(t[i, [0, 2]] - t[(i + 1) % 3, [0, 2]]).max() for i in range(3)]
        i = int(np.argmax(d))
        if d[i] <= lim: out.append(t); continue
        j, k = (i + 1) % 3, (i + 2) % 3
        m = (t[i] + t[j]) / 2
        a = np.stack([t[i], m, t[k]]); b = np.stack([m, t[j], t[k]])
        stack.append(a); stack.append(b)
    return out


def _tris(M, layers):
    """(material) -> array (n, 3, 13): x y z nx ny nz u v r g b ancX ancZ"""
    by = {}
    for (ti, tj, lay, mat), lst in M.data.items():
        if lay not in layers: continue
        for c in lst:
            if not len(c.idx): continue
            pn = np.frombuffer(c.pn.tobytes(), np.float32).reshape(-1, 6)
            uv = np.frombuffer(c.uv.tobytes(), np.float32).reshape(-1, 2)
            col = np.frombuffer(c.col.tobytes(), np.uint8).reshape(-1, 4)[:, :3].astype(np.float32)
            idx = np.frombuffer(c.idx.tobytes(), np.uint16).astype(np.int64)
            v = np.hstack([pn, uv, col])[idx].reshape(-1, 3, 11)
            anc = np.frombuffer(c.anc.tobytes(), np.float32).reshape(-1, 2)
            assert len(anc) == len(v), (lay, mat, len(anc), len(v))
            v = np.concatenate([v, np.repeat(anc[:, None, :], 3, axis=1)], axis=2)      # colunas 11, 12 = ancora do objeto
            by.setdefault(mat, []).append(v)
    return {m: np.concatenate(v) for m, v in by.items()}


def write_sub2(path, by_mat):
    dt = np.dtype([('p', '<i2', 3), ('n', 'i1', 3), ('uv', '<f4', 2), ('c', 'u1', 3)])
    recs = []; ntri = 0
    for m, T in sorted(by_mat.items()):
        T = T.astype(np.float64)
        ext = np.abs(T[:, :, [0, 2]].max(1) - T[:, :, [0, 2]].min(1)).max(1)
        big = ext > 56.0
        if big.any():
            extra = [s for t in T[big] for s in _split(t)]
            T = np.concatenate([T[~big], np.stack(extra)]) if extra else T[~big]
        cx = T[:, :, 0].mean(1); cz = T[:, :, 2].mean(1)
        ax, az = T[:, 0, 11], T[:, 0, 12]                                 # objeto inteiro no pedaco da sua ancora (predio nao fica pela metade)
        near = np.hypot(cx - ax, cz - az) < 38.0
        cx = np.where(near, ax, cx); cz = np.where(near, az, cz)
        cell = (np.clip(cz, 0, None) // 64).astype(np.int64) * 1000 + (np.clip(cx, 0, None) // 64).astype(np.int64)
        order = np.argsort(cell, kind='stable'); T = T[order]; cell = cell[order]
        bounds = np.flatnonzero(np.diff(cell)) + 1
        starts = np.concatenate([[0], bounds]); ends = np.concatenate([bounds, [len(cell)]])
        for s, e in zip(starts, ends):
            c = int(cell[s]); V = T[s:e].reshape(-1, 13)
            ox, oz = (c % 1000) * 64.0, (c // 1000) * 64.0
            o = np.zeros(len(V), dt)
            rel = np.stack([V[:, 0] - ox, V[:, 1] + DY, V[:, 2] - oz], 1) * 50.0
            assert np.abs(rel).max() < 32760, (m, c, np.abs(rel).max())
            o['p'] = np.round(rel).astype('<i2'); o['n'] = np.round(np.clip(V[:, 3:6], -1, 1) * 127).astype('i1')
            o['uv'] = V[:, 6:8].astype('<f4'); o['c'] = np.clip(V[:, 8:11], 0, 255).astype('u1')
            recs.append((c, mat_id(m), len(V), float(V[:, 1].max() + DY), o.tobytes())); ntri += len(V) // 3
    with open(path, 'wb') as f:
        f.write(b'SUB2'); f.write(struct.pack('<i', len(recs)))
        for (c, mid, nv, ymax, data) in recs:
            f.write(struct.pack('<iiif', c, mid, nv, ymax)); f.write(data)
    open(path + '.len', 'w').write(str(os.path.getsize(path)))
    return ntri


def walk_raster(T, nx, nz, step=2.0):
    Wk = np.full((nz, nx), -1e9, np.float32)
    for t in T:
        x0 = t[:, 0].min(); x1 = t[:, 0].max(); z0 = t[:, 2].min(); z1 = t[:, 2].max()
        i0 = max(int(np.ceil(x0 / step)), 0); i1 = min(int(np.floor(x1 / step)), nx - 1)
        j0 = max(int(np.ceil(z0 / step)), 0); j1 = min(int(np.floor(z1 / step)), nz - 1)
        if i1 < i0 or j1 < j0: continue
        X, Z = np.meshgrid(np.arange(i0, i1 + 1) * step, np.arange(j0, j1 + 1) * step)
        ax, az = t[0, 0], t[0, 2]; bx, bz = t[1, 0] - ax, t[1, 2] - az; cx, cz = t[2, 0] - ax, t[2, 2] - az
        den = bx * cz - bz * cx
        if abs(den) < 1e-9: continue
        u = ((X - ax) * cz - (Z - az) * cx) / den; v = ((Z - az) * bx - (X - ax) * bz) / den
        ins = (u >= -1e-4) & (v >= -1e-4) & (u + v <= 1 + 1e-4)
        if not ins.any(): continue
        Y = t[0, 1] + u * (t[1, 1] - t[0, 1]) + v * (t[2, 1] - t[0, 1])
        sub = Wk[j0:j1 + 1, i0:i1 + 1]
        np.maximum(sub, np.where(ins, Y, -1e9), out=sub)
    return Wk


def run(P, G, L, M, assets):
    os.makedirs(assets, exist_ok=True)
    # ---- relevo
    nx, nz = int(W / G8) + 2, int(H / G8) + 2
    X, Z = np.meshgrid(np.arange(nx) * G8, np.arange(nz) * G8)
    Hh = G.height(np.clip(X, 0, W), np.clip(Z, 0, H)) + DY
    from plan6 import river_x, RIVER_W, RIVER_WALL
    rxv = np.vectorize(river_x)(Z); dr = np.abs(X - rxv)
    Hh = np.where((dr < RIVER_W / 2 + RIVER_WALL + 1.0) & (Z < 1716), np.minimum(Hh, -1.2), Hh)      # a margem do rio no jogo fica escondida sob o cais/gramado
    cm = np.clip(np.round(Hh * 100.0), -32000, 32000).astype('<i2')
    with open(os.path.join(assets, 'c6.bin'), 'wb') as f:
        f.write(struct.pack('<iif', nx, nz, G8)); f.write(cm.tobytes())
    sand = (Z > 1712) & (Hh < 1.3)
    with open(os.path.join(assets, 'c6_sand.bin'), 'wb') as f:
        f.write(struct.pack('<ii', nx, nz)); f.write(sand.astype(np.uint8).tobytes())
    # ---- malhas
    tot = 0
    for fname, layers in FILES.items():
        n = write_sub2(os.path.join(assets, fname), _tris(M, layers)); tot += n
        print(f'  {fname}: {n} triangulos, {os.path.getsize(os.path.join(assets, fname)) / 1e6:.1f} MB')
    # ---- chao andavel (faces viradas para cima, baixas, de materiais de piso)
    wt = []
    for m, T in _tris(M, ('ruas', 'lotes', 'parques', 'orla')).items():
        if m not in WALK_MATS: continue
        up = (T[:, :, 4].mean(1) > 0.7) & (T[:, :, 1].max(1) < 1.6)
        if up.any(): wt.append(T[up][:, :, :3])
    wt = np.concatenate(wt).astype(np.float64)
    wnx, wnz = int(W / 2.0) + 3, int(H / 2.0) + 3
    Wk = walk_raster(wt, wnx, wnz)
    # seguranca: o terreno nunca fica acima do chao andavel vizinho (gramados/ruas perto do pe dos morros)
    from scipy.ndimage import minimum_filter
    big = np.where(Wk < -1e8, 1e9, Wk + DY)
    mn = minimum_filter(big, size=9)[::4, ::4]                       # menor chao andavel num raio de ~8 m, na grade de 8 m
    mn = np.pad(mn, ((0, max(0, nz - mn.shape[0])), (0, max(0, nx - mn.shape[1]))), constant_values=1e9)[:nz, :nx]
    fix = (mn < 1e8) & (Hh > mn - 0.25)
    Hh = np.where(fix, mn - 0.25, Hh)
    print(f'  terreno rebaixado sob o chao andavel em {int(fix.sum())} vertices')
    with open(os.path.join(assets, 'c6.bin'), 'wb') as f:
        f.write(struct.pack('<iif', nx, nz, G8)); f.write(np.clip(np.round(Hh * 100.0), -32000, 32000).astype('<i2').tobytes())
    cmw = np.where(Wk < -1e8, -32768, np.clip(np.round((Wk + DY) * 100.0), -32000, 32000)).astype('<i2')
    with open(os.path.join(assets, 'c6_walk.bin'), 'wb') as f:
        f.write(struct.pack('<iif', wnx, wnz, 2.0)); f.write(cmw.tobytes())
    print(f'  chao andavel: {len(wt)} triangulos, {int((Wk > -1e8).sum())} pontos')
    # ---- json
    houses = [{'k': h['k'], 'x': h['centro'][0], 'z': h['centro'][2], 'lvl': round(Y_WALK + DY - 0.08 - 0.10, 3), 'yaw': h['yaw']} for h in L.player]
    solidr = [v for (cx, cz, ux, uz, hu, hv) in L.B.colliders for v in (cx, cz, ux, uz, -hu, -hv, hu, hv)]
    trees = [v for t in L.props.app_trees for v in t]
    tree_y = [round(y + DY, 2) for y in L.props.app_y]                 # altura do chao de cada planta (canteiro, calcada, gramado)
    js = {'world': [float(W), float(H)], 'roads': [], 'rounds': [], 'nodes': [], 'houses': houses, 'bld': [], 'lamp': [], 'hyd': [], 'tree': trees, 'tree_y': tree_y, 'solid': [], 'solidr': solidr,
          'c6': {'dy': DY, 'mats': MAT_ORDER}}
    json.dump(js, open(os.path.join(assets, 'c6.json'), 'w'), separators=(',', ':'))
    print(f'  {len(houses)} casas, {len(trees) // 6} arvores do app, {len(solidr) // 8} colisoes')
    # ---- texturas (512 px)
    td = os.path.join(assets, 'c6tex'); os.makedirs(td, exist_ok=True)
    for m in MAT_ORDER:
        img = Image.fromarray(np.clip(MATS[m][0](), 0, 255).astype(np.uint8)).resize((512, 512), Image.LANCZOS)
        img.save(os.path.join(td, m + '.jpg'), quality=88)
    print(f'  {len(MAT_ORDER)} texturas; total da malha: {tot} triangulos')
    return MAT_ORDER
