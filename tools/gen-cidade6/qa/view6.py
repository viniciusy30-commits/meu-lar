"""Conferencia visual da Cidade 6: three.js no Chromium sem tela (mesmo renderizador do gen-cidade5).
Fonte: a malha em memoria (Mesh) ou arquivos GLB gravados (le e desenha exatamente o que foi exportado)."""
import os, sys, json, math, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from mesh import TILE, read_glb


class Source:
    def __init__(self):
        self.parts = []          # (bbox xmin,zmin,xmax,zmax, pos, nrm, col, idx)

    def add_mesh(self, M):
        for (ti, tj, lay), lst in M.data.items():
            for c in lst:
                if not len(c.idx): continue
                pn = np.frombuffer(c.pn.tobytes(), np.float32).reshape(-1, 6)
                col = np.frombuffer(c.col.tobytes(), np.uint8).reshape(-1, 4)[:, :3] / 255.0
                idx = np.frombuffer(c.idx.tobytes(), np.uint16).astype(np.int64)
                p = pn[:, :3]
                self.parts.append((p[:, 0].min(), p[:, 2].min(), p[:, 0].max(), p[:, 2].max(), p, pn[:, 3:6], col, idx))
        return self

    def add_glb(self, path):
        prims, g = read_glb(path)
        for (nm, pos, nrm, col, idx) in prims:
            self.parts.append((pos[:, 0].min(), pos[:, 2].min(), pos[:, 0].max(), pos[:, 2].max(), pos, nrm, col, idx))
        return self

    def tris(self, x0, z0, x1, z1):
        out = []
        for (a, b, c, d, p, n, col, idx) in self.parts:
            if a > x1 or c < x0 or b > z1 or d < z0: continue
            P = p[idx]; N = n[idx]; C = col[idx]
            t = P.reshape(-1, 3, 3); cx = t[:, :, 0].mean(1); cz = t[:, :, 2].mean(1)
            keep = np.repeat((cx >= x0) & (cx <= x1) & (cz >= z0) & (cz <= z1), 3)
            k = keep.sum()
            if not k: continue
            out.append(np.hstack([P[keep], N[keep], C[keep], np.zeros((k, 3))]).astype(np.float32))
        return np.vstack(out) if out else np.zeros((0, 12), np.float32)


class Viewer:
    def __init__(self, src):
        self.S = src; self.jobs = []
        os.makedirs(os.path.join(HERE, 'tmp'), exist_ok=True)

    def shot(self, path, eye, at, R=None, w=1280, h=720, fov=60, fog=(600, 2600), bg=None):
        R = R or max(250.0, math.hypot(eye[0] - at[0], eye[2] - at[2]) * 2.2)
        data = self.S.tris(at[0] - R, at[2] - R, at[0] + R, at[2] + R)
        fn = f'tmp/s{len(self.jobs)}.bin'; data.tofile(os.path.join(HERE, fn))
        self.jobs.append({'file': fn, 'eye': list(map(float, eye)), 'at': list(map(float, at)), 'out': os.path.abspath(path), 'w': w, 'h': h, 'fov': fov, 'fog0': fog[0], 'fog1': fog[1], 'bg': bg})

    def top(self, path, x, z, span, w=1100, h=1100, y=0.0):
        """vista de cima (quase ortogonal): camera alta com fov pequeno"""
        fov = 20.0; hgt = span / 2 / math.tan(math.radians(fov / 2))
        self.shot(path, (x, y + hgt, z + 0.01), (x, y, z), R=span * 0.75, w=w, h=h, fov=fov, fog=(hgt * 3, hgt * 4))

    def run(self):
        jf = os.path.join(HERE, 'tmp', 'jobs.json'); json.dump(self.jobs, open(jf, 'w'))
        env = dict(os.environ); env['NODE_PATH'] = subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip()
        r = subprocess.run(['node', os.path.join(HERE, 'shots.js'), jf], env=env, capture_output=True, text=True)
        if r.returncode: print(r.stdout[-2000:], r.stderr[-2000:])
        for j in self.jobs:
            try: os.remove(os.path.join(HERE, j['file']))
            except OSError: pass
        self.jobs = []
