#!/usr/bin/env python3
"""Etapa 45: corpos do Sims 3 com ESQUELETO PROPRIO (nada do Bozo).
Uso: python3 etapa45_sims_rig.py <pasta com bodies/ faces/ (RARs extraidos)> <assets/cute>   (precisa de base.bin com os clipes, heartbeat.png, p_hairback_heartbeat.bin e sk_*.png ja gerados pela etapa 44)
 - malha do Sims 3 em proporcao real (so escala uniforme; sem warp para o Bozo e sem girar os bracos)
 - juntas ajustadas na propria malha (ombro, cotovelo, punho, quadril, joelho, tornozelo, coluna, pescoco, cabeca): etapa45_rig.fit_joints
 - pesos por difusao na superficie (nao ha mais copia do vertice mais proximo do Bozo): braco nao gruda no tronco; pescoco em degrade ate o corte do rosto
 - clipes (parado, andar, pulo, correr, masculinos) adaptados a esse esqueleto: mesmas rotacoes, comprimentos de osso do Sims; sola travada no chao
Gera: p_body_<id>.bin (todas as variantes), p_hairback_h<estagio><sexo>.bin e clips_<grupo>.bin (grupo = estagio+sexo: af am tf tm ef em cu pu)."""
import sys, os, struct, importlib.util
RAWDIR = sys.argv[1]; CUDIR = sys.argv[2]
_here = os.path.dirname(os.path.abspath(__file__))
os.environ['BASE_BIN'] = os.path.join(CUDIR, 'base.bin')
sys.path.insert(0, _here)
sys.argv = ['x', RAWDIR, CUDIR]
def _load(name, fn):
    sp = importlib.util.spec_from_file_location(name, os.path.join(_here, fn)); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
e = _load('e43', 'etapa43_julie.py'); s44 = _load('e44', 'etapa44_sims.py')
import numpy as np
from PIL import Image
import etapa45_rig as R
RAW = RAWDIR.rstrip('/') + '/'; CU = CUDIR.rstrip('/') + '/'
H_ADULT_F = 1.675
SW = float(os.environ.get('SW', '0.968'))   # mantem a altura do adulto feminino igual a das etapas anteriores (so escala uniforme)
CJ0, SC0 = e.CJ.copy(), e.SC.copy()

def face_atlas_eyes(st, g):
    atlas = np.asarray(Image.open(CU + 'sk_%s%s.png' % (st, g)).convert('RGB')).astype(float)
    return s44.find_eyes(atlas[0:1024, 1024:2048])
def uvA(m, xo): return np.stack([(xo + m['uv'][:, 0] * 1024) / e.AW, ((1 - m['uv'][:, 1]) * 1024) / e.AH], 1)

def group_rig(sd):
    """juntas do grupo (estagio+sexo), tiradas da malha 'normal' do estagio"""
    bn = sd['body'][1] if 1 in sd['body'] else list(sd['body'].values())[0]
    body = e.load(RAW + 'bodies/%s.obj' % bn); face = e.load(RAW + 'faces/%s.obj' % sd['face']['n'])
    J, cls = R.fit_joints(body['pos'], body['idx'], face['pos'][:, 1].min(), face['pos'][:, 1].max())
    ratio = body['pos'][:, 1].max() / H_ADULT_F
    return J, ratio, face['pos'][:, 1].min()

def build_variant(sd, typ, J, gratio, eyes):
    body = e.load(RAW + 'bodies/%s.obj' % sd['body'][typ])
    face = e.load(RAW + 'faces/%s.obj' % sd['face']['f' if typ == 3 else 'n'])
    scalp = e.load(RAW + 'faces/%s.obj' % sd['scalp'])
    ratio = body['pos'][:, 1].max() / H_ADULT_F
    sc = 100.0 / ratio * SW
    xf = lambda m: m['pos'] * sc
    fymin = face['pos'][:, 1].min()
    bi, bw = R.skin_weights(body['pos'], body['idx'], J, R.classify(body['pos'], body['idx']), fymin - 0.003)
    parts = []
    for name, m, xo in (('body', body, 0), ('face', face, 1024), ('scalp', scalp, None)):
        pos = xf(m); idx = m['idx'].copy(); n, idx = e.vnormals(pos, idx, m['nor'])
        if xo is None: uv = np.tile([(e.HAIR_BLK[0] + e.HAIR_BLK[2] / 2) / e.AW, (e.HAIR_BLK[1] + e.HAIR_BLK[2] / 2) / e.AH], (len(pos), 1))
        else: uv = uvA(m, xo)
        if name == 'body': pbi, pbw = bi, bw
        else:
            pbi = np.zeros((len(pos), 4), np.uint8); pbw = np.zeros((len(pos), 4), np.uint8); pbi[:, 0] = R.BI['head']; pbw[:, 0] = 255
        parts.append(dict(name=name, pos=pos, nor=n, uv=uv, idx=idx, bi=pbi, bw=pbw))
    for (cx, cy) in eyes:
        p, n = e.uv_to_3d(face, cx, cy); pl, _ = e.uv_to_3d(face, cx - 40, cy); pr, _ = e.uv_to_3d(face, cx + 40, cy)
        r = 0.50 * np.linalg.norm(pl - pr) * sc * 0.93
        c = p * sc - n * 0.55 * r
        P, N, UV, I = e.make_sphere(c, r)
        bi_ = np.zeros((len(P), 4), np.uint8); bw_ = np.zeros((len(P), 4), np.uint8); bi_[:, 0] = R.BI['head']; bw_[:, 0] = 255
        parts.append(dict(name='eye', pos=P, nor=N, uv=UV, idx=I, bi=bi_, bw=bw_))
    return parts, ratio, sc, (body, scalp)

def old_scalp_box(scalp, ratio):
    q = e.warp_body(scalp['pos'] * 100 / ratio); return q.min(0), q.max(0)

def write_clips(path, clips):
    out = bytearray(b'CLP1' + struct.pack('<2i', 55, len(clips)))
    for ln, d in clips:
        d = np.ascontiguousarray(d, dtype='<f4'); out += struct.pack('<fi', float(ln), d.shape[0]) + d.tobytes()
    open(path, 'wb').write(bytes(out))

def main():
    rows = []; hair_done = set(); clips_done = set()
    for sd in s44.stage_def():
        grp = sd['st'] + sd['g']
        J, gratio, _ = group_rig(sd)
        eyes = face_atlas_eyes(sd['st'], sd['g'])
        for typ in sorted(sd['body']):
            vid = '%s%s%d' % (sd['st'], sd['g'], typ)
            parts, ratio, sc, (body, scalp) = build_variant(sd, typ, J, gratio, eyes)
            n = s44.write_body(CU + 'p_body_%s.bin' % vid, parts)
            if grp not in clips_done and typ == 1:
                b = parts[0]; rest = b['pos']; sole = np.nonzero(rest[:, 1] < 0.05 * rest[:, 1].max())[0]
                Q25 = np.array([J[nm] for nm in R.BONES]) * sc
                write_clips(CU + 'clips_%s.bin' % grp, R.retarget_clips(Q25, b['bi'], b['bw'], rest, sole)); clips_done.add(grp)
            if sd['st'] in 'ate' and grp not in hair_done and typ == 1:
                omin, omax = old_scalp_box(scalp, ratio); nmin, nmax = scalp['pos'].min(0) * sc, scalp['pos'].max(0) * sc
                e.CJ = CJ0 + ((nmin + nmax) / 2 - (omin + omax) / 2); e.SC = SC0 * (nmax - nmin) / np.maximum(omax - omin, 1e-6)
                hr, hidx = e.build_hair([p for p in parts if p['name'] in ('body', 'face', 'scalp')])
                e.write_piece(CU + 'p_hairback_h%s.bin' % grp, hr, hidx); hair_done.add(grp)
            rows.append('%s|%s|%s|%d|%.4f|%d' % (vid, sd['st'], sd['g'], typ, ratio, 1 if sd['st'] in 'ate' else 0))
            print(vid, n, 'verts', flush=True)
    open(CU + 'simbodies.txt', 'w').write('# id|estagio(p c t a e)|sexo(f m u)|tipo(0 magro 1 normal 2 atletico 3 gordo)|altura relativa|tem cabelo\n' + '\n'.join(rows) + '\n')

if __name__ == '__main__': main()
