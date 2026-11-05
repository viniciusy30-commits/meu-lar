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
def build(objs):
    # vertices únicos por (arquivo, v, vt); uv já no atlas (v de cima para baixo)
    P=[];UV=[];I=[];key={}
    for f,grp in objs:
        V,T,F=rd(f,grp)
        head = grp is not None
        for tri in F:
            if not head and min(V[vi][1] for vi,_ in tri) > 1.63: continue      # o corpo do TS4 traz uma cabeça simples: fica a cabeça detalhada
            for vi,ti in tri:
                k=(f,vi,ti)
                if k not in key:
                    key[k]=len(P); P.append(V[vi])
                    u,v=T[ti]
                    UV.append((u, 1-v) if head else (u, 0.5+(1-v)*0.5))   # corpo: textura assada na metade de baixo do atlas (bake.py)
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
    # olhos: bordas abertas da cabeça (furos dos olhos) -> globos oculares texturizados com o olho do atlas
    N=normals(Q,I)
    # pesos: média dos 6 vizinhos mais próximos no corpo do Sims (peso por distância e por normal parecida)
    sn=sv['nor'].astype(float); tree=cKDTree(sp); d,nb=tree.query(Q,k=8)
    W=np.zeros((len(Q),256))
    bi=sv['bi'].astype(int); bw=sv['bw'].astype(float)/255
    for j in range(8):
        wj=1/(d[:,j]+0.3)**2 * np.clip((N*sn[nb[:,j]]).sum(1)+0.3,0.05,1.3)
        for c in range(4): np.add.at(W,(np.arange(len(Q)),bi[nb[:,j],c]),wj*bw[nb[:,j],c])
    top=np.argsort(-W,axis=1)[:,:4]; tw=np.take_along_axis(W,top,1); tw/=tw.sum(1,keepdims=True)
    q=np.round(tw*255).astype(int); q[:,0]+=255-q.sum(1)
    v=np.zeros(len(Q),E.DT); v['pos']=Q; v['nor']=N
    v['uv']=UVs; v['col']=255; v['bi']=top; v['bw']=q
    assert len(v)<65535
    E.write_piece('/tmp/s4/p_body_%s5.bin'%out_grp, v, I.astype(np.uint16), fl, tail)
    im=Image.open(U+tex).convert('RGB').resize((1024,2048),Image.LANCZOS)
    im=bake(im, v, I, src_grp, U+tex)
    im.save('/tmp/s4/sk_s4%s.png'%sexo,optimize=True)
    print(out_grp,len(v),len(I),'escala',k)
    return Q,I
go('m','d73f136a-MaleBodyMesh_OBJ.obj','a625f04d-MaleHeadMesh_OBJ.obj','9cfa0126-image.png','am','am')
go('f','bff5d4f1-FemaleBodMesh_OBJ.obj','8e063fe5-FemaleHeadMesh_OBJ.obj','8231880d-image.png','af','af')
