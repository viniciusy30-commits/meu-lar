#!/usr/bin/env python3
import os,sys,struct
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]; CU=ROOT/'app/src/main/assets/cute'; SK=CU/'skate'; PRE=ROOT/'fit-ross'
sys.path[:0]=[str(ROOT/'ferramentas/sims4'),str(ROOT/'ferramentas')]
import dbpf,geom,hv
from rle2 import rle2_mip0
DT=np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)])
def cupread(p):
 b=Path(p).read_bytes(); n,ni,_=struct.unpack_from('<3i',b,4); v=np.frombuffer(b,DT,n,16).copy(); i=np.frombuffer(b,'<u2',ni,16+n*44).reshape(-1,3).copy(); return v,i
def cupwrite(p,v,i):
 with open(p,'wb') as f:f.write(b'CUP1'+struct.pack('<3i',len(v),i.size,0)+v.tobytes()+i.astype('<u2').tobytes())
def meshes(es):
 a=[]
 for e in es:
  if e['t']==0x015A1849:
   try:
    g=geom.parse(dbpf.data(e))
    if len(g.get('pos',[])):a.append(g)
   except Exception as x:print('GEOM skip',x)
 if not a:raise RuntimeError('GEOM ausente')
 return a
def texture(es):
 a=[e for e in es if e['t']==0x3453CF95]
 if not a:raise RuntimeError('RLE2 ausente')
 return rle2_mip0(dbpf.data(max(a,key=lambda e:len(dbpf.data(e)))))
def bodyread(grp):
 b=(CU/f'p_body_{grp}5.bin').read_bytes(); n,ni,_=struct.unpack_from('<3i',b,4); v=np.frombuffer(b,DT,n,16).copy(); i=np.frombuffer(b,'<u2',ni,16+n*44).reshape(-1,3).copy();return v,i
def weights(P,b):
 d,ix=cKDTree(b['pos'].astype(float)).query(P,k=6); W=np.zeros((len(P),55)); bi=b['bi'].astype(int); bw=b['bw'].astype(float)/255
 for j in range(6):
  w=1/(d[:,j]+1)**2
  for c in range(4):np.add.at(W,(np.arange(len(P)),bi[ix[:,j],c]),w*bw[ix[:,j],c])
 W/=np.maximum(W.sum(1,keepdims=True),1e-12); W[:,6]+=W[:,5]+W[:,9]+W[:,13]; W[:,[5,9,13]]=0
 top=np.argsort(-W,axis=1)[:,:4]; tw=np.take_along_axis(W,top,1);tw/=tw.sum(1,keepdims=True); q=np.rint(tw*255).astype(int);q[:,0]+=255-q.sum(1)
 if np.any(q<0) or np.any(q>255):raise RuntimeError('pesos inválidos')
 return top.astype('u1'),q.astype('u1')
# Deriva a transformação exata usada no corpo do jogo a partir do Bernard convertido.
be=dbpf.read(str(ROOT/'JohnnySims_Bernard_Hair_V1_MF.package')); bg=max(meshes(be),key=lambda g:len(g['pos']))
bv,_=cupread(SK/'bern1_am5.cup')
if len(bg['pos'])!=len(bv):raise RuntimeError(f'Bernard não corresponde: {len(bg["pos"])} / {len(bv)}')
X=np.column_stack([bg['pos'].astype(float),np.ones(len(bv))]); B=np.linalg.lstsq(X,bv['pos'].astype(float),rcond=None)[0]; A=B[:3]; off=B[3]; k=np.trace(A)/3
err=np.linalg.norm(X@B-bv['pos'],axis=1); rms=np.sqrt(np.mean(err**2)); p95=np.percentile(err,95); an=np.linalg.norm(A-np.eye(3)*k)
print('Calibração:',k,'RMS',rms,'P95',p95,'anisotropia',an)
if k<=0 or an>.015 or rms>.004 or p95>.008:raise RuntimeError('calibração espacial reprovada; exportação cancelada')
PRE.mkdir(exist_ok=True)
for grp,sex in [('am','M'),('af','F')]:
 b,bi=bodyread(grp); skin=Image.open(CU/f'sk_s4{sex.lower()}.png').convert('RGBA')
 body=(b['pos'].astype(float),b['uv'].astype(float),b['col'][:,:3].astype(float)/255,bi.astype(int),skin,0.0)
 for ver in ('V1','V2'):
  ident=f'ross{ver[-1]}_{grp}5'; es=dbpf.read(str(ROOT/f'JohnnySims_Ross_Hair_{ver}_{sex}.package'))
  g=max(meshes(es),key=lambda x:len(x['pos'])); P=g['pos'].astype(float)*k+off; N=g['nor'].astype(float); UV=g['uv'][0].astype(float)*[2,1]; I=g['idx'].astype(int)
  if len(P)>65535:raise RuntimeError(ident+' excede índice uint16')
  top,q=weights(P,b); v=np.zeros(len(P),DT);v['pos']=P;v['nor']=N;v['uv']=UV;v['col']=255;v['bi']=top;v['bw']=q
  tx=texture(es); tx.save(SK/f'{ident}.png',optimize=True);cupwrite(SK/f'{ident}.cup',v,I)
  hair=(P,UV,np.ones((len(P),3)),I,tx,.35);yc=b['pos'][:,1].max()-9
  ims=[hv.raster([body,hair],512,view,((0,yc),34)) for view in ('f','s','b','q')]
  panel=np.concatenate(ims,axis=1);Image.fromarray(panel).save(PRE/f'{ident}_fit.png')
  Image.fromarray(ims[0]).save(CU/'thumbs'/f'{ident}.png')
  print(ident,len(P),'vertices',len(I),'triângulos')
print('ROSS_CONVERSION_OK')
