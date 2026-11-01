#!/usr/bin/env python3
"""
Etapa 5 do Meu Lar: sapatos, luvas, chapéus, óculos, barbas e acessórios de cabeça do pack BoZo -> peças CUP1 + atlas "extra2" recolorível.
Uso: python3 etapa5_extra.py <pasta de trabalho com fbxr.py, clothes_lib.py, idx.pkl e pk/up> <saída = assets/cute>
- Peças com esqueleto no FBX (sapatos, luvas, barbas): pesos dos clusters do FBX (osso 'Jaw' e olhos -> cabeça; 'calf_twist_01_l1' -> canela).
- Peças sem esqueleto (chapéus, óculos, chifres, antena): espaço local da cabeça (como os cabelos): posição + HEAD, 100% osso da cabeça.
- Regiões de cor (extra2_recolor.txt): 1 = barba (slots Cabelo/Pontas), 4 = sapatos (slots 7 e 8), 5 = acessórios (slots 10 e 11), 6 = lentes escuras (slots 10 e 11).
Máscara do pack: R = cor 1, G+B = cor 2 (igual às Etapas 3 e 4).
"""
import sys, os, struct
WORK = sys.argv[1]; OUT = sys.argv[2]
sys.path.insert(0, WORK)
import numpy as np
from PIL import Image
import clothes_lib as CL
from clothes_lib import *

_orig = CL.bone_index
def bone_index2(name):
    n = name
    if n == 'Jaw' or n.startswith('eye') or n.startswith('Eye'): return 8
    if n.endswith('_l1') or n.endswith('_r1'): n = n[:-1]
    return _orig(n)
CL.bone_index = bone_index2

HEAD = np.array([0.0, 157.3375, -0.4809])
AW, T, COLS = 2016, 224, 9
B = 'Assets/BoZo_StylizedModularCharacters/Outfits/Base/'
REFS = {1: ((112, 76, 50), (160, 116, 74)), 4: ((200, 200, 206), (96, 96, 106)), 5: ((190, 190, 196), (104, 104, 114)), 6: ((46, 50, 62), (30, 32, 40))}
SLOTS = {1: (2, 3), 4: (7, 8), 5: (10, 11), 6: (10, 11)}
NAMES = {1: 'barba', 4: 'sapatos', 5: 'acessorios', 6: 'lentes'}

# (slot do manifesto, id, pasta, arquivo, tipo, região)  tipo: skin = esqueleto do FBX, head = espaço local da cabeça
FEET = ['BigBoots', 'ComfyShoes', 'CoolShoes', 'OfficeShoes', 'SchoolShoes', 'ShortBoots', 'ShowerSandal', 'SlipOns', 'SportsShoes', 'StreetShoes', 'WorkBoots']
GLOVES = [('ArmWarmers', 'Gloves_ArmWarmers.fbx'), ('FingerlessGloves', 'BSMC_Outfit_Gloves_Fingerless.fbx'), ('WorkGloves', 'BSMC_Outfit_Gloves_WorkGloves.fbx')]
HATS = ['Ballcap', 'Beanie', 'Bucket', 'Fedora', 'Sunhat']
BEARDS = ['BushyBeard', 'ChinGoatee', 'FullBeard', 'Goatee', 'Mustashe', 'MustasheChin']
GLASSES = [('RoundGlasses', 'BSMC_Outfit_Face_RoundGlasses/', 5), ('RoundShaded', 'BSMC_Outfit_Face_RoundShaded/', 6), ('ShadedGlasses', 'BSMC_Outfit_Face_ShadedGlasses/', 6), ('SimpleGlasses', 'BSMC_Outfit_Face_SimpleGlasses/', 5)]
HEADACC = [('AlienAntenna', 'BSMC_Outfit_Head_AlienAttena/'), ('Horns', 'BSMC_Outfit_Head_Horns/')]

def only(sub, suf):
    c = [p for p in idx if p.startswith(B) and sub in p and p.endswith(suf)]
    assert len(c) == 1, (sub, suf, c)
    return c[0]

jobs = []
for i in FEET: jobs.append(('feet', i, only('/Feet/Outfit_Feet_%s/' % i, '.fbx'), 'skin', 4))
for i, f in GLOVES: jobs.append(('gloves', i, only('/Gloves/', '/' + f), 'skin', 5))
for i in HATS: jobs.append(('hat', i, only('/Hat/Outfit_Hat_%s/' % i, '.fbx'), 'head', 5))
for i, d, r in GLASSES: jobs.append(('glasses', i, only('/Face/' + d, '.fbx'), 'head', r))
for i in BEARDS: jobs.append(('beard', i, only('/LowerFace/Outfit_LowerFace_%s/' % i, '.fbx'), 'skin', 1))
for i, d in HEADACC: jobs.append(('headAcc', i, only('/Head/' + d, '.fbx'), 'head', 5))

def tex_of(fbxpath):
    folder = os.path.dirname(fbxpath)
    ds = [p for p in idx if os.path.dirname(p) == folder and p.lower().endswith('_d.png')]
    return ds[0] if len(ds) == 1 else None

n_tiles = len({tex_of(j[2]) for j in jobs if tex_of(j[2])}) + 4
ROWS = (n_tiles + COLS - 1) // COLS
AH = ROWS * T
atlas = np.full((AH, AW, 3), 128.0); a0 = np.zeros((AH, AW)); a1 = np.zeros((AH, AW)); sh = np.zeros((AH, AW)); rid = np.zeros((AH, AW), np.uint8)
texmap = {}; solids = {}
def put(tile, M_or_none, region):
    x0, y0 = tile; sl = (slice(y0, y0 + T), slice(x0, x0 + T))
    if M_or_none is None:
        w0 = np.ones((T, T)); w1 = np.zeros((T, T)); shade = np.full((T, T), 0.85)
    else:
        M = M_or_none; R, G, Bc = M[..., 0], M[..., 1], M[..., 2]
        tot = R + G + Bc; w1 = np.clip((G + Bc) / np.maximum(tot, 1e-4), 0, 1); w1 = np.where(tot > 0.03, w1, 0.0); w0 = 1 - w1
        shade = np.clip(0.35 + 0.75 * M.max(-1), 0.3, 1.1)
    c0 = np.array(REFS[region][0], float); c1 = np.array(REFS[region][1], float)
    ref = w0[..., None] * c0 + w1[..., None] * c1
    atlas[sl] = np.clip(ref * shade[..., None], 0, 255); a0[sl] = w0; a1[sl] = w1; sh[sl] = shade; rid[sl] = region
def next_tile():
    n = len(texmap) + len(solids); return ((n % COLS) * T, (n // COLS) * T)
def tile_for(tp, region):
    if tp in texmap: return texmap[tp]
    t = next_tile(); texmap[tp] = t
    im = Image.open(path(tp)).convert('RGB').resize((T, T), Image.LANCZOS)
    put(t, np.asarray(im).astype(float) / 255, region); return t
def solid_for(region):
    if region in solids: return solids[region]
    t = next_tile(); solids[region] = t; put(t, None, region); return t

def convert(m, tile, off):
    x0, y0 = tile; V = m['V']; cv = m['corner_v']; uv = np.clip(m['cuv'], 0.0, 1.0)
    tris = []
    for poly in m['polys']:
        for k in range(1, len(poly) - 1): tris.append((poly[0], poly[k], poly[k + 1]))
    key = {}; verts = []; ix = []
    for tri in tris:
        for c in tri:
            kk = (int(cv[c]), round(float(uv[c][0]), 5), round(float(uv[c][1]), 5), tuple(np.round(m['cn'][c], 4)))
            if kk not in key: key[kk] = len(verts); verts.append(c)
            ix.append(key[kk])
    verts = np.array(verts); ix = np.array(ix, np.uint16)
    pos = V[cv[verts]] + off
    nor = m['cn'][verts].astype(np.float64); nor /= np.maximum(np.linalg.norm(nor, axis=1, keepdims=True), 1e-9)
    return pos, nor, uv[verts], ix, cv[verts]

REC = np.dtype([('pos', '<f4', 3), ('nor', '<f4', 3), ('uv', '<f4', 2), ('col', 'u1', 4), ('bi', 'u1', 4), ('bw', 'u1', 4)])
def write_cup1(fn, pos, nor, uv, ix, bi, bw):
    n = len(pos); r = np.zeros(n, REC); r['pos'] = pos; r['nor'] = nor; r['uv'] = uv; r['col'] = 255; r['bi'] = bi; r['bw'] = bw
    with open(fn, 'wb') as f:
        f.write(b'CUP1' + struct.pack('<3i', n, len(ix), 0)); f.write(r.tobytes()); f.write(ix.astype('<u2').tobytes())

os.makedirs(OUT, exist_ok=True)
man = []
for slot, pid, fp, kind, region in jobs:
    tp = tex_of(fp)
    tile = tile_for(tp, region) if tp else solid_for(region)
    r, ob, geos, cl, bone_of = load_skinned(path(fp))
    g = geos[0]; m = mesh_from_geo(g)
    # uv -> tile (v invertido, como nas Etapas 3 e 4)
    if kind == 'skin':
        GW = geo_weights(r, ob, geos, cl, bone_of); skb, skw = skin_arrays(GW[g.props[0]], len(m['V']))
        pos, nor, uvv, ix, vsrc = convert(m, tile, 0.0)
        bi, bw = skb[vsrc], skw[vsrc]
    else:
        pos, nor, uvv, ix, vsrc = convert(m, tile, HEAD)
        bi = np.zeros((len(pos), 4), np.uint8); bw = np.zeros((len(pos), 4), np.uint8); bi[:, 0] = 8; bw[:, 0] = 255
    x0, y0 = tile
    if tp: uvt = np.stack([(x0 + 1 + uvv[:, 0] * (T - 2)) / AW, (y0 + 1 + (1 - uvv[:, 1]) * (T - 2)) / AH], 1)
    else: uvt = np.tile(np.array([(x0 + T / 2) / AW, (y0 + T / 2) / AH]), (len(pos), 1))
    fn = 'p_%s_%s.bin' % (slot.lower(), pid.lower())
    write_cup1(os.path.join(OUT, fn), pos, nor, uvt, ix, bi, bw)
    man.append('%s|%s|%s|extra2.png' % (slot, pid, fn))
    print(slot, pid, len(pos), 'v', len(ix) // 3, 'tris', pos.min(0).round(1), pos.max(0).round(1), 'tex' if tp else 'sólido')
# fora dos tiles: cinza
used = np.zeros((AH, AW), bool)
for (x0, y0) in list(texmap.values()) + list(solids.values()): used[y0:y0 + T, x0:x0 + T] = True
atlas[~used] = 128
Image.fromarray(np.round(atlas).astype(np.uint8)).save(os.path.join(OUT, 'extra2.png'), optimize=True)
img = np.zeros((AH, AW, 3), np.uint8); img[..., 0] = np.round(a0 * 255); img[..., 1] = np.round(a1 * 255); img[..., 2] = rid
Image.fromarray(img).save(os.path.join(OUT, 'extra2_recolor.png'), optimize=True)
g_ = np.round(np.clip(sh, 0, 2) / 2 * 255).astype(np.uint8)
Image.fromarray(np.stack([g_] * 3, -1)).save(os.path.join(OUT, 'extra2_recolor_s.png'), optimize=True)
L = ['# id|nome|slot0|slot1|ref0 (sRGB 0..255)|ref1']
for k in (1, 4, 5, 6): L.append('%d|%s|%d|%d|%s|%s' % (k, NAMES[k], SLOTS[k][0], SLOTS[k][1], ' '.join('%.1f' % x for x in REFS[k][0]), ' '.join('%.1f' % x for x in REFS[k][1])))
open(os.path.join(OUT, 'extra2_recolor.txt'), 'w').write('\n'.join(L) + '\n')
open(os.path.join(OUT, 'extra2_pieces.txt'), 'w').write('\n'.join(man) + '\n')
print(len(texmap), 'texturas,', len(solids), 'sólidos;', len(man), 'peças; atlas', AW, 'x', AH)
