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
    """Z da linha da costa (mar para Z maior): ORLA LONGA e suave (estilo Joao Pessoa), com uma baia rasa no centro (foz do rio)."""
    return 2870.0 + 40 * math.sin(x / 430.0 + 0.6) + 18 * math.sin(x / 190.0 + 1.3) - 175.0 * math.exp(-((x - 2300.0) / 700.0) ** 2)

# ORLA (distancias a partir do mar, em m): areia 0-60, muro/escadas 60-62.5, calcadao 62.5-76.5, jardim 76.5-79.8,
# vagas a 60 graus 79.8-85.5, Av. Beira-Mar (eixo a 97 m, 2x2 faixas + canteiro), calcada do lado da cidade ate ~113 m
ORLA_AXIS = 97.0
ORLA_CALC = 27.5          # eixo do calcadao a 27,5 m do eixo da avenida (lado do mar)
ORLA_URBAN_MIN = 116.0    # ruas da cidade so a partir daqui

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
COVES = []          # (sem enseadas: a orla e uma praia longa e continua)

# nomes para a previa/GPS (centros aproximados; os bairros definitivos saem do zoneamento da Etapa D)
PLACES = {'Alto da Colina': (1550, 1050), 'Parque do Mirante': (2650, 1050), 'Centro / Praca da Lagoa': (2000, 1780), 'Orla Oeste (praia)': (1500, 2700),
          'Peninsula Real': (3150, 2420), 'Vila Esperanca': (1250, 1950), 'Colina Leste': (3150, 1400), 'Orla Leste (praia)': (3100, 2760),
          'Ponte Vermelha Oeste': (540, 1420), 'Ponte Vermelha Leste': (3870, 1420)}
