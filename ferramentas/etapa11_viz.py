"""Etapa 11 - renderização de conferência (silhuetas lado/frente) de um clip do base.bin."""
import sys, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from etapa11_base import *

def skin_all(bs, S):
    ver = bs['ver']; pos = ver['pos'].astype(np.float64); bi = ver['bi']; bw = ver['bw'] / 255.0
    out = np.zeros((len(pos), 3))
    for k in range(4):
        M = S[bi[:, k]].reshape(-1, 3, 4)
        out += bw[:, k:k+1] * (np.einsum('nij,nj->ni', M[:, :, :3], pos) + M[:, :, 3])
    return out

def montage(path_bin, clip, out_png, nph=8, title=''):
    bs = read_base(path_bin)
    ln, d = bs['clips'][clip]
    nf = d.shape[0]
    fig, ax = plt.subplots(2, nph, figsize=(2.0 * nph, 7.2))
    ver = bs['ver']
    for j in range(nph):
        f = int(round(j * (nf - 1) / nph))
        P = skin_all(bs, d[f].astype(np.float64))
        o = np.argsort(P[:, 0])
        ax[0, j].scatter(P[:, 2], P[:, 1], s=0.35, c='#335', alpha=0.6, linewidths=0)
        ax[0, j].set_xlim(-0.9, 0.9); ax[0, j].set_ylim(-0.05, 1.6); ax[0, j].set_aspect('equal'); ax[0, j].axhline(0, c='r', lw=0.6)
        ax[0, j].set_title('%s f%d (%.2fs)' % (title, f, ln * f / (nf - 1)), fontsize=7); ax[0, j].axis('off')
        ax[1, j].scatter(P[:, 0], P[:, 1], s=0.35, c='#533', alpha=0.6, linewidths=0)
        ax[1, j].set_xlim(-0.8, 0.8); ax[1, j].set_ylim(-0.05, 1.6); ax[1, j].set_aspect('equal'); ax[1, j].axhline(0, c='r', lw=0.6); ax[1, j].axis('off')
    plt.tight_layout(); plt.savefig(out_png, dpi=80); plt.close()

if __name__ == '__main__':
    montage(sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 8, sys.argv[5] if len(sys.argv) > 5 else '')
