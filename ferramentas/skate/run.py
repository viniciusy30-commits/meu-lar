import sys, os, numpy as np
sys.path.insert(0,'/home/claude/work/skate')
from PIL import Image
from sk_common import *; from sk_garments import *; from sk_bake import *; from sk_paint import *
ART=np.asarray(Image.open(CUTE+'skatetee.png').convert('RGB'))
OUT='/home/claude/work/skate/out/'
os.makedirs(OUT,exist_ok=True)

def bake(P,N,tri,btype_fn):
    P1,N1,T1,A1=prepare(P,N,tri,btype_fn)
    # normais recalculadas depois das beiradas
    Pn,Nn,An,UV,T=unwrap(P1,N1,T1,A1)
    feat=np.hstack([Pn,Nn,An]).astype(np.float32)
    F,mask=raster_attrs(UV,T,feat)
    return Pn,Nn,UV,T,F

def do_tee(B,g):
    P,N,tri,info=build_tee(B)
    bt=lambda p: 2 if (p[1]>B.neck_y-12 and abs(p[0])<12) else (1 if abs(p[0])>B.sh[0]+4 else 0)
    Pn,Nn,UV,T,F=bake(P,N,tri,bt)
    img=paint_tee(F,B,ART)
    Image.fromarray(img).save(OUT+'%s_tee.png'%g,optimize=True)
    bi,bw=transfer_weights(B,Pn); write_cup(OUT+'%s_tee.cup'%g,Pn,Nn,UV,T,bi,bw)
    return Pn,Nn,UV,T,img
def do_shorts(B,g):
    P,N,tri,info=build_shorts(B)
    bt=lambda p: 3 if p[1]>info['waist']-6 else 0
    Pn,Nn,UV,T,F=bake(P,N,tri,bt)
    img=paint_shorts(F,B,info)
    Image.fromarray(img).save(OUT+'%s_shorts.png'%g,optimize=True)
    bi,bw=transfer_weights(B,Pn); write_cup(OUT+'%s_shorts.cup'%g,Pn,Nn,UV,T,bi,bw)
    return Pn,Nn,UV,T,img
def do_shoes(B,g):
    d=open(CUTE+'p_feet_allstar.bin','rb').read(); nv,ni,fl=struct.unpack_from('<3I',d,4)
    v=np.frombuffer(d,DT,nv,16); P=v['p'].astype(float); N=v['n'].astype(float); UV=v['uv'].astype(float)
    T=np.frombuffer(d,'<u2',ni,16+nv*44).reshape(-1,3).astype(np.int64)
    m=(B.P0[:,1]<14)&(B.P0[:,0]>0); lo=B.P0[m].min(0); hi=B.P0[m].max(0)
    bl=np.array([6.9,-0.2,-4.8]); bh=np.array([15.9,12.0,17.7])
    sc=(hi-lo)/(bh-bl); sc[1]=1.0
    sg=np.sign(P[:,0]); ax=np.abs(P[:,0])
    P2=P.copy(); P2[:,0]=sg*(lo[0]+(ax-bl[0])*sc[0]); P2[:,1]=(P[:,1]-bl[1])*sc[1]+lo[1]; P2[:,2]=lo[2]+(P[:,2]-bl[2])*sc[2]
    N2=N/sc; N2/=np.linalg.norm(N2,axis=1,keepdims=True)
    # recorta a textura do atlas e remapeia UV
    atlas=Image.open(CUTE+'extra2.png').convert('RGBA'); AWt,AHt=atlas.size
    x0,x1,y0,y1=192,1216,640,896
    tex=atlas.crop((x0,y0,x1,y1)).convert('RGB')
    UV2=np.stack([(UV[:,0]*AWt-x0)/(x1-x0),(UV[:,1]*AHt-y0)/(y1-y0)],1)
    assert UV2.min()>=-0.001 and UV2.max()<=1.001,(UV2.min(),UV2.max())
    tex.save(OUT+'%s_shoes.png'%g)
    bi,bw=transfer_weights(B,P2); write_cup(OUT+'%s_shoes.cup'%g,P2,N2,UV2,T,bi,bw)
    return len(P2)
if __name__=='__main__':
    g=sys.argv[1]; B=load_body(g)
    which=sys.argv[2] if len(sys.argv)>2 else 'both'
    if which in('both','tee'): r=do_tee(B,g); print('tee',len(r[0]),len(r[3]))
    if which in('both','shoes'): print('shoes',do_shoes(B,g))
    if which in('both','shorts'): r=do_shorts(B,g); print('shorts',len(r[0]),len(r[3]))
