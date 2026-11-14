"""python3 qa/look.py out_prefix x,z [x,z ...]  -> 2 vistas (obliqua e baixa) por ponto"""
import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qa3d import Viewer
v = Viewer(); pre = sys.argv[1]; outs = []
for k, a in enumerate(sys.argv[2:]):
    x, z = map(float, a.split(',')); y = v.ground_y(x, z)
    o1 = f'{pre}_{k}a.png'; o2 = f'{pre}_{k}b.png'
    v.shot(o1, (x - 45, y + 38, z + 55), (x, y, z), w=960, h=600)
    v.shot(o2, (x + 30, y + 3.5, z - 28), (x, y + 0.5, z), w=960, h=600)
    outs += [o1, o2]
v.run(); print('\n'.join(outs))
