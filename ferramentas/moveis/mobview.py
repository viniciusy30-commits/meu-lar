import sys,struct,os,json,math
import numpy as np
from PIL import Image,ImageDraw
def readbin(path):
    b=open(path,'rb').read(); assert b[:4]==b'MOB1'
    nt,np_,cw,ch=struct.unpack_from('<4I',b,4); o=20
    texs=[]
    for _ in range(nt):
        l=b[o];o+=1;texs.append(b[o:o+l].decode());o+=l
    parts=[]
    for _ in range(np_):
        mat,ti,cut,r,g,bl,a=struct.unpack_from('<bhbffff',b,o);o+=struct.calcsize('<bhbffff')
        nv,ni=struct.unpack_from('<II',b,o);o+=8
        v=np.frombuffer(b,dtype='<f4',count=nv*8,offset=o).reshape(nv,8);o+=nv*32
        idx=np.frombuffer(b,dtype='<u2',count=ni,offset=o);o+=ni*2
        parts.append(dict(mat=mat,tex=texs[ti] if ti>=0 else None,cut=cut,tint=(r,g,bl,a),v=v,idx=idx))
    assert o==len(b)
    return dict(cw=cw,ch=ch,parts=parts)
def render(item,texdir,size=256,yaw=25,pitch=28,bg=(238,240,244)):
    img=Image.new('RGB',(size,size),bg); dr=ImageDraw.Draw(img)
    cw,ch=item['cw'],item['ch']
    cy,sy=math.cos(math.radians(yaw)),math.sin(math.radians(yaw)); cp,sp=math.cos(math.radians(pitch)),math.sin(math.radians(pitch))
    def proj(P):
        P=P-np.array([cw/2,0,ch/2])
        x=P[:,0]*cy+P[:,2]*sy; z=-P[:,0]*sy+P[:,2]*cy
        y=P[:,1]*cp-z*sp; d=P[:,1]*sp+z*cp
        return x,y,d
    allP=np.concatenate([p['v'][:,:3] for p in item['parts']])
    x,y,d=proj(allP); ext=max(x.max()-x.min(),y.max()-y.min(),1e-6); sc=size*0.86/ext
    cx=(x.max()+x.min())/2; cyy=(y.max()+y.min())/2
    L=np.array([0.45,1.0,0.65]);L/=np.linalg.norm(L)
    tris=[]
    for p in item['parts']:
        tex=None
        if p['tex']:
            try: tex=np.array(Image.open(texdir+'/'+p['tex']).convert('RGBA'))
            except Exception as e: tex=None
        v=p['v']; I=p['idx'].reshape(-1,3)
        X,Y,D=proj(v[:,:3])
        for t in I:
            n=v[t,3:6].mean(0); nn=np.linalg.norm(n); n=n/nn if nn>0 else n
            uv=v[t,6:8].mean(0)
            if tex is not None:
                h,w=tex.shape[:2]; c=tex[int((uv[1]%1)*h)%h,int((uv[0]%1)*w)%w][:3]/255.
                if p['cut'] and tex[int((uv[1]%1)*h)%h,int((uv[0]%1)*w)%w][3]<128: continue
            else: c=np.array([1,1,1.])
            c=c*np.array(p['tint'][:3])
            lit=0.55+0.5*max(0,float(np.dot(n,L)))
            col=tuple(int(min(255,255*k*lit)) for k in c)
            pts=[(size/2+(X[i]-cx)*sc,size/2-(Y[i]-cyy)*sc) for i in t]
            tris.append((D[t].mean(),pts,col))
    for _,pts,col in sorted(tris,key=lambda a:a[0],reverse=True): dr.polygon(pts,fill=col)
    return img
if __name__=='__main__':
    d=sys.argv[1]; names=sorted(f[:-4] for f in os.listdir(d) if f.endswith('.bin'))
    cols=int(sys.argv[3]) if len(sys.argv)>3 else 6; S=220
    rows=(len(names)+cols-1)//cols; sheet=Image.new('RGB',(cols*S,rows*S+0),(255,255,255)); dr=ImageDraw.Draw(sheet)
    for i,n in enumerate(names):
        it=readbin(d+'/'+n+'.bin'); im=render(it,d+'/tex',S)
        sheet.paste(im,((i%cols)*S,(i//cols)*S)); dr.text(((i%cols)*S+4,(i//cols)*S+4),n,fill=(0,0,0))
    sheet.save(sys.argv[2]); print(sheet.size)
