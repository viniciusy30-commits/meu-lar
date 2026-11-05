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
