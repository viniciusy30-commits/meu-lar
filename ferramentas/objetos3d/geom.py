"""Primitivas de modelagem (malha com chanfro, torno, tubo, esfera...) que escrevem numa Geo (glb_lib)."""
import numpy as np, math
from glb_lib import Geo as _Geo

def V(*a): return np.array(a, float)
def nrm(v): return v / (np.linalg.norm(v) + 1e-9)


class Geo(_Geo):
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



import glb_lib as _gl
_gl.GEO_CLASS = Geo


def add_xf(dst, src, R=None, t=(0, 0, 0)):
    """copia a geometria de src para dst aplicando rotação R (3x3) e translação t."""
    R = np.eye(3) if R is None else np.asarray(R, float); t = np.asarray(t, float)
    for key, P, N, C, UV, T in src.arrays():
        dst.add(key, P @ R.T + t, N @ R.T, C, UV, T)


def rot_x(a):
    c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def rect_path(cx, cy, cz, w, d, rad, n=6):
    pts = []
    for (sx, sz, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ccx = cx + sx * (w / 2 - rad); ccz = cz + sz * (d / 2 - rad)
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append(V(ccx + rad * math.cos(a), cy, ccz + rad * math.sin(a)))
    pts.append(pts[0]); return pts


def piping(g, key, cx, cy, cz, w, d, r, col, rad=0.03):
    pts = rect_path(cx, cy, cz, w, d, rad); g.tube(key, pts, [r] * len(pts), sides=6, col=lambda p, t: tuple(col) + (1,), vscale=4.0)


def disc(g, key, c, r, height=lambda rr: 0.0, rings=6, seg=28, uv=3.0, col=(1, 1, 1)):
    """disco (tampa, terra) com relevo radial height(r/raio)."""
    cx, cy, cz = c; P = []; N = []; UV = []; C = []; T = []
    for i in range(rings + 1):
        rr = r * i / rings
        for j in range(seg + 1):
            a = 2 * math.pi * j / seg; x = cx + rr * math.cos(a); z = cz + rr * math.sin(a)
            P.append((x, cy + height(rr / r), z)); UV.append((x * uv, z * uv)); C.append(tuple(col) + (1,))
    P = np.array(P); n = np.zeros_like(P)
    for i in range(rings):
        for j in range(seg):
            a = i * (seg + 1) + j; b = a + 1; c2 = a + seg + 1; d = c2 + 1
            if i > 0: T.append((a, b, c2))
            T.append((b, d, c2))
    T = np.array(T)
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    for k in range(3): np.add.at(n, T[:, k], fn)
    n[:, 1] = np.where(np.abs(n[:, 1]) < 1e-12, 1e-6, n[:, 1])
    n /= np.linalg.norm(n, axis=1, keepdims=True); n *= np.sign(n[:, 1:2])
    g.add(key, P, n, C, UV, T)


def grid_normals(P, T):
    n = np.zeros_like(P)
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    for k in range(3): np.add.at(n, T[:, k], fn)
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)
