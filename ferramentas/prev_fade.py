import sys; sys.path.insert(0,'/home/claude/work/skate')
import numpy as np, math
from sk_common import load_body
from prev import raster
import struct
def read_cup(fn):
    d=open(fn,'rb').read(); nv,ni,fl=struct.unpack('<3I',d[4:16])
    v=np.frombuffer(d[16:16+nv*44],dtype=np.uint8).reshape(nv,44)
    P=np.frombuffer(v[:,0:12].tobytes(),'<f4').reshape(nv,3).astype(float); N=np.frombuffer(v[:,12:24].tobytes(),'<f4').reshape(nv,3).astype(float); UV=np.frombuffer(v[:,24:32].tobytes(),'<f4').reshape(nv,2)
    T=np.frombuffer(d[16+nv*44:16+nv*44+ni*2],'<u2').reshape(-1,3).astype(int); return P,N,UV,T
from PIL import Image
def view(g, cup, png, out, yaws=(0, 50, 90, 140, 180), pitch=0.0, size=440):
    B=load_body(g); P,N,UV,T=read_cup(cup); tex=np.array(Image.open(png).convert('RGBA'))
    top=B.P[:,1].max(); zc=0.8
    ims=[]
    for yw in yaws:
        a=math.radians(yw); c,s=math.cos(a),math.sin(a); cp,sp=math.cos(pitch),math.sin(pitch)
        def tf(Q):
            Q=Q.copy(); Q[:,2]-=zc; x=Q[:,0]*c+Q[:,2]*s; z=-Q[:,0]*s+Q[:,2]*c; y=Q[:,1]-(top-14)
            y2=y*cp-z*sp; z2=y*sp+z*cp
            return np.stack([x,y2+14,z2],1)
        img=np.zeros((size,size,3),np.uint8)+70; zb=np.full((size,size),-1e9)
        raster(tf(B.P),tf(B.N),B.idx,'front',size=(size,size),ymax=32,color=(214,170,145),state=(img,zb))
        raster(tf(P),tf(N),T,'front',size=(size,size),ymax=32,tex=tex,UV=UV,state=(img,zb))
        ims.append(img)
    Image.fromarray(np.hstack(ims)).save(out)
if __name__=='__main__':
    g=sys.argv[1]; view(g,sys.argv[2],sys.argv[3],sys.argv[4])
