import numpy as np
from scipy.spatial import cKDTree
from sk_common import *

def trace_loop(edges):
    adj={}
    for a,b in edges:
        adj.setdefault(a,[]).append(b); adj.setdefault(b,[]).append(a)
    start=edges[0][0]; loop=[start]; prev=None; cur=start
    while True:
        nxt=[x for x in adj[cur] if x!=prev]
        if not nxt: break
        n=nxt[0]
        if n==start or n in loop: break
        loop.append(n); prev,cur=cur,n
    return [int(v) for v in loop]

def _sel_tris(B,M1):
    return B.idx[M1[B.idx].all(1)]

def _compact(P,N,tri,*attrs):
    u,inv=np.unique(tri.ravel(),return_inverse=True)
    return (P[u],N[u],inv.reshape(-1,3))+tuple(a[u] for a in attrs)

# ---------------------------------------------------------------- camiseta longa
DEF_TEE=dict(hem=24.0,off_t=[4.6,3.8,2.4,1.5,1.0],s0=2.0,s1=3.2,sp=1.6,sl=0.88,fl=3.6,curve=3.8)
def build_tee(B,st=None):
    st=dict(DEF_TEE,**(st or {}))
    P=B.P; N=B.N; nv=len(P)
    def cut_neck(z,x=None):
        r=np.hypot(0 if x is None else x,z+2.0) if x is not None else np.abs(z+2.0)
        return (B.neck_y-4.6)-3.0*smooth(1.0,9.0,z)+6.0*smooth(6.5,13.0,r)
    yc=B.hip[1]-6.5                       # corte do tronco (acima da virilha)
    HEM=B.hip[1]-st['hem']                     # barra da camiseta (meio da coxa)
    sh=B.sh.copy(); el=B.el.copy()
    # eixo do braço (lado +x); espelha para -x
    def arm_t(p):
        s=np.sign(p[:,0]+1e-9); S=np.stack([sh[0]*s,np.full(len(p),sh[1]),np.full(len(p),sh[2])],1)
        E=np.stack([el[0]*s,np.full(len(p),el[1]),np.full(len(p),el[2])],1)
        u=E-S; L1=np.linalg.norm(u,axis=1); u=u/L1[:,None]
        return ((p-S)*u).sum(1),L1,u
    t1,L1,u1=arm_t(P)
    SL=st['sl']*L1                             # comprimento da manga (até quase o cotovelo)
    zc=P[:,2]
    torso0=(B.armw<0.5)&(P[:,1]>=yc)&(P[:,1]<=cut_neck(zc,P[:,0]))
    torso1=(B.armw<0.5)&(P[:,1]>=yc)&(P[:,1]<=cut_neck(zc,P[:,0])+2.5)&(P[:,1]<B.neck_y+3)
    sl0=(B.armw>=0.2)&(t1<=SL)&(t1>-3.0)&(P[:,1]>100)
    sl1=(B.armw>=0.2)&(t1<=SL+2.5)&(t1>-3.0)&(P[:,1]>100)
    M0=torso0|sl0; M1=torso1|sl1
    tri=_sel_tris(B,M1)
    Q=P.copy(); n=N.copy()
    # grampos
    low=np.zeros(nv,bool)
    cn=cut_neck(zc,P[:,0]); top=(Q[:,1]>cn)&(B.armw<0.5); Q[top,1]=cn[top]
    over=(B.armw>=0.2)&(t1>SL)&sl1
    Q[over]-=u1[over]*(t1[over]-SL[over])[:,None]
    # deslocamento (folga) pela normal
    y=Q[:,1]
    off_t=np.interp(y,[yc,110,125,140,155],st['off_t'])
    tt=np.clip(t1/np.maximum(SL,1),0,1)
    off_s=st['s0']+st['s1']*tt**st['sp']
    wS=smooth(0.20,0.60,B.armw)
    off=off_t*(1-wS)+off_s*wS
    Q=Q+n*off[:,None]
    # dobras na parte baixa do tronco
    ang=np.arctan2(Q[:,0],Q[:,2])
    fold=0.55*np.sin(9*ang+Q[:,1]*0.13)*smooth(135,105,Q[:,1])*(1-wS)
    Q=Q+np.stack([Q[:,0]*0,0*Q[:,0],0*Q[:,0]],1)
    r=np.stack([Q[:,0],np.zeros(nv),Q[:,2]-(-1.5)],1); rn=np.linalg.norm(r,axis=1,keepdims=True); rn[rn<1e-6]=1
    Q=Q+(r/rn)*fold[:,None]
    keep=np.zeros(nv,bool); keep[np.unique(tri)]=True
    fixed=np.zeros(nv,bool)
    Q=laplace(Q,tri,fixed|~keep,it=2,lam=0.45)
    # ---- barra longa: anéis paramétricos descendo de y0 (raio medido nos vértices do tronco, por ângulo)
    bev=[e for e in boundary_edges(tri) if Q[e[0],1]<yc+9 and Q[e[1],1]<yc+9 and B.armw[e[0]]<0.35 and B.armw[e[1]]<0.35]
    yb=np.array([Q[v,1] for e in bev for v in e])
    y0=float(np.percentile(yb,85))-2.4
    sel=np.where(keep&(B.armw<0.35)&(Q[:,1]>y0-0.8)&(Q[:,1]<y0+4.5))[0]
    c=np.array([np.mean(Q[sel,0]),0,np.mean(Q[sel,2])])
    NA=96
    ang=np.arctan2(Q[sel,0]-c[0],Q[sel,2]-c[2]); rad=np.hypot(Q[sel,0]-c[0],Q[sel,2]-c[2])
    bins=((ang+np.pi)/(2*np.pi)*NA).astype(int)%NA
    R=np.full(NA,np.nan)
    for k in range(NA):
        m=bins==k
        if m.any(): R[k]=rad[m].max()
    ok=~np.isnan(R); xs=np.arange(NA)
    R=np.interp(xs,np.concatenate([xs[ok]-NA,xs[ok],xs[ok]+NA]),np.concatenate([R[ok]]*3))
    R=np.convolve(np.concatenate([R[-3:],R,R[:3]]),np.ones(7)/7,mode='valid')[:NA] if False else R
    th=(xs+0.5)/NA*2*np.pi-np.pi
    P_all=[Q]; N_all=[n]; tri_all=[tri]; base=nv
    RF=[np.zeros(nv)]; RY=[np.zeros(nv)]
    K=9; rings=[]
    for j in range(0,K+1):
        f=j/K; ids=[]
        for k in range(NA):
            d=np.array([np.sin(th[k]),0,np.cos(th[k])])
            front=abs(d[2]); hem=HEM-st['curve']*front**2.2
            yv=y0+(hem-y0)*f
            flare=st['fl']*f**1.05+0.8*np.sin(f*np.pi)+0.6
            rr=R[k]+flare+0.35*np.sin(11*th[k]+f*2)*f
            p=c+d*rr; p[1]=yv
            P_all.append(p[None]); N_all.append(d[None]); ids.append(base); base+=1
            RF.append(np.array([0.5*f])); RY.append(np.array([y0]))
        rings.append(ids)
    T=[]
    for j in range(K):
        a_=rings[j]; b_=rings[j+1]
        for k in range(NA):
            k2=(k+1)%NA
            T+=[(a_[k],b_[k],a_[k2]),(a_[k2],b_[k],b_[k2])]
    tri_all.append(np.array(T,np.int64))
    PP=np.vstack(P_all); NN=np.vstack(N_all); TT=np.vstack(tri_all)
    NN=vnormals(PP,TT)
    # normais de fora para dentro: confere pelo centro do tronco
    cen=np.array([0,0,-1.5]); chk=((PP[:,[0,2]]-cen[[0,2]])*NN[:,[0,2]]).sum(1)
    if np.mean(chk[chk!=0]>0)<0.5: NN=-NN
    return PP,NN,TT,dict(yc=yc,HEM=HEM,ringf=np.concatenate(RF),ry0=np.concatenate(RY))


# ---------------------------------------------------------------- bermuda jeans baggy
def build_shorts(B):
    P=B.P; N=B.N; nv=len(P)
    waist=B.hip[1]+5.0
    hem=B.kn[1]-5.0
    band=(B.armw<0.3)&(np.abs(P[:,0])<26)
    M0=band&(P[:,1]>=hem)&(P[:,1]<=waist)
    M1=band&(P[:,1]>=hem-2.5)&(P[:,1]<=waist+2.5)
    tri=_sel_tris(B,M1)
    Q=P.copy(); n=N.copy()
    Q[(Q[:,1]<hem)&M1,1]=hem
    Q[(Q[:,1]>waist)&M1,1]=waist
    y=Q[:,1]
    off=np.interp(y,[hem,60,80,90,100,waist],[5.4,4.5,3.5,2.5,1.7,1.1])
    # empurra para fora do eixo da perna (calça larga) em vez de só pela normal
    Q=Q+n*off[:,None]
    ang=np.arctan2(Q[:,0],Q[:,2])
    ax=np.where(Q[:,0]>=0,1,-1)*B.hip[0]
    r=np.stack([Q[:,0]-ax,np.zeros(nv),Q[:,2]],1); rn=np.linalg.norm(r,axis=1,keepdims=True); rn[rn<1e-6]=1
    fold=0.55*np.sin(7*np.arctan2(r[:,0],r[:,2])+Q[:,1]*0.21)*smooth(95,60,Q[:,1])
    Q=Q+(r/rn)*fold[:,None]
    keep=np.zeros(nv,bool); keep[np.unique(tri)]=True
    Q=laplace(Q,tri,~keep,it=2,lam=0.4)
    NN=vnormals(Q,tri)
    cen=np.array([0,0,0.0]); chk=((Q[:,[0,2]]-np.array([np.where(Q[:,0]>=0,1,-1)*B.hip[0],0*Q[:,0]]).T)*NN[:,[0,2]]).sum(1)
    if np.mean(chk[keep]>0)<0.5: NN=-NN
    return Q,NN,tri,dict(waist=waist,hem=hem)


def subdivide(P,N,tri,extra):
    """1 -> 4 triângulos (pontos médios); 'extra' = lista de arrays por vértice (interpolados)."""
    mid={}; Pn=[P]; Nn=[N]; Ex=[[e] for e in extra]; n=len(P); T=[]
    def m(a,b):
        nonlocal n
        k=(a,b) if a<b else (b,a)
        if k not in mid:
            mid[k]=n; n+=1
            Pn.append(((P[a]+P[b])/2)[None]); nn=(N[a]+N[b]); nn=nn/max(np.linalg.norm(nn),1e-9); Nn.append(nn[None])
            for i,e in enumerate(extra): Ex[i].append(np.atleast_1d((e[a]+e[b])/2))
        return mid[k]
    for a,b,c in tri:
        ab,bc,ca=m(a,b),m(b,c),m(c,a)
        T+=[(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]
    return np.vstack(Pn),np.vstack(Nn),np.array(T,np.int64),[np.concatenate(e) for e in Ex]

# ---------------------------------------------------------------- calça cargo baggy
def build_cargo(B):
    waist=B.hip[1]+4.5
    hem=B.an[1]+3.0
    footw=np.array([sum(w for b,w in zip(B.BI[i],B.BW[i]) if b in (19,20,23,24)) for i in range(len(B.P))])
    P0=B.P; N0=B.N
    band=(B.armw<0.3)&(footw<0.55)&(np.abs(P0[:,0])<26)
    M1=band&(P0[:,1]>=hem-3.0)&(P0[:,1]<=waist+3.0)
    tri0=_sel_tris(B,M1)
    P,N,tri,(bandf,legf)=subdivide(P0,N0,tri0,[band.astype(float),np.sign(P0[:,0])*(np.abs(P0[:,0])>0.8)])
    nv=len(P); ymid=P[:,1]
    keep=np.zeros(nv,bool); keep[np.unique(tri)]=True
    Q=P.copy(); n=N.copy()
    Q[(Q[:,1]<hem)&keep,1]=hem
    Q[(Q[:,1]>waist)&keep,1]=waist
    y=Q[:,1]
    off=np.interp(y,[hem,45,60,80,90,100,waist],[5.2,5.6,5.4,4.8,3.6,2.2,1.2])
    Q=Q+n*off[:,None]
    # volume extra nas pernas (calça larga): afasta do eixo da perna
    sgn=np.where(Q[:,0]>=0,1.0,-1.0)
    axis_x=sgn*B.kn[0]
    r=np.stack([Q[:,0]-axis_x,np.zeros(nv),Q[:,2]-B.kn[2]],1); rn=np.linalg.norm(r,axis=1,keepdims=True); rn[rn<1e-6]=1
    extra=0.5*smooth(98,70,Q[:,1])
    Q=Q+(r/rn)*extra[:,None]
    # pernas retas e largas (cargo baggy): raio mínimo constante em volta do eixo da perna
    ay=np.interp(Q[:,1],[B.an[1],B.kn[1],B.hip[1]],[B.an[0],B.kn[0],B.hip[0]]); az=np.interp(Q[:,1],[B.an[1],B.kn[1],B.hip[1]],[B.an[2],B.kn[2],B.hip[2]])
    axx=sgn*ay
    rv=np.stack([Q[:,0]-axx,np.zeros(nv),Q[:,2]-az],1); rl=np.linalg.norm(rv,axis=1); rl[rl<1e-6]=1e-6
    Rt=np.interp(Q[:,1],[14,45,70,92,100],[10.4,11.0,11.8,12.6,11.8])
    wR=smooth(100,92,Q[:,1])*keep
    newr=rl+(np.maximum(rl,Rt)-rl)*wR
    Q=Q+(rv/rl[:,None])*(newr-rl)[:,None]
    Q[:,0]=sgn*np.maximum(np.abs(Q[:,0]),1.3)*keep+Q[:,0]*(~keep)
    r=np.stack([Q[:,0]-axis_x,np.zeros(nv),Q[:,2]-B.kn[2]],1); rn=np.linalg.norm(r,axis=1,keepdims=True); rn[rn<1e-6]=1
    # dobras: ondas verticais + empilhado perto do tornozelo
    th=np.arctan2(r[:,0],r[:,2])
    fold=0.9*np.sin(6*th+Q[:,1]*0.12)*smooth(100,70,Q[:,1])+0.8*np.sin(Q[:,1]*1.35)*smooth(40,14,Q[:,1])
    Q=Q+(r/rn)*fold[:,None]
    # bolsos cargo: volume nas coxas, lado de fora
    for s in (-1,1):
        side=(Q[:,0]*s>0)
        px=smooth(-8.5,-3.0,(Q[:,2]-0.5))*smooth(8.5,3.0,(Q[:,2]-0.5))   # largura em z
        py=smooth(61,66,Q[:,1])*smooth(92,86,Q[:,1])
        outer=smooth(0.0,1.0,(np.abs(Q[:,0])-(np.abs(axis_x)+2.0))/6.0)
        bump=3.4*px*py*outer*side
        dirx=np.stack([np.full(nv,s),np.zeros(nv),np.zeros(nv)],1)
        Q=Q+dirx*bump[:,None]*0.9+(r/rn)*bump[:,None]*0.3
    Q=laplace(Q,tri,~keep,it=2,lam=0.35)
    # tubo extra descendo até perto do chão (barra empilhada sobre o tênis)
    NA=48; P_all=[Q]; N_all=[n]; tri_all=[tri]; base=nv; LEG=[np.sign(legf)]
    for s in (-1,1):
        legv=np.where(keep&(np.sign(Q[:,0])==s)&(Q[:,1]<40))[0]
        y0=float(np.percentile(Q[legv,1],4))+0.8
        sel=np.where(keep&(np.sign(Q[:,0])==s)&(Q[:,1]>y0-1.0)&(Q[:,1]<y0+4.0))[0]
        c=np.array([np.mean(Q[sel,0]),0,np.mean(Q[sel,2])])
        ang=np.arctan2(Q[sel,0]-c[0],Q[sel,2]-c[2]); rad=np.hypot(Q[sel,0]-c[0],Q[sel,2]-c[2])
        bins=((ang+np.pi)/(2*np.pi)*NA).astype(int)%NA
        R=np.full(NA,np.nan)
        for k in range(NA):
            m=bins==k
            if m.any(): R[k]=rad[m].max()
        ok=~np.isnan(R); xs=np.arange(NA)
        R=np.interp(xs,np.concatenate([xs[ok]-NA,xs[ok],xs[ok]+NA]),np.concatenate([R[ok]]*3))
        th2=(xs+0.5)/NA*2*np.pi-np.pi
        K=5; rings=[]
        for j in range(K+1):
            f=j/K; ids=[]
            for k in range(NA):
                d=np.array([np.sin(th2[k]),0,np.cos(th2[k])])
                yv=y0+(9.0-y0)*f
                rr=R[k]+0.7+1.6*f+0.5*np.sin(9*th2[k]+f*3)*f+0.45*np.sin(f*9)*f
                p=c+d*rr; p[1]=yv
                P_all.append(p[None]); N_all.append(d[None]); ids.append(base); base+=1; LEG.append(np.array([float(s)]))
            rings.append(ids)
        T=[]
        for j in range(K):
            a_=rings[j]; b_=rings[j+1]
            for k in range(NA):
                k2=(k+1)%NA; T+=[(a_[k],b_[k],a_[k2]),(a_[k2],b_[k],b_[k2])]
        tri_all.append(np.array(T,np.int64))
    PP=np.vstack(P_all); TT=np.vstack(tri_all); NN=vnormals(PP,TT)
    ax2=np.where(PP[:,0]>=0,1,-1)*B.kn[0]
    chk=((PP[:,[0]]-ax2[:,None])*NN[:,[0]]).sum(1)
    if np.mean(chk[np.abs(PP[:,1]-60)<15]>0)<0.5: NN=-NN
    return PP,NN,TT,dict(waist=waist,hem=hem,low=9.0,leg=np.concatenate(LEG))
