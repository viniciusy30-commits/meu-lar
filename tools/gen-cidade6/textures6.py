"""Cidade 6 - texturas procedurais (1024 px, JPEG) e tabela de materiais.
Cada textura nasce de um mapa de ALTURA iluminado (relevo: tijolo, telha, tabua, pedra parecem ter volume) + cor com variacao
por peca, sujeira e desgaste. A cor do vertice multiplica a textura: as 'tingiveis' (siding, reboco, telha, folhagem...) sao
claras e recebem a cor de cada casa; as naturais (asfalto, grama, tijolo, vidro...) ja tem a cor certa."""
import os, math
import numpy as np
from PIL import Image

N = 1024
LX, LY = -0.55, -0.7           # luz de cima-esquerda (para o relevo)


def vnoise(n, cells, seed):
    r = np.random.RandomState(seed); g = r.rand(cells + 1, cells + 1); g[-1, :] = g[0, :]; g[:, -1] = g[:, 0]
    t = np.linspace(0, cells, n, endpoint=False); i = t.astype(int); f = t - i; f = f * f * (3 - 2 * f)
    a = g[i][:, i]; b = g[i][:, i + 1]; c = g[i + 1][:, i]; d = g[i + 1][:, i + 1]
    fx = f[None, :]; fy = f[:, None]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(n=N, base=4, oct=5, seed=0, gain=0.5):
    s = np.zeros((n, n)); amp = 1.0; tot = 0
    for o in range(oct):
        s += vnoise(n, base * 2 ** o, seed + o * 13) * amp; tot += amp; amp *= gain
    return s / tot


def light(h, strength=1.0):
    """sombreado do relevo: derivada do mapa de altura (repete nas bordas)"""
    gx = np.roll(h, -1, 1) - np.roll(h, 1, 1); gy = np.roll(h, -1, 0) - np.roll(h, 1, 0)
    return 1.0 + strength * (gx * LX + gy * LY)


def rgb3(c, v):
    v = v[..., None] if v.ndim == 2 else v
    return v * np.array(c, float)[None, None, :]


def grid_ids(x, y, w, h, stagger=0.5):
    row = (y // h).astype(int); off = (row % 2) * stagger * w
    col = ((x + off) // w).astype(int)
    u = ((x + off) % w) / w; v = (y % h) / h
    return row * 1009 + col, u, v


def hash01(i, s=0):
    return ((np.sin(np.asarray(i, float) * 12.9898 + s * 78.233) * 43758.5453) % 1.0 + 1.0) % 1.0


def voronoi(n, k, seed):
    r = np.random.RandomState(seed); P = r.rand(k, 2) * n
    P = np.vstack([P + (dx, dy) for dx in (-n, 0, n) for dy in (-n, 0, n)])
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    best = np.full((n, n), 1e12, np.float32); second = best.copy(); idx = np.zeros((n, n), np.int32)
    for i, (px, py) in enumerate(P):
        d = (x - px) ** 2 + (y - py) ** 2
        m = d < best
        second = np.where(m, best, np.minimum(second, d)); idx = np.where(m, i % k, idx); best = np.where(m, d, best)
    return idx, np.sqrt(second) - np.sqrt(best)


Y, X = np.mgrid[0:N, 0:N].astype(np.float64)


# ================================================================ chao
def asfalto():
    n1 = fbm(N, 8, 6, 1); n2 = fbm(N, 64, 2, 2); sp = np.random.RandomState(3).rand(N, N)
    v = 0.34 + 0.08 * n1 + 0.05 * n2 + (sp > 0.94) * 0.09 - (sp < 0.05) * 0.07
    v += np.clip((fbm(N, 3, 3, 4) - 0.55) * 3, 0, 1) * 0.05
    crack = (np.abs(fbm(N, 3, 6, 5, 0.6) - 0.5) < 0.0022) & (fbm(N, 2, 2, 75) > 0.55)
    v = np.where(crack, v * 0.6, v)
    v *= light(n2 + sp * 0.3, 0.8)
    return rgb3((228, 229, 233), v)


def calcada():
    pid, u, w = grid_ids(X, Y, N / 2, N / 2, 0.0)
    tone = 0.80 + 0.05 * hash01(pid) + 0.06 * fbm(N, 6, 5, 6) + 0.03 * fbm(N, 64, 2, 7)
    edge = np.minimum.reduce([u, 1 - u, w, 1 - w]) * (N / 2)
    h = np.clip(edge / 4, 0, 1) + 0.05 * fbm(N, 40, 2, 8)
    v = tone * light(h, 1.2) * np.where(edge < 2.5, 0.72, 1.0)
    return rgb3((240, 236, 228), v - np.clip((fbm(N, 4, 4, 9) - 0.6) * 4, 0, 1) * 0.06)


def paver():
    pid, u, w = grid_ids(X, Y, N / 8, N / 16, 0.5)
    tone = 0.70 + 0.10 * hash01(pid, 2) + 0.05 * fbm(N, 20, 3, 10)
    edge = np.minimum.reduce([u * (N / 8), (1 - u) * (N / 8), w * (N / 16), (1 - w) * (N / 16)])
    v = tone * light(np.clip(edge / 5, 0, 1), 1.5) * np.where(edge < 2.0, 0.55, 1.0)
    warm = hash01(pid, 5)
    return np.dstack([v * (222 + warm * 18), v * (208 + warm * 10), v * 190])


def grama():
    n1 = fbm(N, 6, 6, 11); n2 = fbm(N, 48, 3, 12); sp = np.random.RandomState(13).rand(N, N)
    g = 0.55 + 0.22 * n1 + 0.14 * n2 + 0.10 * fbm(N, 20, 3, 14) + (sp > 0.9) * 0.07 - (sp < 0.06) * 0.08
    g *= light(n2 * 0.6 + sp * 0.4, 0.9)
    dry = np.clip((fbm(N, 3, 3, 15) - 0.55) * 3, 0, 1)
    return np.dstack([g * (98 + 40 * dry), g * (160 + 6 * dry), g * (68 + 10 * dry)])


def areia():
    n1 = fbm(N, 5, 6, 16); sp = np.random.RandomState(17).rand(N, N)
    rip = np.sin(X * 0.045 + n1 * 14 + Y * 0.01) * 0.5 + 0.5
    v = (0.86 + 0.07 * n1 + (sp > 0.96) * 0.05 - (sp < 0.03) * 0.06) * light(rip * 0.6 + sp * 0.4, 0.6)
    return rgb3((240, 223, 184), v)


def agua():
    n1 = fbm(N, 4, 4, 18); n2 = fbm(N, 32, 3, 19); n3 = fbm(N, 12, 3, 20)
    sh = light(n2 * 0.7 + n3 * 0.3, 3.0)
    base = 0.78 + 0.10 * n1
    spec = np.clip((sh - 1.12) * 3, 0, 1) * 0.35
    return np.dstack([base * 58 * sh + spec * 190, base * 118 * sh + spec * 170, base * 168 * sh + spec * 120])


# ================================================================ paredes
def tijolo():
    bw, bh = N / 8, N / 24
    pid, u, w = grid_ids(X, Y, bw, bh, 0.5)
    t = hash01(pid, 3)
    r = 142 + t * 40 + 18 * fbm(N, 40, 2, 21); g = 66 + t * 16 + 8 * fbm(N, 40, 2, 22); b = 48 + t * 10
    burnt = hash01(pid, 9) > 0.88
    r = np.where(burnt, r * 0.72, r); g = np.where(burnt, g * 0.7, g); b = np.where(burnt, b * 0.75, b)
    edge = np.minimum.reduce([u * bw, (1 - u) * bw, w * bh, (1 - w) * bh])
    mortar = edge < 3.0
    sh = light(np.clip(edge / 4, 0, 1) + 0.15 * fbm(N, 60, 2, 23), 1.6)
    m = 196 + 14 * fbm(N, 30, 2, 24)
    return np.dstack([np.where(mortar, m, r), np.where(mortar, m * 0.97, g), np.where(mortar, m * 0.92, b)]) * sh[..., None]


def siding():
    bh = N / 12
    t = (Y % bh) / bh
    h = t * 0.6 + np.where(t > 0.9, -0.4, 0)
    grain = 0.03 * fbm(N, 6, 4, 25) + 0.015 * np.sin(X * 0.02 + fbm(N, 4, 3, 26) * 8)
    v = (0.93 + grain) * light(h, 1.4) * np.where(t > 0.92, 0.66, 1.0)
    return rgb3((255, 255, 255), v - np.clip((fbm(N, 3, 3, 27) - 0.6) * 2, 0, 1) * 0.05 * (Y / N))


def reboco():
    h = fbm(N, 24, 4, 28) * 0.7 + np.random.RandomState(29).rand(N, N) * 0.3
    v = (0.90 + 0.05 * fbm(N, 6, 4, 30)) * light(h, 0.8)
    streak = np.clip((fbm(N, 2, 3, 31) - 0.55) * 2, 0, 1) * 0.04 * (1 - np.abs(np.sin(X / N * 9.0)))
    return rgb3((255, 255, 255), v - streak)


def telha_shingle():
    rh, tw = N / 14, N / 9
    row = (Y // rh).astype(int); off = hash01(row, 4) * tw
    col = ((X + off) // tw).astype(int); u = ((X + off) % tw) / tw; t = (Y % rh) / rh
    pid = row * 997 + col
    tone = 0.62 + 0.12 * hash01(pid, 6) + 0.06 * fbm(N, 30, 3, 32)
    v = tone * light(t + 0.2 * fbm(N, 50, 2, 33), 1.4) * np.where(t > 0.88, 0.55, 1.0) * np.where(u < 0.012, 0.6, 1.0)
    return rgb3((240, 240, 240), v + np.random.RandomState(34).rand(N, N) * 0.08 - 0.04)


def telha_ceramica():
    cw, rh = N / 8, N / 6
    cx = (X % cw) / cw; cy = (Y % rh) / rh
    pid = (Y // rh).astype(int) * 31 + (X // cw).astype(int)
    hb = np.sin(cx * math.pi) * (0.6 + 0.4 * cy)
    h = hb + np.where(cy > 0.9, -0.5, 0)
    tone = 0.75 + 0.15 * hash01(pid, 7) + 0.05 * fbm(N, 30, 2, 35)
    v = tone * light(h * 3, 0.7) * np.where(cy > 0.9, 0.6, 1.0)
    moss = np.clip((fbm(N, 5, 3, 36) - 0.62) * 3, 0, 1)
    return np.dstack([v * (205 - 60 * moss), v * (98 + 10 * moss), v * (64 - 10 * moss)])


def pedra():
    idx, edge = voronoi(N, 80, 37)
    tone = 0.58 + 0.2 * hash01(idx, 8) + 0.10 * fbm(N, 16, 3, 38)
    v = tone * light(np.clip(edge / 10, 0, 1) + 0.2 * fbm(N, 30, 3, 39), 1.4) * np.where(edge < 3.0, 0.5, 1.0)
    warm = hash01(idx, 11)
    return np.dstack([v * (190 + 20 * warm), v * (182 + 10 * warm), v * 168])


def concreto():
    v = (0.80 + 0.05 * fbm(N, 6, 5, 42)) * light(fbm(N, 20, 4, 40) * 0.5 + np.random.RandomState(41).rand(N, N) * 0.2, 0.7)
    seam = ((Y % (N / 2)) < 3) | ((X % (N / 2)) < 3)
    v = np.where(seam, v * 0.84, v)
    for (px, py) in ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)):
        v = np.where(((X - px * N) ** 2 + (Y - py * N) ** 2) < 60, v * 0.72, v)
    return rgb3((238, 236, 232), v - np.clip((fbm(N, 3, 3, 43) - 0.6) * 3, 0, 1) * 0.07)


def madeira():
    pw = N / 6
    plank = (Y // pw).astype(int); t = (Y % pw) / pw
    grain = 0.035 * np.sin(Y * 0.35 + fbm(N, 3, 3, 44) * 5 + plank * 2.3 + X * 0.004) + 0.02 * np.sin(Y * 0.9 + X * 0.01 + plank) + 0.03 * fbm(N, 64, 2, 45)
    tone = 0.70 + 0.10 * hash01(plank, 12)
    v = (tone + grain) * light(np.where(t < 0.04, 0.0, 1.0) + grain, 0.8) * np.where(t < 0.035, 0.45, 1.0)
    return np.dstack([v * 196, v * 142, v * 96])


def cerca():
    bw = N / 8
    board = (X // bw).astype(int); u = (X % bw) / bw
    v = 0.86 + 0.025 * np.sin(X * 0.35 + board * 1.7 + fbm(N, 3, 3, 46) * 4 + Y * 0.004) + 0.04 * hash01(board, 13) + 0.03 * fbm(N, 64, 2, 76)
    v = v * light(np.where(u < 0.04, 0.0, 1.0) + 0.1 * fbm(N, 40, 2, 47), 0.9) * np.where(u < 0.035, 0.5, 1.0)
    rail = (np.abs(Y - N * 0.18) < 10) | (np.abs(Y - N * 0.82) < 10)
    v = np.where(rail, v * 0.88, v)
    return np.dstack([v * 238, v * 214, v * 182])


def metal():
    v = 0.76 + 0.05 * fbm(N, 4, 4, 48)
    rib = (X % (N / 8)) / (N / 8)
    return rgb3((255, 255, 255), v * light(np.sin(rib * math.pi) * 2, 0.5))


def cascalho():
    idx, edge = voronoi(256, 900, 49)
    idx = np.tile(idx, (4, 4)); edge = np.tile(edge, (4, 4))
    return rgb3((222, 220, 216), (0.55 + 0.3 * hash01(idx, 14)) * light(np.clip(edge / 3, 0, 1), 1.0))


# ================================================================ fachadas
def _window(img, x0, x1, y0, y1, rng_id, frame=(236, 236, 232), lit=0.0, mullion=True, curtain=True):
    m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    gy = (Y - y0) / max(1, (y1 - y0))
    sky = 0.55 + 0.40 * (1 - gy)
    refl = (np.abs(((X - x0) * 0.6 + (Y - y0)) % (x1 - x0 + 1) - (x1 - x0) * 0.4) < (x1 - x0) * 0.08)
    img[m] = np.dstack([sky * 92 + refl * 40, sky * 120 + refl * 40, sky * 146 + refl * 35])[m]
    if curtain:
        cov = 0.15 + 0.5 * float(hash01(rng_id, 21))
        tint = np.array([(236, 228, 210), (210, 222, 230), (230, 214, 200), (190, 196, 204)][int(float(hash01(rng_id, 22)) * 4) % 4], float)
        img[m & (gy < cov)] = tint * 0.85
    fw = max(4, int((x1 - x0) * 0.06))
    fr = m & (((X - x0) < fw) | ((x1 - X) < fw) | ((Y - y0) < fw) | ((y1 - Y) < fw) | (mullion & (np.abs(X - (x0 + x1) / 2) < fw * 0.6)))
    img[fr] = frame
    sh = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y0 + fw * 2.5)
    img[sh & ~fr] *= 0.7
    img[(X >= x0 - fw * 2) & (X < x1 + fw * 2) & (Y >= y1) & (Y < y1 + fw * 1.6)] = (210, 205, 196)
    img[(X >= x0 - fw * 2) & (X < x1 + fw * 2) & (Y >= y1 + fw * 1.6) & (Y < y1 + fw * 3)] *= 0.84


def fachada_janelas():
    """predio residencial: 2 baias de 3 m x 1 andar de 3 m; parede clara tingivel"""
    img = rgb3((255, 255, 255), (0.92 + 0.04 * fbm(N, 10, 4, 50)) * light(fbm(N, 30, 3, 51), 0.5))
    img[Y > N * 0.94] *= 0.9
    for k in range(2):
        _window(img, k * N / 2 + N * 0.10, k * N / 2 + N * 0.40, N * 0.22, N * 0.70, k + 1)
    return img


def fachada_classica():
    """predio antigo de tijolo: janelas altas com arco, cornija (2 baias x 1 andar de 3,6 m)"""
    img = tijolo()
    for k in range(2):
        x0 = k * N / 2 + N * 0.14; x1 = k * N / 2 + N * 0.36
        _window(img, x0, x1, N * 0.18, N * 0.74, 10 + k, frame=(242, 238, 228))
        arch = (Y < N * 0.18) & (Y > N * 0.08) & ((((X - (x0 + x1) / 2) / ((x1 - x0) / 2 + 10)) ** 2 + ((Y - N * 0.18) / (N * 0.09)) ** 2) < 1)
        img[arch] = (226, 214, 196)
        img[arch & (np.abs(X - (x0 + x1) / 2) < 12)] = (200, 190, 172)
    img[Y > N * 0.90] = (228, 220, 204)
    img[(Y > N * 0.90) & (Y < N * 0.915)] = (180, 172, 160)
    return img


def fachada_vidro():
    sky = 0.50 + 0.40 * (1 - Y / N) + 0.10 * fbm(N, 3, 3, 52)
    cloud = np.clip((fbm(N, 4, 4, 53) - 0.5) * 2, 0, 1) * 0.25
    pane = ((X // (N / 2)) % 2) * 0.04
    img = np.dstack([(sky + cloud + pane) * 82, (sky + cloud + pane) * 118, (sky + cloud * 0.8 + pane) * 150 + 18])
    spand = Y > N * 0.80
    img[spand] = np.array([92.0, 104.0, 116.0]) * (0.9 + 0.1 * fbm(N, 8, 2, 54)[spand][:, None])
    img[((X % (N / 2)) < 9) | ((Y % N) < 10) | (np.abs(Y - N * 0.80) < 5)] = (196, 200, 206)
    img[((X % (N / 2)) >= 9) & ((X % (N / 2)) < 14)] *= 0.75
    return img


def fachada_escritorio():
    img = rgb3((240, 238, 232), (0.86 + 0.05 * fbm(N, 8, 3, 55)) * light(fbm(N, 30, 3, 56), 0.5))
    band = (Y > N * 0.16) & (Y < N * 0.70)
    g = 0.55 + 0.4 * (1 - (Y - N * 0.16) / (N * 0.54)) + 0.08 * fbm(N, 3, 2, 57)
    refl = np.abs(((X * 0.5 + Y) % (N * 0.6)) - N * 0.3) < N * 0.04
    img[band] = np.dstack([g * 70 + refl * 30, g * 96 + refl * 30, g * 118 + refl * 25])[band]
    img[band & ((X % (N / 3)) < 7)] = (62, 66, 72)
    img[(Y >= N * 0.70) & (Y < N * 0.72)] *= 0.7
    img[(Y >= N * 0.14) & (Y < N * 0.16)] *= 0.8
    return img


def fachada_moderna():
    img = rgb3((255, 255, 255), 0.94 + 0.03 * fbm(N, 10, 3, 58))
    _window(img, N * 0.06, N * 0.62, N * 0.10, N * 0.86, 30, frame=(60, 62, 66), mullion=False)
    wood = (X >= N * 0.70) & (X < N * 0.96) & (Y >= N * 0.10) & (Y < N * 0.86)
    img[wood] = madeira()[wood]
    img[Y > N * 0.90] = (214, 212, 206)
    return img


def vitrine():
    g = 0.45 + 0.35 * (Y / N) + 0.08 * fbm(N, 4, 2, 59)
    img = np.dstack([g * 62, g * 78, g * 92])
    img[((Y % (N / 4)) < 6) & (Y > N * 0.3)] = (150, 140, 120)
    goods = (Y > N * 0.3) & (fbm(N, 30, 2, 60) > 0.55) & ((Y % (N / 4)) > 12) & ((Y % (N / 4)) < 60)
    gcol = np.dstack([fbm(N, 20, 2, 61) * 255, fbm(N, 20, 2, 62) * 200, fbm(N, 20, 2, 63) * 160])
    img[goods] = img[goods] * 0.4 + gcol[goods] * 0.6
    refl = (np.abs(((X + Y * 0.7) % (N / 2)) - N / 4) < N / 22)
    img[refl] = np.minimum(img[refl] * 1.5 + 30, 255)
    img[((X % (N / 2)) < 12) | (Y < 12) | (Y > N - 60)] = (46, 48, 52)
    return img


def janela_casa():
    img = np.zeros((N, N, 3)) + (242, 242, 238)
    _window(img, 56, N - 56, 56, N - 80, 40, frame=(242, 242, 238))
    gl = (X > 70) & (X < N - 70) & (Y > 70) & (Y < N - 94)
    img[gl & ((np.abs(X - N * 0.25) < 6) | (np.abs(X - N * 0.75) < 6) | (np.abs(Y - N * 0.33) < 6) | (np.abs(Y - N * 0.62) < 6))] = (242, 242, 238)
    return img


def porta():
    img = rgb3((255, 255, 255), 0.82 + 0.04 * fbm(N, 8, 3, 64))
    hh = np.zeros((N, N))
    for (a, b, c, e) in ((0.12, 0.44, 0.06, 0.44), (0.56, 0.88, 0.06, 0.44), (0.12, 0.44, 0.52, 0.94), (0.56, 0.88, 0.52, 0.94)):
        hh[(X > a * N) & (X < b * N) & (Y > c * N) & (Y < e * N)] = 1.0
        hh[(X > a * N + 18) & (X < b * N - 18) & (Y > c * N + 18) & (Y < e * N - 18)] = 0.4
    img *= light(hh * 6, 1.0)[..., None]
    img[((X - 0.90 * N) ** 2 + (Y - 0.52 * N) ** 2) < 300] = (205, 178, 92)
    return img


def garagem():
    t = (Y % (N / 5)) / (N / 5)
    v = (0.88 + 0.03 * fbm(N, 8, 3, 65)) * light(np.where(t < 0.06, 0.0, t), 1.2) * np.where(t < 0.05, 0.62, 1.0)
    return rgb3((255, 255, 255), np.where((X % (N / 4)) < 5, v * 0.9, v))


# ================================================================ natureza
def folhagem():
    idx, edge = voronoi(512, 1400, 66)
    idx = np.tile(idx, (2, 2)); edge = np.tile(edge, (2, 2))
    v = (0.60 + 0.30 * hash01(idx, 15)) * light(np.clip(edge / 6, 0, 1), 1.2) * np.where(edge < 1.2, 0.55, 1.0)
    return rgb3((255, 255, 255), v * (0.85 + 0.15 * fbm(N, 6, 3, 67)))


def casca():
    h = np.sin(X * 0.09 + fbm(N, 4, 3, 69) * 12)
    v = (0.55 + 0.2 * fbm(N, 6, 4, 68) + 0.12 * h) * light(h, 0.4)
    return np.dstack([v * 150, v * 114, v * 84])


def quadra():
    v = 0.86 + 0.04 * fbm(N, 30, 3, 70)
    return np.dstack([v * 72, v * 140, v * 102])


def terreno():
    sp = np.random.RandomState(71).rand(N, N)
    v = (0.80 + 0.10 * fbm(N, 8, 5, 73) + 0.05 * fbm(N, 48, 2, 74) + (sp > 0.94) * 0.04 - (sp < 0.06) * 0.05) * light(fbm(N, 16, 4, 72), 0.6)
    return rgb3((255, 255, 255), v)


def branco():
    return np.full((64, 64, 3), 255.0)


MATS = {
    'asfalto': (asfalto, (8.0, 8.0)), 'calcada': (calcada, (3.0, 3.0)), 'paver': (paver, (2.4, 2.4)), 'grama': (grama, (6.0, 6.0)),
    'areia': (areia, (6.0, 6.0)), 'agua': (agua, (14.0, 14.0)), 'tijolo': (tijolo, (2.4, 2.4)), 'siding': (siding, (2.4, 2.4)),
    'reboco': (reboco, (4.0, 4.0)), 'telha': (telha_shingle, (3.0, 3.0)), 'ceramica': (telha_ceramica, (2.0, 2.0)),
    'vidro': (fachada_vidro, (3.0, 3.6)), 'janelas': (fachada_janelas, (6.0, 3.0)), 'escritorio': (fachada_escritorio, (3.0, 3.6)),
    'classica': (fachada_classica, (6.0, 3.6)), 'moderna': (fachada_moderna, (3.0, 3.0)),
    'vitrine': (vitrine, (3.0, 3.0)), 'madeira': (madeira, (2.0, 2.0)), 'pedra': (pedra, (2.5, 2.5)), 'concreto': (concreto, (3.0, 3.0)),
    'cascalho': (cascalho, (2.0, 2.0)), 'folhagem': (folhagem, (2.0, 2.0)), 'janela': (janela_casa, (1.0, 1.0)), 'porta': (porta, (1.0, 1.0)),
    'garagem': (garagem, (1.0, 1.0)), 'metal': (metal, (2.0, 2.0)), 'casca': (casca, (1.0, 1.0)), 'quadra': (quadra, (4.0, 4.0)),
    'cerca': (cerca, (1.6, 1.8)), 'terreno': (terreno, (8.0, 8.0)), 'liso': (branco, (1.0, 1.0)),
}


def make_all(outdir, only=None):
    os.makedirs(outdir, exist_ok=True)
    for k, (fn, sc) in MATS.items():
        if only and k not in only: continue
        Image.fromarray(np.clip(fn(), 0, 255).astype(np.uint8)).save(os.path.join(outdir, k + '.jpg'), quality=86)
    return outdir


if __name__ == '__main__':
    import sys
    d = make_all(sys.argv[1] if len(sys.argv) > 1 else '/tmp/tex6')
    from PIL import ImageDraw
    ks = list(MATS); cols = 8; s = 200
    sheet = Image.new('RGB', (cols * s, ((len(ks) + cols - 1) // cols) * (s + 18)), 'white')
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(ks):
        sheet.paste(Image.open(os.path.join(d, k + '.jpg')).resize((s, s)), ((i % cols) * s, (i // cols) * (s + 18)))
        dr.text(((i % cols) * s + 4, (i // cols) * (s + 18) + s + 2), k, fill='black')
    sheet.save(os.path.join(d, '_prancha.png'))
    print('ok', len(ks))
