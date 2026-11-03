#!/usr/bin/env python3
"""Pre-visualizacao dos clipes gerados (silhueta sombreada, lado + frente) -- confere anatomia e passada.
Uso: python3 etapa53_preview.py <assets/cute> <pasta com clips_<g>.bin> <grupo> <saida.png> [clipe=1] [nquadros=8] [tipo=1]"""
import sys, os
_here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, _here)
CU = sys.argv[1].rstrip('/') + '/'; CLIPDIR = sys.argv[2].rstrip('/') + '/'; grp = sys.argv[3]; outp = sys.argv[4]
clip = int(sys.argv[5]) if len(sys.argv) > 5 else 1; nq = int(sys.argv[6]) if len(sys.argv) > 6 else 8; typ = int(sys.argv[7]) if len(sys.argv) > 7 else 1
sys.argv = [sys.argv[0], CU]
import numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import etapa48_jovem as E
K = 0.0082
v, idx, fl, tail = E.read_piece(CU + 'p_body_%s%d.bin' % (grp, typ))
cl = E.read_clips(CLIPDIR + 'clips_%s.bin' % grp)
ln, d = cl[clip]
pos = v['pos'].astype(np.float64); bi = v['bi'].astype(int); bw = v['bw'] / 255.0
def skin(M):
    M = M.reshape(55, 3, 4).astype(np.float64); out = np.zeros_like(pos)
    for k in range(4):
        Mb = M[bi[:, k]]; out += bw[:, k, None] * (np.einsum('vij,vj->vi', Mb[:, :, :3], pos) + Mb[:, :, 3])
    return out / K
frames = np.linspace(0, len(d) - 1, nq + 1)[:nq].astype(int)
fig, ax = plt.subplots(2, nq, figsize=(1.7 * nq, 2 * 2.3))
tri = idx
for c, f in enumerate(frames):
    P = skin(d[f])
    for r, view in enumerate(('side', 'front')):
        a = ax[r, c]
        if view == 'side': X = P[:, 2]; Y = P[:, 1]; Dp = P[:, 0]; n_axis = 0
        else: X = -P[:, 0]; Y = P[:, 1]; Dp = -P[:, 2]; n_axis = 2
        T3 = P[tri]; e1 = T3[:, 1] - T3[:, 0]; e2 = T3[:, 2] - T3[:, 0]; nn = np.cross(e1, e2); nn /= (np.linalg.norm(nn, axis=1, keepdims=True) + 1e-12)
        cam = np.array([1.0, 0, 0]) if view == 'side' else np.array([0, 0, -1.0])
        # depth: the camera looks from +x (side) / -z... draw back-to-front by distance along view axis
        depth = (T3.mean(1) * cam).sum(1)
        order = np.argsort(depth)
        light = np.array([0.4, 0.6, 0.7]); shade = 0.35 + 0.65 * np.clip(np.abs(nn @ light) , 0, 1)
        polys = np.stack([X[tri], Y[tri]], -1)[order]
        col = plt.cm.Greys(shade[order] * 0.85)
        a.add_collection(PolyCollection(polys, facecolors=col, edgecolors='none'))
        a.set_xlim(-0.8, 0.8) if False else None
        cx = 0.0
        a.set_xlim(-1.0 / K * 0.0 + (X.mean() - 0.75 / K * 0 - 80), (X.mean() + 80)) if False else None
        a.set_aspect('equal'); a.set_ylim(-5, P[:, 1].max() + 5); a.set_xlim(X.mean() - 70, X.mean() + 70) if view == 'side' else a.set_xlim(-70, 70)
        a.axhline(0, color='r', lw=0.6); a.axis('off'); a.set_title('f%d' % f, fontsize=7)
plt.tight_layout(); plt.savefig(outp, dpi=130); print('ok', outp)
