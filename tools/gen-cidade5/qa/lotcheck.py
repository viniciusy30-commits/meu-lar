import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from PIL import Image, ImageDraw
import geo as G, assemble, terrain_final as T
geo = G.Geo(); c = assemble.build(geo); hf, yn, X, Z = T.run(c, geo); P = c.lotplan
rects = [('casa%d' % (h['k'] + 1), h['lot']['rect']) for h in P.houses] + [('lote%d' % l['id'], [tuple(p) for p in l['rect']]) for l in P.lots]
idr = np.full((3600, 4400), -1, np.int32); pairs = {}
for n, (nm, r) in enumerate(rects):
    xs = [p[0] for p in r]; zs = [p[1] for p in r]; x0, x1 = int(min(xs)) - 1, int(max(xs)) + 2; z0, z1 = int(min(zs)) - 1, int(max(zs)) + 2
    cx = sum(xs) / 4; cz = sum(zs) / 4; im = Image.new('L', (x1 - x0, z1 - z0), 0); pts = []
    for (x, z) in r:
        dx, dz = x - cx, z - cz; l = math.hypot(dx, dz) or 1; pts.append((x - dx / l * 1.3 - x0, z - dz / l * 1.3 - z0))
    ImageDraw.Draw(im).polygon(pts, fill=1); m = np.array(im) > 0
    sub = idr[z0:z1, x0:x1]; hit = m & (sub >= 0)
    for o in np.unique(sub[hit]): pairs[(int(o), n)] = int((hit & (sub == o)).sum())
    sub[m] = n
big = sorted(pairs.items(), key=lambda kv: -kv[1])[:12]
print('total', sum(pairs.values()), 'pares', len(pairs))
for (a, b), v in big: print(rects[a][0], rects[b][0], v, [round(sum(p[0] for p in rects[a][1]) / 4), round(sum(p[1] for p in rects[a][1]) / 4)])
