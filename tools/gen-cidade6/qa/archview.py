"""python3 qa/archview.py SAIDA [ids] -> predio principal do campus de cada profissao (arch6), fachada, 3/4 e alto."""
import os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from mesh import Mesh, Frame
import buildings6, jobs2_6, arch6
from lots6 import Lots
from roads6 import Y_WALK
from view6 import Source, Viewer
import appview
from jobview import FakeL

def main():
    out = sys.argv[1]; ids = sys.argv[2:] or list(arch6.BUILDERS)
    os.makedirs(out, exist_ok=True)
    M = Mesh(6000, 400); L = FakeL(M); spots = {}; x = 40.0
    for jid in ids:
        w, d = 84.0, 30.0; nf = Lots.CAMPUS_FLOORS.get(jid, max(3, jobs2_6.SPEC[jid][2]))
        F = Frame((x, 40.0), (1, 0)); jobs2_6.place(L, F, jid, w, d, nf); spots[jid] = (x, 40.0, w, d, nf); x += w + 60
    M.free('lotes'); M.m('calcada'); M.poly([(0, Y_WALK, 30), (x, Y_WALK, 30), (x, Y_WALK, 200), (0, Y_WALK, 200)], (230, 228, 222), (0, 1, 0))
    M.m('asfalto'); M.poly([(0, 0.0, 0), (x, 0.0, 0), (x, 0.0, 30), (0, 0.0, 30)], (90, 90, 90), (0, 1, 0))
    v = Viewer(Source().add_mesh(M), appview.texdir())
    for jid, (x0, z0, w, d, nf) in spots.items():
        cx = x0 + w / 2; H = max(12, nf * 3.4)
        v.shot(os.path.join(out, f'{jid}_1.png'), (cx - 20, 4.0 + H * 0.25, z0 - 30 - H * 0.6), (cx, H * 0.45, z0 + d / 2), R=260, fov=62)
        v.shot(os.path.join(out, f'{jid}_2.png'), (x0 - 25, H * 0.8 + 10, z0 - 25), (cx, H * 0.35, z0 + d / 2), R=260, fov=62)
        v.shot(os.path.join(out, f'{jid}_3.png'), (cx + 8, 2.0, z0 - 12), (cx - 2, 4.0, z0 + 4), R=120, fov=70)
    v.run()

if __name__ == '__main__': main()
