import struct, numpy as np
from scipy.spatial import cKDTree
from scipy import ndimage
CUTE='/home/claude/work/merged/app/src/main/assets/cute/'
DT=np.dtype([('p','<3f4'),('n','<3f4'),('uv','<2f4'),('c','4u1'),('bi','4u1'),('bw','4u1')])
class Body: pass
def load_body(g):
    d=open(CUTE+'p_body_%s1.bin'%g,'rb').read(); nv,ni,fl=struct.unpack_from('<3I',d,4)
    v=np.frombuffer(d,DT,nv,16); idx=np.frombuffer(d,'<u2',ni,16+nv*44).reshape(-1,3).astype(np.int64)
    B=Body(); B.g=g; B.P=v['p'].astype(np.float64); B.N=v['n'].astype(np.float64); B.BI=v['bi'].astype(int); B.BW=v['bw'].astype(float)/255.0; B.idx=idx
    for ln in open(CUTE+'bodyrig.txt'):
        k,vals=ln.strip().split('|')
        if k==g+'1': B.rig=np.array([float(x) for x in vals.split(',')])
    B.sh=B.rig[0:3]; B.el=B.rig[3:6]; B.ha=B.rig[6:9]; B.hip=B.rig[9:12]; B.kn=B.rig[12:15]; B.an=B.rig[15:18]
    B.neck_y=B.rig[19]; B.head_y=B.rig[20]
    arm=set(list(range(10,13))+list(range(14,17))+list(range(25,55)))
    B.armw=np.array([sum(w for b,w in zip(B.BI[i],B.BW[i]) if b in arm) for i in range(len(B.P))])
    B.simh=1.0
    weld(B)
    return B

def vnormals(P,tri):
    a,b,c=P[tri[:,0]],P[tri[:,1]],P[tri[:,2]]
    fn=np.cross(b-a,c-a); N=np.zeros_like(P)
    for k in range(3): np.add.at(N,tri[:,k],fn)
    L=np.linalg.norm(N,axis=1,keepdims=True); L[L<1e-12]=1; return N/L

def boundary_edges(tri):
    e={}
    for t in tri:
        for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])):
            k=(a,b) if a<b else (b,a); e.setdefault(k,[0,(a,b)]); e[k][0]+=1
    return [v[1] for v in e.values() if v[0]==1]

def laplace(P,tri,fixed,it=2,lam=0.5):
    nv=len(P); nb=[set() for _ in range(nv)]
    for t in tri:
        for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])): nb[a].add(b); nb[b].add(a)
    P=P.copy()
    for _ in range(it):
        Q=P.copy()
        for i in range(nv):
            if fixed[i] or not nb[i]: continue
            m=np.mean([P[j] for j in nb[i]],axis=0); Q[i]=P[i]+lam*(m-P[i])
        P=Q
    return P

def add_lips(P,N,tri,attr,thick):
    """fecha as bordas abertas com uma beirada de espessura 'thick' (vai para dentro pela normal)."""
    be=boundary_edges(tri); inner={}; P2=[P]; N2=[N]; A2=[attr]; n=len(P); newtri=[tri]
    def get(v):
        nonlocal n
        if v not in inner:
            inner[v]=n; n+=1; P2.append((P[v]-N[v]*thick)[None]); N2.append((-N[v])[None]); A2.append(attr[v][None])
        return inner[v]
    q=[]
    for a,b in be:
        ia,ib=get(a),get(b); q+= [(a,b,ib),(a,ib,ia)]
    newtri.append(np.array(q,np.int64).reshape(-1,3))
    return np.vstack(P2),np.vstack(N2),np.vstack(newtri),np.vstack(A2),be

def transfer_weights(B,P,slot=None):
    """copia pesos de osso do corpo: 3 vizinhos do mesmo lado, ponderados por 1/(d+0.8)."""
    tree=cKDTree(B.P0); k=10
    d,ix=tree.query(P,k=k)
    bi=np.zeros((len(P),4),np.uint8); bw=np.zeros((len(P),4),np.uint8)
    for v in range(len(P)):
        x=P[v,0]; sel=[]
        for dd,j in zip(d[v],ix[v]):
            bx=B.P0[j,0]
            if abs(x)>2.5 and abs(bx)>1.0 and (x>0)!=(bx>0): continue
            sel.append((dd,j))
            if len(sel)==3: break
        if not sel: sel=[(d[v,0],ix[v,0])]
        acc={}
        for dd,j in sel:
            wk=1.0/(dd+0.8)
            for b,w in zip(B.BI0[j],B.BW0[j]):
                if w>0: acc[b]=acc.get(b,0)+w*wk
        top=sorted(acc.items(),key=lambda kv:-kv[1])[:4]; s=sum(w for _,w in top)
        q=[int(round(w/s*255)) for _,w in top]; q[0]+=255-sum(q)
        for k2,((b,_),w) in enumerate(zip(top,q)): bi[v,k2]=b; bw[v,k2]=w
    return bi,bw

def write_cup(path,P,N,UV,tri,bi,bw):
    n=len(P); r=np.zeros(n,DT); r['p']=P; r['n']=N; r['uv']=UV; r['c']=255; r['bi']=bi; r['bw']=bw
    assert n<65536,n
    with open(path,'wb') as f:
        f.write(b'CUP1'+struct.pack('<3i',n,tri.size,0)); f.write(r.tobytes()); f.write(tri.astype('<u2').reshape(-1).tobytes())

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)


def weld(B):
    """junta vértices coincidentes (costuras de UV do corpo), para a roupa não rachar."""
    key=np.round(B.P*200).astype(np.int64)
    _,first,inv=np.unique(key,axis=0,return_index=True,return_inverse=True)
    inv=inv.reshape(-1)
    n=len(first)
    N=np.zeros((n,3)); np.add.at(N,inv,B.N)
    L=np.linalg.norm(N,axis=1,keepdims=True); L[L<1e-9]=1
    B.P0=B.P; B.N0=B.N; B.BI0=B.BI; B.BW0=B.BW   # originais (para pesos)
    B.P=B.P[first]; B.N=N/L; B.BI=B.BI[first]; B.BW=B.BW[first]; B.armw=B.armw[first]
    idx=inv[B.idx]; ok=(idx[:,0]!=idx[:,1])&(idx[:,1]!=idx[:,2])&(idx[:,0]!=idx[:,2])
    B.idx=idx[ok]


def transfer_weights2(B,P,A):
    """pesos por tipo de vértice: A[:,2]=perna (+1/-1/0), A[:,3]=fração da barra (camiseta), A[:,4]=altura de origem da barra."""
    tree=cKDTree(B.P0); k=12
    def wq(q,side):
        d,ix=tree.query(q,k=k); sel=[]
        for dd,j in zip(d,ix):
            bx=B.P0[j,0]
            if side!=0 and abs(bx)>1.0 and (bx>0)!=(side>0): continue
            sel.append((dd,j))
            if len(sel)==3: break
        if not sel: sel=[(d[0],ix[0])]
        acc={}
        for dd,j in sel:
            wk=1.0/(dd+0.8)
            for b,w in zip(B.BI0[j],B.BW0[j]):
                if w>0: acc[b]=acc.get(b,0)+w*wk
        sm=sum(acc.values()); return {b:w/sm for b,w in acc.items()}
    bi=np.zeros((len(P),4),np.uint8); bw=np.zeros((len(P),4),np.uint8)
    cache={}
    for v in range(len(P)):
        x,y,z=P[v]; leg=A[v,2]; rf=A[v,3]; y0=A[v,4]
        side=float(np.sign(x)) if abs(x)>2.5 else 0.0
        if rf>0.001:
            Wt=wq(np.array([x,y0,z]),side); Wl=wq(P[v],side)
            W={}
            for b,w in Wt.items(): W[b]=W.get(b,0)+w*(1-rf)
            for b,w in Wl.items(): W[b]=W.get(b,0)+w*rf
        elif abs(leg)>0.5:
            lg=1.0 if leg>0 else -1.0
            t=float(smooth(B.hip[1],B.hip[1]-12.0,y))
            axp=np.array([lg*np.interp(y,[B.an[1],B.kn[1],B.hip[1]],[B.an[0],B.kn[0],B.hip[0]]),y,np.interp(y,[B.an[1],B.kn[1],B.hip[1]],[B.an[2],B.kn[2],B.hip[2]])])
            W=wq(P[v]*(1-t)+axp*t,lg)
        else:
            W=wq(P[v],side)
        top=sorted(W.items(),key=lambda kv:-kv[1])[:4]; sm=sum(w for _,w in top)
        q=[int(round(w/sm*255)) for _,w in top]; q[0]+=255-sum(q)
        for k2,((b,_),w) in enumerate(zip(top,q)): bi[v,k2]=b; bw[v,k2]=w
    return bi,bw
