#!/usr/bin/env python3
"""Prova que base.bin + peças == f_1.bin: clips idênticos byte a byte e malha pele-a-pele igual em todos os quadros.
Uso: python3 etapa1_verify.py <f_1.bin> <pasta cute novo>"""
import struct, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from etapa1_split import REC, read_cut1


def load_new(folder):
    b = open(os.path.join(folder, 'base.bin'), 'rb').read()
    assert b[:4] == b'CUT1'
    nv, ni, nb, nc = struct.unpack_from('<4i', b, 4)
    off = 20
    v = np.frombuffer(b, dtype=REC, count=nv, offset=off); off += nv * 44
    idx = np.frombuffer(b, dtype='<u2', count=ni, offset=off); off += ni * 2
    clips = b[off:]
    skins = [(v, idx)]
    keys = []
    for ln in open(os.path.join(folder, 'pieces.txt'), encoding='utf-8').read().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith('#') or ln.startswith('outfit='):
            continue
        slot, pid, fn, tex = ln.split('|')
        pb = open(os.path.join(folder, fn), 'rb').read()
        assert pb[:4] == b'CUP1'
        pnv, pni, flags = struct.unpack_from('<3i', pb, 4)
        o = 16
        pv = np.frombuffer(pb, dtype=REC, count=pnv, offset=o); o += pnv * 44
        pi = np.frombuffer(pb, dtype='<u2', count=pni, offset=o); o += pni * 2
        assert o == len(pb)
        skins.append((pv, pi)); keys.append(slot + '/' + pid)
    return nb, nc, clips, skins, keys


def skin_tris(v, idx, M):   # M: (nb,3,4) float32
    pos = v['pos'].astype(np.float32); nor = v['nor'].astype(np.float32)
    bw = v['bw'].astype(np.float32) / 255.0; bi = v['bi'].astype(np.int64)
    P = np.zeros_like(pos); N = np.zeros_like(nor)
    for k in range(4):
        m = M[bi[:, k]]
        w = bw[:, k:k + 1]
        P += w * (np.einsum('vij,vj->vi', m[:, :, :3], pos) + m[:, :, 3])
        N += w * np.einsum('vij,vj->vi', m[:, :, :3], nor)
    nl = np.linalg.norm(N, axis=1, keepdims=True); N = np.where(nl > 1e-9, N / np.maximum(nl, 1e-9), N)
    t = idx.reshape(-1, 3).astype(np.int64)
    return P[t], N[t], v['uv'][t], v['col'][t]


def main(old, newf):
    d = read_cut1(old)
    nb, nc, clips, skins, keys = load_new(newf)
    assert nb == d['nb'] and nc == d['nc']
    assert clips == d['clips_raw'], 'CLIPS DIFERENTES!'
    print('clips idênticos byte a byte:', len(clips), 'bytes')
    off = 0; worst = 0.0; frames = 0
    for c in range(nc):
        dur, nf = struct.unpack_from('<fi', clips, off); off += 8
        arr = np.frombuffer(clips, dtype='<f4', count=nf * nb * 12, offset=off).reshape(nf, nb, 3, 4); off += nf * nb * 48
        for f in range(nf):
            M = arr[f]
            Po, No, Uo, Co = skin_tris(d['v'], d['idx'], M)
            parts = [skin_tris(v, i, M) for v, i in skins]
            Pn = np.concatenate([p[0] for p in parts]); Nn = np.concatenate([p[1] for p in parts])
            Un = np.concatenate([p[2] for p in parts]); Cn = np.concatenate([p[3] for p in parts])
            assert Pn.shape == Po.shape, (Pn.shape, Po.shape)
            worst = max(worst, float(np.abs(Pn - Po).max()), float(np.abs(Nn - No).max()))
            assert (Un == Uo).all() and (Cn == Co).all()
            frames += 1
    print('quadros comparados:', frames, '| maior diferença (pos/normal):', worst)
    assert worst == 0.0
    print('IDÊNTICO')


main(sys.argv[1], sys.argv[2])
