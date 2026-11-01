"""Etapa 18 - troca SÓ o clipe de PULO (índice 2) pela animação Jumping.fbx (Mixamo).

O Jumping.fbx dura 2,37 s: parado -> agacha (0,4-0,85 s) -> voa (0,85-1,45 s) -> amortece (1,45-1,9 s) -> levanta.
No jogo a altura do pulo vem da física (Renderer3D: vy=3,9 m/s, g=11 -> 0,709 s no ar) e o clipe já começa no ar,
então usamos só a fase aérea da animação (JANELA_A..JANELA_B) esticada para a duração do voo (DUR).
Para a altura não somar duas vezes (física + Mixamo), a pelve é re-travada em cada quadro: o ponto mais baixo do pé
fica em y = 0 (o salto sobe pela física; a perna dobrar/esticar em relação ao chão continua vindo da animação).
Mesmo retargeting da Etapa 11 (T-pose -> A-pose, 55 ossos). Andar, correr, parado e demais clipes ficam idênticos.

Uso:  python3 etapa18_pulo.py <base.bin entrada> <Jumping.fbx> <base.bin saída>
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from etapa11_fbxanim import Anim
from etapa11_retarget import Retarget, JUMP
from etapa11_base import write_base

JANELA_A, JANELA_B = 0.867, 1.450   # s do FBX: pés acabando de sair do chão -> pés voltando ao chão
DUR = 0.709                          # s: tempo no ar do jogo (2 * 3,9 / 11)
FPS = 60


def jump_clip(rt, path):
    A = Anim(path)
    Wb = A.world(0, animated=False)
    Ls = np.linalg.norm(Wb['LeftLeg'][1] - Wb['LeftUpLeg'][1]) + np.linalg.norm(Wb['LeftFoot'][1] - Wb['LeftLeg'][1])
    Lt = np.linalg.norm(rt.P[18] - rt.P[17]) + np.linalg.norm(rt.P[19] - rt.P[18])
    s_leg = Lt / Ls
    n = int(round(DUR * FPS))
    ts = [JANELA_A + (JANELA_B - JANELA_A) * k / n for k in range(n + 1)]
    cs = np.array([(A.world(t)['LeftUpLeg'][1] + A.world(t)['RightUpLeg'][1]) / 2 for t in ts])
    cmean = cs.mean(0)
    zero = np.zeros(3)
    fr = np.array([rt.pose(A, t, Wb, s_leg, zero, 1.0, cmean) for t in ts])
    low = np.array([rt.foot_low(f) for f in fr])
    fr[:, :, 7] += (-low)[:, None]            # trava de chão quadro a quadro (altura vem da física do jogo)
    return DUR, fr, dict(s_leg=s_leg, quadros=n + 1, janela=(JANELA_A, JANELA_B))


def main():
    base_in, fbx, base_out = sys.argv[1:4]
    rt = Retarget(base_in)
    T, cj, info = jump_clip(rt, fbx)
    print(info)
    clips = [(l, d.copy()) for l, d in rt.base['clips']]
    clips[JUMP] = (T, cj)
    write_base(base_out, rt.base, clips)
    print('gravado', base_out, [(round(l, 3), d.shape[0]) for l, d in clips])


if __name__ == '__main__':
    main()
