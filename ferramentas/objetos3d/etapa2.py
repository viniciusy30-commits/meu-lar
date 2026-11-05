"""ETAPA 2 do Plano Mestre (v4): cama de casal, sofá de 3 lugares, geladeira, fogão com forno e pia de cozinha.
Cada modelo segue a ficha do PDF (construção visual; física, animação e interação; apoios v4; conteúdo interno v4).
Convenções de extras (lidas pelo jogo, Glb.kt / Renderer3D.kt):
  * anim.gatilho = "ocupado" + anim.assento = "IP_sentar_N" -> almofada daquele lugar afunda quando ele está ocupado
  * anim.verbos = ["Acender", "Apagar"] -> texto do botão da peça (em vez de Abrir/Fechar)
  * extras.efeito = {"tipo": "chama"|"agua"|"luz"|"vapor", "quando": "<peça>"} -> efeito só com a peça acionada
  * extras.mostrar_quando = ["porta"...] -> conteúdo interno só desenhado com a peça aberta (otimização Android)
  * IP_deitar_* (acao deitar, dormir=true) ; IP_lavar (acao lavar, alavanca=<peça>)
Uso: python3 etapa2.py <pasta de saída> [modelo...]
"""
import sys, os, math, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pm_lib import *        # noqa
import conteudo as CT

WHITE = (0.95, 0.95, 0.94); DARK = (0.12, 0.12, 0.13); INOX = (0.78, 0.80, 0.82)
SEAT_SIT = 0.013            # quanto o traseiro afunda na almofada


def flip_last(g, key):
    a = g.parts[key]; a['N'][-1] = -a['N'][-1]; a['T'][-1] = a['T'][-1][:, [0, 2, 1]]


def emissive(g):
    """zera as normais (no jogo e no GLB: material emissivo, sem luz)"""
    for a in g.parts.values(): a['N'] = [N * 0 for N in a['N']]


def piping_v(g, key, x0, x1, y0, y1, z, r, col, rad=0.03, axis='z'):
    """vivo (cordão) em volta de um retângulo vertical no plano X-Y (axis='z') ou Z-Y (axis='x')"""
    pts = []
    w = x1 - x0; h = y1 - y0; cx = (x0 + x1) / 2; cy = (y0 + y1) / 2
    for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ccx = cx + sx * (w / 2 - rad); ccy = cy + sy * (h / 2 - rad)
        for i in range(7):
            a = math.radians(a0 + 90 * i / 6); u = ccx + rad * math.cos(a); v = ccy + rad * math.sin(a)
            pts.append(V(u, v, z) if axis == 'z' else V(z, v, u))
    pts.append(pts[0])
    g.tube(key, pts, [r] * len(pts), sides=6, col=lambda p, t: C4(col), vscale=4.0)


# ================================================================================================ SOFÁ DE 3 LUGARES
def sofa():
    W, D = 1.76, 0.78; armW = 0.15; armH = 0.56
    legH = 0.075; deck1 = 0.255; seatH = 0.115; seat_top = deck1 + seatH
    zb = -D / 2; zbk = zb + 0.17                  # frente do encosto (estrutura)
    Wi = W - 2 * armW; sw = Wi / 3
    lean = math.radians(13); bch = 0.40; bct = 0.15
    SIT_Z = 0.41
    fab = (0.36, 0.46, 0.52); fabD = (0.28, 0.36, 0.41); wood = (0.52, 0.36, 0.22)
    M = G.Model('int_sofa3', meta('int_sofa3', 'Sofá de 3 lugares', 'sala', 'assentos', 'funcional',
               dict(tipo='estatico', massa=55.0, motivo='móvel grande ancorado; almofadas sem física independente (ficha)'),
               estados=['livre', 'ocupado por lugar'], grade=[2, 1],
               ocupacao='por lugar: IP_sentar_0/1/2 têm ocupação própria (não senta onde já tem alguém)',
               interacoes=[dict(acao='sentar', pontos=['IP_sentar_0', 'IP_sentar_1', 'IP_sentar_2'], cancelavel=True,
                                sequencia=['aproximar', 'girar', 'sentar (animação)', 'sentado (laço)', 'levantar'])]))
    fr = M.node('estrutura'); g = fr.geo
    # 6 pés de madeira torneados (sob os braços e no meio), do piso até a base
    for x in (-W / 2 + 0.075, 0.0, W / 2 - 0.075):
        for z in (zb + 0.07, D / 2 - 0.09):
            g.lathe(OAK, (x, 0, z), [(0, 0), (0.016, 0), (0.017, 0.004), (0.019, legH * 0.6), (0.022, legH + 0.0005), (0, legH + 0.0005)], sides=14, col=C4(wood))
    # braços (estrutura lateral contínua do pé ao topo), estofados com bordas arredondadas e vivo na frente
    for sx in (-1, 1):
        cx = sx * (W / 2 - armW / 2)
        rbox(g, LIN, (cx, legH + (armH - legH) / 2, 0), (armW, armH - legH, D), r=0.05, col=fab, uv=3, puff=0.006, step=0.08)
        piping_v(g, LIN, cx - armW / 2 + 0.05, cx + armW / 2 - 0.05, legH + 0.05, armH - 0.05, D / 2 + 0.002, 0.005, fabD, rad=0.02)
        piping_v(g, LIN, -D / 2 + 0.01, D / 2 - 0.01, legH + 0.012, armH - 0.008, cx + sx * (armW / 2 + 0.0035), 0.005, fabD, rad=0.045, axis='x') if False else None
    # base (plataforma estofada entre os braços)
    rbox(g, LIN, (0, legH + (deck1 - legH) / 2, -0.008), (Wi + 0.002, deck1 - legH + 0.0005, D - 0.016), r=0.02, col=fabD, uv=3, step=0.1)
    g.tube(LIN, [V(-Wi / 2, legH + 0.03, D / 2 - 0.016 + 0.002), V(Wi / 2, legH + 0.03, D / 2 - 0.016 + 0.002)], [0.005, 0.005], sides=6, col=lambda p, t: C4(fab))
    # encosto (estrutura estofada) e parte traseira modelada (costuras, vivo, faixa inferior)
    back_top = 0.70
    rbox(g, LIN, (0, (deck1 - 0.001 + back_top) / 2 + 0.0, zb + 0.085), (Wi + 0.002, back_top - deck1 + 0.002, 0.17), r=0.04, col=fab, uv=3, puff=0.004, step=0.1)
    rbox(g, LIN, (0, (legH + back_top) / 2, zb + 0.012), (Wi + 0.002, back_top - legH - 0.01, 0.024), r=0.008, col=fab, uv=3, step=0.15)
    for x in (-Wi / 6, Wi / 6):
        g.tube(LIN, [V(x, legH + 0.02, zb - 0.0005), V(x, back_top - 0.03, zb - 0.0005)], [0.0028, 0.0028], sides=5, col=lambda p, t: C4(fabD))
    g.tube(LIN, [V(-Wi / 2, back_top - 0.012, zb + 0.004), V(Wi / 2, back_top - 0.012, zb + 0.004)], [0.0055, 0.0055], sides=6, col=lambda p, t: C4(fabD))
    rng = np.random.default_rng(3)
    for i in range(3):
        cx = -Wi / 2 + sw * (i + 0.5)
        # almofada de assento (nó próprio: afunda quando o lugar está ocupado; pivô na base)
        cu = M.node('almofada_assento_%d' % i, (cx, deck1, 0), extras=dict(anim=dict(tipo='escala', eixo=[0, 1, 0], min=1.0, max=0.9, dur=0.6,
                    curva='suave', gatilho='ocupado', assento='IP_sentar_%d' % i, estado_inicial=1.0)))
        gc = cu.geo; zc = (zbk + D / 2) / 2; dep = D / 2 - zbk + 0.001
        rbox(gc, LIN, (cx, deck1 + seatH / 2 - 0.0005, zc), (sw + 0.001, seatH, dep), r=0.03, col=tuple(np.array(fab) * rng.uniform(0.98, 1.02)), uv=3,
             puff=0.010 + rng.uniform(-0.002, 0.002), step=0.06)
        piping(gc, LIN, cx, seat_top - 0.012, zc, sw - 0.012, dep - 0.012, 0.0045, fabD, rad=0.03)
        piping(gc, LIN, cx, deck1 + 0.012, zc, sw - 0.012, dep - 0.012, 0.0045, fabD, rad=0.03)
        # almofada de encosto: base apoiada no assento, topo encostado na estrutura do encosto
        tmp = Geo()
        rbox(tmp, LIN, (0, bch / 2, -bct / 2), (sw - 0.004, bch, bct), r=0.045, col=tuple(np.array(fab) * rng.uniform(1.0, 1.04)), uv=3, puff=0.014, step=0.06)
        piping(tmp, LIN, 0, bch / 2, -bct / 2, sw - 0.016, bct - 0.012, 0.0045, fabD, rad=0.04) if False else None
        R = rot_x(-lean)
        top_back = R @ V(0, bch, 0)                       # canto de trás de cima depois de inclinar
        base_z = zbk - top_back[2] + 0.0005
        add_xf(g, tmp, R, (cx, seat_top + 0.0 - 0.006, base_z))
    M.empty('COL_base', (0, seat_top / 2, 0), extras=dict(shape='box', size=[Wi, seat_top, D], bloqueia=True, camada='movel',
            nota='base + assentos; a frente do assento é o limite (espaço de aproximação livre)'))
    for sx in (-1, 1):
        M.empty('COL_braco_' + ('D' if sx > 0 else 'E'), (sx * (W / 2 - armW / 2), armH / 2, 0), extras=dict(shape='box', size=[armW, armH, D], bloqueia=True, camada='movel'))
    M.empty('COL_encosto', (0, back_top / 2, zb + 0.085), extras=dict(shape='box', size=[Wi, back_top, 0.17], bloqueia=True, camada='movel'))
    M.empty('SURF_assentos', (0, seat_top, 0.1), extras=dict(shape='box', size=[Wi, 0, 0.5], recebe='objetos leves'))
    for i in range(3):
        cx = -Wi / 2 + sw * (i + 0.5)
        M.empty('IP_sentar_%d' % i, (cx, 0, SIT_Z), extras=dict(acao='sentar', aproximacao=[cx, 0, SIT_Z + 0.42], inicio=[cx, 0, SIT_Z + 0.12],
                assento_y=seat_top - SEAT_SIT, olhar='+Z', almofada='almofada_assento_%d' % i))
    M.bake_ao(maxd=0.22, strength=0.55)
    return finish(M)


# ================================================================================================ CAMA DE CASAL
def _drape(e, ytop_in, th, R, yb, s):
    """perfil (desloc. horizontal, y) da superfície de cima de um edredom; s = comprimento de arco a partir do centro"""
    Rin = R - th; a = e - Rin
    out = []
    for rr, yt in ((R, ytop_in + th), (Rin, ytop_in)):
        S = abs(s)
        if S <= a: off = S; y = yt
        elif S <= a + rr * math.pi / 2:
            ph = (S - a) / rr; off = a + rr * math.sin(ph); y = yt - rr * (1 - math.cos(ph))
        else:
            off = a + rr; y = yt - rr - (S - a - rr * math.pi / 2)
        out.append((off, max(y, yb)))
    return out


def cama():
    MW, ML, MH = 1.16, 1.62, 0.20; rt = 0.035
    y_sl = 0.17; MT = y_sl + MH                       # topo das ripas / topo do colchão
    sheet_top = MT + 0.003
    hzP = ML / 2 + rt / 2; hxP = MW / 2 + rt / 2      # centro dos postes
    wood = (0.62, 0.44, 0.28); woodD = (0.48, 0.33, 0.21)
    M = G.Model('int_cama_casal', meta('int_cama_casal', 'Cama de casal', 'quarto', 'camas', 'funcional',
               dict(tipo='estatico', massa=75.0, motivo='estrutura ancorada; colchão e roupa de cama sem física'),
               estados=['livre', 'sentado na borda', 'deitado', 'dormindo'], grade=[2, 2],
               ocupacao='por lado: IP_deitar_E e IP_deitar_D (não deita onde já tem alguém)', salva='lado ocupado e sono (item.st "sono=<lado>")',
               interacoes=[dict(acao='deitar/dormir', pontos=['IP_deitar_E', 'IP_deitar_D'], cancelavel=True,
                                sequencia=['aproximar', 'alinhar', 'sentar na borda', 'deitar', 'deitado (laço)', 'dormir', 'despertar', 'sentar', 'levantar'])]))
    fr = M.node('estrutura'); g = fr.geo
    # postes (pés): de pé no piso; cabeceira sobe até 0,95
    for sx in (-1, 1):
        for sz, hh in ((-1, 0.95), (1, 0.32)):
            rbox(g, OAK, (sx * hxP, hh / 2, sz * hzP), (0.056, hh, 0.056), r=0.008, col=wood, uv=1.5, step=0.2)
            sphere(g, OAK, (sx * hxP, hh, sz * hzP), 0.031, wood, seg=8, sy=0.5)
    # laterais, travessa da cabeceira e peseira (presas nos postes)
    for sx in (-1, 1):
        rbox(g, OAK, (sx * hxP, 0.21, 0), (rt, 0.16, 2 * hzP - 0.055), r=0.006, col=wood, uv=1.5, step=0.3)
    for sz in (-1, 1):
        rbox(g, OAK, (0, 0.21, sz * hzP), (2 * hxP - 0.055, 0.16, rt), r=0.006, col=wood, uv=1.5, step=0.3)
    # estrado: sarrafos de apoio nas laterais, viga central com 2 pés, ripas
    yl0 = y_sl - 0.015 - 0.02
    for sx in (-1, 1):
        rbox(g, OAK, (sx * (MW / 2 - 0.01 + 0.00025), yl0 + 0.01, 0), (0.0205, 0.02, ML), r=0.002, col=woodD, uv=1.5)
    rbox(g, OAK, (0, yl0 + 0.01, 0), (0.05, 0.02, ML + 0.001), r=0.003, col=woodD, uv=1.5)
    for zz in (-ML / 4, ML / 4):
        g.lathe(OAK, (0, 0, zz), [(0, 0), (0.02, 0), (0.02, yl0 + 0.0005), (0, yl0 + 0.0005)], sides=10, col=C4(woodD))
    nsl = 15
    for k in range(nsl):
        z = -ML / 2 + 0.05 + k * (ML - 0.1) / (nsl - 1)
        rbox(g, OAK, (0, y_sl - 0.0075 - 0.00025, z), (MW - 0.004, 0.015, 0.07), r=0.003, col=(0.80, 0.66, 0.46), uv=1.5)
    # colchão (sobre as ripas), com vivo e respiros na lateral
    rbox(g, LIN, (0, y_sl + MH / 2 - 0.0005, 0), (MW, MH, ML), r=0.035, col=(0.94, 0.94, 0.92), uv=3, puff=0.004, step=0.15)
    piping(g, LIN, 0, y_sl + 0.012, 0, MW - 0.012, ML - 0.012, 0.0055, (0.75, 0.78, 0.82), rad=0.035)
    for sx in (-1, 1):
        for zz in (-0.3, 0.3):
            tmp = Geo(); tmp.lathe(MET, (0, 0, 0), [(0.006, 0), (0.009, 0.0015), (0.009, 0.0025), (0.006, 0.003)], sides=12, col=C4(CHROME))
            add_xf(g, tmp, rot_z(-sx * math.pi / 2), (sx * (MW / 2 - 0.001), y_sl + 0.07, zz))
    # lençol de baixo (cobre o topo e desce 7 cm pelos lados)
    rbox(g, LIN, (0, sheet_top - 0.035, 0), (MW + 0.006, 0.07, ML + 0.006), r=0.034, col=(0.97, 0.97, 0.96), uv=3, step=0.15)
    # edredom: casca com espessura (3 cm) apoiada no lençol, caindo pelos lados e pelo pé; dobrado perto dos travesseiros
    e = MW / 2 + 0.003; th = 0.03; Rr = 0.05; yb = 0.23
    zt = -ML / 2 + 0.47; ezf = ML / 2 + 0.003
    nU = 30; nV = 22
    SU = (e - (Rr - th)) + Rr * math.pi / 2 + (sheet_top + th - Rr - yb)
    ed = (0.40, 0.52, 0.60); edin = (0.86, 0.86, 0.82)
    zc0 = zt; Lz = ezf - zt
    Pout = np.zeros((nV, nU, 3)); Pin = np.zeros((nV, nU, 3))
    for j in range(nV):
        v = j / (nV - 1)
        sz = v * (Lz - (Rr - th) + Rr * math.pi / 2 + (sheet_top + th - Rr - yb))
        for i in range(nU):
            su = (i / (nU - 1) * 2 - 1) * SU
            (ox, yxo), (ixo, yxi) = _drape(e, sheet_top, th, Rr, yb, su)
            (oz, yzo), (izo, yzi) = _drape(Lz, sheet_top, th, Rr, yb, sz)
            wav = 0.004 * math.sin(i * 0.9 + j * 1.3) * (1 if abs(su) < e - 0.05 else 0.3) * (1 if sz < Lz - 0.05 else 0.3)
            Pout[j, i] = (math.copysign(ox, su), min(yxo, yzo) + wav, zc0 + oz)
            Pin[j, i] = (math.copysign(ixo, su), min(yxi, yzi), zc0 + izo)
    def grid(P, flip, col):
        Pf = P.reshape(-1, 3); T = []
        for j in range(nV - 1):
            for i in range(nU - 1):
                a_ = j * nU + i; T += [(a_, a_ + nU, a_ + 1), (a_ + 1, a_ + nU, a_ + nU + 1)]
        T = np.array(T); N = grid_normals(Pf, T)
        if (N[:, 1].mean() < 0) != flip: N = -N; T = T[:, [0, 2, 1]]
        g.add(LIN, Pf, N, [col + (1,)] * len(Pf), Pf[:, [0, 2]] * 3, T)
    grid(Pout, False, ed); grid(Pin, True, edin)
    # barra (bainha) ligando as duas cascas nas bordas
    for row_o, row_i in ((Pout[:, 0], Pin[:, 0]), (Pout[:, -1], Pin[:, -1]), (Pout[-1], Pin[-1]), (Pout[0], Pin[0])):
        loft(g, LIN, [np.vstack([row_o, row_i[::-1]])], ed, cap0=False, cap1=False) if False else None
        Q = np.vstack([row_o, row_i]); n = len(row_o); T = []
        for k in range(n - 1): T += [(k, k + 1, n + k), (k + 1, n + k + 1, n + k)]
        T = np.array(T); N = grid_normals(Q, T)
        g.add(LIN, Q, N, [tuple(np.array(ed) * 0.85) + (1,)] * len(Q), Q[:, [0, 2]] * 3, T)
    # dobra virada (lençol de cima por cima do edredom) seguindo o perfil do edredom na cabeceira
    path = [V(p[0], p[1] + 0.006, zt + 0.02) for p in Pout[0][::2]] + [V(Pout[0][-1][0], Pout[0][-1][1] + 0.006, zt + 0.02)]
    g.tube(LIN, path, [0.026] * len(path), sides=10, col=lambda p, t: C4((0.97, 0.97, 0.95)))
    # travesseiros (fronha com vivo) apoiados no lençol; almofadas decorativas encostadas na cabeceira
    hb_front = -hzP + 0.036 + 0.004
    for sx in (-1, 1):
        x = sx * 0.28
        pg = Geo(); rbox(pg, LIN, (0, 0.05, 0), (0.48, 0.10, 0.30), r=0.045, col=(0.98, 0.98, 0.97), uv=3, puff=0.022, step=0.05)
        piping(pg, LIN, 0, 0.05, 0, 0.47, 0.29, 0.004, (0.85, 0.85, 0.88), rad=0.045)
        ground(pg) if False else None
        lo = min(P[:, 1].min() for _, P, *_ in pg.arrays())
        add_xf(g, pg, None, (x, sheet_top - lo - EMB, -ML / 2 + 0.2))
        pill_top = sheet_top - lo - EMB + max(P[:, 1].max() for _, P, *_ in pg.arrays())
        cg = Geo(); rbox(cg, LIN, (0, 0.17, -0.05), (0.42, 0.34, 0.10), r=0.04, col=(0.80, 0.62, 0.42) if sx < 0 else (0.62, 0.70, 0.78), uv=3, puff=0.02, step=0.05)
        Rk = rot_x(-math.radians(16)); top = Rk @ V(0, 0.34, -0.10)
        # base na frente do travesseiro (no lençol) e topo encostado na cabeceira
        add_xf(g, cg, Rk, (x * 0.98, sheet_top - 0.012, hb_front - top[2] + 0.0005))
    # cabeceira estofada entre os postes, com capitonê e vivo
    hbz = -hzP
    rbox(g, OAK, (0, 0.62, hbz - 0.006), (2 * hxP - 0.055, 0.66, 0.03), r=0.006, col=wood, uv=1.5, step=0.3)
    hfab = (0.70, 0.66, 0.60)
    rbox(g, LIN, (0, 0.63, hbz + 0.016), (2 * hxP - 0.08, 0.60, 0.04), r=0.018, col=hfab, uv=3, puff=0.008, step=0.06)
    for r_ in range(3):
        for c_ in range(7):
            bx = -0.48 + c_ * 0.16 + (0.08 if r_ % 2 else 0)
            if abs(bx) > 0.52: continue
            by = 0.45 + r_ * 0.17
            tmp = Geo(); tmp.lathe(LIN, (0, 0, 0), [(0, 0), (0.009, 0), (0.0095, 0.004), (0.006, 0.0065), (0, 0.007)], sides=10, col=C4(np.array(hfab) * 0.7))
            hx_ = (2 * hxP - 0.08) / 2; f_ = max(0.0, (1 - (bx / hx_) ** 2) * (1 - ((by - 0.63) / 0.30) ** 2))
            add_xf(g, tmp, rot_x(math.pi / 2), (bx, by, hbz + 0.016 + 0.02 + 0.008 * f_ - 0.002))
    piping_v(g, LIN, -hxP + 0.042, hxP - 0.042, 0.335, 0.925, hbz + 0.036, 0.006, np.array(hfab) * 0.8, rad=0.02)
    M.empty('COL_base', (0, 0.19, 0), extras=dict(shape='box', size=[2 * hxP + 0.056, 0.38, 2 * hzP + 0.056], bloqueia=True, camada='movel',
            nota='estrutura (pés, laterais, peseira)'))
    M.empty('COL_colchao', (0, y_sl + MH / 2, 0), extras=dict(shape='box', size=[MW, MH, ML], bloqueia=False, camada='superficie',
            nota='colchão separado; a roupa de cama não tem colisor'))
    M.empty('COL_cabeceira', (0, 0.475, hbz), extras=dict(shape='box', size=[2 * hxP + 0.056, 0.95, 0.07], bloqueia=True, camada='movel'))
    duvet_top = sheet_top + th
    M.empty('SURF_cama', (0, duvet_top, 0.15), extras=dict(shape='box', size=[MW, 0, ML - 0.6], recebe='objetos leves'))
    for sx, nm in ((-1, 'IP_deitar_E'), (1, 'IP_deitar_D')):
        edge = sx * (hxP + 0.03)
        sit_x = edge + sx * 0.15
        M.empty(nm, (sit_x, 0, 0.12), yaw=(math.pi / 2 if sx > 0 else -math.pi / 2),
                extras=dict(acao='deitar', dormir=True, lado=('direito' if sx > 0 else 'esquerdo'), aproximacao=[edge + sx * 0.6, 0, 0.12],
                            inicio=[edge + sx * 0.27, 0, 0.12], assento_y=duvet_top - 0.012, deitado=[sx * 0.28, duvet_top + 0.005, -ML / 2 + 0.13],
                            olhar=('+X' if sx > 0 else '-X'),
                            sequencia=['aproximar pelo lado', 'alinhar (virar de costas)', 'sentar na borda', 'deitar (1 s)', 'deitado', 'dormir',
                                       'despertar', 'sentar', 'levantar']))
    M.bake_ao(maxd=0.25, strength=0.5)
    return finish(M)


# ================================================================================================ GELADEIRA
def geladeira():
    W, D, H = 0.56, 0.60, 1.50; t = 0.03
    zF = D / 2 - 0.03; zB = -D / 2
    yb = 0.10; ydv0, ydv1 = 1.06, 1.10
    dth = 0.05; dz0 = zF + 0.002
    M = G.Model('int_geladeira', meta('int_geladeira', 'Geladeira duplex', 'cozinha', 'eletrodomesticos', 'funcional',
               dict(tipo='estatico', massa=62.0, motivo='eletrodoméstico pesado ancorado'),
               estados=['fechada', 'abrindo', 'aberta', 'fechando'], grade=[1, 1], luz_interna='acende com a porta da geladeira aberta',
               inventario='opcional na ficha: não implementado (o conteúdo é cenário modelado)',
               conteudo_interno=['frutas e legumes na gaveta (maçã, laranja, tomate, banana, cenoura, alface)', 'queijo, frios e manteiga', 'potes com tampa e comida',
                                 'iogurtes e latas', 'garrafas, caixa de leite, bisnagas e ovos na porta', 'freezer: formas de gelo, congelados e sorvete'],
               interacoes=[dict(acao='abrir/fechar', pecas=['porta_freezer', 'porta_geladeira', 'gaveta_legumes'])]))
    body = M.node('corpo'); g = body.geo
    # pés niveladores e base do motor (com grade)
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.lathe(PLN, (sx * (W / 2 - 0.05), 0, sz * (D / 2 - 0.06)), [(0, 0), (0.018, 0), (0.018, 0.006), (0.008, 0.01), (0.008, 0.0255), (0, 0.0255)], sides=12, col=C4(DARK))
    rbox(g, PLN, (0, (0.025 + yb) / 2, -0.002), (W, yb - 0.025 + 0.001, D - 0.004), r=0.004, col=WHITE, uv=1)
    for k in range(7):
        rbox(g, PLN, (0, 0.04 + k * 0.009, D / 2 - 0.0045), (W - 0.12, 0.004, 0.003), r=0.001, col=(0.25, 0.25, 0.27), uv=1)
    # caixa: laterais, topo, fundo, piso interno e divisória (painéis com espessura; o interior é a face interna branca)
    for sx in (-1, 1): rbox(g, PLN, (sx * (W / 2 - t / 2), (yb + H) / 2, (zB + zF) / 2), (t, H - yb + 0.001, zF - zB), r=0.004, col=WHITE, uv=1, step=0.4)
    rbox(g, PLN, (0, H - t / 2, (zB + zF) / 2), (W - 2 * t + 0.001, t, zF - zB), r=0.003, col=WHITE, uv=1, step=0.4)
    rbox(g, PLN, (0, (yb + H - t) / 2, zB + t / 2), (W - 2 * t + 0.001, H - t - yb + 0.001, t), r=0.003, col=(0.96, 0.97, 0.98), uv=1, step=0.4)
    rbox(g, PLN, (0, yb + 0.015, (zB + zF) / 2), (W - 2 * t + 0.001, 0.03, zF - zB), r=0.003, col=(0.96, 0.97, 0.98), uv=1, step=0.4)
    rbox(g, PLN, (0, (ydv0 + ydv1) / 2, (zB + zF) / 2), (W - 2 * t + 0.001, ydv1 - ydv0, zF - zB), r=0.003, col=WHITE, uv=1, step=0.4)
    xi = W / 2 - t; zi0 = zB + t
    # nervuras nas paredes (apoios das prateleiras) e prateleiras de vidro com acabamento
    shelves = (0.335, 0.47, 0.72, 0.92); zsf = zF - 0.115
    for k, yy in enumerate(shelves):
        for sx in (-1, 1):
            rbox(g, PLN, (sx * (xi - 0.005), yy - 0.008, (zi0 + zsf) / 2), (0.011, 0.008, zsf - zi0 - 0.02), r=0.002, col=(0.90, 0.92, 0.94), uv=1)
        rbox(g, GLASS, (0, yy - 0.002, (zi0 + zsf) / 2 + 0.002), (2 * xi - 0.002, 0.008, zsf - zi0 - 0.004), r=0.002, col=(0.75, 0.88, 0.90), uv=1) if False else None
        gl = Geo(); rbox(gl, GLASS, (0, 0, 0), (2 * xi - 0.002, 0.007, zsf - zi0 - 0.004), r=0.002, col=(0.80, 0.92, 0.95), uv=1)
        a_ = gl.parts[GLASS]; a_['C'] = [np.c_[C[:, :3], np.full(len(C), 0.35)] for C in a_['C']]
        add_xf(g, gl, None, (0, yy - 0.004 + 0.0035 - 0.0005, (zi0 + zsf) / 2))
        rbox(g, PLN, (0, yy - 0.0005, zsf - 0.006), (2 * xi - 0.001, 0.016, 0.012), r=0.003, col=(0.75, 0.78, 0.82), uv=1)
    # luz interna (soquete no teto da geladeira) e o brilho (efeito)
    rbox(g, PLN, (0, ydv0 - 0.012, -0.08), (0.12, 0.024, 0.05), r=0.006, col=(0.92, 0.93, 0.95), uv=1)
    lz = M.node('luz', (0, ydv0 - 0.025, -0.08), extras=dict(efeito=dict(tipo='luz', quando='porta_geladeira')))
    tmpl = Geo(); rbox(tmpl, PLN, (0, ydv0 - 0.026, -0.08), (0.10, 0.004, 0.035), r=0.0015, col=(1.0, 0.98, 0.88), uv=1); emissive(tmpl); add_xf(lz.geo, tmpl)
    # ---- portas (dobradiça à direita) com vedação, nichos (porta da geladeira), puxador
    ax_x = W / 2 - 0.012; ax_z = dz0 + dth / 2
    for nm, y0, y1, ang in (('porta_geladeira', yb + 0.004, ydv0 + 0.015, 1.92), ('porta_freezer', ydv0 + 0.025, H - 0.003, 1.92)):
        cy = (y0 + y1) / 2
        dn = M.node(nm, (ax_x, cy, ax_z), extras=dict(anim=dict(tipo='dobradica', eixo=[0, 1, 0], min=0.0, max=ang, dur=0.6, curva='suave', estado_inicial=0.0,
                    alca=[-W / 2 + 0.05, cy, dz0 + dth + 0.05], rotulo='porta do freezer' if 'freezer' in nm else 'porta da geladeira', colide_com=['parede', 'movel'],
                    limite='até 110° ou até a parede')))
        gd = dn.geo
        rbox(gd, PLN, (0, cy, dz0 + dth / 2), (W - 0.004, y1 - y0, dth), r=0.012, col=WHITE, uv=1, step=0.25)
        # vedação de borracha (encosta na frente da caixa)
        pts = []
        for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
            ccx = sx * (W / 2 - 0.02 - 0.02); ccy = cy + sy * ((y1 - y0) / 2 - 0.02 - 0.02)
            for i in range(5):
                a = math.radians(a0 + 90 * i / 4); pts.append(V(ccx + 0.02 * math.cos(a), ccy + 0.02 * math.sin(a), dz0 - 0.0045))
        pts.append(pts[0])
        gd.tube(PLN, pts, [0.0075] * len(pts), sides=8, col=lambda p, tt: C4((0.18, 0.18, 0.2)))
        # puxador vertical (lado esquerdo, oposto à dobradiça)
        hx = -W / 2 + 0.04; hy0 = cy - (y1 - y0) * 0.3 if 'freezer' not in nm else y0 + 0.04; hy1 = cy + (y1 - y0) * 0.3 if 'freezer' not in nm else y0 + 0.16
        gd.tube(MET, [V(hx, hy0, dz0 + dth + 0.03), V(hx, hy1, dz0 + dth + 0.03)], [0.009, 0.009], sides=12, col=lambda p, tt: C4(INOX))
        for yy in (hy0, hy1): gd.tube(MET, [V(hx, yy, dz0 + dth - 0.0005), V(hx, yy, dz0 + dth + 0.03)], [0.007, 0.007], sides=10, col=lambda p, tt: C4(INOX))
        if nm == 'porta_geladeira':
            # forro da porta com 3 nichos (fundo + frente) presos ao forro
            rbox(gd, PLN, (0, cy, dz0 - 0.004), (W - 0.12, y1 - y0 - 0.12, 0.009), r=0.004, col=(0.94, 0.95, 0.96), uv=1)
            cn = M.node('conteudo_porta', (ax_x, cy, ax_z), parent=dn, extras=dict(mostrar_quando=[nm], nota='conteúdo dos nichos da porta'))
            gc = cn.geo
            bins = ((0.16, 0.11, 0.075), (0.47, 0.09, 0.06), (0.80, 0.08, 0.065))
            for (by, bd, bh) in bins:
                zb0 = dz0 - 0.0085 - bd
                rbox(gd, PLN, (0, by + 0.003, zb0 + bd / 2), (W - 0.13, 0.006, bd + 0.0005), r=0.002, col=(0.88, 0.92, 0.95), uv=1)
                rbox(gd, PLN, (0, by + bh / 2, zb0 + 0.003), (W - 0.13, bh, 0.006), r=0.002, col=(0.82, 0.90, 0.96), uv=1)
                for sx in (-1, 1): rbox(gd, PLN, (sx * (W / 2 - 0.065 - 0.003), by + bh / 2, zb0 + bd / 2), (0.006, bh, bd + 0.0005), r=0.002, col=(0.82, 0.90, 0.96), uv=1)
            fl = lambda by: by + 0.006
            zb_ = lambda bd: dz0 - 0.0085 - bd / 2
            # nicho de baixo: garrafa d'água, suco e leite
            for x, item in ((-0.16, CT.garrafa((0.80, 0.90, 0.98), ((0.15, 0.45, 0.85), (0.95, 0.95, 0.95)), (0.10, 0.35, 0.80), h=0.26, r=0.033)),
                            (-0.085, CT.garrafa((0.98, 0.65, 0.15), ((0.95, 0.95, 0.90), (0.30, 0.60, 0.20)), (0.95, 0.75, 0.10), h=0.22, r=0.03)),
                            (0.02, CT.caixa_leite()), (0.11, CT.caixa_leite(marca=(0.85, 0.25, 0.20)))):
                place(gc, item[0], x, fl(0.16) - EMB, zb_(0.11))
            # nicho do meio: ketchup, mostarda, molho
            for x, item in ((-0.15, CT.bisnaga((0.80, 0.10, 0.06), (0.95, 0.95, 0.95))), (-0.08, CT.bisnaga((0.95, 0.80, 0.15), (0.20, 0.45, 0.85))),
                            (0.0, CT.garrafa((0.35, 0.18, 0.10), ((0.95, 0.90, 0.75), (0.80, 0.15, 0.10)), (0.95, 0.95, 0.90), h=0.16, r=0.022, gargalo=0.008, vidro=True)),
                            (0.07, CT.iogurte()), (0.135, CT.iogurte(tampa=(0.25, 0.55, 0.85)))):
                place(gc, item[0], x, fl(0.47) - EMB, zb_(0.09))
            # nicho de cima: porta-ovos com ovos
            eg, ei = CT.bandeja_ovos(n_x=4, n_z=1, cheio={0, 1, 2})
            place(gc, eg, -0.05, fl(0.80) - EMB, zb_(0.08) + 0.003)
            eg, ei = CT.bandeja_ovos(n_x=2, n_z=1)
            place(gc, eg, 0.13, fl(0.80) - EMB, zb_(0.08) + 0.003)
    # dobradiças: suporte em cima (sobre o topo), no meio (na frente da divisória) e embaixo (na base); pinos entram nas portas
    def pin(yy0, yy1): g.lathe(MET, (ax_x, yy0, ax_z), [(0, 0), (0.0055, 0), (0.0055, yy1 - yy0), (0, yy1 - yy0)], sides=10, col=C4(INOX))
    rbox(g, MET, (W / 2 - 0.03, H + 0.003 - 0.0005, (zF - 0.04 + ax_z + 0.015) / 2), (0.06, 0.006, ax_z + 0.015 - zF + 0.04), r=0.002, col=INOX, uv=1)
    pin(H - 0.02, H + 0.0005)
    rbox(g, MET, (W / 2 - 0.03, (ydv0 + 0.015 + ydv0 + 0.025) / 2, (zF - 0.0005 + ax_z + 0.015) / 2), (0.06, 0.0095, ax_z + 0.015 - zF + 0.0005), r=0.001, col=INOX, uv=1)
    pin(ydv0 + 0.0, ydv0 + 0.04)
    rbox(g, MET, (W / 2 - 0.03, yb + 0.004 - 0.003, (zF - 0.0005 + ax_z + 0.015) / 2), (0.06, 0.006, ax_z + 0.015 - zF + 0.0005), r=0.001, col=INOX, uv=1)
    pin(yb - 0.002, yb + 0.03)
    # ---- gaveta de legumes (trilho; só abre com a porta aberta), apoiada no piso interno
    gw = 2 * xi - 0.012; gdp = zsf - zi0 - 0.01; gh0 = yb + 0.03; gh = 0.335 - 0.008 - 0.004 - gh0
    gz = (zi0 + zsf) / 2 + 0.004
    gv = M.node('gaveta_legumes', (0, gh0 + gh / 2, gz), extras=dict(anim=dict(tipo='trilho', eixo=[0, 0, 1], min=0.0, max=0.22, dur=0.4, curva='suave',
                estado_inicial=0.0, precisa='porta_geladeira', alca=[0, gh0 + gh * 0.8, zsf + 0.05], rotulo='gaveta de legumes', colide_com=['parede', 'movel'])))
    gg = gv.geo; GC = (0.86, 0.93, 0.95)
    rbox(gg, PLN, (0, gh0 + 0.003 - 0.0005, gz), (gw, 0.006, gdp), r=0.002, col=GC, uv=1)
    for sx in (-1, 1): rbox(gg, PLN, (sx * (gw / 2 - 0.003), gh0 + gh / 2, gz), (0.006, gh, gdp), r=0.002, col=GC, uv=1)
    rbox(gg, PLN, (0, gh0 + gh / 2, gz - gdp / 2 + 0.003), (gw, gh, 0.006), r=0.002, col=GC, uv=1)
    rbox(gg, PLN, (0, gh0 + gh / 2, gz + gdp / 2 - 0.004), (gw, gh, 0.008), r=0.003, col=(0.80, 0.90, 0.94), uv=1)
    rbox(gg, PLN, (0, gh0 + gh - 0.012, gz + gdp / 2 + 0.006), (gw * 0.5, 0.012, 0.012), r=0.004, col=(0.75, 0.82, 0.86), uv=1)
    cv = M.node('conteudo_gaveta', (0, gh0 + gh / 2, gz), parent=gv, extras=dict(mostrar_quando=['porta_geladeira'], nota='frutas e legumes'))
    gcv = cv.geo; fl0 = gh0 + 0.006
    for (x, z, fn) in ((-0.17, -0.12, CT.maca), (-0.10, -0.13, CT.maca), (-0.135, -0.05, CT.laranja), (-0.06, -0.06, CT.laranja), (-0.17, 0.03, CT.tomate),
                       (-0.11, 0.04, CT.tomate), (-0.06, 0.035, CT.maca)):
        it, inf = fn(); place(gcv, it, x, fl0 - EMB, z, yaw=x * 30)
    it, inf = CT.alface(r=0.065); place(gcv, it, 0.10, fl0 - EMB, -0.08)
    it, inf = CT.banana_penca(); place(gcv, it, 0.07, fl0 - EMB, 0.06, yaw=0.3)
    for k in range(3):
        it, inf = CT.cenoura(); place(gcv, it, 0.13, fl0 - EMB, 0.10 + 0.0, yaw=1.5 + 0.08 * k) if k == 0 else place(gcv, it, 0.13 + 0.028 * k, fl0 - EMB, 0.11, yaw=1.55)
    # ---- conteúdo das prateleiras (só com a porta da geladeira aberta)
    cs = M.node('conteudo_prateleiras', extras=dict(mostrar_quando=['porta_geladeira'], nota='prateleiras da geladeira'))
    gs = cs.geo
    def top(yy): return yy - 0.004 + 0.0035 - 0.0005 + 0.0035
    y1 = top(0.335)
    place(gs, CT.queijo_cunha()[0], -0.13, y1 - EMB, -0.10, yaw=0.4)
    place(gs, CT.frios_bandeja()[0], 0.08, y1 - EMB, -0.12)
    place(gs, CT.manteigueira()[0], 0.12, y1 - EMB, 0.02)
    y2 = top(0.47)
    pg, pi = CT.pote_tampa()
    place(gs, pg, -0.12, y2 - EMB, -0.12)
    place(gs, CT.pote_tampa(cor_tampa=(0.85, 0.30, 0.30), comida=(0.95, 0.85, 0.55))[0], -0.12, y2 + pi['altura'] - 2 * EMB, -0.12, yaw=0.15)
    for k, (x, z) in enumerate(((0.06, -0.15), (0.12, -0.15), (0.09, -0.09))):
        place(gs, CT.iogurte(tampa=[(0.85, 0.30, 0.45), (0.95, 0.75, 0.20), (0.40, 0.25, 0.70)][k])[0], x, y2 - EMB, z)
    for x in (0.0, 0.07):
        place(gs, CT.lata((0.80, 0.08, 0.08), (0.95, 0.95, 0.95))[0], x, y2 - EMB, 0.05)
    y3 = top(0.72)
    place(gs, CT.pote_tampa(w=0.18, d=0.13, h=0.08, cor_tampa=(0.30, 0.65, 0.40), comida=(0.75, 0.70, 0.30))[0], 0.08, y3 - EMB, -0.11)
    place(gs, CT.lata((0.15, 0.35, 0.75), (0.95, 0.80, 0.20))[0], -0.15, y3 - EMB, -0.14)
    place(gs, CT.lata((0.20, 0.60, 0.25), (0.95, 0.95, 0.95))[0], -0.15, y3 - EMB, -0.07)
    place(gs, CT.garrafa((0.25, 0.10, 0.12), ((0.92, 0.88, 0.75), (0.55, 0.10, 0.15)), (0.15, 0.10, 0.08), h=0.18, r=0.03, gargalo=0.01, vidro=True)[0], -0.08, y3 - EMB, -0.12)
    y4 = top(0.92)
    place(gs, CT.pote_tampa(w=0.16, d=0.12, h=0.06, comida=(0.55, 0.30, 0.15))[0], -0.1, y4 - EMB, -0.1)
    place(gs, CT.bandeja_ovos(n_x=3, n_z=2)[0], 0.12, y4 - EMB, -0.1)
    # ---- freezer
    cf = M.node('conteudo_freezer', extras=dict(mostrar_quando=['porta_freezer'], nota='freezer'))
    gf = cf.geo; yf = ydv1
    fg, fi = CT.forma_gelo()
    place(gf, fg, -0.07, yf - EMB, -0.16)
    place(gf, CT.forma_gelo(cor=(0.90, 0.75, 0.85))[0], -0.07, yf + fi['altura'] - 2 * EMB, -0.16, yaw=0.05)
    place(gf, CT.saco_congelado()[0], -0.10, yf - EMB, 0.05, yaw=0.1)
    place(gf, CT.pote_sorvete()[0], 0.13, yf - EMB, -0.05)
    place(gf, CT.saco_congelado(cor=(0.85, 0.35, 0.25), w=0.14, d=0.18)[0], 0.12, yf - EMB, 0.12, yaw=-0.2) if False else None
    M.empty('COL_corpo', (0, H / 2, -0.01), extras=dict(shape='box', size=[W, H, D - 0.02], bloqueia=True, camada='movel'))
    M.empty('SURF_topo', (0, H, 0), extras=dict(shape='box', size=[W, 0, D - 0.04], recebe='objetos'))
    M.empty('IP_usar', (0, 0, D / 2 + 0.55), extras=dict(acao='abrir/fechar', olhar='-Z'))
    M.bake_ao(maxd=0.22, strength=0.5)
    return finish(M)


# ================================================================================================ FOGÃO COM FORNO
def fogao():
    W, D = 0.50, 0.55; ytop = 0.765; ysh = ytop - 0.02
    zF = D / 2; zB = -D / 2
    M = G.Model('int_fogao', meta('int_fogao', 'Fogão 4 bocas com forno', 'cozinha', 'eletrodomesticos', 'funcional',
               dict(tipo='estatico', massa=38.0, motivo='eletrodoméstico ancorado'),
               estados=['desligado', 'ligado', 'cozinhando'],
               regra_estados='ligado = alguma boca ou o forno aceso; cozinhando = a boca com a panela acesa (sai vapor da panela)', grade=[1, 1],
               conteudo_interno=['grade do forno nas guias', 'bolo assando na forma'],
               interacoes=[dict(acao='acender/apagar', pecas=['botao_0', 'botao_1', 'botao_2', 'botao_3', 'botao_forno']), dict(acao='abrir/fechar', pecas=['porta_forno'])]))
    body = M.node('corpo'); g = body.geo
    # pés reguláveis (no piso) e chapa de base
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.lathe(PLN, (sx * (W / 2 - 0.04), 0, sz * (D / 2 - 0.05)), [(0, 0), (0.016, 0), (0.016, 0.005), (0.009, 0.009), (0.009, 0.0305), (0, 0.0305)], sides=12, col=C4(DARK))
    rbox(g, MET, (0, 0.0375, 0), (W, 0.015, D), r=0.003, col=(0.55, 0.56, 0.58), uv=1)
    # laterais e fundo (inox), rodapé, painel de comandos
    for sx in (-1, 1): rbox(g, MET, (sx * (W / 2 - 0.01), (0.045 + ysh) / 2, 0), (0.02, ysh - 0.045 + 0.001, D), r=0.003, col=INOX, uv=1, step=0.3)
    rbox(g, MET, (0, (0.045 + ysh) / 2, zB + 0.01), (W - 0.04 + 0.001, ysh - 0.045 + 0.001, 0.02), r=0.002, col=INOX, uv=1, step=0.3)
    rbox(g, PLN, (0, 0.0675, zF - 0.01), (W - 0.04 + 0.001, 0.045 + 0.001, 0.02), r=0.002, col=DARK, uv=1)
    rbox(g, MET, (0, 0.7025, zF - 0.015), (W - 0.04 + 0.001, 0.085, 0.03), r=0.004, col=INOX, uv=1, step=0.2)
    # forno: piso, teto, fundo e laterais esmaltados (escuro), com guias da grade
    cav = (0.16, 0.16, 0.18)
    rbox(g, PLN, (0, 0.105, -0.01), (W - 0.04 + 0.001, 0.02, D - 0.04), r=0.002, col=cav, uv=1)
    rbox(g, PLN, (0, 0.615, -0.01), (W - 0.04 + 0.001, 0.02, D - 0.04), r=0.002, col=cav, uv=1)
    rbox(g, PLN, (0, 0.36, zB + 0.025), (W - 0.04 + 0.001, 0.49, 0.01), r=0.002, col=cav, uv=1)
    for sx in (-1, 1): rbox(g, PLN, (sx * (W / 2 - 0.0225), 0.36, -0.01), (0.005, 0.49, D - 0.04), r=0.001, col=cav, uv=1)
    guides = (0.22, 0.32, 0.42)
    for yy in guides:
        for sx in (-1, 1):
            rbox(g, PLN, (sx * (W / 2 - 0.031), yy, -0.02), (0.013, 0.008, D - 0.12), r=0.003, col=(0.22, 0.22, 0.24), uv=1)
    # moldura da boca do forno (esmalte escuro) e isolamento acima do forno
    for sx in (-1, 1): rbox(g, PLN, (sx * (W / 2 - 0.03), 0.38, zF - 0.006), (0.02 + 0.001, 0.54, 0.012), r=0.002, col=cav, uv=1)
    rbox(g, PLN, (0, 0.635, zF - 0.006), (W - 0.04 + 0.001, 0.02, 0.012), r=0.002, col=cav, uv=1)
    rbox(g, PLN, (0, (0.625 + ysh) / 2, -0.02), (W - 0.04 + 0.001, ysh - 0.625 + 0.001, D - 0.08), r=0.003, col=(0.35, 0.33, 0.30), uv=1)
    # elemento de aquecimento (brilha com o forno ligado)
    rbox(g, PLN, (0, 0.118, -0.01), (0.30, 0.006, 0.30), r=0.002, col=(0.25, 0.22, 0.20), uv=1)
    ef = M.node('calor_forno', (0, 0.122, -0.01), extras=dict(efeito=dict(tipo='luz', quando='botao_forno')))
    tmp = Geo()
    for k in range(5):
        tmp.tube(PLN, [V(-0.13, 0.122, -0.12 + k * 0.055), V(0.13, 0.122, -0.12 + k * 0.055)], [0.004, 0.004], sides=6, col=lambda p, t: C4((1.0, 0.45, 0.15)))
    emissive(tmp); add_xf(ef.geo, tmp)
    # grade do forno (arame) apoiada nas guias do meio, com o bolo
    yg = guides[1] + 0.004
    rw = W - 2 * 0.0375 + 0.002; rd = D - 0.14
    rack = Geo()
    path = rect_path(0, yg + 0.003 - 0.0005, -0.03, rw, rd, 0.01)
    rack.tube(MET, path, [0.003] * len(path), sides=6, col=lambda p, t: C4(CHROME))
    for k in range(9):
        x = -rw / 2 + 0.02 + k * (rw - 0.04) / 8
        rack.tube(MET, [V(x, yg + 0.003 + 0.002, -0.03 - rd / 2 + 0.002), V(x, yg + 0.003 + 0.002, -0.03 + rd / 2 - 0.002)], [0.0022] * 2, sides=5, col=lambda p, t: C4(CHROME))
    add_xf(g, rack)
    bg, bi = CT.bolo_forma()
    place(g, bg, 0.0, yg + 0.003 + 0.002 + 0.0022 - EMB, -0.02)
    # mesa (cooktop) sobre o corpo, encosto traseiro preso no fundo
    rbox(g, MET, (0, ysh + 0.01 - 0.0005, 0), (W, 0.02, D), r=0.006, col=(0.85, 0.86, 0.88), uv=1, step=0.2)
    rbox(g, MET, (0, (ysh + 0.84) / 2, zB + 0.012), (W, 0.84 - ysh + 0.001, 0.022), r=0.006, col=INOX, uv=1, step=0.2)
    # queimadores encaixados na mesa (copo, espalhador com fendas, tampa esmaltada)
    burners = [(-0.115, 0.095, 0.034), (0.115, 0.095, 0.03), (-0.115, -0.125, 0.04), (0.115, -0.125, 0.034)]
    names = ['frente esquerda', 'frente direita', 'trás esquerda', 'trás direita']
    for i, (bx, bz, br) in enumerate(burners):
        g.lathe(MET, (bx, ytop - 0.0005, bz), [(0, 0), (br + 0.012, 0), (br + 0.012, 0.004), (br + 0.004, 0.006), (br * 0.9, 0.007), (0, 0.007)], sides=24, col=C4((0.40, 0.40, 0.42)))
        g.lathe(PLN, (bx, ytop + 0.0065, bz), [(0, 0), (br, 0), (br, 0.009), (0, 0.009)], sides=28, col=C4((0.15, 0.15, 0.16)))
        for k in range(20):
            a = 2 * math.pi * k / 20
            g.tube(PLN, [V(bx + (br + 0.0004) * math.cos(a), ytop + 0.0085, bz + (br + 0.0004) * math.sin(a)), V(bx + (br + 0.0004) * math.cos(a), ytop + 0.0125, bz + (br + 0.0004) * math.sin(a))],
                   [0.0011] * 2, sides=3, col=lambda p, t: C4((0.05, 0.05, 0.05)))
        g.lathe(PLN, (bx, ytop + 0.0155 - 0.0005, bz), [(0, 0.004), (br * 0.92, 0.0), (br * 0.96, 0.002), (br * 0.75, 0.006), (0, 0.007)], sides=24, col=C4((0.10, 0.10, 0.11)))
        # chamas (efeito, só com o botão aceso): línguas azuis saindo das fendas, abaixo da grade e da panela
        fn_ = M.node('chama_%d' % i, (bx, ytop + 0.01, bz), extras=dict(efeito=dict(tipo='chama', quando='botao_%d' % i)))
        tmp = Geo()
        for k in range(20):
            a = 2 * math.pi * k / 20; c = V(bx + (br + 0.002) * math.cos(a), ytop + 0.0105, bz + (br + 0.002) * math.sin(a))
            d = V(math.cos(a), 0, math.sin(a))
            tmp.tube(PLN, [c, c + d * 0.008 + V(0, 0.006, 0), c + d * 0.012 + V(0, 0.016, 0)], [0.0035, 0.0028, 0.0008], sides=5,
                     col=lambda p, t: C4((0.25 + 0.5 * t, 0.45 + 0.3 * t, 1.0), 0.85))
        emissive(tmp); add_xf(fn_.geo, tmp)
    # grades de ferro fundido (duas, cada uma sobre duas bocas), em pé na mesa pelos próprios pés com borracha
    gy = ytop + 0.034; gr = 0.0055
    for sx in (-1, 1):
        x0 = sx * 0.005; x1 = sx * (W / 2 - 0.012)
        xa, xb = min(x0, x1), max(x0, x1); za, zb_ = -D / 2 + 0.04, D / 2 - 0.025
        frame = [V(xa, gy, za), V(xb, gy, za), V(xb, gy, zb_), V(xa, gy, zb_), V(xa, gy, za)]
        g.tube(MET, frame, [gr] * 5, sides=8, col=lambda p, t: C4((0.10, 0.10, 0.10)))
        for p in frame[:4]:
            g.tube(MET, [p, p - V(0, gy - ytop - 0.004, 0)], [gr] * 2, sides=8, col=lambda p, t: C4((0.10, 0.10, 0.10)))
            g.lathe(PLN, (p[0], ytop - 0.0005, p[2]), [(0, 0), (0.008, 0), (0.008, 0.0045), (0, 0.0045)], sides=10, col=C4((0.05, 0.05, 0.05)))
        g.tube(MET, [V(xa, gy, (za + zb_) / 2 - 0.015), V(xb, gy, (za + zb_) / 2 - 0.015)], [gr] * 2, sides=8, col=lambda p, t: C4((0.10, 0.10, 0.10)))
        for (bx, bz, br) in burners:
            if (bx > 0) != (sx > 0): continue
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2; dx, dz = math.cos(a), math.sin(a)
                # dedo: do quadro até perto do queimador (fica 1,6 cm acima da tampa)
                tx = (xb if dx > 0 else xa) - bx; tz = ((zb_ if dz > 0 else za) - bz)
                L1 = min(abs(tx / dx), abs(tz / dz)) if abs(dx) > 1e-6 and abs(dz) > 1e-6 else 0.1
                p0 = V(bx + dx * (br + 0.022), gy + 0.0005, bz + dz * (br + 0.022)); p1 = V(bx + dx * L1, gy, bz + dz * L1)
                g.tube(MET, [p0, p1], [0.0045, gr], sides=7, col=lambda p, t: C4((0.10, 0.10, 0.10)))
    # panela na grade da frente esquerda (fundo apoiado nos dedos), com tampa e alças
    px, pz, _ = burners[0]; py0 = gy + gr - EMB + 0.0005
    g.lathe(MET, (px, py0, pz), [(0, 0), (0.078, 0), (0.084, 0.006), (0.084, 0.085), (0.088, 0.088), (0.086, 0.09)], sides=32, col=C4((0.70, 0.72, 0.75)))
    g.lathe(MET, (px, py0 + 0.0855, pz), [(0.087, 0), (0.08, 0.008), (0.05, 0.02), (0.0, 0.024)], sides=32, col=C4((0.80, 0.82, 0.84)))
    g.lathe(PLN, (px, py0 + 0.0855 + 0.0235, pz), [(0, 0), (0.008, 0), (0.012, 0.01), (0.012, 0.016), (0, 0.018)], sides=14, col=C4(DARK))
    for s in (-1, 1):
        g.tube(PLN, [V(px + s * 0.083, py0 + 0.07, pz - 0.025), V(px + s * 0.108, py0 + 0.075, pz - 0.018), V(px + s * 0.108, py0 + 0.075, pz + 0.018), V(px + s * 0.083, py0 + 0.07, pz + 0.025)],
               [0.0055] * 4, sides=8, col=lambda p, t: C4(DARK))
    vp = M.node('vapor_panela', (px, py0 + 0.13, pz), extras=dict(efeito=dict(tipo='vapor', quando='botao_0'), nota='cozinhando: vapor sai da tampa'))
    tmp = Geo()
    for k in range(4):
        a = k * 1.7; c = V(px + 0.01 * math.cos(a), py0 + 0.127, pz + 0.01 * math.sin(a))
        tmp.tube(PLN, [c, c + V(0.01 * math.cos(a + 1), 0.04, 0.01 * math.sin(a + 1)), c + V(-0.008, 0.09, 0.006), c + V(0.01, 0.14, -0.01)], [0.006, 0.012, 0.016, 0.004], sides=7,
                 col=lambda p, t: C4((0.95, 0.96, 0.98), 0.45 * (1 - t) + 0.05))
    emissive(tmp); add_xf(vp.geo, tmp)
    # botões (cada um gira no próprio eixo curto), com anel no painel
    kx = (-0.17, -0.085, 0.0, 0.085, 0.17); ky = 0.705; kz = zF
    knob_names = ['botao_2', 'botao_0', 'botao_1', 'botao_3', 'botao_forno']
    labels = ['boca de trás esquerda', 'boca da frente esquerda', 'boca da frente direita', 'boca de trás direita', 'forno']
    for x, nm, lab in zip(kx, knob_names, labels):
        g.lathe(MET, (0, 0, 0), [(0.016, 0), (0.024, 0), (0.024, 0.002), (0.016, 0.002)], sides=24, col=C4((0.6, 0.6, 0.62))) if False else None
        tmp = Geo(); tmp.lathe(MET, (0, 0, 0), [(0.016, -0.0005), (0.025, -0.0005), (0.025, 0.0015), (0.016, 0.0018)], sides=24, col=C4((0.62, 0.62, 0.64)))
        add_xf(g, tmp, rot_x(math.pi / 2), (x, ky, kz))
        verbs = ['Ligar', 'Desligar'] if nm == 'botao_forno' else ['Acender', 'Apagar']
        kn = M.node(nm, (x, ky, kz), extras=dict(anim=dict(tipo='dobradica', eixo=[0, 0, 1], min=0.0, max=round(math.radians(-100), 4), dur=0.3, curva='suave',
                    estado_inicial=0.0, alca=[x, ky, kz + 0.07], rotulo=lab, verbos=verbs)))
        tmp = Geo()
        tmp.lathe(PLN, (0, 0, 0), [(0, -0.003), (0.005, -0.003), (0.005, 0.006), (0.018, 0.008), (0.019, 0.022), (0.016, 0.026), (0, 0.027)], sides=24, col=C4((0.14, 0.14, 0.15)))
        rbox(tmp, PLN, (0, 0.03, 0), (0.007, 0.012, 0.026) if False else (0.006, 0.01, 0.03), r=0.002, col=(0.14, 0.14, 0.15), uv=1) if False else None
        rbox(tmp, PLN, (0, 0.018, 0), (0.03, 0.016, 0.008), r=0.003, col=(0.16, 0.16, 0.17), uv=1)
        rbox(tmp, PLN, (0.011, 0.0265, 0), (0.008, 0.0012, 0.002), r=0.0004, col=(0.95, 0.95, 0.95), uv=1)
        add_xf(kn.geo, tmp, rot_x(math.pi / 2), (x, ky, kz))
    # porta do forno (dobradiça embaixo), moldura inox, visor de vidro duplo e puxador
    dz0 = zF + 0.002; dth = 0.04; dy0 = 0.092; dy1 = 0.652
    ax_y = dy0 + 0.012; ax_zz = dz0 + dth / 2
    dn = M.node('porta_forno', (0, ax_y, ax_zz), extras=dict(anim=dict(tipo='dobradica', eixo=[1, 0, 0], min=0.0, max=round(math.radians(85), 4), dur=0.55, curva='suave',
                estado_inicial=0.0, alca=[-0.2, 0.62, dz0 + dth + 0.06], rotulo='porta do forno', colide_com=['parede', 'movel'])))
    gd = dn.geo; dw = W - 0.006
    cyd = (dy0 + dy1) / 2; hd = dy1 - dy0
    for (cx_, cy_, sx_, sy_) in ((0, dy1 - 0.045, dw, 0.09), (0, dy0 + 0.04, dw, 0.08), (-dw / 2 + 0.03, cyd, 0.06, hd), (dw / 2 - 0.03, cyd, 0.06, hd)):
        rbox(gd, MET, (cx_, cy_, dz0 + dth / 2), (sx_, sy_, dth), r=0.004, col=INOX, uv=1, step=0.2)
    for zz, a in ((dz0 + dth - 0.004, 0.45), (dz0 + 0.006, 0.35)):
        gl = Geo(); rbox(gl, GLASS, (0, (dy0 + 0.08 + dy1 - 0.09) / 2, zz), (dw - 0.12 + 0.001, dy1 - 0.09 - dy0 - 0.08 + 0.001, 0.005), r=0.001, col=(0.10, 0.10, 0.12), uv=1)
        a_ = gl.parts[GLASS]; a_['C'] = [np.c_[C[:, :3], np.full(len(C), a)] for C in a_['C']]
        add_xf(gd, gl)
    gd.tube(MET, [V(-0.19, dy1 - 0.035, dz0 + dth + 0.035), V(0.19, dy1 - 0.035, dz0 + dth + 0.035)], [0.008, 0.008], sides=12, col=lambda p, tt: C4(CHROME))
    for x in (-0.17, 0.17): gd.tube(MET, [V(x, dy1 - 0.035, dz0 + dth - 0.0005), V(x, dy1 - 0.035, dz0 + dth + 0.035)], [0.006, 0.006], sides=10, col=lambda p, tt: C4(CHROME))
    # dobradiças: pino no eixo, preso no braço que sai da lateral
    for sx in (-1, 1):
        g.lathe(MET, (0, 0, 0), [(0, 0)], sides=3, col=C4(INOX)) if False else None
        tmp = Geo(); tmp.lathe(MET, (0, 0, 0), [(0, 0), (0.006, 0), (0.006, 0.05), (0, 0.05)], sides=10, col=C4(CHROME))
        add_xf(g, tmp, rot_z(sx * math.pi / 2), (sx * (W / 2 - 0.001), ax_y, ax_zz))
        rbox(g, MET, (sx * (W / 2 - 0.004), ax_y, (zF - 0.02 + ax_zz) / 2), (0.008, 0.02, ax_zz - zF + 0.02), r=0.001, col=INOX, uv=1)
    M.empty('COL_corpo', (0, 0.42, -0.0), extras=dict(shape='box', size=[W, 0.84, D], bloqueia=True, camada='movel'))
    M.empty('SURF_mesa', (0, ytop, 0), extras=dict(shape='box', size=[W, 0, D], recebe='panelas'))
    M.empty('IP_usar', (0, 0, D / 2 + 0.42), extras=dict(acao='usar', olhar='-Z', nota='as bocas são escolhidas pela posição do personagem (o botão mais perto)'))
    M.bake_ao(maxd=0.2, strength=0.5)
    return finish(M)


# ================================================================================================ PIA DE COZINHA
def pia():
    W, D = 0.80, 0.52; ytop = 0.77; tt = 0.03; yct = ytop - tt
    zF = D / 2; zB = -D / 2; t = 0.018
    hxs, hzs, zs = 0.21, 0.165, 0.02                  # meia-largura/profundidade do furo da cuba e centro
    M = G.Model('int_pia', meta('int_pia', 'Pia com gabinete', 'cozinha', 'pias', 'funcional',
               dict(tipo='estatico', massa=45.0, motivo='móvel com tampo de pedra ancorado'),
               estados=['torneira fechada', 'torneira aberta'], grade=[1, 1],
               conteudo_interno=['sifão ligado ao ralo e à parede', 'detergentes, borrifador', 'esponjas e pano de prato', 'lixeira de pedal'],
               interacoes=[dict(acao='abrir/fechar torneira', pecas=['alavanca']), dict(acao='lavar', ponto='IP_lavar'), dict(acao='abrir/fechar', pecas=['porta_E', 'porta_D'])]))
    body = M.node('corpo'); g = body.geo
    CW = (0.93, 0.92, 0.89)
    y0 = 0.08
    # rodapé (quadro no piso), laterais, base, fundo e travessas sob o tampo
    for sx in (-1, 1): rbox(g, PLN, (sx * (W / 2 - t / 2), y0 / 2 + 0.00025, -0.01), (t, y0 + 0.0005, D - 0.06), r=0.002, col=(0.30, 0.30, 0.31), uv=1)
    for zz in (zF - 0.05, zB + 0.03): rbox(g, PLN, (0, y0 / 2 + 0.00025, zz), (W - 2 * t + 0.001, y0 + 0.0005, 0.018), r=0.002, col=(0.30, 0.30, 0.31), uv=1)
    for sx in (-1, 1): rbox(g, PLN, (sx * (W / 2 - t / 2), (y0 + yct) / 2, 0), (t, yct - y0 + 0.001, D), r=0.002, col=CW, uv=1, step=0.3)
    rbox(g, PLN, (0, y0 + t / 2, -0.001), (W - 2 * t + 0.001, t, D - 0.002), r=0.002, col=CW, uv=1)
    rbox(g, PLN, (0, (y0 + t + yct) / 2, zB + 0.005), (W - 2 * t + 0.001, yct - y0 - t + 0.001, 0.01), r=0.002, col=(0.90, 0.88, 0.84), uv=1)
    for zz in (zF - 0.04, zB + 0.05): rbox(g, PLN, (0, yct - 0.04, zz), (W - 2 * t + 0.001, 0.08, 0.018), r=0.002, col=CW, uv=1)
    # tampo de pedra (4 peças em volta do furo da cuba) e espelho de fundo
    stone = lambda: (0.30 + 0.04 * np.random.rand(), 0.29 + 0.04 * np.random.rand(), 0.28 + 0.04 * np.random.rand())
    np.random.seed(4)
    tx0, tx1 = -W / 2 - 0.01, W / 2 + 0.01; tz0, tz1 = zB, zF + 0.025
    pieces = [((tx0 + tx1) / 2, (tz0 + zs - hzs) / 2, tx1 - tx0, zs - hzs - tz0), ((tx0 + tx1) / 2, (zs + hzs + tz1) / 2, tx1 - tx0, tz1 - zs - hzs),
              ((tx0 - hxs) / 2, zs, -hxs - tx0, 2 * hzs + 0.002), ((hxs + tx1) / 2, zs, tx1 - hxs, 2 * hzs + 0.002)]
    for (cx_, cz_, sx_, sz_) in pieces:
        tmp = Geo(); rbox(tmp, PLN, (cx_, yct + tt / 2, cz_), (sx_, tt, sz_), r=0.003, col=(1, 1, 1), uv=2, step=0.05)
        a_ = tmp.parts[PLN]; P = a_['P'][-1]; C = a_['C'][-1].copy()
        nz = np.sin(P[:, 0] * 173) * np.sin(P[:, 2] * 191) * 0.5 + np.sin(P[:, 0] * 61 + P[:, 2] * 47) * 0.5
        C[:, :3] = np.clip(np.array([0.32, 0.31, 0.30]) + 0.08 * nz[:, None] + np.where(nz > 0.8, 0.25, 0)[:, None], 0, 1); a_['C'][-1] = C
        add_xf(g, tmp)
    rbox(g, PLN, (0, ytop + 0.035 - 0.0005, zB + 0.0075), (tx1 - tx0, 0.07, 0.015), r=0.003, col=(0.33, 0.32, 0.31), uv=2)
    # cuba de inox encaixada (borda apoiada no tampo), paredes e fundo com caimento para o ralo
    rim_o = rounded_rect(2 * hxs + 0.06, 2 * hzs + 0.06, 0.03, n=4); rim_i = rounded_rect(2 * hxs - 0.004, 2 * hzs - 0.004, 0.025, n=4)
    bot = rounded_rect(2 * hxs - 0.03, 2 * hzs - 0.03, 0.03, n=4)
    def ring(poly, y, s=1.0): return np.array([[x * s, y, z * s + zs] for x, z in poly])
    depth = 0.16
    rings = [ring(rim_o, ytop - 0.0005), ring(rim_o, ytop + 0.0035), ring(rim_i, ytop + 0.0035), ring(rim_i, ytop - 0.01), ring(bot, ytop - depth + 0.012), ring(bot, ytop - depth, 0.96)]
    loft(g, MET, rings, (0.80, 0.82, 0.84), cap0=False, cap1=True, uvs=3)
    # ralo com cesto (furinhos) no fundo
    yd = ytop - depth
    g.lathe(MET, (0, yd - 0.0005, zs), [(0, 0.004), (0.032, 0.0), (0.034, 0.002), (0.03, 0.004), (0.02, 0.003), (0, 0.003)], sides=24, col=C4((0.70, 0.72, 0.74)))
    for k in range(12):
        a = 2 * math.pi * k / 12
        g.lathe(MET, (0.013 * math.cos(a), yd + 0.0025, zs + 0.013 * math.sin(a)), [(0, 0.0), (0.0018, 0.0), (0.0018, 0.0012), (0, 0.0012)], sides=6, col=C4((0.15, 0.15, 0.16)))
    # cano do ralo, sifão em "U" e saída para a parede (atravessa o fundo do gabinete)
    pr = 0.016
    g.tube(PLN, [V(0, yd + 0.002, zs), V(0, yd - 0.08, zs)], [pr, pr], sides=12, col=lambda p, t: C4((0.92, 0.92, 0.90)))
    u = [V(0, yd - 0.08, zs)]
    for k in range(1, 9):
        a = math.pi * k / 8; u.append(V(0, yd - 0.08 - 0.045 * math.sin(a), zs - 0.045 * (1 - math.cos(a))))
    u += [V(0, yd - 0.06, zs - 0.09), V(0, yd - 0.045, zs - 0.11), V(0, yd - 0.045, zB + 0.02)]
    g.tube(PLN, u, [pr] * len(u), sides=12, col=lambda p, t: C4((0.92, 0.92, 0.90)))
    g.lathe(PLN, (0, 0, 0), [(0, 0)], sides=3, col=C4(DARK)) if False else None
    tmp = Geo(); tmp.lathe(PLN, (0, 0, 0), [(pr - 0.001, 0), (pr + 0.012, 0), (pr + 0.012, 0.006), (pr - 0.001, 0.006)], sides=14, col=C4((0.85, 0.85, 0.83)))
    add_xf(g, tmp, rot_x(math.pi / 2), (0, yd - 0.045, zB + 0.01 + 0.0005 + 0.006))
    for yy in (yd - 0.06,):
        tmp = Geo(); tmp.lathe(PLN, (0, 0, 0), [(pr - 0.001, -0.008), (pr + 0.004, -0.008), (pr + 0.004, 0.008), (pr - 0.001, 0.008)], sides=14, col=C4((0.85, 0.85, 0.83)))
        add_xf(g, tmp, None, (0, yd - 0.03, zs))
    # torneira de mesa: canopla, corpo, bica alta (pescoço de ganso) com arejador
    fz = zs - hzs - 0.045; cr = 0.019
    g.lathe(MET, (0, ytop - 0.0005, fz), [(0, 0), (0.03, 0), (0.03, 0.004), (0.024, 0.008), (0, 0.008)], sides=24, col=C4(CHROME))
    g.lathe(MET, (0, ytop + 0.0075, fz), [(0, 0), (cr, 0), (cr, 0.075), (cr * 0.92, 0.082), (0, 0.082)], sides=24, col=C4(CHROME))
    sp = [V(0, ytop + 0.07, fz)]
    for k in range(1, 13):
        a = math.pi * k / 12; sp.append(V(0, ytop + 0.07 + 0.12 * math.sin(a / 2 + 0.0) if k < 6 else ytop + 0.19 + 0.0 * k, fz) if False else None) if False else None
    path = [V(0, ytop + 0.07, fz), V(0, ytop + 0.16, fz)]
    R_ = (zs - fz) / 2; cz_ = fz + R_
    for k in range(1, 13):
        a = math.pi * k / 12; path.append(V(0, ytop + 0.16 + R_ * math.sin(a), cz_ - R_ * math.cos(a)))
    path.append(V(0, ytop + 0.14, zs))
    g.tube(MET, path, [0.0105] * len(path), sides=14, col=lambda p, t: C4(CHROME))
    g.lathe(MET, (0, ytop + 0.128, zs), [(0, 0), (0.012, 0), (0.0125, 0.014), (0, 0.016)], sides=14, col=C4(CHROME))
    g.lathe(PLN, (0, ytop + 0.1275, zs), [(0, 0), (0.009, 0), (0.009, 0.001), (0, 0.001)], sides=12, col=C4(DARK))
    # alavanca (monocomando): gira para cima no eixo X; cubo encaixado no corpo
    lv = M.node('alavanca', (0, ytop + 0.0835, fz), extras=dict(anim=dict(tipo='dobradica', eixo=[1, 0, 0], min=0.0, max=round(math.radians(-28), 4), dur=0.3,
                curva='suave', estado_inicial=0.0, alca=[0, ytop + 0.1, fz + 0.06], rotulo='torneira', verbos=['Abrir', 'Fechar'])))
    tmp = Geo(); tmp.lathe(MET, (0, 0, 0), [(0, -0.001), (0.016, -0.001), (0.016, 0.012), (0.012, 0.016), (0, 0.016)], sides=20, col=C4(CHROME))
    tmp.tube(MET, [V(0, 0.01, -0.004), V(0, 0.02, -0.03), V(0, 0.024, -0.07)], [0.007, 0.006, 0.0055], sides=10, col=lambda p, t: C4(CHROME))
    sphere(tmp, MET, (0, 0.024, -0.07), 0.0062, CHROME, seg=6)
    add_xf(lv.geo, tmp, None, (0, ytop + 0.0835, fz))
    # água (efeito): jato do arejador até o ralo, com respingo no fundo
    ag = M.node('agua', (0, ytop + 0.128, zs), extras=dict(efeito=dict(tipo='agua', quando='alavanca'), nota='a água cai dentro da cuba, no ralo (não vaza)'))
    tmp = Geo()
    tmp.tube(PLN, [V(0, ytop + 0.1285, zs), V(0, (ytop + 0.1285 + yd) / 2, zs), V(0, yd + 0.004, zs)], [0.0075, 0.0065, 0.006], sides=12, col=lambda p, t: C4((0.70, 0.85, 0.98), 0.55))
    tmp.lathe(PLN, (0, yd + 0.003, zs), [(0.006, 0.0), (0.03, 0.006), (0.035, 0.002)], sides=18, col=C4((0.80, 0.90, 1.0), 0.45))
    emissive(tmp); add_xf(ag.geo, tmp)
    # ---- portas (dobradiças nas laterais) e puxadores
    dz0 = zF + 0.002; dth = 0.018; ph = yct - 0.003 - (y0 + 0.003); py = (y0 + 0.003 + yct - 0.003) / 2
    for sx, nm in ((-1, 'porta_E'), (1, 'porta_D')):
        ax_x = sx * (W / 2 - 0.005); ax_z = dz0 + dth / 2
        pw = W / 2 - 0.0065 - 0.0015; cx = sx * (0.0015 + pw / 2)
        ang = math.radians(100) * (-1 if sx < 0 else 1)
        dn = M.node(nm, (ax_x, py, ax_z), extras=dict(anim=dict(tipo='dobradica', eixo=[0, 1, 0], min=0.0, max=round(ang, 4), dur=0.5, curva='suave', estado_inicial=0.0,
                    alca=[cx - sx * (pw / 2 - 0.04), 0.62, dz0 + dth + 0.05], rotulo='porta do gabinete', colide_com=['parede', 'movel'])))
        gd = dn.geo
        rbox(gd, PLN, (cx, py, dz0 + dth / 2), (pw, ph, dth), r=0.003, col=CW, uv=1, step=0.25)
        rbox(gd, PLN, (cx, py, dz0 + dth + 0.0015), (pw - 0.07, ph - 0.07, 0.004), r=0.002, col=tuple(np.array(CW) * 0.96), uv=1)
        kx = cx - sx * (pw / 2 - 0.04)
        gd.tube(MET, [V(kx, 0.55, dz0 + dth + 0.025), V(kx, 0.69, dz0 + dth + 0.025)], [0.006, 0.006], sides=10, col=lambda p, tt_: C4(CHROME))
        for yy in (0.565, 0.675): gd.tube(MET, [V(kx, yy, dz0 + dth - 0.0005), V(kx, yy, dz0 + dth + 0.025)], [0.0045, 0.0045], sides=8, col=lambda p, tt_: C4(CHROME))
        for yy in (y0 + 0.08, yct - 0.08):
            g.tube(MET, [V(ax_x, yy - 0.025, ax_z), V(ax_x, yy + 0.025, ax_z)], [0.005, 0.005], sides=10, col=lambda p, tt_: C4(CHROME))
            for e2 in (-1, 1): sphere(g, MET, (ax_x, yy + e2 * 0.025, ax_z), 0.005, CHROME, seg=5, sy=0.5)
            rbox(g, MET, (sx * (W / 2 - 0.0095), yy, (zF - 0.0005 + ax_z) / 2), (0.013, 0.04, ax_z - zF + 0.0005), r=0.0008, col=CHROME, uv=1)
    # ---- conteúdo do gabinete (só com uma porta aberta)
    cn = M.node('conteudo_gabinete', extras=dict(mostrar_quando=['porta_E', 'porta_D'], nota='embaixo da pia'))
    gc = cn.geo; yf = y0 + t
    lx, li = CT.lixeira(r=0.085, h=0.25); place(gc, lx, -0.22, yf - EMB, 0.0)
    place(gc, CT.pano_dobrado()[0], -0.22, yf + li['altura'] - 0.003 - EMB, 0.0, yaw=0.3) if False else None
    place(gc, CT.detergente()[0], 0.16, yf - EMB, -0.12)
    place(gc, CT.detergente(cor=(0.95, 0.75, 0.20), h=0.17)[0], 0.22, yf - EMB, -0.09, yaw=0.4)
    place(gc, CT.borrifador()[0], 0.27, yf - EMB, -0.15, yaw=-0.5)
    eg, ei = CT.esponja(); place(gc, eg, 0.17, yf - EMB, 0.10, yaw=0.2)
    place(gc, CT.esponja(cor=(0.35, 0.65, 0.90), fibra=(0.95, 0.85, 0.30))[0], 0.17, yf + ei['altura'] - 2 * EMB, 0.10, yaw=-0.15)
    place(gc, CT.pano_dobrado()[0], 0.08, yf - EMB, 0.13, yaw=0.1)
    M.empty('COL_corpo', (0, ytop / 2, 0.0125), extras=dict(shape='box', size=[W + 0.02, ytop, D + 0.025], bloqueia=True, camada='movel'))
    M.empty('SURF_tampo', (0, ytop, zs), extras=dict(shape='box', size=[W, 0, D], recebe='louça, objetos', exceto='furo da cuba'))
    M.empty('IP_lavar', (0, 0, zF + 0.30), extras=dict(acao='lavar', olhar='-Z', alavanca='alavanca', duracao=3.5, rotulo='Lavar as mãos',
            sequencia=['ir até a frente da cuba', 'virar para a pia', 'abrir a torneira (interagir)', 'lavar (água correndo)', 'fechar a torneira (interagir)']))
    M.bake_ao(maxd=0.2, strength=0.5)
    return finish(M)


ALL = [cama, sofa, geladeira, fogao, pia]

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/glb_e2'
    only = sys.argv[2:] or None
    os.makedirs(out, exist_ok=True)
    for f in ALL:
        if only and f.__name__ not in only: continue
        M = f(); fn = os.path.join(out, M.id + '.glb'); n = M.write_glb(fn)
        err, warn, info = G.verify(fn)
        print('%-20s %7d bytes %6d vért. %6d tri. erros=%d avisos=%d %s' % (M.id, n, info['vertices'], info['triangulos'], len(err), len(warn), M.meta['dimensoes']))
        for e in err: print('   ERRO:', e)
        for w in warn: print('   aviso:', w)
