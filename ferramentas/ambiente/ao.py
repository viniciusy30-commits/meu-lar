import numpy as np, math
def bake_ao(A,voxel=0.02,rays=24,maxd=0.45,strength=0.62,seed=1):
    """oclusão ambiente por vértice, calculada na malha do próprio objeto (grade de voxels)."""
    arrs=A.arrays()
    allP=np.vstack([a[1] for a in arrs]); lo=allP.min(0)-0.5; hi=allP.max(0)+0.5
    dims=np.ceil((hi-lo)/voxel).astype(int)+1
    occ=np.zeros(dims,bool)
    for key,P,N,C,UV,T in arrs:
        T=np.asarray(T,int)
        a=P[T[:,0]];b=P[T[:,1]];c=P[T[:,2]]
        area=np.linalg.norm(np.cross(b-a,c-a),axis=1)/2
        n=np.clip((area/(voxel*voxel*0.5)).astype(int)+1,1,400)
        rng=np.random.default_rng(seed)
        for k in np.unique(n):
            m=n==k
            u=rng.random((m.sum(),k,1)); v=rng.random((m.sum(),k,1)); f=u+v>1; u=np.where(f,1-u,u); v=np.where(f,1-v,v)
            pts=a[m][:,None]+u*(b[m]-a[m])[:,None]+v*(c[m]-a[m])[:,None]
            pts=np.concatenate([pts.reshape(-1,3),a[m],b[m],c[m]])
            ix=((pts-lo)/voxel).astype(int); occ[ix[:,0],ix[:,1],ix[:,2]]=True
    rng=np.random.default_rng(seed)
    # direcoes no hemisferio (cosseno ponderado)
    r1=rng.random(rays); r2=rng.random(rays); ph=2*np.pi*r2; rr=np.sqrt(r1)
    local=np.stack([rr*np.cos(ph),rr*np.sin(ph),np.sqrt(1-r1)],1)
    steps=np.arange(0.05,maxd,voxel*1.5)
    res={}
    for key,P,N,C,UV,T in arrs:
        nl=np.linalg.norm(N,axis=1); ok=nl>0.2
        n=np.where(ok[:,None],N/np.maximum(nl[:,None],1e-9),np.array([0,1,0.]))
        up=np.where(np.abs(n[:,1:2])<0.9,np.array([0,1,0.]),np.array([1,0,0.]))
        t1=np.cross(n,up); t1/=np.linalg.norm(t1,axis=1,keepdims=True); t2=np.cross(n,t1)
        D=local[None,:,0:1]*t1[:,None]+local[None,:,1:2]*t2[:,None]+local[None,:,2:3]*n[:,None]   # (V,R,3)
        org=P+n*0.012
        hit=np.zeros((len(P),rays))
        for s in steps:
            q=org[:,None]+D*s; ix=((q-lo)/voxel).astype(int)
            ix=np.clip(ix,0,dims-1)
            h=occ[ix[...,0],ix[...,1],ix[...,2]]
            w=(1-s/maxd)
            hit=np.maximum(hit,h*w)
        o=hit.mean(1)
        k=1-strength*np.clip(o*1.6,0,1)
        res[key]=np.where(ok,k,1.0)
    # aplica
    for key,a in A.parts.items():
        k=res[key]; off=0
        for i,C in enumerate(a['C']):
            n=len(C); C=np.asarray(C,float).copy(); C[:,:3]*=k[off:off+n,None]; a['C'][i]=C; off+=n
    return A
