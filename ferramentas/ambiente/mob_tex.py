import numpy as np, math
from flora_lib import *
def rug_b(name='rug_b.png',W=1024,H=512):
    # passadeira: listras largas e borda
    y,x=np.mgrid[0:H,0:W]; u=(x+0.5)/W; v=(y+0.5)/H
    cream=np.array([236,226,204.]); sage=np.array([128,152,128.]); navy=np.array([48,66,98.]); terra=np.array([190,110,76.])
    img=np.zeros((H,W,3)); img[:]=cream
    border=(u<0.03)|(u>0.97)|(v<0.07)|(v>0.93); img[border]=navy
    inner=(u>0.045)&(u<0.955)&(v>0.11)&(v<0.89); 
    st=(np.floor(u*18)%2==0); img[inner&st]=sage
    mid=(np.abs(v-0.5)<0.06)&inner; img[mid]=terra
    for k in range(18):
        cu=(k+0.5)/18; d=np.abs(u-cu)*W+np.abs(v-0.5)*H*1.2
        img[(d<14)&inner]=np.where(k%2==0,cream,sage)[None]
    img*= (0.9+0.14*tnoise(512,0.5,0.5,5)[:H,:W if W<=512 else 512].repeat(1,1) if False else 1)[...,None] if False else 1
    n=tnoise(512,0.6,0.6,9); n=np.array(Image.fromarray((n*255).astype(np.uint8)).resize((W,H)))/255.
    img*= (0.9+0.14*n)[...,None]
    save_tex(name,img)
def rug_c(name='rug_c.png',W=1024,H=512):
    y,x=np.mgrid[0:H,0:W]; u=(x+0.5)/W; v=(y+0.5)/H
    bg=np.array([40,52,66.]); cream=np.array([226,212,184.]); gold=np.array([208,160,72.]); rust=np.array([168,72,52.])
    img=np.zeros((H,W,3)); img[:]=bg
    # losangos repetidos
    cu=(u*10)%1; cv=(v*4)%1; d=np.abs(cu-0.5)+np.abs(cv-0.5)
    img[d<0.42]=cream; img[d<0.30]=rust; img[d<0.16]=gold; img[d<0.06]=bg
    border=(u<0.025)|(u>0.975)|(v<0.06)|(v>0.94); img[border]=gold
    border2=((u<0.04)&(u>=0.025))|((u>0.96)&(u<=0.975))|((v<0.09)&(v>=0.06))|((v>0.91)&(v<=0.94)); img[border2]=bg
    n=tnoise(512,0.6,0.6,10); n=np.array(Image.fromarray((n*255).astype(np.uint8)).resize((W,H)))/255.
    img*=(0.9+0.14*n)[...,None]; save_tex(name,img)
def round_(name,cols,rings,seed,S=512):
    y,x=np.mgrid[0:S,0:S]; u=(x+0.5)/S*2-1; v=(y+0.5)/S*2-1; d=np.hypot(u,v); ang=np.arctan2(v,u)
    img=np.zeros((S,S,3)); img[:]=cols[0]
    for (r0,r1,ci) in rings: img[(d>=r0)&(d<r1)]=cols[ci]
    img[d>1]=cols[0]
    n=tnoise(S,0.6,0.6,seed); img*=(0.9+0.14*n)[...,None]; save_tex(name,img)
def rug_d(name='rug_d.png'):
    cream=np.array([232,220,196.]); terra=np.array([186,98,68.]); sage=np.array([132,150,120.]); navy=np.array([54,70,104.]); gold=np.array([210,168,86.])
    S=512; y,x=np.mgrid[0:S,0:S]; u=(x+0.5)/S*2-1; v=(y+0.5)/S*2-1; d=np.hypot(u,v); a=np.arctan2(v,u)
    img=np.zeros((S,S,3)); img[:]=cream
    img[(d>0.92)]=navy; img[(d>0.86)&(d<=0.92)]=cream; img[(d>0.72)&(d<=0.86)]=terra
    img[(d>0.5)&(d<=0.72)]=np.where((np.floor((a+math.pi)/(2*math.pi)*24)%2==0)[...,None],sage,cream)[(d>0.5)&(d<=0.72)]
    img[(d>0.36)&(d<=0.5)]=navy; img[(d>0.3)&(d<=0.36)]=gold
    img[(d>0.14)&(d<=0.3)]=np.where((np.floor((a+math.pi)/(2*math.pi)*12)%2==0)[...,None],terra,cream)[(d>0.14)&(d<=0.3)]
    img[d<=0.14]=gold
    n=tnoise(S,0.6,0.6,12); img*=(0.9+0.14*n)[...,None]; save_tex(name,img)
def rug_e(name='rug_e.png'):
    S=512; y,x=np.mgrid[0:S,0:S]; u=(x+0.5)/S*2-1; v=(y+0.5)/S*2-1; d=np.hypot(u,v)
    base=np.array([196,182,160.]); dark=np.array([92,86,78.]); img=np.zeros((S,S,3)); img[:]=base
    img[(d>0.88)]=dark; img[(d>0.8)&(d<=0.88)]=np.array([226,214,192.])
    for r in (0.6,0.4,0.2): img[np.abs(d-r)<0.025]=np.array([150,136,116.])
    n=tnoise(S,0.5,0.5,13); img*=(0.88+0.2*n)[...,None]; save_tex(name,img)
if __name__=='__main__':
    rug_b(); rug_c(); rug_d(); rug_e(); print('ok')
