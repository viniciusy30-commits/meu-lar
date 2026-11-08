# Uso: python3 ferramentas/etapa116_mascaras_s4.py app/src/main/assets/cute <pasta de saída>
# Gera as máscaras de recolor do atlas de pele do Sims 4: pele/sobrancelha/lábios (RGB) e íris (cinza).
import sys, struct, numpy as np
from PIL import Image
from scipy import ndimage
cute=sys.argv[1]; out=sys.argv[2]
DT=np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)])
def tris(path):
    b=open(path,'rb').read(); nv,ni,fl=struct.unpack('<3i',b[4:16])
    v=np.frombuffer(b,DT,nv,16); idx=np.frombuffer(b,'<u2',ni,16+nv*44).reshape(-1,3); return v['uv'].astype(float),idx
def cover(uv,idx,W,H):
    m=Image.new('L',(W,H),0); from PIL import ImageDraw; d=ImageDraw.Draw(m)
    for t in idx: d.polygon([(uv[i,0]*W,uv[i,1]*H) for i in t],fill=255)
    return np.asarray(m)>0
for s,g in (('m','am5'),('f','af5')):
    A=np.asarray(Image.open(f'{cute}/sk_s4{s}.png').convert('RGB'),float); H,W=A.shape[:2]
    uv,idx=tris(f'{cute}/p_body_{g}.bin')
    cov=ndimage.binary_dilation(cover(uv,idx,W,H),iterations=6)
    lum=A@[.299,.587,.114]; r,gg,b=A[...,0],A[...,1],A[...,2]
    skin=np.clip((r-b-20)/20,0,1)*(r>=gg-2)*cov
    # sobrancelhas: escuras dentro da caixa
    brow=np.zeros((H,W)); box=(slice(694,729),slice(380,645))
    reg=lum[box]; Ls=np.median(reg); brow[box]=np.clip((Ls*0.72-reg)/(Ls*0.22),0,1)
    brow=ndimage.gaussian_filter(brow,0.6)
    # lábios: diferença para a pele ao redor (borrão) dentro de uma elipse
    blur=ndimage.gaussian_filter(A,(14,14,0)); d=np.linalg.norm(A-blur,axis=2)
    yy,xx=np.mgrid[0:H,0:W]; ell=(((xx-512)/58.)**2+((yy-862)/30.)**2)<1
    ell=ndimage.gaussian_filter(ell.astype(float),3)
    bx=(xx>=466)&(xx<=560)&(yy>=841)&(yy<=886)
    gl=np.median(gg[(yy>=895)&(yy<=905)&(xx>=470)&(xx<=555)])
    core=bx&(gg<gl*0.74)&((((xx-513)/47.)**2+((yy-862)/19.)**2)<1)
    core=ndimage.binary_closing(core,iterations=3); core=ndimage.binary_fill_holes(core)
    lips=ndimage.gaussian_filter(core.astype(float),1.2)
    # íris: azul saturado em volta do centro do olho do atlas
    cx,cy=50,563; rad=((xx-cx)**2+(yy-cy)**2)<26**2
    iris=np.clip((b-r-25)/40,0,1)*rad; iris=ndimage.gaussian_filter(iris,0.5)
    skin=skin*(1-np.maximum(brow,lips))
    M=np.stack([skin,brow,lips],2); Image.fromarray((M*255).round().astype(np.uint8)).save(f'{out}/sk_s4{s}_mask.png',optimize=True)
    Image.fromarray((iris*255).round().astype(np.uint8)).save(f'{out}/sk_s4{s}_iris.png',optimize=True)
    print(s,'skin',skin.sum()/1e3,'brow',brow.sum(),'lips',lips.sum(),'iris',iris.sum())
