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
