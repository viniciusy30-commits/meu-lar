"""Conferencia dos predios das profissoes e da prefeitura, um por um, sem gerar a cidade inteira.
python3 qa/jobview.py SAIDA [ids...]  -> para cada predio: fachada, 3/4, interior (varios pontos) e planta sem o teto."""
import os, sys, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from mesh import Mesh, Frame
import buildings6, jobs6, jobs2_6
from roads6 import Y_WALK
from view6 import Source, Viewer
import appview


class FakeL:
    def __init__(self, M):
        self.M = M; self.rnd = random.Random(5); self.B = buildings6.Builder(M, self.rnd)
        self.trees = []; self.parked = []; self.jobs = []; self.props_lights = []; self.benches = []
    SPECIAL = {}


def main():
    out = sys.argv[1]; ids = sys.argv[2:] or list(jobs2_6.SPEC)
    os.makedirs(out, exist_ok=True)
    M = Mesh(4000, 400); L = FakeL(M)
    spots = {}
    x = 40.0
    for jid in ids:
        if jid == 'prefeito':
            F = Frame((x, 40.0), (1, 0)); jobs6.prefeitura(L, F, 110.0, 110.0); spots[jid] = (x, 40.0, 110.0, 80.0); x += 140; continue
        w, d = jobs2_6.width(jid), jobs2_6.depth(jid)
        F = Frame((x, 40.0), (1, 0)); jobs2_6.place(L, F, jid); spots[jid] = (x, 40.0, w, d); x += w + 40
    # chao: calcada na frente e terreno
    M.free('lotes'); M.m('calcada'); M.poly([(0, Y_WALK, 30), (x, Y_WALK, 30), (x, Y_WALK, 200), (0, Y_WALK, 200)], (230, 228, 222), (0, 1, 0))
    M.m('asfalto'); M.poly([(0, 0.0, 0), (x, 0.0, 0), (x, 0.0, 30), (0, 0.0, 30)], (90, 90, 90), (0, 1, 0))
    S = Source().add_mesh(M)
    v = Viewer(S, appview.texdir())
    # fonte sem teto (planta): so triangulos abaixo de 3,6 m acima do piso
    CUT = jobs2_6.Y0 + 3.4 if 'prefeito' not in ids else 5.6
    cut = Source()
    for p in S.parts:
        a, b, c, d, mat, P, N, uv, col, idx = p
        t = P[idx].reshape(-1, 3, 3); keep = np.repeat(t[:, :, 1].max(1) < CUT, 3)
        if keep.any(): cut.parts.append((a, b, c, d, mat, P, N, uv, col, idx[keep]))
    vc = Viewer(cut, appview.texdir())
    for jid, (x0, z0, w, d) in spots.items():
        cx = x0 + w / 2; y = Y_WALK + 1.6
        if jid == 'prefeito':
            v.shot(os.path.join(out, f'{jid}_1fachada.png'), (cx, 9.0, z0 - 25), (cx, 7.0, z0 + 30), R=150, fov=60)
            v.shot(os.path.join(out, f'{jid}_2tres4.png'), (cx - 30, 14.0, z0 - 10), (cx, 6.0, z0 + 28), R=150, fov=60)
            v.shot(os.path.join(out, f'{jid}_3entrada.png'), (cx, 3.4, z0 + 28.5), (cx, 2.8, z0 + 50), R=90, fov=75)
            v.shot(os.path.join(out, f'{jid}_4fundo.png'), (cx + 12, 3.4, z0 + 30), (cx + 20, 2.6, z0 + 40), R=90, fov=75)
            v.shot(os.path.join(out, f'{jid}_5lado.png'), (cx, 3.4, z0 + 48), (cx, 2.8, z0 + 58), R=90, fov=75)
            continue
        v.shot(os.path.join(out, f'{jid}_1fachada.png'), (cx, 6.0, z0 - 22), (cx, 5.0, z0 + 2), R=120, fov=60)
        v.shot(os.path.join(out, f'{jid}_2tres4.png'), (x0 - 12, 9.0, z0 - 16), (cx, 4.0, z0 + d / 2), R=120, fov=60)
        v.shot(os.path.join(out, f'{jid}_3entrada.png'), (cx + 1.0, y, z0 + 1.0), (cx, 1.4, z0 + d - 1), R=80, fov=70)
        v.shot(os.path.join(out, f'{jid}_4fundo.png'), (x0 + w * 0.3, y, z0 + d - 1.2), (x0 + w * 0.7, 1.2, z0 + 1.0), R=80, fov=70)
        v.shot(os.path.join(out, f'{jid}_5lado.png'), (x0 + 1.0, y, z0 + d * 0.5), (x0 + w - 1, 1.2, z0 + d * 0.5), R=80, fov=70)
    v.run()
    for jid, (x0, z0, w, d) in spots.items():
        vc.top(os.path.join(out, f'{jid}_6planta.png'), x0 + w / 2, z0 + (d / 2 if jid != 'prefeito' else 44), max(w, d) + 6 if jid != 'prefeito' else 80)
    vc.run()


if __name__ == '__main__':
    main()
