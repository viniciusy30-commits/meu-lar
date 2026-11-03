import sys; sys.path.insert(0,'/home/claude/work/skate')
from sk_common import *; from sk_garments import *; from prev import raster
from PIL import Image
TEE=dict(hem=13.0,off_t=[7.0,6.2,5.2,3.6,1.4],s0=3.4,s1=4.2,sp=1.3,sl=1.05,fl=2.2,curve=2.0)
if __name__=='__main__':
    B=load_body('am')
    t,tn,tt,_=build_tee(B,TEE)
    c,cn,ct,info=build_cargo(B); print(c.shape,ct.shape,info)
    out=[]
    for view in ['front','side','back']:
        img=np.zeros((760,520,3),np.uint8)+40; zb=np.full((760,520),-1e9)
        raster(B.P,B.N,B.idx,view,color=(190,150,130),state=(img,zb))
        raster(c,cn,ct,view,color=(70,70,76),state=(img,zb))
        raster(t,tn,tt,view,color=(30,30,34),state=(img,zb))
        out.append(img)
    W=Image.new('RGB',(1560,760))
    for i,o in enumerate(out): W.paste(Image.fromarray(o),(i*520,0))
    W.resize((1170,570)).save('/tmp/cg_geo.png')
