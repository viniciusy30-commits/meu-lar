"""Cidade 6 - patio de cada predio de profissao (miolo da quadra, ligado a rua por uma entrada de carros).
Cada profissao tem o seu: patio das ambulancias, patio de treino dos bombeiros, garagem das viaturas, garagem dos
caminhoes de lixo, doca de carga, patio da oficina, canteiro de obras, quadra da escola, jardim executivo...
Piso elevado 6 cm acima do piso da quadra (nada pisca), sempre com postes, bancos ou elementos do uso e arvores
nas bordas quando sobra espaco."""
import math
from mesh import Frame, shade
from roads6 import Y_WALK
from shapely.geometry import box as sbox

Y = Y_WALK + 0.06
GLOW = (255, 238, 196)


def _floor(L, x0, z0, x1, z1, mat, col):
    M = L.M; M.free('lotes'); M.m(mat); M.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], Y_WALK - 0.05, Y, col)


def _stalls(L, x0, z0, x1, z1, along_x=True, every=2.7):
    """faixas de vaga pintadas numa fileira"""
    M = L.M; M.m('liso')
    if along_x:
        q = x0
        while q <= x1 + 1e-6: M.box(q - 0.06, q + 0.06, Y, Y + 0.012, z0, z1, (245, 245, 240)); q += every
    else:
        q = z0
        while q <= z1 + 1e-6: M.box(x0, x1, Y, Y + 0.012, q - 0.06, q + 0.06, (245, 245, 240)); q += every


def _van(L, x, z, body, stripe, cross=False, lightbar=None, along_x=False):
    """utilitario/ambulancia/viatura: caixa, cabine com vidro, rodas, faixa e (opcional) cruz e giroflex"""
    M = L.M; F = Frame((x, z), (1, 0) if along_x else (0, 1))
    def bx(a, b, c, e, y0, y1, col, mat='metal'):
        M.m(mat); M.prism(F.rect(a, b, c, e), Y + y0, Y + y1, col)
    bx(-2.6, 1.6, -1.0, 1.0, 0.45, 2.55, body)
    bx(1.6, 2.6, -1.0, 1.0, 0.45, 1.9, body); bx(1.62, 2.62, -0.92, 0.92, 1.15, 1.8, (40, 52, 66), 'vidro')
    bx(-2.62, 2.62, -1.02, 1.02, 1.05, 1.3, stripe, 'liso')
    if cross:
        for s_ in (-1, 1):
            a, b = F.xz(-0.6, s_ * 1.03); M.m('liso')
            M.box(a - 0.12, a + 0.12, Y + 1.5, Y + 2.2, b - 0.02, b + 0.02, (220, 30, 40)) if along_x else M.box(a - 0.02, a + 0.02, Y + 1.5, Y + 2.2, b - 0.12, b + 0.12, (220, 30, 40))
    if lightbar: bx(1.0, 1.5, -0.7, 0.7, 2.55 if not cross else 2.55, 2.7, lightbar, 'liso')
    for a in (-1.7, 1.7):
        for s_ in (-1, 1):
            p, q = F.xz(a, s_ * 0.95); M.m('liso'); M.cyl(p, q, 0.4, Y, Y + 0.08, (30, 30, 30), 10)
    L.B.solid(F, -2.6, 2.6, -1.0, 1.0)


def _car(L, x, z, body, along_x=False, lightbar=None):
    """carro baixo (viatura, carro da oficina)"""
    M = L.M; F = Frame((x, z), (1, 0) if along_x else (0, 1))
    def bx(a, b, c, e, y0, y1, col, mat='metal'):
        M.m(mat); M.prism(F.rect(a, b, c, e), Y + y0, Y + y1, col)
    bx(-2.2, 2.2, -0.88, 0.88, 0.3, 0.95, body); bx(-1.1, 1.0, -0.8, 0.8, 0.95, 1.45, (40, 52, 66), 'vidro')
    bx(-1.05, 0.95, -0.82, 0.82, 1.45, 1.5, body)
    if lightbar: bx(-0.2, 0.2, -0.6, 0.6, 1.5, 1.62, lightbar, 'liso')
    for a in (-1.4, 1.4):
        for s_ in (-1, 1):
            p, q = F.xz(a, s_ * 0.85); M.m('liso'); M.cyl(p, q, 0.33, Y, Y + 0.06, (30, 30, 30), 10)
    L.B.solid(F, -2.2, 2.2, -0.9, 0.9)


def _trees_edge(L, x0, z0, x1, z1, kinds=('folhosa', 'ornamental'), step=8.0, both=True):
    r = L.rnd; M = L.M
    for zz in ((z0 + 2.0, z1 - 2.0) if both else (z0 + 2.0,)):
        q = x0 + 3.0
        while q < x1 - 2.5:
            M.m('pedra'); M.prism([(q - 0.9, zz - 0.9), (q + 0.9, zz - 0.9), (q + 0.9, zz + 0.9), (q - 0.9, zz + 0.9)], Y, Y + 0.14, (200, 194, 182))
            L.trees.append((q, zz, r.choice(kinds), r.uniform(0.9, 1.15), Y + 0.14)); q += step


def _lamps(L, x0, z0, x1, z1):
    for (px, pz) in ((x0 + 1.0, z0 + 1.0), (x1 - 1.0, z1 - 1.0), (x0 + 1.0, z1 - 1.0), (x1 - 1.0, z0 + 1.0)): L.plights.append((px, pz, Y))


def build(L, jid, x0, z0, x1, z1):
    r = L.rnd; M = L.M
    L.pocc.append(sbox(x0, z0, x1, z1))
    w, d = x1 - x0, z1 - z0; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    M.at(cx, cz, 'lotes')
    if w < 14 or d < 14:
        _floor(L, x0, z0, x1, z1, 'paver', (226, 220, 210)); L.planter(x0 + 1, z0 + 1, x1 - 1, z1 - 1); M.free(); return
    ax = w >= d                                                               # fileiras ao longo do lado maior
    def rows(n_max, item_len, gap, fn):
        """distribui veiculos/objetos numa fileira central (nunca mais que n_max)"""
        Lr = (w if ax else d) - 6.0; n = max(1, min(n_max, int(Lr / (item_len + gap))))
        for k in range(n):
            t = (k + 0.5) / n
            fn(x0 + 3 + Lr * t if ax else cx, cz if ax else z0 + 3 + Lr * t)
    if jid in ('medico', 'enfermeiro'):
        _floor(L, x0, z0, x1, z1, 'asfalto', (78, 78, 82)); _stalls(L, x0 + 3, cz - 3.5, x1 - 3, cz + 3.5, True, 3.4) if ax else _stalls(L, cx - 3.5, z0 + 3, cx + 3.5, z1 - 3, False, 3.4)
        rows(4 if jid == 'medico' else 2, 3.4, 0.0, lambda x, z: _van(L, x, z, (250, 250, 250), (220, 40, 50), True, (220, 30, 40), not ax))
        # jardim de espera dos acompanhantes num canto
        _trees_edge(L, x0, z0, x1, z1, ('florida', 'ornamental'), 9.0, False)
        for k in range(3): L.benches.append((x0 + 4 + k * 3.0, z1 - 1.6, 0, -1, Y))
    elif jid == 'bombeiro':
        _floor(L, x0, z0, x1, z1, 'concreto', (190, 188, 184))
        rows(2, 8.5, 2.0, lambda x, z: _van(L, x, z, (200, 30, 28), (250, 250, 250), False, (60, 120, 230), ax))
        # torre de treino, hidrantes, cones e carretel de mangueira
        tx, tz = x1 - 4, z0 + 4
        M.m('tijolo'); M.box(tx - 2, tx + 2, Y, Y + 11, tz - 2, tz + 2, (170, 70, 56)); M.m('metal')
        for k in range(4): M.box(tx - 2.05, tx - 1.95, Y + 1.5 + k * 2.5, Y + 2.6 + k * 2.5, tz - 0.6, tz + 0.6, (60, 60, 64))
        L.B.solid(Frame((tx, tz), (1, 0)), -2, 2, -2, 2)
        for k in range(3):
            hx = x0 + 3 + k * 4; M.m('metal'); M.cyl(hx, z1 - 2, 0.18, Y, Y + 0.7, (220, 40, 30), 8); M.cyl(hx, z1 - 2, 0.24, Y + 0.7, Y + 0.8, (220, 40, 30), 8)
        for k in range(8):
            M.m('liso'); M.cyl(x0 + 4 + k * 1.5, cz + (5 if ax else 0), 0.22, Y, Y + 0.6, (250, 120, 30), 8, True, 0.03)
        M.m('metal'); M.cyl(x0 + 2.5, z0 + 3, 0.7, Y + 0.6, Y + 1.0, (200, 30, 28), 12)
    elif jid == 'policial':
        _floor(L, x0, z0, x1, z1, 'asfalto', (70, 70, 74))
        _stalls(L, x0 + 3, z0 + 2, x1 - 3, z0 + 7, True, 2.8); _stalls(L, x0 + 3, z1 - 7, x1 - 3, z1 - 2, True, 2.8)
        q = x0 + 4.4
        while q < x1 - 3:
            _car(L, q, z0 + 4.5, (240, 240, 244) if r.random() < 0.7 else (30, 40, 70), False, (40, 90, 220))
            if r.random() < 0.6: _car(L, q, z1 - 4.5, (240, 240, 244), False, (40, 90, 220))
            q += 2.8 * 2
        for k in range(int((w - 8) / 2.2)):                                   # barreiras de transito
            bxx = x0 + 4 + k * 2.2; M.m('liso'); M.box(bxx - 0.9, bxx + 0.9, Y + 0.5, Y + 0.8, cz - 0.1, cz + 0.1, (240, 240, 240) if k % 2 else (220, 40, 40))
            M.box(bxx - 0.85, bxx - 0.75, Y, Y + 0.5, cz - 0.3, cz + 0.3, (60, 60, 64)); M.box(bxx + 0.75, bxx + 0.85, Y, Y + 0.5, cz - 0.3, cz + 0.3, (60, 60, 64))
    elif jid == 'lixeiro':
        _floor(L, x0, z0, x1, z1, 'concreto', (176, 174, 168))
        rows(3, 8.0, 2.0, lambda x, z: _van(L, x, z, (60, 140, 70), (250, 250, 248), False, (240, 180, 40), ax))
        cols = ((60, 140, 70), (40, 100, 200), (240, 200, 40), (200, 60, 50), (120, 120, 124))
        for k in range(int((w - 6) / 2.2)):
            bxx = x0 + 3.5 + k * 2.2; M.m('metal'); M.box(bxx - 0.9, bxx + 0.9, Y, Y + 1.3, z1 - 2.6, z1 - 1.0, cols[k % 5]); M.box(bxx - 0.95, bxx + 0.95, Y + 1.3, Y + 1.38, z1 - 2.7, z1 - 0.9, shade(cols[k % 5], -30))
            L.B.solid(Frame((bxx, z1 - 1.8), (1, 0)), -0.9, 0.9, -0.8, 0.8)
    elif jid in ('entregador', 'repositor', 'frentista', 'diarista'):
        _floor(L, x0, z0, x1, z1, 'concreto', (190, 188, 182))
        body = {'entregador': (240, 140, 40), 'repositor': (60, 150, 70), 'frentista': (30, 100, 180), 'diarista': (40, 150, 190)}[jid]
        rows(3, 6.0, 2.0, lambda x, z: _van(L, x, z, body, (250, 250, 248), False, None, ax))
        # paletes com caixas e gaiolas de carga junto da parede
        for k in range(int((w - 6) / 2.4)):
            px_ = x0 + 3.5 + k * 2.4; M.m('madeira'); M.box(px_ - 0.6, px_ + 0.6, Y, Y + 0.15, z0 + 1.2, z0 + 2.4, (170, 130, 90))
            h = r.choice((0.5, 0.9, 1.3)); M.m('liso'); M.box(px_ - 0.55, px_ + 0.55, Y + 0.15, Y + 0.15 + h, z0 + 1.25, z0 + 2.35, (200, 170, 120))
            L.B.solid(Frame((px_, z0 + 1.8), (1, 0)), -0.6, 0.6, -0.6, 0.6)
        if jid == 'entregador':
            for k in range(6):
                mx = x0 + 4 + k * 1.4; M.m('metal'); M.box(mx - 0.12, mx + 0.12, Y + 0.3, Y + 0.7, z1 - 3, z1 - 1.6, body); M.cyl(mx, z1 - 3, 0.3, Y, Y + 0.06, (30, 30, 30), 8); M.cyl(mx, z1 - 1.6, 0.3, Y, Y + 0.06, (30, 30, 30), 8)
    elif jid == 'mecanico':
        _floor(L, x0, z0, x1, z1, 'concreto', (160, 158, 154))
        rows(4, 4.4, 1.6, lambda x, z: _car(L, x, z, r.choice(((200, 60, 50), (60, 90, 160), (230, 230, 230), (40, 40, 44))), ax))
        for k in range(6):                                                    # pilhas de pneus e tambores de oleo
            tx = x0 + 3 + k * 1.6; M.m('liso')
            for q in range(r.randint(2, 5)): M.cyl(tx, z1 - 2, 0.38, Y + q * 0.24, Y + q * 0.24 + 0.22, (30, 30, 32), 12)
        for k in range(4): M.m('metal'); M.cyl(x1 - 2 - k * 0.8, z0 + 2, 0.3, Y, Y + 0.9, (40, 90, 160) if k % 2 else (200, 60, 50), 10)
    elif jid == 'engenheiro':
        _floor(L, x0, z0, x1, z1, 'cascalho', (170, 160, 140))
        # canteiro de obras: containers-escritorio, tubos, pilhas de blocos, betoneira
        M.m('metal')
        for k in range(2):
            ccx = x0 + 4 + k * 7; M.box(ccx, ccx + 6, Y, Y + 2.6, z0 + 2, z0 + 4.4, (240, 180, 40) if k == 0 else (230, 230, 226)); L.B.solid(Frame((ccx + 3, z0 + 3.2), (1, 0)), -3, 3, -1.2, 1.2)
        for k in range(5): M.cyl(cx - 3 + k * 0.0, cz - 1 + k * 0.62, 0.3, Y, Y + 0.6, (180, 180, 186), 10)
        for k in range(4):
            bxx = x1 - 4 - k * 2.2; M.m('concreto'); M.box(bxx - 0.8, bxx + 0.8, Y, Y + 0.4 + 0.3 * (k % 3), z1 - 3, z1 - 1.6, (190, 188, 182))
        M.m('metal'); M.cyl(cx + 4, cz + 2, 0.7, Y + 0.6, Y + 1.8, (240, 120, 40), 12, True, 0.4); M.box(cx + 3.2, cx + 4.8, Y, Y + 0.6, cz + 1.4, cz + 2.6, (60, 60, 64))
        for k in range(int((w - 4) / 2.0)): M.m('liso'); M.box(x0 + 2 + k * 2.0, x0 + 2.9 + k * 2.0, Y, Y + 1.2, z1 - 0.5, z1 - 0.45, (240, 120, 40) if k % 2 else (250, 250, 250))
    elif jid == 'professor':
        _floor(L, x0, z0, x1, z1, 'quadra', (60, 120, 170))
        # quadra poliesportiva com linhas e tabelas, arquibancada de um lado
        M.m('liso')
        for (a, b, c_, e) in ((x0 + 2, x1 - 2, z0 + 2, z0 + 2.1), (x0 + 2, x1 - 2, z1 - 2.1, z1 - 2), (x0 + 2, x0 + 2.1, z0 + 2, z1 - 2), (x1 - 2.1, x1 - 2, z0 + 2, z1 - 2), (cx - 0.05, cx + 0.05, z0 + 2, z1 - 2)):
            M.box(a, b, Y, Y + 0.012, c_, e, (250, 250, 248))
        for sx_ in (x0 + 2.5, x1 - 2.5):
            M.m('metal'); M.cyl(sx_, cz, 0.08, Y, Y + 3.0, (220, 220, 224), 8); M.box(sx_ - 0.05, sx_ + 0.05, Y + 2.6, Y + 3.6, cz - 0.9, cz + 0.9, (250, 250, 250))
        for k in range(3): M.m('concreto'); M.box(x0 + 3, x1 - 3, Y, Y + 0.45 * (k + 1), z1 - 1.5 + 0.0 - k * 0.0, z1 - 0.5, (200, 198, 192)) if k == 0 else None
    else:   # juiz, advogado, secretario, programador, empresario, atendente: jardim executivo
        _floor(L, x0, z0, x1, z1, 'paver', (224, 216, 204))
        M.m('grama'); M.prism([(x0 + 3, z0 + 3), (x1 - 3, z0 + 3), (x1 - 3, z1 - 3), (x0 + 3, z1 - 3)], Y, Y + 0.04, (110, 160, 80))
        # espelho d'agua com repuxos, escultura e bancos de pedra
        M.m('pedra'); M.prism([(cx - 5, cz - 1.6), (cx + 5, cz - 1.6), (cx + 5, cz + 1.6), (cx - 5, cz + 1.6)], Y, Y + 0.5, (210, 204, 192))
        M.m('agua'); M.prism([(cx - 4.7, cz - 1.3), (cx + 4.7, cz - 1.3), (cx + 4.7, cz + 1.3), (cx - 4.7, cz + 1.3)], Y + 0.5, Y + 0.45, (120, 180, 200))
        for k in range(5): M.m('liso'); M.cyl(cx - 3.6 + k * 1.8, cz, 0.04, Y + 0.45, Y + 1.4, (230, 245, 250), 5, True, 0.01)
        L.B.solid(Frame((cx, cz), (1, 0)), -5, 5, -1.6, 1.6)
        if jid == 'programador':
            for k in range(4): M.m('liso'); M.cyl(x0 + 5 + k * 3, z1 - 5, 0.6, Y + 0.04, Y + 0.6, ((240, 120, 40), (60, 140, 200), (140, 60, 180), (90, 170, 80))[k], 10, True, 0.35)   # pufes
        for (dx, dz) in ((0, 1), (0, -1)):
            for k in (-1, 1): L.benches.append((cx + k * 3.0, cz + dz * 3.4, 0, -dz, Y + 0.04))
        _trees_edge(L, x0 + 1, z0 + 1, x1 - 1, z1 - 1, ('florida', 'oval', 'ornamental'), 7.0, True)
    _lamps(L, x0, z0, x1, z1)
    M.free()
