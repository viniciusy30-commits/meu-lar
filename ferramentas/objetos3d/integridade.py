"""Verificação de integridade estrutural (Plano Mestre v4, Regra 1 — nada flutuando).

Para um GLB da biblioteca:
  1. separa a malha em PEÇAS (componentes conexos da malha, em cada nó), na pose pedida (peças móveis fechadas ou abertas);
  2. para cada par de peças próximas mede a menor distância entre as superfícies: pontos a cada 1,5 mm sobre as ARESTAS de
     uma peça contra os triângulos da outra (distância exata ponto-triângulo), nos dois sentidos. Entre dois triângulos a menor
     distância sempre cai numa aresta de um deles, então a medida nunca é menor que a real: aprovar com <= 2 mm é seguro;
  3. monta o grafo de contatos (vão <= 2 mm = encostado/encaixado) e exige que TODA peça chegue ao piso (y = 0) por uma
     cadeia de contatos; nada pode ficar abaixo do piso;
  4. devolve a tabela de apoios: cada peça, a peça em que se apoia (primeiro passo no caminho até o piso) e o vão medido.
Nós com extras.efeito (chama, água, luz) são efeitos visuais e ficam fora da conta.
Uso: python3 integridade.py arquivo.glb [...]
"""
import sys, os, json, math
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb_lib as G

GAP = 0.002          # vão máximo aceito (m)
STEP = 0.0015        # espaçamento da amostragem (m)


def _anim_local(an, u):
    c = min(max(u, 0.0), 1.0); e = c * c * (3 - 2 * c)
    v = an['min'] + (an['max'] - an['min']) * e
    ax = np.array(an['eixo'], float); M = np.eye(4)
    if an['tipo'] == 'dobradica':
        a = ax / (np.linalg.norm(ax) + 1e-12); x, y, z = a; cs, sn = math.cos(v), math.sin(v); C = 1 - cs
        M[:3, :3] = [[cs + x * x * C, x * y * C - z * sn, x * z * C + y * sn], [y * x * C + z * sn, cs + y * y * C, y * z * C - x * sn], [z * x * C - y * sn, z * y * C + x * sn, cs + z * z * C]]
    elif an['tipo'] == 'trilho':
        M[:3, 3] = ax * v
    elif an['tipo'] == 'escala':
        M[:3, :3] = np.diag([v if ax[k] > 0 else 1.0 for k in range(3)])
    return M


def world_mats(gj, states):
    W = {}
    def rec(i, M):
        nd = gj['nodes'][i]; L = np.eye(4)
        L[:3, :3] = G.quat_mat(nd.get('rotation', [0, 0, 0, 1])) @ np.diag(nd.get('scale', [1, 1, 1])); L[:3, 3] = nd.get('translation', [0, 0, 0])
        an = nd.get('extras', {}).get('anim')
        if an is not None: L = L @ _anim_local(an, states.get(i, 0.0))
        W[i] = M @ L
        for c in nd.get('children', []): rec(c, W[i])
    for r in gj['scenes'][gj.get('scene', 0)]['nodes']: rec(r, np.eye(4))
    return W


def pieces(path, states):
    gj, bin_ = G.read_glb(path); W = world_mats(gj, states)
    # nós de efeito (e os filhos deles) ficam de fora
    skip = set()
    def mark(i):
        skip.add(i)
        for c in gj['nodes'][i].get('children', []): mark(c)
    for i, nd in enumerate(gj['nodes']):
        if 'efeito' in nd.get('extras', {}): mark(i)
    out = []
    for i, nd in enumerate(gj['nodes']):
        if 'mesh' not in nd or i in skip: continue
        Ps = []; Ts = []; Ms = []; off = 0
        for pr in gj['meshes'][nd['mesh']]['primitives']:
            P = G.accessor(gj, bin_, pr['attributes']['POSITION']).astype(float)
            T = G.accessor(gj, bin_, pr['indices']).astype(int).reshape(-1, 3)
            P = (W[i][:3, :3] @ P.T).T + W[i][:3, 3]
            Ps.append(P); Ts.append(T + off); off += len(P)
            Ms += [gj['materials'][pr['material']]['name']] * len(T)
        P = np.vstack(Ps); T = np.vstack(Ts); Ms = np.array(Ms)
        # solda vértices na mesma posição e separa componentes conexos (union-find nos triângulos)
        key = np.round(P / 1e-6).astype(np.int64)
        _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
        TT = inv[T]; par = np.arange(inv.max() + 1)
        def find(a):
            r = a
            while par[r] != r: r = par[r]
            while par[a] != r: par[a], a = r, par[a]
            return r
        for a, b, c in TT:
            ra, rb, rc = find(a), find(b), find(c)
            par[rb] = ra; par[find(rc)] = ra
        roots = np.array([find(t[0]) for t in TT])
        for k, r in enumerate(np.unique(roots)):
            sel = roots == r; tri = P[T[sel]]
            out.append(dict(node=nd['name'], mat=str(Ms[sel][0]), tri=tri, lo=tri.reshape(-1, 3).min(0), hi=tri.reshape(-1, 3).max(0)))
    for k, p in enumerate(out):
        c = (p['lo'] + p['hi']) / 2
        p['nome'] = '%s/%s #%d (%.2f, %.2f, %.2f)' % (p['node'], p['mat'].replace('madeira_', '').replace('tecido_', ''), k, c[0], c[1], c[2])
    return out, gj


def _pt_tri(p, a, b, c):
    """distância exata de pontos p (M,3) a triângulos (K,3) -> (M,K). Ericson, Real-Time Collision Detection 5.1.5"""
    p = p[:, None, :]; a = a[None]; b = b[None]; c = c[None]
    ab = b - a; ac = c - a; ap = p - a
    d1 = (ab * ap).sum(-1); d2 = (ac * ap).sum(-1)
    bp = p - b; d3 = (ab * bp).sum(-1); d4 = (ac * bp).sum(-1)
    cp = p - c; d5 = (ab * cp).sum(-1); d6 = (ac * cp).sum(-1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = va + vb + vc; den = np.where(np.abs(den) < 1e-30, 1e-30, den)
    v = vb / den; w = vc / den
    q = a + ab * v[..., None] + ac * w[..., None]
    def seg(x, y):
        xy = y - x; t = ((p - x) * xy).sum(-1) / np.maximum((xy * xy).sum(-1), 1e-30)
        return x + xy * np.clip(t, 0, 1)[..., None]
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0); q = np.where(m[..., None], seg(b, c), q)
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0); q = np.where(m[..., None], seg(a, c), q)
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0); q = np.where(m[..., None], seg(a, b), q)
    m = (d6 >= 0) & (d5 <= d6); q = np.where(m[..., None], np.broadcast_to(c, q.shape), q)
    m = (d3 >= 0) & (d4 <= d3); q = np.where(m[..., None], np.broadcast_to(b, q.shape), q)
    m = (d1 <= 0) & (d2 <= 0); q = np.where(m[..., None], np.broadcast_to(a, q.shape), q)
    return np.linalg.norm(p - q, axis=-1)


def _in_box(tri, lo, hi):
    return np.all(tri.max(1) >= lo, 1) & np.all(tri.min(1) <= hi, 1)


def _edge_pts(tri, lo, hi, step):
    """pontos sobre as arestas dos triângulos (espaçamento step), só dentro da caixa"""
    t = tri[_in_box(tri, lo, hi)]
    if len(t) == 0: return np.zeros((0, 3))
    E = np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]])
    k = np.round(np.sort(E, axis=1).reshape(-1, 6) / 1e-6).astype(np.int64)
    _, u = np.unique(k, axis=0, return_index=True); E = E[u]
    # só a parte da aresta dentro da caixa (corte paramétrico)
    d = E[:, 1] - E[:, 0]; t0 = np.zeros(len(E)); t1 = np.ones(len(E))
    for ax in range(3):
        with np.errstate(divide='ignore', invalid='ignore'):
            ta = (lo[ax] - E[:, 0, ax]) / d[:, ax]; tb = (hi[ax] - E[:, 0, ax]) / d[:, ax]
        lo_t = np.where(np.abs(d[:, ax]) < 1e-12, np.where((E[:, 0, ax] >= lo[ax] - 1e-9) & (E[:, 0, ax] <= hi[ax] + 1e-9), -np.inf, np.inf), np.minimum(ta, tb))
        hi_t = np.where(np.abs(d[:, ax]) < 1e-12, np.where((E[:, 0, ax] >= lo[ax] - 1e-9) & (E[:, 0, ax] <= hi[ax] + 1e-9), np.inf, -np.inf), np.maximum(ta, tb))
        t0 = np.maximum(t0, lo_t); t1 = np.minimum(t1, hi_t)
    ok = t1 >= t0; E = E[ok]; t0 = t0[ok]; t1 = t1[ok]
    if len(E) == 0: return np.zeros((0, 3))
    L = np.linalg.norm(E[:, 1] - E[:, 0], axis=1) * (t1 - t0); n = np.minimum((L / step).astype(int) + 1, 2000)
    rep = np.repeat(np.arange(len(E)), n + 1)
    s = np.concatenate([np.linspace(0, 1, m + 1) for m in n])
    tt = t0[rep] + (t1 - t0)[rep] * s
    return E[rep, 0] + (E[rep, 1] - E[rep, 0]) * tt[:, None]


def _min_dist(pa, tb, lo, hi, gap):
    P = _edge_pts(pa, lo, hi, STEP)
    T = tb[_in_box(tb, lo - gap, hi + gap)]
    if len(P) == 0 or len(T) == 0: return 9.0
    # pré-filtro: ponto longe de todo vértice do outro lado por mais que (maior aresta + vão) não toca
    rmax = float(np.linalg.norm(T - T[:, [1, 2, 0]], axis=2).max()) + gap
    d0, _ = cKDTree(T.reshape(-1, 3)).query(P, k=1, distance_upper_bound=rmax); P = P[np.isfinite(d0)]
    best = 9.0
    for i in range(0, len(P), 384):
        for j in range(0, len(T), 384):
            d = float(_pt_tri(P[i:i + 384], T[j:j + 384, 0], T[j:j + 384, 1], T[j:j + 384, 2]).min())
            if d < best:
                best = d
                if best <= 2e-4: return best
    return best


def contacts(ps, gap=GAP):
    E = {}
    lo = np.array([p['lo'] for p in ps]) - gap; hi = np.array([p['hi'] for p in ps]) + gap
    order = np.argsort(lo[:, 0])
    for ii, a in enumerate(order):
        for b in order[ii + 1:]:
            if lo[b, 0] > hi[a, 0]: break
            if np.any(lo[a] > hi[b]) or np.any(lo[b] > hi[a]): continue
            rlo = np.maximum(lo[a], lo[b]); rhi = np.minimum(hi[a], hi[b])
            d = _min_dist(ps[a]['tri'], ps[b]['tri'], rlo, rhi, gap)
            if d > gap: d = min(d, _min_dist(ps[b]['tri'], ps[a]['tri'], rlo, rhi, gap))
            if d <= gap: E[(a, b)] = E[(b, a)] = d
    return E


def check(path, states, gap=GAP):
    ps, gj = pieces(path, states)
    E = contacts(ps, gap)
    lomin = min(p['lo'][1] for p in ps)
    ground = [k for k, p in enumerate(ps) if p['lo'][1] <= 0.0005]
    nb = {k: [] for k in range(len(ps))}
    for (a, b), d in E.items(): nb[a].append((b, d))
    # BFS a partir do piso: apoio de cada peça = vizinho mais perto do piso
    via = {k: ('piso', 0.0) for k in ground}; fila = list(ground); dist = {k: 0 for k in ground}
    while fila:
        nx = []
        for a in fila:
            for b, d in nb[a]:
                if b not in via:
                    via[b] = (a, d); dist[b] = dist[a] + 1; nx.append(b)
        fila = nx
    soltas = [k for k in range(len(ps)) if k not in via]
    tabela = []
    for k, p in enumerate(ps):
        if k in via:
            a, d = via[k]
            tabela.append(dict(peca=p['nome'], apoio='piso (y = 0)' if a == 'piso' else ps[a]['nome'], vao_mm=round(d * 1000, 2)))
        else:
            # vão até a peça mais perto (para o relatório da falha)
            best = (None, 9.0)
            for j, q in enumerate(ps):
                if j == k: continue
                dd = np.maximum(0, np.maximum(q['lo'] - p['hi'], p['lo'] - q['hi']))
                dd = float(np.linalg.norm(dd))
                if dd < best[1]: best = (q['nome'], dd)
            tabela.append(dict(peca=p['nome'], apoio='NENHUM — FLUTUANDO', vao_mm=None, mais_perto=best[0], dist_caixa_mm=round(best[1] * 1000, 1)))
    ok = not soltas and lomin >= -0.0005
    return dict(ok=ok, pecas=len(ps), soltas=[ps[k]['nome'] for k in soltas], y_min=round(float(lomin), 5), tabela=tabela)


def anim_nodes(path):
    gj, _ = G.read_glb(path)
    return {i: nd['name'] for i, nd in enumerate(gj['nodes']) if 'anim' in nd.get('extras', {}) and nd['extras']['anim']['tipo'] != 'escala'}


def full(path):
    """pose fechada + tudo aberto (as gavetas internas abrem junto com as portas)"""
    an = anim_nodes(path)
    res = dict(fechado=check(path, {}))
    if an: res['aberto'] = check(path, {i: 1.0 for i in an})
    res['ok'] = all(r['ok'] for r in res.values() if isinstance(r, dict))
    return res


if __name__ == '__main__':
    for f in sys.argv[1:]:
        r = full(f)
        print('%-28s %s' % (os.path.basename(f), 'APROVADO' if r['ok'] else 'REPROVADO'))
        for pose in ('fechado', 'aberto'):
            if pose not in r: continue
            q = r[pose]
            print('   %-8s peças=%d soltas=%d y_min=%.4f' % (pose, q['pecas'], len(q['soltas']), q['y_min']))
            for t in q['tabela']:
                if t['vao_mm'] is None: print('      SOLTA:', t['peca'], '| mais perto:', t['mais_perto'], t['dist_caixa_mm'], 'mm')
