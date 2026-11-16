"""Cidade 6: exporta a arvore da Cidade 2 (alamo do city2.glb: tronco + folhas recortadas) para o jogo.
Saida: assets/hds/c6_tree.bin (malha) e assets/hds/c6tex/arvore_folhas.png / arvore_casca.png (texturas do proprio city2.glb).
Formato c6_tree.bin: 'TRE6', int n; por peca: int mat (57 folhas / 58 casca), int nv, int ni, float r,g,b (cor do material),
nv * (x y z nx ny nz u v) float32, ni * uint16. Base do tronco na origem, metros (escala 1 = o modelo original, ~18,7 m)."""
import json, struct, os, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, '..', '..', 'app', 'src', 'main', 'assets', 'hds')
LEAF, BARK = 57, 58


def run():
    b = open(os.path.join(A, 'city2.glb'), 'rb').read()
    L = struct.unpack_from('<I', b, 12)[0]; J = json.loads(b[20:20 + L])
    o = 20 + L; bl = struct.unpack_from('<I', b, o)[0]; B = b[o + 8:o + 8 + bl]
    inst = json.load(open(os.path.join(A, 'city2.json')))['inst']
    mname = [m.get('name', '') for m in J['materials']]
    # o no da arvore: o mais repetido entre os que tem material de folha recortada (alphaMode MASK) e casca
    cnt = collections.Counter(a[0] for a in inst)
    cand = []
    for ni, n in enumerate(J['nodes']):
        if 'mesh' not in n: continue
        ms = [J['materials'][p['material']] for p in J['meshes'][n['mesh']]['primitives'] if 'material' in p]
        if any(m.get('alphaMode') == 'MASK' and 'leaves' in m.get('name', '') for m in ms) and any('bark' in m.get('name', '') for m in ms): cand.append((cnt[ni], ni))
    node = max(cand)[1]

    def acc(i, comps):
        a = J['accessors'][i]; v = J['bufferViews'][a['bufferView']]
        dt = {5126: '<f4', 5123: '<u2', 5125: '<u4'}[a['componentType']]; sz = np.dtype(dt).itemsize
        st = v.get('byteStride', sz * comps); off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        raw = np.frombuffer(B, np.uint8, (a['count'] - 1) * st + sz * comps, off)
        out = np.lib.stride_tricks.as_strided(raw, (a['count'], sz * comps), (st, 1)).copy().view(dt).reshape(a['count'], comps)
        return out

    def image(mi):
        t = J['materials'][mi]['pbrMetallicRoughness']['baseColorTexture']['index']
        im = J['images'][J['textures'][t]['source']]; v = J['bufferViews'][im['bufferView']]
        return B[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']]

    prims = []
    for p in J['meshes'][J['nodes'][node]['mesh']]['primitives']:
        mi = p['material']; leaf = J['materials'][mi].get('alphaMode') == 'MASK'
        P = acc(p['attributes']['POSITION'], 3).astype(np.float32); N = acc(p['attributes']['NORMAL'], 3).astype(np.float32)
        U = acc(p['attributes']['TEXCOORD_0'], 2).astype(np.float32); I = acc(p['indices'], 1).reshape(-1).astype(np.uint16)
        col = J['materials'][mi]['pbrMetallicRoughness'].get('baseColorFactor', [1, 1, 1, 1])[:3]
        prims.append([LEAF if leaf else BARK, P, N, U, I, col])
        open(os.path.join(A, 'c6tex', 'arvore_folhas.png' if leaf else 'arvore_casca.png'), 'wb').write(image(mi))
    bark = [q for q in prims if q[0] == BARK][0][1]
    low = bark[bark[:, 1] < bark[:, 1].min() + 1.0]
    c = np.array([low[:, 0].mean(), bark[:, 1].min(), low[:, 2].mean()], np.float32)
    with open(os.path.join(A, 'c6_tree.bin'), 'wb') as f:
        f.write(b'TRE6'); f.write(struct.pack('<i', len(prims)))
        for (mat, P, N, U, I, col) in prims:
            f.write(struct.pack('<iii3f', mat, len(P), len(I), *col))
            f.write(np.hstack([P - c, N, U]).astype('<f4').tobytes()); f.write(I.astype('<u2').tobytes())
    allp = np.vstack([q[1] for q in prims]) - c
    print(f'  arvore da Cidade 2: no {node} ({cnt[node]} copias no city2), {sum(len(q[4]) // 3 for q in prims)} triangulos, '
          f'altura {allp[:, 1].max():.1f} m, raio {np.hypot(allp[:, 0], allp[:, 2]).max():.1f} m')
    return float(allp[:, 1].max()), float(np.hypot(allp[:, 0], allp[:, 2]).max())


if __name__ == '__main__':
    run()
