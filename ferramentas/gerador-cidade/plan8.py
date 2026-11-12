# ===================== Etapa 185: plano da Cidade 2 (especificação v4) =====================
# Centro no meio; 8 radiais; Anel do Núcleo (r=0,15); Circular Interna (r=0,50); bairros em anel (0,55-0,88);
# Circular Externa / Estrada-Parque (r=0,90); Av. Costeira na orla; rio a leste com 3 pontes (P-1, P-2, P-3).
def rpol(x, z): return math.hypot(x - CX0, z - CZ0) / RR
def tpol(x, z): return math.degrees(math.atan2(-(z - CZ0), x - CX0)) % 360.0
def inang(t, a0, a1):
    t = t % 360; a0 = a0 % 360; a1 = a1 % 360
    return (a0 <= t <= a1) if a0 <= a1 else (t >= a0 or t <= a1)
# terreno: plano onde é cidade (mantém a elevação da Alameda e a encosta da Vila Nova, mais suaves)
RRm = np.hypot(X - CX0, Z - CZ0) / RR
mflat = np.clip(1 - (RRm - 0.80) / 0.14, 0, 1); mflat = mflat * mflat * (3 - 2 * mflat)
Tbig = gaussian_filter(terr, 10.0)
Tfl = terr * (1 - 0.75 * mflat) + Tbig * 0.75 * mflat
Tfl = np.where(water, terr, Tfl)
Tfl = np.where(water | (terr < 1.35), terr, np.maximum(Tfl, 1.5))
Tfl_s = gaussian_filter(Tfl, 2.0)
Tfl_s = np.where(terr < 1.35, terr, Tfl_s)
def Th(x, z): return float(map_coordinates(Tfl_s, [[z / G], [x / G]], order=1, mode='nearest')[0])
def plen(P): return float(np.hypot(*np.diff(P, axis=0).T).sum())
def cum(P): return np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
def wdist(x, z):
    if not (0 <= x <= WX and 0 <= z <= WZ): return -1.0
    return float(map_coordinates(water_d, [[z / G], [x / G]], order=1)[0])
import struct, pickle
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra, connected_components
rngN = np.random.default_rng(185)
def _wf(s, a):
    r = gaussian_filter(rngN.standard_normal(X.shape), s / G, mode='wrap'); return a * r / r.std()
WARPX = _wf(300, 14) + _wf(110, 4); WARPZ = _wf(300, 14) + _wf(110, 4)
def warp(P):
    P = np.asarray(P, float); sh = P.shape[:-1]
    ix = np.clip(P[..., 0] / G, 0, NX - 1.001).ravel(); iz = np.clip(P[..., 1] / G, 0, NZ - 1.001).ravel()
    dx = map_coordinates(WARPX, [iz, ix], order=1).reshape(sh); dz = map_coordinates(WARPZ, [iz, ix], order=1).reshape(sh)
    return P + np.stack([dx, dz], -1)
def wd_v(P):
    P = np.asarray(P, float); ix = np.clip(P[:, 0] / G, 0, NX - 1.001); iz = np.clip(P[:, 1] / G, 0, NZ - 1.001)
    d = map_coordinates(water_d, [iz, ix], order=1, mode='nearest')
    out = (P[:, 0] < 0) | (P[:, 0] > WX) | (P[:, 1] < 0) | (P[:, 1] > WZ)
    return np.where(out, -1.0, d)
SLP = np.hypot(*np.gradient(Tfl_s, G))

WIDTH = {0: 20, 1: 18, 2: 13, 3: 9}
defs = []
def R(name, cls, pts, w=None, elev=False, cul=False, bridge=False, snap=60.0, hill=False, smooth=False, bairro=None, wp=True):
    P = np.array(pts, float)
    if smooth: P = catmull([tuple(p) for p in P], 8.0)
    if wp: P = warp(dens(P, 25.0))
    defs.append(dict(name=name, cls=cls, w=(w if w else WIDTH[cls]), pts=P, elev=elev, cul=cul, bridge=bridge, snap=snap, hill=hill, bairro=bairro))

# raio das circulares levemente irregular (contorno orgânico, nada de círculo perfeito)
def rmod(r, deg, amp): return r * (1 + amp * math.sin(math.radians(deg) * 3 + 0.8) + amp * 0.6 * math.sin(math.radians(deg) * 5 + 2.3))
def arc(r, a0, a1, amp=0.035, step=4.0):
    if a1 < a0: a1 += 360
    return [polar(rmod(r, a, amp), a) for a in np.arange(a0, a1 + 1e-6, step)]
def radial(deg, r0, r1, bend=0.0):
    p0 = np.array(polar(rmod(r0, deg, 0.035) if r0 >= 0.5 else r0, deg)); p1 = np.array(polar(rmod(r1, deg, 0.035) if r1 >= 0.5 else r1, deg))
    m = (p0 + p1) / 2; v = p1 - p0; n = np.array([-v[1], v[0]]) / max(np.hypot(*v), 1e-9)
    return [tuple(p0), tuple(m + n * bend), tuple(p1)]

def P_(r, deg, amp=0.035): return polar(rmod(r, deg, amp) if r >= 0.5 else r, deg)
HUBS0 = {'Praça Central': (*polar(0, 0), 42)}
for k, a in enumerate((0, 45, 90, 135, 180, 225, 270, 315)):
    HUBS0[f'Anel do Núcleo {k + 1}'] = (*polar(0.15, a), 15)
for nm, a, r_ in (('Rot. Acácias', 45, 24), ('Rot. Vila Nova', 135, 24), ('Rot. Condomínio', 225, 24), ('Rot. da Orla', 270, 30), ('Rot. Alameda', 315, 24)):
    HUBS0[nm] = (*P_(0.5, a), r_)
for nm, a in (('Entrada Vila Nova', 135), ('Entrada Acácias', 45), ('Entrada Alameda', 315)):
    HUBS0[nm] = (*polar(0.62, a), 15)
HUBS = {}
for k, (hx, hz, hr) in HUBS0.items():
    HUBS[k] = (float(hx), float(hz), hr)
    if wdist(hx, hz) < hr + 30: print('AVISO hub perto da água:', k, round(wdist(hx, hz)))

# ---- Praça Central -> radiais cardeais (Av. Central N/S, Rua Comercial/Transversais L/O)
R('Av. Central Norte', 1, radial(90, 0.0, 0.5), w=20, wp=False)
R('Estrada do Parque Norte', 2, radial(90, 0.5, 0.9, 0) , w=14)
R('Av. Central Sul', 1, radial(270, 0.0, 0.5), w=20, wp=False)
R('Av. Central Sul (Orla)', 1, [P_(0.5, 270), polar(0.62, 271), polar(0.70, 270)], w=18, wp=False)
R('Av. Transversal Leste', 2, radial(0, 0.0, 0.5), w=16, wp=False)
R('Av. Transversal Leste (Ponte P-1)', 2, radial(0, 0.5, 0.9, 10), w=16, bridge=True)
R('Av. Transversal Oeste', 2, radial(180, 0.0, 0.5), w=16, wp=False)
R('Av. Transversal Oeste (Borda)', 2, radial(180, 0.5, 0.9, -10), w=16)
# ---- diagonais: Anel do Núcleo -> Circular Interna -> entrada -> praça do bairro -> Estrada-Parque
for nm, a in (('Av. dos Bairros Leste', 45), ('Av. dos Bairros Oeste', 135), ('Av. do Condomínio', 225), ('Alameda das Palmeiras', 315)):
    w = 16 if a == 315 else 14
    R(nm, 2, radial(a, 0.15, 0.5, 12), w=w)
    R(nm + ' (bairro)', 2, radial(a, 0.5, 0.9, -14), w=w)
# ---- anéis
R('Anel do Núcleo', 2, arc(0.15, 0, 360, 0.0, 3.0), w=13, wp=False, smooth=False)
R('Avenida Circular Interna', 1, arc(0.5, 0, 360, 0.035, 3.0), w=18, wp=False)
R('Estrada-Parque (Circular Externa)', 2, arc(0.9, 300, 240, 0.03, 3.0), w=14, bridge=True, wp=False)
# ---- Av. Costeira: segue a orla da enseada, por trás da faixa de areia
xa, xb = P_(0.9, 240)[0], P_(0.9, 300)[0]
cost = []
for x in np.arange(xa, xb + 1, 30):
    cost.append((x, coast_at(x) - 85 - 25 * math.sin((x - xa) / (xb - xa) * math.pi) * 0))
cost[0] = P_(0.9, 240); cost[-1] = P_(0.9, 300)
cz_ = np.array([c[1] for c in cost]); cz_s = np.convolve(np.pad(cz_, 3, mode='edge'), np.ones(7) / 7, mode='valid')
cost = [(c[0], float(min(z, coast_at(c[0]) - 70))) for c, z in zip(cost, cz_s)]
cost[0] = P_(0.9, 240); cost[-1] = P_(0.9, 300)
R('Avenida Costeira', 1, cost, w=18, wp=False, smooth=True)
# ---- Eixo de Serviços (Av. Logística): duas coletoras paralelas à Av. Central Sul
for sgn, nm in ((-1, 'Av. Logística Oeste'), (1, 'Av. Logística Leste')):
    x = CX0 + sgn * 120
    R(nm, 2, [(x, CZ0 + 0.17 * RR), (x, CZ0 + 0.47 * RR)], w=13, wp=False)
nart = len(defs)

# ---- zonas: grades de ruas locais recortadas pelo formato de cada bairro
def m_centro(x, z): return rpol(x, z) < 0.135
def m_distr(x, z): r = rpol(x, z); return 0.17 < r < 0.47 and not (r > 0.17 and abs(x - CX0) < 140 and z > CZ0 + 0.16 * RR)
def m_serv(x, z): return 0.17 < rpol(x, z) < 0.47 and abs(x - CX0) < 140 and z > CZ0 + 0.16 * RR
def ring(x, z, a0, a1, r0=0.535, r1=0.885):
    r = rpol(x, z); t = tpol(x, z); return r0 < r < r1 and inang(t, a0, a1)
def m_vn(x, z):
    t = tpol(x, z); r = rpol(x, z)
    # leque: abre para fora (mais largo perto da borda)
    w_ = 46 + 34 * (r - 0.53) / 0.35
    return 0.535 < r < 0.885 and abs(((t - 147) + 180) % 360 - 180) < w_
def m_ac(x, z): return ring(x, z, 22, 104) and wdist(x, z) > 40 and x < CX0 + 760
def m_al(x, z): return (ring(x, z, 286, 360) or ring(x, z, 0, 18)) and wdist(x, z) > 40
def m_co(x, z): return ring(x, z, 196, 248, 0.535, 0.80)
def m_or(x, z):
    r = rpol(x, z); t = tpol(x, z)
    return r > 0.535 and inang(t, 247, 288) and z < coast_at(x) - 95
def m_rio(x, z):   # margem leste do rio (Beira-Rio), entre o rio e a Estrada-Parque
    r = rpol(x, z); return r < 0.885 and x > CX0 + 600 and wdist(x, z) > 40 and inang(tpol(x, z), 330, 70) and not m_ac(x, z) and not m_al(x, z)
ZONES = [
    dict(nm='Centro', mask=m_centro, c=(CX0, CZ0), hu=150, hv=150, sx=[72, 78], sz=[72, 78], every=2, w=11, hill=False, sd=1, drop=0.0, cls3=3),
    dict(nm='Distritos do Centro', mask=m_distr, c=(CX0, CZ0), hu=480, hv=480, sx=[92, 100, 108], sz=[92, 100, 108], every=3, w=10, hill=False, sd=2, drop=0.03),
    dict(nm='Distrito de Serviços', mask=m_serv, c=(CX0, CZ0 + 320), hu=140, hv=160, sx=[80, 90], sz=[80, 90], every=99, w=11, hill=False, sd=3, drop=0.0),
    dict(nm='Vila Nova', mask=m_vn, c=polar(0.71, 147), hu=420, hv=420, sx=[66, 72, 78], sz=[66, 72, 78], every=4, w=8.5, hill=True, sd=4, drop=0.03),
    dict(nm='Jardim das Acácias', mask=m_ac, c=polar(0.71, 63), hu=420, hv=420, sx=[84, 92, 100], sz=[84, 92, 100], every=4, w=9, hill=False, sd=5, drop=0.04),
    dict(nm='Alameda das Palmeiras', mask=m_al, c=polar(0.71, 330), hu=420, hv=420, sx=[115, 125, 135], sz=[110, 120, 130], every=99, w=10, hill=True, sd=6, drop=0.04),
    dict(nm='Condomínio Mar Azul', mask=m_co, c=polar(0.67, 222), hu=300, hv=300, sx=[88, 96], sz=[88, 96], every=99, w=8.5, hill=False, sd=7, drop=0.0),
    dict(nm='Orla', mask=m_or, c=polar(0.7, 268), hu=420, hv=260, sx=[82, 90, 98], sz=[78, 86], every=3, w=9, hill=False, sd=8, drop=0.03),
    dict(nm='Beira-Rio', mask=m_rio, c=polar(0.72, 15), hu=360, hv=480, sx=[95, 110], sz=[95, 110], every=99, w=9, hill=False, sd=9, drop=0.05),
]
BMASK = {'Vila Nova': m_vn, 'Jardim das Acácias': m_ac, 'Alameda das Palmeiras': m_al, 'Condomínio Mar Azul': m_co, 'Orla': m_or}
# Condomínio: via circular interna (ilha de quadras)
cc = np.array(polar(0.67, 222))
R('Rua do Condomínio (circular)', 3, [tuple(cc + 105 * np.array([math.cos(a), math.sin(a)])) for a in np.linspace(0, 2 * math.pi, 61)], w=9, wp=False, bairro='Condomínio Mar Azul')
nart = len(defs)
