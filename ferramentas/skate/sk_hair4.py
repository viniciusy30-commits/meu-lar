import sys, numpy as np
sys.path.insert(0,'/home/claude/work/skate')
from PIL import Image
from scipy import ndimage
from sk_common import *
from sk_hair2 import HP, hairline, cap

def wrap(a): return (a+np.pi)%(2*np.pi)-np.pi

def chunk(hp,th0,y0,th1,y1,width,thick,off0,vol,flick,wave,ph,rng,nseg=14,K=7,curl_in=0.0):
    """mecha 3D (tubo achatado e afilado) que vai de (th0,y0) até (th1,y1) por cima da cabeça."""
    dth=wrap(th1-th0)
    C=[];NR=[]
    for k in range(nseg):
        s=k/(nseg-1)
        e=s*s*(3-2*s)
        th=th0+dth*(0.35*s+0.65*e)+wave*0.05*np.sin(2*np.pi*(1.2*s+ph))*s
        y=y0+(y1-y0)*(0.55*s+0.45*s**1.6)
        off=off0+vol*np.sin(np.pi*min(1,s*1.15))**0.8+flick*s**3-curl_in*s**4
        r=hp.surf(y,th,max(off,0.15))
        C.append(hp.pos(y,th,r))
        nr=np.array([np.sin(th),0.25,np.cos(th)]); NR.append(nr/np.linalg.norm(nr))
    C=np.array(C); NR=np.array(NR)
    T=np.gradient(C,axis=0); T/=np.maximum(np.linalg.norm(T,axis=1,keepdims=True),1e-9)
    P=[];UV=[];Tri=[]
    for k in range(nseg):
        s=k/(nseg-1)
        tap=(1-s**2.2)**0.9 if s<1 else 0.0
        w=width*(0.75+0.25*np.sin(np.pi*min(1,s*1.6)))*tap*0.5
        h=thick*tap*0.5+0.02
        n=NR[k]-T[k]*np.dot(NR[k],T[k]); n/=max(np.linalg.norm(n),1e-9)
        b=np.cross(T[k],n)
        for j in range(K):
            a=2*np.pi*j/K
            P.append(C[k]+b*np.cos(a)*w+n*np.sin(a)*h)
            UV.append((j/K,s))
    for k in range(nseg-1):
        for j in range(K):
            a=k*K+j; b_=k*K+(j+1)%K; c=a+K; d=b_+K
            Tri+=[(a,c,b_),(b_,c,d)]
    # tampa na raiz
    ci=len(P); P.append(C[0]-T[0]*0.3); UV.append((0.5,0.0))
    for j in range(K): Tri.append((ci,j,(j+1)%K))
    return np.array(P),np.array(UV),np.array(Tri)

def build_hair(B,seed=7):
    rng=np.random.default_rng(seed)
    hp=HP(B); top=B.head_y+19.7
    Pc,Nc,UVc,tri=cap(B,hp)
    # capacete um pouco para dentro (só preenche fendas)
    PK=[];UK=[];TK=[];base=0
    def add(res):
        nonlocal base
        P_,U_,T_=res
        PK.append(P_); UK.append(np.stack([0.5+0.5*(0.02+0.96*U_[:,0]),0.02+0.96*U_[:,1]],1)); TK.append(T_+base); base+=len(P_)
    def tipy(th):
        a=abs(th)
        return np.interp(a,[0,0.6,0.95,1.3,1.8,2.4,3.14],[174.5,175.0,170.0,165.0,161.5,158.5,157.0])
    # 1) camada de baixo: da coroa até as pontas, cobrindo tudo (exceto a frente)
    for th in np.linspace(-np.pi,np.pi,34,endpoint=False):
        th=th+rng.uniform(-0.04,0.04)
        if abs(th)<0.75: continue
        y0=top-1.5+rng.uniform(-1,0.5)
        add(chunk(hp,th,y0,th,tipy(th)+rng.uniform(-1.0,1.0),rng.uniform(4.4,5.4),1.5,0.4,0.8,1.2,1.0,rng.uniform(0,1),rng))
    # 2) camada do meio (wolf cut): mais curta, pontas viradas para fora
    for th in np.linspace(-np.pi,np.pi,24,endpoint=False):
        th=th+rng.uniform(-0.08,0.08)
        if abs(th)<0.8: continue
        y0=top-0.8+rng.uniform(-1,0.5)
        add(chunk(hp,th,y0,th+rng.uniform(-0.1,0.1),tipy(th)+rng.uniform(3.5,6.0),rng.uniform(4.0,5.0),1.7,1.3,1.4,2.2,1.2,rng.uniform(0,1),rng))
    # 3) volume de cima (bagunçado): mechas curtas saindo da coroa
    for k in range(22):
        th=rng.uniform(-np.pi,np.pi); th1=th+rng.uniform(-0.25,0.25)
        y0=top-0.3+rng.uniform(-0.8,0.3)
        y1=top-rng.uniform(6,11)
        add(chunk(hp,th,y0,th1,y1,rng.uniform(3.6,4.6),1.5,1.4,1.0,0.6,1.5,rng.uniform(0,1),rng,nseg=10))
    # 3b) cobertura do topo: mechas com raízes espalhadas no alto da cabeça (sem "disco" liso)
    for k in range(34):
        th=rng.uniform(-np.pi,np.pi); y0=top-rng.uniform(0.3,5.5)
        add(chunk(hp,th,y0,th+rng.uniform(-0.35,0.35),y0-rng.uniform(7,11),rng.uniform(4.0,5.2),1.5,rng.uniform(1.2,2.0),0.9,0.5,1.2,rng.uniform(0,1),rng,nseg=9))
    # 4) franja bagunçada caindo na testa (pontas separadas, até as sobrancelhas)
    for k in range(17):
        f=(k+0.5)/17*2-1
        th1=f*0.95+rng.uniform(-0.05,0.05)
        th0=f*0.35+rng.uniform(-0.15,0.15)
        y0=top-0.5+rng.uniform(-0.6,0.4)
        y1=174.0+3.0*abs(f)**1.6+rng.uniform(-1.0,1.0)
        if abs(f)>0.75: y1-=2.5
        add(chunk(hp,th0,y0,th1,y1,rng.uniform(3.4,4.4),1.5,1.4+0.6*(k%2),1.6,0.3,1.4,rng.uniform(0,1),rng,curl_in=0.6))
    # 5) mechas de lado na frente das orelhas (emolduram o rosto)
    for sg in (-1,1):
        for k in range(4):
            th1=sg*(1.0+0.12*k)+rng.uniform(-0.05,0.05)
            add(chunk(hp,sg*0.5,top-2.0,th1,167.0-1.2*k+rng.uniform(-1,1),rng.uniform(3.8,4.6),1.5,1.2,1.2,1.5,1.0,rng.uniform(0,1),rng))
    PK=np.vstack(PK); UK=np.vstack(UK); TK=np.vstack(TK)
    NK=vnormals(PK,TK)
    cpt=np.array([0,B.head_y+7.5,hp.zc])
    # cap: escuro, um pouco encolhido
    from scipy.spatial import cKDTree
    hv=B.P[:,1]>B.neck_y-4; HPb=B.P[hv]; HNb=B.N[hv]
    d,ix=cKDTree(HPb).query(Pc,k=4); w=1/(d+0.2)
    sp=(HPb[ix]*w[...,None]).sum(1)/w.sum(1)[:,None]; sn=(HNb[ix]*w[...,None]).sum(1); sn/=np.linalg.norm(sn,axis=1,keepdims=True)
    Pc2=Pc-sn*(((Pc-sp)*sn).sum(1)-0.4)[:,None]
    PP=np.vstack([Pc2,PK]); NN=np.vstack([Nc,NK]); UV=np.vstack([UVc,UK]); TT=np.vstack([tri,TK+len(Pc)])
    return PP,NN,UV,TT

def make_texture():
    H=512; W=1024
    img=np.zeros((H,W,4),np.float32); img[...,3]=255
    def streaks(h,w,seed,sig):
        r=np.random.default_rng(seed).standard_normal((h,w)).astype(np.float32)
        n=ndimage.gaussian_filter(r,sig,mode=('wrap','wrap')); n/=max(n.std(),1e-6); return n
    h=H; w=W//2
    n1=streaks(h,w,1,(14,0.8))
    img[:,:w,:3]=np.array([14,14,17],np.float32)+n1[...,None]*2.5+np.clip(n1,0,3)[...,None]*np.array([6,7,10],np.float32)
    vv=np.linspace(0,1,h)[:,None]; uu=np.linspace(0,1,w)[None,:]
    s1=streaks(h,w,5,(30,0.7)); s2=streaks(h,w,6,(8,0.5))
    col=np.array([13,13,16],np.float32)+s1[...,None]*3.0+s2[...,None]*1.8
    # brilho: faixa ao longo da mecha, no lado de fora do tubo (u ~0.25)
    face=np.clip(np.sin(2*np.pi*uu),0,1)**1.5
    sheen=face*(0.45+0.55*np.exp(-((vv-0.4)/0.3)**2))*np.clip(0.75+0.35*s1,0,1.4)
    col+=sheen[...,None]*np.array([38,42,56],np.float32)
    
    img[:,w:,:3]=col
    return Image.fromarray(np.clip(img,0,255).astype(np.uint8),'RGBA')

def do_hair(g,OUT):
    B=load_body(g)
    P,N,UV,T=build_hair(B)
    make_texture().save(OUT+'%s_hair.png'%g,optimize=True)
    bi=np.zeros((len(P),4),np.uint8); bw=np.zeros((len(P),4),np.uint8)
    t=np.clip((B.neck_y-2.0-P[:,1])/9.0,0,1)
    bi[:,0]=8; bi[:,1]=4; bw[:,0]=np.round((1-t)*255); bw[:,1]=255-bw[:,0]
    write_cup(OUT+'%s_hair.cup'%g,P,N,UV,T,bi,bw)
    return len(P),len(T)
if __name__=='__main__':
    print(do_hair(sys.argv[1],'/home/claude/work/skate/out2/'))
