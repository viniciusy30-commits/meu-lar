exec(open('view1.py').read().split("def body")[0].replace("print(","(lambda *a,**k:None)("))
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
g=G[0x52][0]
P=g['pos'].astype(float)*K+OFF; UV=g['uv'][0].astype(float); I=g['idx'].astype(int)
n=len(P)
A=coo_matrix((np.ones(len(I)*3),(np.r_[I[:,0],I[:,1],I[:,2]],np.r_[I[:,1],I[:,2],I[:,0]])),shape=(n,n))
nc,lab=connected_components(A,directed=False)
print('componentes',nc)
for c in range(nc):
    m=lab==c; t=m[I[:,0]]
    print(c,'v',m.sum(),'tri',t.sum(),'y',P[m,1].min().round(1),P[m,1].max().round(1),'x',P[m,0].min().round(1),P[m,0].max().round(1),'z',P[m,2].min().round(1),P[m,2].max().round(1),'uv',UV[m].min(0).round(2),UV[m].max(0).round(2))
np.save('lab.npy',lab)
# bones
import struct
sys_path=None
E2=None
e=[e for e in r if e['t']==0x015A1849 and (e['g']&0xff)==0x52][0]
raw=dbpf.data(e)
b=raw; i=b.find(b'GEOM'); v,tgo=struct.unpack_from('<2I',b,i+4); end=i+12+tgo
for nb in range(1,300):
    p=end-4*nb-4
    if struct.unpack_from('<I',b,p)[0]==nb: print('bones',nb,[hex(x) for x in struct.unpack_from('<%dI'%nb,b,p+4)][:80]); break
