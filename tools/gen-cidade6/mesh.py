"""Cidade 6 - construtor de malha indexada por TILE e CAMADA, primitivas geometricas e gravador GLB.

Coordenadas do mundo: X leste (0..W), Z sul (0..H), Y para cima, em metros (o mesmo eixo do glTF).
Cada elemento (triangulo/quad/caixa...) vai para o tile do "ancora" atual (o objeto inteiro fica num tile so)
ou, sem ancora, para o tile do seu centro. Cada (tile, camada) guarda pedacos com menos de 65 mil vertices
(o leitor GLB do jogo usa indices de 16 bits)."""
import math, struct, json
from array import array
import numpy as np

TILE = 250.0
MAXV = 65000


def rgb(h):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def shade(c, d):
    return tuple(max(0, min(255, int(v + d))) for v in c)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Chunk:
    __slots__ = ('pn', 'col', 'idx', 'nv')

    def __init__(self):
        self.pn = array('f'); self.col = array('B'); self.idx = array('H'); self.nv = 0


class Mesh:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.nx, self.nz = int(math.ceil(W / TILE)), int(math.ceil(H / TILE))
        self.data = {}            # (ti, tj, camada) -> [Chunk]
        self.anchor = None
        self.layer = 'geral'
        self.ntri = 0

    # ---------------------------------------------------------------- contexto
    def at(self, x, z, layer=None):
        """ancora o proximo objeto no tile de (x, z)"""
        self.anchor = (x, z)
        if layer: self.layer = layer
        return self

    def free(self, layer=None):
        self.anchor = None
        if layer: self.layer = layer
        return self

    def tile_of(self, x, z):
        return (min(max(int(x // TILE), 0), self.nx - 1), min(max(int(z // TILE), 0), self.nz - 1))

    def _chunk(self, key, nv):
        lst = self.data.get(key)
        if lst is None: lst = self.data[key] = [Chunk()]
        c = lst[-1]
        if c.nv + nv > MAXV:
            c = Chunk(); lst.append(c)
        return c

    # ---------------------------------------------------------------- elementos basicos
    def poly(self, pts, col, n=None, flip_ok=True):
        """poligono convexo plano (lista de (x,y,z)) com normal plana; n: normal desejada (o sentido dos indices segue n)"""
        k = len(pts)
        if k < 3: return
        p0 = pts[0]
        ax, ay, az = pts[1][0] - p0[0], pts[1][1] - p0[1], pts[1][2] - p0[2]
        bx, by, bz = pts[2][0] - p0[0], pts[2][1] - p0[1], pts[2][2] - p0[2]
        gx, gy, gz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
        if k > 3 and gx * gx + gy * gy + gz * gz < 1e-12:
            bx, by, bz = pts[3][0] - p0[0], pts[3][1] - p0[1], pts[3][2] - p0[2]
            gx, gy, gz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
        L = math.sqrt(gx * gx + gy * gy + gz * gz)
        if L < 1e-12: return
        gx, gy, gz = gx / L, gy / L, gz / L
        rev = False
        if n is not None:
            if gx * n[0] + gy * n[1] + gz * n[2] < 0: rev = True; gx, gy, gz = -gx, -gy, -gz
        # glTF: frente = anti-horario visto de fora (normal pela regra da mao direita)
        if self.anchor is not None: cx, cz = self.anchor
        else: cx = sum(p[0] for p in pts) / k; cz = sum(p[2] for p in pts) / k
        t = self.tile_of(cx, cz)
        c = self._chunk((t[0], t[1], self.layer), k)
        base = c.nv
        for p in pts:
            c.pn.extend((p[0], p[1], p[2], gx, gy, gz)); c.col.extend((col[0], col[1], col[2], 255))
        c.nv += k
        for i in range(1, k - 1):
            if rev: c.idx.extend((base, base + i + 1, base + i))
            else: c.idx.extend((base, base + i, base + i + 1))
        self.ntri += k - 2

    def tri(self, a, b, c, col, n=None): self.poly([a, b, c], col, n)

    def quad(self, a, b, c, d, col, n=None): self.poly([a, b, c, d], col, n)

    def smooth_grid(self, P, N, C):
        """grade de vertices com normais suaves (terreno): P (nz,nx,3), N (nz,nx,3), C (nz,nx,3); quebrada por tile"""
        nz, nx = P.shape[:2]
        for j in range(nz - 1):
            for i in range(nx - 1):
                q = [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]
                cx = (P[j, i, 0] + P[j, i + 1, 0]) / 2; cz = (P[j, i, 2] + P[j + 1, i, 2]) / 2
                t = self.tile_of(cx, cz)
                ch = self._chunk((t[0], t[1], self.layer), 4)
                base = ch.nv
                for (a, b) in q:
                    ch.pn.extend((float(P[a, b, 0]), float(P[a, b, 1]), float(P[a, b, 2]), float(N[a, b, 0]), float(N[a, b, 1]), float(N[a, b, 2])))
                    ch.col.extend((int(C[a, b, 0]), int(C[a, b, 1]), int(C[a, b, 2]), 255))
                ch.nv += 4
                # frente para cima: (x+,z) x (x,z+) -> y- ; entao ordem 0,3,2 / 0,2,1 aponta para cima
                ch.idx.extend((base, base + 3, base + 2, base, base + 2, base + 1))
                self.ntri += 2

    # ---------------------------------------------------------------- solidos
    def prism(self, c4, y0, y1, col, top=True, bottom=False, colt=None, sides=None):
        """prisma vertical sobre poligono convexo (lista de (x,z) em qualquer sentido)"""
        n = len(c4)
        cx = sum(p[0] for p in c4) / n; cz = sum(p[1] for p in c4) / n
        for k in range(n):
            a = c4[k]; b = c4[(k + 1) % n]
            ex, ez = b[0] - a[0], b[1] - a[1]; L = math.hypot(ex, ez)
            if L < 1e-6: continue
            fx, fz = ez / L, -ex / L
            if fx * ((a[0] + b[0]) / 2 - cx) + fz * ((a[1] + b[1]) / 2 - cz) < 0: fx, fz = -fx, -fz
            cc = col if sides is None else sides[k % len(sides)]
            cc = shade(cc, -10 if abs(fx) > abs(fz) else 0)
            self.quad((a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1]), cc, (fx, 0, fz))
        if top: self.poly([(p[0], y1, p[1]) for p in c4], colt or col, (0, 1, 0))
        if bottom: self.poly([(p[0], y0, p[1]) for p in c4], col, (0, -1, 0))

    def box(self, x0, x1, y0, y1, z0, z1, col, top=True, bottom=False, colt=None):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, col, top, bottom, colt)

    def cyl(self, cx, cz, r, y0, y1, col, seg=8, top=True, r1=None, colt=None):
        r1 = r if r1 is None else r1
        pts0 = [(cx + math.cos(2 * math.pi * i / seg) * r, cz + math.sin(2 * math.pi * i / seg) * r) for i in range(seg)]
        pts1 = [(cx + math.cos(2 * math.pi * i / seg) * r1, cz + math.sin(2 * math.pi * i / seg) * r1) for i in range(seg)]
        for i in range(seg):
            a0, b0 = pts0[i], pts0[(i + 1) % seg]; a1, b1 = pts1[i], pts1[(i + 1) % seg]
            am = 2 * math.pi * (i + 0.5) / seg
            nrm = (math.cos(am), (r - r1) / max(0.01, (y1 - y0)), math.sin(am))
            if r1 < 1e-4: self.tri((a0[0], y0, a0[1]), (b0[0], y0, b0[1]), (cx, y1, cz), col, nrm)
            else: self.quad((a0[0], y0, a0[1]), (b0[0], y0, b0[1]), (b1[0], y1, b1[1]), (a1[0], y1, a1[1]), col, nrm)
        if top and r1 > 1e-4: self.poly([(p[0], y1, p[1]) for p in pts1], colt or col, (0, 1, 0))

    def sphere(self, cx, cy, cz, r, col, seg=6, rings=4, sy=1.0):
        """esfera baixa (copa de arvore): faixas de quads"""
        P = []
        for j in range(rings + 1):
            th = math.pi * j / rings
            P.append([(cx + math.sin(th) * math.cos(2 * math.pi * i / seg) * r, cy + math.cos(th) * r * sy, cz + math.sin(th) * math.sin(2 * math.pi * i / seg) * r) for i in range(seg)])
        for j in range(rings):
            for i in range(seg):
                a, b = P[j][i], P[j][(i + 1) % seg]; c, d = P[j + 1][(i + 1) % seg], P[j + 1][i]
                mx = (a[0] + b[0] + c[0] + d[0]) / 4 - cx; my = (a[1] + b[1] + c[1] + d[1]) / 4 - cy; mz = (a[2] + b[2] + c[2] + d[2]) / 4 - cz
                cc = shade(col, int(-18 + 30 * (my / max(r * sy, 0.01) + 1) / 2))
                if j == 0: self.tri(a, c, d, cc, (mx, my, mz))
                elif j == rings - 1: self.tri(a, b, d, cc, (mx, my, mz))
                else: self.quad(a, b, c, d, cc, (mx, my, mz))

    def flat(self, poly, y, col, holes=None, n=(0, 1, 0)):
        """poligono qualquer (com buracos) plano em y, triangulado (earcut)"""
        import mapbox_earcut as ec
        rings = [poly] + (holes or [])
        verts = []; ends = []
        for r in rings:
            r = list(r)
            if len(r) > 1 and r[0] == r[-1]: r = r[:-1]
            verts.extend(r); ends.append(len(verts))
        if len(verts) < 3: return
        V = np.array(verts, dtype=np.float64)
        try: tri = ec.triangulate_float64(V, np.array(ends, dtype=np.uint32))
        except Exception: return
        for i in range(0, len(tri), 3):
            a, b, c = V[tri[i]], V[tri[i + 1]], V[tri[i + 2]]
            self.tri((a[0], y, a[1]), (b[0], y, b[1]), (c[0], y, c[1]), col, n)

    def shp(self, geom, y, col, n=(0, 1, 0)):
        """desenha um poligono/multipoligono do shapely plano em y"""
        if geom is None or geom.is_empty: return
        gs = getattr(geom, 'geoms', [geom])
        for g in gs:
            if g.geom_type != 'Polygon' or g.area < 0.01: continue
            self.flat(list(g.exterior.coords), y, col, [list(r.coords) for r in g.interiors], n)

    def wall_strip(self, line, y0, y1, th, col, top=True):
        """muro/cerca ao longo de uma polilinha (x,z)"""
        for i in range(len(line) - 1):
            a, b = line[i], line[i + 1]
            dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz)
            if L < 1e-3: continue
            nx, nz = -dz / L * th / 2, dx / L * th / 2
            self.prism([(a[0] - nx, a[1] - nz), (b[0] - nx, b[1] - nz), (b[0] + nx, b[1] + nz), (a[0] + nx, a[1] + nz)], y0, y1, col, top)

    # ---------------------------------------------------------------- saida
    def stats(self):
        out = {}
        for (ti, tj, lay), lst in self.data.items():
            out[lay] = out.get(lay, 0) + sum(len(c.idx) // 3 for c in lst)
        return out


class Frame:
    """referencial de um lote/construcao: origem o (x,z), eixo u (ao longo da rua) e v (para dentro do lote)"""
    def __init__(self, o, u):
        self.ox, self.oz = o; L = math.hypot(u[0], u[1])
        self.ux, self.uz = u[0] / L, u[1] / L
        self.vx, self.vz = -self.uz, self.ux

    def flipv(self):
        self.vx, self.vz = -self.vx, -self.vz; return self

    def xz(self, u, v): return (self.ox + self.ux * u + self.vx * v, self.oz + self.uz * u + self.vz * v)

    def p(self, u, v, y): x, z = self.xz(u, v); return (x, y, z)

    def rect(self, u0, u1, v0, v1): return [self.xz(u0, v0), self.xz(u1, v0), self.xz(u1, v1), self.xz(u0, v1)]

    def nu(self, s=1): return (self.ux * s, 0, self.uz * s)

    def nv(self, s=1): return (self.vx * s, 0, self.vz * s)


# ======================================================================== GLB
def _pad4(b, fill=b'\x00'):
    return b + fill * ((4 - len(b) % 4) % 4)


def write_glb(path, nodes_spec, extras=None):
    """nodes_spec: lista de (nome, translacao (x,y,z), [chunks]) ; cada chunk vira uma primitiva com POSITION/NORMAL/COLOR_0/indices"""
    bin_ = bytearray(); bviews = []; accs = []; meshes = []; nodes = []
    mat = [{'name': 'cidade', 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 0.0, 'roughnessFactor': 1.0}, 'doubleSided': False}]

    def add_view(data, target):
        nonlocal bin_
        off = len(bin_); bin_ += data
        while len(bin_) % 4: bin_ += b'\x00'
        bviews.append({'buffer': 0, 'byteOffset': off, 'byteLength': len(data), **({'target': target} if target else {})})
        return len(bviews) - 1

    ntri = 0
    for (name, tr, chunks) in nodes_spec:
        prims = []
        for c in chunks:
            if not len(c.idx): continue
            pn = np.frombuffer(c.pn.tobytes(), np.float32).reshape(-1, 6).copy()
            pn[:, 0] -= tr[0]; pn[:, 1] -= tr[1]; pn[:, 2] -= tr[2]
            pos = np.ascontiguousarray(pn[:, 0:3]); nrm = pn[:, 3:6]
            ln = np.linalg.norm(nrm, axis=1, keepdims=True); ln[ln < 1e-9] = 1; nrm = np.ascontiguousarray(nrm / ln, dtype=np.float32)
            col = np.frombuffer(c.col.tobytes(), np.uint8)
            idx = np.frombuffer(c.idx.tobytes(), np.uint16)
            vp = add_view(pos.tobytes(), 34962); vn = add_view(nrm.tobytes(), 34962); vc = add_view(col.tobytes(), 34962)
            vi = add_view(idx.tobytes(), 34963)
            nv = len(pos)
            accs.append({'bufferView': vp, 'componentType': 5126, 'count': nv, 'type': 'VEC3', 'min': pos.min(0).tolist(), 'max': pos.max(0).tolist()}); ap = len(accs) - 1
            accs.append({'bufferView': vn, 'componentType': 5126, 'count': nv, 'type': 'VEC3'}); an = len(accs) - 1
            accs.append({'bufferView': vc, 'componentType': 5121, 'normalized': True, 'count': nv, 'type': 'VEC4'}); ac = len(accs) - 1
            accs.append({'bufferView': vi, 'componentType': 5123, 'count': len(idx), 'type': 'SCALAR'}); ai = len(accs) - 1
            prims.append({'attributes': {'POSITION': ap, 'NORMAL': an, 'COLOR_0': ac}, 'indices': ai, 'material': 0})
            ntri += len(idx) // 3
        if not prims: continue
        meshes.append({'name': name, 'primitives': prims})
        nodes.append({'name': name, 'mesh': len(meshes) - 1, 'translation': [float(tr[0]), float(tr[1]), float(tr[2])]})
    gl = {'asset': {'version': '2.0', 'generator': 'meu-lar gen-cidade6'}, 'scene': 0, 'scenes': [{'name': 'cidade', 'nodes': list(range(len(nodes)))}],
          'nodes': nodes, 'meshes': meshes, 'materials': mat, 'accessors': accs, 'bufferViews': bviews, 'buffers': [{'byteLength': len(bin_)}]}
    if extras: gl['extras'] = extras
    js = _pad4(json.dumps(gl, separators=(',', ':')).encode(), b' ')
    bb = _pad4(bytes(bin_))
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bb)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(bb), 0x004E4942)); f.write(bb)
    return ntri


def read_glb(path):
    """leitor de conferencia: devolve lista de (nome, pos Nx3 mundo, nrm Nx3, cor Nx3 0..1, idx)"""
    raw = open(path, 'rb').read()
    jl = struct.unpack_from('<I', raw, 12)[0]; g = json.loads(raw[20:20 + jl]); bo = 20 + jl + 8; b = raw[bo:]
    def acc(i, dt, k):
        a = g['accessors'][i]; v = g['bufferViews'][a['bufferView']]
        return np.frombuffer(b, dt, a['count'] * k, v.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(a['count'], k) if k > 1 else np.frombuffer(b, dt, a['count'], v.get('byteOffset', 0) + a.get('byteOffset', 0))
    out = []
    for nd in g['nodes']:
        if 'mesh' not in nd: continue
        t = np.array(nd.get('translation', [0, 0, 0]), np.float32)
        for p in g['meshes'][nd['mesh']]['primitives']:
            at = p['attributes']
            pos = acc(at['POSITION'], np.float32, 3) + t; nrm = acc(at['NORMAL'], np.float32, 3); col = acc(at['COLOR_0'], np.uint8, 4)[:, :3] / 255.0
            idx = acc(p['indices'], np.uint16, 1).astype(np.int64)
            out.append((nd['name'], pos, nrm, col, idx))
    return out, g
