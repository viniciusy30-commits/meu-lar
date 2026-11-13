"""CIDADE 5 "Meular City" v2 - geografia organica. UNICA fonte de verdade. Metros; X leste, Z sul, Y cima."""
import math
RNG = 5005
WX, WZ = 4400.0, 3600.0
CELL = 16.0                       # resolucao dos campos de trabalho (o heightmap final do jogo e de 8 m)
NX, NZ = int(WX / CELL) + 1, int(WZ / CELL) + 1

CITY_CENTER = (2150.0, 2000.0)
BASIN_C, BASIN_R = (2200.0, 1830.0), (1500.0, 1150.0)       # bacia urbana elipse + ruido => cercada de montanhas
LAGOON = (2000.0, 1780.0, 190.0, 110.0)                      # x, z, raio x, raio z  (Praca da Lagoa)

# estreitos (canais) que isolam a cidade; as pontes vermelhas atravessam cada um
CHANNEL_W = {'pts': [(640, 3500), (620, 2700), (570, 2100), (540, 1500), (600, 950), (700, 500), (770, 0)], 'w': 440.0}
CHANNEL_E = {'pts': [(3740, 3500), (3780, 2700), (3850, 2100), (3870, 1500), (3800, 950), (3700, 500), (3640, 0)], 'w': 400.0}
RIVER = {'pts': [(2350, 0), (2330, 350), (2400, 700), (2330, 1050), (2420, 1400), (2340, 1760), (2470, 2100), (2400, 2450), (2460, 2880)], 'w0': 56.0, 'w1': 140.0}

def coast(x):
    """Z da linha da costa (mar para Z maior). Baia ao centro-leste, enseadas e pontas."""
    return 2900.0 + 90 * math.sin(x / 260.0) + 55 * math.sin(x / 97.0 + 1.0) - 380.0 * math.exp(-((x - 2450.0) / 430.0) ** 2) \
        + 120.0 * math.exp(-((x - 3150.0) / 160.0) ** 2)        # ponta de terra (Peninsula Real) a leste da baia

# colinas dentro da bacia: (x, z, altura, sigma)
HILLS = [
    (1550, 1050, 120, 240),   # Alto da Colina (nobre)
    (2650, 1050, 85, 200),    # Parque do Mirante
    (1350, 1700, 45, 170),    # Colina da Igreja
    (3150, 1400, 60, 220),    # Colina Leste
    (2250, 1450, 34, 130),    # morro do centro
    (1250, 2450, 30, 160),    # morro do sul
    (3100, 2350, 38, 130),    # Peninsula Real
    (880, 1450, 34, 150),     # Colina da Ponte Oeste
    (3560, 1450, 34, 150),    # Colina da Ponte Leste
]

# pontes vermelhas suspensas (uma em cada lado) + tuneis nos limites do mapa
RED_BRIDGE_W = {'z': 1500.0, 'x_a': 290.0, 'x_b': 800.0, 'towers': (330.0, 750.0), 'deck': 34.0, 'portal': (90.0, 1420.0)}
RED_BRIDGE_E = {'z': 1500.0, 'x_a': 4100.0, 'x_b': 3640.0, 'towers': (3680.0, 4060.0), 'deck': 34.0, 'portal': (4310.0, 1440.0)}

# hierarquia viaria (largura de calcada a calcada): nome -> (classe do Relevo.kt, largura, dsep tracado, declive max)
LEVELS = [('ave', 1, 28.0, 360.0, 0.09), ('col', 2, 20.0, 150.0, 0.11), ('loc', 3, 15.0, 80.0, 0.14)]

# enseadas (x, z, rx, rz) que recortam a terra para um contorno irregular
COVES = [(1500.0, 2790.0, 190.0, 330.0), (3300.0, 2900.0, 200.0, 420.0)]

# nomes para a previa/GPS (centros aproximados; os bairros definitivos saem do zoneamento da Etapa D)
PLACES = {'Alto da Colina': (1550, 1050), 'Parque do Mirante': (2650, 1050), 'Centro / Praca da Lagoa': (2000, 1780), 'Recanto do Sul (praia)': (1700, 2780),
          'Peninsula Real': (3150, 2420), 'Vila Esperanca': (1250, 1950), 'Colina Leste': (3150, 1400), 'Marina': (1500, 2790), 'Orla Leste': (3300, 2800),
          'Ponte Vermelha Oeste': (540, 1420), 'Ponte Vermelha Leste': (3870, 1420)}
