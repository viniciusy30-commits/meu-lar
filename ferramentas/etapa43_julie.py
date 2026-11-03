#!/usr/bin/env python3
"""Etapa 43: Julie (Sims 3, MTS whiterider Bodies/Faces/Skins) -> p_body_julie.bin + julie.png + p_hairback_heartbeatjulie.bin.
Uso: python3 etapa43_julie.py <pasta com bodies/ faces/ skins/ (RARs extraidos)> <assets/cute>
Corpo afBody_fit + afface + afscalp ligados ao esqueleto do app (pesos do base.bin por vizinho mais proximo), olhos esfericos,
sobrancelhas, top e short pintados, cabelo Heartbeat reajustado a cabeca dela. Pele do corpo: tfBody.dds (afBody.dds veio corrompido no RAR)."""
import sys as _s
RAWDIR=_s.argv[1] if len(_s.argv)>1 else '.'; CUDIR=_s.argv[2] if len(_s.argv)>2 else '.'

# ---- objr.py ----
import numpy as np
def load(path):
    V=[];T=[];N=[];F=[]
    for l in open(path,errors='ignore'):
        p=l.split()
        if not p: continue
        if p[0]=='v': V.append(list(map(float,p[1:4])))
        elif p[0]=='vt': T.append(list(map(float,p[1:3])))
        elif p[0]=='vn': N.append(list(map(float,p[1:4])))
        elif p[0]=='f':
            vs=[tuple((int(x)-1 if x else -1) for x in (q.split('/')+['','',''])[:3]) for q in p[1:]]
            for i in range(1,len(vs)-1): F.append((vs[0],vs[i],vs[i+1]))
    V=np.array(V);T=np.array(T) if T else np.zeros((1,2));N=np.array(N) if N else np.zeros((1,3))
    key={};pos=[];uv=[];nor=[];idx=[]
    for tri in F:
        for (a,b,c) in tri:
            k=(a,b,c)
            if k not in key:
                key[k]=len(pos);pos.append(V[a]);uv.append(T[b] if b>=0 else [0,0]);nor.append(N[c] if c>=0 else [0,0,0])
            idx.append(key[k])
    return dict(pos=np.array(pos),uv=np.array(uv),nor=np.array(nor),idx=np.array(idx).reshape(-1,3))
def render(meshes,yaw=0,W=360,H=640,center=(0,0.9,0),scale=300,bg=(70,76,90),tex=None):
    img=np.zeros((H,W,3),np.float32)+np.array(bg,np.float32);zb=np.full((H,W),1e9)
    c,s=np.cos(np.radians(yaw)),np.sin(np.radians(yaw))
    R=np.array([[c,0,s],[0,1,0],[-s,0,c]])
    for m in meshes:
        P=(m['pos']-np.array(center))@R.T
        sx=W/2+P[:,0]*scale; sy=H/2-P[:,1]*scale; z=-P[:,2]
        n=m['nor']@R.T if 'nor' in m and np.abs(m['nor']).sum()>0 else None
        col=m.get('color',(220,180,160)); tx=m.get('tex')
        for t in m['idx']:
            x=sx[t];y=sy[t];x0,x1=int(max(x.min(),0)),int(min(x.max()+1,W-1));y0,y1=int(max(y.min(),0)),int(min(y.max()+1,H-1))
            if x1<=x0 or y1<=y0: continue
            gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
            d=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
            if abs(d)<1e-9: continue
            l0=((y[1]-y[2])*(gx-x[2])+(x[2]-x[1])*(gy-y[2]))/d
            l1=((y[2]-y[0])*(gx-x[2])+(x[0]-x[2])*(gy-y[2]))/d
            l2=1-l0-l1; ins=(l0>=0)&(l1>=0)&(l2>=0)
            if not ins.any(): continue
            zz=l0*z[t[0]]+l1*z[t[1]]+l2*z[t[2]]
            yy,xx=np.nonzero(ins); yy=yy+y0; xx=xx+x0; ok=zz[ins]<zb[yy,xx]
            yy,xx=yy[ok],xx[ok]; zb[yy,xx]=zz[ins][ok]
            a0,a1,a2=l0[ins][ok],l1[ins][ok],l2[ins][ok]
            if n is not None: nn=a0[:,None]*n[t[0]]+a1[:,None]*n[t[1]]+a2[:,None]*n[t[2]]; nn/=np.linalg.norm(nn,axis=1,keepdims=True)+1e-9
            else:
                e1=P[t[1]]-P[t[0]];e2=P[t[2]]-P[t[0]];nn=np.cross(e1,e2);nn=nn/(np.linalg.norm(nn)+1e-9);nn=np.tile(nn,(len(yy),1))
            sh=np.clip(nn[:,2]*0.6+nn[:,1]*0.3+0.35,0.2,1.1)
            if tx is not None:
                uv=a0[:,None]*m['uv'][t[0]]+a1[:,None]*m['uv'][t[1]]+a2[:,None]*m['uv'][t[2]]
                h,w=tx.shape[:2]; u=np.clip((uv[:,0]*w).astype(int),0,w-1); v=np.clip(((1-uv[:,1])*h).astype(int),0,h-1)
                cc=tx[v,u,:3].astype(np.float32)
                if m.get('cut') and tx.shape[2]==4:
                    keep=tx[v,u,3]>=m['cut']*255
                    zb[yy[~keep],xx[~keep]]=1e9; yy=yy[keep];xx=xx[keep];cc=cc[keep];sh=sh[keep]
            else: cc=np.array(col,np.float32)[None,:]
            img[yy,xx]=cc*sh[:,None]
    return np.clip(img,0,255).astype(np.uint8)

# ---- gen1.py ----
import numpy as np, struct, sys
from scipy.spatial import cKDTree
CU=CUDIR.rstrip('/')+'/'
def read_base(path=CU+'base.bin'):
    b=open(path,'rb').read(); nv,ni=struct.unpack('<2i',b[4:12])
    dt=np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)])
    r=np.frombuffer(b,dt,nv,20); idx=np.frombuffer(b,'<u2',ni,20+nv*dt.itemsize).astype(np.int64)
    return r, idx.reshape(-1,3)
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
YS=[0,48,93,400]; YT=[-0.2,54.4,95.2,95.2+(400-93)*0.91]
def warp_body(P):
    """Sims 3 (cm) -> espaco do app: y por partes (pernas casam com as juntas do esqueleto), x/z um pouco menores acima do quadril"""
    Q=P.copy(); Q[:,1]=np.interp(P[:,1],YS,YT)
    s=np.interp(P[:,1],[0,75,93,400],[1.0,1.0,0.93,0.93]); Q[:,0]*=s; Q[:,2]*=s
    return Q

PIV=np.array([16.0,141.0,0.0])
def pose_arms(Q, ang_deg=9.3, scale=0.94):
    """gira os bracos em volta do ombro (A-pose do Sims 3 -> pose dos bracos do app) e encurta; peso suave perto do ombro"""
    Q=Q.copy()
    for sg in (1,-1):
        piv=PIV*np.array([sg,1,1])
        w=smooth(22,34,np.abs(Q[:,0]))*(Q[:,1]<150)*(Q[:,0]*sg>0)
        sel=w>0
        d=Q[sel]-piv; ang=np.radians(ang_deg)*w[sel]
        xs=d[:,0]*sg; ys=d[:,1]
        xr=xs*np.cos(ang)+ys*np.sin(ang); yr=-xs*np.sin(ang)+ys*np.cos(ang)
        k=1-(1-scale)*w[sel]
        d2=d.copy(); d2[:,0]=xr*sg*k; d2[:,1]=yr*k
        Q[sel]=piv+d2
    return Q

# ---- gen2.py ----
import numpy as np, struct, sys, os
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
RAW=RAWDIR.rstrip('/')+'/'
AW,AH=2048,1280
EYE_BLK=(0,1024,512,256); HAIR_BLK=(1024,1024,64)
IRIS=np.array([112,82,48],float)

def raster_uv(m, size=1024):
    """interpola a posicao 3D de cada texel da UV do corpo (mascara + posicoes)"""
    P3=np.zeros((size,size,3)); mask=np.zeros((size,size),bool)
    uv=m['uv'].copy(); X=uv[:,0]*size; Y=(1-uv[:,1])*size
    for t in m['idx']:
        x=X[t];y=Y[t]; x0,x1=int(max(x.min()-1,0)),int(min(x.max()+1,size-1)); y0,y1=int(max(y.min()-1,0)),int(min(y.max()+1,size-1))
        gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        d=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
        if abs(d)<1e-9: continue
        l0=((y[1]-y[2])*(gx-x[2])+(x[2]-x[1])*(gy-y[2]))/d; l1=((y[2]-y[0])*(gx-x[2])+(x[0]-x[2])*(gy-y[2]))/d; l2=1-l0-l1
        ins=(l0>=-0.02)&(l1>=-0.02)&(l2>=-0.02)
        p=l0[...,None]*m['pos'][t[0]]+l1[...,None]*m['pos'][t[1]]+l2[...,None]*m['pos'][t[2]]
        sub=P3[y0:y1+1,x0:x1+1]; sub[ins]=p[ins]; mask[y0:y1+1,x0:x1+1]|=ins
    return P3,mask

def fill_outside(img, mask):
    """estende a cor dos ilhas da UV para fora (sem halo/emenda no filtro bilinear)"""
    ii=ndimage.distance_transform_edt(~mask,return_distances=False,return_indices=True)
    out=img.copy(); out[~mask]=img[ii[0][~mask],ii[1][~mask]]; return out

def paint_outfit(skin, P3, mask, body_m):
    """biquini-top + short jeans pintados na pele, por posicao 3D (m do Sims 3)"""
    X,Y,Z=P3[...,0],P3[...,1],P3[...,2]
    pm=body_m['pos']; sl=lambda y:pm[(np.abs(pm[:,1]-y)<0.02)&(np.abs(pm[:,0])<0.3)]
    ys=np.arange(1.0,1.32,0.01); wid=[(np.ptp(sl(y)[:,0]) if len(sl(y)) else 9) for y in ys]; waist=ys[int(np.argmin(wid))]
    ys2=np.arange(1.15,1.5,0.01); zf=[sl(y)[:,2].max() if len(sl(y)) else -9 for y in ys2]; bust=ys2[int(np.argmax(zf))]
    print('waist',waist,'bust',bust)
    ed=0.006
    def band(a,b): return smooth(a-ed,a+ed,Y)*(1-smooth(b-ed,b+ed,Y))
    xl=1-smooth(0.19-0.01,0.19+0.01,np.abs(X))   # so o tronco (bracos ficam de fora)
    top=band(bust-0.075,bust+0.085)*xl
    # tira o topo atras do pescoco/ombro: alca fina so na frente
    shorts=band(0.84,waist-0.065)*(1-smooth(0.27,0.29,np.abs(X)))
    rng=np.random.RandomState(3); n=ndimage.gaussian_filter(rng.randn(*Y.shape),1.2)*0.5+ndimage.gaussian_filter(rng.randn(*Y.shape),4)*0.8
    fab_top=np.array([246,244,240],float)[None,None,:]*(1+0.02*n[...,None])
    jeans=np.array([63,92,140],float)[None,None,:]*(1+0.06*n[...,None])
    # pesponto: faixa de cos mais escura e barra clara
    cos=band(waist-0.085,waist-0.065); bar=band(0.84,0.855)
    jeans=jeans*(1-0.22*cos[...,None])+np.array([120,150,195])*0.0
    jeans=jeans*(1-bar[...,None]*0.15)+np.array([205,220,240])*bar[...,None]*0.25
    out=skin.copy()
    out=out*(1-top[...,None])+fab_top*top[...,None]
    out=out*(1-shorts[...,None])+jeans*shorts[...,None]
    return np.clip(out,0,255)

# ---- gen3.py ----
import numpy as np, struct, sys, os
from PIL import Image, ImageDraw, ImageFilter

def uv_to_3d(m, px, py, size=1024):
    uv=m['uv']; X=uv[:,0]*size; Y=(1-uv[:,1])*size
    for t in m['idx']:
        x=X[t];y=Y[t]
        if px<x.min() or px>x.max() or py<y.min() or py>y.max(): continue
        d=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
        if abs(d)<1e-12: continue
        l0=((y[1]-y[2])*(px-x[2])+(x[2]-x[1])*(py-y[2]))/d; l1=((y[2]-y[0])*(px-x[2])+(x[0]-x[2])*(py-y[2]))/d; l2=1-l0-l1
        if l0>=-1e-6 and l1>=-1e-6 and l2>=-1e-6:
            n=l0*m['nor'][t[0]]+l1*m['nor'][t[1]]+l2*m['nor'][t[2]]
            return l0*m['pos'][t[0]]+l1*m['pos'][t[1]]+l2*m['pos'][t[2]], n/np.linalg.norm(n)
    return None,None

def vnormals(P, idx, ref_n=None):
    """normais suaves (soldando vertices na mesma posicao); devolve (normais, idx possivelmente com a ordem das faces invertida)"""
    key=np.round(P*1000).astype(np.int64); _,inv=np.unique(key,axis=0,return_inverse=True); inv=inv.reshape(-1)
    e1=P[idx[:,1]]-P[idx[:,0]]; e2=P[idx[:,2]]-P[idx[:,0]]; fn=np.cross(e1,e2)
    N=np.zeros((inv.max()+1,3))
    for k in range(3): np.add.at(N,inv[idx[:,k]],fn)
    n=N[inv]; n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-12)
    if ref_n is not None and (n*ref_n).sum(1).mean()<0:
        n=-n; idx=idx[:,::-1].copy()
    return n, idx

def eye_texture():
    W,H=EYE_BLK[2],EYE_BLK[3]
    lon=(np.arange(W)+.5)/W; lat_v=(np.arange(H)+.5)/H
    LON=(lon[None,:]-.5)*2*np.pi; LAT=(.5-lat_v[:,None])*np.pi
    dx=np.cos(LAT)*np.sin(LON); dy=np.sin(LAT)+0*LON; dz=np.cos(LAT)*np.cos(LON)
    th=np.arccos(np.clip(dz,-1,1))
    img=np.zeros((H,W,3)); img[:]=np.array([243,239,235])
    img*= (1-0.10*smooth(0.55,1.2,th))[...,None]               # esclera sombreia nas bordas
    img*= (1-0.07*np.clip(-dy*1.0,0,1))[...,None]
    R=0.50
    iris=np.array(IRIS); inner=np.clip(iris*1.35+18,0,255); rim=np.clip(iris*0.45,0,255)
    t=np.clip(th/R,0,1)
    col=inner[None,None,:]*(1-smooth(0.15,0.75,t))[...,None]+iris[None,None,:]*smooth(0.15,0.75,t)[...,None]
    col=col*(1-smooth(0.80,1.0,t))[...,None]+rim*smooth(0.80,1.0,t)[...,None]
    a=1-smooth(R-0.025,R+0.01,th)
    img=img*(1-a[...,None])+col*a[...,None]
    pup=1-smooth(0.17,0.21,th); img=img*(1-pup[...,None])+np.array([14,11,11])*pup[...,None]
    # brilho (catch-light) em cima/esquerda
    cx,cy,cz=np.array([-0.22,0.24,0.94])/np.linalg.norm([-0.22,0.24,0.94])
    ang=np.arccos(np.clip(dx*cx+dy*cy+dz*cz,-1,1)); hl=1-smooth(0.05,0.085,ang)
    img=img*(1-0.9*hl[...,None])+255*0.9*hl[...,None]
    return np.clip(img,0,255)

def make_sphere(center, r, nlon=22, nlat=14):
    P=[];N=[];UV=[];I=[]
    for j in range(nlat+1):
        lat=np.pi/2-np.pi*j/nlat
        for i in range(nlon+1):
            lo=(i/nlon-.5)*2*np.pi
            d=np.array([np.cos(lat)*np.sin(lo),np.sin(lat),np.cos(lat)*np.cos(lo)])
            P.append(center+d*r);N.append(d);UV.append(((EYE_BLK[0]+(i/nlon)*EYE_BLK[2]-0)/AW,(EYE_BLK[1]+(j/nlat)*EYE_BLK[3])/AH))
    for j in range(nlat):
        for i in range(nlon):
            a=j*(nlon+1)+i;b=a+1;c=a+nlon+1;d=c+1
            I+= [a,c,b,b,c,d]
    return np.array(P),np.array(N),np.array(UV),np.array(I).reshape(-1,3)

def paint_face(face_rgb):
    """sobrancelhas e delineado suave por cima da pele do rosto (a UV do Sims 3 nao traz isso)"""
    base=Image.fromarray(face_rgb.astype(np.uint8)).convert('RGBA'); S=4
    L=Image.new('L',(1024*2,1024*2),0)  # mascara de sobrancelha (2x para suavizar)
    dr=ImageDraw.Draw(L)
    def brow(cx,cy,sg):
        pts=[(cx+sg*46,cy-62),(cx+sg*22,cy-76),(cx-sg*8,cy-83),(cx-sg*38,cy-76),(cx-sg*66,cy-60)]
        th=[8,11,12,10,5]
        # curva suave por interpolacao linear densa
        P=np.array(pts,float)*2; t=np.linspace(0,1,60); xs=np.interp(t,np.linspace(0,1,len(P)),P[:,0]); ys=np.interp(t,np.linspace(0,1,len(P)),P[:,1]); ws=np.interp(t,np.linspace(0,1,len(th)),np.array(th)*2)
        for x,y,w in zip(xs,ys,ws): dr.ellipse([x-w/2,y-w/2,x+w/2,y+w/2],fill=255)
    brow(369,362,1); brow(659,364,-1)
    L=L.resize((1024,1024),Image.LANCZOS).filter(ImageFilter.GaussianBlur(2.2))
    a=np.asarray(L).astype(float)/255*0.62
    col=np.array([78,52,38],float)
    rgb=np.asarray(base)[...,:3].astype(float)
    rgb=rgb*(1-a[...,None])+col*a[...,None]
    # delineado: arco superior em volta do buraco do olho
    L2=Image.new('L',(2048,2048),0); d2=ImageDraw.Draw(L2)
    for cx,cy in ((369,362),(659,364)):
        for k in range(-60,61):
            t=np.radians(180+ (k+60)*1.5 - 0) ; 
        arc=[(2*(cx+50*np.cos(np.radians(a_))),2*(cy-34*np.sin(np.radians(a_)))) for a_ in np.linspace(-12,192,50)]
        d2.line(arc,fill=255,width=11)
    L2=L2.resize((1024,1024),Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.6))
    a2=np.asarray(L2).astype(float)/255*0.55
    rgb=rgb*(1-a2[...,None])+np.array([46,32,28])*a2[...,None]
    return np.clip(rgb,0,255)

# ---- gen4.py ----
import numpy as np, struct, sys, os, json

def build(out_dir='/home/claude/jx/out', body_name='afBody_fit'):
    body=load(RAW+'bodies/%s.obj'%body_name); face=load(RAW+'faces/afface.obj'); scalp=load(RAW+'faces/afscalp.obj')
    # --- texturas ---
    fimg=np.asarray(Image.open(RAW+'skins/afFace.dds').convert('RGB')).astype(float)
    bimg=np.asarray(Image.open(RAW+'skins/tfBody.dds').convert('RGB')).astype(float)
    fm=fimg.reshape(-1,3).mean(0); bm=bimg.reshape(-1,3).mean(0)
    bimg=np.clip(bimg*(fm/bm)[None,None,:],0,255)
    P3,mask=raster_uv(body)
    bsk=paint_outfit(bimg,P3*100/100.0,mask,body)
    bsk=fill_outside(bsk,mask)
    fsk=paint_face(fimg)
    atlas=np.zeros((AH,AW,3)); atlas[:]=fm
    atlas[0:1024,0:1024]=bsk; atlas[0:1024,1024:2048]=fsk
    atlas[EYE_BLK[1]:EYE_BLK[1]+EYE_BLK[3],EYE_BLK[0]:EYE_BLK[0]+EYE_BLK[2]]=eye_texture()
    hb=np.asarray(Image.open(CU+'heartbeat.png').convert('RGBA'))[0:128,512:640]; hair_rgb=hb[...,:3][hb[...,3]>200].mean(0)
    hx,hy,hs=HAIR_BLK; atlas[hy:hy+hs,hx:hx+hs]=hair_rgb
    # --- malhas no espaco do app ---
    def xf(m): 
        return pose_arms(warp_body(m['pos']*100))
    parts=[]
    for name,m,xo in (('body',body,0),('face',face,1024),('scalp',scalp,None)):
        pos=xf(m); idx=m['idx'].copy()
        n,idx=vnormals(pos,idx,m['nor'])
        if xo is None: uvA=np.tile([(hx+hs/2)/AW,(hy+hs/2)/AH],(len(pos),1))
        else:
            sx=(xo+m['uv'][:,0]*1024)/AW; sy=((1-m['uv'][:,1])*1024)/AH; uvA=np.stack([sx,sy],1)
        parts.append(dict(name=name,pos=pos,nor=n,uv=uvA,idx=idx))
    # --- olhos: esferas nos buracos do rosto ---
    eyes=[]
    ctr=[]
    for cx,cy in ((369,362),(659,364)):
        p,n=uv_to_3d(face,cx,cy); pl,_=uv_to_3d(face,cx-40,cy); pr,_=uv_to_3d(face,cx+40,cy)
        wid=np.linalg.norm(pl-pr)*100       # largura do buraco (cm do Sims)
        ctr.append((p*100,n,wid)); 
    fpos=xf(face)
    for (p,n,wid) in ctr:
        r=0.50*wid*0.93; c=warp_body(p[None,:])[0]-n*0.55*r*np.array([0.2,0.2,1.0])*0+0  # centro: atras da superficie
        c=warp_body(p[None,:])[0]-n*0.55*r
        P,N,UV,I=make_sphere(c,r)
        eyes.append(dict(name='eye',pos=P,nor=N,uv=UV,idx=I))
    print('hole widths',[round(c[2],2) for c in ctr],'eye r',r)
    # --- pesos do esqueleto ---
    br,bidx=read_base(); bpos=br['pos'].astype(float); tree=cKDTree(bpos)
    def weights(P):
        d,j=tree.query(P,k=8); wn=1.0/(d+0.5)**2
        BI=np.zeros((len(P),4),np.uint8); BW=np.zeros((len(P),4),np.uint8)
        for v in range(len(P)):
            acc={}
            for q in range(8):
                for s in range(4):
                    w=br['bw'][j[v,q],s]
                    if w: acc[int(br['bi'][j[v,q],s])]=acc.get(int(br['bi'][j[v,q],s]),0)+w*wn[v,q]
            top=sorted(acc.items(),key=lambda a:-a[1])[:4]; tot=sum(a[1] for a in top)
            ws=[int(round(255*a[1]/tot)) for a in top]; ws[0]+=255-sum(ws)
            for s,(b,_) in enumerate(top): BI[v,s]=b; BW[v,s]=ws[s]
        return BI,BW
    for pt in parts+eyes:
        n=len(pt['pos'])
        if pt['name']=='body':
            BI,BW=weights(pt['pos'])
            head=pt['pos'][:,1]>=158; BI[head]=[8,0,0,0]; BW[head]=[255,0,0,0]
        else:
            BI=np.zeros((n,4),np.uint8); BW=np.zeros((n,4),np.uint8); BI[:,0]=8; BW[:,0]=255
        pt['bi']=BI; pt['bw']=BW
    return atlas, parts+eyes, dict(body=body,face=face,fpos=fpos)


# ---- hairj.py ----
import numpy as np, struct, sys, pickle
HB=CU+'p_hairback_heartbeat.bin'
CA=np.array([0,165.1,3.25]); CJ=np.array([0,169.9,0.7]); SC=np.array([0.86,0.96,0.97])
def push_out(P,bpos,bnor,clear=0.5,iters=6):
    tree=cKDTree(bpos);P=P.copy();tot=0
    for _ in range(iters):
        dist,j=tree.query(P,k=4); n=bnor[j].mean(1); n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-9)
        p0=bpos[j].mean(1); sd=((P-p0)*n).sum(1); bad=(sd<clear)&(dist[:,0]<4.0)
        if not bad.any(): break
        P[bad]+=n[bad]*(clear-sd[bad])[:,None]; tot=bad.sum()
    return P,tot
def read_piece(path):
    b=open(path,'rb').read(); nv,ni,fl=struct.unpack('<3i',b[4:16])
    dt=np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)])
    r=np.frombuffer(b,dt,nv,16).copy(); idx=np.frombuffer(b,'<u2',ni,16+nv*44).astype(np.int64).reshape(-1,3)
    return r,idx
def build_hair(parts):
    r,idx=read_piece(HB); nh=17780
    keep=(idx<nh).all(1); idx=idx[keep]; r=r[:nh].copy()
    P=r['pos'].astype(float)
    t=smooth(120,155,P[:,1])[:,None]
    T=CJ+(P-CA)*SC
    P2=P*(1-t)+T*t
    skin=np.vstack([p['pos'] for p in parts if p['name'] in('body','face','scalp')])
    sn=np.vstack([p['nor'] for p in parts if p['name'] in('body','face','scalp')])
    P3,nb=push_out(P2,skin,sn)
    print('hair verts',nh,'tris',len(idx),'push_out',nb)
    r['pos']=P3
    return r,idx
def write_piece(path,r,idx,hide=None):
    with open(path,'wb') as f:
        f.write(b'CUP1'+struct.pack('<3i',len(r),idx.size,1 if hide is not None else 0)); f.write(r.tobytes()); f.write(idx.astype('<u2').tobytes())
        if hide is not None: f.write(struct.pack('<i',len(hide))); f.write(np.asarray(hide,'<u2').tobytes())

# ---- gen5.py ----
import numpy as np, struct, sys, os
def main(out):
    atlas,parts,info=build()
    Image.fromarray(np.clip(atlas+0.5,0,255).astype(np.uint8)).save(os.path.join(out,'julie.png'),optimize=True)
    # peca unica: corpo + rosto + couro cabeludo + olhos
    P=np.vstack([p['pos'] for p in parts]); N=np.vstack([p['nor'] for p in parts]); UV=np.vstack([p['uv'] for p in parts])
    BI=np.vstack([p['bi'] for p in parts]); BW=np.vstack([p['bw'] for p in parts])
    off=np.cumsum([0]+[len(p['pos']) for p in parts])[:-1]
    IDX=np.concatenate([(p['idx']+o).reshape(-1) for p,o in zip(parts,off)])
    n=len(P); assert n<65536
    r=np.zeros(n,np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)]))
    r['pos']=P; r['nor']=N; r['uv']=np.clip(UV,0,1); r['col']=255; r['bi']=BI; r['bw']=BW
    br,bidx=read_base(); nt=len(bidx); ymean=br['pos'][bidx][:,:,1].mean(1); keep=int(np.argmin(ymean))
    hide=np.array([t for t in range(nt) if t!=keep],'<u2')
    write_piece(os.path.join(out,'p_body_julie.bin'),r,IDX.reshape(-1,3),hide)
    hr,hidx=build_hair(parts); write_piece(os.path.join(out,'p_hairback_heartbeatjulie.bin'),hr,hidx)
    print('julie body',n,'verts',len(IDX)//3,'tris; hide',len(hide),'of',nt,'; keep tri',keep)


if __name__=='__main__': main(CUDIR)
