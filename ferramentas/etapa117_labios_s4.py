# Etapa 117b: repinta os labios do atlas do Sims 4 (limpos, sem manchas, borda suave, linha central fina e natural).
# Uso: python3 etapa117_labios_s4.py <pasta com sk_s4m/f.png ja alisados> <saida>
import sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
cin,cout=sys.argv[1],sys.argv[2]
def ng(A,w,s):
    num=np.stack([nd.gaussian_filter(A[...,c]*w,s) for c in range(3)],2); den=nd.gaussian_filter(w,s)[...,None]
    return num/np.maximum(den,1e-6)
for sx in 'mf':
    A=np.asarray(Image.open(f'{cin}/sk_s4{sx}.png').convert('RGB'),float); H,W=A.shape[:2]
    yy,xx=np.mgrid[0:H,0:W].astype(float); g=A[...,1]
    box=(xx>=440)&(xx<=590)&(yy>=830)&(yy<=905)
    gl=np.median(g[(yy>=895)&(yy<=905)&(xx>=470)&(xx<=555)])
    core=(g<gl*0.74)&(((xx-513)/47.)**2+((yy-862)/19.)**2<1)&box
    core=nd.binary_closing(core,iterations=3); core=nd.binary_fill_holes(core)
    core=nd.binary_opening(core,iterations=1)
    ys,xs=np.where(core)
    gg=g.copy(); gg[~core]=1e9
    # linha de separacao: linha mais escura da regiao central de cada coluna
    line=np.median(ys[g[core]<=np.percentile(g[core],12)])
    cx=xs.mean(); hw=(xs.max()-xs.min())/2
    # forma limpa: mascara suavizada
    dx=(xx-cx)/(hw*1.1); t=np.clip(1-dx**2,0,1)
    top=line-11.5*t**0.62+2.2*np.exp(-((xx-cx)/5.5)**2)-1.2*np.exp(-((np.abs(xx-cx)-11)/4.5)**2)
    bot=line+27.0*t**0.7
    d_in=np.minimum(yy-top,bot-yy)                 # distancia (px) para dentro da forma
    alpha=np.clip(d_in/2.0+0.5,0,1)*(np.abs(dx)<1.0)
    alpha=nd.gaussian_filter(alpha,0.7)
    up=(yy<line)&(alpha>0); lo=(yy>=line)&(alpha>0)
    cu=ng(A,((core)&(yy<line-2)).astype(float),6)
    cl=ng(A,((core)&(yy>line+2)).astype(float),6)
    # cor media, com gradiente suave vertical
    mu=np.median(A[core&(yy<line-2)],axis=0); ml=np.median(A[core&(yy>line+2)],axis=0)
    ty=np.clip((yy-(line-12))/12,0,1)
    base=np.where((yy<line)[...,None],mu*0.55+cu*0.45,ml*0.55+cl*0.45)
    base=nd.gaussian_filter(base,(2.0,2.0,0))
    # sombra do labio de cima e brilho do de baixo
    ex=np.exp(-((xx-cx)/(hw*0.55))**2)
    lowc=(yy-line)
    top_sh=np.exp(-((yy-(line-6))/6.0)**2)*0.10
    hi=np.exp(-((lowc-8)/5.0)**2)*ex*0.10
    L=base*(1-top_sh[...,None]*(yy<line)[...,None])*(1+hi[...,None]*(yy>=line)[...,None])
    # linha central fina, mais forte no meio e sumindo nos cantos
    fade=np.clip(1-np.abs(xx-cx)/(hw*1.0),0,1)**0.6
    ln=np.exp(-((yy-line)/1.1)**2)*fade
    L=L*(1-0.38*ln[...,None])
    # cantos da boca um pouco mais escuros e suaves
    cor=np.exp(-((np.abs(xx-cx)-hw*0.92)/(hw*0.12))**2)*np.exp(-((yy-line)/3.0)**2)*0.12
    L=L*(1-cor[...,None])
    # aplica: fora dos labios pele lisa ja existente; transicao pelo alpha
    reg=alpha>0
    B=A*(1-alpha[...,None])+L*alpha[...,None]
    # remove restos escuros (contorno antigo) logo fora do labio: mistura para pele lisa
    ring=nd.binary_dilation(alpha>0.02,iterations=5)&(alpha<0.9)
    skin=ng(A,((~nd.binary_dilation(core,iterations=9))&box).astype(float),7)
    rw=nd.gaussian_filter(ring.astype(float)*(1-alpha),1.5)
    B=B*(1-rw[...,None])+skin*rw[...,None]*(1-alpha[...,None])+B*rw[...,None]*alpha[...,None]
    Image.fromarray(np.clip(B,0,255).astype(np.uint8)).save(f'{cout}/sk_s4{sx}.png',optimize=True)
    print(sx,'linha',line,'cx',cx,'hw',hw)
