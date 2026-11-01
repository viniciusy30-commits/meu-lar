import sys;sys.path.insert(0,'/home/claude/proj/codigo/ferramentas')
import numpy as np
from etapa14_poselib import *
from etapa14_clips import curl_fingers
import os
ARM_ABD=float(os.environ.get('ARM_ABD','9'));FORE_BACK=float(os.environ.get('FORE_BACK','5'))
p=Poser(BASE);cl=p.base['clips']
def male_edit(D,pos,par):
    # coluna: base da coluna para frente (pelve sob o tronco), peito aberto, cabeça nivelada
    Poser.rot(D,pos,1,Rx(deg(par['lean'])))
    Poser.rot(D,pos,3,Rx(-deg(par['chest'])))
    Poser.rot(D,pos,6,Rx(-deg(par['lean']-par['chest'])*0.6))
    Poser.rot(D,pos,8,Rx(-deg(par['lean']-par['chest'])*0.4+deg(par['chin'])))
    for s in (+1,-1):
        o=0 if s>0 else 4
        th,ft=17+o,19+o
        Poser.rot(D,pos,th,Rz(s*deg(par['hip_abd'])))
        Poser.rot(D,pos,ft,Rz(-s*deg(par['hip_abd'])))
        Poser.rot(D,pos,ft,Ry(s*deg(par['toe_out'])))
        # ombros levemente para trás/baixo
        Poser.rot(D,pos,9+(0 if s>0 else 4),Rz(-s*deg(par['shoulder_drop'])))
        Poser.rot(D,pos,11+o,Rz(-s*deg(par['fore_in'])))
        # Etapa 27: braço (parte de cima) mais aberto, antebraço volta para manter a mão perto da coxa
        Poser.rot(D,pos,10+o,Rz(s*deg(par.get('arm_abd',0.0))))
        Poser.rot(D,pos,11+o,Rz(-s*deg(par.get('fore_back',0.0))))
IDLE_M=dict(lean=4.0,chest=3.0,chin=0.0,hip_abd=2.2,toe_out=7,shoulder_drop=0.0,fore_in=0,curl=(18,30,18),arm_abd=ARM_ABD,fore_back=FORE_BACK)
WALK_M=dict(lean=2.0,chest=2.0,chin=0.0,hip_abd=2.0,toe_out=3,shoulder_drop=0.0,fore_in=0,curl=(18,30,18),arm_abd=ARM_ABD,fore_back=FORE_BACK)
def make(clip,par):
    ln,d=clip;out=[]
    for f in range(len(d)):
        D,pos=p.world(d[f].astype(np.float64));male_edit(D,pos,par);out.append(p.pack(D,pos))
    out=np.array(out)
    low0=min(p.rt.foot_low(f.astype(np.float64)) for f in d);low1=min(p.rt.foot_low(f.astype(np.float64)) for f in out)
    out[:,:,7]+=(low0-low1)
    return ln,out.astype(np.float32)
if __name__=='__main__':
    new=[(l,d.copy()) for l,d in cl]
    new[4]=make(cl[0],IDLE_M);new[5]=make(cl[1],WALK_M)
    import os;os.makedirs('/tmp/etapa27_saida',exist_ok=True)
    write_base('/tmp/base_new.bin',p.base,new)
    print('ok',[(round(l,2),d.shape[0]) for l,d in new])
