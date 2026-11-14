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


ORLA_END_Y = 2.55    # nivel do terreno nas pontas da orla (calcadao 2,4 / praca 2,61)
LOT_SLOPE_MAX = 0.20   # lotes comuns acima disso nao recebem construcao (ficam naturais)
YB_RIVER = 1.25     # banco (terraco) do calcadao ribeirinho: 1,45 m acima do espelho d'agua (-0.2)

def _chamfer8(src):
    nz_, nx_ = src.shape; D = np.where(src, 0.0, 1e9); r2 = STEP * 1.41421356
    for j in range(nz_):
        Dj = D[j]; Dp = D[j - 1] if j > 0 else None
        for i in range(nx_):
            v = Dj[i]
            if v == 0: continue
            if i > 0: v = min(v, Dj[i - 1] + STEP)
            if Dp is not None:
                v = min(v, Dp[i] + STEP)
                if i > 0: v = min(v, Dp[i - 1] + r2)
                if i < nx_ - 1: v = min(v, Dp[i + 1] + r2)
            Dj[i] = v
    for j in range(nz_ - 1, -1, -1):
        Dj = D[j]; Dn = D[j + 1] if j < nz_ - 1 else None
        for i in range(nx_ - 1, -1, -1):
            v = Dj[i]
            if v == 0: continue
            if i < nx_ - 1: v = min(v, Dj[i + 1] + STEP)
            if Dn is not None:
                v = min(v, Dn[i] + STEP)
                if i < nx_ - 1: v = min(v, Dn[i + 1] + r2)
                if i > 0: v = min(v, Dn[i - 1] + r2)
            Dj[i] = v
    return D


def river_terrace(h0, X, Z, city):
    """Etapa E0: nas margens do rio urbano o terreno vira um banco plano (terraco) de 15 m ao longo da agua, para o calcadao ribeirinho; depois sobe em talude suave"""
    smooth = lambda w: w * w * (3 - 2 * w)
    Dr, _ = G.poly_dist(X, Z, RIVER['pts'])
    water = h0 < -0.2
    src = water & (Dr < 200) & (Z > 520) & (Z < 2620)
    if not src.any(): return None
    D = _chamfer8(src)
    zone = (Z > 600) & (Z < 2540)
    fz = smooth(np.clip((Z - 600) / 70.0, 0, 1)) * smooth(np.clip((2540 - Z) / 80.0, 0, 1))
    fac = np.ones_like(h0)
    for e in city.edges:
        if e['kind'] != 'bridge': continue
        P = e['p']
        for a, b in zip(P, P[1:]):
            d, _ = G.seg_dist(X, Z, a, b)
            fac = np.minimum(fac, smooth(np.clip((d - 34.0) / 40.0, 0, 1)))
    dh = np.abs(h0 - YB_RIVER); sh = np.clip(4.0 * dh, 12.0, 70.0)
    FL = 15.0
    w = np.where(D <= FL, 1.0, smooth(np.clip(1.0 - (D - FL) / sh, 0, 1))) * (~water) * zone * fz * fac
    out = [(w, 500.0 + D, np.full_like(h0, YB_RIVER))]
    # lagoa (Praca da Lagoa): banco baixo (0,95 m) de 14 m em volta da agua
    lx, lz, rx, rz = LAGOON
    ell = np.hypot((X - lx) / (rx + 60), (Z - lz) / (rz + 60)) < 1.0
    srcl = water & ell
    if srcl.any():
        Dl = _chamfer8(srcl); YL = 0.95
        shl = np.clip(4.0 * np.abs(h0 - YL), 12.0, 40.0)
        wl = np.where(Dl <= FL, 1.0, smooth(np.clip(1.0 - (Dl - FL) / shl, 0, 1))) * (~water) * ell
        out.append((wl, 500.0 + Dl, np.full_like(h0, YL)))
    return out

def carve(h, X, Z, city, ynode, geo=None, plateaus=()):
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
    # plats dos LOTES COMUNS (Etapa E): cada lote com declive <= 14 % e nivelado na altura da rua (+12 cm); talude 1:3 no maximo em volta; os mais inclinados ficam naturais (jardim/mata)
    if geo is not None and getattr(city, 'lotplan', None) is not None:
        import lots as _lots2
        for l in city.lotplan.lots:
            if l['slope'] > LOT_SLOPE_MAX: continue
            a_, b_, c_, d_ = l['rect']; w_ = math.hypot(b_[0] - a_[0], b_[1] - a_[1]); dd_ = math.hypot(d_[0] - a_[0], d_[1] - a_[1])
            pl = {'cx': (a_[0] + c_[0]) / 2, 'cz': (a_[1] + c_[1]) / 2, 'tx': (b_[0] - a_[0]) / w_, 'tz': (b_[1] - a_[1]) / w_, 'hw': w_ / 2, 'hd': dd_ / 2}
            R_ = max(w_, dd_) / 2 + 22
            i0, i1 = max(int((pl['cx'] - R_) / STEP), 0), min(int((pl['cx'] + R_) / STEP) + 2, N8X); j0, j1 = max(int((pl['cz'] - R_) / STEP), 0), min(int((pl['cz'] + R_) / STEP) + 2, N8Z)
            if i1 <= i0 or j1 <= j0: continue
            dd2 = _lots2.plateau_weight(X[j0:j1, i0:i1], Z[j0:j1, i0:i1], pl)
            yl = l['y'] + 0.12
            sh2 = np.clip(3.0 * np.abs(h0[j0:j1, i0:i1] - yl), 5.0, 18.0)
            w2 = np.where(dd2 <= 0.5, 1.0, smooth(np.clip(1.0 - (dd2 - 0.5) / sh2, 0, 1)))
            put(j0, j1, i0, i1, w2, 520.0 + dd2, np.full_like(dd2, yl))
    if geo is not None:
        for rt in (river_terrace(h0, X, Z, city) or []): put(0, N8Z, 0, N8X, rt[0], rt[1], rt[2])
    # margem natural rochosa: nas margens que nao sao praia, rio urbano, lagoa nem pontas da orla o terreno ganha um barranco (berma) de ~3 m junto da agua:
    # inclinacao forte (o app pinta de rocha) e barreira visual — ninguem entra na agua de bobeira e nenhuma margem e so grama descendo para o mar
    if geo is not None:
        water_ = h0 < -0.2
        Dn = _chamfer8(water_)
        Dr_, _t = G.poly_dist(X, Z, RIVER['pts'])
        lx_, lz_, rx_, rz_ = LAGOON
        ell_ = np.hypot((X - lx_) / (rx_ + 70), (Z - lz_) / (rz_ + 70)) < 1.0
        ii_ = np.clip(np.round(X / CELL).astype(int), 0, NX - 1); jj_ = np.clip(np.round(Z / CELL).astype(int), 0, NZ - 1)
        beach_ = geo.beach_zone[jj_, ii_] & (geo.Dsea[jj_, ii_] < 110.0)
        urb_river = (Dr_ < 230) & (Z > 520) & (Z < 2700)
        inside = (X > 700) & (X < 3700)
        cnt0 = {}
        for e_ in city.edges:
            if e_.get('name') == 'Av. Beira-Mar':
                for q_ in (e_['a'], e_['b']): cnt0[q_] = cnt0.get(q_, 0) + 1
        qends = [(city.nodes[q_][0], city.nodes[q_][1] + 34.0) for q_, c_ in cnt0.items() if c_ == 1 and (city.nodes[q_][0] < 1500 or city.nodes[q_][0] > 3000)]
        near_q = np.zeros_like(water_)
        for (ex_, ez_) in qends: near_q |= np.hypot(X - ex_, Z - ez_) < 640.0
        nat = (~water_) & inside & (~beach_) & (~ell_) & (~urb_river) & (Z < 2880) & (~near_q)
        bump = 3.0 * smooth(np.clip(Dn / 10.0, 0, 1)) * (1.0 - smooth(np.clip((Dn - 14.0) / 22.0, 0, 1)))
        wn = np.where(nat & (Dn > 0) & (Dn < 40), 1.0, 0.0)
        put(0, N8Z, 0, N8X, wn, 600.0 + Dn, h0 + bump)
        # CAIS das pontas: 560 m de margem (canal + mar) em volta de cada ponta da orla viram terraco plano ao nivel da praca (2,55 m), para o cais de pedra e o calcadao
        for (ex_, ez_) in qends:
            dd = np.hypot(X - ex_, Z - ez_)
            near = dd < 560.0
            src = water_ & near
            if not src.any(): continue
            Dq = _chamfer8(src)
            fade = smooth(np.clip((560.0 - dd) / 90.0, 0, 1))
            shq = np.clip(4.0 * np.abs(h0 - ORLA_END_Y), 14.0, 60.0)
            sand_q = geo.beach_zone[jj_, ii_] & (geo.Dsea[jj_, ii_] < 66.0) & (h0 < 1.6)
            wq = np.where(Dq <= 18.0, 1.0, smooth(np.clip(1.0 - (Dq - 18.0) / shq, 0, 1))) * (~water_) * (~sand_q) * fade * near
            put(0, N8Z, 0, N8X, wq, 520.0 + Dq, np.full_like(h0, ORLA_END_Y))
    # FUNDO RASO junto das margens tratadas (cais das pontas, rio urbano, lagoa): a agua ganha uma plataforma rasa de ~6 % de declive em vez de despencar do chao,
    # entao o app mostra o degrade turquesa da agua rasa e a agua deixa de parecer 'colada' no chao
    if geo is not None:
        wat = h0 < -0.2
        zones = np.zeros_like(wat)
        for (ex_, ez_) in qends: zones |= np.hypot(X - ex_, Z - ez_) < 600.0
        Dr2, _t2 = G.poly_dist(X, Z, RIVER['pts']); zones |= (Dr2 < 230) & (Z > 520) & (Z < 2560)
        zones |= np.hypot((X - lx_) / (rx_ + 90), (Z - lz_) / (rz_ + 90)) < 1.0
        if zones.any():
            Dl = _chamfer8(~wat)                                   # distancia da agua ate a terra
            shelf = -(0.30 + 0.07 * Dl)
            wsh = np.where(wat & zones & (shelf > h0), smooth(np.clip((130.0 - Dl) / 60.0, 0, 1)), 0.0)
            put(0, N8Z, 0, N8X, wsh, 430.0 + Dl, shelf)
    # RELEVO das pontas: o campo plano em volta da praca ganha colinas suaves (ate ~3,5 m) a partir de 90 m da praca (o parque fica plano), com os morros mais altos para o lado da terra
    if geo is not None:
        for (ex_, ez_) in qends:
            dd = np.hypot(X - ex_, Z - ez_)
            near_ = (dd > 80.0) & (dd < 330.0)
            fb = (G.fbm(X, Z, 150.0, 3, 1) - 0.5) * 2.0 + 0.35 * (G.fbm(X, Z, 60.0, 2, 3) - 0.5) * 2.0
            fall = smooth(np.clip((dd - 80.0) / 70.0, 0, 1)) * (1.0 - smooth(np.clip((dd - 240.0) / 90.0, 0, 1)))
            Dw = _chamfer8(h0 < -0.2)
            keep_water = smooth(np.clip((Dw - 26.0) / 30.0, 0, 1))                    # junto da agua o cais manda; o relevo so comeca a 26 m dela
            rel = 3.6 * fb * fall * keep_water
            wr = np.where(near_ & (~(h0 < -0.2)) & (np.abs(rel) > 0.05), 0.96, 0.0)
            put(0, N8Z, 0, N8X, wr, 560.0 + dd, np.maximum(h0 + rel, 0.4))
    # pontas da orla: terreno plano (nivel do calcadao) em volta da Praca do Farol, para o parque nascer rente ao piso
    cnt = {}
    for e in city.edges:
        if e.get('name') == 'Av. Beira-Mar':
            for q in (e['a'], e['b']): cnt[q] = cnt.get(q, 0) + 1
    ends = [(city.nodes[q][0], city.nodes[q][1] + 34.0) for q, c_ in cnt.items() if c_ == 1]       # as duas pontas da Av. Beira-Mar (bolsao de retorno)
    for (ex, ez) in ends:
        R_ = 48.0 + 70.0
        i0, i1 = max(int((ex - R_) / STEP), 0), min(int((ex + R_) / STEP) + 2, N8X); j0, j1 = max(int((ez - R_) / STEP), 0), min(int((ez + R_) / STEP) + 2, N8Z)
        d = np.hypot(X[j0:j1, i0:i1] - ex, Z[j0:j1, i0:i1] - ez); hh = h0[j0:j1, i0:i1]
        wet = hh < -0.2
        sh = np.clip(4.0 * np.abs(hh - ORLA_END_Y), 14.0, 60.0)
        ii_ = np.clip(np.round(X[j0:j1, i0:i1] / CELL).astype(int), 0, NX - 1); jj_ = np.clip(np.round(Z[j0:j1, i0:i1] / CELL).astype(int), 0, NZ - 1)
        beach_ = geo.beach_zone[jj_, ii_] & (geo.Dsea[jj_, ii_] < 72.0)                  # a areia continua areia (o terreno plano e so da ponta de terra)
        w = np.where(d <= 48.0, 1.0, smooth(np.clip(1.0 - (d - 48.0) / sh, 0, 1))) * (~wet) * (~beach_)
        put(j0, j1, i0, i1, w, 500.0 + d, np.full_like(d, ORLA_END_Y))
    # platos dos lotes das casas (Etapa D): plano dentro do lote, talude suave fora
    if plateaus:
        import lots as _lots
        for pl in plateaus:
            R_ = max(pl['hw'], pl['hd']) + 64 + 4
            i0, i1 = max(int((pl['cx'] - R_) / STEP), 0), min(int((pl['cx'] + R_) / STEP) + 2, N8X)
            j0, j1 = max(int((pl['cz'] - R_) / STEP), 0), min(int((pl['cz'] + R_) / STEP) + 2, N8Z)
            if i1 <= i0 or j1 <= j0: continue
            d = _lots.plateau_weight(X[j0:j1, i0:i1], Z[j0:j1, i0:i1], pl)
            FL = 7.0                                  # alem do lote o terreno continua plano (a grade de 8 m nao pode "morder" o quintal), mas perde o empate para as ruas
            dh = np.abs(h0[j0:j1, i0:i1] - pl['y']); sh = np.clip(4.0 * dh, pl['blend'], 60.0)      # talude 1:4 no maximo: o morro desce suave em volta do terraco, sem barranco
            w = np.where(d <= FL, 1.0, smooth(np.clip(1.0 - (d - FL) / sh, 0, 1)))
            put(j0, j1, i0, i1, np.maximum(w, 0), np.where(d <= 0.3, -1.0, 500.0 + d), np.full_like(d, pl['y']))
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
    import lots
    city.lotplan = lots.plan(city, geo, ynode)
    for ln in city.lotplan.log: print('  ' + ln)
    hf = carve(h, X, Z, city, ynode, geo, city.lotplan.plateaus)
    # faixa de areia (entre o mar e o muro do calcadao): nunca acima de 1,2 m (senao o jogo pinta grama na praia)
    ii = np.clip(np.round(X / CELL).astype(int), 0, NX - 1); jj = np.clip(np.round(Z / CELL).astype(int), 0, NZ - 1)
    sand = geo.beach_zone[jj, ii] & (geo.Dsea[jj, ii] < 58.0) & ~geo.water[jj, ii]
    hf = np.where(sand & (hf > 1.2), 1.2, hf)
    return hf, ynode, X, Z

def sample8(h, x, z):
    fx = min(max(x / STEP, 0), N8X - 1.001); fz = min(max(z / STEP, 0), N8Z - 1.001)
    i, j = int(fx), int(fz); a, b = fx - i, fz - j
    return (h[j, i] * (1 - a) + h[j, i + 1] * a) * (1 - b) + (h[j + 1, i] * (1 - a) + h[j + 1, i + 1] * a) * b
