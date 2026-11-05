import numpy as np,dbpf,geom
from scipy.spatial import cKDTree
S='/tmp/s4p/softe/[akalukery] softe collection - default replacement '
def rdobj(f):
    V=[];T=[]
    for l in open(f):
        if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('vt '): T.append([float(x) for x in l.split()[1:3]])
    return np.array(V),np.array(T)
def geoms(name):
    out=[]
    for e in dbpf.read(S+name+'.package'):
        if e['t']==0x015A1849:
            g=geom.parse(dbpf.data(e)); out.append(g)
    # only LOD0: largest per distinct y-range -> take groups by max verts; keep all with distinct pos sets
    return out
def train(names):
    P=[];U0=[];U1=[]
    for n in names:
        for g in geoms(n):
            P.append(g['pos']);U0.append(g['uv'][0]);U1.append(g['uv'][1])
    return np.vstack(P),np.vstack(U0),np.vstack(U1)

import struct
def _fnv(s):
    h=0x811C9DC5
    for c in s.lower().encode(): h=(h*0x01000193)&0xffffffff; h^=c
    return h
S4NAMES=['b__ROOT__','b__ROOT_bind__','b__Pelvis__','b__Spine0__','b__Spine1__','b__Spine2__','b__Neck__','b__Head__','b__CAS_L_Breast__','b__CAS_R_Breast__']
for _s in 'LR':
    S4NAMES+=['b__%s_%s__'%(_s,x) for x in ['Clavicle','UpperArm','ShoulderTwist','Elbow','ForeArmTwist','Forearm','Hand','Thigh','ThighTwist','Calf','Foot','Toe',
        'Index0','Index1','Index2','Mid0','Mid1','Mid2','Ring0','Ring1','Ring2','Pinky0','Pinky1','Pinky2','Thumb0','Thumb1','Thumb2']]
HN={_fnv(n):n for n in S4NAMES}
def geom_bones(b):
    i=b.find(b'GEOM'); v,tgo=struct.unpack_from('<2I',b,i+4); end=i+12+tgo
    for nb in range(1,300):
        p=end-4*nb-4
        if struct.unpack_from('<I',b,p)[0]==nb: return [HN.get(h,'?%08X'%h) for h in struct.unpack_from('<%dI'%nb,b,p+4)]
def train_w(names):
    """por vértice das roupas de baixo: 4 nomes de osso do TS4 + 4 pesos (0..1)"""
    BN=[];BW=[]
    for n in names:
        for e in dbpf.read(S+n+'.package'):
            if e['t']!=0x015A1849: continue
            b=dbpf.data(e); g=geom.parse(b); bl=geom_bones(b)
            bi=g['bi'].astype(int); bw=g['bw'].astype(float)/255
            BN.append(np.array([[bl[x] if x<len(bl) else '?' for x in r] for r in bi])); BW.append(bw)
    return np.vstack(BN),np.vstack(BW)
