from fitlib import *
MARGIN=0.35   # cm de folga mínima entre a blusa e a pele
def load_top():
    r,gs=load_geoms(); e,g=gs[0x29]; raw=dbpf.data(e)
    bones=geom_bones(raw)
    P0=g['pos'].astype(float)*K+OFF; N=g['nor'].astype(float); UV=g['uv'][0].astype(float); I=g['idx'].astype(int)
    bi=g['bi'].astype(int); bw=g['bw'].astype(float)/255
    amap=np.array([APP[n] for n in bones])
    W=np.zeros((len(P0),55)); np.add.at(W,(np.arange(len(P0))[:,None],amap[bi]),bw)
    return r,P0,N,UV,I,W
def load_body():
    sv,si,fl,_=E.read_piece(CU+'p_body_af5.bin')
    return sv,si.astype(int)
def body_w55(sv):
    n=len(sv); W=np.zeros((n,55)); bi=sv['bi'].astype(int); bw=sv['bw'].astype(float)/255
    np.add.at(W,(np.arange(n)[:,None],bi),bw); return W
def adjacency(n,I):
    nb=[set() for _ in range(n)]
    for a,b,c in I: nb[a]|={b,c}; nb[b]|={a,c}; nb[c]|={a,b}
    return [np.array(sorted(s)) for s in nb]
def clearance_push(P0,I,sv,margin=MARGIN):
    sp=sv['pos'].astype(float); sn=sv['nor'].astype(float)
    t=cKDTree(sp); d,nb=t.query(P0); n=sn[nb]; n/=np.linalg.norm(n,axis=1,keepdims=True)
    sd=((P0-sp[nb])*n).sum(1)
    need=np.where(d<1.5,np.maximum(0,margin-sd),0.0)
    adj=adjacency(len(P0),I)
    s=need.copy()
    for _ in range(3):
        s=np.array([ (s[i]+s[a].mean())/2 if len(a) else s[i] for i,a in enumerate(adj)])
        s=np.maximum(s,need)
    return P0+n*s[:,None],s,sd,d

if __name__=='__main__':
    r,P0,N,UV,I,W=load_top(); sv,si=load_body()
    P1,s,sd,d=clearance_push(P0,I,sv)
    print('push: max',s.max().round(2),'média nos tocados',s[s>0].mean().round(2),'n',(s>0).sum(),'/',len(s))
    # pesos: nativo vs corpo nos vértices coincidentes
    Wb=body_w55(sv); t=cKDTree(sv['pos'].astype(float)); dd,nb=t.query(P0)
    co=dd<0.05; diff=np.abs(W[co]-Wb[nb[co]]).sum(1)/2
    print('coincidentes',co.sum(),'dif. de peso nativo×corpo: média',diff.mean().round(4),'máx',diff.max().round(3),'>0.05:',(diff>0.05).sum())
    hand=np.isin(W.argmax(1),list(range(12,13))+list(range(16,17))+list(range(25,55)))
    print('vértices de mão',hand.sum())
