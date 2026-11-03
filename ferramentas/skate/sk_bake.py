import numpy as np
from scipy.spatial import cKDTree
from scipy import ndimage
from sk_common import *

TS=512; AW=TS*3; AH=TS*2

def prepare(P,N,tri,btype_fn):
    """bd/btype por vértice (antes das beiradas), depois fecha as bordas com beirada."""
    be=boundary_edges(tri)
    bv=np.unique(np.array(be).ravel()) if be else np.array([],int)
    bd=np.full(len(P),99.0); bt=np.zeros(len(P))
    if len(bv):
        tree=cKDTree(P[bv]); d,ix=tree.query(P)
        bd=d; types=np.array([btype_fn(P[v]) for v in bv]); bt=types[ix].astype(float)
    attr=np.stack([bd,bt],1)
    P2,N2,T2,A2,_=add_lips(P,N,tri,attr,0.55)
    nb=len(P)
    A2[nb:,0]=0.0
    return P2,N2,T2,A2

def unwrap(P,N,tri,A):
    """divide em 6 telas planares (frente, costas, +x, -x, cima, baixo) por triângulo; devolve malha com vértices duplicados por tela."""
    lo=P.min(0)-0.3; hi=P.max(0)+0.3; W=hi-lo
    a,b,c=P[tri[:,0]],P[tri[:,1]],P[tri[:,2]]
    fn=np.cross(b-a,c-a); fn/=np.maximum(np.linalg.norm(fn,axis=1,keepdims=True),1e-12)
    ax=np.argmax(np.abs(fn),axis=1); sg=np.take_along_axis(fn,ax[:,None],1)[:,0]>0
    tile=np.where(ax==2,np.where(sg,0,1),np.where(ax==0,np.where(sg,2,3),np.where(sg,4,5)))
    keymap={}; Pn=[];Nn=[];An=[];UV=[];T=[]
    def uv_for(p,t):
        x,y,z=p
        if t==0: u=(x-lo[0])/W[0]; v=1-(y-lo[1])/W[1]
        elif t==1: u=(hi[0]-x)/W[0]; v=1-(y-lo[1])/W[1]
        elif t==2: u=(hi[2]-z)/W[2]; v=1-(y-lo[1])/W[1]
        elif t==3: u=(z-lo[2])/W[2]; v=1-(y-lo[1])/W[1]
        elif t==4: u=(x-lo[0])/W[0]; v=(hi[2]-z)/W[2]
        else: u=(x-lo[0])/W[0]; v=(z-lo[2])/W[2]
        col=t%3; row=t//3; pad=3.0/TS
        u=pad+u*(1-2*pad); v=pad+v*(1-2*pad)
        return ((col+u)/3.0,(row+v)/2.0)
    for ti,t in enumerate(tri):
        tl=int(tile[ti]); row=[]
        for v in t:
            k=(int(v),tl)
            if k not in keymap:
                keymap[k]=len(Pn); Pn.append(P[v]); Nn.append(N[v]); An.append(A[v]); UV.append(uv_for(P[v],tl))
            row.append(keymap[k])
        T.append(row)
    return np.array(Pn),np.array(Nn),np.array(An),np.array(UV),np.array(T,np.int64)

def raster_attrs(UV,T,feat):
    """feat: (nv,k) -> imagem (AH,AW,k) por rasterização em UV; devolve também máscara."""
    k=feat.shape[1]; img=np.zeros((AH,AW,k),np.float32); mask=np.zeros((AH,AW),bool)
    X=UV[:,0]*AW; Y=UV[:,1]*AH
    for t in T:
        xs=X[t]; ys=Y[t]
        x0=int(max(0,np.floor(xs.min()))); x1=int(min(AW-1,np.ceil(xs.max()))); y0=int(max(0,np.floor(ys.min()))); y1=int(min(AH-1,np.ceil(ys.max())))
        if x1<x0 or y1<y0: continue
        d=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
        if abs(d)<1e-9: continue
        gx,gy=np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5)
        a=((ys[1]-ys[2])*(gx-xs[2])+(xs[2]-xs[1])*(gy-ys[2]))/d; b=((ys[2]-ys[0])*(gx-xs[2])+(xs[0]-xs[2])*(gy-ys[2]))/d; c=1-a-b
        m=(a>=-0.02)&(b>=-0.02)&(c>=-0.02)
        if not m.any(): continue
        val=a[...,None]*feat[t[0]]+b[...,None]*feat[t[1]]+c[...,None]*feat[t[2]]
        sub=img[y0:y1+1,x0:x1+1]; sub[m]=val[m]; mask[y0:y1+1,x0:x1+1]|=m
    # dilata (preenche o vazio com o texel mais próximo: evita linhas nas emendas)
    idx=ndimage.distance_transform_edt(~mask,return_distances=False,return_indices=True)
    img=img[idx[0],idx[1]]
    return img,mask
