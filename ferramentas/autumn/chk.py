import sys; sys.path.insert(0,'/home/claude/w')
from prev import *
v,i,fl,_=E.read_piece('out/autumn_af5.cup'); P=v['pos'].astype(float); UV=v['uv'].astype(float); I=i.astype(int)
print('cup',len(P),len(I),'y',P[:,1].min().round(1),P[:,1].max().round(1))
b,sv,si=body()
rows=[]
for nm in ('mostarda','preto'):
    tx=np.asarray(Image.open('out/autumn_%s.png'%nm).convert('RGBA'))
    ims=[hv.raster([b,topmesh(P,UV,I,tx,0.0)],420,vw,((0,95),75)) for vw in 'fsbq']
    rows.append(np.hstack(ims))
Image.fromarray(np.vstack(rows)).save('/home/claude/sk/chk1.png')
