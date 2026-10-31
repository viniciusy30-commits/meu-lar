#!/usr/bin/env python3
"""
Etapa 2 do Meu Lar: gera os dados de recoloração do atlas cute/textures.png (2048x1024).
Saídas (em <assets>/cute/):
  recolor.png   : RGB. R = w0, G = w1 (pesos dos 2 slots da região, 0..255 = 0..1), B = id da região (0 = sem região)
  recolor_s.png : RGB (tudo igual). Sombra S do pixel (0..2 em 0..255) = luminância assada / luminância da cor de referência
  recolor.txt : uma linha por região:  id|nome|slot0|slot1|r0 g0 b0|r1 g1 b1   (cores de referência sRGB 0..255 = como a Mary está assada)
Modelo (em sRGB, por pixel e canal c; D_k = cor_k - ref_k):
  saida = (base + S*(w0*max(D_0,0) + w1*max(D_1,0))) * (1 + w0*min(D_0/ref_0,0) + w1*min(D_1/ref_1,0))
Escurecer multiplica (mantém o detalhe), clarear soma. Com as cores de referência a saída é IGUAL ao textures.png (identidade exata).
Uso: python3 etapa2_masks.py <pasta com t_*.png (máscaras do pack)> <textures.png> <pasta_saida>
"""
import sys, os, numpy as np
from PIL import Image

def lum(c): return 0.2126*c[...,0]+0.7152*c[...,1]+0.0722*c[...,2]
def sstep(x,a,b):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)

# id, nome, x,y,tamanho, máscara(arquivo), slot0, slot1
REG=[(1,'corpo',0,0,1024,'cbced9',0,-1),
     (2,'blusa',1024,0,512,'5e7eb7',4,5),
     (3,'saia',1536,0,512,'00b80f',6,-1),
     (4,'cabeloTras',1024,512,512,'ad56d3',2,3),
     (5,'cabeloFrente',1536,512,256,'964d11',2,3),
     (6,'olhos',1792,512,256,None,1,-1),
     (7,'sandalia',1536,768,128,'7db498',7,8)]

def main(maskdir, tex, out):
    base=np.asarray(Image.open(tex).convert('RGB')).astype(np.float64)/255
    H,W,_=base.shape
    a0=np.zeros((H,W)); a1=np.zeros((H,W)); sh=np.zeros((H,W)); rid=np.zeros((H,W),np.uint8)
    lines=[]
    for (i,name,x,y,s,mk,s0,s1) in REG:
        B=base[y:y+s,x:x+s]
        if name=='olhos':
            mx=B.max(-1); mn=B.min(-1)
            sat=(mx-mn)/np.maximum(mx,1e-3)
            w0=sstep(sat,0.55,0.8)*sstep(mx,0.10,0.25)*((B[...,0]>B[...,1])&(B[...,1]>=B[...,2]-0.02))
            w1=np.zeros_like(w0)
        elif name.startswith('cabelo'):
            # pontas rosa assadas no cabelo: detectadas pela cor assada (r-g alto e azul > verde)
            tip=sstep(B[...,0]-B[...,1],0.55,0.72)*(B[...,2]>B[...,1]*1.3)
            w1=tip; w0=1-tip
        else:
            m=Image.open(os.path.join(maskdir,'t_%s.png'%mk)).convert('RGB')
            m=np.asarray(m.resize((s,s),Image.LANCZOS)).astype(np.float64)/255
            if name=='corpo':
                w0=1-sstep(m[...,2],0.10,0.45); w1=np.zeros_like(w0)
            else:
                R,G=m[...,0],m[...,1]; t=R+G
                w1=np.where(t>0.03,G/np.maximum(t,1e-6),0.0) if s1>=0 else np.zeros_like(R)
                w0=1-w1
                # pixels sem nenhuma máscara (fora das ilhas UV) ficam sem efeito
                cov=sstep(t,0.02,0.10); w0*=cov; w1*=cov
        ws=[w0,w1]
        refs=[]
        for k,w in enumerate(ws):
            if k==1 and s1<0: refs.append(np.zeros(3)); continue
            sel=w>0.8
            if sel.sum()<20: sel=w>0.3
            refs.append(B[sel].mean(0) if sel.sum()>0 else np.array([.5,.5,.5]))
        refmix=(w0[...,None]*refs[0]+w1[...,None]*refs[1])
        L=lum(B); Lr=np.maximum(lum(refmix),1e-3)
        S=np.clip(L/Lr,0,1.9)
        tot=w0+w1
        # onde a referência é escura demais a sombra não é confiável: efeito nulo
        S=np.where(lum(refmix)>0.04,S,0.0)
        S=np.where(tot>0.02,S,0.0)
        sl=(slice(y,y+s),slice(x,x+s))
        a0[sl]=np.clip(w0,0,1); a1[sl]=np.clip(w1,0,1); sh[sl]=np.clip(S,0,2); rid[sl]=np.where(tot>0.02,i,0)
        lines.append('%d|%s|%d|%d|%s|%s'%(i,name,s0,s1,' '.join('%.1f'%(255*v) for v in refs[0]),' '.join('%.1f'%(255*v) for v in refs[1])))
        print(name,'ref0',np.round(refs[0]*255),'ref1',np.round(refs[1]*255),'cobertura',round(float((tot>0.02).mean()),2))
    img=np.zeros((H,W,3),np.uint8)
    img[...,0]=np.round(a0*255); img[...,1]=np.round(a1*255); img[...,2]=rid
    Image.fromarray(img,'RGB').save(os.path.join(out,'recolor.png'),optimize=True)
    g=np.round(sh/2*255).astype(np.uint8)
    Image.fromarray(np.stack([g,g,g],-1),'RGB').save(os.path.join(out,'recolor_s.png'),optimize=True)
    open(os.path.join(out,'recolor.txt'),'w').write('# id|nome|slot0|slot1|ref0 (sRGB 0..255)|ref1\n'+'\n'.join(lines)+'\n')

if __name__=='__main__': main(*sys.argv[1:4])
