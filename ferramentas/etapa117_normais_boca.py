# Etapa 117: suaviza as normais da malha em volta da boca (o vinco entre labio e pele criava uma aureola clara com a luz).
# Uso: python3 etapa117_normais_boca.py <cute entrada> <cute saida>   (so reescreve as normais de p_body_am5.bin / p_body_af5.bin)
import sys, struct, numpy as np
from collections import defaultdict
DT=np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)])
cin,cout=sys.argv[1],sys.argv[2]
for g in ('am5','af5'):
    raw=bytearray(open(f'{cin}/p_body_{g}.bin','rb').read()); nv,ni,fl=struct.unpack('<3i',raw[4:16])
    v=np.frombuffer(bytes(raw[16:16+nv*44]),DT).copy(); idx=np.frombuffer(bytes(raw[16+nv*44:16+nv*44+ni*2]),'<u2').reshape(-1,3).astype(int)
    P=v['pos'].astype(float); N0=v['nor'].astype(float)
    key=np.round(P,3); uniq={}; wid=np.zeros(nv,int)
    for i,k in enumerate(map(tuple,key)): wid[i]=uniq.setdefault(k,len(uniq))
    nu=len(uniq)
    fn=np.cross(P[idx[:,1]]-P[idx[:,0]],P[idx[:,2]]-P[idx[:,0]])
    acc=np.zeros((nu,3))
    for t,n in zip(idx,fn):
        for i in t: acc[wid[i]]+=n
    # vizinhos por posicao soldada
    nb=defaultdict(set)
    for t in idx:
        for a in range(3):
            for b in range(3):
                if a!=b: nb[wid[t[a]]].add(wid[t[b]])
    nrm=lambda a:a/np.maximum(np.linalg.norm(a,axis=1,keepdims=True),1e-9)
    S=nrm(acc)
    # regiao da boca (cm): ao redor do centro dos labios
    upos=np.zeros((nu,3)); upos[wid]=P
    c=np.median(P[np.abs(P[:,0])<0.5][:,1:],axis=0) if False else None
    # centro: vertices cujo uv cai no miolo da boca (atlas 1024x2048)
    uv=v['uv'].astype(float); px=uv[:,0]*1024; py=uv[:,1]*2048
    core=(np.abs(px-513)<48)&(np.abs(py-862)<20)
    cen=P[core].mean(0)
    dist=np.linalg.norm((upos-cen)*np.array([1,1.3,1]),axis=1)
    R0,R1=3.2,5.6   # cm: ate R0 suavizacao total, some ate R1
    w=np.clip((R1-dist)/(R1-R0),0,1)*np.clip((dist-2.0)/0.8,0,1)   # nao mexe nos labios/fresta (dentro de 2 cm do centro)
    for it in range(6):
        S2=S.copy()
        for u,ns in nb.items():
            if w[u]>0:
                m=S[list(ns)].mean(0)+S[u]
                S2[u]=m/np.linalg.norm(m)
        S=S2
    Nu=nrm(acc)*0  # novo = mistura do antigo (por vertice) com o suavizado
    new=N0.copy()
    for i in range(nv):
        u=wid[i]; wi=w[u]
        if wi<=0: continue
        s=S[u]
        if np.dot(s,N0[i])<0: s=-s
        m=N0[i]*(1-wi)+s*wi; new[i]=m/np.linalg.norm(m)
    v['nor']=new.astype('<f4')
    raw[16:16+nv*44]=v.tobytes()
    open(f'{cout}/p_body_{g}.bin','wb').write(raw)
    print(g,'verts alterados',int((w[wid]>0).sum()),'dist centro',cen.round(2))
