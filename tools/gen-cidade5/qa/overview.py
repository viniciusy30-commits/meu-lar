"""mapa geral: relevo, zona urbana, praia, agua e ruas (da city5_roads.json ou do grafo montado agora)"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, geo as G, assemble
from PIL import Image, ImageDraw
out = sys.argv[1]; S = 3
geo = G.Geo(); c = assemble.build(geo) if '--build' in sys.argv else (assemble.City(geo) if '--raw' in sys.argv else None)
h = geo.h; NZ, NX = h.shape
img = np.zeros((NZ, NX, 3), np.uint8); img[...] = (70, 120, 60)
img[h > 40] = (110, 120, 80); img[h > 120] = (130, 115, 95)
img[geo.urban] = (190, 190, 175); img[geo.beach_zone] = (225, 215, 170)
img[geo.beach_zone & (geo.Dsea < 62)] = (235, 215, 150); img[geo.water] = (60, 120, 190)
im = Image.fromarray(img).resize((NX * S, NZ * S), Image.NEAREST); d = ImageDraw.Draw(im)
if c is not None:
    for e in c.edges:
        if e['kind'] == 'redbridge': continue
        p = [(q[0] / 16 * S, q[1] / 16 * S) for q in e['p']]
        d.line(p, fill=(0, 190, 200) if 'Orla' in e.get('name', '') else (200, 40, 40) if e['lvl'] == 0 else ((40, 40, 160) if e['lvl'] == 1 else (30, 30, 30)), width=3 if e['lvl'] == 0 else 2)
for x in range(0, 4400, 400): d.text((x / 16 * S + 2, 2), str(x), fill='white')
for z in range(0, 3600, 400): d.text((2, z / 16 * S + 2), str(z), fill='white')
im.save(out)
if c is not None: print('arestas', len(c.edges), 'nos', len(c.nodes))
