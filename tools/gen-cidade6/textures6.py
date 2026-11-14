"""Cidade 6 - texturas procedurais (512 px, JPEG) e tabela de materiais.
Cada material: textura + quantos metros a textura cobre (escala do UV no mundo). A cor do vertice multiplica a textura:
texturas 'tingiveis' (siding, reboco, telha, folhagem...) sao claras e recebem a cor da casa; as naturais (asfalto, grama,
areia, tijolo, vidro...) ja tem a cor certa e usam vertice branco."""
import os, math
import numpy as np
from PIL import Image, ImageFilter

N = 512
RNG = np.random.RandomState(7)


def vnoise(n, cells, seed):
    r = np.random.RandomState(seed); g = r.rand(cells + 1, cells + 1); g[-1, :] = g[0, :]; g[:, -1] = g[:, 0]
    t = np.linspace(0, cells, n, endpoint=False); i = t.astype(int); f = t - i; f = f * f * (3 - 2 * f)
    a = g[i][:, i]; b = g[i][:, i + 1]; c = g[i + 1][:, i]; d = g[i + 1][:, i + 1]
    fx = f[None, :]; fy = f[:, None]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(n, base=4, oct=5, seed=0):
    s = np.zeros((n, n)); amp = 1.0; tot = 0
    for o in range(oct):
        s += vnoise(n, base * 2 ** o, seed + o * 13) * amp; tot += amp; amp *= 0.5
    return s / tot


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def col(rgb, v):
    return np.dstack([v * rgb[0], v * rgb[1], v * rgb[2]])


# ---------------------------------------------------------------- texturas
def asfalto():
    n1 = fbm(N, 8, 5, 1); sp = RNG.rand(N, N)
    v = 0.30 + 0.10 * n1 + (sp > 0.93) * 0.10 - (sp < 0.04) * 0.08
    patch = (fbm(N, 3, 3, 9) > 0.62) * 0.04                     # remendos levemente mais escuros
    v = v - patch
    return col((235, 236, 240), v)


def calcada():
    n1 = fbm(N, 6, 5, 2); sp = RNG.rand(N, N)
    v = 0.80 + 0.07 * n1 + (sp > 0.97) * 0.04 - (sp < 0.02) * 0.05
    y, x = np.mgrid[0:N, 0:N]
    j = ((x % (N // 2)) < 3) | ((y % (N // 2)) < 3)              # junta a cada 1,5 m (textura = 3 m)
    v = np.where(j, v * 0.70, v)
    # leve variacao por placa
    pl = (np.floor(x / (N // 2)) * 7 + np.floor(y / (N // 2)) * 3) % 4
    v = v * (0.97 + pl * 0.012)
    return col((238, 234, 226), v)


def paver():
    y, x = np.mgrid[0:N, 0:N]
    bh = N // 16; bw = N // 8
    row = y // bh; off = (row % 2) * (bw // 2)
    bx = (x + off) % bw; by = y % bh
    j = (bx < 3) | (by < 3)
    idv = ((x + off) // bw * 31 + row * 17) % 7
    base = 0.72 + idv * 0.025 + 0.06 * fbm(N, 10, 4, 3)
    v = np.where(j, 0.45, base)
    c = np.dstack([v * 228, v * 214, v * 196])
    return c


def grama():
    n1 = fbm(N, 6, 6, 4); n2 = fbm(N, 24, 3, 5); sp = RNG.rand(N, N)
    g = 0.55 + 0.25 * n1 + 0.12 * n2 + (sp > 0.9) * 0.08
    img = np.dstack([g * 112, g * 168, g * 74])
    # pequenas lâminas mais claras
    img[..., 1] += (sp > 0.985) * 40
    return img


def areia():
    n1 = fbm(N, 5, 5, 6); sp = RNG.rand(N, N)
    y, x = np.mgrid[0:N, 0:N]
    rip = 0.04 * np.sin((x * 0.06 + n1 * 9))
    v = 0.84 + 0.08 * n1 + rip + (sp > 0.95) * 0.05 - (sp < 0.03) * 0.06
    return col((240, 224, 182), v)


def agua():
    n1 = fbm(N, 4, 4, 8); n2 = fbm(N, 32, 3, 11); n3 = fbm(N, 16, 3, 12)
    v = 0.80 + 0.10 * n1 + 0.08 * n3
    rip = np.clip((n2 - 0.58) * 5, 0, 1) * 0.22
    return np.dstack([v * 64 + rip * 150, v * 128 + rip * 120, v * 178 + rip * 70])


def tijolo():
    y, x = np.mgrid[0:N, 0:N]
    bh = N // 24; bw = N // 8
    row = y // bh; off = (row % 2) * (bw // 2)
    bx = (x + off) % bw; by = y % bh
    j = (bx < 4) | (by < 3)
    idv = (((x + off) // bw) * 13 + row * 7) % 9
    n1 = fbm(N, 16, 4, 12)
    r = 150 + idv * 6 + n1 * 30; g = 72 + idv * 3 + n1 * 15; b = 54 + n1 * 12
    m = 200 + n1 * 20
    return np.dstack([np.where(j, m, r), np.where(j, m * 0.97, g), np.where(j, m * 0.92, b)])


def siding():
    y, x = np.mgrid[0:N, 0:N]
    bh = N // 12                                                  # 12 tabuas por 2,4 m (20 cm)
    t = (y % bh) / bh
    v = 0.92 + 0.05 * fbm(N, 8, 3, 13) - 0.22 * (t > 0.86) + 0.05 * t
    v -= 0.03 * fbm(N, 32, 2, 14)
    return col((255, 255, 255), v)


def reboco():
    v = 0.90 + 0.06 * fbm(N, 10, 5, 15) + 0.03 * (RNG.rand(N, N) - 0.5)
    return col((255, 255, 255), v)


def telha_shingle():
    y, x = np.mgrid[0:N, 0:N]
    rh = N // 12; tw = N // 10
    row = y // rh; off = ((row * 37) % 5) * tw // 5
    tx = (x + off) % tw; ty = (y % rh) / rh
    v = 0.62 + 0.10 * fbm(N, 20, 3, 16) + 0.08 * (((x + off) // tw * 11 + row * 5) % 5) / 5
    v = v - 0.25 * (ty > 0.85) - 0.18 * (tx < 3)
    v += (RNG.rand(N, N) - 0.5) * 0.08
    return col((235, 235, 235), v)


def telha_ceramica():
    y, x = np.mgrid[0:N, 0:N]
    cw = N // 8; rh = N // 6
    cx = (x % cw) / cw; cy = (y % rh) / rh
    bulge = np.sin(cx * math.pi)
    v = 0.55 + 0.38 * bulge - 0.25 * (cy > 0.88) + 0.05 * fbm(N, 12, 3, 17)
    return np.dstack([v * 205, v * 105, v * 70])


def fachada_vidro():
    """parede-cortina: 2 baias de 1,5 m x 1 andar de 3,6 m por textura (u=3 m, v=3,6 m)"""
    y, x = np.mgrid[0:N, 0:N]
    g = 0.5 + 0.35 * (1 - y / N) + 0.15 * fbm(N, 3, 3, 18)
    r = 70 * g; gg = 115 * g; b = 150 * g + 30
    mull = ((x % (N // 2)) < 8) | ((y % N) < 10) | (np.abs(y - N * 0.78) < 4)
    spand = y > N * 0.80
    img = np.dstack([r, gg, b])
    img[spand] = (np.array([96, 110, 122])[None, :] * (0.9 + 0.1 * fbm(N, 8, 2, 19)[spand][:, None]))
    img[mull] = (200, 204, 208)
    return img


def fachada_janelas():
    """predio residencial: 1 baia de 3 m x 1 andar de 3 m; parede clara (tingivel) com janela, peitoril e verga"""
    y, x = np.mgrid[0:N, 0:N]
    v = 0.93 + 0.04 * fbm(N, 10, 4, 20)
    img = col((255, 255, 255), v)
    wx0, wx1, wy0, wy1 = int(N * 0.22), int(N * 0.78), int(N * 0.22), int(N * 0.70)
    win = (x >= wx0) & (x < wx1) & (y >= wy0) & (y < wy1)
    gl = 0.55 + 0.35 * (1 - (y - wy0) / (wy1 - wy0)) * 0.6 + 0.1 * fbm(N, 4, 2, 21)
    img[win] = np.dstack([gl * 85, gl * 115, gl * 140])[win]
    frame = win & (((x - wx0) < 10) | ((wx1 - x) < 10) | ((y - wy0) < 10) | ((wy1 - y) < 10) | (np.abs(x - N // 2) < 5))
    img[frame] = (236, 236, 232)
    sill = (x >= wx0 - 14) & (x < wx1 + 14) & (y >= wy1) & (y < wy1 + 14)
    img[sill] = (205, 200, 192)
    shadow = (x >= wx0) & (x < wx1) & (y >= wy1 + 14) & (y < wy1 + 22)
    img[shadow] = img[shadow] * 0.86
    return img


def fachada_escritorio():
    """faixa continua de janelas (fita) + peitoril de concreto: 3 m x 3,6 m"""
    y, x = np.mgrid[0:N, 0:N]
    v = 0.86 + 0.05 * fbm(N, 8, 3, 22)
    img = col((240, 238, 232), v)
    band = (y > N * 0.18) & (y < N * 0.72)
    g = 0.55 + 0.4 * (1 - (y - N * 0.18) / (N * 0.54)) + 0.1 * fbm(N, 3, 2, 23)
    img[band] = np.dstack([g * 72, g * 98, g * 118])[band]
    mull = band & ((x % (N // 3)) < 6)
    img[mull] = (60, 64, 70)
    return img


def vitrine():
    y, x = np.mgrid[0:N, 0:N]
    g = 0.5 + 0.4 * (y / N) + 0.1 * fbm(N, 4, 2, 24)
    img = np.dstack([g * 60, g * 80, g * 95])
    # reflexo diagonal
    refl = (np.abs(((x + y) % (N // 2)) - N // 4) < N // 18)
    img[refl] = img[refl] * 1.35
    fr = ((x % (N // 2)) < 10) | (y < 10) | (y > N - 12)
    img[fr] = (52, 54, 58)
    return img


def madeira():
    y, x = np.mgrid[0:N, 0:N]
    pw = N // 6
    plank = y // pw
    grain = 0.06 * np.sin(x * 0.05 + fbm(N, 6, 3, 25) * 12 + plank * 2)
    v = 0.70 + grain + 0.06 * fbm(N, 24, 2, 26) + (plank % 3) * 0.03
    v = np.where((y % pw) < 4, 0.4, v)
    return np.dstack([v * 190, v * 140, v * 95])


def pedra():
    """muro de pedra: celulas de Voronoi (pedras) com argamassa"""
    y, x = np.mgrid[0:N, 0:N]
    r = np.random.RandomState(40); k = 70
    P = r.rand(k, 2) * N
    P = np.vstack([P + (dx, dy) for dx in (-N, 0, N) for dy in (-N, 0, N)])
    best = np.full((N, N), 1e9); second = np.full((N, N), 1e9); idx = np.zeros((N, N), int)
    for i, (px, py) in enumerate(P):
        d = (x - px) ** 2 + (y - py) ** 2
        m = d < best
        second = np.where(m, best, np.minimum(second, d)); idx = np.where(m, i % k, idx); best = np.where(m, d, best)
    edge = np.sqrt(second) - np.sqrt(best)
    tone = (idx * 37 % 11) / 11.0
    v = 0.58 + 0.16 * tone + 0.10 * fbm(N, 16, 3, 41)
    v = v * (0.8 + 0.2 * np.clip(edge / 12, 0, 1))
    v = np.where(edge < 3.0, 0.42, v)
    return np.dstack([v * 205, v * 196, v * 180])


def concreto():
    v = 0.80 + 0.06 * fbm(N, 6, 5, 29) + 0.02 * (RNG.rand(N, N) - 0.5)
    y, x = np.mgrid[0:N, 0:N]
    v = np.where(((y % (N // 2)) < 2) | ((x % (N // 2)) < 2), v * 0.88, v)
    for (px, py) in ((N * 0.25, N * 0.25), (N * 0.75, N * 0.25), (N * 0.25, N * 0.75), (N * 0.75, N * 0.75)):   # furos de forma
        v = np.where(((x - px) ** 2 + (y - py) ** 2) < 30, v * 0.75, v)
    return col((240, 238, 234), v)


def cascalho():
    sp = RNG.rand(N, N); v = 0.55 + 0.25 * fbm(N, 40, 2, 31) + (sp > 0.8) * 0.1 - (sp < 0.15) * 0.1
    return col((220, 218, 214), v)


def folhagem():
    n1 = fbm(N, 10, 5, 32); sp = RNG.rand(N, N)
    v = 0.62 + 0.32 * n1 + (sp > 0.92) * 0.12 - (sp < 0.08) * 0.15
    return col((255, 255, 255), v)


def janela_casa():
    """janela de casa (moldura branca, 2 folhas com divisao): UV 0..1 por janela"""
    y, x = np.mgrid[0:N, 0:N]
    img = np.zeros((N, N, 3)) + (240, 240, 236)
    gx0, gx1, gy0, gy1 = 28, N - 28, 28, N - 28
    gl = (x > gx0) & (x < gx1) & (y > gy0) & (y < gy1)
    g = 0.55 + 0.35 * (1 - y / N) + 0.1 * fbm(N, 3, 2, 33)
    img[gl] = np.dstack([g * 90, g * 120, g * 145])[gl]
    bars = gl & ((np.abs(x - N // 2) < 9) | (np.abs(y - N // 2) < 7) | (np.abs(x - N // 4) < 4) | (np.abs(x - 3 * N // 4) < 4))
    img[bars] = (240, 240, 236)
    refl = gl & (np.abs((x - y) % (N // 2) - N // 4) < 14)
    img[refl] = np.minimum(img[refl] * 1.3, 255)
    return img


def porta():
    y, x = np.mgrid[0:N, 0:N]
    v = 0.8 + 0.05 * fbm(N, 8, 3, 34)
    img = col((255, 255, 255), v)
    for (a, b, c, d) in ((0.15, 0.45, 0.08, 0.45), (0.55, 0.85, 0.08, 0.45), (0.15, 0.45, 0.55, 0.92), (0.55, 0.85, 0.55, 0.92)):
        m = (x > a * N) & (x < b * N) & (y > c * N) & (y < d * N)
        img[m] *= 0.86
        e = m & ((x < a * N + 6) | (y < c * N + 6))
        img[e] *= 0.8
    kn = ((x - 0.88 * N) ** 2 + (y - 0.55 * N) ** 2) < 120
    img[kn] = (200, 175, 90)
    return img


def garagem():
    y, x = np.mgrid[0:N, 0:N]
    v = 0.86 + 0.04 * fbm(N, 8, 3, 35)
    v = np.where((y % (N // 5)) < 6, 0.62, v)
    v = np.where((y % (N // 5)) > (N // 5) - 4, 0.95, v)
    return col((255, 255, 255), v)


def metal():
    v = 0.75 + 0.06 * fbm(N, 4, 4, 36); y, x = np.mgrid[0:N, 0:N]
    v = np.where((x % (N // 8)) < 3, v * 0.8, v)
    return col((255, 255, 255), v)


def casca():
    y, x = np.mgrid[0:N, 0:N]
    v = 0.55 + 0.2 * fbm(N, 6, 4, 37) + 0.12 * np.sin(x * 0.12 + fbm(N, 4, 3, 38) * 10)
    return np.dstack([v * 150, v * 112, v * 80])


def quadra():
    """piso de quadra esportiva (verde com textura fina)"""
    v = 0.85 + 0.05 * fbm(N, 20, 3, 39)
    return np.dstack([v * 70, v * 140, v * 100])


def cerca():
    """cerca de tabuas verticais (madeira clara envelhecida, tingivel)"""
    y, x = np.mgrid[0:N, 0:N]
    bw = N // 8
    board = x // bw
    v = 0.86 + 0.05 * np.sin(y * 0.03 + board * 1.7 + fbm(N, 8, 3, 44) * 6) + 0.03 * ((board * 7) % 3)
    v = np.where((x % bw) < 4, 0.55, v)
    v = np.where((np.abs(y - N * 0.2) < 6) | (np.abs(y - N * 0.8) < 6), v * 0.9, v)
    return np.dstack([v * 236, v * 214, v * 184])


def terreno():
    """solo neutro (tingido pela cor do vertice: grama, areia, rocha)"""
    sp = RNG.rand(N, N)
    v = 0.80 + 0.12 * fbm(N, 8, 5, 42) + 0.06 * fbm(N, 40, 2, 43) + (sp > 0.93) * 0.05 - (sp < 0.06) * 0.06
    return col((255, 255, 255), v)


def branco():
    return np.full((64, 64, 3), 255.0)


# nome: (funcao, metros por repeticao (u, v))
MATS = {
    'asfalto': (asfalto, (7.0, 7.0)), 'calcada': (calcada, (3.0, 3.0)), 'paver': (paver, (2.4, 2.4)), 'grama': (grama, (6.0, 6.0)),
    'areia': (areia, (5.0, 5.0)), 'agua': (agua, (12.0, 12.0)), 'tijolo': (tijolo, (2.4, 2.4)), 'siding': (siding, (2.4, 2.4)),
    'reboco': (reboco, (3.0, 3.0)), 'telha': (telha_shingle, (3.0, 3.0)), 'ceramica': (telha_ceramica, (2.0, 2.0)),
    'vidro': (fachada_vidro, (3.0, 3.6)), 'janelas': (fachada_janelas, (3.0, 3.0)), 'escritorio': (fachada_escritorio, (3.0, 3.6)),
    'vitrine': (vitrine, (3.0, 3.0)), 'madeira': (madeira, (2.0, 2.0)), 'pedra': (pedra, (2.5, 2.5)), 'concreto': (concreto, (3.0, 3.0)),
    'cascalho': (cascalho, (2.0, 2.0)), 'folhagem': (folhagem, (2.0, 2.0)), 'janela': (janela_casa, (1.0, 1.0)), 'porta': (porta, (1.0, 1.0)),
    'garagem': (garagem, (1.0, 1.0)), 'metal': (metal, (2.0, 2.0)), 'casca': (casca, (1.0, 1.0)), 'quadra': (quadra, (4.0, 4.0)),
    'cerca': (cerca, (1.6, 1.8)), 'terreno': (terreno, (8.0, 8.0)), 'liso': (branco, (1.0, 1.0)),
}


def make_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    for k, (fn, sc) in MATS.items():
        p = os.path.join(outdir, k + '.jpg')
        img = to_img(fn())
        img.save(p, quality=88)
    return outdir


if __name__ == '__main__':
    import sys
    d = make_all(sys.argv[1] if len(sys.argv) > 1 else '/tmp/tex6')
    # prancha de conferencia
    ks = list(MATS); cols = 7; s = 160
    sheet = Image.new('RGB', (cols * s, ((len(ks) + cols - 1) // cols) * (s + 18)), 'white')
    from PIL import ImageDraw
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(ks):
        im = Image.open(os.path.join(d, k + '.jpg')).resize((s, s))
        sheet.paste(im, ((i % cols) * s, (i // cols) * (s + 18)))
        dr.text(((i % cols) * s + 4, (i // cols) * (s + 18) + s + 2), k, fill='black')
    sheet.save(os.path.join(d, '_prancha.png'))
    print('ok', len(ks))
