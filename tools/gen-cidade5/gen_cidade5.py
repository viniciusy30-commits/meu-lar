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
KIND = ['ave', 'col', 'loc', 'hwy']
data = {'world': [WX, WZ], 'lagoon': list(LAGOON), 'channels': [CHANNEL_W, CHANNEL_E], 'river': RIVER, 'red_bridges': c.red,
        'rounds': [{'x': r['x'], 'z': r['z'], 'r': r['r']} for r in c.rounds],
        'nodes': [{'x': round(n[0], 2), 'z': round(n[1], 2), 'kind': 'portal' if i in c.portals else ('cul' if i in c.cul else 'junction')} for i, n in enumerate(c.nodes)],
        'edges': [{'a': e['a'], 'b': e['b'], 'cls': KIND[e['lvl']], 'c': LEVELS[min(e['lvl'], 2)][1] if e['lvl'] < 3 else 0, 'kind': e['kind'], 'name': e['name'],
                   'p': [[round(p[0], 1), round(p[1], 1)] for p in e['p']]} for e in c.edges]}
json.dump(data, open(os.path.join(out, 'city5_roads.json'), 'w'), separators=(',', ':'))
np.save(os.path.join(out, 'height16.npy'), geo.h.astype(np.float32))
im = preview2.terrain_img(geo, 0.3)
E2 = [{'p': e['p'], 'cls': KIND[e['lvl']], 'kind': e['kind']} for e in c.edges]
N2 = [{'x': c.nodes[i][0], 'z': c.nodes[i][1], 'kind': 'cul'} for i in c.cul]
im = preview2.draw_roads(im, E2, N2, 0.3, c.rounds)
d = ImageDraw.Draw(im)
for nm, (x, z) in PLACES.items(): d.text((x * 0.3 - 30, z * 0.3 - 5), nm, fill=(255, 255, 255))
d.text((8, 6), f'MEULAR CITY v2 - ETAPA A - mundo {WX:.0f}x{WZ:.0f} m (1 px = 3,3 m) - {len(c.edges)} trechos, {len(c.nodes)} nos', fill=(255, 255, 255))
im.save(os.path.join(out, 'preview_A.png'))
print(f'ETAPA A v2: {"TODOS OS VALIDADORES VERDES" if allok else "HA VALIDADORES VERMELHOS"}  ({time.time()-t:.1f}s)')
sys.exit(0 if allok else 1)
