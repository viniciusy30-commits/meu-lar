import sys,os; sys.path.insert(0,'/home/claude/w')
from hbuild import *
from prev import body
def show(names,slug,out,cy=150,h=70,S=360,views='fsbq'):
    b,_,_=body(); rows=[]
    tx=np.asarray(Image.open(OUT+'lotus_%s.png'%slug).convert('RGBA'))
    for n in names:
        v,i,fl,_=E.read_piece(OUT+'lotus_%s.cup'%n); P=v['pos'].astype(float); UV=v['uv'].astype(float); I=i.astype(int)
        rows.append(np.hstack([hv.raster([b,(P,UV,np.ones((len(P),3)),I,tx,0.45)],S,vw,((0,cy),h)) for vw in views]))
    Image.fromarray(np.vstack(rows)).save(out)
if __name__=='__main__':
    show(['coque','solto'],'ruivo','hchk.png')
