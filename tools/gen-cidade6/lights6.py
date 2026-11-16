"""Cidade 6 - luminarias detalhadas (pracas, parques, molhes, calcadoes). Cada estilo tem base, fuste, aneis,
braco/cabeca e vidro emissivo (material 'liso' em tom quente: no ciclo de noite vira luz)."""
import math

GLOW = (255, 238, 196)
IRON = (34, 40, 46)
IRON2 = (52, 60, 68)


def _base(M, x, z, y, r=0.26, col=IRON):
    """pe fundido: degrau, sino canelado e anel"""
    M.m('metal')
    M.cyl(x, z, r + 0.06, y, y + 0.08, col, 10)
    M.cyl(x, z, r, y + 0.08, y + 0.75, col, 10, False, r * 0.55)
    for k in range(10):                                       # caneluras
        a = 2 * math.pi * k / 10; rr = r * 0.8
        M.box(x + math.cos(a) * rr - 0.025, x + math.cos(a) * rr + 0.025, y + 0.15, y + 0.6, z + math.sin(a) * rr - 0.025, z + math.sin(a) * rr + 0.025, IRON2)
    M.cyl(x, z, r * 0.62, y + 0.75, y + 0.85, IRON2, 10)


def _lantern(M, x, z, y, s=1.0):
    """lanterna de 4 vidros (estilo antigo): bandeja, montantes, vidros acesos, chapeu com remate"""
    M.m('metal')
    M.cyl(x, z, 0.12 * s, y, y + 0.08 * s, IRON, 8)
    M.cyl(x, z, 0.2 * s, y + 0.08 * s, y + 0.14 * s, IRON, 4)
    M.m('liso')
    M.cyl(x, z, 0.19 * s, y + 0.14 * s, y + 0.62 * s, GLOW, 4, False, 0.25 * s)
    M.m('metal')
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        for (rr0, rr1) in ((0.2, 0.26),):
            ax, az = x + math.cos(a) * rr0 * s, z + math.sin(a) * rr0 * s; bx, bz = x + math.cos(a) * rr1 * s, z + math.sin(a) * rr1 * s
            M.quad((ax, y + 0.14 * s, az), (ax + 0.02, y + 0.14 * s, az), (bx + 0.02, y + 0.62 * s, bz), (bx, y + 0.62 * s, bz), IRON, (math.cos(a), 0, math.sin(a)))
    M.cyl(x, z, 0.32 * s, y + 0.62 * s, y + 0.68 * s, IRON, 4)
    M.cyl(x, z, 0.3 * s, y + 0.68 * s, y + 0.9 * s, IRON, 4, False, 0.05 * s)
    M.sphere(x, y + 0.95 * s, z, 0.05 * s, IRON, 5, 3)


def victorian(M, x, z, y, heads=1):
    """poste colonial de praca: pe canelado, fuste com aneis, uma lanterna no topo ou duas em braco com volutas"""
    _base(M, x, z, y)
    M.m('metal')
    M.cyl(x, z, 0.075, y + 0.85, y + 3.4, IRON, 8, False, 0.06)
    for yy in (y + 1.6, y + 2.6): M.cyl(x, z, 0.1, yy, yy + 0.06, IRON2, 8)
    if heads == 1:
        M.cyl(x, z, 0.1, y + 3.4, y + 3.5, IRON2, 8)
        _lantern(M, x, z, y + 3.5)
    else:
        M.cyl(x, z, 0.09, y + 3.3, y + 3.4, IRON2, 8)
        for sg in (-1, 1):
            # braco em arco com voluta
            prev = None
            for k in range(7):
                t = k / 6; px, py = x + sg * 0.6 * t, y + 3.35 + 0.35 * math.sin(t * math.pi)
                if prev: M.quad((prev[0], prev[1] - 0.03, z - 0.03), (px, py - 0.03, z - 0.03), (px, py + 0.03, z + 0.03), (prev[0], prev[1] + 0.03, z + 0.03), IRON, (0, 1, 0))
                prev = (px, py)
            for k in range(6):
                a0, a1 = k * 1.0, (k + 1) * 1.0; rr0, rr1 = 0.12 - k * 0.015, 0.12 - (k + 1) * 0.015
                M.quad((x + sg * (0.3 + math.cos(a0) * rr0), y + 3.15 + math.sin(a0) * rr0, z - 0.02), (x + sg * (0.3 + math.cos(a1) * rr1), y + 3.15 + math.sin(a1) * rr1, z - 0.02),
                       (x + sg * (0.3 + math.cos(a1) * rr1), y + 3.15 + math.sin(a1) * rr1, z + 0.02), (x + sg * (0.3 + math.cos(a0) * rr0), y + 3.15 + math.sin(a0) * rr0, z + 0.02), IRON, (0, 0, 1))
            M.cyl(x + sg * 0.6, z, 0.02, y + 3.2, y + 3.4, IRON, 5)
            _lantern(M, x + sg * 0.6, z, y + 2.75, 0.8)
        M.sphere(x, y + 3.75, z, 0.07, IRON, 6, 4)


def globes(M, x, z, y, n=3):
    """candelabro de globos: pe canelado, fuste, coroa com 3 (ou 5) globos leitosos em bracos curvos e um no alto"""
    _base(M, x, z, y, 0.3)
    M.m('metal')
    M.cyl(x, z, 0.085, y + 0.85, y + 3.6, IRON, 8, False, 0.065)
    M.cyl(x, z, 0.12, y + 2.2, y + 2.28, IRON2, 8)
    M.cyl(x, z, 0.14, y + 3.6, y + 3.7, IRON2, 8)
    for k in range(n):
        a = 2 * math.pi * k / n + 0.3
        ex, ez = x + math.cos(a) * 0.55, z + math.sin(a) * 0.55
        prev = (x, y + 3.65, z)
        for j in range(1, 6):
            t = j / 5; px, pz = x + math.cos(a) * 0.55 * t, z + math.sin(a) * 0.55 * t; py = y + 3.65 + 0.25 * math.sin(t * math.pi * 0.5) - 0.1 * t
            M.quad((prev[0], prev[1] - 0.025, prev[2]), (px, py - 0.025, pz), (px, py + 0.025, pz), (prev[0], prev[1] + 0.025, prev[2]), IRON, (-math.sin(a), 0, math.cos(a)))
            prev = (px, py, pz)
        M.cyl(ex, ez, 0.07, prev[1], prev[1] + 0.08, IRON2, 8)
        M.m('liso'); M.sphere(ex, prev[1] + 0.28, ez, 0.22, GLOW, 10, 6); M.m('metal')
    M.cyl(x, z, 0.06, y + 3.7, y + 3.95, IRON, 8)
    M.m('liso'); M.sphere(x, y + 4.2, z, 0.25, GLOW, 10, 6); M.m('metal')
    M.sphere(x, y + 4.47, z, 0.04, IRON, 5, 3)


def modern(M, x, z, y):
    """luminaria contemporanea de parque: fuste quadrado de aco escovado, faixa de LED vertical e cabeca em disco"""
    M.m('concreto'); M.box(x - 0.22, x + 0.22, y, y + 0.12, z - 0.22, z + 0.22, (200, 198, 192))
    M.m('metal')
    M.box(x - 0.07, x + 0.07, y + 0.12, y + 4.0, z - 0.07, z + 0.07, (150, 156, 162))
    M.m('liso'); M.box(x + 0.07, x + 0.085, y + 0.6, y + 3.4, z - 0.02, z + 0.02, GLOW)
    M.m('metal')
    M.cyl(x, z, 0.45, y + 4.0, y + 4.1, (150, 156, 162), 16)
    M.cyl(x, z, 0.38, y + 4.1, y + 4.16, (120, 126, 132), 16)
    M.m('liso'); M.cyl(x, z, 0.4, y + 3.97, y + 4.0, GLOW, 16, True)


def bollard(M, x, z, y):
    """balizador baixo de jardim (cilindro com aro de luz)"""
    M.m('metal'); M.cyl(x, z, 0.09, y, y + 0.7, IRON2, 8)
    M.m('liso'); M.cyl(x, z, 0.085, y + 0.55, y + 0.65, GLOW, 8, False)
    M.m('metal'); M.cyl(x, z, 0.11, y + 0.7, y + 0.76, IRON, 8)


STYLES = ('vitoriano', 'vitoriano2', 'globos', 'moderno')


def post(M, x, z, y, style):
    if style == 'vitoriano': victorian(M, x, z, y, 1)
    elif style == 'vitoriano2': victorian(M, x, z, y, 2)
    elif style == 'globos': globes(M, x, z, y, 3)
    elif style == 'globos5': globes(M, x, z, y, 5)
    else: modern(M, x, z, y)
