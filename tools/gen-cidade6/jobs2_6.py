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
    'repositor':  ('SUPERBOM', 'loja', 1, 64, 40, 'ceramica', (238, 236, 230), (60, 150, 70)),
    'atendente':  ('LANCHONETE DO ZE', 'loja', 3, 34, 24, 'ceramica', (250, 240, 214), (200, 50, 40)),
    'diarista':   ('BRILHO LIMPEZA', 'loja', 4, 32, 24, 'ceramica', (226, 240, 246), (40, 150, 190)),
    'frentista':  ('POSTO ROTA SUL', 'loja', 2, 44, 28, 'ceramica', (240, 242, 244), (30, 100, 180)),
    'medico':     ('HOSPITAL SANTA CLARA', 'inst', 7, 62, 34, 'ceramica', (244, 246, 248), (200, 40, 50)),
    'entregador': ('EXPRESSO JA', 'tijolo', 3, 46, 30, 'concreto', (176, 96, 70), (240, 140, 40)),
    'lixeiro':    ('CENTRAL DE COLETA', 'tijolo', 3, 54, 34, 'concreto', (150, 96, 74), (70, 150, 70)),
    'mecanico':   ('OFICINA DO TONINHO', 'tijolo', 2, 46, 30, 'concreto', (160, 92, 70), (230, 170, 30)),
    'bombeiro':   ('BOMBEIROS', 'tijolo', 3, 52, 34, 'concreto', (178, 70, 56), (200, 40, 36)),
    'policial':   ('DELEGACIA', 'inst', 5, 48, 30, 'ceramica', (232, 234, 238), (30, 60, 140)),
    'enfermeiro': ('CLINICA AURORA', 'inst', 6, 46, 28, 'ceramica', (244, 246, 244), (30, 150, 130)),
    'professor':  ('ESCOLA PRIMAVERA', 'inst', 4, 62, 34, 'madeira', (244, 226, 180), (230, 120, 40)),
    'juiz':       ('FORUM DA COMARCA', 'classico', 4, 54, 34, 'pedra', (226, 216, 196), (150, 120, 70)),
    'advogado':   ('ALMEIDA & PRADO', 'classico', 9, 36, 24, 'madeira', (214, 200, 178), (40, 80, 60)),
    'secretario': ('ESCRITORIO CENTRAL', 'vidro', 13, 42, 28, 'madeira', (220, 224, 228), (60, 90, 150)),
    'engenheiro': ('PILAR CONSTRUTORA', 'vidro', 11, 42, 28, 'madeira', (210, 206, 198), (230, 170, 30)),
    'programador': ('NOVA TECH', 'vidro', 15, 46, 30, 'madeira', (230, 232, 238), (120, 70, 210)),
    'empresario': ('GRUPO ATLAS', 'vidro', 26, 48, 34, 'pedra', (40, 46, 56), (200, 170, 90)),
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
    '0': '01110 10001 10011 10101 11001 10001 01110', '1': '00100 01100 00100 00100 00100 00100 01110',
    '2': '01110 10001 00001 00010 00100 01000 11111', '3': '11110 00001 00001 01110 00001 00001 11110',
    '4': '00010 00110 01010 10010 11111 00010 00010', '5': '11111 10000 11110 00001 00001 10001 01110',
    '6': '00110 01000 10000 11110 10001 10001 01110', '7': '11111 00001 00010 00100 01000 01000 01000',
    '8': '01110 10001 10001 01110 10001 10001 01110', '9': '01110 10001 10001 01111 00001 00010 01100',
    '-': '00000 00000 00000 11111 00000 00000 00000', '.': '00000 00000 00000 00000 00000 01100 01100',
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
        j.bx(door_u + s_ * 0.55 - 0.55, door_u + s_ * 0.55 + 0.55, -0.06, -0.03, Y0, Y0 + 2.8, (150, 186, 204), 'vidro')     # porta de vidro fechada (sem interior)
        j.bx(door_u + s_ * 0.12 - 0.03, door_u + s_ * 0.12 + 0.03, -0.1, -0.06, Y0 + 0.9, Y0 + 1.5, (200, 200, 206), 'metal')   # puxador
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
def grand(j, jid, w, d, top, spec, door_u):
    """o que faz o predio da profissao se destacar na cidade: torres de quina mais altas com coroa iluminada,
    portal de entrada de dois andares com colunas e vidro na cor da marca, letreiro grande no alto (letras em relevo
    sobre estrutura), faixa vertical luminosa, iluminacao de fachada e praca de entrada (floreiras, mastros, balizadores)."""
    sign, style, floors, _, _, _, wall, acc = spec
    clad = shade(acc, -25) if style != 'classico' else (232, 222, 200)
    cm = 'metal' if style == 'vidro' else 'pedra'
    tw = min(5.0, w * 0.12)
    # ---- torres das quinas (sobem 3,5 m acima da cobertura)
    for (a, b) in ((-0.3, tw), (w - tw, w + 0.3)):
        j.bx(a, b, -0.6, 4.2, Y_WALK, top + 3.5, clad, cm)
        j.bx(a - 0.15, b + 0.15, -0.75, 4.35, top + 3.5, top + 3.85, shade(clad, 25), 'concreto')
        j.bx(a + 0.4, b - 0.4, -0.62, -0.6, top + 2.4, top + 3.2, GLOW, 'liso')                       # coroa acesa
        for f in range(max(1, int((top - Y0 - HH) / FH))):                                             # janelas estreitas da torre
            y = Y0 + HH + 0.9 + f * FH
            if y + 1.8 < top + 2.2: j.bx(a + tw * 0.32, b - tw * 0.32, -0.66, -0.6, y, y + 1.8, (170, 200, 220) if style != 'tijolo' else (60, 70, 80), 'janela')
        j.bx(a + 0.2, b - 0.2, -0.64, -0.6, Y_WALK + 0.05, Y_WALK + 0.25, GLOW, 'liso')               # luz rasante na base
    # ---- portal de entrada de dois andares
    pw = min(9.0, w * 0.3); ph = min(top - Y_WALK - 0.5, Y0 + HH + FH + 1.2)
    for s_ in (-1, 1):
        cu = door_u + s_ * pw / 2
        j.cyl(cu, -2.6, 0.38, Y_WALK, ph, (246, 244, 238) if style != 'vidro' else (210, 214, 220), 'pedra' if style != 'vidro' else 'metal', 16)
        j.cyl(cu, -2.6, 0.5, Y_WALK, Y_WALK + 0.35, shade(clad, 10), 'pedra', 16)
        j.cyl(cu, -2.6, 0.5, ph - 0.3, ph, shade(clad, 10), 'pedra', 16)
    j.bx(door_u - pw / 2 - 0.7, door_u + pw / 2 + 0.7, -3.3, 0.05, ph, ph + 1.1, clad, cm)
    j.bx(door_u - pw / 2 - 0.85, door_u + pw / 2 + 0.85, -3.45, 0.05, ph + 1.1, ph + 1.25, shade(clad, 25), 'concreto')
    sign_text(j, sign, door_u, -3.31, ph + 0.18, 0.62, (255, 250, 236), 0.06, pw + 0.8)
    j.bx(door_u - pw / 2 + 0.6, door_u + pw / 2 - 0.6, -0.08, -0.02, Y0 + HH + 0.2, ph - 0.1, shade(acc, 30), 'vidro')   # vidro colorido sobre a porta
    j.M.m('liso'); j.M.poly([j.F.p(door_u - pw / 2, -3.3, ph - 0.01), j.F.p(door_u + pw / 2, -3.3, ph - 0.01), j.F.p(door_u + pw / 2, -0.1, ph - 0.01), j.F.p(door_u - pw / 2, -0.1, ph - 0.01)], GLOW, (0, -1, 0))
    j.bx(door_u - pw / 2 - 0.4, door_u + pw / 2 + 0.4, -3.6, 0.0, Y_WALK, Y_WALK + 0.12, (214, 208, 196), 'pedra')            # piso do portal
    # ---- letreiro grande no alto, sobre estrutura metalica, de frente para a rua
    sw = min(w - 2 * tw - 2.0, max(10.0, len(sign) * 1.05))
    if sw > 6:
        for q in range(4): uu = w / 2 - sw / 2 + sw * q / 3; j.bx(uu - 0.08, uu + 0.08, 1.2, 1.36, top + 0.32, top + 1.2, DARK, 'metal')
        j.bx(w / 2 - sw / 2 - 0.3, w / 2 + sw / 2 + 0.3, 1.1, 1.2, top + 1.1, top + 3.1, shade(acc, -40), 'liso')
        sign_text(j, sign, w / 2, 1.1, top + 1.35, 1.45, (255, 248, 230), 0.08, sw)
    # ---- faixa vertical luminosa (marca) na torre direita
    j.bx(w - tw + 0.6, w - 0.6, -0.72, -0.64, Y0 + HH + 0.8, top + 1.8, acc, 'liso')
    j.bx(w - tw / 2 - 0.12, w - tw / 2 + 0.12, -0.74, -0.72, Y0 + HH + 1.0, top + 1.6, GLOW, 'liso')
    # ---- praca de entrada: floreiras com arbustos, mastros com bandeiras e balizadores
    for s_ in (-1, 1):
        fu = door_u + s_ * (pw / 2 + 3.2)
        if 1.5 < fu < w - 1.5:
            j.bx(fu - 1.4, fu + 1.4, -4.2, -2.4, Y_WALK, Y_WALK + 0.55, (200, 194, 182), 'pedra')
            j.bx(fu - 1.25, fu + 1.25, -4.05, -2.55, Y_WALK + 0.55, Y_WALK + 0.58, (90, 70, 50), 'liso')
            x, z = j.F.xz(fu, -3.3); j.L.trees.append((x, z, 'arbusto', 1.0, Y_WALK + 0.58))
            j.solid(fu - 1.4, fu + 1.4, -4.2, -2.4)
    for q, fc in enumerate((acc, (40, 140, 70), (30, 60, 150))):
        mu = tw + 1.5 + q * 1.4
        if mu < door_u - pw / 2 - 1.0:
            j.cyl(mu, -3.8, 0.06, Y_WALK, Y_WALK + 8.5, (230, 230, 232), 'metal', 8)
            G = j.sub(mu, -3.8, 0); J(j.L, G).bx(0.06, 1.7, -0.01, 0.01, Y_WALK + 7.2, Y_WALK + 8.3, fc, 'liso')
    q = door_u - pw / 2 - 0.6
    while q < door_u + pw / 2 + 0.7:
        j.cyl(q, -4.6, 0.12, Y_WALK, Y_WALK + 0.8, (60, 62, 66), 'metal', 8); q += 1.5


def interior2(j, jid, w, d, spec, door_u, garage_doors=()):
    """sem interior mobiliado: o predio e fechado (vidro escurecido com cortinas por dentro), a porta e o ponto de
    trabalho na calcada (o jogo mostra o marcador e o botao TRABALHAR)"""
    j.bx(0.3, w - 0.3, 0.3, 0.42, Y0, Y0 + 3.4, (70, 78, 88), 'liso')                     # fundo atras das vitrines
    j.solid(door_u - 1.2, door_u + 1.2, -0.1, 0.5)


# ---------------------------------------------------------------- montagem
def depth(jid):
    return SPEC[jid][4]


def width(jid):
    return SPEC[jid][3]


def place(L, F, jid, w_=None, d_=None, floors_=None):
    """predio na fileira: F na divisa com a calcada, u ao longo da rua, v para dentro; ocupa width x depth
    (w_, d_, floors_: tamanho do predio principal do campus da profissao, que ocupa a frente inteira da quadra)"""
    spec = SPEC[jid]
    if w_ or d_ or floors_:
        spec = (spec[0], spec[1], floors_ or spec[2], w_ or spec[3], d_ or spec[4], spec[5], spec[6], spec[7])
    sign, style, floors, w, d, fl, wall, acc = spec
    j = J(L, F)
    x, z = F.xz(w / 2, d / 2); L.M.at(x, z, 'lotes')
    import arch6
    if w_ and jid in arch6.BUILDERS:                                       # campus: arquitetura propria da profissao
        door_u, door_v = arch6.build(L, F, jid, w, d, floors, spec)
        L.M.free('lotes')
        dx, dz = F.xz(door_u, door_v - 1.5)
        L.jobs.append({'id': jid, 'nome': NAMES[jid], 'x': round(dx, 1), 'z': round(dz, 1), 'cor': 0xFF000000 | (acc[0] << 16) | (acc[1] << 8) | acc[2], 'icone': NAMES[jid][0], 'emoji': jobs6.EMOJI.get(jid, '💼')})
        L.__dict__.setdefault('feet', []).append((F.rect(0, w, 0, d), acc))
        L.B.drives.append((*F.xz(door_u, door_v - 1.2), 2.6))
        return
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
    grand(j, jid, w, d, top, spec, door_u)
    interior2(j, jid, w, d, spec, door_u, extra)
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
