"""Pontes vermelhas (SO CENARIO, estilo Golden Gate), portais de tunel e pilares das pontes sobre o rio."""
import math
from bake import rgb, PLAIN, STONE, METAL, PAVER
import terrain_final as T

ASPHALT = 15
OR1 = rgb('#C0361B'); OR2 = rgb('#A82B14'); OR3 = rgb('#D2492B')
CONC = rgb('#C9C6BE'); CONC2 = rgb('#B0ABA0'); DARK = rgb('#1C1C20'); ASPH = rgb('#4A4B50'); WHITE = rgb('#F2F2F2'); YEL = rgb('#F5C518'); LAMP = rgb('#2B2E33')

def norm3(v):
    l = math.sqrt(sum(a * a for a in v)) or 1e-9
    return (v[0] / l, v[1] / l, v[2] / l)

def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

def bar(B, p0, p1, w, col, mat=METAL, w2=None):
    """barra de secao quadrada entre dois pontos 3D"""
    w2 = w if w2 is None else w2
    d = norm3((p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]))
    up = (0, 1, 0) if abs(d[1]) < 0.9 else (1, 0, 0)
    s = norm3(cross(d, up)); t = norm3(cross(d, s))
    def C(p, sx, tx, ww): return (p[0] + s[0] * sx * ww / 2 + t[0] * tx * ww / 2, p[1] + s[1] * sx * ww / 2 + t[1] * tx * ww / 2, p[2] + s[2] * sx * ww / 2 + t[2] * tx * ww / 2)
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for q in range(4):
        a, b = corners[q], corners[(q + 1) % 4]
        quad = [C(p0, a[0], a[1], w), C(p0, b[0], b[1], w), C(p1, b[0], b[1], w2), C(p1, a[0], a[1], w2)]
        nrm = norm3(cross((quad[1][0] - quad[0][0], quad[1][1] - quad[0][1], quad[1][2] - quad[0][2]), (quad[3][0] - quad[0][0], quad[3][1] - quad[0][1], quad[3][2] - quad[0][2])))
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        out = (s[0] * mid[0] + t[0] * mid[1], s[1] * mid[0] + t[1] * mid[1], s[2] * mid[0] + t[2] * mid[1])
        if nrm[0] * out[0] + nrm[1] * out[1] + nrm[2] * out[2] < 0: nrm = (-nrm[0], -nrm[1], -nrm[2])
        B.quad(mat, quad, nrm, col, None, True)

def slab(B, x0, x1, z0, z1, y0, y1, col, mat=PLAIN):
    B.box((x0 + x1) / 2, (z0 + z1) / 2, abs(x1 - x0), abs(z1 - z0), y0, y1, col, mat, True, False)

def tower(B, tx, zc, y0, y_top, deck):
    gap = 11.0                                              # eixo das pernas (fora do tabuleiro de 20 m)
    for sg in (-1, 1):
        zz = zc + sg * gap
        # perna afunilada em 3 trechos (art deco)
        levels = [(y0, deck + 12, 3.6), (deck + 12, deck + 34, 3.0), (deck + 34, y_top, 2.5)]
        for ya, yb, w in levels:
            B.obox_pts([(tx - w / 2, zz - w / 2), (tx + w / 2, zz - w / 2), (tx + w / 2, zz + w / 2), (tx - w / 2, zz + w / 2)], ya, yb, OR1, METAL, True, False)
            # nervuras verticais nas faces (profundidade)
            for fx in (-1, 1):
                B.box(tx + fx * (w / 2 + 0.12), zz, 0.24, w * 0.55, ya, yb, OR2, METAL, True, False)
        B.box(tx, zz, 3.4, 3.4, y_top, y_top + 1.6, OR2, METAL, True, False)          # capitel/sela dos cabos
    # travessas em portico (4 niveis)
    for hh, hgt in ((deck + 15, 3.0), (deck + 27, 2.6), (deck + 39, 2.4), (y_top - 3, 3.2)):
        slab(B, tx - 1.4, tx + 1.4, zc - gap - 1.4, zc + gap + 1.4, hh, hh + hgt, OR1, METAL)
        # diagonais dentro do portico
        bar(B, (tx, hh, zc - gap + 1.5), (tx, hh + hgt, zc - 1), 0.5, OR2)
        bar(B, (tx, hh, zc + gap - 1.5), (tx, hh + hgt, zc + 1), 0.5, OR2)

def red_bridge(B, rb, hf, deck_y, lookout_x):
    """rb: z, x_a (lado da montanha), x_b (lado da cidade), towers, portal. deck_y: nivel do mirante."""
    zc = rb['z']; xa, xb = rb['x_a'], rb['x_b']
    sgn = 1 if xb > xa else -1                           # sentido do lado da cidade para a montanha = -sgn
    t1, t2 = sorted(rb['towers'])
    # portal: onde o terreno passa de deck+9
    xp = xa
    for _ in range(400):
        if T.sample8(hf, xp, zc) >= deck_y + 9: break
        xp += -sgn * 2.0 if xb > xa else 2.0
        if abs(xp - xa) > 260: break
    xl, xr = (min(xa, xb), max(xa, xb))
    # --- tabuleiro: de lookout_x ate o portal
    xs = sorted([lookout_x + sgn * 0.15, xp]); x0, x1 = xs          # o tabuleiro comeca exatamente onde a rua termina (no do mirante)
    yd = deck_y + 0.12
    W2 = 10.0
    # secao igual a da rua que chega (coletora): pista +-6 m, guia, calcada ate +-10 m
    slab(B, x0, x1, zc - W2, zc + W2, yd - 0.4, yd - 0.15, rgb('#8E8C86'), PAVER)                  # laje de concreto
    slab(B, x0, x1, zc - 6.0, zc + 6.0, yd - 0.15, yd, rgb('#4A4A4E'), ASPHALT)                    # pista (mesma cor do asfalto da cidade)
    for off in (-0.2, 0.2):
        slab(B, x0, x1, zc + off - 0.06, zc + off + 0.06, yd, yd + 0.02, YEL)
    for off in (-5.6, 5.6):
        slab(B, x0, x1, zc + off - 0.06, zc + off + 0.06, yd, yd + 0.02, WHITE)
    for sg in (-1, 1):
        slab(B, x0, x1, zc + sg * 6.0 - 0.1 if sg > 0 else zc - 6.2, zc + sg * 6.2 if sg > 0 else zc - 6.0 + 0.1, yd, yd + 0.15, CONC2, PAVER)   # guia
        lo, hi = (zc + 6.2, zc + 10.0) if sg > 0 else (zc - 10.0, zc - 6.2)
        slab(B, x0, x1, lo, hi, yd, yd + 0.15, CONC, PAVER)                                                              # calcada
        slab(B, x0, x1, zc + sg * 10.0 - 0.25, zc + sg * 10.0 + 0.25, yd, yd + 1.15, CONC2, PAVER)  # mureta
        bar(B, (x0, yd + 1.3, zc + sg * 10.0), (x1, yd + 1.3, zc + sg * 10.0), 0.12, OR1)             # corrimao
        for xx in range(int(x0), int(x1), 3):
            bar(B, (xx, yd + 1.15, zc + sg * 10.0), (xx, yd + 1.3, zc + sg * 10.0), 0.1, OR2)
    # viga-caixao + trelica de enrijecimento sob/ao lado do tabuleiro (so sobre a agua e ate o portal)
    slab(B, x0, x1, zc - W2 - 0.6, zc + W2 + 0.6, yd - 3.4, yd - 0.4, OR2, METAL)
    for sg in (-1, 1):
        n = int((x1 - x0) // 7)
        for q in range(n):
            xa_, xb_ = x0 + q * 7, x0 + (q + 1) * 7
            bar(B, (xa_, yd - 3.3, zc + sg * (W2 + 0.7)), (xb_ - 3.5, yd - 0.45, zc + sg * (W2 + 0.7)), 0.35, OR1)
            bar(B, (xa_ + 3.5, yd - 0.45, zc + sg * (W2 + 0.7)), (xb_, yd - 3.3, zc + sg * (W2 + 0.7)), 0.35, OR1)
    # aterro + muros nas pontas em terra (abaixo do deck, ate o terreno)
    for sg in (-1, 1):
        for xx in range(int(x0), int(x1), 4):
            ht = T.sample8(hf, xx, zc + sg * W2)
            if ht < yd - 3.4 and ht > -0.5:
                B.box(xx + 2, zc + sg * (W2 + 0.3), 4, 0.6, ht, yd - 3.4, CONC2, STONE, False, False)
    # --- torres e cabos
    y_top = deck_y + 58.0
    for tx in (t1, t2): tower(B, tx, zc, -3.0, y_top, deck_y)
    cab_z = [zc - 12.5, zc + 12.5]
    L = t2 - t1; xm = (t1 + t2) / 2; y_mid = deck_y + 13.0
    anc_l = t1 - 62.0; anc_r = t2 + 62.0
    for cz in cab_z:
        pts = []
        # vao lateral esquerdo (reto-curvo) -> vao central (parabola) -> vao lateral direito
        for q in range(0, 16): u = q / 15; x = anc_l + (t1 - anc_l) * u; y = (deck_y + 4.0) + (y_top - 1 - (deck_y + 4.0)) * (u ** 1.6); pts.append((x, y, cz))
        for q in range(1, 41): u = q / 40; x = t1 + L * u; y = y_top - 1 - (y_top - 1 - y_mid) * (1 - ((x - xm) / (L / 2)) ** 2); pts.append((x, y, cz))
        for q in range(1, 16): u = q / 15; x = t2 + (anc_r - t2) * u; y = (y_top - 1) + ((deck_y + 4.0) - (y_top - 1)) * (u ** 0.62); pts.append((x, y, cz))
        for p0, p1 in zip(pts, pts[1:]): bar(B, p0, p1, 0.95, OR1, METAL)
        # pendurais verticais a cada ~12 m no vao central e nos laterais
        for (x, y, z) in pts[::3]:
            if t1 + 8 < x < t2 - 8 or (anc_l + 8 < x < t1 - 4) or (t2 + 4 < x < anc_r - 8):
                bar(B, (x, y - 0.4, z), (x, yd + 1.15, z), 0.14, OR3)
    # ancoragens (blocos de concreto) nas duas extremidades dos cabos
    for ax in (anc_l, anc_r):
        for sg in (-1, 1):                                      # blocos AO LADO do tabuleiro (nunca em cima da pista)
            slab(B, ax - 5, ax + 5, min(zc + sg * 11.2, zc + sg * 18.0), max(zc + sg * 11.2, zc + sg * 18.0), deck_y - 3, deck_y + 6, CONC2, STONE)
            slab(B, ax - 5.4, ax + 5.4, min(zc + sg * 11.0, zc + sg * 18.4), max(zc + sg * 11.0, zc + sg * 18.4), deck_y + 6, deck_y + 6.5, CONC, STONE)
    # --- portal do tunel (so visual): moldura de concreto + vao escuro com arco
    px = xp; d = -1 if xb > xa else 1                    # d aponta da ponte para dentro da montanha
    face_x = px
    for sg in (-1, 1): slab(B, px - 1.5, px + 1.5, zc + sg * 7.8 - 3.2 * (1 if sg > 0 else 0) + (3.2 if sg < 0 else 0) - 0.1, zc + sg * 7.8 + 3.2 * (1 if sg > 0 else 0) - (3.2 if sg < 0 else 0) + 0.1, yd - 0.4, yd + 11.0, CONC, STONE)
    slab(B, px - 1.5, px + 1.5, zc - 11.0, zc + 11.0, yd + 7.6, yd + 11.0, CONC, STONE)
    # vao escuro (plano) recuado
    n = 14
    for q in range(n):
        a0 = math.pi * q / n; a1 = math.pi * (q + 1) / n
        r = 7.6
        p = [(px + 0.6 * d, yd, zc - r * math.cos(a0)), (px + 0.6 * d, yd + 0.0 + 0.0, zc - r * math.cos(a1))]
        yy0 = yd + 0.0 + (r * 0.75) * math.sin(a0); yy1 = yd + (r * 0.75) * math.sin(a1)
        B.quad(PLAIN, [(px + 0.7 * d, yd, zc - r * math.cos(a0)), (px + 0.7 * d, yd, zc - r * math.cos(a1)), (px + 0.7 * d, yy1 + 1.0, zc - r * math.cos(a1)), (px + 0.7 * d, yy0 + 1.0, zc - r * math.cos(a0))],
               (-d, 0, 0), DARK, None, False)
    return {'portal_x': px, 'deck_y': deck_y, 'tower_top': y_top}

def bridge_piers(B, stl_pts, hf, yroad, half):
    """pilares sob o tabuleiro de uma ponte sobre o rio: stl_pts = [(x,z,y,tx,tz)] em intervalos de ~28 m"""
    for (x, z, y, tx, tz) in stl_pts:
        nx_, nz_ = -tz, tx
        for sg in (-1, 1):
            cx, cz = x + nx_ * 3.6 * sg, z + nz_ * 3.6 * sg
            ht = T.sample8(hf, cx, cz)
            top = y - 1.5
            if top - ht > 2.0:
                B.obox_pts([(cx - 0.9 * tx - 0.6 * nx_, cz - 0.9 * tz - 0.6 * nz_), (cx + 0.9 * tx - 0.6 * nx_, cz + 0.9 * tz - 0.6 * nz_), (cx + 0.9 * tx + 0.6 * nx_, cz + 0.9 * tz + 0.6 * nz_), (cx - 0.9 * tx + 0.6 * nx_, cz - 0.9 * tz + 0.6 * nz_)], min(ht, -2.0), top, CONC2, STONE, False, False)
        # travessa
        B.obox_pts([(x - 1.0 * tx - 4.6 * nx_, z - 1.0 * tz - 4.6 * nz_), (x + 1.0 * tx - 4.6 * nx_, z + 1.0 * tz - 4.6 * nz_), (x + 1.0 * tx + 4.6 * nx_, z + 1.0 * tz + 4.6 * nz_), (x - 1.0 * tx + 4.6 * nx_, z - 1.0 * tz + 4.6 * nz_)], y - 2.0, y - 1.4, CONC2, STONE, True, False)
