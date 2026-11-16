"""Procura triangulos coplanares sobrepostos (de pecas diferentes) em toda a malha: causa do pisca-pisca no jogo.
python3 qa/coplanar.py [camadas]  -> resumo por camada/material e exemplos com coordenadas"""
import os, sys, collections, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
os.environ.setdefault('STAGE', 'all')
import build6
from shapely.geometry import Polygon


def scan(M, layers=None, tol=0.012, min_area=0.02):
    tris = []
    for (ti, tj, lay, mat), lst in M.data.items():
        if layers and lay not in layers: continue
        for ci, c in enumerate(lst):
            pn = np.frombuffer(c.pn.tobytes(), np.float32).reshape(-1, 6)
            idx = np.frombuffer(c.idx.tobytes(), np.uint16).astype(np.int64).reshape(-1, 3)
            anc = np.frombuffer(c.anc.tobytes(), np.float32).reshape(-1, 2) if len(c.anc) else np.zeros((len(idx), 2), np.float32)
            P = pn[:, :3][idx]
            tris.append((lay, mat, P, anc[:len(idx)]))
    out = collections.Counter(); ex = collections.defaultdict(list)
    for lay, mat, P, anc in tris:
        pass
    # tudo junto: normal, plano, celula
    allP = np.concatenate([t[2] for t in tris]); tag = np.concatenate([[i] * len(t[2]) for i, t in enumerate(tris)])
    anc = np.concatenate([t[3] for t in tris])
    n = np.cross(allP[:, 1] - allP[:, 0], allP[:, 2] - allP[:, 0]); ar = np.linalg.norm(n, axis=1) / 2
    ok = ar > min_area / 4; allP, tag, anc, n, ar = allP[ok], tag[ok], anc[ok], n[ok], ar[ok]
    if os.environ.get('BOX'):
        bx = list(map(float, os.environ['BOX'].split(','))); cc = allP.mean(1)
        ok = (cc[:, 0] > bx[0]) & (cc[:, 0] < bx[2]) & (cc[:, 2] > bx[1]) & (cc[:, 2] < bx[3]); allP, tag, anc, n, ar = allP[ok], tag[ok], anc[ok], n[ok], ar[ok]
    n = n / (2 * ar[:, None])
    s = np.where(np.abs(n[:, 0]) > 1e-6, np.sign(n[:, 0]), np.where(np.abs(n[:, 1]) > 1e-6, np.sign(n[:, 1]), np.sign(n[:, 2])))
    n0 = n.copy(); n = n * s[:, None]
    d = (n * allP[:, 0]).sum(1)
    c = allP.mean(1)
    key = np.stack([np.round(n[:, 0] * 40), np.round(n[:, 1] * 40), np.round(n[:, 2] * 40), np.round(d / tol), np.floor(c[:, 0] / 4), np.floor(c[:, 1] / 4), np.floor(c[:, 2] / 4)], 1).astype(np.int64)
    order = np.lexsort(key.T[::-1]); key = key[order]
    br = np.flatnonzero(np.any(np.diff(key, axis=0) != 0, axis=1)) + 1
    starts = np.concatenate([[0], br]); ends = np.concatenate([br, [len(key)]])
    nflag = 0
    for a, b in zip(starts, ends):
        if b - a < 2 or b - a > 400: continue
        ids = order[a:b]
        # duas pecas diferentes: ancora diferente (objetos distintos) e sobreposicao real em 2D no plano
        nn = n[ids[0]]; ax = int(np.argmax(np.abs(nn))); keep = [i for i in range(3) if i != ax]
        polys = [Polygon(allP[i][:, keep]).buffer(-0.01) for i in ids]
        for p in range(len(ids)):
            for q in range(p + 1, len(ids)):
                i, j = ids[p], ids[q]
                if polys[p].is_empty or polys[q].is_empty: continue
                if (n0[i] * n0[j]).sum() < 0: continue          # costas com costas (dentro de um volume): nao aparece
                ov = polys[p].intersection(polys[q]).area
                if ov > min_area:
                    k2 = (tris[tag[i]][0] + '/' + tris[tag[i]][1], tris[tag[j]][0] + '/' + tris[tag[j]][1])
                    out[k2] += 1; nflag += 1
                    if len(ex[k2]) < 4: ex[k2].append(tuple(np.round(allP[i].mean(0), 1)))
    return out, ex


if __name__ == '__main__':
    P, G, L, M = build6.build()
    lays = sys.argv[1].split(',') if len(sys.argv) > 1 else None
    out, ex = scan(M, lays)
    for k, v in out.most_common(40): print(v, k, ex[k])
    print('total', sum(out.values()))
