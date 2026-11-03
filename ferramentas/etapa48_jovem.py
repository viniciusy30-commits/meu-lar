#!/usr/bin/env python3
"""Etapa 48: anatomia do corpo Jovem (e demais grupos, se pedido): coluna reta, ombros/claviculas certos, bracos junto do corpo.
Refaz, SEM precisar dos OBJ originais, a partir dos proprios assets ja gerados:
  - assets/cute/p_body_<g>{0,1,3}.bin (malha em repouso)  -> novos pesos de pele
  - assets/cute/clips_<g>.bin (so p/ recuperar as juntas de repouso por minimos quadrados) -> novos clipes
Uso: python3 etapa48_jovem.py <assets/cute> <grupos: tf tm ...> [--out <pasta>] [--check]
"""
import sys, os, struct
_here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, _here)
CU = sys.argv[1].rstrip('/') + '/'
os.environ['BASE_BIN'] = CU + 'base.bin'
import numpy as np
import etapa45_rig as R
from etapa11_base import GP, K

DT = np.dtype([('pos', '<f4', 3), ('nor', '<f4', 3), ('uv', '<f4', 2), ('col', 'u1', 4), ('bi', 'u1', 4), ('bw', 'u1', 4)])
SW = 0.968
TARGET_DEG = {0: 6.0, 1: 6.0, 3: 5.0, 4: 6.0, 5: 6.0, 6: 5.0}   # abertura final do braco (graus da vertical) por clipe; pulo (2) nao muda

def read_piece(path):
    b = open(path, 'rb').read(); assert b[:4] == b'CUP1'
    nv, ni, fl = struct.unpack('<3i', b[4:16]); o = 16
    v = np.frombuffer(b, DT, nv, o).copy(); o += nv * 44
    idx = np.frombuffer(b, '<u2', ni, o).reshape(-1, 3).copy(); o += ni * 2
    return v, idx, fl, b[o:]

def write_piece(path, v, idx, fl, tail):
    with open(path, 'wb') as f:
        f.write(b'CUP1' + struct.pack('<3i', len(v), idx.size, fl)); f.write(v.tobytes()); f.write(idx.astype('<u2').tobytes()); f.write(tail)

def read_clips(path):
    b = open(path, 'rb').read(); assert b[:4] == b'CLP1'
    nb, nc = struct.unpack('<2i', b[4:12]); o = 12; out = []
    for _ in range(nc):
        ln, nf = struct.unpack('<fi', b[o:o + 8]); o += 8
        d = np.frombuffer(b, '<f4', nf * nb * 12, o).reshape(nf, nb, 12).copy(); o += nf * nb * 12 * 4; out.append((ln, d))
    return out

def write_clips(path, clips):
    out = bytearray(b'CLP1' + struct.pack('<2i', 55, len(clips)))
    for ln, d in clips:
        d = np.ascontiguousarray(d, dtype='<f4'); out += struct.pack('<fi', float(ln), d.shape[0]) + d.tobytes()
    open(path, 'wb').write(bytes(out))

def recover_Q(cl):
    """juntas de repouso (unid. de armazenamento) a partir dos clipes: tn_i - tn_pai = (Dn_pai - Dn_i) Q_i"""
    Q = np.zeros((25, 3))
    for i in range(1, 25):
        p = GP[i]; A = []; b = []
        for ln, d in cl:
            M = d[:, :25].reshape(len(d), 25, 3, 4).astype(np.float64) / K
            A.append((M[:, p, :, :3] - M[:, i, :, :3]).reshape(-1, 3)); b.append((M[:, i, :, 3] - M[:, p, :, 3]).reshape(-1))
        Q[i] = np.linalg.lstsq(np.vstack(A), np.concatenate(b), rcond=None)[0]
    return Q

def body_part(v, idx):
    nb = int(np.argmax(v['uv'][:, 0] >= 0.5))
    return nb, idx[(idx < nb).all(1)]

def sc_of(ratio): return 100.0 / ratio * SW

def abduction(clips, Q25):
    """abertura media (graus da vertical, plano frontal) do braco esquerdo (ombro->cotovelo) por clipe"""
    ua, la = R.BI['upperarm_l'], R.BI['lowerarm_l']; res = []
    for ln, d in clips:
        M = d[:, :25].reshape(len(d), 25, 3, 4).astype(np.float64) / K
        ps = np.einsum('fij,j->fi', M[:, ua, :, :3], Q25[ua]) + M[:, ua, :, 3]
        pe = np.einsum('fij,j->fi', M[:, la, :, :3], Q25[la]) + M[:, la, :, 3]
        v = pe - ps; res.append(float(np.degrees(np.arctan2(v[:, 0].mean() * 1, -v[:, 1].mean()))))
    return res

def adduct(clips, Q25, degs):
    from etapa11_base import K as KK
    out = []
    for ci, (ln, res) in enumerate(clips):
        deg = degs.get(ci, 0.0); res = res.copy()
        if abs(deg) > 1e-6:
            a = np.radians(deg)
            for f in range(res.shape[0]):
                M = res[f].reshape(-1, 3, 4).astype(np.float64) / KK
                for side, sg in (('l', -1.0), ('r', 1.0)):
                    ua = R.BI['upperarm_' + side]; hd = R.BI['hand_' + side]
                    p = M[ua, :, :3] @ Q25[ua] + M[ua, :, 3]
                    th = sg * a; c, s = np.cos(th), np.sin(th)
                    Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
                    for b in [ua, ua + 1, hd] + (list(range(25, 40)) if side == 'l' else list(range(40, 55))):
                        M[b, :, :3] = Rz @ M[b, :, :3]; M[b, :, 3] = Rz @ (M[b, :, 3] - p) + p
                res[f] = (M * KK).reshape(-1, 12).astype(np.float32)
        out.append((ln, res))
    return out

# flexao final do cotovelo (graus; 0 = braco reto) = FLEX0 + (flexao original - FLEX0) * KEEP. Parado: relaxado (~8 graus); andar: balanco suave; correr/pulo: como o clipe.
ELBOW = {0: (8.0, 0.0), 1: (8.0, 0.55), 4: (8.0, 0.0), 5: (8.0, 0.55)}
def _arc(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); c = float(a @ b)
    if c > 0.999999: return np.eye(3)
    v = np.cross(a, b); vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + vx + vx @ vx / (1 + c)

def relax_elbows(clips, Q25, spec):
    from etapa11_base import K as KK
    out = []
    for ci, (ln, res) in enumerate(clips):
        res = res.copy()
        if ci in spec:
            f0, keep = spec[ci]
            for f in range(res.shape[0]):
                M = res[f].reshape(-1, 3, 4).astype(np.float64) / KK
                for side in ('l', 'r'):
                    ua, la, hd = R.BI['upperarm_' + side], R.BI['lowerarm_' + side], R.BI['hand_' + side]
                    P = lambda b: M[b, :, :3] @ Q25[b] + M[b, :, 3]
                    s_, e_, h_ = P(ua), P(la), P(hd)
                    a = (e_ - s_) / np.linalg.norm(e_ - s_); b = (h_ - e_) / np.linalg.norm(h_ - e_)
                    fl = np.arccos(np.clip(a @ b, -1, 1)); fn = np.radians(f0) + (fl - np.radians(f0)) * keep
                    if fl <= fn: continue
                    perp = b - (a @ b) * a; perp /= np.linalg.norm(perp)
                    bn = a * np.cos(fn) + perp * np.sin(fn); Rr = _arc(b, bn)
                    for q in [la, hd] + (list(range(25, 40)) if side == 'l' else list(range(40, 55))):
                        M[q, :, :3] = Rr @ M[q, :, :3]; M[q, :, 3] = Rr @ (M[q, :, 3] - e_) + e_
                res[f] = (M * KK).reshape(-1, 12).astype(np.float32)
        out.append((ln, res))
    return out

def align_hands(clips, Q25, skip=(2,)):
    """mao = continuacao do antebraco (mesma rotacao, pivo no punho); antes herdava a rotacao do clipe antigo e o punho ficava torto"""
    from etapa11_base import K as KK
    out = []
    for ci, (ln, res) in enumerate(clips):
        res = res.copy()
        if ci not in skip:
            for f in range(res.shape[0]):
                M = res[f].reshape(-1, 3, 4).astype(np.float64) / KK
                for side in ('l', 'r'):
                    la, hd = R.BI['lowerarm_' + side], R.BI['hand_' + side]
                    Rl = M[la, :, :3]; ph = Rl @ Q25[hd] + M[la, :, 3]
                    M[hd, :, :3] = Rl; M[hd, :, 3] = ph - Rl @ Q25[hd]
                    for q in (range(25, 40) if side == 'l' else range(40, 55)): M[q] = M[hd]
                res[f] = (M * KK).reshape(-1, 12).astype(np.float32)
        out.append((ln, res))
    return out

def run(grp, ratios, outdir, check=False):
    v1, i1, fl1, tail1 = read_piece(CU + 'p_body_%s1.bin' % grp)
    old = read_clips(CU + 'clips_%s.bin' % grp); Qold = recover_Q(old)
    sc = sc_of(ratios[grp + '1']); u = ratios[grp + '1']
    nb, T = body_part(v1, i1); P = v1['pos'][:nb].astype(np.float64) / sc
    face_ymin = Qold[R.BI['head']][1] / sc - 0.07 * u
    J, cls = R.fit_joints(P, T, face_ymin, None)
    Qnew = np.array([J[nm] for nm in R.BONES]) * sc
    if check:
        print('juntas (antigo recuperado -> novo), unid. de armazenamento:')
        for k, nm in enumerate(R.BONES): print('  %-12s %s -> %s' % (nm, Qold[k].round(1), Qnew[k].round(1)))
    # pesos novos para as 3 variantes (cada uma com a propria malha, juntas do grupo)
    for typ in (0, 1, 3):
        fn = CU + 'p_body_%s%d.bin' % (grp, typ)
        if not os.path.exists(fn): continue
        v, idx, fl, tail = read_piece(fn); nbv, Tv = body_part(v, idx)
        Pv = v['pos'][:nbv].astype(np.float64) / sc
        bi, bw = R.skin_weights(Pv, Tv, J, R.classify(Pv, Tv), face_ymin - 0.003)
        v['bi'][:nbv] = bi; v['bw'][:nbv] = bw
        write_piece(outdir + os.path.basename(fn), v, idx, fl, tail)
    # clipes novos
    rest = v1['pos'][:nb].astype(np.float64); sole = np.nonzero(rest[:, 1] < 0.05 * rest[:, 1].max())[0]
    v1n, _, _, _ = read_piece(outdir + 'p_body_%s1.bin' % grp)
    cl = R.retarget_clips(Qnew, v1n['bi'][:nb], v1n['bw'][:nb], rest, sole)
    cl = align_hands(cl, Qnew)
    ab = abduction(cl, Qnew)
    degs = {ci: ab[ci] - TARGET_DEG[ci] for ci in TARGET_DEG if ci < len(cl)}
    print(grp, 'abertura do braco por clipe (antes de aproximar):', [round(a, 1) for a in ab], '-> aproximar', {k: round(x, 1) for k, x in degs.items()})
    cl = adduct(cl, Qnew, degs)
    cl = relax_elbows(cl, Qnew, ELBOW)
    write_clips(outdir + 'clips_%s.bin' % grp, cl)
    return Qnew

if __name__ == '__main__':
    args = [a for a in sys.argv[2:] if not a.startswith('--')]
    out = CU
    if '--out' in sys.argv: out = sys.argv[sys.argv.index('--out') + 1].rstrip('/') + '/'; args = [a for a in args if a != out.rstrip('/')]
    os.makedirs(out, exist_ok=True)
    ratios = {}
    for ln in open(CU + 'simbodies.txt'):
        if ln.startswith('#') or not ln.strip(): continue
        p = ln.strip().split('|'); ratios[p[0]] = float(p[4])
    for g in args: run(g, ratios, out, '--check' in sys.argv)
