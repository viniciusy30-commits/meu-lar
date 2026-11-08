"""Etapa 118: clipes da piscina (Run_To_Dive, Swimming, Swimming_To_Edge, Treading_Water do Mixamo) para o esqueleto de 55 ossos do TS4.
Uso: python3 etapa118_piscina_clipes.py <pasta cute entrada> <pasta com os 4 .fbx> <pasta cute saida>
Acrescenta 4 clipes (indices 11..14) a clips_am5.bin e clips_af5.bin (os 11 primeiros ficam iguais; roda de novo sem duplicar).
Referencias verticais (o jogo soma a altura absoluta da agua/borda):
  11 RUN_DIVE   : chao = y 0 (borda da piscina); SEM deslocamento horizontal (o jogo move o personagem pela tabela de avanco impressa)
  12 SWIM       : superficie da agua = y 0; laco no lugar
  13 SWIM_EDGE  : borda (maos no chao do deck) = y 0; sem deslocamento horizontal (tabela de avanco impressa); termina pendurado na borda
  14 TREAD      : superficie da agua = y 0; laco no lugar
Imprime as constantes (em metros do jogo, altura 1.0) para o Kotlin."""
import sys, os, struct
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etapa11_base import GP, NB, K
from etapa11_fbxanim import Anim
from etapa11_retarget import Retarget, ortho

def read_clips(path):
    b = open(path, 'rb').read(); assert b[:4] == b'CLP1'
    nb, nc = struct.unpack('<2i', b[4:12]); o = 12; out = []
    for _ in range(nc):
        ln, nf = struct.unpack('<fi', b[o:o + 8]); o += 8
        d = np.frombuffer(b, '<f4', nf * nb * 12, o).reshape(nf, nb, 12).copy(); o += nf * nb * 12 * 4; out.append((ln, d))
    assert o == len(b); return out
def write_clips(path, clips):
    out = bytearray(b'CLP1' + struct.pack('<2i', 55, len(clips)))
    for ln, d in clips:
        d = np.ascontiguousarray(d, dtype='<f4'); out += struct.pack('<fi', float(ln), d.shape[0]) + d.tobytes()
    open(path, 'wb').write(bytes(out))
def recover_P(clips):
    P = np.zeros((NB, 3))
    for c in range(1, NB):
        q = GP[c]
        A = np.concatenate([(d[:, q, :] - d[:, c, :]).reshape(-1, 3, 4).astype(float) for ln, d in clips])
        P[c] = np.linalg.lstsq(A[:, :, :3].reshape(-1, 3), -A[:, :, 3].reshape(-1), rcond=None)[0]
    P[0] = (P[17] + P[21]) / 2
    return P

def make_rt(clips11):
    rt = Retarget.__new__(Retarget)
    P = recover_P(clips11); P[20][0] = P[19][0]; P[24][0] = P[23][0]
    rt.P = P
    idle = clips11[0][1][0].astype(np.float64)
    rt.Didle = [ortho(idle[i].reshape(3, 4)[:, :3] / K) for i in range(NB)]
    return rt

def joints(rt, S):
    S = S.reshape(NB, 3, 4)
    return (np.einsum('bij,bj->bi', S[:, :, :3], rt.P) + S[:, :, 3]) / K      # cm do jogo

def build(rt, path, mode, sub, yref_mix):
    """mode: 'once' (deslocamento relativo ao 1o quadro) ou 'loop' (centrado). yref_mix: y (cm Mixamo) que vira y=0, ou funcao(A)."""
    A = Anim(path); Wb = A.world(0, animated=False)
    Ls = np.linalg.norm(Wb['LeftLeg'][1] - Wb['LeftUpLeg'][1]) + np.linalg.norm(Wb['LeftFoot'][1] - Wb['LeftLeg'][1])
    Lt = np.linalg.norm(rt.P[18] - rt.P[17]) + np.linalg.norm(rt.P[19] - rt.P[18])
    s = Lt / Ls
    T = A.t1 - A.t0; n = int(round(T * 30)); nfr = n * sub
    hipc = lambda t: (A.world(t)['LeftUpLeg'][1] + A.world(t)['RightUpLeg'][1]) / 2
    c0 = hipc(A.t0)
    if mode == 'once': cmean = c0
    else: cmean = np.mean([hipc(A.t0 + T * k / n) for k in range(n)], 0)
    fr = np.array([rt.pose(A, A.t0 + T * (k / nfr), Wb, s, np.zeros(3), T, cmean) for k in range(nfr + 1)])
    if mode == 'loop': fr[-1] = fr[0]
    return A, T, fr, s

def main():
    cin, fbx, cout = sys.argv[1:4]; os.makedirs(cout, exist_ok=True)
    for g in ('am5', 'af5'):
        clips = read_clips(f'{cin}/clips_{g}.bin')[:11]
        rt = make_rt(clips)
        specs = [('Run_To_Dive', 'once', 2), ('Swimming', 'loop', 2), ('Swimming_To_Edge', 'once', 2), ('Treading_Water', 'loop', 2)]
        mode_of = {n: m for n, m, _ in specs}
        built = {}
        for nm, mode, sub in specs:
            built[nm] = build(rt, f'{fbx}/{nm}.fbx', mode, sub, None)
        new = []
        info = {}
        for nm, mode, sub in specs:
            A, T, fr, s = built[nm]
            ty = [3, 7, 11]
            def ycm(f, b=None):   # y (cm do jogo) das juntas do quadro f
                J = joints(rt, fr[f]); return J
            if nm == 'Run_To_Dive':
                # pe no chao nos primeiros quadros: a bola do pe mais baixa fica na altura de repouso
                lows = [min(joints(rt, fr[f])[20][1], joints(rt, fr[f])[24][1]) for f in range(0, 12)]
                dy = rt.P[20][1] - min(lows)
            elif nm == 'Swimming':
                dy = -0.80 * 100 * s
            elif nm == 'Treading_Water':
                dy = -1.30 * 100 * s
            else:   # Swimming_To_Edge: maos do ultimo quadro = chao do deck
                J = joints(rt, fr[-1]); hy = (J[12][1] + J[16][1]) / 2
                dy = -hy
            fr = fr.copy(); fr[:, :, 7] += dy * K
            fwd = None
            if mode_of[nm] == 'once':
                # tira o deslocamento horizontal do quadril (o jogo move o jogador); guarda o avanco para frente por quadro
                J0 = [joints(rt, fr[f])[0] for f in range(len(fr))]
                fwd = np.array([(j[2] - J0[0][2]) * K for j in J0])      # m do jogo (altura 1,0)
                for f in range(len(fr)):
                    fr[f, :, 3] -= (J0[f][0] - J0[0][0]) * K
                    fr[f, :, 11] -= (J0[f][2] - J0[0][2]) * K
            new.append((T, fr))
            J = [joints(rt, fr[f]) for f in range(len(fr))]
            hips0 = J[0][0]; hipsE = J[-1][0]
            nm_info = dict(T=T, nf=len(fr), s=s, dy_cm=dy)
            nm_info['disp_fwd_m'] = (hipsE[2] - hips0[2]) * K
            nm_info['hips0_m'] = (hips0 * 0.01).round(3); nm_info['hipsE_m'] = (hipsE * 0.01).round(3)
            nm_info['headE_m'] = (J[-1][8] * 0.01).round(3)
            nm_info['handsE_m'] = (((J[-1][12] + J[-1][16]) / 2) * 0.01).round(3)
            if fwd is not None:
                step = 0.15; ts = np.arange(0, T + 1e-6, step)
                nm_info['avanco_cada_0.15s'] = [round(float(np.interp(t, np.linspace(0, T, len(fwd)), fwd)), 3) for t in ts]
            info[nm] = nm_info
        out = clips + new
        write_clips(f'{cout}/clips_{g}.bin', out)
        print(g, [(round(l, 2), d.shape[0]) for l, d in out])
        for k, v in info.items(): print(' ', k, v)
        np.save(f'/home/claude/work/new_{g}.npy', np.array([c[1] for c in new], dtype=object), allow_pickle=True)
if __name__ == '__main__': main()
