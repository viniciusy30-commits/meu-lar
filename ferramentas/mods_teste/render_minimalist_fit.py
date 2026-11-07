#!/usr/bin/env python3
"""Renderiza corpo masculino com cada peça Minimalist e combinações."""
from pathlib import Path
import struct, json
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw
ROOT=Path("app/src/main/assets/cute")
OUT=Path("fit-minimalist"); OUT.mkdir(exist_ok=True)
def read(p):
 b=p.read_bytes()
 if b[:4]!=b"CUP1": raise ValueError(f"CUP1 inválido: {p}")
 nv,ni,_=struct.unpack_from("<III",b,4)
 dt=np.dtype([("pos","<f4",(3,)),("nor","<f4",(3,)),("uv","<f4",(2,)),("rgba","u1",(4,)),("bi","u1",(4,)),("bw","u1",(4,))])
 v=np.frombuffer(b,dtype=dt,count=nv,offset=16)
 idx=np.frombuffer(b,dtype="<u2",count=ni,offset=16+nv*44).reshape(-1,3).astype(np.int32)
 if idx.max()>=nv: raise ValueError(f"índice fora da malha: {p}")
 return {"pos":v["pos"].copy(),"nor":v["nor"].copy(),"uv":v["uv"].copy(),"idx":idx}
body=read(ROOT/"p_body_am5.bin")
items={n:read(ROOT/"skate"/(n+".cup")) for n in ("minimalist_top_am5","minimalist_short_am5","minimalist_jeans_am5")}
# Métrica de proximidade roupa-corpo em pontos amostrados; não substitui inspeção visual no aparelho.
metrics={}
tree=cKDTree(body["pos"])
for n,g in items.items():
 d,_=tree.query(g["pos"],k=1)
 metrics[n]={"vertices":len(g["pos"]),"triangles":len(g["idx"]),"y_min":float(g["pos"][:,1].min()),"y_max":float(g["pos"][:,1].max()),"nearest_body_mean_cm":float(d.mean()),"nearest_body_p95_cm":float(np.percentile(d,95)),"uv_min":g["uv"].min(axis=0).tolist(),"uv_max":g["uv"].max(axis=0).tolist()}
def cover(g):
 # Oculta a pele apenas onde a superfície da roupa está realmente próxima.
 tri=body["idx"]; centers=body["pos"][tri].mean(axis=1)
 tr=cKDTree(g["pos"]); d,_=tr.query(centers,k=1)
 return (d<1.65)
def render(names,view):
 masks=[cover(items[n]) for n in names]
 hide=np.logical_or.reduce(masks) if masks else np.zeros(len(body["idx"]),bool)
 if view in ("frente","costas"):
  project=lambda p:p[:,[0,1]]
  depth=lambda p:p[:,2] if view=="frente" else -p[:,2]
 else:
  project=lambda p:p[:,[2,1]]
  depth=lambda p:p[:,0] if view=="lado" else -p[:,0]
 meshes=[(body,(205,163,135),hide)]
 palette={"minimalist_top_am5":(42,53,78),"minimalist_short_am5":(60,111,157),"minimalist_jeans_am5":(55,91,145)}
 meshes += [(items[n],palette[n],None) for n in names]
 allp=np.concatenate([m[0]["pos"] for m in meshes])
 q=project(allp); lo=q.min(axis=0); hi=q.max(axis=0); span=max(hi-lo)*1.12
 W,H=720,1080; scale=min((W-24)/span,(H-24)/span); center=(lo+hi)/2
 zbuf=np.full((H,W),-np.inf,np.float32); canvas=np.full((H,W,3),235,np.uint8)
 for mesh,color,mask in meshes:
  pos=mesh["pos"]; tri=mesh["idx"]
  if mask is not None: tri=tri[~mask]
  for ids in tri:
   xyz=pos[ids]; xy=project(xyz); px=(W/2+(xy[:,0]-center[0])*scale); py=(H/2-(xy[:,1]-center[1])*scale); zz=depth(xyz)
   x0=max(0,int(np.floor(px.min()))); x1=min(W-1,int(np.ceil(px.max())))
   y0=max(0,int(np.floor(py.min()))); y1=min(H-1,int(np.ceil(py.max())))
   if x1<x0 or y1<y0: continue
   ax,ay=px[0],py[0]; bx,by=px[1],py[1]; cx,cy=px[2],py[2]
   den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
   if abs(den)<1e-8: continue
   gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
   a=((by-cy)*(gx-cx)+(cx-bx)*(gy-cy))/den
   b=((cy-ay)*(gx-cx)+(ax-cx)*(gy-cy))/den
   c=1-a-b; inside=(a>=-1e-5)&(b>=-1e-5)&(c>=-1e-5)
   z=a*zz[0]+b*zz[1]+c*zz[2]; sub=zbuf[y0:y1+1,x0:x1+1]
   take=inside&(z>sub)
   if take.any(): sub[take]=z[take]; canvas[y0:y1+1,x0:x1+1][take]=color
 im=Image.fromarray(canvas); ImageDraw.Draw(im).text((14,12),"MASCULINO — "+(" + ".join(names) if names else "corpo") +" — "+view,fill=(15,15,15))
 return im
combos={"camiseta_short":["minimalist_top_am5","minimalist_short_am5"],"camiseta_jeans":["minimalist_top_am5","minimalist_jeans_am5"],"short":["minimalist_short_am5"],"jeans":["minimalist_jeans_am5"],"camiseta":["minimalist_top_am5"]}
for name,names in combos.items():
 for view in ("frente","costas","lado"): render(names,view).save(OUT/f"{name}_{view}.png")
# Painel compacto com vistas das combinações mais importantes.
files=[OUT/f"{name}_{view}.png" for name in ("camiseta_short","camiseta_jeans") for view in ("frente","costas","lado")]
ims=[Image.open(p).resize((360,540)) for p in files]
sheet=Image.new("RGB",(1080,1080),"white")
for i,im in enumerate(ims): sheet.paste(im,((i%3)*360,(i//3)*540))
sheet.save(OUT/"painel_combinacoes.png")
(OUT/"diagnostico.json").write_text(json.dumps(metrics,indent=2,ensure_ascii=False))
print(json.dumps(metrics,ensure_ascii=False))
print("RENDER_MINIMALIST_OK")
