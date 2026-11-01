"""Etapa 12 - prévia do rosto (vista frontal) com a MESMA fórmula de recoloração do CuteColor.kt."""
import sys, os, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etapa11_base import read_base

REF = {1: (248.1, 158.1, 135.5), 5: (212.7, 116.6, 75.2), 6: (126.5, 56.5, 4.9)}
SLOT0 = {1: 'skin', 5: 'hair', 6: 'eyes'}

def hexrgb(h): return np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], float)

def recolor(tex, rec, shd, skin=None, hair=None, eyes=None):
    out = tex.copy(); ids = rec[..., 2].astype(int); w0 = rec[..., 0] / 255.0; s = shd[..., 2] * 2 / 255.0
    ch = {1: skin, 5: hair, 6: eyes}
    for i, c in ch.items():
        if c is None: continue
        m = ids == i
        ref = np.array(REF[i]); d = c - ref
        p = np.maximum(d, 0); n = np.where(d < 0, d / np.maximum(ref, 1), 0)
        W = w0[m][:, None]; S = s[m][:, None]
        out[m] = np.clip((tex[m] + S * W * p) * (1 + W * n), 0, 255)
    return out

def render(base_path, tex, px_per_unit=34, x_rng=(-12, 12), y_rng=(150, 174)):
    bs = read_base(base_path); v = bs['ver']
    pos = v['pos'].astype(float); uv = v['uv'].astype(float) * [2048, 1024]
    idx = bs['idx'].astype(int).reshape(-1, 3)
    W = int((x_rng[1] - x_rng[0]) * px_per_unit); H = int((y_rng[1] - y_rng[0]) * px_per_unit)
    img = np.zeros((H, W, 3)); zb = np.full((H, W), -1e9)
    p = pos[idx]
    nrm = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    ok = (p[:, :, 1].min(1) > y_rng[0] - 2) & (p[:, :, 1].max(1) < y_rng[1] + 2) & (np.abs(p[:, :, 0]).max(1) < 14) & (p[:, :, 2].min(1) > 0) & (nrm[:, 2] > 0)
    for t in idx[ok]:
        a, b, c = pos[t]; ua, ub, uc = uv[t]
        X = (np.array([a[0], b[0], c[0]]) - x_rng[0]) * px_per_unit
        Y = (y_rng[1] - np.array([a[1], b[1], c[1]])) * px_per_unit
        x0, x1 = int(max(X.min(), 0)), int(min(X.max() + 1, W - 1)); y0, y1 = int(max(Y.min(), 0)), int(min(Y.max() + 1, H - 1))
        if x1 <= x0 or y1 <= y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (Y[1] - Y[2]) * (X[0] - X[2]) + (X[2] - X[1]) * (Y[0] - Y[2])
        if abs(d) < 1e-9: continue
        l1 = ((Y[1] - Y[2]) * (gx - X[2]) + (X[2] - X[1]) * (gy - Y[2])) / d
        l2 = ((Y[2] - Y[0]) * (gx - X[2]) + (X[0] - X[2]) * (gy - Y[2])) / d
        l3 = 1 - l1 - l2
        m = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        if not m.any(): continue
        z = l1 * a[2] + l2 * b[2] + l3 * c[2]
        U = l1 * ua[0] + l2 * ub[0] + l3 * uc[0]; V = l1 * ua[1] + l2 * ub[1] + l3 * uc[1]
        zz = zb[y0:y1 + 1, x0:x1 + 1]; upd = m & (z > zz)
        col = tex[np.clip(V.astype(int), 0, tex.shape[0] - 1), np.clip(U.astype(int), 0, tex.shape[1] - 1)]
        img[y0:y1 + 1, x0:x1 + 1][upd] = col[upd]; zz[upd] = z[upd]
    # leve sombreamento por profundidade só para dar volume
    return np.clip(img, 0, 255).astype(np.uint8)

def main(cute_dir, base_path, out_png, configs):
    tex = np.asarray(Image.open(os.path.join(cute_dir, 'textures.png')).convert('RGB')).astype(float)
    rec = np.asarray(Image.open(os.path.join(cute_dir, 'recolor.png')).convert('RGB'))
    shd = np.asarray(Image.open(os.path.join(cute_dir, 'recolor_s.png')).convert('RGB'))
    tiles = []
    for name, sk, ha in configs:
        t2 = recolor(tex, rec, shd, hexrgb(sk) if sk else None, hexrgb(ha) if ha else None)
        tiles.append(render(base_path, t2))
    Image.fromarray(np.concatenate(tiles, 1)).save(out_png)

if __name__ == '__main__':
    cute = sys.argv[1]; out = sys.argv[2]
    cfgs = [('original', None, None), ('pele clara + cabelo ruivo', '#FFE0C4', '#B5482A'), ('pele escura + cabelo preto', '#6B4430', '#1C1A1A')]
    main(cute, os.path.join(cute, 'base.bin') if os.path.exists(os.path.join(cute, 'base.bin')) else sys.argv[3], out, cfgs)
