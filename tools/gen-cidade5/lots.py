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
MIN_HOUSE_GAP = 22.0                         # distancia minima entre quintais de casas do jogador

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
        self.rej = {}; self.fronts = []; self.lots = []; self.houses = []; self.plateaus = []; self.driveways = {}; self.solids = []; self.trees = []
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


def others_aligned(plan, fr, F, Tn, Nn, Wl, Dl, margin=18.0, tol_deg=4.0):
    """outras calcadas perto do lote (esquinas, ruas dos fundos/lados) precisam ser paralelas ou perpendiculares a frente: a casa nao gira de novo"""
    if not hasattr(plan, '_fp'):
        xs, zs, tx, tz, ks = [], [], [], [], []
        for q, f in enumerate(plan.fronts):
            xs.append(f['X']); zs.append(f['Z']); tx.append(f['TX']); tz.append(f['TZ']); ks.append(np.full(len(f['X']), q))
        plan._fp = (np.concatenate(xs), np.concatenate(zs), np.concatenate(tx), np.concatenate(tz), np.concatenate(ks))
    X, Z, TX, TZ, K = plan._fp
    own = next(q for q, f in enumerate(plan.fronts) if f is fr)
    cx = F[0] + Nn[0] * Dl / 2; cz = F[1] + Nn[1] * Dl / 2; rr = math.hypot(Wl, Dl) / 2 + margin
    m = (np.abs(X - cx) < rr) & (np.abs(Z - cz) < rr) & (K != own)
    if not m.any(): return True
    dx = X[m] - F[0]; dz = Z[m] - F[1]
    u = dx * Tn[0] + dz * Tn[1]; v = dx * Nn[0] + dz * Nn[1]
    near = (np.abs(u) < Wl / 2 + margin) & (v > -margin) & (v < Dl + margin)
    if not near.any(): return True
    dot = np.abs(TX[m][near] * Tn[0] + TZ[m][near] * Tn[1])
    bad = (dot < math.cos(math.radians(tol_deg))) & (dot > math.sin(math.radians(tol_deg)))
    return not bad.any()


def try_house(plan, geo, hp, fr, i, tol_deg, side_m, gap_front, rear_m, slope_max):
    """tenta colocar a casa hp (com o quintal real) na frente fr, indice i; devolve dict do lote ou None.
    Sistema do lote: u = ao longo da rua (T), v = para dentro do lote (N); a frente do quintal (porta/portao) fica a gap_front m da calcada."""
    nx, nz = fr['NX'][i], fr['NZ'][i]
    face = 1.0 if hp['fz'] > 0 else -1.0
    # a casa GIRA: R(yaw) leva a frente (0, face) para -N (frente voltada para a rua). R(yaw)(x, z) = (c x - s z, s x + c z)
    cy, sy = -nz * face, nx * face
    yaw = math.atan2(sy, cy)
    if abs(math.degrees(yaw)) > tol_deg and tol_deg < 180: return None
    tx, tz = fr['TX'][i], fr['TZ'][i]
    x0, x1, z0, z1 = hp['yard']
    rot = lambda x, z: (cy * x - sy * z, sy * x + cy * z)
    cu = []
    for x in (x0, x1):
        for z in (z0, z1):
            rx, rz = rot(x, z); cu.append((rx * tx + rz * tz, rx * nx + rz * nz))        # cantos do quintal (girado) relativos ao centro da casa
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
    if dev > 0.4: return None
    ja = int(np.searchsorted(S, S[i] - Wl / 2 - 12)); jb = min(int(np.searchsorted(S, S[i] + Wl / 2 + 12)), len(S) - 1)           # a calcada nao pode virar mais de ~3 graus em volta do lote
    cdev = np.abs(fr['TX'][ja:jb + 1] * tx + fr['TZ'][ja:jb + 1] * tz)
    if cdev.min() < math.cos(math.radians(3.0)): return None
    cor = rect_corners(F, Tn, Nn, Wl, Dl, inset=0.0)
    if poly_mask(plan.block, rect_corners(F, Tn, Nn, Wl, Dl, inset=0.6)): return None
    if poly_mask(plan.occ, rect_corners(F, Tn, Nn, Wl - 0.9, Dl - 0.9, inset=0.45), 0.0): return None
    if not others_aligned(plan, fr, F, Tn, Nn, Wl, Dl): return None
    hm, sl = terrain_stats(geo, cor)
    if sl > slope_max: return None
    yfront = float(np.interp(S[i], S, fr['Y']))
    if abs(hm - yfront) > 2.6: return None
    C = (F[0] + Tn[0] * u_c + Nn[0] * v_c, F[1] + Tn[1] * u_c + Nn[1] * v_c)
    return {'rect': cor, 'F': F, 'T': Tn, 'N': Nn, 'W': Wl, 'D': Dl, 'C': C, 'yfront': yfront, 'angle': 0.0, 'yaw': yaw, 'cs': cy, 'sn': sy, 'terr': hm, 'slope': sl, 'S': float(S[i]),
            'gap': gap_front}


def rot_pts(pts, C, cs, sn):
    return [(C[0] + cs * x - sn * z, C[1] + sn * x + cs * z) for x, z in pts]


def aabb(q):
    return (min(p[0] for p in q), min(p[1] for p in q), max(p[0] for p in q), max(p[1] for p in q))


def yard_aabb(hp, C, cs, sn):
    x0, x1, z0, z1 = hp['yard']
    return aabb(rot_pts([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], C, cs, sn))


def place_houses(plan, geo, plots):
    order = sorted(range(len(plots)), key=lambda k: -(plots[k]['yard'][1] - plots[k]['yard'][0]) * (plots[k]['yard'][3] - plots[k]['yard'][2]))
    placed = {}
    for k in order:
        hp = plots[k]; bairro = HOUSE_BAIRRO[k]; ax, az = BAIRROS[bairro]
        estate = bairro in ESTATE
        side_m = 4.0 if estate else 2.0; gap_front = 4.0 if estate else 3.0; rear_m = 5.0 if estate else 2.5
        slope_max = 0.16 if bairro == 'Alto da Colina' else 0.12
        best = None
        def far_enough(r):
            a = yard_aabb(hp, r['C'], r['cs'], r['sn'])
            for o in placed.values():
                b = o['yard']
                dx = max(a[0] - b[2], b[0] - a[2], 0); dz = max(a[1] - b[3], b[1] - a[3], 0)
                if math.hypot(dx, dz) < MIN_HOUSE_GAP: return False
            return True
        best = None
        for tol in (180.0,):                                          # a casa gira para ficar reta com a calcada (qualquer rua)
            for radius in (420, 700, 1100, 2000):
                cands = []
                for fr in plan.fronts:
                    if fr['lvl'] == 0 and k not in BEACH_HOUSES: continue
                    d = np.hypot(fr['X'] - ax, fr['Z'] - az)
                    for i in np.nonzero(d < radius)[0][::2]:
                        cands.append((float(d[i]) + (60.0 if fr['lvl'] == 1 else 0.0), fr, int(i)))
                cands.sort(key=lambda t: t[0])
                tried = 0
                for sc, fr, i in cands:
                    r = try_house(plan, geo, hp, fr, i, tol, side_m, gap_front, rear_m, slope_max)
                    tried += 1
                    if r and far_enough(r):
                        r['score'] = sc; r['fr'] = fr; best = r; break
                    if tried > 6000: break
                if best: break
            if best: break
        if not best:
            plan.log.append(f'casa {k + 1}: SEM LOTE'); continue
        fr = best['fr']; plat = best['yfront'] + HOUSE_UP
        face = 1.0 if hp['fz'] > 0 else -1.0
        C = best['C']
        cs, sn = best['cs'], best['sn']
        hw_, hd_ = hp['bw'] / 2, hp['bd'] / 2
        boxq = rot_pts([(-hw_, -hd_), (hw_, -hd_), (hw_, hd_), (-hw_, hd_)], C, cs, sn)
        yx0, yx1, yz0, yz1 = hp['yard']
        yardq = rot_pts([(yx0, yz0), (yx1, yz0), (yx1, yz1), (yx0, yz1)], C, cs, sn)
        box = aabb(boxq); yard = aabb(yardq)
        draw_poly(plan.occ, best['rect'], True)
        door = rot_pts([(hp['fx'], hp['fz'])], C, cs, sn)[0]
        placed[k] = {'k': k, 'name': hp['name'], 'bairro': bairro, 'lot': {kk: best[kk] for kk in ('rect', 'F', 'T', 'N', 'W', 'D', 'yfront', 'angle', 'slope', 'gap')},
                     'cx': C[0], 'cz': C[1], 'y': plat, 'box': box, 'yard': yard, 'boxq': boxq, 'yardq': yardq, 'yaw': best['yaw'], 'cs': cs, 'sn': sn, 'bw': hp['bw'], 'bd': hp['bd'], 'face': face, 'door': door, 'edge': fr['k'], 'sgn': fr['sgn'],
                     's': best['S'], 'street': fr['name'], 'lvl': fr['lvl']}
        plan.log.append(f'casa {k + 1} ({bairro}): lote {best["W"]:.0f}x{best["D"]:.0f} m em ({C[0]:.0f},{C[1]:.0f}) girada {math.degrees(best["yaw"]):.1f} graus declive {best["slope"]*100:.1f}%')
    plan.houses = [placed[k] for k in sorted(placed)]
    for h in plan.houses:
        r = h['lot']['rect']
        cx = sum(p[0] for p in r) / 4; cz = sum(p[1] for p in r) / 4
        plan.plateaus.append({'cx': cx, 'cz': cz, 'tx': h['lot']['T'][0], 'tz': h['lot']['T'][1], 'hw': h['lot']['W'] / 2, 'hd': h['lot']['D'] / 2, 'y': h['y'], 'blend': 9.0, 'k': h['k']})


# ---------------------------------------------------------------------------------------------------- lotes comuns (dados para a Etapa E)
# ---------------------------------------------------------------------------------------------------- loteamento por quadra (v3)
# Cada lado de rua ("frente") e dono da faixa de terreno mais proxima dele (Voronoi das frentes): os lotes de frentes opostas
# encostam os fundos no meio da quadra, como numa cidade de verdade. Cada frente tem um CARATER (largura do lote, recuo,
# familia de construcoes) igual de ponta a ponta: rua de casas iguais, rua comercial, quadra do centro com predios colados.
CHAR = {   # largura (min, max), profundidade (min, max), largura fixa na rua?
    'centro':    ((16, 30), (16, 46), False),
    'centro2':   ((12, 20), (14, 36), False),
    'orla':      ((26, 38), (20, 46), False),
    'avenida':   ((18, 28), (16, 42), False),
    'misto':     ((14, 20), (14, 36), False),
    'suburbio':  ((14.5, 17.5), (15, 36), True),
    'nobre':     ((21, 26), (20, 42), True),
}


def front_char(fr, geo, rnd):
    i = len(fr['X']) // 2; cx, cz = float(fr['X'][i]), float(fr['Z'][i])
    j, ii = geo.idx(cx, cz); Ds = float(geo.Dsea[j, ii]); h = geo.height(cx, cz); sl = geo.slope_at(cx, cz)
    lv = fr['lvl']
    if math.hypot((cx - LAGOON[0]) / 1.15, cz - LAGOON[1]) < 640 and h < 18:
        return 'centro' if lv <= 1 else 'centro2'
    if cz > 2300 and Ds < 300:
        return 'orla' if lv <= 1 else 'suburbio'
    if sl > 0.16 or h > 62: return 'nobre'
    if lv == 0: return 'avenida'
    if lv == 1: return 'misto'
    return 'suburbio'


def block_axes(plan):
    """eixo comprido de cada quadra (componente do terreno livre): so os lados compridos recebem lotes"""
    from scipy import ndimage
    free = ~plan.block & ~plan.occ
    lab, n = ndimage.label(free)
    info = {}
    for k, sl in enumerate(ndimage.find_objects(lab)):
        if sl is None: continue
        sub = lab[sl] == (k + 1); area = int(sub.sum())
        if area < 400: continue
        zz, xx = np.nonzero(sub)
        if area > 20000:
            sel = np.random.RandomState(k).choice(len(xx), 20000, replace=False); zz, xx = zz[sel], xx[sel]
        xx = xx + sl[1].start + 0.5; zz = zz + sl[0].start + 0.5
        mx, mz = xx.mean(), zz.mean()
        ev, evec = np.linalg.eigh(np.cov(np.stack([xx - mx, zz - mz])))
        U = evec[:, 1]; V = np.array([-U[1], U[0]])
        pu = (xx - mx) * U[0] + (zz - mz) * U[1]; pv = (xx - mx) * V[0] + (zz - mz) * V[1]
        Lu = np.percentile(pu, 99) - np.percentile(pu, 1); Lv = np.percentile(pv, 99) - np.percentile(pv, 1)
        info[k + 1] = (U, Lu, Lv, area)
    return lab, info

def fill_condos(plan, geo, rnd):
    """miolo de superquadra sem rua: condominio. Vielas internas de bloquete (7 m) a cada duas fileiras de lotes,
    lotes de frente para a viela, mesma familia de casa (ou predios, no centro) no condominio inteiro."""
    from scipy import ndimage
    H, W = plan.block.shape
    free = ~plan.block & ~plan.occ
    free = ndimage.binary_erosion(free, iterations=2)
    lab, n = ndimage.label(free)
    plan.lanes = getattr(plan, 'lanes', [])
    ncond = 0; nlot = 0
    for k, sl in enumerate(ndimage.find_objects(lab)):
        if sl is None: continue
        sub = lab[sl] == (k + 1); area = int(sub.sum())
        if area < 5000: continue
        zz, xx = np.nonzero(sub)
        if len(xx) > 30000:
            sel = np.random.RandomState(k).choice(len(xx), 30000, replace=False); zz, xx = zz[sel], xx[sel]
        xx = xx + sl[1].start + 0.5; zz = zz + sl[0].start + 0.5
        mx, mz = float(xx.mean()), float(zz.mean())
        ev, evec = np.linalg.eigh(np.cov(np.stack([xx - mx, zz - mz])))
        U = evec[:, 1]; V = np.array([-U[1], U[0]])
        pu = (xx - mx) * U[0] + (zz - mz) * U[1]; pv = (xx - mx) * V[0] + (zz - mz) * V[1]
        u0, u1 = float(pu.min()), float(pu.max()); v0, v1 = float(pv.min()), float(pv.max())
        if u1 - u0 < 45 or v1 - v0 < 30: continue
        cx, cz = mx, mz
        j, i = geo.idx(cx, cz)
        centro = math.hypot((cx - LAGOON[0]) / 1.15, cz - LAGOON[1]) < 700 and geo.height(cx, cz) < 22
        if geo.slope_at(cx, cz) > 0.2: continue
        if centro: Wl, Dl, ch = rnd.choice((26.0, 30.0)), 30.0, 'condo_predio'
        else: Wl, Dl, ch = rnd.choice((15.0, 16.0, 17.0)), rnd.choice((24.0, 26.0, 28.0)), 'condo'
        LANE = 7.0
        style = rnd.random(); fcol = rnd.random()
        period = 2 * Dl + LANE + 0.6
        # posicao das vielas: centralizadas na faixa disponivel
        nper = max(1, int((v1 - v0) / period))
        vstart = v0 + ((v1 - v0) - nper * period) / 2
        placed_c = 0
        for p in range(nper):
            vl0 = vstart + p * period + Dl + 0.3                 # viela entre vl0 e vl0+LANE
            vl1 = vl0 + LANE
            span = []
            for (sd, vf) in ((-1, vl0), (+1, vl1)):           # sd=-1: lote acima da viela (fundo para -V)
                Nn = (float(V[0] * sd), float(V[1] * sd))
                Tn = (float(U[0]), float(U[1]))
                nl = int((u1 - u0 - 4) / Wl)
                us = u0 + ((u1 - u0) - nl * Wl) / 2
                for q in range(nl):
                    uc = us + Wl * (q + 0.5)
                    P = np.array([mx, mz]) + U * uc + V * vf
                    F = (float(P[0]), float(P[1]))
                    cor = rect_corners(F, Tn, Nn, Wl - 0.4, Dl)
                    if poly_mask(plan.block, cor): continue
                    if poly_mask(plan.occ, rect_corners(F, Tn, Nn, Wl - 1.0, Dl - 1.0, inset=0.5), 0.0): continue
                    if not all(free[min(H - 1, max(0, int(c[1]))), min(W - 1, max(0, int(c[0])))] for c in cor): continue
                    hm, slp = terrain_stats(geo, cor)
                    if slp > 0.09: continue
                    draw_poly(plan.occ, cor, True)
                    plan.lots.append({'id': len(plan.lots), 'edge': -1, 'sgn': 1, 'lvl': 2, 'street': '', 'rect': [[round(c[0], 2), round(c[1], 2)] for c in cor],
                                      'w': round(Wl - 0.4, 1), 'd': Dl, 'y': round(hm, 2), 'slope': round(slp, 3), 'kind': 'livre', 'char': ch,
                                      'front': 100000 + k, 'setback': 4.5, 'style': round(style, 3), 'pos': q, 'inner': True, 'fcol': round(fcol, 3)})
                    span.append(q); placed_c += 1
            # viela so entre lotes vizinhos (trechos continuos), e so onde o chao e livre
            qs = sorted(set(span)); runs = []
            for q in qs:
                if runs and q == runs[-1][1] + 1: runs[-1][1] = q
                else: runs.append([q, q])
            for (qa, qb) in runs:
                if qb - qa < 1: continue
                a_, b_ = us + Wl * qa, us + Wl * (qb + 1)
                ca = [np.array([mx, mz]) + U * uu + V * vv for (uu, vv) in ((a_, vl0), (b_, vl0), (b_, vl1), (a_, vl1))]
                cc = [(float(c[0]), float(c[1])) for c in ca]
                if poly_mask(plan.block, cc): continue
                if terrain_stats(geo, cc)[1] > 0.09: continue                 # viela em ladeira: nao (os lotes ficam com acesso pelo gramado)
                plan.lanes.append([list(c) for c in cc])
                draw_poly(plan.occ, cc, True)
        if placed_c:
            ncond += 1; nlot += placed_c
    plan.log.append(f'condominios no miolo das superquadras: {ncond} ({nlot} lotes, {len(plan.lanes)} vielas)')


def subdivide(plan, geo, seed=RNG + 3):
    from scipy.spatial import cKDTree
    rnd = random.Random(seed)
    H, W = plan.block.shape
    G = 2                                                     # raster de dono a cada 2 m
    PX = []; FI = []
    for fi, fr in enumerate(plan.fronts):
        for i in range(len(fr['S'])):
            PX.append((fr['X'][i], fr['Z'][i])); FI.append(fi)
    PX = np.array(PX); FI = np.array(FI)
    tree = cKDTree(PX)
    gz, gx = np.mgrid[0:H:G, 0:W:G]
    free = ~plan.block[::G, ::G]
    q = np.stack([gx[free] + 0.5, gz[free] + 0.5], 1)
    dist, idx = tree.query(q, distance_upper_bound=60.0)
    owner = np.full(free.shape, -1, np.int32)
    ok = np.isfinite(dist)
    tmp = np.full(len(q), -1, np.int32); tmp[ok] = FI[idx[ok]]
    owner[free] = tmp
    plan.owner = owner
    # largura da quadra em cada ponto da frente: anda pela normal ate bater na rua do outro lado (mascara de bloqueio)
    blk = plan.block
    for fi, fr in enumerate(plan.fronts):
        across = np.zeros(len(fr['S']))
        for i in range(len(fr['S'])):
            x0, z0, nx, nz = fr['X'][i], fr['Z'][i], fr['NX'][i], fr['NZ'][i]
            t = 1.5
            while t < 130.0:
                x, z = int(x0 + nx * t), int(z0 + nz * t)
                if x < 0 or z < 0 or x >= W or z >= H or blk[z, x]: break
                t += 1.0
            across[i] = t - 1.5
        fr['across'] = across
        fr['char'] = front_char(fr, geo, rnd)
        fr['len'] = float(fr['S'][-1] - fr['S'][0])
    # ---- quadras regulares: duas fileiras de lotes iguais, fundos encostados no eixo da quadra
    for fr in plan.fronts:
        (wmin, wmax), _, fixed = CHAR[fr['char']]
        fr['Wf'] = rnd.uniform(wmin, wmax)
        fr['setback'] = {'suburbio': rnd.choice((5.0, 5.5, 6.0, 6.5)), 'nobre': rnd.choice((7.5, 8.5, 9.5)), 'misto': rnd.choice((3.0, 4.0, 5.0))}.get(fr['char'], 0.0)
        fr['style'] = rnd.random()
    lab, binfo = block_axes(plan)
    nskip = 0
    for fr in plan.fronts:
        i = len(fr['X']) // 2
        x, z = int(fr['X'][i] + fr['NX'][i] * 4), int(fr['Z'][i] + fr['NZ'][i] * 4)
        fr['skip'] = False
        if not (0 <= x < W and 0 <= z < H): continue
        c = int(lab[z, x]); bi = binfo.get(c)
        if not bi: continue
        U, Lu, Lv, area = bi
        fr['comp'] = c
        if Lu > 170 or area > 16000: continue                       # quadra grande/irregular: todos os lados sao frente
        tdot = abs(fr['TX'][i] * U[0] + fr['TZ'][i] * U[1])
        if tdot < 0.6: fr['skip'] = True; nskip += 1                  # lado curto da quadra: esquina vira jardim
    plan.log.append(f'lados curtos de quadra sem lote: {nskip}')
    for fi in sorted(range(len(plan.fronts)), key=lambda q: (plan.fronts[q].get('skip', False), -plan.fronts[q]['len'])):
        fr = plan.fronts[fi]
        ch = fr['char']; (wmin, wmax), (dmin, dmax), fixed = CHAR[ch]
        S = fr['S']
        Wf = fr['Wf']
        s = S[0] + 0.5
        while s < S[-1] - 6:
            Wl = Wf + rnd.uniform(-0.25, 0.25) if fixed else rnd.uniform(wmin, wmax)
            if s + Wl > S[-1]:
                Wl = S[-1] - s                                   # ultimo lote da frente: o que sobrar (se der)
                if Wl < wmin * 0.8: break
            ia = int(np.searchsorted(S, s)); ib = min(int(np.searchsorted(S, s + Wl)), len(S) - 1)
            A = (fr['X'][ia], fr['Z'][ia]); B = (fr['X'][ib], fr['Z'][ib])
            dxx, dzz = B[0] - A[0], B[1] - A[1]; ll = math.hypot(dxx, dzz) or 1
            Tn = (dxx / ll, dzz / ll); Nn = (-Tn[1], Tn[0])
            im = (ia + ib) // 2
            if Nn[0] * fr['NX'][im] + Nn[1] * fr['NZ'][im] < 0: Nn = (-Nn[0], -Nn[1])
            F = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
            A = float(np.min(fr['across'][ia:ib + 1]))
            Dav = (A - 0.6) if A < 2 * dmin + 1.0 else (A / 2.0 - 0.4)       # quadra estreita: lote de rua a rua; senao fundos no meio
            D = min(dmax, Dav)
            placed = False
            while D >= dmin:
                cor = rect_corners(F, Tn, Nn, ll, D)
                if poly_mask(plan.block, rect_corners(F, Tn, Nn, ll, D, inset=0.6)): plan.rej['block'] = plan.rej.get('block', 0) + 1; D -= 2; continue
                if poly_mask(plan.occ, rect_corners(F, Tn, Nn, ll - 1.6, D - 1.2, inset=0.8), 0.0): plan.rej['occ'] = plan.rej.get('occ', 0) + 1; D -= 2; continue
                hm, sl = terrain_stats(geo, cor)
                if sl > 0.22: plan.rej['slope'] = plan.rej.get('slope', 0) + 1; break
                draw_poly(plan.occ, cor, True)
                plan.lots.append({'id': len(plan.lots), 'edge': fr['k'], 'sgn': fr['sgn'], 'lvl': fr['lvl'], 'street': fr['name'], 'rect': [[round(p[0], 2), round(p[1], 2)] for p in cor],
                                  'w': round(ll, 1), 'd': round(D, 1), 'y': round(float(np.interp(s + Wl / 2, S, fr['Y'])), 2), 'slope': round(sl, 3), 'kind': 'livre',
                                  'char': ch, 'front': fi, 'setback': fr['setback'], 'style': round(fr['style'], 3), 'pos': fr.setdefault('nlot', 0)}); fr['nlot'] += 1
                placed = True; break
            s += (Wl + 0.4) if placed else 2.0
    fill_condos(plan, geo, rnd)
    # miolo fundo (mais de 60 m de qualquer rua) ou sobra entre lotes: mata/bosque
    deep = free & (owner < 0)
    jj, ii = np.nonzero(deep[::6, ::6])
    nw = 0
    for j, i in zip(jj, ii):
        x = i * 6 * G + rnd.uniform(0, 6 * G); z = j * 6 * G + rnd.uniform(0, 6 * G)
        if 0 <= int(z) < H and 0 <= int(x) < W and not plan.occ[int(z), int(x)] and not plan.block[int(z), int(x)] and not geo.is_water(x, z) and geo.slope_at(x, z) < 0.5:
            plan.trees.append([round(x, 1), round(z, 1), rnd.choice((0, 1, 1, 3, 3)), round(rnd.uniform(0.9, 1.35), 2), round(rnd.uniform(0, 6.28), 2), round(rnd.uniform(0, 1), 2)]); nw += 1
    plan.log.append(f'loteamento v3: {len(plan.lots)} lotes; mata no miolo: {nw} arvores')


def fill_gaps(plan, geo, seed=RNG + 7):
    """preenche o miolo das quadras: grade de candidatos do mais proximo da rua para dentro; cada lote alinhado a rua mais proxima"""
    from scipy.spatial import cKDTree
    rnd = random.Random(seed)
    pts = []; info = []
    for fr in plan.fronts:
        for i in range(0, len(fr['S']), 2):
            pts.append((fr['X'][i], fr['Z'][i])); info.append((fr['TX'][i], fr['TZ'][i], fr['NX'][i], fr['NZ'][i], fr['lvl']))
    if not pts: return
    tree = cKDTree(np.array(pts)); info = np.array(info)
    H, W = plan.block.shape
    free = ~plan.block & ~plan.occ
    ys, xs = np.nonzero(free[::4, ::4]); xs = xs * 4; ys = ys * 4
    d, idx = tree.query(np.stack([xs, ys], 1))
    order = np.argsort(d)
    added = 0
    for o in order:
        x, z = float(xs[o]), float(ys[o])
        if plan.occ[int(z), int(x)] or plan.block[int(z), int(x)]: continue
        k = int(idx[o]); tx, tz, nx, nz, lv = info[k]
        px, pz = pts[k]
        if (x - px) * nx + (z - pz) * nz < 0: nx, nz = -nx, -nz
        T_ = (-nz, nx); N_ = (nx, nz)
        for Wl, D in ((26, 30), (22, 28), (20, 24), (18, 22), (16, 20), (14, 16)):
            Wl = Wl + rnd.uniform(-1.5, 1.5)
            F = (x - N_[0] * D / 2, z - N_[1] * D / 2)
            cor = rect_corners(F, T_, N_, Wl, D)
            if poly_mask(plan.block, rect_corners(F, T_, N_, Wl, D, inset=0.6)): continue
            if poly_mask(plan.occ, rect_corners(F, T_, N_, Wl - 0.9, D - 0.9, inset=0.45), 0.0): continue
            hm, sl = terrain_stats(geo, cor)
            if sl > 0.20: continue
            draw_poly(plan.occ, cor, True)
            plan.lots.append({'id': len(plan.lots), 'edge': -1, 'sgn': 1, 'lvl': 2, 'street': '', 'rect': [[round(p[0], 2), round(p[1], 2)] for p in cor],
                              'w': round(Wl, 1), 'd': D, 'y': round(hm, 2), 'slope': round(sl, 3), 'kind': 'livre', 'inner': True}); added += 1
            break
    plan.log.append(f'miolo: +{added} lotes')

      base = newl

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
    subdivide(P, geo)
    P.log.append(f'rejeicoes de lote: {P.rej}')
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
    out = {'houses': [{'k': h['k'], 'name': h['name'], 'bairro': h['bairro'], 'x': round(h['cx'], 3), 'z': round(h['cz'], 3), 'lvl': round(h['y'], 3), 'yaw': round(h['yaw'], 5), 'box': [round(v, 2) for v in h['box']], 'boxq': [[round(p[0], 2), round(p[1], 2)] for p in h['boxq']], 'yardq': [[round(p[0], 2), round(p[1], 2)] for p in h['yardq']],
                       'face': 'sul' if h['face'] > 0 else 'norte', 'street': h['street'], 'edge': h['edge'], 'lot': [[round(p[0], 2), round(p[1], 2)] for p in h['lot']['rect']],
                       'lot_w': round(h['lot']['W'], 1), 'lot_d': round(h['lot']['D'], 1), 'door': [round(h['door'][0], 2), round(h['door'][1], 2)], 'yfront': round(h['lot']['yfront'], 2)} for h in P.houses],
           'lots': P.lots, 'solids': P.solids, 'trees': P.trees, 'lanes': getattr(P, 'lanes', []), 'log': P.log}
    json.dump(out, open(path, 'w'), separators=(',', ':'))
