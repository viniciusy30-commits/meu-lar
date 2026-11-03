import numpy as np, sys
sys.path.insert(0,'/home/claude/work/proto')
from PIL import Image
def raster(P,N,tri,view,size=(520,760),ymax=190,color=(200,200,200),tex=None,UV=None,bodyP=None,bodyTri=None,bodyN=None,state=None):
    W,H=size
    if state is None: img=np.zeros((H,W,3),np.uint8)+40; zb=np.full((H,W),-1e9)
    else: img,zb=state
    sc=H/ymax*0.96
    def proj(p):
        if view=='front': return (W/2+p[:,0]*sc, H-p[:,1]*sc-10, p[:,2])
        if view=='side': return (W/2+p[:,2]*sc, H-p[:,1]*sc-10, p[:,0])
        if view=='back': return (W/2-p[:,0]*sc, H-p[:,1]*sc-10, -p[:,2])
    L=np.array([0.3,0.5,0.8]); L/=np.linalg.norm(L)
    if view=='back': L=np.array([-0.3,0.5,-0.8])
    if view=='side': L=np.array([0.8,0.5,0.3])
    X,Y,Z=proj(P)
    for ti,t in enumerate(tri):
        xs=X[t]; ys=Y[t]; zs=Z[t]
        x0,x1=int(max(0,xs.min())),int(min(W-1,xs.max())); y0,y1=int(max(0,ys.min())),int(min(H-1,ys.max()))
        if x1<x0 or y1<y0: continue
        gx,gy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1))
        d=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
        if abs(d)<1e-9: continue
        a=((ys[1]-ys[2])*(gx-xs[2])+(xs[2]-xs[1])*(gy-ys[2]))/d; b=((ys[2]-ys[0])*(gx-xs[2])+(xs[0]-xs[2])*(gy-ys[2]))/d; c=1-a-b
        m=(a>=0)&(b>=0)&(c>=0)
        if not m.any(): continue
        z=a*zs[0]+b*zs[1]+c*zs[2]; m&=z>zb[y0:y1+1,x0:x1+1]
        nn=a[...,None]*N[t[0]]+b[...,None]*N[t[1]]+c[...,None]*N[t[2]]
        nn/=np.maximum(np.linalg.norm(nn,axis=-1,keepdims=True),1e-9)
        sh=np.clip(np.abs((nn*L).sum(-1)),0,1)*0.75+0.25
        if tex is not None:
            u=a*UV[t[0],0]+b*UV[t[1],0]+c*UV[t[2],0]; v=a*UV[t[0],1]+b*UV[t[1],1]+c*UV[t[2],1]
            th,tw=tex.shape[:2]; col=tex[np.clip((v*th).astype(int),0,th-1),np.clip((u*tw).astype(int),0,tw-1)][...,:3].astype(float)
        else: col=np.zeros(m.shape+(3,))+np.array(color,float)
        col=col*sh[...,None]
        sub=img[y0:y1+1,x0:x1+1]; sub[m]=col[m].astype(np.uint8); zb[y0:y1+1,x0:x1+1][m]=z[m]
    return img
