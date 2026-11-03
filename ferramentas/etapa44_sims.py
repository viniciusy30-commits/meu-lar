#!/usr/bin/env python3
"""Etapa 44: todos os corpos do Sims 3 (MTS whiterider Bodies/Faces/Skins): bebe, crianca, jovem, adulto, idoso x feminino/masculino x magro/normal/atletico/gordo.
Uso: python3 etapa44_sims.py <pasta com bodies/ faces/ skins/> <assets/cute>   (precisa de base.bin, heartbeat.png e etapa43_julie.py ao lado)
Gera por variante p_body_<id>.bin (corpo+rosto+couro cabeludo+olhos ligados ao esqueleto do app, normalizado para a altura do adulto; o app escala por SIM_H),
sk_<estagio><sexo>.png (atlas de pele), p_hairback_<estagio><sexo>.bin (Heartbeat ajustado) e simbodies.txt (tabela lida pelo app).
Postura do Sims: bracos para baixo, ao lado do corpo (a malha e' posta assim; os pesos vem da pose original do app)."""
import sys, os, importlib.util
RAWDIR = sys.argv[1]; CUDIR = sys.argv[2]
_here = os.path.dirname(os.path.abspath(__file__))
sys.argv = ['x', RAWDIR, CUDIR]
_spec = importlib.util.spec_from_file_location('e43', os.path.join(_here, 'etapa43_julie.py'))
e = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(e)
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
from scipy.spatial import cKDTree
RAW = RAWDIR.rstrip('/') + '/'; CU = CUDIR.rstrip('/') + '/'
H_ADULT_F = 1.675
ARM_EXTRA = float(os.environ.get('ARM_EXTRA', '30'))   # graus a mais que a pose do app (bracos mais para baixo)

# estagio: (codigo, prefixo de arquivo por sexo, tipos disponiveis {tipo: arquivo corpo}, rosto normal/gordo, couro cabeludo, pele corpo, pele rosto)
# tipos: 0 magro, 1 normal (malha fit: a malha 'normal' do pack vem sem pes e e' quase igual a fit), 3 gordo
def stage_def():
    S = []
    for g, gp in (('f', 'f'), ('m', 'm')):
        S.append(dict(st='a', g=g, body={0: 'a%sBody_thin' % gp, 1: 'a%sBody_fit' % gp, 3: 'a%sBody_fat' % gp},
                      face={'n': 'a%sface' % gp, 'f': 'a%sFace_fat' % gp}, scalp='a%sscalp' % gp, sb='a%sBody' % gp, sf='a%sFace' % gp))
        S.append(dict(st='t', g=g, body={0: 't%sBody_thin' % gp, 1: 't%sBody_fit' % gp, 3: 't%sBody_fat' % gp},
                      face={'n': 't%sFace' % gp, 'f': 't%sFace_fat' % gp}, scalp='t%sScalp' % gp,
                      sb='tfBody' if gp == 'f' else 'amBody', sf='afFace' if gp == 'f' else 'amFace'))
        S.append(dict(st='e', g=g, body={0: 'e%sBody_thin' % gp, 1: 'e%sBody' % gp, 3: 'e%sBody_fat' % gp},
                      face={'n': 'e%sFace' % gp, 'f': 'e%sFace_fat' % gp}, scalp='a%sscalp' % gp, sb='e%sBody' % gp, sf='e%sFace' % gp))
    S.append(dict(st='c', g='u', body={1: 'cuBody', 3: 'cuBody_fat'}, face={'n': 'cuface', 'f': 'cuFace_fat'}, scalp='cuscalp', sb='cuBody', sf='cuFace'))
    S.append(dict(st='p', g='u', body={1: 'puBody'}, face={'n': 'puface', 'f': 'puface'}, scalp='puscalp', sb='puBody', sf='puFace'))
    return S

def dds(name):
    return np.asarray(Image.open(RAW + 'skins/' + name + '.dds').convert('RGB')).astype(float)

def find_eyes(fimg):
    lum = fimg.sum(-1)
    lab, n = ndimage.label(lum < 330)
    c = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if 1500 < len(ys) < 9000 and 250 < ys.mean() < 480: c.append((xs.mean(), ys.mean(), len(ys)))
    c.sort(key=lambda t: -t[2]); c = sorted(c[:2], key=lambda t: t[0])
    assert len(c) == 2, c
    return [(int(a), int(b)) for a, b, _ in c]

def paint_face2(face_rgb, eyes, brows):
    if not brows: return face_rgb.copy()
    base = Image.fromarray(face_rgb.astype(np.uint8)).convert('RGBA')
    L = Image.new('L', (2048, 2048), 0); dr = ImageDraw.Draw(L)
    def brow(cx, cy, sg):
        pts = [(cx + sg * 46, cy - 62), (cx + sg * 22, cy - 76), (cx - sg * 8, cy - 83), (cx - sg * 38, cy - 76), (cx - sg * 66, cy - 60)]
        th = [8, 11, 12, 10, 5]
        P = np.array(pts, float) * 2; t = np.linspace(0, 1, 60)
        xs = np.interp(t, np.linspace(0, 1, len(P)), P[:, 0]); ys = np.interp(t, np.linspace(0, 1, len(P)), P[:, 1]); ws = np.interp(t, np.linspace(0, 1, len(th)), np.array(th) * 2)
        for x, y, w in zip(xs, ys, ws): dr.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=255)
    brow(eyes[0][0], eyes[0][1], 1); brow(eyes[1][0], eyes[1][1], -1)
    L = L.resize((1024, 1024), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2.2))
    a = np.asarray(L).astype(float) / 255 * 0.62
    rgb = np.asarray(base)[..., :3].astype(float)
    rgb = rgb * (1 - a[..., None]) + np.array([78, 52, 38], float) * a[..., None]
    L2 = Image.new('L', (2048, 2048), 0); d2 = ImageDraw.Draw(L2)
    for cx, cy in eyes:
        arc = [(2 * (cx + 50 * np.cos(np.radians(a_))), 2 * (cy - 34 * np.sin(np.radians(a_)))) for a_ in np.linspace(-12, 192, 50)]
        d2.line(arc, fill=255, width=11)
    L2 = L2.resize((1024, 1024), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.6))
    a2 = np.asarray(L2).astype(float) / 255 * 0.55
    return np.clip(rgb * (1 - a2[..., None]) + np.array([46, 32, 28]) * a2[..., None], 0, 255)

def paint_basic(skin, P3, mask, body_m, Hh, female_top, kid):
    """top (so feminino e criancas) + short, pintados na pele, por posicao 3D; proporcoes relativas a altura Hh do corpo"""
    X, Y = P3[..., 0], P3[..., 1]
    pm = body_m['pos']
    sl = lambda y: pm[(np.abs(pm[:, 1] - y) < 0.012 * Hh) & (np.abs(pm[:, 0]) < 0.18 * Hh)]
    ys = np.arange(0.62 * Hh, 0.80 * Hh, 0.004 * Hh)
    wid = [(np.ptp(sl(y)[:, 0]) if len(sl(y)) else 9) for y in ys]; waist = ys[int(np.argmin(wid))]
    if female_top and not kid:
        ys2 = np.arange(0.78 * Hh, 0.85 * Hh, 0.004 * Hh)
        zf = [sl(y)[:, 2].max() if len(sl(y)) else -9 for y in ys2]; bust = ys2[int(np.argmax(zf))]
    else:
        bust = waist + 0.12 * Hh
    ed = 0.0036 * Hh
    def band(a, b): return e.smooth(a - ed, a + ed, Y) * (1 - e.smooth(b - ed, b + ed, Y))
    xl = 1 - e.smooth(0.113 * Hh, 0.125 * Hh, np.abs(X))
    top = (band(waist - 0.01 * Hh, waist + 0.19 * Hh) if kid else band(bust - 0.045 * Hh, bust + 0.05 * Hh)) * xl if female_top else np.zeros_like(Y)
    xs_ = 1 - e.smooth(0.16 * Hh, 0.173 * Hh, np.abs(X))
    hem = 0.68 * waist
    shorts = band(hem, waist - 0.039 * Hh) * xs_
    rng = np.random.RandomState(3)
    n = ndimage.gaussian_filter(rng.randn(*Y.shape), 1.2) * 0.5 + ndimage.gaussian_filter(rng.randn(*Y.shape), 4) * 0.8
    fab = np.array([246, 244, 240], float)[None, None, :] * (1 + 0.02 * n[..., None])
    jeans = np.array([63, 92, 140], float)[None, None, :] * (1 + 0.06 * n[..., None])
    cos = band(waist - 0.039 * Hh - 0.012 * Hh, waist - 0.039 * Hh); bar = band(hem, hem + 0.009 * Hh)
    jeans = jeans * (1 - 0.22 * cos[..., None])
    jeans = jeans * (1 - bar[..., None] * 0.15) + np.array([205, 220, 240]) * bar[..., None] * 0.25
    out = skin.copy()
    out = out * (1 - top[..., None]) + fab * top[..., None]
    out = out * (1 - shorts[..., None]) + jeans * shorts[..., None]
    return np.clip(out, 0, 255)

_brw = {}
def base_weights():
    if 'r' not in _brw:
        br, bidx = e.read_base(); _brw['r'] = br; _brw['t'] = cKDTree(br['pos'].astype(float))
    return _brw['r'], _brw['t']

def weights(P, k=8):
    br, tree = base_weights()
    d, j = tree.query(P, k=k); wn = 1.0 / (d + 0.5) ** 2
    BI = np.zeros((len(P), 4), np.uint8); BW = np.zeros((len(P), 4), np.uint8)
    for v in range(len(P)):
        acc = {}
        for q in range(k):
            for s in range(4):
                w = br['bw'][j[v, q], s]
                if w: acc[int(br['bi'][j[v, q], s])] = acc.get(int(br['bi'][j[v, q], s]), 0) + w * wn[v, q]
        top = sorted(acc.items(), key=lambda a: -a[1])[:4]; tot = sum(a[1] for a in top)
        ws = [int(round(255 * a[1] / tot)) for a in top]; ws[0] += 255 - sum(ws)
        for s, (b, _) in enumerate(top): BI[v, s] = b; BW[v, s] = ws[s]
    return BI, BW

def make_atlas(sd, cache):
    key = sd['st'] + sd['g']
    if key in cache: return cache[key]
    body_n = sd['body'][1] if 1 in sd['body'] else list(sd['body'].values())[0]
    bm = e.load(RAW + 'bodies/%s.obj' % body_n)
    Hh = bm['pos'][:, 1].max()
    fimg = dds(sd['sf']); bimg = dds(sd['sb'])
    eyes = find_eyes(fimg)
    fm = fimg.reshape(-1, 3).mean(0); bmn = bimg.reshape(-1, 3).mean(0)
    bimg = np.clip(bimg * (fm / bmn)[None, None, :], 0, 255)
    P3, mask = e.raster_uv(bm)
    kid = sd['st'] in 'cp'
    female_top = sd['g'] in 'fu' if not kid else True
    bsk = paint_basic(bimg, P3, mask, bm, Hh, female_top, kid)
    bsk = e.fill_outside(bsk, mask)
    fsk = paint_face2(fimg, eyes, brows=(sd['g'] == 'f' and sd['st'] in 'at'))
    atlas = np.zeros((e.AH, e.AW, 3)); atlas[:] = fm
    atlas[0:1024, 0:1024] = bsk; atlas[0:1024, 1024:2048] = fsk
    EB = e.EYE_BLK
    atlas[EB[1]:EB[1] + EB[3], EB[0]:EB[0] + EB[2]] = e.eye_texture()
    hb = np.asarray(Image.open(CU + 'heartbeat.png').convert('RGBA'))[0:128, 512:640]; hair_rgb = hb[..., :3][hb[..., 3] > 200].mean(0)
    hx, hy, hs = e.HAIR_BLK; atlas[hy:hy + hs, hx:hx + hs] = hair_rgb
    cache[key] = (atlas, eyes)
    return cache[key]

def build_variant(sd, typ, cache):
    atlas, eyes = make_atlas(sd, cache)
    body = e.load(RAW + 'bodies/%s.obj' % sd['body'][typ])
    face = e.load(RAW + 'faces/%s.obj' % sd['face']['f' if typ == 3 else 'n'])
    scalp = e.load(RAW + 'faces/%s.obj' % sd['scalp'])
    ratio = body['pos'][:, 1].max() / H_ADULT_F
    hx, hy, hs = e.HAIR_BLK
    def xf(m, ang): return e.pose_arms(e.warp_body(m['pos'] * 100 / ratio), ang_deg=ang)
    A0 = 9.3; A1 = A0 + ARM_EXTRA
    parts = []
    for name, m, xo in (('body', body, 0), ('face', face, 1024), ('scalp', scalp, None)):
        pos = xf(m, A1); idx = m['idx'].copy()
        n, idx = e.vnormals(pos, idx, m['nor'])
        if xo is None: uvA = np.tile([(hx + hs / 2) / e.AW, (hy + hs / 2) / e.AH], (len(pos), 1))
        else: uvA = np.stack([(xo + m['uv'][:, 0] * 1024) / e.AW, ((1 - m['uv'][:, 1]) * 1024) / e.AH], 1)
        parts.append(dict(name=name, pos=pos, nor=n, uv=uvA, idx=idx, lookup=xf(m, A0)))
    eyeP = []
    for (cx, cy) in eyes:
        p, n = e.uv_to_3d(face, cx, cy); pl, _ = e.uv_to_3d(face, cx - 40, cy); pr, _ = e.uv_to_3d(face, cx + 40, cy)
        wid = np.linalg.norm(pl - pr) * 100 / ratio
        r = 0.50 * wid * 0.93
        c = e.warp_body(p[None, :] * 100 / ratio)[0] - n * 0.55 * r
        P, N, UV, I = e.make_sphere(c, r)
        eyeP.append(dict(name='eye', pos=P, nor=N, uv=UV, idx=I, lookup=P))
    for pt in parts + eyeP:
        n = len(pt['pos'])
        if pt['name'] in ('body',):
            BI, BW = weights(pt['lookup']); head = pt['lookup'][:, 1] >= 158; BI[head] = [8, 0, 0, 0]; BW[head] = [255, 0, 0, 0]
        else:
            BI = np.zeros((n, 4), np.uint8); BW = np.zeros((n, 4), np.uint8); BI[:, 0] = 8; BW[:, 0] = 255
        pt['bi'] = BI; pt['bw'] = BW
    return atlas, parts + eyeP, ratio

def write_body(path, parts):
    P = np.vstack([p['pos'] for p in parts]); N = np.vstack([p['nor'] for p in parts]); UV = np.vstack([p['uv'] for p in parts])
    BI = np.vstack([p['bi'] for p in parts]); BW = np.vstack([p['bw'] for p in parts])
    off = np.cumsum([0] + [len(p['pos']) for p in parts])[:-1]
    IDX = np.concatenate([(p['idx'] + o).reshape(-1) for p, o in zip(parts, off)])
    n = len(P); assert n < 65536
    r = np.zeros(n, np.dtype([('pos', '<f4', 3), ('nor', '<f4', 3), ('uv', '<f4', 2), ('col', 'u1', 4), ('bi', 'u1', 4), ('bw', 'u1', 4)]))
    r['pos'] = P; r['nor'] = N; r['uv'] = np.clip(UV, 0, 1); r['col'] = 255; r['bi'] = BI; r['bw'] = BW
    br, bidx = e.read_base(); nt = len(bidx); ymean = br['pos'][bidx][:, :, 1].mean(1); keep = int(np.argmin(ymean))
    hide = np.array([t for t in range(nt) if t != keep], '<u2')
    e.write_piece(path, r, IDX.reshape(-1, 3), hide)
    return n

def main():
    cache = {}; rows = []; hair_done = set(); tex_done = set()
    TY = {0: 'm', 1: 'n', 2: 'a', 3: 'g'}
    for sd in stage_def():
        for typ in sorted(sd['body']):
            vid = '%s%s%d' % (sd['st'], sd['g'], typ)
            atlas, parts, ratio = build_variant(sd, typ, cache)
            n = write_body(CU + 'p_body_%s.bin' % vid, parts)
            tex = 'sk_%s%s.png' % (sd['st'], sd['g'])
            if tex not in tex_done:
                tex_done.add(tex)
                Image.fromarray(np.clip(atlas + 0.5, 0, 255).astype(np.uint8)).save(CU + tex, optimize=True)
            hair = 0
            if sd['st'] in 'ate' and (sd['st'] + sd['g']) not in hair_done and typ == 1:
                hr, hidx = e.build_hair([p for p in parts if p['name'] in ('body', 'face', 'scalp')])
                e.write_piece(CU + 'p_hairback_h%s%s.bin' % (sd['st'], sd['g']), hr, hidx); hair_done.add(sd['st'] + sd['g'])
            hair = 1 if sd['st'] in 'ate' else 0
            rows.append('%s|%s|%s|%d|%.4f|%d' % (vid, sd['st'], sd['g'], typ, ratio, hair))
            print(vid, n, 'verts ratio %.3f' % ratio, flush=True)
    open(CU + 'simbodies.txt', 'w').write('# id|estagio(p c t a e)|sexo(f m u)|tipo(0 magro 1 normal 2 atletico 3 gordo)|altura relativa|tem cabelo\n' + '\n'.join(rows) + '\n')

if __name__ == '__main__': main()
