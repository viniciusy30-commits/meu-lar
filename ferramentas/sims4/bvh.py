import numpy as np, re
from scipy.spatial.transform import Rotation as R
def load(path):
    txt=open(path).read(); hdr,mot=txt.split('MOTION')
    names=[];par=[];chans=[];stack=[];off=[]
    toks=hdr.split()
    i=0; last=None
    while i<len(toks):
        t=toks[i]
        if t in('ROOT','JOINT'):
            names.append(toks[i+1]); par.append(stack[-1] if stack else -1); last=len(names)-1; i+=2
        elif t=='End': last=None; i+=2; 
        elif t=='{': stack.append(last); i+=1
        elif t=='}': stack.pop(); i+=1
        elif t=='OFFSET':
            if last is not None and len(off)<len(names): off.append([float(x) for x in toks[i+1:i+4]])
            i+=4
        elif t=='CHANNELS':
            n=int(toks[i+1]); 
            if last is not None: chans.append(toks[i+2:i+2+n])
            i+=2+n
        else: i+=1
    lines=mot.strip().split('\n'); ft=float(lines[1].split()[-1])
    D=np.array([[float(x) for x in l.split()] for l in lines[2:]])
    nf=len(D); nj=len(names); Wr=[None]*nj; Wp=np.zeros((nf,nj,3)); c=0
    loc=[]
    for j in range(nj):
        ch=chans[j]; v=D[:,c:c+len(ch)]; c+=len(ch)
        t=np.tile(np.array(off[j]),(nf,1)); rot_order=''; ang=[]
        for k,nm in enumerate(ch):
            if nm.endswith('position'): t[:,'XYZ'.index(nm[0])]=v[:,k]
            else: rot_order+=nm[0]; ang.append(v[:,k])
        r=R.from_euler(rot_order,np.stack(ang,1),degrees=True)
        loc.append((t,r))
    for j in range(nj):
        t,r=loc[j]; p=par[j]
        if p<0: Wr[j]=r; Wp[:,j]=t
        else: Wr[j]=Wr[p]*r; Wp[:,j]=Wp[:,p]+Wr[p].apply(t)
    return names,par,ft,Wp,Wr
