"""fotos 3D obliquas de todos os ladrilhos (300 m) que tem ruas -> qa/tour/tNN.png e mosaicos"""
import sys, os, json, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qa3d import Viewer
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
T = 300.0
R = json.load(open('out/city5_roads.json'))
cells = set()
for e in R['edges']:
    for p in e['p']: cells.add((int(p[0] // T), int(p[1] // T)))
for e in R['edges']:
    for a, b in zip(e['p'], e['p'][1:]):
        n = int(math.hypot(b[0] - a[0], b[1] - a[1]) // 50) + 1
        for t in range(n + 1): cells.add((int((a[0] + (b[0] - a[0]) * t / n) // T), int((a[1] + (b[1] - a[1]) * t / n) // T)))
cells = sorted(cells, key=lambda c: (c[1], c[0]))
v = Viewer(); idx = []
for k, (i, j) in enumerate(cells):
    cx, cz = (i + 0.5) * T, (j + 0.5) * T; y = v.ground_y(cx, cz)
    o = os.path.join(out, f't{k:02d}.png')
    v.shot(o, (cx - 40, y + 150, cz + 230), (cx, y, cz - 10), w=1100, h=700, R=330, fog=(600, 1400))
    idx.append({'k': k, 'x': cx, 'z': cz})
v.run(); json.dump(idx, open(os.path.join(out, 'index.json'), 'w')); print(len(cells))
