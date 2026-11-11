# Prévia fiel à geometria do Relevo.kt (etapa 180b): asfalto até o centro, meio-fio com bocas, faixa central cortada, rotatória aberta
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw
d=json.load(open('city3.json'))
ROADS=[]
for o in d['roads']:
    p=np.array(o['p'],float).reshape(-1,4); x=p[:,0];z=p[:,1];y=p[:,2]; n=len(x)
    if n<2: continue
    nx=np.zeros(n);nz=np.zeros(n)
    for q in range(n):
        a=max(q-1,0);b=min(q+1,n-1);tx=x[b]-x[a];tz=z[b]-z[a];l=math.hypot(tx,tz)
        if l<1e-4: tx,tz=1,0
        else: tx/=l;tz/=l
        nx[q]=-tz;nz[q]=tx
    if 'n0' in o: nx[0],nz[0]=o['n0']
    if 'n1' in o: nx[-1],nz[-1]=o['n1']
    cs=np.r_[0,np.cumsum(np.hypot(np.diff(x),np.diff(z)))]
    ROADS.append(dict(c=o['c'],w=o['w'],x=x,z=z,y=y,nx=nx,nz=nz,cs=cs,ta=o.get('a',0),tb=o.get('b',0),gl=o.get('cl',[]),gr=o.get('cr',[]),n=o['n']))
HUBS=d['rounds']
def spans(s0,s1,gaps):
    out=[];cur=s0;i=0
    while i+1<len(gaps):
        g0,g1=gaps[i],gaps[i+1];i+=2
        if g1<=cur: continue
        if g0>=s1: break
        if g0>cur: out.append((cur,g0))
        cur=max(cur,g1)
        if cur>=s1: break
    if cur<s1-1e-3: out.append((cur,s1))
    return out
def arm_at(qx,qz,h):
    a=h['arms'];i=0
    while i+4<len(a):
        dx=qx-a[i];dz=qz-a[i+1];ux=a[i+2];uz=a[i+3]
        ax=dx*ux+dz*uz;lat=abs(-dx*uz+dz*ux)
        if ax>=-2 and lat<=a[i+4]+0.15: return True
        i+=5
    return False
def render(cx,cz,half,S,fn):
    W=int(2*half*S);im=Image.new('RGB',(W,W),(120,170,80));dr=ImageDraw.Draw(im)
    def P(x,z): return ((x-cx+half)*S,(z-cz+half)*S)
    ASPH=(70,75,80);CURB=(215,205,185);LINE=(255,255,255);LY=(255,213,79)
    near=[r for r in ROADS if (abs(r['x']-cx).min()<half+30 and abs(r['z']-cz).min()<half+30)]
    def quad(a,b,c,e,col): dr.polygon([P(*a),P(*b),P(*c),P(*e)],fill=col)
    for h in HUBS:
        if abs(h['x']-cx)<half+40 and abs(h['z']-cz)<half+40:
            dr.ellipse([P(h['x']-h['r'],h['z']-h['r']),P(h['x']+h['r'],h['z']+h['r'])],fill=ASPH)
    for r in near:
        for q in range(len(r['x'])-1):
            hw=r['w']/2
            a=(r['x'][q]+r['nx'][q]*hw,r['z'][q]+r['nz'][q]*hw);b=(r['x'][q]-r['nx'][q]*hw,r['z'][q]-r['nz'][q]*hw)
            c=(r['x'][q+1]-r['nx'][q+1]*hw,r['z'][q+1]-r['nz'][q+1]*hw);e=(r['x'][q+1]+r['nx'][q+1]*hw,r['z'][q+1]+r['nz'][q+1]*hw)
            quad(a,b,c,e,ASPH)
    for h in HUBS:
        if abs(h['x']-cx)<half+40 and abs(h['z']-cz)<half+40:
            ri=h['r']*0.45;r2=h['r']+1.8;nc=96
            for k in range(nc):
                a0=k*2*math.pi/nc;a1=(k+1)*2*math.pi/nc
                am=(a0+a1)/2
                if arm_at(math.cos(am)*(h['r']+0.9),math.sin(am)*(h['r']+0.9),h): continue
                quad((h['x']+math.cos(a0)*h['r'],h['z']+math.sin(a0)*h['r']),(h['x']+math.cos(a0)*r2,h['z']+math.sin(a0)*r2),(h['x']+math.cos(a1)*r2,h['z']+math.sin(a1)*r2),(h['x']+math.cos(a1)*h['r'],h['z']+math.sin(a1)*h['r']),CURB)
            dr.ellipse([P(h['x']-ri-1,h['z']-ri-1),P(h['x']+ri+1,h['z']+ri+1)],fill=CURB)
            dr.ellipse([P(h['x']-ri,h['z']-ri),P(h['x']+ri,h['z']+ri)],fill=(185,220,160))
    for r in near:
        cw=1.2 if r['c']==3 else 1.8;hw=r['w']/2
        for q in range(len(r['x'])-1):
            x0,z0,x1,z1=r['x'][q],r['z'][q],r['x'][q+1],r['z'][q+1];ax,az,bx,bz=r['nx'][q],r['nz'][q],r['nx'][q+1],r['nz'][q+1]
            sA,sB=r['cs'][q],r['cs'][q+1];sl=sB-sA
            for side,gp in((1,r['gl']),(-1,r['gr'])):
                for s0,s1 in spans(sA,sB,gp):
                    t0=(s0-sA)/sl if sl>1e-4 else 0;t1=(s1-sA)/sl if sl>1e-4 else 1
                    p0=(x0+(x1-x0)*t0,z0+(z1-z0)*t0);p1=(x0+(x1-x0)*t1,z0+(z1-z0)*t1)
                    m0=((ax+(bx-ax)*t0)*side,(az+(bz-az)*t0)*side);m1=((ax+(bx-ax)*t1)*side,(az+(bz-az)*t1)*side)
                    quad((p0[0]+m0[0]*hw,p0[1]+m0[1]*hw),(p0[0]+m0[0]*(hw+cw),p0[1]+m0[1]*(hw+cw)),(p1[0]+m1[0]*(hw+cw),p1[1]+m1[1]*(hw+cw)),(p1[0]+m1[0]*hw,p1[1]+m1[1]*hw),CURB)
    for r in near:
        if r['c']>2: continue
        tot=r['cs'][-1]
        for q in range(len(r['x'])-1):
            sA,sB=r['cs'][q],r['cs'][q+1];sl=sB-sA;s0=max(sA,r['ta']);s1=min(sB,tot-r['tb'])
            if s1>s0+1e-3 and sl>1e-4:
                t0=(s0-sA)/sl;t1=(s1-sA)/sl;x0,z0,x1,z1=r['x'][q],r['z'][q],r['x'][q+1],r['z'][q+1]
                dr.line([P(x0+(x1-x0)*t0,z0+(z1-z0)*t0),P(x0+(x1-x0)*t1,z0+(z1-z0)*t1)],fill=LY if r['c']==0 else LINE,width=max(1,int(0.3*S)))
    im.save(fn);return im
if __name__=='__main__':
    cx,cz,half,S=map(float,sys.argv[1:5]);render(cx,cz,half,S,sys.argv[5])
