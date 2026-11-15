"""Conferencia visual da Cidade 6: three.js no Chromium sem tela, com as texturas de cada material.
Fonte: a malha em memoria (Mesh) ou GLB gravados (desenha exatamente o que foi exportado)."""
import os, sys, json, math, subprocess, shutil
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from mesh import read_glb


class Source:
    def __init__(self):
        self.parts = []          # (xmin, zmin, xmax, zmax, material, pos, nrm, uv, col, idx)

    def add_mesh(self, M):
        for (ti, tj, lay, mat), lst in M.data.items():
            for c in lst:
                if not len(c.idx): continue
                pn = np.frombuffer(c.pn.tobytes(), np.float32).reshape(-1, 6)
                uv = np.frombuffer(c.uv.tobytes(), np.float32).reshape(-1, 2)
                col = np.frombuffer(c.col.tobytes(), np.uint8).reshape(-1, 4)[:, :3] / 255.0
                idx = np.frombuffer(c.idx.tobytes(), np.uint16).astype(np.int64)
                p = pn[:, :3]
                self.parts.append((p[:, 0].min(), p[:, 2].min(), p[:, 0].max(), p[:, 2].max(), mat, p, pn[:, 3:6], uv, col, idx))
        return self

    def add_glb(self, path):
        prims, g = read_glb(path)
        for (nm, mat, pos, nrm, uv, col, idx) in prims:
            self.parts.append((pos[:, 0].min(), pos[:, 2].min(), pos[:, 0].max(), pos[:, 2].max(), mat, pos, nrm, uv, col, idx))
        return self

    def tris(self, x0, z0, x1, z1):
        out = {}
        for (a, b, c, d, mat, p, n, uv, col, idx) in self.parts:
            if a > x1 or c < x0 or b > z1 or d < z0: continue
            P = p[idx]; t = P.reshape(-1, 3, 3); cx = t[:, :, 0].mean(1); cz = t[:, :, 2].mean(1)
            keep = np.repeat((cx >= x0) & (cx <= x1) & (cz >= z0) & (cz <= z1), 3)
            if not keep.any(): continue
            ii = idx[keep]
            out.setdefault(mat, []).append(np.hstack([p[ii], n[ii], col[ii], uv[ii]]).astype(np.float32))
        return {m: np.vstack(v) for m, v in out.items()}


class Viewer:
    def __init__(self, src, texdir):
        self.S = src; self.jobs = []
        os.makedirs(os.path.join(HERE, 'tmp'), exist_ok=True)
        td = os.path.join(HERE, 'tex')
        if os.path.islink(td) or os.path.exists(td):
            if os.path.islink(td): os.unlink(td)
            else: shutil.rmtree(td)
        os.symlink(os.path.abspath(texdir), td)

    def shot(self, path, eye, at, R=None, w=1280, h=720, fov=60, fog=(700, 2600), bg=None, front=False):
        R = R or max(250.0, math.hypot(eye[0] - at[0], eye[2] - at[2]) * 2.2)
        groups = []
        for mat, arr in self.S.tris(at[0] - R, at[2] - R, at[0] + R, at[2] + R).items():
            fn = f'tmp/s{len(self.jobs)}_{mat}.bin'; arr.tofile(os.path.join(HERE, fn)); groups.append({'file': fn, 'tex': mat})
        self.jobs.append({'groups': groups, 'eye': list(map(float, eye)), 'at': list(map(float, at)), 'out': os.path.abspath(path), 'w': w, 'h': h,
                          'fov': fov, 'fog0': fog[0], 'fog1': fog[1], 'bg': bg, 'front': front})

    def top(self, path, x, z, span, w=1100, h=1100, y=0.0):
        fov = 20.0; hgt = span / 2 / math.tan(math.radians(fov / 2))
        self.shot(path, (x, y + hgt, z + 0.01), (x, y, z), R=span * 0.75, w=w, h=h, fov=fov, fog=(hgt * 3, hgt * 4))

    def run(self):
        jf = os.path.join(HERE, 'tmp', 'jobs.json'); json.dump(self.jobs, open(jf, 'w'))
        env = dict(os.environ); env['NODE_PATH'] = subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip(); env['VIEW'] = 'view6.html'
        r = subprocess.run(['node', os.path.join(HERE, 'shots.js'), jf], env=env, capture_output=True, text=True)
        if r.returncode or 'console:' in r.stdout: print(r.stdout[-2000:], r.stderr[-2000:])
        for j in self.jobs:
            for g in j['groups']:
                try: os.remove(os.path.join(HERE, g['file']))
                except OSError: pass
        self.jobs = []
