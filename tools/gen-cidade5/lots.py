"""ETAPA D: quarteiroes -> lotes ao longo das ruas, as 17 casas (posicao/frente/platô), caminho, garagem com rebaixo da guia, cercas e arvores do lote.

Fluxo:  terrain_final.run -> lots.plan(city, geo, ynode) -> platos entram na terraplenagem; ground.build usa plan.driveways (rebaixo da guia)
        e lots.build_ground(gr, plan) desenha caminho/garagem/cerca; gen_cidade5 exporta houses/solids/trees para o app.
As casas do Hds NAO giram (a malha vem do city2.glb): so ficam em trechos de rua quase leste-oeste e do lado certo (frente norte ou sul)."""
import math, json, random, os
import numpy as np
from PIL import Image, ImageDraw
from plan import *
import terrain_final as T
from bake import rgb, PLAIN, STONE, WOOD, METAL, PAVER, GRASS

SW_Y = 0.27; ROADY = 0.12
HOUSE_UP = 0.12                         # patamar do lote acima da calcada da frente (o app soma +0,08 do piso)
COLL = {'conc': rgb('#CFCBC2'), 'conc2': rgb('#BDB8AD'), 'white': rgb('#F4F1EA'), 'brick': rgb('#B5654A'), 'stone': rgb('#8F8A7E'), 'stone2': rgb('#A7A194'),
        'iron': rgb('#2A2C30'), 'wood': rgb('#8B6B47'), 'hedge': rgb('#3F7F3A'), 'block': rgb('#D9D2C3'), 'plaster': rgb('#EADFCB')}
SW = 1.4                                   # largura do caminho da porta
DRV_W = 3.0                                # largura da garagem
DRV_LEN = 5.6

# casas (indice k = "Casa k+1" do HdsEstate): nome, bairro, ancora (x, z), frente norte(-1)/sul(+1), margens (frente, lateral, fundo), pode ter frente na Av. Beira-Mar
BAIRROS = {'Vila Esperança': (1250, 1950), 'Parque das Flores': (1300, 1600), 'Jardim Central': (3000, 1900), 'Recanto do Sul': (1500, 2690),
           'Alto da Colina': (1560, 1060), 'Península Real': (3380, 2770)}
HOUSE_BAIRRO = {0: 'Vila Esperança', 11: 'Vila Esperança', 7: 'Vila Esperança', 12: 'Vila Esperança', 8: 'Vila Esperança',
                9: 'Parque das Flores', 10: 'Parque das Flores', 13: 'Parque das Flores',
                4: 'Jardim Central', 5: 'Jardim Central', 6: 'Jardim Central',
                14: 'Recanto do Sul', 15: 'Recanto do Sul', 3: 'Recanto do Sul',
                2: 'Alto da Colina', 1: 'Alto da Colina', 16: 'Península Real'}
BEACH_HOUSES = {14, 15, 3, 16}
ESTATE = {'Alto da Colina', 'Península Real'}
FENCE = {'Vila Esperança': 'bloco', 'Parque das Flores': 'estacas', 'Jardim Central': 'tijolo', 'Recanto do Sul': 'madeira', 'Alto da Colina': 'pedra', 'Península Real': 'ferro'}


class Plan:
    def __init__(self):
        self.fronts = []; self.lots = []; self.houses = []; self.plateaus = []; self.driveways = {}; self.solids = []; self.trees = []
        self.block = None; self.occ = None; self.log = []


# ---------------------------------------------------------------------------------------------------- frentes de rua
def build_fronts(city, geo, yn):
    fronts = []
    for k, e in enumerate(city.edges):
        if e['kind'] in ('bridge', 'redbridge'): continue
        lvl = min(e['lvl'], 2)
        if e['lvl'] >= 3: continue
        half = T.HALF.get(lvl, 7.5)
        pp = T.profile_pts(e, yn[e['a']], yn[e['b']])
        pts = np.array([[p[0], p[1]] for p in pp]); ys = np.array([p[2] for p in pp])
        seg = np.hypot(*(pts[1:] - pts[:-1]).T); cs = np.concatenate([[0], np.cumsum(seg)]); L = cs[-1]
        ca = e.get('_ca', 0.0); cb = e.get('_cb', 0.0)
        if L - ca - cb < 14: continue
        S = np.arange(ca + 2.0, L - cb - 2.0 + 1e-6, 2.0)
        X = np.interp(S, cs, pts[:, 0]); Z = np.interp(S, cs, pts[:, 1]); Y = np.interp(S, cs, ys)
        Sa = np.clip(S - 3, 0, L); Sb = np.clip(S + 3, 0, L)
        tx = np.interp(Sb, cs, pts[:, 0]) - np.interp(Sa, cs, pts[:, 0]); tz = np.interp(Sb, cs, pts[:, 1]) - np.interp(Sa, cs, pts[:, 1])
        ln = np.hypot(tx, tz) + 1e-9; tx /= ln; tz /= ln
        for sgn in (1, -1):
            nx = -tz * sgn; nz = tx * sgn                    # normal para FORA da rua (lado do lote)
            if e.get('name') == 'Av. Beira-Mar':
                mx, mz = X[len(X) // 2], Z[len(Z) // 2]
                if geo.Dsea[geo.idx(mx + nx[len(X) // 2] * 30, mz + nz[len(X) // 2] * 30)] < geo.Dsea[geo.idx(mx - nx[len(X) // 2] * 30, mz - nz[len(X) // 2] * 30)]: continue   # lado do mar = orla
            fronts.append({'k': k, 'sgn': sgn, 'lvl': lvl, 'name': e.get('name', ''), 'S': S, 'X': X + nx * half, 'Z': Z + nz * half, 'Y': Y + SW_Y,
                           'NX': nx, 'NZ': nz, 'TX': tx * sgn, 'TZ': tz * sgn, 'half': half, 'L': L})
    return fronts


# ---------------------------------------------------------------------------------------------------- rasters
def make_block(city, geo, plan, size=(4400, 3600)):
    W, H = size
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    for k, e in enumerate(city.edges):
        half = T.HALF.get(min(e['lvl'], 2), 7.5)
        if e['kind'] == 'redbridge': half = 12
        pts = [(p[0], p[1]) for p in e['p']]
        if len(pts) >= 2: d.line(pts, fill=255, width=int(2 * (half - 0.9)), joint='curve')
    # discos nos cruzamentos (esquinas e canteiros) e rotatorias
    cut = {}
    for k, e in enumerate(city.edges):
        for end, ni in (('a', e['a']), ('b', e['b'])):
            cut[ni] = max(cut.get(ni, 0.0), e.get('_ca' if end == 'a' else '_cb', 0.0))
    rr = {r['node']: r['r'] for r in city.rounds}
    for ni, n in enumerate(city.nodes):
        R = cut.get(ni, 0.0) + 0.5
        if ni in rr: R = max(R, rr[ni] + 16.0)
        R = max(R, 9.0)
        d.ellipse([n[0] - R, n[1] - R, n[0] + R, n[1] + R], fill=255)
    for r in city.rounds:
        d.ellipse([r['x'] - r['r'] - 16, r['z'] - r['r'] - 16, r['x'] + r['r'] + 16, r['z'] + r['r'] + 16], fill=255)
    block = np.array(im) > 0
    # agua, praia/orla (ate a calcada da Av. Beira-Mar), lagoa
    NZ_, NX_ = geo.water.shape
    jj = np.clip((np.arange(H) / CELL).astype(int), 0, NZ_ - 1)[:, None]; ii = np.clip((np.arange(W) / CELL).astype(int), 0, NX_ - 1)[None, :]
    wat = geo.water[jj, ii]
    ws = wat.copy()
    for _ in range(4):                                       # engorda a agua em ~8 m
        ws = ws | np.roll(ws, 1, 0) | np.roll(ws, -1, 0) | np.roll(ws, 1, 1) | np.roll(ws, -1, 1)
    block |= ws
    block |= (geo.Dsea[jj, ii] < ORLA_AXIS + 15.0) & geo.beach_zone[jj, ii]
    block |= (geo.Dsea[jj, ii] < ORLA_AXIS + 15.0) & (geo.Z[jj, ii] > 2000)
    return block


# ---------------------------------------------------------------------------------------------------- geometria de retangulo
def rect_corners(F, T_, N_, W, D, inset=0.0):
    """F = centro da frente (ponto), T_ = tangente, N_ = normal para dentro do lote; retorna 4 cantos (frente esq, frente dir, fundo dir, fundo esq)"""
    a = (F[0] - T_[0] * W / 2 + N_[0] * inset, F[1] - T_[1] * W / 2 + N_[1] * inset)
    b = (F[0] + T_[0] * W / 2 + N_[0] * inset, F[1] + T_[1] * W / 2 + N_[1] * inset)
    return [a, b, (b[0] + N_[0] * (D - inset), b[1] + N_[1] * (D - inset)), (a[0] + N_[0] * (D - inset), a[1] + N_[1] * (D - inset))]


def poly_mask(arr, corners, shrink=0.0):
    """True se o poligono (convexo, em m) toca alguma celula verdadeira de arr (1 px = 1 m)"""
    xs = [c[0] for c in corners]; zs = [c[1] for c in corners]
    x0, x1 = int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 1; z0, z1 = int(math.floor(min(zs))) - 1, int(math.ceil(max(zs))) + 1
    H, W = arr.shape
    if x0 < 0 or z0 < 0 or x1 >= W or z1 >= H: return True
    im = Image.new('L', (x1 - x0 + 1, z1 - z0 + 1), 0)
    cx = sum(xs) / 4; cz = sum(zs) / 4
    pts = []
    for (x, z) in corners:
        dx, dz = x - cx, z - cz; l = math.hypot(dx, dz) or 1
        pts.append((x - dx / l * shrink - x0 + 0.5, z - dz / l * shrink - z0 + 0.5))
    ImageDraw.Draw(im).polygon(pts, fill=255)
    return bool(((np.array(im) > 0) & arr[z0:z1 + 1, x0:x1 + 1]).any())


def draw_poly(arr, corners, val=True):
    xs = [c[0] for c in corners]; zs = [c[1] for c in corners]
    x0, x1 = int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 1; z0, z1 = int(math.floor(min(zs))) - 1, int(math.ceil(max(zs))) + 1
    im = Image.new('L', (x1 - x0 + 1, z1 - z0 + 1), 0)
    ImageDraw.Draw(im).polygon([(x - x0 + 0.5, z - z0 + 0.5) for x, z in corners], fill=255)
    sub = arr[z0:z1 + 1, x0:x1 + 1]
    sub |= (np.array(im) > 0)


def terrain_stats(geo, corners):
    hs = []
    for u in np.linspace(0.05, 0.95, 5):
        for v in np.linspace(0.05, 0.95, 5):
            a = (corners[0][0] + (corners[1][0] - corners[0][0]) * u, corners[0][1] + (corners[1][1] - corners[0][1]) * u)
            b = (corners[3][0] + (corners[2][0] - corners[3][0]) * u, corners[3][1] + (corners[2][1] - corners[3][1]) * u)
            hs.append(geo.height(a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v))
    diag = math.hypot(math.hypot(corners[1][0] - corners[0][0], corners[1][1] - corners[0][1]), math.hypot(corners[3][0] - corners[0][0], corners[3][1] - corners[0][1]))
    return float(np.mean(hs)), float(max(hs) - min(hs)) / max(diag, 1.0)


# ---------------------------------------------------------------------------------------------------- casas
def load_plots():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app', 'src', 'main', 'assets', 'hds', 'city2.json')
    d = json.load(open(p))
    ext = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'house_extents.json')))     # quintal real (cerca incluida), medido na malha da casa
    out = []
    for k, pl in enumerate(d['plots']):
        cx = (pl['x0'] + pl['x1']) / 2; cz = (pl['z0'] + pl['z1']) / 2
        x0, x1, z0, z1 = ext[str(k)]
        out.append({'k': k, 'name': pl['name'], 'bw': pl['x1'] - pl['x0'], 'bd': pl['z1'] - pl['z0'], 'fx': pl['x'] - cx, 'fz': pl['z'] - cz, 'yard': (x0, x1, z0, z1)})
    return out


def try_house(plan, geo, hp, fr, i, tol_deg, side_m, gap_front, rear_m, slope_max):
    """tenta colocar a casa hp (com o quintal real) na frente fr, indice i; devolve dict do lote ou None.
    Sistema do lote: u = ao longo da rua (T), v = para dentro do lote (N); a frente do quintal (porta/portao) fica a gap_front m da calcada."""
    nx, nz = fr['NX'][i], fr['NZ'][i]
    face = 1.0 if hp['fz'] > 0 else -1.0
    cosang = (-nz) * face                                         # frente da casa = -N precisa apontar ~ (0, face)
    if cosang < math.cos(math.radians(tol_deg)): return None
    tx, tz = fr['TX'][i], fr['TZ'][i]
    x0, x1, z0, z1 = hp['yard']
    cu = [((x - 0.0) * tx + (z - 0.0) * tz, (x - 0.0) * nx + (z - 0.0) * nz) for x in (x0, x1) for z in (z0, z1)]        # cantos do quintal relativos ao centro da casa
    umin = min(c[0] for c in cu); umax = max(c[0] for c in cu); vmin = min(c[1] for c in cu); vmax = max(c[1] for c in cu)
    Wl = (umax - umin) + 2 * side_m; Dl = gap_front + (vmax - vmin) + rear_m
    u_c = -(umin + umax) / 2                                       # casa deslocada para o quintal ficar centrado no lote
    v_c = gap_front - vmin
    F = (fr['X'][i], fr['Z'][i]); Tn = (tx, tz); Nn = (nx, nz)
    S = fr['S']; s0, s1 = S[i] - Wl / 2, S[i] + Wl / 2
    if s0 < S[0] or s1 > S[-1]: return None
    ia = int(np.searchsorted(S, s0)); ib = min(int(np.searchsorted(S, s1)), len(S) - 1)
    A = (fr['X'][ia], fr['Z'][ia]); B = (fr['X'][ib], fr['Z'][ib])
    dxx, dzz = B[0] - A[0], B[1] - A[1]; ll = math.hypot(dxx, dzz) or 1
    dev = max(abs((fr['X'][q] - A[0]) * dzz - (fr['Z'][q] - A[1]) * dxx) / ll for q in range(ia, ib + 1))
    if dev > 0.7: return None
    cor = rect_corners(F, Tn, Nn, Wl, Dl, inset=0.0)
    if poly_mask(plan.block, rect_corners(F, Tn, Nn, Wl, Dl, inset=0.6)): return None
    if poly_mask(plan.occ, rect_corners(F, Tn, Nn, Wl - 0.9, Dl - 0.9, inset=0.45), 0.0): return None
    hm, sl = terrain_stats(geo, cor)
    if sl > slope_max: return None
    yfront = float(np.interp(S[i], S, fr['Y']))
    if abs(hm - yfront) > 2.6: return None
    C = (F[0] + Tn[0] * u_c + Nn[0] * v_c, F[1] + Tn[1] * u_c + Nn[1] * v_c)
    return {'rect': cor, 'F': F, 'T': Tn, 'N': Nn, 'W': Wl, 'D': Dl, 'C': C, 'yfront': yfront, 'angle': math.degrees(math.acos(min(1.0, cosang))), 'terr': hm, 'slope': sl, 'S': float(S[i]),
            'gap': gap_front}


def place_houses(plan, geo, plots):
    order = sorted(range(len(plots)), key=lambda k: -(plots[k]['yard'][1] - plots[k]['yard'][0]) * (plots[k]['yard'][3] - plots[k]['yard'][2]))
    placed = {}
    for k in order:
        hp = plots[k]; bairro = HOUSE_BAIRRO[k]; ax, az = BAIRROS[bairro]
        estate = bairro in ESTATE
        side_m = 4.0 if estate else 2.0; gap_front = 4.0 if estate else 3.0; rear_m = 5.0 if estate else 2.5
        slope_max = 0.16 if bairro == 'Alto da Colina' else 0.12
        best = None
        for radius in (420, 700, 1100, 2000):
            cands = []
            for fr in plan.fronts:
                if fr['lvl'] == 0 and k not in BEACH_HOUSES: continue
                d = np.hypot(fr['X'] - ax, fr['Z'] - az)
                for i in np.nonzero(d < radius)[0][::2]:
                    cands.append((float(d[i]) + (60.0 if fr['lvl'] == 1 else 0.0), fr, int(i)))
            cands.sort(key=lambda t: t[0])
            for tol in (2.5, 5, 8, 12, 20):
                tried = 0
                for sc, fr, i in cands:
                    r = try_house(plan, geo, hp, fr, i, tol, side_m, gap_front, rear_m, slope_max)
                    tried += 1
                    if r:
                        r['score'] = sc; r['fr'] = fr; best = r; break
                    if tried > 6000: break
                if best: break
            if best: break
        if not best:
            plan.log.append(f'casa {k + 1}: SEM LOTE'); continue
        fr = best['fr']; plat = best['yfront'] + HOUSE_UP
        face = 1.0 if hp['fz'] > 0 else -1.0
        C = best['C']
        box = (C[0] - hp['bw'] / 2, C[1] - hp['bd'] / 2, C[0] + hp['bw'] / 2, C[1] + hp['bd'] / 2)
        yard = (C[0] + hp['yard'][0], C[1] + hp['yard'][2], C[0] + hp['yard'][1], C[1] + hp['yard'][3])
        draw_poly(plan.occ, best['rect'], True)
        door = (C[0] + hp['fx'], C[1] + hp['fz'])
        placed[k] = {'k': k, 'name': hp['name'], 'bairro': bairro, 'lot': {kk: best[kk] for kk in ('rect', 'F', 'T', 'N', 'W', 'D', 'yfront', 'angle', 'slope', 'gap')},
                     'cx': C[0], 'cz': C[1], 'y': plat, 'box': box, 'yard': yard, 'bw': hp['bw'], 'bd': hp['bd'], 'face': face, 'door': door, 'edge': fr['k'], 'sgn': fr['sgn'],
                     's': best['S'], 'street': fr['name'], 'lvl': fr['lvl']}
        plan.log.append(f'casa {k + 1} ({bairro}): lote {best["W"]:.0f}x{best["D"]:.0f} m em ({C[0]:.0f},{C[1]:.0f}) frente {"sul" if face > 0 else "norte"} desvio {best["angle"]:.1f} graus declive {best["slope"]*100:.1f}%')
    plan.houses = [placed[k] for k in sorted(placed)]
    for h in plan.houses:
        r = h['lot']['rect']
        cx = sum(p[0] for p in r) / 4; cz = sum(p[1] for p in r) / 4
        plan.plateaus.append({'cx': cx, 'cz': cz, 'tx': h['lot']['T'][0], 'tz': h['lot']['T'][1], 'hw': h['lot']['W'] / 2, 'hd': h['lot']['D'] / 2, 'y': h['y'], 'blend': 9.0, 'k': h['k']})


# ---------------------------------------------------------------------------------------------------- lotes comuns (dados para a Etapa E)
def fill_lots(plan, geo, seed=RNG):
    rnd = random.Random(seed)
    for fr in plan.fronts:
        S = fr['S']; s = S[0]
        wmin, wmax = {0: (28, 44), 1: (20, 30), 2: (15, 22)}[fr['lvl']]
        while s < S[-1] - 10:
            Wl = rnd.uniform(wmin, wmax)
            i = int(np.searchsorted(S, s + Wl / 2))
            if i >= len(S) or s + Wl > S[-1]: break
            F = (float(fr['X'][i]), float(fr['Z'][i])); Tn = (float(fr['TX'][i]), float(fr['TZ'][i])); Nn = (float(fr['NX'][i]), float(fr['NZ'][i]))
            ia = int(np.searchsorted(S, s)); ib = int(np.searchsorted(S, s + Wl))
            A = (fr['X'][ia], fr['Z'][ia]); B = (fr['X'][min(ib, len(S) - 1)], fr['Z'][min(ib, len(S) - 1)])
            dxx, dzz = B[0] - A[0], B[1] - A[1]; ll = math.hypot(dxx, dzz) or 1
            Tn = (dxx / ll * (1 if (dxx * Tn[0] + dzz * Tn[1]) >= 0 else -1), dzz / ll * (1 if (dxx * Tn[0] + dzz * Tn[1]) >= 0 else -1))
            Nn2 = (-Tn[1], Tn[0])
            if Nn2[0] * Nn[0] + Nn2[1] * Nn[1] < 0: Nn2 = (-Nn2[0], -Nn2[1])
            Nn = Nn2
            F = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
            ok = None
            for D in ((42, 34, 28, 22) if fr['lvl'] > 0 else (50, 40, 30)):
                cor = rect_corners(F, Tn, Nn, Wl, D)
                if poly_mask(plan.block, rect_corners(F, Tn, Nn, Wl, D, inset=0.6)): continue
                if poly_mask(plan.occ, rect_corners(F, Tn, Nn, Wl - 0.9, D - 0.9, inset=0.45), 0.0): continue
                hm, sl = terrain_stats(geo, cor)
                if sl > 0.22: continue
                ok = (cor, D, hm, sl); break
            if ok:
                cor, D, hm, sl = ok
                draw_poly(plan.occ, cor, True)
                plan.lots.append({'id': len(plan.lots), 'edge': fr['k'], 'sgn': fr['sgn'], 'lvl': fr['lvl'], 'street': fr['name'], 'rect': [[round(p[0], 2), round(p[1], 2)] for p in cor],
                                  'w': round(Wl, 1), 'd': D, 'y': round(float(np.interp(s + Wl / 2, S, fr['Y'])), 2), 'slope': round(sl, 3), 'kind': 'livre'})
                s += Wl + 0.3
            else:
                s += 5.0


# ---------------------------------------------------------------------------------------------------- planejamento
def plan(city, geo, yn):
    P = Plan()
    P.fronts = build_fronts(city, geo, yn)
    P.block = make_block(city, geo, P)
    P.occ = np.zeros_like(P.block)
    plots = load_plots()
    place_houses(P, geo, plots)
    # rebaixos de guia: intervalo de arco (s) do trecho de rua onde a garagem cruza a calcada
    for h in P.houses:
        lot = h['lot']; T_ = lot['T']; N_ = lot['N']
        fr = next(f for f in P.fronts if f['k'] == h['edge'] and f['sgn'] == h['sgn'])
        # garagem encostada no lado com mais folga (escolhe o lado -T)
        door_u = (h['door'][0] - lot['F'][0]) * T_[0] + (h['door'][1] - lot['F'][1]) * T_[1]
        side = -1.0 if door_u > 0 else 1.0                            # apron do lado oposto ao caminho da porta
        lot['drive_u'] = side * (lot['W'] / 2 - 1.2 - DRV_W / 2)
        # arco da rua: projeta o centro da garagem na frente
        F = lot['F']; u = lot['drive_u']
        cx, cz = F[0] + T_[0] * u, F[1] + T_[1] * u
        q = int(np.argmin((fr['X'] - cx) ** 2 + (fr['Z'] - cz) ** 2))
        sc = float(fr['S'][q])
        lot['drive_s'] = sc
    fill_lots(P, geo)
    P.log.append(f'{len(P.houses)} casas; {len(P.lots)} lotes comuns; {len(P.fronts)} frentes de rua')
    return P


# ---------------------------------------------------------------------------------------------------- terraplenagem (usado por terrain_final.carve)
def plateau_weight(X, Z, pl):
    u = (X - pl['cx']) * pl['tx'] + (Z - pl['cz']) * pl['tz']; v = -(X - pl['cx']) * pl['tz'] + (Z - pl['cz']) * pl['tx']
    du = np.maximum(np.abs(u) - pl['hw'], 0.0); dv = np.maximum(np.abs(v) - pl['hd'], 0.0)
    d = np.hypot(du, dv)
    return d


# ---------------------------------------------------------------------------------------------------- chao do lote: caminho, garagem, cerca, arvores
def build_ground(gr, P):
    import ground
    B = gr.B; geo = gr.geo
    g = gr
    for h in P.houses:
        lot = h['lot']; T_ = lot['T']; N_ = lot['N']; F = lot['F']; W = lot['W']; D = lot['D']
        yf = lot['yfront']; yp = h['y']
        fr_k = h['edge']; sgn = h['sgn']
        def lp(u, v, y): return (F[0] + T_[0] * u + N_[0] * v, y, F[1] + T_[1] * u + N_[1] * v)       # u lateral, v para dentro do lote
        def yat(v): return yf + 0.03 + (yp + 0.03 - yf - 0.03) * min(max(v / 6.0, 0.0), 1.0)
        # --- caminho da porta ate a calcada (reto, na direcao -N a partir da frente da porta)
        door = h['door']
        u_door = (door[0] - F[0]) * T_[0] + (door[1] - F[1]) * T_[1]
        v_door = (door[0] - F[0]) * N_[0] + (door[1] - F[1]) * N_[1]
        lot['walk_u'] = u_door
        steps = max(2, int(max(v_door, 1.0) / 2.0))
        for q in range(steps):
            v0 = v_door * q / steps; v1 = v_door * (q + 1) / steps
            g.quad(PAVER, [lp(u_door - SW / 2, v0, yat(v0)), lp(u_door + SW / 2, v0, yat(v0)), lp(u_door + SW / 2, v1, yat(v1)), lp(u_door - SW / 2, v1, yat(v1))], COLL['conc'], 'lotpath')
        # degrau/soleira na porta
        g.quad(PAVER, [lp(u_door - 1.3, v_door - 0.0, yp + 0.04), lp(u_door + 1.3, v_door - 0.0, yp + 0.04), lp(u_door + 1.3, v_door + 1.2, yp + 0.04), lp(u_door - 1.3, v_door + 1.2, yp + 0.04)], COLL['conc2'], 'lotpath')
        # (sem garagem/rampa: so o caminho da porta ate a calcada)
        ud = lot['drive_u']
        # --- arvores no recuo da frente e nos fundos do lote (a cerca do quintal ja vem com a casa)
        rnd = random.Random(h['k'] * 31 + 7)
        yx0, yz0, yx1, yz1 = h['yard']
        for q in range(4):
            u = rnd.choice([-1, 1]) * (W / 2 - 1.5 - rnd.uniform(0, 1.5)); v = rnd.choice([2.2, D - 1.2, 3.0])
            tx_, tz_ = F[0] + T_[0] * u + N_[0] * v, F[1] + T_[1] * u + N_[1] * v
            if yx0 - 0.5 < tx_ < yx1 + 0.5 and yz0 - 0.5 < tz_ < yz1 + 0.5: continue
            if abs(u - ud) < 2.6 and v < DRV_LEN + 1: continue
            if abs(u - u_door) < 2.0 and v < v_door + 2: continue
            P.trees.append([round(tx_, 1), round(tz_, 1), rnd.choice([0, 1, 1, 3]), round(rnd.uniform(0.8, 1.2), 2), round(rnd.uniform(0, 6.28), 2), round(rnd.uniform(0, 1), 2)])
        # caixa de correio ao lado do caminho
        mx, mz = F[0] + T_[0] * (u_door + 1.4) + N_[0] * 1.0, F[1] + T_[1] * (u_door + 1.4) + N_[1] * 1.0
        B.box(mx, mz, 0.12, 0.12, yf, yf + 1.0, COLL['iron'], METAL, True, False); B.box(mx, mz, 0.38, 0.22, yf + 1.0, yf + 1.28, rgb('#C0392B') if h['k'] % 2 else rgb('#2C3E50'), METAL, True, False)


def seg_box(B, a, b, y0, hgt, th, col, mat=STONE):
    dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz)
    if L < 0.05: return
    ux, uz = dx / L, dz / L; px, pz = -uz * th / 2, ux * th / 2
    B.obox_pts([(a[0] - px, a[1] - pz), (b[0] - px, b[1] - pz), (b[0] + px, b[1] + pz), (a[0] + px, a[1] + pz)], y0, y0 + hgt, col, mat, True, False)


def fence_poly(P, B, h, lot, style, gaps_front, yp):
    T_ = lot['T']; N_ = lot['N']; F = lot['F']; W = lot['W']; D = lot['D']
    def pt(u, v): return (F[0] + T_[0] * u + N_[0] * v, F[1] + T_[1] * u + N_[1] * v)
    # arestas: frente (v=0.15), lados (u=+-W/2), fundo (v=D)
    edges = [('front', (-W / 2 + 0.15, 0.2), (W / 2 - 0.15, 0.2), gaps_front),
             ('side', (-W / 2 + 0.15, 0.2), (-W / 2 + 0.15, D - 0.15), []), ('side', (W / 2 - 0.15, 0.2), (W / 2 - 0.15, D - 0.15), []),
             ('rear', (-W / 2 + 0.15, D - 0.15), (W / 2 - 0.15, D - 0.15), [])]
    hgt, th, col, mat = {'bloco': (1.0, 0.25, COLL['block'], STONE), 'estacas': (1.05, 0.06, COLL['white'], WOOD), 'tijolo': (1.0, 0.3, COLL['brick'], STONE),
                         'madeira': (0.75, 0.1, COLL['wood'], WOOD), 'pedra': (2.0, 0.45, COLL['stone'], STONE), 'ferro': (1.7, 0.06, COLL['iron'], METAL)}[style]
    rails = style in ('estacas', 'madeira', 'ferro')
    for kind, (u0, v0), (u1, v1), gaps in edges:
        a = pt(u0, v0); b = pt(u1, v1)
        L = math.hypot(b[0] - a[0], b[1] - a[1]);
        # intervalos livres ao longo da aresta (parametro em m a partir de a)
        if kind == 'front': cuts = sorted([(g0 - u0, g1 - u0) for g0, g1 in gaps])
        else: cuts = []
        free = []; cur = 0.0
        for g0, g1 in cuts:
            if g0 > cur: free.append((cur, g0))
            cur = max(cur, g1)
        if cur < L: free.append((cur, L))
        ux, uz = (b[0] - a[0]) / (L or 1), (b[1] - a[1]) / (L or 1)
        if style == 'madeira' and kind == 'front': continue       # praia: sem muro na frente
        for f0, f1 in free:
            pa = (a[0] + ux * f0, a[1] + uz * f0); pb = (a[0] + ux * f1, a[1] + uz * f1)
            ln = f1 - f0
            if ln < 0.3: continue
            if style in ('bloco', 'tijolo', 'pedra'):
                seg_box(B, pa, pb, yp - 0.2, hgt + 0.2, th, col, mat)
                seg_box(B, pa, pb, yp + hgt, 0.08, th + 0.1, COLL['white'] if style != 'pedra' else COLL['stone2'], mat)        # tampa
                if style == 'pedra':
                    n = max(1, int(ln // 6))
                    for q in range(n + 1):
                        c = (pa[0] + (pb[0] - pa[0]) * q / n, pa[1] + (pb[1] - pa[1]) * q / n)
                        B.box(c[0], c[1], 0.7, 0.7, yp - 0.2, yp + hgt + 0.5, COLL['stone2'], STONE, True, False)
            else:
                # estacas / madeira / ferro: postes a cada 2,2 m, 2 travessas e ripas
                n = max(1, int(round(ln / 2.2)))
                for q in range(n + 1):
                    c = (pa[0] + (pb[0] - pa[0]) * q / n, pa[1] + (pb[1] - pa[1]) * q / n)
                    B.box(c[0], c[1], 0.12, 0.12, yp - 0.05, yp + hgt + 0.1, col, mat, True, False)
                seg_box(B, pa, pb, yp + hgt * 0.78, 0.06, 0.05, col, mat); seg_box(B, pa, pb, yp + hgt * 0.30, 0.06, 0.05, col, mat)
                step = 0.34 if style == 'estacas' else 0.22
                m = max(1, int(ln / step))
                for q in range(m):
                    c = (pa[0] + (pb[0] - pa[0]) * (q + 0.5) / m, pa[1] + (pb[1] - pa[1]) * (q + 0.5) / m)
                    if style == 'madeira' and q % 2: continue
                    B.box(c[0], c[1], 0.07, 0.07, yp, yp + hgt - (0.12 if style == 'estacas' else 0.0), col, mat, True, False)
            # colisao: pedacos de ~1,2 m (caixas alinhadas aos eixos)
            nloc = max(1, int(ln / 1.2))
            for q in range(nloc):
                c0 = (pa[0] + (pb[0] - pa[0]) * q / nloc, pa[1] + (pb[1] - pa[1]) * q / nloc); c1 = (pa[0] + (pb[0] - pa[0]) * (q + 1) / nloc, pa[1] + (pb[1] - pa[1]) * (q + 1) / nloc)
                P.solids.append([round(min(c0[0], c1[0]) - 0.15, 2), round(min(c0[1], c1[1]) - 0.15, 2), round(max(c0[0], c1[0]) + 0.15, 2), round(max(c0[1], c1[1]) + 0.15, 2)])
    # pilares na entrada da garagem/porta (estilos de muro)
    if style in ('bloco', 'tijolo', 'pedra', 'ferro'):
        for g0, g1 in gaps_front:
            for u in (g0, g1):
                c = pt(u, 0.2)
                B.box(c[0], c[1], 0.45, 0.45, yp - 0.2, yp + hgt + 0.35, COLL['stone2'] if style in ('pedra', 'ferro') else col, STONE, True, False)


def export(P, path):
    out = {'houses': [{'k': h['k'], 'name': h['name'], 'bairro': h['bairro'], 'x': round(h['cx'], 3), 'z': round(h['cz'], 3), 'lvl': round(h['y'], 3), 'box': [round(v, 2) for v in h['box']],
                       'face': 'sul' if h['face'] > 0 else 'norte', 'street': h['street'], 'edge': h['edge'], 'lot': [[round(p[0], 2), round(p[1], 2)] for p in h['lot']['rect']],
                       'lot_w': round(h['lot']['W'], 1), 'lot_d': round(h['lot']['D'], 1), 'door': [round(h['door'][0], 2), round(h['door'][1], 2)], 'yfront': round(h['lot']['yfront'], 2)} for h in P.houses],
           'lots': P.lots, 'solids': P.solids, 'trees': P.trees, 'log': P.log}
    json.dump(out, open(path, 'w'), separators=(',', ':'))
