"""Etapa 50: tabela de pontos de referencia (esqueleto + busto) de cada corpo do Sims 3, para os sliders de corpo.
Gera assets/cute/bodyrig.txt, uma linha por corpo:  chave|v0,v1,...  (cm, mesmo referencial da malha p_body_*.bin)
Ordem dos 23 valores (ver BodyMorph.RIG_N):
  0-2 ombro (upperarm_l)  3-5 cotovelo (lowerarm_l)  6-8 punho (hand_l)  9-11 quadril (thigh_l)  12-14 joelho (calf_l)
  15-17 tornozelo (foot_l)  18 y topo do peito (spine_05)  19 y base do pescoco (neck_02)  20 y junta da cabeca (head)
  21 z central do tronco (cintura)  22 y do topo da cabeca
  (o busto, a barriga etc. sao calculados no app a partir destes pontos: ver BodyMorph.warpSim)
Uso: python3 etapa50_rig_sliders.py <assets/cute>
"""
import sys, os, struct
CU = sys.argv[1].rstrip('/') + '/'
os.environ['BASE_BIN'] = CU + 'base.bin'
sys.argv = [sys.argv[0], CU]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'etapa48_jovem.py')).read().split('def run(')[0]
exec(src)   # read_piece, read_clips, recover_Q, sc_of, R (etapa45_rig), CU
ratios = {}
for ln in open(CU + 'pieces.txt'):
    p = ln.strip().split('|')
    if p[0] == 'body' and len(p) > 4 and p[1].startswith('S_'): ratios[p[1][2:]] = float(p[4])
# As juntas recuperadas dos clipes estao numa escala propria de cada grupo; a escala certa (cm da malha) sai de uma regressao:
# centroide dos vertices de cada osso (pesos de pele) ~ ponto medio do segmento do osso (coxa, canela, braco, antebraco).
PAIRS = [('thigh_l', 'calf_l'), ('calf_l', 'foot_l'), ('upperarm_l', 'lowerarm_l'), ('lowerarm_l', 'hand_l')]
def calibrate(Q, P, bi, bw):
    num = den = 0.0
    for a, b in PAIRS:
        ia = R.BI[a]; w = np.zeros(len(P))
        for k in range(4): w += np.where(bi[:, k] == ia, bw[:, k], 0)
        if w.sum() < 1: continue
        cen = (P * w[:, None]).sum(0) / w.sum(); mid = (Q[ia] + Q[R.BI[b]]) / 2
        num += cen[1] * mid[1]; den += mid[1] ** 2
    return num / den
GROUPS = {}
for g in ['af', 'tf', 'ef', 'am', 'tm', 'em', 'cu', 'pu']:
    Q = recover_Q(read_clips(CU + 'clips_%s.bin' % g)) * sc_of(ratios[g + '1']) / 100.0
    v, idx, fl, tail = read_piece(CU + 'p_body_%s1.bin' % g)
    GROUPS[g] = Q * calibrate(Q, v['pos'].astype(np.float64), v['bi'], v['bw'] / 255.0)
def J(Q, n): return Q[R.BI[n]]
lines = []
for key in sorted(ratios):
    g, t = key[:2], key[2]
    Q = GROUPS[g]
    v, idx, fl, tail = read_piece(CU + 'p_body_%s.bin' % key)
    P = v['pos'].astype(np.float64); bi = v['bi']; bw = v['bw'] / 255.0
    def wsum(ids):
        m = np.zeros(len(P))
        for k in range(4): m += np.where(np.isin(bi[:, k], ids), bw[:, k], 0)
        return m
    arm = wsum(list(range(9, 17)) + list(range(25, 55)))
    hipY = J(Q, 'thigh_l')[1]; topY = J(Q, 'spine_05')[1]
    wy = hipY + 0.58 * (topY - hipY)
    m = (np.abs(P[:, 1] - wy) < 2.5) & (arm < 0.3)
    zc = 0.5 * (P[m, 2].max() + P[m, 2].min()) if m.sum() else 0.0
    r = list(J(Q, 'upperarm_l')) + list(J(Q, 'lowerarm_l')) + list(J(Q, 'hand_l')) + list(J(Q, 'thigh_l')) + list(J(Q, 'calf_l')) + list(J(Q, 'foot_l'))
    r += [topY, J(Q, 'neck_02')[1], J(Q, 'head')[1], zc, float(P[:, 1].max())]
    lines.append(key + '|' + ','.join('%.2f' % x for x in r))
    print(key, 'hipY %.1f waistY %.1f topY %.1f zc %.1f' % (hipY, wy, topY, zc))
open(CU + 'bodyrig.txt', 'w').write('\n'.join(lines) + '\n')
print(len(lines), 'corpos ->', CU + 'bodyrig.txt')
