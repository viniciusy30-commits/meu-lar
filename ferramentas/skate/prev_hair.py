import sys; sys.path.insert(0,'/home/claude/work/skate')
from sk_common import *; from prev import raster
from PIL import Image
import struct
def read_cup(fn):
    d=open(fn,'rb').read(); nv,ni,fl=struct.unpack('<3I',d[4:16])
    v=np.frombuffer(d[16:16+nv*44],dtype=np.uint8).reshape(nv,44)
    P=np.frombuffer(v[:,0:12].tobytes(),'<f4').reshape(nv,3); N=np.frombuffer(v[:,12:24].tobytes(),'<f4').reshape(nv,3); UV=np.frombuffer(v[:,24:32].tobytes(),'<f4').reshape(nv,2)
    T=np.frombuffer(d[16+nv*44:16+nv*44+ni*2],'<u2').reshape(-1,3).astype(int)
    return P,N,UV,T
g=sys.argv[1]; O='/home/claude/work/skate/out2/'
P,N,UV,T=read_cup(O+g+'_hair.cup'); tex=np.array(Image.open(O+g+'_hair.png'))
B=load_body(g)
S=(1200,1700)
outs=[]
for view in ['front','side','back']:
    img=np.zeros((S[1],S[0],3),np.uint8)+40; zb=np.full((S[1],S[0]),-1e9)
    hv=B.P[:,1]>140
    raster(B.P,B.N,B.idx[hv[B.idx].all(1)],view,size=S,ymax=190,color=(200,160,140),state=(img,zb))
    raster(P,N,T,view,size=S,ymax=190,tex=tex,UV=UV,state=(img,zb))
    sc=S[1]/190*0.96
    y0=int(S[1]-200*sc-10); y1=int(S[1]-130*sc-10)
    outs.append(img[max(0,y0):y1, 200:1000])
im=Image.fromarray(np.hstack(outs)); im.save('/tmp/hair_%s.png'%g); print(im.size)
