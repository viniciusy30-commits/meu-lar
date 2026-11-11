
import json,numpy as np,struct,math,sys
from PIL import Image,ImageDraw
d=json.load(open('city3.json'));b=open('relevo.bin','rb').read()
nx,nz,g=struct.unpack('<iif',b[:12]);h=np.frombuffer(b[12:],'<i2').reshape(nz,nx)/100.0
S=float(sys.argv[1]) if len(sys.argv)>1 else 1.0
W,H=int(3200*S),int(2400*S)
gx,gy=np.gradient(h);sh=np.clip(0.55+(-gx-gy)*0.12,0.3,1.0)
im=np.zeros((nz,nx,3));im[...]=np.array([140,195,110])
im*=sh[...,None];im[h<0.3]=[90,150,210]
img=Image.fromarray(im.clip(0,255).astype('uint8')).resize((W,H),Image.BILINEAR);dr=ImageDraw.Draw(img)
col={0:(190,70,70),1:(70,70,80),2:(80,80,90),3:(95,95,105)}
def trimmed(r):
    p=r['p'];pts=[(p[i],p[i+1]) for i in range(0,len(p),4)]
    cs=[0]
    for i in range(1,len(pts)): cs.append(cs[-1]+math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]))
    tot=cs[-1];out=[]
    for i,q in enumerate(pts):
        if r['a']-0.4<=cs[i]<=tot-r['b']+0.4: out.append(q)
    return out
for r in sorted(d['roads'],key=lambda r:-r['c']):
    pts=trimmed(r)
    if len(pts)<2: continue
    dr.line([(x*S,z*S) for x,z in pts],fill=(210,205,190),width=max(1,int((r['w']+3.6)*S)))
for r in sorted(d['roads'],key=lambda r:-r['c']):
    pts=trimmed(r)
    if len(pts)<2: continue
    dr.line([(x*S,z*S) for x,z in pts],fill=col[r['c']],width=max(1,int(r['w']*S)))
for q in d['nodes']:
    rr=(q[3]+1.0) if q[4]==0 else q[3]
    dr.ellipse(((q[0]-rr)*S,(q[1]-rr)*S,(q[0]+rr)*S,(q[1]+rr)*S),fill=(95,95,105))
for q in d['rounds']:
    r=q['r'];dr.ellipse(((q['x']-r)*S,(q['z']-r)*S,(q['x']+r)*S,(q['z']+r)*S),fill=(95,95,105),outline=(210,205,190))
    r2=r*0.45;dr.ellipse(((q['x']-r2)*S,(q['z']-r2)*S,(q['x']+r2)*S,(q['z']+r2)*S),fill=(120,180,100))
for q in d['houses']: dr.rectangle(((q['x']-8)*S,(q['z']-8)*S,(q['x']+8)*S,(q['z']+8)*S),fill=(220,40,40))
img.save('full.png')
for i,(x0,z0) in enumerate([(0,0),(1600,0),(0,1200),(1600,1200)]):
    img.crop((int(x0*S),int(z0*S),int((x0+1600)*S),int((z0+1200)*S))).save(f'q{i}.png')
print('ok')
