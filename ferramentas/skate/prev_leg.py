import sys; sys.path.insert(0,'/home/claude/work/skate')
from sk_common import *; from sk_cargo2 import *; from prev import raster
from PIL import Image
def read_cup(fn):
    d=open(fn,'rb').read(); nv,ni,fl=struct.unpack('<3I',d[4:16])
    v=np.frombuffer(d[16:16+nv*44],dtype=np.uint8).reshape(nv,44)
    P=np.frombuffer(v[:,0:12].tobytes(),'<f4').reshape(nv,3).astype(float); N=np.frombuffer(v[:,12:24].tobytes(),'<f4').reshape(nv,3).astype(float); UV=np.frombuffer(v[:,24:32].tobytes(),'<f4').reshape(nv,2)
    T=np.frombuffer(d[16+nv*44:16+nv*44+ni*2],'<u2').reshape(-1,3).astype(int)
    return P,N,UV,T
g=sys.argv[1]; O='/home/claude/work/skate/out2/'
B=load_body(g); c,cn,ct,info=build_cargo2(B,O+g+'_shoes.cup')
sP,sN,sUV,sT=read_cup(O+g+'_shoes.cup')
S=(1200,1700); sc=S[1]/190*0.96
outs=[]
for view in ['front','side','back']:
    img=np.zeros((S[1],S[0],3),np.uint8)+40; zb=np.full((S[1],S[0]),-1e9)
    raster(B.P,B.N,B.idx,view,size=S,ymax=190,color=(190,150,130),state=(img,zb))
    raster(sP,sN,sT,view,size=S,ymax=190,color=(235,235,235),state=(img,zb))
    raster(c,cn,ct,view,size=S,ymax=190,color=(70,72,90),state=(img,zb))
    y0=int(S[1]-70*sc-10); y1=S[1]
    outs.append(img[y0:y1,150:1050])
Image.fromarray(np.hstack(outs)).save('/tmp/leg_%s.png'%g)
