"""Etapa 14 - acrescenta ao base.bin os clipes MASCULINOS: 4 = parado, 5 = andar, 6 = correr (derivados dos clipes 0, 1, 3; esses ficam intactos).
Postura masculina: pés afastados, peito aberto, braços relaxados e dedos levemente curvados.
Uso: python3 etapa14_clips.py <base.bin entrada> <base.bin saída>   (a entrada precisa ter só os 4 clipes originais)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from etapa14_poselib import *

def rodrigues(axis, ang):
    a = axis / np.linalg.norm(axis); K_ = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(ang) * K_ + (1 - np.cos(ang)) * K_ @ K_

def curl_fingers(D, pos, side, degs):
    base = 25 if side > 0 else 40
    kax = pos[base + 9] - pos[base]; kax = kax / np.linalg.norm(kax)
    sg = 1.0 if side > 0 else -1.0
    for f in range(4):
        for k in range(3):
            Poser.rot(D, pos, base + f * 3 + k, rodrigues(kax, sg * deg(degs[k])))

def male_edit(D, pos, par):
    for s in (+1, -1):
        o = 0 if s > 0 else 4
        th, ft = 17 + o, 19 + o
        Poser.rot(D, pos, th, Rz(s * deg(par['hip_abd'])))
        Poser.rot(D, pos, ft, Rz(-s * deg(par['hip_abd'])))
        Poser.rot(D, pos, ft, Ry(s * deg(par['toe_out'])))
    for b in (1, 3, 5):
        Poser.rot(D, pos, b, Rx(-deg(par['spine_ext']) / 3))
    for s in (+1, -1):
        o = 0 if s > 0 else 4
        Poser.rot(D, pos, 10 + o, Rz(s * deg(par['arm_abd'])))
        Poser.rot(D, pos, 11 + o, Rz(-s * deg(par['fore_in'])))
        curl_fingers(D, pos, s, par['curl'])

IDLE_M = dict(hip_abd=4.5, toe_out=6, spine_ext=3, arm_abd=0, fore_in=8, curl=(18, 30, 18))
WALK_M = dict(hip_abd=2.5, toe_out=0, spine_ext=2, arm_abd=0, fore_in=4, curl=(18, 30, 18))
RUN_M = dict(hip_abd=2.0, toe_out=0, spine_ext=0, arm_abd=12, fore_in=0, curl=(25, 40, 25))

def make(p, clip, par):
    ln, d = clip
    out = []
    for f in range(len(d)):
        D, pos = p.world(d[f].astype(np.float64)); male_edit(D, pos, par); out.append(p.pack(D, pos))
    out = np.array(out)
    low0 = min(p.rt.foot_low(f.astype(np.float64)) for f in d); low1 = min(p.rt.foot_low(f.astype(np.float64)) for f in out)
    out[:, :, 7] += (low0 - low1)   # mantém o pé no chão
    return ln, out.astype(np.float32)

if __name__ == '__main__':
    p = Poser(sys.argv[1]); cl = p.base['clips']
    assert len(cl) == 4
    new = [(l, d.copy()) for l, d in cl] + [make(p, cl[0], IDLE_M), make(p, cl[1], WALK_M), make(p, cl[3], RUN_M)]
    write_base(sys.argv[2], p.base, new)
    print('clipes', [(round(l, 3), d.shape[0]) for l, d in new])
