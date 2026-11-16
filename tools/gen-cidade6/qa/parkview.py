"""Conferencia rapida do Parque Central (Lagoa Azul) sem gerar a cidade: python3 qa/parkview.py SAIDA [plantas]"""
import os, sys, struct, random, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from mesh import Mesh, WHITE
from plan6 import Plan, W, H
from roads6 import Y_LAWN
import props6, buildings6
from view6 import Source, Viewer
import appview


class Stub: pass


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    P = Plan(); blk = [b for b in P.blocks if b.get('zone') == 'parque'][0]
    M = Mesh(W, H)
    L = Stub(); L.B = buildings6.Builder(M, random.Random(1)); L.B.drives = []
    pr = props6.Props(P, Stub(), L, M)
    pr.central_park(blk)
    M.free('lotes'); M.m('grama'); M.shp(blk['poly'], Y_LAWN, (120, 170, 90))
    S = Source().add_mesh(M)
    A = appview.A
    tb = open(os.path.join(A, 'c6_tree.bin'), 'rb').read(); n = struct.unpack_from('<i', tb, 4)[0]; o = 8; TP = []
    for _ in range(n):
        mat, nv, ni, cr, cg, cb = struct.unpack_from('<iii3f', tb, o); o += 24
        V = np.frombuffer(tb, '<f4', nv * 8, o).reshape(nv, 8); o += nv * 32
        I = np.frombuffer(tb, '<u2', ni, o).astype(np.int64); o += ni * 2
        TP.append(('arvore_folhas' if mat == 57 else 'arvore_casca', V, I, np.array([cr, cg, cb])))
    H6 = max(t[1][:, 1].max() for t in TP); R6 = max(np.hypot(t[1][:, 0], t[1][:, 2]).max() for t in TP)
    S.trees6 = (pr.app_trees, [y + 0.7 - 0.7 for y in pr.app_y], TP, H6, R6, None, 1, 1, 1)
    minx, minz, maxx, maxz = blk['poly'].bounds; cx, cz = (minx + maxx) / 2, (minz + maxz) / 2
    appview.add_trees(S, cx, cz, 400, 900)
    print('arvores/plantas:', len(pr.app_trees), 'fauna:', len(getattr(pr, 'fauna', [])))
    v = Viewer(S, appview.texdir())
    lx, lz = cx + 8, cz + 14
    shots = sys.argv[2:] or ['all']
    v.top(os.path.join(out, 'p_top.png'), cx, cz, 230)
    v.shot(os.path.join(out, 'p_aerea.png'), (cx - 90, 70, maxz + 40), (cx, 0, cz), R=500, fov=60)
    v.shot(os.path.join(out, 'p_aerea2.png'), (maxx + 40, 60, minz - 40), (cx, 0, cz), R=500, fov=60)
    g = getattr(pr, 'lagoa', None)
    if g:
        ix, iz = g[4], g[5]
        v.shot(os.path.join(out, 'p_ponte.png'), (ix + 14, 3.0, iz - 26), (ix, 1.0, iz - 12), R=200, fov=60)
        v.shot(os.path.join(out, 'p_ponte_baixo.png'), (ix + 9, 0.6, iz - 13), (ix, 0.6, iz - 13), R=200, fov=70)
        v.shot(os.path.join(out, 'p_deque.png'), (g[0] + g[2] * 0.4, 3.2, g[1] - g[3] * 0.2), (g[0] + g[2] * 0.85, 0.5, g[1] - g[3] * 0.4), R=200, fov=70)
        v.shot(os.path.join(out, 'p_deque2.png'), (g[0] + g[2] * 1.3, 6, g[1] + g[3] * 0.4), (g[0] + g[2] * 0.85, 0.5, g[1] - g[3] * 0.4), R=200, fov=60)
    for i, (nm, (px, pz)) in enumerate(getattr(pr, 'park_spots', {}).items()):
        v.shot(os.path.join(out, f'p_s_{nm}.png'), (px - 12, 14, pz + 14), (px, 0.5, pz), R=200, fov=62); v.shot(os.path.join(out, f'p_t_{nm}.png'), (px + 6, 1.7, pz + 8), (px, 1.0, pz), R=120, fov=70)
    v.run()


if __name__ == '__main__':
    main()
