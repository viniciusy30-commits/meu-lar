"""Miniaturas (PNG 160x160 com fundo transparente) da loja, renderizadas a partir dos próprios GLB."""
import sys, os, math
_H = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(_H, '..', 'ambiente'), '/home/claude/work/env'):
    if os.path.isdir(_p): sys.path.insert(0, _p); break
sys.path.insert(0, _H)
import preview as PV
import icon_render as IR
from PIL import Image
IR.OUT = PV.FL.OUT; IR.tex_cache = PV.FL.tex_cache

def thumb(glb, out, yaw=0.62, pitch=0.42, S=320):
    arrs, gj = PV.load_posed(glb, {})
    A = PV.asset_from(arrs, yaw, pitch)
    IR.preview_rgba(A, '/tmp/_t.png', size=(S, S))
    im = Image.open('/tmp/_t.png').convert('RGBA')
    bb = im.getbbox()
    if bb:
        im = im.crop(bb); w, h = im.size; m = max(w, h); sq = Image.new('RGBA', (m, m)); sq.paste(im, ((m - w) // 2, (m - h) // 2)); im = sq
    im.resize((160, 160), Image.LANCZOS).save(out)

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]; os.makedirs(dst, exist_ok=True)
    for f in sorted(os.listdir(src)):
        if f.endswith('.glb'): thumb(os.path.join(src, f), os.path.join(dst, f[:-4] + '.png'))
    print(sorted(os.listdir(dst)))
