"""Sinalizacao: semaforos (poste + braco), placas, linhas de retencao, setas, dentes de tubarao, lombadas, placa de fim de via. Geometria assada + dados JSON."""
import math
import numpy as np
from bake import rgb, PLAIN, METAL, PAVER, STONE
from plan import *
import traffic as TR

ASPHALT = 15
C = {'pole': rgb('#4B4F55'), 'red': rgb('#D32F2F'), 'white': rgb('#F5F5F5'), 'yellow': rgb('#F5C518'), 'blue': rgb('#1E5AA8'), 'black': rgb('#1B1B1D'), 'green': rgb('#2E9E4F'),
     'back': rgb('#8A8D91'), 'bump_y': rgb('#F2C400'), 'bump_k': rgb('#1E1E20'), 'head': rgb('#1D1F22'), 'redlit': rgb('#FF3B30'), 'amber': rgb('#8A6A12'), 'grn': rgb('#145A28')}
ROADY = 0.12; CURB_H = 0.15

def norm(dx, dz):
    l = math.hypot(dx, dz) or 1e-9
    return dx / l, dz / l

class Furn:
    def __init__(self, gr, tr):
        self.g = gr; self.tr = tr; self.B = gr.B; self.c = gr.c
        self.signs = []; self.heads = []; self.poles = []; self.bump_polys = []
        self.arrows = 0; self.lines = 0
        self.pits = [(q['pit'][0], q['pit'][1]) for q in gr.fronts if 'pit' in q]

    # --------------------------------------------------------- primitivas
    def pole(self, x, z, y0, h, r=0.07, col=None, tag=''):
        self.B.cyl(x, z, r, y0, y0 + h, col or C['pole'], 8)
        self.poles.append((x, z)); self.pole_tags = getattr(self, 'pole_tags', []) + [(x, z, tag)]

    def plate(self, cx, cy, cz, n, shape, size, col, border=None, mat=PLAIN):
        """placa vertical voltada para n=(nx,nz). shape: oct|tri|circle|diamond|rect"""
        nx, nz = n; t = (-nz, nx)                                  # horizontal da placa
        def P(u, v, off=0.0): return (cx + t[0] * u + nx * off, cy + v, cz + t[1] * u + nz * off)
        pts = {'oct': [(math.cos(math.radians(22.5 + 45 * i)) * size, math.sin(math.radians(22.5 + 45 * i)) * size) for i in range(8)],
               'tri': [(0, -size * 0.9), (size * 1.0, size * 0.75), (-size * 1.0, size * 0.75)],
               'circle': [(math.cos(math.radians(30 * i)) * size, math.sin(math.radians(30 * i)) * size) for i in range(12)],
               'diamond': [(0, size * 1.1), (size * 1.1, 0), (0, -size * 1.1), (-size * 1.1, 0)],
               'rect': [(-size * 0.5, size * 0.8), (size * 0.5, size * 0.8), (size * 0.5, -size * 0.8), (-size * 0.5, -size * 0.8)]}[shape]
        def fan(poly, color, off, flip=False, scale=1.0):
            for i in range(1, len(poly) - 1):
                a, b, c = poly[0], poly[i], poly[i + 1]
                A, Bp, Cp = P(a[0] * scale, a[1] * scale, off), P(b[0] * scale, b[1] * scale, off), P(c[0] * scale, c[1] * scale, off)
                nn = (-nx, 0, -nz) if flip else (nx, 0, nz)
                self.B.tri(mat, A, Bp, Cp, nn, color, None, True)
        if border: fan(pts, border, 0.012)
        fan(pts, col, 0.018, scale=0.82 if border else 1.0)
        fan(pts, C['back'], -0.012, flip=True)

    def room(self, a):
        """metros de rua livres (a partir do corte) neste braco antes do proximo cruzamento"""
        g = self.g; e = g.c.edges[a['k']]; oth = e['b'] if a['end'] == 'a' else e['a']
        oc = max([x['cut'] for x in g.arms.get(oth, []) if x['k'] == a['k']] or [0])
        return g.elen(a['k']) - a['cut'] - oc

    def road_vec(self, a):
        """posicao/tangente de um braco a uma distancia: devolve funcao s_out -> (x,z,y,dx_out,dz_out) com s_out a partir do corte"""
        g = self.g; k = a['k']; L = g.elen(k)
        def f(s_out):
            s = a['cut'] + s_out if a['end'] == 'a' else L - a['cut'] - s_out
            s = min(max(s, 0.0), L)
            x, z, y, tx, tz = g.at(k, s)
            xa, za, *_ = g.at(k, max(s - 3, 0)); xb, zb, *_ = g.at(k, min(s + 3, L))
            tx, tz = norm(xb - xa, zb - za)
            dx, dz = (tx, tz) if a['end'] == 'a' else (-tx, -tz)           # para fora do no
            return x, z, y, dx, dz
        return f

    # --------------------------------------------------------- placas e semaforos
    def add_sign(self, kind, x, z, y, n, text='', shape='circle', size=0.38, col=None, border=None, ph=2.4, extra=None):
        for sh in (0.0, 2.3, -2.3, 4.6, -4.6):
            xx, zz = x + n[0] * sh, z + n[1] * sh
            if not any(math.hypot(xx - px, zz - pz) < 1.35 for px, pz in self.pits): x, z = xx, zz; break
        self.pole(x, z, y, ph, tag=kind)
        self.plate(x, y + ph - 0.25, z, n, shape, size, col, border)
        self.signs.append({'type': kind, 'x': round(x, 2), 'z': round(z, 2), 'y': round(y, 2), 'nx': round(n[0], 3), 'nz': round(n[1], 3), 'text': text, 'h': ph})

    def signal_pole(self, ni, a):
        g = self.g; arm_fn = self.road_vec(a)
        lvl = min(a['lvl'], 2); aa = a['a']; ins = TR.SEC_INS[lvl]
        x, z, y, dx, dz = arm_fn(8.0)
        rin = (dz, -dx)                                                   # direita de quem chega
        lat = aa + 0.2 + 1.0
        px, pz = x + rin[0] * lat, z + rin[1] * lat; yb = y + ROADY + CURB_H
        for sh in (0.0, 2.6, -2.6, 5.0):
            if not any(math.hypot(px + dx * sh - qx, pz + dz * sh - qz) < 1.5 for qx, qz in self.pits): px, pz = px + dx * sh, pz + dz * sh; break
        self.B.cyl(px, pz, 0.13, yb, yb + 6.4, C['pole'], 10); self.poles.append((px, pz))
        face = (dx, dz)                                                   # cabecas voltadas para quem se aproxima
        offs = TR.lane_offsets(lvl)
        # braco: do poste ate a ultima faixa (avenida) / ate o eixo da faixa (coletora)
        far = offs[0] if lvl == 0 else offs[0]
        ex, ez = x + rin[0] * far, z + rin[1] * far
        from scenery import bar
        bar(self.B, (px, yb + 6.0, pz), (ex, yb + 6.0, ez), 0.14, C['pole'], METAL)
        for u, off in enumerate(offs):
            hx, hz = x + rin[0] * off, z + rin[1] * off
            self.head(hx, yb + 5.45, hz, face)
            self.heads.append({'node': ni, 'k': a['k'], 'end': a['end'], 'x': round(hx, 2), 'y': round(yb + 5.45, 2), 'z': round(hz, 2), 'nx': round(face[0], 3), 'nz': round(face[1], 3), 'lane': u})
        # cabeca de poste (visivel de perto)
        self.head(px, yb + 3.0, pz, face)
        self.heads.append({'node': ni, 'k': a['k'], 'end': a['end'], 'x': round(px, 2), 'y': round(yb + 3.0, 2), 'z': round(pz, 2), 'nx': round(face[0], 3), 'nz': round(face[1], 3), 'lane': -1})

    def head(self, x, y, z, n):
        nx, nz = n; t = (-nz, nx)
        w, h, d = 0.22, 0.55, 0.20
        corners = [(x - t[0] * w - nx * d, z - t[1] * w - nz * d), (x + t[0] * w - nx * d, z + t[1] * w - nz * d), (x + t[0] * w + nx * d, z + t[1] * w + nz * d), (x - t[0] * w + nx * d, z - t[1] * w + nz * d)]
        self.B.obox_pts(corners, y - h, y + h, C['head'], PLAIN, True, False)
        for q, col in ((0.30, C['redlit']), (0.0, C['amber']), (-0.30, C['grn'])):
            cx, cz = x + nx * (d + 0.015), z + nz * (d + 0.015)
            self.B.quad(PLAIN, [(cx - t[0] * 0.11, y + q - 0.11, cz - t[1] * 0.11), (cx + t[0] * 0.11, y + q - 0.11, cz + t[1] * 0.11), (cx + t[0] * 0.11, y + q + 0.11, cz + t[1] * 0.11), (cx - t[0] * 0.11, y + q + 0.11, cz - t[1] * 0.11)], (nx, 0, nz), col, None, True)

    # --------------------------------------------------------- linhas
    def hline(self, x, z, y, d, lo, hi, s0, s1, col, layer='mark'):
        """faixa pintada: lateral [lo,hi] (lado direito de quem chega), ao longo [s0,s1] para fora do no"""
        rin = (d[1], -d[0])
        p = [(x + d[0] * s0 + rin[0] * lo, y + ROADY + 0.02, z + d[1] * s0 + rin[1] * lo), (x + d[0] * s0 + rin[0] * hi, y + ROADY + 0.02, z + d[1] * s0 + rin[1] * hi),
             (x + d[0] * s1 + rin[0] * hi, y + ROADY + 0.02, z + d[1] * s1 + rin[1] * hi), (x + d[0] * s1 + rin[0] * lo, y + ROADY + 0.02, z + d[1] * s1 + rin[1] * lo)]
        self.g.quad(PLAIN, p, col, layer); self.lines += 1

    def arrow(self, x, z, y, d_travel, col):
        """seta reta (aponta para d_travel)"""
        r = (-d_travel[1], d_travel[0]); yy = y + ROADY + 0.02
        def Pt(a, b): return (x + d_travel[0] * a + r[0] * b, yy, z + d_travel[1] * a + r[1] * b)
        self.g.quad(PLAIN, [Pt(-1.8, -0.2), Pt(0.4, -0.2), Pt(0.4, 0.2), Pt(-1.8, 0.2)], col, 'mark')
        self.B.tri(PLAIN, Pt(0.3, -0.7), Pt(1.8, 0.0), Pt(0.3, 0.7), (0, 1, 0), col, None, True)
        self.arrows += 1

    def build_approaches(self):
        g = self.g; tr = self.tr
        for ni, arms in g.arms.items():
            n = len(arms)
            if n < 3: continue
            for a in arms:
                ctl = tr.control.get((ni, a['k'], a['end']))
                if a['kind'] == 'bridge' or ctl is None: continue
                lvl = min(a['lvl'], 2); aa = TR.SEC_A[lvl]; ins = TR.SEC_INS[lvl]
                f = self.road_vec(a)
                s_line = 5.2 if a.get('xw') else 1.8
                x, z, y, dx, dz = f(s_line); d = (dx, dz)
                lo = ins + 0.25; hi = aa - (2.0 if lvl == 2 else 2.5)
                if ctl in ('signal', 'stop'):
                    self.hline(x, z, y, d, lo, hi, -0.25, 0.25, C['white'])
                elif ctl == 'yield':
                    # dentes de tubarao
                    off = lo
                    while off < hi - 0.5:
                        rin = (d[1], -d[0]); yy = y + ROADY + 0.02
                        P0 = (x + rin[0] * off, yy, z + rin[1] * off); P1 = (x + rin[0] * (off + 0.7), yy, z + rin[1] * (off + 0.7)); P2 = (x + rin[0] * (off + 0.35) + d[0] * 0.9, yy, z + rin[1] * (off + 0.35) + d[1] * 0.9)
                        self.B.tri(PLAIN, P0, P1, P2, (0, 1, 0), C['white'], None, True); off += 1.0
                # setas nas avenidas
                if lvl == 0 and ctl in ('signal', 'priority', 'stop') and g.elen(a['k']) > 70:
                    xa, za, ya, dxa, dza = f(14.0)
                    rin = (dza, -dxa)
                    for off in TR.lane_offsets(0):
                        self.arrow(xa + rin[0] * off, za + rin[1] * off, ya, (-dxa, -dza), C['white'])
                # sinalizacao vertical
                xs, zs, ys, dxs, dzs = f(min(7.8, max(2.0, self.room(a) - 3.0)))
                rin = (dzs, -dxs); lat = aa + 0.2 + 0.85
                px, pz = xs + rin[0] * lat, zs + rin[1] * lat; yb = ys + ROADY + CURB_H
                face = (dxs, dzs)
                if ctl == 'signal':
                    self.signal_pole(ni, a)
                elif ctl == 'stop':
                    self.add_sign('stop', px, pz, yb, face, 'PARE', 'oct', 0.40, C['red'], C['white'])
                elif ctl == 'yield':
                    self.add_sign('yield', px, pz, yb, face, 'DÊ A PREFERÊNCIA', 'tri', 0.42, C['white'], C['red'])
                    # aviso de rotatoria a 60 m (vias maiores)
                    if lvl <= 1 and g.elen(a['k']) > 130:
                        xr, zr, yr, dxr, dzr = f(min(60.0, self.room(a) - 6.0)); rr = (dzr, -dxr)
                        self.add_sign('rotatoria', xr + rr[0] * lat, zr + rr[1] * lat, yr + ROADY + CURB_H, (dxr, dzr), 'ROTATÓRIA', 'diamond', 0.34, C['yellow'], C['black'])
                if a.get('xw') and ctl != 'signal':
                    xp, zp, yp, dxp, dzp = f(min(13.5, max(3.0, self.room(a) - 3.0))); rp = (dzp, -dxp)
                    self.add_sign('pedestre', xp + rp[0] * lat, zp + rp[1] * lat, yp + ROADY + CURB_H, (dxp, dzp), 'PEDESTRE', 'diamond', 0.34, C['yellow'], C['black'])

    # --------------------------------------------------------- limites de velocidade
    def build_speed_signs(self):
        g = self.g; c = self.c
        for k, e in enumerate(c.edges):
            if e['kind'] == 'redbridge': continue
            lvl = min(e['lvl'], 2); L = g.elen(k); aa = TR.SEC_A[lvl]; sp = (TR.LANES[lvl]['speed'] if e['kind'] != 'bridge' else 50)
            ca = max([a['cut'] for a in g.arms.get(e['a'], []) if a['k'] == k and a['end'] == 'a'] or [0]); cb = max([a['cut'] for a in g.arms.get(e['b'], []) if a['k'] == k and a['end'] == 'b'] or [0])
            if L < ca + cb + 60: continue
            ss = [(ca + 38.0, 'f')]
            ss.append((L - cb - 38.0, 'b'))
            s = ca + 38.0 + 300.0
            while s < L - cb - 80.0: ss.append((s, 'f' if len(ss) % 2 == 0 else 'b')); s += 300.0
            for s, dirn in ss:
                x, z, y, tx, tz = g.at(k, s)
                n_f = (-tz, tx)                                   # direita do sentido a->b
                if dirn == 'f': nxv = n_f; face = (-tx, -tz)    # placa no lado direito de quem anda a->b, voltada para quem chega (de tras)
                else: nxv = (-n_f[0], -n_f[1]); face = (tx, tz)
                lat = aa + 0.2 + 0.85
                if g.zone(x, z) == 'ponte' and False: continue
                self.add_sign('velocidade', x + nxv[0] * lat, z + nxv[1] * lat, y + ROADY + CURB_H, face, str(sp), 'circle', 0.36, C['white'], C['red'])

    # --------------------------------------------------------- lombadas
    def build_bumps(self):
        g = self.g; tr = self.tr
        for b in tr.bumps:
            k = b['k']; e = g.c.edges[k]; lvl = min(e['lvl'], 2); aa = TR.SEC_A[lvl]
            x, z, y, tx, tz = g.at(k, b['s']); nx_, nz_ = -tz, tx
            yb = y + ROADY
            LEN = [0.0, 0.9, 2.7, 3.6]; HH = [0.0, 0.10, 0.10, 0.0]
            nstr = int((2 * aa) / 0.6) + 1
            for q in range(3):
                for i in range(nstr):
                    o0 = -aa + i * 0.6; o1 = min(aa, o0 + 0.6)
                    if o1 - o0 < 0.05: continue
                    col = C['bump_y'] if (i % 2 == 0) else C['bump_k']
                    def P(s_, o_, h_): return (x + tx * (s_ - 1.8) + nx_ * o_, yb + h_, z + tz * (s_ - 1.8) + nz_ * o_)
                    self.B.quad(PLAIN, [P(LEN[q], o0, HH[q]), P(LEN[q], o1, HH[q]), P(LEN[q + 1], o1, HH[q + 1]), P(LEN[q + 1], o0, HH[q + 1])], (0, 1, 0), col, None, True)
            self.bump_polys.append([(x - tx * 1.8 + nx_ * aa, z - tz * 1.8 + nz_ * aa), (x + tx * 1.8 + nx_ * aa, z + tz * 1.8 + nz_ * aa), (x + tx * 1.8 - nx_ * aa, z + tz * 1.8 - nz_ * aa), (x - tx * 1.8 - nx_ * aa, z - tz * 1.8 - nz_ * aa)])
            b['poly'] = self.bump_polys[-1]
            # placa "lombada" 24 m antes, nos dois sentidos
            for sgn in (1, -1):
                s2 = b['s'] - 24.0 * sgn
                if s2 < 5 or s2 > g.elen(k) - 5: continue
                ca_ = max([a['cut'] for a in g.arms.get(e['a'], []) if a['k'] == k and a['end'] == 'a'] or [0]); cb_ = max([a['cut'] for a in g.arms.get(e['b'], []) if a['k'] == k and a['end'] == 'b'] or [0])
                if s2 < ca_ + 5 or s2 > g.elen(k) - cb_ - 5: continue
                xx, zz, yy, ttx, ttz = g.at(k, s2); n_f = (-ttz, ttx)
                nv = (n_f[0] * sgn, n_f[1] * sgn); face = (ttx * sgn, ttz * sgn)       # lado direito de quem anda em sgn, voltada para quem chega
                lat = aa + 0.2 + 0.85
                self.add_sign('lombada', xx + nv[0] * lat, zz + nv[1] * lat, yy + ROADY + CURB_H, (-face[0], -face[1]) if False else (-ttx * sgn, -ttz * sgn), 'LOMBADA', 'diamond', 0.34, C['yellow'], C['black'])

    # --------------------------------------------------------- fim de via
    def build_ends(self):
        for info in getattr(self.g, 'cais_info', []):
            nx, nz = info['x'], info['z']; d = (info['dx'], info['dz']); r = (-d[1], d[0])
            yb = self.g.yn[info['node']] + ROADY + CURB_H
            for sgn in (-1, 1):
                x, z = nx + r[0] * 2.0 * sgn - d[0] * 3.9, nz + r[1] * 2.0 * sgn - d[1] * 3.9
                self.B.cyl(x, z, 0.06, yb, yb + 1.2, C['pole'], 8)
            self.add_sign('fim-de-via', nx - d[0] * 3.9, nz - d[1] * 3.9, yb, d, 'FIM DA VIA', 'rect', 0.55, C['red'], C['white'], ph=1.9)

    def build(self):
        self.build_approaches(); self.build_speed_signs(); self.build_bumps(); self.build_ends()
        return self
