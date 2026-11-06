import sys,numpy as np
sys.path.insert(0,'/tmp/h4')
import hair4 as H, hv
from hair4 import *
OUT=CU+'skate/'
for grp in ('am','af'):
    P,N,UV,I,top,q,sv,si=H.build(grp)
    print(grp,'peso no osso 8 (cabeça):',round(float((q[top==8]).sum()/ (255*len(P))),3),'pescoço/outros:',np.unique(top[:,0],return_counts=True))
    v=H.piece(P,N,UV,I,top,q)
    E.write_piece(OUT+'bern1_%s5.cup'%grp,v,I.astype(np.uint16),0,b'')
    import shutil; shutil.copy(OUT+'bern1_am.png',OUT+'bern1_%s5.png'%grp)
    # miniatura: cabeça lisa + cabelo, fundo transparente
    sp=sv['pos'].astype(float); lim=sp[:,1].max()*0.86
    keep=[t for t in si.astype(int) if (sp[t,1]>lim).all()]
    tx=np.asarray(Image.open(OUT+'bern1_am.png').convert('RGBA'))
    skin=(sp,np.zeros((len(sp),2)),np.tile(np.array([0xE3,0xBF,0xA2])/255.,(len(sp),1)),np.array(keep),None,0.0)
    hair=(P,UV,np.ones((len(P),3)),I,tx,0.45)
    yc=sp[:,1].max()-8
    def r(bg):
        import hv as h2
        return None
    # fundo: renderiza duas vezes (cinza e verde) para achar máscara
    import hv
    S=256
    a=hv.raster([skin,hair],S,'q',((0,yc),30)); 
    bgmask=(a==205).all(2)
    rgba=np.dstack([a,np.where(bgmask,0,255).astype(np.uint8)])
    Image.fromarray(rgba).save(CU+'thumbs/bern1_%s5.png'%grp)
print('ok')
