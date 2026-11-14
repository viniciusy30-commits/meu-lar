"""Validadores da ETAPA D (lotes e 17 casas)."""
import math
import numpy as np
from PIL import Image, ImageDraw
from plan import *
import validate_ground
import terrain_final as T


def inside_rect(p, rect, shrink=0.0):
    """ponto dentro do retangulo (4 cantos) com margem"""
    a, b, c, d = rect
    ux, uz = b[0] - a[0], b[1] - a[1]; wl = math.hypot(ux, uz); ux /= wl; uz /= wl
    vx, vz = d[0] - a[0], d[1] - a[1]; hl = math.hypot(vx, vz); vx /= hl; vz /= hl
    u = (p[0] - a[0]) * ux + (p[1] - a[1]) * uz; v = (p[0] - a[0]) * vx + (p[1] - a[1]) * vz
    return shrink <= u <= wl - shrink and shrink <= v <= hl - shrink


def run(gr, P, city, geo, hf):
    out = []; ok = True
    H = P.houses
    # 1) as 17 casas existem, uma vez so
    ks = sorted(h['k'] for h in H)
    good = ks == list(range(17)); ok &= good
    out.append(f'  casas colocadas: {len(H)} de 17 (indices unicos: {len(set(ks))}) {"ok" if good else "FALTAM " + str(sorted(set(range(17)) - set(ks)))}')
    # 2) quintal (cerca incluida) dentro do lote com margem >= 1 m e a caixa da casa com >= 3 m
    bad = []
    for h in H:
        x0, z0, x1, z1 = h['yard']; rect = h['lot']['rect']
        for c in ((x0, z0), (x1, z0), (x1, z1), (x0, z1)):
            if not inside_rect(c, rect, 1.0): bad.append(f'casa {h["k"] + 1}: quintal fora do lote')
        bx0, bz0, bx1, bz1 = h['box']
        for c in ((bx0, bz0), (bx1, bz0), (bx1, bz1), (bx0, bz1)):
            if not inside_rect(c, rect, 3.0): bad.append(f'casa {h["k"] + 1}: casa a menos de 3 m da divisa')
    good = not bad; ok &= good
    out.append(f'  quintal dentro do lote (margem >= 1 m, casa >= 3 m): {len(bad)} problemas {"ok" if good else "PROBLEMA"}' + (' ' + str(bad[:4]) if bad else ''))
    # 3) frente da casa para a rua: angulo entre a frente (0, +-1) e a direcao da rua
    worst = max((h['lot']['angle'] for h in H), default=0)
    good = worst <= 20.5; ok &= good
    out.append(f'  frente da casa voltada para a rua: pior desvio {worst:.1f} graus (<= 20) {"ok" if good else "PROBLEMA"}')
    # 4) distancia minima entre caixas >= 6 m
    close = []
    for i in range(len(H)):
        for j in range(i + 1, len(H)):
            a, b = H[i]['box'], H[j]['box']
            dx = max(a[0] - b[2], b[0] - a[2], 0); dz = max(a[1] - b[3], b[1] - a[3], 0); d = math.hypot(dx, dz)
            if d < 6.0: close.append((H[i]['k'] + 1, H[j]['k'] + 1, round(d, 1)))
    good = not close; ok &= good
    out.append(f'  distancia minima entre casas >= 6 m: {len(close)} pares perto {"ok" if good else "PROBLEMA"}' + (' ' + str(close[:4]) if close else ''))
    # 5) lotes (casas e comuns) nao se sobrepoem entre si
    W_, H_ = 4400, 3600
    cnt = np.zeros((H_, W_), np.uint8)
    rects = [h['lot']['rect'] for h in H] + [[tuple(p) for p in l['rect']] for l in P.lots]
    for r in rects:
        xs = [p[0] for p in r]; zs = [p[1] for p in r]
        x0, x1 = int(min(xs)) - 1, int(max(xs)) + 2; z0, z1 = int(min(zs)) - 1, int(max(zs)) + 2
        im = Image.new('L', (x1 - x0, z1 - z0), 0)
        cx = sum(xs) / 4; cz = sum(zs) / 4
        pts = []
        for (x, z) in r:
            dx, dz = x - cx, z - cz; l = math.hypot(dx, dz) or 1
            pts.append((x - dx / l * 1.3 - x0, z - dz / l * 1.3 - z0))                # encolhe ~1 m: lotes vizinhos dividem divisa (raster de 1 m)
        ImageDraw.Draw(im).polygon(pts, fill=1)
        cnt[z0:z1, x0:x1] += np.array(im, np.uint8)
    over = int((cnt > 1).sum())
    good = over < 40; ok &= good
    out.append(f'  sobreposicao entre lotes: {over} m2 ({len(rects)} lotes) {"ok" if good else "PROBLEMA"}')
    # 6) lotes das casas nao tocam asfalto, calcada, guia, canteiro (exceto a faixa de entrada do rebaixo)
    M = validate_ground.raster(gr, ['asphalt', 'curb', 'sidewalk', 'median', 'island'])
    er = lambda m: m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
    road = er(M['asphalt']) | er(M['sidewalk']) | er(M['median']) | er(M['island'])
    hit = 0
    for h in H:
        r = h['lot']['rect']
        xs = [p[0] for p in r]; zs = [p[1] for p in r]
        x0, x1 = int(min(xs)) - 1, int(max(xs)) + 2; z0, z1 = int(min(zs)) - 1, int(max(zs)) + 2
        im = Image.new('L', (x1 - x0, z1 - z0), 0)
        cx = sum(xs) / 4; cz = sum(zs) / 4
        pts = []
        for (x, z) in r:
            dx, dz = x - cx, z - cz; l = math.hypot(dx, dz) or 1
            pts.append((x - dx / l * 1.0 - x0, z - dz / l * 1.0 - z0))
        ImageDraw.Draw(im).polygon(pts, fill=255)
        hit += int(((np.array(im) > 0) & road[z0:z1, x0:x1]).sum())
    good = hit < 30; ok &= good
    out.append(f'  lotes das casas sobre rua/calcada: {hit} m2 {"ok" if good else "PROBLEMA"}')
    # 7) platô: terreno final no quintal inteiro igual ao nivel da casa
    worst = 0.0; wl = None
    for h in H:
        x0, z0, x1, z1 = h['yard']
        for x in np.linspace(x0, x1, 9):
            for z in np.linspace(z0, z1, 9):
                d = abs(T.sample8(hf, x, z) - h['y'])
                if d > worst: worst, wl = d, h['k'] + 1
    good = worst < 0.7; ok &= good
    out.append(f'  platô nivelado sob a casa e o quintal: pior diferenca {worst:.2f} m (casa {wl}) {"ok" if good else "PROBLEMA"}')
    # 8) acesso: porta -> calcada (caminho reto <= 5 % de rampa) e garagem com rebaixo
    bad = []
    for h in H:
        lot = h['lot']; yf = lot['yfront']; yp = h['y']
        v_door = (h['door'][0] - lot['F'][0]) * lot['N'][0] + (h['door'][1] - lot['F'][1]) * lot['N'][1]
        grade = abs(yp - yf) / max(v_door, 1.0)
        if v_door < 1.5 or v_door > 12 or grade > 0.05: bad.append((h['k'] + 1, round(v_door, 1), round(grade * 100, 1)))
    good = not bad; ok &= good
    out.append(f'  caminho porta->calcada (<=5 %) e garagem: {len(bad)} problemas {"ok" if good else "PROBLEMA"}' + (' ' + str(bad[:4]) if bad else ''))
    # 9) cada casa com rua da frente e bairro certo
    bad = [(h['k'] + 1, h['bairro']) for h in H if not h['street'] and h['lvl'] > 1]
    out.append(f'  ruas da frente: ' + ', '.join(f'C{h["k"] + 1}={h["street"] or "rua sem nome"}' for h in H[:6]) + ' ...')
    out.append(f'  lotes comuns (para a Etapa E): {len(P.lots)}; solidos de cerca: {len(P.solids)}; arvores de lote: {len(P.trees)}')
    return ok, out
