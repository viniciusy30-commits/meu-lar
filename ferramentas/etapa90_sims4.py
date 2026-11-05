NECK_TINT=False
import sys, numpy as np, struct
sys.path.insert(0,'/tmp/ml/ferramentas'); sys.argv=['x','/tmp/ml/app/src/main/assets/cute']
import etapa48_jovem as E
from scipy.spatial import cKDTree
from PIL import Image
from scipy import ndimage
U='/mnt/user-data/uploads/'
def rd(f, grp=None):
    V=[];T=[];F=[];g=None
    for l in open(f):
        if l.startswith('g '): g=l.split()[1]
        elif l.startswith('v '): V.append(list(map(float,l.split()[1:4])))
        elif l.startswith('vt '): T.append(list(map(float,l.split()[1:3])))
        elif l.startswith('f '):
            if grp and g!=grp: continue
            p=[x.split('/') for x in l.split()[1:]]; F.append([(int(a[0])-1,int(a[1])-1) for a in p])
    return np.array(V),np.array(T),F
sys.path.insert(0,'/tmp/s4tools')
import uvfix
_TR=uvfix.train(['top','bottom','mens'])
_FEM={}
def uv0_for(objf):
    # Etapa 90b: o OBJ só trouxe o UV1 (cilíndrico). O UV0 (atlas) vem das roupas de baixo padrão do TS4 (.package Softe):
    # mesmo corpo da EA -> posição igual dá o UV0 exato (o UV1 desempata as costuras, onde há vértices duplicados).
    # Mulher: o resto (pés) pelo vizinho em UV1. Homem: o tronco/braços vêm do corpo da mulher já resolvido
    # (corpo do homem ajustado ao tamanho do dela; vizinho por posição + UV1, para não trocar frente/costas)
    TP,T0,T1=_TR
    V,T,_=rd(objf); u1=np.c_[T[:,0],1-T[:,1]]; V=V[:len(T)]
    dp,ip=cKDTree(TP).query(V,k=6)
    cost=np.where(dp<1e-4,np.linalg.norm(T1[ip]-u1[:,None],axis=2),1e9)
    j=cost.argmin(1); ie=ip[np.arange(len(V)),j]; ex=cost.min(1)<1e8
    if 'V' not in _FEM:
        da,ia=cKDTree(T1).query(u1)
        out=np.where(ex[:,None],T0[ie],T0[ia]); _FEM.update(V=V,U1=u1,U0=out)
    else:
        FV,FU1,FU0=_FEM['V'],_FEM['U1'],_FEM['U0']
        W=V.copy()
        lo,hi=V.min(0),V.max(0); flo,fhi=FV.min(0),FV.max(0)
        W=(V-lo)/(hi-lo)*(fhi-flo)+flo
        da,ia=cKDTree(np.c_[FV*4,FU1]).query(np.c_[W*4,u1])
        out=np.where(ex[:,None],T0[ie],FU0[ia])
    # pés: o .package não tem pés (vêm dos sapatos) -> cor lisa da pele do tornozelo
    ft=(V[:,1]<0.205)   # pé + tornozelo (o atlas desenha linhas no tornozelo que viram faixa)
    ok=np.where(~ft&(V[:,1]>0.25)&(V[:,1]<0.4)&ex)[0]
    for side in (1,-1):
        fs=ft&(np.sign(V[:,0])==side); cs=ok[np.sign(V[ok,0])==side]
        if fs.any() and len(cs):
            # uma cor só por pé (o meio da panturrilha, na frente) -> sem listras
            c=cs[np.argmax(V[cs,2]-np.abs(V[cs,1]-0.32))]; out[fs]=out[c]
    # candidatos de UV0 nas costuras (mesma posição, ilhas diferentes): cada triângulo escolhe o da sua ilha
    cand=[[out[t]] for t in range(len(V))]
    for t in np.where(ex)[0]:
        for jj in range(6):
            if dp[t,jj]<1e-4:
                c=T0[ip[t,jj]]
                if all(np.abs(c-x).max()>1e-4 for x in cand[t]): cand[t].append(c)
    if 'cand' not in _FEM: _FEM['cand']=cand
    elif 'ia' in dir():
        for t in np.where(~ex&~ft)[0]:
            for c in _FEM['cand'][ia[t]]:
                if all(np.abs(c-x).max()>1e-4 for x in cand[t]): cand[t].append(c)
    print(objf[-25:],'exato',ex.sum(),'aprox',(~ex).sum(),'pés',ft.sum(),'costuras',sum(len(c)>1 for c in cand))
    return cand
_ORIG=[]
import glob as _g
def _head_ring(hf, bodyf):
    # Etapa 90c: o corpo traz uma cabeça simples. A borda de baixo da cabeça detalhada coincide com uma volta de vértices do
    # pescoço do corpo: corta o corpo exatamente nessa volta (triângulos alcançáveis a partir dos pés sem cruzar a volta)
    from collections import Counter, defaultdict
    HV,_,HF=rd(hf,'TS4Head_lod0'); c=Counter()
    for t in HF:
        ids=[vi for vi,_ in t]
        for a_,b_ in ((ids[0],ids[1]),(ids[1],ids[2]),(ids[2],ids[0])): c[tuple(sorted((a_,b_)))]+=1
    hb=np.unique([k for k,n in c.items() if n==1]); hb=hb[HV[hb,1]<1.7]
    V,_,F=rd(bodyf)
    d,_i=cKDTree(HV[hb]).query(V); onring=d<1e-5
    _,pid=np.unique(np.round(V,5),axis=0,return_inverse=True); pid=pid.ravel()   # solda por posição (o OBJ vem em pedaços)
    onp=np.zeros(pid.max()+1,bool); onp[pid[onring]]=True
    raw=[tuple(vi for vi,_ in t) for t in F]
    tris=[tuple(pid[x] for x in t) for t in raw]
    onring=onp
    em=defaultdict(list)
    for k,t in enumerate(tris):
        for a_,b_ in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])): em[tuple(sorted((a_,b_)))].append(k)
    start=int(np.argmin([min(V[x,1] for x in t) for t in raw]))
    keep=np.zeros(len(tris),bool); keep[start]=True; st=[start]
    while st:
        k=st.pop(); t=tris[k]
        for a_,b_ in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])):
            if onring[a_] and onring[b_]: continue
            for k2 in em[tuple(sorted((a_,b_)))]:
                if not keep[k2]: keep[k2]=True; st.append(k2)
    print('corpo: triângulos mantidos',keep.sum(),'de',len(tris),'volta',onring.sum())
    # pedaços soltos (sem ligação com os pés): mantém se estiverem abaixo da volta
    ry=V[d<1e-5,1].max()
    for k in range(len(raw)):
        if not keep[k] and max(V[x,1] for x in raw[k])<ry-0.03: keep[k]=True
    # o que sobrou da cabeça simples encostada na cabeça detalhada (queixo): fora
    hv=np.unique([vi for t in HF for vi,_ in t]); kd=cKDTree(HV[hv]); y0=V[d<1e-5,1].min(); zc_=V[d<1e-5,2].mean()
    for k in np.where(keep)[0]:
        cen=V[list(raw[k])].mean(0)
        if cen[2]>zc_+0.02 and cen[1]>y0+0.004 and kd.query(cen)[0]<0.015 and not all(onring[pid[x]] for x in raw[k]):
            if sum(onring[pid[x]] for x in raw[k])<2: keep[k]=False
    print('corpo: triângulos mantidos',keep.sum(),'de',len(tris))
    ks={raw[k] for k in np.where(keep)[0]}
    return lambda t: t not in ks
def build(objs):
    _ORIG.clear()
    # vertices únicos por (arquivo, v, vt); uv já no atlas (v de cima para baixo)
    P=[];UV=[];I=[];key={}
    for f,grp in objs:
        V,T,F=rd(f,grp)
        head = grp is not None
        if not head:
            B0=uv0_for(f)
            ring=_head_ring(U+('8e063fe5-FemaleHeadMesh_OBJ.obj' if 'Female' in f else 'a625f04d-MaleHeadMesh_OBJ.obj'), f)
        for tri in F:
            if not head and ring(tuple(vi for vi,_ in tri)): continue   # o corpo traz uma cabeça simples: corta exatamente na borda de baixo da cabeça detalhada
            if head: ch=[tuple((T[ti][0],1-T[ti][1])) for vi,ti in tri]
            else:
                import itertools
                best=None
                for combo in itertools.product(*[B0[ti] for vi,ti in tri]):
                    c=np.array(combo); sp=np.ptp(c,axis=0).max()
                    if best is None or sp<best[0]: best=(sp,combo)
                ch=[tuple(np.round(x,6)) for x in best[1]]
                if best[0]>0.1:   # triângulo entre duas ilhas do atlas (ombro): cor lisa de um canto, sem faixa esticada
                    ys=[V[vi][1] for vi,_ in tri]; c0=ch[int(np.argmin(ys))]; ch=[c0,c0,c0]
            for (vi,ti),uv in zip(tri,ch):
                k=(f,vi,uv)
                if k not in key:
                    key[k]=len(P); P.append(V[vi]); UV.append(uv); _ORIG.append(1 if head else 0)
                I.append(key[k])
    return np.array(P),np.array(UV),np.array(I).reshape(-1,3)
def eyes(head_obj):
    """globos oculares (o TS4 os tem separados): esfera atrás de cada furo do olho, com o olho do atlas no canto"""
    from collections import Counter
    V,T,F=rd(head_obj,'TS4Head_lod0'); Fi=np.array([[a for a,_ in t] for t in F])
    _,inv=np.unique(np.round(V,5),axis=0,return_inverse=True); inv=inv.ravel(); FF=inv[Fi]
    e=Counter()
    for t in FF:
        for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])): e[tuple(sorted((a,b)))]+=1
    W=np.zeros((inv.max()+1,3)); W[inv]=V
    bv=np.unique([v for k,c in e.items() if c==1 for v in k]); B=W[bv]
    P=[];UV=[];I=[]
    for side in (-1,1):
        m=(B[:,0]*side>0.005)&(B[:,1]>1.70)&(B[:,1]<1.80)&(B[:,2]>0.04); Q=B[m]
        c=Q.mean(0); r=max(np.ptp(Q[:,0]),np.ptp(Q[:,1]))*0.56
        cen=np.array([c[0],c[1],Q[:,2].max()-r+0.002])
        n=16; base=len(P)
        for i in range(n+1):
            th=np.pi*i/n
            for j in range(2*n+1):
                ph=2*np.pi*j/(2*n); d=np.array([np.sin(th)*np.cos(ph),np.cos(th),np.sin(th)*np.sin(ph)])
                p=cen+d*r; P.append(p)
                UV.append((0.0512+d[0]*0.047, 0.2760-d[1]*0.0235) if d[2]>-0.2 else (0.006,0.26))
        for i in range(n):
            for j in range(2*n):
                a=base+i*(2*n+1)+j; I+= [[a,a+2*n+1,a+1],[a+1,a+2*n+1,a+2*n+2]]
    return np.array(P),np.array(UV),np.array(I)
def normals(P,I):
    n=np.zeros_like(P); fn=np.cross(P[I[:,1]]-P[I[:,0]],P[I[:,2]]-P[I[:,0]])
    for k in range(3): np.add.at(n,I[:,k],fn)
    return n/(np.linalg.norm(n,axis=1,keepdims=True)+1e-12)
def eye_boundaries(P,I):
    from collections import Counter
    e=Counter()
    for t in I:
        for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])): e[tuple(sorted((a,b)))]+=1
    # posições (soldadas) para não pegar costura de UV
    return [k for k,c in e.items() if c==1]
def bake(atlas, v, I, grp, texpath, S=1024):
    """o OBJ do corpo veio com o canal de UV errado (layout cilíndrico, não o do atlas do TS4): a pele do corpo é assada
    na metade de baixo do atlas, a partir do corpo do Sims 3 (mesma pose e posição), com o tom corrigido para o do rosto do TS4"""
    sys.path.insert(0,'/home/claude/work/obj3d')
    from integridade import _pt_tri
    CU='/tmp/ml/app/src/main/assets/cute/'
    sv,sidx,_,_=E.read_piece(CU+'p_body_%s1.bin'%grp)
    sk=np.asarray(Image.open(CU+'sk_%s.png'%grp).convert('RGB'),float); sh,sw=sk.shape[:2]
    SP=sv['pos'].astype(float); SU=sv['uv'].astype(float); ST=sidx.astype(int)
    P=v['pos'].astype(float); UV=v['uv'].astype(float)
    tb=I[(UV[I][:,:,1]>=0.5).all(1)]                       # triângulos do corpo
    A=np.asarray(atlas,float).copy(); H=A.shape[0]
    out=np.zeros((S,S,3)); have=np.zeros((S,S),bool)
    cen=SP[ST].mean(1); tree=cKDTree(cen)
    for t in tb:
        q=np.c_[UV[t][:,0]*S, (UV[t][:,1]-0.5)*2*S]
        x0,y0=np.floor(q.min(0)).astype(int); x1,y1=np.ceil(q.max(0)).astype(int)
        x0=max(x0,0); y0=max(y0,0); x1=min(x1,S-1); y1=min(y1,S-1)
        if x1<x0 or y1<y0: continue
        gx,gy=np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5)
        a,b,c=q; den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-9: continue
        l0=((b[1]-c[1])*(gx-c[0])+(c[0]-b[0])*(gy-c[1]))/den; l1=((c[1]-a[1])*(gx-c[0])+(a[0]-c[0])*(gy-c[1]))/den; l2=1-l0-l1
        m=(l0>=-0.02)&(l1>=-0.02)&(l2>=-0.02)
        if not m.any(): continue
        pts=l0[m,None]*P[t[0]]+l1[m,None]*P[t[1]]+l2[m,None]*P[t[2]]
        _,cand=tree.query(pts,k=6)
        best=np.full(len(pts),1e9); buv=np.zeros((len(pts),2))
        for j in range(6):
            tri=ST[cand[:,j]]; A0=SP[tri[:,0]];B0=SP[tri[:,1]];C0=SP[tri[:,2]]
            # projeção no plano do triângulo + baricêntricas (aproximação do ponto mais perto)
            nrm=np.cross(B0-A0,C0-A0); nn=np.linalg.norm(nrm,axis=1,keepdims=True)+1e-12; nrm/=nn
            pp=pts-((pts-A0)*nrm).sum(1,keepdims=True)*nrm
            v0=B0-A0;v1=C0-A0;v2=pp-A0
            d00=(v0*v0).sum(1);d01=(v0*v1).sum(1);d11=(v1*v1).sum(1);d20=(v2*v0).sum(1);d21=(v2*v1).sum(1)
            dn=d00*d11-d01*d01+1e-12; bb=(d11*d20-d01*d21)/dn; cc=(d00*d21-d01*d20)/dn; aa=1-bb-cc
            bc=np.clip(np.stack([aa,bb,cc],1),0,1); bc/=bc.sum(1,keepdims=True)
            cp=bc[:,0,None]*A0+bc[:,1,None]*B0+bc[:,2,None]*C0
            dd=np.linalg.norm(cp-pts,axis=1)
            u_=bc[:,0,None]*SU[tri[:,0]]+bc[:,1,None]*SU[tri[:,1]]+bc[:,2,None]*SU[tri[:,2]]
            # triângulo do Sims com UV espalhado (atravessa costura) não serve
            span=np.ptp(SU[tri],axis=1).max(1)
            dd=np.where(span>0.25,1e9,dd)
            better=dd<best; best[better]=dd[better]; buv[better]=u_[better]
        sx=np.clip(buv[:,0]*sw,0,sw-1).astype(int); sy=np.clip(buv[:,1]*sh,0,sh-1).astype(int)
        yy=gy[m].astype(int); xx=gx[m].astype(int)
        out[yy,xx]=sk[sy,sx]; have[yy,xx]=True
    # tom: o corpo assado recebe a média de cor da pele do rosto do TS4 (faixa da bochecha no atlas)
    face=np.asarray(Image.open(texpath).convert('RGB').resize((1024,2048)),float)[int(0.36*2048):int(0.44*2048),int(0.30*1024):int(0.36*1024)].reshape(-1,3)
    skin=out[have]; lum=skin.mean(1)
    ref=skin[(lum>np.percentile(lum,40))&(lum<np.percentile(lum,90))].mean(0)
    gain=face.mean(0)/ref*1.12
    out=np.clip(out*gain,0,255)
    # preenche as bordas (dilatação) para a costura não mostrar fundo
    idx_=ndimage.distance_transform_edt(~have,return_distances=False,return_indices=True)
    out=out[idx_[0],idx_[1]]
    A[H//2:]=Image.fromarray(out.astype(np.uint8)).resize((1024,H//2))
    return Image.fromarray(A.astype(np.uint8))

def neck_tone(im,Q,UV,I,O):
    # a parte de baixo da cabeça (pescoço) tem outro tom que o pescoço do corpo: degradê no atlas até o tom do corpo
    A=np.asarray(im).astype(float); H,Wd=A.shape[:2]
    hy=Q[O==1,1]; y0=hy.min(); y1=y0+(hy.max()-y0)*0.15
    def samp(m):
        uv=UV[m]; return A[np.clip((uv[:,1]*H).astype(int),0,H-1),np.clip((uv[:,0]*Wd).astype(int),0,Wd-1)]
    bodyc=samp((O==0)&(Q[:,1]>y0-6)&(Q[:,1]<y0+2)).mean(0)
    headc=samp((O==1)&(Q[:,1]<y0+3)).mean(0)
    gain=bodyc/np.maximum(headc,1)
    F=np.ones((H,Wd)); done=np.zeros((H,Wd),bool)
    for tri in I[(O[I]==1).all(1)]:
        if Q[tri,1].min()>y1: continue
        u=UV[tri,0]*Wd; w=UV[tri,1]*H; yy=Q[tri,1]
        x0,x1=int(max(0,u.min()-1)),int(min(Wd-1,u.max()+1)); r0,r1=int(max(0,w.min()-1)),int(min(H-1,w.max()+1))
        gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(r0,r1+1)+.5)
        d=(w[1]-w[2])*(u[0]-u[2])+(u[2]-u[1])*(w[0]-w[2])
        if abs(d)<1e-9: continue
        l0=((w[1]-w[2])*(gx-u[2])+(u[2]-u[1])*(gy-w[2]))/d; l1=((w[2]-w[0])*(gx-u[2])+(u[0]-u[2])*(gy-w[2]))/d; l2=1-l0-l1
        m=(l0>=-0.02)&(l1>=-0.02)&(l2>=-0.02)
        yv=l0*yy[0]+l1*yy[1]+l2*yy[2]; t=np.clip((y1-yv)/(y1-y0),0,1)
        F[r0:r1+1,x0:x1+1][m]=t[m]; done[r0:r1+1,x0:x1+1][m]=True
    F=ndimage.gaussian_filter(F,3)
    G=1+(gain[None,None,:]-1)*F[...,None]
    print('pescoço: ganho',gain.round(3))
    return Image.fromarray(np.clip(A*G,0,255).astype(np.uint8))
def tint(im,Q,UV,O):
    # cor por vértice (o shader multiplica a textura por ela): o pescoço do corpo escurece em degradê até o tom da
    # parte de baixo da cabeça (sem anel na emenda) e os pés recebem o tom do tornozelo
    A=np.asarray(im.resize((1024,2048))).astype(float); H,Wd=A.shape[:2]
    def samp(m):
        uv=UV[m]; return A[np.clip((uv[:,1]*H).astype(int),0,H-1),np.clip((uv[:,0]*Wd).astype(int),0,Wd-1)]
    C=np.ones((len(Q),3))
    y0=Q[O==1,1].min()
    headc=np.median(samp((O==1)&(Q[:,1]<y0+3)),0); bodyc=np.median(samp((O==0)&(Q[:,1]>y0-4)),0)
    g=np.clip(headc/np.maximum(bodyc,1),0.6,1)
    t=np.clip((Q[:,1]-(y0-14))/14,0,1)[:,None]*(O==0)[:,None]
    C=C*(1-t)+g*t if NECK_TINT else C
    yb=Q[:,1].min(); h=Q[:,1].max()-yb
    ank=(O==0)&(Q[:,1]>yb+h*0.11)&(Q[:,1]<yb+h*0.14); ft=(O==0)&(Q[:,1]<yb+h*0.105)
    if ank.any() and ft.any():
        gf=np.clip(np.median(samp(ank),0)/np.maximum(np.median(samp(ft),0),1),0.5,1); s_=np.clip((yb+h*0.105-Q[ft,1])/(h*0.03),0,1)[:,None]; C[ft]=1-(1-gf)*s_
    print('pescoço',g.round(3))
    return np.round(C*255).astype(np.uint8)
def go(sexo, body, head, tex, src_grp, out_grp):
    P,UVs,I=build([(U+body,None),(U+head,'TS4Head_lod0')])
    EP,EU,EI=eyes(U+head); I=np.vstack([I,EI+len(P)]); P=np.vstack([P,EP]); UVs=np.vstack([UVs,EU])
    sv,sidx,fl,tail=E.read_piece('/tmp/ml/app/src/main/assets/cute/p_body_%s1.bin'%src_grp)
    sp=sv['pos'].astype(float)
    # escala/posição: altura e centro iguais ao corpo do Sims 3 (T-pose nos dois)
    k=(sp[:,1].max()-sp[:,1].min())/(P[:,1].max()-P[:,1].min())
    Q=P*k; Q[:,1]+=sp[:,1].min()-Q[:,1].min()
    for ax in (0,2):
        # alinha pelo tronco (y entre 40% e 70% da altura)
        h0,h1=np.percentile(sp[:,1],[40,70]); ms=(sp[:,1]>h0)&(sp[:,1]<h1); mq=(Q[:,1]>h0)&(Q[:,1]<h1)
        Q[:,ax]+=np.median(sp[ms,ax])-np.median(Q[mq,ax])
    O=np.r_[np.array(_ORIG),np.full(len(Q)-len(_ORIG),2)]   # 0 corpo, 1 cabeça, 2 olhos
    # pés: o pé do TS4 é maior que o do Sims 3 e atravessava os sapatos -> cada pé ganha o tamanho/posição do pé do Sims 3
    ya=sp[:,1].min()+(sp[:,1].max()-sp[:,1].min())*0.075
    for side in (1,-1):
        ms=(sp[:,1]<ya)&(np.sign(sp[:,0])==side); mq=(Q[:,1]<ya*1.6)&(np.sign(Q[:,0])==side)&(O==0)
        qf=(Q[:,1]<ya)&mq
        if ms.sum()<5 or qf.sum()<5: continue
        s0,s1=sp[ms].min(0),sp[ms].max(0); q0,q1=Q[qf].min(0),Q[qf].max(0)
        tgt=(Q[mq]-q0)/(q1-q0)*(s1-s0)+s0; tgt[:,1]=Q[mq,1]*0+ (Q[mq,1]-q0[1])/(q1[1]-q0[1])*(s1[1]-s0[1])+s0[1]
        t=np.clip((ya*1.6-Q[mq,1])/(ya*0.6),0,1)[:,None]   # transição suave até a canela
        Q[mq]=Q[mq]*(1-t)+tgt*t
    # olhos: bordas abertas da cabeça (furos dos olhos) -> globos oculares texturizados com o olho do atlas
    N=normals(Q,I)
    # pesos: média dos 6 vizinhos mais próximos no corpo do Sims (peso por distância e por normal parecida)
    sn=sv['nor'].astype(float); tree=cKDTree(sp); d,nb=tree.query(Q,k=8)
    W=np.zeros((len(Q),256))
    bi=sv['bi'].astype(int); bw=sv['bw'].astype(float)/255
    for j in range(8):
        wj=1/(d[:,j]+0.3)**2 * np.clip((N*sn[nb[:,j]]).sum(1)+0.3,0.05,1.3)
        for c in range(4): np.add.at(W,(np.arange(len(Q)),bi[nb[:,j],c]),wj*bw[nb[:,j],c])
    # suaviza os pesos no espaço (cabeça e pescoço do corpo, costuras): vértices vizinhos deformam igual -> sem abrir fresta na nuca
    nbr=cKDTree(Q).query_ball_point(Q,r=2.5)
    W=W/W.sum(1,keepdims=True)
    W2=np.array([W[n_].mean(0) for n_ in nbr]); nk_=(O!=2)&(Q[:,1]>Q[O==1,1].min()-10)   # só cabeça/pescoço (mãos e dedos ficam como estão)
    W=np.where(nk_[:,None],W2,W)
    top=np.argsort(-W,axis=1)[:,:4]; tw=np.take_along_axis(W,top,1); tw/=tw.sum(1,keepdims=True)
    q=np.round(tw*255).astype(int); q[:,0]+=255-q.sum(1)
    A=np.asarray(Image.open(U+tex).convert('RGBA')).astype(float)
    have=(A[...,3]>200)&(A[...,:3].sum(2)>60)   # fundo transparente/preto entre as ilhas vira a cor vizinha (sem linha nas costuras)
    have=ndimage.binary_erosion(have,iterations=4)   # as bordas das ilhas do atlas têm linha escura
    ii=ndimage.distance_transform_edt(~have,return_distances=False,return_indices=True)
    im=Image.fromarray(A[...,:3][ii[0],ii[1]].astype(np.uint8)).resize((1024,2048),Image.LANCZOS)
    # normais iguais em vértices na mesma posição (costuras de UV e emenda cabeça/corpo): sem linha de luz
    grp_=cKDTree(Q).query_ball_point(Q,r=0.35)
    N=np.array([N[[j for j in g_ if (O[j]==2)==(O[i]==2)]].sum(0) for i,g_ in enumerate(grp_)]); N/=np.linalg.norm(N,axis=1,keepdims=True)+1e-12
    v=np.zeros(len(Q),E.DT); v['pos']=Q; v['nor']=N
    v['uv']=UVs; v['col']=255; v['col'][:,:3]=tint(im,Q,UVs,O); v['bi']=top; v['bw']=q
    assert len(v)<65535
    E.write_piece('/tmp/s4/p_body_%s5.bin'%out_grp, v, I.astype(np.uint16), fl, tail)
    im.save('/tmp/s4/sk_s4%s.png'%sexo,optimize=True)
    print(out_grp,len(v),len(I),'escala',k)
    return Q,I
go('f','b676d3f0-FemaleBodMesh_OBJ.obj','8e063fe5-FemaleHeadMesh_OBJ.obj','8231880d-image.png','af','af')
go('m','9b0bb74c-MaleBodyMesh_OBJ.obj','a625f04d-MaleHeadMesh_OBJ.obj','9cfa0126-image.png','am','am')
