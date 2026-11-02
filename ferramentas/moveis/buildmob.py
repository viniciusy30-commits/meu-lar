import sys,os,json,math,struct,shutil
sys.path.insert(0,'/tmp/claude-0/-home-claude/341b3dbd-d941-51da-bfe9-860592c8dd80/scratchpad')
import numpy as np
from PIL import Image
import mobparse as mp
OUT=sys.argv[1] if len(sys.argv)>1 else '/tmp/claude-0/-home-claude/341b3dbd-d941-51da-bfe9-860592c8dd80/scratchpad/out_mob'
SPEC=json.load(open('/tmp/claude-0/-home-claude/341b3dbd-d941-51da-bfe9-860592c8dd80/scratchpad/mobspec.json'))
os.makedirs(OUT+'/tex',exist_ok=True)
# Mt ids do app: PLAIN0 FLOOR_L1 FLOOR_D2 TILE3 STONE4 PLASTER5 WOOD6 FABRIC7 GRASS8 PAVER9 RUG10 METAL11 GLASS12
def spec_mat(mi):
    s=mi.get('smooth'); me=mi.get('metal') or 0
    if s is None: s=0.3
    if me>0.5: return 11
    if s<0.15: return 7
    if s<0.3: return 0
    if s<0.5: return 6
    return 1
texcache={}
def tex_out(rel):
    if rel in texcache: return texcache[rel]
    src=mp.W+'home/'+mp.M[rel]+'/asset'
    im=Image.open(src); alpha=False
    if im.mode in('RGBA','LA','P'):
        im=im.convert('RGBA'); a=np.array(im)[:,:,3]; alpha=bool((a<250).any())
        if not alpha: im=im.convert('RGB')
    else: im=im.convert('RGB')
    w,h=im.size
    def pot(x): 
        p=64
        while p*2<=min(x,1024)*1.2 and p<1024: p*=2
        return p
    im=im.resize((pot(w),pot(h)),Image.LANCZOS)
    base=os.path.splitext(os.path.basename(rel))[0].lower().replace(' ','_')
    ext='png' if alpha else 'jpg'
    fn=base+'.'+ext
    if alpha: im.save(OUT+'/tex/'+fn,optimize=True)
    else: im.save(OUT+'/tex/'+fn,quality=86)
    texcache[rel]=(fn,alpha,np.array(im.convert('RGBA')))
    return texcache[rel]
def rotY(P,k):
    c=[1,0,-1,0][k%4]; s=[0,1,0,-1][k%4]
    x=P[:,0]*c+P[:,2]*s; z=-P[:,0]*s+P[:,2]*c
    return np.stack([x,P[:,1],z],1)
def build(name,sp):
    d=mp.load(name); V=d['V']; polys=d['polys']; cv=d['cv']
    rot=sp.get('rot',0)
    P=rotY(V,rot)
    mn=P.min(0); mx=P.max(0); size=mx-mn
    s0=1.0
    long=max(size[0],size[2])
    cap=99.0
    if long>cap: s0=cap/long
    sz=size*s0
    cw=sp.get('cw') or max(1,math.ceil(sz[0]-0.1)); ch=sp.get('ch') or max(1,math.ceil(sz[2]-0.1))
    s=min(s0,(cw-0.04)/size[0] if size[0]>0 else 9,(ch-0.04)/size[2] if size[2]>0 else 9)
    s=1.0
    cx=(mn[0]+mx[0])/2; cz=(mn[2]+mx[2])/2
    def tf(Pv): return np.stack([(Pv[:,0]-cx)*s+cw/2,(Pv[:,1]-mn[1])*s,(Pv[:,2]-cz)*s+ch/2],1)
    # normals / uv per corner
    ncorner=len(cv)
    N=d['N']
    if d['mapn']=='ByVertice': cn=N[cv]
    elif d['nidx'] is not None and len(d['nidx'])==ncorner and len(N)!=ncorner: cn=N[d['nidx']]
    else: cn=N[:ncorner]
    cn=rotY(cn,rot)
    UV=d['UV']; cuv=UV[d['UVI']] if d['UVI'] is not None else UV[:ncorner]
    parts={}
    for pi,poly in enumerate(polys):
        mi=d['mats'][pi] if d['mapm']=='ByPolygon' else d['mats'][0]
        parts.setdefault(int(mi),[]).append(poly)
    outparts=[]
    for mi,pl in sorted(parts.items()):
        mname=d['names'][mi]; info=mp.MATS.get(mname)
        if info is None: base=mname.split('.')[0]; info=mp.MATS.get(base)
        if info is None: print('WARN no mat',name,mname); info=dict(tex=None,color=(.8,.8,.8,1),smooth=.3,metal=0)
        keymap={};verts=[];idx=[]
        tex=info['tex']; tsx=tsy=1;tox=toy=0; fn=None; alpha=False
        if tex:
            fn,alpha,_=tex_out(tex[0]); tsx,tsy,tox,toy=tex[1:5]
        for poly in pl:
            ids=[]
            for c in poly:
                key=(int(cv[c]),c if d['mapn']!='ByVertice' else -1,)
                key=(int(cv[c]),tuple(np.round(cn[c],3)),tuple(np.round(cuv[c],4)))
                if key not in keymap:
                    keymap[key]=len(verts); verts.append(c)
                ids.append(keymap[key])
            for j in range(1,len(ids)-1): idx+= [ids[0],ids[j],ids[j+1]]
        vc=np.array(verts)
        pos=tf(P[cv[vc]]); nor=cn[vc]; nl=np.linalg.norm(nor,axis=1,keepdims=True); nor=nor/np.maximum(nl,1e-9)
        uv=cuv[vc].copy(); uv[:,0]=uv[:,0]*tsx+tox; uv[:,1]=1-(uv[:,1]*tsy+toy)
        # winding: keep (no culling in app)
        col=info['color']; 
        outparts.append(dict(mat=spec_mat(info),tex=fn,cut=0.5 if alpha else 0.0,tint=col,pos=pos.astype('<f4'),nor=nor.astype('<f4'),uv=uv.astype('<f4'),idx=np.array(idx,dtype='<u2'),mname=mname))
    return dict(parts=outparts,cw=cw,ch=ch,height=float((mx[1]-mn[1])*s),scale=s,size=size)
def write(name,b):
    texs=[];
    for p in b['parts']:
        if p['tex'] and p['tex'] not in texs: texs.append(p['tex'])
    o=bytearray(b'MOB1'); o+=struct.pack('<4I',len(texs),len(b['parts']),b['cw'],b['ch'])
    for t in texs:
        e=t.encode(); o+=struct.pack('<B',len(e))+e
    for p in b['parts']:
        o+=struct.pack('<bhbffff',p['mat'],texs.index(p['tex']) if p['tex'] else -1,1 if p['cut']>0 else 0,*p['tint'])
        o+=struct.pack('<II',len(p['pos']),len(p['idx']))
        for i in range(len(p['pos'])): o+=p['pos'][i].tobytes()+p['nor'][i].tobytes()+p['uv'][i].tobytes()
        o+=p['idx'].tobytes()
    open(OUT+'/'+name+'.bin','wb').write(o); return len(o)
if __name__=='__main__':
    res={}
    for name,sp in SPEC.items():
        b=build(name,sp); n=write(name,b)
        res[name]=dict(**sp,cw=b['cw'],ch=b['ch'],h=round(b['height'],2),scale=round(b['scale'],3),bytes=n,nv=sum(len(p['pos']) for p in b['parts']))
        print(name,res[name])
    json.dump(res,open(OUT+'/_info.json','w'),indent=1)
    print('textures',len(texcache),sum(os.path.getsize(OUT+'/tex/'+f) for f in os.listdir(OUT+'/tex')))
