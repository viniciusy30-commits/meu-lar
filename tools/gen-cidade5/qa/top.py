"""python3 qa/top.py prefixo x,z[,R] ...  -> vista quase de cima (R = meia-largura em m)"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qa3d import Viewer
v = Viewer(); pre = sys.argv[1]; outs = []
for k, a in enumerate(sys.argv[2:]):
    p = list(map(float, a.split(','))); x, z = p[0], p[1]; R = p[2] if len(p) > 2 else 30.0; y = v.ground_y(x, z)
    o = f'{pre}_{k}.png'; v.shot(o, (x, y + R * 1.9, z + R * 0.35), (x, y, z), w=900, h=700, R=R * 3); outs.append(o)
v.run(); print(' '.join(outs))
