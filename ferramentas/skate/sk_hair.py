import sys, numpy as np
sys.path.insert(0,'/home/claude/work/skate')
from PIL import Image
from scipy import ndimage
from sk_common import *; from sk_garments import subdivide
rng=np.random.default_rng(11)

def hairline(az,B):
    a=np.abs(az); top=B.head_y+19.7
    xs=[0.0,0.7,1.15,1.6,1.95,2.5,3.14]
    ys=[top-5.0,top-5.6,top-9.0,top-14.0,top-19.0,top-23.0,top-25.0]
    return np.interp(a,xs,ys)

def frame_at(Pc,Nc,target):
    i=int(np.argmin(((Pc-target)**2).sum(1))); p=Pc[i]; n=Nc[i]
    down=np.array([0,-1.0,0]); down=down-n*np.dot(down,n); down/=max(np.linalg.norm(down),1e-6)
    side=np.cross(n,down); side/=max(np.linalg.norm(side),1e-6)
    return p,n,down,side

def lock(p,n,down,side,L,w0,tilt,bulge,sway,cyc,ph,curl=0.0,nseg=8,up=False):
    d=down*np.cos(tilt)+side*np.sin(tilt)
    pts=[];nrm=[];wd=[]
    for k in range(nseg):
        s=k/(nseg-1)
        base=p+n*0.25+d*(L*s)
        base=base+n*(bulge*np.sin(np.pi*min(1,s*1.1))+0.9*s)
        base=base+side*(sway*np.sin(2*np.pi*(s*cyc+ph))*s)
        if curl: base=base+(-d)*(curl*np.sin(np.pi*s)**2)+n*curl*0.8*s*s
        pts.append(base); wd.append(w0*(1-0.5*s))
    pts=np.array(pts)
    tang=np.gradient(pts,axis=0); tang/=np.maximum(np.linalg.norm(tang,axis=1,keepdims=True),1e-9)
    P=[];N=[];UV=[]
    for k in range(nseg):
        sv=np.cross(tang[k],n); sv/=max(np.linalg.norm(sv),1e-9)
        nn=np.cross(sv,tang[k]); nn/=max(np.linalg.norm(nn),1e-9)
        if np.dot(nn,n)<0: nn=-nn
        for e in (-1,1):
            P.append(pts[k]+sv*e*wd[k]/2); N.append(nn); UV.append(((e+1)/2,k/(nseg-1)))
    T=[]
    for k in range(nseg-1):
        a,b,c,d_=2*k,2*k+1,2*k+2,2*k+3
        T+=[(a,b,c),(b,d_,c)]
    return np.array(P),np.array(N),np.array(UV),np.array(T)

def build_hair(B):
    P=B.P; N=B.N
    hv=(P[:,1]>B.neck_y-1.5)
    tri0=B.idx[hv[B.idx].all(1)]
    P1,N1,tri,_=subdivide(P,N,tri0,[np.zeros(len(P))])
    P1,N1,tri,_=subdivide(P1,N1,tri,[np.zeros(len(P1))])
    c=np.array([0.0,B.head_y+7.5,0.0])
    az=np.arctan2(P1[:,0],P1[:,2]-c[2]); hl=hairline(az,B)
    cen=P1[tri].mean(1); caz=np.arctan2(cen[:,0],cen[:,2]-c[2]); chl=hairline(caz,B)
    sel=(cen[:,1]>chl)&(cen[:,1]>B.neck_y+2)
    tri=tri[sel]
    u,inv=np.unique(tri.ravel(),return_inverse=True); Pc=P1[u].copy(); Nc=N1[u].copy(); tri=inv.reshape(-1,3)
    azc=np.arctan2(Pc[:,0],Pc[:,2]-c[2]); hlc=hairline(azc,B); yy=Pc[:,1]
    top=B.head_y+19.7
    above=yy-hlc
    taper=smooth(0.0,2.5,above)
    th=1.45+2.2*smooth(top-9,top,yy)+1.7*smooth(0.3,0.95,np.cos(azc))*smooth(top-8,top-1,yy)
    th+=0.5*np.sin(7*azc+yy*0.42)+0.35*np.sin(12*azc-yy*0.31)+0.25*np.sin(17*azc+yy*0.6)
    th=np.maximum(th,0.5)*(0.25+0.75*taper)
    Pc=Pc+Nc*th[:,None]
    Pc=laplace(Pc,tri,np.zeros(len(Pc),bool),it=2,lam=0.35)
    Nc=vnormals(Pc,tri)
    if np.mean(((Pc-c)*Nc).sum(1)>0)<0.5: Nc=-Nc
    # UV do capacete (tela esquerda do atlas): u=azimute, v=altura
    ymin,ymax=Pc[:,1].min(),Pc[:,1].max()
    UVc=np.stack([((azc+np.pi)/(2*np.pi))*0.5*0.96+0.01,1-(Pc[:,1]-ymin)/(ymax-ymin)*0.96-0.02],1)
    # mechas (cartões com alfa)
    PK=[];NK=[];UK=[];TK=[]
    def add(res):
        P_,N_,U_,T_=res; base=sum(len(x) for x in PK)
        PK.append(P_); NK.append(N_); UK.append(np.stack([0.5+0.5*U_[:,0]*0.96+0.02*0.5,U_[:,1]*0.96+0.02],1)); TK.append(T_+base)
    def root(azv,ydel=1.2):
        yh=hairline(np.array([azv]),B)[0]+ydel
        return frame_at(Pc,Nc,np.array([c[0]+np.sin(azv)*11.5,yh,c[2]+np.cos(azv)*11.5-0.0]))
    # franja caindo na testa (varrida para um lado)
    for k,azv in enumerate(np.linspace(-0.95,0.95,17)):
        p,n,d,s=root(azv,0.8+rng.uniform(0,1.4))
        ytip=175.8+rng.uniform(-0.5,2.0)+1.6*abs(azv)+(0.8 if azv>0.4 else 0)
        L=max(3.0,(p[1]-ytip)*1.05)
        add(lock(p,n,d,s,L,rng.uniform(3.2,4.6),0.30+rng.uniform(-0.25,0.2)*(1 if azv>0 else 1),rng.uniform(1.0,2.2),rng.uniform(0.6,1.4),rng.uniform(0.7,1.3),rng.uniform(0,1),curl=rng.uniform(0.3,1.2)))
    # laterais cobrindo as orelhas
    for sg in (-1,1):
        for azv in np.linspace(1.0,2.35,8):
            a=sg*azv; p,n,d,s=root(a,0.6+rng.uniform(0,1.6))
            L=rng.uniform(6.0,9.5)
            add(lock(p,n,d,s,L,rng.uniform(3.4,5.0),rng.uniform(-0.2,0.25),rng.uniform(1.2,2.4),rng.uniform(0.8,1.7),rng.uniform(0.8,1.5),rng.uniform(0,1),curl=rng.uniform(0.4,1.4)))
    # nuca / costas, ondas até o pescoço
    for azv in np.linspace(2.35,np.pi,10):
        for sg in ((-1,1) if azv<3.0 else (1,)):
            a=sg*azv; p,n,d,s=root(a,2.5+rng.uniform(0,3.0))
            L=rng.uniform(9.0,13.5)
            add(lock(p,n,d,s,L,rng.uniform(3.6,5.2),rng.uniform(-0.15,0.15),rng.uniform(1.4,2.6),rng.uniform(0.8,1.8),rng.uniform(0.9,1.6),rng.uniform(0,1),curl=rng.uniform(0.6,1.8)))
    # cachos no topo (bagunçado)
    for k in range(11):
        azv=rng.uniform(-np.pi,np.pi); yv=rng.uniform(B.head_y+12.5,B.head_y+18.5)
        p,n,d,s=frame_at(Pc,Nc,np.array([np.sin(azv)*rng.uniform(2,8),yv,np.cos(azv)*rng.uniform(2,8)]))
        # direção para fora/cima com giro
        dirv=n*0.18+(s*rng.uniform(-1,1)+d*rng.uniform(-0.8,0.8))
        dirv/=np.linalg.norm(dirv); s2=np.cross(n,dirv); s2/=max(np.linalg.norm(s2),1e-6)
        add(lock(p,n,dirv,s2,rng.uniform(3.0,4.2),rng.uniform(3.4,4.6),0.0,rng.uniform(0.6,1.4),rng.uniform(0.6,1.2),rng.uniform(0.9,1.5),rng.uniform(0,1),curl=rng.uniform(0.8,1.8),nseg=7))
    PK=np.vstack(PK);NK=np.vstack(NK);UK=np.vstack(UK);TK=np.vstack(TK)
    PP=np.vstack([Pc,PK]); NN=np.vstack([Nc,NK]); UV=np.vstack([UVc,UK]); TT=np.vstack([tri,TK+len(Pc)])
    return PP,NN,UV,TT

def make_texture(size=1024):
    H=512; W=size
    img=np.zeros((H,W,4),np.float32)
    def streaks(h,w,seed,sig=(14,0.9)):
        r=np.random.default_rng(seed).standard_normal((h,w)).astype(np.float32)
        n=ndimage.gaussian_filter(r,sig,mode=('wrap','wrap')); n/=max(n.std(),1e-6); return n
    # --- capacete (esq.): preto com fios e brilho
    h=H; w=W//2
    n1=streaks(h,w,1,(18,0.8)); n2=streaks(h,w,2,(6,0.6)); n3=streaks(h,w,3,(30,2.0))
    base=np.array([11,11,13],np.float32)
    col=base+(n1[...,None]*3.0+n2[...,None]*2.0)
    gl=np.clip(n3*0.9-0.2,0,1)*np.clip(n1*0.5+0.5,0,1)
    col+=gl[...,None]*np.array([40,42,54],np.float32)
    root=np.linspace(1,0,h)[:,None]  # raiz mais escura em cima? (v cresce para baixo)
    col*=(0.7+0.3*np.clip(1-root,0,1))[...,None]
    img[:,:w,:3]=col; img[:,:w,3]=255
    # --- mechas (dir.): forma afilada, fios, ponta serrilhada
    h=H; w=W//2
    vv=np.linspace(0,1,h)[:,None]; uu=np.linspace(0,1,w)[None,:]
    s1=streaks(h,w,5,(20,0.9)); s2=streaks(h,w,6,(5,0.5)); s3=streaks(h,w,7,(2,2))
    half=0.5*(1-0.62*vv**1.5)
    edge=np.abs(uu-0.5)-half+0.012*s3*(vv>0.6)
    alpha=np.clip(0.5-edge*60,0,1)
    gaps=np.clip((s2*0.5+0.5)*3-0.9,0,1)   # fios soltos
    tipcut=np.clip((1-vv)*8,0,1)
    alpha=alpha*np.clip(0.97+0.1*gaps,0,1)*tipcut
    lc=np.array([10,10,12],np.float32)+(s1[...,None]*2.5+s2[...,None]*0.8)
    glo=np.clip(s1*0.9-0.1,0,1)*np.clip(1-vv*0.5,0,1)
    lc+=glo[...,None]*np.array([26,28,36],np.float32)
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
