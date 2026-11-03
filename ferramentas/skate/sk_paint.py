import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
from sk_common import smooth
rng=np.random.default_rng(7)

def lerpc(a,b,t): return a+(b-a)*t[...,None]
def noise(shape,sigma,seed=0):
    r=np.random.default_rng(seed).standard_normal(shape).astype(np.float32)
    n=ndimage.gaussian_filter(r,sigma,mode='wrap'); n/=max(n.std(),1e-6); return n
def blend(img,mask,col,alpha=1.0):
    a=(mask.astype(np.float32)*alpha)[...,None]; col=np.asarray(col,np.float32)
    return img*(1-a)+col*a
def dashes(u,period=0.55,duty=0.62): return ((u/period)%1.0)<duty
def poly_dist(X,Y,pts,sel):
    """distância (no plano x,y) de cada pixel selecionado a uma polilinha densa."""
    pts=np.asarray(pts,float); dense=[]
    for i in range(len(pts)-1):
        n=max(2,int(np.linalg.norm(pts[i+1]-pts[i])/0.12)); t=np.linspace(0,1,n,endpoint=False)
        dense.append(pts[i]+(pts[i+1]-pts[i])*t[:,None])
    dense.append(pts[-1:]); dense=np.vstack(dense)
    tree=cKDTree(dense); d=np.full(X.shape,99.0,np.float32)
    ii=np.where(sel)
    q=np.stack([X[ii],Y[ii]],1); dd,ix=tree.query(q); d[ii]=dd
    # coordenada ao longo da linha
    u=np.zeros(X.shape,np.float32); cum=np.concatenate([[0],np.cumsum(np.linalg.norm(np.diff(dense,axis=0),axis=1))]); u[ii]=cum[ix]
    return d,u
def bez(p0,p1,p2,n=40):
    t=np.linspace(0,1,n)[:,None]; return (1-t)**2*np.array(p0)+2*(1-t)*t*np.array(p1)+t**2*np.array(p2)
THREAD=np.array([214,160,66]); THREAD2=np.array([232,214,160])

def stitch_line(img,d,u,w=0.17,col=THREAD,period=0.62,duty=0.6,shade=True):
    m=(d<w)&dashes(u,period,duty)
    out=blend(img,m,col)
    if shade:   # sombra do ponto
        s=((d>=w)&(d<w*2.4)&dashes(u,period,duty)); out=blend(out,s,out*0.75,0.5)
    return out

# ---------------------------------------------------------------- camiseta
def paint_tee(F,B,art):
    H,W,_=F.shape; X,Y,Z=F[...,0],F[...,1],F[...,2]; nz=F[...,5]; nx=F[...,3]; bd=F[...,6]; bt=F[...,7]
    base=np.array([24,24,27],np.float32)
    img=np.zeros((H,W,3),np.float32)+base
    g=noise((H,W),0.9,1)*2.2+noise((H,W),3.0,2)*1.6
    # malha da camisa (fios) - leve listra fina na vertical
    knit=0.5+0.5*np.sin(np.arange(W)[None,:]*1.9+noise((H,W),2,3)*0.6)
    img=img+g[...,None]+knit[...,None]*2.0
    # dobras e luz suave
    th=np.arctan2(X,Z+1.5)
    folds=np.sin(9*th+Y*0.13)*smooth(135,100,Y)
    img=img*(1+0.10*folds[...,None])
    # desbotado leve (lavada) na parte baixa e ombros
    fade=smooth(108,80,Y)*0.5+smooth(135,148,Y)*0.35
    img=img+((noise((H,W),4.0,4)*0.5+0.5)*fade*10)[...,None]
    # estampa grande nas costas
    top=B.sh[1]-2.0; hgt=40.0; wid=hgt*art.shape[1]/art.shape[0]
    back=(nz<-0.35)
    au=(X+wid/2)/wid; av=(top-Y)/hgt
    m=back&(au>=0)&(au<1)&(av>=0)&(av<1)
    if m.any():
        ix=np.clip((au[m]*art.shape[1]).astype(int),0,art.shape[1]-1); iy=np.clip((av[m]*art.shape[0]).astype(int),0,art.shape[0]-1)
        a=art[iy,ix]  # RGB cream sobre quase-preto
        lum=(a.astype(np.float32).mean(1)-26)/(215-26); lum=np.clip(lum,0,1)
        # estampa desgastada
        wear=np.clip(noise((H,W),1.2,5)[m]*0.35+0.85,0,1)
        al=lum*wear
        cream=np.array([222,210,160],np.float32)
        px=img[m]; img[m]=px*(1-al[:,None])+cream*al[:,None]
    # logo pequeno no peito (lado esquerdo do personagem = +x)
    lh=7.0; lw=lh*art.shape[1]/art.shape[0]; cx=9.5; cy=B.sh[1]-13.5
    front=(nz>0.35)
    au=(X-(cx-lw/2))/lw; av=(cy+lh/2-Y)/lh
    m=front&(au>=0)&(au<1)&(av>=0)&(av<1)
    if m.any():
        ix=np.clip((au[m]*art.shape[1]).astype(int),0,art.shape[1]-1); iy=np.clip((av[m]*art.shape[0]).astype(int),0,art.shape[0]-1)
        lum=np.clip((art[iy,ix].astype(np.float32).mean(1)-26)/(215-26),0,1)
        px=img[m]; img[m]=px*(1-lum[:,None])+np.array([222,210,160],np.float32)*lum[:,None]
    # gola canelada
    neck=(bt==2)&(bd<2.4)
    rib=0.5+0.5*np.sin(np.arctan2(X,Z+1.5)*60)
    img=blend(img,neck,np.array([19,19,21])+rib[...,None]*6)
    u=np.arctan2(X,Z+1.5)*6.0
    img=stitch_line(img,np.abs(bd-2.4),u,0.12,np.array([70,70,76]),0.5,0.6,False)
    img=blend(img,(bt==2)&(bd<0.4),np.array([36,36,40]),0.8)
    # barra e punhos: dobra + costura dupla
    hemm=(bt==0)|(bt==1)
    uu=np.arctan2(X,Z+1.5)*8.0+Y*0.5
    for off,wd in ((1.35,0.14),(1.75,0.14)):
        img=stitch_line(img,np.abs(bd-off),uu,wd,np.array([62,62,68]),0.6,0.62,False)
    crease=hemm&(np.abs(bd-2.3)<0.12)
    img=img*(1-0.18*crease[...,None])
    img=blend(img,hemm&(bd<0.35),np.array([30,30,34]),0.6)
    # costura do ombro e laterais (finas, tom sobre tom)
    sm=np.abs(np.abs(X)-np.where(Y>140,B.sh[0]*0.55,B.sh[0]*0.0+999))
    img=blend(img,(Y>128)&(Y<150)&(np.abs(np.abs(X)-B.sh[0]*0.95)<0.14),np.array([40,40,44]),0.7)
    # etiqueta interna branca nas costas da gola
    tag=(nz<-0.3)&(np.abs(X)<2.3)&(Y>B.neck_y-8.5)&(Y<B.neck_y-4.2)
    img=blend(img,tag,np.array([205,205,200]),0.9)
    return np.clip(img,0,255).astype(np.uint8)

# ---------------------------------------------------------------- bermuda jeans
def paint_shorts(F,B,info):
    H,W,_=F.shape; X,Y,Z=F[...,0],F[...,1],F[...,2]; nz=F[...,5]; bd=F[...,6]; bt=F[...,7]
    wy=info['waist']; hem=info['hem']; ax=np.abs(X); front=nz>0.0; back=nz<=0.0
    ky=B.kn[1]
    indigo=np.array([46,72,118],np.float32); light=np.array([112,146,186],np.float32)
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    twill=0.5+0.5*np.sin((xx+yy)*0.95); twill2=0.5+0.5*np.sin((xx-yy)*0.31)
    g=noise((H,W),0.8,11)*0.55+noise((H,W),2.2,12)*0.35
    base=np.zeros((H,W,3),np.float32)+indigo
    base=base*(1+0.10*(twill[...,None]-0.5)+0.05*(twill2[...,None]-0.5))
    base=base*(1+0.07*g[...,None])
    # desbotado
    n3=noise((H,W),9.0,13)*0.5+0.5; n4=noise((H,W),3.5,14)*0.5+0.5
    fade=0.20*n3+0.10*n4
    fade+=0.30*smooth(64,92,Y)*smooth(0.1,0.9,nz)*np.exp(-((ax-B.hip[0]-2)/9.0)**2)      # frente das coxas
    fade+=0.24*np.exp(-((Y-(ky+1.5))/5.0)**2)*np.exp(-((ax-B.kn[0])/7.0)**2)*smooth(0.0,0.7,nz)   # joelhos
    fade+=0.30*smooth(wy-8,wy-24,Y)*np.exp(-((ax-6.0)/5)**2)*front      # vinco da virilha
    fade+=0.30*smooth(8.0,0.0,bd)
    fade=np.clip(fade,0,0.78)
    img=base*(1-fade[...,None])+light*fade[...,None]
    # bigodes (whiskers) na frente do quadril
    for s in (-1,1):
        for k in range(9):
            a=0.12+0.07*k; y0=wy-5.5-k*0.9
            d=np.abs((Y-(y0-(ax-9)*a*0.9)))  # linha inclinada
            m=front&(np.sign(X)==s)&(ax>5)&(ax<17.5)&(d<0.16)&(smooth(0,1,noise((H,W),1.5,20+k)+0.2)>0.4)
            img=blend(img,m,light,0.30)
    # respingos de tinta (visual skatista)
    sel=np.where(((F[...,6]>0)&(Y<wy-8)&(Y>hem+6)).ravel())[0]
    cols=[np.array([236,236,230]),np.array([196,70,60]),np.array([240,200,70])]
    r=np.random.default_rng(5)
    for i in range(14):
        k=sel[r.integers(len(sel))]; c=F.reshape(-1,F.shape[2])[k,:3]; rad=r.uniform(0.18,0.6)
        d=np.sqrt(((F[...,:3]-c)**2).sum(-1)); img=blend(img,d<rad,cols[i%3],0.85)
    # cós
    wb=(Y>wy-4.6)
    img=blend(img,wb,img*0.9)
    uang=np.arctan2(X,Z)*14.0
    for y0 in (wy-0.65,wy-3.95):
        img=stitch_line(img,np.abs(Y-y0),uang,0.13,THREAD)
    # passadores
    for th in (0.62,-0.62,1.55,-1.55,2.55,-2.55):
        d=np.abs(np.arctan2(X,Z)-th)*14.5
        m=(d<0.6)&(Y>wy-5.4)&(Y<wy+0.2)
        img=blend(img,m,img*0.75)
        e=(np.abs(d-0.6)<0.1)&(Y>wy-5.4)&(Y<wy+0.2)
        img=blend(img,e,THREAD,0.9)
    # botão e braguilha
    bc=(Z>0)&(((X-0.0)**2+(Y-(wy-2.2))**2)<1.15**2)
    ring=(Z>0)&(((X)**2+(Y-(wy-2.2))**2)<0.85**2)
    img=blend(img,bc,np.array([120,118,112])); img=blend(img,ring,np.array([178,176,168])); img=blend(img,(Z>0)&(((X)**2+(Y-(wy-2.2))**2)<0.3**2),np.array([90,88,84]))
    fly=np.vstack([bez((-1.4,wy-4.6),(-1.5,wy-15),(-0.6,wy-17.6),30)]); 
    d,u=poly_dist(X,Y,fly,front&(ax<4)&(Y<wy-4)&(Y>wy-19))
    img=stitch_line(img,d,u,0.14,THREAD,0.6,0.6)
    d,u=poly_dist(X,Y,[(0.0,wy-4.6),(0.0,wy-15.5)],front&(ax<1.2)&(Y<wy-4)&(Y>wy-17))
    img=blend(img,(d<0.1)&(Y<wy-4.6),img*0.78)
    # bolsos frontais
    for s in (-1,1):
        c=bez((s*6.4,wy-4.7),(s*7.0,wy-13.5),(s*15.8,wy-13.8),60)
        d,u=poly_dist(X,Y,c,front&(np.sign(X)==s))
        img=stitch_line(img,d,u,0.15,THREAD,0.6,0.62)
        img=stitch_line(img,np.abs(d-0.55),u,0.14,THREAD,0.6,0.62) if False else img
        # rebite no canto
        for p in (c[0],c[-1]):
            m=front&(((X-p[0])**2+(Y-p[1])**2)<0.42**2); img=blend(img,m,np.array([166,104,58]))
            m=front&(((X-p[0])**2+(Y-p[1])**2)<0.2**2); img=blend(img,m,np.array([210,150,90]))
        # sombra da abertura
        m=front&(d<0.4)&(d>0.15); img=blend(img,m,img*0.72,0.4)
    # bolsos de trás
    for s in (-1,1):
        top=wy-5.4; cx=s*6.8
        poly=[(cx-5.6,top),(cx+5.6,top),(cx+5.6,top-8.8),(cx,top-12.4),(cx-5.6,top-8.8),(cx-5.6,top)]
        d,u=poly_dist(X,Y,poly,back&(np.sign(X)==s))
        img=stitch_line(img,d,u,0.15,THREAD,0.62,0.62)
        arc1=bez((cx-4.8,top-1.1),(cx-3.0,top-5.2),(cx,top-6.4),30); arc2=bez((cx+4.8,top-1.1),(cx+3.0,top-5.2),(cx,top-6.4),30)
        for arc in (arc1,arc2):
            d,u=poly_dist(X,Y,arc,back&(np.sign(X)==s)&(np.abs(X-cx)<6.5))
            img=stitch_line(img,d,u,0.14,np.array([226,190,110]),0.6,0.65)
        for p in ((cx-5.6,top),(cx+5.6,top)):
            m=back&(((X-p[0])**2+(Y-p[1])**2)<0.42**2); img=blend(img,m,np.array([166,104,58])); img=blend(img,back&(((X-p[0])**2+(Y-p[1])**2)<0.2**2),np.array([210,150,90]))
    # yoke
    for s in (-1,1):
        yk=[(s*0.2,wy-8.8),(s*15.5,wy-4.6)]
        d,u=poly_dist(X,Y,yk,back&(np.sign(X)==s)&(ax>0.1))
        img=stitch_line(img,d,u,0.14,THREAD,0.6,0.62)
    # etiqueta de couro atrás
    lp=back&(ax<2.9)&(Y<wy-0.6)&(Y>wy-4.2)
    img=blend(img,lp,np.array([128,88,54])); img=blend(img,back&(ax<2.9)&(Y<wy-0.6)&(Y>wy-4.2)&((np.abs(ax-2.45)<0.12)|(np.abs(Y-(wy-0.95))<0.12)|(np.abs(Y-(wy-3.85))<0.12)),np.array([84,56,34]))
    skate=back&(ax<1.7)&(np.abs(Y-(wy-2.4))<0.55)&(((ax/1.7)**2+((Y-(wy-2.4))/0.55)**2)<1)
    img=blend(img,skate,np.array([196,160,110]))
    # costura lateral (externa) e interna: duas linhas
    xo=np.zeros(H*W); 
    ybins=np.arange(int(hem)-2,int(wy)+3)
    outx={}; inx={}
    vy=F[...,1][F[...,6]>0.4]; vx=ax[F[...,6]>0.4]
    for yb in ybins:
        m=np.abs(vy-yb)<0.8
        if m.any(): outx[yb]=vx[m].max(); inx[yb]=vx[m].min()
    ys=np.array(sorted(outx)); ox=np.interp(Y,ys,[outx[k] for k in ys]); ix_=np.interp(Y,ys,[inx[k] for k in ys])
    so=ox-ax
    for off in (0.45,1.15):
        img=stitch_line(img,np.abs(so-off),Y*1.6,0.14,THREAD,0.6,0.62)
    si=(ax-ix_)*(Y<wy-20)
    img=stitch_line(img,np.abs(ax-ix_-0.55)+(Y>=wy-20)*9,Y*1.6,0.14,THREAD,0.6,0.62)
    # barra: dobra de 3.5 cm com duas costuras, borda desfiada
    hm=(bt==0)&(bd<3.9)
    img=img*(1-0.22*((np.abs(bd-3.7)<0.22)&(bt==0))[...,None])
    uu=np.arctan2(X,Z)*10+ (np.sign(X)*0)
    img=stitch_line(img,np.abs(bd-3.25),uu+Y,0.14,THREAD,0.6,0.62)
    img=stitch_line(img,np.abs(bd-0.65),uu+Y,0.14,THREAD,0.6,0.62)
    fr=(bt==0)&(bd<0.4)
    thr=(noise((H,W),0.6,30)>0.2)
    img=blend(img,fr&thr,np.array([150,172,200]),0.8)
    return np.clip(img,0,255).astype(np.uint8)
