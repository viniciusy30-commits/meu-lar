"""CIDADE 5 "Meular City" - UNICA fonte de verdade (PROMPT-CIDADE-5-MEULAR-CITY.md). Metros; X leste, Z sul, Y cima."""
import math

RNG = 5005
WX, WZ = 2700.0, 2100.0
G = 8.0
XA = [200.0, 588.0, 976.0, 1364.0, 1752.0, 2140.0]
ZA = [200.0, 588.0, 976.0, 1364.0, 1752.0]
XA_NAME = ["Av. Oeste", "Av. das Flores", "Av. dos Pioneiros", "Av. da República", "Av. do Rio", "Av. Leste"]
ZA_NAME = ["Av. Norte", "Av. dos Jardins", "Av. Central", "Av. do Sul", "Av. Beira-Mar"]

# larguras totais (borda de calçada a borda de calçada)
W_AVE, W_COL, W_LOC, W_HWY, W_MARG, W_ALLEY = 28.0, 20.0, 15.0, 36.0, 20.0, 6.0
CLS = {'ave': 1, 'hwy': 0, 'col': 2, 'loc': 3}          # campo "c" do Relevo.kt
WIDTH = {'ave': W_AVE, 'hwy': W_HWY, 'col': W_COL, 'loc': W_LOC}

# tipo de cada superquadra (i, j): RES / CEN / ESP
SQ_TYPE = {
    (0, 0): 'ESP', (1, 0): 'ESP', (2, 0): 'RES', (3, 0): 'CEN', (4, 0): 'ESP',
    (0, 1): 'RES', (1, 1): 'ESP', (2, 1): 'CEN', (3, 1): 'CEN', (4, 1): 'CEN',
    (0, 2): 'RES', (1, 2): 'CEN', (2, 2): 'CEN', (3, 2): 'CEN', (4, 2): 'CND',
    (0, 3): 'RES', (1, 3): 'ESP', (2, 3): 'CEN', (3, 3): 'ESP', (4, 3): 'ESP',
}
SQ_NAME = {
    (0, 0): 'Alto da Colina', (1, 0): 'Parque do Mirante', (2, 0): 'Jardim Central', (3, 0): 'Distrito Medico', (4, 0): 'Arena Meular',
    (0, 1): 'Parque das Flores (bairro)', (1, 1): 'Parque das Flores', (2, 1): 'Centro Norte', (3, 1): 'Centro Leste', (4, 1): 'Shopping + SuperBom',
    (0, 2): 'Vila Esperanca', (1, 2): 'Distrito de Servicos', (2, 2): 'Centro Oeste', (3, 2): 'Centro Sul', (4, 2): 'Condominio Rio Azul',
    (0, 3): 'Recanto Alto', (1, 3): 'Marina', (2, 3): 'Orla Central', (3, 3): 'Parque Aquatico', (4, 3): 'Parque de Diversoes',
}

def sq_rect(i, j):
    return (XA[i] + 14, ZA[j] + 14, XA[i + 1] - 14, ZA[j + 1] - 14)

# ruas internas: centros (relativos ao canto da SQ)
RES_STREETS = [67.5 + 75 * k for k in range(4)]     # 5 quarteiroes de 60 + 4 ruas de 15
CEN_STREETS = [85.0 + 95 * k for k in range(3)]     # 4 quarteiroes de 75 + 3 ruas de 20

# rotatorias (cruzamentos de avenida): nome -> (x, z, R)
ROUNDS = {
    'Praca Central': (1364.0, 976.0, 48.0),
    'Rotatoria do Mirante': (588.0, 588.0, 30.0),
    'Rotatoria das Flores': (588.0, 976.0, 32.0),
    'Rotatoria Universitaria': (976.0, 588.0, 30.0),
    'Rotatoria do Rio': (1752.0, 976.0, 38.0),
    'Rotatoria do Sul': (976.0, 1364.0, 30.0),
    'Rotatoria do Farol': (1364.0, 1752.0, 44.0),
    'Rotatoria Peninsula': (2560.0, 1752.0, 26.0),
}

# rodovia
HWY_Z_NORTH = 60.0
HWY_ARC_C = (2160.0, 160.0); HWY_ARC_R = 100.0
HWY_X = 2260.0
HWY_Y_DECK = 7.5
HWY_ELEV_Z0, HWY_ELEV_Z1, HWY_RAMP_END = 160.0, 1500.0, 1640.0
MARG_W_X, MARG_E_X = 2222.0, 2298.0
SERVICE_Z = 130.0
RIVER = [(2395, 0), (2395, 500), (2380, 1000), (2395, 1500), (2395, 1830), (2395, 1880)]
RIVER_W = 70.0

# MASCARA DA CIDADE (terra urbana). Contorno organico, sentido horario.
CITY_MASK = [
    (130, 40), (330, 28), (620, 52), (900, 30), (1180, 55), (1232, 60), (1300, 172), (1560, 166), (1640, 50), (1760, 58), (2040, 30), (2250, 48), (2338, 120),
    (2360, 260), (2342, 420), (2366, 600), (2338, 780), (2352, 980), (2336, 1180), (2362, 1380), (2344, 1560), (2368, 1700), (2352, 1820), (2330, 1872),
    # costa sul com baia a sudeste
    (2280, 1900), (2215, 1852), (2150, 1808), (2070, 1812), (2010, 1860), (1960, 1905), (1850, 1884), (1650, 1892),
    (1450, 1868), (1250, 1896), (1050, 1874), (940, 1890), (850, 1720), (848, 1590), (790, 1580), (772, 1720), (750, 1880), (560, 1893), (400, 1858), (290, 1868),
    # cabo a sudoeste
    (195, 1905), (112, 1860), (86, 1790), (124, 1722),
    # serra a oeste
    (96, 1560), (70, 1420), (150, 1320), (262, 1250), (268, 1150), (240, 1070), (110, 1000), (95, 930), (60, 780), (100, 620), (48, 470), (92, 330), (150, 190),
]
MARINA_INLET = [(752, 1700), (772, 1720), (790, 1580), (848, 1590), (850, 1720), (868, 1700), (880, 1960), (740, 1960)]
PENINSULA_MASK = [(2432, 1392), (2540, 1352), (2655, 1376), (2700, 1470), (2692, 1700), (2700, 1790), (2640, 1862), (2520, 1846), (2432, 1810)]

def pip(poly, x, z):
    inside = False; n = len(poly)
    for k in range(n):
        x1, z1 = poly[k]; x2, z2 = poly[(k + 1) % n]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1:
            inside = not inside
    return inside

def in_mask(x, z):
    return pip(CITY_MASK, x, z) or pip(PENINSULA_MASK, x, z)
