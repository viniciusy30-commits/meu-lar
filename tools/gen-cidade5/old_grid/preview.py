import math
from PIL import Image, ImageDraw
from plan import *

SC = 0.5
def P(x, z): return (x * SC, z * SC)

def draw(g, path, label=True):
    im = Image.new('RGB', (int(WX * SC), int(WZ * SC)), (86, 128, 80))       # mata/terreno fora da cidade
    d = ImageDraw.Draw(im)
    # mar (abaixo da costa) e rio
    d.polygon([P(0, 1850), P(300, 1925), P(900, 1935), P(1700, 1925), P(2200, 1890), P(2330, 1900), P(2700, 1890), P(2700, 2100), P(0, 2100)], fill=(30, 100, 150))
    d.polygon([P(*q) for q in MARINA_INLET], fill=(30, 100, 150))
    d.polygon([P(*p) for p in CITY_MASK], fill=(150, 178, 120))
    d.polygon([P(*p) for p in PENINSULA_MASK], fill=(150, 178, 120))
    # mar dentro do retangulo mas fora da mascara no sul/baia
    water = [(0, 1500), (60, 1700), (96, 1790), (124, 1722)]  # nada: a mascara ja define terra
    rv = RIVER
    d.line([P(*p) for p in rv], fill=(40, 120, 170), width=int(RIVER_W * SC))
    d.ellipse([P(2395 - 35, 1880 - 35), P(2395 + 35, 1880 + 35)], fill=(40, 120, 170))
    # superquadras (tipo) - contornos leves
    cols = {'RES': (170, 195, 140), 'CEN': (190, 190, 195), 'ESP': (160, 200, 150), 'CND': (175, 185, 160)}
    for (i, j), t in SQ_TYPE.items():
        x0, z0, x1, z1 = sq_rect(i, j)
        d.rectangle([P(x0, z0), P(x1, z1)], outline=(120, 140, 105))
        if label: d.text(P(x0 + 6, z0 + 4), SQ_NAME[(i, j)], fill=(60, 60, 60))
    # vias
    order = {'n': 0, 'ramp': 1, 'elev': 2, 'bridge': 2}
    for e in sorted(g.edges, key=lambda e: order.get(e['kind'], 0)):
        col = {'ave': (60, 60, 70), 'col': (80, 80, 88), 'loc': (110, 110, 118), 'hwy': (200, 90, 40)}[e['cls']]
        if e['kind'] == 'elev': col = (230, 120, 50)
        if e['kind'] == 'bridge': col = (240, 240, 250)
        if e['kind'] == 'ramp': col = (220, 150, 60)
        w = max(1, int(e['w'] * SC))
        d.line([P(*p) for p in e['pts']], fill=col, width=w, joint='curve')
    for nm, (x, z, r) in ROUNDS.items():
        d.ellipse([P(x - r, z - r), P(x + r, z + r)], fill=(60, 60, 70), outline=(255, 255, 255))
        d.ellipse([P(x - r + 16, z - r + 16), P(x + r - 16, z + r - 16)], fill=(90, 150, 80))
    for k, n in g.nodes.items():
        if n['kind'] == 'cul': d.ellipse([P(k[0] - 6, k[1] - 6), P(k[0] + 6, k[1] + 6)], fill=(255, 220, 0))
    for nm, (x, z) in (('A', (0, 0)),):
        pass
    d.text((8, 6), 'MEULAR CITY - ETAPA A (esqueleto viario) - preview 1px = 2 m', fill=(255, 255, 255))
    im.save(path)
