import sys,struct,os,json,math; sys.path.insert(0,'/home/claude/tools')
import sf,um,scene,etc,numpy as np
from PIL import Image
DATA='/home/claude/hds/Hds/assets/bin/Data'
os.chdir(DATA)
_cache={}
def F(n):
    if n.startswith('Library'): return None
    if n not in _cache: _cache[n]=scene.load(n)
    return _cache[n]
def ref(d,fid,pid):
    f=d if fid==0 else F(d['ext'][fid-1])
    return f,pid
def obj(f,pid):
    if f is None: return None
    for p,o,s,t,c in f['objs']:
        if p==pid: return o,s,c
def qmat(q):
    x,y,z,w=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def local(tr):
    M=np.eye(4); M[:3,:3]=qmat(tr['q'])*np.array(tr['s'])[None,:]; M[:3,3]=tr['p']; return M
def world(t,tid,memo={}):
    k=(id(t),tid)
    if k in memo: return memo[k]
    v=t[tid]; L=local(v)
    W=L if v['father'] not in t else world(t,v['father'])@L
    memo[k]=W; return W
def scene_items(name):
    d=F(name); g,t=scene.gos(d); b=d['data']
    mf={};mr={}
    for pid,off,sz,ti,cid in d['objs']:
        if cid==33:
            r=sf.R(b,off); r.i32(); gp=r.i64(); fid=r.i32(); mp=r.i64(); mf[gp]=(fid,mp)
        elif cid==23:
            r=sf.R(b,off); r.i32(); gp=r.i64(); mr[gp]=(off,sz)
    goT={v['go']:k for k,v in t.items()}
    items=[]
    for gp,(fid,mp) in mf.items():
        if gp not in mr or gp not in goT: continue
        f,pid=ref(d,fid,mp); o=obj(f,pid)
        if not o or o[2]!=43: continue
        # materials of renderer
        off,sz=mr[gp]
        def chk(fi,pi):
            if fi<0 or fi>len(d['ext']): return False
            ff,_=ref(d,fi,pi); oo=obj(ff,pi); return oo is not None and oo[2]==21
        mats,_=um.renderer_mats(d,off,sz,chk)
        # active flag
        items.append(dict(go=gp,name=g[gp][0],mesh=(id(f),fid,pid),f=f,mo=o,mats=[ref(d,*m) for m in (mats or [])],W=world(t,goT[gp]),d=d))
    return items
if __name__=='__main__':
    its=scene_items(sys.argv[1]); print(len(its))
    from collections import Counter
    print(Counter(i['name'].split(' (')[0] for i in its).most_common(15))

# ---------- GLB ----------
import io
TEXC={}
def get_tex(d,tp):
    fid,pid=tp
    if pid==0: return None
    f,_=ref(d,fid,pid); o=obj(f,pid)
    if not o or o[2]!=28: return None
    key=(id(f),pid)
    if key in TEXC: return TEXC[key]
    t=um.tex(f,o[0],o[1]); res=None
    if t['dlen']>0 and t['fmt'] in (34,45,47):
        img=etc.decode(t['data'],t['w'],t['h'],t['fmt'])[::-1]
        res=(t['name'],Image.fromarray(img))
    elif t['dlen']>0 and t['fmt'] in (4,):
        pass
    TEXC[key]=res; return res
def get_mat(d,mp):
    f,pid=mp; o=obj(f,pid)
    if not o: return None
    m=um.material(f,o[0],o[1])
    col=m['colors'].get('_Color',(1,1,1,1))
    tx=None
    if '_MainTex' in m['tex']: tx=get_tex(f,m['tex']['_MainTex'])
    return dict(name=m['name'],col=tuple(col),tex=tx,tp=m['tex'].get('_MainTex'))
def mesh_data(f,o):
    m=um.mesh(f,o[0],o[1]); ch=um.decode(m,m['vd'])
    if 0 not in ch: return None
    P=ch[0][:,:3]; N=ch[1][:,:3] if 1 in ch else None; UV=ch[4][:,:2] if 4 in ch else None
    subs=[]
    for s in m['subs']:
        ix=um.indices(m,s)
        if ix is None: continue
        subs.append(ix.astype(np.int64)+s['bv'])
    return dict(name=m['name'],P=P,N=N,UV=UV,subs=subs)
def build_glb(groups,path):
    """groups: dict matkey -> dict(mat=..., P,N,UV,I lists)"""
    bin=bytearray(); bvs=[]; acc=[]; prims=[]; mats=[]; texs=[]; imgs=[]
    def addbuf(arr,target):
        while len(bin)%4: bin.append(0)
        st=len(bin); bin.extend(arr.tobytes()); bvs.append(dict(buffer=0,byteOffset=st,byteLength=arr.nbytes,target=target)); return len(bvs)-1
    imgidx={}
    for k,gr in groups.items():
        P=np.concatenate(gr['P']).astype(np.float32); N=np.concatenate(gr['N']).astype(np.float32); UV=np.concatenate(gr['UV']).astype(np.float32)
        off=0; I=[]
        for p,i in zip(gr['P'],gr['I']): I.append(i+off); off+=len(p)
        I=np.concatenate(I).astype(np.uint32)
        mat=gr['mat']; m=dict(name=mat['name'],pbrMetallicRoughness=dict(baseColorFactor=[round(c,4) for c in mat['col'][:3]]+[1.0],metallicFactor=0.0,roughnessFactor=0.9),doubleSided=True)
        if mat['tex']:
            tn,im=mat['tex']
            if tn not in imgidx:
                bio=io.BytesIO(); im.save(bio,'PNG'); bb=bio.getvalue()
                while len(bin)%4: bin.append(0)
                st=len(bin); bin.extend(bb); bvs.append(dict(buffer=0,byteOffset=st,byteLength=len(bb)))
                imgs.append(dict(bufferView=len(bvs)-1,mimeType='image/png',name=tn)); texs.append(dict(source=len(imgs)-1,sampler=0)); imgidx[tn]=len(texs)-1
            m['pbrMetallicRoughness']['baseColorTexture']=dict(index=imgidx[tn])
        mats.append(m)
        pa=addbuf(P,34962); na=addbuf(N,34962); ua=addbuf(UV,34962); ia=addbuf(I,34963)
        base=len(acc)
        acc+= [dict(bufferView=pa,componentType=5126,count=len(P),type='VEC3',min=P.min(0).tolist(),max=P.max(0).tolist()),
               dict(bufferView=na,componentType=5126,count=len(N),type='VEC3'),
               dict(bufferView=ua,componentType=5126,count=len(UV),type='VEC2'),
               dict(bufferView=ia,componentType=5125,count=len(I),type='SCALAR')]
        prims.append(dict(attributes=dict(POSITION=base,NORMAL=base+1,TEXCOORD_0=base+2),indices=base+3,material=len(mats)-1))
    js=dict(asset=dict(version='2.0'),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(mesh=0,name='city')],meshes=[dict(primitives=prims)],
            materials=mats,accessors=acc,bufferViews=bvs,buffers=[dict(byteLength=len(bin))])
    if texs: js['textures']=texs; js['images']=imgs; js['samplers']=[dict(magFilter=9729,minFilter=9987,wrapS=10497,wrapT=10497)]
    j=json.dumps(js,separators=(',',':')).encode()
    while len(j)%4: j+=b' '
    while len(bin)%4: bin.append(0)
    out=struct.pack('<III',0x46546C67,2,12+8+len(j)+8+len(bin))+struct.pack('<II',len(j),0x4E4F534A)+j+struct.pack('<II',len(bin),0x004E4942)+bytes(bin)
    open(path,'wb').write(out); return len(out)
def export_scene(name,path,skip=lambda n:False):
    its=scene_items(name); groups={}; md={}
    for it in its:
        if skip(it['name']): continue
        key=(id(it['f']),it['mo'][0])
        if key not in md: md[key]=mesh_data(it['f'],it['mo'])
        m=md[key]
        if not m: continue
        W=it['W']; R=W[:3,:3]; T=W[:3,3]
        for si,ix in enumerate(m['subs']):
            if si>=len(it['mats']): continue
            mt=get_mat(it['d'],it['mats'][si])
            if not mt: continue
            mk=(mt['name'],mt['tp'])
            gr=groups.setdefault(mk,dict(mat=mt,P=[],N=[],UV=[],I=[]))
            used=np.unique(ix); remap=np.full(len(m['P']),-1); remap[used]=np.arange(len(used))
            P=(m['P'][used]@R.T+T); P[:,2]*=-1
            N=m['N'][used]@np.linalg.inv(R).T if m['N'] is not None else np.tile([0,1,0],(len(used),1))
            N[:,2]*=-1; N/= (np.linalg.norm(N,axis=1,keepdims=True)+1e-9)
            UV=m['UV'][used].copy() if m['UV'] is not None else np.zeros((len(used),2),np.float32); UV[:,1]=1-UV[:,1]
            I=remap[ix][:,[0,2,1]].reshape(-1)
            if np.linalg.det(R)<0: I=remap[ix][:,[0,1,2]].reshape(-1)
            gr['P'].append(P);gr['N'].append(N);gr['UV'].append(UV);gr['I'].append(I)
    return build_glb(groups,path),len(groups)
