import sys; sys.path.insert(0,'/home/claude/w')
from prev import *
v,i,fl,_=E.read_piece('out/bloom_af5.cup'); P=v['pos'].astype(float); UV=v['uv'].astype(float); I=i.astype(int)
b,sv,si=body()
rows=[]
for nm in ('branco','rosa'):
    tx=np.asarray(Image.open('out/bloom_%s_af5.png'%nm).convert('RGBA'))
    ims=[hv.raster([b,topmesh(P,UV,I,tx)],420,vw,((0,125),75)) for vw in 'fsbq']
    rows.append(np.hstack(ims))
Image.fromarray(np.vstack(rows)).save('check.png')
