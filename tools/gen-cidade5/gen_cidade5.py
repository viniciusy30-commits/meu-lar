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
# ---- ETAPA C: chao (asfalto, guias, calcadas, faixas, cruzamentos, protecoes, pontes)
import ground, validate_ground, render3d, prev_ground, math
t0 = time.time()
gr = ground.Ground(c, geo, hf, ynode); gr.build()
import traffic, furniture, validate_traffic, orla, validate_orla
tr = traffic.Traffic(gr); tr.build_moves(); tr.plan_control(); tr.plan_bumps()
fu = furniture.Furn(gr, tr).build()
gr.fu_poles = list(fu.poles)
o = orla.Orla(gr, geo, hf).build()
ok_o, msg_o = validate_orla.run(gr, o, geo, hf)
print(('PASSOU ' if ok_o else 'FALHOU ') + 'ETAPA C3: orla das praias (calcadao, escadas, pieres)')
for m in msg_o: print(m)
allok &= ok_o
import validate_lots
ok_l, msg_l = validate_lots.run(gr, c.lotplan, c, geo, hf)
print(('PASSOU ' if ok_l else 'FALHOU ') + 'ETAPA D: lotes e as 17 casas')
for m in msg_l: print(m)
allok &= ok_l
ok_c, msg_c = validate_ground.v_ground(gr)
print(('PASSOU ' if ok_c else 'FALHOU ') + f'ETAPA C: chao e protecoes ({time.time()-t0:.1f}s)')
for m in msg_c: print(m)
allok &= ok_c
ok_t, msg_t = validate_traffic.run(gr, tr, fu)
print(('PASSOU ' if ok_t else 'FALHOU ') + 'ETAPA C2: transito e sinalizacao')
for m in msg_t: print(m)
allok &= ok_t
nrec = gr.B.write(os.path.join(out, 'city5_ground.bin'))
json.dump({'fronts': gr.fronts, 'red_bridges': [{k: float(v) if hasattr(v, 'item') or isinstance(v, float) else v for k, v in r.items()} for r in gr.red_info]}, open(os.path.join(out, 'frontages.json'), 'w'), separators=(',', ':'))
# dados de transito e sinalizacao para o jogo (carros, semaforos, placas, lombadas)
lanes = {}
for k, e in enumerate(c.edges):
    lvl = min(e['lvl'], 2)
    lanes[k] = {'lvl': e['lvl'], 'kind': e['kind'], 'speed_kmh': 50 if e['kind'] == 'bridge' else traffic.LANES[lvl]['speed'],
                'fwd_offsets': traffic.lane_offsets(lvl), 'bwd_offsets': [-o for o in traffic.lane_offsets(lvl)], 'drive_side': 'right'}
def rp(P): return [[round(p[0], 1), round(p[1], 1)] for p in P[::2]] if len(P) > 6 else [[round(p[0], 1), round(p[1], 1)] for p in P]
json.dump({'lanes': lanes, 'moves': [{'node': m['node'], 'kind': m['kind'], 'from': list(m['from']), 'to': list(m['to']), 'lane_from': m['lane_from'], 'lane_to': m['lane_to'], 'y': round(m['y'], 2), 'path': rp(m['path'])} for m in tr.moves],
           'control': [{'node': k[0], 'edge': k[1], 'end': k[2], 'type': v} for k, v in tr.control.items()],
           'signals': {str(k): v for k, v in tr.signals.items()}},
          open(os.path.join(out, 'traffic.json'), 'w'), separators=(',', ':'))
fu.atlas.save(os.path.join(out, 'signs_atlas.png'))
json.dump({'atlas': {k: [round(v, 5) for v in uv] for k, uv in fu.atlas.uv.items()}, 'streets': {str(k): v for k, v in fu.street_of.items()}, 'ped_signal_heads': fu.ped_heads, 'signs': fu.signs, 'signal_heads': fu.heads, 'speed_bumps': [{'x': round(b['x'], 2), 'z': round(b['z'], 2), 'y': round(b['y'], 2), 'tx': round(b['tx'], 3), 'tz': round(b['tz'], 3), 'edge': b['k'], 'why': b['why']} for b in tr.bumps]},
          open(os.path.join(out, 'signage.json'), 'w'), separators=(',', ':'))
json.dump(o.items, open(os.path.join(out, 'orla.json'), 'w'), separators=(',', ':'))
# fotos de TODAS as ruas (ladrilhos de 400 m) + mapa-indice
import tiles
made = tiles.make_all(gr, c, os.path.join(out, 'fotos'), hf=hf, extras={'signs': fu.signs, 'heads': fu.heads, 'bumps': [b['poly'] for b in tr.bumps], 'orla': o.items})
print(f'  {len(made)} fotos geradas em out/fotos')
# vistas de conferencia
jn = min((n for n, a in gr.arms.items() if len(a) >= 4), key=lambda n: math.hypot(c.nodes[n][0] - LAGOON[0], c.nodes[n][1] - LAGOON[1]))
jx, jz = c.nodes[jn][:2]
prev_ground.crop(gr, jx, jz, 60, 10, os.path.join(out, 'ground_cruzamento_topo.png'))
render3d.render(gr.B, jx, 0, jz, 60, math.radians(35), math.radians(40), os.path.join(out, 'ground_cruzamento_obliquo.png'))
render3d.render(gr.B, 520, 35, 1500, 300, math.radians(-18), math.radians(10), os.path.join(out, 'ponte_vermelha_oeste.png'), size=1200, dist=620)
KIND = ['ave', 'col', 'loc', 'hwy']
data = {'world': [WX, WZ], 'lagoon': list(LAGOON), 'channels': [CHANNEL_W, CHANNEL_E], 'river': RIVER, 'red_bridges': c.red,
        'rounds': [{'x': r['x'], 'z': r['z'], 'r': r['r']} for r in c.rounds],
        'nodes': [{'x': round(n[0], 2), 'z': round(n[1], 2), 'kind': 'lookout' if i in c.lookouts else (c.legit[i] if i in c.legit else 'junction')} for i, n in enumerate(c.nodes)],
        'edges': [{'a': e['a'], 'b': e['b'], 'cls': KIND[e['lvl']], 'c': LEVELS[min(e['lvl'], 2)][1] if e['lvl'] < 3 else 0, 'kind': e['kind'], 'name': e['name'],
                   'p': [[round(q[0], 1), round(q[1], 1), round(q[2], 2)] for q in T.profile_pts(e, ynode[e['a']], ynode[e['b']])]} for e in c.edges]}
json.dump(data, open(os.path.join(out, 'city5_roads.json'), 'w'), separators=(',', ':'))
import lots as _lots
_lots.export(c.lotplan, os.path.join(out, 'lots.json'))
import app_export
app_export.run(out, geo, hf, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'src', 'main', 'assets', 'hds')))
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
print(f'saidas: city5_ground.bin ({os.path.getsize(os.path.join(out, "city5_ground.bin"))/1e6:.1f} MB, {nrec} blocos), frontages.json, relevo5.bin, city5_roads.json')
print(f'ETAPA A v2: {"TODOS OS VALIDADORES VERDES" if allok else "HA VALIDADORES VERMELHOS"}  ({time.time()-t:.1f}s)')
sys.exit(0 if allok else 1)
