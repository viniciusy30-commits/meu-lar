"""ETAPA 1 do Plano Mestre v3 (protótipo): cadeira de jantar, mesa de jantar e armário com porta e gaveta (guarda-roupa).
Cada peça segue a ficha do PDF:
  Mesa de jantar  — tampo com espessura e bordas, pernas e reforços, área livre para joelhos, compatível com 4 cadeiras;
                    estática; superfície para pratos/copos; pontos de sentar ficam nas CADEIRAS (não no tampo);
                    a cadeira pode ser puxada sem atravessar a mesa (o tampo não bloqueia o encaixe, só as pernas).
  Cadeira de jantar — assento com espessura, encosto, pernas e travessas (nada fino demais); assento na altura da mesa e
                    espaço para joelhos; estática no uso normal (arrastável no modo de edição); ponto de sentar central
                    voltado para a frente (para a mesa); "puxar a cadeira" como deslize suave (trilho) antes de sentar.
  Guarda-roupa    — caixa com laterais, topo, base, fundo, portas com espessura, dobradiças, puxadores, prateleiras e
                    cabideiro; interior modelado; corpo ancorado; portas com dobradiça e limite; gavetas com trilho;
                    ponto de interação frontal; teste de parede antes de abrir; personagem não fica preso.
Uso: python3 models_e1.py <pasta de saída>
"""
import sys, os, math, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import *          # noqa
import glb_lib as G
from models import OAK, LIN, GLZ, MET, PLN, BRASS, meta, finish

WAL = (0.78, 0.56, 0.38); WALD = (0.62, 0.43, 0.29)
SEAT_SIT = 0.335 + 0.013          # traseiro do adulto sentado (sit.txt) + afundamento


# ================================================================================================ MESA DE JANTAR
def mesa():
    L, Wd, T, Y = 1.20, 0.74, 0.035, 0.60
    M = G.Model('int_mesa_jantar', meta('int_mesa_jantar', 'Mesa de jantar', 'cozinha', 'mesas', 'apoio',
               dict(tipo='estatico', massa=32.0, motivo='móvel de apoio ancorado; só serve de superfície'),
               estados=[], grade=[2, 1], capacidade=4,
               vagas_cadeiras=[dict(x=-0.28, z=0.48, olhar='-Z'), dict(x=0.28, z=0.48, olhar='-Z'), dict(x=-0.28, z=-0.48, olhar='+Z'), dict(x=0.28, z=-0.48, olhar='+Z')], nota_vagas='cadeira encaixada: 10 cm do assento sob o tampo',
               interacoes=[dict(acao='nenhuma', nota='pontos de sentar ficam nas cadeiras')]))
    n = M.node('mesa'); g = n.geo
    # tampo com borda arredondada e chanfro embaixo (duas camadas)
    rbox(g, OAK, (0, Y - T / 2, 0), (L, T, Wd), r=0.012, col=WAL, uv=1.4, step=0.25)
    rbox(g, OAK, (0, Y - T - 0.004, 0), (L - 0.03, 0.008, Wd - 0.03), r=0.003, col=WALD, uv=1.4, step=0.4)
    # saia (aventais) recuada 5 cm, 6 cm de altura: joelhos livres abaixo de 0,505 m
    ay = Y - T - 0.008 - 0.03; inset = 0.06
    for sz in (-1, 1):
        rbox(g, OAK, (0, ay, sz * (Wd / 2 - inset)), (L - 2 * inset - 0.02, 0.06, 0.022), r=0.004, col=WALD, uv=1.4, step=0.4)
    for sx in (-1, 1):
        rbox(g, OAK, (sx * (L / 2 - inset), ay, 0), (0.022, 0.06, Wd - 2 * inset - 0.02), r=0.004, col=WALD, uv=1.4, step=0.4)
    # pernas: seção quadrada afunilando (5 -> 3,6 cm) com cantos arredondados, e reforços (cantoneiras) nos cantos
    for sx in (-1, 1):
        for sz in (-1, 1):
            x = sx * (L / 2 - inset); z = sz * (Wd / 2 - inset)
            nseg = 6; P = []; N = []; UV = []; C = []
            for s in range(nseg + 1):
                t = s / nseg; y = t * (Y - T - 0.008); h = 0.018 + 0.007 * t
                ring = []
                for k in range(16):
                    a = 2 * math.pi * k / 16
                    # quadrado arredondado (superelipse)
                    cx_, sz_ = math.cos(a), math.sin(a)
                    ex = math.copysign(abs(cx_) ** 0.35, cx_); ez = math.copysign(abs(sz_) ** 0.35, sz_)
                    P.append((x + ex * h, y, z + ez * h)); N.append((cx_, 0, sz_)); UV.append((k / 16 * 0.6, y * 2)); C.append(WAL + (1,))
            T_ = []
            for s in range(nseg):
                for k in range(16):
                    a_ = s * 16 + k; b_ = s * 16 + (k + 1) % 16
                    T_ += [(a_, b_, a_ + 16), (b_, b_ + 16, a_ + 16)]
            g.add(OAK, P, N, C, UV, T_)
            g.lathe(OAK, (x, 0, z), [(0, 0), (0.017, 0), (0.019, 0.004), (0, 0.004)], sides=16, col=WALD + (1,))      # sapata
            # cantoneira (bloco de reforço) entre a perna e o avental
            rbox(g, OAK, (x - sx * 0.045, ay, z - sz * 0.045), (0.07, 0.05, 0.022), r=0.003, col=WALD, uv=1.4, rot=math.radians(45 * sx * sz))
    # colisores: tampo (não bloqueia o encaixe da cadeira) + 4 pernas (bloqueiam)
    M.empty('COL_tampo', (0, Y - (T + 0.07) / 2, 0), extras=dict(shape='box', size=[L, T + 0.07, Wd], bloqueia=False, camada='superficie',
            nota='cadeiras entram embaixo; objetos soltos apoiam'))
    for sx in (-1, 1):
        for sz in (-1, 1):
            M.empty('COL_perna_%s%s' % ('D' if sx > 0 else 'E', 'F' if sz > 0 else 'T'), (sx * (L / 2 - inset), (Y - T) / 2, sz * (Wd / 2 - inset)),
                    extras=dict(shape='box', size=[0.06, Y - T, 0.06], bloqueia=True, camada='movel'))
    M.empty('SURF_tampo', (0, Y, 0), extras=dict(shape='box', size=[L - 0.02, 0, Wd - 0.02], recebe='pratos, copos, objetos'))
    M.bake_ao(maxd=0.25, strength=0.5)
    return finish(M)


# ================================================================================================ CADEIRA DE JANTAR
def cadeira():
    SW, SD = 0.42, 0.40
    zf, zb = 0.21, -0.17                     # frente e trás do assento
    sit_z = zf - 0.05                        # raiz sentada (pés ficam sob a borda do assento)
    PULL = 0.35
    M = G.Model('int_cadeira_jantar', meta('int_cadeira_jantar', 'Cadeira de jantar', 'cozinha', 'cadeiras', 'interativo',
               dict(tipo='estatico', massa=5.5, motivo='estática no uso; arrastável só no modo de edição'),
               estados=['livre', 'puxada', 'ocupada'], grade=[1, 1],
               interacoes=[dict(acao='sentar', ponto='IP_sentar', puxar='cadeira', cancelavel=True)]))
    ch = M.node('cadeira', (0, 0, 0), extras=dict(anim=dict(tipo='trilho', eixo=[0, 0, -1], min=0.0, max=PULL, dur=0.55, curva='suave',
                gatilho='puxar', estado_inicial=0.0, empurrada=0.36, nota='empurrada = progresso (0..1) em que a cadeira fica com a pessoa sentada: 10 cm para fora do encaixe, joelhos sob o tampo')))
    g = ch.geo
    Y = 0.335
    # assento: tábua de 3 cm com borda arredondada + almofada fina estofada
    rbox(g, OAK, (0, Y - 0.015, (zf + zb) / 2), (SW, 0.03, SD - 0.02), r=0.01, col=WAL, uv=1.6, step=0.2)
    rbox(g, LIN, (0, Y + 0.012, (zf + zb) / 2 + 0.005), (SW - 0.04, 0.026, SD - 0.06), r=0.012, col=(0.86, 0.80, 0.70), uv=3.2, puff=0.008, step=0.06)
    # pernas dianteiras retas afuniladas (seção 3,4 -> 2,8 cm)
    for sx in (-1, 1):
        x = sx * (SW / 2 - 0.03)
        g.tube(OAK, [V(x, 0, zf - 0.03), V(x, Y - 0.03, zf - 0.035)], [0.014, 0.017], sides=10, col=lambda p, t: WAL + (1,))
        # perna traseira sobe e vira o montante do encosto, inclinada para trás
        pts = [V(x, 0, zb - 0.02), V(x, Y - 0.03, zb + 0.015), V(x, Y + 0.18, zb - 0.005), V(x, Y + 0.44, zb - 0.06)]
        g.tube(OAK, pts, [0.015, 0.017, 0.016, 0.014], sides=10, col=lambda p, t: WAL + (1,))
        # travessa lateral baixa
        g.tube(OAK, [V(x, 0.12, zf - 0.03), V(x, 0.12, zb)], [0.009, 0.009], sides=8, col=lambda p, t: WALD + (1,))
    # travessa central (H) e travessas sob o assento
    g.tube(OAK, [V(-(SW / 2 - 0.03), 0.13, (zf + zb) / 2), V((SW / 2 - 0.03), 0.13, (zf + zb) / 2)], [0.009, 0.009], sides=8, col=lambda p, t: WALD + (1,))
    for zz in (zf - 0.035, zb + 0.012):
        rbox(g, OAK, (0, Y - 0.05, zz), (SW - 0.07, 0.035, 0.018), r=0.003, col=WALD, uv=1.6)
    # encosto: travessa de cima curva + duas ripas curvas
    for hh, th, nm in ((Y + 0.40, 0.06, 'top'), (Y + 0.27, 0.04, 'mid'), (Y + 0.16, 0.03, 'low')):
        zc = zb - 0.06 * ((hh - (Y - 0.03)) / 0.47) - 0.005
        pts = []; nseg = 10
        for k in range(nseg + 1):
            s = k / nseg - 0.5
            pts.append(V(s * (SW - 0.06), hh, zc + 0.03 - 0.06 * (s * 2) ** 2 * 0.5))
        # perfil retangular extrudado ao longo da curva (tábua curva)
        P = []; N = []; UV = []; C = []; T_ = []
        for k, p in enumerate(pts):
            for (dy, dz, nn) in ((th / 2, 0.009, (0, 0.3, 1)), (th / 2, -0.009, (0, 0.3, -1)), (-th / 2, -0.009, (0, -0.3, -1)), (-th / 2, 0.009, (0, -0.3, 1))):
                P.append(p + V(0, dy, dz)); N.append(nn); UV.append((k / nseg, dy * 4)); C.append(WAL + (1,))
        for k in range(nseg):
            for f in range(4):
                a_ = k * 4 + f; b_ = k * 4 + (f + 1) % 4
                T_ += [(a_, b_, a_ + 4), (b_, b_ + 4, a_ + 4)]
        T_ += [(0, 2, 1), (0, 3, 2)]; e0 = nseg * 4; T_ += [(e0, e0 + 1, e0 + 2), (e0, e0 + 2, e0 + 3)]
        g.add(OAK, P, N, C, UV, T_)
    # colisores (no nó que desliza: acompanham a cadeira puxada)
    M.empty('COL_assento', (0, Y / 2 + 0.01, (zf + zb) / 2), parent=ch, extras=dict(shape='box', size=[SW, Y + 0.03, SD], bloqueia=True, camada='movel'))
    M.empty('COL_encosto', (0, Y + 0.24, zb - 0.03), parent=ch, extras=dict(shape='box', size=[SW - 0.02, 0.46, 0.07], bloqueia=True, camada='movel'))
    # sentar: raiz final perto da frente do assento; início 12 cm à frente; chegada pela lateral esquerda (a frente costuma estar na mesa)
    M.empty('IP_sentar', (0, 0, sit_z), extras=dict(acao='sentar', inicio=[0, 0, sit_z + 0.12], aproximacao=[-0.62, 0, sit_z + 0.12],
            assento_y=Y + 0.026 - 0.013, olhar='+Z', puxar='cadeira',
            sequencia=['puxar a cadeira (0,55 s)', 'andar até a lateral', 'entrar entre a cadeira e a mesa', 'virar de costas', 'sentar',
                       'empurrar para a mesa junto com o personagem', 'sentado', 'afastar', 'levantar', 'empurrar a cadeira de volta']))
    M.bake_ao(maxd=0.18, strength=0.5)
    return finish(M)


# ================================================================================================ GUARDA-ROUPA (armário com porta e gaveta)
def guarda_roupa():
    W, D, H = 1.10, 0.50, 1.62
    t = 0.022; zf = D / 2 - 0.02
    M = G.Model('int_guarda_roupa', meta('int_guarda_roupa', 'Guarda-roupa', 'quarto', 'armazenamento', 'funcional',
               dict(tipo='estatico', massa=85.0, motivo='móvel alto ancorado: não tomba nem desliza'),
               estados=['fechado', 'abrindo', 'aberto', 'fechando'], grade=[2, 1],
               interacoes=[dict(acao='abrir/fechar', pecas=['porta_E', 'porta_D', 'gaveta_E', 'gaveta_D'])]))
    body = M.node('corpo'); g = body.geo
    CW = (0.94, 0.92, 0.88)         # laca off-white; interior em carvalho
    y0 = 0.07                       # rodapé
    # caixa: laterais, topo, base, fundo, rodapé recuado, divisória e moldura do topo
    for sx in (-1, 1): rbox(g, PLN, (sx * (W / 2 - t / 2), (y0 + H) / 2, 0), (t, H - y0, D - 0.01), r=0.004, col=CW, uv=1, step=0.4)
    rbox(g, PLN, (0, H - t / 2, 0), (W, t, D - 0.01), r=0.004, col=CW, uv=1, step=0.4)
    rbox(g, PLN, (0, y0 + t / 2, 0), (W - 2 * t, t, D - 0.02), r=0.003, col=CW, uv=1, step=0.4)
    rbox(g, OAK, (0, (y0 + H) / 2, -D / 2 + 0.01), (W - 2 * t, H - y0 - t, 0.012), r=0.002, col=OAKC_, uv=1.4, step=0.4) if False else None
    rbox(g, OAK, (0, (y0 + H) / 2, -D / 2 + 0.012), (W - 2 * t, H - y0 - t, 0.012), r=0.002, col=(0.88, 0.72, 0.52), uv=1.4, step=0.4)
    rbox(g, PLN, (0, y0 / 2, zf - 0.04), (W - 0.06, y0, 0.018), r=0.003, col=(0.35, 0.34, 0.33), uv=1)
    rbox(g, PLN, (0, H + 0.012, 0.005), (W + 0.03, 0.024, D + 0.015), r=0.006, col=CW, uv=1, step=0.4)       # moldura (coroa)
    ydr = 0.30                      # trave entre gavetas e portas
    rbox(g, PLN, (0, ydr, 0), (W - 2 * t, t, D - 0.02), r=0.003, col=CW, uv=1, step=0.4)
    rbox(g, OAK, (0, (ydr + H) / 2, -0.01), (0.02, H - ydr - t, D - 0.05), r=0.003, col=(0.88, 0.72, 0.52), uv=1.4, step=0.4)   # divisória
    rbox(g, PLN, (0, (y0 + ydr) / 2 + 0.01, -0.01), (0.02, ydr - y0 - t, D - 0.05), r=0.003, col=CW, uv=1)
    # lado esquerdo: 4 prateleiras com roupas dobradas
    xl0, xl1 = -W / 2 + t, -0.01
    rng = np.random.default_rng(5)
    cols = [(0.25, 0.35, 0.55), (0.85, 0.85, 0.82), (0.55, 0.20, 0.22), (0.30, 0.45, 0.30), (0.15, 0.15, 0.17), (0.80, 0.70, 0.50)]
    for k, yy in enumerate((0.62, 0.92, 1.22, 1.48)):
        rbox(g, OAK, ((xl0 + xl1) / 2, yy, -0.01), (xl1 - xl0, 0.018, D - 0.06), r=0.003, col=(0.88, 0.72, 0.52), uv=1.4)
        if yy < 1.4:
            x = xl0 + 0.03
            for pile in range(2):
                hcur = yy + 0.009
                for f in range(rng.integers(3, 6)):
                    th = rng.uniform(0.025, 0.04)
                    rbox(g, LIN, (x + 0.11, hcur + th / 2, -0.02), (0.21 + rng.uniform(-0.01, 0.01), th, 0.28), r=0.01, col=cols[rng.integers(len(cols))], uv=3, puff=0.004, step=0.1)
                    hcur += th
                x += 0.25
    # caixa organizadora embaixo à esquerda
    rbox(g, PLN, (-0.26, ydr + 0.11, -0.03), (0.4, 0.18, 0.32), r=0.012, col=(0.80, 0.84, 0.88), uv=1)
    # lado direito: cabideiro (tubo com suportes) + cabides com camisas
    rx0, rx1 = 0.01, W / 2 - t; ry = 1.42
    g.tube(MET, [V(rx0 + 0.01, ry, -0.01), V(rx1 - 0.01, ry, -0.01)], [0.011, 0.011], sides=12, col=lambda p, tt: (0.80, 0.82, 0.85, 1))
    for xx in (rx0 + 0.01, rx1 - 0.01): g.lathe(MET, (xx, ry, -0.01), [(0, -0.02), (0.025, -0.02), (0.025, 0.02), (0, 0.02)], sides=12, col=(0.75, 0.77, 0.8, 1)) if False else rbox(g, MET, (xx, ry, -0.01), (0.01, 0.05, 0.05), r=0.003, col=(0.75, 0.77, 0.8), uv=1)
    shirts = [(0.85, 0.85, 0.88), (0.30, 0.40, 0.60), (0.75, 0.30, 0.28), (0.20, 0.20, 0.22), (0.60, 0.70, 0.55), (0.90, 0.80, 0.55)]
    for i, xx in enumerate(np.linspace(rx0 + 0.07, rx1 - 0.07, 6)):
        hx = xx
        # cabide: gancho + barra triangular
        g.tube(MET, [V(hx, ry + 0.005, -0.01), V(hx, ry + 0.03, -0.01), V(hx, ry + 0.02, 0.01), V(hx, ry - 0.03, 0.0)], [0.002] * 4, sides=5, col=lambda p, tt: (0.75, 0.77, 0.8, 1))
        g.tube(OAK, [V(hx, ry - 0.03, -0.20), V(hx, ry - 0.07, -0.01), V(hx, ry - 0.03, 0.18)], [0.006] * 3, sides=6, col=lambda p, tt: (0.85, 0.68, 0.45, 1))
        # camisa: painel com ombros e mangas caindo (espessura), virada de lado no cabide
        c = shirts[i]
        sh = Geo()
        rbox(sh, LIN, (0, -0.30, 0), (0.018, 0.56, 0.36), r=0.008, col=c, uv=3, puff=0.006, step=0.08)
        for sz in (-1, 1):
            sl = Geo(); rbox(sl, LIN, (0, -0.16, 0), (0.016, 0.30, 0.09), r=0.007, col=tuple(np.array(c) * 0.95), uv=3, step=0.1)
            add_xf(sh, sl, rot_x(sz * math.radians(16)), V(0.003, -0.03, sz * 0.17))
        add_xf(g, sh, rot_y(rng.uniform(-0.08, 0.08)), V(hx, ry - 0.045, -0.01))
    # sapatos no fundo do lado direito
    for i, xx in enumerate((0.13, 0.31)):
        for s2 in (-1, 1):
            rbox(g, PLN, (xx + s2 * 0.045, ydr + 0.035, 0.02), (0.07, 0.05, 0.22), r=0.022, col=[(0.15, 0.12, 0.1), (0.85, 0.85, 0.85)][i], uv=1, step=0.1)
    # ---- portas (dobradiças nas laterais, abrem 105° para fora)
    ph = H - ydr - 0.02 - 0.008; py = ydr + 0.012 + ph / 2
    for sx, nm in ((-1, 'porta_E'), (1, 'porta_D')):
        hx = sx * (W / 2 - 0.004); pw = W / 2 - 0.009; cx = sx * (0.0015 + pw / 2)
        ang = math.radians(105) * (-1 if sx < 0 else 1)
        dn = M.node(nm, (hx, py, zf), extras=dict(anim=dict(tipo='dobradica', eixo=[0, 1, 0], min=0.0, max=round(ang, 4), dur=0.65, curva='suave', estado_inicial=0.0,
                    alca=[cx - sx * (pw / 2 - 0.05), 1.0, zf + 0.05], rotulo='porta', raio=round(pw, 3), colide_com=['parede', 'movel'])))
        gd = dn.geo
        rbox(gd, PLN, (cx, py, zf + 0.011), (pw, ph, 0.022), r=0.004, col=CW, uv=1, step=0.25)
        # almofada em relevo (dois painéis) e frisos
        for yy, hh in ((py + ph * 0.2, ph * 0.52), (py - ph * 0.32, ph * 0.28)):
            rbox(gd, PLN, (cx, yy, zf + 0.0235), (pw - 0.09, hh, 0.005), r=0.003, col=tuple(np.array(CW) * 0.97), uv=1, step=0.25)
        # puxador vertical de latão
        kx = cx - sx * (pw / 2 - 0.05)
        gd.tube(MET, [V(kx, 0.86, zf + 0.05), V(kx, 1.14, zf + 0.05)], [0.007, 0.007], sides=10, col=lambda p, tt: BRASS + (1,))
        for yy in (0.88, 1.12): gd.tube(MET, [V(kx, yy, zf + 0.022), V(kx, yy, zf + 0.05)], [0.005, 0.005], sides=8, col=lambda p, tt: BRASS + (1,))
        # dobradiças (3), presas na lateral
        for yy in (py - ph / 2 + 0.08, py, py + ph / 2 - 0.08):
            g.tube(MET, [V(hx, yy - 0.025, zf + 0.004), V(hx, yy + 0.025, zf + 0.004)], [0.0045, 0.0045], sides=8, col=lambda p, tt: BRASS + (1,))
    # ---- gavetas (trilho, curso 30 cm, caixa interna completa)
    dh = ydr - y0 - 0.012 - 0.006; dy = y0 + 0.003 + dh / 2 + 0.006
    for sx, nm in ((-1, 'gaveta_E'), (1, 'gaveta_D')):
        fw = W / 2 - 0.009; cx = sx * (0.0015 + fw / 2)
        dn = M.node(nm, (cx, dy, zf), extras=dict(anim=dict(tipo='trilho', eixo=[0, 0, 1], min=0.0, max=0.30, dur=0.45, curva='suave', estado_inicial=0.0,
                    alca=[cx, dy + 0.02, zf + 0.05], rotulo='gaveta', colide_com=['parede', 'movel'])))
        gd = dn.geo
        rbox(gd, PLN, (cx, dy, zf + 0.011), (fw, dh, 0.022), r=0.004, col=CW, uv=1, step=0.25)
        for s2 in (-1, 1): rbox(gd, OAK, (cx + s2 * (fw / 2 - 0.035), dy - 0.012, zf - 0.20), (0.012, dh - 0.05, 0.40), r=0.002, col=(0.86, 0.70, 0.50), uv=1.4)
        rbox(gd, OAK, (cx, dy - dh / 2 + 0.03, zf - 0.20), (fw - 0.07, 0.006, 0.40), r=0.001, col=(0.86, 0.70, 0.50), uv=1.4)
        rbox(gd, OAK, (cx, dy - 0.012, zf - 0.395), (fw - 0.07, dh - 0.05, 0.012), r=0.002, col=(0.86, 0.70, 0.50), uv=1.4)
        for k in range(5):     # meias/camisetas enroladas dentro
            sphere(gd, LIN, (cx - 0.16 + k * 0.08, dy - dh / 2 + 0.06, zf - 0.12 - (k % 2) * 0.12), 0.035, cols[k % len(cols)], seg=8, sy=0.7)
        gd.tube(MET, [V(cx - 0.08, dy + 0.02, zf + 0.05), V(cx + 0.08, dy + 0.02, zf + 0.05)], [0.007, 0.007], sides=10, col=lambda p, tt: BRASS + (1,))
        for xx in (cx - 0.08, cx + 0.08): gd.tube(MET, [V(xx, dy + 0.02, zf + 0.022), V(xx, dy + 0.02, zf + 0.05)], [0.005, 0.005], sides=8, col=lambda p, tt: BRASS + (1,))
    M.empty('COL_corpo', (0, (H + 0.024) / 2, 0), extras=dict(shape='box', size=[W + 0.03, H + 0.024, D], bloqueia=True, camada='movel'))
    M.empty('SURF_topo', (0, H + 0.024, 0), extras=dict(shape='box', size=[W, 0, D], recebe='caixas, objetos'))
    M.empty('IP_usar', (0, 0, D / 2 + 0.45), extras=dict(acao='abrir/fechar', olhar='-Z', nota='a peça usada é a mais perto do olhar'))
    M.bake_ao(maxd=0.25, strength=0.55)
    return finish(M)


ALL = [cadeira, mesa, guarda_roupa]

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/glb_e1'
    os.makedirs(out, exist_ok=True)
    rep = {}
    for f in ALL:
        M = f(); fn = os.path.join(out, M.id + '.glb'); n = M.write_glb(fn)
        err, warn, info = G.verify(fn)
        rep[M.id] = dict(erros=err, avisos=warn, info=info)
        print('%-20s %7d bytes %6d vért. %6d tri. erros=%d avisos=%d %s' % (M.id, n, info['vertices'], info['triangulos'], len(err), len(warn), M.meta['dimensoes']))
        for e in err: print('   ERRO:', e)
        for w in warn: print('   aviso:', w)
    json.dump(rep, open(os.path.join(out, 'verificacao_etapa1.json'), 'w'), ensure_ascii=False, indent=1)
