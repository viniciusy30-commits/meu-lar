"""Validadores da ETAPA C (chao): buracos, sobreposicao entre camadas, faixas fora do asfalto, orcamento."""
import math, os
import numpy as np
from PIL import Image, ImageDraw
from plan import *

def raster(g, names, scale=1.0):
    W, H = int(WX * scale), int(WZ * scale)
    masks = {}
    for nm in names:
        im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
        for name, pts in g.layers:
            if name == nm: d.polygon([(p[0] * scale, p[1] * scale) for p in pts], fill=255)
        masks[nm] = np.array(im) > 0
    return masks

def v_ground(g):
    c = g.c; out = []; ok = True
    M = raster(g, ['asphalt', 'curb', 'sidewalk', 'verge', 'median', 'mark'])
    # 1) sobreposicao entre camadas
    def erode(m): return m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
    E = {k: erode(v) for k, v in M.items()}
    for a, b in (('asphalt', 'sidewalk'), ('asphalt', 'verge'), ('sidewalk', 'verge'), ('sidewalk', 'median'), ('asphalt', 'median')):
        ov = int((E[a] & E[b]).sum()); base = max(1, int(min(E[a].sum(), E[b].sum())))
        pct = 100.0 * ov / base
        good = pct < 1.2
        out.append(f'  sobreposicao {a} x {b}: {ov} m2 ({pct:.2f}%) {"ok" if good else "ALTA"}'); ok &= good
    # 2) buracos: centro de cada rua precisa estar sobre asfalto (ou canteiro central)
    miss = 0; tot = 0; samples = []
    for k, e in enumerate(c.edges):
        if e['kind'] == 'redbridge': continue
        L = g.elen(k)
        for s in np.arange(2.0, L - 1.0, 3.0):
            x, z, y, _, _ = g.at(k, s); tot += 1
            i, j = int(x), int(z)
            if not (0 <= i < M['asphalt'].shape[1] and 0 <= j < M['asphalt'].shape[0]): continue
            if not (M['asphalt'][j, i] or M['median'][j, i] or M['asphalt'][min(j + 1, M['asphalt'].shape[0] - 1), i] or M['asphalt'][j, min(i + 1, M['asphalt'].shape[1] - 1)]):
                miss += 1
                if len(samples) < 12: samples.append((round(x), round(z), e['name'] or 'rua'))
    pct = 100.0 * miss / max(tot, 1); good = pct < 0.8
    out.append(f'  buracos no eixo das ruas: {miss}/{tot} amostras ({pct:.2f}%) {"ok" if good else "ALTO"}' + (f' ex.: {samples[:6]}' if samples else '')); ok &= good
    # 3) faixas pintadas fora do asfalto (permitido: rampa tatil sobre calcada)
    mk = M['mark']; bad = int((mk & ~M['asphalt'] & ~M['sidewalk'] & ~M['median']).sum())
    pct = 100.0 * bad / max(1, int(mk.sum())); good = pct < 4.0
    out.append(f'  pintura fora de asfalto/calcada: {bad} m2 ({pct:.2f}%) {"ok" if good else "ALTO"}'); ok &= good
    # 4) calcada dos dois lados
    nos = 0; tot2 = 0
    for k, e in enumerate(c.edges):
        if e['kind'] == 'redbridge': continue
        sec = {0: 14.0, 1: 10.0, 2: 7.5}[min(e['lvl'], 2)]; asp = {0: 11.5, 1: 6.0, 2: 5.0}[min(e['lvl'], 2)]
        L = g.elen(k)
        ca = max([a['cut'] for a in g.arms[e['a']] if a['k'] == k and a['end'] == 'a'] or [0]); cb = max([a['cut'] for a in g.arms[e['b']] if a['k'] == k and a['end'] == 'b'] or [0])
        for s in np.arange(8.0, L - 8.0, 9.0):
            if s < ca + 2 or s > L - cb - 2: continue                    # dentro do cruzamento nao ha calcada ao lado da pista
            x, z, y, tx, tz = g.at(k, s)
            for sg in (1, -1):
                px, pz = x + (-tz) * sg * (asp + 1.6), z + tx * sg * (asp + 1.6); tot2 += 1
                i, j = int(px), int(pz)
                if 0 <= i < M['sidewalk'].shape[1] and 0 <= j < M['sidewalk'].shape[0] and not (M['sidewalk'][j, i] or M['verge'][j, i] or M['curb'][j, i]): nos += 1
    pct = 100.0 * nos / max(tot2, 1); good = pct < 2.0
    out.append(f'  trechos sem calcada/canteiro ao lado da pista: {nos}/{tot2} ({pct:.2f}%) {"ok" if good else "ALTO"}'); ok &= good
    # 5) orcamento
    ntri = g.B.ntri; mb = ntri * 3 * (8 * 4 + 3) / 1e6
    good = ntri < 420000 and mb < 55
    out.append(f'  triangulos: {ntri} (~{mb:.0f} MB sem compressao) {"ok" if good else "ACIMA DO ORCAMENTO"}'); ok &= good
    out.append(f'  protecoes: {g.stats["guard_m"]:.0f} m de guard-rail, {g.stats["wall_m"]:.0f} m de muro de arrimo, {g.stats["short_edges"]} trechos curtos sem corpo, {g.stats["junctions"]} cruzamentos/pontas')
    return ok, out
