import sys,struct,os,numpy as np
from scipy.spatial import cKDTree
A=sys.argv[1]
REC=np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)])
b=open(A+'base.bin','rb').read(); nv,ni,nb,nc=struct.unpack_from('<4i',b,4)
bv=np.frombuffer(b,REC,nv,20); bt=np.frombuffer(b,'<u2',ni,20+nv*44).reshape(-1,3).astype(int)
dom=bv['bi'][np.arange(nv),np.argmax(bv['bw'],1)]
FEET=[19,20,23,24]; HANDS=[12,16]+list(range(25,55))
def samples(pos,ix,nor,step=0.6):
    P=[];N=[]
    for a,b_,c in ix.reshape(-1,3).astype(int):
        pa,pb,pc=pos[a],pos[b_],pos[c]
        k=int(np.ceil(max(np.linalg.norm(pb-pa),np.linalg.norm(pc-pb),np.linalg.norm(pa-pc))/step)); k=max(1,min(k,12))
        for i in range(k+1):
            for j in range(k+1-i):
                u,v=i/k,j/k; w=1-u-v; P.append(pa*w+pb*u+pc*v); N.append(nor[a]*w+nor[b_]*u+nor[c]*v)
    return np.array(P),np.array(N)
def run(fn,bones,dist=1.5):
    raw=open(A+fn,'rb').read(); n,ni_,fl=struct.unpack_from('<3i',raw,4)
    v=np.frombuffer(raw,REC,n,16); ix=np.frombuffer(raw,'<u2',ni_,16+n*44)
    P,N=samples(v['pos'].astype(float),ix,v['nor'].astype(float))
    d,j=cKDTree(P).query(bv['pos'].astype(float))
    cov=np.isin(dom,bones)&(d<dist)&(np.einsum('ij,ij->i',N[j],bv['nor'].astype(float))>0.2)
    sel=np.where(cov[bt].all(1))[0].astype(np.uint16)
    body=raw[:16]; body=b'CUP1'+struct.pack('<3i',n,ni_,1 if len(sel) else 0)+raw[16:16+n*44+ni_*2]
    if len(sel): body+=struct.pack('<i',len(sel))+sel.astype('<u2').tobytes()
    open(A+fn,'wb').write(body); print(fn,'oculta',len(sel),'de',len(bt))
for f in sorted(os.listdir(A)):
    if f.startswith('p_feet_') and 'sandals' not in f: run(f,FEET)
    elif f.startswith('p_gloves_'): run(f,HANDS)
