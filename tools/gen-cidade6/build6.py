#!/usr/bin/env python3
"""Cidade 6: python3 build6.py [saida]  -> tiles GLB + manifesto + GLB unico + previas"""
import sys, os, time, json
from mesh import Mesh
from plan6 import Plan, W, H
import roads6

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'cidade6')
STAGE = os.environ.get('STAGE', 'all')


def build():
    t = time.time()
    P = Plan(); M = Mesh(W, H)
    G = roads6.Ground(P, M).build()
    print(f'chao: {M.ntri} triangulos ({time.time() - t:.1f}s)')
    L = None
    if STAGE != 'chao':
        import lots6
        L = lots6.Lots(P, G, M).build()
        print(f'lotes/construcoes: {M.ntri} triangulos ({time.time() - t:.1f}s)')
        import props6
        L.props = props6.Props(P, G, L, M).build()
    print(f'total: {M.ntri} triangulos ({time.time() - t:.1f}s)')
    return P, G, L, M


def export(P, G, L, M, out=OUT, texdir=None, single=True):
    import shutil, math
    from mesh import write_glb, TILE
    import textures6
    os.makedirs(os.path.join(out, 'tiles', 'texturas'), exist_ok=True)
    tdir = os.path.join(out, 'tiles', 'texturas')
    textures6.make_all(tdir)
    # agrupa por tile -> camada -> material
    tiles = {}
    for (ti, tj, lay, mat), lst in M.data.items():
        tiles.setdefault((ti, tj), {}).setdefault(lay, {}).setdefault(mat, []).extend(lst)
    man = {'nome': 'Cidade 6 - Meu Lar', 'tamanho_m': [W, H], 'eixos': 'X leste, Z sul, Y para cima (metros, igual ao glTF)', 'tile_m': TILE,
           'texturas': 'tiles/texturas/*.jpg (uri relativa dentro de cada tile)', 'tiles': [], 'casas_jogador': L.player,
           'colisoes_ret': {'formato': '[cx, cz, ux, uz, meia_u, meia_v] (retangulo girado: eixo u=(ux,uz), v perpendicular)', 'lista': L.B.colliders},
           'spawn': [float(L.player[0]['centro'][0]), 0.3, float(L.player[0]['centro'][2])] if L.player else [1140, 0.3, 1000]}
    tot = 0
    for (ti, tj), lays in sorted(tiles.items()):
        tr = (ti * TILE, 0.0, tj * TILE)
        spec = [(f'{lay}_{ti:02d}_{tj:02d}', tr, mats) for lay, mats in sorted(lays.items())]
        mk = []
        for h in L.player:
            if M.tile_of(h['centro'][0], h['centro'][2]) == (ti, tj):
                mk.append((f"CasaJogador_{h['k'] + 1:02d}_{h['modelo']}", (h['centro'][0], h['centro'][1], h['centro'][2]), h['yaw']))
        fn = f'tile_{ti:02d}_{tj:02d}.glb'
        n = write_glb(os.path.join(out, 'tiles', fn), spec, tdir, embed=False, tex_uri_prefix='texturas/', markers=mk)
        tot += n
        man['tiles'].append({'arquivo': 'tiles/' + fn, 'i': ti, 'j': tj, 'x0': ti * TILE, 'z0': tj * TILE, 'triangulos': n, 'camadas': sorted(lays),
                             'bytes': os.path.getsize(os.path.join(out, 'tiles', fn))})
    json.dump(man, open(os.path.join(out, 'cidade6.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'tiles: {len(man["tiles"])} arquivos, {tot} triangulos, {sum(t["bytes"] for t in man["tiles"]) / 1e6:.1f} MB')
    if single:
        mk = [(f"CasaJogador_{h['k'] + 1:02d}_{h['modelo']}", tuple(h['centro']), h['yaw']) for h in L.player]
        # GLB unico em duas partes (cada uma < 100 MB): ruas/construcoes e vegetacao + parques + terreno/agua/orla
        for (fname, keep) in (('cidade6_completa.glb', lambda lay: lay not in ('carros', 'mobiliario') + ('vegetacao', 'arvores', 'arbustos', 'mata', 'parques', 'terreno', 'agua', 'orla')), ('cidade6_vegetacao.glb', lambda lay: lay in ('vegetacao', 'arvores', 'arbustos', 'mata', 'parques', 'terreno', 'agua', 'orla'))):
            spec = []
            for (ti, tj), lays in sorted(tiles.items()):
                for lay, mats in sorted(lays.items()):
                    if keep(lay): spec.append((f'{lay}_{ti:02d}_{tj:02d}', (ti * TILE, 0.0, tj * TILE), mats))
            fn = os.path.join(out, fname)
            n = write_glb(fn, spec, tdir, embed=True, markers=mk if 'completa' in fname else None, quant=True)
            print(f'{fname}: {n} triangulos, {os.path.getsize(fn) / 1e6:.1f} MB')
    return man


if __name__ == '__main__':
    P, G, L, M = build()
    print(M.stats())
    import numpy as np
    bad = {}; tot = 0
    for (ti, tj, lay, mat), lst in M.data.items():
        for c in lst:
            pn = np.frombuffer(c.pn.tobytes(), np.float32).reshape(-1, 6); idx = np.frombuffer(c.idx.tobytes(), np.uint16).reshape(-1, 3)
            p = pn[:, :3]; g = np.cross(p[idx[:, 1]] - p[idx[:, 0]], p[idx[:, 2]] - p[idx[:, 0]]); nm = pn[:, 3:][idx].mean(1)
            k = int(((g * nm).sum(1) < -1e-9).sum()); tot += len(idx)
            if k: bad[lay] = bad.get(lay, 0) + k
    print('faces invertidas (normal x ordem dos vertices):', bad or 0, 'de', tot)
    if os.environ.get('GLB', '1') != '0': export(P, G, L, M, single=os.environ.get('SINGLE', 'leve'))

    if os.environ.get('APP', '1') != '0':
        import app_export6
        print('exportando para o jogo (assets/hds/c6*)...')
        app_export6.run(P, G, L, M, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app', 'src', 'main', 'assets', 'hds'))
        import tree_export6; tree_export6.run()          # arvore da Cidade 2 (c6_tree.bin + c6tex/arvore_*.png)
