"""Biblioteca de CONTEÚDO INTERNO (Plano Mestre v4, Regra 2): objetos guardados modelados com forma própria e detalhe.

Nenhum objeto aqui é cubo, esfera ou cilindro genérico: cada um tem as partes que o identificam (dobras, gola, costuras,
gargalo, tampa, rótulo, sola, cadarço...). Todos são construídos na origem com a BASE em y = 0 (onde encostam no apoio) e a
frente para +Z; quem coloca usa pm_lib.place(..., y = altura do apoio - EMB).
Cada função devolve (geo, info) onde info tem 'altura' e, quando faz sentido, pontos de encaixe.
"""
import math
import numpy as np
from pm_lib import *        # noqa


def _shade(c, k): return tuple(min(1.0, max(0.0, v * k)) for v in c[:3])


def ground(g):
    """desloca a geometria para o ponto mais baixo ficar exatamente em y = 0"""
    lo = min(P[:, 1].min() for _, P, *_ in g.arrays())
    for a in g.parts.values():
        a['P'] = [P - np.array([0, lo, 0]) for P in a['P']]
    return g


# ================================================================================================ ROUPAS DOBRADAS
def camiseta_dobrada(cor, w=0.22, d=0.27, h=0.034, estampa=None, seed=0):
    """camiseta dobrada: duas camadas com dobra frontal arredondada, mangas dobradas sobre as laterais e gola canelada"""
    g = Geo(); rng = np.random.default_rng(seed)
    h1 = h * 0.55; h2 = h - h1 + 0.001
    rbox(g, LIN, (0, h1 / 2, 0), (w, h1, d), r=min(h1 / 2 - 0.0005, 0.009), col=cor, uv=4, puff=0.002, step=0.05)
    rbox(g, LIN, (0, h1 + h2 / 2 - 0.001, -0.004), (w - 0.012, h2, d - 0.012), r=min(h2 / 2 - 0.0005, 0.008), col=_shade(cor, 1.03), uv=4, puff=0.003, step=0.05)
    top = h - 0.0005
    # mangas dobradas para dentro (abas sobre as laterais, com a bainha da manga)
    for sx in (-1, 1):
        rbox(g, LIN, (sx * (w / 2 - 0.032), top + 0.0015, -0.02), (0.05, 0.004, d * 0.55), r=0.0018, col=_shade(cor, 0.94), uv=4, step=0.05)
        g.tube(LIN, [V(sx * (w / 2 - 0.058), top + 0.0025, -0.02 - d * 0.27), V(sx * (w / 2 - 0.058), top + 0.0025, -0.02 + d * 0.27)], [0.0018, 0.0018], sides=6, col=lambda p, t: C4(_shade(cor, 0.88)))
    # gola canelada (meia-lua perto do fundo) e o recorte do decote
    a = np.linspace(math.radians(200), math.radians(340), 14)
    pts = [V(0.055 * math.cos(t), top + 0.002, -d / 2 + 0.075 + 0.045 * math.sin(t)) for t in a]
    g.tube(LIN, pts, [0.0035] * len(pts), sides=7, col=lambda p, t: C4(_shade(cor, 0.85)))
    # estampa (faixa) na frente
    if estampa is not None:
        rbox(g, LIN, (0, top + 0.0008, 0.035), (w * 0.45, 0.0016, d * 0.18), r=0.0006, col=estampa, uv=4, step=0.05)
    # vinco da dobra na frente
    g.tube(LIN, [V(-w / 2 + 0.012, h * 0.52, d / 2 - 0.0005), V(w / 2 - 0.012, h * 0.52, d / 2 - 0.0005)], [0.0012, 0.0012], sides=5, col=lambda p, t: C4(_shade(cor, 0.78)))
    return g, dict(altura=top + 0.004)


def calca_dobrada(cor=(0.22, 0.32, 0.52), w=0.24, d=0.29, h=0.042):
    """calça jeans dobrada: camadas, bolso traseiro com pesponto, cós com passadores e rebite"""
    g = Geo()
    h1 = h * 0.5
    rbox(g, LIN, (0, h1 / 2, 0), (w, h1, d), r=0.009, col=cor, uv=5, puff=0.002, step=0.05)
    rbox(g, LIN, (0, h1 + (h - h1) / 2 - 0.001, -0.003), (w - 0.008, h - h1 + 0.001, d - 0.008), r=0.009, col=_shade(cor, 1.05), uv=5, puff=0.003, step=0.05)
    top = h - 0.0005
    stitch = (0.85, 0.58, 0.25)
    # bolso traseiro (pentágono) com pesponto
    poly = [(-0.06, -0.06), (0.06, -0.06), (0.06, 0.03), (0.0, 0.055), (-0.06, 0.03)]
    extrude(g, LIN, [(x + 0.03, z + 0.01) for x, z in poly], top - 0.0004, top + 0.0022, _shade(cor, 0.93), uv=5)
    for k in range(len(poly)):
        x0, z0 = poly[k]; x1, z1 = poly[(k + 1) % len(poly)]
        g.tube(LIN, [V(x0 * 0.9 + 0.03, top + 0.0024, z0 * 0.9 + 0.01), V(x1 * 0.9 + 0.03, top + 0.0024, z1 * 0.9 + 0.01)], [0.0009, 0.0009], sides=4, col=lambda p, t: C4(stitch))
    # cós no fundo, com passadores e rebite de metal
    rbox(g, LIN, (0, top + 0.0015, -d / 2 + 0.022), (w - 0.02, 0.004, 0.03), r=0.0015, col=_shade(cor, 0.9), uv=5, step=0.05)
    for xx in (-0.07, 0.0, 0.07):
        rbox(g, LIN, (xx, top + 0.0035, -d / 2 + 0.022), (0.008, 0.002, 0.034), r=0.0008, col=_shade(cor, 0.85), uv=5)
    g.lathe(MET, (0.095, top + 0.0032, -d / 2 + 0.022), [(0, 0), (0.004, 0), (0.0045, 0.0012), (0, 0.0016)], sides=10, col=C4(BRASS))
    # costura lateral (linha clara)
    g.tube(LIN, [V(-w / 2 + 0.016, top - 0.0002, -d / 2 + 0.03), V(-w / 2 + 0.016, top - 0.0002, d / 2 - 0.03)], [0.0011, 0.0011], sides=4, col=lambda p, t: C4(stitch))
    return g, dict(altura=top + 0.0045)


def blusa_trico_dobrada(cor, w=0.24, d=0.28, h=0.05):
    """suéter de tricô dobrado: camadas grossas com nervuras do tricô e punhos canelados aparecendo na frente"""
    g = Geo()
    h1 = h * 0.5
    rbox(g, LIN, (0, h1 / 2, 0), (w, h1, d), r=0.012, col=cor, uv=7, puff=0.003, step=0.04)
    rbox(g, LIN, (0, h1 + (h - h1) / 2 - 0.001, -0.002), (w - 0.01, h - h1 + 0.001, d - 0.01), r=0.012, col=_shade(cor, 1.04), uv=7, puff=0.004, step=0.04)
    top = h - 0.0005
    # nervuras do tricô (tranças) no topo
    for xx in (-0.06, 0.0, 0.06):
        pts = [V(xx + 0.006 * math.sin(k * 1.4), top + 0.0015, -d / 2 + 0.03 + k * (d - 0.06) / 14) for k in range(15)]
        g.tube(LIN, pts, [0.0035] * 15, sides=6, col=lambda p, t: C4(_shade(cor, 0.9)))
    # punhos canelados das mangas dobradas, à frente
    for sx in (-1, 1):
        for k in range(4):
            g.tube(LIN, [V(sx * (0.035 + k * 0.009), h * 0.25, d / 2 - 0.004), V(sx * (0.035 + k * 0.009), h * 0.8, d / 2 - 0.004)], [0.003, 0.003], sides=5, col=lambda p, t: C4(_shade(cor, 0.86)))
    return g, dict(altura=top + 0.005)


def toalha_dobrada(cor, w=0.28, d=0.22, h=0.07):
    """toalha felpuda dobrada em três: dobras arredondadas e barra lisa com listras"""
    g = Geo()
    nl = 3; lh = h / nl
    for k in range(nl):
        rbox(g, LIN, (0, lh * k + lh / 2 - 0.0005 * k, 0.003 * (k % 2)), (w - 0.004 * k, lh + 0.001, d - 0.004 * k), r=lh / 2 - 0.0005, col=_shade(cor, 1 - 0.03 * k), uv=9, puff=0.003, step=0.05)
    # barra lisa e duas listras na frente das dobras (seguindo a curva da dobra)
    for k in range(nl):
        yy = lh * k + lh / 2 - 0.0005 * k; r = lh / 2 - 0.0005; zc = 0.003 * (k % 2) + (d - 0.004 * k) / 2 - r
        for dy in (-0.006, 0.006):
            zs = zc + math.sqrt(max(r * r - dy * dy, 0)) - 0.0004
            g.tube(LIN, [V(-w / 2 + 0.014, yy + dy, zs), V(w / 2 - 0.014, yy + dy, zs)], [0.0016, 0.0016], sides=5, col=lambda p, t: C4(_shade(cor, 0.7)))
    return g, dict(altura=h - 0.0015 * nl)


def pilha(dst, itens, x, y, z, yaw=0.0):
    """empilha [(geo, info)] a partir da altura y; cada peça apoiada na de baixo (0,5 mm de encaixe)"""
    yy = y - EMB
    for geo, info in itens:
        place(dst, geo, x, yy, z, yaw)
        yy += info['altura'] - EMB
    return yy


# ================================================================================================ MEIAS, ROUPA ÍNTIMA
def meia_enrolada(cor, comp=0.085, r=0.026, listra=None):
    """par de meias enrolado: rolo com o punho canelado dobrado por cima (fica deitado, apoiado na lateral)"""
    g = Geo()
    prof = [(0, 0), (r * 0.55, 0.002), (r * 0.9, 0.012), (r, 0.03), (r * 0.98, comp * 0.62), (r * 0.9, comp * 0.8), (r * 0.6, comp * 0.95), (0, comp)]
    tmp = Geo(); tmp.lathe(LIN, (0, 0, 0), prof, sides=18, col=C4(cor), uscale=2, vscale=6)
    # punho dobrado (aro mais largo, canelado) em volta de 1/3 do rolo
    cuf = [(r * 0.97, comp * 0.18), (r * 1.1, comp * 0.2), (r * 1.13, comp * 0.42), (r * 1.08, comp * 0.46), (r * 0.97, comp * 0.47)]
    tmp.lathe(LIN, (0, 0, 0), cuf, sides=18, col=C4(_shade(cor, 0.9)), uscale=8, vscale=6)
    for k in range(9):
        a = 2 * math.pi * k / 9
        tmp.tube(LIN, [V(r * 1.12 * math.cos(a), comp * 0.21, r * 1.12 * math.sin(a)), V(r * 1.12 * math.cos(a), comp * 0.44, r * 1.12 * math.sin(a))], [0.0016, 0.0016], sides=4, col=lambda p, t: C4(_shade(cor, 0.82)))
    if listra is not None:
        tmp.lathe(LIN, (0, 0, 0), [(r * 1.0, comp * 0.62), (r * 1.004, comp * 0.63), (r * 1.004, comp * 0.68), (r * 1.0, comp * 0.69)], sides=18, col=C4(listra))
    # deitado: eixo do rolo ao longo de X, encostando no apoio pela lateral do punho (maior raio)
    add_xf(g, tmp, rot_z(-math.pi / 2), (-comp / 2, r * 1.13, 0))
    return g, dict(altura=2 * r * 1.13)


def cueca_dobrada(cor, w=0.13, d=0.12, h=0.016):
    """roupa íntima dobrada: tecido com o elástico do cós aparecendo"""
    g = Geo()
    rbox(g, LIN, (0, h / 2, 0), (w, h, d), r=h / 2 - 0.0005, col=cor, uv=6, puff=0.002, step=0.04)
    rbox(g, LIN, (0, h - 0.0005 + 0.0015, -d / 2 + 0.012), (w - 0.006, 0.003, 0.016), r=0.0012, col=(0.15, 0.15, 0.16), uv=6, step=0.05)
    for xx in np.linspace(-w / 2 + 0.015, w / 2 - 0.015, 6):
        rbox(g, LIN, (xx, h + 0.0028, -d / 2 + 0.012), (0.012, 0.001, 0.004), r=0.0004, col=(0.92, 0.92, 0.92), uv=6)
    return g, dict(altura=h + 0.003)


# ================================================================================================ CABIDE E ROUPAS PENDURADAS
HANG = dict(neck=-0.045, arm_end=0.19, drop=0.045, r=0.0075)


def cabide(rail_r):
    """cabide de madeira com gancho de metal. Origem = centro do cabideiro; o arame do gancho encosta no cabideiro.
    Plano do cabide = Y-Z (as roupas ficam de lado, viradas para ±X). Devolve também a função da linha dos braços."""
    g = Geo(); hr = 0.0021; R = rail_r + hr
    # gancho: sobe pelo lado +Z encostado no tubo, passa por cima e desce do outro lado
    pts = [V(0, HANG['neck'] - 0.002, 0), V(0, -R - 0.012, 0.004), V(0, -R * 0.45, R * 0.98)]
    for a in np.linspace(math.radians(20), math.radians(205), 12):
        pts.append(V(0, R * math.sin(a), R * math.cos(a)))
    pts.append(V(0, -0.016, -R * 0.75))
    g.tube(MET, pts, [hr] * len(pts), sides=7, col=lambda p, t: C4(CHROME))
    sphere(g, MET, tuple(pts[-1]), hr * 1.3, CHROME, seg=5)
    # base do gancho (rosca) entrando na madeira
    g.tube(MET, [V(0, HANG['neck'] - 0.012, 0), V(0, HANG['neck'] + 0.004, 0)], [0.0035, 0.0035], sides=8, col=lambda p, t: C4(CHROME))
    # braços de madeira: perfil achatado, ombros arredondados
    wood = (0.80, 0.60, 0.38)
    for sz in (-1, 1):
        pts = [V(0, HANG['neck'], 0)]
        for k in range(1, 9):
            t = k / 8; z = sz * HANG['arm_end'] * t
            pts.append(V(0, HANG['neck'] - HANG['drop'] * t ** 1.15, z))
        tmp = Geo(); tmp.tube(OAK, pts, [HANG['r']] * len(pts), sides=10, col=lambda p, t: C4(wood))
        sphere(tmp, OAK, tuple(pts[-1]), HANG['r'], wood, seg=6)
        add_xf(g, tmp, np.diag([0.55, 1, 1]), (0, 0, 0))      # achatado: 8 mm de espessura x 15 mm de altura
    # barra de calça (metal) ligando as pontas por baixo
    yb = HANG['neck'] - HANG['drop'] - 0.05
    for sz in (-1, 1):
        g.tube(MET, [V(0, HANG['neck'] - HANG['drop'] * 0.93, sz * HANG['arm_end'] * 0.94), V(0, yb, sz * 0.15)], [0.0022] * 2, sides=6, col=lambda p, t: C4(CHROME))
    g.tube(MET, [V(0, yb, -0.15), V(0, yb, 0.15)], [0.0025, 0.0025], sides=6, col=lambda p, t: C4(CHROME))

    def arm_top(z):
        t = min(abs(z) / HANG['arm_end'], 1.0)
        return HANG['neck'] - HANG['drop'] * t ** 1.15 + HANG['r']
    return g, dict(arm_top=arm_top)


def _torso_rings(arm_top, comp, larg, cintura, barra, esp, n=24, gola=0.062):
    """anéis horizontais (x = espessura, z = largura) de uma roupa pendurada pelos ombros no cabide.
    No ombro, cada anel passa 0,5 mm acima do topo do braço do cabide (o tecido apoia no cabide)."""
    rings = []
    for yy in np.linspace(arm_top(gola) - 0.0005, arm_top(0.185) - 0.0005, 6):
        # z em que o topo do braço fica 0,5 mm abaixo deste anel
        lo, hi = 0.0, 0.19
        for _ in range(40):
            m = (lo + hi) / 2
            if arm_top(m) > yy - 0.0005: lo = m
            else: hi = m
        rings.append(ring_ellipse(0, yy, 0, esp * 0.75, max(lo, gola), n=n))
    y0 = rings[-1][0, 1]
    for t, rz, rx in ((0.03, larg * 1.0, esp), (0.18, larg * 0.98, esp * 1.05), (0.45, cintura, esp), (0.75, barra * 0.97, esp * 0.95), (1.0, barra, esp * 0.9)):
        rings.append(ring_ellipse(0, y0 - comp * t, 0, rx, rz, n=n))
    return rings


def camisa_pendurada(cor, arm_top, comp=0.60, manga=True, xadrez=None, botoes=True):
    """camisa no cabide (frente = +X): corpo com ombros caindo sobre os braços do cabide, gola, mangas com punho,
    carcela com botões e bolso. arm_top = função do cabide."""
    g = Geo()
    rings = _torso_rings(arm_top, comp, 0.205, 0.19, 0.2, 0.018)
    if xadrez is not None:
        c2 = xadrez
        col = lambda p, t: cor if (int((p[1] + 5) / 0.03) + int((p[2] + 5) / 0.03)) % 2 else c2
    else:
        col = cor
    loft(g, LIN, rings, col, uvs=3)
    ys = rings[5][0, 1]
    # gola: colarinho dobrado em volta do decote (com as pontas viradas para a frente)
    gl = []
    for a in np.linspace(0, 2 * math.pi, 24):
        gl.append(V(0.011 * math.cos(a), rings[0][0, 1] + 0.006, 0.064 * math.sin(a)))
    g.tube(LIN, gl, [0.006] * len(gl), sides=6, col=lambda p, t: C4(_shade(cor if not callable(cor) else (0.9, 0.9, 0.9), 0.95)))
    for sz in (-1, 1):
        tri = [V(0.012, rings[0][0, 1] + 0.004, sz * 0.012), V(0.016, rings[0][0, 1] - 0.045, sz * 0.03), V(0.013, rings[0][0, 1] + 0.002, sz * 0.062)]
        g.tube(LIN, tri, [0.004, 0.006, 0.004], sides=5, col=lambda p, t: C4(_shade(cor, 0.97)))
    # carcela + botões na frente (superfície +X)
    xf = 0.018 * 1.02
    if botoes:
        y_top = rings[0][0, 1] - 0.03
        rbox(g, LIN, (xf - 0.001, (y_top + ys - comp + 0.02) / 2, 0), (0.004, y_top - (ys - comp + 0.02), 0.024), r=0.0015, col=_shade(cor, 0.96), uv=3, step=0.1)
        for yy in np.linspace(y_top - 0.02, ys - comp + 0.06, 7):
            g.lathe(PLN, (0, 0, 0), [(0, 0), (0.0055, 0), (0.0058, 0.0015), (0.004, 0.0024), (0, 0.0024)], sides=10, col=C4((0.93, 0.92, 0.88)))
            # o último lathe foi criado na origem com eixo Y; gira para o eixo X e leva à carcela
            a = g.parts[PLN]; P = a['P'][-1]; N = a['N'][-1]
            R = rot_z(-math.pi / 2); a['P'][-1] = P @ R.T + np.array([xf + 0.0008, yy, 0]); a['N'][-1] = N @ R.T
        # bolso no peito
        rbox(g, LIN, (xf - 0.0005, ys - 0.11, 0.09), (0.003, 0.11, 0.095), r=0.0012, col=_shade(cor, 0.94), uv=3, step=0.1)
    if manga:
        for sz in (-1, 1):
            z0 = sz * 0.196; y0 = ys - 0.012
            pts = [V(0, y0, z0 * 0.93), V(0, y0 - 0.06, sz * 0.222), V(0, y0 - 0.25, sz * 0.232), V(0, y0 - 0.5, sz * 0.226)]
            tmp = Geo(); tmp.tube(LIN, pts, [0.05, 0.047, 0.042, 0.037], sides=12, col=(lambda p, t: C4(col(p, t))) if callable(col) else (lambda p, t: C4(cor)))
            # punho
            pc = [V(0, y0 - 0.495, sz * 0.226), V(0, y0 - 0.56, sz * 0.225)]
            tmp.tube(LIN, pc, [0.039, 0.038], sides=12, col=lambda p, t: C4(_shade(cor if not callable(cor) else (0.85, 0.85, 0.85), 0.92)))
            disc(tmp, LIN, (0, y0 - 0.56, sz * 0.225), 0.038, rings=2, seg=12, col=_shade(cor if not callable(cor) else (0.8, 0.8, 0.8), 0.6))
            a = tmp.parts[LIN]; a['N'][-1] = -a['N'][-1]; a['T'][-1] = a['T'][-1][:, [0, 2, 1]]
            add_xf(g, tmp, np.diag([0.42, 1, 1]), (0, 0, 0))
    return g


def vestido_pendurado(cor, arm_top, comp=0.92, estampa=None):
    """vestido de alças no cabide: corpete justo, cintura marcada com faixa e saia rodada com pregas"""
    g = Geo()
    rings = _torso_rings(arm_top, 0.30, 0.17, 0.135, 0.15, 0.03)
    loft(g, LIN, rings, cor, cap1=False, uvs=3)
    yb = rings[-1][0, 1]
    # faixa da cintura
    belt = [ring_ellipse(0, yb + 0.012, 0, 0.0285, 0.152, n=24), ring_ellipse(0, yb - 0.012, 0, 0.0285, 0.152, n=24)]
    loft(g, LIN, belt, _shade(cor, 0.75), uvs=3)
    # saia: anéis com pregas (raio ondulado) abrindo até a barra
    sk = []
    for t in np.linspace(0, 1, 9):
        a = np.linspace(0, 2 * math.pi, 44, endpoint=False)
        rz = 0.15 + 0.085 * t ** 1.2; rx = 0.03 + 0.02 * t ** 1.2
        wob = 1 + 0.06 * t * np.sin(a * 11)
        sk.append(np.stack([rx * wob * np.cos(a), np.full(44, yb - 0.0 - (comp - 0.30) * t), rz * wob * np.sin(a)], 1))
    loft(g, LIN, sk, cor, cap0=False, cap1=True, uvs=3)
    if estampa is not None:
        # faixas estampadas na saia: anéis colados na superfície (mesmas pregas), 0,6 mm por fora
        for t0 in (0.55, 0.62, 0.9):
            band = []
            for t in (t0, t0 + 0.03):
                a = np.linspace(0, 2 * math.pi, 44, endpoint=False)
                rz = 0.15 + 0.085 * t ** 1.2; rx = 0.03 + 0.02 * t ** 1.2; wob = 1 + 0.06 * t * np.sin(a * 11)
                band.append(np.stack([(rx * wob + 0.0006) * np.cos(a), np.full(44, yb - (comp - 0.30) * t), (rz * wob + 0.0006) * np.sin(a)], 1))
            loft(g, LIN, band, estampa, cap0=False, cap1=False, uvs=3)
    return g


# ================================================================================================ CALÇADOS
def tenis(cor, sola=(0.95, 0.95, 0.93), cadarco=(0.97, 0.97, 0.97), lado=1, L=0.25):
    """tênis: sola com borda e cravos, cabedal costurado, biqueira, língua, ilhoses e cadarço cruzado, contraforte"""
    g = Geo()
    def width(t):     # t = 0 calcanhar .. 1 bico
        return 0.034 + 0.018 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.8 + (0.004 if t > 0.55 else 0)
    n = 22; poly = []
    for k in range(n):
        t = k / (n - 1); z = -L / 2 + L * t
        poly.append((lado * 0.004 * math.sin(math.pi * t) + width(t), z))
    for k in range(n - 1, -1, -1):
        t = k / (n - 1); z = -L / 2 + L * t
        poly.append((lado * 0.004 * math.sin(math.pi * t) - width(t), z))
    poly = poly[::-1]
    hs = 0.024
    extrude(g, PLN, poly, 0.0, hs, sola, uv=4, bevel=0.002)
    # faixa de cor na sola e cravos no bico
    extrude(g, PLN, [(x * 1.004, z * 1.003) for x, z in poly], hs * 0.45, hs * 0.62, _shade(sola, 0.8), uv=4)
    # cabedal: anéis em arco sobre a sola, do calcanhar ao bico
    rings = []
    m = 14
    for k in range(m):
        t = 0.02 + 0.96 * k / (m - 1); z = -L / 2 + L * t; w = width(t) * 0.97
        hh = 0.062 if t < 0.25 else (0.062 - 0.012 * (t - 0.25) / 0.2 if t < 0.45 else max(0.022, 0.05 - 0.06 * (t - 0.45)))
        a = np.linspace(0, math.pi, 13)
        xs = lado * 0.004 * math.sin(math.pi * t) + w * np.cos(a); ys = hs - 0.002 + hh * np.sin(a) ** 0.85
        r = np.stack([xs, ys, np.full(13, z)], 1)
        rings.append(np.vstack([r, np.array([[xs[-1], hs - 0.002, z], [xs[0], hs - 0.002, z]])[::-1][:0]]))
    loft(g, LIN, rings, cor, uvs=6)
    # biqueira (outra cor) e contraforte do calcanhar
    rings2 = [np.c_[r[:, 0] * 1.03, (r[:, 1] - hs) * 1.03 + hs, r[:, 2]] for r in rings[-4:]]
    loft(g, PLN, rings2, _shade(sola, 0.9), uvs=6)
    rings3 = [np.c_[r[:, 0] * 1.04, np.minimum((r[:, 1] - hs) * 1.04 + hs, hs + 0.04), r[:, 2]] for r in rings[:3]]
    loft(g, PLN, rings3, _shade(cor, 0.7), uvs=6)
    # boca do tênis: forro escuro rente ao cabedal e debrum acolchoado em volta; língua saindo da boca
    zc = -L / 2 + L * 0.2
    ysurf = hs - 0.002 + 0.062
    oval = [(0.026 * math.cos(a) + lado * 0.0025, zc + 0.042 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 20, endpoint=False)]
    extrude(g, LIN, oval, ysurf - 0.004, ysurf + 0.0008, (0.16, 0.16, 0.18), uv=4)
    pts = [V(x, ysurf + 0.0008, z) for x, z in oval] + [V(oval[0][0], ysurf + 0.0008, oval[0][1])]
    g.tube(LIN, pts, [0.0045] * len(pts), sides=6, col=lambda p, t: C4(_shade(cor, 0.8)))
    tg = Geo(); rbox(tg, LIN, (0, 0, 0), (0.045, 0.006, 0.075), r=0.0028, col=_shade(cor, 0.95), uv=4)
    add_xf(g, tg, rot_x(math.radians(-38)), (lado * 0.003, hs + 0.064, zc + 0.065))
    # ilhoses e cadarço cruzado sobre o peito do pé
    eye = []
    for k in range(5):
        t = 0.36 + 0.07 * k; z = -L / 2 + L * t
        hh = 0.062 - 0.012 * min(1, (t - 0.25) / 0.2) if t < 0.45 else max(0.022, 0.05 - 0.06 * (t - 0.45))
        yy = hs - 0.002 + hh * 0.97
        for sx in (-1, 1):
            p = V(sx * 0.016 + lado * 0.003, yy - 0.003, z)
            g.lathe(MET, tuple(p), [(0.0028, 0), (0.0036, 0.0008), (0.0028, 0.0016)], sides=8, col=C4(CHROME))
            eye.append(p)
    for k in range(4):
        a = eye[2 * k]; b = eye[2 * k + 1]; c = eye[2 * k + 2]; d = eye[2 * k + 3]
        for p0, p1 in ((a, d), (b, c)):
            g.tube(LIN, [p0 + V(0, 0.0025, 0), (p0 + p1) / 2 + V(0, 0.0045, 0), p1 + V(0, 0.0025, 0)], [0.0018] * 3, sides=5, col=lambda p, t: C4(cadarco))
    # laço
    top = eye[-2] + V(0.016, 0.004, 0)
    for s in (-1, 1):
        g.tube(LIN, [top, top + V(s * 0.02, 0.006, 0.006), top + V(s * 0.028, 0.0, -0.004), top + V(0, 0.001, 0)], [0.0018] * 4, sides=5, col=lambda p, t: C4(cadarco))
    return g, dict(altura=hs + 0.065)


def sapatilha(cor, L=0.235, lado=1):
    """sapatilha de bico fino: sola fina com salto baixo, cabedal baixo com debrum e lacinho na frente"""
    g = Geo()
    def width(t): return 0.031 + 0.016 * math.sin(math.pi * min(1.0, t * 1.1)) ** 0.9 - (0.02 * (t - 0.85) / 0.15 if t > 0.85 else 0)
    n = 22; poly = []
    for k in range(n):
        t = k / (n - 1); poly.append((width(t), -L / 2 + L * t))
    for k in range(n - 1, -1, -1):
        t = k / (n - 1); poly.append((-width(t), -L / 2 + L * t))
    poly = poly[::-1]
    extrude(g, PLN, poly, 0.0, 0.008, (0.2, 0.16, 0.14), uv=4, bevel=0.0015)
    # salto baixo
    extrude(g, PLN, [(0.022 * math.cos(a), -L / 2 + 0.03 + 0.024 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)], 0.0, 0.0085, (0.15, 0.12, 0.1), uv=4)
    rings = []
    for k in range(12):
        t = 0.02 + 0.96 * k / 11; z = -L / 2 + L * t; w = width(t) * 0.98
        hh = 0.038 if t < 0.3 else max(0.012, 0.038 - 0.03 * (t - 0.3) / 0.7)
        a = np.linspace(0, math.pi, 11)
        rings.append(np.stack([w * np.cos(a), 0.007 + hh * np.sin(a) ** 0.9, np.full(11, z)], 1))
    loft(g, LIN, rings, cor, uvs=6)
    # abertura (forro) e debrum
    zc = -L / 2 + L * 0.32
    extrude(g, LIN, [(0.03 * math.cos(a), zc + 0.075 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 22, endpoint=False)], 0.033, 0.0395, (0.85, 0.75, 0.62), uv=4)
    pts = [V(0.03 * math.cos(a), 0.0395, zc + 0.075 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 23)]
    g.tube(LIN, pts, [0.0018] * len(pts), sides=5, col=lambda p, t: C4(_shade(cor, 0.7)))
    # laço
    zb = -L / 2 + L * 0.73; yb = 0.007 + (0.038 - 0.03 * (0.73 - 0.3) / 0.7) - 0.001
    for s in (-1, 1):
        g.tube(LIN, [V(0, yb, zb), V(s * 0.012, yb + 0.004, zb + 0.004), V(s * 0.016, yb + 0.002, zb - 0.004), V(0, yb, zb)], [0.003, 0.004, 0.004, 0.003], sides=6, col=lambda p, t: C4(_shade(cor, 0.8)))
    return g, dict(altura=0.05)


# ================================================================================================ CAIXAS
def caixa_organizadora(cor, w=0.40, d=0.32, h=0.17, etiqueta='lã'):
    """caixa organizadora de plástico com tampa encaixada, pegadores vazados (rebaixo escuro) e porta-etiqueta"""
    g = Geo()
    rbox(g, PLN, (0, h * 0.46, 0), (w, h * 0.92, d), r=0.014, col=cor, uv=2, step=0.1)
    # tampa com aba e nervuras
    rbox(g, PLN, (0, h * 0.92 + 0.009 - 0.0005, 0), (w + 0.008, 0.018, d + 0.008), r=0.008, col=_shade(cor, 0.92), uv=2, step=0.1)
    for k in range(3):
        rbox(g, PLN, (0, h * 0.92 + 0.0185, -d / 4 + k * d / 4), (w - 0.06, 0.004, 0.01), r=0.0018, col=_shade(cor, 0.88), uv=2)
    # pegadores (rebaixos) nas laterais e porta-etiqueta na frente
    for sx in (-1, 1):
        rbox(g, PLN, (sx * (w / 2 + 0.0006), h * 0.7, 0), (0.003, 0.03, 0.09), r=0.0012, col=_shade(cor, 0.45), uv=2)
    rbox(g, PLN, (0, h * 0.55, d / 2 + 0.0012), (0.11, 0.05, 0.003), r=0.0012, col=(0.95, 0.93, 0.86), uv=2)
    for k in range(3):
        rbox(g, PLN, (-0.02 + k * 0.016, h * 0.55, d / 2 + 0.0028), (0.012, 0.004, 0.0006), r=0.0002, col=(0.25, 0.25, 0.3), uv=2)
    return g, dict(altura=h * 0.92 + 0.0215)


# ================================================================================================ COZINHA: GARRAFAS, CAIXAS, POTES
def _lathe(g, key, c, prof, sides, col, rot=None):
    if rot is None: g.lathe(key, c, prof, sides=sides, col=C4(col)); return
    tmp = Geo(); tmp.lathe(key, (0, 0, 0), prof, sides=sides, col=C4(col)); add_xf(g, tmp, rot, c)


def garrafa(cor, rotulo, tampa, h=0.25, r=0.034, gargalo=0.012, vidro=False):
    """garrafa PET/vidro: base com pés, corpo, ombro, gargalo com anel e tampa estriada, rótulo envolvendo o corpo"""
    g = Geo()
    key = GLASS if vidro else PLN
    a = 0.85 if not vidro else 0.55
    prof = [(0, 0), (r * 0.7, 0), (r * 0.92, 0.004), (r, 0.012), (r, h * 0.55), (r * 0.97, h * 0.62), (r * 0.75, h * 0.72), (gargalo * 1.35, h * 0.84),
            (gargalo, h * 0.88), (gargalo, h * 0.93)]
    tmp = Geo(); tmp.lathe(key, (0, 0, 0), prof, sides=20, col=C4(cor, a)); add_xf(g, tmp)
    # anel do gargalo e tampa estriada
    g.lathe(PLN, (0, h * 0.885, 0), [(gargalo * 0.98, 0), (gargalo * 1.5, 0.0015), (gargalo * 1.5, 0.004), (gargalo * 0.98, 0.0045)], sides=16, col=C4(tampa))
    g.lathe(PLN, (0, h * 0.925, 0), [(0, 0), (gargalo * 1.18, 0), (gargalo * 1.2, 0.002), (gargalo * 1.2, h * 0.07), (gargalo * 1.1, h * 0.075), (0, h * 0.075)], sides=16, col=C4(tampa))
    for k in range(14):
        an = 2 * math.pi * k / 14
        g.tube(PLN, [V(gargalo * 1.21 * math.cos(an), h * 0.93, gargalo * 1.21 * math.sin(an)), V(gargalo * 1.21 * math.cos(an), h * 0.99, gargalo * 1.21 * math.sin(an))], [0.0009] * 2, sides=4, col=lambda p, t: C4(_shade(tampa, 0.8)))
    # rótulo (faixa envolvente 0,4 mm por fora) com uma faixa de outra cor
    g.lathe(PLN, (0, 0, 0), [(r + 0.0004, h * 0.18), (r + 0.0004, h * 0.48)], sides=20, col=C4(rotulo[0]))
    g.lathe(PLN, (0, 0, 0), [(r + 0.0007, h * 0.29), (r + 0.0007, h * 0.36)], sides=20, col=C4(rotulo[1]))
    return g, dict(altura=h + 0.0)


def caixa_leite(cor=(0.95, 0.95, 0.93), marca=(0.20, 0.45, 0.80), w=0.07, d=0.07, h=0.19):
    """caixa de leite longa-vida: corpo com vincos, topo em telhado com a aba selada, tampa de rosca e estampa"""
    g = Geo()
    rbox(g, PLN, (0, h * 0.42, 0), (w, h * 0.84, d), r=0.003, col=cor, uv=3, step=0.05)
    # telhado (duas abas inclinadas) e aba selada no topo
    ang = math.radians(32); rise = d / 2 * math.tan(ang)
    for s in (-1, 1):
        tmp = Geo(); rbox(tmp, PLN, (0, 0, 0), (w * 0.999, 0.003, d / 2 / math.cos(ang) + 0.004), r=0.001, col=cor, uv=3)
        add_xf(g, tmp, rot_x(s * ang), (0, h * 0.84 + rise / 2 - 0.001, s * d / 4))
    rbox(g, PLN, (0, h * 0.84 + rise + 0.005, 0), (w * 0.999, 0.014, 0.003), r=0.0008, col=cor, uv=3)
    # laterais do telhado (triângulos dobrados) como abas finas
    for sx in (-1, 1):
        extrude(g, PLN, [(sx * w / 2 - 0.0015, -d / 2), (sx * w / 2 + 0.0015, -d / 2), (sx * w / 2 + 0.0015, d / 2), (sx * w / 2 - 0.0015, d / 2)], h * 0.84 - 0.001, h * 0.84 + 0.004, _shade(cor, 0.95))
    # tampa de rosca na aba da frente
    tmp = Geo(); tmp.lathe(PLN, (0, 0, 0), [(0, 0), (0.011, 0), (0.0115, 0.002), (0.0115, 0.012), (0, 0.012)], sides=14, col=C4((0.95, 0.80, 0.20)))
    nrm = np.array([0, math.cos(ang), math.sin(ang)])
    add_xf(g, tmp, rot_x(ang), np.array([0, h * 0.84 + rise / 2 - 0.001, d / 4]) + nrm * 0.001)
    # estampa: faixa de cor e "vaquinha" (manchas)
    rbox(g, PLN, (0, h * 0.4, d / 2 + 0.0003), (w * 0.94, h * 0.32, 0.001), r=0.0004, col=marca, uv=3)
    rbox(g, PLN, (0, h * 0.4, -d / 2 - 0.0003), (w * 0.94, h * 0.32, 0.001), r=0.0004, col=marca, uv=3)
    rbox(g, PLN, (0, h * 0.62, d / 2 + 0.0007), (w * 0.6, 0.02, 0.001), r=0.0004, col=(0.95, 0.95, 0.95), uv=3)
    return g, dict(altura=h * 0.84 + rise + 0.012)


def ovo(r=0.0215, cor=(0.93, 0.84, 0.70)):
    """ovo: perfil assimétrico (ponta fina em cima), em pé"""
    g = Geo(); n = 14; prof = []
    for k in range(n + 1):
        t = k / n; a = math.pi * t
        y = r * 1.33 * (1 - math.cos(a)); rr = r * math.sin(a) * (1 - 0.18 * t)
        prof.append((rr, y))
    g.lathe(PLN, (0, 0, 0), prof, sides=14, col=C4(cor))
    return g, dict(altura=r * 2.66)


def bandeja_ovos(n_x=3, n_z=2, cor=(0.80, 0.86, 0.88), cheio=None):
    """porta-ovos da porta da geladeira: bandeja com cavidades (copinhos) e ovos encaixados"""
    g = Geo(); p = 0.05
    w = n_x * p + 0.01; d = n_z * p + 0.01
    rbox(g, PLN, (0, 0.006, 0), (w, 0.012, d), r=0.004, col=cor, uv=2)
    eggs = []
    for i in range(n_x):
        for j in range(n_z):
            x = -w / 2 + 0.005 + p * (i + 0.5); z = -d / 2 + 0.005 + p * (j + 0.5)
            g.lathe(PLN, (x, 0.012 - 0.0005, z), [(0.018, 0), (0.0205, 0.0015), (0.0175, 0.012), (0.0172, 0.013), (0.0155, 0.0135)], sides=14, col=C4(_shade(cor, 0.92)))
            if cheio is None or (i * n_z + j) in cheio:
                eg, ei = ovo(cor=(0.93, 0.84, 0.70) if (i + j) % 3 else (0.96, 0.94, 0.90))
                place(g, eg, x, 0.012 + 0.0005, z)
    return g, dict(altura=0.012 + 0.057)


def maca(cor=(0.75, 0.12, 0.12), r=0.036):
    """maçã: perfil com covinha no topo e na base, cabinho e folha"""
    g = Geo(); prof = []
    n = 16
    for k in range(n + 1):
        t = k / n; a = math.pi * t
        rr = r * math.sin(a) * (1.0 + 0.10 * math.sin(a) ** 2 - 0.12 * t)
        y = r * (1 - math.cos(a)) * 0.92
        prof.append((rr, y))
    prof[0] = (0, r * 0.12); prof[-1] = (0, prof[-1][1] - r * 0.22)
    def col(p, t): return None
    tmp = Geo(); tmp.lathe(PLN, (0, 0, 0), prof, sides=18, col=C4(cor))
    # rajado: cor varia com o ângulo
    a_ = tmp.parts[PLN]; P = a_['P'][-1]; C = a_['C'][-1].copy()
    ang = np.arctan2(P[:, 2], P[:, 0]); k = 0.85 + 0.15 * np.sin(ang * 7) * np.clip(P[:, 1] / (2 * r), 0, 1)
    C[:, :3] = np.clip(np.array(cor) * k[:, None] + np.array([0.15, 0.12, 0.0]) * (1 - np.clip(P[:, 1] / r, 0, 1))[:, None], 0, 1); a_['C'][-1] = C
    add_xf(g, tmp)
    ytop = max(p[1] for p in prof)
    g.tube(OAK, [V(0, ytop - 0.012, 0), V(0.002, ytop + 0.006, 0), V(0.005, ytop + 0.014, 0.001)], [0.0016, 0.0014, 0.0012], sides=5, col=lambda p, t: C4((0.35, 0.25, 0.12)))
    lf = Geo(); extrude(lf, PLN, [(0, 0), (0.008, 0.008), (0.012, 0.022), (0.006, 0.03), (0, 0.032), (-0.006, 0.03), (-0.012, 0.022), (-0.008, 0.008)], -0.0006, 0.0006, (0.25, 0.55, 0.20))
    add_xf(g, lf, rot_x(math.radians(-60)) @ rot_y(0.8), (0.003, ytop + 0.004, 0.0))
    ground(g)
    return g, dict(altura=ytop + 0.016)


def laranja(r=0.037):
    """laranja: levemente achatada, casca com poros (relevo na cor) e o umbigo com a marca do cabo"""
    g = Geo(); prof = []
    n = 16
    for k in range(n + 1):
        a = math.pi * k / n; prof.append((r * math.sin(a), r * 0.94 * (1 - math.cos(a))))
    tmp = Geo(); tmp.lathe(PLN, (0, 0, 0), prof, sides=22, col=C4((0.98, 0.55, 0.10)))
    a_ = tmp.parts[PLN]; P = a_['P'][-1]; C = a_['C'][-1].copy()
    h = np.sin(P[:, 0] * 900) * np.sin(P[:, 1] * 870) * np.sin(P[:, 2] * 910)
    C[:, :3] = np.clip(np.array([0.98, 0.55, 0.10]) * (0.92 + 0.08 * h)[:, None], 0, 1); a_['C'][-1] = C
    add_xf(g, tmp)
    g.lathe(PLN, (0, r * 1.88 - 0.0005, 0), [(0, 0.001), (0.004, 0.0005), (0.0045, 0.0)], sides=8, col=C4((0.45, 0.50, 0.15)))
    for k in range(5):
        a = 2 * math.pi * k / 5
        g.tube(PLN, [V(0, r * 1.88 - 0.0004, 0), V(0.006 * math.cos(a), r * 1.88 - 0.0012, 0.006 * math.sin(a))], [0.0012, 0.0008], sides=4, col=lambda p, t: C4((0.40, 0.45, 0.12)))
    return g, dict(altura=r * 1.88 + 0.001)


def tomate(r=0.032):
    """tomate: gomos (lóbulos) no contorno, sépalas em estrela e cabinho"""
    g = Geo(); n = 14; sides = 24
    tmp = Geo(); prof = [(r * math.sin(math.pi * k / n), r * 0.82 * (1 - math.cos(math.pi * k / n))) for k in range(n + 1)]
    tmp.lathe(PLN, (0, 0, 0), prof, sides=sides, col=C4((0.85, 0.12, 0.08)))
    a_ = tmp.parts[PLN]; P = a_['P'][-1]
    ang = np.arctan2(P[:, 2], P[:, 0]); rad = np.hypot(P[:, 0], P[:, 2])
    k = 1 + 0.07 * np.cos(ang * 5) * np.clip(rad / r, 0, 1)
    P[:, 0] *= k; P[:, 2] *= k; a_['P'][-1] = P
    add_xf(g, tmp)
    yt = r * 1.64
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        g.tube(PLN, [V(0, yt - 0.001, 0), V(0.007 * math.cos(a), yt - 0.0003, 0.007 * math.sin(a)), V(0.013 * math.cos(a), yt - 0.003, 0.013 * math.sin(a))], [0.0024, 0.002, 0.0008], sides=4, col=lambda p, t: C4((0.20, 0.45, 0.15)))
    g.tube(PLN, [V(0, yt - 0.002, 0), V(0, yt + 0.006, 0.001)], [0.0016, 0.0013], sides=5, col=lambda p, t: C4((0.25, 0.45, 0.15)))
    return g, dict(altura=yt + 0.006)


def banana_penca(n=3, L=0.17):
    """penca de bananas: frutos curvos de seção pentagonal, pontas escuras, unidos no cabo (deitada)"""
    g = Geo()
    for i in range(n):
        off = (i - (n - 1) / 2) * 0.03; tilt = (i - (n - 1) / 2) * 0.12
        pts = []; rad = []
        for k in range(12):
            t = k / 11; a = (t - 0.5) * 1.6
            x = math.sin(a) * L * 0.62; y = (1 - math.cos(a)) * L * 0.35
            pts.append(V(x * math.cos(tilt), y, off + x * math.sin(tilt)))
            rad.append(0.0175 * (0.55 + 0.45 * math.sin(math.pi * min(1, t * 1.15)) ** 0.6))
        base_y = min(p[1] - r for p, r in zip(pts, rad))
        pts = [p - V(0, base_y, 0) for p in pts]
        tmp = Geo(); tmp.tube(PLN, pts, rad, sides=5, col=lambda p, t: C4((0.98, 0.85, 0.25) if 0.08 < t < 0.95 else (0.35, 0.28, 0.10)))
        add_xf(g, tmp)
    # cabo comum da penca
    e = V(-L * 0.62 * math.sin(0.8), (1 - math.cos(0.8)) * L * 0.35, 0)
    g.tube(PLN, [e + V(0, -0.002 + 0.0, -0.03), e + V(-0.02, 0.012, 0.0), e + V(0, -0.002, 0.03)], [0.009, 0.01, 0.009], sides=6, col=lambda p, t: C4((0.55, 0.50, 0.20)))
    return g, dict(altura=0.06)


def cenoura(L=0.15):
    """cenoura: raiz afunilada com anéis, ponta fina e rama de folhas (deitada)"""
    g = Geo(); pts = []; rad = []
    for k in range(10):
        t = k / 9; pts.append(V(-L / 2 + L * t, 0, 0.004 * math.sin(t * 3))); rad.append(0.014 * (1 - t) ** 0.8 + 0.0015)
    m = max(rad)
    pts = [p + V(0, m, 0) for p in pts]
    for k in range(len(rad)):
        pts[k] = pts[k] - V(0, m - rad[k], 0)
    g.tube(PLN, pts, rad, sides=10, col=lambda p, t: C4((0.95, 0.50, 0.12) if int(t * 22) % 3 else (0.85, 0.42, 0.10)))
    root = pts[0]
    sphere(g, PLN, tuple(root), rad[0] * 0.98, (0.80, 0.45, 0.12), seg=8, sy=1.0)     # coroa (topo da raiz)
    for k in range(6):
        a = (k - 2.5) * 0.25
        g.tube(PLN, [root + V(0.002, 0.0, 0), root + V(-0.03, 0.006 + 0.004 * k % 3, a * 0.05), root + V(-0.07, 0.008, a * 0.12)], [0.0028, 0.002, 0.001], sides=4, col=lambda p, t: C4((0.25, 0.55, 0.18)))
    return g, dict(altura=2 * m)


def alface(r=0.07):
    """pé de alface: folhas em camadas (conchas onduladas) abrindo de dentro para fora"""
    g = Geo()
    for layer in range(4):
        nl = 5 + layer; rr = r * (0.45 + 0.18 * layer); hh = r * (1.1 - 0.12 * layer)
        for k in range(nl):
            a0 = 2 * math.pi * (k + 0.5 * layer) / nl
            rings = []
            for j in range(6):
                t = j / 5
                cx = math.cos(a0) * rr * t * 0.6; cz = math.sin(a0) * rr * t * 0.6; y = 0.004 + hh * math.sin(t * math.pi * 0.55)
                ww = 0.012 + 0.03 * math.sin(t * math.pi) * (1 + 0.15 * layer)
                wav = 0.004 * math.sin(j * 2.3 + k)
                tx, tz = -math.sin(a0), math.cos(a0)
                rings.append(np.array([[cx + tx * ww, y + wav, cz + tz * ww], [cx + math.cos(a0) * 0.004, y + 0.006, cz + math.sin(a0) * 0.004],
                                       [cx - tx * ww, y - wav, cz - tz * ww], [cx - math.cos(a0) * 0.004, y - 0.002, cz - math.sin(a0) * 0.004]]))
            loft(g, LIN, rings, (0.45 + 0.08 * layer, 0.75, 0.30 - 0.04 * layer), cap0=False, cap1=False, uvs=6)
    g.lathe(PLN, (0, 0, 0), [(0, 0), (0.018, 0), (0.02, 0.012), (0, 0.016)], sides=10, col=C4((0.85, 0.90, 0.65)))
    return g, dict(altura=r * 1.1)


def pote_tampa(cor_pote=(0.92, 0.94, 0.95), cor_tampa=(0.30, 0.55, 0.85), w=0.15, d=0.11, h=0.07, comida=(0.80, 0.35, 0.15)):
    """pote plástico retangular com tampa de travas, comida aparecendo pelas paredes translúcidas"""
    g = Geo()
    rings = [np.c_[np.array(rounded_rect(w * 0.94, d * 0.94, 0.012))[:, 0], np.zeros(24), np.array(rounded_rect(w * 0.94, d * 0.94, 0.012))[:, 1]],
             np.c_[np.array(rounded_rect(w, d, 0.014))[:, 0], np.full(24, h * 0.85), np.array(rounded_rect(w, d, 0.014))[:, 1]]]
    loft(g, PLN, rings, cor_pote, uvs=3)
    # comida dentro (nível visível) e tampa com borda e 4 travas
    rbox(g, PLN, (0, h * 0.31 + 0.0003, 0), (w * 0.88, h * 0.62, d * 0.86), r=0.01, col=comida, uv=4, puff=0.0)
    rbox(g, PLN, (0, h * 0.85 + 0.007 - 0.0005, 0), (w + 0.006, 0.014, d + 0.006), r=0.006, col=cor_tampa, uv=3)
    for sx in (-1, 1):
        rbox(g, PLN, (sx * (w / 2 + 0.004), h * 0.8, 0), (0.004, 0.024, 0.03), r=0.0015, col=_shade(cor_tampa, 0.85), uv=3)
    for sz in (-1, 1):
        rbox(g, PLN, (0, h * 0.8, sz * (d / 2 + 0.004)), (0.04, 0.024, 0.004), r=0.0015, col=_shade(cor_tampa, 0.85), uv=3)
    return g, dict(altura=h * 0.85 + 0.0135)


def queijo_cunha(r=0.075, h=0.05, ang=0.9):
    """fatia de queijo (cunha) com casca e furos, sobre um pratinho de madeira"""
    g = Geo()
    _lathe(g, OAK, (0, 0, 0), [(0, 0), (0.09, 0), (0.095, 0.004), (0.093, 0.009), (0, 0.009)], 24, (0.80, 0.60, 0.38))
    a = np.linspace(-ang / 2, ang / 2, 9)
    poly = [(0.0 - 0.03, 0.0)] + [(-0.03 + r * math.cos(t), r * math.sin(t)) for t in a]
    extrude(g, PLN, poly, 0.0085, 0.0085 + h, (0.98, 0.85, 0.40), bevel=0.002)
    for t in a[1:-1:2]:
        rbox(g, PLN, (-0.03 + (r + 0.0006) * math.cos(t), 0.0085 + h / 2, (r + 0.0006) * math.sin(t)), (0.002, h * 0.96, 0.012), r=0.0008, col=(0.92, 0.70, 0.25), uv=2,
             rot=-t)
    for (px, pz, pr) in ((0.02, 0.0, 0.006), (0.032, 0.012, 0.004), (0.01, -0.008, 0.0035)):
        g.lathe(PLN, (px, 0.0085 + h + 0.0002, pz), [(0, -0.0008), (pr, -0.0003), (pr, 0.0004)], sides=10, col=C4((0.88, 0.70, 0.30)))
    return g, dict(altura=0.0085 + h)


def frios_bandeja(cor=(0.92, 0.62, 0.62)):
    """frios fatiados (presunto) em bandeja com filme: fatias dobradas sobrepostas e etiqueta"""
    g = Geo(); w, d = 0.15, 0.10
    rbox(g, PLN, (0, 0.008, 0), (w, 0.016, d), r=0.004, col=(0.15, 0.15, 0.17), uv=2)
    for k in range(5):
        tmp = Geo(); rbox(tmp, PLN, (0, 0, 0), (0.1, 0.004, 0.075), r=0.0018, col=_shade(cor, 1 - 0.03 * k), uv=4, puff=0.002)
        add_xf(g, tmp, rot_z(math.radians(10)), (-0.035 + k * 0.018, 0.016 + 0.003 + 0.004 * min(k, 2) + 0.0028 * max(0, k - 2), 0))
    rbox(g, PLN, (0.035, 0.04 - 0.0005, 0.02), (0.05, 0.002, 0.035), r=0.0008, col=(0.98, 0.98, 0.95), uv=2)
    return g, dict(altura=0.04)


def lata(cor, faixa, h=0.105, r=0.028):
    """lata de refrigerante: fundo côncavo, corpo, pescoço afunilado, borda dobrada, tampa com anel de abrir"""
    g = Geo()
    prof = [(0, 0.004), (r * 0.75, 0.0), (r * 0.95, 0.003), (r, 0.01), (r, h * 0.86), (r * 0.82, h * 0.97), (r * 0.82, h)]
    g.lathe(MET, (0, 0, 0), prof, sides=22, col=C4(cor))
    g.lathe(MET, (0, 0, 0), [(r + 0.0004, h * 0.3), (r + 0.0004, h * 0.55)], sides=22, col=C4(faixa))
    g.lathe(MET, (0, h - 0.0008, 0), [(r * 0.82, 0), (r * 0.86, 0.002), (r * 0.8, 0.003), (0, 0.0015)], sides=22, col=C4(CHROME))
    tmp = Geo(); extrude(tmp, MET, [(-0.006, -0.004), (0.006, -0.004), (0.008, 0.01), (0, 0.014), (-0.008, 0.01)], 0, 0.0008, CHROME)
    add_xf(g, tmp, None, (0, h + 0.0015, 0.0))
    return g, dict(altura=h + 0.003)


def iogurte(cor=(0.97, 0.97, 0.95), tampa=(0.85, 0.30, 0.45), r=0.026, h=0.065):
    """copo de iogurte: copinho troncocônico com aba, tampa de alumínio e rótulo"""
    g = Geo()
    g.lathe(PLN, (0, 0, 0), [(0, 0), (r * 0.78, 0), (r, h * 0.95), (r * 1.15, h * 0.97), (r * 1.15, h), (0, h)], sides=18, col=C4(cor))
    g.lathe(MET, (0, h - 0.0004, 0), [(r * 1.16, 0), (r * 1.16, 0.0012), (0, 0.0014)], sides=18, col=C4(tampa))
    g.lathe(PLN, (0, 0, 0), [(r * 0.85 + 0.0005, h * 0.25), (r * 0.94 + 0.0005, h * 0.7)], sides=18, col=C4(tampa))
    return g, dict(altura=h + 0.002)


def manteigueira():
    """pote de manteiga com tampa e a manteiga cortada aparecendo pela tampa transparente"""
    g = Geo(); w, d = 0.11, 0.075
    rbox(g, PLN, (0, 0.012, 0), (w, 0.024, d), r=0.006, col=(0.95, 0.95, 0.92), uv=2)
    rbox(g, PLN, (-0.012, 0.024 + 0.016 - 0.0005, 0), (0.07, 0.032, 0.05), r=0.003, col=(0.98, 0.90, 0.55), uv=2)
    rbox(g, PLN, (0.035, 0.024 + 0.016 - 0.0005, 0), (0.025, 0.026, 0.05), r=0.004, col=(0.98, 0.90, 0.55), uv=2, puff=0.002)
    return g, dict(altura=0.056)


def bisnaga(cor, tampa, h=0.17, r=0.026):
    """bisnaga de molho (ketchup/mostarda): corpo apertável oval, tampa flip com bico"""
    g = Geo()
    tmp = Geo(); tmp.lathe(PLN, (0, 0, 0), [(0, 0), (r * 0.9, 0), (r, 0.01), (r * 1.02, h * 0.5), (r * 0.92, h * 0.8), (r * 0.55, h * 0.88), (0, h * 0.88)], sides=18, col=C4(cor))
    add_xf(g, tmp, np.diag([1.0, 1.0, 0.72]))
    g.lathe(PLN, (0, h * 0.88 - 0.0008, 0), [(0, 0), (r * 0.62, 0), (r * 0.62, 0.016), (r * 0.3, 0.02), (0.004, 0.028), (0, 0.028)], sides=14, col=C4(tampa))
    g.lathe(PLN, (0, 0, 0), [(r + 0.0004, h * 0.3), (r * 1.02 + 0.0006, h * 0.55)], sides=18, col=C4((0.96, 0.96, 0.94))) if False else None
    tmp = Geo(); tmp.lathe(PLN, (0, 0, 0), [(r * 1.0 + 0.0005, h * 0.3), (r * 1.02 + 0.0005, h * 0.55)], sides=18, col=C4((0.96, 0.96, 0.94)))
    add_xf(g, tmp, np.diag([1.0, 1.0, 0.72]))
    return g, dict(altura=h * 0.88 + 0.027)


# ================================================================================================ FREEZER
def forma_gelo(cor=(0.75, 0.88, 0.95), nx=7, nz=2):
    """forma de gelo: bandeja com divisórias e cubos de gelo com cantos arredondados em cada cavidade"""
    g = Geo(); p = 0.034; w = nx * p + 0.01; d = nz * p + 0.01; h = 0.03
    rbox(g, PLN, (0, 0.002, 0), (w, 0.004, d), r=0.0015, col=cor, uv=2)
    for sx in (-1, 1): rbox(g, PLN, (sx * (w / 2 - 0.002), h / 2, 0), (0.004, h, d), r=0.0012, col=cor, uv=2)
    for sz in (-1, 1): rbox(g, PLN, (0, h / 2, sz * (d / 2 - 0.002)), (w, h, 0.004), r=0.0012, col=cor, uv=2)
    for i in range(1, nx): rbox(g, PLN, (-w / 2 + 0.005 + i * p, h * 0.45, 0), (0.002, h * 0.9, d - 0.004), r=0.0008, col=cor, uv=2)
    for j in range(1, nz): rbox(g, PLN, (0, h * 0.45, -d / 2 + 0.005 + j * p), (w - 0.004, h * 0.9, 0.002), r=0.0008, col=cor, uv=2)
    for i in range(nx):
        for j in range(nz):
            rbox(g, GLASS, (-w / 2 + 0.005 + p * (i + 0.5), 0.004 + 0.012 - 0.0005, -d / 2 + 0.005 + p * (j + 0.5)), (p - 0.006, 0.024, p - 0.006), r=0.006, col=(0.88, 0.95, 1.0), uv=2)
    return g, dict(altura=h)


def saco_congelado(cor=(0.20, 0.55, 0.30), w=0.16, d=0.21, h=0.035):
    """pacote de vegetais congelados: saco estufado com soldas serrilhadas nas pontas e estampa"""
    g = Geo()
    rbox(g, PLN, (0, h / 2, 0), (w, h, d - 0.03), r=h / 2 - 0.001, col=cor, uv=3, puff=0.008, step=0.03)
    for sz in (-1, 1):
        zz = sz * (d / 2 - 0.012)
        rbox(g, PLN, (0, 0.006, zz), (w * 0.98, 0.003, 0.03), r=0.001, col=_shade(cor, 0.85), uv=3)
        for k in range(16):
            x = -w * 0.47 + k * w * 0.94 / 15
            g.tube(PLN, [V(x, 0.0073, zz - 0.012), V(x, 0.0073, zz + 0.012)], [0.0006] * 2, sides=3, col=lambda p, t: C4(_shade(cor, 0.7)))
    # ervilhas/legumes desenhados na frente (pequenos discos)
    for k in range(7):
        x = -0.05 + (k % 4) * 0.033; z = -0.03 + (k // 4) * 0.04
        hx = w / 2 - (h / 2 - 0.001); hz = (d - 0.03) / 2 - (h / 2 - 0.001)
        f = max(0.0, (1 - (x / (w / 2)) ** 2) * (1 - (z / ((d - 0.03) / 2)) ** 2))
        g.lathe(PLN, (x, h + 0.008 * f - 0.0004, z), [(0, 0.0004), (0.008, 0.0), (0.0085, 0.0008), (0, 0.0012)], sides=10, col=C4((0.45, 0.80, 0.30) if k % 2 else (0.95, 0.60, 0.15)))
    ground(g)
    return g, dict(altura=h + 0.016)


def pote_sorvete(cor=(0.95, 0.85, 0.70), tampa=(0.55, 0.25, 0.15)):
    """pote de sorvete de 2 L: balde troncocônico com alça de encaixe, tampa com aba e rótulo"""
    g = Geo(); r0, r1, h = 0.062, 0.075, 0.10
    g.lathe(PLN, (0, 0, 0), [(0, 0), (r0, 0), (r1, h), (r1 + 0.004, h), (r1 + 0.004, h + 0.004), (0, h + 0.004)], sides=24, col=C4(cor))
    g.lathe(PLN, (0, h - 0.002, 0), [(r1 + 0.005, 0), (r1 + 0.006, 0.006), (r1 - 0.002, 0.012), (0, 0.013)], sides=24, col=C4(tampa))
    g.lathe(PLN, (0, 0, 0), [(r0 + (r1 - r0) * 0.2 + 0.0005, h * 0.2), (r0 + (r1 - r0) * 0.75 + 0.0005, h * 0.75)], sides=24, col=C4(tampa))
    return g, dict(altura=h + 0.011)


# ================================================================================================ FORNO
def bolo_forma(r=0.11, h_forma=0.05, cor_bolo=(0.82, 0.55, 0.25)):
    """bolo assando na forma redonda com furo (forma de pudim/anel): massa crescida com topo dourado e rachadura"""
    g = Geo()
    prof = [(0.025, h_forma), (0.022, 0.0), (r - 0.004, 0.0), (r, h_forma), (r + 0.006, h_forma + 0.002)]
    g.lathe(MET, (0, 0, 0), [(0.02, 0.0), (r, 0.0), (r + 0.004, h_forma), (r + 0.009, h_forma + 0.002), (r + 0.009, h_forma + 0.004)], sides=28, col=C4((0.55, 0.56, 0.58)))
    g.lathe(MET, (0, 0, 0), [(0.016, h_forma + 0.02), (0.02, 0.0)], sides=16, col=C4((0.55, 0.56, 0.58)))
    # massa: anel com domo, topo mais escuro
    dome = [(0.0215, h_forma + 0.004), (0.03, h_forma + 0.022), (0.06, h_forma + 0.034), (0.09, h_forma + 0.026), (r + 0.003, h_forma + 0.004), (r - 0.002, h_forma * 0.5), (0.023, h_forma * 0.5)]
    tmp = Geo(); tmp.lathe(PLN, (0, 0, 0), dome[::-1], sides=28, col=C4(cor_bolo))
    a_ = tmp.parts[PLN]; P = a_['P'][-1]; C = a_['C'][-1].copy()
    top = np.clip((P[:, 1] - h_forma) / 0.03, 0, 1)
    C[:, :3] = np.array(cor_bolo) * (1 - 0.35 * top)[:, None]; a_['C'][-1] = C
    add_xf(g, tmp)
    for k in range(9):
        a = 2 * math.pi * k / 9 + 0.3
        g.tube(PLN, [V(0.058 * math.cos(a), h_forma + 0.0335, 0.058 * math.sin(a)), V(0.066 * math.cos(a + 0.25), h_forma + 0.0325, 0.066 * math.sin(a + 0.25))], [0.002] * 2, sides=4, col=lambda p, t: C4((0.45, 0.25, 0.10)))
    return g, dict(altura=h_forma + 0.036)


# ================================================================================================ LIMPEZA (gabinete da pia)
def detergente(cor=(0.30, 0.75, 0.35), h=0.18):
    """frasco de detergente: corpo oval com cintura, tampa flip com bico e rótulo"""
    g = Geo(); r = 0.03
    tmp = Geo(); tmp.lathe(PLN, (0, 0, 0), [(0, 0), (r * 0.9, 0), (r, 0.01), (r, h * 0.35), (r * 0.82, h * 0.5), (r, h * 0.66), (r * 0.9, h * 0.82), (r * 0.45, h * 0.88), (0, h * 0.88)], sides=18, col=C4(cor, 0.9))
    add_xf(g, tmp, np.diag([1.0, 1.0, 0.6]))
    g.lathe(PLN, (0, h * 0.88 - 0.0008, 0), [(0, 0), (0.013, 0), (0.013, 0.016), (0.006, 0.02), (0.003, 0.03), (0, 0.03)], sides=14, col=C4((0.95, 0.95, 0.95)))
    tmp = Geo(); tmp.lathe(PLN, (0, 0, 0), [(r * 1.0 + 0.0005, h * 0.12), (r * 1.0 + 0.0005, h * 0.32)], sides=18, col=C4((0.95, 0.95, 0.90)))
    add_xf(g, tmp, np.diag([1.0, 1.0, 0.6]))
    return g, dict(altura=h * 0.88 + 0.029)


def borrifador(cor=(0.30, 0.55, 0.90), h=0.22):
    """borrifador: frasco com ombro, gatilho, bico e tubo; rótulo"""
    g = Geo(); r = 0.036
    g.lathe(PLN, (0, 0, 0), [(0, 0), (r * 0.9, 0), (r, 0.012), (r, h * 0.55), (r * 0.6, h * 0.66), (0.014, h * 0.7), (0, h * 0.7)], sides=18, col=C4(cor, 0.85))
    g.lathe(PLN, (0, 0, 0), [(r + 0.0005, h * 0.15), (r + 0.0005, h * 0.45)], sides=18, col=C4((0.96, 0.96, 0.92)))
    head = (0.95, 0.95, 0.95)
    g.lathe(PLN, (0, h * 0.7 - 0.0008, 0), [(0, 0), (0.017, 0), (0.017, 0.02), (0.012, 0.03), (0, 0.03)], sides=14, col=C4(head))
    rbox(g, PLN, (0, h * 0.7 + 0.04, 0.015), (0.03, 0.03, 0.06), r=0.008, col=head, uv=2)
    rbox(g, PLN, (0, h * 0.7 + 0.04, 0.047), (0.016, 0.014, 0.008), r=0.003, col=(0.9, 0.3, 0.2), uv=2)
    tmp = Geo(); rbox(tmp, PLN, (0, 0, 0), (0.014, 0.05, 0.01), r=0.004, col=head, uv=2)
    add_xf(g, tmp, rot_x(math.radians(-20)), (0, h * 0.7 + 0.008, 0.03))
    return g, dict(altura=h * 0.7 + 0.055)


def esponja(cor=(0.98, 0.85, 0.25), fibra=(0.20, 0.55, 0.30)):
    """esponja dupla face: espuma macia com poros e a fibra abrasiva verde por cima, cintura"""
    g = Geo(); w, d = 0.10, 0.07
    rbox(g, PLN, (0, 0.012, 0), (w, 0.024, d), r=0.006, col=cor, uv=8, puff=0.002)
    rbox(g, LIN, (0, 0.024 + 0.004 - 0.0005, 0), (w, 0.008, d), r=0.002, col=fibra, uv=12)
    for k in range(12):
        x = -0.04 + (k % 6) * 0.016; z = -0.02 + (k // 6) * 0.04
        g.lathe(PLN, (x, 0.012, d / 2 + 0.0002), [(0, -0.002), (0.002, 0.0)], sides=6, col=C4(_shade(cor, 0.75))) if False else None
        rbox(g, PLN, (x, 0.008 + (k % 3) * 0.005, d / 2 + 0.0003), (0.003, 0.003, 0.001), r=0.0006, col=_shade(cor, 0.7), uv=2)
    return g, dict(altura=0.031)


def pano_dobrado(cor=(0.92, 0.92, 0.88), xadrez=(0.80, 0.25, 0.25)):
    """pano de prato dobrado em quatro: camadas, barra com listras e a etiqueta"""
    g = Geo(); w, d = 0.16, 0.12
    for k in range(3):
        rbox(g, LIN, (0.002 * k, 0.003 + 0.0055 * k, 0.001 * k), (w - 0.003 * k, 0.0065, d - 0.003 * k), r=0.003, col=cor, uv=6, puff=0.001)
    top = 0.003 + 0.011 + 0.00325
    for dz in (-0.03, -0.022, 0.022, 0.03):
        rbox(g, LIN, (0.004, top, dz), (w - 0.012, 0.001, 0.004), r=0.0004, col=xadrez, uv=6)
    return g, dict(altura=top + 0.0005)


def lixeira(cor=(0.85, 0.85, 0.85), h=0.24, r=0.09):
    """lixeira de pedal pequena: balde metálico, pedal, tampa com dobradiça atrás e saco de lixo aparecendo na borda"""
    g = Geo()
    g.lathe(MET, (0, 0, 0), [(0, 0.006), (r * 0.92, 0.006), (r * 0.95, 0.0), (r, 0.01), (r, h), (0, h)][:-1] + [(r * 0.97, h)], sides=26, col=C4(cor)) if False else \
        g.lathe(MET, (0, 0, 0), [(0, 0.0), (r * 0.95, 0.0), (r, 0.01), (r, h - 0.004), (r * 1.02, h)], sides=26, col=C4(cor))
    disc(g, MET, (0, 0.0, 0), r * 0.95, rings=2, seg=26, col=cor); a = g.parts[MET]; a['N'][-1] = -a['N'][-1]; a['T'][-1] = a['T'][-1][:, [0, 2, 1]]
    # base plástica preta e pedal
    g.lathe(PLN, (0, 0, 0), [(r + 0.0005, 0.0), (r + 0.004, 0.002), (r + 0.004, 0.02), (r + 0.0005, 0.022)], sides=26, col=C4((0.12, 0.12, 0.13)))
    rbox(g, PLN, (0, 0.012, r + 0.018), (0.06, 0.012, 0.035), r=0.004, col=(0.12, 0.12, 0.13), uv=2)
    # saco aparecendo na borda e tampa abaulada com dobradiça
    g.lathe(PLN, (0, h - 0.012, 0), [(r * 0.99, 0.0), (r * 1.035, 0.004), (r * 1.035, 0.012)], sides=26, col=C4((0.15, 0.15, 0.18)))
    g.lathe(MET, (0, h - 0.0005, 0), [(r * 1.04, 0), (r * 1.04, 0.008), (r * 0.8, 0.026), (0, 0.032)], sides=26, col=C4(_shade(cor, 1.05)))
    g.tube(PLN, [V(-0.02, h + 0.004, -r - 0.004), V(0.02, h + 0.004, -r - 0.004)], [0.005, 0.005], sides=8, col=lambda p, t: C4((0.12, 0.12, 0.13)))
    return g, dict(altura=h + 0.032)


# ================================================================================================ LOUÇA E MESA (aparador)
def prato(r=0.11, cor=(0.97, 0.97, 0.95), borda=(0.25, 0.40, 0.60)):
    """prato raso: pé (anel), fundo, aba levantada e friso colorido na borda"""
    g = Geo()
    prof = [(0, 0.004), (r * 0.42, 0.004), (r * 0.44, 0.0), (r * 0.5, 0.0), (r * 0.52, 0.004), (r * 0.62, 0.005), (r * 0.9, 0.014), (r, 0.018),
            (r * 0.99, 0.02), (r * 0.88, 0.0165), (r * 0.6, 0.0085), (0, 0.0085)]
    g.lathe(GLZ, (0, 0, 0), prof, sides=32, col=C4(cor))
    g.lathe(GLZ, (0, 0, 0), [(r * 0.93, 0.0175), (r * 0.965, 0.0195)], sides=32, col=C4(borda))
    return g, dict(altura=0.009)


def tigela(r=0.07, h=0.05, cor=(0.86, 0.58, 0.42)):
    """tigela de cerâmica com pé e borda arredondada"""
    g = Geo()
    g.lathe(GLZ, (0, 0, 0), [(0, 0.004), (r * 0.42, 0.004), (r * 0.45, 0.0), (r * 0.55, 0.0), (r * 0.6, 0.006), (r * 0.9, h * 0.6), (r, h), (r * 0.97, h + 0.003),
                             (r * 0.92, h), (r * 0.82, h * 0.6), (r * 0.5, h * 0.25), (0, h * 0.22)], sides=28, col=C4(cor))
    return g, dict(altura=h + 0.003)


def xicara(cor=(0.95, 0.95, 0.93), r=0.032, h=0.05):
    """xícara com alça (de lado) apoiada no pires"""
    g = Geo()
    g.lathe(GLZ, (0, 0, 0), [(0, 0.003), (0.03, 0.003), (0.032, 0.0), (0.05, 0.0), (0.062, 0.008), (0.06, 0.01), (0.03, 0.007), (0, 0.007)], sides=26, col=C4(cor))
    y0 = 0.007 - 0.0005
    g.lathe(GLZ, (0, y0, 0), [(0, 0.002), (r * 0.6, 0.002), (r * 0.62, 0.0), (r * 0.8, 0.0), (r * 0.95, h * 0.4), (r, h), (r * 0.95, h), (r * 0.88, h * 0.4), (0, h * 0.1)],
            sides=24, col=C4(cor))
    pts = [V(r * 0.97, y0 + h * 0.8, 0), V(r + 0.016, y0 + h * 0.78, 0), V(r + 0.02, y0 + h * 0.5, 0), V(r + 0.012, y0 + h * 0.25, 0), V(r * 0.9, y0 + h * 0.25, 0)]
    g.tube(GLZ, pts, [0.0035] * len(pts), sides=7, col=lambda p, t: C4(cor))
    return g, dict(altura=y0 + h)


def organizador_talheres(cor=(0.82, 0.66, 0.46)):
    """organizador de madeira com divisórias, garfos, facas e colheres deitados nos compartimentos"""
    g = Geo(); w, d, h = 0.26, 0.30, 0.04
    rbox(g, OAK, (0, 0.003, 0), (w, 0.006, d), r=0.002, col=cor, uv=2)
    for sx in (-1, 1): rbox(g, OAK, (sx * (w / 2 - 0.004), h / 2, 0), (0.008, h, d), r=0.002, col=cor, uv=2)
    for sz in (-1, 1): rbox(g, OAK, (0, h / 2, sz * (d / 2 - 0.004)), (w, h, 0.008), r=0.002, col=cor, uv=2)
    cw = (w - 0.008) / 4
    for k in range(1, 4): rbox(g, OAK, (-w / 2 + 0.004 + k * cw, h * 0.45, 0), (0.005, h * 0.9, d - 0.008), r=0.0015, col=cor, uv=2)
    st = CHROME
    for k, kind in enumerate(('garfo', 'faca', 'colher', 'colher')):
        xc = -w / 2 + 0.004 + cw * (k + 0.5)
        for n in range(3):
            x = xc + (n - 1) * 0.012; y = 0.006 + 0.0025 + n * 0.0012
            # cabo
            g.tube(MET, [V(x, y, -0.12), V(x, y, 0.02)], [0.0035, 0.003], sides=6, col=lambda p, t: C4(st))
            if kind == 'faca':
                rbox(g, MET, (x, y, 0.07), (0.012, 0.0015, 0.1), r=0.0006, col=st, uv=2)
            elif kind == 'garfo':
                rbox(g, MET, (x, y, 0.04), (0.014, 0.0015, 0.04), r=0.0006, col=st, uv=2)
                for tq in range(4):
                    rbox(g, MET, (x - 0.0055 + tq * 0.0037, y, 0.075), (0.0018, 0.0015, 0.032), r=0.0005, col=st, uv=2)
            else:
                tmp = Geo(); tmp.lathe(MET, (0, 0, 0), [(0, 0), (0.016, 0.0015), (0.017, 0.004), (0, 0.0012)], sides=14, col=C4(st))
                add_xf(g, tmp, np.diag([0.75, 1, 1.1]), (x, y - 0.0018, 0.06))
    return g, dict(altura=h)


def castical_vela(cor_vela=(0.95, 0.92, 0.82)):
    """castiçal de latão (base, haste torneada, copinho) com vela, pavio e um pingo de cera"""
    g = Geo()
    g.lathe(MET, (0, 0, 0), [(0, 0), (0.035, 0), (0.036, 0.004), (0.022, 0.012), (0.008, 0.02), (0.012, 0.05), (0.007, 0.08), (0.016, 0.1), (0.018, 0.108),
                             (0.012, 0.11), (0, 0.11)], sides=22, col=C4(BRASS))
    g.lathe(PLN, (0, 0.105, 0), [(0, 0), (0.0105, 0), (0.0105, 0.13), (0.008, 0.134), (0, 0.135)], sides=16, col=C4(cor_vela))
    g.tube(PLN, [V(0, 0.233, 0), V(0.001, 0.248, 0)], [0.0012, 0.0009], sides=4, col=lambda p, t: C4((0.12, 0.10, 0.08)))
    g.tube(PLN, [V(0.0103, 0.236, 0), V(0.0108, 0.215, 0.001), V(0.0106, 0.2, 0.0)], [0.0018, 0.0016, 0.0011], sides=5, col=lambda p, t: C4(cor_vela))
    return g, dict(altura=0.248)
