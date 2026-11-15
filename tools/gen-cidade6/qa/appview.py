"""Visualizador "como no jogo": le os arquivos exportados para o app (c6.bin, c6_sand.bin, c6_*.bin SUB2) e desenha
terreno + agua (plano em -0,2 onde o terreno fica abaixo de -0,15) + malhas, com as duas faces (o jogo nao corta faces de tras)."""
import os, sys, struct, math, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from view6 import Source, Viewer
import app_export6 as AE
A = os.path.join(HERE, '..', '..', '..', 'app', 'src', 'main', 'assets', 'hds')


def load():
    S = Source()
    b = open(os.path.join(A, 'c6.bin'), 'rb').read(); nx, nz, g = struct.unpack_from('<iif', b, 0)
    h = np.frombuffer(b, '<i2', offset=12).reshape(nz, nx) / 100.0
    sb = open(os.path.join(A, 'c6_sand.bin'), 'rb').read(); sand = np.frombuffer(sb, np.uint8, offset=8).reshape(nz, nx).astype(bool)
    # terreno em blocos de 16x16 celulas
    gz, gx = np.gradient(h, g)
    N = np.dstack([-gx, np.ones_like(h), -gz]); N /= np.linalg.norm(N, axis=2, keepdims=True)
    C = np.where(sand[..., None], np.array([230, 214, 164]) / 255.0, np.array([150, 200, 120]) / 255.0)
    C = np.where((np.hypot(gx, gz) > 0.75)[..., None], np.array([168, 156, 132]) / 255.0, C)
    for j0 in range(0, nz - 1, 16):
        for i0 in range(0, nx - 1, 16):
            j1, i1 = min(j0 + 16, nz - 1), min(i0 + 16, nx - 1)
            jj, ii = np.mgrid[j0:j1 + 1, i0:i1 + 1]
            P = np.stack([ii * g, h[jj, ii], jj * g], -1).reshape(-1, 3).astype(np.float32)
            w = i1 - i0 + 1
            q = np.array([[(a * w + c, a * w + c + 1, (a + 1) * w + c + 1), (a * w + c, (a + 1) * w + c + 1, (a + 1) * w + c)] for a in range(j1 - j0) for c in range(i1 - i0)]).reshape(-1)
            S.parts.append((i0 * g, j0 * g, i1 * g, j1 * g, 'terreno', P, N[jj, ii].reshape(-1, 3).astype(np.float32), (P[:, [0, 2]] / 8.0).astype(np.float32), C[jj, ii].reshape(-1, 3), q[[0, 2, 1] * 0 + list(range(len(q)))] if False else q.reshape(-1, 3)[:, [0, 2, 1]].reshape(-1)))
            # agua
            hh = h[j0:j1 + 1, i0:i1 + 1]
            lo = np.minimum.reduce([hh[:-1, :-1], hh[1:, :-1], hh[:-1, 1:], hh[1:, 1:]]) < -0.15
            if lo.any():
                aj, ai = np.nonzero(lo); Pw = []; 
                for a, c in zip(aj, ai):
                    x0, z0 = (i0 + c) * g, (j0 + a) * g
                    Pw += [(x0, -0.2, z0), (x0, -0.2, z0 + g), (x0 + g, -0.2, z0 + g), (x0, -0.2, z0), (x0 + g, -0.2, z0 + g), (x0 + g, -0.2, z0)]
                Pw = np.array(Pw, np.float32)
                S.parts.append((i0 * g, j0 * g, i1 * g, j1 * g, 'agua', Pw, np.tile(np.array([[0, 1, 0]], np.float32), (len(Pw), 1)), (Pw[:, [0, 2]] / 14.0).astype(np.float32), np.tile(np.array([[0.75, 0.86, 0.92]]), (len(Pw), 1)), np.arange(len(Pw))))
    dt = np.dtype([('p', '<i2', 3), ('n', 'i1', 3), ('uv', '<f4', 2), ('c', 'u1', 3)])
    names = {0: 'liso'}; names.update({AE.MAT_BASE + i: m for i, m in enumerate(AE.MAT_ORDER)})
    for fn in AE.FILES:
        b = open(os.path.join(A, fn), 'rb').read(); n = struct.unpack_from('<i', b, 4)[0]; o = 8
        for _ in range(n):
            cell, mat, nv, ymax = struct.unpack_from('<iiif', b, o); o += 16
            q = np.frombuffer(b, dt, nv, o); o += nv * 20
            ox, oz = (cell % 1000) * 64.0, (cell // 1000) * 64.0
            P = np.stack([q['p'][:, 0] / 50.0 + ox, q['p'][:, 1] / 50.0, q['p'][:, 2] / 50.0 + oz], 1).astype(np.float32)
            S.parts.append((P[:, 0].min(), P[:, 2].min(), P[:, 0].max(), P[:, 2].max(), names[mat], P, (q['n'] / 127.0).astype(np.float32), q['uv'].astype(np.float32), q['c'] / 255.0, np.arange(nv)))
    # arvores do proprio app (lista do c6.json): tronco + copa simples
    J = json.load(open(os.path.join(A, 'c6.json')))
    tf = J.get('tree') or []; tl = [tf[i:i + 6] for i in range(0, len(tf), 6)]
    by = {}
    for t in tl: by.setdefault((int(t[0] // 64), int(t[1] // 64)), []).append(t)
    COL = [(0.30, 0.52, 0.22), (0.36, 0.58, 0.26), (0.26, 0.46, 0.2), (0.2, 0.4, 0.24)]
    for key, lst in by.items():
        P = []; C = []
        for t in lst:
            x, z, sp, sc = t[0], t[1], int(t[2]) % 4, t[3]
            i = min(max(int(x / g), 0), nx - 1); j = min(max(int(z / g), 0), nz - 1); y = h[j, i]
            R = 2.6 * sc; hh = 3.0 * sc; top = y + hh + R * 1.7; mid = y + hh + R * 0.6
            ring = [(x + R, mid, z), (x, mid, z + R), (x - R, mid, z), (x, mid, z - R)]
            for k in range(4):
                a, b = ring[k], ring[(k + 1) % 4]
                P += [a, b, (x, top, z), b, a, (x, y + hh * 0.7, z)]; C += [COL[sp]] * 3 + [tuple(c * 0.7 for c in COL[sp])] * 3
            P += [(x - 0.2, y, z), (x + 0.2, y, z), (x, y + hh, z)]; C += [(0.35, 0.26, 0.18)] * 3
        P = np.array(P, np.float32)
        S.parts.append((P[:, 0].min(), P[:, 2].min(), P[:, 0].max(), P[:, 2].max(), 'liso', P, np.tile(np.array([[0, 1, 0]], np.float32), (len(P), 1)), np.zeros((len(P), 2), np.float32), np.array(C), np.arange(len(P))))
    return S


if __name__ == '__main__':
    out = sys.argv[1]; S = load()
    v = Viewer(S, os.path.join(A, 'c6tex'))
    td = os.path.join(HERE, 'tex')
    for a in sys.argv[2:]:
        f = a.split(',')
        if f[1] == 'top': v.top(os.path.join(out, f'a_{f[0]}.png'), float(f[2]), float(f[3]), float(f[4]), 1000, 1000, 0.7)
        else:
            x, z, x2, z2, hh = map(float, f[1:6]); v.shot(os.path.join(out, f'a_{f[0]}.png'), (x, hh, z), (x2, 2.2, z2), R=430, fov=62, fog=(300, 430))
    v.run()
