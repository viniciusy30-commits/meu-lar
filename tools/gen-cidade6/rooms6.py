"""Cidade 6 - salas planejadas dos predios (profissoes e prefeitura).

Room: retangulo (u0, u1, v0, v1) no referencial do predio, com as portas que dao nele. Cada porta reserva uma area
livre (a largura da porta + 0,5 m de cada lado, 1,4 m para dentro) e cada movel colocado ocupa o seu retangulo:
um movel so entra se couber inteiro na sala, sem encostar em outro e sem tampar porta (folga de circulacao de 0,6 m).
Paredes internas com portas de verdade (folha aberta encostada na parede, batente, macaneta) de tipos diferentes.
"""
import math
from mesh import shade
from jobs6 import J, GLOW, WOOD, WOOD_L, STEEL, DARK
import jobs6


def Y0(): return jobs6.Y0
def HH(): return jobs6.HH


class Room:
    def __init__(self, j, u0, u1, v0, v1, name=''):
        self.j = j; self.u0, self.u1, self.v0, self.v1 = u0, u1, v0, v1; self.name = name
        self.occ = []; self.keep = []

    def door(self, side, pos, width):
        """registra uma porta na parede 'side' (n: v0, s: v1, w: u0, e: u1) centrada em pos"""
        a, b = pos - width / 2 - 0.5, pos + width / 2 + 0.5
        if side == 'n': self.keep.append((a, b, self.v0, self.v0 + 1.4))
        elif side == 's': self.keep.append((a, b, self.v1 - 1.4, self.v1))
        elif side == 'w': self.keep.append((self.u0, self.u0 + 1.4, a, b))
        else: self.keep.append((self.u1 - 1.4, self.u1, a, b))
        return self

    def fits(self, u0, u1, v0, v1, gap=0.0):
        if u0 < self.u0 - 1e-6 or u1 > self.u1 + 1e-6 or v0 < self.v0 - 1e-6 or v1 > self.v1 + 1e-6: return False
        for (a, b, c, d) in self.keep:
            if u0 < b and u1 > a and v0 < d and v1 > c: return False
        for (a, b, c, d) in self.occ:
            if u0 < b + gap and u1 > a - gap and v0 < d + gap and v1 > c - gap: return False
        return True

    def take(self, u0, u1, v0, v1):
        self.occ.append((u0, u1, v0, v1))

    def put(self, u0, u1, v0, v1, fn, gap=0.0):
        """chama fn() se o retangulo couber; registra a ocupacao"""
        if not self.fits(u0, u1, v0, v1, gap): return False
        fn(); self.take(u0, u1, v0, v1); return True

    @property
    def w(self): return self.u1 - self.u0

    @property
    def d(self): return self.v1 - self.v0

    @property
    def cu(self): return (self.u0 + self.u1) / 2

    @property
    def cv(self): return (self.v0 + self.v1) / 2

    # -------- encostar na parede: devolve (u, v, rot) do centro de um movel de largura w e fundo dp encostado
    def on_wall(self, side, pos, w, dp):
        """rot segue a convencao dos moveis: costas do movel (+v local) na parede"""
        if side == 's': return (pos, self.v1 - dp / 2, 0), (pos - w / 2, pos + w / 2, self.v1 - dp, self.v1)
        if side == 'n': return (pos, self.v0 + dp / 2, 2), (pos - w / 2, pos + w / 2, self.v0, self.v0 + dp)
        if side == 'w': return (self.u0 + dp / 2, pos, 1), (self.u0, self.u0 + dp, pos - w / 2, pos + w / 2)
        return (self.u1 - dp / 2, pos, 3), (self.u1 - dp, self.u1, pos - w / 2, pos + w / 2)

    def along(self, side, w, dp, step=None, margin=0.3):
        """posicoes ao longo de uma parede (centros), da ponta para a outra"""
        L0, L1 = (self.u0, self.u1) if side in ('n', 's') else (self.v0, self.v1)
        step = step or (w + 0.1)
        p = L0 + margin + w / 2
        while p + w / 2 <= L1 - margin + 1e-6:
            yield p
            p += step


# ==================================================================== paredes internas e portas
def door_leaf(j, u, v, axis, width, kind, swing=1):
    """folha de porta aberta encostada na parede (nao bloqueia a passagem), batente e macaneta.
    axis 'u': parede de v fixo (porta abre para +v*swing); axis 'v': parede de u fixo."""
    y0 = Y0(); h = 2.15
    col = {'madeira': (150, 104, 66), 'vidro': (170, 200, 214), 'cozinha': (196, 200, 206), 'banheiro': (232, 228, 220),
           'cortafogo': (190, 60, 50), 'grade': STEEL, 'dupla': (170, 200, 214)}[kind]
    mat = {'madeira': 'madeira', 'vidro': 'vidro', 'cozinha': 'metal', 'banheiro': 'liso', 'cortafogo': 'metal', 'grade': 'metal', 'dupla': 'vidro'}[kind]
    leaves = [(-1, width / 2)] if kind == 'dupla' else [(1, width)]
    if kind == 'dupla': leaves = [(-1, width / 2), (1, width / 2)]
    for (end, lw) in leaves:
        # dobradica na ponta 'end' da abertura; a folha fica perpendicular a parede, para dentro
        if axis == 'u':
            hu = u + end * width / 2; s = swing
            a, b = (hu - 0.03, hu + 0.03) if True else (0, 0)
            ub0, ub1 = (hu - 0.05, hu) if end > 0 else (hu, hu + 0.05)
            j.bx(ub0, ub1, v + s * 0.08, v + s * (0.08 + lw), y0 + 0.02, y0 + h, col, mat)
            if kind in ('madeira', 'banheiro', 'cortafogo'):
                kv = v + s * (0.08 + lw - 0.12); j.bx(ub0 - 0.04, ub1 + 0.04, min(kv, kv + s * 0.06), max(kv, kv + s * 0.06), y0 + 1.0, y0 + 1.06, (200, 190, 150), 'metal')
            if kind == 'cozinha':
                j.cyl(ub0 - 0.01 if end > 0 else ub1 + 0.01, v + s * (0.08 + lw / 2), 0.15, y0 + 1.35, y0 + 1.36, (180, 210, 225), 'vidro', 12)
        else:
            hv = v + end * width / 2; s = swing
            vb0, vb1 = (hv - 0.05, hv) if end > 0 else (hv, hv + 0.05)
            j.bx(u + s * 0.08, u + s * (0.08 + lw), vb0, vb1, y0 + 0.02, y0 + h, col, mat)
            if kind in ('madeira', 'banheiro', 'cortafogo'):
                ku = u + s * (0.08 + lw - 0.12); j.bx(min(ku, ku + s * 0.06), max(ku, ku + s * 0.06), vb0 - 0.04, vb1 + 0.04, y0 + 1.0, y0 + 1.06, (200, 190, 150), 'metal')
    if kind == 'banheiro':                                                # placa
        if axis == 'u': j.bx(u - 0.15, u + 0.15, v - 0.1, v - 0.08, y0 + 2.3, y0 + 2.6, (40, 90, 160), 'liso')
        else: j.bx(u - 0.1, u - 0.08, v - 0.15, v + 0.15, y0 + 2.3, y0 + 2.6, (40, 90, 160), 'liso')


def wall(j, axis, c, a0, a1, doors=(), glass=False, col=(244, 242, 236), t=0.12, swing=1):
    """parede interna: axis 'u' = parede de v=c indo de u=a0 a a1; 'v' = parede de u=c de v=a0 a a1.
    doors: [(pos, largura, tipo)]. Folhas abertas para o lado 'swing'. Topo abaixo do forro (sem coplanar)."""
    y0 = Y0(); y1 = Y0() + HH() - 0.13
    cuts = sorted((p - w_ / 2, p + w_ / 2, k) for (p, w_, k) in doors)
    p = a0
    G = j.F if axis == 'u' else j.sub(c, 0.0, 1)
    jj = J(j.L, G) if axis == 'v' else j
    # no referencial girado (axis v): u' = v, v' = -u + c  -> parede em v'=0
    def seg(s0, s1, ya, yb, mat='reboco', cc=col):
        if s1 - s0 < 0.01: return
        if axis == 'u': j.bx(s0, s1, c - t / 2, c + t / 2, ya, yb, cc, mat)
        else: jj.bx(s0, s1, -t / 2, t / 2, ya, yb, cc, mat)

    def solid(s0, s1):
        if axis == 'u': j.solid(s0, s1, c - t / 2, c + t / 2)
        else: jj.solid(s0, s1, -t / 2, t / 2)
    for (s0, s1, k) in cuts + [(a1, a1, None)]:
        if s0 > p:
            if glass:
                seg(p, s0, y0, y0 + 0.9); seg(p, s0, y0 + 2.5, y1)
                seg(p, s0, y0 + 0.9, y0 + 2.5, 'vidro', (180, 206, 220))
                q = p
                while q <= s0 + 1e-6: seg(q - 0.03, q + 0.03, y0, y1, 'metal', (90, 94, 100)); q += 1.2
            else: seg(p, s0, y0, y1)
            solid(p, s0)
        if k is None: break
        seg(s0, s1, y0 + 2.2, y1)                                            # verga sobre a porta
        seg(s0 - 0.06, s0, y0, y0 + 2.2, 'liso', (90, 84, 78)); seg(s1, s1 + 0.06, y0, y0 + 2.2, 'liso', (90, 84, 78))    # batente
        if k != 'vao':
            if axis == 'u': door_leaf(j, (s0 + s1) / 2, c, 'u', s1 - s0, k, swing)
            else: door_leaf(j, c, (s0 + s1) / 2, 'v', s1 - s0, k, swing)
        p = s1
