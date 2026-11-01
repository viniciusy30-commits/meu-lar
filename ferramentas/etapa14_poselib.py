"""Edição de poses no mundo para o esqueleto de 55 ossos (base.bin). Copiado/adaptado de etapa11_retarget."""
import sys, os
sys.path.insert(0, '' + os.path.dirname(os.path.abspath(__file__)) + '')
import numpy as np
from etapa11_base import read_base, write_base, recover_bind, GP, NB, K, NAMES
from etapa11_retarget import Retarget, ortho, arc

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app', 'src', 'main', 'assets', 'cute', 'base.bin')
BINDLINKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'etapa14_bindlinks.pkl')
CHILDREN = [[j for j in range(NB) if GP[j] == i] for i in range(NB)]
def subtree(b):
    out = [b]; k = 0
    while k < len(out):
        out += CHILDREN[out[k]]; k += 1
    return out
SUB = [subtree(i) for i in range(NB)]

class Poser:
    def __init__(self, path=BASE):
        self.rt = Retarget(path)
        self.P = self.rt.P.copy()
        self.base = self.rt.base
        # dedos: a posição recuperada dos clips é indeterminada (dedos rígidos na mão); usa a pose de ligação exata do FBX
        import pickle
        bl = pickle.load(open(BINDLINKS, 'rb'))
        fn = ['index', 'middle', 'ring', 'pinky', 'thumb']
        for si, s in enumerate(('l', 'r')):
            for fi, f in enumerate(fn):
                for k in (1, 2, 3):
                    nm = '%s_0%d_%s' % (f, k, s)
                    self.P[25 + si * 15 + fi * 3 + (k - 1)] = bl[nm][3, :3]
    def world(self, S):
        """S (55,12) -> D (55,3,3) rotações, pos (55,3) posição mundial das juntas (unid. FBX)."""
        D = np.zeros((NB, 3, 3)); pos = np.zeros((NB, 3))
        for i in range(NB):
            M = S[i].reshape(3, 4).astype(np.float64) / K
            D[i] = M[:, :3]; pos[i] = D[i] @ self.P[i] + M[:, 3]
        return D, pos
    def pack(self, D, pos):
        S = np.zeros((NB, 12))
        for i in range(NB):
            t = pos[i] - D[i] @ self.P[i]
            S[i] = (K * np.hstack([D[i], t[:, None]])).reshape(12)
        return S.astype(np.float32)
    @staticmethod
    def rot(D, pos, b, R, pivot=None):
        """Gira o osso b (e todos os filhos) com a rotação MUNDIAL R em torno de `pivot` (padrão: junta de b)."""
        pv = pos[b].copy() if pivot is None else np.asarray(pivot, float)
        for j in SUB[b]:
            D[j] = R @ D[j]; pos[j] = pv + R @ (pos[j] - pv)
    @staticmethod
    def shift(D, pos, b, off):
        for j in SUB[b]: pos[j] = pos[j] + np.asarray(off, float)

def Rx(a):
    c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def Ry(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def Rz(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def deg(a): return np.deg2rad(a)

if __name__ == '__main__':
    p = Poser()
    for ci, (ln, d) in enumerate(p.base['clips']):
        err = 0
        for f in range(len(d)):
            D, pos = p.world(d[f].astype(np.float64)); S2 = p.pack(D, pos)
            err = max(err, np.abs(S2 - d[f]).max())
        print('clip', ci, 'len', ln, 'frames', len(d), 'roundtrip err', err)
    D, pos = p.world(p.base['clips'][0][1][0].astype(np.float64))
    np.set_printoptions(precision=1, suppress=True)
    for i in [0, 4, 8, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28, 29]: print(i, NAMES[i], 'pivot', p.P[i], 'pos', pos[i])
    # primeiro = último quadro?
    for ci, (ln, d) in enumerate(p.base['clips']): print(ci, 'loop diff', np.abs(d[0] - d[-1]).max())
