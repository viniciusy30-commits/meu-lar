"""Etapa 31 - gola das roupas segue o pescoço do corpo: nos vértices do pescoço (y > 139) os pesos de osso das blusas/vestidos
passam a ser misturados com os do vértice mais próximo do corpo-base, então a pele não vaza na gola quando o personagem se mexe.
Uso: python3 etapa31_pescoco.py [pasta_assets_cute]   (altera p_top_*.bin e p_overall_*.bin no lugar)"""
import sys, os, glob, struct
import numpy as np
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app', 'src', 'main', 'assets', 'cute')
REC = np.dtype([('pos', '<f4', 3), ('nor', '<f4', 3), ('uv', '<f4', 2), ('col', 'u1', 4), ('bi', 'u1', 4), ('bw', 'u1', 4)])
def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
b = open(os.path.join(SRC, 'base.bin'), 'rb').read(); nv, ni, nb, nc = struct.unpack_from('<4i', b, 4)
br = np.frombuffer(b, REC, nv, 20); BP = br['pos'].astype(float); BI = br['bi'].astype(int); BW = br['bw'].astype(float) / 255
cand = np.where(BP[:, 1] > 128)[0]
for f in sorted(glob.glob(os.path.join(SRC, 'p_top_*.bin')) + glob.glob(os.path.join(SRC, 'p_overall_*.bin'))):
    raw = bytearray(open(f, 'rb').read()); n = struct.unpack_from('<i', raw, 4)[0]
    r = np.frombuffer(raw, REC, n, 16).copy()
    P = r['pos'].astype(float); I = r['bi'].astype(int); W = r['bw'].astype(float) / 255
    ch = 0
    for v in np.where(P[:, 1] > 139)[0]:
        t = sm(139, 147, P[v, 1])
        j = cand[np.argmin(np.linalg.norm(BP[cand] - P[v], axis=1))]
        d = {}
        for k in range(4):
            d[I[v, k]] = d.get(I[v, k], 0) + (1 - t) * W[v, k]
            d[BI[j, k]] = d.get(BI[j, k], 0) + t * BW[j, k]
        top = sorted(d.items(), key=lambda kv: -kv[1])[:4]
        tot = sum(w for _, w in top)
        if tot <= 0: continue
        q = np.zeros(4, int); ids = np.zeros(4, int)
        for k, (bid, w) in enumerate(top): ids[k] = bid; q[k] = int(round(w / tot * 255))
        q[np.argmax(q)] += 255 - q.sum()
        r['bi'][v] = ids; r['bw'][v] = q; ch += 1
    raw[16:16 + n * 44] = r.tobytes()
    open(f, 'wb').write(bytes(raw)); print(os.path.basename(f), 'vertices da gola ajustados:', ch)
