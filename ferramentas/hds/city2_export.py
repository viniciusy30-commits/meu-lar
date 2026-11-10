import sys,json,io,struct,math,re
sys.path.insert(0,'/home/claude/tools')
import numpy as np, citygen
from PIL import Image
R=citygen.build(NX=4,NZ=2); T=citygen.templates(R); P=citygen.finish(R,T); citygen.extras(R,P)
ctx=R.ctx; xr,zr=ctx['xr'],ctx['zr']
plist=R.plist; inst=R.inst
def Mof(r): return np.array(r[1:13],float).reshape(3,4)
def wverts(r):
    M=Mof(r); out=[]
    for (mi,Pv,Nv,UV,I) in plist[r[0]]['subs']:
        out.append((Pv@M[:,:3].T+M[:,3],I.reshape(-1,3)))
    return out
# ---- caixas das casas (só corpo: sem cerca) e colisões
CS=0.25
cells=set()
pb={}
for r in inst:
    pi,kind,plot=r[0],r[13],r[14]; nm=plist[pi]['name'].lower()
    fence=bool(re.search(r'fence|post|gate',nm))
    for V,I in wverts(r):
        if plot>=0 and not fence and nm not in('baseboard_mesh','ao_mesh') :
            b=pb.setdefault(plot,[1e9,1e9,-1e9,-1e9]); b[0]=min(b[0],V[:,0].min()); b[1]=min(b[1],V[:,2].min()); b[2]=max(b[2],V[:,0].max()); b[3]=max(b[3],V[:,2].max())
        if kind!=1 or 'gate' in nm: continue
        if nm.startswith('lamp') or 'tree' in nm: continue
        A=V[I[:,0]];B=V[I[:,1]];C=V[I[:,2]]
        ymin=np.minimum(np.minimum(A[:,1],B[:,1]),C[:,1]); ymax=np.maximum(np.maximum(A[:,1],B[:,1]),C[:,1])
        ok=(ymax>0.25)&(ymin<1.8)
        A,B,C=A[ok],B[ok],C[ok]
        for a,b,c in zip(A,B,C):
            e=max(np.linalg.norm(b-a),np.linalg.norm(c-a),np.linalg.norm(c-b)); n=max(1,int(math.ceil(e/0.12)))
            ii,jj=np.meshgrid(np.arange(n+1),np.arange(n+1)); m=(ii+jj)<=n; u=(ii[m]/n)[:,None]; v=(jj[m]/n)[:,None]
            pts=a+(b-a)*u+(c-a)*v; pts=pts[(pts[:,1]>0.25)&(pts[:,1]<1.8)]
            if len(pts): 
                for x,z in set(map(tuple,np.floor(pts[:,[0,2]]/CS).astype(int))): cells.add((x,z))
print('cells',len(cells))
# merge cells -> rects
rows={}
for x,z in cells: rows.setdefault(z,[]).append(x)
runs={}
for z,xs in rows.items():
    xs.sort(); s=p=xs[0]
    for x in xs[1:]+[None]:
        if x is not None and x==p+1: p=x; continue
        runs.setdefault((s,p),[]).append(z); 
        if x is not None: s=p=x
rects=[]
for (s,e),zs in runs.items():
    zs.sort(); a=p=zs[0]
    for z in zs[1:]+[None]:
        if z is not None and z==p+1: p=z; continue
        rects+= [s*CS,a*CS,(e+1)*CS,(p+1)*CS]
        if z is not None: a=p=z
print('solids',len(rects)//4)
# ---- GLB
used=sorted(set(r[0] for r in inst)); remap={p:i for i,p in enumerate(used)}
mats_used=sorted(set(s[0] for p in used for s in plist[p]['subs'])); mremap={m:i for i,m in enumerate(mats_used)}
tex_used=sorted(set(R.mats[m]['tex'] for m in mats_used if R.mats[m]['tex']>=0)); tremap={t:i for i,t in enumerate(tex_used)}
bin=bytearray(); bvs=[]; acc=[]; meshes=[]; nodes=[]
def ab(arr,tg=None):
    while len(bin)%4: bin.append(0)
    st=len(bin); bin.extend(arr.tobytes()); d=dict(buffer=0,byteOffset=st,byteLength=arr.nbytes)
    if tg: d['target']=tg
    bvs.append(d); return len(bvs)-1
imgs=[];textures=[]
for t in tex_used:
    tn,im=R.timgs[t]; bio=io.BytesIO(); im.save(bio,'PNG',optimize=True); bb=bio.getvalue()
    while len(bin)%4: bin.append(0)
    st=len(bin); bin.extend(bb); bvs.append(dict(buffer=0,byteOffset=st,byteLength=len(bb))); imgs.append(dict(bufferView=len(bvs)-1,mimeType='image/png',name=tn)); textures.append(dict(source=len(imgs)-1,sampler=0))
gm=[]
for m in mats_used:
    mm=R.mats[m]; pm=dict(baseColorFactor=mm['col']+[1.0],metallicFactor=0.0,roughnessFactor=0.9)
    if mm['tex']>=0: pm['baseColorTexture']=dict(index=tremap[mm['tex']])
    gm.append(dict(name=mm['name'],pbrMetallicRoughness=pm,doubleSided=True,**({'alphaMode':'MASK','alphaCutoff':0.5} if mm['cut'] else {})))
for p in used:
    prims=[]
    for (mi,Pv,Nv,UV,I) in plist[p]['subs']:
        b0=len(acc)
        acc+=[dict(bufferView=ab(Pv,34962),componentType=5126,count=len(Pv),type='VEC3',min=Pv.min(0).tolist(),max=Pv.max(0).tolist()),
              dict(bufferView=ab(Nv,34962),componentType=5126,count=len(Nv),type='VEC3'),
              dict(bufferView=ab(UV,34962),componentType=5126,count=len(UV),type='VEC2')]
        assert len(Pv)<65536
        acc.append(dict(bufferView=ab(I.astype(np.uint16),34963),componentType=5123,count=len(I),type='SCALAR'))
        prims.append(dict(attributes=dict(POSITION=b0,NORMAL=b0+1,TEXCOORD_0=b0+2),indices=b0+3,material=mremap[mi]))
    meshes.append(dict(primitives=prims)); nodes.append(dict(name='p%d'%remap[p],mesh=len(meshes)-1))
js=dict(asset=dict(version='2.0'),scene=0,scenes=[dict(nodes=list(range(len(nodes))))],nodes=nodes,meshes=meshes,materials=gm,textures=textures,images=imgs,samplers=[dict(magFilter=9729,minFilter=9987,wrapS=10497,wrapT=10497)],accessors=acc,bufferViews=bvs,buffers=[dict(byteLength=len(bin))])
j=json.dumps(js,separators=(',',':')).encode()
while len(j)%4: j+=b' '
while len(bin)%4: bin.append(0)
import os; os.makedirs('/home/claude/out/c2',exist_ok=True)
open('/home/claude/out/c2/city2.glb','wb').write(struct.pack('<III',0x46546C67,2,12+8+len(j)+8+len(bin))+struct.pack('<II',len(j),0x4E4F534A)+j+struct.pack('<II',len(bin),0x004E4942)+bytes(bin))
# ---- json
rt=lambda v:round(float(v),3)
plots=[]
for k,pl in enumerate(P):
    b=pb[k]; plots.append(dict(name=pl['name'],x0=rt(b[0]),z0=rt(b[1]),x1=rt(b[2]),z1=rt(b[3]),x=rt(pl['x']),z=rt(pl['z'])))
out=dict(inst=[[remap[r[0]]]+[round(x,3) for x in r[1:13]]+[r[13],r[14]] for r in inst],plots=plots,solids=[round(x,2) for x in rects],
  xr=xr,zr=zr,res=[ (xr[1]+xr[2])/2,(zr[0]+zr[1])/2 ],bounds=[xr[0],zr[0],xr[-1],zr[-1]])
json.dump(out,open('/home/claude/out/c2/city2.json','w'),separators=(',',':'))
print('glb',os.path.getsize('/home/claude/out/c2/city2.glb')//1024,'KB json',os.path.getsize('/home/claude/out/c2/city2.json')//1024,'KB pieces',len(used),'mats',len(mats_used),'tex',len(tex_used))
print(plots[:2])
