import struct, numpy as np, sys
from PIL import Image, ImageDraw
def rd(path):
    d=open(path,'rb').read(); nv,ni,fl=struct.unpack_from('<3I',d,4)
    dt=np.dtype([('p','<3f4'),('n','<3f4'),('uv','<2f4'),('c','4u1'),('bi','4u1'),('bw','4u1')])
    v=np.frombuffer(d,dt,nv,16); idx=np.frombuffer(d,'<u2',ni,16+nv*44).reshape(-1,3).astype(int)
    return v,idx
def splat(v,idx,tex,view,size=(520,760),ymax=190,color=None):
    # rasterize triangles with z-buffer (nearest-depth) using simple barycentric loops on downsized triangles
    W,H=size; img=np.zeros((H,W,3),np.uint8)+40; zb=np.full((H,W),-1e9)
    P=v['p']; uv=v['uv']
    sc=H/ymax*0.96
    def proj(p):
        if view=='front': return (W/2+p[:,0]*sc, H-p[:,1]*sc-10, p[:,2])
        if view=='side': return (W/2+p[:,2]*sc, H-p[:,1]*sc-10, -p[:,0]*0+0)
    X,Y,Z=proj(P)
    th,tw=tex.shape[:2] if tex is not None else (1,1)
    for t in idx:
        xs=X[t]; ys=Y[t]; zs=Z[t]
        x0,x1=int(max(0,xs.min())),int(min(W-1,xs.max())); y0,y1=int(max(0,ys.min())),int(min(H-1,ys.max()))
        if x1<x0 or y1<y0: continue
        gx,gy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1))
        d=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
        if abs(d)<1e-9: continue
        a=((ys[1]-ys[2])*(gx-xs[2])+(xs[2]-xs[1])*(gy-ys[2]))/d
        b=((ys[2]-ys[0])*(gx-xs[2])+(xs[0]-xs[2])*(gy-ys[2]))/d
        c=1-a-b
        m=(a>=0)&(b>=0)&(c>=0)
        if not m.any(): continue
        z=a*zs[0]+b*zs[1]+c*zs[2]
        m&=z>zb[y0:y1+1,x0:x1+1]
        if view=='side': pass
        u=a*uv[t[0],0]+b*uv[t[1],0]+c*uv[t[2],0]; w=a*uv[t[0],1]+b*uv[t[1],1]+c*uv[t[2],1]
        if tex is not None:
            col=tex[np.clip((w*th).astype(int),0,th-1),np.clip((u*tw).astype(int),0,tw-1)][...,:3]
        else:
            col=np.zeros(m.shape+(3,),np.uint8); col[:]=color if color else (200,200,200)
        sub=img[y0:y1+1,x0:x1+1]; sub[m]=col[m]; zb[y0:y1+1,x0:x1+1][m]=z[m]
    return img
if __name__=='__main__':
    body,bidx=rd('/home/claude/work/merged/app/src/main/assets/cute/p_body_am1.bin')
    out=[]
    for f,tx in [('MESH_ambottomboardshortsCBOY.package_0','/tmp/out_7f6bfa7f_AdultLS.package_tex.png'),('MESH_ambodypoloshirtoverhangCBOY.package_0','/tmp/out_7f1075ca_AdultTJ.package_tex.png'),('MESH_amBodyHiphopBaggyCBOY.package_0','/tmp/out_7fae4060_Adulthiphop.package_tex.png')]:
        v,idx=rd('/tmp/out_%s.cull.cup'%f)
        tex=np.asarray(Image.open(tx).convert('RGB'))
        for view in ['front','side']:
            bimg=splat(body,bidx,None,view,color=(180,140,120))
            # overlay piece on body
            pimg=splat(v,idx,tex,view)
            m=(pimg!=40).any(2)
            bimg[m]=pimg[m]
            out.append(bimg)
    W=Image.new('RGB',(520*6,760))
    for i,o in enumerate(out): W.paste(Image.fromarray(o),(i*520,0))
    W=W.resize((520*3,380)); W.save('/tmp/fit_view.png')
