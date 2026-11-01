import numpy as np,pickle,struct,os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
P=pickle.load(open('basepos.pkl','rb')).astype(np.float64)
def sm(a,b,x): t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
def gs(x,c,s): return np.exp(-((x-c)/s)**2)
def warp(p,b):
    x,y,z=p[:,0],p[:,1],p[:,2]; ax=np.abs(x); sx=np.where(x<0,-1.,1.)
    d=np.zeros_like(p); low=1-sm(146,156,y)
    peso,ombro,peito,busto,cint,quad,coxa,braco,cab=.14*b[1],3*b[2],.1*b[3],2.6*b[4],.15*b[5],.12*b[6],.25*b[7],.25*b[8],.12*b[9]
    d[:,0]+=sx*np.minimum(ax,24)*peso*low; d[:,2]+=(z-3)*peso*low
    d[:,0]+=sx*ombro*sm(22,34,ax)*sm(62,78,y)*low
    w=sm(100,114,y)*(1-sm(128,140,y))*(1-sm(18,28,ax)); d[:,0]+=x*peito*w; d[:,2]+=z*peito*w
    w=gs(y,121,7)*gs(ax,8,6)*sm(-1,5,z); d[:,2]+=busto*w
    w=sm(92,100,y)*(1-sm(110,118,y))*(1-sm(20,30,ax)); d[:,0]+=x*cint*w; d[:,2]+=z*cint*w
    w=sm(66,78,y)*(1-sm(94,104,y))*(1-sm(26,36,ax)); d[:,0]+=x*quad*w; d[:,2]+=(z-3)*quad*.5*w
    rx=x-sx*9.3; rz=z-3.8; r=np.hypot(rx,rz); w=sm(44,58,y)*(1-sm(86,98,y))*(1-sm(11,19,r))*sm(0,5,ax); d[:,0]+=rx*coxa*w; d[:,2]+=rz*coxa*w
    ux=.6012*sx; vx=x-sx*13.3; vy=y-142.5; vz=z+2.9; t=vx*ux+vy*-.7991+vz*-.0076
    px=vx-t*ux; py=vy+t*.7991; pz=vz+t*.0076; r=np.sqrt(px**2+py**2+pz**2)
    w=sm(6,16,t)*(1-sm(44,52,t))*(1-sm(9,15,r)); d[:,0]+=px*braco*w; d[:,1]+=py*braco*w; d[:,2]+=pz*braco*w
    w=sm(146,156,y); d[:,0]+=x*cab*w; d[:,1]+=(y-148)*cab*w; d[:,2]+=z*cab*w
    return p+d
names="Altura Peso Ombros Peito Busto Cintura Quadril Coxas Braços Cabeça".split()
fig,ax=plt.subplots(2,5,figsize=(18,9))
for i in range(1,10):
    a=ax.flat[i-1]
    for s,c in ((-1,'tab:blue'),(1,'tab:red')):
        b=np.zeros(10); b[i]=s; Q=warp(P,b)
        view=(0,1) if i!=4 else (2,1)
        a.scatter(Q[::3,view[0]],Q[::3,view[1]],s=.3,c=c,alpha=.5)
    a.scatter(P[::3,(0,1)[0] if i!=4 else 2],P[::3,1],s=.3,c='k',alpha=.4)
    a.set_title(names[i]+' (preto=0, azul=-100, vermelho=+100)'+(' [lado]' if i==4 else '')); a.set_aspect('equal')
    b=np.zeros(10); b[i]=1; D=np.linalg.norm(warp(P,b)-P,axis=1); print(names[i],'desloc. máx %.2f'%D.max(),'NaN' if np.isnan(D).any() else 'ok')
plt.tight_layout(); plt.savefig('warp.png',dpi=60)
