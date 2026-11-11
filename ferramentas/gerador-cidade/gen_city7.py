import collections
from terrain4 import *
from scipy.ndimage import gaussian_filter, map_coordinates
def catmull(pts,step=6.0):
    P=[np.array(p,float) for p in pts]; P=[P[0]*2-P[1]]+P+[P[-1]*2-P[-2]]
    out=[]
    for i in range(1,len(P)-2):
        p0,p1,p2,p3=P[i-1],P[i],P[i+1],P[i+2]
        n=max(2,int(np.hypot(*(p2-p1))/step))
        for t in np.linspace(0,1,n,endpoint=False):
            t2,t3=t*t,t*t*t
            out.append(0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t2+(-p0+3*p1-3*p2+p3)*t3))
    out.append(P[-2]);return np.array(out)
def dens(P,step=10.0):
    P=np.asarray(P,float);out=[P[0]]
    for a,b in zip(P[:-1],P[1:]):
        L=float(np.hypot(*(b-a)));n=max(1,int(math.ceil(L/step)))
        for k in range(1,n+1): out.append(a+(b-a)*k/n)
    return np.array(out)
def wdist(x,z):
    if not(0<=x<=WX and 0<=z<=WZ): return -1.0
    return float(map_coordinates(water_d,[[z/G],[x/G]],order=1,mode='nearest')[0])
def coast_z(x):
    col=np.where(sea[:,min(int(x/G),NX-1)])[0]; return float(col[0]*G) if len(col) else WZ
DISTRICTS={'Centro':(600,740,1600,1500),'Parque das Flores':(90,1220,560,1660),'Vila Esperança':(90,1780,560,2080),
 'Jardim Central':(2240,430,2960,960),'Recanto do Sul':(1960,1560,2700,1920),'Parque Norte':(1120,230,1600,700)}
def rect_mask(r,feather=70):
    x0,z0,x1,z1=r
    dx=np.maximum(np.maximum(x0-X,X-x1),0);dz=np.maximum(np.maximum(z0-Z,Z-z1),0)
    d=np.hypot(dx,dz); t=np.clip(1-d/feather,0,1); return t*t*(3-2*t)
def ell_mask(cx,cz,rx,rz,feather=80):
    d=np.hypot((X-cx)/rx,(Z-cz)/rz); t=np.clip(1-(d-1)*np.hypot(rx,rz)/feather,0,1); return t*t*(3-2*t)
Tbig=gaussian_filter(terr,10.0)
mflat=np.zeros(terr.shape)
for nm,r in DISTRICTS.items(): mflat=np.maximum(mflat,rect_mask(r))
mflat=np.maximum(mflat,ell_mask(2850,1400,330,300))
Tfl=terr*(1-0.92*mflat)+Tbig*0.92*mflat
Tfl=np.where(water,terr,np.maximum(Tfl,0.9))
Tfl_s=gaussian_filter(Tfl,2.0)
def Th(x,z): return float(map_coordinates(Tfl_s,[[z/G],[x/G]],order=1,mode='nearest')[0])
def plen(P): return float(np.hypot(*np.diff(P,axis=0).T).sum())
def cum(P): return np.r_[0,np.cumsum(np.hypot(*np.diff(P,axis=0).T))]
import struct, pickle
# =====================================================================================
# definição das ruas v5 (cls: 0 rodovia, 1 avenida, 2 coletora, 3 local)
# rede orgânica: arterias curvas + bairros em grade irregular + tecido Voronoi de densidade variável
# =====================================================================================
from scipy.spatial import Voronoi, cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra, connected_components
rngN=np.random.default_rng(11)
def _wf(s,a):
    r=gaussian_filter(rngN.standard_normal(X.shape),s/G,mode='wrap'); return a*r/r.std()
WARPX=_wf(320,42)+_wf(120,9); WARPZ=_wf(320,42)+_wf(120,9)
def warp(P):
    P=np.asarray(P,float); sh=P.shape[:-1]
    ix=np.clip(P[...,0]/G,0,NX-1.001).ravel(); iz=np.clip(P[...,1]/G,0,NZ-1.001).ravel()
    dx=map_coordinates(WARPX,[iz,ix],order=1).reshape(sh); dz=map_coordinates(WARPZ,[iz,ix],order=1).reshape(sh)
    return P+np.stack([dx,dz],-1)
def wd_v(P):
    P=np.asarray(P,float); ix=np.clip(P[:,0]/G,0,NX-1.001); iz=np.clip(P[:,1]/G,0,NZ-1.001)
    d=map_coordinates(water_d,[iz,ix],order=1,mode='nearest')
    out=(P[:,0]<0)|(P[:,0]>WX)|(P[:,1]<0)|(P[:,1]>WZ)
    return np.where(out,-1.0,d)
SLP=np.hypot(*np.gradient(Tfl_s,G))
def slp_at(x,z): return float(map_coordinates(SLP,[[z/G],[x/G]],order=1,mode='nearest')[0])

WIDTH={0:20,1:18,2:12,3:9}
defs=[]
def R(name,cls,pts,w=None,elev=False,cul=False,bridge=False,snap=60.0,hill=False,smooth=False,bairro=None,wp=True):
    P=np.array(pts,float)
    if smooth: P=catmull([tuple(p) for p in P],8.0)
    if wp: P=warp(dens(P,25.0))
    defs.append(dict(name=name,cls=cls,w=(w if w else WIDTH[cls]),pts=P,elev=elev,cul=cul,bridge=bridge,snap=snap,hill=hill,bairro=bairro))

HUBS0={'Praça Central':(1100,1120,32),'Rot. Oeste':(500,1120,28),'Rot. Leste':(1960,1085,28),'Rot. do Porto':(1100,1700,28),
      'Rot. Jardim':(2600,790,28),'Rot. Recanto':(2300,1740,28),'Praça da Colina':(500,640,26),'Rot. Norte':(1330,470,26)}
HUBS={}
for k,(hx,hz,hr) in HUBS0.items():
    q=warp(np.array([hx,hz]));HUBS[k]=(float(q[0]),float(q[1]),hr)
    if wdist(*q)<hr+30: print('AVISO hub perto da água:',k,round(wdist(*q)))
# ---- rodovia/elevado: atravessa a cidade de leste a oeste
R('Rodovia Oeste',0,[(-60,1195),(150,1175),(330,1148),(500,1120)],smooth=True,elev=True)
R('Elevado Paulista',0,[(500,1120),(1560,1120),(1760,1105),(1960,1085)],smooth=True,elev=True)
R('Rodovia Leste',0,[(1960,1085),(2300,1052),(2700,1026),(3260,1046)],smooth=True,elev=True)
# ---- avenidas: ligam os bairros, os centros e as rotatórias
R('Av. Central',1,[(1100,1700),(1100,1120),(1100,900)])
R('Viaduto da Av. Central',1,[(1100,900),(1100,680)],elev=True)
R('Av. Central Norte',1,[(1100,680),(1200,560),(1330,470)],smooth=True)
R('Av. Leste',1,[(1330,470),(1540,640),(1540,1120),(1450,1350)],smooth=True)
R('Av. Topo',1,[(1330,470),(1600,300),(1780,260),(1950,250),(2300,330),(2480,385),(2575,470),(2600,570)],smooth=True,bridge=True)
R('Av. Norte',1,[(-60,830),(500,800),(1100,790),(1700,770),(2100,790),(2600,790),(3260,800)],bridge=True,smooth=True)
R('Av. Oeste',1,[(660,300),(660,1120),(660,1738)])
R('Av. Noroeste',2,[(500,640),(440,480),(500,330),(660,300)],smooth=True,hill=True)
R('Anel Oeste',2,[(500,640),(500,1120),(500,1500),(420,1900)],smooth=True)
R('Av. Sul',1,[(500,1450),(1100,1450),(1450,1350),(1700,1440),(1960,1560)],bridge=True,smooth=True)
R('Av. do Porto',1,[(-60,1900),(420,1900),(700,1720),(1100,1700)],smooth=True)
R('Av. do Porto Leste',1,[(1100,1700),(1400,1560),(1700,1440)],smooth=True)
R('Av. Lagoa',2,[(1960,790),(1960,1085),(1960,1560)])
R('Av. Jardim',1,[(2600,570),(2600,790),(2600,1100)],smooth=True)
R('Av. Recanto',1,[(1960,1560),(2100,1700),(2300,1740),(2600,1740),(2790,1610),(2860,1490),(2850,1400),(2740,1280),(2600,1100)],smooth=True)
nart=len(defs)

# ---- arterias densas
APt=[];ATg=[];A0=[];AId=[]
for di,d in enumerate(defs):
    P=dens(d['pts'],10.0)
    T=np.vstack([P[1:]-P[:-1],P[-1:]-P[-2:-1]]);T/=np.maximum(np.hypot(*T.T),1e-9)[:,None]
    for p,t in zip(P,T): APt.append(p);ATg.append(t);A0.append(1 if (d['cls']==0 or d['elev']) else 0);AId.append(di)
APt=np.array(APt);ATg=np.array(ATg);A0=np.array(A0);AId=np.array(AId);Atree=cKDTree(APt)
def proj_poly(P,q):
    a=P[:-1];b=P[1:];v=b-a;L2=(v**2).sum(1)+1e-12
    t=np.clip(((q-a)*v).sum(1)/L2,0,1);pr=a+v*t[:,None];d=np.hypot(*(pr-q).T);k=int(d.argmin());return float(d[k]),pr[k]
SNAPD=48.0
HX=np.array([[h[0],h[1]] for h in HUBS.values()]);HR=np.array([h[2] for h in HUBS.values()]);Htree=cKDTree(HX)

ZONES=[
 dict(nm='Centro',c=(1100,1120),hu=440,hv=330,sx=[95,110,125],sz=[95,110,125],every=4,w=9,hill=False,sd=1,drop=0.06),
 dict(nm='Parque das Flores',c=(295,1420),hu=205,hv=240,sx=[100,115,130],sz=[100,115,130],every=3,w=9,hill=False,sd=2,drop=0.06),
 dict(nm='Vila Esperança',c=(295,1910),hu=205,hv=170,sx=[95,110,125],sz=[95,110,125],every=3,w=8.5,hill=False,sd=3,drop=0.06),
 dict(nm='Alto da Colina',c=(375,545),hu=245,hv=215,sx=[140,165],sz=[120,150],every=99,w=8.5,hill=True,sd=7,drop=0.05),
 dict(nm='Oeste Alto',c=(300,960),hu=180,hv=135,sx=[100,120],sz=[100,120],every=99,w=8.5,hill=False,sd=8,drop=0.05),
 dict(nm='Bairro Norte',c=(1260,540),hu=260,hv=200,sx=[130,150],sz=[120,140],every=99,w=8.5,hill=True,sd=9,drop=0.05),
 dict(nm='Jardim Central',c=(2680,695),hu=430,hv=265,sx=[95,110,125],sz=[95,110,125],every=4,w=9,hill=False,sd=4,drop=0.06),
 dict(nm='Recanto do Sul',c=(2330,1740),hu=370,hv=180,sx=[90,105,120],sz=[90,105,120],every=4,w=9,hill=False,sd=5,drop=0.06),
 dict(nm='Distrito Leste',c=(2900,1350),hu=250,hv=250,sx=[95,110,125],sz=[95,110,125],every=4,w=9,hill=False,sd=6,drop=0.06),
 dict(nm='Beira-Rio',c=(1760,1280),hu=190,hv=150,sx=[95,110],sz=[95,110],every=99,w=8.5,hill=False,sd=11,drop=0.05),
 dict(nm='Morro Alto',c=(850,560),hu=150,hv=230,sx=[130,150],sz=[130,150],every=99,w=8.5,hill=True,sd=12,drop=0.05),
 dict(nm='Porto',c=(1050,1575),hu=350,hv=115,sx=[90,105,120],sz=[90,105],every=99,w=8.5,hill=False,sd=10,drop=0.04),
]
VV=[];VS=[];EE=[]
def addv(p,sid=-1): VV.append((float(p[0]),float(p[1])));VS.append(sid);return len(VV)-1
for z in ZONES:
    r=np.random.default_rng(z['sd']*101)
    def cumul(half,sp):
        t=[-half]
        while t[-1]+min(sp)*0.8<half: t.append(t[-1]+float(r.choice(sp)))
        t.append(half);return np.array(t)
    us=cumul(z['hu'],z['sx']);vs=cumul(z['hv'],z['sz']);nu,nv=len(us),len(vs)
    idx=-np.ones((nu,nv),int);jt=min(z['sx'])*0.05
    for i in range(nu):
        for j in range(nv):
            u=us[i]+(r.normal(0,jt) if 0<i<nu-1 else 0);v=vs[j]+(r.normal(0,jt) if 0<j<nv-1 else 0)
            x=z['c'][0]+u;zz=z['c'][1]+v
            p=warp(np.array([x,zz]))
            if wdist(p[0],p[1])<18 or not(20<p[0]<WX-20 and 20<p[1]<WZ-20): continue
            sid=-1
            best=None
            for di in range(nart):
                if defs[di]['elev']: continue
                d,q=proj_poly(defs[di]['pts'],p)
                if d<SNAPD and (best is None or d<best[0]): best=(d,q,di)
            if best: p=best[1];sid=best[2]
            idx[i,j]=addv(p,sid)
    for i in range(nu):
        for j in range(nv):
            a0=idx[i,j]
            if a0<0: continue
            if i+1<nu and idx[i+1,j]>=0:
                col=(j%z['every']==0) and 0<j<nv-1
                if col or r.random()>z['drop']: EE.append(dict(a=a0,b=idx[i+1,j],cls=2 if col else 3,tag='g:'+z['nm'],cul=False))
            if j+1<nv and idx[i,j+1]>=0:
                col=(i%z['every']==0) and 0<i<nu-1
                if col or r.random()>z['drop']: EE.append(dict(a=a0,b=idx[i,j+1],cls=2 if col else 3,tag='g:'+z['nm'],cul=False))
print('grade: vértices',len(VV),'arestas',len(EE))
VV=np.array(VV);VS=np.array(VS)
def samples(p,q,step=14.0):
    L=float(np.hypot(*(q-p)));n=max(2,int(L/step)+1);t=np.linspace(0,1,n)[:,None];return p+(q-p)*t
keepE=[];RS=collections.Counter()
for e in EE:
    p=VV[e['a']];q=VV[e['b']]
    if np.hypot(*(q-p))<3: RS['curta']+=1;continue
    if VS[e['a']]>=0 and VS[e['a']]==VS[e['b']]: RS['mesma_av']+=1;continue
    S=samples(p,q)
    if (S[:,0].min()<20)|(S[:,0].max()>WX-20)|(S[:,1].min()<20)|(S[:,1].max()>WZ-20): RS['borda']+=1;continue
    if wd_v(S).min()<14: RS['agua']+=1;continue
    dh,ih=Htree.query(S)
    if (dh<HR[ih]+16).any(): RS['hub']+=1;continue
    d,ia=Atree.query(S);bad=False
    dirv=(q-p)/max(np.hypot(*(q-p)),1e-9)
    for dd,ii in zip(d,ia):
        if A0[ii] and dd<26: bad=True;break
        if dd<20 and abs(float(dirv@ATg[ii]))>0.80 and not(dd<3): bad=True;break
    if bad: RS['arterial']+=1;continue
    keepE.append(e)
EE=keepE;print('após regras:',len(EE),dict(RS))
used=sorted(set([e['a'] for e in EE]+[e['b'] for e in EE]))
mp={v:i for i,v in enumerate(used)};P0=VV[used];n0=len(used)
par=list(range(n0))
def fnd(x):
    while par[x]!=x: par[x]=par[par[x]];x=par[x]
    return x
for i,j in cKDTree(P0).query_pairs(38.0):
    a,b=fnd(i),fnd(j)
    if a!=b: par[a]=b
cl=collections.defaultdict(list)
for i in range(n0): cl[fnd(i)].append(i)
rid={r:k for k,r in enumerate(cl)};PV=np.array([P0[v].mean(0) for r,v in cl.items()])
seen={};E2=[]
for e in EE:
    a=rid[fnd(mp[e['a']])];b=rid[fnd(mp[e['b']])]
    if a==b: continue
    k=(min(a,b),max(a,b))
    if k in seen:
        if e['cls']<E2[seen[k]]['cls']: E2[seen[k]]['cls']=e['cls']
        continue
    seen[k]=len(E2);E2.append(dict(a=a,b=b,cls=e['cls'],tag=e['tag'],cul=False))
EE=E2;print('após fusão: vértices',len(PV),'arestas',len(EE))
def ECE(e): return float(np.hypot(*(PV[e['a']]-PV[e['b']])))
def prune_dead():
    while True:
        deg=collections.Counter()
        for e in EE: deg[e['a']]+=1;deg[e['b']]+=1
        # um ponto está "preso" numa avenida se estiver a <3 m dela
        def onart(v):
            d,_=Atree.query(PV[v]);return d<4.0
        rem=[i for i,e in enumerate(EE) if (deg[e['a']]==1 and not onart(e['a'])) or (deg[e['b']]==1 and not onart(e['b']))]
        if not rem: break
        rs=set(rem);EE[:]=[e for i,e in enumerate(EE) if i not in rs]
prune_dead()
print('após poda de becos:',len(EE))
# ângulos agudos: tira a rua de quadra que sai muito rente a outra rua no mesmo cruzamento
def acute_pass():
    inc=collections.defaultdict(list)
    for i,e in enumerate(EE):
        inc[e['a']].append((i,PV[e['b']]-PV[e['a']]));inc[e['b']].append((i,PV[e['a']]-PV[e['b']]))
    rem=set()
    for v,L in inc.items():
        dirs=[(i,d/max(np.hypot(*d),1e-9)) for i,d in L]
        for x in range(len(dirs)):
            for y in range(x+1,len(dirs)):
                if abs(float(dirs[x][1]@dirs[y][1]))>0.0 and float(dirs[x][1]@dirs[y][1])>0.70:   # <~45 graus
                    i,j=dirs[x][0],dirs[y][0]
                    rem.add(i if ECE(EE[i])<ECE(EE[j]) else j)
        d,ia=Atree.query(PV[v])
        if d<4.0:
            for i,dv in dirs:
                if abs(float(dv@ATg[ia]))>0.72 and EE[i]['tag'].startswith('g:'): rem.add(i)
    EE[:]=[e for i,e in enumerate(EE) if i not in rem]
    return len(rem)
for _ in range(4):
    n_=acute_pass();prune_dead()
    if not n_: break
print('após ângulos:',len(EE))
def short_pass():
    deg=collections.Counter()
    for e in EE: deg[e['a']]+=1;deg[e['b']]+=1
    rem=set()
    for i,e in enumerate(EE):
        if ECE(e)<46 and deg[e['a']]>=3 and deg[e['b']]>=3 and e['tag'].startswith('g:'): rem.add(i)
    EE[:]=[e for i,e in enumerate(EE) if i not in rem]
    return len(rem)
for _ in range(3):
    n_=short_pass();prune_dead()
    if not n_: break
print('após trechos curtos:',len(EE))

def uloop_pass():
    deg=collections.Counter()
    for e in EE: deg[e['a']]+=1;deg[e['b']]+=1
    ad=collections.defaultdict(list)
    for i,e in enumerate(EE): ad[e['a']].append((e['b'],i));ad[e['b']].append((e['a'],i))
    seen=set();rem=set()
    onA=lambda q:Atree.query(PV[q])[0]<4.0
    for v in list(ad):
        if deg[v]==2 and not onA(v): continue
        for (w,ei) in ad[v]:
            if ei in seen: continue
            path=[v,w];es=[ei];seen.add(ei);cur=w;pe=ei
            while deg[cur]==2 and not onA(cur):
                (n1,e1),(n2,e2)=ad[cur];nxt,ne=(n1,e1) if e1!=pe else (n2,e2)
                if ne in seen: break
                seen.add(ne);es.append(ne);path.append(nxt);pe=ne;cur=nxt
            L=sum(ECE(EE[k]) for k in es)
            da,ia_=Atree.query(PV[path[0]]);db,ib_=Atree.query(PV[path[-1]])
            dd_=np.hypot(*(PV[path[0]]-PV[path[-1]]))
            if EE[es[0]]['tag'].startswith('g:') and ((da<4 and db<4 and L<640 and dd_<0.62*L) or (L<520 and dd_<0.45*L)):
                rem.update(es)
    EE[:]=[e for i,e in enumerate(EE) if i not in rem]
    return len(rem)
for _ in range(3):
    n_=uloop_pass();prune_dead()
    if not n_: break
print('após laços em U:',len(EE))
# componentes que não tocam nenhuma avenida saem
nn=len(PV);ar=np.array([e['a'] for e in EE]);br=np.array([e['b'] for e in EE])
nc,lb=connected_components(coo_matrix((np.ones(len(EE)),(ar,br)),shape=(nn,nn)),directed=False)
tou=set()
for v in set(ar)|set(br):
    if Atree.query(PV[v])[0]<6.0: tou.add(lb[v])
EE=[e for e in EE if lb[e['a']] in tou]
# correntes
adj=collections.defaultdict(list)
for i,e in enumerate(EE): adj[e['a']].append((e['b'],i));adj[e['b']].append((e['a'],i))
def brk(v):
    nb=adj[v]
    if len(nb)!=2: return True
    a,b=EE[nb[0][1]],EE[nb[1][1]]
    return a['cls']!=b['cls'] or a['tag']!=b['tag'] or Atree.query(PV[v])[0]<4.0
usedE=set();chains=[]
for v in list(adj):
    if not brk(v): continue
    for (w,ei) in adj[v]:
        if ei in usedE: continue
        path=[v,w];usedE.add(ei);cur=w;pe=ei
        while not brk(cur):
            (n1,e1),(n2,e2)=adj[cur];nxt,ne=(n1,e1) if e1!=pe else (n2,e2)
            if ne in usedE: break
            usedE.add(ne);path.append(nxt);pe=ne;cur=nxt
        chains.append((path,EE[ei]))
PREF={'Centro':'Rua','Parque das Flores':'Alameda','Vila Esperança':'Rua','Alto da Colina':'Terraço','Oeste Alto':'Rua','Bairro Norte':'Alameda','Jardim Central':'Alameda','Recanto do Sul':'Travessa','Distrito Leste':'Rua','Porto':'Rua','Beira-Rio':'Rua','Morro Alto':'Terraço'}
ZW={z['nm']:z for z in ZONES};nm_=collections.Counter();rj=np.random.default_rng(9)
for path,e in chains:
    pts=np.array([PV[k] for k in path]);z=ZW[e['tag'][2:]]
    w=12 if e['cls']==2 else z['w']
    pf=PREF[z['nm']];nm_[pf]+=1
    R(f"{pf} {nm_[pf]}",e['cls'],pts,w=w,cul=False,hill=bool(z['hill']),smooth=(len(pts)>2),snap=30.0,wp=False,bairro=z['nm'])
print('correntes:',len(chains),'defs totais',len(defs))

# =====================================================================================
# recorte em terra, cruzamentos, nós e arestas
# =====================================================================================
roads=defs
def seg_inter(P,Q):
    a=P[:-1][:,None,:];b=P[1:][:,None,:];c=Q[:-1][None,:,:];d=Q[1:][None,:,:]
    r=b-a;s=d-c;den=r[...,0]*s[...,1]-r[...,1]*s[...,0]
    qp=c-a
    with np.errstate(divide='ignore',invalid='ignore'):
        t=(qp[...,0]*s[...,1]-qp[...,1]*s[...,0])/den
        u=(qp[...,0]*r[...,1]-qp[...,1]*r[...,0])/den
    eps=1e-7
    m=(np.abs(den)>1e-9)&(t>=-eps)&(t<=1+eps)&(u>=-eps)&(u<=1+eps)
    out=[]
    for i,j in np.argwhere(m): out.append((a[i,0]+r[i,0]*t[i,j],i,j))
    return out
def bbox(P,pad=0): return (P[:,0].min()-pad,P[:,1].min()-pad,P[:,0].max()+pad,P[:,1].max()+pad)
def bb_hit(A,B): return not(A[2]<B[0] or B[2]<A[0] or A[3]<B[1] or B[3]<A[1])
nodes=[];NG={}
def get_node(p,tol=5.0):
    kx,kz=int(p[0]//20),int(p[1]//20)
    for dx in(-1,0,1):
        for dz in(-1,0,1):
            for k in NG.get((kx+dx,kz+dz),()):
                q=nodes[k]
                if math.hypot(p[0]-q[0],p[1]-q[1])<tol: return k
    nodes.append((float(p[0]),float(p[1])));NG.setdefault((kx,kz),[]).append(len(nodes)-1);return len(nodes)-1
def nearest_on(P,q):
    a=P[:-1];b=P[1:];v=b-a;L2=(v**2).sum(1)+1e-12
    t=np.clip(((q-a)*v).sum(1)/L2,0,1);pr=a+v*t[:,None];d=np.hypot(*(pr-q).T);k=int(d.argmin());return float(d[k]),pr[k],k,float(t[k])
BB=[bbox(r['pts'],2) for r in roads]
onroad=[[] for _ in roads]
for i in range(len(roads)):
    for j in range(i+1,len(roads)):
        if roads[i]['elev'] or roads[j]['elev']: continue
        if not bb_hit(BB[i],BB[j]): continue
        for p,_,_ in seg_inter(roads[i]['pts'],roads[j]['pts']):
            k=get_node(p);onroad[i].append(k);onroad[j].append(k)
for i,r in enumerate(roads):
    for end in(0,-1):
        if r['elev']: continue
        if r['cul'] and end==-1: continue
        e=r['pts'][end]
        if any(math.hypot(e[0]-nodes[k][0],e[1]-nodes[k][1])<1.0 for k in onroad[i]): continue
        best=None
        for j,o in enumerate(roads):
            if j==i or o['elev']: continue
            if not bb_hit((e[0]-r['snap'],e[1]-r['snap'],e[0]+r['snap'],e[1]+r['snap']),BB[j]): continue
            d,q,_,_=nearest_on(o['pts'],e)
            if d<r['snap'] and (best is None or d<best[0]): best=(d,q,j)
        if best:
            d,q,j=best
            if d>0.5: r['pts']=np.vstack([r['pts'],q]) if end==-1 else np.vstack([q,r['pts']])
            k=get_node(q);onroad[i].append(k);onroad[best[2]].append(k)
for i,r in enumerate(roads):
    if not r['elev']: continue
    for end in(0,-1):
        e=r['pts'][end];best=None
        for k,q in enumerate(nodes):
            d=math.hypot(e[0]-q[0],e[1]-q[1])
            if d<30 and (best is None or d<best[0]): best=(d,k)
        k=best[1] if best else get_node(e)
        if best and best[0]>0.5: r['pts']=np.vstack([r['pts'],nodes[k]]) if end==-1 else np.vstack([nodes[k],r['pts']])
        onroad[i].append(k)
        for j,o in enumerate(roads):
            if j==i or o['elev']: continue
            d,q,_,_=nearest_on(o['pts'],np.array(nodes[k]))
            if d<3.0: onroad[j].append(k)
print('nós:',len(nodes))
# hubs
hubnode={}
for nm,(hx,hz,hr) in HUBS.items():
    best=None
    for k,q in enumerate(nodes):
        d=math.hypot(hx-q[0],hz-q[1])
        if d<30 and (best is None or d<best[0]): best=(d,k)
    if best is None:
        hit=[i for i,r in enumerate(roads) if not r['elev'] and nearest_on(r['pts'],np.array([hx,hz]))[0]<6.0]
        if hit:
            k=get_node((hx,hz),1.0)
            for i in hit: onroad[i].append(k)
            best=(0.0,k)
    if best is None: print('hub sem nó:',nm);continue
    hubnode[best[1]]=(nm,hr)
edges=[]
for i,r in enumerate(roads):
    P=r['pts'];cs=cum(P);ks=[]
    for k in set(onroad[i]):
        d,q,sg,t=nearest_on(P,np.array(nodes[k]))
        if d<7.0: ks.append((cs[sg]+t*(cs[sg+1]-cs[sg]),k))
    ks.sort()
    if not ks or ks[0][0]>3.0: ks.insert(0,(0.0,get_node(P[0],1.0)))
    if ks[-1][0]<cs[-1]-3.0: ks.append((float(cs[-1]),get_node(P[-1],1.0)))
    ded=[ks[0]]
    for s,k in ks[1:]:
        if k!=ded[-1][1] and s-ded[-1][0]>2.0: ded.append((s,k))
    for (s0,k0),(s1,k1) in zip(ded[:-1],ded[1:]):
        m=(cs>s0+1.5)&(cs<s1-1.5)
        Q=np.vstack([np.array(nodes[k0])[None],P[m],np.array(nodes[k1])[None]])
        Q=dens(Q,10.0)
        edges.append(dict(road=i,a=k0,b=k1,pts=Q,cls=r['cls'],w=r['w'],name=r['name'],elev=r['elev'],hill=r['hill'],cul=r['cul'],bridge=r['bridge'],bairro=r['bairro']))
print('arestas:',len(edges))
deg=collections.Counter()
for e in edges: deg[e['a']]+=1;deg[e['b']]+=1

# ---- auditoria
_de=[(k,nodes[k]) for k in range(len(nodes)) if deg[k]==1 and not(nodes[k][0]<25 or nodes[k][0]>WX-25 or nodes[k][1]<25 or nodes[k][1]>WZ-25)]
print('AUDITORIA pontas soltas (fora da borda):',len(_de),[(round(p[0]),round(p[1])) for k,p in _de][:20])
HUBR={k:hr for k,(nm,hr) in hubnode.items()}
for e in edges:
    for end,k in((0,e['a']),(-1,e['b'])):
        if k not in HUBR: continue
        c=np.array(nodes[k]);hr=HUBR[k];P=e['pts']
        if end==-1: P=P[::-1]
        d=np.hypot(*(P-c).T)
        out=np.where(d>=hr-0.4)[0]
        if len(out)==0: print('aresta curta no hub',e['name']);continue
        i0=out[0]
        if i0==0: continue
        a=P[i0-1];b=P[i0];t=(hr-0.4-d[i0-1])/max(d[i0]-d[i0-1],1e-6);q=a+(b-a)*np.clip(t,0,1)
        # Etapa 180b: a pista começa onde os DOIS cantos da largura ficam dentro do círculo (sem cunha de grama entre pista e rotatória)
        sg_=b-a;sg_=sg_/max(np.hypot(*sg_),1e-9);mm_=np.array([-sg_[1],sg_[0]]);hw_=e['w']/2
        q2=a.copy()
        for tt in np.linspace(1.0,0.0,81):
            pt_=a+(b-a)*tt
            if max(np.hypot(*(pt_+hw_*mm_-c)),np.hypot(*(pt_-hw_*mm_-c)))<=hr-0.25: q2=pt_;break
        P=np.vstack([q2,P[i0:]])
        e['pts']=P if end==0 else P[::-1]

# =====================================================================================
# alturas
# =====================================================================================
SL={0:0.07,1:0.075,2:0.085,3:0.10}
nh=np.array([Th(*q) for q in nodes])
for k,hr in HUBR.items():
    c=nodes[k];vals=[Th(c[0]+hr*math.cos(a),c[1]+hr*math.sin(a)) for a in np.linspace(0,6.28,12,endpoint=False)];nh[k]=float(np.mean(vals))
for e in edges: e['L']=plen(e['pts'])
for it in range(400):
    ch=0.0
    for e in edges:
        if e['elev']: continue
        lim=(0.13 if e['hill'] else SL[e['cls']])*max(e['L'],1.0);dh=nh[e['b']]-nh[e['a']]
        ex=abs(dh)-lim
        if ex>1e-3:
            s=math.copysign(ex*0.5,dh);nh[e['a']]+=s;nh[e['b']]-=s;ch=max(ch,ex)
    if ch<0.01:break
print('relaxamento: iterações',it,'resíduo',round(ch,3))
def gsmooth(a,sig):
    if sig<=0 or len(a)<3: return a
    k=int(sig*3)+1;x=np.arange(-k,k+1);ker=np.exp(-0.5*(x/sig)**2);ker/=ker.sum()
    return np.convolve(np.pad(a,(k,k),mode='edge'),ker,mode='valid')
def land_interp(z,wet):
    idx=np.where(~wet)[0]
    if len(idx)==0: return z
    return np.interp(np.arange(len(z)),idx,z[idx])
def edge_profile(e,ha,hb):
    P=e['pts'];n=len(P);cs=cum(P);L=max(cs[-1],1e-3)
    lin=ha+(hb-ha)*cs/L
    wet=np.array([wdist(*p)<=3.0 for p in P])
    base=np.array([Th(*p) for p in P]);dev=land_interp(base-lin,wet)
    dev=gsmooth(dev,4.0)
    taper=np.clip(np.minimum(cs,L-cs)/35.0,0,1);taper=taper*taper*(3-2*taper)
    z=lin+dev*taper
    lim=(0.13 if e['hill'] else SL[e['cls']])
    d=np.maximum(np.hypot(*np.diff(P,axis=0).T),1e-3)
    for _ in range(500):
        dz=np.diff(z);ex=np.abs(dz)-lim*d;m=ex>1e-4
        if not m.any():break
        adj=np.where(m,np.sign(dz)*ex*0.5,0.0);z[:-1]+=adj;z[1:]-=adj;z[0]=ha;z[-1]=hb
    return z,wet
def sstep(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
for e in edges:
    if e['elev']: continue
    e['z'],e['wet']=edge_profile(e,nh[e['a']],nh[e['b']])
    # cruzamento nivelado: trecho plano junto a cada ponta e transição suave; depois a rampa máxima volta a valer (com as pontas planas fixas)
    cs_=cum(e['pts']);L_=cs_[-1];z0_=e['z'].copy()
    lim_=(0.13 if e['hill'] else SL[e['cls']]);d_=np.maximum(np.hypot(*np.diff(e['pts'],axis=0).T),1e-3)
    best_=None
    for flat_,ramp_ in((7.0,17.0),(5.0,15.0),(3.5,12.0),(2.0,10.0),(0.0,1.0)):
        z_=z0_.copy();pin_=np.zeros(len(z_),bool);pv_=np.zeros(len(z_))
        for end,hn in(('a',nh[e['a']]),('b',nh[e['b']])):
            s_=cs_ if end=='a' else L_-cs_
            w_=sstep((s_-flat_)/ramp_) if flat_>0 else sstep(s_/ramp_)
            z_[:]=hn+(z_-hn)*np.where(s_<flat_+ramp_,w_,1.0)
            if flat_>0:
                m_=s_<=flat_;pin_|=m_;pv_[m_]=hn
        pin_[0]=pin_[-1]=True;pv_[0]=nh[e['a']];pv_[-1]=nh[e['b']]
        for _ in range(1500):
            dz_=np.diff(z_);ex_=np.abs(dz_)-lim_*d_;mk_=ex_>1e-4
            if not mk_.any():break
            adj_=np.where(mk_,np.sign(dz_)*ex_*0.5,0.0);z_[:-1]+=adj_;z_[1:]-=adj_;z_[pin_]=pv_[pin_]
        worst_=float(((np.abs(np.diff(z_))/d_)).max()) if len(d_) else 0.0
        if best_ is None or worst_<best_[0]: best_=(worst_,z_.copy())
        if worst_<=lim_*1.02: break
    e['z']=best_[1]
# elevados
allpts=[];allh=[];allhw=[];allid=[]
for ei,e in enumerate(edges):
    if e['elev']: continue
    for p,z in zip(e['pts'],e['z']): allpts.append(p);allh.append(z);allhw.append(e['w']/2);allid.append(ei)
allpts=np.array(allpts);allh=np.array(allh);allhw=np.array(allhw);allid=np.array(allid)
tree=cKDTree(allpts)
CLEAR=6.4;RAMP=0.060
for ei in sorted(range(len(edges)),key=lambda i:edges[i]['cls']):
    e=edges[ei]
    if not e['elev']: continue
    P=dens(e['pts'],8.0);e['pts']=P;cs=cum(P);L=cs[-1];n=len(P)
    ha=nh[e['a']];hb=nh[e['b']]
    lin=ha+(hb-ha)*cs/L
    wet=np.array([wdist(*p)<=3.0 for p in P])
    base=land_interp(np.array([Th(*p) for p in P])-lin,wet)
    base=lin+gsmooth(base,5.0)*np.clip(np.minimum(cs,L-cs)/40.0,0,1)
    ca=np.array(nodes[e['a']]);cb=np.array(nodes[e['b']])
    req=np.full(n,-1e9)
    for i,p in enumerate(P):
        if np.hypot(*(p-ca))<max(26,HUBR.get(e['a'],0)+14) or np.hypot(*(p-cb))<max(26,HUBR.get(e['b'],0)+14): continue
        for q in tree.query_ball_point(p,e['w']/2+12):
            if allid[q]==ei: continue
            if np.hypot(*(allpts[q]-p))<e['w']/2+allhw[q]+1.0:
                req[i]=max(req[i],allh[q]+CLEAR)
    env=np.full(n,-1e9)
    for i in np.where(req>-1e8)[0]:
        env=np.maximum(env,req[i]-RAMP*np.abs(cs-cs[i]))
    z=np.maximum(base,env)
    z=gsmooth(z,3.0);z=np.maximum(z,env);z=gsmooth(z,1.5);z=np.maximum(z,env)
    z[0]=ha;z[-1]=hb
    for _ in range(300):
        dz=np.diff(z);d=np.maximum(np.hypot(*np.diff(P,axis=0).T),1e-3);ex=np.abs(dz)-0.075*d;m=ex>1e-4
        if not m.any():break
        adj=np.where(m,np.sign(dz)*ex*0.5,0.0);z[:-1]+=adj;z[1:]-=adj;z[0]=ha;z[-1]=hb
    e['z']=z;e['wet']=wet
    up=z-np.array([Th(*p) for p in P])
    print(f"elevado {e['name']}: {L:.0f} m, altura máx {up.max():.1f} m, elevado(>2,2) {int((up>2.2).sum()*8)} m")
# corredor das ruas no terreno
fin=Tfl.copy()
Dc=np.full(X.shape,1e9);Zc=np.zeros(X.shape)
def stamp(P,Z_,hwc):
    for i in range(len(P)-1):
        a=P[i];b=P[i+1];vx=b[0]-a[0];vz=b[1]-a[1];L2=vx*vx+vz*vz
        if L2<1e-6: continue
        ix0=max(int((min(a[0],b[0])-hwc-14)/G),0);ix1=min(int((max(a[0],b[0])+hwc+14)/G)+2,NX)
        iz0=max(int((min(a[1],b[1])-hwc-14)/G),0);iz1=min(int((max(a[1],b[1])+hwc+14)/G)+2,NZ)
        if ix0>=ix1 or iz0>=iz1: continue
        xx=X[iz0:iz1,ix0:ix1];zz=Z[iz0:iz1,ix0:ix1]
        t=np.clip(((xx-a[0])*vx+(zz-a[1])*vz)/L2,0,1)
        d=np.hypot(xx-(a[0]+vx*t),zz-(a[1]+vz*t))-hwc
        yy=Z_[i]+(Z_[i+1]-Z_[i])*t
        sub=Dc[iz0:iz1,ix0:ix1];zs=Zc[iz0:iz1,ix0:ix1];m=d<sub;sub[m]=d[m];zs[m]=yy[m]
def runs_of(mask):
    runs=[];cur=[]
    for i,k in enumerate(mask):
        if k:cur.append(i)
        else:
            if len(cur)>1:runs.append(cur)
            cur=[]
    if len(cur)>1:runs.append(cur)
    return runs
for e in edges:
    P=e['pts'];z=e['z'];hwc=e['w']/2+(1.2 if e['cls']==3 else 1.8)
    if e['elev']:
        up=z-np.array([Th(*p) for p in P])
        for r_ in runs_of(up<2.4): stamp(P[r_],z[r_],hwc)
    else:
        for r_ in runs_of(~e['wet']): stamp(P[r_],z[r_],hwc)
for k,(nm,hr) in hubnode.items():
    c=nodes[k];d=np.hypot(X-c[0],Z-c[1])-hr-2.0;m=d<Dc;Dc[m]=d[m];Zc[m]=nh[k]
for k in range(len(nodes)):
    if deg[k]>=3 and k not in HUBR:
        c=nodes[k];hr=max([e['w'] for e in edges if e['a']==k or e['b']==k])/2+2
        d=np.hypot(X-c[0],Z-c[1])-hr;m=d<Dc;Dc[m]=d[m];Zc[m]=nh[k]
wc=np.clip(1-(Dc-2.0)/10.0,0,1);wc=wc*wc*(3-2*wc)
fin=np.where((wc>0)&(~water),fin*(1-wc)+(Zc-0.22)*wc,fin)

# =====================================================================================
# casas (17 lotes, de frente para ruas E-O)
# =====================================================================================
plots=json.load(open('city2.json'))['plots']
AREA=[76,850,619,439,355,326,357,154,215,254,274,131,208,253,351,363,1002]
BAIRRO=json.load(open('bairros_casas.json'))
FACING=['n','n','s','s','n','n','s','s','n','n','s','s','n','n','s','s','n']
REG={'Vila Esperança':(90,1780,560,2080),'Parque das Flores':(90,1220,560,1660),'Jardim Central':(2240,430,2960,960),
     'Recanto do Sul':(1960,1560,2700,1920),'Alto da Colina':(200,360,560,720)}
houses=[]
for k in range(17):
    p=plots[k];houses.append(dict(k=k,w=p['x1']-p['x0'],d=p['z1']-p['z0'],area=AREA[k],bairro=BAIRRO[k],facing=FACING[k]))
slots=[]
for ei,e in enumerate(edges):
    if e['elev'] or e['cls']==0 or e['wet'].any(): continue
    P=e['pts']
    if len(P)<3: continue
    T=np.vstack([P[1:]-P[:-1],P[-1:]-P[-2:-1]]);T/=np.maximum(np.hypot(*T.T),1e-9)[:,None]
    ew=np.abs(T[:,1])<0.10
    i=0
    while i<len(P):
        if not ew[i]: i+=1;continue
        j=i
        while j+1<len(P) and ew[j+1]: j+=1
        if j>i:
            xs_,zs_=P[i:j+1,0],P[i:j+1,1];o=np.argsort(xs_);xs_,zs_=xs_[o],zs_[o]
            xa,xb=float(xs_[0]),float(xs_[-1])
            if xb-xa>=60:
                for s_ in(1,-1):
                    fc='n' if s_==1 else 's'
                    for x in np.arange(xa+30,xb-30,6.0):
                        slots.append((x,float(np.interp(x,xs_,zs_)),s_,fc,ei,xa,xb))
        i=j+1
print('vagas de lote:',len(slots))
placed=[];REGPAD=0;PROX=16
def pick(h,minsep,reg):
    rad=max(h['w'],h['d'])/2+3
    rx0,rz0,rx1,rz1=REG[h['bairro']];rx0-=REGPAD;rz0-=REGPAD;rx1+=REGPAD;rz1+=REGPAD
    best=None;rr=np.random.default_rng(h['k']+5)
    pool=[s for s in slots if s[3]==h['facing'] and rx0<=s[0]<=rx1 and rz0<=s[1]<=rz1]
    rr.shuffle(pool)
    for x,zr,s,fc,ei,xa,xb in pool[:900]:
        e=edges[ei];hw=e['w']/2+(1.2 if e['cls']==3 else 1.8)
        cz=zr+s*(hw+5.5+h['d']/2);cx=x
        if not(xa+h['w']/2+9<=cx<=xb-h['w']/2-9):continue
        if wdist(cx,cz)<rad+25:continue
        okk=True
        for q in tree.query_ball_point([cx,cz],rad+22):
            if allid[q]!=ei and math.hypot(allpts[q][0]-cx,allpts[q][1]-cz)<rad+allhw[q]+4: okk=False;break
        if not okk:continue
        if any(math.hypot(cx-o['cx'],cz-o['cz'])<minsep for o in placed):continue
        zz=Th(cx,cz)
        if h['k']==16: sc=zz
        elif h['k']==0: sc=-math.hypot(cx-330,cz-1960)*0.02
        elif h['bairro']=='Recanto do Sul': sc=-wdist(cx,cz)*0.03+rr.random()
        else: sc=rr.random()*3
        if best is None or sc>best[0]: best=(sc,cx,cz,s,ei)
    return best
for k in [0,16,1,2,3,4,5,6,7,10,11,13,14,15,8,9,12]:
    h=houses[k];b=None
    for REGPAD,PROX in((0,16),(0,10),(120,12),(240,8),(450,6),(900,5),(2000,4)):
        for ms in(260,200,140,90):
            b=pick(h,ms,None)
            if b:break
        if b:break
    if b is None:print('sem lugar p/ casa',k+1);continue
    sc,cx,cz,s,ei=b
    e=edges[ei];P=e['pts'];i=int(np.argmin(np.hypot(P[:,0]-cx,P[:,1]-cz)))
    h.update(cx=float(cx),cz=float(cz),street=e['name'],level=float(e['z'][i])+0.35,side=s)
    placed.append(h)
print('casas colocadas:',len(placed))
for h in placed:
    x0,x1=h['cx']-h['w']/2-3,h['cx']+h['w']/2+3;z0,z1=h['cz']-h['d']/2-3,h['cz']+h['d']/2+3
    dx=np.maximum(np.maximum(x0-X,X-x1),0);dz=np.maximum(np.maximum(z0-Z,Z-z1),0);d=np.hypot(dx,dz)
    t=np.clip(1-d/10.0,0,1);t=t*t*(3-2*t)
    fin=np.where(~water,fin*(1-t)+(h['level']-0.3)*t,fin)
d_in=distance_transform_edt(water)*G
fin=np.where(water,-0.7-np.minimum(d_in,64)/64*2.3,fin)
fin=np.where((~water)&(fin<0.4),0.4,fin)
fin=gaussian_filter(fin,0.6)
fin=np.where(water,-0.7-np.minimum(d_in,64)/64*2.3,np.maximum(fin,0.4))
# cobertura
_m=np.ones(X.shape,bool)
for e in edges:
    for p in e['pts']: _m[min(int(p[1]/G),NZ-1),min(int(p[0]/G),NX-1)]=False
_d=distance_transform_edt(_m)*G;_land=~water
print('terra a menos de 100 m de uma rua: %.0f%%  menos de 150 m: %.0f%%'%(100*(_d[_land]<100).mean(),100*(_d[_land]<150).mean()))
from scipy.sparse import coo_matrix as _cm
from scipy.sparse.csgraph import connected_components as _cc
nc_,lb_=_cc(_cm((np.ones(len(edges)),([e['a'] for e in edges],[e['b'] for e in edges])),shape=(len(nodes),len(nodes))),directed=False)
print('componentes conectadas:',sorted(collections.Counter(lb_[[e['a'] for e in edges]]).values(),reverse=True)[:6])

# =====================================================================================
# exportação (Etapa 180b): pistas vão até o centro do cruzamento; meio-fio com "bocas"; sem discos
# =====================================================================================
CWF=lambda c:1.2 if c==3 else 1.8
def away(e,end):
    P=e['pts'];cs=cum(P)
    if end=='a':
        k=int(np.searchsorted(cs,6.0));k=min(max(k,1),len(P)-1);v=P[k]-P[0]
    else:
        L=cs[-1];k=int(np.searchsorted(cs,L-6.0));k=min(max(k,0),len(P)-2);v=P[k]-P[-1]
    return v/max(np.hypot(*v),1e-9)
inc=collections.defaultdict(list)
for ei,e in enumerate(edges):
    if e['a']==e['b'] or len(e['pts'])<2: continue   # (elevadas contam: nas pontas elas pousam no chão)
    inc[e['a']].append((ei,'a'));inc[e['b']].append((ei,'b'))
gaps=collections.defaultdict(lambda:{'l':[],'r':[]});ltrim=collections.defaultdict(lambda:[0.0,0.0])
SS=np.arange(0.0,48.0,0.25)
for k,pcs in inc.items():
    if k in HUBR or len(pcs)<3: continue
    info=[]
    for ei,end in pcs:
        e=edges[ei];u=away(e,end)
        npl=np.array([-u[1],u[0]]) if end=='a' else np.array([u[1],-u[0]])
        info.append((ei,end,u,npl,e['w'],CWF(e['cls'])))
    for ii,(ei,end,u,npl,w,cw) in enumerate(info):
        L=plen(edges[ei]['pts'])
        ltrim[ei][0 if end=='a' else 1]=max(o[4] for jj,o in enumerate(info) if jj!=ii)/2+1.0
        for sgn,key in((1,'l'),(-1,'r')):
            ins=np.zeros(len(SS),bool)
            for off in(w/2+0.5,w/2+cw*0.5,w/2+cw-0.15):
                pts=SS[:,None]*u[None,:]+(sgn*off)*npl[None,:]
                for jj,(ej,endj,uj,nj,wj,cwj) in enumerate(info):
                    if jj==ii: continue
                    mj=np.array([-uj[1],uj[0]])
                    tau=pts@uj;lat=np.abs(pts@mj)
                    ins|=(tau>=0.3)&(lat<=wj/2+0.2)
            if ins.any():
                lo=max(0.0,float(SS[ins].min())-0.4);hi=float(SS[ins].max())+0.4
                gaps[ei][key].append((lo,hi) if end=='a' else (max(0.0,L-hi),L-lo))
# --- rotatórias: o meio-fio da pista só começa onde a pista sai do círculo; a faixa central também
for k,hr in HUBR.items():
    c=np.array(nodes[k])
    for ei,e in enumerate(edges):
        for end in('a','b'):
            if e[end]!=k or len(e['pts'])<2: continue
            u=away(e,end);npl=np.array([-u[1],u[0]]) if end=='a' else np.array([u[1],-u[0]])
            P=e['pts'];p0=P[0] if end=='a' else P[-1];L=plen(P);w=e['w'];cw=CWF(e['cls'])
            for key,sgn in(('l',1),('r',-1)):
                hi=48.0   # o meio-fio começa no 1º ponto em que a faixa toca fora do círculo (sem lasca de grama)
                for off in(w/2,w/2+cw*0.5,w/2+cw):
                    pts=p0[None,:]+SS[:,None]*u[None,:]+(sgn*off)*npl[None,:]
                    out_=np.hypot(*(pts-c).T)>hr+0.05
                    s_=float(SS[out_.argmax()]) if out_.any() else 48.0
                    hi=min(hi,s_)
                gaps[ei][key].append((0.0,hi) if end=='a' else (max(0.0,L-hi),L))
            ax_=np.hypot(*((p0[None,:]+SS[:,None]*u[None,:])-c).T)>hr+0.05
            sa=float(SS[ax_.argmax()]) if ax_.any() else 0.0
            ltrim[ei][0 if end=='a' else 1]=sa+0.4
def merge(iv):
    iv=sorted(iv);out=[]
    for a,b in iv:
        if out and a<=out[-1][1]+0.3: out[-1][1]=max(out[-1][1],b)
        else: out.append([a,b])
    return [x for ab in out for x in ab]
# --- Etapa 180b: onde duas pistas se emendam (curva ou reta), as duas pontas usam a MESMA normal (esquadro) -> sem cunha de grama na quina
mit={}
def ulocal(e,end):
    P=e['pts'];v=(P[1]-P[0]) if end=='a' else (P[-2]-P[-1]);return v/max(np.hypot(*v),1e-9)
for k,lst in inc.items():
    if k in HUBR or len(lst)<2: continue
    us=[ulocal(edges[ei],end) for ei,end in lst]
    cand=[]
    for i in range(len(lst)):
        for j in range(i+1,len(lst)):
            dt=float(us[i]@us[j])
            if dt<-0.5: cand.append((dt,i,j))   # curva de até 60 graus
    cand.sort();used=set()
    for dt,i,j in cand:
        if i in used or j in used: continue
        used|={i,j}
        A=us[j]-us[i];A=A/max(np.hypot(*A),1e-9)
        sc=1.0/max(0.6,float(A@us[j]))
        for idx in(i,j):
            ei,end=lst[idx]
            s=1.0 if ((idx==i and end=='b') or (idx==j and end=='a')) else -1.0
            f=s*A
            mit[(ei,end)]=[round(float(-f[1]*sc),3),round(float(f[0]*sc),3)]
out=[]
for ei,e in enumerate(edges):
    P=e['pts'];z=e['z'];up=z-np.array([Th(*p) for p in P])
    wetf=(e['wet']|(up>2.2)).astype(int);flat=[]
    for i in range(len(P)):
        flat+=[round(float(P[i,0]),1),round(float(P[i,1]),1),round(float(z[i]),2),int(wetf[i])]
    d=dict(c=e['cls'],w=e['w'],a=round(ltrim[ei][0],1),b=round(ltrim[ei][1],1),n=e['name'],p=flat)
    if (ei,'a') in mit: d['n0']=mit[(ei,'a')]
    if (ei,'b') in mit: d['n1']=mit[(ei,'b')]
    if ei in gaps:
        gl=merge(gaps[ei]['l']);gr=merge(gaps[ei]['r'])
        if gl: d['cl']=[round(x,1) for x in gl]
        if gr: d['cr']=[round(x,1) for x in gr]
    out.append(d)
rounds=[]
for k,(nm,hr) in hubnode.items():
    arms=[]
    for ei,e in enumerate(edges):   # todas as pistas que chegam na rotatória (inclusive as elevadas, que ali pousam no chão)
        for end in('a','b'):
            if e[end]!=k or len(e['pts'])<2: continue
            P=e['pts'];p=P[0] if end=='a' else P[-1];u=away(e,end)
            arms+=[round(float(p[0]-nodes[k][0]),2),round(float(p[1]-nodes[k][1]),2),round(float(u[0]),3),round(float(u[1]),3),round(e['w']/2,1)]
    rounds.append(dict(x=round(nodes[k][0],1),z=round(nodes[k][1],1),r=hr,y=round(float(nh[k]),2),n=nm,arms=arms))
padn=[]
js=dict(roads=out,rounds=rounds,nodes=padn,
        houses=[dict(k=h['k'],x=round(h['cx'],1),z=round(h['cz'],1),lvl=round(h['level'],2)) for h in placed],world=[WX,WZ])
json.dump(js,open('city3.json','w'),separators=(',',':'))
with open('relevo.bin','wb') as f:
    f.write(struct.pack('<iif',NX,NZ,G)); f.write(np.round(fin*100).astype('<i2').tobytes())
pickle.dump(dict(fin=fin,water=water,edges=edges,nodes=nodes,hubnode=hubnode,placed=placed,nh=nh,padn=padn),open('state5.pkl','wb'))
print('ok  ruas',len(out),'rotatórias',len(rounds),'cruzamentos com bocas:',sum(1 for e in out if 'cl' in e or 'cr' in e))
