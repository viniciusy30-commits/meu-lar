import sys, numpy as np
sys.path.insert(0,'/home/claude/work/skate')
from PIL import Image
from scipy import ndimage
from sk_common import *; from sk_garments import subdivide

NA=96; Y0=138.0; NY=56   # tabela de raio da cabeça: y de 138 a 194, 1 cm

def profile(B):
    P=B.P; m=(P[:,1]>Y0)&(P[:,1]<Y0+NY)
    hv=P[(P[:,1]>162)]; zc=(hv[:,2].min()+hv[:,2].max())/2
    p=P[m]; th=np.arctan2(p[:,0],p[:,2]-zc); r=np.hypot(p[:,0],p[:,2]-zc)
    iy=((p[:,1]-Y0)).astype(int); ia=(((th+np.pi)/(2*np.pi))*NA).astype(int)%NA
    R=np.zeros((NY,NA))
    for a,b,v in zip(iy,ia,r): R[a,b]=max(R[a,b],v)
    # preenche vazios (interpola circularmente / verticalmente)
    for j in range(NY):
        row=R[j]; ok=row>0
        if ok.sum()>=3:
            xs=np.arange(NA); R[j]=np.interp(xs,np.concatenate([xs[ok]-NA,xs[ok],xs[ok]+NA]),np.concatenate([row[ok]]*3))
        else: R[j]=0
    for j in range(NY):
        if R[j].max()==0: R[j]=R[j-1] if j>0 else R[j]
    R=ndimage.gaussian_filter(R,(0.8,1.2),mode=('nearest','wrap'))
    R=np.minimum(R,np.interp(Y0+np.arange(NY),[150,160,166],[11.2,11.9,13.2])[:,None])
    # envoltória: o cabelo cai reto a partir da parte mais larga acima (janela de 7 cm)
    E=R.copy()
    for j in range(NY):
        E[j]=R[j:min(NY,j+8)].max(0)
    E=ndimage.gaussian_filter(E,(1.0,2.0),mode=('nearest','wrap'))
    return R,E,zc

class HP:
    def __init__(s,B):
        s.R,s.E,s.zc=profile(B)
    def _look(s,T,y,th):
        fy=np.clip(y-Y0,0,NY-1.001); j=int(fy); t=fy-j
        fa=((th+np.pi)/(2*np.pi))*NA; a=int(np.floor(fa))%NA; u=fa-np.floor(fa); a2=(a+1)%NA
        v0=T[j,a]*(1-u)+T[j,a2]*u; v1=T[j+1,a]*(1-u)+T[j+1,a2]*u
        return v0*(1-t)+v1*t
    def surf(s,y,th,thick):
        return max(s._look(s.E,y,th),s._look(s.R,y,th)+0.9)+thick
    def pos(s,y,th,rr):
        return np.array([rr*np.sin(th),y,s.zc+rr*np.cos(th)])

def hairline(az,B):
    a=np.abs(az); top=B.head_y+19.7
    xs=[0.0,0.5,0.9,1.3,1.7,2.1,2.6,3.14]
    ys=[top-5.0,top-5.4,top-8.0,top-12.0,top-15.5,top-19.0,top-23.5,top-25.0]
    return np.interp(a,xs,ys)

def tipline(a):
    a=np.abs(a)
    return np.interp(a,[0.7,1.2,1.7,2.3,2.9,3.14],[168.5,164.5,162.0,159.0,156.0,155.0])

def card(hp,th0,y0,ytip,dth,width,thick,flick,sway,ph,rng,nseg=10):
    rows=[]
    for k in range(nseg):
        s=k/(nseg-1)
        y=y0+(ytip-y0)*s
        th=th0+dth*s**1.35+sway*np.sin(2*np.pi*(1.3*s+ph))*s*0.06
        cols=[]
        for e in (-1,0,1):
            R0=hp.surf(y,th,thick)
            wth=e*(width*(1-0.25*s)/2)/R0
            tt=th+wth
            rr=hp.surf(y,tt,thick)+flick*s**2.6+0.35*(1-abs(e))*np.sin(np.pi*min(1,s*1.2))
            cols.append(hp.pos(y,tt,rr))
        rows.append(cols)
    rows=np.array(rows)   # nseg,3,3
    ns=nseg
    P=rows.reshape(-1,3)
    UV=np.array([(e/2,k/(ns-1)) for k in range(ns) for e in (0,1,2)],float)
    T=[]
    for k in range(ns-1):
        for e in range(2):
            a=k*3+e; b=a+1; c=a+3; d=c+1
            T+=[(a,b,c),(b,d,c)]
    return P,UV,np.array(T)

def cap(B,hp):
    P=B.P; N=B.N
    hv=(P[:,1]>B.neck_y-1.5)
    tri0=B.idx[hv[B.idx].all(1)]
    P1,N1,tri,_=subdivide(P,N,tri0,[np.zeros(len(P))])
    P1,N1,tri,_=subdivide(P1,N1,tri,[np.zeros(len(P1))])
    zc=hp.zc
    cen=P1[tri].mean(1); caz=np.arctan2(cen[:,0],cen[:,2]-zc); chl=hairline(caz,B)
    tri=tri[(cen[:,1]>chl)&(cen[:,1]>B.neck_y+2)]
    u,inv=np.unique(tri.ravel(),return_inverse=True); Pc=P1[u].copy(); Nc=N1[u].copy(); tri=inv.reshape(-1,3)
    azc=np.arctan2(Pc[:,0],Pc[:,2]-zc); hlc=hairline(azc,B); yy=Pc[:,1]
    top=B.head_y+19.7
    taper=smooth(0.0,3.0,yy-hlc)
    th=1.1+1.5*smooth(top-10,top,yy)+0.5*smooth(0.3,0.95,np.cos(azc))*smooth(top-8,top-1,yy)
    th=th*(0.3+0.7*taper)
    Pc=Pc+Nc*th[:,None]
    Pc=laplace(Pc,tri,np.zeros(len(Pc),bool),it=2,lam=0.35)
    Nc=vnormals(Pc,tri)
    if np.mean(((Pc-np.array([0,B.head_y+7.5,zc]))*Nc).sum(1)>0)<0.5: Nc=-Nc
    ymin,ymax=Pc[:,1].min(),Pc[:,1].max()
    UVc=np.stack([((azc+np.pi)/(2*np.pi))*0.5*0.96+0.01,1-(Pc[:,1]-ymin)/(ymax-ymin)*0.96-0.02],1)
    return Pc,Nc,UVc,tri

def build_hair(B,seed=5):
    rng=np.random.default_rng(seed)
    hp=HP(B)
    Pc,Nc,UVc,tri=cap(B,hp)
    PK=[];UK=[];TK=[];base=0
    def add(res):
        nonlocal base
        P_,U_,T_=res
        PK.append(P_); UK.append(np.stack([0.5+0.5*(0.02+0.96*U_[:,0]),0.02+0.96*U_[:,1]],1)); TK.append(T_+base); base+=len(P_)
    top=B.head_y+19.7
    # --- camadas de trás e dos lados (wolf cut: curtas por cima, compridas por baixo)
    tiers=[ # (espaço angular, espessura, raiz acima da linha, encurtamento, flick, largura)
        (0.17,0.55,2.0,0.0,0.9,4.6),
        (0.19,1.30,4.5,5.0,1.2,4.4),
        (0.23,2.05,7.5,10.5,1.7,4.2)]
    for ti,(dstep,thick,rootup,shorten,flick,wd) in enumerate(tiers):
        a=-np.pi+dstep*(0.5*(ti%2))
        while a<np.pi:
            aa=((a+np.pi)%(2*np.pi))-np.pi
            if abs(aa)>0.62:
                y0=min(top-3.0,hairline(np.array([aa]),B)[0]+rootup)
                yt=tipline(aa)+shorten*(0.55 if abs(aa)<1.4 else 1.0)+rng.uniform(-1.3,1.3)
                if yt<y0-3:
                    add(card(hp,aa,y0,yt,rng.uniform(-0.05,0.05),wd*rng.uniform(0.9,1.15),thick,flick*rng.uniform(0.7,1.3),rng.uniform(0.6,1.4),rng.uniform(0,1),rng))
            a+=dstep*rng.uniform(0.9,1.1)
    # --- cortina (franja repartida ao meio): cada lado varre da risca até a têmpora
    for sg in (-1,1):
        for li,(thick,n,yend0,wd) in enumerate([(0.9,7,168.0,3.5),(1.6,6,171.0,3.3),(2.3,4,174.0,3.0)]):
            for k in range(n):
                f=(k+0.5)/n
                th0=sg*(0.07+0.35*f**1.3)
                y0=181.8-1.5*f
                yend=yend0+3.5*f+rng.uniform(-0.7,0.7)
                dth=sg*(1.30-0.55*f)*(1.0-0.12*li)
                add(card(hp,th0,y0,yend,dth,wd,thick,0.9+0.5*li,rng.uniform(0.4,1.1),rng.uniform(0,1),rng,nseg=11))
    # --- camada curta do topo para dar volume (repartida: fios saem da risca)
    for sg in (-1,1):
        for k in range(7):
            f=(k+0.5)/7
            th0=sg*(0.25+2.7*f)
            y0=top-1.2
            yend=top-9.0-3.0*np.sin(f*np.pi)-rng.uniform(0,3)
            add(card(hp,th0,y0,yend,sg*rng.uniform(0.0,0.25),4.4,2.6,1.9,rng.uniform(0.5,1.2),rng.uniform(0,1),rng,nseg=8))
    PK=np.vstack(PK); UK=np.vstack(UK); TK=np.vstack(TK)
    # normais (cartões: pela geometria; orientadas para fora)
    cpt=np.array([0,B.head_y+7.5,hp.zc])
    NK=vnormals(PK,TK)
    flip=((PK-cpt)*NK).sum(1)<0; NK[flip]=-NK[flip]
    PP=np.vstack([Pc,PK]); NN=np.vstack([Nc,NK]); UV=np.vstack([UVc,UK]); TT=np.vstack([tri,TK+len(Pc)])
    return PP,NN,UV,TT

def make_texture(size=1024):
    H=512; W=size
    img=np.zeros((H,W,4),np.float32)
    def streaks(h,w,seed,sig):
        r=np.random.default_rng(seed).standard_normal((h,w)).astype(np.float32)
        n=ndimage.gaussian_filter(r,sig,mode=('wrap','wrap')); n/=max(n.std(),1e-6); return n
    h=H; w=W//2
    n1=streaks(h,w,1,(18,0.8)); n2=streaks(h,w,2,(6,0.6)); n3=streaks(h,w,3,(30,2.0))
    base=np.array([10,10,12],np.float32)
    col=base+(n1[...,None]*2.6+n2[...,None]*1.6)
    gl=np.clip(n3*0.9-0.2,0,1)*np.clip(n1*0.5+0.5,0,1)
    col+=gl[...,None]*np.array([30,32,42],np.float32)
    img[:,:w,:3]=col; img[:,:w,3]=255
    vv=np.linspace(0,1,h)[:,None]; uu=np.linspace(0,1,w)[None,:]
    s1=streaks(h,w,5,(26,0.9)); s2=streaks(h,w,6,(7,0.55)); s3=streaks(h,w,7,(2,1.6))
    # silhueta da mecha: larga na raiz, afina em ponta com fios separados
    half=0.5*(1-0.80*smooth(0.35,1.0,vv)**1.2)
    edge=np.abs(uu-0.5)-half+0.012*s3*(vv>0.5)
    alpha=np.clip(0.5-edge*70,0,1)
    gaps=((s2>1.05)&(vv>0.62+0.2*np.abs(s1)))   # pontas repartidas
    alpha=alpha*(~gaps)*np.clip((1-vv)*14,0,1)
    lc=np.array([9,9,11],np.float32)+(s1[...,None]*2.8+s2[...,None]*1.2)
    # brilho (reflexo) em faixa suave + raiz mais escura
    sheen=np.exp(-((vv-0.30)/0.16)**2)*np.clip(s1*0.45+0.55,0,1)
    lc+=sheen[...,None]*np.array([34,36,46],np.float32)
    lc*=(0.72+0.28*smooth(0.0,0.25,vv))[...,None]
    img[:,w:,:3]=lc; img[:,w:,3]=alpha*255
    return Image.fromarray(np.clip(img,0,255).astype(np.uint8),'RGBA')

def do_hair(g,OUT):
    B=load_body(g)
    P,N,UV,T=build_hair(B)
    tex=make_texture(); tex.save(OUT+'%s_hair.png'%g,optimize=True)
    bi=np.zeros((len(P),4),np.uint8); bw=np.zeros((len(P),4),np.uint8)
    t=np.clip((B.neck_y-2.0-P[:,1])/9.0,0,1)
    bi[:,0]=8; bi[:,1]=4; bw[:,0]=np.round((1-t)*255); bw[:,1]=255-bw[:,0]
    write_cup(OUT+'%s_hair.cup'%g,P,N,UV,T,bi,bw)
    return len(P),len(T)
if __name__=='__main__':
    import os; OUT='/home/claude/work/skate/out2/'; os.makedirs(OUT,exist_ok=True)
    print(do_hair(sys.argv[1],OUT))
