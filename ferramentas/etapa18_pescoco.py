"""Etapa 18 - conserta o PESCOÇO que "descolava" ao andar/correr.

Causa: o pescoço do base.bin é feito de 3 malhas soltas (tronco, faixa do pescoço, cabeça) que se encontram em anéis de
vértices na mesma posição, mas cada malha tinha pesos de osso diferentes (tronco: spine_04, cabeça: head). Quando a
cabeça gira, os dois lados do anel se afastam (até 1,4 cm andando e 7,3 cm correndo) e aparece uma fresta.

Correção (só pesos de osso; posições, UVs, normais e animações não mudam):
 1. SOLDA: vértices na mesma posição passam a ter exatamente os mesmos pesos (valem os do tronco > pescoço > cabeça).
 2. DEGRADÊ: na coluna do pescoço (y 140..157) os pesos viram uma função só da posição, passando devagar por
    spine_05 -> neck_01 -> neck_02 -> head (o osso neck_02 quase não era usado). Peças que abraçam o pescoço
    (blusas/gola, vestidos, barbas) usam a MESMA função, então acompanham a pele.

Uso:  python3 etapa18_pescoco.py <pasta cute entrada> <pasta cute saída>
"""
import sys, os, struct, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import scipy.sparse as sp, scipy.sparse.csgraph as cg
from scipy.spatial import cKDTree
from etapa11_base import REC, read_base

CHAIN_B = [5, 6, 7, 8]                 # spine_05, neck_01, neck_02, head
CHAIN_Y = [141.0, 148.0, 152.5, 157.0]  # altura (unidades do modelo) em que cada osso "manda"
SLOTS = ('top', 'overall', 'beard')     # peças que abraçam o pescoço


def sm(x, e0, e1):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def chain_weights(y):
    """(n,4) pesos sobre CHAIN_B, interpolação linear por altura (suavizada)."""
    y = np.clip(y, CHAIN_Y[0], CHAIN_Y[-1])
    W = np.zeros((len(y), 4))
    for k in range(3):
        y0, y1 = CHAIN_Y[k], CHAIN_Y[k + 1]
        m = (y >= y0) & (y <= y1)
        u = sm(y[m], y0, y1)            # suaviza a passagem entre ossos vizinhos
        W[m, k] = 1 - u; W[m, k + 1] = u
    return W


def dense(v):
    """pesos (n,55) a partir de bi/bw."""
    n = len(v); D = np.zeros((n, 55))
    for k in range(4):
        np.add.at(D, (np.arange(n), v['bi'][:, k].astype(int)), v['bw'][:, k] / 255.0)
    return D


def pack(D):
    """(n,55) -> bi (n,4) uint8, bw (n,4) uint8 somando 255 (4 maiores pesos)."""
    n = len(D)
    idx = np.argsort(-D, axis=1)[:, :4]
    w = np.take_along_axis(D, idx, 1)
    w = w / np.maximum(w.sum(1, keepdims=True), 1e-9)
    q = np.floor(w * 255 + 0.5).astype(int)
    q[np.arange(n), 0] += 255 - q.sum(1)        # sobra/falta vai pro maior
    idx = np.where(q > 0, idx, 0)
    return idx.astype(np.uint8), q.astype(np.uint8)


def blend_factor(pos):
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    return sm(y, 140.0, 144.0) * (1 - sm(np.abs(x), 7.5, 10.5)) * (1 - sm(z, 5.0, 8.0))


def apply_function(v, mask_extra=None):
    pos = v['pos'].astype(float)
    a = blend_factor(pos)
    if mask_extra is not None: a = a * mask_extra
    sel = np.where(a > 1e-4)[0]
    if len(sel) == 0: return v, 0
    D = dense(v)
    F = np.zeros((len(sel), 55))
    cw = chain_weights(pos[sel, 1])
    for k, b in enumerate(CHAIN_B): F[:, b] = cw[:, k]
    D[sel] = a[sel, None] * F + (1 - a[sel, None]) * D[sel]
    bi, bw = pack(D[sel])
    v = v.copy(); v['bi'][sel] = bi; v['bw'][sel] = bw
    return v, len(sel)


def weld_base(v, idx):
    """vértices coincidentes ganham os mesmos pesos (prioridade tronco > pescoço > cabeça)."""
    n = len(v); pos = v['pos'].astype(float)
    tri = idx.reshape(-1, 3).astype(int)
    r = np.concatenate([tri[:, 0], tri[:, 1]]); c = np.concatenate([tri[:, 1], tri[:, 2]])
    nc, lab = cg.connected_components(sp.coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    # classifica cada componente: tronco = osso dominante 4 e y máx ~147; pescoço = dominante 6; cabeça = dominante 8
    dom = np.zeros(nc, int); ymax = np.zeros(nc); cnt = np.zeros(nc, int)
    for k in range(nc):
        m = lab == k; cnt[k] = m.sum(); ymax[k] = pos[m, 1].max()
        b = v['bi'][m][np.arange(m.sum()), v['bw'][m].argmax(1)]
        dom[k] = np.bincount(b, minlength=55).argmax()
    prio = np.where(dom == 4, 0, np.where(dom == 6, 1, 2))
    near = (pos[:, 1] > 138) & (pos[:, 1] < 160)
    tr = cKDTree(pos)
    pairs = np.array(sorted(tr.query_pairs(0.02)))
    pairs = pairs[near[pairs[:, 0]]] if len(pairs) else pairs
    n2 = sp.coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n))
    ng, gl = cg.connected_components(n2, directed=False)
    D = dense(v); out = D.copy(); fixed = 0
    for g in np.unique(gl[np.unique(pairs)]):
        mem = np.where(gl == g)[0]
        if len(mem) < 2: continue
        best = mem[np.argmin(prio[lab[mem]] * 1000 + mem)]
        if np.abs(D[mem] - D[best]).max() > 1e-6:
            out[mem] = D[best]; fixed += 1
    bi, bw = pack(out)
    v = v.copy(); v['bi'] = bi; v['bw'] = bw
    return v, fixed


def main(src, dst):
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(src):
        p = os.path.join(src, f)
        if os.path.isfile(p) and not os.path.exists(os.path.join(dst, f)): shutil.copy(p, os.path.join(dst, f))
    bs = read_base(os.path.join(src, 'base.bin'))
    v, fixed = weld_base(bs['ver'], bs['idx'])
    print('soldadura: %d grupos de vértices coincidentes acertados' % fixed)
    v, n = apply_function(v)
    print('base.bin: %d vértices com degradê do pescoço' % n)
    raw = bytearray(bs['raw'])
    raw[20:20 + bs['nv'] * REC.itemsize] = np.ascontiguousarray(v, dtype=REC).tobytes()
    open(os.path.join(dst, 'base.bin'), 'wb').write(bytes(raw))
    tot = 0
    for ln in open(os.path.join(src, 'pieces.txt'), encoding='utf-8').read().splitlines():
        ln = ln.strip()
        if not ln or ln[0] == '#' or ln.startswith('outfit='): continue
        slot, pid, fn, tex = ln.split('|')
        if slot not in SLOTS: continue
        pb = bytearray(open(os.path.join(src, fn), 'rb').read())
        assert pb[:4] == b'CUP1'
        nv, ni, fl = struct.unpack_from('<3i', pb, 4)
        pv = np.frombuffer(bytes(pb), dtype=REC, count=nv, offset=16).copy()
        pv2, n = apply_function(pv)
        if n:
            pb[16:16 + nv * REC.itemsize] = np.ascontiguousarray(pv2, dtype=REC).tobytes()
            open(os.path.join(dst, fn), 'wb').write(bytes(pb)); tot += n
    # peças que não estão no manifesto (ex.: p_top_bikini.bin, p_beard_*) também
    for fn in sorted(os.listdir(src)):
        if not fn.startswith('p_') or not fn.endswith('.bin'): continue
        slot = fn[2:].split('_')[0]
        if slot not in SLOTS: continue
        pb = bytearray(open(os.path.join(dst, fn), 'rb').read())
        # já processado acima? (compara com a origem)
        if bytes(pb) != open(os.path.join(src, fn), 'rb').read(): continue
        nv, ni, fl = struct.unpack_from('<3i', pb, 4)
        pv = np.frombuffer(bytes(pb), dtype=REC, count=nv, offset=16).copy()
        pv2, n = apply_function(pv)
        if n:
            pb[16:16 + nv * REC.itemsize] = np.ascontiguousarray(pv2, dtype=REC).tobytes()
            open(os.path.join(dst, fn), 'wb').write(bytes(pb)); tot += n
    print('peças (top/overall/beard): %d vértices com o mesmo degradê' % tot)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
