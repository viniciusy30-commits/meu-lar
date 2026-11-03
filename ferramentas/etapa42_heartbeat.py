#!/usr/bin/env python3
"""Etapa 42: converte Alesso_Heartbeat.sims3pack (Sims 3, cabelo longo liso com franja) -> p_hairback_heartbeat.bin + heartbeat.png.
Uso: python3 etapa42_heartbeat.py <pacote.sims3pack> <assets/cute>   (dbpf.py, geom.py, refpack.py na mesma pasta; base.bin em assets/cute)
- Malha LOD0 (GEOM 1A1932736124F822) sem alterar a forma: so escala uniforme e posicao (ajuste rigido medido contra a cabeca do app),
  mais um campo radial suave (como o Faye) e um empurrao para fora onde o cabelo entrava no corpo (ombros/peito).
- Cores: o Sims 3 pinta o cabelo com um mapa de controle (R=raiz, G=mecha clara, B=pontas); aqui as cores do preset sao "assadas" na textura (ombre castanho/loiro).
- Couro cabeludo: pedaco da cabeca do app, com UV num bloco de cor solida (raiz) da textura: sem furos nem emendas."""
import sys, os, struct, collections, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
from dbpf import read_index, get
from geom import parse_geom
from refpack import refpack

HAIR_LOD0 = 0x1A1932736124F822
TEX = {'diffuse': 0x27DE051809D3BFE6, 'control': 0x6F19D3FD094E0F22}
# ajuste rigido Sims 3 -> cabeca do app (cm): P = (0,TOPAPP,0) + (X-(0,TOP,0))*S + (0,DY,DZ)
S, TOP, TOPAPP, DY, DZ = 0.896, 188.9, 177.4, -0.7, 2.0
C0 = np.array([0.0, 162.0, 2.5]); NA, NE = 48, 24
# cores do preset (raiz / mecha clara / pontas / base)
ROOT = np.array([0.5529412, 0.4156863, 0.2784314]); HIGH = np.array([0.9647059, 0.8431373, 0.6823530])
TIP = np.array([0.5686275, 0.3803922, 0.2470588]); BASE = np.array([0.8156863, 0.6274510, 0.4627451]); GAIN = 1.3
BLK = (512, 0, 128)   # bloco livre da textura (x, y, lado) para a cor solida do couro cabeludo

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
def shift_field(H, cap, off=0.9, smax=4.0, smin=-4.0):
    rh, ia, ie = dirbins(H); Rh = np.full((NA, NE), np.nan)
    for a, e, r in zip(ia, ie, rh):
        if np.isnan(Rh[a, e]) or r > Rh[a, e]: Rh[a, e] = r
    rc, ja, je = dirbins(cap); bk = collections.defaultdict(list)
    for a, e, r in zip(ja, je, rc): bk[(a, e)].append(r)
    Rc = np.full((NA, NE), np.nan)
    for (a, e), v in bk.items():
        if len(v) >= 3: Rc[a, e] = np.percentile(v, 10)
    F = np.clip(Rc - Rh - off, smin, smax); ok = ~np.isnan(F); F0 = np.where(ok, F, 0.0)
    num = ndimage.gaussian_filter(F0, 1.6, mode=('wrap', 'nearest')); den = ndimage.gaussian_filter(ok.astype(float), 1.6, mode=('wrap', 'nearest'))
    return np.where(den > 0.05, num/np.maximum(den, 1e-6), 0.0) * np.clip(den/0.5, 0, 1)
def fit_to_head(P, F, y0=146.0, y1=162.0):
    d = P - C0; r = np.linalg.norm(d, axis=1) + 1e-9; _, ia, ie = dirbins(P)
    return C0 + d*((r - F[ia, ie]*smooth(y0, y1, P[:, 1]))/r)[:, None]
def push_out(P, bpos, bnor, clear=0.45, iters=6):
    """empurra para fora (ao longo da normal da pele) os vertices que ficaram dentro/colados no corpo (ombros, peito, nuca)"""
    tree = cKDTree(bpos); P = P.copy(); tot = 0
    for _ in range(iters):
        dist, j = tree.query(P, k=4)
        n = bnor[j].mean(1); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        p0 = bpos[j].mean(1); sd = ((P - p0)*n).sum(1)       # distancia assinada (>0 = fora)
        bad = (sd < clear) & (dist[:, 0] < 4.0)
        if not bad.any(): break
        P[bad] += n[bad]*(clear - sd[bad])[:, None]; tot = bad.sum()
    return P, tot
def smooth_disp(P0, P1, idx, it=2, lam=0.5):
    """suaviza so o deslocamento (P1-P0) entre vertices vizinhos: o empurrao nao cria degraus"""
    D = P1 - P0; n = len(P0)
    e = np.vstack([idx[:, [0, 1]], idx[:, [1, 2]], idx[:, [2, 0]]]); e = np.vstack([e, e[:, ::-1]])
    cnt = np.bincount(e[:, 0], minlength=n).astype(float)
    for _ in range(it):
        s = np.zeros_like(D)
        for k in range(3): s[:, k] = np.bincount(e[:, 0], weights=D[e[:, 1], k], minlength=n)
        m = cnt > 0; D[m] = (1-lam)*D[m] + lam*s[m]/cnt[m, None]
    return P0 + D
def scalp(bpos, bnor, bidx, off=1.0):
    m = (bpos[:, 1] >= 156) & (np.abs(bpos[:, 0]) < 13) & ((bpos[:, 2] <= 6) | (bpos[:, 1] >= 172)) & ((np.abs(bpos[:, 0]) <= 8.5) | (bpos[:, 1] >= 167))
    tri = bidx[m[bidx].all(1)]; used = np.unique(tri); remap = -np.ones(len(bpos), np.int64); remap[used] = np.arange(len(used))
    return bpos[used] + bnor[used]*off, bnor[used], remap[tri]
def bake(d, c):
    d = d.astype(np.float64)/255; c = c.astype(np.float64)/255
    w = c[..., :3]; s = w.sum(-1, keepdims=True); w = w/np.maximum(s, 1.0)
    tint = (1-w.sum(-1, keepdims=True))*BASE + w[..., 0:1]*ROOT + w[..., 1:2]*HIGH + w[..., 2:3]*TIP
    rgb = np.clip(d[..., :3]*tint*GAIN, 0, 1)
    return np.dstack([rgb, d[..., 3]])
def main(pkg, out):
    raw = open(pkg, 'rb').read(); p = 4 + struct.unpack('<I', raw[:4])[0] + 2
    p += 4 + struct.unpack('<I', raw[p:p+4])[0]; open(os.path.join(os.path.dirname(os.path.abspath(pkg)), '_hb.package'), 'wb').write(raw[p:]); tmp = os.path.join(os.path.dirname(os.path.abspath(pkg)), '_hb.package')
    d, ents = read_index(tmp); os.remove(tmp)
    def res(e):
        r = d[e['off']:e['off']+e['fsize']]
        return refpack(r)[0] if e['comp'] == 0xffff else r
    g = [e for e in ents if e['type'] == 0x015A1849 and e['inst'] == HAIR_LOD0][0]
    G = parse_geom(res(g)); V = G['verts']
    pos = np.array([struct.unpack('<3f', x) for x in V[(1, 1)]], np.float64)*100
    nor = np.array([struct.unpack('<3f', x) for x in V[(2, 1)]], np.float64)
    uv = np.array([struct.unpack('<2f', x) for x in V[(3, 1)]], np.float64)
    idx = G['idx'].reshape(-1, 3).astype(np.int64)
    P = np.array([0, TOPAPP, 0]) + (pos - np.array([0, TOP, 0]))*S + np.array([0, DY, DZ])
    bpos, bnor, bidx = read_base(os.path.join(out, 'base.bin'))
    H = bpos[(bpos[:, 1] >= 146) & (np.abs(bpos[:, 0]) < 13)]
    F = shift_field(H, P[P[:, 1] > 150]); P1 = fit_to_head(P, F)
    P2, nb = push_out(P1, bpos, bnor)
    P = P2
    # textura: cores do preset assadas; cor das bordas estendida para o transparente (sem halo cinza)
    tx = {e['inst']: e for e in ents if e['type'] == 0x00B2D882}
    dif = np.asarray(Image.open(io.BytesIO(res(tx[TEX['diffuse']]))).convert('RGBA')); ctl = np.asarray(Image.open(io.BytesIO(res(tx[TEX['control']]))).convert('RGBA'))
    tex = (bake(dif, ctl)*255 + 0.5).astype(np.uint8)
    a = tex[..., 3]; solid = a >= 100
    ii = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    tex[..., :3] = tex[..., :3][ii[0], ii[1]]
    # cor do couro cabeludo = media da raiz (topo do cabelo) ja assada
    top = pos[:, 1] > pos[:, 1].max() - 14
    tu = np.clip((uv[top, 0]*1024).astype(int), 0, 1023); tv = np.clip((uv[top, 1]*1024).astype(int), 0, 1023)
    ok = tex[tv, tu, 3] >= 100; rc = tex[tv, tu, :3][ok].astype(float).mean(0)*1.0
    x0, y0, s0 = BLK; assert not (tex[max(y0-24, 0):y0+s0+24, x0-24:x0+s0+24, 3] > 8).any(), 'bloco nao esta livre'
    tex[y0:y0+s0, x0:x0+s0, :3] = np.round(rc).astype(np.uint8); tex[y0:y0+s0, x0:x0+s0, 3] = 255
    Image.fromarray(tex).save(os.path.join(out, 'heartbeat.png'), optimize=True)
    sp, sn, stri = scalp(bpos, bnor, bidx); n0 = len(P)
    suv = np.tile([(x0 + s0/2)/1024.0, (y0 + s0/2)/1024.0], (len(sp), 1))
    P = np.vstack([P, sp]); nor = np.vstack([nor, sn]); UV = np.vstack([uv, suv]); idx = np.concatenate([idx.reshape(-1), (stri + n0).reshape(-1)])
    n = len(P)
    r = np.zeros(n, np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)]))
    r['pos'] = P; r['nor'] = nor; r['uv'] = np.clip(UV, 0, 1); r['col'] = 255
    t = np.clip((150.0 - P[:, 1]) / 10.0, 0, 1); w1 = np.round(t*255).astype(np.uint8)
    r['bi'][:, 0] = 8; r['bi'][:, 1] = 4; r['bw'][:, 0] = 255 - w1; r['bw'][:, 1] = w1
    with open(os.path.join(out, 'p_hairback_heartbeat.bin'), 'wb') as f:
        f.write(b'CUP1' + struct.pack('<3i', n, len(idx), 0)); f.write(r.tobytes()); f.write(idx.astype('<u2').tobytes())
    print(n, 'vertices', len(idx)//3, 'tris', P.min(0).round(1), P.max(0).round(1), 'push_out', nb, 'scalp rgb', rc.round(0))
if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
