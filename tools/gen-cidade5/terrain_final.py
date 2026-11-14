"""ETAPA B: heightmap final (8 m), perfil de altura de cada rua (declive limitado) e terraplenagem (corte/aterro)."""
import math, struct
import numpy as np
from plan import *
import geo as G

STEP = 8.0
N8X, N8Z = int(WX / STEP) + 1, int(WZ / STEP) + 1
GRADE = {0: 0.065, 1: 0.075, 2: 0.095}        # declive maximo final por nivel (ave/col/loc)
HALF = {0: 15.8, 1: 10.0, 2: 7.5}

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
    bz = geo.beach_zone[np.ix_(np.clip(np.round(zs).astype(int), 0, NZ - 1), np.clip(np.round(xs).astype(int), 0, NX - 1))]
    det = np.where(bz, 0.0, det)
    h = np.where(land, h + det, h)
    # linha d'agua da praia SUAVE: perfil da areia/mar pela costa analitica (a mascara de 16 m deixava a beira em degraus)
    jj = np.clip(np.round(zs).astype(int), 0, NZ - 1)[:, None]; ii = np.clip(np.round(xs).astype(int), 0, NX - 1)[None, :]
    sea8 = geo.sea[jj, ii]; bz8 = geo.beach_zone[jj, ii]
    dz8 = np.vectorize(coast)(X[0])[None, :] - Z
    m = (X > 820) & (X < 3640) & (bz8 | sea8) & (dz8 > -140) & (dz8 < 56)
    prof = np.where(dz8 > 0, np.interp(dz8, [0, 56, 61], [0.15, 0.98, 1.15]), np.maximum(-0.6 + dz8 * 0.045, -45.0))
    h = np.where(m, prof, h)
    return h, X, Z

def elen(p): return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(p, p[1:]))

def node_profile(city, geo, iters=900):
    """altura de cada no = terreno, depois relaxa ate todas as ruas respeitarem o declive maximo"""
    y = [geo.height(n[0], n[1]) for n in city.nodes]
    y = [max(v, 1.2) for v in y]                              # nunca abaixo do nivel do mar + calcada
    E = []
    for e in city.edges:
        T_ = elen(e['p']); Le = T_ - e.get('_ca', 0) - e.get('_cb', 0); lim = GRADE.get(e['lvl'], 0.065) if e['kind'] != 'bridge' else 0.07
        if e['kind'] != 'bridge' and Le < 0.1 * T_: Le, lim = 1.0, 0.10        # plato de um no encosta no do outro: quase mesma altura (degrau <= 10 cm)
        else: Le = max(Le, 0.3 * T_)
        E.append((e['a'], e['b'], Le, lim))
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
    """perfil de altura da rua: PLATO plano junto a cada cruzamento (cruzamentos planos) e rampa linear no meio.
    IMPORTANTE: os pontos de quebra do plato (s=ca e s=T-cb) viram vertices da polilinha; sem isso a altura era
    interpolada entre os vertices originais (as vezes a dezenas de metros) e a rua nao encontrava o cruzamento (degraus de ate 1,5 m)."""
    pts = e['p']; Ls = [0.0]
    for a, b in zip(pts, pts[1:]): Ls.append(Ls[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    T = Ls[-1] or 1.0
    ca = e.get('_ca', 0.0); cb = e.get('_cb', 0.0)
    if ca + cb > T - 0.6: k_ = (T - 0.6) / max(ca + cb, 1e-6); ca *= k_; cb *= k_
    def y(s):
        if s <= ca: return ya
        if s >= T - cb: return yb
        return ya + (yb - ya) * (s - ca) / max(T - ca - cb, 1e-6)
    def at(s):
        for i in range(len(Ls) - 1):
            if Ls[i + 1] >= s or i == len(Ls) - 2:
                f = (s - Ls[i]) / max(Ls[i + 1] - Ls[i], 1e-9); f = min(max(f, 0.0), 1.0)
                return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f)
    extra = [q for q in (ca, T - cb) if 0.5 < q < T - 0.5]
    # tambem um vertice de ~14 m em 14 m nos trechos longos da rampa (declive uniforme e terreno acompanhando)
    allS = sorted(set([round(v, 4) for v in Ls] + [round(v, 4) for v in extra]))
    out = []
    for sv in allS:
        if out and sv - out[-1][3] < 0.05: continue
        if sv in Ls: p = pts[Ls.index(sv)] if sv in Ls else at(sv)
        else: p = at(sv)
        out.append((p[0], p[1], y(sv), sv))
    return [(p[0], p[1], p[2]) for p in out]

FLAT_EXTRA = 4.0      # terreno plano alem da borda da calcada (a grade de 8 m nao "morde" a borda)

def carve(h, X, Z, city, ynode, geo=None):
    """terraplenagem: cada vertice da grade de 8 m recebe a altura da rua MAIS PROXIMA no ponto projetado
    (nao a do ultimo ponto amostrado), plano ate HALF+FLAT_EXTRA e talude suave depois."""
    h0 = h.copy()
    acc_w = np.zeros_like(h); acc_d = np.full_like(h, 1e9); acc_y = np.zeros_like(h)
    def put(j0, j1, i0, i1, w, d, y):
        sw = acc_w[j0:j1, i0:i1]; sd = acc_d[j0:j1, i0:i1]; sy = acc_y[j0:j1, i0:i1]
        better = (w > sw + 1e-6) | ((np.abs(w - sw) <= 1e-6) & (d < sd) & (w > 0))
        sw[better] = w[better]; sd[better] = d[better]; sy[better] = y[better] if np.ndim(y) else y
    def smooth(w): return w * w * (3 - 2 * w)
    for rd in city.rounds:
        y = ynode[rd['node']]; R = rd['r'] + 3.0 + FLAT_EXTRA; SH = 14.0
        i0, i1 = max(int((rd['x'] - R - SH) / STEP), 0), min(int((rd['x'] + R + SH) / STEP) + 2, N8X)
        j0, j1 = max(int((rd['z'] - R - SH) / STEP), 0), min(int((rd['z'] + R + SH) / STEP) + 2, N8Z)
        d = np.hypot(X[j0:j1, i0:i1] - rd['x'], Z[j0:j1, i0:i1] - rd['z'])
        w = np.where(d <= R, 1.0, smooth(np.clip(1.0 - (d - R) / SH, 0, 1)))
        put(j0, j1, i0, i1, w, np.maximum(d - R, 0), np.full_like(d, y))
    for k, e in enumerate(city.edges):
        if e['kind'] in ('bridge', 'redbridge'): continue
        flat = HALF.get(e['lvl'], 7.5) + FLAT_EXTRA
        beach = geo is not None and e.get('name') == 'Av. Beira-Mar'
        pp = profile_pts(e, ynode[e['a']], ynode[e['b']])
        for (ax, az, ay), (bx, bz, by) in zip(pp, pp[1:]):
            vx, vz = bx - ax, bz - az; L2 = vx * vx + vz * vz
            if L2 < 1e-6: continue
            if beach:
                # lado do mar: plano ate a borda do calcadao (ORLA_CALC + HALF_W da orla) e depois a areia
                L_ = math.sqrt(L2); nxs, nzs = -vz / L_, vx / L_; mx, mz = (ax + bx) / 2, (az + bz) / 2
                sp = geo.Dsea[geo.idx(mx + nxs * 25, mz + nzs * 25)] < geo.Dsea[geo.idx(mx - nxs * 25, mz - nzs * 25)]
                sgn = 1.0 if sp else -1.0
                fs = ORLA_CALC + 7.0 + 0.6
            M = flat + 72.0
            i0, i1 = max(int((min(ax, bx) - M) / STEP), 0), min(int((max(ax, bx) + M) / STEP) + 2, N8X)
            j0, j1 = max(int((min(az, bz) - M) / STEP), 0), min(int((max(az, bz) + M) / STEP) + 2, N8Z)
            if i1 <= i0 or j1 <= j0: continue
            XX = X[j0:j1, i0:i1]; ZZ = Z[j0:j1, i0:i1]
            t = np.clip(((XX - ax) * vx + (ZZ - az) * vz) / L2, 0, 1)
            d = np.hypot(XX - (ax + vx * t), ZZ - (az + vz * t))
            y = ay + (by - ay) * t
            dh = np.abs(h0[j0:j1, i0:i1] - y); sh = np.clip(3.6 * dh, 10.0, 70.0)
            if beach:
                side = ((XX - ax) * nxs + (ZZ - az) * nzs) * sgn > 0                 # True = lado do mar
                fl = np.where(side, fs, flat); sh = np.where(side, 3.0, sh)
                w = np.where(d <= fl, 1.0, smooth(np.clip(1.0 - (d - fl) / sh, 0, 1)))
                # debaixo das vagas/jardim/calcadao (lajes da orla) o terreno fica no nivel da areia: o pe do muro e areia, nao grama
                y = np.where(side & (d > 13.0), np.minimum(y, 1.05), y)
            else:
                w = np.where(d <= flat, 1.0, smooth(np.clip(1.0 - (d - flat) / sh, 0, 1)))
            put(j0, j1, i0, i1, w, d, y)
    wgt = np.clip(acc_w, 0, 1)
    return np.where(wgt > 0, h0 * (1 - wgt) + acc_y * wgt, h0)

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
    hf = carve(h, X, Z, city, ynode, geo)
    # faixa de areia (entre o mar e o muro do calcadao): nunca acima de 1,2 m (senao o jogo pinta grama na praia)
    ii = np.clip(np.round(X / CELL).astype(int), 0, NX - 1); jj = np.clip(np.round(Z / CELL).astype(int), 0, NZ - 1)
    sand = geo.beach_zone[jj, ii] & (geo.Dsea[jj, ii] < 58.0) & ~geo.water[jj, ii]
    hf = np.where(sand & (hf > 1.2), 1.2, hf)
    return hf, ynode, X, Z

def sample8(h, x, z):
    fx = min(max(x / STEP, 0), N8X - 1.001); fz = min(max(z / STEP, 0), N8Z - 1.001)
    i, j = int(fx), int(fz); a, b = fx - i, fz - j
    return (h[j, i] * (1 - a) + h[j, i + 1] * a) * (1 - b) + (h[j + 1, i] * (1 - a) + h[j + 1, i + 1] * a) * b
