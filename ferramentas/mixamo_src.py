"""Fonte de animacao Mixamo (FBX) com a mesma interface da Source da UAL (etapa53). Acha sozinha 1 ciclo fechado da corrida."""
import numpy as np
from etapa11_fbxanim import Anim

def _map():
    m = {'pelvis': 'Hips', 'spine_01': 'Spine', 'spine_02': 'Spine1', 'spine_03': 'Spine2', 'neck_01': 'Neck', 'Head': 'Head'}
    for s, S in (('l', 'Left'), ('r', 'Right')):
        m.update({'clavicle_' + s: S + 'Shoulder', 'upperarm_' + s: S + 'Arm', 'lowerarm_' + s: S + 'ForeArm', 'hand_' + s: S + 'Hand',
                  'thigh_' + s: S + 'UpLeg', 'calf_' + s: S + 'Leg', 'foot_' + s: S + 'Foot', 'ball_' + s: S + 'ToeBase'})
        for nm, N in (('thumb', 'Thumb'), ('index', 'Index'), ('middle', 'Middle'), ('ring', 'Ring'), ('pinky', 'Pinky')):
            for k in (1, 2, 3): m['%s_0%d_%s' % (nm, k, s)] = '%sHand%s%d' % (S, N, k)
            m['%s_04_leaf_%s' % (nm, s)] = '%sHand%s4' % (S, N)
    return m
MAP = _map()

class _Rig:
    def __init__(self, owner): self.o = owner
    def duration(self, anim): return self.o.period

class MixSource:
    SC = 0.01
    def __init__(self, path, fps=60):
        self.a = Anim(path); a = self.a
        Wr = a.world(0, False)
        self.pr = {n: Wr[v][1] * self.SC for n, v in MAP.items()}
        self.Rr = {n: Wr[v][0] for n, v in MAP.items()}
        self.nm = {n: i for i, n in enumerate(MAP)}
        self.rig = _Rig(self)
        # ciclo: menor atraso em que a pose se repete
        T = np.arange(a.t0, a.t1 - 1e-6, 1.0 / fps)
        keys = ['Head', 'LeftHand', 'RightHand', 'LeftFoot', 'RightFoot', 'LeftLeg', 'RightLeg', 'LeftForeArm', 'RightForeArm']
        F = []
        for t in T:
            W = a.world(t); h = W['Hips'][1]
            F.append(np.concatenate([W[k][1] - np.array([h[0], 0, h[2]]) for k in keys]) * self.SC)
        F = np.array(F); n = len(F)
        # procura (inicio, periodo) em que a pose se repete melhor (captura real nao e' periodica: o resto fecha-se com mistura)
        self.ov = 0.3; io = int(self.ov * fps)
        best = None
        for L in range(int(0.8 * fps), int(1.4 * fps) + 1):
            for i in range(io, n - L):
                e = np.linalg.norm(F[i + L] - F[i]) + 0.5 * np.linalg.norm((F[i + L + 1] if i + L + 1 < n else F[i + L]) - F[i + 1] - (F[i + L] - F[i]))
                if best is None or e < best[0]: best = (e, i, L)
        e, i0, L = best
        self.t_start = T[i0]; self.period = L / fps
        print('[mixamo] ciclo %.3f s a partir de %.3f s (erro de fechamento %.4f m)' % (self.period, self.t_start, e))

    def _raw(self, t):
        W = self.a.world(t); p = {}; D = {}
        for n, v in MAP.items():
            Rw, P = W[v]; p[n] = P * self.SC; D[n] = Rw @ self.Rr[n].T
        return p, D

    def pose(self, anim, t):
        p, D = self._raw(self.t_start + t)
        w = (t - (self.period - self.ov)) / self.ov
        if w > 0:      # fim do ciclo: mistura com o trecho de antes do inicio, para o ultimo quadro = o primeiro
            w = min(w, 1.0); w = w * w * (3 - 2 * w)
            p2, D2 = self._raw(self.t_start + t - self.period)
            from scipy.spatial.transform import Rotation as Rot, Slerp
            for n in p:
                p[n] = p[n] * (1 - w) + p2[n] * w
                r = Rot.from_matrix(np.stack([D[n], D2[n]])); D[n] = Slerp([0, 1], r)([w]).as_matrix()[0]
        return p, D


class MixClip(MixSource):
    """Etapa 63: um clipe Mixamo (FBX) como esta, sem procurar ciclo.
    segs: lista de (u0, u1, s0, s1) -- tempo do clipe [u0,u1] <- tempo do FBX [s0,s1] (linear; permite esticar o trecho no ar).
    lift_base: se dado, a subida do quadril acima desta altura (m) e' retirada de todo o corpo (quem sobe e' o jogo, pela fisica do pulo)."""
    def __init__(self, path, segs=None, lift_base=None, fps=60, no_root=False):
        self.a = Anim(path); a = self.a
        Wr = a.world(0, False)
        self.pr = {n: Wr[v][1] * self.SC for n, v in MAP.items()}
        self.Rr = {n: Wr[v][0] for n, v in MAP.items()}
        self.nm = {n: i for i, n in enumerate(MAP)}
        self.rig = _Rig(self)
        self.segs = segs or [(0.0, a.t1 - a.t0, a.t0, a.t1)]
        self.period = self.segs[-1][1]
        self.lift_base = lift_base
        self.ov = 0.0
        # no_root: retira o deslocamento linear do quadril no plano (clipe que anda; quem anda e' o jogo)
        self.drift = None
        if no_root:
            h0 = a.world(a.t0)['Hips'][1] * self.SC; h1 = a.world(a.t1)['Hips'][1] * self.SC
            self.drift = (np.array([h1[0] - h0[0], 0.0, h1[2] - h0[2]]), a.t0, a.t1)

    def src_t(self, u):
        for (u0, u1, s0, s1) in self.segs:
            if u <= u1 or (u0, u1, s0, s1) == self.segs[-1]:
                return s0 + (s1 - s0) * min(max((u - u0) / (u1 - u0), 0.0), 1.0)

    def lift_at(self, s):
        if self.lift_base is None: return 0.0
        return max(0.0, self.a.world(s)['Hips'][1][1] * self.SC - self.lift_base)

    def pose(self, anim, u):
        s = self.src_t(u)
        p, D = self._raw(s)
        if self.drift is not None:
            d, t0, t1 = self.drift; off = d * ((s - t0) / (t1 - t0))
            p = {n: v - off for n, v in p.items()}
        lf = self.lift_at(s)
        if lf: p = {n: v - np.array([0.0, lf, 0.0]) for n, v in p.items()}
        return p, D


def air_window(path, thr=0.02, fps=240):
    """(decolagem, pouso) em s do FBX: primeiro/ultimo instante em que o pe mais baixo esta acima do chao + thr."""
    a = Anim(path); W0 = a.world(a.t0)
    g = min(W0['LeftFoot'][1][1], W0['RightFoot'][1][1]) * 0.01
    T = np.arange(a.t0, a.t1, 1.0 / fps); up = []
    for t in T:
        W = a.world(t); up.append(min(W['LeftFoot'][1][1], W['RightFoot'][1][1]) * 0.01 > g + thr + 0.0)
    up = np.array(up)
    # chao de referencia: o mais baixo do clipe
    low = min(min(a.world(t)['LeftFoot'][1][1], a.world(t)['RightFoot'][1][1]) for t in T[::8]) * 0.01
    up = np.array([min(a.world(t)['LeftFoot'][1][1], a.world(t)['RightFoot'][1][1]) * 0.01 > low + 0.03 for t in T])
    idx = np.nonzero(up)[0]
    return float(T[idx[0]]), float(T[idx[-1]]), float(low), float(a.t1)
