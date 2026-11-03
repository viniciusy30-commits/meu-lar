import sys; sys.path.insert(0,'/home/claude/work/skate'); sys.path.insert(0,'/home/claude/work/proto')
import numpy as np, struct
from PIL import Image
from sk_common import *; from prev import raster
def rdcup(p):
    d=open(p,'rb').read(); nv,ni,fl=struct.unpack_from('<3I',d,4)
    v=np.frombuffer(d,DT,nv,16); idx=np.frombuffer(d,'<u2',ni,16+nv*44).reshape(-1,3).astype(int)
    return v['p'].astype(float),v['n'].astype(float),v['uv'].astype(float),idx
def show(g,items,out,views=('front','side','back'),size=(520,760)):
    B=load_body(g); imgs=[]
    for view in views:
        W_,H_=size; img=np.zeros((H_,W_,3),np.uint8)+40; zb=np.full((H_,W_),-1e9)
        raster(B.P,B.N,B.idx,view,size=size,color=(190,150,130),state=(img,zb))
        for cup,png in items:
            P,N,UV,T=rdcup(cup); tex=np.asarray(Image.open(png).convert('RGB'))
            raster(P,N,T,view,size=size,tex=tex,UV=UV,state=(img,zb))
        imgs.append(img)
    W=Image.new('RGB',(size[0]*len(views),size[1]))
    for i,o in enumerate(imgs): W.paste(Image.fromarray(o),(i*size[0],0))
    W.save(out)
if __name__=='__main__':
    g=sys.argv[1]; O=sys.argv[-1] if sys.argv[-1].startswith('/') else '/home/claude/work/skate/out/'
    items=[]
    for n in sys.argv[3:]: items.append((O+'%s_%s.cup'%(g,n),O+'%s_%s.png'%(g,n)))
    show(g,items,sys.argv[2])
