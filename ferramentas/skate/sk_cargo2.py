import sys, struct, numpy as np
sys.path.insert(0,'/home/claude/work/skate')
from scipy import ndimage
from sk_common import *; from sk_garments import subdivide, _sel_tris

def read_cup_pos(fn):
    d=open(fn,'rb').read(); nv,ni,fl=struct.unpack('<3I',d[4:16])
    v=np.frombuffer(d[16:16+nv*44],dtype=np.uint8).reshape(nv,44)
    return np.frombuffer(v[:,0:12].tobytes(),'<f4').reshape(nv,3).astype(float)

class ShoeField:
    """altura da superfície do tênis (cada pé) em função de (x,z)."""
    def __init__(self,P,cs=0.5):
        self.cs=cs; self.x0=-35.0; self.z0=-30.0; nx=int(70/cs); nz=int(70/cs)
        self.H=np.zeros((nz,nx))
        ix=((P[:,0]-self.x0)/cs).astype(int); iz=((P[:,2]-self.z0)/cs).astype(int)
        for a,b,y in zip(ix,iz,P[:,1]): self.H[b,a]=max(self.H[b,a],y)
        self.H=ndimage.maximum_filter(self.H,size=7)
        self.H=ndimage.gaussian_filter(self.H,1.6)
        self.H=np.where(self.H<0.4,0.0,self.H)
    def __call__(self,x,z):
        a=np.clip(((np.asarray(x)-self.x0)/self.cs).astype(int),0,self.H.shape[1]-1); b=np.clip(((np.asarray(z)-self.z0)/self.cs).astype(int),0,self.H.shape[0]-1)
        return self.H[b,a]

def build_cargo2(B,shoe_cup):
    SP=read_cup_pos(shoe_cup); SF=ShoeField(SP)
    waist=B.hip[1]+4.5
    ycut=30.0
    footw=np.array([sum(w for b,w in zip(B.BI[i],B.BW[i]) if b in (19,20,23,24)) for i in range(len(B.P))])
    P0=B.P; N0=B.N
    band=(B.armw<0.3)&(footw<0.55)&(np.abs(P0[:,0])<26)
    M1=band&(P0[:,1]>=ycut-3.0)&(P0[:,1]<=waist+3.0)
    tri0=_sel_tris(B,M1)
    P,N,tri,(bandf,legf)=subdivide(P0,N0,tri0,[band.astype(float),np.sign(P0[:,0])*(np.abs(P0[:,0])>0.8)])
    cy=P[tri][:,:,1].mean(1); tri=tri[cy>=ycut]
    u,inv=np.unique(tri.ravel(),return_inverse=True); P=P[u]; N=N[u]; legf=legf[u]; tri=inv.reshape(-1,3)
    nv=len(P)
    keep=np.ones(nv,bool)
    Q=P.copy(); n=N.copy()
    off=np.interp(Q[:,1],[ycut,40,55,70,90,100,waist],[1.8,2.6,2.8,2.0,1.8,1.5,1.2])
    Q=Q+n*off[:,None]
    sgn=np.where(Q[:,0]>=0,1.0,-1.0)
    axis_x=sgn*B.kn[0]
    r=np.stack([Q[:,0]-axis_x,np.zeros(nv),Q[:,2]-B.kn[2]],1); rn=np.linalg.norm(r,axis=1,keepdims=True); rn[rn<1e-6]=1
    ay=np.interp(Q[:,1],[B.an[1],B.hip[1]],[B.an[0]+0.6,B.hip[0]+1.2]); az=np.interp(Q[:,1],[B.an[1],B.hip[1]],[B.an[2]+0.8,B.hip[2]])   # eixo reto (perna da calça reta, sem dobra no joelho)
    axx=sgn*ay
    rv=np.stack([Q[:,0]-axx,np.zeros(nv),Q[:,2]-az],1); rl=np.linalg.norm(rv,axis=1); rl[rl<1e-6]=1e-6
    Rt=np.interp(Q[:,1],[ycut,45,70,85,95,102],[12.0,11.6,11.8,12.6,11.6,8.6])   # perna reta (sem 'balão' nos quadris)
    wR=np.ones(nv)
    newr=rl+(np.maximum(rl,Rt)-rl)*wR
    Q=Q+(rv/rl[:,None])*(newr-rl)[:,None]
    Q[:,0]=sgn*np.maximum(np.abs(Q[:,0]),1.3)
    r=np.stack([Q[:,0]-axis_x,np.zeros(nv),Q[:,2]-B.kn[2]],1); rn=np.linalg.norm(r,axis=1,keepdims=True); rn[rn<1e-6]=1
    th=np.arctan2(r[:,0],r[:,2])
    fold=0.45*np.sin(6*th+Q[:,1]*0.12)*smooth(98,70,Q[:,1])
    Q=Q+(r/rn)*fold[:,None]
    for s in (-1,1):
        side=(Q[:,0]*s>0)
        px=smooth(-8.4,-6.4,(Q[:,2]-0.5))*smooth(8.4,6.4,(Q[:,2]-0.5))
        py=smooth(61,64,Q[:,1])*smooth(88,85,Q[:,1])
        outer=smooth(0.2,0.8,(Q[:,0]-axis_x)*s/np.maximum(rn[:,0],1e-6))
        bump=1.9*px*py*outer*side
        Q=Q+(r/rn)*bump[:,None]
    # laço de borda inferior (por perna): vértices de borda abertos perto de ycut
    be=[e for e in boundary_edges(tri) if P[e[0],1]<60 and P[e[1],1]<60]
    nxt={a:b for a,b in be}
    loops=[]; seen=set()
    for a0 in list(nxt):
        if a0 in seen: continue
        lp=[a0]; seen.add(a0); a=nxt[a0]
        while a!=a0 and a not in seen:
            lp.append(a); seen.add(a); a=nxt.get(a,a0)
        loops.append(lp)
    loopv=np.array(sorted(v for lp in loops for v in lp))
    Q=laplace(Q,tri,np.isin(np.arange(nv),loopv),it=2,lam=0.35)
    P_all=[Q]; tri_all=[tri]; LEG=[np.sign(legf)]; base=nv
    K=16
    for s in (-1,1):
        lp=[l for l in loops if np.sign(Q[l,0].mean())==s][0]
        lv=np.array(lp)
        _a=np.arctan2(Q[lv,0]-Q[lv,0].mean(),Q[lv,2]-Q[lv,2].mean()); _d=np.angle(np.exp(1j*np.diff(np.append(_a,_a[0]))))
        if _d.sum()<0: lv=lv[::-1]
        c=np.array([Q[lv,0].mean(),0,Q[lv,2].mean()])
        ang=np.arctan2(Q[lv,0]-c[0],Q[lv,2]-c[2])
        n_=len(lv)
        Q[lv,1]=ycut                         # borda reta
        R0=np.hypot(Q[lv,0]-c[0],Q[lv,2]-c[2])
        # altura da barra: assenta em cima do tênis; atrás/lados cai até quase o chão
        # contorno do tênis visto do centro da perna (raio por ângulo)
        sp=SP[np.sign(SP[:,0])==s]
        sa=np.arctan2(sp[:,0]-c[0],sp[:,2]-c[2]); sr=np.hypot(sp[:,0]-c[0],sp[:,2]-c[2])
        NB=72; bins=((sa+np.pi)/(2*np.pi)*NB).astype(int)%NB
        SR=np.zeros(NB)
        for kb in range(NB):
            m=bins==kb
            if m.any(): SR[kb]=sr[m].max()
        SR=ndimage.maximum_filter1d(SR,3,mode='wrap'); SR=ndimage.gaussian_filter1d(SR,1.0,mode='wrap')
        shoeR=SR[((ang+np.pi)/(2*np.pi)*NB).astype(int)%NB]
        fwd=smooth(0.15,0.65,np.cos(ang))
        # atrás e dos lados: a barra passa por FORA do tênis e cai quase até o chão; na frente: apoia em cima do peito do pé
        Rback=np.maximum(R0*0.95,shoeR+1.0)
        Rfront=R0*0.84-0.9*np.maximum(0,np.cos(ang))
        Rh=Rback*(1-fwd)+Rfront*fwd
        hx=c[0]+np.sin(ang)*Rh; hz=c[2]+np.cos(ang)*Rh
        yfront=np.maximum(SF(hx,hz)+1.1,1.6)
        yh=2.2*(1-fwd)+yfront*fwd
        yh=ndimage.gaussian_filter1d(yh,2.0,mode='wrap')
        Rh=ndimage.gaussian_filter1d(Rh,1.5,mode='wrap')
        yh=np.maximum(yh,1.6)
        rings=[list(lv)]
        for j in range(1,K+1):
            f=j/K; ids=[]
            for i in range(n_):
                a=ang[i]; d=np.array([np.sin(a),0,np.cos(a)])
                ff=smooth(0,1,f)
                rr=R0[i]+(Rh[i]-R0[i])*ff
                fr=max(0.0,d[2])
                rr+=0.9*np.sin(np.pi*f)*fr**1.5                    # tecido se acumulando na frente
                rr+=0.33*np.sin(2*np.pi*f*2.6+a*2.0)*smooth(0.15,0.6,f)    # dobras horizontais leves
                rr+=0.28*np.sin(7*a+f*2.5)*smooth(0.1,0.5,f)
                y=ycut+(yh[i]-ycut)*f
                x=c[0]+d[0]*rr; z=c[2]+d[2]*rr
                for _ in range(10):                                 # nunca atravessa o tênis
                    if SF(x,z)+0.5<=y: break
                    rr+=0.35; x=c[0]+d[0]*rr; z=c[2]+d[2]*rr
                if SF(x,z)+0.5>y: y=SF(x,z)+0.5
                P_all.append(np.array([[x,y,z]])); LEG.append(np.array([float(s)])); ids.append(base); base+=1
            rings.append(ids)
        T=[]
        for j in range(K):
            a_=rings[j]; b_=rings[j+1]
            for k in range(n_):
                k2=(k+1)%n_; T+=[(a_[k],b_[k],a_[k2]),(a_[k2],b_[k],b_[k2])]
        tri_all.append(np.array(T,np.int64))
    PP=np.vstack([Q]+P_all[1:]); TT=np.vstack(tri_all)
    bset=set(); [bset.update(e) for e in boundary_edges(TT)]
    fixed=(PP[:,1]>56)|np.isin(np.arange(len(PP)),list(bset))
    PP=laplace(PP,TT,fixed,it=5,lam=0.45)
    NN=vnormals(PP,TT)
    ax2=np.where(PP[:,0]>=0,1,-1)*B.kn[0]
    chk=((PP[:,[0]]-ax2[:,None])*NN[:,[0]]).sum(1)
    if np.mean(chk[np.abs(PP[:,1]-60)<15]>0)<0.5: NN=-NN
    return PP,NN,TT,dict(waist=waist,hem=ycut,low=1.6,leg=np.concatenate(LEG))
