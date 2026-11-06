from geo import *
from scipy import ndimage
import json,os
OUT='/home/claude/w/out/'; os.makedirs(OUT,exist_ok=True)
lab=np.load('/home/claude/sk/lab.npy')
SKIRT=[52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,81,82,83,84]
BELT=[38,39,40,47,48,49,50,51]+list(range(67,81))+[85,86,87,88]
SEL=SKIRT+BELT
# cores: (indice do swatch no pacote, slug, nome)
SW=[(0,'mostarda','Xadrez mostarda'),(1,'cinza','Xadrez cinza'),(2,'oliva','Xadrez verde-oliva'),(3,'ferrugem','Xadrez ferrugem'),(4,'petroleo','Xadrez azul petróleo'),(5,'preto','Preta')]
MARGIN=0.5
def build():
    r,gs=load_geoms(); e,g=gs[0x52]; raw=dbpf.data(e); bones=geom_bones(raw)
    P0=g['pos'].astype(float)*K+OFF; N=g['nor'].astype(float); UV=g['uv'][0].astype(float); I=g['idx'].astype(int)
    bi=g['bi'].astype(int); bw=g['bw'].astype(float)/255
    amap=np.array([APP[n] for n in bones]); W=np.zeros((len(P0),55)); np.add.at(W,(np.arange(len(P0))[:,None],amap[bi]),bw)
    return r,P0,N,UV,I,W
def weights(P0,W,sv,thigh_keep=0.55):
    # coxas: só parte do peso nativo vai para a perna; o resto vai para a pelve (a saia rodada não rasga/estica tanto ao andar)
    W=W.copy(); TH=[17,21,18,22]  # coxa e torção de coxa (L,R)  [17+0,21+0 = coxas; 18,22 = joelho? checado abaixo]
    return W
if __name__=='__main__':
    r,P0,N,UV,I,W=build()
    print('ossos dominantes por componente:')
    for c in (52,63,47):
        m=lab==c; print(c,np.bincount(W[m].argmax(1),minlength=55).nonzero()[0])

def go():
    r,P0,N,UV,I,W=build(); sv,si=load_body()
    UVp=UV.copy(); UVp[:,1]=(UV[:,1]-0.5)*2
    sel=np.isin(lab,SEL); tri=sel[I[:,0]]&sel[I[:,1]]&sel[I[:,2]]; I2=I[tri]
    vs=np.unique(I2.ravel()); vm=-np.ones(len(P0),int); vm[vs]=np.arange(len(vs)); I3=vm[I2]
    P=P0[vs]; Nn=N[vs]; U=UVp[vs]; Wn=W[vs].copy()
    print('triângulos',len(I3),'vértices',len(vs),'UV v',U[:,1].min().round(3),U[:,1].max().round(3))
    # pesos: coxas só 55% (resto na pelve)
    th=Wn[:,17]+Wn[:,21]; Wn[:,17]*=0.55; Wn[:,21]*=0.55; Wn[:,0]+=0.45*th
    # afasta da pele (sem furar nos quadris)
    P1,push,sd,d=clearance_push(P,I3,sv,MARGIN)
    print('push máx',push.max().round(2),'tocados',(push>0).sum())
    # onde cola no corpo usa os pesos do corpo
    Wb=body_w55(sv); t=cKDTree(sv['pos'].astype(float)); dd,nb=t.query(P)
    k=np.clip((dd-0.05)/1.45,0,1)[:,None]; Wf=Wn  # preserva os nativos; só mistura quando colado
    Wf=Wb[nb]*(1-k)+Wn*k
    top=np.argsort(-Wf,axis=1)[:,:4]; tw=np.take_along_axis(Wf,top,1); tw/=np.maximum(tw.sum(1,keepdims=True),1e-9)
    q=np.round(tw*255).astype(int); q[:,0]+=255-q.sum(1)
    v=np.zeros(len(vs),E.DT); v['pos']=P1; v['nor']=Nn; v['uv']=U; v['col']=255; v['bi']=top; v['bw']=q
    E.write_piece(OUT+'autumn_af5.cup',v,I3.astype(np.uint16),0,b'')
    # texturas
    T={e['inst']&0xffffff:e for e in r if e['t']==0x3453CF95}; order=json.load(open('order.json'))
    S=1024
    # cobertura do atlas (para estender cor além das bordas das ilhas)
    COV=np.zeros((S,S),bool)
    for a,b,c in I3:
        u=U[[a,b,c],0]*S; w=U[[a,b,c],1]*S
        x0,x1=int(max(0,np.floor(u.min()))),int(min(S-1,np.ceil(u.max()))); y0,y1=int(max(0,np.floor(w.min()))),int(min(S-1,np.ceil(w.max())))
        gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        d_=(w[1]-w[2])*(u[0]-u[2])+(u[2]-u[1])*(w[0]-w[2])
        if abs(d_)<1e-9: continue
        l0=((w[1]-w[2])*(gx-u[2])+(u[2]-u[1])*(gy-w[2]))/d_; l1=((w[2]-w[0])*(gx-u[2])+(u[0]-u[2])*(gy-w[2]))/d_; l2=1-l0-l1
        m=(l0>=-0.02)&(l1>=-0.02)&(l2>=-0.02); COV[(gy[m]-.5).astype(int),(gx[m]-.5).astype(int)]=True
    dist,(iy,ix)=ndimage.distance_transform_edt(~COV,return_indices=True)
    for idx,slug,nm in SW:
        im=rle2.rle2_mip0(dbpf.data(T[order[idx][1]])); W_,H_=im.size
        im=im.crop((0,H_//2,W_,H_)).resize((S,S),Image.LANCZOS)
        a=np.asarray(im.convert('RGB')).copy()
        a=a[iy,ix]*(~COV)[...,None]+a*(COV)[...,None]
        Image.fromarray(a.astype(np.uint8)).save(OUT+'autumn_%s.png'%slug,optimize=True); print(slug,nm,flush=True)
    np.savez(OUT+'geo.npz',P0=P,P1=P1,I3=I3,U=U,Nn=Nn)
go() if __name__=='__main__' else None
