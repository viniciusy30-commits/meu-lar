import sys,os,json; sys.path.insert(0,'/home/claude/w')
from hcommon import *
from scipy.spatial import cKDTree
from scipy import ndimage
OUT='/home/claude/w/hout/'; os.makedirs(OUT,exist_ok=True)
COL=[(0,'ruivo','Ruivo'),(2,'preto','Preto'),(4,'castanhoe','Castanho escuro'),(5,'castanho','Castanho'),(10,'loiroe','Loiro escuro'),(11,'loiro','Loiro'),(14,'platina','Platinado'),(1,'cinza','Cinza'),(19,'rosa','Rosa'),(20,'azul','Azul')]
VAR=[('coque',0xae58a7,False),('solto',0xae58a4,True)]
r=dbpf.read(HP); G={}
for e in r:
    if e['t']==0x015A1849: G[e['g']&0xffffff]=geom.parse(dbpf.data(e))
T={e['inst']:e for e in r if e['t']==0x3453CF95}
order=json.load(open('horder.json'))
sv,si,fl,_=E.read_piece(CU+'p_body_af5.bin'); sp=sv['pos'].astype(float); sn=sv['nor'].astype(float); si=si.astype(int)
bi=sv['bi'].astype(int); bw=sv['bw'].astype(float)/255
def uvmap(uv):  # recorte 1024x1024 do atlas 2048x4096: x 0..1024, y 256..1280
    return np.c_[uv[:,0]*2048/1024,(uv[:,1]*4096-256)/1024]
def weights(P):
    t=cKDTree(sp); d,nb=t.query(P,k=6)
    W=np.zeros((len(P),55))
    for j in range(6):
        wj=1/(d[:,j]+1.0)**2
        for c in range(4): np.add.at(W,(np.arange(len(P)),bi[nb[:,j],c]),wj*bw[nb[:,j],c])
    W/=W.sum(1,keepdims=True)
    arms=[9,10,11,12,13,14,15,16]+list(range(25,55))     # cabelo não balança com os braços: segue o peito
    W[:,5]+=W[:,arms].sum(1); W[:,arms]=0
    return W
def quant(W):
    top=np.argsort(-W,axis=1)[:,:4]; tw=np.take_along_axis(W,top,1); tw/=np.maximum(tw.sum(1,keepdims=True),1e-9)
    q=np.round(tw*255).astype(int); q[:,0]+=255-q.sum(1); return top,q
def tex(idx):
    k=order[idx][1]; im=rle2.rle2_mip0(dbpf.data(T[k])); W,H=im.size
    c=np.asarray(im.crop((0,256,1024,1280))).astype(float)
    solid=c[...,3]>8
    d,(iy,ix)=ndimage.distance_transform_edt(~solid,return_indices=True)
    c2=c.copy(); c2[~solid,:3]=c[iy,ix,:3][~solid]      # sem franja escura nas bordas das mechas
    return np.clip(c2+0.5,0,255).astype(np.uint8)
CAPY=float(os.environ.get('CAPY','176')); CAPZ=float(os.environ.get('CAPZ','-1.5'))
def build(name,gk,cap):
    g=G[gk]; P=g['pos'].astype(float)*K+OFF; N=g['nor'].astype(float); UV=uvmap(g['uv'][0].astype(float)); I=g['idx'].astype(int)
    W=weights(P)
    if cap:
        cen=sp[si].mean(1); ks=si[(cen[:,1]>=CAPY)|((cen[:,2]<CAPZ)&(cen[:,1]>=CAPY-9))|((np.abs(cen[:,0])>6.5)&(cen[:,1]>=CAPY-7))]; vs=np.unique(ks.ravel()); m=-np.ones(len(sp),int); m[vs]=np.arange(len(vs))
        cn=sn[vs]/np.linalg.norm(sn[vs],axis=1,keepdims=True); cp=sp[vs]+cn*0.45
        tx0=tex(0); px=tx0[np.clip((UV[:len(g['pos']),1]*1024).astype(int),0,1023),np.clip((UV[:len(g['pos']),0]*1024).astype(int),0,1023)]
        lum=px[:,:3].astype(float).mean(1); okm=(px[:,3]>240)&(P[:len(g['pos']),1]>150); med=np.median(lum[okm])
        j=np.where(okm)[0][np.argmin(np.abs(lum[okm]-med))]; ux=UV[j]
        Wc=np.zeros((len(vs),55)); 
        for c in range(4): np.add.at(Wc,(np.arange(len(vs)),bi[vs,c]),bw[vs,c])
        Wc[:,5]+=Wc[:,[9,10,11,12,13,14,15,16]].sum(1); Wc[:,[9,10,11,12,13,14,15,16]]=0
        P=np.vstack([P,cp]); N=np.vstack([N,cn]); UV=np.vstack([UV,np.tile(ux,(len(vs),1))]); I=np.vstack([I,m[ks]+len(g['pos'])]); W=np.vstack([W,Wc])
        print('capa',len(vs),'vértices; uv raiz',ux.round(3))
    tp,q=quant(W)
    v=np.zeros(len(P),E.DT); v['pos']=P; v['nor']=N; v['uv']=UV; v['col']=255; v['bi']=tp; v['bw']=q
    return v,I
if __name__=='__main__':
    for name,gk,cap in VAR:
        v,I=build(name,gk,cap); E.write_piece(OUT+'lotus_%s.cup'%name,v,I.astype(np.uint16),0,b''); print(name,len(v),len(I),os.path.getsize(OUT+'lotus_%s.cup'%name))
    for idx,slug,nm in COL:
        Image.fromarray(tex(idx)).save(OUT+'lotus_%s.png'%slug,optimize=True); print(slug,os.path.getsize(OUT+'lotus_%s.png'%slug),flush=True)
