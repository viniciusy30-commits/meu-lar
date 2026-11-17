"""Carro: Entering_Car e Exiting_Car (Mixamo) -> clipes 19 (entrar) e 20 (sair) do esqueleto de 55 ossos do TS4
(clips_am5.bin / clips_af5.bin). O deslocamento do quadril fica no clipe (o jogo ancora o clipe no banco do motorista):
  entrar: comeca em pe ao lado da porta do motorista olhando para o carro e termina sentado com as maos no volante
  sair:   comeca sentado (olhando para a frente do carro) e termina em pe fora do carro, do lado do motorista
O pe mais baixo do 1o quadro do 'entrar' (e do ultimo quadro do 'sair') fica em y = 0.
Uso: python3 etapa_carro_clipes.py <pasta cute> <pasta com Entering_Car.fbx e Exiting_Car.fbx>"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etapa11_base import K
from etapa118_piscina_clipes import read_clips, write_clips, make_rt, joints, build


def main():
    cdir, fbx = sys.argv[1:3]
    for g in ('am5', 'af5'):
        clips = read_clips(f'{cdir}/clips_{g}.bin')[:19]
        rt = make_rt(clips[:11])
        new = []
        for nm, ref in (('Entering_Car', 0), ('Exiting_Car', -1)):
            A, T, fr, s = build(rt, f'{fbx}/{nm}.fbx', 'once', 2, None)
            fr = fr.copy()
            J = joints(rt, fr[ref])
            low = min(J[19][1], J[20][1], J[23][1], J[24][1])
            fr[:, :, 7] -= low * K
            J0, J1 = joints(rt, fr[0]), joints(rt, fr[-1])
            new.append((T, fr))
            print(g, nm, 'T=%.2f' % T, 'quadril ini', np.round(J0[0] * K / K, 1), 'fim', np.round(J1[0], 1), '(cm do jogo)')
        write_clips(f'{cdir}/clips_{g}.bin', clips + new)


if __name__ == '__main__':
    main()
