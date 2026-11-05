"""Pré-visualização a partir do próprio GLB (relido do disco): prova que o arquivo contém o que foi modelado."""
import sys, os, math
import numpy as np
_H = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(_H, '..', 'ambiente'), '/home/claude/work/env'):
    if os.path.isdir(_p): sys.path.insert(0, _p); break
import flora_lib as FL
FL.OUT = os.path.dirname(os.path.abspath(__file__)) + '/'
FL.tex_cache = lambda name, _c={}: _c.setdefault(name, np.asarray(__import__('PIL.Image').Image.open(FL.OUT + 'tex/' + name).convert('RGBA')))
import glb_lib as G
from PIL import Image


def asset_from(arrs, yaw, pitch, anim=None):
    A = FL.Asset('x'); cy, sy = math.cos(yaw), math.sin(yaw); cp, sp = math.cos(pitch), math.sin(pitch)
    def rot(Q):
        x = Q[:, 0] * cy + Q[:, 2] * sy; z = -Q[:, 0] * sy + Q[:, 2] * cy; y = Q[:, 1]
        return np.stack([x, y * cp - z * sp, y * sp + z * cp], 1)
    for key, P, N, C, UV, T in arrs: A.add(key, rot(P), rot(N), C, UV, T)
    return A


def render(path, out, views=((0.6, 0.42), (-0.6, 0.42), (math.pi - 0.5, 0.35)), size=380, anim=None):
    arrs, gj = load_posed(path, anim or {})
    ims = []
    allP = np.vstack([a[1] for a in arrs]); ext = (allP.max(0) - allP.min(0)).max() * 1.25
    for yaw, pitch in views:
        A = asset_from(arrs, yaw, pitch); FL.preview(A, '/tmp/_p.png', views=('front',), size=(size, size), span=ext)
        ims.append(Image.open('/tmp/_p.png').copy())
    S = Image.new('RGB', (size * len(ims), size)); [S.paste(im, (i * size, 0)) for i, im in enumerate(ims)]; S.save(out)


def load_posed(path, anim, skip_fx=False):
    """relê o GLB aplicando valores de animação {nó: valor} (dobradiça = ângulo, trilho = deslocamento, escala)."""
    gj, bin_ = G.read_glb(path)
    for i, nd in enumerate(gj['nodes']):
        an = nd.get('extras', {}).get('anim')
        if an and nd['name'] in anim:
            v = anim[nd['name']]; ax = np.array(an['eixo'], float)
            if an['tipo'] == 'dobradica':
                q = [ax[0] * math.sin(v / 2), ax[1] * math.sin(v / 2), ax[2] * math.sin(v / 2), math.cos(v / 2)]; nd['rotation'] = q
            elif an['tipo'] == 'trilho':
                nd['translation'] = list(np.array(nd.get('translation', [0, 0, 0])) + ax * v)
            elif an['tipo'] == 'escala':
                nd['scale'] = list(np.where(ax > 0, v, 1.0))
    W = G.world_mats(gj); out = []
    for i, nd in enumerate(gj['nodes']):
        if 'mesh' not in nd: continue
        if skip_fx and ('efeito' in nd.get('extras', {}) or 'mostrar_quando' in nd.get('extras', {})): continue
        for pr in gj['meshes'][nd['mesh']]['primitives']:
            at = pr['attributes']; m = gj['materials'][pr['material']]
            P = G.accessor(gj, bin_, at['POSITION']).astype(float); N = G.accessor(gj, bin_, at['NORMAL']).astype(float)
            UV = G.accessor(gj, bin_, at['TEXCOORD_0']).astype(float); C = G.accessor(gj, bin_, at['COLOR_0']).astype(float)
            T = G.accessor(gj, bin_, pr['indices']).astype(int).reshape(-1, 3)
            P = (W[i][:3, :3] @ P.T).T + W[i][:3, 3]; N = (W[i][:3, :3] @ N.T).T
            ex = m['extras']; out.append(((ex['tex'], ex['mt'], ex['cut']), P, N, C, UV, T))
    return out, gj


if __name__ == '__main__':
    render(sys.argv[1], sys.argv[2])
