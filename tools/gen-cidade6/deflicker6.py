"""Cidade 6: tira o pisca-pisca (disputa de profundidade) de toda a malha antes de exportar.
Acha triangulos coplanares que se sobrepoem, virados para o mesmo lado, e afasta os de cima alguns centimetros
ao longo da normal (o maior fica no lugar; cada camada sobreposta sobe 2,5 cm). O jogo desenha as duas faces e o plano
proximo da camera e longe: duas superficies a menos de ~2 cm brigam de longe."""
import numpy as np
from array import array
from shapely.geometry import Polygon

STEP = 0.025


def run(M, tol=0.012, min_area=0.01, skip_layers=('arbustos', 'mata'), max_area=12.0):
    big = []
    recs = []                                     # (chave do chunk, indice do chunk, indice do triangulo)
    P_all = []; keys = []
    for key, lst in M.data.items():
        if key[2] in skip_layers: continue
        for ci, c in enumerate(lst):
            if not len(c.idx): continue
            pn = np.frombuffer(c.pn.tobytes(), np.float32).reshape(-1, 6)
            idx = np.frombuffer(c.idx.tobytes(), np.uint16).astype(np.int64).reshape(-1, 3)
            P_all.append(pn[:, :3][idx]); keys.append((key, ci, len(idx)))
    if not P_all: return 0
    P = np.concatenate(P_all)
    src = np.concatenate([np.full(n, k, np.int64) for k, (_, _, n) in enumerate(keys)])
    loc = np.concatenate([np.arange(n) for (_, _, n) in keys])
    nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); ar = np.linalg.norm(nrm, axis=1) / 2
    good = ar > min_area / 4
    n0 = np.zeros_like(nrm); n0[good] = nrm[good] / (2 * ar[good, None])
    sg = np.where(np.abs(n0[:, 0]) > 1e-6, np.sign(n0[:, 0]), np.where(np.abs(n0[:, 1]) > 1e-6, np.sign(n0[:, 1]), np.sign(n0[:, 2])))
    n = n0 * sg[:, None]; d = (n * P[:, 0]).sum(1); c = P.mean(1)
    lift = np.zeros(len(P))
    # duas grades deslocadas (meio passo) para nao perder pares que caem na divisa de uma celula
    for off in (0.0, 0.5):
        K = np.stack([np.round(n[:, 0] * 40), np.round(n[:, 1] * 40), np.round(n[:, 2] * 40), np.floor(d / tol + off),
                      np.floor(c[:, 0] / 6 + off), np.floor(c[:, 1] / 6 + off), np.floor(c[:, 2] / 6 + off)], 1).astype(np.int64)
        K[~good] = -1 - np.arange((~good).sum())[:, None]
        order = np.lexsort(K.T[::-1]); Ks = K[order]
        br = np.flatnonzero(np.any(np.diff(Ks, axis=0) != 0, axis=1)) + 1
        for a, b in zip(np.concatenate([[0], br]), np.concatenate([br, [len(Ks)]])):
            if b - a < 2 or b - a > 600: continue
            ids = order[a:b]
            ax = int(np.argmax(np.abs(n[ids[0]]))); kp = [i for i in range(3) if i != ax]
            ids = sorted(ids, key=lambda i: -ar[i])
            polys = {i: Polygon(P[i][:, kp]).buffer(-0.005) for i in ids}
            for q, j in enumerate(ids):
                if polys[j].is_empty: continue
                lv = lift[j]
                for i in ids[:q]:
                    if polys[i].is_empty or (n0[i] * n0[j]).sum() < 0: continue
                    if src[i] == src[j] and abs(lift[i] - lift[j]) < 1e-9 and polys[i].touches(polys[j]): continue
                    ova = polys[i].intersection(polys[j]).area
                    if ova > min_area and lift[j] < lift[i] + STEP - 1e-9:
                        if ar[j] > max_area: big.append((ova, keys[src[i]][0][2:], keys[src[j]][0][2:], tuple(np.round(P[j].mean(0), 1)))); continue
                        lv = max(lv, lift[i] + STEP)
                lift[j] = lv
    big.sort(key=lambda b: -b[0])
    for b in big[:25]: print('   coplanar grande:', b)
    moved = np.flatnonzero(lift > 0)
    if not len(moved): return 0
    # reescreve os chunks: triangulos levantados ganham vertices proprios
    by = {}
    for t in moved: by.setdefault(src[t], []).append(t)
    done = 0
    for s, ts in by.items():
        key, ci, _ = keys[s]; ch = M.data[key][ci]
        if ch.nv + 3 * len(ts) >= 65000: continue
        pn = np.frombuffer(ch.pn.tobytes(), np.float32).reshape(-1, 6).copy()
        uv = np.frombuffer(ch.uv.tobytes(), np.float32).reshape(-1, 2)
        col = np.frombuffer(ch.col.tobytes(), np.uint8).reshape(-1, 4)
        idx = np.frombuffer(ch.idx.tobytes(), np.uint16).astype(np.int64).reshape(-1, 3).copy()
        add_pn, add_uv, add_col = [], [], []
        base = ch.nv
        for t in ts:
            li = loc[t]; vids = idx[li]
            for k, v in enumerate(vids):
                p = pn[v].copy(); p[:3] = p[:3] + n0[t] * lift[t]
                add_pn.append(p); add_uv.append(uv[v]); add_col.append(col[v])
                idx[li, k] = base; base += 1
            done += 1
        ch.pn = array('f', np.concatenate([pn, np.array(add_pn, np.float32)]).ravel().tolist())
        ch.uv = array('f', np.concatenate([uv, np.array(add_uv, np.float32)]).ravel().tolist())
        ch.col = array('B', np.concatenate([col, np.array(add_col, np.uint8)]).ravel().tolist())
        ch.idx = array('H', idx.ravel().astype(np.uint16).tolist())
        ch.nv = base
    return done
