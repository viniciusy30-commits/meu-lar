import sys,json,numpy as np
sys.path.insert(0,'/tmp/ml/ferramentas'); sys.argv=['x','/tmp/ml/app/src/main/assets/cute']
sys.path.insert(0,'/tmp/ml/ferramentas/sims4'); sys.path.insert(0,'/tmp/h4')
import dbpf,geom, etapa48_jovem as E, hv
from scipy.spatial import cKDTree
from PIL import Image
CU='/tmp/ml/app/src/main/assets/cute/'
def native():
    r=dbpf.read('/tmp/jb/JohnnySims_Bernard_Hair_V1_MF.package')
    gs=[e for e in r if e['t']==0x015A1849]
    return geom.parse(dbpf.data(gs[2]))
def build(grp,params=None):
    g=native(); xf=json.load(open('/tmp/s4/xf_%s.json'%grp)); k=xf['k']; off=np.array(xf['off'])
    P=g['pos'].astype(float)*k+off; N=g['nor'].astype(float)
    UV=g['uv'][0].astype(float)*[2,1]
    sv,si,fl,_=E.read_piece(CU+'p_body_%s5.bin'%grp)
    sp=sv['pos'].astype(float)
    # pesos: do pedaço de pele mais próximo (cabelo acompanha o couro cabeludo)
    t=cKDTree(sp); d,nb=t.query(P,k=6)
    W=np.zeros((len(P),55)); bi=sv['bi'].astype(int); bw=sv['bw'].astype(float)/255
    for j in range(6):
        wj=1/(d[:,j]+1.0)**2
        for c in range(4): np.add.at(W,(np.arange(len(P)),bi[nb[:,j],c]),wj*bw[nb[:,j],c])
    W/=W.sum(1,keepdims=True)
    W[:,6]+=W[:,5]+W[:,9]+W[:,13]; W[:,[5,9,13]]=0   # cabelo curto: segue cabeça/pescoço, nunca ombros/braços
    top=np.argsort(-W,axis=1)[:,:4]; tw=np.take_along_axis(W,top,1); tw/=tw.sum(1,keepdims=True)
    q=np.round(tw*255).astype(int); q[:,0]+=255-q.sum(1)
    return P,N,UV,g['idx'].astype(int),top,q,sv,si
def piece(P,N,UV,I,top,q):
    v=np.zeros(len(P),E.DT); v['pos']=P; v['nor']=N; v['uv']=UV; v['col']=255; v['bi']=top; v['bw']=q
    return v
if __name__=='__main__':
    for grp,sk in (('am','sk_s4m.png'),('af','sk_s4f.png')):
        P,N,UV,I,top,q,sv,si=build(grp)
        tx=np.asarray(Image.open(CU+'skate/bern1_am.png').convert('RGBA'))
        skin=np.asarray(Image.open(CU+sk).convert('RGBA'))
        sp=sv['pos'].astype(float); body=(sp,sv['uv'].astype(float),sv['col'][:,:3].astype(float)/255,si.astype(int),skin,0.0)
        hair=(P,UV,np.ones((len(P),3)),I,tx,0.45)
        yc=(sp[:,1].max()-9); ims=[]
        for vw in 'fsbq':
            ims.append(hv.raster([body,hair],420,vw,((0,yc),34)))
        Image.fromarray(np.hstack(ims)).save('/tmp/h4/v_%s.png'%grp)
