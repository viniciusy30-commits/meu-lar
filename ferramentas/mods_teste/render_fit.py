#!/usr/bin/env python3
"""Renderização diagnóstica das roupas Hooded short jacket + cargo pants."""
from pathlib import Path
import struct, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from scipy.spatial import cKDTree

ROOT=Path("app/src/main/assets/cute")
OUT=Path("fit-preview")
OUT.mkdir(exist_ok=True)

def read_cup(path):
    b=path.read_bytes()
    if b[:4] != b"CUP1": raise ValueError(f"{path}: formato inesperado {b[:4]!r}")
    nv,ni,flags=struct.unpack_from("<III",b,4)
    dtype=np.dtype([("pos","<f4",(3,)),("nor","<f4",(3,)),("uv","<f4",(2,)),("rgba","u1",(4,)),("bi","u1",(4,)),("bw","u1",(4,))])
    v=np.frombuffer(b,dtype=dtype,count=nv,offset=16)
    off=16+nv*44
    idx=np.frombuffer(b,dtype="<u2",count=ni,offset=off).reshape(-1,3).astype(np.int32)
    return {"pos":v["pos"].copy(),"nor":v["nor"].copy(),"bi":v["bi"].copy(),"bw":v["bw"].astype(np.float32)/255.0,"idx":idx}

def current_cover(body, garment, ymax, ymin=0.0, protected=None, radius=3.2):
    # Reproduz Cover.mark com faixa vertical e proteção por pesos de osso.
    p=garment["pos"]; n=garment["nor"]
    tree=cKDTree(p)
    tri=body["idx"]; bp=body["pos"]
    centers=bp[tri].mean(axis=1)
    dist,near=tree.query(centers,k=1,workers=-1)
    side=np.einsum("ij,ij->i",centers-p[near],n[near])
    keep=(dist <= radius) & (side < 0.6) & (centers[:,1] <= ymax) & (centers[:,1] >= ymin)
    if protected:
        bi=body["bi"][tri]; bw=body["bw"][tri]
        keep &= ~np.any(np.isin(bi,list(protected)) & (bw >= 0.15),axis=(1,2))
    return keep

def render_view(body, jacket, pants, masks, sex, view, show_jacket=True, show_pants=True, suffix=''):
    # Painter sorting in orthographic projection; colors distinguish body/jacket/pants.
    if view in ("frente","costas"):
        xy=lambda p: p[:,:,[0,1]]
        depth=lambda p: p[:,:,2] if view=="frente" else -p[:,:,2]
    elif view=="lado":
        xy=lambda p: p[:,:,[2,1]]
        depth=lambda p: p[:,:,0]
    else:
        xy=lambda p: p[:,[2,1]]
        depth=lambda p: -p[:,:,0]
    faces=[]
    meshes=[(body,(0.83,0.66,0.54,1.0),masks)]
    if show_jacket: meshes.append((jacket,(0.20,0.23,0.29,1.0),None))
    if show_pants: meshes.append((pants,(0.22,0.38,0.62,1.0),None))
    for mesh,color,mask in meshes:
        tri=mesh["idx"]
        if mask is not None: tri=tri[~mask]
        pos=mesh["pos"]
        for start in range(0,len(tri),4000):
            q=tri[start:start+4000]
            xyz=pos[q]
            z=depth(xyz).mean(axis=1)
            for poly,d in zip(xy(xyz),z):
                faces.append((float(d),poly,color))
    faces.sort(key=lambda x:x[0])
    fig,ax=plt.subplots(figsize=(5,8),dpi=180)
    ax.set_facecolor("#e8e8e8")
    coll=PolyCollection([f[1] for f in faces],facecolors=[f[2] for f in faces],edgecolors="none",closed=True)
    ax.add_collection(coll)
    visible=[body["pos"]]
    if show_jacket: visible.append(jacket["pos"])
    if show_pants: visible.append(pants["pos"])
    p=np.concatenate(visible)
    if view in ("frente","costas"):
        xx=p[:,0]; yy=p[:,1]
    else:
        xx=p[:,2]; yy=p[:,1]
    cx=(xx.min()+xx.max())/2
    span=max(xx.max()-xx.min(),yy.max()-yy.min())
    ax.set_xlim(cx-span*.58,cx+span*.58)
    ax.set_ylim(yy.min()-4,yy.max()+4)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"{sex.upper()} — {suffix or view}",fontsize=12)
    fig.tight_layout(pad=0.2)
    fig.savefig(OUT/f"{sex}_{suffix or view}.png",bbox_inches="tight",pad_inches=.04)
    plt.close(fig)

report={}
for sex,grp in [("masculino","am5"),("feminino","af5")]:
    body=read_cup(ROOT/f"p_body_{grp}.bin")
    jacket=read_cup(ROOT/f"skate/hood_{grp}.cup")
    pants=read_cup(ROOT/f"skate/hcargo_{grp}.cup")
    # Correção candidata: ergue o acabamento inferior 3 cm e afasta a barra 0,75 cm pela normal.
    jacket["pos"]=jacket["pos"].copy()
    y0=jacket["pos"][:,1].copy()
    w=np.clip((114.0-y0)/13.0,0.0,1.0)
    w=w*w*(3.0-2.0*w)
    jacket["pos"][:,1] += 5.0*w
    jacket["pos"] += jacket["nor"]*(1.40*w[:,None])
    neck_y=158.24 if grp=="am5" else 156.52
    hand_bones=set([11,12,15,16]+list(range(25,55)))
    foot_bones=set([18,19,20,22,23,24])
    # A jaqueta não apaga a cintura abaixo da barra; a calça não apaga pés/tornozelos.
    jm=current_cover(body,jacket,neck_y-7,102.0,hand_bones)
    # Sweep de limites/raios da calça para encontrar a menor máscara que ainda cobre a malha.
    pants_top=float(pants["pos"][:,1].max())
    waist_diag={}
    for rad in (3.2,2.4,1.8,1.4,1.0):
        for inset in (0.0,1.0,2.0,3.0):
            test=current_cover(body,pants,pants_top-inset,0.0,foot_bones,rad)
            waist_diag[f"r{rad}_inset{inset}"]={"waist_hidden":int((test&((body["pos"][body["idx"]].mean(axis=1)[:,1]>=72)&(body["pos"][body["idx"]].mean(axis=1)[:,1]<=108))).sum()),"total_hidden":int(test.sum())}
    pm=current_cover(body,pants,pants_top-2.0,0.0,foot_bones,1.4)
    combined=jm|pm
    waist=(centers if False else body["pos"][body["idx"]].mean(axis=1))
    waist=(waist[:,1]>=72)&(waist[:,1]<=108)
    combos={"sem_roupa":(np.zeros_like(combined),False,False),
            "so_jaqueta":(jm,True,False),
            "so_calca":(pm,False,True),
            "jaqueta_e_calca":(combined,True,True)}
    combo_counts={}
    for name,(mask,showj,showp) in combos.items():
        combo_counts[name]={"cintura_total":int(waist.sum()),"cintura_oculta":int((mask&waist).sum())}
        for view in ("frente","costas"):
            render_view(body,jacket,pants,mask,sex,view,showj,showp,f"{name}_{view}")
    centers=body["pos"][body["idx"]].mean(axis=1)
    # Bones de mão/dedos conforme ARM_L/ARM_R em CuteChar.kt.
    hand_bones=set([12,16]+list(range(25,55)))
    hand=np.any(np.isin(body["bi"][body["idx"]],list(hand_bones)) & (body["bw"][body["idx"]]>.15),axis=(1,2))
    foot=centers[:,1] < 18.0
    waist=(centers[:,1]>=72)&(centers[:,1]<=108)
    seam=(jacket["pos"][:,1]>=72)&(jacket["pos"][:,1]<=108)&(jacket["pos"][:,2]<0)
    tree=cKDTree(pants["pos"])
    ds,_=tree.query(jacket["pos"][seam],k=1,workers=-1)
    def bone_distribution(tri_mask):
        ids=body["idx"][tri_mask]
        bi=body["bi"][ids]
        bw=body["bw"][ids]
        vals={}
        for bone in range(55):
            vals[str(bone)]=round(float(bw[bi==bone].sum()),2)
        return {k:v for k,v in vals.items() if v>0}
    near=ds<1.0
    report[sex]={
      "jacket_y_range_cm":[float(jacket["pos"][:,1].min()),float(jacket["pos"][:,1].max())],
      "jacket_hem_lift_max_cm":5.0,"jacket_hem_outset_max_cm":1.40,
      "mask_protected_hand_bones":sorted(hand_bones),"mask_protected_foot_bones":sorted(foot_bones),
      "pants_y_range_cm":[float(pants["pos"][:,1].min()),float(pants["pos"][:,1].max())],
      "jacket_z_range_cm":[float(jacket["pos"][:,2].min()),float(jacket["pos"][:,2].max())],
      "pants_z_range_cm":[float(pants["pos"][:,2].min()),float(pants["pos"][:,2].max())],
      "hidden_hand_bone_weights":bone_distribution(combined&hand),
      "hidden_low_foot_bone_weights":bone_distribution(combined&foot),
      "hidden_foot_y_range_cm":[float(centers[combined&foot,1].min()),float(centers[combined&foot,1].max())] if np.any(combined&foot) else None,
      "pants_mask_sweep":waist_diag,
      "pants_mask_candidate":{"radius_cm":1.4,"top_inset_cm":2.0},
      "combination_waist_masks":combo_counts,
      "hidden_waist_by_jacket":int((jm&waist).sum()),
      "hidden_waist_by_pants":int((pm&waist).sum()),
      "jacket_pants_close_y_range_cm":[float(jacket["pos"][seam][near,1].min()),float(jacket["pos"][seam][near,1].max())] if np.any(near) else None,
      "jacket_pants_close_z_range_cm":[float(jacket["pos"][seam][near,2].min()),float(jacket["pos"][seam][near,2].max())] if np.any(near) else None,
      "body_vertices":int(len(body["pos"])),"jacket_vertices":int(len(jacket["pos"])),"pants_vertices":int(len(pants["pos"])),
      "body_triangles":int(len(body["idx"])),"jacket_cover_triangles":int(jm.sum()),"pants_cover_triangles":int(pm.sum()),
      "hidden_hand_triangles":int((combined&hand).sum()),"hand_triangles":int(hand.sum()),
      "hidden_low_foot_triangles":int((combined&foot).sum()),"low_foot_triangles":int(foot.sum()),
      "hidden_waist_triangles":int((combined&waist).sum()),"waist_triangles":int(waist.sum()),
      "back_waist_jacket_vertices":int(seam.sum()),
      "back_waist_jacket_vertices_within_1cm_of_pants":int((ds<1.0).sum()) if len(ds) else 0,
      "back_waist_min_distance_cm":float(ds.min()) if len(ds) else None
    }
    for view in ("frente","costas","lado"):
        render_view(body,jacket,pants,combined,sex,view,True,True)

(OUT/"diagnostico.json").write_text(json.dumps(report,indent=2,ensure_ascii=False))
# Contact sheet
from PIL import Image, ImageDraw
files=[OUT/f"{s}_{c}_{v}.png" for s in ("masculino","feminino") for c in ("sem_roupa","so_jaqueta","so_calca","jaqueta_e_calca") for v in ("frente","costas")]
ims=[Image.open(f).convert("RGB") for f in files]
w=max(i.width for i in ims); h=max(i.height for i in ims)
sheet=Image.new("RGB",(w*4,h*4),"white")
for k,im in enumerate(ims): sheet.paste(im.resize((w,h)),((k%4)*w,(k//4)*h))
sheet.save(OUT/"combinacoes_cintura.png")
print(json.dumps(report,indent=2,ensure_ascii=False))
