"""Linhas de costa/orla: contornos de distancia ao mar (marching squares) para a Av. Beira-Mar, o calcadao e a faixa de areia."""
import math
import numpy as np
from plan import *

def contour(field, level, mask=None, cell=CELL):
    """marching squares: devolve lista de polilinhas [(x,z),...] onde field == level (so em celulas com mask True)"""
    H, W = field.shape
    segs = []
    def interp(x0, z0, v0, x1, z1, v1):
        t = (level - v0) / (v1 - v0) if v1 != v0 else 0.5
        return (x0 + (x1 - x0) * t, z0 + (z1 - z0) * t)
    for j in range(H - 1):
        for i in range(W - 1):
            if mask is not None and not (mask[j, i] and mask[j + 1, i] and mask[j, i + 1] and mask[j + 1, i + 1]): continue
            v = (field[j, i], field[j, i + 1], field[j + 1, i + 1], field[j + 1, i])
            c = [(i * cell, j * cell), ((i + 1) * cell, j * cell), ((i + 1) * cell, (j + 1) * cell), (i * cell, (j + 1) * cell)]
            idx = sum((1 << k) for k in range(4) if v[k] > level)
            if idx in (0, 15): continue
            pts = []
            for a in range(4):
                b = (a + 1) % 4
                if (v[a] > level) != (v[b] > level): pts.append(interp(c[a][0], c[a][1], v[a], c[b][0], c[b][1], v[b]))
            if len(pts) == 2: segs.append((pts[0], pts[1]))
            elif len(pts) == 4: segs.append((pts[0], pts[1])); segs.append((pts[2], pts[3]))
    # encadeia segmentos
    key = lambda p: (round(p[0], 1), round(p[1], 1))
    adj = {}
    for a, b in segs:
        adj.setdefault(key(a), []).append((a, b)); adj.setdefault(key(b), []).append((b, a))
    used = set(); lines = []
    for a, b in segs:
        k0 = (key(a), key(b))
        if k0 in used: continue
        line = [a, b]; used.add(k0); used.add((key(b), key(a)))
        for end in (0, 1):
            while True:
                tip = line[-1] if end == 0 else line[0]
                nxt = None
                for (p, q) in adj.get(key(tip), []):
                    if (key(p), key(q)) in used: continue
                    nxt = (p, q); break
                if not nxt: break
                used.add((key(nxt[0]), key(nxt[1]))); used.add((key(nxt[1]), key(nxt[0])))
                if end == 0: line.append(nxt[1])
                else: line.insert(0, nxt[1])
        lines.append(line)
    return lines

def smooth_line(p, passes=3, keep_ends=True):
    for _ in range(passes):
        if len(p) < 3: break
        out = [p[0]]
        for a, b in zip(p, p[1:]):
            out.append((a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25)); out.append((a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75))
        out.append(p[-1]); p = out
    return p

def resample(p, step):
    out = [p[0]]; acc = 0.0
    for a, b in zip(p, p[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        while acc + step <= L + 1e-9 and L > 0:
            acc += step; f = acc / L; out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
        acc -= L
    out.append(p[-1]); return out

def length(p): return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(p, p[1:]))

def beach_lines(geo, level_eff, min_len=150.0):
    """polilinhas a 'level_eff' metros do mar (distancia efetiva), dentro da zona de praia; suavizadas"""
    m = geo.beach_zone | np.roll(geo.beach_zone, 1, 0) | np.roll(geo.beach_zone, -1, 0) | np.roll(geo.beach_zone, 1, 1) | np.roll(geo.beach_zone, -1, 1)
    lines = contour(geo.Dsea, level_eff, m)
    out = []
    for l in lines:
        if length(l) < min_len: continue
        l = resample(smooth_line(resample(l, 12.0), 3), 8.0)
        out.append(l)
    return out
