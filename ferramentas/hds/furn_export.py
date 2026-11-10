import sys,os,re,io,json,struct,collections; sys.path.insert(0,'/home/claude/tools')
import bake, export, scene, um, numpy as np
from PIL import Image
LOD=re.compile(r'lod[_]?[1-9]|_LOD_[1-9]|dummy|dirt|collider|shadow|water_cyl',re.I)
OUT=re.compile(r'^(Dirt|Garbage|Player|DayNight)|^CarTraffic|Mustang|Charger|Rover|^Bmw|Tesla|Mercedes|^Ford|Scaffolding',re.I)
S=np.diag([1,1,-1.,1])
models=[]; mats={}; mlist=[]; tex={}; tlist=[]
def tid(name,im):
    k=(name,im.size)
    if k in tex: return tex[k]
    if max(im.size)>512: im=im.resize((min(512,im.size[0]),min(512,im.size[1])),Image.LANCZOS)
    tex[k]=len(tlist); tlist.append((name,im)); return tex[k]
def mid(m):
    k=(m['name'],m['tp'])
    if k in mats: return mats[k]
    ti=-1; cut=False
    if m['tex']:
        tn,im=m['tex']; ti=tid(tn,im)
        if im.mode=='RGBA' and not tn.endswith('_baked'): cut=bool((np.asarray(im.getchannel('A'))<128).mean()>0.02)
    mlist.append(dict(name=m['name'],col=[round(float(c),4) for c in m['col'][:3]],tex=ti,cut=cut)); mats[k]=len(mlist)-1; return mats[k]
for n in sorted(os.listdir('.')):
    if len(n)!=32: continue
    try: its=export.scene_items(n)
    except Exception: continue
    its=[i for i in its if not LOD.search(i['name'])]
    if not its: continue
    d=export.F(n); g,t=scene.gos(d); root=[g[v['go']][0] for k,v in t.items() if v['father'] not in t][0].split(' (')[0]
    if OUT.search(root): continue
    prims=collections.defaultdict(lambda:[[],[],[],[]]); ok=False
    for it in its:
        md=export.mesh_data(it['f'],it['mo'])
        if not md: continue
        M=S@it['W']@S; mir=bool(np.linalg.det(M[:3,:3])<0)
        mt=[export.get_mat(it['d'],x) for x in it['mats']]
        for si,ix in enumerate(md['subs']):
            if si>=len(mt) or not mt[si]: continue
            used=np.unique(ix); rm=np.full(len(md['P']),-1); rm[used]=np.arange(len(used))
            P=md['P'][used].astype(float).copy(); P[:,2]*=-1
            N=(md['N'][used].astype(float).copy() if md['N'] is not None else np.tile([0,1,0.],(len(used),1))); N[:,2]*=-1
            UV=md['UV'][used].astype(float).copy() if md['UV'] is not None else np.zeros((len(used),2)); UV[:,1]=1-UV[:,1]
            Pw=P@M[:3,:3].T+M[:3,3]; Nw=N@np.linalg.inv(M[:3,:3]); Nw/=np.linalg.norm(Nw,axis=1,keepdims=True)+1e-9
            tri=rm[ix]; tri=tri[:,[0,1,2]] if mir else tri[:,[0,2,1]]
            mm=mid(mt[si]); a=prims[mm]; off=sum(len(x) for x in a[0])
            a[0].append(Pw.astype(np.float32)); a[1].append(Nw.astype(np.float32)); a[2].append(UV.astype(np.float32)); a[3].append((tri.reshape(-1)+off).astype(np.uint32)); ok=True
    if not ok: continue
    allp=np.concatenate([p for a in prims.values() for p in a[0]])
    cat=re.sub(r'_?(View|Template)$','',root)
    models.append(dict(file=n,name=cat,prims=dict(prims),bbox=[allp.min(0).round(3).tolist(),allp.max(0).round(3).tolist()]))
print('modelos',len(models),'materiais',len(mlist),'texturas',len(tlist))
import pickle; pickle.dump((models,mlist,tlist),open('/home/claude/out/furn.pkl','wb'))
