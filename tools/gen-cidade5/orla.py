"""ORLA das praias: calcadao com ondas + ciclovia, muro com escadas para a areia, faixa de palmeiras, quiosques, salva-vidas, chuveiros, redes de volei, guarda-sois e PIERES."""
import math, random
import numpy as np
from bake import rgb, shade, PLAIN, STONE, WOOD, METAL, PAVER, ROOF, TILE
ASPH = 15
from plan import *
import shore, scenery

YP = 2.40           # nivel do calcadao (acima do mar)
HALF_W = 7.0        # meia-largura do calcadao (de -7 mar a +7 avenida)
GARDEN_O = 9.4      # jardim de palmeiras de +7 a +10,3; guia; vagas de +10,5 ate a pista (+16 = borda do asfalto da avenida)
PARK_O1 = ORLA_CALC - 11.5
XW_HALF = 1.75      # meia-largura da travessia de pedestres (patamar sem vagas)
SW_Y = 0.27; ROADY = 0.12
COL = {'asph': rgb('#4A4A4E'), 'bay': rgb('#A7A59C'), 'curbP': rgb('#C9C4B8'), 'stall': rgb('#F2F2F2'), 'wave1': rgb('#EDE7DA'), 'wave2': rgb('#B4AC9C'), 'wave3': rgb('#D9D2C2'), 'bike': rgb('#B8452F'), 'wall': rgb('#CFCABF'), 'wall2': rgb('#B3AD9F'), 'grass': rgb('#6FA84A'),
       'wood': rgb('#8B6B47'), 'wood2': rgb('#6E5236'), 'rail': rgb('#E9E6DE'), 'lamp': rgb('#2B2E33'), 'bench': rgb('#7A5A3A'), 'iron': rgb('#2A2C30'), 'sand': rgb('#E4D4B4'),
       'roof': rgb('#B58A4A'), 'towerR': rgb('#D6402A'), 'towerW': rgb('#F2F2F2'), 'net': rgb('#E5E5E5'), 'step': rgb('#D8D3C7'), 'step2': rgb('#BEB8AA'), 'white': rgb('#F5F5F5'), 'water': rgb('#4F9BD0'),
       'trunk': rgb('#7A5A3A'), 'leaf': rgb('#3F8A3F'), 'shower': rgb('#A8B0B8')}
UMB = [rgb(c) for c in ('#E53935', '#FDD835', '#1E88E5', '#43A047', '#FB8C00', '#8E24AA', '#00ACC1')]

def norm(dx, dz):
    l = math.hypot(dx, dz) or 1e-9
    return dx / l, dz / l

class Orla:
    def __init__(self, gr, geo, hf, seed=RNG):
        self.g = gr; self.geo = geo; self.hf = hf; self.B = gr.B; self.rnd = random.Random(seed)
        self.gy, self.gx = np.gradient(geo.Dsea, CELL)
        self.items = {'palms': [], 'lamps': [], 'benches': [], 'kiosks': [], 'towers': [], 'showers': [], 'courts': [], 'umbrellas': [], 'stairs': [], 'piers': [], 'paths': [], 'bins': []}
        self.stats = {'prom_m': 0.0, 'wall_m': 0.0, 'stairs': 0, 'piers': 0}
        self.lines = []
        self.polys = []          # (layer, pts) p/ validar
        self.frames_all = []

    # ---------------------------------------------------------- geometria basica
    def grad(self, x, z):
        fx = min(max(x / CELL, 0), NX - 1.001); fz = min(max(z / CELL, 0), NZ - 1.001); i, j = int(fx), int(fz); a, b = fx - i, fz - j
        def bl(A): return (A[j, i] * (1 - a) + A[j, i + 1] * a) * (1 - b) + (A[j + 1, i] * (1 - a) + A[j + 1, i + 1] * a) * b
        return bl(self.gx), bl(self.gy)

    def frames(self, line, step=4.0):
        pts = shore.resample(line, step); out = []
        for k, p in enumerate(pts):
            a = pts[max(k - 2, 0)]; b = pts[min(k + 2, len(pts) - 1)]
            tx, tz = norm(b[0] - a[0], b[1] - a[1]); gx, gz = self.grad(*p)
            nx_, nz_ = -tz, tx
            if nx_ * gx + nz_ * gz < 0: nx_, nz_ = -nx_, -nz_              # normal para o lado da AVENIDA (aumenta a distancia ao mar)
            out.append({'x': p[0], 'z': p[1], 'tx': tx, 'tz': tz, 'nx': nx_, 'nz': nz_, 's': 0.0})
        acc = 0.0
        for k in range(1, len(out)):
            acc += math.hypot(out[k]['x'] - out[k - 1]['x'], out[k]['z'] - out[k - 1]['z']); out[k]['s'] = acc
        return out

    def P(self, f, o, dy=0.0, s_off=0.0):
        return (f['x'] + f['nx'] * o + f['tx'] * s_off, f['yp'] + dy, f['z'] + f['nz'] * o + f['tz'] * s_off)

    def strip(self, fr, o0, o1, dy, mat, col, layer=None, i0=0, i1=None):
        i1 = len(fr) - 1 if i1 is None else i1
        for k in range(i0, i1):
            a, b = fr[k], fr[k + 1]
            q = [self.P(a, o0, dy), self.P(b, o0, dy), self.P(b, o1, dy), self.P(a, o1, dy)]
            self.g.quad(mat, q, col, layer)

    def vwall(self, fr, o, y0, y1, col, face, mat=STONE, gaps=()):
        for k in range(len(fr) - 1):
            a, b = fr[k], fr[k + 1]
            if any(g0 <= a['s'] <= g1 or g0 <= b['s'] <= g1 for g0, g1 in gaps): continue
            pa, pb = self.P(a, o, y0), self.P(b, o, y0)
            nv = (a['nx'] * face, 0, a['nz'] * face)
            self.B.quad(mat, [pa, pb, (pb[0], b['yp'] + y1, pb[2]), (pa[0], a['yp'] + y1, pa[2])], nv, col, None, True)

    # ---------------------------------------------------------- cadeia da Av. Beira-Mar -> quadros da orla
    def chains(self):
        g = self.g; c = g.c
        ks = [k for k, e in enumerate(c.edges) if g.is_beach(k) and e['kind'] == 'n']
        adj = {}
        for k in ks:
            e = c.edges[k]; adj.setdefault(e['a'], []).append(k); adj.setdefault(e['b'], []).append(k)
        used = set(); out = []
        starts = [n for n, l in adj.items() if len(l) == 1] + [n for n, l in adj.items() if len(l) != 1]
        for n0 in starts:
            for k0 in adj[n0]:
                if k0 in used: continue
                seq = []; n = n0; k = k0
                while k is not None and k not in used:
                    used.add(k); e = c.edges[k]; fwd = e['a'] == n; seq.append((k, fwd)); n = e['b'] if fwd else e['a']
                    nxt = [q for q in adj.get(n, []) if q not in used]
                    k = nxt[0] if len(adj.get(n, [])) == 2 and nxt else None
                st = []
                for k, fwd in seq:
                    L = g.elen(k); sea = g.sea_sign(k); m = max(2, int(L / 4.0))
                    for q in range(m + 1):
                        if st and q == 0: continue
                        sv = L * q / m if fwd else L * (1 - q / m)
                        x, z, y, tx, tz = g.at(k, sv)
                        xa, za, _, _, _ = g.at(k, max(sv - 3, 0)); xb, zb, _, _, _ = g.at(k, min(sv + 3, L)); tx, tz = norm(xb - xa, zb - za)
                        nsx, nsz = -tz * sea, tx * sea                                  # normal para o MAR
                        if not fwd: tx, tz = -tx, -tz
                        st.append([x, z, y, tx, tz, nsx, nsz])
                # suaviza as normais (emendas nos cruzamentos) e monta os quadros no eixo do calcadao
                for _ in range(3):
                    for i in range(1, len(st) - 1):
                        st[i][5] = (st[i - 1][5] + 2 * st[i][5] + st[i + 1][5]) / 4; st[i][6] = (st[i - 1][6] + 2 * st[i][6] + st[i + 1][6]) / 4
                fr = []
                for x, z, y, tx, tz, nsx, nsz in st:
                    l = math.hypot(nsx, nsz) or 1; nsx, nsz = nsx / l, nsz / l
                    cx, cz = x + nsx * ORLA_CALC, z + nsz * ORLA_CALC
                    ok = not self.geo.is_water(cx - nsx * (HALF_W + 2), cz - nsz * (HALF_W + 2)) and not self.geo.is_water(cx, cz)
                    fr.append({'x': cx, 'z': cz, 'ax': x, 'az': z, 'tx': -nsz, 'tz': nsx, 'nx': -nsx, 'nz': -nsz, 'yp': y + SW_Y - 0.06, 'ya': y, 'ok': ok, 's': 0.0})
                # tangente coerente com a normal (t x n), e corta trechos sobre a agua
                runs = []; cur = []
                for f in fr:
                    if f['ok']: cur.append(f)
                    else:
                        if len(cur) > 12: runs.append(cur)
                        cur = []
                if len(cur) > 12: runs.append(cur)
                for r in runs:
                    acc = 0.0
                    for i in range(len(r)):
                        if i: acc += math.hypot(r[i]['x'] - r[i - 1]['x'], r[i]['z'] - r[i - 1]['z'])
                        r[i]['s'] = acc
                    out.append(r)
        return out

    def sub_frames(self, fr, a, b):
        return [self.at(fr, a)] + [f for f in fr if a < f['s'] < b] + [self.at(fr, b)]

    def crossings(self, fr):
        """posicoes (s) das faixas de pedestre que atravessam a Av. Beira-Mar e chegam neste trecho de orla"""
        out = []
        for (x, z) in getattr(self.g, 'xw_beach', []):
            best = None
            for k in range(len(fr) - 1):                                      # projecao EXATA do centro da faixa na polilinha da avenida
                ax_, az_, bx_, bz_ = fr[k]['ax'], fr[k]['az'], fr[k + 1]['ax'], fr[k + 1]['az']
                vx, vz = bx_ - ax_, bz_ - az_; L2 = vx * vx + vz * vz
                if L2 < 1e-9: continue
                t = min(max(((x - ax_) * vx + (z - az_) * vz) / L2, 0.0), 1.0)
                d = math.hypot(x - (ax_ + vx * t), z - (az_ + vz * t))
                if best is None or d < best[0]: best = (d, fr[k]['s'] + (fr[k + 1]['s'] - fr[k]['s']) * t)
            if best and best[0] < 3.0: out.append(best[1])
        return sorted(out)

    def parking(self, fr, xr):
        """vagas inclinadas a 60 graus (2,6 m de largura): faixas brancas da guia ate a pista"""
        L = fr[-1]['s']; s = 3.0; nst = 0
        ang = math.radians(60.0); depth = PARK_O1 - (GARDEN_O + 0.2); sh = depth / math.tan(ang); pitch = 2.8 / math.sin(ang)
        while s < L - 3.0 - sh:
            if any(a - 1.0 <= s <= b + 1.0 + sh for a, b in xr): s += pitch; continue
            f0 = self.at(fr, s); f1 = self.at(fr, s + sh)
            p0 = self.P(f0, GARDEN_O + 0.2, -0.07); p1 = self.P(f1, PARK_O1 - 0.1, -0.07)
            dx, dz = p1[0] - p0[0], p1[2] - p0[2]; l = math.hypot(dx, dz) or 1; ox, oz = -dz / l * 0.08, dx / l * 0.08
            self.B.quad(PLAIN, [(p0[0] - ox, p0[1], p0[2] - oz), (p1[0] - ox, p1[1], p1[2] - oz), (p1[0] + ox, p1[1], p1[2] + oz), (p0[0] + ox, p0[1], p0[2] + oz)], (0, 1, 0), COL['stall'], None, True)
            s += pitch; nst += 1
        self.stats['vagas'] = self.stats.get('vagas', 0) + max(nst - 1, 0)

    def landing(self, fr, c):
        """passagem de pedestres: retangulo reto, perpendicular EXATA a avenida no centro da faixa, da faixa ate o calcadao; a ciclovia continua toda vermelha
        com uma travessia zebrada em cima"""
        f = self.at(fr, c)
        k = min(range(len(fr) - 1), key=lambda q: abs(fr[q]['s'] - c))
        tx, tz = fr[min(k + 1, len(fr) - 1)]['ax'] - fr[max(k - 1, 0)]['ax'], fr[min(k + 1, len(fr) - 1)]['az'] - fr[max(k - 1, 0)]['az']
        l = math.hypot(tx, tz) or 1; tx, tz = tx / l, tz / l
        nx_, nz_ = -tz, tx
        if nx_ * (-f['nx']) + nz_ * (-f['nz']) < 0: nx_, nz_ = -nx_, -nz_             # (nx_, nz_) = para o MAR
        ax, az = f['ax'], f['az']; yp = f['yp']; hw = XW_HALF
        def Pt(d, u, dy): return (ax + nx_ * d + tx * u, yp + dy, az + nz_ * d + tz * u)
        d_far = ORLA_CALC - HALF_W; d_ramp = ORLA_CALC - (PARK_O1 - 1.2); d_near = ORLA_CALC - PARK_O1
        self.g.quad(PAVER, [Pt(d_ramp, -hw, 0.10), Pt(d_far, -hw, 0.10), Pt(d_far, hw, 0.10), Pt(d_ramp, hw, 0.10)], COL['wave1'], 'prom')
        self.g.quad(PAVER, [Pt(d_near, -hw, -0.08), Pt(d_ramp, -hw, 0.10), Pt(d_ramp, hw, 0.10), Pt(d_near, hw, -0.08)], COL['wave3'], 'prom')
        # barras brancas (zebra) sobre a ciclovia vermelha (o piso da ciclovia fica a +0,06): 0,5 m de barra a cada 1 m
        nb = int(round(2 * hw))
        for j in range(nb):
            u0 = -hw + 0.25 + j * (2 * hw / nb); u1 = u0 + 0.5
            self.B.quad(PLAIN, [Pt(ORLA_CALC - 7.0, u0, 0.09), Pt(ORLA_CALC - 7.0, u1, 0.09), Pt(ORLA_CALC - 3.0, u1, 0.09), Pt(ORLA_CALC - 3.0, u0, 0.09)], (0, 1, 0), COL['white'], None, True)
        self.items['paths'].append({'x': round(ax + nx_ * d_near, 2), 'z': round(az + nz_ * d_near, 2), 'sx': round(nx_, 3), 'sz': round(nz_, 3), 's': round(c, 1)})

    def end_plaza(self, fr, end, so):
        f = fr[end]; YPf = f['yp']
        tdx, tdz = f['tx'] * so, f['tz'] * so                      # sentido para fora da ponta
        sea = (-f['nx'], -f['nz'])
        def dry(x, z, pad=0.0): return self.sample(x, z) > -0.05 and not self.geo.is_water(x, z)
        Rr = None
        for cand in (13.0, 11.5, 10.0, 8.5, 7.0):
            cx = f['x'] + tdx * cand * 0.85; cz = f['z'] + tdz * cand * 0.85
            ok = all(dry(cx + math.cos(a_ * math.pi / 8) * (cand + 2.5), cz + math.sin(a_ * math.pi / 8) * (cand + 2.5)) for a_ in range(16)) and dry(cx, cz)
            if ok: Rr = cand; break
        if Rr is None:                                              # sem espaco (rio/mar): so um murinho de fechamento
            c4 = [(self.P(f, o, 0, 0.0)[0], self.P(f, o, 0, 0.0)[2]) for o in (-HALF_W - 0.35, GARDEN_O + 0.2)] + [(self.P(f, o, 0, 0.45 * so)[0], self.P(f, o, 0, 0.45 * so)[2]) for o in (GARDEN_O + 0.2, -HALF_W - 0.35)]
            self.B.obox_pts(c4, YPf - 1.6, YPf + 1.0, COL['wall'], STONE, True, False); return
        cx = f['x'] + tdx * Rr * 0.85; cz = f['z'] + tdz * Rr * 0.85
        ring = [(cx + math.cos(a_ * math.pi / 18) * Rr, cz + math.sin(a_ * math.pi / 18) * Rr) for a_ in range(36)]
        ground_lo = min(min(self.sample(x, z) for x, z in ring), self.sample(cx, cz)) - 0.4
        ang_in = math.atan2(-tdz, -tdx); ang_sea = math.atan2(sea[1], sea[0])
        def angdiff(a, b): return abs((a - b + math.pi) % (2 * math.pi) - math.pi)
        # piso: setores de 10 graus em aneis, padrao radial claro/escuro + anel vermelho (continua a ciclovia)
        NSEG = 36
        for k in range(NSEG):
            a0 = 2 * math.pi * k / NSEG; a1 = 2 * math.pi * (k + 1) / NSEG
            for (r0, r1, kind) in ((2.7, Rr - 3.2, 'pizza'), (Rr - 3.2, Rr - 2.2, 'red'), (Rr - 2.2, Rr, 'edge')):
                col = (COL['wave1'] if k % 2 == 0 else COL['wave3']) if kind == 'pizza' else (COL['bike'] if kind == 'red' else COL['wave1'])
                q = [(cx + math.cos(a0) * r0, YPf + 0.06, cz + math.sin(a0) * r0), (cx + math.cos(a0) * r1, YPf + 0.06, cz + math.sin(a0) * r1),
                     (cx + math.cos(a1) * r1, YPf + 0.06, cz + math.sin(a1) * r1), (cx + math.cos(a1) * r0, YPf + 0.06, cz + math.sin(a1) * r0)]
                self.g.quad(PAVER, q, col, 'bike' if kind == 'red' else 'prom')
        # laje: tampa e saia ate o terreno
        for k in range(NSEG):
            a0 = 2 * math.pi * k / NSEG; a1 = 2 * math.pi * (k + 1) / NSEG; am = (a0 + a1) / 2
            p0 = (cx + math.cos(a0) * Rr, cz + math.sin(a0) * Rr); p1 = (cx + math.cos(a1) * Rr, cz + math.sin(a1) * Rr)
            in_open = angdiff(am, ang_in) < math.radians(42); in_sea = angdiff(am, ang_sea) < math.radians(15)
            self.B.quad(STONE, [(p0[0], ground_lo, p0[1]), (p1[0], ground_lo, p1[1]), (p1[0], YPf + 0.06, p1[1]), (p0[0], YPf + 0.06, p0[1])], (math.cos(am), 0, math.sin(am)), COL['wall'], None, True)
            if not in_open and not in_sea:            # murinho de contorno (0,95 m) com tampa
                q0 = (cx + math.cos(a0) * (Rr - 0.35), cz + math.sin(a0) * (Rr - 0.35)); q1 = (cx + math.cos(a1) * (Rr - 0.35), cz + math.sin(a1) * (Rr - 0.35))
                self.B.quad(STONE, [(p0[0], YPf + 0.06, p0[1]), (p1[0], YPf + 0.06, p1[1]), (p1[0], YPf + 1.0, p1[1]), (p0[0], YPf + 1.0, p0[1])], (math.cos(am), 0, math.sin(am)), COL['wall2'], None, True)
                self.B.quad(STONE, [(q0[0], YPf + 0.06, q0[1]), (q1[0], YPf + 0.06, q1[1]), (q1[0], YPf + 1.0, q1[1]), (q0[0], YPf + 1.0, q0[1])], (-math.cos(am), 0, -math.sin(am)), COL['wall2'], None, True)
                self.B.quad(STONE, [(q0[0], YPf + 1.0, q0[1]), (q1[0], YPf + 1.0, q1[1]), (p1[0], YPf + 1.0, p1[1]), (p0[0], YPf + 1.0, p0[1])], (0, 1, 0), COL['wall'], None, True)
        self.polys.append(('prom', ring))
        # escada para a areia no lado do mar (4,6 m de largura)
        sx_, sz_ = math.cos(ang_sea), math.sin(ang_sea); rx_, rz_ = -sz_, sx_
        base = (cx + sx_ * Rr, cz + sz_ * Rr); yb = max(self.sample(base[0] + sx_ * 2.6, base[1] + sz_ * 2.6), 0.2)
        n = max(3, int(round((YPf + 0.06 - yb) / 0.15))); rise = (YPf + 0.06 - yb) / n; tread = 0.34; W = 4.6
        for i in range(n):
            yt = YPf + 0.06 - (i + 1) * rise
            c0 = (base[0] + sx_ * i * tread - rx_ * W / 2, base[1] + sz_ * i * tread - rz_ * W / 2); c1 = (base[0] + sx_ * (i + 1) * tread - rx_ * W / 2, base[1] + sz_ * (i + 1) * tread - rz_ * W / 2)
            c2 = (c1[0] + rx_ * W, c1[1] + rz_ * W); c3 = (c0[0] + rx_ * W, c0[1] + rz_ * W)
            self.g.quad(PAVER, [(c0[0], yt + 0.01, c0[1]), (c1[0], yt + 0.01, c1[1]), (c2[0], yt + 0.01, c2[1]), (c3[0], yt + 0.01, c3[1])], COL['step'] if i % 2 == 0 else COL['step2'], None)
            self.B.quad(PLAIN, [(c0[0], yt + rise, c0[1]), (c3[0], yt + rise, c3[1]), (c3[0], yt, c3[1]), (c0[0], yt, c0[1])], (-sx_, 0, -sz_), COL['step2'], None, True)
        for sg in (-1, 1):
            px, pz = base[0] + rx_ * sg * (W / 2 + 0.05), base[1] + rz_ * sg * (W / 2 + 0.05)
            for i in range(0, n + 1, 3): self.B.cyl(px + sx_ * i * tread, pz + sz_ * i * tread, 0.04, YPf + 0.06 - i * rise, YPf + 0.06 - i * rise + 1.0, COL['iron'], 6)
        for sg in (-1, 1):
            self.cheek(base[0] - sx_ * 0.4, base[1] - sz_ * 0.4, sx_, sz_, n * tread + 1.2, sg * (W / 2 + 0.55), YPf + 0.55, yb + 0.55, min(yb, YPf - 1.5) - 0.8)
        self.items['stairs'].append({'x': round(base[0], 2), 'z': round(base[1], 2), 'dx': round(sx_, 3), 'dz': round(sz_, 3), 'steps': n, 'w': W, 'top': YPf, 'plaza': True})
        self.stats['stairs'] += 1
        # fonte central
        self.B.cyl(cx, cz, 2.6, YPf + 0.06, YPf + 0.62, COL['wall'], 28, STONE, False)
        self.B.cyl(cx, cz, 2.6, YPf + 0.62, YPf + 0.66, COL['wall2'], 28, STONE, True, 2.2)
        for k in range(24):
            a0 = 2 * math.pi * k / 24; a1 = 2 * math.pi * (k + 1) / 24
            self.B.tri(PLAIN, (cx, YPf + 0.5, cz), (cx + math.cos(a0) * 2.2, YPf + 0.5, cz + math.sin(a0) * 2.2), (cx + math.cos(a1) * 2.2, YPf + 0.5, cz + math.sin(a1) * 2.2), (0, 1, 0), COL['water'], None, True)
        self.B.cyl(cx, cz, 0.45, YPf + 0.5, YPf + 1.3, COL['wall'], 12, STONE, True)
        self.B.cyl(cx, cz, 0.08, YPf + 1.3, YPf + 3.0, rgb('#CFE9F5'), 8, PLAIN, True, 0.03)
        self.B.cyl(cx, cz, 0.55, YPf + 3.0, YPf + 3.06, rgb('#CFE9F5'), 12, PLAIN, True)
        # bancos virados para o centro, postes e palmeiras em canteiros redondos
        for k in range(12):
            a_ = 2 * math.pi * k / 12 + math.pi / 12
            if angdiff(a_, ang_in) < math.radians(42) or angdiff(a_, ang_sea) < math.radians(30): continue
            rr = Rr - 4.4; bx, bz = cx + math.cos(a_) * rr, cz + math.sin(a_) * rr
            tt = (-math.sin(a_), math.cos(a_)); nn = (math.cos(a_), math.sin(a_))
            c4 = [(bx - tt[0] * 0.9 - nn[0] * 0.25, bz - tt[1] * 0.9 - nn[1] * 0.25), (bx + tt[0] * 0.9 - nn[0] * 0.25, bz + tt[1] * 0.9 - nn[1] * 0.25), (bx + tt[0] * 0.9 + nn[0] * 0.25, bz + tt[1] * 0.9 + nn[1] * 0.25), (bx - tt[0] * 0.9 + nn[0] * 0.25, bz - tt[1] * 0.9 + nn[1] * 0.25)]
            self.B.obox_pts(c4, YPf + 0.5, YPf + 0.62, COL['bench'], WOOD, True, False)
            for sg in (-1, 1): self.B.box(bx + tt[0] * 0.7 * sg, bz + tt[1] * 0.7 * sg, 0.15, 0.4, YPf + 0.06, YPf + 0.5, COL['iron'], PLAIN, True, False)
            self.items['benches'].append({'x': round(bx, 2), 'z': round(bz, 2), 'nx': round(-nn[0], 3), 'nz': round(-nn[1], 3)})
        for k in range(8):
            a_ = 2 * math.pi * k / 8 + math.pi / 8
            if angdiff(a_, ang_in) < math.radians(40) or angdiff(a_, ang_sea) < math.radians(30): continue
            px, pz = cx + math.cos(a_) * (Rr - 1.1), cz + math.sin(a_) * (Rr - 1.1)
            if k % 2 == 0:
                self.B.cyl(px, pz, 0.08, YPf + 0.06, YPf + 4.6, COL['lamp'], 8); self.B.box(px, pz, 0.7, 0.3, YPf + 4.5, YPf + 4.7, rgb('#FFF0B8'), PLAIN, True, False)
                self.items['lamps'].append({'x': round(px, 2), 'z': round(pz, 2), 'y': YPf + 0.06})
            else:
                self.palm_at(px, pz, YPf + 0.3, 1.0)
                self.items['palms'].append({'x': round(px, 2), 'z': round(pz, 2), 'y': YPf + 0.5, 'sp': 'palmeira', 'scale': 1.0, 'baked': True})
        self.items.setdefault('plazas', []).append({'x': round(cx, 2), 'z': round(cz, 2), 'r': Rr, 'y': round(YPf, 2)})

    # ---------------------------------------------------------- construcao por segmento
    def build_line(self, fr, idx):
        if len(fr) < 10: return
        L = fr[-1]['s']; self.stats['prom_m'] += L
        # posicoes de escada / pier
        stairs = []; s = 45.0
        while s < L - 30: stairs.append(s); s += 92.0 + self.rnd.uniform(-8, 8)
        piers = []
        if L > 500: piers.append(L * (0.42 if idx % 2 == 0 else 0.55))
        if L > 1300: piers = [L * 0.27, L * 0.72]
        gaps = [(s_ - 3.4, s_ + 3.4) for s_ in stairs] + [(p_ - 4.8, p_ + 4.8) for p_ in piers]
        # --- piso com ondas: 7 faixas de 2 m, fase deslocada com a distancia (dai o desenho de onda)
        nb = 7
        for b in range(nb):
            o0 = -HALF_W + 2.0 * b; o1 = o0 + 2.0
            for k in range(len(fr) - 1):
                a_, b_ = fr[k], fr[k + 1]
                ph = math.sin((a_['s'] + b * 3.5) / 7.0) > 0
                col = COL['wave1'] if (ph and b % 2 == 0) or (not ph and b % 2 == 1) else (COL['wave2'] if b % 3 == 0 else COL['wave3'])
                if b in (5, 6): col = COL['bike']
                q = [self.P(a_, o0, 0.06), self.P(b_, o0, 0.06), self.P(b_, o1, 0.06), self.P(a_, o1, 0.06)]
                self.g.quad(PAVER, q, col, 'bike' if b in (5, 6) else ('prom2' if col == COL['wave2'] else 'prom'))
        # ciclovia de MAO DUPLA (3..7 m, tudo vermelho): linhas de borda, tracejado central e setas de sentido
        self.strip(fr, 3.0 - 0.07, 3.0 + 0.07, 0.08, PLAIN, COL['white'], None)
        self.strip(fr, 7.0 - 0.07, 7.0 + 0.07, 0.08, PLAIN, COL['white'], None)
        Lc = fr[-1]['s']; sd = 1.0
        while sd < Lc - 3.0:
            f0 = self.at(fr, sd); f1 = self.at(fr, min(sd + 2.0, Lc))
            self.B.quad(PLAIN, [self.P(f0, 5.0 - 0.06, 0.085), self.P(f1, 5.0 - 0.06, 0.085), self.P(f1, 5.0 + 0.06, 0.085), self.P(f0, 5.0 + 0.06, 0.085)], (0, 1, 0), COL['white'], None, True)
            sd += 5.0
        sd = 22.0
        while sd < Lc - 10.0:
            for o_, dr in ((4.0, 1.0), (6.0, -1.0)):                      # faixa interna +s, faixa externa -s
                f = self.at(fr, sd); st_ = -1.1 * dr; en_ = 0.3 * dr; hd = 1.2 * dr
                Pq = lambda so, oo: self.P(f, o_ + oo, 0.085, so)
                self.B.quad(PLAIN, [Pq(st_, -0.07), Pq(en_, -0.07), Pq(en_, 0.07), Pq(st_, 0.07)], (0, 1, 0), COL['white'], None, True)
                self.B.tri(PLAIN, Pq(en_, -0.4), Pq(en_ + hd, 0.0), Pq(en_, 0.4), (0, 1, 0), COL['white'], None, True)
            sd += 55.0
        # --- jardim de palmeiras entre o calcadao e as vagas (mesmo nivel do calcadao) + guia + VAGAS a 60 graus junto a avenida
        xs = self.crossings(fr)
        xr = [(c - XW_HALF, c + XW_HALF) for c in xs]
        # calcada de pedestres (concreto claro) entre a ciclovia e as vagas, guia e piso das vagas (continuos; a passagem fica por cima)
        self.strip(fr, HALF_W, GARDEN_O, 0.05, PAVER, COL['wave3'], 'prom')
        self.strip(fr, GARDEN_O, GARDEN_O + 0.2, 0.06, PAVER, COL['curbP'], 'curb')
        self.vwall(fr, GARDEN_O + 0.2, -0.115, 0.06, COL['curbP'], 1, PLAIN)
        self.strip(fr, GARDEN_O + 0.2, PARK_O1 + 0.35, -0.115, PAVER, COL['bay'], 'bay')
        self.parking(fr, xr)
        # travessias: patamar elevado do asfalto ate o calcadao (rampa acessivel), sem vagas
        for c in xs: self.landing(fr, c)
        # --- muro de contencao/balaustrada do lado do mar, com vaos nas escadas e nos piers
        self.vwall(fr, -HALF_W, -1.5, 0.98, COL['wall'], -1, STONE, gaps)
        self.vwall(fr, -HALF_W - 0.35, 0.0, 0.98, COL['wall2'], 1, STONE, gaps)
        for k in range(len(fr) - 1):
            a_, b_ = fr[k], fr[k + 1]
            if any(g0 <= a_['s'] <= g1 or g0 <= b_['s'] <= g1 for g0, g1 in gaps): continue
            q = [self.P(a_, -HALF_W - 0.35, 0.98), self.P(b_, -HALF_W - 0.35, 0.98), self.P(b_, -HALF_W + 0.05, 0.98), self.P(a_, -HALF_W + 0.05, 0.98)]
            self.B.quad(STONE, q, (0, 1, 0), COL['wall'], None, True); self.stats['wall_m'] += 4.0
            self.polys.append(('wall', [(p[0], p[2]) for p in q]))
        # --- pontas do calcadao: praca-mirante circular (fonte, bancos, palmeiras, postes, escada para a areia)
        for end, so in ((0, -1.0), (len(fr) - 1, 1.0)):
            self.end_plaza(fr, end, so)
        # --- escadas
        for s_ in stairs: self.stairs(fr, s_)
        # --- piers
        for s_ in piers: self.pier(fr, s_)
        # --- mobiliario: palmeiras, postes, bancos, lixeiras
        gp = gaps
        fpoles = getattr(self.g, 'fu_poles', [])
        def near_pole(s_, o_):
            f_ = self.at(fr, s_); x_, z_ = f_['x'] + f_['nx'] * o_, f_['z'] + f_['nz'] * o_
            return any(abs(px - x_) < 2.6 and abs(pz - z_) < 2.6 and math.hypot(px - x_, pz - z_) < 2.6 for px, pz in fpoles)
        def in_gap(s_, pad=0.0):
            if any(g0 - pad <= s_ <= g1 + pad for g0, g1 in gp): return True
            return any(abs(s_ - c) < XW_HALF + 1.0 + pad for c in xs)
        s_ = 6.0; palm_s = []
        while s_ < L - 4:
            f = self.at(fr, s_)
            if not in_gap(s_, 3.5) and not near_pole(s_, 8.3): self.palm(f, 8.3); palm_s.append(s_)
            s_ += 18.0
        s_ = 12.0; alt = 1
        while s_ < L - 4:
            f = self.at(fr, s_)
            if not in_gap(s_, 2.0) and all(abs(s_ - pp) > 3.0 for pp in palm_s) and not near_pole(s_, 9.0 if alt > 0 else -HALF_W + 0.9):
                self.lamp(f, 9.0 if alt > 0 else -HALF_W + 0.9); alt = -alt
            s_ += 26.0
        s_ = 30.0
        while s_ < L - 4:
            f = self.at(fr, s_)
            if not in_gap(s_, 3.0): self.bench(f, -HALF_W + 1.6)
            s_ += 42.0
        # --- areia: quiosques, salva-vidas, redes de volei, chuveiros, guarda-sois
        s_ = 70.0
        while s_ < L - 40:
            if not in_gap(s_, 8.0): self.kiosk(self.at(fr, s_), -HALF_W - 9.0, idx)
            s_ += 148.0
        s_ = 110.0
        while s_ < L - 40:
            if not in_gap(s_, 8.0): self.tower(self.at(fr, s_), -HALF_W - 30.0)
            s_ += 236.0
        s_ = 175.0
        while s_ < L - 50:
            if not in_gap(s_, 8.0): self.court(self.at(fr, s_), -HALF_W - 26.0)
            s_ += 205.0
        for s_ in stairs: self.shower(self.at(fr, s_ + 5.5), -HALF_W - 6.0)
        # guarda-sois em manchas
        for _ in range(int(L / 5)):
            s_ = self.rnd.uniform(10, L - 10); f = self.at(fr, s_); o = -HALF_W - self.rnd.uniform(12, 46)
            if not in_gap(s_, 5.0): self.umbrella(f, o)
        # --- acessos da avenida ao calcadao (calcada cruzando a faixa de palmeiras) onde ha rua em T
        self.frames_all.append(fr)

    def at(self, fr, s):
        lo, hi = 0, len(fr) - 1
        while hi - lo > 1:
            m = (lo + hi) // 2
            if fr[m]['s'] <= s: lo = m
            else: hi = m
        a, b = fr[lo], fr[hi]; t = (s - a['s']) / max(b['s'] - a['s'], 1e-6)
        f = {k: a[k] + (b[k] - a[k]) * t for k in ('x', 'z', 'tx', 'tz', 'nx', 'nz', 's', 'yp', 'ax', 'az')}
        l = math.hypot(f['tx'], f['tz']) or 1; f['tx'] /= l; f['tz'] /= l; l = math.hypot(f['nx'], f['nz']) or 1; f['nx'] /= l; f['nz'] /= l
        return f

    # ---------------------------------------------------------- objetos
    def groundy(self, x, z): return max(0.0, self.sample(x, z))

    def sample(self, x, z):
        import terrain_final as T
        return T.sample8(self.hf, x, z)

    def cheek(self, x0, z0, dx, dz, run, lat, ytop0, ytop1, ybot, th=0.4):
        """muro lateral inclinado ao lado de uma escada: comeca em (x0,z0) e segue (dx,dz) por `run` m; `lat` = deslocamento lateral do eixo"""
        rx, rz = -dz, dx
        ax, az = x0 + rx * lat, z0 + rz * lat
        bx, bz = ax + dx * run, az + dz * run
        P = lambda x, z, o: (x + rx * o, z + rz * o)
        for o_in, o_out, nrm in ((-th / 2, th / 2, 1.0),):
            a_i, a_o = P(ax, az, -th / 2), P(ax, az, th / 2); b_i, b_o = P(bx, bz, -th / 2), P(bx, bz, th / 2)
            self.B.quad(STONE, [(a_o[0], ybot, a_o[1]), (b_o[0], ybot, b_o[1]), (b_o[0], ytop1, b_o[1]), (a_o[0], ytop0, a_o[1])], (rx, 0, rz), COL['wall'], None, True)
            self.B.quad(STONE, [(b_i[0], ybot, b_i[1]), (a_i[0], ybot, a_i[1]), (a_i[0], ytop0, a_i[1]), (b_i[0], ytop1, b_i[1])], (-rx, 0, -rz), COL['wall'], None, True)
            self.B.quad(STONE, [(a_i[0], ytop0, a_i[1]), (a_o[0], ytop0, a_o[1]), (b_o[0], ytop1, b_o[1]), (b_i[0], ytop1, b_i[1])], (0, 1, 0), COL['wall2'], None, True)
            self.B.quad(STONE, [(b_i[0], ybot, b_i[1]), (b_o[0], ybot, b_o[1]), (b_o[0], ytop1, b_o[1]), (b_i[0], ytop1, b_i[1])], (dx, 0, dz), COL['wall'], None, True)
            self.B.quad(STONE, [(a_o[0], ybot, a_o[1]), (a_i[0], ybot, a_i[1]), (a_i[0], ytop0, a_i[1]), (a_o[0], ytop0, a_o[1])], (-dx, 0, -dz), COL['wall'], None, True)

    def stairs(self, fr_, s0):
        f = self.at(fr_, s0); YPf = f['yp']; W = 6.0; rise = 0.14
        x0, z0 = f['x'] + f['nx'] * (-HALF_W), f['z'] + f['nz'] * (-HALF_W)       # topo, na borda do mar do calcadao
        sx, sz = -f['nx'], -f['nz']                                                # sentido de descida (para o mar)
        yb = self.sample(x0 + sx * 3.4, z0 + sz * 3.4)
        n = max(3, int(round((YPf - yb) / rise))); rise = (YPf - yb) / n; tread = 0.32
        for i in range(n):
            yt = YPf - (i + 1) * rise
            c0 = (x0 + sx * (i * tread) - f['tx'] * W / 2, z0 + sz * (i * tread) - f['tz'] * W / 2); c1 = (x0 + sx * ((i + 1) * tread) - f['tx'] * W / 2, z0 + sz * ((i + 1) * tread) - f['tz'] * W / 2)
            c2 = (c1[0] + f['tx'] * W, c1[1] + f['tz'] * W); c3 = (c0[0] + f['tx'] * W, c0[1] + f['tz'] * W)
            col = COL['step'] if i % 2 == 0 else COL['step2']
            self.g.quad(PAVER, [(c0[0], yt + 0.01, c0[1]), (c1[0], yt + 0.01, c1[1]), (c2[0], yt + 0.01, c2[1]), (c3[0], yt + 0.01, c3[1])], col, None)
            # espelho
            self.B.quad(PLAIN, [(c0[0], yt + rise, c0[1]), (c3[0], yt + rise, c3[1]), (c3[0], yt, c3[1]), (c0[0], yt, c0[1])], (-sx, 0, -sz), COL['step2'], None, True)
            self.polys.append(('stairs', [c0, c1, c2, c3]))
        # corrimaos (dois lados + central) e muretas laterais
        for sg in (-1, 1):
            px, pz = x0 - f['tx'] * (W / 2 + 0.05) * (-sg), z0 - f['tz'] * (W / 2 + 0.05) * (-sg)
            for i in range(0, n + 1, 3):
                self.B.cyl(px + sx * i * tread, pz + sz * i * tread, 0.04, YPf - i * rise, YPf - i * rise + 1.0, COL['iron'], 6)
            self.B.quad(PLAIN, [(px, YPf + 0.95, pz), (px + sx * n * tread, YPf - n * rise + 0.95, pz + sz * n * tread), (px + sx * n * tread, YPf - n * rise + 1.02, pz + sz * n * tread), (px, YPf + 1.02, pz)], (-f['nx'] * 0 + f['tx'] * sg, 0, f['tz'] * sg), COL['iron'], None, True)
        # muros laterais da escada (cobrem a quina do calcadao e o talude de terreno ao lado)
        for sg in (-1, 1):
            self.cheek(x0, z0, sx, sz, n * tread + 0.9, sg * (W / 2 + 0.55), YPf + 0.55, yb + 0.55, min(yb, YPf - 1.5) - 0.8)
        self.items['stairs'].append({'x': round(x0, 2), 'z': round(z0, 2), 'dx': round(sx, 3), 'dz': round(sz, 3), 'steps': n, 'w': W, 'top': YPf})
        self.stats['stairs'] += 1

    def pier(self, fr_, s0):
        f = self.at(fr_, s0); YPf = f['yp']; sx, sz = -f['nx'], -f['nz']                           # do calcadao para o mar
        x0, z0 = f['x'] + f['nx'] * (-HALF_W - 0.3), f['z'] + f['nz'] * (-HALF_W - 0.3)
        W = 7.0; deck = YPf + 0.55
        # comprimento ate encontrar agua >= 3,5 m + 20 m
        Lp = 0.0
        while Lp < 220:
            d = -self.sample(x0 + sx * Lp, z0 + sz * Lp)
            if d > 3.5 and Lp > 70: break
            Lp += 4.0
        Lp = max(110.0, Lp + 24.0)
        rx, rz = -sz, sx                                       # lateral do pier
        def PP(a, b, y): return (x0 + sx * a + rx * b, y, z0 + sz * a + rz * b)
        TH = 0.42                                              # espessura do deck (fachada de madeira) - nao e mais uma folha de papel
        n = int(Lp / 3.0)
        def slab(a0, a1, b0, b1, col, top_col=None):
            self.B.obox_pts([PP(a0, b0, 0)[0::2], PP(a1, b0, 0)[0::2], PP(a1, b1, 0)[0::2], PP(a0, b1, 0)[0::2]], deck - TH, deck, col, WOOD, True, True, 0.5)
        for i in range(n):
            a0, a1 = i * 3.0, (i + 1) * 3.0
            # tres tabuas longitudinais largas, tons proximos (sem xadrez) + juntas finas transversais a cada 0,6 m
            for k in range(3):
                b0, b1 = -W / 2 + k * (W / 3), -W / 2 + (k + 1) * (W / 3)
                self.B.obox_pts([PP(a0, b0, 0)[0::2], PP(a1, b0, 0)[0::2], PP(a1, b1, 0)[0::2], PP(a0, b1, 0)[0::2]], deck - TH, deck, COL['wood'] if k != 1 else rgb('#977650'), WOOD, True, False, 0.5)
            for j in range(1, 5):
                aj = a0 + j * 0.6
                self.B.quad(PLAIN, [PP(aj - 0.02, -W / 2, deck + 0.004), PP(aj + 0.02, -W / 2, deck + 0.004), PP(aj + 0.02, W / 2, deck + 0.004), PP(aj - 0.02, W / 2, deck + 0.004)], (0, 1, 0), COL['wood2'], None, True)
            self.polys.append(('pier', [(PP(a0, -W / 2, 0)[0], PP(a0, -W / 2, 0)[2]), (PP(a1, -W / 2, 0)[0], PP(a1, -W / 2, 0)[2]), (PP(a1, W / 2, 0)[0], PP(a1, W / 2, 0)[2]), (PP(a0, W / 2, 0)[0], PP(a0, W / 2, 0)[2])]))
            # travessa sob o deck + par de estacas de madeira ate o fundo
            self.B.obox_pts([PP(a0 + 1.2, -W / 2 - 0.25, 0)[0::2], PP(a0 + 1.5, -W / 2 - 0.25, 0)[0::2], PP(a0 + 1.5, W / 2 + 0.25, 0)[0::2], PP(a0 + 1.2, W / 2 + 0.25, 0)[0::2]], deck - TH - 0.38, deck - TH, COL['wood2'], WOOD, False, False, 0.5)
            for sg in (-1, 1):
                px, pz = PP(a0 + 1.35, sg * (W / 2 - 0.2), 0)[0], PP(a0 + 1.35, sg * (W / 2 - 0.2), 0)[2]
                bot = min(self.sample(px, pz), -0.5) - 1.2
                self.B.box(px, pz, 0.42, 0.42, bot, deck - TH, COL['wood2'], WOOD, False, False, 0.5)
            # guarda-corpo: poste a cada 3 m + corrimao superior e intermediario
            for sg in (-1, 1):
                px, pz = PP(a0, sg * (W / 2 - 0.1), 0)[0], PP(a0, sg * (W / 2 - 0.1), 0)[2]
                self.B.box(px, pz, 0.12, 0.12, deck, deck + 1.05, COL['rail'], METAL, True, False)
                scenery.bar(self.B, PP(a0, sg * (W / 2 - 0.1), deck + 1.02), PP(a1, sg * (W / 2 - 0.1), deck + 1.02), 0.05, COL['rail'], METAL)
                scenery.bar(self.B, PP(a0, sg * (W / 2 - 0.1), deck + 0.55), PP(a1, sg * (W / 2 - 0.1), deck + 0.55), 0.03, COL['rail'], METAL)
        # luminarias e bancos
        for i in range(1, int(Lp / 22) + 1):
            a = i * 22.0
            for sg in (-1, 1):
                px, pz = PP(a, sg * (W / 2 - 0.3), 0)[0], PP(a, sg * (W / 2 - 0.3), 0)[2]
                self.B.cyl(px, pz, 0.07, deck, deck + 4.2, COL['lamp'], 8); self.B.box(px, pz, 0.5, 0.5, deck + 4.1, deck + 4.3, rgb('#FFF0B8'), PLAIN, True, False)
                self.items['lamps'].append({'x': round(px, 2), 'z': round(pz, 2), 'y': deck, 'pier': True})
        for i in range(1, int(Lp / 34) + 1):
            a = i * 34.0 + 5
            bx, bz = PP(a, W / 2 - 0.9, 0)[0], PP(a, W / 2 - 0.9, 0)[2]
            self.B.box(bx, bz, 1.5, 0.5, deck + 0.35, deck + 0.50, COL['bench'], WOOD, True, False); self.B.box(bx, bz, 0.3, 0.3, deck, deck + 0.35, COL['iron'], PLAIN, True, False)
        # plataforma do fim (22 x 16) com gazebo, tambem espessa
        a0, a1 = Lp, Lp + 16.0
        for j in range(8):
            for k in range(3):
                bb0, bb1 = -11 + k * 7.33, -11 + (k + 1) * 7.33
                self.B.obox_pts([PP(a0 + j * 2.0, bb0, 0)[0::2], PP(a0 + (j + 1) * 2.0, bb0, 0)[0::2], PP(a0 + (j + 1) * 2.0, bb1, 0)[0::2], PP(a0 + j * 2.0, bb1, 0)[0::2]], deck - TH, deck, COL['wood'] if (k % 2 == 0) else rgb('#977650'), WOOD, True, False, 0.5)
        self.polys.append(('pier', [(PP(a0, -11, 0)[0], PP(a0, -11, 0)[2]), (PP(a1, -11, 0)[0], PP(a1, -11, 0)[2]), (PP(a1, 11, 0)[0], PP(a1, 11, 0)[2]), (PP(a0, 11, 0)[0], PP(a0, 11, 0)[2])]))
        for aa in (a0 + 1.0, a0 + 8.0, a1 - 1.0):
            for bb in (-10.0, -3.5, 3.5, 10.0):
                px, pz = PP(aa, bb, 0)[0], PP(aa, bb, 0)[2]; bot = min(self.sample(px, pz), -0.5) - 1.2
                self.B.box(px, pz, 0.5, 0.5, bot, deck - TH, COL['wood2'], WOOD, False, False, 0.5)
        for (aa, sgb) in ((a0, 1), (a1, 1)):
            for sg in (-1, 1):
                scenery.bar(self.B, PP(aa, sg * 10.95, deck + 1.02), PP(aa, 0, deck + 1.02) if False else PP(aa, sg * 4.0, deck + 1.02), 0.05, COL['rail'], METAL)
        for sg in (-1, 1):
            scenery.bar(self.B, PP(a0, sg * 10.95, deck + 1.02), PP(a1, sg * 10.95, deck + 1.02), 0.05, COL['rail'], METAL)
            scenery.bar(self.B, PP(a1, sg * 10.95, deck + 1.02), PP(a1, sg * 3.0, deck + 1.02), 0.05, COL['rail'], METAL)
        cx, cz = PP(a0 + 8.0, 0, 0)[0], PP(a0 + 8.0, 0, 0)[2]
        for sgx in (-1, 1):
            for sgz in (-1, 1): self.B.cyl(cx + sgx * 3.2, cz + sgz * 3.2, 0.12, deck, deck + 3.2, COL['rail'], 8)
        for q in range(4):          # telhado piramidal do gazebo
            ang0 = math.pi / 4 + q * math.pi / 2; ang1 = ang0 + math.pi / 2
            P0 = (cx + math.cos(ang0) * 4.2, deck + 3.1, cz + math.sin(ang0) * 4.2); P1 = (cx + math.cos(ang1) * 4.2, deck + 3.1, cz + math.sin(ang1) * 4.2); top = (cx, deck + 5.0, cz)
            nn = (math.cos((ang0 + ang1) / 2), 0.6, math.sin((ang0 + ang1) / 2))
            self.B.tri(ROOF, P0, P1, top, nn, COL['roof'], None, True); self.B.tri(ROOF, P0, P1, top, (-nn[0], -0.6, -nn[2]), COL['wood2'], None, True)
        # rampa de entrada (do calcadao ao deck): 6 m, com espessura
        for i in range(6):
            y0 = YPf + 0.06 + (deck - YPf - 0.06) * i / 6.0; y1 = YPf + 0.06 + (deck - YPf - 0.06) * (i + 1) / 6.0
            A0, A1 = -6 + i, -6 + i + 1
            self.g.quad(WOOD, [PP(A0, -W / 2, y0), PP(A1, -W / 2, y1), PP(A1, W / 2, y1), PP(A0, W / 2, y0)], COL['wood'], None)
            for sg in (-1, 1):
                self.B.quad(WOOD, [PP(A0, sg * W / 2, y0 - TH), PP(A1, sg * W / 2, y1 - TH), PP(A1, sg * W / 2, y1), PP(A0, sg * W / 2, y0)], (rx * sg, 0, rz * sg), COL['wood2'], None, True)
        self.items['piers'].append({'x': round(x0, 2), 'z': round(z0, 2), 'dx': round(sx, 3), 'dz': round(sz, 3), 'len': round(Lp + 16.0, 1), 'w': W, 'deck': round(deck, 2)})
        self.stats['piers'] += 1

    def palm(self, f, o):
        YPf = f['yp']
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o
        sc = self.rnd.uniform(0.9, 1.2)
        self.palm_at(x, z, YPf + 0.18, sc)
        self.items['palms'].append({'x': round(x, 2), 'z': round(z, 2), 'y': YPf + 0.1, 'sp': 'palmeira', 'scale': round(sc, 2), 'baked': True})

    def palm_at(self, x, z, y0, sc=1.0):
        """canteiro redondo + palmeira (tronco levemente curvo em 6 trechos + 11 folhas arqueadas) ja no mesh"""
        self.B.cyl(x, z, 0.75, y0 - 0.18, y0 + 0.02, COL['wall'], 9, STONE, True)
        self.B.cyl(x, z, 0.62, y0 + 0.02, y0 + 0.07, rgb('#5A4632'), 9, PLAIN, True)
        ang = self.rnd.uniform(0, 6.283); lean = self.rnd.uniform(0.25, 0.55) * sc; H = 7.0 * sc
        px, py, pz = x, y0, z
        n = 4
        for k in range(n):
            t0 = k / n; t1 = (k + 1) / n
            x0_, z0_ = x + math.cos(ang) * lean * t0 * t0 * 3.0, z + math.sin(ang) * lean * t0 * t0 * 3.0
            x1_, z1_ = x + math.cos(ang) * lean * t1 * t1 * 3.0, z + math.sin(ang) * lean * t1 * t1 * 3.0
            r0 = 0.22 * sc * (1 - 0.35 * t0); r1 = 0.22 * sc * (1 - 0.35 * t1)
            for q in range(5):
                a0 = 2 * math.pi * q / 5; a1 = 2 * math.pi * (q + 1) / 5; am = (a0 + a1) / 2
                col = COL['trunk'] if (k % 2 == 0) else rgb('#6A4C30')
                self.B.quad(WOOD, [(x0_ + math.cos(a0) * r0, y0 + H * t0, z0_ + math.sin(a0) * r0), (x0_ + math.cos(a1) * r0, y0 + H * t0, z0_ + math.sin(a1) * r0),
                                   (x1_ + math.cos(a1) * r1, y0 + H * t1, z1_ + math.sin(a1) * r1), (x1_ + math.cos(a0) * r1, y0 + H * t1, z1_ + math.sin(a0) * r1)], (math.cos(am), 0, math.sin(am)), col, None, True)
            px, py, pz = x1_, y0 + H * t1, z1_
        for q in range(9):                                      # folhas: faixa arqueada de 2 segmentos, dupla face
            a_ = 2 * math.pi * q / 9 + self.rnd.uniform(-0.15, 0.15); L = 3.1 * sc * self.rnd.uniform(0.85, 1.1)
            cx, cz = math.cos(a_), math.sin(a_); sx_, sz_ = -cz, cx; w = 0.55 * sc
            pts = []
            for u in range(3):
                tt = u / 2.0
                pts.append((px + cx * L * tt, py + 0.55 * math.sin(math.pi * tt * 0.9) * sc - 0.5 * L * tt * tt * 0.55, pz + cz * L * tt, w * (1 - 0.75 * tt)))
            col = rgb('#3F8F3A') if q % 2 == 0 else rgb('#4FA044')
            for u in range(2):
                A, Bp = pts[u], pts[u + 1]
                quad = [(A[0] - sx_ * A[3], A[1], A[2] - sz_ * A[3]), (A[0] + sx_ * A[3], A[1], A[2] + sz_ * A[3]), (Bp[0] + sx_ * Bp[3], Bp[1], Bp[2] + sz_ * Bp[3]), (Bp[0] - sx_ * Bp[3], Bp[1], Bp[2] - sz_ * Bp[3])]
                self.B.quad(PLAIN, quad, (0, 1, 0), col, None, True); self.B.quad(PLAIN, quad[::-1], (0, -1, 0), rgb('#2F7A2F'), None, True)

    def lamp(self, f, o):
        YPf = f['yp']
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o
        self.B.cyl(x, z, 0.08, YPf + 0.06, YPf + 4.6, COL['lamp'], 8); self.B.box(x, z, 0.7, 0.3, YPf + 4.5, YPf + 4.7, rgb('#FFF0B8'), PLAIN, True, False)
        self.items['lamps'].append({'x': round(x, 2), 'z': round(z, 2), 'y': YPf + 0.06})

    def bench(self, f, o):
        YPf = f['yp']
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o
        t = (f['tx'], f['tz']); n = (f['nx'], f['nz'])
        c4 = [(x - t[0] * 0.9 - n[0] * 0.25, z - t[1] * 0.9 - n[1] * 0.25), (x + t[0] * 0.9 - n[0] * 0.25, z + t[1] * 0.9 - n[1] * 0.25), (x + t[0] * 0.9 + n[0] * 0.25, z + t[1] * 0.9 + n[1] * 0.25), (x - t[0] * 0.9 + n[0] * 0.25, z - t[1] * 0.9 + n[1] * 0.25)]
        self.B.obox_pts(c4, YPf + 0.4, YPf + 0.52, COL['bench'], WOOD, True, False)
        for sg in (-1, 1): self.B.box(x + t[0] * 0.7 * sg, z + t[1] * 0.7 * sg, 0.15, 0.4, YPf + 0.06, YPf + 0.4, COL['iron'], PLAIN, True, False)
        self.items['benches'].append({'x': round(x, 2), 'z': round(z, 2), 'nx': round(-n[0], 3), 'nz': round(-n[1], 3)})

    def kiosk(self, f, o, idx):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o
        yb = self.sample(x, z); t = (f['tx'], f['tz']); n = (f['nx'], f['nz']); S = 2.4
        col = self.rnd.choice([rgb('#F2E8D0'), rgb('#9ED8D8'), rgb('#F4B6A0'), rgb('#C8E0A0')])
        c4 = [(x - t[0] * S - n[0] * S, z - t[1] * S - n[1] * S), (x + t[0] * S - n[0] * S, z + t[1] * S - n[1] * S), (x + t[0] * S + n[0] * S, z + t[1] * S + n[1] * S), (x - t[0] * S + n[0] * S, z - t[1] * S + n[1] * S)]
        self.B.obox_pts(c4, yb, yb + 2.6, col, PLAIN, False, False)
        # balcao frontal (para o mar) e telhado de palha piramidal
        cxx, czz = x - n[0] * (S + 0.5), z - n[1] * (S + 0.5)
        c2 = [(cxx - t[0] * S * 0.8 - n[0] * 0.3, czz - t[1] * S * 0.8 - n[1] * 0.3), (cxx + t[0] * S * 0.8 - n[0] * 0.3, czz + t[1] * S * 0.8 - n[1] * 0.3), (cxx + t[0] * S * 0.8 + n[0] * 0.3, czz + t[1] * S * 0.8 + n[1] * 0.3), (cxx - t[0] * S * 0.8 + n[0] * 0.3, czz - t[1] * S * 0.8 + n[1] * 0.3)]
        self.B.obox_pts(c2, yb, yb + 1.05, rgb('#8B6B47'), WOOD, True, False)
        R = S * 1.9
        for q in range(4):
            a0 = math.pi / 4 + q * math.pi / 2; a1 = a0 + math.pi / 2
            P0 = (x + (math.cos(a0) * t[0] + math.sin(a0) * n[0]) * R, yb + 2.5, z + (math.cos(a0) * t[1] + math.sin(a0) * n[1]) * R)
            P1 = (x + (math.cos(a1) * t[0] + math.sin(a1) * n[0]) * R, yb + 2.5, z + (math.cos(a1) * t[1] + math.sin(a1) * n[1]) * R)
            self.B.tri(ROOF, P0, P1, (x, yb + 4.4, z), (math.cos((a0 + a1) / 2), 0.7, math.sin((a0 + a1) / 2)), COL['roof'], None, True)
        # mesas e guarda-sois
        for j in (-1, 0, 1):
            tx_, tz_ = cxx - n[0] * 3.0 + t[0] * j * 3.0, czz - n[1] * 3.0 + t[1] * j * 3.0
            self.B.cyl(tx_, tz_, 0.55, yb + 0.7, yb + 0.76, rgb('#F5F5F5'), 8); self.B.cyl(tx_, tz_, 0.05, yb, yb + 0.7, COL['iron'], 6)
        self.items['kiosks'].append({'x': round(x, 2), 'z': round(z, 2), 'nx': round(-n[0], 3), 'nz': round(-n[1], 3), 'y': round(yb, 2)})

    def tower(self, f, o):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o; yb = self.sample(x, z)
        for sx_ in (-1, 1):
            for sz_ in (-1, 1): self.B.cyl(x + sx_ * 1.0, z + sz_ * 1.0, 0.09, yb, yb + 3.1, COL['towerW'], 6)
        self.B.box(x, z, 3.0, 3.0, yb + 3.1, yb + 5.4, COL['towerR'], PLAIN, True, False)
        self.B.box(x, z, 3.3, 3.3, yb + 5.4, yb + 5.6, COL['towerW'], PLAIN, True, False)
        self.B.cyl(x + 1.3, z + 1.3, 0.04, yb + 5.6, yb + 7.6, COL['iron'], 6)
        self.B.quad(PLAIN, [(x + 1.3, yb + 7.0, z + 1.3), (x + 2.5, yb + 7.0, z + 1.3), (x + 2.5, yb + 7.6, z + 1.3), (x + 1.3, yb + 7.6, z + 1.3)], (0, 0, -1), rgb('#E53935'), None, True)
        self.items['towers'].append({'x': round(x, 2), 'z': round(z, 2), 'y': round(yb, 2)})

    def court(self, f, o):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o; yb = self.sample(x, z); t = (f['tx'], f['tz'])
        for sg in (-1, 1):
            self.B.cyl(x + t[0] * 4.5 * sg, z + t[1] * 4.5 * sg, 0.06, yb, yb + 2.4, COL['iron'], 6)
        self.B.quad(PLAIN, [(x - t[0] * 4.5, yb + 1.5, z - t[1] * 4.5), (x + t[0] * 4.5, yb + 1.5, z + t[1] * 4.5), (x + t[0] * 4.5, yb + 2.4, z + t[1] * 4.5), (x - t[0] * 4.5, yb + 2.4, z - t[1] * 4.5)], (f['nx'], 0, f['nz']), COL['net'], None, True)
        self.B.quad(PLAIN, [(x + t[0] * 4.5, yb + 1.5, z + t[1] * 4.5), (x - t[0] * 4.5, yb + 1.5, z - t[1] * 4.5), (x - t[0] * 4.5, yb + 2.4, z - t[1] * 4.5), (x + t[0] * 4.5, yb + 2.4, z + t[1] * 4.5)], (-f['nx'], 0, -f['nz']), COL['net'], None, True)
        self.items['courts'].append({'x': round(x, 2), 'z': round(z, 2), 'tx': round(t[0], 3), 'tz': round(t[1], 3)})

    def shower(self, f, o):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o; yb = self.sample(x, z)
        self.B.cyl(x, z, 0.05, yb, yb + 2.4, COL['shower'], 6); self.B.box(x, z, 0.5, 0.5, yb, yb + 0.1, COL['wall'], PLAIN, True, False)
        self.B.cyl(x, z, 0.14, yb + 2.35, yb + 2.45, COL['shower'], 8)
        self.items['showers'].append({'x': round(x, 2), 'z': round(z, 2), 'y': round(yb, 2)})

    def umbrella(self, f, o):
        x, z = f['x'] + f['nx'] * o, f['z'] + f['nz'] * o; yb = self.sample(x, z)
        if yb < 0.3: return
        col = UMB[self.rnd.randrange(len(UMB))]
        self.B.cyl(x, z, 0.03, yb, yb + 2.0, COL['iron'], 5)
        for q in range(6):
            a0 = q * math.pi / 3; a1 = a0 + math.pi / 3
            self.B.tri(PLAIN, (x + math.cos(a0) * 1.1, yb + 1.85, z + math.sin(a0) * 1.1), (x + math.cos(a1) * 1.1, yb + 1.85, z + math.sin(a1) * 1.1), (x, yb + 2.2, z), (0, 1, 0), col if q % 2 == 0 else COL['white'], None, True)
        self.items['umbrellas'].append({'x': round(x, 2), 'z': round(z, 2)})

    def access_paths(self):
        """calcada de acesso da travessia da avenida ate o calcadao (corta a faixa de palmeiras)"""
        out = []
        for (x, z) in getattr(self.g, 'xw_beach', []):
            D = float(self.geo.Dsea[self.geo.idx(x, z)])
            if not (50 < D < 68): continue
            gx, gz = self.grad(x, z); sx, sz = norm(-gx, -gz); tx, tz = -sz, sx
            p0 = (x + sx * 14.0, z + sz * 14.0); p1 = (x + sx * 19.0, z + sz * 19.0)
            y0 = self.sample(*p0) + 0.27; y1 = YP + 0.06
            W = 2.4
            q = [(p0[0] - tx * W, y0, p0[1] - tz * W), (p0[0] + tx * W, y0, p0[1] + tz * W), (p1[0] + tx * W, y1, p1[1] + tz * W), (p1[0] - tx * W, y1, p1[1] - tz * W)]
            self.g.quad(PAVER, q, COL['wave1'], 'prom')
            out.append({'x': round(x, 2), 'z': round(z, 2), 'sx': round(sx, 3), 'sz': round(sz, 3)})
        self.items['paths'] = out
        return out

    def build(self):
        self.items['paths'] = []
        for i, fr in enumerate(self.chains()): self.build_line(fr, i)
        self.g.layers.extend(self.polys)
        return self
