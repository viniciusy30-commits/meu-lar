import json,math,sys,struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont
src=sys.argv[1]; out=sys.argv[2]; S=float(sys.argv[3]) if len(sys.argv)>3 else 0.3
cx=float(sys.argv[4]) if len(sys.argv)>4 else None
d=json.load(open(src)); WX,WZ=d['world']
raw=open('relevo.bin','rb').read();nx,nz,g=struct.unpack('<iif',raw[:12]);H=np.frombuffer(raw[12:12+nx*nz*2],'<i2').reshape(nz,nx)/100
if cx is None: x0,z0,x1,z1=0,0,WX,WZ
else:
    cz=float(sys.argv[5]);half=float(sys.argv[6]);x0,z0,x1,z1=cx-half,cz-half,cx+half,cz+half
N=(int((x1-x0)*S),int((z1-z0)*S))
ys,xs=np.mgrid[0:N[1],0:N[0]];wx=np.clip((x0+xs/S)/g,0,nx-1.01).astype(int);wz=np.clip((z0+ys/S)/g,0,nz-1.01).astype(int);hh=H[wz,wx]
a=np.zeros((N[1],N[0],3),np.uint8)
t=np.clip(hh/40,0,1)[...,None]
a[:]=(np.array([120,175,95])*(1-t)+np.array([200,205,150])*t).astype(np.uint8)
a[(hh>=-0.1)&(hh<1.3)]=(228,214,164);a[hh<-0.1]=(70,140,205)
im=Image.fromarray(a);dr=ImageDraw.Draw(im)
P=lambda x,z:((x-x0)*S,(z-z0)*S)
for r in d['roads']:
    p=r['p'];pts=[P(p[i],p[i+1]) for i in range(0,len(p),4)]
    col=(60,62,70) if r['c']<=1 else ((95,95,105) if r['c']==2 else (130,130,138))
    dr.line(pts,fill=col,width=max(1,int(r['w']*S)))
    for i in range(0,len(p)-4,4):
        if p[i+3]: dr.line([P(p[i],p[i+1]),P(p[i+4],p[i+5])],fill=(200,120,60),width=max(2,int(r['w']*S)))
for h in d['rounds']:
    x,z=P(h['x'],h['z']);rr=h['r']*S;dr.ellipse([x-rr,z-rr,x+rr,z+rr],fill=(60,62,70));ri=rr*.45;dr.ellipse([x-ri,z-ri,x+ri,z+ri],fill=(150,200,120))
col={0:(235,200,160),1:(210,150,120),2:(240,170,70),3:(200,200,215),4:(120,150,200),5:(60,90,160)}
b=d.get('bld',[])
for i in range(0,len(b),9):
    x,z,w,dd,fl,ang,k=b[i:i+7];c,s=math.cos(ang),math.sin(ang)
    pts=[P(x+c*u-s*v,z+s*u+c*v) for u,v in((-w/2,-dd/2),(w/2,-dd/2),(w/2,dd/2),(-w/2,dd/2))]
    dr.polygon(pts,fill=col[int(k)],outline=(60,60,60) if S>0.6 else None)
t=d.get('tree',[])
for i in range(0,len(t),6):
    x,z=P(t[i],t[i+1]);r=max(0.6,1.8*S*t[i+3]);dr.ellipse([x-r,z-r,x+r,z+r],fill=(40,115,50))
for h in d['houses']:
    x,z=P(h['x'],h['z']);dr.rectangle([x-4,z-4,x+4,z+4],fill=(255,0,200));dr.text((x+5,z-5),str(h['k']+1),fill=(0,0,0))
for l in d.get('labels',[]):
    x,z=P(l['x'],l['z']);dr.text((x,z),l['t'],fill=(0,0,0))
im.save(out)
