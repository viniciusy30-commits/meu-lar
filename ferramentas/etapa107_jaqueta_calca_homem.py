#!/usr/bin/env python3
"""Etapa 107 - jaqueta com capuz e calça cargo: conserta o sombreado e cria a versão do corpo masculino do Sims 4.

Uso (na raiz do projeto):  python3 ferramentas/etapa107_jaqueta_calca_homem.py [--so-conferir]

Entrada : app/src/main/assets/cute/skate/hood_af5.cup e hcargo_af5.cup (versão original da etapa 105),
          corpos app/src/main/assets/cute/p_body_af5.bin e p_body_am5.bin.
Saída   : os mesmos hood_af5.cup / hcargo_af5.cup corrigidos e hood_am5.cup / hcargo_am5.cup (homem).

1) BUG VISUAL (manchas escuras/brancas na jaqueta e na calça)
   A malha original vem com DUAS cascas coladas (a de fora e uma de dentro, com normais virados para o corpo),
   separadas por ~0,3 mm. O teste de profundidade do celular não separa as duas, então em vários pontos a casca
   de dentro vencia e, com a normal virada para dentro, a luz a deixava escura (e a camisa branca da barra
   ficava toda "estilhaçada").
   Correção: todo vértice cuja normal aponta para o corpo (normal . direção que sai do corpo < -0,15) tem a normal
   invertida. As duas cascas passam a receber a mesma luz e a mesma textura, então a disputa de profundidade
   deixa de aparecer. Nenhum triângulo é apagado (apagar abria frestas serrilhadas na barra da jaqueta).
   Exceção: na CAMISA que aparece embaixo da jaqueta (bloco da textura com u>0,78 e v>0,70) as cópias de dentro
   são apagadas (só ali: sobravam riscos claros na barra e, lá, apagar não deixa fresta). Só a jaqueta tem camisa.
   Fora isso o .cup só muda nas normais; UVs, ossos e pesos continuam iguais.

2) HOMEM (corpo am5)
   O corpo masculino do Sims 4 usa o mesmo atlas UV do feminino. Para cada vértice do corpo feminino acha-se o ponto
   de mesmo UV no masculino (deslocamento feminino->masculino); o campo é suavizado (mediana + média de 16 vizinhos)
   e aplicado em cada vértice da roupa por média ponderada dos 12 vértices de corpo mais próximos. Depois, vértices
   da roupa que ficaram a menos de 0,5 cm da pele masculina são empurrados para fora pela normal do corpo.
   Ossos/pesos/UVs não mudam (mesmo esqueleto), então as animações e a textura/cores são as mesmas da versão feminina.
"""
import os, sys, struct
import numpy as np
from scipy.spatial import cKDTree

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
CUTE = os.path.join(ROOT, 'app/src/main/assets/cute')
SKATE = os.path.join(CUTE, 'skate')

DT = np.dtype([('p', '<f4', 3), ('n', '<f4', 3), ('uv', '<f4', 2), ('c', 'u1', 4), ('bi', 'u1', 4), ('bw', 'u1', 4)])


def read_cup(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'CUP1'
    nv, ni, fl = struct.unpack_from('<iii', d, 4)
    o = 16
    v = np.frombuffer(d, DT, nv, o).copy()
    o += nv * DT.itemsize
    idx = np.frombuffer(d, '<u2', ni, o).copy()
    o += ni * 2
    tail = d[o:]            # lista de triângulos escondidos (flags&1); estas peças não têm
    return dict(v=v, idx=idx, fl=fl, tail=tail)


def write_cup(path, m):
    v, idx = m['v'], m['idx'].astype('<u2')
    with open(path, 'wb') as f:
        f.write(b'CUP1' + struct.pack('<iii', len(v), len(idx), m['fl']))
        f.write(v.astype(DT).tobytes())
        f.write(idx.tobytes())
        f.write(m['tail'])


def flip_inner_normals(m, body_pos, thr=-0.15):
    P = m['v']['p'].astype(np.float64)
    N = m['v']['n'].astype(np.float64)
    _, i = cKDTree(body_pos).query(P)
    away = P - body_pos[i]
    away /= np.maximum(np.linalg.norm(away, axis=1), 1e-9)[:, None]
    flip = (N * away).sum(1) < thr
    N[flip] *= -1
    out = dict(m)
    out['v'] = m['v'].copy()
    out['v']['n'] = N.astype(np.float32)
    return out, int(flip.sum())


def inner_duplicates(m, body_pos, maxd=0.9, rad=2.5):
    """Triângulos virados para o corpo cuja projeção (ao longo da própria normal, até [maxd] cm de cada lado) cai
    dentro de um triângulo virado para fora: são a cópia de dentro de uma casca dupla."""
    tri = m['idx'].astype(int).reshape(-1, 3)
    P = m['v']['p'].astype(np.float64); N = m['v']['n'].astype(np.float64)
    _, i = cKDTree(body_pos).query(P)
    vout = (N * (P - body_pos[i])).sum(1) > 0
    tout = vout[tri].sum(1) >= 2
    c = P[tri].mean(1)
    gn = np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]])
    gn /= np.maximum(np.linalg.norm(gn, axis=1), 1e-12)[:, None]
    oi = np.where(tout)[0]; to = cKDTree(c[oi])
    inner = np.zeros(len(tri), bool)
    for t in np.where(~tout)[0]:
        cand = oi[to.query_ball_point(c[t], rad)]
        if len(cand) == 0:
            continue
        a, b, cc = P[tri[cand, 0]], P[tri[cand, 1]], P[tri[cand, 2]]
        n = gn[cand]
        dist = ((c[t] - a) * n).sum(1)
        q = c[t] - dist[:, None] * n
        v0, v1, v2 = b - a, cc - a, q - a
        d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1)
        d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
        den = d00 * d11 - d01 * d01 + 1e-18
        u = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
        if ((np.abs(dist) < maxd) & (u >= 0) & (w >= 0) & (u + w <= 1)).any():
            inner[t] = True
    return tri, inner


def remove_shirt_duplicates(m, body_pos):
    tri, inner = inner_duplicates(m, body_pos)
    cen = m['v']['uv'][tri].mean(1)
    rm = inner & (cen[:, 0] > 0.78) & (cen[:, 1] > 0.70)
    out = dict(m)
    out['idx'] = tri[~rm].reshape(-1).astype('<u2')
    return out, int(rm.sum())


def uv_correspondence(F, M):
    fp = F['v']['p'].astype(float); fuv = F['v']['uv'].astype(float)
    mp = M['v']['p'].astype(float); muv = M['v']['uv'].astype(float); mt = M['idx'].astype(int).reshape(-1, 3)
    tree = cKDTree(muv[mt].mean(1))
    out = np.zeros_like(fp); ok = np.zeros(len(fp), bool)
    for i in range(len(fp)):
        q = fuv[i]
        for t in tree.query(q, k=24)[1]:
            a, b, c = muv[mt[t]]
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-14:
                continue
            l1 = ((b[1] - c[1]) * (q[0] - c[0]) + (c[0] - b[0]) * (q[1] - c[1])) / d
            l2 = ((c[1] - a[1]) * (q[0] - c[0]) + (a[0] - c[0]) * (q[1] - c[1])) / d
            l3 = 1 - l1 - l2
            if min(l1, l2, l3) >= -1e-4:
                pt = l1 * mp[mt[t, 0]] + l2 * mp[mt[t, 1]] + l3 * mp[mt[t, 2]]
                if np.linalg.norm(pt - fp[i]) < 12:      # descarta ilha de UV errada
                    out[i] = pt; ok[i] = True; break
    return fp, out, ok


def smooth_field(fp, out, ok, k=16):
    D = out - fp
    idx = np.where(ok)[0]
    ii = cKDTree(fp[idx]).query(fp[idx], k=k)[1]
    Dm = np.median(D[idx][ii], axis=1)
    return fp[idx], Dm[ii].mean(1)


def transfer(G, pts, field, k=12):
    d, i = cKDTree(pts).query(G, k=k)
    w = 1 / (d ** 2 + 1.0); w /= w.sum(1, keepdims=True)
    return G + (field[i] * w[..., None]).sum(1)


def clearance(G, body, minc=0.0, rad=1.5, k=32):
    """Folga mínima da pele: vértices da roupa a menos de [minc] cm do corpo masculino sobem pela normal do corpo.
    A subida é COERENTE: cada vértice recebe a maior subida pedida pelos vizinhos num raio de [rad] cm, assim as
    camadas coladas da roupa (casca de fora, forro, bolsos) andam juntas e não trocam de ordem (empurrar cada vértice
    sozinho fazia o forro preto do bolso vazar para fora da perna)."""
    mp = body['v']['p'].astype(float); mn = body['v']['n'].astype(float)
    d, i = cKDTree(mp).query(G, k=3)
    s = np.einsum('nkj,nkj->nk', G[:, None, :] - mp[i], mn[i]).mean(1)
    n = mn[i].mean(1); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-9)[:, None]
    need = np.where((d[:, 0] < 4) & (s < minc), minc - s, 0.0)
    dd, ii = cKDTree(G).query(G, k=k)
    push = np.where(dd <= rad, need[ii], 0.0).max(1)
    return G + n * push[:, None]


def main():
    only_check = '--so-conferir' in sys.argv
    F = read_cup(os.path.join(CUTE, 'p_body_af5.bin'))
    M = read_cup(os.path.join(CUTE, 'p_body_am5.bin'))
    fp, out, ok = uv_correspondence(F, M)
    pts, field = smooth_field(fp, out, ok)
    print('corpo: %d/%d vertices com correspondencia, |deslocamento| mediano %.2f cm' % (ok.sum(), len(ok), np.median(np.linalg.norm(field, axis=1))))
    for name in ('hood', 'hcargo'):
        src = os.path.join(SKATE, name + '_af5.cup')
        m = read_cup(src)
        nrm = 0
        if name == 'hood':          # só a jaqueta tem a camisa por baixo (decide pelas normais ORIGINAIS, antes de inverter)
            m, nrm = remove_shirt_duplicates(m, F['v']['p'].astype(float))
        fixed, nflip = flip_inner_normals(m, F['v']['p'].astype(float))
        print('%s: %d vertices, %d normais invertidas, %d triangulos duplicados da camisa apagados' % (name, len(m['v']), nflip, nrm))
        male = dict(fixed)
        male['v'] = fixed['v'].copy()
        G = fixed['v']['p'].astype(float)
        G2 = clearance(transfer(G, pts, field), M, minc=0.0)
        male['v']['p'] = G2.astype(np.float32)
        print('  homem: deslocamento medio %.2f cm' % np.linalg.norm(G2 - G, axis=1).mean())
        if not only_check:
            write_cup(src, fixed)
            write_cup(os.path.join(SKATE, name + '_am5.cup'), male)
    print('pronto' if not only_check else 'so conferido (nada gravado)')


if __name__ == '__main__':
    main()
