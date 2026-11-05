"""Base comum dos assets do Plano Mestre (v4): materiais, metadados e primitivas extras (loft, extrusão, colocação).

Regra 1 (nada flutuando): toda peça nasce do ponto em que se apoia. Os construtores de conteúdo recebem a ALTURA DO APOIO e
colocam a base do objeto 0,5 mm abaixo dela (encaixe invisível), nunca acima. O verificador (integridade.py) confere.
"""
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import *          # noqa
import glb_lib as G

# chaves (textura, material do jogo Mt.*, recorte)
OAK = ('carvalho.png', 6, 0); LIN = ('linho.png', 7, 0); GLZ = ('esmalte.png', 0, 0); MET = ('escovado.png', 11, 0)
PLN = ('liso.png', 0, 0); GLASS = ('liso.png', 12, 0); KRAFT = ('papelao_liso.png', 0, 0)
MATNAMES = {OAK: 'madeira_carvalho', LIN: 'tecido', GLZ: 'ceramica_esmaltada', MET: 'metal_escovado', PLN: 'plastico_pintura',
            GLASS: 'vidro', KRAFT: 'papelao'}
BRASS = (0.93, 0.76, 0.42); STEEL = (0.80, 0.82, 0.85); CHROME = (0.86, 0.88, 0.90)
EMB = 0.0005                # encaixe: a base fica 0,5 mm dentro do apoio (contato garantido, invisível)


def meta(aid, nome, cat, sub, classe, fis, **kw):
    m = dict(id=aid, nome=nome, categoria=cat, subcategoria=sub, classe=classe, versao=2, plano='Plano Mestre v4',
             escala='m (jogo; adulto ~1,45 m)', eixos=dict(cima='+Y', frente='+Z', origem='centro do piso do objeto'), fisica=fis)
    m.update(kw); return m


def finish(M):
    lo, hi = M.bounds(); d = hi - lo
    M.meta['dimensoes'] = dict(largura=round(float(d[0]), 4), altura=round(float(d[1]), 4), profundidade=round(float(d[2]), 4))
    M.meta['caixa'] = dict(min=[round(float(x), 4) for x in lo], max=[round(float(x), 4) for x in hi])
    M.matnames = MATNAMES
    return M


def C4(c, a=1.0): return tuple(c[:3]) + (a,)


def place(dst, src, x=0.0, y=0.0, z=0.0, yaw=0.0, R=None):
    """copia src (construído na origem) para dst girado em Y (yaw) e transladado"""
    RR = rot_y(yaw) if R is None else R
    add_xf(dst, src, RR, (x, y, z))


def loft(g, key, rings, col, cap0=True, cap1=True, uvs=1.0):
    """superfície por anéis (lista de arrays (n,3), mesmo n); tampas planas nas pontas (leque no centro)."""
    R = [np.asarray(r, float) for r in rings]; m = len(R); n = len(R[0])
    P = []; UV = []; T = []
    L = 0.0
    for i, r in enumerate(R):
        if i: L += float(np.linalg.norm(r.mean(0) - R[i - 1].mean(0)))
        for k in range(n + 1):
            P.append(r[k % n]); UV.append((k / n * uvs, L * uvs * 3))
    for i in range(m - 1):
        for k in range(n):
            a = i * (n + 1) + k; b = a + 1; c = a + n + 1; d = c + 1
            T += [(a, c, b), (b, c, d)]
    P = np.array(P); T = np.array(T)
    N = grid_normals(P, T)
    # orientação: normais para fora do eixo central
    cen = np.repeat(np.array([r.mean(0) for r in R]), n + 1, axis=0)
    if (((P - cen) * N).sum(1) < 0).mean() > 0.5: T = T[:, [0, 2, 1]]; N = -N
    cols = [C4(col(P[i], i // (n + 1) / max(m - 1, 1)) if callable(col) else col) for i in range(len(P))]
    g.add(key, P, N, cols, UV, T)
    for end, r in ((cap0, R[0]), (cap1, R[-1])):
        if not end: continue
        c = r.mean(0); fn = np.cross(r[1] - r[0], r[2] - r[0])
        out = (c - (R[1].mean(0) if r is R[0] else R[-2].mean(0)))
        if np.dot(fn, out) < 0: order = list(range(n))[::-1]
        else: order = list(range(n))
        nn = out / (np.linalg.norm(out) + 1e-12)
        PP = [c] + [r[k] for k in order]; TT = [(0, 1 + k, 1 + (k + 1) % n) for k in range(n)]
        cc = C4(col(c, 0.0 if r is R[0] else 1.0) if callable(col) else col)
        g.add(key, PP, [nn] * len(PP), [cc] * len(PP), [(p[0] * uvs, p[2] * uvs) for p in PP], TT)


def ring_ellipse(cx, cy, cz, rx, rz, n=16, axis='y', ry=None, phase=0.0):
    """anel elíptico perpendicular ao eixo dado"""
    a = np.linspace(0, 2 * math.pi, n, endpoint=False) + phase
    if axis == 'y': return np.stack([cx + rx * np.cos(a), np.full(n, cy), cz + rz * np.sin(a)], 1)
    if axis == 'z': return np.stack([cx + rx * np.cos(a), cy + rz * np.sin(a), np.full(n, cz)], 1)
    return np.stack([np.full(n, cx), cy + rx * np.cos(a), cz + rz * np.sin(a)], 1)


def extrude(g, key, poly, y0, y1, col, uv=1.0, bevel=0.0):
    """prisma vertical a partir de um contorno 2D (x, z) anti-horário visto de cima; bevel = chanfro no topo"""
    poly = np.asarray(poly, float); n = len(poly)
    # normal 2D para fora
    def offs(d):
        out = []
        for i in range(n):
            p0 = poly[i - 1]; p1 = poly[i]; p2 = poly[(i + 1) % n]
            e1 = p1 - p0; e2 = p2 - p1
            n1 = np.array([e1[1], -e1[0]]); n1 /= np.linalg.norm(n1) + 1e-12
            n2 = np.array([e2[1], -e2[0]]); n2 /= np.linalg.norm(n2) + 1e-12
            nm = n1 + n2; nm /= np.linalg.norm(nm) + 1e-12
            out.append(p1 - nm * d)
        return np.array(out)
    rings = [np.c_[poly[:, 0], np.full(n, y0), poly[:, 1]], np.c_[poly[:, 0], np.full(n, y1 - bevel), poly[:, 1]]]
    if bevel > 0:
        q = offs(bevel); rings.append(np.c_[q[:, 0], np.full(n, y1), q[:, 1]])
    _prism(g, key, rings, col, uv)


def _prism(g, key, rings, col, uv):
    n = len(rings[0]); P = []; N = []; UV = []; T = []; C = []
    cc = C4(col)
    for i in range(len(rings) - 1):
        A = rings[i]; B = rings[i + 1]
        for k in range(n):
            a0 = A[k]; a1 = A[(k + 1) % n]; b0 = B[k]; b1 = B[(k + 1) % n]
            nrm = np.cross(a1 - a0, b0 - a0); l = np.linalg.norm(nrm)
            if l < 1e-14: continue
            nrm = nrm / l; base = len(P)
            P += [a0, a1, b1, b0]; N += [nrm] * 4; C += [cc] * 4
            s = np.linalg.norm(a1 - a0)
            UV += [(0, a0[1] * uv), (s * uv, a1[1] * uv), (s * uv, b1[1] * uv), (0, b0[1] * uv)]
            T += [(base, base + 2, base + 1), (base, base + 3, base + 2)]
    # fixa a orientação pelo centro
    P = np.array(P); N = np.array(N); T = np.array(T)
    cen = np.vstack(rings).mean(0)
    if ((P - cen) * N).sum(1).mean() < 0: T = T[:, [0, 2, 1]]; N = -N
    g.add(key, P, N, C, UV, T)
    for ring, up in ((rings[0], -1), (rings[-1], 1)):
        c = ring.mean(0); PP = [c] + list(ring); TT = [(0, 1 + k, 1 + (k + 1) % n) for k in range(n)]
        fn = np.cross(ring[1] - c, ring[0] - c)
        if (fn[1] > 0) != (up > 0): TT = [(a, cc_, b) for a, b, cc_ in TT]
        g.add(key, PP, [(0, up, 0)] * len(PP), [cc] * len(PP), [(p[0] * uv, p[2] * uv) for p in PP], TT)


def rounded_rect(w, d, r, n=5):
    pts = []
    for (sx, sz, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        cx = sx * (w / 2 - r); cz = sz * (d / 2 - r)
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def tubec(g, key, pts, r, col, sides=8):
    """tubo de raio constante por pontos, com tampas (calotas) nas pontas"""
    pts = [np.asarray(p, float) for p in pts]
    g.tube(key, pts, [r] * len(pts), sides=sides, col=lambda p, t: C4(col))
    for p in (pts[0], pts[-1]):
        sphere(g, key, tuple(p), r, tuple(col[:3]), seg=max(4, sides // 2))
