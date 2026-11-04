import sys, numpy as np
sys.path.insert(0,'/home/claude/work/skate')
from PIL import Image
from scipy import ndimage
from sk_common import *
from sk_hair2 import HP, hairline, cap, tipline

def trace(hp,B,p0,sgn,lam0,length,ytip,thick,rng,front_clamp=True,bias_fwd=0.0,front_flat=False):
    """segue a superfície da cabeça a partir da risca: lateral perto do topo, gravidade embaixo."""
    top=B.head_y+19.7; zc=hp.zc
    pts=[p0.copy()]; p=p0.copy(); L=0.0; ds=1.2
    th=np.arctan2(p[0],p[2]-zc)
    for it in range(60):
        y=p[1]
        lam=(lam0 if front_flat else lam0*smooth(top-10.0,top-0.5,y))
        g=np.array([sgn*lam,-(1-lam)-(0.0 if not front_flat else 0.35),0.0])
        # normal aproximada da superfície (da esfera da cabeça)
        c=np.array([0.0,min(y,B.head_y+9.5),zc]); n=p-c; n/=max(np.linalg.norm(n),1e-6)
        d=g-n*np.dot(g,n); dn=np.linalg.norm(d)
        if dn<1e-6: break
        d/=dn
        q=p+d*ds
        thq=np.arctan2(q[0],q[2]-zc); yq=q[1]
        if front_clamp and abs(thq)<1.25 and yq<174.2: break
        r=hp.surf(yq,thq,thick)
        q=hp.pos(yq,thq,r)
        pts.append(q); p=q; L+=ds
        if yq<=ytip or L>=length: break
    return np.array(pts)

def lock(hp,path,width,thick,flick,nseg=10,ncol=5):
    # reamostra por comprimento de arco
    seg=np.linalg.norm(np.diff(path,axis=0),axis=1); cum=np.concatenate([[0],np.cumsum(seg)])
    if cum[-1]<2.0: return None
    ss=np.linspace(0,cum[-1],nseg)
    C=np.stack([np.interp(ss,cum,path[:,k]) for k in range(3)],1)
    tang=np.gradient(C,axis=0); tang/=np.maximum(np.linalg.norm(tang,axis=1,keepdims=True),1e-9)
    rows=[]
    for k in range(nseg):
        s=k/(nseg-1)
        wk=width*(1.0-0.55*s**2.4)*(1.0-0.9*smooth(0.90,1.0,s))
        cc=C[k]; th=np.arctan2(cc[0],cc[2]-hp.zc); y=cc[1]
        r0=np.hypot(cc[0],cc[2]-hp.zc)
        # direção lateral na superfície = perpendicular ao caminho e à normal radial
        nrm=np.array([np.sin(th),0.15,np.cos(th)]); nrm/=np.linalg.norm(nrm)
        side=np.cross(nrm,tang[k]); sn=np.linalg.norm(side)
        side=side/sn if sn>1e-6 else np.array([1.0,0,0])
        row=[]
        for e in np.linspace(-1,1,ncol):
            q=cc+side*e*wk/2
            tq=np.arctan2(q[0],q[2]-hp.zc); yq=q[1]
            rr=hp.surf(yq,tq,thick)+0.9*(1-e*e)*(1-0.6*s)+flick*s**2.5
            row.append(hp.pos(yq,tq,rr))
        rows.append(row)
    rows=np.array(rows)
    P=rows.reshape(-1,3)
    UV=np.array([((e+1)/2,k/(nseg-1)) for k in range(nseg) for e in np.linspace(-1,1,ncol)],float)
    T=[]
    for k in range(nseg-1):
        for e in range(ncol-1):
            a=k*ncol+e; b=a+1; c=a+ncol; d=c+1
            T+=[(a,b,c),(b,d,c)]
    return P,UV,np.array(T)

def build_hair(B,seed=3):
    rng=np.random.default_rng(seed)
    hp=HP(B); top=B.head_y+19.7; zc=hp.zc
    Pc,Nc,UVc,tri=cap(B,hp)
    # saia de cabelo: casca contínua que cai da linha do cabelo até um pouco antes das pontas
    ths=np.linspace(-np.pi,np.pi,97); R=9
    SP=[];SU=[];ST=[]
    valid=np.abs(ths)>=0.78
    rows_idx=np.zeros((R+1,len(ths)),int)
    for j,th in enumerate(ths):
        ytop=hairline(np.array([th]),B)[0]+2.0
        ybot=float(tipline(abs(th)))+5.0+1.2*np.sin(7*th)+0.8*np.sin(13*th+1)
        for i in range(R+1):
            y=ytop+(ybot-ytop)*i/R
            r=hp.surf(y,th,0.05+0.35*i/R)
            rows_idx[i,j]=len(SP); SP.append(hp.pos(y,th,r))
            SU.append((0.01+0.46*(th+np.pi)/(2*np.pi),0.02+0.96*i/R))
    for j in range(len(ths)-1):
        if not (valid[j] and valid[j+1]): continue
        for i in range(R):
            a=rows_idx[i,j]; b=rows_idx[i,j+1]; c=rows_idx[i+1,j]; d=rows_idx[i+1,j+1]
            ST+=[(a,b,c),(b,d,c)]
    SP=np.array(SP); SU=np.array(SU); ST=np.array(ST)
    PK=[SP];UK=[SU];TK=[ST];base=len(SP)
    def add(res):
        nonlocal base
        if res is None: return
        P_,U_,T_=res
        PK.append(P_); UK.append(np.stack([0.5+0.5*(0.02+0.96*U_[:,0]),0.02+0.96*U_[:,1]],1)); TK.append(T_+base); base+=len(P_)
    # raízes ao longo da risca (frente -> coroa -> costas)
    def root(phi,thick):
        # phi 0..1: 0 = linha do cabelo da frente, 0.5 = coroa, 1 = nuca
        if phi<0.5:
            u=phi/0.5; y=179.2+(top-179.2)*np.sin(u*np.pi/2)**1.0; th=0.0
        else:
            u=(phi-0.5)/0.5; y=top-(top-174.0)*np.sin(u*np.pi/2)**1.4; th=np.pi
        r=hp.surf(y,th,thick)
        return hp.pos(y,th,r)
    tiers=[ # (espessura, comprimento relativo, largura, flick, nº de raízes)
        (0.55,1.00,5.8,1.7,13),
        (1.25,0.80,5.6,2.3,12),
        (1.95,0.58,5.4,2.9,10)]
    for ti,(thick,lenf,wd,flick,nroot) in enumerate(tiers):
        for sgn in (-1,1):
            for k in range(nroot):
                phi=(k+0.5)/nroot*0.93+0.03+rng.uniform(-0.01,0.01)+ti*0.012
                lam0=np.interp(phi,[0,0.26,0.30,0.55,0.8,1.0],[0.80,0.80,0.92,0.62,0.30,0.12])
                if phi<0.26: thick=thick*0.55
                p0=root(phi,thick); p0=p0+np.array([sgn*0.5,0,0])
                # comprimento/ponta: mais comprido atrás (nuca), médio nos lados
                tipy=np.interp(phi,[0,0.3,0.55,0.8,1.0],[168.0,163.0,159.0,156.0,154.5])+ (1-lenf)*14.0*np.interp(phi,[0,0.5,1],[0.2,1.0,1.0])+rng.uniform(-1.0,1.0)
                length=np.interp(phi,[0,0.3,0.55,1.0],[20.0,24.0,26.0,22.0])*(0.55+0.45*lenf)
                if phi<0.28: tipy=max(tipy,175.0 if ti>0 else 173.5)
                path=trace(hp,B,p0,sgn,lam0,length,tipy,thick,rng,front_flat=(phi<0.26))
                add(lock(hp,path,wd*rng.uniform(0.92,1.12),thick,flick*rng.uniform(0.7,1.3)))
    # camada baixa da nuca/laterais (para o corte comprido atrás): raízes na altura das orelhas, caindo reto
    for sgn in (-1,1):
        for k,az in enumerate(np.linspace(0.9,np.pi-0.15,9)):
            for ti,(thick,drop) in enumerate(((0.5,0.0),(1.2,2.5))):
                y0=hairline(np.array([az]),B)[0]+4.5+ti*2.0
                th=sgn*az
                p0=hp.pos(y0,th,hp.surf(y0,th,thick))
                ytip=np.interp(az,[0.9,1.6,2.3,2.9,3.1],[164.0,160.5,157.5,155.0,154.5])+drop+rng.uniform(-0.8,0.8)
                path=trace(hp,B,p0,0.0,0.0,24.0,ytip,thick,rng,front_clamp=False)
                add(lock(hp,path,5.6*rng.uniform(0.95,1.1),thick,1.3))
    PK=np.vstack(PK); UK=np.vstack(UK); TK=np.vstack(TK)
    cpt=np.array([0,B.head_y+7.5,zc])
    NK=vnormals(PK,TK)
    flip=((PK-cpt)*NK).sum(1)<0; NK[flip]=-NK[flip]
    PP=np.vstack([Pc,PK]); NN=np.vstack([Nc,NK]); UV=np.vstack([UVc,UK]); TT=np.vstack([tri,TK+len(Pc)])
    return PP,NN,UV,TT

def make_texture(size=1024):
    H=512; W=size
    img=np.zeros((H,W,4),np.float32); img[...,3]=255
    def streaks(h,w,seed,sig):
        r=np.random.default_rng(seed).standard_normal((h,w)).astype(np.float32)
        n=ndimage.gaussian_filter(r,sig,mode=('wrap','wrap')); n/=max(n.std(),1e-6); return n
    h=H; w=W//2
    # capacete: escuro com fios radiais suaves
    n1=streaks(h,w,1,(16,0.9)); n2=streaks(h,w,2,(5,0.6))
    cap=np.array([11,11,14],np.float32)+n1[...,None]*2.2+n2[...,None]*1.2
    img[:,:w,:3]=cap
    vv=np.linspace(0,1,h)[:,None]; uu=np.linspace(0,1,w)[None,:]
    s1=streaks(h,w,5,(24,1.0)); s2=streaks(h,w,6,(6,0.6))
    edge=np.abs(uu-0.5)*2
    base=np.array([10,10,13],np.float32)+(s1[...,None]*1.8+s2[...,None]*0.7)
    base*= (1-0.30*smooth(0.55,1.0,edge))[...,None]            # bordas mais escuras
    # brilho em faixa (mecha): suave, bem na parte de cima/meio da mecha
    band=np.exp(-((uu-0.5+0.06*np.sin(vv*5))/0.28)**2)*np.exp(-((vv-0.38)/0.30)**2)
    band=band*np.clip(0.8+0.25*s1,0,1.2)
    hl=np.array([26,30,42],np.float32)
    col=base+band[...,None]*hl
    col*= (0.80+0.20*smooth(0.0,0.20,vv))[...,None]
    img[:,w:,:3]=col
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
    OUT='/home/claude/work/skate/out2/'
    print(do_hair(sys.argv[1],OUT))
