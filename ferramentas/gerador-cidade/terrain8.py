# Etapa 185 - terreno da Cidade 2 nova (especificação v4)
# Centro no meio (C), mar ao sul com enseada e pontas, rio vindo do norte pelo leste até o mar,
# morros baixos no noroeste (Vila Nova), elevação no sudeste (Alameda), mata e morros fechando o norte.
# Eixos do jogo: x = leste, z = SUL (o norte é -z).
import numpy as np, json, math
from scipy.ndimage import gaussian_filter, map_coordinates, distance_transform_edt
rng = np.random.default_rng(85)
WX, WZ = 2600.0, 2400.0; G = 8.0
NX, NZ = int(WX / G) + 1, int(WZ / G) + 1
xs = np.arange(NX) * G; zs = np.arange(NZ) * G
X, Z = np.meshgrid(xs, zs)
CX0, CZ0 = 1300.0, 1100.0      # Praça Central (ponto zero)
RR = 1000.0                    # raio útil R

def polar(r, deg):
    a = math.radians(deg); return (CX0 + r * RR * math.cos(a), CZ0 - r * RR * math.sin(a))

def gauss(cx, cz, r, h): return h * np.exp(-(((X - cx) ** 2 + (Z - cz) ** 2) / (2 * (r / 2) ** 2)))
def smooth_noise(s, a):
    r = gaussian_filter(rng.standard_normal(X.shape), s / G, mode='reflect'); return a * r / r.std()

# ---------- relevo base: centro plano ~8 m, sobe para o norte e para os cantos
terr = 8.0 + 0.0 * X
terr += gauss(300, 230, 900, 34)        # morros do noroeste (atrás da Vila Nova)
terr += gauss(1300, -110, 900, 30)        # serra do norte (borda verde / mata)
terr += gauss(2500, 230, 800, 30)       # morro do nordeste (além do rio)
terr += gauss(1830, 1670, 520, 13)      # elevação da Alameda das Palmeiras (vista para o mar)
terr += gauss(-150, 1350, 700, 22)       # morro do oeste (esconde o canto)
terr += gauss(2850, 1200, 600, 18)      # morro do leste
terr += gauss(780, 710, 420, 5)        # encosta baixa da Vila Nova
terr += smooth_noise(120, 2.2) + smooth_noise(45, 0.8) + smooth_noise(18, 0.25)
# centro bem plano
dC = np.hypot(X - CX0, Z - CZ0)
flat = np.clip(1 - (dC - 380) / 260, 0, 1); flat = flat * flat * (3 - 2 * flat)
terr = terr * (1 - 0.85 * flat) + 8.0 * 0.85 * flat

# ---------- costa irregular: enseada da Praia do Farol no sul, pontas a SO e SE, costa sobe nos cantos
cz = (2010 + 70 * np.sin(xs / 210 + 0.7) + 35 * np.sin(xs / 83 + 2.1)
      - 140 * np.exp(-((xs - 1300) / 420) ** 2)          # enseada (a água entra)
      + 120 * np.exp(-((xs - 660) / 170) ** 2)          # Ponta do Farol (oeste da enseada)
      + 150 * np.exp(-((xs - 1930) / 200) ** 2)          # ponta da Alameda
      - 520 * np.clip((300 - xs) / 500, 0, 1) ** 1.6     # oeste: costa sobe (esconde o canto SO)
      - 430 * np.clip((xs - 2300) / 400, 0, 1) ** 1.5)   # leste: idem (canto SE)
coast = np.tile(cz, (NZ, 1))
sea = Z > coast
dsea = Z - coast
terr = np.where(dsea > -260, terr * np.clip(-dsea / 260, 0, 1) ** 0.7 + 2.2 * (1 - np.clip(-dsea / 260, 0, 1) ** 0.7), terr)
terr = np.where(sea, -1.0 - np.minimum(dsea, 300) * 0.03, terr)

# ---------- rio: nasce no norte, corre pelo leste (entre o anel e a borda) e deságua a SE
def catmull(P, step=6.0):
    P = [np.array(p, float) for p in P]; P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]; n = max(2, int(np.hypot(*(p2 - p1)) / step))
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2]); return np.array(out)
RIVER = catmull([(1860, -190), (1900, 50), (2000, 280), (2040, 550), (2070, 810), (2040, 1100), (2090, 1360),
                 (2200, 1570), (2300, 1750), (2360, 2000), (2380, 2350)], 6.0)
Rd = np.full(X.shape, 1e9); Rt = np.zeros(X.shape)
for i, (a, b) in enumerate(RIVER[::2]):
    d = np.hypot(X - a, Z - b); m = d < Rd; Rd[m] = d[m]; Rt[m] = i / (len(RIVER) / 2)
RW = 16 + 12 * Rt                      # meia-largura do rio (32 m no norte, 56 m na foz)
riv = Rd < RW
terr = terr - 7 * np.exp(-(Rd / 60) ** 2) * (~sea)   # vale suave
terr = np.where(riv, np.minimum(terr, -0.5), terr)

terr = np.where((~sea) & (~riv), np.maximum(terr, 1.6), terr)
# praia: faixa de areia (altura < 1,3 m) junto ao mar, de largura variável (45 a 75 m)
ds = distance_transform_edt(~sea) * G
bw = 60 + 15 * np.sin(X / 140 + 1.1)
sandk = np.clip(ds / bw, 0, 1)
blend = np.clip((ds - bw) / 60, 0, 1); blend = blend * blend * (3 - 2 * blend)
beach = 0.25 + 0.9 * sandk
terr = np.where((~sea) & (~riv), np.where(ds < bw, beach, terr * blend + 2.0 * (1 - blend)), terr)
water = sea | riv
terr = np.where(water, np.minimum(terr, -0.6), terr)
water_d = distance_transform_edt(~water) * G

def terr_at(px, pz): return float(map_coordinates(terr, [[pz / G], [px / G]], order=1, mode='nearest')[0])
def is_water(px, pz, margin=0):
    if not (0 <= px <= WX and 0 <= pz <= WZ): return True
    ix = int(px / G); iz = int(pz / G); return water_d[min(iz, NZ - 1), min(ix, NX - 1)] <= margin
def coast_at(x): return float(np.interp(x, xs, cz))
