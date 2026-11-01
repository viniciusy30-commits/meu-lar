#!/usr/bin/env python3
"""
All Star (cano alto, lona + borracha) procedural para o Meu Lar -> peça CUP1 feet/AllStar + tiles no atlas extra2 (região 7, recolorível).
Uso: python3 allstar.py <assets/cute (entrada e saída)>
Modelo: lona (SDF + sulco do cadarço), borracha (sola + faixa + biqueira), 12 ilhós, 2 respiros, cadarço cruzado com laço, patch com estrela.
Cores (extra2_recolor.txt, região 7): w0 = lona/faixa/risco da sola (slot 7), w1 = borracha/cadarço (slot 8). Ilhós, patch e sola fixos.
Esqueleto: pesos copiados do pé/canela do corpo-base (ossos 18/19/20 = pé direito, 22/23/24 = esquerdo).
"""
import sys, os, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.spatial import cKDTree
from skimage import measure

A = sys.argv[1].rstrip('/') + '/'
PREVIEW = len(sys.argv) > 2 and sys.argv[2] == 'preview'

# ------------------------------------------------------------------ SDF (pé direito, x local: + = fora; z + = bico; y + = cima)
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)
def smax(a, b, k): return -smin(-a, -b, k)
def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

BOT = -2.0; ZH, ZT = -6.0, 19.4; CUFF = 17.4; X0 = 11.15
def foot_cx(z): return np.interp(z, [-7, 0, 10, 20], [0.0, 0.0, 0.05, 0.5])
def foot_hw(z):
    return np.interp(z, [-6.0, -5.3, -4.0, -1.5, 2.0, 5.0, 8.5, 12, 15, 17, 18.6, 19.4], [0.0, 2.3, 3.9, 4.4, 4.2, 4.35, 4.9, 5.3, 5.1, 4.5, 3.0, 0.0])
def plan(x, z, off=0.0):
    cx = foot_cx(z); w = foot_hw(z) + off
    arch = np.where(x < cx, np.interp(z, [-2, 2, 5, 9, 12], [0, 0.4, 0.55, 0.3, 0]), 0)
    d = np.abs(x - cx) - (w - arch)
    dz = np.maximum(ZH - off - z, z - (ZT + off))
    return np.where((d > 0) & (dz > 0), np.sqrt(d * d + dz * dz), np.maximum(d, dz))
def top_profile(z):
    return np.interp(z, [-6.0, -5.0, -3, 0, 2.0, 3.6, 5.5, 8, 11, 14, 17, 18.6, 19.4], [CUFF, CUFF, CUFF, CUFF, 15.5, 12.8, 9.4, 7.4, 6.4, 5.6, 4.5, 3.0, 1.0])
def leg_cx(y): return -0.15 - 0.4 * np.clip((y - 10) / 8, 0, 1)
def leg_r(y):
    wid = np.clip((CUFF - y) / 10, 0, 1)
    return 3.45 + 0.5 * wid + 0.1 * sstep(15, CUFF, y), 3.95 + 0.55 * wid + 0.1 * sstep(15, CUFF, y)
def spring(z): return 0.5 * sstep(12, 19.4, z)
LEGZ = -0.5

def canvas0(p):
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    yy = y - spring(z)
    fu = plan(x, z, -0.15)
    top = top_profile(z)
    ytop = 1.2 + (top - 1.2) * (0.6 + 0.4 * np.clip(-fu / 3.0, 0, 1) ** 0.7)
    up = smax(fu, yy - ytop, 0.8)
    up = np.maximum(up, BOT + 0.6 - yy)
    cxl = leg_cx(y); rx, rz = leg_r(y)
    tube = (np.sqrt(((x - cxl) / rx) ** 2 + ((z - LEGZ) / rz) ** 2) - 1) * 3.5
    tube = np.maximum(tube, y - CUFF); tube = np.maximum(tube, BOT + 0.6 - y)
    body = smin(up, tube, 1.3)
    hole = (np.sqrt(((x - cxl) / (rx - 0.75)) ** 2 + ((z - LEGZ) / (rz - 0.75)) ** 2) - 1) * 3.0
    hole = np.maximum(hole, 6.5 - y)
    return np.maximum(body, -hole)
def rubber0(p):
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    yy = y - spring(z)
    sole = smax(plan(x, z, 0.55), np.maximum(BOT - yy, yy - 0.5), 0.5)
    top_fox = 2.5 + 0.9 * sstep(-1.5, -5.8, z)
    fox = smax(plan(x, z, 0.30), np.maximum(BOT - yy, yy - top_fox), 0.45)
    s = smin(sole, fox, 0.3)
    fu = plan(x, z, -0.15); top = top_profile(z)
    ytop = 1.2 + (top - 1.2) * (0.6 + 0.4 * np.clip(-fu / 3.0, 0, 1) ** 0.7) + 0.45
    zc = 12.0 + 0.7 * (np.abs(x - foot_cx(z)) / 4.6) ** 2
    c = smax(plan(x, z, 0.32), np.maximum(zc - z, yy - ytop), 0.8)
    c = np.maximum(c, BOT - yy)
    return smin(s, c, 0.35)

def grad(p, fn, e=0.04):
    g = np.zeros_like(p)
    for i in range(3):
        d = np.zeros(3); d[i] = e
        g[..., i] = (fn(p + d) - fn(p - d)) / (2 * e)
    return g
def project(p, fn, it=8):
    p = np.array(p, float)
    for _ in range(it):
        d = fn(p); g = grad(p, fn); gg = np.maximum((g * g).sum(-1, keepdims=True), 1e-9); p = p - g * d[..., None] / gg
    n = grad(p, fn); n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
    return p, n

# ------------------------------------------------------------------ linha central, ilhós, sulco
def centerline():
    ctrl = np.array([(9.6, 6.5), (8.3, 7.3), (7.0, 8.4), (5.9, 9.7), (5.0, 11.1), (4.55, 12.6), (4.35, 14.2), (4.3, 15.9)])
    pts = []
    for z, y in ctrl:
        p, n = project(np.array([leg_cx(y), y + 0.5, z]), canvas0)
        pts.append(p)
    pts = np.array(pts)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    ts = np.linspace(0, L[-1], 80)
    dense = np.stack([np.interp(ts, L, pts[:, c]) for c in range(3)], 1)
    dense, nd = project(dense, canvas0)
    for _ in range(2): dense[1:-1] = (dense[:-2] + 2 * dense[1:-1] + dense[2:]) / 4
    dense, nd = project(dense, canvas0, 3)
    return dense, nd
CL, CN = centerline()
GROOVE = cKDTree(CL + CN * 0.5)
def canvas(p):
    d = GROOVE.query(p.reshape(-1, 3))[0].reshape(p.shape[:-1])
    return smax(canvas0(p), -(d - 1.0), 0.3)
def rubber(p): return rubber0(p)

def cl_at(s):
    """ponto, normal e tangente (para cima) da linha central em s (0..1)."""
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(CL, axis=0), axis=1))]); t = s * L[-1]
    p = np.array([np.interp(t, L, CL[:, c]) for c in range(3)]); n = np.array([np.interp(t, L, CN[:, c]) for c in range(3)])
    q = np.array([np.interp(min(t + 0.2, L[-1]), L, CL[:, c]) for c in range(3)]) - np.array([np.interp(max(t - 0.2, 0), L, CL[:, c]) for c in range(3)])
    n /= np.linalg.norm(n); q /= np.linalg.norm(q)
    return p, n, q

# ------------------------------------------------------------------ malha (marching cubes) + corte do que fica escondido
def mc(fn, st, box):
    (x0, x1), (y0, y1), (z0, z1) = box
    xs = np.arange(x0, x1 + st, st); ys = np.arange(y0, y1 + st, st); zs = np.arange(z0, z1 + st, st)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij'); G = fn(np.stack([X, Y, Z], -1))
    v, f, _, _ = measure.marching_cubes(G, 0, spacing=(st, st, st))
    v = v + np.array([xs[0], ys[0], zs[0]])
    v, n = project(v, fn, 4)
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    fl = (np.cross(b - a, c - a) * (n[f[:, 0]] + n[f[:, 1]] + n[f[:, 2]])).sum(1) < 0
    f = f.copy(); f[fl] = f[fl][:, [0, 2, 1]]
    return v, f, n
BOX = ((-8.5, 8.5), (-3, 19), (-8, 22))
def cull(v, f, others, tol):
    c = v[f].mean(1); keep = np.ones(len(f), bool)
    for fn in others: keep &= fn(c) > tol
    return f[keep]
def compact(v, f, *ex):
    u, inv = np.unique(f.ravel(), return_inverse=True)
    return (v[u], inv.reshape(-1, 3)) + tuple(e[u] for e in ex)

# ------------------------------------------------------------------ atlas (linha 3 do extra2.png)
AW, AH = 2016, 896
CX, CY, CW, CH = 232, 676, 320, 216        # lona: vista lateral (z,y)
RX, RY = 566, 676                          # borracha: mesma vista
LX, LY, LW, LH = 904, 676, 48, 48          # cadarço
EX, EY, EW = 960, 676, 64                  # ilhós (radial)
PX, PY, PW = 1040, 676, 128                # patch
Z0, Z1, Y0, Y1 = -7.0, 22.0, -2.6, 18.0
def uv_side(p, ox, oy):
    u = np.clip((p[:, 2] - Z0) / (Z1 - Z0), 0.012, 0.988); v = np.clip((p[:, 1] - Y0) / (Y1 - Y0), 0.012, 0.988)
    return np.stack([(ox + u * CW) / AW, (oy + (1 - v) * CH) / AH], 1)
def uv_px(px, py): return np.array([px / AW, py / AH])

# ------------------------------------------------------------------ geometria auxiliar
def tube(path, r, ns=5, closed=False):
    path = np.asarray(path, float); n = len(path)
    T = np.gradient(path, axis=0); T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    ref = np.array([0, 1.0, 0]) if abs(T[0, 1]) < 0.9 else np.array([1.0, 0, 0])
    N = np.cross(T[0], ref); N /= np.linalg.norm(N); rings = []
    for i in range(n):
        if i > 0:
            N = N - T[i] * np.dot(N, T[i]); N /= max(np.linalg.norm(N), 1e-9)
        B = np.cross(T[i], N); rr = r if np.isscalar(r) else r[i]
        ring = []
        for k in range(ns):
            a = 2 * np.pi * k / ns; d = N * np.cos(a) + B * np.sin(a)
            ring.append((path[i] + d * rr, d))
        rings.append(ring)
    pos = np.array([q[0] for rg in rings for q in rg]); nor = np.array([q[1] for rg in rings for q in rg])
    ix = []
    for i in range(n - 1):
        for k in range(ns):
            a = i * ns + k; b = i * ns + (k + 1) % ns; c = (i + 1) * ns + k; d = (i + 1) * ns + (k + 1) % ns
            ix += [a, c, b, b, c, d]
    ix = np.array(ix).reshape(-1, 3)
    return pos, nor, ix

def disc(center, normal, up, rad, rings=2, ns=12):
    """disco achatado (ilhós / patch): vértice central + anéis."""
    normal = normal / np.linalg.norm(normal); up = up - normal * np.dot(up, normal); up /= np.linalg.norm(up); rt = np.cross(up, normal)
    pos = [center]; ang = [(0.0, 0.0)]
    for r in range(1, rings + 1):
        for k in range(ns):
            a = 2 * np.pi * k / ns; pos.append(center + (rt * np.cos(a) + up * np.sin(a)) * rad * r / rings); ang.append((r / rings, a))
    ix = []
    for k in range(ns): ix.append((0, 1 + k, 1 + (k + 1) % ns))
    for r in range(1, rings):
        for k in range(ns):
            a = 1 + (r - 1) * ns + k; b = 1 + (r - 1) * ns + (k + 1) % ns; c = 1 + r * ns + k; d = 1 + r * ns + (k + 1) % ns
            ix += [(a, c, b), (b, c, d)]
    return np.array(pos), np.array(ang), np.array(ix)

def build_right():
    """devolve dict de partes (pos, nor, uv, ix) no espaço local do pé direito."""
    parts = []
    # --- lona
    vc, fc, nc = mc(canvas, 0.8, BOX)
    vr, fr, nr = mc(rubber, 0.7, BOX)
    fc = cull(vc, fc, [rubber], -0.25)
    fr = cull(vr, fr, [canvas0], -0.6)
    vc, fc, nc = compact(vc, fc, nc)
    vr, fr, nr = compact(vr, fr, nr)
    parts.append(('canvas', vc, nc, uv_side(vc, CX, CY), fc))
    parts.append(('rubber', vr, nr, uv_side(vr, RX, RY), fr))
    # --- ilhós do cadarço (6 pares) + pontos de passagem
    S = np.linspace(0.04, 0.9, 6)
    EL = []; ER = []
    for s in S:
        p, n, t = cl_at(s)
        side = np.cross(t, n); side /= np.linalg.norm(side)
        if side[0] < 0: side = -side
        for sg, lst in ((-1, EL), (1, ER)):
            q, nq = project(p + side * sg * 1.55 + n * 0.3, canvas0)
            lst.append((q, nq, t))
    def eyelet(q, nq, t, rad=0.46):
        pos, ang, ix = disc(q + nq * 0.07, nq, t, rad, 2, 8)
        uv = np.array([uv_px(EX + EW / 2 + a[0] * np.cos(a[1]) * (EW / 2 - 3) , EY + EW / 2 + a[0] * np.sin(a[1]) * (EW / 2 - 3)) for a in ang])
        # raio 0.5 do disco (anel de dentro) cai no aro prateado; centro = furo escuro
        nor = np.tile(nq, (len(pos), 1))
        return pos, nor, uv, ix
    for lst in (EL, ER):
        for q, nq, t in lst:
            pos, nor, uv, ix = eyelet(q, nq, t)
            parts.append(('eyelet', pos, nor, uv, ix))
    # respiros do lado de dentro (2 ilhós no arco do pé)
    for z in (-1.3, 1.0):
        q, nq = project(np.array([-4.6, 4.6, z]), canvas0)
        pos, nor, uv, ix = eyelet(q, nq, np.array([0, 1.0, 0]), 0.5)
        parts.append(('eyelet', pos, nor, uv, ix))
    # --- patch com estrela, lado de dentro do tornozelo
    q, nq = project(np.array([-5.4, 9.2, -0.4]), canvas0)
    pos, ang, ix = disc(q + nq * 0.05, nq, np.array([0, 1.0, 0]), 1.65, 3, 16)
    uv = np.array([uv_px(PX + PW / 2 + a[0] * np.cos(a[1]) * (PW / 2 - 3), PY + PW / 2 - a[0] * np.sin(a[1]) * (PW / 2 - 3)) for a in ang])
    # normal do patch: a da superfície em cada ponto
    pp, nn = project(pos, canvas0, 4)
    pos = pp + nn * 0.05
    parts.append(('patch', pos, nn, uv, ix))
    # --- cadarço cruzado
    lace_uv = uv_px(LX + LW / 2, LY + LH / 2)
    def lace(a, b, na, nb, lift=0.3, r=0.27):
        ts = np.linspace(0, 1, 9)
        nm = (na + nb); nm /= np.linalg.norm(nm)
        path = np.array([a + (b - a) * t + nm * (lift + 0.36 * np.sin(np.pi * t)) for t in ts])
        pos, nor, ix = tube(path, r, 5)
        return ('lace', pos, nor, np.tile(lace_uv, (len(pos), 1)), ix)
    for i in range(5):
        parts.append(lace(EL[i][0], ER[i + 1][0], EL[i][1], ER[i + 1][1]))
        parts.append(lace(ER[i][0], EL[i + 1][0], ER[i][1], EL[i + 1][1]))
    # primeira volta: cadarço reto no ilhós de baixo
    parts.append(lace(EL[0][0], ER[0][0], EL[0][1], ER[0][1], 0.22))
    # --- laço
    pt, nt, tt = cl_at(0.94)
    side = np.cross(tt, nt); side /= np.linalg.norm(side)
    if side[0] < 0: side = -side
    base = pt + nt * 0.9
    for sg in (-1, 1):
        ts = np.linspace(0, 2 * np.pi, 15)
        ctr = base + side * sg * 1.25 + tt * 0.25
        path = np.array([ctr + side * sg * 1.25 * np.cos(a) * -1 + tt * 0.85 * np.sin(a) + nt * 0.25 * np.sin(a) ** 2 for a in ts])
        pos, nor, ix = tube(path, 0.26, 5)
        parts.append(('lace', pos, nor, np.tile(lace_uv, (len(pos), 1)), ix))
        tail = np.array([base + side * sg * (0.2 + 1.5 * t ** 1.3) - tt * (3.0 * t) + nt * (0.15 + 0.35 * np.sin(np.pi * t)) for t in np.linspace(0, 1, 8)])
        pos, nor, ix = tube(tail, 0.26, 5)
        parts.append(('lace', pos, nor, np.tile(lace_uv, (len(pos), 1)), ix))
    return parts

# ------------------------------------------------------------------ pesos de osso a partir do corpo-base
REC = np.dtype([('pos', '<f4', 3), ('nor', '<f4', 3), ('uv', '<f4', 2), ('col', 'u1', 4), ('bi', 'u1', 4), ('bw', 'u1', 4)])
def load_body():
    b = open(A + 'base.bin', 'rb').read(); nv, ni, nb, nc = struct.unpack_from('<4i', b, 4)
    v = np.frombuffer(b, REC, nv, 20); t = np.frombuffer(b, '<u2', ni, 20 + nv * 44).reshape(-1, 3).astype(int)
    return v, t
def skin_weights(P, body):
    sel = (body['pos'][:, 0] > 0) & (body['pos'][:, 1] < 45)
    BP = body['pos'][sel].astype(float); BI = body['bi'][sel]; BW = body['bw'][sel].astype(float)
    tree = cKDTree(BP); d, idx = tree.query(P, k=5)
    out_i = np.zeros((len(P), 4), np.uint8); out_w = np.zeros((len(P), 4), np.uint8)
    for r in range(len(P)):
        acc = {}
        wk = 1.0 / (d[r] + 0.4) ** 2; wk /= wk.sum()
        for j, w in zip(idx[r], wk):
            for bi_, bw_ in zip(BI[j], BW[j]):
                if bw_ > 0: acc[int(bi_)] = acc.get(int(bi_), 0) + w * bw_ / 255.0
        it = sorted(acc.items(), key=lambda kv: -kv[1])[:4]; tot = sum(w for _, w in it)
        bi = [k for k, _ in it] + [0] * (4 - len(it)); bw = [w / tot * 255 for _, w in it] + [0] * (4 - len(it))
        bwi = np.round(bw).astype(int); bwi[0] += 255 - bwi.sum()
        out_i[r] = bi; out_w[r] = bwi
    return out_i, out_w

# ------------------------------------------------------------------ atlas
def paint_atlas():
    atlas = np.asarray(Image.open(A + 'extra2.png').convert('RGB')).astype(float)
    rm = np.asarray(Image.open(A + 'extra2_recolor.png').convert('RGB')).astype(np.uint8).copy()
    rs = np.asarray(Image.open(A + 'extra2_recolor_s.png').convert('RGB')).astype(np.uint8).copy()
    assert atlas.shape[:2] == (AH, AW), atlas.shape
    # limpa a área (linha 3, a partir da coluna 1): só tiles vazios (28..35)
    assert set(np.unique(rm[672:, 224:, 2]).tolist()) <= {0, 7}, 'área do atlas já usada por outra peça'
    R0 = np.array([36.0, 36.0, 40.0]); R1 = np.array([238.0, 238.0, 240.0])
    rng = np.random.RandomState(7)
    def put(x0, y0, w, h, base, w0, w1, rid, sh):
        sl = (slice(y0, y0 + h), slice(x0, x0 + w))
        atlas[sl] = base; rm[sl + (0,)] = np.round(w0 * 255); rm[sl + (1,)] = np.round(w1 * 255); rm[sl + (2,)] = rid
        g = np.round(np.clip(sh, 0, 2) / 2 * 255).astype(np.uint8); rs[sl] = np.stack([g, g, g], -1)
    # --- coordenadas de cada pixel (z,y)
    xs = (np.arange(CW) + 0.5) / CW * (Z1 - Z0) + Z0; ys = Y1 - (np.arange(CH) + 0.5) / CH * (Y1 - Y0)
    Zg, Yg = np.meshgrid(xs, ys)
    # trama da lona: fios cruzados + ruído leve
    weave = 1.0 + 0.10 * (np.sin(Zg * 26.0) * np.sin(Yg * 26.0)) + 0.05 * rng.randn(CH, CW)
    weave = np.clip(weave, 0.7, 1.3)
    # --- lona
    sh = weave.copy(); w0 = np.ones((CH, CW)); w1 = np.zeros((CH, CW))
    # costura tracejada logo acima da faixa e perto da borda do cano
    for yl, dz in ((3.55, 0.7), (16.55, 0.6)):
        line = (np.abs(Yg - yl) < 0.11) & (np.mod(Zg, dz) < dz * 0.62)
        sh = np.where(line, 1.75, sh)
    # faixa fina mais clara na borda do cano
    sh = np.where(Yg > 17.1, sh * 1.12, sh)
    base = R0[None, None, :] * sh[..., None]
    put(CX, CY, CW, CH, base, w0, w1, 7, sh)
    # --- borracha: branca; risco preto na faixa (w0 = acompanha a cor da lona); sola com frisos
    sh = 1.0 + 0.02 * rng.randn(CH, CW); w0 = np.zeros((CH, CW)); w1 = np.ones((CH, CW))
    shr = np.full((CH, CW), 1.0)
    stripe = (Yg > 0.95) & (Yg < 1.45)
    w0 = np.where(stripe, 1.0, w0); w1 = np.where(stripe, 0.0, w1)
    stripe2 = (Yg > 1.75) & (Yg < 1.95)
    w0 = np.where(stripe2, 1.0, w0); w1 = np.where(stripe2, 0.0, w1)
    # acima da faixa (so atras da biqueira) a borracha assume a cor da lona: esconde a junção irregular com a lona
    top = (Yg > 2.1) & (Zg < 11.9)
    w0 = np.where(top, 1.0, w0); w1 = np.where(top, 0.0, w1)
    # sola: faixa de baixo cinza com frisos transversais
    tread = Yg < -1.55
    shr = np.where(tread, 0.62 + 0.18 * (np.mod(Zg, 0.9) < 0.45), shr)
    # borda de baixo mais suja
    shr = np.where((Yg < -1.2) & ~tread, 0.9, shr)
    shr = shr + 0.02 * rng.randn(CH, CW)
    base = np.where(w0[..., None] > 0.5, R0[None, None, :] * shr[..., None], R1[None, None, :] * shr[..., None])
    put(RX, RY, CW, CH, base, w0, w1, 7, shr)
    # --- cadarço (w1): trama diagonal
    gy, gx = np.mgrid[0:LH, 0:LW]
    shl = 0.93 + 0.07 * np.sin((gx + gy) * 1.1)
    put(LX, LY, LW, LH, R1[None, None, :] * shl[..., None], np.zeros((LH, LW)), np.ones((LH, LW)), 7, shl)
    # --- ilhós (fixo): centro escuro, aro prateado, borda cinza
    gy, gx = np.mgrid[0:EW, 0:EW]; r = np.hypot(gx + 0.5 - EW / 2, gy + 0.5 - EW / 2) / (EW / 2 - 3)
    col = np.zeros((EW, EW, 3))
    col[:] = (70, 72, 80)
    ring = (r > 0.45) & (r <= 0.92)
    col[ring] = (205, 208, 214)
    col[r > 0.92] = (150, 152, 160)
    col[r <= 0.45] = (18, 16, 20)
    put(EX, EY, EW, EW, col, np.zeros((EW, EW)), np.zeros((EW, EW)), 0, np.ones((EW, EW)))
    # --- patch (fixo): disco branco, aro azul-marinho e vermelho, estrela azul
    gy, gx = np.mgrid[0:PW, 0:PW]; cx = gx + 0.5 - PW / 2; cy = gy + 0.5 - PW / 2; r = np.hypot(cx, cy) / (PW / 2 - 3)
    col = np.zeros((PW, PW, 3)); col[:] = (236, 236, 238)
    col[(r > 0.80) & (r <= 0.92)] = (178, 28, 36)
    col[(r > 0.92)] = (24, 40, 110)
    col[(r > 0.70) & (r <= 0.80)] = (236, 236, 238)
    ang = np.arctan2(-cy, cx)
    star_r = 0.55 * (0.45 + 0.55 * (np.abs(np.cos(2.5 * (ang - np.pi / 2))) ** 0.8 * 0 + (0.5 + 0.5 * np.cos(5 * (ang - np.pi / 2)))))
    star = (r < star_r)
    col[star] = (24, 40, 110)
    put(PX, PY, PW, PW, col, np.zeros((PW, PW)), np.zeros((PW, PW)), 0, np.ones((PW, PW)))
    # margem: replica as bordas das áreas pintadas para não vazar cor entre vizinhos (filtro bilinear)
    for (x0, y0, w, h) in ((CX, CY, CW, CH), (RX, RY, CW, CH), (LX, LY, LW, LH), (EX, EY, EW, EW), (PX, PY, PW, PW)):
        for k in range(1, 4):
            for arr in (atlas, rm, rs):
                arr[y0 - k, x0:x0 + w] = arr[y0, x0:x0 + w]; arr[y0 + h - 1 + k, x0:x0 + w] = arr[y0 + h - 1, x0:x0 + w]
                arr[y0 - k:y0 + h + k, x0 - k] = arr[y0 - k:y0 + h + k, x0]; arr[y0 - k:y0 + h + k, x0 + w - 1 + k] = arr[y0 - k:y0 + h + k, x0 + w - 1]
    return atlas, rm, rs

# ------------------------------------------------------------------ gravação CUP1 e ocultar corpo
def write_cup1(fn, pos, nor, uv, ix, bi, bw, hide):
    n = len(pos); r = np.zeros(n, REC); r['pos'] = pos; r['nor'] = nor; r['uv'] = uv; r['col'] = 255; r['bi'] = bi; r['bw'] = bw
    with open(fn, 'wb') as f:
        f.write(b'CUP1' + struct.pack('<3i', n, len(ix), 1 if len(hide) else 0)); f.write(r.tobytes()); f.write(ix.astype('<u2').tobytes())
        if len(hide): f.write(struct.pack('<i', len(hide))); f.write(hide.astype('<u2').tobytes())
def samples(pos, ix, nor, step=0.6):
    P = []; N = []
    for a, b_, c in ix.reshape(-1, 3).astype(int):
        pa, pb, pc = pos[a], pos[b_], pos[c]
        k = int(np.ceil(max(np.linalg.norm(pb - pa), np.linalg.norm(pc - pb), np.linalg.norm(pa - pc)) / step)); k = max(1, min(k, 12))
        for i in range(k + 1):
            for j in range(k + 1 - i):
                u, v = i / k, j / k; w = 1 - u - v; P.append(pa * w + pb * u + pc * v); N.append(nor[a] * w + nor[b_] * u + nor[c] * v)
    return np.array(P), np.array(N)
def hide_list(pos, ix, nor, body, bt):
    dom = body['bi'][np.arange(len(body)), np.argmax(body['bw'], 1)]
    P, N = samples(pos.astype(float), ix, nor.astype(float))
    d, j = cKDTree(P).query(body['pos'].astype(float))
    cov = np.isin(dom, [19, 20, 23, 24]) & (d < 1.5) & (np.einsum('ij,ij->i', N[j], body['nor'].astype(float)) > 0.2)
    return np.where(cov[bt].all(1))[0].astype(np.uint16)

def main():
    body, bt = load_body()
    parts = build_right()
    pos = np.concatenate([p[1] for p in parts]); nor = np.concatenate([p[2] for p in parts]); uv = np.concatenate([p[3] for p in parts])
    ix = []; off = 0
    for p in parts:
        ix.append(p[4] + off); off += len(p[1])
    ix = np.concatenate(ix)
    # mundo: pé direito
    P = pos.copy(); P[:, 0] += X0
    bi, bw = skin_weights(P, body)
    Pl = P.copy(); Pl[:, 0] *= -1; Nl = nor.copy(); Nl[:, 0] *= -1
    mp = {17: 21, 18: 22, 19: 23, 20: 24}
    bil = np.vectorize(lambda b: mp.get(int(b), int(b)))(bi).astype(np.uint8)
    n = len(P)
    allp = np.concatenate([P, Pl]); alln = np.concatenate([nor, Nl]); alluv = np.concatenate([uv, uv])
    allix = np.concatenate([ix, ix[:, [0, 2, 1]] + n]); allbi = np.concatenate([bi, bil]); allbw = np.concatenate([bw, bw])
    hide = hide_list(allp, allix, alln, body, bt)
    write_cup1(A + 'p_feet_allstar.bin', allp, alln, alluv, allix.ravel(), allbi, allbw, hide)
    atlas, rm, rs = paint_atlas()
    Image.fromarray(np.round(atlas).astype(np.uint8)).save(A + 'extra2.png', optimize=True)
    Image.fromarray(rm).save(A + 'extra2_recolor.png', optimize=True)
    Image.fromarray(rs).save(A + 'extra2_recolor_s.png', optimize=True)
    # tabela de cores: região 7
    t = open(A + 'extra2_recolor.txt').read().splitlines()
    t = [l for l in t if not l.startswith('7|')]
    t.append('7|allstar|7|8|36.0 36.0 40.0|238.0 238.0 240.0')
    open(A + 'extra2_recolor.txt', 'w').write('\n'.join(t) + '\n')
    np.savez('/tmp/allstar_dbg.npz', pos=allp, nor=alln, uv=alluv, ix=allix, bi=allbi, bw=allbw)
    for name in sorted({p[0] for p in parts}): print(name, sum(len(p[1]) for p in parts if p[0] == name), 'v')
    print('total', len(allp), 'v', len(allix), 'tris, ocultos', len(hide))

if __name__ == '__main__':
    main()
