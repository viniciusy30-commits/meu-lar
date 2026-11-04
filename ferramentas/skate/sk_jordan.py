import sys, numpy as np
sys.path.insert(0,'/home/claude/work/skate')
from PIL import Image
from scipy import ndimage
from sk_common import *
from sk_bake import unwrap, raster_attrs
from sk_paint import noise, blend, stitch_line, poly_dist

Q_EXP=3.4
PT=dict(UPPER=0,SOLE=1,TONGUE=2,LACE=3,RIM=4,INSOLE=5)

def st_funcs(W,z0,z1):
    def wF(s):
        s=np.asarray(s,float)
        sh=np.clip(s/0.07,0,1); cap=np.sqrt(np.clip(1-(1-sh)**2,0,1))
        body=W*np.interp(s,[0,0.12,0.30,0.50,0.70,0.78,1.0],[0.62,0.72,0.80,0.88,1.0,1.0,1.0])
        tt=np.clip((s-0.78)/0.22,0,1); toe=(1-tt**2.3)**(1/2.3)
        return np.maximum(body*cap*toe,0.0)
    def lift(s): return 1.15*smooth(0.80,1.0,np.asarray(s,float))**1.4
    return wF,lift

def build_shoe(B,side=1):
    m=(B.P0[:,1]<14)&(B.P0[:,0]>0); lo=B.P0[m].min(0); hi=B.P0[m].max(0)
    xc=(lo[0]+hi[0])/2; W=(hi[0]-lo[0])/2+1.25
    z0=lo[2]-1.5; z1=hi[2]+2.7; Lz=z1-z0
    wF,lift=st_funcs(W,z0,z1)
    SOLE=2.9
    N=56; t=np.linspace(0,1,N); S=(1-np.cos(np.pi*t))/2
    Z=z0+S*Lz; w=wF(S); ysb=lift(S); yst=ysb+SOLE
    # altura do cabedal (topo do arco) e abertura do tornozelo
    hAbs=np.interp(S,[0,0.06,0.10,0.2,0.3,0.4,0.46,0.55,0.65,0.75,0.85,0.92,1.0],[11.4,11.5,11.0,10.2,9.2,8.5,8.4,7.5,6.5,5.5,4.7,4.0,3.4])
    tt2=np.clip((S-0.90)/0.10,0,1); toecap=(1-tt2**2.3)**(1/2.3)
    ha_closed=np.maximum(hAbs-yst,0.25)*toecap
    sa,sb=0.085,0.455
    gap=smooth(sa,sa+0.03,S)*(1-smooth(sb-0.11,sb,S))
    yc=np.interp(S,[0.08,0.2,0.3,0.4,0.46],[11.0,10.3,9.3,8.4,8.0])
    ha_open=(yc-yst)/0.80
    ha=ha_closed*(1-gap)+ha_open*gap
    th_a=np.arcsin(0.80**(Q_EXP/2))
    thL=np.pi/2+(th_a-np.pi/2)*gap
    KL=9
    P=[];A=[];idx={}
    def sec(i,th):
        c=np.cos(th); sn=np.sin(th)
        x=w[i]*np.sign(c)*np.abs(c)**(2/Q_EXP)
        y=yst[i]+ha[i]*np.abs(sn)**(2/Q_EXP)
        return x,y
    L=np.zeros((N,KL),int); R=np.zeros((N,KL),int)
    for i in range(N):
        for k in range(KL):
            th=thL[i]*k/(KL-1); x,y=sec(i,th); L[i,k]=len(P); P.append((xc+x,y,Z[i])); A.append((PT['UPPER'],S[i],x))
        for k in range(KL):
            th=(np.pi-thL[i])+thL[i]*k/(KL-1); x,y=sec(i,th); R[i,k]=len(P); P.append((xc+x,y,Z[i])); A.append((PT['UPPER'],S[i],x))
    T=[]
    for i in range(N-1):
        for arr in (L,R):
            for k in range(KL-1):
                a,b,c,d=arr[i,k],arr[i,k+1],arr[i+1,k],arr[i+1,k+1]
                T+=[(a,b,c),(b,d,c)]
        gi=gap[i]>1e-4; gj=gap[i+1]>1e-4
        if gi and not gj: T.append((L[i,-1],R[i,0],L[i+1,-1]))
        if gj and not gi: T.append((L[i+1,-1],R[i+1,0],L[i,-1]))
        if gi and gj:   # abertura nas duas estações: nada no meio (borda aberta)
            pass
    # --- cadarços (degraus) no peito do pé
    rungs=[]
    for sj in np.linspace(0.485,0.625,5):
        i=int(np.argmin(abs(S-sj)))
        pts=[];nm=[]
        for th in np.linspace(0.42,np.pi-0.42,13):
            x,y=sec(i,th); cx=np.cos(th); sy=np.sin(th)
            nx=np.sign(cx)*abs(cx)**(2/Q_EXP-1)*0.0+cx; ny=sy
            nn=np.array([cx*0.9,sy,0.0]); nn/=np.linalg.norm(nn)+1e-9
            pts.append(np.array([xc+x,y,Z[i]])+nn*0.34)
        rungs.append(np.array(pts))
    for r in rungs:
        base=len(P)
        for p in r:
            P.append(tuple(p+np.array([0,0,0.32]))); A.append((PT['LACE'],0,0)); P.append(tuple(p-np.array([0,0,0.32]))); A.append((PT['LACE'],0,0))
        for k in range(len(r)-1):
            a=base+2*k; T+=[(a,a+1,a+2),(a+1,a+3,a+2)]
    # --- língua
    i0=int(np.argmin(abs(S-0.50))); i1=int(np.argmin(abs(S-0.36)))
    tb=[];KT=9
    for u in np.linspace(0,1,8):
        zt=Z[i0]+(Z[i1]-Z[i0])*u*1.02
        yb=yst[i0]+ha[i0]*0.93+(11.9-(yst[i0]+ha[i0]*0.93))*smooth(0,1,u)*1.0
        wd=w[i0]*(0.56+0.34*u)
        row=[]
        for v in np.linspace(-1,1,KT):
            row.append((xc+v*wd, yb+0.6*(1-v*v)*0.5-0.0*u, zt+0.55*(1-v*v)*(1-0.4*u)))
        tb.append(row)
    base=len(P)
    for row in tb:
        for p in row: P.append(p); A.append((PT['TONGUE'],0,0))
    for r in range(len(tb)-1):
        for k in range(KT-1):
            a=base+r*KT+k; T+=[(a,a+1,a+KT),(a+1,a+KT+1,a+KT)]
    # --- beirada interna da abertura (espessura)
    rimL=[L[i,-1] for i in range(N) if gap[i]>1e-4]; rimR=[R[i,0] for i in range(N) if gap[i]>1e-4]
    loop=rimL+rimR[::-1]
    inner=[]
    for v in loop:
        p=np.array(P[v]); dx=xc-p[0]; dz=(Z[int(np.argmin(abs(Z-p[2])))]-p[2])*0
        q=p+np.array([np.sign(dx)*0.6,-0.35,0.0])
        inner.append(len(P)); P.append(tuple(q)); A.append((PT['RIM'],0,0))
    for k in range(len(loop)-1):
        a,b=loop[k],loop[k+1]; c,d=inner[k],inner[k+1]; T+=[(a,b,c),(b,d,c)]
    # --- palmilha (fundo da abertura)
    # --- sola: 3 anéis ao redor do contorno + fundo plano
    outl=[]
    for i in range(N): outl.append((i,+1))
    for i in range(N-2,0,-1): outl.append((i,-1))
    npts=len(outl)
    def ring(off,yfun):
        ids=[]
        for (i,sg) in outl:
            ww=w[i]; px=xc+sg*ww; pz=Z[i]
            # normal 2D do contorno (aprox): derivada
            j0=max(i-1,0); j1=min(i+1,N-1)
            dwx=(w[j1]-w[j0]); dz=(Z[j1]-Z[j0])
            tx,tz=sg*dwx,dz; nn=np.hypot(tx,tz)+1e-9
            nxv,nzv=tz/nn,-tx/nn
            if sg*nxv<0 and abs(ww)>0.3: nxv,nzv=-nxv,-nzv
            if ww<0.3:   # pontas (calcanhar/bico): normal ao longo do eixo z
                nxv,nzv=0.0,(-1.0 if i<N//2 else 1.0)
            ids.append(len(P)); P.append((px+nxv*off,yfun(i),pz+nzv*off)); A.append((PT['SOLE'],S[i],sg*ww))
        return ids
    rA=ring(-0.45,lambda i:ysb[i]); rB=ring(0.62,lambda i:ysb[i]+1.15); rC=ring(0.34,lambda i:yst[i]-0.05)
    for ra,rb in ((rA,rB),(rB,rC)):
        for k in range(npts):
            k2=(k+1)%npts; T+=[(ra[k],rb[k],ra[k2]),(ra[k2],rb[k],rb[k2])]
    # fundo
    ctr=len(P); P.append((xc,float(np.mean(ysb)),float(np.mean(Z)))); A.append((PT['SOLE'],0.5,0))
    for k in range(npts):
        k2=(k+1)%npts; T.append((rA[k],ctr,rA[k2]))
    # anel superior da sola até a base do cabedal (patamar): liga rC à linha base do cabedal
    base_ids={}
    for (i,sg) in outl:
        base_ids[(i,sg)]=(L[i,0] if sg>0 else R[i,-1])
    for k in range(npts):
        k2=(k+1)%npts; a,b=base_ids[outl[k]],base_ids[outl[k2]]
        T+=[(rC[k],a,rC[k2]),(rC[k2],a,b)]
    P=np.array(P,float); A=np.array(A,float); T=np.array(T,int)
    # espelho para o pé esquerdo
    return P,A,T,dict(xc=xc,W=W,z0=z0,z1=z1,SOLE=SOLE)

def both(B):
    P,A,T,info=build_shoe(B)
    n=len(P); PL=P.copy(); PL[:,0]=-PL[:,0]
    AL=A.copy(); AL[:,2]=A[:,2]    # lx: positivo = lado de fora (para ambos os pés)
    TL=T[:,[0,2,1]]+n
    PP=np.vstack([P,PL]); AA=np.vstack([A,AL]); TT=np.vstack([T,TL])
    return PP,AA,TT,info

def paint_jordan(F,info):
    H,W,_=F.shape
    X,Y,Z=F[...,0],F[...,1],F[...,2]; nx,ny,nz=F[...,3],F[...,4],F[...,5]
    part=np.rint(F[...,6]).astype(int); S=F[...,7]; lx=F[...,8]
    z0,z1=info['z0'],info['z1']; Lz=z1-z0
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    WHITE=np.array([240,240,236],np.float32); BLACK=np.array([24,24,27],np.float32); GREY=np.array([205,205,200],np.float32)
    grain=noise((H,W),0.8,31)
    img=np.zeros((H,W,3),np.float32)+WHITE
    img=img*(1+0.018*grain[...,None])
    crease=noise((H,W),4.0,32)*0.5+0.5
    img=img*(1-0.05*(crease[...,None]-0.5))
    yst=2.9
    up=(part==0)
    black=np.zeros((H,W),bool)
    # bico preto
    capb=0.735
    black|=up&(S>capb)
    # colarinho (faixa na borda da abertura) e contraforte do calcanhar
    yrim=np.interp(S,[0.08,0.2,0.3,0.4,0.46,0.55],[11.0,10.3,9.3,8.4,8.0,0.0])
    black|=up&(S<0.47)&(Y>yrim-1.25)
    heel_edge=0.07+0.075*smooth(3.4,10.0,Y)
    black|=up&(S<heel_edge)
    # painel lateral (faixa curva) preto
    pts=np.array([(z0+0.215*Lz,yst+1.4),(z0+0.30*Lz,yst+0.95),(z0+0.42*Lz,yst+1.7),(z0+0.53*Lz,yst+3.3),(z0+0.62*Lz,yst+4.6)])
    side=up&(np.abs(nx)>0.35)&(S<0.70)
    d,u=poly_dist(Z,Y,pts,side)
    tot=np.linalg.norm(pts[-1]-pts[0]); uu=np.clip(u/ (tot*1.05),0,1)
    thick=1.55*(1-uu)**0.8+0.35
    black|=side&(d<thick)
    img=blend(img,black,BLACK)
    # costuras brancas nas bordas dos pretos
    d_cap=np.abs(S-capb)*Lz
    img=stitch_line(img,d_cap+(~up)*9,Y*1.2+X*0.7,0.12,GREY,0.55,0.6)
    d_rim=np.abs(Y-(yrim-1.25))
    img=stitch_line(img,d_rim+((~up)|(S>0.47)|(S<0.08))*9,Z*1.2,0.11,GREY,0.55,0.6)
    # perfurações do bico
    px=(X*1.8); pz=(Z*1.8)
    cell=((np.abs(((px+0.5*np.floor(pz))%1.0)-0.5)**2+np.abs((pz%1.0)-0.5)**2)<0.07)
    perf=up&(S>0.80)&(S<0.94)&(ny>0.35)&(np.abs(lx)<4.4)
    img=blend(img,perf&cell,np.array([70,70,76]))
    # sombra de oclusão perto da sola
    ao=smooth(yst+2.2,yst,Y)*up
    img=img*(1-0.18*ao[...,None])
    # sola
    so=(part==1)
    mid=np.array([244,244,240],np.float32)
    img=blend(img,so,mid)
    bottom=so&(ny<-0.55)
    tread=np.array([58,58,62],np.float32)+np.array([10,10,10],np.float32)*(0.5+0.5*np.sin(Z*2.6)*np.sin(X*2.6))[...,None]
    img=np.where(bottom[...,None],tread,img)
    sidew=so&(ny>=-0.55)
    # linha de costura da sola e friso cinza
    img=blend(img,sidew&(np.abs(Y-1.75)<0.07),np.array([200,200,200]))
    d_st=np.abs(Y-2.15)
    img=stitch_line(img,d_st+(~sidew)*9,Z*1.0+X*1.0,0.075,np.array([150,150,150]),0.5,0.55,False)
    img=blend(img,sidew&(Y<0.35),np.array([225,225,222]))
    img=img*(1-0.10*(sidew&(ny<0.2)&(Y>0.2)&(Y<1.0))[...,None])
    # língua: branca com faixa preta no topo
    tg=(part==2)
    img=blend(img,tg,np.array([242,242,238]))
    img=blend(img,tg&(Y>11.3),BLACK)
    # cadarço
    img=blend(img,part==3,np.array([30,30,32]))
    img=blend(img,part==4,BLACK)
    img=np.clip(img,0,255)
    return img.astype(np.uint8)

def bake_nolip(P,N,T,A):
    Pn,Nn,An,UV,Tn=unwrap(P,N,T,A)
    feat=np.hstack([Pn,Nn,An]).astype(np.float32)
    F,mask=raster_attrs(UV,Tn,feat)
    return Pn,Nn,An,UV,Tn,F

def do_jordan(B,g,OUT):
    P,A,T,info=build_shoe(B)
    N=vnormals(P,T)
    cen=np.stack([np.full(len(P),info['xc']),np.full(len(P),5.0),P[:,2]],1)
    fl=((P-cen)*N).sum(1)<0; N[fl]=-N[fl]
    Pn,Nn,An,UV,Tn,F=bake_nolip(P,N,T,A)
    Image.fromarray(paint_jordan(F,info)).save(OUT+'%s_shoes.png'%g,optimize=True)
    # pé esquerdo = espelho (mesmas UV, mesma textura)
    n=len(Pn); PL=Pn.copy(); PL[:,0]*=-1; NL=Nn.copy(); NL[:,0]*=-1
    PP=np.vstack([Pn,PL]); NN=np.vstack([Nn,NL]); UU=np.vstack([UV,UV]); TT=np.vstack([Tn,Tn[:,[0,2,1]]+n])
    bi,bw=transfer_weights(B,PP); write_cup(OUT+'%s_shoes.cup'%g,PP,NN,UU,TT,bi,bw)
    return len(PP)
if __name__=='__main__':
    import os
    g=sys.argv[1]; OUT='/home/claude/work/skate/out2/'
    B=load_body(g); print(do_jordan(B,g,OUT))
