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
    # arvores do jogo (Cidade 6): a arvore da Cidade 2 (c6_tree.bin), modelo inteiro ate NEAR m do ponto de vista, cartoes alem
    J = json.load(open(os.path.join(A, 'c6.json')))
    tf = J.get('tree') or []; tl = [tf[i:i + 6] for i in range(0, len(tf), 6)]
    tb = open(os.path.join(A, 'c6_tree.bin'), 'rb').read(); n = struct.unpack_from('<i', tb, 4)[0]; o = 8; TP = []
    for _ in range(n):
        mat, nv, ni, cr, cg, cb = struct.unpack_from('<iii3f', tb, o); o += 24
        V = np.frombuffer(tb, '<f4', nv * 8, o).reshape(nv, 8); o += nv * 32
        I = np.frombuffer(tb, '<u2', ni, o).astype(np.int64); o += ni * 2
        TP.append(('arvore_folhas' if mat == 57 else 'arvore_casca', V, I, np.array([cr, cg, cb])))
    H6 = max(t[1][:, 1].max() for t in TP); R6 = max(np.hypot(t[1][:, 0], t[1][:, 2]).max() for t in TP)
    SP6 = [(0.42, 0.42), (0.40, 0.45), (0.30, 0.30), (0.25, 0.47)]
    TINT = [(1, 1, 1), (0.88, 1.04, 0.86), (1.1, 1.02, 0.8), (0.74, 0.92, 0.82)]
    S.trees6 = (tl, TP, H6, R6, SP6, TINT, h, g, nx, nz)
    return S


def add_trees(S, cx, cz, near=90.0, far=420.0):
    """como o jogo: blocos de 64 m a menos de `near` do ponto de vista com o modelo, o resto com cartoes"""
    tl, TP, H6, R6, SP6, TINT, h, g, nx, nz = S.trees6
    S.parts = [p for p in S.parts if not str(p[4]).startswith('arvore')]
    acc = {}
    for t in tl:
        x, z, sp, sc, ry, k = t; sp = int(sp) % 4
        bx0, bz0 = (x // 64) * 64, (z // 64) * 64
        dd = math.hypot(max(0, bx0 - cx, cx - bx0 - 64), max(0, bz0 - cz, cz - bz0 - 64))
        if dd > far: continue
        i = min(max(int(x / g), 0), nx - 1); j = min(max(int(z / g), 0), nz - 1); y = h[j, i] - 0.05
        sx, sy = SP6[sp][0] * sc, SP6[sp][1] * sc; f = 0.86 + 0.26 * k; tint = np.array(TINT[sp]) * f
        cs, sn = math.cos(ry), math.sin(ry)
        if dd < near:
            for (mat, V, I, col) in TP:
                px, py, pz = V[:, 0] * sx, V[:, 1] * sy, V[:, 2] * sx
                P = np.stack([px * cs + pz * sn + x, py + y, -px * sn + pz * cs + z], 1)
                N = np.stack([V[:, 3] * cs + V[:, 5] * sn, V[:, 4], -V[:, 3] * sn + V[:, 5] * cs], 1)
                acc.setdefault(mat, []).append((P[I], N[I], V[I][:, 6:8], np.tile(col * tint, (len(I), 1))))
        else:
            leaf = [q for q in TP if q[0] == 'arvore_folhas'][0]
            hh = H6 * sy * 1.04; w = R6 * sx * 0.95; P = []; U = []
            for jj in range(3):
                a = ry + jj * math.pi / 3; c, s_ = math.cos(a) * w, math.sin(a) * w
                q = [(x - c, y, z - s_), (x + c, y, z + s_), (x + c, y + hh, z + s_), (x - c, y + hh, z - s_)]
                P += [q[0], q[1], q[2], q[0], q[2], q[3]]; U += [(0, 1), (1, 1), (1, 0), (0, 1), (1, 0), (0, 0)]
            P = np.array(P, np.float32)
            acc.setdefault('arvore_folhas', []).append((P, np.tile([0, 1, 0], (len(P), 1)), np.array(U, np.float32), np.tile(leaf[3] * tint, (len(P), 1))))
    for mat, l in acc.items():
        P = np.concatenate([q[0] for q in l]).astype(np.float32); N = np.concatenate([q[1] for q in l]).astype(np.float32)
        U = np.concatenate([q[2] for q in l]).astype(np.float32); C = np.clip(np.concatenate([q[3] for q in l]), 0, 1)
        for s0 in range(0, len(P), 300000):
            sl = slice(s0, s0 + 300000); p = P[sl]
            S.parts.append((p[:, 0].min(), p[:, 2].min(), p[:, 0].max(), p[:, 2].max(), mat, p, N[sl], U[sl], C[sl], np.arange(len(p))))


if __name__ == '__main__':
    out = sys.argv[1]; S = load()
    v = Viewer(S, os.path.join(A, 'c6tex'))
    td = os.path.join(HERE, 'tex')
    for a in sys.argv[2:]:
        f = a.split(',')
        if f[1] == 'top': add_trees(S, float(f[2]), float(f[3]), 0, 1e9); v.top(os.path.join(out, f'a_{f[0]}.png'), float(f[2]), float(f[3]), float(f[4]), 1000, 1000, 0.7)
        else:
            x, z, x2, z2, hh = map(float, f[1:6]); add_trees(S, x, z); v.shot(os.path.join(out, f'a_{f[0]}.png'), (x, hh, z), (x2, 2.2, z2), R=430, fov=62, fog=(300, 430))
    v.run()
