"""Protótipos da biblioteca 3D (Etapa 0/83): vaso decorativo, caixa e bola com física, poltrona e aparador interativos.
Revisados pelo Plano Mestre v4: nada flutuando (verificado por integridade.py) e conteúdo interno detalhado no aparador.

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
        tt = r / 0.154; ysoil = 0.30 + 0.012 * (1 - tt * tt) + 0.002 * math.sin(tt * 9)
        sphere(g, PLN, (math.cos(a) * r, ysoil + s * 0.55 * 0.35, math.sin(a) * r), s, tuple(np.array([0.86, 0.84, 0.80]) * rng.uniform(0.85, 1.0)), seg=6, sy=0.55)
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
        pts = [V(x, 0.0045, z0), V(x, 0.03, z0 + (z1 - z0) * 0.04), V(x + (0.002 if x > 0 else -0.002), y1 * 0.5, (z0 + z1) / 2), V(x, y1, z1)]
        g.tube(OAK, pts, [r0, r0, (r0 + r1) / 2 * 1.05, r1], sides=12, col=lambda p, t: OAKC + (1,), vscale=1.6)
        disc(g, OAK, (x, 0.0045, z0), r0, rings=2, seg=12, col=OAKD); a_ = g.parts[OAK]; a_['N'][-1] = -a_['N'][-1]; a_['T'][-1] = a_['T'][-1][:, [0, 2, 1]]
        g.lathe(OAK, (x, 0, z0), [(0.0, 0.0), (r0 * 0.95, 0.0), (r0 * 1.05, 0.002), (r0, 0.005), (0, 0.005)], sides=12, col=OAKD + (1,))   # sapata
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
    add_xf(g, tmp, rot_x(-lean), top)
    for hh in (0.30, 0.44):
        tmp = Geo(); rbox(tmp, OAK, (0, 0, 0), (0.58, 0.035, 0.016), r=0.006, col=OAKD, uv=2.0)
        add_xf(g, tmp, rot_x(-lean), V(0, 0.22 + hh * math.cos(lean), -0.245 - hh * math.sin(lean) - 0.004))
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
    add_xf(gb, tmp, rot_x(-lean), V(0, 0.345, -0.108))
    # ---- colisores, superfícies e ponto de sentar
    M.empty('COL_base', (0, 0.18, -0.005), extras=dict(shape='box', size=[0.72, 0.36, 0.57], bloqueia=True, camada='movel'))
    for sx in (-1, 1):
        M.empty('COL_braco_' + ('D' if sx > 0 else 'E'), (sx * X, 0.43, 0.005), extras=dict(shape='box', size=[0.085, 0.14, 0.60], bloqueia=True, camada='movel'))
        M.empty('SURF_braco_' + ('D' if sx > 0 else 'E'), (sx * X, 0.506, 0.005), extras=dict(shape='box', size=[0.07, 0, 0.56], recebe='copo, livro, controle'))
    M.empty('COL_encosto', (0, 0.56, -0.235), extras=dict(shape='box', size=[0.64, 0.42, 0.16], bloqueia=True, camada='movel'))
    M.empty('IP_sentar', (0, 0, SIT_Z), extras=dict(acao='sentar', aproximacao=[0, 0, SIT_Z + 0.42], inicio=[0, 0, SIT_Z + 0.12],
            assento_y=SEAT_TOP - 0.013, olhar='+Z', alvo=[0, (0.1 + SEAT_TOP + 0.03) / 2, 0.06, 0.585, SEAT_TOP - 0.07, 0.385],
            sequencia=['andar até a aproximação', 'virar de costas', 'sentar (1,3 s)', 'sentado (laço)', 'levantar (1,0 s)'],
            cancelar='mexer o analógico ou tocar em Levantar: levanta e volta à aproximação; durante a ida, só para'))
    M.bake_ao(maxd=0.22, strength=0.55)
    return finish(M)


# ================================================================================================ 5. APARADOR (interativo: portas e gavetas)
def aparador():
    import conteudo as CT
    from pm_lib import C4, CHROME, place, EMB
    W, D, H, LEG = 1.10, 0.40, 0.66, 0.15
    M = G.Model('int_aparador', meta('int_aparador', 'Aparador de carvalho', 'sala', 'armazenamento', 'interativo',
               dict(tipo='estatico', massa=38.0, motivo='móvel grande ancorado; só portas e gavetas se mexem (dobradiça e trilho com limite)'),
               estados=['fechado', 'abrindo', 'aberto', 'fechando'], grade=[2, 1],
               conteudo_interno=['pilha de pratos com friso', 'tigelas empilhadas', 'xícaras com pires', 'toalhas de mesa dobradas',
                                 'organizador com garfos, facas e colheres', 'guardanapos dobrados', 'castiçais com velas (no tampo)'],
               interacoes=[dict(acao='abrir/fechar', alvo='peça na mira', pecas=['gaveta_E', 'gaveta_D', 'porta_E', 'porta_D'])]))
    body = M.node('corpo'); g = body.geo
    y0 = LEG; t = 0.02; zF = D / 2; xin = W / 2 - t; EMB_ = 0.0005
    # pés palito inclinados com ponteira de latão, entrando na base
    for sx in (-1, 1):
        for sz in (-1, 1):
            x = sx * (W / 2 - 0.07); z = sz * (D / 2 - 0.07)
            g.tube(OAK, [V(x + sx * 0.025, 0.012, z + sz * 0.02), V(x, y0 + 0.01, z)], [0.013, 0.02], sides=12, col=lambda p, tt: OAKD + (1,), vscale=2)
            g.lathe(MET, (x + sx * 0.025, 0, z + sz * 0.02), [(0, 0), (0.013, 0), (0.0135, 0.018), (0.012, 0.02), (0, 0.02)], sides=12, col=BRASS + (1,))
    # carcaça: tampo sobre as laterais, base e trave entre elas, fundo encaixado, divisórias
    rbox(g, OAK, (0, H - 0.0125, 0), (W, 0.025, D), r=0.008, col=OAKC, uv=1.6, step=0.3)
    for sx in (-1, 1):
        rbox(g, OAK, (sx * (W / 2 - t / 2), (y0 + H - 0.025) / 2, 0), (t, H - 0.025 - y0 + 0.001, D), r=0.003, col=OAKC, uv=1.6, step=0.3)
    rbox(g, OAK, (0, y0 + t / 2, -0.002), (2 * xin + 0.001, t, D - 0.004), r=0.003, col=OAKC, uv=1.6, step=0.4)
    rbox(g, OAK, (0, (y0 + t + H - 0.025) / 2, -D / 2 + 0.005), (2 * xin + 0.001, H - 0.025 - y0 - t + 0.001, 0.008), r=0.002, col=OAKD, uv=1.6, step=0.4)
    ydr = 0.49; tt_ = 0.018
    rbox(g, OAK, (0, ydr + tt_ / 2, -0.002), (2 * xin + 0.001, tt_, D - 0.004), r=0.003, col=OAKC, uv=1.6, step=0.4)
    rbox(g, OAK, (0, (y0 + t + ydr) / 2, -0.01), (0.018, ydr - y0 - t + 0.001, D - 0.02), r=0.003, col=OAKC, uv=1.6)
    rbox(g, OAK, (0, (ydr + tt_ + H - 0.025) / 2, -0.01), (0.018, H - 0.025 - ydr - tt_ + 0.001, D - 0.02), r=0.003, col=OAKC, uv=1.6)
    xd = 0.009                                   # face da divisória
    ysh = 0.34; tsh = 0.016
    for sx in (-1, 1):
        rbox(g, OAK, (sx * (xd + xin) / 2, ysh, -0.012), (xin - xd + 0.001, tsh, D - 0.04), r=0.003, col=OAKC, uv=1.6)
        for xx in (sx * (xd + 0.004), sx * (xin - 0.004)):
            for zz in (-0.12, 0.12):
                g.lathe(MET, (xx, ysh - tsh / 2 - 0.005, zz), [(0, 0), (0.003, 0), (0.003, 0.0055), (0, 0.0055)], sides=8, col=C4(CHROME))
    # castiçais com velas no tampo
    for xx in (-0.38, 0.40):
        cg, ci = CT.castical_vela(); place(g, cg, xx, H - EMB_, 0.0)
    # ---- conteúdo atrás das portas (só desenhado com a porta aberta)
    cE = M.node('conteudo_E', extras=dict(mostrar_quando=['porta_E'])); cD = M.node('conteudo_D', extras=dict(mostrar_quando=['porta_D']))
    gE = cE.geo; gD = cD.geo
    yb = y0 + t; ys = ysh + tsh / 2
    xl = -(xd + xin) / 2; xr = (xd + xin) / 2
    CT.pilha(gE, [CT.prato(borda=(0.25, 0.40, 0.60)) for _ in range(6)], xl - 0.12, yb, -0.02)
    CT.pilha(gE, [CT.prato(r=0.085, borda=(0.25, 0.40, 0.60)) for _ in range(5)], xl + 0.12, yb, -0.04)
    tg, ti = CT.tigela()
    place(gE, tg, xl - 0.12, ys - EMB_, -0.03)
    place(gE, CT.tigela(r=0.062, cor=(0.86, 0.58, 0.42))[0], xl - 0.12, ys + 0.0125 - EMB_, -0.03)
    place(gE, CT.tigela(r=0.055, h=0.04, cor=(0.55, 0.65, 0.58))[0], xl + 0.12, ys - EMB_, -0.06)
    CT.pilha(gD, [CT.toalha_dobrada((0.95, 0.93, 0.86), w=0.30, d=0.22, h=0.05), CT.toalha_dobrada((0.80, 0.28, 0.25), w=0.30, d=0.22, h=0.05)], xr, yb, -0.03)
    for k, (xx, zz) in enumerate(((xr - 0.15, -0.08), (xr - 0.04, -0.09), (xr + 0.07, -0.08), (xr + 0.17, -0.07))):
        xg, xi = CT.xicara(cor=[(0.95, 0.95, 0.93), (0.30, 0.45, 0.62), (0.95, 0.95, 0.93), (0.30, 0.45, 0.62)][k])
        place(gD, xg, xx, ys - EMB_, zz, yaw=0.6 * k)
    # ---- gavetas: corrediça nas laterais/divisória, caixa encostada nela, frente embutida (curso 0,26 m)
    fy0 = ydr + tt_ + 0.0015; fy1 = H - 0.025 - 0.0015; fh = fy1 - fy0; fyc = (fy0 + fy1) / 2
    dz0 = zF - 0.018; rth = 0.012; bh = 0.09; by0 = ydr + tt_ + 0.004; bd = 0.30
    for sx, nm in ((-1, 'gaveta_E'), (1, 'gaveta_D')):
        xa = xd; xb = xin
        rail_y = by0 + bh * 0.5
        for xx in (sx * (xa + rth / 2), sx * (xb - rth / 2)):
            rbox(g, MET, (xx, rail_y, dz0 - bd / 2), (rth + 0.001, 0.012, bd), r=0.001, col=(0.70, 0.72, 0.74), uv=1)
        bw = xb - xa - 2 * rth; bcx = sx * (xa + rth + bw / 2)
        fw = xb - xa - 0.003; fcx = sx * (xa + 0.0015 + fw / 2)
        dn = M.node(nm, (fcx, fyc, dz0), extras=dict(anim=dict(tipo='trilho', eixo=[0, 0, 1], min=0.0, max=0.26, dur=0.42, curva='suave',
                    estado_inicial=0.0, alca=[fcx, fyc, zF + 0.04], rotulo='gaveta', colide_com=['parede', 'movel'])))
        gd = dn.geo
        rbox(gd, OAK, (fcx, fyc, dz0 + 0.009), (fw, fh, 0.018), r=0.004, col=OAKC, uv=1.6, step=0.2)
        bz0 = dz0 - bd; bz1 = dz0 + 0.0005
        for s2 in (-1, 1):
            rbox(gd, OAK, (bcx + s2 * (bw / 2 - 0.006), by0 + bh / 2, (bz0 + bz1) / 2), (0.012, bh, bz1 - bz0), r=0.002, col=OAKD, uv=1.6)
        rbox(gd, OAK, (bcx, by0 + 0.003, (bz0 + bz1) / 2), (bw - 0.023, 0.006, bz1 - bz0 - 0.001), r=0.001, col=OAKD, uv=1.6)
        rbox(gd, OAK, (bcx, by0 + bh / 2, bz0 + 0.006), (bw - 0.023, bh, 0.012), r=0.002, col=OAKD, uv=1.6)
        gd.tube(MET, [V(fcx, fyc, zF - 0.0005), V(fcx, fyc, zF + 0.014)], [0.005, 0.005], sides=10, col=lambda p, tt: BRASS + (1,))
        sphere(gd, MET, (fcx, fyc, zF + 0.02), 0.012, BRASS, seg=10, sy=0.8)
        cn = M.node('conteudo_' + nm, (fcx, fyc, dz0), parent=dn, extras=dict(mostrar_quando=[nm]))
        gc = cn.geo; fl = by0 + 0.006
        if sx < 0:
            og, oi = CT.organizador_talheres(); place(gc, og, bcx, fl - EMB_, (bz0 + bz1) / 2)
        else:
            for k in range(2):
                CT.pilha(gc, [CT.cueca_dobrada((0.95, 0.94, 0.88) if k == 0 else (0.85, 0.75, 0.55), w=0.16, d=0.16, h=0.012) for _ in range(3)],
                         bcx - 0.1 + k * 0.2, fl, (bz0 + bz1) / 2)
    # ---- portas embutidas (dobradiça de pino na lateral, abrem para fora até 100°)
    py0 = y0 + t + 0.0015; py1 = ydr - 0.0015; ph = py1 - py0; py = (py0 + py1) / 2
    for sx, nm in ((-1, 'porta_E'), (1, 'porta_D')):
        ax_x = sx * (xin - 0.0015); ax_z = dz0 + 0.009
        pw = xin - 0.0015 - (xd + 0.0015); cx = sx * (xd + 0.0015 + pw / 2)
        ang = math.radians(100) * (-1 if sx < 0 else 1)
        dn = M.node(nm, (ax_x, py, ax_z), extras=dict(anim=dict(tipo='dobradica', eixo=[0, 1, 0], min=0.0, max=round(ang, 4), dur=0.55, curva='suave',
                    estado_inicial=0.0, alca=[cx - sx * (pw / 2 - 0.05), py + 0.08, zF + 0.04], rotulo='porta', raio=round(pw, 3), colide_com=['parede', 'movel'])))
        gd = dn.geo
        rbox(gd, OAK, (cx, py, dz0 + 0.009), (pw, ph, 0.018), r=0.004, col=OAKC, uv=1.6, step=0.2)
        rbox(gd, OAK, (cx, py, zF + 0.0025), (pw - 0.07, ph - 0.07, 0.006), r=0.003, col=tuple(np.array(OAKC) * 0.96), uv=1.6, step=0.2)
        for hy in (py - ph / 2 + 0.05, py + ph / 2 - 0.05):
            g.tube(MET, [V(ax_x, hy - 0.02, ax_z), V(ax_x, hy + 0.02, ax_z)], [0.005, 0.005], sides=8, col=lambda p, tt: BRASS + (1,))
            for e in (-1, 1): sphere(g, MET, (ax_x, hy + e * 0.02, ax_z), 0.005, BRASS, seg=5, sy=0.5)
        kx = cx - sx * (pw / 2 - 0.05)
        gd.tube(MET, [V(kx, py + 0.08, zF + 0.005), V(kx, py + 0.08, zF + 0.018)], [0.005, 0.005], sides=10, col=lambda p, tt: BRASS + (1,))
        sphere(gd, MET, (kx, py + 0.08, zF + 0.024), 0.012, BRASS, seg=10, sy=0.8)
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
