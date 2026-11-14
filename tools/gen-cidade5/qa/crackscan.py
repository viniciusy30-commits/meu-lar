"""varre TODOS os cruzamentos/pontas: vista de cima sem terreno; conta pixels magenta finos (frestas). python3 qa/crackscan.py saida.json"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from qa3d import Viewer
R = json.load(open('out/city5_roads.json'))
pts = [(n['x'], n['z']) for n in R['nodes']]
v = Viewer(); jobs = []
for k, (x, z) in enumerate(pts):
    y = v.ground_y(x, z); o = f'qa/tmp/c{k:03d}.png'; v.shot(o, (x, y + 90, z + 1), (x, y, z), w=640, h=640, R=120, terrain=False, bg=0xff00ff, fov=45); jobs.append((k, x, z, o))
v.run(); bad = []
for k, x, z, o in jobs:
    a = np.array(Image.open(o).convert('RGB')).astype(int); m = (a[:, :, 0] > 240) & (a[:, :, 1] < 20) & (a[:, :, 2] > 240)
    # fresta = magenta com pixels de pavimento dos dois lados em ate 5 px (na horizontal ou na vertical)
    fin = np.zeros_like(m)
    for d in (1, 2, 3, 4, 5):
        l = np.roll(~m, d, 1); r = np.roll(~m, -d, 1); u = np.roll(~m, d, 0); dn = np.roll(~m, -d, 0)
    # ate 5 px de largura: cada pixel magenta com vizinho nao-magenta a esquerda E a direita (dentro de 5) ou acima E abaixo
    asph = (np.abs(a[:, :, 0] - 112) < 16) & (np.abs(a[:, :, 1] - 113) < 16) & (np.abs(a[:, :, 2] - 118) < 16)
    left = np.zeros_like(m); right = np.zeros_like(m); up = np.zeros_like(m); down = np.zeros_like(m)
    for d in range(1, 5):
        left |= np.roll(asph, d, 1); right |= np.roll(asph, -d, 1); up |= np.roll(asph, d, 0); down |= np.roll(asph, -d, 0)
    fin = m & ((left & right) | (up & down))
    fin[:8] = fin[-8:] = False; fin[:, :8] = fin[:, -8:] = False
    n = int(fin.sum())
    if n > 25: bad.append((k, round(x), round(z), n))
    os.remove(o)
print('cruzamentos com frestas:', len(bad)); print(bad[:30])
json.dump(bad, open(sys.argv[1], 'w'))
