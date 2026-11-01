#!/usr/bin/env python3
"""
Etapa 12 - pinta SOBRANCELHAS e dá cor aos LÁBIOS no atlas cute/textures.png (tile do rosto) e ajusta a máscara de cor.

Problema: o tile do rosto do pack não tem sobrancelhas pintadas e os lábios têm quase a mesma cor da pele (só um tom
levemente dessaturado). Resultado no jogo: rosto sem sobrancelha e boca sem cor.

Correção (só pixels do rosto; malha, ossos e animações não mudam):
 - Sobrancelhas: curva em 3D (pose de referência) mapeada para o atlas pelos triângulos da frente do rosto (etapa12_uvmap.py),
   pintada como traço afinando para fora. Entram na região 5 (cabeloFrente) com sombra 0,5: a sobrancelha fica sempre com
   METADE da cor de cabelo escolhida (castanho-avermelhado no padrão; acompanha qualquer cor de cabelo).
 - Lábios: região segmentada por cor no tile, pintada de rosa mantendo o sombreado original; continua na região da pele
   (id 1) com sombra menor, então acompanha o tom de pele escolhido (mais avermelhado que a pele em qualquer tom).
   A linha da boca vira vinho escuro, também na região da pele (com sombra baixa para não clarear em pele clara).
Uso: python3 etapa12_rosto.py <pasta cute> <pasta saída> [previa.png]
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from etapa12_uvmap import FaceUV

HAIR_REF = np.array([212.7, 116.6, 75.2])      # referência da região 5 (cabeloFrente) em recolor.txt
BROW_K = 0.5                                    # sobrancelha = 50% da cor do cabelo
LIP_BASE = np.array([205.0, 92.0, 104.0])       # rosa-coral dos lábios (pele original)
LIP_S = 0.55                                    # sombra (quanto a pele escolhida clareia os lábios)
SEAM = np.array([128.0, 44.0, 56.0])            # linha da boca
SEAM_S = 0.15
LIPBOX = (745, 275, 830, 325)                   # x0 y0 x1 y1 do entorno da boca no atlas

def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def brow_alpha(face, shape, xs=1.5, xe=6.8, y0=167.2, arch=1.15, n=140):
    """Alpha (0..1) das duas sobrancelhas, em pixels do atlas. Curva 3D: começa baixa e grossa no nariz, arco, afina fora."""
    h, w = shape
    A = np.zeros((h, w))
    yy, xx = np.mgrid[0:h, 0:w]
    for side in (1, -1):
        for k in range(n + 1):
            t = k / n
            x = xs + (xe - xs) * t
            y = y0 + arch * np.sin(np.pi * t ** 0.8) - 0.15 * t
            r3 = 0.42 * (1 - 0.72 * t ** 1.2) + 0.05     # meia espessura em unidades do modelo
            p = face.to_px(side * x, y)
            if p is None: continue
            u, v, _ = p
            r = r3 * 12.0
            x0, x1, y0_, y1 = int(u - r - 3), int(u + r + 4), int(v - r - 3), int(v + r + 4)
            sub = np.hypot(xx[y0_:y1, x0:x1] - u, yy[y0_:y1, x0:x1] - v)
            A[y0_:y1, x0:x1] = np.maximum(A[y0_:y1, x0:x1], 1 - sstep(sub, r - 0.9, r + 0.9))
    return A

def main(cute, out, preview=None):
    os.makedirs(out, exist_ok=True)
    tex = np.asarray(Image.open(os.path.join(cute, 'textures.png')).convert('RGB')).astype(np.float64)
    rec = np.asarray(Image.open(os.path.join(cute, 'recolor.png')).convert('RGB')).copy()
    shd = np.asarray(Image.open(os.path.join(cute, 'recolor_s.png')).convert('RGB')).copy()
    face = FaceUV(os.path.join(cute, 'base.bin'))
    new = tex.copy()

    # ---------------- lábios ----------------
    x0, y0, x1, y1 = LIPBOX
    W = tex[y0:y1, x0:x1]
    rg = W[..., 0] - W[..., 1]
    m = ndi.binary_opening(rg < 90, iterations=1)
    lab, n = ndi.label(m)
    big = np.argmax(ndi.sum(m, lab, range(1, n + 1))) + 1
    lip = ndi.binary_fill_holes(lab == big)
    # linha da boca: linha escura no meio dos lábios (já excluída da máscara de pele)
    lum = 0.2126 * W[..., 0] + 0.7152 * W[..., 1] + 0.0722 * W[..., 2]
    rows = np.where(lip)[0]
    seam_row = int(np.argmin(np.where(lip.any(1), lum.min(1), 1e9)))
    seam = np.zeros_like(lip)
    sx = np.where(lip[seam_row])[0]
    seam[seam_row, sx.min() - 1: sx.max() + 2] = True
    lipf = ndi.gaussian_filter(lip.astype(float), 0.7)
    lipf = np.clip(lipf * 1.15, 0, 1)
    # sombreado: usa a luminosidade original dos lábios (parte de cima mais escura que a de baixo)
    lm = lum[lip].mean()
    det = np.clip(lum / lm, 0.85, 1.15)
    ys = np.arange(W.shape[0])[:, None]
    ys_rel = (ys - rows.min()) / max(rows.max() - rows.min(), 1)
    low = np.clip(1.0 + 0.10 * np.exp(-((ys_rel - 0.70) / 0.12) ** 2), 1, 1.2)        # leve brilho no lábio de baixo
    lipcol = np.clip(LIP_BASE[None, None, :] * (det * low)[..., None] ** 1.3, 0, 255)
    tile = new[y0:y1, x0:x1]
    tile[:] = W * (1 - lipf[..., None]) + lipcol * lipf[..., None]
    tile[seam] = SEAM
    # máscara: lábios e linha seguem a pele (id 1, R=255) com sombra menor
    mt = rec[y0:y1, x0:x1]; st = shd[y0:y1, x0:x1]
    mt[lipf > 0.02] = (255, 0, 1)
    mt[seam] = (255, 0, 1)
    s_old = st[..., 2].astype(np.float64) * 2 / 255
    s_old = np.where(lipf > 0.02, np.maximum(s_old, 0.9), s_old)         # sombra original da pele nessa área (~1)
    s_new = s_old * (1 - lipf) + LIP_S * lipf
    s_new = np.where(seam, SEAM_S, s_new)
    g = np.round(np.clip(s_new, 0, 2) / 2 * 255).astype(np.uint8)
    st[...] = np.stack([g, g, g], -1)

    # ---------------- sobrancelhas ----------------
    A = brow_alpha(face, (tex.shape[0], tex.shape[1]))
    # fecha emendas do mapeamento 3D->atlas (faixa clara diagonal no meio da sobrancelha direita)
    core = ndi.binary_closing(A > 0.5, structure=np.ones((3, 3), bool), iterations=4)
    core = ndi.binary_fill_holes(core)
    A = np.maximum(A, core.astype(float))
    brow = HAIR_REF * BROW_K
    # pequeno gradiente: mais escura no miolo, levemente mais clara nas pontas finas (nunca mais clara que o cabelo)
    new = new * (1 - A[..., None]) + brow[None, None, :] * A[..., None]
    sel = A > 0.5
    rec[sel] = (255, 0, 5)
    shd[sel] = np.round(BROW_K / 2 * 255)
    # onde A é fraca (borda) mantém pele; os pixels de borda já misturam um pouco da cor da sobrancelha

    Image.fromarray(np.round(np.clip(new, 0, 255)).astype(np.uint8), 'RGB').save(os.path.join(out, 'textures.png'), optimize=True)
    Image.fromarray(rec, 'RGB').save(os.path.join(out, 'recolor.png'), optimize=True)
    Image.fromarray(shd, 'RGB').save(os.path.join(out, 'recolor_s.png'), optimize=True)
    print('lábios: %d px, linha na linha %d; sobrancelha: %d px' % (lip.sum(), seam_row + y0, sel.sum()))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
