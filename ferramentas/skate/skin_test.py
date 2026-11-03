import sys; sys.path.insert(0,'/home/claude/work/skate')
import numpy as np, struct
from PIL import Image
from sk_common import *; from prev import raster
from preview import rdcup
def load_clips(g):
    d=open(CUTE+'clips_%s.bin'%g,'rb').read(); assert d[:4]==b'CLP1'
    nb,nc=struct.unpack_from('<2i',d,4); p=12; out=[]
    for c in range(nc):
        ln,nf=struct.unpack_from('<fi',d,p); p+=8
        a=np.frombuffer(d,'<f4',nf*nb*12,p).reshape(nf,nb,12); p+=nf*nb*12*4; out.append((ln,a))
    return nb,out
def skin(P,N,bi,bw,M):
    out=np.zeros_like(P); on=np.zeros_like(N)
    for k in range(4):
        m=M[bi[:,k]]  # (n,12)
        w=bw[:,k:k+1]
        out+=w*np.stack([(m[:,0:3]*P).sum(1)+m[:,3],(m[:,4:7]*P).sum(1)+m[:,7],(m[:,8:11]*P).sum(1)+m[:,11]],1)
        on+=w*np.stack([(m[:,0:3]*N).sum(1),(m[:,4:7]*N).sum(1),(m[:,8:11]*N).sum(1)],1)
    return out,on
def cupfull(p):
    d=open(p,'rb').read(); nv,ni,fl=struct.unpack_from('<3I',d,4)
    v=np.frombuffer(d,DT,nv,16); idx=np.frombuffer(d,'<u2',ni,16+nv*44).reshape(-1,3).astype(int)
    return v['p'].astype(float),v['n'].astype(float),v['uv'].astype(float),idx,v['bi'].astype(int),v['bw'].astype(float)/255
if __name__=='__main__':
    g=sys.argv[1]; O=sys.argv[2]; clip=int(sys.argv[3]); frac=float(sys.argv[4])
    nb,clips=load_clips(g); ln,a=clips[clip]; f=int(frac*(len(a)-1)); M=a[f].copy(); sc=np.linalg.norm(M[0,0:3]); print('scale',sc); M=M/sc if False else M
    SC=1.0/sc
    imgs=[]
    for view in ('front','side'):
        img=np.zeros((760,520,3),np.uint8)+40; zb=np.full((760,520),-1e9)
        Pb,Nb,UVb,Ib,bib,bwb=cupfull(CUTE+'p_body_%s1.bin'%g)
        Pb2,Nb2=skin(Pb,Nb,bib,bwb,M); Pb2=Pb2*SC; raster(Pb2,Nb2,Ib,view,color=(190,150,130),state=(img,zb))
        for n in sys.argv[5:]:
            P,N,UV,I,bi,bw=cupfull(O+'%s_%s.cup'%(g,n)); P2,N2=skin(P,N,bi,bw,M); P2=P2*SC
            tex=np.asarray(Image.open(O+'%s_%s.png'%(g,n)).convert('RGB')); raster(P2,N2,I,view,tex=tex,UV=UV,state=(img,zb))
        imgs.append(img)
    W=Image.new('RGB',(1040,760)); [W.paste(Image.fromarray(o),(i*520,0)) for i,o in enumerate(imgs)]
    W.save('/tmp/skin.png')
