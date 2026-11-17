"""Cidade 6 - arquitetura propria de cada profissao (predio principal do campus).

Cada profissao tem um projeto diferente, inspirado em tipologias reais:
  medico      hospital moderno (Einstein/Morumbi): embasamento de 3 andares com brises horizontais, duas laminas
              de internacao com janelas em fita, atrio de vidro, marquise do pronto-socorro, heliponto
  enfermeiro  clinica estilo Rede Sarah (Lele): bloco baixo e comprido, sheds curvos na cobertura, brises
  policial    delegacia brutalista: concreto aparente, aletas verticais, bloco em balanco sobre a entrada
  bombeiro    quartel historico de tijolo: portoes em arco com aduelas e pedra-chave, torre de mangueiras
  professor   escola FDE: bloco sobre pilotis, cobogo nas circulacoes, brises coloridos, mural
  juiz        forum neoclassico: escadaria, colunata com frontao, cupula com lanterna
  advogado    edificio art deco com escalonamentos, pilares continuos e coroa dourada
  secretario  modernismo internacional (Lever/Seagram): embasamento sobre pilotis e lamina de vidro verde
  empresario  torre corporativa com quinas chanfradas, recuos, aletas de LED e coroa com mastro
  programador sede de tecnologia em caixas empilhadas e deslocadas com terracos verdes
  engenheiro  high-tech (Pompidou): caixa de vidro com exoesqueleto de aco, contraventamento em X, dutos
  repositor   hipermercado: caixao alto, abobada sobre a entrada, letreiro enorme
  atendente   lanchonete retro (diner): pontas arredondadas, frisos cromados, neon, totem
  frentista   posto: cobertura grande com bombas na frente, loja de conveniencia atras, totem de precos
  diarista    escritorio de limpeza: quinas de vidro curvas, faixas em onda, bolhas
  mecanico    galpao com cobertura em dente de serra, portoes de enrolar com elevadores
  entregador  centro de distribuicao: docas com abrigos, caminhoes encostados, escritorio de vidro na quina
  lixeiro     central de triagem: galpao verde, silos, esteira inclinada, chamine
Referencial: u ao longo da rua (0..w), v para dentro (0..d), fachada principal em v=0 olhando para -v.
Cada build devolve (door_u, door_v): ponto da porta (o marcador de trabalho fica 1,5 m a frente)."""
import math
from mesh import shade
from roads6 import Y_WALK
from jobs6 import J, GLOW, DARK, STEEL, WOOD, Y0, HH
from jobs2_6 import sign_text

FH = 3.4
GLASS = (150, 186, 204)
GREEN_GLASS = (120, 170, 160)
DARK_GLASS = (70, 90, 110)
WHITE = (246, 246, 244)
CONC = (170, 168, 162)
GOLD = (214, 178, 96)
PI = math.pi


# ======================================================================== primitivas
def mass(j, u0, u1, v0, v1, y0, y1, col, mat, top=True, solid=True, uvf=None):
    """volume (caixa) com colisao; uvf=(su, sv, ytopo) alinha a textura de fachada aos andares"""
    if u1 < u0: u0, u1 = u1, u0
    if v1 < v0: v0, v1 = v1, v0
    j.B.box(j.F, u0, u1, v0, v1, y0, y1, col, mat, top, wall_uv=uvf)
    if solid and y0 < Y_WALK + 2.0: j.solid(u0, u1, v0, v1)


def faces(j, u0, u1, v0, v1):
    """as 4 faces de uma caixa como referenciais locais (face em v=0, para fora = -v): frente, direita, fundo, esquerda"""
    return [(J(j.L, j.sub(u0, v0, 0)), u1 - u0), (J(j.L, j.sub(u1, v0, 1)), v1 - v0),
            (J(j.L, j.sub(u1, v1, 2)), u1 - u0), (J(j.L, j.sub(u0, v1, 3)), v1 - v0)]


def roof(j, u0, u1, v0, v1, y, pcol=(220, 218, 212), par=0.9, deck=(176, 178, 182), equip=0, cap=(206, 208, 212)):
    """cobertura: laje, platibanda com rufo e equipamentos"""
    j.bx(u0 + 0.2, u1 - 0.2, v0 + 0.2, v1 - 0.2, y, y + 0.04, deck, 'concreto')
    if par > 0:
        for (a, b, c, e) in ((u0, u1, v0, v0 + 0.25), (u0, u1, v1 - 0.25, v1), (u0, u0 + 0.25, v0 + 0.25, v1 - 0.25), (u1 - 0.25, u1, v0 + 0.25, v1 - 0.25)):
            j.bx(a, b, c, e, y, y + par, pcol, 'concreto')
            j.bx(a - 0.04, b + 0.04, c - 0.04, e + 0.04, y + par, y + par + 0.06, cap, 'metal')
    r = j.r
    for k in range(equip):
        ua = r.uniform(u0 + 2.0, max(u0 + 2.5, u1 - 4.0)); va = r.uniform(v0 + 2.0, max(v0 + 2.5, v1 - 3.0))
        j.bx(ua, ua + 1.8, va, va + 1.2, y + 0.04, y + 1.2, (204, 206, 210), 'metal')
        j.cyl(ua + 0.9, va + 0.6, 0.42, y + 1.2, y + 1.26, (80, 84, 90), 'metal', 12)


def ribbon(jj, L, y, h, glass=GLASS, mull=1.5, mcol=DARK, m0=0.5, m1=None, mat='vidro'):
    """janela em fita (vidro continuo com montantes) na face de jj"""
    m1 = L - m0 if m1 is None else m1
    if m1 - m0 < 0.6: return
    jj.bx(m0, m1, -0.03, 0.0, y, y + h, glass, mat)
    q = m0
    while q <= m1 + 0.01:
        jj.bx(q - 0.04, q + 0.04, -0.07, -0.02, y, y + h, mcol, 'metal'); q += mull
    for yy in (y, y + h): jj.bx(m0 - 0.04, m1 + 0.04, -0.07, -0.02, yy - 0.04, yy + 0.04, mcol, 'metal')


def punched(jj, u, y, w, h, frame=(240, 238, 232), deep=0.18, glass=GLASS, sill=(214, 210, 200), mull=True, mat='vidro'):
    """janela recortada com requadro, peitoril e montante"""
    jj.bx(u - w / 2, u + w / 2, -0.02, 0.0, y, y + h, glass, mat)
    for (a, b, c, e) in ((u - w / 2 - 0.1, u - w / 2, y, y + h), (u + w / 2, u + w / 2 + 0.1, y, y + h), (u - w / 2 - 0.1, u + w / 2 + 0.1, y + h, y + h + 0.1)):
        jj.bx(a, b, -deep, 0.0, c, e, frame, 'liso')
    if mull: jj.bx(u - 0.03, u + 0.03, -0.06, -0.02, y, y + h, frame, 'metal')
    if sill: jj.bx(u - w / 2 - 0.16, u + w / 2 + 0.16, -deep - 0.06, 0.0, y - 0.1, y, sill, 'concreto')


def arch(jj, uc, y, r, t, depth, col, mat='reboco', fill=None, fill_mat='vidro', n=10, key=None):
    """arco de volta inteira na face (aduelas como aneis), fecho opcional e vidro em leque"""
    M = jj.M; F = jj.F; nrm = F.nv(-1)
    M.m(mat)
    for k in range(n):
        a0, a1 = PI * k / n, PI * (k + 1) / n
        pi0 = F.p(uc + r * math.cos(a0), -depth, y + r * math.sin(a0)); pi1 = F.p(uc + r * math.cos(a1), -depth, y + r * math.sin(a1))
        po0 = F.p(uc + (r + t) * math.cos(a0), -depth, y + (r + t) * math.sin(a0)); po1 = F.p(uc + (r + t) * math.cos(a1), -depth, y + (r + t) * math.sin(a1))
        M.quad(pi0, po0, po1, pi1, col, nrm)
        # intradorso e extradorso (espessura)
        am = (a0 + a1) / 2
        M.quad(pi0, pi1, F.p(uc + r * math.cos(a1), 0.0, y + r * math.sin(a1)), F.p(uc + r * math.cos(a0), 0.0, y + r * math.sin(a0)), shade(col, -12),
               (-(F.ux * math.cos(am)), -math.sin(am), -(F.uz * math.cos(am))))
        M.quad(po0, po1, F.p(uc + (r + t) * math.cos(a1), 0.0, y + (r + t) * math.sin(a1)), F.p(uc + (r + t) * math.cos(a0), 0.0, y + (r + t) * math.sin(a0)), col,
               (F.ux * math.cos(am), math.sin(am), F.uz * math.cos(am)))
    if fill is not None:
        M.m(fill_mat)
        pts = [F.p(uc + r * math.cos(PI * k / n), -0.02, y + r * math.sin(PI * k / n)) for k in range(n + 1)]
        M.poly(pts, fill, nrm)
        for k in range(1, 4):                                                    # raios do caixilho
            a = PI * k / 4
            jj.bx(uc + r * 0.5 * math.cos(a) - 0.03, uc + r * 0.5 * math.cos(a) + 0.03, -0.05, -0.02, y, y + r * math.sin(a) * 0.98, DARK, 'metal') if k == 2 else None
    if key:
        jj.bx(uc - 0.22, uc + 0.22, -depth - 0.08, 0.0, y + r - 0.05, y + r + t + 0.12, key, 'reboco')


def beam(M, a, b, t, col, mat='metal'):
    """barra de secao quadrada t entre dois pontos 3D quaisquer (diagonais de contraventamento, esteiras)"""
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    L = math.sqrt(dx * dx + dy * dy + dz * dz)
    if L < 1e-6: return
    dx, dy, dz = dx / L, dy / L, dz / L
    ux, uy, uz = (0, 1, 0) if abs(dy) < 0.9 else (1, 0, 0)
    px, py, pz = dy * uz - dz * uy, dz * ux - dx * uz, dx * uy - dy * ux
    pl = math.sqrt(px * px + py * py + pz * pz); px, py, pz = px / pl * t / 2, py / pl * t / 2, pz / pl * t / 2
    qx, qy, qz = dy * pz - dz * py, dz * px - dx * pz, dx * py - dy * px
    ql = math.sqrt(qx * qx + qy * qy + qz * qz); qx, qy, qz = qx / ql * t / 2, qy / ql * t / 2, qz / ql * t / 2
    M.m(mat)
    cs = [(px + qx, py + qy, pz + qz), (-px + qx, -py + qy, -pz + qz), (-px - qx, -py - qy, -pz - qz), (px - qx, py - qy, pz - qz)]
    for i in range(4):
        c0, c1 = cs[i], cs[(i + 1) % 4]
        nx, ny, nz = (c0[0] + c1[0]), (c0[1] + c1[1]), (c0[2] + c1[2])
        M.quad((a[0] + c0[0], a[1] + c0[1], a[2] + c0[2]), (b[0] + c0[0], b[1] + c0[1], b[2] + c0[2]),
               (b[0] + c1[0], b[1] + c1[1], b[2] + c1[2]), (a[0] + c1[0], a[1] + c1[1], a[2] + c1[2]), col, (nx, ny, nz))


def vault(j, u0, u1, vc, rad, y, col, mat='metal', n=10, axis='u', end=True, endcol=None):
    """abobada (meio cilindro) com eixo ao longo de u (de u0 a u1) centrada em v=vc, nascendo em y"""
    M = j.M; F = j.F; M.m(mat)
    for k in range(n):
        a0, a1 = PI * k / n, PI * (k + 1) / n; am = (a0 + a1) / 2
        p = [F.p(u0, vc + rad * math.cos(a0), y + rad * math.sin(a0)), F.p(u1, vc + rad * math.cos(a0), y + rad * math.sin(a0)),
             F.p(u1, vc + rad * math.cos(a1), y + rad * math.sin(a1)), F.p(u0, vc + rad * math.cos(a1), y + rad * math.sin(a1))]
        M.quad(*p, col, (F.vx * math.cos(am), math.sin(am), F.vz * math.cos(am)))
        M.quad(*p, shade(col, -30), (-F.vx * math.cos(am), -math.sin(am), -F.vz * math.cos(am)))   # face de baixo
    if end:
        for uu, s in ((u0, -1), (u1, 1)):
            M.m('vidro' if endcol is None else mat)
            M.poly([F.p(uu, vc + rad * math.cos(PI * k / n), y + rad * math.sin(PI * k / n)) for k in range(n + 1)], endcol or GLASS, F.nu(s))


def flag(j, u, v, h, col):
    j.cyl(u, v, 0.06, Y_WALK, Y_WALK + h, (232, 232, 234), 'metal', 8)
    j.ball(u, v, Y_WALK + h + 0.08, 0.1, GOLD, 'metal')
    G = j.sub(u, v, 0); J(j.L, G).bx(0.07, 1.9, -0.01, 0.01, Y_WALK + h - 1.3, Y_WALK + h - 0.1, col, 'liso')


def planter(j, u0, u1, v0, v1, kind='arbusto', h=0.55):
    j.bx(u0, u1, v0, v1, Y_WALK, Y_WALK + h, (196, 190, 178), 'reboco')
    j.bx(u0 + 0.12, u1 - 0.12, v0 + 0.12, v1 - 0.12, Y_WALK + h, Y_WALK + h + 0.03, (86, 66, 48), 'liso')
    j.solid(u0, u1, v0, v1)
    n = max(1, int((max(u1 - u0, v1 - v0)) / 1.6))
    for k in range(n):
        t = (k + 0.5) / n
        uu = u0 + (u1 - u0) * (t if u1 - u0 >= v1 - v0 else 0.5); vv = v0 + (v1 - v0) * (t if v1 - v0 > u1 - u0 else 0.5)
        x, z = j.F.xz(uu, vv); j.L.trees.append((x, z, kind, 0.9, Y_WALK + h + 0.03))


def bollards(j, u0, u1, v, step=1.6):
    q = u0
    while q <= u1 + 0.01: j.cyl(q, v, 0.11, Y_WALK, Y_WALK + 0.85, (64, 66, 70), 'metal', 8); j.cyl(q, v, 0.12, Y_WALK + 0.7, Y_WALK + 0.76, GLOW, 'liso', 8); q += step


def glass_door(j, u, v, w=2.2, h=2.7, frame=DARK, canopy=None):
    """porta dupla de vidro fechada (sem interior) com puxadores; v = face"""
    j.bx(u - w / 2 - 0.12, u + w / 2 + 0.12, v - 0.1, v + 0.02, Y_WALK + 0.15, Y_WALK + 0.15 + h + 0.12, frame, 'metal')
    j.bx(u - w / 2, u + w / 2, v - 0.14, v - 0.1, Y_WALK + 0.15, Y_WALK + 0.15 + h, (120, 160, 182), 'vidro')
    j.bx(u - 0.02, u + 0.02, v - 0.16, v - 0.1, Y_WALK + 0.15, Y_WALK + 0.15 + h, frame, 'metal')
    for s in (-1, 1): j.bx(u + s * 0.14 - 0.025, u + s * 0.14 + 0.025, v - 0.22, v - 0.16, Y_WALK + 1.0, Y_WALK + 1.8, (210, 210, 214), 'metal')
    j.bx(u - w / 2 - 0.3, u + w / 2 + 0.3, v - 1.4, v, Y_WALK, Y_WALK + 0.15, (150, 146, 140), 'reboco')
    if canopy:
        j.bx(u - canopy[0] / 2, u + canopy[0] / 2, v - canopy[1], v, Y_WALK + h + 0.6, Y_WALK + h + 0.8, (60, 64, 70), 'metal')
        j.M.m('liso'); j.M.poly([j.F.p(u - canopy[0] / 2 + 0.2, v - canopy[1] + 0.2, Y_WALK + h + 0.59), j.F.p(u + canopy[0] / 2 - 0.2, v - canopy[1] + 0.2, Y_WALK + h + 0.59),
                                 j.F.p(u + canopy[0] / 2 - 0.2, v - 0.1, Y_WALK + h + 0.59), j.F.p(u - canopy[0] / 2 + 0.2, v - 0.1, Y_WALK + h + 0.59)], GLOW, (0, -1, 0))


def letters(j, text, uc, v, y, h, col, maxw=None, back=None, pad=0.5):
    """letreiro em relevo; com back=(cor) ganha placa atras"""
    if back:
        px = h / 7.0; w = len(text) * 6 * px - px
        if maxw and w > maxw: w = maxw; h = h * maxw / (len(text) * 6 * px - px)
        j.bx(uc - w / 2 - pad, uc + w / 2 + pad, v - 0.1, v, y - pad * 0.6, y + h + pad * 0.6, back, 'liso')
        v = v - 0.1
    sign_text(j, text, uc, v, y, h, col, 0.07, maxw)


def floors_grid(jj, L, ybase, nfl, fh, fn):
    for f in range(nfl): fn(jj, L, ybase + f * fh, f)


# ======================================================================== 1. hospital
def medico(j, w, d, nf, spec):
    acc = spec[7]; pod = 3; yp = Y_WALK + 0.15 + HH + (pod - 1) * FH         # topo do embasamento
    # embasamento: brises horizontais brancos sobre fita de vidro azul
    mass(j, 0, w, 2.0, d, Y_WALK, yp, (236, 238, 240), 'reboco')
    for (jj, L) in faces(j, 0, w, 2.0, d):
        for f in range(pod):
            y = Y_WALK + 0.15 + (0 if f == 0 else HH + (f - 1) * FH)
            if f > 0: ribbon(jj, L, y + 0.9, 1.7, (140, 180, 206), 1.8, (220, 222, 226))
            jj.bx(-0.2, L + 0.2, -1.0, 0.0, y + (HH if f == 0 else FH) - 0.25, y + (HH if f == 0 else FH) + 0.05, WHITE, 'liso')   # brise horizontal
    # terreo: pele de vidro recuada com pilares
    jf = faces(j, 0, w, 2.0, d)[0][0]
    ribbon(jf, w, Y_WALK + 0.3, 3.4, (120, 160, 186), 2.0, DARK, 1.0, w - 1.0)
    for k in range(int(w / 8) + 1): j.cyl(1.0 + k * (w - 2) / max(1, int(w / 8)), 1.2, 0.35, Y_WALK, Y_WALK + 0.15 + HH, WHITE, 'concreto', 12)
    # duas laminas de internacao
    tw = min(30.0, w * 0.34); td = min(16.0, d - 6); ytop = yp + (nf - pod) * FH
    blades = ((3.0, 3.0 + tw), (w - 3.0 - tw, w - 3.0))
    for bi, (a, b) in enumerate(blades):
        v0 = 6.0; v1 = v0 + td
        mass(j, a, b, v0, v1, yp, ytop + (FH if bi == 1 else 0), (244, 246, 248), 'reboco', solid=False)
        yt = ytop + (FH if bi == 1 else 0)
        for (jj, L) in faces(j, a, b, v0, v1):
            for f in range(int((yt - yp) / FH)):
                y = yp + f * FH
                ribbon(jj, L, y + 0.9, 1.5, (150, 196, 220), 1.4, (210, 214, 220), 0.8)
                jj.bx(0.0, L, -0.12, 0.0, y - 0.05, y + 0.25, (226, 230, 234), 'concreto')
        # nucleo de escada em vidro azul (faixa vertical) e cruz vermelha no topo
        G = faces(j, a, b, v0, v1)[0][0]
        G.bx(tw / 2 - 1.4, tw / 2 + 1.4, -0.35, 0.0, yp, yt + 1.6, (90, 140, 190), 'vidro')
        roof(j, a, b, v0, v1, yt, (238, 240, 242), 1.0, equip=0 if bi == 0 else 3)
        if bi == 0:                                                     # heliponto
            hu, hv = (a + b) / 2, (v0 + v1) / 2; R = min(tw, td) / 2 - 0.6
            j.cyl(hu, hv, R, yt + 1.0, yt + 1.25, (80, 86, 94), 'concreto', 24)
            j.cyl(hu, hv, R - 0.4, yt + 1.25, yt + 1.27, (246, 246, 246), 'liso', 24)
            j.cyl(hu, hv, R - 0.8, yt + 1.27, yt + 1.29, (80, 86, 94), 'concreto', 24)
            for (a_, b_, c_, e_) in ((-2.2, -1.4, -2.6, 2.6), (1.4, 2.2, -2.6, 2.6), (-1.4, 1.4, -0.4, 0.4)): j.bx(hu + a_, hu + b_, hv + c_, hv + e_, yt + 1.29, yt + 1.32, (250, 250, 250), 'liso')
            for k in range(16): a_ = 2 * PI * k / 16; j.ball(hu + math.cos(a_) * (R - 0.2), hv + math.sin(a_) * (R - 0.2), yt + 1.33, 0.08, (60, 220, 90), 'liso')
            for (pu, pv) in ((hu - R * 0.7, hv - R * 0.7), (hu + R * 0.7, hv - R * 0.7), (hu - R * 0.7, hv + R * 0.7), (hu + R * 0.7, hv + R * 0.7)):
                j.cyl(pu, pv, 0.2, yt + 1.06, yt + 1.0 + 0.04, DARK, 'metal', 6)
        else:
            G2 = J(j.L, j.sub((a + b) / 2, v0 - 0.4, 0))
            G2.bx(-1.6, 1.6, -0.3, 0.0, yt + 2.2, yt + 3.2, (220, 30, 40), 'liso'); G2.bx(-0.5, 0.5, -0.3, 0.0, yt + 1.1, yt + 4.3, (220, 30, 40), 'liso')
            G2.bx(-1.8, 1.8, -0.02, 0.3, yt + 1.0, yt + 4.5, WHITE, 'liso')
    # atrio de vidro entre as laminas (entrada principal)
    au0, au1 = blades[0][1] + 2.0, blades[1][0] - 2.0; door_u = (au0 + au1) / 2
    if au1 - au0 > 6:
        mass(j, au0, au1, -1.0, 2.2, Y_WALK, yp + FH, (150, 190, 214), 'vidro', solid=True)
        G = J(j.L, j.sub(au0, -1.0, 0)); q = 0.0
        while q <= au1 - au0 + 0.01: G.bx(q - 0.06, q + 0.06, -0.1, 0.0, Y_WALK, yp + FH, (230, 232, 236), 'metal'); q += 1.8
        for k in range(int((yp + FH - Y_WALK) / 1.8)): G.bx(0, au1 - au0, -0.1, 0.0, Y_WALK + 1.8 * (k + 1) - 0.05, Y_WALK + 1.8 * (k + 1) + 0.05, (230, 232, 236), 'metal')
        j.bx(au0 - 0.3, au1 + 0.3, -1.3, 2.4, yp + FH, yp + FH + 0.5, WHITE, 'metal')
        letters(j, spec[0], door_u, -1.3, yp + FH - 1.9, 1.1, (200, 30, 40), au1 - au0 - 2.0, (250, 250, 250))
    glass_door(j, door_u, -1.0, 3.0, 2.8)
    # marquise do pronto-socorro (lado esquerdo) com faixa EMERGENCIA
    eu = blades[0][0] + tw * 0.5
    j.bx(eu - 7.0, eu + 7.0, -4.5, 2.0, Y_WALK + 4.4, Y_WALK + 4.9, WHITE, 'metal')
    j.bx(eu - 7.05, eu + 7.05, -4.55, -4.45, Y_WALK + 4.4, Y_WALK + 4.9, (210, 30, 40), 'liso')
    letters(j, 'EMERGENCIA', eu, -4.55, Y_WALK + 4.45, 0.38, (255, 255, 255))
    for s in (-1, 1): j.cyl(eu + s * 6.4, -4.0, 0.2, Y_WALK, Y_WALK + 4.4, (230, 230, 232), 'metal', 10); j.solid(eu + s * 6.4 - 0.2, eu + s * 6.4 + 0.2, -4.2, -3.8)
    j.M.m('liso'); j.M.poly([j.F.p(eu - 6.6, -4.2, Y_WALK + 4.39), j.F.p(eu + 6.6, -4.2, Y_WALK + 4.39), j.F.p(eu + 6.6, 1.8, Y_WALK + 4.39), j.F.p(eu - 6.6, 1.8, Y_WALK + 4.39)], GLOW, (0, -1, 0))
    glass_door(j, eu, 2.0, 3.6, 2.8)
    roof(j, 0, w, 2.0, d, yp, (236, 238, 240), 0.9, equip=4)
    planter(j, au0 - 6.0, au0 - 1.5, -3.6, -2.2); planter(j, au1 + 1.5, au1 + 6.0, -3.6, -2.2)
    return door_u, -1.0


# ======================================================================== 2. clinica (Sarah)
def enfermeiro(j, w, d, nf, spec):
    acc = spec[7]; nf = 2; yt = Y_WALK + 0.15 + HH + FH
    mass(j, 0, w, 3.0, d, Y_WALK, yt, (248, 248, 246), 'reboco')
    for (jj, L) in faces(j, 0, w, 3.0, d):
        ribbon(jj, L, Y_WALK + 0.9, 2.6, (150, 196, 210), 1.6, (240, 240, 240), 0.8)
        ribbon(jj, L, Y_WALK + 0.15 + HH + 0.8, 1.6, (150, 196, 210), 1.6, (240, 240, 240), 0.8)
        # brises horizontais em aluminio na cor da clinica (tres laminas por andar)
        for y in (Y_WALK + 0.15 + HH - 0.3, yt - 0.4):
            for k in range(3): jj.bx(0.2, L - 0.2, -1.1 + k * 0.05, -0.75 + k * 0.05 if k else -0.75, y - 0.55 * k - 0.06, y - 0.55 * k, acc if k == 0 else (232, 234, 236), 'metal')
    # sheds curvos (quarto de cilindro) em sequencia ao longo da profundidade, abertos para o norte (vidro)
    sw = 4.6; n = int((d - 3.0) / sw); M = j.M; F = j.F
    for k in range(n):
        v0 = 3.0 + k * sw; v1 = v0 + sw; seg = 7
        M.m('metal')
        for s in range(seg):
            a0 = PI / 2 * s / seg; a1 = PI / 2 * (s + 1) / seg
            y0_ = yt + 2.4 * math.sin(a0); y1_ = yt + 2.4 * math.sin(a1)
            vv0 = v1 - sw * (1 - math.cos(a0))
            vv1 = v1 - sw * (1 - math.cos(a1))
            p = [F.p(0.3, vv0, y0_), F.p(w - 0.3, vv0, y0_), F.p(w - 0.3, vv1, y1_), F.p(0.3, vv1, y1_)]
            am = (a0 + a1) / 2
            M.quad(*p, (236, 238, 240), (F.vx * math.sin(am) * 0.6, math.cos(am) + 0.2, F.vz * math.sin(am) * 0.6))
            M.quad(*p, (210, 214, 218), (0, -1, 0))
        # face envidracada do shed (vertical, voltada para a frente) e testeiras
        j.bx(0.3, w - 0.3, v0 - 0.02, v0 + 0.02, yt, yt + 2.4, (130, 176, 200), 'vidro', False)
        for uu in (0.3, w - 0.3):
            M.m('reboco'); M.poly([F.p(uu, v1, yt), F.p(uu, v0, yt), F.p(uu, v0, yt + 2.4)] + [F.p(uu, v1 - sw * (1 - math.cos(PI / 2 * s / seg)), yt + 2.4 * math.sin(PI / 2 * s / seg)) for s in range(seg, 0, -1)][:0], acc, F.nu(-1 if uu < 1 else 1))
        q = 1.5
        while q < w - 1: j.bx(q - 0.05, q + 0.05, v0 - 0.06, v0 + 0.04, yt, yt + 2.4, (240, 240, 240), 'metal'); q += 2.4
    # varanda-jardim na frente com pergolado e entrada
    door_u = w / 2
    j.bx(door_u - 6.0, door_u + 6.0, -2.0, 3.0, Y_WALK + 3.3, Y_WALK + 3.55, acc, 'metal')
    for s in (-1, 1): j.cyl(door_u + s * 5.6, -1.6, 0.16, Y_WALK, Y_WALK + 3.3, WHITE, 'metal', 10); j.solid(door_u + s * 5.6 - 0.16, door_u + s * 5.6 + 0.16, -1.76, -1.44)
    letters(j, spec[0], door_u, -2.0, Y_WALK + 3.62, 0.7, acc, 11.0)
    glass_door(j, door_u, 3.0, 3.0, 2.7)
    G = J(j.L, j.sub(w - 4.0, -0.4, 0))
    G.bx(-1.4, 1.4, -0.2, 0.0, Y_WALK + 6.0, Y_WALK + 6.8, acc, 'liso'); G.bx(-0.4, 0.4, -0.2, 0.0, Y_WALK + 5.0, Y_WALK + 7.8, acc, 'liso')
    for k in range(int(w / 10)):
        u = 4.0 + k * 10.0
        if abs(u - door_u) > 8 and u < w - 3: planter(j, u - 2.0, u + 2.0, 0.6, 2.4, 'flores' if k % 2 else 'arbusto', 0.5)
    return door_u, 3.0


# ======================================================================== 3. delegacia brutalista
def policial(j, w, d, nf, spec):
    acc = spec[7]; C = (176, 174, 168); yt = Y_WALK + 0.15 + HH + (nf - 1) * FH
    # bloco base recuado (vidro escuro e concreto) e bloco superior em balanco
    mass(j, 0, w, 4.0, d, Y_WALK, Y_WALK + 0.15 + HH, C, 'concreto')
    jf = faces(j, 0, w, 4.0, d)
    for (jj, L) in jf:
        q = 1.2
        while q < L - 2: punched(jj, q + 0.9, Y_WALK + 1.4, 1.8, 2.2, (60, 62, 66), 0.3, DARK_GLASS, None); q += 3.6
    mass(j, 0, w, 0.0, d, Y_WALK + 0.15 + HH, yt, (186, 184, 178), 'concreto', solid=False)
    for (jj, L) in faces(j, 0, w, 0.0, d):
        for f in range(nf - 1):
            y = Y_WALK + 0.15 + HH + f * FH
            ribbon(jj, L, y + 1.1, 1.3, DARK_GLASS, 1.2, (60, 62, 66), 0.6)
        q = 0.0
        while q <= L + 0.01:                                            # aletas verticais profundas de concreto
            jj.bx(q - 0.18, q + 0.18, -1.0, 0.0, Y_WALK + 0.15 + HH, yt + 0.6, C, 'concreto'); q += 2.4
        jj.bx(-0.2, L + 0.2, -1.05, 0.0, yt, yt + 0.6, (168, 166, 160), 'concreto')
        jj.bx(-0.2, L + 0.2, -1.05, 0.0, Y_WALK + 0.15 + HH - 0.6, Y_WALK + 0.15 + HH, (168, 166, 160), 'concreto')
        jj.bx(-0.2, L + 0.2, -1.1, -1.05, Y_WALK + 0.15 + HH - 0.35, Y_WALK + 0.15 + HH - 0.2, (40, 90, 220), 'liso')       # faixa azul
    # pilares-parede sob o balanco
    for k in range(int(w / 12) + 1):
        u = 0.6 + k * (w - 1.2) / max(1, int(w / 12)); j.bx(u - 0.4, u + 0.4, 0.4, 4.0, Y_WALK, Y_WALK + 0.15 + HH, C, 'concreto'); j.solid(u - 0.4, u + 0.4, 0.4, 4.0)
    roof(j, 0, w, 0.0, d, yt + 0.6, C, 0.0, equip=3)
    # torre de comunicacao com antenas
    tu, tv = w * 0.8, d * 0.5
    j.bx(tu - 2.0, tu + 2.0, tv - 2.0, tv + 2.0, yt + 0.6, yt + 4.0, C, 'concreto')
    for (a, b) in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)): j.cyl(tu + a, tv + b, 0.05, yt + 4.0, yt + 16.0, (200, 60, 50), 'metal', 6)
    for k in range(10): j.bx(tu - 0.55, tu + 0.55, tv - 0.55, tv + 0.55, yt + 4.0 + k * 1.2, yt + 4.08 + k * 1.2, (220, 220, 220), 'metal')
    for k in range(3): j.cyl(tu + 0.6, tv, 0.45, yt + 8 + k * 2.5, yt + 8.2 + k * 2.5, (240, 240, 240), 'metal', 10)
    j.ball(tu, tv, yt + 16.2, 0.18, (255, 40, 40), 'liso')
    # entrada: rasgo no balanco com letreiro e brasao
    door_u = w / 2
    letters(j, 'POLICIA CIVIL', door_u, -1.06, Y_WALK + 0.15 + HH + 0.4, 0.9, (240, 240, 244), min(w - 6, 14.0))
    G = J(j.L, j.sub(door_u, -1.1, 0))
    G.cyl(0, -0.05, 0.9, yt - 2.2, yt - 2.0, GOLD, 'metal', 6)
    G.bx(-0.9, 0.9, -0.15, 0.0, yt - 2.9, yt - 1.2, (30, 60, 140), 'liso'); G.bx(-0.5, 0.5, -0.2, -0.15, yt - 2.6, yt - 1.5, GOLD, 'metal')
    glass_door(j, door_u, 4.0, 3.0, 2.8)
    for s in (-1, 1): j.bx(door_u + s * 2.4 - 0.15, door_u + s * 2.4 + 0.15, 3.7, 3.95, Y_WALK + 2.4, Y_WALK + 3.0, (40, 90, 220), 'liso')
    for k, c in enumerate(((0, 150, 70), (30, 60, 140), (240, 240, 240))): flag(j, 3.0 + k * 2.2, -3.0, 10.0, c)
    bollards(j, door_u - 8, door_u + 8, -3.4)
    return door_u, 4.0


# ======================================================================== 4. quartel de bombeiros historico
def bombeiro(j, w, d, nf, spec):
    BR = (168, 72, 52); ST = (226, 216, 196); nf = 3; yt = Y_WALK + 0.15 + HH + 0.8 + (nf - 1) * FH
    hu0 = w - 9.0                                                  # torre de mangueiras no lado direito
    mass(j, 0, hu0, 0.0, d, Y_WALK, yt, BR, 'tijolo')
    jf = faces(j, 0, hu0, 0.0, d)
    # portoes em arco (apparatus bays) na frente
    nb = max(3, min(6, int((hu0 - 4) / 7.0))); bw = (hu0 - 4) / nb; yg = Y_WALK + 0.15
    for k in range(nb):
        uc = 2.0 + (k + 0.5) * bw; r = min(2.3, bw / 2 - 0.7)
        j.bx(uc - r, uc + r, -0.06, -0.02, Y_WALK, yg + 3.0, (180, 30, 30), 'liso')                     # portao vermelho
        for yy in (yg + 1.0, yg + 2.0): j.bx(uc - r, uc + r, -0.09, -0.06, yy - 0.04, yy + 0.04, (240, 240, 236), 'liso')
        for q in range(4): j.bx(uc - r + 0.3 + q * (2 * r - 0.6) / 4, uc - r + 0.3 + (q + 0.8) * (2 * r - 0.6) / 4, -0.08, -0.06, yg + 2.2, yg + 2.85, GLASS, 'vidro')
        arch(jf[0][0], uc, yg + 3.0, r, 0.45, 0.25, ST, 'reboco', (140, 180, 200), key=(236, 226, 206))
        for s in (-1, 1): j.bx(uc + s * (r + 0.22) - 0.25, uc + s * (r + 0.22) + 0.25, -0.3, 0.0, Y_WALK, yg + 3.0, ST, 'reboco')
        for q in range(int((r * 2) / 0.6)): j.bx(uc - r + q * 0.6, uc - r + q * 0.6 + 0.3, -3.0, -0.3, Y_WALK + 0.003, Y_WALK + 0.012, (240, 200, 40), 'liso')
    # andares: janelas em arco duplas, cornija com misulas
    for f in range(nf - 1):
        y = Y_WALK + 0.15 + HH + 0.8 + f * FH
        for (jj, L) in jf:
            n = max(1, int(L / 3.2))
            for k in range(n):
                uc = (k + 0.5) * L / n
                punched(jj, uc, y + 0.6, 1.2, 1.7, ST, 0.22, (120, 150, 170), ST, True)
                arch(jj, uc, y + 2.3, 0.6, 0.18, 0.22, ST, 'reboco', (120, 150, 170), n=6)
            jj.bx(-0.1, L + 0.1, -0.2, 0.0, y - 0.25, y, ST, 'reboco')
    for (jj, L) in jf:
        jj.bx(-0.3, L + 0.3, -0.5, 0.0, yt - 0.5, yt, ST, 'reboco')
        q = 0.4
        while q < L - 0.2: jj.bx(q, q + 0.25, -0.45, 0.0, yt - 0.9, yt - 0.5, ST, 'reboco'); q += 1.2
        jj.bx(-0.2, L + 0.2, -0.25, 0.0, Y_WALK + 0.15 + HH + 0.1, Y_WALK + 0.15 + HH + 0.7, ST, 'reboco')
    letters(j, 'CORPO DE BOMBEIROS', hu0 / 2, -0.25, Y_WALK + 0.15 + HH + 0.18, 0.44, (160, 20, 20), hu0 - 4)
    roof(j, 0, hu0, 0.0, d, yt, BR, 1.0, equip=2, cap=ST)
    # torre de mangueiras (campanile): fuste de tijolo, mirante em arcos, telhado piramidal, sino
    ty = yt + 12.0
    mass(j, hu0, w, 0.0, 9.0, Y_WALK, ty, BR, 'tijolo')
    for (jj, L) in faces(j, hu0, w, 0.0, 9.0):
        for k in range(4):
            y = Y_WALK + 3.0 + k * 4.6
            if y < ty - 5: punched(jj, L / 2, y, 0.9, 2.0, ST, 0.2, (100, 120, 140), ST, False); arch(jj, L / 2, y + 2.0, 0.45, 0.14, 0.2, ST, 'reboco', (100, 120, 140), n=6)
        for s in (0.25, L - 0.25): jj.bx(s - 0.25, s + 0.25, -0.12, 0.0, Y_WALK, ty, ST, 'reboco')       # cunhais
        # mirante: dois arcos abertos por face
        for uc in (L * 0.3, L * 0.7):
            jj.bx(uc - 1.0, uc + 1.0, -0.02, 0.0, ty - 4.2, ty - 1.6, (40, 26, 22), 'liso')
            arch(jj, uc, ty - 1.6, 1.0, 0.3, 0.2, ST, 'reboco', (40, 26, 22), 'liso', n=8)
        jj.bx(-0.4, L + 0.4, -0.6, 0.0, ty - 0.4, ty, ST, 'reboco')
    M = j.M; F = j.F; M.m('telha'); cu, cv = (hu0 + w) / 2, 4.5; tp = ty + 5.5
    for (a, b) in (((hu0 - 0.4, -0.4), (w + 0.4, -0.4)), ((w + 0.4, -0.4), (w + 0.4, 9.4)), ((w + 0.4, 9.4), (hu0 - 0.4, 9.4)), ((hu0 - 0.4, 9.4), (hu0 - 0.4, -0.4))):
        M.tri(F.p(a[0], a[1], ty), F.p(b[0], b[1], ty), F.p(cu, cv, tp), (110, 60, 50))
    j.cyl(cu, cv, 0.05, tp, tp + 1.6, GOLD, 'metal', 6)
    j.ball(cu, cv, ty - 2.8, 0.55, GOLD, 'metal')                                                    # sino
    G = J(j.L, j.sub(cu, -0.6, 0)); G.cyl(0, -0.05, 1.1, ty - 0.2, ty - 0.2, WHITE, 'liso', 3)
    G.bx(-1.1, 1.1, -0.12, 0.0, yt + 3.4, yt + 5.6, (250, 248, 240), 'liso'); G.bx(-0.04, 0.04, -0.16, -0.12, yt + 4.5, yt + 5.3, DARK); G.bx(0.0, 0.6, -0.16, -0.12, yt + 4.46, yt + 4.54, DARK)
    letters(j, '193', cu, -0.62, yt - 1.6, 1.4, (255, 220, 60))
    door_u = hu0 + 4.5
    glass_door(j, door_u, 0.0, 1.8, 2.6, (120, 30, 24), (3.2, 1.4))
    j.cyl(1.0, -1.0, 0.25, Y_WALK, Y_WALK + 0.8, (220, 30, 30), 'metal', 10); j.ball(1.0, -1.0, Y_WALK + 0.85, 0.24, (220, 30, 30), 'metal')   # hidrante
    return door_u, 0.0


# ======================================================================== 5. escola FDE
def professor(j, w, d, nf, spec):
    acc = spec[7]; nf = 3; yp = Y_WALK + 3.6; yt = yp + nf * FH; C = (196, 194, 188)
    cols = ((230, 70, 60), (60, 140, 220), (240, 190, 40), (70, 170, 90), (150, 90, 200))
    # pilotis: pilares redondos coloridos, terreo livre (com nucleo fechado de servicos)
    nu_ = max(3, int(w / 7.2)); nv_ = 3
    for a in range(nu_ + 1):
        for b in range(nv_):
            u = 1.0 + a * (w - 2) / nu_; v = 2.0 + b * (d - 4) / (nv_ - 1)
            j.cyl(u, v, 0.32, Y_WALK, yp, cols[a % len(cols)], 'liso', 12); j.solid(u - 0.32, u + 0.32, v - 0.32, v + 0.32)
    cu0, cu1 = w * 0.62, w * 0.62 + min(16.0, w * 0.2)
    mass(j, cu0, cu1, 6.0, d - 2.0, Y_WALK, yp, (238, 232, 220), 'reboco')
    for (jj, L) in faces(j, cu0, cu1, 6.0, d - 2.0): ribbon(jj, L, Y_WALK + 1.2, 1.6, GLASS, 1.6, (240, 240, 240), 1.0)
    # bloco das salas sobre os pilotis
    j.bx(0, w, 0.0, d, yp - 0.6, yp, C, 'concreto')
    mass(j, 0, w, 0.0, d, yp, yt, (244, 238, 226), 'reboco', solid=False)
    jf = faces(j, 0, w, 0.0, d)
    for f in range(nf):
        y = yp + f * FH
        # frente: circulacao com cobogo (grelha de blocos vazados)
        jj, L = jf[0]
        nb = max(3, int(L / 7.2)); bw = L / nb
        for b in range(nb):
            a0, a1 = b * bw + 0.3, (b + 1) * bw - 0.3
            if b % 3 != 1:                                               # cobogo branco sobre fundo sombreado
                jj.bx(a0, a1, -0.02, 0.0, y + 0.1, y + FH - 0.3, (96, 92, 88), 'liso')
                g = a0
                while g <= a1 + 0.01: jj.bx(g - 0.07, g + 0.07, -0.32, -0.02, y + 0.1, y + FH - 0.3, (246, 244, 238), 'reboco'); g += (a1 - a0) / max(1, round((a1 - a0) / 0.42))
                for k in range(8): yy = y + 0.1 + k * (FH - 0.4) / 7; jj.bx(a0, a1, -0.32, -0.02, yy - 0.06, yy + 0.06, (246, 244, 238), 'reboco')
            else:                                                       # sala com janela e brises verticais coloridos
                jj.bx(a0, a1, -0.03, 0.0, y + 0.9, y + 2.7, GLASS, 'vidro')
                q = a0 + 0.3; k = 0
                while q < a1: jj.bx(q - 0.07, q + 0.07, -0.9, -0.03, y + 0.2, y + FH - 0.3, cols[(k + b + f) % len(cols)], 'liso'); q += 0.8; k += 1
            jj.bx(b * bw - 0.3, b * bw + 0.3, -0.4, 0.0, y, y + FH, C, 'concreto')
        jj.bx(-0.1, L + 0.1, -0.4, 0.0, y + FH - 0.3, y + FH, C, 'concreto')
        # fundos e laterais: salas com fita de janelas e brises verticais coloridos
        for (jj, L) in jf[1:]:
            ribbon(jj, L, y + 0.9, 1.8, GLASS, 1.8, (240, 240, 240), 0.6)
            q = 0.9
            k = 0
            while q < L - 0.6: jj.bx(q - 0.06, q + 0.06, -0.8, -0.05, y + 0.2, y + FH - 0.2, cols[(k + f) % len(cols)], 'liso'); q += 1.2; k += 1
            jj.bx(-0.1, L + 0.1, -0.85, 0.0, y + FH - 0.25, y + FH, C, 'concreto')
    # cobertura metalica em asa de borboleta sobre o bloco
    M = j.M; F = j.F; M.m('metal')
    for (va, vb, ya, yb) in ((-1.2, d / 2, yt + 2.0, yt + 0.8), (d / 2, d + 1.2, yt + 0.8, yt + 2.0)):
        M.quad(F.p(-1.0, va, ya), F.p(w + 1.0, va, ya), F.p(w + 1.0, vb, yb), F.p(-1.0, vb, yb), (200, 204, 210), (0, 1, 0))
        M.quad(F.p(-1.0, va, ya - 0.02), F.p(w + 1.0, va, ya - 0.02), F.p(w + 1.0, vb, yb - 0.02), F.p(-1.0, vb, yb - 0.02), (160, 164, 170), (0, -1, 0))
    for k in range(int(w / 6) + 1):
        u = k * w / max(1, int(w / 6))
        for v in (0.3, d - 0.3): j.cyl(u, v, 0.08, yt, yt + 2.0 if v < 1 else yt + 2.0, (120, 124, 130), 'metal', 6)
    j.bx(0, w, 0, d, yt, yt + 0.2, C, 'concreto')
    # mural colorido e letreiro na empena lateral
    jl, L = jf[3]
    for k in range(5): jl.bx(1.0 + k * (L - 2) / 5, 1.0 + (k + 1) * (L - 2) / 5, -0.95, -0.85, yp + 0.4, yt - 0.4, cols[k], 'liso')
    door_u = w * 0.3
    letters(j, spec[0], w * 0.3, -0.36, yp - 0.55, 0.45, (255, 255, 255), w * 0.5, shade(acc, -20), 0.25)
    G = J(j.L, j.sub(w * 0.78, -0.36, 0))
    G.cyl(0, -0.05, 1.0, yt - 1.6, yt - 1.6, WHITE, 'liso', 3)
    G.bx(-1.0, 1.0, -0.14, 0.0, yt - 2.6, yt - 0.6, (250, 248, 240), 'liso'); G.bx(-0.04, 0.04, -0.18, -0.14, yt - 1.6, yt - 0.9, DARK); G.bx(0.0, 0.6, -0.18, -0.14, yt - 1.64, yt - 1.56, DARK)
    # portao da escola (grade colorida) e bicicletario
    glass_door(j, door_u, 6.0, 3.0, 2.6)
    for k in range(8): j.bx(door_u + 4 + k * 0.8 - 0.03, door_u + 4 + k * 0.8 + 0.03, 0.5, 1.5, Y_WALK, Y_WALK + 0.8, cols[k % 5], 'metal')
    return door_u, 6.0


# ======================================================================== 6. forum neoclassico
def juiz(j, w, d, nf, spec):
    ST = (232, 224, 206); ST2 = (214, 204, 184); nf = 3; yb = Y_WALK + 1.6; yt = yb + 4.6 + (nf - 1) * 4.0
    pw = min(w * 0.42, 34.0); pu0 = (w - pw) / 2; pu1 = pu0 + pw; door_u = w / 2; pv = 7.0
    # corpo: embasamento rusticado alto + andares com janelas com frontoes
    mass(j, 0, w, pv, d, Y_WALK, yt, ST, 'reboco')
    for (jj, L) in faces(j, 0, w, pv, d):
        for k in range(int((yb - Y_WALK + 4.6) / 0.6)): jj.bx(-0.05, L + 0.05, -0.08, 0.0, Y_WALK + k * 0.6, Y_WALK + k * 0.6 + 0.5, ST2, 'reboco')
        n = max(1, int(L / 3.6))
        for k in range(n):
            uc = (k + 0.5) * L / n
            if jj is faces(j, 0, w, pv, d)[0][0] and pu0 - 1 < uc < pu1 + 1: continue
            punched(jj, uc, yb + 1.0, 1.3, 2.6, (246, 240, 228), 0.25, (110, 130, 150), ST)
            for f in range(nf - 1):
                y = yb + 4.6 + f * 4.0
                punched(jj, uc, y + 0.8, 1.3, 2.4, (246, 240, 228), 0.25, (110, 130, 150), ST)
                if f == 0:                                              # frontao triangular sobre a janela nobre
                    jj.M.m('reboco'); G = jj.F
                    jj.M.quad(G.p(uc - 1.0, -0.3, y + 3.35), G.p(uc + 1.0, -0.3, y + 3.35), G.p(uc + 1.0, -0.3, y + 3.5), G.p(uc - 1.0, -0.3, y + 3.5), ST, G.nv(-1))
                    jj.M.tri(G.p(uc - 1.0, -0.3, y + 3.5), G.p(uc + 1.0, -0.3, y + 3.5), G.p(uc, -0.3, y + 4.0), ST, G.nv(-1))
                    jj.bx(uc - 1.0, uc + 1.0, -0.3, 0.0, y + 3.3, y + 3.36, ST2, 'reboco')
        jj.bx(-0.3, L + 0.3, -0.5, 0.0, yb + 4.4, yb + 4.6, ST2, 'reboco')
        jj.bx(-0.4, L + 0.4, -0.7, 0.0, yt - 0.7, yt, ST, 'reboco')
        q = 0.3
        while q < L: jj.bx(q, q + 0.18, -0.55, 0.0, yt - 0.95, yt - 0.7, ST2, 'reboco'); q += 0.5
        jj.bx(-0.1, L + 0.1, -0.2, 0.0, yt, yt + 1.0, ST, 'reboco')                                        # balaustrada (plinto)
        q = 0.4
        while q < L - 0.2: jj.cyl(q, -0.12, 0.09, yt + 0.0, yt + 0.9, ST, 'reboco', 6); q += 0.45
    roof(j, 0, w, pv, d, yt + 0.9, ST, 0.0, equip=0)
    # escadaria monumental ate o portico
    for k in range(8):
        v0 = -1.0 + k * 0.5; j.bx(pu0 - 1.5 + k * 0.1, pu1 + 1.5 - k * 0.1, v0, pv, Y_WALK, Y_WALK + (k + 1) * 0.2, ST2 if k % 2 else ST, 'reboco')
    j.solid(pu0 - 1.5, pu1 + 1.5, 2.5, pv)
    for s in (-1, 1):                                                   # pedestais com leoes/urnas
        u = door_u + s * (pw / 2 + 1.0); j.bx(u - 0.8, u + 0.8, -1.0, 2.0, Y_WALK, Y_WALK + 1.8, ST2, 'reboco'); j.solid(u - 0.8, u + 0.8, -1.0, 2.0)
        j.cyl(u, 0.5, 0.45, Y_WALK + 1.8, Y_WALK + 2.6, (190, 184, 170), 'reboco', 10, True, 0.6); j.ball(u, 0.5, Y_WALK + 2.9, 0.4, (190, 184, 170), 'reboco')
    # portico: colunas com base e capitel, entablamento e frontao
    nc = 8; ych = yt - 1.4
    for k in range(nc):
        cu = pu0 + 0.7 + k * (pw - 1.4) / (nc - 1)
        j.bx(cu - 0.65, cu + 0.65, 3.4, 4.7, yb, yb + 0.35, ST2, 'reboco')
        j.cyl(cu, 4.05, 0.52, yb + 0.35, yb + 0.6, ST, 'reboco', 16)
        j.cyl(cu, 4.05, 0.46, yb + 0.6, ych - 0.5, (240, 234, 220), 'reboco', 16, False, 0.4)
        for q in range(12):
            a_ = 2 * PI * q / 12; j.bx(cu + math.cos(a_) * 0.44 - 0.02, cu + math.cos(a_) * 0.44 + 0.02, 4.05 + math.sin(a_) * 0.44 - 0.02, 4.05 + math.sin(a_) * 0.44 + 0.02, yb + 0.7, ych - 0.7, (222, 214, 198), 'reboco')   # caneluras
        j.cyl(cu, 4.05, 0.44, ych - 0.5, ych - 0.25, ST, 'reboco', 16, True, 0.62)
        j.bx(cu - 0.7, cu + 0.7, 3.35, 4.75, ych - 0.25, ych, ST, 'reboco'); j.solid(cu - 0.5, cu + 0.5, 3.55, 4.55)
    j.bx(pu0 - 0.2, pu1 + 0.2, 3.2, pv, ych, ych + 1.6, ST, 'reboco')
    j.bx(pu0 - 0.3, pu1 + 0.3, 3.1, pv, ych + 1.6, ych + 1.85, ST2, 'reboco')
    letters(j, 'FORUM DA COMARCA', door_u, 3.2, ych + 0.4, 0.75, (150, 120, 70), pw - 3)
    M = j.M; F = j.F; ph = 4.2; yf = ych + 1.85
    M.m('reboco'); M.tri(F.p(pu0 - 0.3, 3.1, yf), F.p(pu1 + 0.3, 3.1, yf), F.p(door_u, 3.1, yf + ph), ST, F.nv(-1))
    M.tri(F.p(pu0 + 1.2, 3.0, yf + 0.35), F.p(pu1 - 1.2, 3.0, yf + 0.35), F.p(door_u, 3.0, yf + ph - 0.6), ST2, F.nv(-1))      # timpano
    M.m('telha')
    M.quad(F.p(pu0 - 0.6, 2.9, yf), F.p(door_u, 2.9, yf + ph + 0.2), F.p(door_u, pv + 1.0, yf + ph + 0.2), F.p(pu0 - 0.6, pv + 1.0, yf), (150, 140, 128), (-F.ux, 2.0, -F.uz))
    M.quad(F.p(door_u, 2.9, yf + ph + 0.2), F.p(pu1 + 0.6, 2.9, yf), F.p(pu1 + 0.6, pv + 1.0, yf), F.p(door_u, pv + 1.0, yf + ph + 0.2), (150, 140, 128), (F.ux, 2.0, F.uz))
    j.ball(door_u, 2.95, yf + ph * 0.45, 0.8, GOLD, 'metal')                                          # brasao no timpano
    # portas de bronze altas
    for k in (-1, 0, 1):
        u = door_u + k * 5.0
        j.bx(u - 1.2, u + 1.2, pv - 0.12, pv - 0.02, yb, yb + 4.2, (120, 90, 50), 'metal')
        arch(J(j.L, j.sub(0, pv - 0.02, 0)), u, yb + 4.2, 1.2, 0.3, 0.2, ST2, 'reboco', (110, 130, 150), n=8)
    # cupula sobre tambor com colunas e lanterna
    cv = pv + (d - pv) / 2; R = min(7.5, (d - pv) / 2 - 1.0)
    j.cyl(door_u, cv, R + 0.6, yt + 0.9, yt + 1.6, ST2, 'reboco', 24)
    j.cyl(door_u, cv, R, yt + 1.6, yt + 5.6, ST, 'reboco', 24)
    for q in range(16):
        a_ = 2 * PI * q / 16; j.cyl(door_u + math.cos(a_) * (R + 0.35), cv + math.sin(a_) * (R + 0.35), 0.22, yt + 1.6, yt + 5.4, (240, 234, 220), 'reboco', 8)
        if q % 2 == 0: G = J(j.L, j.sub(door_u + math.cos(a_ + PI / 16) * R, cv + math.sin(a_ + PI / 16) * R, 0))
    j.cyl(door_u, cv, R + 0.5, yt + 5.4, yt + 6.0, ST2, 'reboco', 24)
    M.m('metal')
    for i in range(6):
        a0 = PI / 2 * i / 6; a1 = PI / 2 * (i + 1) / 6
        j.cyl(door_u, cv, R * math.cos(a0) + 0.01, yt + 6.0 + R * 0.9 * math.sin(a0), yt + 6.0 + R * 0.9 * math.sin(a1), (110, 150, 140), 'metal', 24, i == 5, R * math.cos(a1) + 0.01)
    yl = yt + 6.0 + R * 0.9
    j.cyl(door_u, cv, 1.0, yl - 0.2, yl + 1.8, ST, 'reboco', 12)
    for q in range(8): a_ = 2 * PI * q / 8; j.cyl(door_u + math.cos(a_) * 1.05, cv + math.sin(a_) * 1.05, 0.08, yl, yl + 1.6, ST2, 'reboco', 6)
    j.cyl(door_u, cv, 1.2, yl + 1.8, yl + 2.6, (110, 150, 140), 'metal', 12, True, 0.05)
    j.ball(door_u, cv, yl + 2.7, 0.2, GOLD, 'metal')
    for q in range(4): a_ = 2 * PI * q / 4; j.ball(door_u + math.cos(a_) * 0.9, cv + math.sin(a_) * 0.9, yl + 0.6, 0.12, GLOW, 'liso')
    # estatua da Justica na praca
    su = 4.0
    if su < pu0 - 4:
        j.bx(su - 1.0, su + 1.0, -2.0, 0.0, Y_WALK, Y_WALK + 2.4, ST2, 'reboco'); j.solid(su - 1.0, su + 1.0, -2.0, 0.0)
        j.cyl(su, -1.0, 0.35, Y_WALK + 2.4, Y_WALK + 4.0, (200, 196, 186), 'reboco', 10, True, 0.25); j.ball(su, -1.0, Y_WALK + 4.25, 0.25, (200, 196, 186), 'reboco')
        j.bx(su - 0.04, su + 0.04, -1.0, -0.9, Y_WALK + 3.6, Y_WALK + 5.0, (200, 196, 186), 'reboco'); j.bx(su - 0.7, su + 0.7, -1.0, -0.94, Y_WALK + 4.94, Y_WALK + 5.0, GOLD, 'metal')
        for s in (-1, 1): j.cyl(su + s * 0.65, -0.97, 0.2, Y_WALK + 4.3, Y_WALK + 4.36, GOLD, 'metal', 8)
    for s in (-1, 1): flag(j, door_u + s * (pw / 2 + 3.5), -2.0, 11.0, (0, 150, 70) if s < 0 else (30, 60, 140))
    return door_u, pv - 0.02


# ======================================================================== 7. art deco
def advogado(j, w, d, nf, spec):
    ST = (232, 222, 204); PIER = (242, 234, 218); SP = (64, 58, 54)
    tiers = [(0.0, w, 0.0, d, 4), (w * 0.2, w * 0.8, 2.5, d - 2.5, 7), (w * 0.3, w * 0.7, 4.0, d - 4.0, 6), (w * 0.38, w * 0.62, 5.5, d - 5.5, 5)]
    y0 = Y_WALK; ytops = []
    for ti, (u0, u1, v0, v1, fl) in enumerate(tiers):
        yb = Y_WALK if ti == 0 else ytops[-1]
        yt = Y_WALK + 0.15 + HH + (fl - 1) * FH if ti == 0 else yb + fl * FH
        mass(j, u0, u1, v0, v1, yb, yt, ST, 'reboco', solid=ti == 0)
        for (jj, L) in faces(j, u0, u1, v0, v1):
            n = max(2, int(L / 2.4)); bw = L / n
            ys = yb + (HH + 0.15 if ti == 0 else 0.0)
            jj.bx(0.3, L - 0.3, -0.02, 0.0, ys + 0.2, yt - 0.8, SP, 'liso')                              # fundo escuro dos vaos
            for k in range(n):
                uc = (k + 0.5) * bw; ff = int((yt - 0.8 - ys) / FH)
                for f in range(ff): jj.bx(uc - bw * 0.3, uc + bw * 0.3, -0.04, -0.02, ys + f * FH + 0.8, ys + f * FH + 2.6, (150, 170, 180), 'vidro')
            for k in range(n + 1):                                                                      # pilares continuos
                jj.bx(k * bw - 0.22, k * bw + 0.22, -0.3, 0.0, ys, yt + (1.2 if k % 2 == 0 else 0.6), PIER, 'reboco')
            for f in range(int((yt - 0.8 - ys) / FH)):
                jj.bx(0.3, L - 0.3, -0.08, 0.0, ys + f * FH + 0.15, ys + f * FH + 0.75, (120, 96, 70), 'metal')   # spandrel de bronze
            jj.bx(-0.2, L + 0.2, -0.35, 0.0, yt - 0.8, yt, ST, 'reboco')
            # friso dourado em zigue-zague no coroamento de cada escalonamento
            q = 0.0
            while q < L - 0.6: jj.bx(q + 0.1, q + 0.5, -0.4, -0.35, yt - 0.6, yt - 0.2, GOLD, 'metal'); q += 0.8
        roof(j, u0, u1, v0, v1, yt, ST, 0.3)
        ytops.append(yt)
    # coroa: aletas escalonadas douradas e agulha
    u0, u1, v0, v1, _ = tiers[-1]; yt = ytops[-1]; cu = (u0 + u1) / 2; cv = (v0 + v1) / 2
    for k in range(4):
        s = 1.0 - k * 0.22
        j.bx(cu - (u1 - u0) / 2 * s, cu + (u1 - u0) / 2 * s, cv - (v1 - v0) / 2 * s, cv + (v1 - v0) / 2 * s, yt + k * 1.6, yt + (k + 1) * 1.6, ST if k % 2 == 0 else GOLD, 'reboco' if k % 2 == 0 else 'metal')
        G = J(j.L, j.sub(cu, cv - (v1 - v0) / 2 * s, 0))
        for q in range(5): G.bx(-((u1 - u0) / 2 * s) + 0.5 + q * ((u1 - u0) * s - 1.0) / 4 - 0.1, -((u1 - u0) / 2 * s) + 0.5 + q * ((u1 - u0) * s - 1.0) / 4 + 0.1, -0.06, 0.0, yt + k * 1.6 + 0.2, yt + (k + 1) * 1.6 - 0.2, GLOW, 'liso')
    j.cyl(cu, cv, 0.35, yt + 6.4, yt + 14.0, GOLD, 'metal', 8, True, 0.04)
    # portal: arco alto de bronze com letreiro
    door_u = w / 2
    G = J(j.L, j.sub(0, -0.3, 0))
    G.bx(door_u - 3.4, door_u + 3.4, -0.4, 0.0, Y_WALK, Y_WALK + 7.0, PIER, 'reboco')
    G.bx(door_u - 2.4, door_u + 2.4, -0.42, -0.4, Y_WALK + 0.15, Y_WALK + 5.0, (90, 70, 50), 'metal')
    arch(G, door_u, Y_WALK + 5.0, 2.4, 0.4, 0.42, GOLD, 'metal', (120, 140, 150), n=10)
    for q in range(5): G.bx(door_u - 2.0 + q * 1.0 - 0.04, door_u - 2.0 + q * 1.0 + 0.04, -0.46, -0.42, Y_WALK + 3.0, Y_WALK + 5.0, GOLD, 'metal')
    letters(j, spec[0], door_u, -0.72, Y_WALK + 7.2, 0.6, GOLD, 12.0)
    glass_door(j, door_u, -0.72, 2.2, 2.8, GOLD)
    for s in (-1, 1): j.cyl(door_u + s * 4.2, -1.2, 0.08, Y_WALK, Y_WALK + 3.0, DARK, 'metal', 6); j.ball(door_u + s * 4.2, -1.2, Y_WALK + 3.1, 0.25, GLOW, 'liso')
    return door_u, -0.72


# ======================================================================== 8. modernismo internacional
def secretario(j, w, d, nf, spec):
    GG = (110, 168, 156); MUL = (60, 70, 70); ST = (220, 222, 224)
    yp = Y_WALK + 0.15 + HH + FH                                     # embasamento de 2 andares
    # embasamento horizontal sobre pilotis com patio de esculturas
    for k in range(int(w / 6) + 1):
        u = 1.0 + k * (w - 2) / max(1, int(w / 6))
        for v in (1.0, d - 1.0): j.bx(u - 0.25, u + 0.25, v - 0.25, v + 0.25, Y_WALK, Y_WALK + 4.2, (230, 232, 234), 'metal'); j.solid(u - 0.25, u + 0.25, v - 0.25, v + 0.25)
    lb0, lb1 = w * 0.35, w * 0.65
    mass(j, lb0, lb1, 3.0, d - 3.0, Y_WALK, Y_WALK + 4.2, (160, 200, 200), 'vidro')
    j.bx(0, w, 0, d, Y_WALK + 4.2, yp + 0.4, GG, 'vidro')
    for (jj, L) in faces(j, 0, w, 0, d):
        q = 0.0
        while q <= L: jj.bx(q - 0.05, q + 0.05, -0.12, 0.0, Y_WALK + 4.2, yp + 0.4, MUL, 'metal'); q += 1.5
        for yy in (Y_WALK + 4.2, Y_WALK + 4.2 + FH * 0.5, Y_WALK + 4.2 + FH, yp + 0.4): jj.bx(0, L, -0.14, 0.0, yy - 0.3, yy, (200, 204, 206), 'metal')
    roof(j, 0, w, 0, d, yp + 0.4, (200, 204, 206), 1.1, (120, 150, 90), 0)
    for k in range(int(w / 6)):                                      # jardim na cobertura do embasamento
        x, z = j.F.xz(3 + k * 6, d * 0.3); j.L.trees.append((x, z, 'arbusto', 1.0, yp + 0.44))
    # lamina vertical de vidro verde com spandrels e montantes em I
    tu0, tu1 = w * 0.6, min(w - 2.0, w * 0.6 + 26.0); tv0, tv1 = 4.0, min(d - 4.0, 18.0)
    yt = yp + 0.4 + (nf - 2) * FH
    mass(j, tu0, tu1, tv0, tv1, yp + 0.4, yt, GG, 'escritorio', solid=False, uvf=(1.5, FH, yt))
    for (jj, L) in faces(j, tu0, tu1, tv0, tv1):
        q = 0.0
        while q <= L + 0.01: jj.bx(q - 0.05, q + 0.05, -0.25, 0.0, yp + 0.4, yt, (90, 80, 60), 'metal'); q += 1.5   # perfis I de bronze
        for f in range(int((yt - yp - 0.4) / FH)):
            y = yp + 0.4 + f * FH; jj.bx(0, L, -0.06, 0.0, y, y + 0.8, (70, 96, 90), 'liso')
    j.bx(tu0 - 0.2, tu1 + 0.2, tv0 - 0.2, tv1 + 0.2, yt, yt + 3.0, (90, 100, 100), 'metal')               # coroamento cego (maquinas)
    j.bx(tu0, tu1, tv0, tv1, yt + 3.0, yt + 3.1, (160, 160, 160), 'concreto')
    letters(j, spec[0], (lb0 + lb1) / 2, -0.15, Y_WALK + 4.2 + FH * 0.5 + 0.2, 0.7, (255, 255, 255), (lb1 - lb0) - 1)
    # espelhos d'agua com esculturas na praca sob o embasamento
    for (a, b) in ((2.0, lb0 - 2.0), (lb1 + 2.0, w - 2.0)):
        if b - a > 6:
            j.bx(a, b, -3.5, -0.5, Y_WALK, Y_WALK + 0.4, (210, 206, 198), 'reboco'); j.bx(a + 0.25, b - 0.25, -3.25, -0.75, Y_WALK + 0.4, Y_WALK + 0.42, (70, 130, 160), 'agua'); j.solid(a, b, -3.5, -0.5)
            j.cyl((a + b) / 2, -2.0, 0.35, Y_WALK + 0.42, Y_WALK + 2.4, (60, 62, 66), 'metal', 8, True, 0.1); j.ball((a + b) / 2, -2.0, Y_WALK + 2.7, 0.55, (200, 120, 60), 'metal')
    door_u = (lb0 + lb1) / 2
    glass_door(j, door_u, 3.0, 3.0, 2.8)
    return door_u, 3.0


# ======================================================================== 9. torre corporativa
def empresario(j, w, d, nf, spec):
    DG = (60, 72, 88); FR = (40, 44, 50); acc = spec[7]
    # embasamento de granito com atrio de 3 andares
    yp = Y_WALK + 0.15 + HH + 2 * FH
    mass(j, 0, w, 6.0, d, Y_WALK, yp, (54, 56, 60), 'reboco')
    for (jj, L) in faces(j, 0, w, 6.0, d):
        for f in range(3): ribbon(jj, L, Y_WALK + 0.6 + f * (HH if f == 0 else FH) + (0 if f < 2 else HH - FH), 2.4, DG, 2.0, (30, 32, 36), 1.0)
        jj.bx(-0.1, L + 0.1, -0.3, 0.0, yp - 0.6, yp, (40, 42, 46), 'reboco')
    roof(j, 0, w, 6.0, d, yp, (54, 56, 60), 0.9, (110, 150, 90))
    # torre: planta quadrada com quinas chanfradas, 3 escalonamentos
    tw = min(30.0, w * 0.4, d - 2.0); cu = w / 2; cv = 6.0 + (d - 6.0) / 2 if d - 6 > tw else d / 2
    ytop = yp
    levels = [(tw, nf * 0.55), (tw * 0.84, nf * 0.3), (tw * 0.66, nf * 0.15)]
    M = j.M; F = j.F
    for li, (s, fl) in enumerate(levels):
        h = max(2, int(fl)) * FH; ch = s * 0.18; hs = s / 2
        pts = [(-hs + ch, -hs), (hs - ch, -hs), (hs, -hs + ch), (hs, hs - ch), (hs - ch, hs), (-hs + ch, hs), (-hs, hs - ch), (-hs, -hs + ch)]
        c8 = [F.xz(cu + a, cv + b) for (a, b) in pts]
        M.m('escritorio'); M.prism(c8, ytop, ytop + h, (150, 170, 190), True, False, (70, 74, 80), None, None, (3.0, FH, ytop + h))
        # aletas verticais de LED nas quinas chanfradas e faixas horizontais por andar
        for k in range(8):
            a = pts[k]; b = pts[(k + 1) % 8]
            if k % 2 == 1:
                for t in (0.25, 0.5, 0.75):
                    x, z = F.xz(cu + a[0] + (b[0] - a[0]) * t, cv + a[1] + (b[1] - a[1]) * t)
                    M.m('liso'); M.box(x - 0.12, x + 0.12, ytop, ytop + h + 2.0, z - 0.12, z + 0.12, GLOW if t == 0.5 else acc)
        for f in range(int(h / FH)):
            y = ytop + f * FH
            M.m('metal'); M.prism([F.xz(cu + p[0] * 1.012, cv + p[1] * 1.012) for p in pts], y - 0.1, y + 0.1, FR, False)
        M.m('metal'); M.prism([F.xz(cu + p[0] * 1.04, cv + p[1] * 1.04) for p in pts], ytop + h, ytop + h + 0.6, (200, 180, 120))
        ytop += h + 0.6
    # coroa: armacao aberta iluminada e mastro
    s = levels[-1][0] * 0.7
    for (a, b) in ((-1, -1), (1, -1), (1, 1), (-1, 1)): j.bx(cu + a * s / 2 - 0.2, cu + a * s / 2 + 0.2, cv + b * s / 2 - 0.2, cv + b * s / 2 + 0.2, ytop, ytop + 8.0, (200, 180, 120), 'metal')
    for k in range(4): j.bx(cu - s / 2, cu + s / 2, cv - s / 2, cv + s / 2, ytop + 2.0 * (k + 1) - 0.08, ytop + 2.0 * (k + 1), GLOW, 'liso', False)
    j.cyl(cu, cv, 0.3, ytop, ytop + 22.0, (220, 220, 224), 'metal', 8, True, 0.05); j.ball(cu, cv, ytop + 22.0, 0.25, (255, 40, 40), 'liso')
    sign_text(j, 'ATLAS', cu, cv - levels[-1][0] / 2 * 1.04 - 0.05, ytop - 3.6, 2.2, GOLD, 0.12, levels[-1][0] * 0.8)
    # entrada: marquise de vidro em balanco com tirantes e letreiro dourado
    door_u = cu
    j.bx(door_u - 8.0, door_u + 8.0, 1.0, 6.0, Y_WALK + 5.6, Y_WALK + 5.8, (170, 200, 214), 'vidro')
    for s_ in (-1, 1): beam(j.M, j.F.p(door_u + s_ * 7.6, 1.2, Y_WALK + 5.8), j.F.p(door_u + s_ * 4.0, 6.0, Y_WALK + 9.5), 0.08, (200, 202, 206))
    mass(j, door_u - 9.0, door_u + 9.0, 4.0, 6.2, Y_WALK, Y_WALK + 9.0, (90, 110, 130), 'vidro')
    letters(j, 'GRUPO ATLAS', door_u, 4.0, Y_WALK + 6.6, 1.1, GOLD, 16.0)
    glass_door(j, door_u, 4.0, 3.6, 3.0, GOLD)
    for s_ in (-1, 1):
        for k in range(3): flag(j, door_u + s_ * (11.0 + k * 2.0), 1.0, 9.0, (30, 40, 60) if k != 1 else acc)
    bollards(j, door_u - 9, door_u + 9, 0.0, 1.5)
    return door_u, 4.0


# ======================================================================== 10. sede de tecnologia
def programador(j, w, d, nf, spec):
    cols = [(120, 70, 210), (60, 190, 160), (240, 160, 40), (230, 80, 120)]
    gl = [(150, 140, 210), (130, 200, 196), (220, 196, 150), (220, 160, 180)]
    boxes = []; yb = Y_WALK; r = j.r
    n = 5; bw = min(w * 0.55, 48.0); bd = min(d - 4.0, 20.0)
    for k in range(n):
        off = (k % 2) * (w - bw - 4.0) * (0.35 + 0.3 * (k % 3) / 2) + 2.0
        dv = 2.0 + (k % 3) * 2.0
        fl = 3 if k < n - 1 else 2
        u0, u1 = off, off + bw - k * 2.0; v0, v1 = dv, dv + bd
        yt = yb + (HH + 0.15 if k == 0 else 0) + fl * FH - (FH if k == 0 else 0)
        mass(j, u0, u1, v0, v1, yb, yt, (250, 250, 252), 'liso', solid=(k == 0))
        for (jj, L) in faces(j, u0, u1, v0, v1):
            jj.bx(0.4, L - 0.4, -0.03, 0.0, yb + 0.4, yt - 0.5, gl[k % 4], 'vidro')
            q = 0.4
            while q <= L - 0.39: jj.bx(q - 0.04, q + 0.04, -0.1, -0.03, yb + 0.4, yt - 0.5, (240, 240, 244), 'metal'); q += 1.6
            for f in range(int((yt - yb) / FH) + 1):
                y = yb + 0.4 + f * FH
                if y < yt - 0.4: jj.bx(0.4, L - 0.4, -0.12, -0.03, y - 0.15, y + 0.1, (250, 250, 252), 'liso')
            jj.bx(-0.05, L + 0.05, -0.05, 0.0, yt - 0.5, yt, cols[k % 4], 'liso')                      # faixa colorida
        # terraco verde em cima com guarda-corpo de vidro, arvores e deque
        j.bx(u0 + 0.3, u1 - 0.3, v0 + 0.3, v1 - 0.3, yt, yt + 0.25, (110, 160, 80), 'grama')
        for (a, b, c, e) in ((u0, u1, v0, v0 + 0.1), (u0, u1, v1 - 0.1, v1), (u0, u0 + 0.1, v0, v1), (u1 - 0.1, u1, v0, v1)): j.bx(a, b, c, e, yt, yt + 1.1, (190, 220, 230), 'vidro')
        j.bx(u0 + 2.0, u0 + 8.0, v0 + 2.0, v0 + 6.0, yt + 0.25, yt + 0.35, WOOD, 'madeira')
        for q in range(int((u1 - u0 - 4) / 5)):
            x, z = j.F.xz(u0 + 3.0 + q * 5.0, v1 - 2.0); j.L.trees.append((x, z, r.choice(('arbusto', 'ornamental', 'folhosa')), 0.8, yt + 0.25))
        boxes.append((u0, u1, v0, v1, yt)); yb = yt + 0.25
    # logo gigante (N em pixels) e letreiro no topo
    u0, u1, v0, v1, yt = boxes[-1]
    letters(j, 'NOVA TECH', (u0 + u1) / 2, v0 + 0.5, yt + 1.4, 1.8, (255, 255, 255), u1 - u0 - 2, cols[0], 0.4)
    # entrada: tubo de vidro saliente com escada colorida atras
    door_u = boxes[0][0] + 6.0
    mass(j, door_u - 3.5, door_u + 3.5, -2.0, boxes[0][2] + 0.5, Y_WALK, Y_WALK + 4.6, (190, 210, 240), 'vidro')
    j.bx(door_u - 3.7, door_u + 3.7, -2.2, boxes[0][2] + 0.5, Y_WALK + 4.6, Y_WALK + 5.0, cols[0], 'liso')
    letters(j, 'NOVA TECH', door_u, -2.2, Y_WALK + 3.6, 0.5, cols[0], 6.0, (255, 255, 255), 0.2)
    glass_door(j, door_u, -2.0, 2.4, 2.7)
    # bicicletario e pufes coloridos na frente
    for k in range(10): j.bx(door_u + 5 + k * 0.9 - 0.03, door_u + 5 + k * 0.9 + 0.03, -2.0, -1.0, Y_WALK, Y_WALK + 0.8, (60, 62, 66), 'metal')
    for k in range(5): j.cyl(door_u - 6 - k * 1.2, -1.2, 0.35, Y_WALK, Y_WALK + 0.45, cols[k % 4], 'liso', 10)
    return door_u, -2.0


# ======================================================================== 11. high-tech (exoesqueleto)
def engenheiro(j, w, d, nf, spec):
    Y = (240, 190, 30); RED = (210, 50, 40); BL = (40, 110, 200); GR = (70, 160, 80)
    yt = Y_WALK + 0.15 + HH + (nf - 1) * FH; bay = 7.2
    mass(j, 1.2, w - 1.2, 2.0, d - 2.0, Y_WALK, yt, (200, 220, 232), 'escritorio', uvf=(1.8, FH, yt))
    nb = max(2, int((w - 2.4) / bay)); bw = (w - 2.4) / nb
    nbv = max(1, int((d - 4) / bay))
    M = j.M; F = j.F
    # exoesqueleto: pilares e vigas brancos a 1,2 m da fachada, X em cada bay, pisos tecnicos
    for k in range(nb + 1):
        u = 1.2 + k * bw
        for v in (0.8, d - 0.8): j.bx(u - 0.3, u + 0.3, v - 0.3, v + 0.3, Y_WALK, yt + 2.0, (240, 240, 240), 'metal'); j.solid(u - 0.3, u + 0.3, v - 0.3, v + 0.3)
    for f in range(nf + 1):
        y = Y_WALK + 0.15 + (HH + (f - 1) * FH if f > 0 else 0)
        if f == 0: continue
        for v in (0.8, d - 0.8): j.bx(0.9, w - 0.9, v - 0.18, v + 0.18, y - 0.3, y, (240, 240, 240), 'metal')
        for k in range(nb + 1): j.bx(1.2 + k * bw - 0.1, 1.2 + k * bw + 0.1, 0.8, 2.0, y - 0.22, y - 0.08, (220, 220, 220), 'metal')
        if f < nf and f % 2 == 1:
            for k in range(nb):
                u = 1.2 + k * bw
                for v in (0.8, d - 0.8):
                    beam(M, F.p(u + 0.2, v, y), F.p(u + bw - 0.2, v, y + 2 * FH - 0.3), 0.26, RED if v < 1 else (230, 230, 230))
                    beam(M, F.p(u + bw - 0.2, v, y), F.p(u + 0.2, v, y + 2 * FH - 0.3), 0.26, RED if v < 1 else (230, 230, 230))
        # passarelas de grelha
        j.bx(1.2, w - 1.2, 0.6, 2.0, y - 0.08, y - 0.02, (160, 164, 170), 'metal')
        j.bx(1.2, w - 1.2, 0.55, 0.62, y, y + 1.05, (200, 200, 204), 'metal', False)
    # dutos coloridos verticais nos fundos e escada rolante em tubo diagonal na frente
    for k, c in enumerate((BL, GR, Y, RED, BL, GR)):
        u = 3.0 + k * (w - 6) / 5
        j.cyl(u, d + 0.6, 0.6 if k % 2 else 0.9, Y_WALK, yt + 3.0, c, 'metal', 14)
        j.cyl(u, d + 0.6, 1.0, yt + 3.0, yt + 3.6, shade(c, -20), 'metal', 14)
    for k, c in enumerate((BL, GR, Y)):                                  # dutos coloridos tambem na fachada da rua (lado direito)
        u = w - 3.0 - k * 1.4
        j.cyl(u, -0.2, 0.45, Y_WALK + 0.15 + HH, yt + 2.5, c, 'metal', 12)
        for q in range(int((yt - Y_WALK - HH) / FH)): j.cyl(u, -0.2, 0.5, Y_WALK + HH + 0.5 + q * FH, Y_WALK + HH + 0.62 + q * FH, shade(c, -30), 'metal', 12)
        j.cyl(u, -0.2, 0.45, yt + 2.5, yt + 2.9, shade(c, -20), 'metal', 12, True, 0.7)
    for s in range(nf - 1):
        y = Y_WALK + 0.15 + HH + s * FH
        u0_ = 4.0 + (s % 2) * 10.0
        beam(M, F.p(u0_, -0.6, y - FH + 0.6 if s else Y_WALK + 0.6), F.p(u0_ + 10.0, -0.6, y + 0.6), 1.6, (200, 220, 236), 'vidro')
        beam(M, F.p(u0_, -0.6, (y - FH if s else Y_WALK) + 0.1), F.p(u0_ + 10.0, -0.6, y + 0.1), 0.25, RED)
    # cobertura: grua amarela e letreiro
    roof(j, 1.2, w - 1.2, 2.0, d - 2.0, yt, (220, 220, 220), 1.0, equip=3)
    gu, gv = w * 0.7, d * 0.5
    for (a, b) in ((-0.6, -0.6), (0.6, -0.6), (-0.6, 0.6), (0.6, 0.6)): j.bx(gu + a - 0.07, gu + a + 0.07, gv + b - 0.07, gv + b + 0.07, yt, yt + 16.0, Y, 'metal')
    for k in range(13):
        y = yt + 0.6 + k * 1.2
        beam(M, F.p(gu - 0.6, gv - 0.6, y), F.p(gu + 0.6, gv - 0.6, y + 1.2), 0.06, Y); beam(M, F.p(gu - 0.6, gv + 0.6, y + 1.2), F.p(gu + 0.6, gv + 0.6, y), 0.06, Y)
    j.bx(gu - 18.0, gu + 6.0, gv - 0.45, gv + 0.45, yt + 16.0, yt + 16.7, Y, 'metal')
    j.bx(gu + 3.5, gu + 6.0, gv - 0.9, gv + 0.9, yt + 15.0, yt + 16.0, (90, 94, 100), 'concreto')
    j.bx(gu - 0.9, gu + 0.9, gv - 0.9, gv + 0.9, yt + 14.6, yt + 16.0, Y, 'metal')
    beam(M, F.p(gu, gv, yt + 20.0), F.p(gu - 17.0, gv, yt + 16.7), 0.05, DARK); beam(M, F.p(gu, gv, yt + 20.0), F.p(gu + 5.5, gv, yt + 16.7), 0.05, DARK)
    j.bx(gu - 0.2, gu + 0.2, gv - 0.2, gv + 0.2, yt + 16.7, yt + 20.0, Y, 'metal')
    j.cyl(gu - 13.0, gv, 0.02, yt + 8.0, yt + 16.0, DARK, 'metal', 4); j.bx(gu - 13.4, gu - 12.6, gv - 0.4, gv + 0.4, yt + 7.4, yt + 8.0, Y, 'metal')
    letters(j, 'PILAR', w * 0.3, 0.6, yt + 1.4, 2.0, Y, 14.0, (40, 44, 50), 0.4)
    door_u = w / 2
    glass_door(j, door_u, 2.0, 3.0, 2.8, Y, (6.0, 2.4))
    letters(j, 'PILAR CONSTRUTORA', door_u, -0.6, Y_WALK + 0.15 + HH - 1.0, 0.6, Y, 16.0, (40, 44, 50), 0.3)
    return door_u, 2.0


# ======================================================================== 12. hipermercado
def repositor(j, w, d, nf, spec):
    RED = (210, 40, 40); GRN = (60, 150, 70); yt = Y_WALK + 9.0
    mass(j, 0, w, 3.0, d, Y_WALK, yt, (236, 234, 228), 'concreto')
    for (jj, L) in faces(j, 0, w, 3.0, d):
        q = 0.0
        while q < L: jj.bx(q, q + 2.9, -0.06, 0.0, Y_WALK + 4.2, yt - 0.6, (226, 224, 218) if int(q / 3) % 2 else (240, 238, 232), 'metal'); q += 3.0
        jj.bx(-0.1, L + 0.1, -0.2, 0.0, yt - 0.6, yt, RED, 'liso')
        jj.bx(-0.1, L + 0.1, -0.2, 0.0, Y_WALK + 3.9, Y_WALK + 4.2, GRN, 'liso')
    # faixa de vidro do terreo (vitrine) na frente
    jf = faces(j, 0, w, 3.0, d)[0][0]
    ribbon(jf, w, Y_WALK + 0.3, 3.4, (160, 196, 210), 2.0, (60, 62, 66), 1.0, w - 1.0)
    roof(j, 0, w, 3.0, d, yt, (226, 224, 218), 0.8, equip=8)
    for k in range(4): j.bx(4 + k * (w - 10) / 3, 6.5 + k * (w - 10) / 3, d * 0.4, d * 0.4 + 6, yt + 0.04, yt + 0.4, (150, 160, 180), 'vidro')   # claraboias
    # portico de entrada em abobada de vidro, saliente
    door_u = w / 2; R = 5.5
    for s in (-1, 1): mass(j, door_u + s * (R + 0.2) - 0.5, door_u + s * (R + 0.2) + 0.5, -4.0, 3.0, Y_WALK, Y_WALK + 6.0, RED, 'liso')
    G = J(j.L, j.sub(0, 0, 1))
    vault(J(j.L, j.sub(door_u, -4.0, 1)), 0.0, 7.0, 0.0, R + 0.7, Y_WALK + 6.0, (200, 220, 230), 'vidro', 12, end=False)
    Jv = J(j.L, j.sub(door_u, -4.0, 1))
    for k in range(5): vault(Jv, k * 1.7, k * 1.7 + 0.15, 0.0, R + 0.75, Y_WALK + 6.0, (240, 240, 240), 'metal', 12, end=False)
    j.bx(door_u - R, door_u + R, -4.02, -3.9, Y_WALK + 4.0, Y_WALK + 6.0, (250, 250, 250), 'liso')
    letters(j, 'SUPERBOM', door_u, -4.02, Y_WALK + 4.25, 1.4, RED, 2 * R - 1)
    glass_door(j, door_u - 2.0, 3.0, 2.8, 2.7); glass_door(j, door_u + 2.0, 3.0, 2.8, 2.7)
    # letreiro gigante na platibanda e logo
    letters(j, 'SUPERBOM', w * 0.25, 2.8, yt - 3.4, 2.4, (255, 255, 255), w * 0.35, RED, 0.5)
    G = J(j.L, j.sub(w * 0.8, 2.8, 0)); G.bx(-2.6, 2.6, -0.15, 0.0, yt - 5.2, yt + 0.6, GRN, 'liso'); G.bx(-1.6, 1.6, -0.2, -0.15, yt - 3.6, yt - 1.6, (255, 255, 255), 'liso')
    for q in range(3): G.bx(-1.2 + q * 0.9, -0.6 + q * 0.9, -0.24, -0.2, yt - 3.1, yt - 2.4, RED, 'liso')
    # carrinhos (abrigo) e totem
    j.bx(door_u + R + 3, door_u + R + 10, -3.0, -1.0, Y_WALK + 2.4, Y_WALK + 2.55, RED, 'metal')
    for s in (0, 1): j.cyl(door_u + R + 3.2 + s * 6.6, -2.0, 0.06, Y_WALK, Y_WALK + 2.4, DARK, 'metal', 6)
    for k in range(8): j.bx(door_u + R + 3.6 + k * 0.75, door_u + R + 4.2 + k * 0.75, -2.6, -1.4, Y_WALK + 0.15, Y_WALK + 1.0, (180, 184, 190), 'metal', False)
    return door_u, 3.0


# ======================================================================== 13. lanchonete retro
def atendente(j, w, d, nf, spec):
    RED = (210, 40, 40); CH = (220, 224, 230); CR = (250, 240, 214)
    dw = min(w - 8.0, 46.0); u0 = (w - dw) / 2; u1 = u0 + dw; dv0, dv1 = 4.0, 16.0; R = (dv1 - dv0) / 2; yt = Y_WALK + 5.2
    mass(j, u0 + R, u1 - R, dv0, dv1, Y_WALK, yt, CR, 'reboco')
    for uc in (u0 + R, u1 - R): j.cyl(uc, dv0 + R, R, Y_WALK, yt, CR, 'reboco', 20); j.solid(uc - R * 0.7, uc + R * 0.7, dv0, dv1)
    # faixas cromadas, faixa vermelha e janelas corridas, contornando as pontas
    def ring(y0_, y1_, col, mat, rr):
        j.bx(u0 + R, u1 - R, dv0 - (rr - R), dv0, y0_, y1_, col, mat, False); j.bx(u0 + R, u1 - R, dv1, dv1 + (rr - R), y0_, y1_, col, mat, False)
        for uc in (u0 + R, u1 - R):
            j.M.m(mat); x, z = j.F.xz(uc, dv0 + R)
            for k in range(10):
                s = 1 if uc > w / 2 else -1
                a0 = -PI / 2 + PI * k / 10; a1 = -PI / 2 + PI * (k + 1) / 10
                p0 = j.F.xz(uc + s * rr * math.cos(a0), dv0 + R + rr * math.sin(a0)); p1 = j.F.xz(uc + s * rr * math.cos(a1), dv0 + R + rr * math.sin(a1))
                am = (a0 + a1) / 2; nx, nz = j.F.xz(uc + s * math.cos(am), dv0 + R + math.sin(am)); nx -= x; nz -= z
                j.M.quad((p0[0], y0_, p0[1]), (p1[0], y0_, p1[1]), (p1[0], y1_, p1[1]), (p0[0], y1_, p0[1]), col, (nx, 0, nz))
    ring(Y_WALK + 1.1, Y_WALK + 2.9, (130, 170, 190), 'vidro', R + 0.03)
    for yy in (Y_WALK + 0.9, Y_WALK + 3.0, Y_WALK + 3.9, yt - 0.3): ring(yy, yy + 0.16, CH, 'metal', R + 0.08)
    ring(Y_WALK + 3.2, Y_WALK + 3.8, RED, 'liso', R + 0.06)
    ring(Y_WALK + 0.15, Y_WALK + 0.85, (60, 140, 160), 'liso', R + 0.05)
    j.bx(u0 + 1, u1 - 1, dv0 + 1, dv1 - 1, yt, yt + 0.4, CH, 'metal')
    # letreiro de telhado com neon e totem alto em forma de seta
    letters(j, 'LANCHONETE DO ZE', (u0 + u1) / 2, dv0 + R - 0.3, yt + 0.6, 1.4, (255, 220, 80), dw - 2 * R, RED, 0.4)
    j.bx((u0 + u1) / 2 - 8, (u0 + u1) / 2 + 8, dv0 + R - 0.3, dv0 + R, yt + 0.4, yt + 0.6, CH, 'metal')
    tu = u1 + 2.5 if u1 + 4 < w else u0 - 2.5
    j.cyl(tu, 0.0, 0.25, Y_WALK, Y_WALK + 12.0, CH, 'metal', 10)
    G = J(j.L, j.sub(tu, 0.0, 1))
    G.bx(-1.8, 1.8, -0.25, 0.25, Y_WALK + 7.0, Y_WALK + 11.0, RED, 'liso'); G.bx(-1.9, 1.9, -0.3, 0.3, Y_WALK + 7.0, Y_WALK + 7.2, GLOW, 'liso'); G.bx(-1.9, 1.9, -0.3, 0.3, Y_WALK + 10.8, Y_WALK + 11.0, GLOW, 'liso')
    for s in (-1, 1): sign_text(G, 'DINER', 0, s * 0.26 if s < 0 else -0.26, Y_WALK + 8.4, 1.0, (255, 230, 120), 0.05) if s < 0 else None
    G.bx(-1.2, 1.2, -0.2, 0.2, Y_WALK + 5.0, Y_WALK + 6.6, (255, 220, 80), 'liso')
    j.ball(tu, 0.0, Y_WALK + 12.3, 0.5, (255, 220, 80), 'liso')
    # entrada com marquise cromada e degraus; mesas na varanda
    door_u = (u0 + u1) / 2
    glass_door(j, door_u, dv0, 2.0, 2.6, CH, (5.0, 2.0))
    for k in range(4):
        tu_ = u0 + R + 2 + k * 4.0
        if abs(tu_ - door_u) < 4: continue
        j.cyl(tu_, 1.8, 0.45, Y_WALK + 0.72, Y_WALK + 0.76, (255, 255, 255), 'liso', 12); j.cyl(tu_, 1.8, 0.05, Y_WALK, Y_WALK + 0.72, CH, 'metal', 6)
        j.cyl(tu_, 1.8, 0.03, Y_WALK + 0.76, Y_WALK + 2.3, CH, 'metal', 6); j.cyl(tu_, 1.8, 1.3, Y_WALK + 2.1, Y_WALK + 2.4, RED if k % 2 else (255, 255, 255), 'liso', 8, False, 0.05)
        for s in (-1, 1): j.cyl(tu_ + s * 0.8, 1.8, 0.22, Y_WALK, Y_WALK + 0.48, RED, 'liso', 10)
        j.solid(tu_ - 0.5, tu_ + 0.5, 1.3, 2.3)
    # area atras do diner (cozinha) — bloco baixo
    mass(j, u0 + 4, u1 - 4, dv1, min(d - 1, dv1 + 8), Y_WALK, Y_WALK + 4.0, (220, 214, 200), 'reboco')
    roof(j, u0 + 4, u1 - 4, dv1, min(d - 1, dv1 + 8), Y_WALK + 4.0, (220, 214, 200), 0.6, equip=3)
    j.cyl(u0 + 8, dv1 + 4, 0.4, Y_WALK + 4.0, Y_WALK + 6.5, CH, 'metal', 10)
    return door_u, dv0


# ======================================================================== 14. posto
def frentista(j, w, d, nf, spec):
    BL = (30, 100, 180); YE = (250, 200, 40)
    cw = min(w - 6.0, 44.0); cu0 = (w - cw) / 2; cu1 = cu0 + cw; cv0, cv1 = 0.0, 14.0; ch = Y_WALK + 5.6
    # cobertura com bordas iluminadas
    j.bx(cu0, cu1, cv0, cv1, ch, ch + 1.0, (250, 250, 250), 'metal')
    for (jj, L) in faces(j, cu0, cu1, cv0, cv1):
        jj.bx(-0.02, L + 0.02, -0.06, 0.0, ch + 0.1, ch + 0.9, BL, 'liso'); jj.bx(-0.02, L + 0.02, -0.08, -0.06, ch + 0.4, ch + 0.55, YE, 'liso')
    letters(j, 'ROTA SUL', (cu0 + cu1) / 2, -0.08, ch + 0.2, 0.6, (255, 255, 255), cw * 0.4)
    j.M.m('liso')
    for k in range(int(cw / 4)):
        for q in range(3): u = cu0 + 2 + k * 4; v = 2.5 + q * 4.5; j.M.poly([j.F.p(u - 0.6, v - 0.6, ch - 0.01), j.F.p(u + 0.6, v - 0.6, ch - 0.01), j.F.p(u + 0.6, v + 0.6, ch - 0.01), j.F.p(u - 0.6, v + 0.6, ch - 0.01)], GLOW, (0, -1, 0))
    ni = max(2, int(cw / 10))
    for k in range(ni):
        u = cu0 + (k + 0.5) * cw / ni
        j.cyl(u, 7.0, 0.35, Y_WALK, ch, (240, 240, 240), 'metal', 12); j.solid(u - 0.5, u + 0.5, 3.5, 10.5)
        j.bx(u - 0.6, u + 0.6, 3.5, 10.5, Y_WALK, Y_WALK + 0.25, (240, 200, 40), 'concreto')            # ilha
        for v in (5.0, 9.0):
            j.bx(u - 0.4, u + 0.4, v - 0.5, v + 0.5, Y_WALK + 0.25, Y_WALK + 2.0, (250, 250, 250), 'metal')
            j.bx(u - 0.42, u + 0.42, v - 0.52, v + 0.52, Y_WALK + 1.6, Y_WALK + 2.0, BL, 'liso')
            for s in (-1, 1): j.bx(u + s * 0.42 - 0.02, u + s * 0.42 + 0.02, v - 0.3, v + 0.1, Y_WALK + 1.1, Y_WALK + 1.5, (40, 40, 44), 'liso')
            j.bx(u - 0.2, u + 0.2, v - 0.56, v - 0.52, Y_WALK + 1.2, Y_WALK + 1.5, (120, 220, 140), 'liso')
    # faixas de piso das pistas
    for k in range(ni + 1):
        u = cu0 + k * cw / ni
        j.bx(u - 0.08, u + 0.08, 0.5, 13.5, Y_WALK + 0.003, Y_WALK + 0.012, (250, 250, 250), 'liso')
    # loja de conveniencia atras
    sv0 = 16.0; sv1 = min(d - 1.0, 30.0); su0, su1 = cu0 + 2, cu1 - 2
    mass(j, su0, su1, sv0, sv1, Y_WALK, Y_WALK + 5.0, (246, 246, 246), 'reboco')
    jf = faces(j, su0, su1, sv0, sv1)[0][0]
    ribbon(jf, su1 - su0, Y_WALK + 0.3, 3.2, (170, 200, 214), 2.0, DARK, 1.0)
    jf.bx(-0.1, su1 - su0 + 0.1, -0.6, 0.0, Y_WALK + 3.7, Y_WALK + 5.0, BL, 'liso')
    letters(j, 'CONVENIENCIA 24H', (su0 + su1) / 2, sv0 - 0.6, Y_WALK + 4.0, 0.7, (255, 255, 255), su1 - su0 - 4)
    roof(j, su0, su1, sv0, sv1, Y_WALK + 5.0, (246, 246, 246), 0.6, equip=2)
    door_u = (su0 + su1) / 2
    glass_door(j, door_u, sv0, 2.4, 2.7)
    # totem de precos
    tu = cu0 - 2.0 if cu0 > 3 else cu1 + 2.0
    j.bx(tu - 1.2, tu + 1.2, -1.0, -0.4, Y_WALK, Y_WALK + 9.0, BL, 'liso'); j.solid(tu - 1.2, tu + 1.2, -1.0, -0.4)
    G = J(j.L, j.sub(tu, -1.0, 0))
    G.bx(-1.0, 1.0, -0.05, 0.0, Y_WALK + 7.0, Y_WALK + 8.6, (255, 255, 255), 'liso'); G.bx(-0.7, 0.7, -0.08, -0.05, Y_WALK + 7.4, Y_WALK + 8.2, YE, 'liso')
    for k in range(3):
        G.bx(-1.0, 1.0, -0.05, 0.0, Y_WALK + 1.6 + k * 1.7, Y_WALK + 3.0 + k * 1.7, (20, 20, 24), 'liso')
        sign_text(G, '5.89' if k == 0 else ('6.19' if k == 1 else '4.39'), 0.2, -0.05, Y_WALK + 1.9 + k * 1.7, 0.8, (255, 60, 40) if k else (80, 255, 120), 0.03)
    # calibrador e lavagem
    j.bx(cu1 + 1.0, cu1 + 1.6, 4.0, 4.6, Y_WALK, Y_WALK + 1.6, (240, 240, 240), 'metal') if cu1 + 2 < w else None
    return door_u, sv0


# ======================================================================== 15. limpeza
def diarista(j, w, d, nf, spec):
    AQ = (40, 170, 200); LI = (150, 220, 230); WH = (250, 252, 252)
    bw = min(w - 6.0, 52.0); u0 = (w - bw) / 2; u1 = u0 + bw; v0, v1 = 4.0, min(d - 2.0, 20.0); R = 5.0; yt = Y_WALK + 0.15 + HH + 2 * FH
    mass(j, u0 + R, u1 - R, v0, v1, Y_WALK, yt, WH, 'reboco')
    mass(j, u0, u0 + R, v0 + R, v1, Y_WALK, yt, WH, 'reboco'); mass(j, u1 - R, u1, v0 + R, v1, Y_WALK, yt, WH, 'reboco')
    # quinas de vidro curvas (frente) com montantes
    M = j.M; F = j.F
    for (uc, s) in ((u0 + R, -1), (u1 - R, 1)):
        for k in range(8):
            a0 = PI / 2 * k / 8; a1 = PI / 2 * (k + 1) / 8
            p0 = F.xz(uc + s * R * math.sin(a0), v0 + R - R * math.cos(a0)); p1 = F.xz(uc + s * R * math.sin(a1), v0 + R - R * math.cos(a1))
            am = (a0 + a1) / 2; nx, nz = F.xz(uc + s * math.sin(am), v0 + R - math.cos(am)); c0 = F.xz(uc, v0 + R); nx -= c0[0]; nz -= c0[1]
            M.m('vidro'); M.quad((p0[0], Y_WALK, p0[1]), (p1[0], Y_WALK, p1[1]), (p1[0], yt, p1[1]), (p0[0], yt, p0[1]), LI, (nx, 0, nz))
            M.m('metal'); M.box(p0[0] - 0.05, p0[0] + 0.05, Y_WALK, yt, p0[1] - 0.05, p0[1] + 0.05, (230, 236, 240))
            for f in range(3):
                y = Y_WALK + 0.15 + HH + f * FH - 0.2 if f < 2 else yt - 0.3
                M.quad((p0[0] + nx * 0.06, y, p0[1] + nz * 0.06), (p1[0] + nx * 0.06, y, p1[1] + nz * 0.06), (p1[0] + nx * 0.06, y + 0.3, p1[1] + nz * 0.06), (p0[0] + nx * 0.06, y + 0.3, p0[1] + nz * 0.06), AQ, (nx, 0, nz))
        j.cyl(uc, v0 + R, R * 0.98, yt - 0.01, yt, WH, 'reboco', 16)
        j.solid(uc - R * 0.7 if s > 0 else uc - R, uc + R if s > 0 else uc + R * 0.7, v0 + 0.5, v0 + R)
    for (jj, L) in faces(j, u0 + R, u1 - R, v0, v1)[:1] + faces(j, u0, u1, v0 + R, v1)[1:]:
        for f in range(3):
            y = Y_WALK + 0.15 + (HH + (f - 1) * FH if f else 0)
            ribbon(jj, L, y + 0.9, 1.6, LI, 1.5, (230, 236, 240), 0.6)
            # faixa em onda (blocos escalonados) acima de cada andar
            q = 0.0
            while q < L - 0.4: jj.bx(q, q + 0.4, -0.08, 0.0, y + 2.75 + 0.18 * math.sin(q * 0.8), y + 2.95 + 0.18 * math.sin(q * 0.8), AQ, 'liso'); q += 0.4
    roof(j, u0 + R, u1 - R, v0, v1, yt, WH, 0.6, equip=2)
    # bolhas na fachada e letreiro
    r = j.r
    for k in range(14):
        bu = r.uniform(u0 + R + 1, u1 - R - 1); by = r.uniform(Y_WALK + 6, yt - 0.5)
        j.ball(bu, v0 - 0.3, by, r.uniform(0.25, 0.7), (200, 240, 250), 'liso')
    letters(j, 'BRILHO LIMPEZA', (u0 + u1) / 2, v0 - 0.1, yt + 0.8, 1.2, AQ, bw - 2 * R, WH, 0.4)
    door_u = (u0 + u1) / 2
    glass_door(j, door_u, v0, 2.4, 2.7, AQ, (5.0, 2.2))
    for s in (-1, 1): planter(j, door_u + s * 5 - 1.5, door_u + s * 5 + 1.5, 1.0, 2.6, 'flores')
    return door_u, v0


# ======================================================================== 16. oficina (dente de serra)
def mecanico(j, w, d, nf, spec):
    YE = (230, 170, 30); GR = (90, 100, 110); yt = Y_WALK + 6.0; FV = 6.0
    mass(j, 0, w, FV, d, Y_WALK, yt, (196, 198, 200), 'metal')
    # marquise de servico em balanco sobre os boxes (v 0..FV), com tirantes e luzes
    j.bx(-0.3, w + 0.3, -0.4, FV, Y_WALK + 4.8, Y_WALK + 5.3, (230, 232, 234), 'metal')
    j.bx(-0.32, w + 0.32, -0.45, -0.4, Y_WALK + 4.8, Y_WALK + 5.3, YE, 'liso')
    j.M.m('liso'); q = 3.0
    while q < w - 2: j.M.poly([j.F.p(q - 0.8, 1.0, Y_WALK + 4.79), j.F.p(q + 0.8, 1.0, Y_WALK + 4.79), j.F.p(q + 0.8, 1.6, Y_WALK + 4.79), j.F.p(q - 0.8, 1.6, Y_WALK + 4.79)], GLOW, (0, -1, 0)); q += 6.0
    q = 0.0
    while q <= w: j.cyl(q, 0.0, 0.14, Y_WALK, Y_WALK + 4.8, GR, 'metal', 8); j.solid(q - 0.15, q + 0.15, -0.15, 0.15); q += 12.0
    for (jj, L) in faces(j, 0, w, FV, d):
        q = 0.0
        while q < L: jj.bx(q, q + 0.12, -0.06, 0.0, Y_WALK + 1.2, yt, (176, 178, 182), 'metal'); q += 0.5    # chapa ondulada
        jj.bx(-0.05, L + 0.05, -0.08, 0.0, Y_WALK, Y_WALK + 1.2, (110, 104, 98), 'concreto')
        jj.bx(-0.05, L + 0.05, -0.1, 0.0, yt - 0.5, yt, YE, 'liso')
    # cobertura em dente de serra (sheds com vidro)
    M = j.M; F = j.F; sw = 5.0; n = int((d - 2.0) / sw)
    for k in range(n):
        v0 = 2.0 + k * sw; v1 = v0 + sw
        if v0 < FV: continue
        M.m('metal'); M.quad(F.p(0, v0, yt + 2.4), F.p(w, v0, yt + 2.4), F.p(w, v1, yt), F.p(0, v1, yt), (150, 154, 160), (0, 1, -0.4))
        M.m('vidro'); M.quad(F.p(0, v0, yt), F.p(w, v0, yt), F.p(w, v0, yt + 2.4), F.p(0, v0, yt + 2.4), (150, 186, 200), F.nv(-1))
        for uu in (0.0, w): M.m('metal'); M.poly([F.p(uu, v0, yt), F.p(uu, v1, yt), F.p(uu, v0, yt + 2.4)], (176, 178, 182), F.nu(-1 if uu == 0 else 1))
    # portoes abertos com elevadores e carros dentro (vao escuro), portao de enrolar recolhido
    nb = max(3, int((w - 12) / 6.0)); door_u = 4.0
    r = j.r
    for k in range(nb):
        u = 10.0 + k * 6.0
        if u + 5 > w - 1: break
        j.bx(u, u + 5.0, FV - 0.12, FV, Y_WALK, Y_WALK + 4.4, (40, 42, 46), 'liso')                       # vao escuro do box
        j.bx(u - 0.1, u + 5.1, FV - 0.4, FV, Y_WALK + 4.4, Y_WALK + 4.75, (210, 212, 216), 'metal')       # portao recolhido
        lift = k % 3 != 2; yc = Y_WALK + (1.6 if lift else 0.0)
        if lift:
            for s in (0, 1): j.bx(u + 0.3 + s * 4.0, u + 0.7 + s * 4.0, 2.0, 2.4, Y_WALK, Y_WALK + 3.2, (220, 50, 40), 'metal')   # colunas do elevador
            for s in (0, 1): j.bx(u + 0.7 + s * 3.0, u + 1.3 + s * 3.0, 0.8, 4.4, yc - 0.12, yc, (200, 40, 30), 'metal')   # bracos
        cc = r.choice(((40, 80, 160), (200, 200, 204), (160, 30, 30), (30, 30, 34), (230, 200, 60)))
        j.bx(u + 1.0, u + 4.0, 0.6, 4.6, yc + 0.35, yc + 1.05, cc, 'liso')                                  # carro (lateral para a rua)
        j.bx(u + 1.2, u + 3.8, 1.5, 3.7, yc + 1.05, yc + 1.55, (70, 84, 96), 'vidro')
        j.bx(u + 1.1, u + 3.9, 1.4, 3.8, yc + 1.55, yc + 1.62, cc, 'liso')
        for (a_, b_) in ((1.2, 1.2), (3.8, 1.2), (1.2, 4.0), (3.8, 4.0)): j.bx(u + a_ - 0.12, u + a_ + 0.12, b_ - 0.33, b_ + 0.33, yc, yc + 0.66, (24, 24, 24), 'liso')
        if not lift: j.bx(u + 0.2, u + 1.0, 4.4, 5.6, Y_WALK, Y_WALK + 1.0, (200, 40, 30), 'metal')            # carrinho de ferramentas
        j.solid(u, u + 5.0, 0.6, 4.6)
        for q in range(int(5.0 / 0.5)): j.bx(u + 0.1 + q * 0.5, u + 0.35 + q * 0.5, -1.0, 0.0, Y_WALK + 0.003, Y_WALK + 0.012, YE, 'liso')
        sign_text(j, str(k + 1), u + 2.5, FV - 0.42, Y_WALK + 4.42, 0.3, YE, 0.03)
    letters(j, 'OFICINA DO TONINHO', w / 2, -0.46, Y_WALK + 4.85, 0.36, (30, 30, 30), w - 4)
    for s in (0, 1): j.bx(w * 0.62 + s * 15.0 - 0.1, w * 0.62 + s * 15.0 + 0.1, FV + 1.0, FV + 1.3, yt + 1.0, yt + 2.6, DARK, 'metal')
    letters(j, 'AUTO CENTER', w * 0.62 + 7.5, FV + 1.0, yt + 2.6, 1.2, (255, 255, 255), 14.0, GR, 0.3)
    # escritorio/recepcao com vidro na ponta
    j.bx(0.5, 8.5, FV - 0.06, FV, Y_WALK + 0.3, Y_WALK + 3.6, (170, 200, 214), 'vidro')
    glass_door(j, door_u, FV, 2.0, 2.6, YE)
    # torre de pneus e placa de pneu gigante
    for k in range(6): j.cyl(w - 2.0, -1.4, 0.36, Y_WALK + k * 0.26, Y_WALK + (k + 1) * 0.26 - 0.01, (24, 24, 24), 'liso', 14)
    j.solid(w - 2.4, w - 1.6, -1.8, -1.0)
    return door_u, FV


# ======================================================================== 17. centro de distribuicao
def entregador(j, w, d, nf, spec):
    OR = (240, 140, 40); yt = Y_WALK + 11.0
    mass(j, 0, w, 0.0, d, Y_WALK, yt, (226, 228, 230), 'metal')
    for (jj, L) in faces(j, 0, w, 0.0, d):
        q = 0.0
        while q < L: jj.bx(q, q + 0.1, -0.05, 0.0, Y_WALK + 1.2, yt, (210, 212, 216), 'metal'); q += 0.6
        jj.bx(-0.05, L + 0.05, -0.08, 0.0, yt - 1.2, yt - 0.4, OR, 'liso')
        jj.bx(-0.05, L + 0.05, -0.08, 0.0, Y_WALK, Y_WALK + 1.2, (120, 120, 124), 'concreto')
        ribbon(jj, L, yt - 2.6, 1.0, (170, 196, 210), 2.0, (90, 94, 100), 2.0)
    roof(j, 0, w, 0.0, d, yt, (226, 228, 230), 0.8, equip=5)
    # escritorio de vidro em balanco na quina esquerda
    mass(j, 0.0, 14.0, -3.0, 0.2, Y_WALK, Y_WALK + 8.0, (150, 190, 214), 'vidro')
    for k in range(9): j.bx(k * 1.75 - 0.05, k * 1.75 + 0.05, -3.12, -3.0, Y_WALK, Y_WALK + 8.0, (60, 62, 66), 'metal')
    j.bx(-0.2, 14.2, -3.2, 0.2, Y_WALK + 8.0, Y_WALK + 8.6, OR, 'liso')
    letters(j, 'EXPRESSO JA', w * 0.55, -0.1, yt - 4.4, 1.8, OR, w * 0.45, (255, 255, 255), 0.4)
    # docas: portas seccionais, abrigos pretos, para-choques, plataforma e caminhoes
    nd = max(3, int((w - 18) / 5.0))
    for k in range(nd):
        u = 17.0 + k * 5.0
        if u + 3.4 > w - 1: break
        j.bx(u, u + 3.4, -0.08, 0.0, Y_WALK + 1.2, Y_WALK + 4.4, (200, 200, 204), 'metal')
        for q in range(8): j.bx(u, u + 3.4, -0.1, -0.08, Y_WALK + 1.2 + q * 0.4 - 0.02, Y_WALK + 1.2 + q * 0.4 + 0.02, (170, 172, 176), 'metal')
        j.bx(u - 0.4, u + 3.8, -0.8, -0.1, Y_WALK + 1.0, Y_WALK + 4.8, (30, 30, 32), 'liso')
        j.bx(u + 0.1, u + 3.3, -0.82, -0.78, Y_WALK + 1.2, Y_WALK + 4.6, (60, 60, 64), 'liso')
        for s in (0.2, 3.2): j.bx(u + s - 0.15, u + s + 0.15, -1.0, -0.8, Y_WALK + 0.6, Y_WALK + 1.1, (20, 20, 20), 'liso')
        j.bx(u - 0.4, u + 3.8, -1.0, 0.0, Y_WALK, Y_WALK + 1.2, (130, 128, 124), 'concreto')
        j.bx(u + 1.4, u + 2.0, -0.12, -0.08, Y_WALK + 4.7, Y_WALK + 4.9, (60, 220, 90) if k % 2 else (230, 40, 40), 'liso')
    j.solid(16.0, w, -1.0, 0.0)
    door_u = 7.0
    glass_door(j, door_u, -3.0, 2.2, 2.7, OR)
    return door_u, -3.0


# ======================================================================== 18. central de triagem
def lixeiro(j, w, d, nf, spec):
    GR = (70, 150, 70); DG = (40, 90, 50); yt = Y_WALK + 10.0; M = j.M; F = j.F
    sh0 = 0.0; sh1 = w - 16.0
    mass(j, sh0, sh1, 2.0, d, Y_WALK, yt, (90, 160, 90), 'metal')
    for (jj, L) in faces(j, sh0, sh1, 2.0, d):
        q = 0.0
        while q < L: jj.bx(q, q + 0.1, -0.05, 0.0, Y_WALK + 1.4, yt, (70, 130, 72), 'metal'); q += 0.6
        jj.bx(-0.05, L + 0.05, -0.08, 0.0, Y_WALK, Y_WALK + 1.4, (120, 120, 120), 'concreto')
        jj.bx(-0.05, L + 0.05, -0.08, 0.0, yt - 0.6, yt, (240, 240, 236), 'liso')
    # telhado em duas aguas com lanternim
    for (va, vb, s) in ((2.0, 2.0 + (d - 2) / 2, 1), (2.0 + (d - 2) / 2, d, -1)):
        M.m('metal'); M.quad(F.p(-0.5, va, yt + (0 if s > 0 else 3.0)), F.p(sh1 + 0.5, va, yt + (0 if s > 0 else 3.0)), F.p(sh1 + 0.5, vb, yt + (3.0 if s > 0 else 0)), F.p(-0.5, vb, yt + (3.0 if s > 0 else 0)), (210, 212, 214), (0, 1, 0))
    for uu, s in ((0.0, -1), (sh1, 1)): M.m('metal'); M.poly([F.p(uu, 2.0, yt), F.p(uu, d, yt), F.p(uu, 2.0 + (d - 2) / 2, yt + 3.0)], (90, 160, 90), F.nu(s))
    j.bx(2, sh1 - 2, 2.0 + (d - 2) / 2 - 1.0, 2.0 + (d - 2) / 2 + 1.0, yt + 3.0, yt + 4.0, (180, 210, 220), 'vidro')
    # portoes grandes com faixas
    for k in range(3):
        u = 4.0 + k * (sh1 - 8) / 3
        j.bx(u, u + 6.0, -0.08, 0.0, Y_WALK, Y_WALK + 6.0, (200, 200, 204), 'metal')
        for q in range(12): j.bx(u, u + 6.0, -0.1, -0.08, Y_WALK + q * 0.5 - 0.02, Y_WALK + q * 0.5 + 0.02, (170, 172, 176), 'metal')
        j.bx(u - 0.3, u + 6.3, -0.3, 0.0, Y_WALK + 6.0, Y_WALK + 6.6, DG, 'liso')
        for q in range(6): j.bx(u + 0.2 + q, u + 0.6 + q, -3.0, -0.2, Y_WALK + 0.003, Y_WALK + 0.012, (240, 200, 40), 'liso')
    letters(j, 'CENTRAL DE COLETA', sh1 / 2, -0.06, yt - 3.0, 1.4, (255, 255, 255), sh1 * 0.7, DG, 0.4)
    # silos, esteira inclinada e chamine
    for k in range(3):
        su = sh1 + 3.5 + (k % 2) * 6.0; sv = 6.0 + k * 7.0
        if sv + 3 > d: break
        j.cyl(su, sv, 2.6, Y_WALK + 3.0, Y_WALK + 15.0, (220, 222, 226), 'metal', 16); j.cyl(su, sv, 2.6, Y_WALK + 15.0, Y_WALK + 16.6, (200, 202, 206), 'metal', 16, True, 0.4)
        j.cyl(su, sv, 0.6, Y_WALK + 1.0, Y_WALK + 3.0, (200, 202, 206), 'metal', 12, True, 2.6)
        for (a, b) in ((-1.6, -1.6), (1.6, -1.6), (1.6, 1.6), (-1.6, 1.6)): j.bx(su + a - 0.12, su + a + 0.12, sv + b - 0.12, sv + b + 0.12, Y_WALK, Y_WALK + 3.6, (60, 64, 70), 'metal')
        for q in range(4): j.cyl(su, sv, 2.65, Y_WALK + 5.0 + q * 3.0, Y_WALK + 5.2 + q * 3.0, GR, 'liso', 16)
        j.solid(su - 2.0, su + 2.0, sv - 2.0, sv + 2.0)
    beam(M, F.p(sh1 + 2.0, 5.0, Y_WALK + 2.0), F.p(sh1 - 2.0, 5.0, yt - 1.0), 1.4, (90, 96, 104), 'metal')
    beam(M, F.p(sh1 + 2.0, 5.0, Y_WALK + 2.75), F.p(sh1 - 2.0, 5.0, yt - 0.25), 1.2, (230, 230, 230), 'metal')
    j.cyl(sh1 - 4.0, d - 4.0, 0.9, yt, yt + 14.0, (200, 200, 200), 'metal', 12, True, 0.7)
    for q in range(3): j.cyl(sh1 - 4.0, d - 4.0, 0.95, yt + 10 + q * 1.2, yt + 10.5 + q * 1.2, (220, 40, 40) if q % 2 == 0 else (250, 250, 250), 'liso', 12)
    # baias de reciclagem coloridas e escritorio
    for k, c in enumerate(((40, 100, 200), (220, 50, 40), (240, 200, 40), (60, 150, 70))):
        u = sh1 + 1.0 + k * 3.6
        if u + 3.2 < w: j.bx(u, u + 3.2, -2.5, 1.0, Y_WALK, Y_WALK + 1.8, c, 'metal'); j.solid(u, u + 3.2, -2.5, 1.0)
    door_u = sh1 / 2
    glass_door(j, 2.0 + (sh1 - 8) / 3 + 7.5 if (sh1 - 8) / 3 > 9 else 2.0, 0.0, 2.0, 2.6, DG, (3.6, 1.6))
    return (2.0 + (sh1 - 8) / 3 + 7.5 if (sh1 - 8) / 3 > 9 else 2.0), 0.0


BUILDERS = {k: v for k, v in globals().items() if k in (
    'medico', 'enfermeiro', 'policial', 'bombeiro', 'professor', 'juiz', 'advogado', 'secretario', 'empresario',
    'programador', 'engenheiro', 'repositor', 'atendente', 'frentista', 'diarista', 'mecanico', 'entregador', 'lixeiro')}


def build(L, F, jid, w, d, nf, spec):
    j = J(L, F)
    return BUILDERS[jid](j, w, d, nf, spec)
