#!/usr/bin/env python3
"""Etapa 49: (1) maos naturais em TODAS as idades; (2) anatomia do Jovem (coluna, ombros, bracos) em TODAS as idades.

Problema 1 - maos esticadas: a malha da mao do Sims 3 e' uma "luva" inteira ligada so ao osso `hand`; os 30 ossos de dedos
(25..54) existiam no esqueleto mas NENHUM vertice tinha peso neles, e os clipes os faziam copiar o punho (mao rigida, dedos retos).
  -> aqui os vertices da mao ganham pesos nos ossos dos dedos (4 dedos + polegar, 3 falanges cada, mistura suave nas juntas)
  -> e os clipes dobram os dedos: mao relaxada (parado/andar/pulo) e punho frouxo (correr).

Problema 2 - idades diferentes do Jovem: so tf/tm tinham passado pela correcao de coluna/ombro/braco da etapa 48.
  -> o mesmo pipeline (etapa48_jovem) agora roda em tf tm af am ef em cu pu, com as mesmas regras (so muda o tamanho do corpo).

Uso: python3 etapa49_maos_idades.py <assets/cute> [grupos...] [--out <pasta>]
     (sem grupos = tf tm af am ef em cu pu)
"""
import sys, os
_here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, _here)
_args = [a for a in sys.argv[1:]]
CU = _args[0].rstrip('/') + '/'
sys.argv = [sys.argv[0], CU]          # etapa48_jovem le sys.argv[1] ao importar
import numpy as np
import etapa48_jovem as E
import etapa45_rig as R
from etapa11_base import K as KK

GROUPS_ALL = ['tf', 'tm', 'af', 'am', 'ef', 'em', 'cu', 'pu']
RUN_CLIPS = {3, 6}                  # indices dos clipes de correr (0 parado, 1 andar, 2 pulo, 3 correr, 4/5/6 versoes masculinas)

# ------------------------------------------------------------------ curvatura dos dedos (graus por falange: proximal, media, distal)
# ordem: indicador, medio, anelar, minimo, polegar
CURL_RELAX = [(16, 24, 12), (20, 29, 14), (24, 33, 16), (28, 37, 18), (6, 12, 9)]
CURL_RUN = [(38, 58, 28), (43, 63, 32), (48, 67, 34), (52, 72, 38), (14, 24, 14)]

def smooth(x):
    x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)

def finger_bones(side, f):
    base = 25 if side == 'l' else 40
    return [base + 3 * f + k for k in range(3)]

def kmeans1d(x, k, it=30):
    c = np.quantile(x, (np.arange(k) + 0.5) / k)
    for _ in range(it):
        a = np.abs(x[:, None] - c[None]).argmin(1)
        nc = np.array([x[a == i].mean() if (a == i).any() else c[i] for i in range(k)])
        if np.allclose(nc, c): break
        c = nc
    return np.sort(c)

# ------------------------------------------------------------------ modelo geometrico da mao (lado esquerdo; o direito e' o espelho em x)
def hand_model(P, cls, J, sc):
    A = P[cls == 'armL']
    h = J['hand_l'].copy(); tip = J['_handtip_l'].copy()
    L = float(np.linalg.norm(tip - h)); d = (tip - h) / L
    n = np.array([-d[1], d[0], 0.0]); n /= np.linalg.norm(n)
    if n[0] > 0: n = -n                      # n: lado da palma (para o corpo)
    z = np.array([0.0, 0.0, 1.0])
    s0 = (A - h) @ d
    H = A[s0 > 0.0]
    wv = (H - h) @ z
    wsign = 1.0 if abs(wv.max()) > abs(wv.min()) else -1.0     # lado do polegar
    wax = z * wsign
    u = (H - h) @ d; w = (H - h) @ wax; nn = (H - h) @ n
    # polegar: muito para o lado e na parte de baixo (proximal) da mao
    thumb_m = (w > 0.34 * L) & (u < 0.62 * L)
    # dedos: colunas na metade distal
    fm = (u > 0.68 * L) & (w < 0.34 * L + 0.02 * L)
    wc = kmeans1d(w[fm], 4)[::-1]            # indicador (mais perto do polegar) -> minimo
    sp = float(np.mean(np.abs(np.diff(wc))))
    lat = np.abs(w[:, None] - wc[None]); col = lat.argmin(1)
    u_mcp = 0.50 * L
    fingers = []
    for k in range(4):
        sel = fm & (col == k)
        umax = float(np.percentile(u[sel], 99.5)) if sel.sum() > 3 else L
        nc = float(nn[sel].mean()) if sel.sum() > 3 else float(nn.mean())
        Lf = max(umax - u_mcp, 0.2 * L)
        ju = [u_mcp, u_mcp + 0.43 * Lf, u_mcp + 0.75 * Lf]
        piv = [h + d * x + wax * wc[k] + n * nc for x in ju]
        fingers.append(dict(wc=wc[k], ju=ju, piv=piv, tip=umax))
    # polegar
    T = thumb_m & (w > 0.40 * L)
    B = np.array([0.36 * L, 0.12 * L])       # (w, u) da base
    TT = np.stack([w[T], u[T]], 1)
    tipi = np.argmax(np.linalg.norm(TT - B, axis=1)); tp = TT[tipi]
    ax2 = (tp - B); Lt = float(np.linalg.norm(ax2)); ax2 /= Lt
    nth = float(nn[T].mean())
    tj = [0.0, 0.42, 0.72]
    tpiv = [h + wax * (B[0] + ax2[0] * Lt * t) + d * (B[1] + ax2[1] * Lt * t) + n * nth for t in tj]
    tdir = wax * ax2[0] + d * ax2[1]; tdir /= np.linalg.norm(tdir)
    thumb = dict(B=B, ax2=ax2, Lt=Lt, tj=tj, piv=tpiv, dir=tdir)
    return dict(h=h, d=d, n=n, wax=wax, L=L, wc=wc, sp=sp, u_mcp=u_mcp, fingers=fingers, thumb=thumb, sc=sc)

# ------------------------------------------------------------------ pesos de pele dos dedos
def apply_finger_weights(Pv, clsv, hm, bi, bw):
    """redistribui o peso do osso `hand` das duas maos entre os ossos dos dedos. Pv em metros; bi/bw (n,4) uint8; devolve novos."""
    n = len(Pv); L = hm['L']; dl = 0.06 * L
    NEW_I = np.zeros((n, 4), np.uint8); NEW_W = np.zeros((n, 4), np.uint8)
    full = np.zeros((n, 55)); idx = np.arange(n)
    for k in range(4):
        np.add.at(full, (idx, bi[:, k].astype(int)), bw[:, k] / 255.0)
    for side in ('l', 'r'):
        sg = 1.0 if side == 'l' else -1.0
        Pm = Pv * np.array([sg, 1.0, 1.0])
        label = 'armL' if side == 'l' else 'armR'
        sel = np.nonzero((clsv == label))[0]
        if len(sel) == 0: continue
        X = Pm[sel] - hm['h']
        u = X @ hm['d']; w = X @ hm['wax']
        sel2 = u > -0.02 * L
        sel = sel[sel2]; u = u[sel2]; w = w[sel2]
        hb = R.BI['hand_' + side]
        wh = full[sel, hb].copy()                       # peso atual do osso mao = quantidade a redistribuir
        # -- polegar
        th = hm['thumb']
        tau = ((w - th['B'][0]) * th['ax2'][0] + (u - th['B'][1]) * th['ax2'][1]) / th['Lt']
        tf = smooth((w - 0.34 * hm['L']) / (0.07 * hm['L'])) * (u < 0.66 * L)
        dt = 0.10
        St = [smooth((tau - tj + dt) / (2 * dt)) for tj in th['tj']]
        cth = [1 - St[0], St[0] - St[1], St[1] - St[2], St[2]]
        # -- dedos
        wc = hm['wc']; sp = hm['sp']
        lat = np.exp(-((w[:, None] - wc[None]) / (0.55 * sp)) ** 2)       # (m,4)
        lat /= lat.sum(1, keepdims=True) + 1e-12
        # so os 2 dedos mais proximos
        for i in range(len(lat)):
            o = np.argsort(-lat[i]); lat[i, o[2:]] = 0
        lat /= lat.sum(1, keepdims=True) + 1e-12
        Sj = [smooth((u - j + dl) / (2 * dl)) for j in hm['fingers'][0]['ju']]
        chand = 1 - Sj[0]; c1 = Sj[0] - Sj[1]; c2 = Sj[1] - Sj[2]; c3 = Sj[2]
        # -- combina: fracao do peso da mao que vai para cada osso
        frac = np.zeros((len(sel), 55))
        frac[:, hb] = (1 - tf) * chand + tf * cth[0]
        for k in range(4):
            b = finger_bones(side, k)
            for j, cj in enumerate((c1, c2, c3)):
                frac[:, b[j]] += (1 - tf) * lat[:, k] * cj
        tb = finger_bones(side, 4)
        for j in range(3): frac[:, tb[j]] += tf * cth[j + 1]
        full[sel, hb] = 0.0
        full[sel] += frac * wh[:, None]
    # 4 maiores influencias
    ii = np.argsort(-full, 1)[:, :4]; vv = np.take_along_axis(full, ii, 1)
    vv = np.where(vv < 0.015, 0, vv); vv /= vv.sum(1, keepdims=True)
    q = np.round(vv * 255).astype(int); q[:, 0] += 255 - q.sum(1)
    return ii.astype(np.uint8), q.astype(np.uint8)

# ------------------------------------------------------------------ clipes: dobra os dedos
def rodrigues(ax, th):
    ax = ax / np.linalg.norm(ax); c, s = np.cos(th), np.sin(th)
    X = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) * c + s * X + (1 - c) * np.outer(ax, ax)

def T4(q, Rm):
    """transformacao 4x4 que gira Rm em torno do ponto q"""
    M = np.eye(4); M[:3, :3] = Rm; M[:3, 3] = q - Rm @ q; return M

def curl_hands(clips, hm):
    """para cada clipe/quadro: osso do dedo = osso da mao * (cadeia de rotacoes das falanges em torno das juntas)"""
    sc = hm['sc']; out = []
    # eixos e juntas (unid. de armazenamento) por lado
    spec = {}
    for side in ('l', 'r'):
        sg = 1.0 if side == 'l' else -1.0
        S = np.array([sg, 1.0, 1.0])
        d = hm['d'] * S; n = hm['n'] * S; wax = hm['wax'] * S
        items = []
        for k in range(4):
            fg = hm['fingers'][k]
            items.append((finger_bones(side, k), [p * S * sc for p in fg['piv']], np.cross(d, n)))
        th = hm['thumb']; tdir = th['dir'] * S
        flex = n * 0.78 - wax * 0.40; flex /= np.linalg.norm(flex)       # polegar fecha em direcao a palma / ao indicador
        items.append((finger_bones(side, 4), [p * S * sc for p in th['piv']], np.cross(tdir, flex)))
        spec[side] = items
    for ci, (ln, res) in enumerate(clips):
        res = res.copy(); curl = CURL_RUN if ci in RUN_CLIPS else CURL_RELAX
        for f in range(res.shape[0]):
            M = res[f].reshape(-1, 3, 4).astype(np.float64) / KK
            for side in ('l', 'r'):
                Mh = np.eye(4); Mh[:3, :4] = M[R.BI['hand_' + side]]
                for fi, (bones, piv, axis) in enumerate(spec[side]):
                    A = np.eye(4)
                    for j in range(3):
                        A = A @ T4(piv[j], rodrigues(axis, np.radians(curl[fi][j])))
                        M[bones[j]] = (Mh @ A)[:3, :4]
            res[f] = (M * KK).reshape(-1, 12).astype(np.float32)
        out.append((ln, res))
    return out


# ------------------------------------------------------------------ clavicula so no topo do ombro
def fix_clavicle(Pv, clsv, J, bi, bw):
    """A difusao do Etapa 45 prende a lateral inteira do tronco (ate 14 cm abaixo do ombro) na clavicula (~50% do peso);
    quando o ombro se mexe a costela lateral vira uma "aba" esticada na axila. Aqui a clavicula so influencia o topo do ombro:
    abaixo dele o peso vai para a coluna (tronco) ou para o braco (ilha do braco)."""
    n = len(Pv); uu = J['_H'] / 1.675
    full = np.zeros((n, 55)); idx = np.arange(n)
    for k in range(4): np.add.at(full, (idx, bi[:, k].astype(int)), bw[:, k] / 255.0)
    ycut = J['upperarm_l'][1] - 0.02 * uu
    fac = smooth((Pv[:, 1] - (ycut - 0.05 * uu)) / (0.05 * uu))        # 1 acima de ycut, 0 abaixo de ycut-5cm
    for side in ('l', 'r'):
        cb = R.BI['clavicle_' + side]; ub = R.BI['upperarm_' + side]
        wc = full[:, cb] * (1 - fac); full[:, cb] -= wc
        arm = clsv == ('armL' if side == 'l' else 'armR')
        full[arm, ub] += wc[arm]
        t = ~arm; sp = full[:, 1:6]
        has = sp.sum(1) > 1e-6
        tgt = np.where(has, 1 + sp.argmax(1), 4)
        full[np.nonzero(t)[0], tgt[t]] += wc[t]
    ii = np.argsort(-full, 1)[:, :4]; vv = np.take_along_axis(full, ii, 1)
    vv = np.where(vv < 0.02, 0, vv); vv /= vv.sum(1, keepdims=True)
    q = np.round(vv * 255).astype(int); q[:, 0] += 255 - q.sum(1)
    return ii.astype(np.uint8), q.astype(np.uint8)

# ------------------------------------------------------------------ axila: pesos suavizados (sem "prateleira" entre braco e tronco)
from scipy.sparse import coo_matrix, diags as _diags
def smooth_armpit(Pv, Tv, J, bi, bw, iters=28, lam=0.6, rad=0.135):
    """Os pesos do Sims mudam de repente na costura braco/tronco (axila): ao girar o braco, a pele do tronco vira uma aba esticada.
    Aqui os pesos (25 ossos) sao suavizados por difusao na malha soldada, so numa esfera em volta de cada axila."""
    n = len(Pv); uu = J['_H'] / 1.675
    key = np.round(Pv * 1e5).astype(np.int64); uq, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1)
    m = len(uq); Q = Pv[first]
    full = np.zeros((n, 55)); idx = np.arange(n)
    for k in range(4): np.add.at(full, (idx, bi[:, k].astype(int)), bw[:, k] / 255.0)
    Wu = np.zeros((m, 55)); Wu[inv] = full
    a = inv[np.r_[Tv[:, 0], Tv[:, 1], Tv[:, 2]]]; b = inv[np.r_[Tv[:, 1], Tv[:, 2], Tv[:, 0]]]; ok = a != b
    Adj = coo_matrix((np.ones(ok.sum() * 2), (np.r_[a[ok], b[ok]], np.r_[b[ok], a[ok]])), shape=(m, m)).tocsr(); Adj.data[:] = 1.0
    deg = np.asarray(Adj.sum(1)).ravel() + 1e-9
    mask = np.zeros(m)
    for sg in (1.0, -1.0):
        S = J['upperarm_l'] * np.array([sg, 1, 1]); C = S + np.array([-0.04 * sg, -0.11, 0.0]) * uu
        d = np.linalg.norm(Q - C, axis=1) / (rad * uu); mask = np.maximum(mask, smooth(1.0 - d))
    mask[Q[:, 1] > J['upperarm_l'][1] + 0.05 * uu] = 0       # nada acima do ombro (pescoco/cabeca)
    lm = (lam * mask)[:, None]
    for _ in range(iters): Wu = Wu + lm * ((Adj @ Wu) / deg[:, None] - Wu)
    full = Wu[inv]
    ii = np.argsort(-full, 1)[:, :4]; vv = np.take_along_axis(full, ii, 1)
    vv = np.where(vv < 0.02, 0, vv); vv /= vv.sum(1, keepdims=True)
    q = np.round(vv * 255).astype(int); q[:, 0] += 255 - q.sum(1)
    return ii.astype(np.uint8), q.astype(np.uint8)

# ------------------------------------------------------------------ bracos "The Sims": balanco e abertura mais contidos
# (centro_atual, escala, novo_centro) em graus. Frente/tras: 0 = braco na vertical, negativo = para tras.
SWING = {1: (-16.0, 0.85, -14.0), 5: (-16.0, 0.85, -14.0), 3: (-12.0, 0.70, -6.0), 6: (-12.0, 0.70, -6.0)}
ABD = {1: (6.0, 0.55, 6.0), 5: (6.0, 0.55, 6.0)}              # abertura lateral: balanco do andar mais contido
ELBOW2 = dict(E.ELBOW); ELBOW2.update({3: (20.0, 0.88), 6: (20.0, 0.88)})   # correr: cotovelo ~92-105 graus (antes 103-117)

def natural_arms(clips, Q25):
    out = []
    for ci, (ln, res) in enumerate(clips):
        res = res.copy()
        if ci in SWING or ci in ABD:
            for f in range(res.shape[0]):
                M = res[f].reshape(-1, 3, 4).astype(np.float64) / KK
                for side in ('l', 'r'):
                    ua, la = R.BI['upperarm_' + side], R.BI['lowerarm_' + side]; hd = R.BI['hand_' + side]
                    bones = [ua, la, hd] + (list(range(25, 40)) if side == 'l' else list(range(40, 55)))
                    sx = 1.0 if side == 'l' else -1.0
                    def rot(Rm, p):
                        for b in bones:
                            M[b, :, :3] = Rm @ M[b, :, :3]; M[b, :, 3] = Rm @ (M[b, :, 3] - p) + p
                    def arm():
                        s_ = M[ua, :, :3] @ Q25[ua] + M[ua, :, 3]; e_ = M[la, :, :3] @ Q25[la] + M[la, :, 3]; return s_, e_ - s_
                    if ci in SWING:
                        c, k, c2 = SWING[ci]; p, v = arm(); sag = np.degrees(np.arctan2(v[2], -v[1])); d = (c2 + k * (sag - c)) - sag
                        th = -np.radians(d); cs, sn = np.cos(th), np.sin(th)
                        rot(np.array([[1, 0, 0], [0, cs, -sn], [0, sn, cs]]), p)
                    if ci in ABD:
                        c, k, c2 = ABD[ci]; p, v = arm(); ab = np.degrees(np.arctan2(sx * v[0], -v[1])); d = (c2 + k * (ab - c)) - ab
                        th = sx * np.radians(d); cs, sn = np.cos(th), np.sin(th)
                        rot(np.array([[cs, -sn, 0], [sn, cs, 0], [0, 0, 1]]), p)
                res[f] = (M * KK).reshape(-1, 12).astype(np.float32)
        out.append((ln, res))
    return out


# ------------------------------------------------------------------ cabeca/pescoco na corrida: olhar para a frente
# O clipe antigo inclina o tronco ~16 graus e o pescoco acompanha (12-21), mas joga a cabeca 10-21 graus para TRAS:
# o boneco olha para cima e o pescoco parece enorme/quebrado. Angulos "para cima" absolutos (graus, + = para frente), por clipe:
# (alvo medio, fracao do balanco original mantida) para neck_01, neck_02, head
HEAD = {3: ((8.0, 0.4), (4.0, 0.4), (-1.0, 0.3)), 6: ((8.0, 0.4), (4.0, 0.4), (-1.0, 0.3))}
def fix_head(clips, Q25):
    out = []
    for ci, (ln, res) in enumerate(clips):
        res = res.copy()
        if ci in HEAD:
            bones = [R.BI['neck_01'], R.BI['neck_02'], R.BI['head']]
            def upang(M, b): return np.degrees(np.arctan2(M[b, 2, 1], M[b, 1, 1]))
            Ms = [res[f].reshape(-1, 3, 4).astype(np.float64) / KK for f in range(res.shape[0])]
            means = [np.mean([upang(M, b) for M in Ms]) for b in bones]
            for f, M in enumerate(Ms):
                for j, b in enumerate(bones):
                    tgt, keep = HEAD[ci][j]; cur = upang(M, b)
                    d = np.radians((tgt + keep * (cur - means[j])) - cur); cs, sn = np.cos(d), np.sin(d)
                    Rx = np.array([[1, 0, 0], [0, cs, -sn], [0, sn, cs]])
                    p = M[b, :, :3] @ Q25[b] + M[b, :, 3]
                    for q in bones[j:]:
                        M[q, :, :3] = Rx @ M[q, :, :3]; M[q, :, 3] = Rx @ (M[q, :, 3] - p) + p
                res[f] = (M * KK).reshape(-1, 12).astype(np.float32)
        out.append((ln, res))
    return out

# ------------------------------------------------------------------ pipeline por grupo (etapa48 + dedos)
def run(grp, ratios, outdir):
    v1, i1, fl1, tail1 = E.read_piece(CU + 'p_body_%s1.bin' % grp)
    old = E.read_clips(CU + 'clips_%s.bin' % grp); Qold = E.recover_Q(old)
    sc = E.sc_of(ratios[grp + '1']); u = ratios[grp + '1']
    nb, T = E.body_part(v1, i1); P = v1['pos'][:nb].astype(np.float64) / sc
    face_ymin = Qold[R.BI['head']][1] / sc - 0.07 * u
    J, cls = R.fit_joints(P, T, face_ymin, None)
    Qnew = np.array([J[nm] for nm in R.BONES]) * sc
    hm = hand_model(P, cls, J, sc)
    for typ in (0, 1, 3):
        fn = CU + 'p_body_%s%d.bin' % (grp, typ)
        if not os.path.exists(fn): continue
        v, idx, fl, tail = E.read_piece(fn); nbv, Tv = E.body_part(v, idx)
        Pv = v['pos'][:nbv].astype(np.float64) / sc
        clsv = R.classify(Pv, Tv)
        bi, bw = R.skin_weights(Pv, Tv, J, clsv, face_ymin - 0.003)
        bi, bw = fix_clavicle(Pv, clsv, J, bi, bw)
        bi, bw = smooth_armpit(Pv, Tv, J, bi, bw)
        bi, bw = apply_finger_weights(Pv, clsv, hm, bi, bw)
        v['bi'][:nbv] = bi; v['bw'][:nbv] = bw
        E.write_piece(outdir + os.path.basename(fn), v, idx, fl, tail)
    rest = v1['pos'][:nb].astype(np.float64); sole = np.nonzero(rest[:, 1] < 0.05 * rest[:, 1].max())[0]
    v1n, _, _, _ = E.read_piece(outdir + 'p_body_%s1.bin' % grp)
    cl = R.retarget_clips(Qnew, v1n['bi'][:nb], v1n['bw'][:nb], rest, sole)
    cl = E.align_hands(cl, Qnew)
    ab = E.abduction(cl, Qnew)
    degs = {ci: ab[ci] - E.TARGET_DEG[ci] for ci in E.TARGET_DEG if ci < len(cl)}
    cl = E.adduct(cl, Qnew, degs)
    cl = natural_arms(cl, Qnew)
    cl = fix_head(cl, Qnew)
    cl = E.relax_elbows(cl, Qnew, ELBOW2)
    cl = curl_hands(cl, hm)
    E.write_clips(outdir + 'clips_%s.bin' % grp, cl)
    print(grp, 'ok | mao L=%.1f cm, dedos(w)=%s' % (hm['L'] * 100, np.round(hm['wc'] * 100, 1)))
    return Qnew, hm

if __name__ == '__main__':
    rest_args = _args[1:]
    out = CU
    if '--out' in rest_args:
        i = rest_args.index('--out'); out = rest_args[i + 1].rstrip('/') + '/'; rest_args = rest_args[:i] + rest_args[i + 2:]
    groups = [a for a in rest_args if not a.startswith('--')] or GROUPS_ALL
    os.makedirs(out, exist_ok=True)
    ratios = {}
    for ln in open(CU + 'simbodies.txt'):
        if ln.startswith('#') or not ln.strip(): continue
        p = ln.strip().split('|'); ratios[p[0]] = float(p[4])
    for g in groups: run(g, ratios, out)
