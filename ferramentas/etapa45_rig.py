"""Etapa 45: esqueleto ajustado direto na malha do Sims 3 + pesos por difusao + adaptacao dos clipes do app (modulo usado por etapa45_sims_rig.py)."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import os
BASE_BIN=os.environ.get('BASE_BIN','base.bin')
BOZO_Y = [0, 0.116, 0.262, 0.403, 0.606, 1.0]   # fracoes da coluna (pelvis..spine_05) so como distribuicao

def islands(P, T):
    n = len(P); a = np.r_[T[:, 0], T[:, 1], T[:, 2]]; b = np.r_[T[:, 1], T[:, 2], T[:, 0]]
    k, lab = connected_components(coo_matrix((np.ones(len(a)), (a, b)), shape=(n, n)), directed=False)
    return lab

def classify(P, T):
    """rotulo por vertice: 'armL','armR','torso','legs','foot' (pelas ilhas de UV)"""
    lab = islands(P, T); out = np.array(['?'] * len(P), dtype=object)
    ymax = P[:, 1].max()
    for i in np.unique(lab):
        q = P[lab == i]
        if len(q) < 20: continue
        cx = q[:, 0].mean(); xr = np.abs(q[:, 0]).max()
        if xr > 0.28 * ymax and cx > 0.05: c = 'armL'
        elif xr > 0.28 * ymax and cx < -0.05: c = 'armR'
        elif q[:, 1].max() < 0.2 * ymax: c = 'foot'
        elif q[:, 1].max() > 0.9 * ymax: c = 'torso'
        else: c = 'legs'
        out[lab == i] = c
    out[out == '?'] = 'torso'
    return out

def slice_c(Q, y, tol, xs=None):
    s = Q[np.abs(Q[:, 1] - y) < tol]
    if xs is not None: s = s[(s[:, 0] >= xs[0]) & (s[:, 0] <= xs[1])]
    return s.mean(0) if len(s) else None

def fit_joints(P, T, face_ymin=None, face_ymax=None):
    """P em metros (obj). Devolve dict nome->posicao (metros) para os 25 ossos."""
    cls = classify(P, T); H = P[:, 1].max(); u = H / 1.675
    J = {}
    # ---- braco esquerdo (+x) ----
    A = P[cls == 'armL']
    c0 = A.mean(0)
    # eixo: PCA dos centroides de fatias ao longo do comprimento (sem a mao)
    d0 = A[np.argmax(A[:, 0])] - A[np.argmin(A[:, 0])]; d0 /= np.linalg.norm(d0)
    s = (A - c0) @ d0; lo, hi = s.min(), s.max()
    cs = []; ss = []
    for t in np.linspace(lo + 0.08 * (hi - lo), lo + 0.62 * (hi - lo), 14):
        m = np.abs(s - t) < 0.012 * u
        if m.sum() > 3: cs.append(A[m].mean(0)); ss.append(t)
    cs = np.array(cs); cm = cs.mean(0); _, _, vt = np.linalg.svd(cs - cm); d = vt[0] * np.sign(vt[0][0])
    tip = A[np.argmax((A - cm) @ d)]; tipp = (tip - cm) @ d
    xsh = A[:, 0].min() + 0.035 * u
    ssh = (xsh - cm[0]) / d[0]; Jsh = cm + d * ssh
    La = tipp - ssh
    J['upperarm_l'] = Jsh; J['lowerarm_l'] = cm + d * (ssh + 0.42 * La); J['hand_l'] = cm + d * (ssh + 0.76 * La)
    J['_handtip_l'] = cm + d * tipp
    # ---- pernas ----
    L = P[(cls == 'legs') | (cls == 'foot')]; Lr = L[L[:, 0] > 0.0]
    Lc = P[cls == 'legs']; crotch = None; zr = (Lc[:, 2].min() + Lc[:, 2].max()) / 2
    for y in np.arange(0.95 * u, 0.25 * u, -0.004 * u):
        sl = Lc[(np.abs(Lc[:, 1] - y) < 0.006 * u) & (Lc[:, 2] < zr - 0.02 * u)]
        if len(sl) and np.abs(sl[:, 0]).min() > 0.012 * u: crotch = y + 0.004 * u; break
    if crotch is None: crotch = 0.5 * (face_ymax if face_ymax else H)
    yh = crotch + 0.035 * u
    sl = Lr[(np.abs(Lr[:, 1] - (crotch - 0.12 * u)) < 0.02 * u) & (Lr[:, 0] > 0.0)]
    hx = 0.5 * (sl[:, 0].min() + sl[:, 0].max()) if len(sl) else 0.09 * u
    zc = 0.5 * (sl[:, 2].min() + sl[:, 2].max()) if len(sl) else 0.0
    J['thigh_l'] = np.array([hx, yh, zc])
    yk = 0.285 * H; ka = slice_c(Lr, yk, 0.015 * u); J['calf_l'] = np.array([ka[0], yk, ka[2]])
    ya = 0.045 * H; aa = slice_c(Lr, 0.11 * u, 0.02 * u); J['foot_l'] = np.array([aa[0], ya, aa[2] - 0.012 * u])
    F = P[cls == 'foot']; F = F[F[:, 0] > 0]; tipz = F[:, 2].max()
    J['ball_l'] = np.array([aa[0], 0.022 * u, tipz - 0.075 * u]); J['_toe_l'] = np.array([aa[0], 0.012 * u, tipz])
    # ---- coluna / pescoco ----
    Tt = P[cls == 'torso']; ytop = Tt[:, 1].max()
    ysh = J['upperarm_l'][1]
    if face_ymin is None: face_ymin = ytop - 0.06 * u
    yh_ = face_ymin + 0.07 * u; y1 = ysh + 0.06 * u; y2 = (y1 + yh_) / 2; y5 = ysh - 0.03 * u
    def zmid(y, w=0.12):
        s_ = Tt[(np.abs(Tt[:, 1] - y) < 0.012 * u) & (np.abs(Tt[:, 0]) < w * u)]
        return (s_[:, 2].min() + 0.55 * (s_[:, 2].max() - s_[:, 2].min())) if len(s_) else 0.0
    sn_ = Tt[(np.abs(Tt[:, 1] - y2) < 0.012 * u) & (np.abs(Tt[:, 0]) < 0.05 * u)]; zn = sn_[:, 2].mean() if len(sn_) else 0.0
    J['head'] = np.array([0, yh_, zn - 0.004 * u]); J['neck_02'] = np.array([0, y2, zn]); J['neck_01'] = np.array([0, y1, zn])
    z5 = zmid(y5); J['spine_05'] = np.array([0, y5, z5])
    pz = J['thigh_l'][2]; J['pelvis'] = np.array([0, yh, pz])
    for i, f in enumerate(BOZO_Y[1:-1], 1):
        y = yh + f * (y5 - yh); J['spine_0%d' % i] = np.array([0, y, pz + f * (z5 - pz)])
    J['clavicle_l'] = np.array([0.02 * u, y5 + 0.042 * u, z5 - 0.008 * u])
    J['_ytop'] = ytop; J['_H'] = H
    # espelha direita
    for k in list(J):
        if k.endswith('_l'):
            q = J[k].copy(); q[0] = -q[0]; J[k[:-2] + '_r'] = q
    return J, cls

# ---------------- pesos (difusao de calor na malha soldada) ----------------
from scipy.sparse import csr_matrix, diags
from scipy.sparse.linalg import splu
BONES = ['pelvis','spine_01','spine_02','spine_03','spine_04','spine_05','neck_01','neck_02','head',
         'clavicle_l','upperarm_l','lowerarm_l','hand_l','clavicle_r','upperarm_r','lowerarm_r','hand_r',
         'thigh_l','calf_l','foot_l','ball_l','thigh_r','calf_r','foot_r','ball_r']
BI = {n: i for i, n in enumerate(BONES)}      # indices iguais aos do esqueleto do app (0..24)
def segments(J):
    S = {}
    ch = {'pelvis':'spine_01','spine_01':'spine_02','spine_02':'spine_03','spine_03':'spine_04','spine_04':'spine_05','spine_05':'neck_01',
          'neck_01':'neck_02','neck_02':'head'}
    for a, c in ch.items(): S[a] = (J[a], J[c])
    S['head'] = (J['head'], J['head'] + np.array([0, 0.12, 0]) * J['_H'] / 1.675)
    for sd in ('l', 'r'):
        S['clavicle_' + sd] = (J['clavicle_' + sd], J['upperarm_' + sd]); S['upperarm_' + sd] = (J['upperarm_' + sd], J['lowerarm_' + sd])
        S['lowerarm_' + sd] = (J['lowerarm_' + sd], J['hand_' + sd]); S['hand_' + sd] = (J['hand_' + sd], J['_handtip_' + sd])
        S['thigh_' + sd] = (J['thigh_' + sd], J['calf_' + sd]); S['calf_' + sd] = (J['calf_' + sd], J['foot_' + sd])
        S['foot_' + sd] = (J['foot_' + sd], J['ball_' + sd]); S['ball_' + sd] = (J['ball_' + sd], J['_toe_' + sd])
    return S
def seg_dist(P, a, b):
    ab = b - a; t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1); return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
ALLOW = {
 'armL': ['clavicle_l','upperarm_l','lowerarm_l','hand_l'], 'armR': ['clavicle_r','upperarm_r','lowerarm_r','hand_r'],
 'torso': ['pelvis','spine_01','spine_02','spine_03','spine_04','spine_05','neck_01','neck_02','head','clavicle_l','clavicle_r'],
 'legs': ['pelvis','spine_01','thigh_l','calf_l','thigh_r','calf_r'],
 'foot': ['calf_l','foot_l','ball_l','calf_r','foot_r','ball_r']}
def skin_weights(P, T, J, cls, head_y, k_anchor=0.35, r0=0.035):
    """P (n,3) m; devolve BI (n,4) uint8 e BW (n,4) uint8"""
    u = J['_H'] / 1.675; n = len(P)
    key = np.round(P * 1e5).astype(np.int64); uq, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1)
    m = len(uq); Q = P[first]; qc = cls[first]
    # grafo (cotan seria melhor; pesos por 1/aresta bastam para esta malha)
    a = inv[np.r_[T[:, 0], T[:, 1], T[:, 2]]]; b = inv[np.r_[T[:, 1], T[:, 2], T[:, 0]]]
    ok = a != b; a, b = a[ok], b[ok]
    w = 1.0 / np.maximum(np.linalg.norm(Q[a] - Q[b], axis=1), 1e-4) * 0.02
    Wm = csr_matrix((np.r_[w, w], (np.r_[a, b], np.r_[b, a])), shape=(m, m)); Wm.sum_duplicates(); Wm.data[:] = np.minimum(Wm.data, 8.0)
    deg = np.asarray(Wm.sum(1)).ravel(); L = diags(deg) - Wm
    S = segments(J); A = np.zeros((m, len(BONES))); D = np.zeros(m)
    for v in range(m): pass
    for cname, allowed in ALLOW.items():
        sel = np.nonzero(qc == cname)[0]
        if len(sel) == 0: continue
        dd = np.stack([seg_dist(Q[sel], *S[bn]) for bn in allowed], 1)
        if cname in ('legs',):   # lado do corpo: perna esquerda so para x>0 (perto do centro vale qualquer uma)
            for j, bn in enumerate(allowed):
                if bn.endswith('_l'): dd[:, j] += np.where(Q[sel, 0] < -0.01 * u, 1.0, 0)
                if bn.endswith('_r'): dd[:, j] += np.where(Q[sel, 0] > 0.01 * u, 1.0, 0)
        jb = dd.argmin(1)
        for j, bn in enumerate(allowed): A[sel[jb == j], BI[bn]] = 1.0
        D[sel] = dd.min(1)
    unk = A.sum(1) == 0; A[unk, BI['spine_02']] = 1.0
    h = deg * k_anchor * (r0 / np.maximum(D, 0.008)) ** 2 + 1e-3
    # cabeca: do corte do rosto para cima = 100% cabeca (casa com a malha rigida do rosto)
    top = Q[:, 1] >= head_y
    A[top] = 0; A[top, BI['head']] = 1.0; h[top] = 1e4
    Wt = splu((L + diags(h)).tocsc()).solve(h[:, None] * A)
    Wt = np.clip(Wt, 0, None)
    # 4 maiores
    idx = np.argsort(-Wt, 1)[:, :4]; val = np.take_along_axis(Wt, idx, 1); val = np.where(val < 0.02, 0, val); val /= val.sum(1, keepdims=True)
    q = np.round(val * 255).astype(int); q[:, 0] += 255 - q.sum(1)
    return idx[inv].astype(np.uint8), q[inv].astype(np.uint8)

# ---------------- animacao: adapta os clipes do app ao esqueleto novo ----------------
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etapa11_base import read_base as _rb, recover_bind as _rbind, GP as _GP, K as _K, NB as _NB
_BASE = None
def bozo():
    global _BASE
    if _BASE is None:
        bs = _rb(BASE_BIN)
        _BASE = (bs, _rbind(bs['clips'], bs['ver']))
    return _BASE
CMAP = {0:1,1:2,2:3,3:4,4:5,5:6,6:7,7:8, 9:10,10:11,11:12, 13:14,14:15,15:16, 17:18,18:19,19:20, 21:22,22:23,23:24}
def _arc(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); c = float(a @ b)
    if c < -0.9999:
        ax = np.cross(a, [1, 0, 0]); ax /= np.linalg.norm(ax); return 2 * np.outer(ax, ax) - np.eye(3)
    v = np.cross(a, b); vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + vx + vx @ vx / (1 + c)
def retarget_clips(Q25, bi, bw, rest, sole_ids):
    """Q25: (25,3) juntas do Sims em unidades de armazenamento; rest: vertices (n,3) em repouso (mesmas unidades); devolve lista [(len, (nf,55,12))]"""
    bs, Pb = bozo(); out = []
    Q = np.zeros((_NB, 3)); Q[:25] = Q25
    for ln, d in bs['clips']:
        nf = d.shape[0]; res = np.zeros((nf, _NB, 12), np.float32)
        for f in range(nf):
            A = d[f].reshape(_NB, 3, 4).astype(np.float64); R = A[:, :, :3] / _K; t = A[:, :, 3] / _K
            p = np.einsum('bij,bj->bi', R, Pb) + t
            Dn = np.zeros((25, 3, 3)); pn = np.zeros((25, 3))
            for i in range(25):
                Dn[i] = R[i]
                if i in CMAP:
                    c = CMAP[i]; a = p[c] - p[i]; dn = Q[c] - Q[i]
                    Dn[i] = _arc(R[i] @ dn, a) @ R[i]
                if i == 0: pn[0] = Q[0] + (p[0] - Pb[0])
                else: pn[i] = pn[_GP[i]] + Dn[_GP[i]] @ (Q[i] - Q[_GP[i]])
            tn = pn - np.einsum('bij,bj->bi', Dn, Q[:25])
            # trava de chao: ponto mais baixo da sola em y = 0
            ys = np.zeros(len(sole_ids))
            for k in range(4):
                bb = bi[sole_ids, k]; ww = bw[sole_ids, k] / 255.0
                ys += ww * (np.einsum('vj,vj->v', Dn[bb][:, 1, :], rest[sole_ids]) + tn[bb][:, 1])
            tn[:, 1] -= ys.min()
            M = np.zeros((_NB, 3, 4)); M[:25, :, :3] = Dn; M[:25, :, 3] = tn
            for fb in list(range(25, 40)): M[fb] = M[12]
            for fb in list(range(40, 55)): M[fb] = M[16]
            res[f] = (M * _K).reshape(_NB, 12)
        out.append((ln, res))
    return out
def pose_mesh(rest, bi, bw, M55):
    """M55: (55,12) -> posicoes em metros"""
    M = M55.reshape(-1, 3, 4); out = np.zeros_like(rest)
    for k in range(4):
        Mb = M[bi[:, k]]; out += (bw[:, k] / 255.0)[:, None] * (np.einsum('vij,vj->vi', Mb[:, :, :3], rest) + Mb[:, :, 3])
    return out

# ---- Etapa 47: bracos mais junto do corpo (a pose de repouso do Sims 3 e' um A bem aberto) ----
ADD_DEG = {0: 9.0, 1: 8.0, 3: 5.0, 4: 9.0, 5: 8.0, 6: 5.0}   # por indice de clipe (pulo = 2 nao muda)
def adduct_arms(clips, Q25):
    """Gira o braco inteiro (ombro->dedos) no plano frontal, em torno do ombro ja posado, em direcao ao corpo."""
    from etapa11_base import K as KK
    out = []
    for ci, (ln, res) in enumerate(clips):
        deg = ADD_DEG.get(ci, 0.0)
        if deg:
            a = np.radians(deg)
            for f in range(res.shape[0]):
                M = res[f].reshape(-1, 3, 4).astype(np.float64) / KK
                for side, sg in (('l', -1.0), ('r', 1.0)):
                    ua = BI['upperarm_' + side]; hd = BI['hand_' + side]
                    p = M[ua, :, :3] @ Q25[ua] + M[ua, :, 3]
                    th = sg * a; c, s = np.cos(th), np.sin(th)
                    Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
                    bones = [ua, ua + 1, hd] + (list(range(25, 40)) if side == 'l' else list(range(40, 55)))
                    for b in bones:
                        Rn = Rz @ M[b, :, :3]; tn = Rz @ (M[b, :, 3] - p) + p
                        M[b, :, :3] = Rn; M[b, :, 3] = tn
                res[f] = (M * KK).reshape(-1, 12).astype(np.float32)
        out.append((ln, res))
    return out
