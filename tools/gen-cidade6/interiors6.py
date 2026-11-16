"""Cidade 6 - interiores dos predios das profissoes (salas planejadas com rooms6.Room).

Planta padrao (servicos/escritorios): recepcao na frente; nos fundos a sala principal (esquerda) e a coluna de apoio
(direita) com copa e banheiros. Lojas e galpoes tem planta propria. Toda porta tem folha de verdade e area livre;
todo movel e colocado com Room.put (cabe inteiro, nao encosta em outro, nao tampa porta)."""
import math
from mesh import shade
import jobs6
from jobs6 import J, GLOW, WOOD, WOOD_L, STEEL, DARK, gondola, cart, fire_truck, garbage_truck, moto
from rooms6 import Room, wall

Y0 = jobs6.Y0
HH = jobs6.HH
WALLC = (244, 242, 236)


# ==================================================================== moveis com pegada (para Room.put)
def shelf(R, side, pos, w=1.8, h=2.0, dp=0.42, col=WOOD, items='livros'):
    (u, v, rot), fp = R.on_wall(side, pos, w, dp)
    return R.put(*fp, lambda: R.j.shelf(u, v, rot, w, h, dp, col, items))


def counter(R, side, pos, w, dp=0.62, col=(240, 236, 228), top=(70, 70, 76), h=0.92):
    (u, v, rot), fp = R.on_wall(side, pos, w, dp)
    return R.put(*fp, lambda: R.j.counter(u, v, rot, w, dp, col, top, h))


def seats(R, side, pos, n=3, col=(40, 120, 180)):
    w = n * 0.58
    (u, v, rot), fp = R.on_wall(side, pos, w, 0.55)
    return R.put(*fp, lambda: R.j.seats_row(u, v, rot, n, col))


def sofa(R, side, pos, w=2.0, col=(90, 110, 140)):
    (u, v, rot), fp = R.on_wall(side, pos, w, 0.95)
    return R.put(*fp, lambda: R.j.sofa(u, v, rot, w, col))


def lockers(R, side, pos, n=5, col=(110, 130, 150)):
    w = n * 0.42
    (u, v, rot), fp = R.on_wall(side, pos, w, 0.52)
    return R.put(*fp, lambda: R.j.lockers(u, v, rot, n, col))


def plant(R, u, v, s=1.0):
    r_ = 0.3 * s
    return R.put(u - r_, u + r_, v - r_, v + r_, lambda: R.j.plant(u, v, s))


def corners(R, s=1.0, which='ab'):
    pts = {'a': (R.u0 + 0.4, R.v0 + 0.4), 'b': (R.u1 - 0.4, R.v0 + 0.4), 'c': (R.u0 + 0.4, R.v1 - 0.4), 'd': (R.u1 - 0.4, R.v1 - 0.4)}
    for k in which: plant(R, *pts[k], s)


def workstation(R, u, v, rot, col=(60, 70, 90), w=1.5):
    """mesa com computador e cadeira: rot 0 = a pessoa senta do lado -v e olha para +v"""
    fp = {0: (u - w / 2, u + w / 2, v - 1.2, v + 0.4), 2: (u - w / 2, u + w / 2, v - 0.4, v + 1.2),
          1: (u - 0.4, u + 1.2, v - w / 2, v + w / 2), 3: (u - 1.2, u + 0.4, v - w / 2, v + w / 2)}[rot]
    def go():
        R.j.desk(u, v, rot, w, 0.75)
        G = R.j.sub(u, v, rot); x, z = G.xz(0, -0.8); R.j.chair_at(x, z, rot, col)
    return R.put(*fp, go)


def table_chairs(R, u, v, w=1.6, dp=0.9, n=2, col=WOOD_L, ccol=(60, 60, 70)):
    """mesa com cadeiras dos dois lados (ao longo de u)"""
    fp = (u - w / 2 - 0.1, u + w / 2 + 0.1, v - dp / 2 - 0.75, v + dp / 2 + 0.75)
    def go():
        R.j.table(u, v, 0, w, dp, col)
        for k in range(n):
            cu = u - w / 2 + w * (k + 0.5) / n
            G = R.j.sub(cu, v - dp / 2 - 0.35, 2); J(R.j.L, G).chair(0, 0, 0, ccol, False)
            G = R.j.sub(cu, v + dp / 2 + 0.35, 0); J(R.j.L, G).chair(0, 0, 0, ccol, False)
    return R.put(*fp, go)


def round_set(R, u, v, r=0.45, n=3, ccol=(200, 60, 50)):
    e = r + 0.7
    return R.put(u - e, u + e, v - e, v + e, lambda: R.j.round_table(u, v, r, (248, 248, 246), n, ccol))


def wall_items(R, side, pos, kind, **kw):
    """itens pendurados (quadro, TV, relogio, lousa): nao ocupam o chao"""
    j = R.j
    rot = {'s': 0, 'n': 2, 'w': 1, 'e': 3}[side]
    if side == 's': u, v = pos, R.v1 - 0.02
    elif side == 'n': u, v = pos, R.v0 + 0.02
    elif side == 'w': u, v = R.u0 + 0.02, pos
    else: u, v = R.u1 - 0.02, pos
    if kind == 'art': j.art(u, v, rot, kw.get('w', 1.0), kw.get('h', 0.7), kw.get('y', 1.6))
    elif kind == 'tv': j.tv(u, v, rot, kw.get('w', 1.3), kw.get('y', 1.9))
    elif kind == 'clock': j.clock(u, v, rot, kw.get('y', 2.9))
    elif kind == 'board': j.board(u, v, rot, kw.get('w', 3.0), kw.get('h', 1.2), kw.get('col', (40, 70, 50)))


# ==================================================================== copa e banheiro
def restroom(R, unisex=False):
    """banheiro: piso de ceramica com borda, 1-2 boxes com divisoria e porta, vaso, bancada com cubas e espelho"""
    j = R.j
    j.bx(R.u0, R.u1, R.v0, R.v1, Y0 + 0.012, Y0 + 0.022, (228, 232, 236), 'paver')
    nst = 2 if R.w > 2.7 else 1; sw = min(1.25, (R.w - 0.1) / nst)
    for k in range(nst):
        a = R.u1 - (k + 1) * sw
        j.bx(a, a + 0.04, R.v1 - 1.5, R.v1, Y0 + 0.15, Y0 + 2.0, (196, 206, 216), 'liso')        # divisoria
        j.bx(a + 0.04, a + sw - 0.04, R.v1 - 1.52, R.v1 - 1.5, Y0 + 2.0, Y0 + 2.04, (196, 206, 216), 'liso')
        j.bx(a + 0.05, a + 0.09, R.v1 - 1.5 - 0.6, R.v1 - 1.5, Y0 + 0.15, Y0 + 1.95, (210, 220, 228), 'liso')   # porta do box aberta
        cu = a + sw / 2
        j.cyl(cu, R.v1 - 0.45, 0.2, Y0 + 0.02, Y0 + 0.42, (252, 252, 252), 'ceramica', 14)
        j.bx(cu - 0.2, cu + 0.2, R.v1 - 0.18, R.v1 - 0.03, Y0 + 0.42, Y0 + 0.82, (252, 252, 252), 'ceramica')
        j.bx(cu + 0.35, cu + 0.45, R.v1 - 0.06, R.v1 - 0.02, Y0 + 0.75, Y0 + 0.9, (240, 240, 240), 'liso')      # papel
        R.take(a, a + sw, R.v1 - 1.5, R.v1)
    # bancada com cubas na parede w (ou n se estreito)
    bw = min(1.6, R.d - 2.0)
    if bw > 0.8:
        (u, v, rot), fp = R.on_wall('w', R.v0 + 0.3 + bw / 2, bw, 0.55)
        if R.fits(*fp):
            j.counter(u, v, rot, bw, 0.55, (236, 236, 238), (220, 220, 224), 0.85)
            for k in range(2 if bw > 1.2 else 1):
                vv = R.v0 + 0.3 + bw * (k + 0.5) / (2 if bw > 1.2 else 1)
                j.cyl(R.u0 + 0.28, vv, 0.17, Y0 + 0.86, Y0 + 0.88, (250, 250, 250), 'ceramica', 12)
                j.cyl(R.u0 + 0.08, vv, 0.02, Y0 + 0.86, Y0 + 1.1, (200, 200, 204), 'metal', 6)
            j.bx(R.u0 + 0.01, R.u0 + 0.03, R.v0 + 0.35, R.v0 + 0.25 + bw, Y0 + 1.15, Y0 + 2.0, (200, 220, 232), 'vidro')   # espelho
            R.take(*fp)
    j.bx(R.u1 - 0.03, R.u1 - 0.01, R.v0 + 0.3, R.v0 + 0.6, Y0 + 1.2, Y0 + 1.6, (240, 240, 240), 'liso')          # papeleira


def pantry(R):
    """copa: bancada com pia e armario aereo, geladeira, micro-ondas, cafeteira, mesinha com cadeiras"""
    j = R.j
    side = 's'
    bw = min(R.w - 1.1, 2.8)
    if bw >= 1.2:
        pos = R.u0 + 0.2 + bw / 2
        (u, v, rot), fp = R.on_wall(side, pos, bw, 0.62)
        if R.fits(*fp):
            j.counter(u, v, rot, bw, 0.62, (236, 232, 222), (90, 90, 96), 0.92)
            j.bx(fp[0], fp[1], R.v1 - 0.36, R.v1 - 0.02, Y0 + 1.55, Y0 + 2.25, (236, 232, 222), 'liso')
            j.bx(fp[0] + 0.3, fp[0] + 0.75, R.v1 - 0.5, R.v1 - 0.12, Y0 + 0.92, Y0 + 1.2, (40, 40, 44))           # micro-ondas
            j.bx(fp[0] + 0.95, fp[0] + 1.15, R.v1 - 0.42, R.v1 - 0.15, Y0 + 0.92, Y0 + 1.27, (30, 30, 30))         # cafeteira
            j.bx(fp[1] - 0.7, fp[1] - 0.2, R.v1 - 0.5, R.v1 - 0.12, Y0 + 0.92, Y0 + 0.93, (200, 204, 208), 'metal')   # pia
            R.take(*fp)
    (u, v, rot), fp = R.on_wall('e', R.v1 - 0.45, 0.7, 0.7)
    R.put(*fp, lambda: (j.bx(fp[0], fp[1], fp[2], fp[3], Y0, Y0 + 1.85, (232, 232, 234), 'metal'), j.bx(fp[0] - 0.01, fp[0], fp[2] + 0.1, fp[2] + 0.14, Y0 + 0.9, Y0 + 1.6, (160, 160, 164), 'metal')))
    if R.w > 2.2 and R.d > 2.6: round_set(R, R.cu, R.v0 + (R.d - 0.62) / 2, 0.45, 3, (120, 160, 190))


def lights(j, R, step=3.0):
    nu = max(1, int(R.w / step)); nv = max(1, int(R.d / step))
    for a in range(nu):
        for b in range(nv): j.light(R.u0 + R.w * (a + 0.5) / nu, R.v0 + R.d * (b + 0.5) / nv, 1.1, 0.55)


# ==================================================================== montagem
def build(j, jid, w, d, spec, door_u, garage_doors=()):
    sign, style, floors, _, _, fl, wall_c, acc = spec
    fm = {'ceramica': 'paver', 'madeira': 'madeira', 'concreto': 'concreto', 'pedra': 'pedra'}[fl]
    fcol = {'ceramica': (232, 230, 226), 'madeira': (176, 132, 90), 'concreto': (196, 194, 190), 'pedra': (228, 222, 208)}[fl]
    j.bx(0.15, w - 0.15, 0.15, d - 0.15, Y0 - 0.04, Y0, fcol, fm)
    j.ceiling(0.15, w - 0.15, 0.15, d - 0.15)
    for (a, b, c, e) in ((0.15, w - 0.15, 0.15, 0.2), (0.15, w - 0.15, d - 0.2, d - 0.15), (0.15, 0.2, 0.15, d - 0.15), (w - 0.2, w - 0.15, 0.15, d - 0.15)):
        j.bx(a, b, c, e, Y0, Y0 + 0.1, (90, 84, 78), 'liso')                                   # rodape
    U0, U1, V0, V1 = 0.2, w - 0.2, 0.2, d - 0.2
    if jid in ('bombeiro', 'mecanico', 'lixeiro', 'entregador'): return garage(j, jid, w, d, acc, door_u, garage_doors)
    if jid in ('repositor', 'frentista'): return market(j, jid, w, d, acc, door_u)
    if jid == 'atendente': return diner(j, w, d, acc, door_u)
    # ---- planta padrao
    vf = round(min(d * 0.4, 7.0), 2)
    ua = round(w * 0.64, 2)
    vm = round(vf + (d - vf) * 0.5, 2)
    pm = round((U0 + ua) / 2, 2); cs = round((ua + U1) / 2, 2)
    main_door = {'secretario': 'vidro', 'engenheiro': 'vidro', 'programador': 'vidro', 'empresario': 'dupla', 'advogado': 'madeira',
                 'juiz': 'dupla', 'policial': 'madeira', 'professor': 'madeira', 'enfermeiro': 'madeira', 'medico': 'dupla', 'diarista': 'cortafogo'}.get(jid, 'madeira')
    wall(j, 'u', vf, U0, U1, [(pm, 1.8 if main_door == 'dupla' else 1.0, main_door), (cs, 0.9, 'madeira')], glass=style == 'vidro')
    wall(j, 'v', ua, vf, V1, [])
    wall(j, 'u', vm, ua, U1, [(cs, 0.85, 'banheiro')])
    Rh = Room(j, U0, U1, V0, vf - 0.07, 'recepcao').door('n', door_u, 2.4).door('s', pm, 1.8).door('s', cs, 0.9)
    Rm = Room(j, U0, ua - 0.07, vf + 0.07, V1, 'principal').door('n', pm, 1.8)
    Rc = Room(j, ua + 0.07, U1, vf + 0.07, vm - 0.07, 'copa').door('n', cs, 0.9).door('s', cs, 0.85)
    Rb = Room(j, ua + 0.07, U1, vm + 0.07, V1, 'banheiro').door('n', cs, 0.85)
    for R in (Rh, Rm, Rc, Rb): lights(j, R)
    reception(Rh, jid, acc, door_u)
    pantry(Rc); restroom(Rb)
    MAIN.get(jid, offices)(Rm, jid, acc)


def reception(R, jid, acc, door_u):
    j = R.j
    # balcao paralelo a fachada, de um lado da entrada (nunca na frente das portas)
    cw = min(3.2, R.w * 0.3)
    for cu in (door_u + R.w * 0.27, door_u - R.w * 0.27):
        fp = (cu - cw / 2 - 0.2, cu + cw / 2 + 0.2, R.v0 + 1.7, R.v0 + 3.2)
        if R.fits(*fp):
            j.counter(cu, R.v0 + 2.0, 0, cw, 0.62, (246, 244, 238), shade(acc, -10), 1.05)
            j.bx(cu - cw / 2 + 0.1, cu + cw / 2 - 0.1, R.v0 + 1.66, R.v0 + 1.675, Y0 + 0.4, Y0 + 0.85, acc, 'liso')
            j.register(cu - cw / 2 + 0.5, R.v0 + 2.0, 0)
            G = j.sub(cu, R.v0 + 2.75, 0); J(j.L, G).chair(0, 0, 0, (50, 54, 60))
            R.take(*fp); break
    for pos in (R.u0 + 1.2, R.u1 - 1.2):
        if abs(pos - door_u) > 2.4: seats(R, 'n', pos, 3, shade(acc, 15))
    seats(R, 'w', R.cv, 3, shade(acc, 15))
    corners(R, 1.1, 'abcd')
    wall_items(R, 'e', R.cv, 'art', w=1.4, h=0.9)
    wall_items(R, 'w', R.cv, 'tv', w=1.2, y=2.0)
    wall_items(R, 's', door_u, 'clock', y=2.9)
    j.rug(door_u - 1.3, door_u + 1.3, R.v0 + 0.3, R.v0 + 1.5, shade(acc, 45))
    (u, v, rot), fp = R.on_wall('e', R.v0 + 0.9, 0.4, 0.4)
    R.put(*fp, lambda: j.water_cooler(u, v))


# ---------------------------------------------------------------- salas principais
def offices(R, jid, acc):
    j = R.j
    col = acc if jid == 'programador' else (60, 70, 90)
    # estantes no fundo, mesas em fileiras de frente para o fundo, plantas
    p = R.u0 + 1.2
    while p + 0.9 < R.u1 - 0.3:
        shelf(R, 's', p, 1.8, 2.0, 0.42, WOOD, 'pastas' if jid not in ('advogado', 'empresario') else 'livros'); p += 2.2
    v = R.v0 + 2.0
    while v < R.v1 - 1.6:
        u = R.u0 + 1.2
        while u < R.u1 - 0.8:
            workstation(R, u, v, 0, col); u += 2.0
        v += 2.4
    if jid in ('advogado', 'empresario'): table_chairs(R, R.cu, R.v1 - 2.2, 2.4, 1.0, 3, (110, 76, 50), (60, 40, 30))
    if jid == 'programador':
        for k in range(2): (u_, v_, rot), fp = R.on_wall('e', R.v1 - 0.6 - k * 0.75, 0.62, 0.62); R.put(*fp, lambda u_=u_, v_=v_, fp=fp: server(j, fp))
    corners(R, 1.0, 'abd')
    wall_items(R, 'w', R.cv, 'art', w=1.6, h=1.0)


def server(j, fp):
    j.bx(fp[0], fp[1], fp[2], fp[3], Y0, Y0 + 2.0, (30, 32, 36), 'metal')
    for q in range(10): j.bx(fp[0] - 0.01, fp[0], fp[2] + 0.06, fp[3] - 0.06, Y0 + 0.25 + q * 0.16, Y0 + 0.27 + q * 0.16, (60, 220, 120), 'liso')


def classroom(R, jid, acc):
    j = R.j
    wall_items(R, 's', R.cu, 'board', w=min(4.0, R.w - 1.4), h=1.2)
    (u, v, rot), fp = R.on_wall('s', R.cu, 1.5, 1.6)
    def teacher():
        j.desk(R.cu, R.v1 - 1.25, 2, 1.4, 0.7, False, WOOD); G = j.sub(R.cu, R.v1 - 0.55, 0); J(j.L, G).chair(0, 0, 0)
    R.put(R.cu - 0.8, R.cu + 0.8, R.v1 - 1.7, R.v1, teacher)
    cols = min(6, int((R.w - 2.0) / 1.25)); rows = min(5, int((R.d - 3.4) / 1.35))
    u_0 = R.cu - (cols - 1) * 1.25 / 2; v_0 = R.v1 - 2.6 - (rows - 1) * 1.35
    for i in range(cols):
        for k in range(rows):
            u = u_0 + i * 1.25; v = v_0 + k * 1.35
            R.put(u - 0.42, u + 0.42, v - 0.95, v + 0.3, lambda u=u, v=v: (j.table(u, v, 0, 0.75, 0.5, (196, 164, 116), 0.72), J(j.L, j.sub(u, v - 0.55, 0)).chair(0, 0, 2, (60, 120, 200), False)))
    shelf(R, 'w', R.cv, 1.4, 1.5, 0.36, (240, 200, 90), 'livros')
    wall_items(R, 'e', R.cv, 'art', w=1.6, h=1.0, y=1.7)


def police(R, jid, acc):
    j = R.j
    # duas celas no fundo (grade com porta), mesas dos investigadores na frente
    cw = R.w / 2; cv0 = R.v1 - 2.6
    for k in range(2):
        ca = R.u0 + k * cw
        if k: wall(j, 'v', ca, cv0, R.v1, [], col=(214, 212, 208))
        jail(j, ca + 0.06, ca + cw - 0.06, cv0, R.v1)
        R.take(ca, ca + cw, cv0 - 0.6, R.v1)
    workstation(R, R.u0 + 1.2, R.v0 + 1.8, 0, (30, 60, 140)); workstation(R, R.u0 + 3.4, R.v0 + 1.8, 0, (30, 60, 140))
    lockers(R, 'e', R.v0 + 1.6, 4, (60, 80, 120))
    wall_items(R, 'w', R.v0 + 1.6, 'board', w=1.8, h=1.0, col=(240, 240, 236))


def jail(j, a, b, c, e):
    """cela: grade com porta (aberta), banco de concreto, colchao, vaso de inox"""
    q = a + 0.15; mid = (a + b) / 2
    while q < b - 0.1:
        if abs(q - mid) > 0.45: j.cyl(q, c, 0.025, Y0, Y0 + 2.6, STEEL, 'metal', 6)
        q += 0.15
    j.bx(a, b, c - 0.03, c + 0.03, Y0 + 2.6, Y0 + 2.7, STEEL, 'metal'); j.bx(a, b, c - 0.03, c + 0.03, Y0 + 0.02, Y0 + 0.08, STEEL, 'metal')
    for qq in range(5): j.cyl(mid + 0.45, c + 0.1 + qq * 0.15, 0.022, Y0, Y0 + 2.5, STEEL, 'metal', 6)      # porta da grade aberta
    j.solid(a, mid - 0.45, c - 0.05, c + 0.05); j.solid(mid + 0.45, b, c - 0.05, c + 0.05)
    j.bx(a + 0.2, b - 0.2, e - 0.7, e - 0.05, Y0, Y0 + 0.45, (170, 172, 176), 'concreto')
    j.bx(a + 0.3, a + 1.6, e - 0.65, e - 0.1, Y0 + 0.45, Y0 + 0.55, (90, 110, 140), 'liso')
    j.cyl(b - 0.45, c + 0.6, 0.2, Y0, Y0 + 0.42, (200, 204, 208), 'metal', 12)
    j.solid(a + 0.2, b - 0.2, e - 0.7, e - 0.05)


def clinic(R, jid, acc):
    j = R.j
    n = max(1, int((R.w - 0.4) / 2.5))
    for k in range(n):
        mu = R.u0 + 0.3 + 2.5 * (k + 0.5)
        if not R.fits(mu - 0.55, mu + 0.55, R.v1 - 2.2, R.v1): continue
        bed(j, mu, R.v1); R.take(mu - 0.55, mu + 1.25, R.v1 - 2.2, R.v1)
        if k < n - 1: j.bx(mu + 1.22, mu + 1.24, R.v1 - 2.4, R.v1 - 0.1, Y0 + 0.3, Y0 + 2.1, (150, 210, 200), 'liso')     # cortina
    workstation(R, R.u0 + 1.2, R.v0 + 1.8, 0, acc)
    shelf(R, 'e', R.v0 + 1.4, 1.4, 1.8, 0.42, (240, 240, 240), 'caixas')
    corners(R, 0.9, 'a')


def bed(j, u, v1):
    """leito: estrutura metalica, colchao, lencol, travesseiro, grades, suporte de soro e monitor"""
    j.bx(u - 0.48, u + 0.48, v1 - 2.15, v1 - 0.2, Y0 + 0.45, Y0 + 0.6, (230, 232, 236), 'metal')
    j.bx(u - 0.45, u + 0.45, v1 - 2.1, v1 - 0.25, Y0 + 0.6, Y0 + 0.66, (246, 248, 250), 'liso')
    j.bx(u - 0.44, u + 0.44, v1 - 1.6, v1 - 0.95, Y0 + 0.66, Y0 + 0.69, (150, 196, 224), 'liso')
    j.bx(u - 0.35, u + 0.35, v1 - 0.65, v1 - 0.3, Y0 + 0.66, Y0 + 0.78, (252, 252, 252), 'liso')
    j.bx(u - 0.48, u + 0.48, v1 - 0.22, v1 - 0.16, Y0 + 0.45, Y0 + 1.1, (200, 204, 210), 'metal')
    for (a, b) in ((u - 0.44, v1 - 2.1), (u + 0.44, v1 - 2.1), (u - 0.44, v1 - 0.25), (u + 0.44, v1 - 0.25)): j.cyl(a, b, 0.025, Y0, Y0 + 0.45, STEEL, 'metal', 6)
    j.cyl(u + 0.85, v1 - 0.5, 0.02, Y0, Y0 + 2.0, STEEL, 'metal', 6); j.bx(u + 0.78, u + 0.92, v1 - 0.52, v1 - 0.48, Y0 + 1.7, Y0 + 1.95, (220, 240, 250), 'liso')
    j.bx(u - 0.95, u - 0.65, v1 - 0.6, v1 - 0.3, Y0, Y0 + 1.1, (200, 204, 210), 'metal'); j.bx(u - 0.94, u - 0.66, v1 - 0.61, v1 - 0.6, Y0 + 0.75, Y0 + 1.0, (60, 200, 120), 'liso')
    j.solid(u - 0.5, u + 0.5, v1 - 2.15, v1 - 0.2)


def court(R, jid, acc):
    j = R.j
    cu = R.cu
    R.put(cu - 2.6, cu + 2.6, R.v1 - 2.3, R.v1, lambda: bench_judge(j, cu, R.v1))
    for s_ in (-1, 1):
        tu = cu + s_ * 1.9
        R.put(tu - 0.9, tu + 0.9, R.v1 - 4.6, R.v1 - 3.2, lambda tu=tu: (j.table(tu, R.v1 - 3.7, 0, 1.6, 0.7, (120, 84, 56)), J(j.L, j.sub(tu - 0.45, R.v1 - 4.3, 0)).chair(0, 0, 2, (60, 40, 30)), J(j.L, j.sub(tu + 0.45, R.v1 - 4.3, 0)).chair(0, 0, 2, (60, 40, 30))))
    v = R.v0 + 1.6
    while v < R.v1 - 5.4:
        for s_ in (-1, 1):
            a, b = (R.u0 + 0.4, cu - 0.8) if s_ < 0 else (cu + 0.8, R.u1 - 0.4)
            R.put(a, b, v - 0.25, v + 0.3, lambda a=a, b=b, v=v: (j.bx(a, b, v - 0.2, v + 0.2, Y0, Y0 + 0.45, (120, 84, 56), 'liso'), j.bx(a, b, v + 0.2, v + 0.26, Y0 + 0.45, Y0 + 0.95, (120, 84, 56), 'liso'), j.solid(a, b, v - 0.2, v + 0.26)))
        v += 1.1
    for s_ in (-1, 1): j.cyl(cu + s_ * 3.2, R.v1 - 0.4, 0.03, Y0, Y0 + 2.4, (200, 170, 80), 'metal', 6); j.bx(cu + s_ * 3.2, cu + s_ * 3.2 + 0.02, R.v1 - 0.42, R.v1 - 0.38, Y0 + 1.5, Y0 + 2.3, (30, 110, 60), 'liso')


def bench_judge(j, cu, v1):
    j.bx(cu - 2.6, cu + 2.6, v1 - 2.2, v1 - 0.05, Y0, Y0 + 0.45, (120, 84, 56), 'madeira')
    j.bx(cu - 2.3, cu + 2.3, v1 - 2.15, v1 - 1.65, Y0 + 0.45, Y0 + 1.5, (110, 76, 50), 'liso'); j.bx(cu - 2.4, cu + 2.4, v1 - 2.2, v1 - 1.6, Y0 + 1.5, Y0 + 1.58, (90, 60, 40), 'liso')
    G = j.sub(cu, v1 - 1.0, 0); J(j.L, G).chair(0, 0, 0, (120, 30, 30))
    j.bx(cu - 0.4, cu + 0.4, v1 - 0.45, v1 - 0.3, Y0 + 0.45, Y0 + 1.9, (120, 30, 30), 'liso')
    j.bx(cu - 0.9, cu + 0.9, v1 - 0.03, v1 - 0.01, Y0 + 2.1, Y0 + 3.2, (230, 200, 120), 'liso')
    j.solid(cu - 2.6, cu + 2.6, v1 - 2.2, v1 - 0.05)


def cleaning(R, jid, acc):
    j = R.j
    p = R.u0 + 1.1
    while p < R.u1 - 1.0: shelf(R, 's', p, 1.8, 2.0, 0.45, (200, 205, 210), 'caixas'); p += 2.1
    for k in range(3):
        cu = R.u0 + 1.0 + k * 1.3
        R.put(cu - 0.4, cu + 0.4, R.v0 + 0.6, R.v0 + 1.4, lambda cu=cu: (j.bx(cu - 0.35, cu + 0.35, R.v0 + 0.7, R.v0 + 1.3, Y0 + 0.1, Y0 + 0.9, (64, 170, 200), 'metal'), j.cyl(cu - 0.15, R.v0 + 1.0, 0.18, Y0 + 0.9, Y0 + 1.2, (240, 200, 40), 'liso', 10), j.cyl(cu + 0.2, R.v0 + 1.0, 0.02, Y0 + 0.9, Y0 + 1.7, STEEL, 'metal', 6)))
    table_chairs(R, R.cu + 0.6, R.cv + 0.4, 1.6, 0.8, 2)
    lockers(R, 'e', R.cv, 4, (64, 170, 200))


MAIN = {'professor': classroom, 'policial': police, 'enfermeiro': clinic, 'medico': clinic, 'juiz': court, 'diarista': cleaning}


# ---------------------------------------------------------------- planta propria: lanchonete, mercado, garagens
def diner(j, w, d, acc, door_u):
    U0, U1, V0, V1 = 0.2, w - 0.2, 0.2, d - 0.2
    vf = round(d * 0.5, 2); ua = round(w * 0.68, 2)
    kd = round(U0 + 1.0, 2)                                             # porta da cozinha (canto esquerdo)
    wall(j, 'u', vf, U0, ua, [(kd, 0.95, 'cozinha')])
    wall(j, 'u', vf, ua, U1, [((ua + U1) / 2, 0.85, 'banheiro')])
    wall(j, 'v', ua, vf, V1, [])
    S = Room(j, U0, U1, V0, vf - 0.07, 'salao').door('n', door_u, 2.4).door('s', kd, 0.95).door('s', (ua + U1) / 2, 0.85)
    K = Room(j, U0, ua - 0.07, vf + 0.07, V1, 'cozinha').door('n', kd, 0.95)
    Bn = Room(j, ua + 0.07, U1, vf + 0.07, V1, 'banheiro').door('n', (ua + U1) / 2, 0.85)
    for R in (S, K, Bn): lights(j, R)
    # balcao de atendimento junto da parede da cozinha, com passa-pratos, deixando a porta livre
    a = kd + 1.2; b = ua - 0.4
    if b - a > 2.0:
        S.put(a, b, vf - 1.65, vf - 0.07, lambda: None)
        j.counter((a + b) / 2, vf - 0.45, 0, b - a, 0.7, (246, 238, 220), acc, 1.05)
        u = a + 0.45
        while u < b - 0.3:
            j.cyl(u, vf - 1.15, 0.21, Y0 + 0.72, Y0 + 0.78, acc, 'liso', 12); j.cyl(u, vf - 1.15, 0.04, Y0, Y0 + 0.72, STEEL, 'metal', 6); u += 0.8
        j.register(b - 0.6, vf - 0.45, 0)
        for k in range(3): j.bx(a + 0.3 + k * (b - a - 0.6) / 3, a + 0.3 + (k + 0.85) * (b - a - 0.6) / 3, vf - 0.075, vf - 0.067, Y0 + 2.3, Y0 + 3.0, GLOW, 'liso')
    # mesas: cabines nas laterais e mesas redondas no meio
    for (side, pos) in (('w', V0 + 1.4), ('e', V0 + 1.4)):
        booth(S, side, pos, acc)
    u = S.u0 + 2.6
    while u < S.u1 - 2.4:
        if abs(u - door_u) > 2.0: round_set(S, u, S.v0 + 3.0, 0.42, 3, acc)
        u += 2.6
    corners(S, 1.0, 'ab')
    wall_items(S, 'w', vf - 1.0, 'tv', w=1.1, y=2.1)
    # cozinha: chapa, fogao, fritadeira e coifa no fundo; pia e geladeiras na lateral; estoque
    eq = [(1.2, 'chapa'), (0.9, 'fogao'), (0.7, 'frita'), (1.2, 'pia')]
    p = K.u0 + 0.3
    for (wq, kind) in eq:
        (u, v, rot), fp = K.on_wall('s', p + wq / 2, wq, 0.75)
        if K.put(*fp, lambda fp=fp, kind=kind: kitchen_unit(j, fp, kind)): p += wq + 0.02
    j.bx(K.u0 + 0.3, p, K.v1 - 0.8, K.v1 - 0.02, Y0 + 2.3, Y0 + 2.75, (200, 202, 206), 'metal')         # coifa
    for k in range(2):
        (u, v, rot), fp = K.on_wall('e', K.v1 - 0.5 - k * 0.85, 0.8, 0.75)
        K.put(*fp, lambda fp=fp: (j.bx(fp[0], fp[1], fp[2], fp[3], Y0, Y0 + 2.0, (220, 222, 226), 'metal'), j.bx(fp[0] - 0.01, fp[0], fp[2] + 0.06, fp[2] + 0.1, Y0 + 0.9, Y0 + 1.6, (150, 150, 154), 'metal')))
    shelf(K, 'w', K.cv, 1.6, 2.0, 0.42, (200, 200, 204), 'caixas')
    K.put(K.cu - 0.7, K.cu + 0.7, K.cv - 0.4, K.cv + 0.4, lambda: (j.bx(K.cu - 0.7, K.cu + 0.7, K.cv - 0.4, K.cv + 0.4, Y0, Y0 + 0.9, (210, 212, 216), 'metal'), j.solid(K.cu - 0.7, K.cu + 0.7, K.cv - 0.4, K.cv + 0.4)))   # mesa de preparo
    restroom(Bn)


def booth(R, side, pos, acc):
    """cabine de lanchonete encostada na parede: mesa e dois bancos estofados"""
    j = R.j
    (u, v, rot), fp = R.on_wall(side, pos, 1.9, 1.4)
    def go():
        a, b, c, e = fp
        if side in ('w', 'e'):
            t0, t1 = (a, a + 0.75) if side == 'w' else (b - 0.75, b)
            j.bx(t0, t1, c + 0.65, e - 0.65, Y0 + 0.72, Y0 + 0.76, (250, 250, 246), 'liso'); j.cyl((t0 + t1) / 2, (c + e) / 2, 0.05, Y0, Y0 + 0.72, STEEL)
            for (s0, s1) in ((c, c + 0.5), (e - 0.5, e)):
                j.bx(a, b, s0, s1, Y0, Y0 + 0.45, acc, 'liso')
                bk = (s0, s0 + 0.12) if s0 == c else (s1 - 0.12, s1)
                j.bx(a, b, bk[0], bk[1], Y0 + 0.45, Y0 + 1.15, shade(acc, -15), 'liso')
            j.solid(a, b, c, e)
    return R.put(*fp, go)


def kitchen_unit(j, fp, kind):
    a, b, c, e = fp
    j.bx(a, b, c, e, Y0, Y0 + 0.88, (210, 212, 216), 'metal'); j.bx(a - 0.01, b + 0.01, c - 0.01, e, Y0 + 0.88, Y0 + 0.92, (190, 192, 196), 'metal')
    if kind == 'chapa': j.bx(a + 0.05, b - 0.05, c + 0.1, e - 0.1, Y0 + 0.92, Y0 + 0.95, (40, 40, 40), 'metal')
    elif kind == 'fogao':
        for (p, q) in ((0.25, 0.25), (0.65, 0.25), (0.25, 0.5), (0.65, 0.5)): j.cyl(a + (b - a) * p / 0.9, c + q, 0.1, Y0 + 0.92, Y0 + 0.95, (30, 30, 30), 'metal', 10)
    elif kind == 'frita': j.bx(a + 0.08, b - 0.08, c + 0.12, e - 0.12, Y0 + 0.92, Y0 + 0.93, (200, 160, 60), 'liso')
    else: j.bx(a + 0.15, b - 0.15, c + 0.12, e - 0.12, Y0 + 0.92, Y0 + 0.93, (170, 174, 180), 'metal'); j.cyl((a + b) / 2, e - 0.08, 0.02, Y0 + 0.92, Y0 + 1.25, STEEL, 'metal', 6)
    j.solid(a, b, c, e)


def market(j, jid, w, d, acc, door_u):
    U0, U1, V0, V1 = 0.2, w - 0.2, 0.2, d - 0.2
    vs = round(d - 4.6, 2); ub = round(w * 0.62, 2)
    sd = round(U0 + 1.4, 2)
    wall(j, 'u', vs, U0, ub, [(sd, 1.6, 'cortafogo')])
    wall(j, 'u', vs, ub, U1, [((ub + U1) / 2, 0.85, 'banheiro')])
    wall(j, 'v', ub, vs, V1, [])
    L = Room(j, U0, U1, V0, vs - 0.07, 'loja').door('n', door_u, 2.4).door('s', sd, 1.6).door('s', (ub + U1) / 2, 0.85)
    E = Room(j, U0, ub - 0.07, vs + 0.07, V1, 'estoque').door('n', sd, 1.6)
    Bn = Room(j, ub + 0.07, U1, vs + 0.07, V1, 'banheiro').door('n', (ub + U1) / 2, 0.85)
    for R in (L, E, Bn): lights(j, R, 3.4)
    # caixas perto da entrada (dos dois lados da porta)
    for k in range(3):
        for s_ in (-1, 1):
            cu = door_u + s_ * (2.4 + k * 2.2)
            L.put(cu - 0.85, cu + 0.85, L.v0 + 1.6, L.v0 + 3.0, lambda cu=cu: checkout(j, cu, L.v0 + 2.3, acc))
    # gondolas no meio, geladeiras no fundo e hortifruti na lateral
    p = L.u0 + 1.4
    while p < L.u1 - 3.0:
        v0, v1 = L.v0 + 4.4, L.v1 - 2.2
        if v1 - v0 > 2.0: L.put(p - 0.5, p + 0.5, v0, v1, lambda p=p, v0=v0, v1=v1: gondola(j, p, v0, v1), 0.6)
        p += 2.8
    p = L.u0 + 0.8
    while p < L.u1 - 0.8:
        (u, v, rot), fp = L.on_wall('s', p, 1.15, 0.8)
        L.put(*fp, lambda fp=fp: fridge(j, fp))
        p += 1.2
    v = L.v0 + 4.6
    while v < L.v1 - 2.6:
        L.put(L.u1 - 1.8, L.u1 - 0.2, v - 0.6, v + 0.6, lambda v=v: produce(j, L.u1 - 1.0, v), 0.4); v += 1.8
    for k in range(4): L.put(L.u0 + 0.3, L.u0 + 0.95, L.v0 + 0.3 + k * 0.45, L.v0 + 0.7 + k * 0.45, lambda k=k: cart(j, L.u0 + 0.62, L.v0 + 0.5 + k * 0.45))
    p = E.u0 + 1.4
    while p < E.u1 - 1.2: shelf(E, 's', p, 2.4, 2.6, 0.8, (90, 120, 160), 'caixas'); p += 2.8
    restroom(Bn)


def checkout(j, cu, cv, acc):
    j.bx(cu - 0.8, cu + 0.2, cv - 0.4, cv + 0.4, Y0, Y0 + 0.85, (236, 232, 222), 'liso'); j.bx(cu - 0.82, cu + 0.22, cv - 0.42, cv + 0.42, Y0 + 0.85, Y0 + 0.9, (40, 40, 44), 'liso')
    j.bx(cu - 0.75, cu - 0.05, cv - 0.25, cv + 0.25, Y0 + 0.9, Y0 + 0.905, (30, 30, 30), 'liso')          # esteira
    j.register(cu + 0.05, cv, 0)
    j.cyl(cu + 0.55, cv, 0.05, Y0, Y0 + 2.2, (200, 200, 204), 'metal', 8); j.bx(cu + 0.35, cu + 0.75, cv - 0.06, cv + 0.06, Y0 + 2.2, Y0 + 2.5, acc, 'liso')
    G = j.sub(cu + 0.45, cv + 0.15, 0); J(j.L, G).chair(0, 0, 3, (50, 50, 56))
    j.solid(cu - 0.82, cu + 0.22, cv - 0.42, cv + 0.42)


def fridge(j, fp):
    a, b, c, e = fp
    j.bx(a, b, c, e, Y0, Y0 + 2.1, (220, 228, 236), 'metal')
    j.bx(a + 0.04, b - 0.04, c - 0.01, c, Y0 + 0.2, Y0 + 2.0, (190, 220, 235), 'vidro')
    for q in range(4): j.bx(a + 0.1, b - 0.1, c + 0.05, e - 0.1, Y0 + 0.3 + q * 0.42, Y0 + 0.52 + q * 0.42, ((230, 230, 220), (250, 200, 60), (200, 60, 50), (60, 120, 200))[q], 'liso')
    j.bx(a, b, c - 0.02, c, Y0 + 2.0, Y0 + 2.1, GLOW, 'liso')
    j.solid(a, b, c, e)


def produce(j, u, v):
    j.bx(u - 0.8, u + 0.8, v - 0.6, v + 0.6, Y0, Y0 + 0.75, WOOD, 'liso')
    cols = ((230, 60, 40), (250, 180, 40), (90, 170, 60), (240, 220, 80))
    for q in range(10): j.ball(u - 0.6 + (q % 5) * 0.3, v - 0.3 + (q // 5) * 0.6, Y0 + 0.86, 0.12, cols[(int(v) + q // 5) % 4])
    j.solid(u - 0.8, u + 0.8, v - 0.6, v + 0.6)


def garage(j, jid, w, d, acc, door_u, garage_doors):
    U0, U1, V0, V1 = 0.2, w - 0.2, 0.2, d - 0.2
    vb = round(d - 5.0, 2)
    u1_ = round(w * 0.5, 2); u2_ = round(w * 0.75, 2)
    wall(j, 'u', vb, U0, U1, [((U0 + u1_) / 2, 0.95, 'madeira'), ((u1_ + u2_) / 2, 0.85, 'banheiro'), ((u2_ + U1) / 2, 0.9, 'madeira')])
    wall(j, 'v', u1_, vb, V1, []); wall(j, 'v', u2_, vb, V1, [])
    G = Room(j, U0, U1, V0, vb - 0.07, 'garagem').door('n', door_u, 1.6)
    for (a, b, _, _, _) in garage_doors: G.door('n', (a + b) / 2, b - a)
    for p in ((U0 + u1_) / 2, (u1_ + u2_) / 2, (u2_ + U1) / 2): G.door('s', p, 0.95)
    O = Room(j, U0, u1_ - 0.07, vb + 0.07, V1, 'vestiario').door('n', (U0 + u1_) / 2, 0.95)
    Bn = Room(j, u1_ + 0.07, u2_ - 0.07, vb + 0.07, V1, 'banheiro').door('n', (u1_ + u2_) / 2, 0.85)
    C = Room(j, u2_ + 0.07, U1, vb + 0.07, V1, 'copa').door('n', (u2_ + U1) / 2, 0.9)
    for R in (G, O, Bn, C): lights(j, R, 3.4)
    # veiculos alinhados com os portoes (as faixas da porta ficam livres na frente)
    G.keep = [k for k in G.keep if not (k[2] <= G.v0 + 0.01 and (k[1] - k[0]) > 4.0)]
    for (a, b, _, _, _) in garage_doors:
        cu = (a + b) / 2; cv = G.v0 + 1.6 + (G.d - 3.2) / 2
        if jid == 'bombeiro': G.put(cu - 1.3, cu + 1.3, cv - 4.3, cv + 4.3, lambda cu=cu, cv=cv: fire_truck(j, cu, cv))
        elif jid == 'lixeiro': G.put(cu - 1.3, cu + 1.3, cv - 4.1, cv + 4.1, lambda cu=cu, cv=cv: garbage_truck(j, cu, cv))
        elif jid == 'mecanico': G.put(cu - 1.7, cu + 1.7, cv - 2.6, cv + 2.6, lambda cu=cu, cv=cv: lift(j, cu, cv))
        else:
            for k in range(3): G.put(cu - 0.45 + (k - 1) * 1.3, cu + 0.45 + (k - 1) * 1.3, cv - 0.9, cv + 0.9, lambda cu=cu, cv=cv, k=k: moto(j, cu + (k - 1) * 1.3, cv))
    if jid == 'bombeiro':
        p = G.u0 + 0.6
        while p < G.u1 - 0.5:
            (u, v, rot), fp = G.on_wall('s', p, 0.7, 0.3)
            G.put(*fp, lambda u=u, fp=fp: (j.bx(fp[0] + 0.05, fp[1] - 0.05, fp[2], fp[3], Y0 + 1.4, Y0 + 2.2, (210, 180, 60), 'liso'), j.cyl(u, (fp[2] + fp[3]) / 2, 0.17, Y0 + 2.2, Y0 + 2.5, (220, 40, 30), 'liso', 10)))
            p += 0.9
    elif jid == 'mecanico':
        p = G.u0 + 1.6
        while p < G.u1 - 1.4:
            (u, v, rot), fp = G.on_wall('s', p, 2.6, 0.6)
            G.put(*fp, lambda fp=fp: workbench(j, fp)); p += 3.0
    elif jid in ('lixeiro', 'entregador'):
        p = G.u0 + 1.4
        while p < G.u1 - 1.2:
            if jid == 'entregador': shelf(G, 's', p, 2.4, 2.6, 0.8, (220, 120, 40), 'caixas')
            else:
                (u, v, rot), fp = G.on_wall('s', p, 1.2, 1.0)
                G.put(*fp, lambda fp=fp: (j.bx(fp[0], fp[1], fp[2], fp[3], Y0, Y0 + 1.2, ((40, 120, 60), (220, 160, 40), (40, 90, 170))[int(fp[0]) % 3], 'metal'), j.solid(*fp)))
            p += 2.8
    lockers(O, 's', O.cu, max(3, int((O.w - 0.6) / 0.42)), shade(acc, -10))
    (u, v, rot), fp = O.on_wall('w', O.cv, 1.6, 0.5)
    O.put(*fp, lambda: (j.bx(fp[0], fp[1], fp[2], fp[3], Y0, Y0 + 0.45, WOOD, 'liso'), j.solid(*fp)))
    workstation(O, O.cu + 0.8, O.v0 + 1.6, 0, acc)
    restroom(Bn); pantry(C)


def lift(j, cu, cv):
    for s_ in (-1, 1): j.bx(cu + s_ * 1.5 - 0.15, cu + s_ * 1.5 + 0.15, cv - 0.15, cv + 0.15, Y0, Y0 + 2.6, (40, 90, 160), 'metal'); j.solid(cu + s_ * 1.5 - 0.15, cu + s_ * 1.5 + 0.15, cv - 0.15, cv + 0.15)
    for s_ in (-1, 1): j.bx(cu - 1.3, cu + 1.3, cv + s_ * 0.9 - 0.08, cv + s_ * 0.9 + 0.08, Y0 + 1.6, Y0 + 1.7, (60, 60, 64), 'metal')
    x, z = j.F.xz(cu, cv); j.L.parked.append((x, z, j.F.vx, j.F.vz, Y0 + 1.72))


def workbench(j, fp):
    a, b, c, e = fp
    j.bx(a, b, c, e, Y0, Y0 + 0.88, (180, 40, 36), 'metal'); j.bx(a - 0.02, b + 0.02, c - 0.02, e, Y0 + 0.88, Y0 + 0.93, (110, 90, 70), 'liso')
    j.bx(a, b, e - 0.04, e - 0.01, Y0 + 1.1, Y0 + 2.2, (200, 204, 208), 'metal')
    for k in range(int((b - a) / 0.25)): j.bx(a + 0.1 + k * 0.25, a + 0.14 + k * 0.25, e - 0.06, e - 0.04, Y0 + 1.4 + (k % 3) * 0.22, Y0 + 1.62 + (k % 3) * 0.22, (60, 60, 64), 'metal')
    j.solid(a, b, c, e)
