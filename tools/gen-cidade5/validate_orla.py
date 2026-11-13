"""Validadores da ORLA (praias)."""
import math
import numpy as np
from plan import *
import validate_ground, shore

def run(g, o, geo, hf):
    import terrain_final as T
    out = []; ok = True
    M = validate_ground.raster(g, ['asphalt', 'sidewalk', 'verge', 'prom', 'prom2', 'bike', 'stairs', 'pier', 'wall'])
    er = lambda m: m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
    H, W = M['asphalt'].shape
    ds = geo.Dsea; bz = geo.beach_zone
    # 1) nenhum asfalto/calcada de rua entre a avenida e o mar (rua nao desce para a praia)
    ys, xs = np.nonzero(er(M['asphalt']))
    bad = 0
    for x, y in zip(xs, ys):
        j, i = geo.idx(x, y)
        if bz[j, i] and ds[j, i] < 30: bad += 1
    good = bad < 12; ok &= good
    out.append(f'  asfalto entre a Av. Beira-Mar e o mar: {bad} m2 (rua nao desce para a areia) {"ok" if good else "PROBLEMA"}')
    # 2) calcadao nao encosta/cobre asfalto, calcada, canteiro
    prom = M['prom'] | M['prom2'] | M['bike']
    ov_a = int((er(prom) & er(M['asphalt'])).sum()); ov_s = int((er(prom) & er(M['sidewalk'])).sum())
    good = ov_a == 0 and ov_s < 25; ok &= good
    out.append(f'  calcadao sobre asfalto: {ov_a} m2; sobre calcada de rua: {ov_s} m2 {"ok" if good else "PROBLEMA"}')
    # 3) escadas a cada <= 130 m em cada trecho de orla (distancia ao longo do calcadao)
    worst = 0.0
    for fr in o.frames_all:
        L = fr[-1]['s']
        ss = []
        for s in o.items['stairs']:
            k = min(range(0, len(fr)), key=lambda q: (fr[q]['x'] - s['x']) ** 2 + (fr[q]['z'] - s['z']) ** 2)
            if math.hypot(fr[k]['x'] - s['x'], fr[k]['z'] - s['z']) < 9.0: ss.append(fr[k]['s'])
        ss.sort()
        gaps = [ss[0]] + [b_ - a_ for a_, b_ in zip(ss, ss[1:])] + [L - ss[-1]] if ss else [L]
        worst = max(worst, max(gaps))
    good = worst < 140; ok &= good
    out.append(f'  escadas da orla para a areia: {len(o.items["stairs"])} (maior distancia sem escada ~{worst:.0f} m) {"ok" if good else "PROBLEMA"}')
    # 4) pieres sobre a agua
    pr_ok = 0
    for p in o.items['piers']:
        wet = 0; tot = 0
        for a in np.arange(5, p['len'], 4.0):
            h = T.sample8(hf, p['x'] + p['dx'] * a, p['z'] + p['dz'] * a); tot += 1; wet += (h < 0.2)
        if wet / max(tot, 1) > 0.5: pr_ok += 1
    good = len(o.items['piers']) >= 2 and pr_ok == len(o.items['piers']); ok &= good
    out.append(f'  pieres: {len(o.items["piers"])} (com >50% sobre a agua: {pr_ok}); comprimento {[p["len"] for p in o.items["piers"]]} m {"ok" if good else "PROBLEMA"}')
    # 5) objetos da areia nao estao na agua e nao em cima da escada/pier
    wet = 0
    for k in ('kiosks', 'towers', 'courts', 'showers'):
        for it in o.items[k]:
            if T.sample8(hf, it['x'], it['z']) < 0.25: wet += 1
    good = wet == 0; ok &= good
    out.append(f'  quiosques/salva-vidas/chuveiros/quadras: {len(o.items["kiosks"])}/{len(o.items["towers"])}/{len(o.items["showers"])}/{len(o.items["courts"])}; dentro d\'agua: {wet} {"ok" if good else "PROBLEMA"}')
    # 6) palmeiras/postes livres de escadas, acessos e piers
    clash = 0
    keep = [(s['x'], s['z']) for s in o.items['stairs']] + [(p['x'], p['z']) for p in o.items['piers']]
    for it in o.items['palms'] + o.items['lamps']:
        if it.get('pier'): continue
        for (px, pz) in keep:
            if math.hypot(it['x'] - px, it['z'] - pz) < 4.0: clash += 1; break
    for it in o.items['palms']:
        for q in o.items['paths']:
            if math.hypot(it['x'] - q['x'] - q['sx'] * 17, it['z'] - q['z'] - q['sz'] * 17) < 3.0: clash += 1; break
    good = clash == 0; ok &= good
    out.append(f'  palmeiras/postes bloqueando escada ou acesso: {clash} {"ok" if good else "PROBLEMA"}')
    out.append(f'  orla: {o.stats["prom_m"]:.0f} m de calcadao, {o.stats["wall_m"]:.0f} m de muro, {len(o.items["palms"])} palmeiras, {len(o.items["lamps"])} postes, {len(o.items["benches"])} bancos, {len(o.items["umbrellas"])} guarda-sois, {len(o.items["paths"])} acessos pela travessia da avenida')
    return ok, out
