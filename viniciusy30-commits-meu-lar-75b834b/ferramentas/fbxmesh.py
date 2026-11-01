import numpy as np
from fbxr import *
def tris_from(PVI):
    # PVI: polygon vertex indices with negative end marker; fan triangulation
    polys=[];cur=[]
    for i,x in enumerate(PVI):
        if x<0: cur.append(~x); polys.append(cur); cur=[]
        else: cur.append(x)
    return polys
def load_mesh(path):
    r=parse(path); ob=r.get('Objects'); g=ob.get('Geometry')
    V=g.get('Vertices').props[0].reshape(-1,3).astype(np.float64)
    PVI=g.get('PolygonVertexIndex').props[0]
    # corner list
    corner_v=np.where(PVI<0,~PVI,PVI)
    polys=[];cur=[]
    for ci,x in enumerate(PVI):
        cur.append(ci)
        if x<0: polys.append(cur); cur=[]
    ln=g.get('LayerElementNormal'); N=ln.get('Normals').props[0].reshape(-1,3)
    mapn=ln.get('MappingInformationType').props[0]
    lu=g.get('LayerElementUV'); UV=lu.get('UV').props[0].reshape(-1,2); UVI=lu.get('UVIndex').props[0]
    cn=N[corner_v] if mapn=='ByVertice' else N[np.arange(len(PVI))]
    cuv=UV[UVI]
    mats=None
    lm=g.get('LayerElementMaterial')
    if lm and lm.get('MappingInformationType').props[0]=='ByPolygon': mats=lm.get('Materials').props[0]
    return dict(V=V,corner_v=corner_v,polys=polys,cn=cn,cuv=cuv,mats=mats,root=r)
