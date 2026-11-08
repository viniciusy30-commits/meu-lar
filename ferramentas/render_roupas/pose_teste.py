import sys, numpy as np
sys.path.insert(0,'/home/claude/proj/codigo/ferramentas/render_roupas')
import render_roupas as R
from pathlib import Path
from PIL import Image
import struct
def read2(p):
    g=R.read(p); b=Path(p).read_bytes(); nv=struct.unpack_from('<I',b,4)[0]
    dt=np.dtype([('pos','<f4',(3,)),('nor','<f4',(3,)),('uv','<f4',(2,)),('rgba','u1',(4,)),('bi','u1',(4,)),('bw','u1',(4,))])
    v=np.frombuffer(b,dtype=dt,count=nv,offset=16)
    g['bi']=v['bi'].astype(int); g['bw']=v['bw'].astype(float)/255; return g
def rot(axis_deg,pivot):
    a=np.radians(axis_deg); c,s=np.cos(a),np.sin(a)
    M=np.eye(4); M[1,1]=c; M[1,2]=-s; M[2,1]=s; M[2,2]=c   # rotação em torno de x
    T=np.eye(4); T[:3,3]=pivot; Ti=np.eye(4); Ti[:3,3]=-np.array(pivot)
    return T@M@Ti
def pose(hipR,kneeR,ankR,hipL,kneeL,ankL):
    I=np.eye(4); B={}
    def chain(side,hip,knee,ank,px):
        H=rot(hip,(px,84,1)); K=H@rot(knee,(px,48,2)); A=K@rot(ank,(px,8,0))
        return H,K,A
    r=chain('R',hipR,kneeR,ankR,8.5); l=chain('L',hipL,kneeL,ankL,-8.5)
    for b,m in zip((17,18,19,20),(r[0],r[1],r[2],r[2])): B[b]=m
    for b,m in zip((21,22,23,24),(l[0],l[1],l[2],l[2])): B[b]=m
    return B
def skin(g,B):
    P=g['pos']; Q=np.zeros_like(P); N=np.zeros_like(P); Nn=g['nor']
    h=np.c_[P,np.ones(len(P))]
    for k in range(4):
        for b in np.unique(g['bi'][:,k]):
            m=(g['bi'][:,k]==b)&(g['bw'][:,k]>0)
            M=B.get(int(b),np.eye(4))
            Q[m]+=g['bw'][m,k,None]*(h[m]@M.T)[:,:3]
            N[m]+=g['bw'][m,k,None]*(Nn[m]@M[:3,:3].T)
    out=dict(g); out['pos']=Q; out['nor']=N/(np.linalg.norm(N,axis=1,keepdims=True)+1e-9); return out
if __name__=='__main__':
    name=sys.argv[1]; outp=sys.argv[2]
    body=read2(R.ROOT/'p_body_am5.bin'); cl=read2(R.ROOT/'skate'/f'minimalist_{name}_am5.cup')
    tex=np.asarray(Image.open(R.ROOT/'skate'/f'minimalist_{name}_am5.png').convert('RGB'))
    ims=[]
    for P_ in [(0,0,0,0,0,0),(40,-10,5,-30,-70,-20),(-30,-80,20,45,-5,10),(60,-5,-25,-20,-90,0)]:
        B=pose(*P_)
        items=[(skin(body,B),None,(224,172,140)),(skin(cl,B),tex,None)]
        for v in ('front','side'):
            ims.append(R.render(items,v,W=300,H=560,ymin=-2,ymax=120))
    W=sum(i.width for i in ims); s=Image.new('RGB',(W,ims[0].height)); x=0
    for i in ims: s.paste(i,(x,0)); x+=i.width
    s.save(outp)
