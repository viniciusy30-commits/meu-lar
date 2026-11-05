#!/usr/bin/env python3
"""Etapa 86: clipe 8 = Interagir (Interact da Universal Animation Library) — o personagem estica o braço e mexe na peça
(abrir porta/gaveta, ligar aparelho). Lê clips_<g>.bin (8 clipes), mantém os 8 byte a byte e acrescenta o 9º.
Uso: python3 etapa86_interagir.py <assets/cute> <UAL1_Standard.glb> [grupos...] [--out <pasta>]
"""
import sys, os
_here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, _here)
argv0 = list(sys.argv)
import numpy as np
import etapa53_animacoes_ual as A
import etapa83_sentar as S
sys.argv = argv0

if __name__ == '__main__':
    args = sys.argv[1:]; cu = args[0].rstrip('/') + '/'; rest = args[2:]; out = cu
    if '--out' in rest:
        i = rest.index('--out'); out = rest[i + 1].rstrip('/') + '/'; rest = rest[:i] + rest[i + 2:]
    os.makedirs(out, exist_ok=True)
    ratios = A.read_ratios(); src = A.Source(A.UAL)
    for g in rest or A.GROUPS_ALL:
        body = A.recover_joints(g, ratios); sc = body['sc']; v = body['v']; nb = body['nb']
        bi = v['bi'].astype(int); bw = v['bw'].astype(float); rest_m = v['pos'].astype(np.float64) / sc
        H = rest_m[:nb, 1].max(); sole = np.nonzero(rest_m[:, 1] < 0.04 * H)[0]
        old = S.read_clips(cu + 'clips_%s.bin' % g)
        assert len(old) == 8, 'clips_%s.bin deveria ter 8 clipes (etapa 83)' % g
        rt = A.Retarget(src, body, S.PAR, 'Interact', 30)
        cl = A.build_clip(src, rt, body, 'Interact', 30, sole, bi, bw, rest_m)
        M = cl['M'].copy(); M[:, :, 1, 3] -= cl['sole_y'].min()
        Mo = M.copy(); Mo[:, :, :, :3] *= A.K; Mo[:, :, :, 3] *= sc * A.K
        final = [(ln, d) for ln, d in old] + [(cl['dur'], Mo.reshape(len(M), 55, 12).astype(np.float32))]
        A.E.write_clips(out + 'clips_%s.bin' % g, final)
        print(g, 'interagir %.2f s, %d quadros' % (cl['dur'], len(M)), flush=True)
