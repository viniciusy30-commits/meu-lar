"""Etapa 90f: clipes do app (55 ossos) refeitos para girar em volta das juntas do esqueleto ORIGINAL do TS4.
Cada osso mantém a rotação do clipe original; a posição de cada junta é refeita por cinemática direta com os
comprimentos de osso do TS4 (assim o cotovelo dobra no cotovelo do TS4, o ombro no ombro do TS4 etc.)."""
import sys, json, numpy as np
sys.argv=['x','/tmp/ml/app/src/main/assets/cute']; sys.path.insert(0,'/tmp/ml/ferramentas')
import etapa48_jovem as E
from etapa11_base import GP, NAMES
CU='/tmp/ml/app/src/main/assets/cute/'
S4={}
for l in open(CU+'skel_s4.txt'):
    if l.startswith('#'): continue
    f=l.strip().split('|'); S4[f[1]]=np.array([float(x) for x in f[3:6]])
def j55(grp):
    xf=json.load(open('/tmp/s4/xf_%s.json'%grp)); k=xf['k']; off=np.array(xf['off'])
    w=lambda n: S4[n]*k+off
    J=np.zeros((55,3))
    J[0]=w('b__Pelvis__'); J[2]=w('b__Spine0__'); J[1]=(J[0]+J[2])/2; J[3]=(J[2]+w('b__Spine1__'))/2; J[4]=w('b__Spine1__'); J[5]=w('b__Spine2__')
    J[6]=w('b__Neck__'); J[8]=w('b__Head__'); J[7]=(J[6]+J[8])/2
    for s,o,f0,l0 in (('L',0,25,17),('R',4,40,21)):
        J[9+o]=w('b__%s_Clavicle__'%s); J[10+o]=w('b__%s_UpperArm__'%s); J[11+o]=w('b__%s_Forearm__'%s); J[12+o]=w('b__%s_Hand__'%s)
        J[l0]=w('b__%s_Thigh__'%s); J[l0+1]=w('b__%s_Calf__'%s); J[l0+2]=w('b__%s_Foot__'%s); J[l0+3]=w('b__%s_Toe__'%s)
        for kk,fn in enumerate(['Index','Mid','Ring','Pinky','Thumb']):
            for j in range(3): J[f0+kk*3+j]=w('b__%s_%s%d__'%(s,fn,j))
    return J
def appjoints(grp):
    # juntas de repouso do app só para a pelve (raiz): o resto vem da cinemática direta
    return None
def convert(grp_src, grp):
    J=j55(grp)
    cl=E.read_clips(CU+'clips_%s.bin'%grp_src); out=[]
    order=sorted(range(55),key=lambda b:0 if GP[b]<0 else 1)  # pais antes dos filhos (GP já é topológico)
    for ln,d in cl:
        nf=len(d); M=d.reshape(nf,55,3,4).astype(float); N=np.zeros_like(M)
        for f in range(nf):
            P=np.zeros((55,3))
            for b in range(55):
                A=M[f,b,:,:3]
                p=GP[b]
                if p<0: P[b]=A@J[b]+M[f,b,:,3]
                else: P[b]=P[p]+M[f,p,:,:3]@(J[b]-J[p])
                N[f,b,:,:3]=A; N[f,b,:,3]=P[b]-A@J[b]
        out.append((ln,N.reshape(nf,55,12)))
    E.write_clips('/tmp/s4/clips_%s5.bin'%grp_src,out)
    return J
if __name__=='__main__':
    for g in ('am','af'):
        J=convert(g,g); print(g,'ok', J[[0,10,11,12,17,18,19]].round(1))
