"""Etapa 15 - lábios viram região própria (id 8, slot 12 "Lábios") nas máscaras de cor.
Uso: python3 etapa15_labios.py <pasta cute>   (reescreve recolor.png, recolor_s.png e acrescenta a linha 8 em recolor.txt)"""
import sys, os, numpy as np
from PIL import Image
cute = sys.argv[1]
rp, sp = os.path.join(cute, 'recolor.png'), os.path.join(cute, 'recolor_s.png')
rec = np.asarray(Image.open(rp).convert('RGB')).copy(); shd = np.asarray(Image.open(sp).convert('RGB')).copy()
x0, y0, x1, y1 = 745, 275, 830, 325
r = rec[y0:y1, x0:x1]; s = shd[y0:y1, x0:x1]
lip = (r[..., 0] == 255) & (r[..., 1] == 0) & (r[..., 2] == 1) & (s[..., 0] < 100)
r[lip] = (255, 0, 8)
seam = lip & (s[..., 0] < 30)
s[lip & ~seam] = 128; s[seam] = 19
Image.fromarray(rec, 'RGB').save(rp, optimize=True); Image.fromarray(shd, 'RGB').save(sp, optimize=True)
t = os.path.join(cute, 'recolor.txt'); txt = open(t).read()
if '\n8|' not in txt: open(t, 'a').write('8|labios|12|-1|205.0 92.0 104.0|0.0 0.0 0.0\n')
print('pixels de lábio:', int(lip.sum()), 'linha da boca:', int(seam.sum()))
