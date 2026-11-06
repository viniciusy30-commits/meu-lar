"""Etapa 103 - pele Llumisims Mercuria como pele padrao do corpo Sims 4.
Uso: python3 etapa103_mercuria.py <Mercuria.package> <pasta assets/cute>
Camadas da Mercuria: 11 = mulher adulta (rosto+corpo), 46 = homem adulto.
A Mercuria e uma camada de detalhe cinza + alfa; o tom vem da pele atual do app
(mesmo matiz/brilho), multiplicado pelo detalhe. Preserva do atlas antigo: boca/dentes,
olhos, sobrancelhas e roupa de baixo. Preenche o padding preto das ilhas (sem fendas)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sims4'))
import numpy as np, dbpf, lrle
from PIL import Image
from scipy import ndimage as ndi

def lum(x): return x[..., 0]*.3 + x[..., 1]*.59 + x[..., 2]*.11

def build(pkg, idx, cur_path, out_path, male):
    r = dbpf.read(pkg)
    im = lrle.decode(dbpf.data(r[idx]), 0)[0].astype(np.float32)
    cur = np.array(Image.open(cur_path).convert('RGB')).astype(np.float32)
    H, W = cur.shape[:2]
    assert im.shape[:2] == (H, W), (im.shape, cur.shape)
    a = im[..., 3] / 255.0
    g = im[..., :3].mean(-1) / 255.0
    f = (1 - a + a * g)                       # fator de multiplicacao
    black = (a > 0.9) & (g < 0.12)            # padding preto das ilhas
    valid = (a > 0) & ~black
    ys, xs = np.mgrid[0:H, 0:W]
    # roupa de baixo do atlas antigo (cinza-azulada): r-b pequeno
    uw = ((cur[..., 0] - cur[..., 2]) < 70) & (ys > 1000) & (xs < 520)
    uw = ndi.binary_opening(uw, iterations=1)
    uw = ndi.binary_closing(uw, iterations=3)
    # tom: matiz/brilho da pele atual sobre o corpo valido, sem roupa de baixo
    body = valid & (ys > 1040) & ~ndi.binary_dilation(uw, iterations=6) & (a > 0.3)
    tone = np.median(cur[body], axis=0) / np.median(f[body])
    tone = tone * min(1.0, 255.0 / tone.max())      # sem estourar o canal vermelho
    # escuro demais = sobra/padding da Mercuria (vira fresta preta no modelo): tambem e invalido
    dark = (a > 0) & (f < 0.60 * np.median(f[body]))
    dark = ndi.binary_dilation(dark, iterations=2) & (a > 0)
    valid = valid & ~dark
    valid[1024:1470, 722:830] = False      # vao entre os bracos (UV sem uso, so tinha sombra)
    # tira pontinhos e faixas soltas (ilhas pequenas = sobra da Mercuria)
    lab, n = ndi.label(valid)
    sz = ndi.sum(valid, lab, range(1, n + 1))
    big = np.zeros(n + 1, bool); big[1:] = sz >= 6000
    valid = big[lab]
    out = tone[None, None, :] * f[..., None]
    out = np.clip(out, 0, 255)
    # preenche invalidos: sangria do vizinho valido mais proximo
    dist, (iy, ix) = ndi.distance_transform_edt(~valid, return_indices=True)
    bleed = out[iy, ix]
    # cor lisa para areas sem dados (pes, sobras): mediana da canela
    leg = valid & (ys > 1700) & (ys < 1900) & (xs < 380)
    flat = np.median(out[leg], axis=0)
    near = (dist <= 10)[..., None]
    out = np.where(valid[..., None], out, np.where(near, bleed, flat[None, None, :]))
    # topo (y<512) liso na cor da testa; mantem boca/dentes do atlas antigo
    face = valid & (ys > 760) & (ys < 900) & (xs > 420) & (xs < 600)
    fore = np.median(out[face], axis=0)
    top = ys < 512
    out = np.where(top[..., None], fore[None, None, :], out)
    # pecas do atlas antigo: olho (esq), dentes/boca (dir, topo)
    keep = np.zeros((H, W), bool)
    keep[505:625, 0:112] = True
    mouth = (ys < 700) & (xs > 780) & (lum(cur) < 105)
    mouth |= (ys > 500) & (ys < 700) & (xs > 955) & (xs < 1018)
    keep |= ndi.binary_dilation(mouth, iterations=3) & (xs > 780) & (ys < 720)
    keep = ndi.binary_closing(keep, iterations=4)
    out = np.where(keep[..., None], cur, out)
    # sobrancelhas do atlas antigo (escuras sobre a pele)
    bx = (slice(690, 738), slice(380, 650))
    cb = cur[bx]; lb = lum(cb); med = np.median(lb)
    ab = np.clip((med - lb - 12) / max(med - 70, 1), 0, 1) ** 0.8
    ab = ndi.gaussian_filter(ab, 0.6)[..., None]
    out[bx] = out[bx] * (1 - ab) + cb * ab
    # roupa de baixo (suavizada)
    m = ndi.gaussian_filter(ndi.binary_dilation(uw, iterations=1).astype(np.float32), 0.8)[..., None]
    out = out * (1 - m) + cur * m
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGB').save(out_path, optimize=True)
    return tone

if __name__ == '__main__':
    pkg, cute = sys.argv[1], sys.argv[2]
    for idx, name, male in ((11, 'sk_s4f.png', False), (46, 'sk_s4m.png', True)):
        p = os.path.join(cute, name)
        t = build(pkg, idx, p + '.antigo' if os.path.exists(p + '.antigo') else p, p, male)
        print(name, 'tom', t.round(1))
