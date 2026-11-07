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
 return {"pos":v["pos"].copy(),"nor":v["nor"].copy(),"uv":v["uv"].copy(),"bi":v["bi"].copy(),"bw":v["bw"].astype(np.float32)/255.0,"idx":idx}
body=read(ROOT/"p_body_am5.bin")
items={n:read(ROOT/"skate"/(n+".cup")) for n in ("minimalist_top_am5","minimalist_short_am5","minimalist_jeans_am5")}
for n,g in items.items():
 g["tex"]=np.asarray(Image.open(ROOT/"skate"/(n+".png")).convert("RGBA")).copy()
 Image.fromarray(g["tex"]).save(OUT/(n+"_texture.png"))
 Image.fromarray(g["tex"][:,:,3]).save(OUT/(n+"_alpha_channel.png"))
 g["alpha_channel_nonopaque"]=bool(np.any(g["tex"][:,:,3]<250))
 g["tex"][:,:,3]=255
 g["alpha"]=False
# Métrica de proximidade roupa-corpo em pontos amostrados; não substitui inspeção visual no aparelho.
metrics={}
tree=cKDTree(body["pos"])
for n,g in items.items():
 d,_=tree.query(g["pos"],k=1)
 metrics[n]={"vertices":len(g["pos"]),"triangles":len(g["idx"]),"y_min":float(g["pos"][:,1].min()),"y_max":float(g["pos"][:,1].max()),"nearest_body_mean_cm":float(d.mean()),"nearest_body_p95_cm":float(np.percentile(d,95)),"uv_min":g["uv"].min(axis=0).tolist(),"uv_max":g["uv"].max(axis=0).tolist(),"texture_alpha_channel_nonopaque":g["alpha_channel_nonopaque"],"transparent_texture_pixels":int(np.sum(g["tex"][:,:,3]<250)),"texture_pixels":int(g["tex"].shape[0]*g["tex"].shape[1])}
def closest_point_triangle(p,a,b,c):
 ab=b-a; ac=c-a; ap=p-a
 d1=np.dot(ab,ap); d2=np.dot(ac,ap)
 if d1<=0 and d2<=0:return a,np.array([1.,0.,0.])
 bp=p-b; d3=np.dot(ab,bp); d4=np.dot(ac,bp)
 if d3>=0 and d4<=d3:return b,np.array([0.,1.,0.])
 vc=d1*d4-d3*d2
 if vc<=0 and d1>=0 and d3<=0:
  v=d1/(d1-d3);return a+v*ab,np.array([1-v,v,0.])
 cp=p-c; d5=np.dot(ab,cp); d6=np.dot(ac,cp)
 if d6>=0 and d5<=d6:return c,np.array([0.,0.,1.])
 vb=d5*d2-d1*d6
 if vb<=0 and d2>=0 and d6<=0:
  w=d2/(d2-d6);return a+w*ac,np.array([1-w,0.,w])
 va=d3*d6-d5*d4
 if va<=0 and d4-d3>=0 and d5-d6>=0:
  w=(d4-d3)/((d4-d3)+(d5-d6));return b+w*(c-b),np.array([0.,1-w,w])
 den=va+vb+vc
 if abs(den)<1e-12:return a,np.array([1.,0.,0.])
 v=vb/den;w=vc/den;u=1-v-w
 return u*a+v*b+w*c,np.array([u,v,w])
def closest_point_triangle(p,a,b,c):
 ab=b-a; ac=c-a; ap=p-a
 d1=np.dot(ab,ap); d2=np.dot(ac,ap)
 if d1<=0 and d2<=0:return a,np.array([1.,0.,0.])
 bp=p-b; d3=np.dot(ab,bp); d4=np.dot(ac,bp)
 if d3>=0 and d4<=d3:return b,np.array([0.,1.,0.])
 vc=d1*d4-d3*d2
 if vc<=0 and d1>=0 and d3<=0:
  v=d1/(d1-d3);return a+v*ab,np.array([1-v,v,0.])
 cp=p-c; d5=np.dot(ab,cp); d6=np.dot(ac,cp)
 if d6>=0 and d5<=d6:return c,np.array([0.,0.,1.])
 vb=d5*d2-d1*d6
 if vb<=0 and d2>=0 and d6<=0:
  w=d2/(d2-d6);return a+w*ac,np.array([1-w,0.,w])
 va=d3*d6-d5*d4
 if va<=0 and d4-d3>=0 and d5-d6>=0:
  w=(d4-d3)/((d4-d3)+(d5-d6));return b+w*(c-b),np.array([0.,1-w,w])
 den=va+vb+vc
 if abs(den)<1e-12:return a,np.array([1.,0.,0.])
 v=vb/den;w=vc/den;u=1-v-w
 return u*a+v*b+w*c,np.array([u,v,w])
def cover(g,radius=4.5,protected=None,slot="top",side_limit=1.0):
 gp=g["pos"];gn=g["nor"];gi=g["idx"];bp=body["pos"];bi=body["idx"]
 centers=bp[bi].mean(axis=1);tree=cKDTree(gp)
 _,nearest=tree.query(centers,k=min(12,len(gp)),workers=-1)
 if nearest.ndim==1:nearest=nearest[:,None]
 incident=[[] for _ in range(len(gp))]
 for tj,tri in enumerate(gi):
  for v in tri:incident[int(v)].append(tj)
 keep=np.zeros(len(bi),dtype=bool); protected_set=set(protected or [])
 body_bones=body["bi"][bi];body_weights=body["bw"][bi]
 ymin=float(gp[:,1].min())-radius; ymax=float(gp[:,1].max())-7.0 if slot=="top" else float(gp[:,1].max())+0.5
 for ti,center in enumerate(centers):
  if center[1]<ymin or center[1]>ymax: continue
  if protected_set and any(int(bone) in protected_set and weight>=.15 for bone,weight in zip(body_bones[ti].ravel(),body_weights[ti].ravel())):continue
  samples=np.vstack((center,bp[bi[ti]]));covered=0
  for point in samples:
   _,near=tree.query(point,k=min(12,len(gp)),workers=-1)
   if np.isscalar(near):near=[int(near)]
   candidates=set()
   for v in np.atleast_1d(near):candidates.update(incident[int(v)])
   best_d2=float("inf");best_side=float("inf")
   for gj in candidates:
    ids=gi[gj];a,b,cc=gp[ids];q,bary=closest_point_triangle(point,a,b,cc)
    delta=point-q;d2=float(np.dot(delta,delta))
    if d2>=best_d2:continue
    n=(gn[ids]*bary[:,None]).sum(axis=0);nl=float(np.linalg.norm(n))
    side=float(np.dot(delta,n/nl)) if nl>1e-8 else float("inf")
    best_d2=d2;best_side=side
   if best_d2<=radius*radius and best_side<side_limit:covered+=1
  keep[ti]=covered>=3
 return keep
# Mesmas proteções e limites adotados no renderizador Android:
# a camiseta não apaga mãos/dedos; calças preservam pés e tornozelos.
HAND_BONES=[12,16,*range(25,55)]
FOOT_BONES=[18,19,20,22,23,24]
MASKS={
 "minimalist_top_am5":cover(items["minimalist_top_am5"],4.0,HAND_BONES,"top",0.9),
 "minimalist_short_am5":cover(items["minimalist_short_am5"],3.8,FOOT_BONES,"bottom",0.9),
 "minimalist_jeans_am5":cover(items["minimalist_jeans_am5"],4.5,FOOT_BONES,"bottom",0.9)
}

def render(names,view,hide_body=False):
 masks=[MASKS[n] for n in names]
 hide=np.logical_or.reduce(masks) if masks else np.zeros(len(body["idx"]),bool)
 if view in ("frente","costas"):
  project=lambda p:p[:,[0,1]]
  depth=lambda p:p[:,2] if view=="frente" else -p[:,2]
 else:
  project=lambda p:p[:,[2,1]]
  depth=lambda p:p[:,0] if view=="lado" else -p[:,0]
 meshes=[] if hide_body else [(body,(205,163,135),hide)]
 palette={"minimalist_top_am5":(42,53,78),"minimalist_short_am5":(60,111,157),"minimalist_jeans_am5":(55,91,145)}
 meshes += [(items[n],palette[n],None) for n in names]
 allp=np.concatenate([m[0]["pos"] for m in meshes])
 q=project(allp); lo=q.min(axis=0); hi=q.max(axis=0); span=max(hi-lo)*1.12
 W,H=720,1080; scale=min((W-24)/span,(H-24)/span); center=(lo+hi)/2
 zbuf=np.full((H,W),-np.inf,np.float32); canvas=np.full((H,W,3),235,np.uint8)
 for mesh,color,mask in meshes:
  pos=mesh["pos"]; tri=mesh["idx"]; tex=mesh.get("tex")
  if mask is not None: tri=tri[~mask]
  th,tw=(tex.shape[:2] if tex is not None else (0,0))
  uv=mesh.get("uv")
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
   cc=1-a-b; inside=(a>=-1e-5)&(b>=-1e-5)&(cc>=-1e-5)
   z=a*zz[0]+b*zz[1]+cc*zz[2]; sub=zbuf[y0:y1+1,x0:x1+1]
   take=inside&(z>sub)
   if not take.any(): continue
   if tex is not None:
    u=(a*uv[ids[0],0]+b*uv[ids[1],0]+cc*uv[ids[2],0])
    v=(a*uv[ids[0],1]+b*uv[ids[1],1]+cc*uv[ids[2],1])
    tx=tex[np.clip((v*th).astype(int),0,th-1),np.clip((u*tw).astype(int),0,tw-1)]
    outcolor=tx[:,:,:3]
   else: outcolor=np.empty((y1-y0+1,x1-x0+1,3),dtype=np.uint8);outcolor[:]=color
   sub[take]=z[take]
   canvas[y0:y1+1,x0:x1+1][take]=outcolor[take]
 im=Image.fromarray(canvas); ImageDraw.Draw(im).text((14,12),"MASCULINO — "+(" + ".join(names) if names else "corpo") +" — "+view,fill=(15,15,15))
 return im
combos={"camiseta_short":["minimalist_top_am5","minimalist_short_am5"],"camiseta_jeans":["minimalist_top_am5","minimalist_jeans_am5"],"short":["minimalist_short_am5"],"jeans":["minimalist_jeans_am5"],"camiseta":["minimalist_top_am5"]}
render(["minimalist_jeans_am5"],"frente",True).save(OUT/"jeans_sem_corpo_frente.png")
render(["minimalist_short_am5"],"frente",True).save(OUT/"short_sem_corpo_frente.png")
render(["minimalist_top_am5"],"frente",True).save(OUT/"camiseta_sem_corpo_frente.png")
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
