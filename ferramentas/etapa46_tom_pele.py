#!/usr/bin/env python3
"""Etapa 46: tom de pele dos corpos do Sims 3. O shader do app soma ate ~1.16x de luz em superficies viradas para cima (ombros);
com a pele original (~240,213,204) isso estourava para branco (faixa branca nos ombros/pescoco). Escurece e satura levemente so os pixels de pele
(r > b + 20) de corpo e rosto (area 0..1024 x 0..2048 do atlas); eyes/cabelo/roupas pintadas ficam como estao.
Uso: python3 etapa46_tom_pele.py app/src/main/assets/cute"""
import sys, glob, numpy as np
from PIL import Image
K, SAT = 0.80, 1.12
d = sys.argv[1]
for p in sorted(glob.glob(d + '/sk_*.png')):
    a = np.asarray(Image.open(p).convert('RGB')).astype(np.float64)
    reg = a[0:1024, 0:2048]
    skin = (reg[..., 0] > reg[..., 2] + 20)[..., None]
    L = (reg * np.array([0.299, 0.587, 0.114])).sum(2, keepdims=True)
    new = np.clip((L + (reg - L) * SAT) * K, 0, 255)
    a[0:1024, 0:2048] = np.where(skin, new, reg)
    Image.fromarray(a.round().astype(np.uint8)).save(p, optimize=True)
    print(p.split('/')[-1], 'ok')
