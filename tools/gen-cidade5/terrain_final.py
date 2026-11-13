"""ETAPA B: heightmap final (8 m), perfil de altura de cada rua (declive limitado) e terraplenagem (corte/aterro)."""
import math, struct
import numpy as np
from plan import *
import geo as G

STEP = 8.0
N8X, N8Z = int(WX / STEP) + 1, int(WZ / STEP) + 1
GRADE = {0: 0.065, 1: 0.075, 2: 0.095}        # declive maximo final por nivel (ave/col/loc)
HALF = {0: 14.0, 1: 10.0, 2: 7.5}

def upsample(geo):
    xs = np.arange(N8X) * STEP / CELL; zs = np.arange(N8Z) * STEP / CELL
    xs = np.clip(xs, 0, NX - 1.0001); zs = np.clip(zs, 0, NZ - 1.0001)
    i0 = xs.astype(int); j0 = zs.astype(int); fx = xs - i0; fz = zs - j0
    H = geo.h
    a = H[np.ix_(j0, i0)]; b = H[np.ix_(j0, i0 + 1)]; c = H[np.ix_(j0 + 1, i0)]; d = H[np.ix_(j0 + 1, i0 + 1)]
    FX, FZ = fx[None, :], fz[:, None]
    h = (a * (1 - FX) + b * FX) * (1 - FZ) + (c * (1 - FX) + d * FX) * FZ
    X, Z = np.meshgrid(np.arange(N8X) * STEP, np.arange(N8Z) * STEP)
    # detalhe fino so em terra e fora do centro plano (a terraplenagem das ruas sobrescreve onde houver rua)
    land = h > 1.0
    det = (G.fbm(X, Z, 70.0, 3, 5) - 0.5) * 1.6 * np.clip(h / 30.0, 0.15, 1.0)
    return np.where(land, h + det, h), X, Z

def elen(p): return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(p, p[1:]))

def node_profile(city, geo, iters=900):
    """altura de cada no = terreno, depois relaxa ate todas as ruas respeitarem o declive maximo"""
    y = [geo.height(n[0], n[1]) for n in city.nodes]
    y = [max(v, 1.2) for v in y]                              # nunca abaixo do nivel do mar + calcada
    E = [(e['a'], e['b'], max(elen(e['p']) - e.get('_ca', 0) - e.get('_cb', 0), 0.3 * elen(e['p'])), GRADE.get(e['lvl'], 0.065) if e['kind'] != 'bridge' else 0.07) for e in city.edges]
    for it in range(iters):
        worst = 0.0
        for a, b, L, lim in E:
            dh = y[b] - y[a]; allow = lim * L
            if abs(dh) > allow:
                ex = (abs(dh) - allow) / 2.0 * 0.9; s = 1 if dh > 0 else -1
                y[a] += s * ex; y[b] -= s * ex; worst = max(worst, abs(dh) / L)
        if worst <= max(GRADE.values()) * 1.001 and it > 5: break
    return y

def profile_pts(e, ya, yb):
    """perfil de altura da rua: PLATO plano junto a cada cruzamento (cruzamentos planos) e rampa linear no meio"""
    pts = e['p']; Ls = [0.0]
    for a, b in zip(pts, pts[1:]): Ls.append(Ls[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    T = Ls[-1] or 1.0
    ca = min(e.get('_ca', 0.0), T * 0.45); cb = min(e.get('_cb', 0.0), T * 0.45)
    def y(s):
        if s <= ca: return ya
        if s >= T - cb: return yb
        return ya + (yb - ya) * (s - ca) / max(T - ca - cb, 1e-6)
    return [(p[0], p[1], y(s)) for p, s in zip(pts, Ls)]

def carve(h, X, Z, city, ynode):
    h0 = h.copy(); acc_y = np.zeros_like(h); acc_w = np.zeros_like(h)
    # rotatorias: disco plano (anel + calcada) na altura do no
    for rd in city.rounds:
        y = ynode[rd['node']]; R = rd['r'] + 3.0
        i0, i1 = int((rd['x'] - R - 14) / STEP), int((rd['x'] + R + 14) / STEP) + 1; j0, j1 = int((rd['z'] - R - 14) / STEP), int((rd['z'] + R + 14) / STEP) + 1
        i0, j0 = max(i0, 0), max(j0, 0); i1, j1 = min(i1, N8X), min(j1, N8Z)
        d = np.hypot(X[j0:j1, i0:i1] - rd['x'], Z[j0:j1, i0:i1] - rd['z'])
        w = np.clip(1.0 - np.clip(d - R, 0, None) / 14.0, 0, 1); w = w * w * (3 - 2 * w); w = np.where(d <= R, 1.0, w)
        sub_w = acc_w[j0:j1, i0:i1]; sub_y = acc_y[j0:j1, i0:i1]; better = (w >= sub_w) & (w > 0)
        sub_y[better] = y; sub_w[better] = w[better]
    order = sorted(range(len(city.edges)), key=lambda k: -city.edges[k]['lvl'])    # ave por ultimo => prevalece
    for k in order:
        e = city.edges[k]
        if e['kind'] in ('bridge', 'redbridge'): continue
        half = HALF.get(e['lvl'], 7.5)
        pp = profile_pts(e, ynode[e['a']], ynode[e['b']])
        # amostras a cada ~4 m
        smp = []
        for (ax, az, ay), (bx, bz, by) in zip(pp, pp[1:]):
            L = math.hypot(bx - ax, bz - az); n = max(1, int(L / 4))
            for t in range(n): smp.append((ax + (bx - ax) * t / n, az + (bz - az) * t / n, ay + (by - ay) * t / n))
        smp.append(pp[-1])
        for (x, z, y) in smp:
            i = int(round(x / STEP)); j = int(round(z / STEP))
            if not (0 <= i < N8X and 0 <= j < N8Z): continue
            dh = abs(h0[j, i] - y); sh = min(34.0, max(7.0, 2.2 * dh))
            R = half + sh; r = int(R / STEP) + 1
            j0, j1, i0, i1 = max(j - r, 0), min(j + r + 1, N8Z), max(i - r, 0), min(i + r + 1, N8X)
            d = np.hypot(X[j0:j1, i0:i1] - x, Z[j0:j1, i0:i1] - z)
            w = np.clip(1.0 - np.clip(d - half, 0, None) / sh, 0, 1); w = w * w * (3 - 2 * w)
            w = np.where(d <= half, 1.0, w)
            m = w > 0
            sub_w = acc_w[j0:j1, i0:i1]; sub_y = acc_y[j0:j1, i0:i1]
            better = (w >= sub_w) & (w > 0)
            sub_y[better] = (y * w)[better] / np.maximum(w[better], 1e-6) * 0 + y        # a rua mais "perto" decide a altura
            sub_w[better] = w[better]
    wgt = np.clip(acc_w, 0, 1)
    return np.where(wgt > 0, h0 * (1 - wgt) + np.where(acc_w > 0, acc_y, h0) * wgt, h0)

def set_plateaus(city, geo):
    import ground
    cuts = ground.compute_all_cuts(city, geo)
    for k, e in enumerate(city.edges):
        e['_ca'] = cuts.get((k, 'a'), 0.0); e['_cb'] = cuts.get((k, 'b'), 0.0)

def write_bin(h, path):
    cm = np.clip(np.round(h * 100.0), -32000, 32000).astype('<i2')
    with open(path, 'wb') as f:
        f.write(struct.pack('<iif', N8X, N8Z, STEP)); f.write(cm.tobytes())

def run(city, geo):
    set_plateaus(city, geo)
    h, X, Z = upsample(geo)
    ynode = node_profile(city, geo)
    hf = carve(h, X, Z, city, ynode)
    return hf, ynode, X, Z

def sample8(h, x, z):
    fx = min(max(x / STEP, 0), N8X - 1.001); fz = min(max(z / STEP, 0), N8Z - 1.001)
    i, j = int(fx), int(fz); a, b = fx - i, fz - j
    return (h[j, i] * (1 - a) + h[j, i + 1] * a) * (1 - b) + (h[j + 1, i] * (1 - a) + h[j + 1, i + 1] * a) * b
