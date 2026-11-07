import struct, sys, numpy as np
from pathlib import Path
from PIL import Image
from scipy.spatial import cKDTree
ROOT=Path('/home/claude/proj/codigo/app/src/main/assets/cute')
def read(p):
    b=Path(p).read_bytes(); nv,ni,_=struct.unpack_from('<III',b,4)
    dt=np.dtype([('pos','<f4',(3,)),('nor','<f4',(3,)),('uv','<f4',(2,)),('rgba','u1',(4,)),('bi','u1',(4,)),('bw','u1',(4,))])
    v=np.frombuffer(b,dtype=dt,count=nv,offset=16)
    idx=np.frombuffer(b,dtype='<u2',count=ni,offset=16+nv*44).reshape(-1,3).astype(np.int32)
    return dict(pos=v['pos'].copy(),nor=v['nor'].copy(),uv=v['uv'].copy(),idx=idx)
def raster(img,zb,P,N,UV,idx,tex,base,W,H,view):
    # view: 'front','back','side'
    if view=='front': R=np.array([[1,0,0],[0,1,0],[0,0,1]])
    elif view=='back': R=np.array([[-1,0,0],[0,1,0],[0,0,-1]])
    else: R=np.array([[0,0,-1],[0,1,0],[1,0,0]])
    return R
def render(items,view,W=400,H=800,ymin=-2,ymax=170,flip=False):
    R=raster(None,None,None,None,None,None,None,None,W,H,view)
    img=np.zeros((H,W,3),np.float32)+245; zb=np.full((H,W),-1e9,np.float32)
    sc=H/(ymax-ymin)
    L=np.array([0.3,0.4,0.85]); L/=np.linalg.norm(L)
    for g,tex,base in items:
        P=g['pos']@R.T; N=g['nor']@R.T
        X=P[:,0]*sc+W/2; Y=H-(P[:,1]-ymin)*sc; Z=P[:,2]
        for t in g['idx']:
            a,b,c=t
            x0=int(max(0,np.floor(min(X[a],X[b],X[c])))); x1=int(min(W-1,np.ceil(max(X[a],X[b],X[c]))))
            y0=int(max(0,np.floor(min(Y[a],Y[b],Y[c])))); y1=int(min(H-1,np.ceil(max(Y[a],Y[b],Y[c]))))
            if x1<x0 or y1<y0: continue
            d=(Y[b]-Y[c])*(X[a]-X[c])+(X[c]-X[b])*(Y[a]-Y[c])
            if abs(d)<1e-9: continue
            xs,ys=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
            w0=((Y[b]-Y[c])*(xs-X[c])+(X[c]-X[b])*(ys-Y[c]))/d
            w1=((Y[c]-Y[a])*(xs-X[c])+(X[a]-X[c])*(ys-Y[c]))/d
            w2=1-w0-w1
            m=(w0>=-1e-4)&(w1>=-1e-4)&(w2>=-1e-4)
            if not m.any(): continue
            z=w0*Z[a]+w1*Z[b]+w2*Z[c]
            sub=zb[y0:y1+1,x0:x1+1]; ok=m&(z>sub)
            if not ok.any(): continue
            n=(w0[...,None]*N[a]+w1[...,None]*N[b]+w2[...,None]*N[c]); n/=np.linalg.norm(n,axis=-1,keepdims=True)+1e-9
            lam=np.clip(n@L,0,1)*0.65+0.35
            if tex is not None:
                u=w0*g['uv'][a,0]+w1*g['uv'][b,0]+w2*g['uv'][c,0]; v=w0*g['uv'][a,1]+w1*g['uv'][b,1]+w2*g['uv'][c,1]
                th,tw=tex.shape[:2]
                col=tex[np.clip((v*th).astype(int),0,th-1),np.clip((u*tw).astype(int),0,tw-1),:3].astype(np.float32)
            else: col=np.broadcast_to(np.array(base,np.float32),lam.shape+(3,))
            out=col*lam[...,None]
            sub[ok]=z[ok]; zb[y0:y1+1,x0:x1+1]=sub
            im=img[y0:y1+1,x0:x1+1]; im[ok]=out[ok]
    return Image.fromarray(np.clip(img,0,255).astype(np.uint8))
def load(n):
    g=read(ROOT/'skate'/(n+'.cup')); t=np.asarray(Image.open(ROOT/'skate'/(n+'.png')).convert('RGB')); return g,t
if __name__=='__main__':
    out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=True)
    body=read(ROOT/'p_body_am5.bin'); skin=(224,172,140)
    cl={k:load('minimalist_%s_am5'%k) for k in ('top','short','jeans')}
    combos={'corpo':[],'top':['top'],'short':['short'],'jeans':['jeans'],'top_short':['top','short'],'top_jeans':['top','jeans']}
    for name,parts in combos.items():
        ims=[]
        for v in ('front','back','side'):
            items=[(body,None,skin)]+[(cl[p][0],cl[p][1],None) for p in parts]
            ims.append(render(items,v))
        W=sum(i.width for i in ims); s=Image.new('RGB',(W,ims[0].height)); x=0
        for i in ims: s.paste(i,(x,0)); x+=i.width
        s.save(out/(name+'.png')); print(name)
