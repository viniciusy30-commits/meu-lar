import sys, os, numpy as np
sys.path.insert(0,'/home/claude/work/skate')
from PIL import Image
from sk_common import *; from sk_garments import *; from sk_bake import *; from sk_paint import *; from sk_paint2 import *
def bake(P,N,tri,btype_fn,extra=None):
    P1,N1,T1,A1=prepare(P,N,tri,btype_fn,extra)
    Pn,Nn,An,UV,T=unwrap(P1,N1,T1,A1)
    feat=np.hstack([Pn,Nn,An]).astype(np.float32)
    F,mask=raster_attrs(UV,T,feat)
    return Pn,Nn,UV,T,F,An
from prev_cg import TEE
OUT='/home/claude/work/skate/out2/'; os.makedirs(OUT,exist_ok=True)
ART=np.asarray(Image.open('/home/claude/work/skate/chaos_art.png').convert('RGBA'))
def do_tee(B,g):
    P,N,tri,info=build_tee(B,TEE)
    bt=lambda p: 2 if (p[1]>B.neck_y-12 and abs(p[0])<12) else (1 if abs(p[0])>B.sh[0]+4 else 0)
    Pn,Nn,UV,T,F,An=bake(P,N,tri,bt,(np.zeros(len(P)),info['ringf'],info['ry0']))
    Image.fromarray(paint_tee2(F,B,ART)).save(OUT+'%s_tee.png'%g,optimize=True)
    bi,bw=transfer_weights2(B,Pn,An); write_cup(OUT+'%s_tee.cup'%g,Pn,Nn,UV,T,bi,bw)
def do_cargo(B,g):
    P,N,tri,info=build_cargo(B)
    bt=lambda p: 3 if p[1]>info['waist']-6 else 0
    Pn,Nn,UV,T,F,An=bake(P,N,tri,bt,(info['leg'],np.zeros(len(P)),np.zeros(len(P))))
    Image.fromarray(paint_cargo(F,B,info)).save(OUT+'%s_cargo.png'%g,optimize=True)
    bi,bw=transfer_weights2(B,Pn,An); write_cup(OUT+'%s_cargo.cup'%g,Pn,Nn,UV,T,bi,bw)
def do_shoes(B,g):
    import struct
    from scipy import ndimage
    d=open(CUTE+'p_feet_allstar.bin','rb').read(); nv,ni,fl=struct.unpack_from('<3I',d,4)
    v=np.frombuffer(d,DT,nv,16); P=v['p'].astype(float); N=v['n'].astype(float); UV=v['uv'].astype(float)
    T=np.frombuffer(d,'<u2',ni,16+nv*44).reshape(-1,3).astype(np.int64)
    CUT=9.6
    keep=P[T][:,:,1].mean(1)<CUT
    T=T[keep]
    # beirada acolchoada na borda do corte
    be=[e for e in boundary_edges(T) if P[e[0],1]>CUT-1.2 and P[e[1],1]>CUT-1.2]
    inner={}; Pl=[P]; Nl=[N]; UVl=[UV]; n=len(P); q=[]
    def get(vv):
        nonlocal n
        if vv not in inner:
            inner[vv]=n; n+=1; Pl.append((P[vv]-N[vv]*0.9+np.array([0,0.35,0]))[None]); Nl.append((-N[vv])[None]); UVl.append(UV[vv][None])
        return inner[vv]
    for a,b in be:
        ia,ib=get(a),get(b); q+=[(a,b,ib),(a,ib,ia)]
    T=np.vstack([T,np.array(q,np.int64).reshape(-1,3)]); P=np.vstack(Pl); N=np.vstack(Nl); UV=np.vstack(Ul) if False else np.vstack(UVl)
    # compacta
    u,inv=np.unique(T.ravel(),return_inverse=True); P=P[u]; N=N[u]; UV=UV[u]; T=inv.reshape(-1,3)
    # encaixe no pé do Sims
    m=(B.P0[:,1]<14)&(B.P0[:,0]>0); lo=B.P0[m].min(0); hi=B.P0[m].max(0)
    bl=np.array([6.9,-0.2,-4.8]); bh=np.array([15.9,12.0,17.7]); sc=(hi-lo)/(bh-bl); sc[1]=1.0
    sg=np.sign(P[:,0]); ax=np.abs(P[:,0]); P2=P.copy()
    P2[:,0]=sg*(lo[0]+(ax-bl[0])*sc[0]); P2[:,1]=(P[:,1]-bl[1])*sc[1]+lo[1]; P2[:,2]=lo[2]+(P[:,2]-bl[2])*sc[2]
    N2=N/sc; N2/=np.linalg.norm(N2,axis=1,keepdims=True)
    atlas=Image.open(CUTE+'extra2.png').convert('RGB'); AWt,AHt=atlas.size
    x0,x1,y0,y1=192,1216,640,896
    tex=np.asarray(atlas.crop((x0,y0,x1,y1))).astype(np.float32).copy()
    UV2=np.stack([(UV[:,0]*AWt-x0)/(x1-x0),(UV[:,1]*AHt-y0)/(y1-y0)],1)
    # --- repinta a tela lateral (lona) como couro branco com detalhes pretos (panda)
    CW,CH=320,216; ox,oy=40,36; Z0,Z1,Y0,Y1=-7.0,22.0,-2.6,18.0
    jj,ii=np.mgrid[0:CH,0:CW].astype(np.float32)
    zz=Z0+(ii+0.5)/CW*(Z1-Z0); yy=Y1-(jj+0.5)/CH*(Y1-Y0)
    img=np.zeros((CH,CW,3),np.float32)+np.array([238,238,234],np.float32)
    grain=ndimage.gaussian_filter(np.random.default_rng(1).standard_normal((CH,CW)).astype(np.float32),0.7)*3.0
    img+=grain[...,None]
    # perfurações no bico
    per=(zz>12.5)&(yy>0.6)&(yy<6.5)&(((ii%7)<2)&((jj%7)<2)); img[per]*=0.78
    black=np.array([22,22,25],np.float32); 
    heel=((zz+7.0)/6.4)**2+((yy-3.6)/7.6)**2<1.0
    collar=yy>8.2
    lz=9.6-(yy-6.5)*(5.3/9.4); eyestay=(np.abs(zz-lz)<2.1)&(yy>2.0)
    wing=((zz-2.4)/6.3)**2+((yy-4.4)/3.6)**2<1.0
    toecap=(zz>16.8)&(yy<5.8)&(((zz-16.8)/3.2)**2+((yy-0.5)/6.0)**2<1.0)
    for msk in (heel,collar,eyestay,wing): img[msk]=black
    img[toecap]=np.array([226,226,222],np.float32)
    # costuras brancas/cinzas dentro do preto e pretas no branco
    def edge(msk,w=2):
        e=ndimage.binary_dilation(msk,iterations=w)^ndimage.binary_dilation(msk,iterations=w-1) if w>1 else msk
        return e
    for msk in (heel,wing,eyestay): 
        inner_=ndimage.binary_erosion(msk,iterations=4)^ndimage.binary_erosion(msk,iterations=5); dash=((ii+jj)%6)<3
        img[inner_&dash]=np.array([205,205,200],np.float32)
    out_=ndimage.binary_dilation(collar,iterations=3)&~collar; img[out_&(((ii)%6)<3)]=np.array([90,90,92],np.float32)
    tex[oy:oy+CH,ox:ox+CW]=np.clip(img,0,255)
    # --- sola/borracha: tira o quadrado preto (fica branca)
    RX,RY=374,36
    rub=tex[RY:RY+CH,RX:RX+CW]; dark=rub.mean(2)<90; dark[165:]=False
    rub[dark]=np.array([236,236,232],np.float32)
    # --- selo do tornozelo: preto liso
    tex[36:36+128,848:848+128]=np.array([22,22,25],np.float32)
    tex=np.clip(tex,0,255).astype(np.uint8)
    Image.fromarray(tex).save(OUT+'%s_shoes.png'%g,optimize=True)
    bi,bw=transfer_weights(B,P2); write_cup(OUT+'%s_shoes.cup'%g,P2,N2,UV2,T,bi,bw)
    return len(P2)
if __name__=='__main__':
    g=sys.argv[1]; B=load_body(g); which=sys.argv[2:] or ['tee','cargo','shoes']
    if 'tee' in which: do_tee(B,g)
    if 'cargo' in which: do_cargo(B,g)
    if 'shoes' in which: print('shoes',do_shoes(B,g))
