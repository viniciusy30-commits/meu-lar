# Etapa 166: chão de caminhada e paredes por andar das casas do Hds -> city2walk.bin
import sys,json,math,re,struct
import numpy as np, citygen
R=citygen.build(NX=4,NZ=2); T=citygen.templates(R); P=citygen.finish(R,T); citygen.extras(R,P)
plist=R.plist; inst=R.inst
js=json.load(open('/home/claude/a/codigo/app/src/main/assets/hds/city2.json'))
plots=js['plots']; CS=0.25; M0=0.6
# Etapa 166: a Casa 5 tinha uma caixa de 286x100 m (peças soltas a ~243 m de altura); recalcula as caixas ignorando peças fora de -20..20 m
_pb={}
for _r in inst:
    _pl=_r[14]; _nm=plist[_r[0]]['name'].lower()
    if _pl<0 or re.search(r'fence|post|gate',_nm) or _nm in('baseboard_mesh','ao_mesh'): continue
    _M=np.array(_r[1:13],float).reshape(3,4)
    for (_mi,_Pv,_Nv,_UV,_I) in plist[_r[0]]['subs']:
        _V=_Pv@_M[:,:3].T+_M[:,3]
        if _V[:,1].min()<-20 or _V[:,1].max()>20: continue
        _b=_pb.setdefault(_pl,[1e9,1e9,-1e9,-1e9]); _b[0]=min(_b[0],_V[:,0].min()); _b[1]=min(_b[1],_V[:,2].min()); _b[2]=max(_b[2],_V[:,0].max()); _b[3]=max(_b[3],_V[:,2].max())
for _k,_p in enumerate(plots):
    _b=_pb[_k]; _p.update(x0=round(float(_b[0]),3),z0=round(float(_b[1]),3),x1=round(float(_b[2]),3),z1=round(float(_b[3]),3))
    print(_k,_p['name'],_p['x0'],_p['z0'],_p['x1'],_p['z1'])
def Mof(r): return np.array(r[1:13],float).reshape(3,4)
grids=[]
for p in plots:
    x0=p['x0']-M0; z0=p['z0']-M0; nx=int(math.ceil((p['x1']+M0-x0)/CS)); nz=int(math.ceil((p['z1']+M0-z0)/CS))
    grids.append(dict(x0=x0,z0=z0,nx=nx,nz=nz,wall=np.zeros(nx*nz,np.uint32),fl=[set() for _ in range(nx*nz)]))
BAD=re.compile(r'baseboard|ao_mesh|road|lamp|tree|hydrant|trash|bed|fence|gate|post|grama|junction')
FENCE=re.compile(r'fence|post|gate')
def tri_points(A,B,C,sp):
    e=max(np.linalg.norm(B-A),np.linalg.norm(C-A),np.linalg.norm(C-B)); n=max(1,int(math.ceil(e/sp)))
    ii,jj=np.meshgrid(np.arange(n+1),np.arange(n+1)); m=(ii+jj)<=n; u=(ii[m]/n)[:,None]; v=(jj[m]/n)[:,None]
    return A+(B-A)*u+(C-A)*v
for r in inst:
    pl=r[14]; kind=r[13]
    if pl<0: continue
    nm=plist[r[0]]['name'].lower(); G=grids[pl]; M=Mof(r)
    if BAD.search(nm) and not (kind==1 and not FENCE.search(nm)): continue
    for (mi,Pv,Nv,UV,I) in plist[r[0]]['subs']:
        V=Pv@M[:,:3].T+M[:,3]; T3=I.reshape(-1,3)
        for a,b,c in zip(V[T3[:,0]],V[T3[:,1]],V[T3[:,2]]):
            nrm=np.cross(b-a,c-a); ln=np.linalg.norm(nrm)
            if ln<1e-9: continue
            ny=nrm[1]/ln
            if kind==1:
                if FENCE.search(nm): continue
                pts=tri_points(a,b,c,0.12)
                pts=pts[(pts[:,1]>=-3)&(pts[:,1]<13)]
            else:
                if ny<0.5: continue
                pts=tri_points(a,b,c,0.1)
                pts=pts[(pts[:,1]>-3.2)&(pts[:,1]<8.5)]
            if not len(pts): continue
            ix=np.floor((pts[:,0]-G['x0'])/CS).astype(int); iz=np.floor((pts[:,2]-G['z0'])/CS).astype(int)
            ok=(ix>=0)&(ix<G['nx'])&(iz>=0)&(iz<G['nz'])
            ix,iz,y=ix[ok],iz[ok],pts[ok,1]
            if kind==1:
                bits=np.clip(np.floor((y+3)/0.5).astype(int),0,31)
                for i,j,bt in set(zip(ix.tolist(),iz.tolist(),bits.tolist())): G['wall'][j*G['nx']+i]|=(1<<bt)
            else:
                hq=np.round(y/0.04).astype(int)
                for i,j,h in set(zip(ix.tolist(),iz.tolist(),hq.tolist())): G['fl'][j*G['nx']+i].add(h)
out=bytearray(struct.pack('<If',len(grids),CS))
tot=0
for G in grids:
    out+=struct.pack('<ffii',G['x0'],G['z0'],G['nx'],G['nz'])
    out+=G['wall'].tobytes()
    for s in G['fl']:
        hs=[]
        for h in sorted(s):
            if hs and h-hs[-1]<=1: hs[-1]=h
            else: hs.append(h)
        hs=hs[:10]; tot+=len(hs)
        out+=struct.pack('<B',len(hs))+b''.join(struct.pack('<h',int(h*4)) for h in hs)   # cm
open('/home/claude/out/c2/city2walk.bin','wb').write(out)
print('bytes',len(out),'floor entries',tot)

# Etapa 167: buracos na grama (plano de y=0) sobre porões/escadas/piscina: células com piso abaixo de -0,5 m
holes=[]
for G in grids:
    nx,nz=G['nx'],G['nz']
    m=np.array([bool(f) and min(f)*0.04<=-0.5 for f in G['fl']]).reshape(nz,nx)
    # junta em retângulos: faixas por linha, depois empilha faixas iguais
    runs={}
    for z in range(nz):
        x=0
        while x<nx:
            if m[z,x]:
                e=x
                while e+1<nx and m[z,e+1]: e+=1
                runs.setdefault((x,e),[]).append(z); x=e+1
            else: x+=1
    for (a,e),zs in runs.items():
        zs.sort(); s0=p=zs[0]
        for z in zs[1:]+[None]:
            if z is not None and z==p+1: p=z; continue
            holes+=[round(G['x0']+a*CS,3),round(G['z0']+s0*CS,3),round(G['x0']+(e+1)*CS,3),round(G['z0']+(p+1)*CS,3)]
            if z is not None: s0=p=z
js['holes']=holes
json.dump(js,open('/home/claude/out/c2/city2.json','w'),separators=(',',':'))
print('holes',len(holes)//4)
