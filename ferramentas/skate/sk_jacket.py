import sys, numpy as np
sys.path.insert(0,'/home/claude/work/skate')
from PIL import Image
from sk_common import *
from sk_garments import _sel_tris, subdivide
from sk_bake import unwrap, raster_attrs
from sk_paint import noise, blend, stitch_line, poly_dist, bez

def build_jacket(B):
    P=B.P; N=B.N; nv=len(P)
    ncx,ncz=0.0,-1.5
    def cut_neck(z,x):
        r=np.hypot(x,z-ncz)
        return (B.neck_y-3.2)-2.0*smooth(1.0,9.0,z)+6.0*smooth(5.2,10.5,r)
    yc=B.hip[1]-0.5                       # corte do tronco (cintura)
    HEM=B.hip[1]-5.4                      # fim da barra (cós)
    sh=B.sh.copy(); ha=B.ha.copy()
    # eixo do braço: ombro -> mão (braço reto em A)
    def arm_t(p):
        s=np.sign(p[:,0]+1e-9)
        S=np.stack([sh[0]*s,np.full(len(p),sh[1]),np.full(len(p),sh[2])],1)
        Hh=np.stack([ha[0]*s,np.full(len(p),ha[1]),np.full(len(p),ha[2])],1)
        u=Hh-S; L=np.linalg.norm(u,axis=1); u=u/L[:,None]
        t=((p-S)*u).sum(1); perp=np.linalg.norm((p-S)-t[:,None]*u,axis=1)
        return t,L,u,perp
    t1,L1,u1,perp=arm_t(P)
    SL=0.915*L1                          # manga até o punho
    zc=P[:,2]
    torso0=(B.armw<0.5)&(P[:,1]>=yc)&(P[:,1]<=cut_neck(zc,P[:,0]))
    torso1=(B.armw<0.5)&(P[:,1]>=yc)&(P[:,1]<=cut_neck(zc,P[:,0])+2.5)&(P[:,1]<B.neck_y+3)
    sl0=(B.armw>=0.2)&(t1<=SL)&(t1>-3.0)&(perp<11.0)
    sl1=(B.armw>=0.2)&(t1<=SL+2.5)&(t1>-3.0)&(perp<11.0)
    M1=torso1|sl1
    tri=_sel_tris(B,M1)
    P,N,tri,(armw,)=subdivide(P,N,tri,[B.armw]); nv=len(P)
    t1,L1,u1,perp=arm_t(P); SL=0.915*L1; zc=P[:,2]
    sl1=(armw>=0.2)&(t1<=SL+2.5)&(t1>-3.0)&(perp<11.0)
    Q=P.copy(); n=N.copy()
    cn=cut_neck(zc,P[:,0]); top=(Q[:,1]>cn)&(armw<0.5); Q[top,1]=cn[top]
    over=(armw>=0.2)&(t1>SL)&sl1
    Q[over]-=u1[over]*(t1[over]-SL[over])[:,None]
    y=Q[:,1]
    off_t=np.interp(y,[yc,110,125,140,155],[8.6,8.0,7.0,4.9,2.7])
    off_s=np.interp(t1,[-3,0,14,30,44,SL.max()],[5.4,5.2,4.5,4.0,3.6,3.1])
    wS=smooth(0.20,0.60,armw)
    off=off_t*(1-wS)+off_s*wS
    Q=Q+n*off[:,None]
    ang=np.arctan2(Q[:,0],Q[:,2]-ncz)
    fold=0.5*np.sin(9*ang+Q[:,1]*0.13)*smooth(135,105,Q[:,1])*(1-wS)
    r=np.stack([Q[:,0],np.zeros(nv),Q[:,2]-ncz],1); rn=np.linalg.norm(r,axis=1,keepdims=True); rn[rn<1e-6]=1
    Q=Q+(r/rn)*fold[:,None]
    keep=np.zeros(nv,bool); keep[np.unique(tri)]=True
    Q=laplace(Q,tri,~keep,it=2,lam=0.45)
    be_all=boundary_edges(tri)
    # ---- cós (barra) a partir do laço de baixo do tronco, vértices compartilhados
    be=[e for e in be_all if Q[e[0],1]<yc+9 and Q[e[1],1]<yc+9 and armw[e[0]]<0.35 and armw[e[1]]<0.35]
    # ---- gola: laço do pescoço
    bn=[e for e in be_all if Q[e[0],1]>B.neck_y-9 and Q[e[1],1]>B.neck_y-9 and armw[e[0]]<0.35 and armw[e[1]]<0.35]
    def order(edges):
        adj={}
        for a_,b_ in edges: adj.setdefault(a_,[]).append(b_); adj.setdefault(b_,[]).append(a_)
        start=edges[0][0]; ring=[start]; prev=-1; cur=start
        while True:
            nx=[x for x in adj[cur] if x!=prev]
            if not nx or nx[0]==start: break
            prev,cur=cur,nx[0]; ring.append(cur)
            if len(ring)>len(adj)+2: break
        return [int(v) for v in ring]
    ring=order(be); nring=order(bn)
    P_all=[Q]; N_all=[n]; tri_all=[tri]; base=nv
    c=np.array([np.mean(Q[ring,0]),0,np.mean(Q[ring,2])])
    rings=[ring]; K=3
    for j in range(1,K+1):
        f=j/K; ids=[]
        for v in ring:
            p0=Q[v]; d=np.array([p0[0]-c[0],0,p0[2]-c[2]]); dl=max(np.linalg.norm(d),1e-6); d=d/dl
            p=p0.copy(); p[1]=yc+(HEM-yc)*f if False else p0[1]+(HEM-p0[1])*f
            p=p-d*(0.9*np.sin(np.pi*f)*0.6)+d*0.3*f      # cós levemente franzido
            P_all.append(p[None]); N_all.append(d[None]); ids.append(base); base+=1
        rings.append(ids)
    T=[]
    nr=len(ring)
    for j in range(K):
        a_=rings[j]; b_=rings[j+1]
        for k in range(nr):
            k2=(k+1)%nr; T+=[(a_[k],b_[k],a_[k2]),(a_[k2],b_[k],b_[k2])]
    tri_all.append(np.array(T,np.int64))
    # gola virada: 3 anéis acima do pescoço (menor na frente)
    cn_=np.array([np.mean(Q[nring,0]),0,np.mean(Q[nring,2])])
    crings=[nring]; Tc=[]
    spec=[(2.2,-0.3),(3.5,0.6),(2.8,2.5)]
    for j,(dy,dr) in enumerate(spec):
        ids=[]
        for v in nring:
            p0=Q[v]; d=np.array([p0[0]-cn_[0],0,p0[2]-cn_[2]]); dl=max(np.linalg.norm(d),1e-6); d=d/dl
            th=abs(np.arctan2(d[0],d[2]))
            g=0.55+0.45*smooth(0.0,0.9,th)
            p=p0.copy(); p[1]=p0[1]+dy*g; p=p+d*dr
            P_all.append(p[None]); N_all.append(d[None]); ids.append(base); base+=1
        crings.append(ids)
    nn_=len(nring)
    for j in range(len(spec)):
        a_=crings[j]; b_=crings[j+1]
        for k in range(nn_):
            k2=(k+1)%nn_; Tc+=[(a_[k],b_[k],a_[k2]),(a_[k2],b_[k],b_[k2])]
    tri_all.append(np.array(Tc,np.int64))
    PP=np.vstack(P_all); NN=np.vstack(N_all); TT=np.vstack(tri_all)
    NN=vnormals(PP,TT)
    cen=np.array([0,0,ncz]); chk=((PP[:,[0,2]]-cen[[0,2]])*NN[:,[0,2]]).sum(1)
    if np.mean(chk[chk!=0]>0)<0.5: NN=-NN
    return PP,NN,TT,dict(yc=yc,HEM=HEM,neck=B.neck_y,sh=B.sh)

GREYT=np.array([178,178,172],np.float32)
def paint_jacket(F,B,info):
    H,W,_=F.shape; X,Y,Z=F[...,0],F[...,1],F[...,2]; nx=F[...,3]; ny=F[...,4]; nz=F[...,5]; bd=F[...,6]; bt=F[...,7]
    ax=np.abs(X); sgn=np.sign(X); front=nz>0.1; back=nz<-0.1
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    HEM=info['HEM']; yc=info['yc']; neck=info['neck']
    twill=0.5+0.5*np.sin((xx*0.8+yy*0.8)*1.1)
    base=np.zeros((H,W,3),np.float32)+np.array([25,26,30],np.float32)
    base=base*(1+0.10*(twill[...,None]-0.5))+(noise((H,W),0.8,41)*1.5)[...,None]
    n3=noise((H,W),9.0,42)*0.5+0.5; n4=noise((H,W),3.2,43)*0.5+0.5
    fade=0.10*n3+0.07*n4
    # braço: eixo ombro-mão
    shx,shy,shz=B.sh; hax,hay,haz=B.ha
    ux=hax-shx; uy=hay-shy; uz=haz-shz; L=np.sqrt(ux*ux+uy*uy+uz*uz); ux,uy,uz=ux/L,uy/L,uz/L
    rx=ax-shx; ry=Y-shy; rz=Z-shz
    t=rx*ux+ry*uy+rz*uz
    px=rx-t*ux; py=ry-t*uy; pz=rz-t*uz
    perp=np.sqrt(px*px+py*py+pz*pz)
    # ângulo em volta do eixo (0 = frente)
    v0=np.array([0,0,1.0]); w0=np.cross(np.array([ux,uy,uz]),v0); w0/=np.linalg.norm(w0)
    pv=px*v0[0]+py*v0[1]+pz*v0[2]; pw=px*w0[0]+py*w0[1]+pz*w0[2]
    ang=np.arctan2(pw,pv)
    SL=0.915*L
    sleeve=(ax>shx+1.5)&(t>0)&(perp<9.5)&(Y<shy+3)
    torso=~sleeve
    fade+=0.20*smooth(1.4,0.0,np.abs(bd))                      # bordas gastas
    fade+=0.14*smooth(146,152,Y)*smooth(-8,8,Y-146)*(1-sleeve)   # ombros
    fade+=0.12*np.exp(-((Y-122)/12.0)**2)*np.exp(-((ax-8)/9.0)**2)*front
    fade+=0.16*np.exp(-((t-(0.52*L))/5.0)**2)*sleeve              # cotovelo
    fade+=0.13*np.exp(-((Y-(HEM+6))/4.0)**2)*torso
    fade+=0.12*np.exp(-((ax-13)/3.0)**2)*np.exp(-((Y-110)/8.0)**2)  # "bigodes" no quadril
    fade=np.clip(fade,0,0.55)
    img=base*(1-fade[...,None])+np.array([92,94,103],np.float32)*fade[...,None]
    # dobras baked (sombra)
    wr=np.sin(Y*1.1+noise((H,W),5,44)*2.0)*smooth(135,95,Y)
    img=img*(1+0.07*wr[...,None])
    # ---- frente: placket, botões, pences, bolsos
    pk=front&(ax<1.7)&(Y<neck-2.5)&(Y>HEM)
    img=img*(1+0.05*pk[...,None])
    for xs in (1.75,2.45):
        d,u=poly_dist(X,Y,[(xs,neck-3.6),(xs,HEM+1.0)],front&(ax<xs+0.7)&(sgn>0)); img=stitch_line(img,d,u,0.085,GREYT,0.5,0.6)
        d,u=poly_dist(X,Y,[(-xs,neck-3.6),(-xs,HEM+1.0)],front&(ax<xs+0.7)&(sgn<0)); img=stitch_line(img,d,u,0.085,GREYT,0.5,0.6)
    for yb in [neck-6.2-8.0*k for k in range(7)]:
        r2=(X**2+(Y-yb)**2)
        img=blend(img,front&(r2<0.95**2),np.array([70,70,78])); img=blend(img,front&(r2<0.82**2),np.array([128,128,136]))
        img=blend(img,front&(r2<0.44**2),np.array([168,168,176])); img=blend(img,front&(r2<0.16**2),np.array([60,60,66]))
    # pences verticais (2 linhas paralelas) de cada lado do placket
    for s in (-1,1):
        for dx in (5.0,5.55):
            d,u=poly_dist(X,Y,[(s*dx,neck-8.5),(s*dx,HEM+3.0)],front&(sgn==s)&(np.abs(ax-dx)<1.0)); img=stitch_line(img,d,u,0.085,GREYT,0.5,0.6)
    # bolsos do peito com aba (pontuda) e botão
    for s in (-1,1):
        x0,x1=6.8,14.6; yt,yb2,yp=143.2,137.6,136.6
        outline=[(s*x0,yb2-5.6),(s*x0,yt),(s*x1,yt),(s*x1,yb2-5.6)]
        d,u=poly_dist(X,Y,outline,front&(sgn==s)&(ax>x0-1)&(ax<x1+1)&(Y>yb2-7)&(Y<yt+1)); img=stitch_line(img,d,u,0.10,GREYT,0.5,0.6)
        d,u=poly_dist(X,Y,[(s*x0,yt),(s*x0,yb2),(s*(x0+x1)/2,yp),(s*x1,yb2),(s*x1,yt)],front&(sgn==s)&(ax>x0-1)&(ax<x1+1)&(Y>yp-1)&(Y<yt+1)); img=stitch_line(img,d,u,0.10,GREYT,0.5,0.55)
        flap=front&(sgn==s)&(ax>x0)&(ax<x1)&(Y>yb2)&(Y<yt); img=img*(1-0.07*flap[...,None])
        bx=s*(x0+x1)/2; r2=((X-bx)**2+(Y-(yb2+0.5))**2)
        img=blend(img,front&(r2<0.8**2),np.array([70,70,78])); img=blend(img,front&(r2<0.68**2),np.array([128,128,136])); img=blend(img,front&(r2<0.36**2),np.array([168,168,176]))
    # ---- costas: carcela, pences, centro
    yk=148.4
    for dy in (0.0,0.5):
        for s in (-1,1):
            d,u=poly_dist(X,Y,[(s*0.0,yk+0.4-dy),(s*8.5,yk-1.4-dy),(s*16.0,yk-0.6-dy)],back&(sgn==s)); img=stitch_line(img,d,u,0.085,GREYT,0.5,0.6)
    for s in (-1,1):
        for dx in (6.4,6.95):
            d,u=poly_dist(X,Y,[(s*dx,yk-1.0),(s*dx,HEM+3.0)],back&(sgn==s)&(np.abs(ax-dx)<1.0)); img=stitch_line(img,d,u,0.085,GREYT,0.5,0.6)
    d,u=poly_dist(X,Y,[(0,yk+0.4),(0,HEM+3.0)],back&(ax<1.0)); img=stitch_line(img,d,u,0.085,GREYT,0.5,0.6)
    # ---- barra (cós) e abas laterais
    for yb3 in (yc-0.4,HEM+1.2):
        d=np.abs(Y-yb3); uang=np.arctan2(X,Z)*10.0
        img=stitch_line(img,d+(~torso)*9,uang,0.085,GREYT,0.5,0.6)
    band=torso&(Y<yc-0.4)&(Y>HEM)
    img=img*(1-0.10*band[...,None])
    for s in (-1,1):
        tab=(sgn==s)&(np.abs(Z-0.0)<2.2)&(np.abs(ax-13.8)<2.4)&(Y>HEM+0.5)&(Y<yc+1.0)
        side=tab&(nx*s>0.2)
        d,u=poly_dist(Z,Y,[(-2.2,HEM+0.8),(-2.2,yc+0.8),(2.2,yc+0.8),(2.2,HEM+0.8)],side); img=stitch_line(img,d,u,0.09,GREYT,0.5,0.6)
        bm=side&((Z**2+(Y-(yc-1.8))**2)<0.7**2); img=blend(img,bm,np.array([110,110,118]))
    # ---- mangas: costuras ao longo, punho com botão e fenda
    for a0 in (0.55,-0.55,np.pi-0.5,-(np.pi-0.5)):
        dd=np.abs(ang-a0)*np.maximum(perp,1.0)
        img=stitch_line(img,dd+(~(sleeve&(t>2)&(t<SL-6.5)))*9,t*1.0,0.085,GREYT,0.5,0.6)
    cuffR=sleeve&(t>SL-6.2)
    img=img*(1-0.07*cuffR[...,None])
    for tt_ in (SL-6.2,SL-5.6,SL-0.9):
        img=stitch_line(img,np.abs(t-tt_)+(~sleeve)*9,ang*perp,0.085,GREYT,0.5,0.6)
    for a1 in (-1.1,1.1):
        pos=np.abs(ang-a1)*np.maximum(perp,1.0)
        bm=sleeve&(np.abs(t-(SL-3.2))<0.8)&(pos<0.8)
        img=blend(img,bm,np.array([110,110,118]))
    # ---- gola (bordas costuradas)
    col=(Y>neck-3.2)&(bt==2)
    for dd in (0.55,1.0):
        img=stitch_line(img,np.abs(bd-dd)+(~(Y>neck-3.5))*9,np.arctan2(X,Z)*8.0,0.08,GREYT,0.5,0.6)
    img=img*(1-0.08*(Y>neck-0.8)[...,None])
    # barra gasta e punho gasto
    return np.clip(img,0,255).astype(np.uint8)

def do_jacket(B,g,OUT):
    from sk_bake import prepare
    P,N,tri,info=build_jacket(B)
    sx=B.sh[0]+10
    bt=lambda p: 2 if p[1]>B.neck_y-4.0 else (1 if abs(p[0])>sx else 0)
    P1,N1,T1,A1=prepare(P,N,tri,bt,(np.zeros(len(P)),np.zeros(len(P)),np.zeros(len(P))))
    Pn,Nn,An,UV,Tn=unwrap(P1,N1,T1,A1)
    feat=np.hstack([Pn,Nn,An]).astype(np.float32)
    F,mask=raster_attrs(UV,Tn,feat)
    Image.fromarray(paint_jacket(F,B,info)).save(OUT+'%s_jacket.png'%g,optimize=True)
    bi,bw=transfer_weights2(B,Pn,An); write_cup(OUT+'%s_jacket.cup'%g,Pn,Nn,UV,Tn,bi,bw)
    return len(Pn)
if __name__=='__main__':
    g=sys.argv[1]; B=load_body(g); print(do_jacket(B,g,'/home/claude/work/skate/out2/'))
