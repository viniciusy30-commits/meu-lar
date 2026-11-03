import numpy as np
from sk_paint import *
GREY=np.array([104,104,110]); GREY2=np.array([150,150,156])

def paint_tee2(F,B,art):
    H,W,_=F.shape; X,Y,Z=F[...,0],F[...,1],F[...,2]; nz=F[...,5]; bd=F[...,6]; bt=F[...,7]
    img=np.zeros((H,W,3),np.float32)+np.array([21,21,23],np.float32)
    g=noise((H,W),0.9,1)*2.0+noise((H,W),3.0,2)*1.5
    knit=0.5+0.5*np.sin(np.arange(W)[None,:]*1.7+noise((H,W),2,3)*0.7)
    img=img+g[...,None]+knit[...,None]*1.6
    th=np.arctan2(X,Z+1.5)
    img=img*(1+0.12*(np.sin(8*th+Y*0.11)*smooth(138,92,Y))[...,None])
    # desbotado (lavagem) nas costuras e ombros
    wash=(noise((H,W),5.0,4)*0.5+0.5)*(0.35*smooth(135,150,Y)+0.4*smooth(110,88,Y)+0.15)
    img=img+(wash*14)[...,None]
    # ESTAMPA na frente
    S=37.0; top=B.sh[1]-2.5; cx=0.8
    au=(X-(cx-S/2))/S; av=(top-Y)/S
    m=(nz>0.3)&(au>=0)&(au<1)&(av>=0)&(av<1)
    if m.any():
        ix=np.clip((au[m]*art.shape[1]).astype(int),0,art.shape[1]-1); iy=np.clip((av[m]*art.shape[0]).astype(int),0,art.shape[0]-1)
        a=art[iy,ix,3].astype(np.float32)/255.0
        crack=np.clip(noise((H,W),0.9,6)[m]*0.22+0.93,0,1)*np.clip(noise((H,W),6.0,7)[m]*0.15+0.95,0,1)
        al=a*crack
        col=np.stack([art[iy,ix,0],art[iy,ix,1],art[iy,ix,2]],1).astype(np.float32)*0.97
        img[m]=img[m]*(1-al[:,None])+col*al[:,None]
    # pequena marca nas costas (gola)
    tag=(nz<-0.3)&(np.abs(X)<2.2)&(Y>B.neck_y-8.5)&(Y<B.neck_y-4.4)
    img=blend(img,tag,np.array([205,205,200]),0.9)
    # gola
    neck=(bt==2)&(bd<2.6)
    rib=0.5+0.5*np.sin(np.arctan2(X,Z+1.5)*64)
    img=blend(img,neck,np.array([17,17,19])+rib[...,None]*6)
    u=np.arctan2(X,Z+1.5)*6.0
    img=stitch_line(img,np.abs(bd-2.6),u,0.12,np.array([64,64,70]),0.5,0.6,False)
    hemm=(bt==0)|(bt==1)
    uu=np.arctan2(X,Z+1.5)*8.0+Y*0.5
    for off in (1.4,1.85): img=stitch_line(img,np.abs(bd-off),uu,0.14,np.array([60,60,66]),0.6,0.62,False)
    img=img*(1-0.2*(hemm&(np.abs(bd-2.5)<0.13))[...,None])
    img=blend(img,hemm&(bd<0.35),np.array([30,30,34]),0.6)
    return np.clip(img,0,255).astype(np.uint8)

def paint_cargo(F,B,info):
    H,W,_=F.shape; X,Y,Z=F[...,0],F[...,1],F[...,2]; nx=F[...,3]; nz=F[...,5]; bd=F[...,6]; bt=F[...,7]
    wy=info['waist']; hem=info['hem']; ax=np.abs(X); sgn=np.sign(X); front=nz>0; back=nz<=0
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    twill=0.5+0.5*np.sin((xx+yy)*0.9)
    base=np.zeros((H,W,3),np.float32)+np.array([29,29,32],np.float32)
    base=base*(1+0.11*(twill[...,None]-0.5))+(noise((H,W),0.8,11)*1.4)[...,None]
    # lavado: cinza desbotado em coxas, joelhos e dobras
    n3=noise((H,W),8.0,13)*0.5+0.5; n4=noise((H,W),3.0,14)*0.5+0.5
    fade=0.16*n3+0.10*n4
    fade+=0.22*smooth(60,92,Y)*smooth(0.0,0.8,nz)
    fade+=0.26*np.exp(-((Y-B.kn[1])/6.5)**2)*smooth(-0.2,0.6,nz)
    fade+=0.16*np.exp(-((Y-(B.an[1]+8))/6.0)**2)
    fade+=0.22*smooth(wy-6,wy-26,Y)*np.exp(-((ax-5)/5.5)**2)*(front)
    fade+=0.25*smooth(7.0,0.0,bd)
    fade=np.clip(fade,0,0.55)
    img=base*(1-fade[...,None])+np.array([88,88,94],np.float32)*fade[...,None]
    # rugas horizontais (empilhado) e verticais baked como sombra
    wr=np.sin(Y*1.35+noise((H,W),6,15)*2.0)*smooth(46,16,Y)
    img=img*(1+0.14*wr[...,None])
    wr2=np.sin(np.arctan2(X-sgn*B.kn[0],Z)*6+Y*0.12)*smooth(98,60,Y)
    img=img*(1+0.07*wr2[...,None])
    # cós
    wb=(Y>wy-4.8)
    img=img*(1-0.1*wb[...,None])
    uang=np.arctan2(X,Z)*14.0
    for y0 in (wy-0.65,wy-4.1): img=stitch_line(img,np.abs(Y-y0),uang,0.13,GREY)
    for th in (0.62,-0.62,1.55,-1.55,2.55,-2.55):
        d=np.abs(np.arctan2(X,Z)-th)*14.5; m=(d<0.62)&(Y>wy-5.6)&(Y<wy+0.2)
        img=blend(img,m,img*0.78); e=(np.abs(d-0.62)<0.1)&(Y>wy-5.6)&(Y<wy+0.2); img=blend(img,e,GREY,0.85)
    bc=(Z>0)&((X**2+(Y-(wy-2.2))**2)<1.2**2); img=blend(img,bc,np.array([120,120,126])); img=blend(img,(Z>0)&((X**2+(Y-(wy-2.2))**2)<0.8**2),np.array([170,170,176])); img=blend(img,(Z>0)&((X**2+(Y-(wy-2.2))**2)<0.28**2),np.array([70,70,76]))
    fly=bez((-1.4,wy-4.8),(-1.5,wy-15),(-0.6,wy-17.8),30)
    d,u=poly_dist(X,Y,fly,front&(ax<4)&(Y<wy-4)&(Y>wy-19)); img=stitch_line(img,d,u,0.14,GREY,0.6,0.6)
    # bolsos frontais em diagonal
    for s in (-1,1):
        c=bez((s*6.3,wy-4.9),(s*7.0,wy-13.5),(s*15.2,wy-14.0),60)
        d,u=poly_dist(X,Y,c,front&(sgn==s)); img=stitch_line(img,d,u,0.15,GREY,0.6,0.62)
        m=front&(d<0.45)&(d>0.15); img=blend(img,m,img*0.7,0.45)
    # bolsos cargo laterais (volume na malha): aba + pregas + botão de pressão
    pz0,pz1,py0,py1=-6.8,7.8,64.5,88.0; flapy=79.5; zc=(pz0+pz1)/2
    for s in (-1,1):
        side=(sgn==s)&(nx*s>0.12)
        inr=side&(Z>pz0)&(Z<pz1)&(Y>py0)&(Y<py1)
        img=blend(img,inr,img*1.05)
        # contornos costurados
        for (pts) in ([(pz0,py0),(pz0,flapy)],[(pz1,py0),(pz1,flapy)],[(pz0,py0),(pz1,py0)]):
            d,u=poly_dist(Z,Y,pts,side&(Z>pz0-2)&(Z<pz1+2)&(Y>py0-2)&(Y<py1+2)); img=stitch_line(img,d,u,0.15,GREY,0.6,0.6)
        # aba (parte de cima) com borda dupla e ponta levemente arredondada
        flap=[(pz0-0.3,flapy+0.0),(pz0-0.3,py1),(pz1+0.3,py1),(pz1+0.3,flapy)]
        img=blend(img,side&(Z>pz0-0.3)&(Z<pz1+0.3)&(Y>flapy)&(Y<py1),img*0.88)
        d,u=poly_dist(Z,Y,[(pz0-0.3,flapy),(pz1+0.3,flapy)],side&(Z>pz0-3)&(Z<pz1+3)&(np.abs(Y-flapy)<2)); img=stitch_line(img,d,u,0.15,GREY,0.6,0.6)
        d2,u2=poly_dist(Z,Y,[(pz0-0.3,flapy+0.55),(pz1+0.3,flapy+0.55)],side&(Z>pz0-3)&(Z<pz1+3)&(np.abs(Y-flapy)<2)); img=stitch_line(img,d2,u2,0.12,GREY,0.6,0.6,False)
        img=blend(img,side&(np.abs(Y-flapy)<0.5)&(np.abs(Y-flapy)>0.18)&(Z>pz0)&(Z<pz1),img*0.6,0.5)
        # pregas laterais do fole
        for zz in (pz0+0.9,pz1-0.9):
            img=blend(img,side&(np.abs(Z-zz)<0.16)&(Y>py0)&(Y<flapy),img*0.62,0.7)
        # botão de pressão
        bm=side&(((Z-zc)**2+(Y-(flapy+0.2))**2)<0.62**2); img=blend(img,bm,np.array([128,128,134])); img=blend(img,side&(((Z-zc)**2+(Y-(flapy+0.2))**2)<0.36**2),np.array([176,176,182]))
    # bolsos de trás com aba
    for s in (-1,1):
        cx=s*6.6; top=wy-5.6
        for pts in ([(cx-5,top-4.6),(cx-5,top-15),(cx+5,top-15),(cx+5,top-4.6)],):
            d,u=poly_dist(X,Y,pts,back&(sgn==s)); img=stitch_line(img,d,u,0.15,GREY,0.62,0.62)
        d,u=poly_dist(X,Y,[(cx-5.3,top-4.6),(cx+5.3,top-4.6)],back&(sgn==s)); img=stitch_line(img,d,u,0.15,GREY,0.62,0.62)
        img=blend(img,back&(sgn==s)&(np.abs(X-cx)<5.3)&(Y<top)&(Y>top-4.6),img*0.9)
        bm=back&(sgn==s)&(((X-cx)**2+(Y-(top-4.0))**2)<0.6**2); img=blend(img,bm,np.array([128,128,134]))
    # costura lateral e interna
    outx={}; inx={}
    vm=(F[...,6]>0.4)&(Y>hem)&(Y<wy)
    vy=Y[vm]; vx=ax[vm]
    for yb in range(int(hem)-1,int(wy)+2):
        m=np.abs(vy-yb)<0.8
        if m.any(): outx[yb]=vx[m].max(); inx[yb]=vx[m].min()
    from scipy.ndimage import gaussian_filter1d
    ys=np.array(sorted(outx)); ox=np.interp(Y,ys,gaussian_filter1d(np.array([outx[k] for k in ys]),2.0)); ix_=np.interp(Y,ys,gaussian_filter1d(np.array([inx[k] for k in ys]),2.0))
    so=ox-ax
    outer=(nx*sgn>0.35)&(Y<wy-1); inner_s=(nx*sgn<-0.35)&(Y<wy-22)&(Y>hem+5)
    for off in (0.5,1.2): img=stitch_line(img,np.abs(so-off)+(~outer)*9,Y*1.6,0.14,GREY,0.6,0.62)
    img=stitch_line(img,np.abs(ax-ix_-0.6)+(~inner_s)*9,Y*1.6,0.14,GREY,0.6,0.62)
    # alça com fivela na lateral da perna (parte de baixo)
    for s in (-1,1):
        side=(sgn==s)&(nx*s>0.1)
        sz0=0.8; strap=side&(np.abs(Z-sz0)<1.0)&(Y>hem+3)&(Y<py0-0.5)
        img=blend(img,strap,np.array([18,18,20])); 
        for e in (-1.0,1.0): img=blend(img,side&(np.abs(Z-sz0-e*0.85)<0.1)&(Y>hem+3)&(Y<py0-0.5),GREY,0.8)
        bk=side&(np.abs(Z-sz0)<1.25)&(np.abs(Y-(hem+14))<1.4); img=blend(img,bk,np.array([150,150,156])); img=blend(img,side&(np.abs(Z-sz0)<0.7)&(np.abs(Y-(hem+14))<0.7),np.array([30,30,34]))
    # barra
    img=img*(1-0.2*((np.abs(bd-3.0)<0.2)&(bt==0))[...,None])
    uu=np.arctan2(X,Z)*10
    img=stitch_line(img,np.abs(bd-2.6),uu+Y,0.14,GREY,0.6,0.62)
    img=stitch_line(img,np.abs(bd-0.7),uu+Y,0.14,GREY,0.6,0.62)
    thr=noise((H,W),0.6,30)>0.25
    img=blend(img,(bt==0)&(bd<0.4)&thr,np.array([90,90,96]),0.7)
    return np.clip(img,0,255).astype(np.uint8)
