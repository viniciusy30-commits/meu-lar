import export,numpy as np,json,struct,io,os,time
from PIL import Image
S=np.diag([1.,1.,-1.,1.])
scenes=[('House%d'%h,l) for h,l in zip([1,2,3,4,5,6,7,8,10,11,12],range(2,13))]+[('Apt1',13),('Apt2',14),('Apt3',15),('Office1',16),('House13',17),('House14',18),('House17',19),('House18',20),('House19',21),('House20',22)]
def skip(n):
    n=n.split(' (')[0]; return n.startswith('Clouds') or n.endswith(('_lod_1','_lod_2','_LOD1','_LOD2')) or '_lod_1' in n or '_lod_2' in n
pieces={}   # key -> idx
plist=[]    # dict(name,subs:[(matkey,P,N,UV,I)])
matkeys={}; mats=[]; texs={}; timgs=[]
def matid(mt):
    k=(mt['name'],mt['tp'])
    if k in matkeys: return matkeys[k]
    ti=-1
    if mt['tex']:
        tn,im=mt['tex']
        if tn not in texs:
            if max(im.size)>512: im=im.resize((512,512) if im.size[0]==im.size[1] else (min(512,im.size[0]),min(512,im.size[1])),Image.LANCZOS)
            texs[tn]=len(timgs); timgs.append((tn,im))
        ti=texs[tn]
    cut=False
    if ti>=0:
        im=timgs[ti][1]
        if im.mode=='RGBA':
            a=np.asarray(im.getchannel('A')); cut=bool((a<128).mean()>0.02)
    mats.append(dict(name=mt['name'],col=[round(float(c),4) for c in mt['col'][:3]],tex=ti,cut=cut)); matkeys[k]=len(mats)-1; return matkeys[k]
layouts={}; md={}
t0=time.time()
for name,l in scenes:
    inst=[]
    for it in export.scene_items('level%d'%l):
        if skip(it['name']): continue
        mk=(id(it['f']),it['mo'][0])
        if mk not in md: md[mk]=export.mesh_data(it['f'],it['mo'])
        m=md[mk]
        if not m: continue
        mt=[export.get_mat(it['d'],x) for x in it['mats']]
        mids=tuple(matid(x) if x else -1 for x in mt)
        W=it['W']; mir=bool(np.linalg.det(W[:3,:3])<0)
        pk=(mk,mids,mir)
        if pk not in pieces:
            subs=[]
            for si,ix in enumerate(m['subs']):
                if si>=len(mids) or mids[si]<0: continue
                used=np.unique(ix); rm=np.full(len(m['P']),-1); rm[used]=np.arange(len(used))
                P=m['P'][used].copy(); P[:,2]*=-1
                N=(m['N'][used].copy() if m['N'] is not None else np.tile([0,1,0.],(len(used),1))); N[:,2]*=-1
                UV=m['UV'][used].copy() if m['UV'] is not None else np.zeros((len(used),2),np.float32); UV[:,1]=1-UV[:,1]
                tri=rm[ix]; tri=tri[:,[0,1,2]] if mir else tri[:,[0,2,1]]
                subs.append((mids[si],P.astype(np.float32),N.astype(np.float32),UV.astype(np.float32),tri.reshape(-1).astype(np.uint32)))
            pieces[pk]=len(plist); plist.append(dict(name=m['name'],subs=subs))
        M=S@W@S
        inst.append([pieces[pk]]+[round(float(x),5) for x in M[:3,:].reshape(-1)])  # 12 floats: 3x4 row-major
    layouts[name]=inst; print(name,len(inst),len(plist),len(mats),len(timgs),'%.0fs'%(time.time()-t0),flush=True)
os.makedirs('/home/claude/out/hds',exist_ok=True)
# write kit.glb: one node per piece
bin=bytearray(); bvs=[]; acc=[]; meshes=[]; nodes=[]
def ab(arr,tg=None):
    while len(bin)%4: bin.append(0)
    st=len(bin); bin.extend(arr.tobytes()); d=dict(buffer=0,byteOffset=st,byteLength=arr.nbytes)
    if tg: d['target']=tg
    bvs.append(d); return len(bvs)-1
imgs=[];textures=[]
for tn,im in timgs:
    bio=io.BytesIO(); im.save(bio,'PNG',optimize=True); bb=bio.getvalue()
    while len(bin)%4: bin.append(0)
    st=len(bin); bin.extend(bb); bvs.append(dict(buffer=0,byteOffset=st,byteLength=len(bb))); imgs.append(dict(bufferView=len(bvs)-1,mimeType='image/png',name=tn)); textures.append(dict(source=len(imgs)-1,sampler=0))
gm=[]
for m in mats:
    pm=dict(baseColorFactor=m['col']+[1.0],metallicFactor=0.0,roughnessFactor=0.9)
    if m['tex']>=0: pm['baseColorTexture']=dict(index=m['tex'])
    gm.append(dict(name=m['name'],pbrMetallicRoughness=pm,doubleSided=True,**({'alphaMode':'MASK','alphaCutoff':0.5} if m['cut'] else {})))
for pi,p in enumerate(plist):
    prims=[]
    for (mi,P,N,UV,I) in p['subs']:
        b0=len(acc)
        acc+=[dict(bufferView=ab(P,34962),componentType=5126,count=len(P),type='VEC3',min=P.min(0).tolist(),max=P.max(0).tolist()),
              dict(bufferView=ab(N,34962),componentType=5126,count=len(N),type='VEC3'),
              dict(bufferView=ab(UV,34962),componentType=5126,count=len(UV),type='VEC2')]
        if len(P)<65536: I2=I.astype(np.uint16); ct=5123
        else: I2=I; ct=5125
        acc.append(dict(bufferView=ab(I2,34963),componentType=ct,count=len(I2),type='SCALAR'))
        prims.append(dict(attributes=dict(POSITION=b0,NORMAL=b0+1,TEXCOORD_0=b0+2),indices=b0+3,material=mi))
    meshes.append(dict(primitives=prims)); nodes.append(dict(name='p%d'%pi,mesh=pi))
js=dict(asset=dict(version='2.0'),scene=0,scenes=[dict(nodes=list(range(len(nodes))))],nodes=nodes,meshes=meshes,materials=gm,textures=textures,images=imgs,samplers=[dict(magFilter=9729,minFilter=9987,wrapS=10497,wrapT=10497)],accessors=acc,bufferViews=bvs,buffers=[dict(byteLength=len(bin))])
j=json.dumps(js,separators=(',',':')).encode()
while len(j)%4: j+=b' '
while len(bin)%4: bin.append(0)
open('/home/claude/out/hds/kit.glb','wb').write(struct.pack('<III',0x46546C67,2,12+8+len(j)+8+len(bin))+struct.pack('<II',len(j),0x4E4F534A)+j+struct.pack('<II',len(bin),0x004E4942)+bytes(bin))
for n,i in layouts.items(): json.dump(i,open('/home/claude/out/hds/%s.json'%n,'w'),separators=(',',':'))
print('pieces',len(plist),'mats',len(mats),'tex',len(timgs))
