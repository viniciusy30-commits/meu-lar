"""Visualizador oblíquo simples (algoritmo do pintor) da malha assada, so para conferir a geometria."""
import math
from PIL import Image, ImageDraw

def terrain_tris(hf, cx, cz, radius, step=8.0):
    out = []
    i0 = max(int((cx - radius) / step), 0); i1 = min(int((cx + radius) / step) + 1, hf.shape[1] - 2); j0 = max(int((cz - radius) / step), 0); j1 = min(int((cz + radius) / step) + 1, hf.shape[0] - 2)
    for j in range(j0, j1):
        for i in range(i0, i1):
            h = [hf[j, i], hf[j, i + 1], hf[j + 1, i + 1], hf[j + 1, i]]; avg = sum(h) / 4
            P = [(i * step, h[0], j * step), ((i + 1) * step, h[1], j * step), ((i + 1) * step, h[2], (j + 1) * step), (i * step, h[3], (j + 1) * step)]
            if avg < -0.1: col = (58, 148, 190); P = [(p[0], -0.4, p[2]) for p in P]
            elif avg < 1.3: col = (226, 208, 160)
            elif avg > 60: col = (118, 110, 98)
            else: col = (104, 150, 86)
            dx = (h[1] - h[0] + h[2] - h[3]) / (2 * step); dz = (h[3] - h[0] + h[2] - h[1]) / (2 * step); l = math.sqrt(dx * dx + 1 + dz * dz); n = (-dx / l, 1 / l, -dz / l)
            for tri in ((P[0], P[1], P[2]), (P[0], P[2], P[3])): out.append([(p[0], p[1], p[2], n[0], n[1], n[2], 0, 0, col[0], col[1], col[2]) for p in tri])
    return out

def render(bake, cx, cy, cz, radius, yaw, pitch, path, size=1000, dist=None, hf=None):
    tris = terrain_tris(hf, cx, cz, radius * 1.5) if hf is not None else []
    for (cell, mat), verts in bake.tris.items():
        for i in range(0, len(verts), 3):
            v = verts[i:i + 3]
            mx = sum(p[0] for p in v) / 3; mz = sum(p[2] for p in v) / 3
            if abs(mx - cx) > radius or abs(mz - cz) > radius: continue
            tris.append(v)
    cyaw, syaw = math.cos(yaw), math.sin(yaw); cp, sp = math.cos(pitch), math.sin(pitch)
    D = dist or radius * 2.2
    def proj(p):
        x, y, z = p[0] - cx, p[1] - cy, p[2] - cz
        x1 = x * cyaw - z * syaw; z1 = x * syaw + z * cyaw
        y1 = y * cp - z1 * sp; z2 = y * sp + z1 * cp
        w = D + z2
        f = size * 0.9 / (2 * radius) * (D / max(w, 1))
        return size / 2 + x1 * f, size / 2 - y1 * f, z2
    items = []
    L = (0.45, 0.8, 0.3); ln = math.sqrt(sum(a * a for a in L)); L = tuple(a / ln for a in L)
    for v in tris:
        q = [proj(p) for p in v]
        dep = sum(a[2] for a in q) / 3
        n = v[0][3:6]
        sh = 0.55 + 0.45 * max(0.0, n[0] * L[0] + n[1] * L[1] + n[2] * L[2]) if (n[0] or n[1] or n[2]) else 0.9
        col = tuple(min(255, int(c * sh)) for c in v[0][8:11])
        items.append((dep, [(a[0], a[1]) for a in q], col))
    items.sort(key=lambda t: -t[0])
    im = Image.new('RGB', (size, size), (150, 190, 225)); d = ImageDraw.Draw(im)
    for dep, pts, col in items: d.polygon(pts, fill=col)
    im.save(path)
