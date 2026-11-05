#!/usr/bin/env python3
"""Etapa 83: clipes de SENTAR (entrar, sentado em laço, levantar) da Universal Animation Library nos corpos do Sims 3.

Uso: python3 etapa83_sentar.py <assets/cute> <UAL1_Standard.glb> [grupos...] [--out <pasta>]

Lê clips_<g>.bin já existente (5 clipes: parado, andar, pulo, correr, pulo correndo), recalcula SÓ os novos com o
mesmo retarget da Etapa 53 e grava o arquivo com 8 clipes:
  5 Sentar (Sitting_Enter)   6 Sentado (Sitting_Idle_Loop)   7 Levantar (Sitting_Exit)
Os 5 primeiros são copiados byte a byte (nada muda no que já funciona).
Também imprime, por grupo, a altura do assento (ponto mais baixo do quadril/coxas sentado) e o recuo do quadril,
que o jogo usa para alinhar o personagem ao assento (Interact.kt / Sit).
"""
import sys, os, struct
_here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, _here)
argv0 = list(sys.argv)
import numpy as np
import etapa53_animacoes_ual as A          # lê sys.argv[1..2] ao importar
sys.argv = argv0

SIT = [('Sitting_Enter', 30), ('Sitting_Idle_Loop', 30), ('Sitting_Exit', 30)]
APP = 100.0 * A.E.SW * A.K     # metros do OBJ -> unidades do jogo (antes da escala de altura do slider)
PAR = dict(sx=1.0, sz=1.0, sb=1.0, pgain=1.0, trunk=0.0, head=0.0, abd=(None, 1.0), sag=(None, 1.0), rate=1.0)


def read_clips(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'CLP1'
    nb, nc = struct.unpack_from('<2i', b, 4); o = 12; out = []
    for c in range(nc):
        ln, nf = struct.unpack_from('<fi', b, o); o += 8
        d = np.frombuffer(b, '<f4', nf * nb * 12, o).reshape(nf, nb, 12).copy(); o += nf * nb * 12 * 4
        out.append((ln, d))
    return out


def skin(M, rest_m, bi, bw, ids):
    P = np.zeros((len(ids), 3))
    for k in range(4):
        bb = bi[ids, k]; ww = bw[ids, k] / 255.0
        Mb = M[bb]
        P += ww[:, None] * (np.einsum('vij,vj->vi', Mb[:, :, :3], rest_m[ids]) + Mb[:, :, 3])
    return P


def run(src, grp, ratios, cu, out):
    body = A.recover_joints(grp, ratios); sc = body['sc']; v = body['v']; nb = body['nb']
    assert body['wdiff'] < 0.01
    bi = v['bi'].astype(int); bw = v['bw'].astype(float)
    rest_m = v['pos'].astype(np.float64) / sc
    H = rest_m[:nb, 1].max(); sole_ids = np.nonzero(rest_m[:, 1] < 0.04 * H)[0]
    old = read_clips(cu + 'clips_%s.bin' % grp)
    assert len(old) >= 5, 'clips_%s.bin deveria ter 5 clipes' % grp
    built = []
    for anim, fps in SIT:
        rt = A.Retarget(src, body, PAR, anim, fps)
        built.append(A.build_clip(src, rt, body, anim, fps, sole_ids, bi, bw, rest_m))
    low = min(cl['sole_y'].min() for cl in built)      # um único chão para os 3 (entrar -> sentado -> levantar sem salto)
    final = [(ln, d) for ln, d in old[:5]]
    # métricas do assento no quadro do meio do laço sentado
    Ms = built[1]['M'][len(built[1]['M']) // 2].copy(); Ms[:, 1, 3] -= low
    hip_bones = {A.BI[n] for n in ('pelvis', 'thigh_l', 'thigh_r')}
    ids = np.nonzero(np.isin(bi[:nb, 0], list(hip_bones)) & (bw[:nb, 0] > 128))[0]
    P = skin(Ms, rest_m, bi, bw, ids)
    seat_y = P[:, 1].min(); back_z = P[:, 2].min()
    Mr = built[0]['M'][0].copy(); Mr[:, 1, 3] -= low
    P0 = skin(Mr, rest_m, bi, bw, ids)
    for cl in built:
        M = cl['M'].copy(); M[:, :, 1, 3] -= low
        Mo = M.copy(); Mo[:, :, :, :3] *= A.K; Mo[:, :, :, 3] *= sc * A.K
        final.append((cl['dur'], Mo.reshape(len(M), 55, 12).astype(np.float32)))
    A.E.write_clips(out + 'clips_%s.bin' % grp, final)
    hs = ratios[grp + '1']
    print('[%s] sentar %.2fs / laço %.2fs / levantar %.2fs | assento y=%.3f m, traseiro z=%.3f m (em pé: %.3f) | escala %.3f'
          % (grp, built[0]['dur'], built[1]['dur'], built[2]['dur'], seat_y, back_z, P0[:, 2].min(), hs))
    return seat_y * APP, back_z * APP


if __name__ == '__main__':
    args = sys.argv[1:]
    cu = args[0].rstrip('/') + '/'
    rest = args[2:]
    out = cu
    if '--out' in rest:
        i = rest.index('--out'); out = rest[i + 1].rstrip('/') + '/'; rest = rest[:i] + rest[i + 2:]
    os.makedirs(out, exist_ok=True)
    groups = rest or A.GROUPS_ALL
    ratios = A.read_ratios(); src = A.Source(A.UAL)
    rows = []
    for g in groups:
        sy, bz = run(src, g, ratios, cu, out)
        rows.append('%s|%.4f|%.4f' % (g, sy, bz))
    open(out + 'sit.txt', 'w').write('# grupo|altura do assento (m)|recuo do traseiro em relação à raiz (m, z<0 = atrás); multiplicar pela escala de altura do slider\n' + '\n'.join(rows) + '\n')
