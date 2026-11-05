import numpy as np, os
from PIL import Image
from flora_lib import *
def preview_rgba(asset,fn,size=(256,256),span=None):
    views=('front',)
    arr=asset.arrays(); allP=np.vstack([a[1] for a in arr]); lo=allP.min(0); hi=allP.max(0); c=(lo+hi)/2
    ext=span or max(hi[1]-lo[1],hi[0]-lo[0],hi[2]-lo[2])*1.1
    W,H=size; sc=H/ext; imgs=[]
    L=np.array([0.45,1.0,0.65]); L/=np.linalg.norm(L)
    for view in views:
        img=np.zeros((H,W,3),np.float32)
        zb=np.full((H,W),-1e9)
        for (t,mat,cut),P,N,C,UV,T in arr:
            tx=tex_cache(t) if os.path.exists(OUT+'tex/'+t) else None
            if view=='front': X=W/2+(P[:,0]-c[0])*sc; Z=P[:,2]
            elif view=='side': X=W/2+(P[:,2]-c[2])*sc; Z=P[:,0]
            else: X=W/2+(P[:,0]-c[0])*sc; Z=P[:,1]
            Y=H*0.5-(P[:,1]-c[1])*sc if view!='top' else H*0.5-(P[:,2]-c[2])*sc
            if view=='side': pass
            for tri in T:
                xs=X[tri];ys=Y[tri];zs=Z[tri]
                x0,x1=int(max(0,xs.min())),int(min(W-1,xs.max()+1)); y0,y1=int(max(0,ys.min())),int(min(H-1,ys.max()+1))
                if x1<x0 or y1<y0: continue
                gx,gy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1))
                d=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
                if abs(d)<1e-9: continue
                a=((ys[1]-ys[2])*(gx-xs[2])+(xs[2]-xs[1])*(gy-ys[2]))/d; b=((ys[2]-ys[0])*(gx-xs[2])+(xs[0]-xs[2])*(gy-ys[2]))/d; cc=1-a-b
                m=(a>=-1e-3)&(b>=-1e-3)&(cc>=-1e-3)
                if not m.any(): continue
                z=a*zs[0]+b*zs[1]+cc*zs[2]; m&=z>zb[y0:y1+1,x0:x1+1]
                nn=a[...,None]*N[tri[0]]+b[...,None]*N[tri[1]]+cc[...,None]*N[tri[2]]; nl=np.linalg.norm(nn,axis=-1); nn=nn/np.maximum(nl[...,None],1e-9)
                diff=np.clip((nn*L).sum(-1),0,1); amb=0.42+0.18*(0.5+0.5*nn[...,1]); light=np.where(nl<0.1,1.0,amb+0.62*diff)
                vc=a[...,None]*C[tri[0]][:3]+b[...,None]*C[tri[1]][:3]+cc[...,None]*C[tri[2]][:3]
                if tx is not None:
                    u=a*UV[tri[0],0]+b*UV[tri[1],0]+cc*UV[tri[2],0]; v=a*UV[tri[0],1]+b*UV[tri[1],1]+cc*UV[tri[2],1]
                    th,tw=tx.shape[:2]; ix=(u*tw).astype(int)%tw if not cut else np.clip((u*tw).astype(int),0,tw-1); iy=(v*th).astype(int)%th if not cut else np.clip((v*th).astype(int),0,th-1)
                    tv=tx[iy,ix]; col=tv[...,:3].astype(float)
                    if cut: m=m&(tv[...,3]>127)
                else: col=np.full(m.shape+(3,),200.0)
                col=col*vc*light[...,None]
                sub=img[y0:y1+1,x0:x1+1]; sub[m]=col[m]; zb[y0:y1+1,x0:x1+1][m]=z[m]
        rgb=np.clip(img,0,255).astype(np.uint8); al=((zb>-1e8)*255).astype(np.uint8)
    Image.fromarray(np.dstack([rgb,al]),'RGBA').save(fn)
