import sys,os,json
from atlas import *
from scipy import ndimage
OUT='/home/claude/w/out/'; os.makedirs(OUT,exist_ok=True)
# cores do pacote (índice do swatch -> nome em português)
SW=[(0,'Branco'),(1,'Creme'),(4,'Azul claro'),(5,'Lavanda'),(7,'Pêssego'),(8,'Coral'),(9,'Vermelho'),(10,'Cinza'),(11,'Preto'),(12,'Verde'),(13,'Amarelo'),(14,'Rosa pink')]
SLUG={0:'branco',1:'creme',4:'azul',5:'lavanda',7:'pessego',8:'coral',9:'vermelho',10:'cinza',11:'preto',12:'verde',13:'amarelo',14:'rosa'}
def lace_layer(r,key):
    im=tex_for(r,key); W_,H_=im.size
    im=im.crop((0,H_//2,W_,H_))                                     # só a metade de baixo do atlas é usada
    a=np.asarray(im).astype(float)/255; rgb=a[...,:3]*a[...,3:4]; al=a[...,3]
    if im.width!=S:
        rgb=cv2.resize(rgb,(S,S),interpolation=cv2.INTER_AREA); al=cv2.resize(al,(S,S),interpolation=cv2.INTER_AREA)
    rgb=rgb/np.maximum(al[...,None],1e-4)
    return np.clip(rgb,0,1),al
def build_geometry():
    r,P0,N,UV,I,W=load_top(); sv,si=load_body()
    UVp=UV.copy(); UVp[:,1]=(UV[:,1]-0.5)*2
    hand=np.isin(W.argmax(1),[12,16]+list(range(25,55)))
    keep=[t for t in range(len(I)) if hand[I[t]].sum()<2]
    P1,push,sd,d=clearance_push(P0,I,sv)
    # pesos: onde a blusa cola no corpo usa EXATAMENTE os pesos do corpo (mesma deformação); longe, os nativos
    Wb=body_w55(sv); t=cKDTree(sv['pos'].astype(float)); dd,nb=t.query(P0)
    k=np.clip((dd-0.05)/1.45,0,1)[:,None]; Wf=Wb[nb]*(1-k)+W*k
    return r,P0,P1,N,UV,UVp,I,Wf,keep,sv,si
def quant(Wf):
    top=np.argsort(-Wf,axis=1)[:,:4]; tw=np.take_along_axis(Wf,top,1); tw/=np.maximum(tw.sum(1,keepdims=True),1e-9)
    q=np.round(tw*255).astype(int); q[:,0]+=255-q.sum(1); return top,q
def compose(r,key,POS,COV,uvb,Ucol,bake):
    lace,a=lace_layer(r,key)
    La=a[COV]; Lc=lace[COV]

    ae=np.clip(La,0,1)
    col=Lc*ae[:,None]+Ucol*(1-ae[:,None])                      # renda por cima da pele (a parte transparente mostra a pele de verdade)
    alpha=np.clip((ae-0.25)/0.30,0,1)
    alpha=np.maximum(alpha,bake.astype(float))                    # pele pintada onde ficariam as alças do sutiã
    col=np.where((bake&(ae<0.6))[:,None],Ucol,col)
    rgba=np.zeros((S,S,4)); rgba[COV,:3]=col; rgba[COV,3]=alpha
    # preenchimento das bordas das ilhas (sem franja escura na filtragem bilinear)
    solid=COV&(rgba[...,3]>0.02)
    d,(iy,ix)=ndimage.distance_transform_edt(~solid,return_indices=True)
    fill=rgba[iy,ix]; out=rgba.copy(); out[~solid,:3]=fill[~solid,:3]
    near=(~solid)&(d<=3); out[near,3]=fill[near,3]*np.clip(1-(d[near]-1)/2.0,0,1)*0+0
    return np.clip(out*255+0.5,0,255).astype(np.uint8)
if __name__=='__main__':
    r,P0,P1,N,UV,UVp,I,Wf,keep,sv,si=build_geometry()
    POS,COV,TID=raster_atlas(P0,UVp,I,keep)
    sk2,brad,sk=inpaint_skin()
    q=POS[COV]; uvb,dist=body_uv_at(q,sv,si)
    Ucol=sample(sk2,uvb)/255.0
    inbra=brad[np.clip((uvb[:,1]*brad.shape[0]).astype(int),0,brad.shape[0]-1),np.clip((uvb[:,0]*brad.shape[1]).astype(int),0,brad.shape[1]-1)]
    inbra&=(dist<1.2)                                              # só onde o corpo está mesmo colado
    texs={}; used=np.zeros(len(I),bool)
    T=json.load(open('order.json'))
    for idx,nm in SW:
        key=T[idx][1]; rgba=compose(r,key,POS,COV,uvb,Ucol,inbra); texs[idx]=rgba
        al=rgba[...,3]>127
        cnt=np.bincount(TID[COV&al],minlength=len(I)); used|=cnt>0
        print(idx,nm,'ok',flush=True)
    keep2=[t for t in keep if used[t]]; print('triângulos finais',len(keep2),'de',len(I))
    vmap=-np.ones(len(P0),int); vs=np.unique(I[keep2].ravel()); vmap[vs]=np.arange(len(vs))
    top,qw=quant(Wf)
    v=np.zeros(len(vs),E.DT); v['pos']=P1[vs]; v['nor']=N[vs]; v['uv']=UVp[vs]; v['col']=255; v['bi']=top[vs]; v['bw']=qw[vs]
    idx=vmap[I[keep2]]

    E.write_piece(OUT+'bloom_af5.cup',v,idx.astype(np.uint16),0,b'')
    for i,nm in SW: Image.fromarray(texs[i]).save(OUT+'bloom_%s_af5.png'%SLUG[i],optimize=True)
    np.savez(OUT+'geo.npz',P0=P0,P1=P1,vs=vs,idx=idx)
    print('vértices',len(vs),'triângulos',len(idx),'cup bytes',os.path.getsize(OUT+'bloom_af5.cup'))
