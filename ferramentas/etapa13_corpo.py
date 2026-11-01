"""Etapa 13 - corpo masculino x feminino e busto maior: réplica em Python da BodyMorph.warp (Kotlin) + prévia renderizada.
Uso: python3 etapa13_corpo.py <base.bin> <saida.png>"""
import sys, os, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etapa11_base import read_base

# ---- parâmetros (iguais aos de BodyMorph.kt) ----
BUST_C = (9.0, 127.0, 7.5); BUST_R = 11.0; BUST_UP = 0.85; BUST_DN = 1.1; BUST_P = 0.8; BUST_SPREAD = 0.9; BUST_DROP = 0.10
BUST_POS = 8.0; BUST_NEG = 3.0; BUST_BASE_F = 2.0; BUST_BASE_M = -1.5
M_OMBRO, M_PEITO, M_CINT, M_QUAD, M_BRACO, M_PESCOCO = 0.75, 0.6, 0.55, -0.6, 0.25, 0.13
M_ALTURA = 1.035

def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def gs(x, c, s): return np.exp(-((x - c) / s) ** 2)

def warp(p, b, masc=False):
    b = np.array(b, float).copy()
    x, y, z = p[:, 0], p[:, 1], p[:, 2]; ax = np.abs(x); sx = np.where(x < 0, -1., 1.)
    d = np.zeros_like(p); low = 1 - sm(146, 156, y)
    m = 1.0 if masc else 0.0
    peso = .14 * b[1]; ombro = 3.0 * (b[2] + M_OMBRO * m); peito = .10 * (b[3] + M_PEITO * m)
    cint = .15 * (b[5] + M_CINT * m); quad = .12 * (b[6] + M_QUAD * m); coxa = .25 * b[7]; braco = .25 * (b[8] + M_BRACO * m); cab = .12 * b[9]
    busto = (BUST_POS * b[4] if b[4] > 0 else BUST_NEG * b[4]) + (BUST_BASE_M if masc else BUST_BASE_F)
    d[:, 0] += sx * np.minimum(ax, 24) * peso * low; d[:, 2] += (z - 3) * peso * low
    d[:, 0] += sx * ombro * sm(22, 34, ax) * sm(62, 78, y) * low
    w = sm(100, 114, y) * (1 - sm(128, 140, y)) * (1 - sm(18, 28, ax)); d[:, 0] += x * peito * w; d[:, 2] += z * peito * w
    # busto: duas cúpulas suaves empurradas para frente (altura em função da distância ao mamilo), com leve abertura para os lados e queda
    cx, cy, cz = BUST_C
    dx = x - sx * cx; dy = y - cy
    dys = np.where(dy > 0, dy * BUST_UP, dy * BUST_DN)
    rho = np.sqrt(dx * dx + dys * dys)
    fr = sm(-3.0, 3.0, z)                       # só a frente do tronco
    t = np.clip(1 - rho / BUST_R, 0, 1); h = (t * t * (3 - 2 * t)) ** BUST_P * fr
    d[:, 2] += busto * h
    d[:, 0] += dx / BUST_R * BUST_SPREAD * busto * h
    d[:, 1] += dys / BUST_R * BUST_SPREAD * busto * h - BUST_DROP * busto * h
    w = sm(92, 100, y) * (1 - sm(110, 118, y)) * (1 - sm(20, 30, ax)); d[:, 0] += x * cint * w; d[:, 2] += z * cint * w
    w = sm(66, 78, y) * (1 - sm(94, 104, y)) * (1 - sm(26, 36, ax)); d[:, 0] += x * quad * w; d[:, 2] += (z - 3) * quad * .5 * w
    rx = x - sx * 9.3; rz = z - 3.8; r = np.hypot(rx, rz)
    w = sm(44, 58, y) * (1 - sm(86, 98, y)) * (1 - sm(11, 19, r)) * sm(0, 5, ax); d[:, 0] += rx * coxa * w; d[:, 2] += rz * coxa * w
    ux = .6012 * sx; vx = x - sx * 13.3; vy = y - 142.5; vz = z + 2.9; t = vx * ux + vy * -.7991 + vz * -.0076
    px = vx - t * ux; py = vy + t * .7991; pz = vz + t * .0076; r = np.sqrt(px ** 2 + py ** 2 + pz ** 2)
    w = sm(6, 16, t) * (1 - sm(44, 52, t)) * (1 - sm(9, 15, r)); d[:, 0] += px * braco * w; d[:, 1] += py * braco * w; d[:, 2] += pz * braco * w
    w = sm(146, 156, y); d[:, 0] += x * cab * w; d[:, 1] += (y - 148) * cab * w; d[:, 2] += z * cab * w
    if masc:   # pescoço mais grosso
        w = gs(y, 149, 5); d[:, 0] += x * M_PESCOCO * w; d[:, 2] += (z + 0.3) * M_PESCOCO * w
    return p + d

def vnormals(P, idx):
    t = P[idx]; n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); N = np.zeros_like(P)
    for k in range(3): np.add.at(N, idx[:, k], n)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)

def render(P, N, idx, rot, color, W=330, H=640, ppu=3.4, cy=88.0):
    c, s = np.cos(rot), np.sin(rot)
    R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    Q = P @ R.T; NN = N @ R.T
    img = np.zeros((H, W, 3)); zb = np.full((H, W), -1e9)
    L = np.array([-0.35, 0.45, 0.82]); L /= np.linalg.norm(L)
    X = Q[:, 0] * ppu + W / 2; Y = H / 2 - (Q[:, 1] - cy) * ppu
    for t in idx:
        xs, ys, zs = X[t], Y[t], Q[t, 2]
        x0, x1 = int(max(xs.min(), 0)), int(min(xs.max() + 1, W - 1)); y0, y1 = int(max(ys.min(), 0)), int(min(ys.max() + 1, H - 1))
        if x1 <= x0 or y1 <= y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        dd = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(dd) < 1e-9: continue
        l1 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / dd
        l2 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / dd; l3 = 1 - l1 - l2
        m = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        if not m.any(): continue
        z = l1 * zs[0] + l2 * zs[1] + l3 * zs[2]
        n = l1[..., None] * NN[t[0]] + l2[..., None] * NN[t[1]] + l3[..., None] * NN[t[2]]
        n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-9)
        lam = np.clip(n @ L, 0, 1) * 0.8 + 0.22
        zz = zb[y0:y1 + 1, x0:x1 + 1]; up = m & (z > zz)
        img[y0:y1 + 1, x0:x1 + 1][up] = (lam[..., None] * color)[up]; zz[up] = z[up]
    return np.clip(img, 0, 255).astype(np.uint8)

def main(base, out):
    bs = read_base(base); P = bs['ver']['pos'].astype(float); idx = bs['idx'].astype(int).reshape(-1, 3)
    skin = np.array([250., 190., 165.])
    cfgs = [('F padrão', [0] * 10, False), ('F busto +50', [0, 0, 0, 0, .5, 0, 0, 0, 0, 0], False), ('F busto +100', [0, 0, 0, 0, 1, 0, 0, 0, 0, 0], False), ('M padrão', [0] * 10, True)]
    rows = []
    for rot in (0.0, np.pi / 2 * 0.999, 0.6):
        tiles = []
        for nm, b, masc in cfgs:
            Q = warp(P, b, masc)
            tiles.append(render(Q, vnormals(Q, idx), idx, rot, skin))
        rows.append(np.concatenate(tiles, 1))
    Image.fromarray(np.concatenate(rows, 0)).save(out)
    zr = []
    for rot in (0.0, 0.7, np.pi / 2 * 0.999):
        tiles = []
        for nm, b, masc in cfgs:
            Q = warp(P, b, masc)
            tiles.append(render(Q, vnormals(Q, idx), idx, rot, skin, W=330, H=330, ppu=7.0, cy=125.0))
        zr.append(np.concatenate(tiles, 1))
    Image.fromarray(np.concatenate(zr, 0)).save(out.replace('.png', '_zoom.png'))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
