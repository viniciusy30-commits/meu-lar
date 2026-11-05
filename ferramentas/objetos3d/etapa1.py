"""ETAPA 1 do Plano Mestre (v4): cadeira de jantar, mesa de jantar e armário com porta e gaveta (guarda-roupa).

Fichas (PDF v4):
  Mesa de jantar  — tampo com espessura e bordas, pernas e reforços, joelhos livres, 4 cadeiras; estática; superfície para
                    pratos/copos; pontos de sentar nas cadeiras; cadeira puxada sem atravessar a mesa.
                    (v4) pernas no piso e presas ao tampo/avental; tampo sobre pernas e avental; reforços encostados.
  Cadeira de jantar — assento com espessura, encosto, pernas e travessas; altura de mesa; estática; ponto de sentar central
                    virado para a mesa; puxar a cadeira suave. (v4) 4 pés no piso; assento nas pernas/travessas; encosto
                    preso às pernas traseiras; travessas encostadas.
  Guarda-roupa    — caixa (laterais, topo, base, fundo), portas com espessura, dobradiças, puxadores, prateleiras e cabideiro;
                    interior modelado; portas com dobradiça e limite; gavetas com trilho; ponto frontal; parede antes de abrir.
                    (v4) rodapé no piso; caixa na base; prateleiras nas laterais/divisória; cabideiro preso nos suportes;
                    cabides no cabideiro; roupas nos cabides; portas nas dobradiças; gavetas nos trilhos.
                    (v4) conteúdo: cabides com gancho e barra, camisas/vestido com gola, mangas e caimento, roupas dobradas
                    com camadas e dobras, sapatos com sola e cadarço, caixa com tampa, meias e roupa íntima nas gavetas.
Uso: python3 etapa1.py <pasta de saída>
"""
import sys, os, math, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pm_lib import *        # noqa
import conteudo as CT

WAL = (0.78, 0.56, 0.38); WALD = (0.62, 0.43, 0.29)


# ================================================================================================ MESA DE JANTAR
def mesa():
    L, Wd, T, Y = 1.20, 0.74, 0.035, 0.60
    M = G.Model('int_mesa_jantar', meta('int_mesa_jantar', 'Mesa de jantar', 'cozinha', 'mesas', 'apoio',
               dict(tipo='estatico', massa=32.0, motivo='móvel de apoio ancorado; só serve de superfície'),
               estados=[], grade=[2, 1], capacidade=4,
               vagas_cadeiras=[dict(x=-0.28, z=0.48, olhar='-Z'), dict(x=0.28, z=0.48, olhar='-Z'), dict(x=-0.28, z=-0.48, olhar='+Z'), dict(x=0.28, z=-0.48, olhar='+Z')],
               nota_vagas='cadeira encaixada: 10 cm do assento sob o tampo',
               interacoes=[dict(acao='nenhuma', nota='pontos de sentar ficam nas cadeiras')]))
    n = M.node('mesa'); g = n.geo
    # tampo (com borda arredondada) e sub-tampo chanfrado colado embaixo
    rbox(g, OAK, (0, Y - T / 2, 0), (L, T, Wd), r=0.012, col=WAL, uv=1.4, step=0.25)
    rbox(g, OAK, (0, Y - T - 0.004 + 0.0005, 0), (L - 0.03, 0.008 + 0.001, Wd - 0.03), r=0.003, col=WALD, uv=1.4, step=0.4)
    ytop_leg = Y - T - 0.008                        # face de baixo do sub-tampo: pernas e avental encostam aqui
    ay = ytop_leg - 0.03 + 0.0005; inset = 0.06
    for sz in (-1, 1):
        rbox(g, OAK, (0, ay, sz * (Wd / 2 - inset)), (L - 2 * inset, 0.06, 0.022), r=0.004, col=WALD, uv=1.4, step=0.4)
    for sx in (-1, 1):
        rbox(g, OAK, (sx * (L / 2 - inset), ay, 0), (0.022, 0.06, Wd - 2 * inset), r=0.004, col=WALD, uv=1.4, step=0.4)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x = sx * (L / 2 - inset); z = sz * (Wd / 2 - inset)
            # perna: seção quadrada arredondada afunilando 5 -> 3,6 cm, do piso (sobre a sapata) até o sub-tampo
            nseg = 6; P = []; N = []; UV = []; C = []
            for s in range(nseg + 1):
                t = s / nseg; y = 0.004 + t * (ytop_leg + 0.0005 - 0.004); h = 0.018 + 0.007 * t
                for k in range(16):
                    a = 2 * math.pi * k / 16; cx_, sz_ = math.cos(a), math.sin(a)
                    ex = math.copysign(abs(cx_) ** 0.35, cx_); ez = math.copysign(abs(sz_) ** 0.35, sz_)
                    P.append((x + ex * h, y, z + ez * h)); N.append((cx_, 0, sz_)); UV.append((k / 16 * 0.6, y * 2)); C.append(WAL + (1,))
            T_ = []
            for s in range(nseg):
                for k in range(16):
                    a_ = s * 16 + k; b_ = s * 16 + (k + 1) % 16
                    T_ += [(a_, b_, a_ + 16), (b_, b_ + 16, a_ + 16)]
            base = len(P); P.append((x, 0.004, z)); N.append((0, -1, 0)); UV.append((0, 0)); C.append(WAL + (1,))
            T_ += [(base, (k + 1) % 16, k) for k in range(16)]
            g.add(OAK, P, N, C, UV, T_)
            # sapata de feltro (proteção do piso): do piso até a perna
            g.lathe(LIN, (x, 0, z), [(0, 0), (0.019, 0), (0.0205, 0.002), (0.019, 0.0045), (0, 0.0045)], sides=16, col=(0.30, 0.27, 0.24, 1))
            # cantoneira em 45° encaixada nos dois aventais e encostada no sub-tampo
            xc = sx * (L / 2 - inset - 0.011); zc = sz * (Wd / 2 - inset - 0.011); a = 0.034
            rbox(g, OAK, (xc - sx * a, ytop_leg - 0.025 + 0.0005, zc - sz * a), (2 * a * math.sqrt(2) + 0.012, 0.05, 0.022), r=0.003, col=WALD, uv=1.4,
                 rot=math.atan2(sz, sx))
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
    zf, zb = 0.21, -0.17
    sit_z = zf - 0.05
    PULL = 0.35
    M = G.Model('int_cadeira_jantar', meta('int_cadeira_jantar', 'Cadeira de jantar', 'cozinha', 'cadeiras', 'interativo',
               dict(tipo='estatico', massa=5.5, motivo='estática no uso; arrastável só no modo de edição'),
               estados=['livre', 'puxada', 'ocupada'], grade=[1, 1],
               interacoes=[dict(acao='sentar', ponto='IP_sentar', puxar='cadeira', cancelavel=True)]))
    ch = M.node('cadeira', (0, 0, 0), extras=dict(anim=dict(tipo='trilho', eixo=[0, 0, -1], min=0.0, max=PULL, dur=0.55, curva='suave',
                gatilho='puxar', estado_inicial=0.0, empurrada=0.36, nota='empurrada = progresso (0..1) em que a cadeira fica com a pessoa sentada')))
    g = ch.geo
    Y = 0.335; PAD = 0.005
    rbox(g, OAK, (0, Y - 0.015, (zf + zb) / 2), (SW, 0.03, SD - 0.02), r=0.01, col=WAL, uv=1.6, step=0.2)
    rbox(g, LIN, (0, Y + 0.012, (zf + zb) / 2 + 0.005), (SW - 0.04, 0.026, SD - 0.06), r=0.012, col=(0.86, 0.80, 0.70), uv=3.2, puff=0.008, step=0.06)
    wl = lambda p, t: WAL + (1,)
    for sx in (-1, 1):
        x = sx * (SW / 2 - 0.03)
        # pernas começam na sapata (vertical no pé, depois a inclinação) e entram no assento
        g.tube(OAK, [V(x, PAD - 0.0005, zf - 0.03), V(x, 0.03, zf - 0.0305), V(x, Y - 0.025, zf - 0.035)], [0.014, 0.0145, 0.017], sides=10, col=wl)
        disc(g, OAK, (x, PAD - 0.0005, zf - 0.03), 0.014, rings=2, seg=10, col=WAL); a = g.parts[OAK]; a['N'][-1] = -a['N'][-1]; a['T'][-1] = a['T'][-1][:, [0, 2, 1]]
        pts = [V(x, PAD - 0.0005, zb - 0.02), V(x, 0.03, zb - 0.017), V(x, Y - 0.03, zb + 0.015), V(x, Y + 0.18, zb - 0.005), V(x, Y + 0.44, zb - 0.06)]
        g.tube(OAK, pts, [0.015, 0.0152, 0.017, 0.016, 0.014], sides=10, col=wl)
        disc(g, OAK, (x, PAD - 0.0005, zb - 0.02), 0.015, rings=2, seg=10, col=WAL); a = g.parts[OAK]; a['N'][-1] = -a['N'][-1]; a['T'][-1] = a['T'][-1][:, [0, 2, 1]]
        sphere(g, OAK, (x, Y + 0.44, zb - 0.06), 0.014, WAL, seg=8)              # ponta arredondada do montante
        for zz, rr in ((zf - 0.03, 0.0145), (zb - 0.02, 0.0155)):                 # sapatas de feltro no piso
            g.lathe(LIN, (x, 0, zz), [(0, 0), (rr, 0), (rr + 0.001, 0.002), (rr, PAD), (0, PAD)], sides=12, col=(0.30, 0.27, 0.24, 1))
        g.tube(OAK, [V(x, 0.12, zf - 0.03), V(x, 0.12, zb - 0.005)], [0.009, 0.009], sides=8, col=lambda p, t: WALD + (1,))
    g.tube(OAK, [V(-(SW / 2 - 0.03), 0.13, (zf + zb) / 2), V((SW / 2 - 0.03), 0.13, (zf + zb) / 2)], [0.009, 0.009], sides=8, col=lambda p, t: WALD + (1,))
    for zz in (zf - 0.035, zb + 0.012):
        rbox(g, OAK, (0, Y - 0.05 + 0.0005, zz), (SW - 0.06 + 0.004, 0.035, 0.018), r=0.003, col=WALD, uv=1.6)
    for hh, th in ((Y + 0.40, 0.06), (Y + 0.27, 0.04), (Y + 0.16, 0.03)):
        zc = zb - 0.06 * ((hh - (Y - 0.03)) / 0.47) - 0.005
        pts = []; nseg = 10
        for k in range(nseg + 1):
            s = k / nseg - 0.5
            pts.append(V(s * (SW - 0.06), hh, zc + 0.03 - 0.06 * (s * 2) ** 2 * 0.5))
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
    M.empty('COL_assento', (0, Y / 2 + 0.01, (zf + zb) / 2), parent=ch, extras=dict(shape='box', size=[SW, Y + 0.03, SD], bloqueia=True, camada='movel'))
    M.empty('COL_encosto', (0, Y + 0.24, zb - 0.03), parent=ch, extras=dict(shape='box', size=[SW - 0.02, 0.46, 0.07], bloqueia=True, camada='movel'))
    M.empty('IP_sentar', (0, 0, sit_z), extras=dict(acao='sentar', inicio=[0, 0, sit_z + 0.12], aproximacao=[-0.62, 0, sit_z + 0.12],
            assento_y=Y + 0.026 - 0.013, olhar='+Z', puxar='cadeira',
            sequencia=['puxar a cadeira (0,55 s)', 'andar até a lateral', 'entrar entre a cadeira e a mesa', 'virar de costas', 'sentar',
                       'empurrar para a mesa junto com o personagem', 'sentado', 'afastar', 'levantar', 'empurrar a cadeira de volta']))
    M.bake_ao(maxd=0.18, strength=0.5)
    return finish(M)


# ================================================================================================ GUARDA-ROUPA
def guarda_roupa():
    W, D, H = 1.10, 0.50, 1.62
    t = 0.022; zF = D / 2                     # face da frente da caixa
    y0 = 0.07; ydr = 0.30
    CW = (0.94, 0.92, 0.88); INC = (0.88, 0.72, 0.52)
    M = G.Model('int_guarda_roupa', meta('int_guarda_roupa', 'Guarda-roupa', 'quarto', 'armazenamento', 'funcional',
               dict(tipo='estatico', massa=85.0, motivo='móvel alto ancorado: não tomba nem desliza'),
               estados=['fechado', 'abrindo', 'aberto', 'fechando'], grade=[2, 1],
               folgas_documentadas=['portas e frentes de gaveta: 2 mm à frente da caixa e 3 mm entre si (ligadas pelas dobradiças/trilhos)'],
               conteudo_interno=['cabides de madeira com gancho e barra', '3 camisas (lisa, xadrez, listrada) e 1 vestido pendurados', 'calças jeans, camisetas, suéteres e toalhas dobrados',
                                 'tênis e sapatilha', 'caixa organizadora com tampa', 'meias enroladas e roupas íntimas nas gavetas'],
               interacoes=[dict(acao='abrir/fechar', pecas=['porta_E', 'porta_D', 'gaveta_E', 'gaveta_D'])]))
    body = M.node('corpo'); g = body.geo
    # ---- rodapé (quadro no piso): frente recuada, fundo e laterais sob as laterais da caixa
    for sx in (-1, 1): rbox(g, PLN, (sx * (W / 2 - t / 2), y0 / 2 + 0.00025, -0.01), (t, y0 + 0.0005, D - 0.06), r=0.002, col=(0.35, 0.34, 0.33), uv=1)
    rbox(g, PLN, (0, y0 / 2 + 0.00025, zF - 0.045), (W - 2 * t + 0.001, y0 + 0.0005, 0.018), r=0.002, col=(0.35, 0.34, 0.33), uv=1)
    rbox(g, PLN, (0, y0 / 2 + 0.00025, -D / 2 + 0.03), (W - 2 * t + 0.001, y0 + 0.0005, 0.018), r=0.002, col=(0.35, 0.34, 0.33), uv=1)
    # ---- caixa: laterais (sobre o rodapé), base e topo entre/sobre elas, fundo encaixado, trave e divisórias
    for sx in (-1, 1): rbox(g, PLN, (sx * (W / 2 - t / 2), (y0 + H - t) / 2, 0), (t, H - t - y0 + 0.001, D), r=0.003, col=CW, uv=1, step=0.4)
    rbox(g, PLN, (0, H - t / 2, 0), (W, t, D), r=0.003, col=CW, uv=1, step=0.4)
    rbox(g, PLN, (0, y0 + t / 2, -0.001), (W - 2 * t + 0.001, t, D - 0.002), r=0.002, col=CW, uv=1, step=0.4)
    rbox(g, OAK, (0, (y0 + t + H - t) / 2, -D / 2 + 0.006), (W - 2 * t + 0.001, H - t - y0 - t + 0.001, 0.01), r=0.002, col=INC, uv=1.4, step=0.4)
    rbox(g, PLN, (0, H + 0.012 - 0.0005, 0.006), (W + 0.03, 0.024, D + 0.016), r=0.006, col=CW, uv=1, step=0.4)          # coroa
    rbox(g, PLN, (0, ydr, -0.001), (W - 2 * t + 0.001, t, D - 0.002), r=0.002, col=CW, uv=1, step=0.4)                    # trave
    rbox(g, OAK, (0, (ydr + t / 2 + H - t) / 2, -0.004), (0.02, H - t - ydr - t / 2 + 0.001, D - 0.012), r=0.003, col=INC, uv=1.4, step=0.4)   # divisória
    rbox(g, PLN, (0, (y0 + t + ydr - t / 2) / 2, -0.004), (0.02, ydr - t / 2 - y0 - t + 0.001, D - 0.012), r=0.002, col=CW, uv=1)
    xin = W / 2 - t                          # face interna da lateral
    content_E = M.node('conteudo_E', extras=dict(mostrar_quando=['porta_E'], nota='interior esquerdo: só desenhado com a porta aberta (Android)'))
    content_D = M.node('conteudo_D', extras=dict(mostrar_quando=['porta_D'], nota='interior direito: só desenhado com a porta aberta (Android)'))
    gE = content_E.geo; gD = content_D.geo
    # ---- lado esquerdo: 4 prateleiras apoiadas na lateral e na divisória (com pinos de apoio)
    shelves = (0.62, 0.92, 1.22, 1.48); ts = 0.018
    for yy in shelves:
        rbox(g, OAK, ((-xin - 0.01) / 2, yy, -0.003), (xin - 0.01 + 0.001, ts, D - 0.03), r=0.002, col=INC, uv=1.4)
        for xx in (-xin + 0.004, -0.014):
            for zz in (-0.17, 0.17):
                g.lathe(MET, (xx, yy - ts / 2 - 0.005, zz), [(0, 0), (0.003, 0), (0.003, 0.0055), (0, 0.0055)], sides=8, col=C4(CHROME))
    top = lambda yy: yy + ts / 2
    xl = (-xin - 0.01) / 2                     # centro do vão esquerdo
    CT.pilha(gE, [CT.calca_dobrada((0.22, 0.32, 0.52)), CT.calca_dobrada((0.15, 0.20, 0.33)), CT.calca_dobrada((0.60, 0.55, 0.45))], xl - 0.125, top(0.62), 0.01)
    CT.pilha(gE, [CT.blusa_trico_dobrada((0.55, 0.20, 0.22)), CT.blusa_trico_dobrada((0.85, 0.80, 0.70))], xl + 0.13, top(0.62), 0.01)
    CT.pilha(gE, [CT.camiseta_dobrada((0.95, 0.95, 0.94)), CT.camiseta_dobrada((0.20, 0.24, 0.30), estampa=(0.9, 0.7, 0.2)), CT.camiseta_dobrada((0.88, 0.45, 0.35)), CT.camiseta_dobrada((0.40, 0.55, 0.40))],
             xl - 0.125, top(0.92), 0.015)
    CT.pilha(gE, [CT.camiseta_dobrada((0.16, 0.16, 0.18)), CT.camiseta_dobrada((0.95, 0.85, 0.40)), CT.camiseta_dobrada((0.55, 0.70, 0.85), estampa=(0.95, 0.95, 0.95))],
             xl + 0.13, top(0.92), 0.015)
    CT.pilha(gE, [CT.blusa_trico_dobrada((0.30, 0.42, 0.32)), CT.blusa_trico_dobrada((0.20, 0.22, 0.35))], xl - 0.125, top(1.22), 0.01)
    CT.pilha(gE, [CT.toalha_dobrada((0.95, 0.93, 0.88), w=0.24, d=0.2), CT.toalha_dobrada((0.55, 0.70, 0.80), w=0.24, d=0.2)], xl + 0.13, top(1.22), 0.02)
    CT.pilha(gE, [CT.toalha_dobrada((0.85, 0.55, 0.50), w=0.24, d=0.2)], xl - 0.125, top(1.48), 0.02)
    CT.pilha(gE, [CT.toalha_dobrada((0.97, 0.97, 0.95), w=0.24, d=0.2)], xl + 0.13, top(1.48), 0.02)
    cx_, ci = CT.caixa_organizadora((0.80, 0.84, 0.88), w=0.40, d=0.30, h=0.17)
    place(gE, cx_, xl, ydr + t / 2 - EMB, -0.02)
    # ---- lado direito: cabideiro com suportes (flanges) parafusados na divisória e na lateral
    rx0, rx1 = 0.01, xin; ry = 1.42; rz = -0.005; rr = 0.011
    g.tube(MET, [V(rx0 + 0.0055, ry, rz), V(rx1 - 0.0055, ry, rz)], [rr, rr], sides=14, col=lambda p, tt: C4(CHROME))
    for xx, sgn in ((rx0, 1), (rx1, -1)):
        tmp = Geo(); tmp.lathe(MET, (0, 0, 0), [(0, 0), (0.024, 0), (0.024, 0.003), (0.016, 0.006), (0.0125, 0.0115), (0, 0.0115)], sides=16, col=C4(CHROME))
        add_xf(g, tmp, rot_z(-sgn * math.pi / 2), (xx - sgn * 0.0005, ry, rz))
    # prateleira de cima do lado direito (sobre suportes de metal na divisória e na lateral)
    ysd = 1.50
    rbox(g, OAK, ((rx0 + rx1) / 2, ysd, -0.003), (rx1 - rx0 + 0.001, ts, D - 0.03), r=0.002, col=INC, uv=1.4)
    for xx in (rx0 + 0.004, rx1 - 0.004):
        for zz in (-0.17, 0.17):
            g.lathe(MET, (xx, ysd - ts / 2 - 0.005, zz), [(0, 0), (0.003, 0), (0.003, 0.0055), (0, 0.0055)], sides=8, col=C4(CHROME))
    CT.pilha(gD, [CT.toalha_dobrada((0.75, 0.82, 0.70), w=0.22, d=0.2)], 0.15, ysd + ts / 2, 0.02)
    CT.pilha(gD, [CT.blusa_trico_dobrada((0.75, 0.62, 0.45), w=0.2, d=0.26)], 0.40, ysd + ts / 2, 0.0)
    # cabides com roupas (escala do jogo: 0,85 das medidas de adulto real), construídos para o tubo encostar no gancho
    S = 0.85
    roupas = [('camisa', dict(cor=(0.92, 0.94, 0.97))), ('camisa', dict(cor=(0.75, 0.25, 0.25), xadrez=(0.25, 0.22, 0.30))),
              ('vestido', dict(cor=(0.30, 0.45, 0.62), estampa=(0.95, 0.95, 0.90))), ('camisa', dict(cor=(0.45, 0.62, 0.78))),
              ('camisa', dict(cor=(0.20, 0.22, 0.25))), ('camisa', dict(cor=(0.88, 0.80, 0.62)))]
    xs = np.linspace(rx0 + 0.055, rx1 - 0.055, len(roupas))
    for (kind, kw), xx in zip(roupas, xs):
        hg, hi = CT.cabide(rr / S)
        piece = Geo()
        add_xf(piece, hg)
        if kind == 'camisa': add_xf(piece, CT.camisa_pendurada(arm_top=hi['arm_top'], **kw))
        else: add_xf(piece, CT.vestido_pendurado(arm_top=hi['arm_top'], **kw))
        add_xf(gD, piece, np.diag([S, S, S]) @ rot_y(0.06 * math.sin(xx * 40)), (xx, ry, rz))
    # sapatos no fundo direito (sobre a trave), pares lado a lado
    yb = ydr + t / 2 - EMB
    for i, (fn, kw) in enumerate(((CT.tenis, dict(cor=(0.20, 0.30, 0.50))), (CT.sapatilha, dict(cor=(0.62, 0.20, 0.25))))):
        for lado in (-1, 1):
            sg, si = fn(lado=lado, **kw)
            add_xf(gD, sg, np.diag([S, S, S]) @ rot_y(0.05 * lado), (0.12 + i * 0.24 + lado * 0.048, yb, 0.03))
    # ---- portas (sobrepostas à frente da caixa, 2 mm de folga; dobradiças de pino com aba parafusada na lateral)
    dz0 = zF + 0.002; dth = 0.022
    ph = H - 0.003 - (ydr + 0.0015); py = ydr + 0.0015 + ph / 2
    for sx, nm in ((-1, 'porta_E'), (1, 'porta_D')):
        ax_x = sx * (W / 2 - 0.006); ax_z = dz0 + dth / 2
        pw = W / 2 - 0.0075 - 0.0015; cx = sx * (0.0015 + pw / 2)
        ang = math.radians(105) * (-1 if sx < 0 else 1)
        dn = M.node(nm, (ax_x, py, ax_z), extras=dict(anim=dict(tipo='dobradica', eixo=[0, 1, 0], min=0.0, max=round(ang, 4), dur=0.65, curva='suave', estado_inicial=0.0,
                    alca=[cx - sx * (pw / 2 - 0.05), 1.0, dz0 + dth + 0.05], rotulo='porta', raio=round(pw, 3), colide_com=['parede', 'movel'])))
        gd = dn.geo
        rbox(gd, PLN, (cx, py, dz0 + dth / 2), (pw, ph, dth), r=0.004, col=CW, uv=1, step=0.25)
        for yy, hh in ((py + ph * 0.2, ph * 0.52), (py - ph * 0.32, ph * 0.28)):
            rbox(gd, PLN, (cx, yy, dz0 + dth + 0.002), (pw - 0.09, hh, 0.005), r=0.002, col=tuple(np.array(CW) * 0.97), uv=1, step=0.25)
        kx = cx - sx * (pw / 2 - 0.05); zfront = dz0 + dth
        gd.tube(MET, [V(kx, 0.86, zfront + 0.028), V(kx, 1.14, zfront + 0.028)], [0.007, 0.007], sides=10, col=lambda p, tt: C4(BRASS))
        for yy in (0.88, 1.12): gd.tube(MET, [V(kx, yy, zfront - 0.0005), V(kx, yy, zfront + 0.028)], [0.005, 0.005], sides=8, col=lambda p, tt: C4(BRASS))
        for yy in (py - ph / 2 + 0.08, py, py + ph / 2 - 0.08):
            # pino (corpo) + aba parafusada na frente da lateral; o pino atravessa a borda da porta
            g.tube(MET, [V(ax_x, yy - 0.03, ax_z), V(ax_x, yy + 0.03, ax_z)], [0.0055, 0.0055], sides=10, col=lambda p, tt: C4(BRASS))
            for e in (-1, 1): sphere(g, MET, (ax_x, yy + e * 0.03, ax_z), 0.0055, BRASS, seg=5, sy=0.5)
            rbox(g, MET, (sx * (W / 2 - 0.011), yy, (zF - 0.0005 + ax_z) / 2), (0.016, 0.05, ax_z - zF + 0.0005), r=0.0008, col=BRASS, uv=1)
    # ---- gavetas: corrediça presa na lateral/divisória, caixa da gaveta encostada na corrediça (curso 30 cm)
    fy0 = y0 + 0.003; fy1 = ydr - 0.0015; fh = fy1 - fy0; fyc = (fy0 + fy1) / 2
    ob0 = y0 + t                               # topo da base
    bh = (ydr - t / 2) - ob0 - 0.018           # altura da caixa (folga de 18 mm em cima)
    by0 = ob0 + 0.006                          # caixa fica 6 mm acima da base, pendurada nas corrediças
    rail_y = by0 + bh * 0.45; rl = 0.40; rth = 0.0125
    for sx, nm in ((-1, 'gaveta_E'), (1, 'gaveta_D')):
        oa = 0.01; ob = xin                     # vão: da divisória (x=0,01) à lateral
        xa = sx * oa; xb = sx * ob
        for xx in (xa + sx * rth / 2, xb - sx * rth / 2):
            rbox(g, MET, (xx, rail_y, zF - 0.01 - rl / 2), (rth + 0.001, 0.014, rl), r=0.001, col=(0.70, 0.72, 0.74), uv=1)
        bw = ob - oa - 2 * rth; bcx = sx * (oa + rth + bw / 2)
        fw = W / 2 - 0.0075 - 0.0015; fcx = sx * (0.0015 + fw / 2)
        dn = M.node(nm, (fcx, fyc, dz0), extras=dict(anim=dict(tipo='trilho', eixo=[0, 0, 1], min=0.0, max=0.30, dur=0.45, curva='suave', estado_inicial=0.0,
                    alca=[fcx, fyc + 0.02, dz0 + 0.07], rotulo='gaveta', colide_com=['parede', 'movel'])))
        gd = dn.geo; INB = (0.86, 0.70, 0.50)
        rbox(gd, PLN, (fcx, fyc, dz0 + 0.011), (fw, fh, 0.022), r=0.004, col=CW, uv=1, step=0.25)
        bz0 = dz0 - 0.40; bz1 = dz0 + 0.0005
        for s2 in (-1, 1):                     # laterais da caixa (encostam nas corrediças)
            rbox(gd, OAK, (bcx + s2 * (bw / 2 - 0.006), by0 + bh / 2, (bz0 + bz1) / 2), (0.012, bh, bz1 - bz0), r=0.002, col=INB, uv=1.4)
        rbox(gd, OAK, (bcx, by0 + 0.003, (bz0 + bz1) / 2), (bw - 0.023, 0.006, bz1 - bz0 - 0.001), r=0.001, col=INB, uv=1.4)       # fundo
        rbox(gd, OAK, (bcx, by0 + bh / 2, bz0 + 0.006), (bw - 0.023, bh, 0.012), r=0.002, col=INB, uv=1.4)                        # traseira
        rbox(gd, OAK, (bcx, by0 + bh / 2, bz1 - 0.006), (bw - 0.023, bh, 0.012), r=0.002, col=INB, uv=1.4)                        # frente interna
        gd.tube(MET, [V(fcx - 0.08, fyc + 0.02, dz0 + 0.05), V(fcx + 0.08, fyc + 0.02, dz0 + 0.05)], [0.007, 0.007], sides=10, col=lambda p, tt: C4(BRASS))
        for xx in (fcx - 0.08, fcx + 0.08): gd.tube(MET, [V(xx, fyc + 0.02, dz0 + 0.0215), V(xx, fyc + 0.02, dz0 + 0.05)], [0.005, 0.005], sides=8, col=lambda p, tt: C4(BRASS))
        # conteúdo da gaveta (nó filho: só desenhado com a gaveta aberta)
        cn = M.node('conteudo_' + nm, (fcx, fyc, dz0), parent=dn, extras=dict(mostrar_quando=[nm], nota='conteúdo da gaveta'))
        gc = cn.geo; fl = by0 + 0.006
        if sx < 0:
            cols = [(0.15, 0.15, 0.17), (0.92, 0.92, 0.92), (0.30, 0.40, 0.60), (0.75, 0.30, 0.30), (0.55, 0.55, 0.52), (0.95, 0.80, 0.30)]
            k = 0
            for row in range(3):
                for col_ in range(4):
                    sg, si = CT.meia_enrolada(cols[k % len(cols)], listra=(0.9, 0.2, 0.2) if k % 3 == 0 else None); k += 1
                    place(gc, sg, bcx - bw / 2 + 0.07 + col_ * 0.11, fl - EMB, bz0 + 0.07 + row * 0.11, yaw=0.15 * ((k % 3) - 1))
        else:
            for i, c in enumerate(((0.20, 0.22, 0.35), (0.85, 0.85, 0.85), (0.40, 0.15, 0.20))):
                CT.pilha(gc, [CT.cueca_dobrada(c), CT.cueca_dobrada(tuple(np.array(c) * 0.9))], bcx - bw / 2 + 0.085 + i * 0.15, fl, bz0 + 0.09)
            CT.pilha(gc, [CT.camiseta_dobrada((0.95, 0.95, 0.94), w=0.2, d=0.22, h=0.03), CT.camiseta_dobrada((0.30, 0.30, 0.32), w=0.2, d=0.22, h=0.03)],
                     bcx, fl, bz0 + 0.27)
    M.empty('COL_corpo', (0, (H + 0.024) / 2, 0), extras=dict(shape='box', size=[W + 0.03, H + 0.024, D], bloqueia=True, camada='movel'))
    M.empty('SURF_topo', (0, H + 0.024, 0), extras=dict(shape='box', size=[W, 0, D], recebe='caixas, objetos'))
    M.empty('IP_usar', (0, 0, D / 2 + 0.45), extras=dict(acao='abrir/fechar', olhar='-Z', nota='a peça usada é a mais perto do olhar'))
    M.bake_ao(maxd=0.25, strength=0.55)
    return finish(M)


ALL = [cadeira, mesa, guarda_roupa]

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/glb_e1'
    only = sys.argv[2:] or None
    os.makedirs(out, exist_ok=True)
    for f in ALL:
        if only and f.__name__ not in only: continue
        M = f(); fn = os.path.join(out, M.id + '.glb'); n = M.write_glb(fn)
        err, warn, info = G.verify(fn)
        print('%-20s %7d bytes %6d vért. %6d tri. erros=%d avisos=%d %s' % (M.id, n, info['vertices'], info['triangulos'], len(err), len(warn), M.meta['dimensoes']))
        for e in err: print('   ERRO:', e)
        for w in warn: print('   aviso:', w)
