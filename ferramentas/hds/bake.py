# Etapa 167: papéis de parede do Hds (shader de máscara de cor) assados em textura de albedo
import sys; sys.path.insert(0,'/home/claude/tools')
import export, um, numpy as np
from PIL import Image
orig=export.get_mat; BAKED={}
def bake(d,mp,r):
    f,pid=mp; o=export.obj(f,pid)
    if not o: return r
    m=um.material(f,o[0],o[1]); mk=m['tex'].get('_ColorMaskTexture')
    if not mk or not mk[1] or '_LayerRTexture' in m['tex']: return r
    ff,_=export.ref(f,mk[0],mk[1]); oo=export.obj(ff,mk[1])
    if not oo or oo[2]!=28: return r
    t=um.tex(ff,oo[0],oo[1]); w,h=t['w'],t['h']
    if t['dlen']<=0: return r
    if t['fmt']==63:
        a=np.frombuffer(t['data'][:w*h],np.uint8).reshape(h,w).astype(float)/255; mask=np.stack([a,0*a,0*a],-1)[::-1]
    else:
        g=export.get_tex(f,mk)
        if not g: return r
        mask=np.asarray(g[1].convert('RGB')).astype(float)/255
    c=m['colors']; one=np.ones(3)
    bgk='_ColorOfBackground' in c
    out=np.array(c.get('_ColorOfBackground',(1,1,1,1))[:3])[None,None,:]*np.ones_like(mask)
    for k,ch in (('_ColorOnR',0),('_ColorOnG',1),('_ColorOnB',2)):
        col=np.array(c.get(k,(1,1,1,1))[:3])[None,None,:]; mm=mask[...,ch:ch+1]
        out=out*(1-mm)+col*mm
    if not bgk: out=out*np.array(c.get('_Color',(1,1,1,1))[:3])[None,None,:]
    im=Image.fromarray((np.clip(out,0,1)*255+0.5).astype(np.uint8),'RGB')
    BAKED[m['name']]=im
    return dict(name=r['name'],col=(1.0,1.0,1.0,1.0),tex=(m['name']+'_baked',im),tp=None)
def gm(d,mp):
    r=orig(d,mp)
    if r is None: return r
    try: return bake(d,mp,r)
    except Exception as e: print('bake falhou',r['name'],e); return r
export.get_mat=gm
