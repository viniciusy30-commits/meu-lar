"""Etapa 11 - leitura/escrita do base.bin (CUT1) e reconstrução da pose de referência do esqueleto de 55 ossos."""
import struct, numpy as np
K = 0.0082
NB = 55
REC = np.dtype([('pos', '<f4', 3), ('nor', '<f4', 3), ('uv', '<f4', 2), ('col', 'u1', 4), ('bi', 'u1', 4), ('bw', 'u1', 4)])

# hierarquia (pai de cada osso), derivada dos nomes do esqueleto (ver clothes_lib.bone_index)
def build_parents():
    gp = [-1] * NB
    for i in range(1, 6): gp[i] = i - 1          # pelvis -> spine_01..05
    gp[6] = 5; gp[7] = 6; gp[8] = 7              # neck_01, neck_02, head
    for c0 in (9, 13):                            # braços L/R: clavicle, upperarm, lowerarm, hand
        gp[c0] = 5; gp[c0 + 1] = c0; gp[c0 + 2] = c0 + 1; gp[c0 + 3] = c0 + 2
    for c0 in (17, 21):                           # pernas L/R: thigh, calf, foot, ball
        gp[c0] = 0; gp[c0 + 1] = c0; gp[c0 + 2] = c0 + 1; gp[c0 + 3] = c0 + 2
    for side, hand in ((0, 12), (15, 16)):        # dedos: 5 por mão, 3 ossos cada
        base = 25 + side
        for f in range(5):
            b = base + f * 3
            gp[b] = hand; gp[b + 1] = b; gp[b + 2] = b + 1
    return gp
GP = build_parents()

NAMES = ['pelvis', 'spine_01', 'spine_02', 'spine_03', 'spine_04', 'spine_05', 'neck_01', 'neck_02', 'head',
         'clavicle_l', 'upperarm_l', 'lowerarm_l', 'hand_l', 'clavicle_r', 'upperarm_r', 'lowerarm_r', 'hand_r',
         'thigh_l', 'calf_l', 'foot_l', 'ball_l', 'thigh_r', 'calf_r', 'foot_r', 'ball_r']
FN = ['index', 'middle', 'ring', 'pinky', 'thumb']
for s in ('l', 'r'):
    for f in FN:
        for k in (1, 2, 3):
            NAMES.append('%s_0%d_%s' % (f, k, s))
# ordem dos dedos no vetor de 55: L = 25..39 (index,middle,ring,pinky,thumb), R = 40..54
assert len(NAMES) == 55

def read_base(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'CUT1'
    nv, ni, nb, nc = struct.unpack_from('<4i', b, 4)
    o = 20
    ver = np.frombuffer(b, dtype=REC, count=nv, offset=o); o += nv * REC.itemsize
    idx = np.frombuffer(b, dtype='<u2', count=ni, offset=o); o += ni * 2
    clips = []
    for c in range(nc):
        ln, nf = struct.unpack_from('<fi', b, o); o += 8
        d = np.frombuffer(b, dtype='<f4', count=nf * nb * 12, offset=o).reshape(nf, nb, 12); o += nf * nb * 12 * 4
        clips.append((ln, d.copy()))
    assert o == len(b), (o, len(b))
    return dict(raw=b, nv=nv, ni=ni, nb=nb, ver=ver, idx=idx, clips=clips, head_end=20 + nv * REC.itemsize + ni * 2)

def write_base(path, base, clips):
    """Reescreve o base.bin com a lista de clips [(duração, array(nf,55,12))]; vértices e índices iguais."""
    b = base['raw']
    out = bytearray(b[:4]) + struct.pack('<4i', base['nv'], base['ni'], base['nb'], len(clips)) + b[20:base['head_end']]
    for ln, d in clips:
        d = np.ascontiguousarray(d, dtype='<f4')
        out += struct.pack('<fi', float(ln), d.shape[0]) + d.tobytes()
    open(path, 'wb').write(bytes(out))

def recover_bind(clips, ver):
    """Posições dos joints na pose de referência, a partir das matrizes de pele dos clips.
    Para cada osso filho c com pai q: S_q(t)*[p_c;1] = S_c(t)*[p_c;1] em todo quadro t (elo rígido)."""
    P = np.zeros((NB, 3))
    for c in range(1, NB):
        q = GP[c]
        if q < 0: continue
        A = []
        for ln, d in clips:
            D = (d[:, q, :] - d[:, c, :]).reshape(-1, 3, 4).astype(np.float64)   # (nf,3,4)
            A.append(D)
        A = np.concatenate(A)                                # (N,3,4)
        M = A[:, :, :3].reshape(-1, 3); r = -A[:, :, 3].reshape(-1)
        sol, res, rk, sv = np.linalg.lstsq(M, r, rcond=None)
        P[c] = sol
    # raiz: ponto médio das coxas (a posição exata da raiz quase não afeta a pele; ver notas)
    P[0] = (P[17] + P[21]) / 2
    return P

if __name__ == '__main__':
    import sys
    bs = read_base(sys.argv[1])
    print('nv', bs['nv'], 'ni', bs['ni'], 'nb', bs['nb'], 'clips', [(round(l, 3), d.shape) for l, d in bs['clips']])
    P = recover_bind(bs['clips'], bs['ver'])
    np.set_printoptions(precision=2, suppress=True)
    for i in range(NB): print(i, NAMES[i], GP[i], P[i])
    v = bs['ver']['pos']; print('bbox', v.min(0), v.max(0))
