exec(open('insp2.py').read().split("for i,e in enumerate")[0])
import sys
sys.argv=['x','/home/claude/proj/codigo/app/src/main/assets/cute/']
import etapa48_jovem as E, hv
from PIL import Image
CU='/home/claude/proj/codigo/app/src/main/assets/cute/'
K=96.93378170724961; OFF=np.array([0.0,0.785003982,0.360869205])
# texturas
for k in (0xeb1d91,0xe26bed):
    im=rle2.rle2_mip0(dbpf.data(T[k])); print(hex(k),im.size); im.convert('RGBA').resize((512,512)).save('tex_%x.png'%k)
for e in r:
    if e['t']==0xB2D882: d=dbpf.data(e); open('dds_b2.dds','wb').write(d); print('dds',len(d))
# malhas
G={}
for e in r:
    if e['t']==0x015A1849:
        G.setdefault(e['g']&0xff,[]).append(geom.parse(dbpf.data(e)))
print({hex(k):[len(g['pos']) for g in v] for k,v in G.items()})

def body():
    sv,si,fl,_=E.read_piece(CU+'p_body_af5.bin'); sp=sv['pos'].astype(float)
    skin=np.asarray(Image.open(CU+'sk_s4f.png').convert('RGBA'))
    return (sp,sv['uv'].astype(float),sv['col'][:,:3].astype(float)/255,si.astype(int),skin,0.0),sv,si
g=G[0x52][0]
P=g['pos'].astype(float)*K+OFF; UV=g['uv'][0].astype(float); I=g['idx'].astype(int)
print('P',P.min(0).round(1),P.max(0).round(1),'UV',UV.min(0),UV.max(0))
tx=np.asarray(rle2.rle2_mip0(dbpf.data(T[0xeb1d91])))
UVp=UV.copy(); 
b,sv,si=body()
print('body',b[0].min(0).round(1),b[0].max(0).round(1))
ims=[hv.raster([b,(P,UV,np.ones((len(P),3)),I,tx,0.45)],420,vw,((0,125),75)) for vw in 'fsbq']
Image.fromarray(np.hstack(ims)).save('v_all.png')
