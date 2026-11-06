import sys,numpy as np
from PIL import Image
def raster(meshes,S,view,box):
    # meshes: list of (P,UV,CC,I,tex(rgba arr or None),acut). view: 'f','s','b','q'
    ang={'f':0,'s':90,'b':180,'q':35}[view]; a=np.radians(ang); R=np.array([[np.cos(a),0,-np.sin(a)],[0,1,0],[np.sin(a),0,np.cos(a)]])
    img=np.full((S,S,3),205,np.uint8); zb=np.full((S,S),-1e9)
    (cx,cy),h=box; sc=S/h
    for P,UV,CC,I,tx,acut in meshes:
        Q=P@R.T; X=Q[:,0]; Y=Q[:,1]; Z=Q[:,2]
        sx=(X-cx)*sc+S/2; sy=S/2-(Y-cy)*sc
        if tx is not None: th,tw=tx.shape[:2]
        for a_,b_,c_ in I:
            xs=sx[[a_,b_,c_]]; ys=sy[[a_,b_,c_]]
            x0,x1=int(max(0,xs.min())),int(min(S-1,xs.max()+1)); y0,y1=int(max(0,ys.min())),int(min(S-1,ys.max()+1))
            if x1<x0 or y1<y0: continue
            gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
            d=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
            if abs(d)<1e-9: continue
            l0=((ys[1]-ys[2])*(gx-xs[2])+(xs[2]-xs[1])*(gy-ys[2]))/d; l1=((ys[2]-ys[0])*(gx-xs[2])+(xs[0]-xs[2])*(gy-ys[2]))/d; l2=1-l0-l1
            m=(l0>=0)&(l1>=0)&(l2>=0)
            if not m.any(): continue
            z=(l0*Z[a_]+l1*Z[b_]+l2*Z[c_]); yy=gy[m].astype(int); xx=gx[m].astype(int); zz=z[m]
            u=(l0*UV[a_,0]+l1*UV[b_,0]+l2*UV[c_,0])[m]; w=(l0*UV[a_,1]+l1*UV[b_,1]+l2*UV[c_,1])[m]
            cc=(l0[...,None]*CC[a_]+l1[...,None]*CC[b_]+l2[...,None]*CC[c_])[m]
            if tx is not None:
                t=tx[np.clip((w*th).astype(int),0,th-1),np.clip((u*tw).astype(int),0,tw-1)]
                keep=t[:,3]/255.>acut; col=cc*t[:,:3]/255.
            else: keep=np.ones(len(zz),bool); col=cc
            ok=(zz>zb[yy,xx])&keep
            zb[yy[ok],xx[ok]]=zz[ok]; img[yy[ok],xx[ok]]=np.clip(col[ok]*255,0,255)
    return (img,zb) if False else img
