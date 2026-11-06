from geo import *
import cv2
S=1024
def inpaint_skin():
    """pele do corpo SEM o sutiã (alças e bojo pintados na textura) — usada por baixo da renda e nas aberturas"""
    sk=np.asarray(Image.open(CU+'sk_s4f.png').convert('RGB')); H,W=sk.shape[:2]
    f=sk.astype(float); m=(f[...,2]>=f[...,0]*0.80); m[:H//2]=False; m[:,W//2:]=False; m[int(H*0.655):]=False   # só o sutiã (a calcinha fica)
    md=cv2.dilate(m.astype(np.uint8),np.ones((5,5),np.uint8))
    out=cv2.inpaint(cv2.cvtColor(sk,cv2.COLOR_RGB2BGR),md,6,cv2.INPAINT_TELEA)
    out=cv2.cvtColor(out,cv2.COLOR_BGR2RGB)
    return out,cv2.dilate(md,np.ones((13,13),np.uint8)).astype(bool),sk
def raster_atlas(P0,UVp,I,keep):
    """para cada texel do atlas S×S: triângulo + baricêntricas; devolve posição 3D (S,S,3) e máscara de cobertura"""
    POS=np.zeros((S,S,3)); COV=np.zeros((S,S),bool); TID=-np.ones((S,S),int)
    for t in keep:
        a,b,c=I[t]; u=UVp[[a,b,c],0]*S; v=UVp[[a,b,c],1]*S
        x0,x1=int(max(0,np.floor(u.min()))),int(min(S-1,np.ceil(u.max()))); y0,y1=int(max(0,np.floor(v.min()))),int(min(S-1,np.ceil(v.max())))
        if x1<x0 or y1<y0: continue
        gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        d=(v[1]-v[2])*(u[0]-u[2])+(u[2]-u[1])*(v[0]-v[2])
        if abs(d)<1e-9: continue
        l0=((v[1]-v[2])*(gx-u[2])+(u[2]-u[1])*(gy-v[2]))/d; l1=((v[2]-v[0])*(gx-u[2])+(u[0]-u[2])*(gy-v[2]))/d; l2=1-l0-l1
        m=(l0>=-0.02)&(l1>=-0.02)&(l2>=-0.02)
        if not m.any(): continue
        ys=(gy[m]-.5).astype(int); xs=(gx[m]-.5).astype(int)
        POS[ys,xs]=l0[m,None]*P0[a]+l1[m,None]*P0[b]+l2[m,None]*P0[c]; COV[ys,xs]=True; TID[ys,xs]=t
    return POS,COV,TID
def body_uv_at(Q,sv,si):
    """UV do corpo no ponto mais próximo da superfície do corpo (triângulo a triângulo; sem confundir as ilhas de UV)"""
    sp=sv['pos'].astype(float); suv=sv['uv'].astype(float)
    A=sp[si[:,0]];B=sp[si[:,1]];C=sp[si[:,2]]; cen=(A+B+C)/3

    kd=cKDTree(cen); out=np.zeros((len(Q),2)); dist=np.zeros(len(Q))
    for s0 in range(0,len(Q),60000):
        q=Q[s0:s0+60000]; _,cand=kd.query(q,k=10)
        a=A[cand];b=B[cand];c=C[cand]; p=q[:,None,:]
        ab=b-a; ac=c-a; ap=p-a
        d00=(ab*ab).sum(2);d01=(ab*ac).sum(2);d11=(ac*ac).sum(2);d20=(ap*ab).sum(2);d21=(ap*ac).sum(2)
        den=d00*d11-d01*d01; den=np.where(np.abs(den)<1e-12,1e-12,den)
        v=(d11*d20-d01*d21)/den; w=(d00*d21-d01*d20)/den; u=1-v-w
        u=np.clip(u,0,None);v=np.clip(v,0,None);w=np.clip(w,0,None); sm=u+v+w; u/=sm;v/=sm;w/=sm
        cp=u[...,None]*a+v[...,None]*b+w[...,None]*c; dd=np.linalg.norm(p-cp,axis=2)
        j=dd.argmin(1); r=np.arange(len(q)); tri=cand[r,j]
        uu=u[r,j];vv=v[r,j];ww=w[r,j]
        out[s0:s0+60000]=uu[:,None]*suv[si[tri,0]]+vv[:,None]*suv[si[tri,1]]+ww[:,None]*suv[si[tri,2]]
        dist[s0:s0+60000]=dd[r,j]
    return out,dist
def sample(img,uv):
    H,W=img.shape[:2]; x=np.clip(uv[:,0]*W-0.5,0,W-1.001); y=np.clip(uv[:,1]*H-0.5,0,H-1.001)
    x0=x.astype(int);y0=y.astype(int);fx=(x-x0)[:,None];fy=(y-y0)[:,None]
    f=img.astype(float)
    return (f[y0,x0]*(1-fx)*(1-fy)+f[y0,x0+1]*fx*(1-fy)+f[y0+1,x0]*(1-fx)*fy+f[y0+1,x0+1]*fx*fy)
