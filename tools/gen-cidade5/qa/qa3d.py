"""Visualizador 3D de conferencia (three.js no Chromium sem tela): terreno do app + malha assada, como no jogo."""
import os, sys, json, struct, math, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'app', 'src', 'main', 'assets', 'hds'))

def C(h): h = h.lstrip('#'); return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)], float) / 255.0
GRASS_LO, GRASS_HI = C('B4DA9A'), C('E4EBB0'); SAND = C('E6D6A4'); ROCK = C('A89C84'); BED = C('A8966F')
SHAL, DEEP, FOAM = C('8FE0D6'), C('1B5FA6'), C('E8FAF7')
# o jogo multiplica a cor da grama pela textura (verde mais escuro); aproximacao
GRASS_TEX = np.array([0.42, 0.62, 0.30]) / 0.85

class Scene:
    def __init__(self, assets=ASSETS):
        b = open(os.path.join(assets, 'c5.bin'), 'rb').read(); self.nx, self.nz, self.g = struct.unpack_from('<iif', b, 0)
        self.h = np.frombuffer(b, '<i2', offset=12).reshape(self.nz, self.nx) / 100.0
        b = open(os.path.join(assets, 'c5_mesh.bin'), 'rb').read(); n = struct.unpack_from('<i', b, 4)[0]; o = 8
        dt = np.dtype([('f', '<f4', 8), ('c', 'u1', 3)]); self.recs = []
        for _ in range(n):
            cell, mat, nv, ymax = struct.unpack_from('<iiif', b, o); o += 16
            a = np.frombuffer(b, dt, nv, o); o += nv * 35
            self.recs.append((cell % 1000 * 64.0, cell // 1000 * 64.0, mat, a))
        self.assets = assets
        try:
            b = open(os.path.join(assets, 'c5_sand.bin'), 'rb').read(); sx, sz = struct.unpack_from('<ii', b, 0)
            self.sand = np.frombuffer(b, np.uint8, offset=8).reshape(sz, sx).astype(bool)
        except OSError: self.sand = None

    def terrain(self, x0, z0, x1, z1):
        g = self.g; i0, i1 = max(int(x0 / g), 0), min(int(x1 / g) + 1, self.nx - 1); j0, j1 = max(int(z0 / g), 0), min(int(z1 / g) + 1, self.nz - 1)
        H = self.h; out = []
        def nrm(i, j):
            dx = (H[j, min(i + 1, self.nx - 1)] - H[j, max(i - 1, 0)]) / (2 * g); dz = (H[min(j + 1, self.nz - 1), i] - H[max(j - 1, 0), i]) / (2 * g); l = math.sqrt(dx * dx + 1 + dz * dz); return (-dx / l, 1 / l, -dz / l)
        for j in range(j0, j1):
            for i in range(i0, i1):
                h00, h10, h01, h11 = H[j, i], H[j, i + 1], H[j + 1, i], H[j + 1, i + 1]
                avg = (h00 + h10 + h01 + h11) / 4; lo = min(h00, h10, h01, h11)
                steep = max(abs(h10 - h00), abs(h01 - h00), abs(h11 - h10), abs(h11 - h01)) / g > 0.5
                ns = int(self.sand[j, i]) + int(self.sand[j, i + 1]) + int(self.sand[j + 1, i]) + int(self.sand[j + 1, i + 1]) if self.sand is not None else -1
                def col(h, i_=None, j_=None):
                    if avg < -0.1:
                        if h > -0.15 and self.sand is not None and (h > 0 or self.sand[min(j_, self.nz - 1), min(i_, self.nx - 1)]): return SAND
                        return BED
                    if ns >= 0:
                        if ns >= 2 and avg < 1.6: return SAND
                    elif avg < 1.3: return SAND
                    gc = (GRASS_LO + (GRASS_HI - GRASS_LO) * min(max(h / 60, 0), 1))
                    if i_ is not None:
                        n_ = nrm(i_, j_); sl = math.sqrt(max(1 / (n_[1] ** 2) - 1, 0))
                        rk = min(max((sl - 0.55) / 0.45, 0), 1); gc = gc + (ROCK - gc) * rk * rk * 0.85
                    if h < 1.3 and ns < 0: gc = gc + (SAND - gc) * 0.75
                    return gc * GRASS_TEX
                V = {(0, 0): (i * g, h00, j * g), (1, 0): ((i + 1) * g, h10, j * g), (0, 1): (i * g, h01, (j + 1) * g), (1, 1): ((i + 1) * g, h11, (j + 1) * g)}
                for tri in (((0, 0), (1, 0), (1, 1)), ((0, 0), (1, 1), (0, 1))):
                    for k in tri:
                        p = V[k]; out.append((*p, *nrm(i + k[0], j + k[1]), *col(p[1], i + k[0], j + k[1]), 0, 0, 0))
                if lo < -0.15:
                    for tri in (((0, 0), (1, 0), (1, 1)), ((0, 0), (1, 1), (0, 1))):
                        for k in tri:
                            hh = V[k][1]; d = min(max(-0.2 - hh, 0), 9) / 9; body = SHAL + (DEEP - SHAL) * math.sqrt(d)
                            cc = body + (FOAM - body) * min(max(1 - (-0.2 - hh) / 0.55, 0), 1) * 0.8
                            out.append((V[k][0], -0.2, V[k][2], 0, 1, 0, *cc, 0, 0, 0))
        return np.array(out, np.float32)

    def houses_mesh(self, x0, z0, x1, z1):
        """caixas das casas (altura 6 m, cor salmao) + contorno do quintal (pilares) para conferir o posicionamento (as casas reais so existem no jogo)"""
        try: L = json.load(open(os.path.join(HERE, '..', 'out', 'lots.json')))
        except OSError: return np.zeros((0, 12), np.float32)
        out = []
        def quad(p, n, c):
            for t in ((0, 1, 2), (0, 2, 3)):
                for k in t: out.append((*p[k], *n, *c, 0, 0, 0))
        for h in L['houses']:
            bx0, bz0, bx1, bz1 = h['box']
            if bx1 < x0 or bx0 > x1 or bz1 < z0 or bz0 > z1: continue
            y = h['lvl'] + 0.08; hh = 6.0; col = (0.93, 0.62, 0.52)
            q = h.get('boxq') or [(bx0, bz0), (bx1, bz0), (bx1, bz1), (bx0, bz1)]
            for p, r in zip(q, q[1:] + q[:1]):
                ex, ez = r[0] - p[0], r[1] - p[1]; L_ = math.hypot(ex, ez) or 1
                nrm = (ez / L_, 0, -ex / L_)
                quad([(p[0], y, p[1]), (r[0], y, r[1]), (r[0], y + hh, r[1]), (p[0], y + hh, p[1])], nrm, col)
                quad([(r[0], y, r[1]), (p[0], y, p[1]), (p[0], y + hh, p[1]), (r[0], y + hh, r[1])], (-nrm[0], 0, -nrm[2]), col)
            quad([(p[0], y + hh, p[1]) for p in q], (0, 1, 0), (0.55, 0.25, 0.2))
            # porta (faixa verde) e contorno do quintal
            dx, dz = h['door']; quad([(dx - 0.8, y + 0.05, dz - 0.3), (dx + 0.8, y + 0.05, dz - 0.3), (dx + 0.8, y + 0.05, dz + 0.3), (dx - 0.8, y + 0.05, dz + 0.3)], (0, 1, 0), (0.1, 0.8, 0.2))
            lr = h['lot']
            for a, b in zip(lr, lr[1:] + lr[:1]):
                ex, ez = b[0] - a[0], b[1] - a[1]; L_ = math.hypot(ex, ez); ux, uz = ex / L_, ez / L_
                quad([(a[0] - uz * 0.08, y + 0.02, a[1] + ux * 0.08), (b[0] - uz * 0.08, y + 0.02, b[1] + ux * 0.08), (b[0] + uz * 0.08, y + 0.02, b[1] - ux * 0.08), (a[0] + uz * 0.08, y + 0.02, a[1] - ux * 0.08)], (0, 1, 0), (1, 1, 0))
        return np.array(out, np.float32).reshape(-1, 12) if out else np.zeros((0, 12), np.float32)

    def mesh(self, x0, z0, x1, z1):
        out = []
        for cx, cz, mat, a in self.recs:
            if cx > x1 or cx + 64 < x0 or cz > z1 or cz + 64 < z0: continue
            f = a['f']; c = a['c'] / 255.0
            if mat == 15: c = c * 0.62          # asfalto texturizado escurece no jogo
            sign = np.full((len(f), 1), 1.0 if mat == 17 else 0.0, np.float32)
            out.append(np.hstack([f[:, :6], c, f[:, 6:8], sign]).astype(np.float32))
        return np.vstack(out) if out else np.zeros((0, 12), np.float32)

class Viewer:
    """junta pedidos de foto e renderiza todos de uma vez (node + playwright + three.js)"""
    def __init__(self, scene=None):
        import shutil
        self.S = scene or Scene(); self.jobs = []
        shutil.copy(os.path.join(self.S.assets, 'c5_signs.png'), os.path.join(HERE, 'atlas.png'))
        os.makedirs(os.path.join(HERE, 'tmp'), exist_ok=True)

    def shot(self, path, eye, at, R=None, w=1280, h=720, fov=60, fog=(300, 900), terrain=True, bg=None):
        cx, cz = at[0], at[2]; R = R or max(200.0, math.hypot(eye[0] - at[0], eye[2] - at[2]) * 2.0)
        x0, z0, x1, z1 = cx - R, cz - R, cx + R, cz + R
        parts = ([self.S.terrain(x0, z0, x1, z1)] if terrain else []) + [self.S.mesh(x0, z0, x1, z1), (real_houses_mesh(x0, z0, x1, z1) if os.environ.get('REALH') else self.S.houses_mesh(x0, z0, x1, z1))]
        data = np.vstack(parts)
        fn = f'tmp/s{len(self.jobs)}.bin'; data.tofile(os.path.join(HERE, fn))
        self.jobs.append({'file': fn, 'eye': list(map(float, eye)), 'at': list(map(float, at)), 'out': os.path.abspath(path), 'w': w, 'h': h, 'fov': fov, 'fog0': fog[0], 'fog1': fog[1], 'bg': bg})

    def run(self):
        jf = os.path.join(HERE, 'tmp', 'jobs.json'); json.dump(self.jobs, open(jf, 'w'))
        env = dict(os.environ); env['NODE_PATH'] = subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip()
        r = subprocess.run(['node', os.path.join(HERE, 'shots.js'), jf], env=env, capture_output=True, text=True)
        if r.returncode: print(r.stdout, r.stderr)
        for j in self.jobs:
            try: os.remove(os.path.join(HERE, j['file']))
            except OSError: pass
        self.jobs = []

    def ground_y(self, x, z):
        return float(self.S.h[min(max(int(round(z / self.S.g)), 0), self.S.nz - 1), min(max(int(round(x / self.S.g)), 0), self.S.nx - 1)])

if __name__ == '__main__':
    v = Viewer()
    x, z = float(sys.argv[1]), float(sys.argv[2]); y = v.ground_y(x, z)
    v.shot(sys.argv[3], (x - 40, y + 25, z + 40), (x, y, z))
    v.run()


def real_houses_mesh(x0, z0, x1, z1, assets=None):
    """as casas REAIS (malhas do city2.glb) com a mesma transformacao do app (Hds.kt addInst): translada o centro para a posicao do c5.json e gira por 'yaw'"""
    import struct
    assets = assets or os.path.join(HERE, '..', '..', '..', 'app', 'src', 'main', 'assets', 'hds')
    raw = open(os.path.join(assets, 'city2.glb'), 'rb').read(); jl = struct.unpack_from('<I', raw, 12)[0]; g = json.loads(raw[20:20 + jl])
    bo = 20 + jl + 8; bin_ = raw[bo:]
    d = json.load(open(os.path.join(assets, 'city2.json'))); c5 = json.load(open(os.path.join(assets, 'c5.json')))
    cache = {}
    def prims(ni):
        if ni in cache: return cache[ni]
        n = g['nodes'][ni]; out = []
        if 'mesh' in n:
            for p in g['meshes'][n['mesh']]['primitives']:
                ac = g['accessors'][p['attributes']['POSITION']]; bv = g['bufferViews'][ac['bufferView']]
                pos = np.frombuffer(bin_, np.float32, ac['count'] * 3, bv.get('byteOffset', 0) + ac.get('byteOffset', 0)).reshape(-1, 3)
                ia = g['accessors'][p['indices']]; iv = g['bufferViews'][ia['bufferView']]
                dt = {5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[ia['componentType']]
                idx = np.frombuffer(bin_, dt, ia['count'], iv.get('byteOffset', 0) + ia.get('byteOffset', 0)).astype(np.int64)
                out.append((pos, idx))
        cache[ni] = out; return out
    out = []
    for h in c5['houses']:
        k = h['k']; pl = d['plots'][k]; cxs = (pl['x0'] + pl['x1']) / 2; czs = (pl['z0'] + pl['z1']) / 2
        cx, cz = h['x'], h['z']
        if cx < x0 - 60 or cx > x1 + 60 or cz < z0 - 60 or cz > z1 + 60: continue
        yaw = h.get('yaw', 0.0); cs, sn = math.cos(yaw), math.sin(yaw)
        pdx, pdz = cx - cxs, cz - czs
        for a in d['inst']:
            if a[14] != k: continue
            kind = a[13]
            m = np.array(a[1:13], np.float64).reshape(3, 4)
            for pos, idx in prims(a[0]):
                w = pos @ m[:, :3].T + m[:, 3]
                wx = w[:, 0] + pdx; wz = w[:, 2] + pdz
                rx = cx + cs * (wx - cx) - sn * (wz - cz); rz = cz + sn * (wx - cx) + cs * (wz - cz)
                wy = w[:, 1] + h['lvl'] + 0.08
                P = np.stack([rx, wy, rz], 1)
                t = P[idx].reshape(-1, 3, 3); nrm = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); l = np.linalg.norm(nrm, axis=1, keepdims=True); nrm = nrm / np.maximum(l, 1e-9)
                col = {0: (0.45, 0.62, 0.35), 1: (0.9, 0.85, 0.78), 2: (0.7, 0.3, 0.25)}.get(kind, (0.8, 0.8, 0.8))
                n = t.shape[0]
                rec = np.zeros((n, 3, 12), np.float32); rec[:, :, 0:3] = t; rec[:, :, 3:6] = nrm[:, None, :]; rec[:, :, 6:9] = col
                out.append(rec.reshape(-1, 12))
    return np.vstack(out).astype(np.float32) if out else np.zeros((0, 12), np.float32)
