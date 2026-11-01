import numpy as np,struct
from pc import load,REC,D
def sm(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
PAR=dict(ex=0.30,exh=0.50,ez=0.24,hem=26.0,drop=(1.5,-4.0),sk=1.95,sf=0.50,t0=10.0)
def sleeve_w(P):
    ax=np.abs(P[:,0]);S=np.array([13.3,142.5,-2.9]);u=np.array([0.6012,-0.7991,-0.0076])
    t=(ax-S[0])*u[0]+(P[:,1]-S[1])*u[1]+(P[:,2]-S[2])*u[2]
    return sm(4,12,t)*sm(15,22,ax)
def deform(P):
    x,y,z=P[:,0].copy(),P[:,1].copy(),P[:,2].copy()
    sx=np.where(x<0,-1.0,1.0);ax=np.abs(x)
    S=np.array([13.3,142.5,-2.9]);u=np.array([0.6012,-0.7991,-0.0076])
    vx=ax-S[0];vy=y-S[1];vz=z-S[2]
    t=vx*u[0]+vy*u[1]+vz*u[2]
    px=vx-t*u[0];py=vy-t*u[1];pz=vz-t*u[2];r=np.sqrt(px**2+py**2+pz**2)
    # peso da manga: depois da axila e fora do tronco
    ws=sm(4,12,t)*sm(15,22,ax)
    # --- tronco ---
    wt=(1-ws)
    collar=1-0.9*sm(132,148,y)*(1-sm(10,20,ax)*0.5)
    ex=PAR['ex']+PAR['exh']*(1-sm(104,132,y))
    X=ax*(1+ex*wt*collar)
    Z=(z-2.0)*(1+(PAR['ez']+0.24*(1-sm(108,132,y)))*wt*collar)+2.0
    Y=y-PAR['hem']*(1-sm(104,126,y))*wt
    # ombro caído: o ombro e a manga descem e vão para fora
    dsh=sm(10,22,ax)*(1-sm(144,152,y)*0.0)
    X=X+PAR['drop'][0]*dsh*(1-0.0)*(ws*0+1)*sm(18,26,ax)
    Y=Y+PAR['drop'][1]*sm(18,26,ax)*sm(125,142,y)
    # --- manga: estica ao longo do eixo e abre ---
    t0=PAR['t0'];k=PAR['sk']
    tn=np.where(t>t0,t0+(t-t0)*k,t)
    rn=r*(1+PAR['sf']*sm(t0+2,27,t))
    dt=(tn-t)*ws
    dr=(rn-r)*ws
    # direção radial
    rad=np.stack([px,py,pz],1)/np.maximum(r,1e-6)[:,None]
    ux=np.array([u[0],u[1],u[2]])
    off=dt[:,None]*ux[None,:]+dr[:,None]*rad
    X=X+off[:,0];Y=Y+off[:,1];Z=Z+off[:,2]
    return np.stack([sx*X,Y,Z],1)
if __name__=='__main__':
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    r,idx,fl,h=load('top_shirt');P=r['pos'].astype(float);Q=deform(P)
    b,bi_,_,_=load('bottom_looseJeans'.lower()) if False else load('bottom_loosejeans')
    J=b['pos'].astype(float)
    fig,ax=plt.subplots(1,3,figsize=(15,7))
    for a,(i,j,t) in zip(ax,[(0,1,'frente'),(2,1,'lado'),(0,2,'cima')]):
        a.scatter(J[:,i],J[:,j] if j==1 else J[:,j],s=0.2,c='gray')
        a.scatter(Q[:,i],Q[:,j],s=0.6,c='r');a.set_aspect('equal');a.set_title(t)
        if j==1: a.set_ylim(70,155)
    plt.savefig('skate1.png',dpi=55)
    print(Q.min(0).round(1),Q.max(0).round(1),np.isfinite(Q).all())
import numpy as np,struct,os
from PIL import Image,ImageDraw,ImageFilter
from skate import deform,sm,sleeve_w
from pc import load,REC,D
OUT='/home/claude/out/etapa25'
A=OUT+'/app/src/main/assets/cute';os.makedirs(A+'/icons',exist_ok=True)
r,idx,fl,hide=load('top_shirt')
P=deform(r['pos'].astype(float));T=idx.reshape(-1,3).astype(int)
# pesos: a manga inteira segue só o osso do braço (antes parte seguia o tronco e rasgava ao mexer o braço)
ws=sleeve_w(r['pos'].astype(float));BI=r['bi'].astype(int);BW=r['bw'].astype(float)/255.0
BI2=BI.copy();BW2=BW.copy()
for v in np.where(ws>0)[0]:
    ub=10 if r['pos'][v,0]>0 else 14
    ids=list(BI[v]);w=list(BW[v]*(1-ws[v]))
    if ub in ids: w[ids.index(ub)]+=ws[v]
    else:
        k=int(np.argmin(w));ids[k]=ub;w[k]=ws[v]
    w=np.array(w);w/=w.sum();BI2[v]=ids;BW2[v]=w
r['bi']=BI2.astype(np.uint8)
q=np.round(BW2*255).astype(int);q[np.arange(len(q)),q.argmax(1)]+=255-q.sum(1);r['bw']=q.astype(np.uint8)
# normais suaves (soldando vértices de mesma posição)
key=np.round(P,3);_,inv=np.unique(key,axis=0,return_inverse=True);inv=inv.ravel()
fn=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]])
acc=np.zeros((inv.max()+1,3))
for k in range(3): np.add.at(acc,inv[T[:,k]],fn)
N=acc[inv];N/=np.maximum(np.linalg.norm(N,axis=1),1e-9)[:,None]
# orientação: normal deve apontar para fora do tronco (comparar com a original)
N0=r['nor'].astype(float)
if (N*N0).sum(1).mean()<0: N=-N
# UV planar nas costas
TW,TH=1024,1536;BW,BH=36.0,54.0;YT=148.0
back=N[:,2]<-0.15
u=np.clip(0.5+P[:,0]/BW,0,1);v=np.clip((YT-P[:,1])/BH,0,1)
uv=np.stack([u,v],1)
fr=np.array([0.02,0.02]);uv[~back]=fr
# triângulos de estampa = os 3 vértices nas costas; o resto usa um pixel preto (vértices duplicados, sem borrar a estampa pelas laterais)
ptri=back[T].all(1)
nvo=len(P)
Pn=np.concatenate([P,P]);Nn=np.concatenate([N,N]);UVn=np.concatenate([uv,np.tile(fr,(nvo,1))])
Tn=T.copy();Tn[~ptri]+=nvo
used=np.unique(Tn);remap=-np.ones(len(Pn),int);remap[used]=np.arange(len(used))
Pn,Nn,UVn=Pn[used],Nn[used],UVn[used];Tn=remap[Tn]
src=np.concatenate([np.arange(nvo),np.arange(nvo)])[used]
r2=np.zeros(len(Pn),REC)
for f in ('bi','bw'): r2[f]=r[f][src]
r2['pos']=Pn;r2['nor']=Nn;r2['uv']=UVn.astype(np.float32);r2['col']=255
idx2=Tn.astype('<u2').ravel()
open(A+'/p_top_skatetee.bin','wb').write(b'CUP1'+struct.pack('<3i',len(r2),len(idx2),1)+r2.tobytes()+idx2.tobytes()+struct.pack('<i',len(hide))+hide.tobytes())
P,N,uv,T=Pn,Nn,UVn,Tn
print('verts',len(r2),'tris',len(Tn),'print tris',ptri.sum(),'hide',len(hide))
# ---- textura ----
S=2;W,H=TW*S,TH*S;im=Image.new('RGB',(W,H),(22,22,24));d=ImageDraw.Draw(im)
pxcm=TW/BW*S
def X(x):return (0.5+x/BW)*W
def Y(y):return (YT-y)/BH*H
cream=(214,204,160);dark=(22,22,24)
def poly(pts,fill=None,outline=None,w=0):
    d.polygon([(X(a),Y(b)) for a,b in pts],fill=fill)
def line(pts,wcm,col=cream):
    d.line([(X(a),Y(b)) for a,b in pts],fill=col,width=max(1,int(wcm*pxcm)),joint='curve')
def circ(cx,cy,rr,fill=None,out=None,wc=0.3):
    d.ellipse([X(cx-rr),Y(cy+rr),X(cx+rr),Y(cy-rr)],fill=fill,outline=out,width=max(1,int(wc*pxcm)))
ay=128.5
def cr(vw,hw,top,bot,arm,col):
    pts=[(-vw,ay+top),(vw,ay+top),(vw,ay+hw),(arm,ay+hw),(arm,ay-hw),(vw,ay-hw),(vw,ay+bot),(-vw,ay+bot),(-vw,ay-hw),(-arm,ay-hw),(-arm,ay+hw),(-vw,ay+hw)]
    poly(pts,fill=col)
cr(2.3,2.1,9.0,-26.0,11.0,cream)
cr(1.8,1.6,8.4,-25.4,10.4,dark)
cr(1.3,1.1,7.8,-24.8,9.8,cream)
cr(0.8,0.6,7.2,-24.2,9.2,dark)
# florões nas pontas
for (px,py) in [(0,ay+9),(0,ay-26),(-11,ay),(11,ay)]:
    circ(px,py,2.6,fill=cream);circ(px,py,1.9,fill=dark);circ(px,py,1.2,fill=cream);circ(px,py,0.6,fill=dark)
# medalhão central
circ(0,ay,4.0,fill=cream);circ(0,ay,3.3,fill=dark);circ(0,ay,2.4,fill=cream);circ(0,ay,1.5,fill=dark);circ(0,ay,0.7,fill=cream)
# losangos na haste
for yy in (ay-9,ay-16):
    poly([(0,yy+2.2),(1.6,yy),(0,yy-2.2),(-1.6,yy)],fill=cream)
    poly([(0,yy+1.2),(0.8,yy),(0,yy-1.2),(-0.8,yy)],fill=dark)
# gotejado
for xx,ln in [(-1.2,5),(0.9,9),(1.8,3.5)]:
    line([(xx,ay-26),(xx,ay-26-ln)],0.5);circ(xx,ay-26-ln,0.5,fill=cream)
for xx,ln in [(-9.5,3.5),(-6.5,2),(9,4.5),(6.8,2.2)]:
    line([(xx,ay-2.1),(xx,ay-2.1-ln)],0.42);circ(xx,ay-2.1-ln,0.42,fill=cream)
for xx,ln in [(-3.5,2.0),(4.0,1.5)]:
    line([(xx,ay+9),(xx,ay+9-ln)],0.3)
im=im.resize((TW,TH),Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.3))
# bordas pretas garantidas
a=np.array(im);a[:3]=dark;a[-3:]=dark;a[:,:3]=dark;a[:,-3:]=dark
Image.fromarray(a).save(A+'/skatetee.png',optimize=True)
im.crop((0,0,TW,TH)).resize((256,384)).save('/home/claude/w/tex_prev.png')
np.save('/home/claude/w/skate_mesh.npy',dict(P=P,N=N,T=T,uv=uv,back=back),allow_pickle=True)
