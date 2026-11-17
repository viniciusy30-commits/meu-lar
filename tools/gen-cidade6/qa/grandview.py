"""render rapido da igreja e da escola novas (grand6): python3 qa/grandview.py SAIDA"""
import os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from mesh import Mesh, Frame
import buildings6, grand6
from view6 import Source, Viewer
import appview
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
M = Mesh(4000, 400); B = buildings6.Builder(M, random.Random(3))
M.free('lotes')
F1 = Frame((40.0, 40.0), (1, 0)); grand6.church(B, F1, 60.0, 80.0)
F2 = Frame((160.0, 40.0), (1, 0)); grand6.school(B, F2, 150.0, 90.0, lambda *a, **k: None)
M.free('lotes'); M.m('grama'); M.poly([(0, 0.12, 30), (400, 0.12, 30), (400, 0.12, 200), (0, 0.12, 200)], (120, 170, 90), (0, 1, 0))
S = Source().add_mesh(M); v = Viewer(S, appview.texdir())
v.shot(os.path.join(out, 'igreja1.png'), (55, 14, 0), (70, 12, 70), R=200, fov=60)
v.shot(os.path.join(out, 'igreja2.png'), (20, 25, 10), (70, 10, 80), R=200, fov=60)
v.shot(os.path.join(out, 'escola1.png'), (210, 18, -5), (210, 6, 60), R=250, fov=65)
v.shot(os.path.join(out, 'escola2.png'), (320, 40, 10), (230, 4, 80), R=300, fov=60)
v.run()
