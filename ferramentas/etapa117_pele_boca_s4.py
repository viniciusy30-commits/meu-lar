# Etapa 117: alisa a pele em volta da boca e do queixo no atlas do Sims 4 (manchas claras, aureola dos labios, vinco escuro sob o labio).
# Uso: python3 etapa117_pele_boca_s4.py <pasta cute de entrada> <pasta de saida>
import sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
cute=sys.argv[1]; out=sys.argv[2]
def ngauss(A,w,s):
    num=np.stack([nd.gaussian_filter(A[...,c]*w,s) for c in range(3)],2); den=nd.gaussian_filter(w,s)[...,None]
    return num/np.maximum(den,1e-6)
for sx in 'mf':
    A=np.asarray(Image.open(f'{cute}/sk_s4{sx}.png').convert('RGB'),float); H,W=A.shape[:2]
    yy,xx=np.mgrid[0:H,0:W].astype(float); g=A[...,1]
    box=(xx>=440)&(xx<=590)&(yy>=830)&(yy<=905)
    gl=np.median(g[(yy>=895)&(yy<=905)&(xx>=470)&(xx<=555)])
    core=(g<gl*0.74)&(((xx-513)/47.)**2+((yy-862)/19.)**2<1)&box
    core=nd.binary_closing(core,iterations=3); core=nd.binary_fill_holes(core)
    # regiao de trabalho: elipse grande em volta da boca ate o queixo, com borda suave
    reg=(((xx-513)/92.)**2+((yy-885)/62.)**2)
    f=np.clip((1.0-reg)/0.35,0,1); f=nd.gaussian_filter(f,3)
    # pele de referencia: tudo da regiao exceto labios (dilatados), narinas/nariz (acima de y=832) e a faixa do queixo muito clara nao e excluida
    excl=nd.binary_dilation(core,iterations=11)|(yy<836)
    wskin=(~excl).astype(float)*(((xx-513)/110.)**2+((yy-885)/80.)**2<1)
    S=ngauss(A,wskin,16)           # pele lisa estimada
    S2=ngauss(S,np.ones_like(wskin),4)
    # aureola em volta dos labios: troca totalmente pela pele lisa (borda suave)
    d=nd.distance_transform_edt(~core)
    ring=np.clip(1-(d-0.5)/12.0,0,1)*(~core)
    ring=nd.gaussian_filter(ring,1.5)
    # fora da aureola: mistura 85% em direcao a pele lisa (tira manchas claras/escuras), mantem 15% do detalhe
    k=np.clip(f*0.85,0,1)
    B=A*(1-k[...,None])+S2*k[...,None]
    B=B*(1-ring[...,None])+S2*ring[...,None]
    # labios intactos
    core_s=nd.gaussian_filter(core.astype(float),0.8)
    B=B*(1-core_s[...,None])+A*core_s[...,None]
    Image.fromarray(np.clip(B,0,255).astype(np.uint8)).save(f'{out}/sk_s4{sx}.png',optimize=True)
    print(sx,'ok')
