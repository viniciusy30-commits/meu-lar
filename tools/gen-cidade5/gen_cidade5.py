#!/usr/bin/env python3
"""ETAPA A (v2 organica): python3 gen_cidade5.py [pasta]  -> city5_roads.json + preview_A.png + relatorio"""
import json, sys, os, time
import numpy as np
from PIL import ImageDraw
import geo as G, assemble, validate2, preview2
from plan import *

out = sys.argv[1] if len(sys.argv) > 1 else 'out'
os.makedirs(out, exist_ok=True)
t = time.time()
geo = G.Geo(); c = assemble.build(geo)
res = validate2.run_all(c, geo); allok = True
for name, ok, msgs in res:
    print(('PASSOU ' if ok else 'FALHOU ') + name)
    for m in msgs: print('   ' + m)
    allok &= ok
import terrain_final as T
hf, ynode, X8, Z8 = T.run(c, geo)
ok_b, msg_b = validate2.v_final(c, hf, ynode)
print(('PASSOU ' if ok_b else 'FALHOU ') + 'ETAPA B: terreno final e terraplenagem')
for m in msg_b: print('   ' + m)
allok &= ok_b
T.write_bin(hf, os.path.join(out, 'relevo5.bin'))
KIND = ['ave', 'col', 'loc', 'hwy']
data = {'world': [WX, WZ], 'lagoon': list(LAGOON), 'channels': [CHANNEL_W, CHANNEL_E], 'river': RIVER, 'red_bridges': c.red,
        'rounds': [{'x': r['x'], 'z': r['z'], 'r': r['r']} for r in c.rounds],
        'nodes': [{'x': round(n[0], 2), 'z': round(n[1], 2), 'kind': 'lookout' if i in c.lookouts else (c.legit[i] if i in c.legit else 'junction')} for i, n in enumerate(c.nodes)],
        'edges': [{'a': e['a'], 'b': e['b'], 'cls': KIND[e['lvl']], 'c': LEVELS[min(e['lvl'], 2)][1] if e['lvl'] < 3 else 0, 'kind': e['kind'], 'name': e['name'],
                   'p': [[round(q[0], 1), round(q[1], 1), round(q[2], 2)] for q in T.profile_pts(e, ynode[e['a']], ynode[e['b']])]} for e in c.edges]}
json.dump(data, open(os.path.join(out, 'city5_roads.json'), 'w'), separators=(',', ':'))
np.save(os.path.join(out, 'height16.npy'), geo.h.astype(np.float32))
import types
im = preview2.terrain_img(types.SimpleNamespace(h=hf), 0.3, cell=8.0)
E2 = [{'p': e['p'], 'cls': KIND[e['lvl']], 'kind': e['kind']} for e in c.edges]
N2 = [{'x': c.nodes[i][0], 'z': c.nodes[i][1], 'kind': c.legit[i]} for i in c.legit] + [{'x': c.nodes[i][0], 'z': c.nodes[i][1], 'kind': 'lookout'} for i in c.lookouts]
im = preview2.draw_roads(im, E2, N2, 0.3, c.rounds)
d = ImageDraw.Draw(im)
for r in c.red:   # pontes vermelhas: so cenario
    xa, xb = sorted((r['x_a'], r['x_b']))
    d.line([(xa * 0.3, r['z'] * 0.3), (xb * 0.3, r['z'] * 0.3)], fill=(225, 30, 30), width=5)
    for tx in r['towers']: d.rectangle([tx * 0.3 - 3, r['z'] * 0.3 - 9, tx * 0.3 + 3, r['z'] * 0.3 + 9], fill=(255, 90, 40))
    px, pz = r['portal']; d.ellipse([px * 0.3 - 5, pz * 0.3 - 5, px * 0.3 + 5, pz * 0.3 + 5], fill=(40, 40, 40), outline=(255, 255, 255))
for nm, (x, z) in PLACES.items(): d.text((x * 0.3 - 30, z * 0.3 - 5), nm, fill=(255, 255, 255))
d.text((8, 6), f'MEULAR CITY v2 - ETAPA A - mundo {WX:.0f}x{WZ:.0f} m (1 px = 3,3 m) - {len(c.edges)} trechos, {len(c.nodes)} nos', fill=(255, 255, 255))
d.text((8, 20), 'amarelo = bolsao de retorno | ciano = fim na praia/cais | magenta = mirante da ponte (cancela) | ponte vermelha = SO VISUAL (sem acesso)', fill=(255, 255, 255))
im.save(os.path.join(out, 'preview_A.png'))
print(f'ETAPA A v2: {"TODOS OS VALIDADORES VERDES" if allok else "HA VALIDADORES VERMELHOS"}  ({time.time()-t:.1f}s)')
sys.exit(0 if allok else 1)
