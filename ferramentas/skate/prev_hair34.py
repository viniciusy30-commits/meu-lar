import sys; sys.path.insert(0,'/home/claude/work/skate')
import struct, numpy as np
from sk_common import *; from prev import raster
from PIL import Image
def read_cup(fn):
    d=open(fn,'rb').read(); nv,ni,fl=struct.unpack('<3I',d[4:16])
    v=np.frombuffer(d[16:16+nv*44],dtype=np.uint8).reshape(nv,44)
    P=np.frombuffer(v[:,0:12].tobytes(),'<f4').reshape(nv,3).astype(float); N=np.frombuffer(v[:,12:24].tobytes(),'<f4').reshape(nv,3).astype(float); UV=np.frombuffer(v[:,24:32].tobytes(),'<f4').reshape(nv,2)
    T=np.frombuffer(d[16+nv*44:16+nv*44+ni*2],'<u2').reshape(-1,3).astype(int); return P,N,UV,T
g=sys.argv[1]
B=load_body(g); P,N,UV,T=read_cup('out2/%s_hair.cup'%g); tex=np.array(Image.open('out2/%s_hair.png'%g))
outs=[]
for yaw,pitch in ((0.0,0.1),(0.6,0.45),(-2.5,0.4),(0.0,0.9)):
    def tf(X):
        c=np.array([0,B.head_y+6,0]); Y=X-c
        R1=np.array([[np.cos(yaw),0,np.sin(yaw)],[0,1,0],[-np.sin(yaw),0,np.cos(yaw)]])
        R2=np.array([[1,0,0],[0,np.cos(pitch),-np.sin(pitch)],[0,np.sin(pitch),np.cos(pitch)]])
        return (Y@R1.T)@R2.T+np.array([0,30,0])
    S=(600,600); img=np.zeros((600,600,3),np.uint8)+60; zb=np.full((600,600),-1e9)
    hv=B.P[:,1]>140; tri=B.idx[hv[B.idx].all(1)]
    Rm=lambda n: tf(n+np.array([0,B.head_y+6,0]))-np.array([0,30,0])
    raster(tf(B.P),Rm(B.N),tri,'front',size=S,ymax=60,color=(200,160,140),state=(img,zb))
    raster(tf(P),Rm(N),T,'front',size=S,ymax=60,tex=tex,UV=UV,state=(img,zb))
    outs.append(img)
Image.fromarray(np.hstack(outs)).save('/tmp/hair34.png')
