"""python3 qa/cracks.py prefixo x,z[,R] ...  -> vista de cima SEM terreno (fundo magenta): frestas na malha aparecem magenta"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qa3d import Viewer
v = Viewer(); pre = sys.argv[1]; outs = []
for k, a in enumerate(sys.argv[2:]):
    p = list(map(float, a.split(','))); x, z = p[0], p[1]; R = p[2] if len(p) > 2 else 30.0; y = v.ground_y(x, z)
    o = f'{pre}_{k}.png'; v.shot(o, (x, y + R * 2.0, z + R * 0.02), (x, y, z), w=900, h=900, R=R * 3, terrain=False, bg=0xff00ff, fov=45); outs.append(o)
v.run(); print(' '.join(outs))
