"""Cidade 6 - mapa do jogo: imagem detalhada vista de cima (c6_map.png), nomes das ruas, pontos de interesse e a rede
de ruas para o GPS (c6.json 'mapa').

Imagem: relevo sombreado bem leve, mar e rio com margem, areia, calcadao em ondas, quadras por zona, parques e
pracas, arvores (pontinhos), predios (pegada de cada colisao grande), pracas dos predios de profissao com a cor da
marca, ruas com contorno (avenidas em amarelo-claro, Beira-Mar em laranja-claro), pontes, molhes e faixas de pedestre.
Escala: PX metros por pixel; o jogo desenha a imagem no retangulo (0,0)-(W,H) do mundo do gerador.
"""
import math, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from plan6 import W, H, PROFILE, half_row, shore_z, river_x, RIVER_W, RIVER_WALL

PX = 0.8                      # metros por pixel na imagem final
SS = 2                        # supersample

# nomes das vias (sem repetir): avenidas, ruas do centro e ruas de bairro
AV = ['Av. Brasil', 'Av. das Palmeiras', 'Av. Independência', 'Av. dos Bandeirantes', 'Av. Atlântica', 'Av. do Contorno']
CENTRO = ['Rua XV de Novembro', 'Rua Sete de Setembro', 'Rua da Matriz', 'Rua do Comércio', 'Rua Direita', 'Rua Tiradentes',
          'Rua Barão do Rio Branco', 'Rua Marechal Deodoro', 'Rua Floriano Peixoto', 'Rua Santos Dumont', 'Rua Rui Barbosa',
          'Rua Dom Pedro II', 'Rua da Quitanda', 'Rua do Ouvidor', 'Rua General Osório', 'Rua José Bonifácio', 'Rua Benjamin Constant',
          'Rua Duque de Caxias', 'Rua Princesa Isabel', 'Rua Visconde de Mauá', 'Rua Carlos Gomes', 'Rua Joaquim Nabuco', 'Rua Castro Alves',
          'Rua Machado de Assis', 'Rua Álvares Cabral', 'Rua Anchieta', 'Rua Paraná', 'Rua Bahia']
BAIRRO = ['Rua das Acácias', 'Rua dos Ipês', 'Rua das Hortênsias', 'Rua dos Girassóis', 'Rua das Margaridas', 'Rua das Orquídeas',
          'Rua dos Jacarandás', 'Rua das Tulipas', 'Rua dos Cravos', 'Rua das Violetas', 'Rua dos Lírios', 'Rua das Camélias',
          'Rua das Bromélias', 'Rua dos Manacás', 'Rua das Azaleias', 'Rua dos Flamboyants', 'Rua das Magnólias', 'Rua dos Coqueiros',
          'Rua das Mangueiras', 'Rua dos Cajueiros', 'Rua das Jabuticabeiras', 'Rua dos Pinheiros', 'Rua das Paineiras', 'Rua dos Cedros',
          'Rua das Amendoeiras', 'Rua dos Bem-te-vis', 'Rua dos Sabiás', 'Rua dos Canários', 'Rua das Andorinhas', 'Rua dos Colibris',
          'Rua das Gaivotas', 'Rua dos Tucanos', 'Rua das Araras', 'Rua dos Pardais', 'Rua das Garças', 'Rua dos Pelicanos',
          'Rua Cecília Meireles', 'Rua Clarice Lispector', 'Rua Carlos Drummond', 'Rua Vinícius de Moraes', 'Rua Tom Jobim',
          'Rua Cora Coralina', 'Rua Manuel Bandeira', 'Rua Mário Quintana', 'Rua Rachel de Queiroz', 'Rua Jorge Amado',
          'Rua Graciliano Ramos', 'Rua Monteiro Lobato', 'Rua Érico Veríssimo', 'Rua Lygia Fagundes', 'Rua Ariano Suassuna',
          'Rua Portinari', 'Rua Tarsila do Amaral', 'Rua Anita Malfatti', 'Rua Di Cavalcanti', 'Rua Villa-Lobos', 'Rua Chiquinha Gonzaga',
          'Rua Pixinguinha', 'Rua Cartola', 'Rua Noel Rosa', 'Rua Elis Regina', 'Rua Gonzagão', 'Rua Dorival Caymmi', 'Rua Ary Barroso',
          'Rua do Sol', 'Rua da Lua', 'Rua das Estrelas', 'Rua do Horizonte', 'Rua da Aurora', 'Rua do Mirante', 'Rua da Colina',
          'Rua da Brisa', 'Rua do Farol', 'Rua da Ponte']


def road_names(P):
    """nome bonito de cada via do plano (estavel: ordem do plano)"""
    out = {}; ia = ic = ib = 0
    for r in P.roads:
        k = r['kind']
        if k == 'orla': nm = 'Av. Beira-Mar'
        elif k == 'av': nm = AV[ia % len(AV)]; ia += 1
        elif k == 'centro': nm = CENTRO[ic % len(CENTRO)]; ic += 1
        else: nm = BAIRRO[ib % len(BAIRRO)]; ib += 1
        out[id(r)] = nm
    return out


def build(P, G, L, assets):
    names = road_names(P)
    s = SS / PX
    Wp, Hp = int(W * s), int(H * s)
    img = Image.new('RGB', (Wp, Hp), (237, 234, 226))
    d = ImageDraw.Draw(img)
    T = lambda x, z: (x * s, z * s)

    def poly(g, fill, outline=None, width=1):
        for p in getattr(g, 'geoms', [g]):
            if p.geom_type != 'Polygon' or p.is_empty: continue
            d.polygon([T(*c) for c in p.exterior.coords], fill=fill, outline=outline, width=width)
            for h in p.interiors: d.polygon([T(*c) for c in h.coords], fill=(237, 234, 226))

    # ---- relevo: tom verde nos morros + sombreado leve
    gx = np.arange(0, W, 8.0); gz = np.arange(0, H, 8.0)
    Xg, Zg = np.meshgrid(gx, gz); Hg = G.height(Xg, Zg)
    dzx = np.gradient(Hg, axis=1); dzz = np.gradient(Hg, axis=0)
    shade = np.clip(1.0 - (dzx * 0.7 + dzz * 0.5) * 0.08, 0.82, 1.08)
    hill = np.clip((Hg - 3) / 25.0, 0, 1)
    base = np.dstack([237 - 40 * hill, 234 - 14 * hill, 226 - 50 * hill]) * shade[..., None]
    bimg = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).resize((Wp, Hp), Image.BILINEAR)
    img.paste(bimg); d = ImageDraw.Draw(img)

    # ---- quadras por zona
    zcol = {'centro': (232, 226, 216), 'suburbio': (240, 237, 228), 'orla': (234, 228, 218), 'marina': (232, 228, 222),
            'parque': (190, 226, 168), 'ribeirinho': (196, 228, 172), 'praia': (244, 230, 190)}
    for b in P.blocks: poly(b['poly'], zcol.get(b['zone'], (236, 232, 224)))
    # ---- agua
    poly(P.sea, (122, 196, 232)); poly(P.river, (122, 196, 232))
    for g in (P.sea, P.river):
        for p in getattr(g, 'geoms', [g]):
            if p.geom_type == 'Polygon': d.line([T(*c) for c in p.exterior.coords], fill=(96, 170, 214), width=int(2 * s))
    # faixa de espuma e areia
    xs = np.arange(0, W + 1, 4.0)
    sand = [T(x, 1718.0) for x in xs] + [T(x, shore_z(x)) for x in xs[::-1]]
    d.polygon(sand, fill=(246, 230, 186))
    d.line([T(x, shore_z(x)) for x in xs], fill=(250, 250, 246), width=int(1.6 * s))
    # calcadao (pedra portuguesa: listras onduladas)
    z0 = 1688.0 + half_row('orla')
    d.polygon([T(0, z0), T(W, z0), T(W, 1718), T(0, 1718)], fill=(248, 246, 240))
    for k in range(3):
        zz = z0 + 6 + k * 8
        d.line([T(x, zz + 1.5 * math.sin(x / 6.0)) for x in np.arange(0, W, 1.5)], fill=(70, 70, 76), width=max(1, int(0.9 * s)))
    d.line([T(0, z0 + 2.2), T(W, z0 + 2.2)], fill=(206, 110, 96), width=int(2.8 * s))      # ciclovia

    # ---- arvores (pontinhos) e predios
    tr = getattr(L.props, 'app_trees', [])
    for t in tr:
        x, z = t[0], t[1]; r_ = 1.3 * s
        d.ellipse([x * s - r_, z * s - r_, x * s + r_, z * s + r_], fill=(150, 200, 120))
    for (cx, cz, ux, uz, hu, hv) in L.B.colliders:
        if hu * hv < 6.0: continue
        vx, vz = -uz, ux
        pts = [(cx + ux * a + vx * b, cz + uz * a + vz * b) for (a, b) in ((-hu, -hv), (hu, -hv), (hu, hv), (-hu, hv))]
        d.polygon([T(*p) for p in pts], fill=(214, 206, 194), outline=(186, 176, 162))
    for (pts, col) in getattr(L, 'feet', []):                          # predios das profissoes e prefeitura (cor da marca)
        lite = tuple(int(v * 0.45 + 255 * 0.55) for v in col)
        d.polygon([T(*p) for p in pts], fill=lite, outline=tuple(int(v * 0.8) for v in col), width=int(1.0 * s))
    # pracas dos predios de profissao (cor da marca) e prefeitura
    for j in getattr(L, 'jobs', []):
        c = j['cor'] & 0xFFFFFF; col = ((c >> 16) & 255, (c >> 8) & 255, c & 255)
        lite = tuple(int(v * 0.35 + 255 * 0.65) for v in col)
        x, z = j['x'], j['z']; r_ = 4.0 * s
        d.ellipse([x * s - r_, z * s - r_, x * s + r_, z * s + r_], fill=lite, outline=col, width=int(0.8 * s))

    # ---- ruas: contorno (calcada) e pista
    order = sorted(P.roads, key=lambda r: {'rua': 0, 'centro': 1, 'av': 2, 'orla': 3}[r['kind']])
    for r in order:
        pts = [T(*p) for p in r['pts']]
        w = half_row(r['kind']) * 2 * s
        d.line(pts, fill=(200, 196, 188), width=int(w + 1.2 * s), joint='curve')
    for r in order:
        pts = [T(*p) for p in r['pts']]
        pr = PROFILE[r['kind']]
        w = (pr['road'] * 2 + pr['med'] * 2) * s
        col = {'rua': (255, 255, 255), 'centro': (255, 255, 255), 'av': (255, 236, 160), 'orla': (255, 214, 150)}[r['kind']]
        d.line(pts, fill=col, width=int(w), joint='curve')
        for p in (r['pts'][0], r['pts'][-1]):
            rr = w / 2; d.ellipse([p[0] * s - rr, p[1] * s - rr, p[0] * s + rr, p[1] * s + rr], fill=col)
        if pr['med'] > 0:
            d.line(pts, fill=(170, 210, 140) if r['kind'] == 'av' else (240, 200, 130), width=max(1, int(pr['med'] * 1.6 * s)), joint='curve')
    # molhes dos farois
    zsh = shore_z(river_x(1840))
    for sgn in (-1, 1):
        pts = [T(river_x(zz) + sgn * (RIVER_W / 2 + RIVER_WALL / 2), zz) for zz in np.arange(1718, zsh + 85, 4.0)]
        d.line(pts, fill=(160, 156, 150), width=int(4.0 * s))
        lx, lz = river_x(zsh + 84) + sgn * (RIVER_W / 2 + RIVER_WALL / 2), zsh + 91
        d.ellipse([(lx - 9) * s, (lz - 9) * s, (lx + 9) * s, (lz + 9) * s], fill=(200, 196, 188), outline=(150, 146, 140), width=int(s))

    img = img.resize((int(W / PX), int(H / PX)), Image.LANCZOS)
    img.save(os.path.join(assets, 'c6_map.png'), optimize=True)

    # ---- rotulos das ruas (pontos ao longo da via, com angulo), pontos de interesse
    labels = []
    placed = {}                                       # um nome a cada ~450 m (nada de nome repetido em cima de nome)
    for r in sorted(P.roads, key=lambda r_: -LineString(r_['pts']).length):
        ls = LineString(r['pts']); L_ = ls.length
        if L_ < 60: continue
        n = max(1, int(L_ // 300))
        for k in range(n):
            t = (k + 0.5) / n * L_
            p = ls.interpolate(t); q = ls.interpolate(min(L_, t + 4)); p0 = ls.interpolate(max(0, t - 4))
            ang = math.degrees(math.atan2(q.y - p0.y, q.x - p0.x))
            if ang > 90: ang -= 180
            if ang < -90: ang += 180
            nm_ = names[id(r)]
            if any(math.hypot(p.x - a_, p.y - b_) < 450 for (a_, b_) in placed.get(nm_, [])): continue
            if any(math.hypot(p.x - l_[0], p.y - l_[1]) < 70 for l_ in labels): continue
            placed.setdefault(nm_, []).append((p.x, p.y))
            labels.append([round(p.x, 1), round(p.y, 1), round(ang, 1), nm_, {'rua': 0, 'centro': 1, 'av': 2, 'orla': 3}[r['kind']]])
    pois = []
    pass
    for b in P.blocks:
        if b['zone'] == 'parque': pois.append([round(b['poly'].centroid.x, 1), round(b['poly'].centroid.y, 1), 'Parque Central', 'parque'])
    rb = [b for b in P.blocks if b['zone'] == 'ribeirinho']
    for k, b in enumerate(rb[::3]): pois.append([round(b['poly'].centroid.x, 1), round(b['poly'].centroid.y, 1), 'Parque do Rio', 'parque'])
    for (nm, (x, z, _)) in L.SPECIAL.items():
        if nm.startswith('escola'): pois.append([x, z, 'Escola Municipal', 'escola'])
        elif nm == 'igreja': pois.append([x, z, 'Igreja Matriz', 'igreja'])
    pois.append([round(W * 0.3, 1), 1770.0, 'Praia do Sol', 'praia']); pois.append([round(W * 0.78, 1), 1770.0, 'Praia das Ondas', 'praia'])
    pois.append([round(river_x(zsh + 84) - RIVER_W / 2, 1), round(zsh + 91, 1), 'Farol', 'farol'])
    pois.append([round(river_x(1200), 1), 1200.0, 'Rio Azul', 'rio'])
    EMO = {'parque': '🌳', 'escola': '🎒', 'igreja': '⛪', 'praia': '🏖️', 'farol': '🗼', 'rio': '🌊'}
    pois = [p + [EMO.get(p[3], '📍')] for p in pois]

    # ---- rede de ruas para o GPS: eixos cortados nos cruzamentos
    lines = [LineString(r['pts']) for r in P.roads]
    merged = unary_union(lines)
    nodes = {}; nx_ = []; edges = []
    def nid(c):
        k = (round(c[0] / 1.0), round(c[1] / 1.0))
        if k not in nodes: nodes[k] = len(nx_); nx_.append([round(c[0], 1), round(c[1], 1)])
        return nodes[k]
    rl = [(LineString(r['pts']), names[id(r)]) for r in P.roads]
    nm_idx = {}; nm_list = []
    for seg in getattr(merged, 'geoms', [merged]):
        cs = list(seg.coords)
        if len(cs) < 2 or seg.length < 0.5: continue
        a = nid(cs[0]); b = nid(cs[-1])
        mp = seg.interpolate(0.5, normalized=True)
        nm = min(rl, key=lambda q: q[0].distance(mp))[1]
        if nm not in nm_idx: nm_idx[nm] = len(nm_list); nm_list.append(nm)
        flat = [round(v, 1) for c in cs for v in c]
        edges.append([a, b, round(seg.length, 1), nm_idx[nm], flat])
    return {'img': [0.0, 0.0, float(W), float(H)], 'rotulos': labels, 'pois': pois,
            'grafo': {'nos': [v for p in nx_ for v in p], 'arestas': edges, 'nomes': nm_list}}
