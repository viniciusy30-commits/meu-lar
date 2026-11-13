"""Malha assada do bairro (Cidade 3): triângulos soltos por material e por pedaço de terreno de 64 m.
Coordenadas RELATIVAS ao canto do mapa (o app soma CX, CZ). Convenção igual à do Relevo.kt:
  frente de uma face = lado da normal; ordem dos vértices ajustada pela normal.
Materiais (Mt do app): PLAIN 0, TILE 3, STONE 4, PLASTER 5, WOOD 6, GRASS 8, PAVER 9, METAL 11, ROOF 14.
"""
import math, struct
from collections import defaultdict

PLAIN, TILE, STONE, PLASTER, WOOD, GRASS, PAVER, METAL, ROOF = 0, 3, 4, 5, 6, 8, 9, 11, 14
CELL = 64.0


def rgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def shade(c, d):
    return tuple(max(0, min(255, v + d)) for v in c)


def mixc(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


class Bake:
    def __init__(self):
        self.tris = defaultdict(list)     # (cj*1000+ci, mat) -> lista de vértices (x,y,z,nx,ny,nz,u,v,r,g,b)
        self.ntri = 0

    # ---- primitivas -----------------------------------------------------------------------------
    def tri(self, mat, p0, p1, p2, n, col, uv=None, lit=True):
        ax, ay, az = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        bx, by, bz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
        gx, gy, gz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
        if gx * gx + gy * gy + gz * gz < 1e-10:
            return
        order = (0, 1, 2)
        if gx * n[0] + gy * n[1] + gz * n[2] < 0:
            order = (0, 2, 1)
        pts = (p0, p1, p2)
        if uv is None:
            uv = ((p0[0], p0[2]), (p1[0], p1[2]), (p2[0], p2[2]))
        cx = (p0[0] + p1[0] + p2[0]) / 3.0
        cz = (p0[2] + p1[2] + p2[2]) / 3.0
        key = (int(max(0, cz) // CELL) * 1000 + int(max(0, cx) // CELL), mat)
        l = 1.0 if lit else 0.0
        out = self.tris[key]
        for i in order:
            p = pts[i]
            out.append((p[0], p[1], p[2], n[0] * l, n[1] * l, n[2] * l, uv[i][0], uv[i][1], col[0], col[1], col[2]))
        self.ntri += 1

    def quad(self, mat, p, n, col, uv=None, lit=True):
        u = uv if uv is not None else [(q[0], q[2]) for q in p]
        self.tri(mat, p[0], p[1], p[2], n, col, (u[0], u[1], u[2]), lit)
        self.tri(mat, p[0], p[2], p[3], n, col, (u[0], u[2], u[3]), lit)

    def poly(self, mat, pts, n, col, lit=True):
        """polígono convexo (leque)"""
        for i in range(1, len(pts) - 1):
            self.tri(mat, pts[0], pts[i], pts[i + 1], n, col, None, lit)

    def box(self, cx, cz, sx, sz, y0, y1, col, mat=PLAIN, top=True, bottom=False, uvs=1.0):
        """caixa alinhada aos eixos (cx,cz = centro; sx,sz = tamanho)"""
        x0, x1, z0, z1 = cx - sx / 2, cx + sx / 2, cz - sz / 2, cz + sz / 2
        self.obox_pts([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, col, mat, top, bottom, uvs)

    def obox_pts(self, c4, y0, y1, col, mat=PLAIN, top=True, bottom=False, uvs=1.0):
        """prisma vertical sobre um quadrilátero convexo (4 pontos xz em ordem)"""
        cx = sum(p[0] for p in c4) / 4.0
        cz = sum(p[1] for p in c4) / 4.0
        for k in range(4):
            a = c4[k]; b = c4[(k + 1) % 4]
            nx, nz = (a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cz
            # normal da face = perpendicular à aresta apontando para fora
            ex, ez = b[0] - a[0], b[1] - a[1]
            L = math.hypot(ex, ez)
            if L < 1e-6:
                continue
            fx, fz = ez / L, -ex / L
            if fx * nx + fz * nz < 0:
                fx, fz = -fx, -fz
            self.quad(mat, [(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])], (fx, 0, fz), col,
                      [(0, y0 * uvs), (L * uvs, y0 * uvs), (L * uvs, y1 * uvs), (0, y1 * uvs)])
        if top:
            self.quad(mat, [(p[0], y1, p[1]) for p in c4], (0, 1, 0), col)
        if bottom:
            self.quad(mat, [(p[0], y0, p[1]) for p in c4], (0, -1, 0), col)

    def cyl(self, cx, cz, r, y0, y1, col, seg=8, mat=PLAIN, top=True, r2=None):
        r2 = r if r2 is None else r2
        for i in range(seg):
            a0 = 2 * math.pi * i / seg; a1 = 2 * math.pi * (i + 1) / seg
            am = (a0 + a1) / 2
            p = [(cx + math.cos(a0) * r, y0, cz + math.sin(a0) * r), (cx + math.cos(a1) * r, y0, cz + math.sin(a1) * r),
                 (cx + math.cos(a1) * r2, y1, cz + math.sin(a1) * r2), (cx + math.cos(a0) * r2, y1, cz + math.sin(a0) * r2)]
            self.quad(mat, p, (math.cos(am), 0.0, math.sin(am)), col, [(0, 0), (1, 0), (1, 1), (0, 1)])
            if top and r2 > 0.001:
                self.tri(mat, (cx, y1, cz), p[3], p[2], (0, 1, 0), col)

    # ---- saída ----------------------------------------------------------------------------------
    def write(self, path):
        recs = []
        for (cell, mat), verts in sorted(self.tris.items()):
            if not verts:
                continue
            recs.append((cell, mat, verts))
        with open(path, 'wb') as f:
            f.write(b'SUB1')
            f.write(struct.pack('<i', len(recs)))
            for cell, mat, verts in recs:
                ymax = max(v[1] for v in verts)
                f.write(struct.pack('<iiif', cell, mat, len(verts), ymax))
                for v in verts:
                    f.write(struct.pack('<8f3B', v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8], v[9], v[10]))
        return len(recs)
