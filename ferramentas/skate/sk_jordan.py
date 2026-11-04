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
    hAbs=np.interp(S,[0,0.06,0.10,0.2,0.3,0.4,0.46,0.55,0.65,0.75,0.85,0.92,1.0],[10.6,10.7,10.4,9.8,9.0,8.4,8.2,7.4,6.5,5.6,4.8,4.1,3.5])
    tt2=np.clip((S-0.90)/0.10,0,1); toecap=(1-tt2**2.3)**(1/2.3)
    ha_closed=np.maximum(hAbs-yst,0.25)*toecap
    sa,sb=0.085,0.455
    gap=smooth(sa,sa+0.03,S)*(1-smooth(sb-0.11,sb,S))
    yc=np.interp(S,[0.08,0.2,0.3,0.4,0.46],[10.3,9.8,9.0,8.3,8.0])
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
        yb=yst[i0]+ha[i0]*0.93+(10.2-(yst[i0]+ha[i0]*0.93))*smooth(0,1,u)*1.0
        wd=w[i0]*(0.60-0.12*u**2)
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
    WHITE=np.array([238,238,234],np.float32); BLACK=np.array([22,22,25],np.float32)
    img=np.zeros((H,W,3),np.float32)+WHITE
    img=img*(1+0.02*noise((H,W),0.8,31)[...,None])
    up=(part==0); Wd=info['W']; side=np.abs(lx)/max(Wd,1e-6)
    blk=np.zeros((H,W),bool)
    capE=0.795+0.03*smooth(0.3,1.0,side)          # biqueira preta (borda curva)
    blk|=up&(S>capE)
    blk|=up&(S>0.42)&(S<0.705)&(np.abs(lx)<2.9)   # ilhoses / painel dos cadarços
    yrim=np.interp(S,[0.0,0.08,0.2,0.3,0.4,0.46],[10.6,10.6,9.8,9.0,8.3,8.0])
    blk|=up&(S<0.46)&(Y>yrim-1.5)                 # gola
    blk|=up&(S<0.13+0.07*smooth(3.0,9.0,Y))       # contraforte do calcanhar
    # faixa lateral (arco genérico) do calcanhar até o peito do pé
    z0,z1=info['z0'],info['z1']; Lz=z1-z0; yst=2.9
    pts=np.array([(z0+0.22*Lz,yst+1.1),(z0+0.34*Lz,yst+1.0),(z0+0.47*Lz,yst+2.2),(z0+0.60*Lz,yst+4.0)])
    sd=up&(side>0.55)&(S>0.19)&(S<0.66)
    d,u=poly_dist(Z,Y,pts,sd)
    tot=np.linalg.norm(np.diff(pts,axis=0),axis=1).sum(); uu=np.clip(u/tot,0,1)
    blk|=sd&(d<(0.2+0.8*(1-uu)**1.3))
    img=blend(img,blk,BLACK)
    GRY=np.array([150,150,150],np.float32)
    img=stitch_line(img,np.abs(S-capE)*Lz+(~up)*9,X*2+Y*2,0.07,GRY,0.45,0.6,False)
    img=stitch_line(img,np.abs(Y-(yrim-1.5))+((~up)|(S>0.46))*9,Z*2,0.07,GRY,0.45,0.6,False)
    # sombra junto da sola
    img=img*(1-0.15*(up*smooth(yst+1.8,yst,Y))[...,None])
    so=(part==1)
    img=blend(img,so,np.array([244,244,240]))
    img=blend(img,so&(ny<-0.55),np.array([30,30,33]))
    img=blend(img,so&(ny>=-0.55)&(Y<0.45),np.array([40,40,44]))
    img=blend(img,so&(ny>=-0.55)&(np.abs(Y-2.0)<0.06),np.array([170,170,170]))
    tg=(part==2)
    img=blend(img,tg,np.array([240,240,236])); img=blend(img,tg&(Y>9.4),BLACK)
    img=blend(img,part==3,np.array([235,235,232]))   # cadarços brancos
    img=blend(img,part==4,BLACK)
    return np.clip(img,0,255).astype(np.uint8)

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
    # cada peça com seu próprio atlas (projeção planar sobreposta estragava a textura)
    tpart=np.rint(A[T][:,0,0]).astype(int)
    groups=[[0],[1],[2],[3],[4]]
    slots=[(0,0,2,2),(0,2,2,2),(0,4,1,1),(1,4,1,1),(0,5,1,1)]   # (col,row,w,h) em unidades de 768x512
    GW,GH=2,6
    big=np.zeros((GH*512,GW*768,3),np.uint8)
    Ps=[];Ns=[];Us=[];Ts=[];base=0
    for gi,(grp,(cx,cy,w,h)) in enumerate(zip(groups,slots)):
        sel=np.isin(tpart,grp)
        if not sel.any(): continue
        Tg=T[sel]; u,inv=np.unique(Tg.ravel(),return_inverse=True); Tg=inv.reshape(-1,3)
        Pn,Nn,An,UV,Tn,F=bake_nolip(P[u],N[u],Tg,A[u])
        tex=paint_jordan(F,info)
        tim=Image.fromarray(tex).resize((w*768,h*512),Image.LANCZOS)
        big[cy*512:(cy+h)*512,cx*768:(cx+w)*768]=np.array(tim)
        UV2=np.stack([(cx+UV[:,0]*w)/GW,(cy+UV[:,1]*h)/GH],1)
        Ps.append(Pn);Ns.append(Nn);Us.append(UV2);Ts.append(Tn+base);base+=len(Pn)
    Pn=np.vstack(Ps);Nn=np.vstack(Ns);UV=np.vstack(Us);Tn=np.vstack(Ts)
    Image.fromarray(big).resize((2048,2048),Image.LANCZOS).save(OUT+'%s_shoes.png'%g,optimize=True)
    n=len(Pn); PL=Pn.copy(); PL[:,0]*=-1; NL=Nn.copy(); NL[:,0]*=-1
    PP=np.vstack([Pn,PL]); NN=np.vstack([Nn,NL]); UU=np.vstack([UV,UV]); TT=np.vstack([Tn,Tn[:,[0,2,1]]+n])
    bi,bw=transfer_weights(B,PP); write_cup(OUT+'%s_shoes.cup'%g,PP,NN,UU,TT,bi,bw)
    return len(PP)
if __name__=='__main__':
    import os
    g=sys.argv[1]; OUT='/home/claude/work/skate/out2/'
    B=load_body(g); print(do_jordan(B,g,OUT))
