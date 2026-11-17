"""Escadas: Ascending_Stairs, Descending_Stairs, Running_Up_Stairs, Running_Descending_Stairs (Mixamo) -> clipes 15..18
do esqueleto de 55 ossos do TS4 (clips_am5.bin / clips_af5.bin). Cada clipe vira um laço no lugar: o avanço e a
subida/descida do quadril são retirados (linha reta do 1o ao último quadro) e o jogo é quem move o personagem pelo
degrau. O pé de apoio do 1o quadro fica em y = 0. Imprime avanço e desnível por ciclo (m do jogo).
Uso: python3 etapa_escadas_clipes.py <pasta cute> <pasta com os 4 .fbx>"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etapa11_base import NB, K
from etapa118_piscina_clipes import read_clips, write_clips, make_rt, joints, build

NAMES = ['Ascending_Stairs', 'Descending_Stairs', 'Running_Up_Stairs', 'Running_Descending_Stairs']


def main():
    cdir, fbx = sys.argv[1:3]
    for g in ('am5', 'af5'):
        clips = read_clips(f'{cdir}/clips_{g}.bin')[:15]
        rt = make_rt(clips[:11])
        new = []
        for nm in NAMES:
            A, T, fr, s = build(rt, f'{fbx}/{nm}.fbx', 'once', 2, None)
            fr = fr.copy(); n = len(fr)
            J = [joints(rt, fr[f]) for f in range(n)]
            h0, h1 = J[0][0], J[-1][0]
            for f in range(n):
                a = f / (n - 1)
                fr[f, :, 3] -= (J[f][0][0] - J[0][0][0]) * K                    # sem deriva lateral
                fr[f, :, 7] -= (h1[1] - h0[1]) * a * K                           # tira a subida (linear)
                fr[f, :, 11] -= (h1[2] - h0[2]) * a * K                          # tira o avanço (linear)
            J = [joints(rt, fr[f]) for f in range(n)]
            low = min(J[0][20][1], J[0][24][1], J[0][19][1], J[0][23][1])
            fr[:, :, 7] += (rt.P[20][1] - low) * K if False else -low * K + 0.0   # pé mais baixo do 1o quadro no chão
            new.append((T, fr))
            print(g, nm, 'T=%.2f s' % T, 'avanco/ciclo=%.3f m' % ((h1[2] - h0[2]) * K), 'desnivel/ciclo=%.3f m' % ((h1[1] - h0[1]) * K), 'quadros', n)
        write_clips(f'{cdir}/clips_{g}.bin', clips + new)


if __name__ == '__main__':
    main()
