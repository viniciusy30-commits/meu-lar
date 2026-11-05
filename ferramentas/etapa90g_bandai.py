"""Etapa 90g: andar/correr de captura de movimento (Bandai Namco Research Motion Dataset, uso não comercial)
passados para os 55 ossos do app com as juntas do esqueleto original do TS4.
Cada osso copia a DIREÇÃO do osso da captura (e o giro dele a partir de um quadro de calibração);
as posições saem por cinemática direta com os comprimentos do TS4 (sem esticar nada)."""
import sys, numpy as np
sys.path.insert(0,'/tmp/s4/anim')
import bvh
from scipy.spatial.transform import Rotation as R, Slerp
exec(open('/tmp/s4/anim/s4clips.py').read().split("if __name__")[0])
MAP={0:('Hips','Spine'),1:('Spine','Chest'),2:('Spine','Chest'),3:('Spine','Chest'),4:('Chest','Neck'),5:('Chest','Neck'),
     6:('Neck','Head'),7:('Neck','Head'),8:('Head',None)}
CH={0:2,1:2,2:3,3:4,4:5,5:6,6:8,7:8}
for s,o,l0 in (('L',0,17),('R',4,21)):
    MAP.update({9+o:('Shoulder_'+s,'UpperArm_'+s),10+o:('UpperArm_'+s,'LowerArm_'+s),11+o:('LowerArm_'+s,'Hand_'+s),12+o:('Hand_'+s,None),
                l0:('UpperLeg_'+s,'LowerLeg_'+s),l0+1:('LowerLeg_'+s,'Foot_'+s),l0+2:('Foot_'+s,'Toes_'+s),l0+3:('Toes_'+s,None)})
    CH.update({9+o:10+o,10+o:11+o,11+o:12+o,l0:l0+1,l0+1:l0+2,l0+2:l0+3})
def arc(a,b):
    a=a/np.linalg.norm(a); b=b/np.linalg.norm(b); v=np.cross(a,b); c=a@b
    if np.linalg.norm(v)<1e-8: return R.identity()
    return R.from_rotvec(v/np.linalg.norm(v)*np.arctan2(np.linalg.norm(v),c))
def retarget(path,grp,old_clip,period=None,fps_out=60):
    n,p,ft,Wp,Wr=bvh.load(path); ix={k:i for i,k in enumerate(n)}; nf=len(Wp)
    J=j55(grp)
    # direção de caminhada -> +z
    tr=Wp[-1,ix['Hips']]-Wp[0,ix['Hips']]; yaw=np.arctan2(tr[0],tr[2]); Y=R.from_euler('y',-yaw)
    Wp=Y.apply(Wp.reshape(-1,3)).reshape(Wp.shape); Wr=[Y*w for w in Wr]
    # ciclo: período com a pose mais parecida (relativa ao quadril), no meio da captura
    rel=Wp-Wp[:,ix['Hips']:ix['Hips']+1]
    sig=rel[:,ix['Foot_L'],2]-rel[:,ix['Foot_R'],2]
    zc=np.where((sig[:-1]<0)&(sig[1:]>=0))[0]          # pé esquerdo passa à frente: um passo completo (esq+dir) entre dois
    m=len(zc)//2; f1=int(zc[max(0,m-1)]); T=int(zc[max(0,m-1)+1]-f1); F=list(range(f1,f1+T+1))
    print(path.split('/')[-1],'ciclo',f1,T,'quadros',round(T*ft,3),'s')
    # calibração no primeiro quadro do ciclo
    f0=F[0]; Rb0={}
    for b,(jn,cn) in MAP.items():
        if cn is None: continue
        Rb0[b]=arc(J[CH[b]]-J[b], Wp[f0,ix[cn]]-Wp[f0,ix[jn]])
    for b,(jn,cn) in MAP.items():
        if cn is None: Rb0[b]=Rb0[{8:6,12:11,16:15,20:19,24:23}[b]]
    # tronco, pescoço e cabeça: mantêm a postura de repouso do TS4 + o movimento da captura (sem olhar para cima/inclinar)
    for b in range(1,9): Rb0[b]=Rb0[0]
    # dedos: giro relativo à mão copiado do clipe antigo (quadro 0)
    oldM=old_clip[0].reshape(55,3,4); s=np.cbrt(np.linalg.det(oldM[0,:,:3]))
    oldR=[R.from_matrix(oldM[b,:,:3]/s) for b in range(55)]
    hips_h=np.median(Wp[:,ix['Hips'],1]); k=(J[0][1]-0)/hips_h
    out=[]
    root0=Wp[F[0],ix['Hips']]; drift=(Wp[F[-1],ix['Hips']]-root0)/T
    for q,f in enumerate(F):
        Rb={}
        for b,(jn,cn) in MAP.items(): Rb[b]=Wr[ix[jn]][f]*Wr[ix[jn]][f0].inv()*Rb0[b]
        for side,hb,f0b in (('L',12,25),('R',16,40)):
            for j in range(15): Rb[f0b+j]=Rb[hb]*oldR[hb].inv()*oldR[f0b+j]
        P=np.zeros((55,3))
        rp=Wp[f,ix['Hips']]-root0-drift*q; rp[1]=Wp[f,ix['Hips'],1]
        P[0]=np.array([rp[0]*k*0.6, rp[1]*k, rp[2]*k*0.6])   # no lugar (o jogo move o personagem)
        for b in range(1,55): P[b]=P[GP[b]]+Rb[GP[b]].apply(J[b]-J[GP[b]])
        out.append((Rb,P))
    # pé no chão: menor altura dos dedos/pés no ciclo = altura de repouso
    toes=np.array([[o[1][20][1],o[1][24][1],o[1][19][1]-(J[19][1]-J[20][1]),o[1][23][1]-(J[23][1]-J[24][1])] for o in out]).min()
    dy=min(J[20][1],J[24][1])-toes
    # reamostra para fps_out, fechando o laço
    tt=np.arange(T+1)*ft; L=T*ft; no=int(round(L*fps_out)); ts=np.linspace(0,L,no,endpoint=False)
    M=np.zeros((no,55,3,4))
    for b in range(55):
        rots=R.concatenate([o[0][b] for o in out]); sl=Slerp(tt,rots)
        Pb=np.array([o[1][b] for o in out]); Pb[:,1]+=dy
        Pb[-1]=Pb[0] if b==0 else Pb[-1]
        rr=sl(ts).as_matrix(); pp=np.array([np.interp(ts,tt,Pb[:,c]) for c in range(3)]).T
        M[:,b,:,:3]=rr*s; M[:,b,:,3]=pp*s-np.einsum('nij,j->ni',rr*s,J[b])
    # costura do laço: últimos 15% misturados com o começo
    nb=max(3,no//7)
    for i in range(nb):
        a=(i+1)/(nb+1); M[no-nb+i]=M[no-nb+i]*(1-a)+M[0]*a
    return L, M.reshape(no,55,12).astype(np.float32)
