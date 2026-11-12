import json,math,sys,struct
import numpy as np
from PIL import Image, ImageDraw
cx,cz,half,S,out=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),sys.argv[5]
d=json.load(open('city3.json'))
raw=open('relevo.bin','rb').read();nx,nz,g=struct.unpack('<iif',raw[:12]);H=np.frombuffer(raw[12:12+nx*nz*2],'<i2').reshape(nz,nx)/100
N=int(2*half*S);im=Image.new('RGB',(N,N),(120,170,95));dr=ImageDraw.Draw(im)
# água
ys,xs=np.mgrid[0:N,0:N];wx=(cx-half+xs/S)/g;wz=(cz-half+ys/S)/g
wx=np.clip(wx,0,nx-1.01).astype(int);wz=np.clip(wz,0,nz-1.01).astype(int);hh=H[wz,wx]
a=np.asarray(im).copy();a[hh<-0.15]=(80,150,210);a[(hh>=-0.15)&(hh<1.3)]=(225,214,164);im=Image.fromarray(a);dr=ImageDraw.Draw(im)
P=lambda x,z:((x-(cx-half))*S,(z-(cz-half))*S)
for r in d['roads']:
    p=r['p'];pts=[P(p[i],p[i+1]) for i in range(0,len(p),4)]
    dr.line(pts,fill=(70,72,80),width=max(1,int(r['w']*S)))
for h in d['rounds']:
    x,z=P(h['x'],h['z']);rr=h['r']*S;dr.ellipse([x-rr,z-rr,x+rr,z+rr],fill=(70,72,80));ri=rr*.45;dr.ellipse([x-ri,z-ri,x+ri,z+ri],fill=(150,200,120))
col={0:(235,200,160),1:(210,150,120),2:(240,170,70),3:(200,200,215),4:(120,150,200),5:(60,90,160)}
b=d['bld']
for i in range(0,len(b),9):
    x,z,w,dd,fl,ang,k=b[i:i+7];c,s=math.cos(ang),math.sin(ang)
    pts=[P(x+c*u-s*v,z+s*u+c*v) for u,v in((-w/2,-dd/2),(w/2,-dd/2),(w/2,dd/2),(-w/2,dd/2))]
    dr.polygon(pts,fill=col[int(k)],outline=(60,60,60))
t=d['tree']
for i in range(0,len(t),6):
    x,z=P(t[i],t[i+1]);r=max(1,1.8*S*t[i+3]);dr.ellipse([x-r,z-r,x+r,z+r],fill=(40,120,50))
l=d['lamp']
for i in range(0,len(l),4):
    x,z=P(l[i],l[i+1]);dr.ellipse([x-1.5,z-1.5,x+1.5,z+1.5],fill=(255,240,80))
hy=d['hyd']
for i in range(0,len(hy),2):
    x,z=P(hy[i],hy[i+1]);dr.ellipse([x-2,z-2,x+2,z+2],fill=(230,30,30))
im.save(out)
