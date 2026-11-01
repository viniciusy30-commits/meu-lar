"""Etapa 11 - troca os clipes de ANDAR e CORRER pelas animações do Mixamo enviadas (Walking.fbx / Slow_Run.fbx).

Uso:  python3 etapa11_retarget.py <base.bin entrada> <Walking.fbx> <Slow_Run.fbx> <base.bin saída>

Como funciona (retargeting do esqueleto Mixamo, 65 ossos, T-pose  ->  esqueleto do jogo, 55 ossos, A-pose):
 - A pose de referência do esqueleto do jogo é recuperada dos próprios clips do base.bin (elo rígido pai-filho).
 - Cada osso recebe uma rotação MUNDIAL relativa à pose de referência (D). A matriz de pele é  S = K*[D | p(t) - D*p_ref].
 - Pelve, coluna, pescoço, cabeça e clavículas: D = rotação mundial do osso do Mixamo relativa à T-pose dele.
 - Pernas e braços (coxa, canela, pé, braço, antebraço): iguala-se a DIREÇÃO do osso no mundo (resolve T-pose x A-pose).
 - Mão e dedão do pé: rotação relativa ao osso pai, transferida do Mixamo. Dedos da mão ficam relaxados como no Idle.
 - Raiz: o deslocamento para frente é removido (o jogo move o personagem); mantém quique e balanço lateral.
 - Trava de chão: sobe/desce tudo para o ponto mais baixo do pé tocar y=0.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from etapa11_fbxanim import Anim
from etapa11_base import *

IDLE, WALK, JUMP, RUN = 0, 1, 2, 3
SUB = 2   # quadros por quadro do Mixamo (30 fps -> 60 fps; o jogo interpola linearmente entre quadros)


# ---------------- álgebra ----------------
def arc(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    c = float(a @ b)
    if c < -0.9999:
        ax = np.cross(a, [1, 0, 0])
        if np.linalg.norm(ax) < 1e-3: ax = np.cross(a, [0, 0, 1])
        ax /= np.linalg.norm(ax)
        return 2 * np.outer(ax, ax) - np.eye(3)
    v = np.cross(a, b)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)

def to_quat(R):
    t = np.trace(R)
    if t > 0:
        s = np.sqrt(t + 1) * 2; q = [0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s]
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1 + R[0, 0] - R[1, 1] - R[2, 2]) * 2; q = [(R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s]
    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1 + R[1, 1] - R[0, 0] - R[2, 2]) * 2; q = [(R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s]
    else:
        s = np.sqrt(1 + R[2, 2] - R[0, 0] - R[1, 1]) * 2; q = [(R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s]
    q = np.array(q); return q / np.linalg.norm(q)

def from_quat(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])

def slerp(Ra, Rb, u):
    qa, qb = to_quat(Ra), to_quat(Rb)
    if qa @ qb < 0: qb = -qb
    d = min(1.0, qa @ qb)
    th = np.arccos(d)
    if th < 1e-6: return Ra.copy()
    q = (np.sin((1 - u) * th) * qa + np.sin(u * th) * qb) / np.sin(th)
    return from_quat(q / np.linalg.norm(q))

def ortho(R):
    u, s, vt = np.linalg.svd(R); return u @ vt


# ---------------- mapeamento de ossos ----------------
SRC_SIDE = {'l': 'Left', 'r': 'Right'}
# osso do jogo -> filho "principal" (direção) e nome do osso do Mixamo + filho do Mixamo
def dir_bones():
    out = {}
    for sd, S in (('l', 'Left'), ('r', 'Right')):
        o = 0 if sd == 'l' else 4
        out[10 + o] = (11 + o, S + 'Arm', S + 'ForeArm')
        out[11 + o] = (12 + o, S + 'ForeArm', S + 'Hand')
        out[17 + o] = (18 + o, S + 'UpLeg', S + 'Leg')
        out[18 + o] = (19 + o, S + 'Leg', S + 'Foot')
        out[19 + o] = (20 + o, S + 'Foot', S + 'ToeBase')
    return out
DIR = dir_bones()


class Retarget:
    def __init__(self, base_path):
        self.base = read_base(base_path)
        P = recover_bind(self.base['clips'], self.base['ver'])
        P[20][0] = P[19][0]; P[24][0] = P[23][0]       # x da bola do pé é indeterminado: fica em frente ao tornozelo
        self.P = P
        idle = self.base['clips'][IDLE][1][0].astype(np.float64)    # (55,12)
        self.Didle = [ortho(idle[i].reshape(3, 4)[:, :3] / K) for i in range(NB)]
        ver = self.base['ver']
        dom = ver['bi'][np.arange(self.base['nv']), ver['bw'].argmax(1)]
        self.foot_v = np.where(np.isin(dom, [19, 20, 23, 24]))[0]
        # só o pé "de verdade": vértices cujo y de referência está abaixo de 14 (sola)
        self.foot_v = self.foot_v[ver['pos'][self.foot_v, 1] < 14.0]

    # ---- uma pose ----
    def pose(self, A, t, Wb, s_leg, drift, T, cmean):
        P = self.P
        W = A.world(t)
        # delta mundial da fonte (relativo à T-pose do Mixamo)
        def Ds(n): return W[n][0] @ Wb[n][0].T
        D = [None] * NB
        D[0] = Ds('Hips')
        sp = [Ds('Spine'), Ds('Spine1'), Ds('Spine2')]
        D[1] = sp[0]; D[2] = slerp(sp[0], sp[1], 0.5); D[3] = sp[1]; D[4] = slerp(sp[1], sp[2], 0.5); D[5] = sp[2]
        dn, dh = Ds('Neck'), Ds('Head')
        D[6] = dn; D[7] = slerp(dn, dh, 0.5); D[8] = dh
        D[9] = Ds('LeftShoulder'); D[13] = Ds('RightShoulder')
        # ossos por direção
        for i, (c, nm, ch) in DIR.items():
            db = P[c] - P[i]
            ds = W[ch][1] - W[nm][1]
            D[i] = arc(db, ds)
        # mãos e dedão do pé: rotação relativa transferida
        for sd, S in (('l', 'Left'), ('r', 'Right')):
            o = 0 if sd == 'l' else 4
            # mão: relativa ao antebraço
            rel = Ds(S + 'ForeArm').T @ Ds(S + 'Hand')
            A_ = arc(Wb[S + 'Hand'][1] - Wb[S + 'ForeArm'][1], P[12 + o] - P[11 + o])
            D[12 + o] = D[11 + o] @ (A_ @ rel @ A_.T)
            # ponta do pé (ball): relativa ao pé
            rel = Ds(S + 'Foot').T @ Ds(S + 'ToeBase')
            A_ = arc(Wb[S + 'ToeBase'][1] - Wb[S + 'Foot'][1], P[20 + o] - P[19 + o])
            D[20 + o] = D[19 + o] @ (A_ @ rel @ A_.T)
        # dedos da mão: relaxados como no Idle, seguindo a mão
        for i in range(25, NB):
            h = 12 if i < 40 else 16
            D[i] = D[h] @ (self.Didle[h].T @ self.Didle[i])
        # posição da pelve: ponto médio das coxas da fonte (rígido na pelve), em escala, sem o deslocamento para frente
        c = (W['LeftUpLeg'][1] + W['RightUpLeg'][1]) / 2
        cx = c.copy(); cx[0] -= cmean[0]; cx[2] -= cmean[2]
        cx -= drift * (t / T)                         # tira o deslocamento linear (só x e z, drift[1]=0)
        p0 = np.array([cx[0] * s_leg, c[1] * s_leg, cx[2] * s_leg])
        # FK no esqueleto do jogo
        pos = [None] * NB
        for i in range(NB):
            q = GP[i]
            pos[i] = p0 if q < 0 else pos[q] + D[q] @ (P[i] - P[q])
        S = np.zeros((NB, 12))
        for i in range(NB):
            tr = pos[i] - D[i] @ P[i]
            M = np.hstack([D[i], tr[:, None]])
            S[i] = (K * M).reshape(12)
        return S

    def foot_low(self, S):
        """altura (m) do ponto mais baixo do pé."""
        ver = self.base['ver']; fv = self.foot_v
        pos = ver['pos'][fv].astype(np.float64); bi = ver['bi'][fv]; bw = ver['bw'][fv] / 255.0
        y = np.zeros(len(fv))
        for k in range(4):
            M = S[bi[:, k]].reshape(-1, 3, 4)
            y += bw[:, k] * (np.einsum('nj,nj->n', M[:, 1, :3], pos) + M[:, 1, 3])
        return y.min()

    def clip_from(self, path, name):
        A = Anim(path)
        Wb = A.world(0, animated=False)
        # escala: comprimento da perna (coxa + canela) do jogo / do Mixamo
        Ls = np.linalg.norm(Wb['LeftLeg'][1] - Wb['LeftUpLeg'][1]) + np.linalg.norm(Wb['LeftFoot'][1] - Wb['LeftLeg'][1])
        Lt = np.linalg.norm(self.P[18] - self.P[17]) + np.linalg.norm(self.P[19] - self.P[18])
        s_leg = Lt / Ls
        T = A.t1 - A.t0
        n = int(round(T * 30))                         # quadros únicos do Mixamo (o último repete o primeiro)
        W0 = A.world(A.t0); W1 = A.world(A.t1)
        c0 = (W0['LeftUpLeg'][1] + W0['RightUpLeg'][1]) / 2
        c1 = (W1['LeftUpLeg'][1] + W1['RightUpLeg'][1]) / 2
        drift = c1 - c0; drift[1] = 0.0
        # média horizontal da pelve (centro do ciclo)
        ts = np.linspace(A.t0, A.t1, n + 1)
        cs = np.array([((A.world(t)['LeftUpLeg'][1] + A.world(t)['RightUpLeg'][1]) / 2) - drift * ((t - A.t0) / T) for t in ts])
        cmean = cs.mean(0)
        nfr = n * SUB
        frames = []
        for k in range(nfr + 1):
            t = A.t0 + T * (k / nfr)
            frames.append(self.pose(A, t, Wb, s_leg, drift, T, cmean))
        fr = np.array(frames)
        fr[-1] = fr[0]                                  # laço fecha sem salto
        # trava de chão: o ponto mais baixo do pé (em todo o ciclo) toca y = 0
        low = np.array([self.foot_low(f) for f in fr])
        dy = -low.min()
        fr[:, :, 7] += dy
        speed = np.linalg.norm(drift) * s_leg * K / T   # m/s no espaço do jogo
        info = dict(name=name, T=T, n=n, s_leg=s_leg, speed=speed, dy_m=dy, low_min=low.min(), low_med=np.median(low + dy),
                    low_frames=(low + dy))
        return T, fr, info


def main():
    base_in, walk_fbx, run_fbx, base_out = sys.argv[1:5]
    rt = Retarget(base_in)
    Tw, cw, iw = rt.clip_from(walk_fbx, 'walk')
    Tr, cr, ir = rt.clip_from(run_fbx, 'run')
    for i in (iw, ir):
        lf = i.pop('low_frames')
        print(i)
        print('   pé mais baixo por quadro (cm): min %.2f  mediana %.2f  máx %.2f' % (lf.min() * 100, np.median(lf) * 100, lf.max() * 100))
    clips = [(l, d.copy()) for l, d in rt.base['clips']]
    clips[WALK] = (Tw, cw)
    clips[RUN] = (Tr, cr)
    write_base(base_out, rt.base, clips)
    print('gravado', base_out, [(round(l, 3), d.shape[0]) for l, d in clips])
    np.save('/home/claude/work/walk_new.npy', cw); np.save('/home/claude/work/run_new.npy', cr)


if __name__ == '__main__':
    main()
