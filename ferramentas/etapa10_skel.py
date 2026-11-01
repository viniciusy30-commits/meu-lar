import numpy as np,pickle,struct
K=0.0082
G,GP,BI=pickle.load(open('/home/claude/p/game_skel.pkl','rb'))
NB=55
Bc={i:BI[i].T.copy() for i in range(NB)}          # bind (coluna), 4x4: [R|p]
Rb={i:Bc[i][:3,:3].copy() for i in range(NB)}
Pb={i:Bc[i][:3,3].copy() for i in range(NB)}
Tl={i:(Rb[GP[i]].T@(Pb[i]-Pb[GP[i]]) if GP[i]>=0 else Pb[i].copy()) for i in range(NB)}   # translação local no quadro do pai
ORDER=[]
def _top():
    seen=set()
    def v(i):
        if i in seen: return
        if GP[i]>=0: v(GP[i])
        seen.add(i); ORDER.append(i)
    for i in range(NB): v(i)
_top()
def fk(Rw,root_pos):
    """Rw: dict osso->rotação mundo (3x3). Retorna dict osso->(R,pos)"""
    W={}
    for i in ORDER:
        p=GP[i]
        if p<0: pos=root_pos
        else: pos=W[p][1]+W[p][0]@Tl[i]
        W[i]=(Rw[i],pos)
    return W
def skin(W):
    out=np.zeros((NB,12),np.float32)
    for i in range(NB):
        R,p=W[i]
        M=np.eye(4); M[:3,:3]=R; M[:3,3]=p
        S=K*(M@np.linalg.inv(Bc[i]))
        out[i]=S[:3,:].reshape(12)
    return out
def abs_rot_from_skin(S):
    """S (55,12) -> Rw dict, pos dict (mundo rígido, cm): W = S/K @ Bc"""
    W={}
    for i in range(NB):
        M=np.eye(4); M[:3,:]=S[i].reshape(3,4)/K; M[3,3]=1
        Wm=M@Bc[i]; W[i]=(Wm[:3,:3],Wm[:3,3])
    return W
def Rx(a):
    c,s=np.cos(a),np.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def Ry(a):
    c,s=np.cos(a),np.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def Rz(a):
    c,s=np.cos(a),np.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])
def arc(a,b):
    a=a/np.linalg.norm(a); b=b/np.linalg.norm(b)
    v=np.cross(a,b); c=float(a@b)
    if c<-0.9999:
        ax=np.cross(a,[1,0,0]); 
        if np.linalg.norm(ax)<1e-3: ax=np.cross(a,[0,0,1])
        ax/=np.linalg.norm(ax); return 2*np.outer(ax,ax)-np.eye(3)
    vx=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return np.eye(3)+vx+vx@vx/(1+c)
