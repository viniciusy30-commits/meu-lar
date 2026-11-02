"""Etapa 27 - camiseta larga (skatista): malha lisa (sem ombros estufados), mangas presas só ao osso do braço e textura recolorível.
Uso: python3 etapa27_camiseta_skate.py [pasta_assets_cute_de_origem] [pasta_de_saida]
Precisa de p_top_shirt.bin (peça original do pack) na pasta de origem. Gera p_top_skatetee.bin, skatetee.png e as máscaras de recolor."""
import sys, os, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app', 'src', 'main', 'assets', 'cute')
OUT = sys.argv[2] if len(sys.argv) > 2 else SRC
REC = np.dtype([('pos', '<f4', 3), ('nor', '<f4', 3), ('uv', '<f4', 2), ('col', 'u1', 4), ('bi', 'u1', 4), ('bw', 'u1', 4)])

def load(n):
    b = open(os.path.join(SRC, 'p_%s.bin' % n), 'rb').read(); nv, ni, fl = struct.unpack_from('<3i', b, 4)
    r = np.frombuffer(b, REC, nv, 16).copy(); o = 16 + nv * 44
    idx = np.frombuffer(b, '<u2', ni, o); o += ni * 2
    hide = None
    if fl & 1:
        nh = struct.unpack_from('<i', b, o)[0]; hide = np.frombuffer(b, '<u2', nh, o + 4)
    return r, idx, fl, hide

def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

S0 = np.array([13.3, 142.5, -2.9]); U = np.array([0.6012, -0.7991, -0.0076])   # início e direção do braço na pose de ligação
CUFF_T = float(os.environ.get('CUFF_T', '16.5'))
PAR = dict(sk=1.7, sf=0.55, ex0=0.40, ex1=0.50, ez0=0.34, ez1=0.40, hem=22.0, drop=1.2)

def frame(P):
    ax = np.abs(P[:, 0]); v = np.stack([ax - S0[0], P[:, 1] - S0[1], P[:, 2] - S0[2]], 1)
    t = v @ U; pr = v - t[:, None] * U[None, :]; r = np.linalg.norm(pr, axis=1)
    return ax, t, pr, r

def sleeve_w(P):
    ax, t, pr, r = frame(P)
    return sm(4, 12, t) * sm(15, 22, ax)

def deform(P, par=PAR):
    x, y, z = P[:, 0].copy(), P[:, 1].copy(), P[:, 2].copy()
    sx = np.where(x < 0, -1.0, 1.0); ax, t, pr, r = frame(P)
    ws = sleeve_w(P); wt = 1 - ws
    low = 1 - sm(100, 130, y)
    collar = 1 - 0.9 * sm(132, 148, y) * (1 - sm(10, 20, ax) * 0.5)
    ex = par['ex0'] + (par['ex1'] - par['ex0']) * low
    ez = par['ez0'] + (par['ez1'] - par['ez0']) * low
    X = ax * (1 + ex * wt * collar)
    Z = (z - 2.0) * (1 + ez * wt * collar) + 2.0
    Y = y - par['hem'] * (1 - sm(102, 128, y)) * wt
    Y = Y - par['drop'] * sm(10, 24, ax) * sm(125, 145, y) * wt
    t0 = 8.0
    tn = np.where(t > t0, t0 + (t - t0) * par['sk'], t)
    rn = r * (1 + par['sf'] * sm(-2, 8, t))
    rad = pr / np.maximum(r, 1e-6)[:, None]
    off = ((tn - t) * ws)[:, None] * U[None, :] + ((rn - r) * ws)[:, None] * rad
    X = X + off[:, 0]; Y = Y + off[:, 1]; Z = Z + off[:, 2]
    return np.stack([sx * X, Y, Z], 1)

# ---------------------------------------------------------------- malha
r, idx, fl, hide = load('top_shirt')
P0 = r['pos'].astype(float)
# Etapa 33: boca da manga reta. Os vértices da barra da manga ficavam espalhados (t 14..17,5) e a deformação virava dente de serra: alinha todos num plano.
_ax_, _t_, _pr_, _r_ = frame(P0)
_cuff = (_ax_ > 15) & (P0[:, 1] < 135) & (_t_ > 11.9) & (_t_ < 19.0)
P0[_cuff] += ((CUFF_T - _t_[_cuff])[:, None]) * U[None, :] * np.array([[1.0, 1.0, 1.0]]) * np.where(P0[_cuff, 0:1] < 0, np.array([[-1.0, 1.0, 1.0]]), 1.0)
# raio: a dobra interna do friso (raio 1,6..3) entrava no braço e recortava a boca da manga: leva tudo ao raio externo daquele ângulo
_ax_, _t_, _pr_, _r_ = frame(P0)
_e1 = np.cross(U, [0, 0, 1.0]); _e1 /= np.linalg.norm(_e1); _e2 = np.cross(U, _e1)
_ang = np.arctan2(_pr_ @ _e2, _pr_ @ _e1)
_ci = np.where(_cuff)[0]
for _s in (1.0, -1.0):
    _sel = _ci[(np.sign(P0[_ci, 0]) == _s)]
    for _i in _sel:
        _d = np.abs(np.angle(np.exp(1j * (_ang[_sel] - _ang[_i]))))
        _R = _r_[_sel][_d < np.radians(14)].max()
        if _r_[_i] < _R and _r_[_i] > 1e-6:
            _k = _R / _r_[_i]
            _a = _pr_[_i] * (_k - 1.0)
            P0[_i, 0] += _s * _a[0]; P0[_i, 1] += _a[1]; P0[_i, 2] += _a[2]

P = deform(P0); T = idx.reshape(-1, 3).astype(int)
# pesos: a manga inteira segue só o osso do braço (10 = upperarm_l, 14 = upperarm_r)
ws = sleeve_w(P0)
_ax0, _t0, _pr0, _r0 = frame(P0)
GUS = float(os.environ.get('GUS', '0.75'))
wsw = ws * (1 - GUS * sm(0.5, 4.0, -_pr0[:, 1]) * (1 - sm(14, 26, _t0)) * sm(-2, 4, _t0))   # Etapa 32: sovaco acompanha o tronco
BI = r['bi'].astype(int); BW = r['bw'].astype(float) / 255.0
BI2 = BI.copy(); BW2 = BW.copy()
for v in np.where(wsw > 0)[0]:
    ub = 10 if P0[v, 0] > 0 else 14
    ids = list(BI[v]); w = list(BW[v] * (1 - wsw[v]))
    if ub in ids: w[ids.index(ub)] += wsw[v]
    else:
        k = int(np.argmin(w)); ids[k] = ub; w[k] = wsw[v]
    w = np.array(w); w /= w.sum(); BI2[v] = ids; BW2[v] = w
r['bi'] = BI2.astype(np.uint8)
q = np.round(BW2 * 255).astype(int); q[np.arange(len(q)), q.argmax(1)] += 255 - q.sum(1); r['bw'] = q.astype(np.uint8)
# ---- contorno liso do corpo (superelipse) com folga contra as calças: sem calombos
import glob
ZC = 2.0
YB = np.arange(70, 131, 2.0)
def smooth1(v, k=4):
    out = v.copy()
    for i in range(len(v)):
        lo, hi = max(0, i - k), min(len(v), i + k + 1); out[i] = v[lo:hi].mean()
    return out
def ext(Q, m):
    ax_, bf_, bb_ = np.zeros(len(YB)), np.zeros(len(YB)), np.zeros(len(YB))
    for i, y0 in enumerate(YB):
        mm = m & (np.abs(Q[:, 1] - y0) < 2.0)
        if mm.any():
            ax_[i] = np.abs(Q[mm, 0]).max(); bf_[i] = (Q[mm, 2] - ZC).max(); bb_[i] = (ZC - Q[mm, 2]).max()
    return ax_, bf_, bb_
torso = (ws < 0.02) & (np.abs(P[:, 0]) < 30)
sa, sf_, sb = ext(P, torso & (P[:, 1] < 131))
pa, pf, pb = np.zeros(len(YB)), np.zeros(len(YB)), np.zeros(len(YB))
for f in glob.glob(os.path.join(SRC, 'p_bottom_*.bin')) :
    nm = os.path.basename(f)[2:-4]
    if any(k in nm for k in ('skirt', 'bikini', 'underwear', 'dress')): continue
    q, _, _, _ = load(nm); Q = q['pos'].astype(float)
    ea, ef, eb = ext(Q, (np.abs(Q[:, 0]) < 40) & (Q[:, 1] < 114))
    pa, pf, pb = np.maximum(pa, ea), np.maximum(pf, ef), np.maximum(pb, eb)
MG = 2.4
A = smooth1(np.maximum(sa, np.where(pa > 0, pa + MG, 0)), 3)
BF = smooth1(np.maximum(sf_, np.where(pf > 0, pf + MG, 0)), 3)
BB = smooth1(np.maximum(sb, np.where(pb > 0, pb + MG, 0)), 3)
# caimento reto: do peito para baixo a largura nunca diminui (sem "cintura")
def down_max(v): return np.maximum.accumulate(v[::-1])[::-1]
A, BF, BB = [smooth1(down_max(v), 2) for v in (A, BF, BB)]
# o corpo não encolhe: pelo menos o tamanho da malha alargada; a transição ombro->corpo vem de smooth1
yy = P[:, 1]
a_ = np.interp(yy, YB, A); bf_v = np.interp(yy, YB, BF); bb_v = np.interp(yy, YB, BB)
bz = np.where(P[:, 2] - ZC >= 0, bf_v, bb_v)
th = np.arctan2(P[:, 2] - ZC, P[:, 0]); rr = np.hypot(P[:, 0], P[:, 2] - ZC)
NSE = 3.2
c, sn = np.abs(np.cos(th)) / np.maximum(a_, 1e-3), np.abs(np.sin(th)) / np.maximum(bz, 1e-3)
rt = (c ** NSE + sn ** NSE) ** (-1.0 / NSE)
tor = (1 - ws) * (1 - sm(118, 130, yy)) * (1 - sm(0.5, 0.0, a_ * 0 + 1) * 0)
wb = 0.9 * tor
rn_ = rr + wb * (rt - rr)
P = P.copy(); P[:, 0] = np.cos(th) * rn_ ; P[:, 2] = ZC + np.sin(th) * rn_
P[:, 0] = np.where(np.abs(P[:, 0]) < 1e-6, 0, P[:, 0]) * 1.0
# dobras suaves e discretas
fold = 0.6 * np.sin(th * 6 + 0.7) * sm(126, 92, yy) * (1 - ws)
P[:, 0] += np.cos(th) * fold; P[:, 2] += np.sin(th) * fold
# Etapa 31: sem dobras no ombro: suavização (Laplaciano) só na junção ombro/manga, preservando gola, barra e boca da manga
_k = np.round(P, 3); _u, _inv = np.unique(_k, axis=0, return_inverse=True); _inv = _inv.ravel(); _nu = len(_u)
_nb = [set() for _ in range(_nu)]
for a_, b_, c_ in T:
    for u_, v_ in ((a_, b_), (b_, c_), (c_, a_)):
        _nb[_inv[u_]].add(_inv[v_]); _nb[_inv[v_]].add(_inv[u_])
_ax, _t, _pr, _r = frame(P0)
_msk_u = np.zeros(_nu)
_mv = sm(112, 124, P0[:, 1]) * sm(5, 11, _ax) * (1 - sm(18, 30, _t)) * (1 - sm(146, 152, P0[:, 1]))
np.maximum.at(_msk_u, _inv, _mv)
_Pu = np.zeros((_nu, 3)); _Pu[_inv] = P
for _ in range(10):
    _new = _Pu.copy()
    for i_ in range(_nu):
        if _msk_u[i_] > 0 and _nb[i_]:
            _new[i_] = _Pu[i_] + 0.6 * _msk_u[i_] * (_Pu[list(_nb[i_])].mean(0) - _Pu[i_])
    _Pu = _new
P = _Pu[_inv]
# Etapa 32b: o topo do ombro da camisa ficava colado no corpo (mesma superfície): a pele furava o tecido. Sobe ~1 cm só no ombro (não na gola)
_w = sm(134, 141, P[:, 1]) * sm(7, 11, np.abs(P[:, 0])) * (1 - sm(26, 34, np.abs(P[:, 0])))
_rx = P[:, 0]; _rz = P[:, 2] - 2.0; _rl = np.maximum(np.hypot(_rx, _rz), 1e-6)
P[:, 1] += 1.0 * _w; P[:, 0] += 0.6 * _w * _rx / _rl; P[:, 2] += 0.6 * _w * _rz / _rl
# normais suaves (soldando vértices de mesma posição)
key = np.round(P, 3); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
acc = np.zeros((inv.max() + 1, 3))
for k in range(3): np.add.at(acc, inv[T[:, k]], fn)
N = acc[inv]; N /= np.maximum(np.linalg.norm(N, axis=1), 1e-9)[:, None]
if (N * r['nor'].astype(float)).sum(1).mean() < 0: N = -N
# UV planar nas costas; o resto aponta para um pixel sem estampa
TW, TH = 1024, 1536; BWc, BHc = 36.0, 54.0; YT = 148.0
back = N[:, 2] < -0.15
uv = np.stack([np.clip(0.5 + P[:, 0] / BWc, 0, 1), np.clip((YT - P[:, 1]) / BHc, 0, 1)], 1)
fr = np.array([0.02, 0.02]); uv[~back] = fr
ptri = back[T].all(1)
nvo = len(P)
Pn = np.concatenate([P, P]); Nn = np.concatenate([N, N]); UVn = np.concatenate([uv, np.tile(fr, (nvo, 1))])
Tn = T.copy(); Tn[~ptri] += nvo
used = np.unique(Tn); remap = -np.ones(len(Pn), int); remap[used] = np.arange(len(used))
Pn, Nn, UVn = Pn[used], Nn[used], UVn[used]; Tn = remap[Tn]
src = np.concatenate([np.arange(nvo), np.arange(nvo)])[used]
r2 = np.zeros(len(Pn), REC)
for f in ('bi', 'bw'): r2[f] = r[f][src]
r2['pos'] = Pn; r2['nor'] = Nn; r2['uv'] = UVn.astype(np.float32); r2['col'] = 255
idx2 = Tn.astype('<u2').ravel()
os.makedirs(OUT, exist_ok=True)
_bb = open(os.path.join(SRC, 'base.bin'), 'rb').read(); _nvb, _nib = struct.unpack_from('<2i', _bb, 4)
_bp = np.frombuffer(_bb, np.dtype([('pos', '<f4', 3), ('r', 'u1', 32)]), _nvb, 20)['pos'].astype(float)
_bt = np.frombuffer(_bb, '<u2', _nib, 20 + _nvb * 44).astype(int).reshape(-1, 3)
_cen = _bp[_bt].mean(1)
_extra = np.where((np.abs(_cen[:, 0]) > 9) & (np.abs(_cen[:, 0]) < 30) & (_cen[:, 1] > 137) & (_cen[:, 1] < 151))[0]
hide = np.unique(np.concatenate([hide.astype(int), _extra])).astype('<u2')
print('triangulos do corpo escondidos a mais no topo do ombro:', len(_extra))
open(os.path.join(OUT, 'p_top_skatetee.bin'), 'wb').write(b'CUP1' + struct.pack('<3i', len(r2), len(idx2), 1) + r2.tobytes() + idx2.tobytes() + struct.pack('<i', len(hide)) + hide.tobytes())
print('verts', len(r2), 'tris', len(Tn), 'finite', bool(np.isfinite(Pn).all()))

# ---------------------------------------------------------------- textura + máscaras de recolor
SS = 2; W, H = TW * SS, TH * SS
pxcm = TW / BWc * SS
def X(x): return (0.5 + x / BWc) * W
def Y(y): return (YT - y) / BHc * H
def estampa(fg, bg, mode):
    im = Image.new(mode, (W, H), bg); d = ImageDraw.Draw(im)
    def poly(pts, fill): d.polygon([(X(a), Y(b)) for a, b in pts], fill=fill)
    def line(pts, wcm, col): d.line([(X(a), Y(b)) for a, b in pts], fill=col, width=max(1, int(wcm * pxcm)), joint='curve')
    def circ(cx, cy, rr, fill): d.ellipse([X(cx - rr), Y(cy + rr), X(cx + rr), Y(cy - rr)], fill=fill)
    ay = 128.5
    def cr(vw, hw, top, bot, arm, col):
        poly([(-vw, ay + top), (vw, ay + top), (vw, ay + hw), (arm, ay + hw), (arm, ay - hw), (vw, ay - hw), (vw, ay + bot), (-vw, ay + bot),
              (-vw, ay - hw), (-arm, ay - hw), (-arm, ay + hw), (-vw, ay + hw)], col)
    cr(2.3, 2.1, 9.0, -26.0, 11.0, fg); cr(1.8, 1.6, 8.4, -25.4, 10.4, bg); cr(1.3, 1.1, 7.8, -24.8, 9.8, fg); cr(0.8, 0.6, 7.2, -24.2, 9.2, bg)
    for (px, py) in [(0, ay + 9), (0, ay - 26), (-11, ay), (11, ay)]:
        circ(px, py, 2.6, fg); circ(px, py, 1.9, bg); circ(px, py, 1.2, fg); circ(px, py, 0.6, bg)
    circ(0, ay, 4.0, fg); circ(0, ay, 3.3, bg); circ(0, ay, 2.4, fg); circ(0, ay, 1.5, bg); circ(0, ay, 0.7, fg)
    for yy in (ay - 9, ay - 16):
        poly([(0, yy + 2.2), (1.6, yy), (0, yy - 2.2), (-1.6, yy)], fg); poly([(0, yy + 1.2), (0.8, yy), (0, yy - 1.2), (-0.8, yy)], bg)
    for xx, ln in [(-1.2, 5), (0.9, 9), (1.8, 3.5)]:
        line([(xx, ay - 26), (xx, ay - 26 - ln)], 0.5, fg); circ(xx, ay - 26 - ln, 0.5, fg)
    for xx, ln in [(-9.5, 3.5), (-6.5, 2), (9, 4.5), (6.8, 2.2)]:
        line([(xx, ay - 2.1), (xx, ay - 2.1 - ln)], 0.42, fg); circ(xx, ay - 2.1 - ln, 0.42, fg)
    for xx, ln in [(-3.5, 2.0), (4.0, 1.5)]:
        line([(xx, ay + 9), (xx, ay + 9 - ln)], 0.3, fg)
    return im
mask = estampa(255, 0, 'L').resize((TW, TH), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.3))
a = np.array(mask).astype(float) / 255.0
a[:3] = 0; a[-3:] = 0; a[:, :3] = 0; a[:, -3:] = 0
DARK = np.array([22.0, 22.0, 24.0]); CREAM = np.array([214.0, 204.0, 160.0])
rgb = DARK[None, None, :] * (1 - a[..., None]) + CREAM[None, None, :] * a[..., None]
Image.fromarray(np.round(rgb).astype(np.uint8)).save(os.path.join(OUT, 'skatetee.png'), optimize=True)
# recolor.png: R = peso do slot 0 (camisa), G = peso do slot 1 (estampa), B = id da região (1)
rc = np.zeros((TH, TW, 3), np.uint8)
rc[..., 0] = np.round((1 - a) * 255); rc[..., 1] = np.round(a * 255); rc[..., 2] = 1
Image.fromarray(rc).save(os.path.join(OUT, 'skatetee_recolor.png'), optimize=True)
Image.fromarray(np.full((TH, TW, 3), 128, np.uint8)).save(os.path.join(OUT, 'skatetee_recolor_s.png'), optimize=True)
open(os.path.join(OUT, 'skatetee_recolor.txt'), 'w').write('# id|nome|slot0|slot1|ref0 (sRGB 0..255)|ref1\n1|camiseta|4|5|22.0 22.0 24.0|214.0 204.0 160.0\n')
print('textura ok')
