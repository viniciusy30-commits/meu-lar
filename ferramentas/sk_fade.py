"""Cabelo masculino LOW FADE com topo texturizado curto (franja para a frente). Original, feito para cada corpo do jogo.

Partes (uma peça CUP1, slot hairBack, uma textura 1024x1024 RGBA):
  1. Casca do couro cabeludo: superfície lisa por raio a partir do centro da cabeça (raio = crânio medido por raios
     contra a malha do corpo + 1,2 mm). Linha do cabelo própria: testa, entradas, costeletas, contorno da orelha e nuca.
     O degradê (pele -> fios curtos -> denso) vem da textura: cada linha da textura tem uma densidade de fios curtinhos
     (recorte por alfa); a coordenada v de cada vértice é o nível do degradê ali (baixo nas laterais e na nuca).
  2. Topo texturizado: ~330 mechas (cartões curvos de 3 colunas) em 3 camadas + franja, enraizadas no topo,
     penteadas para a frente a partir do redemoinho, levantadas do crânio e com pontas desencontradas.
Unidades: as do corpo (cabeça adulta ~26 de altura). Ossos: cabeça (8).
"""
import sys, math
sys.path.insert(0, '/home/claude/work/skate')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
from sk_common import load_body, write_cup, smooth
from sk_hair2 import HP

OUT = '/home/claude/work/skate/out5/'
TW = 1024
AM_NECK = 157.71; AM_H = 26.28
RNG = np.random.default_rng(7)


# ------------------------------------------------------------------------------------------------ textura
def make_texture(path):
    W = TW; H = TW
    alpha = Image.new('L', (W, H), 0); da = ImageDraw.Draw(alpha)
    col = np.zeros((H, W, 3), np.float32)
    base_lo = np.array([62, 55, 50.]); base_hi = np.array([24, 19, 16.])
    # --- metade de cima: degradê. linha r (0..511) = nível f = r/511 (0 pele, 1 denso)
    rows = np.arange(512) / 511.0
    for r in range(512):
        col[r, :, :] = base_lo * (1 - rows[r]) + base_hi * rows[r]
    cov = lambda f: np.clip((f - 0.03) / 0.9, 0, 1) ** 1.25
    rng = np.random.default_rng(3)
    band = 6
    for y0 in range(0, 512, band):
        f = (y0 + band / 2) / 511.0; c = min(0.985, cov(f))
        if c <= 0: continue
        seglen = 6 + 14 * f                    # fios ficam mais compridos para cima (de 0,6 a 2 mm)
        area_each = seglen * 2.0
        n = int(-math.log(1 - c) / area_each * band * W)
        for _ in range(n):
            x = rng.uniform(0, W); y = y0 + rng.uniform(0, band)
            ang = math.radians(90 + rng.normal(0, 22))   # para baixo (cresce para a nuca)
            L = seglen * rng.uniform(0.6, 1.3)
            x2 = x + math.cos(ang) * L; y2 = y + math.sin(ang) * L
            da.line([(x, y), (x2, y2)], fill=255, width=2)
    a = np.array(alpha, np.float32)
    a[470:512, :] = 255                       # topo do degradê: fechado (couro cabeludo nunca aparece)
    # variação de cor dos fios curtos (mais escuro onde há fio)
    streak = ndimage.gaussian_filter(np.random.default_rng(5).normal(size=(512, W)), (2.5, 0.7))
    col[:512] *= (1.0 + 0.10 * streak[..., None])
    # --- metade de baixo: 8 mechas (128 x 512), raiz embaixo (linha 1023), ponta em cima (linha 512)
    tile = Image.new('RGBA', (W, 512), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    rng = np.random.default_rng(11)
    for k in range(8):
        x0 = k * 128
        nstr = 70
        for s in range(nstr):
            cx = x0 + 64 + rng.normal(0, 22)
            cx = min(max(cx, x0 + 10), x0 + 118)
            L = rng.uniform(300, 505)
            amp = rng.uniform(2, 9); ph = rng.uniform(0, 6.28); fr = rng.uniform(0.008, 0.02)
            lean = rng.normal(0, 0.05)
            g = rng.uniform(0, 1)
            if g < 0.15: cc = np.array([66, 50, 38])      # fios claros (brilho)
            elif g < 0.5: cc = np.array([38, 29, 23])
            else: cc = np.array([22, 17, 14])
            pts = []
            for i in range(26):
                t = i / 25
                y = 511 - t * L
                x = cx + math.sin(ph + y * fr) * amp * t + lean * (511 - y) * 0.3
                pts.append((x, y, t))
            for i in range(25):
                (xa, ya, ta), (xb, yb, tb) = pts[i], pts[i + 1]
                w = max(1, int(round(4.2 * (1 - ta) + 1.2)))
                al = 255 if ta < 0.8 else int(255 * (1 - (ta - 0.8) / 0.2) ** 0.7)
                td.line([(xa, ya), (xb, yb)], fill=(int(cc[0]), int(cc[1]), int(cc[2]), max(al, 0)), width=w)
        # raiz densa
        td.rectangle([x0 + 30, 470, x0 + 98, 511], fill=(24, 19, 16, 255))
    tl = np.array(tile).astype(np.float32)
    # fundo das mechas com a cor dos fios (sem halo claro ao filtrar)
    m = tl[..., 3] > 0
    fill = np.array([28, 22, 18.])
    rgb = np.where(m[..., None], tl[..., :3], fill)
    col[512:] = rgb
    a[512:] = tl[..., 3]
    out = np.dstack([np.clip(col, 0, 255), np.clip(a, 0, 255)]).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(path)
    return out


# ------------------------------------------------------------------------------------------------ crânio por raios
def ray_head(B, C, th, el):
    """raio (distância do centro C) da superfície do corpo nas direções (th, el); a maior interseção (lado de fora)."""
    top = B.P[:, 1].max()
    tri = B.idx[(B.P[B.idx][:, :, 1] > B.neck_y - 2).all(1)]
    V0 = B.P[tri[:, 0]]; E1 = B.P[tri[:, 1]] - V0; E2 = B.P[tri[:, 2]] - V0
    D = np.stack([np.cos(el) * np.sin(th), np.sin(el), np.cos(el) * np.cos(th)], -1).reshape(-1, 3)
    R = np.full(len(D), np.nan)
    for i0 in range(0, len(D), 192):
        d = D[i0:i0 + 192][:, None, :]
        pv = np.cross(d, E2[None]); det = (E1[None] * pv).sum(-1)
        ok = np.abs(det) > 1e-9; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        tv = C[None, None, :] - V0[None]
        u = (tv * pv).sum(-1) * inv
        qv = np.cross(tv, E1[None]); v = (d * qv).sum(-1) * inv
        t = (E2[None] * qv).sum(-1) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        t = np.where(hit, t, -1)
        R[i0:i0 + 192] = np.where(hit.any(1), t.max(1), np.nan)
    return R.reshape(th.shape)


def interp_lin(x, k):
    k = np.array(k, float); return np.interp(x, k[:, 0], k[:, 1])


# linha do cabelo (y - topo) por azimute |th| (0 = testa, pi = nuca)
HAIRLINE = [(0, -6.8), (0.55, -7.0), (0.8, -8.0), (0.95, -10.8), (1.07, -14.2), (1.20, -14.4), (1.30, -11.6), (1.42, -10.4), (1.62, -10.0),
            (1.80, -10.8), (1.95, -13.2), (2.2, -16.8), (2.55, -19.8), (3.15, -21.0)]
# começo do topo (onde nascem as mechas)
TOPLINE = [(0, -6.9), (0.75, -7.4), (1.2, -8.6), (1.57, -9.3), (2.2, -10.0), (3.15, -10.6)]


def fade_level(a, dy):
    yb = interp_lin(a, HAIRLINE)
    front = np.clip((dy - yb) / 0.6, 0, 1)
    Hh = interp_lin(a, [(0.9, 4.4), (1.6, 4.6), (2.4, 5.4), (3.15, 5.8)])
    side = smooth(0.0, 1.0, (dy - yb - 0.35) / Hh)
    w = smooth(0.72, 0.95, a)
    return front * (1 - w) + side * w, yb


# ------------------------------------------------------------------------------------------------ peça
def build(g, B, tex):
    top = B.P[:, 1].max(); hp = HP(B); zc = hp.zc
    C = np.array([0.0, top - 11.0, zc])
    NT, NE = 144, 72
    th = np.linspace(-np.pi, np.pi, NT, endpoint=False) + np.pi / NT
    el = np.radians(np.linspace(-62, 89, NE))
    TH, EL = np.meshgrid(th, el)
    R = ray_head(B, C, TH, EL)
    # preenche falhas e suaviza; orelhas/nariz não importam (ficam fora da linha do cabelo)
    bad = np.isnan(R)
    if bad.any():
        idx = ndimage.distance_transform_edt(bad, return_distances=False, return_indices=True)
        R = R[tuple(idx)]
    Rp = np.hstack([R[:, -2:], R, R[:, :2]]); Rs = ndimage.median_filter(Rp, size=(3, 3), mode='nearest')[:, 2:-2]
    Rs = ndimage.gaussian_filter(Rs, (0.8, 1.0), mode=('nearest', 'wrap'))
    Rf = np.maximum(Rs, ndimage.gaussian_filter(R, (0.6, 0.6), mode=('nearest', 'wrap')))   # nunca para dentro do crânio
    dirs = np.stack([np.cos(EL) * np.sin(TH), np.sin(EL), np.cos(EL) * np.cos(TH)], -1)

    def shell_at(off):
        return C + dirs * (Rf + off)[..., None]

    def r_dir(d):
        """raio do crânio na direção d (vetores unitários), por interpolação na grade"""
        t_ = np.arctan2(d[:, 0], d[:, 2]); e_ = np.arcsin(np.clip(d[:, 1], -1, 1))
        fi = (t_ - th[0]) / (2 * np.pi / NT); fj = (e_ - el[0]) / (el[1] - el[0])
        fj = np.clip(fj, 0, NE - 1.001); j = fj.astype(int); tj = fj - j
        i = np.floor(fi).astype(int); ti = fi - i; i0 = i % NT; i1 = (i + 1) % NT
        r0 = Rf[j, i0] * (1 - ti) + Rf[j, i1] * ti; r1 = Rf[j + 1, i0] * (1 - ti) + Rf[j + 1, i1] * ti
        return r0 * (1 - tj) + r1 * tj

    # ---------------- 1. casca com degradê
    S = shell_at(0.12)
    dy = S[..., 1] - top; A = np.abs(TH)
    f, yb = fade_level(A, dy)
    keep = dy >= yb - 0.25
    # normais da grade
    Sx = np.roll(S, -1, 1) - np.roll(S, 1, 1); Se = np.vstack([S[1:2] - S[0:1], S[2:] - S[:-2], S[-1:] - S[-2:-1]])
    Ng = np.cross(Se, Sx); Ng /= np.linalg.norm(Ng, axis=-1, keepdims=True) + 1e-12
    Ng *= np.sign((Ng * dirs).sum(-1, keepdims=True))
    # triângulos por célula; carta UV pela célula (6 cartas em volta da cabeça)
    P = []; N = []; UV = []; T = []
    NCH = 6
    vid = {}
    def vert(j, i, ch):
        key = (j, i % NT, ch)
        if key in vid: return vid[key]
        ii = i % NT
        tt = th[ii] if i < NT else th[ii] + 2 * np.pi
        c0 = -np.pi + ch * 2 * np.pi / NCH
        u = 0.03 + 0.94 * (tt - c0) / (2 * np.pi / NCH)
        u = min(max(u, 0.0), 1.0)
        v = 0.0008 + 0.4985 * float(np.clip(f[j, ii], 0, 1))
        P.append(S[j, ii]); N.append(Ng[j, ii]); UV.append((u, v)); vid[key] = len(P) - 1
        return vid[key]
    for j in range(NE - 1):
        for i in range(NT):
            i2 = i + 1
            q = [(j, i), (j, i2 % NT), (j + 1, i), (j + 1, i2 % NT)]
            ks = [keep[a_, b_] for a_, b_ in q]
            tc = (th[i] + (th[i2] if i2 < NT else th[0] + 2 * np.pi)) / 2
            ch = int((tc + np.pi) / (2 * np.pi) * NCH) % NCH
            if ks[0] and ks[1] and ks[2]: T.append((vert(j, i, ch), vert(j + 1, i, ch), vert(j, i2, ch)))
            if ks[1] and ks[3] and ks[2]: T.append((vert(j, i2, ch), vert(j + 1, i, ch), vert(j + 1, i2, ch)))
    # tampa do topo (polo): leque
    jt = NE - 1; cidx = len(P); P.append(C + np.array([0, Rf[jt].mean() + 0.12, 0])); N.append((0, 1, 0)); UV.append((0.5, 0.4993))
    for i in range(NT):
        ch = int(((th[i] + np.pi) / (2 * np.pi)) * NCH) % NCH
        a_ = vert(jt, i, ch); b_ = vert(jt, i + 1, ch)
        T.append((a_, b_, cidx))
    P = np.array(P); N = np.array(N, float); UV = np.array(UV, float); T = np.array(T, int)
    nshell = len(P)

    # ---------------- 2. topo texturizado (mechas)
    K = C + np.array([0, Rf[-1].mean() - 1.0, -4.5])          # redemoinho: alto, um pouco atrás
    St = shell_at(0.0)
    dyt = St[..., 1] - top
    ytop = interp_lin(A, TOPLINE)
    region = dyt >= ytop - 0.2
    # área de cada célula para sortear raízes
    cell = region[:-1, :] & region[1:, :]
    ar = np.linalg.norm(np.cross(np.roll(St, -1, 1)[:-1] - St[:-1], St[1:] - St[:-1]), axis=-1) * cell
    pr = ar.reshape(-1) / ar.sum()
    cards_P = []; cards_N = []; cards_UV = []; cards_T = []

    def add_card(p0, n0, D, L, w0, lift, tilt, tile, droop=0.0, minoff=0.25):
        nseg = 7
        Bw = np.cross(D, n0); Bw /= np.linalg.norm(Bw) + 1e-12
        Bw = Bw * math.cos(tilt) + n0 * math.sin(tilt)
        pts = []
        for s in range(nseg + 1):
            t = s / nseg
            p = p0 + D * (L * t) + n0 * (lift * math.sin(math.pi * min(t, 0.85) / 1.7)) + np.array([0, -droop * t * t, 0])
            pts.append(p)
        pts = np.array(pts)
        # nunca entra no crânio: empurra para fora do raio local + folga
        d = pts - C; rr = np.linalg.norm(d, axis=1); du = d / rr[:, None]
        rs = r_dir(du)
        need = rs + minoff + 0.15 * np.linspace(0, 1, nseg + 1) - rr
        pts = pts + du * np.maximum(need, 0)[:, None]
        base = len(cards_P)
        u0 = tile / 8.0
        for s in range(nseg + 1):
            t = s / nseg
            w = w0 * (1 - 0.45 * t)
            nn = du[s] * 0.7 + n0 * 0.3; nn /= np.linalg.norm(nn)
            for c_, off in enumerate((-0.5, 0.0, 0.5)):
                q = pts[s] + Bw * (off * w) + nn * (0.12 * w * (1 - abs(off) * 2))
                cards_P.append(q); cards_N.append(nn)
                cards_UV.append((u0 + (0.06 + 0.88 * (off + 0.5)) / 8.0, 0.9995 - t * 0.499))
        for s in range(nseg):
            for c_ in range(2):
                a_ = base + s * 3 + c_; b_ = a_ + 3
                cards_T.append((a_, b_, a_ + 1)); cards_T.append((a_ + 1, b_, b_ + 1))

    def tangent(v, n0):
        v = v - n0 * (v @ n0); l = np.linalg.norm(v)
        return v / l if l > 1e-6 else np.cross(n0, [1.0, 0, 0])

    def sample_roots(n):
        cells = RNG.choice(len(pr), size=n, p=pr)
        j = cells // NT; i = cells % NT
        a1 = RNG.random(n); a2 = RNG.random(n)
        p = St[j, i] * ((1 - a1) * (1 - a2))[:, None] + St[j, (i + 1) % NT] * (a1 * (1 - a2))[:, None] + St[j + 1, i] * ((1 - a1) * a2)[:, None] + St[j + 1, (i + 1) % NT] * (a1 * a2)[:, None]
        return p

    layers = [(170, 4.4, 1.9, 0.12, 0.12, 0.22), (160, 4.6, 1.6, 0.35, 0.22, 0.55), (120, 3.9, 1.35, 0.6, 0.35, 0.95)]
    fwd = np.array([0, 0, 1.0])
    for (n, L0, w0, lift0, tilt0, minoff) in layers:
        for p0 in sample_roots(n):
            d = p0 - C; n0 = d / np.linalg.norm(d)
            a = abs(math.atan2(d[0], d[2])); dyp = p0[1] - top
            Rd = tangent(p0 - K, n0)
            Fd = tangent(fwd, n0)
            wf = float(np.clip((p0[2] - K[2]) / 7.0, 0, 1) * np.clip((dyp + 8.5) / 5.0, 0, 1))
            D = Rd * (1 - wf) + Fd * wf
            D = tangent(D + RNG.normal(0, 0.17, 3), n0)
            yt = interp_lin(a, TOPLINE)
            edge = np.clip((dyp - yt) / 2.5, 0, 1)            # perto da borda do topo: mais curto, deitado
            L = L0 * RNG.uniform(0.75, 1.2) * (0.6 + 0.4 * edge)
            lift = lift0 * RNG.uniform(0.6, 1.3) * (0.35 + 0.65 * edge)
            add_card(p0 - n0 * 0.1, n0, D, L, w0 * RNG.uniform(0.8, 1.2), lift, RNG.normal(0, tilt0), int(RNG.integers(8)), minoff=minoff)
    # franja: nasce na linha da testa e cai para a frente/baixo, sem chegar nas sobrancelhas
    for k in range(34):
        a_t = RNG.uniform(-0.75, 0.75)
        e_lo = None
        # ponto da linha do cabelo nesse azimute (procura na grade a 1ª linha acima da linha do cabelo)
        ii = int(((a_t + np.pi) / (2 * np.pi)) * NT) % NT
        col = np.where(dyt[:, ii] >= interp_lin(abs(a_t), TOPLINE) + RNG.uniform(0.2, 1.6))[0]
        if len(col) == 0: continue
        p0 = St[col[0], ii]
        d = p0 - C; n0 = d / np.linalg.norm(d)
        D = tangent(np.array([0, -0.55, 1.0]) + RNG.normal(0, 0.25, 3), n0)
        add_card(p0 - n0 * 0.1, n0, D, RNG.uniform(3.2, 4.6), RNG.uniform(1.2, 1.7), RNG.uniform(0.5, 1.0), RNG.normal(0, 0.35), int(RNG.integers(8)), droop=0.6, minoff=0.35)
    CP = np.array(cards_P); CN = np.array(cards_N); CUV = np.array(cards_UV); CT = np.array(cards_T) + nshell
    # franja não desce além da testa
    fr = (CP[:, 2] > zc + 5) & (CP[:, 1] - top < -9.6)
    CP[fr, 1] = top - 9.6
    Pall = np.vstack([P, CP]); Nall = np.vstack([N, CN]); UVall = np.vstack([UV, CUV]); Tall = np.vstack([T, CT])
    return Pall, Nall, UVall, Tall, nshell


def make(g, tex):
    B0 = load_body(g); B = load_body(g)
    k = (B.P[:, 1].max() - B.neck_y) / AM_H
    piv = np.array([0, B.neck_y, 0.0]); new = np.array([0, AM_NECK, 0.0])
    if k > 1.04:
        B.P = (B.P - piv) / k + new; B.neck_y = AM_NECK
    else:
        k = 1.0; new = piv
    P, N, UV, T, ns = build(g, B, tex)
    if k > 1.0: P = (P - new) * k + piv
    nv = len(P)
    bi = np.zeros((nv, 4), np.uint8); bw = np.zeros((nv, 4), np.uint8); bi[:, 0] = 8; bw[:, 0] = 255
    write_cup(OUT + 'fade1_%s.cup' % g, P.astype(np.float32), N.astype(np.float32), UV.astype(np.float32), T, bi, bw)
    return P, N, UV, T, ns


if __name__ == '__main__':
    import os; os.makedirs(OUT, exist_ok=True)
    tex = make_texture(OUT + 'fade1.png')
    for g in sys.argv[1:] or ['am']:
        P, N, UV, T, ns = make(g, tex)
        print(g, 'vértices', len(P), 'tri', len(T), 'casca', ns, flush=True)
