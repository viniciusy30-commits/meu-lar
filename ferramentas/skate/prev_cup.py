import sys; sys.path.insert(0,'/home/claude/work/skate')
import struct, numpy as np
from sk_common import *; from prev import raster
from PIL import Image
def read_cup(fn):
    d=open(fn,'rb').read(); nv,ni,fl=struct.unpack('<3I',d[4:16])
    v=np.frombuffer(d[16:16+nv*44],dtype=np.uint8).reshape(nv,44)
    P=np.frombuffer(v[:,0:12].tobytes(),'<f4').reshape(nv,3).astype(float); N=np.frombuffer(v[:,12:24].tobytes(),'<f4').reshape(nv,3).astype(float); UV=np.frombuffer(v[:,24:32].tobytes(),'<f4').reshape(nv,2)
    T=np.frombuffer(d[16+nv*44:16+nv*44+ni*2],'<u2').reshape(-1,3).astype(int); return P,N,UV,T
g,cup,png,out=sys.argv[1:5]; FLIP=len(sys.argv)>5
B=load_body(g); P,N,UV,T=read_cup(cup); UV=UV.copy(); UV[:,1]=1-UV[:,1] if FLIP else UV[:,1]; tex=np.array(Image.open(png).convert('RGBA')); print(len(P),len(T))
outs=[]
for view in ['front','side','back']:
    img=np.zeros((900,520,3),np.uint8)+60; zb=np.full((900,520),-1e9)
    raster(B.P,B.N,B.idx,view,size=(520,900),ymax=190,color=(200,160,140),state=(img,zb))
    raster(P,N,T,view,size=(520,900),ymax=190,tex=tex,UV=UV,state=(img,zb))
    outs.append(img[40:620])
Image.fromarray(np.hstack(outs)).save(out)
