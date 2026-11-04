import sys; sys.path.insert(0,'/home/claude/work/skate')
import struct, numpy as np
from sk_common import *; from prev import raster
from PIL import Image
g=sys.argv[1]; jk=(len(sys.argv)<3 or sys.argv[2]!='nojk')
O='/home/claude/work/skate/out2/'
def read_cup(fn):
    d=open(fn,'rb').read(); nv,ni,fl=struct.unpack('<3I',d[4:16])
    v=np.frombuffer(d[16:16+nv*44],dtype=np.uint8).reshape(nv,44)
    P=np.frombuffer(v[:,0:12].tobytes(),'<f4').reshape(nv,3).astype(float); N=np.frombuffer(v[:,12:24].tobytes(),'<f4').reshape(nv,3).astype(float); UV=np.frombuffer(v[:,24:32].tobytes(),'<f4').reshape(nv,2)
    T=np.frombuffer(d[16+nv*44:16+nv*44+ni*2],'<u2').reshape(-1,3).astype(int); return P,N,UV,T
B=load_body(g)
items=[]
for n in ['cargo','shoes','tee','jacket','hair']:
    if n=='jacket' and not jk: continue
    P,N,UV,T=read_cup(O+'%s_%s.cup'%(g,n)); tex=np.array(Image.open(O+'%s_%s.png'%(g,n)).convert('RGBA'))
    if n=='tee' and jk:   # esconde a manga da camiseta
        S=B.sh; E=B.el; u=(E-S); L=np.linalg.norm(u); u/=L
        c=P[T].mean(1); c[:,0]=np.abs(c[:,0]); r=c-S; t=r@u; perp=np.linalg.norm(r-t[:,None]*u,axis=1)
        T=T[~((t>2)&(t<L*1.15)&(perp<14.5))]
    items.append((P,N,UV,T,tex))
outs=[]
for view in ['front','side','back']:
    img=np.zeros((900,520,3),np.uint8)+60; zb=np.full((900,520),-1e9)
    hv=B.P[:,1]>-1
    raster(B.P,B.N,B.idx,view,size=(520,900),ymax=190,color=(200,160,140),state=(img,zb))
    for P,N,UV,T,tex in items: raster(P,N,T,view,size=(520,900),ymax=190,tex=tex,UV=UV,state=(img,zb))
    outs.append(img)
Image.fromarray(np.hstack(outs)).save('/tmp/outfit_%s.png'%g)
