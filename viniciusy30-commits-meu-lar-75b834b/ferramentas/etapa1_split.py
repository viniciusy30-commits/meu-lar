#!/usr/bin/env python3
"""
Etapa 1 do Meu Lar: divide o personagem "assado" (cute/f_1.bin, formato CUT1) em
  - cute/base.bin  : corpo + boca + cabeça + olhos + os 3 clips (Idle/Walk/Jump copiados byte a byte)  [CUT1]
  - cute/p_*.bin   : uma peça por arquivo (só malha/pesos/UV para o mesmo esqueleto de 55 ossos)       [CUP1]
  - cute/pieces.txt: manifesto das peças e roupa padrão

Uso:  python3 etapa1_split.py <f_1.bin> <pasta_saida>        (gera e verifica)
Formato CUP1 (little-endian): "CUP1" | nv | ni | flags(int32, 0) | nv * 44 bytes de vértice | ni * uint16
Vértice (44 bytes, igual ao CUT1): pos(3f) normal(3f) uv(2f) cor(4 bytes) boneIdx(4 bytes) pesos(4 bytes).
Os clips NÃO são alterados: a matriz de cada osso é a mesma, então as peças seguem Idle/Walk/Jump aprovados.
"""
import struct, sys, os
import numpy as np

REC = np.dtype([('pos', '<f4', 3), ('nor', '<f4', 3), ('uv', '<f4', 2),
                ('col', 'u1', 4), ('bi', 'u1', 4), ('bw', 'u1', 4)])
assert REC.itemsize == 44


def read_cut1(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'CUT1'
    nv, ni, nb, nc = struct.unpack_from('<4i', b, 4)
    off = 20
    v = np.frombuffer(b, dtype=REC, count=nv, offset=off).copy(); off += nv * 44
    idx = np.frombuffer(b, dtype='<u2', count=ni, offset=off).copy(); off += ni * 2
    clips_raw = b[off:]            # todos os clips, bytes exatamente como estão
    return dict(nv=nv, ni=ni, nb=nb, nc=nc, v=v, idx=idx, clips_raw=clips_raw)


# Blocos de vértices (intervalos [a,b) do f_1.bin original). Cada bloco é uma malha inteira do pack.
# 5204..6008 são ~800 vértices órfãos (nenhum triângulo usa): descartados, não aparecem em nada.
BASE = [(0, 5204), (6008, 9591)]            # corpo, boca, cabeça, olhos
PIECES = [                                   # (slot, id, intervalos) na ordem de desenho original
    ('top',       'Sweater',    [(9591, 11126)]),
    ('bottom',    'Skirt',      [(11126, 11864)]),
    ('feet',      'Sandals',    [(11864, 12746)]),
    ('hairBack',  'Flare',      [(12746, 14024)]),   # inclui 2 tufos pequenos que usam a textura do cabelo
    ('hairFront', 'LongSweeps', [(14024, 14691)]),
]


def extract(d, ranges):
    """Vértices dos intervalos (ordem original) + triângulos que os usam (ordem original, índices locais)."""
    sel = np.concatenate([np.arange(a, b) for a, b in ranges])
    remap = -np.ones(d['nv'], dtype=np.int64)
    remap[sel] = np.arange(len(sel))
    tri = d['idx'].reshape(-1, 3).astype(np.int64)
    inside = remap[tri] >= 0
    full = inside.all(1)
    part = inside.any(1) & ~full
    assert not part.any(), 'triângulo atravessa blocos'
    T = remap[tri[full]]
    return d['v'][sel], T.astype(np.uint16).reshape(-1), np.where(full)[0]


def write_cup1(path, v, idx):
    with open(path, 'wb') as f:
        f.write(b'CUP1' + struct.pack('<3i', len(v), len(idx), 0))
        f.write(v.tobytes())
        f.write(idx.astype('<u2').tobytes())


def main(src, outdir):
    os.makedirs(outdir, exist_ok=True)
    d = read_cut1(src)
    bv, bidx, btri = extract(d, BASE)
    with open(os.path.join(outdir, 'base.bin'), 'wb') as f:
        f.write(b'CUT1' + struct.pack('<4i', len(bv), len(bidx), d['nb'], d['nc']))
        f.write(bv.tobytes()); f.write(bidx.astype('<u2').tobytes()); f.write(d['clips_raw'])
    used = [btri]
    lines = ['# slot|id|arquivo|textura   (ordem = ordem de desenho)']
    for slot, pid, rng in PIECES:
        v, idx, tri = extract(d, rng)
        fn = 'p_%s_%s.bin' % (slot.lower(), pid.lower())
        write_cup1(os.path.join(outdir, fn), v, idx)
        used.append(tri)
        lines.append('%s|%s|%s|textures.png' % (slot, pid, fn))
    lines.append('# roupa padrão (a Mary): chaves slot/id')
    lines.append('outfit=' + ','.join('%s/%s' % (s, i) for s, i, _ in PIECES))
    open(os.path.join(outdir, 'pieces.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    allt = np.concatenate(used)
    assert len(allt) == len(set(allt.tolist())) == d['ni'] // 3, 'triângulos perdidos/duplicados'
    print('ok: base %d vértices %d tris; peças:' % (len(bv), len(bidx) // 3),
          [(s, i) for s, i, _ in PIECES])


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
