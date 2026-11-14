"""Cidade 6 - construtor de malha indexada por TILE, CAMADA e MATERIAL; primitivas geometricas; gravador GLB com texturas.

Coordenadas do mundo: X leste (0..W), Z sul (0..H), Y para cima, em metros (o mesmo eixo do glTF).
Cada elemento vai para o tile do "ancora" atual (o objeto inteiro fica num tile so) ou, sem ancora, para o tile do seu centro.
Cada (tile, camada, material) guarda pedacos com menos de 65 mil vertices (o leitor GLB do jogo usa indices de 16 bits).
UV: sem UV explicito, projecao planar no mundo na escala do material (metros por repeticao da textura)."""
import math, struct, json, os
from array import array
import numpy as np
from textures6 import MATS

TILE = 250.0
MAXV = 65000


def rgb(h):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def shade(c, d):
    return tuple(max(0, min(255, int(v + d))) for v in c)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


WHITE = (255, 255, 255)


class Chunk:
    __slots__ = ('pn', 'uv', 'col', 'idx', 'nv')

    def __init__(self):
        self.pn = array('f'); self.uv = array('f'); self.col = array('B'); self.idx = array('H'); self.nv = 0


class Mesh:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.nx, self.nz = int(math.ceil(W / TILE)), int(math.ceil(H / TILE))
        self.data = {}            # (ti, tj, camada, material) -> [Chunk]
        self.anchor = None
        self.layer = 'geral'
        self.mat = 'liso'
        self.ntri = 0
        self.ao = True

    # ---------------------------------------------------------------- contexto
    def at(self, x, z, layer=None):
        self.anchor = (x, z)
        if layer: self.layer = layer
        return self

    def free(self, layer=None):
        self.anchor = None
        if layer: self.layer = layer
        return self

    def m(self, mat):
        """material atual; devolve o anterior"""
        old = self.mat; self.mat = mat; return old

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
    def poly(self, pts, col, n=None, uv=None):
        """poligono convexo plano (lista de (x,y,z)); n: normal desejada (o sentido dos indices segue n); uv: lista de (u,v) opcional"""
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
        if n is not None and gx * n[0] + gy * n[1] + gz * n[2] < 0: rev = True; gx, gy, gz = -gx, -gy, -gz
        if self.anchor is not None: cx, cz = self.anchor
        else: cx = sum(p[0] for p in pts) / k; cz = sum(p[2] for p in pts) / k
        t = self.tile_of(cx, cz)
        c = self._chunk((t[0], t[1], self.layer, self.mat), k)
        base = c.nv
        if uv is None:
            su, sv = MATS.get(self.mat, (None, (1.0, 1.0)))[1]
            if abs(gy) > 0.7:
                uv = [(p[0] / su, p[2] / sv) for p in pts]
            else:
                hl = math.hypot(gx, gz) or 1.0; tx, tz = -gz / hl, gx / hl
                uv = [((p[0] * tx + p[2] * tz) / su, -p[1] / sv) for p in pts]
        multi = isinstance(col[0], (tuple, list))
        for i, p in enumerate(pts):
            cc = col[i] if multi else col
            c.pn.extend((p[0], p[1], p[2], gx, gy, gz)); c.uv.extend(uv[i]); c.col.extend((cc[0], cc[1], cc[2], 255))
        c.nv += k
        for i in range(1, k - 1):
            if rev: c.idx.extend((base, base + i + 1, base + i))
            else: c.idx.extend((base, base + i, base + i + 1))
        self.ntri += k - 2

    def tri(self, a, b, c, col, n=None, uv=None): self.poly([a, b, c], col, n, uv)

    def quad(self, a, b, c, d, col, n=None, uv=None): self.poly([a, b, c, d], col, n, uv)

    def smooth_grid(self, P, N, C):
        """grade com normais suaves (terreno): P, N, C arrays (nz, nx, 3)"""
        nz, nx = P.shape[:2]
        su, sv = MATS.get(self.mat, (None, (1.0, 1.0)))[1]
        for j in range(nz - 1):
            for i in range(nx - 1):
                q = ((j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i))
                cx = (P[j, i, 0] + P[j, i + 1, 0]) / 2; cz = (P[j, i, 2] + P[j + 1, i, 2]) / 2
                t = self.tile_of(cx, cz)
                ch = self._chunk((t[0], t[1], self.layer, self.mat), 4)
                base = ch.nv
                for (a, b) in q:
                    x, y, z = float(P[a, b, 0]), float(P[a, b, 1]), float(P[a, b, 2])
                    ch.pn.extend((x, y, z, float(N[a, b, 0]), float(N[a, b, 1]), float(N[a, b, 2])))
                    ch.uv.extend((x / su, z / sv))
                    ch.col.extend((int(C[a, b, 0]), int(C[a, b, 1]), int(C[a, b, 2]), 255))
                ch.nv += 4
                ch.idx.extend((base, base + 3, base + 2, base, base + 2, base + 1))
                self.ntri += 2

    # ---------------------------------------------------------------- solidos
    def prism(self, c4, y0, y1, col, top=True, bottom=False, colt=None, sides=None, mat_top=None, wall_uv=None):
        """prisma vertical sobre poligono convexo (lista de (x,z)); wall_uv=(su, sv, v0): UV das paredes
        corrido ao longo do contorno (fachadas: janelas alinhadas nas quinas)"""
        n = len(c4)
        cx = sum(p[0] for p in c4) / n; cz = sum(p[1] for p in c4) / n
        run = 0.0
        for k in range(n):
            a = c4[k]; b = c4[(k + 1) % n]
            ex, ez = b[0] - a[0], b[1] - a[1]; L = math.hypot(ex, ez)
            if L < 1e-6: continue
            fx, fz = ez / L, -ex / L
            if fx * ((a[0] + b[0]) / 2 - cx) + fz * ((a[1] + b[1]) / 2 - cz) < 0: fx, fz = -fx, -fz
            cc = col if sides is None else sides[k % len(sides)]
            uv = None
            if wall_uv:
                su, sv, v0 = wall_uv
                u0 = round(run / su); u1 = u0 + max(1, round(L / su))
                uv = [(u0, (v0 - y0) / sv), (u1, (v0 - y0) / sv), (u1, (v0 - y1) / sv), (u0, (v0 - y1) / sv)]
                run += L
            if y0 < 1.0 and y1 - y0 > 1.2 and self.ao:          # sombra de contato: base da parede mais escura
                ym = min(y1, y0 + 1.4); cd = shade(cc, -38); cm = cc
                if uv: uvm = [(uv[0][0], uv[0][1] + (uv[3][1] - uv[0][1]) * (ym - y0) / (y1 - y0)), (uv[1][0], uv[1][1] + (uv[2][1] - uv[1][1]) * (ym - y0) / (y1 - y0))]
                self.quad((a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], ym, b[1]), (a[0], ym, a[1]), [cd, cd, cm, cm], (fx, 0, fz), [uv[0], uv[1], uvm[1], uvm[0]] if uv else None)
                if y1 > ym + 0.01: self.quad((a[0], ym, a[1]), (b[0], ym, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1]), cc, (fx, 0, fz), [uvm[0], uvm[1], uv[2], uv[3]] if uv else None)
            else:
                self.quad((a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1]), cc, (fx, 0, fz), uv)
        if top or bottom:
            old = self.mat
            if mat_top: self.mat = mat_top
            if top: self.poly([(p[0], y1, p[1]) for p in c4], colt or col, (0, 1, 0))
            if bottom: self.poly([(p[0], y0, p[1]) for p in c4], col, (0, -1, 0))
            self.mat = old

    def box(self, x0, x1, y0, y1, z0, z1, col, top=True, bottom=False, colt=None):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, col, top, bottom, colt)

    def cyl(self, cx, cz, r, y0, y1, col, seg=8, top=True, r1=None, colt=None):
        r1 = r if r1 is None else r1
        pts0 = [(cx + math.cos(2 * math.pi * i / seg) * r, cz + math.sin(2 * math.pi * i / seg) * r) for i in range(seg)]
        pts1 = [(cx + math.cos(2 * math.pi * i / seg) * r1, cz + math.sin(2 * math.pi * i / seg) * r1) for i in range(seg)]
        circ = 2 * math.pi * max(r, 0.05)
        for i in range(seg):
            a0, b0 = pts0[i], pts0[(i + 1) % seg]; a1, b1 = pts1[i], pts1[(i + 1) % seg]
            am = 2 * math.pi * (i + 0.5) / seg
            nrm = (math.cos(am), (r - r1) / max(0.01, (y1 - y0)), math.sin(am))
            uu0, uu1 = i / seg * circ, (i + 1) / seg * circ
            if r1 < 1e-4: self.tri((a0[0], y0, a0[1]), (b0[0], y0, b0[1]), (cx, y1, cz), col, nrm, [(uu0, -y0), (uu1, -y0), ((uu0 + uu1) / 2, -y1)])
            else: self.quad((a0[0], y0, a0[1]), (b0[0], y0, b0[1]), (b1[0], y1, b1[1]), (a1[0], y1, a1[1]), col, nrm, [(uu0, -y0), (uu1, -y0), (uu1, -y1), (uu0, -y1)])
        if top and r1 > 1e-4: self.poly([(p[0], y1, p[1]) for p in pts1], colt or col, (0, 1, 0))

    def indexed(self, P, N, UV, C, T):
        """grupo indexado com vertices compartilhados (normais suaves): P/N lista (x,y,z), UV (u,v), C (r,g,b), T triangulos (i,j,k)"""
        if self.anchor is not None: cx, cz = self.anchor
        else: cx = sum(p[0] for p in P) / len(P); cz = sum(p[2] for p in P) / len(P)
        t = self.tile_of(cx, cz)
        c = self._chunk((t[0], t[1], self.layer, self.mat), len(P))
        base = c.nv
        for i, p in enumerate(P):
            n = N[i]; L = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]) or 1.0
            c.pn.extend((p[0], p[1], p[2], n[0] / L, n[1] / L, n[2] / L)); c.uv.extend(UV[i]); c.col.extend((C[i][0], C[i][1], C[i][2], 255))
        c.nv += len(P)
        for (a, b, d) in T: c.idx.extend((base + a, base + b, base + d))
        self.ntri += len(T)

    def sphere(self, cx, cy, cz, r, col, seg=6, rings=4, sy=1.0, jit=0.0, rnd=None):
        """esfera com vertices compartilhados e normais suaves (copa de arvore); jit: irregularidade do contorno"""
        P, N, UV, C, T = [], [], [], [], []
        import random as _r
        rr = rnd or _r
        P.append((cx, cy + r * sy, cz)); N.append((0, 1, 0)); UV.append((0.5, 0)); C.append(shade(col, 14))
        for j in range(1, rings):
            th = math.pi * j / rings; y = math.cos(th)
            cc = shade(col, int(-22 + 36 * (y + 1) / 2))
            for i in range(seg):
                ph = 2 * math.pi * i / seg + (0.5 if j % 2 else 0) * 2 * math.pi / seg
                nx, nz = math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph)
                k = 1.0 + (rr.uniform(-jit, jit) if jit else 0.0)
                P.append((cx + nx * r * k, cy + y * r * sy * k, cz + nz * r * k)); N.append((nx, y, nz)); UV.append((i * 0.6, j * 0.6)); C.append(shade(cc, int(rr.uniform(-10, 10)) if jit else 0))
        P.append((cx, cy - r * sy, cz)); N.append((0, -1, 0)); UV.append((0.5, rings * 0.6)); C.append(shade(col, -26))
        bot = len(P) - 1
        ring = lambda j, i: 1 + (j - 1) * seg + (i % seg)
        for i in range(seg):
            T.append((0, ring(1, i + 1), ring(1, i)))
            T.append((bot, ring(rings - 1, i), ring(rings - 1, i + 1)))
        for j in range(1, rings - 1):
            for i in range(seg):
                a, b = ring(j, i), ring(j, i + 1); c2, d = ring(j + 1, i), ring(j + 1, i + 1)
                if j % 2: T.append((a, b, d)); T.append((a, d, c2))
                else: T.append((a, b, c2)); T.append((b, d, c2))
        self.indexed(P, N, UV, C, T)

    def smooth_cyl(self, cx, cz, r, y0, y1, col, seg=6, r1=None):
        """tronco/cone com normais suaves e vertices compartilhados (sem tampa)"""
        r1 = r if r1 is None else r1
        P, N, UV, C, T = [], [], [], [], []
        slope = (r - r1) / max(0.01, y1 - y0)
        for i in range(seg + 1):
            a = 2 * math.pi * i / seg; ca, sa = math.cos(a), math.sin(a)
            P.append((cx + ca * r, y0, cz + sa * r)); N.append((ca, slope, sa)); UV.append((i / seg, -y0)); C.append(col)
            P.append((cx + ca * max(r1, 0.0), y1, cz + sa * max(r1, 0.0))); N.append((ca, slope, sa)); UV.append((i / seg, -y1)); C.append(shade(col, 10))
        for i in range(seg):
            a, b, c2, d = 2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1
            T.append((a, d, c2)); T.append((a, c2, b))
        self.indexed(P, N, UV, C, T)

    def flat(self, poly, y, col, holes=None, n=(0, 1, 0)):
        """poligono qualquer (com buracos) plano em y, triangulado (earcut)"""
        import mapbox_earcut as ec
        rings = [poly] + (holes or [])
        verts = []; ends = []
        for r in rings:
            r = list(r)
            if len(r) > 1 and tuple(r[0]) == tuple(r[-1]): r = r[:-1]
            verts.extend(r); ends.append(len(verts))
        if len(verts) < 3: return
        V = np.array(verts, dtype=np.float64)
        try: tri = ec.triangulate_float64(V, np.array(ends, dtype=np.uint32))
        except Exception: return
        for i in range(0, len(tri), 3):
            a, b, c = V[tri[i]], V[tri[i + 1]], V[tri[i + 2]]
            self.tri((a[0], y, a[1]), (b[0], y, b[1]), (c[0], y, c[1]), col, n)

    def shp(self, geom, y, col, n=(0, 1, 0)):
        """poligono/multipoligono do shapely plano em y (triangulacao de Delaunay restrita: exata com buracos)"""
        import shapely
        if geom is None or geom.is_empty: return
        for g in getattr(geom, 'geoms', [geom]):
            if g.geom_type in ('MultiPolygon', 'GeometryCollection'): self.shp(g, y, col, n); continue
            if g.geom_type != 'Polygon' or g.area < 0.01: continue
            if not g.is_valid: g = g.buffer(0)
            tris = shapely.constrained_delaunay_triangles(g)
            for t in getattr(tris, 'geoms', []):
                c = list(t.exterior.coords)[:3]
                self.tri((c[0][0], y, c[0][1]), (c[1][0], y, c[1][1]), (c[2][0], y, c[2][1]), col, n)

    def wall_strip(self, line, y0, y1, th, col, top=True):
        for i in range(len(line) - 1):
            a, b = line[i], line[i + 1]
            dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz)
            if L < 1e-3: continue
            nx, nz = -dz / L * th / 2, dx / L * th / 2
            self.prism([(a[0] - nx, a[1] - nz), (b[0] - nx, b[1] - nz), (b[0] + nx, b[1] + nz), (a[0] + nx, a[1] + nz)], y0, y1, col, top)

    # ---------------------------------------------------------------- saida
    def stats(self):
        out = {}
        for (ti, tj, lay, mat), lst in self.data.items():
            out[lay] = out.get(lay, 0) + sum(len(c.idx) // 3 for c in lst)
        return out


class Frame:
    """referencial: origem o (x,z), eixo u (ao longo da rua) e v (para dentro do lote)"""
    def __init__(self, o, u, flip=False):
        self.ox, self.oz = o; L = math.hypot(u[0], u[1])
        self.ux, self.uz = u[0] / L, u[1] / L
        self.vx, self.vz = -self.uz, self.ux
        if flip: self.vx, self.vz = -self.vx, -self.vz

    def xz(self, u, v): return (self.ox + self.ux * u + self.vx * v, self.oz + self.uz * u + self.vz * v)

    def p(self, u, v, y): x, z = self.xz(u, v); return (x, y, z)

    def rect(self, u0, u1, v0, v1): return [self.xz(u0, v0), self.xz(u1, v0), self.xz(u1, v1), self.xz(u0, v1)]

    def nu(self, s=1): return (self.ux * s, 0, self.uz * s)

    def nv(self, s=1): return (self.vx * s, 0, self.vz * s)


# ======================================================================== GLB
def _pad4(b, fill=b'\x00'):
    return b + fill * ((4 - len(b) % 4) % 4)


def write_glb(path, nodes_spec, texdir, embed=False, tex_uri_prefix='texturas/', extras=None, markers=None):
    """nodes_spec: lista de (nome, translacao, {material: [chunks]}).
    Texturas: embed=True embute os JPEG no GLB; senao referencia arquivos externos (uri = prefixo + nome.jpg)."""
    bin_ = bytearray(); bviews = []; accs = []; meshes = []; nodes = []
    mats_used = []
    for (_, _, bymat) in nodes_spec:
        for m in bymat:
            if m not in mats_used: mats_used.append(m)
    mats_used.sort()
    mid = {m: i for i, m in enumerate(mats_used)}

    def add_view(data, target=None):
        nonlocal bin_
        off = len(bin_); bin_ += data
        while len(bin_) % 4: bin_ += b'\x00'
        bv = {'buffer': 0, 'byteOffset': off, 'byteLength': len(data)}
        if target: bv['target'] = target
        bviews.append(bv); return len(bviews) - 1

    images = []; textures = []; materials = []
    for i, m in enumerate(mats_used):
        fn = os.path.join(texdir, m + '.jpg')
        if embed:
            images.append({'bufferView': add_view(open(fn, 'rb').read()), 'mimeType': 'image/jpeg', 'name': m})
        else:
            images.append({'uri': tex_uri_prefix + m + '.jpg', 'name': m})
        textures.append({'sampler': 0, 'source': i})
        materials.append({'name': m, 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'baseColorTexture': {'index': i}, 'metallicFactor': 0.0,
                                                              'roughnessFactor': 0.35 if m in ('vidro', 'vitrine', 'agua', 'escritorio') else 0.95}})
    ntri = 0
    for (name, tr, bymat) in nodes_spec:
        prims = []
        for m in sorted(bymat):
            for c in bymat[m]:
                if not len(c.idx): continue
                pn = np.frombuffer(c.pn.tobytes(), np.float32).reshape(-1, 6).copy()
                pn[:, 0] -= tr[0]; pn[:, 1] -= tr[1]; pn[:, 2] -= tr[2]
                pos = np.ascontiguousarray(pn[:, 0:3]); nrm = pn[:, 3:6]
                ln = np.linalg.norm(nrm, axis=1, keepdims=True); ln[ln < 1e-9] = 1; nrm = np.ascontiguousarray(nrm / ln, dtype=np.float32)
                uv = np.frombuffer(c.uv.tobytes(), np.float32).reshape(-1, 2)
                col = np.frombuffer(c.col.tobytes(), np.uint8).reshape(-1, 4)
                idx = np.frombuffer(c.idx.tobytes(), np.uint16).astype(np.int64)
                # funde vertices identicos (posicao, normal, uv, cor)
                key = np.hstack([np.round(pos * 1000).astype(np.int64), np.round(nrm * 1000).astype(np.int64), np.round(uv * 4096).astype(np.int64), col.astype(np.int64)])
                _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
                pos = np.ascontiguousarray(pos[first]); nrm = np.ascontiguousarray(nrm[first]); uv = np.ascontiguousarray(uv[first]); col = np.ascontiguousarray(col[first]).reshape(-1)
                idx = inv.reshape(-1)[idx].astype(np.uint16)
                nv = len(pos)
                ap = len(accs); accs.append({'bufferView': add_view(pos.tobytes(), 34962), 'componentType': 5126, 'count': nv, 'type': 'VEC3', 'min': pos.min(0).tolist(), 'max': pos.max(0).tolist()})
                an = len(accs); accs.append({'bufferView': add_view(nrm.tobytes(), 34962), 'componentType': 5126, 'count': nv, 'type': 'VEC3'})
                au = len(accs); accs.append({'bufferView': add_view(uv.tobytes(), 34962), 'componentType': 5126, 'count': nv, 'type': 'VEC2'})
                ac = len(accs); accs.append({'bufferView': add_view(col.tobytes(), 34962), 'componentType': 5121, 'normalized': True, 'count': nv, 'type': 'VEC4'})
                ai = len(accs); accs.append({'bufferView': add_view(idx.tobytes(), 34963), 'componentType': 5123, 'count': len(idx), 'type': 'SCALAR'})
                prims.append({'attributes': {'POSITION': ap, 'NORMAL': an, 'TEXCOORD_0': au, 'COLOR_0': ac}, 'indices': ai, 'material': mid[m]})
                ntri += len(idx) // 3
        if not prims: continue
        meshes.append({'name': name, 'primitives': prims})
        nodes.append({'name': name, 'mesh': len(meshes) - 1, 'translation': [float(tr[0]), float(tr[1]), float(tr[2])]})
    for (mn, mt, myaw) in (markers or []):          # nos vazios (ex.: onde vai cada casa do jogador)
        q = [0.0, math.sin(myaw / 2), 0.0, math.cos(myaw / 2)]
        nodes.append({'name': mn, 'translation': [float(v) for v in mt], 'rotation': q})
    gl = {'asset': {'version': '2.0', 'generator': 'meu-lar gen-cidade6'}, 'scene': 0, 'scenes': [{'name': 'cidade', 'nodes': list(range(len(nodes)))}],
          'nodes': nodes, 'meshes': meshes, 'materials': materials, 'textures': textures, 'images': images,
          'samplers': [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}],
          'accessors': accs, 'bufferViews': bviews, 'buffers': [{'byteLength': len(bin_)}]}
    if extras: gl['extras'] = extras
    js = _pad4(json.dumps(gl, separators=(',', ':')).encode(), b' ')
    bb = _pad4(bytes(bin_))
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bb)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(bb), 0x004E4942)); f.write(bb)
    return ntri


def read_glb(path):
    """leitor de conferencia: lista de (no, material, pos Nx3 mundo, nrm, uv, cor Nx3 0..1, idx)"""
    raw = open(path, 'rb').read()
    jl = struct.unpack_from('<I', raw, 12)[0]; g = json.loads(raw[20:20 + jl]); bo = 20 + jl + 8; b = raw[bo:]
    def acc(i, dt, k):
        a = g['accessors'][i]; v = g['bufferViews'][a['bufferView']]
        arr = np.frombuffer(b, dt, a['count'] * k, v.get('byteOffset', 0) + a.get('byteOffset', 0))
        return arr.reshape(a['count'], k) if k > 1 else arr
    out = []
    for nd in g['nodes']:
        if 'mesh' not in nd: continue
        t = np.array(nd.get('translation', [0, 0, 0]), np.float32)
        for p in g['meshes'][nd['mesh']]['primitives']:
            at = p['attributes']
            out.append((nd['name'], g['materials'][p['material']]['name'], acc(at['POSITION'], np.float32, 3) + t, acc(at['NORMAL'], np.float32, 3),
                        acc(at['TEXCOORD_0'], np.float32, 2), acc(at['COLOR_0'], np.uint8, 4)[:, :3] / 255.0, acc(p['indices'], np.uint16, 1).astype(np.int64)))
    return out, g
