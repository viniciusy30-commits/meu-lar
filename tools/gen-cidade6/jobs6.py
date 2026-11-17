"""Cidade 6 - predios das profissoes (um por profissao) e a prefeitura nova.

Cada predio: recuo com praca de entrada (piso, canteiros, bicicletario, poste, mastro, placa-totem), fachada com
embasamento de pedra, porta de vidro com marquise, vitrines/janelas com caixilho, andares de cima com janelas,
platibanda e equipamentos no telhado; DENTRO, o terreo inteiro e andavel: piso proprio, rodape, forro com luminarias
(acendem a noite), divisorias com portas, e cada sala mobiliada para a profissao (recepcao, sala de espera, salas
de trabalho, copa e banheiros). Colisoes nas paredes (com vao nas portas) e nos moveis grandes.

Referencial: F na divisa do lote com a calcada; u ao longo da rua, v para dentro do lote.
"""
import math
from mesh import Frame, shade, WHITE
from roads6 import Y_WALK

GLOW = (255, 238, 196)          # cor exata das luminarias (o jogo acende a noite)
Y0 = Y_WALK + 0.15              # piso interno
HH = 4.2                        # pe-direito do terreo
WOOD = (150, 108, 72)
WOOD_L = (196, 158, 116)
STEEL = (120, 126, 134)
DARK = (46, 50, 56)

# id -> (nome do local, cor da marca, andares, largura, fundo, piso)
JOBS = {
    'diarista': ('Brilho Limpeza', (64, 170, 200), 1, 18, 15, 'ceramica'),
    'lixeiro': ('Central de Coleta', (70, 140, 70), 1, 30, 24, 'concreto'),
    'atendente': ('Lanchonete do Zé', (220, 60, 50), 1, 20, 16, 'ceramica'),
    'entregador': ('Expresso Já', (240, 140, 40), 1, 24, 18, 'concreto'),
    'frentista': ('Posto Rota Sul', (30, 110, 190), 1, 16, 12, 'ceramica'),
    'repositor': ('SuperBom', (230, 70, 50), 1, 36, 28, 'ceramica'),
    'professor': ('Escola Primavera', (240, 180, 40), 2, 32, 22, 'madeira'),
    'secretario': ('Escritório Central', (60, 90, 150), 3, 22, 16, 'madeira'),
    'policial': ('Delegacia', (30, 60, 140), 2, 28, 22, 'ceramica'),
    'bombeiro': ('Quartel dos Bombeiros', (200, 40, 36), 2, 28, 24, 'concreto'),
    'mecanico': ('Oficina do Toninho', (90, 100, 110), 1, 26, 18, 'concreto'),
    'enfermeiro': ('Clínica Aurora', (40, 160, 140), 2, 22, 18, 'ceramica'),
    'medico': ('Hospital Santa Clara', (200, 40, 50), 4, 40, 28, 'ceramica'),
    'advogado': ('Almeida & Prado', (90, 60, 40), 3, 20, 16, 'madeira'),
    'juiz': ('Fórum da Comarca', (150, 120, 70), 3, 30, 26, 'pedra'),
    'engenheiro': ('Pilar Construtora', (230, 170, 30), 3, 24, 18, 'madeira'),
    'programador': ('Nova Tech', (110, 70, 200), 4, 26, 18, 'madeira'),
    'empresario': ('Grupo Atlas', (30, 40, 60), 6, 28, 20, 'pedra'),
}
EMOJI = {'diarista': '🧽', 'lixeiro': '♻️', 'atendente': '🍔', 'entregador': '📦', 'frentista': '⛽', 'repositor': '🛒', 'professor': '🏫', 'secretario': '🗂️', 'policial': '🚓', 'bombeiro': '🚒', 'mecanico': '🔧', 'enfermeiro': '🩺', 'medico': '🏥', 'advogado': '📜', 'juiz': '⚖️', 'engenheiro': '🏗️', 'programador': '💻', 'empresario': '🏢'}
ORDER = ['repositor', 'professor', 'policial', 'bombeiro', 'juiz', 'empresario', 'programador', 'engenheiro', 'advogado',
         'secretario', 'enfermeiro', 'mecanico', 'entregador', 'lixeiro', 'atendente', 'diarista', 'frentista']


class J:
    """contexto de um predio: frame, construtor, malha, lista de luzes/colisoes do lote"""
    def __init__(self, L, F):
        self.L = L; self.B = L.B; self.M = L.M; self.F = F; self.r = L.rnd

    # ---------------------------------------------------------------- primitivas
    def bx(self, u0, u1, v0, v1, y0, y1, col, mat='liso', top=True, F=None):
        F = F or self.F
        if u1 < u0: u0, u1 = u1, u0
        if v1 < v0: v0, v1 = v1, v0
        self.B.box(F, u0, u1, v0, v1, y0, y1, col, mat, top)

    def solid(self, u0, u1, v0, v1, F=None):
        F = F or self.F
        if u1 < u0: u0, u1 = u1, u0
        if v1 < v0: v0, v1 = v1, v0
        self.B.solid(F, u0, u1, v0, v1)

    def cyl(self, u, v, r, y0, y1, col, mat='metal', seg=10, top=True, r1=None, F=None):
        F = F or self.F; x, z = F.xz(u, v); self.M.m(mat); self.M.cyl(x, z, r, y0, y1, col, seg, top, r1)

    def ball(self, u, v, y, r, col, mat='liso', F=None):
        F = F or self.F; x, z = F.xz(u, v); self.M.m(mat); self.M.sphere(x, y, z, r, col, 8, 5)

    def sub(self, u, v, rot):
        """sub-referencial girado (rot 0..3 em passos de 90 graus) com origem em (u, v)"""
        F = self.F; ux, uz = F.ux, F.uz
        for _ in range(rot % 4): ux, uz = -uz, ux
        G = Frame(F.xz(u, v), (ux, uz))
        return G

    def light(self, u, v, w=1.2, d=0.6, y=None, F=None):
        """luminaria de forro (painel aceso) e registro da poca de luz"""
        F = F or self.F; y = Y0 + HH - 0.22 if y is None else y
        self.bx(u - w / 2 - 0.04, u + w / 2 + 0.04, v - d / 2 - 0.04, v + d / 2 + 0.04, y + 0.02, y + 0.08, (235, 235, 232), 'metal', F=F)
        self.M.m('liso'); self.M.poly([F.p(u - w / 2, v - d / 2, y), F.p(u + w / 2, v - d / 2, y), F.p(u + w / 2, v + d / 2, y), F.p(u - w / 2, v + d / 2, y)], GLOW, (0, -1, 0))
        x, z = F.xz(u, v); self.L.props_lights.append((round(x, 1), round(z, 1), 4.5))

    def ceiling(self, u0, u1, v0, v1, col=(250, 250, 248)):
        """forro: laje com a face de baixo branca (vista de dentro) e sanca no contorno"""
        F = self.F; y = Y0 + HH
        self.bx(u0, u1, v0, v1, y - 0.12, y, col, 'reboco')
        self.M.m('reboco'); self.M.poly([F.p(u0, v0, y - 0.12), F.p(u1, v0, y - 0.12), F.p(u1, v1, y - 0.12), F.p(u0, v1, y - 0.12)], col, (0, -1, 0))
        for (a, b, c, e) in ((u0, u1, v0, v0 + 0.25), (u0, u1, v1 - 0.25, v1), (u0, u0 + 0.25, v0, v1), (u1 - 0.25, u1, v0, v1)):
            self.bx(a, b, c, e, y - 0.3, y - 0.12, col, 'reboco')
            self.M.m('reboco'); self.M.poly([F.p(a, c, y - 0.3), F.p(b, c, y - 0.3), F.p(b, e, y - 0.3), F.p(a, e, y - 0.3)], col, (0, -1, 0))

    # ---------------------------------------------------------------- paredes
    def wall_v(self, u0, u1, v, y0, y1, t, col, mat, ops=(), side=-1, inner=(246, 244, 240)):
        """parede de v fixo de u0 a u1 com aberturas (ua, ub, ya, yb, tipo) tipo 'porta' | 'janela' | 'vitrine'"""
        cuts = sorted(ops)
        u = u0
        for (ua, ub, ya, yb, kind) in cuts + [(u1, u1, y0, y1, None)]:
            if ua > u: self.bx(u, ua, v - t / 2, v + t / 2, y0, y1, col, mat); self.solid(u, ua, v - t / 2, v + t / 2)
            if kind is None: break
            if ya > y0 + 0.01: self.bx(ua, ub, v - t / 2, v + t / 2, y0, ya, col, mat); self.solid(ua, ub, v - t / 2, v + t / 2) if kind != 'porta' else None
            if yb < y1 - 0.01: self.bx(ua, ub, v - t / 2, v + t / 2, yb, y1, col, mat)
            if kind in ('janela', 'vitrine'):
                self.solid(ua, ub, v - t / 2, v + t / 2)
                self.bx(ua, ub, v - 0.02, v + 0.02, ya, yb, (170, 200, 214), 'vidro')
                fr = DARK if kind == 'vitrine' else (236, 236, 232)
                for uu in ([ua, ub] + ([(ua + ub) / 2] if ub - ua > 1.8 else [])): self.bx(uu - 0.05, uu + 0.05, v - t / 2 - 0.02, v + t / 2 + 0.02, ya, yb, fr, 'metal')
                for yy in (ya, yb): self.bx(ua, ub, v - t / 2 - 0.02, v + t / 2 + 0.02, yy - 0.05, yy + 0.05, fr, 'metal')
                self.bx(ua - 0.05, ub + 0.05, v + side * (t / 2 + 0.12), v + side * (t / 2) , ya - 0.12, ya - 0.04, (220, 216, 208), 'concreto')   # peitoril
            if kind == 'porta':
                self.bx(ua - 0.08, ua, v - t / 2 - 0.03, v + t / 2 + 0.03, ya, yb, DARK, 'metal'); self.bx(ub, ub + 0.08, v - t / 2 - 0.03, v + t / 2 + 0.03, ya, yb, DARK, 'metal')
                self.bx(ua - 0.08, ub + 0.08, v - t / 2 - 0.03, v + t / 2 + 0.03, yb, yb + 0.1, DARK, 'metal')
            u = ub

    def wall_u(self, v0, v1, u, y0, y1, t, col, mat, ops=()):
        """parede de u fixo (lateral) de v0 a v1, aberturas (va, vb, ya, yb, tipo)"""
        G = Frame(self.F.xz(u, 0), (self.F.vx, self.F.vz))       # u' = v, v' = -u (gira 90 graus)
        old = self.F; self.F = G
        sgn = 1 if abs(G.vx - (-old.ux)) < 1e-6 and abs(G.vz - (-old.uz)) < 1e-6 else -1
        try:
            if sgn > 0: self.wall_v(v0, v1, 0.0, y0, y1, t, col, mat, ops)
            else: self.wall_v(v0, v1, 0.0, y0, y1, t, col, mat, ops)
        finally: self.F = old

    def partition(self, u0, u1, v, door=None, col=(244, 242, 236), glass=False):
        """divisoria interna (v fixo) com porta (centro, largura)"""
        ops = []
        if door: ops.append((door[0] - door[1] / 2, door[0] + door[1] / 2, Y0, Y0 + 2.2, 'porta'))
        if glass:
            g0 = u0 + 0.4; g1 = u1 - 0.4
            segs = [(g0, (door[0] - door[1] / 2 - 0.3) if door else g1)] + ([((door[0] + door[1] / 2 + 0.3), g1)] if door else [])
            for (a, b) in segs:
                if b - a > 0.8: ops.append((a, b, Y0 + 0.9, Y0 + 2.4, 'janela'))
        self.wall_v(u0, u1, v, Y0, Y0 + HH, 0.12, col, 'reboco', ops)

    def partition_u(self, v0, v1, u, door=None, col=(244, 242, 236)):
        ops = [(door[0] - door[1] / 2, door[0] + door[1] / 2, Y0, Y0 + 2.2, 'porta')] if door else []
        self.wall_u(v0, v1, u, Y0, Y0 + HH, 0.12, col, 'reboco', ops)

    # ---------------------------------------------------------------- moveis (sub-referencial G: u largura, v profundidade)
    def chair(self, u, v, rot, col=(60, 70, 90), office=True):
        G = self.sub(u, v, rot)
        if office:
            self.cyl(0, 0, 0.28, Y0, Y0 + 0.04, DARK, F=G); self.cyl(0, 0, 0.03, Y0 + 0.04, Y0 + 0.45, STEEL, F=G)
            self.bx(-0.24, 0.24, -0.22, 0.24, Y0 + 0.45, Y0 + 0.55, col, F=G); self.bx(-0.23, 0.23, 0.2, 0.27, Y0 + 0.55, Y0 + 1.05, col, F=G)
        else:
            for (a, b) in ((-0.2, -0.2), (0.2, -0.2), (-0.2, 0.2), (0.2, 0.2)): self.bx(a - 0.02, a + 0.02, b - 0.02, b + 0.02, Y0, Y0 + 0.45, STEEL, 'metal', F=G)
            self.bx(-0.23, 0.23, -0.23, 0.23, Y0 + 0.45, Y0 + 0.5, col, F=G); self.bx(-0.23, 0.23, 0.2, 0.24, Y0 + 0.5, Y0 + 0.92, col, F=G)

    def desk(self, u, v, rot, w=1.6, d=0.75, pc=True, col=WOOD_L):
        G = self.sub(u, v, rot)
        self.bx(-w / 2, w / 2, -d / 2, d / 2, Y0 + 0.72, Y0 + 0.76, col, 'madeira', F=G)
        for a in (-w / 2 + 0.05, w / 2 - 0.05): self.bx(a - 0.03, a + 0.03, -d / 2 + 0.05, d / 2 - 0.05, Y0, Y0 + 0.72, STEEL, 'metal', F=G)
        self.bx(-w / 2 + 0.05, -w / 2 + 0.5, -d / 2 + 0.05, d / 2 - 0.05, Y0, Y0 + 0.7, shade(col, -20), 'liso', F=G)       # gaveteiro
        for k in range(3): self.bx(-w / 2 + 0.1, -w / 2 + 0.45, -d / 2 + 0.04, -d / 2 + 0.05, Y0 + 0.12 + k * 0.2, Y0 + 0.28 + k * 0.2, shade(col, 10), 'liso', F=G)
        if pc:
            self.bx(-0.3, 0.3, d / 2 - 0.22, d / 2 - 0.18, Y0 + 0.88, Y0 + 1.22, (24, 26, 30), F=G)               # monitor
            self.bx(-0.27, 0.27, d / 2 - 0.225, d / 2 - 0.22, Y0 + 0.9, Y0 + 1.2, (70, 120, 180), F=G)
            self.bx(-0.03, 0.03, d / 2 - 0.2, d / 2 - 0.14, Y0 + 0.76, Y0 + 0.88, (40, 40, 44), F=G)
            self.bx(-0.22, 0.22, -0.1, 0.08, Y0 + 0.76, Y0 + 0.78, (40, 40, 44), F=G)                              # teclado
            self.bx(0.3, 0.36, -0.05, 0.05, Y0 + 0.76, Y0 + 0.79, (40, 40, 44), F=G)
        self.bx(w / 2 - 0.45, w / 2 - 0.15, -0.2, 0.1, Y0 + 0.76, Y0 + 0.8, (248, 248, 244), F=G)                    # papeis
        self.cyl(w / 2 - 0.2, d / 2 - 0.2, 0.04, Y0 + 0.76, Y0 + 0.86, (200, 60, 50), 'ceramica', 8, F=G)            # caneca
        self.solid(-w / 2, w / 2, -d / 2, d / 2, F=G)

    def workstation(self, u, v, rot, col=(60, 70, 90)):
        self.desk(u, v, rot); G = self.sub(u, v, rot)
        x, z = G.xz(0, -0.75); self.chair_at(x, z, rot, col)

    def chair_at(self, x, z, rot, col):
        # cadeira num ponto do mundo virada para o mesmo lado da mesa
        F = self.F; ux, uz = F.ux, F.uz
        for _ in range(rot % 4): ux, uz = -uz, ux
        G = Frame((x, z), (ux, uz))
        self.cyl(0, 0, 0.28, Y0, Y0 + 0.04, DARK, F=G); self.cyl(0, 0, 0.03, Y0 + 0.04, Y0 + 0.45, STEEL, F=G)
        self.bx(-0.24, 0.24, -0.24, 0.22, Y0 + 0.45, Y0 + 0.55, col, F=G); self.bx(-0.23, 0.23, -0.31, -0.24, Y0 + 0.55, Y0 + 1.05, col, F=G)

    def shelf(self, u, v, rot, w=1.8, h=2.1, d=0.4, col=WOOD, items='livros'):
        G = self.sub(u, v, rot)
        self.bx(-w / 2, w / 2, -d / 2, d / 2, Y0, Y0 + 0.08, shade(col, -20), F=G)
        for a in (-w / 2, w / 2 - 0.04): self.bx(a, a + 0.04, -d / 2, d / 2, Y0, Y0 + h, col, F=G)
        self.bx(-w / 2, w / 2, d / 2 - 0.02, d / 2, Y0, Y0 + h, shade(col, -12), F=G)
        n = int(h / 0.42)
        pal = [(180, 50, 50), (40, 90, 160), (60, 140, 80), (220, 180, 60), (120, 80, 140), (230, 230, 220), (200, 110, 50)]
        for k in range(n):
            y = Y0 + 0.08 + k * 0.42
            self.bx(-w / 2, w / 2, -d / 2, d / 2, y, y + 0.03, col, F=G)
            if items == 'livros':
                a = -w / 2 + 0.06
                while a < w / 2 - 0.12:
                    t = self.r.uniform(0.03, 0.07); hb = self.r.uniform(0.22, 0.34)
                    if self.r.random() < 0.9: self.bx(a, a + t, -d / 2 + 0.05, d / 2 - 0.06, y + 0.03, y + 0.03 + hb, self.r.choice(pal), F=G)
                    a += t + 0.005
            elif items == 'caixas':
                a = -w / 2 + 0.08
                while a < w / 2 - 0.4:
                    bw = self.r.uniform(0.25, 0.45); self.bx(a, a + bw, -d / 2 + 0.04, d / 2 - 0.04, y + 0.03, y + 0.03 + self.r.uniform(0.2, 0.36), self.r.choice(((180, 140, 90), (200, 160, 110), (160, 120, 80))), F=G); a += bw + 0.04
            elif items == 'pastas':
                a = -w / 2 + 0.06
                while a < w / 2 - 0.1: self.bx(a, a + 0.07, -d / 2 + 0.05, d / 2 - 0.05, y + 0.03, y + 0.33, self.r.choice(pal[:3]), F=G); a += 0.08
        self.solid(-w / 2, w / 2, -d / 2, d / 2, F=G)

    def sofa(self, u, v, rot, w=2.0, col=(90, 110, 140)):
        G = self.sub(u, v, rot)
        self.bx(-w / 2, w / 2, -0.45, 0.45, Y0 + 0.08, Y0 + 0.42, col, F=G)
        self.bx(-w / 2, w / 2, 0.25, 0.45, Y0 + 0.42, Y0 + 0.85, shade(col, -10), F=G)
        for a in (-w / 2, w / 2 - 0.18): self.bx(a, a + 0.18, -0.45, 0.45, Y0 + 0.42, Y0 + 0.62, shade(col, -10), F=G)
        for k in range(int(w / 0.7)): self.bx(-w / 2 + 0.2 + k * 0.68, -w / 2 + 0.84 + k * 0.68, -0.4, 0.2, Y0 + 0.42, Y0 + 0.52, shade(col, 12), F=G)
        for a in (-w / 2 + 0.06, w / 2 - 0.06): self.cyl(a, -0.38, 0.03, Y0, Y0 + 0.08, DARK, F=G)
        self.solid(-w / 2, w / 2, -0.45, 0.45, F=G)

    def seats_row(self, u, v, rot, n=4, col=(40, 120, 180)):
        """longarina de cadeiras de espera"""
        G = self.sub(u, v, rot); w = n * 0.58
        self.bx(-w / 2, w / 2, -0.05, 0.05, Y0 + 0.3, Y0 + 0.36, STEEL, 'metal', F=G)
        for a in (-w / 2 + 0.2, w / 2 - 0.2):
            self.bx(a - 0.03, a + 0.03, -0.25, 0.25, Y0, Y0 + 0.04, STEEL, 'metal', F=G); self.bx(a - 0.03, a + 0.03, -0.02, 0.02, Y0, Y0 + 0.34, STEEL, 'metal', F=G)
        for k in range(n):
            a = -w / 2 + 0.04 + k * 0.58
            self.bx(a, a + 0.5, -0.22, 0.22, Y0 + 0.4, Y0 + 0.45, col, F=G); self.bx(a, a + 0.5, 0.2, 0.25, Y0 + 0.45, Y0 + 0.9, col, F=G)
        self.solid(-w / 2, w / 2, -0.25, 0.25, F=G)

    def table(self, u, v, rot, w=1.4, d=0.8, col=WOOD_L, h=0.75):
        G = self.sub(u, v, rot)
        self.bx(-w / 2, w / 2, -d / 2, d / 2, Y0 + h - 0.04, Y0 + h, col, 'madeira', F=G)
        for (a, b) in ((-w / 2 + 0.06, -d / 2 + 0.06), (w / 2 - 0.06, -d / 2 + 0.06), (-w / 2 + 0.06, d / 2 - 0.06), (w / 2 - 0.06, d / 2 - 0.06)): self.bx(a - 0.03, a + 0.03, b - 0.03, b + 0.03, Y0, Y0 + h - 0.04, shade(col, -30), F=G)
        self.solid(-w / 2, w / 2, -d / 2, d / 2, F=G)

    def round_table(self, u, v, r=0.45, col=(246, 246, 244), chairs=3, ccol=(200, 60, 50)):
        self.cyl(u, v, 0.25, Y0, Y0 + 0.03, DARK); self.cyl(u, v, 0.04, Y0 + 0.03, Y0 + 0.72, STEEL); self.cyl(u, v, r, Y0 + 0.72, Y0 + 0.76, col, 'liso', 16)
        for k in range(chairs):
            a = 2 * math.pi * k / chairs; cu, cv = u + math.cos(a) * (r + 0.4), v + math.sin(a) * (r + 0.4)
            self.chair(cu, cv, 0, ccol, False)
        self.solid(u - r, u + r, v - r, v + r)

    def counter(self, u, v, rot, w=3.0, d=0.6, col=(240, 236, 228), top=(60, 60, 64), h=1.05):
        G = self.sub(u, v, rot)
        self.bx(-w / 2, w / 2, -d / 2, d / 2, Y0, Y0 + h - 0.05, col, 'liso', F=G)
        self.bx(-w / 2 - 0.03, w / 2 + 0.03, -d / 2 - 0.05, d / 2 + 0.03, Y0 + h - 0.05, Y0 + h, top, 'ceramica', F=G)
        self.bx(-w / 2, w / 2, -d / 2 - 0.01, -d / 2, Y0, Y0 + 0.1, DARK, F=G)                                   # rodape
        self.solid(-w / 2, w / 2, -d / 2, d / 2, F=G)

    def register(self, u, v, rot):
        G = self.sub(u, v, rot)
        self.bx(-0.2, 0.2, -0.15, 0.15, Y0 + 1.05, Y0 + 1.15, (40, 40, 44), F=G); self.bx(-0.16, 0.16, 0.05, 0.08, Y0 + 1.15, Y0 + 1.42, (30, 30, 34), F=G)
        self.bx(-0.14, 0.14, 0.045, 0.05, Y0 + 1.18, Y0 + 1.39, (80, 160, 120), F=G)

    def plant(self, u, v, s=1.0, pot=(210, 120, 80)):
        self.cyl(u, v, 0.22 * s, Y0, Y0 + 0.45 * s, pot, 'ceramica', 10, True, 0.17 * s)
        x, z = self.F.xz(u, v); self.L.trees.append((x, z, 'arbusto', 0.55 * s, Y0 + 0.4 * s))

    def rug(self, u0, u1, v0, v1, col):
        self.bx(u0, u1, v0, v1, Y0 + 0.005, Y0 + 0.015, col, 'liso')
        self.bx(u0 + 0.15, u1 - 0.15, v0 + 0.15, v1 - 0.15, Y0 + 0.015, Y0 + 0.02, shade(col, 25), 'liso')

    def art(self, u, v, rot, w=1.0, h=0.7, y=1.6, col=None):
        """quadro na parede (rot: lado para onde o quadro olha)"""
        G = self.sub(u, v, rot); col = col or self.r.choice(((210, 120, 80), (80, 140, 190), (120, 170, 110), (220, 190, 90)))
        self.bx(-w / 2, w / 2, 0, 0.04, Y0 + y - h / 2, Y0 + y + h / 2, (40, 36, 30), F=G)
        self.bx(-w / 2 + 0.06, w / 2 - 0.06, -0.01, 0.0, Y0 + y - h / 2 + 0.06, Y0 + y + h / 2 - 0.06, col, F=G)
        self.bx(-w / 4, w / 6, -0.015, -0.01, Y0 + y - h / 4, Y0 + y + h / 8, shade(col, 40), F=G)

    def board(self, u, v, rot, w=3.0, h=1.2, col=(40, 70, 50)):
        """quadro-negro/branco na parede"""
        G = self.sub(u, v, rot)
        self.bx(-w / 2 - 0.05, w / 2 + 0.05, 0, 0.05, Y0 + 0.85, Y0 + 0.9 + h, (170, 140, 100), F=G)
        self.bx(-w / 2, w / 2, -0.01, 0.0, Y0 + 0.9, Y0 + 0.85 + h, col, F=G)
        self.bx(-w / 2, w / 2, -0.1, 0.0, Y0 + 0.86, Y0 + 0.9, (170, 140, 100), F=G)
        for k in range(4): self.bx(-w / 2 + 0.3, -w / 2 + 0.3 + self.r.uniform(0.6, 1.8), -0.015, -0.01, Y0 + 1.6 + k * 0.18, Y0 + 1.62 + k * 0.18, (235, 235, 230), F=G)

    def tv(self, u, v, rot, w=1.3, y=1.9):
        G = self.sub(u, v, rot)
        self.bx(-w / 2, w / 2, 0, 0.06, Y0 + y - w * 0.28, Y0 + y + w * 0.28, (20, 20, 24), F=G)
        self.bx(-w / 2 + 0.04, w / 2 - 0.04, -0.005, 0.0, Y0 + y - w * 0.28 + 0.04, Y0 + y + w * 0.28 - 0.04, (60, 110, 170), F=G)

    def clock(self, u, v, rot, y=2.9):
        G = self.sub(u, v, rot); x, z = G.xz(0, 0.02)
        self.bx(-0.18, 0.18, 0, 0.05, Y0 + y - 0.18, Y0 + y + 0.18, (250, 250, 248), F=G)
        self.bx(-0.01, 0.01, -0.005, 0, Y0 + y, Y0 + y + 0.13, DARK, F=G); self.bx(0, 0.1, -0.005, 0, Y0 + y - 0.01, Y0 + y + 0.01, DARK, F=G)

    def water_cooler(self, u, v):
        self.bx(u - 0.17, u + 0.17, v - 0.17, v + 0.17, Y0, Y0 + 1.0, (240, 240, 240))
        self.cyl(u, v, 0.15, Y0 + 1.0, Y0 + 1.45, (140, 190, 230), 'vidro', 10)
        self.solid(u - 0.17, u + 0.17, v - 0.17, v + 0.17)

    def bin(self, u, v, col=(70, 120, 80)):
        self.cyl(u, v, 0.16, Y0, Y0 + 0.45, col, 'liso', 10, True, 0.18)

    def lockers(self, u, v, rot, n=6, col=(110, 130, 150)):
        G = self.sub(u, v, rot); w = n * 0.42
        self.bx(-w / 2, w / 2, -0.25, 0.25, Y0, Y0 + 1.9, col, 'metal', F=G)
        for k in range(n):
            a = -w / 2 + k * 0.42
            self.bx(a + 0.01, a + 0.41, -0.26, -0.25, Y0 + 0.05, Y0 + 1.85, shade(col, 12), 'metal', F=G)
            for j in range(3): self.bx(a + 0.12, a + 0.3, -0.265, -0.26, Y0 + 1.6 - j * 0.04, Y0 + 1.62 - j * 0.04, DARK, F=G)
            self.bx(a + 0.33, a + 0.36, -0.27, -0.26, Y0 + 0.95, Y0 + 1.05, (200, 200, 200), F=G)
        self.solid(-w / 2, w / 2, -0.25, 0.25, F=G)

    def restroom(self, u0, u1, v0, v1):
        """banheiro: 2 boxes com divisoria, vasos e bancada com cubas e espelho"""
        self.bx(u0, u1, v0, v1, Y0 + 0.002, Y0 + 0.006, (230, 232, 236), 'ceramica')
        w = u1 - u0; bw = min(1.2, (w - 0.2) / 2)
        for k in range(2):
            a = u0 + 0.1 + k * bw
            self.bx(a + bw - 0.03, a + bw, v1 - 1.5, v1, Y0 + 0.15, Y0 + 2.0, (190, 200, 210), 'liso')
            self.cyl(a + bw / 2, v1 - 0.35, 0.2, Y0, Y0 + 0.42, (250, 250, 250), 'ceramica', 12)
            self.bx(a + bw / 2 - 0.2, a + bw / 2 + 0.2, v1 - 0.15, v1 - 0.05, Y0 + 0.42, Y0 + 0.82, (250, 250, 250), 'ceramica')
        self.bx(u0 + 0.1, u0 + 0.13, v1 - 1.5, v1, Y0 + 0.15, Y0 + 2.0, (190, 200, 210), 'liso')
        self.bx(u0 + 0.1, u1 - 0.1, v0 + 0.05, v0 + 0.6, Y0 + 0.82, Y0 + 0.88, (220, 220, 224), 'ceramica')
        for k in range(2): self.cyl(u0 + w * (0.3 + 0.4 * k), v0 + 0.33, 0.17, Y0 + 0.8, Y0 + 0.88, (250, 250, 250), 'ceramica', 12)
        self.bx(u0 + 0.2, u1 - 0.2, v0 + 0.02, v0 + 0.04, Y0 + 1.2, Y0 + 2.0, (200, 220, 230), 'vidro')
        self.solid(u0 + 0.1, u1 - 0.1, v0 + 0.05, v0 + 0.6)

    def pantry(self, u0, u1, v0, v1):
        """copa: armarios, pia, geladeira, micro-ondas, cafeteira e mesa com cadeiras"""
        w = u1 - u0
        self.counter((u0 + u1) / 2, v1 - 0.35, 2, min(w - 0.6, 2.8), 0.6, (236, 232, 222), (90, 90, 96), 0.92)
        self.bx(u0 + 0.3, u0 + 0.3 + min(w - 0.6, 2.8), v1 - 0.35, v1 - 0.02, Y0 + 1.5, Y0 + 2.2, (236, 232, 222), 'liso')
        self.bx(u1 - 0.95, u1 - 0.3, v1 - 0.7, v1 - 0.05, Y0, Y0 + 1.8, (230, 230, 232), 'metal'); self.solid(u1 - 0.95, u1 - 0.3, v1 - 0.7, v1 - 0.05)
        self.bx(u0 + 0.5, u0 + 0.95, v1 - 0.55, v1 - 0.15, Y0 + 0.92, Y0 + 1.2, (40, 40, 44))
        self.bx(u0 + 1.1, u0 + 1.3, v1 - 0.45, v1 - 0.2, Y0 + 0.92, Y0 + 1.25, (30, 30, 30))
        self.round_table((u0 + u1) / 2, (v0 + v1) / 2 - 0.2, 0.5, (246, 246, 244), 3, (120, 160, 190))

    # ---------------------------------------------------------------- fachada e casca
    def shell(self, w, d, floors, brand, floor_mat, wall=(232, 226, 214), sv=6.0, front_ops=None):
        """predio de w x d com recuo sv: piso, paredes com aberturas, forro, andares de cima, platibanda; devolve (u0, v0)"""
        u0 = 0.0; v0 = sv; u1 = w; v1 = sv + d
        r = self.r
        # embasamento e piso
        self.bx(u0 - 0.2, u1 + 0.2, v0 - 0.2, v1 + 0.2, Y_WALK - 0.3, Y0 - 0.005, (170, 166, 158), 'pedra')
        fcol = {'ceramica': (234, 232, 228), 'madeira': (170, 128, 88), 'concreto': (196, 194, 190), 'pedra': (226, 220, 206), 'paver': (220, 214, 204)}[floor_mat]
        self.M.m('paver' if floor_mat == 'ceramica' else floor_mat)
        fm = 'paver' if floor_mat == 'ceramica' else floor_mat
        self.bx(u0 + 0.15, u1 - 0.15, v0 + 0.15, v1 - 0.15, Y0 - 0.02, Y0, fcol, fm)
        # degrau/rampa na entrada
        dc = w / 2
        self.bx(dc - 2.4, dc + 2.4, v0 - 1.6, v0 - 0.2, Y_WALK, Y0 - 0.075, (214, 210, 202), 'concreto')
        # paredes externas
        ops = front_ops if front_ops is not None else []
        if front_ops is None:
            ops.append((dc - 1.2, dc + 1.2, Y0, Y0 + 2.7, 'porta'))
            k = 1
            while True:
                a = dc + 1.9 + (k - 1) * 3.2
                if a + 2.4 > u1 - 0.8: break
                ops.append((a, a + 2.4, Y0 + 0.5, Y0 + 3.0, 'vitrine')); ops.append((w - a - 2.4, w - a, Y0 + 0.5, Y0 + 3.0, 'vitrine')); k += 1
        self.wall_v(u0, u1, v0, Y0, Y0 + HH, 0.3, wall, 'reboco', ops)
        back_ops = []
        a = 1.5
        while a + 1.6 < w - 1.5: back_ops.append((a, a + 1.6, Y0 + 1.2, Y0 + 2.6, 'janela')); a += 4.0
        self.wall_v(u0, u1, v1, Y0, Y0 + HH, 0.3, wall, 'reboco', back_ops)
        for uu in (u0, u1):
            side_ops = []; a = v0 + 2.0
            while a + 1.6 < v1 - 1.5: side_ops.append((a, a + 1.6, Y0 + 1.2, Y0 + 2.6, 'janela')); a += 4.5
            self.wall_side(v0, v1, uu, side_ops, wall)
        # forro e rodape
        self.ceiling(u0 + 0.15, u1 - 0.15, v0 + 0.15, v1 - 0.15)
        # andares de cima (fachada com janelas) e cobertura
        top = Y0 + HH
        if floors > 1:
            self.bx(u0 - 0.1, u1 + 0.1, v0 - 0.1, v1 + 0.1, top, top + 0.35, shade(wall, -18), 'concreto')     # cinta
            self.B.box(self.F, u0, u1, v0, v1, top + 0.35, top + 0.35 + (floors - 1) * 3.4, wall, 'janelas', False, wall_uv=(3.0, 3.4, top + 0.35))
            top = top + 0.35 + (floors - 1) * 3.4
        self.bx(u0, u1, v0, v1, top - 0.02, top, shade(wall, -10), 'concreto')
        for (a, b, c, e) in ((u0 - 0.15, u1 + 0.15, v0 - 0.15, v0 + 0.15), (u0 - 0.15, u1 + 0.15, v1 - 0.15, v1 + 0.15), (u0 - 0.15, u0 + 0.15, v0, v1), (u1 - 0.15, u1 + 0.15, v0, v1)):
            self.bx(a, b, c, e, top, top + 1.0, shade(wall, -22), 'concreto')
        for k in range(r.randint(1, 3)):
            ua = r.uniform(u0 + 2, u1 - 4); va = r.uniform(v0 + 2, v1 - 4)
            self.bx(ua, ua + 2.2, va, va + 1.4, top, top + 1.3, (200, 202, 206), 'metal')
            self.cyl(ua + 1.1, va + 0.7, 0.45, top + 1.3, top + 1.4, (90, 94, 100), 'metal', 12)
        # marquise sobre a porta e letreiro com a cor da marca
        self.bx(dc - 3.0, dc + 3.0, v0 - 2.2, v0 - 0.15, Y0 + 3.1, Y0 + 3.3, (60, 64, 70), 'metal')
        self.M.m('liso'); self.M.poly([self.F.p(dc - 2.8, v0 - 2.0, Y0 + 3.09), self.F.p(dc + 2.8, v0 - 2.0, Y0 + 3.09), self.F.p(dc + 2.8, v0 - 0.3, Y0 + 3.09), self.F.p(dc - 2.8, v0 - 0.3, Y0 + 3.09)], GLOW, (0, -1, 0))
        self.bx(dc - 2.95, dc + 2.95, v0 - 2.2, v0 - 2.1, Y0 + 3.3, Y0 + 3.75, brand, 'liso')
        sw = min(w - 2, 10.0)
        self.bx(dc - sw / 2, dc + sw / 2, v0 - 0.32, v0 - 0.16, Y0 + HH - 0.95, Y0 + HH - 0.15, brand, 'liso')
        self.bx(dc - sw / 2 + 0.15, dc + sw / 2 - 0.15, v0 - 0.34, v0 - 0.32, Y0 + HH - 0.8, Y0 + HH - 0.3, (250, 250, 248), 'liso')
        for k in range(int(sw / 0.5) - 1):                            # "letras" do letreiro
            if r.random() < 0.8: self.bx(dc - sw / 2 + 0.4 + k * 0.5, dc - sw / 2 + 0.72 + k * 0.5, v0 - 0.35, v0 - 0.34, Y0 + HH - 0.72, Y0 + HH - 0.38, brand, 'liso')
        return u0, v0, u1, v1

    def wall_side(self, v0, v1, u, ops, wall):
        """parede lateral (u fixo) com janelas"""
        cuts = sorted(ops); v = v0
        for (va, vb, ya, yb, kind) in cuts + [(v1, v1, Y0, Y0 + HH, None)]:
            if va > v: self.bx(u - 0.15, u + 0.15, v, va, Y0, Y0 + HH, wall, 'reboco'); self.solid(u - 0.15, u + 0.15, v, va)
            if kind is None: break
            self.bx(u - 0.15, u + 0.15, va, vb, Y0, ya, wall, 'reboco'); self.bx(u - 0.15, u + 0.15, va, vb, yb, Y0 + HH, wall, 'reboco')
            self.bx(u - 0.02, u + 0.02, va, vb, ya, yb, (170, 200, 214), 'vidro'); self.solid(u - 0.15, u + 0.15, va, vb)
            for vv in (va, vb): self.bx(u - 0.17, u + 0.17, vv - 0.05, vv + 0.05, ya, yb, (236, 236, 232), 'metal')
            v = vb

    def forecourt(self, w, sv, brand, lot_w):
        """praca da entrada: piso, canteiros com arbustos, bicicletario, totem com a marca, mastro e postes"""
        r = self.r; dc = w / 2
        self.bx(-2.0, w + 2.0, 0.0, sv - 0.2, Y_WALK + 0.005, Y_WALK + 0.02, (226, 220, 210), 'paver')
        for s in (-1, 1):
            cu = dc + s * (w / 2 - 2.2)
            self.bx(cu - 1.6, cu + 1.6, 1.2, 3.2, Y_WALK, Y_WALK + 0.45, (190, 186, 178), 'concreto')
            self.bx(cu - 1.45, cu + 1.45, 1.35, 3.05, Y_WALK + 0.45, Y_WALK + 0.47, (92, 70, 50), 'liso')
            for k in range(3): x, z = self.F.xz(cu - 1.0 + k, 2.2); self.L.trees.append((x, z, 'flores' if k != 1 else 'arbusto', r.uniform(0.8, 1.1), Y_WALK + 0.47))
            self.solid(cu - 1.6, cu + 1.6, 1.2, 3.2)
        # totem
        tu = dc - w / 2 - 1.0 if w < lot_w - 6 else dc - 4.2
        self.bx(tu - 0.5, tu + 0.5, 0.6, 0.9, Y_WALK, Y_WALK + 2.6, (60, 64, 70), 'metal')
        self.bx(tu - 0.45, tu + 0.45, 0.58, 0.6, Y_WALK + 1.6, Y_WALK + 2.5, brand, 'liso')
        self.bx(tu - 0.35, tu + 0.35, 0.57, 0.58, Y_WALK + 1.9, Y_WALK + 2.2, (250, 250, 248), 'liso'); self.solid(tu - 0.5, tu + 0.5, 0.6, 0.9)
        # mastro
        mu = dc + w / 2 + 1.0 if w < lot_w - 6 else dc + 4.2
        self.cyl(mu, 1.0, 0.07, Y_WALK, Y_WALK + 8.5, (220, 220, 220), 'metal', 8, True, 0.05)
        G = self.sub(mu, 1.0, 0)
        self.bx(0.07, 1.5, -0.01, 0.01, Y_WALK + 7.4, Y_WALK + 8.3, brand, 'liso', F=G)
        # bicicletario
        for k in range(4):
            bu = dc + w / 2 - 4.5 + k * 0.7 if w > 14 else dc - 4 + k * 0.7
            for s in (-1, 1): self.bx(bu - 0.02, bu + 0.02, 4.6 + s * 0.3, 4.6 + s * 0.3 + 0.04, Y_WALK, Y_WALK + 0.75, STEEL, 'metal')
            self.bx(bu - 0.02, bu + 0.02, 4.3, 4.94, Y_WALK + 0.73, Y_WALK + 0.77, STEEL, 'metal')
        # postes da praca
        import lights6
        for pu in (dc - w / 2 + 0.8, dc + w / 2 - 0.8):
            x, z = self.F.xz(pu, 0.9); self.M.at(x, z, 'mobiliario'); lights6.post(self.M, x, z, Y_WALK, 'moderno'); self.M.free('lotes')
            self.L.props_lights.append((round(x, 1), round(z, 1), 12.0))


# ==================================================================== interiores por profissao
def interior(j, jid, u0, v0, u1, v1, brand):
    """divide o terreo em recepcao (frente), salas de trabalho (fundo) e apoio (copa/banheiros) e mobilia"""
    w = u1 - u0; d = v1 - v0; dc = (u0 + u1) / 2; r = j.r
    vf = v0 + d * 0.42                       # divisoria entre a frente e os fundos
    ua = u0 + w * 0.62                       # divisoria entre a sala principal e o apoio
    # iluminacao do forro: grade de paineis
    for uu in [u0 + 2.0 + k * 3.5 for k in range(int((w - 3) / 3.5) + 1)]:
        for vv in [v0 + 2.0 + k * 3.2 for k in range(int((d - 3) / 3.2) + 1)]:
            if uu < u1 - 1 and vv < v1 - 1: j.light(uu, vv)
    open_plan = jid in ('repositor', 'mecanico', 'bombeiro', 'lixeiro', 'entregador')
    if not open_plan:
        j.partition(u0 + 0.15, u1 - 0.15, vf, (dc, 1.6), glass=jid in ('programador', 'empresario', 'secretario', 'engenheiro', 'advogado'))
        j.partition_u(vf, v1 - 0.15, ua, ((vf + v1) / 2 + 1.5, 1.2))
        # apoio: copa e banheiros
        vm = (vf + v1) / 2
        j.partition(ua, u1 - 0.15, vm + 0.6, (ua + 1.2, 1.0))
        j.pantry(ua + 0.3, u1 - 0.3, vf + 0.3, vm + 0.3)
        j.restroom(ua + 0.2, u1 - 0.2, vm + 0.8, v1 - 0.2)
    # --- recepcao (comum a quase todos)
    def reception(col=brand):
        j.counter(dc + w * 0.18, v0 + 2.6, 0, 3.2, 0.7, (240, 238, 232), shade(col, -20))
        j.bx(dc + w * 0.18 - 1.6, dc + w * 0.18 + 1.6, v0 + 2.24, v0 + 2.25, Y0 + 0.3, Y0 + 0.8, col, 'liso')
        j.register(dc + w * 0.18 - 0.8, v0 + 2.6, 0)
        j.chair_at(*j.F.xz(dc + w * 0.18, v0 + 3.4), 2, (50, 54, 60))
        j.seats_row(u0 + 2.4, v0 + 1.4, 2, 4, shade(col, 10))
        j.seats_row(u0 + 1.0, v0 + 3.6, 1, 3, shade(col, 10))
        j.plant(u0 + 0.6, v0 + 0.8); j.plant(u1 - 0.6, v0 + 0.8, 1.2)
        j.water_cooler(u0 + 0.5, vf - 0.5)
        j.tv(u0 + 2.4, vf - 0.08, 2); j.clock(dc, vf - 0.07, 2)
        j.rug(dc - 1.8, dc + 1.8, v0 + 0.5, v0 + 2.0, shade(col, 30))
        j.art(u1 - 0.18, v0 + 3.5, 1, 1.2, 0.8)
    # --- salas por profissao
    back = (u0 + 0.4, ua - 0.4, vf + 0.4, v1 - 0.4)
    bu0, bu1, bv0, bv1 = back
    if jid == 'diarista':
        reception()
        for k in range(3): j.shelf(bu0 + 1.2 + k * 2.0, bv1 - 0.25, 2, 1.8, 2.0, 0.45, (200, 205, 210), 'caixas')
        for k in range(3):
            cu = bu0 + 1.0 + k * 1.3; j.cyl(cu, bv0 + 1.2, 0.28, Y0 + 0.08, Y0 + 0.5, (240, 200, 40), 'liso', 12); j.cyl(cu, bv0 + 1.2, 0.03, Y0 + 0.5, Y0 + 1.2, STEEL)    # baldes e esfregoes
            j.bx(cu - 0.15, cu + 0.15, bv0 + 1.15, bv0 + 1.25, Y0 + 1.2, Y0 + 1.25, (60, 140, 200))
        j.table((bu0 + bu1) / 2 + 1.0, (bv0 + bv1) / 2, 0, 2.0, 0.9); j.lockers(bu1 - 1.4, bv0 + 0.3, 0, 5, (64, 170, 200))
    elif jid == 'atendente':
        # lanchonete: balcao com chapa, coifa, cardapio luminoso, banquetas, mesas e cabines
        j.counter(dc, vf - 0.6, 0, w * 0.55, 0.7, (240, 238, 232), (200, 60, 50))
        for k in range(int(w * 0.55 / 0.8)): j.cyl(dc - w * 0.27 + 0.4 + k * 0.8, vf - 1.3, 0.2, Y0 + 0.7, Y0 + 0.76, (200, 60, 50), 'liso', 12); j.cyl(dc - w * 0.27 + 0.4 + k * 0.8, vf - 1.3, 0.04, Y0, Y0 + 0.7, STEEL)
        j.register(dc + 1.5, vf - 0.6, 0)
        for k in range(3): j.bx(dc - 3 + k * 2.1, dc - 1.1 + k * 2.1, vf - 0.1, vf - 0.08, Y0 + 2.4, Y0 + 3.2, GLOW, 'liso')     # cardapio aceso
        j.counter(dc, vf + 1.0, 2, w * 0.5, 0.8, (210, 210, 214), (120, 120, 126), 0.95)
        j.bx(dc - 1.5, dc + 0.5, vf + 0.7, vf + 1.3, Y0 + 0.95, Y0 + 1.0, (40, 40, 40), 'metal')                                       # chapa
        j.bx(dc - 1.7, dc + 0.7, vf + 0.6, vf + 1.4, Y0 + 2.4, Y0 + 2.9, (200, 200, 204), 'metal')                                   # coifa
        j.bx(bu0, bu0 + 0.8, bv1 - 1.0, bv1, Y0, Y0 + 1.9, (220, 220, 224), 'metal'); j.bx(bu0 + 0.9, bu0 + 1.7, bv1 - 1.0, bv1, Y0, Y0 + 1.9, (220, 220, 224), 'metal')
        j.shelf(bu1 - 1.2, bv1 - 0.25, 2, 2.0, 2.0, 0.45, (200, 200, 204), 'caixas')
        for k in range(2):
            tu = u0 + 2.0 + k * 3.5
            j.round_table(tu, v0 + 2.5, 0.45, (246, 246, 244), 3, (200, 60, 50))
        for k in range(2):                                         # cabines (booths) junto da parede lateral
            bv = v0 + 1.5 + k * 2.4
            j.table(u1 - 1.3, bv, 1, 1.2, 0.7, (240, 240, 236))
            for s in (-1, 1): j.bx(u1 - 2.0, u1 - 0.6, bv + s * 0.75 - 0.25, bv + s * 0.75 + 0.25, Y0, Y0 + 0.45, (200, 60, 50)); j.bx(u1 - 2.0, u1 - 0.6, bv + s * 1.0 - 0.06, bv + s * 1.0 + 0.06, Y0 + 0.45, Y0 + 1.1, (200, 60, 50))
        j.plant(u0 + 0.6, v0 + 0.8)
    elif jid in ('secretario', 'advogado', 'engenheiro', 'programador', 'empresario'):
        reception()
        # escritorio aberto com ilhas de estacoes, sala de reuniao, estantes
        n = max(1, int((bu1 - bu0 - 1) / 3.4))
        for i in range(n):
            for k in range(2):
                cu = bu0 + 1.7 + i * 3.4; cv = bv0 + 1.4 + k * 2.6
                if cv > bv1 - 1.0: continue
                j.workstation(cu - 0.85, cv, 0, brand if jid == 'programador' else (60, 70, 90)); j.workstation(cu + 0.85, cv, 0, (60, 70, 90))
        if jid == 'engenheiro':
            for k in range(2): j.table(bu1 - 1.2, bv0 + 1.2 + k * 1.8, 1, 1.4, 1.0, (240, 240, 236), 0.9); j.bx(bu1 - 1.65, bu1 - 0.75, bv0 + 0.8 + k * 1.8, bv0 + 1.6 + k * 1.8, Y0 + 0.9, Y0 + 0.905, (210, 225, 240))
        if jid == 'programador':
            for k in range(3): j.bx(bu1 - 0.9, bu1 - 0.3, bv1 - 1.0 - k * 0.8, bv1 - 0.4 - k * 0.8, Y0, Y0 + 2.0, (30, 32, 36), 'metal'); [j.bx(bu1 - 0.91, bu1 - 0.89, bv1 - 0.95 - k * 0.8, bv1 - 0.45 - k * 0.8, Y0 + 0.2 + q * 0.15, Y0 + 0.22 + q * 0.15, (60, 220, 120)) for q in range(12)]
            j.bx(u0 + 0.5, u0 + 2.5, vf - 0.6, vf - 0.3, Y0, Y0 + 0.8, (110, 70, 200)); j.sofa(dc - 2.5, vf - 1.3, 0, 2.2, (110, 70, 200))
        if jid in ('advogado', 'empresario'):
            j.shelf(bu0 + 1.1, bv1 - 0.25, 2, 2.0, 2.2, 0.4, WOOD, 'livros'); j.shelf(bu0 + 3.2, bv1 - 0.25, 2, 2.0, 2.2, 0.4, WOOD, 'pastas')
            j.table((bu0 + bu1) / 2, bv1 - 2.2, 0, 3.0, 1.2, (110, 76, 50))
            for s in (-1, 1):
                for k in range(3): j.chair((bu0 + bu1) / 2 - 1.0 + k * 1.0, bv1 - 2.2 + s * 0.95, 0 if s > 0 else 2, (60, 40, 30))
            j.rug(bu0 + 0.5, bu1 - 0.5, bv1 - 3.6, bv1 - 0.8, (140, 60, 50))
        j.shelf(ua - 0.7, bv0 + 1.2, 3, 1.6, 1.4, 0.45, (230, 230, 232), 'pastas')
        j.bx(ua - 1.1, ua - 0.5, bv0 + 2.4, bv0 + 3.0, Y0, Y0 + 1.05, (210, 212, 216)); j.bx(ua - 1.05, ua - 0.55, bv0 + 2.45, bv0 + 2.95, Y0 + 1.05, Y0 + 1.15, (60, 62, 66))   # impressora
        for k in range(3): j.plant(bu0 + 0.5 + k * 3.3, bv0 + 0.5, 0.9)
    elif jid == 'professor':
        reception((240, 180, 40))
        # sala de aula: quadro, mesa do professor, carteiras em fileiras, armario, mapas
        j.board((bu0 + bu1) / 2, bv1 - 0.06, 2, min(4.0, bu1 - bu0 - 1.5), 1.2)
        j.desk((bu0 + bu1) / 2, bv1 - 1.4, 2, 1.4, 0.7, False, WOOD)
        rows = int((bv1 - bv0 - 3.2) / 1.25); cols = int((bu1 - bu0 - 1) / 1.3)
        for i in range(cols):
            for k in range(rows):
                cu = bu0 + 0.9 + i * 1.3; cv = bv0 + 0.9 + k * 1.25
                j.table(cu, cv, 0, 0.75, 0.5, (190, 160, 110), 0.7); j.chair(cu, cv - 0.5, 0, (60, 120, 200), False)
        j.shelf(bu0 + 0.6, bv1 - 0.4, 3, 1.4, 1.6, 0.4, (240, 200, 90), 'livros')
        j.art(bu0 + 0.07, (bv0 + bv1) / 2, 3, 1.6, 1.0, 1.9, (120, 190, 220))
    elif jid == 'policial':
        reception((30, 60, 140))
        # sala dos investigadores e duas celas com grades
        j.workstation(bu0 + 1.2, bv0 + 1.2, 0, (30, 60, 140)); j.workstation(bu0 + 3.2, bv0 + 1.2, 0, (30, 60, 140))
        j.board(bu0 + 2.2, bv0 + 0.07, 0, 2.2, 1.0, (240, 240, 236))
        cw = (bu1 - bu0) / 2
        for k in range(2):
            ca = bu0 + k * cw; cv0 = bv1 - 3.0
            j.bx(ca + 0.05, ca + cw - 0.05, cv0, cv0 + 0.06, Y0 + 2.6, Y0 + 2.7, STEEL, 'metal'); j.bx(ca, ca + 0.08, cv0, bv1, Y0, Y0 + HH - 0.1, (200, 200, 196), 'reboco')
            q = ca + 0.2
            while q < ca + cw - 0.1:
                if abs(q - (ca + cw / 2)) > 0.45: j.cyl(q, cv0 + 0.03, 0.025, Y0, Y0 + 2.6, STEEL, 'metal', 6)
                q += 0.16
            j.solid(ca, ca + cw, cv0 - 0.03, cv0 + 0.09)
            j.bx(ca + 0.3, ca + cw - 0.3, bv1 - 0.8, bv1 - 0.1, Y0, Y0 + 0.45, (170, 172, 176), 'concreto'); j.bx(ca + 0.4, ca + 1.6, bv1 - 0.75, bv1 - 0.15, Y0 + 0.45, Y0 + 0.55, (90, 110, 140))
            j.cyl(ca + cw - 0.6, bv1 - 0.4, 0.2, Y0, Y0 + 0.4, (220, 220, 222), 'ceramica', 10)
        j.lockers(ua - 1.5, bv0 + 0.3, 0, 5, (60, 80, 120))
    elif jid == 'enfermeiro':
        reception((40, 160, 140))
        # consultorios: macas com lencol, biombo, armario de remedios, pia, balanca
        for k in range(2):
            mu = bu0 + 1.2 + k * ((bu1 - bu0) / 2)
            j.bx(mu - 0.4, mu + 0.4, bv1 - 2.3, bv1 - 0.4, Y0 + 0.6, Y0 + 0.75, (240, 244, 246)); j.bx(mu - 0.4, mu + 0.4, bv1 - 0.7, bv1 - 0.4, Y0 + 0.75, Y0 + 0.9, (220, 230, 240))
            for (a, b) in ((mu - 0.35, bv1 - 2.2), (mu + 0.35, bv1 - 2.2), (mu - 0.35, bv1 - 0.5), (mu + 0.35, bv1 - 0.5)): j.cyl(a, b, 0.025, Y0, Y0 + 0.6, STEEL, 'metal', 6)
            j.solid(mu - 0.4, mu + 0.4, bv1 - 2.3, bv1 - 0.4)
            j.bx(mu + 0.8, mu + 0.82, bv1 - 2.4, bv1 - 0.4, Y0 + 0.3, Y0 + 1.9, (150, 210, 200), 'liso')            # biombo
            j.desk(mu + 1.6, bv0 + 1.0, 0, 1.2, 0.6); j.chair(mu + 1.6, bv0 + 0.4, 0)
        j.shelf(ua - 0.6, bv0 + 1.5, 3, 1.2, 1.8, 0.4, (240, 240, 240), 'caixas')
        j.bx(bu0 + 0.2, bu0 + 0.6, bv0 + 0.3, bv0 + 0.7, Y0, Y0 + 0.08, (60, 60, 64)); j.cyl(bu0 + 0.4, bv0 + 0.5, 0.02, Y0, Y0 + 1.4, STEEL)
    elif jid == 'juiz':
        # forum: plenario com tribuna elevada, banco das partes, testemunha e galeria
        j.bx(dc - 2.0, dc + 2.0, v0 + 0.4, v0 + 1.4, Y0, Y0 + 1.1, (140, 100, 64))                  # balcao de atendimento
        j.seats_row(u0 + 2.2, v0 + 2.5, 1, 4, (110, 70, 50)); j.seats_row(u1 - 2.2, v0 + 2.5, 3, 4, (110, 70, 50))
        cu = (bu0 + bu1) / 2
        j.bx(cu - 3.0, cu + 3.0, bv1 - 2.4, bv1 - 0.4, Y0, Y0 + 0.45, (120, 84, 56), 'madeira')       # estrado
        j.bx(cu - 2.6, cu + 2.6, bv1 - 2.3, bv1 - 1.7, Y0 + 0.45, Y0 + 1.6, (110, 76, 50)); j.bx(cu - 2.7, cu + 2.7, bv1 - 2.35, bv1 - 1.65, Y0 + 1.6, Y0 + 1.68, (90, 60, 40))
        j.chair(cu, bv1 - 1.1, 2, (120, 30, 30)); j.bx(cu - 0.3, cu + 0.3, bv1 - 0.6, bv1 - 0.45, Y0 + 0.45, Y0 + 1.9, (120, 30, 30))
        j.solid(cu - 3.0, cu + 3.0, bv1 - 2.4, bv1 - 0.4)
        j.bx(cu - 1.0, cu + 1.0, bv1 - 0.1, bv1 - 0.06, Y0 + 2.2, Y0 + 3.4, (230, 200, 120), 'liso')    # brasao
        j.ball(cu, bv1 - 0.1, Y0 + 2.8, 0.35, (200, 170, 80))
        for s in (-1, 1): j.table(cu + s * 2.4, bv1 - 4.0, 0, 2.0, 0.8, (120, 84, 56)); j.chair(cu + s * 2.4 - 0.5, bv1 - 4.8, 0, (60, 40, 30)); j.chair(cu + s * 2.4 + 0.5, bv1 - 4.8, 0, (60, 40, 30))
        j.bx(bu1 - 1.6, bu1 - 0.6, bv1 - 3.0, bv1 - 2.0, Y0, Y0 + 1.1, (110, 76, 50)); j.solid(bu1 - 1.6, bu1 - 0.6, bv1 - 3.0, bv1 - 2.0)   # testemunha
        for k in range(2): j.bx(bu0 + 0.5, bu1 - 0.5, bv0 + 0.6 + k * 1.1, bv0 + 1.0 + k * 1.1, Y0, Y0 + 0.45, (120, 84, 56)); j.bx(bu0 + 0.5, bu1 - 0.5, bv0 + 0.92 + k * 1.1, bv0 + 1.0 + k * 1.1, Y0 + 0.45, Y0 + 0.95, (120, 84, 56)); j.solid(bu0 + 0.5, bu1 - 0.5, bv0 + 0.6 + k * 1.1, bv0 + 1.0 + k * 1.1)
        for s in (-1, 1): j.cyl(cu + s * 3.4, bv1 - 0.6, 0.03, Y0, Y0 + 2.4, (200, 170, 80)); j.bx(cu + s * 3.4, cu + s * 3.4 + 0.02, bv1 - 0.62, bv1 - 0.58, Y0 + 1.6, Y0 + 2.3, (30, 110, 60))
    elif jid == 'medico':
        reception((200, 40, 50))
        # enfermaria: leitos com cortina, suporte de soro, monitores; posto de enfermagem
        n = max(2, int((bu1 - bu0) / 2.6))
        for k in range(n):
            mu = bu0 + 1.3 + k * 2.6
            j.bx(mu - 0.5, mu + 0.5, bv1 - 2.3, bv1 - 0.3, Y0 + 0.45, Y0 + 0.62, (240, 244, 246)); j.bx(mu - 0.45, mu + 0.45, bv1 - 0.75, bv1 - 0.35, Y0 + 0.62, Y0 + 0.75, (250, 250, 250))
            j.bx(mu - 0.5, mu + 0.5, bv1 - 0.3, bv1 - 0.25, Y0 + 0.45, Y0 + 1.1, (200, 204, 208), 'metal'); j.bx(mu - 0.5, mu + 0.5, bv1 - 2.35, bv1 - 2.3, Y0 + 0.45, Y0 + 0.9, (200, 204, 208), 'metal')
            j.bx(mu - 0.45, mu + 0.45, bv1 - 1.9, bv1 - 0.9, Y0 + 0.62, Y0 + 0.66, (140, 190, 220))
            j.solid(mu - 0.5, mu + 0.5, bv1 - 2.35, bv1 - 0.25)
            j.cyl(mu + 0.75, bv1 - 0.6, 0.02, Y0, Y0 + 2.0, STEEL); j.bx(mu + 0.68, mu + 0.82, bv1 - 0.62, bv1 - 0.58, Y0 + 1.7, Y0 + 1.95, (220, 240, 250))
            j.bx(mu - 0.85, mu - 0.6, bv1 - 0.9, bv1 - 0.6, Y0 + 1.2, Y0 + 1.5, (30, 30, 34)); j.bx(mu - 0.84, mu - 0.61, bv1 - 0.91, bv1 - 0.9, Y0 + 1.24, Y0 + 1.46, (60, 200, 120))
            if k < n - 1: j.bx(mu + 1.25, mu + 1.27, bv1 - 2.6, bv1 - 0.2, Y0 + 0.3, Y0 + 2.2, (170, 210, 230), 'liso')
        j.counter(bu0 + 2.0, bv0 + 1.0, 0, 3.0, 0.7, (240, 244, 246), (200, 40, 50)); j.chair(bu0 + 1.5, bv0 + 1.8, 2); j.chair(bu0 + 2.5, bv0 + 1.8, 2)
    elif jid == 'bombeiro':
        # garagem com dois caminhoes, parede de equipamentos, armarios, mastro de descida, sala de estar
        for k in range(2): fire_truck(j, u0 + w * (0.28 + 0.44 * k), v0 + d * 0.48)
        for k in range(int(w / 1.6)):
            hu = u0 + 0.8 + k * 1.6; j.bx(hu - 0.3, hu + 0.3, v1 - 0.4, v1 - 0.2, Y0 + 1.4, Y0 + 2.2, (210, 180, 60)); j.cyl(hu, v1 - 0.3, 0.17, Y0 + 2.2, Y0 + 2.5, (220, 40, 30), 'liso', 10)   # casacos e capacetes
        j.lockers(u0 + 2.5, v1 - 1.2, 2, 6, (180, 40, 36))
        j.cyl(u1 - 1.5, v1 - 1.5, 0.05, Y0, Y0 + HH, (220, 220, 220)); j.cyl(u1 - 1.5, v1 - 1.5, 0.6, Y0, Y0 + 0.1, (200, 40, 36), 'liso', 12)
        j.sofa(u1 - 3.0, v1 - 3.0, 0, 2.2, (90, 60, 50)); j.tv(u1 - 3.0, v1 - 0.25, 2)
    elif jid == 'mecanico':
        # oficina: dois elevadores com carro, bancada de ferramentas, painel, pneus, compressor
        for k in range(2):
            lu = u0 + w * (0.27 + 0.46 * k); lv = v0 + d * 0.5
            for s in (-1, 1): j.bx(lu + s * 1.4 - 0.15, lu + s * 1.4 + 0.15, lv - 0.15, lv + 0.15, Y0, Y0 + 2.6, (40, 90, 160), 'metal'); j.solid(lu + s * 1.4 - 0.15, lu + s * 1.4 + 0.15, lv - 0.15, lv + 0.15)
            for s in (-1, 1): j.bx(lu - 1.2, lu + 1.2, lv + s * 0.9 - 0.08, lv + s * 0.9 + 0.08, Y0 + 1.6, Y0 + 1.7, (60, 60, 64), 'metal')
            x, z = j.F.xz(lu, lv); j.L.parked.append((x, z, j.F.vx, j.F.vz, Y0 + 1.72))
        j.bx(u0 + 0.5, u1 - 0.5, v1 - 0.8, v1 - 0.2, Y0, Y0 + 0.9, (180, 40, 36), 'metal'); j.bx(u0 + 0.45, u1 - 0.45, v1 - 0.85, v1 - 0.15, Y0 + 0.9, Y0 + 0.95, (110, 90, 70))
        j.bx(u0 + 0.5, u1 - 0.5, v1 - 0.22, v1 - 0.18, Y0 + 1.2, Y0 + 2.4, (200, 204, 208), 'metal')
        for k in range(int((w - 1) / 0.35)): j.bx(u0 + 0.7 + k * 0.35, u0 + 0.74 + k * 0.35, v1 - 0.25, v1 - 0.23, Y0 + 1.5 + (k % 3) * 0.25, Y0 + 1.75 + (k % 3) * 0.25, (60, 60, 64))
        j.solid(u0 + 0.5, u1 - 0.5, v1 - 0.85, v1 - 0.15)
        for k in range(5): j.cyl(u1 - 1.0, v0 + 1.2 + k * 0.3, 0.33, Y0, Y0 + 0.24, (30, 30, 30), 'liso', 12)
        j.cyl(u0 + 1.0, v0 + 1.2, 0.3, Y0, Y0 + 0.9, (200, 40, 36), 'metal', 12)
    elif jid == 'repositor':
        # supermercado: caixas, gondolas, frigorificos, hortifruti, carrinhos
        for k in range(3):
            cu = u0 + 2.5 + k * 3.0
            j.counter(cu, v0 + 2.6, 0, 1.6, 0.8, (240, 236, 228), (40, 40, 44), 0.9); j.register(cu + 0.5, v0 + 2.6, 0)
            j.bx(cu + 0.85, cu + 0.95, v0 + 2.1, v0 + 3.1, Y0, Y0 + 2.2, (200, 200, 200), 'metal'); j.bx(cu + 0.6, cu + 1.2, v0 + 2.5, v0 + 2.7, Y0 + 2.2, Y0 + 2.5, (230, 70, 50)); j.bx(cu + 0.7, cu + 1.1, v0 + 2.48, v0 + 2.5, Y0 + 2.25, Y0 + 2.45, GLOW)
        nrow = int((w - 4) / 2.8)
        for k in range(nrow):
            gu = u0 + 2.5 + k * 2.8
            gondola(j, gu, v0 + 5.0, v1 - 4.0)
        j.bx(u0 + 0.3, u1 - 0.3, v1 - 1.1, v1 - 0.2, Y0, Y0 + 2.1, (220, 228, 236), 'metal')          # frigorificos
        for k in range(int((w - 1) / 1.2)):
            fu = u0 + 0.5 + k * 1.2; j.bx(fu, fu + 1.1, v1 - 1.12, v1 - 1.1, Y0 + 0.2, Y0 + 2.0, (190, 220, 235), 'vidro')
            for q in range(5): j.bx(fu + 0.1, fu + 1.0, v1 - 0.9, v1 - 0.4, Y0 + 0.3 + q * 0.38, Y0 + 0.5 + q * 0.38, self_pick(j))
        j.solid(u0 + 0.3, u1 - 0.3, v1 - 1.1, v1 - 0.2)
        for k in range(4):                                           # hortifruti em bancas
            hu = u1 - 2.0; hv = v0 + 5.0 + k * 1.6
            if hv > v1 - 4: break
            j.bx(hu - 0.8, hu + 0.8, hv - 0.6, hv + 0.6, Y0, Y0 + 0.75, WOOD)
            for q in range(10): j.ball(hu - 0.6 + (q % 5) * 0.3, hv - 0.3 + (q // 5) * 0.5, Y0 + 0.85, 0.12, ((230, 60, 40), (250, 180, 40), (90, 170, 60), (240, 220, 80))[k])
            j.solid(hu - 0.8, hu + 0.8, hv - 0.6, hv + 0.6)
        for k in range(4): cart(j, u0 + 1.0, v0 + 0.8 + k * 0.4)
    elif jid in ('lixeiro', 'entregador'):
        # galpao: veiculos, estantes porta-palete com caixas/containers, escritorio envidracado
        if jid == 'lixeiro':
            for k in range(2): garbage_truck(j, u0 + w * (0.28 + 0.44 * k), v0 + d * 0.5)
            for k in range(6): j.bx(u0 + 1.0 + k * 1.4, u0 + 2.2 + k * 1.4, v1 - 1.4, v1 - 0.3, Y0, Y0 + 1.2, ((40, 120, 60), (220, 160, 40), (40, 90, 170), (180, 40, 36))[k % 4], 'metal'); j.solid(u0 + 1.0, u0 + 1.0 + 6 * 1.4, v1 - 1.4, v1 - 0.3)
        else:
            for k in range(3): j.shelf(u0 + 2.0 + k * 3.0, v1 - 0.6, 2, 2.6, 3.0, 0.9, (220, 120, 40), 'caixas')
            for k in range(4): moto(j, u0 + 1.5 + k * 1.4, v0 + 2.5)
            for k in range(8): j.bx(u1 - 4.0 + (k % 4) * 0.7, u1 - 3.4 + (k % 4) * 0.7, v0 + 5.0 + (k // 4) * 0.7, v0 + 5.6 + (k // 4) * 0.7, Y0, Y0 + 0.5, (196, 150, 100))
        ou0, ou1, ov0, ov1 = u1 - 5.5, u1 - 0.3, v0 + 0.3, v0 + 3.6
        j.wall_v(ou0, ou1, ov1, Y0, Y0 + 2.8, 0.1, (240, 240, 236), 'reboco', [(ou0 + 0.4, ou0 + 1.4, Y0, Y0 + 2.2, 'porta'), (ou0 + 1.8, ou1 - 0.4, Y0 + 0.9, Y0 + 2.4, 'janela')])
        j.workstation(ou0 + 2.5, ov0 + 1.3, 0, (240, 140, 40) if jid == 'entregador' else (70, 140, 70))
    elif jid == 'frentista':
        # loja de conveniencia do posto: balcao, prateleiras, geladeiras, cafe
        j.counter(dc + 2.0, v0 + 2.0, 0, 2.6, 0.7, (240, 236, 228), (30, 110, 190)); j.register(dc + 1.2, v0 + 2.0, 0)
        for k in range(2): gondola(j, u0 + 2.5 + k * 2.6, vf - 0.5, v1 - 1.5)
        j.bx(u1 - 1.0, u1 - 0.2, v0 + 3.5, v1 - 0.5, Y0, Y0 + 2.0, (220, 228, 236), 'metal'); j.solid(u1 - 1.0, u1 - 0.2, v0 + 3.5, v1 - 0.5)
        j.bx(u0 + 0.3, u0 + 1.3, v0 + 0.5, v0 + 1.1, Y0, Y0 + 0.95, (90, 60, 40)); j.bx(u0 + 0.5, u0 + 0.9, v0 + 0.6, v0 + 0.95, Y0 + 0.95, Y0 + 1.35, (30, 30, 30))
    return vf


def self_pick(j):
    return j.r.choice(((230, 230, 220), (250, 200, 60), (200, 60, 50), (60, 120, 200), (90, 170, 70)))


def gondola(j, u, v0, v1):
    """gondola dupla com produtos coloridos nos dois lados e cabeceira"""
    j.bx(u - 0.5, u + 0.5, v0, v1, Y0, Y0 + 0.1, (210, 212, 216), 'metal'); j.bx(u - 0.03, u + 0.03, v0, v1, Y0, Y0 + 1.8, (220, 222, 226), 'metal')
    for k in range(4):
        y = Y0 + 0.15 + k * 0.42
        for s in (-1, 1):
            j.bx(u + s * 0.03, u + s * 0.48, v0, v1, y, y + 0.03, (200, 202, 206), 'metal')
            vv = v0 + 0.05
            while vv < v1 - 0.2:
                L_ = j.r.uniform(0.15, 0.4); j.bx(u + s * 0.08, u + s * 0.42, vv, vv + L_ - 0.02, y + 0.03, y + 0.03 + j.r.uniform(0.15, 0.32), self_pick(j)); vv += L_
    j.bx(u - 0.5, u + 0.5, v0 - 0.08, v0, Y0 + 1.6, Y0 + 1.9, (230, 70, 50), 'liso')
    j.solid(u - 0.5, u + 0.5, v0, v1)


def cart(j, u, v):
    j.bx(u - 0.3, u + 0.3, v - 0.15, v + 0.25, Y0 + 0.35, Y0 + 0.85, (200, 204, 210), 'metal', False)
    for (a, b) in ((-0.25, -0.1), (0.25, -0.1), (-0.25, 0.2), (0.25, 0.2)): j.cyl(u + a, v + b, 0.05, Y0, Y0 + 0.1, DARK, 'liso', 6)


def fire_truck(j, u, v):
    G = j.sub(u, v, 1)
    j.bx(-4.2, 4.2, -1.25, 1.25, Y0 + 0.55, Y0 + 2.9, (200, 30, 28), 'metal', F=G)
    j.bx(2.6, 4.2, -1.25, 1.25, Y0 + 2.9, Y0 + 3.3, (200, 30, 28), 'metal', F=G)
    j.bx(2.9, 4.22, -1.15, 1.15, Y0 + 1.9, Y0 + 2.8, (40, 50, 60), 'vidro', F=G)
    j.bx(-4.0, 2.4, -0.9, 0.9, Y0 + 2.9, Y0 + 3.05, (200, 200, 204), 'metal', F=G)                       # escada
    for k in range(10): j.bx(-3.8 + k * 0.62, -3.75 + k * 0.62, -0.9, 0.9, Y0 + 3.05, Y0 + 3.1, (200, 200, 204), 'metal', F=G)
    for k in range(4): j.bx(-3.8 + k * 1.5, -2.6 + k * 1.5, -1.27, -1.25, Y0 + 1.1, Y0 + 2.4, (190, 190, 194), 'metal', F=G)
    j.bx(-4.2, 4.2, -1.27, -1.25, Y0 + 0.75, Y0 + 0.9, (250, 250, 248), F=G)
    for a in (-2.8, 2.8):
        for s in (-1, 1): x, z = G.xz(a, s * 1.15); j.M.m('liso'); j.M.cyl(x, z, 0.5, Y0, Y0 + 0.01, DARK, 3)
        for s in (-1, 1): j.cyl(a, s * 1.2, 0.5, Y0, Y0 + 0.12, (30, 30, 30), 'liso', 12, F=G)
    j.bx(3.0, 3.6, -0.6, 0.6, Y0 + 3.3, Y0 + 3.45, (60, 120, 230), F=G)
    j.solid(-4.2, 4.2, -1.25, 1.25, F=G)


def garbage_truck(j, u, v):
    G = j.sub(u, v, 1)
    j.bx(-3.8, 1.8, -1.2, 1.2, Y0 + 0.6, Y0 + 3.2, (60, 140, 70), 'metal', F=G)
    j.bx(1.8, 3.8, -1.15, 1.15, Y0 + 0.6, Y0 + 2.7, (250, 250, 248), 'metal', F=G)
    j.bx(2.6, 3.82, -1.05, 1.05, Y0 + 1.7, Y0 + 2.5, (40, 50, 60), 'vidro', F=G)
    j.bx(-4.0, -3.8, -1.1, 1.1, Y0 + 0.8, Y0 + 3.0, (240, 180, 40), 'metal', F=G)
    for a in (-2.6, -1.0, 2.8):
        for s in (-1, 1): j.cyl(a, s * 1.15, 0.48, Y0, Y0 + 0.12, (30, 30, 30), 'liso', 12, F=G)
    j.solid(-4.0, 3.8, -1.2, 1.2, F=G)


def moto(j, u, v):
    G = j.sub(u, v, 1)
    for a in (-0.6, 0.6): j.cyl(a, 0, 0.3, Y0, Y0 + 0.08, (30, 30, 30), 'liso', 12, F=G)
    j.bx(-0.6, 0.5, -0.12, 0.12, Y0 + 0.4, Y0 + 0.7, (240, 140, 40), 'metal', F=G)
    j.bx(-0.8, -0.3, -0.25, 0.25, Y0 + 0.7, Y0 + 1.1, (240, 140, 40), 'liso', F=G)                    # bau
    j.bx(0.5, 0.56, -0.3, 0.3, Y0 + 0.95, Y0 + 1.0, DARK, 'metal', F=G)
    j.solid(-0.8, 0.7, -0.3, 0.3, F=G)


# ==================================================================== montagem
def place_job(L, F, lot_w, jid):
    """um predio de profissao no lote (frente na rua); devolve o ponto da porta (mundo)"""
    nome, brand, floors, w, d, fl = JOBS[jid]
    w = min(w, lot_w - 4); sv = 6.0
    off = (lot_w - w) / 2
    Fb = Frame(F.xz(off, 0), (F.ux, F.uz)); Fb.vx, Fb.vz = F.vx, F.vz
    j = J(L, Fb)
    wall = {'empresario': (60, 66, 76), 'programador': (232, 234, 240), 'bombeiro': (180, 52, 44), 'juiz': (224, 214, 192),
            'medico': (244, 246, 248), 'advogado': (90, 70, 56), 'lixeiro': (150, 170, 150), 'mecanico': (120, 128, 136)}.get(jid, (232, 226, 214))
    x, z = F.xz(off + w / 2, sv / 2)
    L.M.at(x, z, 'lotes')
    garage = jid in ('bombeiro', 'mecanico', 'lixeiro', 'entregador')
    front_ops = None
    if garage:
        # portoes largos de garagem ao lado da porta de pedestres
        dc = w / 2
        front_ops = [(dc - 0.8, dc + 0.8, Y0, Y0 + 2.7, 'porta')]
        for s in (-1, 1):
            a = dc + s * 3.0; b = a + s * 6.0
            front_ops.append((min(a, b), max(a, b), Y0, Y0 + 3.8, 'porta'))
    u0, v0, u1, v1 = j.shell(w, d, floors, brand, fl, wall, sv, front_ops)
    if garage:
        for s in (-1, 1):                                            # portao de enrolar recolhido + faixas no piso
            a = w / 2 + s * 3.0; b = a + s * 6.0
            j.bx(min(a, b), max(a, b), v0 - 0.3, v0 + 0.3, Y0 + 3.8, Y0 + 4.1, (200, 200, 204), 'metal')
            j.bx(min(a, b), max(a, b), 0.0, v0 - 0.2, Y_WALK + 0.006, Y_WALK + 0.025, (190, 190, 190), 'concreto')
    interior(j, jid, u0 + 0.15, v0 + 0.15, u1 - 0.15, v1 - 0.15, brand)
    L.__dict__.setdefault('feet', []).append((Fb.rect(0, w, sv, sv + d), brand))
    j.forecourt(w, sv, brand, lot_w)
    L.M.free('lotes')
    dx, dz = Fb.xz(w / 2, sv - 2.0)
    L.jobs.append({'id': jid, 'nome': nome, 'x': round(dx, 1), 'z': round(dz, 1), 'cor': 0xFF000000 | (brand[0] << 16) | (brand[1] << 8) | brand[2], 'icone': nome[0], 'emoji': EMOJI.get(jid, '💼')})
    L.B.drives.append((*Fb.xz(w / 2, -1.5), 3.0))                   # nada de arvore/poste na frente da entrada
    return dx, dz


# ==================================================================== prefeitura
def prefeitura(L, F, Lw, D):
    """Paco Municipal: esplanada com fonte e jardins formais, palacio neoclassico sobre podio com escadaria, portico
    de 6 colunas com frontao e relogio, alas com janelas em arco e pilastras, balaustrada, cupula sobre tambor
    com colunata e lanterna. Dentro: atrio de marmore com piso xadrez e rotunda, atendimento ao cidadao,
    gabinete do prefeito e plenario da camara."""
    global Y0, HH
    old = (Y0, HH)
    r = L.rnd
    bw = min(Lw - 20, 66.0); bd = min(D - 34, 34.0)
    u0 = (Lw - bw) / 2; v0 = 26.0
    Fb = Frame(F.xz(u0, 0), (F.ux, F.uz)); Fb.vx, Fb.vz = F.vx, F.vz
    j = J(L, Fb); B = L.B; M = L.M
    stone = (236, 230, 216); stone2 = (214, 206, 190); trim = (246, 242, 232)
    x, z = Fb.xz(bw / 2, v0); M.at(x, z, 'lotes')
    # ---- esplanada
    Y0 = Y_WALK + 0.02
    j.bx(-u0 + 1, bw + u0 - 1, 0.0, v0 - 2.0, Y_WALK + 0.005, Y0, (232, 226, 214), 'paver')
    for k in range(int((bw + 2 * u0 - 4) / 2.0)):                       # faixas de pedra no piso
        uu = -u0 + 2 + k * 2.0; j.bx(uu, uu + 0.12, 0.5, v0 - 2.5, Y0, Y0 + 0.004, (196, 188, 172), 'pedra')
    fc = bw / 2; fv = v0 * 0.3
    j.cyl(fc, fv, 5.5, Y0, Y0 + 0.6, stone2, 'pedra', 32); j.cyl(fc, fv, 5.0, Y0 + 0.5, Y0 + 0.55, (90, 160, 200), 'agua', 32)
    j.cyl(fc, fv, 1.2, Y0 + 0.5, Y0 + 1.4, stone, 'pedra', 16); j.cyl(fc, fv, 2.4, Y0 + 1.4, Y0 + 1.6, stone, 'pedra', 16, True, 1.6)
    j.cyl(fc, fv, 0.4, Y0 + 1.6, Y0 + 2.6, stone, 'pedra', 12); j.cyl(fc, fv, 1.1, Y0 + 2.6, Y0 + 2.75, stone, 'pedra', 12)
    for k in range(12):                                                 # jatos
        a = 2 * math.pi * k / 12; jx, jz = fc + math.cos(a) * 3.4, fv + math.sin(a) * 3.4
        j.cyl(jx, jz, 0.06, Y0 + 0.55, Y0 + 1.5, (225, 240, 250), 'liso', 6, True, 0.02)
    j.solid(fc - 5.5, fc + 5.5, fv - 5.5, fv + 5.5)
    for s in (-1, 1):                                                   # jardins formais com cerca-viva e palmeiras imperiais
        gu = fc + s * (bw * 0.33)
        j.bx(gu - 9, gu + 9, 3.0, v0 - 6.0, Y0, Y0 + 0.08, (110, 160, 80), 'grama')
        for (a, b, c, e) in ((gu - 9, gu + 9, 3.0, 3.6), (gu - 9, gu + 9, v0 - 6.6, v0 - 6.0), (gu - 9, gu - 8.4, 3.0, v0 - 6.0), (gu + 8.4, gu + 9, 3.0, v0 - 6.0)):
            j.bx(a, b, c, e, Y0, Y0 + 0.75, (62, 110, 60), 'folhagem'); j.solid(a, b, c, e)
        for k in range(3):
            x2, z2 = Fb.xz(gu - 6 + k * 6, (v0 - 3) / 2); L.trees.append((x2, z2, 'palmeira', 1.5, Y0 + 0.08))
        # canteiros de flores em losango entre as palmeiras e estatua de bronze no pedestal
        for k in range(2):
            bu = gu - 3 + k * 6; bv = (v0 - 3) / 2
            j.bx(bu - 1.6, bu + 1.6, bv - 1.6, bv + 1.6, Y0 + 0.08, Y0 + 0.3, (210, 204, 190), 'pedra')
            for q in range(5):
                x2, z2 = Fb.xz(bu - 1.0 + q * 0.5, bv + (0.6 if q % 2 else -0.6)); L.trees.append((x2, z2, 'flores', 1.1, Y0 + 0.3))
        su, sv = gu + s * 6.5, 6.0
        j.bx(su - 0.9, su + 0.9, sv - 0.9, sv + 0.9, Y0 + 0.08, Y0 + 1.6, (226, 220, 206), 'pedra')
        j.bx(su - 1.05, su + 1.05, sv - 1.05, sv + 1.05, Y0 + 1.6, Y0 + 1.75, (210, 204, 190), 'pedra')
        j.cyl(su, sv, 0.32, Y0 + 1.75, Y0 + 3.0, (120, 96, 60), 'metal', 10); j.cyl(su, sv, 0.24, Y0 + 3.0, Y0 + 3.4, (120, 96, 60), 'metal', 10, True, 0.18)
        j.solid(su - 1.05, su + 1.05, sv - 1.05, sv + 1.05)
        for k in range(10): x2, z2 = Fb.xz(gu - 7 + (k % 5) * 3.5, 6.0 + (k // 5) * (v0 - 14)); L.trees.append((x2, z2, 'flores', 1.0, Y0 + 0.08))
    for k in range(3):                                                  # mastros (pais, estado, cidade)
        mu = fc - 3.0 + k * 3.0
        j.cyl(mu, v0 - 11.6, 0.3, Y0, Y0 + 0.5, stone2, 'pedra', 10); j.cyl(mu, v0 - 11.6, 0.08, Y0 + 0.5, Y0 + 12.0, (230, 230, 230), 'metal', 8, True, 0.05)
        G = j.sub(mu, v0 - 11.6, 0); j.bx(0.08, 2.0, -0.01, 0.01, Y0 + 10.6, Y0 + 11.8, ((40, 140, 70), (230, 200, 40), (40, 80, 170))[k], 'liso', F=G)
    import lights6
    for s in (-1, 1):
        for k in range(4):
            pu = fc + s * (7.0 + k * (bw * 0.12)); x2, z2 = Fb.xz(pu, 1.5)
            M.at(x2, z2, 'mobiliario'); lights6.post(M, x2, z2, Y0, 'globos5'); M.free('lotes'); L.props_lights.append((round(x2, 1), round(z2, 1), 13.0))
    # ---- podio e escadaria
    Yp = Y0 + 1.6
    j.bx(-1.0, bw + 1.0, v0, v0 + bd + 1.0, Y_WALK - 0.3, Yp, stone2, 'pedra')
    PF = v0 - 6.2                                                       # frente da plataforma do portico
    j.bx(fc - 11.0, fc + 11.0, PF, v0 + 0.02, Y_WALK - 0.3, Yp, stone2, 'pedra')       # o podio avanca sob o portico
    for k in range(8):                                                  # escadaria encostada na plataforma
        j.bx(fc - 10.6, fc + 10.6, PF - 4.0 + k * 0.5, PF + 0.02, Y_WALK - 0.3, Y0 + (k + 1) * 0.2 - 0.01, (224, 218, 204), 'pedra')
    for s in (-1, 1):                                                   # muretas laterais da escada com pinha
        j.bx(fc + s * 11.0 - 0.45, fc + s * 11.0 + 0.45, PF - 4.3, v0, Y_WALK - 0.3, Yp + 0.9, stone, 'pedra')
        j.ball(fc + s * 11.0, PF - 3.9, Yp + 1.25, 0.35, stone)
    # ---- casca: terreo enterravel, andar nobre e cobertura
    Y0 = Yp + 0.02; HH = 6.0
    pu0, pu1 = fc - 9.5, fc + 9.5
    ops = [(fc - 1.6, fc + 1.6, Y0, Y0 + 4.2, 'porta')]
    a = 1.5
    while a + 2.0 < bw - 1.5:
        if not (pu0 - 1.0 < a + 1.0 < pu1 + 1.0): ops.append((a, a + 2.0, Y0 + 1.0, Y0 + 4.4, 'janela'))
        a += 4.2
    for (pa, pb) in ((fc - 7.0, fc - 4.0), (fc + 4.0, fc + 7.0)): ops.append((pa, pb, Y0 + 1.0, Y0 + 4.4, 'janela'))
    j.wall_v(0, bw, v0 + 1.0, Y0, Y0 + HH, 0.4, stone, 'reboco', ops)
    j.wall_v(0, bw, v0 + bd, Y0, Y0 + HH, 0.4, stone, 'reboco', [(a, a + 2.0, Y0 + 1.2, Y0 + 4.2, 'janela') for a in [2.0 + k * 4.5 for k in range(int((bw - 4) / 4.5))]])
    j.wall_side(v0 + 1.0, v0 + bd, 0.0, [(v0 + 3 + k * 4.5, v0 + 5 + k * 4.5, Y0 + 1.2, Y0 + 4.2, 'janela') for k in range(int((bd - 6) / 4.5))], stone)
    j.wall_side(v0 + 1.0, v0 + bd, bw, [(v0 + 3 + k * 4.5, v0 + 5 + k * 4.5, Y0 + 1.2, Y0 + 4.2, 'janela') for k in range(int((bd - 6) / 4.5))], stone)
    for (a, b, c, e) in ((0, bw, v0 + 1.0, v0 + bd), ):
        pass
    for a in [1.0 + k * 4.2 for k in range(int((bw - 1) / 4.2) + 1)]:   # pilastras e arcos das janelas
        if a > bw - 0.5: break
        j.bx(a - 0.35, a + 0.35, v0 + 0.62, v0 + 0.8, Y0, Y0 + HH + 5.0, trim, 'reboco')
    j.bx(-0.3, bw + 0.3, v0 + 0.5, v0 + bd + 0.4, Y0 + HH, Y0 + HH + 0.5, trim, 'concreto')                    # cornija do terreo
    Yn = Y0 + HH + 0.5
    B.box(Fb, 0, bw, v0 + 1.0, v0 + bd, Yn, Yn + 5.0, stone, 'classica', False, wall_uv=(4.2, 5.0, Yn))           # andar nobre
    j.bx(-0.5, bw + 0.5, v0 + 0.4, v0 + bd + 0.5, Yn + 5.0, Yn + 5.7, trim, 'concreto')                         # entablamento
    j.bx(0, bw, v0 + 1.0, v0 + bd, Yn + 5.0, Yn + 5.05, stone2, 'concreto')
    for (a, b, c, e) in ((-0.3, bw + 0.3, v0 + 0.5, v0 + 0.8), (-0.3, bw + 0.3, v0 + bd + 0.1, v0 + bd + 0.4), (-0.3, 0.0, v0 + 0.5, v0 + bd + 0.4), (bw, bw + 0.3, v0 + 0.5, v0 + bd + 0.4)):
        j.bx(a, b, c, e, Yn + 5.7, Yn + 5.85, trim, 'concreto'); j.bx(a, b, c, e, Yn + 6.75, Yn + 6.9, trim, 'concreto')
    q = 0.3
    while q < bw - 0.2:                                                  # balaustres
        j.cyl(q, v0 + 0.65, 0.09, Yn + 5.85, Yn + 6.75, trim, 'concreto', 8, True, 0.06); q += 0.45
    # ---- portico: 6 colunas, frontao com relogio
    vp = v0 - 4.6
    j.bx(pu0 - 0.6, pu1 + 0.6, vp - 0.4, v0 + 1.0, Yp - 0.01, Yp + 0.02, (240, 236, 228), 'pedra')
    for k in range(6):
        cu = pu0 + (pu1 - pu0) * k / 5
        j.bx(cu - 0.75, cu + 0.75, vp - 0.75, vp + 0.75, Y0, Y0 + 0.5, trim, 'pedra')
        j.cyl(cu, vp, 0.62, Y0 + 0.5, Y0 + 0.75, trim, 'pedra', 16)
        j.cyl(cu, vp, 0.55, Y0 + 0.75, Yn + 4.4, stone, 'concreto', 16, False, 0.48)
        for f in range(12):                                             # caneluras
            a2 = 2 * math.pi * f / 12; j.bx(cu + math.cos(a2) * 0.5 - 0.03, cu + math.cos(a2) * 0.5 + 0.03, vp + math.sin(a2) * 0.5 - 0.03, vp + math.sin(a2) * 0.5 + 0.03, Y0 + 1.0, Yn + 4.2, stone2, 'concreto')
        j.cyl(cu, vp, 0.62, Yn + 4.4, Yn + 4.7, trim, 'concreto', 16); j.bx(cu - 0.8, cu + 0.8, vp - 0.8, vp + 0.8, Yn + 4.7, Yn + 5.0, trim, 'concreto')
        j.solid(cu - 0.6, cu + 0.6, vp - 0.6, vp + 0.6)
    j.bx(pu0 - 1.0, pu1 + 1.0, vp - 1.0, v0 + 1.0, Yn + 5.0, Yn + 5.9, trim, 'concreto')
    M.m('reboco')
    M.tri(Fb.p(pu0 - 1.0, vp - 1.0, Yn + 5.9), Fb.p(pu1 + 1.0, vp - 1.0, Yn + 5.9), Fb.p(fc, vp - 1.0, Yn + 10.2), stone, Fb.nv(-1))
    j.gable_roof = None
    M.m('telha')
    M.quad(Fb.p(pu0 - 1.3, vp - 1.3, Yn + 5.85), Fb.p(fc, vp - 1.3, Yn + 10.35), Fb.p(fc, v0 + 1.0, Yn + 10.35), Fb.p(pu0 - 1.3, v0 + 1.0, Yn + 5.85), (150, 150, 146), None)
    M.quad(Fb.p(fc, vp - 1.3, Yn + 10.35), Fb.p(pu1 + 1.3, vp - 1.3, Yn + 5.85), Fb.p(pu1 + 1.3, v0 + 1.0, Yn + 5.85), Fb.p(fc, v0 + 1.0, Yn + 10.35), (150, 150, 146), None)
    cx_, cz_ = Fb.xz(fc, vp - 1.05)                                     # relogio no frontao
    G = j.sub(fc, vp - 1.02, 0)
    j.bx(-1.05, 1.05, -0.08, 0.0, Yn + 6.2, Yn + 8.3, (220, 190, 110), 'liso', F=G)
    j.bx(-0.9, 0.9, -0.1, -0.08, Yn + 6.35, Yn + 8.15, (250, 248, 240), 'liso', F=G)
    for k in range(12):
        a2 = 2 * math.pi * k / 12; j.bx(math.cos(a2) * 0.75 - 0.04, math.cos(a2) * 0.75 + 0.04, -0.11, -0.1, Yn + 7.25 + math.sin(a2) * 0.75 - 0.04, Yn + 7.25 + math.sin(a2) * 0.75 + 0.04, DARK, 'liso', F=G)
    j.bx(-0.03, 0.03, -0.12, -0.11, Yn + 7.25, Yn + 7.85, DARK, 'liso', F=G); j.bx(0.0, 0.45, -0.12, -0.11, Yn + 7.22, Yn + 7.28, DARK, 'liso', F=G)
    # forro do portico com luminarias
    for k in range(5): j.light(pu0 + 1.9 + k * 3.8, vp + 2.6, 0.8, 0.8, Yn + 4.95)
    # ---- cupula: tambor com colunata, cupula, lanterna
    dv = v0 + bd * 0.55; Yd = Yn + 5.7
    j.cyl(fc, dv, 8.5, Yd, Yd + 4.5, stone, 'reboco', 32)
    for k in range(24):
        a2 = 2 * math.pi * k / 24; cu, cv = fc + math.cos(a2) * 8.9, dv + math.sin(a2) * 8.9
        j.cyl(cu, cv, 0.28, Yd, Yd + 4.4, trim, 'concreto', 8)
        if k % 3 == 0:
            G = j.sub(fc + math.cos(a2 + 0.13) * 8.52, dv + math.sin(a2 + 0.13) * 8.52, 0)
    j.cyl(fc, dv, 9.4, Yd + 4.4, Yd + 5.0, trim, 'concreto', 32)
    x3, z3 = Fb.xz(fc, dv); M.m('metal'); M.sphere(x3, Yd + 5.0, z3, 8.6, (110, 150, 140), 32, 10, 0.75)
    j.cyl(fc, dv, 1.4, Yd + 11.2, Yd + 13.2, trim, 'concreto', 12)
    for k in range(8):
        a2 = 2 * math.pi * k / 8; j.cyl(fc + math.cos(a2) * 1.5, dv + math.sin(a2) * 1.5, 0.12, Yd + 11.2, Yd + 13.2, trim, 'concreto', 6)
    j.ball(fc, dv, Yd + 13.6, 1.5, (110, 150, 140), 'metal')
    j.cyl(fc, dv, 0.06, Yd + 14.8, Yd + 18.5, (220, 200, 120), 'metal', 6)
    G = j.sub(fc, dv, 0); j.bx(0.06, 1.6, -0.01, 0.01, Yd + 17.2, Yd + 18.3, (40, 140, 70), 'liso', F=G)
    # telhado das alas
    j.bx(0, bw, v0 + 1.0, v0 + bd, Yn + 5.6, Yn + 5.7, (170, 170, 166), 'concreto')
    # ---- interior (terreo, pe-direito 6 m)
    iu0, iu1, iv0, iv1 = 0.4, bw - 0.4, v0 + 1.4, v0 + bd - 0.4
    j.bx(iu0, iu1, iv0, iv1, Y0 - 0.02, Y0, (238, 234, 226), 'pedra')
    q = 0                                                                # piso xadrez de marmore no atrio
    for i in range(int(18 / 1.2)):
        for k in range(int((bd * 0.55) / 1.2)):
            if (i + k) % 2 == 0: j.bx(fc - 9 + i * 1.2, fc - 7.8 + i * 1.2, iv0 + 0.4 + k * 1.2, iv0 + 1.6 + k * 1.2, Y0, Y0 + 0.003, (52, 56, 62), 'liso')
    j.ceiling(iu0, iu1, iv0, iv1)
    for uu in [iu0 + 2.5 + k * 4.0 for k in range(int((iu1 - iu0 - 3) / 4.0) + 1)]:
        for vv in [iv0 + 2.5 + k * 4.0 for k in range(int((iv1 - iv0 - 3) / 4.0) + 1)]: j.light(uu, vv, 0.9, 0.9)
    # lustre no atrio
    j.cyl(fc, iv0 + 7.0, 0.04, Y0 + HH - 1.6, Y0 + HH, (200, 170, 80), 'metal', 6)
    for k in range(8):
        a2 = 2 * math.pi * k / 8; j.ball(fc + math.cos(a2) * 1.0, iv0 + 7.0 + math.sin(a2) * 1.0, Y0 + HH - 1.6, 0.16, GLOW)
    j.ball(fc, iv0 + 7.0, Y0 + HH - 1.9, 0.3, GLOW)
    # divisorias: alas esquerda (atendimento) e direita (gabinete) separadas do atrio; plenario no fundo
    j.partition_u(iv0, iv1 - 9.0, fc - 10.0, (iv0 + 5.0, 2.2), (244, 238, 226))
    j.partition_u(iv0, iv1 - 9.0, fc + 10.0, (iv0 + 5.0, 2.2), (244, 238, 226))
    j.partition(iu0, iu1, iv1 - 9.0, (fc, 3.0), (244, 238, 226))
    # atrio: balcao de informacoes, bandeiras, bancos, vasos, painel do brasao
    j.counter(fc, iv0 + 9.5, 0, 4.0, 0.8, (240, 236, 226), (90, 60, 40)); j.chair_at(*Fb.xz(fc - 0.8, iv0 + 10.3), 2, (110, 30, 30)); j.chair_at(*Fb.xz(fc + 0.8, iv0 + 10.3), 2, (110, 30, 30))
    for k in range(3):
        mu = fc - 2.0 + k * 2.0; j.cyl(mu, iv1 - 9.6, 0.25, Y0, Y0 + 0.12, (200, 170, 80), 'metal'); j.cyl(mu, iv1 - 9.6, 0.03, Y0 + 0.12, Y0 + 2.6, (200, 170, 80), 'metal')
        G = j.sub(mu, iv1 - 9.6, 0); j.bx(0.03, 0.9, -0.01, 0.01, Y0 + 1.6, Y0 + 2.5, ((40, 140, 70), (230, 200, 40), (40, 80, 170))[k], 'liso', F=G)
    for s in (-1, 1):
        for k in range(2): j.bx(fc + s * 6.5 - 1.2, fc + s * 6.5 + 1.2, iv0 + 3.0 + k * 4.0 - 0.25, iv0 + 3.0 + k * 4.0 + 0.25, Y0, Y0 + 0.45, (140, 100, 64), 'liso'); j.solid(fc + s * 6.5 - 1.2, fc + s * 6.5 + 1.2, iv0 + 3.0 + k * 4.0 - 0.25, iv0 + 3.0 + k * 4.0 + 0.25)
        j.plant(fc + s * 8.8, iv0 + 1.0, 1.4); j.plant(fc + s * 8.8, iv1 - 10.0, 1.4)
    j.rug(fc - 1.6, fc + 1.6, iv0 + 0.4, iv0 + 8.5, (150, 40, 40))
    # atendimento ao cidadao (ala esquerda): guiches, senha, longarinas
    for k in range(3):
        gu = iu0 + 2.0 + k * 3.0
        if gu > fc - 11.5: break
        j.counter(gu, iv1 - 11.5, 2, 2.4, 0.7, (240, 236, 226), (40, 80, 170)); j.workstation(gu, iv1 - 10.6, 2, (40, 80, 170))
        j.bx(gu - 1.2, gu - 1.18, iv1 - 11.5, iv1 - 9.2, Y0, Y0 + 1.6, (200, 210, 220), 'vidro')
    j.tv(iu0 + 0.1, iv0 + 4.0, 3, 1.2, 2.6)
    for k in range(3): j.seats_row(iu0 + 4.0, iv0 + 2.0 + k * 1.6, 0, 5, (40, 80, 170))
    # gabinete do prefeito (ala direita): mesa grande, poltronas, estantes, bandeiras, retrato, sofa
    gu = fc + 10.0 + (iu1 - fc - 10.0) / 2
    j.rug(gu - 3.5, gu + 3.5, iv0 + 2.0, iv1 - 11.0, (120, 40, 40))
    j.desk(gu, iv1 - 12.5, 2, 2.4, 1.0, True, (110, 76, 50)); j.chair_at(*Fb.xz(gu, iv1 - 11.6), 2, (90, 20, 20))
    for s in (-1, 1): j.chair(gu + s * 0.7, iv1 - 13.7, 0, (90, 20, 20), False)
    j.shelf(gu - 2.2, iv1 - 9.3, 2, 2.0, 2.6, 0.4, (110, 76, 50), 'livros'); j.shelf(gu + 2.2, iv1 - 9.3, 2, 2.0, 2.6, 0.4, (110, 76, 50), 'livros')
    j.art(gu, iv1 - 9.08, 2, 1.2, 1.5, 2.6, (150, 110, 70))
    j.sofa(gu, iv0 + 2.6, 0, 2.6, (120, 40, 40)); j.table(gu, iv0 + 3.8, 0, 1.4, 0.7, (110, 76, 50), 0.45)
    for k in range(2): j.cyl(gu + 3.0, iv1 - 10.0 - k * 0.9, 0.2, Y0, Y0 + 0.08, (200, 170, 80), 'metal'); j.cyl(gu + 3.0, iv1 - 10.0 - k * 0.9, 0.03, Y0, Y0 + 2.4, (200, 170, 80), 'metal')
    # plenario (fundo): mesa diretora elevada, bancadas em semicirculo, tribuna e galeria
    pv = iv1 - 4.5
    j.bx(fc - 5.0, fc + 5.0, iv1 - 2.2, iv1 - 0.3, Y0, Y0 + 0.5, (120, 84, 56), 'madeira')
    j.bx(fc - 4.5, fc + 4.5, iv1 - 2.1, iv1 - 1.5, Y0 + 0.5, Y0 + 1.6, (110, 76, 50)); j.solid(fc - 5.0, fc + 5.0, iv1 - 2.2, iv1 - 0.3)
    for k in range(5): j.chair(fc - 3.2 + k * 1.6, iv1 - 0.9, 2, (110, 30, 30))
    j.bx(fc - 1.5, fc + 1.5, iv1 - 0.25, iv1 - 0.2, Y0 + 2.4, Y0 + 4.2, (230, 200, 120), 'liso'); j.ball(fc, iv1 - 0.25, Y0 + 3.3, 0.6, (200, 170, 80))
    for ring in range(2):
        R = 5.0 + ring * 1.8
        for k in range(9):
            a2 = math.pi * (0.15 + 0.7 * k / 8); cu, cv = fc + math.cos(a2) * R, pv - math.sin(a2) * R * 0.55
            G = j.sub(cu, cv, 0); j.bx(-0.55, 0.55, -0.25, 0.25, Y0, Y0 + 0.8, (120, 84, 56), F=G); j.bx(-0.6, 0.6, -0.3, 0.3, Y0 + 0.8, Y0 + 0.85, (90, 60, 40), F=G)
            j.chair(cu, cv - 0.7, 0, (40, 90, 60))
    j.bx(fc - 0.5, fc + 0.5, pv - 1.2, pv - 0.6, Y0, Y0 + 1.15, (110, 76, 50)); j.solid(fc - 0.5, fc + 0.5, pv - 1.2, pv - 0.6)
    M.free('lotes')
    dx, dz = Fb.xz(fc, v0 - 6.0)
    L.jobs.append({'id': 'prefeito', 'nome': 'Prefeitura', 'x': round(dx, 1), 'z': round(dz, 1), 'cor': 0xFFC9A227, 'icone': 'P', 'emoji': '🏛️'})
    L.B.solid(Fb, -1.0, bw + 1.0, v0 + bd + 0.5, v0 + bd + 1.0)
    L.__dict__.setdefault('feet', []).append((Fb.rect(-1.0, bw + 1.0, v0 - 4.6, v0 + bd + 1.0), (201, 162, 39)))
    Y0, HH = old
