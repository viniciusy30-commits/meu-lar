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

def terrain_bg(hf, cx, cz, half, ppm):
    import numpy as np
    S = int(2 * half * ppm)
    xs = cx - half + (np.arange(S) + 0.5) / ppm; zs = cz - half + (np.arange(S) + 0.5) / ppm
    fx = np.clip(xs / 8.0, 0, hf.shape[1] - 1.001); fz = np.clip(zs / 8.0, 0, hf.shape[0] - 1.001)
    i0 = fx.astype(int); j0 = fz.astype(int); ax = (fx - i0)[None, :]; az = (fz - j0)[:, None]
    H = (hf[np.ix_(j0, i0)] * (1 - ax) + hf[np.ix_(j0, i0 + 1)] * ax) * (1 - az) + (hf[np.ix_(j0 + 1, i0)] * (1 - ax) + hf[np.ix_(j0 + 1, i0 + 1)] * ax) * az
    gz, gx = np.gradient(H, 1.0 / ppm)
    sh = np.clip(0.80 + 1.4 * (-gx * 0.6 - gz * 0.8), 0.55, 1.15)
    col = np.zeros(H.shape + (3,), float)
    col[:] = (110, 148, 92); hi = np.clip(H / 90.0, 0, 1)[..., None]
    col = col * (1 - hi) + np.array([96, 120, 78]) * hi
    col = np.where((H > 120)[..., None], np.array([130, 122, 110]), col)
    col = np.where(((H < 1.3) & (H > 0.0))[..., None], np.array([226, 208, 160]), col)
    deep = np.clip(-H / 12.0, 0, 1)[..., None]
    col = np.where((H <= 0)[..., None], np.array([90, 190, 205]) * (1 - deep) + np.array([30, 90, 150]) * deep, col)
    col = col * np.where(H <= 0, 1.0, sh)[..., None]
    return Image.fromarray(np.clip(col, 0, 255).astype('uint8'))

def tile(B, cx, cz, half, ppm, path, label, hf=None, extras=None):
    S = int(2 * half * ppm); im = terrain_bg(hf, cx, cz, half, ppm) if hf is not None else Image.new('RGB', (S, S), (104, 138, 88)); d = ImageDraw.Draw(im)
    def P(p): return ((p[0] - cx + half) * ppm, (p[1] - cz + half) * ppm)
    for lay in prev_ground.ORDER:
        c = prev_ground.CO[lay]
        for (x0, z0, x1, z1, pts) in B.get(lay, ()):
            if x1 < cx - half or x0 > cx + half or z1 < cz - half or z0 > cz + half: continue
            d.polygon([P(p) for p in pts], fill=c)
    if extras:
        def P(x, z): return ((x - cx + half) * ppm, (z - cz + half) * ppm)
        for poly in extras.get('bumps', []):
            if any(abs(p[0] - cx) < half and abs(p[1] - cz) < half for p in poly):
                q = [P(*p) for p in poly]; d.polygon(q, fill=(242, 196, 0)); d.line(q + [q[0]], fill=(30, 30, 32), width=2)
        for s in extras.get('signs', []):
            if abs(s['x'] - cx) > half or abs(s['z'] - cz) > half: continue
            px, pz = P(s['x'], s['z']); r = 4.0
            if s['type'] == 'stop': d.regular_polygon((px, pz, r + 1), 8, fill=(211, 47, 47), outline=(255, 255, 255))
            elif s['type'] == 'yield': d.polygon([(px - r - 1, pz - r), (px + r + 1, pz - r), (px, pz + r + 1)], fill=(255, 255, 255), outline=(211, 47, 47))
            elif s['type'] == 'velocidade': d.ellipse([px - r, pz - r, px + r, pz + r], fill=(255, 255, 255), outline=(211, 47, 47), width=2)
            elif s['type'] in ('pedestre', 'lombada', 'rotatoria'): d.polygon([(px, pz - r - 1), (px + r + 1, pz), (px, pz + r + 1), (px - r - 1, pz)], fill=(245, 197, 24), outline=(20, 20, 20))
            else: d.rectangle([px - r, pz - 3, px + r, pz + 3], fill=(211, 47, 47), outline=(255, 255, 255))
        for h in extras.get('heads', []):
            if abs(h['x'] - cx) > half or abs(h['z'] - cz) > half or h['lane'] != -1: continue
            px, pz = P(h['x'], h['z']); d.rectangle([px - 5, pz - 5, px + 5, pz + 5], fill=(20, 20, 22), outline=(255, 255, 255)); d.ellipse([px - 3, pz - 3, px + 3, pz + 3], fill=(255, 59, 48))
    if extras and extras.get('orla'):
        def P2(x, z): return ((x - cx + half) * ppm, (z - cz + half) * ppm)
        O = extras['orla']
        for pm in O.get('umbrellas', []):
            if abs(pm['x'] - cx) < half and abs(pm['z'] - cz) < half:
                px, pz = P2(pm['x'], pm['z']); d.ellipse([px - 3, pz - 3, px + 3, pz + 3], fill=(229, 57, 53), outline=(255, 255, 255))
        for k_, col_, r_ in (('palms', (30, 120, 40), 4), ('lamps', (255, 235, 130), 2), ('benches', (122, 90, 58), 3), ('showers', (150, 200, 255), 3)):
            for pm in O.get(k_, []):
                if abs(pm['x'] - cx) < half and abs(pm['z'] - cz) < half:
                    px, pz = P2(pm['x'], pm['z']); d.ellipse([px - r_, pz - r_, px + r_, pz + r_], fill=col_, outline=(0, 0, 0))
        for pm in O.get('kiosks', []):
            if abs(pm['x'] - cx) < half and abs(pm['z'] - cz) < half:
                px, pz = P2(pm['x'], pm['z']); d.rectangle([px - 8, pz - 8, px + 8, pz + 8], fill=(181, 138, 74), outline=(60, 40, 20), width=2)
        for pm in O.get('towers', []):
            if abs(pm['x'] - cx) < half and abs(pm['z'] - cz) < half:
                px, pz = P2(pm['x'], pm['z']); d.rectangle([px - 6, pz - 6, px + 6, pz + 6], fill=(214, 64, 42), outline=(255, 255, 255), width=2)
        for pm in O.get('courts', []):
            if abs(pm['x'] - cx) < half and abs(pm['z'] - cz) < half:
                px, pz = P2(pm['x'], pm['z']); d.line([(px - pm['tx'] * 22, pz - pm['tz'] * 22), (px + pm['tx'] * 22, pz + pm['tz'] * 22)], fill=(255, 255, 255), width=3)
    d.rectangle([0, 0, S - 1, 22], fill=(20, 20, 24)); d.text((8, 5), label, fill=(255, 255, 255))
    # escala 50 m
    d.line([(S - 20 - 50 * ppm, S - 16), (S - 20, S - 16)], fill=(255, 255, 255), width=3); d.text((S - 20 - 50 * ppm, S - 32), '50 m', fill=(255, 255, 255))
    im.save(path)

def make_all(g, c, outdir, half=200, ppm=3.0, hf=None, extras=None):
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
            tile(B, cx, cz, half, ppm, path, f'FOTO {idx:02d}   centro x={cx:.0f} z={cz:.0f}   ({2*half:.0f} x {2*half:.0f} m)', hf, extras)
            made.append((idx, cx, cz, i, j, path))
    # legenda
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


def paths_view(g, tr, cx, cz, half, ppm, path, title, fu=None):
    """vista de cima com as trajetorias dos carros (mao direita): verde=reto, azul=direita, laranja=esquerda, roxo=retorno, ciano=rotatoria"""
    from PIL import Image, ImageDraw
    B = bucket(g); S = int(2 * half * ppm); im = Image.new('RGB', (S, S), (104, 138, 88)); d = ImageDraw.Draw(im)
    def P(p): return ((p[0] - cx + half) * ppm, (p[1] - cz + half) * ppm)
    for lay in prev_ground.ORDER:
        for (x0, z0, x1, z1, pts) in B.get(lay, ()):
            if x1 < cx - half or x0 > cx + half or z1 < cz - half or z0 > cz + half: continue
            d.polygon([P(p) for p in pts], fill=prev_ground.CO[lay])
    col = {'straight': (80, 220, 80), 'right': (70, 140, 255), 'left': (255, 150, 30), 'uturn': (200, 90, 255), 'roundabout': (40, 230, 230)}
    for m in tr.moves:
        P0 = m['path']
        if not any(abs(p[0] - cx) < half and abs(p[1] - cz) < half for p in P0): continue
        pts = [P(p) for p in P0]; d.line(pts, fill=col[m['kind']], width=2)
        # seta no fim
        a, b = pts[-2], pts[-1]; ang = math.atan2(b[1] - a[1], b[0] - a[0])
        d.polygon([b, (b[0] - 7 * math.cos(ang - 0.4), b[1] - 7 * math.sin(ang - 0.4)), (b[0] - 7 * math.cos(ang + 0.4), b[1] - 7 * math.sin(ang + 0.4))], fill=col[m['kind']])
    if fu is not None:
        for s in fu.signs:
            if abs(s['x'] - cx) < half and abs(s['z'] - cz) < half:
                px, pz = P((s['x'], s['z'])); r = 5
                if s['type'] == 'stop': d.regular_polygon((px, pz, r + 2), 8, fill=(211, 47, 47), outline=(255, 255, 255))
                elif s['type'] == 'yield': d.polygon([(px - 7, pz - 6), (px + 7, pz - 6), (px, pz + 7)], fill=(255, 255, 255), outline=(211, 47, 47))
                elif s['type'] == 'velocidade': d.ellipse([px - r, pz - r, px + r, pz + r], fill=(255, 255, 255), outline=(211, 47, 47), width=2)
                else: d.polygon([(px, pz - 7), (px + 7, pz), (px, pz + 7), (px - 7, pz)], fill=(245, 197, 24), outline=(20, 20, 20))
        for h in fu.heads:
            if abs(h['x'] - cx) < half and abs(h['z'] - cz) < half and h['lane'] == -1:
                px, pz = P((h['x'], h['z'])); d.rectangle([px - 6, pz - 6, px + 6, pz + 6], fill=(20, 20, 22), outline=(255, 255, 255)); d.ellipse([px - 3, pz - 3, px + 3, pz + 3], fill=(255, 59, 48))
        for b in tr.bumps:
            if abs(b['x'] - cx) < half and abs(b['z'] - cz) < half:
                q = [P(p) for p in b['poly']]; d.polygon(q, fill=(242, 196, 0)); d.line(q + [q[0]], fill=(20, 20, 20), width=2)
    d.rectangle([0, 0, S - 1, 24], fill=(20, 20, 24)); d.text((8, 6), title, fill=(255, 255, 255))
    d.text((8, S - 18), 'verde=reto  azul=direita  laranja=esquerda  roxo=retorno  ciano=rotatoria  | vermelho=PARE  ◄ semaforo = quadrado preto', fill=(255, 255, 255))
    im.save(path)
