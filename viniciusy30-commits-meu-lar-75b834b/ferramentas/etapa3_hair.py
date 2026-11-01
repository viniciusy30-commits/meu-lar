#!/usr/bin/env python3
"""
Etapa 3 do Meu Lar: converte os 23 cabelos restantes do pack BoZo (13 traseiros + 8... ver HAIRS) em peças CUP1 + atlas de cabelo.
Uso: python3 etapa3_hair.py <pasta com 'up' (unitypackage extraído)> <assets/cute>
Saídas: p_hairback_<id>.bin, p_hairfront_<id>.bin, hair.png (1024x1024), hair_recolor.png, hair_recolor_s.png, hair_recolor.txt, hair_pieces.txt
Regras: o cabelo é preso ao osso da cabeça (8); a parte que desce abaixo do pescoço passa a seguir o peito (osso 4) para não atravessar o corpo.
Posição = vértice do FBX + deslocamento da cabeça (0; 157.3375; -0.4809), igual às peças da Etapa 1 (verificado).
"""
import sys, os, re, struct, collections
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fbxmesh import load_mesh

HEAD = np.array([0.0, 157.3375, -0.4809])
BACK = ['Buzzed','DreadBack','LongDreads','LongStreight','PonyTailLong','PonyTailShort','Punk','Scrappy','Short','ShortBob','TwinTailLong','TwinTailShort','Wild','WildTail']   # Flare já existe
FRONT = ['BangSideFlicks','Fohawk','HangingDreads','Hime','Messy','QuicklyHair','SweaptBack','SweaptDreads','WolfCut']                                                          # LongSweeps já existe
T = 192; COLS = 5; ATL = 1024
C0 = np.array([112, 76, 50], float); C1 = np.array([160, 116, 74], float)   # cor padrão (castanho) e cor das pontas

def sstep(x,a,b):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)

def index(upk):
    d={}
    for g in os.listdir(upk):
        pf=os.path.join(upk,g,'pathname')
        if os.path.exists(pf): d[open(pf).read().split('\n')[0].strip()]=os.path.join(upk,g,'asset')
    return d

def find(idx, slot, pid):
    suffix = {'HairBack':'BSMC_Outfit_HairBack_%s.fbx','HairFront':'BSMC_Outfit_HairFront_%s.fbx'}[slot] % pid
    cands=[p for p in idx if p.endswith('.fbx') and '/Base/%s/'%slot in p and (os.path.basename(p)==suffix or pid in os.path.basename(p))]
    exact=[p for p in cands if pid.lower() in os.path.basename(p).lower()]
    # precisa casar exatamente o final do nome (PonyTailLong x PonyTailShort etc.)
    ex=[p for p in exact if os.path.basename(p).lower().endswith('_'+pid.lower()+'.fbx')]
    assert len(ex)==1,(slot,pid,ex)
    return ex[0]

def tex_for(idx, fbxpath):
    folder=os.path.dirname(fbxpath)
    ds=[p for p in idx if os.path.dirname(p)==folder and p.lower().endswith('_d.png')]
    assert len(ds)==1,(folder,ds); return ds[0]

def convert(m, tile_xy):
    x0,y0=tile_xy
    V=m['V']; cv=m['corner_v']; nc=len(cv)
    uv=np.clip(m['cuv'],0.0,1.0)
    tris=[]
    for poly in m['polys']:
        for k in range(1,len(poly)-1): tris.append((poly[0],poly[k],poly[k+1]))
    key={}; verts=[]; idx=[]
    for tri in tris:
        for c in tri:
            kk=(int(cv[c]), round(float(uv[c][0]),5), round(float(uv[c][1]),5), tuple(np.round(m['cn'][c],4)))
            if kk not in key:
                key[kk]=len(verts); verts.append(c)
            idx.append(key[kk])
    verts=np.array(verts); idx=np.array(idx,np.uint16)
    pos=V[cv[verts]]+HEAD
    nor=m['cn'][verts].astype(np.float64); nor/=np.maximum(np.linalg.norm(nor,axis=1,keepdims=True),1e-9)
    u=(x0+uv[verts][:,0]*T)/ATL; v=(y0+(1-uv[verts][:,1])*T)/ATL
    return pos,nor,np.stack([u,v],1),idx

def write_cup1(path,pos,nor,uv,idx):
    n=len(pos)
    REC=np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)])
    r=np.zeros(n,REC); r['pos']=pos; r['nor']=nor; r['uv']=uv; r['col']=255
    t=np.clip((150.0-pos[:,1])/10.0,0,1)         # abaixo de y=140 segue o peito (osso 4), acima de 150 só a cabeça (osso 8)
    r['bi'][:,0]=8; r['bi'][:,1]=4
    w1=np.round(t*255).astype(np.uint8); r['bw'][:,0]=255-w1; r['bw'][:,1]=w1
    with open(path,'wb') as f:
        f.write(b'CUP1'+struct.pack('<3i',n,len(idx),0)); f.write(r.tobytes()); f.write(idx.astype('<u2').tobytes())

def main(upk,out):
    idx=index(upk)
    jobs=[('HairBack',p) for p in BACK]+[('HairFront',p) for p in FRONT]
    texmap={}   # textura -> tile
    atlas=np.zeros((ATL,ATL,3)); a0=np.zeros((ATL,ATL)); a1=np.zeros((ATL,ATL)); sh=np.zeros((ATL,ATL)); rid=np.zeros((ATL,ATL),np.uint8)
    man=[]; stats=[]
    for slot,pid in jobs:
        fp=find(idx,slot,pid); tp=tex_for(idx,fp)
        if tp not in texmap:
            n=len(texmap); texmap[tp]=((n%COLS)*T,(n//COLS)*T)
            x0,y0=texmap[tp]
            im=Image.open(idx[tp]).convert('RGB').resize((T,T),Image.LANCZOS)
            M=np.asarray(im).astype(float)/255
            R,G,B=M[...,0],M[...,1],M[...,2]
            tot=R+G+B; w1=np.clip((G+B)/np.maximum(tot,1e-4),0,1); w1=np.where(tot>0.03,w1,0.0); w0=1-w1
            shade=np.clip(0.35+0.75*M.max(-1),0.3,1.1)
            ref=(w0[...,None]*C0+w1[...,None]*C1)
            sl=(slice(y0,y0+T),slice(x0,x0+T))
            atlas[sl]=np.clip(ref*shade[...,None],0,255); a0[sl]=w0; a1[sl]=w1; sh[sl]=shade; rid[sl]=1
        m=load_mesh(idx[fp])
        pos,nor,uv,ix=convert(m,texmap[tp])
        fn='p_%s_%s.bin'%(slot.lower(),pid.lower())
        write_cup1(os.path.join(out,fn),pos,nor,uv,ix)
        man.append('%s|%s|%s|hair.png'%(slot[0].lower()+slot[1:] if slot=='HairFront' else 'hairBack',pid,fn))
        stats.append((slot,pid,len(pos),len(ix)//3,os.path.basename(tp)))
        print(slot,pid,len(pos),'v',len(ix)//3,'tris',pos.min(0).round(1),pos.max(0).round(1))
    # tiles não usados: cinza neutro fora de região (id 0)
    atlas[rid==0]=(128,128,128)
    Image.fromarray(np.round(atlas).astype(np.uint8)).save(os.path.join(out,'hair.png'),optimize=True)
    img=np.zeros((ATL,ATL,3),np.uint8); img[...,0]=np.round(a0*255); img[...,1]=np.round(a1*255); img[...,2]=rid
    Image.fromarray(img).save(os.path.join(out,'hair_recolor.png'),optimize=True)
    g=np.round(np.clip(sh,0,2)/2*255).astype(np.uint8)
    Image.fromarray(np.stack([g,g,g],-1)).save(os.path.join(out,'hair_recolor_s.png'),optimize=True)
    open(os.path.join(out,'hair_recolor.txt'),'w').write('# id|nome|slot0|slot1|ref0 (sRGB 0..255)|ref1\n1|cabelo|2|3|%s|%s\n'%(' '.join('%.1f'%x for x in C0),' '.join('%.1f'%x for x in C1)))
    open(os.path.join(out,'hair_pieces.txt'),'w').write('\n'.join(man)+'\n')
    print(len(texmap),'texturas em',ATL,'x',ATL)
if __name__=='__main__': main(sys.argv[1],sys.argv[2])
