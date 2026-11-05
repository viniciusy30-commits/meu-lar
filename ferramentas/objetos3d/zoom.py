"""prévia ampliada de uma região do GLB (para conferir detalhe do conteúdo)"""
import sys, math, numpy as np
import preview as PV
from PIL import Image
def zoom(path, out, lo, hi, views=((0.5, 0.5), (-0.5, 0.35)), anim=None, size=420):
    arrs, gj = PV.load_posed(path, anim or {})
    lo = np.array(lo); hi = np.array(hi); sel = []
    for key, P, N, C, UV, T in arrs:
        c = P[T]; m = np.all(np.all((c >= lo) & (c <= hi), 2), 1)
        if m.any():
            TT = T[m]; u, inv = np.unique(TT, return_inverse=True)
            sel.append((key, P[u] - np.array([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]), N[u], C[u], UV[u], inv.reshape(-1, 3)))
    ims = []
    for yaw, pitch in views:
        A = PV.asset_from(sel, yaw, pitch); PV.FL.preview(A, '/tmp/_z.png', views=('front',), size=(size, size), span=float((hi - lo).max()) * 1.1)
        ims.append(Image.open('/tmp/_z.png').copy())
    S = Image.new('RGB', (size * len(ims), size)); [S.paste(im, (i * size, 0)) for i, im in enumerate(ims)]; S.save(out)
if __name__ == '__main__':
    pass
