#!/usr/bin/env python3
"""Etapa 41: converte LeahLillith_FayeHair_001.package (Sims 4) -> p_hairback_faye.bin + faye.png + icone.
Uso: python3 etapa41_faye.py <pacote> <assets/cute>   (dbpf.py, geom.py, rle2.py na mesma pasta)
Franja/topo = GEOM 805EC934 (LOD0), trança = 8037F206. Escala uniforme S, topo ancorado em TOP; sem deformar o modelo."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from scipy import ndimage
from dbpf import read_index, get
from geom import parse_geom, arrays
from rle2 import rle2_mip0
S, TOP, TZ, TOP_S4 = 1.3, 180.0, 4.0, 186.5
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
    a = im[..., 3]; solid = a >= 100
    ii = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    im[..., :3] = im[..., :3][ii[0], ii[1]]             # cor das bordas para dentro do transparente (sem halo cinza)
    Image.fromarray(im).save(os.path.join(out, 'faye.png'), optimize=True)
    print(n, 'vertices', len(idx)//3, 'tris', P.min(0).round(1), P.max(0).round(1))
if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
