"""Cidade 6 - predios das profissoes, versao 2.

Cada predio entra na FILEIRA de predios de uma quadra do centro (sem praca vazia em volta), de frente para a rua
(de preferencia uma avenida), cada um num quadrante diferente do centro. Fachada com volume de verdade:
embasamento de pedra, pilastras entre os vaos, vitrines com caixilho e bandeira, porta dupla recuada com soleira,
toldos, faixa de letreiro com LETRAS EM RELEVO (fonte de pixels), placa de bandeira, arandelas, janelas dos andares
com moldura, peitoril e verga, cintas entre andares, cornija, platibanda com rufo e casa de maquinas. Cada
profissao tem uma assinatura propria (torre de treino dos bombeiros, portico do forum, coroa da sede, grua da
construtora, etc). Dentro: salas planejadas, moveis encostados nas paredes e em fileiras, sempre dentro da sala.
Sem superficies coplanares (nada pisca): toda placa tem folga de pelo menos 1 cm.
"""
import math, unicodedata
from mesh import Frame, shade
from roads6 import Y_WALK
import jobs6
from jobs6 import J, GLOW, WOOD, WOOD_L, STEEL, DARK, gondola, cart, fire_truck, garbage_truck, moto

Y0 = jobs6.Y0
HH = jobs6.HH
FH = 3.4                                 # altura dos andares de cima

# id -> (letreiro, estilo, andares, largura, fundo, piso, parede, detalhe)
SPEC = {
    'repositor':  ('SUPERBOM', 'loja', 1, 36, 26, 'ceramica', (238, 236, 230), (60, 150, 70)),
    'atendente':  ('LANCHONETE DO ZE', 'loja', 2, 18, 16, 'ceramica', (250, 240, 214), (200, 50, 40)),
    'diarista':   ('BRILHO LIMPEZA', 'loja', 2, 16, 16, 'ceramica', (226, 240, 246), (40, 150, 190)),
    'frentista':  ('POSTO ROTA SUL', 'loja', 1, 22, 18, 'ceramica', (240, 242, 244), (30, 100, 180)),
    'medico':     ('HOSPITAL SANTA CLARA', 'inst', 5, 40, 28, 'ceramica', (244, 246, 248), (200, 40, 50)),
    'entregador': ('EXPRESSO JA', 'tijolo', 2, 24, 20, 'concreto', (176, 96, 70), (240, 140, 40)),
    'lixeiro':    ('CENTRAL DE COLETA', 'tijolo', 2, 30, 22, 'concreto', (150, 96, 74), (70, 150, 70)),
    'mecanico':   ('OFICINA DO TONINHO', 'tijolo', 1, 26, 20, 'concreto', (160, 92, 70), (230, 170, 30)),
    'bombeiro':   ('BOMBEIROS', 'tijolo', 2, 30, 24, 'concreto', (178, 70, 56), (200, 40, 36)),
    'policial':   ('DELEGACIA', 'inst', 3, 26, 20, 'ceramica', (232, 234, 238), (30, 60, 140)),
    'enfermeiro': ('CLINICA AURORA', 'inst', 3, 22, 18, 'ceramica', (244, 246, 244), (30, 150, 130)),
    'professor':  ('ESCOLA PRIMAVERA', 'inst', 3, 32, 22, 'madeira', (244, 226, 180), (230, 120, 40)),
    'juiz':       ('FORUM DA COMARCA', 'classico', 3, 30, 24, 'pedra', (226, 216, 196), (150, 120, 70)),
    'advogado':   ('ALMEIDA & PRADO', 'classico', 4, 18, 16, 'madeira', (214, 200, 178), (40, 80, 60)),
    'secretario': ('ESCRITORIO CENTRAL', 'vidro', 6, 22, 18, 'madeira', (220, 224, 228), (60, 90, 150)),
    'engenheiro': ('PILAR CONSTRUTORA', 'vidro', 5, 24, 18, 'madeira', (210, 206, 198), (230, 170, 30)),
    'programador': ('NOVA TECH', 'vidro', 7, 26, 20, 'madeira', (230, 232, 238), (120, 70, 210)),
    'empresario': ('GRUPO ATLAS', 'vidro', 12, 28, 22, 'pedra', (40, 46, 56), (200, 170, 90)),
}
ORDER = ['repositor', 'policial', 'bombeiro', 'juiz', 'empresario', 'programador', 'professor', 'enfermeiro', 'engenheiro',
         'advogado', 'secretario', 'mecanico', 'entregador', 'lixeiro', 'atendente', 'diarista', 'frentista']
NAMES = {k: v[0] for k, v in jobs6.JOBS.items()}

# ---------------------------------------------------------------- fonte de pixels 5x7 (letreiros em relevo)
GL = {
    'A': '01110 10001 10001 11111 10001 10001 10001', 'B': '11110 10001 10001 11110 10001 10001 11110',
    'C': '01110 10001 10000 10000 10000 10001 01110', 'D': '11110 10001 10001 10001 10001 10001 11110',
    'E': '11111 10000 10000 11110 10000 10000 11111', 'F': '11111 10000 10000 11110 10000 10000 10000',
    'G': '01110 10001 10000 10111 10001 10001 01111', 'H': '10001 10001 10001 11111 10001 10001 10001',
    'I': '01110 00100 00100 00100 00100 00100 01110', 'J': '00111 00010 00010 00010 00010 10010 01100',
    'K': '10001 10010 10100 11000 10100 10010 10001', 'L': '10000 10000 10000 10000 10000 10000 11111',
    'M': '10001 11011 10101 10101 10001 10001 10001', 'N': '10001 11001 10101 10011 10001 10001 10001',
    'O': '01110 10001 10001 10001 10001 10001 01110', 'P': '11110 10001 10001 11110 10000 10000 10000',
    'Q': '01110 10001 10001 10001 10101 10010 01101', 'R': '11110 10001 10001 11110 10100 10010 10001',
    'S': '01111 10000 10000 01110 00001 00001 11110', 'T': '11111 00100 00100 00100 00100 00100 00100',
    'U': '10001 10001 10001 10001 10001 10001 01110', 'V': '10001 10001 10001 10001 10001 01010 00100',
    'W': '10001 10001 10001 10101 10101 10101 01010', 'X': '10001 10001 01010 00100 01010 10001 10001',
    'Y': '10001 10001 01010 00100 00100 00100 00100', 'Z': '11111 00001 00010 00100 01000 10000 11111',
    '&': '01100 10010 10100 01000 10101 10010 01101', ' ': '00000 00000 00000 00000 00000 00000 00000',
}


def sign_text(j, text, uc, v, y, height, col, depth=0.06, maxw=None):
    """escreve o texto com letras de blocos (relevo) centradas em uc, na face v (olhando para -v), base em y"""
    t = ''.join(c for c in unicodedata.normalize('NFD', text.upper()) if unicodedata.category(c) != 'Mn')
    px = height / 7.0
    width = len(t) * 6 * px - px
    if maxw and width > maxw: px = maxw / (len(t) * 6 - 1); width = maxw
    u = uc + width / 2                       # quem olha de fora (para +v) le da direita (u maior) para a esquerda
    for ch in t:
        g = GL.get(ch, GL[' ']).split()
        for row, bits in enumerate(g):
            yy = y + (6 - row) * px
            k = 0
            while k < 5:
                if bits[k] == '1':
                    k2 = k
                    while k2 + 1 < 5 and bits[k2 + 1] == '1': k2 += 1
                    j.bx(u - (k2 + 1) * px, u - k * px, v - depth, v, yy, yy + px, col, 'liso')
                    k = k2 + 1
                else: k += 1
        u -= 6 * px


# ---------------------------------------------------------------- fachada
def win(j, u, v, y, w, h, frame=(240, 238, 232), deep=0.12, sill=True, glass_mat='janela'):
    """janela na face v (olha para -v): vidro recuado, moldura, peitoril e verga"""
    j.bx(u - w / 2, u + w / 2, v - 0.005, v + 0.01, y, y + h, (255, 255, 255), glass_mat)
    for (a, b, c, e) in ((u - w / 2 - 0.1, u - w / 2, y - 0.02, y + h + 0.02), (u + w / 2, u + w / 2 + 0.1, y - 0.02, y + h + 0.02), (u - w / 2, u + w / 2, y + h, y + h + 0.1)):
        j.bx(a, b, v - deep, v + 0.02, c, e, frame, 'liso')
    j.bx(u - 0.02, u + 0.02, v - 0.04, v + 0.01, y, y + h, frame, 'liso')                      # montante
    if sill: j.bx(u - w / 2 - 0.15, u + w / 2 + 0.15, v - 0.2, v + 0.02, y - 0.1, y, shade(frame, -10), 'concreto')


def ground_floor(j, w, d, spec, door_u, ops_extra=None):
    """terreo: paredes com vitrines/portas (frente) e janelas (fundos), pilastras e embasamento; devolve aberturas"""
    _, style, floors, _, _, _, wall, acc = spec
    nb = max(3, int(round(w / 3.8))); bw = w / nb
    ops = list(ops_extra or [])
    taken = [(a, b) for (a, b, _, _, _) in ops]
    if not any(a <= door_u <= b for (a, b) in taken): ops.append((door_u - 1.1, door_u + 1.1, Y0, Y0 + 2.8, 'porta')); taken.append((door_u - 1.1, door_u + 1.1))
    for k in range(nb):
        a, b = k * bw + 0.45, (k + 1) * bw - 0.45
        if b - a < 1.0 or any(not (b < x0 - 0.3 or a > x1 + 0.3) for (x0, x1) in taken): continue
        ops.append((a, b, Y0 + 0.45, Y0 + 3.2, 'vitrine' if style in ('loja', 'posto') else 'janela'))
    mat = 'tijolo' if style == 'tijolo' else 'reboco'
    j.wall_v(0, w, 0.0, Y0, Y0 + HH, 0.3, wall, mat, ops)
    back = [(a, a + 1.4, Y0 + 1.3, Y0 + 2.7, 'janela') for a in [1.5 + q * 4.0 for q in range(int((w - 3) / 4.0))]]
    j.wall_v(0, w, d, Y0, Y0 + HH, 0.3, wall, mat, back)
    for uu in (0.0, w): j.wall_side(0.0, d, uu, [], wall)
    # pilastras e embasamento de pedra
    clad = shade(acc, -40) if style == 'vidro' else ((206, 198, 184) if style != 'tijolo' else (120, 110, 104))
    for k in range(nb + 1):
        uu = k * bw
        if any(x0 - 0.2 < uu < x1 + 0.2 for (x0, x1) in taken if x1 - x0 > 3.0): continue
        j.bx(uu - 0.32, uu + 0.32, -0.22, 0.16, Y_WALK, Y0 + HH + 0.02, clad, 'pedra' if style != 'vidro' else 'metal')
    j.bx(-0.05, w + 0.05, -0.08, 0.16, Y_WALK - 0.05, Y0 + 0.42, (150, 144, 136), 'pedra', False)
    return nb, bw


def upper(j, w, d, spec):
    """andares de cima: volume com janelas de verdade nas 4 faces, cintas, cornija, platibanda e cobertura"""
    _, style, floors, _, _, _, wall, acc = spec
    ybase = Y0 + HH + 0.6                           # depois da faixa do letreiro
    top = ybase + (floors - 1) * FH if floors > 1 else Y0 + HH + 0.9
    mat = {'tijolo': 'tijolo', 'classico': 'reboco', 'inst': 'reboco', 'loja': 'reboco', 'posto': 'reboco', 'vidro': 'concreto'}[style]
    j.B.box(j.F, 0.0, w, 0.0, d, Y0 + HH, top, wall, mat, False)
    if floors > 1:
        nb = max(2, int(round(w / 3.4))); bw = w / nb
        nd = max(2, int(round(d / 3.4))); bd = d / nd
        for f in range(floors - 1):
            y = ybase + f * FH
            j.bx(-0.06, w + 0.06, -0.06, d + 0.06, y - 0.12, y + 0.0, shade(wall, -14), 'concreto', False)        # cinta
            if style == 'vidro':
                continue
            for k in range(nb): win(j, (k + 0.5) * bw, 0.0, y + 0.8, min(1.8, bw - 0.9), 1.7, (246, 244, 238) if style != 'tijolo' else (230, 226, 216))
            # fundos e laterais: janelas simples (moldura so) em frames girados
            for (G, L_, n_) in ((j.sub(w, d, 2), w, nb), (j.sub(0.0, d, 3), d, nd), (j.sub(w, 0.0, 1), d, nd)):
                jj = J(j.L, G); bb = L_ / n_
                for k in range(n_): win(jj, (k + 0.5) * bb, 0.0, y + 0.8, min(1.5, bb - 1.0), 1.6, (236, 234, 228), 0.08, False)
        if style == 'vidro':
            # pele de vidro: painel continuo e grade de montantes/spandrels na frente e nas laterais
            for (G, L_) in ((j.F, w), (j.sub(w, d, 2), w)):
                jj = J(j.L, G)
                jj.bx(0.2, L_ - 0.2, -0.02, 0.0, Y0 + HH + 0.6, top - 0.3, (255, 255, 255), 'escritorio')
                q = 0.2
                while q <= L_ - 0.19: jj.bx(q - 0.05, q + 0.05, -0.12, -0.02, Y0 + HH + 0.6, top - 0.2, shade(acc, -50), 'metal'); q += 1.6
                for f in range(floors):
                    yy = Y0 + HH + 0.6 + f * FH
                    if yy < top - 0.3: jj.bx(0.15, L_ - 0.15, -0.14, -0.02, yy - 0.1, yy + 0.25, shade(wall, 20), 'metal')
    # cornija, platibanda com rufo, cobertura sem coplanar
    j.bx(-0.35, w + 0.35, -0.35, d + 0.35, top, top + 0.28, shade(wall, 18) if style != 'vidro' else shade(acc, -30), 'concreto')
    if style == 'classico':
        q = 0.2
        while q < w - 0.1: j.bx(q, q + 0.16, -0.3, -0.05, top - 0.16, top, shade(wall, 22), 'concreto'); q += 0.42      # denticulos
    for (a, b, c, e) in ((-0.2, w + 0.2, -0.2, 0.15), (-0.2, w + 0.2, d - 0.15, d + 0.2), (-0.2, 0.15, 0.15, d - 0.15), (w - 0.15, w + 0.2, 0.15, d - 0.15)):
        j.bx(a, b, c, e, top + 0.28, top + 1.1, shade(wall, -6), 'concreto')
        j.bx(a - 0.05, b + 0.05, c - 0.05, e + 0.05, top + 1.1, top + 1.18, (210, 212, 216), 'metal')
    j.bx(0.15, w - 0.15, 0.15, d - 0.15, top + 0.28, top + 0.32, (176, 178, 182), 'concreto')
    r = j.r
    j.bx(w * 0.15, w * 0.15 + 3.0, d * 0.55, d * 0.55 + 2.4, top + 0.32, top + 2.6, shade(wall, -10), 'concreto')     # casa de maquinas
    for k in range(r.randint(2, 4)):
        ua = r.uniform(w * 0.4, w - 3.0); va = r.uniform(1.5, d - 3.0)
        j.bx(ua, ua + 1.6, va, va + 1.1, top + 0.32, top + 1.3, (206, 208, 212), 'metal')
        j.cyl(ua + 0.8, va + 0.55, 0.38, top + 1.3, top + 1.36, (90, 94, 100), 'metal', 12)
    return top


def storefront(j, w, nb, bw, spec, door_u):
    """faixa do letreiro com letras em relevo, toldos, marquise da porta, arandelas e placa de bandeira"""
    sign, style, floors, _, _, _, wall, acc = spec
    yb = Y0 + HH - 0.15
    band = shade(acc, -35) if style in ('loja', 'posto') else (shade(wall, -45) if style != 'vidro' else (30, 34, 40))
    j.bx(0.0, w, -0.42, 0.0, yb, yb + 0.85, band, 'liso')
    j.bx(-0.05, w + 0.05, -0.5, 0.0, yb + 0.85, yb + 0.95, shade(band, 30), 'metal')
    sign_text(j, sign, w / 2, -0.42, yb + 0.14, 0.58, (255, 250, 236) if style != 'classico' else (232, 200, 120), 0.07, w - 2.0)
    # logo redondo do lado do letreiro
    G = j.sub(1.2, -0.43, 0); j.M.m('liso'); x, z = G.xz(0, 0)
    j.bx(0.55, 1.85, -0.5, -0.43, yb + 0.12, yb + 0.72, acc, 'liso')
    j.bx(0.8, 1.6, -0.52, -0.5, yb + 0.25, yb + 0.6, (255, 255, 255), 'liso')
    if style in ('loja', 'posto'):
        for k in range(nb):
            a, b = k * bw + 0.35, (k + 1) * bw - 0.35
            if a < door_u < b: continue
            y0 = Y0 + 3.3
            j.M.m('liso'); stripes = 6
            for s_ in range(stripes):
                ua = a + (b - a) * s_ / stripes; ub = a + (b - a) * (s_ + 1) / stripes
                col = acc if s_ % 2 == 0 else (250, 250, 246)
                j.M.quad(j.F.p(ua, -0.45, y0 + 0.5), j.F.p(ub, -0.45, y0 + 0.5), j.F.p(ub, -1.6, y0), j.F.p(ua, -1.6, y0), col, (0, 0.8, -0.6))
                j.M.quad(j.F.p(ua, -1.6, y0), j.F.p(ub, -1.6, y0), j.F.p(ub, -1.6, y0 - 0.25), j.F.p(ua, -1.6, y0 - 0.25), col, (0, 0, -1))
    # marquise da porta com forro aceso
    j.bx(door_u - 2.0, door_u + 2.0, -1.9, 0.0, Y0 + 3.0, Y0 + 3.18, (54, 58, 64), 'metal')
    j.M.m('liso'); j.M.poly([j.F.p(door_u - 1.8, -1.75, Y0 + 2.99), j.F.p(door_u + 1.8, -1.75, Y0 + 2.99), j.F.p(door_u + 1.8, -0.2, Y0 + 2.99), j.F.p(door_u - 1.8, -0.2, Y0 + 2.99)], GLOW, (0, -1, 0))
    for s_ in (-1, 1):
        j.bx(door_u + s_ * 1.4 - 0.4, door_u + s_ * 1.4 + 0.4, -0.06, -0.03, Y0, Y0 + 2.8, (170, 200, 214), 'vidro')       # folhas abertas
        j.bx(door_u + s_ * 2.0 - 0.06, door_u + s_ * 2.0 + 0.06, -2.0, -1.88, Y0 + 0.05, Y0 + 3.0, (54, 58, 64), 'metal')
    j.bx(door_u - 1.2, door_u + 1.2, -1.2, 0.2, Y0 - 0.03, Y0 - 0.005, (120, 116, 110), 'liso')                         # capacho
    # arandelas entre os vaos
    for k in range(1, nb):
        uu = k * bw
        if abs(uu - door_u) < 2.2: continue
        j.bx(uu - 0.1, uu + 0.1, -0.32, -0.22, Y0 + 2.4, Y0 + 2.7, DARK, 'metal')
        j.bx(uu - 0.08, uu + 0.08, -0.36, -0.32, Y0 + 2.45, Y0 + 2.65, GLOW, 'liso')
    # placa de bandeira (perpendicular a fachada)
    G = j.sub(w - 0.9, -0.3, 1); jj = J(j.L, G)
    jj.bx(-0.05, 0.05, 0.0, 0.9, Y0 + 3.6, Y0 + 3.66, DARK, 'metal')
    jj.bx(0.15, 1.05, -0.04, 0.04, Y0 + 2.6, Y0 + 3.55, acc, 'liso')
    jj.bx(0.3, 0.9, -0.05, 0.05, Y0 + 2.8, Y0 + 3.35, (255, 255, 255), 'liso')


def signature(j, jid, w, d, top, spec, door_u):
    """o detalhe que faz cada predio unico"""
    _, style, floors, _, _, _, wall, acc = spec
    r = j.r
    if jid == 'bombeiro':
        tu = w - 3.0                                                          # torre de treino com janelas e sirene
        j.B.box(j.F, tu - 2.2, tu + 2.2, d - 4.6, d - 0.2, top, top + 9.0, wall, 'tijolo', True)
        for f in range(3): win(j, tu, d - 4.6, top + 1.2 + f * 2.6, 1.0, 1.3, (240, 240, 236))
        j.cyl(tu, d - 2.4, 0.35, top + 9.0, top + 9.6, (220, 30, 30), 'liso', 10)
        sign_text(j, '193', 3.2, -0.43, Y0 + HH - 0.02, 0.4, (255, 220, 60), 0.05)
    elif jid == 'policial':
        for s_ in (-1, 1):                                                    # luminarias azuis e mastro
            j.bx(door_u + s_ * 2.4 - 0.15, door_u + s_ * 2.4 + 0.15, -0.3, -0.05, Y0 + 2.2, Y0 + 2.8, (40, 90, 220), 'liso')
        x, z = j.F.xz(1.0, -1.5); j.cyl(1.0, -1.5, 0.06, Y_WALK, Y_WALK + 9.0, (220, 220, 220), 'metal', 8)
        G = j.sub(1.0, -1.5, 0); J(j.L, G).bx(0.06, 1.6, -0.01, 0.01, Y_WALK + 7.8, Y_WALK + 8.8, (40, 140, 70), 'liso')
        j.bx(0, w, -0.2, 0.0, Y0 + HH + 0.62, Y0 + HH + 0.92, (30, 60, 140), 'liso')
    elif jid == 'juiz':
        # portico com 4 colunas, frontao e escadaria
        pu0, pu1 = door_u - 5.0, door_u + 5.0
        for k in range(5): j.bx(pu0 - 0.5 - k * 0.1, pu1 + 0.5 + k * 0.1, -3.6 + k * 0.5, -3.1 + k * 0.5 if k < 4 else 0.0, Y_WALK, Y0 - 0.12 * (4 - k) - 0.01, (220, 214, 200), 'pedra')
        for k in range(4):
            cu = pu0 + (pu1 - pu0) * k / 3
            j.cyl(cu, -2.4, 0.42, Y0, Y0 + 0.3, (236, 230, 216), 'pedra', 14); j.cyl(cu, -2.4, 0.34, Y0 + 0.3, Y0 + 6.6, (240, 236, 224), 'concreto', 14, False, 0.3)
            j.bx(cu - 0.5, cu + 0.5, -2.9, -1.9, Y0 + 6.6, Y0 + 6.9, (236, 230, 216), 'concreto'); j.solid(cu - 0.4, cu + 0.4, -2.8, -2.0)
        j.bx(pu0 - 0.8, pu1 + 0.8, -3.2, 0.0, Y0 + 6.9, Y0 + 7.6, (236, 230, 216), 'concreto')
        j.M.m('reboco'); j.M.tri(j.F.p(pu0 - 0.8, -3.2, Y0 + 7.6), j.F.p(pu1 + 0.8, -3.2, Y0 + 7.6), j.F.p(door_u, -3.2, Y0 + 9.6), (232, 224, 206), (j.F.vx * -1, 0, j.F.vz * -1))
        j.M.m('telha'); j.M.quad(j.F.p(pu0 - 1.0, -3.4, Y0 + 7.55), j.F.p(door_u, -3.4, Y0 + 9.75), j.F.p(door_u, 0.0, Y0 + 9.75), j.F.p(pu0 - 1.0, 0.0, Y0 + 7.55), (150, 150, 146), None)
        j.M.quad(j.F.p(door_u, -3.4, Y0 + 9.75), j.F.p(pu1 + 1.0, -3.4, Y0 + 7.55), j.F.p(pu1 + 1.0, 0.0, Y0 + 7.55), j.F.p(door_u, 0.0, Y0 + 9.75), (150, 150, 146), None)
        j.ball(door_u, -3.25, Y0 + 8.3, 0.5, (200, 170, 80), 'metal')                # brasao/balanca
    elif jid == 'empresario':
        # coroa iluminada e logo no topo; marquise de vidro
        j.bx(1.0, w - 1.0, 1.0, d - 1.0, top + 1.18, top + 4.5, (30, 34, 40), 'metal', False)
        for k in range(int((w - 2) / 1.2)): j.bx(1.0 + k * 1.2, 1.1 + k * 1.2, 0.9, 1.0, top + 1.2, top + 4.5, GLOW, 'liso')
        sign_text(j, 'ATLAS', w / 2, 0.9, top + 2.1, 1.6, (230, 200, 120), 0.1)
        j.bx(door_u - 4.0, door_u + 4.0, -3.5, 0.0, Y0 + 3.6, Y0 + 3.75, (170, 200, 214), 'vidro')
        for s_ in (-1, 1): j.cyl(door_u + s_ * 3.6, -3.2, 0.12, Y_WALK, Y0 + 3.6, (200, 202, 206), 'metal', 8)
    elif jid == 'programador':
        # terraco com jardim e pergolado no topo, aletas coloridas
        for k in range(int(w / 2.2)): j.bx(0.6 + k * 2.2, 0.75 + k * 2.2, -0.6, -0.12, Y0 + HH + 0.6, top - 0.3, ((120, 70, 210), (60, 190, 160), (240, 160, 40))[k % 3], 'liso')
        j.bx(1.0, w - 1.0, 1.0, d - 1.0, top + 0.32, top + 0.6, (110, 160, 80), 'grama')
        for k in range(4):
            x, z = j.F.xz(2.0 + k * (w - 4) / 3, d - 2.5); j.L.trees.append((x, z, 'arbusto', 0.9, top + 0.6))
        for q in range(6): j.bx(2.0 + q * 1.0, 2.1 + q * 1.0, 2.0, 6.0, top + 2.8, top + 2.9, WOOD, 'liso')
        for (a, b) in ((2.0, 2.0), (7.0, 2.0), (2.0, 6.0), (7.0, 6.0)): j.bx(a - 0.06, a + 0.06, b - 0.06, b + 0.06, top + 0.6, top + 2.8, WOOD, 'liso')
    elif jid == 'engenheiro':
        # grua no telhado (torre treliçada, lanca e contrapeso)
        gu, gv = w * 0.7, d * 0.5
        for (a, b) in ((-0.6, -0.6), (0.6, -0.6), (-0.6, 0.6), (0.6, 0.6)): j.bx(gu + a - 0.06, gu + a + 0.06, gv + b - 0.06, gv + b + 0.06, top + 0.32, top + 14.0, (240, 190, 30), 'metal')
        for k in range(12): j.bx(gu - 0.6, gu + 0.6, gv - 0.62, gv - 0.58, top + 0.9 + k * 1.1, top + 0.98 + k * 1.1, (240, 190, 30), 'metal')
        j.bx(gu - 14.0, gu + 5.0, gv - 0.4, gv + 0.4, top + 14.0, top + 14.6, (240, 190, 30), 'metal')
        j.bx(gu + 3.0, gu + 5.0, gv - 0.8, gv + 0.8, top + 13.2, top + 14.0, (90, 94, 100), 'concreto')
        j.bx(gu - 0.8, gu + 0.8, gv - 0.8, gv + 0.8, top + 13.0, top + 14.0, (240, 190, 30), 'metal')
        j.cyl(gu - 11.0, gv, 0.02, top + 7.0, top + 14.0, DARK, 'metal', 4)
    elif jid == 'professor':
        G = j.sub(w / 2, -0.03, 0); jj = J(j.L, G)                             # relogio na fachada
        jj.cyl(0, -0.08, 0.7, Y0 + HH + 1.2, Y0 + HH + 1.2, (255, 255, 255), 'liso', 3)
        jj.bx(-0.7, 0.7, -0.12, -0.03, Y0 + HH + 1.3, Y0 + HH + 2.7, (250, 248, 240), 'liso')
        jj.bx(-0.03, 0.03, -0.14, -0.12, Y0 + HH + 2.0, Y0 + HH + 2.55, DARK); jj.bx(0.0, 0.45, -0.14, -0.12, Y0 + HH + 1.97, Y0 + HH + 2.03, DARK)
        for k in range(int(w / 3.4)): j.bx(0.5 + k * 3.4, 1.2 + k * 3.4, -0.08, -0.02, Y0 + HH + 0.62, Y0 + HH + 0.9, ((230, 70, 60), (60, 140, 220), (240, 190, 40), (70, 170, 90))[k % 4], 'liso')
    elif jid == 'enfermeiro':
        G = j.sub(w - 0.9, -0.3, 1); jj = J(j.L, G)                            # cruz verde luminosa
        jj.bx(0.2, 1.0, -0.05, 0.05, Y0 + 4.6, Y0 + 4.86, (40, 200, 120), 'liso'); jj.bx(0.47, 0.73, -0.05, 0.05, Y0 + 4.33, Y0 + 5.13, (40, 200, 120), 'liso')
    elif jid == 'medico':
        # marquise do pronto-socorro com cruz vermelha e heliponto no telhado
        j.bx(door_u - 5.0, door_u + 5.0, -5.0, 0.0, Y0 + 3.5, Y0 + 3.8, (250, 250, 250), 'metal')
        for s_ in (-1, 1): j.cyl(door_u + s_ * 4.6, -4.6, 0.15, Y_WALK, Y0 + 3.5, (220, 220, 224), 'metal', 8); j.solid(door_u + s_ * 4.6 - 0.15, door_u + s_ * 4.6 + 0.15, -4.75, -4.45)
        G = j.sub(door_u, -5.02, 0); jj = J(j.L, G)
        jj.bx(-0.9, 0.9, -0.06, 0.0, Y0 + 3.9, Y0 + 4.3, (220, 30, 40), 'liso'); jj.bx(-0.2, 0.2, -0.06, 0.0, Y0 + 3.4, Y0 + 4.8, (220, 30, 40), 'liso')
        hu, hv = w / 2, d / 2
        j.cyl(hu, hv, 7.0, top + 0.32, top + 0.5, (90, 96, 104), 'concreto', 24); j.cyl(hu, hv, 6.4, top + 0.5, top + 0.52, (250, 250, 250), 'liso', 24); j.cyl(hu, hv, 6.0, top + 0.52, top + 0.54, (90, 96, 104), 'concreto', 24)
        for (a_, b_, c_, e_) in ((-2.2, -1.4, -2.6, 2.6), (1.4, 2.2, -2.6, 2.6), (-1.4, 1.4, -0.4, 0.4)): j.bx(hu + a_, hu + b_, hv + c_, hv + e_, top + 0.54, top + 0.57, (250, 250, 250), 'liso')
    elif jid == 'advogado':
        j.bx(door_u - 1.6, door_u + 1.6, -1.6, -0.1, Y0 + 2.9, Y0 + 3.0, (40, 80, 60), 'liso')
        j.bx(door_u + 1.4, door_u + 1.9, -0.36, -0.32, Y0 + 1.2, Y0 + 1.8, (200, 170, 90), 'metal')    # placa de bronze
    elif jid in ('mecanico', 'entregador', 'lixeiro'):
        for k in range(r.randint(3, 6)): j.cyl(w - 1.2, -1.2 - (k % 3) * 0.7, 0.33, Y_WALK, Y_WALK + 0.24 * (1 + k // 3), (30, 30, 30), 'liso', 12)   # pneus
    elif jid == 'atendente':
        for k in range(2):                                                    # mesinhas na calcada
            tu = 2.0 + k * 3.2
            j.cyl(tu, -2.6, 0.4, Y_WALK + 0.72, Y_WALK + 0.76, (250, 250, 246), 'liso', 12); j.cyl(tu, -2.6, 0.04, Y_WALK, Y_WALK + 0.72, STEEL)
            j.cyl(tu, -2.6, 0.03, Y_WALK + 0.76, Y_WALK + 2.4, (220, 220, 220)); j.cyl(tu, -2.6, 1.2, Y_WALK + 2.2, Y_WALK + 2.45, acc, 'liso', 8, False, 0.05)
            j.solid(tu - 0.4, tu + 0.4, -3.0, -2.2)


# ---------------------------------------------------------------- interiores planejados
def interior2(j, jid, w, d, spec, door_u):
    """salas: frente (recepcao/atendimento) ate vf; fundos: sala principal (0..ua) e apoio (ua..w: copa + banheiros)"""
    sign, style, floors, _, _, fl, wall, acc = spec
    u0, v0, u1, v1 = 0.3, 0.3, w - 0.3, d - 0.3
    jw = J(j.L, j.F)
    # piso e forro
    fm = {'ceramica': 'paver', 'madeira': 'madeira', 'concreto': 'concreto', 'pedra': 'pedra'}[fl]
    fcol = {'ceramica': (232, 230, 226), 'madeira': (176, 132, 90), 'concreto': (196, 194, 190), 'pedra': (228, 222, 208)}[fl]
    j.bx(0.15, w - 0.15, 0.15, d - 0.15, Y0 - 0.04, Y0, fcol, fm)
    j.ceiling(0.15, w - 0.15, 0.15, d - 0.15)
    for uu in [1.8 + k * 3.4 for k in range(int((w - 2.4) / 3.4) + 1)]:
        for vv in [1.8 + k * 3.2 for k in range(int((d - 2.4) / 3.2) + 1)]:
            if uu < w - 1.2 and vv < d - 1.2: j.light(uu, vv, 1.1, 0.55)
    # rodape
    for (a, b, c, e) in ((0.15, w - 0.15, 0.15, 0.2), (0.15, w - 0.15, d - 0.2, d - 0.15), (0.15, 0.2, 0.15, d - 0.15), (w - 0.2, w - 0.15, 0.15, d - 0.15)):
        j.bx(a, b, c, e, Y0, Y0 + 0.1, (90, 84, 78), 'liso')
    open_plan = style in ('tijolo',) or jid in ('repositor', 'frentista')
    if open_plan:
        _open_interior(j, jid, w, d, acc, door_u)
        return
    vf = round(min(d * 0.42, 7.5), 2)
    ua = round(w * 0.64, 2)
    j.partition(0.15, w - 0.15, vf, (door_u, 1.6), glass=style == 'vidro')
    j.partition_u(vf, d - 0.15, ua, (vf + 1.4, 1.1))
    vm = round((vf + d) / 2 + 0.3, 2)
    j.partition(ua, w - 0.15, vm, (ua + 1.0, 0.9))
    j.pantry(ua + 0.35, w - 0.45, vf + 0.35, vm - 0.3)
    j.restroom(ua + 0.25, w - 0.35, vm + 0.3, d - 0.35)
    _front_room(j, jid, w, vf, door_u, acc)
    _main_room(j, jid, 0.45, vf + 0.45, ua - 0.45, d - 0.45, acc)


def _front_room(j, jid, w, vf, door_u, acc):
    """recepcao: balcao de frente para a porta, espera dos dois lados, plantas nos cantos, quadro e TV"""
    cu = door_u; cv = vf - 1.6
    if jid == 'atendente':
        # lanchonete: balcao ao fundo do salao, banquetas, mesas com cadeiras
        j.counter(w / 2, vf - 0.6, 0, w - 3.0, 0.7, (246, 238, 220), acc)
        k = 0; u = 2.0
        while u < w - 2.0:
            j.cyl(u, vf - 1.3, 0.21, Y0 + 0.72, Y0 + 0.78, acc, 'liso', 12); j.cyl(u, vf - 1.3, 0.04, Y0, Y0 + 0.72, STEEL); u += 0.85
        j.register(w - 2.4, vf - 0.6, 0)
        for k in range(3): j.bx(w / 2 - 3.0 + k * 2.1, w / 2 - 1.2 + k * 2.1, vf - 0.08, vf - 0.075, Y0 + 2.3, Y0 + 3.0, GLOW, 'liso')
        for u in (2.2, w - 2.2):
            if abs(u - door_u) > 1.8: j.round_table(u, 1.6, 0.45, (250, 250, 246), 3, acc)
        return
    j.counter(cu, cv, 0, min(3.4, w * 0.35), 0.7, (246, 244, 238), shade(acc, -10))
    j.bx(cu - 1.6, cu + 1.6, cv - 0.38, cv - 0.365, Y0 + 0.35, Y0 + 0.85, acc, 'liso')
    j.register(cu - 0.9, cv, 0)
    G = j.sub(cu, cv + 0.75, 2); jj = J(j.L, G); jj.chair(0, 0, 2, (50, 54, 60))
    for s_ in (-1, 1):
        su = door_u + s_ * (w * 0.3)
        if 1.6 < su < w - 1.6: j.seats_row(su, 0.75, 2, 3, shade(acc, 15))
    j.plant(0.75, 0.75, 1.2); j.plant(w - 0.75, 0.75, 1.2)
    j.plant(0.75, vf - 0.75); j.plant(w - 0.75, vf - 0.75)
    j.tv(0.9 + 0.08, vf / 2, 1, 1.2, 2.0)
    j.art(w - 0.25, vf / 2, 3, 1.4, 0.9)
    j.clock(cu, vf - 0.1, 0, 3.1)
    j.rug(cu - 1.6, cu + 1.6, 0.6, cv - 0.6, shade(acc, 45))
    j.water_cooler(0.6, vf - 1.8)


def _main_room(j, jid, a, b, c, e, acc):
    """sala principal de cada profissao, dentro do retangulo (u a..c, v b..e)"""
    W_ = c - a; D_ = e - b
    if jid in ('secretario', 'engenheiro', 'programador', 'empresario', 'advogado'):
        # estacoes em fileiras (pares frente a frente), armarios no fundo, impressora e plantas
        cols = max(1, int((W_ - 0.6) / 1.8)); rows = max(1, int((D_ - 2.2) / 2.6))
        for i in range(cols):
            for k in range(rows):
                u = a + 0.9 + i * 1.8 + 0.3; v = b + 1.2 + k * 2.6
                j.workstation(u, v, 0, acc if jid == 'programador' else (60, 70, 90))
        j.shelf(a + 1.0, e - 0.22, 0, 1.8, 2.0, 0.4, WOOD, 'pastas' if jid != 'advogado' else 'livros')
        if W_ > 4.5: j.shelf(a + 3.0, e - 0.22, 0, 1.8, 2.0, 0.4, WOOD, 'livros')
        j.plant(c - 0.5, e - 0.5, 1.1); j.plant(c - 0.5, b + 0.5)
        if jid == 'engenheiro': j.table(c - 1.2, e - 1.4, 1, 1.6, 1.0, (240, 240, 236), 0.92); j.bx(c - 1.7, c - 0.7, e - 2.2, e - 0.6, Y0 + 0.92, Y0 + 0.925, (210, 225, 240))
        if jid == 'programador':
            for k in range(2):
                j.bx(c - 0.75, c - 0.15, b + 0.4 + k * 0.8, b + 1.0 + k * 0.8, Y0, Y0 + 2.0, (30, 32, 36), 'metal'); j.solid(c - 0.75, c - 0.15, b + 0.4 + k * 0.8, b + 1.0 + k * 0.8)
                for q in range(10): j.bx(c - 0.76, c - 0.74, b + 0.45 + k * 0.8, b + 0.95 + k * 0.8, Y0 + 0.25 + q * 0.16, Y0 + 0.27 + q * 0.16, (60, 220, 120))
        return
    if jid == 'professor':
        j.board((a + c) / 2, e - 0.05, 0, min(4.0, W_ - 1.4), 1.2)
        j.desk((a + c) / 2, e - 1.3, 2, 1.4, 0.7, False, WOOD); G = j.sub((a + c) / 2, e - 0.6, 0); J(j.L, G).chair(0, 0, 0, (60, 70, 90))
        cols = max(1, int((W_ - 0.8) / 1.25)); rows = max(1, int((D_ - 3.0) / 1.2))
        for i in range(cols):
            for k in range(rows):
                u = a + 0.9 + i * 1.25; v = b + 0.7 + k * 1.2
                j.table(u, v, 0, 0.75, 0.5, (196, 164, 116), 0.72); G = j.sub(u, v - 0.5, 0); J(j.L, G).chair(0, 0, 2, (60, 120, 200), False)
        j.shelf(a + 0.25, (b + e) / 2, 1, 1.4, 1.5, 0.35, (240, 200, 90), 'livros')
        return
    if jid == 'policial':
        j.workstation(a + 1.2, b + 1.2, 0, (30, 60, 140)); j.workstation(a + 3.2, b + 1.2, 0, (30, 60, 140))
        cw = W_ / 2
        for k in range(2):
            ca = a + k * cw; cv0 = e - 2.6
            j.bx(ca, ca + 0.1, cv0, e, Y0, Y0 + HH - 0.15, (210, 208, 204), 'reboco')
            q = ca + 0.25
            while q < ca + cw - 0.15:
                if abs(q - (ca + cw / 2)) > 0.5: j.cyl(q, cv0, 0.025, Y0, Y0 + 2.7, STEEL, 'metal', 6)
                q += 0.15
            j.bx(ca + 0.1, ca + cw, cv0 - 0.03, cv0 + 0.03, Y0 + 2.7, Y0 + 2.8, STEEL, 'metal')
            j.solid(ca, ca + cw, cv0 - 0.05, cv0 + 0.05)
            j.bx(ca + 0.3, ca + cw - 0.3, e - 0.7, e - 0.05, Y0, Y0 + 0.45, (170, 172, 176), 'concreto'); j.bx(ca + 0.4, ca + 1.6, e - 0.65, e - 0.1, Y0 + 0.45, Y0 + 0.55, (90, 110, 140))
        return
    if jid in ('enfermeiro', 'medico'):
        n = max(1, int(W_ / 2.4))
        for k in range(n):
            mu = a + 1.2 + k * 2.4
            j.bx(mu - 0.4, mu + 0.4, e - 2.1, e - 0.2, Y0 + 0.6, Y0 + 0.75, (240, 244, 246)); j.bx(mu - 0.38, mu + 0.38, e - 0.6, e - 0.25, Y0 + 0.75, Y0 + 0.9, (210, 228, 240))
            for (p, q) in ((mu - 0.35, e - 2.0), (mu + 0.35, e - 2.0), (mu - 0.35, e - 0.3), (mu + 0.35, e - 0.3)): j.cyl(p, q, 0.025, Y0, Y0 + 0.6, STEEL, 'metal', 6)
            j.solid(mu - 0.4, mu + 0.4, e - 2.1, e - 0.2)
            if k < n - 1: j.bx(mu + 1.15, mu + 1.17, e - 2.3, e - 0.2, Y0 + 0.3, Y0 + 2.0, (150, 210, 200), 'liso')
        j.desk(a + 1.0, b + 0.9, 2, 1.3, 0.6); G = j.sub(a + 1.0, b + 1.6, 0); J(j.L, G).chair(0, 0, 0)
        j.shelf(c - 0.22, b + 1.2, 3, 1.4, 1.8, 0.4, (240, 240, 240), 'caixas')
        return
    if jid == 'juiz':
        cu = (a + c) / 2
        j.bx(cu - 2.6, cu + 2.6, e - 2.2, e - 0.1, Y0, Y0 + 0.45, (120, 84, 56), 'liso')
        j.bx(cu - 2.3, cu + 2.3, e - 2.1, e - 1.6, Y0 + 0.45, Y0 + 1.55, (110, 76, 50), 'liso'); j.bx(cu - 2.4, cu + 2.4, e - 2.15, e - 1.55, Y0 + 1.55, Y0 + 1.62, (90, 60, 40), 'liso')
        G = j.sub(cu, e - 1.0, 0); J(j.L, G).chair(0, 0, 0, (120, 30, 30)); j.solid(cu - 2.6, cu + 2.6, e - 2.2, e - 0.1)
        j.bx(cu - 0.9, cu + 0.9, e - 0.06, e - 0.03, Y0 + 2.2, Y0 + 3.3, (230, 200, 120), 'liso')
        for s_ in (-1, 1): j.table(cu + s_ * 1.8, e - 3.8, 0, 1.6, 0.7, (120, 84, 56)); G = j.sub(cu + s_ * 1.8, e - 4.4, 0); J(j.L, G).chair(0, 0, 2, (60, 40, 30))
        for k in range(2):
            vv = b + 0.6 + k * 1.1
            if vv > e - 5.0: break
            j.bx(a + 0.4, c - 0.4, vv, vv + 0.4, Y0, Y0 + 0.45, (120, 84, 56), 'liso'); j.bx(a + 0.4, c - 0.4, vv - 0.05, vv, Y0 + 0.45, Y0 + 0.95, (120, 84, 56), 'liso'); j.solid(a + 0.4, c - 0.4, vv - 0.05, vv + 0.4)
        return
    # padrao: duas mesas e estante
    j.workstation(a + 1.2, b + 1.2, 0); j.shelf(a + 1.0, e - 0.22, 0, 1.8)


def _open_interior(j, jid, w, d, acc, door_u):
    """galpoes e lojas de salao unico"""
    if jid == 'repositor':
        for k in range(3):                                                   # caixas junto da frente
            cu = 2.6 + k * 3.0
            if abs(cu - door_u) < 1.8: continue
            j.counter(cu, 2.4, 0, 1.6, 0.8, (240, 236, 228), (40, 40, 44), 0.9); j.register(cu + 0.5, 2.4, 0)
            j.bx(cu + 0.9, cu + 1.0, 1.9, 2.9, Y0, Y0 + 2.2, (200, 200, 204), 'metal'); j.bx(cu + 0.7, cu + 1.2, 2.3, 2.5, Y0 + 2.2, Y0 + 2.5, acc, 'liso')
        nrow = int((w - 6) / 2.8)
        for k in range(nrow): gondola(j, 3.0 + k * 2.8, 5.0, d - 4.0)
        j.bx(0.4, w - 0.4, d - 1.1, d - 0.25, Y0, Y0 + 2.1, (220, 228, 236), 'metal'); j.solid(0.4, w - 0.4, d - 1.1, d - 0.25)
        u = 0.6
        while u < w - 1.6:
            j.bx(u, u + 1.1, d - 1.12, d - 1.1, Y0 + 0.2, Y0 + 2.0, (190, 220, 235), 'vidro')
            for q in range(4): j.bx(u + 0.1, u + 1.0, d - 0.95, d - 0.45, Y0 + 0.35 + q * 0.42, Y0 + 0.55 + q * 0.42, jobs6.self_pick(j))
            u += 1.2
        for k in range(4):
            hv = 5.0 + k * 1.7
            if hv > d - 4.5: break
            j.bx(w - 2.4, w - 0.8, hv - 0.6, hv + 0.6, Y0, Y0 + 0.75, WOOD, 'liso'); j.solid(w - 2.4, w - 0.8, hv - 0.6, hv + 0.6)
            for q in range(10): j.ball(w - 2.2 + (q % 5) * 0.3, hv - 0.3 + (q // 5) * 0.5, Y0 + 0.86, 0.12, ((230, 60, 40), (250, 180, 40), (90, 170, 60), (240, 220, 80))[k])
        for k in range(4): cart(j, 0.9, 1.0 + k * 0.45)
        return
    if jid == 'frentista':
        j.counter(w / 2 + 2.0, 2.2, 0, 2.6, 0.7, (240, 236, 228), acc); j.register(w / 2 + 1.2, 2.2, 0)
        for k in range(2): gondola(j, 2.5 + k * 2.6, 4.5, d - 2.0)
        j.bx(w - 1.0, w - 0.3, 3.5, d - 0.6, Y0, Y0 + 2.0, (220, 228, 236), 'metal'); j.solid(w - 1.0, w - 0.3, 3.5, d - 0.6)
        return
    if jid == 'bombeiro':
        for k in range(2): fire_truck(j, w * (0.27 + 0.42 * k), d * 0.45)
        u = 1.0
        while u < w - 1.0:
            j.bx(u - 0.3, u + 0.3, d - 0.45, d - 0.25, Y0 + 1.4, Y0 + 2.2, (210, 180, 60)); j.cyl(u, d - 0.35, 0.17, Y0 + 2.2, Y0 + 2.5, (220, 40, 30), 'liso', 10); u += 1.6
        j.lockers(3.0, d - 1.3, 0, 6, (180, 40, 36))
        j.cyl(w - 1.5, d - 1.6, 0.05, Y0, Y0 + HH - 0.15, (220, 220, 220)); j.cyl(w - 1.5, d - 1.6, 0.6, Y0, Y0 + 0.1, (200, 40, 36), 'liso', 12)
        return
    if jid == 'mecanico':
        for k in range(2):
            lu = w * (0.27 + 0.46 * k); lv = d * 0.5
            for s_ in (-1, 1): j.bx(lu + s_ * 1.4 - 0.15, lu + s_ * 1.4 + 0.15, lv - 0.15, lv + 0.15, Y0, Y0 + 2.6, (40, 90, 160), 'metal'); j.solid(lu + s_ * 1.4 - 0.15, lu + s_ * 1.4 + 0.15, lv - 0.15, lv + 0.15)
            for s_ in (-1, 1): j.bx(lu - 1.2, lu + 1.2, lv + s_ * 0.9 - 0.08, lv + s_ * 0.9 + 0.08, Y0 + 1.6, Y0 + 1.7, (60, 60, 64), 'metal')
            x, z = j.F.xz(lu, lv); j.L.parked.append((x, z, j.F.vx, j.F.vz, Y0 + 1.72))
        j.bx(0.6, w - 0.6, d - 0.85, d - 0.3, Y0, Y0 + 0.9, (180, 40, 36), 'metal'); j.bx(0.55, w - 0.55, d - 0.9, d - 0.25, Y0 + 0.9, Y0 + 0.95, (110, 90, 70), 'liso')
        j.bx(0.6, w - 0.6, d - 0.29, d - 0.26, Y0 + 1.2, Y0 + 2.4, (200, 204, 208), 'metal'); j.solid(0.6, w - 0.6, d - 0.9, d - 0.25)
        return
    if jid == 'lixeiro':
        for k in range(2): garbage_truck(j, w * (0.27 + 0.42 * k), d * 0.5)
        for k in range(6): j.bx(1.0 + k * 1.4, 2.2 + k * 1.4, d - 1.4, d - 0.3, Y0, Y0 + 1.2, ((40, 120, 60), (220, 160, 40), (40, 90, 170), (180, 40, 36))[k % 4], 'metal')
        j.solid(1.0, 1.0 + 6 * 1.4, d - 1.4, d - 0.3)
        return
    if jid == 'entregador':
        for k in range(3): j.shelf(2.2 + k * 3.0, d - 0.6, 0, 2.6, 3.0, 0.9, (220, 120, 40), 'caixas')
        for k in range(4): moto(j, 1.5 + k * 1.4, 2.6)
        for k in range(8): j.bx(w - 4.0 + (k % 4) * 0.7, w - 3.4 + (k % 4) * 0.7, 5.0 + (k // 4) * 0.7, 5.6 + (k // 4) * 0.7, Y0, Y0 + 0.5, (196, 150, 100), 'liso')
        return


# ---------------------------------------------------------------- montagem
def depth(jid):
    return SPEC[jid][4]


def width(jid):
    return SPEC[jid][3]


def place(L, F, jid):
    """predio na fileira: F na divisa com a calcada, u ao longo da rua, v para dentro; ocupa width x depth"""
    spec = SPEC[jid]; sign, style, floors, w, d, fl, wall, acc = spec
    j = J(L, F)
    x, z = F.xz(w / 2, d / 2); L.M.at(x, z, 'lotes')
    door_u = w / 2 if jid not in ('bombeiro', 'mecanico', 'lixeiro', 'entregador') else 2.4
    extra = []
    if jid in ('bombeiro', 'mecanico', 'lixeiro', 'entregador'):          # portoes de garagem largos
        a = 4.2
        while a + 4.6 < w - 0.6: extra.append((a, a + 4.6, Y0, Y0 + 3.6, 'porta')); a += 5.4
    nb, bw = ground_floor(j, w, d, spec, door_u, extra)
    for (a, b, _, _, _) in extra:                                          # portao de enrolar recolhido + faixas
        j.bx(a, b, -0.35, 0.3, Y0 + 3.6, Y0 + 3.95, (200, 200, 204), 'metal')
        for q in range(int((b - a) / 0.5)): j.bx(a + 0.2 + q * 0.5, a + 0.45 + q * 0.5, -1.6, -0.2, Y_WALK + 0.003, Y_WALK + 0.012, (240, 200, 40), 'liso')
    top = upper(j, w, d, spec)
    storefront(j, w, nb, bw, spec, door_u)
    signature(j, jid, w, d, top, spec, door_u)
    interior2(j, jid, w, d, spec, door_u)
    L.M.free('lotes')
    dx, dz = F.xz(door_u, -1.5)
    L.jobs.append({'id': jid, 'nome': NAMES[jid], 'x': round(dx, 1), 'z': round(dz, 1), 'cor': 0xFF000000 | (acc[0] << 16) | (acc[1] << 8) | acc[2], 'icone': NAMES[jid][0], 'emoji': jobs6.EMOJI.get(jid, '💼')})
    L.__dict__.setdefault('feet', []).append((F.rect(0, w, 0, d), acc))
    L.B.drives.append((*F.xz(door_u, -1.2), 2.6))
    for k in range(int((w - 2) / 3.4) + 1): x, z = F.xz(1.2 + k * 3.4, d / 2); L.props_lights.append((round(x, 1), round(z, 1), 4.5))


def _unused_posto(j, w, d, spec):
    """posto: cobertura com bombas na frente (o predio da loja fica atras, no fundo do lote)"""
    sign, style, floors, _, _, _, wall, acc = spec
    # (o posto ocupa o mesmo retangulo: a loja e o predio; a cobertura vai na calcada larga da frente nao cabe —
    #  entao as bombas ficam numa marquise grande colada na fachada)
    j.bx(1.0, w - 1.0, -4.5, 0.0, Y0 + 4.4, Y0 + 5.0, (250, 250, 250), 'metal')
    j.bx(1.0, w - 1.0, -4.52, -4.45, Y0 + 4.45, Y0 + 4.95, acc, 'liso')
    j.M.m('liso'); j.M.poly([j.F.p(1.2, -4.3, Y0 + 4.39), j.F.p(w - 1.2, -4.3, Y0 + 4.39), j.F.p(w - 1.2, -0.2, Y0 + 4.39), j.F.p(1.2, -0.2, Y0 + 4.39)], GLOW, (0, -1, 0))
    for k in range(3):
        pu = 4.0 + k * (w - 8) / 2
        j.cyl(pu, -4.0, 0.2, Y_WALK, Y0 + 4.4, (240, 240, 240), 'metal', 10)
