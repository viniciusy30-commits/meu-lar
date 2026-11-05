import numpy as np, math
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
from furn_lib import *
from flora_lib import *
WK=K('grain',F['WOOD']); MK=K('metal',F['METAL']); PK=K('white',F['PLAIN'])
GLK=('white.png',F['PLAIN'],0)

def cloud_tex():
    W,H=512,256; r=np.random.default_rng(4); a=np.zeros((H,W)); y,x=np.mgrid[0:H,0:W]
    for i in range(70):
        cx=r.uniform(90,W-90); cy=r.uniform(H*0.45,H*0.7)*1.0; rx=r.uniform(40,90); ry=rx*r.uniform(0.35,0.6)
        cy-= (1-abs(cx-W/2)/(W/2))*40*r.random()
        a=np.maximum(a,np.clip(1-(((x-cx)/rx)**2+((y-cy)/ry)**2),0,1)**0.6)
    a=ndimage.gaussian_filter(a,6); a=np.clip(a*1.5,0,1)
    base=ndimage.gaussian_filter(a,25); shade=np.clip(1-(y/H-0.35)*0.9,0.55,1.0)
    top=np.clip(0.80+0.22*(1-base)*shade,0,1)
    rgb=np.stack([top*255,(top*0.985)*255,(top*0.96+0.02)*255],-1)
    low=np.clip((y/H-0.5)*1.6,0,1)[...,None]*0.18; rgb=rgb*(1-low)+np.array([150,170,200])*low
    rgb[...,:]=np.clip(rgb,0,255)
    al=(a**1.2*255)
    al[:,:20]*=np.linspace(0,1,20); al[:,-20:]*=np.linspace(1,0,20); al[:12]*=np.linspace(0,1,12)[:,None]; al[-12:]*=np.linspace(1,0,12)[:,None]
    Image.fromarray(np.dstack([rgb,al]).astype(np.uint8)).save(OUT+'tex/cloud.png')

def cloud():
    A=Asset('cloud_a'); key=('cloud.png',0,0)
    A.add(key,[(-0.5,-0.25,0),(0.5,-0.25,0),(0.5,0.25,0),(-0.5,0.25,0)],[(0,0,0)]*4,[(1,1,1,1)]*4,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
    return A

def lamp():
    A=Asset('lamp_post'); iron=(0.16,0.17,0.19); 
    A.lathe(MK,(0,0,0),[(0,0),(0.15,0),(0.15,0.04),(0.11,0.07),(0.075,0.14),(0.05,0.22),(0.04,0.3)],sides=16,col=iron+(1,))
    A.lathe(MK,(0,0,0),[(0.04,0.3),(0.032,0.6),(0.03,1.4),(0.036,1.52),(0.05,1.56),(0.05,1.6)],sides=14,col=iron+(1,))
    # lanterna: base, vidro luminoso, tampa
    A.lathe(MK,(0,1.58,0),[(0.0,0),(0.11,0),(0.13,0.03),(0.1,0.06),(0,0.06)],sides=16,col=iron+(1,))
    A.lathe(PK,(0,1.64,0),[(0.095,0),(0.115,0.12),(0.12,0.2),(0.1,0.28),(0.085,0.3)],sides=16,col=(1.0,0.93,0.68,1))
    for k in range(4):
        a=k*math.pi/2+math.pi/4; 
        A.tube(MK,[V(math.cos(a)*0.1,1.64,math.sin(a)*0.1),V(math.cos(a)*0.118,1.78,math.sin(a)*0.118),V(math.cos(a)*0.095,1.94,math.sin(a)*0.095)],[0.008]*3,sides=6,col=lambda p,t:iron+(1,))
    A.lathe(MK,(0,1.93,0),[(0.0,0.0),(0.15,0.0),(0.14,0.02),(0.09,0.06),(0.04,0.1),(0.022,0.13),(0.0,0.18)],sides=16,col=iron+(1,))
    A.lathe(PK,(0,2.04,0),[(0,0),(0.02,0.01),(0.025,0.03),(0.012,0.06),(0,0.07)],sides=8,col=(0.2,0.2,0.22,1))
    return A

def bench():
    A=Asset('bench'); wd=(0.80,0.58,0.36); iron=(0.15,0.16,0.18)
    for z in np.linspace(-0.2,0.15,4): rbox(A,WK,(0,0.46,z),(1.5,0.04,0.075),0.012,wd,uv=2,step=0.5)
    for i,(y,tz) in enumerate([(0.62,-0.27),(0.76,-0.30),(0.90,-0.33)]): rbox(A,WK,(0,y,tz),(1.5,0.1,0.03),0.012,wd,uv=2,step=0.5)
    for sx in (-0.67,0.67):
        A.tube(MK,[V(sx,0,0.18),V(sx,0.2,0.16),V(sx,0.44,0.14)],[0.022,0.02,0.02],sides=8,col=lambda p,t:iron+(1,))
        A.tube(MK,[V(sx,0,-0.2),V(sx,0.3,-0.25),V(sx,0.46,-0.25),V(sx,0.7,-0.3),V(sx,0.95,-0.34)],[0.022,0.02,0.02,0.02,0.02],sides=8,col=lambda p,t:iron+(1,))
        rbox(A,MK,(sx,0.43,-0.02),(0.04,0.03,0.4),0.01,iron,uv=1,step=0.5)
        rbox(A,MK,(sx,0.66,-0.28),(0.04,0.03,0.12),0.01,iron,uv=1,step=0.5)
        A.lathe(MK,(sx,0.95,-0.34),[(0,0),(0.03,0),(0.034,0.02),(0.02,0.04),(0,0.045)],sides=10,col=iron+(1,))
        rbox(A,MK,(sx,0.02,0.18),(0.12,0.02,0.1),0.008,iron,uv=1,step=0.5); rbox(A,MK,(sx,0.02,-0.2),(0.12,0.02,0.1),0.008,iron,uv=1,step=0.5)
    return A

def mailbox():
    A=Asset('mailbox'); 
    rbox(A,WK,(0,0.6,0),(0.09,1.2,0.09),0.015,(0.42,0.30,0.22),uv=2)
    rbox(A,WK,(0.0,1.2,0),(0.13,0.03,0.13),0.01,(0.46,0.33,0.24),uv=2)
    red=(0.78,0.22,0.19)
    # corpo arredondado em arco
    n=14; P=[];N=[];T=[];C=[]
    for i in range(n+1):
        a=math.pi*i/n; 
        for z in (-0.17,0.17):
            P.append(V(0.13*math.cos(a),1.22+0.12*math.sin(a)*0.9+0.0,z)); N.append(V(math.cos(a),math.sin(a),0)); C.append(red+(1,))
    for i in range(n):
        a=i*2; T+=[(a,a+1,a+2),(a+1,a+3,a+2)]
    A.add(MK,P,N,C,[(0,0)]*len(P),T)
    rbox(A,MK,(0,1.215,0),(0.27,0.03,0.34),0.01,red,uv=1,step=0.5)
    rbox(A,MK,(0,1.30,0.175),(0.27,0.0,0.0),0.0,red)
    rbox(A,MK,(0.0,1.26,0.18),(0.25,0.2,0.012),0.01,(0.7,0.18,0.16),uv=1,step=0.5)
    rbox(A,MK,(0.15,1.3,-0.05),(0.012,0.12,0.04),0.004,(0.95,0.8,0.25),uv=1,step=0.5)
    return A

def lantern_cap():
    A=Asset('gate_lantern'); iron=(0.17,0.18,0.2)
    A.lathe(MK,(0,0,0),[(0,0),(0.07,0),(0.08,0.02),(0.06,0.05),(0,0.05)],sides=14,col=iron+(1,))
    A.lathe(PK,(0,0.05,0),[(0.06,0),(0.085,0.1),(0.09,0.16),(0.075,0.22),(0.06,0.23)],sides=14,col=(1.0,0.93,0.68,1))
    A.lathe(MK,(0,0.27,0),[(0.0,0.0),(0.1,0.0),(0.09,0.02),(0.05,0.05),(0.02,0.1),(0,0.12)],sides=14,col=iron+(1,))
    return A

if __name__=='__main__':
    cloud_tex()
    for f in (cloud,lamp,bench,mailbox,lantern_cap):
        A=f(); A.write(); print(A.name,A.stats())
    preview(lamp(),'/tmp/p_lamp.png',views=('front','side'),size=(240,420))
    preview(bench(),'/tmp/p_bench.png',views=('front','side'),size=(420,300))
    preview(mailbox(),'/tmp/p_mail.png',views=('front','side'),size=(300,360))
