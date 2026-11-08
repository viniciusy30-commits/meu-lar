# Limpa a boca do atlas do Sims 4: tira o contorno claro em volta dos lábios e a emenda vertical do lábio de cima.
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
    core=nd.binary_closing(core,iterations=3); core=nd.binary_fill_holes(core); core=nd.gaussian_filter(core.astype(float),2.0)>0.45
    # emenda vertical do lábio de cima: corrige o brilho da metade esquerda para casar com a direita
    line=int(round(np.median(np.where(core)[0][A[core][:,1]<np.percentile(A[core][:,1],10)]))) if core.any() else 860
    L=A.copy()
    up=core&(yy<line-1)
    lum=A@[.299,.587,.114]
    lft=up&(xx>=498)&(xx<=511); rgt=up&(xx>=514)&(xx<=527)
    if lft.any() and rgt.any():
        r=float(np.clip(lum[rgt].mean()/lum[lft].mean(),0.94,1.06))
        ramp=np.clip((xx-470)/(511-470),0,1)       # correção só perto do centro, some para fora
        fac=1+(r-1)*np.where(xx<=512,np.clip((xx-478)/(511-478),0,1),np.clip((548-xx)/(548-514),0,1))
        L=np.where(up[...,None],A*fac[...,None],A)
        L=nd.gaussian_filter(L,(0,0.7,0))*0+L
        # suaviza um pouco só em volta do centro
        Ls=np.stack([nd.gaussian_filter(L[...,c],1.3) for c in range(3)],2)
        wcen=nd.gaussian_filter((up&(np.abs(xx-513)<10)).astype(float),2)
        L=L*(1-wcen[...,None])+Ls*wcen[...,None]
    # contorno claro: dentro do anel, mistura para a pele suave
    keep=box&~nd.binary_dilation(core,iterations=9)
    skin=ngauss(L,keep.astype(float),7)
    ring=nd.binary_dilation(core,iterations=8)&~core
    d=nd.distance_transform_edt(~core)
    wr=nd.gaussian_filter(np.clip(1-(d-1.0)/8,0,1)*ring,2.0)
    B=L*(1-wr[...,None])+skin*wr[...,None]
    Image.fromarray(np.clip(B,0,255).astype(np.uint8)).save(f'{out}/sk_s4{sx}.png',optimize=True)
    print(sx,'linha',line,'ratio',round(float(r),3) if lft.any() else None)
