import numpy as np, math
from flora_lib import *
F=MT
def V(*a): return np.array(a,float)
def nrm(v): return v/(np.linalg.norm(v)+1e-9)
TEX=dict(grain='grain.png',weave='weave.png',metal='brushed.png',white='white.png',leather='leather.png')
def K(tex,mat=0,cut=0): return (TEX.get(tex,tex),mat,cut)
OAK=(0.93,0.76,0.54);WAL=(0.62,0.42,0.30);WHT=(0.96,0.95,0.92);BLK=(0.14,0.15,0.17);BRASS=(0.9,0.72,0.38);STEEL=(0.82,0.85,0.88)

def _samples(h,r,step=0.22):
    r=max(r,1e-4); edge=[0,r*0.5,r] if r>=0.03 else [0,r]
    inner=max(2*h-2*r,0); n=max(1,int(inner/step)); mid=[r+inner*i/n for i in range(1,n)]
    pts=sorted(set([round(v,6) for v in edge+mid+[2*h-e for e in edge]]))
    return [p-h for p in pts]

def rbox(A,key,c,size,r=0.02,col=(1,1,1),uv=1.0,puff=0.0,ao=None,step=0.22,faces='all',rot=0.0):
    c=np.asarray(c,float); h=np.asarray(size,float)/2; r=min(r,*h*0.999)
    P=[];N=[];C=[];UV=[];T=[]
    for ax in range(3):
        for sg in (-1,1):
            if faces=='notbottom' and ax==1 and sg==-1: continue
            if faces=='nobottomtop' and ax==1: continue
            b,cc=[i for i in range(3) if i!=ax]
            sb=_samples(h[b],r,step); sc=_samples(h[cc],r,step); base=len(P)
            for vb in sb:
                for vc in sc:
                    q=np.zeros(3); q[ax]=sg*h[ax]; q[b]=vb; q[cc]=vc
                    inner=np.clip(q,-(h-r),h-r); d=q-inner; l=np.linalg.norm(d)
                    if l>1e-9: n=d/l; p=inner+n*r
                    else: n=np.zeros(3); n[ax]=sg; p=q
                    if puff:
                        f=(1-(q[b]/h[b])**2)*(1-(q[cc]/h[cc])**2); p=p+n*puff*f
                    if rot: 
                        cs,sn=math.cos(rot),math.sin(rot); p=np.array([p[0]*cs+p[2]*sn,p[1],-p[0]*sn+p[2]*cs]); n=np.array([n[0]*cs+n[2]*sn,n[1],-n[0]*sn+n[2]*cs])
                    w=c+p; P.append(w); N.append(n)
                    u=(w[b if ax!=1 else 0]+0)*uv; v=(w[cc if ax!=1 else 2])*uv
                    if ax==0: u,v=w[2]*uv,w[1]*uv
                    elif ax==1: u,v=w[0]*uv,w[2]*uv
                    else: u,v=w[0]*uv,w[1]*uv
                    UV.append((u,v)); k=1.0 if ao is None else ao(w)
                    C.append((col[0]*k,col[1]*k,col[2]*k,1))
            nb,nc=len(sb),len(sc)
            for i in range(nb-1):
                for j in range(nc-1):
                    a=base+i*nc+j; T+=[(a,a+1,a+nc),(a+1,a+nc+1,a+nc)]
    A.add(key,P,N,C,UV,T)

def leg(A,key,x,z,h,r0,r1,col,sides=10,y0=0.0,ao=True,lean=(0,0)):
    pts=[V(x,y0,z),V(x+lean[0]*0.5,y0+h*0.5,z+lean[1]*0.5),V(x+lean[0],y0+h,z+lean[1])]
    A.tube(key,pts,[r0,(r0+r1)/2,r1],sides=sides,vscale=1.0/0.5,uscale=1.0,col=lambda p,t:(col[0]*(0.75+0.25*min(1,p[1]/0.3)),col[1]*(0.75+0.25*min(1,p[1]/0.3)),col[2]*(0.75+0.25*min(1,p[1]/0.3)),1))

def gao(y0=0.28,lo=0.68):
    return lambda w: lo+(1-lo)*min(1.0,max(0.0,w[1]/y0))

def quad(A,key,p0,p1,p2,p3,n,col=(1,1,1,1),uv=((0,1),(1,1),(1,0),(0,0))):
    A.add(key,[p0,p1,p2,p3],[n]*4,[col]*4,list(uv),[(0,1,2),(0,2,3)])

def sphere(A,key,c,r,col=(1,1,1),seg=14,sy=1.0,uv=1.0,emit=False):
    P=[];N=[];C=[];UV=[];T=[]
    for i in range(seg+1):
        t=math.pi*i/seg
        for j in range(seg*2+1):
            p=2*math.pi*j/(seg*2); n=V(math.sin(t)*math.cos(p),math.cos(t),math.sin(t)*math.sin(p))
            P.append(np.asarray(c)+V(n[0]*r,n[1]*r*sy,n[2]*r)); N.append(np.zeros(3) if emit else n); C.append(col+(1,)); UV.append((j/(seg*2)*uv,i/seg*uv))
    for i in range(seg):
        for j in range(seg*2):
            a=i*(seg*2+1)+j; T+=[(a,a+1,a+seg*2+1),(a+1,a+seg*2+2,a+seg*2+1)]
    A.add(key,P,N,C,UV,T)

def books(A,c,w,rng,maxh=0.3,depth=0.2,tilt_last=True,sp='spine.png'):
    """fileira de livros ao longo de +x a partir de c=(x,y,z); devolve x final"""
    x=c[0]; cols=[(0.78,0.28,0.22),(0.9,0.68,0.2),(0.28,0.55,0.34),(0.22,0.42,0.66),(0.5,0.32,0.62),(0.9,0.5,0.22),(0.2,0.6,0.64),(0.9,0.86,0.76),(0.62,0.2,0.3)]
    end=c[0]+w; i=0
    while x<end-0.06:
        ww=rng.uniform(0.035,0.07); hh=rng.uniform(maxh*0.72,maxh); 
        if x+ww>end: break
        cl=cols[rng.integers(len(cols))]; cx=x+ww/2
        A.box(K('weave',F['FABRIC']),(cx,c[1]+hh/2,c[2]),(ww,hh,depth),col=cl+(1,),uv=3.0)
        A.add(K(sp,F['PLAIN'],1),[V(cx-ww/2*0.9,c[1]+hh*0.12,c[2]+depth/2+0.0012),V(cx+ww/2*0.9,c[1]+hh*0.12,c[2]+depth/2+0.0012),V(cx+ww/2*0.9,c[1]+hh*0.9,c[2]+depth/2+0.0012),V(cx-ww/2*0.9,c[1]+hh*0.9,c[2]+depth/2+0.0012)],[V(0,0,1)]*4,[(1,1,1,1)]*4,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
        x+=ww+0.004; i+=1
    return x

def ceramic(A,c,prof,col,sides=24): A.lathe(K('white',F['PLAIN']),c,prof,sides=sides,col=col+(1,))
