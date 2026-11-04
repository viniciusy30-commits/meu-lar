import sys; sys.path.insert(0,'/home/claude/work/skate')
from sk_common import *; from prev import raster
from PIL import Image
import struct
def read_cup(fn):
    d=open(fn,'rb').read(); nv,ni,fl=struct.unpack('<3I',d[4:16])
    v=np.frombuffer(d[16:16+nv*44],dtype=np.uint8).reshape(nv,44)
    P=np.frombuffer(v[:,0:12].tobytes(),'<f4').reshape(nv,3).astype(float); N=np.frombuffer(v[:,12:24].tobytes(),'<f4').reshape(nv,3).astype(float); UV=np.frombuffer(v[:,24:32].tobytes(),'<f4').reshape(nv,2)
    T=np.frombuffer(d[16+nv*44:16+nv*44+ni*2],'<u2').reshape(-1,3).astype(int); return P,N,UV,T
g=sys.argv[1]; O='/home/claude/work/skate/out2/'
P,N,UV,T=read_cup(O+g+'_shoes.cup'); tex=np.array(Image.open(O+g+'_shoes.png').convert('RGB'))
B=load_body(g); m=(B.P0[:,1]<14)&(B.P0[:,0]>0); cx=(B.P0[m].min(0)[0]+B.P0[m].max(0)[0])/2
S=(900,700); outs=[]
for yaw in (0.55,1.25,-0.5,3.14):
    R=np.array([[np.cos(yaw),0,np.sin(yaw)],[0,1,0],[-np.sin(yaw),0,np.cos(yaw)]])
    Pc=(P-np.array([cx,0,0]))@R.T; Nr=N@R.T
    sel=P[T][:,:,0].mean(1)>0
    img=np.zeros((S[1],S[0],3),np.uint8)+60; zb=np.full((S[1],S[0]),-1e9)
    raster(Pc,Nr,T[sel],'front',size=S,ymax=32,tex=tex,UV=UV,state=(img,zb))
    outs.append(img[320:700,90:810])
Image.fromarray(np.hstack(outs)).save('/tmp/shoe_tex.png')
