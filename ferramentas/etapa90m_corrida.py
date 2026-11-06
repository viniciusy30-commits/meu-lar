import sys,pickle; sys.argv=['x','/tmp/ml/app/src/main/assets/cute']; sys.path.insert(0,'/tmp/s4/anim')
from rt2 import *; import sneak
exec(open('/tmp/s4/gif.py').read())
B='/tmp/bn/dataset/Bandai-Namco-Research-Motiondataset-2/data/dataset-2_%s.bvh'
CAL=(B%'walk_normal_001',0)   # quadro em pé, braços soltos: calibração sem torcer cotovelo
TR=list(range(1,17))+list(range(25,55))
def fixlat(clip,J):
    fr=[sneak.unpack(clip[f],J) for f in range(len(clip))]
    u=np.mean([(P[8]-P[0])/np.linalg.norm(P[8]-P[0]) for _,P,_ in fr],0); C=R.from_euler('z',np.arctan2(u[0],u[1]))
    out=[]
    for Rb,P,s in fr:
        Rb=list(Rb)
        for b in TR: Rb[b]=C*Rb[b]
        Q=P.copy()
        for b in range(1,55):
            if b in TR or GP[b] in TR: Q[b]=Q[GP[b]]+Rb[GP[b]].apply(J[b]-J[GP[b]])
        out.append(sneak.pack(Rb,Q,J,s))
    return np.array(out,np.float32)
res={}
for g,(fn,a,b) in (('am',('run_normal_001',11,34)),('af',('run_normal_004',30,53))):
    cur=E.read_clips('/tmp/ml/app/src/main/assets/cute/clips_%s5.bin'%g); J=j55(g)
    L,M=retarget(B%fn,'bandai',g,a,b,cur[1][1],cal=CAL); M=fixlat(M,J)
    res[g]=(L,M)
    for yaw,tag in ((0,'frente'),(40,'lado')):
        grid_gif(g,[('antes',cur[3][0],cur[3][1]),('depois',L,M)],'/tmp/s4/corrida_%s_%s.gif'%('homem' if g=='am' else 'mulher',tag),yaw=yaw,cols=2)
pickle.dump(res,open('/tmp/s4/anim/runfix.pkl','wb'))
