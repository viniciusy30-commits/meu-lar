"""python3 qa/street.py prefixo idx_no [idx_no...]: vista de jogador (camera atras e acima) olhando para o cruzamento por cada braco"""
import sys, os, json, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qa3d import Viewer
R = json.load(open('out/city5_roads.json')); pre = sys.argv[1]; v = Viewer(); outs = []
for ni in map(int, sys.argv[2:]):
    n = R['nodes'][ni]; arms = []
    for e in R['edges']:
        for end, idx in (('a', e['a']), ('b', e['b'])):
            if idx == ni:
                p = e['p'] if end == 'a' else e['p'][::-1]; q = p[min(2, len(p) - 1)]
                d = math.hypot(q[0] - p[0][0], q[1] - p[0][1]) or 1; arms.append(((q[0] - p[0][0]) / d, (q[1] - p[0][1]) / d, e['cls']))
    for k, (dx, dz, cls) in enumerate(arms):
        x, z = n['x'] + dx * 26, n['z'] + dz * 26; y = v.ground_y(x, z)
        o = f'{pre}_{ni}_{k}.png'; v.shot(o, (x, y + 3.2, z), (n['x'], v.ground_y(n['x'], n['z']) + 0.5, n['z']), w=900, h=500, fov=60, R=120); outs.append(o)
v.run(); print(' '.join(outs))
