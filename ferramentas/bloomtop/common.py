import sys,json,struct,numpy as np
R='/home/claude/p/codigo/'
CU=R+'app/src/main/assets/cute/'
sys.argv=['x',CU]
sys.path.insert(0,R+'ferramentas'); import etapa48_jovem as E
sys.path.insert(0,R+'ferramentas/sims4'); sys.modules.pop('dbpf',None); sys.modules.pop('geom',None)
import dbpf,geom,hv
import rle2
from PIL import Image
K=96.93378170724961; OFF=np.array([0.0,0.785003982,0.360869205])
PK='/home/claude/w/Aurum_BloomTop_3Female.package'
def load_geoms():
    r=dbpf.read(PK); out={}
    for e in r:
        if e['t']==0x015A1849:
            g=geom.parse(dbpf.data(e)); out[e['g']&0xff]=(e,g)
    return r,out
def tex_for(r,key):
    for e in r:
        if e['t']==0x3453CF95 and (e['inst']&0xffffff)==key: return rle2.rle2_mip0(dbpf.data(e))
