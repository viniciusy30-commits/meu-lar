import sys; sys.path.insert(0,'.')
from etapa10_skel import *
import struct
D2R=np.pi/180
# ---------------- parâmetros ----------------
CYCLE=0.62          # s por ciclo completo (2 passos)
SPEED_M=2.6         # m/s no jogo (casado com Renderer3D.RUN_SPEED)
V=SPEED_M/K         # cm/s no espaço do modelo
DUTY=0.36           # fração do ciclo com o pé no chão
NFR=48
H_MID,H_AMP=89.0,3.2   # altura do quadril (cm): média e amplitude do quique
def sm(a,b,x):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
# ---------------- nuvem do pé (para ancorar no chão) ----------------
b=open('/home/claude/p/work/app/src/main/assets/cute/base.bin','rb').read()
nv,ni,nb,nc=struct.unpack_from('<4i',b,4)
REC=np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)])
VER=np.frombuffer(b,dtype=REC,count=nv,offset=20)
P=VER['pos'].astype(float); BIX=VER['bi']; BW=VER['bw']
dom=BIX[np.arange(nv),BW.argmax(1)]
FOOT=P[(dom==19)]-Pb[19]; BALL=P[(dom==20)]-Pb[20]
BALLREL=Pb[20]-Pb[19]
def ankle_h(p,pb):
    """altura do tornozelo para o ponto mais baixo do pé tocar y=0"""
    R1=Rx(-p*D2R); R2=Rx(-pb*D2R)
    pf=FOOT@R1.T; pbl=(BALL@R2.T)+R1@BALLREL
    return -min(pf[:,1].min(),pbl[:,1].min())
L1=np.linalg.norm(Pb[18]-Pb[17]); L2=np.linalg.norm(Pb[19]-Pb[18])
def foot_pitch_stance(s): return 6*(1-sm(0,0.3,s))-34*sm(0.45,1.0,s)
def ball_pitch_stance(s,p): return p*(1-sm(0.55,0.95,s))
def foot_pitch_swing(u): return -34+16*sm(0,0.3,u)+24*sm(0.45,1.0,u)
def ball_pitch_swing(u,p): return p*(0.5*sm(0,0.2,u)+0.5*sm(0.6,1,u)*1.0) if u<1 else p
Z_LAND=24.0
TST=DUTY*CYCLE; TSW=(1-DUTY)*CYCLE
Z_OFF=Z_LAND-V*TST
def herm(p0,p1,m0,m1,u):
    h00=2*u**3-3*u**2+1; h10=u**3-2*u**2+u; h01=-2*u**3+3*u**2; h11=u**3-u**2
    return h00*p0+h10*m0+h01*p1+h11*m1
Y_LAND=ankle_h(foot_pitch_stance(0),ball_pitch_stance(0,foot_pitch_stance(0)))
Y_OFF=ankle_h(foot_pitch_stance(1),ball_pitch_stance(1,foot_pitch_stance(1)))
def leg_target(ph,side):
    """ph: fase da perna (0=pouso). Retorna (zrel, y, pitchfoot, pitchball)"""
    if ph<DUTY:
        s=ph/DUTY; p=foot_pitch_stance(s); pb=ball_pitch_stance(s,p)
        return Z_LAND-V*TST*s, ankle_h(p,pb), p, pb
    u=(ph-DUTY)/(1-DUTY)
    z=herm(Z_OFF,Z_LAND,-V*TSW,-V*TSW,u)
    p=foot_pitch_swing(u); pb=ball_pitch_swing(u,p)
    y=Y_OFF+(Y_LAND-Y_OFF)*sm(0,1,u)+27.0*np.sin(np.pi*u**0.8)**1.3
    return z,y,p,pb
# ---------------- idle (dedos relaxados) ----------------
CI=np.load('/home/claude/p/clip0.npy')
WI=abs_rot_from_skin(CI[0])
LROT={i:(WI[GP[i]][0].T@WI[i][0] if GP[i]>=0 else None) for i in range(NB)}
FINGERS=[i for i in range(25,55)]
def pose(phi):
    cp=2*np.pi*phi
    Rw={}
    # --- pelvis e coluna ---
    yawP=-10*D2R*np.cos(cp); yawC=14*D2R*np.cos(cp)
    rollP=3*D2R*np.cos(2*np.pi*(phi-0.18))
    def Dspine(k):  # k=0 pelvis .. 5
        t=k/5.0
        yaw=yawP+(yawC-yawP)*t
        roll=rollP*(1-1.6*t)
        lean=(3+k*1.3)*D2R
        return Ry(yaw)@Rz(roll)@Rx(lean),yaw
    Dk={}
    for k in range(6):
        Dk[k],_=Dspine(k); Rw[k]=Dk[k]@Rb[k]
    # pescoço e cabeça (cabeça estável)
    yc=yawC
    Rw[6]=(Ry(0.55*yc)@Rx(7*D2R))@Rb[6]
    Rw[7]=(Ry(0.3*yc)@Rx(5*D2R))@Rb[7]
    Rw[8]=(Ry(0.12*yc)@Rx(2.5*D2R)@Rz(-0.4*rollP))@Rb[8]
    # --- pelvis: posição ---
    H=H_MID-H_AMP*np.cos(4*np.pi*(phi-0.18))
    swayx=1.4*np.cos(2*np.pi*(phi-0.18))
    # quadril médio em y == H
    hipmid_off=(Pb[17]+Pb[21])/2-Pb[0]
    hipmid_rot=Rw[0]@(Rb[0].T@hipmid_off)
    pel=np.array([swayx,H-hipmid_rot[1]+0.0,Pb[0][2]-hipmid_rot[2]+hipmid_off[2]*0+ (0)])
    pel[2]=Pb[0][2]-0.0
    # --- braços ---
    for side,(c0,legph) in ((+1,(9,0.0)),(-1,(13,0.5))):
        cl,ua,la,ha=c0,c0+1,c0+2,c0+3
        # braço oposto à perna do mesmo lado: ph_leg=0 => perna adiante, braço atrás
        A=40*D2R; b0=8*D2R; dl=0.04
        th=-A*np.cos(2*np.pi*(phi-legph-dl))*1.0+b0
        if side<0: th=A*np.cos(2*np.pi*(phi-dl))+b0   # direito: oposto ao esquerdo
        eps=9*D2R
        u=np.array([side*np.sin(eps),-np.cos(eps)*np.cos(th),np.cos(eps)*np.sin(th)])
        beta=(88+12*(th-b0)/A)*D2R
        f=Rx(-beta)@u; f[0]-=side*0.05; f/=np.linalg.norm(f)
        # clavícula acompanha o peito
        Rw[cl]=Dk[5]@Rz(side*2*D2R*np.cos(cp))@Rb[cl]
        Rw[ua]=arc(Pb[la]-Pb[ua],u)@Rb[ua]
        Rw[la]=arc(Pb[ha]-Pb[la],f)@Rb[la]
        Dh=Rw[la]@Rb[la].T
        Rw[ha]=Dh@Rb[ha]
    for i in FINGERS: Rw[i]=None
    # --- pernas (rot. provisória; posições via IK) ---
    legs=[]
    for side,(th,kn,fo,ba,ph) in ((+1,(17,18,19,20,phi%1.0)),(-1,(21,22,23,24,(phi+0.5)%1.0))):
        legs.append((side,th,kn,fo,ba,ph))
        Rw[th]=np.eye(3); Rw[kn]=np.eye(3); Rw[fo]=np.eye(3); Rw[ba]=np.eye(3)
    # FK parcial para obter quadris
    tmp={i:(Rw[i] if Rw[i] is not None else np.eye(3)) for i in range(NB)}
    W=fk(tmp,pel)
    for side,th,kn,fo,ba,ph in legs:
        hip=W[th][1]
        zr,y,p,pb=leg_target(ph,side)
        ank=np.array([side*9.4+ (side*1.2*np.sin(np.pi*max(0,(ph-DUTY))/(1-DUTY)) if ph>DUTY else 0)+swayx*0.0,y,hip[2]+zr])
        d=ank-hip; dist=np.linalg.norm(d); dist=min(dist,L1+L2-0.05); dn=d/np.linalg.norm(d)
        a=(L1**2-L2**2+dist**2)/(2*dist); h=np.sqrt(max(L1**2-a**2,0))
        pole=np.array([side*0.12,0,1.0]); pp=pole-(pole@dn)*dn; pp/=np.linalg.norm(pp)
        knee=hip+dn*a+pp*h
        ank=hip+dn*dist
        Rw[th]=arc(Pb[kn]-Pb[th],knee-hip)@Rb[th]
        Rw[kn]=arc(Pb[fo]-Pb[kn],ank-knee)@Rb[kn]
        Rw[fo]=Rx(-p*D2R)@Rb[fo]
        Rw[ba]=Rx(-pb*D2R)@Rb[ba]
    # dedos: local do idle
    for i in range(25,55):
        pass
    # FK final com dedos
    full={}
    for i in ORDER:
        if Rw[i] is None: full[i]=None
    Rfull={}
    for i in ORDER:
        if Rw[i] is not None: Rfull[i]=Rw[i]
        else: Rfull[i]=Rfull[GP[i]]@LROT[i]
    W=fk(Rfull,pel)
    return skin(W),W
def build(nfr=NFR):
    fr=[]
    for k in range(nfr+1):
        S,_=pose((k/nfr)%1.0); fr.append(S)
    return np.array(fr)
if __name__=='__main__':
    c=build()
    print(c.shape, 'laço fecha',np.abs(c[0]-c[-1]).max(), 'Y_LAND',Y_LAND,'Y_OFF',Y_OFF,'Zoff',Z_OFF,'L',L1,L2)
    np.save('/home/claude/p/run/run.npy',c)
