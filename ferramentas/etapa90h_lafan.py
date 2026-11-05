"""Etapa 90h: retarget genérico (BVH -> 55 ossos do app com as juntas do TS4). Fontes: LAFAN1 (Ubisoft) e Bandai Namco."""
import sys, numpy as np
sys.path.insert(0,'/tmp/s4/anim'); import bvh
from scipy.spatial.transform import Rotation as R, Slerp
exec(open('/tmp/s4/anim/s4clips.py').read().split("if __name__")[0])
SK={'lafan':dict(H='Hips',S=('Spine','Spine1','Spine2'),N='Neck',Hd='Head',
        L=dict(sh='LeftShoulder',ua='LeftArm',fa='LeftForeArm',h='LeftHand',th='LeftUpLeg',ca='LeftLeg',ft='LeftFoot',to='LeftToe'),
        R=dict(sh='RightShoulder',ua='RightArm',fa='RightForeArm',h='RightHand',th='RightUpLeg',ca='RightLeg',ft='RightFoot',to='RightToe')),
    'bandai':dict(H='Hips',S=('Spine','Chest','Chest'),N='Neck',Hd='Head',
        L=dict(sh='Shoulder_L',ua='UpperArm_L',fa='LowerArm_L',h='Hand_L',th='UpperLeg_L',ca='LowerLeg_L',ft='Foot_L',to='Toes_L'),
        R=dict(sh='Shoulder_R',ua='UpperArm_R',fa='LowerArm_R',h='Hand_R',th='UpperLeg_R',ca='LowerLeg_R',ft='Foot_R',to='Toes_R'))}
def maps(k):
    s=SK[k]; S0,S1,S2=s['S']
    MAP={0:(s['H'],S0),1:(S0,S1),2:(S0,S1),3:(S1,S2),4:(S2,s['N']),5:(S2,s['N']),6:(s['N'],s['Hd']),7:(s['N'],s['Hd']),8:(s['Hd'],None)}
    if S1==S2: MAP[3]=(S0,S1); MAP[4]=(S1,s['N']); MAP[5]=(S1,s['N'])
    CH={0:2,1:2,2:3,3:4,4:5,5:6,6:8,7:8}
    for side,o,l0 in (('L',0,17),('R',4,21)):
        d=s[side]
        MAP.update({9+o:(d['sh'],d['ua']),10+o:(d['ua'],d['fa']),11+o:(d['fa'],d['h']),12+o:(d['h'],None),
                    l0:(d['th'],d['ca']),l0+1:(d['ca'],d['ft']),l0+2:(d['ft'],d['to']),l0+3:(d['to'],None)})
        CH.update({9+o:10+o,10+o:11+o,11+o:12+o,l0:l0+1,l0+1:l0+2,l0+2:l0+3})
    return MAP,CH
def arc(a,b):
    a=a/np.linalg.norm(a); b=b/np.linalg.norm(b); v=np.cross(a,b); c=a@b
    if np.linalg.norm(v)<1e-8: return R.identity()
    return R.from_rotvec(v/np.linalg.norm(v)*np.arctan2(np.linalg.norm(v),c))
_cache={}
def load(path):
    if path not in _cache: _cache[path]=bvh.load(path)
    return _cache[path]
def facing(Wp,ix,k,f):
    s=SK[k]; a=Wp[f,ix[s['L']['th']]]-Wp[f,ix[s['R']['th']]]; fw=np.cross(a,[0,1,0]); fw[1]=0
    return fw/np.linalg.norm(fw)
def retarget(path,k,grp,F0,F1,old_clip,loop=True,mode='inplace',fps_out=60,warp=None,yaw_from='face',cal=None,tmap=None,relax=None):
    n,p,ft,Wp,Wr=load(path); ix={kk:i for i,kk in enumerate(n)}
    MAP,CH=maps(k); J=j55(grp)
    F=list(range(F0,F1+1)); T=F1-F0
    if yaw_from=='travel':
        tr=Wp[F1,ix[SK[k]['H']]]-Wp[F0,ix[SK[k]['H']]]; fw=tr.copy(); fw[1]=0; fw/=np.linalg.norm(fw)
    else: fw=np.mean([facing(Wp,ix,k,f) for f in F],0); fw/=np.linalg.norm(fw)
    Y=R.from_euler('y',-np.arctan2(fw[0],fw[2]))
    Wp=Y.apply(Wp.reshape(-1,3)).reshape(Wp.shape); Wr=[Y*w for w in Wr]
    # calibração: quadro em T-pose (LAFAN: quadro 0), girado para olhar para +z
    f0=F0 if cal is None else cal
    if isinstance(cal,tuple):   # T-pose de outra captura (mesmo esqueleto)
        n2,p2,ft2,Wp2,Wr2=load(cal[0]); f0=cal[1]
        Wp=Wp.copy(); Wr=list(Wr)
        Wp_cal=Wp2; Wr_cal=Wr2
    else: Wp_cal=Wp; Wr_cal=Wr
    cf=facing(Wp_cal,ix,k,f0); Yc=R.from_euler('y',-np.arctan2(cf[0],cf[2]))
    Rb0={}; W0={}
    for b,(jn,cn) in MAP.items():
        W0[b]=Yc*Wr_cal[ix[jn]][f0]
        if cn is not None: Rb0[b]=arc(J[CH[b]]-J[b], Yc.apply(Wp_cal[f0,ix[cn]]-Wp_cal[f0,ix[jn]]))
    for b,(jn,cn) in MAP.items():
        if cn is None: Rb0[b]=Rb0[{8:6,12:11,16:15,20:19,24:23}[b]]
    if cal is None:
        for b in range(1,9): Rb0[b]=Rb0[0]   # sem T-pose: tronco/cabeça mantêm a postura de repouso
    oldM=old_clip[0].reshape(55,3,4); s=np.cbrt(np.linalg.det(oldM[0,:,:3])); oldR=[R.from_matrix(oldM[b,:,:3]/s) for b in range(55)]
    H=ix[SK[k]['H']]
    stand=np.percentile(Wp[:,H,1],90)   # altura do quadril em pé nesta captura
    kk=J[0][1]/stand
    root0=Wp[F0,H].copy(); drift=(Wp[F1,H]-root0)/max(T,1)
    out=[]
    for q,f in enumerate(F):
        Rb={b:Wr[ix[jn]][f]*W0[b].inv()*Rb0[b] for b,(jn,cn) in MAP.items()}
        if relax is not None:   # braços soltos (o clipe antigo, relativos ao peito): para capturas segurando arma
            rM=relax.reshape(55,3,4); rR=[R.from_matrix(rM[b,:,:3]/s) for b in range(55)]
            for b in range(9,17): Rb[b]=Rb[5]*rR[5].inv()*rR[b]
        for hb,fb in ((12,25),(16,40)):
            for j in range(15): Rb[fb+j]=Rb[hb]*oldR[hb].inv()*oldR[fb+j]
        P=np.zeros((55,3)); rp=Wp[f,H]-root0
        if loop: rp=rp-drift*q
        rp[1]=Wp[f,H,1]-stand
        if mode=='jump': rp[1]=min(rp[1],0.0)          # o jogo faz o voo; o clipe só agacha/encolhe
        P[0]=np.array([rp[0]*kk*0.5, J[0][1]+rp[1]*kk, rp[2]*kk*(0.5 if loop else 0.0)])
        for b in range(1,55): P[b]=P[GP[b]]+Rb[GP[b]].apply(J[b]-J[GP[b]])
        out.append((Rb,P))
    if mode!='jump':
        lo=np.array([[o[1][20][1],o[1][24][1]] for o in out]).min()
        dy=min(J[20][1],J[24][1])-lo
        if mode=='crouch': dy=min(J[20][1],J[24][1])-np.array([[o[1][20][1],o[1][24][1]] for o in out]).min()
    else: dy=0
    tt=np.arange(T+1)*ft; L=T*ft
    if warp: L=warp
    if tmap:
        L=tmap[-1][0]; no=int(round(L*fps_out)); to=np.linspace(0,L,no)
        ts=np.interp(to,[a for a,b in tmap],[(b-F0)*ft for a,b in tmap])
    else:
        no=int(round(L*fps_out)); ts=np.linspace(0,T*ft,no,endpoint=not loop)
    M=np.zeros((no,55,3,4))
    for b in range(55):
        sl=Slerp(tt,R.concatenate([o[0][b] for o in out]))
        Pb=np.array([o[1][b] for o in out]); Pb[:,1]+=dy
        rr=sl(ts).as_matrix(); pp=np.array([np.interp(ts,tt,Pb[:,c]) for c in range(3)]).T
        M[:,b,:,:3]=rr*s; M[:,b,:,3]=pp*s-np.einsum('nij,j->ni',rr*s,J[b])
    if loop:
        nb=max(3,no//7)
        for i in range(nb):
            a=(i+1)/(nb+1); M[no-nb+i]=M[no-nb+i]*(1-a)+M[0]*a
    return L, M.reshape(no,55,12).astype(np.float32)
