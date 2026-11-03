"""Leitor minimo de GLB (glTF 2.0) para a Universal Animation Library (Quaternius, CC0).
Le esqueleto (nos), pose de repouso e animacoes (translation/rotation/scale, LINEAR) sem dependencias alem de numpy."""
import json, struct, numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

def _glb(path):
    b = open(path, 'rb').read(); assert b[:4] == b'glTF'
    o = 12; js = bn = None
    while o < len(b):
        l, t = struct.unpack('<II', b[o:o + 8]); d = b[o + 8:o + 8 + l]; o += 8 + l
        if t == 0x4E4F534A: js = json.loads(d)
        elif t == 0x004E4942: bn = d
    return js, bn

def _acc(js, bn, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    n = NC[a['type']]; dt = CT[a['componentType']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0)
    if stride and stride != n * np.dtype(dt).itemsize:
        raw = np.frombuffer(bn, np.uint8, a['count'] * stride, off).reshape(a['count'], stride)
        return np.frombuffer(raw[:, :n * np.dtype(dt).itemsize].tobytes(), dt).reshape(a['count'], n).astype(np.float64)
    return np.frombuffer(bn, dt, a['count'] * n, off).reshape(a['count'], n).astype(np.float64)

def quat_mat(q):
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])

def slerp(q0, q1, t):
    d = float(q0 @ q1)
    if d < 0: q1 = -q1; d = -d
    if d > 0.9995:
        q = q0 + t * (q1 - q0); return q / np.linalg.norm(q)
    th = np.arccos(d); s = np.sin(th)
    return (np.sin((1 - t) * th) * q0 + np.sin(t * th) * q1) / s

class Rig:
    def __init__(self, path):
        js, bn = _glb(path); self.js = js
        sk = js['skins'][0]; self.joints = sk['joints']
        nodes = js['nodes']; n = len(nodes)
        self.parent = [-1] * n
        for i, nd in enumerate(nodes):
            for c in nd.get('children', []): self.parent[c] = i
        self.names = [nd.get('name', str(i)) for i, nd in enumerate(nodes)]
        self.rest_t = np.zeros((n, 3)); self.rest_q = np.tile([0, 0, 0, 1.0], (n, 1)); self.rest_s = np.ones((n, 3))
        for i, nd in enumerate(nodes):
            if 'translation' in nd: self.rest_t[i] = nd['translation']
            if 'rotation' in nd: self.rest_q[i] = nd['rotation']
            if 'scale' in nd: self.rest_s[i] = nd['scale']
        # ordem topologica
        order = []; seen = set()
        def visit(i):
            if i in seen: return
            if self.parent[i] >= 0: visit(self.parent[i])
            seen.add(i); order.append(i)
        for i in range(n): visit(i)
        self.order = order
        self.anims = {}
        for a in js['animations']:
            ch = {}
            for c in a['channels']:
                s = a['samplers'][c['sampler']]
                assert s.get('interpolation', 'LINEAR') in ('LINEAR', 'STEP'), s
                tm = _acc(js, bn, s['input'])[:, 0]; v = _acc(js, bn, s['output'])
                ch[(c['target']['node'], c['target']['path'])] = (tm, v)
            self.anims[a['name']] = ch
        self.name_to_node = {nm: i for i, nm in enumerate(self.names)}

    def duration(self, anim):
        return max(tm[-1] for tm, _ in self.anims[anim].values())

    def local(self, anim, t):
        """T, Q, S locais de todos os nos no tempo t (s)."""
        n = len(self.names)
        T = self.rest_t.copy(); Q = self.rest_q.copy(); S = self.rest_s.copy()
        for (node, path), (tm, v) in self.anims[anim].items():
            if t <= tm[0]: k0 = k1 = 0; u = 0.0
            elif t >= tm[-1]: k0 = k1 = len(tm) - 1; u = 0.0
            else:
                k1 = int(np.searchsorted(tm, t, 'right')); k0 = k1 - 1; u = (t - tm[k0]) / (tm[k1] - tm[k0])
            if path == 'rotation': Q[node] = slerp(v[k0], v[k1], u) if k0 != k1 else v[k0]
            elif path == 'translation': T[node] = v[k0] + u * (v[k1] - v[k0])
            elif path == 'scale': S[node] = v[k0] + u * (v[k1] - v[k0])
        return T, Q, S

    def world(self, T, Q, S):
        """matrizes 4x4 de mundo de todos os nos."""
        n = len(self.names); W = np.zeros((n, 4, 4))
        for i in self.order:
            L = np.eye(4); L[:3, :3] = quat_mat(Q[i]) @ np.diag(S[i]); L[:3, 3] = T[i]
            W[i] = L if self.parent[i] < 0 else W[self.parent[i]] @ L
        return W

    def rest_world(self):
        return self.world(self.rest_t, self.rest_q, self.rest_s)
