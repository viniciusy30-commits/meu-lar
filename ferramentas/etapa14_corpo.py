"""Protótipo da deformação masculina (a versão final vai para ferramentas/etapa14_corpo.py e BodyMorph.kt)."""
import numpy as np
def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def gs(x, c, s): return np.exp(-((x - c) / s) ** 2)

# parâmetros femininos (iguais ao BodyMorph.kt atual)
BUST_C = (9.0, 127.0); BUST_R = 11.0; BUST_UP = 0.85; BUST_DN = 1.1; BUST_P = 0.8; BUST_SPREAD = 0.9; BUST_DROP = 0.10
BUST_POS = 8.0; BUST_NEG = 3.0; BUST_BASE_F = 2.0

M = dict(OMBRO=0.6, PEITO=0.15, CINT=0.0, QUAD=0.0, BRACO=0.15, PESCOCO=0.12, BUST_BASE=-1.0, PESO=0.0, ZFAC=0.25,
         PEC=0.0, PEC_Y=121.0, PEC_R=14.0, DELT=0.7, COXA=0.0, BUTT=0.0, TRAP=0.0, ALTURA=1.0)

def warp(p, b, masc=False, M=M):
    b = np.array(b, float).copy()
    x, y, z = p[:, 0], p[:, 1], p[:, 2]; ax = np.abs(x); sx = np.where(x < 0, -1., 1.)
    d = np.zeros_like(p); low = 1 - sm(146, 156, y)
    m = 1.0 if masc else 0.0
    peso = .14 * (b[1] + M['PESO'] * m); ombro = 3.0 * (b[2] + M['OMBRO'] * m); peito = .10 * (b[3] + M['PEITO'] * m)
    cint = .15 * (b[5] + M['CINT'] * m); quad = .12 * (b[6] + M['QUAD'] * m); coxa = .25 * (b[7] + M['COXA'] * m)
    braco = .25 * (b[8] + M['BRACO'] * m); cab = .12 * b[9]
    busto = (BUST_POS * b[4] if b[4] > 0 else BUST_NEG * b[4]) + (M['BUST_BASE'] if masc else BUST_BASE_F)
    d[:, 0] += sx * np.minimum(ax, 24) * peso * low; d[:, 2] += (z - 3) * peso * low
    d[:, 0] += sx * ombro * sm(22, 34, ax) * sm(62, 78, y) * low
    w = sm(100, 114, y) * (1 - sm(128, 140, y)) * (1 - sm(18, 28, ax)); d[:, 0] += x * peito * w; d[:, 2] += z * peito * w * (1 - m * (1 - M['ZFAC']))
    cx, cy = BUST_C
    dx = x - sx * cx; dy = y - cy
    dys = np.where(dy > 0, dy * BUST_UP, dy * BUST_DN)
    rho = np.sqrt(dx * dx + dys * dys)
    fr = sm(-3.0, 3.0, z)
    t = np.clip(1 - rho / BUST_R, 0, 1); h = (t * t * (3 - 2 * t)) ** BUST_P * fr
    d[:, 2] += busto * h
    d[:, 0] += dx / BUST_R * BUST_SPREAD * busto * h
    d[:, 1] += dys / BUST_R * BUST_SPREAD * busto * h - BUST_DROP * busto * h
    w = sm(92, 100, y) * (1 - sm(110, 118, y)) * (1 - sm(20, 30, ax)); d[:, 0] += x * cint * w; d[:, 2] += z * cint * w * (1 - m * (1 - M['ZFAC']))
    w = sm(66, 78, y) * (1 - sm(94, 104, y)) * (1 - sm(26, 36, ax)); d[:, 0] += x * quad * w; d[:, 2] += (z - 3) * quad * .5 * w
    rx = x - sx * 9.3; rz = z - 3.8; r = np.hypot(rx, rz)
    w = sm(44, 58, y) * (1 - sm(86, 98, y)) * (1 - sm(11, 19, r)) * sm(0, 5, ax); d[:, 0] += rx * coxa * w; d[:, 2] += rz * coxa * w
    ux = .6012 * sx; vx = x - sx * 13.3; vy = y - 142.5; vz = z + 2.9; t = vx * ux + vy * -.7991 + vz * -.0076
    px = vx - t * ux; py = vy + t * .7991; pz = vz + t * .0076; r = np.sqrt(px ** 2 + py ** 2 + pz ** 2)
    w = sm(6, 16, t) * (1 - sm(44, 52, t)) * (1 - sm(9, 15, r)); d[:, 0] += px * braco * w; d[:, 1] += py * braco * w; d[:, 2] += pz * braco * w
    w = sm(146, 156, y); d[:, 0] += x * cab * w; d[:, 1] += (y - 148) * cab * w; d[:, 2] += z * cab * w
    if masc:
        w = gs(y, 149, 5); d[:, 0] += x * M['PESCOCO'] * w; d[:, 2] += (z + 0.3) * M['PESCOCO'] * w
        # peitoral: placa larga e baixa, para frente
        pdx = x - sx * 8.5; pdy = y - M['PEC_Y']
        rr = np.sqrt(pdx * pdx + pdy * pdy); tt = np.clip(1 - rr / M['PEC_R'], 0, 1)
        d[:, 2] += M['PEC'] * (tt * tt * (3 - 2 * tt)) * sm(-3, 3, z)
        # deltoide: volume no topo do braço (para os lados)
        ddx = x - sx * 19.0; ddy = y - 137.0; rr = np.sqrt(ddx * ddx + ddy * ddy); tt = np.clip(1 - rr / 15.0, 0, 1)
        d[:, 0] += sx * M['DELT'] * (tt * tt * (3 - 2 * tt))
        # trapézio: preenche a ligação pescoço-ombro
        d[:, 1] += M['TRAP'] * gs(ax, 11.0, 7.0) * gs(y, 146.0, 4.5)
        # glúteo mais reto
        d[:, 2] += M['BUTT'] * (z - 3.8) * sm(66, 78, y) * (1 - sm(94, 104, y)) * (z < 3.8)
    return p + d
