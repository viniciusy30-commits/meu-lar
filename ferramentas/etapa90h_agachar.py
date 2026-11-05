"""Etapa 90h: andar agachado = pernas do andar novo (passada encurtada) com IK de 2 ossos, pelve na altura do agachar
parado, tronco/braços/cabeça do agachar parado (captura)."""
import numpy as np
from scipy.spatial.transform import Rotation as R
from rt2 import arc, GP
def unpack(M,J):
    M=M.reshape(55,3,4); s=np.cbrt(np.linalg.det(M[0,:,:3]))
    Rb=[R.from_matrix(M[b,:,:3]/s) for b in range(55)]; P=np.array([M[b,:,:3]@J[b]+M[b,:,3] for b in range(55)])/s
    return Rb,P,s
def pack(Rb,P,J,s):
    M=np.zeros((55,3,4))
    for b in range(55): A=Rb[b].as_matrix()*s; M[b,:,:3]=A; M[b,:,3]=P[b]*s-A@J[b]
    return M.reshape(55,12)
def make(walk,idle,J,stride=0.55):
    n=len(walk); ci=idle[len(idle)//2]
    Ri,Pi,s=unpack(ci,J); out=[]
    W=[unpack(walk[f],J) for f in range(n)]
    wr=np.mean([w[1][0] for w in W],0)
    for f in range(n):
        Rw,Pw,_=W[f]
        Rb=list(Ri); P=np.zeros((55,3))
        P[0]=Pi[0]+np.array([0,(Pw[0][1]-wr[1])*0.6,0])
        for b in range(1,55): P[b]=P[GP[b]]+Rb[GP[b]].apply(J[b]-J[GP[b]])
        for th,ca,ft,to in ((17,18,19,20),(21,22,23,24)):
            hip=P[th]
            tgt=Pi[ft]+np.array([0,Pw[ft][1]-min(W[g][1][ft][1] for g in range(n)),(Pw[ft][2]-wr[2])*stride])
            l1=np.linalg.norm(J[ca]-J[th]); l2=np.linalg.norm(J[ft]-J[ca])
            d=tgt-hip; L=np.clip(np.linalg.norm(d),1e-3,l1+l2-1e-3); dn=d/np.linalg.norm(d); tgt=hip+dn*L
            a=np.arccos(np.clip((l1*l1+L*L-l2*l2)/(2*l1*L),-1,1))
            pole=np.array([0,0,1.0]); pole=pole-dn*(pole@dn); pole/=np.linalg.norm(pole)
            knee=hip+dn*np.cos(a)*l1+pole*np.sin(a)*l1
            Rt=arc(J[ca]-J[th],knee-hip)
            Rb[th]=Rt; Rc=arc(J[ft]-J[ca],tgt-knee); Rb[ca]=Rc
            Rb[ft]=Rw[ft]; Rb[to]=Rw[to]
            P[ca]=knee; P[ft]=tgt; P[to]=tgt+Rb[ft].apply(J[to]-J[ft])
        out.append(pack(Rb,P,J,s))
    return np.array(out,dtype=np.float32)
def adjust(clip,J,idle_old,lean=0.6):
    """menos inclinação do tronco e braços soltos pendurados (direção de mundo do parado antigo)"""
    Ro,_,_=unpack(idle_old,J); out=[]
    for f in range(len(clip)):
        Rb,P,s=unpack(clip[f],J)
        for b in range(0,9): Rb[b]=R.from_rotvec(Rb[b].as_rotvec()*lean)
        for b in (10,11,12,14,15,16): Rb[b]=Ro[b]
        for hb,fb in ((12,25),(16,40)):
            for j in range(15): Rb[fb+j]=Rb[hb]*Ro[hb].inv()*Ro[fb+j]
        keep={b:P[b].copy() for b in (17,18,19,20,21,22,23,24)}
        root=P[0].copy()
        for b in range(1,55): P[b]=P[GP[b]]+Rb[GP[b]].apply(J[b]-J[GP[b]])
        out.append(pack(Rb,P,J,s))
    return np.array(out,dtype=np.float32)
