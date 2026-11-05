import struct, numpy as np
def parse(b):
    ma,mi,n=struct.unpack_from('<3I',b,0); p=12; out=[]
    for _ in range(n):
        pos=struct.unpack_from('<3f',b,p); p+=12; q=struct.unpack_from('<4f',b,p); p+=16; sc=struct.unpack_from('<3f',b,p); p+=12
        ln,=struct.unpack_from('<I',b,p); p+=4; name=b[p:p+ln].decode('latin1'); p+=ln
        opp,par,h,fl=struct.unpack_from('<iiII',b,p); p+=16
        out.append(dict(pos=np.array(pos),q=np.array(q),sc=np.array(sc),name=name,opp=opp,par=par,hash=h,flags=fl))
    return (ma,mi),out
from scipy.spatial.transform import Rotation as R
def world(bs):
    W=[None]*len(bs)
    for i,b in enumerate(bs):
        r=R.from_quat(b['q']); t=b['pos']
        if b['par']<0: W[i]=(r,t)
        else:
            pr,pt=W[b['par']]; W[i]=(pr*r, pt+pr.apply(t))
    return W
