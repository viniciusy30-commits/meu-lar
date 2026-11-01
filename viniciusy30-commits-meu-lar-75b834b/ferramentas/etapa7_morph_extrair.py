import sys,os,pickle; sys.path.insert(0,'r/'+os.listdir('r')[0]+'/ferramentas')
from fbxr import *
import numpy as np
P=pickle.load(open('basepos.pkl','rb')).astype(np.float64)
r=parse('up/7ec03051d776f9741825b664371a802c/asset'); ob=r.get('Objects')
geos=ob.all('Geometry')
mesh=[g for g in geos if g.props[2]=='Mesh'][0]
HV=mesh.get('Vertices').props[0].reshape(-1,3).astype(np.float64)
# mapear vértice da cabeça -> vértice(s) do base.bin (posição idêntica)
from collections import defaultdict
key=lambda p:(round(p[0],3),round(p[1],3),round(p[2],3))
d=defaultdict(list)
for i,p in enumerate(P): d[key(p)].append(i)
hmap=[d.get(key(p),[]) for p in HV]
print('cabeça->base: sem par',sum(1 for m in hmap if not m),'com >1 par',sum(1 for m in hmap if len(m)>1),'de',len(HV))
shapes={}
for g in geos:
    if g.props[2]!='Shape': continue
    nm=g.props[1].split('\x00')[0]
    ix=g.get('Indexes').props[0]; dv=g.get('Vertices').props[0].reshape(-1,3)
    shapes[nm]=(ix,dv)
    mx=np.abs(dv).max() if len(dv) else 0
    print('%-38s n=%4d max|d|=%.2f'%(nm,len(ix),mx))
pickle.dump((hmap,shapes,HV),open('morph.pkl','wb'))
