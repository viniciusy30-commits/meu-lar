#!/usr/bin/env python3
"""Etapa 52: esqueleto ORIGINAL do Sims 3 (auRig/cuRig/puRig.grannyrig, pacote Blender GEOM Tools de SmugTomato, GPL).
Uso: python3 etapa52_esqueleto_original.py <pasta com os .grannyrig> <pasta com bodies/ (OBJ)> <assets/cute>
Gera skel_au/cu/pu.txt (todos os 257 ossos, posicao no mundo, metros) e bodyrig.txt (juntas reais x escala de cada corpo).
Ver sims3_rig_tools.py (leitor do formato .grannyrig)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sims3_rig_tools as T
import numpy as np
RIGDIR, BODIES, CU = [a.rstrip('/') + '/' for a in sys.argv[1:4]]
BODY = {'af': 'afBody_fit', 'am': 'amBody_fit', 'tf': 'tfBody_fit', 'tm': 'tmBody_fit', 'ef': 'efBody', 'em': 'emBody', 'cu': 'cuBody', 'pu': 'puBody'}
RIG = {'a': 'auRig', 't': 'auRig', 'e': 'auRig', 'c': 'cuRig', 'p': 'puRig'}
old = {}
for l in open(CU + 'bodyrig.txt'):
    k, v = l.strip().split('|'); old[k] = [float(x) for x in v.split(',')]
out = []
for k in sorted(old):
    g = k[:2]; H = T.objmax(BODIES + BODY[g] + '.obj')[:, 1].max()
    W = T.world(T.load(RIGDIR + RIG[g[0]] + '.grannyrig')); s = 100 / (H / 1.675) * 0.968
    j = lambda n: W[n] * s
    r = [*j('b__L_UpperArm__'), *j('b__L_Forearm__'), *j('b__L_Hand__'), *j('b__L_Thigh__'), *j('b__L_Calf__'), *j('b__L_Foot__'),
         j('b__Spine2__')[1], j('b__Neck__')[1], j('b__Head__')[1], old[k][21], old[k][22]]
    out.append(k + '|' + ','.join('%.2f' % x for x in r))
open(CU + 'bodyrig.txt', 'w').write('\n'.join(out) + '\n')
for nm, lab in [('auRig', 'adulto'), ('cuRig', 'crianca'), ('puRig', 'bebe')]:
    bs = T.load(RIGDIR + nm + '.grannyrig'); W = T.world(bs)
    L = ['# Esqueleto original do The Sims 3 (%s). Metros, referencial das malhas OBJ.' % lab, '# indice|osso|pai|x|y|z']
    L += ['%d|%s|%d|%.5f|%.5f|%.5f' % (i, b['name'], b['par'], *W[b['name']]) for i, b in enumerate(bs)]
    open(CU + 'skel_%s.txt' % nm[:2], 'w').write('\n'.join(L) + '\n')
print('ok')
