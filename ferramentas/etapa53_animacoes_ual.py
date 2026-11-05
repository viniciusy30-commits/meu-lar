#!/usr/bin/env python3
"""Etapa 53: animacoes Parado / Andar / Correr da Universal Animation Library (Quaternius, CC0) nos corpos do Sims 3.

Uso: python3 etapa53_animacoes_ual.py <assets/cute> <UAL1_Standard.glb> [grupos...] [--out <pasta>] [--preview <pasta>]
     (sem grupos = tf tm af am ef em cu pu)

O que faz, por grupo (estagio+sexo):
  1. Recupera as juntas de repouso do corpo EXATAMENTE como a Etapa 49 as usou nos pesos de pele (fit_joints; o unico
     dado perdido, face_ymin, e' achado varrendo ate os pesos reconstruidos ficarem identicos aos de p_body_<g>1.bin).
  2. Para cada quadro da UAL calcula a pose mundial do esqueleto de origem e a adapta aos 55 ossos do app:
       - pelve, coluna, pescoco, cabeca, claviculas, pes e dedos do pe: rotacao relativa ao repouso (delta de mundo);
       - bracos, antebracos e maos: DIRECAO de cada osso copiada da UAL (a UAL repousa em T, o Sims 3 em A);
       - pernas: cinematica inversa de 2 ossos (tornozelo = tornozelo da UAL em relacao ao quadril, na escala da perna),
         joelho para o lado em que a UAL dobra o joelho. Resultado: o pe de apoio nao desliza;
       - dedos: flexao de cada falange medida na UAL e aplicada nas juntas dos dedos do Sims 3 (hand_model da Etapa 49).
  3. Grava clips_<g>.bin (CLP1, 55 ossos): 0 Parado (Idle_Loop), 1 Andar (Walk_Loop), 2 Pulo (pose do parado, sem animacao),
     3 Correr (Jog_Fwd_Loop). Sola do pe mais baixa de cada clipe = chao (y = 0).
"""
import sys, os, struct
_here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, _here)
_args = sys.argv[1:]
CU = _args[0].rstrip('/') + '/'
UAL = _args[1]
sys.argv = [sys.argv[0], CU]                 # etapa48/49 leem sys.argv[1] ao importar
import numpy as np
from scipy.spatial.transform import Rotation as Rot, Slerp
import etapa49_maos_idades as E49
from ual_glb import Rig
E = E49.E; R = E49.R
from etapa11_base import GP, K

BONES = R.BONES; BI = R.BI
GROUPS_ALL = ['tf', 'tm', 'af', 'am', 'ef', 'em', 'cu', 'pu']
# clipe -> (animacao da UAL, quadros por segundo gravados)
CLIPS = [('Idle_Loop', 30), ('Walk_Loop', 60), ('Jump_Combo', 60), ('Jog_Fwd_Loop', 60), ('RunJump', 60)]
IDLE, WALK, JUMP, RUN, RUNJUMP = 0, 1, 2, 3, 4
AIR = 0.71      # tempo no ar do pulo do app (2*3.9/11)

# --- ajustes finos ---------------------------------------------------------------------------------------------
FINGER_GAIN = 1.0            # multiplica a flexao dos dedos medida na UAL
THUMB_GAIN = 0.8
# Por clipe (0 parado, 1 andar, 3 correr). A UAL e' de jogo de acao (parado com pes alternados e cabeca baixa, corrida de velocista);
# o The Sims 3 e' mais calmo. Tudo abaixo suaviza so isso; com tudo em 1 / 0 o clipe sai igual ao da UAL.
#   sx, sz : escala do afastamento lateral / frente-tras do pe em relacao ao quadril (passada e largura da base)
#   sb     : escala do quique (altura do tornozelo acima do chao e queda da pelve)
#   pgain  : escala extra so da altura da pelve (joelhos mais esticados)
#   trunk  : graus de tronco endireitados (coluna, crescente de spine_01 ate o pescoco); head: graus a mais na cabeca
#   abd/sag: (centro em graus, ganho) da abertura lateral / balanco frente-tras do braco; centro None = mantem a media da UAL
#   rate   : velocidade de reproducao (embutida na duracao do clipe: 1.2 = 20% mais rapido)
PARAMS = {
    0: dict(sx=0.45, sz=0.30, sb=1.0, pgain=0.35, trunk=8.0, head=3.0, abd=(9.0, 0.6), sag=(-4.0, 1.0), rate=1.0),
    1: dict(sx=1.0, sz=1.0, sb=1.0, pgain=1.0, trunk=11.0, head=3.0, abd=(10.0, 0.7), sag=(-8.0, 1.15), rate=1.2),
    3: dict(sx=1.0, sz=0.5, sb=0.45, pgain=0.8, trunk=10.0, head=3.0, abd=(14.0, 0.5), sag=(-14.0, 0.5), rate=0.9, elb=0.55),
    2: dict(sx=1.0, sz=1.0, sb=0.55, pgain=0.6, trunk=0.0, head=0.0, abd=(18.0, 0.45), sag=(None, 0.8), rate=1.0),
}
# Etapa 63: parado, correr, pulo e pulo correndo vem dos FBX do Mixamo enviados pelo usuario (ferramentas/anim_fbx), sem ajuste de estilo
_ID = dict(sx=1.0, sz=1.0, sb=1.0, pgain=1.0, trunk=0.0, head=0.0, abd=(None, 1.0), sag=(None, 1.0), rate=1.0)
for _k in (0, 2, 3, 4): PARAMS[_k] = dict(_ID)

# ------------------------------------------------------------------------------------------------ utilidades 3D
def unit(v):
    n = np.linalg.norm(v); return v / n if n > 1e-12 else v

def arc_fix(D, dn, a):
    """gira D para que D@dn aponte para a (rotacao minima adicional)."""
    return R._arc(D @ dn, a) @ D

def interp_rot(Ra, Rb, t):
    r = Rot.from_matrix(np.stack([Ra, Rb]))
    return Slerp([0, 1], r)([t]).as_matrix()[0]

def smooth(x):
    x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)

def angle(a, b):
    return float(np.arccos(np.clip(unit(a) @ unit(b), -1, 1)))

# ------------------------------------------------------------------------------------------------ juntas do corpo
def read_ratios():
    ratios = {}
    for ln in open(CU + 'simbodies.txt'):
        if ln.startswith('#') or not ln.strip(): continue
        p = ln.strip().split('|'); ratios[p[0]] = float(p[4])
    return ratios

def full_weights(bi, bw):
    F = np.zeros((len(bi), 55))
    for k in range(4): np.add.at(F, (np.arange(len(bi)), bi[:, k].astype(int)), bw[:, k] / 255.0)
    return F

def rebuild_weights(P, T, clsv, fy, sc):
    J, cls = R.fit_joints(P, T, fy, None)
    bi, bw = R.skin_weights(P, T, J, clsv, fy - 0.003)
    bi, bw = E49.fix_clavicle(P, clsv, J, bi, bw)
    bi, bw = E49.smooth_armpit(P, T, J, bi, bw)
    hm = E49.hand_model(P, cls, J, sc)
    bi, bw = E49.apply_finger_weights(P, clsv, hm, bi, bw)
    return J, cls, hm, bi, bw

def recover_joints(grp, ratios):
    """juntas (metros) que geraram os pesos de p_body_<g>1.bin; varre face_ymin ate os pesos baterem."""
    v1, i1, fl1, tail1 = E.read_piece(CU + 'p_body_%s1.bin' % grp)
    sc = E.sc_of(ratios[grp + '1'])
    nb, T = E.body_part(v1, i1); P = v1['pos'][:nb].astype(np.float64) / sc
    bi0, bw0 = v1['bi'][:nb], v1['bw'][:nb]; F0 = full_weights(bi0, bw0)
    clsv = R.classify(P, T)
    head_full = (bi0[:, 0] == R.BI['head']) & (bw0[:, 0] == 255) & (P[:, 1] > 0.8 * P[:, 1].max())
    ytop = P[head_full, 1].min()
    best = None
    for fy in np.arange(ytop - 0.012, ytop + 0.004, 0.0005):
        J, cls, hm, bi, bw = rebuild_weights(P, T, clsv, fy, sc)
        d = np.abs(full_weights(bi, bw) - F0).sum(1)
        score = (d.mean(), (d > 0.02).mean())
        if best is None or score < best[0]: best = (score, fy, J, cls, hm)
        if score[0] < 1e-9: break
    (dm, dfrac), fy, J, cls, hm = best
    return dict(J=J, cls=cls, hm=hm, sc=sc, P=P, T=T, v=v1, nb=nb, fy=fy, wdiff=dm, wfrac=dfrac, ratio=ratios[grp + '1'])

# ------------------------------------------------------------------------------------------------ origem (UAL)
class Source:
    def __init__(self, path):
        self.rig = Rig(path); self.nm = self.rig.name_to_node
        Wr = self.rig.rest_world()
        self.Wr = Wr; self.Rr = {n: Wr[i][:3, :3] / np.linalg.norm(Wr[i][:3, 0]) for n, i in self.nm.items()}
        self.pr = {n: Wr[i][:3, 3].copy() for n, i in self.nm.items()}

    def pose(self, anim, t):
        r = self.rig; W = r.world(*r.local(anim, t))
        p = {}; D = {}
        for n, i in self.nm.items():
            p[n] = W[i][:3, 3].copy()
            Rw = W[i][:3, :3]; Rw = Rw / np.linalg.norm(Rw[:, 0])
            D[n] = Rw @ self.Rr[n].T
        return p, D

# Pulo: decolagem (Jump_Start) -> no ar (Jump_Loop) -> descida (Jump_Land) em JUMP_DUR s (= tempo no ar do app: 2*3.9/11), com mistura entre trechos
JUMP_DUR = 0.71
JUMP_SEGS = [('Jump_Start', 0.08, 0.40, 0.0, 0.28), ('Jump_Loop', 0.0, 0.22, 0.28, 0.50), ('Jump_Land', 0.0, 0.05, 0.50, JUMP_DUR)]   # anim, t0, t1 (origem), s0, s1 (destino)
class JumpRig:
    def duration(self, anim): return JUMP_DUR
class JumpSource:
    def __init__(self, src):
        self.s = src; self.rig = JumpRig(); self.pr = src.pr; self.Rr = src.Rr; self.nm = src.nm
    def _seg(self, i, t):
        a, t0, t1, s0, s1 = JUMP_SEGS[i]; u = (t - s0) / (s1 - s0); return self.s.pose(a, t0 + (t1 - t0) * min(max(u, 0.0), 1.0))
    def pose(self, anim, t):
        i = 0
        for k, sg in enumerate(JUMP_SEGS):
            if t >= sg[3]: i = k
        p, D = self._seg(i, t)
        ov = 0.07                                    # mistura com o proximo trecho perto do fim do atual
        if i + 1 < len(JUMP_SEGS) and t > JUMP_SEGS[i + 1][3] - ov:
            w = (t - (JUMP_SEGS[i + 1][3] - ov)) / ov; w = w * w * (3 - 2 * min(w, 1.0))
            p2, D2 = self._seg(i + 1, t)
            for n in p:
                p[n] = p[n] * (1 - w) + p2[n] * w
                D[n] = interp_rot(D[n], D2[n], w)
        return p, D

# ------------------------------------------------------------------------------------------------ um quadro
SPINE_SRC = ['pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck_01']

def rotx(deg):
    c, sn = np.cos(np.radians(deg)), np.sin(np.radians(deg)); return np.array([[1, 0, 0], [0, c, -sn], [0, sn, c]])
def rotz(deg):
    c, sn = np.cos(np.radians(deg)), np.sin(np.radians(deg)); return np.array([[c, -sn, 0], [sn, c, 0], [0, 0, 1]])
def sag_of(v): return np.degrees(np.arctan2(v[2], -v[1]))
def abd_of(v, sx): return np.degrees(np.arctan2(sx * v[0], -v[1]))

class Retarget:
    def __init__(self, src, body, par, anim, fps):
        self.par = par
        self.src = src; J = body['J']; self.J = J; self.hm = body['hm']
        self.Q = np.array([J[n] for n in BONES])
        Q = self.Q; pr = src.pr
        # escala da perna (comprimento total dos 2 ossos, alvo / origem)
        self.l1 = np.linalg.norm(Q[BI['calf_l']] - Q[BI['thigh_l']]); self.l2 = np.linalg.norm(Q[BI['foot_l']] - Q[BI['calf_l']])
        s1 = np.linalg.norm(pr['calf_l'] - pr['thigh_l']); s2 = np.linalg.norm(pr['foot_l'] - pr['calf_l'])
        self.k = (self.l1 + self.l2) / (s1 + s2)
        # alturas normalizadas da coluna (pelve=0 .. neck_01=1)
        y0 = pr['pelvis'][1]; y1 = pr['neck_01'][1]
        self.hs = [(pr[n][1] - y0) / (y1 - y0) for n in SPINE_SRC]
        self.ht = {i: (Q[i][1] - Q[0][1]) / (Q[BI['neck_01']][1] - Q[0][1]) for i in range(1, 6)}
        # deslocamento lateral/frontal do pe em relacao ao quadril no repouso (alvo - origem*k): mantem a largura do passo do Sims
        self.foot_off = {}
        for s in 'lr':
            a = Q[BI['foot_' + s]] - Q[BI['thigh_' + s]]; b = pr['foot_' + s] - pr['thigh_' + s]
            o = a - self.k * b; o[1] = 0.0; self.foot_off[s] = o
        self.pole_default = np.array([0.0, 0.0, 1.0])
        self.g_t = Q[BI['foot_l']][1]; self.g_s = pr['foot_l'][1]
        # media do braco na UAL (por lado) para recentrar balanco e abertura
        dur = src.rig.duration(anim); n = int(round(dur * 30)); sg = {'l': [], 'r': []}; ab = {'l': [], 'r': []}
        for f in range(n):
            p, _ = src.pose(anim, dur * f / n)
            for s_, sx in (('l', 1.0), ('r', -1.0)):
                v = p['lowerarm_' + s_] - p['upperarm_' + s_]; sg[s_].append(sag_of(v)); ab[s_].append(abd_of(v, sx))
        self.arm_mean = {s_: (float(np.mean(sg[s_])), float(np.mean(ab[s_]))) for s_ in 'lr'}

    def spine_rot(self, D, h):
        for j in range(len(SPINE_SRC) - 1):
            if h <= self.hs[j + 1] or j == len(SPINE_SRC) - 2:
                t = float(np.clip((h - self.hs[j]) / (self.hs[j + 1] - self.hs[j]), 0, 1))
                return interp_rot(D[SPINE_SRC[j]], D[SPINE_SRC[j + 1]], t)

    def frame(self, p, D, prest_pelvis):
        Q = self.Q; J = self.J; src = self.src; k = self.k
        Dn = np.tile(np.eye(3), (25, 1, 1)); pn = np.zeros((25, 3))
        Dn[0] = D['pelvis']
        for i in range(1, 6): Dn[i] = self.spine_rot(D, self.ht[i])
        Dn[6] = D['neck_01']; Dn[7] = interp_rot(D['neck_01'], D['Head'], 0.5); Dn[8] = D['Head']
        arm_dirs = {}
        for s in 'lr':
            Dn[BI['clavicle_' + s]] = D['clavicle_' + s]
            ua, la, hd = BI['upperarm_' + s], BI['lowerarm_' + s], BI['hand_' + s]
            a1 = unit(p['lowerarm_' + s] - p['upperarm_' + s]); a2 = unit(p['hand_' + s] - p['lowerarm_' + s]); a3 = unit(p['middle_01_' + s] - p['hand_' + s])
            sx_ = 1.0 if s == 'l' else -1.0; par = self.par
            msag, mabd = self.arm_mean[s]
            # balanco: gira o braco inteiro em torno do eixo x (sag' = sag - delta)
            csag, gsag = par['sag']; csag = msag if csag is None else csag
            sag = sag_of(a1); new = csag + gsag * (sag - msag); Rb = rotx(-(new - sag)); a1, a2, a3 = Rb @ a1, Rb @ a2, Rb @ a3
            # abertura: gira em torno de z (ab' = ab + sx*delta)
            cab, gab = par['abd']; cab = mabd if cab is None else cab
            ab = abd_of(a1, sx_); new = cab + gab * (ab - mabd); Rc = rotz(sx_ * (new - ab)); a1, a2, a3 = Rc @ a1, Rc @ a2, Rc @ a3
            e_ = par.get('elb', 1.0); a2 = unit(a1 + e_ * (a2 - a1)); a3 = unit(a2 + e_ * (a3 - a2))   # cotovelo menos dobrado
            dn1 = unit(Q[la] - Q[ua]); dn2 = unit(Q[hd] - Q[la]); dn3 = unit(J['_handtip_' + s] - J['hand_' + s])
            Dn[ua] = arc_fix(D['upperarm_' + s], dn1, a1)
            Dn[la] = arc_fix(D['lowerarm_' + s], dn2, a2)
            Dn[hd] = arc_fix(D['hand_' + s], dn3, a3)
            Dn[BI['foot_' + s]] = D['foot_' + s]; Dn[BI['ball_' + s]] = D['ball_' + s]
        tr, hd_ = self.par['trunk'], self.par['head']
        for i in range(1, 6): Dn[i] = rotx(-tr * (i / 5.0)) @ Dn[i]
        Dn[6] = rotx(-tr) @ Dn[6]; Dn[7] = rotx(-(tr + 0.5 * hd_)) @ Dn[7]; Dn[8] = rotx(-(tr + hd_)) @ Dn[8]
        for i in range(25):
            if i == 0:
                dl = p['pelvis'] - prest_pelvis; pn[0] = Q[0] + k * np.array([dl[0], dl[1] * self.par['sb'] * self.par['pgain'], dl[2]])
            else: pn[i] = pn[GP[i]] + Dn[GP[i]] @ (Q[i] - Q[GP[i]])
            for s in 'lr':
                if i == BI['thigh_' + s]:
                    th, ca, fo = BI['thigh_' + s], BI['calf_' + s], BI['foot_' + s]
                    H = pn[th]
                    rel = p['foot_' + s] - p['thigh_' + s]
                    A = H + k * np.array([rel[0] * self.par['sx'], 0.0, rel[2] * self.par['sz']]) + self.foot_off[s]
                    A[1] = self.g_t + self.par['sb'] * k * (p['foot_' + s][1] - self.g_s)     # altura absoluta do tornozelo: apoio sempre no chao
                    u = A - H; d = np.linalg.norm(u); u = u / d
                    d = float(np.clip(d, abs(self.l1 - self.l2) + 1e-4, (self.l1 + self.l2) * 0.9995)); A = H + u * d
                    # lado do joelho: o da origem (componente perpendicular ao eixo quadril-tornozelo)
                    ks = p['calf_' + s] - p['thigh_' + s]; ax = unit(p['foot_' + s] - p['thigh_' + s])
                    perp = ks - ax * (ks @ ax); m = np.linalg.norm(perp)
                    pd = self.pole_default - u * (self.pole_default @ u); pd = unit(pd)
                    w = float(smooth(m / 0.03))
                    pole = unit(w * (perp / max(m, 1e-9)) + (1 - w) * pd); pole = unit(pole - u * (pole @ u))
                    ca_ = np.clip((self.l1 ** 2 + d ** 2 - self.l2 ** 2) / (2 * self.l1 * d), -1, 1); sa_ = np.sqrt(1 - ca_ ** 2)
                    Kn = H + u * (self.l1 * ca_) + pole * (self.l1 * sa_)
                    Dn[th] = arc_fix(D['thigh_' + s], unit(Q[ca] - Q[th]), Kn - H)
                    Dn[ca] = arc_fix(D['calf_' + s], unit(Q[fo] - Q[ca]), A - Kn)
        return Dn, pn

    def finger_angles(self, p, side):
        """(5 dedos, 3 falanges): flexao (rad) em relacao ao repouso, medida na origem."""
        pr = self.src.pr; out = np.zeros((5, 3))
        names = ['index', 'middle', 'ring', 'pinky', 'thumb']
        for fi, nm in enumerate(names):
            ch = ['hand_' + side, '%s_01_%s' % (nm, side), '%s_02_%s' % (nm, side), '%s_03_%s' % (nm, side), '%s_04_leaf_%s' % (nm, side)]
            def dirs(pp): return [pp[ch[j + 1]] - pp[ch[j]] for j in range(4)]
            dp = dirs(p); dr = dirs(pr)
            for j in range(3):
                out[fi, j] = max(angle(dp[j], dp[j + 1]) - angle(dr[j], dr[j + 1]), 0.0)
        return out

# ------------------------------------------------------------------------------------------------ dedos
def finger_spec(hm, side):
    sg = 1.0 if side == 'l' else -1.0; S = np.array([sg, 1.0, 1.0])
    d = hm['d'] * S; n = hm['n'] * S; wax = hm['wax'] * S; items = []
    for k in range(4):
        fg = hm['fingers'][k]; items.append((E49.finger_bones(side, k), [q * S for q in fg['piv']], np.cross(d, n)))
    th = hm['thumb']; tdir = th['dir'] * S
    flex = n * 0.78 - wax * 0.40; flex /= np.linalg.norm(flex)
    items.append((E49.finger_bones(side, 4), [q * S for q in th['piv']], np.cross(tdir, flex)))
    return items

def apply_fingers(M, spec, ang, side):
    """M: (55,3,4) em metros; ossos dos dedos = osso da mao * cadeia de rotacoes em torno das juntas."""
    Mh = np.eye(4); Mh[:3, :4] = M[BI['hand_' + side]]
    for fi, (bones, piv, axis) in enumerate(spec):
        A = np.eye(4); g = THUMB_GAIN if fi == 4 else FINGER_GAIN
        for j in range(3):
            A = A @ E49.T4(piv[j], E49.rodrigues(axis, ang[fi, j] * g))
            M[bones[j]] = (Mh @ A)[:3, :4]

# ------------------------------------------------------------------------------------------------ clipe
def build_clip(src, rt, body, anim, fps, sole_ids, bi, bw, rest_m, min_arm_note=None):
    dur = src.rig.duration(anim); N = int(round(dur * fps))
    spec = {s: finger_spec(body['hm'], s) for s in 'lr'}
    frames = np.zeros((N + 1, 55, 3, 4)); sole_y = np.zeros(N + 1); info = {'ang': []}
    prest = src.pr['pelvis']
    for f in range(N + 1):
        t = dur * f / N
        p, D = src.pose(anim, t)
        Dn, pn = rt.frame(p, D, prest)
        M = np.zeros((55, 3, 4))
        for i in range(25): M[i, :, :3] = Dn[i]; M[i, :, 3] = pn[i] - Dn[i] @ rt.Q[i]
        for s in 'lr': apply_fingers(M, spec[s], rt.finger_angles(p, s), s)
        frames[f] = M
        # altura (m, espaco do OBJ) da sola posada
        y = np.zeros(len(sole_ids))
        for kk in range(4):
            bb = bi[sole_ids, kk]; ww = bw[sole_ids, kk] / 255.0
            y += ww * (np.einsum('vj,vj->v', M[bb][:, 1, :3], rest_m[sole_ids]) + M[bb][:, 1, 3])
        sole_y[f] = y.min()
    return dict(dur=dur, N=N, M=frames, sole_y=sole_y)

def loop_gap(cl):
    """diferenca maxima entre o primeiro e o ultimo quadro (deve ser ~0 num laço fechado)."""
    return float(np.abs(cl['M'][0] - cl['M'][-1]).max())

# ------------------------------------------------------------------------------------------------ por grupo
def run_group(src, grp, ratios, outdir):
    body = recover_joints(grp, ratios); sc = body['sc']; v = body['v']; nb = body['nb']
    typ = 3 if (grp + '3') in ratios else None
    print('[%s] pesos reconstruidos: diff media %.2e, vertices>0.02: %.4f (face_ymin=%.4f)' % (grp, body['wdiff'], body['wfrac'], body['fy']))
    assert body['wdiff'] < 0.01, 'juntas nao batem com os pesos salvos'
    bi = v['bi'].astype(int); bw = v['bw'].astype(float)
    rest_m = v['pos'].astype(np.float64) / sc
    # vertices da sola: so os do corpo (abaixo de 5% da altura)
    H = rest_m[:nb, 1].max(); sole_ids = np.nonzero(rest_m[:, 1] < 0.04 * H)[0]
    out = []; report = {}
    clips = {}
    for ci, c in enumerate(CLIPS):
        if c is None: continue
        anim, fps = c
        sx_ = MIX.get(ci, src)
        rt = Retarget(sx_, body, PARAMS[ci], anim, fps)
        cl = build_clip(sx_, rt, body, anim, fps, sole_ids, bi, bw, rest_m)
        clips[ci] = (cl, rt)
    # altura do chao: sola mais baixa de cada clipe = y 0 (o app so sobe, nunca desce)
    final = []
    for ci in range(len(CLIPS)):
        if False: pass
        else: cl = clips[ci][0]; M = cl['M'].copy(); low = cl['sole_y'].min(); dur = cl['dur'] / PARAMS[ci]['rate']
        M[:, :, 1, 3] -= low                  # translacao y de todos os ossos (espaco OBJ em metros)
        Mo = M.copy(); Mo[:, :, :, :3] *= K; Mo[:, :, :, 3] *= sc * K
        final.append((dur, Mo.reshape(len(M), 55, 12).astype(np.float32)))
        if True:
            report[ci] = dict(dur=dur, frames=len(M), gap=loop_gap(clips[ci][0]), lift_range=(clips[ci][0]['sole_y'].max() - low))
    E.write_clips(outdir + 'clips_%s.bin' % grp, final)
    return dict(body=body, clips=clips, report=report, final=final, sole_ids=sole_ids, K_sc=K * sc)

if __name__ == '__main__':
    rest_args = _args[2:]
    out = CU
    prev = None
    if '--out' in rest_args:
        i = rest_args.index('--out'); out = rest_args[i + 1].rstrip('/') + '/'; rest_args = rest_args[:i] + rest_args[i + 2:]
    if '--preview' in rest_args:
        i = rest_args.index('--preview'); prev = rest_args[i + 1]; rest_args = rest_args[:i] + rest_args[i + 2:]
    groups = [a for a in rest_args if not a.startswith('--')] or GROUPS_ALL
    os.makedirs(out, exist_ok=True)
    ratios = read_ratios(); src = Source(UAL)
    from mixamo_src import MixClip, air_window
    FB = os.path.join(_here, 'anim_fbx') + '/'
    MIX = {}
    MIX[IDLE] = MixClip(FB + 'Idle.fbx')
    MIX[RUN] = MixClip(FB + 'Running_1.fbx')
    for ci_, fn, pre, tail, base in ((JUMP, 'Jump_1.fbx', 0.14, 0.75, 1.034), (RUNJUMP, 'Running_Jump.fbx', 0.0, None, 0.859)):
        t_off, t_land, low_, tend = air_window(FB + fn)
        a_ = pre + AIR; segs = []
        if pre > 0: segs.append((0.0, pre, t_off - pre, t_off))
        segs.append((pre, a_, t_off, t_land))
        t_end = min(t_land + tail, tend) if tail else tend
        segs.append((a_, a_ + (t_end - t_land), t_land, t_end))
        MIX[ci_] = MixClip(FB + fn, segs=segs, lift_base=base)
        print('[mixamo] %s: decola %.3f, pousa %.3f, ar %.2f s -> %.2f s; clipe %.2f s' % (fn, t_off, t_land, t_land - t_off, AIR, MIX[ci_].period))
    for g in groups:
        r = run_group(src, g, ratios, out)
        print('   k perna %.3f -> corrida: pe de apoio ~ %.2f m/s no jogo' % (r['clips'][RUN][1].k, r['clips'][RUN][1].k * 3.3))
        for ci, rep in r['report'].items():
            print('   clipe %d: %.3f s, %d quadros, fecha laco (dif max %.4f), subida da sola no ciclo %.1f cm' % (ci, rep['dur'], rep['frames'], rep['gap'], rep['lift_range'] * 100))
