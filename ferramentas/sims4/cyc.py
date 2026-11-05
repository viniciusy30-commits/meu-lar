import numpy as np
def cycles(Wp,ix,k,a,b,vmin,vmax,ft):
    from rt2 import SK
    s=SK[k]; H=Wp[:,ix[s['H']]]
    out=[]
    for f in range(a+1,b-1):
        pass
    L=Wp[:,ix[s['L']['ft']]]; Rr=Wp[:,ix[s['R']['ft']]]
    fw=np.cross(Wp[:,ix[s['L']['th']]]-Wp[:,ix[s['R']['th']]],[0,1,0]); fw[:,1]=0; fw/=np.linalg.norm(fw,axis=1,keepdims=True)
    sig=np.einsum('ij,ij->i',L-Rr,fw)
    zc=[f for f in range(a,b-1) if sig[f]<0<=sig[f+1]]
    for i in range(len(zc)-1):
        f0,f1=zc[i],zc[i+1]; v=np.linalg.norm(H[f1,[0,2]]-H[f0,[0,2]])/((f1-f0)*ft)
        turn=np.degrees(np.arccos(np.clip(fw[f0]@fw[f1],-1,1)))
        if vmin<=v<=vmax and turn<8: out.append((f0,f1,int(v),int(turn)))
    return out
