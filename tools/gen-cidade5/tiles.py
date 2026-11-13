"""Gera fotos (vista de cima) de TODAS as ruas, em ladrilhos numerados, para conferencia."""
import math, os
from PIL import Image, ImageDraw
import prev_ground
from plan import *

def bucket(g):
    B = {}
    for name, pts in g.layers:
        xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
        B.setdefault(name, []).append((min(xs), min(zs), max(xs), max(zs), pts))
    return B

def tile(B, cx, cz, half, ppm, path, label):
    S = int(2 * half * ppm); im = Image.new('RGB', (S, S), (104, 138, 88)); d = ImageDraw.Draw(im)
    def P(p): return ((p[0] - cx + half) * ppm, (p[1] - cz + half) * ppm)
    for lay in prev_ground.ORDER:
        c = prev_ground.CO[lay]
        for (x0, z0, x1, z1, pts) in B.get(lay, ()):
            if x1 < cx - half or x0 > cx + half or z1 < cz - half or z0 > cz + half: continue
            d.polygon([P(p) for p in pts], fill=c)
    d.rectangle([0, 0, S - 1, 22], fill=(20, 20, 24)); d.text((8, 5), label, fill=(255, 255, 255))
    # escala 50 m
    d.line([(S - 20 - 50 * ppm, S - 16), (S - 20, S - 16)], fill=(255, 255, 255), width=3); d.text((S - 20 - 50 * ppm, S - 32), '50 m', fill=(255, 255, 255))
    im.save(path)

def make_all(g, c, outdir, half=200, ppm=3.0):
    os.makedirs(outdir, exist_ok=True)
    B = bucket(g)
    xs = [n[0] for n in c.nodes]; zs = [n[1] for n in c.nodes]
    x0, x1, z0, z1 = min(xs) - 40, max(xs) + 40, min(zs) - 40, max(zs) + 40
    nxt = int(math.ceil((x1 - x0) / (2 * half))); nzt = int(math.ceil((z1 - z0) / (2 * half)))
    made = []; idx = 0
    for j in range(nzt):
        for i in range(nxt):
            cx = x0 + (i + 0.5) * 2 * half; cz = z0 + (j + 0.5) * 2 * half
            has = any(abs(n[0] - cx) < half + 20 and abs(n[1] - cz) < half + 20 for n in c.nodes) or any(
                min(p[0] for p in e['p']) < cx + half and max(p[0] for p in e['p']) > cx - half and min(p[1] for p in e['p']) < cz + half and max(p[1] for p in e['p']) > cz - half for e in c.edges)
            if not has: continue
            idx += 1
            path = os.path.join(outdir, f'foto_{idx:02d}.png')
            tile(B, cx, cz, half, ppm, path, f'FOTO {idx:02d}   centro x={cx:.0f} z={cz:.0f}   ({2*half:.0f} x {2*half:.0f} m)')
            made.append((idx, cx, cz, i, j, path))
    # mapa-indice
    sc = 0.28
    ov = Image.new('RGB', (int(WX * sc), int(WZ * sc)), (60, 90, 70)); d = ImageDraw.Draw(ov)
    for name in ('asphalt', 'sidewalk', 'island'):
        col = prev_ground.CO[name] if name != 'sidewalk' else (200, 170, 150)
        for (a, b, cc, dd, pts) in B.get(name, ()): d.polygon([(p[0] * sc, p[1] * sc) for p in pts], fill=col)
    for (idx, cx, cz, i, j, path) in made:
        d.rectangle([(cx - half) * sc, (cz - half) * sc, (cx + half) * sc, (cz + half) * sc], outline=(255, 215, 0))
        d.text(((cx - half) * sc + 4, (cz - half) * sc + 4), str(idx), fill=(255, 255, 255))
    ov.save(os.path.join(outdir, '00_mapa_indice.png'))
    return made
