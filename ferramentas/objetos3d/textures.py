"""Texturas procedurais da biblioteca (todas potência de 2). As cores finais vêm da cor do vértice; as texturas
claras/neutras dão só o veio, a trama e a variação."""
import numpy as np, math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex') + '/'

def noise(n, m, sx, sy, seed):
    r = np.random.default_rng(seed).normal(size=(m, n)); r = ndimage.gaussian_filter(r, (sy, sx), mode='wrap')
    return (r - r.min()) / (r.max() - r.min() + 1e-9)

def save(name, a):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(D + name)

def oak():
    n = 512; y, x = np.mgrid[0:n, 0:n] / n
    w = noise(n, n, 40, 1.2, 1) * 0.6 + noise(n, n, 8, 0.6, 2) * 0.4          # veio ao longo de x (u)
    rings = np.sin((y * 38 + w * 6.0 + noise(n, n, 60, 6, 3) * 3) * math.pi)
    fine = noise(n, n, 20, 0.35, 4)
    v = 0.86 + 0.07 * rings + 0.10 * (fine - 0.5) + 0.05 * (noise(n, n, 3, 3, 5) - 0.5)
    pores = (noise(n, n, 6, 0.3, 6) > 0.78) * -0.06
    v = v + pores
    rgb = np.stack([v * 255, v * 236, v * 214], -1)
    save('carvalho.png', rgb)

def linen():
    n = 256; y, x = np.mgrid[0:n, 0:n]
    wx = 0.5 + 0.5 * np.sin(x * 2 * math.pi / 4.0); wy = 0.5 + 0.5 * np.sin(y * 2 * math.pi / 4.0)
    weave = np.where(((x // 4) + (y // 4)) % 2 == 0, wx, wy)
    slub = noise(n, n, 18, 0.6, 7) * 0.5 + noise(n, n, 0.6, 22, 8) * 0.5
    v = 0.80 + 0.10 * weave + 0.12 * (slub - 0.5) + 0.04 * (np.random.default_rng(9).random((n, n)) - 0.5)
    save('linho.png', np.stack([v * 255] * 3, -1))

def glaze():
    n = 256
    sp = (np.random.default_rng(10).random((n, n)) > 0.993) * -0.25
    sp = ndimage.gaussian_filter(sp, 0.6, mode='wrap')
    v = 0.93 + 0.05 * (noise(n, n, 30, 30, 11) - 0.5) + sp
    # escorrido do esmalte (faixas verticais suaves: v = altura)
    drip = noise(n, n, 2.5, 26, 12)
    v = v - 0.06 * np.clip(drip - 0.55, 0, 1) * 2
    save('esmalte.png', np.stack([v * 255] * 3, -1))

def soil():
    n = 256; a = noise(n, n, 1.2, 1.2, 13); b = noise(n, n, 4, 4, 14)
    v = 0.25 + 0.25 * a + 0.12 * b
    chips = noise(n, n, 2.0, 2.0, 15) > 0.82
    rgb = np.stack([v * 120, v * 88, v * 64], -1)
    rgb[chips] = rgb[chips] * 0.5 + np.array([150, 105, 70]) * 0.5
    save('terra.png', rgb)

def cardboard():
    """atlas 512: [0..256)x[0..256) papelão liso; [256..512)x[0..256) face com impressão; faixa inferior: fita adesiva."""
    n = 512; y, x = np.mgrid[0:n, 0:n]
    fl = 0.5 + 0.5 * np.sin(x * 2 * math.pi / 9.0)                      # ondulado do papelão (bem sutil)
    v = 0.88 + 0.03 * fl + 0.08 * (noise(n, n, 6, 6, 16) - 0.5) + 0.05 * (noise(n, n, 40, 1.5, 17) - 0.5)
    rgb = np.stack([v * 214, v * 168, v * 116], -1)
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    ink = (52, 44, 40)
    # face impressa: setas "este lado para cima", taça (frágil), guarda-chuva (manter seco)
    ox, oy = 256, 0
    for k, cx in enumerate((ox + 58, ox + 96)):
        d.polygon([(cx, oy + 34), (cx - 15, oy + 54), (cx - 6, oy + 54), (cx - 6, oy + 80), (cx + 6, oy + 80), (cx + 6, oy + 54), (cx + 15, oy + 54)], fill=ink)
    d.line([(ox + 40, oy + 88), (ox + 114, oy + 88)], fill=ink, width=4)
    gx, gy = ox + 168, oy + 36
    d.polygon([(gx - 18, gy), (gx + 18, gy), (gx + 14, gy + 22), (gx + 3, gy + 30), (gx + 3, gy + 46), (gx + 12, gy + 50), (gx - 12, gy + 50), (gx - 3, gy + 46), (gx - 3, gy + 30), (gx - 14, gy + 22)], outline=ink, width=4)
    d.line([(gx + 2, gy + 3), (gx - 6, gy + 14), (gx + 5, gy + 18)], fill=ink, width=3)
    ux, uy = ox + 214, oy + 46
    d.pieslice([ux - 22, uy - 18, ux + 22, uy + 26], 180, 360, fill=ink)
    d.line([(ux, uy + 4), (ux, uy + 30)], fill=ink, width=4); d.arc([ux - 8, uy + 22, ux + 2, uy + 36], 0, 180, fill=ink, width=4)
    for i in range(6): d.line([(ux - 26 + i * 9, uy - 30), (ux - 30 + i * 9, uy - 22)], fill=ink, width=3)
    d.rectangle([ox + 30, oy + 120, ox + 226, oy + 226], outline=ink, width=3)
    for i in range(5): d.line([(ox + 44, oy + 140 + i * 17), (ox + 44 + [150, 120, 160, 90, 130][i], oy + 140 + i * 17)], fill=(70, 60, 54), width=5)
    # código de barras genérico
    rr = np.random.default_rng(3)
    xx = ox + 140
    while xx < ox + 216:
        w = int(rr.integers(1, 4)); d.rectangle([xx, oy + 200, xx + w - 1, oy + 220], fill=ink); xx += w + int(rr.integers(1, 3))
    # fita adesiva (faixa y 256..320): plástico brilhante bege transparente
    tape = np.array(im).astype(float)
    t = tape[256:320]; t[:] = t * 0.55 + np.array([232, 205, 150]) * 0.45
    t += (noise(n, 64, 30, 0.8, 18)[:, :, None] - 0.5) * 30
    tape[256:320] = t
    im = Image.fromarray(np.clip(tape, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5))
    im.crop((0, 0, 256, 256)).save(D + 'papelao_liso.png')
    pr = np.array(im.crop((256, 0, 512, 256))).astype(float)
    ink = (pr.sum(-1) < 330).astype(float)
    ink = ndimage.gaussian_filter(ink, 0.6)
    rgba = np.dstack([np.full(pr.shape[:2], 54.0), np.full(pr.shape[:2], 46.0), np.full(pr.shape[:2], 42.0), np.clip(ink * 1.6, 0, 1) * 235])
    Image.fromarray(rgba.astype(np.uint8), 'RGBA').save(D + 'papelao_impresso.png')
    im.crop((0, 256, 256, 320)).save(D + 'fita.png')

def ball():
    """bola de borracha: 6 gomos (u) com cores alternadas e costuras; cores na textura (vértice branco)."""
    W, H = 512, 256; y, x = np.mgrid[0:H, 0:W]
    u = x / W; v = y / H
    seg = (u * 6).astype(int) % 6
    cols = np.array([[232, 64, 58], [248, 246, 238], [40, 120, 210], [248, 246, 238], [252, 196, 40], [248, 246, 238]], float)
    rgb = cols[seg]
    edge = np.abs((u * 6) % 1 - 0.5) * 2                     # 1 na costura
    seam = np.clip((edge - 0.965) / 0.035, 0, 1)
    rgb *= (1 - 0.45 * seam)[:, :, None]
    # tampas dos polos: círculo branco com anel
    pole = np.minimum(v, 1 - v)
    cap = pole < 0.11
    rgb[cap] = [244, 242, 234]
    ring = np.abs(pole - 0.11) < 0.008
    rgb[ring] *= 0.6
    rgb *= (0.96 + 0.06 * noise(W, H, 6, 6, 19))[:, :, None]
    save('bola.png', rgb)

def monstera():
    """folha de costela-de-adão (base em coração em cima, ponta embaixo): fendas entre as nervuras e furos; 512x512."""
    n = 512; y, x = np.mgrid[0:n, 0:n].astype(float)
    cx = n / 2
    # contorno: coração largo; r(theta) em coordenadas centradas um pouco acima do meio
    t = np.clip((y - 22) / (500 - 22), 0, 1)
    q = np.clip(t / 0.30, 0, 1); f = (1 - t) ** 0.6 * (0.8 + 1.1 * t) / 0.9 * np.sqrt(1 - (1 - q) ** 2) ** 0.9
    A = ((np.abs(x - cx) < 238 * f) & (y > 22) & (y < 500)).astype(float)
    notch = (np.abs(x - cx) < (34 - (y - 22) * 0.75)) & (y < 70)          # recorte em V onde entra o pecíolo
    A[notch] = 0
    rng = np.random.default_rng(22)
    for side in (-1, 1):
        for k in range(7):
            yy0 = 96 + k * 50 + rng.uniform(-6, 6)
            sl = 0.50 + 0.05 * k                                       # inclinação das nervuras (desce para a ponta)
            # fenda entre esta nervura e a próxima: do meio da lâmina até a borda, alargando
            for s in np.linspace(0.0, 1.0, 90):
                d = 70 + s * 200
                px = cx + side * d; py = yy0 + 22 + d * sl
                r_ = 2.5 + 9.5 * s ** 1.4
                A[(x - px) ** 2 + (y - py) ** 2 < r_ * r_] = 0
            if k < 6:
                d = 46; px = cx + side * d; py = yy0 + 18 + d * sl
                ang = math.atan(sl); ca, sa = math.cos(ang), math.sin(ang)
                u = ((x - px) * ca * side + (y - py) * sa); v = (-(x - px) * sa * side + (y - py) * ca)
                A[(u / 15.0) ** 2 + (v / 6.5) ** 2 < 1] = 0
    A = ndimage.gaussian_filter(A, 0.8)
    base = np.array([34, 96, 44], float); tip = np.array([66, 132, 58], float)
    g = noise(n, n, 22, 22, 20)
    rgb = base * (1 - g[:, :, None] * 0.55) + tip * (g[:, :, None] * 0.55)
    vein = np.exp(-((x - cx) / 4.0) ** 2) * 0.45 * (y > 40)
    for side in (-1, 1):
        for k in range(8):
            yy0 = 96 + k * 50 - 4
            sl = 0.50 + 0.05 * k
            dline = np.abs((y - yy0) - np.abs(x - cx) * sl) / math.sqrt(1 + sl * sl)
            vein = np.maximum(vein, (dline < 2.0) * (side * (x - cx) > 0) * 0.22 * np.exp(-np.abs(x - cx) / 300))
    rgb = rgb * (1 + vein[:, :, None] * 0.7)
    rgb *= (0.88 + 0.16 * (y / n))[:, :, None]
    # brilho cerado perto da nervura
    rgb += (np.exp(-((x - cx) / 90) ** 2) * 14)[:, :, None]
    out = np.dstack([np.clip(rgb, 0, 255), np.clip(A * 255, 0, 255)])
    Image.fromarray(out.astype(np.uint8), 'RGBA').save(D + 'folha_costela.png')

def plain():
    save('liso.png', np.full((8, 8, 3), 255.0))

def brass():
    n = 128; v = 0.9 + 0.1 * noise(n, n, 30, 0.4, 21)
    save('escovado.png', np.stack([v * 255] * 3, -1))

def wood_dark_end():
    pass

if __name__ == '__main__':
    os.makedirs(D, exist_ok=True)
    for f in (oak, linen, glaze, soil, cardboard, ball, monstera, plain, brass): f()
    print(sorted(os.listdir(D)))
