#!/usr/bin/env python3
"""Etapa 41: converte LeahLillith_FayeHair_001.package (Sims 4) -> p_hairback_faye.bin + faye.png + icone.
Uso: python3 etapa41_faye.py <pacote> <assets/cute>   (dbpf.py, geom.py, rle2.py na mesma pasta)
Franja/topo = GEOM 805EC934 (LOD0), trança = 8037F206. Escala uniforme S, topo ancorado em TOP.
Etapa 41 (ajuste 6): (1) o cabelo e encaixado na cabeca real do app (deslocamento radial suave, preserva as mechas);
(2) o Sims pinta o couro cabeludo da propria cabeca da cor do cabelo e a malha do mod nao tem calota: geramos um couro
cabeludo liso colado na cabeca (textura original, ladrilho denso), sem ele sobravam so mechas finas franzidas e furos.
Precisa de base.bin na pasta de saida (assets/cute)."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import collections
from PIL import Image
from scipy import ndimage
from dbpf import read_index, get
from geom import parse_geom, arrays
from rle2 import rle2_mip0
S, TOP, TZ, TOP_S4 = 1.4, 180.0, 1.5, 186.5

C0 = np.array([0.0, 162.0, 2.5]); NA, NE = 48, 24
def read_base(path):
    b = open(path, 'rb').read(); nv, ni = struct.unpack('<2i', b[4:12])
    dt = np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)])
    r = np.frombuffer(b, dt, nv, 20); idx = np.frombuffer(b, '<u2', ni, 20 + nv*dt.itemsize).astype(np.int64)
    return r['pos'].astype(np.float64), r['nor'].astype(np.float64), idx.reshape(-1, 3)
def dirbins(V):
    d = V - C0; r = np.linalg.norm(d, axis=1) + 1e-9
    az = np.arctan2(d[:, 0], d[:, 2]); el = np.arcsin(np.clip(d[:, 1]/r, -1, 1))
    return r, np.clip(((az+np.pi)/(2*np.pi)*NA).astype(int), 0, NA-1), np.clip(((el+np.pi/2)/np.pi*NE).astype(int), 0, NE-1)
def smooth(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1); return t*t*(3-2*t)
def shift_field(H, cap, off=1.0, smax=6.0, smin=-3.0):
    """quanto puxar o cabelo (ao longo do raio, a partir do centro da cabeca) para ele encostar na pele; campo suave por direcao"""
    rh, ia, ie = dirbins(H); Rh = np.full((NA, NE), np.nan)
    for a, e, r in zip(ia, ie, rh):
        if np.isnan(Rh[a, e]) or r > Rh[a, e]: Rh[a, e] = r
    rc, ja, je = dirbins(cap); bk = collections.defaultdict(list)
    for a, e, r in zip(ja, je, rc): bk[(a, e)].append(r)
    Rc = np.full((NA, NE), np.nan)
    for (a, e), v in bk.items():
        if len(v) >= 3: Rc[a, e] = np.percentile(v, 10)
    S = np.clip(Rc - Rh - off, smin, smax); ok = ~np.isnan(S); S0 = np.where(ok, S, 0.0)
    num = ndimage.gaussian_filter(S0, 1.6, mode=('wrap', 'nearest')); den = ndimage.gaussian_filter(ok.astype(float), 1.6, mode=('wrap', 'nearest'))
    return np.where(den > 0.05, num/np.maximum(den, 1e-6), 0.0) * np.clip(den/0.5, 0, 1)
def fit_to_head(P, F, y0=140.0, y1=156.0):
    d = P - C0; r = np.linalg.norm(d, axis=1) + 1e-9; _, ia, ie = dirbins(P)
    return C0 + d*((r - F[ia, ie]*smooth(y0, y1, P[:, 1]))/r)[:, None]
def scalp(bpos, bnor, bidx, off=1.2):
    """couro cabeludo: pedaco da propria malha da cabeca (y alto), um pouco inflado; UV no ladrilho denso (x 60..210, y 110..520 da textura)"""
    m = (bpos[:, 1] >= 156) & (np.abs(bpos[:, 0]) < 13) & ((bpos[:, 2] <= 6) | (bpos[:, 1] >= 172)) & ((np.abs(bpos[:, 0]) <= 8.5) | (bpos[:, 1] >= 167))   # sem orelhas/laterais baixas (as cartas laterais cobrem)
    tri = bidx[m[bidx].all(1)]; used = np.unique(tri); remap = -np.ones(len(bpos), np.int64); remap[used] = np.arange(len(used))
    P = bpos[used] + bnor[used]*off; N = bnor[used]
    d = P - C0; r = np.linalg.norm(d, axis=1) + 1e-9; th = np.arccos(np.clip(d[:, 1]/r, -1, 1)); az = np.arctan2(d[:, 0], d[:, 2])
    thm = th.max() + 1e-6
    u = (60 + 150*(np.abs(az)/np.pi)) / 1024.0                 # espelhado no plano central: sem emenda
    v = (110 + 410*(th/thm)) / 1024.0                          # raiz escura no alto, mais clara para baixo
    return P, N, np.stack([u, v], 1), remap[tri]
def main(pkg, out):
    d, ents = read_index(pkg)
    gm = {e['group']: e for e in ents if e['type'] == 0x015A1849}
    parts = [arrays(parse_geom(get(d, gm[g]))) for g in (0x805EC934, 0x8037F206)]
    pos = np.vstack([p[0] for p in parts]).astype(np.float64) * 100
    nor = np.vstack([p[1] for p in parts]).astype(np.float64)
    uv = np.vstack([p[2] for p in parts]).astype(np.float64)
    n0 = len(parts[0][0]); idx = np.vstack([parts[0][5], parts[1][5] + n0]).reshape(-1)
    P = np.stack([pos[:, 0]*S, TOP + S*(pos[:, 1]-TOP_S4), TZ + S*pos[:, 2]], 1)
    nor /= np.maximum(np.linalg.norm(nor, axis=1, keepdims=True), 1e-9)
    UV = np.stack([uv[:, 0]*2, uv[:, 1]*4], 1)          # a textura usa só o canto 0..0.5 x 0..0.25
    bpos, bnor, bidx = read_base(os.path.join(out, 'base.bin'))
    H = bpos[(bpos[:, 1] >= 146) & (np.abs(bpos[:, 0]) < 13)]
    cap = P[:n0]; F = shift_field(H, cap[cap[:, 1] > 150])
    P = fit_to_head(P, F)                                    # encaixe na cabeca do app
    nor0 = nor
    sp, sn, suv, stri = scalp(bpos, bnor, bidx)
    ns = len(sp); base_n = len(P)
    P = np.vstack([P, sp]); nor = np.vstack([nor, sn]); UV = np.vstack([UV, suv])
    idx = np.concatenate([idx, (stri + base_n).reshape(-1)])
    n = len(P)
    r = np.zeros(n, np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)]))
    r['pos'] = P; r['nor'] = nor; r['uv'] = np.clip(UV, 0, 1); r['col'] = 255
    t = np.clip((150.0 - P[:, 1]) / 10.0, 0, 1)         # acima de 150: cabeça (osso 8); abaixo de 140: peito (osso 4)
    w1 = np.round(t*255).astype(np.uint8)
    r['bi'][:, 0] = 8; r['bi'][:, 1] = 4; r['bw'][:, 0] = 255 - w1; r['bw'][:, 1] = w1
    with open(os.path.join(out, 'p_hairback_faye.bin'), 'wb') as f:
        f.write(b'CUP1' + struct.pack('<3i', n, len(idx), 0)); f.write(r.tobytes()); f.write(idx.astype('<u2').tobytes())
    tex = {e['inst']: e for e in ents if e['type'] == 0x3453CF95}[0x8E92139C4D019447]
    im = np.asarray(rle2_mip0(get(d, tex))).copy()[:1024, :1024]
    a = im[..., 3]; solid = a >= 100   # textura ORIGINAL do mod: so a cor das bordas e estendida p/ o transparente
    ii = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    im[..., :3] = im[..., :3][ii[0], ii[1]]             # cor das bordas para dentro do transparente (sem halo cinza)
    Image.fromarray(im).save(os.path.join(out, 'faye.png'), optimize=True)
    print(n, 'vertices', len(idx)//3, 'tris', P.min(0).round(1), P.max(0).round(1))
if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
