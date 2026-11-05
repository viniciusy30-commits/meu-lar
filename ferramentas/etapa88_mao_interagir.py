#!/usr/bin/env python3
"""Etapa 88: conserta a mão no clipe 8 (interagir). O clipe da UAL torcia o punho (a mão girava de lado e os dedos ficavam
tortos ao esticar o braço). Aqui a mão passa a seguir o antebraço (punho reto, como na pose de repouso do Sims) e os dedos
ficam numa curva relaxada (30% da flexão do clipe original), com a palma virada para baixo (pronação de 60°, metade no
antebraço e metade no punho). Os outros clipes não mudam.
Uso: python3 etapa88_mao_interagir.py <pasta com clips_<g>.bin> [--out <pasta>] [grupos...]
"""
import sys, os
import numpy as np
from scipy.spatial.transform import Rotation as Rot, Slerp
_here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, _here)
ARGS = sys.argv[1:]
sys.argv = [sys.argv[0], os.path.join(_here, '..', 'app/src/main/assets/cute'),
            os.path.join(_here, '..', 'Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb')]
import etapa83_sentar as S
CLIP = 8; GROUPS = ['tf', 'tm', 'af', 'am', 'ef', 'em', 'cu', 'pu']
REST = {}


def write_clips(path, clips):
    import struct
    nb = 55
    with open(path, 'wb') as f:
        f.write(b'CLP1'); f.write(struct.pack('<ii', nb, len(clips)))
        for ln, d in clips:
            f.write(struct.pack('<fi', float(ln), len(d))); f.write(np.ascontiguousarray(d, dtype='<f4').tobytes())


def A4(m12):
    M = np.eye(4); M[:3, :4] = m12.reshape(3, 4); return M


def fix(d, BI, curl=0.3, pron=-60.0):
    out = d.copy()
    for s in 'lr':
        ua, la, hd = BI['upperarm_' + s], BI['lowerarm_' + s], BI['hand_' + s]
        base = 25 if s == 'l' else 40
        fingers = [base + k for k in range(15)]
        for f in range(len(d)):
            Mla = A4(d[f, la]); Mhd = A4(d[f, hd])
            sc = np.cbrt(abs(np.linalg.det(Mla[:3, :3])))
            Mnew = Mla.copy()                       # punho reto: a mão gira junto com o antebraço
            if pron:
                # pronação (palma para baixo, como quem vai pegar/apertar): metade no antebraço (pivô no cotovelo), metade no punho
                Ml = Mla[:3, :3] / sc
                ax = Ml @ REST[s]['dir']; ax /= np.linalg.norm(ax)
                el = np.arccos(np.clip(-ax[1], -1, 1)) / (np.pi / 2)        # 0 = braço caído, 1 = esticado na horizontal
                wgt = float(np.clip((el - 0.25) / 0.6, 0, 1)); wgt = wgt * wgt * (3 - 2 * wgt)
                sg = (1 if s == 'r' else -1) * wgt
                def about(piv_rest, ang, M):
                    pw = M[:3, :3] @ piv_rest + M[:3, 3]
                    Rq = Rot.from_rotvec(ax * np.radians(ang) * sg).as_matrix()
                    T = np.eye(4); T[:3, :3] = Rq; T[:3, 3] = pw - Rq @ pw
                    return T
                Tel = about(REST[s]['elbow'], pron * 0.5, Mla)
                Mla_n = Tel @ Mla
                out[f, la] = Mla_n[:3, :4].reshape(12)
                Mnew = about(REST[s]['wrist'], pron * 0.5, Mla_n) @ Mla_n
            out[f, hd] = Mnew[:3, :4].reshape(12)
            inv_old = np.linalg.inv(Mhd)
            for b in fingers:
                rel = inv_old @ A4(d[f, b])          # pose do dedo relativa à mão antiga
                R = rel[:3, :3]; t = rel[:3, 3]
                # metade da flexão: rotação relativa interpolada até a identidade (o pivô fica no lugar: t = (I - R) p)
                r = Rot.from_matrix(R / np.cbrt(abs(np.linalg.det(R))))
                Rh = Slerp([0, 1], Rot.concatenate([Rot.identity(), r]))([curl]).as_matrix()[0]
                # pivô p do osso: solução de (I - R) p = t (mínimos quadrados)
                p = np.linalg.lstsq(np.eye(3) - R, t, rcond=None)[0]
                reln = np.eye(4); reln[:3, :3] = Rh; reln[:3, 3] = (np.eye(3) - Rh) @ p
                out[f, b] = (Mnew @ reln)[:3, :4].reshape(12)
    return out


if __name__ == '__main__':
    args = ARGS; src = args[0].rstrip('/') + '/'; rest = args[1:]; out = src
    if '--out' in rest:
        i = rest.index('--out'); out = rest[i + 1].rstrip('/') + '/'; rest = rest[:i] + rest[i + 2:]
    os.makedirs(out, exist_ok=True)
    import etapa53_animacoes_ual as A
    for g in rest or GROUPS:
        body = A.recover_joints(g, A.read_ratios()); sc0 = body['sc']; Q = body['Q'] if 'Q' in body else None
        J = body['J']
        for s_ in 'lr':
            w = np.asarray(J['hand_' + s_], float); e = np.asarray(J['lowerarm_' + s_], float)
            REST[s_] = dict(dir=(w - e) / np.linalg.norm(w - e), wrist=w * sc0, elbow=e * sc0)
        cl = S.read_clips(src + 'clips_%s.bin' % g)
        ln, d = cl[CLIP]
        d2 = fix(np.asarray(d, np.float64).reshape(len(d), 55, 12), A.BI, curl=float(os.environ.get('CURL', 0.3)), pron=float(os.environ.get('PRON', -60))).astype(np.float32)
        cl = [(l_, dd) for l_, dd in cl]; cl[CLIP] = (ln, d2)
        A.E.write_clips(out + 'clips_%s.bin' % g, cl)
        print(g, 'mão do clipe 8 corrigida (%d quadros)' % len(d2))
