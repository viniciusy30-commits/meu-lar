import sys, struct, numpy as np
sys.path.insert(0,'/home/claude/work/skate')
from PIL import Image
from scipy import ndimage
from sk_common import DT

def read_cup(fn):
    d=open(fn,'rb').read(); nv,ni,fl=struct.unpack('<3I',d[4:16])
    r=np.frombuffer(d,DT,nv,16).copy()
    idx=np.frombuffer(d,'<u2',ni,16+nv*44).astype(np.int64).reshape(-1,3)
    return r,idx

def sub_weights(bi,bw,a,b):
    acc={}
    for k in range(4):
        if bw[a,k]>0: acc[int(bi[a,k])]=acc.get(int(bi[a,k]),0)+bw[a,k]/255.0*0.5
        if bw[b,k]>0: acc[int(bi[b,k])]=acc.get(int(bi[b,k]),0)+bw[b,k]/255.0*0.5
    top=sorted(acc.items(),key=lambda kv:-kv[1])[:4]; s=sum(w for _,w in top) or 1
    q=[int(round(w/s*255)) for _,w in top]; q[0]+=255-sum(q)
    ii=np.zeros(4,np.uint8); ww=np.zeros(4,np.uint8)
    for i,((bn,_),w) in enumerate(zip(top,q)): ii[i]=bn; ww[i]=w
    return ii,ww

def subdivide(r,idx):
    mid={}; recs=[r]; n=len(r); new=[]; T=[]
    P=r['p']; N=r['n']; UV=r['uv']; BI=r['bi']; BW=r['bw']
    def m(a,b):
        nonlocal n
        k=(a,b) if a<b else (b,a)
        if k not in mid:
            mid[k]=n; n+=1
            e=np.zeros(1,DT)
            e['p']=(P[a]+P[b])/2; nn=N[a]+N[b]; e['n']=nn/max(np.linalg.norm(nn),1e-9); e['uv']=(UV[a]+UV[b])/2; e['c']=255
            ii,ww=sub_weights(BI,BW,a,b); e['bi']=ii; e['bw']=ww
            new.append(e)
        return mid[k]
    for a,b,c in idx:
        ab,bc,ca=m(a,b),m(b,c),m(c,a)
        T+=[(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]
    return np.concatenate([r]+new),np.array(T,np.int64)

def decollide(g,r,idx,clear=0.9):
    """empurra para fora do corpo os vértices que ficaram por dentro (a parte de cima da regata afundava 1-2 cm)."""
    from sk_common import load_body, laplace, vnormals
    from scipy.spatial import cKDTree
    B=load_body(g); P=r['p'].astype(float)
    tree=cKDTree(B.P)
    for it in range(8):
        d,ix=tree.query(P,k=8)
        # distância assinada em relação a cada vizinho; vale a pior (mais "por dentro")
        sd=((P[:,None,:]-B.P[ix])*B.N[ix]).sum(2)
        worst=np.where(d<6.0,sd,99.0).min(1)
        nb=(B.N[ix]*(1/(d+0.3))[...,None]).sum(1); nb/=np.linalg.norm(nb,axis=1,keepdims=True)
        push=np.maximum(clear-worst,0)
        push=np.minimum(push,2.5)
        P=P+nb*push[:,None]
        P=laplace(P,idx,np.zeros(len(P),bool),it=1,lam=0.3)
    r=r.copy(); r['p']=P
    r['n']=vnormals(P,idx)
    return r

def process(g,mask_png,fit_raw,out_cup):
    r,idx=read_cup(fit_raw)
    r=decollide(g,r,idx)
    r,idx=subdivide(r,idx)
    al=np.array(Image.open(mask_png).convert('RGBA'))[...,3]>128
    al=ndimage.binary_dilation(al,iterations=12)
    H,W=al.shape
    def inside(uv):
        x=np.clip((uv[:,0]*W).astype(int),0,W-1); y=np.clip((uv[:,1]*H).astype(int),0,H-1); return al[y,x]
    UV=r['uv']; vin=inside(UV)
    cen=UV[idx].mean(1); cin=inside(cen)
    keep=cin|(vin[idx].sum(1)>=1)
    T=idx[keep]
    u,inv=np.unique(T.ravel(),return_inverse=True); r2=r[u]; T2=inv.reshape(-1,3)
    nv=len(r2); assert nv<65536
    with open(out_cup,'wb') as f:
        f.write(b'CUP1'+struct.pack('<3i',nv,T2.size,0)); f.write(r2.tobytes()); f.write(T2.astype('<u2').reshape(-1,3).tobytes())
    return nv,len(T2)

def dilate_fill(rgb,alpha,px=8):
    mask=alpha>128
    d,(iy,ix)=ndimage.distance_transform_edt(~mask,return_indices=True)
    out=rgb[iy,ix]
    out[d>px]=0
    return out

def variants(OUTD,g):
    S='/tmp/sg/'
    A0=np.array(Image.open(S+'img_0.png')); alpha=A0[...,3]
    gray={'plain':np.array(Image.open(S+'img_9.png').convert('RGB')).astype(np.float32),
          'love':np.array(Image.open(S+'img_2.png').convert('RGB')).astype(np.float32),
          'haters':np.array(Image.open(S+'img_5.png').convert('RGB')).astype(np.float32)}
    mask={'love':np.array(Image.open(S+'img_1.png').convert('RGB')),'haters':np.array(Image.open(S+'img_4.png').convert('RGB'))}
    res={}
    res['white']=gray['plain']
    res['black']=gray['plain']*0.17
    for k in ('love','haters'):
        m=mask[k]; text=(m[...,0]>150)&(m[...,2]>150)&(m[...,1]<110)
        b=gray[k]*0.17
        b[text]=gray[k][text]
        res[k]=b
    return res,alpha

if __name__=='__main__':
    import os
    OUTD=sys.argv[1]
    res,alpha=variants(OUTD,None)
    for name,rgb in res.items():
        t=dilate_fill(np.clip(rgb,0,255).astype(np.uint8),alpha)
        rgba=np.dstack([t,alpha]).astype(np.uint8)
        Image.fromarray(rgba,'RGBA').save('/tmp/sg/tex_%s.png'%name,optimize=True)
    for g in ('am','tm','em'):
        print(g,process(g,'/tmp/sg/img_0.png','/tmp/sg/fit_%s_raw.cup'%g,'/tmp/sg/singlet_%s.cup'%g))
