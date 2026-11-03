#!/usr/bin/env python3
"""Etapa 51: tira TODAS as animacoes. Cada corpo do Sims 3 fica na pose original da malha (A-pose do jogo), sem clipes, sem ajuste de bracos/maos/cabeca.
Uso: python3 etapa51_sem_animacao.py <assets/cute>
 - clips_<grupo>.bin (af am tf tm ef em cu pu): 1 clipe de 1 quadro = so a escala cm->m (K), pes exatamente no chao
 - base.bin e f_1.bin (restos do boneco antigo/Mixamo): clipes trocados por 1 clipe parado
O formato dos arquivos e' o mesmo; o app nao precisa mudar."""
import sys, struct, numpy as np
K = 0.0082
CU = sys.argv[1].rstrip('/') + '/'
NB = 55
PDT = np.dtype([('pos', '<f4', 3), ('nor', '<f4', 3), ('uv', '<f4', 2), ('col', 'u1', 4), ('bi', 'u1', 4), ('bw', 'u1', 4)])

def static_clip(ty_cm=0.0):
    m = np.zeros((NB, 12), '<f4')
    m[:, 0] = K; m[:, 5] = K; m[:, 10] = K; m[:, 7] = -ty_cm * K
    return struct.pack('<fi', 1.0, 1) + m.tobytes()

for g in ['af', 'am', 'tf', 'tm', 'ef', 'em', 'cu', 'pu']:
    b = open(CU + 'p_body_%s1.bin' % g, 'rb').read()
    nv = struct.unpack('<i', b[4:8])[0]
    miny = np.frombuffer(b, PDT, nv, 16)['pos'][:, 1].min()
    open(CU + 'clips_%s.bin' % g, 'wb').write(b'CLP1' + struct.pack('<2i', NB, 1) + static_clip(miny))
    print('clips_%s.bin: parado, sola em y=%.3f cm' % (g, miny))

for name in ['base.bin', 'f_1.bin']:
    b = open(CU + name, 'rb').read()
    nv, ni, nb, nc = struct.unpack('<4i', b[4:20])
    start = 20 + nv * PDT.itemsize + ni * 2
    o = start
    for _ in range(nc):
        nf = struct.unpack('<i', b[o + 4:o + 8])[0]; o += 8 + nf * nb * 48
    assert o == len(b) and nb == NB, (name, o, len(b), nb)
    open(CU + name, 'wb').write(b[:4] + struct.pack('<4i', nv, ni, nb, 1) + b[20:start] + static_clip(0.0))
    print(name, 'clipes', nc, '->', 1)
