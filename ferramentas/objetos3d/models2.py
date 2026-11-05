"""Lote 2 da biblioteca 3D: sofá de 3 lugares, cama de casal, geladeira, fogão com forno e pia de cozinha.
Mesma convenção e escala do lote 1 (models.py). Uso: python3 models2.py <pasta de saída>
Novidades de metadados neste lote:
  * anim.gatilho = "ligado"  -> a peça segue o estado ligado/desligado do aparelho (botões, alavanca)
  * anim.gatilho = "ocupado" + anim.assento = "IP_sentar_N" -> almofada daquele lugar afunda
  * extras.efeito = {"tipo": "chama"|"agua"|"luz", "quando": "ligado" | "<peça aberta>"} -> nó só aparece nesse estado
  * IP_usar com acao "ligar" (rotulo_ligar/rotulo_desligar); IP_deitar_* com acao "deitar" (sentar na borda + deitado)
"""
import sys, os, math, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import *          # noqa
import glb_lib as G
import models as M1
from models import OAK, LIN, GLZ, MET, PLN, OAKC, OAKD, BRASS, meta, finish, recolor

STEEL = (0.80, 0.82, 0.85); WHITE = (0.95, 0.95, 0.94); DARK = (0.12, 0.12, 0.13)
CHROME = ('escovado.png', 11, 0)
SEAT_TOP = M1.SEAT_TOP; SIT_Z = M1.SIT_Z


def emit_box(g, key, c, size, col):
    """caixa sem iluminação (normais zero = emissiva no jogo e no GLB)"""
    tmp = Geo(); rbox(tmp, key, c, size, r=min(size) * 0.3, col=col, uv=1.0, step=1)
    for k, P, N, C, UV, T in tmp.arrays(): g.add(k, P, N * 0, C, UV, T)


# ================================================================================================ SOFÁ 3 LUGARES
def sofa3():
    W = 1.78; X = W / 2 - 0.045
    M = G.Model('int_sofa3', meta('int_sofa3', 'Sofá de 3 lugares', 'sala', 'assentos', 'interativo',
               dict(tipo='estatico', massa=48.0, motivo='móvel grande ancorado'), estados=['livre', 'ocupado'], grade=[2, 1],
               interacoes=[dict(acao='sentar', pontos=['IP_sentar_0', 'IP_sentar_1', 'IP_sentar_2'], cancelavel=True)]))
    fr = M.node('estrutura'); g = fr.geo
    def leg(x, z0, z1, y1, r0, r1):
        pts = [V(x, 0, z0), V(x, y1 * 0.5, (z0 + z1) / 2), V(x, y1, z1)]
        g.tube(OAK, pts, [r0, (r0 + r1) / 2 * 1.05, r1], sides=12, col=lambda p, t: OAKC + (1,), vscale=1.6)
    for sx in (-1, 1):
        x = sx * X
        leg(x, 0.265, 0.235, 0.485, 0.017, 0.023)
        leg(x, -0.285, -0.235, 0.485, 0.017, 0.023)
        rbox(g, OAK, (x, 0.494, 0.005), (0.074, 0.024, 0.60), r=0.011, col=OAKC, uv=2.0, step=0.12)
        rbox(g, OAK, (x, 0.494, 0.27), (0.086, 0.024, 0.07), r=0.012, col=OAKC, uv=2.0, step=0.06)
        rbox(g, OAK, (x - sx * 0.03, 0.215, 0.0), (0.026, 0.05, 0.50), r=0.006, col=OAKC, uv=2.0)
    for z in (0.235, -0.235):
        rbox(g, OAK, (0, 0.215, z), (W - 0.1, 0.05, 0.026), r=0.006, col=OAKC, uv=2.0, step=0.4)
    # pés do meio (sofá comprido não pode envergar)
    for z in (0.2, -0.2):
        g.tube(OAK, [V(0, 0, z), V(0, 0.19, z)], [0.018, 0.02], sides=10, col=lambda p, t: OAKD + (1,))
    rbox(g, LIN, (0, 0.238, 0.0), (W - 0.12, 0.012, 0.47), r=0.004, col=(0.25, 0.26, 0.27), uv=3.0, step=0.5)
    lean = math.radians(9)
    for xx in (-X + 0.04, -0.3, 0.3, X - 0.04):
        a = V(xx, 0.22, -0.245); b2 = a + V(0, 0.54 * math.cos(lean), -0.54 * math.sin(lean))
        g.tube(OAK, [a, (a + b2) / 2, b2], [0.017, 0.018, 0.016], sides=10, col=lambda p, t: OAKC + (1,), vscale=1.6)
    top = V(0, 0.22 + 0.53 * math.cos(lean), -0.245 - 0.53 * math.sin(lean))
    tmp = Geo(); rbox(tmp, OAK, (0, 0, 0), (W - 0.06, 0.05, 0.024), r=0.008, col=OAKC, uv=2.0, step=0.4); add_xf(g, tmp, rot_x(-lean), top)
    for hh in (0.30, 0.44):
        tmp = Geo(); rbox(tmp, OAK, (0, 0, 0), (W - 0.1, 0.035, 0.016), r=0.006, col=OAKD, uv=2.0, step=0.4)
        add_xf(g, tmp, rot_x(-lean), V(0, 0.22 + hh * math.cos(lean), -0.245 - hh * math.sin(lean) - 0.004))
    fab = (0.80, 0.58, 0.30); pip = (0.62, 0.42, 0.20)        # linho mostarda
    sw = (W - 0.16) / 3
    for i in range(3):
        cx = (i - 1) * sw
        cu = M.node('almofada_assento_%d' % i, (cx, 0.244, 0.06), extras=dict(anim=dict(tipo='escala', eixo=[0, 1, 0], min=1.0, max=0.88, dur=0.6,
                    curva='suave', gatilho='ocupado', assento='IP_sentar_%d' % i, estado_inicial=1.0)))
        gc = cu.geo
        rbox(gc, LIN, (cx, 0.2995, 0.06), (sw - 0.006, 0.111, 0.385), r=0.042, col=fab, uv=3.2, puff=0.016, step=0.07)
        piping(gc, LIN, cx, 0.2995 + 0.111 / 2 - 0.023, 0.06, sw - 0.012, 0.378, 0.0075, pip, rad=0.042)
        piping(gc, LIN, cx, 0.2995 - 0.111 / 2 + 0.023, 0.06, sw - 0.012, 0.378, 0.0075, pip, rad=0.042)
        bk = M.node('almofada_encosto_%d' % i, (cx, 0.345, -0.15)); gb = bk.geo
        tmp = Geo()
        rbox(tmp, LIN, (0, 0.21, -0.065), (sw - 0.01, 0.42, 0.13), r=0.045, col=fab, uv=3.2, puff=0.02, step=0.07)
        for (bx, by) in ((-0.13, 0.15), (0.13, 0.15), (0.0, 0.29)):
            sphere(tmp, LIN, (bx, by, 0.019), 0.012, tuple(np.array(fab) * 0.8), seg=8, sy=0.6)
        add_xf(gb, tmp, rot_x(-lean), V(cx, 0.345, -0.108))
    # manta de tricô dobrada sobre o braço esquerdo (decoração, sem colisão)
    mt = M.node('manta'); gm = mt.geo
    nx_, nz_ = 14, 22
    Pm = np.zeros((nz_, nx_, 3))
    for j in range(nz_):
        for i in range(nx_):
            s = i / (nx_ - 1); t = j / (nz_ - 1)
            z = -0.20 + 0.40 * s
            # perfil: sobe pelo lado de fora, passa por cima do braço, desce pelo lado de dentro (meia volta)
            ang = (t - 0.5) * math.pi * 1.05
            px = -X + math.sin(ang) * 0.06; py = 0.506 + 0.012 + math.cos(ang) * 0.02 - max(0, abs(t - 0.5) - 0.25) * 0.55
            px += (abs(t - 0.5) > 0.25) * math.copysign(1, t - 0.5) * 0.0
            wav = 0.006 * math.sin(s * 9 + t * 4)
            Pm[j, i] = (px + wav, py, z)
    Pf = Pm.reshape(-1, 3); T = []
    for j in range(nz_ - 1):
        for i in range(nx_ - 1):
            a_ = j * nx_ + i; T += [(a_, a_ + 1, a_ + nx_), (a_ + 1, a_ + nx_ + 1, a_ + nx_)]
    T = np.array(T); Nm = grid_normals(Pf, T)
    Nm *= np.where((Nm * (Pf - np.array([-X, 0.45, 0]))).sum(1, keepdims=True) < 0, -1, 1)
    UVm = np.array([(i / (nx_ - 1) * 3, j / (nz_ - 1) * 3) for j in range(nz_) for i in range(nx_)])
    gm.add(LIN, Pf, Nm, [(0.92, 0.90, 0.84, 1)] * len(Pf), UVm, T)
    # o braço também tem a parte de dentro/fora da manta: espessura (cópia empurrada)
    gm.add(LIN, Pf - Nm * 0.006, -Nm, [(0.86, 0.84, 0.78, 1)] * len(Pf), UVm, T[:, [0, 2, 1]])
    M.empty('COL_base', (0, 0.18, -0.005), extras=dict(shape='box', size=[W + 0.01, 0.36, 0.57], bloqueia=True, camada='movel'))
    for sx in (-1, 1):
        M.empty('COL_braco_' + ('D' if sx > 0 else 'E'), (sx * X, 0.43, 0.005), extras=dict(shape='box', size=[0.088, 0.14, 0.60], bloqueia=True, camada='movel'))
    M.empty('COL_encosto', (0, 0.56, -0.235), extras=dict(shape='box', size=[W - 0.05, 0.42, 0.16], bloqueia=True, camada='movel'))
    for i in range(3):
        cx = (i - 1) * sw
        M.empty('IP_sentar_%d' % i, (cx, 0, SIT_Z), extras=dict(acao='sentar', aproximacao=[cx, 0, SIT_Z + 0.42], inicio=[cx, 0, SIT_Z + 0.12],
                assento_y=SEAT_TOP - 0.013, olhar='+Z', almofada='almofada_assento_%d' % i))
    M.bake_ao(maxd=0.22, strength=0.55)
    return finish(M)


# ================================================================================================ CAMA DE CASAL
def cama():
    MW, ML, MT = 1.16, 1.62, 0.33          # colchão: largura, comprimento, topo (com o edredom fica a 0,37)
    z0 = -ML / 2; z1 = ML / 2
    M = G.Model('int_cama_casal', meta('int_cama_casal', 'Cama de casal', 'quarto', 'camas', 'interativo',
               dict(tipo='estatico', massa=70.0, motivo='estrutura ancorada; colchão e roupa de cama não têm física'),
               estados=['livre', 'sentado', 'deitado'], grade=[2, 2],
               interacoes=[dict(acao='deitar', pontos=['IP_deitar_E', 'IP_deitar_D'], cancelavel=True)]))
    fr = M.node('estrutura'); g = fr.geo
    # base (estrado com saia de madeira), pés
    rbox(g, OAK, (0, 0.17, 0.02), (MW + 0.08, 0.14, ML + 0.06), r=0.012, col=OAKC, uv=1.6, step=0.4)
    for sx in (-1, 1):
        for zz in (z0 + 0.06, z1 - 0.02):
            g.tube(OAK, [V(sx * (MW / 2 - 0.02), 0, zz), V(sx * (MW / 2 - 0.02), 0.11, zz)], [0.022, 0.026], sides=12, col=lambda p, t: OAKD + (1,))
    # cabeceira estofada com capitonê em losango, moldura de madeira
    hb = -ML / 2 - 0.04
    rbox(g, OAK, (0, 0.52, hb - 0.03), (MW + 0.16, 0.94, 0.05), r=0.015, col=OAKC, uv=1.6, step=0.3)
    hfab = (0.62, 0.66, 0.70)
    rbox(g, LIN, (0, 0.64, hb + 0.005), (MW + 0.02, 0.62, 0.06), r=0.03, col=hfab, uv=3, puff=0.012, step=0.06)
    for r_ in range(3):
        for c_ in range(6):
            bx = -0.45 + c_ * 0.18 + (0.09 if r_ % 2 else 0)
            if abs(bx) > 0.52: continue
            sphere(g, LIN, (bx, 0.45 + r_ * 0.17, hb + 0.04), 0.011, tuple(np.array(hfab) * 0.75), seg=8, sy=0.6)
    # colchão (volumétrico, vivo nas bordas)
    rbox(g, LIN, (0, MT - 0.075, 0.02), (MW, 0.15, ML), r=0.04, col=(0.94, 0.94, 0.92), uv=3, puff=0.006, step=0.15)
    piping(g, LIN, 0, MT - 0.01, 0.02, MW - 0.01, ML - 0.01, 0.006, (0.80, 0.82, 0.84), rad=0.04)
    # edredom: cobre do pé até 0,45 m da cabeceira, cai 18 cm pelos lados; dobra virada perto do travesseiro
    ed = (0.45, 0.55, 0.62)
    nx_, nz_ = 26, 30
    zs = np.linspace(z0 + 0.42, z1 + 0.03, nz_)
    Pm = np.zeros((nz_, nx_, 3))
    for j, z in enumerate(zs):
        for i in range(nx_):
            s = i / (nx_ - 1) * 2 - 1
            half = MW / 2 + 0.035
            if abs(s) < 0.72:
                x = s / 0.72 * half * 0.86; y = MT + 0.04 + 0.006 * math.sin(i * 1.7 + j * 0.9)
            else:
                u = (abs(s) - 0.72) / 0.28
                ang = u * math.pi / 2
                x = math.copysign(half * 0.86 + math.sin(ang) * half * 0.14 + (u > 0.5) * 0.0, s)
                y = MT + 0.04 - (1 - math.cos(ang)) * 0.03 - u * u * 0.17
                x = math.copysign(min(abs(x), half), s)
            if z > z1 - 0.02: y -= (z - (z1 - 0.02)) * 3.0 * min(1, 0.4 + abs(s))
            Pm[j, i] = (x, y, z)
    Pf = Pm.reshape(-1, 3); T = []
    for j in range(nz_ - 1):
        for i in range(nx_ - 1):
            a_ = j * nx_ + i; T += [(a_, a_ + nx_, a_ + 1), (a_ + 1, a_ + nx_, a_ + nx_ + 1)]
    T = np.array(T); Nm = grid_normals(Pf, T)
    if Nm[:, 1].mean() < 0: Nm = -Nm; T = T[:, [0, 2, 1]]
    UVm = Pf[:, [0, 2]] * 3
    g.add(LIN, Pf, Nm, [ed + (1,)] * len(Pf), UVm, T)
    g.add(LIN, Pf - Nm * 0.012, -Nm, [tuple(np.array(ed) * 0.8) + (1,)] * len(Pf), UVm, T[:, [0, 2, 1]])
    # dobra virada (lençol branco aparecendo)
    rbox(g, LIN, (0, MT + 0.045, z0 + 0.43), (MW + 0.06, 0.03, 0.12), r=0.014, col=(0.96, 0.96, 0.95), uv=3, puff=0.004, step=0.1)
    # travesseiros (2 por lado), um apoiado na cabeceira
    for sx in (-1, 1):
        x = sx * 0.28
        rbox(g, LIN, (x, MT + 0.05, z0 + 0.20), (0.48, 0.10, 0.30), r=0.045, col=(0.97, 0.97, 0.96), uv=3, puff=0.03, step=0.06)
        tmp = Geo(); rbox(tmp, LIN, (0, 0, 0), (0.46, 0.30, 0.10), r=0.045, col=(0.80, 0.70, 0.55), uv=3, puff=0.03, step=0.06)
        add_xf(g, tmp, rot_x(-math.radians(18)), V(x, MT + 0.17, z0 + 0.05))
    M.empty('COL_base', (0, 0.19, 0.02), extras=dict(shape='box', size=[MW + 0.08, 0.38, ML + 0.06], bloqueia=True, camada='movel'))
    M.empty('COL_cabeceira', (0, 0.5, hb - 0.01), extras=dict(shape='box', size=[MW + 0.16, 1.0, 0.09], bloqueia=True, camada='movel'))
    M.empty('SURF_colchao', (0, MT + 0.04, 0.1), extras=dict(shape='box', size=[MW, 0, ML - 0.4], recebe='objetos leves'))
    # deitar: senta na borda (de costas para a cama) e deita com a cabeça no travesseiro
    for sx, nm in ((-1, 'IP_deitar_E'), (1, 'IP_deitar_D')):
        edge = sx * (MW / 2 + 0.04)
        sit_x = edge + sx * 0.15          # raiz (pés) 15 cm para fora da borda; o traseiro fica 15 cm dentro
        M.empty(nm, (sit_x, 0, 0.12), yaw=math.atan2(sx, 0) if False else (math.pi / 2 if sx > 0 else -math.pi / 2),
                extras=dict(acao='deitar', aproximacao=[edge + sx * 0.6, 0, 0.12], inicio=[edge + sx * 0.27, 0, 0.12],
                            assento_y=MT + 0.03, deitado=[sx * 0.28, MT + 0.045, z0 + 0.12], olhar=('+X' if sx > 0 else '-X'),
                            sequencia=['andar até o lado', 'virar de costas', 'sentar na borda', 'deitar (1 s)', 'deitado', 'sentar', 'levantar']))
    M.bake_ao(maxd=0.25, strength=0.5)
    return finish(M)


# ================================================================================================ GELADEIRA
def geladeira():
    W, D, H = 0.62, 0.60, 1.48; t = 0.035
    zf = D / 2 - 0.06               # frente da caixa (portas ficam rente)
    M = G.Model('int_geladeira', meta('int_geladeira', 'Geladeira duplex', 'cozinha', 'eletrodomesticos', 'funcional',
               dict(tipo='estatico', massa=60.0, motivo='eletrodoméstico pesado ancorado'),
               estados=['fechada', 'abrindo', 'aberta', 'fechando'], grade=[1, 1],
               interacoes=[dict(acao='abrir/fechar', pecas=['porta_freezer', 'porta_geladeira', 'gaveta_legumes'])]))
    body = M.node('corpo'); g = body.geo
    WH = WHITE
    # carcaça (laterais, topo, base, fundo) com espessura real, interior branco-gelo
    rbox(g, PLN, (-(W / 2 - t / 2), H / 2 + 0.02, -0.03), (t, H - 0.04, D - 0.06), r=0.006, col=WH, uv=1, step=0.5)
    rbox(g, PLN, ((W / 2 - t / 2), H / 2 + 0.02, -0.03), (t, H - 0.04, D - 0.06), r=0.006, col=WH, uv=1, step=0.5)
    rbox(g, PLN, (0, H - t / 2, -0.03), (W, t, D - 0.06), r=0.01, col=WH, uv=1, step=0.5)
    rbox(g, PLN, (0, 0.06, -0.03), (W, 0.08, D - 0.06), r=0.006, col=WH, uv=1, step=0.5)
    rbox(g, PLN, (0, H / 2 + 0.02, -D / 2 + 0.015), (W - 0.02, H - 0.04, 0.03), r=0.004, col=(0.90, 0.92, 0.93), uv=1, step=0.5)
    rbox(g, PLN, (0, 0.03, D / 2 - 0.07), (W - 0.04, 0.05, 0.02), r=0.004, col=DARK, uv=1)          # grade do rodapé
    for xx in np.linspace(-0.24, 0.24, 13):
        rbox(g, PLN, (xx, 0.03, D / 2 - 0.059), (0.008, 0.035, 0.004), r=0.001, col=(0.05, 0.05, 0.05), uv=1, step=1)
    ysep = 1.02
    rbox(g, PLN, (0, ysep, -0.03), (W - 0.02, 0.05, D - 0.08), r=0.006, col=WH, uv=1, step=0.5)            # divisória freezer
    liner = (0.93, 0.95, 0.97)
    # prateleiras (bordas de plástico + vidro claro opaco), produtos
    for yy in (0.40, 0.62, 0.84):
        rbox(g, PLN, (0, yy, -0.04), (W - 2 * t, 0.008, D - 0.14), r=0.002, col=(0.82, 0.90, 0.94), uv=1, step=0.5)
        rbox(g, PLN, (0, yy + 0.006, zf - 0.07), (W - 2 * t, 0.02, 0.012), r=0.003, col=liner, uv=1)
    rng = np.random.default_rng(3)
    # jarra, potes, frutas, iogurtes
    g.lathe(GLZ, (-0.15, 0.408, -0.05), [(0, 0), (0.055, 0), (0.06, 0.02), (0.06, 0.16), (0.045, 0.19), (0.0, 0.19)], sides=20, col=(0.95, 0.75, 0.30, 1))
    for i in range(3):
        rbox(g, PLN, (0.05 + i * 0.07, 0.43, -0.03), (0.06, 0.05, 0.08), r=0.012, col=[(0.85, 0.3, 0.3), (0.3, 0.6, 0.85), (0.95, 0.95, 0.9)][i], uv=1, step=1)
    for i in range(5):
        sphere(g, PLN, (-0.16 + i * 0.07 + rng.uniform(-0.01, 0.01), 0.665, -0.04 + rng.uniform(-0.04, 0.04)), 0.035, [(0.85, 0.15, 0.12), (0.95, 0.65, 0.12), (0.4, 0.7, 0.2)][i % 3], seg=10)
    rbox(g, PLN, (0.1, 0.89, -0.06), (0.26, 0.09, 0.16), r=0.02, col=(0.95, 0.95, 0.96), uv=1, step=1)   # pote grande
    rbox(g, PLN, (-0.14, 0.87, -0.05), (0.14, 0.05, 0.12), r=0.01, col=(0.95, 0.85, 0.55), uv=1, step=1)  # queijo
    # freezer: gavetas de gelo e potes
    rbox(g, PLN, (0, 1.12, -0.05), (W - 0.1, 0.06, D - 0.18), r=0.01, col=(0.85, 0.92, 0.97), uv=1)
    for i in range(3): rbox(g, PLN, (-0.15 + i * 0.15, 1.25, -0.06), (0.12, 0.10, 0.16), r=0.02, col=(0.92, 0.95, 0.98), uv=1, step=1)
    # luz interna (só acesa com a porta de baixo aberta)
    lz = M.node('luz', (0, 0.97, -0.05), extras=dict(efeito=dict(tipo='luz', quando='porta_geladeira')))
    emit_box(lz.geo, PLN, (0, 0.975, -0.05), (0.16, 0.012, 0.05), (1.0, 0.98, 0.9))
    # gaveta de legumes (trilho)
    gv = M.node('gaveta_legumes', (0, 0.22, zf - 0.02), extras=dict(anim=dict(tipo='trilho', eixo=[0, 0, 1], min=0.0, max=0.22, dur=0.4, curva='suave',
                estado_inicial=0.0, alca=[0, 0.29, zf - 0.02], rotulo='gaveta', precisa='porta_geladeira')))
    ggv = gv.geo
    rbox(ggv, PLN, (0, 0.22, zf - 0.03), (W - 2 * t - 0.01, 0.15, 0.012), r=0.004, col=(0.78, 0.90, 0.95), uv=1)
    rbox(ggv, PLN, (0, 0.16, zf - 0.22), (W - 2 * t - 0.02, 0.01, 0.38), r=0.002, col=(0.85, 0.93, 0.97), uv=1)
    for s2 in (-1, 1): rbox(ggv, PLN, (s2 * (W / 2 - t - 0.01), 0.21, zf - 0.22), (0.008, 0.1, 0.38), r=0.002, col=(0.85, 0.93, 0.97), uv=1)
    for i in range(4): sphere(ggv, PLN, (-0.16 + i * 0.1, 0.20, zf - 0.18 + (i % 2) * 0.08), 0.04, [(0.35, 0.65, 0.2), (0.9, 0.45, 0.1), (0.85, 0.2, 0.15), (0.35, 0.65, 0.2)][i], seg=10)
    # portas (dobradiça à direita, abrem até 110°), com vedação, prateleiras de porta e produtos
    for nm, y0, y1, lab in (('porta_freezer', ysep + 0.02, H, 'freezer'), ('porta_geladeira', 0.10, ysep - 0.01, 'geladeira')):
        hx = W / 2 - 0.005; hh = y1 - y0; cy = (y0 + y1) / 2
        ang = math.radians(110)
        dn = M.node(nm, (hx, cy, zf), extras=dict(anim=dict(tipo='dobradica', eixo=[0, 1, 0], min=0.0, max=round(ang, 4), dur=0.6, curva='suave',
                    estado_inicial=0.0, alca=[-W / 2 + 0.06, cy, zf + 0.09], rotulo=lab, raio=W, colide_com=['parede', 'movel'])))
        gd = dn.geo
        rbox(gd, PLN, (0, cy, zf + 0.03), (W, hh - 0.006, 0.06), r=0.012, col=WH, uv=1, step=0.25)
        rbox(gd, PLN, (0, cy, zf - 0.004), (W - 0.04, hh - 0.04, 0.012), r=0.006, col=(0.88, 0.90, 0.92), uv=1, step=0.5)   # vedação
        # puxador vertical (barra de alumínio escovado com espaçadores)
        hxp = -W / 2 + 0.06; h0 = cy - hh * 0.3; h1 = cy + hh * 0.3
        gd.tube(CHROME, [V(hxp, h0, zf + 0.085), V(hxp, h1, zf + 0.085)], [0.011, 0.011], sides=12, col=lambda p, tt: STEEL + (1,))
        for yy in (h0, h1): gd.tube(CHROME, [V(hxp, yy, zf + 0.06), V(hxp, yy, zf + 0.085)], [0.008, 0.008], sides=8, col=lambda p, tt: STEEL + (1,))
        if nm == 'porta_geladeira':
            for yy in (0.30, 0.55, 0.80):
                rbox(gd, PLN, (0, yy, zf - 0.04), (W - 0.1, 0.05, 0.06), r=0.006, col=(0.86, 0.93, 0.97), uv=1)
            for i, x in enumerate((-0.18, -0.08, 0.04)):
                gd.lathe(PLN, (x, 0.305, zf - 0.04), [(0, 0), (0.032, 0), (0.034, 0.16), (0.012, 0.22), (0.012, 0.25), (0, 0.25)], sides=14, col=[(0.2, 0.55, 0.3, 1), (0.85, 0.25, 0.2, 1), (0.95, 0.95, 0.95, 1)][i])
            rbox(gd, PLN, (0.15, 0.62, zf - 0.04), (0.07, 0.14, 0.06), r=0.008, col=(0.95, 0.95, 0.92), uv=1, step=1)   # caixa de leite
            for i in range(6): sphere(gd, PLN, (-0.18 + i * 0.045, 0.82, zf - 0.04), 0.019, (0.95, 0.88, 0.78), seg=8, sy=1.25)   # ovos
        else:
            rbox(gd, PLN, (0, y0 + 0.12, zf - 0.04), (W - 0.1, 0.04, 0.05), r=0.006, col=(0.86, 0.93, 0.97), uv=1)
    M.empty('COL_corpo', (0, H / 2, -0.005), extras=dict(shape='box', size=[W, H, D - 0.01], bloqueia=True, camada='movel'))
    M.empty('SURF_topo', (0, H, -0.03), extras=dict(shape='box', size=[W - 0.04, 0, D - 0.1], recebe='objetos'))
    M.empty('IP_usar', (0, 0, D / 2 + 0.55), extras=dict(acao='abrir/fechar', olhar='-Z'))
    M.bake_ao(maxd=0.2, strength=0.45)
    return finish(M)


# ================================================================================================ FOGÃO 4 BOCAS
def fogao():
    W, D, H = 0.56, 0.52, 0.72
    zf = D / 2 - 0.02
    M = G.Model('int_fogao', meta('int_fogao', 'Fogão 4 bocas com forno', 'cozinha', 'eletrodomesticos', 'funcional',
               dict(tipo='estatico', massa=35.0, motivo='eletrodoméstico ancorado'), estados=['desligado', 'ligado'], grade=[1, 1],
               interacoes=[dict(acao='ligar/desligar', ponto='IP_usar'), dict(acao='abrir/fechar', pecas=['porta_forno'])]))
    body = M.node('corpo'); g = body.geo
    INOX = (0.86, 0.87, 0.88); BLK = (0.10, 0.10, 0.11)
    # gabinete em chapas (laterais, fundo, base, tampo e faixa do painel): a frente do forno é aberta, a porta fecha
    for sx in (-1, 1): rbox(g, CHROME, (sx * (W / 2 - 0.006), (H + 0.04) / 2, -0.02), (0.012, H - 0.04, D - 0.04), r=0.004, col=INOX, uv=2, step=0.3)
    rbox(g, CHROME, (0, (H + 0.04) / 2, -D / 2 + 0.006), (W - 0.01, H - 0.04, 0.012), r=0.003, col=INOX, uv=2, step=0.3)
    rbox(g, CHROME, (0, 0.066, -0.02), (W - 0.01, 0.012, D - 0.04), r=0.003, col=INOX, uv=2, step=0.3)
    rbox(g, CHROME, (0, H - 0.06, -0.02), (W - 0.01, 0.10, D - 0.04), r=0.006, col=INOX, uv=2, step=0.3)
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.lathe(PLN, (sx * (W / 2 - 0.05), 0, sz * (D / 2 - 0.08)), [(0, 0), (0.02, 0), (0.022, 0.045), (0.0, 0.045)], sides=12, col=BLK + (1,))
    rbox(g, PLN, (0, 0.03, zf - 0.02), (W - 0.04, 0.05, 0.012), r=0.004, col=BLK, uv=1)          # rodapé
    # mesa (cooktop) preta com 4 queimadores e grades de ferro
    rbox(g, PLN, (0, H - 0.005, -0.02), (W + 0.01, 0.012, D - 0.02), r=0.004, col=(0.07, 0.07, 0.08), uv=1, step=0.4)
    burners = [(-0.13, -0.12, 0.05), (0.13, -0.12, 0.04), (-0.13, 0.10, 0.04), (0.13, 0.10, 0.05)]
    for (bx, bz, br) in burners:
        g.lathe(CHROME, (bx, H, bz), [(0, 0), (br + 0.012, 0), (br + 0.012, 0.008), (br, 0.012), (br * 0.6, 0.016), (0, 0.018)], sides=24, col=(0.55, 0.56, 0.58, 1))
        g.lathe(PLN, (bx, H + 0.018, bz), [(0, 0), (br * 0.55, 0), (br * 0.55, 0.008), (0, 0.01)], sides=18, col=BLK + (1,))
    for gx in (-0.13, 0.13):
        # grade: aro + 4 braços com pés, com espessura
        for gz in (-0.11, 0.10):
            ring = [V(gx + 0.12 * math.cos(a), H + 0.04, gz + 0.11 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 25)]
            g.tube(PLN, ring, [0.006] * 25, sides=6, col=lambda p, tt: (0.13, 0.13, 0.14, 1))
            for a in np.radians([45, 135, 225, 315]):
                p_out = V(gx + 0.12 * math.cos(a), H + 0.04, gz + 0.11 * math.sin(a)); p_in = V(gx + 0.035 * math.cos(a), H + 0.045, gz + 0.035 * math.sin(a))
                g.tube(PLN, [p_out, p_in], [0.006, 0.006], sides=6, col=lambda p, tt: (0.13, 0.13, 0.14, 1))
                g.tube(PLN, [V(p_out[0], H, p_out[2]), p_out], [0.006, 0.006], sides=6, col=lambda p, tt: (0.13, 0.13, 0.14, 1))
    # panela na boca da frente-esquerda (sobre a grade)
    g.lathe(CHROME, (-0.13, H + 0.046, 0.10), [(0, 0), (0.085, 0), (0.09, 0.01), (0.092, 0.10), (0.098, 0.105), (0.095, 0.11), (0.086, 0.10), (0.084, 0.012), (0, 0.012)], sides=28, col=(0.78, 0.79, 0.8, 1))
    g.tube(PLN, [V(-0.03, H + 0.13, 0.10), V(0.08, H + 0.13, 0.10)], [0.009, 0.009], sides=8, col=lambda p, tt: BLK + (1,))
    g.lathe(CHROME, (-0.13, H + 0.155, 0.10), [(0, 0), (0.097, 0), (0.06, 0.02), (0.012, 0.025), (0.012, 0.035), (0, 0.035)], sides=28, col=(0.8, 0.81, 0.82, 1))
    # painel de comandos (faixa frontal superior) e botões que giram
    rbox(g, PLN, (0, H - 0.06, zf + 0.004), (W - 0.02, 0.09, 0.016), r=0.006, col=(0.16, 0.16, 0.17), uv=1)
    for i, kx in enumerate((-0.2, -0.1, 0.0, 0.1, 0.2)):
        nm = 'botao_%d' % i
        kn = M.node(nm, (kx, H - 0.06, zf + 0.012), extras=dict(anim=dict(tipo='dobradica', eixo=[0, 0, 1], min=0.0, max=round(math.radians(-110), 4),
                    dur=0.35, curva='suave', gatilho='ligado', estado_inicial=0.0)))
        gk = kn.geo
        gk.lathe(PLN, (kx, H - 0.06, zf + 0.012), [(0, 0), (0.021, 0), (0.021, 0.02), (0.018, 0.026), (0, 0.026)], sides=20, col=(0.20, 0.20, 0.22, 1)) if False else None
        tmp = Geo(); tmp.lathe(PLN, (0, 0, 0), [(0, 0), (0.021, 0), (0.021, 0.02), (0.018, 0.026), (0, 0.026)], sides=20, col=(0.20, 0.20, 0.22, 1))
        add_xf(gk, tmp, rot_x(math.pi / 2), V(kx, H - 0.06, zf + 0.012))
        rbox(gk, PLN, (kx, H - 0.06 + 0.008, zf + 0.04), (0.005, 0.018, 0.004), r=0.001, col=(0.9, 0.9, 0.9), uv=1, step=1)   # marca do botão
    # chamas (azuis, emissivas): uma coroa por queimador, aparecem só ligado
    fl = M.node('chamas', (0, H + 0.02, 0), extras=dict(efeito=dict(tipo='chama', quando='ligado')))
    gf = fl.geo
    for (bx, bz, br) in burners:
        for k in range(14):
            a = 2 * math.pi * k / 14
            cx_ = bx + math.cos(a) * (br + 0.004); cz_ = bz + math.sin(a) * (br + 0.004)
            out = V(math.cos(a), 0, math.sin(a))
            base = V(cx_, H + 0.014, cz_)
            tip = base + out * 0.012 + V(0, 0.03, 0)
            side = np.cross(out, [0, 1, 0]) * 0.005
            gf.add(PLN, [base - side, base + side, tip], [(0, 0, 0)] * 3, [(0.35, 0.55, 1.0, 1)] * 3, [(0, 0), (1, 0), (0.5, 1)], [(0, 1, 2)])
            gf.add(PLN, [base - side * 0.5 + out * 0.002, base + side * 0.5 + out * 0.002, tip - out * 0.004 - V(0, 0.012, 0)], [(0, 0, 0)] * 3,
                   [(0.85, 0.92, 1.0, 1)] * 3, [(0, 0), (1, 0), (0.5, 1)], [(0, 1, 2)])
    # porta do forno: dobradiça embaixo (eixo X), abre 85° para baixo; visor escuro e puxador
    py0 = 0.08; py1 = H - 0.12
    dn = M.node('porta_forno', (0, py0, zf + 0.01), extras=dict(anim=dict(tipo='dobradica', eixo=[1, 0, 0], min=0.0, max=round(math.radians(85), 4), dur=0.55,
                curva='suave', estado_inicial=0.0, alca=[0, py1 - 0.04, zf + 0.06], rotulo='forno', colide_com=['parede', 'movel'])))
    gd = dn.geo
    rbox(gd, CHROME, (0, (py0 + py1) / 2, zf + 0.025), (W - 0.03, py1 - py0, 0.03), r=0.006, col=INOX, uv=2, step=0.3)
    rbox(gd, PLN, (0, (py0 + py1) / 2 + 0.01, zf + 0.041), (W - 0.14, (py1 - py0) * 0.55, 0.004), r=0.012, col=(0.06, 0.06, 0.07), uv=1)
    rbox(gd, PLN, (0, (py0 + py1) / 2 + 0.01, zf + 0.0435), (W - 0.18, (py1 - py0) * 0.45, 0.001), r=0.01, col=(0.16, 0.17, 0.2), uv=1)
    hy = py1 - 0.04
    gd.tube(CHROME, [V(-0.2, hy, zf + 0.075), V(0.2, hy, zf + 0.075)], [0.009, 0.009], sides=12, col=lambda p, tt: STEEL + (1,))
    for xx in (-0.2, 0.2): gd.tube(CHROME, [V(xx, hy, zf + 0.04), V(xx, hy, zf + 0.075)], [0.007, 0.007], sides=8, col=lambda p, tt: STEEL + (1,))
    # interior do forno (cavidade escura com grade)
    rbox(g, PLN, (0, (py0 + py1) / 2, -0.03), (W - 0.08, py1 - py0 - 0.03, D - 0.12), r=0.01, col=(0.08, 0.08, 0.09), uv=1, step=0.5)
    for xx in np.linspace(-0.2, 0.2, 9): g.tube(CHROME, [V(xx, 0.30, -0.2), V(xx, 0.30, 0.2)], [0.003, 0.003], sides=6, col=lambda p, tt: STEEL + (1,))
    M.empty('COL_corpo', (0, H / 2, -0.01), extras=dict(shape='box', size=[W, H, D - 0.02], bloqueia=True, camada='movel'))
    M.empty('SURF_mesa', (0, H + 0.04, -0.01), extras=dict(shape='box', size=[W - 0.04, 0, D - 0.06], recebe='panelas (sobre as grades)'))
    M.empty('IP_usar', (0, 0, D / 2 + 0.42), extras=dict(acao='ligar', rotulo_ligar='Ligar fogão', rotulo_desligar='Desligar fogão', olhar='-Z',
            estados=['desligado', 'ligado'], cancelar='tocar de novo desliga; sair de perto não deixa o fogão ligado sem querer? (não: o estado fica salvo)'))
    M.bake_ao(maxd=0.15, strength=0.45)
    return finish(M)


# ================================================================================================ PIA DE COZINHA
def pia():
    W, D, H = 0.90, 0.48, 0.74
    zf = D / 2 - 0.02
    M = G.Model('int_pia', meta('int_pia', 'Pia de cozinha com gabinete', 'cozinha', 'bancadas', 'funcional',
               dict(tipo='estatico', massa=45.0, motivo='bancada ancorada'), estados=['torneira fechada', 'aberta'], grade=[1, 1],
               interacoes=[dict(acao='abrir/fechar torneira', ponto='IP_usar'), dict(acao='abrir/fechar', pecas=['porta_E', 'porta_D'])]))
    body = M.node('corpo'); g = body.geo
    WH = (0.93, 0.92, 0.90)
    # gabinete branco com rodapé recuado
    for sx in (-1, 1): rbox(g, PLN, (sx * (W / 2 - 0.009), (H - 0.03) / 2, -0.01), (0.018, H - 0.03, D - 0.04), r=0.003, col=WH, uv=1)
    rbox(g, PLN, (0, 0.09, -0.01), (W - 0.03, 0.018, D - 0.05), r=0.003, col=WH, uv=1)
    rbox(g, PLN, (0, 0.04, zf - 0.06), (W - 0.03, 0.08, 0.015), r=0.003, col=(0.3, 0.3, 0.32), uv=1)
    rbox(g, PLN, (0, (H - 0.03) / 2, -D / 2 + 0.01), (W - 0.03, H - 0.05, 0.01), r=0.002, col=(0.88, 0.87, 0.85), uv=1)
    rbox(g, PLN, (0, 0.33, -0.02), (0.016, 0.48, D - 0.06), r=0.002, col=WH, uv=1)
    # sifão e tubo (visíveis com a porta aberta)
    g.tube(CHROME, [V(0, H - 0.2, -0.05), V(0, 0.42, -0.05), V(0, 0.36, 0.0), V(0, 0.42, 0.05), V(0, 0.44, -0.2)], [0.018] * 5, sides=10, col=lambda p, tt: (0.75, 0.76, 0.78, 1))
    # produtos de limpeza dentro
    g.lathe(PLN, (-0.25, 0.1, -0.05), [(0, 0), (0.04, 0), (0.042, 0.18), (0.015, 0.24), (0.015, 0.27), (0, 0.27)], sides=14, col=(0.25, 0.55, 0.85, 1))
    g.lathe(PLN, (-0.15, 0.1, -0.02), [(0, 0), (0.035, 0), (0.036, 0.15), (0.012, 0.2), (0, 0.2)], sides=14, col=(0.95, 0.85, 0.25, 1))
    rbox(g, PLN, (0.24, 0.13, -0.04), (0.2, 0.06, 0.16), r=0.01, col=(0.85, 0.35, 0.35), uv=1)
    # tampo de pedra (granito escuro) com cuba de inox rebaixada
    top = H; tth = 0.03
    stone = (0.32, 0.31, 0.30)
    bw, bd, bdep = 0.46, 0.32, 0.17
    bx0, bz0 = 0.0, 0.0
    # tampo em 4 peças em volta do furo da cuba
    rbox(g, PLN, (0, top + tth / 2, -D / 2 + (D / 2 - bd / 2 + 0.01) / 2 - 0.005), (W + 0.02, tth, (D / 2 - bd / 2) + 0.01), r=0.004, col=stone, uv=1, step=0.4)
    rbox(g, PLN, (0, top + tth / 2, D / 2 - (D / 2 - bd / 2 + 0.03) / 2 + 0.02), (W + 0.02, tth, (D / 2 - bd / 2) + 0.03), r=0.004, col=stone, uv=1, step=0.4)
    for sx in (-1, 1):
        rbox(g, PLN, (sx * (bw / 2 + (W / 2 - bw / 2 + 0.01) / 2), top + tth / 2, 0), ((W / 2 - bw / 2) + 0.01, tth, bd + 0.01), r=0.003, col=stone, uv=1, step=0.4)
    # cuba: paredes e fundo com espessura, borda e ralo
    cuba = (0.80, 0.81, 0.83)
    yb = top + tth - bdep
    rbox(g, CHROME, (0, yb + 0.004, 0), (bw - 0.004, 0.008, bd - 0.004), r=0.02, col=cuba, uv=2, step=0.2)
    for sx in (-1, 1): rbox(g, CHROME, (sx * (bw / 2 - 0.004), yb + bdep / 2, 0), (0.008, bdep, bd), r=0.003, col=cuba, uv=2)
    for sz in (-1, 1): rbox(g, CHROME, (0, yb + bdep / 2, sz * (bd / 2 - 0.004)), (bw, bdep, 0.008), r=0.003, col=cuba, uv=2)
    g.lathe(CHROME, (0, yb + 0.009, 0), [(0, 0.0), (0.035, 0.0), (0.04, 0.003), (0.0, 0.003)], sides=20, col=(0.55, 0.56, 0.58, 1))
    for k in range(8):
        a = k * math.pi / 4; g.add(PLN, [V(0, yb + 0.0125, 0), V(0.025 * math.cos(a), yb + 0.0125, 0.025 * math.sin(a)), V(0.025 * math.cos(a + 0.2), yb + 0.0125, 0.025 * math.sin(a + 0.2))],
                                     [(0, 1, 0)] * 3, [(0.1, 0.1, 0.1, 1)] * 3, [(0, 0)] * 3, [(0, 2, 1)])
    # rodabanca
    rbox(g, PLN, (0, top + tth + 0.04, -D / 2 + 0.01), (W + 0.02, 0.08, 0.02), r=0.004, col=stone, uv=1, step=0.4)
    # torneira bica alta (gooseneck) cromada
    tx, tz = 0.0, -bd / 2 - 0.04
    g.lathe(CHROME, (tx, top + tth, tz), [(0, 0), (0.028, 0), (0.028, 0.012), (0.016, 0.02), (0.016, 0.07)], sides=16, col=STEEL + (1,))
    pts = [V(tx, top + tth + 0.06, tz)]
    for a in np.linspace(0, math.pi * 0.95, 14):
        pts.append(V(tx, top + tth + 0.06 + 0.24 + math.sin(a) * 0.08, tz + 0.09 - math.cos(a) * 0.09))
    pts = [pts[0], V(tx, top + tth + 0.30, tz)] + pts[2:]
    g.tube(CHROME, pts, [0.012] * len(pts), sides=12, col=lambda p, tt: STEEL + (1,))
    spout = pts[-1]
    g.lathe(CHROME, (spout[0], spout[1] - 0.02, spout[2]), [(0.0, 0), (0.014, 0), (0.014, 0.02)], sides=12, col=(0.6, 0.6, 0.62, 1))
    # alavanca (gira ao abrir a água)
    lv = M.node('alavanca', (tx + 0.03, top + tth + 0.07, tz), extras=dict(anim=dict(tipo='dobradica', eixo=[0, 0, 1], min=0.0, max=round(math.radians(-55), 4),
                dur=0.3, curva='suave', gatilho='ligado', estado_inicial=0.0)))
    lv.geo.tube(CHROME, [V(tx + 0.03, top + tth + 0.07, tz), V(tx + 0.10, top + tth + 0.075, tz)], [0.007, 0.006], sides=10, col=lambda p, tt: STEEL + (1,))
    sphere(lv.geo, CHROME, (tx + 0.03, top + tth + 0.07, tz), 0.014, STEEL, seg=10)
    # água (cilindro emissivo azul-claro da bica até o ralo; aparece só aberta) + respingo no fundo
    ag = M.node('agua', (spout[0], spout[1] - 0.02, spout[2]), extras=dict(efeito=dict(tipo='agua', quando='ligado')))
    ga = ag.geo
    ytop_ = spout[1] - 0.02; ybot = yb + 0.012
    tmp = Geo(); tmp.tube(PLN, [V(spout[0], ytop_, spout[2]), V(spout[0], (ytop_ + ybot) / 2, spout[2]), V(spout[0], ybot, spout[2])], [0.0065, 0.0055, 0.006], sides=10,
                          col=lambda p, tt: (0.75, 0.88, 1.0, 1), vscale=6)
    for k, P, N, C, UV, T in tmp.arrays(): ga.add(k, P, N * 0, C, UV, T)
    for k in range(10):
        a = k * math.pi / 5
        b0 = V(spout[0], ybot, spout[2]); b1 = b0 + V(0.035 * math.cos(a), 0.012, 0.035 * math.sin(a))
        ga.add(PLN, [b0 + V(-0.003, 0, 0), b0 + V(0.003, 0, 0), b1], [(0, 0, 0)] * 3, [(0.85, 0.93, 1.0, 1)] * 3, [(0, 0)] * 3, [(0, 1, 2)])
    # portas do gabinete (dobradiças nas laterais)
    ph = H - 0.14; py = 0.10 + ph / 2
    for sx, nm in ((-1, 'porta_E'), (1, 'porta_D')):
        hx = sx * (W / 2 - 0.004); pw = W / 2 - 0.012; cx = sx * (0.004 + pw / 2)
        ang = math.radians(100) * (-1 if sx < 0 else 1)
        dn = M.node(nm, (hx, py, zf), extras=dict(anim=dict(tipo='dobradica', eixo=[0, 1, 0], min=0.0, max=round(ang, 4), dur=0.5, curva='suave', estado_inicial=0.0,
                    alca=[cx - sx * (pw / 2 - 0.05), py + 0.2, zf + 0.04], rotulo='porta', colide_com=['parede', 'movel'])))
        gd = dn.geo
        rbox(gd, PLN, (cx, py, zf + 0.009), (pw, ph, 0.018), r=0.004, col=WH, uv=1, step=0.2)
        kx = cx - sx * (pw / 2 - 0.05)
        gd.tube(CHROME, [V(kx, py + 0.12, zf + 0.035), V(kx, py + 0.28, zf + 0.035)], [0.006, 0.006], sides=10, col=lambda p, tt: STEEL + (1,))
        for yy in (py + 0.12, py + 0.28): gd.tube(CHROME, [V(kx, yy, zf + 0.018), V(kx, yy, zf + 0.035)], [0.005, 0.005], sides=8, col=lambda p, tt: STEEL + (1,))
    M.empty('COL_corpo', (0, (H + tth) / 2, 0), extras=dict(shape='box', size=[W + 0.02, H + tth, D], bloqueia=True, camada='movel'))
    M.empty('SURF_bancada', (0, H + tth, 0), extras=dict(shape='box', size=[W, 0, D], recebe='objetos (fora da cuba)'))
    M.empty('IP_usar', (0, 0, D / 2 + 0.40), extras=dict(acao='ligar', rotulo_ligar='Abrir torneira', rotulo_desligar='Fechar torneira', olhar='-Z',
            estados=['fechada', 'aberta']))
    M.bake_ao(maxd=0.18, strength=0.5)
    return finish(M)


ALL = [sofa3, cama, geladeira, fogao, pia]

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/glb_l2'
    os.makedirs(out, exist_ok=True)
    rep = {}
    for f in ALL:
        M = f(); fn = os.path.join(out, M.id + '.glb'); n = M.write_glb(fn)
        err, warn, info = G.verify(fn)
        rep[M.id] = dict(erros=err, avisos=warn, info=info)
        print('%-18s %7d bytes %6d vért. %6d tri. erros=%d avisos=%d %s' % (M.id, n, info['vertices'], info['triangulos'], len(err), len(warn), M.meta['dimensoes']))
        for e in err: print('   ERRO:', e)
        for w in warn: print('   aviso:', w)
    json.dump(rep, open(os.path.join(out, 'verificacao_lote2.json'), 'w'), ensure_ascii=False, indent=1)
