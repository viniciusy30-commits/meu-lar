import struct, numpy as np
RIGS='/home/claude/geom/blender-sims3-geom-master/io_simgeom/data/rigs/'
def load(p):
    b=open(p,'rb').read(); o=8; n=struct.unpack('<I',b[o:o+4])[0]; o+=4; bones=[]
    for _ in range(n):
        v=struct.unpack('<10f',b[o:o+40]); o+=40
        ln=struct.unpack('<i',b[o:o+4])[0]; o+=4; nm=b[o:o+ln].decode('latin1'); o+=ln
        mi,pi,h,fl=struct.unpack('<iiII',b[o:o+16]); o+=16
        bones.append(dict(p=np.array(v[:3]),q=np.array(v[3:7]),s=np.array(v[7:10]),name=nm,par=pi))
    return bones
def qm(q):
    x,y,z,w=q/np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def world(bs):
    W=[None]*len(bs)
    for i,b in enumerate(bs):
        L=np.eye(4); L[:3,:3]=qm(b['q'])@np.diag(b['s']); L[:3,3]=b['p']
        W[i]=L if b['par']<0 else W[b['par']]@L
    return {b['name']:W[i][:3,3].copy() for i,b in enumerate(bs)}
def objmax(p):
    v=np.array([l.split()[1:4] for l in open(p) if l.startswith('v ')],float); return v
