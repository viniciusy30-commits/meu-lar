import sys,json,re,collections
sys.path.insert(0,'/tmp/claude-0/-home-claude/341b3dbd-d941-51da-bfe9-860592c8dd80/scratchpad')
import fbxr,numpy as np
W='/tmp/claude-0/-home-claude/341b3dbd-d941-51da-bfe9-860592c8dd80/scratchpad/w/'
M=json.load(open(W+'homemap.json')); B='Assets/home-set-2020s/'
G2P={}  # guid -> pathname
for k,d in M.items():
    meta=W+'home/'+d+'/asset.meta'
    try:
        for ln in open(meta):
            if ln.startswith('guid:'): G2P[ln.split()[1]]=k
    except: pass
def mat_info(path):
    t=open(path).read()
    name=re.search(r'\nMaterial:.*?m_Name: ([^\n]*)',t,re.S).group(1).strip()
    shader=re.search(r'm_Shader:.*guid: (\w+)',t).group(1)
    def tex(prop):
        m=re.search(r'- '+prop+r':\n\s+m_Texture: \{fileID: (-?\d+), guid: (\w+).*\n\s+m_Scale: \{x: ([-\d.e]+), y: ([-\d.e]+)\}\n\s+m_Offset: \{x: ([-\d.e]+), y: ([-\d.e]+)\}',t)
        if m and m.group(1)!='0': return G2P.get(m.group(2)),float(m.group(3)),float(m.group(4)),float(m.group(5)),float(m.group(6))
    def col(prop):
        m=re.search(r'- '+prop+r': \{r: ([-\d.e]+), g: ([-\d.e]+), b: ([-\d.e]+), a: ([-\d.e]+)\}',t)
        return tuple(float(x) for x in m.groups()) if m else None
    def fl(prop):
        m=re.search(r'- '+prop+r': ([-\d.e]+)',t); return float(m.group(1)) if m else None
    surf=fl('_Surface')
    return dict(name=name,shader=shader,tex=tex('_BaseMap') or tex('_MainTex'),color=col('_BaseColor') or col('_Color') or (1,1,1,1),
        smooth=fl('_Smoothness') if fl('_Smoothness') is not None else fl('_Glossiness'),metal=fl('_Metallic'),surface=surf,emis=col('_EmissionColor'))
MATS={}
for k,d in M.items():
    if k.startswith(B+'mat/') and k.endswith('.mat'):
        i=mat_info(W+'home/'+d+'/asset'); MATS[i['name']]=i
def load(name):
    r=fbxr.parse(W+'home/'+M[B+'meshes/%s.fbx'%name]+'/asset'); ob=r.get('Objects')
    g=ob.get('Geometry'); V=g.get('Vertices').props[0].reshape(-1,3).astype(np.float64)
    PVI=g.get('PolygonVertexIndex').props[0]
    ln=g.get('LayerElementNormal');N=ln.get('Normals').props[0].reshape(-1,3);mapn=ln.get('MappingInformationType').props[0]
    nidx=ln.get('NormalsIndex').props[0] if ln.get('NormalsIndex') else None
    lu=g.get('LayerElementUV');UV=lu.get('UV').props[0].reshape(-1,2);UVI=lu.get('UVIndex').props[0] if lu.get('UVIndex') else None
    lm=g.get('LayerElementMaterial');mm=lm.get('MappingInformationType').props[0];mats=lm.get('Materials').props[0]
    names=[k.props[1].split('\x00')[0] for k in ob.kids if k.name=='Material']
    # polygons
    polys=[];cur=[]
    for ci,x in enumerate(PVI):
        cur.append(ci)
        if x<0: polys.append(cur);cur=[]
    cv=np.where(PVI<0,~PVI,PVI)
    return dict(V=V,cv=cv,polys=polys,N=N,mapn=mapn,nidx=nidx,UV=UV,UVI=UVI,mats=mats,mapm=mm,names=names)
if __name__=='__main__':
    items=sorted(k[len(B+'meshes/'):-4] for k in M if k.startswith(B+'meshes/') and k.endswith('.fbx'))
    for n in items:
        d=load(n);V=d['V'];s=V.max(0)-V.min(0)
        print('%-22s %5.2f x %5.2f x %5.2f  v=%d mats=%s map=%s/%s'%(n,s[0],s[2],s[1],len(V),d['names'],d['mapn'],d['mapm']))
    print(len(MATS), [ (k,v['shader'][:6],v['surface']) for k,v in MATS.items() if v['surface'] not in (0.0,None)])
