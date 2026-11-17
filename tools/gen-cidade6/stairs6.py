"""Cidade 6 - registro das escadas. y do pe = topo do primeiro degrau (o mais baixo); a linha da escada e
y(s) = y_pe + s * espelho / piso, s medido a partir do primeiro espelho no sentido de subida. (o jogo usa para por o personagem na linha exata da escada e casar a animacao de
subir degrau com cada degrau). Degrau padrao = o da animacao de subir (Mixamo Ascending_Stairs): 20 cm x 21,35 cm."""
R = 0.20
RUN = 0.2135
FL = []          # [x, z do pe da escada (meio), dx, dz (sentido de subida), largura, n degraus, espelho, piso, y do pe]


def add(x, z, dx, dz, width, n, riser, run, ybot):
    FL.append([round(x, 3), round(z, 3), round(dx, 4), round(dz, 4), round(width, 2), int(n), round(riser, 4), round(run, 4), round(ybot, 3)])
