"""Visualizador oblíquo simples (algoritmo do pintor) da malha assada, so para conferir a geometria."""
import math
from PIL import Image, ImageDraw

def render(bake, cx, cy, cz, radius, yaw, pitch, path, size=1000, dist=None):
    tris = []
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
    d.rectangle([0, size * 0.62, size, size], fill=(106, 140, 90))
    for dep, pts, col in items: d.polygon(pts, fill=col)
    im.save(path)
