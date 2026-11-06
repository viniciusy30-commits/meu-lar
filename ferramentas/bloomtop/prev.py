import sys; sys.path.insert(0,'/home/claude/w'); from common import *
def body():
    sv,si,fl,_=E.read_piece(CU+'p_body_af5.bin'); sp=sv['pos'].astype(float)
    skin=np.asarray(Image.open(CU+'sk_s4f.png').convert('RGBA'))
    return (sp,sv['uv'].astype(float),sv['col'][:,:3].astype(float)/255,si.astype(int),skin,0.0),sv,si
def topmesh(P,UV,I,tx,acut=0.45):
    return (P,UV,np.ones((len(P),3)),I,tx,acut)
def sheet(meshes,name,cy=125,h=75,S=420,views='fsbq'):
    ims=[hv.raster(meshes,S,v,((0,cy),h)) for v in views]
    Image.fromarray(np.hstack(ims)).save(name)
if __name__=='__main__':
    r,gs=load_geoms(); g=gs[0x29][1]
    P=g['pos'].astype(float)*K+OFF; UV=g['uv'][0].astype(float); I=g['idx'].astype(int)
    tx=np.asarray(tex_for(r,0x073252))
    b,sv,si=body()
    sheet([b,topmesh(P,UV,I,tx)],'v0.png')
