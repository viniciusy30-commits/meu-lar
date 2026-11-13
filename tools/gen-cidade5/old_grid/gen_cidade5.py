#!/usr/bin/env python3
"""ETAPA A: python3 gen_cidade5.py [pasta_saida]  -> city5_roads.json + preview_A.png + relatorio dos validadores"""
import json, sys, os
import roads, validate, preview
from plan import *

out = sys.argv[1] if len(sys.argv) > 1 else 'out'
os.makedirs(out, exist_ok=True)
g, lines = roads.build()
roads.finalize(g)
res = validate.run_all(g)
allok = True
for name, ok, msgs in res:
    print(('PASSOU ' if ok else 'FALHOU ') + name)
    for m in msgs: print('   ' + m)
    allok &= ok
data = {'world': [WX, WZ], 'mask': CITY_MASK, 'peninsula': PENINSULA_MASK, 'river': RIVER, 'river_w': RIVER_W,
        'rounds': {k: list(v) for k, v in ROUNDS.items()},
        'nodes': [dict(v) for v in g.nodes.values()],
        'edges': [{'id': e['id'], 'name': e['name'], 'cls': e['cls'], 'c': CLS[e['cls']], 'w': e['w'], 'kind': e['kind'], 'y0': e['y0'], 'y1': e['y1'],
                   'p': [[round(a, 2), round(b, 2)] for a, b in e['pts']]} for e in g.edges]}
with open(os.path.join(out, 'city5_roads.json'), 'w') as f: json.dump(data, f, separators=(',', ':'))
preview.draw(g, os.path.join(out, 'preview_A.png'))
print('ETAPA A:', 'TODOS OS VALIDADORES VERDES' if allok else 'HA VALIDADORES VERMELHOS')
sys.exit(0 if allok else 1)
