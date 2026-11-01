#!/usr/bin/env python3
"""
Etapa 7 (correção): repinta o miolo dos olhos no atlas cute/textures.png (tile 256x256 em (1792,512)) e refaz a máscara de cor
(recolor.png / recolor_s.png / linha 'olhos' de recolor.txt) só nesse tile.
Antes: íris com ~65 px de raio ocupava quase toda a abertura, sem esclera nem brilho. Agora: íris menor, pupila, anel externo escuro,
esclera branca sombreada pelas pálpebras e dois brilhos (que não recolorem). Pele e cílios pintados ficam como estavam.
Uso: python3 etapa7_olhos.py <pasta cute> <pasta saída>
"""
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
X0, Y0, S = 1792, 512, 256
CX, CY = 127.6, 128.6          # polo do UV da esfera do olho
RI, RP = 46.0, 17.0            # raio da íris e da pupila (texels)

def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def lum(c): return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]

def main(cute, out):
    os.makedirs(out, exist_ok=True)
    tex = np.asarray(Image.open(os.path.join(cute, 'textures.png')).convert('RGB')).astype(np.float64) / 255
    T = tex[Y0:Y0 + S, X0:X0 + S].copy()
    r, g, b = T[..., 0], T[..., 1], T[..., 2]
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float64)
    d = np.hypot(xx - CX, yy - CY)
    skin = (b > 0.38 * r) & ((r - g) > 0.18) & (r > 0.43)
    lash = (lum(T) < 0.16) & ((r - b) < 0.05) & (d > 40)    # preto neutro dos cílios (a íris escura é amarronzada)
    # só a linha grossa dos cílios: abertura remove o contorno fino da íris antiga; depois recupera as bordas (até 4 px) dentro do preto
    core = ndi.binary_opening(lash, iterations=3)
    lash = ndi.binary_dilation(core, iterations=4, mask=lash)
    lash = ndi.binary_dilation(lash, iterations=1)
    cand = (~skin) & ~lash
    lab, _ = ndi.label(cand)
    ap = lab == lab[int(CY), int(CX)]
    ap = ndi.binary_closing(ap, iterations=2) | (d < RP + 2)
    ap = ndi.binary_fill_holes(ap)
    edge = ndi.distance_transform_edt(ap)
    scl = np.array([0.94, 0.93, 0.94])
    shade = sstep(edge, 0, 24)
    sclera = scl[None, None, :] * (0.55 + 0.45 * shade[..., None])
    t = np.clip(d / RI, 0, 1)
    base = np.array([0.43, 0.17, 0.01])
    light = np.array([0.80, 0.38, 0.03])
    up = np.clip((CY - yy) / RI, -1, 1)
    grad = np.clip(0.5 - 0.5 * up, 0, 1) ** 1.3
    iris = base[None, None, :] * (1 - grad[..., None]) + light[None, None, :] * grad[..., None]
    iris *= (0.75 + 0.25 * sstep(t, 0.0, 0.45))[..., None]
    ring = sstep(t, 0.78, 1.0)
    iris *= (1 - 0.70 * ring)[..., None]
    lid = sstep(edge, 0, 10)
    iris *= (0.55 + 0.45 * lid)[..., None]
    pupil = 1 - sstep(d, RP - 1.0, RP + 1.0)
    iris = iris * (1 - pupil[..., None]) + np.array([0.02, 0.02, 0.03]) * pupil[..., None]
    inside_iris = sstep(RI + 1.2 - d, 0, 2.4)
    eye = sclera * (1 - inside_iris[..., None]) + iris * inside_iris[..., None]
    def blob(cx, cy, rad, soft):
        return 1 - sstep(np.hypot(xx - cx, yy - cy), rad - soft, rad + soft)
    hl = np.clip(blob(CX - 15, CY - 17, 9.0, 2.5) + 0.8 * blob(CX + 15, CY + 14, 4.5, 1.5), 0, 1)
    eye = eye * (1 - hl[..., None]) + hl[..., None]
    k = sstep(edge, 1.0, 3.5) * (1 - lash)
    new = T * (1 - k[..., None]) + eye * k[..., None]
    tex[Y0:Y0 + S, X0:X0 + S] = new
    Image.fromarray(np.round(tex * 255).astype(np.uint8), 'RGB').save(os.path.join(out, 'textures.png'), optimize=True)
    rec = np.asarray(Image.open(os.path.join(cute, 'recolor.png')).convert('RGB')).copy()
    shd = np.asarray(Image.open(os.path.join(cute, 'recolor_s.png')).convert('RGB')).copy()
    w0 = inside_iris * (1 - pupil) * (1 - hl) * k
    sel = w0 > 0.8
    ref = new[sel].mean(0)
    Lr = max(lum(ref), 1e-3)
    Sh = np.clip(lum(new) / Lr, 0, 1.9)
    Sh = np.where(w0 > 0.02, Sh, 0.0)
    tile = rec[Y0:Y0 + S, X0:X0 + S]
    tile[..., 0] = np.round(np.clip(w0, 0, 1) * 255); tile[..., 1] = 0
    tile[..., 2] = np.where(w0 > 0.02, 6, 0)
    gs = np.round(Sh / 2 * 255).astype(np.uint8)
    shd[Y0:Y0 + S, X0:X0 + S] = np.stack([gs, gs, gs], -1)
    Image.fromarray(rec, 'RGB').save(os.path.join(out, 'recolor.png'), optimize=True)
    Image.fromarray(shd, 'RGB').save(os.path.join(out, 'recolor_s.png'), optimize=True)
    lines = open(os.path.join(cute, 'recolor.txt'), encoding='utf-8').read().splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith('6|olhos|'):
            p = ln.split('|'); p[4] = ' '.join('%.1f' % (255 * v) for v in ref); lines[i] = '|'.join(p)
    open(os.path.join(out, 'recolor.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print('ref íris', np.round(ref * 255, 1), 'abertura px', int(ap.sum()))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
