import sys; sys.path.insert(0,'/home/claude/work/skate')
from sk_common import *; from sk_garments import *; from sk_jacket import *; from prev import raster
from prev_cg import TEE
from PIL import Image
g=sys.argv[1]
B=load_body(g); t,tn,tt,_=build_tee(B,TEE); j,jn,jt,info=build_jacket(B)
outs=[]
for view in ['front','side','back']:
    img=np.zeros((900,560,3),np.uint8)+40; zb=np.full((900,560),-1e9)
    raster(B.P,B.N,B.idx,view,size=(560,900),ymax=190,color=(190,150,130),state=(img,zb))
    raster(t,tn,tt,view,size=(560,900),ymax=190,color=(120,120,130),state=(img,zb))
    raster(j,jn,jt,view,size=(560,900),ymax=190,color=(40,42,50),state=(img,zb))
    outs.append(img[60:620])
Image.fromarray(np.hstack(outs)).save('/tmp/jk_%s.png'%g)
