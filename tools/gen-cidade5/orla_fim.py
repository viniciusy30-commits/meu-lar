"""Praca do Farol: acabamento das pontas da orla (plaza grande com rosa dos ventos, canteiros floridos, ciclovia que entra e faz o retorno em anel, bandeiras)"""
import math
from bake import rgb, shade, PLAIN, STONE, WOOD, METAL, PAVER, ROOF
from plan import *

FLOWERS = [rgb('#E53935'), rgb('#FDD835'), rgb('#EC407A'), rgb('#F5F5F5'), rgb('#AB47BC'), rgb('#FB8C00')]


def angdiff(a, b): return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def extras(o, f, so, cx, cz, Rr, Y, ang_in, ang_sea, red0, red1):
    import orla as O
    B = o.B; g = o.g; COL = O.COL
    YP = Y + 0.06
    # 1) a ciclovia ENTRA na praca: o trecho vermelho (3..7 m) segue reto ate o anel e se funde com ele
    rmid = (red0 + red1) / 2
    off_c = math.hypot(cx - f['x'], cz - f['z'])
    ext = (off_c - math.sqrt(max(rmid * rmid - 25.0, 1.0)) + 0.9) * so
    q = [o.P(f, 3.0, 0.065, 0.0), o.P(f, 7.0, 0.065, 0.0), o.P(f, 7.0, 0.065, ext), o.P(f, 3.0, 0.065, ext)]
    g.quad(PAVER, q, COL['bike'], 'bike')
    for oo in (3.0, 7.0):                                    # filetes brancos continuam ate o anel
        a = o.P(f, oo - 0.07, 0.08, 0.0); b = o.P(f, oo - 0.07, 0.08, ext); c = o.P(f, oo + 0.07, 0.08, ext); d = o.P(f, oo + 0.07, 0.08, 0.0)
        B.quad(PLAIN, [a, b, c, d], (0, 1, 0), COL['white'], None, True)
    # tracejado central do anel (mao dupla) e setas de sentido (anti-horario)
    rm = (red0 + red1) / 2
    n = 40
    for k in range(n):
        if k % 2: continue
        a0 = 2 * math.pi * k / n; a1 = 2 * math.pi * (k + 0.55) / n
        if angdiff((a0 + a1) / 2, ang_in) < math.radians(24): continue
        B.quad(PLAIN, [(cx + math.cos(a0) * (rm - 0.06), YP + 0.02, cz + math.sin(a0) * (rm - 0.06)), (cx + math.cos(a1) * (rm - 0.06), YP + 0.02, cz + math.sin(a1) * (rm - 0.06)),
                       (cx + math.cos(a1) * (rm + 0.06), YP + 0.02, cz + math.sin(a1) * (rm + 0.06)), (cx + math.cos(a0) * (rm + 0.06), YP + 0.02, cz + math.sin(a0) * (rm + 0.06))], (0, 1, 0), COL['white'], None, True)
    for rr_, sgn in ((rm - 0.9, 1.0), (rm + 0.9, -1.0)):     # uma seta em cada faixa do anel, cada uma no seu sentido
        a_ = ang_in + math.pi * 0.62 * sgn
        tx, tz = -math.sin(a_) * sgn, math.cos(a_) * sgn; px, pz = cx + math.cos(a_) * rr_, cz + math.sin(a_) * rr_
        nx_, nz_ = -tz, tx
        B.quad(PLAIN, [(px - tx * 1.2 - nx_ * 0.07, YP + 0.02, pz - tz * 1.2 - nz_ * 0.07), (px + tx * 0.2 - nx_ * 0.07, YP + 0.02, pz + tz * 0.2 - nz_ * 0.07), (px + tx * 0.2 + nx_ * 0.07, YP + 0.02, pz + tz * 0.2 + nz_ * 0.07), (px - tx * 1.2 + nx_ * 0.07, YP + 0.02, pz - tz * 1.2 + nz_ * 0.07)], (0, 1, 0), COL['white'], None, True)
        B.tri(PLAIN, (px + tx * 0.2 - nx_ * 0.4, YP + 0.02, pz + tz * 0.2 - nz_ * 0.4), (px + tx * 1.4, YP + 0.02, pz + tz * 1.4), (px + tx * 0.2 + nx_ * 0.4, YP + 0.02, pz + tz * 0.2 + nz_ * 0.4), (0, 1, 0), COL['white'], None, True)
    # 2) rosa dos ventos no piso (8 pontas) + aneis de granito
    r_in, r_out = (3.1 if Rr < 14 else 3.4) + 0.9, red0 - 0.8
    for k in range(8):
        a = math.pi / 4 * k; hw = math.radians(9 if k % 2 == 0 else 6); ln = r_out if k % 2 == 0 else (r_out + r_in) / 2 + 0.6
        col = COL['wall2'] if k % 2 == 0 else COL['wave2']
        p0 = (cx + math.cos(a - hw) * r_in, YP + 0.012, cz + math.sin(a - hw) * r_in); p1 = (cx + math.cos(a) * ln, YP + 0.012, cz + math.sin(a) * ln); p2 = (cx + math.cos(a + hw) * r_in, YP + 0.012, cz + math.sin(a + hw) * r_in)
        B.tri(PLAIN, p0, p1, (cx + math.cos(a) * r_in, YP + 0.012, cz + math.sin(a) * r_in), (0, 1, 0), col, None, True)
        B.tri(PLAIN, (cx + math.cos(a) * r_in, YP + 0.012, cz + math.sin(a) * r_in), p1, p2, (0, 1, 0), shade(col, -22), None, True)
    for rr_, w in ((r_out + 0.45, 0.13), (r_in - 0.35, 0.13)):
        for k in range(48):
            a0 = 2 * math.pi * k / 48; a1 = 2 * math.pi * (k + 1) / 48
            B.quad(PLAIN, [(cx + math.cos(a0) * (rr_ - w), YP + 0.012, cz + math.sin(a0) * (rr_ - w)), (cx + math.cos(a1) * (rr_ - w), YP + 0.012, cz + math.sin(a1) * (rr_ - w)),
                           (cx + math.cos(a1) * (rr_ + w), YP + 0.012, cz + math.sin(a1) * (rr_ + w)), (cx + math.cos(a0) * (rr_ + w), YP + 0.012, cz + math.sin(a0) * (rr_ + w))], (0, 1, 0), COL['wall2'], None, True)
    # 3) canteiros floridos redondos entre a rosa e o anel da ciclovia
    rp = red0 - 0.75
    nplant = 14 if Rr >= 18 else 0
    for k in range(nplant):
        a = 2 * math.pi * (k + 0.5) / nplant
        if angdiff(a, ang_in) < math.radians(34) or angdiff(a, ang_sea) < math.radians(22): continue
        px, pz = cx + math.cos(a) * rp, cz + math.sin(a) * rp
        B.cyl(px, pz, 0.62, YP, YP + 0.42, COL['wall'], 10, STONE, False)
        col = FLOWERS[k % len(FLOWERS)]
        B.cyl(px, pz, 0.54, YP + 0.42, YP + 0.5, rgb('#4E7C35'), 10, PLAIN, True)
        for q in range(6):
            aa = 2 * math.pi * q / 6 + k
            B.cyl(px + math.cos(aa) * 0.26, pz + math.sin(aa) * 0.26, 0.17, YP + 0.5, YP + 0.62, col if q % 2 == 0 else shade(col, -30), 6, PLAIN, True)
    # 4) mastros com bandeiras (Brasil / cidade) perto da entrada do mar
    for sg in (-1, 1):
        a = ang_sea + sg * math.radians(42)
        px, pz = cx + math.cos(a) * (Rr - 1.4), cz + math.sin(a) * (Rr - 1.4)
        B.cyl(px, pz, 0.07, YP, YP + 9.0, COL['rail'], 8, METAL, True)
        wx, wz = -math.sin(a), math.cos(a)
        fc = rgb('#17A34A') if sg < 0 else rgb('#1E5BB8')
        B.quad(PLAIN, [(px, YP + 8.9, pz), (px + wx * 2.2, YP + 8.7, pz + wz * 2.2), (px + wx * 2.2, YP + 7.4, pz + wz * 2.2), (px, YP + 7.5, pz)], (math.cos(a), 0, math.sin(a)), fc, None, True)
        B.quad(PLAIN, [(px, YP + 8.9, pz), (px, YP + 7.5, pz), (px + wx * 2.2, YP + 7.4, pz + wz * 2.2), (px + wx * 2.2, YP + 8.7, pz + wz * 2.2)], (-math.cos(a), 0, -math.sin(a)), fc, None, True)
        B.quad(PLAIN, [(px + wx * 1.1, YP + 8.55, pz + wz * 1.1), (px + wx * 1.8, YP + 8.15, pz + wz * 1.8), (px + wx * 1.1, YP + 7.75, pz + wz * 1.1), (px + wx * 0.4, YP + 8.15, pz + wz * 0.4)], (math.cos(a), 0, math.sin(a)), rgb('#FFD600'), None, True)
        o.items['lamps'].append({'x': round(px, 2), 'z': round(pz, 2), 'y': round(YP, 2), 'flag': True})


# ----------------------------------------------------------------------------------------------- parque da ponta
def parks(o):
    """Parque do Farol: alameda de palmeiras do piso da praca ate o mirante da beira d'agua, canteiros floridos, ligacao ate a avenida, quiosque redondo, arvores"""
    import orla as O
    for p in o.items.get('plazas', []):
        if not (p['x'] < 1500 or p['x'] > 3000) or p['r'] < 13: continue
        _park(o, p, O)


def _park(o, p, O):
    B = o.B; g = o.g; COL = O.COL; rnd = o.rnd
    cx, cz, R, Y = p['x'], p['z'], p['r'], p['y']
    sea_x, sea_z = p['sx'], p['sz']; lx, lz = -sea_x, -sea_z                       # l: lado da terra (avenida)
    P = g.c.lotplan
    import validate_ground
    if not hasattr(o, '_street_occ'):
        M = validate_ground.raster(g, ['asphalt', 'sidewalk', 'curb', 'median', 'island']); o._street_occ = M['asphalt'] | M['sidewalk'] | M['curb'] | M['median'] | M['island']
    from PIL import Image, ImageDraw, ImageFilter
    import numpy as _np
    if not hasattr(o, '_park_occ'):
        im = Image.new('L', (int(WX), int(WZ)), 0); dr = ImageDraw.Draw(im)
        for name, pts in o.polys:                                                   # toda a orla (calcadao, ciclovia, vagas, muro, escadas, pieres, pracas)
            if len(pts) >= 3: dr.polygon([(q[0], q[1]) for q in pts], fill=255)
        o._park_occ = o._street_occ | (_np.array(im.filter(ImageFilter.MaxFilter(7))) > 0)
    occ = o._park_occ
    def used(x, z, pad=2):
        i, j = int(x), int(z)
        return j < pad or i < pad or j >= occ.shape[0] - pad or i >= occ.shape[1] - pad or bool(occ[j - pad:j + pad + 1, i - pad:i + pad + 1].any())
    def beach(x, z):
        i, j = int(min(max(round(x / CELL), 0), NX - 1)), int(min(max(round(z / CELL), 0), NZ - 1))
        return bool(o.geo.beach_zone[j, i] and o.geo.Dsea[j, i] < 70.0)
    def land(x, z, lim=1.0): return o.sample(x, z) > lim and not beach(x, z)
    # eixo da alameda: a direcao com mais terra livre a partir da praca (a ponta e uma faixa de terra entre a praia e o canal)
    best_ax = None
    for da in range(0, 360, 10):
        an = math.radians(da); ux_, uz_ = math.cos(an), math.sin(an); d = R + 11.0
        while d < 150:
            x, z = cx + ux_ * d, cz + uz_ * d
            ok = land(x, z, 0.9) and not used(x, z, 2) and land(x + uz_ * 7, z - ux_ * 7, 0.8) and land(x - uz_ * 7, z + ux_ * 7, 0.8)
            if not ok: break
            d += 3.0
        if best_ax is None or d > best_ax[0] + 1e-6: best_ax = (d, ux_, uz_)
    ax, az = best_ax[1], best_ax[2]; wx_, wz_ = az, -ax                          # lateral do eixo
    def pt(u, w, dy=0.0):                                                         # u ao longo do eixo, w lateral
        x, z = cx + ax * u + wx_ * w, cz + az * u + wz_ * w
        return (x, o.sample(x, z) + dy, z)
    def strip(u0, u1, w0, w1, col, mat=PAVER, dy=0.05, layer='prom', step=3.0):
        if u1 - u0 < 2: return
        n = max(1, int(abs(u1 - u0) / step))
        for k in range(n):
            a, b = u0 + (u1 - u0) * k / n, u0 + (u1 - u0) * (k + 1) / n
            q = [pt(a, w0, dy), pt(b, w0, dy), pt(b, w1, dy), pt(a, w1, dy)]
            B.quad(mat, q, (0, 1, 0), col)
            if layer: g.polys.append((layer, [(v[0], v[2]) for v in q])) if hasattr(g, 'polys') else g.poly(layer, [(v[0], v[2]) for v in q])
    def near_stairs(x, z):
        for q in o.items.get('paths', []):
            if math.hypot(x - q['x'] - q['sx'] * 17, z - q['z'] - q['sz'] * 17) < 5.5: return True
        for st in o.items.get('stairs', []):
            for q in range(0, 9):
                if math.hypot(x - (st['x'] + st['dx'] * q), z - (st['z'] + st['dz'] * q)) < 5.5: return True
        return False
    def lamp(u, w):
        x, y, z = pt(u, w, 0.05)
        if near_stairs(x, z): return
        B.cyl(x, z, 0.09, y, y + 4.6, COL['lamp'], 8); B.cyl(x, z, 0.16, y, y + 0.4, COL['lamp'], 8)
        B.box(x, z, 0.7, 0.3, y + 4.5, y + 4.7, rgb('#FFF0B8'), PLAIN, True, False)
        o.items['lamps'].append({'x': round(x, 2), 'z': round(z, 2), 'y': round(y, 2)})
    def palm(u, w):
        x, y, z = pt(u, w, 0.0)
        if used(x, z, 1) or not land(x, z) or near_stairs(x, z): return
        o.palm_at(x, z, y + 0.25, rnd.uniform(0.95, 1.25)); o.items['palms'].append({'x': round(x, 2), 'z': round(z, 2), 'y': round(y + 0.3, 2), 'sp': 'palmeira', 'scale': 1.0, 'baked': True})
    def bench(u, w, face):
        x, y, z = pt(u, w, 0.05); fx, fz = (wx_, wz_) if face > 0 else (-wx_, -wz_); tx_, tz_ = -fz, fx
        c4 = [(x - tx_ * 0.95 - fx * 0.24, z - tz_ * 0.95 - fz * 0.24), (x + tx_ * 0.95 - fx * 0.24, z + tz_ * 0.95 - fz * 0.24), (x + tx_ * 0.95 + fx * 0.24, z + tz_ * 0.95 + fz * 0.24), (x - tx_ * 0.95 + fx * 0.24, z - tz_ * 0.95 + fz * 0.24)]
        B.obox_pts(c4, y + 0.4, y + 0.52, COL['bench'], WOOD, True, False)
        for sg in (-1, 1): B.box(x + tx_ * 0.7 * sg, z + tz_ * 0.7 * sg, 0.15, 0.4, y, y + 0.4, COL['iron'], PLAIN, True, False)
        o.items['benches'].append({'x': round(x, 2), 'z': round(z, 2), 'nx': round(-fx, 3), 'nz': round(-fz, 3)})
    # --- 1) alameda: da borda da praca ate o mirante
    u0 = R + 3.0; u1 = R + 10.0
    while u1 < 140 and land(*pt(u1 + 3, 0)[::2], lim=0.9) and not used(*pt(u1 + 3, 0)[::2], 2) and land(*pt(u1 + 3, 6)[::2], lim=0.8) and land(*pt(u1 + 3, -6)[::2], lim=0.8): u1 += 3.0
    u1 -= 9.0
    has_al = (u1 - u0) >= 26
    if not has_al: u1 = u0 - 12.0
    W = 5.2
    strip(u0, u1, -W / 2, W / 2, rgb('#D8D2C4'))
    strip(u0, u1, -W / 2 - 0.3, -W / 2, COL['wall2'], dy=0.06, layer='curb'); strip(u0, u1, W / 2, W / 2 + 0.3, COL['wall2'], dy=0.06, layer='curb')
    for k in range(0, int(u1 - u0), 7):                                             # juntas transversais
        a = u0 + k; B.quad(PLAIN, [pt(a, -W / 2, 0.062), pt(a + 0.08, -W / 2, 0.062), pt(a + 0.08, W / 2, 0.062), pt(a, W / 2, 0.062)], (0, 1, 0), COL['wall2'], None, True)
    u = u0 + 6.0; kk = 0
    while u < u1 - 4:
        for w in (-W / 2 - 1.6, W / 2 + 1.6): palm(u, w)
        u += 9.0
    u = u0 + 12.0
    while u < u1 - 6:
        lamp(u, -W / 2 - 0.9 if kk % 2 == 0 else W / 2 + 0.9); kk += 1; u += 18.0
    u = u0 + 20.0; kk = 0
    while u < u1 - 10:
        bench(u, (-W / 2 - 1.2) if kk % 2 == 0 else (W / 2 + 1.2), 1 if kk % 2 == 0 else -1); kk += 1; u += 36.0
    # canteiros floridos dos dois lados (grama baixa, meio-fio de pedra e flores)
    for sg in (-1, 1):
        w0, w1 = sg * (W / 2 + 3.4), sg * (W / 2 + 8.6)
        a, b = (min(w0, w1), max(w0, w1))
        uu = u0 + 4.0
        while uu < u1 - 6:
            u2 = min(uu + 22.0, u1 - 6)
            q = [pt(uu, a, 0.04), pt(u2, a, 0.04), pt(u2, b, 0.04), pt(uu, b, 0.04)]
            if all(land(v[0], v[2]) and not used(v[0], v[2], 1) for v in q):
                B.quad(PLAIN, q, (0, 1, 0), rgb('#4E8F3A'))
                for (pa, pb, qa, qb) in ((uu, u2, a, a), (uu, u2, b, b), (uu, uu, a, b), (u2, u2, a, b)):
                    c4 = [pt(pa, qa - 0.12, 0), pt(pb, qb - 0.12, 0), pt(pb, qb + 0.12, 0), pt(pa, qa + 0.12, 0)]
                    B.obox_pts([(v[0], v[2]) for v in c4], c4[0][1] - 0.1, c4[0][1] + 0.34, COL['wall'], STONE, True, False)
                for _ in range(26):
                    fu, fw = rnd.uniform(uu + 0.6, u2 - 0.6), rnd.uniform(a + 0.6, b - 0.6); x, y, z = pt(fu, fw, 0.04)
                    B.cyl(x, z, rnd.uniform(0.28, 0.5), y, y + rnd.uniform(0.12, 0.3), FLOWERS[rnd.randrange(len(FLOWERS))], 6, PLAIN, True)
            uu = u2 + 4.0
    # --- 2) mirante no fim da alameda
    mu = u1 + 7.0; mr = 7.5
    ring = [pt(mu + math.cos(2 * math.pi * k / 24) * mr, math.sin(2 * math.pi * k / 24) * mr, 0.05) for k in range(24)]
    if has_al and sum(1 for v in ring if land(v[0], v[2], 0.6)) >= 22 and not any(used(v[0], v[2], 1) for v in ring):
        for k in range(24):
            a0, a1 = 2 * math.pi * k / 24, 2 * math.pi * (k + 1) / 24
            c0, c1 = pt(mu, 0, 0.05), None
            q = [pt(mu, 0, 0.05), pt(mu + math.cos(a0) * mr, math.sin(a0) * mr, 0.05), pt(mu + math.cos(a1) * mr, math.sin(a1) * mr, 0.05)]
            B.tri(PAVER, q[0], q[1], q[2], (0, 1, 0), COL['wave1'] if k % 2 == 0 else COL['wave3'])
            g.poly('prom', [(v[0], v[2]) for v in q]) if hasattr(g, 'poly') else None
            if k % 3 != 0:                                                           # balaustrada (abre 1 de 3 vaos para a alameda e a vista)
                for rr, h in ((mr - 0.15, 1.0),):
                    x0, y0, z0 = pt(mu + math.cos(a0) * rr, math.sin(a0) * rr, 0.05); x1, y1, z1 = pt(mu + math.cos(a1) * rr, math.sin(a1) * rr, 0.05)
                    B.obox_pts([(x0, z0), (x1, z1), (x1 + (x0 - x1) * 0 + 0.0, z1 + 0.18), (x0, z0 + 0.18)], min(y0, y1), min(y0, y1) + 0.55, COL['wall'], STONE, True, False) if False else None
                    B.quad(STONE, [(x0, y0, z0), (x1, y1, z1), (x1, y1 + 1.0, z1), (x0, y0 + 1.0, z0)], (math.cos((a0 + a1) / 2) * -1, 0, math.sin((a0 + a1) / 2) * -1), COL['wall'], None, True)
                    B.quad(STONE, [(x1, y1, z1), (x0, y0, z0), (x0, y0 + 1.0, z0), (x1, y1 + 1.0, z1)], (math.cos((a0 + a1) / 2), 0, math.sin((a0 + a1) / 2)), COL['wall2'], None, True)
                    B.quad(STONE, [(x0, y0 + 1.0, z0), (x1, y1 + 1.0, z1), (x1 + (x0 - x1) * 0, y1 + 1.0, z1 + 0.0), (x0, y0 + 1.0, z0)], (0, 1, 0), COL['wall'], None, True)
        x, y, z = pt(mu, 0, 0.05)
        B.cyl(x, z, 0.5, y, y + 0.6, COL['wall'], 10, STONE, True)
        B.cyl(x, z, 0.09, y, y + 4.8, COL['lamp'], 8); B.box(x, z, 0.8, 0.4, y + 4.6, y + 4.85, rgb('#FFF0B8'), PLAIN, True, False)
        o.items['lamps'].append({'x': round(x, 2), 'z': round(z, 2), 'y': round(y, 2)})
        for k in range(4):
            a = math.pi / 2 * k + math.pi / 4; x, y, z = pt(mu + math.cos(a) * (mr - 2.2), math.sin(a) * (mr - 2.2), 0.05)
            fx, fz = -(x - pt(mu, 0)[0]), -(z - pt(mu, 0)[2]); l = math.hypot(fx, fz) or 1; fx, fz = fx / l, fz / l; tx_, tz_ = -fz, fx
            c4 = [(x - tx_ * 0.95 - fx * 0.24, z - tz_ * 0.95 - fz * 0.24), (x + tx_ * 0.95 - fx * 0.24, z + tz_ * 0.95 - fz * 0.24), (x + tx_ * 0.95 + fx * 0.24, z + tz_ * 0.95 + fz * 0.24), (x - tx_ * 0.95 + fx * 0.24, z - tz_ * 0.95 + fz * 0.24)]
            B.obox_pts(c4, y + 0.4, y + 0.52, COL['bench'], WOOD, True, False)
    # --- 3) ligacao ate a avenida: caminho largo de pedestres da praca ate a calcada mais proxima (do lado da terra)
    best = None
    for da in range(-70, 71, 10):
        ang = math.radians(da); dx_ = lx * math.cos(ang) - lz * math.sin(ang); dz_ = lx * math.sin(ang) + lz * math.cos(ang)
        d = R + 1.0
        while d < 75:
            x, z = cx + dx_ * d, cz + dz_ * d
            if used(x, z, 0): break
            d += 1.5
        if d < 75 and (best is None or d < best[0]): best = (d, dx_, dz_)
    if best:
        d, dx_, dz_ = best; d1 = d - 2.0
        n = int((d1 - R) / 2.5) + 1
        px_, pz_ = -dz_, dx_
        for k in range(n):
            a, b = R + 0.5 + (d1 - R - 0.5) * k / n, R + 0.5 + (d1 - R - 0.5) * (k + 1) / n
            def PQ(dd, ww):
                x, z = cx + dx_ * dd + px_ * ww, cz + dz_ * dd + pz_ * ww; return (x, o.sample(x, z) + 0.05, z)
            B.quad(PAVER, [PQ(a, -2.2), PQ(b, -2.2), PQ(b, 2.2), PQ(a, 2.2)], (0, 1, 0), rgb('#D8D2C4'))
        for k, dd in enumerate(range(int(R + 5), int(d1 - 3), 14)):
            for sg in (-1, 1):
                x, z = cx + dx_ * dd + px_ * sg * 3.6, cz + dz_ * dd + pz_ * sg * 3.6
                if not used(x, z, 1) and land(x, z) and not near_stairs(x, z): o.palm_at(x, z, o.sample(x, z) + 0.25, 1.1); o.items['palms'].append({'x': round(x, 2), 'z': round(z, 2), 'y': round(o.sample(x, z) + 0.3, 2), 'sp': 'palmeira', 'scale': 1.0, 'baked': True})
            x, z = cx + dx_ * (dd + 7) + px_ * 3.0, cz + dz_ * (dd + 7) + pz_ * 3.0
            if not used(x, z, 1) and land(x, z):
                y = o.sample(x, z) + 0.05; B.cyl(x, z, 0.09, y, y + 4.6, COL['lamp'], 8); B.box(x, z, 0.7, 0.3, y + 4.5, y + 4.7, rgb('#FFF0B8'), PLAIN, True, False); o.items['lamps'].append({'x': round(x, 2), 'z': round(z, 2), 'y': round(y, 2)})
    # --- 4) quiosque redondo (cobertura de palha) perto da praca, do lado da terra
    for da in (35, -35, 55, -55):
        ang = math.radians(da); dx_ = lx * math.cos(ang) - lz * math.sin(ang); dz_ = lx * math.sin(ang) + lz * math.cos(ang)
        kx, kz = cx + dx_ * (R + 13.0), cz + dz_ * (R + 13.0)
        if land(kx, kz, 1.0) and not used(kx, kz, 5):
            y = o.sample(kx, kz) + 0.05
            B.cyl(kx, kz, 3.4, y, y + 0.18, COL['wave1'], 14, PAVER, True)
            B.cyl(kx, kz, 1.9, y + 0.18, y + 2.5, rgb('#E8D9B5'), 12, PLAIN, False)
            B.cyl(kx, kz, 3.5, y + 2.5, y + 4.4, rgb('#C79B4E'), 14, ROOF, False, 0.15)
            for q in range(6):
                a = 2 * math.pi * q / 6; B.cyl(kx + math.cos(a) * 3.0, kz + math.sin(a) * 3.0, 0.08, y + 0.18, y + 2.6, COL['rail'], 6, METAL, True)
                tx_, tz_ = kx + math.cos(a + 0.5) * 2.4, kz + math.sin(a + 0.5) * 2.4
                if q % 2 == 0:
                    B.cyl(tx_, tz_, 0.55, y + 0.78, y + 0.82, COL['white'], 8, PLAIN, True); B.cyl(tx_, tz_, 0.05, y + 0.18, y + 0.78, COL['iron'], 6, METAL, True)
            break
    # --- 4b) equipamentos do parque: quadra poliesportiva, playground e area de piquenique (cada um num trecho plano e livre)
    taken = [(cx, cz, R + 6.0)]
    for (ux_, uz_) in ((0, 0),):
        pass
    if has_al: taken.append((cx + ax * (u1 / 2 + R / 2), cz + az * (u1 / 2 + R / 2), max(u1 / 2 + 4.0, 12.0)))              # corredor da alameda
    def spot(half_x, half_z, dmin=R + 10, dmax=95, prefer=None):
        import itertools
        angs = list(range(0, 360, 12)); rnd.shuffle(angs)
        for d in range(int(dmin), int(dmax), 5):
            for ang in angs:
                a_ = math.radians(ang); x, z = cx + math.cos(a_) * d, cz + math.sin(a_) * d
                rad = math.hypot(half_x, half_z) + 1.5
                if any(math.hypot(x - tx, z - tz) < tr + rad for tx, tz, tr in taken): continue
                hs = []; ok = True
                for gx in (-1, -0.5, 0, 0.5, 1):
                    for gz in (-1, -0.5, 0, 0.5, 1):
                        px, pz = x + gx * half_x, z + gz * half_z
                        if not land(px, pz, 1.0) or used(px, pz, 3): ok = False; break
                        hs.append(o.sample(px, pz))
                    if not ok: break
                if ok and max(hs) - min(hs) < 0.5:
                    taken.append((x, z, rad)); return x, z, a_
        print('   spot nao achado', half_x, half_z)
        return None
    def box_(x, z, hx, hz, ang, y0, y1, col, mat=PLAIN):
        ca, sa = math.cos(ang), math.sin(ang)
        c4 = [(x + ca * dx_ - sa * dz_, z + sa * dx_ + ca * dz_) for dx_, dz_ in ((-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz))]
        B.obox_pts(c4, y0, y1, col, mat, True, False)
        return c4
    def floor_(x, z, hx, hz, ang, y, col, mat=PAVER, layer='prom'):
        ca, sa = math.cos(ang), math.sin(ang)
        q = [(x + ca * dx_ - sa * dz_, y, z + sa * dx_ + ca * dz_) for dx_, dz_ in ((-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz))]
        B.quad(mat, q, (0, 1, 0), col)
        g.poly(layer, [(v[0], v[2]) for v in q])
    def line_(x, z, hx, hz, ang, y, a0, b0, a1, b1, w=0.07):
        ca, sa = math.cos(ang), math.sin(ang)
        def P_(u, v): return (x + ca * u - sa * v, y, z + sa * u + ca * v)
        dx_, dz_ = a1 - a0, b1 - b0; l = math.hypot(dx_, dz_) or 1; nx_, nz_ = -dz_ / l * w, dx_ / l * w
        B.quad(PLAIN, [P_(a0 - nx_, b0 - nz_), P_(a1 - nx_, b1 - nz_), P_(a1 + nx_, b1 + nz_), P_(a0 + nx_, b0 + nz_)], (0, 1, 0), COL['white'], None, True)
    # quadra poliesportiva 26 x 14
    sp = spot(13.5, 7.5)
    if sp:
        x, z, a_ = sp; y = o.sample(x, z) + 0.06; ang = a_
        floor_(x, z, 14.2, 8.2, ang, y - 0.02, rgb('#9C9486'))
        floor_(x, z, 13.0, 7.0, ang, y, rgb('#3F6FA8'))
        for (a0, b0, a1, b1) in ((-13, -7, 13, -7), (-13, 7, 13, 7), (-13, -7, -13, 7), (13, -7, 13, 7), (0, -7, 0, 7)):
            line_(x, z, 13, 7, ang, y + 0.012, a0, b0, a1, b1)
        for sgn in (-1, 1):                                                       # arcos de gol/cestas
            ca, sa = math.cos(ang), math.sin(ang); hx_, hz_ = x + ca * 12.2 * sgn, z + sa * 12.2 * sgn
            B.cyl(hx_, hz_, 0.08, y, y + 3.1, COL['lamp'], 8, METAL, True)
            box_(hx_ - ca * 0.35 * sgn, hz_ - sa * 0.35 * sgn, 0.05, 0.9, ang, y + 2.6, y + 3.5, COL['white'])
        for sgn in (-1, 1):                                                       # alambrado baixo nas laterais
            for k in range(-6, 7):
                ca, sa = math.cos(ang), math.sin(ang)
                B.cyl(x + ca * k * 2.2 - sa * 8.0 * sgn, z + sa * k * 2.2 + ca * 8.0 * sgn, 0.05, y - 0.02, y + 1.6, COL['iron'], 6, METAL, True)
        o.items['courts'].append({'x': round(x, 1), 'z': round(z, 1), 'tx': round(math.cos(ang), 3), 'tz': round(math.sin(ang), 3)})
    # playground 14 x 12 (piso de borracha + balanco, escorregador, gangorra, caixa de areia)
    sp = spot(7.5, 6.5)
    if sp:
        x, z, a_ = sp; y = o.sample(x, z) + 0.06; ang = a_
        floor_(x, z, 7.6, 6.6, ang, y - 0.02, COL['wall2']); floor_(x, z, 7.0, 6.0, ang, y, rgb('#C0643C'))
        ca, sa = math.cos(ang), math.sin(ang)
        def L_(u, v): return (x + ca * u - sa * v, z + sa * u + ca * v)
        for sgn in (-1, 1):                                                       # balanco
            px, pz = L_(-4.5, 2.2 * sgn)
            B.cyl(px, pz, 0.07, y, y + 2.6, rgb('#2E7D32'), 6, METAL, True)
        for cz_ in (-1.4, 1.4):
            a1_, b1_ = L_(-4.5, cz_ - 3.6), L_(-4.5, cz_ + 3.6)
        px0, pz0 = L_(-4.5, -3.6); px1, pz1 = L_(-4.5, 3.6)
        B.cyl(px0, pz0, 0.07, y, y + 2.6, rgb('#2E7D32'), 6, METAL, True); B.cyl(px1, pz1, 0.07, y, y + 2.6, rgb('#2E7D32'), 6, METAL, True)
        box_(*L_(-4.5, 0.0), 0.05, 3.7, ang, y + 2.5, y + 2.62, rgb('#2E7D32'), METAL)
        for v in (-1.8, 1.8):
            sx_, sz_ = L_(-4.5, v); box_(sx_, sz_, 0.2, 0.22, ang, y + 0.5, y + 0.55, rgb('#D6402A'))
            B.quad(PLAIN, [(sx_ + ca * 0.2, y + 2.5, sz_ + sa * 0.2), (sx_ - ca * 0.2, y + 2.5, sz_ - sa * 0.2), (sx_ - ca * 0.2, y + 0.55, sz_ - sa * 0.2), (sx_ + ca * 0.2, y + 0.55, sz_ + sa * 0.2)], (0, 0, 1), COL['iron'], None, True)
        sx_, sz_ = L_(3.0, -3.0)                                                  # escorregador: torre + rampa
        box_(sx_, sz_, 0.8, 0.8, ang, y, y + 2.2, rgb('#FDD835'))
        ex, ez = L_(3.0 + 3.6, -3.0)
        B.quad(PLAIN, [(sx_ + ca * 0.8 - sa * 0.35, y + 2.0, sz_ + sa * 0.8 + ca * 0.35), (sx_ + ca * 0.8 + sa * 0.35, y + 2.0, sz_ + sa * 0.8 - ca * 0.35), (ex + sa * 0.35, y + 0.2, ez - ca * 0.35), (ex - sa * 0.35, y + 0.2, ez + ca * 0.35)], (0, 1, 0), rgb('#1E88E5'), None, True)
        gx_, gz_ = L_(3.0, 3.0); box_(gx_, gz_, 1.6, 1.6, ang, y, y + 0.35, rgb('#E8D9B5')); box_(gx_, gz_, 1.3, 1.3, ang, y + 0.3, y + 0.38, rgb('#D9B65B'))   # caixa de areia
        o.items.setdefault('playgrounds', []).append({'x': round(x, 1), 'z': round(z, 1)})
    # area de piquenique: cobertura quadrada + 3 mesas com bancos
    sp = spot(6.0, 6.0)
    if sp:
        x, z, a_ = sp; y = o.sample(x, z) + 0.06; ang = a_
        floor_(x, z, 6.2, 6.2, ang, y, rgb('#D8D2C4'))
        ca, sa = math.cos(ang), math.sin(ang)
        for (u, v) in ((-5, -5), (5, -5), (5, 5), (-5, 5)):
            B.cyl(x + ca * u - sa * v, z + sa * u + ca * v, 0.14, y, y + 3.0, rgb('#7A5A3A'), 6, WOOD, True)
        box_(x, z, 6.0, 6.0, ang, y + 3.0, y + 3.25, rgb('#8B6B47'), WOOD)
        for (u, v) in ((-2.4, 0.0), (2.4, -2.6), (2.4, 2.6)):
            tx_, tz_ = x + ca * u - sa * v, z + sa * u + ca * v
            box_(tx_, tz_, 1.0, 0.45, ang, y + 0.72, y + 0.78, rgb('#8B6B47'), WOOD)
            for sg in (-1, 1): box_(tx_ - sa * 0.95 * sg, tz_ + ca * 0.95 * sg, 1.0, 0.18, ang, y + 0.42, y + 0.47, rgb('#7A5A3A'), WOOD)
            box_(tx_, tz_, 0.1, 0.1, ang, y, y + 0.72, COL['iron'])
        o.items.setdefault('picnic', []).append({'x': round(x, 1), 'z': round(z, 1)})
    # --- 5) arvores e palmeiras no gramado em volta (nunca em cima de caminhos, ruas, mirante, praca)
    placed = 0; tries = 0
    while placed < 70 and tries < 1500:
        tries += 1
        ang = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(R + 7, 150)
        x, z = cx + math.cos(ang) * d, cz + math.sin(ang) * d
        uu = (x - cx) * ax + (z - cz) * az; ww = (x - cx) * wx_ + (z - cz) * wz_
        if abs(ww) < W / 2 + 10 and -2 < uu < u1 + 16: continue
        if not land(x, z, 1.2) or used(x, z, 4): continue
        if math.hypot(x - cx, z - cz) < R + 6: continue
        o.trees_extra = getattr(o, 'trees_extra', [])
        P.trees.append([round(x, 1), round(z, 1), rnd.choice((0, 1, 1, 3, 3)), round(rnd.uniform(1.0, 1.6), 2), round(rnd.uniform(0, 6.28), 2), round(rnd.uniform(0, 1), 2)]); placed += 1
