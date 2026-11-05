import sys,pickle,glob; sys.path.insert(0,'/tmp/s4/anim')
from rt2 import *
exec(open('/tmp/s4/gif.py').read())
B='/tmp/bn/dataset/Bandai-Namco-Research-Motiondataset-2/data/dataset-2_run_normal_%s.bvh'
C='/tmp/cmu/data/%s.bvh'
RUN=[('A',B%'001','bandai',11,34,None),('B',B%'002','bandai',30,53,None),('C',B%'004','bandai',30,53,None),('D',B%'006','bandai',30,53,None),
     ('E',B%'008','bandai',36,59,None),('F','/tmp/lf1/run2_subject1.bvh','lafan',1175,1199,0),('G','/tmp/lf1/run1_subject5.bvh','lafan',611,632,0)]
def jt(i,j,fps): return [(0,i-0.25*fps),(0.15,i),(1.0,j),(1.6,j+0.6*fps)]
def rjt(i,j,fps): return [(0,i-0.15*fps),(0.1,i),(0.62,j),(0.92,j+0.3*fps)]
JMP=[('A','016/16_01',133,172),('B','016/16_02',231,277),('C','013/13_39',166,221),('D','013/13_40',154,209),('E','013/13_41',180,246),('F','013/13_42',185,253)]
RJ=[('A','049/49_04',161,212),('B','075/75_02',67,93),('C','075/75_03',90,121),('D','127/127_21',77,129)]
res={}
for g in ('am','af'):
    old=E.read_clips('/tmp/s4/clips_%s5.bin'%g); oc=old[1][1]
    it=[(lab,)+retarget(fn,k,g,a,b,oc,cal=c) for lab,fn,k,a,b,c in RUN]+[('H (atual)',old[3][0],old[3][1])]
    res[(g,'run')]=it; grid_gif(g,it,'/tmp/s4/correr_%s.gif'%('homem' if g=='am' else 'mulher'))
    it=[]
    for lab,f,i,j in JMP:
        tm=jt(i,j,120); it.append((lab,)+retarget(C%f,'cmu',g,int(tm[0][1]),int(tm[-1][1]),oc,loop=False,mode='jump',tmap=tm))
    it.append(('G (atual)',old[2][0],old[2][1])); res[(g,'jump')]=it
    globals()['FIX']=True
    grid_gif(g,it,'/tmp/s4/pulo_%s.gif'%('homem' if g=='am' else 'mulher'),arc=(0.15,1.0,45))
    it=[]
    for lab,f,i,j in RJ:
        tm=rjt(i,j,120); it.append((lab,)+retarget(C%f,'cmu',g,int(tm[0][1]),int(tm[-1][1]),oc,loop=False,mode='jump',tmap=tm,yaw_from='travel'))
    it.append(('E (atual)',old[4][0],old[4][1])); res[(g,'rj')]=it
    grid_gif(g,it,'/tmp/s4/pulo_correndo_%s.gif'%('homem' if g=='am' else 'mulher'),arc=(0.1,0.62,35),cols=5)
    globals()['FIX']=False
pickle.dump(res,open('/tmp/s4/anim/cand2.pkl','wb'))
