import math
import numpy as np
from PIL import Image, ImageDraw
from plan import *

def terrain_img(G, scale=0.3):
    h = G.h; gz, gx = np.gradient(h, CELL)
    k = 2.6
    nx_, nz_ = -gx * k, -gz * k; nn = np.sqrt(nx_ ** 2 + 1 + nz_ ** 2)
    L = np.array([-0.55, 0.70, -0.45]); L = L / np.linalg.norm(L)
    sh = np.clip(0.42 + 0.75 * ((nx_ * L[0] + 1 * L[1] + nz_ * L[2]) / nn), 0.25, 1.25)
    img = np.zeros(h.shape + (3,), float)
    def lerp(c0, c1, t): return np.array(c0)[None, None, :] * (1 - t[..., None]) + np.array(c1)[None, None, :] * t[..., None]
    land = np.clip(h / 260.0, 0, 1)
    col = lerp((104, 150, 84), (86, 112, 70), np.clip(h / 80, 0, 1))
    col = np.where((h > 80)[..., None], lerp((86, 112, 70), (128, 120, 108), np.clip((h - 80) / 160, 0, 1)), col)
    col = np.where((h > 210)[..., None], lerp((128, 120, 108), (235, 238, 240), np.clip((h - 210) / 60, 0, 1)), col)
    sand = (h < 2.2) & (h > 0.0)
    col = np.where(sand[..., None], np.array([226, 208, 160])[None, None, :], col)
    deep = np.clip(-h / 22.0, 0, 1)
    wcol = lerp((90, 190, 205), (18, 70, 130), deep)
    col = np.where((h <= 0)[..., None], wcol, col)
    col = col * np.where(h <= 0, 1.0, sh)[..., None]
    col = np.clip(col, 0, 255).astype(np.uint8)
    col = np.clip(col, 0, 255)
    # curvas de nivel a cada 25 m
    lv = np.floor(h / 25.0)
    edge = (lv != np.roll(lv, 1, 0)) | (lv != np.roll(lv, 1, 1))
    col = np.where((edge & (h > 2))[..., None], col * 0.82, col).astype(np.uint8)
    im = Image.fromarray(col).resize((int(WX * scale), int(WZ * scale)), Image.BILINEAR)
    return im

def draw_roads(im, edges, nodes, scale=0.3, rounds=()):
    d = ImageDraw.Draw(im)
    cols = {'ave': (250, 235, 150), 'col': (240, 240, 240), 'loc': (214, 214, 214), 'hwy': (255, 120, 60)}
    wid = {'ave': 3, 'col': 2, 'loc': 1, 'hwy': 4}
    for e in sorted(edges, key=lambda e: {'loc': 0, 'col': 1, 'ave': 2, 'hwy': 3}.get(e['cls'], 0)):
        pts = [(p[0] * scale, p[1] * scale) for p in e['p']]
        c = cols[e['cls']]
        if e['kind'] == 'redbridge': c = (225, 30, 30)
        if e['kind'] == 'bridge': c = (255, 255, 255)
        w = wid[e['cls']] + (2 if e['kind'] == 'redbridge' else 0)
        d.line(pts, fill=c, width=w, joint='curve')
    for n in nodes:
        if n['kind'] in ('cul',): d.ellipse([n['x'] * scale - 2, n['z'] * scale - 2, n['x'] * scale + 2, n['z'] * scale + 2], fill=(255, 215, 0))
    for r in rounds:
        d.ellipse([r['x'] * scale - 5, r['z'] * scale - 5, r['x'] * scale + 5, r['z'] * scale + 5], outline=(255, 255, 255), fill=(80, 150, 70))
    return im
