import sys; sys.path.insert(0,'/home/claude/work/skate')
from sk_common import *; from sk_garments import *; from sk_cargo2 import *; from prev import raster
from prev_cg import TEE
from PIL import Image
g=sys.argv[1]; O='/home/claude/work/skate/out2/'
B=load_body(g); c,cn,ct,info=build_cargo2(B,O+g+'_shoes.cup'); t,tn,tt,_=build_tee(B,TEE)
sP=read_cup_pos(O+g+'_shoes.cup')
exec(open('/home/claude/work/skate/prev_leg.py').read().split("g=sys.argv")[0].split("B=load_body")[0]) if False else None
import struct
def read_cup(fn):
    d=open(fn,'rb').read(); nv,ni,fl=struct.unpack('<3I',d[4:16])
    v=np.frombuffer(d[16:16+nv*44],dtype=np.uint8).reshape(nv,44)
    P=np.frombuffer(v[:,0:12].tobytes(),'<f4').reshape(nv,3).astype(float); N=np.frombuffer(v[:,12:24].tobytes(),'<f4').reshape(nv,3).astype(float)
    T=np.frombuffer(d[16+nv*44:16+nv*44+ni*2],'<u2').reshape(-1,3).astype(int); return P,N,T
sP,sN,sT=read_cup(O+g+'_shoes.cup')
outs=[]
for view in ['front','side','back']:
    img=np.zeros((900,520,3),np.uint8)+40; zb=np.full((900,520),-1e9)
    raster(B.P,B.N,B.idx,view,size=(520,900),ymax=190,color=(190,150,130),state=(img,zb))
    raster(sP,sN,sT,view,size=(520,900),ymax=190,color=(235,235,235),state=(img,zb))
    raster(c,cn,ct,view,size=(520,900),ymax=190,color=(70,72,90),state=(img,zb))
    raster(t,tn,tt,view,size=(520,900),ymax=190,color=(30,30,34),state=(img,zb))
    outs.append(img)
Image.fromarray(np.hstack(outs)).save('/tmp/fit_%s.png'%g)
