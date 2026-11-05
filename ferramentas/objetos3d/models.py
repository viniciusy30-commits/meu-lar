"""Etapa 1 da biblioteca 3D: protótipos (vaso decorativo, caixa e bola com física, poltrona e aparador interativos).

Escala: unidades do jogo (m). O personagem adulto do Meu Lar mede ~1,45 m; as medidas abaixo foram tiradas da pose
sentada real (ferramentas/etapa83_sentar.py -> sit.txt), não de tabela.
Uso: python3 models.py <pasta de saída>   (grava <id>.glb, verifica cada um e imprime o relatório)
"""
import sys, os, math, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import *          # noqa  (Geo, rbox, sphere, disc, piping, add_xf, rot_*)
import glb_lib as G

# chaves (textura, material do jogo, recorte)
OAK = ('carvalho.png', 6, 0); LIN = ('linho.png', 7, 0); GLZ = ('esmalte.png', 0, 0); SOIL = ('terra.png', 0, 0)
LEAF = ('folha_costela.png', 8, 1); MET = ('escovado.png', 11, 0); PLN = ('liso.png', 0, 0)
KRAFT = ('papelao_liso.png', 0, 0); PRINT = ('papelao_impresso.png', 0, 1); TAPE = ('fita.png', 0, 0); BALL = ('bola.png', 0, 0)
MATNAMES = {OAK: 'madeira_carvalho', LIN: 'tecido_linho', GLZ: 'ceramica_esmaltada', SOIL: 'terra_vaso', LEAF: 'folha_planta',
            MET: 'latao_escovado', PLN: 'plastico_fosco', KRAFT: 'papelao', PRINT: 'papelao_impresso', TAPE: 'fita_adesiva', BALL: 'borracha_bola'}

OAKC = (0.92, 0.74, 0.52); OAKD = (0.70, 0.50, 0.33); BRASS = (0.93, 0.76, 0.42)


def meta(aid, nome, cat, sub, classe, fis, **kw):
    m = dict(id=aid, nome=nome, categoria=cat, subcategoria=sub, classe=classe, versao=1, escala='m (jogo; adulto ~1,45 m)',
             eixos=dict(cima='+Y', frente='+Z', origem='centro do piso do objeto'), fisica=fis)
    m.update(kw); return m


def finish(M, dims_note=None):
    lo, hi = M.bounds(); d = hi - lo
    M.meta['dimensoes'] = dict(largura=round(float(d[0]), 4), altura=round(float(d[1]), 4), profundidade=round(float(d[2]), 4))
    M.meta['caixa'] = dict(min=[round(float(x), 4) for x in lo], max=[round(float(x), 4) for x in hi])
    M.matnames = MATNAMES
    return M


def recolor(g, key, fn):
    """aplica fn(P) -> cores (n,3) na última peça adicionada com a chave key."""
    a = g.parts[key]; P = a['P'][-1]; C = a['C'][-1].copy(); C[:, :3] = fn(P); a['C'][-1] = C


# ================================================================================================ 1. VASO (decorativo)
def vaso():
    M = G.Model('decor_vaso_costela', meta('decor_vaso_costela', 'Vaso com costela-de-adão', 'decoracao', 'plantas', 'decorativo',
               dict(tipo='estatico', massa=14.0, motivo='vaso cheio de terra: pesado, não deve tombar nem deslizar ao encostar'),
               estados=[], interacoes=[], grade=[1, 1]))
    pot = M.node('vaso')
    g = pot.geo
    prof = [(0.0, 0.0), (0.098, 0.0), (0.106, 0.004), (0.108, 0.014), (0.104, 0.022), (0.112, 0.03), (0.128, 0.07), (0.146, 0.13),
            (0.160, 0.20), (0.168, 0.26), (0.171, 0.31), (0.172, 0.335), (0.176, 0.348), (0.181, 0.356), (0.181, 0.364),
            (0.176, 0.371), (0.168, 0.373), (0.160, 0.369), (0.157, 0.36), (0.155, 0.33), (0.153, 0.30)]
    g.lathe(GLZ, (0, 0, 0), prof, sides=40, col=(1, 1, 1, 1), uscale=2.0, vscale=2.4)
    def potcol(P):
        a = np.arctan2(P[:, 2], P[:, 0]); r = np.hypot(P[:, 0], P[:, 2])
        line = 0.05 + 0.012 * np.sin(a * 5) + 0.008 * np.sin(a * 11 + 1.3)          # borda irregular do esmalte
        glaze = np.array([0.50, 0.63, 0.57]); clay = np.array([0.78, 0.50, 0.36])
        t = np.clip((P[:, 1] - line) / 0.006, 0, 1)[:, None]
        c = clay * (1 - t) + glaze * t
        c = c * (1 + 0.10 * np.clip((P[:, 1] - 0.20) / 0.17, 0, 1))[:, None]          # mais claro perto da borda (esmalte mais fino)
        inner = (r < 0.1575) & (P[:, 1] > 0.29)
        c[inner] = c[inner] * 0.55
        return c
    recolor(g, GLZ, potcol)
    # terra levemente abaulada + pedrinhas
    disc(g, SOIL, (0, 0.30, 0), 0.154, height=lambda t: 0.012 * (1 - t * t) + 0.002 * math.sin(t * 9), rings=6, seg=36, uv=3.2)
    rng = np.random.default_rng(4)
    for i in range(9):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.06, 0.135); s = rng.uniform(0.008, 0.014)
        sphere(g, PLN, (math.cos(a) * r, 0.31 + 0.006 * (1 - (r / 0.154) ** 2) + s * 0.25, math.sin(a) * r), s, tuple(np.array([0.86, 0.84, 0.80]) * rng.uniform(0.85, 1.0)), seg=6, sy=0.55)
    # planta (nó próprio: pode balançar no futuro)
    pl = M.node('planta', (0, 0.31, 0))
    gp = pl.geo
    golden = math.radians(137.5)
    leaves = [(0.46, 72, 0.40), (0.36, 58, 0.38), (0.54, 80, 0.42), (0.30, 50, 0.34), (0.42, 66, 0.40), (0.26, 44, 0.31), (0.50, 76, 0.39), (0.33, 54, 0.36), (0.22, 38, 0.27)]
    for i, (plen, elev, lsz) in enumerate(leaves):
        az = i * golden + 0.4
        dirh = np.array([math.cos(az), 0, math.sin(az)])
        base = np.array([0, 0.31, 0]) + dirh * 0.02 * (i % 3)
        # pecíolo: arco subindo e abrindo
        pts = []; e = math.radians(elev)
        for k in range(9):
            t = k / 8; ang = e * (1 - 0.35 * t)            # vai deitando
            pts.append(base + dirh * (plen * t * math.cos(ang) * 0.95) + np.array([0, plen * t * math.sin(e) * (1 - 0.18 * t), 0]))
        pts = np.array(pts)
        gp.tube(LEAF if False else PLN, pts, [0.0095 - 0.0035 * k / 8 for k in range(9)], sides=6,
                col=lambda p, t: (0.36, 0.55, 0.30, 1), vscale=1.0)
        tip = pts[-1]; tdir = (pts[-1] - pts[-2]); tdir /= np.linalg.norm(tdir)
        # lâmina: grade nu x nv, base (v=0) no fim do pecíolo; curva para baixo ao longo do comprimento e dobra em V no meio
        nu, nv = 9, 11; L = lsz; Wd = lsz * 0.98
        side = np.cross(tdir, [0, 1, 0]); side /= np.linalg.norm(side)
        fwd0 = dirh * math.cos(math.radians(34)) + np.array([0, math.sin(math.radians(34)), 0])  # sai quase na horizontal
        upn = np.cross(side, fwd0); upn /= np.linalg.norm(upn)
        if upn[1] < 0: upn = -upn
        droop = math.radians(62 + 12 * (i % 3))
        P = np.zeros((nv, nu, 3)); UV = np.zeros((nv, nu, 2))
        cur = tip.copy(); d = fwd0.copy(); spine = []
        for j in range(nv):
            spine.append((cur.copy(), d.copy()))
            t = j / (nv - 1); a = droop / (nv - 1)
            # gira d em torno de 'side' (para baixo)
            d = d * math.cos(a) - np.cross(side, d) * math.sin(a); d /= np.linalg.norm(d)
            cur = cur + d * L / (nv - 1)
        for j in range(nv):
            c, dd = spine[j]; nrm_ = np.cross(dd, side); nrm_ /= np.linalg.norm(nrm_)
            if nrm_[1] < 0 and j == 0: pass
            for k in range(nu):
                s = (k / (nu - 1) - 0.5)
                fold = 0.11 * Wd * abs(s * 2) ** 1.3                      # bordas descem (V raso)
                wav = 0.006 * math.sin(k * 2.1 + j * 1.3)
                P[j, k] = c + side * s * Wd - (nrm_ if nrm_[1] > 0 else -nrm_) * (fold + wav)
                UV[j, k] = (k / (nu - 1), j / (nv - 1))
        Pf = P.reshape(-1, 3); UVf = UV.reshape(-1, 2); T = []
        for j in range(nv - 1):
            for k in range(nu - 1):
                a_ = j * nu + k; T += [(a_, a_ + nu, a_ + 1), (a_ + 1, a_ + nu, a_ + nu + 1)]
        T = np.array(T); N = grid_normals(Pf, T)
        if N[:, 1].mean() < 0: T = T[:, [0, 2, 1]]; N = -N
        shade = 0.9 + 0.12 * ((i * 37) % 7) / 6
        gp.add(LEAF, Pf, N, [(shade, shade, shade, 1)] * len(Pf), UVf, T)
    # colisor e metadados
    M.empty('COL_vaso', (0, 0.186, 0), extras=dict(shape='cyl', size=[0.36, 0.372, 0.36], bloqueia=True, camada='movel'))
    M.bake_ao(maxd=0.18, strength=0.5)
    return finish(M)


# ================================================================================================ 2. CAIXA (física)
def caixa():
    W, H, D = 0.40, 0.30, 0.32
    M = G.Model('fis_caixa_papelao', meta('fis_caixa_papelao', 'Caixa de papelão', 'objetos', 'utilidades', 'fisico',
               dict(tipo='dinamico', massa=1.2, atrito=0.62, restituicao=0.12, amortecimento=0.08, amortecimento_ang=0.25,
                    colisor='COL_caixa', motivo='caixa leve: pode ser empurrada, cair de móveis e tombar; repousa sem tremer (dorme parada)'),
               estados=[], interacoes=[dict(acao='empurrar', modo='contato do personagem')], grade=[1, 1]))
    b = M.node('caixa', (0, 0, 0)); g = b.geo
    rbox(g, KRAFT, (0, H / 2, 0), (W, H, D), r=0.006, col=(1, 1, 1), uv=2.2, step=0.5)
    # fresta entre as abas maiores (ao longo de x), coberta pela fita
    g.add(PLN, [(-W / 2 + 0.006, H + 0.0004, -0.002), (W / 2 - 0.006, H + 0.0004, -0.002), (W / 2 - 0.006, H + 0.0004, 0.002), (-W / 2 + 0.006, H + 0.0004, 0.002)],
          [(0, 1, 0)] * 4, [(0.30, 0.22, 0.15, 1)] * 4, [(0, 0), (1, 0), (1, 1), (0, 1)], [(0, 2, 1), (0, 3, 2)])
    # fita sobre a fresta, descendo 9 cm nas laterais (esquerda e direita)
    tw = 0.056; e = 0.0012
    g.add(TAPE, [(-W / 2, H + e, -tw / 2), (W / 2, H + e, -tw / 2), (W / 2, H + e, tw / 2), (-W / 2, H + e, tw / 2)], [(0, 1, 0)] * 4, [(1, 1, 1, 1)] * 4,
          [(0, 0), (1.6, 0), (1.6, 1), (0, 1)], [(0, 2, 1), (0, 3, 2)])
    for sx in (-1, 1):
        x = sx * (W / 2 + e)
        q = [(x, H, -tw / 2), (x, H, tw / 2), (x, H - 0.09, tw / 2), (x, H - 0.09, -tw / 2)]
        g.add(TAPE, q, [(sx, 0, 0)] * 4, [(1, 1, 1, 1)] * 4, [(0, 0), (0, 1), (0.35, 1), (0.35, 0)], [(0, 1, 2), (0, 2, 3)])
    # marcas de uso: cantos levemente amassados não são modelados (caixa nova)
    # impressão na frente e no lado direito (plano colado 0,6 mm fora)
    o = 0.0006
    def printq(face):
        if face == 'z':
            z = D / 2 + o; q = [(-0.16, 0.025, z), (0.16, 0.025, z), (0.16, 0.255, z), (-0.16, 0.255, z)]
            g.add(PRINT, q, [(0, 0, 1)] * 4, [(1, 1, 1, 1)] * 4, [(0, 1), (1, 1), (1, 0), (0, 0)], [(0, 1, 2), (0, 2, 3)])
        else:
            x = W / 2 + o; q = [(x, 0.02, 0.10), (x, 0.02, -0.10), (x, 0.20, -0.10), (x, 0.20, 0.10)]
            g.add(PRINT, q, [(1, 0, 0)] * 4, [(1, 1, 1, 1)] * 4, [(0, 1), (1, 1), (1, 0), (0, 0)], [(0, 1, 2), (0, 2, 3)])
    printq('z'); printq('x')
    M.empty('COL_caixa', (0, H / 2, 0), extras=dict(shape='box', size=[W, H, D], bloqueia=False, camada='objeto_solto'))
    M.empty('SURF_tampa', (0, H, 0), extras=dict(shape='box', size=[W - 0.02, 0, D - 0.02], recebe='objetos pequenos'))
    M.bake_ao(maxd=0.12, strength=0.35)
    return finish(M)


# ================================================================================================ 3. BOLA (física)
def bola():
    R = 0.11
    M = G.Model('fis_bola', meta('fis_bola', 'Bola de borracha', 'objetos', 'brinquedos', 'fisico',
               dict(tipo='dinamico', massa=0.35, atrito=0.55, restituicao=0.62, amortecimento=0.03, amortecimento_ang=0.06, rolamento=0.012,
                    colisor='COL_bola', motivo='bola oca de borracha: quica, rola e é chutada quando o personagem corre contra ela'),
               estados=[], interacoes=[dict(acao='chutar/empurrar', modo='contato do personagem')], grade=[1, 1]))
    b = M.node('bola', (0, R, 0)); g = b.geo
    sphere(g, BALL, (0, R, 0), R, (1, 1, 1), seg=18)
    M.empty('COL_bola', (0, R, 0), extras=dict(shape='sphere', size=[2 * R, 2 * R, 2 * R], bloqueia=False, camada='objeto_solto'))
    M.bake_ao(maxd=0.05, strength=0.2)
    return finish(M)


# ================================================================================================ 4. POLTRONA (interativa: sentar)
SIT_Z = 0.20            # raiz do personagem sentado (pés) - ver etapa83_sentar.py: traseiro fica 0,30 m atrás da raiz
SEAT_TOP = 0.355        # topo da almofada em repouso; sentado afunda até 0,342
def poltrona():
    M = G.Model('int_poltrona', meta('int_poltrona', 'Poltrona de linho', 'sala', 'assentos', 'interativo',
               dict(tipo='estatico', massa=24.0, motivo='móvel grande ancorado: não tomba nem desliza com o personagem'),
               estados=['livre', 'ocupada'], grade=[1, 1],
               interacoes=[dict(acao='sentar', ponto='IP_sentar', animacoes=['sentar', 'sentado', 'levantar'], cancelavel=True)]))
    fr = M.node('estrutura'); g = fr.geo
    X = 0.33
    # pernas torneadas inclinadas (frente e trás), que continuam até os braços
    def leg(x, z0, z1, y1, r0, r1):
        pts = [V(x, 0, z0), V(x + (0.002 if x > 0 else -0.002), y1 * 0.5, (z0 + z1) / 2), V(x, y1, z1)]
        g.tube(OAK, pts, [r0, (r0 + r1) / 2 * 1.05, r1], sides=12, col=lambda p, t: OAKC + (1,), vscale=1.6)
        g.lathe(OAK, (x, 0, z0), [(0.0, 0.0), (r0 * 0.9, 0.0), (r0, 0.004)], sides=12, col=OAKD + (1,))   # sapata
    for sx in (-1, 1):
        x = sx * X
        leg(x, 0.265, 0.235, 0.485, 0.016, 0.022)       # dianteira
        leg(x, -0.285, -0.235, 0.485, 0.016, 0.022)     # traseira
        # braço: tábua com ponta arredondada, mais larga na frente
        rbox(g, OAK, (x, 0.494, 0.005), (0.072, 0.024, 0.60), r=0.011, col=OAKC, uv=2.0, step=0.12)
        rbox(g, OAK, (x, 0.494, 0.27), (0.084, 0.024, 0.07), r=0.012, col=OAKC, uv=2.0, step=0.06)
        # travessa lateral do assento
        rbox(g, OAK, (x * 0.94, 0.215, 0.0), (0.026, 0.05, 0.50), r=0.006, col=OAKC, uv=2.0)
    for z in (0.235, -0.235):
        rbox(g, OAK, (0, 0.215, z), (0.62, 0.05, 0.026), r=0.006, col=OAKC, uv=2.0)
    # plataforma do assento (cinta de tecido escuro sob a almofada)
    rbox(g, LIN, (0, 0.238, 0.0), (0.60, 0.012, 0.47), r=0.004, col=(0.25, 0.26, 0.27), uv=3.0, step=0.5)
    # encosto: dois montantes inclinados + travessa de cima + 2 ripas
    lean = math.radians(9)
    for sx in (-1, 1):
        a = V(sx * 0.29, 0.22, -0.245); b2 = a + V(0, 0.54 * math.cos(lean), -0.54 * math.sin(lean))
        g.tube(OAK, [a, (a + b2) / 2, b2], [0.017, 0.018, 0.016], sides=10, col=lambda p, t: OAKC + (1,), vscale=1.6)
    top = V(0, 0.22 + 0.53 * math.cos(lean), -0.245 - 0.53 * math.sin(lean))
    tmp = Geo(); rbox(tmp, OAK, (0, 0, 0), (0.62, 0.05, 0.024), r=0.008, col=OAKC, uv=2.0)
    add_xf(g, tmp, rot_x(lean), top)
    for hh in (0.30, 0.44):
        tmp = Geo(); rbox(tmp, OAK, (0, 0, 0), (0.58, 0.035, 0.016), r=0.006, col=OAKD, uv=2.0)
        add_xf(g, tmp, rot_x(lean), V(0, 0.22 + hh * math.cos(lean), -0.245 - hh * math.sin(lean) - 0.004))
    # ---- almofada do assento (nó próprio: afunda quando ocupada)
    fab = (0.47, 0.57, 0.60); pip = (0.36, 0.44, 0.47)
    cu = M.node('almofada_assento', (0, 0.244, 0.06), extras=dict(anim=dict(tipo='escala', eixo=[0, 1, 0], min=1.0, max=0.88, dur=0.6,
                curva='suave', gatilho='ocupado', estado_inicial=1.0)))
    gc = cu.geo
    rbox(gc, LIN, (0, 0.2995, 0.06), (0.585, 0.111, 0.385), r=0.042, col=fab, uv=3.2, puff=0.016, step=0.07)
    piping(gc, LIN, 0, 0.2995 + 0.111 / 2 - 0.023, 0.06, 0.578, 0.378, 0.0075, pip, rad=0.042)
    piping(gc, LIN, 0, 0.2995 - 0.111 / 2 + 0.023, 0.06, 0.578, 0.378, 0.0075, pip, rad=0.042)
    # ---- almofada do encosto (inclinada, capitonê com botões)
    bk = M.node('almofada_encosto', (0, 0.345, -0.15)); gb = bk.geo
    tmp = Geo()
    th = 0.13; hh = 0.42
    rbox(tmp, LIN, (0, hh / 2, -th / 2), (0.57, hh, th), r=0.045, col=fab, uv=3.2, puff=0.02, step=0.07)
    piping(tmp, LIN, 0, 0, 0, 0, 0, 0, pip) if False else None
    for (bx, by) in ((-0.15, 0.13), (0.0, 0.13), (0.15, 0.13), (-0.15, 0.29), (0.0, 0.29), (0.15, 0.29)):
        sphere(tmp, LIN, (bx, by, 0.019 + 0.0), 0.012, tuple(np.array(fab) * 0.8), seg=8, sy=0.6)
    tmp2 = Geo()
    # pregas que saem dos botões (pequenas depressões desenhadas como faixas mais escuras)
    add_xf(gb, tmp, rot_x(lean), V(0, 0.345, -0.108))
    # ---- colisores, superfícies e ponto de sentar
    M.empty('COL_base', (0, 0.18, -0.005), extras=dict(shape='box', size=[0.72, 0.36, 0.57], bloqueia=True, camada='movel'))
    for sx in (-1, 1):
        M.empty('COL_braco_' + ('D' if sx > 0 else 'E'), (sx * X, 0.43, 0.005), extras=dict(shape='box', size=[0.085, 0.14, 0.60], bloqueia=True, camada='movel'))
        M.empty('SURF_braco_' + ('D' if sx > 0 else 'E'), (sx * X, 0.506, 0.005), extras=dict(shape='box', size=[0.07, 0, 0.56], recebe='copo, livro, controle'))
    M.empty('COL_encosto', (0, 0.56, -0.235), extras=dict(shape='box', size=[0.64, 0.42, 0.16], bloqueia=True, camada='movel'))
    M.empty('IP_sentar', (0, 0, SIT_Z), extras=dict(acao='sentar', aproximacao=[0, 0, SIT_Z + 0.42], inicio=[0, 0, SIT_Z + 0.12],
            assento_y=SEAT_TOP - 0.013, olhar='+Z', ocupado_por=None,
            sequencia=['andar até a aproximação', 'virar de costas', 'sentar (1,3 s)', 'sentado (laço)', 'levantar (1,0 s)'],
            cancelar='mexer o analógico ou tocar em Levantar: levanta e volta à aproximação; durante a ida, só para'))
    M.bake_ao(maxd=0.22, strength=0.55)
    return finish(M)


# ================================================================================================ 5. APARADOR (interativo: portas e gavetas)
def aparador():
    W, D, H, LEG = 1.10, 0.40, 0.66, 0.15
    M = G.Model('int_aparador', meta('int_aparador', 'Aparador de carvalho', 'sala', 'armazenamento', 'interativo',
               dict(tipo='estatico', massa=38.0, motivo='móvel grande ancorado; só portas e gavetas se mexem (dobradiça e trilho com limite)'),
               estados=['fechado', 'abrindo', 'aberto', 'fechando'], grade=[2, 1],
               interacoes=[dict(acao='abrir/fechar', alvo='peça mais perto do olhar', pecas=['gaveta_E', 'gaveta_D', 'porta_E', 'porta_D'])]))
    body = M.node('corpo'); g = body.geo
    y0 = LEG; t = 0.02; zf = D / 2 - 0.012                # face frontal da carcaça (portas ficam rente a ela)
    # pés palito inclinados
    for sx in (-1, 1):
        for sz in (-1, 1):
            x = sx * (W / 2 - 0.07); z = sz * (D / 2 - 0.07)
            g.tube(OAK, [V(x + sx * 0.025, 0.012, z + sz * 0.02), V(x, y0 + 0.01, z)], [0.013, 0.02], sides=12, col=lambda p, tt: OAKD + (1,), vscale=2)
            g.lathe(MET, (x + sx * 0.025, 0, z + sz * 0.02), [(0, 0), (0.013, 0), (0.0135, 0.018), (0.012, 0.02)], sides=12, col=BRASS + (1,))
    # carcaça: tampo (com borda chanfrada), laterais, base, fundo, divisória e prateleira
    rbox(g, OAK, (0, H - 0.0125, 0), (W, 0.025, D), r=0.008, col=OAKC, uv=1.6, step=0.3)
    rbox(g, OAK, (0, y0 + t / 2, -0.004), (W - 0.01, t, D - 0.02), r=0.004, col=OAKC, uv=1.6, step=0.4)
    for sx in (-1, 1):
        rbox(g, OAK, (sx * (W / 2 - t / 2), (y0 + H - 0.025) / 2, 0), (t, H - 0.025 - y0, D - 0.004), r=0.004, col=OAKC, uv=1.6, step=0.3)
    rbox(g, OAK, (0, (y0 + H) / 2, -D / 2 + 0.006), (W - 0.02, H - y0 - 0.02, 0.008), r=0.002, col=OAKD, uv=1.6, step=0.4)
    rbox(g, OAK, (0, 0.33, -0.01), (0.018, 0.32, D - 0.04), r=0.003, col=OAKC, uv=1.6)                       # divisória das portas
    ydr = 0.49                                                                                               # trave entre portas e gavetas
    rbox(g, OAK, (0, ydr + 0.009, -0.004), (W - 0.03, 0.018, D - 0.03), r=0.003, col=OAKC, uv=1.6, step=0.4)
    rbox(g, OAK, (0, 0.5715, -0.01), (0.018, 0.125, D - 0.04), r=0.003, col=OAKC, uv=1.6)                     # divisória das gavetas
    for sx in (-1, 1):
        rbox(g, OAK, (sx * W / 4, y0 + 0.02 + 0.17, -0.02), (W / 2 - 0.05, 0.016, D - 0.08), r=0.003, col=OAKC, uv=1.6)   # prateleira
    # interior: livros deitados e uma tigela (aparecem ao abrir)
    rng = np.random.default_rng(7)
    yb = y0 + 0.02
    for k, (cl, hh, ww) in enumerate(((0.62, 0.20, 0.17), (0.25, 0.42, 0.66), (0.80, 0.70, 0.55))):
        tk = 0.028
        rbox(g, LIN, (-W / 4 - 0.02, yb + tk / 2 + k * tk, -0.03 + k * 0.006), (0.24 - k * 0.02, tk, 0.18), r=0.004, col=(cl, hh, ww), uv=3, step=0.3)
    g.lathe(GLZ, (W / 4, yb + 0.188, -0.03), [(0, 0), (0.05, 0), (0.07, 0.03), (0.09, 0.07), (0.086, 0.074), (0.066, 0.04), (0.0, 0.03)], sides=24, col=(0.86, 0.58, 0.42, 1))
    rbox(g, LIN, (W / 4 + 0.02, yb + 0.03, -0.04), (0.26, 0.06, 0.2), r=0.01, col=(0.86, 0.82, 0.74), uv=3, puff=0.008, step=0.1)   # toalhas dobradas
    # ---- gavetas (trilho em +Z, curso 0,26 m)
    dh = 0.131; dy = 0.5655
    for sx, nm in ((-1, 'gaveta_E'), (1, 'gaveta_D')):
        fw = W / 2 - 0.0235; cx = sx * (0.0015 + fw / 2)
        dn = M.node(nm, (cx, dy, zf), extras=dict(anim=dict(tipo='trilho', eixo=[0, 0, 1], min=0.0, max=0.26, dur=0.42, curva='suave',
                    estado_inicial=0.0, alca=[cx, dy, zf + 0.04], rotulo='gaveta', colide_com=['parede', 'movel'])))
        gd = dn.geo
        rbox(gd, OAK, (cx, dy, zf + 0.009), (fw, dh, 0.018), r=0.004, col=OAKC, uv=1.6, step=0.2)
        # caixa interna da gaveta (laterais, fundo, traseira)
        for s2 in (-1, 1):
            rbox(gd, OAK, (cx + s2 * (fw / 2 - 0.03), dy - 0.008, zf - 0.17), (0.012, dh - 0.03, 0.33), r=0.002, col=OAKD, uv=1.6)
        rbox(gd, OAK, (cx, dy - dh / 2 + 0.012, zf - 0.17), (fw - 0.06, 0.006, 0.33), r=0.001, col=OAKD, uv=1.6)
        rbox(gd, OAK, (cx, dy - 0.008, zf - 0.335), (fw - 0.06, dh - 0.03, 0.012), r=0.002, col=OAKD, uv=1.6)
        # puxador redondo de latão
        gd.lathe(MET, (cx, dy, zf + 0.018), [(0, 0), (0.007, 0), (0.007, 0.01), (0.004, 0.016)], sides=12, col=BRASS + (1,)) if False else None
        gd.tube(MET, [V(cx, dy, zf + 0.018), V(cx, dy, zf + 0.032)], [0.005, 0.005], sides=10, col=lambda p, tt: BRASS + (1,))
        sphere(gd, MET, (cx, dy, zf + 0.038), 0.012, BRASS, seg=10, sy=0.8)
    # ---- portas (dobradiça nas bordas externas; abrem para fora até 100°)
    ph = 0.331; py = 0.3315
    for sx, nm in ((-1, 'porta_E'), (1, 'porta_D')):
        hx = sx * (W / 2 - 0.012)            # eixo da dobradiça
        pw = W / 2 - 0.0235
        cx = sx * (0.0015 + pw / 2)
        # porta esquerda gira para -X (ângulo negativo em Y); direita para +X
        ang = math.radians(100) * (-1 if sx < 0 else 1)
        dn = M.node(nm, (hx, py, zf), extras=dict(anim=dict(tipo='dobradica', eixo=[0, 1, 0], min=0.0, max=round(ang, 4), dur=0.55, curva='suave',
                    estado_inicial=0.0, alca=[cx - sx * (pw / 2 - 0.05), py + 0.08, zf + 0.04], rotulo='porta', raio=round(pw, 3), colide_com=['parede', 'movel'])))
        gd = dn.geo
        rbox(gd, OAK, (cx, py, zf + 0.009), (pw, ph, 0.018), r=0.004, col=OAKC, uv=1.6, step=0.2)
        # almofada em relevo (moldura interna)
        rbox(gd, OAK, (cx, py, zf + 0.0205), (pw - 0.07, ph - 0.07, 0.006), r=0.003, col=tuple(np.array(OAKC) * 0.96), uv=1.6, step=0.2)
        # dobradiças (2 por porta)
        for hy in (py - ph / 2 + 0.05, py + ph / 2 - 0.05):
            g.tube(MET, [V(hx, hy - 0.02, zf + 0.004), V(hx, hy + 0.02, zf + 0.004)], [0.0045, 0.0045], sides=8, col=lambda p, tt: BRASS + (1,))
        kx = cx - sx * (pw / 2 - 0.05)
        gd.tube(MET, [V(kx, py + 0.08, zf + 0.018), V(kx, py + 0.08, zf + 0.032)], [0.005, 0.005], sides=10, col=lambda p, tt: BRASS + (1,))
        sphere(gd, MET, (kx, py + 0.08, zf + 0.038), 0.012, BRASS, seg=10, sy=0.8)
    M.empty('COL_corpo', (0, (y0 + H) / 2 + 0.0, 0), extras=dict(shape='box', size=[W, H - y0, D], bloqueia=True, camada='movel'))
    M.empty('COL_pes', (0, y0 / 2, 0), extras=dict(shape='box', size=[W - 0.1, y0, D - 0.1], bloqueia=True, camada='movel'))
    M.empty('SURF_tampo', (0, H, 0), extras=dict(shape='box', size=[W - 0.02, 0, D - 0.02], recebe='objetos'))
    M.empty('IP_usar', (0, 0, D / 2 + 0.45), extras=dict(acao='abrir/fechar', aproximacao=[0, 0, D / 2 + 0.45], olhar='-Z'))
    M.bake_ao(maxd=0.22, strength=0.55)
    return finish(M)


ALL = [vaso, caixa, bola, poltrona, aparador]

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
    os.makedirs(out, exist_ok=True)
    rep = {}
    for f in ALL:
        M = f(); fn = os.path.join(out, M.id + '.glb'); n = M.write_glb(fn)
        err, warn, info = G.verify(fn)
        rep[M.id] = dict(erros=err, avisos=warn, info=info)
        print('%-22s %7d bytes  %6d vért. %6d tri.  erros=%d avisos=%d %s' % (M.id, n, info['vertices'], info['triangulos'], len(err), len(warn), M.meta['dimensoes']))
        for e in err: print('   ERRO:', e)
        for w in warn: print('   aviso:', w)
    json.dump(rep, open(os.path.join(out, 'verificacao.json'), 'w'), ensure_ascii=False, indent=1)
