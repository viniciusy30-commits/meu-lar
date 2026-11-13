"""Terreno, agua e mascara urbana (campos de 16 m) - ETAPA A/B v2."""
import math
import numpy as np
from collections import deque
from plan import *

_RS = np.random.RandomState(RNG)
_TAB = [_RS.rand(128, 128) for _ in range(6)]

def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def vnoise(x, z, tab, scale):
    u = x / scale; v = z / scale
    i0 = np.floor(u).astype(int); j0 = np.floor(v).astype(int)
    fu = u - i0; fv = v - j0; fu = fu * fu * (3 - 2 * fu); fv = fv * fv * (3 - 2 * fv)
    n = tab.shape[0]
    a = tab[j0 % n, i0 % n]; b = tab[j0 % n, (i0 + 1) % n]; c = tab[(j0 + 1) % n, i0 % n]; d = tab[(j0 + 1) % n, (i0 + 1) % n]
    return a * (1 - fu) * (1 - fv) + b * fu * (1 - fv) + c * (1 - fu) * fv + d * fu * fv

def fbm(x, z, scale=900.0, octs=5, k0=0):
    s = 0; amp = 0.5; tot = 0
    for o in range(octs):
        s = s + amp * vnoise(x + 311 * o, z + 173 * o, _TAB[(k0 + o) % 6], scale / (2 ** o)); tot += amp; amp *= 0.5
    return s / tot

def seg_dist(X, Z, p, q):
    dx, dz = q[0] - p[0], q[1] - p[1]; L2 = dx * dx + dz * dz
    t = np.clip(((X - p[0]) * dx + (Z - p[1]) * dz) / L2, 0, 1)
    return np.hypot(X - (p[0] + t * dx), Z - (p[1] + t * dz)), t

def poly_dist(X, Z, pts):
    best = None; bt = None
    for k in range(len(pts) - 1):
        d, t = seg_dist(X, Z, pts[k], pts[k + 1])
        if best is None: best = d; bt = np.full(d.shape, float(k)) + t
        else:
            m = d < best; best = np.where(m, d, best); bt = np.where(m, k + t, bt)
    return best, bt

def carve(h, d, half, depth, bank, reach=330.0):
    inside = d < half
    hc = np.where(inside, -depth * (1 - (d / half) ** 2), bank * (d - half))
    w = smooth(half + reach * 0.45, half + reach, d)          # longe do canal o relevo original volta
    return np.minimum(h, hc) * (1 - w) + h * w

def build():
    xs = np.arange(NX) * CELL; zs = np.arange(NZ) * CELL
    X, Z = np.meshgrid(xs, zs)
    # bacia urbana e montanhas
    ex = (X - BASIN_C[0]) / BASIN_R[0]; ez = (Z - BASIN_C[1]) / BASIN_R[1]
    ang = np.arctan2(ez, ex)
    wob = fbm(np.cos(ang) * 700 + 2000, np.sin(ang) * 700 + 2000, 520.0, 4, 1)
    rho = np.hypot(ex, ez) * (1.0 + 0.62 * (wob - 0.5))
    f1 = fbm(X, Z, 800.0, 5, 2); rid = (1.0 - np.abs(2 * fbm(X, Z, 520.0, 5, 3) - 1)) ** 2
    mount = 330.0 * smooth(0.88, 1.55, rho) * (0.15 + 0.7 * f1 + 1.1 * rid) + 40.0 * smooth(0.75, 1.0, rho)
    ridge = 70.0 * smooth(1.0, 1.5, rho) * (fbm(X, Z, 140.0, 4, 3) - 0.5)
    h = 4.0 + 7.0 * (fbm(X, Z, 420.0, 4, 4) - 0.5) * smooth(1.25, 0.5, rho) + mount + ridge
    for hx, hz, hh, hs in HILLS:
        h = h + hh * np.exp(-((X - hx) ** 2 + (Z - hz) ** 2) / (2 * hs * hs))
    # centro plano
    flat = smooth(520.0, 240.0, np.hypot(X - 2000.0, Z - 1800.0))
    h = h * (1 - 0.92 * flat) + 4.5 * 0.92 * flat
    # costa: praia e mar
    cz = np.vectorize(coast)(X[0])[None, :] * np.ones_like(X)
    dz = cz - Z                                           # >0 em terra
    beach = np.minimum(h, 1.6 + np.maximum(dz, 0) * 0.014)
    h = np.where(dz > -1e9, np.where(dz > 0, np.minimum(h, np.where(dz < 260, beach + (dz / 260.0) ** 2 * 60, h)), -0.6 + dz * 0.045), h)
    h = np.where(dz < 0, np.maximum(-0.6 + dz * 0.045, -45.0), h)
    # canais, rio, lagoa
    for ch in (CHANNEL_W, CHANNEL_E):
        d, _ = poly_dist(X, Z, ch['pts']); w = ch['w'] * (1 + 0.12 * (fbm(X, Z, 380, 2, 5) - 0.5)) / 2
        h = carve(h, d, w, 22.0, 0.45)
    d, t = poly_dist(X, Z, RIVER['pts']); half = (RIVER['w0'] + (RIVER['w1'] - RIVER['w0']) * np.clip(t / (len(RIVER['pts']) - 1), 0, 1) ** 1.5) / 2
    h = carve(h, d, half, 4.0, 0.22)
    lx, lz, rx, rz = LAGOON
    e = np.hypot((X - lx) / rx, (Z - lz) / rz) * (1 + 0.07 * (fbm(X, Z, 120, 2, 1) - 0.5))
    h = np.minimum(h, np.where(e < 1.6, 3.2 * (e - 1.0) * (rx / 150.0) - (e < 1.0) * 0.5, 1e9))
    for cx0, cz0, crx, crz in COVES:        # enseadas que entram na cidade (marina, foz, cove norte)
        e2 = np.hypot((X - cx0) / crx, (Z - cz0) / crz) * (1 + 0.12 * (fbm(X, Z, 200, 2, 2) - 0.5))
        h = np.minimum(h, np.where(e2 < 1.5, 5.0 * (e2 - 1.0) * (crx / 150.0), 1e9))
    water = h < 0.0
    # inclinacao
    gz, gx = np.gradient(h, CELL)
    slope = np.hypot(gx, gz)
    # mascara urbana: terra baixa e suave, ligada ao centro
    cand = (h > 0.55) & (h < 150.0) & (slope < 0.34) & (rho < 1.12)
    # afasta 1 celula da agua
    wd = water.copy()
    for _ in range(1):
        wd = wd | np.roll(wd, 1, 0) | np.roll(wd, -1, 0) | np.roll(wd, 1, 1) | np.roll(wd, -1, 1)
    cand &= ~wd
    lab = np.zeros(cand.shape, np.int32); n = 0; sizes = {}
    for j0 in range(NZ):
        for i0 in range(NX):
            if cand[j0, i0] and lab[j0, i0] == 0:
                n += 1; lab[j0, i0] = n; dq = deque([(j0, i0)]); c = 1
                while dq:
                    j, i = dq.popleft()
                    for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        a, b = j + dj, i + di
                        if 0 <= a < NZ and 0 <= b < NX and cand[a, b] and lab[a, b] == 0:
                            lab[a, b] = n; dq.append((a, b)); c += 1
                sizes[n] = c
    keep = [k for k, v in sizes.items() if v >= 900]
    urban = np.isin(lab, keep)
    for _ in range(2):   # abre/fecha para tirar espinhos
        m = urban.astype(np.int16)
        n = sum(np.roll(np.roll(m, dj, 0), di, 1) for dj in (-1, 0, 1) for di in (-1, 0, 1))
        urban = n >= 5
    return {'X': X, 'Z': Z, 'h': h, 'water': water, 'slope': slope, 'urban': urban, 'rho': rho}

class Geo:
    def __init__(self):
        g = build(); self.__dict__.update(g)
    def idx(self, x, z):
        return min(max(int(round(z / CELL)), 0), NZ - 1), min(max(int(round(x / CELL)), 0), NX - 1)
    def height(self, x, z):
        fx = min(max(x / CELL, 0), NX - 1.001); fz = min(max(z / CELL, 0), NZ - 1.001)
        i, j = int(fx), int(fz); a, b = fx - i, fz - j; H = self.h
        return (H[j, i] * (1 - a) + H[j, i + 1] * a) * (1 - b) + (H[j + 1, i] * (1 - a) + H[j + 1, i + 1] * a) * b
    def is_urban(self, x, z):
        j, i = self.idx(x, z); return bool(self.urban[j, i])
    def is_water(self, x, z):
        j, i = self.idx(x, z); return bool(self.water[j, i])
    def slope_at(self, x, z):
        j, i = self.idx(x, z); return float(self.slope[j, i])
