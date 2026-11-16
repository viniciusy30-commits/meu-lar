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
    for fn in list(AE.FILES) + ['c6_bld2.bin']:
        b = open(os.path.join(A, fn), 'rb').read(); n = struct.unpack_from('<i', b, 4)[0]; o = 8
        for _ in range(n):
            cell, mat, nv, ymax = struct.unpack_from('<iiif', b, o); o += 16
            q = np.frombuffer(b, dt, nv, o); o += nv * 20
            ox, oz = (cell % 1000) * 64.0, (cell // 1000) * 64.0
            P = np.stack([q['p'][:, 0] / 50.0 + ox, q['p'][:, 1] / 50.0, q['p'][:, 2] / 50.0 + oz], 1).astype(np.float32)
            S.parts.append((P[:, 0].min(), P[:, 2].min(), P[:, 0].max(), P[:, 2].max(), names[mat], P, (q['n'] / 127.0).astype(np.float32), q['uv'].astype(np.float32), q['c'] / 255.0, np.arange(nv)))
    # arvores do jogo (Cidade 6): a arvore da Cidade 2 (c6_tree.bin) e os arbustos/flores do app (assets/flora)
    J = json.load(open(os.path.join(A, 'c6.json')))
    tf = J.get('tree') or []; tl = [tf[i:i + 6] for i in range(0, len(tf), 6)]
    ty = J.get('tree_y') or []
    tb = open(os.path.join(A, 'c6_tree.bin'), 'rb').read(); n = struct.unpack_from('<i', tb, 4)[0]; o = 8; TP = []
    for _ in range(n):
        mat, nv, ni, cr, cg, cb = struct.unpack_from('<iii3f', tb, o); o += 24
        V = np.frombuffer(tb, '<f4', nv * 8, o).reshape(nv, 8); o += nv * 32
        I = np.frombuffer(tb, '<u2', ni, o).astype(np.int64); o += ni * 2
        TP.append(('arvore_folhas' if mat == 57 else 'arvore_casca', V, I, np.array([cr, cg, cb])))
    H6 = max(t[1][:, 1].max() for t in TP); R6 = max(np.hypot(t[1][:, 0], t[1][:, 2]).max() for t in TP)
    S.trees6 = (tl, ty, TP, H6, R6, h, g, nx, nz)
    return S


SP6 = [(0.42, 0.42), (0.40, 0.45), (0.30, 0.30), (0.25, 0.47)]
TINT = [(1, 1, 1), (0.88, 1.04, 0.86), (1.1, 1.02, 0.8), (0.74, 0.92, 0.82)]
PLANT6 = ['bush_a', 'bush_b', 'bush_pink', 'bush_white', 'hedge', 'fl_daisy', 'fl_tulip', 'fl_lav', 'fl_poppy', 'fl_yellow']
FL = os.path.join(HERE, '..', '..', '..', 'app', 'src', 'main', 'assets', 'flora')
_flora = {}


def flora(id_):
    if id_ in _flora: return _flora[id_]
    b = open(os.path.join(FL, id_ + '.bin'), 'rb').read(); o = 4; nt, np_ = struct.unpack_from('<ii', b, o); o += 8; names = []
    for _ in range(nt):
        n = b[o]; o += 1; names.append(b[o:o + n].decode()); o += n
    out = []
    for _ in range(np_):
        ti = struct.unpack_from('<h', b, o + 1)[0]; nv, ni = struct.unpack_from('<ii', b, o + 4); o += 12
        V = np.frombuffer(b, np.uint8, nv * 36, o).reshape(nv, 36); o += nv * 36
        I = np.frombuffer(b, '<u2', ni, o).astype(np.int64); o += ni * 2
        pos = V[:, :12].copy().view('<f4').reshape(nv, 3); nor = V[:, 12:24].copy().view('<f4').reshape(nv, 3)
        col = V[:, 24:28].astype(np.float32)[:, :3] / 255.0; uv = V[:, 28:36].copy().view('<f4').reshape(nv, 2)
        out.append(('flora_' + names[ti], pos, nor, col, uv, I))
    _flora[id_] = out; return out


def add_trees(S, cx, cz, near=90.0, far=420.0):
    """como o jogo: blocos de 64 m a menos de `near` com o modelo (e arbustos/flores), o resto com cartoes"""
    tl, ty, TP, H6, R6, h, g, nx, nz = S.trees6
    S.parts = [p for p in S.parts if not (str(p[4]).startswith('arvore') or str(p[4]).startswith('flora_'))]
    acc = {}
    for q, t in enumerate(tl):
        x, z, sp0, sc, ry, k = t; sp0 = int(sp0); sp = min(sp0, 3)
        bx0, bz0 = (x // 64) * 64, (z // 64) * 64
        dd = math.hypot(max(0, bx0 - cx, cx - bx0 - 64), max(0, bz0 - cz, cz - bz0 - 64))
        if dd > far: continue
        if q < len(ty): y = ty[q]
        else:
            i = min(max(int(x / g), 0), nx - 1); j = min(max(int(z / g), 0), nz - 1); y = h[j, i] - 0.05
        cs, sn = math.cos(ry), math.sin(ry)
        if sp0 >= 4:
            if dd >= near: continue
            f = 0.9 + 0.2 * k
            for (mat, pos, nor, col, uv, I) in flora(PLANT6[min(sp0 - 4, 9)]):
                px, py, pz = pos[:, 0] * sc, pos[:, 1] * sc, pos[:, 2] * sc
                P = np.stack([px * cs + pz * sn + x, py + y, -px * sn + pz * cs + z], 1)
                N = np.stack([nor[:, 0] * cs + nor[:, 2] * sn, nor[:, 1], -nor[:, 0] * sn + nor[:, 2] * cs], 1)
                acc.setdefault(mat, []).append((P[I], N[I], uv[I], col[I] * f))
            continue
        sx, sy = SP6[sp][0] * sc, SP6[sp][1] * sc; tint = np.array(TINT[sp]) * (0.86 + 0.26 * k)
        if dd < near:
            for (mat, V, I, col) in TP:
                px, py, pz = V[:, 0] * sx, V[:, 1] * sy, V[:, 2] * sx
                P = np.stack([px * cs + pz * sn + x, py + y, -px * sn + pz * cs + z], 1)
                N = np.stack([V[:, 3] * cs + V[:, 5] * sn, V[:, 4], -V[:, 3] * sn + V[:, 5] * cs], 1)
                acc.setdefault(mat, []).append((P[I], N[I], V[I][:, 6:8], np.tile(col * tint, (len(I), 1))))
        else:
            leaf = [q_ for q_ in TP if q_[0] == 'arvore_folhas'][0]
            y0 = y + 2.6 * sy; hh = H6 * sy * 1.02; w = R6 * sx * 0.92; P = []; U = []
            for jj in range(3):
                a_ = ry + jj * math.pi / 3; c, s_ = math.cos(a_) * w, math.sin(a_) * w
                qq = [(x - c, y0, z - s_), (x + c, y0, z + s_), (x + c, y + hh, z + s_), (x - c, y + hh, z - s_)]
                P += [qq[0], qq[1], qq[2], qq[0], qq[2], qq[3]]; U += [(0, .86), (1, .86), (1, 0), (0, .86), (1, 0), (0, 0)]
            P = np.array(P, np.float32)
            acc.setdefault('arvore_folhas', []).append((P, np.tile([0, 1, 0], (len(P), 1)), np.array(U, np.float32), np.tile(leaf[3] * tint, (len(P), 1))))
            tr = 0.5 * sx; ty1 = y + 5.2 * sy; P = []; U = []; N = []
            for jj in range(6):
                a0 = ry + jj * math.pi / 3; a1 = a0 + math.pi / 3; am = (a0 + a1) / 2
                p0 = (x + math.cos(a0) * tr, z + math.sin(a0) * tr); p1 = (x + math.cos(a1) * tr, z + math.sin(a1) * tr)
                vt = (ty1 - y) / 2
                P += [(p0[0], y, p0[1]), (p1[0], y, p1[1]), (p1[0], ty1, p1[1]), (p0[0], y, p0[1]), (p1[0], ty1, p1[1]), (p0[0], ty1, p0[1])]
                U += [(jj / 6, vt), ((jj + 1) / 6, vt), ((jj + 1) / 6, 0), (jj / 6, vt), ((jj + 1) / 6, 0), (jj / 6, 0)]; N += [(math.cos(am), 0, math.sin(am))] * 6
            acc.setdefault('arvore_casca', []).append((np.array(P, np.float32), np.array(N, np.float32), np.array(U, np.float32), np.tile([0.8, 0.78, 0.76], (len(P), 1))))
    for mat, l in acc.items():
        P = np.concatenate([q_[0] for q_ in l]).astype(np.float32); N = np.concatenate([q_[1] for q_ in l]).astype(np.float32)
        U = np.concatenate([q_[2] for q_ in l]).astype(np.float32); C = np.clip(np.concatenate([q_[3] for q_ in l]), 0, 1)
        for s0 in range(0, len(P), 300000):
            sl = slice(s0, s0 + 300000); p = P[sl]
            S.parts.append((p[:, 0].min(), p[:, 2].min(), p[:, 0].max(), p[:, 2].max(), mat, p, N[sl], U[sl], C[sl], np.arange(len(p))))


def texdir():
    """pasta de texturas do visualizador: as da Cidade 6 + as do app (flora_*.png)"""
    td = os.path.join(HERE, 'tmp', 'tex_all'); os.makedirs(td, exist_ok=True)
    for src, pre in ((os.path.join(A, 'c6tex'), ''), (os.path.join(FL, 'tex'), 'flora_')):
        for f in os.listdir(src):
            d = os.path.join(td, pre + f)
            if not os.path.exists(d): os.symlink(os.path.abspath(os.path.join(src, f)), d)
    return td



def add_city2_houses(S):
    """casas do jogador como o jogo monta (Hds.kt): pecas do city2.glb de cada lote, giradas em volta do centro da casa e na altura lvl + 0,08"""
    import struct as st
    b = open(os.path.join(A, 'city2.glb'), 'rb').read(); L = st.unpack_from('<I', b, 12)[0]; J = json.loads(b[20:20 + L])
    o = 20 + L; bl = st.unpack_from('<I', b, o)[0]; B = b[o + 8:o + 8 + bl]
    d = json.load(open(os.path.join(A, 'city2.json'))); hs = {h['k']: h for h in json.load(open(os.path.join(A, 'c6.json')))['houses']}

    def acc(i, comps):
        a_ = J['accessors'][i]; v = J['bufferViews'][a_['bufferView']]
        dt = {5126: '<f4', 5123: '<u2', 5125: '<u4'}[a_['componentType']]; sz = np.dtype(dt).itemsize
        stv = v.get('byteStride', sz * comps); off = v.get('byteOffset', 0) + a_.get('byteOffset', 0)
        raw = np.frombuffer(B, np.uint8, (a_['count'] - 1) * stv + sz * comps, off)
        return np.lib.stride_tricks.as_strided(raw, (a_['count'], sz * comps), (stv, 1)).copy().view(dt).reshape(a_['count'], comps)
    cache = {}
    out = {}
    for a_ in d['inst']:
        k = a_[14]
        if k < 0 or k not in hs: continue
        n = J['nodes'][a_[0]]
        if 'mesh' not in n: continue
        if a_[0] not in cache:
            ps = []
            for p in J['meshes'][n['mesh']]['primitives']:
                mt = J['materials'][p.get('material', 0)]; col = mt.get('pbrMetallicRoughness', {}).get('baseColorFactor', [0.8, 0.8, 0.8, 1])[:3]
                if mt.get('alphaMode') == 'BLEND' or 'Glass' in mt.get('name', ''): col = [0.55, 0.65, 0.75]
                ps.append((acc(p['attributes']['POSITION'], 3), acc(p['attributes']['NORMAL'], 3), acc(p['indices'], 1).reshape(-1).astype(np.int64), np.array(col)))
            cache[a_[0]] = ps
        pl = d['plots'][k]; cxs = (pl['x0'] + pl['x1']) / 2; czs = (pl['z0'] + pl['z1']) / 2; h = hs[k]
        Mx = np.array(a_[1:13]).reshape(3, 4); c_, s_ = math.cos(h['yaw']), math.sin(h['yaw'])
        for (P, N, I, col) in cache[a_[0]]:
            W_ = P @ Mx[:, :3].T + Mx[:, 3]; Nw = N @ Mx[:, :3].T
            tx = W_[:, 0] - cxs; tz = W_[:, 2] - czs
            X = c_ * tx - s_ * tz + h['x']; Z = s_ * tx + c_ * tz + h['z']; Y = W_[:, 1] + h['lvl'] + 0.08
            NX = c_ * Nw[:, 0] - s_ * Nw[:, 2]; NZ = s_ * Nw[:, 0] + c_ * Nw[:, 2]
            Pw = np.stack([X, Y, Z], 1)[I].astype(np.float32); Nn = np.stack([NX, Nw[:, 1], NZ], 1)[I]
            Nn = (Nn / np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-6)).astype(np.float32)
            out.setdefault(k, []).append((Pw, Nn, np.tile(col, (len(I), 1))))
    for k, l in out.items():
        P = np.concatenate([q[0] for q in l]); N = np.concatenate([q[1] for q in l]); C = np.clip(np.concatenate([q[2] for q in l]), 0, 1)
        S.parts.append((P[:, 0].min(), P[:, 2].min(), P[:, 0].max(), P[:, 2].max(), 'liso', P, N, np.zeros((len(P), 2), np.float32), C, np.arange(len(P))))

if __name__ == '__main__':
    out = sys.argv[1]; S = load(); add_city2_houses(S)
    v = Viewer(S, texdir())
    td = os.path.join(HERE, 'tex')
    for a in sys.argv[2:]:
        f = a.split(',')
        if f[1] == 'top': add_trees(S, float(f[2]), float(f[3]), 0, 1e9); v.top(os.path.join(out, f'a_{f[0]}.png'), float(f[2]), float(f[3]), float(f[4]), 1000, 1000, 0.7)
        else:
            x, z, x2, z2, hh = map(float, f[1:6]); add_trees(S, x, z); v.shot(os.path.join(out, f'a_{f[0]}.png'), (x, hh, z), (x2, 2.2, z2), R=430, fov=62, fog=(300, 430))
    v.run()
