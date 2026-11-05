import numpy as np, struct, math, os
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
OUT='/home/claude/work/env/out/'
MT=dict(PLAIN=0,FLOOR_L=1,FLOOR_D=2,TILE=3,STONE=4,PLASTER=5,WOOD=6,FABRIC=7,GRASS=8,PAVER=9,RUG=10,METAL=11,GLASS=12)

def tnoise(n,sx,sy,seed):
    r=np.random.default_rng(seed).normal(size=(n,n)); r=ndimage.gaussian_filter(r,(sy,sx),mode='wrap')
    r=(r-r.min())/(r.max()-r.min()+1e-9); return r
def lerpc(a,b,t): t=t[...,None]; return np.array(a,float)*(1-t)+np.array(b,float)*t
def save_tex(name,arr):
    Image.fromarray(np.clip(arr,0,255).astype(np.uint8)).save(OUT+'tex/'+name)

class Asset:
    def __init__(s,name): s.name=name; s.parts={}
    def _acc(s,key):
        if key not in s.parts: s.parts[key]=dict(P=[],N=[],C=[],UV=[],T=[],n=0)
        return s.parts[key]
    def add(s,key,P,N,C,UV,T):
        a=s._acc(key); P=np.asarray(P,float); n=len(P)
        a['P'].append(P); a['N'].append(np.asarray(N,float)); a['C'].append(np.asarray(C,float)); a['UV'].append(np.asarray(UV,float))
        a['T'].append(np.asarray(T,int)+a['n']); a['n']+=n
    # ---------- primitivas
    def tube(s,key,path,radii,sides=7,vscale=0.6,uscale=1.0,col=None,cap=True):
        path=np.asarray(path,float); m=len(path)
        tg=np.gradient(path,axis=0); tg/=np.linalg.norm(tg,axis=1,keepdims=True)+1e-9
        u=np.cross(tg[0],[0.3,0.9,0.1]); u/=np.linalg.norm(u)+1e-9
        P=[];N=[];UV=[];C=[]; L=0
        for i in range(m):
            if i>0: L+=np.linalg.norm(path[i]-path[i-1])
            if i>0:
                u=u-tg[i]*np.dot(u,tg[i]); nu=np.linalg.norm(u); u=u/nu if nu>1e-6 else np.cross(tg[i],[1,0,0])
            v=np.cross(tg[i],u)
            for k in range(sides+1):
                a=2*math.pi*k/sides; d=math.cos(a)*u+math.sin(a)*v
                P.append(path[i]+d*radii[i]); N.append(d); UV.append((k/sides*uscale,L*vscale))
                c=col(path[i],i/(m-1)) if col else (1,1,1,1); C.append(c)
        T=[]
        for i in range(m-1):
            for k in range(sides):
                a=i*(sides+1)+k; b=a+1; c=a+sides+1; d=c+1
                T+=[(a,c,b),(b,c,d)]
        s.add(key,P,N,C,UV,T)
    def cards(s,key,centers,size,normals,cols,rng,spread=0.0,uvrect=(0,0,1,1),aspect=1.0,orient=None):
        P=[];N=[];UV=[];C=[];T=[]
        for i,c in enumerate(centers):
            q=rng.normal(size=3); q/=np.linalg.norm(q)
            if orient is not None: q=orient[i]
            a=np.cross(q,[0,1,0]); 
            if np.linalg.norm(a)<1e-3: a=np.array([1.,0,0])
            a/=np.linalg.norm(a); b=np.cross(q,a)
            ang=rng.uniform(0,2*math.pi); a2=a*math.cos(ang)+b*math.sin(ang); b2=-a*math.sin(ang)+b*math.cos(ang)
            sz=size*rng.uniform(0.8,1.25); h=sz/2
            base=len(P); cc=np.asarray(c)+rng.normal(size=3)*spread
            for (x,y,uu,vv) in ((-1,-1,0,1),(1,-1,1,1),(1,1,1,0),(-1,1,0,0)):
                P.append(cc+a2*x*h+b2*y*h*aspect); N.append(normals[i]); C.append(cols[i])
                UV.append((uvrect[0]+uu*(uvrect[2]-uvrect[0]),uvrect[1]+vv*(uvrect[3]-uvrect[1])))
            T+=[(base,base+1,base+2),(base,base+2,base+3)]
        s.add(key,P,N,C,UV,T)
    def box(s,key,c,sz,col=(1,1,1,1),uv=1.0,tilt=None):
        cx,cy,cz=c; sx,sy,sz_=[v/2 for v in sz]
        faces=[((1,0,0),[(1,-1,-1),(1,-1,1),(1,1,1),(1,1,-1)]),((-1,0,0),[(-1,-1,1),(-1,-1,-1),(-1,1,-1),(-1,1,1)]),
               ((0,1,0),[(-1,1,-1),(1,1,-1),(1,1,1),(-1,1,1)]),((0,-1,0),[(-1,-1,1),(1,-1,1),(1,-1,-1),(-1,-1,-1)]),
               ((0,0,1),[(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]),((0,0,-1),[(1,-1,-1),(-1,-1,-1),(-1,1,-1),(1,1,-1)])]
        P=[];N=[];UV=[];C=[];T=[]
        for nrm,vs in faces:
            b=len(P)
            for (x,y,z) in vs:
                P.append((cx+x*sx,cy+y*sy,cz+z*sz_)); N.append(nrm); C.append(col)
                if nrm[0]!=0: UV.append(((cz+z*sz_)*uv,(cy+y*sy)*uv))
                elif nrm[1]!=0: UV.append(((cx+x*sx)*uv,(cz+z*sz_)*uv))
                else: UV.append(((cx+x*sx)*uv,(cy+y*sy)*uv))
            T+=[(b,b+1,b+2),(b,b+2,b+3)]
        s.add(key,P,N,C,UV,T)
    def lathe(s,key,c,prof,sides=16,col=(1,1,1,1),uscale=1.0,vscale=1.0):
        cx,cy,cz=c; P=[];N=[];UV=[];C=[];T=[]
        pr=np.asarray(prof,float); m=len(pr)
        for i,(r,y) in enumerate(pr):
            if i==0: dr,dy=pr[1][0]-r,pr[1][1]-y
            elif i==m-1: dr,dy=r-pr[i-1][0],y-pr[i-1][1]
            else: dr,dy=pr[i+1][0]-pr[i-1][0],pr[i+1][1]-pr[i-1][1]
            nr,ny=dy,-dr; l=math.hypot(nr,ny)+1e-9; nr/=l; ny/=l
            for k in range(sides+1):
                a=2*math.pi*k/sides
                P.append((cx+math.cos(a)*r,cy+y,cz+math.sin(a)*r)); N.append((math.cos(a)*nr,ny,math.sin(a)*nr)); C.append(col); UV.append((k/sides*uscale,y*vscale))
        for i in range(m-1):
            for k in range(sides):
                a=i*(sides+1)+k; T+=[(a,a+1,a+sides+1),(a+1,a+sides+2,a+sides+1)]
        s.add(key,P,N,C,UV,T)
    def merge(s,o,t=(0,0,0),sc=1.0,ry=0.0,tint=None):
        cs,sn=math.cos(ry),math.sin(ry)
        for key,P,N,C,UV,T in o.arrays():
            P=P*sc; Pn=np.stack([P[:,0]*cs+P[:,2]*sn,P[:,1],-P[:,0]*sn+P[:,2]*cs],1)+np.asarray(t)
            Nn=np.stack([N[:,0]*cs+N[:,2]*sn,N[:,1],-N[:,0]*sn+N[:,2]*cs],1)
            s.add(key,Pn,Nn,C,UV,T)
    def arrays(s):
        out=[]
        for key,a in s.parts.items():
            P=np.vstack(a['P']);N=np.vstack(a['N']);C=np.vstack(a['C']);UV=np.vstack(a['UV']);T=np.vstack(a['T'])
            out.append((key,P,N,C,UV,T))
        return out
    def stats(s): return sum(len(a[1]) for a in s.arrays()),sum(len(a[5]) for a in s.arrays())
    def write(s,fn=None):
        fn=fn or OUT+s.name+'.bin'; arr=s.arrays(); tex=sorted({k[0] for k,*_ in arr})
        b=bytearray(b'FLR1'); b+=struct.pack('<2I',len(tex),len(arr))
        for t in tex: e=t.encode(); b+=struct.pack('<B',len(e))+e
        for (t,mat,cut),P,N,C,UV,T in arr:
            assert len(P)<65536,(s.name,len(P))
            b+=struct.pack('<BhB',mat,tex.index(t),cut)+struct.pack('<2I',len(P),len(T)*3)
            cb=(np.clip(np.asarray(C,float),0,1)*255).astype(np.uint8)
            if cb.shape[1]==3: cb=np.hstack([cb,np.full((len(cb),1),255,np.uint8)])
            for i in range(len(P)):
                b+=struct.pack('<6f',*P[i],*N[i])+cb[i].tobytes()+struct.pack('<2f',*UV[i])
            b+=np.asarray(T,'<u2').tobytes()
        open(fn,'wb').write(b)

def tex_cache(name):
    return np.asarray(Image.open(OUT+'tex/'+name).convert('RGBA'))

def preview(asset,fn,views=('front','side'),size=(480,520),span=None,ground=True):
    arr=asset.arrays(); allP=np.vstack([a[1] for a in arr]); lo=allP.min(0); hi=allP.max(0); c=(lo+hi)/2
    ext=span or max(hi[1]-lo[1],hi[0]-lo[0],hi[2]-lo[2])*1.1
    W,H=size; sc=H/ext; imgs=[]
    L=np.array([0.45,1.0,0.65]); L/=np.linalg.norm(L)
    for view in views:
        img=np.zeros((H,W,3),np.float32); 
        yy=np.linspace(0,1,H)[:,None,None]; img[:]=np.array([170,215,240])*(1-yy)+np.array([225,240,250])*yy
        zb=np.full((H,W),-1e9)
        for (t,mat,cut),P,N,C,UV,T in arr:
            tx=tex_cache(t) if os.path.exists(OUT+'tex/'+t) else None
            if view=='front': X=W/2+(P[:,0]-c[0])*sc; Z=P[:,2]
            elif view=='side': X=W/2+(P[:,2]-c[2])*sc; Z=P[:,0]
            else: X=W/2+(P[:,0]-c[0])*sc; Z=P[:,1]
            Y=H*0.5-(P[:,1]-c[1])*sc if view!='top' else H*0.5-(P[:,2]-c[2])*sc
            if view=='side': pass
            for tri in T:
                xs=X[tri];ys=Y[tri];zs=Z[tri]
                x0,x1=int(max(0,xs.min())),int(min(W-1,xs.max()+1)); y0,y1=int(max(0,ys.min())),int(min(H-1,ys.max()+1))
                if x1<x0 or y1<y0: continue
                gx,gy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1))
                d=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
                if abs(d)<1e-9: continue
                a=((ys[1]-ys[2])*(gx-xs[2])+(xs[2]-xs[1])*(gy-ys[2]))/d; b=((ys[2]-ys[0])*(gx-xs[2])+(xs[0]-xs[2])*(gy-ys[2]))/d; cc=1-a-b
                m=(a>=-1e-3)&(b>=-1e-3)&(cc>=-1e-3)
                if not m.any(): continue
                z=a*zs[0]+b*zs[1]+cc*zs[2]; m&=z>zb[y0:y1+1,x0:x1+1]
                nn=a[...,None]*N[tri[0]]+b[...,None]*N[tri[1]]+cc[...,None]*N[tri[2]]; nl=np.linalg.norm(nn,axis=-1); nn=nn/np.maximum(nl[...,None],1e-9)
                diff=np.clip((nn*L).sum(-1),0,1); amb=0.42+0.18*(0.5+0.5*nn[...,1]); light=np.where(nl<0.1,1.0,amb+0.62*diff)
                vc=a[...,None]*C[tri[0]][:3]+b[...,None]*C[tri[1]][:3]+cc[...,None]*C[tri[2]][:3]
                if tx is not None:
                    u=a*UV[tri[0],0]+b*UV[tri[1],0]+cc*UV[tri[2],0]; v=a*UV[tri[0],1]+b*UV[tri[1],1]+cc*UV[tri[2],1]
                    th,tw=tx.shape[:2]; ix=(u*tw).astype(int)%tw if not cut else np.clip((u*tw).astype(int),0,tw-1); iy=(v*th).astype(int)%th if not cut else np.clip((v*th).astype(int),0,th-1)
                    tv=tx[iy,ix]; col=tv[...,:3].astype(float)
                    if cut: m=m&(tv[...,3]>127)
                else: col=np.full(m.shape+(3,),200.0)
                col=col*vc*light[...,None]
                sub=img[y0:y1+1,x0:x1+1]; sub[m]=col[m]; zb[y0:y1+1,x0:x1+1][m]=z[m]
        imgs.append(np.clip(img,0,255).astype(np.uint8))
    Image.fromarray(np.hstack(imgs)).save(fn)
