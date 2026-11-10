import struct,json,sys,math,numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
def load(path):
    b=open(path,'rb').read(); jl=struct.unpack_from('<I',b,12)[0]; g=json.loads(b[20:20+jl]); bin0=20+jl+8
    return g,b,bin0
def acc(g,b,bin0,i,dt,n):
    a=g['accessors'][i]; v=g['bufferViews'][a['bufferView']]; o=bin0+v['byteOffset']
    return np.frombuffer(b,dtype=dt,count=a['count']*n,offset=o).reshape(a['count'],n)
def rotm(axis,deg):
    a=math.radians(deg); c,s=math.cos(a),math.sin(a); M=np.eye(4)
    if axis=='x': M[1,1]=c;M[1,2]=-s;M[2,1]=s;M[2,2]=c
    if axis=='y': M[0,0]=c;M[0,2]=s;M[2,0]=-s;M[2,2]=c
    return M
def trans(t): M=np.eye(4); M[:3,3]=t; return M
def render(path,out,doors,steer,roll,az,el):
    g,b,bin0=load(path); nodes=g['nodes']; par={}
    for i,n in enumerate(nodes):
        for c in n.get('children',[]): par[c]=i
    W={}
    def world(i):
        if i in W: return W[i]
        n=nodes[i]; M=trans(n.get('translation',[0,0,0]))
        nm=n['name']
        if nm.startswith('porta_'): M=M@rotm('y',doors.get(nm,0))
        if nm.startswith('dir_'): M=M@rotm('y',steer)
        if nm.startswith('roda_'): M=M@rotm('x',roll)
        if i in par: M=world(par[i])@M
        W[i]=M; return M
    polys=[];cols=[]
    mc=[(.95,.95,.95),(.25,.25,.25),(.1,.2,.3),(.8,.8,.85),(.6,.6,.6),(.2,.2,.3),(.2,.2,.25),(.15,.15,.15),(.3,.5,.9)]
    for i,n in enumerate(nodes):
        if 'mesh' not in n: continue
        M=world(i)
        for p in g['meshes'][n['mesh']]['primitives']:
            pos=acc(g,b,bin0,p['attributes']['POSITION'],'<f4',3); idx=acc(g,b,bin0,p['indices'],'<u2',1).ravel().reshape(-1,3)
            wp=(M[:3,:3]@pos.T).T+M[:3,3]
            for t in idx: polys.append(wp[t]); cols.append(mc[p['material']])
    polys=np.array(polys); 
    a=math.radians(az); e=math.radians(el)
    # camera
    fwd=np.array([math.cos(e)*math.sin(a),math.sin(e),math.cos(e)*math.cos(a)])
    up=np.array([0,1,0]); r=np.cross(up,fwd); r/=np.linalg.norm(r); u=np.cross(fwd,r)
    xs=polys@r; ys=polys@u; zs=polys@fwd
    order=np.argsort(zs.mean(1))
    n_=np.cross(polys[:,1]-polys[:,0],polys[:,2]-polys[:,0]); n_/=np.linalg.norm(n_,axis=1,keepdims=True)+1e-9
    L=np.array([0.4,0.8,0.5]); L/=np.linalg.norm(L); sh=0.45+0.55*np.abs(n_@L)
    pc=PolyCollection([np.stack([xs[i],ys[i]],1) for i in order],facecolors=[tuple(np.array(cols[i])*sh[i]) for i in order],edgecolors='none')
    fig,ax=plt.subplots(figsize=(9,6)); ax.add_collection(pc); ax.set_xlim(xs.min()-.1,xs.max()+.1); ax.set_ylim(ys.min()-.1,ys.max()+.1); ax.set_aspect('equal'); ax.axis('off'); fig.patch.set_facecolor('#d8e4ee')
    fig.savefig(out,dpi=70,bbox_inches='tight')
if __name__=='__main__':
    path=sys.argv[1]
    d={'porta_FE':-65,'porta_TE':-62,'porta_FD':0,'porta_TD':0}
    render(path,'p1.png',d,-30,35,40,22)    # frente-esquerda (lado +x) com portas abertas e roda esterçada
    render(path,'p2.png',{},0,0,150,18)     # trás-direita fechado
    render(path,'p3.png',{'porta_FE':-65,'porta_TE':-62,'porta_FD':65,'porta_TD':62},0,0,0,70)  # vista de cima, 4 portas abertas
