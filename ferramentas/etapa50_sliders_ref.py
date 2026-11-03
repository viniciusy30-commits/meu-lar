"""Etapa 50: referencia em Python (numpy) da deformacao dos sliders de corpo (BodyMorph.warpSim, Kotlin). O Kotlin foi portado
linha a linha desta funcao; este arquivo tambem desenha a conferencia (frente/lado, cinza = original, vermelho = +100, azul = -100).
Uso: python3 etapa50_sliders_ref.py <assets/cute> <saida.png> [corpo=af1]"""
import sys, struct
import numpy as np

NS = 27
NAMES = ["Altura", "Peso", "Ombros (largura)", "Peito", "Busto (tamanho)", "Cintura", "Quadril", "Coxas", "Braços (espessura)", "Cabeça",
         "Busto (altura)", "Busto (distância)", "Bumbum", "Barriga", "Postura", "Pescoço (espessura)", "Pescoço (comprimento)",
         "Ombros (altura)", "Antebraços", "Braços (comprimento)", "Mãos", "Panturrilhas", "Pernas (comprimento)", "Vão das coxas",
         "Tornozelos", "Pés", "Torso (comprimento)"]

def sm(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def gs(x, c, s):
    u = (x - c) / s
    return np.exp(-u * u)

def seg(px, py, pz, A, B):
    """t (sem limite), t limitado a 0..1 e distancia ao segmento A->B; devolve tambem o vetor perpendicular (ponto - eixo)."""
    abx, aby, abz = B[0] - A[0], B[1] - A[1], B[2] - A[2]
    l2 = abx * abx + aby * aby + abz * abz
    t = ((px - A[0]) * abx + (py - A[1]) * aby + (pz - A[2]) * abz) / l2
    tc = np.clip(t, 0.0, 1.0)
    qx, qy, qz = px - (A[0] + tc * abx), py - (A[1] + tc * aby), pz - (A[2] + tc * abz)
    return t, tc, np.sqrt(qx * qx + qy * qy + qz * qz), qx, qy, qz

def warp(src, b, r):
    """src: (n,3) cm; b: NS valores -1..1 (b[0], altura, e escala global: nao entra aqui); r: 23 valores do bodyrig.txt."""
    S = (r[0], r[1], r[2]); E = (r[3], r[4], r[5]); W = (r[6], r[7], r[8])
    H = (r[9], r[10], r[11]); K = (r[12], r[13], r[14]); A = (r[15], r[16], r[17])
    topY, neckY, headJ, zc = r[18], r[19], r[20], r[21]
    hipY, kneeY, ankY = H[1], K[1], A[1]
    T = topY - hipY
    waistY = hipY + 0.58 * T
    chestY = hipY + 0.78 * T
    bustY = hipY + 0.80 * T
    bustX = 0.52 * S[0]
    crotchY = hipY - 0.26 * (hipY - kneeY)
    x = src[:, 0]; y = src[:, 1]; z = src[:, 2]
    ax = np.abs(x); sx = np.where(x < 0, -1.0, 1.0)
    dx = np.zeros(len(x)); dy = np.zeros(len(x)); dz = np.zeros(len(x))
    zr = z - zc
    low = 1.0 - sm(neckY - 8.0, neckY + 2.0, y)          # tudo menos a cabeca
    # braco inteiro (ombro -> punho -> ponta da mao) e perna: mascaras por distancia aos eixos
    tS, tSc, dS, _, _, _ = seg(ax, y, z, S, W)
    armAll = sm(-0.18, 0.04, tS) * (1.0 - sm(13.0, 19.0, dS))
    tU, tUc, dU, uX, uY, uZ = seg(ax, y, z, S, E)
    tF, tFc, dF, fX, fY, fZ = seg(ax, y, z, E, W)
    useF = dF < dU
    armD = np.where(useF, dF, dU)
    armT = np.where(useF, 0.5 + 0.5 * tFc, 0.5 * tUc)
    armX = np.where(useF, fX, uX); armY = np.where(useF, fY, uY); armZ = np.where(useF, fZ, uZ)
    armIn = (1.0 - sm(9.0, 14.0, armD))
    notArm = 1.0 - armAll

    # --- Peso (corpo todo, menos a cabeca)
    b1 = b[1]
    if b1 != 0:
        xc = np.minimum(ax, S[0] + 6.0)
        dx += sx * xc * 0.14 * b1 * low
        dz += zr * 0.14 * b1 * low * (1.0 - armAll * 0.5)
    # --- Ombros: largura e altura
    capW = sm(4.0, S[0], ax) * sm(topY - 12.0, topY, y) * (1.0 - sm(neckY - 2.0, neckY + 6.0, y))
    shW = np.maximum(armAll, capW)
    if b[2] != 0:
        dx += sx * 3.0 * b[2] * shW
    if b[17] != 0:
        dy += 2.5 * b[17] * shW
    # --- Peito (costelas)
    if b[3] != 0:
        w = sm(waistY + 4.0, chestY - 2.0, y) * (1.0 - sm(topY - 2.0, topY + 6.0, y)) * (1.0 - sm(S[0] - 4.0, S[0] + 2.0, ax)) * notArm
        dx += x * 0.10 * b[3] * w
        dz += zr * 0.10 * b[3] * w * 0.6
    # --- Busto: tamanho, altura e distancia (cupulas, so na frente)
    if b[4] != 0 or b[10] != 0 or b[11] != 0:
        bdx = ax - bustX
        bdy0 = y - bustY
        bdy = np.where(bdy0 > 0, bdy0 * 0.85, bdy0 * 1.1)
        R = 0.24 * T
        rho = np.sqrt(bdx * bdx + bdy * bdy)
        t = np.clip(1.0 - rho / R, 0.0, 1.0)
        hw = (t * t * (3.0 - 2.0 * t)) ** 0.8 * sm(-3.0, 3.0, zr) * notArm
        amp = np.where(b[4] > 0, 5.5 * b[4], 2.5 * b[4])
        dz += amp * hw
        dx += bdx / R * 0.9 * amp * hw * sx * 0.0 + sx * (bdx / R) * 0.9 * amp * hw * 0.0
        dx += sx * 0.5 * amp * hw * (bdx / R)
        dy += (bdy / R) * 0.9 * amp * hw * 0.4 - 0.1 * amp * hw
        dy += 3.2 * b[10] * hw
        dx += sx * 3.0 * b[11] * hw * sm(0.0, 5.0, ax)
    # --- Cintura
    if b[5] != 0:
        w = sm(waistY - 9.0, waistY - 2.0, y) * (1.0 - sm(waistY + 2.0, waistY + 9.0, y)) * (1.0 - sm(13.0, 19.0, ax)) * notArm
        dx += x * 0.15 * b[5] * w
        dz += zr * 0.15 * b[5] * w * 0.6
    # --- Quadril
    if b[6] != 0:
        w = sm(crotchY - 8.0, crotchY + 4.0, y) * (1.0 - sm(waistY - 8.0, waistY, y)) * (1.0 - sm(21.0, 29.0, ax)) * notArm
        dx += x * 0.12 * b[6] * w
        dz += zr * 0.06 * b[6] * w
    # --- Barriga (para a frente, abaixo da cintura)
    if b[13] != 0:
        ex = ax / 13.0; ey = (y - (waistY - 6.0)) / 11.0
        t = np.clip(1.0 - np.sqrt(ex * ex + ey * ey), 0.0, 1.0)
        dz += 4.5 * b[13] * (t * t * (3.0 - 2.0 * t)) * sm(-2.0, 4.0, zr) * notArm
    # --- Bumbum (para tras)
    if b[12] != 0:
        cx = ax - 0.5 * H[0] * 0.9
        cy = y - (hipY + 3.0)
        t = np.clip(1.0 - np.sqrt(cx * cx + cy * cy) / 14.0, 0.0, 1.0)
        hb = (t * t * (3.0 - 2.0 * t)) * sm(0.0, 6.0, -zr) * notArm
        dz -= 4.0 * b[12] * hb
        dx += sx * 0.8 * b[12] * hb * sm(0.0, 5.0, ax)
        dy += 0.6 * b[12] * hb
    # --- Coxas e vao das coxas (eixo quadril -> joelho)
    tL, tLc, dL, lX, lY, lZ = seg(ax, y, z, H, K)
    thighW = (1.0 - sm(11.0, 17.0, dL)) * sm(0.04, 0.2, tL) * (1.0 - sm(0.82, 1.0, tL)) * sm(0.0, 5.0, ax)
    if b[7] != 0:
        dx += sx * lX * 0.25 * b[7] * thighW
        dy += lY * 0.0
        dz += lZ * 0.25 * b[7] * thighW
    if b[23] != 0:
        dx += sx * 1.2 * b[23] * thighW
    # --- Panturrilhas e tornozelos (eixo joelho -> tornozelo)
    tC, tCc, dC, cX, cY, cZ = seg(ax, y, z, K, A)
    if b[21] != 0:
        w = (1.0 - sm(10.0, 15.0, dC)) * sm(0.05, 0.25, tC) * (1.0 - sm(0.55, 0.85, tC)) * sm(0.0, 4.0, ax)
        dx += sx * cX * 0.22 * b[21] * w
        dz += cZ * 0.22 * b[21] * w
    if b[24] != 0:
        w = (1.0 - sm(8.0, 12.0, dC)) * gs(y, ankY + 5.0, 4.5) * sm(0.0, 4.0, ax)
        dx += sx * cX * 0.30 * b[24] * w
        dz += cZ * 0.30 * b[24] * w
    # --- Pes (escala em x/z em torno do tornozelo; a sola continua no chao)
    if b[25] != 0:
        w = 1.0 - sm(ankY + 1.0, ankY + 8.0, y)
        dx += (ax - A[0]) * sx * 0.25 * b[25] * w * 0.7
        dz += (z - A[2]) * 0.25 * b[25] * w
    # --- Bracos: espessura, antebracos, comprimento, maos
    if b[8] != 0:
        w = sm(0.06, 0.28, armT) * (1.0 - sm(0.86, 1.0, armT)) * armIn
        dx += sx * armX * 0.25 * b[8] * w
        dy += armY * 0.25 * b[8] * w
        dz += armZ * 0.25 * b[8] * w
    if b[18] != 0:
        w = sm(0.42, 0.58, armT) * (1.0 - sm(0.88, 1.0, armT)) * armIn
        dx += sx * armX * 0.28 * b[18] * w
        dy += armY * 0.28 * b[18] * w
        dz += armZ * 0.28 * b[18] * w
    if b[19] != 0:
        ux, uy, uz = W[0] - S[0], W[1] - S[1], W[2] - S[2]
        ln = (ux * ux + uy * uy + uz * uz) ** 0.5
        k = 0.12 * b[19] * ln * sm(0.05, 0.9, tS) * (1.0 - sm(13.0, 19.0, dS))
        dx += sx * ux / ln * k
        dy += uy / ln * k
        dz += uz / ln * k
    if b[20] != 0:
        w = sm(0.92, 1.06, tS) * (1.0 - sm(13.0, 19.0, dS))
        dx += sx * (ax - W[0]) * 0.35 * b[20] * w
        dy += (y - W[1]) * 0.35 * b[20] * w
        dz += (z - W[2]) * 0.35 * b[20] * w
    # --- Pescoco: espessura e cabeca
    if b[15] != 0:
        w = gs(y, 0.5 * (topY + neckY) + 2.0, 6.0) * (1.0 - sm(7.0, 12.0, ax))
        dx += x * 0.25 * b[15] * w
        dz += zr * 0.25 * b[15] * w
    if b[9] != 0:
        w = sm(neckY - 2.0, neckY + 8.0, y)
        c = 0.12 * b[9]
        dx += x * c * w
        dy += (y - neckY) * c * w
        dz += zr * c * w
    # --- Postura: gira o tronco de cima em torno da cintura (b>0 = mais ereta, b<0 = curvada)
    if b[14] != 0:
        th = -0.10 * b[14] * sm(waistY, chestY, y)
        yr = y - waistY
        dz += -yr * np.sin(th) + zr * (np.cos(th) - 1.0)
        dy += zr * np.sin(th) + yr * (np.cos(th) - 1.0)
    # --- comprimentos (pernas, torso, pescoco): remapeamento de y; o braco acompanha o ombro
    fLeg = 1.0 + 0.07 * b[22]; fTor = 1.0 + 0.08 * b[26]; fNeck = 1.0 + 0.35 * b[16]
    def extra(yy):
        e = (fLeg - 1.0) * (np.clip(yy, ankY, hipY) - ankY)
        e = e + (fTor - 1.0) * (np.clip(yy, hipY, topY) - hipY)
        e = e + (fNeck - 1.0) * (np.clip(yy, topY + 3.0, neckY + 2.0) - (topY + 3.0))
        return e
    ex_y = extra(y)
    exS = extra(np.full(len(y), S[1]))
    ex_y = ex_y + (exS - ex_y) * armAll
    dy += ex_y
    out = np.empty_like(src)
    out[:, 0] = x + dx; out[:, 1] = y + dy; out[:, 2] = z + dz
    return out

DT = np.dtype([('p', '<f4', 3), ('n', '<f4', 3), ('uv', '<f4', 2), ('c', 'u1', 4), ('bi', 'u1', 4), ('bw', 'u1', 4)])
def load_body(cu, key):
    b = open(cu + 'p_body_%s.bin' % key, 'rb').read()
    nv, ni, fl = struct.unpack_from('<iii', b, 4)
    v = np.frombuffer(b, DT, nv, 16)
    idx = np.frombuffer(b, '<u2', ni, 16 + nv * 44).reshape(-1, 3)
    return v['p'].astype(np.float64), idx
def load_rig(cu):
    d = {}
    for ln in open(cu + 'bodyrig.txt'):
        k, v = ln.strip().split('|'); d[k] = [float(t) for t in v.split(',')]
    return d

if __name__ == '__main__':
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cu = sys.argv[1].rstrip('/') + '/'; out = sys.argv[2]; key = sys.argv[3] if len(sys.argv) > 3 else 'af1'
    P, idx = load_body(cu, key); rig = load_rig(cu)[key]
    side = {4, 10, 12, 13, 14, 15, 1}
    cols = 6; rows = (NS + cols - 1) // cols
    fig, axs = plt.subplots(rows, cols, figsize=(cols * 3.0, rows * 4.6))
    for i in range(NS):
        a = axs[i // cols][i % cols]
        res = {}
        for sgn, col in ((1, 'red'), (-1, 'blue')):
            b = np.zeros(NS); b[i] = sgn
            res[sgn] = warp(P, b, rig) if i != 0 else P * (1 + 0.06 * sgn)
        u = 2 if i in side else 0
        a.scatter(P[:, u], P[:, 1], s=0.3, c='0.7')
        a.scatter(res[1][:, u], res[1][:, 1], s=0.3, c='red', alpha=0.5)
        a.scatter(res[-1][:, u], res[-1][:, 1], s=0.3, c='blue', alpha=0.5)
        a.set_aspect('equal'); a.set_title(NAMES[i] + (' (lado)' if i in side else ''), fontsize=9); a.axis('off')
        if i in (0,): continue
    for j in range(NS, rows * cols): axs[j // cols][j % cols].axis('off')
    plt.tight_layout(); plt.savefig(out, dpi=70)
    # sanidade: NaN e inversoes
    for i in range(1, NS):
        for sgn in (1, -1):
            b = np.zeros(NS); b[i] = sgn; Q = warp(P, b, rig)
            assert np.isfinite(Q).all(), (i, sgn)
    b = np.full(NS, 0.0); b[1:] = 1.0; assert np.isfinite(warp(P, b, rig)).all()
    print('ok', out)
